#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search the local training corpus. No network; never copies files."""
import json, os, re, sys, argparse
from pathlib import Path
def _corpus():
    env=os.environ.get('CMD_CORPUS')
    if env: return Path(env)
    for base in [Path.cwd(), *Path(__file__).resolve().parents]:
        p=base/'work'/'command-corpus'
        if p.is_dir(): return p
    return Path('work/command-corpus')
CORPUS=_corpus()
ap=argparse.ArgumentParser()
ap.add_argument('query')
ap.add_argument('--category')
ap.add_argument('--limit',type=int,default=5)
ap.add_argument('--chars',type=int,default=700)
ap.add_argument('--json',action='store_true')
a=ap.parse_args()
terms=[t.lower() for t in re.split(r'\s+',a.query.strip()) if t]
rows=[]
for fn in ('train.jsonl','valid.jsonl','test.jsonl'):
 p=CORPUS/fn
 if not p.exists(): continue
 for line in p.open(encoding='utf-8'):
  try: r=json.loads(line)
  except Exception: continue
  if a.category and r.get('category')!=a.category: continue
  hay=(r.get('name','')+' '+' '.join(r.get('tags',[]) or [])+' '+r.get('text','')).lower()
  score=sum(3 if t in r.get('name','').lower() else 1 for t in terms if t in hay)
  if score<=0: continue
  rows.append((score,r))
rows.sort(key=lambda x:(-x[0],x[1].get('chars',0)))
out=[]
for score,r in rows[:a.limit]:
 text=r.get('text','')
 pos=-1
 for t in terms:
  pos=text.lower().find(t)
  if pos>=0: break
 if pos<0: pos=0
 s=max(0,pos-160); snippet=text[s:s+a.chars]
 out.append({'score':score,'id':r.get('id'),'name':r.get('name'),'category':r.get('category'),'subcategory':r.get('subcategory'),'command_lines':r.get('command_lines'),'chars':r.get('chars'),'source':r.get('source'),'snippet':snippet})
if a.json:
 print(json.dumps(out,ensure_ascii=False,indent=1))
else:
 for i,x in enumerate(out,1):
  print(f"\n[{i}] {x['name']}  {x['category']}/{x['subcategory']}  cmds={x['command_lines']} chars={x['chars']}")
  print(x['source'])
  print(x['snippet'][:a.chars].replace('\n',' | '))
