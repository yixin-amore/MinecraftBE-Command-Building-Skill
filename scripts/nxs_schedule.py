#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NXS schedule: one command block per material via Bedrock functions."""
from __future__ import annotations
import json, argparse, math
from collections import defaultdict
from pathlib import Path

def schedule(artifact, function_prefix='nxs_'):
    points=artifact.get('points',[]); commands=artifact.get('commands',[])
    by_mat=defaultdict(list)
    for p,c in zip(points,commands):
        mat=p.get('material') or artifact.get('raster',{}).get('material','minecraft:stone')
        by_mat[mat].append(c)
    funcs={}; blocks=[]; chunks=0
    for i,(mat,cmds) in enumerate(sorted(by_mat.items())):
        name=function_prefix+str(i)
        # Bedrock function limit: keep chunks under 10k; here we also cap 1k for latency.
        for ci in range(0,len(cmds),1000):
            fn=name+'_'+str(ci//1000); funcs[fn]=cmds[ci:ci+1000]; chunks+=1
            blocks.append({'command':'function '+fn,'material':mat,'commands':len(cmds[ci:ci+1000])})
    out={'functions':funcs,'command_blocks':blocks,'materials':len(by_mat),
         'absolute_cb':len(commands),'scheduled_cb':len(blocks),'chunks':chunks,
         'issues':[] if len(blocks)<=80 else ['scheduled CB %d > 80'%len(blocks)]}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('artifact'); ap.add_argument('--out',default=None); ap.add_argument('--prefix',default='nxs_')
    a=ap.parse_args(); d=json.loads(Path(a.artifact).read_text(encoding='utf-8')); s=schedule(d,a.prefix)
    print(json.dumps({k:s[k] for k in ('materials','absolute_cb','scheduled_cb','chunks','issues')},ensure_ascii=False,indent=1))
    if a.out: Path(a.out).write_text(json.dumps(s,ensure_ascii=False,indent=1),encoding='utf-8')
if __name__=='__main__': main()
