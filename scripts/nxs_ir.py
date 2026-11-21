#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NXS raster IR: shapes, CSG, transforms, adaptive lattice."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Tuple, List, Optional

def _add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def _sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _mul(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def _len(a): return math.sqrt(sum(x*x for x in a))
def _dist(a,b): return _len(_sub(a,b))

@dataclass
class Shape:
    def contains(self,p): raise NotImplementedError
    def bounds(self): raise NotImplementedError
    def selector(self):
        return None

@dataclass
class Box(Shape):
    center: Tuple[float,float,float]=(0,0,0)
    size: Tuple[float,float,float]=(1,1,1)
    def contains(self,p):
        return all(abs(p[i]-self.center[i])<=self.size[i]/2 for i in range(3))
    def bounds(self):
        return tuple(self.center[i]-self.size[i]/2 for i in range(3)), tuple(self.center[i]+self.size[i]/2 for i in range(3))
    def selector(self):
        x,y,z=self.center; sx,sy,sz=self.size
        return {'x':(x-sx/2,x+sx/2),'y':(y-sy/2,y+sy/2),'z':(z-sz/2,z+sz/2)}

@dataclass
class Sphere(Shape):
    center: Tuple[float,float,float]=(0,0,0)
    radius: float=1
    def contains(self,p): return _dist(p,self.center)<=self.radius
    def bounds(self):
        r=self.radius; return tuple(self.center[i]-r for i in range(3)),tuple(self.center[i]+r for i in range(3))
    def selector(self): return {'r':self.radius,'center':self.center}

@dataclass
class Cylinder(Shape):
    center: Tuple[float,float,float]=(0,0,0)
    radius: float=1
    height: float=2
    axis: str='y'
    def contains(self,p):
        a={'x':0,'y':1,'z':2}[self.axis]
        others=[i for i in range(3) if i!=a]
        if abs(p[a]-self.center[a])>self.height/2: return False
        return sum((p[i]-self.center[i])**2 for i in others)<=self.radius**2
    def bounds(self):
        a={'x':0,'y':1,'z':2}[self.axis]; r=self.radius; h=self.height/2
        lo=list(self.center[i]-r for i in range(3)); hi=list(self.center[i]+r for i in range(3))
        lo[a]=self.center[a]-h; hi[a]=self.center[a]+h
        return tuple(lo),tuple(hi)

@dataclass
class Cone(Shape):
    center: Tuple[float,float,float]=(0,0,0)
    radius: float=1
    height: float=2
    axis: str='y'
    def contains(self,p):
        a={'x':0,'y':1,'z':2}[self.axis]; others=[i for i in range(3) if i!=a]
        y=p[a]-self.center[a]
        if y<-self.height/2 or y>self.height/2: return False
        t=(y+self.height/2)/self.height
        return sum((p[i]-self.center[i])**2 for i in others) <= (self.radius*(1-t))**2
    def bounds(self):
        return tuple(self.center[i]-self.radius for i in range(3)),tuple(self.center[i]+self.radius for i in range(3))

@dataclass
class Capsule(Shape):
    a: Tuple[float,float,float]=(0,0,0)
    b: Tuple[float,float,float]=(0,1,0)
    radius: float=0.5
    def contains(self,p):
        ab=_sub(self.b,self.a); ap=_sub(p,self.a)
        denom=sum(x*x for x in ab)
        t=0 if denom==0 else max(0,min(1,sum(ap[i]*ab[i] for i in range(3))/denom))
        return _dist(p,_add(self.a,_mul(ab,t)))<=self.radius
    def bounds(self):
        r=self.radius
        return tuple(min(self.a[i],self.b[i])-r for i in range(3)),tuple(max(self.a[i],self.b[i])+r for i in range(3))

@dataclass
class Torus(Shape):
    center: Tuple[float,float,float]=(0,0,0)
    R: float=2
    r: float=0.5
    axis: str='y'
    def contains(self,p):
        a={'x':0,'y':1,'z':2}[self.axis]; others=[i for i in range(3) if i!=a]
        q=math.sqrt(sum((p[i]-self.center[i])**2 for i in others))
        return (q-self.R)**2+(p[a]-self.center[a])**2<=self.r**2
    def bounds(self):
        m=self.R+self.r; return tuple(self.center[i]-m for i in range(3)),tuple(self.center[i]+m for i in range(3))

@dataclass
class Plane(Shape):
    center: Tuple[float,float,float]=(0,0,0)
    normal: Tuple[float,float,float]=(0,1,0)
    thickness: float=0.5
    def contains(self,p):
        n=self.normal; ln=_len(n)
        if ln==0: return False
        return abs(sum((p[i]-self.center[i])*n[i] for i in range(3))/ln)<=self.thickness/2
    def bounds(self):
        t=self.thickness/2
        return tuple(self.center[i]-t for i in range(3)),tuple(self.center[i]+t for i in range(3))

@dataclass
class PolygonPrism(Shape):
    points: List[Tuple[float,float]]=field(default_factory=list)  # x,z polygon
    y0: float=0
    y1: float=1
    def contains(self,p):
        if not (self.y0<=p[1]<=self.y1): return False
        x,z=p[0],p[2]; inside=False; n=len(self.points)
        for i in range(n):
            x1,z1=self.points[i]; x2,z2=self.points[(i+1)%n]
            if (z1>z)!=(z2>z) and x < (x2-x1)*(z-z1)/(z2-z1)+x1: inside=not inside
        return inside
    def bounds(self):
        if not self.points: return (0,0,0),(0,0,0)
        xs=[p[0] for p in self.points]; zs=[p[1] for p in self.points]
        return (min(xs),self.y0,min(zs)),(max(xs),self.y1,max(zs))

@dataclass
class ExtrudedCurve(Shape):
    points: List[Tuple[float,float,float]]=field(default_factory=list)
    radius: float=0.3
    def contains(self,p):
        return any(_dist(p,self.points[i])<=self.radius for i in range(len(self.points))) or any(
            _dist(p, _closest_on_segment(p,self.points[i],self.points[i+1]))<=self.radius
            for i in range(len(self.points)-1))
    def bounds(self):
        r=self.radius
        return tuple(min(p[i] for p in self.points)-r for i in range(3)),tuple(max(p[i] for p in self.points)+r for i in range(3))

def _closest_on_segment(p,a,b):
    ab=_sub(b,a); ap=_sub(p,a); d=sum(x*x for x in ab)
    if d==0: return a
    t=max(0,min(1,sum(ap[i]*ab[i] for i in range(3))/d))
    return _add(a,_mul(ab,t))

@dataclass
class Union(Shape):
    a: Shape; b: Shape
    def contains(self,p): return self.a.contains(p) or self.b.contains(p)
    def bounds(self):
        la,ha=self.a.bounds(); lb,hb=self.b.bounds()
        return tuple(min(la[i],lb[i]) for i in range(3)),tuple(max(ha[i],hb[i]) for i in range(3))
@dataclass
class Intersect(Shape):
    a: Shape; b: Shape
    def contains(self,p): return self.a.contains(p) and self.b.contains(p)
    def bounds(self):
        la,ha=self.a.bounds(); lb,hb=self.b.bounds()
        return tuple(max(la[i],lb[i]) for i in range(3)),tuple(min(ha[i],hb[i]) for i in range(3))
@dataclass
class Subtract(Shape):
    a: Shape; b: Shape
    def contains(self,p): return self.a.contains(p) and not self.b.contains(p)
    def bounds(self): return self.a.bounds()

@dataclass
class Transform(Shape):
    shape: Shape
    translate: Tuple[float,float,float]=(0,0,0)
    rotate: Tuple[float,float,float]=(0,0,0)
    scale: float=1.0
    def _inv(self,p):
        x,y,z=p; tx,ty,tz=self.translate; x-=tx; y-=ty; z-=tz
        s=self.scale or 1; x/=s; y/=s; z/=s
        rx,ry,rz=[math.radians(a) for a in self.rotate]
        # inverse rotation z,y,x
        c,sn=math.cos(-rz),math.sin(-rz); x,y=x*c-y*sn,x*sn+y*c
        c,sn=math.cos(-ry),math.sin(-ry); x,z=x*c+z*sn,-x*sn+z*c
        c,sn=math.cos(-rx),math.sin(-rx); y,z=y*c-z*sn,y*sn+z*c
        return (x,y,z)
    def contains(self,p): return self.shape.contains(self._inv(p))
    def bounds(self):
        lo,hi=self.shape.bounds(); pts=[]
        for x in (lo[0],hi[0]):
            for y in (lo[1],hi[1]):
                for z in (lo[2],hi[2]): pts.append(self._fwd((x,y,z)))
        return tuple(min(p[i] for p in pts) for i in range(3)),tuple(max(p[i] for p in pts) for i in range(3))
    def _fwd(self,p):
        x,y,z=p; s=self.scale or 1; x*=s; y*=s; z*=s
        rx,ry,rz=[math.radians(a) for a in self.rotate]
        c,sn=math.cos(rx),math.sin(rx); y,z=y*c-z*sn,y*sn+z*c
        c,sn=math.cos(ry),math.sin(ry); x,z=x*c+z*sn,-x*sn+z*c
        c,sn=math.cos(rz),math.sin(rz); x,y=x*c-y*sn,x*sn+y*c
        return (x+self.translate[0],y+self.translate[1],z+self.translate[2])

@dataclass
class Mirror(Shape):
    shape: Shape
    axis: str='x'
    plane: float=0
    def contains(self,p):
        if self.shape.contains(p): return True
        a={'x':0,'y':1,'z':2}[self.axis]; q=list(p); q[a]=2*self.plane-q[a]
        return self.shape.contains(tuple(q))
    def bounds(self):
        lo,hi=self.shape.bounds(); a={'x':0,'y':1,'z':2}[self.axis]
        lo=list(lo); hi=list(hi); lo[a]=min(lo[a],2*self.plane-hi[a]); hi[a]=max(hi[a],2*self.plane-lo[a])
        return tuple(lo),tuple(hi)

@dataclass
class Array(Shape):
    shape: Shape
    count: Tuple[int,int,int]=(2,1,1)
    offset: Tuple[float,float,float]=(0,0,0)
    def contains(self,p):
        for x in range(self.count[0]):
            for y in range(self.count[1]):
                for z in range(self.count[2]):
                    if self.shape.contains((p[0]-x*self.offset[0],p[1]-y*self.offset[1],p[2]-z*self.offset[2])): return True
        return False
    def bounds(self):
        lo,hi=self.shape.bounds(); off=tuple((self.count[i]-1)*self.offset[i] for i in range(3))
        return tuple(min(lo[i],lo[i]+off[i]) for i in range(3)),tuple(max(hi[i],hi[i]+off[i]) for i in range(3))

@dataclass
class Repeat(Shape):
    shape: Shape
    period: Tuple[float,float,float]=(1,1,1)
    count: Tuple[int,int,int]=(2,1,1)
    def contains(self,p):
        for x in range(self.count[0]):
            for y in range(self.count[1]):
                for z in range(self.count[2]):
                    if self.shape.contains((p[0]-x*self.period[0],p[1]-y*self.period[1],p[2]-z*self.period[2])): return True
        return False
    def bounds(self): return Array(self.shape,self.count,self.period).bounds()

@dataclass
class NxsRaster:
    width: float=16
    height: float=16
    depth: float=16
    levels: int=3
    shape: Shape=field(default_factory=Sphere)
    material: str='minecraft:balloon_gas_particle'
    emit: str='particle'
    origin: Tuple[float,float,float]=(0,0,0)
    axes: str='3d'
    surface_only: bool=False
    max_cells: int=4096
    def sample(self):
        dim=2 if self.axes=='2d' else 3
        lo,hi=self.shape.bounds()
        root=max(max(0.001,hi[i]-lo[i]) for i in range(3)) if dim==3 else max(max(0.001,hi[0]-lo[0]),max(0.001,hi[2]-lo[2]))
        cells=[]; limit=max(1,int(self.max_cells))
        def rec(x,y,z,size,depth):
            if len(cells)>=limit: return
            if dim==2:
                # corners + edge midpoints + center (thin rings need edge probes)
                pts=[(x+size*i,y,z+size*j) for i in (0,1) for j in (0,1)]
                pts += [(x+size/2,y,z),(x,y,z+size/2),(x+size,y,z+size/2),(x+size/2,y,z+size)]
                pts += [(x+size/2,y,z+size/2)]
                inside=[self.shape.contains(p) for p in pts]
                allin=all(inside)
            else:
                pts=[(x+size*i,y+size*j,z+size*k) for i in (0,1) for j in (0,1) for k in (0,1)]
                pts += [(x+size/2,y+size/2,z),(x+size/2,y+size/2,z+size),
                        (x+size/2,y,z+size/2),(x+size/2,y+size,z+size/2),
                        (x,y+size/2,z+size/2),(x+size,y+size/2,z+size/2)]
                # edge midpoints
                for a in (0,1):
                    for b in (0,1):
                        pts += [(x+size/2,y+size*a,z+size*b),(x+size*a,y+size/2,z+size*b),(x+size*a,y+size*b,z+size/2)]
                pts += [(x+size/2,y+size/2,z+size/2)]
                inside=[self.shape.contains(p) for p in pts]
                allin=all(inside)
            if not any(inside): return
            if depth>=max(1,int(self.levels)):
                cy = 0 if dim==2 else y+size/2
                if self.shape.contains((x+size/2,cy,z+size/2)):
                    cells.append((x+size/2, cy, z+size/2,size))
                return
            if allin and (self.surface_only or depth>=max(1,int(self.levels))-1):
                cells.append((x+size/2, 0 if dim==2 else y+size/2, z+size/2,size)); return
            if dim==2:
                h=size/2
                rec(x,y,z,h,depth+1); rec(x+h,y,z,h,depth+1); rec(x,y,z+h,h,depth+1); rec(x+h,y,z+h,h,depth+1)
            else:
                h=size/2
                for dx in (0,h):
                    for dy in (0,h):
                        for dz in (0,h): rec(x+dx,y+dy,z+dz,h,depth+1)
        start=(lo[0], 0 if dim==2 else lo[1], lo[2])
        rec(start[0],start[1],start[2],root,0)
        return cells
    def to_dict(self):
        return {'width':self.width,'height':self.height,'depth':self.depth,'levels':self.levels,
                'origin':list(self.origin),'axes':self.axes,'material':self.material,'emit':self.emit,
                'surface_only':self.surface_only,'max_cells':self.max_cells,
                'cells':[list(c) for c in self.sample()]}

# Common spelling alias: a Sweep is an extruded polyline tube.
Sweep = ExtrudedCurve
