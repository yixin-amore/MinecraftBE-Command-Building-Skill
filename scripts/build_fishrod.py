#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""鱼竿枪 —— 按功能分链 + 改朝向断链。

结构严格照 `断链演示.mcstructure`：
每条功能链 = 1 个循环闸门 + 1 个复位块 + 1 个自断块 + N 个业务块，
全部无条件块，断链靠 `setblock` 改 `facing_direction`，不用 conditional_bit。

    x+0  循环块   execute if entity <闸门条件>
    x+1  链块     复位：把 x+2 摆回朝前（每 tick 都做，所以链能自愈）
    x+2  链块     自断：闸门条件不成立时把自己摆成朝后 → 触发已执行过的 x+1 → 链停
    x+3..链块     业务（全部无条件，各自带选择器过滤）

三条功能链 = 3 条常驻。不持枪、没子弹时只有 3 条闸门在跑。

用法：
    python build_fishrod.py --dump-spec specs/fishrod_gun.json
    python build_fishrod.py --spec specs/fishrod_gun.json \
           --template _template.mcworld --out 鱼竿枪指令世界.mcworld
"""
import argparse
import json
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B

# ---------------------------------------------------------------- 常量
FOE = ("type=!player,type=!xp_orb,type=!item,type=!fishing_hook,"
       "type=!arrow,type=!boat,type=!armor_stand")

ROD = "hasitem={item=fishing_rod,location=slot.weapon.mainhand}"

# 枪型：id -> (显示名, 弹匣, 射速刻, 弹丸数, 伤害档, 散布档, 换弹刻, 弹速档, 后坐力, 射程刻)
GUNS = {
    1: ("ＡＲ－１５",   30,  3, 1, 2, 1, 28, 1, "0.16", 32),
    2: ("ＡＷＭ",        5, 24, 1, 4, 0, 55, 2, "0.42", 45),
    3: ("ＳＰＡＳ－１２", 8, 16, 6, 1, 4, 46, 1, "0.30", 12),
}
# 副手物品 → 枪型（顺序即优先级，后写的覆盖先写的）
GUN_SWITCH = [(2, "arrow"), (3, "blaze_powder")]

# 伤害档 -> 实际伤害（/damage 只吃字面量，必须分档）
DMG_TIERS = [(1, 4), (2, 8), (3, 14), (4, 25)]

# 散布档 -> 局部偏移前缀
SPREAD = {
    0: "^0^0^",
    1: "^0.03^0^",
    2: "^-0.03^0^",
    3: "^0^0.025^",
    4: "^0^-0.025^",
}
STEP = "0.9"


# ---------------------------------------------------------------- HUD
def cell(obj, i, lit_color="§a", dark_color="§8", ch="▮"):
    """单格：满则亮色，否则暗色。

    全程字符串拼接，不能用 % 格式化 —— % 会把 %%2 吃成 %2，条件拼接当场失效。
    """
    return ('{"translate":"%%2","with":[{"selector":"@s[scores={'
            + obj + '=' + str(i) + '..}]"},'
            '{"text":"' + lit_color + ch + '"}]},'
            '{"translate":"%%2","with":[{"selector":"@s[scores={'
            + obj + '=..' + str(i - 1) + '}]"},'
            '{"text":"' + dark_color + ch + '"}]},')


def gun_name():
    """枪名：每种枪型一个条件组件。全角字母等宽，切枪不跳字。"""
    out = []
    for gid in sorted(GUNS):
        out.append('{"translate":"%%2","with":[{"selector":"@s[scores={gtype='
                   + str(gid) + '}]"},{"text":"' + GUNS[gid][0] + '"}]},')
    return "".join(out)


def hud():
    """两行 actionbar：型号与弹药 / 弹匣条与状态。"""
    bar = "".join(cell("ammo_t", i) for i in range(1, 11))
    parts = [
        '{"rawtext":[',
        '{"text":"§8▏ §f"},',
        gun_name(),
        '{"text":"  §8· §f"},',
        '{"score":{"objective":"ammo","name":"@s"}},',
        '{"text":"§8／"},',
        '{"score":{"objective":"mag","name":"@s"}},',
        '{"translate":"%%2","with":[{"selector":"@s[scores={reload=1..}]"},'
        '{"text":"  §7换弹中"}]},',
        '{"translate":"%%2","with":[{"selector":"@s[scores={reload=0,ammo=0}]"},'
        '{"text":"  §c空仓"}]},',
        '{"translate":"%%2","with":[{"selector":"@s[scores={reload=0,ammo=1..}]"},'
        '{"text":"  §a就绪"}]},',
        '{"text":"\\n§8▏ "},',
        bar,
        '{"translate":"%%2","with":[{"selector":"@s[scores={reload=1..}]"},'
        '{"text":"  §7"}]},',
        '{"translate":"%%2","with":[{"selector":"@s[scores={reload=1..}]"},'
        '{"score":{"objective":"reload","name":"@s"}}]},',
        '{"translate":"%%2","with":[{"selector":"@s[scores={reload=1..}]"},'
        '{"text":"§8／"}]},',
        '{"translate":"%%2","with":[{"selector":"@s[scores={reload=1..}]"},'
        '{"score":{"objective":"reload_t","name":"@s"}}]},',
        ']}',
    ]
    return B._escape("".join(parts).replace(",]}", "]}"))


# ---------------------------------------------------------------- spec
def fishrod_spec():
    obj = [
        ("gun", "dummy", "持枪"), ("gtype", "dummy", "枪型"),
        ("gtype_last", "dummy", ""),
        ("mag", "dummy", "弹匣"), ("ammo", "dummy", "余弹"),
        ("reserve", "dummy", "备弹"), ("reload", "dummy", "换弹"),
        ("reload_t", "dummy", ""), ("fire_cd", "dummy", ""),
        ("fire_rate", "dummy", ""),
        ("firing", "dummy", ""), ("pellet", "dummy", ""),
        ("ammo_t", "dummy", ""), ("rl_tmp", "dummy", ""),
        ("gdmg", "dummy", ""), ("spread", "dummy", ""),
        ("bspd", "dummy", ""), ("range", "dummy", "射程"),
        ("b_life", "dummy", ""), ("b_dmg", "dummy", ""),
        ("b_sp", "dummy", ""), ("b_spd", "dummy", ""),
        ("b_new", "dummy", ""),
        ("sys", "dummy", ""),
    ]

    init = []
    for name, crit, disp in obj:
        init.append("scoreboard objectives add %s %s" % (name, crit) +
                    (' "%s"' % disp if disp else ""))
    init += [
        "scoreboard players set zero sys 0",
        "scoreboard players set one sys 1",
        "scoreboard players set two sys 2",
        "scoreboard players set three sys 3",
        "scoreboard players set four sys 4",
        "scoreboard players set six sys 6",
        "scoreboard players set ten sys 10",
        "scoreboard players set thirty sys 30",
        "scoreboard players set hundred sys 100",
        "gamerule commandblocksenabled true",
        # 聊天栏灰字：6 条 gamerule，sendcommandfeedback 必须第一条
        # （命令方块界面的「上一个输出」是方块 NBT 的 TrackOutput，这里管不到）
        "gamerule sendcommandfeedback false",
        "gamerule commandblockoutput false",
        "gamerule showdeathmessages false",
        "gamerule announceadvancements false",
        "gamerule showrecipemessages false",
        "gamerule showcoordinates false",
        "gamerule dodaylightcycle false",
        "gamerule doweathercycle false",
        "gamerule domobspawning false",
        "gamerule keepinventory true",
        "gamerule mobgriefing false",
        "hud @a hide health",
        "hud @a hide hunger",
        "hud @a hide armor",
        "hud @a hide status_effects",
        "hud @a hide item_text",
        "effect @a saturation 1 255 true",
        "setworldspawn 8 -59 7",
        "time set noon",
        # 配装：主手鱼竿 = 枪，副手物品切枪型
        "give @a fishing_rod 1",
        "give @a arrow 1",
        "give @a blaze_powder 1",
        "kill @e[type=xp_orb]",
        "summon zombie 5 -60 16",
        "summon zombie 8 -60 17",
        "summon zombie 11 -60 16",
        "summon zombie 14 -60 18",
        "tellraw @a " + B._escape(
            '{"rawtext":[{"text":"§b§l鱼竿枪 §r§f已就绪\\n'
            '§7主手 §f鱼竿§7 = 枪，§f右键抛竿§7 = 开火\\n'
            '§7副手 §f空§7 = §fＡＲ－１５ §8(30发/连发)\\n'
            '§7副手 §f箭§7 = §eＡＷＭ §8(5发/一枪一个)\\n'
            '§7副手 §f烈焰粉§7 = §6ＳＰＡＳ－１２ §8(8发/6弹丸)\\n'
            '§7低头 §f(rxm=88)§7 = 换弹"}]}'),
    ]

    def cfg(gid):
        """某种枪型的静态配置，每刻覆盖。只写容量类，不碰 ammo。"""
        name, mag, rate, pellet, dmg, sp, rl, spd, recoil, rng = GUNS[gid]
        return [
            "execute as @a[scores={gun=1,gtype=%d}] run scoreboard players set @s mag %d"
            % (gid, mag),
            "execute as @a[scores={gun=1,gtype=%d}] run scoreboard players set @s fire_rate %d"
            % (gid, rate),
            "execute as @a[scores={gun=1,gtype=%d}] run scoreboard players set @s pellet %d"
            % (gid, pellet),
            "execute as @a[scores={gun=1,gtype=%d}] run scoreboard players set @s gdmg %d"
            % (gid, dmg),
            "execute as @a[scores={gun=1,gtype=%d}] run scoreboard players set @s spread %d"
            % (gid, sp),
            "execute as @a[scores={gun=1,gtype=%d}] run scoreboard players set @s reload_t %d"
            % (gid, rl),
            "execute as @a[scores={gun=1,gtype=%d}] run scoreboard players set @s bspd %d"
            % (gid, spd),
            "execute as @a[scores={gun=1,gtype=%d}] run scoreboard players set @s range %d"
            % (gid, rng),
        ]

    # ================= 链 A：玩家状态 =================
    # 闸门：有人主手持鱼竿。管兜底 / 枪型 / 配置 / 换弹 / HUD。
    seg_state = [
        # 布尔位兜底：从未赋值的玩家也要能被 scores={x=0} 匹配
        "scoreboard players add @a gun 0",
        "scoreboard players add @a gtype 0",
        "scoreboard players add @a gtype_last 0",
        "scoreboard players add @a mag 0",
        "scoreboard players add @a ammo 0",
        "scoreboard players add @a reserve 0",
        "scoreboard players add @a reload 0",
        "scoreboard players add @a reload_t 0",
        "scoreboard players add @a fire_cd 0",
        "scoreboard players add @a fire_rate 0",
        "scoreboard players add @a firing 0",
        "scoreboard players add @a pellet 0",
        "scoreboard players add @a ammo_t 0",
        "scoreboard players add @a gdmg 0",
        "scoreboard players add @a spread 0",
        "scoreboard players add @a bspd 0",
        "scoreboard players add @a range 0",
        # 持枪标记：先给持有者置 1，再把非持有者清 0
        # 不清 0 的话，扔了鱼竿的玩家会一直留在 gun=1 里，HUD 关不掉
        "execute as @a[%s] run scoreboard players set @s gun 1" % ROD,
        "execute as @a unless entity @s[%s] run scoreboard players set @s gun 0" % ROD,
        "execute as @a[%s] run scoreboard players set @s gtype 1" % ROD,
    ]
    # 副手切枪型：后写的覆盖先写的
    for gid, item in GUN_SWITCH:
        seg_state.append(
            "execute as @a[scores={gun=1},hasitem={item=%s,location=slot.weapon.offhand}]"
            " run scoreboard players set @s gtype %d" % (item, gid))
    for gid in sorted(GUNS):
        seg_state += cfg(gid)
    seg_state += [
        # 换枪时补满（gtype != gtype_last 才触发，不会每刻重置弹药）
        "execute as @a[scores={gun=1}] unless score @s gtype = @s gtype_last"
        " run scoreboard players operation @s ammo = @s mag",
        "execute as @a[scores={gun=1}] unless score @s gtype = @s gtype_last"
        " run scoreboard players operation @s reserve = @s mag",
        "execute as @a[scores={gun=1}] unless score @s gtype = @s gtype_last"
        " run scoreboard players operation @s reserve *= four sys",
        "execute as @a[scores={gun=1}] unless score @s gtype = @s gtype_last"
        " run scoreboard players operation @s gtype_last = @s gtype",
        # 余弹不得超过弹匣（切到小弹匣时夹住）
        "execute as @a[scores={gun=1}] run scoreboard players operation @s ammo < @s mag",
        # 开火冷却递减 + 夹到 0
        "scoreboard players remove @a[scores={gun=1}] fire_cd 1",
        "scoreboard players operation @a[scores={gun=1}] fire_cd > zero sys",
        # 换弹触发：低头 + 弹不满 + 不在换弹 + 冷却已过
        "execute as @a[scores={gun=1},rxm=88,%s] if score @s ammo < @s mag"
        " unless score @s reload matches 1.. unless score @s fire_cd matches 1.."
        " run scoreboard players operation @s reload = @s reload_t" % ROD,
        # 换弹倒计时（判 =1 而不是 =0：递减在前，最后那一 tick 才是 1）
        "scoreboard players remove @a[scores={gun=1,reload=1..}] reload 1",
        # 换弹结算：缺额 = mag - ammo，被 reserve 夹住，再双向转账
        "execute as @a[scores={reload=1}] run scoreboard players operation @s rl_tmp = @s mag",
        "execute as @a[scores={reload=1}] run scoreboard players operation @s rl_tmp -= @s ammo",
        "execute as @a[scores={reload=1}] run scoreboard players operation @s rl_tmp < @s reserve",
        "execute as @a[scores={reload=1}] run scoreboard players operation @s reserve -= @s rl_tmp",
        "execute as @a[scores={reload=1}] run scoreboard players operation @s ammo += @s rl_tmp",
        "execute as @a[scores={reload=1}] run scoreboard players set @s reload 0",
        # 换弹音：每 tick 机械摩擦 + 最后一 tick 卡榫入位
        "execute as @a[scores={gun=1,reload=1..}] at @s run playsound armor.equip_iron"
        " @a[r=16] ~~~ 0.5 1.5",
        "execute as @a[scores={gun=1,reload=1}] at @s run playsound armor.equip_iron"
        " @a[r=16] ~~~ 1 0.8",
        "execute as @a[scores={gun=1,reload=1}] at @s run playsound random.click"
        " @a[r=16] ~~~ 0.9 1.2",
        # 弹匣条格数 = ammo * 10 / mag
        "execute as @a[scores={gun=1}] run scoreboard players operation @s ammo_t = @s ammo",
        "execute as @a[scores={gun=1}] run scoreboard players operation @s ammo_t *= ten sys",
        "execute as @a[scores={gun=1}] run scoreboard players operation @s ammo_t /= @s mag",
        # HUD 只给真正拿着鱼竿的人
        "execute as @a[%s] run titleraw @s actionbar %s" % (ROD, hud()),
    ]

    # ================= 链 B：开火 =================
    # 闸门：有人持鱼竿 且 场上有鱼钩（抛竿了）。
    seg_fire = [
        # 抛竿 = 扳机。钩子出现即视为按下，本刻标记 firing
        "execute as @a[scores={gun=1,fire_cd=0,reload=0}] at @s"
        " if entity @e[type=fishing_hook,r=6] run scoreboard players set @s firing 1",
        # 上锁：冷却顶到射速。链 A 已在本刻递减过，所以下一发要等满 fire_rate 刻
        "execute as @a[scores={firing=1}]"
        " run scoreboard players operation @s fire_cd = @s fire_rate",
        # 收竿：钩子一消失鱼竿立刻能再抛，这就是能连发的关键
        "execute as @a[scores={firing=1}] at @s run kill @e[type=fishing_hook,r=8]",
        # 空仓：两声干涩的咔哒，不出弹
        "execute as @a[scores={firing=1,ammo=0}] at @s"
        " run playsound random.click @s ~~~ 0.7 1.8",
        "execute as @a[scores={firing=1,ammo=0}] at @s"
        " run playsound note.bass @s ~~~ 0.5 0.6",
    ]
    # 出弹：霰弹按 pellet 连召唤，一颗一条。
    # ammo=1.. 是唯一门槛；扣弹排在段尾，这里看到的还是"开火前"的余弹
    for n in range(1, 7):
        cond = "firing=1,ammo=1.." + (",pellet=%d.." % n if n > 1 else "")
        seg_fire.append(
            "execute as @a[scores={%s}] at @s anchored eyes"
            " run summon xp_orb ^ ^ ^1.2" % cond)
    seg_fire += [
        # 新弹打标：r=1.4 只覆盖刚生成那批（上一发已飞出 1.8 格）
        "execute as @a[scores={firing=1,ammo=1..}] at @s anchored eyes"
        " run scoreboard players set @e[type=xp_orb,r=1.4] b_new 1",
        # 继承朝向：先 tp 到玩家位置吃掉 yRot/pitch，再 tp 到眼前。顺序不能反
        "execute as @a[scores={firing=1,ammo=1..}] at @s"
        " run tp @e[type=xp_orb,scores={b_new=1}] ~~~ ~ ~",
        "execute as @a[scores={firing=1,ammo=1..}] at @s anchored eyes"
        " run tp @e[type=xp_orb,scores={b_new=1}] ^ ^ ^1.2",
    ]
    # 灌参数：选择器用 r=1.4 就近限定，不能写全局 b_new=1（两个玩家同刻开火会互相覆盖）
    for src, dst in (("range", "b_life"), ("gdmg", "b_dmg"), ("bspd", "b_spd")):
        seg_fire.append(
            "execute as @a[scores={firing=1,ammo=1..}] at @s anchored eyes"
            " run scoreboard players operation @e[type=xp_orb,r=1.4]"
            " %s = @s %s" % (dst, src))
    seg_fire += [
        "execute as @a[scores={firing=1,ammo=1..,spread=1..}] at @s anchored eyes"
        " run scoreboard players random @e[type=xp_orb,r=1.4] b_sp 0 4",
        "execute as @a[scores={firing=1,ammo=1..,spread=0}] at @s anchored eyes"
        " run scoreboard players set @e[type=xp_orb,r=1.4] b_sp 0",
        "scoreboard players set @e[type=xp_orb,scores={b_new=1}] b_new 0",
        # 枪口焰：三种枪型各一套
        "execute as @a[scores={firing=1,ammo=1..,gtype=1}] at @s anchored eyes"
        " positioned ^^^1.4 run particle minecraft:basic_flame_particle ~~~",
        "execute as @a[scores={firing=1,ammo=1..,gtype=2}] at @s anchored eyes"
        " positioned ^^^1.6 run particle minecraft:sparkler_emitter ~~~",
        "execute as @a[scores={firing=1,ammo=1..,gtype=3}] at @s anchored eyes"
        " positioned ^^^1.4 run particle minecraft:basic_smoke_particle ~~~",
        # 后坐力：三档震动
        "execute as @a[scores={firing=1,ammo=1..,gtype=1}]"
        " run camerashake add @s 0.16 0.15 rotational",
        "execute as @a[scores={firing=1,ammo=1..,gtype=2}]"
        " run camerashake add @s 0.42 0.3 rotational",
        "execute as @a[scores={firing=1,ammo=1..,gtype=3}]"
        " run camerashake add @s 0.30 0.2 rotational",
        # 枪声：低频冲击 + 中频爆裂 + 高频锐利，三层叠加
        "execute as @a[scores={firing=1,ammo=1..}] at @s"
        " run playsound random.explode @a[r=24] ~~~ 0.7 0.9",
        "execute as @a[scores={firing=1,ammo=1..}] at @s"
        " run playsound mob.blaze.hit @a[r=24] ~~~ 0.9 1.4",
        "execute as @a[scores={firing=1,ammo=1..}] at @s"
        " run playsound random.break @a[r=16] ~~~ 0.5 1.8",
        # 扣弹：所有特效都看完余弹了，这里才真正消耗
        "execute as @a[scores={firing=1,ammo=1..}]"
        " run scoreboard players remove @s ammo 1",
        # 补一次 HUD：链 A 是在扣弹之前画的，这里重画让条和数字同帧
        "execute as @a[scores={firing=1,gun=1}]"
        " run scoreboard players operation @s ammo_t = @s ammo",
        "execute as @a[scores={firing=1,gun=1}]"
        " run scoreboard players operation @s ammo_t *= ten sys",
        "execute as @a[scores={firing=1,gun=1}]"
        " run scoreboard players operation @s ammo_t /= @s mag",
        "execute as @a[scores={firing=1},%s] run titleraw @s actionbar %s" % (ROD, hud()),
        # 清标记：必须最后
        "execute as @a[scores={firing=1}] run scoreboard players set @s firing 0",
    ]

    # ================= 链 C：子弹 =================
    # 闸门：场上还有存活子弹。管推进 / 命中 / 销毁。
    seg_bullet = []
    for sp, prefix in sorted(SPREAD.items()):
        seg_bullet.append(
            "execute as @e[type=xp_orb,scores={b_life=1..,b_sp=%d}] at @s"
            " run tp @s %s%s" % (sp, prefix, STEP))
    # 弹速档 2（狙击）：再走一步，等效 1.8 格/刻
    seg_bullet.append(
        "execute as @e[type=xp_orb,scores={b_life=1..,b_sp=0,b_spd=2}] at @s"
        " run tp @s ^^^%s" % STEP)
    # 命中结算：分档伤害（/damage 不吃计分板，只能一档一条）
    for tier, dmg in DMG_TIERS:
        seg_bullet.append(
            "execute as @e[type=xp_orb,scores={b_life=1..,b_dmg=%d}] at @s"
            " if entity @e[r=0.9,%s] run damage @e[r=0.9,c=1,%s] %d entity_attack"
            " entity @s" % (tier, FOE, FOE, dmg))
    seg_bullet += [
        "execute as @e[type=xp_orb,scores={b_life=1..}] at @s"
        " if entity @e[r=0.9,%s] run particle minecraft:critical_hit_emitter ~~~" % FOE,
        "execute as @e[type=xp_orb,scores={b_life=1..}] at @s"
        " if entity @e[r=0.9,%s] run playsound random.orb @a[r=20] ~~~ 1 2" % FOE,
        "execute as @e[type=xp_orb,scores={b_life=1..}] at @s"
        " if entity @e[r=0.9,%s] run playsound mob.irongolem.hit @a[r=20] ~~~ 0.8 1.6"
        % FOE,
        # 先结算伤害，最后销毁：反过来会先杀掉自己，entity @s 失效，伤害打空
        "execute as @e[type=xp_orb,scores={b_life=1..}] at @s"
        " if entity @e[r=0.9,%s] run kill @s" % FOE,
        "scoreboard players remove @e[type=xp_orb,scores={b_life=1..}] b_life 1",
        "execute as @e[type=xp_orb,scores={b_life=..0}] at @s run kill @s",
    ]

    # 三条功能链，各一个循环闸门 → 3 条常驻
    chains = [
        {"id": "init", "kind": "impulse", "button": True, "cmds": init},
        {"id": "state", "kind": "gated",
         "gate": "execute if entity @a[%s]" % ROD,
         "brk": "execute unless entity @a[%s]" % ROD,
         "cmds": seg_state},
        {"id": "fire", "kind": "gated",
         "gate": "execute if entity @a[%s] if entity @e[type=fishing_hook]" % ROD,
         "brk": "execute unless entity @e[type=fishing_hook]",
         "cmds": seg_fire},
        {"id": "bullet", "kind": "gated",
         "gate": "execute if entity @e[type=xp_orb,scores={b_life=1..}]",
         "brk": "execute unless entity @e[type=xp_orb,scores={b_life=1..}]",
         "cmds": seg_bullet},
    ]

    panels = [
        {"label": "补满弹药", "cmds": [
            "scoreboard players operation @p ammo = @p mag",
            "scoreboard players operation @p reserve = @p mag",
            "scoreboard players operation @p reserve *= four sys",
            'tellraw @p {"rawtext":[{"text":"§a弹药已补满"}]}',
        ]},
        {"label": "清空靶场", "cmds": [
            "kill @e[type=zombie]",
            "kill @e[type=xp_orb]",
            "summon zombie 5 -60 16",
            "summon zombie 8 -60 17",
            "summon zombie 11 -60 16",
            "summon zombie 14 -60 18",
            'tellraw @p {"rawtext":[{"text":"§7靶场已重置"}]}',
        ]},
        {"label": "再给一根鱼竿", "cmds": [
            "give @p fishing_rod 1",
            'tellraw @p {"rawtext":[{"text":"§f已获得 §7鱼竿"}]}',
        ]},
        {"label": "重置自身", "cmds": [
            "scoreboard players reset @p ammo",
            "scoreboard players reset @p reserve",
            "scoreboard players reset @p reload",
            "scoreboard players reset @p fire_cd",
            "scoreboard players reset @p gtype_last",
            'tellraw @p {"rawtext":[{"text":"§c枪械状态已重置"}]}',
        ]},
    ]

    return {
        "meta": {"name": "鱼竿枪指令世界", "spawn": [8, -59, 7],
                 "gametype": "creative", "debug_output": False},
        "objectives": [{"name": n, "criteria": c, "display": d} for n, c, d in obj],
        "chains": chains,
        "panels": panels,
    }


# ---------------------------------------------------------------- 布局
def _fd(dx, dz):
    """位移 → facing_direction（0下 1上 2北 3南 4西 5东）。"""
    if dx > 0:
        return 5
    if dx < 0:
        return 4
    if dz > 0:
        return 3
    return 2


def _fkey(dx, dz):
    """位移 → 链块键名。"""
    if dx > 0:
        return "ch_E"
    if dx < 0:
        return "ch_W"
    if dz > 0:
        return "ch_S"
    return "ch_N"


def layout(spec, width=16, ground=4):
    """把 spec 排成多条链，返回 (blocks, entities, depth, idle)。

    gated 链的骨架（与 断链演示 一致，全部无条件块）：
        [0] 循环闸门   execute if entity <条件>
        [1] 复位       setblock ~dx ~ ~dz chain_command_block["facing_direction"=朝前]
        [2] 自断       execute unless <条件> run setblock ~ ~ ~ ...["facing_direction"=朝后]
        [3..] 业务
    """
    blocks, entities = {}, {}
    rows = 0
    for ch in spec["chains"]:
        n = len(ch["cmds"]) + (3 if ch["kind"] == "gated" else 0)
        rows += (n + width - 1) // width
    depth = rows + len(spec["panels"]) + 3
    B.make_floor(blocks, width, depth, 3)

    idle = 0

    def add_chain(ch, start_z):
        nonlocal idle
        body = ch["cmds"]
        gated = ch["kind"] == "gated"
        n = len(body) + (3 if gated else 0)
        path = B.serpentine(n, start_z, width)

        def put(i, cmd, auto):
            x, z = path[i]
            if i == 0:
                key = "rep_E" if gated else (
                    "imp_E" if ch["kind"] == "impulse" else "rep_E")
            elif i + 1 < len(path):
                key = _fkey(path[i + 1][0] - x, path[i + 1][1] - z)
            else:
                # 末块沿用流向，不能固定朝东（否则会指回前一块互相触发）
                key = _fkey(x - path[i - 1][0], z - path[i - 1][1])
            blocks[(x, ground, z)] = key
            entities[(x, z)] = (B._escape(cmd), auto, 0)

        if gated:
            idle += 1
            # [0] 循环闸门
            put(0, ch["gate"], 1)
            # [1] 复位：把下一格摆回"朝前"
            dx = path[2][0] - path[1][0]
            dz = path[2][1] - path[1][1]
            put(1, 'setblock ~%d ~ ~%d chain_command_block["facing_direction"=%d]'
                % (dx, dz, _fd(dx, dz)), 1)
            # [2] 自断：条件不成立就把自己摆成"朝后"，触发已跑过的 [1] → 链停
            bx, bz = -dx, -dz
            put(2, 'execute unless %s run setblock ~ ~ ~ chain_command_block'
                   '["facing_direction"=%d]'
                % (ch["brk"][len("execute unless "):], _fd(bx, bz)), 1)
            for i, cmd in enumerate(body):
                put(3 + i, cmd, 1)
        else:
            for i, cmd in enumerate(body):
                put(i, cmd, 0 if (i == 0 and ch["kind"] == "impulse") else 1)

        if ch.get("button"):
            blocks[(path[0][0], ground + 1, path[0][1])] = "btn"
            blocks[(path[0][0], ground - 1, path[0][1])] = "floor_btn"
        return path[-1][1]

    z = 0
    for ch in spec["chains"]:
        z = add_chain(ch, z) + 1

    for panel in spec["panels"]:
        # 面板也是无条件链：每条命令自带选择器，不靠条件块传播
        for i, cmd in enumerate(panel["cmds"]):
            key = "imp_E" if i == 0 else "ch_E"
            blocks[(i, ground, z)] = key
            entities[(i, z)] = (B._escape(cmd), 0 if i == 0 else 1, 0)
        blocks[(0, ground + 1, z)] = "btn"
        blocks[(0, ground - 1, z)] = "floor_btn"
        z += 1
    return blocks, entities, depth, idle


def build_world(template, out, spec):
    meta = spec["meta"]
    blocks, entities, depth, idle = layout(spec)

    chunks = {}
    for (x, y, z), key in blocks.items():
        chunks.setdefault((x // 16, z // 16), {}).setdefault("blocks", {})[(x % 16, y, z % 16)] = key
    for (x, z), val in entities.items():
        chunks.setdefault((x // 16, z // 16), {}).setdefault("ents", {})[(x % 16, z % 16)] = val

    pairs, seq = [], 0
    for (cx, cz) in sorted(chunks):
        c = chunks[(cx, cz)]
        sub = B.encode_subchunk(-4, c.get("blocks", {}))
        kb = struct.pack("<ii", cx, cz)
        for tag, val in ((b"\x2c", b"\x28"), (b"\x2b", b"\x00" * 632),
                         (b"\x36", struct.pack("<i", 2)),
                         (b"\x2f" + struct.pack("<b", -4), sub)):
            seq += 1
            pairs.append((seq, kb + tag, val))
        body = b"".join(B.cb_entity(cx * 16 + lx, -60, cz * 16 + lz, cmd, auto, cond,
                                    track=1 if meta.get("debug_output") else 0)
                        for (lx, lz), (cmd, auto, cond) in sorted(c.get("ents", {}).items()))
        if body:
            seq += 1
            pairs.append((seq, kb + b"\x31", body))

    all_cmds = [c for c, _, _ in entities.values()]
    bad = B.check_commands(all_cmds)
    if bad:
        print("[警告] %d 条 tellraw/titleraw JSON 非法：" % len(bad))
        for frag, err in bad[:5]:
            print("    %s ... → %s" % (frag, err))

    gt = {"survival": 0, "creative": 1, "adventure": 2, "spectator": 3}[
        meta.get("gametype", "creative")]
    level = B.build_level_dat(template, meta["name"], meta.get("spawn", [8, -60, 7]), gt)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("level.dat", level)
        zf.writestr("levelname.txt", meta["name"])
        zf.writestr("world_behavior_packs.json", "[]")
        zf.writestr("world_resource_packs.json", "[]")
        zf.writestr("db/CURRENT", "MANIFEST-000000\n")
        zf.writestr("db/LOCK", b"")
        zf.writestr("db/LOG", b"")
        zf.writestr("db/MANIFEST-000000", B.manifest_bytes(0))
        zf.writestr("db/000001.log", B.log_records(pairs))

    return {"chunks": len(chunks), "blocks": len(entities),
            "buttons": sum(1 for v in blocks.values() if v == "btn"),
            "cmds": len(all_cmds), "out": out, "depth": depth, "idle": idle}


def main():
    ap = argparse.ArgumentParser(description="鱼竿枪：按功能分链 + 改朝向断链")
    ap.add_argument("--dump-spec", metavar="JSON")
    ap.add_argument("--spec")
    ap.add_argument("--template")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.dump_spec:
        spec = fishrod_spec()
        os.makedirs(os.path.dirname(os.path.abspath(args.dump_spec)), exist_ok=True)
        with open(args.dump_spec, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        n = sum(len(c.get("cmds", [])) for c in spec["chains"]) + \
            sum(len(p["cmds"]) for p in spec["panels"])
        gated = sum(1 for c in spec["chains"] if c["kind"] == "gated")
        print("[spec] %s  链 %d 条（其中功能链 %d 条）/ 命令 %d 条"
              % (args.dump_spec, len(spec["chains"]), gated, n))
        return

    if not (args.spec and args.template and args.out):
        ap.error("生成世界需要 --spec / --template / --out")

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    info = build_world(args.template, args.out, spec)
    print("[完成] %s" % info["out"])
    print("        区块 %d 个，命令方块 %d 个，按钮 %d 个，命令 %d 条，地板深 %d"
          % (info["chunks"], info["blocks"], info["buttons"], info["cmds"], info["depth"]))
    print("        功能链 %d 条 → 空闲每刻只有 %d 条闸门在跑"
          % (info["idle"], info["idle"]))
    print("        下一步：python verify_mcworld.py <文件>")


if __name__ == "__main__":
    main()
