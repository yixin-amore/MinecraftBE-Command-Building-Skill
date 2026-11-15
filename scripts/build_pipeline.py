#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用一键验收流水线：build → verify → check_bounds → lint → chain_break → export。

覆盖 mct skill 的「交付前最低动作」（references/19-constraints-64x64x100.md 第七节），
且任一步失败即时退出。不绑定任何具体项目——只要你的 `build_*.py` 遵循标准 CLI：
    --dump-spec / --spec / --template / --out
就能直接套用。

来源：寒冰拔刀实战（5.1 万块 / 120 秒）。把过去手敲一长串命令、expect 数拍脑袋的坑
固化成一条命令。

用法：
    python build_pipeline.py \
        --build-script build_badao2.py \
        --template "C:/.../_template.mcworld" \
        --outdir out \
        --name 寒冰拔刀

    # 已知道链数时直接给定，跳过探真值：
    python build_pipeline.py --build-script build_x.py --template T.mcworld \
        --outdir out --name X --expect 131 --func 0
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = lambda f: os.path.join(HERE, f)


def run(args, step, check=True):
    print("\n=== %s ===" % step)
    print("$ " + " ".join('"%s"' % a if " " in a else a for a in args))
    r = subprocess.run(args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    # 只打印末尾，避免刷屏（完整输出仍可在 CI 日志里看）
    tail = out if len(out) <= 4000 else "...(省略前 %d 字符)...\n%s" % (
        len(out) - 3000, out[-3000:])
    print(tail.rstrip())
    if check and r.returncode != 0:
        sys.exit("[流水线中止] %s 失败（exit=%d）" % (step, r.returncode))
    return r


def parse_chain(text):
    """从 check_chain_break 输出里抠出 可断链数 / 面板 setblock 数 / 是否出现 ✗。"""
    gated = dis = None
    m = re.search(r"可断链\s+(\d+)\s*条", text)
    if m:
        gated = int(m.group(1))
    m = re.search(r"面板 setblock.*?(\d+)\s*条", text)
    if m:
        dis = int(m.group(1))
    return gated, dis, ("✗" in text)


def main():
    ap = argparse.ArgumentParser(
        description="mct 通用一键验收流水线（build→verify→bounds→lint→chain→export）")
    ap.add_argument("--build-script", required=True, help="你的 build_*.py（标准 CLI）")
    ap.add_argument("--template", required=True, help="真实存档 .mcworld 模板")
    ap.add_argument("--outdir", required=True, help="产物目录（spec/cb.json/mcworld/结构 都放这）")
    ap.add_argument("--name", required=True, help="交付物基名（不加版本后缀，遵循 U7）")
    ap.add_argument("--max-x", type=int, default=64)
    ap.add_argument("--max-y", type=int, default=100)
    ap.add_argument("--max-z", type=int, default=64)
    ap.add_argument("--expect", type=int, default=None,
                    help="可断链数（不给则自动探真值）")
    ap.add_argument("--func", type=int, default=None,
                    help="面板 setblock 数/2（不给则自动探真值）")
    ap.add_argument("--keep-mcworld", action="store_true",
                    help="默认在导出成功后删掉中间 .mcworld（遵循 U1 只交 .mcstructure）")
    a = ap.parse_args()

    if not os.path.exists(a.template):
        sys.exit("[错误] 模板不存在：%s" % a.template)
    if not os.path.exists(a.build_script):
        sys.exit("[错误] 构建脚本不存在：%s" % a.build_script)

    os.makedirs(a.outdir, exist_ok=True)
    outdir = os.path.abspath(a.outdir)
    spec = os.path.join(outdir, "spec.json")
    mcw = os.path.join(outdir, "_b.mcworld")
    cb = os.path.join(outdir, "cb.json")
    mcs = os.path.join(outdir, "%s.mcstructure" % a.name)
    py = sys.executable

    # 1) 出 spec（顺带 measure_ta 把 tickingarea 写进去）
    run([py, a.build_script, "--dump-spec", spec], "1/7 dump-spec")

    # 2) 生成世界
    run([py, a.build_script, "--spec", spec,
         "--template", a.template, "--out", mcw], "2/7 build-world")

    # 3) 回读校验
    run([py, NAME("verify_mcworld.py"), mcw], "3/7 verify-mcworld")

    # 4) 包围盒断言 ≤ 64×64×100 + 打印常加载区
    run([py, NAME("check_bounds.py"), mcw,
         "--max-x", str(a.max_x), "--max-y", str(a.max_y),
         "--max-z", str(a.max_z)], "4/7 check-bounds")

    # 5) 指令体检（粒子+音效+JSON 白名单）
    run([py, NAME("lint_commands.py"), spec], "5/7 lint")

    # 6) 导 cb.json
    run([py, NAME("dump_cbworld.py"), mcw, "--json", cb], "6/7 dump-cbworld")

    # 7a) 断链走查：探真值（expect/func 不给时）
    disc = run([py, NAME("check_chain_break.py"), cb,
                "--expect", "999", "--func", "999"], "7a/7 chain-break(探真值)",
               check=False)
    gated, dis, has_prob = parse_chain(disc.stdout or "")
    if has_prob:
        sys.exit("[流水线中止] 断链走查发现 ✗ 结构问题，见 7a 输出")
    expect = a.expect if a.expect is not None else gated
    func = a.func if a.func is not None else (dis // 2 if dis is not None else 0)
    print("[探真值] 可断链=%s 面板setblock=%s → --expect %s --func %s"
          % (gated, dis, expect, func))

    # 7b) 断链走查：用真实值正式跑
    final = run([py, NAME("check_chain_break.py"), cb,
                 "--expect", str(expect), "--func", str(func)],
                "7b/7 chain-break(正式)", check=True)
    if "✗" in (final.stdout or ""):
        sys.exit("[流水线中止] 断链走查正式跑出现 ✗，见 7b 输出")

    # 8) 导出结构
    run([py, NAME("mcworld_to_structure.py"), "--input", mcw, "--out", mcs],
        "8/7 export-structure")

    if not a.keep_mcworld and os.path.exists(mcw):
        os.remove(mcw)
        print("[清理] 已删除中间 %s（只交付 .mcstructure，遵循 U1）" % mcw)

    print("\n✅ 流水线全部通过")
    print("   交付物：%s" % mcs)
    print("   链数：可断 %s / 面板 %s (func=%s)" % (expect, dis, func))


if __name__ == "__main__":
    main()
