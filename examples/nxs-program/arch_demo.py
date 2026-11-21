#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge an NXS spiral stair into an ArchBuilder and write BDX."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SKILL=HERE.parents[1]; sys.path.insert(0,str(SKILL/'scripts'))
from arch_compile import ArchBuilder, Palette
from nxs_program import NxsProgram, SpiralOp
from nxs_arch import apply_program

def main():
    b=ArchBuilder(40,40,Palette()); b.site('grass')
    p=NxsProgram('spiral-arch'); p.add(SpiralOp(center=(20,2,20),radius=7,turns=1.5,rise=18,count=40,material='minecraft:stone_bricks',kind='block'))
    info=apply_program(p,b,origin=(0,0,0))
    out=HERE/'out'; out.mkdir(exist_ok=True)
    b.write_bdx(out/'nxs-arch.bdx',(700,0,700))
    print(json.dumps({'apply':info,'stats':b.stats()},ensure_ascii=False,indent=1))
if __name__=='__main__': main()
