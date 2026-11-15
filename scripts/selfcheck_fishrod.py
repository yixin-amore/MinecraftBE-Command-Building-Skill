#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""鱼竿枪交付物 22 项自检：全部从 .mcworld 回读，不看生成时的内存数据。

结构基准是 `断链演示.mcstructure`：
  每条功能链 = 循环闸门 + 复位块 + 自断块 + N 个业务块，全部无条件块。
"""
import argparse
import json
import math
import os
import re
import struct
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_mcworld as V

OK, FAIL = "\u2713", "\u2717"
DIR = {0: (0, -1, 0), 1: (0, 1, 0), 2: (0, 0, -1),
       3: (0, 0, 1), 4: (-1, 0, 0), 5: (1, 0, 0)}
REV = {v: k for k, v in DIR.items()}


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
    nested = [n for n in names if n.startswith("world/")]
    rec(1, "包结构：9 项齐全且 level.dat 在 zip 根",
        need.issubset(set(names)) and not nested,
        "%d 项 / 嵌套 %d" % (len(names), len(nested)))

    # 2 level.dat 头部
    lv = zf.read("level.dat")
    ver, ln = struct.unpack("<II", lv[:8])
    body = lv[8:]
    _, _, nbt, off = V.rnbt(body, 0)
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
        not miss and not bad, "缺 %s 值异常 %s" % (miss or "无", bad or "无"))

    # 4 db 五件套
    cur = zf.read("db/CURRENT").decode("utf-8", "replace").strip()
    rec(4, "db 五件套齐全 + CURRENT 指向 MANIFEST",
        all(("db/" + x) in names for x in ("CURRENT", "LOCK", "LOG",
                                          "MANIFEST-000000", "000001.log"))
        and cur == "MANIFEST-000000", "CURRENT=%s" % cur)

    # 5 CRC
    payloads, crc_bad = V.parse_log(zf.read("db/000001.log"))
    rec(5, "日志记录 CRC32C 全通过", crc_bad == 0,
        "%d 条记录 / %d 条错误" % (len(payloads), crc_bad))

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
    facing_detail, nsub, nent = [], 0, 0
    n_cond = n_uncond = 0
    ents_full, ents = [], []
    grid, cmd_at = {}, {}
    for pl in payloads:
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
                    _, _, _, p = V.rnbt(d, p)
                    continue
                bpw = 32 // bits
                words = math.ceil(4096 / bpw)
                wstart = p
                p += words * 4
                pc = struct.unpack("<I", d[p:p + 4])[0]; p += 4
                pal_cond = []
                for i in range(pc):
                    _, _, vv, p = V.rnbt(d, p)
                    nmz = vv.get("name", (0, ""))[1]
                    if i == 0 and nmz != "minecraft:air":
                        pal_air = False
                    st = vv.get("states", (10, {}))[1]
                    if "facing_direction" in st:
                        ft, fv = st["facing_direction"]
                        if ft != 3:
                            facing_ok = False
                        facing_detail.append(fv)
                    pal_cond.append((nmz, st.get("conditional_bit", (0, 0))[1],
                                     st.get("facing_direction", (0, 0))[1]))
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
                                pos = (cx * 16 + ((nslot >> 8) & 15),
                                       sy * 16 + (nslot & 15),
                                       cz * 16 + ((nslot >> 4) & 15))
                                grid[pos] = (pnm, pcb, pfd)
                        nslot += 1
            if p != len(d):
                sub_ok = False
        elif tag == b"\x31":
            b = val
            o2 = 0
            while o2 < len(b):
                _, _, vv, o2 = V.rnbt(b, o2)
                if vv.get("id", (0, ""))[1] == "CommandBlock":
                    nent += 1
                    ents_full.append(vv)
                    pos = (vv["x"][1], vv["y"][1], vv["z"][1])
                    cmd = vv.get("Command", (0, ""))[1]
                    ents.append(pos + (cmd,))
                    cmd_at[pos] = cmd

    rec(6, "子区块字节精确消费（无残留/无越界）", sub_ok, "%d 个子区块层" % nsub)
    rec(7, "调色板 [0] 为 minecraft:air", pal_air, "")
    rec(8, "facing_direction 全部为 TAG_Int", facing_ok,
        "取值集合 %s" % sorted(set(facing_detail)))

    inrange = all(-64 <= y <= 320 for _, y, _, _ in ents)
    spread = len({(x, z) for x, _, z, _ in ents})
    rec(9, "命令方块实体使用世界坐标（y 合法、位置分散）",
        inrange and spread > 1, "%d 个实体 / %d 个不同 (x,z)" % (nent, spread))

    cmds = [c for *_, c in ents]

    mcf = [c for c in cmds if "function" in c]
    tg = [c for c in cmds if c.startswith("tag ") or " tag @" in c]
    rec(10, "命令中无 function / 无 tag 指令（状态全走计分板）",
        not mcf and not tg, "function %d / tag %d" % (len(mcf), len(tg)))

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

    vp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_mcworld.py")
    out = subprocess.run([sys.executable, vp, args.path],
                         capture_output=True, text=True).stdout
    m = re.search(r"链末端 (\d+) 个", out)
    ends = int(m.group(1)) if m else -1
    # init + 3 功能链 + 4 面板 = 8
    rec(12, "链末端数量与链数一致（init + 3 功能链 + 4 面板 = 8）",
        ends == 8, "实测 %d 个" % ends)

    # ---------- 沿链走向重建每条链 ----------
    rep = sorted([p for p, v in grid.items()
                  if v[0].endswith("repeating_command_block")],
                 key=lambda p: (p[2], p[0]))
    chains = []
    for r in rep:
        seq, cur, seen = [], r, set()
        while cur in grid and cur not in seen:
            seen.add(cur)
            seq.append((cur, grid[cur][2], cmd_at.get(cur, "")))
            dx, dy, dz = DIR.get(grid[cur][2], (0, 0, 0))
            cur = (cur[0] + dx, cur[1] + dy, cur[2] + dz)
        chains.append(seq)
    # 按 z 排序的全局命令序列，供跨链顺序检查
    glob = [c for ch in chains for _, _, c in ch]

    # 13 断链结构：无一个条件块（全靠改朝向）
    rec(13, "全部无条件块（断链只靠 facing_direction，不用 conditional_bit）",
        n_cond == 0 and n_uncond > 0,
        "条件 %d / 无条件 %d" % (n_cond, n_uncond))

    # 14 三条功能链，每条都是 闸门 + 复位 + 自断
    good, detail = 0, []
    for seq in chains:
        if len(seq) < 4:
            detail.append("链过短")
            continue
        (p0, f0, c0), (p1, f1, c1), (p2, f2, c2) = seq[0], seq[1], seq[2]
        ok_reset = c1.startswith("setblock ~") and "chain_command_block" in c1
        # 复位块的相对坐标必须正好指向自断块，否则摆错格子
        mr = re.match(r"setblock ~(-?\d+) ~ ~(-?\d+)", c1)
        if mr:
            ok_reset = ok_reset and (
                (p1[0] + int(mr.group(1)), p1[1], p1[2] + int(mr.group(2))) == p2)
        else:
            ok_reset = False
        # 复位块的 facing_direction 必须是"运行方向"（从复位格指向自断格）
        run_fd = REV.get((p2[0] - p1[0], 0, p2[2] - p1[2]))
        mf = re.search(r'facing_direction"=(\d+)', c1)
        ok_run = mf is not None and int(mf.group(1)) == run_fd
        ok_break = (c2.startswith("execute unless")
                    and "run setblock ~ ~ ~ chain_command_block" in c2)
        # 自断块"运行时"会把自己摆成朝链首，但方块上存的是"朝运行方向"。
        # 所以要读命令里的 facing_direction 数字，验证它反算回来落在复位块上。
        mm = re.search(r'facing_direction"=(\d+)', c2)
        ok_back = False
        if mm:
            fb = int(mm.group(1))
            tx = (p2[0] + DIR[fb][0], p2[1] + DIR[fb][1], p2[2] + DIR[fb][2])
            ok_back = tx == p1
        if ok_reset and ok_run and ok_break and ok_back:
            good += 1
        else:
            detail.append("z=%d 复位%s 运行向%s 自断%s 回指%s"
                          % (p0[2], ok_reset, ok_run, ok_break, ok_back))
    rec(14, "每条功能链：复位块朝运行方向、自断块朝链首方向",
        len(chains) == 3 and good == 3,
        "%d/%d 条合格 %s" % (good, len(chains), " ".join(detail) or ""))

    # 15 命令方块控制台静默
    loud = [e for e in ents_full
            if e.get("TrackOutput", (1, 0))[1] != 0
            or e.get("LastOutput", (0, ""))[1] != ""]
    rec(15, "命令方块控制台静默（TrackOutput=0 且 LastOutput 为空）",
        not loud, "%d 个方块仍在记录输出" % len(loud))

    # 16 聊天栏灰字
    need = ["sendcommandfeedback false", "commandblockoutput false",
            "showdeathmessages false", "announceadvancements false",
            "showrecipemessages false", "showcoordinates false"]
    have = {c.strip() for c in cmds}
    missg = [g for g in need if ("gamerule " + g) not in have]
    rec(16, "聊天栏灰字屏蔽（6 条 gamerule 齐全）", not missg,
        "缺 %s" % (missg or "无"))

    # 17 空闲常驻 = 功能链数
    rec(17, "空闲常驻 = 功能链数 = 3 条（每刻只跑 3 个闸门）",
        len(rep) == 3, "循环块 %d 个 / 总命令方块 %d 个" % (len(rep), nent))

    # 18 三条闸门各管一件事
    g = [chains[0][0][2] if chains else "", chains[1][0][2] if len(chains) > 1 else "",
         chains[2][0][2] if len(chains) > 2 else ""]
    ok18 = ("fishing_rod" in g[0] and "fishing_hook" in g[1]
            and "xp_orb" in g[2] and "b_life" in g[2])
    rec(18, "闸门分工：持枪 / 抛竿 / 有子弹", ok18,
        " / ".join(x[:44] for x in g))

    # 19 出弹流水线顺序（在开火链内查）
    fire = chains[1] if len(chains) > 1 else []
    fseq = [c for _, _, c in fire]

    def idx(sub, seq=fseq):
        for i, c in enumerate(seq):
            if sub in c:
                return i
        return -1

    order = [idx("summon xp_orb"), idx("b_new 1"), idx("scores={b_new=1}] ~~~ ~ ~"),
             idx("scores={b_new=1}] ^ ^ ^1.2"), idx("b_life = @s range"),
             idx("remove @s ammo 1")]
    rec(19, "出弹流水线顺序（召唤→打标→继承朝向→灌参数→扣弹）",
        all(x >= 0 for x in order) and order == sorted(order),
        " / ".join(str(x + 1) for x in order))

    # 20 递减在判断之前
    state = chains[0] if chains else []
    sseq = [c for _, _, c in state]
    i_cd = idx("remove @a[scores={gun=1}] fire_cd 1", sseq)
    i_rl = idx("remove @a[scores={gun=1,reload=1..}] reload 1", sseq)
    i_settle = idx("rl_tmp = @s mag", sseq)
    i_hud = idx("titleraw @s actionbar", sseq)
    rec(20, "递减在结算之前（fire_cd→开火；reload→换弹结算），且 HUD 在链尾",
        i_cd >= 0 and i_rl >= 0 and i_settle >= 0 and i_rl < i_settle
        and i_hud > i_cd,
        "fire_cd %d / reload %d<%d / HUD %d" % (i_cd + 1, i_rl + 1, i_settle + 1, i_hud + 1))

    # 21 %%2 未被 % 格式化破坏
    bad2 = [c for c in cmds if '"translate":"%2"' in c]
    hud = [c for c in cmds if "actionbar" in c]
    rec(21, "HUD 条件拼接未被 % 格式化破坏（%%2 完好）",
        not bad2 and len(hud) == 2 and hud[0].count('"translate":"%%2"') >= 20,
        "腐坏 %d / HUD %d 条 / %%2 组件 %d 个"
        % (len(bad2), len(hud), hud[0].count('"translate":"%%2"') if hud else 0))

    # 22 auto 位：循环块和链块必须自动推进，脉冲块必须 auto=0（等按钮）
    bad_auto = []
    for e in ents_full:
        pos = (e["x"][1], e["y"][1], e["z"][1])
        name = grid.get(pos, ("", 0, 0))[0]
        a = e.get("auto", (1, 1))[1]
        if name == "minecraft:command_block":
            if a != 0:
                bad_auto.append((pos, "脉冲 auto=%d" % a))
        elif "command_block" in name and a != 1:
            bad_auto.append((pos, "%s auto=%d" % (name, a)))
    rec(22, "auto 位正确（脉冲块 auto=0，循环/链块 auto=1）",
        not bad_auto, "%d 个异常 %s" % (len(bad_auto), bad_auto[:3] or ""))

    print("=== 鱼竿枪交付物 22 项自检 ===")
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
