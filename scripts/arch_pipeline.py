#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Architecture pipeline: builder -> voxels/BDX -> preview -> readback."""
import sys, json, importlib.util, subprocess, argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
SKILL=HERE.parent
ap=argparse.ArgumentParser()
ap.add_argument('--builder',required=True)
ap.add_argument('--outdir',default=None)
ap.add_argument('--start',default='900,0,900')
a=ap.parse_args()
start=tuple(map(int,a.start.split(',')))
out=Path(a.outdir) if a.outdir else Path(a.builder).resolve().parent/'out'
out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('arch_build_'+str(abs(hash(a.builder))),a.builder)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
b,stats=mod.build()
vox={f'{x},{y},{z}':v for (x,y,z),v in b.V.items()}
(out/'voxels.json').write_text(json.dumps(vox,ensure_ascii=False),encoding='utf-8')
n=b.write_bdx(out/'building.bdx',start)
subprocess.run([sys.executable,str(HERE/'arch_preview.py'),str(out/'voxels.json'),'--out',str(out/'building')],check=True)
subprocess.run([sys.executable,str(HERE/'arch_readback.py'),str(out/'building.bdx'),'--start',a.start,'--json',str(out/'readback.json')],check=True)
rb=json.loads((out/'readback.json').read_text())
issues=[]
if rb['blocks']!=len(b.V): issues.append(f"block count {rb['blocks']} != voxels {len(b.V)}")
if rb['bounds']!=[min(x for x,y,z in b.V),min(y for x,y,z in b.V),min(z for x,y,z in b.V),max(x for x,y,z in b.V),max(y for x,y,z in b.V),max(z for x,y,z in b.V)]:
 issues.append(f"bounds {rb['bounds']} != builder bounds")
rep={'voxels':len(b.V),'bdx_blocks':rb['blocks'],'bounds':rb['bounds'],'start':start,'issues':issues,'stats':stats,'readback':rb}
(out/'report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps({'voxels':len(b.V),'bdx_blocks':rb['blocks'],'issues':issues,'out':str(out)},ensure_ascii=False,indent=1))
if issues: raise SystemExit(1)
