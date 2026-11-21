#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""General NXS spatial program IR: frames, paths, radial, spiral, arrays."""
from __future__ import annotations
import math, json, argparse
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

Vec3=Tuple[float,float,float]
def add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def mul(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def rad(d): return math.radians(d)

@dataclass
class NxsFrame:
    origin: Vec3=(0,0,0)
    yaw: float=0.0
    pitch: float=0.0
    roll: float=0.0
    scale: float=1.0
    def basis(self):
        y,p=rad(self.yaw),rad(self.pitch)
        f=(-math.sin(y)*math.cos(p), math.sin(p), math.cos(y)*math.cos(p))
        r=(math.cos(y),0.0,-math.sin(y))
        u=(r[1]*f[2]-r[2]*f[1],r[2]*f[0]-r[0]*f[2],r[0]*f[1]-r[1]*f[0])
        return r,u,f
    def point(self,local:Vec3):
        r,u,f=self.basis(); s=self.scale
        return (self.origin[0]+s*(r[0]*local[0]+u[0]*local[1]+f[0]*local[2]),
                self.origin[1]+s*(r[1]*local[0]+u[1]*local[1]+f[1]*local[2]),
                self.origin[2]+s*(r[2]*local[0]+u[2]*local[1]+f[2]*local[2]))
    def moved(self,local:Vec3):
        p=self.point(local); return NxsFrame(p,self.yaw,self.pitch,self.roll,self.scale)
    def rotated(self,dyaw=0,dpitch=0,droll=0):
        return NxsFrame(self.origin,self.yaw+dyaw,self.pitch+dpitch,self.roll+droll,self.scale)
    def to_dict(self): return {'origin':list(self.origin),'yaw':self.yaw,'pitch':self.pitch,'roll':self.roll,'scale':self.scale}

@dataclass
class NxsInstance:
    frame: NxsFrame
    material: str='minecraft:stone'
    kind: str='block'
    label: str=''
    tick: int=0
    def to_dict(self):
        return {'pos':list(self.frame.origin),'yaw':self.frame.yaw,'pitch':self.frame.pitch,
                'scale':self.frame.scale,'material':self.material,'kind':self.kind,'label':self.label,'tick':self.tick}

class NxsOp:
    label='op'
    def instances(self)->List[NxsInstance]: raise NotImplementedError

@dataclass
class EmitOp(NxsOp):
    frame: NxsFrame
    material: str='minecraft:stone'
    kind: str='block'
    label: str='emit'
    def instances(self): return [NxsInstance(self.frame,self.material,self.kind,self.label)]

@dataclass
class SpiralOp(NxsOp):
    center: Vec3=(0,0,0)
    radius: float=4
    turns: float=1
    rise: float=4
    count: int=16
    material: str='minecraft:stone_bricks'
    kind: str='block'
    label: str='spiral'
    def instances(self):
        out=[]
        for i in range(self.count):
            t=i/max(1,self.count-1); a=2*math.pi*self.turns*t
            p=(self.center[0]+self.radius*math.cos(a),self.center[1]+self.rise*t,self.center[2]+self.radius*math.sin(a))
            out.append(NxsInstance(NxsFrame(p, math.degrees(a)+90,0),self.material,self.kind,self.label))
        return out

@dataclass
class RadialOp(NxsOp):
    center: Vec3=(0,0,0)
    radius: float=4
    count: int=24
    material: str='minecraft:glass'
    kind: str='block'
    label: str='radial'
    y: float=0
    def instances(self):
        out=[]
        for i in range(self.count):
            a=2*math.pi*i/self.count
            p=(self.center[0]+self.radius*math.cos(a),self.center[1]+self.y,self.center[2]+self.radius*math.sin(a))
            out.append(NxsInstance(NxsFrame(p,math.degrees(a)+90,0),self.material,self.kind,self.label))
        return out

@dataclass
class ArrayOp(NxsOp):
    frame: NxsFrame
    count: Tuple[int,int,int]=(2,1,1)
    offset: Vec3=(1,0,0)
    material: str='minecraft:stone'
    kind: str='block'
    label: str='array'
    def instances(self):
        out=[]
        for x in range(self.count[0]):
            for y in range(self.count[1]):
                for z in range(self.count[2]):
                    p=add(self.frame.origin,(x*self.offset[0],y*self.offset[1],z*self.offset[2]))
                    out.append(NxsInstance(NxsFrame(p,self.frame.yaw,self.frame.pitch),self.material,self.kind,self.label))
        return out

@dataclass
class PathOp(NxsOp):
    points: List[Vec3]
    material: str='minecraft:stone'
    kind: str='particle'
    label: str='path'
    samples: int=16
    closed: bool=False
    def instances(self):
        if len(self.points)<2: return []
        pts=self.points+([self.points[0]] if self.closed else [])
        out=[]
        for i in range(self.samples):
            t=i/max(1,self.samples-1)*(len(pts)-1); k=min(int(t),len(pts)-2); u=t-k
            p=(pts[k][0]+(pts[k+1][0]-pts[k][0])*u,pts[k][1]+(pts[k+1][1]-pts[k][1])*u,pts[k][2]+(pts[k+1][2]-pts[k][2])*u)
            out.append(NxsInstance(NxsFrame(p),self.material,self.kind,self.label))
        return out

@dataclass
class OrbitOp(NxsOp):
    center: Vec3=(0,0,0)
    radius: float=4
    height: float=2
    count: int=24
    material: str='minecraft:end_rod'
    kind: str='particle'
    label: str='orbit'
    axis: str='y'
    turns: float=1.0
    tick_step: int=0
    def instances(self):
        out=[]
        for i in range(self.count):
            a=2*math.pi*self.turns*i/self.count
            if self.axis=='y': p=(self.center[0]+self.radius*math.cos(a),self.center[1]+self.height,self.center[2]+self.radius*math.sin(a)); yaw=math.degrees(a)+90; pitch=0
            elif self.axis=='x': p=(self.center[0]+self.height,self.center[1]+self.radius*math.cos(a),self.center[2]+self.radius*math.sin(a)); yaw=0; pitch=math.degrees(a)
            else: p=(self.center[0]+self.radius*math.cos(a),self.center[1]+self.radius*math.sin(a),self.center[2]+self.height); yaw=math.degrees(a)+90; pitch=0
            out.append(NxsInstance(NxsFrame(p,yaw,pitch),self.material,self.kind,self.label,i*self.tick_step if self.tick_step else 0))
        return out

@dataclass
class BezierOp(NxsOp):
    controls: List[Vec3]
    samples: int=24
    material: str='minecraft:stone'
    kind: str='particle'
    label: str='bezier'
    def instances(self):
        if len(self.controls)==4:
            def pt(t):
                u=1-t; p0,p1,p2,p3=self.controls
                return tuple(u**3*p0[i]+3*u*u*t*p1[i]+3*u*t*t*p2[i]+t**3*p3[i] for i in range(3))
        elif len(self.controls)==3:
            def pt(t):
                u=1-t; p0,p1,p2=self.controls
                return tuple(u*u*p0[i]+2*u*t*p1[i]+t*t*p2[i] for i in range(3))
        else:
            return PathOp(self.controls,self.material,self.kind,self.label,self.samples).instances()
        return [NxsInstance(NxsFrame(pt(i/max(1,self.samples-1))),self.material,self.kind,self.label) for i in range(self.samples)]

@dataclass
class ArcOp(NxsOp):
    center: Vec3=(0,0,0)
    radius: float=4
    start_deg: float=0
    end_deg: float=90
    samples: int=16
    axis: str='y'
    height: float=0
    material: str='minecraft:stone'
    kind: str='particle'
    label: str='arc'
    def instances(self):
        out=[]
        for i in range(self.samples):
            a=math.radians(self.start_deg+(self.end_deg-self.start_deg)*i/max(1,self.samples-1))
            if self.axis=='y': p=(self.center[0]+self.radius*math.cos(a),self.center[1]+self.height,self.center[2]+self.radius*math.sin(a))
            elif self.axis=='x': p=(self.center[0]+self.height,self.center[1]+self.radius*math.cos(a),self.center[2]+self.radius*math.sin(a))
            else: p=(self.center[0]+self.radius*math.cos(a),self.center[1]+self.radius*math.sin(a),self.center[2]+self.height)
            out.append(NxsInstance(NxsFrame(p,math.degrees(a)+90,0),self.material,self.kind,self.label))
        return out

@dataclass
class BranchOp(NxsOp):
    frame: NxsFrame
    depth: int=3
    branches: int=2
    length: float=3
    angle: float=28
    decay: float=0.72
    material: str='minecraft:stone'
    kind: str='block'
    label: str='branch'
    def instances(self):
        out=[]
        def rec(f,d,L):
            if d<=0: return
            end=f.moved((0,0,L))
            out.append(NxsInstance(end,self.material,self.kind,self.label))
            for i in range(self.branches):
                yaw=(i-(self.branches-1)/2)*self.angle
                rec(f.rotated(dyaw=yaw,dpitch=-abs(yaw)*0.25),d-1,L*self.decay)
        rec(self.frame,self.depth,self.length)
        return out

    def tree(self):
        def node(f,d,L):
            n={'frame':f.to_dict(),'children':[]}
            if d<=0: return n
            end=f.moved((0,0,L))
            n['emit']={'pos':list(end.origin),'material':self.material,'kind':self.kind,'label':self.label}
            for i in range(self.branches):
                yaw=(i-(self.branches-1)/2)*self.angle
                n['children'].append(node(f.rotated(dyaw=yaw,dpitch=-abs(yaw)*0.25),d-1,L*self.decay))
            return n
        return node(self.frame,self.depth,self.length)

@dataclass
class RayOp(NxsOp):
    origin: Vec3=(0,0,0)
    direction: Vec3=(0,0,1)
    length: float=8
    step: float=0.5
    shape: object=None   # optional nxs_ir.Shape; first hit ends ray
    material: str='minecraft:end_rod'
    kind: str='particle'
    label: str='ray'
    def instances(self):
        n=max(1,int(self.length/max(1e-6,self.step))); d=self.direction; ln=math.sqrt(sum(v*v for v in d)) or 1
        d=tuple(v/ln for v in d); out=[]
        for i in range(n+1):
            p=add(self.origin,tuple(v*self.step*i for v in d))
            if self.shape is not None and not self.shape.contains(p): break
            out.append(NxsInstance(NxsFrame(p),self.material,self.kind,self.label))
        return out

@dataclass
class QueryOp(NxsOp):
    child: NxsOp
    shape: object
    mode: str='inside'   # inside | outside
    label: str='query'
    def instances(self):
        out=[]
        for x in self.child.instances():
            hit=self.shape.contains(x.frame.origin)
            if (hit and self.mode=='inside') or ((not hit) and self.mode=='outside'): out.append(x)
        return out

@dataclass
class NxsProgram:
    name: str='program'
    ops: List[NxsOp]=field(default_factory=list)
    prefix: str=''
    def add(self,op): self.ops.append(op); return self
    def instances(self):
        out=[]
        for op in self.ops: out.extend(op.instances())
        return out
    def absolute_commands(self):
        out=[]
        for x in self.instances():
            p=x.frame.origin
            if x.kind=='particle': out.append('particle %s %.3f %.3f %.3f'%(x.material,*p))
            elif x.kind=='setblock' or x.kind=='block': out.append('setblock %.3f %.3f %.3f %s'%(*p,x.material))
            elif x.kind=='entity': out.append('summon %s %.3f %.3f %.3f'%(x.material,*p))
            else: out.append('particle %s %.3f %.3f %.3f'%(x.material,*p))
        return out
    def commands(self, relative=True):
        return self.relative_commands() if relative else self.absolute_commands()
    def templates(self):
        out=[]
        for x in self.instances():
            p=x.frame.origin
            base='execute positioned %.3f %.3f %.3f rotated %.3f %.3f run '%(*p,x.frame.yaw,x.frame.pitch)
            if x.kind=='particle': cmd='particle %s ^ ^ ^'%x.material
            elif x.kind in ('setblock','block'): cmd='setblock %.3f %.3f %.3f %s'%(*p,x.material)
            elif x.kind=='entity': cmd='summon %s ^ ^ ^'%x.material
            else: cmd='particle %s ^ ^ ^'%x.material
            out.append(base+cmd)
        return out
    def relative_commands(self):
        """Default: coords are program-local offsets from the command source."""
        out=[]
        for x in self.instances():
            p=x.frame.origin
            if x.kind in ('block','setblock'): emit='setblock ~ ~ ~ %s'%x.material
            elif x.kind=='entity': emit='summon %s ~ ~ ~'%x.material
            else: emit='particle %s ^ ^ ^'%x.material
            out.append('execute positioned ~%.3f ~%.3f ~%.3f rotated %.3f %.3f run %s'%(p[0],p[1],p[2],x.frame.yaw,x.frame.pitch,emit))
        return out
    def timeline(self):
        ticks={}
        for x in self.instances():
            ticks.setdefault(x.tick,[]).append(x)
        return {str(t):[{'pos':list(x.frame.origin),'label':x.label,'kind':x.kind} for x in xs] for t,xs in sorted(ticks.items())}
    def lower_tree(self):
        children=[]; trees=[]
        for op in self.ops:
            if isinstance(op,BranchOp): trees.append({'op':'branch','tree':op.tree()})
            else:
                for x in op.instances():
                    children.append({'frame':x.frame.to_dict(),'command':('setblock ~ ~ ~ %s'%x.material) if x.kind in ('block','setblock') else ('particle %s ^ ^ ^'%x.material),'label':x.label,'tick':x.tick})
        return {'name':self.name,'root':NxsFrame().to_dict(),'ops':trees,'children':children}
    def to_dict(self):
        cmds=self.commands()
        return {'name':self.name,'instances':[x.to_dict() for x in self.instances()],
                'commands':cmds,'absolute_commands':self.absolute_commands(),
                'templates':self.templates(),'relative':self.relative_commands(),
                'lower_tree':self.lower_tree(),'timeline':self.timeline(),
                'budget':{'instances':len(cmds),'commands':len(cmds),'chars':sum(len(c)+1 for c in cmds)}}

def demo():
    p=NxsProgram('nxs-program-demo')
    p.add(SpiralOp(center=(0,0,0),radius=4,turns=1,rise=6,count=24,material='minecraft:stone_bricks',kind='block'))
    p.add(RadialOp(center=(0,10,0),radius=5,count=24,material='minecraft:glass',kind='block'))
    p.add(OrbitOp(center=(0,20,0),radius=6,height=0,count=24,material='minecraft:end_rod',kind='particle'))
    return p
if __name__=='__main__':
    p=demo(); print(json.dumps(p.to_dict(),ensure_ascii=False,indent=1)[:2000])
