#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_tidegun.py —— 「潮汐」鱼竿枪 v3（真实原理版）

**这一版按 SKILL.md 第 99–102 章重写**，和 v2 的实现思路完全不同：

  第 99 章  钩子 = 扳机（取完 @p 立刻 kill，玩家看不到浮漂 = 伪无）
            xp_orb = 弹道载体，`tp ~~500~` 是 **y+500** 垂直顶高，之后不再动
            散射 = 旋转 yaw/pitch（单位 1/100 度），二分法 512/256/…/1 一次拧到位
  第 99.5  四步固定：碰撞穷举 → 三段肢体 → 粒子 → 伤害收尾
  第 100 章 换弹 zd / zdmax 双变量 + 溢出回灌 + 两条结算分支
  第 101 章 队伍uid 比对做免伤
  第 102 章 40 项穿透白名单

链结构（7 条功能链 + 1 条初始化 + 3 个面板）：

  init     脉冲   建档 / gamerule / tickingarea / 锚点哨兵 / 常驻 HUD
  clock    循环   全局刻 + 射速间隔递减 + 掉枪清零
  state    循环   枪型 / 容量 / 伤害 / 溢出回灌 / 换弹倒计时 / 结算 / HUD
  trigger  循环   钩子出现 → 判空仓 → 打开火标 → 杀钩子（伪无）
  shot     循环   出弹（一 tick 一颗）→ 顶高 → 打标 → 灌参数 → 散射 → 枪口 → 音效 → 后坐 → 扣弹
  bullet   循环   碰撞穷举 → 三段肢体 → 粒子 → 伤害 → 清理
  reload   循环   换弹过程音 + 完成提示

用法：
  python build_tidegun.py --dump-spec tide.json
  python build_tidegun.py --spec tide.json --template _template.mcworld --out 潮汐鱼竿枪.mcworld
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B


def J(o):
    """紧凑 JSON。用 json.dumps 彻底避开 %% 被格式化吃掉的问题。"""
    return json.dumps(o, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------- 选择器常量
ROD = "{item=fishing_rod,location=slot.weapon.mainhand}"
BODY = ("type=!item,type=!xp_orb,type=!fishing_hook,type=!armor_stand,"
        "type=!arrow,type=!snowball,type=!boat")


def shell(n):
    return "{item=nautilus_shell,data=%d,location=slot.weapon.offhand}" % n


def shellless():
    return "{item=nautilus_shell,location=slot.weapon.offhand,quantity=0}"


# ---------------------------------------------------------------- 枪型表
# type, 名, 弹匣容量, 射速刻, 单发伤害, 一次打几发, 换弹刻, 音效基音, 射程, **音效档**
#
# ❗ 50 把枪 = 5 个系列 × 10 把。参数按系列基线 + 序号微调，**全部从这张表算**：
#    Lore、默认值、自愈建档、图鉴面板、箱子里的弹匣，没有一处手写数字。
# ❗ **音效档**（1..5）而不是每把枪一套音效：50 把 × 4 层 = 200 条太浪费，
#    5 档 × 4 层 = 20 条就够，音高再按枪微调。
# ❗ **弹道链只有一条**（不按枪拆）：`tg_recoil` 一开始就等于这把枪的射程，
#    射程外的格子自动不满足条件 —— 12 格的枪只跑 12 格，100 格的跑 100 格。
#    50 把枪各一条链的话，光弹道就要几万个方块。
MAX_RANGE = 100

GUN_SERIES = [
    # 系列名, 弹匣, 射速, 伤害, 连发, 换弹, 音高, 射程基线, 射程序号步长, 散射(0.1°), 音效档
    ("手枪",   12,  4,  6, 1, 16, 1.10,   12,   2,  30, 1),
    ("冲锋枪", 30,  2,  4, 5, 24, 1.00,   30,   3,  45, 2),
    ("步枪",   20,  5,  9, 3, 30, 0.95,   80,   8,  20, 3),
    ("狙击",    5, 20, 16, 1, 50, 0.80,   95,   1,  10, 4),
    ("特种",    8, 10, 14, 2, 36, 0.70,   60,   4,  60, 5),
]

GUN_NAMES = [
    "蜂鸟", "邮差", "铁皮", "短吻", "灰雀", "咬合", "双管", "快枪", "银币", "裁决",
    "蜂群", "织布机", "缝纫", "齿轮", "打点", "连珠", "铁扫", "织网", "蚁群", "暴雨",
    "长弓", "猎鹿", "白桦", "准星", "老兵", "边线", "铁轨", "长夜", "列队", "定音",
    "远望", "尺规", "银针", "冷杉", "一息", "长笛", "玻璃", "潮线", "定海", "终章",
    "熔渣", "电弧", "霜刃", "灼痕", "相位", "回声", "铁砧", "逆流", "涌潮", "终末",
]


def _make_guns():
    """50 把枪：5 系列 × 10 把，**每一把的参数都可以单独改**（U54）。

    列：编号 / 名字 / 弹匣 / 射速刻 / 伤害 / 连发 / 换弹刻 / 音高 / 射程 / 散射 / **粒子编号** / 音效档
    序号越大越偏"重"：弹匣更大、伤害更高、射程更远、散射更小。
    """
    out, t = [], 0
    for base, cap, cd, dmg, burst, rtime, pitch, rng, rstep, spd, snd in GUN_SERIES:
        for k in range(10):
            t += 1
            out.append((
                t, GUN_NAMES[t - 1],
                max(2, cap + (k - 4)),                        # 弹匣
                max(1, cd + (k % 3) - 1),                     # 射速刻
                dmg + k // 3,                                 # 伤害
                burst,                                        # 连发
                rtime,                                        # 换弹刻
                round(pitch + k * 0.01, 2),                   # 音高
                min(MAX_RANGE, max(8, rng + (k - 5) * rstep)),  # 射程
                max(5, spd - k * 2),                          # 散射（0.1°，序号越大越准）
                k + 1,                                        # 粒子编号 1..10（每把枪不同）
                snd,                                          # 音效档
            ))
    return out


GUNS = _make_guns()


def _spd_tier(spd):
    """散射值（0.1°）→ 档位 1/2/3。"""
    return 1 if spd <= 20 else (2 if spd <= 40 else 3)


def validate():
    """**数据校验**（U51）：表写错了当场报，不要等进游戏才发现。

    校验的是"这张表能不能变成合法的命令"：
    编号唯一、名字唯一、参数在合理区间、弹匣 data 值不越界、音效档存在、
    粒子表长度够、射程上限和表一致。
    """
    errs = []
    ts = [g[0] for g in GUNS]
    names = [g[1] for g in GUNS]
    if len(GUNS) != 50:
        errs.append("枪数应为 50，实际 %d" % len(GUNS))
    if len(set(ts)) != len(ts):
        errs.append("编号有重复")
    if len(set(names)) != len(names):
        errs.append("名字有重复")
    if ts != list(range(1, len(GUNS) + 1)):
        errs.append("编号必须是 1..%d 连续" % len(GUNS))
    for t, name, cap, cd, dmg, burst, rtime, pitch, rng, spd, part, snd in GUNS:
        if not 1 <= t <= 50:
            errs.append("%s：弹匣 data 必须在 1..50（基岩版物品 data 上限），实际 %d"
                        % (name, t))
        if not 1 <= cap <= 64:
            errs.append("%s：弹匣容量 %d 越界" % (name, cap))
        if not 1 <= cd <= 100:
            errs.append("%s：射速刻 %d 越界" % (name, cd))
        if not 1 <= dmg <= 200:
            errs.append("%s：伤害 %d 越界" % (name, dmg))
        if not 1 <= burst <= 10:
            errs.append("%s：连发数 %d 越界" % (name, burst))
        if not 8 <= rng <= MAX_RANGE:
            errs.append("%s：射程 %d 必须在 8..%d" % (name, rng, MAX_RANGE))
        if part not in range(1, 11):
            errs.append("%s：粒子编号 %d 必须在 1..10" % (name, part))
        if snd not in (1, 2, 3, 4, 5):
            errs.append("%s：音效档 %d 不存在" % (name, snd))
    if len(TRAIL10) != 10:
        errs.append("弹道粒子必须是 10 种，实际 %d" % len(TRAIL10))
    if MAX_RANGE != max(g[8] for g in GUNS):
        errs.append("MAX_RANGE 和表里的最大射程不一致")
    if errs:
        raise SystemExit("[数据校验失败]\n  " + "\n  ".join(errs))
    print("[校验] 50 把枪 / 参数区间 / 粒子表 / 射程上限 —— 全部通过")
print("[guns] %d 把：%s … %s" % (len(GUNS), GUNS[0][1], GUNS[-1][1]))

# 默认伤害 = 手枪的单发伤害（自愈建档 / 试射面板都引用它，不手写数字）
DMG_DEFAULT = GUNS[0][4]

# 射程：**每把枪自己带**（GUNS 倒数第二列），不再全局统一。
#
# ❗ 判定条数 = 射程 × 3（三段肢体）+ 射程（碰撞）+ 射程（粒子）。
#    10 格的手枪只有 40 条，1000 格的轨道炮要 5000 条。
#    每条枪单独一条弹道链，用 `tg_point` 认自己的子弹 —— 手枪开火时
#    轨道炮那 5000 条一条都不会执行。
GUN_RANGE = {g[0]: g[8] for g in GUNS}

# 穿透白名单：子弹能穿过去的方块（第 102.1 节）
PASS = [
    "air", "scaffolding", "ladder", "large_fern", "yellow_flower",
    "double_plant", "red_flower", "iron_bars", "rail", "sapling",
    "torch", "redstone_torch", "soul_torch", "water", "lava",
    "tripwire_hook", "carpet", "lever", "spruce_button", "wooden_button",
    "stone_button", "bamboo_button", "crimson_button", "dark_oak_button",
    "warped_button", "web", "trapdoor", "wall_banner", "unpowered_repeater",
    "unpowered_comparator", "redstone_wire", "standing_banner", "wooden_door",
    "iron_door", "spruce_door", "dark_oak_door", "chain",
]

# 弹道粒子：**10 种轮换**（第 n 格用 TRAIL10[(n-1) % 10]）
#
# ❗ 只用**实测能出粒子**的名字，并且带 `minecraft:` 前缀（SKILL 第 91 章
#    的验证清单就是这么写的）。
#    **踩过的坑**：这里原来写 `electric_spark_particle`，默认枪型（突击）正好用它，
#    在网易服上静默不显示 —— 玩家看到的就是「有枪口焰、有声音，但弹道一条粒子都没有」。
#    `electric_spark_particle` 是较新版本才有的 id，老客户端直接忽略，不报错。
#    现在这 10 个都在 `lint_commands.py` 的 PARTICLES 白名单里，写错会被 lint 拦。
TRAIL10 = [
    "minecraft:endrod",                      # 1..100    细白线（最经典的曳光）
    "minecraft:basic_crit_particle",         # 101..200  小暴击星
    "minecraft:redstone_wire_dust_particle", # 201..300  红色粉尘
    "minecraft:soul_particle",               # 301..400  灵魂点
    "minecraft:note",                        # 401..500  音符
    "minecraft:villager_happy",              # 501..600  绿星
    "minecraft:sparkler_emitter",            # 601..700  小火花
    "minecraft:heart",                       # 701..800  心形
    "minecraft:snowballpoof",                # 801..900  雪球烟
    "minecraft:balloon_gas_particle",        # 901..1000 气球气
]

# 旧接口保留：按枪型取一个"主色"，仍给枪口焰 / 其它地方用
TRAIL = {
    1: "minecraft:basic_flame_particle",   # 突击：短促火线
    2: "minecraft:endrod",                 # 精准：细白线
    3: "minecraft:basic_smoke_particle",   # 霰弹：烟团
}

# 枪口焰（每型 3 点）—— 同样只用验证过的名字
MUZZLE = {
    1: ["minecraft:basic_flame_particle", "minecraft:basic_crit_particle",
        "minecraft:basic_smoke_particle"],
    2: ["minecraft:basic_flame_particle", "minecraft:sparkler_emitter",
        "minecraft:basic_smoke_particle"],
    3: ["minecraft:basic_flame_particle", "minecraft:critical_hit_emitter",
        "minecraft:basic_smoke_particle"],
    4: ["minecraft:endrod", "minecraft:critical_hit_emitter",
        "minecraft:basic_flame_particle"],
    5: ["minecraft:endrod", "minecraft:huge_explosion_emitter",
        "minecraft:basic_flame_particle"],
}


# ---------------------------------------------------------------- UI 组件
def tbl(obj, items, colors):
    """查表法：累加区间选择器 + %%N，失败组件被剔除后索引前移。

    ❗ 末尾必须挂一个**空 text 兜底**。selector 全失败时（如 tg_type=0），
    数组只剩 n 个 text，`%%(n+1)` 越界 → 游戏把 `%N` 原样打在屏幕上。
    加一个空串后越界点落空串，屏幕干净。
    """
    n = len(items)
    sels = [{"selector": "@s[scores={%s=1..%d}]" % (obj, i)} for i in range(1, n + 1)]
    txts = [{"text": colors[i] + items[i]} for i in range(n)]
    return {"translate": "%%" + str(n + 1),
            "with": {"rawtext": sels + txts + [{"text": ""}]}}


def pick(obj, items, colors, base=0):
    """**精确值**查表：分数 == base+i 时取第 i 项。

    ❗ 和 `tbl()` 的区别：`tbl` 用的是累计区间（`1..i`，给条状图用），
       这里是离散值精确匹配（给"第几帧"用）。混用会错位。
    """
    n = len(items)
    sels = [{"selector": "@s[scores={%s=%d}]" % (obj, base + i)} for i in range(n)]
    txts = [{"text": colors[i] + items[i]} for i in range(n)]
    return {"translate": "%%" + str(n + 1),
            "with": {"rawtext": sels + txts + [{"text": ""}]}}


def crosshair():
    """简约战术准星：**主标题**画十字，**副标题**补一个点。

    ❗ 冷却时中间那格在转（U43）：帧号 `tg_cd_frame = tg_cooldown % 4`，
       帧序列 `┼ ╱ ┊ ╲` 循环，看起来就是准星在旋转。
       没冷却时 `tg_cooldown = 0` → 帧 0 → 静态 `┼`。

    ❗ 主标题/副标题是**每 tick 重发**的，所以不需要算持续时间，
       只要 `times 0 20 0`（无淡入淡出）就不会闪。
    """
    FRAMES = ["┼", "╱", "┊", "╲"]
    COLS = ["§7", "§8", "§8", "§8"]
    title = {"rawtext": [
        {"text": "§8┊\n§7┈"},
        pick("tg_cd_frame", FRAMES, COLS),
        {"text": "§7┈\n§8┊"},
    ]}
    return [
        "execute as @a[hasitem=%s] run titleraw @s times 0 20 0" % ROD,
        "execute as @a[hasitem=%s] run titleraw @s title " % ROD + J(title),
        "execute as @a[hasitem=%s] run titleraw @s subtitle " % ROD
        + J({"rawtext": [{"text": "§8·"}]}),
    ]


def cond(sel, text):
    """选择器命中才输出 text。

    ❗ `with` 必须是 `{"rawtext":[...]}`。写成裸数组游戏不解析，
    会把 `%%2` 原样打在屏幕上（实测：HUD 变成一堆 %2）。

    ❗ 末尾必须挂**空 text 兜底**。selector 失败时组件被剔除，数组只剩 1 个，
    `%%2` 越界 → 游戏把 `%2` 打上屏。HUD 里有 5 个互斥状态，同一刻 4 个不满足，
    不兜底就是满屏 `%2`（用户实测：t 显一堆 %，还以为枪坏了）。
    """
    return {"translate": "%%2", "with": {"rawtext": [
        {"selector": sel}, {"text": text}, {"text": ""}]}}


def cell(obj, i, lit="§a", dark="§8", ch="▮"):
    """条状图第 i 格：亮 / 暗两个互斥组件。

    同样挂空 text 兜底——否则每个格子都会漏一个 `%2`，20 格就是满屏 `%2`。
    """
    return [
        {"translate": "%%2", "with": {"rawtext": [
            {"selector": "@s[scores={%s=%d..}]" % (obj, i)}, {"text": lit + ch},
            {"text": ""}]}},
        {"translate": "%%2", "with": {"rawtext": [
            {"selector": "@s[scores={%s=..%d}]" % (obj, i - 1)}, {"text": dark + ch},
            {"text": ""}]}},
    ]


def hud():
    """两行式 HUD：枪型 / 弹匣 / 备弹 / 状态 + 10 格弹药条。"""
    p = "§8▏ "
    comps = [
        {"text": p},
        {"text": "§b"},
        tbl("tg_type", ["突击", "精准", "霰弹"], ["§b", "§d", "§6"]),
        {"text": "  §f"},
        {"score": {"name": "@s", "objective": "tg_magazine"}},
        {"text": "§8／§f"},
        {"score": {"name": "@s", "objective": "tg_capacity"}},
        cond("@s[scores={tg_reload=1..}]", "  §e装填中"),
        cond("@s[scores={tg_reload=0,tg_magazine=0,tg_reserve=0}]", "  §c空仓"),
        cond("@s[scores={tg_reload=0,tg_magazine=0,tg_reserve=1..}]", "  §e按低头换弹"),
        cond("@s[scores={tg_reload=0,tg_magazine=1..}]", "  §a就绪"),
        {"text": "  §8备 §f"},
        {"score": {"name": "@s", "objective": "tg_reserve"}},
        {"text": "\n" + p},
    ]
    for i in range(1, 11):
        comps.extend(cell("tg_bar", i))
    # 血量（U34）：原版血量看不见数字，这里补一个 HUD 读数。
    comps += [
        {"text": "  §c❤ §f"},
        {"score": {"name": "@s", "objective": "tg_health"}},
        {"text": "§8／§f"},
        {"score": {"name": "@s", "objective": "tg_health_max"}},
    ]
    # @s 必须落在 execute as 里，命令方块自己不是实体，裸 @s 直接 No targets matched
    return ("execute as @a[hasitem=%s] run titleraw @s actionbar " % ROD
            + J({"rawtext": comps}))


# ---------------------------------------------------------------- 初始化
def chain_init():
    objs = [
        "tg_tick", "tg_gun", "tg_boot", "tg_type", "tg_magazine", "tg_reserve", "tg_capacity",
        "tg_reload", "tg_reload_time", "tg_cooldown", "tg_damage",
        "tg_recoil", "tg_point", "tg_burst", "tg_user_id", "tg_limb",
        # 子弹 / 锚点都用**计分**打标，不用 tag（U38）
        "tg_bullet", "tg_anchor", "tg_ready", "tg_flag",
        # 伪连发 / 散射 / 准星（U41 U42 U43）
        "tg_shot", "tg_sh", "tg_sv", "tg_cd_frame", "tg_spr", "tg_snd", "tg_page", "tg_spd", "tg_part",
        # 受击待结算分（U44）：命中时 = 攻击者的攻击力，结算链扣完归零
        "tg_hurt",
        "tg_team", "tg_bar", "tg_temp", "tg_temp2", "tg_fire",
        # 相机：开火时 fov 拉近，N 刻后必须 fov_clear（U28）
        "tg_fov",
        # 血量镜像（U34）：只读原版 health，不自己判死
        "tg_health", "tg_health_max",
        # 开镜（U35）：副手望远镜 → fov 拉近
        "tg_aim",
    ]
    cmds = ["scoreboard objectives add %s dummy" % o for o in objs]

    cmds += ["gamerule %s false" % g for g in (
        "sendcommandfeedback", "commandblockoutput", "showdeathmessages",
        "announceadvancements", "showrecipemessages", "showcoordinates")]

    cmds += [
        "scoreboard players set sys_ten tg_temp 10",
        "scoreboard players set sys_five tg_temp 5",
        "scoreboard players set sys_four tg_temp 4",
        "scoreboard players set sys_tick tg_tick 0",
        # 常加载区：先删后建保证幂等
        "tickingarea remove tide",
        # ❗ 宽度必须跟 build_cbworld.W 一致，否则右边那几列方块不在常加载区里，
        #    链走到那儿就断了（表现：只有前面一段命令在跑）。
        "tickingarea add ~-2 ~-2 ~-2 ~%d ~%d ~%d tide true"
        % (B.W + 2, B.FLOOR_GAP + 10, DEPTH + 2),
        # 锚点哨兵：只召唤一次。**用计分不用 tag**（U38）—— 全场零 tag
        "execute unless entity @e[type=armor_stand,scores={tg_anchor=1}] "
        "run summon armor_stand ~ ~1 ~",
        "execute as @e[type=armor_stand,r=8] unless score @s tg_anchor matches 1.. "
        "run scoreboard players set @s tg_anchor 1",
        "effect @e[scores={tg_anchor=1}] invisibility 999999 1 true",
        "effect @e[scores={tg_anchor=1}] resistance 999999 255 true",
        "execute as @e[scores={tg_anchor=1}] run tp @s ~ ~-2 ~",
        # 原生 HUD：零每刻成本
        "scoreboard objectives setdisplay belowname tg_reserve",
        "tellraw @a " + J({"rawtext": [
            {"text": "§8«══ §b潮 汐 §f· §b鱼 竿 枪 §8══»\n"},
            {"text": "§7  副手放§f鹦鹉螺壳§7切枪：§b1§7 突击 / §d2§7 精准 / §66§7 霰弹\n"},
            {"text": "§7  主手§f鱼竿§7抛竿即开火　§7低头§f换弹　§7抬头打更远\n"},
            {"text": "§8  散射靠拧朝向，弹道靠射线穷举，打中三段肢体"},
        ]}),
    ]
    return {"id": "init", "kind": "impulse", "button": True, "cmds": cmds}


# ---------------------------------------------------------------- 时钟
def chain_clock():
    """恒真闸门，**不插复位块**（gate_mode="loop"）。

    `execute if entity @a` 每刻都成功，复位块等于每刻白跑一条 setblock；
    这条链也从不进「断开/接通」面板，插断点毫无意义 —— 直接循环（用户 U14）。
    会失败的命令放最后。
    """
    return {"id": "clock", "kind": "gated", "gate_mode": "loop",
            "gate": "execute if entity @a",
            "cmds": [
                "scoreboard players add sys_tick tg_tick 1",
                "execute if score sys_tick tg_tick matches 20.. run scoreboard players set sys_tick tg_tick 0",
                # uid / 队伍号已移到 join 链（闸门 = 有新人），别塞回时钟链
                # ❗ 这里原来有一条「掉枪清零」：
                #     unless entity @s[hasitem=ROD] → tg_gun=0 → 再把 tg_magazine 设 0
                #    后果：只要鱼竿不在主手（放副手 / 换到别的快捷栏格 / 刚从箱子拿出来
                #    还没选中），弹匣就被清空。玩家一抛竿就是空仓 → **开枪没有反应**。
                #    已删除。tg_gun 只留作「是否持枪」的标记，不再动弹药。
                # 射速间隔（会失败，放最后）
                "scoreboard players remove @a[scores={tg_cooldown=1..}] tg_cooldown 1",
            ] + [
                # ── 血量镜像：原版血量说了算（U34）─────────────────────
                # 扣血走 `damage`（弹道链里），计分板这边**只读不写**。
                # health 是 0..20 的整数，×5 映射成 0..100 给 HUD 用。
                # ❗ 不用二分法：`operation = health` 能直接读，
                #    `*= 5` 就是等比缩放；二分法是给"分数 → 坐标 / 方块"用的
                #    （第 26 章），在这件事上没有优势，反而多十几条命令。
                # 新人建档：`tg_ready` 不存在 → 补 0，join 链的闸门才匹配得到（U19）
                "execute as @a unless score @s tg_ready matches 0.. "
                "run scoreboard players set @s tg_ready 0",
                "execute as @a unless score @s tg_health_max matches 1.. "
                "run scoreboard players set @s tg_health_max 100",
                "execute as @a run scoreboard players operation @s tg_health = @s health",
                "scoreboard players operation @a tg_health *= sys_five tg_temp",
                # ❗ 用户明确要求**去掉受伤声音**（U39）。血量靠 HUD 看，
                #    挨打时不再额外播 `random.hurt`（那个音效也太吵）。
                # ── 准星帧号（U43）：冷却剩余 % 4，驱动准星旋转
                "execute as @a run scoreboard players operation @s tg_cd_frame = @s tg_cooldown",
                "scoreboard players operation @a tg_cd_frame %= sys_four tg_temp",
                # ── 相机复位（U28）──────────────────────────────────────
                # `camera ... fov_set` 是**持续生效**的，不清就一直卡在拉近状态。
                # 开镜链松手时置 `tg_fov 10`，这里倒计时走完再 clear。
                "execute as @a[scores={tg_fov=1..}] run scoreboard players remove @s tg_fov 1",
                "execute as @a[scores={tg_fov=0}] run camera @s fov_clear",
                # 清完置 -1：`scores={tg_fov=0}` 不再命中 → 只清一次，不每刻刷
                "execute as @a[scores={tg_fov=0}] run scoreboard players set @s tg_fov -1",
            ]}


# ---------------------------------------------------------------- 开镜（蹲下）
def chain_aim():
    """**蹲下 = 开镜**：fov 缓动拉近 + 望远镜音效；站起来 = 缓动回原视角。

    ❗ 基岩版没有 `sneaking` 选择器，但**碰撞箱高度能读出来**（U35）：
       站立 1.8 格、蹲下 1.5 格。`@s[y=~1.5,dy=1]` 问的是
       "脚往上 1.5~2.5 格这个体积里有没有我的碰撞箱" —— 站立有、蹲下没有。
       所以：
           站立 = `if entity @s[y=~1.5,dy=1]`
           蹲下 = `unless entity @s[y=~1.5,dy=1] if entity @s[y=~1,dy=1]`
       第二个条件把"游泳 / 爬行 / 睡觉"排除掉（它们更矮，够不到 1.0）。

    ❗ fov 拉近和恢复都必须**给缓动时间**（0.25 / 0.30 秒），不给就是瞬间跳变。
    """
    # ❗ `scores=` 只能出现在**选择器方括号里**，不能当 execute 的子命令写。
    #    踩过：`... if entity @s[y=~1.5,dy=1] scores={tg_aim=1} run ...`
    #    → 整条语法错误 → 收镜三条全失效 → **站起来视角不恢复**。
    R = "execute as @a[hasitem=%s] at @s " % ROD
    DUCK = "unless entity @s[y=~1.5,dy=1] if entity @s[y=~1,dy=1] "   # 蹲下
    STAND = "if entity @s[y=~1.5,dy=1] "                              # 站立
    # 收镜用「站立 + 已在开镜」的玩家；scores 写进选择器
    RS = "execute as @a[hasitem=%s,scores={tg_aim=1}] at @s " % ROD
    return {"id": "aim", "kind": "gated", "label": "开镜",
            "gate": "execute if entity @a[hasitem=%s]" % ROD,
            "cmds": [
                # ① 蹲下且还没开镜 → 拉近到 30°，0.25 秒缓动
                R + DUCK + "unless score @s tg_aim matches 1.. "
                    "run camera @s fov_set 30 0.25 linear",
                # ② 望远镜音效（两层：镜筒 + 机械扣合）
                R + DUCK + "unless score @s tg_aim matches 1.. "
                    "run playsound random.spyglass_use @s ~~~ 1 1",
                R + DUCK + "unless score @s tg_aim matches 1.. "
                    "run playsound random.click @s ~~~ 0.8 1.6",
                R + DUCK + "run scoreboard players set @s tg_aim 1",
                # ③ 站起来 → 先**缓动回 70**（看得见回弹）
                RS + STAND + "run camera @s fov_set 70 0.30 linear",
                # ④ **先点 fov 计时器，再清 tg_aim**（U46）。
                #    ❗ 顺序反了就是「视角不恢复」：三条命令的选择器都是
                #       `scores={tg_aim=1}`，而链是**逐条重新求值**的 ——
                #       中间那条把 tg_aim 改成 0，后面那条当场就匹配不到了，
                #       `tg_fov` 永远设不上 → 主循环的 fov_clear 永远不触发。
                RS + STAND + "run scoreboard players set @s tg_fov 10",
                RS + STAND + "run scoreboard players set @s tg_aim 0",
            ]}


# ---------------------------------------------------------------- 新玩家初始化# ---------------------------------------------------------------- 新玩家初始化# ---------------------------------------------------------------- 新玩家初始化
def chain_join():
    """新人进服才跑：分配 uid / 队伍号 + 初始弹药，置 `tg_ready 1` 后永不再跑。

    ❗ 闸门**不能**写 `execute if entity @a`——恒真 = 每刻全跑，等于把初始化
       塞进时钟链里白烧性能（用户实测指出）。
    ❗ **不用 tag 判新人**（U38）。但新玩家连 `tg_ready` 这一项都没有，
       `scores={tg_ready=0}` 在"这一项不存在"时**不匹配**（U19）。
       解法：主循环链每刻先给所有玩家补一句 `tg_ready 0` 建档，
       闸门就能安心写 `scores={tg_ready=0}`。
    """
    NEW = "@a[scores={tg_ready=0}]"
    return {"id": "join", "kind": "gated",
            "gate": "execute if entity " + NEW,
            "cmds": [
                # 建档：新人可能一条计分项都没有
                "scoreboard players add %s tg_user_id 0" % NEW,
                "scoreboard players add %s tg_team 0" % NEW,
                # uid < 1 才赋予
                "execute as @a[scores={tg_ready=0,tg_user_id=..0}] run scoreboard players random @s tg_user_id 10000 99999",
                # 随机失败兜底：绝不能停在 0（0 = 未初始化，子弹归属会算错）
                "execute as @a[scores={tg_ready=0,tg_user_id=..0}] run scoreboard players set @s tg_user_id 10000",
                "execute as @a[scores={tg_ready=0,tg_team=..0}] run scoreboard players random @s tg_team 10000 99999",
                "execute as @a[scores={tg_ready=0,tg_team=..0}] run scoreboard players set @s tg_team 10000",
                # 初始状态：弹匣**给满**，进服就能开火。
                # ❗ 给 0 会被 trigger 链判「空仓」→ 抛竿没反应，玩家以为枪坏了。
                "scoreboard players set %s tg_type 1" % NEW,
                "scoreboard players set %s tg_capacity 30" % NEW,
                "scoreboard players set %s tg_magazine 30" % NEW,
                "scoreboard players set %s tg_reserve 300" % NEW,
                "scoreboard players set %s tg_cooldown 0" % NEW,
                "scoreboard players set %s tg_reload 0" % NEW,
                "scoreboard players set %s tg_burst 0" % NEW,
                "scoreboard players set %s tg_fire 0" % NEW,
                # 血量镜像 / 开镜（U34 U35）：HUD 分母、伤标、fov 初值
                "scoreboard players set %s tg_health_max 100" % NEW,
                "scoreboard players set %s tg_aim 0" % NEW,
                "scoreboard players set %s tg_fov -1" % NEW,
                "execute as %s run tellraw @s " % NEW + J({"rawtext": [
                    {"text": "§8«§b潮汐§8» §a欢迎，§f"},
                    {"selector": "@s"},
                    {"text": "§7 已分配 UID §f"},
                    {"score": {"name": "@s", "objective": "tg_user_id"}},
                    {"text": "\n§7  主手鱼竿 §8/ §7副手壳切枪 §8/ §7抛竿开火"}]}),
                # 打标：闸门之后不再命中
                "scoreboard players set %s tg_ready 1" % NEW,
            ]}


# ---------------------------------------------------------------- 状态 / 换弹
def chain_state():
    """枪型 → 容量 → 伤害 → 溢出回灌 → 换弹触发 → 倒计时 → 结算 → HUD。"""
    # ❗ 计分项**建档**：`scores={tg_cooldown=0}` 在"这一项根本不存在"时是
    #    **不匹配**，不是当成 0。老存档进来的玩家（join 因为 tag 已存在被跳过）
    #    就会永远满足不了开火条件 → 抛竿毫无反应。这里补 `add 0` 建档。
    #    只在持枪时跑，不持枪一条都不执行。
    cmds = ["scoreboard players add @a[hasitem=%s] %s 0" % (ROD, o) for o in (
        "tg_cooldown", "tg_reload", "tg_burst", "tg_fire", "tg_magazine",
        "tg_reserve", "tg_type", "tg_capacity", "tg_user_id")]

    # 首次持枪引导：只要"从没引导过"，就给满一次。
    # ❗ 为什么需要：join 链的闸门是 `tag=!tg_ready`，老存档玩家早就带着 tg_ready，
    #    进新结构时 join 不再执行 → 弹匣停在 0（或被上一条清零）→ 抛竿永远空仓。
    #    用 tg_boot 当"引导过"的标记，跟 tg_ready 解耦。
    cmds += [
        "execute as @a[hasitem=%s] unless score @s tg_boot matches 1.. "
        "run scoreboard players set @s tg_magazine 30" % ROD,
        "execute as @a[hasitem=%s] unless score @s tg_boot matches 1.. "
        "run scoreboard players set @s tg_reserve 300" % ROD,
        "execute as @a[hasitem=%s] unless score @s tg_boot matches 1.. "
        "run scoreboard players set @s tg_boot 1" % ROD,
    ]

    # 备弹兜底：弹匣和备弹同时见底 = 卡死，补一次（不给无限弹药，只救急一次）
    cmds += [
        "execute as @a[hasitem=%s,scores={tg_magazine=..0,tg_reserve=..0}] "
        "run scoreboard players set @s tg_reserve 300" % ROD,
    ]

    # ── 副手壳 → 枪型 + **该型全部参数**（U31）──
    #
    # ❗ 旧写法在这里只赋 `tg_type`，容量/伤害/精准/换弹/粒子编号在**下面另一个循环**
    #    里按 `tg_type` 补，而且那 5 条**没带 `hasitem` 过滤**：
    #      · 检测与赋值隔了 20 格，中间任何一条改了 tg_type 就对不上；
    #      · 空手玩家的 tg_capacity / tg_damage 也被改写（面板、旁观者全中招）。
    #    表现就是「切枪之后参数和枪型不匹配」。现在每个枪型一块：
    #    检测 → **立刻**把 5 个参数一次赋完，赋值也带 `hasitem` 过滤。
    cmds += [
        # 默认兜底：副手放了 data=0 的壳（普通鹦鹉螺壳）时三条检测都不命中，
        # tg_type 会停在 0 → tg_capacity 停在 0 → 换弹永远补不满 → 无限装填
        "scoreboard players set @a[hasitem=%s] tg_type 1" % ROD,
        "scoreboard players set @a[hasitem=%s] tg_gun 1" % ROD,
    ]
    # 50 把枪的"检测 + 赋值"已经拆成 50 条独立短链（`gun01`..`gun50`，U52），
    # 状态链只留"无壳兜底"。

    # ③ 无壳兜底：没有壳 → 回到枪型 1（参数上面 t=1 那组已给过）
    cmds += [
        "execute as @a[hasitem=%s] run scoreboard players set @s tg_type 1" % shellless(),
    ]

    # 溢出回灌：换枪后 zd 可能大于新容量，多出来的退回 zdmax（第 100.2 节）
    cmds += [
        "execute as @a[scores={tg_magazine=1..}] if score @s tg_magazine > @s tg_capacity run scoreboard players set @s tg_flag 1",
        "execute as @a[scores={tg_flag=1}] run scoreboard players operation @s tg_temp2 = @s tg_magazine",
        "execute as @a[scores={tg_flag=1}] run scoreboard players operation @s tg_magazine = @s tg_capacity",
        "execute as @a[scores={tg_flag=1}] run scoreboard players operation @s tg_temp2 -= @s tg_capacity",
        "execute as @a[scores={tg_flag=1}] run scoreboard players operation @s tg_reserve += @s tg_temp2",
        "scoreboard players set @a[scores={tg_flag=1}] tg_flag 0",
    ]

    # 触发换弹：五个条件同时成立（第 100.3 节）
    cmds += [
        "execute as @a[scores={tg_type=1..,tg_reserve=1..},rxm=88,hasitem=%s] "
        "if score @s tg_magazine < @s tg_capacity "
        "unless score @s tg_reload matches 1.. "
        "unless score @s tg_burst matches 1.. "
        "run scoreboard players operation @s tg_reload = @s tg_reload_time" % ROD,
        # 倒计时
        "scoreboard players remove @a[scores={tg_reload=1..}] tg_reload 1",
        # 差值 = 容量 - 现有
        "execute as @a[scores={tg_reload=1}] run scoreboard players operation @s tg_temp = @s tg_capacity",
        "execute as @a[scores={tg_reload=1}] run scoreboard players operation @s tg_temp -= @s tg_magazine",
        # 分支 A：备弹不够补满 → zd += zdmax，zdmax = 0
        "execute as @a[scores={tg_reload=1}] if score @s tg_reserve < @s tg_temp run scoreboard players set @s tg_flag 1",
        "execute as @a[scores={tg_flag=1}] run scoreboard players operation @s tg_magazine += @s tg_reserve",
        "execute as @a[scores={tg_flag=1}] run scoreboard players set @s tg_reserve 0",
        "execute as @a[scores={tg_flag=1}] run scoreboard players set @s tg_reload 0",
        "scoreboard players set @a[scores={tg_flag=1}] tg_flag 0",
        # 分支 B：备弹够 → zd = 容量，zdmax -= 差值
        "execute as @a[scores={tg_reload=1}] if score @s tg_reserve >= @s tg_temp run scoreboard players set @s tg_flag 2",
        "execute as @a[scores={tg_flag=2}] run scoreboard players operation @s tg_temp2 = @s tg_magazine",
        "execute as @a[scores={tg_flag=2}] run scoreboard players operation @s tg_magazine = @s tg_capacity",
        "execute as @a[scores={tg_flag=2}] run scoreboard players operation @s tg_magazine -= @s tg_temp2",
        "execute as @a[scores={tg_flag=2}] run scoreboard players operation @s tg_reserve -= @s tg_magazine",
        "execute as @a[scores={tg_flag=2}] run scoreboard players operation @s tg_magazine = @s tg_capacity",
        "execute as @a[scores={tg_flag=2}] run scoreboard players set @s tg_reload 0",
        "scoreboard players set @a[scores={tg_flag=2}] tg_flag 0",
    ]

    # 条状图：bar = zd * 10 / cap
    cmds += [
        "execute as @a run scoreboard players operation @s tg_bar = @s tg_magazine",
        "scoreboard players operation @a tg_bar *= sys_ten tg_temp",
        "execute as @a[scores={tg_capacity=1..}] run scoreboard players operation @s tg_bar /= @s tg_capacity",
        hud(),
    ]
    return {"id": "state", "kind": "gated",
            "gate": "execute if entity @a[hasitem=%s]" % ROD,
            "cmds": cmds}


# ---------------------------------------------------------------- 扳机
def chain_trigger():
    """钩子出现 = 有人抛竿。判空仓 → 打标 → 杀钩子（伪无）。

    ❗ **这条链里一个 `hasitem` 都不许出现**（U26）。
       它是「枪不响」的头号单点故障：`hasitem={item=fishing_rod,location=...}`
       一旦不匹配，整段静默跳过，玩家只会觉得"抛竿没反应"。
       而钩子本身就是"有人抛竿"的铁证 —— 不需要再验一遍物品。
    ❗ 所有计分项都做**自愈建档**：`unless score @s X matches 0..` 为真 =
       这一项根本不存在 → 就地补一个默认值。老存档 / 新玩家 / 被面板清空过，
       全都能自己爬起来，不用等 state 链（那条是 hasitem 闸门）。
    """
    T = "execute at @e[type=fishing_hook] as @p"
    return {"id": "trigger", "kind": "gated",
            "gate": "execute if entity @e[type=fishing_hook]",
            "cmds": [
                # ⓿ **扳机标记**：只要钩子出现，先响一声 + actionbar 闪「扳机」。
                #    抛竿后什么都没听到 = 钩子没被识别（问题在这条链之前）；
                #    听到「扳机」但没子弹 = 问题在后面（空仓 / 出弹链）。
                "execute at @e[type=fishing_hook] as @p run playsound random.orb @s ~ ~ ~ 1 2",
                "execute at @e[type=fishing_hook] as @p run titleraw @s actionbar "
                + J({"rawtext": [{"text": "§b▷ 扳 机"}]}),
                # ❶ 自愈建档：分数**不存在**（`matches 0..` 不成立）就补默认值。
                #    顺序很重要 —— 必须在判空仓之前，否则第一次抛竿一定空仓。
                T + " unless score @s tg_magazine matches 0.. "
                "run scoreboard players set @s tg_magazine 30",
                T + " unless score @s tg_reserve matches 0.. "
                "run scoreboard players set @s tg_reserve 300",
                T + " unless score @s tg_type matches 1.. "
                "run scoreboard players set @s tg_type 1",
                T + " unless score @s tg_capacity matches 1.. "
                "run scoreboard players set @s tg_capacity 30",
                T + " unless score @s tg_damage matches 1.. "
                "run scoreboard players set @s tg_damage %d" % DMG_DEFAULT,
                T + " unless score @s tg_point matches 1.. "
                "run scoreboard players set @s tg_point 1",
                # ❷ 空仓提示：先判，后开火（钩子杀了就取不到 @p）
                T + " unless score @s tg_magazine matches 1.. run tellraw @s "
                + J({"rawtext": [{"text": "§8▏ §d◁╿§u▷➤ §c没子弹了"}]}),
                T + " unless score @s tg_magazine matches 1.. at @s run playsound "
                "random.click @a[r=8] ~~~ 0.8 1.9",
                T + " unless score @s tg_magazine matches 1.. at @s run playsound "
                "note.bass @a[r=8] ~~~ 0.5 0.6",
                # ❸ 开火标：冷却归零 + 不在换弹 + 有弹
                # ❗ 不要写 `scores={tg_cooldown=0}`：分数不存在时 `=0` 不匹配，
                #    老存档玩家会永远打不出子弹。用 `unless score ... matches 1..`，
                #    分数不存在 = 没在冷却 = 允许开火。
                T + " unless score @s tg_cooldown matches 1.. "
                "unless score @s tg_reload matches 1.. "
                "if score @s tg_magazine matches 1.. "
                "run scoreboard players set @s tg_fire 1",
                # ❹ **开火标回执**：看得见的一步。听到「扳机」没看到「开火」
                #    = 条件没过（冷却 / 换弹 / 空仓），不用再猜。
                "execute as @a[scores={tg_fire=1}] run titleraw @s actionbar "
                + J({"rawtext": [{"text": "§a◈ 开 火"}]}),
                # ❺ 连发数（霰弹 3 颗，一 tick 一颗）
                # 连发数按枪型表给（U41）：一次抛竿 = 一个弹匣节奏的连发段
                *["execute as @a[scores={tg_fire=1,tg_type=%d}] "
                  "run scoreboard players set @s tg_burst %d" % (g[0], g[5])
                  for g in GUNS],
                # 枪型兜底：50 把枪的壳里总有一个匹配不上（比如 data 越界）
                "execute as @a[scores={tg_fire=1,tg_burst=..0}] "
                "run scoreboard players set @s tg_burst 1",
                # 兜底：tg_type 是 0 / 缺项时上面三条都不命中 → 出弹链永远不跑
                "execute as @a[scores={tg_fire=1,tg_burst=..0}] run scoreboard players set @s tg_burst 1",
                "execute as @a[scores={tg_fire=1}] run scoreboard players set @s tg_fire 0",
                # ❻ 伪无：钩子只当信号，立刻杀
                "kill @e[type=fishing_hook]",
            ]}


# ---------------------------------------------------------------- 出弹
def chain_shot():
    """出弹 → 打标 → 顶高 → 灌参数 → 散射 → 枪口 → 音效 → 后坐 → 扣弹 → 冷却。

    50 把枪共用这一条链（U47）：
      · **散射**只有一张 9 方向的表（不是每把枪一套）
      · **枪口焰 / 枪声**按"音效档"分 5 档（不是每把枪一套）
      · 每把枪只多一条"自己的冷却"，其余全共享
    """
    B = "scores={tg_shot=1}"
    BURST = "scores={tg_burst=1..}"
    ANCHOR = "positioned ~~500~"
    cmds = [
        # ⓿ 本 tick 开不开火：有连发余量 **且** 冷却结束
        "execute as @a[%s] unless score @s tg_cooldown matches 1.. "
        "run scoreboard players set @s tg_shot 1" % BURST,
        # 出弹标记
        "execute as @a[%s] at @s run playsound random.bow @s ~ ~ ~ 1 1.2" % B,
        "execute as @a[%s] run titleraw @s actionbar "
        % B + J({"rawtext": [{"text": "§e▸ 出 弹"}]}),
    ]

    # ① 散射（U48）：9 个方向，随机挑一个，**在召唤时就用 `rotated` 定死方向**。
    #
    # ❗ 不能"先召出来再 tp 拧朝向"：`tp` 的旋转参数是**绝对角度**，
    #    写成 `tp @s ~ ~ ~ 0.27 ~` 会把子弹朝向整个重置成 0.27°，
    #    弹道直接歪到地上 —— 表现就是「子弹原地自爆、射不出去」。
    #    `rotated` 是**执行时**的朝向偏移，`^^^` 和 `facing` 都跟着它走，一定生效。
    # 散射（U54）：**每把枪自己的散射值**（0.1° 单位），落到 3 档半径。
    # 9 个方向（中心 + 4 正 + 4 斜），档位 × 方向 = 27 条，50 把枪共用。
    # ❗ 必须用 `rotated`：`tp` 的旋转参数是绝对角度，会把朝向整个重置（A38）。
    TIERS = {1: 1.5, 2: 3.0, 3: 5.0}          # 档 → 半径（度）
    DIRS = [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0),
            (0.707, 0.707), (-0.707, 0.707), (0.707, -0.707), (-0.707, -0.707)]
    cmds.append("scoreboard players random @a[%s] tg_spr 0 %d" % (B, len(DIRS)))
    for tier, rad in TIERS.items():
        # 中心（无偏移）
        cmds.append(
            "execute as @a[scores={tg_shot=1,tg_spd=%d,tg_spr=0}] at @s "
            "run summon xp_orb ^^^1.45 facing ^^^1000" % tier)
        for i, (dx, dy) in enumerate(DIRS, 1):
            cmds.append(
                "execute as @a[scores={tg_shot=1,tg_spd=%d,tg_spr=%d}] at @s "
                "rotated ~%.2f ~%.2f run summon xp_orb ^^^1.45 facing ^^^1000"
                % (tier, i, dx * rad, dy * rad))

    cmds += [
        # ② 先打标（计分，不用 tag），再顶高
        "execute as @a[%s] at @s run scoreboard players set "
        "@e[type=xp_orb,r=3,c=1] tg_bullet 1" % B,
        "execute as @a[%s] at @s run tp "
        "@e[type=xp_orb,r=3,c=1,scores={tg_bullet=1}] ~~500~" % B,
    ]

    BUL = "@e[r=1,scores={tg_bullet=1}]"

    # ③ 灌参数
    for obj in ("tg_user_id", "tg_damage", "tg_team", "tg_point", "tg_part"):
        cmds.append("execute as @a[%s] at @s %s run scoreboard players operation "
                    "%s %s = @s %s" % (B, ANCHOR, BUL, obj, obj))
    cmds += [
        "execute as @a[%s] at @s %s run scoreboard players set %s tg_recoil %d"
        % (B, ANCHOR, BUL, MAX_RANGE),
        "execute as @a[%s] at @s %s run scoreboard players set %s tg_limb 0"
        % (B, ANCHOR, BUL),
    ]

    # ④ 枪口焰：5 档 × 3 点
    for prof in (1, 2, 3, 4, 5):
        for k, p in enumerate(MUZZLE[prof]):
            cmds.append(
                "execute as @a[scores={tg_shot=1,tg_snd=%d}] at @s anchored eyes "
                "positioned ^ ^ ^%s run particle %s ~ ~ ~"
                % (prof, ["1.4", "1.6", "1.2"][k], p))

    # ⑤ 枪声：5 档 × 4 层（音高按枪的 pitch 走不了字面，所以档内统一）
    SND_PITCH = {1: 1.10, 2: 1.00, 3: 0.95, 4: 0.80, 5: 0.70}
    for prof in (1, 2, 3, 4, 5):
        pitch = SND_PITCH[prof]
        for snd, vol, pt, far in (
                ("random.explode", "1.00", pitch * 0.55, True),
                ("mob.ghast.fireball", "0.85", pitch * 0.85, False),
                ("random.break", "0.60", pitch * 1.95, False),
                ("mob.blaze.hit", "0.70", pitch * 1.30, False)):
            tail = ("%.2f 100" % pt) if far else ("%.2f 1" % pt)
            cmds.append("execute as @a[scores={tg_shot=1,tg_snd=%d}] at @s run playsound %s "
                        "@a[r=%d] ~~~ %s %s" % (prof, snd, 48 if far else 32, vol, tail))

    # ⑥ 后坐 / 扣弹 / 冷却
    cmds += [
        "execute as @a[%s] at @s run camerashake add @s 0.12 0.08 positional" % B,
        "scoreboard players remove @a[%s] tg_magazine 1" % B,
        "scoreboard players remove @a[%s] tg_burst 1" % B,
    ]
    # 每打一发就重置冷却（50 条，每把枪一条）
    for t, name, cap, cd, dmg, burst, rtime, pitch, rng, spd, part, snd in GUNS:
        cmds.append("execute as @a[scores={tg_shot=1,tg_type=%d}] "
                    "run scoreboard players set @s tg_cooldown %d" % (t, cd))
    # 射程：把 recoil 覆盖成这把枪自己的射程
    for t, name, cap, cd, dmg, burst, rtime, pitch, rng, spd, part, snd in GUNS:
        cmds.append("execute as @e[type=xp_orb,scores={tg_bullet=1,tg_point=%d}] "
                    "run scoreboard players set @s tg_recoil %d" % (t, rng))
    cmds.append("execute as @a[%s] run scoreboard players set @s tg_shot 0" % B)

    return {"id": "shot", "kind": "gated",
            "gate": "execute if entity @a[scores={tg_burst=1..}]",
            "cmds": cmds}


# ---------------------------------------------------------------- 单枪赋值链
def chain_gun(g):
    """**每把枪一条赋值链**（U52）。

    为什么从状态链里拆出来：50 把枪塞一条链要 300 多格，还挤在一起没法单独排查。
    拆开之后每把枪一条 6 格的短链，闸门就是"副手有没有这个壳"——
    哪把枪的参数不对，直接看那一条链，或者单独把它断开。

    ❗ 闸门用 `hasitem=壳`（不验主手），业务里再按 `hasitem=鱼竿` 过滤：
       没拿竿子的人不该被改参数。
    """
    t, name, cap, cd, dmg, burst, rtime, pitch, rng, spd, part, snd = g
    return {"id": "gun%02d" % t, "kind": "gated", "label": "枪%02d·%s" % (t, name),
            # 二楼：50 条单枪链单独一层，主干那一层就不会被顶到 150 行深
            "level": 1,
            "gate": "execute if entity @a[hasitem=%s]" % shell(t),
            "cmds": [
                "execute as @a[hasitem=%s] run scoreboard players set @s tg_type %d"
                % (ROD, t),
                "execute as @a[hasitem=%s,scores={tg_type=%d}] "
                "run scoreboard players set @s tg_capacity %d" % (ROD, t, cap),
                "execute as @a[hasitem=%s,scores={tg_type=%d}] "
                "run scoreboard players set @s tg_damage %d" % (ROD, t, dmg),
                "execute as @a[hasitem=%s,scores={tg_type=%d}] "
                "run scoreboard players set @s tg_reload_time %d" % (ROD, t, rtime),
                "execute as @a[hasitem=%s,scores={tg_type=%d}] "
                "run scoreboard players set @s tg_point %d" % (ROD, t, t),
                "execute as @a[hasitem=%s,scores={tg_type=%d}] "
                "run scoreboard players set @s tg_snd %d" % (ROD, t, snd),
                # 散射档：0.1° → 1/2/3 档（≤20 → 1，≤40 → 2，其余 3）
                "execute as @a[hasitem=%s,scores={tg_type=%d}] "
                "run scoreboard players set @s tg_spd %d" % (ROD, t, _spd_tier(spd)),
                "execute as @a[hasitem=%s,scores={tg_type=%d}] "
                "run scoreboard players set @s tg_part %d" % (ROD, t, part),
            ]}


# ---------------------------------------------------------------- 子弹（共享）
def chain_bullet():
    """**一条链服务全部 50 把枪**（U47）。

    不按枪拆链的原因：50 把枪各一条弹道链，光弹道就要几万个方块。
    共享链靠 `tg_recoil` 收敛：开火时它 = 这把枪的射程，射程外的格子
    永远满足不了 `tg_recoil=n..`，一条都不跑。12 格的枪只跑 12 格。

    ❗ 全程不用 tag；命中**只记分**（`tg_hurt` = 攻击力），扣血交给「结算」链。
    """
    BUL = "@e[type=xp_orb,scores={tg_bullet=1"      # 基底，条件往同一花括号里追加
    WHITE = " ".join("unless block ^ ^ ^ %s" % b for b in PASS)
    cmds = []

    # ① 碰撞穷举：N 从大到小，最后留下最近的障碍
    for n in range(MAX_RANGE, 0, -1):
        cmds.append(
            "execute as %s,tg_recoil=%d..}] at @s positioned ~~-498.5~ "
            "positioned ^^^%d %s run scoreboard players set @s tg_recoil %d"
            % (BUL, n, n, WHITE, n))

    # ② 三段肢体：头（+1.0）/ 胸（+0.5）/ 腿（-0.5）
    LIMBS = ((1, "-499"), (2, "-499.5"), (3, "-500.5"))
    for n in range(1, MAX_RANGE + 1):
        for limb, off in LIMBS:
            cmds.append(
                "execute as %s,tg_recoil=%d..,tg_limb=0}] at @s "
                "positioned ^^^%d positioned ~~%s~ at @e[r=1.2,c=1,%s] "
                "unless score @e[c=1] tg_team = @s tg_team "
                "run scoreboard players set @s tg_limb %d"
                % (BUL, n, n, off, BODY, n * 10 + limb))

    # ③ 弹道粒子：**10 种 × 每种穷举 100 格 = 1000 条**（U54）
    #
    #    每把枪带自己的 `tg_part`（1..10），只跑自己那一组 100 条。
    #    所以"每把枪的弹道颜色都不一样"，而结构里只需要一张 10×100 的表。
    for p, pname in enumerate(TRAIL10, 1):
        for n in range(1, MAX_RANGE + 1):
            cmds.append(
                "execute as %s,tg_recoil=%d..,tg_part=%d}] at @s positioned ^^^%d "
                "run particle %s ~~-498.5~" % (BUL, n, p, n, pname))

    # ④ 命中：同分（受击分 = 攻击力）+ 受击特效
    for n in range(1, MAX_RANGE + 1):
        P = ("execute as %s,tg_limb=%d..%d}] at @s positioned ^^^%d "
             "positioned ~~-499.5~ " % (BUL, n * 10 + 1, n * 10 + 3, n))
        cmds += [
            P + "as @e[r=1.2,c=1,%s] run scoreboard players operation @s tg_hurt = "
                "@e[type=xp_orb,scores={tg_bullet=1},c=1] tg_damage" % BODY,
            P + "run particle minecraft:basic_crit_particle ~ ~1 ~",
            P + "run playsound mob.irongolem.hit @a[r=20] ~~~ 0.8 1.6",
        ]

    # ⑤ 碰墙特效：recoil 停在哪一格就在那一格炸火花（没打中人才画）
    #
    # ❗ 从 3 格起：1~2 格离枪口太近，火花糊在脸上，看起来就像
    #    「子弹原地自爆」——其实是贴脸打墙。近距离干脆不画。
    for n in range(3, MAX_RANGE):
        cmds.append(
            "execute as %s,tg_recoil=%d,tg_limb=0}] at @s positioned ^^^%d "
            "run particle minecraft:sparkler_emitter ~~-498.5~" % (BUL, n, n))

    cmds.append("kill @e[type=xp_orb,scores={tg_bullet=1}]")
    return {"id": "bullet", "kind": "gated", "label": "弹道",
            "gate": "execute if entity @e[type=xp_orb,scores={tg_bullet=1}]",
            "cmds": cmds}


# ---------------------------------------------------------------- 结算（二分法）
def chain_dmg():
    """受击结算：**二分法扣血**（U44）。

    为什么要二分法：`damage` 只吃**字面数字**，吃不了分数。
    而伤害是算出来的（攻击者的攻击力），必须先把分数变成一条条固定的 `damage`。

    做法：把"这次该掉多少"拆成 2 的幂 —— 256 / 128 / 64 / 32 / 16 / 8 / 4 / 2 / 1。
    每步：分还够 → 扣这么多血、再把这个数从分里减掉。
    9 步 × 2 条 = 18 条，**加多少把枪、伤害改多大都不用动这里**。

    ❗ 幂次必须**从大到小**，"扣血"和"减分"必须**成对**（第 26 章）。
    ❗ 这条链的闸门是"有没有人欠血"，没有欠血就一条都不跑。
    """
    POWERS = (256, 128, 64, 32, 16, 8, 4, 2, 1)
    cmds = []
    for v in POWERS:
        cmds.append("execute as @e[scores={tg_hurt=%d..}] at @s "
                    "run damage @s %d entity_attack" % (v, v))
        cmds.append("execute as @e[scores={tg_hurt=%d..}] "
                    "run scoreboard players remove @s tg_hurt %d" % (v, v))
    return {"id": "dmg", "kind": "gated", "label": "结算",
            "gate": "execute if entity @e[scores={tg_hurt=1..}]",
            "cmds": cmds}


# ---------------------------------------------------------------- 换弹音
def chain_reload():
    return {"id": "reload", "kind": "gated",
            "gate": "execute if entity @a[scores={tg_reload=1..}]",
            "cmds": [
                "execute as @a[scores={tg_reload=1..}] at @s run playsound armor.equip_iron "
                "@a[r=16] ~~~ 1 1.5",
                "execute as @a[scores={tg_reload=1}] at @s run playsound armor.equip_iron "
                "@a[r=16] ~~~ 1 0.8",
                "execute as @a[scores={tg_reload=1}] at @s run playsound random.click "
                "@a[r=16] ~~~ 0.9 1.2",
                "execute as @a[scores={tg_reload=1}] at @s run camerashake add @s 0.06 0.12 positional",
                "execute as @a[scores={tg_reload=1}] at @s run titleraw @s actionbar " + J({"rawtext": [
                    {"text": "§8▏ §e装 填 完 成 §8· §f"},
                    {"score": {"name": "@s", "objective": "tg_magazine"}},
                    {"text": "§8／§f"},
                    {"score": {"name": "@s", "objective": "tg_capacity"}},
                ]}),
            ]}


# ---------------------------------------------------------------- 面板
# 需要断链的功能链 —— **排除闸门恒真的链**（如 clock 的 `execute if entity @a`）。
# 恒真闸门每刻成功，复位块会立刻把断点接回，断链对它毫无意义，直接让它循环即可（U14）。
# 标准断链格式（U3）：
#   [0] 无条件  execute if entity <条件>
#   [1] 有条件  setblock ~1 ~ ~ chain_command_block["facing_direction"=5]
#   外部        setblock <相对坐标> chain_command_block["facing_direction"=4]
#               —— 不要包 `execute unless entity @e[...] run`，直接一句 setblock
# 可断链 = 6 条主干 + 5 条弹道（每条枪一条）+ 开镜，共 12 条。
FUNC_CHAINS = (("join", "state", "trigger", "shot")
               + ("bullet",)
               + ("dmg", "reload", "aim"))


def panels():
    return [
        gunlist(),
        {"id": "p_supply", "kind": "impulse", "button": True, "cmds": [
            "scoreboard players set @p tg_reserve 300",
            "scoreboard players set @p tg_magazine 0",
            "scoreboard players set @p tg_reload 0",
            "playsound random.levelup @p ~~~ 1 1.2",
            "tellraw @p " + J({"rawtext": [{"text": "§a▷ 备弹已补满 §f300 §a发"}]}),
        ]},
        {"id": "p_reset", "kind": "impulse", "button": True, "cmds": [
            "scoreboard players set @a tg_magazine 0",
            "scoreboard players set @a tg_reserve 0",
            "scoreboard players set @a tg_cooldown 0",
            "scoreboard players set @a tg_reload 0",
            "scoreboard players set @a tg_burst 0",
            "scoreboard players set @a tg_fire 0",
            # 血量 / 相机一起复位：否则清完弹还是一副"半血 + 镜头卡住"的样子
            "scoreboard players set @a tg_aim 0",
            "scoreboard players set @a tg_fov -1",
            "camera @a fov_clear",
            "kill @e[type=xp_orb,scores={tg_bullet=1}]",
            "kill @e[type=fishing_hook]",
            "playsound random.click @p ~~~ 0.8 1.4",
            "tellraw @p " + J({"rawtext": [{"text": "§7▷ 已清空弹药与在飞弹丸，血量/视角已复位"}]}),
        ]},
        {"id": "p_purge", "kind": "impulse", "button": True, "cmds": [
            "kill @e[scores={tg_anchor=1}]",
        ] + ["scoreboard objectives remove tg_%s" % o for o in (
            "tick", "gun", "boot", "type", "magazine", "reserve", "capacity",
            "reload", "reload_time", "cooldown", "spread", "damage",
            "horizontal", "vertical", "recoil", "point", "burst", "user_id",
            "limb", "team", "bar", "temp", "temp2", "fire",
            "fov", "health", "health_max", "aim", "bullet", "anchor", "ready", "flag",
            "shot", "sh", "sv", "cd_frame", "spr", "snd", "page", "spd", "part", "hurt")] + [
            "scoreboard objectives setdisplay belowname",
            "tickingarea remove tide",
            "tellraw @p " + J({"rawtext": [{"text": "§c! 已卸载：计分项 / 常加载 / 锚点全部清除"}]}),
        ]},
        # ---- 断链 / 接通 ----
        # `{SET:<链ID>:dis}` / `:arm` 由 build_cbworld 展开成：
        #     setblock <复位块相对坐标> chain_command_block["facing_direction"=<朝后|朝前>]
        # 坐标与朝向**都是现算的**：结构粘到任何位置都对，蛇形换行处也不会写死 5。
        # ❗ 只写一句 setblock，不包 `execute unless ... run`——包了就等于
        #    「有子弹时才断开」，子弹一飞链就被接回去，按了像没反应（U3 / A11）。
        {"id": "p_cut", "kind": "impulse", "button": True, "cmds":
            ["{SET:%s:dis}" % c for c in FUNC_CHAINS] + [
            "playsound random.explode @p ~ ~ ~ 0.6 1.6",
            "tellraw @p " + J({"rawtext": [
                {"text": "§c▷ 全部功能链已断开§7（连接块朝后，闸门过不去）\n"},
                {"text": "§7  再按 §f「接通链条」§7 恢复"}]}),
        ]},
        {"id": "p_join", "kind": "impulse", "button": True, "cmds":
            ["{SET:%s:arm}" % c for c in FUNC_CHAINS] + [
            "playsound random.levelup @p ~ ~ ~ 0.7 1.6",
            "tellraw @p " + J({"rawtext": [{"text": "§a▷ 全部功能链已接通"}]}),
        ]},
        # ---- 自检面板：枪不响时按一下，看停在哪一步 ----
        {"id": "p_diag", "kind": "impulse", "button": True, "cmds": [
            "scoreboard players add @p tg_cooldown 0",
            "scoreboard players add @p tg_reload 0",
            "scoreboard players add @p tg_magazine 0",
            "scoreboard players add @p tg_capacity 0",
            "scoreboard players add @p tg_burst 0",
            "scoreboard players add @p tg_type 0",
            "scoreboard players add @p tg_user_id 0",
            "tellraw @p " + J({"rawtext": [
                {"text": "§8« §b自检 §8»\n"},
                {"text": "§7持枪 §f"}, {"selector": "@s[hasitem=%s]" % ROD},
                {"text": "\n§7枪型 §f"}, {"score": {"name": "@s", "objective": "tg_type"}},
                {"text": "  §7弹匣 §f"}, {"score": {"name": "@s", "objective": "tg_magazine"}},
                {"text": "§7/§f"}, {"score": {"name": "@s", "objective": "tg_capacity"}},
                {"text": "\n§7冷却 §f"}, {"score": {"name": "@s", "objective": "tg_cooldown"}},
                {"text": "  §7换弹 §f"}, {"score": {"name": "@s", "objective": "tg_reload"}},
                {"text": "  §7连发 §f"}, {"score": {"name": "@s", "objective": "tg_burst"}},
                {"text": "  §7UID §f"}, {"score": {"name": "@s", "objective": "tg_user_id"}},
                {"text": "\n§8冷却/换弹/连发 必须都是 0；弹匣要 > 0"}]}),
            "playsound random.orb @p ~ ~ ~ 0.7 1.4",
        ]},
        # ---- 试射：绕过「抛竿检测」，直接让出弹链跑一发 ----
        # 抛竿不响时按它：响了 = 出弹/弹道没问题，问题在扳机检测；
        # 还是不响 = 问题在出弹链本身。一步分清，不用再猜。
        {"id": "p_test", "kind": "impulse", "button": True, "cmds": [
            "scoreboard players add @p tg_damage 0",
            "scoreboard players add @p tg_point 0",
            "scoreboard players add @p tg_user_id 0",
            "scoreboard players add @p tg_team 0",
            "scoreboard players set @p tg_type 1",
            "scoreboard players set @p tg_damage %d" % DMG_DEFAULT,
            "scoreboard players set @p tg_point 1",
            "scoreboard players set @p tg_cooldown 0",
            "scoreboard players set @p tg_reload 0",
            "scoreboard players set @p tg_burst 1",
            "playsound random.bow @p ~ ~ ~ 1 1.2",
            "tellraw @p " + J({"rawtext": [
                {"text": "§b▷ 试射§7：已直接触发出弹链（不经过抛竿检测）\n"},
                {"text": "§7  有子弹飞出 → 出弹没问题，是§f扳机§7没触发"}]}),
        ]},
    ]


# ---------------------------------------------------------------- 说明区
def gun_lines(t):
    """按 `GUNS` 表生成物品 Lore 的数值行 —— **不许手写数字**。

    ❗ 以前 Lore 是手写的，已经和表漂了：精准写「散射 18」实际是 300、
      霰弹写「散射 200」实际是 25。改伤害的时候 Lore 不会跟着变，
      玩家看到的就是假数据。这里一律从表里算。
    """
    _, name, cap, cd, dmg, burst, rtime, pitch, rng, spd, part, snd = {g[0]: g for g in GUNS}[t]
    line = "§r§7-弹匣 §f%d §7发，间隔 §f%d §7刻，单发 §f%d §7点" % (cap, cd, dmg)
    if burst > 1:
        return [line,
                "§r§7-一次 §f%d §7颗，全中 §f%d §7点" % (burst, dmg * burst),
                "§r§7-散射大，贴脸最狠"]
    return [line,
            "§r§7-射程 §f%d §7格　散射 §f%.1f§7°" % (rng, spd / 10.0)]


# 系列的展示色 / 一句话卖点（按音效档 1..5 取，不按具体枪）
GUN_STYLE = {
    1: ("§b", "轻、快，随手就能开火"),
    2: ("§d", "连成一条线，压得人抬不起头"),
    3: ("§a", "中距离最稳的那一类"),
    4: ("§6", "看得见就打得中"),
    5: ("§e", "不按常理出牌的那一档"),
}


def props():
    """说明区：**两个箱子装 50 把枪的弹匣**，物品全部由 GUNS 表生成（U33）。"""
    I = B.item_nbt
    sep = "§r§7——————————————————"
    card = I("paper", 1, display_name="§8▸ §b潮汐鱼竿枪 §8· §f操作卡", slot=0,
             lore=[
                 "§r§7-§b∅ §l§7| §r§f主手 §b鱼竿 §7| §r§g武器：主手",
                 sep,
                 "§r§7-副手放 §b鹦鹉螺壳 §7切枪，共 §f50 §7把",
                 "§r§7-左箱 §f01–25 §8/ §7右箱 §f26–50",
                 "§r§7-§f低头§7换弹　§f蹲下§7开镜",
                 "§r§7-面板按钮 §f「枪械图鉴」§7 查全部参数",
                 sep,
                 "§o§8............浪会替你算弹道。"])

    def shell_item(g, slot):
        t, name, cap, cd, dmg, burst, rtime, pitch, rng, spd, part, snd = g
        col, tagline = GUN_STYLE[snd]
        return I("nautilus_shell", 1, damage=t, slot=slot,
                 display_name="§r§n⫸%s%s §8· §f%02d" % (col, name, t),
                 lore=[
                     "§r§7-%s∅ §l§7| §r§1 ∅ 级 §l§7| §r§g饰品：副手" % col,
                     sep,
                     *gun_lines(t),
                     "§r§7-" + tagline,
                     sep,
                     "§o§8............放副手就生效。"])

    chest1 = [card] + [shell_item(g, i + 1) for i, g in enumerate(GUNS[:25])]
    chest2 = [shell_item(g, i) for i, g in enumerate(GUNS[25:])] + [
        I("leather_chestplate", 1, unbreakable=True, slot=25,
          display_name="§r§n⫸§f暴怒", lore=[
              "§r§7-§4∅ §l§7| §r§1 ∅ 级 §l§7| §r§g饰品：胸部",
              sep,
              "§r§7-周围10格有敌人时伤害 ×1.15，无敌人时 ×0.75",
              sep,
              "§o§8............他又能做什么呢？"]),
        I("fishing_rod", 1, unbreakable=True, slot=26,
          display_name="§r§n⫸§b潮汐 §8· §f鱼竿枪", lore=[
              "§r§7-§b∅ §l§7| §r§1 ∅ 级 §l§7| §r§g武器：主手",
              sep,
              "§r§7-拿在§f主手§7，§b抛竿§7即开火",
              "§r§7-§f低头§7换弹　§f蹲下§7开镜",
              sep,
              "§o§8............浪会替你算弹道。"]),
    ]

    signs = [
        ["§8«§b潮汐§8»", "§f鱼竿枪", "§8—————", "§7左箱：01–25"],
        ["§f主手 §b鱼竿", "§f副手 §b鹦鹉螺壳", "§7壳的 §f名字", "§7决定枪型"],
        ["§f抛竿 §c开火", "§f低头 §e换弹", "§f蹲下 §b开镜", "§8浮漂会被吞掉"],
        ["§b右箱：§f26–50", "§7共 §f50 §7把枪", "§7参数看面板", "§8切枪即换弹匣"],
        ["§f「枪械图鉴」", "§7按一下看 8 把", "§7再按翻页", "§8按了就有反馈"],
        ["§f按钮 = 维护", "§7补弹 §8/ §7清空", "§7自检 §8/ §7断开", "§8按了就有反馈"],
    ]
    out = [{"kind": "chest", "items": chest1, "name": "潮汐 · 装备 01–25", "at": (0, 0)},
           {"kind": "chest", "items": chest2, "name": "潮汐 · 装备 26–50", "at": (0, 1)}]
    for i, sg in enumerate(signs):
        out.append({"kind": "sign", "front": sg, "at": (i + 2, 0)})
    return out


# ---------------------------------------------------------------- 图鉴面板
def gunlist():
    """枪械图鉴：**分页显示 50 把枪的全部参数**（U49）。

    一页 8 把，按一次翻一页，翻到底回第一页。
    `tg_page` 是页码，按 `%%` 无 —— 直接用 `scores={tg_page=pi}` 选页。
    """
    per, n = 8, (len(GUNS) + 7) // 8
    cmds = ["scoreboard players add @p tg_page 0"]
    for pi in range(n):
        page = GUNS[pi * per:(pi + 1) * per]
        comps = [{"text": "§8«§b枪械图鉴§8» §7第 §f%d§7/§f%d §7页\n" % (pi + 1, n)}]
        for g in page:
            t, name, cap, cd, dmg, burst, rtime, pitch, rng, spd, part, snd = g
            col = GUN_STYLE[snd][0]
            comps.append({"text": "§8%02d %s%s §8│§7弹§f%d §7伤§f%d §7射§f%d §7连§f%d §7速§f%d\n"
                                  % (t, col, name, cap, dmg, rng, burst, cd)})
        comps.append({"text": "§8▸ 再按一次翻页"})
        cmds.append("execute as @p[scores={tg_page=%d}] run tellraw @s " % pi
                    + J({"rawtext": comps}))
    cmds += [
        "scoreboard players add @p tg_page 1",
        "execute as @p[scores={tg_page=%d..}] run scoreboard players set @p tg_page 0" % n,
        "playsound random.click @p ~~~ 0.8 1.4",
    ]
    return {"id": "p_gunlist", "kind": "impulse", "button": True, "cmds": cmds}


# ---------------------------------------------------------------- 组装
DEPTH = 0


# ---------------------------------------------------------------- 编译
# 业务命令还是那些（弹道 / 音效 / HUD 的逻辑没动），但**链的结构不再手写**：
# 交给 cbc 编译器，闸门 / 复位 / 自断 / 条件位一律由它生成（见 cbc.py 头注释）。
#
# 恒真闸门（`execute if entity @a`）→ 编译成常驻链：没有闸门、没有复位块、
# 没有自断块，循环块直接装第一条业务，链自己绕回来（用户 U14）。
LOOP_CHAINS = ("clock",)


def _to_spec(chain_spec):
    """把老式 {"id","kind","gate","cmds"} 转成 cbc 的链。

    gate 一律剥掉 `execute if entity ` 前缀 —— cbc 自己加，剥不干净就会拼出
    `execute if entity entity @a`（编译器里已加断言拦这个）。
    """
    cid = chain_spec["id"]
    gate = chain_spec.get("gate") or ""
    body = list(chain_spec["cmds"])

    if chain_spec.get("kind") == "impulse":
        # 面板 / 初始化：靠按钮触发，没有闸门、没有复位、没有自断
        return {"id": cid, "body": body, "when": None, "loop": False,
                "impulse": True}
    if cid in LOOP_CHAINS:
        return {"id": cid, "body": body, "when": None, "loop": True}
    if gate.startswith("execute if entity "):
        sel = gate[len("execute if entity "):]
    elif gate.startswith("execute if "):
        raise SystemExit("%s：闸门必须是 `execute if entity <选择器>`，实际 %s"
                         % (cid, gate))
    else:
        sel = gate
    if sel == "@a":                      # 恒真 → 常驻链，不留 `execute if entity @a`
        return {"id": cid, "body": body, "when": None, "loop": True}
    return {"id": cid, "body": body, "when": sel, "loop": False}


def all_chains():
    """全部业务链（顺序 = 世界里的摆放顺序）。"""
    return ([chain_init(), chain_clock(), chain_join(), chain_state(),
             chain_trigger(), chain_shot()]
            + [chain_bullet()]
            + [chain_gun(g) for g in GUNS]
            + [chain_dmg(), chain_reload(), chain_aim()])


def compile_program():
    """业务链 → cbc 程序 → 命令方块规格。返回 (程序, {链id: 链标签})。"""
    import cbc
    p = cbc.Program("潮汐鱼竿枪")
    labels = {}
    for raw_spec in all_chains():
        sp = _to_spec(raw_spec)
        if raw_spec.get("label"):
            labels[sp["id"]] = raw_spec["label"]
        p.chain(sp["id"], sp["body"], when=sp["when"], loop=sp["loop"],
                impulse=sp.get("impulse", False))
    return p, labels


def spec():
    global DEPTH
    validate()

    def build():
        prog, labels = compile_program()
        chains = prog.emit()["chains"]
        for ch in chains:
            if ch.get("id") in labels:
                ch["label"] = labels[ch["id"]]
            # 二楼：`gun01..gun50` 全部摆到第二层（U53）
            if str(ch.get("id", "")).startswith("gun"):
                ch["level"] = 1
        # 深度按**楼层**分别算，取最大的那层（二楼不叠加深度）
        levels = {}
        for ch in chains:
            levels.setdefault(ch.get("level", 0), []).append(ch)
        depth = 0
        for lv, sub in levels.items():
            rows = 0
            for ch in sub:
                n = len(ch["cmds"]) + (2 if ch["kind"] == "gated" else 0)
                rows += (n + B.W - 1) // B.W      # 宽度跟布局走，不能写死 16
            extra = len(panels()) if lv == 0 else 0
            depth = max(depth, rows + len(sub) + extra + 4 + 2)
        return chains, depth

    chains, DEPTH = build()
    # init 链里 `tickingarea add` 要写 DEPTH，深度算完必须**重编译一次**，
    # 否则常加载区比实际指令区短，走远一点整台机器就停摆。
    chains, DEPTH = build()

    return {
        "meta": {"name": "潮汐鱼竿枪", "spawn": [8, -59, 1], "gametype": "creative",
                 "debug_output": False},
        "chains": chains,
        # ❗ 面板必须**带 id**。旧写法只存 cmds，build_cbworld 认不出是哪条，
        #    方块自述就退化成「链#07 置分」，链头也没有概括（U31）。
        "panels": [{"id": p["id"], "cmds": p["cmds"]} for p in panels()],
        "props": props(),
    }


def build_world(template, out, sp):
    # props_pedestal：说明区垫一格黑混凝土再放（告示牌抬到视线高度）。
    # 和命令方块同层时，玩家站在机器上往下看，牌子在脚边 → 很容易以为"没生成"。
    system = {"chains": list(sp["chains"]), "props": list(sp.get("props") or []),
              "props_pedestal": True}
    for p in sp["panels"]:
        if isinstance(p, dict):
            system["chains"].append({"kind": "impulse", "button": True,
                                     "id": p.get("id"), "cmds": p["cmds"]})
        else:                                  # 老 spec 兼容：纯命令列表
            system["chains"].append({"kind": "impulse", "button": True, "cmds": p})

    info = B.build(template, out, sp["meta"]["name"],
                   tuple(sp["meta"]["spawn"]),
                   1 if sp["meta"]["gametype"] == "creative" else 0,
                   system)
    total, idle = B.tick_stats(system["chains"])
    info.update({"cmds": total, "idle": idle, "depth": DEPTH,
                 "gated": sum(1 for c in system["chains"] if c["kind"] == "gated"),
                 "chains": len(system["chains"])})
    return info


def main():
    ap = argparse.ArgumentParser(description="潮汐鱼竿枪 v3（真实原理版）")
    ap.add_argument("--dump-spec", metavar="JSON")
    ap.add_argument("--spec")
    ap.add_argument("--template")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.dump_spec:
        sp = spec()
        os.makedirs(os.path.dirname(os.path.abspath(args.dump_spec)), exist_ok=True)
        with open(args.dump_spec, "w", encoding="utf-8") as f:
            json.dump(sp, f, ensure_ascii=False, indent=1)
        n = (sum(len(c["cmds"]) for c in sp["chains"])
             + sum(len(p["cmds"]) if isinstance(p, dict) else len(p)
                   for p in sp["panels"]))
        gated = sum(1 for c in sp["chains"] if c["kind"] == "gated")
        print("[spec] %s  链 %d 条（闸门链 %d / 其中可断链 %d）/ 命令 %d 条 / 地板深 %d"
              % (args.dump_spec, len(sp["chains"]) + len(sp["panels"]), gated,
                 len(FUNC_CHAINS), n, DEPTH))
        return

    if not (args.spec and args.template and args.out):
        ap.error("生成世界需要 --spec / --template / --out")

    with open(args.spec, encoding="utf-8") as f:
        sp = json.load(f)
    info = build_world(args.template, args.out, sp)
    print("[完成] %s" % info["out"])
    print("        区块 %d，命令方块 %d，按钮 %d，命令 %d 条"
          % (info["chunks"], info["blocks"], info["buttons"], info["cmds"]))
    print("        说明区 %d 个（箱子/告示牌）" % info.get("props", 0))
    print("        功能链 %d 条 / 总链 %d 条 → 空闲每刻只有 %d 条闸门在跑"
          % (info["gated"], info["chains"], info["idle"]))
    print("        下一步：python verify_mcworld.py <文件>")


if __name__ == "__main__":
    main()
