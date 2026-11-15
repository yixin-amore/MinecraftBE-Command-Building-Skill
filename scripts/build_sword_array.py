#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""十方剑阵 · 穿阵（正前方竖直法阵 + 十剑平行突刺）。

修正上一版两个问题：
  1. 剑阵原本绕玩家水平排布、十把剑却都朝同一世界方向 → 看着"乱"。
     现在整座法阵建在**玩家正前方**的竖直平面上，十剑**全部平行**，一起向前穿阵。
  2. 朝向用「狐狸跟随施法者朝向」实现：每刻 `execute at <施法者> run tp @e[...] ~ ~ ~ ~ ~`
     把施法者的位置和朝向刷给狐狸，于是 basepos 直接写设计坐标（左右 / 上下 / 前后）即可，
     整座法阵天然跟着玩家朝向走，不需要在 Molang 里做旋转矩阵。

七幕（cam_t 从 240 倒数）：
    结印 240..216  正前方 5 格处，竖直法阵逐点画出（8 环 × 48 点）
    凝剑 215..180  十剑从脚下飞到阵后 2.5 格，放大到位
    悬停 179..120  阵前微浮，紫环共鸣
    蓄力 119..80   十剑后撤、抖动
    突刺  79..45   十剑齐穿法阵，冲到阵前 9 格
    余韵  44..1    剑影减速消散，法阵余烬上飘

用法：
    python build_sword_array.py --dump-spec out/spec.json
    python build_sword_array.py --spec out/spec.json --template t.mcworld --out out/_build.mcworld
"""
import argparse
import json
import math
import os
import sys

# 依赖同目录的 build_cbworld.py —— 用相对路径，项目级 / 用户级都能跑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B

SHIELD = "@e[scores={fmbe_shield=1..}]"
BOOK = "@a[hasitem={item=enchanted_book,location=slot.weapon.mainhand}]"
CASTER = "@a[scores={cam_cast=1},c=1]"

DUR = 240
CD = 500
MIN_BLOCKS = 1500

SWORD_ITEM = "minecraft:netherite_sword"
SWORD_N = 10
RING_R = 1.8          # 剑在阵后圆环上的半径
CIRCLE_Z = 5.0        # 法阵平面：正前方 5 格
CIRCLE_Y = 1.2        # 法阵圆心高度
SWORD_Z = 2.5         # 剑悬停位置（阵后 2.5 格）

GRID = sorted([(dx, dz) for dz in range(-8, 9, 2) for dx in range(-8, 9, 2)
               if not (dx == 0 and dz == 0)], key=lambda p: (p[0] ** 2 + p[1] ** 2, p[1], p[0]))


# ---------------------------------------------------------------- 法阵粒子
def vcircle(radius, n, particle, t_from, t_to, cz=CIRCLE_Z, cy=CIRCLE_Y, phase=0.0):
    """竖直平面上的一个圆：n 个点，从 t_from 逐点画到 t_to。"""
    out = []
    for k in range(n):
        th = 2 * math.pi * k / n + math.radians(phase)
        t = t_from - round((t_from - t_to) * k / max(1, n - 1))
        out.append('execute as @a[scores={cam_t=%d}] at @s run particle %s '
                   '^%.2f ^%.2f ^%.2f'
                   % (t, particle, radius * math.cos(th), cy + radius * math.sin(th), cz))
    return out


def spokes(n, r0, r1, steps, particle, t_from, t_to, cz=CIRCLE_Z, cy=CIRCLE_Y):
    """径向辐条：n 个角度 × steps 个点，从内向外画。"""
    out = []
    total = n * steps
    i = 0
    for k in range(n):
        th = 2 * math.pi * k / n
        for j in range(steps):
            r = r0 + (r1 - r0) * j / max(1, steps - 1)
            t = t_from - round((t_from - t_to) * i / max(1, total - 1))
            out.append('execute as @a[scores={cam_t=%d}] at @s run particle %s '
                       '^%.2f ^%.2f ^%.2f'
                       % (t, particle, r * math.cos(th), cy + r * math.sin(th), cz))
            i += 1
    return out


def impact_rings():
    """突刺瞬间：法阵平面上的冲击波，半径从内向外炸开。"""
    out = []
    for i, r in enumerate([0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4, 4.8]):
        out += vcircle(r, 20, "minecraft:totem_particle", 78 - i, 72 - i,
                       cz=CIRCLE_Z + i * 0.15)
    return out


def trails():
    """十剑的突刺拖尾：沿前进方向铺点。"""
    out = []
    for k in range(SWORD_N):
        th = 2 * math.pi * k / SWORD_N
        x, y = RING_R * math.cos(th), CIRCLE_Y + RING_R * math.sin(th)
        for j in range(8):
            z = SWORD_Z + 1.2 + j * 0.85
            t = 76 - j
            out.append('execute as @a[scores={cam_t=%d}] at @s run particle '
                       'minecraft:endrod ^%.2f ^%.2f ^%.2f' % (t, x, y, z))
    return out


def embers():
    """余韵：法阵平面上的余烬上飘。"""
    out = []
    for k in range(48):
        th = 2 * math.pi * k / 48
        r = 0.8 + (k % 5) * 0.55
        t = max(1, 40 - (k % 20))
        out.append('execute as @a[scores={cam_t=%d}] at @s run particle '
                   'minecraft:basic_flame_particle ^%.2f ^%.2f ^%.2f'
                   % (t, r * math.cos(th), CIRCLE_Y + r * math.sin(th) + (k % 4) * 0.3,
                      CIRCLE_Z - 0.2))
    return out


# ---------------------------------------------------------------- 剑
def swords():
    out = []
    for k in range(SWORD_N):
        sx, sz = GRID[k]
        th = math.radians(k * 360.0 / SWORD_N)
        out.append(dict(
            sx=sx, sy=0, sz=sz,
            bx=RING_R * 16 * math.cos(th),       # 设计坐标：左右
            by=(CIRCLE_Y + RING_R * math.sin(th)) * 16,
            ph=round(k * 360.0 / SWORD_N, 1),
        ))
    return out


SWORDS = swords()
N = len(SWORDS)


def phase_body(name):
    out = []
    for c in SWORDS:
        bx, by = c["bx"], c["by"]
        if name == "gather":
            s = "(1-math.exp(-q.life_time*3))"
            body = ("v.xbasepos=%g*%s;v.ybasepos=%g*%s;v.zbasepos=%g*%s;"
                    "v.scale=1.5*%s;v.zrot=90;"
                    % (bx, s, by, s, SWORD_Z * 16, s, s))
        elif name == "hover":
            body = ("v.xbasepos=%g;v.ybasepos=%g+4*math.sin(q.life_time*90+%g);"
                    "v.zbasepos=%g;v.scale=1.5;v.zrot=90;"
                    % (bx, by, c["ph"], SWORD_Z * 16))
        elif name == "charge":
            body = ("v.xbasepos=%g+1.5*math.sin(q.life_time*300+%g);"
                    "v.ybasepos=%g+1.5*math.cos(q.life_time*260+%g);"
                    "v.zbasepos=%g;v.scale=1.5;v.zrot=90;"
                    % (bx, c["ph"], by, c["ph"], 1.2 * 16))
        elif name == "thrust":
            body = ("v.xbasepos=%g;v.ybasepos=%g;"
                    "v.zbasepos=16*(1.2+7.8*math.min(1,math.max(0,q.life_time-3.95)*1.6));"
                    "v.scale=1.5;v.zrot=90;"
                    % (bx, by))
        else:  # after
            body = ("v.xbasepos=%g;v.ybasepos=%g+math.max(0,q.life_time-4.75)*6;"
                    "v.zbasepos=16*(9+math.max(0,q.life_time-4.75)*1.5);"
                    "v.scale=math.max(0.02,1.5-math.max(0,q.life_time-4.75)*0.9);v.zrot=90;"
                    % (bx, by))
        out.append(body)
    return out


PHASES = ["gather", "hover", "charge", "thrust", "after"]
PHASE_GATE = {
    "gather": "execute if entity @a[scores={cam_t=180..215}]",
    "hover":  "execute if entity @a[scores={cam_t=120..179}]",
    "charge": "execute if entity @a[scores={cam_t=80..119}]",
    "thrust": "execute if entity @a[scores={cam_t=45..79}]",
    "after":  "execute if entity @a[scores={cam_t=1..44}]",
}


def at_sw(c, cmd):
    return ("execute at %s positioned ~%d ~%d ~%d run %s"
            % (CASTER, c["sx"], c["sy"], c["sz"], cmd))


# ---------------------------------------------------------------- 初始化
def init_cmds(ta):
    return [
        "gamerule sendcommandfeedback false",
        "gamerule commandblockoutput false",
        "gamerule showdeathmessages false",
        "gamerule announceadvancements false",
        "gamerule showrecipemessages false",
        "gamerule showcoordinates false",
        'scoreboard objectives add cam_t dummy "演出计时"',
        'scoreboard objectives add cam_cast dummy "施法触发"',
        'scoreboard objectives add cam_cd dummy "剑阵冷却"',
        'scoreboard objectives add fmbe_shield dummy "剑阵展示体"',
        "tickingarea remove sword_array",
        ta,
        'tellraw @a {"rawtext":[{"text":"§b十方剑阵 §8· §f手持附魔书施放，§7冷却 25 秒"}]}',
    ]


def trigger_cmds():
    cond = ("%s unless entity @s[scores={cam_cd=1..}] "
            "unless entity @s[scores={cam_t=0..}]" % BOOK)
    return [
        "execute as %s run scoreboard players set @s cam_cast 1" % cond,
        "execute as %s run playsound random.orb @s ~ ~ ~ 0.6 1.6" % cond,
    ]


# ---------------------------------------------------------------- 施法
def cast_cmds():
    c = [
        "execute as %s run camera @s clear" % CASTER,
        "execute as %s run camera @s fov_clear" % CASTER,
        "scoreboard players set %s cam_cd %d" % (CASTER, CD),
        "scoreboard players set %s cam_t %d" % (CASTER, DUR),
        "inputpermission set %s movement disabled" % CASTER,
        "tp @e[scores={fmbe_shield=0}] ~ -400 ~",
    ]
    for i, sw in enumerate(SWORDS, start=1):
        c.append("execute at %s run summon fox ~%d ~%d ~%d" % (CASTER, sw["sx"], sw["sy"], sw["sz"]))
        # 把施法者的位置和朝向刷给这只狐狸 —— 整座剑阵才能"长在正前方"
        c.append(at_sw(sw, "tp @e[type=fox,r=2,c=1] ~ ~ ~ ~ ~"))
        c.append(at_sw(sw, "replaceitem entity @e[type=fox,r=2,c=1] "
                           "slot.weapon.mainhand 0 %s" % SWORD_ITEM))
        c.append(at_sw(sw, "scoreboard players set @e[type=fox,r=2,c=1] fmbe_shield %d" % i))
        c.append(at_sw(sw, 'playanimation @e[type=fox,r=2,c=1] '
                           'animation.player.attack.positions none 0 '
                           '"v.xbasepos=0;v.ybasepos=0;v.zbasepos=0;v.scale=0.02;v.zrot=90;" fmbe.init'))
    c += [
        "effect %s invisibility 999999 1 true" % SHIELD,
        "effect %s resistance 999999 255 true" % SHIELD,
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.aggro",
        "stopsound @a mob.fox.bite",
        "stopsound @a mob.fox.eat",
        "playsound random.explode @a[r=40] ~ ~ ~ 0.7 0.6",
        "playsound raid.horn @a[r=40] ~ ~ ~ 0.9 1.0",
        "playsound item.trident.thunder @a[r=40] ~ ~ ~ 0.8 1.2",
        "playsound conduit.activate @a[r=40] ~ ~ ~ 0.6 1.4",
        "playsound beacon.activate @a[r=40] ~ ~ ~ 1 0.8",
        "execute at %s run particle minecraft:knockback_roar_particle ^ ^1.2 ^3" % CASTER,
        "execute at %s run particle minecraft:totem_particle ^ ^1.2 ^4" % CASTER,
        'execute as @a[scores={cam_t=0..}] run titleraw @s title '
        '{"rawtext":[{"text":"§b§l十 方 剑 阵"}]}',
        'execute as @a[scores={cam_t=0..}] run titleraw @s subtitle '
        '{"rawtext":[{"text":"§7阵起 · 剑出"}]}',
        "scoreboard players set @a cam_cast 0",
    ]
    return c


# ---------------------------------------------------------------- 渲染
def render_cmds():
    return [
        'playanimation %s animation.player.sleeping none 0 "" '
        'controller.animation.fox.move' % SHIELD,
        'playanimation %s animation.creeper.swelling none 0 '
        '"v.xbasepos=v.xbasepos??0;v.ybasepos=v.ybasepos??0;v.zbasepos=v.zbasepos??0;'
        'v.xpos=v.xpos??0;v.ypos=v.ypos??0;v.zpos=v.zpos??0;'
        'v.xrot=v.xrot??0;v.yrot=v.yrot??0;v.zrot=v.zrot??0;'
        'v.scale=v.scale??1;v.xzscale=v.xzscale??1;v.yscale=v.yscale??1;'
        'v.swelling_scale1=2.1385*math.sqrt(v.xzscale*v.scale);'
        'v.swelling_scale2=2.1385*math.sqrt(v.yscale*v.scale);" fmbe.scale' % SHIELD,
        'playanimation %s animation.ender_dragon.neck_head_movement none 0 '
        '"v.head_rotation_x=0;v.head_rotation_y=0;v.head_rotation_z=0;'
        'v.head_position_x=(v.xbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);'
        'v.head_position_y=(10.05185375+v.ybasepos*0.467625)*math.sqrt(v.yscale*v.scale);'
        'v.head_position_z=(17.108-v.zbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);" '
        'fmbe.shift_pos' % SHIELD,
        'playanimation %s animation.warden.move none 0 '
        '"v.body_x_rot=90+v.xrot;v.body_z_rot=90+v.yrot;" fmbe.xrot' % SHIELD,
        'playanimation %s animation.player.attack.rotations none 0 '
        '"v.attack_body_rot_y=-v.zrot;" fmbe.zrot' % SHIELD,
        'playanimation %s animation.parrot.moving none 0 '
        '"v.wing_flap=(16-v.xpos)*3.3333333;" fmbe.xpos' % SHIELD,
        'playanimation %s animation.minecart.move.v1.0 none 0 '
        '"v.rail_offset.x=0;v.rail_offset.y=1.6485+v.ypos/16;v.rail_offset.z=0;" '
        'fmbe.ypos' % SHIELD,
        'playanimation %s animation.parrot.dance none 0 '
        '"v.dance.x=-v.zpos;v.dance.y=0;" fmbe.zpos' % SHIELD,
        # 每刻把施法者的位置 + 朝向刷给全部狐狸：整座剑阵钉在正前方，跟着人转
        "execute at %s run tp %s ~ ~ ~ ~ ~" % (CASTER, SHIELD),
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.bite",
    ]


def phase_cmds(name):
    c = []
    for i, body in enumerate(phase_body(name), start=1):
        c.append('playanimation @e[scores={fmbe_shield=%d}] '
                 'animation.player.attack.positions none 0 "%s" fmbe.ph' % (i, body))
    return c


# ---------------------------------------------------------------- 运镜
def clock_cmds():
    shots = [
        (239, "^ ^1.0 ^-1.2", "out_cubic", 0.9),
        (212, "^2.4 ^1.8 ^-3.0", "in_out_sine", 1.2),
        (185, "^ ^2.2 ^-4.2", "in_out_sine", 1.2),
        (155, "^3.6 ^1.4 ^1.2", "in_out_sine", 1.2),
        (128, "^ ^1.4 ^2.6", "in_out_sine", 1.0),
        (100, "^-2.8 ^2.0 ^0.8", "in_out_sine", 1.0),
        (78,  "^ ^0.8 ^-1.0", "out_quad", 0.5),
        (60,  "^ ^2.6 ^4.0", "out_quad", 0.6),
        (36,  "^ ^3.4 ^-5.0", "out_quad", 0.7),
        (14,  "^ ^1.4 ^-2.4", "out_quad", 0.8),
    ]
    c = ["execute as @a[scores={cam_t=1..}] run scoreboard players remove @s cam_t 1"]
    for t, pos, ease, dur in shots:
        c.append('execute as @a[scores={cam_t=%d}] at @s run camera @s set minecraft:free '
                 'ease %s %s pos %s facing ~ ~1.2 ~' % (t, dur, ease, pos))
    c += [
        "execute as @a[scores={cam_t=239}] run camera @s fov_set 50 0.2 out_quad",
        "execute as @a[scores={cam_t=185}] run camera @s fov_set 78 1.2 in_out_sine",
        "execute as @a[scores={cam_t=128}] run camera @s fov_set 58 1.0 in_out_sine",
        "execute as @a[scores={cam_t=78}] run camera @s fov_set 95 0.3 out_quad",
        "execute as @a[scores={cam_t=36}] run camera @s fov_set 64 0.8 in_out_sine",
        "execute as @a[scores={cam_t=185}] run camerashake add @s 0.3 0.3 positional",
        "execute as @a[scores={cam_t=100}] run camerashake add @s 0.45 0.4 positional",
        "execute as @a[scores={cam_t=78}] run camerashake add @s 1.0 0.7 positional",
        "execute as @a[scores={cam_t=200}] at @s run playsound note.pling @s ~ ~ ~ 1 0.8",
        "execute as @a[scores={cam_t=170}] at @s run playsound totem.use @s ~ ~ ~ 0.8 1.4",
        "execute as @a[scores={cam_t=128}] at @s run playsound beacon.activate @s ~ ~ ~ 1 1.2",
        "execute as @a[scores={cam_t=100}] at @s run playsound note.pling @s ~ ~ ~ 0.8 1.6",
        "execute as @a[scores={cam_t=80}] at @s run playsound item.trident.thunder @s ~ ~ ~ 0.9 1.5",
        "execute as @a[scores={cam_t=78}] at @s run playsound random.explode @s ~ ~ ~ 1 0.7",
        "execute as @a[scores={cam_t=78}] at @s run playsound mob.enderdragon.growl @s ~ ~ ~ 1 0.6",
        "execute as @a[scores={cam_t=78}] at @s run particle minecraft:huge_explosion_emitter ^ ^1.2 ^5",
        "execute as @a[scores={cam_t=78}] at @s run particle minecraft:totem_particle ^ ^1.2 ^5",
        "execute as @a[scores={cam_t=60}] at @s run particle minecraft:knockback_roar_particle ^ ^1.2 ^7",
        "execute as @a[scores={cam_t=14}] at @s run playsound note.harp @s ~ ~ ~ 0.7 0.8",
        "execute as @a[scores={cam_t=0}] run camera @s clear",
        "execute as @a[scores={cam_t=0}] run camera @s fov_clear 0.8 out_elastic",
        "execute as @a[scores={cam_t=0}] run inputpermission set @s movement enabled",
        "execute as @a[scores={cam_t=0}] run scoreboard players set @e[scores={fmbe_shield=1..}] fmbe_shield 0",
        "execute as @a[scores={cam_t=0}] run tp @e[scores={fmbe_shield=0}] ~ -400 ~",
        "execute as @a[scores={cam_t=0}] run scoreboard players set @s cam_t -1",
        'execute as @a[scores={cam_t=-1}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§7剑阵散去"}]}',
    ]
    return c


def cooldown_cmds():
    return [
        "execute as @a[scores={cam_cd=1..}] run scoreboard players remove @s cam_cd 1",
        'execute as @a[scores={cam_cd=1..}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§8十方剑阵 §7冷却 §f"},'
        '{"score":{"name":"@s","objective":"cam_cd"}}]}',
    ]


def abort_cmds():
    return [
        "camera @a clear",
        "camera @a fov_clear",
        "inputpermission set @a movement enabled",
        "scoreboard players set @e[scores={fmbe_shield=1..}] fmbe_shield 0",
        "tp @e[scores={fmbe_shield=0}] ~ -400 ~",
        "scoreboard players set @a cam_t -1",
        "scoreboard players set @a cam_cast 0",
        'execute as @a[scores={cam_t=-1}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§c已中断"}]}',
    ]


def spec(ta="tickingarea add circle ~ ~ ~ 4 sword_array"):
    # 结印：8 环 × 48 点 = 384，一环一条链
    open_chains = []
    for i, r in enumerate([0.55, 0.95, 1.35, 1.75, 2.15, 2.55, 2.95, 3.35, 3.75, 4.15]):
        open_chains.append({
            "id": "fx_c%d" % i, "kind": "gated", "label": "法阵·环%d" % (i + 1),
            "gate": "execute if entity @a[scores={cam_t=%d..%d}]" % (216 - i, 240 - i),
            "cmds": vcircle(r, 48, "minecraft:endrod", 240 - i, 216 - i),
        })
    sp = spokes(24, 1.0, 3.1, 8, "minecraft:enchanting_table_particle", 238, 214)
    im = impact_rings()
    tr, em = trails(), embers()
    deco_chains = []
    for i, r in enumerate([3.9, 4.4, 4.9, 5.4, 5.9, 6.4, 6.9, 7.4]):
        deco_chains.append({
            "id": "fx_d%d" % i, "kind": "gated", "label": "法阵·外环%d" % (i + 1),
            "gate": "execute if entity @a[scores={cam_t=%d..%d}]" % (210 - i, 232 - i),
            "cmds": vcircle(r, 24, "minecraft:soul_particle", 232 - i, 210 - i,
                            cz=CIRCLE_Z + 0.6),
        })

    chains = [
        {"id": "init", "kind": "impulse", "button": True, "label": "初始化",
         "cmds": init_cmds(ta)},
        {"id": "trigger", "kind": "gated", "label": "触发",
         "gate": "execute if entity %s" % BOOK, "cmds": trigger_cmds()},
        {"id": "cast", "kind": "gated", "label": "施法",
         "gate": "execute if entity @a[scores={cam_cast=1}]", "cmds": cast_cmds()},
        {"id": "render", "kind": "gated", "label": "渲染",
         "gate": "execute if entity %s" % SHIELD, "cmds": render_cmds()},
    ] + [
        {"id": "ph_" + p, "kind": "gated", "label": "剑·" + p,
         "gate": PHASE_GATE[p], "cmds": phase_cmds(p)}
        for p in PHASES
    ] + open_chains + deco_chains + [
        {"id": "fx_spoke1", "kind": "gated", "label": "法阵·辐条甲",
         "gate": "execute if entity @a[scores={cam_t=214..238}]", "cmds": sp[:96]},
        {"id": "fx_spoke2", "kind": "gated", "label": "法阵·辐条乙",
         "gate": "execute if entity @a[scores={cam_t=214..238}]", "cmds": sp[96:]},
        {"id": "fx_imp1", "kind": "gated", "label": "法阵·冲击甲",
         "gate": "execute if entity @a[scores={cam_t=72..78}]", "cmds": im[:120]},
        {"id": "fx_imp2", "kind": "gated", "label": "法阵·冲击乙",
         "gate": "execute if entity @a[scores={cam_t=72..78}]", "cmds": im[120:]},
        {"id": "fx_trail", "kind": "gated", "label": "法阵·剑尾",
         "gate": "execute if entity @a[scores={cam_t=69..76}]", "cmds": tr},
        {"id": "fx_ember", "kind": "gated", "label": "法阵·余烬",
         "gate": "execute if entity @a[scores={cam_t=1..40}]", "cmds": em},
        {"id": "clock", "kind": "gated", "label": "运镜",
         "gate": "execute if entity @a[scores={cam_t=0..}]", "cmds": clock_cmds()},
        {"id": "cool", "kind": "gated", "label": "冷却",
         "gate": "execute if entity @a[scores={cam_cd=1..}]", "cmds": cooldown_cmds()},
        {"id": "abort", "kind": "impulse", "button": True, "label": "中断",
         "cmds": abort_cmds()},
    ]
    return {
        "meta": {"name": "十方剑阵", "spawn": [8, -58, 7], "gametype": "creative"},
        "chains": chains,
        "panels": [
            {"label": "面板·运镜断开", "cmds": ["{SET:clock:dis}"]},
            {"label": "面板·运镜接通", "cmds": ["{SET:clock:arm}"]},
            {"label": "面板·渲染断开", "cmds": ["{SET:render:dis}"]},
            {"label": "面板·渲染接通", "cmds": ["{SET:render:arm}"]},
        ],
    }


def to_system(s):
    chains = []
    for ch in s["chains"]:
        cmds = list(ch["cmds"])
        if ch["kind"] == "gated":
            cmds = ["{RESET}"] + cmds
        chains.append({"id": ch["id"], "kind": ch["kind"], "label": ch.get("label"),
                       "gate": ch.get("gate"), "cmds": cmds,
                       "button": ch.get("button", ch["kind"] == "impulse")})
    for p in s["panels"]:
        chains.append({"id": "panel", "kind": "impulse", "label": p["label"],
                       "cmds": p["cmds"], "button": True})

    props = [
        {"kind": "sign", "front": ["§l§b十方剑阵", "§7主手持附魔书即施放",
                                   "§8冷却 25 秒", "§8正前方竖直法阵"]},
        {"kind": "sign", "front": ["§l§a七幕", "§71 结印 · 2 凝剑",
                                   "§73 悬停 · 4 蓄力", "§75 突刺 · 6 余韵"]},
        {"kind": "sign", "front": ["§l§e结构", "§710 剑平行 · 穿阵而出",
                                   "§7法阵 5 格前 · 半径 3.3", "§7清理：tp 虚空"]},
        {"kind": "chest", "name": "剑阵", "items": [
            B.item_nbt("enchanted_book", display_name="§b十方剑阵",
                       lore=["§7主手持此典 → 召十刃", "§8冷却 25 秒"]),
            B.item_nbt("netherite_sword", display_name="§8下界合金剑",
                       lore=["§7剑阵本体"]),
            B.item_nbt("end_rod", display_name="§f法阵光点", lore=["§7结印环"]),
            B.item_nbt("soul_lantern", display_name="§3外环魂火", lore=["§7装饰环"]),
        ]},
    ]
    return {"chains": chains, "props": props, "props_pedestal": True}


def measure_ta(s):
    blocks, _, _ = B.build_scene(to_system(s))
    xs = [x for (x, y, z) in blocks]
    zs = [z for (x, y, z) in blocks]
    return ("tickingarea add ~%d ~-4 ~%d ~%d ~4 ~%d sword_array"
            % (min(xs) - 9, min(zs) - 8 - 2, max(xs) - 9, max(zs) - 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-spec")
    ap.add_argument("--spec")
    ap.add_argument("--template")
    ap.add_argument("--out")
    a = ap.parse_args()

    if a.dump_spec:
        s = spec(measure_ta(spec()))
        os.makedirs(os.path.dirname(os.path.abspath(a.dump_spec)), exist_ok=True)
        with open(a.dump_spec, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
        n = sum(len(c["cmds"]) for c in s["chains"]) + sum(len(p["cmds"]) for p in s["panels"])
        print("[spec] %s  链 %d 条 / 展示体 %d / 命令 %d 条"
              % (a.dump_spec, len(s["chains"]), N, n))
        return

    if not (a.spec and a.template and a.out):
        ap.error("生成世界需要 --spec / --template / --out")
    with open(a.spec, encoding="utf-8") as f:
        s = json.load(f)
    s = spec(measure_ta(s))
    m = s["meta"]
    B.CHAIN_SUMMARY["init"] = "计分项 / 规则 / 常加载"
    B.CHAIN_SUMMARY["trigger"] = "持书 + 冷却就绪 → 置施法触发位"
    B.CHAIN_SUMMARY["clock"] = "倒计时 + 十段运镜 + FOV + 收尾（tp 虚空）"
    info = B.build(a.template, a.out, m["name"], m.get("spawn"), 1, to_system(s))
    print("[完成] %s" % info["out"])
    print("        区块 %d / 命令方块 %d / 按钮 %d / 说明区 %d / 展示体 %d"
          % (info["chunks"], info["blocks"], info["buttons"], info["props"], N))
    if info["blocks"] < MIN_BLOCKS:
        raise SystemExit("命令方块 %d < 硬指标 %d" % (info["blocks"], MIN_BLOCKS))


if __name__ == "__main__":
    main()
