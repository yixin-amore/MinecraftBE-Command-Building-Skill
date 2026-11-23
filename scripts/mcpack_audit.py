#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static audit for a Bedrock .mcpack/.mcaddon: manifest, functions, command stats."""
import sys, json, zipfile, argparse, re
from pathlib import Path

def audit(path):
    z=zipfile.ZipFile(path)
    names=z.namelist()
    manifest=None
    for n in names:
        if n.endswith('manifest.json'):
            manifest=json.loads(z.read(n).decode('utf-8')); break
    funcs={}
    for n in names:
        if n.endswith('.mcfunction'):
            funcs[n]=z.read(n).decode('utf-8')
    lines=[]
    for n,s in funcs.items():
        for i,l in enumerate(s.splitlines(),1):
            if l.strip() and not l.strip().startswith('#'): lines.append((n,i,l))
    cmds=[x[2] for x in lines]
    prefixes={}
    for c in cmds: prefixes[c.split()[0]]=prefixes.get(c.split()[0],0)+1
    issues=[]
    if any('~~~~~' in c for c in cmds): issues.append('suspicious tp @s ~~~~~ (missing spaces)')
    if manifest is None: issues.append('missing manifest.json')
    if max((len(c) for c in cmds),default=0)>10000: issues.append('function command line > 10000 chars')
    return {'source':Path(path).name,'files':names,'manifest':manifest,
            'functions':list(funcs),'commands':len(cmds),
            'playanimation':prefixes.get('playanimation',0),
            'prefixes':prefixes,
            'max_line':max((len(c) for c in cmds),default=0),
            'total_chars':sum(len(c) for c in cmds),
            'issues':issues}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('pack'); ap.add_argument('--json',default=None); a=ap.parse_args()
    r=audit(a.pack); print(json.dumps(r,ensure_ascii=False,indent=1))
    if a.json: Path(a.json).write_text(json.dumps(r,ensure_ascii=False,indent=1),encoding='utf-8')
if __name__=='__main__': main()
