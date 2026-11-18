#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Style profiles distilled from local architecture references."""
from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass(frozen=True)
class StyleProfile:
    name: str
    verticality: Tuple[float,float]   # height / max(width,depth)
    bay_width: Tuple[int,int]
    buttress_every: Tuple[int,int]
    pinnacle_spacing: Tuple[int,int]
    courtyard_ratio: Tuple[float,float]  # 0 if no courtyard
    roof: str
    palette_roles: Dict[str,str] = field(default_factory=dict)

GOTHIC_KIRK = StyleProfile(
    'gothic-kirk',
    verticality=(1.15,2.80), bay_width=(5,9), buttress_every=(5,8),
    pinnacle_spacing=(3,6), courtyard_ratio=(0.0,0.0), roof='steep slate / dark copper',
    palette_roles={'base':'polished_deepslate / tuff','wall':'polished_andesite / stone',
                   'trim':'dark oak / deepslate','glass':'stained glass','roof':'deepslate_tiles'},
)
COURTYARD_CASTLE = StyleProfile(
    'courtyard-castle',
    verticality=(0.55,1.00), bay_width=(5,10), buttress_every=(6,12),
    pinnacle_spacing=(4,8), courtyard_ratio=(0.20,0.55), roof='steep gable + hip + one dominant spire',
    palette_roles={'base':'deepslate / cobble','wall':'stone bricks / calcite',
                   'trim':'polished deepslate','glass':'blue/purple stained','roof':'deepslate tiles / copper'},
)
STYLES={'gothic-kirk':GOTHIC_KIRK,'courtyard-castle':COURTYARD_CASTLE}

def check(style: StyleProfile, verticality: float, bay_width: int, buttress_every: int,
          pinnacle_spacing: int, courtyard_ratio: float=0.0):
    issues=[]
    def rng(label,v,lo,hi):
        if not (lo<=v<=hi): issues.append(f'{label} {v} outside [{lo},{hi}]')
    rng('verticality',verticality,*style.verticality)
    rng('bay_width',bay_width,*style.bay_width)
    rng('buttress_every',buttress_every,*style.buttress_every)
    rng('pinnacle_spacing',pinnacle_spacing,*style.pinnacle_spacing)
    rng('courtyard_ratio',courtyard_ratio,*style.courtyard_ratio)
    return {'style':style.name,'issues':issues,'ok':not issues}

if __name__=='__main__':
    print(check(GOTHIC_KIRK,1.27,7,6,4,0.0))
    print(check(COURTYARD_CASTLE,0.73,8,8,6,0.30))
