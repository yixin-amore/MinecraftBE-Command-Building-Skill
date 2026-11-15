#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""屏障咒典 · 千格版（85 格展示体 + 五阶段 + 八段运镜）。

触发：主手持附魔书 → 穹顶展开 → 运镜 → 碎裂 → 消散 → 冷却 500 刻。
清理**不用 kill**：先摘掉标记分，再把狐狸 tp 到 y-400 的虚空，让引擎自己回收。

阶段（cam_t 从 200 倒数）：
    expand  200..180  从脚下炸开
    hold    179..80   整座公转 + 轻微呼吸
    pulse    79..40   层间错相脉动
    shatter  39..15   向外飞散 + 缩小
    fade     14..1    继续上飘 + 缩到 0

用法：
    python build_shield_cam.py --dump-spec out/spec.json
    python build_shield_cam.py --spec out/spec.json --template t.mcworld --out out/_build.mcworld
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

DUR = 200          # 演出总时长（刻）= 10 秒
CD = 500           # 冷却（刻）= 25 秒
MIN_BLOCKS = 1000  # 交付硬指标

# 生成点：间距 2 的 11x11 网格（去掉中心），按离玩家距离取最近的一批
GRID = sorted([(dx, dz) for dz in range(-10, 11, 2) for dx in range(-10, 11, 2)
               if not (dx == 0 and dz == 0)], key=lambda p: (p[0] ** 2 + p[1] ** 2, p[1], p[0]))

# 穹顶：(个数, 半径, 高度, 起始角, 方块, 组)
DOME = [
    (12, 3.6, 0.1, 0.0,  "minecraft:light_blue_stained_glass", 1),
    (12, 3.4, 0.9, 15.0, "minecraft:light_blue_stained_glass", 1),
    (12, 3.0, 1.8, 0.0,  "minecraft:purple_stained_glass", 1),
    (12, 2.3, 2.6, 15.0, "minecraft:purple_stained_glass", 1),
    (8,  1.4, 3.2, 0.0,  "minecraft:sea_lantern", 1),
    (4,  0.6, 3.6, 45.0, "minecraft:sea_lantern", 1),
]
# 地面法阵：(个数, 半径, 高度, 起始角, 方块, 组)
ARRAY = [
    (16, 6.0, 0.15, 0.0,  "minecraft:end_rod", 2),
    (8,  5.0, 0.15, 22.5, "minecraft:end_rod", 2),
]
CORE_ITEM = "minecraft:beacon"
CORE_Y = 4.0
CORE_SPAWN_Y = 8


def _term(coef, off):
    """拼 `v.R*(coef)±off`。

    ❗ 系数为 0 时不能留 `+96`（Molang 表达式不能以 `+` 开头）；
       系数为负时必须加括号，`v.R*-14.78` 在部分版本会解析失败。
    """
    parts = []
    if abs(coef) > 1e-6:
        parts.append("v.R*(%g)" % round(coef, 2))
    if abs(off) > 1e-6:
        parts.append(("+" if off > 0 else "-") + ("%g" % round(abs(off), 2)))
    if not parts:
        return "0"
    if len(parts) == 1 and parts[0][0] in "+-":
        return parts[0].lstrip("+")
    return parts[0] + "".join(parts[1:])


def cubes():
    """返回 [dict]，每个是一个展示格。"""
    out, i = [], 0
    for n, r, y, off, item, grp in DOME + ARRAY:
        for k in range(n):
            sx, sz = GRID[i]
            th = math.radians(off + k * 360.0 / n)
            out.append(dict(
                sx=sx, sy=0, sz=sz, item=item, r0=r, y16=y * 16, grp=grp,
                cx=16 * math.cos(th), cz=16 * math.sin(th),
                ox=-sx * 16, oz=-sz * 16,
                ph=round(off + k * 360.0 / n, 1),       # 脉动相位
            ))
            i += 1
    out.append(dict(sx=0, sy=CORE_SPAWN_Y, sz=0, item=CORE_ITEM, r0=0,
                    y16=(CORE_Y - CORE_SPAWN_Y) * 16, grp=3,
                    cx=0, cz=0, ox=0, oz=0, ph=0))
    return out


CUBES = cubes()
N = len(CUBES)
DOME_CUBES = [c for c in CUBES if c["grp"] == 1]


def _pos(c):
    """basepos 三件套：x = v.R*coef + 生成点偏移。"""
    return ("v.xbasepos=%s;v.zbasepos=%s;v.ybasepos=%g;"
            % (_term(c["cx"], c["ox"]), _term(c["cz"], c["oz"]), c["y16"]))


def phase_body(name):
    """返回该阶段每格一条的 Molang 主体。"""
    out = []
    for c in CUBES:
        r0, ph = c["r0"], c["ph"]
        if name == "expand":
            r = "%g*(1-math.exp(-q.life_time*5))" % r0
            tail = "v.scale=0.2+0.8*(1-math.exp(-q.life_time*5));"
        elif name == "hold":
            r = "%g*(1+0.04*math.sin(q.life_time*120+%g))" % (r0, ph)
            tail = "v.scale=1;"
        elif name == "pulse":
            r = "%g*(1+0.11*math.sin(q.life_time*220+%g))" % (r0, ph)
            tail = "v.scale=1+0.10*math.sin(q.life_time*220+%g);" % ph
        elif name == "collapse":
            r = ("%g*(1-0.35*math.min(1,math.max(0,q.life_time-6.55)*2))" % r0)
            tail = ("v.scale=1+0.18*math.min(1,math.max(0,q.life_time-6.55)*2);"
                    "v.ypos=math.max(0,q.life_time-6.55)*6;")
        elif name == "shatter":
            r = "%g*(0.65+math.max(0,q.life_time-7.8)*1.1)" % r0
            tail = "v.scale=math.max(0.1,1.18-math.max(0,q.life_time-7.8)*0.7);"
        else:  # fade
            r = "%g*(2.3+math.max(0,q.life_time-9.3)*1.2)" % r0
            tail = ("v.scale=math.max(0.02,0.4-math.max(0,q.life_time-9.3)*0.55);"
                    "v.ypos=math.max(0,q.life_time-9.3)*10;")
        out.append("v.R=%s;%s%s" % (r, _pos(c), tail))
    return out


PHASES = ["expand", "hold", "pulse", "collapse", "shatter", "fade"]
PHASE_GATE = {
    "expand":   "execute if entity @a[scores={cam_t=180..200}]",
    "hold":     "execute if entity @a[scores={cam_t=100..179}]",
    "pulse":    "execute if entity @a[scores={cam_t=70..99}]",
    "collapse": "execute if entity @a[scores={cam_t=45..69}]",
    "shatter":  "execute if entity @a[scores={cam_t=15..44}]",
    "fade":     "execute if entity @a[scores={cam_t=1..14}]",
}


def at_cube(c, cmd):
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
        'scoreboard objectives add cam_t dummy "运镜计时"',
        'scoreboard objectives add cam_cast dummy "施法触发"',
        'scoreboard objectives add cam_cd dummy "咒典冷却"',
        'scoreboard objectives add fmbe_shield dummy "屏障展示体"',
        "tickingarea remove shield_cam",
        ta,
        'tellraw @a {"rawtext":[{"text":"§b屏障咒典 · 千格版 §8· §f手持附魔书施放，§7冷却 25 秒"}]}',
    ]


# ---------------------------------------------------------------- 触发
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
    for i, cb in enumerate(CUBES, start=1):
        c.append("execute at %s run summon fox ~%d ~%d ~%d" % (CASTER, cb["sx"], cb["sy"], cb["sz"]))
        c.append(at_cube(cb, "replaceitem entity @e[type=fox,r=2,c=1] "
                             "slot.weapon.mainhand 0 %s" % cb["item"]))
        c.append(at_cube(cb, "scoreboard players set @e[type=fox,r=2,c=1] fmbe_shield %d" % i))
        # 初始态：缩到脚下 0.05 倍，避免第一刻闪在生成点
        c.append(at_cube(cb, 'playanimation @e[type=fox,r=2,c=1] '
                             'animation.player.attack.positions none 0 '
                             '"v.xbasepos=%g;v.zbasepos=%g;v.ybasepos=%g;v.scale=0.05;" fmbe.init'
                             % (cb["ox"], cb["oz"], cb["y16"])))
        # 起始相位：每格从自己的角度起转，形成螺旋
        c.append(at_cube(cb, 'playanimation @e[type=fox,r=2,c=1] '
                             'animation.player.attack.positions none 0 '
                             '"v.yrot=%g;" fmbe.seed' % cb["ph"]))
    c += [
        "effect %s invisibility 999999 1 true" % SHIELD,
        "effect %s resistance 999999 255 true" % SHIELD,
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.aggro",
        "stopsound @a mob.fox.bite",
        "stopsound @a mob.fox.eat",
        "playsound random.explode @a[r=40] ~ ~ ~ 0.8 0.6",
        "playsound beacon.activate @a[r=40] ~ ~ ~ 1 0.85",
        "playsound item.trident.thunder @a[r=40] ~ ~ ~ 0.9 1.15",
        "playsound raid.horn @a[r=40] ~ ~ ~ 1 1.05",
        "playsound conduit.activate @a[r=40] ~ ~ ~ 0.7 1.3",
        "execute at %s run particle minecraft:knockback_roar_particle ~ ~1.2 ~" % CASTER,
        "execute at %s run particle minecraft:totem_particle ~ ~1.6 ~" % CASTER,
        "execute at %s run particle minecraft:huge_explosion_emitter ~ ~0.4 ~" % CASTER,
        'execute as @a[scores={cam_t=0..}] run titleraw @s title '
        '{"rawtext":[{"text":"§b§l屏 障 领 域"}]}',
        'execute as @a[scores={cam_t=0..}] run titleraw @s subtitle '
        '{"rawtext":[{"text":"§7千格穹顶 · 纯演出"}]}',
        "scoreboard players set @a cam_cast 0",
    ]
    return c


# ---------------------------------------------------------------- 渲染（每刻）
def render_cmds():
    c = [
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
        "execute as %s at @s run tp @s ~ ~ ~ 0 0" % SHIELD,
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.bite",
    ]
    return c


# ---------------------------------------------------------------- 阶段链
def phase_cmds(name):
    # 自转用「累加」而不是绝对值：施法时每格已经种了自己的初始角度（fmbe.seed），
    # 累加才能保住那个相位差，整座看起来是螺旋而不是同一刻起转。
    d_end = len(DOME_CUBES)
    c = [
        'playanimation @e[scores={fmbe_shield=1..%d}] animation.player.attack.positions '
        'none 0 "v.yrot=v.yrot+2.25;" fmbe.spin' % d_end,
        'playanimation @e[scores={fmbe_shield=%d..%d}] animation.player.attack.positions '
        'none 0 "v.yrot=v.yrot-3.5;" fmbe.spin2' % (d_end + 1, N - 1),
        'playanimation @e[scores={fmbe_shield=%d}] animation.player.attack.positions '
        'none 0 "v.yrot=v.yrot+10;" fmbe.spin3' % N,
    ]
    for i, body in enumerate(phase_body(name), start=1):
        c.append('playanimation @e[scores={fmbe_shield=%d}] '
                 'animation.player.attack.positions none 0 "%s" fmbe.ph' % (i, body))
    return c


# ---------------------------------------------------------------- 运镜
def clock_cmds():
    shots = [
        (199, "^ ^0.5 ^-2.0", "out_cubic", 0.8),
        (175, "^ ^3.5 ^-6.0", "in_out_sine", 1.2),
        (145, "^6.0 ^2.5 ^-2.0", "in_out_sine", 1.2),
        (115, "^ ^9.0 ^-5.0", "in_out_sine", 1.2),
        (85,  "^-5.5 ^1.5 ^-3.5", "in_out_sine", 1.2),
        (55,  "^ ^4.0 ^-9.0", "in_out_sine", 1.2),
        (35,  "^ ^0.8 ^-4.5", "out_quad", 0.6),
        (12,  "^ ^1.2 ^-2.6", "out_quad", 0.8),
    ]
    c = ["execute as @a[scores={cam_t=1..}] run scoreboard players remove @s cam_t 1"]
    for t, pos, ease, dur in shots:
        c.append('execute as @a[scores={cam_t=%d}] at @s run camera @s set minecraft:free '
                 'ease %s %s pos %s facing ~ ~1.2 ~' % (t, dur, ease, pos))
    c += [
        "execute as @a[scores={cam_t=199}] run camera @s fov_set 50 0.2 out_quad",
        "execute as @a[scores={cam_t=115}] run camera @s fov_set 80 1.2 in_out_sine",
        "execute as @a[scores={cam_t=55}] run camera @s fov_set 65 1.2 in_out_sine",
        "execute as @a[scores={cam_t=35}] run camera @s fov_set 45 0.4 out_quad",
        "execute as @a[scores={cam_t=115}] run camerashake add @s 0.4 0.3 positional",
        "execute as @a[scores={cam_t=35}] run camerashake add @s 0.7 0.5 positional",
        "execute as @a[scores={cam_t=115}] at @s run playsound totem.use @s ~ ~ ~ 1 1.4",
        "execute as @a[scores={cam_t=35}] at @s run playsound random.explode @s ~ ~ ~ 1 0.8",
        "execute as @a[scores={cam_t=35}] at @s run particle minecraft:huge_explosion_emitter ~ ~2 ~",
        "execute as @a[scores={cam_t=35}] at @s run particle minecraft:totem_particle ~ ~2 ~",
        # 收尾：清相机 → 解锁 → 摘标记 → tp 虚空（不用 kill）
        "execute as @a[scores={cam_t=0}] run camera @s clear",
        "execute as @a[scores={cam_t=0}] run camera @s fov_clear 0.8 out_elastic",
        "execute as @a[scores={cam_t=0}] run inputpermission set @s movement enabled",
        "execute as @a[scores={cam_t=0}] run scoreboard players set @e[scores={fmbe_shield=1..}] fmbe_shield 0",
        "execute as @a[scores={cam_t=0}] run tp @e[scores={fmbe_shield=0}] ~ -400 ~",
        "execute as @a[scores={cam_t=0}] run scoreboard players set @s cam_t -1",
        'execute as @a[scores={cam_t=-1}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§7屏障消散"}]}',
    ]
    return c


# ---------------------------------------------------------------- 冷却
def cooldown_cmds():
    return [
        "execute as @a[scores={cam_cd=1..}] run scoreboard players remove @s cam_cd 1",
        'execute as @a[scores={cam_cd=1..}] run titleraw @s actionbar '
        '{"rawtext":[{"text":"§8屏障咒典 §7冷却 §f"},'
        '{"score":{"name":"@s","objective":"cam_cd"}}]}',
    ]


# ---------------------------------------------------------------- 中断
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


def spec(ta="tickingarea add circle ~ ~ ~ 4 shield_cam"):
    return {
        "meta": {"name": "屏障咒典", "spawn": [8, -58, 7], "gametype": "creative"},
        "chains": [
            {"id": "init", "kind": "impulse", "button": True, "label": "初始化",
             "cmds": init_cmds(ta)},
            {"id": "trigger", "kind": "gated", "label": "触发",
             "gate": "execute if entity %s" % BOOK, "cmds": trigger_cmds()},
            {"id": "cast", "kind": "gated", "label": "施法",
             "gate": "execute if entity @a[scores={cam_cast=1}]", "cmds": cast_cmds()},
            {"id": "render", "kind": "gated", "label": "渲染",
             "gate": "execute if entity %s" % SHIELD, "cmds": render_cmds()},
        ] + [
            {"id": "ph_" + p, "kind": "gated", "label": "阶段·" + p,
             "gate": PHASE_GATE[p], "cmds": phase_cmds(p)}
            for p in PHASES
        ] + [
            {"id": "clock", "kind": "gated", "label": "运镜",
             "gate": "execute if entity @a[scores={cam_t=0..}]", "cmds": clock_cmds()},
            {"id": "cool", "kind": "gated", "label": "冷却",
             "gate": "execute if entity @a[scores={cam_cd=1..}]", "cmds": cooldown_cmds()},
            {"id": "abort", "kind": "impulse", "button": True, "label": "中断",
             "cmds": abort_cmds()},
        ],
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
        {"kind": "sign", "front": ["§l§b屏障咒典 · 千格", "§7主手持附魔书即施放",
                                   "§8冷却 25 秒", "§8六阶段 · 八段运镜"]},
        {"kind": "sign", "front": ["§l§a阶段", "§71 展开 · 2 稳定",
                                   "§73 脉动 · 4 内坍", "§75 碎裂 · 6 消散"]},
        {"kind": "sign", "front": ["§l§e结构", "§7穹顶 61 + 法阵 24",
                                   "§7共 %d 格展示体" % N, "§7清理：tp 虚空"]},
        {"kind": "chest", "name": "咒典", "items": [
            B.item_nbt("enchanted_book", display_name="§b屏障咒典",
                       lore=["§7主手持此典 → 展开领域", "§8冷却 25 秒"]),
            B.item_nbt("light_blue_stained_glass", display_name="§b穹顶下环",
                       lore=["§7淡蓝玻璃 ×24"]),
            B.item_nbt("purple_stained_glass", display_name="§5穹顶上环",
                       lore=["§7紫玻璃 ×24"]),
            B.item_nbt("end_rod", display_name="§f地面法阵", lore=["§7末地烛 ×24"]),
            B.item_nbt("beacon", display_name="§e核心", lore=["§7信标 ×1"]),
        ]},
    ]
    return {"chains": chains, "props": props, "props_pedestal": True}


def measure_ta(s):
    blocks, _, _ = B.build_scene(to_system(s))
    xs = [x for (x, y, z) in blocks]
    zs = [z for (x, y, z) in blocks]
    return ("tickingarea add ~%d ~-4 ~%d ~%d ~4 ~%d shield_cam"
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
        print("[spec] %s  链 %d 条 / 展示格 %d / 命令 %d 条"
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
    B.CHAIN_SUMMARY["clock"] = "倒计时 + 八段运镜 + FOV + 收尾（tp 虚空）"
    info = B.build(a.template, a.out, m["name"], m.get("spawn"), 1, to_system(s))
    print("[完成] %s" % info["out"])
    print("        区块 %d / 命令方块 %d / 按钮 %d / 说明区 %d / 展示格 %d"
          % (info["chunks"], info["blocks"], info["buttons"], info["props"], N))
    if info["blocks"] < MIN_BLOCKS:
        raise SystemExit("命令方块 %d < 硬指标 %d，需要加阶段或加格" % (info["blocks"], MIN_BLOCKS))


if __name__ == "__main__":
    main()
