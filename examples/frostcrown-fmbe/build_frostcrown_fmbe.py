#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""霜冠·维丝佩拉 v2：FMBE 模型 + 真实命中检测。

修复 v1 的两个问题：
  1. Boss 不再是一头劫掠兽，而是 14 个 FMBE 狐狸部件 + 2 个隐形 cow 核心。
  2. 不再用“手持武器靠近”扣血：cow 核心戴一顶只剩 1 点耐久的皮革头盔，
     每 tick `replaceitem ... keep` 只在头盔碎了（=真的被击中）时补上；
     紧接着的 conditional chain block 读这次 replaceitem 的成功次数，置 hit=1。
     命中后才扣血，距离/手持武器都不再参与伤害判定。

输出：frostcrown-commands.bdx / spec.json / manual-build.md / manual-build.txt
竞技场复用 frostcrown-arena.bdx（v1 的建筑，未改）。
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 作为 skill example 时在 <repo>/scripts；作为工作目录副本时在 <workspace>/.dsh/skills/...
SKILL = HERE.parents[1] / "scripts"
if not (SKILL / "bdxgen.py").exists():
    SKILL = HERE.parents[1] / ".dsh/skills/mcbe-command-blocks/scripts"
sys.path.insert(0, str(SKILL))
from bdxgen import Block, write_bdx  # noqa: E402

# ---------------------------------------------------------------- geometry
CX, CY, CZ = 515, 2, 515
FLOOR_Y = CY - 1
PLAT_X = (CX - 10, CX + 10)      # 505..525
PLAT_Z = (CZ - 10, CZ + 16)      # 505..531
GRID_Y = CY + 40                 # 42
MAIN_ORIGIN = (CX - 9, GRID_Y, CZ - 9)       # 506,42,506
INIT_ORIGIN = (CX - 9, GRID_Y + 1, CZ - 9)   # 506,43,506
IDLE_ORIGIN = (CX - 9, GRID_Y + 2, CZ - 9)   # 506,44,506
INIT_B_ORIGIN = (CX - 9, GRID_Y + 1, CZ + 1) # 506,43,516
TRIGGER_B = (PLAT_X[0], GRID_Y + 1, CZ + 1)  # 505,43,516
CAST_ORIGIN = (CX - 9, GRID_Y + 2, CZ + 3)   # 506,44,518
TRIGGER = (PLAT_X[0], GRID_Y + 1, CZ - 9)    # 505,43,506
ROW_LEN = 13
ROW_GAP = 1
BOSS = (CX + 0.5, 4.8, CZ + 0.5)
# 一个移动载体 = 真实受击核心。cow 不渲染护甲，适合藏 1 耐久头盔。
# 它被命令推着追玩家；FMBE 部件每 tick 以它为原点相对 tp。
CORE_POS = (CX + 0.5, 4.5, CZ + 1.3)
CORE_OFFSET_Z = CORE_POS[2] - (CZ + 0.5)   # 部件相对载体的 z 偏移=-0.8
# 空中装配线：每个部件一个独立 x 的装配点，间隔 1 格；c=1 永远不会选错。
STAGE_Y, STAGE_Z = 20.0, CZ + 6.0
ARENA_SEL = f"x={CX - 11},y={CY},z={CZ - 11},dx=23,dy=6,dz=23"
TAG_ARENA = f"x={CX - 11},y={FLOOR_Y},z={CZ - 11},dx=23,dy=6,dz=23"
CRYSTALS = [(CX - 7.5, CY, CZ + 0.5), (CX + 7.5, CY, CZ + 0.5)]
STRAYS = [(CX - 2.5, CY, CZ - 2.5), (CX + 2.5, CY, CZ + 2.5)]
EXIT = (CX, CY, CZ + 15)
TICK = f"{CX - 14} {CY - 2} {CZ - 14} {CX + 14} {CY + 58} {CZ + 40}"
FILL_X = (CX - 11, CX + 11)
FILL_Z = (CZ - 11, CZ + 11)
HP_MAX = 6000
FACING = {"south": 3, "north": 2, "east": 5, "west": 4, "up": 1, "down": 0}

# ---------------------------------------------------------------- FMBE 部件
# (name, item, (x,y,z), scale, yscale)
PARTS = [
    ("head", "wither_skeleton_skull", (CX + 0.5, 7.4, CZ + 0.5), 0.90, 1.0),
    ("crown", "gold_block", (CX + 0.5, 8.6, CZ + 0.5), 0.35, 0.6),
    ("halo", "end_rod", (CX + 0.5, 9.4, CZ + 0.5), 0.45, 0.8),
    ("eye_l", "sea_lantern", (CX + 0.0, 7.6, CZ + 0.1), 0.15, 1.0),
    ("eye_r", "sea_lantern", (CX + 1.0, 7.6, CZ + 0.1), 0.15, 1.0),
    ("torso", "blue_ice", (CX + 0.5, 6.2, CZ + 0.5), 1.20, 1.6),
    ("shoulder_l", "polished_diorite", (CX - 0.9, 6.9, CZ + 0.5), 0.65, 0.8),
    ("shoulder_r", "polished_diorite", (CX + 1.9, 6.9, CZ + 0.5), 0.65, 0.8),
    ("arm_l", "packed_ice", (CX - 1.7, 5.5, CZ + 0.5), 0.40, 2.0),
    ("arm_r", "packed_ice", (CX + 2.7, 5.5, CZ + 0.5), 0.40, 2.0),
    ("staff", "end_rod", (CX + 3.8, 5.8, CZ + 0.5), 0.80, 1.0),
    ("cloak", "light_blue_concrete", (CX + 0.5, 5.8, CZ + 1.4), 1.00, 1.3),
    ("wing_l", "white_stained_glass", (CX - 2.0, 6.8, CZ + 1.0), 0.70, 1.2),
    ("wing_r", "white_stained_glass", (CX + 3.0, 6.8, CZ + 1.0), 0.70, 1.2),
]
PART_BY_NAME = {p[0]: p for p in PARTS}
# 模型单位 1/16 格；旋转是角度
IDLE = {
    "head": (0, 0, 0, 0, 0, 0), "crown": (0, 2, 0, 0, 45, 0), "halo": (0, 1, 4, 90, 0, 0),
    "eye_l": (0, 0, -3, 0, 0, 0), "eye_r": (0, 0, -3, 0, 0, 0),
    "torso": (0, 0, 0, 0, 0, 0),
    "shoulder_l": (-2, 0, 0, 0, 0, 25), "shoulder_r": (2, 0, 0, 0, 0, -25),
    "arm_l": (-2, -2, 0, 0, 0, 70), "arm_r": (2, -2, 0, 0, 0, -70),
    "staff": (2, -2, 0, 90, 0, -10), "cloak": (0, 0, 5, 10, 0, 0),
    "wing_l": (-3, 0, 4, 0, 35, 25), "wing_r": (3, 0, 4, 0, -35, -25),
}
CAST = {
    "head": (-1, -1, -2, -8, 0, 0), "crown": (0, 1, 0, 0, 0, 10), "halo": (0, 1, 4, 90, 0, 25),
    "eye_l": (0, 0, -4, 0, 0, 0), "eye_r": (0, 0, -4, 0, 0, 0),
    "torso": (0, 0, -1, -4, 0, 0),
    "shoulder_l": (-2, 1, 0, 0, 0, 35), "shoulder_r": (2, 1, 0, 0, 0, -35),
    "arm_l": (-3, 1, -1, 0, 0, 105), "arm_r": (3, 1, -1, 0, 0, -105),
    "staff": (3, 1, -2, 70, 0, -35), "cloak": (0, 1, 6, 20, 0, 0),
    "wing_l": (-3, 1, 5, 0, 55, 35), "wing_r": (3, 1, 5, 0, -55, -35),
}


def fmt(v) -> str:
    if isinstance(v, float):
        if abs(v) < 0.05:
            return "0"
        return f"{v:.1f}".rstrip("0").rstrip(".")
    return str(v)


def e(*subs, run):
    return "execute " + " ".join(subs) + " run " + run


def block_center(b):
    x, y, z = b["pos"]
    return x + 0.5, y + 0.5, z + 0.5


def look_at(px, py, pz, tx, ty, tz):
    dx, dy, dz = tx - px, ty - py, tz - pz
    h = math.hypot(dx, dz)
    return round(math.degrees(math.atan2(-dx, dz)), 1), round(math.degrees(math.atan2(-dy, h)), 1)


# ---------------------------------------------------------------- FMBE 命令
def fmbe_expr(part, xfm):
    name, item, pos, sc, ys = part
    dx, dy, dz, rx, ry, rz = xfm
    return (
        "v.xbasepos=0;v.ybasepos=0;v.zbasepos=0;"
        f"v.xpos={dx};v.ypos={dy};v.zpos={dz};"
        f"v.xrot={rx};v.yrot={ry};v.zrot={rz};"
        f"v.scale={sc};v.xzscale=1;v.yscale={ys};"
        "v.swelling_scale1=2.1385*math.sqrt(v.xzscale*v.scale);"
        "v.swelling_scale2=2.1385*math.sqrt(v.yscale*v.scale);"
    )


def pose_commands(part, xfm, pose_value):
    name, item, pos, sc, ys = part
    target = f"@e[tag=boss_p_{name}]"
    expr = fmbe_expr(part, xfm)
    cmds = [
        f'playanimation {target} animation.player.sleeping none 0 "" controller.animation.fox.move',
        f'playanimation {target} animation.creeper.swelling none 0 "{expr}" wiki.scale',
        f'playanimation {target} animation.ender_dragon.neck_head_movement none 0 '
        '"v.head_rotation_x=0;v.head_rotation_y=0;v.head_rotation_z=0;'
        'v.head_position_x=(v.xbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);'
        'v.head_position_y=(10.05185375+v.ybasepos*0.467625)*math.sqrt(v.yscale*v.scale);'
        'v.head_position_z=(17.108-v.zbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);" wiki.shift_pos',
        f'playanimation {target} animation.warden.move none 0 '
        '"v.body_x_rot=90+v.xrot;v.body_z_rot=90+v.yrot;" wiki.xrot',
        f'playanimation {target} animation.player.attack.rotations none 0 '
        '"v.attack_body_rot_y=-v.zrot;" wiki.zrot',
        f'playanimation {target} animation.parrot.moving none 0 '
        '"v.wing_flap=(16-v.xpos)*3.3333333;" wiki.xpos',
        f'playanimation {target} animation.minecart.move.v1.0 none 0 '
        '"v.rail_offset.x=0;v.rail_offset.y=1.6485+v.ypos/16;v.rail_offset.z=0;" wiki.ypos',
        f'playanimation {target} animation.parrot.dance none 0 '
        '"v.dance.x=-v.zpos;v.dance.y=0;" wiki.zpos',
    ]
    return [e("if score pose bs matches %d" % pose_value, run=c) for c in cmds]


# ---------------------------------------------------------------- 初始化链
INIT = [
    ("A.计分板", "Boss 全局状态", "scoreboard objectives add bs dummy"),
    ("A.计分板", "玩家命中冷却/破防时间外的辅助分数", "scoreboard objectives add cd dummy"),
    ("A.计分板", "玩家个人伤害", "scoreboard objectives add dmg dummy"),
    ("A.计分板", "FMBE 姿态（0=待机，1=施法）", "scoreboard objectives add pose dummy"),
    ("A.常加载", "竞技场 + 机关平台", f"tickingarea add {TICK} frost"),
    ("A.清场", "清旧 FMBE 部件", "kill @e[tag=boss_part]"),
    ("A.清场", "清旧核心/载体", "kill @e[tag=boss_core]"),
    ("A.清场", "清旧朝向点（兼容 v3）", "kill @e[tag=boss_aim]"),
    ("A.清场", "清仆从", "kill @e[tag=minion]"),
    ("A.清场", "清冰晶", "kill @e[tag=crystal]"),
    ("A.清场", "二阶段冰地板还原",
     f"fill {FILL_X[0]} {FLOOR_Y} {FILL_Z[0]} {FILL_X[1]} {FLOOR_Y} {FILL_Z[1]} packed_ice 0 replace ice"),
    ("A.载体", "召唤隐形载体（移动核心）", f"summon cow {fmt(CORE_POS[0])} {fmt(CORE_POS[1])} {fmt(CORE_POS[2])}"),
    ("A.载体", "载体 tag（movement + core）",
     f"tag @e[type=cow,x={fmt(CORE_POS[0]-0.5)},y={fmt(CORE_POS[1]-0.5)},z={fmt(CORE_POS[2]-0.5)},dx=1,dy=1,dz=1,c=1] add boss_core"),
    ("A.载体", "载体专用 tag",
     f"tag @e[type=cow,x={fmt(CORE_POS[0]-0.5)},y={fmt(CORE_POS[1]-0.5)},z={fmt(CORE_POS[2]-0.5)},dx=1,dy=1,dz=1,c=1] add boss_carrier"),
    ("A.载体", "隐身", "effect @e[tag=boss_core] invisibility infinite 255 true"),
    ("A.载体", "抗性：血由计分板管，核心不能真死", "effect @e[tag=boss_core] resistance infinite 4 true"),
    ("A.载体", "再生/生命提升，防止被连续攻击打死", "effect @e[tag=boss_core] regeneration infinite 4 true"),
    ("A.载体", "防火", "effect @e[tag=boss_core] fire_resistance infinite 255 true"),
    ("A.载体", "生命提升", "effect @e[tag=boss_core] health_boost infinite 4 true"),
    ("A.载体", "先装满耐久；之后只有碎了才会被 keep 补上",
     "replaceitem entity @e[tag=boss_core] slot.armor.head 0 keep leather_helmet 1 9999"),

]
for idx, (name, item, pos, sc, ys) in enumerate(PARTS):
    x, y, z = pos
    sx = CX - 6 + idx
    INIT += [
        ("B.FMBE", f"召唤部件 {name}（装配点 x={sx}）", f"summon fox {fmt(sx)} {fmt(STAGE_Y)} {fmt(STAGE_Z)}"),
        ("B.FMBE", f"部件 {name} 打 boss_part",
         f"tag @e[type=fox,x={fmt(sx-0.4)},y={fmt(STAGE_Y-1)},z={fmt(STAGE_Z-0.4)},dx=0.8,dy=3,dz=0.8,c=1] add boss_part"),
        ("B.FMBE", f"部件 {name} 独占 tag",
         f"tag @e[type=fox,x={fmt(sx-0.4)},y={fmt(STAGE_Y-1)},z={fmt(STAGE_Z-0.4)},dx=0.8,dy=3,dz=0.8,c=1] add boss_p_{name}"),
        ("B.FMBE", f"部件 {name} 移到最终坐标", f"tp @e[tag=boss_p_{name}] {fmt(x)} {fmt(y)} {fmt(z)}"),
        ("B.FMBE", f"部件 {name} 主手模型",
         f"replaceitem entity @e[tag=boss_p_{name}] slot.weapon.mainhand 0 {item}"),
    ]
INIT += [
    ("B.FMBE", "全体隐身/抗性/减速", "effect @e[tag=boss_part] invisibility infinite 255 true"),
    ("B.FMBE", "全体抗性", "effect @e[tag=boss_part] resistance infinite 255 true"),
    ("B.FMBE", "全体减速", "effect @e[tag=boss_part] slowness infinite 255 true"),
    ("B.FMBE", "成年（狐狸幼体模型会小一圈）", "event entity @e[tag=boss_part] minecraft:ageable_grow_up"),
    ("B.FMBE", "关掉狐狸/牛叫声", "stopsound @a mob.fox.ambient"),
    ("B.FMBE", "关掉核心牛叫声", "stopsound @a mob.cow.ambient"),
    ("C.状态", "满血", f"scoreboard players set hp bs {HP_MAX}"),
    ("C.状态", "冰甲关闭", "scoreboard players set sh bs 0"),
    ("C.状态", "待机", "scoreboard players set st bs 0"),
    ("C.状态", "一阶段", "scoreboard players set ph bs 1"),
    ("C.状态", "阶段播报对齐", "scoreboard players set pa bs 1"),
    ("C.状态", "战斗计时", "scoreboard players set t bs 0"),
    ("C.状态", "节拍", "scoreboard players set bt bs 0"),
    ("C.状态", "技能冷却", "scoreboard players set sc bs 60"),
    ("C.状态", "无施法", "scoreboard players set ct bs -1"),
    ("C.状态", "技能 1", "scoreboard players set sk bs 1"),
    ("C.状态", "破防窗口", "scoreboard players set stg bs 0"),
    ("C.状态", "团灭计时", "scoreboard players set wn bs 0"),
    ("C.状态", "命中标志", "scoreboard players set hit bs 0"),
    ("C.状态", "FMBE 待机姿态", "scoreboard players set pose bs 0"),
    ("D.启动器", "拔掉 A 触发红石块", f"setblock {TRIGGER[0]} {TRIGGER[1]} {TRIGGER[2]} air"),
    ("D.启动器", "拔掉 B 触发红石块", f"setblock {TRIGGER_B[0]} {TRIGGER_B[1]} {TRIGGER_B[2]} air"),
    ("D.提示", "复位提示", 'titleraw @a actionbar {"rawtext":[{"text":"§b机关台已复位 · 走进冰窟开战"}]}'),
]

# ---------------------------------------------------------------- 主链
MAIN = [
    ("1.时钟", "战斗计时", "execute if score st bs matches 1..3 run scoreboard players add t bs 1"),
    ("1.时钟", "20 tick 节拍", "execute if score st bs matches 1..3 run scoreboard players add bt bs 1"),
    ("1.时钟", "节拍环回", "execute if score bt bs matches 20.. run scoreboard players set bt bs 0"),
    ("2.核心", "核心没了 → 团灭", "execute if score st bs matches 1 unless entity @e[tag=boss_core] run scoreboard players set st bs 3"),
    # --- 真实命中：只补“已经碎掉”的头盔；成功=本 tick 被击中 ---
    ("3.命中", "核心头盔：碎了才补，keep 成功即真实命中",
     "replaceitem entity @e[tag=boss_core] slot.armor.head 0 keep leather_helmet 1 9999"),
    ("3.命中", "条件块：上一条 replaceitem 成功 → hit=1",
     "scoreboard players set hit bs 1"),
    # --- FMBE 每 tick 锚定，防重力/AI/玩家挤压 ---
]
for name, item, pos, sc, ys in PARTS:
    dx = pos[0] - (CX + 0.5)
    dy = pos[1] - CORE_POS[1]
    dz = pos[2] - CORE_POS[2]
    # 世界轴相对位置：稳定拼接；载体移动时整组跟随。
    MAIN.append(("4.FMBE", f"跟随部件 {name}",
                 f"execute as @e[tag=boss_p_{name}] at @e[tag=boss_carrier] run tp @s ~{fmt(dx)} ~{fmt(dy)} ~{fmt(dz)}"))
MAIN += [
    ("4.载体", "待机回中心", f"execute if score st bs matches 0 as @e[tag=boss_carrier] at @s run tp @s {fmt(CORE_POS[0])} {fmt(CORE_POS[1])} {fmt(CORE_POS[2])}"),
    ("4.载体", "追击（直接 facing 玩家，不依赖载体 yaw）", "execute if score st bs matches 1 as @e[tag=boss_carrier] at @s facing entity @a[tag=fighter,c=1] eyes if entity @a[tag=fighter,r=24] unless entity @a[tag=fighter,r=2.5] run tp @s ^ ^ ^0.18"),
    ("4.载体", "锁 y=4.5", "execute if score st bs matches 1 as @e[tag=boss_carrier] at @s run tp @s ~ 4.5 ~"),
    ("4.载体", "出界回中心", f"execute if score st bs matches 1 as @e[tag=boss_carrier] at @s unless entity @s[x=506,y=2,z=506,dx=18,dy=8,dz=18] run tp @s {fmt(CORE_POS[0])} {fmt(CORE_POS[1])} {fmt(CORE_POS[2])}"),
    ("5.入场", "进圈开战", f"execute if score st bs matches 0 if entity @a[{ARENA_SEL}] run scoreboard players set st bs 1"),
    ("5.入场", "开战标题",
     'execute if score st bs matches 1 if score t bs matches 0 run titleraw @a title '
     '{"rawtext":[{"text":"§b§l霜冠试炼\\n§7以霜铁之刃斩碎冰冠"}]}'),
    ("5.入场", "发试炼之刃",
     f"execute if score st bs matches 1 if score t bs matches 0 run give @a[{ARENA_SEL}] netherite_sword 1"),
    ("5.入场", "清个人伤害",
     f"execute if score st bs matches 1 if score t bs matches 0 run scoreboard players set @a[{ARENA_SEL}] dmg 0"),
    ("5.入场", "圈内玩家 fighter", f"execute as @a[{ARENA_SEL}] run tag @s add fighter"),
    ("5.入场", "补刀", "execute as @a[tag=fighter] unless entity @s[hasitem={item=netherite_sword}] run give @s netherite_sword 1"),
    ("5.入场", "离场脱战", f"execute as @a[tag=fighter] unless entity @s[{ARENA_SEL}] run tag @s remove fighter"),
    ("6.Boss", "1 Hz 冰晶粒子", "execute if score bt bs matches 0 as @e[tag=boss_carrier] at @s run particle minecraft:end_rod ~ ~2 ~"),
    ("6.Boss", "1 Hz 近身踩踏", "execute if score bt bs matches 0 as @e[tag=boss_carrier] at @s run damage @a[tag=fighter,r=4.5] 8 entity_attack"),
    ("6.Boss", "三阶段暴雪", "execute if score ph bs matches 3 if score bt bs matches 0 run damage @a[tag=fighter] 4 magic"),
    # --- 命中结算：hit 只由头盔碎裂事件产生 ---
    ("7.伤害", "无冰甲：40", "execute if score hit bs matches 1 if score st bs matches 1 if score sh bs matches ..0 run scoreboard players remove hp bs 40"),
    ("7.伤害", "冰甲：白烟、不扣血", "execute if score hit bs matches 1 if score st bs matches 1 if score sh bs matches 1 as @e[tag=boss_carrier] at @s run particle minecraft:basic_smoke_particle ~ ~1 ~"),
    ("7.伤害", "破防：额外 40", "execute if score hit bs matches 1 if score st bs matches 1 if score sh bs matches ..0 if score stg bs matches 1.. run scoreboard players remove hp bs 40"),
    ("7.伤害", "个人伤害统计（最近 fighter）", "execute if score hit bs matches 1 if score st bs matches 1 if score sh bs matches ..0 at @e[tag=boss_carrier] run scoreboard players add @p[tag=fighter] dmg 40"),
    ("7.伤害", "命中粒子", "execute if score hit bs matches 1 if score st bs matches 1 as @e[tag=boss_carrier] at @s run particle minecraft:crit ~ ~1 ~ 0.4 0.4 0.4 0 8"),
    ("7.伤害", "清命中标志", "scoreboard players set hit bs 0"),
    ("7.伤害", "血量钳 0", "execute if score hp bs matches ..-1 run scoreboard players set hp bs 0"),
    ("7.伤害", "破防计时", "execute if score stg bs matches 1.. run scoreboard players remove stg bs 1"),
    # --- 阶段 ---
    ("8.阶段", "二阶段", "execute if score st bs matches 1 if score hp bs matches ..4000 run scoreboard players set ph bs 2"),
    ("8.阶段", "三阶段", "execute if score st bs matches 1 if score hp bs matches ..2000 run scoreboard players set ph bs 3"),
    ("8.阶段", "二阶段标题",
     'execute if score ph bs matches 2 if score pa bs matches 1 run titleraw @a title '
     '{"rawtext":[{"text":"§b§l第二阶段\\n§7冰冠碎裂 · 寒冰护甲"}]}'),
    ("8.阶段", "二阶段吼声", f"execute if score ph bs matches 2 if score pa bs matches 1 run playsound mob.ravager.roar @a {CX} {CY+1} {CZ} 1 0.7"),
    ("8.阶段", "开冰甲", "execute if score ph bs matches 2 if score pa bs matches 1 run scoreboard players set sh bs 1"),
    ("8.阶段", "冰晶 1", f"execute if score ph bs matches 2 if score pa bs matches 1 run summon armor_stand {CRYSTALS[0][0]} {CY} {CRYSTALS[0][2]}"),
    ("8.阶段", "冰晶 2", f"execute if score ph bs matches 2 if score pa bs matches 1 run summon armor_stand {CRYSTALS[1][0]} {CY} {CRYSTALS[1][2]}"),
    ("8.阶段", "冰晶 tag", f"execute if score ph bs matches 2 if score pa bs matches 1 run tag @e[type=armor_stand,{TAG_ARENA}] add crystal"),
    ("8.阶段", "冰晶外观", "execute if score ph bs matches 2 if score pa bs matches 1 run replaceitem entity @e[tag=crystal] slot.weapon.offhand minecraft:sea_lantern"),
    ("8.阶段", "地板变冰", f"execute if score ph bs matches 2 if score pa bs matches 1 run fill {FILL_X[0]} {FLOOR_Y} {FILL_Z[0]} {FILL_X[1]} {FLOOR_Y} {FILL_Z[1]} ice 0 replace packed_ice"),
    ("8.阶段", "记住二阶段", "execute if score ph bs matches 2 if score pa bs matches 1 run scoreboard players set pa bs 2"),
    ("8.阶段", "三阶段标题",
     'execute if score ph bs matches 3 if score pa bs matches 2 run titleraw @a title '
     '{"rawtext":[{"text":"§4§l第三阶段 · 暴雪\\n§7寒风暴雪压场 · 冰甲已碎"}]}'),
    ("8.阶段", "三阶段吼声", f"execute if score ph bs matches 3 if score pa bs matches 2 run playsound mob.wither.spawn @a {CX} {CY+1} {CZ} 1 1.2"),
    ("8.阶段", "三阶段加速", "execute if score ph bs matches 3 if score pa bs matches 2 run effect @e[tag=boss_core] speed infinite 1 true"),
    ("8.阶段", "记住三阶段", "execute if score ph bs matches 3 if score pa bs matches 2 run scoreboard players set pa bs 3"),
    # --- 破盾 ---
    ("9.破盾", "冰晶清空 → 破盾标题",
     'execute if score sh bs matches 1.. unless entity @e[tag=crystal] run titleraw @a title '
     '{"rawtext":[{"text":"§b冰甲崩解\\n§e破防 3 秒 · 全力输出"}]}'),
    ("9.破盾", "破防 60 tick", "execute if score sh bs matches 1.. unless entity @e[tag=crystal] run scoreboard players set stg bs 60"),
    ("9.破盾", "关冰甲", "execute if score sh bs matches 1.. unless entity @e[tag=crystal] run scoreboard players set sh bs 0"),
    # --- 技能 ---
    ("10.技能", "冷却", "execute if score st bs matches 1 if score ct bs matches -1 run scoreboard players remove sc bs 1"),
    ("10.技能", "起手 30 tick", "execute if score st bs matches 1 if score ct bs matches -1 if score sc bs matches ..0 run scoreboard players set ct bs 30"),
    ("10.技能", "切技能", "execute if score ct bs matches 30 run scoreboard players add sk bs 1"),
    ("10.技能", "技能环回", "execute if score ct bs matches 30 if score sk bs matches 3 run scoreboard players set sk bs 1"),
    ("10.技能", "下次间隔", "execute if score ct bs matches 30 run scoreboard players set sc bs 80"),
    ("10.技能", "三阶段加速", "execute if score ct bs matches 30 if score ph bs matches 3 run scoreboard players set sc bs 50"),
    ("10.技能", "霜环预告",
     'execute if score ct bs matches 30 if score sk bs matches 1 run titleraw @a actionbar '
     '{"rawtext":[{"text":"§9⚠ 霜环 · 1.5 秒后爆发 · 冲出冰环！"}]}'),
    ("10.技能", "冰魂预告",
     'execute if score ct bs matches 30 if score sk bs matches 2 run titleraw @a actionbar '
     '{"rawtext":[{"text":"§b⚠ 冰魂降临 · 先清召唤物！"}]}'),
    ("10.技能", "起手音效", f"execute if score ct bs matches 30 run playsound mob.wither.shoot @a {CX} {CY+1} {CZ} 1 1.4"),
    ("10.技能", "前摇倒数", "execute if score ct bs matches 1.. run scoreboard players remove ct bs 1"),
    ("10.技能", "霜环结算", "execute if score ct bs matches 0 if score sk bs matches 1 as @e[tag=boss_carrier] at @s run damage @a[tag=fighter,r=6.5] 18 magic"),
    ("10.技能", "霜环减速", "execute if score ct bs matches 0 if score sk bs matches 1 as @e[tag=boss_carrier] at @s run effect @a[tag=fighter,r=6.5] slowness 40 1 true"),
    ("10.技能", "霜环粒子", "execute if score ct bs matches 0 if score sk bs matches 1 as @e[tag=boss_carrier] at @s run particle minecraft:huge_explosion_emitter ~ ~ ~"),
    ("10.技能", "冰魂 1", f"execute if score ct bs matches 0 if score sk bs matches 2 run summon stray {STRAYS[0][0]} {STRAYS[0][1]} {STRAYS[0][2]}"),
    ("10.技能", "冰魂 2", f"execute if score ct bs matches 0 if score sk bs matches 2 run summon stray {STRAYS[1][0]} {STRAYS[1][1]} {STRAYS[1][2]}"),
    ("10.技能", "冰魂 tag", f"execute if score ct bs matches 0 if score sk bs matches 2 run tag @e[type=stray,{TAG_ARENA}] add minion"),
    ("10.技能", "收技能", "execute if score ct bs matches 0 run scoreboard players set ct bs -1"),
    ("10.技能", "冰魂上限", "execute if score bt bs matches 0 if entity @e[tag=minion,c=3] run kill @e[tag=minion,c=1]"),
    # --- 姿态 ---
    ("11.姿态", "施法时切 cast 姿态", "execute if score ct bs matches 0.. run scoreboard players set pose bs 1"),
    ("11.姿态", "收技能回待机", "execute if score ct bs matches ..-1 run scoreboard players set pose bs 0"),
    # --- UI ---
    ("12.UI", "血条 A",
     'execute if score st bs matches 1 if score bt bs matches 0 run titleraw @a actionbar '
     '{"rawtext":[{"text":"§b❄ 霜冠·维丝佩拉 §8| §fHP §c"},{"score":{"name":"hp","objective":"bs"}},'
     '{"text":"§8/§f6000 §8| §e阶段 "},{"score":{"name":"ph","objective":"bs"}}]}'),
    ("12.UI", "血条 B",
     'execute if score st bs matches 1 if score bt bs matches 10 run titleraw @a actionbar '
     '{"rawtext":[{"text":"§b❄ 霜冠·维丝佩拉 §8| §fHP §c"},{"score":{"name":"hp","objective":"bs"}},'
     '{"text":"§8/§f6000 §8| §e阶段 "},{"score":{"name":"ph","objective":"bs"}}]}'),
    # --- 胜利 ---
    ("13.胜利", "t=0 门", "execute if score st bs matches 1 if score hp bs matches ..0 run scoreboard players set t bs 0"),
    ("13.胜利", "进入胜利", "execute if score st bs matches 1 if score hp bs matches ..0 run scoreboard players set st bs 2"),
    ("13.胜利", "杀核心/载体", "execute if score st bs matches 2 if score t bs matches 0 run kill @e[tag=boss_core]"),
    ("13.胜利", "杀 FMBE 部件", "execute if score st bs matches 2 if score t bs matches 0 run kill @e[tag=boss_part]"),
    ("13.胜利", "清冰魂", "execute if score st bs matches 2 if score t bs matches 0 run kill @e[tag=minion]"),
    ("13.胜利", "清冰晶", "execute if score st bs matches 2 if score t bs matches 0 run kill @e[tag=crystal]"),
    ("13.胜利", "通关标题",
     'execute if score st bs matches 2 if score t bs matches 0 run titleraw @a title '
     '{"rawtext":[{"text":"§b§l霜冠陨落\\n§7试炼完成"}]}'),
    ("13.胜利", "死亡音效", "execute if score st bs matches 2 if score t bs matches 0 run playsound mob.wither.death @a"),
    ("13.胜利", "传出门", f"execute if score st bs matches 2 if score t bs matches 0 run tp @a[tag=fighter] {EXIT[0]} {EXIT[1]} {EXIT[2]}"),
    ("13.胜利", "战利品", "execute if score st bs matches 2 if score t bs matches 0 run give @a[tag=fighter] netherite_ingot 3"),
    ("13.胜利", "个人伤害",
     'execute if score st bs matches 2 if score t bs matches 0 run titleraw @a actionbar '
     '{"rawtext":[{"text":"§e你的伤害 §f"},{"score":{"name":"*","objective":"dmg"}},'
     '{"text":" §8| §b重开：放红石块到 §f505 43 506"}]}'),
    # --- 团灭 ---
    ("14.团灭", "有人重置计时", "execute if score st bs matches 1 if entity @a[tag=fighter] run scoreboard players set wn bs 0"),
    ("14.团灭", "无人计时", "execute unless entity @a[tag=fighter] if score st bs matches 1..3 run scoreboard players add wn bs 1"),
    ("14.团灭", "4 秒团灭", "execute if score st bs matches 1 if score wn bs matches 80 run scoreboard players set st bs 3"),
    ("14.团灭", "团灭标题",
     'execute if score st bs matches 3 if score wn bs matches 100 run titleraw @a title '
     '{"rawtext":[{"text":"§4§l团灭\\n§7重新开战：放红石块到 §f505 43 506"}]}'),
]

# 姿态链：idle 和 cast 分开，每条命令自己带 pose 门
POSE_IDLE = [
    ("11.姿态", f"idle {part[0]} #{i+1}", c)
    for part in PARTS for i, c in enumerate(pose_commands(part, IDLE[part[0]], 0))
]
POSE_CAST = [
    ("11.姿态", f"cast {part[0]} #{i+1}", c)
    for part in PARTS for i, c in enumerate(pose_commands(part, CAST[part[0]], 1))
]


# 长链分两段：A=核心+前 8 部件，B=后 6 部件+效果/状态。
# 115 块单链在真机会吞掉一些 tag 命令；拆成 63/53 两条后每段都短。
_summons = [i for i, (g, n, c) in enumerate(INIT) if n.startswith("召唤部件")]
_split = _summons[8]
INIT_A = INIT[:_split]
INIT_B = INIT[_split:]


# ---------------------------------------------------------------- layout
def snake(n: int, origin, row_len=ROW_LEN, gap=ROW_GAP):
    x0, y, z0 = origin
    xmin, xmax = x0, x0 + row_len - 1
    pts = []
    row = 0
    while len(pts) < n:
        east = row % 2 == 0
        xs = range(xmin, xmax + 1) if east else range(xmax, xmin - 1, -1)
        for x in xs:
            if len(pts) >= n:
                break
            pts.append((x, y, z0 + row * gap))
        if len(pts) >= n:
            break
        row += 1
    out = []
    for i, (x, y, z) in enumerate(pts):
        if i + 1 < len(pts):
            nx, _, nz = pts[i + 1]
            face = "east" if nx > x else "west" if nx < x else "south" if nz > z else "north"
        else:
            face = "east"
        out.append((x, y, z, face))
    return out


def build_blocks():
    blocks = []
    for chain, origin, cmds, head_type, delay, redstone in [
        ("init_a", INIT_ORIGIN, INIT_A, "impulse", 0, "needs_redstone"),
        ("init_b", INIT_B_ORIGIN, INIT_B, "impulse", 0, "needs_redstone"),
        ("main", MAIN_ORIGIN, MAIN, "repeat", 0, "always_active"),
        ("pose_idle", IDLE_ORIGIN, POSE_IDLE, "repeat", 2, "always_active"),
        ("pose_cast", CAST_ORIGIN, POSE_CAST, "repeat", 2, "always_active"),
    ]:
        for i, ((group, note, cmd), (x, y, z, face)) in enumerate(zip(cmds, snake(len(cmds), origin)), start=1):
            prefix = {"init_a": "ia", "init_b": "ib", "main": "m", "pose_idle": "pi", "pose_cast": "pc"}[chain]
            b = dict(
                id=f"{prefix}{i:02d}",
                chain=chain, group=group, note=note, command=cmd,
                type=head_type if i == 1 else "chain",
                facing=face, pos=[x, y, z],
                redstone=redstone if i == 1 else "always_active",
                condition="unconditional", delay=delay if i == 1 else 0,
            )
            # 关键：replaceitem 后面紧邻的 conditional block 读它是否成功
            if chain == "main" and i > 1 and cmd == "scoreboard players set hit bs 1":
                b["condition"] = "conditional"
            blocks.append(b)
    # 链接
    for chain in ("init_a", "init_b", "main", "pose_idle", "pose_cast"):
        arr = [b for b in blocks if b["chain"] == chain]
        for a, b in zip(arr, arr[1:]):
            a["next"] = b["id"]
    return blocks


# ---------------------------------------------------------------- spec
def emit_spec(blocks):
    spec = {
        "name": "frostcrown-fmbe",
        "description": "霜冠·维丝佩拉 v2：14 部件 FMBE 冰霜女王 + 隐形 cow 核心 + 耐久头盔真实命中检测。",
        "target_version": "1.21.130",
        "setup": ["gamerule commandblockoutput false", "gamerule sendcommandfeedback false"],
        "tests": [
            "放红石块到 505 43 506：出现 14 个 FMBE 部件 + 隐形核心，行动栏复位提示",
            "走进冰窟：标题、发剑、血条",
            "站在远处空挥：hp 不动（不是靠近就扣血）",
            "实际砍中核心：头盔碎 → 下一 tick 补头盔 → hp 减 40",
            "用任意武器/空手打中核心：同样只按真实命中结算（不再限定剑）",
            "二阶段：冰甲上身，砍中只冒白烟；冰晶打碎后破防 3 秒双倍",
            "三阶段：暴雪 + 技能加速；打空血：Boss/部件消失、玩家传出、拿战利品",
            "4 秒无人：团灭标题；重放红石块：核心/部件/状态全部复位",
        ],
        "notes": [
            "FMBE：14 只 fox + 主手方块模型；idle/cast 两套 8 条 playanimation 链，每 2 tick 刷新。",
            "命中：cow 核心 slot.armor.head 戴 leather_helmet 1 9999；每 tick replaceitem ... keep 只在头盔碎时成功；紧跟的 conditional block 置 hit=1。",
            "距离、hasitem、手持武器都不参与伤害判定；只有核心真的被击中（头盔碎）才扣血。",
            "核心抗性 IV + 再生 + 生命提升 + 每 tick 锚定，保证不会真死/被推走。",
            "所有命令方块 unconditional（除命中检测那一块），拐弯不需要条件方块。",
        ],
        "blocks": [],
    }
    for b in blocks:
        item = {k: b[k] for k in ("id", "type", "condition", "redstone", "delay", "command", "pos", "facing")}
        item["note"] = f"{b['group']} · {b['note']}"
        if b.get("next"):
            item["next"] = b["next"]
        spec["blocks"].append(item)
    (HERE / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- manual
def setblock_cmd(b):
    block = {"impulse": "command_block", "repeat": "repeating_command_block", "chain": "chain_command_block"}[b["type"]]
    cond = "true" if b["condition"] == "conditional" else "false"
    return f'setblock {b["pos"][0]} {b["pos"][1]} {b["pos"][2]} {block} ["facing_direction"={FACING[b["facing"]]},"conditional_bit"={cond}]'


def vantage(b):
    x, y, z = b["pos"]
    vx, vy, vz = x + 0.5, y + 2.0, z + 0.5
    yaw, pitch = look_at(vx, vy, vz, x + 0.5, y + 0.5, z + 0.5)
    return vx, vy, vz, yaw, pitch


def emit_manual(blocks):
    lines = ["# 霜冠·维丝佩拉 v2 · FMBE 逐块施工表", "",
             "> 竞技场/机关平台：`frostcrown-arena.bdx`，StartPos `500 0 500`。",
             "> 命令方块三层：main `y=42`、init `y=43`、pose `y=44`。",
             "> 触发：`setblock 505 43 506 redstone_block`（init 链尾自动拔掉）。", "",
             "```mcfunction", "gamerule commandblockoutput false", "gamerule sendcommandfeedback false", "```", ""]
    for chain, title in [("init_a", "复位链 A（核心+前 8 部件，impulse）"), ("init_b", "复位链 B（后 6 部件+状态，impulse）"),
                         ("main", "主状态机（repeat）"),
                         ("pose_idle", "FMBE 待机姿态（repeat）"), ("pose_cast", "FMBE 施法姿态（repeat）")]:
        arr = [b for b in blocks if b["chain"] == chain]
        lines += [f"## {title} · {len(arr)} 块", ""]
        for b in arr:
            x, y, z = b["pos"]
            vx, vy, vz, yaw, pitch = vantage(b)
            lines += [f"### {b['id'].upper()} · {b['group']} · {b['note']}", "",
                      f"- [ ] 站位：`/tp @s {fmt(vx)} {fmt(vy)} {fmt(vz)} {fmt(yaw)} {fmt(pitch)}`",
                      f"- [ ] 放置：`/{setblock_cmd(b)}`"]
            if b["type"] in ("repeat", "impulse"):
                lines.append(f"- [ ] 红石：**{'Needs Redstone' if b['redstone'] == 'needs_redstone' else 'Always Active'}**")
            if b["condition"] == "conditional":
                lines.append("- [ ] ⚠ 这是 **conditional** 块，必须紧贴上一块（replaceitem）")
            lines += ["- [ ] 命令：", "", "```mcfunction", b["command"], "```", ""]
    (HERE / "manual-build.md").write_text("\n".join(lines), encoding="utf-8")

    txt = ["霜冠·维丝佩拉 v2 · 逐块施工（纯文本）", "三行一组：tp → setblock → 命令", ""]
    for b in blocks:
        vx, vy, vz, yaw, pitch = vantage(b)
        txt += [f"=== {b['id'].upper()} ({b['pos'][0]} {b['pos'][1]} {b['pos'][2]}) {b['type']} {b['facing']} | {b['note']}",
                f"/tp @s {fmt(vx)} {fmt(vy)} {fmt(vz)} {fmt(yaw)} {fmt(pitch)}",
                "/" + setblock_cmd(b), b["command"], ""]
    (HERE / "manual-build.txt").write_text("\n".join(txt), encoding="utf-8")


# ---------------------------------------------------------------- bdx
def emit_bdx(blocks):
    xs = [b["pos"][0] for b in blocks]
    ys = [b["pos"][1] for b in blocks]
    zs = [b["pos"][2] for b in blocks]
    ox, oy, oz = min(xs), min(ys), min(zs)
    items = []
    for b in blocks:
        x, y, z = b["pos"]
        items.append(Block(x - ox, y - oy, z - oz, b["type"], b["command"],
                           facing=b["facing"], delay=b["delay"],
                           conditional=(b["condition"] == "conditional"),
                           needs_redstone=(b["redstone"] == "needs_redstone"),
                           custom_name=b["id"], track_output=True))
    write_bdx(items, str(HERE / "frostcrown-commands.bdx"))
    (HERE / "import-info.json").write_text(json.dumps(
        {"start_pos": [ox, oy, oz], "command_blocks": len(blocks),
         "init": len(INIT), "init_a": len(INIT_A), "init_b": len(INIT_B),
         "main": len(MAIN), "pose_idle": len(POSE_IDLE), "pose_cast": len(POSE_CAST)},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return ox, oy, oz


def main():
    blocks = build_blocks()
    emit_spec(blocks)
    emit_manual(blocks)
    start = emit_bdx(blocks)
    print(json.dumps({
        "init": len(INIT), "main": len(MAIN), "pose_idle": len(POSE_IDLE), "pose_cast": len(POSE_CAST),
        "total": len(blocks), "start_pos": start,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
