#!/usr/bin/env python3
"""Classify a folder of MCBE command text files.

Not a Bedrock parser: it strips comments, counts command lines, and extracts
recurring syntax so a large command corpus can be turned into a framework.

Usage:
    python3 scripts/command_corpus.py /path/to/commands --json out.json --md out.md
"""
from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path

FIRST = re.compile(r"^/?\s*([a-z_]+)")
OBJ = re.compile(r"scoreboard\s+objectives\s+add\s+([^\s]+)")
TAG = re.compile(r"\btag\s*=\s*!?([A-Za-z0-9_.:-]+)")
TAGADD = re.compile(r"\btag\s+\S+\s+add\s+([^\s]+)")
TYPE = re.compile(r"\btype\s*=\s*!?([a-z_]+)")
SUMMON = re.compile(r"\bsummon\s+([a-z_]+)")
PATTERNS = {
    "execute": r"\bexecute\b", "positioned": r"\bpositioned\b",
    "rotated": r"\brotated\b", "align": r"\balign\b",
    "hasitem": r"\bhasitem\b", "structure": r"\bstructure\b",
    "titleraw": r"\btitleraw\b", "playanimation": r"\bplayanimation\b",
    "summon": r"\bsummon\b", "tag": r"\btag\b", "scoreboard": r"\bscoreboard\b",
    "function": r"\bfunction\b", "particle": r"\bparticle\b",
    "damage": r"\bdamage\b", "clone": r"\bclone\b", "fill": r"\bfill\b",
}

def scan(paths):
    files=[]; fc=Counter(); obj=Counter(); tags=Counter(); types=Counter(); sums=Counter(); pats=Counter()
    for path in paths:
        text=Path(path).read_text(encoding="utf-8", errors="replace")
        lines=[]; comments=0
        for raw in text.splitlines():
            line=raw.strip()
            if not line: continue
            if line.startswith("#") or line.startswith("//"):
                comments+=1; continue
            lines.append(line)
        first=Counter()
        for line in lines:
            m=FIRST.match(line)
            if m: first[m.group(1)]+=1
            for name,rx in PATTERNS.items():
                if re.search(rx,line): pats[name]+=1
            for rx,c in ((OBJ,obj),(TAG,tags),(TAGADD,tags),(TYPE,types),(SUMMON,sums)):
                for x in rx.findall(line): c[x]+=1
        fc.update(first)
        files.append({"file":Path(path).name,"lines":len(text.splitlines()),"comments":comments,
                      "commands":len(lines),"first":dict(first)})
    return {"files":files,"command_freq":dict(fc.most_common()),
            "patterns":dict(pats),"objectives":dict(obj.most_common()),
            "tags":dict(tags.most_common()),"entities":dict(types.most_common()),
            "summons":dict(sums.most_common())}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("dir"); ap.add_argument("--json"); ap.add_argument("--md")
    a=ap.parse_args(); root=Path(a.dir)
    paths=sorted([p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in (".txt",".mcfunction")])
    data=scan(paths)
    if a.json: Path(a.json).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    if a.md:
        out=["# Command corpus scan","",f"files: {len(data['files'])}","","## Per file","",
             "| file | lines | comments | commands |","|---|---:|---:|---:|"]
        for f in data["files"]: out.append(f"| {f['file']} | {f['lines']} | {f['comments']} | {f['commands']} |")
        out += ["","## First command","","| command | count |","|---|---:|"]
        for k,v in data["command_freq"].items(): out.append(f"| `{k}` | {v} |")
        out += ["","## Patterns","","| pattern | lines |","|---|---:|"]
        for k,v in data["patterns"].items(): out.append(f"| `{k}` | {v} |")
        Path(a.md).write_text("\n".join(out)+"\n",encoding="utf-8")
    print(json.dumps({"files":len(data["files"]),"commands":sum(f["commands"] for f in data["files"]),"patterns":data["patterns"]},ensure_ascii=False))

if __name__=="__main__": main()
