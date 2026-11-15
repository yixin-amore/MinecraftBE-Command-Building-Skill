#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""太初 · 紫晶天穹 —— 120 秒以玩家为中心的三维剑阵。

实体（65 个）：
    1        中央神剑（玩家正前方）
    2-13     十二把能量剑（垂直阵环，后期转向神剑并消散）
    14-65    五十二条紫水晶块（五组倾斜轨道）

倾斜轨道的做法（关键）：
    basepos 固定 (0, 0, -R*16)，只给两个角：
        v.xrot = 倾角（0=水平，30/60=倾斜，90=垂直）
        v.yrot 累加（每刻 +ω，在倾斜平面内公转）
    世界位置 = 旋转矩阵作用在 basepos 上，所以"倾斜 + 公转"两个角度就够了，
    不用逐块算三角函数。

九层法阵全部粒子绘制（倾斜环用 y = h + r·sinθ·sin(tilt) 参数化）。

时间轴（cam_t 2400→0，1 秒 20 刻）：
    0-15s   2400..2100  紫晶苏醒
    15-30s  2100..1800  晶体环绕
    30-45s  1800..1500  天穹展开
    45-60s  1500..1200  巨晶降临
    60-75s  1200..900   万剑归一
    75-90s  900..600    紫晶天穹
    90-100s 600..400    最终蓄能
    100-106s 400..280   太初终斩
    106-120s 280..0     天穹归寂

用法：
    python build_amethyst.py --dump-spec out/spec.json
    python build_amethyst.py --spec out/spec.json --template t.mcworld --out out/_build.mcworld
"""
import argparse
import json
import math
import os
import sys

# 依赖同目录的 build_cbworld.py —— 用相对路径，项目级 / 用户级都能跑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B

GEM = "@e[scores={fmbe_gem=1..}]"
BOOK = "@a[hasitem={item=enchanted_book,location=slot.weapon.mainhand}]"
CASTER = "@a[scores={cam_cast=1},c=1]"

DUR = 2400
CD = 3000
MIN_BLOCKS = 1800

AMETHYST = "minecraft:amethyst_block"
CLUSTER = "minecraft:amethyst_cluster"
BUD = "minecraft:amethyst_shard"
GLOW = "minecraft:sea_lantern"
ENDROD = "minecraft:end_rod"
PURPUR = "minecraft:purpur_block"

# 五组轨道：(块数, 半径, 高度, 倾角, 每刻转角, 缩放, 方块, 组号)
ORBITS = [
    (2, 4.0,  1.2,  0.0,  0.9,  3.2, AMETHYST, 1),   # 低空环绕
    (2, 6.0,  4.0, 30.0, -0.7,  4.2, AMETHYST, 2),   # 肩部 30°
    (1, 7.5,  8.0, 60.0,  0.55, 5.4, AMETHYST, 3),   # 天穹 60° 反向
    (1, 5.5,  2.6, 90.0, -0.8,  2.8, CLUSTER,  4),   # 垂直阵环
    (1, 13.0,  6.0, 15.0,  0.35, 7.6, AMETHYST, 5),  # 外层巨型
]
BLADES = 12
BLADE_R, BLADE_Y = 5.5, 2.6

GRID = sorted([(dx, dz) for dz in range(-10, 11, 2) for dx in range(-10, 11, 2)
               if not (dx == 0 and dz == 0)], key=lambda p: (p[0] ** 2 + p[1] ** 2, p[1], p[0]))


# ---------------------------------------------------------------- 粒子画笔
def P(x, y, z, particle, t):
    return ('execute as @a[scores={cam_t=%d}] at @s run particle %s ~%.2f ~%.2f ~%.2f'
            % (t, particle, x, y, z))


def flat_ring(r, n, y, particle, t0, t1, phase=0.0, arc=1.0):
    out = []
    for k in range(n):
        th = 2 * math.pi * k / n * arc + math.radians(phase)
        t = t0 - round((t0 - t1) * k / max(1, n - 1))
        out.append(P(r * math.cos(th), y, r * math.sin(th), particle, t))
    return out


def tilt_ring(r, n, h, tilt, particle, t0, t1, phase=0.0):
    """倾斜圆：绕 X 轴倾斜 tilt 度。tilt=90 就是竖直圆。"""
    out = []
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    for k in range(n):
        th = 2 * math.pi * k / n + math.radians(phase)
        x = r * math.cos(th)
        y = h + r * math.sin(th) * st
        z = r * math.sin(th) * ct
        t = t0 - round((t0 - t1) * k / max(1, n - 1))
        out.append(P(x, y, z, particle, t))
    return out


def line(p0, p1, n, particle, t0, t1):
    out = []
    for k in range(n):
        f = k / max(1, n - 1)
        x = p0[0] + (p1[0] - p0[0]) * f
        y = p0[1] + (p1[1] - p0[1]) * f
        z = p0[2] + (p1[2] - p0[2]) * f
        t = t0 - round((t0 - t1) * k / max(1, n - 1))
        out.append(P(x, y, z, particle, t))
    return out


def poly(points, r, y, particle, t0, t1, phase=0.0, per=8):
    out = []
    verts = [(r * math.cos(2 * math.pi * i / points + math.radians(phase)), y,
              r * math.sin(2 * math.pi * i / points + math.radians(phase)))
             for i in range(points)]
    step = max(1, (t0 - t1) // points)
    for i in range(points):
        out += line(verts[i], verts[(i + 1) % points], per, particle,
                    t0 - i * step, t0 - (i + 1) * step)
    return out


# ---------------------------------------------------------------- 九层
def l1_ground():        # 地面基础几何阵：6 环 + 双六芒 + 十二芒
    c = []
    for i, r in enumerate([2.0, 3.0, 4.0, 5.2, 6.6, 8.2]):
        c += flat_ring(r, 44, 0.05, "minecraft:endrod", 2390 - i * 8, 2350 - i * 8, phase=i * 3)
        c += flat_ring(r, 44, 0.08, "minecraft:enchanting_table_particle",
                       2378 - i * 8, 2338 - i * 8, phase=i * 3 + 2)
    c += poly(6, 5.2, 0.06, "minecraft:endrod", 2330, 2290)
    c += poly(6, 5.2, 0.06, "minecraft:endrod", 2325, 2285, phase=30)
    c += poly(12, 7.0, 0.06, "minecraft:totem_particle", 2320, 2270)
    return c


def l2_waist():         # 低空紫晶环（水平）
    c = []
    for i, r in enumerate([3.4, 4.0, 4.6, 5.2]):
        c += flat_ring(r, 36, 1.0 + i * 0.12, "minecraft:enchanting_table_particle",
                       2120 - i * 10, 2080 - i * 10, phase=i * 5)
        c += flat_ring(r, 36, 1.0 + i * 0.12, "minecraft:endrod", 2105 - i * 10, 2065 - i * 10)
    return c


def l3_shoulder():      # 30° 倾斜阵环
    c = []
    for i, r in enumerate([5.0, 6.0, 7.0]):
        c += tilt_ring(r, 40, 4.0 + i * 0.3, 30, "minecraft:enchanting_table_particle",
                       1820 - i * 10, 1770 - i * 10, phase=i * 7)
        c += tilt_ring(r, 40, 4.0 + i * 0.3, 30, "minecraft:endrod",
                       1805 - i * 10, 1755 - i * 10, phase=i * 7 + 5)
    return c


def l4_sky():           # 60° 交错阵环
    c = []
    for i, r in enumerate([6.4, 7.5, 8.6]):
        c += tilt_ring(r, 40, 8.0 + i * 0.4, 60, "minecraft:soul_particle",
                       1520 - i * 10, 1470 - i * 10, phase=i * 9)
        c += tilt_ring(r, 40, 8.0 + i * 0.4, 60, "minecraft:enchanting_table_particle",
                       1505 - i * 10, 1455 - i * 10, phase=i * 9 + 6)
    return c


def l5_vertical():      # 身后垂直剑阵
    c = []
    for i, r in enumerate([5.5, 6.2, 6.9]):
        c += tilt_ring(r, 40, 2.6, 90, "minecraft:endrod", 1510 - i * 12, 1450 - i * 12, phase=i * 12)
        c += tilt_ring(r, 40, 2.6, 90, "minecraft:totem_particle",
                       1495 - i * 12, 1435 - i * 12, phase=i * 12 + 8)
    return c


def l6_outer():         # 外层巨型晶体轨道
    c = []
    for i, r in enumerate([12.0, 13.0, 14.0]):
        c += flat_ring(r, 48, 6.0 + i * 0.5, "minecraft:enchanting_table_particle",
                       1220 - i * 12, 1150 - i * 12, phase=i * 4)
        c += tilt_ring(r, 48, 6.0 + i * 0.5, 15, "minecraft:endrod",
                       1205 - i * 12, 1135 - i * 12, phase=i * 4 + 6)
    return c


def l7_sky_rune():      # 高空倒置符文阵
    c = []
    for i, r in enumerate([5.0, 6.5, 8.0, 9.5]):
        c += flat_ring(r, 40, 15.0 + i * 1.2, "minecraft:endrod", 920 - i * 10, 870 - i * 10, phase=i * 5)
        c += flat_ring(r, 40, 15.0 + i * 1.2, "minecraft:enchanting_table_particle",
                       905 - i * 10, 855 - i * 10, phase=i * 5 + 4)
    c += poly(6, 7.0, 15.0, "minecraft:totem_particle", 860, 820)
    c += poly(12, 9.0, 18.0, "minecraft:totem_particle", 850, 810, phase=15)
    return c


def l8_shell():         # 球形空间边界：8 纬度 + 4 经线
    c = []
    R = 15.0
    for i, y in enumerate([1.0, 3.5, 6.0, 8.5, 11.0, 13.5, 16.0, 18.5]):
        rr = math.sqrt(max(1.0, R * R - (y - 8.0) ** 2))
        c += flat_ring(rr, 40, y, "minecraft:soul_particle", 640 - i * 8, 600 - i * 8, phase=i * 3)
    for k in range(4):
        th = math.radians(k * 45)
        for j in range(10):
            y = 1.0 + j * 1.9
            rr = math.sqrt(max(0.5, R * R - (y - 8.0) ** 2))
            c.append(P(rr * math.cos(th), y, rr * math.sin(th),
                       "minecraft:endrod", 600 - j * 2 - k))
    return c


def l9_core():          # 神剑核心阵
    c = []
    for i, r in enumerate([1.2, 1.8, 2.4]):
        c += flat_ring(r, 32, 2.5, "minecraft:endrod", 410 - i * 8, 370 - i * 8, phase=i * 6)
        c += tilt_ring(r, 32, 2.5, 45 + i * 30, "minecraft:totem_particle",
                       400 - i * 8, 360 - i * 8, phase=i * 6)
        c += tilt_ring(r, 32, 2.5, 135 - i * 30, "minecraft:totem_particle",
                       395 - i * 8, 355 - i * 8, phase=i * 6 + 4)
    return c


def orbit_paths():      # 五条轨道本体：倾斜环，跟着阶段逐条亮起
    c = []
    for i, (n, r, h, tilt, w, sc, item, grp) in enumerate(ORBITS):
        c += tilt_ring(r, 40, h, tilt, "minecraft:enchanting_table_particle",
                       2100 - i * 90, 2060 - i * 90, phase=i * 11)
        c += tilt_ring(r, 40, h, tilt, "minecraft:endrod",
                       2080 - i * 90, 2040 - i * 90, phase=i * 11 + 4)
    return c


def wake():             # 0-15s 苏醒
    c = [P(0, 0.1, 0, "minecraft:enchanting_table_particle", 2390)]
    c += flat_ring(1.5, 16, 0.05, "minecraft:endrod", 2350, 2320, arc=0.8)
    c += line((0, 0.1, 0), (0, 3.0, 0), 12, "minecraft:enchanting_table_particle", 2300, 2260)
    return c


def gather():           # 60-75s 万剑归一
    c = []
    for i in range(BLADES):
        th = 2 * math.pi * i / BLADES
        x, z = BLADE_R * math.cos(th), BLADE_R * math.sin(th)
        c += line((x, BLADE_Y, z), (0, 2.5, -3.0), 8,
                  "minecraft:enchanting_table_particle", 1180 - i * 4, 1120 - i * 4)
    return c


def charge():           # 90-100s 蓄能
    c = []
    for i, r in enumerate([12.0, 10.0, 8.0, 6.0, 4.0]):
        c += flat_ring(r, 24, 2.0 + i * 0.3, "minecraft:totem_particle",
                       600 - i * 14, 560 - i * 14)
    return c


def slash():            # 100-106s 终斩
    c = []
    # 弧形剑气：三段弧
    for seg, (r, y, a0, a1) in enumerate([(4.0, 2.4, -60, 20), (6.5, 2.6, -40, 40),
                                          (9.0, 2.8, -20, 60)]):
        for k in range(14):
            f = k / 13
            th = math.radians(a0 + (a1 - a0) * f)
            c.append(P(r * math.cos(th), y, r * math.sin(th),
                       "minecraft:endrod", 400 - seg * 2 - k // 4))
    # 三维环形冲击波
    for i, r in enumerate([2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0]):
        c += flat_ring(r, 28, 0.3 + i * 0.4, "minecraft:totem_particle",
                       370 - i * 2, 366 - i * 2)
    # 碎片扩散
    for k in range(40):
        th = 2 * math.pi * k / 40
        rr = 3.0 + (k % 8) * 1.2
        c.append(P(rr * math.cos(th), 1.0 + (k % 5) * 0.8, rr * math.sin(th),
                   "minecraft:enchanting_table_particle", 364 - (k % 6)))
    return c


def settle():           # 106-120s 归寂
    c = []
    c += flat_ring(9.0, 32, 0.1, "minecraft:soul_particle", 260, 200)
    c += tilt_ring(7.5, 28, 8.0, 60, "minecraft:soul_particle", 240, 180)
    c += flat_ring(4.0, 24, 1.2, "minecraft:enchanting_table_particle", 200, 140)
    return c


# ---------------------------------------------------------------- 实体
def actors():
    """1 神剑 + 12 能量剑 + 52 紫水晶 = 65。"""
    out, i = [], 0
    # 神剑：玩家正前方 3 格
    sx, sz = GRID[i]
    out.append(dict(sx=sx, sz=sz, item="minecraft:netherite_sword", orb=0,
                    bx=0, by=40, bz=-48, xrot=0.0, yrot=0.0, scale=3.0))
    i += 1
    # 12 能量剑：垂直阵环，指向中心
    for k in range(BLADES):
        sx, sz = GRID[i]
        th = 360.0 * k / BLADES
        out.append(dict(sx=sx, sz=sz, item="minecraft:iron_sword", orb=6,
                        bx=0, by=BLADE_Y * 16, bz=-BLADE_R * 16,
                        xrot=90.0, yrot=th, scale=1.0))
        i += 1
    # 52 紫水晶
    for n, r, h, tilt, w, sc, item, grp in ORBITS:
        for k in range(n):
            sx, sz = GRID[i]
            out.append(dict(sx=sx, sz=sz, item=item, orb=grp,
                            bx=0, by=h * 16, bz=-r * 16,
                            xrot=tilt, yrot=360.0 * k / n, scale=sc))
            i += 1
    return out


ACTORS = actors()
N = len(ACTORS)


def at_a(a, cmd):
    return ("execute at %s positioned ~%d ~%d ~%d run %s"
            % (CASTER, a["sx"], a["sz"] and a["sz"] or 0, 0, cmd))


def at_actor(a, cmd):
    return ("execute at %s positioned ~%d ~ ~%d run %s"
            % (CASTER, a["sx"], a["sz"], cmd))


def init_cmds(ta):
    return [
        "gamerule sendcommandfeedback false",
        "gamerule commandblockoutput false",
        "gamerule showdeathmessages false",
        "gamerule announceadvancements false",
        "gamerule showrecipemessages false",
        "gamerule showcoordinates false",
        'scoreboard objectives add cam_t dummy "天穹计时"',
        'scoreboard objectives add cam_cast dummy "天穹触发"',
        'scoreboard objectives add cam_cd dummy "天穹冷却"',
        'scoreboard objectives add fmbe_gem dummy "紫晶展示体"',
        'scoreboard objectives add fmbe_orb dummy "紫晶轨道组"',
        "tickingarea remove amethyst",
        ta,
        'tellraw @a {"rawtext":[{"text":"§d太初 · 紫晶天穹 §8· §f手持附魔书开启，§7时长 120 秒 / 冷却 150 秒"}]}',
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
        "tp @e[scores={fmbe_gem=0}] ~ -400 ~",
    ]
    for i, a in enumerate(ACTORS, start=1):
        c.append("execute at %s run summon fox ~%d ~ ~%d" % (CASTER, a["sx"], a["sz"]))
        c.append(at_actor(a, "tp @e[type=fox,r=2,c=1] ~ ~ ~ ~ ~"))
        c.append(at_actor(a, "replaceitem entity @e[type=fox,r=2,c=1] "
                             "slot.weapon.mainhand 0 %s" % a["item"]))
        c.append(at_actor(a, "scoreboard players set @e[type=fox,r=2,c=1] fmbe_gem %d" % i))
        c.append(at_actor(a, "scoreboard players set @e[type=fox,r=2,c=1] fmbe_orb %d" % a["orb"]))
        c.append(at_actor(a, 'playanimation @e[type=fox,r=2,c=1] '
                             'animation.player.attack.positions none 0 '
                             '"v.xbasepos=%g;v.ybasepos=%g;v.zbasepos=%g;'
                             'v.xrot=%g;v.yrot=%g;v.scale=0.02;v.zrot=0;" fmbe.init'
                             % (a["bx"], a["by"], a["bz"], a["xrot"], a["yrot"])))
    c += [
        "effect %s invisibility 999999 1 true" % GEM,
        "effect %s resistance 999999 255 true" % GEM,
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.aggro",
        "stopsound @a mob.fox.bite",
        "stopsound @a mob.fox.eat",
        "playsound ambient.cave @a[r=48] ~ ~ ~ 1 0.5",
        "playsound random.fizz @a[r=48] ~ ~ ~ 0.5 0.6",
        "playsound beacon.activate @a[r=48] ~ ~ ~ 0.8 0.7",
        'execute as @a[scores={cam_t=0..}] run titleraw @s title '
        '{"rawtext":[{"text":"§d§l紫 晶 天 穹"}]}',
        'execute as @a[scores={cam_t=0..}] run titleraw @s subtitle '
        '{"rawtext":[{"text":"§7太初 · 晶体归位"}]}',
        "scoreboard players set @a cam_cast 0",
    ]
    return c


def render_cmds():
    return [
        'playanimation %s animation.player.sleeping none 0 "" '
        'controller.animation.fox.move' % GEM,
        'playanimation %s animation.creeper.swelling none 0 '
        '"v.xbasepos=v.xbasepos??0;v.ybasepos=v.ybasepos??0;v.zbasepos=v.zbasepos??0;'
        'v.xpos=v.xpos??0;v.ypos=v.ypos??0;v.zpos=v.zpos??0;'
        'v.xrot=v.xrot??0;v.yrot=v.yrot??0;v.zrot=v.zrot??0;'
        'v.scale=v.scale??1;v.xzscale=v.xzscale??1;v.yscale=v.yscale??1;'
        'v.swelling_scale1=2.1385*math.sqrt(v.xzscale*v.scale);'
        'v.swelling_scale2=2.1385*math.sqrt(v.yscale*v.scale);" fmbe.scale' % GEM,
        'playanimation %s animation.ender_dragon.neck_head_movement none 0 '
        '"v.head_rotation_x=0;v.head_rotation_y=0;v.head_rotation_z=0;'
        'v.head_position_x=(v.xbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);'
        'v.head_position_y=(10.05185375+v.ybasepos*0.467625)*math.sqrt(v.yscale*v.scale);'
        'v.head_position_z=(17.108-v.zbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);" '
        'fmbe.shift_pos' % GEM,
        'playanimation %s animation.warden.move none 0 '
        '"v.body_x_rot=90+v.xrot;v.body_z_rot=90+v.yrot;" fmbe.xrot' % GEM,
        'playanimation %s animation.player.attack.rotations none 0 '
        '"v.attack_body_rot_y=-v.zrot;" fmbe.zrot' % GEM,
        'playanimation %s animation.parrot.moving none 0 '
        '"v.wing_flap=(16-v.xpos)*3.3333333;" fmbe.xpos' % GEM,
        'playanimation %s animation.minecart.move.v1.0 none 0 '
        '"v.rail_offset.x=0;v.rail_offset.y=1.6485+v.ypos/16;v.rail_offset.z=0;" '
        'fmbe.ypos' % GEM,
        'playanimation %s animation.parrot.dance none 0 '
        '"v.dance.x=-v.zpos;v.dance.y=0;" fmbe.zpos' % GEM,
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.bite",
    ]


# ---------------------------------------------------------------- 轨道与阶段
SPIN = [
    ("s1", "execute if entity @a[scores={cam_t=2100..2400}]",
     'playanimation @e[scores={fmbe_orb=1}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.35;v.scale=1.4*(1-math.exp(-(q.life_time-5)*1.2));" fmbe.s1'),
    ("s2", "execute if entity @a[scores={cam_t=1500..2100}]",
     'playanimation @e[scores={fmbe_orb=1}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.9;v.scale=1.4;" fmbe.s1'),
    ("s3", "execute if entity @a[scores={cam_t=900..1500}]",
     'playanimation @e[scores={fmbe_orb=1}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+1.4;v.scale=1.4+0.15*math.sin(q.life_time*90);" fmbe.s1'),
    ("s4", "execute if entity @a[scores={cam_t=400..900}]",
     'playanimation @e[scores={fmbe_orb=1}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+2.2;v.scale=1.4;" fmbe.s1'),
    ("s5", "execute if entity @a[scores={cam_t=1..400}]",
     'playanimation @e[scores={fmbe_orb=1}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.5;v.scale=1.4;" fmbe.s1'),
]
SPIN_B = [
    ("b1", "execute if entity @a[scores={cam_t=2100..2400}]",
     'playanimation @e[scores={fmbe_orb=2}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-0.25;v.scale=2.4*(1-math.exp(-(q.life_time-10)*1.0));" fmbe.s2'),
    ("b2", "execute if entity @a[scores={cam_t=1500..2100}]",
     'playanimation @e[scores={fmbe_orb=2}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-0.7;v.scale=2.4;" fmbe.s2'),
    ("b3", "execute if entity @a[scores={cam_t=900..1500}]",
     'playanimation @e[scores={fmbe_orb=2}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-1.1;v.scale=2.4;" fmbe.s2'),
    ("b4", "execute if entity @a[scores={cam_t=400..900}]",
     'playanimation @e[scores={fmbe_orb=2}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-1.8;v.scale=2.4;" fmbe.s2'),
    ("b5", "execute if entity @a[scores={cam_t=1..400}]",
     'playanimation @e[scores={fmbe_orb=2}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-0.4;v.scale=2.4;" fmbe.s2'),
]
SPIN_C = [
    ("c1", "execute if entity @a[scores={cam_t=1500..1800}]",
     'playanimation @e[scores={fmbe_orb=3}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.3;v.scale=2.8*(1-math.exp(-(q.life_time-30)*1.2));" fmbe.s3'),
    ("c2", "execute if entity @a[scores={cam_t=900..1500}]",
     'playanimation @e[scores={fmbe_orb=3}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.55;v.scale=2.8;" fmbe.s3'),
    ("c3", "execute if entity @a[scores={cam_t=400..900}]",
     'playanimation @e[scores={fmbe_orb=3}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.9;v.scale=2.8;" fmbe.s3'),
    ("c4", "execute if entity @a[scores={cam_t=1..400}]",
     'playanimation @e[scores={fmbe_orb=3}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.3;v.scale=2.8;" fmbe.s3'),
]
SPIN_D = [
    ("d1", "execute if entity @a[scores={cam_t=1500..1800}]",
     'playanimation @e[scores={fmbe_orb=4}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-0.2;v.scale=1.1*(1-math.exp(-(q.life_time-32)*1.2));" fmbe.s4'),
    ("d2", "execute if entity @a[scores={cam_t=900..1500}]",
     'playanimation @e[scores={fmbe_orb=4}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-0.8;v.scale=1.1;" fmbe.s4'),
    ("d3", "execute if entity @a[scores={cam_t=400..900}]",
     'playanimation @e[scores={fmbe_orb=4}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-1.3;v.scale=1.1;" fmbe.s4'),
    ("d4", "execute if entity @a[scores={cam_t=1..400}]",
     'playanimation @e[scores={fmbe_orb=4}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot-0.3;v.scale=1.1;" fmbe.s4'),
]
SPIN_E = [
    ("e1", "execute if entity @a[scores={cam_t=1200..1500}]",
     'playanimation @e[scores={fmbe_orb=5}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.2;v.scale=4.6*(1-math.exp(-(q.life_time-45)*0.9));" fmbe.s5'),
    ("e2", "execute if entity @a[scores={cam_t=900..1200}]",
     'playanimation @e[scores={fmbe_orb=5}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.35;v.scale=4.6;" fmbe.s5'),
    ("e3", "execute if entity @a[scores={cam_t=400..900}]",
     'playanimation @e[scores={fmbe_orb=5}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.55;v.scale=4.6;" fmbe.s5'),
    ("e4", "execute if entity @a[scores={cam_t=1..400}]",
     'playanimation @e[scores={fmbe_orb=5}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.18;v.scale=4.6;" fmbe.s5'),
]
# 十二把剑：垂直环上，中期转向中心，终斩前消散
BLADE = [
    ("k1", "execute if entity @a[scores={cam_t=1500..1800}]",
     'playanimation @e[scores={fmbe_orb=6}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.15;v.scale=1*(1-math.exp(-(q.life_time-32)*1.5));" fmbe.s6'),
    ("k2", "execute if entity @a[scores={cam_t=900..1500}]",
     'playanimation @e[scores={fmbe_orb=6}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.5;v.scale=1;" fmbe.s6'),
    ("k3", "execute if entity @a[scores={cam_t=600..900}]",
     'playanimation @e[scores={fmbe_orb=6}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+0.8;v.zbasepos=-88+30*math.min(1,math.max(0,q.life_time-60)*0.3);v.scale=1;" fmbe.s6'),
    ("k4", "execute if entity @a[scores={cam_t=400..600}]",
     'playanimation @e[scores={fmbe_orb=6}] animation.player.attack.positions none 0 '
     '"v.yrot=v.yrot+1.2;v.zbasepos=-88+60*math.min(1,math.max(0,q.life_time-75)*0.6);v.scale=1-0.7*math.min(1,math.max(0,q.life_time-95)*0.5);" fmbe.s6'),
    ("k5", "execute if entity @a[scores={cam_t=1..400}]",
     'playanimation @e[scores={fmbe_orb=6}] animation.player.attack.positions none 0 '
     '"v.scale=0.02;" fmbe.s6'),
]
# 神剑：0.02 → 3.0，终斩时前刺
SWORD = [
    ("w1", "execute if entity @a[scores={cam_t=2100..2400}]",
     'playanimation @e[scores={fmbe_orb=0}] animation.player.attack.positions none 0 '
     '"v.zbasepos=-48;v.scale=0.02;" fmbe.s0'),
    ("w2", "execute if entity @a[scores={cam_t=1500..2100}]",
     'playanimation @e[scores={fmbe_orb=0}] animation.player.attack.positions none 0 '
     '"v.zbasepos=-48;v.scale=3*(1-math.exp(-(q.life_time-15)*1.5));v.yrot=q.life_time*20;" fmbe.s0'),
    ("w3", "execute if entity @a[scores={fmbe_orb=0}] and @a[scores={cam_t=400..1500}]",
     'playanimation @e[scores={fmbe_orb=0}] animation.player.attack.positions none 0 '
     '"v.zbasepos=-48;v.scale=3;v.yrot=q.life_time*20;" fmbe.s0'),
    ("w4", "execute if entity @a[scores={cam_t=280..400}]",
     'playanimation @e[scores={fmbe_orb=0}] animation.player.attack.positions none 0 '
     '"v.zbasepos=-48;v.scale=3+0.8*math.sin((400-q.life_time*20)*0.3);v.yrot=q.life_time*60;" fmbe.s0'),
    ("w5", "execute if entity @a[scores={cam_t=1..280}]",
     'playanimation @e[scores={fmbe_orb=0}] animation.player.attack.positions none 0 '
     '"v.zbasepos=-48;v.scale=3;v.yrot=q.life_time*20;" fmbe.s0'),
]


# ---------------------------------------------------------------- 运镜
def clock_cmds():
    shots = [
        (2395, "^ ^1.0 ^-10.0", "out_cubic", 5.0),      # 低角度推进
        (2250, "^ ^3.0 ^-14.0", "in_out_sine", 4.0),
        (2100, "^8 ^4 ^-12", "in_out_sine", 4.0),        # 侧面环绕
        (1950, "^-8 ^4 ^-12", "in_out_sine", 4.0),
        (1800, "^ ^6 ^-16", "in_out_sine", 4.0),         # 背后绕至侧面
        (1650, "^10 ^6 ^-14", "in_out_sine", 4.0),
        (1500, "^ ^4 ^-18", "in_out_sine", 4.0),         # 仰拍巨晶
        (1350, "^ ^2 ^-22", "in_out_sine", 4.0),
        (1200, "^ ^10 ^-20", "in_out_sine", 4.0),        # 环绕
        (1050, "^14 ^8 ^-18", "in_out_sine", 4.0),
        (900,  "^ ^20 ^-16", "in_out_sine", 4.0),        # 快速升高
        (750,  "^ ^26 ^-14", "in_out_sine", 4.0),
        (600,  "^ ^8 ^-16", "in_out_sine", 3.0),         # 推进神剑
        (450,  "^ ^3 ^-8", "in_out_sine", 2.5),
        (400,  "^ ^3 ^-8", "out_quad", 0.3),             # 锁定
        (360,  "^6 ^4 ^-12", "out_quad", 0.6),           # 跟随斩击
        (300,  "^ ^8 ^-18", "in_out_sine", 2.0),
        (240,  "^ ^14 ^-24", "in_out_sine", 3.0),        # 拉远升高
        (120,  "^ ^20 ^-30", "in_out_sine", 4.0),
        (20,   "^ ^24 ^-34", "out_quad", 3.0),
    ]
    c = ["execute as @a[scores={cam_t=1..}] run scoreboard players remove @s cam_t 1"]
    for t, pos, ease, dur in shots:
        c.append('execute as @a[scores={cam_t=%d}] at @s run camera @s set minecraft:free '
                 'ease %s %s pos %s facing ~ ~3.0 ~' % (t, dur, ease, pos))
    c += [
        "execute as @a[scores={cam_t=2395}] run camera @s fov_set 58 1.5 out_quad",
        "execute as @a[scores={cam_t=2100}] run camera @s fov_set 72 2.5 in_out_sine",
        "execute as @a[scores={cam_t=1500}] run camera @s fov_set 88 3.0 in_out_sine",
        "execute as @a[scores={cam_t=900}] run camera @s fov_set 95 3.0 in_out_sine",
        "execute as @a[scores={cam_t=400}] run camera @s fov_set 60 1.0 in_out_sine",
        "execute as @a[scores={cam_t=360}] run camera @s fov_set 105 0.3 out_quad",
        "execute as @a[scores={cam_t=240}] run camera @s fov_set 78 2.0 in_out_sine",
        "execute as @a[scores={cam_t=20}] run camera @s fov_set 70 3.0 in_out_sine",
        "execute as @a[scores={cam_t=1500}] run camerashake add @s 0.25 0.6 positional",
        "execute as @a[scores={cam_t=1200}] run camerashake add @s 0.3 0.6 positional",
        "execute as @a[scores={cam_t=900}] run camerashake add @s 0.4 0.7 positional",
        "execute as @a[scores={cam_t=360}] run camerashake add @s 1.4 1.0 positional",
    ]
    # 音效：(剩余刻, 音效, 音量, 音高)
    cues = [
        (2390, "ambient.cave", 1.0, 0.5), (2380, "random.fizz", 0.4, 0.5),
        (2320, "ambient.cave", 0.8, 0.55), (2260, "note.chime", 0.7, 0.8),
        (2200, "conduit.activate", 0.6, 0.7), (2160, "beacon.activate", 0.7, 0.6),
        (2100, "note.pling", 0.8, 0.9), (2080, "note.pling", 0.8, 1.0),
        (2040, "bell.ring", 0.7, 0.8), (1980, "conduit.activate", 0.7, 0.9),
        (1920, "note.chime", 0.8, 1.0), (1860, "note.flute", 0.7, 0.9),
        (1800, "beacon.power", 0.8, 0.9), (1798, "note.bell", 0.9, 0.9),
        (1740, "note.chime", 0.8, 1.1), (1680, "conduit.activate", 0.7, 1.0),
        (1620, "note.pling", 0.9, 1.1), (1560, "mob.irongolem.hit", 0.7, 1.2),
        (1500, "item.trident.thunder", 0.9, 0.9),
        (1498, "beacon.activate", 0.9, 0.8), (1440, "note.chime", 0.8, 1.2),
        (1380, "ambient.cave", 0.8, 0.5), (1320, "note.bell", 0.9, 1.0),
        (1260, "conduit.activate", 0.8, 1.1), (1200, "raid.horn", 0.8, 0.9),
        (1198, "beacon.power", 0.8, 1.0), (1140, "note.pling", 0.9, 1.2),
        (1080, "note.chime", 0.8, 1.3), (1020, "mob.irongolem.hit", 0.8, 1.3),
        (960,  "conduit.activate", 0.8, 1.2), (900, "beacon.activate", 1.0, 0.9),
        (898,  "ambient.weather.thunder", 0.8, 0.8),
        (840,  "note.bell", 0.9, 1.1), (780, "note.chime", 0.8, 1.4),
        (720,  "conduit.activate", 0.8, 1.3), (660, "note.pling", 0.9, 1.4),
        (620,  "mob.enderdragon.growl", 0.8, 0.6), (600, "beacon.power", 0.9, 1.0),
        (560,  "note.bell", 0.9, 1.2), (520, "conduit.activate", 0.8, 1.4),
        (480,  "note.pling", 0.9, 1.5), (440, "note.chime", 0.9, 1.5),
        (410,  "ambient.cave", 0.5, 0.4), (405, "note.bell", 0.6, 1.4),
        (400,  "item.trident.thunder", 1.0, 0.8),
        (398,  "mob.wither.shoot", 0.9, 0.7), (396, "raid.horn", 1.0, 1.0),
        (360,  "random.explode", 1.0, 0.6), (358, "totem.use", 1.0, 0.9),
        (356,  "mob.enderdragon.growl", 1.0, 0.7), (354, "ambient.weather.thunder", 0.9, 0.9),
        (330,  "note.bell", 1.0, 1.3), (300, "conduit.activate", 0.9, 1.4),
        (270,  "note.pling", 0.9, 1.4), (240, "ambient.cave", 0.8, 0.5),
        (200,  "note.harp", 0.8, 0.9), (160, "note.harp", 0.8, 1.1),
        (120,  "bell.ring", 0.8, 1.0), (80, "note.flute", 0.7, 0.8),
        (40,   "ambient.cave", 0.6, 0.6),
        # —— 加密层：补足晶体共鸣与轨道运转的连续感 ——
        (2370, "note.bass", 0.5, 0.5), (2350, "ambient.cave", 0.7, 0.6),
        (2330, "random.fizz", 0.4, 0.7), (2310, "note.bass", 0.5, 0.6),
        (2280, "bell.ring", 0.5, 0.6), (2240, "note.chime", 0.6, 0.7),
        (2220, "ambient.cave", 0.7, 0.55), (2180, "note.bass", 0.5, 0.7),
        (2140, "random.fizz", 0.5, 0.8), (2120, "note.pling", 0.7, 0.8),
        (2060, "note.chime", 0.7, 0.9), (2020, "bell.ring", 0.6, 0.9),
        (1960, "note.bass", 0.6, 0.8), (1900, "note.pling", 0.7, 1.0),
        (1880, "conduit.activate", 0.6, 1.0), (1840, "note.chime", 0.7, 1.0),
        (1760, "note.bass", 0.6, 0.9), (1720, "bell.ring", 0.6, 1.0),
        (1700, "note.pling", 0.7, 1.1), (1640, "note.chime", 0.7, 1.1),
        (1600, "conduit.activate", 0.6, 1.1), (1540, "note.bass", 0.6, 1.0),
        (1460, "note.pling", 0.7, 1.2), (1420, "bell.ring", 0.6, 1.1),
        (1360, "note.chime", 0.7, 1.2), (1300, "note.bass", 0.6, 1.1),
        (1240, "note.pling", 0.7, 1.3), (1160, "bell.ring", 0.6, 1.2),
        (1120, "note.chime", 0.7, 1.3), (1060, "conduit.activate", 0.6, 1.2),
        (1000, "note.bass", 0.6, 1.2), (960,  "note.pling", 0.7, 1.3),
        (880,  "bell.ring", 0.6, 1.3), (840,  "note.chime", 0.7, 1.4),
        (780,  "note.bass", 0.6, 1.3), (700,  "note.pling", 0.7, 1.4),
        (640,  "conduit.activate", 0.6, 1.3), (580,  "bell.ring", 0.6, 1.4),
        (540,  "note.chime", 0.7, 1.5), (500,  "note.bass", 0.6, 1.4),
        (460,  "note.pling", 0.7, 1.5), (420,  "note.chime", 0.7, 1.6),
        (380,  "bell.ring", 0.6, 1.5), (340,  "note.bass", 0.6, 1.5),
        (280,  "note.pling", 0.7, 1.5), (220,  "note.chime", 0.7, 1.4),
        (180,  "bell.ring", 0.6, 1.3), (140,  "note.bass", 0.6, 1.2),
        (100,  "note.pling", 0.6, 1.1), (60,   "note.chime", 0.6, 1.0),
    ]
    for t, snd, vol, pit in cues:
        c.append('execute as @a[scores={cam_t=%d}] at @s run playsound %s @a[r=48] ~ ~ ~ %s %s'
                 % (t, snd, vol, pit))
    c += [
        "execute as @a[scores={cam_t=0}] run camera @s clear",
        "execute as @a[scores={cam_t=0}] run camera @s fov_clear 2.0 out_elastic",
        "execute as @a[scores={cam_t=0}] run inputpermission set @s movement enabled",
        "execute as @a[scores={cam_t=0}] run scoreboard players set @e[scores={fmbe_gem=1..}] fmbe_gem 0",
        "execute as @a[scores={cam_t=0}] run tp @e[scores={fmbe_gem=0}] ~ -400 ~",
        "execute as @a[scores={cam_t=0}] run scoreboard players set @s cam_t -1",
        'execute as @a[scores={cam_t=-1}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§7紫晶归寂"}]}',
    ]
    return c


def cooldown_cmds():
    return [
        "execute as @a[scores={cam_cd=1..}] run scoreboard players remove @s cam_cd 1",
        'execute as @a[scores={cam_cd=1..}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§8紫晶天穹 §7冷却 §f"},'
        '{"score":{"name":"@s","objective":"cam_cd"}}]}',
    ]


def abort_cmds():
    return [
        "camera @a clear",
        "camera @a fov_clear",
        "inputpermission set @a movement enabled",
        "scoreboard players set @e[scores={fmbe_gem=1..}] fmbe_gem 0",
        "tp @e[scores={fmbe_gem=0}] ~ -400 ~",
        "scoreboard players set @a cam_t -1",
        "scoreboard players set @a cam_cast 0",
        'execute as @a[scores={cam_t=-1}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§c已中断"}]}',
    ]


def spec(ta="tickingarea add circle ~ ~ ~ 4 amethyst"):
    fx = [
        ("苏醒", "execute if entity @a[scores={cam_t=2260..2400}]", wake()),
        ("一层·地面", "execute if entity @a[scores={cam_t=2270..2380}]", l1_ground()),
        ("二层·腰环", "execute if entity @a[scores={cam_t=2040..2100}]", l2_waist()),
        ("三层·肩环", "execute if entity @a[scores={cam_t=1730..1800}]", l3_shoulder()),
        ("四层·天穹", "execute if entity @a[scores={cam_t=1430..1500}]", l4_sky()),
        ("五层·剑阵", "execute if entity @a[scores={cam_t=1410..1500}]", l5_vertical()),
        ("六层·外环", "execute if entity @a[scores={cam_t=1110..1200}]", l6_outer()),
        ("七层·符文", "execute if entity @a[scores={cam_t=810..900}]", l7_sky_rune()),
        ("八层·边界", "execute if entity @a[scores={cam_t=530..620}]", l8_shell()),
        ("九层·核心", "execute if entity @a[scores={cam_t=340..400}]", l9_core()),
        ("轨道", "execute if entity @a[scores={cam_t=1950..2100}]", orbit_paths()),
        ("归一", "execute if entity @a[scores={cam_t=1120..1180}]", gather()),
        ("蓄能", "execute if entity @a[scores={cam_t=460..600}]", charge()),
        ("终斩", "execute if entity @a[scores={cam_t=346..400}]", slash()),
        ("归寂", "execute if entity @a[scores={cam_t=140..260}]", settle()),
    ]
    fx_chains = []
    for label, gate, cmds in fx:
        parts = [cmds[i:i + 80] for i in range(0, len(cmds), 80)] or [[]]
        for j, part in enumerate(parts):
            fx_chains.append({"id": "fx%d" % len(fx_chains), "kind": "gated",
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
         "gate": "execute if entity %s" % GEM, "cmds": render_cmds()},
        # 锁位独立成链：每刻把全部狐狸 tp 回施法者位置+朝向，断开渲染也照锁
        {"id": "lock", "kind": "gated", "label": "锁位",
         "gate": "execute if entity %s" % GEM,
         "cmds": ["execute at %s positioned ~%d ~ ~%d run tp @e[scores={fmbe_gem=%d}] ~ ~ ~ ~ ~"
                  % (CASTER, a["sx"], a["sz"], i)
                  for i, a in enumerate(ACTORS, start=1)]
                 + ["execute as %s run effect @s resistance 999999 255 true" % GEM,
                    "stopsound @a mob.fox.ambient",
                    "stopsound @a mob.fox.bite"]},
    ] + [
        {"id": i, "kind": "gated", "label": "轨·" + i[0].upper(), "gate": g, "cmds": [c]}
        for i, g, c in SPIN + SPIN_B + SPIN_C + SPIN_D + SPIN_E + BLADE + SWORD
    ] + fx_chains + [
        {"id": "clock", "kind": "gated", "label": "运镜",
         "gate": "execute if entity @a[scores={cam_t=0..}]", "cmds": clock_cmds()},
        {"id": "cool", "kind": "gated", "label": "冷却",
         "gate": "execute if entity @a[scores={cam_cd=1..}]", "cmds": cooldown_cmds()},
        {"id": "abort", "kind": "impulse", "button": True, "label": "中断",
         "cmds": abort_cmds()},
    ]
    return {
        "meta": {"name": "紫晶天穹", "spawn": [8, -58, 7], "gametype": "creative"},
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
        {"kind": "sign", "front": ["§l§d太初 · 紫晶天穹", "§7主手持附魔书开启",
                                   "§8时长 120 秒", "§8冷却 150 秒"]},
        {"kind": "sign", "front": ["§l§5五组轨道", "§71 腰环 · 2 肩环30°",
                                   "§73 天穹60° · 4 垂直阵", "§75 外层巨型"]},
        {"kind": "sign", "front": ["§l§b九层法阵", "§7地面→腰→肩→天穹",
                                   "§7剑阵→外环→符文", "§7边界→核心"]},
        {"kind": "chest", "name": "紫晶", "items": [
            B.item_nbt("enchanted_book", display_name="§d太初 · 紫晶天穹",
                       lore=["§7主手持此典 → 展开天穹", "§8时长 120 秒 / 冷却 150 秒"]),
            B.item_nbt("amethyst_block", display_name="§d紫水晶块",
                       lore=["§7巨型晶体 ×7"]),
            B.item_nbt("amethyst_cluster", display_name="§5紫水晶簇",
                       lore=["§7垂直阵环 ×1"]),
            B.item_nbt("netherite_sword", display_name="§f太初神剑", lore=["§7核心"]),
        ]},
    ]
    return {"chains": chains, "props": props, "props_pedestal": True}


def measure_ta(s):
    blocks, _, _ = B.build_scene(to_system(s))
    xs = [x for (x, y, z) in blocks]
    zs = [z for (x, y, z) in blocks]
    return ("tickingarea add ~%d ~-4 ~%d ~%d ~4 ~%d amethyst"
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
    B.CHAIN_SUMMARY["trigger"] = "持书 + 冷却就绪 → 置天穹触发位"
    B.CHAIN_SUMMARY["clock"] = "2400 刻倒计时 + 20 段运镜 + FOV + 收尾"
    info = B.build(a.template, a.out, m["name"], m.get("spawn"), 1, to_system(s))
    print("[完成] %s" % info["out"])
    print("        区块 %d / 命令方块 %d / 按钮 %d / 说明区 %d / 展示体 %d"
          % (info["chunks"], info["blocks"], info["buttons"], info["props"], N))
    if info["blocks"] < MIN_BLOCKS:
        raise SystemExit("命令方块 %d < 硬指标 %d" % (info["blocks"], MIN_BLOCKS))


if __name__ == "__main__":
    main()
