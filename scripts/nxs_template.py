#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile NXS cell/condition metadata into execute templates (one per cell)."""
from __future__ import annotations
import json, argparse
from pathlib import Path

def cell_template(point, condition=None, emit='particle', material='minecraft:stone'):
    x,y,z=point['x'],point['y'],point['z']
    head='execute positioned %.3f %.3f %.3f'%(x,y,z)
    if condition:
        if condition.get('if'):
            head += ' if entity @s[%s]'%','.join(condition['if'])
        if condition.get('unless'):
            head += ' unless entity @s[%s]'%','.join(condition['unless'])
    if emit=='setblock': cmd='setblock %.3f %.3f %.3f %s'%(x,y,z,material)
    elif emit=='fill': cmd='fill %.3f %.3f %.3f %.3f %.3f %.3f %s'%(x,y,z,x,y,z,material)
    else: cmd='particle %s %.3f %.3f %.3f'%(material,x,y,z)
    return head+' run '+cmd

def templates(artifact):
    cond=artifact.get('condition'); emit=artifact.get('raster',{}).get('emit','particle')
    mat=artifact.get('raster',{}).get('material','minecraft:stone')
    return [cell_template(p,cond,emit,mat) for p in artifact.get('points',[])]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('artifact'); ap.add_argument('--out',default=None); a=ap.parse_args()
    d=json.loads(Path(a.artifact).read_text(encoding='utf-8')); ts=templates(d)
    print('\n'.join(ts[:5])); print('... total',len(ts))
    if a.out: Path(a.out).write_text('\n'.join(ts)+'\n',encoding='utf-8')
if __name__=='__main__': main()
