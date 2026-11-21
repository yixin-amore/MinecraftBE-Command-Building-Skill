#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FMBE IR -> pose/setup/frame commands, timelines, and BDX command blocks."""
from __future__ import annotations
import json, sys, argparse
from dataclasses import dataclass, field
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,HERE)
from bdxgen import Block, write_bdx
import bdx_read
from fmbe_ir import (FmbeModel, FmbeBlock, FmbeAnimation, FmbeCarrier,
                     FmbeExport, DEFAULT_VARS, VAR_NAMES)

@dataclass
class FmbeCompileResult:
    model: FmbeModel
    validation: dict
    pose_commands: list = field(default_factory=list)
    setup_commands: list = field(default_factory=list)
    frames: list = field(default_factory=list)
    timelines: list = field(default_factory=list)
    group_switches: list = field(default_factory=list)
    bdx_path: str = ''
    readback: dict = field(default_factory=dict)

def _pos(model, b):
    return model.resolved_position(b)

def _group_index(model, gid):
    for i,g in enumerate(model.groups, 1):
        if g.id == gid: return i
    return 0

def _wrap(model, b, cmd):
    x,y,z=_pos(model,b)
    # Run the FMBE prefix at the part's absolute position, so the timeline
    # command blocks can live anywhere without moving the target.
    return 'execute positioned %d %d %d run %s' % (x,y,z,cmd)

def _value_at(base, anim, var, tick):
    vals=[(kf.tick,float(kf.vars[var])) for kf in anim.keyframes if var in kf.vars]
    if not vals: return base
    if tick <= vals[0][0]: return vals[0][1]
    if tick >= vals[-1][0]: return vals[-1][1]
    if anim.interp == 'step':
        return max((v for t,v in vals if t<=tick), default=vals[0][1])
    for (t0,v0),(t1,v1) in zip(vals,vals[1:]):
        if t0 <= tick <= t1:
            if t1==t0: return v1
            u=(tick-t0)/(t1-t0)
            return v0 + (v1-v0)*u
    return vals[-1][1]

def sample_animation(model, anim):
    """Return [{tick, block, vars, command}] sampled at anim.step."""
    step=max(1,int(anim.step)); ticks=list(range(0,anim.duration+1,step))
    if ticks[-1]!=anim.duration: ticks.append(anim.duration)
    out=[]
    for b in model.animation_targets(anim):
        base=dict(DEFAULT_VARS); base.update(b.vars)
        for tick in ticks:
            vals={}
            for var in VAR_NAMES:
                if any(var in kf.vars for kf in anim.keyframes):
                    vals[var]=_value_at(base[var],anim,var,tick)
                else:
                    vals[var]=base[var]
            merged=b.merged(vals)
            out.append({'tick':tick,'block':b.id,'vars':vals,
                        'command':model.export.command(merged)})
    return out

def setup_commands(model, carrier=None):
    if not carrier or not carrier.enabled: return []
    out=['scoreboard objectives add fmbe_group dummy',
         'scoreboard objectives add fmbe_anim dummy']
    for b in model.blocks:
        x,y,z=_pos(model,b)
        gi=_group_index(model,b.group)
        out += [
            'summon %s %d %d %d'%(carrier.entity,x,y,z),
            'execute positioned %d %d %d run replaceitem entity @e[type=%s,r=0.5,c=1] slot.weapon.mainhand 0 %s'%(x,y,z,carrier.entity,b.item),
            'execute positioned %d %d %d run scoreboard players set @e[type=%s,r=0.5,c=1] %s 1'%(x,y,z,carrier.entity,carrier.display_score),
            'execute positioned %d %d %d run scoreboard players set @e[type=%s,r=0.5,c=1] fmbe_group %d'%(x,y,z,carrier.entity,gi),
            'effect @e[type=%s,scores={%s=1}] invisibility 999999 1 true'%(carrier.entity,carrier.display_score),
            'effect @e[type=%s,scores={%s=1}] resistance 999999 255 true'%(carrier.entity,carrier.display_score),
        ]
    out.append('scoreboard players set @e[scores={fmbe_group=1..}] fmbe_anim 1')
    return out

def compile_model(model, bdx_path=None, write_setup=True):
    report=model.require_valid()
    result=FmbeCompileResult(model,report)
    result.pose_commands=[model.export.command(b) for b in model.blocks]
    result.setup_commands=setup_commands(model,model.carrier) if write_setup else []
    for a in model.animations:
        frames=sample_animation(model,a)
        result.frames.extend(frames)
        # group by tick; one timeline per animation, commands for all targets
        frames_sorted=sorted(frames,key=lambda x:(x['tick'],x['block']))
        result.timelines.append({'animation':a.name or a.block_id or a.group_id,
                                 'group':a.group_id,'loop':a.loop,'frames':frames_sorted})
        if a.group_id:
            gi=_group_index(model,a.group_id); ai=len(result.group_switches)+1
            result.group_switches.append({'animation':a.name or a.group_id,
                                           'group':a.group_id,'group_index':gi,'animation_index':ai,
                                           'members':[b.id for b in model.animation_targets(a)],
                                           'switch_commands':[
                                               'scoreboard players set @e[scores={fmbe_group=%d}] fmbe_anim %d'%(gi,ai)
                                           ]})
    if bdx_path:
        blocks=[]
        # One always-active repeat block per part, at the resolved part origin.
        for b in model.blocks:
            x,y,z=_pos(model,b)
            blocks.append(Block(x,y,z,'repeat',model.export.command(b),facing='east',
                                needs_redstone=False,custom_name=b.name or b.id))
        # Setup chain behind the model.
        if result.setup_commands:
            sx,sy,sz=model.origin[0],model.origin[1],model.origin[2]-4
            for i,c in enumerate(result.setup_commands):
                blocks.append(Block(sx+i,sy,sz,'impulse' if i==0 else 'chain',c,
                                    facing='east',needs_redstone=(i==0),custom_name='fmbe_setup'))
        # One timeline chain per animation, on separate z lanes.
        for ti,tl in enumerate(result.timelines):
            x0=model.origin[0]; y0=model.origin[1]; z0=model.origin[2]-10-ti*2
            first=True; idx=0; prev_tick=0
            for fr in tl['frames']:
                delta=max(0,fr['tick']-prev_tick); prev_tick=fr['tick']
                # a frame entry is one block command; if multiple blocks share tick,
                # they are separate entries and delta becomes 0 after the first.
                b=model.block(fr['block'])
                cmd=_wrap(model,b,fr['command'])
                if tl['group']:
                    gi=_group_index(model,tl['group']); ai=next((g['animation_index'] for g in result.group_switches if g['group']==tl['group'] and g['animation']==tl['animation']),1)
                    cmd='execute if score @e[scores={fmbe_group=%d},c=1] fmbe_anim matches %d run %s'%(gi,ai,cmd)
                blocks.append(Block(x0+idx,y0,z0,'impulse' if first else 'chain',
                                    cmd,facing='east',delay=delta,
                                    needs_redstone=first,custom_name='fmbe_tl_%s'%tl['animation']))
                first=False; idx+=1
        write_bdx(blocks,bdx_path); result.bdx_path=str(bdx_path)
        rows=bdx_read.read(bdx_path)
        cbs=[r for r in rows if r.get('kind')=='command_block']
        result.readback={'total':len(rows),'command_blocks':len(cbs),
                         'parts':len(model.blocks),'setup':len(result.setup_commands),
                         'timelines':len(result.timelines),
                         'timeline_commands':sum(len(t['frames']) for t in result.timelines)}
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('model'); ap.add_argument('--out',default=None)
    ap.add_argument('--frames-out',default=None); ap.add_argument('--no-setup',action='store_true')
    a=ap.parse_args()
    data=json.loads(Path(a.model).read_text(encoding='utf-8'))
    model=FmbeModel.from_dict(data)
    res=compile_model(model, a.out, write_setup=not a.no_setup)
    print(json.dumps({'validation':res.validation,'pose_commands':len(res.pose_commands),
                      'setup_commands':len(res.setup_commands),'frames':len(res.frames),
                      'timelines':len(res.timelines),'group_switches':len(res.group_switches),
                      'bdx':res.bdx_path,'readback':res.readback},ensure_ascii=False,indent=1))
    if a.frames_out:
        Path(a.frames_out).write_text(json.dumps(res.frames,ensure_ascii=False,indent=1),encoding='utf-8')
        print('frames:',a.frames_out)

if __name__=='__main__': main()
