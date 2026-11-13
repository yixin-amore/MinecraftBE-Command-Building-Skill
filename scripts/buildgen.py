#!/usr/bin/env python3
"""Generate a full-block Bedrock .bdx from a small building plan.

Plan JSON:
{
  "name": "chapel",
  "fills": [
    {"from": [0,64,0], "to": [10,64,10], "block": "stone_bricks"}
  ],
  "blocks": [
    {"pos": [5,65,5], "block": "sea_lantern", "data": 0, "states": ""}
  ],
  "commands": [
    {"pos": [0,65,0], "type": "chain", "command": "say built"}
  ]
}

This is intentionally small and deterministic: it expands fills to blocks,
then writes a BDX containing both normal blocks and command blocks. It does not
need an external writer, Java, or a Minecraft client.

Usage:
    python3 scripts/buildgen.py plan.json out.bdx
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

try:
    from bdxgen import Block, BuildBlock, write_build_bdx
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bdxgen import Block, BuildBlock, write_build_bdx

MAX_BLOCKS = 2_000_000


def expand_fill(f: dict):
    a = list(map(int, f["from"]))
    b = list(map(int, f["to"]))
    lo = [min(a[i], b[i]) for i in range(3)]
    hi = [max(a[i], b[i]) for i in range(3)]
    block = f["block"]
    data = int(f.get("data", 0))
    states = f.get("states", "")
    for x in range(lo[0], hi[0] + 1):
        for y in range(lo[1], hi[1] + 1):
            for z in range(lo[2], hi[2] + 1):
                yield BuildBlock(x, y, z, block, data, states)


def load_plan(path: str):
    plan = json.load(open(path, encoding="utf-8"))
    items = []
    for f in plan.get("fills", []):
        items.extend(expand_fill(f))
        if len(items) > MAX_BLOCKS:
            raise SystemExit(f"plan expands beyond {MAX_BLOCKS} blocks; split it")
    for b in plan.get("blocks", []):
        pos = b["pos"]
        items.append(BuildBlock(int(pos[0]), int(pos[1]), int(pos[2]),
                                b["block"], int(b.get("data", 0)), b.get("states", "")))
    for c in plan.get("commands", []):
        pos = c["pos"]
        items.append(Block(int(pos[0]), int(pos[1]), int(pos[2]),
                           c.get("type", "chain"), c["command"],
                           facing=c.get("facing", "east"),
                           delay=int(c.get("delay", 0)),
                           conditional=bool(c.get("conditional", False)),
                           needs_redstone=bool(c.get("needs_redstone", False))))
    return plan, items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--no-sort", action="store_true")
    args = ap.parse_args()
    plan, items = load_plan(args.plan)
    write_build_bdx(items, args.out, sort_blocks=not args.no_sort)
    blocks = sum(isinstance(x, BuildBlock) for x in items)
    cmds = len(items) - blocks
    size = Path(args.out).stat().st_size
    print(json.dumps({"name": plan.get("name", ""), "out": args.out,
                      "normal_blocks": blocks, "command_blocks": cmds,
                      "total": len(items), "bytes": size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
