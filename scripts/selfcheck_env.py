#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境自检：拿到 mct skill 后先跑这个，确认能不能干活。

用法：
    python scripts/selfcheck_env.py

它会检查四件事：
    1. Python 环境（版本 / 能否 import 关键模块）
    2. SKILL.md 与 references/ 是否齐全
    3. scripts/ 关键脚本与 _template.mcworld 是否在
    4. 模板能不能当 mcworld 用（zip 结构 + level.dat）

输出全部 ✅ 才算环境完整；有 ❌ 会给出修法。
"""
import io
import os
import sys
import zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

# 交付流程离不开的脚本（少一个就出不了 .mcstructure）
REQUIRED = [
    ("cbc.py",                "断链编译器（三段式）"),
    ("lint_commands.py",      "指令体检"),
    ("build_cbworld.py",      "世界构建（被所有 build_* import）"),
    ("mcworld_to_structure.py", "导出 .mcstructure"),
    ("verify_mcworld.py",     "回读校验"),
    ("check_chain_break.py",  "断链走查"),
    ("dump_cbworld.py",       "世界 → cb.json"),
    ("_template.mcworld",     "世界模板（level.dat 来源）"),
]

# 有就用、没有也能干活的可选件
OPTIONAL = [
    ("check_props.py",   "说明区走查"),
    ("build_katana.py",  "通用生成器（拔刀剑）"),
    ("build_tidegun.py", "鱼竿枪生成器"),
    ("build_fmbe.py",    "FMBE 展示体生成器"),
]

ok = fail = 0


def mark(cond, label, hint=""):
    global ok, fail
    if cond:
        print("  ✅ %s" % label)
        ok += 1
    else:
        print("  ❌ %s%s" % (label, ("\n     → " + hint) if hint else ""))
        fail += 1
    return cond


def main():
    print("=" * 62)
    print("mct skill 环境自检")
    print("=" * 62)
    print("skill 目录：%s" % ROOT)
    print()

    # ---------- 1. Python ----------
    print("[1/4] Python 环境")
    v = sys.version_info
    mark(v >= (3, 6), "Python %d.%d.%d（需 ≥ 3.6）" % (v[0], v[1], v[2]),
         "升级 Python")
    for mod in ("zipfile", "struct", "json", "re", "math"):
        try:
            __import__(mod)
        except ImportError:
            mark(False, "import %s" % mod, "标准库缺失，检查 Python 安装")
            break
    else:
        mark(True, "标准库齐全（zipfile / struct / json / re / math）")
    print()

    # ---------- 2. 文档 ----------
    print("[2/4] 文档")
    skill_md = os.path.join(ROOT, "SKILL.md")
    if mark(os.path.isfile(skill_md), "SKILL.md",
            "skill 根目录缺主文件，这份 skill 不完整"):
        n = len(io.open(skill_md, encoding="utf-8").read().split("\n"))
        print("     共 %d 行" % n)

    ref_dir = os.path.join(ROOT, "references")
    if mark(os.path.isdir(ref_dir), "references/ 目录",
            "细节全表都在这里，缺了只剩主线"):
        files = sorted(f for f in os.listdir(ref_dir) if f.endswith(".md"))
        print("     共 %d 个文件：%s" % (len(files), " / ".join(f.split("-")[0] for f in files)))
        if len(files) < 10:
            mark(False, "references 数量偏少（应 ≥ 10）", "分发时可能只给了部分文件")
    print()

    # ---------- 3. 脚本 ----------
    print("[3/4] 脚本与模板")
    missing = []
    for name, desc in REQUIRED:
        p = os.path.join(BASE, name)
        if not mark(os.path.isfile(p), "%-22s %s" % (name, desc),
                    "从完整 skill 包里补这个文件"):
            missing.append(name)
    for name, desc in OPTIONAL:
        p = os.path.join(BASE, name)
        if os.path.isfile(p):
            print("  ✅ %-22s %s（可选）" % (name, desc))
        else:
            print("  ○  %-22s %s（可选，缺了不影响出结构）" % (name, desc))
    print()

    # ---------- 4. 模板可用性 ----------
    print("[4/4] 模板可用性")
    tpl = os.path.join(BASE, "_template.mcworld")
    if os.path.isfile(tpl):
        try:
            z = zipfile.ZipFile(tpl)
            names = z.namelist()
            has_level = "level.dat" in names
            has_db = any(n.startswith("db/") for n in names)
            mark(has_level, "模板含 level.dat", "换一个真实存档当模板")
            mark(has_db, "模板含 db/（LevelDB）", "换一个真实存档当模板")
            print("     %d 项 / %.1f KB" % (len(names), os.path.getsize(tpl) / 1024))
        except zipfile.BadZipFile:
            mark(False, "模板不是合法 zip", "重新从游戏导出一份 .mcworld 当模板")
    else:
        mark(False, "缺 _template.mcworld",
             "可以用**任意真实存档**代替：--template 你的存档.mcworld")

    # ---------- 结论 ----------
    print()
    print("=" * 62)
    if fail == 0:
        print("✅ 环境完整，可以按 SKILL.md 的「工作流」开工")
        print()
        print("下一步（三步出一份结构）：")
        print("  1. 写 spec 或改现成生成器：python scripts/build_katana.py --dump-spec my.json")
        print("  2. 打包世界：python scripts/build_katana.py --spec my.json "
              "--template scripts/_template.mcworld --out 世界.mcworld")
        print("  3. 导出结构：python scripts/mcworld_to_structure.py "
              "--input 世界.mcworld --out 指令区.mcstructure")
        return 0
    else:
        print("❌ 有 %d 项不通过，先补齐再开工" % fail)
        if missing:
            print()
            print("缺的脚本：%s" % ", ".join(missing))
            print("→ 这些是交付流程的必需件，缺了无法生成/校验 .mcstructure。")
            print("→ 不要用「手写结构文件」蒙混：SKILL.md 明确要求跑完校验再交付。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
