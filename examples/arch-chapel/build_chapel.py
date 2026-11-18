#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden test: small Gothic chapel built with ArchBuilder."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SKILL=HERE.parents[1]
sys.path.insert(0,str(SKILL/'scripts'))
from arch_compile import ArchBuilder, Palette
from arch_spec import ArchSpec, Mass

W,D=60,80; START=(900,0,900)
def build():
    b=ArchBuilder(W,D,Palette())
    b.site('grass')
    b.box(27,33,2,2,65,79,'light')
    b.box(20,40,2,2,15,55,'trim')
    b.walls(20,40,15,55,2,24,'stone',2)
    b.floor(20,40,15,55,2,'trim')
    for z in range(18,55,8):
        b.buttress(20,z,2,20,-1,0,'dark')
        b.buttress(40,z,2,20,1,0,'dark')
        b.lancet_x(20,z+3,7,11,1,'glass')
        b.lancet_x(40,z+3,7,11,1,'glass')
    b.gable_roof_x(20,40,15,55,25,35,'roof')
    b.crenellate(20,40,15,55,25,'trim',3)
    b.tower(30,60,5,2,50,72)
    b.carve(27,33,2,12,65,66)
    b.box(27,33,2,2,65,65,'wood')
    for k in range(4): b.box(27+k,33-k,13+k,13+k,65,65,'trim')
    b.rose_z(66,30,30,6)
    b.carve(27,33,38,45,64,66)
    for x in range(28,33,3): b.box(x,x,38,45,65,65,'trim')
    for z in (15,55):
        for k in range(6): b.box(30-k,30+k,25+k,25+k,z,z,'trim')
    b.box(42,52,2,14,20,32,'stone'); b.ring(42,52,2,14,20,32,'trim',1)
    b.lancet_z(32,47,6,7,1,'glass2')
    b.gable_roof_z(42,52,20,32,15,23,'roof')
    for x in (42,52):
        for z in (20,32): b.pinnacle(x,z,15,8)
    b.box(45,55,2,2,38,52,'grass')
    b.walls(44,56,38,52,3,6,'dark',1)
    for x in (44,56):
        for z in (38,52): b.pinnacle(x,z,7,5)
    return b,b.stats()
if __name__=='__main__':
    b,st=build()
    (HERE/'chapel-voxels.json').write_text(json.dumps({f'{x},{y},{z}':v for (x,y,z),v in b.V.items()},ensure_ascii=False),encoding='utf-8')
    (HERE/'chapel-stats.json').write_text(json.dumps(st,ensure_ascii=False,indent=1),encoding='utf-8')
    b.write_bdx(HERE/'chapel.bdx',START)
    s=ArchSpec('Arch Chapel',(W,D),[Mass('nave',.60,24,(0,0)),Mass('tower',.30,50,(0,40)),Mass('spire',.10,72,(0,42))],courtyards=1,focal=('tower','rose'))
    print(json.dumps({'stats':st,'check':s.check(),'start':START},ensure_ascii=False,indent=1))
