#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回读 .bdx：解码 BD@ + brotli(BDX\\0\\0 + stream)，与 spec.json 逐块比对。

BDX = b"BD@" + brotli("BDX\\0\\0" + command-stream)；不是 NBT，也不是 zip。
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import brotli

HERE = Path(__file__).resolve().parent
ID_CONST_STR, ID_STATES, ID_BLOCK = 1, 5, 7
ID_X, ID_Y, ID_Z = 21, 23, 25
ID_CMD, ID_END = 27, 88
FACINGS = ["down", "up", "north", "south", "west", "east"]
MODES = ["impulse", "repeat", "chain"]


def cstr(buf: bytes, i: int) -> tuple[str, int]:
    j = buf.index(b"\x00", i)
    return buf[i:j].decode("utf-8"), j + 1


def read(path: Path):
    raw = path.read_bytes()
    assert raw[:3] == b"BD@", "缺少 BD@ 魔数"
    body = brotli.decompress(raw[3:])
    assert body[:5] == b"BDX\x00\x00", "缺少 BDX 头"
    buf, i = body, 5
    names: list[str] = []
    pos = [0, 0, 0]
    out = []
    while i < len(buf):
        op = buf[i]
        i += 1
        if op == ID_CONST_STR:
            s, i = cstr(buf, i)
            names.append(s)
        elif op in (ID_X, ID_Y, ID_Z):
            (v,) = struct.unpack(">i", buf[i:i + 4])
            i += 4
            pos[{ID_X: 0, ID_Y: 1, ID_Z: 2}[op]] += v
        elif op == ID_BLOCK:                     # PlaceBlock: name_id + legacy data
            nid, data = struct.unpack(">HH", buf[i:i + 4])
            i += 4
            out.append({"kind": "block", "name": names[nid], "data": data,
                        "pos": list(pos)})
        elif op == ID_STATES:
            nid, sid = struct.unpack(">HH", buf[i:i + 4])
            i += 4
            out.append({"kind": "block", "name": names[nid],
                        "states": names[sid], "pos": list(pos)})
        elif op == ID_CMD:
            nid, data = struct.unpack(">HH", buf[i:i + 4])
            i += 4
            (mode,) = struct.unpack(">I", buf[i:i + 4])
            i += 4
            cmd, i = cstr(buf, i)
            name, i = cstr(buf, i)
            last, i = cstr(buf, i)
            (delay,) = struct.unpack(">I", buf[i:i + 4])
            i += 4
            eft, track, cond, red = buf[i:i + 4]
            i += 4
            out.append({
                "kind": "command_block", "name": names[nid], "pos": list(pos),
                "mode": MODES[mode], "command": cmd, "custom_name": name,
                "last_output": last, "delay": delay,
                "execute_first_tick": bool(eft), "track_output": bool(track),
                "conditional": bool(cond), "needs_redstone": bool(red),
                "facing": FACINGS[data & 7], "cond_flag": bool(data & 8),
            })
        elif op == ID_END:
            assert i == len(buf), f"Terminate 后还有 {len(buf) - i} 字节"
            break
        else:
            raise SystemExit(f"未知 BDX 指令 {op} @ {i - 1}")
    return out, len(body)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "terrain.bdx"
    spec = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
    blocks, body_len = read(path)
    cbs = [b for b in blocks if b["kind"] == "command_block"]
    others = [b for b in blocks if b["kind"] != "command_block"]
    print(f"文件: {path.name}  {path.stat().st_size} B (解压后 {body_len} B)")
    print(f"命令方块 {len(cbs)} 个，普通方块 {len(others)} 个 -> "
          f"{[b['name'] + '@' + ','.join(map(str, b['pos'])) for b in others]}")

    by_pos = {tuple(b["pos"]): b for b in cbs}
    assert len(by_pos) == len(cbs), "坐标重复"
    assert len(cbs) == len(spec["blocks"]), (len(cbs), len(spec["blocks"]))

    problems = []
    for sb in spec["blocks"]:
        key = tuple(sb["pos"])
        assert key in by_pos, f"BDX 缺少 {sb['id']} @ {key}"
        b = by_pos[key]
        checks = {
            "type": (b["mode"], sb["type"]),
            "command": (b["command"], sb["command"]),
            "facing": (b["facing"], sb["facing"]),
            "delay": (b["delay"], sb["delay"]),
            "needs_redstone": (b["needs_redstone"], sb["redstone"] == "needs_redstone"),
            "conditional": (b["conditional"], sb["condition"] == "conditional"),
            "custom_name": (b["custom_name"], sb["id"]),
        }
        for k, (got, want) in checks.items():
            if got != want:
                problems.append(f"{sb['id']} {k}: bdx={got!r} spec={want!r}")
    if problems:
        print("回读不一致:")
        for p in problems:
            print("  -", p)
        raise SystemExit(1)

    for b in cbs:
        assert b["execute_first_tick"] is True, b
        assert b["track_output"] is True, b
        assert b["last_output"] == "", b
        assert b["cond_flag"] is b["conditional"], b

    heads = [b for b in cbs if b["mode"] != "chain"]
    print(f"头块 {len(heads)} 个：" + ", ".join(
        f"{b['custom_name']}@{b['pos']}({b['mode']},d{b['delay']})" for b in heads))
    xs = [b["pos"][0] for b in cbs]
    ys = [b["pos"][1] for b in cbs]
    zs = [b["pos"][2] for b in cbs]
    print(f"包围盒 x={min(xs)}..{max(xs)} y={min(ys)}..{max(ys)} z={min(zs)}..{max(zs)}"
          f"  ({max(xs)-min(xs)+1}x{max(ys)-min(ys)+1}x{max(zs)-min(zs)+1})")
    print("回读 OK：坐标/朝向/模式/延迟/条件/红石/命令文本/自定义名 全部与 spec 一致")


if __name__ == "__main__":
    main()
