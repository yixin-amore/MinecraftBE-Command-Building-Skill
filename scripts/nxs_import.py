#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PNG / simple SVG -> NXS Shape."""
from __future__ import annotations
import re, xml.etree.ElementTree as ET
from pathlib import Path
from nxs_ir import BitmapMask, Box, Cylinder, PolygonPrism, Union, Shape

def from_png(path, threshold=128, cell=1.0, alpha=True, invert=False):
    from PIL import Image
    im=Image.open(path).convert('RGBA')
    w,h=im.size; px=im.load(); rows=[]
    for z in range(h):
        row=[]
        for x in range(w):
            r,g,b,a=px[x,z]
            if alpha and a>0:
                on = a>=threshold
            else:
                lum=(r+g+b)/3
                on = lum>=threshold
            row.append((not on) if invert else on)
        rows.append(row)
    return BitmapMask(rows,cell=cell,x0=0,z0=0,y0=0,y1=0.5)

def from_svg(path, scale=1.0, thickness=0.5):
    root=ET.parse(path).getroot()
    shapes=[]
    def f(v,default=0):
        if v is None: return default
        m=re.match(r'-?[\d.]+',str(v)); return float(m.group(0))*scale if m else default
    def add(el):
        tag=el.tag.split('}')[-1]
        if tag=='rect':
            x=f(el.get('x')); y=f(el.get('y')); w=f(el.get('width')); h=f(el.get('height'))
            shapes.append(Box((x+w/2,0,-y-h/2),(w,thickness,h)))
        elif tag in ('circle','ellipse'):
            cx=f(el.get('cx')); cy=f(el.get('cy')); rx=f(el.get('r') or el.get('rx')); ry=f(el.get('r') or el.get('ry'))
            shapes.append(Cylinder((cx,0,-cy),max(rx,ry),thickness,'y'))
        elif tag=='polygon':
            pts=str(el.get('points','')).replace(',',' ').split(); nums=list(map(float,pts))
            poly=[(nums[i]*scale,-nums[i+1]*scale) for i in range(0,len(nums)-1,2)]
            if len(poly)>=3: shapes.append(PolygonPrism(poly,-thickness/2,thickness/2))
        for child in list(el): add(child)
    add(root)
    if not shapes: raise ValueError('no supported SVG shapes (rect/circle/ellipse/polygon)')
    s=shapes[0]
    for n in shapes[1:]: s=Union(s,n)
    return s
