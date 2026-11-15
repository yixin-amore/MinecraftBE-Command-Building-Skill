#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拔刀剑指令体系 —— spec 生成 / 布局 / 世界打包。

两条用法：
    python build_katana.py --dump-spec specs/katana.json
    python build_katana.py --spec specs/katana.json --template template.mcworld --out 拔刀剑.mcworld

spec 结构：
{
  "meta":    {"name": "...", "spawn": [x,y,z], "gametype": "creative"},
  "objectives": [{"name": "...", "criteria": "dummy", "display": "..."}],
  "chains":  [{"id": "...", "kind": "impulse|repeat", "button": true, "cmds": ["..."]}],
  "panels":  [{"label": "...", "cmds": ["..."]}]        # 每组一行，首条脉冲，其余条件链
}
"""
import argparse
import json
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B

# ---------------------------------------------------------------- 刀光坐标
# (左, 上, 前)，对应 positioned ^左^上^前
SLASH = {
    1: [  # 横斩：右 → 左，弓形
        ("1.2", "0.9", "3"), ("0.8", "1.05", "3"), ("0.4", "1.15", "3"),
        ("", "1.2", "3"),
        ("-0.4", "1.15", "3"), ("-0.8", "1.05", "3"), ("-1.2", "0.9", "3"),
    ],
    2: [  # 上撩：下 → 上
        ("0.9", "0.2", "2.5"), ("0.6", "0.6", "2.8"), ("0.3", "1.0", "3"),
        ("", "1.5", "3.2"),
        ("-0.3", "2.0", "3"), ("-0.6", "2.4", "2.8"), ("-0.9", "2.8", "2.5"),
    ],
    3: [  # 下劈：上 → 下
        ("0.9", "3.0", "2.5"), ("0.6", "2.6", "2.8"), ("0.3", "2.2", "3"),
        ("", "1.8", "3.2"),
        ("-0.3", "1.3", "3"), ("-0.6", "0.9", "2.8"), ("-0.9", "0.5", "2.5"),
    ],
    4: [  # 回旋：环斩，半径 1.5
        ("", "1.2", "1.5"), ("1.1", "1.2", "1.1"), ("1.5", "1.2", ""),
        ("1.1", "1.2", "-1.1"), ("", "1.2", "-1.5"), ("-1.1", "1.2", "-1.1"),
        ("-1.5", "1.2", ""), ("-1.1", "1.2", "1.1"),
    ],
}
PARTICLE = "minecraft:balloon_gas_particle"

# 攻击范围黑名单：掉落物 / 鱼钩 / 经验球 / 船 一律不算敌人
FOE = "type=!item,type=!player,type=!fishing_hook,type=!xp_orb,type=!boat,type=!arrow"

# 主手物品 → 技能
SKILLS = [
    # (id, 物品, 耗能, 冷却, 伤害, 范围, 粒子, 音效)
    (1, "blaze_rod",  40,  40, 14, 5, "minecraft:huge_explosion_emitter", "random.explode"),
    (2, "feather",    60,  60,  6, 4, "minecraft:endrod",                "mob.enderdragon.flap"),
    (3, "nether_star", 100, 100, 30, 8, "minecraft:sonic_explosion",     "random.totem"),
]


def _p(left, up, front):
    """拼 positioned ^左^上^前，空串表示 0（写 ^ 会被当成 0，但显式写 0 更清楚）。"""
    return "positioned ^%s^%s^%s" % (left or "0", up or "0", front or "0")


def energy_bar():
    return B.bar("energy_t", "§b")


HUD = B._escape(
    '{"rawtext":['
    '{"text":"§8⚔ §f连招 §e"},{"score":{"objective":"combo","name":"@s"}},'
    '{"text":"§8/4   §b⚡ §f"},{"score":{"objective":"energy","name":"@s"}},'
    '{"text":"§8/100"},'
    '{"translate":"%%2","with":{"rawtext":['
    '{"selector":"@s[scores={energy=100}]"},{"text":" §e§l满"}]}},'
    '{"text":"\\n§8▏"},' + energy_bar() +
    '{"translate":"%%2","with":{"rawtext":['
    '{"selector":"@s[scores={atk_cd=8}]"},{"text":"\\n§e✦ 命中"}]}},'
    '{"translate":"%%2","with":{"rawtext":['
    '{"selector":"@s[scores={burst_cd=1..}]"},{"text":"  §7冷却 §f"}]}},'
    '{"translate":"%%2","with":{"rawtext":['
    '{"selector":"@s[scores={burst_cd=1..}]"},'
    '{"score":{"objective":"burst_cd","name":"@s"}}]}}'
    ']}'
)


def katana_spec():
    """返回完整 spec。所有状态落计分项，零 tag。"""
    obj = [
        ("blade", "dummy", "持刀"), ("combo", "dummy", "连招"),
        ("combo_t", "dummy", ""), ("combo_alive", "dummy", ""),
        ("atk_cd", "dummy", ""),
        ("energy", "dummy", "能量"), ("energy_t", "dummy", ""),
        ("slash", "dummy", ""), ("slash_t", "dummy", ""),
        ("burst_cd", "dummy", "技能冷却"), ("skill", "dummy", ""),
        ("sys", "dummy", ""),
    ]

    init = []
    for name, crit, disp in obj:
        init.append(("scoreboard objectives add %s %s" % (name, crit)) +
                    (' "%s"' % disp if disp else ""))
    init += [
        "scoreboard players set zero sys 0",
        "scoreboard players set one sys 1",
        "scoreboard players set four sys 4",
        "scoreboard players set five sys 5",
        "scoreboard players set eight sys 8",
        "scoreboard players set twelve sys 12",
        "scoreboard players set twenty sys 20",
        "scoreboard players set hundred sys 100",
        # 世界设置
        "gamerule commandblocksenabled true",
        # 聊天栏灰字屏蔽（gamerule 只管聊天栏，管不到方块控制台）
        # sendcommandfeedback 放最前：它一关，后面这些 gamerule 自己也不再回显
        "gamerule sendcommandfeedback false",
        "gamerule commandblockoutput false",
        "gamerule showdeathmessages false",
        "gamerule announceadvancements false",
        "gamerule showrecipemessages false",
        "gamerule showcoordinates false",
        "gamerule dodaylightcycle false",
        "gamerule doweathercycle false",
        "gamerule keepinventory true",
        "gamerule mobgriefing false",
        # 界面净化
        "hud @a hide health",
        "hud @a hide hunger",
        "hud @a hide armor",
        "hud @a hide status_effects",
        "hud @a hide item_text",
        "effect @a saturation 1 255 true",
        # 出生点与配装（-59 在命令方块层之上，避免卡进方块）
        "setworldspawn 8 -59 7",
        "time set midnight",
        "gamerule doMobSpawning false",
        "give @a iron_sword 1",
        "give @a blaze_rod 1",
        "give @a feather 1",
        "give @a nether_star 1",
        # 靶场
        "summon zombie 8 -60 15",
        "summon zombie 5 -60 15",
        "summon zombie 11 -60 15",
        "tellraw @a " + B._escape(
            '{"rawtext":[{"text":"§b§l拔刀剑 §r§f已就绪\\n'
            '§7主手 §f铁剑 §7= 拔刀（自动连斩）\\n'
            '§7主手 §6烈焰棒§7= 拔刀斩 §8(40能量)\\n'
            '§7主手 §f羽毛§7= 疾风连斩 §8(60能量)\\n'
            '§7主手 §e下界之星§7= 奥义·月华 §8(100能量)"}]}'),
    ]

# ============================================================
# 低耗断链：闸门数 = 输入通道数
#   刀 + 3 个技能 = 4 条常驻。不持械时 4 条闸门全部失败 → 零执行。
# 段内铁律（级联会吃掉后面，所以顺序不能乱）：
#   1) 先把所有"必定成功"的计分板写入做完（@a 无过滤 + operation clamp）
#   2) 再把"可能失败"的（if entity / damage / particle）排到段尾
#   3) 段内任何一条失败 → 它后面全部跳过，所以最关键的放最前
# ============================================================

    def head(with_booleans=False):
        """每段公共头部：兜底 + 递减 + clamp + 连招窗口。全部必定成功。"""
        out = []
        if with_booleans:
            # 布尔位兜底：未赋值玩家也能被 scores={x=0} 匹配
            out += ["scoreboard players add @a %s 0" % n for n in
                    ("blade", "combo", "combo_t", "combo_alive", "atk_cd",
                     "energy", "energy_t", "slash", "slash_t",
                     "burst_cd", "skill")]
        # 递减：不加 scores 过滤（无目标会失败），一律递减后用 operation 夹到 0
        for o in ("atk_cd", "slash_t", "burst_cd", "combo_t"):
            out.append("scoreboard players remove @a %s 1" % o)
            out.append("scoreboard players operation @a %s > zero sys" % o)
        # 连招窗口：combo_alive = min(combo_t, 1)；combo *= combo_alive
        out += [
            "scoreboard players operation @a combo_alive = @a combo_t",
            "scoreboard players operation @a combo_alive < one sys",
            "scoreboard players operation @a combo *= @a combo_alive",
        ]
        # 能量：min(energy, 100)，再算能量条格数
        out += [
            "scoreboard players operation @a energy < hundred sys",
            "execute as @a run scoreboard players operation @s energy_t = @s energy",
            "execute as @a run scoreboard players operation @s energy_t /= five sys",
        ]
        return out

    # ---- 通道 1：铁剑 · 拔刀 ----
    seg_blade = head(with_booleans=True) + [
        "execute as @a run scoreboard players set @s blade 1",
        # 以下都可能失败，按依赖顺序排
        "execute as @a[scores={blade=1,atk_cd=0}] at @s if entity @e[r=3.2,%s]"
        " run scoreboard players set @s atk_cd 8" % FOE,
        "execute as @a[scores={atk_cd=8}] run scoreboard players operation @s slash = @s combo",
        "execute as @a[scores={atk_cd=8}] run scoreboard players set @s slash_t 4",
        "execute as @a[scores={atk_cd=8}] run scoreboard players add @s energy 8",
        "execute as @a[scores={atk_cd=8}] run scoreboard players add @s combo 1",
        "execute as @a[scores={atk_cd=8,combo=5..}] run scoreboard players set @s combo 1",
        "execute as @a[scores={atk_cd=8}] run scoreboard players set @s combo_t 12",
        "execute as @a[scores={atk_cd=8}] run playsound random.orb @s ~~~ 1 1.6",
    ]
    # 刀光：四个形态连续。同时刻通常只有一种形态活跃，失败的那几种本来也没人匹配。
    for form, pts in sorted(SLASH.items()):
        seg_blade += [
            "execute as @a[scores={slash=%d,slash_t=1..}] at @s %s"
            " run particle %s ~~~" % (form, _p(left, up, front), PARTICLE)
            for left, up, front in pts]
    # 伤害放最后：范围里没敌人就失败，被吃的只有它自己
    for seg, dmg in ((1, 3), (2, 3), (3, 4), (4, 7)):
        seg_blade.append(
            "execute as @a[scores={atk_cd=8,combo=%d}] at @s run damage @e[r=3.5,%s]"
            " %d entity_attack entity @s" % (seg, FOE, dmg))
    seg_blade.append("execute as @a run titleraw @s actionbar " + HUD)

    # ---- 通道 2–4：技能武器 ----
    seg_skill = {}
    for sid, item, cost, cd, dmg, rad, part, snd in SKILLS:
        seg_skill[sid] = head() + [
            "execute as @a[hasitem={item=%s,location=slot.weapon.mainhand},"
            "scores={energy=%d..,burst_cd=0}] run scoreboard players set @s skill %d"
            % (item, cost, sid),
            "execute as @a[hasitem={item=%s,location=slot.weapon.mainhand},"
            "scores={energy=%d..,burst_cd=0}] run scoreboard players set @s burst_cd %d"
            % (item, cost, cd),
            "execute as @a[scores={skill=%d,burst_cd=%d,energy=%d..}] at @s"
            " run particle %s ^^1^3" % (sid, cd, cost, part),
            "execute as @a[scores={skill=%d,burst_cd=%d,energy=%d..}]"
            " run playsound %s @s ~~~ 1 1" % (sid, cd, cost, snd),
            # 扣能量在伤害之前：damage 失败不能白嫖技能
            "execute as @a[scores={skill=%d,burst_cd=%d,energy=%d..}]"
            " run scoreboard players remove @s energy %d" % (sid, cd, cost, cost),
            "execute as @a[scores={skill=%d,burst_cd=%d,energy=%d..}] at @s"
            " run damage @e[r=%d,%s] %d entity_attack entity @s"
            % (sid, cd, cost, rad, FOE, dmg),
            "execute as @a run titleraw @s actionbar " + HUD,
        ]

    segments = [{
        "gate": "execute if entity @a[hasitem={item=iron_sword,"
                "location=slot.weapon.mainhand}]",
        "cmds": seg_blade}]
    for sid, item, cost, cd, dmg, rad, part, snd in SKILLS:
        segments.append({
            "gate": "execute if entity @a[hasitem={item=%s,"
                    "location=slot.weapon.mainhand}]" % item,
            "cmds": seg_skill[sid]})

    panels = [
        {"label": "能量拉满", "cmds": [
            "scoreboard players set @p energy 100",
            'tellraw @p {"rawtext":[{"text":"§b⚡ 能量已充满"}]}',
        ]},
        {"label": "补一把刀", "cmds": [
            "give @p iron_sword 1",
            'tellraw @p {"rawtext":[{"text":"§f已获得 §7铁剑"}]}',
        ]},
        {"label": "清空靶场", "cmds": [
            "kill @e[type=zombie]",
            "summon zombie 8 -60 15",
            "summon zombie 5 -60 15",
            "summon zombie 11 -60 15",
            'tellraw @p {"rawtext":[{"text":"§7靶场已重置"}]}',
        ]},
        {"label": "重置自身", "cmds": [
            "scoreboard players reset @p combo",
            "scoreboard players reset @p combo_t",
            "scoreboard players reset @p atk_cd",
            "scoreboard players reset @p energy",
            "scoreboard players reset @p energy_t",
            "scoreboard players reset @p burst_cd",
            "scoreboard players reset @p slash",
            "scoreboard players reset @p slash_t",
            "scoreboard players reset @p skill",
            'tellraw @p {"rawtext":[{"text":"§c连招与能量已重置"}]}',
        ]},
    ]

    return {
        "meta": {"name": "拔刀剑指令世界", "spawn": [8, -59, 7], "gametype": "creative",
                 "debug_output": False},
        "objectives": [{"name": n, "criteria": c, "display": d} for n, c, d in obj],
        "chains": [
            {"id": "init", "kind": "impulse", "button": True, "cmds": init},
            {"id": "tick", "kind": "repeat", "button": False, "segments": segments},
        ],
        "panels": panels,
    }


# ---------------------------------------------------------------- 布局
def _to_chains(spec):
    """把拔刀剑的 spec 转成通用 chains 格式（全部无条件块，断链靠改朝向）。"""
    chains = []
    for ch in spec["chains"]:
        if "segments" in ch:
            # 每个 segment → 一条独立的功能链
            for i, seg in enumerate(ch["segments"]):
                gate = seg["gate"]
                # ❗ 必须带 id：build_cbworld 用它建 chain_fds / 查 CHAIN_SUMMARY
                chains.append({"id": seg.get("id") or "%s%d" % (ch["id"], i),
                               "kind": "gated", "gate": gate,
                               "brk": gate.replace("execute if ", "", 1),
                               # ❗ 三段式的 [2] 重置块靠业务里这条 `{RESET}` 生成
                               #    （build_cbworld 会把它换成 `setblock ~ ~ ~ chain_command_block[...=4]`）。
                               #    漏了它 → [2] 直接是业务命令 → check_chain_break 报
                               #    「重置块不在连接块的下一条」。
                               "cmds": ["{RESET}"] + list(seg["cmds"])})
        elif ch["kind"] == "impulse":
            chains.append({"id": ch.get("id"), "kind": "impulse", "cmds": ch["cmds"],
                           "button": ch.get("button", True)})
        else:
            chains.append({"id": ch.get("id"), "kind": "gated",
                           "gate": "execute if entity @a",
                           "brk": "entity @a", "cmds": ch["cmds"]})
    for panel in spec["panels"]:
        chains.append({"kind": "impulse", "cmds": panel["cmds"], "button": True})
    return chains


def layout(spec):
    """排成多条功能链。逻辑复用 build_cbworld.build_scene。"""
    return B.build_scene({"chains": _to_chains(spec)})


def build_world(template, out, spec):
    """打包世界 —— **直接复用 `build_cbworld.build()`**。

    ❗ 以前这里有一份独立实现，只写子区块 `-4`、entities 只认 3 元组，
    结果「两层布局 / 说明区 / CustomName 自述」全都用不上，还和
    `build_cbworld` 越改越不一致（真实 bug：`blocks, entities = layout(spec)` 解包报错）。
    现在统一走一个入口，通用生成器跟主流程永远同步。
    """
    meta = spec.get("meta", {})
    gt = {"survival": 0, "creative": 1, "adventure": 2,
          "spectator": 3}[meta.get("gametype", "creative")]
    system = {"chains": _to_chains(spec)}
    if spec.get("props"):
        system["props"] = spec["props"]
    if spec.get("props_pedestal"):
        system["props_pedestal"] = True
    return B.build(template, out, meta.get("name", "指令世界"),
                   meta.get("spawn"), gt, system)


def main():
    ap = argparse.ArgumentParser(description="拔刀剑指令体系：spec 生成 / 世界打包")
    ap.add_argument("--dump-spec", metavar="JSON", help="只导出 spec，不生成世界")
    ap.add_argument("--spec", help="读取 spec 生成世界")
    ap.add_argument("--template", help="真实存档 .mcworld，作为 level.dat 模板")
    ap.add_argument("--out", help="输出 .mcworld 路径")
    args = ap.parse_args()

    if args.dump_spec:
        spec = katana_spec()
        os.makedirs(os.path.dirname(os.path.abspath(args.dump_spec)), exist_ok=True)
        with open(args.dump_spec, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        n = sum(len(c.get("cmds", [])) + sum(len(s["cmds"]) for s in c.get("segments", []))
                for c in spec["chains"]) + sum(len(p["cmds"]) for p in spec["panels"])
        nseg = sum(len(c.get("segments", [])) for c in spec["chains"])
        print("[spec] %s  链 %d 条 / 分段 %d 个 / 命令 %d 条"
              % (args.dump_spec, len(spec["chains"]), nseg, n))
        return

    if not (args.spec and args.template and args.out):
        ap.error("生成世界需要 --spec / --template / --out")

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    info = build_world(args.template, args.out, spec)
    print("[完成] %s" % info["out"])
    print("        区块 %d 个，命令方块 %d 个，按钮 %d 个，命令 %d 条"
          % (info["chunks"], info["blocks"], info["buttons"], info["cmds"]))
    chains = _to_chains(spec)
    tot, res = B.tick_stats(chains)
    print("        共 %d 块，%d 条功能链 → 空闲每刻 %d 条（%.1f%%）"
          % (tot, sum(1 for c in chains if c["kind"] == "gated"), res,
             res / tot * 100 if tot else 0))
    print("        下一步：python verify_mcworld.py <文件>")


if __name__ == "__main__":
    main()
