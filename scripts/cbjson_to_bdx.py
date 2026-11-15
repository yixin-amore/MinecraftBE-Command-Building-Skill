#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cb.json (mct dump_cbworld) -> .bdx command blocks (local prototype).
BDX already supports PlaceBlockWithCommandBlockData (ID 27); this bridges it.
"""
import json, argparse
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from bdxgen import Block, write_bdx, FACING, MODE

def mode_of(block):
    b=block.lower()
    if 'repeating' in b: return 'repeat'
    if 'chain' in b: return 'chain'
    return 'impulse'
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('cbjson'); ap.add_argument('out')
    ap.add_argument('--start-x',type=int,default=0)
    ap.add_argument('--start-y',type=int,default=0)
    ap.add_argument('--start-z',type=int,default=0)
    a=ap.parse_args()
    rows=json.loads(Path(a.cbjson).read_text(encoding='utf-8'))
    out=[]
    for r in rows:
        fd=int(r.get('fd',5))
        facing={v:k for k,v in FACING.items()}.get(fd,'east')
        out.append(Block(
            int(r['x'])-a.start_x, int(r['y'])-a.start_y, int(r['z'])-a.start_z,
            mode_of(r.get('block','command_block')),
            str(r.get('command','')),
            facing=facing,
            delay=int(r.get('tick',0)),
            conditional=bool(r.get('cond',0)),
            needs_redstone=not bool(r.get('auto',0)),
            custom_name=str(r.get('name','')),
            last_output=str(r.get('last','')),
            track_output=bool(r.get('track',1)),
        ))
    write_bdx(out,a.out)
    print('wrote',a.out,len(out),'command blocks')
if __name__=='__main__': main()
