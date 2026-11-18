#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lookup public command syntax facts: command formats and shared token vocabulary."""
import json, argparse
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]/'references'/'command-syntax.json'
ap=argparse.ArgumentParser()
ap.add_argument('command',nargs='?')
ap.add_argument('--version',default='netease-vanilla')
ap.add_argument('--json',action='store_true')
ap.add_argument('--token',help='check a token in the shared vocabulary')
a=ap.parse_args()
d=json.loads(BASE.read_text(encoding='utf-8'))
v=d['versions'].get(a.version)
if not v: raise SystemExit('unknown version: '+a.version)
if a.token:
    ok=a.token in d.get('tokens',[])
    print(json.dumps({'token':a.token,'present':ok},ensure_ascii=False) if a.json else ('yes' if ok else 'no'))
    raise SystemExit(0)
if not a.command:
    print(json.dumps({'version':a.version,'commandCount':v['commandCount'],'commands':sorted(v['commands'])},ensure_ascii=False,indent=1)); raise SystemExit(0)
c=v['commands'].get(a.command)
if not c: raise SystemExit('unknown command: '+a.command)
out={'version':a.version,'command':a.command,'formats':c['formats'],'tokenCount':len(d.get('tokens',[]))}
print(json.dumps(out,ensure_ascii=False,indent=1) if a.json else '\n'.join(c['formats']))
