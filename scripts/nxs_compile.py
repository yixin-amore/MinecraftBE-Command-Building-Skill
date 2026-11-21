#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NXS raster -> commands + budget; selector mask metadata for simple shapes."""
from __future__ import annotations
import json, math, argparse
from dataclasses import dataclass, field
from pathlib import Path
from nxs_ir import (NxsRaster, Shape, Box, Sphere, Cylinder, Cone, Capsule, Torus,
                    Plane, PolygonPrism, ExtrudedCurve, Union, Intersect, Subtract,
                    Transform, Mirror, Array, Repeat)

@dataclass
class NxsBudget:
    points: int
    commands: int
    chars: int
    cb: int
    ticks: int
    max_chars: int = 32500
    max_cb: int = 80
    issues: list = field(default_factory=list)
    def to_dict(self):
        return {'points':self.points,'commands':self.commands,'chars':self.chars,
                'cb':self.cb,'ticks':self.ticks,'max_chars':self.max_chars,
                'max_cb':self.max_cb,'issues':self.issues,'ok':not self.issues}

def selector_mask(shape):
    """Return a simple selector clause dict, or None if not representable as one selection."""
    if isinstance(shape, Box):
        x,y,z=shape.center; sx,sy,sz=shape.size
        return {'x':(x-sx/2,x+sx/2),'y':(y-sy/2,y+sy/2),'z':(z-sz/2,z+sz/2)}
    if isinstance(shape, Sphere):
        return {'r':shape.radius,'center':shape.center}
    if isinstance(shape, Cylinder):
        return {'cyl':(shape.center,shape.radius,shape.height,shape.axis)}
    if isinstance(shape, Torus):
        return {'torus':(shape.center,shape.R,shape.r,shape.axis)}
    if isinstance(shape, Intersect):
        a=selector_mask(shape.a); b=selector_mask(shape.b)
        return {'and':[a,b]} if a and b else None
    if isinstance(shape, Subtract):
        a=selector_mask(shape.a); b=selector_mask(shape.b)
        return {'and':[a,{'not':b}]} if a and b else None
    if isinstance(shape, Union):
        a=selector_mask(shape.a); b=selector_mask(shape.b)
        return {'or':[a,b]} if a and b else None
    return None

def if_unless_clauses(shape):
    """Simple selector clauses; not a full arbitrary CSG-to-selector compiler."""
    def box_clauses(b):
        x,y,z=b.center; sx,sy,sz=b.size
        return ['x=%g'%(x-sx/2),'dx=%g'%sx,'y=%g'%(y-sy/2),'dy=%g'%sy,'z=%g'%(z-sz/2),'dz=%g'%sz]
    if isinstance(shape, Box): return {'if':box_clauses(shape),'unless':[]}
    if isinstance(shape, Sphere): return {'if':['r=%g'%shape.radius,'x=%g'%shape.center[0],'y=%g'%shape.center[1],'z=%g'%shape.center[2]],'unless':[]}
    if isinstance(shape, Cylinder):
        x,y,z=shape.center
        return {'if':['r=%g'%shape.radius,'x=%g'%x,'y=%g'%(y-shape.height/2),'dy=%g'%shape.height,'z=%g'%z],'unless':[]}
    if isinstance(shape, Intersect):
        a=if_unless_clauses(shape.a); b=if_unless_clauses(shape.b)
        return {'if':(a or {}).get('if',[])+(b or {}).get('if',[]),
                'unless':(a or {}).get('unless',[])+(b or {}).get('unless',[])} if a and b else None
    if isinstance(shape, Subtract):
        a=if_unless_clauses(shape.a); b=if_unless_clauses(shape.b)
        return {'if':(a or {}).get('if',[]),'unless':(b or {}).get('if',[])} if a and b else None
    return None

def compile_commands(raster: NxsRaster):
    cells=raster.sample()
    cmds=[]; points=[]
    mat=raster.material
    for (x,y,z,size) in cells:
        wx=raster.origin[0]+x; wy=raster.origin[1]+y; wz=raster.origin[2]+z
        if raster.emit=='setblock':
            cmds.append('setblock %.3f %.3f %.3f %s'%(wx,wy,wz,mat))
        elif raster.emit=='fill':
            h=size/2
            cmds.append('fill %.3f %.3f %.3f %.3f %.3f %.3f %s'%(wx-h,wy-h,wz-h,wx+h,wy+h,wz+h,mat))
        else:
            cmds.append('particle %s %.3f %.3f %.3f'%(mat,wx,wy,wz))
        points.append({'x':wx,'y':wy,'z':wz,'size':size})
    return cells,points,cmds

def compile_raster(raster: NxsRaster):
    cells,points,cmds=compile_commands(raster)
    chars=sum(len(c)+1 for c in cmds)
    cb=len(cmds)
    ticks=max(0,math.ceil(len(cmds)/20))
    issues=[]
    if chars>32500: issues.append('command chars %d > 32500'%chars)
    if cb>80: issues.append('estimated command blocks %d > 80'%cb)
    if len(cells)>raster.max_cells: issues.append('cells %d > max_cells %d'%(len(cells),raster.max_cells))
    b=NxsBudget(len(cells),len(cmds),chars,cb,ticks,issues=issues)
    return {'raster':{'width':raster.width,'height':raster.height,'depth':raster.depth,
                       'levels':raster.levels,'axes':raster.axes,'emit':raster.emit,
                       'material':raster.material,'origin':list(raster.origin)},
            'selector':selector_mask(raster.shape),'condition':if_unless_clauses(raster.shape),
            'points':points,'commands':cmds,'budget':b.to_dict()}

def build_shape(kind,size):
    c=(0,0,0); s=size
    if kind=='circle': return Cylinder(c,s/2,0.5,'y')
    if kind=='ring': return Subtract(Cylinder(c,s/2,0.5,'y'),Cylinder(c,s/2*0.62,0.5,'y'))
    if kind=='square': return Box(c,(s,0.5,s))
    if kind=='cross': return Union(Box(c,(s*0.22,0.5,s)),Box(c,(s,0.5,0.22)))
    if kind=='cube': return Box(c,(s,s,s))
    if kind=='sphere': return Sphere(c,s/2)
    if kind=='torus': return Torus(c,s/2,s/5,'y')
    raise SystemExit('unknown shape '+kind)

def recommend_levels(shape, width=16, height=16, depth=16, axes='3d', max_cb=80, max_levels=8):
    """Largest level whose absolute command count fits max_cb."""
    best=None; rows=[]
    for lv in range(1,max_levels+1):
        r=NxsRaster(width=width,height=height,depth=depth,levels=lv,shape=shape,axes=axes)
        art=compile_raster(r); b=art['budget']
        rows.append({'levels':lv,'points':b['points'],'cb':b['cb'],'ok':b['ok']})
        if b['cb']<=max_cb: best=lv
    return {'recommended':best,'max_cb':max_cb,'rows':rows}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--shape',default='circle')
    ap.add_argument('--size',type=float,default=16); ap.add_argument('--levels',type=int,default=3)
    ap.add_argument('--emit',default='particle',choices=['particle','setblock','fill'])
    ap.add_argument('--material',default='minecraft:balloon_gas_particle')
    ap.add_argument('--out',default=None); ap.add_argument('--axes',default=None)
    ap.add_argument('--recommend-cb',type=int,default=None)
    a=ap.parse_args(); shape=build_shape(a.shape,a.size)
    axes=a.axes or ('2d' if a.shape in ('circle','ring','square','cross') else '3d')
    r=NxsRaster(width=a.size,height=1 if axes=='2d' else a.size,depth=a.size,levels=a.levels,
               shape=shape,material=a.material,emit=a.emit,axes=axes)
    if a.recommend_cb:
        rec=recommend_levels(shape,a.size,a.size,a.size,axes,a.recommend_cb)
        print(json.dumps({'recommend':rec},ensure_ascii=False,indent=1)); return
    art=compile_raster(r)
    print(json.dumps({'shape':a.shape,'axes':axes,'points':art['budget']['points'],
                      'commands':art['budget']['commands'],'chars':art['budget']['chars'],
                      'budget':art['budget']},ensure_ascii=False,indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(art,ensure_ascii=False,indent=1),encoding='utf-8')

if __name__=='__main__': main()
