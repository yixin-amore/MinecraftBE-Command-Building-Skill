#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_props.py —— 检查世界里的「说明区」：箱子物品 NBT + 告示牌文字

`verify_mcworld.py` 只认命令方块，其它方块实体一律跳过。这个脚本专门看那些
被跳过的东西：

  · 箱子：坐标对不对、物品数量、每件物品的 Name / Count / Damage / 显示名 / Lore 行数
  · 告示牌：FrontText 的每一行、颜色值
  · 坐标与方块是否对得上（实体在 (x,y,z)，那一格必须是 chest / *_sign）

用法：
  python check_props.py 世界.mcworld
  python check_props.py 世界.mcstructure      # 结构文件也行
"""
import io
import json
import math
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_mcworld as V

OK, BAD = "\u2713", "\u2717"


def read_world(path):
    """返回 (grid, block_entities)。grid: {(x,y,z): 方块名}"""
    zf = zipfile.ZipFile(path)
    logs = [n for n in zf.namelist() if n.startswith("db/") and n.endswith(".log")]
    items = []
    for n in logs:
        payloads, _ = V.parse_log(zf.read(n))
        for pl in payloads:
            _, cnt = struct.unpack("<QI", pl[:12])
            o = 12
            for _ in range(cnt):
                tt = pl[o]; o += 1
                kl, o = V.rdvarint(pl, o); k = pl[o:o + kl]; o += kl
                if tt == 0:
                    continue
                vl, o = V.rdvarint(pl, o); v = pl[o:o + vl]; o += vl
                items.append((k, v))

    by_chunk = {}
    for k, v in items:
        cx, cz = struct.unpack("<ii", k[:8])
        node = by_chunk.setdefault((cx, cz), {"sub": {}, "ents": b""})
        if k[8] == 0x2f:
            node["sub"][struct.unpack("<b", k[9:10])[0]] = v
        elif k[8] == 0x31:
            node["ents"] = v

    grid, ents = {}, []
    for (cx, cz), node in sorted(by_chunk.items()):
        for y, sub in sorted(node["sub"].items()):
            if len(sub) < 4:
                continue
            if sub[0] == 0x78:
                import zlib
                sub = zlib.decompress(sub)
            bits = sub[3] >> 1
            if bits == 0:
                continue
            bpw = 32 // bits
            words_n = math.ceil(4096 / bpw)
            words = struct.unpack("<" + "I" * words_n, sub[4:4 + words_n * 4])
            o2 = 4 + words_n * 4
            pc = struct.unpack("<I", sub[o2:o2 + 4])[0]; o2 += 4
            pal = []
            for _ in range(pc):
                _, _, p, o2 = V.rnbt(sub, o2)
                pal.append(p["name"][1])
            for x in range(16):
                for zz in range(16):
                    for yy in range(16):
                        slot = (x << 8) | (zz << 4) | yy
                        idx = (words[slot // bpw] >> ((slot % bpw) * bits)) & ((1 << bits) - 1)
                        if idx < len(pal):
                            grid[(cx * 16 + x, y * 16 + yy, cz * 16 + zz)] = pal[idx]

        v = node["ents"]; o = 0
        while o < len(v):
            _, _, e, o = V.rnbt(v, o)
            ents.append(e)
    return grid, ents


def sval(e, key, default=None):
    """取 NBT 值（(tag, value) 元组）。"""
    return e[key][1] if key in e else default


def show_item(it, i):
    name = sval(it, "Name", "?")
    cnt = sval(it, "Count", 0)
    dmg = sval(it, "Damage", 0)
    slot = sval(it, "Slot", None)
    tag = it.get("tag", (0, {}))[1]
    disp = tag.get("display", (0, {}))[1] if "display" in tag else {}
    dn = disp.get("Name", (0, ""))[1] if "Name" in disp else ""
    lore = disp.get("Lore", (0, []))[1] if "Lore" in disp else []
    unb = tag.get("Unbreakable", (0, 0))[1] if "Unbreakable" in tag else 0
    print("    %2d. %-28s ×%-2d data=%-2d slot=%-3s 不可破坏=%d"
          % (i + 1, name.replace("minecraft:", ""), cnt, dmg,
             "-" if slot is None else slot, unb))
    if dn:
        print("        名: %s" % dn)
    for ln in lore:
        print("        述: %s" % ln)
    # 除 display / Unbreakable 之外的 tag 键全部打出来（饰品纹饰、自定义数据等）
    known = ("display", "Unbreakable")
    extra = [(k, v) for k, v in tag.items() if k not in known]
    if extra:
        print("        其他 NBT: %s" % ", ".join(
            "%s=%r" % (k, v[1] if not isinstance(v[1], list) else v[1]) for k, v in extra))


def read_structure(path):
    """读 .mcstructure：返回 (grid, block_entities)。

    结构文件的方块实体挂在 `structure.palette.default.block_position_data.<索引>`
    的 `block_entity_data` 下，索引 = x*sizeY*sizeZ + y*sizeZ + z。
    """
    raw = io.open(path, "rb").read()
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
    # 历史版本可能带 8 字节头（int32 10 + int32 长度），自动跳过
    off = 0
    if len(raw) > 9 and raw[0] == 10 and struct.unpack("<I", raw[1:5])[0] == 0 and \
            struct.unpack("<I", raw[5:9])[0] == len(raw) - 8:
        off = 8
    _, _, root, _ = V.rnbt(raw, off)

    size = root["size"][1]
    sx, sy, sz = size
    st = root["structure"][1]
    default = st["palette"][1]["default"][1]
    pal = []
    for p in default["block_palette"][1]:
        pal.append((p["name"][1],
                    {k: v[1] for k, v in p.get("states", (0, {}))[1].items()}))
    idxs = st["block_indices"][1][0]

    grid = {}
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                i = x * sy * sz + y * sz + z
                if i >= len(idxs):
                    continue
                pi = idxs[i]
                if pi < 0 or pi >= len(pal):
                    continue
                grid[(x, y, z)] = pal[pi][0]

    ents = []
    for key, (t, v) in default.get("block_position_data", (0, {}))[1].items():
        e = v["block_entity_data"][1]
        idx = int(key)
        x = idx // (sy * sz)
        y = (idx // sz) % sy
        z = idx % sz
        e["x"] = (TAG_INT, x); e["y"] = (TAG_INT, y); e["z"] = (TAG_INT, z)
        ents.append(e)
    return grid, ents


TAG_INT = 3


def main():
    if len(sys.argv) < 2:
        print("用法：python check_props.py <世界.mcworld | 结构.mcstructure>")
        return 2
    path = sys.argv[1]
    if not os.path.exists(path):
        print("文件不存在：%s" % path)
        return 2

    if path.lower().endswith(".mcstructure"):
        grid, ents = read_structure(path)
        total = len(ents)
    else:
        grid, ents = read_world(path)
        total = len(ents)
    props = [e for e in ents if sval(e, "id") != "CommandBlock"]
    print("方块实体 %d 个，其中非命令方块 %d 个\n" % (total, len(props)))
    if not props:
        print("（没有说明区。想让世界自带说明，给 spec 加 props，见 SKILL.md 第 98 章）")
        return 0

    bad = 0
    for e in sorted(props, key=lambda e: (sval(e, "z", 0), sval(e, "x", 0))):
        eid = sval(e, "id", "?")
        x, y, z = sval(e, "x", 0), sval(e, "y", 0), sval(e, "z", 0)
        blk = grid.get((x, y, z), "?")
        print("· %s @ (%d,%d,%d)  方块=%s" % (eid, x, y, z, blk.replace("minecraft:", "")))
        if eid == "Chest" and "chest" not in blk:
            print("  %s 坐标上没有箱子方块" % BAD); bad += 1
        if eid == "Sign" and "sign" not in blk:
            print("  %s 坐标上没有告示牌方块" % BAD); bad += 1

        if eid == "Chest":
            cn = sval(e, "CustomName", "")
            if cn:
                print("  自定义名: %s" % cn)
            items = e.get("Items", (0, []))[1]
            print("  物品 %d 件" % len(items))
            for i, it in enumerate(items):
                show_item(it, i)
                if not it.get("tag"):
                    print("        %s 这件没有 NBT（不会被注释）" % BAD); bad += 1
        elif eid == "Sign":
            for side in ("FrontText", "BackText"):
                txt = e.get(side, (0, {}))[1].get("Text", (0, ""))[1]
                if not txt:
                    continue
                print("  %s:" % side)
                for ln in txt.split("\n"):
                    print("    | %s" % ln)
        print()

    print("结论：" + ("有问题，看上面 %s 的行" % BAD if bad else OK + " 说明区正常"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
