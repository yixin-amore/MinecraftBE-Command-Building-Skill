#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read back normal-block BDX and compare bounds/count/palette."""
import struct, brotli, json, argparse
from pathlib import Path
from collections import Counter
def cstr(b,i):
    j=b.index(0,i); return b[i:j].decode('utf-8'),j+1
def read(path):
    raw=Path(path).read_bytes(); assert raw[:3]==b'BD@'; body=brotli.decompress(raw[3:]); assert body[:5]==b'BDX\x00\x00'
    b=body[5:]; i=0; names=[]; pos=[0,0,0]; out=[]
    while i<len(b):
        op=b[i]; i+=1
        if op==1: s,i=cstr(b,i); names.append(s)
        elif op in (21,23,25):
            (v,)=struct.unpack('>i',b[i:i+4]); i+=4; pos[{21:0,23:1,25:2}[op]]+=v
        elif op==5:
            nid,data=struct.unpack('>HH',b[i:i+4]); i+=4; out.append({'name':names[nid],'pos':tuple(pos)})
        elif op==7:
            nid,data=struct.unpack('>HH',b[i:i+4]); i+=4; out.append({'name':names[nid],'pos':tuple(pos)})
        elif op==88: break
        else: raise ValueError('unsupported BDX op '+str(op))
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('bdx'); ap.add_argument('--json',default=None); ap.add_argument('--start',default='0,0,0'); a=ap.parse_args()
    sx,sy,sz=map(int,a.start.split(','))
    rows=read(a.bdx); types=Counter(r['name'] for r in rows)
    out={'blocks':len(rows),'types':dict(types.most_common()),'bounds':[min(r['pos'][0] for r in rows)+sx,min(r['pos'][1] for r in rows)+sy,min(r['pos'][2] for r in rows)+sz,max(r['pos'][0] for r in rows)+sx,max(r['pos'][1] for r in rows)+sy,max(r['pos'][2] for r in rows)+sz]}
    print(json.dumps(out,ensure_ascii=False,indent=1))
    if a.json: Path(a.json).write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
if __name__=='__main__': main()
