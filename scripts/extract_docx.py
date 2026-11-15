#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_docx.py —— .docx → 纯文本（保留段落换行，命令一行一条）

用途：把 E:/Pictures 下的实战原文转成 refs/*.txt，供 skill 直接引用。
不依赖 python-docx，直接读 word/document.xml。

用法：
  python extract_docx.py 输入.docx 输出.txt
  python extract_docx.py E:/Pictures --out-dir refs      # 整个目录批量转
"""
import argparse
import html
import os
import re
import sys
import zipfile


def docx_to_text(path):
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n == "word/document.xml"]
        if not names:
            raise ValueError("%s 里没有 word/document.xml" % path)
        xml = zf.read("word/document.xml").decode("utf-8", "replace")

    # 段落 / 换行 → \n
    xml = xml.replace("</w:p>", "\n")
    xml = xml.replace("<w:br/>", "\n").replace("<w:br />", "\n")
    xml = xml.replace("<w:tab/>", "\t").replace("<w:tab />", "\t")
    # 表格单元格之间加分隔，避免两格文字粘成一行
    xml = xml.replace("</w:tc>", "\t")

    # 只取 <w:t> 里的文字
    parts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml, re.S)
    # 重新按段落切：先按 </w:p> 分块再取块内 w:t，保证换行位置正确
    out_lines = []
    for para in re.split(r"\n", xml):
        txt = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, re.S))
        if txt.strip():
            out_lines.append(html.unescape(txt).rstrip())
        elif out_lines and out_lines[-1] != "":
            out_lines.append("")
    # 压掉连续空行
    text = "\n".join(out_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=".docx → 纯文本")
    ap.add_argument("src", help="单个 .docx 或一个目录")
    ap.add_argument("out", nargs="?", help="输出 .txt（单文件模式）")
    ap.add_argument("--out-dir", help="批量模式的输出目录")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的 txt")
    args = ap.parse_args()

    if os.path.isdir(args.src):
        out_dir = args.out_dir or args.src
        os.makedirs(out_dir, exist_ok=True)
        n = 0
        for fn in sorted(os.listdir(args.src)):
            if not fn.lower().endswith(".docx") or fn.startswith("~$"):
                continue
            dst = os.path.join(out_dir, fn[:-5] + ".txt")
            if os.path.exists(dst) and not args.force:
                print("[跳过] %s（已存在）" % os.path.basename(dst))
                continue
            try:
                t = docx_to_text(os.path.join(args.src, fn))
            except Exception as e:
                print("[失败] %s → %s" % (fn, e))
                continue
            with open(dst, "w", encoding="utf-8") as f:
                f.write(t)
            print("[完成] %-40s %6d 字" % (os.path.basename(dst), len(t)))
            n += 1
        print("共转 %d 份" % n)
        return

    if not args.out:
        ap.error("单文件模式要指定输出 .txt")
    t = docx_to_text(args.src)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(t)
    print("[完成] %s  %d 字" % (args.out, len(t)))


if __name__ == "__main__":
    main()
