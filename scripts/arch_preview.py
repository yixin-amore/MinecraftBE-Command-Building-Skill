#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preview voxels JSON from arch_compile (front / top / isometric)."""
import json, sys, argparse
from pathlib import Path
from PIL import Image, ImageDraw
COL={
 'stone_bricks':(142,139,131),'deepslate_bricks':(70,70,80),'polished_deepslate':(55,55,64),
 'calcite':(228,224,210),'deepslate_tiles':(48,47,54),'oxidized_copper':(65,145,125),
 'weathered_copper':(85,165,145),'blue_stained_glass':(55,110,200),'purple_stained_glass':(125,75,180),
 'gold_block':(230,190,60),'dark_oak_planks':(70,48,30),'iron_bars':(150,150,155),
 'water':(45,95,180),'grass_block':(84,132,62),'dark_oak_leaves':(45,95,52),'dark_oak_log':(76,55,36),
 'lantern':(245,210,120),'sea_lantern':(168,240,208),
 'deepslate_tile_stairs':(48,47,54),'deepslate_tile_slab':(58,57,64),'cut_copper_stairs':(70,150,128),
 'cut_copper':(70,150,128),'weathered_copper':(85,165,145),'glass_pane':(150,190,210),
 'glass':(150,190,210),'iron_bars':(150,150,155),'water':(45,95,180),'wet_sponge':(100,150,80)}
def col(b):
    if b in COL: return COL[b]
    x=str(b).lower()
    if 'deepslate' in x: return (58,57,66)
    if 'blackstone' in x: return (36,35,42)
    if 'copper' in x: return (72,155,132)
    if 'glass' in x: return (80,140,190)
    if 'stone' in x or 'cobble' in x or 'andesite' in x or 'calcite' in x: return (145,142,133)
    if 'water' in x: return (45,95,180)
    if 'gold' in x: return (230,190,60)
    if 'wood' in x or 'plank' in x or 'log' in x: return (90,60,38)
    if 'leaves' in x: return (45,95,52)
    if 'lantern' in x or 'light' in x: return (245,210,120)
    return (110,110,115)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('voxels'); ap.add_argument('--out',default=None); a=ap.parse_args()
    d=json.loads(Path(a.voxels).read_text(encoding='utf-8'))
    V={}
    for k,b in d.items():
        x,y,z=map(int,k.split(',')); V[(x,y,z)]=b
    outbase=Path(a.out or a.voxels).with_suffix('')
    # front from south (max z), top, iso
    front={}
    for (x,y,z),b in V.items():
        k=(x,y)
        if k not in front or z>front[k][0]: front[k]=(z,b)
    minx=min(x for x,y in front); maxx=max(x for x,y in front); miny=min(y for x,y in front); maxy=max(y for x,y in front)
    F=5; W=(maxx-minx+1)*F+30; H=(maxy-miny+1)*F+30
    img=Image.new('RGB',(W,H),(12,16,26)); dr=ImageDraw.Draw(img)
    for (x,y),(z,b) in front.items():
        px=(x-minx)*F+15; py=(maxy-y)*F+15; c=col(b)
        dr.rectangle([px,py,px+F-1,py+F-1],fill=c)
    dr.text((15,8),'front (south)',fill=(240,244,250)); img.save(str(outbase)+'-front.png')
    # top
    top={}
    for (x,y,z),b in V.items():
        k=(x,z)
        if k not in top or y>top[k][0]: top[k]=(y,b)
    minx=min(x for x,z in top);maxx=max(x for x,z in top);minz=min(z for x,z in top);maxz=max(z for x,z in top)
    S=3; img=Image.new('RGB',((maxx-minx+1)*S+30,(maxz-minz+1)*S+30),(12,16,26)); dr=ImageDraw.Draw(img)
    for (x,z),(y,b) in top.items(): dr.rectangle([(x-minx)*S+15,(z-minz)*S+15,(x-minx+1)*S+14,(z-minz+1)*S+14],fill=col(b))
    dr.text((15,8),'top',fill=(240,244,250)); img.save(str(outbase)+'-top.png')
    # iso
    S=2
    def proj(x,y,z): return ((x-z)*S,(x+z)*S//2-y*S)
    pts=list(V.items()); corners=[proj(x,y,z) for x in (min(x for x,y,z in V),max(x for x,y,z in V)) for y in (min(y for x,y,z in V),max(y for x,y,z in V)) for z in (min(z for x,y,z in V),max(z for x,y,z in V))]
    minpx=min(c[0] for c in corners)-20;maxpx=max(c[0] for c in corners)+20; minpy=min(c[1] for c in corners)-20;maxpy=max(c[1] for c in corners)+60
    W=maxpx-minpx;H=maxpy-minpy; img=Image.new('RGB',(W,H),(10,14,24)); dr=ImageDraw.Draw(img)
    ox,oy=-minpx,-minpy
    for (x,y,z),b in sorted(pts,key=lambda p:(p[0][0]+p[0][2]+p[0][1],p[0][1],p[0][0])):
        sx,sy=proj(x,y,z); sx+=ox; sy+=oy; base=col(b)
        topc=tuple(min(255,int(c*1.1)) for c in base); left=tuple(int(c*.72) for c in base); right=tuple(int(c*.5) for c in base)
        dr.polygon([(sx,sy-S//2),(sx+S//2,sy),(sx,sy+S//2),(sx-S//2,sy)],fill=topc)
        dr.polygon([(sx-S//2,sy),(sx,sy+S//2),(sx,sy+S//2+S),(sx-S//2,sy+S)],fill=left)
        dr.polygon([(sx+S//2,sy),(sx,sy+S//2),(sx+S//2,sy+S)],fill=right)
    img=img.resize((W*2,H*2),Image.Resampling.LANCZOS); dr=ImageDraw.Draw(img); dr.text((20,16),'isometric',fill=(240,244,250)); img.save(str(outbase)+'-iso.png')
    print('wrote',outbase,'front/top/iso')
if __name__=='__main__': main()
