#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcworld_to_structure.py —— 把 .mcworld 里的命令方块区域导出成结构文件。

为什么需要它：
  网易版导入外部 .mcworld 经常失败，但**结构文件是官方支持的粘贴方式**——
  进游戏放一个结构方块，加载 .mcstructure，一键把整套命令方块贴到任意位置。
  绕开导入环节，成功率最高。

输出格式（基岩版 mcstructure）：
  {
    format_version: 1,
    size: [x, y, z],
    structure: {
      block_indices: [ [layer0...], [layer1...] ],
      entities: [],
      palette: { default: {
          block_palette: [ {name, states, version}, ... ],
          block_position_data: { "<index>": { block_entity_data: {...} } }
      } }
    },
    structure_world_origin: [x, y, z]
  }

用法：
  python mcworld_to_structure.py --input 世界.mcworld --out 指令区.mcstructure
  python mcworld_to_structure.py --input 世界.mcworld --out x.mcstructure --ext .mcstructure
  python mcworld_to_structure.py --input 世界.mcworld --out 局部.mcstructure \
         --from 0 -61 0 --to 15 -58 18
"""
import argparse
import importlib.util
import math
import os
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cbw = _load("build_cbworld")     # NBT 写入
vm = _load("verify_mcworld")     # 日志与 NBT 读取

TAG_BYTE, TAG_INT, TAG_LONG, TAG_STRING = 1, 3, 4, 8
TAG_LIST, TAG_COMPOUND = 9, 10

# 方块状态的 NBT 类型必须和游戏里注册的一致，不能一律写 INT。
#   `*_bit`           → BYTE（写 INT 会被判为非法状态，整个结构加载失败）
#   `facing_direction`→ INT （写 BYTE 会静默回落成 0 = 朝下，链直接断）
#   `dirt_type` 等枚举 → STRING
STATE_TYPES = {
    "conditional_bit": TAG_BYTE,
    "button_pressed_bit": TAG_BYTE,
    "infiniburn_bit": TAG_BYTE,
    "update_bit": TAG_BYTE,
    "explode_bit": TAG_BYTE,
    "facing_direction": TAG_INT,
    "direction": TAG_INT,
    "age": TAG_INT,
    "dirt_type": TAG_STRING,
    "sand_type": TAG_STRING,
    "stone_type": TAG_STRING,
    "wood_type": TAG_STRING,
}


def state_tag(key, value):
    """按状态名查正确的 NBT 类型；未知状态按值的 Python 类型兜底。"""
    if key in STATE_TYPES:
        return STATE_TYPES[key]
    return TAG_INT if isinstance(value, int) else TAG_STRING
BLOCK_VERSION = 0x01150100


# ---------------------------------------------------------------- 读取世界
def read_world(path):
    """返回 (blocks, entities, origin_hint)。blocks: {(x,y,z): (name, states)}"""
    z = zipfile.ZipFile(path)
    items = []
    for n in [x for x in z.namelist() if x.startswith("db/") and x.endswith(".log")]:
        payloads, _ = vm.parse_log(z.read(n))
        for pl in payloads:
            seq, cnt = struct.unpack("<QI", pl[:12]); o = 12
            for _ in range(cnt):
                t = pl[o]; o += 1
                kl, o = vm.rdvarint(pl, o)
                k = pl[o:o + kl]; o += kl
                if t == 0:
                    continue
                vl, o = vm.rdvarint(pl, o)
                items.append((k, pl[o:o + vl]))

    by_chunk = {}
    for k, v in items:
        cx, cz = struct.unpack("<ii", k[:8])
        node = by_chunk.setdefault((cx, cz), {"sub": {}, "ents": b""})
        if k[8] == 0x2f:
            node["sub"][struct.unpack("<b", k[9:10])[0]] = v
        elif k[8] == 0x31:
            node["ents"] = v

    blocks, entities = {}, {}
    for (cx, cz), node in by_chunk.items():
        for sy, sub in node["sub"].items():
            if len(sub) < 4:
                continue
            if sub[0] == 0x78:
                import zlib
                try:
                    sub = zlib.decompress(sub)
                except Exception:
                    continue
            bits = sub[3] >> 1
            if bits == 0:
                continue
            bpw = 32 // bits
            words = math.ceil(4096 / bpw)
            raw = struct.unpack("<" + "I" * words, sub[4:4 + words * 4])
            o = 4 + words * 4
            pc = struct.unpack("<I", sub[o:o + 4])[0]; o += 4
            pal = []
            for _ in range(pc):
                _, _, p, o = vm.rnbt(sub, o)
                pal.append(p)
            for x in range(16):
                for zz in range(16):
                    for yy in range(16):
                        slot = (x << 8) | (zz << 4) | yy
                        idx = (raw[slot // bpw] >> ((slot % bpw) * bits)) & ((1 << bits) - 1)
                        if idx >= len(pal):
                            continue
                        p = pal[idx]
                        name = p["name"][1]
                        if name == "minecraft:air":
                            continue
                        states = {k2: v2[1] for k2, v2 in p.get("states", (0, {}))[1].items()}
                        blocks[(cx * 16 + x, sy * 16 + yy, cz * 16 + zz)] = (name, states)

        v = node["ents"]; o2 = 0
        while o2 < len(v):
            _, _, e, o2 = vm.rnbt(v, o2)
            # 命令方块 + 箱子 / 告示牌 / 其它容器都要带走：
            # 说明区（注释物品、注释文字）全靠这些方块实体，丢了就只剩空箱子
            entities[(e["x"][1], e["y"][1], e["z"][1])] = e
    return blocks, entities


# ---------------------------------------------------------------- 写结构
def _sanitize(d):
    """把读取器解析出的 NBT（列表是普通数组）转成写入器要的 (元素类型, 数组)。"""
    out = {}
    for k, (t, v) in d.items():
        if t == TAG_LIST:
            if not v:
                out[k] = (TAG_LIST, (TAG_STRING, []))
            else:
                first = v[0]
                et = (TAG_COMPOUND if isinstance(first, dict)
                      else TAG_INT if isinstance(first, int) else TAG_STRING)
                items = [(_sanitize(x) if et == TAG_COMPOUND else x) for x in v]
                out[k] = (TAG_LIST, (et, items))
        elif t == TAG_COMPOUND:
            out[k] = (TAG_COMPOUND, _sanitize(v))
        else:
            out[k] = (t, v)
    return out


def build_structure(blocks, entities, origin, size):
    ox, oy, oz = origin
    sx, sy, sz = size

    palette, pal_index = [], {}
    indices = []
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                pos = (ox + x, oy + y, oz + z)
                if pos not in blocks:
                    indices.append(-1)
                    continue
                name, states = blocks[pos]
                key = (name, tuple(sorted(states.items())))
                if key not in pal_index:
                    pal_index[key] = len(palette)
                    palette.append(key)
                indices.append(pal_index[key])

    # block_position_data：方块实体按索引挂到对应格子上（命令方块 / 箱子 / 告示牌）
    pos_data = {}
    for (x, y, z), ent in entities.items():
        lx, ly, lz = x - ox, y - oy, z - oz
        if not (0 <= lx < sx and 0 <= ly < sy and 0 <= lz < sz):
            continue
        if (x, y, z) not in blocks:
            continue
        idx = lx * sy * sz + ly * sz + lz
        data = {k: v for k, v in ent.items() if k not in ("x", "y", "z")}
        data["x"] = (TAG_INT, 0)
        data["y"] = (TAG_INT, 0)
        data["z"] = (TAG_INT, 0)
        pos_data[str(idx)] = {"block_entity_data": (TAG_COMPOUND, _sanitize(data))}

    block_palette = []
    for name, states in palette:
        block_palette.append({
            "name": (TAG_STRING, name),
            "states": (TAG_COMPOUND, {k: (state_tag(k, v), v) for k, v in states}),
            "version": (TAG_INT, BLOCK_VERSION),
        })

    default = {
        "block_palette": (TAG_LIST, (TAG_COMPOUND, block_palette)),
        "block_position_data": (TAG_COMPOUND, {k: (TAG_COMPOUND, v) for k, v in pos_data.items()}),
    }
    structure = {
        "block_indices": (TAG_LIST, (TAG_LIST, [
            (TAG_INT, indices),
            (TAG_INT, [-1] * (sx * sy * sz)),
        ])),
        "entities": (TAG_LIST, (TAG_COMPOUND, [])),
        "palette": (TAG_COMPOUND, {"default": (TAG_COMPOUND, default)}),
    }
    root = {
        "format_version": (TAG_INT, 1),
        "size": (TAG_LIST, (TAG_INT, [sx, sy, sz])),
        "structure": (TAG_COMPOUND, structure),
        "structure_world_origin": (TAG_LIST, (TAG_INT, [ox, oy, oz])),
    }
    return cbw.nbt_compound(root, named=False)


def bounds(blocks):
    xs = [p[0] for p in blocks]; ys = [p[1] for p in blocks]; zs = [p[2] for p in blocks]
    return (min(xs), min(ys), min(zs)), (max(xs) - min(xs) + 1,
                                         max(ys) - min(ys) + 1,
                                         max(zs) - min(zs) + 1)


def main():
    ap = argparse.ArgumentParser(description="把 .mcworld 导出为结构文件")
    ap.add_argument("--input", required=True, help="源 .mcworld")
    ap.add_argument("--out", required=True, help="输出文件（.mcstructure）")
    ap.add_argument("--from", dest="frm", nargs=3, type=int, help="裁剪起点 x y z")
    ap.add_argument("--to", dest="to", nargs=3, type=int, help="裁剪终点 x y z（含端点）")
    ap.add_argument("--gzip", action="store_true", help="gzip 压缩整个文件（部分工具需要）")
    ap.add_argument("--header", action="store_true",
                    help="已废弃。历史版本在 NBT 前加过 8 字节头（int32 10 + int32 长度），"
                         "实测会让游戏判定文件损坏。保留该开关只为兼容旧命令，不再写入任何字节")
    args = ap.parse_args()
    if args.header:
        print("[提示] --header 已废弃：8 字节头会让结构方块判损坏，已忽略")
    args = ap.parse_args()

    blocks, entities = read_world(args.input)
    if not blocks:
        sys.exit("[错误] 世界里没有方块（可能是纯空气或解析失败）")
    print(f"读到方块 {len(blocks)} 个，命令方块实体 {len(entities)} 个")

    if args.frm and args.to:
        (x1, y1, z1), (x2, y2, z2) = args.frm, args.to
        lo = (min(x1, x2), min(y1, y2), min(z1, z2))
        size = (abs(x2 - x1) + 1, abs(y2 - y1) + 1, abs(z2 - z1) + 1)
    else:
        lo, size = bounds(blocks)
    print(f"区域 起点 {lo} 尺寸 {size}")

    data = build_structure(blocks, entities, lo, size)
    if args.gzip:
        import gzip
        data = gzip.compress(data, mtime=0)
    with open(args.out, "wb") as f:
        f.write(data)
    print(f"[完成] {args.out}（{len(data)} 字节）")
    print("        游戏内：放结构方块 → 加载 → 选这个文件 → 粘贴")


if __name__ == "__main__":
    main()
