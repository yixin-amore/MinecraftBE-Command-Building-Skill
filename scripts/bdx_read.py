#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read BDX normal blocks and command blocks for round-trip validation."""
import struct, brotli, json, argparse
from pathlib import Path
FACINGS=['down','up','north','south','west','east']; MODES=['impulse','repeat','chain']
def cstr(b,i):
    j=b.index(0,i); return b[i:j].decode('utf-8'),j+1
def read(path):
    raw=Path(path).read_bytes(); assert raw[:3]==b'BD@'
    body=brotli.decompress(raw[3:]); assert body[:5]==b'BDX\x00\x00'
    b=body[5:]; i=0; names=[]; pos=[0,0,0]; out=[]
    while i<len(b):
        op=b[i]; i+=1
        if op==1: s,i=cstr(b,i); names.append(s)
        elif op in (21,23,25):
            (v,)=struct.unpack('>i',b[i:i+4]); i+=4; pos[{21:0,23:1,25:2}[op]]+=v
        elif op==5:
            nid,data=struct.unpack('>HH',b[i:i+4]); i+=4
            out.append({'kind':'block','name':names[nid],'pos':tuple(pos)})
        elif op==7:
            nid,data=struct.unpack('>HH',b[i:i+4]); i+=4
            out.append({'kind':'block','name':names[nid],'pos':tuple(pos)})
        elif op==27:
            nid,data=struct.unpack('>HH',b[i:i+4]); i+=4
            (mode,)=struct.unpack('>I',b[i:i+4]); i+=4
            cmd,i=cstr(b,i); name,i=cstr(b,i); last,i=cstr(b,i)
            (delay,)=struct.unpack('>I',b[i:i+4]); i+=4
            eft,track,cond,red=b[i:i+4]; i+=4
            out.append({'kind':'command_block','name':names[nid],'pos':tuple(pos),'mode':MODES[mode],
                        'command':cmd,'custom_name':name,'delay':delay,'conditional':bool(cond),
                        'needs_redstone':bool(red),'facing':FACINGS[data&7]})
        elif op==88: break
        else: raise ValueError('unsupported BDX op '+str(op))
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('bdx'); ap.add_argument('--json',default=None); a=ap.parse_args()
    rows=read(a.bdx); cbs=[r for r in rows if r['kind']=='command_block']
    out={'total':len(rows),'command_blocks':len(cbs),'commands':[r['command'] for r in cbs]}
    print(json.dumps(out,ensure_ascii=False,indent=1) if a.json else '\n'.join(out['commands']))
    if a.json: Path(a.json).write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
if __name__=='__main__': main()
