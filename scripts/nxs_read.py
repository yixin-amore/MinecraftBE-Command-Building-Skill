#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read NXS compiler JSON and validate command/point counts."""
import json, argparse, re
from pathlib import Path
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('artifact'); ap.add_argument('--json',default=None); a=ap.parse_args()
    d=json.loads(Path(a.artifact).read_text(encoding='utf-8'))
    cmds=d.get('commands',[]); pts=d.get('points',[])
    parsed=[]
    for c in cmds:
        m=re.match(r'^(?:execute positioned .*? run )?(particle|setblock|fill)\s+(\S+)',c)
        parsed.append({'kind':m.group(1),'material':m.group(2),'pos':[]} if m else {'error':c})
    issues=[]
    if len(cmds)!=len(pts): issues.append('commands %d != points %d'%(len(cmds),len(pts)))
    if any('error' in p for p in parsed): issues.append('unparsed command')
    budget=d.get('budget',{})
    if budget.get('issues'): issues += budget['issues']
    out={'points':len(pts),'commands':len(cmds),'materials':sorted(set(p.get('material') for p in parsed if p.get('material'))),
         'kinds':sorted(set(p.get('kind') for p in parsed if p.get('kind'))),'issues':issues,'ok':not issues}
    print(json.dumps(out,ensure_ascii=False,indent=1))
    if a.json: Path(a.json).write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
if __name__=='__main__': main()
