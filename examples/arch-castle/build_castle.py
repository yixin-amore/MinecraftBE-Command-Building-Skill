#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small component-library castle: curtain wall, gatehouse, keep, cloister, bay, portal, flying buttress, dormer."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SKILL=HERE.parents[1]
sys.path.insert(0,str(SKILL/'scripts'))
from arch_compile import ArchBuilder, Palette

W,D=120,120; START=(700,0,700)
def build():
    b=ArchBuilder(W,D,Palette())
    b.site('grass')
    # outer curtain with south gate opening
    b.curtain_wall(12,12,108,108,2,26,4,gate_center=60,gate_width=26)
    # gatehouse / keep / cloister
    b.gatehouse(60,108,width=36,depth=18,y0=2,height=58,passage_width=10)
    b.keep(60,40,size=28,y0=2,height=78,spire=24)
    b.cloister(20,62,44,86,2,5,7)
    # hall + roof + dormer
    b.walls(72,98,58,86,2,30,'stone',2)
    b.gable_roof_x(72,98,58,86,31,40,'roof')
    b.gable_face(72,98,58,31,40); b.gable_face(72,98,86,31,40)
    for x in (78,88): b.dormer_z(x,70,41,3)
    # facade test bay left of gate
    b.bay_z(108,28,2,7,18,True,True,True)
    # flying buttress on hall east
    for z in (64,74,84): b.flying_buttress(98,z,2,36,1)
    # portal on bridge front
    b.portal_z(128,60,2,10,14,3,3)
    return b,b.stats()
if __name__=='__main__':
    b,st=build()
    out=HERE/'out'; out.mkdir(exist_ok=True)
    (out/'parts.json').write_text(json.dumps([p.to_dict() for p in b.parts],ensure_ascii=False,indent=1),encoding='utf-8')
    b.write_bdx(out/'castle.bdx',START)
    (out/'stats.json').write_text(json.dumps(st,ensure_ascii=False,indent=1),encoding='utf-8')
    print(json.dumps({'stats':st,'parts':len(b.parts),'start':START},ensure_ascii=False,indent=1))
