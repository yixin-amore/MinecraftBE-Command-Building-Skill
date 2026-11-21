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
    group: Optional[str] = None
    def __post_init__(self):
        if not self.name: self.name = self.id
        self.vars = {k: _num(v) for k,v in self.vars.items() if k in VAR_NAMES}
    def merged(self, extra=None):
        d = dict(DEFAULT_VARS); d.update(self.vars); d.update(extra or {})
        return FmbeBlock(self.id, self.name, self.item, self.offset, d, self.group)
    def vertices(self): return M.vertices(self)
    def matrix4Rows(self): return M.matrix_rows(self)

@dataclass
class Keyframe:
    tick: int
    vars: Dict[str,float] = field(default_factory=dict)

@dataclass
class FmbeAnimation:
    block_id: Optional[str] = None
    duration: int = 1
    keyframes: List[Keyframe] = field(default_factory=list)
    loop: bool = False
    group_id: Optional[str] = None
    name: str = ''
    interp: str = 'linear'          # linear | step
    step: int = 1                   # sample every N ticks

@dataclass
class FmbeBoneGroup:
    id: str
    members: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    offset: Tuple[float,float,float] = (0,0,0)
    rotation: Tuple[float,float,float] = (0,0,0)   # x,y,z degrees

@dataclass
class GroupKeyframe:
    tick: int
    offset: Tuple[float,float,float] = (0,0,0)
    rotation: Tuple[float,float,float] = (0,0,0)
    scale: float = 1.0

@dataclass
class FmbeBoneAnimation:
    group_id: str
    duration: int = 1
    keyframes: List[GroupKeyframe] = field(default_factory=list)
    interp: str = 'linear'
    step: int = 1
    name: str = ''
    loop: bool = False

@dataclass
class FmbeTransition:
    from_anim: str
    to_anim: str
    duration: int = 1
    name: str = ''

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
    bone_animations: List['FmbeBoneAnimation'] = field(default_factory=list)
    transitions: List['FmbeTransition'] = field(default_factory=list)

    def block(self, bid):
        for b in self.blocks:
            if b.id == bid: return b
        return None

    def group(self, gid):
        for g in self.groups:
            if g.id == gid: return g
        return None

    def resolve_offset(self, block):
        """Block offset relative to its bone group, then parent groups."""
        off=list(map(float, block.offset))
        gid=block.group
        seen=set()
        while gid:
            if gid in seen: break
            seen.add(gid); g=self.group(gid)
            if not g: break
            # rotate child offset by group rotation (x,y,z), then translate
            off=list(M.rotx(tuple(off), g.rotation[0]))
            off=list(M.roty(tuple(off), g.rotation[1]))
            off=list(M.rotz(tuple(off), g.rotation[2]))
            for i in range(3): off[i]+=float(g.offset[i])
            gid=g.parent
        return tuple(off)

    def resolved_position(self, block):
        p=self.resolve_offset(block)
        return (int(round(self.origin[0]+p[0])), int(round(self.origin[1]+p[1])), int(round(self.origin[2]+p[2])))

    def group_members_deep(self, gid):
        """Members of gid plus descendants, in group declaration order."""
        out=[]; seen=set()
        def add(g):
            if not g or g.id in seen: return
            seen.add(g.id)
            out.extend(g.members)
            for child in self.groups:
                if child.parent == g.id: add(child)
        add(self.group(gid))
        # de-dup preserving order
        res=[]; used=set()
        for m in out:
            if m not in used: used.add(m); res.append(m)
        return res

    def animation_targets(self, anim):
        if anim.group_id:
            return [self.block(m) for m in self.group_members_deep(anim.group_id) if self.block(m)]
        b=self.block(anim.block_id) if anim.block_id else None
        return [b] if b else []

    def animation_names(self):
        d={a.name or a.block_id or a.group_id: a for a in self.animations}
        for b in self.bone_animations:
            d[b.name or b.group_id]=b
        return d

    def bone_targets(self, ba):
        g=self.group(ba.group_id)
        return [self.block(m) for m in (self.group_members_deep(ba.group_id) if g else []) if self.block(m)]

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
        gids=[g.id for g in self.groups]
        for gid in set(gids):
            if gids.count(gid)>1: issues.append('duplicate group id: '+gid)
        by_group={g.id:g for g in self.groups}
        for b in self.blocks:
            if b.group and b.group not in by_group: issues.append('%s: unknown group %s'%(b.id,b.group))
        for g in self.groups:
            if g.parent and g.parent not in by_group: issues.append('group %s: unknown parent %s'%(g.id,g.parent))
            for m in g.members:
                if m not in ids: issues.append('group %s: unknown member %s'%(g.id,m))
            # cycle check
            seen=set(); cur=g
            while cur and cur.parent:
                if cur.id in seen: issues.append('group cycle at '+cur.id); break
                seen.add(cur.id); cur=by_group.get(cur.parent)
        # resolved part origins must not overlap
        seen={}
        for b in self.blocks:
            p=tuple(round(x,4) for x in self.resolve_offset(b))
            if p in seen: issues.append('resolved offset collision: %s / %s'%(seen[p],b.id))
            seen[p]=b.id
        for a in self.animations:
            targets=self.animation_targets(a)
            if a.group_id and not self.group(a.group_id): issues.append('animation: unknown group '+a.group_id)
            if not a.group_id and a.block_id not in ids: issues.append('animation for unknown block: '+str(a.block_id))
            if a.group_id and a.block_id: issues.append('animation %s: set block_id or group_id, not both'%a.name)
            if a.duration <= 0: issues.append('animation %s duration <= 0'%a.name)
            if a.interp not in ('linear','step'): issues.append('animation %s: unsupported interp %s'%(a.name,a.interp))
            if a.step < 1: issues.append('animation %s: step < 1'%a.name)
            if not targets: warnings.append('animation %s has no targets'%a.name)
            ticks=[]
            for kf in a.keyframes:
                if kf.tick < 0 or kf.tick > a.duration: issues.append('%s: keyframe tick %s outside 0..%s'%(a.name,kf.tick,a.duration))
                if kf.tick in ticks: issues.append('%s: duplicate keyframe tick %s'%(a.name,kf.tick))
                ticks.append(kf.tick)
                for k in kf.vars:
                    if k in ROTATE_KEYS: issues.append('%s: keyframe uses %s (not supported)'%(a.name,k))
                    if k not in VAR_NAMES: issues.append('%s: keyframe unknown var %s'%(a.name,k))
            if a.keyframes and ticks != sorted(ticks): issues.append('%s: keyframes not sorted'%a.name)
        names=self.animation_names()
        for ba in self.bone_animations:
            if ba.group_id not in by_group: issues.append('bone animation: unknown group '+ba.group_id)
            if ba.duration <= 0: issues.append('bone animation %s duration <= 0'%ba.name)
            if ba.interp not in ('linear','step'): issues.append('bone animation %s: unsupported interp %s'%(ba.name,ba.interp))
            if ba.step < 1: issues.append('bone animation %s: step < 1'%ba.name)
            if not self.bone_targets(ba): warnings.append('bone animation %s has no targets'%ba.name)
            ticks=[]
            for kf in ba.keyframes:
                if kf.tick < 0 or kf.tick > ba.duration: issues.append('%s: group keyframe tick %s outside 0..%s'%(ba.name,kf.tick,ba.duration))
                if kf.tick in ticks: issues.append('%s: duplicate group keyframe tick %s'%(ba.name,kf.tick))
                ticks.append(kf.tick)
                if not math.isfinite(float(kf.scale)) or float(kf.scale) <= 0: issues.append('%s: group scale must be > 0'%ba.name)
            if ba.keyframes and ticks != sorted(ticks): issues.append('%s: group keyframes not sorted'%ba.name)
        for tr in self.transitions:
            if tr.from_anim not in names: issues.append('transition: unknown animation '+tr.from_anim)
            if tr.to_anim not in names: issues.append('transition: unknown animation '+tr.to_anim)
            if tr.duration <= 0: issues.append('transition %s: duration <= 0'%tr.name)
        return {'ok':not issues,'issues':issues,'warnings':warnings,
                'blocks':len(self.blocks),'animations':len(self.animations),
                'bone_animations':len(self.bone_animations),'groups':len(self.groups)}

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
                offset=tuple(x.get('offset',[0,0,0])), vars=dict(x.get('vars',{})),
                group=x.get('group')))
        anims=[]
        for a in d.get('animations',[]):
            anims.append(FmbeAnimation(
                block_id=a.get('block_id'), duration=int(a.get('duration',1)),
                keyframes=[Keyframe(int(k['tick']),dict(k.get('vars',{}))) for k in a.get('keyframes',[])],
                loop=bool(a.get('loop',False)), group_id=a.get('group_id'), name=str(a.get('name','')),
                interp=str(a.get('interp','linear')), step=int(a.get('step',1))))
        groups=[FmbeBoneGroup(str(g['id']),list(g.get('members',[])),g.get('parent'),
                tuple(g.get('offset',[0,0,0])),tuple(g.get('rotation',[0,0,0]))) for g in d.get('groups',[])]
        bones=[]
        for a in d.get('bone_animations',[]):
            bones.append(FmbeBoneAnimation(str(a['group_id']),int(a.get('duration',1)),
                [GroupKeyframe(int(k['tick']),tuple(k.get('offset',[0,0,0])),
                               tuple(k.get('rotation',[0,0,0])),float(k.get('scale',1)))
                 for k in a.get('keyframes',[])],
                str(a.get('interp','linear')),int(a.get('step',1)),str(a.get('name','')),bool(a.get('loop',False))))
        transitions=[FmbeTransition(str(t['from']),str(t['to']),int(t.get('duration',1)),str(t.get('name',''))) for t in d.get('transitions',[])]
        carrier=None
        if d.get('carrier') is not None:
            c=d['carrier']; carrier=FmbeCarrier(bool(c.get('enabled',True)),str(c.get('entity','fox')),str(c.get('display_score','fmbe_display')))
        exp=d.get('export',{})
        return cls(name=str(d.get('name','model')),blocks=blocks,animations=anims,groups=groups,
                   export=FmbeExport(exp.get('prefix',FmbeExport.prefix),exp.get('suffix',FmbeExport.suffix)) if exp else FmbeExport(),
                   carrier=carrier,origin=tuple(d.get('origin',[0,0,0])),
                   bone_animations=bones,transitions=transitions)

def _num(v):
    if isinstance(v, bool): return int(v)
    if isinstance(v, int): return v
    try:
        f=float(v)
        return int(f) if f.is_integer() else f
    except Exception:
        return 0
