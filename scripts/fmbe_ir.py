#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FMBE model IR + validation (original, no APK code copied)."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import fmbe_matrix as M

VAR_NAMES = ('xpos','ypos','zpos','xrot','yrot','zrot','scale',
             'extend_scale','extend_xrot','extend_yrot',
             'xbasepos','ybasepos','zbasepos')
DEFAULT_VARS = dict(M.DEFAULT)
ROTATE_KEYS = {'rotatex','rotatey','rotatez'}

class FmbeValidationError(ValueError):
    def __init__(self, issues, warnings=None):
        self.issues = list(issues); self.warnings = list(warnings or [])
        super().__init__('FMBE validation failed: ' + '; '.join(self.issues))

@dataclass
class FmbeExport:
    prefix: str = ('execute positioned ~-1.5~~-0.5 run playanimation '
                   '@e[x=~,z=~,y=~,dx=1,dy=0,dz=0] animation.player.attack.positions _ 0')
    suffix: str = '"{command}" {name}'
    def command(self, block: 'FmbeBlock') -> str:
        parts = []
        for k in VAR_NAMES:
            parts.append('v.%s=%g;' % (k, _num(block.vars.get(k, DEFAULT_VARS[k]))))
        payload = ' '.join(parts)
        suffix = self.suffix.replace('{command}', payload).replace(
            '{name}', block.name or block.id)
        return self.prefix + ' ' + suffix

@dataclass
class FmbeBlock:
    id: str
    name: str = ''
    item: str = 'minecraft:stone'
    offset: Tuple[float,float,float] = (0,0,0)
    vars: Dict[str,float] = field(default_factory=dict)
    def __post_init__(self):
        if not self.name: self.name = self.id
        self.vars = {k: _num(v) for k,v in self.vars.items() if k in VAR_NAMES}
    def merged(self, extra=None):
        d = dict(DEFAULT_VARS); d.update(self.vars); d.update(extra or {})
        return FmbeBlock(self.id, self.name, self.item, self.offset, d)
    def vertices(self): return M.vertices(self)
    def matrix4Rows(self): return M.matrix_rows(self)

@dataclass
class Keyframe:
    tick: int
    vars: Dict[str,float] = field(default_factory=dict)

@dataclass
class FmbeAnimation:
    block_id: str
    duration: int
    keyframes: List[Keyframe] = field(default_factory=list)
    loop: bool = False

@dataclass
class FmbeBoneGroup:
    id: str
    members: List[str] = field(default_factory=list)

@dataclass
class FmbeCarrier:
    enabled: bool = True
    entity: str = 'fox'
    display_score: str = 'fmbe_display'

@dataclass
class FmbeModel:
    name: str
    blocks: List[FmbeBlock] = field(default_factory=list)
    animations: List[FmbeAnimation] = field(default_factory=list)
    groups: List[FmbeBoneGroup] = field(default_factory=list)
    export: FmbeExport = field(default_factory=FmbeExport)
    carrier: Optional[FmbeCarrier] = None
    origin: Tuple[int,int,int] = (0,0,0)

    def block(self, bid):
        for b in self.blocks:
            if b.id == bid: return b
        return None

    def validate(self):
        issues=[]; warnings=[]
        if not self.name: warnings.append('model name is empty')
        if not self.blocks: issues.append('model has no blocks')
        ids=set()
        for b in self.blocks:
            if b.id in ids: issues.append('duplicate block id: '+b.id)
            ids.add(b.id)
            if b.item and not b.item.startswith('minecraft:'):
                warnings.append('item without minecraft: prefix: '+b.item)
            for k,val in b.vars.items():
                if k in ROTATE_KEYS: issues.append('%s: rotatex/y/z not supported in this FMBE version'%b.id)
                if k not in VAR_NAMES: issues.append('%s: unknown var %s'%(b.id,k))
                if not isinstance(val,(int,float)) or not math.isfinite(float(val)):
                    issues.append('%s: non-finite var %s'%(b.id,k))
            for k in ('scale','extend_scale'):
                if float(b.vars.get(k, DEFAULT_VARS[k])) <= 0:
                    issues.append('%s: %s must be > 0'%(b.id,k))
            try:
                vs=list(b.vertices().values())
                flat=[c for p in vs for c in p]
                if not all(math.isfinite(float(c)) for c in flat): issues.append(b.id+': non-finite vertex')
            except Exception as e: issues.append('%s: vertices failed: %s'%(b.id,e))
        # unique part origins (BDX command blocks must not overlap)
        seen={}
        for b in self.blocks:
            if b.offset in seen: issues.append('duplicate part offset: %s / %s'%(seen[b.offset],b.id))
            seen[b.offset]=b.id
        for a in self.animations:
            if a.block_id not in ids: issues.append('animation for unknown block: '+a.block_id)
            if a.duration <= 0: issues.append('animation %s duration <= 0'%a.block_id)
            ticks=[]
            for kf in a.keyframes:
                if kf.tick < 0 or kf.tick > a.duration: issues.append('%s: keyframe tick %s outside 0..%s'%(a.block_id,kf.tick,a.duration))
                if kf.tick in ticks: issues.append('%s: duplicate keyframe tick %s'%(a.block_id,kf.tick))
                ticks.append(kf.tick)
                for k in kf.vars:
                    if k in ROTATE_KEYS: issues.append('%s: keyframe uses %s (not supported)'%(a.block_id,k))
                    if k not in VAR_NAMES: issues.append('%s: keyframe unknown var %s'%(a.block_id,k))
            if a.keyframes and ticks != sorted(ticks): issues.append('%s: keyframes not sorted'%a.block_id)
        for g in self.groups:
            if g.id in [x.id for x in self.groups] and [x.id for x in self.groups].count(g.id)>1:
                issues.append('duplicate group id: '+g.id)
            if not g.members: warnings.append('group %s has no members'%g.id)
            for m in g.members:
                if m not in ids: issues.append('group %s: unknown member %s'%(g.id,m))
        return {'ok':not issues,'issues':issues,'warnings':warnings,
                'blocks':len(self.blocks),'animations':len(self.animations),'groups':len(self.groups)}

    def require_valid(self):
        r=self.validate()
        if not r['ok']: raise FmbeValidationError(r['issues'],r['warnings'])
        return r

    @classmethod
    def from_dict(cls,d):
        blocks=[]
        for x in d.get('blocks',[]):
            blocks.append(FmbeBlock(
                id=str(x['id']), name=str(x.get('name','')), item=str(x.get('item','minecraft:stone')),
                offset=tuple(x.get('offset',[0,0,0])), vars=dict(x.get('vars',{}))))
        anims=[]
        for a in d.get('animations',[]):
            anims.append(FmbeAnimation(str(a['block_id']), int(a['duration']),
                [Keyframe(int(k['tick']),dict(k.get('vars',{}))) for k in a.get('keyframes',[])],
                bool(a.get('loop',False))))
        groups=[FmbeBoneGroup(str(g['id']),list(g.get('members',[]))) for g in d.get('groups',[])]
        carrier=None
        if d.get('carrier') is not None:
            c=d['carrier']; carrier=FmbeCarrier(bool(c.get('enabled',True)),str(c.get('entity','fox')),str(c.get('display_score','fmbe_display')))
        exp=d.get('export',{})
        return cls(str(d.get('name','model')),blocks,anims,groups,
                   FmbeExport(exp.get('prefix',FmbeExport.prefix),exp.get('suffix',FmbeExport.suffix)) if exp else FmbeExport(),
                   carrier,tuple(d.get('origin',[0,0,0])))

def _num(v):
    if isinstance(v, bool): return int(v)
    if isinstance(v, int): return v
    try:
        f=float(v)
        return int(f) if f.is_integer() else f
    except Exception:
        return 0
