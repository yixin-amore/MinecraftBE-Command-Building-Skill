#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small FMBE rigid-body physics IR (independent implementation).

This is not a copy of any third-party pack. It implements the same broad
concepts: a box body, quaternion orientation, gravity, ground contact and
optional spring pull.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

Vec3 = Tuple[float,float,float]
Quat = Tuple[float,float,float,float]

def vadd(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def vsub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def vmul(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def vdot(a,b): return sum(a[i]*b[i] for i in range(3))
def vlen(a): return math.sqrt(vdot(a,a))
def vnorm(a):
    l=vlen(a)
    return (0,0,0) if l<1e-12 else vmul(a,1/l)
def vcross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def qmul(a,b):
    aw,ax,ay,az=a; bw,bx,by,bz=b
    return (aw*bw-ax*bx-ay*by-az*bz,
            aw*bx+ax*bw+ay*bz-az*by,
            aw*by-ax*bz+ay*bw+az*bx,
            aw*bz+ax*by-ay*bx+az*bw)
def qnorm(q):
    l=math.sqrt(sum(x*x for x in q))
    if l<1e-12: return (1,0,0,0)
    return tuple(x/l for x in q)
def qrot(q,v):
    qw,qx,qy,qz=q; vx,vy,vz=v
    # t = 2 * cross(q.xyz, v)
    tx=2*(qy*vz-qz*vy); ty=2*(qz*vx-qx*vz); tz=2*(qx*vy-qy*vx)
    return (vx+qw*tx+(qy*tz-qz*ty),vy+qw*ty+(qz*tx-qx*tz),vz+qw*tz+(qx*ty-qy*tx))

def q_to_euler_deg(q):
    qw,qx,qy,qz=qnorm(q)
    # ZYX-ish, degrees, matching a simple FMBE pose mapping
    sinr=2*(qw*qx+qy*qz); cosr=1-2*(qx*qx+qy*qy)
    rx=math.atan2(sinr,cosr)
    sinp=2*(qw*qy-qz*qx); ry=math.asin(max(-1,min(1,sinp)))
    siny=2*(qw*qz+qx*qy); cosy=1-2*(qy*qy+qz*qz)
    rz=math.atan2(siny,cosy)
    return (math.degrees(rx),math.degrees(ry),math.degrees(rz))

@dataclass
class PlayerBox:
    min: Vec3=(-0.5,0,-0.5)
    max: Vec3=(0.5,1.8,0.5)

@dataclass
class RigidBody:
    center: Vec3=(0,10,0)
    half: Vec3=(0.5,0.5,0.5)
    velocity: Vec3=(0,0,0)
    angular: Vec3=(0,0,0)
    orientation: Quat=(1,0,0,0)
    mass: float=1.0
    restitution: float=0.3
    friction: float=0.6
    scale: float=1.0
    def normalize(self):
        self.orientation=qnorm(self.orientation)
    def corners(self):
        hx,hy,hz=self.half; out=[]
        for sx in (-1,1):
            for sy in (-1,1):
                for sz in (-1,1):
                    out.append(vadd(self.center,qrot(self.orientation,(sx*hx,sy*hy,sz*hz))))
        return out
    def aabb(self):
        pts=self.corners()
        return (tuple(min(p[i] for p in pts) for i in range(3)),
                tuple(max(p[i] for p in pts) for i in range(3)))
    def to_fmbe_vars(self):
        rx,ry,rz=q_to_euler_deg(self.orientation)
        return {'xpos':self.center[0],'ypos':self.center[1],'zpos':self.center[2],
                'xrot':rx,'yrot':ry,'zrot':rz,'scale':self.scale,
                'extend_scale':1,'extend_xrot':0,'extend_yrot':0,
                'xbasepos':0,'ybasepos':0,'zbasepos':0}

@dataclass
class PhysicsWorld:
    ground_y: float=-60.0
    gravity: float=-9.81
    dt: float=0.05
    player: Optional[PlayerBox]=None
    restitution: float=0.3
    friction: float=0.6
    steps: int=0
    def step(self, body: RigidBody, pull: Optional[Vec3]=None, pull_gain=12.0, pull_max=12.0):
        # linear + angular integration
        body.velocity=(body.velocity[0],body.velocity[1]+self.gravity*self.dt,body.velocity[2])
        body.center=vadd(body.center,vmul(body.velocity,self.dt))
        w=body.angular; q=body.orientation
        dq=(-0.5*vdot(w,q[1:])*self.dt,
            0.5*(w[0]*q[0]+w[1]*q[3]-w[2]*q[2])*self.dt,
            0.5*(w[1]*q[0]+w[2]*q[1]-w[0]*q[3])*self.dt,
            0.5*(w[2]*q[0]+w[0]*q[2]-w[1]*q[1])*self.dt)
        body.orientation=qnorm(tuple(q[i]+dq[i] for i in range(4)))
        # ground contact: lowest corner
        pts=body.corners(); min_y=min(p[1] for p in pts)
        if min_y < self.ground_y:
            pen=self.ground_y-min_y
            body.center=(body.center[0],body.center[1]+pen+0.001,body.center[2])
            if body.velocity[1]<0:
                body.velocity=(body.velocity[0],-body.velocity[1]*body.restitution,body.velocity[2])
            body.velocity=(body.velocity[0]*(1-body.friction*0.35),body.velocity[1],body.velocity[2]*(1-body.friction*0.35))
            body.angular=vmul(body.angular,0.92)
        # player AABB push-out (axis of least penetration)
        if self.player:
            lo,hi=body.aabb(); pmin,pmax=self.player.min,self.player.max
            if all(hi[i]>pmin[i] and lo[i]<pmax[i] for i in range(3)):
                depths=[min(hi[i],pmax[i])-max(lo[i],pmin[i]) for i in range(3)]
                axis=min(range(3),key=lambda i:depths[i])
                sign=1 if (lo[axis]+hi[axis])/2 >= (pmin[axis]+pmax[axis])/2 else -1
                push=depths[axis]*sign
                c=list(body.center); c[axis]+=push
                body.center=tuple(c)
                v=list(body.velocity); v[axis]=sign*abs(v[axis])*0.2
                body.velocity=tuple(v)
        # spring pull
        if pull is not None:
            d=vsub(pull,body.center); dist=vlen(d); dir=vnorm(d)
            target=vmul(dir,min(dist*pull_gain,pull_max))
            body.velocity=vadd(body.velocity,vmul(vsub(target,body.velocity),0.25))
        body.normalize(); self.steps+=1
        return body

def simulate(body: RigidBody, ticks=40, world=None, pull=None):
    world=world or PhysicsWorld()
    frames=[]
    for t in range(ticks):
        world.step(body,pull)
        frames.append({'tick':t,'vars':body.to_fmbe_vars(),'center':list(body.center),
                       'quat':list(body.orientation),'ground':world.ground_y})
    return frames
