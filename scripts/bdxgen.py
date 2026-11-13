#!/usr/bin/env python3
"""Generate Bedrock .bdx structures without an external writer.

BDX = b"BD@" + brotli("BDX\0\0" + command-stream)
This module writes normal blocks (legacy data or block-state strings) and
command blocks in the same BDX.

Usage:
    from bdxgen import Block, BuildBlock, write_bdx, write_build_bdx
    write_bdx([Block(0, 0, 0, "repeat", "say hello")], "commands.bdx")
    write_build_bdx([BuildBlock(0, 64, 0, "stone_bricks")], "build.bdx")
"""
from __future__ import annotations

import brotli
import struct
from dataclasses import dataclass, field
from typing import Iterable, Literal

try:
    from block_map import normalize as normalize_block
except ImportError:  # pragma: no cover
    def normalize_block(name: str) -> str:
        return name

# BDX command IDs (big-endian payloads)
ID_CREATE_CONSTANT_STRING = 1
ID_PLACE_BLOCK_WITH_STATES = 5
ID_PLACE_BLOCK = 7
ID_ADD_INT32_X = 21
ID_ADD_INT32_Y = 23
ID_ADD_INT32_Z = 25
ID_PLACE_COMMAND_BLOCK = 27
ID_TERMINATE = 88

FACING = {"down": 0, "up": 1, "north": 2, "south": 3, "west": 4, "east": 5}
MODE = {"impulse": 0, "repeat": 1, "chain": 2}


@dataclass
class BuildBlock:
    x: int
    y: int
    z: int
    block: str
    data: int = 0
    states: str = ""


@dataclass
class Block:
    x: int
    y: int
    z: int
    mode: Literal["impulse", "repeat", "chain"]
    command: str
    facing: Literal["down", "up", "north", "south", "west", "east"] = "east"
    delay: int = 0
    conditional: bool = False
    needs_redstone: bool = False
    custom_name: str = ""
    last_output: str = ""
    track_output: bool = False


def _cstr(s: str) -> bytes:
    return s.encode("utf-8") + b"\x00"


def _cmd(cmd_id: int, payload: bytes = b"") -> bytes:
    return bytes([cmd_id]) + payload


def _move(dx: int, dy: int, dz: int) -> bytes:
    out = bytearray()
    if dx:
        out += _cmd(ID_ADD_INT32_X, struct.pack(">i", dx))
    if dy:
        out += _cmd(ID_ADD_INT32_Y, struct.pack(">i", dy))
    if dz:
        out += _cmd(ID_ADD_INT32_Z, struct.pack(">i", dz))
    return bytes(out)


def _place(block_name_id: int, block: Block) -> bytes:
    data = FACING[block.facing] + (8 if block.conditional else 0)
    flags = bytes([
        1 if True else 0,             # ExecuteOnFirstTick
        1 if block.track_output else 0,
        1 if block.conditional else 0,
        1 if block.needs_redstone else 0,
    ])
    payload = bytearray()
    payload += struct.pack(">HH", block_name_id, data)
    payload += struct.pack(">I", MODE[block.mode])
    payload += _cstr(block.command)
    payload += _cstr(block.custom_name)
    payload += _cstr(block.last_output)
    payload += struct.pack(">I", block.delay)
    payload += flags
    return _cmd(ID_PLACE_COMMAND_BLOCK, bytes(payload))


def write_bdx(
    blocks: Iterable[Block],
    path: str,
    *,
    author: str = "",
    sort_blocks: bool = True,
) -> None:
    """Write command blocks to a .bdx file.

    Blocks are translated along X/Y/Z with AddInt32 commands first; the
    reader starts at (0,0,0). Sorting by (y,z,x) keeps moves small.
    """
    blocks = list(blocks)
    if sort_blocks:
        blocks.sort(key=lambda b: (b.y, b.z, b.x))

    stream = bytearray()
    names: dict[str, int] = {}
    pos = [0, 0, 0]
    for b in blocks:
        name = {
            "impulse": "command_block",
            "repeat": "repeating_command_block",
            "chain": "chain_command_block",
        }[b.mode]
        if name not in names:
            names[name] = len(names)
            stream += _cmd(ID_CREATE_CONSTANT_STRING, _cstr(name))
        stream += _move(b.x - pos[0], b.y - pos[1], b.z - pos[2])
        pos = [b.x, b.y, b.z]
        stream += _place(names[name], b)
    stream += bytes([ID_TERMINATE])

    # Non-empty author metadata is rejected by common BDX loaders
    # (unsigned BDX); keep it empty for maximum compatibility.
    header = b"BDX\x00\x00"
    blob = header + bytes(stream)
    with open(path, "wb") as f:
        f.write(b"BD@")
        f.write(brotli.compress(blob, quality=9))


def write_build_bdx(items: Iterable[Block | BuildBlock], path: str, *, sort_blocks: bool = True) -> None:
    """Write normal blocks + command blocks to a .bdx file.

    Normal blocks use PlaceBlock (legacy data) or PlaceBlockWithBlockStates
    (raw Bedrock block-state string). Command blocks use
    PlaceBlockWithCommandBlockData. No external writer is required.
    """
    items = list(items)
    if sort_blocks:
        items.sort(key=lambda b: (b.y, b.z, b.x))

    names: dict[str, int] = {}
    def sid(s: str) -> int:
        if s not in names:
            names[s] = len(names)
        return names[s]

    # Build the constant-string table before writing any placements.
    for it in items:
        if isinstance(it, BuildBlock):
            it.block = normalize_block(it.block)
            sid(it.block)
            if it.states:
                sid(it.states)
        else:
            sid({"impulse": "command_block", "repeat": "repeating_command_block", "chain": "chain_command_block"}[it.mode])

    stream = bytearray()
    for s in names:
        stream += _cmd(ID_CREATE_CONSTANT_STRING, _cstr(s))

    pos = [0, 0, 0]
    for it in items:
        stream += _move(it.x - pos[0], it.y - pos[1], it.z - pos[2])
        pos = [it.x, it.y, it.z]
        if isinstance(it, BuildBlock):
            if it.states:
                stream += _cmd(ID_PLACE_BLOCK_WITH_STATES, struct.pack(">HH", names[it.block], names[it.states]))
            else:
                stream += _cmd(ID_PLACE_BLOCK, struct.pack(">HH", names[it.block], int(it.data) & 0xFFFF))
        else:
            name = {"impulse": "command_block", "repeat": "repeating_command_block", "chain": "chain_command_block"}[it.mode]
            stream += _place(names[name], it)
    stream += bytes([ID_TERMINATE])

    header = b"BDX\x00\x00"
    with open(path, "wb") as f:
        f.write(b"BD@")
        f.write(brotli.compress(header + bytes(stream), quality=9))


def demo(path: str = "demo.bdx") -> None:
    blocks = [
        Block(0, 0, 0, "repeat", "scoreboard objectives add demo dummy", facing="east", delay=0),
        Block(1, 0, 0, "chain", "scoreboard players add @a demo 1", facing="east", delay=0),
        Block(2, 0, 0, "chain", 'titleraw @a actionbar {"rawtext":[{"text":"demo"}]}', facing="east", delay=0),
    ]
    write_bdx(blocks, path)
    print("wrote", path)


def from_spec(data: dict, path: str) -> None:
    blocks = []
    for b in data["blocks"]:
        x, y, z = b.get("pos", [0, 0, 0])
        blocks.append(Block(
            int(x), int(y), int(z),
            b.get("type", b.get("mode", "chain")),
            b["command"],
            facing=b.get("facing", "east"),
            delay=int(b.get("delay", 0)),
            conditional=bool(b.get("conditional", False)),
            needs_redstone=bool(b.get("needs_redstone", False)),
            custom_name=b.get("custom_name", ""),
            last_output=b.get("last_output", ""),
            track_output=bool(b.get("track_output", False)),
        ))
    write_bdx(blocks, path, author=data.get("author", ""), sort_blocks=bool(data.get("sort_blocks", True)))
    print(f"wrote {path}: {len(blocks)} blocks")


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "--spec":
        if len(sys.argv) < 4:
            raise SystemExit("usage: bdxgen.py --spec <blocks.json> <out.bdx>")
        from_spec(json.load(open(sys.argv[2], encoding="utf-8")), sys.argv[3])
    else:
        demo(sys.argv[1] if len(sys.argv) > 1 else "demo.bdx")
