#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按功能分链 + 改朝向断链 —— 结构测试件（统一方向约定版）。

方向约定（与 SKILL.md「统一方向约定」一致）：
    链沿 −z（北）排，链首在 +z 端
    运行方向 = 北 = facing_direction 2      ← 复位块用
    链首方向 = 南 = facing_direction 3      ← 断开时用

每条功能链 3 段，**只有复位块有条件位**：

    z0+0   循环块 rep_N   cond=0   execute if entity <闸门条件>
    z0-1   链块   chc_N   cond=1   setblock ~ ~ ~-1 chain_command_block["facing_direction"=2]
    z0-2.. 链块   ch_N    cond=0   <业务，一条失败不连坐后面>

逐 tick：
    闸门成功 → 复位块执行，把下一格摆成朝北(2) → 触发业务 → 全跑
    闸门失败 → 复位块被跳过 → 它"没执行" → 下一格根本不被触发 → 业务一条都不跑
    面板「断开链条」→ 把业务第一格改成朝南(3) → 物理断开，直到复位块把它接回

用法：
    python build_chain_split_demo.py --template _template.mcworld --out 断链-按功能分链.mcworld
"""
import argparse
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B

Y = -60
LY = 4
LYB = 5

RUN_FD = 2      # 运行方向：北，指向下一格
HEAD_FD = 3     # 链首方向：南，指向上一格


def put(blocks, ents, x, z, key, cmd, auto, cond=0):
    blocks[(x, LY, z)] = key
    ents[(x, z)] = (B._escape(cmd), auto, cond)


def btn(blocks, x, z):
    blocks[(x, LYB, z)] = "btn"
    blocks[(x, LY - 1, z)] = "floor_btn"


def gated_chain(blocks, ents, x, z0, gate, brk, business):
    """一条功能链（沿 −z 跑）。brk 保留兼容，未使用。返回链尾 z。

    只有复位块是**有条件**的（全链唯一），业务块全部无条件。
    """
    put(blocks, ents, x, z0, "rep_N", gate, 1, 0)
    # 复位：**有条件**。闸门失败就跳过 → 下一格不被触发 → 业务一条都不跑
    put(blocks, ents, x, z0 - 1, "chc_N",
        'setblock ~ ~ ~-1 chain_command_block["facing_direction"=%d]' % RUN_FD, 1, 1)
    for i, cmd in enumerate(business):
        put(blocks, ents, x, z0 - 2 - i, "ch_N", cmd, 1, 0)
    btn(blocks, x, z0)
    return z0 - 2 - len(business)


def scene():
    blocks, ents = {}, {}
    B.make_floor(blocks, 16, 26, 3)

    # ---------------- 初始化链（x=0，沿 −z，脉冲 + 按钮）----------------
    init = [
        'scoreboard objectives add 奖励分 dummy "奖励分"',
        'scoreboard objectives add 次数 dummy "触发次数"',
        'scoreboard players add @a 奖励分 0',
        'scoreboard players add @a 次数 0',
        'gamerule commandblocksenabled true',
        'gamerule sendcommandfeedback false',
        'gamerule commandblockoutput false',
        'gamerule showdeathmessages false',
        'gamerule announceadvancements false',
        'gamerule showrecipemessages false',
        'gamerule showcoordinates false',
        'hud @a hide health',
        'hud @a hide hunger',
        'hud @a hide armor',
        'hud @a hide status_effects',
        'hud @a hide item_text',
        'setworldspawn 0 -59 13',
        'tellraw @a ' + B._escape(
            '{"rawtext":[{"text":"§b§l按功能分链 · 断链测试 §r§f就绪\\n'
            '§7链沿 §e−z §7排：2 = 运行方向，3 = 断开方向\\n'
            '§7每条链只有 §e第 2 格（复位块）§7有条件，业务全部无条件\\n'
            '§7按 §a给奖励§7 → 链 A 响两声并给苹果；'
            '按 §a加分§7 → 链 B 播报并清零\\n'
            '§7链 C 是常驻链，actionbar 每刻在计数；§c断开链条§7 看物理断链"}]}'),
    ]
    z0 = 24
    for i, c in enumerate(init):
        put(blocks, ents, 0, z0 - i, "imp_N" if i == 0 else "ch_N", c,
            0 if i == 0 else 1, 0)
    btn(blocks, 0, z0)

    # ---------------- 链 A：奖励发放（tag 版，照抄用户示例）----------------
    gated_chain(blocks, ents, 2, 12, 'testfor @a[tag=奖励]', 'entity @a[tag=奖励]', [
        'execute at @a[tag=奖励] run playsound note.pling @p ~~~ 1 1.189207',
        'execute at @a[tag=奖励] run playsound note.pling @p ~~~ 1 1.189207',
        'execute as @a[tag=奖励] run give @s apple',
        'execute as @a[tag=奖励] run tag @s remove 奖励',
    ])

    # ---------------- 链 B：计分板奖励 ----------------
    gated_chain(blocks, ents, 4, 12, 'execute if entity @a[scores={奖励分=1..}]',
                'entity @a[scores={奖励分=1..}]', [
        'execute as @a[scores={奖励分=1..}] run playsound note.pling @s ~~~ 1 1.334840',
        'execute as @a[scores={奖励分=1..}] run playsound random.orb @s ~~~ 0.8 1.5',
        'execute as @a[scores={奖励分=1..}] run give @s apple',
        'execute as @a[scores={奖励分=1..}] run scoreboard players set @s 奖励分 0',
    ])

    # ---------------- 链 C：常驻计数（闸门恒真）----------------
    gated_chain(blocks, ents, 6, 12, 'execute if entity @a', 'entity @a', [
        'scoreboard players add @a 次数 1',
        'execute as @a run titleraw @s actionbar '
        + B._escape('{"rawtext":[{"text":"§8▏ §f链 C 常驻计数  §e"},'
                    '{"score":{"objective":"次数","name":"@s"}}]}'),
    ])

    # ---------------- 面板（x=8..14，沿 −z）----------------
    panels = [
        (8, ['tag @p add 奖励',
             'tellraw @p {"rawtext":[{"text":"§a已给 §e奖励 §a标签 —— 链 A 会响两声并给苹果"}]}']),
        (9, ['setblock 2 -60 10 chain_command_block["facing_direction"=3]',
             'setblock 4 -60 10 chain_command_block["facing_direction"=3]',
             'setblock 6 -60 10 chain_command_block["facing_direction"=3]',
             'tellraw @p {"rawtext":[{"text":"§c三条链的业务第一格已改成朝南 —— 物理断开\\n'
             '§7再按闸门按钮：第 2 格复位块会把它们接回朝北"}]}']),
        (10, ['tag @a remove 奖励',
              'tellraw @p {"rawtext":[{"text":"§7已清除全部 §e奖励 §7标签"}]}']),
        (12, ['scoreboard players set @p 奖励分 1',
              'tellraw @p {"rawtext":[{"text":"§b计分板 §e奖励分=1 §b—— 链 B 会播报并清零"}]}']),
        (14, ['scoreboard players set @a 次数 0',
              'tellraw @p {"rawtext":[{"text":"§7链 C 计数已清零"}]}']),
    ]
    for x, cmds in panels:
        for i, c in enumerate(cmds):
            put(blocks, ents, x, 12 - i, "imp_N" if i == 0 else "ch_N", c,
                0 if i == 0 else 1, 0)
        btn(blocks, x, 12)

    return blocks, ents


def build(template, out, name, spawn, gametype):
    blocks, ents = scene()

    chunks = {}
    for (x, y, z), key in blocks.items():
        chunks.setdefault((x // 16, z // 16), {}).setdefault("blocks", {})[
            (x % 16, y, z % 16)] = key
    for (x, z), val in ents.items():
        chunks.setdefault((x // 16, z // 16), {}).setdefault("ents", {})[
            (x % 16, z % 16)] = val

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
        body = b"".join(
            B.cb_entity(cx * 16 + lx, Y, cz * 16 + lz, cmd, auto, cond)
            for (lx, lz), (cmd, auto, cond) in sorted(c.get("ents", {}).items()))
        if body:
            seq += 1
            pairs.append((seq, kb + b"\x31", body))

    bad = B.check_commands([c for c, _, _ in ents.values()])
    if bad:
        print("[警告] %d 条 JSON 非法：" % len(bad))
        for frag, err in bad[:5]:
            print("   ", frag, "→", err)

    level = B.build_level_dat(template, name, spawn, gametype)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("level.dat", level)
        zf.writestr("levelname.txt", name)
        zf.writestr("world_behavior_packs.json", "[]")
        zf.writestr("world_resource_packs.json", "[]")
        zf.writestr("db/CURRENT", "MANIFEST-000000\n")
        zf.writestr("db/LOCK", b"")
        zf.writestr("db/LOG", b"")
        zf.writestr("db/MANIFEST-000000", B.manifest_bytes(0))
        zf.writestr("db/000001.log", B.log_records(pairs))

    print("[完成] %s" % out)
    print("        区块 %d 个，命令方块 %d 个，按钮 %d 个"
          % (len(chunks), len(ents),
             sum(1 for v in blocks.values() if v == "btn")))
    print("        功能链 3 条 → 空闲每刻只有 3 条闸门在跑")


def main():
    ap = argparse.ArgumentParser(description="按功能分链 + 改朝向断链 · 结构测试件")
    ap.add_argument("--template", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="按功能分链断链测试")
    ap.add_argument("--spawn", nargs=3, type=int, default=[0, -59, 13])
    ap.add_argument("--gametype", default="creative",
                    choices=["survival", "creative", "adventure", "spectator"])
    a = ap.parse_args()
    gt = {"survival": 0, "creative": 1, "adventure": 2, "spectator": 3}[a.gametype]
    build(a.template, a.out, a.name, a.spawn, gt)


if __name__ == "__main__":
    main()
