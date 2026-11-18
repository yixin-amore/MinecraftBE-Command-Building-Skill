#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Voxels JSON -> BDX generic bridge."""
import json, argparse, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,HERE)
from bdxgen import BuildBlock, write_build_bdx
ap=argparse.ArgumentParser(); ap.add_argument('voxels'); ap.add_argument('out'); ap.add_argument('--start',default='0,0,0'); a=ap.parse_args()
sx,sy,sz=map(int,a.start.split(',')); d=json.loads(Path(a.voxels).read_text(encoding='utf-8'))
items=[]
for k,b in d.items():
 x,y,z=map(int,k.split(',')); items.append(BuildBlock(x-sx,y-sy,z-sz,b))
write_build_bdx(items,a.out); print('wrote',a.out,len(items))
