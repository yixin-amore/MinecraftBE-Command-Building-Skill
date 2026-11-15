#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_compat.py —— 兼容版：拿一份**真实的**导出存档当底座，只把新区块追加进去。

为什么需要它：
  自己搭 LevelDB 脚手架（CURRENT/MANIFEST/LOG）在个别客户端上会被判为无效，
  导致"导入失败"。这个脚本保留底座的全部原始字节，只往它的日志尾部追加记录，
  最大限度排除兼容性问题。

用法：
  python build_compat.py --base <真实存档.mcworld> --name "世界名" \
         --spawn 8 -60 7 --out 输出.mcworld

注意：
  · 新世界的出生点会指向我们的平台，底座原有的内容留在远处（不影响使用）
  · 区块坐标与底座冲突时会覆盖同名键，建议选空白区域（默认 0,0 起）
"""
import argparse
import importlib.util
import os
import struct
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cbw", os.path.join(HERE, "build_cbworld.py"))
cbw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cbw)

BLOCK = 32768


def parse_log(data):
    out, frag = [], None
    for bs in range(0, len(data), BLOCK):
        be = min(bs + BLOCK, len(data)); p = bs
        while p + 7 <= be:
            crc, ln, t = struct.unpack("<IHB", data[p:p + 7])
            if t == 0 or p + 7 + ln > be:
                break
            pl = data[p + 7:p + 7 + ln]; p += 7 + ln
            if t == 1: out.append(pl)
            elif t == 2: frag = pl
            elif t == 3: frag = (frag or b"") + pl
            elif t == 4: out.append((frag or b"") + pl); frag = None
    return out


def append_records(existing, pairs):
    """在已有日志末尾追加记录，遵守块对齐与分片规则。"""
    out = bytearray(existing)

    def emit(body):
        pos, first = 0, True
        while pos < len(body):
            avail = BLOCK - (len(out) % BLOCK)
            if avail < 7:
                out.extend(b"\x00" * avail); avail = BLOCK
            take = min(len(body) - pos, avail - 7)
            last = (pos + take) == len(body)
            typ = 1 if (first and last) else (2 if first else (4 if last else 3))
            chunk = body[pos:pos + take]
            out.extend(struct.pack("<IHB", cbw._mask(cbw.crc32c(bytes([typ]) + chunk)), take, typ))
            out.extend(chunk)
            pos += take
            first = False

    for seq, key, val in pairs:
        body = (struct.pack("<QI", seq, 1) + bytes([1]) + cbw._varint(len(key)) + key
                + cbw._varint(len(val)) + val)
        emit(body)
    return bytes(out)


def main():
    ap = argparse.ArgumentParser(description="在真实存档上追加区块（兼容版）")
    ap.add_argument("--base", required=True, help="真实存档 .mcworld")
    ap.add_argument("--name", default="指令世界")
    ap.add_argument("--spawn", nargs=3, type=int, default=[8, -60, 7], metavar=("X", "Y", "Z"))
    ap.add_argument("--gametype", default="creative",
                    choices=["survival", "creative", "adventure", "spectator"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    gt = {"survival": 0, "creative": 1, "adventure": 2, "spectator": 3}[args.gametype]
    src = zipfile.ZipFile(args.base)
    log = src.read("db/000001.log")
    max_seq = 0
    for pl in parse_log(log):
        seq, _ = struct.unpack("<QI", pl[:12])
        max_seq = max(max_seq, seq)
    print(f"底座日志 {len(log)} 字节，最大序号 {max_seq}")

    blocks, entities = cbw.build_scene(cbw.demo_system())
    chunks = {}
    for (x, y, z), key in blocks.items():
        chunks.setdefault((x // 16, z // 16), {}).setdefault("blocks", {})[(x % 16, y, z % 16)] = key
    for (x, z), val in entities.items():
        chunks.setdefault((x // 16, z // 16), {}).setdefault("ents", {})[(x % 16, z % 16)] = val

    pairs, seq = [], max_seq
    for (cx, cz) in sorted(chunks):
        c = chunks[(cx, cz)]
        sub = cbw.encode_subchunk(-4, c.get("blocks", {}))
        kb = struct.pack("<ii", cx, cz)
        for tag, val in ((b"\x2c", b"\x28"), (b"\x2b", b"\x00" * 632),
                         (b"\x36", struct.pack("<i", 2)),
                         (b"\x2f" + struct.pack("<b", -4), sub)):
            seq += 1
            pairs.append((seq, kb + tag, val))
        body = b"".join(cbw.cb_entity(cx * 16 + lx, -60, cz * 16 + lz, cmd, auto, cond)
                        for (lx, lz), (cmd, auto, cond) in sorted(c.get("ents", {}).items()))
        if body:
            seq += 1
            pairs.append((seq, kb + b"\x31", body))

    new_log = append_records(log, pairs)
    print(f"追加 {len(pairs)} 条记录 → 日志 {len(new_log)} 字节")

    raw = src.read("level.dat")
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw); ver = 10
    else:
        ver = struct.unpack("<II", raw[:8])[0]
    body = raw[8:] if raw[:2] != b"\x1f\x8b" else raw
    root, _ = cbw._parse_value(body, 3, 10)
    root["LevelName"] = (cbw.TAG_STRING, args.name)
    root["SpawnX"] = (cbw.TAG_INT, args.spawn[0])
    root["SpawnY"] = (cbw.TAG_INT, args.spawn[1])
    root["SpawnZ"] = (cbw.TAG_INT, args.spawn[2])
    root["GameType"] = (cbw.TAG_INT, gt)
    root["commandsEnabled"] = (cbw.TAG_BYTE, 1)
    root["cheatsEnabled"] = (cbw.TAG_BYTE, 1)
    new_body = cbw.nbt_compound(root, named=False)
    level = struct.pack("<II", ver, len(new_body)) + new_body

    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in src.infolist():
            if item.filename == "level.dat":
                zf.writestr("level.dat", level)
            elif item.filename == "db/000001.log":
                zf.writestr("db/000001.log", new_log)
            else:
                zf.writestr(item.filename, src.read(item.filename))

    print(f"[完成] {args.out}")


if __name__ == "__main__":
    main()
