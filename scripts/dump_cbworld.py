#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dump_cbworld.py —— 从任意 .mcworld 里抽出所有命令方块（含方块实体 NBT），
输出成可读文本 / JSON，供学习别人的指令区用。

用法：
  python dump_cbworld.py 世界.mcworld                 # 摘要 + 命令清单
  python dump_cbworld.py 世界.mcworld --json out.json # 结构化导出
  python dump_cbworld.py 世界.mcworld --raw cmds.txt  # 纯命令文本（每行一条）

支持：db/*.log（写日志）+ db/*.ldb（SST，含 snappy 压缩块）
"""
import argparse
import json
import math
import os
import struct
import sys
import zipfile

BLOCK = 32768

# ---------------------------------------------------------------- CRC32C
_POLY = 0x82F63B78
_T = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ _POLY if _c & 1 else _c >> 1
    _T.append(_c)


def crc32c(d):
    c = 0xFFFFFFFF
    for b in d:
        c = (c >> 8) ^ _T[(c ^ b) & 0xFF]
    return c ^ 0xFFFFFFFF


def _mask(c):
    return (((c >> 15) | (c << 17)) + 0xA282EAD8) & 0xFFFFFFFF


def rdvarint(b, o):
    r = s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s; s += 7
        if not x & 0x80:
            return r, o


# ---------------------------------------------------------------- snappy
def snappy_decompress(b):
    n, o = rdvarint(b, 0)
    out = bytearray()
    L = len(b)
    while o < L:
        tag = b[o]; o += 1
        t = tag & 3
        if t == 0:                                   # literal
            ln = tag >> 2
            if ln < 60:
                ln += 1
            else:
                k = ln - 59
                ln = int.from_bytes(b[o:o + k], "little") + 1
                o += k
            out += b[o:o + ln]; o += ln
        else:
            if t == 1:
                ln = ((tag >> 2) & 0x7) + 4
                off = ((tag >> 5) << 8) | b[o]; o += 1
            elif t == 2:
                ln = (tag >> 2) + 1
                off = struct.unpack("<H", b[o:o + 2])[0]; o += 2
            else:
                ln = (tag >> 2) + 1
                off = struct.unpack("<I", b[o:o + 4])[0]; o += 4
            start = len(out) - off
            for i in range(ln):
                out.append(out[start + i])
    return bytes(out)


# ---------------------------------------------------------------- NBT
def rnbt(b, o):
    t = b[o]; o += 1
    if t == 0:
        return 0, "", None, o
    nl = struct.unpack("<H", b[o:o + 2])[0]; o += 2
    nm = b[o:o + nl].decode("utf-8", "replace"); o += nl
    v, o = rp(b, o, t)
    return t, nm, v, o


def rp(b, o, t):
    if t == 1: return struct.unpack("<b", b[o:o + 1])[0], o + 1
    if t == 2: return struct.unpack("<h", b[o:o + 2])[0], o + 2
    if t == 3: return struct.unpack("<i", b[o:o + 4])[0], o + 4
    if t == 4: return struct.unpack("<q", b[o:o + 8])[0], o + 8
    if t == 5: return struct.unpack("<f", b[o:o + 4])[0], o + 4
    if t == 6: return struct.unpack("<d", b[o:o + 8])[0], o + 8
    if t == 7:
        n = struct.unpack("<i", b[o:o + 4])[0]; return list(b[o + 4:o + 4 + n]), o + 4 + n
    if t == 8:
        n = struct.unpack("<H", b[o:o + 2])[0]
        return b[o + 2:o + 2 + n].decode("utf-8", "replace"), o + 2 + n
    if t == 9:
        et = b[o]; n = struct.unpack("<i", b[o + 1:o + 5])[0]; o += 5
        a = []
        for _ in range(n):
            v, o = rp(b, o, et); a.append(v)
        return a, o
    if t == 10:
        d = {}
        while True:
            tt = b[o]
            if tt == 0:
                return d, o + 1
            t2, nm, v, o = rnbt(b, o)
            d[nm] = (t2, v)
    if t == 11:
        n = struct.unpack("<i", b[o:o + 4])[0]
        return list(struct.unpack("<" + "i" * n, b[o + 4:o + 4 + 4 * n])), o + 4 + 4 * n
    raise ValueError("tag %d" % t)


# ---------------------------------------------------------------- .log
def parse_log(data):
    out, frag = [], None
    for bs in range(0, len(data), BLOCK):
        be = min(bs + BLOCK, len(data)); p = bs
        while p + 7 <= be:
            crc, ln, t = struct.unpack("<IHB", data[p:p + 7])
            if t == 0 or p + 7 + ln > be:
                break
            pl = data[p + 7:p + 7 + ln]
            p += 7 + ln
            if t == 1:
                out.append(pl)
            elif t == 2:
                frag = pl
            elif t == 3:
                frag = (frag or b"") + pl
            elif t == 4:
                out.append((frag or b"") + pl); frag = None
    return out


# ---------------------------------------------------------------- .ldb (SST)
def sst_block(data, off, size):
    """size 只算内容，不含 1 字节压缩类型 + 4 字节 CRC。"""
    body = data[off:off + size]
    if not body:
        return b""
    ctype = data[off + size]
    if ctype == 1:
        body = snappy_decompress(body)
    elif ctype == 2:
        import zlib
        body = zlib.decompress(body)
    elif ctype == 4:                                  # Bedrock：raw deflate
        import zlib
        body = zlib.decompress(body, -15)
    return body                                       # 含尾部 restart 数组


def sst_entries(block):
    n = struct.unpack("<I", block[-4:])[0]
    rest = struct.unpack("<" + "I" * n, block[-4 - 4 * n:-4])
    out, o, key = [], 0, b""
    limit = len(block) - 4 - 4 * n
    while o < limit:
        shared, o = rdvarint(block, o)
        nonshared, o = rdvarint(block, o)
        vlen, o = rdvarint(block, o)
        key = key[:shared] + block[o:o + nonshared]; o += nonshared
        val = block[o:o + vlen]; o += vlen
        out.append((key, val))
    return out


def parse_ldb(data):
    """返回 [(key, value)]。"""
    if len(data) < 48:
        return []
    footer = data[-48:]
    if struct.unpack("<Q", footer[-8:])[0] != 0xdb4775248b80fb57:
        return []
    o = 0
    mo, o = rdvarint(footer, o)          # metaindex offset
    ms, o = rdvarint(footer, o)          # metaindex size
    io_, o = rdvarint(footer, o)         # index offset
    isz, o = rdvarint(footer, o)         # index size
    idx = sst_entries(sst_block(data, io_, isz))
    out = []
    for _k, v in idx:
        off, p = rdvarint(v, 0)
        size, p = rdvarint(v, p)
        out.extend(sst_entries(sst_block(data, off, size)))
    return out


# ---------------------------------------------------------------- 汇总
def collect(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    kv = {}
    for n in sorted(x for x in names if x.startswith("db/") and x.endswith(".ldb")):
        for k, v in parse_ldb(z.read(n)):
            kv[k] = v
    for n in sorted(x for x in names if x.startswith("db/") and x.endswith(".log")):
        for pl in parse_log(z.read(n)):
            if len(pl) < 12:
                continue
            seq, cnt = struct.unpack("<QI", pl[:12]); o = 12
            for _ in range(cnt):
                tt = pl[o]; o += 1
                kl, o = rdvarint(pl, o); k = pl[o:o + kl]; o += kl
                if tt == 0:
                    kv.pop(k, None); continue
                vl, o = rdvarint(pl, o); v = pl[o:o + vl]; o += vl
                kv[k] = v
    return kv


def subchunk_blocks(v):
    """返回 {(x,y,z): (name, states)} 局部坐标。"""
    if len(v) < 4 or v[0] == 0x78:
        import zlib
        try:
            v = zlib.decompress(v)
        except Exception:
            return {}
    if len(v) < 5:
        return {}
    ver, layers, yidx = v[0], v[1], struct.unpack("<b", v[2:3])[0]
    bits = v[3] >> 1
    if bits == 0:
        return {}
    bpw = 32 // bits
    words = math.ceil(4096 / bpw)
    idx = struct.unpack("<" + "I" * words, v[4:4 + words * 4])
    o = 4 + words * 4
    pc = struct.unpack("<I", v[o:o + 4])[0]; o += 4
    pal = []
    for _ in range(pc):
        _, _, p, o = rnbt(v, o); pal.append(p)
    mask = (1 << bits) - 1
    out = {}
    for i in range(4096):
        w = idx[i // bpw]
        pid = (w >> ((i % bpw) * bits)) & mask
        if pid >= len(pal):
            continue
        p = pal[pid]
        nm = p.get("name", (8, ""))[1] if isinstance(p, dict) else str(p)
        if "command_block" in nm:
            st = {}
            if isinstance(p, dict) and "states" in p:
                for k2, (t2, v2) in p["states"][1].items():
                    st[k2] = v2
            # 槽位 = x<<8 | z<<4 | y（Bedrock 版本 9 的 X-major 布局）
            out[(i >> 8, yidx * 16 + (i & 15), (i >> 4) & 15)] = (nm, st)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json")
    ap.add_argument("--raw")
    args = ap.parse_args()

    kv = collect(args.path)
    by_chunk, ents = {}, {}
    for k, v in kv.items():
        if len(k) < 9:
            continue
        cx, cz = struct.unpack("<ii", k[:8])
        node = by_chunk.setdefault((cx, cz), {})
        if k[8] == 0x2F:
            node[struct.unpack("<b", k[9:10])[0]] = v
        elif k[8] == 0x31:
            ents[(cx, cz)] = v

    blocks = {}
    for (cx, cz), subs in by_chunk.items():
        for y, v in subs.items():
            for (lx, wy, lz), (nm, st) in subchunk_blocks(v).items():
                blocks[(cx * 16 + lx, wy, cz * 16 + lz)] = (nm, st)

    records = []
    for (cx, cz), raw in ents.items():
        if len(raw) < 4 or raw[0] == 0x78:
            import zlib
            try:
                raw = zlib.decompress(raw)
            except Exception:
                continue
        o = 0
        while o < len(raw):
            try:
                t, nm, d, o = rnbt(raw, o)
            except Exception:
                break
            if t != 10:
                continue
            if "x" not in d:
                continue
            x = d["x"][1]; y = d["y"][1]; z = d["z"][1]
            rec = {
                "x": x, "y": y, "z": z,
                "id": d.get("id", (8, ""))[1],
                "command": d.get("Command", (8, ""))[1],
                "auto": d.get("auto", (1, 0))[1],
                "cond": d.get("conditionalMode", (1, 0))[1],
                "track": d.get("TrackOutput", (1, 0))[1],
                "last": d.get("LastOutput", (8, ""))[1],
                "name": d.get("CustomName", (8, ""))[1],
                "tick": d.get("TickDelay", (3, 0))[1],
            }
            b = blocks.get((x, y, z))
            rec["block"] = b[0] if b else "?"
            rec["fd"] = b[1].get("facing_direction") if b else None
            records.append(rec)

    records.sort(key=lambda r: (r["y"], r["z"], r["x"]))
    print("=== %s ===" % os.path.basename(args.path))
    print("命令方块实体 %d 个" % len(records))
    from collections import Counter
    print("方块类型：", dict(Counter(r["block"].replace("minecraft:", "") for r in records)))
    print("朝向分布：", dict(Counter(r["fd"] for r in records)))
    print("条件位：", dict(Counter(r["cond"] for r in records)),
          " auto：", dict(Counter(r["auto"] for r in records)),
          " TrackOutput：", dict(Counter(r["track"] for r in records)))
    ys = sorted(set(r["y"] for r in records))
    print("y 层：", ys)
    print("坐标范围：x %d..%d  z %d..%d" % (
        min(r["x"] for r in records), max(r["x"] for r in records),
        min(r["z"] for r in records), max(r["z"] for r in records)))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=1)
        print("-> %s" % args.json)
    if args.raw:
        with open(args.raw, "w", encoding="utf-8") as f:
            for r in records:
                f.write("%s\n" % r["command"])
        print("-> %s" % args.raw)


if __name__ == "__main__":
    main()
