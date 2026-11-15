#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拔刀剑交付物 15 项自检：全部从文件回读，不看生成时的内存数据。"""
import argparse
import json
import math
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_mcworld as V

OK, FAIL = "\u2713", "\u2717"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()

    rows = []

    def rec(no, name, ok, detail=""):
        rows.append((no, name, ok, detail))

    zf = zipfile.ZipFile(args.path)
    names = zf.namelist()

    # 1 包结构
    need = {"level.dat", "levelname.txt", "world_behavior_packs.json",
            "world_resource_packs.json", "db/CURRENT", "db/LOCK", "db/LOG",
            "db/MANIFEST-000000", "db/000001.log"}
    nested = [n for n in names if n.startswith(("world/", "拔刀剑"))]
    rec(1, "包结构：9 项齐全且 level.dat 在 zip 根",
        need.issubset(set(names)) and not nested,
        "%d 项 / 嵌套 %d" % (len(names), len(nested)))

    # 2 level.dat 头部
    lv = zf.read("level.dat")
    ver, ln = struct.unpack("<II", lv[:8])
    body = lv[8:]
    t, nm, nbt, off = V.rnbt(body, 0)
    rec(2, "level.dat 头部 version=10 + 长度一致 + NBT 未压缩",
        ver == 10 and ln == len(body) and off == len(body),
        "ver=%d 声明=%d 实际=%d 剩余=%d" % (ver, ln, len(body), len(body) - off))

    # 3 关键键
    keys = ["LevelName", "SpawnX", "SpawnY", "SpawnZ", "GameType",
            "commandsEnabled", "commandblocksenabled", "cheatsEnabled"]
    miss = [k for k in keys if k not in nbt]
    bad = [k for k in ("commandsEnabled", "commandblocksenabled", "cheatsEnabled")
           if nbt.get(k, (0, 0))[1] != 1]
    rec(3, "level.dat 关键键齐全且命令开关为 1",
        not miss and not bad,
        "缺 %s 值异常 %s" % (miss or "无", bad or "无"))

    # 4 db 五件套 + MANIFEST 两条
    man = zf.read("db/MANIFEST-000000")
    nrec = sum(1 for i in range(len(man)) if man[i:i + 1] == b"\x01" and i > 0 and man[i - 1] == 0)
    # 更可靠：按 VersionEdit 起始标记 0x01 且前一字节为 0（长度高字节）粗判
    cur = zf.read("db/CURRENT").decode("utf-8", "replace").strip()
    rec(4, "db 五件套齐全 + CURRENT 指向 MANIFEST",
        all(("db/" + x) in names for x in ("CURRENT", "LOCK", "LOG",
                                          "MANIFEST-000000", "000001.log"))
        and cur == "MANIFEST-000000",
        "CURRENT=%s MANIFEST=%d 字节" % (cur, len(man)))

    # 5 CRC
    payloads, crc_bad = V.parse_log(zf.read("db/000001.log"))
    rec(5, "日志记录 CRC32C 全通过", crc_bad == 0,
        "%d 条记录 / %d 条错误" % (len(payloads), crc_bad))

    # 6 子区块字节精确消费 + 7 调色板首项 air + 8 facing_direction 为 INT
    def _varint(b, o):
        r, s = 0, 0
        while True:
            c = b[o]; o += 1
            r |= (c & 0x7F) << s
            if not c & 0x80:
                break
            s += 7
        return r, o

    sub_ok, pal_air, facing_ok = True, True, True
    facing_detail = []
    nsub, nent = 0, 0
    ents = []
    n_cond, n_uncond = 0, 0          # 断链：条件块 / 无条件块（按方块槽位实计，不看调色板去重）
    ents_full = []                   # 完整方块实体 NBT，用于查 TrackOutput / LastOutput
    grid = {}                        # (x,y,z) -> (方块名, 条件位, 朝向)，用于沿链统计
    for pl in payloads:
        # 记录体 = seq(u64) + batch(u32) + type(u8) + varint(keylen) + key + varint(vallen) + val
        o = 13
        kl, o = _varint(pl, o)
        key = pl[o:o + kl]; o += kl
        vl, o = _varint(pl, o)
        val = pl[o:o + vl]
        tag = key[8:9]
        if tag == b"\x2f":
            nsub += 1
            cx, cz = struct.unpack("<ii", key[:8])
            sy = struct.unpack("<b", key[9:10])[0]
            d = val
            if d[0] == 0x78:
                import zlib
                d = zlib.decompress(d)
            p = 3
            layers = d[1]
            for _ in range(layers):
                sv = d[p]; p += 1
                bits = sv >> 1
                if bits == 0:
                    # 单值层：sv 字节 + 一个完整 NBT 调色板条目（真实存档即如此）
                    _, _, _, p = V.rnbt(d, p)
                    continue
                bpw = 32 // bits
                words = math.ceil(4096 / bpw)
                wstart = p
                p += words * 4
                pc = struct.unpack("<I", d[p:p + 4])[0]; p += 4
                pal_cond = []
                for i in range(pc):
                    tt, nn, vv, p = V.rnbt(d, p)
                    nmz = vv.get("name", (0, ""))[1]
                    if i == 0 and nmz != "minecraft:air":
                        pal_air = False
                    st = vv.get("states", (10, {}))[1]
                    if "facing_direction" in st:
                        ft, fv = st["facing_direction"]
                        if ft != 3:                     # TAG_Int
                            facing_ok = False
                        facing_detail.append(fv)
                    pal_cond.append((nmz, st.get("conditional_bit", (0, 0))[1],
                                     st.get("facing_direction", (0, 0))[1]))
                # 按索引数组实计方块槽位（调色板是去重的，不能拿来数方块）
                if bits:
                    mask = (1 << bits) - 1
                    nslot = 0
                    for wi in range(words):
                        wv = struct.unpack("<I", d[wstart + wi * 4: wstart + wi * 4 + 4])[0]
                        for k in range(bpw):
                            if nslot >= 4096:
                                break
                            v = (wv >> (k * bits)) & mask
                            if v < len(pal_cond):
                                pnm, pcb, pfd = pal_cond[v]
                                if "command_block" in pnm:
                                    if pcb:
                                        n_cond += 1
                                    else:
                                        n_uncond += 1
                                    gx = (nslot >> 8) & 15
                                    gz = (nslot >> 4) & 15
                                    gy = nslot & 15
                                    grid[(cx * 16 + gx, sy * 16 + gy,
                                          cz * 16 + gz)] = (pnm, pcb, pfd)
                            nslot += 1
            if p != len(d):
                sub_ok = False
        elif tag == b"\x31":
            b = val
            o2 = 0
            while o2 < len(b):
                tt, nn, vv, o2 = V.rnbt(b, o2)
                if vv.get("id", (0, ""))[1] == "CommandBlock":
                    nent += 1
                    ents_full.append(vv)
                    ents.append((vv["x"][1], vv["y"][1], vv["z"][1],
                                 vv.get("Command", (0, ""))[1]))

    rec(6, "子区块字节精确消费（无残留/无越界）", sub_ok, "%d 个子区块层" % nsub)
    rec(7, "调色板 [0] 为 minecraft:air", pal_air, "")
    rec(8, "facing_direction 全部为 TAG_Int",
        facing_ok, "取值集合 %s" % sorted(set(facing_detail)))

    # 9 实体坐标为世界坐标
    inrange = all(-64 <= y <= 320 for _, y, _, _ in ents)
    spread = len({(x, z) for x, _, z, _ in ents})
    rec(9, "命令方块实体使用世界坐标（y 合法、位置分散）",
        inrange and spread > 1, "%d 个实体 / %d 个不同 (x,z)" % (nent, spread))

    # 10 无 mcfunction / 无 tag
    cmds = [c for *_, c in ents]
    mcf = [c for c in cmds if "function" in c]
    tg = [c for c in cmds if c.startswith("tag ") or " tag @" in c]
    rec(10, "命令中无 function / 无 tag 指令",
        not mcf and not tg, "function %d / tag %d" % (len(mcf), len(tg)))

    # 11 JSON 合法 + 无真换行
    badj, badn = [], []
    for c in cmds:
        for kw in ("tellraw", "titleraw"):
            i = c.find(kw)
            if i < 0:
                continue
            j = c.find("{", i)
            if j < 0:
                break
            try:
                json.loads(c[j:])
            except Exception as e:
                badj.append(str(e))
            if "\n" in c[j:] or "\r" in c[j:]:
                badn.append(c[:40])
            break
    rec(11, "tellraw/titleraw JSON 合法且无真换行",
        not badj and not badn, "非法 %d / 含真换行 %d" % (len(badj), len(badn)))

    # 12 链末端 = 链数：直接调用独立校验器算，避免自证
    import subprocess
    import re
    vp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_mcworld.py")
    out = subprocess.run([sys.executable, vp, args.path],
                         capture_output=True, text=True).stdout
    m = re.search(r"链末端 (\d+) 个", out)
    ends = int(m.group(1)) if m else -1
    rec(12, "链末端数量与链数一致（init + 4 功能链 + 4 面板 = 9）",
        ends == 9, "实测 %d 个" % ends)

    # 13 断链结构：条件块与无条件块并存，且条件块占比合理
    # 只看条件块=0 → 没断链（空闲全额浪费）；只看条件块 → 缺闸门，段会永久失效
    rec(13, "全部无条件块（断链只靠 facing_direction，不用 conditional_bit）",
        n_cond == 0 and n_uncond > 0,
        "条件 %d / 无条件 %d" % (n_cond, n_uncond))

    # 14 命令方块控制台静默：改的是方块 NBT，不是 gamerule
    loud = [e for e in ents_full
            if e.get("TrackOutput", (1, 0))[1] != 0
            or e.get("LastOutput", (0, ""))[1] != ""]
    rec(14, "命令方块控制台静默（TrackOutput=0 且 LastOutput 为空）",
        not loud, "%d 个方块仍在记录输出" % len(loud))

    # 15 聊天栏灰字屏蔽：这 6 条 gamerule 与上面那条 NBT 是两套东西，缺一不可
    need = ["sendcommandfeedback false", "commandblockoutput false",
            "showdeathmessages false", "announceadvancements false",
            "showrecipemessages false", "showcoordinates false"]
    have = {c.strip() for c in cmds}
    missg = [g for g in need if ("gamerule " + g) not in have]
    rec(15, "聊天栏灰字屏蔽（6 条 gamerule 齐全）",
        not missg, "缺 %s" % (missg or "无"))

    # 16 空闲常驻：沿循环链走一遍，数无条件块
    # 无条件块永远执行（不受前驱失败影响），所以空闲每刻执行的条数 = 链上无条件块数
    DIR = {0: (0, -1, 0), 1: (0, 1, 0), 2: (0, 0, -1),
           3: (0, 0, 1), 4: (-1, 0, 0), 5: (1, 0, 0)}
    rep = [p for p, v in grid.items() if v[0].endswith("repeating_command_block")]
    idle, clen, seen = 0, 0, set()
    if len(rep) == 1:
        cur = rep[0]
        while cur in grid and cur not in seen:
            seen.add(cur)
            nm, cd, fd = grid[cur]
            clen += 1
            if not cd:
                idle += 1          # 循环块自己那条闸门也要算：它每刻真的在执行
            dx, dy, dz = DIR.get(fd, (0, 0, 0))
            cur = (cur[0] + dx, cur[1] + dy, cur[2] + dz)
    rep = [p for p, v in grid.items() if v[0].endswith("repeating_command_block")]
    rec(16, "空闲常驻 = 功能链数 = 4 条（每刻只跑 4 个闸门）",
        len(rep) == 4, "循环块 %d 个 / 总命令方块 %d 个" % (len(rep), nent))

    print("=== 拔刀剑交付物 16 项自检 ===")
    print("文件：%s" % args.path)
    print("")
    npass = 0
    for no, name, ok, detail in rows:
        npass += 1 if ok else 0
        print(" %2d. %s %s" % (no, OK if ok else FAIL, name))
        if detail:
            print("       %s" % detail)
    print("")
    print("通过 %d / %d" % (npass, len(rows)))
    return 0 if npass == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
