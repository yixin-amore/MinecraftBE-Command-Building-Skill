#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FMBE 13-var transform/vertices/export helper (distilled semantics, no APK code copied)."""
from __future__ import annotations
import math, json
from dataclasses import dataclass, field
@dataclass
class FmbeBlock:
    id: str
    vars: dict = field(default_factory=dict)
    name: str = ''
DEFAULT={'xpos':0,'ypos':0,'zpos':0,'xrot':0,'yrot':0,'zrot':0,'scale':1,
         'extend_scale':1,'extend_xrot':0,'extend_yrot':0,
         'xbasepos':0,'ybasepos':0,'zbasepos':0}
LOCAL=[('LBB',(-.5,-.5,-.5)),('RBB',(.5,-.5,-.5)),('LTB',(-.5,.5,-.5)),('RTB',(.5,.5,-.5)),
       ('LBF',(-.5,-.5,.5)),('RBF',(.5,-.5,.5)),('LTF',(-.5,.5,.5)),('RTF',(.5,.5,.5))]
def v(block,key):
    x=block.vars.get(key,DEFAULT[key])
    try: return float(x)
    except Exception: return float(DEFAULT[key])
def rotx(p,a):
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a)); x,y,z=p; return (x,y*c-z*s,y*s+z*c)
def roty(p,a):
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a)); x,y,z=p; return (x*c+z*s,y,-x*s+z*c)
def rotz(p,a):
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a)); x,y,z=p; return (x*c-y*s,x*s+y*c,z)
def apply(block,p):
    x,y,z=p
    x+=v(block,'xbasepos'); y+=v(block,'ybasepos'); z+=v(block,'zbasepos')
    y*=v(block,'extend_scale')
    x,y,z=roty((x,y,z),-v(block,'extend_yrot'))
    x,y,z=rotx((x,y,z),-v(block,'extend_xrot'))
    z*=v(block,'extend_scale')
    x,y,z=rotx((x,y,z),v(block,'extend_xrot'))
    x,y,z=roty((x,y,z),v(block,'extend_yrot'))
    s=v(block,'scale'); x*=s; y*=s; z*=s
    x,y,z=rotz((x,y,z),-v(block,'zrot'))
    x,y,z=rotx((x,y,z),v(block,'xrot'))
    x,y,z=roty((x,y,z),-v(block,'yrot'))
    return (x+v(block,'xpos'), y+v(block,'ypos'), z+v(block,'zpos'))
def vertices(block): return {n:apply(block,p) for n,p in LOCAL}
def matrix_rows(block):
    # affine matrix row-major: columns are images of x/y/z basis + translation
    o=apply(block,(0,0,0)); ex=apply(block,(1,0,0)); ey=apply(block,(0,1,0)); ez=apply(block,(0,0,1))
    cols=[tuple(ex[i]-o[i] for i in range(3)) for i in (0,0,0)]
    # build explicitly
    bx=[ex[i]-o[i] for i in range(3)]; by=[ey[i]-o[i] for i in range(3)]; bz=[ez[i]-o[i] for i in range(3)]
    return [[bx[0],by[0],bz[0],o[0]],[bx[1],by[1],bz[1],o[1]],[bx[2],by[2],bz[2],o[2]],[0,0,0,1]]
def command(block,prefix='execute positioned ~-1.5~~-0.5 run playanimation @e[x=~,z=~,y=~,dx=1,dy=0,dz=0] animation.player.attack.positions _ 0'):
    parts=[]
    for k in DEFAULT:
        parts.append(f'v.{k}={v(block,k):g};')
    return f'{prefix} "{" ".join(parts)}" {block.name or block.id}'
if __name__=='__main__':
    b=FmbeBlock('demo',{'xpos':3,'ypos':1,'zpos':-2,'scale':2,'xrot':45})
    print(json.dumps({'vertices':vertices(b),'matrix4Rows':matrix_rows(b),'command':command(b)},ensure_ascii=False,indent=1))
