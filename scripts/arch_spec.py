#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal architecture spec + composition checks (original, no GPL code)."""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
@dataclass
class Mass:
    name: str
    weight: float
    height: float
    center: Tuple[float,float] = (0.0,0.0)
@dataclass
class ArchSpec:
    name: str
    site: Tuple[float,float]
    masses: List[Mass]
    golden: Tuple[float,...] = (0.382,0.618,0.90)
    facade_layers: int = 4
    palette: Tuple[float,float,float] = (0.60,0.30,0.10)
    courtyards: int = 0
    focal: Tuple[str,...] = ()
    def check(self):
        issues=[]; notes=[]
        total=sum(m.weight for m in self.masses)
        if total<=0: issues.append('masses total weight <= 0')
        else:
            ratios=[m.weight/total for m in self.masses]
            target=[0.60,0.30,0.10]
            if len(ratios)!=3: notes.append('631 expects 3 masses; got %d'%len(ratios))
            for i,(r,t) in enumerate(zip(ratios,target)):
                if abs(r-t)>0.08: issues.append('mass %d ratio %.2f != %.2f (±.08)'%(i+1,r,t))
        # weighted centroid
        if total>0:
            cx=sum(m.center[0]*m.weight for m in self.masses)/total
            cz=sum(m.center[1]*m.weight for m in self.masses)/total
            off=(cx*cx+cz*cz)**0.5
            limit=max(self.site)*0.15
            if off>limit: issues.append('centroid off-axis %.2f > %.2f'%(off,limit))
            else: notes.append('centroid offset %.2f <= %.2f'%(off,limit))
        if self.facade_layers<4: issues.append('facade layers %d < 4'%self.facade_layers)
        if abs(sum(self.palette)-1)>0.02: issues.append('palette sum %.2f != 1'%sum(self.palette))
        if any(x<0 or x>1 for x in self.golden): issues.append('golden marks outside 0..1')
        if self.courtyards<0: issues.append('courtyards < 0')
        if not self.focal: notes.append('no focal declared')
        return {'name':self.name,'issues':issues,'notes':notes,
                'mass_ratios':[round(m.weight/total,3) for m in self.masses] if total else []}
def demo():
    s=ArchSpec('Parliament Study',(180,100),[
        Mass('wings',.60,38,(0,0)), Mass('center',.30,55,(0,0)), Mass('crown',.10,113,(0,0)),
    ],courtyards=2,focal=('dome','rose'))
    r=s.check(); print(r)
    return r
if __name__=='__main__': demo()
