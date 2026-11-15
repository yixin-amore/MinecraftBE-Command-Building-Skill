#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""断链结构走查 —— 按用户 U3 定稿的标准格式逐格核对产物。

标准格式（唯一权威，2026-11 用户定稿 · **三段式**）：

    [0]   无条件   execute if entity <选择器>            检测
    [1]   有条件   setblock ~1 ~ ~ chain_command_block["facing_direction"=5]   连接
    [2]   无条件   setblock ~ ~ ~ chain_command_block["facing_direction"=4]    重置
    [3..] 无条件   <业务>

    重置块**紧跟连接块的下一条**，不在链尾（U24）。

    外部断开：无条件 setblock <连接块相对坐标> chain_command_block["facing_direction"=4]
             —— 不包 `execute unless ... run`，不用绝对坐标

    恒真闸门（`execute if entity @a`）的链：**没有检测、没有连接、没有重置**，
    循环块直接装第一条业务，链自己绕回来（U14）。

用法：
    python scripts/check_chain_break.py <cb.json> --expect 6
"""

import argparse
import json
import re
import sys

SETBLOCK_RE = re.compile(
    r'^setblock\s+(~\S*)\s+~\s+(~\S*)\s+chain_command_block\["facing_direction"=(\d)\]$')
GATE_RE = re.compile(r'^execute\s+if\s+entity\s+(.+)$')
SELF_CUT_RE = re.compile(
    r'^setblock\s+~\s+~\s+~\s+chain_command_block\["facing_direction"=(\d)\]$')

FD = {2: (0, -1), 3: (0, 1), 4: (-1, 0), 5: (1, 0)}   # 0=下 1=上 无后继
BACK = {5: 4, 4: 5, 3: 2, 2: 3}

# 用户 U3 规定的**字面写法**（不许改朝向数字）
CONNECT_CANON = 'setblock ~1 ~ ~ chain_command_block["facing_direction"=5]'
RESET_CANON = 'setblock ~ ~ ~ chain_command_block["facing_direction"=4]'


def load(path):
    with open(path, encoding="utf-8") as f:
        return [e for e in json.load(f) if e.get("command")]


def walk(cbs):
    """命令方块 → 有向图（每块指向 fd 方向那一格）→ 所有极大路径。"""
    # ❗ 必须带 y：二楼和一楼在同一 (x,z) 上有方块，只按 x/z 建索引会互相覆盖
    bypos = {(e["x"], e["y"], e["z"]): e for e in cbs}
    nxt = {}
    for k, e in bypos.items():
        dx, dz = FD.get(e.get("fd") or 0, (0, 0))
        # 只在同一层内找后继（跨层不可能相邻）
        t = (k[0] + dx, k[1], k[2] + dz) if (dx or dz) else None
        nxt[k] = t if t in bypos else None

    heads = [k for k in bypos if not any(v == k for v in nxt.values())]
    chains, seen = [], set()
    for h in heads + list(bypos):
        if h in seen:
            continue
        seq, cur = [], h
        while cur is not None and cur not in seen:
            seen.add(cur)
            seq.append(bypos[cur])
            cur = nxt[cur]
        if seq:
            chains.append(seq)
    return chains


def _tag(seq):
    for b in seq:
        m = re.search(r"tg_(\w+)", b["command"])
        if m:
            return m.group(1)[:10]
    return "?"


def check_gated(seq, problems):
    """三段式：检测 → 连接(有条件) → 重置(无条件) → 业务。"""
    gate = GATE_RE.match(seq[0]["command"])
    if not gate:
        problems.append("第 1 格不是检测块：%s" % seq[0]["command"][:46])
    elif gate.group(1).strip() == "@a":
        problems.append("检测还是 `execute if entity @a`（恒真，应编译成常驻链）")
    if seq[0].get("cond") != 0:
        problems.append("检测块 cond=%s（应 0）" % seq[0].get("cond"))
    if seq[0].get("block") != "minecraft:repeating_command_block":
        problems.append("检测块不是循环块：%s" % seq[0].get("block"))

    if len(seq) < 4:
        problems.append("链太短（%d 格）：三段式至少 检测+连接+重置+1 条业务"
                        % len(seq))
        return

    # ---- [1] 连接块：唯一的有条件块 ----
    if seq[1]["command"] != CONNECT_CANON:
        problems.append("连接块不是标准写法：%s（应为 %s）"
                        % (seq[1]["command"], CONNECT_CANON))
    if seq[1].get("cond") != 1:
        problems.append("❗连接块 cond=%s（必须 1，否则检测失败也空转）"
                        % seq[1].get("cond"))
    if not seq[1].get("auto"):
        problems.append("连接块没开「保持开启」")
    if seq[1].get("block") != "minecraft:chain_command_block":
        problems.append("连接块类型 %s" % seq[1].get("block"))

    # ---- [2] 重置块：紧跟连接块的下一条，无条件 ----
    if seq[2]["command"] != RESET_CANON:
        problems.append("❗重置块不在连接块的下一条 / 写法不对：%s（应为 %s）"
                        % (seq[2]["command"], RESET_CANON))
    if seq[2].get("cond") != 0:
        problems.append("重置块 cond=%s（必须 0）" % seq[2].get("cond"))

    # ---- [3..] 业务：全部无条件 ----
    bad = [i for i, b in enumerate(seq[3:], 3) if b.get("cond") == 1]
    if bad:
        problems.append("业务块带条件位：索引 %s（会连坐）" % bad)

    # 三段式不该再有链尾自断块（重置块已经在第 3 格）
    if len(seq) > 4 and SELF_CUT_RE.match(seq[-1]["command"]):
        problems.append("链尾还挂着老的自断块（三段式不需要）")


def check_loop(seq, problems):
    """常驻链：没有闸门 / 复位块 / 自断块。"""
    g = GATE_RE.match(seq[0]["command"])
    if g and g.group(1).strip() == "@a":
        problems.append("常驻链还留着 `execute if entity @a`（应删掉）")
    if len(seq) > 1 and SETBLOCK_RE.match(seq[1]["command"]):
        problems.append("常驻链不该有复位块")
    if SELF_CUT_RE.match(seq[-1]["command"]):
        problems.append("常驻链不该有自断块")
    bad = [i for i, b in enumerate(seq) if b.get("cond") == 1]
    if bad:
        problems.append("常驻链带条件位：%s" % bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cbjson")
    ap.add_argument("--expect", type=int, default=6, help="可断链总条数")
    ap.add_argument("--func", type=int, default=8,
                    help="进断链面板的功能链条数（面板 setblock = 它 × 2）")
    args = ap.parse_args()

    cbs = load(args.cbjson)
    chains = walk(cbs)
    print("命令方块 %d 个 → 走出 %d 条链" % (len(cbs), len(chains)))

    gated = loop = panels = 0
    fail = 0
    for seq in chains:
        head_blk = seq[0].get("block") or ""
        if head_blk != "minecraft:repeating_command_block":
            # 脉冲块起头 = 面板 / 初始化链，靠按钮触发
            panels += 1
            continue
        problems = []
        if len(seq) > 1 and SETBLOCK_RE.match(seq[1]["command"]):
            gated += 1
            check_gated(seq, problems)
            kind = "可断"
        else:
            loop += 1
            check_loop(seq, problems)
            kind = "常驻"
        if problems:
            fail += 1
            print("  ✗ [%s] %-10s %s" % (kind, _tag(seq), "；".join(problems)))
        else:
            print("  ✓ [%s] %-10s %d 格" % (kind, _tag(seq), len(seq)))

    print("\n可断链 %d 条（期望 %d）/ 常驻链 %d 条 / 面板链 %d 条"
          % (gated, args.expect, loop, panels))
    if gated != args.expect:
        print("❗可断链条数不符")
        fail += 1

    dis = [c for c in cbs if c.get("cond") == 0
           and SETBLOCK_RE.match(c["command"])
           and c["command"].startswith("setblock ~")
           and not SELF_CUT_RE.match(c["command"])]     # 排除链尾自断块
    print("面板 setblock（断开+接通）%d 条（期望 %d）" % (len(dis), args.func * 2))
    if len(dis) != args.func * 2:
        fail += 1
    for c in cbs:
        if "unless entity" in c["command"] and "setblock" in c["command"]:
            print("  ✗ 断开命令包了 execute unless：%s" % c["command"][:60])
            fail += 1
        if re.search(r'setblock\s+-?\d+\s+~', c["command"]):
            print("  ✗ 用了绝对坐标：%s" % c["command"][:60])
            fail += 1

    print("\n结论：%s" % ("通过" if fail == 0 else "失败 %d 项" % fail))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
