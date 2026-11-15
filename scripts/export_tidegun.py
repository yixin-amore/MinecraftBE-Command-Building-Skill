#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""潮汐鱼竿枪 · 一键导出（uuid4 命名 + 原子归位 + 临时文件清理）

为什么要有这个脚本：
  1. 用户要求产物名后带 uuid4 —— 每次构建都是新名字，系统不会再把文件
     重命名成 `名字2` / `名字67`，也就不会再出现「我打开的是旧文件，
     所以断链又没了」的假故障。
  2. 导出必须经 `.mcworld` 中转，但交付物只能是 `.mcstructure`，所以
     mcworld 一律写到临时名并在成功后删除。
  3. 旧产物会被清理，`out/` 里同名只留一份，防止误开旧文件。

用法：
    python scripts/export_tidegun.py
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
PROJ = os.path.abspath(os.path.join(SKILL, "..", "..", ".."))

SPEC = os.path.join(PROJ, "鱼竿枪", "specs", "tidegun.json")
OUTDIR = os.path.join(PROJ, "鱼竿枪", "out")
TEMPLATE = r"F:\新建文件夹 (9)\2026-11-09-13-39-33\data_system\_template.mcworld"
BASE_NAME = "潮汐鱼竿枪"


def run(args, quiet=False):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    if not quiet:
        print(out.rstrip())
    if r.returncode != 0:
        print("\n[失败] %s\n%s" % (" ".join(args), out))
        sys.exit(r.returncode)
    return out


def main():
    if not os.path.exists(TEMPLATE):
        sys.exit("模板世界不存在：%s" % TEMPLATE)
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(os.path.dirname(SPEC), exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="tidegun_")
    mcworld = os.path.join(tmpdir, "_build.mcworld")

    try:
        print("=" * 68)
        print("[0/7] 编译器自检（先证明结构会跑，再生成）")
        run([os.path.join(HERE, "cbc.py")])

        print("\n[1/7] 生成规格")
        run([os.path.join(HERE, "build_tidegun.py"), "--dump-spec", SPEC])

        print("\n[2/7] 构建世界（临时 .mcworld）")
        run([os.path.join(HERE, "build_tidegun.py"), "--spec", SPEC,
             "--template", TEMPLATE, "--out", mcworld])

        print("\n[3/7] 校验世界")
        run([os.path.join(HERE, "verify_mcworld.py"), mcworld])

        print("\n[4/7] 命令语法 lint")
        lint_out = run([os.path.join(HERE, "lint_commands.py"), SPEC])
        bad = [ln for ln in lint_out.splitlines()
               if ln.strip().startswith(("✗", "[X]", "ERROR", "错误"))]
        if bad:
            print("\n[失败] lint 有 %d 条错误" % len(bad))
            sys.exit(1)

        print("\n[5/7] 导出结构文件（uuid4 命名）")
        cbjson = os.path.join(OUTDIR, "cb.json")
        run([os.path.join(HERE, "dump_cbworld.py"), mcworld, "--json", cbjson],
            quiet=True)
        print("  命令方块结构 → %s" % cbjson)

        print("\n[6/7] 断链结构走查（用户 U3 标准格式）")
        run([os.path.join(HERE, "check_chain_break.py"), cbjson,
             "--expect", "58"])

        # 清理旧产物（只留这一份），避免误开旧文件
        old = glob.glob(os.path.join(OUTDIR, BASE_NAME + "*.mcstructure"))
        for f in old:
            os.remove(f)
            print("  清理旧产物 → %s" % os.path.basename(f))

        tag = uuid.uuid4().hex[:8]
        name = "%s-%s.mcstructure" % (BASE_NAME, tag)
        final = os.path.join(OUTDIR, name)
        # 中转文件必须放在 out/ 同一磁盘，否则 os.replace 会报 WinError 17
        stage = os.path.join(OUTDIR, "_stage.mcstructure")
        run([os.path.join(HERE, "mcworld_to_structure.py"),
             "--input", mcworld, "--out", stage], quiet=True)
        os.replace(stage, final)          # 原子归位，杜绝 `名字2` 累积
        print("  产物 → %s" % final)

        left = sorted(os.path.basename(p) for p in
                      glob.glob(os.path.join(OUTDIR, "*.mcstructure")))
        print("\n[交付] out/ 中 .mcstructure 共 %d 份：%s"
              % (len(left), ", ".join(left)))
        print("       大小 %.1f KB" % (os.path.getsize(final) / 1024.0))

        meta = os.path.join(OUTDIR, "build.json")
        with open(meta, "w", encoding="utf-8") as f:
            json.dump({"product": name, "uuid4": tag,
                       "size": os.path.getsize(final)}, f,
                      ensure_ascii=False, indent=1)
        return final
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
