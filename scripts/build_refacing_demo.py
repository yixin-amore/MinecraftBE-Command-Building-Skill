#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""改朝向式物理断链（re-face gating）演示。

原理（基岩版特性）：
  对命令方块执行 setblock 只给方块状态（facing_direction）、不带 NBT 时，
  方块实体里的 Command / auto / conditionalMode 全部保留 —— 只改朝向，不丢内容。

**范式（2026-11 用户明确，只有 1 个有条件块）**：

  [0]   循环块   无条件   闸门（execute if … / testfor …）
  [1]   链块     **有条件**  复位：把下一格朝向改回运行方向
  [2..] 链块     无条件   业务（一条失败不连坐后面）

  · 闸门失败 → [1] 被跳过 → [2] 根本不被触发 → 业务一条都不跑（空闲只花 1 条）
  · 断开由**外部**改朝向完成（面板按钮 / 另一条链把 x=2 改成朝西）
  · 复位块是唯一有条件块：闸门通过才接通，所以不会每刻空跑 setblock

链结构（沿 +X 排布，facing_direction：东=5 西=4）：

  x=0  repeating  闸门：execute if entity @a[tag=奖励]
  x=1  chain      复位（有条件）：把 x=2 改成朝东
  x=2..5 chain    业务：音效 ×2 / give / 清标记

  · 闸门不满足：x=1 跳过 → x=2 不被触发 → 业务一条都不跑
  · 闸门满足：  x=1 把 x=2 接回朝东 → x=2 起业务全跑
  · 按「断开链条」：x=2 朝西 → 物理断开，闸门再满足也不跑，直到复位块把它接回

用法：
  python build_refacing_demo.py --template 真实存档.mcworld --out 断链演示.mcworld
  python mcworld_to_structure.py --input 断链演示.mcworld --out 断链演示.mcstructure
"""
import argparse
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B

# 世界 y 与子区块局部 y 的换算：子区块索引 -4 → 基准 y = -64
#   局部 0..3 → 世界 -64..-61（地形）
#   局部 4    → 世界 -60（命令方块）
#   局部 5    → 世界 -59（按钮）
Y = -60                 # 世界 y（写进 setblock 命令里用）
LY = 4                  # 子区块局部 y（摆方块用）
LYB = 5


def put(blocks, ents, x, z, key, cmd, auto, cond=0):
    blocks[(x, LY, z)] = key
    ents[(x, z)] = (B._escape(cmd), auto, cond)


def btn(blocks, x, z):
    blocks[(x, LYB, z)] = "btn"
    blocks[(x, LY - 1, z)] = "floor_btn"


def scene():
    blocks, ents = {}, {}

    # ---------- 地面 ----------
    B.make_floor(blocks, 16, 16, 3)

    # ---------- 初始化链（z=2，脉冲 + 按钮）----------
    init = [
        'scoreboard objectives add 奖励 dummy "奖励标记"',
        'scoreboard players add @a 奖励 0',
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
        'setworldspawn 0 -59 7',
        'tellraw @a {"rawtext":[{"text":"§b§l改朝向断链演示 §r§f就绪\\n'
                   '§7每条链只有 §e第 2 格（复位块）§7有条件，后面全是无条件\\n'
                   '§7按 §e「给奖励」§7 听声音；按 §e「断开链条」§7 看物理断链"}]}',
    ]
    for i, c in enumerate(init):
        put(blocks, ents, i, 2, "imp_E" if i == 0 else "ch_E",
            c, 0 if i == 0 else 1)
    btn(blocks, 0, 2)

    # ---------- 演示链 A：tag 版（z=7）----------
    # 只有 x=1 复位块是**有条件**的，x=2.. 业务全部无条件
    z = 7
    put(blocks, ents, 0, z, "rep_E",
        'execute if entity @a[tag=奖励]', 1, cond=0)
    put(blocks, ents, 1, z, "chc_E",
        'setblock ~1 ~ ~ chain_command_block["facing_direction"=5]', 1, cond=1)
    put(blocks, ents, 2, z, "ch_E",
        'execute at @a[tag=奖励] run playsound note.pling @p ~ ~ ~ 1 1.189207', 1)
    put(blocks, ents, 3, z, "ch_E",
        'execute at @a[tag=奖励] run playsound note.pling @p ~ ~ ~ 1 1.334840', 1)
    put(blocks, ents, 4, z, "ch_E",
        'execute as @a[tag=奖励] run give @s apple', 1)
    put(blocks, ents, 5, z, "ch_E",
        'execute as @a[tag=奖励] run tag @s remove 奖励', 1)

    # ---------- 演示链 B：计分板版（z=13，不用 tag）----------
    z = 13
    put(blocks, ents, 0, z, "rep_E",
        'execute if entity @a[scores={奖励=1..}]', 1, cond=0)
    put(blocks, ents, 1, z, "chc_E",
        'setblock ~1 ~ ~ chain_command_block["facing_direction"=5]', 1, cond=1)
    put(blocks, ents, 2, z, "ch_E",
        'execute at @a[scores={奖励=1..}] run playsound note.pling @p ~ ~ ~ 1 1.5', 1)
    put(blocks, ents, 3, z, "ch_E",
        'execute at @a[scores={奖励=1..}] run playsound note.pling @p ~ ~ ~ 1 1.681793', 1)
    put(blocks, ents, 4, z, "ch_E",
        'execute as @a[scores={奖励=1..}] run give @s apple', 1)
    put(blocks, ents, 5, z, "ch_E",
        'execute as @a[scores={奖励=1..}] run scoreboard players set @s 奖励 0', 1)

    # ---------- 面板（脉冲 + 按钮）----------
    panels = [
        # (x, z, 第一块命令, 后续)
        (0, 10, 'tag @p add 奖励',
         ['tellraw @p {"rawtext":[{"text":"§a已获得 §e奖励 §a标签 —— 听声音"}]}']),
        # 改朝向断链：把两条链的第 3 格（x=2）改成朝西 → 物理断开
        (0, 11, 'setblock 2 -60 7 chain_command_block["facing_direction"=4]',
         ['setblock 2 -60 13 chain_command_block["facing_direction"=4]',
          'tellraw @p {"rawtext":[{"text":"§c两条链的第 3 格已改成朝西 —— 物理断开\\n'
          '§7再按 §e「给奖励」§7：第 2 格复位块会把它接回朝东"}]}']),
        (0, 12, 'tag @a remove 奖励',
         ['tellraw @p {"rawtext":[{"text":"§7已清除全部 §e奖励 §7标签"}]}']),
        (0, 15, 'scoreboard players set @p 奖励 1',
         ['tellraw @p {"rawtext":[{"text":"§b计分板 §e奖励=1 §b—— 听另一个音"}]}']),
        (4, 15, 'scoreboard players set @a 奖励 0',
         ['tellraw @p {"rawtext":[{"text":"§7计分板 §e奖励 §7已清零"}]}']),
    ]
    for x0, z, first, rest in panels:
        put(blocks, ents, x0, z, "imp_E", first, 0)
        btn(blocks, x0, z)
        for i, c in enumerate(rest):
            put(blocks, ents, x0 + 1 + i, z, "ch_E", c, 1)

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

    # 常驻统计：循环闸门 = 每刻必定执行
    n_cmd = len(ents)
    n_cond = sum(1 for (c, a, cd) in ents.values() if cd)
    print("[完成] %s" % out)
    print("        区块 %d 个，命令方块 %d 个，按钮 %d 个"
          % (len(chunks), n_cmd,
             sum(1 for v in blocks.values() if v == "btn")))
    print("        主循环常驻：2 条（两条演示链的闸门各 1 条）")
    print("        有条件块：%d 个（两条链的复位块各 1 个，其余全部无条件）" % n_cond)


def main():
    ap = argparse.ArgumentParser(description="改朝向式物理断链演示")
    ap.add_argument("--template", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="改朝向断链演示")
    ap.add_argument("--spawn", nargs=3, type=int, default=[0, -59, 7])
    ap.add_argument("--gametype", default="creative",
                    choices=["survival", "creative", "adventure", "spectator"])
    a = ap.parse_args()
    gt = {"survival": 0, "creative": 1, "adventure": 2, "spectator": 3}[a.gametype]
    build(a.template, a.out, a.name, a.spawn, gt)


if __name__ == "__main__":
    main()
