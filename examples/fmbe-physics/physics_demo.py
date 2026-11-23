#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent FMBE rigid-body demo: simulate, bake vars, write a delayed BDX chain."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SKILL=HERE.parents[1]; sys.path.insert(0,str(SKILL/'scripts'))
from fmbe_ir import FmbeModel
from fmbe_physics import RigidBody, PhysicsWorld, PlayerBox, simulate
from bdxgen import Block, write_bdx
import bdx_read

def main():
    model=FmbeModel.from_dict({
        'name':'fmbe-physics',
        'blocks':[{'id':'body','name':'body','item':'minecraft:calcite','offset':[0,0,0],
                   'vars':{'scale':1}}],
        'origin':[0,0,0]
    })
    body=RigidBody(center=(0,10,0),half=(.5,.5,.5),velocity=(1.5,0,-.5),
                   orientation=(0.9238795,0,0.3826834,0))
    world=PhysicsWorld(ground_y=0.0,player=PlayerBox((-1,0,-1),(1,1.8,1)))
    frames=simulate(body,80,world,pull=None)
    base=model.block('body')
    out=[]
    for f in frames:
        b=base.merged(f['vars'])
        out.append({'tick':f['tick'],'vars':f['vars'],'command':model.export.command(b)})
    (HERE/'frames.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
    # delayed timeline: impulse + chain, one frame per chain block
    blocks=[]
    for i,f in enumerate(out):
        cmd='execute positioned 0 0 0 run '+f['command']
        blocks.append(Block(i,0,0,'impulse' if i==0 else 'chain',cmd,facing='east',
                            delay=0 if i==0 else 1,needs_redstone=(i==0),custom_name='fmbe_physics'))
    write_bdx(blocks,HERE/'physics.bdx')
    rows=bdx_read.read(HERE/'physics.bdx')
    print(json.dumps({'frames':len(frames),'y_start':frames[0]['vars']['ypos'],
                      'y_end':frames[-1]['vars']['ypos'],'bdx_blocks':len(rows),
                      'readback':[r for r in rows if r.get('kind')=='command_block'][:1]},ensure_ascii=False,indent=1))
if __name__=='__main__': main()
