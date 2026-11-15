#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""霜月·斩魄 —— 冰蓝灵刃（用 DSL 写的拔刀剑）

设计
    日式灵刃，冰蓝 + 紫白能量。四段式：挥砍 → 连击 → 蓄能 → 终结技。

输入（**全部用已验证的检测手段**，不引入未验证技术）
    主手拿刀                → 装备判定（hasitem）
    抛竿（钩子出现）         → 挥砍（同鱼竿枪的扳机，可靠）
    连击                    → 连击窗口内再抛一次，combo +1
    蹲下                    → 蓄能（碰撞箱高度，46.0.5）
    蓄满后站起               → 终结技

四条功能链
    clock   主循环（计时 / 冷却 / 连击窗口 / 蓄能 / 血量镜像）
    slash   挥砍（按连击段数选刀光 + 近战判定）
    charge  蓄能（蹲下累积，站起结算）
    burst   终结技（多重环 + 垂直斩 + 四层音效）

规模目标：约 210 块 / 4 条可断链

跑法
    python build_blade.py --dump-spec blade.json
    python build_blade.py --spec blade.json --template _template.mcworld --out blade.mcworld
    python mcworld_to_structure.py --input blade.mcworld --out 霜月斩魄.mcstructure
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_cbworld as B
from dsl import (P, Ctx, As, SetScore, AddScore, SubScore, OpScore,
                 PlaySound, Particle, Title, Damage, Effect, Kill,
                 ScoreboardObj, Gamerule, Raw)

# ============================================================ 数值表（唯一真值）
BLADE = {
    "name": "霜月·斩魄",
    "item": "iron_sword",        # 主手判定
    "cd": 8,                     # 挥砍冷却（刻）
    "combo_window": 30,          # 连击窗口（刻）
    "combo_max": 3,              # 三段
    "charge_rate": 1,            # 每刻蓄能
    "charge_full": 60,           # 蓄满需要 60 刻
    "reach": 3.5,                # 近战半径
    # 每段的伤害 / 刀光半径 / 音高
    "stages": [
        (1, 7, 2.6, 1.00),       # (段数, 伤害, 刀光半径, 音高)
        (2, 9, 3.0, 1.10),
        (3, 14, 3.6, 1.25),
    ],
    "burst_dmg": 26,
}

OBJECTIVES = [
    ("blade_ready",    "dummy", "已建档"),
    ("blade_cd",       "dummy", "挥砍冷却"),
    ("blade_combo",    "dummy", "连击段数"),
    ("blade_combo_t",  "dummy", "连击窗口"),
    ("blade_charge",   "dummy", "蓄能值"),
    ("blade_charging", "dummy", "蓄能中"),
    ("blade_fire",     "dummy", "挥砍触发"),
    ("blade_hp",       "dummy", "血量镜像"),
    ("blade_hurt",     "dummy", "待结算伤害"),
]

# 冰蓝 + 紫白的粒子组合（全部在 lint 白名单里）
ICE = "minecraft:endrod"                    # 主色：细白蓝线
MIST = "minecraft:soul_particle"            # 寒气：青蓝点
SPARK = "minecraft:sparkler_emitter"        # 碎光
VIOLET = "minecraft:note"                   # 紫白点缀（音符色）
CRIT = "minecraft:basic_crit_particle"      # 命中星


# ============================================================ 工具：环形 / 弧形
def ring(radius, count, particle, y=1.0, center="~ ~ ~"):
    """一圈粒子。**一圈一条链**，不要塞进同一条（G12）。"""
    cmds = []
    for i in range(count):
        import math
        ang = 2 * math.pi * i / count
        x = round(radius * math.cos(ang), 2)
        z = round(radius * math.sin(ang), 2)
        cmds += Ctx().positioned(center).run(
            Particle(particle, "%.2f %.2f %.2f" % (x, y, z)))
    return cmds


def arc(radius, count, particle, y=1.0, spread=140):
    """前方扇形弧（面向玩家正前方）。"""
    import math
    cmds = []
    half = math.radians(spread / 2)
    for i in range(count):
        t = -half + 2 * half * i / max(1, count - 1)
        x = round(radius * math.sin(t), 2)
        z = round(-radius * math.cos(t), 2)      # -Z 是正前方
        cmds += Ctx().positioned("~ ~ ~").run(
            Particle(particle, "%.2f %.2f %.2f" % (x, y, z)))
    return cmds


# ============================================================ 1. 初始化
def chain_init():
    """建计分项 + 关聊天栏 + 常加载区 + 发刀。**只跑一次**。"""
    cmds = [ScoreboardObj("add", n, c, d).body() for n, c, d in OBJECTIVES]
    cmds += [
        Gamerule("commandblockoutput", "false").body(),
        Gamerule("sendcommandfeedback", "false").body(),
        Gamerule("showcoordinates", "true").body(),
        "tickingarea add ~-2 ~-2 ~-2 ~66 ~6 ~66 blade true",
    ]
    # 发刀（带名字，玩家得先拿到手）
    cmds.append(
        'give @a iron_sword 1 0 {"item_lock":{"mode":"lock_in_slot"},'
        '"display":{"Name":"§b霜月·斩魄","Lore":["§7冰蓝灵刃 §8· §f四段式",'
        '"§8—————","§7抛竿§f挥砍 §8/ §7连击三段","§7蹲下§b蓄能 §8/ §7站起§c终结"]}}')
    cmds.append('tellraw @a {"rawtext":[{"text":"§b▸ 霜月·斩魄 §7已入手：抛竿挥砍、蹲下蓄能"}]}')
    return {"id": "init", "kind": "impulse", "button": True,
            "label": "初始化",
            "summary": "建计分项 / 关聊天栏 / 常加载区 / 发刀",
            "cmds": cmds}


# ============================================================ 2. 主循环
def chain_clock():
    """计时 / 血量镜像 / 建档。**每刻跑，无闸门**（断了整个系统就停）。"""
    cmds = []
    # 血量镜像（原版血量说了算，计分板只读）
    cmds += Ctx().as_(P("@a")).run(
        OpScore("@s", "blade_hp", "=", "@s", "health"))
    # 建档（新玩家没有 blade_ready）
    cmds += As(P("@a")).unless("score @s blade_ready matches 0..").run(
        SetScore("@s", "blade_ready", 0))
    return {"id": "clock", "kind": "loop", "label": "主循环",
            "summary": "血量镜像 + 建档（每刻，无闸门）",
            "cmds": cmds}


def chain_combo():
    """冷却 / 连击窗口管理。**独立功能链**：断开后刀还能砍，只是没冷却和连击。"""
    holder = P("@a", hasitem={"item": BLADE["item"], "location": "slot.weapon.mainhand"})
    cmds = []
    cmds += clamp_dec("blade_cd")
    cmds += clamp_dec("blade_combo_t")
    # 连击窗口走完 → 清连击
    cmds += As(P("@a", scores={"blade_combo_t": 0, "blade_combo": "1.."})).run(
        SetScore("@s", "blade_combo", 0))
    return {"id": "combo", "kind": "gated", "label": "连击",
            "summary": "冷却递减 / 连击窗口 / 窗口走完清连击",
            "gate": "execute if entity %s" % holder,
            "cmds": ["{RESET}"] + cmds}


# ============================================================ 3. 挥砍
def chain_slash():
    """钩子出现 = 挥砍。按连击段数选刀光 + 近战判定。"""
    hook = P("@e", type="fishing_hook")
    holder = P("@a", hasitem={"item": BLADE["item"], "location": "slot.weapon.mainhand"})

    cmds = []

    # ① 只有拿刀的人抛竿才算（钩子的 owner 不好取，用最近的持刀玩家）
    cmds += As(holder).at("@s").run(
        SetScore("@s", "blade_fire", 1),
        AddScore("@s", "blade_combo", 1),
        SetScore("@s", "blade_combo_t", BLADE["combo_window"]),
        PlaySound("random.anvil_land", P("@a", r=16), volume=0.6, pitch=1.6),
    )
    # 连击封顶（超过 3 段回到 3）
    cmds += As(P("@a", scores={"blade_combo": "%d.." % (BLADE["combo_max"] + 1)})).run(
        SetScore("@s", "blade_combo", BLADE["combo_max"]))

    # ② 清钩子（抛竿会被吞掉）
    cmds += Ctx().run(Kill(hook))

    # ③ 冷却闸门：冷却中不挥
    cmds += As(P("@a", scores={"blade_fire": 1, "blade_cd": 0})).run(
        SetScore("@s", "blade_cd", BLADE["cd"]))

    # ④ 三段刀光 + 判定（每段一套）
    for stage, dmg, radius, pitch in BLADE["stages"]:
        me = P("@a", scores={"blade_fire": 1, "blade_cd": BLADE["cd"],
                             "blade_combo": stage})
        cmds += As(me).at("@s").run(
            # 刀光：前方弧形，越到后面越宽
            *[Particle(ICE, "%.2f 1.0 %.2f" % (x, z))
              for x, z in _arc_pts(radius, 5, 120)],
            *[Particle(MIST, "%.2f 0.6 %.2f" % (x, z))
              for x, z in _arc_pts(radius * 0.7, 3, 100)],
            # 命中：近战范围判定
            Damage(P("@e", r=radius, c=5, type="!player"), dmg, source="@p"),
            # 命中音效（音高按段数升）
            PlaySound("mob.irongolem.hit", P("@a", r=20), volume=0.8, pitch=pitch),
            PlaySound("mob.ghast.fireball", P("@a", r=12), volume=0.4,
                      pitch=pitch * 1.6),
            # 连击播报
            Title("@s", "actionbar",
                  {"rawtext": [{"text": "§b⚔ §f%d 段 §8· §7%d" % (stage, dmg)}]}),
        )

    # ⑤ 清触发标记
    cmds += As(P("@a", scores={"blade_fire": 1})).run(
        SetScore("@s", "blade_fire", 0))

    return {"id": "slash", "kind": "gated", "label": "挥砍",
            "summary": "钩子触发 → 三段刀光 + 近战判定 + 连击播报",
            "gate": "execute if entity %s" % hook,
            "cmds": ["{RESET}"] + cmds}


def _arc_pts(radius, count, spread):
    """弧形采样点（x, z），-Z 是正前方。"""
    import math
    half = math.radians(spread / 2)
    pts = []
    for i in range(count):
        t = -half + 2 * half * i / max(1, count - 1)
        pts.append((round(radius * math.sin(t), 2),
                    round(-radius * math.cos(t), 2)))
    return pts


# ============================================================ 4. 蓄能
def chain_charge():
    """蹲下 = 蓄能。**用碰撞箱高度判**（基岩版没有 sneaking 选择器）。"""
    holder = P("@a", hasitem={"item": BLADE["item"], "location": "slot.weapon.mainhand"})
    ducking = As(holder).unless("entity @s[y=~1.5,dy=1]").if_("entity @s[y=~1,dy=1]")

    cmds = []
    # 蹲下且未满 → 蓄能 +1，标记蓄能中
    cmds += ducking.if_("entity @s[scores={blade_charge=..%d}]" % (BLADE["charge_full"] - 1)).run(
        AddScore("@s", "blade_charge", BLADE["charge_rate"]),
        SetScore("@s", "blade_charging", 1),
    )
    # 蓄能音（每 5 刻一次，用 charge 的个位判）
    cmds += As(P("@a", scores={"blade_charging": 1, "blade_charge": "1.."})).at("@s").run(
        PlaySound("random.orb", "@s", volume=0.35, pitch=1.8),
    )
    # 蓄满提示（只在刚满那刻响一次）
    cmds += As(P("@a", scores={"blade_charge": BLADE["charge_full"]})).at("@s").run(
        PlaySound("random.click", "@s", volume=1.0, pitch=2.0),
        Title("@s", "actionbar", {"rawtext": [{"text": "§b❄ 霜月已满 §8· §f站起释放"}]}),
    )
    # 蓄能粒子（蹲着时脚边寒气）
    cmds += As(P("@a", scores={"blade_charging": 1})).at("@s").run(
        Particle(MIST, "~ ~0.3 ~"),
        Particle(SPARK, "~ ~0.6 ~"),
    )

    return {"id": "charge", "kind": "gated", "label": "蓄能",
            "summary": "蹲下累积（碰撞箱判定）+ 寒气粒子 + 满值提示",
            "gate": "execute if entity %s" % holder,
            "cmds": ["{RESET}"] + cmds}


# ============================================================ 5. 终结技
def chain_burst():
    """蓄满后站起 = 终结技。多重环 + 垂直斩 + 四层音效。"""
    holder = P("@a", hasitem={"item": BLADE["item"], "location": "slot.weapon.mainhand"})
    ready = P("@a", scores={"blade_charge": BLADE["charge_full"]})
    standing = As(ready).if_("entity @s[y=~1.5,dy=1]")

    cmds = []
    # ① 三重环（半径递增，冰蓝 + 紫白）
    for r, cnt, pt in ((3, 8, ICE), (5, 12, MIST), (7, 16, VIOLET)):
        for x, z in _arc_pts(r, cnt, 360):
            cmds += standing.at("@s").run(
                Particle(pt, "%.2f 1.0 %.2f" % (x, z)))
    # ② 垂直斩（身前一列粒子）
    for y in range(0, 6):
        cmds += standing.at("@s").run(
            Particle(ICE, "0 %.1f -2.0" % (y * 0.6)))
    # ③ 范围伤害
    cmds += standing.at("@s").run(
        Damage(P("@e", r=7, c=10, type="!player"), BLADE["burst_dmg"], source="@p"),
    )
    # ④ 四层音效（低频冲击 / 炮口爆音 / 金属 / 余响）
    cmds += standing.at("@s").run(
        PlaySound("random.explode", P("@a", r=48), volume=1.0, pitch=0.55, min_volume=100),
        PlaySound("mob.ghast.fireball", P("@a", r=32), volume=0.9, pitch=0.75),
        PlaySound("random.anvil_land", P("@a", r=32), volume=0.8, pitch=0.6),
        PlaySound("mob.blaze.hit", P("@a", r=32), volume=0.7, pitch=1.2),
    )
    # ⑤ 清蓄能 + 播报
    cmds += standing.run(
        SetScore("@s", "blade_charge", 0),
        SetScore("@s", "blade_charging", 0),
        Title("@s", "title", {"rawtext": [{"text": "§b❄ 霜月·斩魄"}]}),
        Title("@s", "subtitle", {"rawtext": [{"text": "§f— 终结 —"}]}),
    )

    return {"id": "burst", "kind": "gated", "label": "终结技",
            "summary": "蓄满站起 → 三重环 + 垂直斩 + 四层音效 + 范围伤害",
            "gate": "execute if entity %s" % holder,
            "cmds": ["{RESET}"] + cmds}


# ============================================================ 6. 面板
def panels():
    """补给面板：清冷却 + 补满蓄能（测试用）。"""
    cmds = As(P("@a")).at("@s").run(
        SetScore("@s", "blade_cd", 0),
        SetScore("@s", "blade_charge", BLADE["charge_full"]),
        PlaySound("random.click", "@s", volume=0.8, pitch=1.4),
        Title("@s", "actionbar", {"rawtext": [{"text": "§a▸ 已补满"}]}),
    )
    return [{"id": "p_supply", "kind": "impulse", "button": True,
             "label": "面板·补给", "summary": "清冷却 + 补满蓄能（测试用）",
             "cmds": cmds}]


# ============================================================ 工具
def clamp_dec(obj, floor="sys_zero", sel="@a"):
    """每刻 -1 再夹到 0。"""
    return Ctx().run(SubScore(sel, obj, 1), OpScore(sel, obj, ">", floor, "sys"))


# ============================================================ 说明区
def props():
    """箱子 + 告示牌：**说明做进世界**（U1 / U2），不写外部文档。"""
    I = B.item_nbt
    sep = "§r§7——————————————————"
    items = [
        I("paper", 1, display_name="§8▸ §b霜月·斩魄 §8· §f操作卡", slot=0,
          lore=[
              "§r§7-§b∅ §l§7| §r§f主手 §b铁剑 §7| §r§g武器：主手",
              sep,
              "§r§7-§f抛竿 §7= §b挥砍 §7（连续抛 = 连击）",
              "§r§7-§f蹲下 §7= §b蓄能 §7（脚下冒寒气）",
              "§r§7-蓄满后 §f站起 §7= §c终结技",
              sep,
              "§r§7-三段连击：伤害 §f7 §8/ §f9 §8/ §f14",
              "§r§7-终结技：半径 §f7 §7，伤害 §f26",
              "§r§7-冷却 §f%d §7刻　连击窗口 §f%d §7刻"
              % (BLADE["cd"], BLADE["combo_window"]),
              sep,
              "§o§8............刀比月更冷。"]),
        I("iron_sword", 1, unbreakable=True, slot=1,
          display_name="§r§n⫸§b霜月·斩魄", lore=[
              "§r§7-§b∅ §l§7| §r§1 ∅ 级 §l§7| §r§g武器：主手",
              sep,
              "§r§7-§f抛竿§7挥砍　§f蹲下§7蓄能",
              "§r§7-四段式：挥砍 / 连击 / 蓄能 / 终结",
              sep,
              "§o§8............浪会替你算弹道。"]),
    ]
    signs = [
        ["§8«§b霜月§8»", "§f斩魄", "§8—————", "§7左箱取刀"],
        ["§f抛竿 §b挥砍", "§f连抛 §b连击", "§7三段递增", "§8浮漂会被吞掉"],
        ["§f蹲下 §b蓄能", "§7脚下冒寒气", "§f站起 §c终结", "§8半径 7 格"],
        ["§f四段式", "§7挥砍 §8/ §7连击", "§7蓄能 §8/ §7终结", "§8断开面板可关"],
    ]
    out = [{"kind": "chest", "items": items, "name": "霜月 · 说明箱", "at": (0, 0)}]
    for i, sg in enumerate(signs):
        out.append({"kind": "sign", "front": sg, "at": (i + 2, 0)})
    return out


# ============================================================ 组装
def to_spec():
    chains = [chain_init(), chain_clock(), chain_combo(), chain_slash(),
              chain_charge(), chain_burst()] + panels()
    return {
        "meta": {"name": "霜月·斩魄", "spawn": [8, -59, 8], "gametype": "creative"},
        "objectives": [{"name": n, "criteria": c, "display": d} for n, c, d in OBJECTIVES],
        "chains": chains,
        "props": props(),
        "props_pedestal": True,
    }


def to_system():
    spec = to_spec()
    return {"chains": spec["chains"], "props": spec["props"],
            "props_pedestal": True}


def main():
    ap = argparse.ArgumentParser(description="霜月·斩魄 生成器（DSL）")
    ap.add_argument("--dump-spec")
    ap.add_argument("--spec")
    ap.add_argument("--template")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.dump_spec:
        spec = to_spec()
        with open(args.dump_spec, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=1)
        n = sum(len(c["cmds"]) for c in spec["chains"])
        print("[spec] %s  链 %d 条 / 命令 %d 条" % (args.dump_spec, len(spec["chains"]), n))
        return

    if not (args.spec and args.template and args.out):
        ap.error("生成世界需要 --spec / --template / --out")
    info = B.build(args.template, args.out, "霜月·斩魄", [8, -59, 8], 1, to_system())
    print("[完成] %s" % info["out"])
    print("        区块 %d / 命令方块 %d / 按钮 %d"
          % (info["chunks"], info["blocks"], info["buttons"]))


if __name__ == "__main__":
    main()
