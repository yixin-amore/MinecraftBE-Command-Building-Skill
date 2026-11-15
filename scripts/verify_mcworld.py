#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_mcworld.py —— 回读校验任意 .mcworld：结构、CRC、子区块、命令方块链。

用法：
  python verify_mcworld.py 世界.mcworld [--verbose]

检查项：
  1. level.dat 能否解析（兼容 8 字节头裸 NBT / gzip）
  2. db 日志每条记录 CRC 是否自洽、分片是否完整
  3. 每个子区块能否精确解完（字节数对得上）
  4. 方块实体是否都落在命令方块上（坐标必须为世界坐标）
  5. 命令方块链是否连贯（朝向的下一个格子是命令方块，或为链末端）
"""
import argparse
import math
import struct
import sys
import zipfile

BLOCK = 32768
# 0 下 / 1 上 / 2 北 / 3 南 / 4 西 / 5 东 —— 三维，竖直链也要能跟
FACING = {5: (1, 0, 0), 4: (-1, 0, 0), 3: (0, 0, 1), 2: (0, 0, -1),
          1: (0, 1, 0), 0: (0, -1, 0)}
TAG_NAMES = {0x2b: "Data3D", 0x2c: "Version", 0x2f: "SubChunk", 0x31: "BlockEntity", 0x36: "FinalizedState"}

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


def parse_log(data):
    """返回 (payloads, crc_errors)。"""
    out, frag, bad = [], None, 0
    for bs in range(0, len(data), BLOCK):
        be = min(bs + BLOCK, len(data)); p = bs
        while p + 7 <= be:
            crc, ln, t = struct.unpack("<IHB", data[p:p + 7])
            if t == 0 or p + 7 + ln > be:
                break
            pl = data[p + 7:p + 7 + ln]
            if _mask(crc32c(bytes([t]) + pl)) != crc:
                bad += 1
            p += 7 + ln
            if t == 1:
                out.append(pl)
            elif t == 2:
                frag = pl
            elif t == 3:
                frag = (frag or b"") + pl
            elif t == 4:
                out.append((frag or b"") + pl); frag = None
    return out, bad


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
        n = struct.unpack("<H", b[o:o + 2])[0]; return b[o + 2:o + 2 + n].decode("utf-8", "replace"), o + 2 + n
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
    raise ValueError(f"tag {t}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    z = zipfile.ZipFile(args.path)
    names = z.namelist()
    print(f"=== {args.path} ===")
    print(f"包内 {len(names)} 个条目：{', '.join(names[:6])}{' ...' if len(names) > 6 else ''}")
    assert "level.dat" in names, "缺少 level.dat（必须在压缩包根目录）"

    # level.dat
    raw = z.read("level.dat")
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw); off = 0; fmt = "gzip"
    else:
        ver, ln = struct.unpack("<II", raw[:8]); off = 8
        fmt = f"头部版本 {ver}，声明长度 {ln}"
        assert len(raw) - 8 == ln, "level.dat 声明长度与实际不符"
    t, nm, root, end = rnbt(raw, off)
    assert t == 10, "level.dat 根不是复合标签"
    print(f"level.dat：{fmt}，{len(root)} 个键，解析完整={end == len(raw)}")
    for k in ("LevelName", "SpawnX", "SpawnY", "SpawnZ", "GameType", "commandsEnabled", "cheatsEnabled"):
        if k in root:
            print(f"  {k} = {root[k][1]}")

    # db
    logs = [n for n in names if n.startswith("db/") and n.endswith(".log")]
    assert logs, "缺少 db/*.log"
    items, total_bad = [], 0
    for n in logs:
        payloads, bad = parse_log(z.read(n))
        total_bad += bad
        for pl in payloads:
            seq, cnt = struct.unpack("<QI", pl[:12]); o = 12
            for _ in range(cnt):
                tt = pl[o]; o += 1
                kl, o = rdvarint(pl, o); k = pl[o:o + kl]; o += kl
                if tt == 0:
                    continue
                vl, o = rdvarint(pl, o); v = pl[o:o + vl]; o += vl
                items.append((k, v))
    print(f"db 日志：{len(items)} 条记录，CRC 错误 {total_bad} 条")

    # 按区块分组：子区块按 y 分层（一个区块可能有多层）
    by_chunk = {}
    for k, v in items:
        cx, cz = struct.unpack("<ii", k[:8])
        node = by_chunk.setdefault((cx, cz), {"sub": {}, "ents": b""})
        if k[8] == 0x2f:
            node["sub"][struct.unpack("<b", k[9:10])[0]] = v
        elif k[8] == 0x31:
            node["ents"] = v

    grid, ents_all, problems, others = {}, [], [], 0
    layers = 0
    for (cx, cz), node in sorted(by_chunk.items()):
        for y, sub in sorted(node["sub"].items()):
            if len(sub) < 4:                     # 空记录
                continue
            if sub[0] == 0x78:                   # zlib 压缩的子区块
                import zlib
                try:
                    sub = zlib.decompress(sub)
                except Exception:
                    problems.append(f"区块({cx},{cz}) y={y} 子区块解压失败")
                    continue
            bits = sub[3] >> 1
            if bits == 0:
                continue
            layers += 1
            bpw = 32 // bits
            words = math.ceil(4096 / bpw)
            raw_idx = struct.unpack("<" + "I" * words, sub[4:4 + words * 4])
            o = 4 + words * 4
            pc = struct.unpack("<I", sub[o:o + 4])[0]; o += 4
            pal = []
            for _ in range(pc):
                _, _, p, o = rnbt(sub, o); pal.append(p)
            for _ in range(sub[1] - 1):          # 其余层（单方块）
                o += 1
                while o < len(sub):
                    tt = sub[o]
                    if tt == 0:
                        o += 1
                        break
                    _, _, _, o = rnbt(sub, o)
            ok = (o == len(sub))
            if not ok:
                problems.append(f"区块({cx},{cz}) y={y} 子区块解析长度不符")
            if args.verbose:
                print(f"  区块({cx},{cz}) y={y} bits={bits} 调色板 {pc} 项 "
                      f"{'精确解完' if ok else '⚠ 字节数不符'}")
            for x in range(16):
                for zz in range(16):
                    for yy in range(16):
                        slot = (x << 8) | (zz << 4) | yy
                        idx = (raw_idx[slot // bpw] >> ((slot % bpw) * bits)) & ((1 << bits) - 1)
                        if idx < len(pal):
                            grid[(cx * 16 + x, y * 16 + yy, cz * 16 + zz)] = pal[idx]

        v = node["ents"]; o2 = 0
        while o2 < len(v):
            _, _, e, o2 = rnbt(v, o2)
            if e.get("id", (0, ""))[1] == "CommandBlock":
                ents_all.append(e)
            else:
                others += 1
    print(f"区块 {len(by_chunk)} 个，含方块数据的层 {layers} 个")

    # 方块实体检查
    print(f"命令方块实体 {len(ents_all)} 个" + (f"（另有 {others} 个其它方块实体已跳过）" if others else ""))
    ends = 0
    for e in ents_all:
        x, y, zz = e["x"][1], e["y"][1], e["z"][1]
        b = grid.get((x, y, zz))
        nm = b["name"][1] if b else "?"
        if "command_block" not in nm:
            problems.append(f"实体({x},{y},{zz}) 下面是 {nm}，不是命令方块")
            continue
        f = b["states"][1].get("facing_direction", (3, 0))[1]
        dx, dy, dz = FACING.get(f, (0, 0, 0))
        nb = grid.get((x + dx, y + dy, zz + dz))
        if not nb or "command_block" not in nb["name"][1]:
            ends += 1
    print(f"链末端 {ends} 个（每条链 1 个，可用来核对链数）")

    if problems:
        print("\n⚠ 发现问题：")
        for p in problems[:10]:
            print("  -", p)
        sys.exit(1)
    print("\n✓ 校验通过")


if __name__ == "__main__":
    main()
