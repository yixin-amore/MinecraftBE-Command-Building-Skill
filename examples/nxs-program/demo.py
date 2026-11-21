#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three non-image NXS programs: spiral stair, rose tracery, orbiting laser."""
import sys, json, math
from pathlib import Path
HERE=Path(__file__).resolve().parent
SKILL=HERE.parents[1]; sys.path.insert(0,str(SKILL/'scripts'))
from nxs_program import (NxsProgram, SpiralOp, RadialOp, OrbitOp, PathOp, NxsFrame,
                        BranchOp, BezierOp, ArcOp, RayOp, QueryOp)
from nxs_ir import Sphere

def spiral():
    p=NxsProgram('spiral-stair')
    p.add(SpiralOp(center=(0,0,0),radius=4,turns=1,rise=6,count=24,
                   material='minecraft:stone_bricks',kind='block'))
    return p

def rose():
    p=NxsProgram('rose-tracery')
    # outer + inner ring
    p.add(RadialOp(center=(0,0,0),radius=6,count=32,material='minecraft:blue_stained_glass',kind='block'))
    p.add(RadialOp(center=(0,0,0),radius=3,count=16,material='minecraft:glass',kind='block'))
    # 8 spokes
    for i in range(8):
        a=2*math.pi*i/8
        p.add(PathOp(points=[(0,0,0),(6*math.cos(a),0,6*math.sin(a))],samples=8,
                     material='minecraft:gold_block',kind='block'))
    return p

def branch():
    p=NxsProgram('branch-tree')
    p.add(BranchOp(NxsFrame((0,0,0)),depth=3,branches=2,length=4,angle=32,decay=.72,
                   material='minecraft:oak_log',kind='block'))
    return p

def curve():
    p=NxsProgram('curve-query')
    p.add(ArcOp(center=(0,0,0),radius=6,start_deg=0,end_deg=180,samples=24,height=0,
                material='minecraft:gold_block',kind='block'))
    p.add(BezierOp(controls=[(0,0,0),(3,8,0),(8,8,0),(12,0,0)],samples=24,
                   material='minecraft:end_rod',kind='particle'))
    p.add(QueryOp(RayOp(origin=(0,0,0),direction=(0,0,1),length=12,step=1,
                        material='minecraft:end_rod',kind='particle'),
                 Sphere((0,0,6),2.5),'inside'))
    return p

def orbit():
    p=NxsProgram('orbiting-laser')
    p.add(OrbitOp(center=(0,20,0),radius=6,height=0,count=24,
                  material='minecraft:end_rod',kind='particle'))
    # two radial beams crossing the orbit
    p.add(PathOp(points=[(-6,20,0),(6,20,0)],samples=24,material='minecraft:end_rod',kind='particle'))
    p.add(PathOp(points=[(0,20,-6),(0,20,6)],samples=24,material='minecraft:end_rod',kind='particle'))
    return p

if __name__=='__main__':
    out=HERE/'out'; out.mkdir(exist_ok=True)
    allrows=[]
    for fn,p in [('spiral',spiral()),('rose',rose()),('orbit',orbit()),('branch',branch()),('curve',curve())]:
        d=p.to_dict(); (out/(fn+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=1),encoding='utf-8')
        row={'name':p.name,'instances':d['budget']['instances'],'commands':d['budget']['commands'],'chars':d['budget']['chars']}
        allrows.append(row); print(row)
    (out/'report.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=1),encoding='utf-8')
