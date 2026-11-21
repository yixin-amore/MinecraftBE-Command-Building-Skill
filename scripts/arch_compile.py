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

@dataclass
class ComponentPort:
    name: str
    pos: tuple
    normal: str = ''
    width: int = 0

@dataclass
class ComponentResult:
    component: str
    bbox: tuple
    ports: list = field(default_factory=list)
    openings: list = field(default_factory=list)
    blocks: int = 0
    def to_dict(self):
        return {'component':self.component,'bbox':list(self.bbox),
                'ports':[{'name':p.name,'pos':list(p.pos),'normal':p.normal,'width':p.width} for p in self.ports],
                'openings':list(self.openings),'blocks':self.blocks}

class ArchBuilder:
    def __init__(self, width, depth, palette=None, ground=0):
        self.w=width; self.d=depth; self.p=palette or Palette(); self.ground=ground
        self.V={}
        self.parts=[]
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

    # ---------- semantic components ----------
    def _bbox(self,x0,x1,y0,y1,z0,z1):
        x0,x1=sorted((int(x0),int(x1))); y0,y1=sorted((int(y0),int(y1))); z0,z1=sorted((int(z0),int(z1)))
        return (x0,y0,z0,x1,y1,z1)
    def _record(self,name,bbox,ports=(),openings=(),blocks=0):
        r=ComponentResult(name,bbox,list(ports),list(openings),blocks)
        self.parts.append(r); return r
    def _crenel_line_x(self,x0,x1,z,y,role='trim',step=3):
        for x in range(x0,x1+1,step): self.box(x,x,y,y+2,z,z,role)
    def _crenel_line_z(self,z0,z1,x,y,role='trim',step=3):
        for z in range(z0,z1+1,step): self.box(x,x,y,y+2,z,z,role)
    def curtain_wall(self,x0,z0,x1,z1,y0=2,height=26,thickness=4,
                     gate_center=None,gate_width=0,crenel=True,buttresses=True,
                     arrow_slits=True,role='stone'):
        """Castle curtain wall. gate cuts the south wall (z1)."""
        x0,x1=sorted((int(x0),int(x1))); z0,z1=sorted((int(z0),int(z1)))
        t=max(1,int(thickness)); y1=y0+height
        segments=[]
        segments.append((x0,x1,z0,z0+t-1))
        if gate_width and gate_center is not None:
            gl=gate_center-gate_width//2; gr=gate_center+gate_width//2
            if gl>x0: segments.append((x0,gl-1,z1-t+1,z1))
            if gr<x1: segments.append((gr+1,x1,z1-t+1,z1))
        else:
            segments.append((x0,x1,z1-t+1,z1))
        segments += [(x0,x0+t-1,z0,z1),(x1-t+1,x1,z0,z1)]
        for (a,b,c,d) in segments:
            self.box(a,b,y0,y1,c,d,role)
            if crenel:
                if c==d or b-a>=d-c:
                    self._crenel_line_x(a,b,c,y1+1)
                    if c!=d: self._crenel_line_x(a,b,d,y1+1)
                else:
                    self._crenel_line_z(c,d,a,y1+1)
                    if a!=b: self._crenel_line_z(c,d,b,y1+1)
        if buttresses:
            for x in range(x0+6,x1,12):
                self.buttress(x,z0,y0,y1-2,0,-1,'dark'); self.buttress(x,z1,y0,y1-2,0,1,'dark')
            for z in range(z0+6,z1,12):
                self.buttress(x0,z,y0,y1-2,-1,0,'dark'); self.buttress(x1,z,y0,y1-2,1,0,'dark')
        if arrow_slits:
            for x in range(x0+10,x1,14):
                for z in (z0,z1):
                    self.carve(x,x,y0+10,y0+12,z,z); self.put(x,y0+10,z,'blackstone'); self.put(x,y0+11,z,'blackstone')
        ports=[ComponentPort('corner_nw',(x0,y0,z0),'N',0),
               ComponentPort('corner_ne',(x1,y0,z0),'N',0),
               ComponentPort('corner_sw',(x0,y0,z1),'S',0),
               ComponentPort('corner_se',(x1,y0,z1),'S',0)]
        if gate_width and gate_center is not None:
            ports += [ComponentPort('gate_l',(gate_center-gate_width//2,y0,z1),'S',gate_width),
                      ComponentPort('gate_r',(gate_center+gate_width//2,y0,z1),'S',gate_width)]
        return self._record('curtain_wall',self._bbox(x0,x1,y0,y1,z0,z1),ports,
                            [('gate',gate_center,z1,gate_width)] if gate_width else [])
    def gatehouse(self,cx,cz,width=30,depth=16,y0=2,height=56,passage_width=8,
                  tower_radius=7,role='stone'):
        x0=cx-width//2; x1=cx+width//2; z0=cz-depth//2; z1=cz+depth//2
        for tx in (x0+tower_radius,x1-tower_radius):
            self.tower(tx,cz,tower_radius,y0,height,height+18,role)
        # gate passage and pointed arch frame
        gl=cx-passage_width//2; gr=cx+passage_width//2
        self.carve(gl,gr,y0,y0+18,z0,z1); self.box(gl,gr,y0,y0,z0,z1,'trim')
        for y in range(y0,y0+19):
            self.box(gl,gl,y,y,z1,z1,'trim'); self.box(gr,gr,y,y,z1,z1,'trim')
        for k in range(5): self.box(gl+k,gr-k,y0+19+k,y0+19+k,z1,z1,'trim')
        # portcullis
        for x in range(gl+2,gr,3):
            for y in range(y0+1,y0+16):
                if y%3: self.box(x,x,y,y,z1-1,z1-1,'iron')
        # bridge / steps
        self.box(gl,gr,y0-1,y0-1,z1,z1+10,'stone')
        for i in range(4): self.box(gl-i,gr+i,y0-1,y0-1,z1+i+1,z1+i+1,'trim')
        return self._record('gatehouse',self._bbox(x0,x1,y0,height+18,z0,z1+10),
            [ComponentPort('gate',(cx,y0,z1),'S',passage_width),
             ComponentPort('wall_l',(x0,y0,cz),'W',width),
             ComponentPort('wall_r',(x1,y0,cz),'E',width)])
    def keep(self,cx,cz,size=30,y0=2,height=78,spire=22,turrets=True,role='stone'):
        x0=cx-size//2; x1=cx+size//2; z0=cz-size//2; z1=cz+size//2
        self.walls(x0,x1,z0,z1,y0,height,role,2); self.floor(x0+2,x1-2,z0+2,z1-2,y0,'trim')
        self.crenellate(x0,x1,z0,z1,height+1,'trim',3)
        for y in (y0+12,y0+28,y0+44):
            for x in (cx-4,cx+4): self.lancet_z(z1,x,y,7,1)
        self.rose_z(z1,cx,y0+30,6)
        if turrets:
            for tx,tz in ((x0,z0),(x1,z0),(x0,z1),(x1,z1)):
                self.box(tx-3,tx+3,y0,height+6,tz-3,tz+3,'dark')
                self.pinnacle(tx,tz,height+7,10)
        self.spire(cx,cz,size//4,height+1,height+spire,'roof')
        return self._record('keep',self._bbox(x0,x1,y0,height+spire,z0,z1),
            [ComponentPort('entry',(cx,y0,z1),'S',6)],
            [('entry',cx,z1,6)])
    def cloister(self,x0,z0,x1,z1,y0=2,bay=5,height=7,role='stone'):
        x0,x1=sorted((int(x0),int(x1))); z0,z1=sorted((int(z0),int(z1)))
        # columns around a void
        for x in range(x0,x1+1,bay):
            for z in (z0,z1):
                self.box(x,x,y0,y0+height,z,z,'trim'); self.box(x-1,x+1,y0+height+1,y0+height+1,z-1,z+1,'light')
        for z in range(z0,z1+1,bay):
            for x in (x0,x1):
                self.box(x,x,y0,y0+height,z,z,'trim'); self.box(x-1,x+1,y0+height+1,y0+height+1,z-1,z+1,'light')
        # low roof strips
        self.box(x0,x1,y0+height+2,y0+height+2,z0,z0+1,'roof')
        self.box(x0,x1,y0+height+2,y0+height+2,z1-1,z1,'roof')
        self.box(x0,x0+1,y0+height+2,y0+height+2,z0,z1,'roof')
        self.box(x1-1,x1,y0+height+2,y0+height+2,z0,z1,'roof')
        self.box(x0+2,x1-2,y0,y0,z0+2,z1-2,'grass')
        return self._record('cloister',self._bbox(x0,x1,y0,y0+height+2,z0,z1),
            [ComponentPort('garth',(x0+2,y0,z0+2),'S',0)],
            [('garth',(x0+2,z0+2,x1-2,z1-2))])
    def bay_z(self,z,cx,y0,width=6,height=18,window=True,buttress=True,gable=False,role='stone'):
        x0=cx-width//2; x1=cx+width//2
        self.box(x0,x1,y0,y0+height,z,z+1,role)
        if window:
            self.carve(cx-1,cx+1,y0+5,y0+height-3,z-1,z+2)
            self.lancet_z(z,cx,y0+5,height-8,2)
        if buttress:
            self.box(x0-1,x0-1,y0,y0+height,z-1,z+1,'dark')
            self.box(x1+1,x1+1,y0,y0+height,z-1,z+1,'dark')
            self.pinnacle(x0-1,z,y0+height+1,6); self.pinnacle(x1+1,z,y0+height+1,6)
        if gable:
            for k in range(width//2+1):
                self.box(cx-k,cx+k,y0+height+k,y0+height+k,z,z+1,'trim')
        return self._record('bay',self._bbox(x0-1,x1+1,y0,y0+height+width//2,z-1,z+1))
    def portal_z(self,z,cx,y0=2,width=6,height=12,order=3,steps=3,role='stone'):
        x0=cx-width//2; x1=cx+width//2
        self.carve(x0,x1,y0,y0+height-1,z-2,z)
        for y in range(y0,y0+height):
            self.box(x0,x0,y,y,z-1,z,'light'); self.box(x1,x1,y,y,z-1,z,'light')
        for k in range(order):
            for yy in range(y0,y0+height-k):
                self.box(x0-k,x0-k,yy,yy,z,z,'trim'); self.box(x1+k,x1+k,yy,yy,z,z,'trim')
            for kk in range(k+1): self.box(x0-kk,x1+kk,y0+height-k+kk,y0+height-k+kk,z,z,'trim')
        self.box(x0+2,x1-2,y0,y0+height-3,z-1,z-1,'wood')
        for i in range(steps): self.box(x0-i,x1+i,y0-1,y0-1,z+i+1,z+i+1,'trim')
        return self._record('portal',self._bbox(x0-order,x1+order,y0-1,y0+height+order,z,z+steps),
            [ComponentPort('door',(cx,y0,z),'S',width)])
    def flying_buttress(self,x,z,y0,y1,dirx,role='stone'):
        bx=x+dirx*6
        self.box(x,x,y0,y1-2,z-1,z+1,'dark'); self.box(bx,bx,y0,y0+4,z-1,z+1,'dark')
        for k in range(7): self.put(x+dirx*k,y0+4+round(3*math.sin(math.pi*k/6)),z,role)
        self.pinnacle(bx,z,y0+9,8)
        return self._record('flying_buttress',self._bbox(min(x,bx),max(x,bx),y0,y1,z-1,z+1))
    def gable_face(self,x0,x1,z,y0,ridge,role='stone'):
        for y in range(y0,ridge+1):
            half=max(0,round((ridge-y)*((x1-x0)/2)/max(1,ridge-y0)))
            self.box((x0+x1)//2-half,(x0+x1)//2+half,y,y,z,z,role)
        return self._record('gable',self._bbox(x0,x1,y0,ridge,z,z))

    def dormer_z(self,x,z,y0,width=3,role='stone'):
        x0=x-width//2; x1=x+width//2
        self.box(x0,x1,y0,y0+4,z,z+3,role)
        self.carve(x0+1,x1-1,y0+1,y0+3,z+3,z+3); self.box(x0+1,x1-1,y0+1,y0+3,z+3,z+3,'glass')
        for k in range(width//2+1): self.box(x-k,x+k,y0+5+k,y0+5+k,z,z+3,'roof')
        return self._record('dormer',self._bbox(x0,x1,y0,y0+5+width//2,z,z+3))

    # ---------- export ----------
    def stats(self):
        return {'voxels':len(self.V),'types':dict(Counter(self.V.values()).most_common()),'bounds':[
            min(x for x,y,z in self.V),min(y for x,y,z in self.V),min(z for x,y,z in self.V),
            max(x for x,y,z in self.V),max(y for x,y,z in self.V),max(z for x,y,z in self.V)]}
    def write_bdx(self,path,start=(0,0,0)):
        items=[BuildBlock(x-start[0],y-start[1],z-start[2],b) for (x,y,z),b in self.V.items()]
        write_build_bdx(items,str(path)); return len(items)
