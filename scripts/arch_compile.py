#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Architecture DSL MVP: semantic builder -> voxels -> BDX.
Original implementation; no GPL code copied.
"""
from __future__ import annotations
import json, math, sys
from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from bdxgen import BuildBlock, write_build_bdx

@dataclass
class Palette:
    stone: str='stone_bricks'
    dark: str='deepslate_bricks'
    trim: str='polished_deepslate'
    light: str='calcite'
    roof: str='deepslate_tiles'
    copper: str='oxidized_copper'
    glass: str='blue_stained_glass'
    glass2: str='purple_stained_glass'
    gold: str='gold_block'
    wood: str='dark_oak_planks'
    iron: str='iron_bars'
    water: str='water'
    grass: str='grass_block'
    leaves: str='dark_oak_leaves'
    log: str='dark_oak_log'
    lantern: str='lantern'
    def get(self, role):
        if role in self.__dict__: return getattr(self,role)
        return role

class ArchBuilder:
    def __init__(self, width, depth, palette=None, ground=0):
        self.w=width; self.d=depth; self.p=palette or Palette(); self.ground=ground
        self.V={}
    # ---------- low level ----------
    def put(self,x,y,z,b): self.V[(int(x),int(y),int(z))]=self.p.get(b)
    def box(self,x0,x1,y0,y1,z0,z1,b):
        x0,x1=sorted((int(x0),int(x1))); y0,y1=sorted((int(y0),int(y1))); z0,z1=sorted((int(z0),int(z1)))
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1): self.put(x,y,z,b)
    def ring(self,x0,x1,y0,y1,z0,z1,b,t=1):
        x0,x1=sorted((int(x0),int(x1))); z0,z1=sorted((int(z0),int(z1)))
        for x in range(x0,x1+1):
            for z in range(z0,z1+1):
                if min(x-x0,x1-x,z-z0,z1-z)<t:
                    for y in range(int(y0),int(y1)+1): self.put(x,y,z,b)
    def carve(self,x0,x1,y0,y1,z0,z1):
        for x in range(min(x0,x1),max(x0,x1)+1):
            for y in range(min(y0,y1),max(y0,y1)+1):
                for z in range(min(z0,z1),max(z0,z1)+1): self.V.pop((x,y,z),None)
    # ---------- architecture ----------
    def site(self, floor='grass', water=True):
        if water: self.box(0,self.w,0,0,0,self.d,'water')
        self.box(2,self.w-2,1,1,2,self.d-2,floor)
        self.box(2,self.w-2,0,0,2,self.d-2,'stone')
    def walls(self,x0,x1,z0,z1,y0,y1,role='stone',t=2):
        self.box(x0,x1,y0,y1,z0,z0+t-1,role); self.box(x0,x1,y0,y1,z1-t+1,z1,role)
        self.box(x0,x0+t-1,y0,y1,z0,z1,role); self.box(x1-t+1,x1,y0,y1,z0,z1,role)
    def floor(self,x0,x1,z0,z1,y,role='trim'): self.box(x0,x1,y,y,z0,z1,role)
    def crenellate(self,x0,x1,z0,z1,y,role='trim',step=2,t=1):
        for x in range(x0,x1+1,step):
            for z in (z0,z1): self.box(x,x,y,y+1,z,z,role)
        for z in range(z0,z1+1,step):
            for x in (x0,x1): self.box(x,x,y,y+1,z,z,role)
    def buttress(self,x,z,y0,y1,dirx=0,dirz=-1,role='dark'):
        # 2x2 projection + sloped cap + pinnacle
        bx=x if dirx==0 else x+dirx*2
        bz=z if dirz==0 else z+dirz*2
        self.box(min(x,bx),max(x,bx),y0,y1,min(z,bz),max(z,bz),role)
        for i in range(3):
            self.box(x-1+i,x+1-i,y1+i,y1+i,z-1,z+1,'trim') if dirx or dirz else None
        self.box(x,x,y1+3,y1+8,z,z,'trim'); self.put(x,y1+9,z,'gold')
    def lancet_z(self,z,cx,y0,h,w=1,glass='glass',role='trim'):
        # recessed 2 deep, pointed top
        self.carve(cx-w,cx+w,y0,y0+h-1,z-2,z)
        self.box(cx-w,cx+w,y0,y0+h-1,z-2,z-2,'dark')
        self.box(cx-w,cx+w,y0,y0+h-1,z-2,z-2,glass)
        for k in range(w+1):
            self.box(cx-w+k,cx+w-k,y0+h+k,y0+h+k,z-1,z,role)
        self.box(cx,cx,y0,y0+h-1,z-1,z-1,role)
    def lancet_x(self,x,cz,y0,h,w=1,glass='glass',role='trim'):
        self.carve(x-2,x,y0,y0+h-1,cz-w,cz+w)
        self.box(x-2,x-2,y0,y0+h-1,cz-w,cz+w,'dark')
        self.box(x-2,x-2,y0,y0+h-1,cz-w,cz+w,glass)
        for k in range(w+1):
            self.box(x-2,x-1,y0+h+k,y0+h+k,cz-w+k,cz+w-k,role)
        self.box(x-2,x-2,y0,y0+h-1,cz,cz,role)

    def rose_z(self,z,cx,cy,r,role='trim',glass='glass',glass2='glass2'):
        for ang in range(0,360,6):
            a=math.radians(ang); self.put(cx+round(r*math.cos(a)),cy+round(r*math.sin(a)),z,role)
        for dx in range(-r+1,r):
            for dy in range(-r+1,r):
                if dx*dx+dy*dy<=(r-1)*(r-1):
                    self.put(cx+dx,cy+dy,z,glass if (dx+dy)%3 else glass2)
        for ang in range(0,360,30):
            a=math.radians(ang)
            for rr in range(2,r):
                self.put(cx+round(rr*math.cos(a)),cy+round(rr*math.sin(a)),z+1,role)
        for rr in (max(2,r//2),r-2):
            for ang in range(0,360,10):
                a=math.radians(ang); self.put(cx+round(rr*math.cos(a)),cy+round(rr*math.sin(a)),z+1,role)
        self.put(cx,cy,z+1,'gold'); self.put(cx,cy,z+2,'lantern')
    def gable_roof_x(self,x0,x1,z0,z1,y0,ridge_y,role='roof'):
        for y in range(y0,ridge_y+1):
            inset=max(0,round((y-y0)*(x1-x0)/max(1,ridge_y-y0)/2))
            self.box(x0+inset,x1-inset,y,y,z0,z1,role)
        self.box((x0+x1)//2,(x0+x1)//2,ridge_y,ridge_y,z0,z1,'copper')
    def gable_roof_z(self,x0,x1,z0,z1,y0,ridge_y,role='roof'):
        for y in range(y0,ridge_y+1):
            inset=max(0,round((y-y0)*(z1-z0)/max(1,ridge_y-y0)/2))
            self.box(x0,x1,y,y,z0+inset,z1-inset,role)
    def spire(self,cx,cz,r0,y0,y1,role='copper'):
        for y in range(y0,y1+1):
            t=(y-y0)/max(1,y1-y0); r=max(0,round(r0*(1-t)))
            if r<=0: self.put(cx,y,cz,role); continue
            for ang in range(0,360,10):
                a=math.radians(ang); self.put(cx+round(r*math.cos(a)),y,cz+round(r*math.sin(a)),role)
            for ang in range(0,360,90):
                a=math.radians(ang); self.put(cx+round(r*math.cos(a)),y,cz+round(r*math.sin(a)),'trim')
        self.put(cx,y1+1,cz,'gold'); self.box(cx-2,cx+2,y1-2,y1-2,cz,cz,'gold')
    def pinnacle(self,x,z,y0,h=8,role='trim'):
        self.box(x-1,x+1,y0,y0+1,z-1,z+1,role)
        self.box(x,x,y0+2,y0+h,z,z,role)
        self.put(x,y0+h+1,z,'gold')
    def tower(self,cx,cz,r,y0,y1,spire_y,role='stone'):
        self.box(cx-r,cx+r,y0,y1,cz-r,cz+r,role)
        self.ring(cx-r,cx+r,y0,y1,cz-r,cz+r,'trim',1)
        self.crenellate(cx-r,cx+r,cz-r,cz+r,y1+1,'trim',2)
        for dx in (-r,r):
            for dz in (-r,r): self.pinnacle(cx+dx,cz+dz,y1+1,6)
        self.spire(cx,cz,r-1,y1+1,spire_y)
    # ---------- export ----------
    def stats(self):
        return {'voxels':len(self.V),'types':dict(Counter(self.V.values()).most_common()),'bounds':[
            min(x for x,y,z in self.V),min(y for x,y,z in self.V),min(z for x,y,z in self.V),
            max(x for x,y,z in self.V),max(y for x,y,z in self.V),max(z for x,y,z in self.V)]}
    def write_bdx(self,path,start=(0,0,0)):
        items=[BuildBlock(x-start[0],y-start[1],z-start[2],b) for (x,y,z),b in self.V.items()]
        write_build_bdx(items,str(path)); return len(items)
