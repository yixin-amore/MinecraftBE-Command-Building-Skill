#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NXS benchmarks: 2D circle, 3D cube, creeper bitmap, simple SVG."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SKILL=HERE.parents[1]; sys.path.insert(0,str(SKILL/'scripts'))
from PIL import Image
from nxs_ir import NxsRaster
from nxs_compile import build_shape, compile_raster, recommend_levels
from nxs_import import from_png, from_svg
from nxs_schedule import schedule

def creeper_png(path):
    im=Image.new('RGBA',(16,16),(0,0,0,0)); px=im.load()
    green=(70,140,70,255)
    for z in range(3,13):
        for x in range(3,13): px[x,z]=green
    # eyes / mouth holes
    for z in range(5,8):
        for x in (5,6,9,10): px[x,z]=(0,0,0,0)
    for z in range(9,12):
        for x in range(7,10): px[x,z]=(0,0,0,0)
    for z in range(10,13):
        for x in (5,6,9,10): px[x,z]=(0,0,0,0)
    im.save(path)

def run(name, shape, axes, levels=3):
    w=16; h=1 if axes=='2d' else 16
    r=NxsRaster(width=w,height=h,depth=16,levels=levels,shape=shape,axes=axes)
    a=compile_raster(r); s=schedule(a)
    a['schedule']={'materials':s['materials'],'scheduled_cb':s['scheduled_cb'],'chunks':s['chunks']}
    return {'name':name,'axes':axes,'levels':levels,'points':a['budget']['points'],
            'commands':a['budget']['commands'],'chars':a['budget']['chars'],
            'absolute_cb':a['budget']['cb'],'ticks':a['budget']['ticks'],
            'budget_ok':a['budget']['ok'],'scheduled_cb':s['scheduled_cb'],
            'chunks':s['chunks']}

def main():
    creeper_png(HERE/'creeper.png')
    svg=HERE/'simple.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect x="2" y="2" width="12" height="12"/><circle cx="8" cy="8" r="3"/></svg>',encoding='utf-8')
    rows=[]
    rows.append(run('circle',build_shape('circle',16),'2d'))
    rows.append(run('cube',build_shape('cube',16),'3d'))
    rows.append(run('creeper',from_png(HERE/'creeper.png'),'2d',4))
    rows.append(run('svg',from_svg(svg),'2d'))
    rows.append({'recommend_circle':recommend_levels(build_shape('circle',16),16,16,16,'2d',80)})
    (HERE/'bench.json').write_text(json.dumps(rows,ensure_ascii=False,indent=1),encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False,indent=1))
if __name__=='__main__': main()
