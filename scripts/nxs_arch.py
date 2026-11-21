#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply NXS Program block instances to ArchBuilder voxels."""
from __future__ import annotations
from nxs_program import NxsProgram

def apply_program(program: NxsProgram, builder, origin=(0,0,0), limit=200000):
    n=0
    for x in program.instances():
        if x.kind not in ('block','setblock'): continue
        p=x.frame.origin
        try:
            builder.put(int(round(origin[0]+p[0])),int(round(origin[1]+p[1])),int(round(origin[2]+p[2])),x.material)
        except Exception:
            continue
        n+=1
        if n>=limit: break
    return {'applied':n,'limit':limit}
