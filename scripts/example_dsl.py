#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""example_dsl —— 用 DSL 写一个完整的小系统（**新写法的模板**）

这个文件演示「代码转指令」的完整流程：

    1. 声明计分项          objectives = [...]
    2. 用 DSL 写业务       每条链 = 一组语义动作
    3. 编译成 spec         to_spec()
    4. 打包世界 / 导出结构  复用 build_cbworld

对比旧写法（`build_katana.py` 那种）：业务命令是手拼字符串，
选择器写 N 遍，`scores=` 容易拼错，改一个字段要全局搜。

**这里没有一行手写命令字符串**（除了 `Raw` 逃生口）。

--------------------------------------------------------------------------
跑法

    python example_dsl.py --dump-spec demo.json
    python example_dsl.py --spec demo.json --template _template.mcworld --out demo.mcworld
    python mcworld_to_structure.py --input demo.mcworld --out demo.mcstructure
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_cbworld as B
from dsl import (P, Ctx, As, SetScore, AddScore, SubScore, OpScore,
                 PlaySound, Particle, Title, Damage, Summon, Kill, Effect,
                 ScoreboardObj, Gamerule, Raw)

# ============================================================ 1. 计分项
OBJECTIVES = [
    ("demo_tick", "dummy", "全局时钟"),
    ("demo_ready", "dummy", "已建档"),
    ("demo_hp", "dummy", "血量镜像"),
    ("demo_cd", "dummy", "冷却"),
    ("demo_fire", "dummy", "触发标记"),
    ("demo_burst", "dummy", "连发余量"),
    ("demo_cap", "dummy", "弹匣容量"),
    ("demo_dmg", "dummy", "单发伤害"),
    ("demo_bullet", "dummy", "子弹标记"),
    ("demo_recoil", "dummy", "弹道射程"),
]

# 数值只有一个源（U33）：改这里，所有地方跟着变
GUN = {
    "name": "试作型",
    "cap": 8,          # 弹匣
    "cd": 6,           # 射速刻
    "dmg": 6,          # 单发伤害
    "burst": 3,        # 连发数
    "range": 12,       # 射程
}


# ============================================================ 2. 业务（DSL）
def chain_init():
    """初始化：建计分项 + 关聊天栏 + 建常加载区。**只跑一次**。"""
    cmds = [ScoreboardObj("add", n, c, d).body() for n, c, d in OBJECTIVES]
    cmds += [
        Gamerule("commandblockoutput", "false").body(),
        Gamerule("sendcommandfeedback", "false").body(),
        Gamerule("showcoordinates", "true").body(),
        # 常加载区：指令区不在出生点附近时必做（第 74 章）
        "tickingarea add ~-2 ~-2 ~-2 ~66 ~6 ~66 demo true",
        'tellraw @a {"rawtext":[{"text":"§b▸ 试作型系统已加载"}]}',
    ]
    return {"id": "init", "kind": "impulse", "button": True, "cmds": cmds}


def chain_clock():
    """主循环：计时 + 冷却递减 + 血量镜像。**每刻跑，必须无闸门**。"""
    cmds = []
    # 计时器
    cmds += Ctx().run(AddScore("@a", "demo_tick", 1))
    # 冷却 / 连发余量递减并夹到 0 —— 这段逻辑以前重复写了三遍
    cmds += clamp_dec("demo_cd")
    # 血量镜像（U34：原版血量说了算，计分板只读）
    cmds += Ctx().as_(P("@a")).run(
        OpScore("@s", "demo_hp", "=", "@s", "health"),
        OpScore("@s", "demo_hp", "*=", "sys_five", "tmp"),
    )
    # 建档：新玩家没有 demo_ready，先补 0（U19）
    cmds += As(P("@a")).if_("entity @s[scores={demo_ready=0..}]").run(
        Raw("scoreboard players set @s demo_ready 1"))
    cmds += As(P("@a")).unless("score @s demo_ready matches 0..").run(
        SetScore("@s", "demo_ready", 0))
    return {"id": "clock", "kind": "loop", "cmds": cmds}


def chain_state():
    """状态：手持指定物品 → 赋参数。**检测完立刻赋全**（U33）。"""
    rod = P("@a", hasitem={"item": "fishing_rod", "location": "slot.weapon.mainhand"})
    cmds = As(rod).run(
        SetScore("@s", "demo_cap", GUN["cap"]),
        SetScore("@s", "demo_dmg", GUN["dmg"]),
    )
    return {"id": "state", "kind": "gated",
            "gate": "execute if entity %s" % rod,
            "cmds": ["{RESET}"] + cmds}


def chain_trigger():
    """扳机：钩子出现 = 有人抛竿。**链里不许有 hasitem**（U26）。"""
    hook = P("@e", type="fishing_hook")
    cmds = As(hook).at("@s").run(
        # 一次抛竿 = 一个连发段（U41）
        SetScore("@s", "demo_burst", GUN["burst"]),
        SetScore("@s", "demo_fire", 1),
    )
    cmds += Ctx().run(Kill(hook))
    return {"id": "trigger", "kind": "gated",
            "gate": "execute if entity %s" % hook,
            "cmds": ["{RESET}"] + cmds}


def chain_shot():
    """开火：有余量 + 冷却归零 → 打一发。**伪连发**（U41）。"""
    shooter = P("@a", scores={"demo_fire": 1})
    cmds = As(shooter).at("@s").unless("score @s demo_cd matches 1..").run(
        # 出弹
        Summon("xp_orb", "^^^1.45", facing="^^^1000"),
        # 枪口 + 音效（4 层，U39）
        Particle("basic_flame_particle", "~ ~1 ~"),
        PlaySound("random.explode", P("@a", r=48), volume=1.0, pitch=0.55, min_volume=100),
        PlaySound("mob.ghast.fireball", P("@a", r=32), volume=0.85, pitch=0.85),
        PlaySound("random.break", P("@a", r=32), volume=0.6, pitch=1.95),
        # 扣弹 / 扣余量 / 重置冷却
        SubScore("@s", "demo_burst", 1),
        SetScore("@s", "demo_cd", GUN["cd"]),
    )
    # 余量打光 → 清触发标记
    cmds += As(P("@a", scores={"demo_burst": "..0"})).run(
        SetScore("@s", "demo_fire", 0))
    return {"id": "shot", "kind": "gated",
            "gate": "execute if entity %s" % shooter,
            "cmds": ["{RESET}"] + cmds}


def chain_bullet():
    """弹道：沿视线逐格扫，命中就地结算（U38）。"""
    bul = P("@e", type="xp_orb", scores={"demo_bullet": 1})
    cmds = []
    # 碰撞穷举（从远到近，最后留下最近的障碍）
    for n in range(GUN["range"], 0, -1):
        cmds += Ctx().as_(bul).at("@s").positioned("~~-498.5~").positioned("^^^%d" % n).if_(
            "block ^ ^ ^ air").run(SetScore("@s", "demo_recoil", n))
    # 命中判定 + 就地扣血
    for n in range(1, GUN["range"] + 1):
        hit = Ctx().as_(bul).at("@s").positioned("^^^%d" % n).positioned("~~-499.5~")
        cmds += hit.run(
            Damage(P("@e", r=1.2, c=1, type="!player"), GUN["dmg"], source="@p"),
            Particle("basic_crit_particle", "~ ~1 ~"),
            PlaySound("mob.irongolem.hit", P("@a", r=20), volume=0.8, pitch=1.6),
        )
    cmds += Ctx().run(Kill(bul))
    return {"id": "bullet", "kind": "gated",
            "gate": "execute if entity %s" % bul,
            "cmds": ["{RESET}"] + cmds}


def panels():
    """面板：补给按钮（脉冲链）。"""
    supply = As(P("@a")).at("@s").run(
        SetScore("@s", "demo_cap", GUN["cap"]),
        PlaySound("random.click", "@s", pitch=1.4),
        Title("@s", "actionbar",
              {"rawtext": [{"text": "§a▸ 已补满"}]}),
    )
    return [{"id": "p_supply", "kind": "impulse", "button": True, "cmds": supply}]


# ============================================================ 3. 语义工具
def clamp_dec(obj, floor="sys_zero", sel="@a"):
    """每刻 -1 再夹到 0。**以前这段重复写三遍**，现在一行调用。"""
    return Ctx().run(
        SubScore(sel, obj, 1),
        OpScore(sel, obj, ">", floor, "sys"),
    )


# ============================================================ 4. 组装
def to_spec():
    chains = [chain_init(), chain_clock(), chain_state(),
              chain_trigger(), chain_shot(), chain_bullet()]
    chains += panels()
    return {
        "meta": {"name": "DSL 示例世界", "spawn": [8, -59, 8], "gametype": "creative"},
        "objectives": [{"name": n, "criteria": c, "display": d} for n, c, d in OBJECTIVES],
        "chains": chains,
    }


def to_system():
    """spec → build_cbworld 的 system 结构。"""
    spec = to_spec()
    chains = []
    for ch in spec["chains"]:
        chains.append(ch)
    return {"chains": chains}


def main():
    ap = argparse.ArgumentParser(description="DSL 示例生成器")
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
        print("[spec] %s  链 %d 条 / 命令 %d 条"
              % (args.dump_spec, len(spec["chains"]), n))
        return

    if not (args.spec and args.template and args.out):
        ap.error("生成世界需要 --spec / --template / --out")

    with open(args.spec, encoding="utf-8") as f:
        json.load(f)                     # 只为校验 JSON 合法
    info = B.build(args.template, args.out, "DSL 示例世界",
                   [8, -59, 8], 1, to_system())
    print("[完成] %s" % info["out"])
    print("        区块 %d / 命令方块 %d / 按钮 %d"
          % (info["chunks"], info["blocks"], info["buttons"]))


if __name__ == "__main__":
    main()
