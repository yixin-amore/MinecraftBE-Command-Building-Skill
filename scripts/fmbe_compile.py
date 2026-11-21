#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FMBE IR -> pose commands / frames / BDX command blocks."""
from __future__ import annotations
import json, sys, argparse
from dataclasses import dataclass, field
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,HERE)
from bdxgen import Block, write_bdx
import bdx_read
from fmbe_ir import FmbeModel, FmbeBlock, FmbeCarrier, FmbeExport, DEFAULT_VARS

@dataclass
class FmbeCompileResult:
    model: FmbeModel
    validation: dict
    pose_commands: list = field(default_factory=list)
    setup_commands: list = field(default_factory=list)
    frames: list = field(default_factory=list)
    bdx_path: str = ''
    readback: dict = field(default_factory=dict)

def _pos(b, origin):
    return (int(origin[0]+b.offset[0]), int(origin[1]+b.offset[1]), int(origin[2]+b.offset[2]))

def setup_commands(model, carrier=None):
    if not carrier or not carrier.enabled: return []
    out=[]
    for b in model.blocks:
        x,y,z=_pos(b,model.origin)
        out.append('summon %s %d %d %d'%(carrier.entity,x,y,z))
        out.append('execute positioned %d %d %d run replaceitem entity @e[type=%s,r=0.5,c=1] slot.weapon.mainhand 0 %s'%(x,y,z,carrier.entity,b.item))
        out.append('execute positioned %d %d %d run scoreboard players set @e[type=%s,r=0.5,c=1] %s 1'%(x,y,z,carrier.entity,carrier.display_score))
        out.append('effect @e[type=%s,scores={%s=1}] invisibility 999999 1 true'%(carrier.entity,carrier.display_score))
        out.append('effect @e[type=%s,scores={%s=1}] resistance 999999 255 true'%(carrier.entity,carrier.display_score))
    return out

def compile_model(model, bdx_path=None, write_setup=True):
    report=model.require_valid()
    result=FmbeCompileResult(model,report)
    result.pose_commands=[model.export.command(b) for b in model.blocks]
    result.setup_commands=setup_commands(model,model.carrier) if write_setup else []
    for a in model.animations:
        base=model.block(a.block_id)
        for kf in a.keyframes:
            merged=base.merged(kf.vars)
            result.frames.append({'tick':kf.tick,'block':a.block_id,
                                  'vars':dict(kf.vars),'command':model.export.command(merged)})
    if bdx_path:
        blocks=[]
        # One always-active repeat block per part, at the part origin.
        for b in model.blocks:
            x,y,z=_pos(b,model.origin)
            blocks.append(Block(x,y,z,'repeat',model.export.command(b),facing='east',
                                needs_redstone=False,custom_name=b.name or b.id))
        # Optional carrier/setup chain, placed behind the model.
        if result.setup_commands:
            sx,sy,sz=model.origin[0],model.origin[1],model.origin[2]-4
            for i,c in enumerate(result.setup_commands):
                blocks.append(Block(sx+i,sy,sz,'impulse' if i==0 else 'chain',c,
                                    facing='east',needs_redstone=(i==0),custom_name='fmbe_setup'))
        write_bdx(blocks,bdx_path); result.bdx_path=str(bdx_path)
        rows=bdx_read.read(bdx_path)
        cbs=[r for r in rows if r.get('kind')=='command_block']
        result.readback={'total':len(rows),'command_blocks':len(cbs),
                         'parts':len(model.blocks),'setup':len(result.setup_commands)}
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('model'); ap.add_argument('--out',default=None); ap.add_argument('--frames-out',default=None); ap.add_argument('--no-setup',action='store_true')
    a=ap.parse_args()
    data=json.loads(Path(a.model).read_text(encoding='utf-8'))
    model=FmbeModel.from_dict(data)
    res=compile_model(model, a.out, write_setup=not a.no_setup)
    print(json.dumps({'validation':res.validation,'pose_commands':len(res.pose_commands),
                      'setup_commands':len(res.setup_commands),'frames':len(res.frames),'bdx':res.bdx_path,'readback':res.readback},
                     ensure_ascii=False,indent=1))
    if a.out:
        print('readback: use scripts/bdx_read.py')
    if a.frames_out:
        Path(a.frames_out).write_text(json.dumps(res.frames,ensure_ascii=False,indent=1),encoding='utf-8')
        print('frames:',a.frames_out)

if __name__=='__main__': main()
