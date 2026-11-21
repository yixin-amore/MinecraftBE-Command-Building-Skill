#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Component-library castle benchmark: asymmetric cliff keep, hall, chapel, cloister."""
import sys, json, math
from pathlib import Path
HERE=Path(__file__).resolve().parent
SKILL=HERE.parents[1]
sys.path.insert(0,str(SKILL/'scripts'))
from arch_compile import ArchBuilder, Palette

W,D=140,120; START=(700,0,700)
def build():
    p=Palette()
    p.stone='calcite'; p.light='smooth_quartz'; p.dark='deepslate_bricks'
    p.trim='polished_deepslate'; p.roof='deepslate_tiles'; p.copper='deepslate_tiles'
    p.glass='blue_stained_glass'; p.glass2='purple_stained_glass'
    b=ArchBuilder(W,D,p); b.site('grass')
    # cliff/island + moat
    b.box(6,134,1,2,6,114,'stone')
    b.box(10,130,2,2,10,110,'grass')
    for x in range(8,133,9):
        b.box(x,x+2,1,3,6,10,'deepslate_bricks'); b.box(x,x+2,1,3,110,114,'deepslate_bricks')
    # curtain wall: gate south; less regular buttress rhythm
    b.curtain_wall(18,18,122,102,2,20,4,gate_center=70,gate_width=24)
    b.gatehouse(70,102,width=30,depth=16,y0=2,height=44,passage_width=8,tower_radius=6)
    # keep is the dominant mass, west-of-centre
    b.keep(55,45,size=26,y0=2,height=68,spire=28)
    # cloister / inner court east of keep
    b.cloister(48,72,80,96,2,4,6)
    # great hall east
    b.walls(84,112,38,74,2,34,'stone',2); b.floor(86,110,40,72,2,'trim')
    b.gable_roof_x(84,112,38,74,35,48,'roof')
    b.gable_face(84,112,38,35,48); b.gable_face(84,112,74,35,48)
    for x in range(88,112,8):
        b.buttress(x,74,2,30,0,1,'dark'); b.buttress(x,38,2,30,0,-1,'dark')
        b.lancet_z(74,x+3,8,16,2); b.lancet_z(38,x+3,8,16,2)
    for x in (90,102): b.dormer_z(x,62,42,3)
    # chapel south-west, lower than keep
    b.walls(24,42,48,76,2,36,'stone',2); b.floor(26,40,50,74,2,'trim')
    b.gable_roof_z(24,42,48,76,37,50,'roof')
    b.gable_face(24,42,76,37,50)
    b.rose_z(76,33,22,7)
    for z in (52,62,72): b.lancet_x(24,z,8,14,1); b.lancet_x(42,z,8,14,1)
    # flying buttresses around chapel, chapel is lower than hall
    for z in (54,64,74):
        b.flying_buttress(24,z,2,34,-1); b.flying_buttress(42,z,2,34,1)
    # facade bays on hall's south face
    for x in (88,96,104): b.bay_z(74,x,2,6,18,True,True,True)
    # portal on bridge
    b.portal_z(122,70,2,9,13,3,3)
    # keep buttresses + banners (break the flat south face)
    for x in (44,50,56,62,66): b.buttress(x,58,2,52,0,1,'dark')
    for x,z in ((43,33),(67,33),(43,57),(67,57)):
        b.box(x-1,x+1,54,62,z,z,'red_wool')
        b.box(x-2,x+2,63,65,z,z,'red_wool')
    # gatehouse banners / lamps on the approach face
    for x in (61,79):
        b.box(x-1,x+1,28,36,110,110,'red_wool')
        b.box(x-2,x+2,37,39,110,110,'red_wool')
        b.put(x,40,110,'gold_block')
    # courtyard well / trees / lamps
    b.box(62,66,3,4,82,86,'dark'); b.box(63,65,5,5,83,85,'water'); b.put(64,6,84,'gold')
    for x,z in ((52,80),(76,80),(52,92),(76,92)):
        b.box(x-1,x+1,3,6,z-1,z+1,'log'); b.box(x-2,x+2,7,9,z-2,z+2,'leaves')
    for x,z in ((44,68),(80,68),(44,98),(80,98),(24,80),(112,80)): b.put(x,8,z,'lantern')
    # base coursing: dark plinth, calcite upper wall, sparse stone bands
    for (x,y,z),blk in list(b.V.items()):
        if blk=='calcite':
            if y<=6: b.V[(x,y,z)]='deepslate_bricks'
            elif y in (20,34,48): b.V[(x,y,z)]='stone_bricks'
    return b,b.stats()
if __name__=='__main__':
    b,st=build(); out=HERE/'out'; out.mkdir(exist_ok=True)
    (out/'parts.json').write_text(json.dumps([p.to_dict() for p in b.parts],ensure_ascii=False,indent=1),encoding='utf-8')
    b.write_bdx(out/'castle.bdx',START)
    (out/'stats.json').write_text(json.dumps(st,ensure_ascii=False,indent=1),encoding='utf-8')
    print(json.dumps({'stats':st,'parts':len(b.parts),'start':START},ensure_ascii=False,indent=1))
