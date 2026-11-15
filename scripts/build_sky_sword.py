#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天穹 · 万剑归宗 —— 120 秒九层法阵（10 个展示实体 + 粒子绘阵 + 电影运镜）。

实体预算（硬上限 10）：
    1  太初·天穹（神剑，垂直悬浮，剑尖向下）
    2-9  悬浮符文 ×8（第三层升起，第六层排布）
    10 天穹阵核心（空中倒置法阵的中心）

九层全部由粒子逐点绘制（每一环 = N 条命令）：
    1 核心剑印  2 内环几何  3 文字环  4 能量带  5 十二星位
    6 悬浮符文(实体)  7 封印环  8 天穹阵  9 虚空边界

时间轴（cam_t 从 2400 倒数，1 秒 = 20 刻）：
    0-12s   万古沉寂 2400..2160
    12-25s  初始阵图 2160..1900
    25-38s  符文觉醒 1900..1640
    38-52s  神剑显现 1640..1360
    52-66s  十二星位 1360..1080
    66-80s  天地双阵 1080..800
    80-94s  万阵共鸣 800..520
    94-110s 太初解封 520..200
    110-120s 神迹永存 200..0

用法：
    python build_sky_sword.py --dump-spec out/spec.json
    python build_sky_sword.py --spec out/spec.json --template t.mcworld --out out/_build.mcworld
"""
import argparse
import json
import math
import os
import sys

# 依赖同目录的 build_cbworld.py —— 用相对路径，项目级 / 用户级都能跑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B

SHIELD = "@e[scores={fmbe_sword=1..}]"
BOOK = "@a[hasitem={item=enchanted_book,location=slot.weapon.mainhand}]"
CASTER = "@a[scores={cam_cast=1},c=1]"

DUR = 2400          # 120 秒
CD = 3000           # 150 秒冷却
MIN_BLOCKS = 1500
SKY_Y = 12.0        # 天穹阵高度

GRID = sorted([(dx, dz) for dz in range(-8, 9, 2) for dx in range(-8, 9, 2)
               if not (dx == 0 and dz == 0)], key=lambda p: (p[0] ** 2 + p[1] ** 2, p[1], p[0]))


# ---------------------------------------------------------------- 粒子画笔
def P(x, y, z, particle, t):
    return ('execute as @a[scores={cam_t=%d}] at @s run particle %s ~%.2f ~%.2f ~%.2f'
            % (t, particle, x, y, z))


def ring(r, n, y, particle, t0, t1, phase=0.0, arc=1.0):
    """一圈：n 点沿圆周，从 t0 逐点画到 t1（cam_t 倒数，t0 > t1）。"""
    out = []
    for k in range(n):
        th = 2 * math.pi * k / n * arc + math.radians(phase)
        t = t0 - round((t0 - t1) * k / max(1, n - 1))
        out.append(P(r * math.cos(th), y, r * math.sin(th), particle, t))
    return out


def line(p0, p1, n, particle, t0, t1):
    """两点之间铺 n 个点。"""
    out = []
    for k in range(n):
        f = k / max(1, n - 1)
        x = p0[0] + (p1[0] - p0[0]) * f
        y = p0[1] + (p1[1] - p0[1]) * f
        z = p0[2] + (p1[2] - p0[2]) * f
        t = t0 - round((t0 - t1) * k / max(1, n - 1))
        out.append(P(x, y, z, particle, t))
    return out


def star(points, r, y, particle, t0, t1, phase=0.0):
    """正多边形（points 个顶点的连线）。"""
    out = []
    verts = [(r * math.cos(2 * math.pi * i / points + math.radians(phase)), y,
              r * math.sin(2 * math.pi * i / points + math.radians(phase)))
             for i in range(points)]
    step = max(1, (t0 - t1) // points)
    for i in range(points):
        out += line(verts[i], verts[(i + 1) % points], 8, particle,
                    t0 - i * step, t0 - (i + 1) * step)
    return out


# ---------------------------------------------------------------- 九层法阵
def layer1():      # 核心剑印：三环 + 八角星
    c = []
    c += ring(0.9, 24, 0.05, "minecraft:endrod", 2150, 2120)
    c += ring(1.5, 24, 0.05, "minecraft:enchanting_table_particle", 2140, 2110)
    c += ring(2.1, 24, 0.05, "minecraft:endrod", 2130, 2100)
    c += star(8, 1.9, 0.06, "minecraft:totem_particle", 2125, 2095)
    return c


def layer2():      # 内环几何：六芒星 + 三角 + 方
    c = []
    c += star(6, 3.0, 0.05, "minecraft:endrod", 2100, 2060, phase=0)
    c += star(6, 3.0, 0.05, "minecraft:endrod", 2090, 2050, phase=30)
    c += star(3, 3.8, 0.05, "minecraft:enchanting_table_particle", 2070, 2040)
    c += star(4, 4.4, 0.05, "minecraft:enchanting_table_particle", 2060, 2030, phase=45)
    return c


def layer3():      # 文字环：两圈密集点
    c = []
    c += ring(5.2, 32, 0.05, "minecraft:sparkler_emitter", 2030, 1970)
    c += ring(5.8, 32, 0.05, "minecraft:sparkler_emitter", 2010, 1950, phase=5)
    return c


def layer4():      # 能量带：三条独立旋转的光带
    c = []
    c += ring(6.4, 36, 0.10, "minecraft:soul_particle", 1900, 1850)
    c += ring(6.9, 36, 0.25, "minecraft:endrod", 1880, 1830, phase=10)
    c += ring(7.4, 36, 0.40, "minecraft:enchanting_table_particle", 1860, 1810, phase=20)
    return c


def layer5():      # 十二星位：12 个节点 + 连接弧
    c = []
    for i in range(12):
        th = 2 * math.pi * i / 12
        cx, cz = 4.6 * math.cos(th), 4.6 * math.sin(th)
        t = 1350 - i * 18
        c.append(P(cx, 0.9, cz, "minecraft:totem_particle", t))
        c.append(P(cx, 1.1, cz, "minecraft:endrod", t - 2))
        # 节点自身的小环
        for k in range(6):
            a = 2 * math.pi * k / 6
            c.append(P(cx + 0.45 * math.cos(a), 0.9, cz + 0.45 * math.sin(a),
                       "minecraft:totem_particle", t - 4 - k))
        # 连向中心
        c += line((cx, 0.9, cz), (cx * 0.3, 0.9, cz * 0.3), 5,
                  "minecraft:endrod", t - 10, t - 14)
    # 十二节点之间的环
    c += ring(4.6, 36, 0.95, "minecraft:totem_particle", 1120, 1085)
    return c


def layer7():      # 封印环：两圈大环 + 八根符号柱
    c = []
    c += ring(8.0, 40, 0.05, "minecraft:endrod", 1080, 1030)
    c += ring(8.6, 40, 0.05, "minecraft:enchanting_table_particle", 1060, 1010)
    for i in range(8):
        th = 2 * math.pi * i / 8
        x, z = 8.3 * math.cos(th), 8.3 * math.sin(th)
        c += line((x, 0.2, z), (x, 3.2, z), 6, "minecraft:soul_particle",
                  1050 - i * 4, 1030 - i * 4)
    return c


def layer8():      # 天穹阵：空中倒置法阵
    c = []
    c += ring(2.2, 36, SKY_Y, "minecraft:endrod", 1060, 1010)
    c += ring(3.6, 40, SKY_Y, "minecraft:enchanting_table_particle", 1040, 980)
    c += ring(4.8, 40, SKY_Y + 0.6, "minecraft:endrod", 1020, 960)
    c += star(6, 4.0, SKY_Y, "minecraft:totem_particle", 1000, 950)
    # 天地连线
    for i in range(12):
        th = 2 * math.pi * i / 12
        c += line((4.0 * math.cos(th), 0.4, 4.0 * math.sin(th)),
                  (4.0 * math.cos(th), SKY_Y, 4.0 * math.sin(th)), 8,
                  "minecraft:endrod", 960 - i * 3, 940 - i * 3)
    return c


def layer9():      # 虚空边界：球形能量壳
    c = []
    R = 9.5
    for i, y in enumerate([1.0, 3.0, 5.5, 8.0, 10.5]):
        rr = math.sqrt(max(0.25, R * R - (y - 5.5) ** 2))
        c += ring(rr, 32, y, "minecraft:soul_particle", 520 - i * 8, 480 - i * 8)
    return c


# ---------------------------------------------------------------- 其它特效
def opening():     # 0-12s 沉寂
    c = [P(0, 0.1, 0, "minecraft:endrod", 2390)]
    c += line((0, 0.05, 0), (3.0, 0.05, 0), 6, "minecraft:endrod", 2340, 2320)
    c += ring(2.4, 24, 0.05, "minecraft:endrod", 2300, 2270, arc=0.75)
    c += ring(3.0, 16, 0.05, "minecraft:sparkler_emitter", 2260, 2230, arc=0.6)
    c += line((0, 0.2, 0), (0, 2.2, 0), 10, "minecraft:endrod", 2200, 2170)
    c += line((-0.5, 1.6, 0), (0.5, 1.6, 0), 5, "minecraft:endrod", 2190, 2175)
    return c


def sword_pillar():  # 神剑显现：垂直光柱 + 环形波
    c = []
    c += line((0, 0.2, 0), (0, 6.0, 0), 20, "minecraft:endrod", 1640, 1600)
    c += ring(1.0, 32, 1.5, "minecraft:totem_particle", 1560, 1530)
    c += ring(1.8, 32, 1.5, "minecraft:endrod", 1550, 1520)
    c += ring(2.6, 32, 1.5, "minecraft:totem_particle", 1540, 1510)
    return c


def resonance():   # 80-94s 共鸣闪烁
    c = []
    for w, t in enumerate([780, 740, 700, 660, 620, 580, 540]):
        c += ring(5.0 + w * 0.4, 24, 0.1 + w * 0.2, "minecraft:totem_particle",
                  t, t - 6)
    return c


def burst():       # 94-110s 解封
    c = []
    c += ring(1.2, 36, 1.0, "minecraft:endrod", 520, 470)
    c += ring(2.4, 36, 1.4, "minecraft:totem_particle", 500, 450)
    c += ring(3.6, 40, 1.8, "minecraft:endrod", 480, 430)
    c += ring(4.8, 40, 2.2, "minecraft:enchanting_table_particle", 460, 410)
    c += star(12, 5.2, 0.2, "minecraft:totem_particle", 440, 390)
    c += ring(6.4, 40, SKY_Y, "minecraft:endrod", 420, 370)
    # 110s 环形光波
    for i, r in enumerate([2.0, 3.2, 4.4, 5.6, 6.8, 8.0, 9.2, 10.4]):
        c += ring(r, 24, 0.1 + i * 0.25, "minecraft:totem_particle", 200 - i, 196 - i)
    return c


def ending():      # 110-120s 余韵
    c = []
    c += ring(9.0, 32, 0.1, "minecraft:soul_particle", 180, 140)
    c += ring(6.0, 32, SKY_Y, "minecraft:soul_particle", 160, 120)
    c += ring(2.0, 24, 1.2, "minecraft:endrod", 140, 100)
    return c


# ---------------------------------------------------------------- 实体
def actors():
    """10 把剑 —— 全部是主体，不再拿符文凑数。

    每把剑的 basepos 固定为 (0, -R, y)，靠 v.yrot 带着 basepos 一起转：
    世界偏移 = R(yrot)·basepos，所以改 yrot 就是在以玩家为圆心公转，
    剑身朝向也同步跟着转 —— 这就是"用 Molang 跟随朝向"。
    """
    out = []
    for i in range(10):
        sx, sz = GRID[i]
        inner = i >= 5
        out.append(dict(
            sx=sx, sz=sz, sy=0, item="minecraft:netherite_sword",
            r=(3.4 if inner else 4.9),
            y=(3.7 if inner else 2.1),
            th=(i - 5) * 72.0 if inner else i * 72.0,
            dir=(-1 if inner else 1),
        ))
    return out


ACTORS = actors()
N = len(ACTORS)


def actor_phase(name):
    """剑的 Molang：v.yrot 既管朝向也管公转（basepos 跟着转）。"""
    out = []
    for a in ACTORS:
        R, Y, th, d = a["r"], a["y"], a["th"], a["dir"]
        # basepos 固定在 -R（正后方），转 yrot 就绕玩家转圈
        base = "v.xbasepos=0;v.zbasepos=%g;v.ybasepos=%g;" % (-R * 16, Y * 16)
        if name == "p1":          # 沉睡：缩在中心
            b = ("v.xbasepos=0;v.zbasepos=0;v.ybasepos=8;v.scale=0.02;v.zrot=90;"
                 "v.yrot=%g;" % th)
        elif name == "p4":        # 神剑显现：从中心散开成剑轮
            g = "(1-math.exp(-(q.life_time-38)*1.8))"
            b = ("v.xbasepos=0;v.zbasepos=%g*%s;v.ybasepos=%g*%s;"
                 "v.scale=2.4*%s;v.zrot=90;v.yrot=%g+q.life_time*%g;"
                 % (-R * 16, g, Y * 16, g, g, th, 18 * d))
        elif name == "p6":        # 天地双阵：外圈加速、内圈反向
            b = (base + "v.scale=2.4;v.zrot=90;v.yrot=%g+q.life_time*%g;"
                 % (th, 42 * d))
        elif name == "p8":        # 解封：全体收束再炸开
            k = "math.max(0,q.life_time-94)"
            b = ("v.xbasepos=0;v.zbasepos=%g*(1-0.45*math.min(1,%s*0.7));"
                 "v.ybasepos=%g*(1+0.25*math.min(1,%s*0.7));"
                 "v.scale=2.4+0.6*math.min(1,%s*0.7);v.zrot=90;"
                 "v.yrot=%g+q.life_time*%g;" % (-R * 16, k, Y * 16, k, k, th, 90 * d))
        else:                     # 稳态 / 余韵
            b = (base + "v.scale=2.4;v.zrot=90;v.yrot=%g+q.life_time*%g;"
                 % (th, 30 * d))
        out.append(b)
    return out


ACTS = [
    ("p1", "execute if entity @a[scores={cam_t=1640..2400}]"),
    ("p4", "execute if entity @a[scores={cam_t=1080..1640}]"),
    ("p6", "execute if entity @a[scores={cam_t=520..1080}]"),
    ("p8", "execute if entity @a[scores={cam_t=200..520}]"),
    ("p9", "execute if entity @a[scores={cam_t=1..200}]"),
]


def at_actor(a, cmd):
    return ("execute at %s positioned ~%d ~%d ~%d run %s"
            % (CASTER, a["sx"], a["sy"], a["sz"], cmd))


# ---------------------------------------------------------------- 链
def init_cmds(ta):
    return [
        "gamerule sendcommandfeedback false",
        "gamerule commandblockoutput false",
        "gamerule showdeathmessages false",
        "gamerule announceadvancements false",
        "gamerule showrecipemessages false",
        "gamerule showcoordinates false",
        'scoreboard objectives add cam_t dummy "归宗计时"',
        'scoreboard objectives add cam_cast dummy "归宗触发"',
        'scoreboard objectives add cam_cd dummy "归宗冷却"',
        'scoreboard objectives add fmbe_sword dummy "剑阵展示体"',
        "tickingarea remove sky_sword",
        ta,
        'tellraw @a {"rawtext":[{"text":"§b天穹 · 万剑归宗 §8· §f手持附魔书开启，§7时长 120 秒 / 冷却 150 秒"}]}',
    ]


def trigger_cmds():
    cond = ("%s unless entity @s[scores={cam_cd=1..}] "
            "unless entity @s[scores={cam_t=0..}]" % BOOK)
    return [
        "execute as %s run scoreboard players set @s cam_cast 1" % cond,
        "execute as %s run playsound random.orb @s ~ ~ ~ 0.6 1.6" % cond,
    ]


def cast_cmds():
    c = [
        "execute as %s run camera @s clear" % CASTER,
        "execute as %s run camera @s fov_clear" % CASTER,
        "scoreboard players set %s cam_cd %d" % (CASTER, CD),
        "scoreboard players set %s cam_t %d" % (CASTER, DUR),
        "inputpermission set %s movement disabled" % CASTER,
        "tp @e[scores={fmbe_sword=0}] ~ -400 ~",
    ]
    for i, a in enumerate(ACTORS, start=1):
        c.append("execute at %s run summon fox ~%d ~%d ~%d" % (CASTER, a["sx"], a["sy"], a["sz"]))
        c.append(at_actor(a, "tp @e[type=fox,r=2,c=1] ~ ~ ~ ~ ~"))
        c.append(at_actor(a, "replaceitem entity @e[type=fox,r=2,c=1] "
                             "slot.weapon.mainhand 0 %s" % a["item"]))
        c.append(at_actor(a, "scoreboard players set @e[type=fox,r=2,c=1] fmbe_sword %d" % i))
        c.append(at_actor(a, 'playanimation @e[type=fox,r=2,c=1] '
                             'animation.player.attack.positions none 0 '
                             '"v.scale=0.02;" fmbe.init'))
    c += [
        "effect %s invisibility 999999 1 true" % SHIELD,
        "effect %s resistance 999999 255 true" % SHIELD,
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.aggro",
        "stopsound @a mob.fox.bite",
        "stopsound @a mob.fox.eat",
        "playsound random.explode @a[r=48] ~ ~ ~ 0.5 0.5",
        "playsound beacon.activate @a[r=48] ~ ~ ~ 0.9 0.7",
        "playsound conduit.activate @a[r=48] ~ ~ ~ 0.7 0.9",
        "playsound raid.horn @a[r=48] ~ ~ ~ 0.8 0.8",
        'execute as @a[scores={cam_t=0..}] run titleraw @s title '
        '{"rawtext":[{"text":"§8§l天 穹"}]}',
        'execute as @a[scores={cam_t=0..}] run titleraw @s subtitle '
        '{"rawtext":[{"text":"§7万剑归宗"}]}',
        "scoreboard players set @a cam_cast 0",
    ]
    return c


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
        "execute at %s run tp %s ~ ~ ~ ~ ~" % (CASTER, SHIELD),
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.bite",
    ]


def actor_cmds(name):
    return ['playanimation @e[scores={fmbe_sword=%d}] '
            'animation.player.attack.positions none 0 "%s" fmbe.ph' % (i, b)
            for i, b in enumerate(actor_phase(name), start=1)]


def clock_cmds():
    """22 段远景运镜（最近 16 格）+ 60 个音效点。"""
    shots = [
        (2395, "^ ^4 ^-22",   "out_cubic", 6.0),   # 远景推进
        (2200, "^ ^8 ^-18",   "in_out_sine", 4.0),
        (2050, "^ ^22 ^-8",   "in_out_sine", 4.0),  # 高空俯视阵图
        (1900, "^14 ^10 ^-14", "in_out_sine", 4.0),
        (1750, "^-14 ^10 ^-14", "in_out_sine", 4.0),
        (1640, "^ ^6 ^-16",   "in_out_sine", 3.0),  # 神剑显现中景
        (1500, "^ ^10 ^-24",  "in_out_sine", 3.0),  # 拉远看剑轮
        (1360, "^16 ^12 ^-18", "in_out_sine", 3.0),
        (1200, "^-18 ^8 ^-16", "in_out_sine", 3.0),
        (1080, "^ ^24 ^-14",  "in_out_sine", 3.0),  # 俯视天地双阵
        (950,  "^ ^14 ^-28",  "in_out_sine", 3.0),
        (800,  "^20 ^10 ^-20", "in_out_sine", 3.0),
        (650,  "^-20 ^10 ^-20", "in_out_sine", 3.0),
        (520,  "^ ^8 ^-30",   "out_quad", 3.0),     # 解封前大远景
        (380,  "^ ^16 ^-26",  "in_out_sine", 2.5),
        (260,  "^ ^6 ^-18",   "out_quad", 2.0),
        (200,  "^ ^12 ^-32",  "out_quad", 1.5),     # 110s 光波
        (120,  "^14 ^8 ^-24", "in_out_sine", 3.0),
        (40,   "^ ^6 ^-18",   "out_quad", 2.0),
        (8,    "^ ^5 ^-16",   "out_quad", 1.5),
    ]
    c = ["execute as @a[scores={cam_t=1..}] run scoreboard players remove @s cam_t 1"]
    for t, pos, ease, dur in shots:
        c.append('execute as @a[scores={cam_t=%d}] at @s run camera @s set minecraft:free '
                 'ease %s %s pos %s facing ~ ~2.5 ~' % (t, dur, ease, pos))
    # FOV：远景要宽
    c += [
        "execute as @a[scores={cam_t=2395}] run camera @s fov_set 55 1.0 out_quad",
        "execute as @a[scores={cam_t=2050}] run camera @s fov_set 78 3.0 in_out_sine",
        "execute as @a[scores={cam_t=1640}] run camera @s fov_set 62 2.0 in_out_sine",
        "execute as @a[scores={cam_t=1080}] run camera @s fov_set 88 2.5 in_out_sine",
        "execute as @a[scores={cam_t=520}] run camera @s fov_set 70 2.0 in_out_sine",
        "execute as @a[scores={cam_t=200}] run camera @s fov_set 105 0.4 out_quad",
        "execute as @a[scores={cam_t=120}] run camera @s fov_set 68 2.5 in_out_sine",
        "execute as @a[scores={cam_t=1600}] run camerashake add @s 0.25 0.5 positional",
        "execute as @a[scores={cam_t=1360}] run camerashake add @s 0.3 0.5 positional",
        "execute as @a[scores={cam_t=800}] run camerashake add @s 0.4 0.6 positional",
        "execute as @a[scores={cam_t=200}] run camerashake add @s 1.3 1.0 positional",
        "execute as @a[scores={cam_t=200}] at @s run particle minecraft:huge_explosion_emitter ^ ^3 ^4",
    ]
    # 音效时间轴：(剩余刻, 音效, 音量, 音高)
    cues = [
        (2390, "ambient.cave", 1.0, 0.6), (2388, "random.fizz", 0.4, 0.5),
        (2340, "ambient.cave", 0.8, 0.55), (2300, "random.fizz", 0.5, 0.7),
        (2260, "bell.ring", 0.5, 0.5), (2220, "ambient.cave", 0.7, 0.5),
        (2160, "beacon.activate", 0.7, 0.6), (2158, "conduit.activate", 0.5, 0.7),
        (2100, "note.chime", 0.8, 0.8), (2080, "note.chime", 0.8, 1.0),
        (2060, "note.chime", 0.8, 1.2), (2030, "note.bell", 0.9, 0.7),
        (1980, "conduit.activate", 0.6, 0.9), (1950, "note.pling", 0.9, 0.9),
        (1930, "note.pling", 0.9, 1.1), (1910, "note.pling", 0.9, 1.3),
        (1900, "ambient.cave", 0.8, 0.6), (1840, "note.flute", 0.8, 0.7),
        (1810, "note.flute", 0.8, 0.9), (1750, "note.chime", 0.9, 1.0),
        (1700, "beacon.power", 0.6, 0.8), (1660, "ambient.cave", 0.9, 0.5),
        (1640, "item.trident.thunder", 1.0, 0.9),
        (1638, "beacon.activate", 1.0, 0.8), (1636, "raid.horn", 0.9, 0.9),
        (1600, "note.pling", 1.0, 1.0), (1590, "note.pling", 1.0, 1.25),
        (1580, "note.pling", 1.0, 1.5), (1560, "mob.irongolem.hit", 0.8, 1.2),
        (1520, "bell.ring", 0.9, 0.8), (1470, "note.chime", 0.8, 1.1),
        (1400, "beacon.power", 0.7, 1.0), (1360, "totem.use", 0.9, 0.9),
        (1358, "note.bell", 0.9, 1.0), (1320, "note.chime", 0.8, 1.2),
        (1290, "note.chime", 0.8, 1.3), (1260, "note.chime", 0.8, 1.4),
        (1230, "note.chime", 0.8, 1.5), (1200, "note.pling", 0.9, 1.2),
        (1140, "conduit.activate", 0.7, 1.0), (1080, "beacon.activate", 1.0, 0.9),
        (1078, "ambient.weather.thunder", 0.9, 0.8),
        (1020, "note.bell", 0.9, 0.9), (980, "note.bell", 0.9, 1.1),
        (940, "ambient.cave", 0.8, 0.6), (880, "conduit.activate", 0.7, 1.1),
        (800, "mob.enderdragon.growl", 0.9, 0.6),
        (798, "beacon.power", 0.8, 0.9), (760, "note.chime", 0.8, 1.3),
        (730, "note.chime", 0.8, 1.4), (700, "conduit.activate", 0.7, 1.2),
        (650, "note.pling", 0.9, 1.3), (620, "note.pling", 0.9, 1.5),
        (580, "raid.horn", 0.9, 1.0), (578, "item.trident.thunder", 0.8, 1.1),
        (520, "mob.wither.shoot", 0.9, 0.7), (518, "beacon.activate", 1.0, 1.0),
        (516, "raid.horn", 1.0, 1.1), (460, "note.bell", 0.9, 1.2),
        (420, "ambient.weather.thunder", 0.8, 0.9), (340, "note.pling", 0.9, 1.4),
        (320, "note.pling", 0.9, 1.5), (300, "note.pling", 0.9, 1.6),
        (260, "conduit.activate", 0.8, 1.3), (230, "note.bell", 1.0, 1.4),
        (200, "random.explode", 1.0, 0.7), (199, "item.trident.thunder", 1.0, 0.9),
        (198, "mob.enderdragon.growl", 1.0, 0.7), (197, "totem.use", 1.0, 1.0),
        (150, "note.harp", 0.8, 0.9), (130, "note.harp", 0.8, 1.1),
        (100, "bell.ring", 0.8, 1.0), (60, "note.flute", 0.7, 0.8),
        (30, "ambient.cave", 0.6, 0.7),
    ]
    for t, snd, vol, pit in cues:
        c.append('execute as @a[scores={cam_t=%d}] at @s run playsound %s @a[r=48] ~ ~ ~ %s %s'
                 % (t, snd, vol, pit))
    c += [
        "execute as @a[scores={cam_t=0}] run camera @s clear",
        "execute as @a[scores={cam_t=0}] run camera @s fov_clear 2.0 out_elastic",
        "execute as @a[scores={cam_t=0}] run inputpermission set @s movement enabled",
        "execute as @a[scores={cam_t=0}] run scoreboard players set @e[scores={fmbe_sword=1..}] fmbe_sword 0",
        "execute as @a[scores={cam_t=0}] run tp @e[scores={fmbe_sword=0}] ~ -400 ~",
        "execute as @a[scores={cam_t=0}] run scoreboard players set @s cam_t -1",
        'execute as @a[scores={cam_t=-1}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§7万剑归宗"}]}',
    ]
    return c


def cooldown_cmds():
    return [
        "execute as @a[scores={cam_cd=1..}] run scoreboard players remove @s cam_cd 1",
        'execute as @a[scores={cam_cd=1..}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§8万剑归宗 §7冷却 §f"},'
        '{"score":{"name":"@s","objective":"cam_cd"}}]}',
    ]


def abort_cmds():
    return [
        "camera @a clear",
        "camera @a fov_clear",
        "inputpermission set @a movement enabled",
        "scoreboard players set @e[scores={fmbe_sword=1..}] fmbe_sword 0",
        "tp @e[scores={fmbe_sword=0}] ~ -400 ~",
        "scoreboard players set @a cam_t -1",
        "scoreboard players set @a cam_cast 0",
        'execute as @a[scores={cam_t=-1}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§c已中断"}]}',
    ]


def spec(ta="tickingarea add circle ~ ~ ~ 4 sky_sword"):
    fx = [
        ("开场·沉寂", "execute if entity @a[scores={cam_t=2160..2400}]", opening()),
        ("一层·剑印", "execute if entity @a[scores={cam_t=2095..2150}]", layer1()),
        ("二层·几何", "execute if entity @a[scores={cam_t=2030..2100}]", layer2()),
        ("三层·文字", "execute if entity @a[scores={cam_t=1950..2030}]", layer3()),
        ("四层·能量带", "execute if entity @a[scores={cam_t=1810..1900}]", layer4()),
        ("七层·封印", "execute if entity @a[scores={cam_t=1010..1080}]", layer7()),
        ("八层·天穹", "execute if entity @a[scores={cam_t=940..1060}]", layer8()),
        ("五层·星位", "execute if entity @a[scores={cam_t=1085..1350}]", layer5()),
        ("九层·边界", "execute if entity @a[scores={cam_t=480..520}]", layer9()),
        ("剑·显现", "execute if entity @a[scores={cam_t=1510..1640}]", sword_pillar()),
        ("共鸣", "execute if entity @a[scores={cam_t=540..780}]", resonance()),
        ("解封", "execute if entity @a[scores={cam_t=196..520}]", burst()),
        ("余韵", "execute if entity @a[scores={cam_t=100..180}]", ending()),
    ]
    # 大块特效按 80 条拆链，避免窗口内每刻全跑
    fx_chains = []
    for label, gate, cmds in fx:
        parts = [cmds[i:i + 80] for i in range(0, len(cmds), 80)] or [[]]
        for j, part in enumerate(parts):
            fx_chains.append({"id": "fx_%d_%d" % (len(fx_chains), j),
                              "kind": "gated",
                              "label": label if len(parts) == 1 else "%s%d" % (label, j + 1),
                              "gate": gate, "cmds": part})

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
        {"id": "act_" + n, "kind": "gated", "label": "器·" + n, "gate": g,
         "cmds": actor_cmds(n)}
        for n, g in ACTS
    ] + fx_chains + [
        {"id": "clock", "kind": "gated", "label": "运镜",
         "gate": "execute if entity @a[scores={cam_t=0..}]", "cmds": clock_cmds()},
        {"id": "cool", "kind": "gated", "label": "冷却",
         "gate": "execute if entity @a[scores={cam_cd=1..}]", "cmds": cooldown_cmds()},
        {"id": "abort", "kind": "impulse", "button": True, "label": "中断",
         "cmds": abort_cmds()},
    ]
    return {
        "meta": {"name": "万剑归宗", "spawn": [8, -58, 7], "gametype": "creative"},
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
        {"kind": "sign", "front": ["§l§8天穹 · 万剑归宗", "§7手持附魔书开启",
                                   "§8时长 120 秒", "§8冷却 150 秒"]},
        {"kind": "sign", "front": ["§l§b九层法阵", "§71 剑印 · 2 几何",
                                   "§73 文字 · 4 能量带", "§75 星位 · 6 符文"]},
        {"kind": "sign", "front": ["§l§e剑轮", "§7十剑双层 · 反向公转",
                                   "§7朝向由 Molang 跟随", "§8实体仅 10 个"]},
        {"kind": "chest", "name": "归宗", "items": [
            B.item_nbt("enchanted_book", display_name="§8天穹 · 万剑归宗",
                       lore=["§7主手持此典 → 开启归宗", "§8时长 120 秒 / 冷却 150 秒"]),
            B.item_nbt("netherite_sword", display_name="§f太初 · 天穹",
                       lore=["§7法阵核心神剑"]),
            B.item_nbt("iron_sword", display_name="§7备用剑",
                       lore=["§7剑轮替补"]),
            B.item_nbt("beacon", display_name="§e天穹核心", lore=["§7由粒子绘制"]),
        ]},
    ]
    return {"chains": chains, "props": props, "props_pedestal": True}


def measure_ta(s):
    blocks, _, _ = B.build_scene(to_system(s))
    xs = [x for (x, y, z) in blocks]
    zs = [z for (x, y, z) in blocks]
    return ("tickingarea add ~%d ~-4 ~%d ~%d ~4 ~%d sky_sword"
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
    B.CHAIN_SUMMARY["trigger"] = "持书 + 冷却就绪 → 置归宗触发位"
    B.CHAIN_SUMMARY["clock"] = "2400 刻倒计时 + 22 段运镜 + FOV + 收尾"
    info = B.build(a.template, a.out, m["name"], m.get("spawn"), 1, to_system(s))
    print("[完成] %s" % info["out"])
    print("        区块 %d / 命令方块 %d / 按钮 %d / 说明区 %d / 展示体 %d"
          % (info["chunks"], info["blocks"], info["buttons"], info["props"], N))
    if info["blocks"] < MIN_BLOCKS:
        raise SystemExit("命令方块 %d < 硬指标 %d" % (info["blocks"], MIN_BLOCKS))


if __name__ == "__main__":
    main()
