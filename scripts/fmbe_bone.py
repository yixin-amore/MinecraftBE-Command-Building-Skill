#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small 4x4 affine helpers for FMBE bone groups."""
from __future__ import annotations
import math

def ident(): return [[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]
def mul(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def trans(x,y,z):
    m=ident(); m[0][3]=x; m[1][3]=y; m[2][3]=z; return m
def scale(s):
    m=ident(); m[0][0]=m[1][1]=m[2][2]=s; return m
def rx(a):
    a=math.radians(a); c,s=math.cos(a),math.sin(a); m=ident()
    m[1][1]=c; m[1][2]=-s; m[2][1]=s; m[2][2]=c; return m
def ry(a):
    a=math.radians(a); c,s=math.cos(a),math.sin(a); m=ident()
    m[0][0]=c; m[0][2]=s; m[2][0]=-s; m[2][2]=c; return m
def rz(a):
    a=math.radians(a); c,s=math.cos(a),math.sin(a); m=ident()
    m[0][0]=c; m[0][1]=-s; m[1][0]=s; m[1][1]=c; return m
def local(offset=(0,0,0), rotation=(0,0,0), sc=1.0):
    m=trans(*offset)
    m=mul(m,rz(rotation[2])); m=mul(m,ry(rotation[1])); m=mul(m,rx(rotation[0]))
    m=mul(m,scale(sc)); return m
def point(m,p):
    v=[float(p[0]),float(p[1]),float(p[2]),1.0]
    o=[sum(m[i][k]*v[k] for k in range(4)) for i in range(4)]
    return (o[0],o[1],o[2])
def world(groups, gid, pose=None, cache=None):
    """Compose group chain. pose maps gid -> (offset,rotation,scale)."""
    if cache is not None and gid in cache: return cache[gid]
    g=groups.get(gid)
    if not g: return ident()
    po=(pose or {}).get(gid)
    off=tuple(g.offset); rot=tuple(g.rotation); sc=1.0
    if po:
        off=tuple(off[i]+po[0][i] for i in range(3))
        rot=tuple(rot[i]+po[1][i] for i in range(3)); sc=po[2]
    m=local(off,rot,sc)
    if g.parent:
        m=mul(world(groups,g.parent,pose,cache),m)
    if cache is not None: cache[gid]=m
    return m
