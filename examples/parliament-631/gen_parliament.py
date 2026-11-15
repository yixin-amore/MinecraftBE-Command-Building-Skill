#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""匈牙利国会大厦 · 河岸立面 / 631 / 深度立面学习版。

坐标：中心 (300,0,300)，StartPos 210,0,250；建筑 x0..180，z0..100。
重点不是“贴一堵墙”，而是四层立面：
  背墙 -> 凹窗/拱廊 -> 前柱/檐口/阳台 -> 尖顶/塔/圆顶剪影。
"""
from __future__ import annotations
import json, math, sys
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SKILL=ROOT/"scripts"
if not (SKILL/"bdxgen.py").exists(): SKILL=ROOT/".dsh/skills/mcbe-command-blocks/scripts"
sys.path.insert(0,str(SKILL))
from bdxgen import BuildBlock, write_build_bdx  # noqa

CREAM="smooth_quartz"; CREAM2="stone_bricks"; CREAM3="calcite"; CREAM4="polished_diorite"; CREAM5="quartz_block"
STONE="tuff"; TRIM="polished_deepslate"; DARK="deepslate_tiles"; DARK2="polished_deepslate"
ROOF="red_terracotta"; ROOF2="deepslate_tiles"; RIDGE="oxidized_copper"; ACCENT="weathered_copper"
GLASS="blue_stained_glass"; GLASS2="purple_stained_glass"; GLASS3="black_stained_glass"
GOLD="gold_block"; GLOW="sea_lantern"; COPPER="oxidized_copper"; WATER="water"; GRASS="grass_block"; LEAVES="dark_oak_leaves"; LOG="dark_oak_log"; WOOD="dark_oak_planks"
V={}
def put(x,y,z,b): V[(int(x),int(y),int(z))]=b
def box(x0,x1,y0,y1,z0,z1,b):
    x0,x1=sorted((int(x0),int(x1))); y0,y1=sorted((int(y0),int(y1))); z0,z1=sorted((int(z0),int(z1)))
    for x in range(x0,x1+1):
        for y in range(y0,y1+1):
            for z in range(z0,z1+1): put(x,y,z,b)
def ring(x0,x1,y0,y1,z0,z1,b,t=1):
    x0,x1=sorted((int(x0),int(x1))); z0,z1=sorted((int(z0),int(z1)))
    for x in range(x0,x1+1):
        for z in range(z0,z1+1):
            if min(x-x0,x1-x,z-z0,z1-z)<t:
                for y in range(int(y0),int(y1)+1): put(x,y,z,b)
def carve(x0,x1,y0,y1,z0,z1):
    for x in range(min(x0,x1),max(x0,x1)+1):
        for y in range(min(y0,y1),max(y0,y1)+1):
            for z in range(min(z0,z1),max(z0,z1)+1): V.pop((x,y,z),None)
def line3(a,b,steps,block,r=0):
    for k in range(steps+1):
        t=k/steps
        x=round(a[0]+(b[0]-a[0])*t); y=round(a[1]+(b[1]-a[1])*t); z=round(a[2]+(b[2]-a[2])*t)
        for dx in range(-r,r+1):
            for dy in range(-r,r+1):
                for dz in range(-r,r+1): put(x+dx,y+dy,z+dz,block)

CX=90; FRONT=76; BACK=10
# ---------------- 多瑙河岸/广场 ----------------
box(0,180,0,0,0,100,WATER)
box(0,180,0,2,0,84,CREAM3)
box(6,174,2,2,0,78,CREAM2)
box(4,176,2,3,0,80,CREAM3)
# 河岸步道 + 台阶
box(4,176,1,1,76,84,CREAM3)
box(56,124,1,1,80,96,CREAM2)
for i in range(5): box(60+i,120-i,1+i,1+i,80-i,81+i,CREAM3)
# 河岸灯/长椅
for x in range(12,176,16):
    for y in range(2,5): put(x,y,82,TRIM)
    put(x,5,82,GLOW)
# 两棵小树
for x in (10,170):
    for y in range(2,6): put(x,y,60,LOG)
    box(x-2,x+2,6,8,58,62,LEAVES)

# ---------------- 主体壳 ----------------
# 后墙 / 侧墙 / 前墙（前墙留出拱廊深度）
box(8,172,3,38,BACK,BACK+3,CREAM)
box(8,12,3,38,BACK,FRONT,CREAM)
box(168,172,3,38,BACK,FRONT,CREAM)
box(8,172,3,38,FRONT-4,FRONT,CREAM)
box(8,172,3,3,BACK,FRONT,DARK)
# 前檐口
box(6,174,18,20,FRONT-2,FRONT+2,CREAM4)
box(6,174,19,19,FRONT+2,FRONT+3,TRIM)
for x in range(8,173,2): put(x,17,FRONT+2,TRIM)
box(6,174,36,38,FRONT-2,FRONT+3,CREAM4)
box(6,174,37,37,FRONT+3,FRONT+4,TRIM)
for x in range(8,173,2): put(x,35,FRONT+3,TRIM)

# ---------------- 底层拱廊：真正的凹进 ----------------
for x in range(12,169,8):
    # 拱廊柱/壁柱
    box(x,x+1,3,18,FRONT-2,FRONT+2,CREAM4)
    box(x,x+1,18,20,FRONT-1,FRONT+3,CREAM3)
    # 真正凹进的拱洞：清出 4 格深，补后墙/顶棚/地面
    carve(x+2,x+7,3,15,FRONT-4,FRONT-1)
    box(x+2,x+7,3,3,FRONT-5,FRONT-1,DARK)
    box(x+2,x+7,16,16,FRONT-5,FRONT-1,CREAM4)
    box(x+2,x+7,3,15,FRONT-5,FRONT-5,DARK)
    # 洞内窗/门
    box(x+3,x+6,4,12,FRONT-5,FRONT-5,GLASS3 if x%16 else GLASS)
    # 尖拱石框
    for k in range(4):
        box(x+2+k,x+7-k,15+k,15+k,FRONT-2,FRONT+1,CREAM4)
    # 前面的独立柱（第三层深度）
    box(x+4,x+4,3,18,FRONT+3,FRONT+3,CREAM5)
    put(x+4,19,FRONT+3,GOLD)
    # 柱头/基座
    box(x+3,x+5,3,4,FRONT+2,FRONT+4,CREAM3)
    box(x+3,x+5,18,19,FRONT+2,FRONT+4,CREAM3)
# 拱廊上方栏杆/檐口
box(8,172,18,20,FRONT+2,FRONT+3,CREAM3)
for x in range(10,173,4): put(x,21,FRONT+2,CREAM4)

# ---------------- 上层：凹窗 + 凸柱 ----------------
for x in range(12,169,8):
    # 退后的上层拱廊：真正挖空 3 格，后墙/窗，形成第二层镂空
    carve(x+2,x+6,23,33,FRONT-4,FRONT-2)
    box(x+2,x+6,23,33,FRONT-5,FRONT-5,DARK)
    box(x+3,x+5,24,31,FRONT-5,FRONT-5,GLASS if x%16 else GLASS2)
    # 前柱之间的尖拱
    for k in range(3):
        box(x+1+k,x+7-k,33+k,33+k,FRONT-1,FRONT+1,CREAM4)
    # 上层小栏杆
    box(x+2,x+6,22,22,FRONT+1,FRONT+2,CREAM3)
    # 窗框/尖拱
    for k in range(3):
        box(x+2+k,x+6-k,33+k,33+k,FRONT-3,FRONT+1,CREAM4)
    # 前凸壁柱 + 双柱（把窗洞夹出阴影）
    box(x,x+1,21,36,FRONT-1,FRONT+2,CREAM4)
    box(x+7,x+8,21,36,FRONT-1,FRONT+2,CREAM4)
    for xx in (x+2,x+6):
        box(xx,xx,22,34,FRONT+2,FRONT+3,CREAM5)
        box(xx-1,xx+1,21,22,FRONT+1,FRONT+4,CREAM3)
        box(xx-1,xx+1,34,35,FRONT+1,FRONT+4,CREAM3)
    # 小阳台（中央几跨）
    if 50<=x<=130:
        box(x,x+8,21,21,FRONT+2,FRONT+5,CREAM3)
        for xx in (x,x+8): put(xx,22,FRONT+5,CREAM4)
    # 每一跨都有山墙；中央跨更高
    gh=47 if x%16==12 else 43
    for y in range(38,gh):
        half=max(1,round((gh-y)*0.75))
        box(x+4-half,x+4+half,y,y,FRONT+2,FRONT+2,CREAM4)
    box(x+3,x+5,gh-4,gh-4,FRONT+3,FRONT+3,CREAM3)
    put(x+4,gh,FRONT+2,GOLD)
    # 山墙尖顶/小尖塔
    box(x+4,x+4,gh+1,gh+5,FRONT+1,FRONT+1,CREAM4)
    put(x+4,gh+6,FRONT+1,GOLD)

# ---------------- 檐口尖塔（打断红屋顶） ----------------
for x in range(10,173,8):
    box(x,x+1,38,47,FRONT+2,FRONT+3,CREAM4)
    for y in range(48,54):
        w=max(0,1-(y-48)//4)
        if w: box(x-w,x+1+w,y,y,FRONT+2,FRONT+3,CREAM3)
    put(x,54,FRONT+2,GOLD)
    for yy in range(40,54,4): put(x+2,yy,FRONT+3,GOLD)

# ---------------- 长屋顶 + 老虎窗 ----------------
for y in range(38,53):
    d=(y-38)
    z0=BACK+2+d; z1=FRONT-2-d
    if z0<=z1:
        box(8,172,y,y,z0,z1,ROOF if y%3 else ROOF2)
box(8,172,53,53,40,44,RIDGE)
for x in range(12,173,8):
    put(x,54,42,GOLD); put(x,55,42,GOLD)
for x in range(20,165,16):
    # 老虎窗：凸出屋顶，带三角顶/侧柱
    box(x-3,x+3,41,46,FRONT-10,FRONT-6,CREAM4)
    box(x-2,x+2,42,45,FRONT-6,FRONT-6,GLASS3)
    for xx in (x-3,x+3): box(xx,xx,41,46,FRONT-10,FRONT-6,CREAM3)
    for y in range(47,51):
        half=max(1,3-(y-47)); box(x-half,x+half,y,y,FRONT-10,FRONT-7,ROOF2)
    put(x,51,FRONT-8,GOLD)

# ---------------- 两座前凸侧阁（打破长条盒子） ----------------
for px in (40,140):
    # 凸出主体 4 格
    box(px-10,px+10,3,38,FRONT+2,FRONT+6,CREAM)
    box(px-11,px+11,18,20,FRONT+4,FRONT+8,CREAM4)
    box(px-11,px+11,36,38,FRONT+4,FRONT+8,CREAM4)
    # 三扇深窗
    for cx in (px-6,px,px+6):
        carve(cx-2,cx+2,7,30,FRONT+4,FRONT+6)
        box(cx-2,cx+2,7,30,FRONT+3,FRONT+3,DARK)
        gb=GLASS if (cx+px)%3 else GLASS2
        box(cx-1,cx+1,8,29,FRONT+4,FRONT+4,gb)
        # 石窗棂：中竖 + 两道横档，避免整块紫玻璃
        box(cx,cx,8,29,FRONT+5,FRONT+5,CREAM4)
        for yy in (14,21,27): box(cx-1,cx+1,yy,yy,FRONT+4,FRONT+5,CREAM4)
        for k in range(3): box(cx-2+k,cx+2-k,30+k,30+k,FRONT+4,FRONT+7,CREAM4)
        box(cx-2,cx+2,6,6,FRONT+4,FRONT+7,CREAM3)
    # 山墙 + 尖塔
    for y in range(39,50):
        half=max(1,round((50-y)*1.2))
        box(px-half,px+half,y,y,FRONT+5,FRONT+7,CREAM4)
    box(px,px,50,58,FRONT+6,FRONT+6,CREAM4)
    for y in range(58,65):
        w=max(0,1-(y-58)//4)
        if w: box(px-w,px+w,y,y,FRONT+5,FRONT+7,CREAM3)
    box(px,px,65,70,FRONT+6,FRONT+6,GOLD)
    box(px-2,px+2,68,68,FRONT+6,FRONT+6,GOLD)
    put(px,71,FRONT+6,GLOW)
    # 四角小尖
    for sx in (-1,1):
        for sz in (-1,1):
            box(px+sx*9,px+sx*9,38,48,FRONT+5+sz,FRONT+5+sz,CREAM4)
            put(px+sx*9,49,FRONT+5+sz,GOLD)

# ---------------- 中央门廊（更深一层） ----------------
# 凸出的三门廊
box(66,114,3,38,FRONT-2,FRONT+10,CREAM)
# 三个深拱门
for cx in (76,90,104):
    carve(cx-5,cx+5,4,21,FRONT+2,FRONT+11)
    box(cx-5,cx+5,3,3,FRONT+4,FRONT+10,DARK)
    for k in range(5):
        box(cx-5+k,cx+5-k,21+k,21+k,FRONT+4,FRONT+10,CREAM4)
    # 门内暗部/门
    box(cx-4,cx+4,4,18,FRONT+4,FRONT+4,DARK)
    box(cx-3,cx+3,4,4,FRONT+4,FRONT+5,WOOD)
    # 前柱
    for xx in (cx-6,cx+6):
        box(xx,xx,4,22,FRONT+10,FRONT+11,CREAM5)
        put(xx,23,FRONT+10,GOLD)
# 门廊上方玫瑰窗（不是蓝色横幅）
RCX,RCY,RZ=90,31,FRONT+9
for ang in range(0,360,8):
    a=math.radians(ang); put(RCX+round(9*math.cos(a)),RCY+round(9*math.sin(a)),RZ,CREAM4)
for dx in range(-8,9):
    for dy in range(-8,9):
        if dx*dx+dy*dy<=64: put(RCX+dx,RCY+dy,RZ,GLASS if (dx+dy)%3 else GLASS2)
for ang in range(0,360,30):
    a=math.radians(ang)
    for r in range(2,9): put(RCX+round(r*math.cos(a)),RCY+round(r*math.sin(a)),RZ+1,CREAM4)
for r in (4,8):
    for ang in range(0,360,12):
        a=math.radians(ang); put(RCX+round(r*math.cos(a)),RCY+round(r*math.sin(a)),RZ+1,CREAM4)
put(RCX,RCY,RZ+1,GOLD); put(RCX,RCY,RZ+2,GLOW)

# 门廊壁柱
for x in (68,112):
    box(x,x,3,38,FRONT+8,FRONT+10,CREAM4)
    for y in range(6,36,6): put(x,y,FRONT+11,GOLD)
# 中央门廊山墙/尖塔
for y in range(39,52):
    half=max(1,round((52-y)*2.0))
    box(90-half,90+half,y,y,FRONT+5,FRONT+9,CREAM4)
box(90,90,52,60,FRONT+7,FRONT+7,GOLD)
box(87,93,56,56,FRONT+7,FRONT+7,GOLD)
put(90,61,FRONT+7,GLOW)
# 门廊两翼小尖塔
for x in (66,114):
    box(x-2,x+2,38,52,FRONT+4,FRONT+8,CREAM4)
    for y in range(52,61):
        w=max(0,2-(y-52)//3)
        if w: box(x-w,x+w,y,y,FRONT+5,FRONT+7,CREAM3)
    put(x,62,FRONT+6,GOLD)
# 玫瑰窗/大窗在门廊上方
for ang in range(0,360,12):
    a=math.radians(ang)
    put(90+round(9*math.cos(a)),35+round(9*math.sin(a)),FRONT+9,CREAM4)
for dx in range(-7,8):
    for dy in range(-7,8):
        if dx*dx+dy*dy<=49: put(90+dx,35+dy,FRONT+9,GLASS if (dx+dy)%3 else GLASS2)
for ang in range(0,360,30):
    a=math.radians(ang)
    for r in range(2,8): put(90+round(r*math.cos(a)),35+round(r*math.sin(a)),FRONT+9,CREAM4)
put(90,35,FRONT+9,GOLD)

# ---------------- 中央圆顶 ----------------
# 鼓座：八角/圆，带窗/扶壁
DCX,DCZ=90,38
for y in range(38,62):
    r=22 if y<58 else 21
    for ang in range(0,360,6):
        a=math.radians(ang); x=round(DCX+r*math.cos(a)); z=round(DCZ+r*math.sin(a))
        put(x,y,z,CREAM if y<58 else CREAM3)
# 鼓座窗/壁柱
for ang in range(0,360,30):
    a=math.radians(ang)
    x=round(DCX+21*math.cos(a)); z=round(DCZ+21*math.sin(a))
    for y in range(44,58): put(x,y,z,GLASS if y%4 else CREAM4)
for ang in range(0,360,45):
    a=math.radians(ang)
    for r in (22,23):
        x=round(DCX+r*math.cos(a)); z=round(DCZ+r*math.sin(a))
        for y in range(38,66): put(x,y,z,CREAM4)
    put(x,67,z,GOLD)
# 圆顶（半球 + 12 道肋，不做成尖锥）
for y in range(62,92):
    t=(y-62)/30
    r=max(0,round(22*math.sqrt(max(0.0,1-t*t))))
    for ang in range(0,360,2):
        a=math.radians(ang); x=round(DCX+r*math.cos(a)); z=round(DCZ+r*math.sin(a))
        put(x,y,z,CREAM if y%2 else CREAM3)
    # 12 道深色/铜肋：只覆盖下 2/3，避免变成“针”
    if t<0.82:
        for ang in range(0,360,30):
            a=math.radians(ang); x=round(DCX+r*math.cos(a)); z=round(DCZ+r*math.sin(a))
            put(x,y,z,COPPER)
# 天窗/叶饰
for ang in range(0,360,60):
    a=math.radians(ang); x=round(DCX+12*math.cos(a)); z=round(DCZ+12*math.sin(a))
    put(x,76,z,GLOW)
# 顶 lantern
for y in range(92,104):
    for x in range(DCX-2,DCX+3):
        for z in range(DCZ-2,DCZ+3):
            if max(abs(x-DCX),abs(z-DCZ))<=2: put(x,y,z,CREAM4 if y%3 else GOLD)
box(DCX-1,DCX+1,104,106,DCZ-1,DCZ+1,GOLD)
box(DCX,DCX,106,112,DCZ,DCZ,GOLD)
box(DCX-3,DCX+3,109,109,DCZ,DCZ,GOLD)
put(DCX,113,DCZ,GLOW)

# ---------------- 双塔（中央圆顶两侧） ----------------
for tx in (48,132):
    tz=48
    box(tx-5,tx+5,3,62,tz-5,tz+5,CREAM)
    # 塔身窗/线脚
    for y in (18,36,54): box(tx-6,tx+6,y,y,tz-6,tz+6,CREAM3)
    for y in range(4,58,8):
        box(tx-1,tx+1,y,y+3,tz+6,tz+6,GLASS)
    # 尖顶
    for y in range(62,82):
        t=(y-62)/20; w=max(0,round(5*(1-t)))
        if w==0: put(tx,y,tz,CREAM4)
        else:
            for x in range(tx-w,tx+w+1):
                for z in range(tz-w,tz+w+1):
                    if max(abs(x-tx),abs(z-tz))==w: put(x,y,z,CREAM4 if y%2 else CREAM3)
    box(tx,tx,82,88,tz,tz,GOLD)
    box(tx-3,tx+3,85,85,tz,tz,GOLD)
    put(tx,89,tz,GLOW)
    # 四角小尖
    for sx in (-1,1):
        for sz in (-1,1):
            box(tx+sx*5,tx+sx*5,62,70,tz+sz*5,tz+sz*5,CREAM4)
            put(tx+sx*5,71,tz+sz*5,GOLD)

# ---------------- 两端 pavilion / 塔 ----------------
for px in (16,164):
    pz=52
    box(px-9,px+9,3,44,pz-9,pz+9,CREAM)
    box(px-10,px+10,44,46,pz-10,pz+10,CREAM4)
    # 端部尖塔
    for y in range(46,66):
        t=(y-46)/20; w=max(0,round(6*(1-t)))
        if w: 
            for x in range(px-w,px+w+1):
                for z in range(pz-w,pz+w+1):
                    if max(abs(x-px),abs(z-pz))==w: put(x,y,z,ROOF2 if y%2 else CREAM4)
    box(px,px,66,72,pz,pz,GOLD); box(px-3,px+3,69,69,pz,pz,GOLD)

# ---------------- 背面/侧翼屋顶/细节 ----------------
for y in range(38,50):
    d=y-38
    box(8,172,y,y,BACK+d,FRONT-2-d,ROOF if y%3 else ROOF2)
# 背立面窗
for x in range(16,168,10):
    box(x,x+4,22,32,BACK+2,BACK+2,DARK)
    box(x+1,x+3,23,31,BACK+2,BACK+2,GLASS)

# 河岸亭/旗杆
for x in (36,144):
    box(x-3,x+3,2,6,80,84,CREAM4)
    for y in range(7,15): put(x,y,82,GOLD)
    put(x,15,82,GLOW)

# ---------------- 内院/采光庭（圣维蕾娜式虚空间） ----------------
for (cx0,cx1,cz0,cz1) in ((18,46,42,70),(134,162,42,70)):
    # 打开屋顶，形成真正的天井
    carve(cx0,cx1,38,55,cz0,cz1)
    # 清除内部可能残留的体块（保留外墙）
    carve(cx0+2,cx1-2,3,37,cz0+2,cz1-2)
    # 庭院铺地/草地/十字步道
    box(cx0+1,cx1-1,1,1,cz0+1,cz1-1,GRASS)
    box(cx0+1,cx1-1,2,2,cz0+1,cz1-1,CREAM2)
    midx=(cx0+cx1)//2; midz=(cz0+cz1)//2
    box(midx-1,midx+1,3,3,cz0+1,cz1-1,CREAM3)
    box(cx0+1,cx1-1,3,3,midz-1,midz+1,CREAM3)
    # 四周围合墙（留拱洞）
    for x in range(cx0,cx1+1):
        for z in (cz0,cz1):
            box(x,x,3,37,z,z,CREAM if (x//4)%2 else STONE)
    for z in range(cz0,cz1+1):
        for x in (cx0,cx1):
            box(x,x,3,37,z,z,CREAM if (z//4)%2 else STONE)
    # 连拱回廊：柱+尖拱，真正凹进
    for x in range(cx0+2,cx1-1,4):
        for z in (cz0,cz1):
            box(x,x,3,14,z,z,CREAM4)
            for k in range(3): box(x-1+k,x+1-k,14+k,14+k,z,z,CREAM4)
    for z in range(cz0+2,cz1-1,4):
        for x in (cx0,cx1):
            box(x,x,3,14,z,z,CREAM4)
            for k in range(3): box(x,x,14+k,14+k,z-1+k,z+1-k,CREAM4)
    # 回廊顶/檐口
    box(cx0,cx1,15,16,cz0,cz0+2,CREAM3); box(cx0,cx1,15,16,cz1-2,cz1,CREAM3)
    box(cx0,cx0+2,15,16,cz0,cz1,CREAM3); box(cx1-2,cx1,15,16,cz0,cz1,CREAM3)
    # 庭院树/灯
    for tx,tz in ((cx0+7,cz0+8),(cx1-7,cz1-8)):
        for y in range(3,7): put(tx,y,tz,LOG)
        box(tx-2,tx+2,7,9,tz-2,tz+2,LEAVES)
    for tx,tz in ((cx0+4,midz),(cx1-4,midz)):
        for y in range(3,6): put(tx,y,tz,TRIM)
        put(tx,6,tz,GLOW)
    # 天井栏板/角尖
    for x in range(cx0,cx1+1,4):
        for z in (cz0-1,cz1+1): put(x,38,z,CREAM4)
    for z in range(cz0,cz1+1,4):
        for x in (cx0-1,cx1+1): put(x,38,z,CREAM4)
    for x in (cx0-1,cx1+1):
        for z in (cz0-1,cz1+1):
            box(x,x,38,44,z,z,CREAM4); put(x,45,z,GOLD)

# 两座议事厅 pavilion 的铜绿陡屋顶（把长条屋顶断开）
for px in (40,140):
    for y in range(38,56):
        inset=max(0,(y-38)//2)
        box(px-10+inset,px+10-inset,y,y,FRONT-16,FRONT-4,ROOF2 if y%4 else ROOF)
    box(px,px,56,64,FRONT-10,FRONT-10,COPPER)
    box(px-3,px+3,61,61,FRONT-10,FRONT-10,COPPER)
    put(px,65,FRONT-10,GOLD)

# 石色分带：下部深、 中部暖、 上部浅；不是一堵奶油墙
for (x,y,z),b in list(V.items()):
    if b!=CREAM: continue
    if y<6: V[(x,y,z)]="blackstone"
    elif y<20: V[(x,y,z)]= "stone_bricks" if (x//8+z//8)%2 else "tuff"
    elif y<30: V[(x,y,z)]= "stone_bricks" if (x//6)%3==0 else CREAM
    elif y>55: V[(x,y,z)]= "calcite" if (x+y)%7==0 else CREAM3

# ---------------- 输出 ----------------
vox=len(V); counts=Counter(V.values())
print("voxels",vox); print("palette",counts.most_common())
# 3D greedy fill compression：比逐层/逐列少一个数量级的命令
remaining=set(V); fills=[]; MAXV=30000
for x,y,z in sorted(V):
    if (x,y,z) not in remaining: continue
    b=V[(x,y,z)]
    # x
    x2=x
    while (x2+1,y,z) in remaining and V[(x2+1,y,z)]==b: x2+=1
    # z
    z2=z
    while True:
        if (x2-x+1)*(z2-z+2)>MAXV: break
        ok=True
        for xx in range(x,x2+1):
            if (xx,y,z2+1) not in remaining or V[(xx,y,z2+1)]!=b: ok=False; break
        if not ok: break
        z2+=1
    # y
    y2=y
    while True:
        if (x2-x+1)*(z2-z+1)*(y2-y+2)>MAXV: break
        ok=True
        for xx in range(x,x2+1):
            for zz in range(z,z2+1):
                if (xx,y2+1,zz) not in remaining or V[(xx,y2+1,zz)]!=b: ok=False; break
            if not ok: break
        if not ok: break
        y2+=1
    for xx in range(x,x2+1):
        for yy in range(y,y2+1):
            for zz in range(z,z2+1): remaining.discard((xx,yy,zz))
    fills.append({"from":[x,y,z],"to":[x2,y2,z2],"block":b})
(HERE/"fills.json").write_text(json.dumps(fills,ensure_ascii=False),encoding="utf-8")
(HERE/"plan.json").write_text(json.dumps({"name":"hungarian-parliament","voxels":vox,"fills":len(fills),
    "start":[210,0,250],"center":[300,0,300],"facade_z":330,"dome":113,"palette":dict(counts)},ensure_ascii=False,indent=2),encoding="utf-8")
items=[BuildBlock(x,y,z,b) for (x,y,z),b in V.items()]
write_build_bdx(items,str(HERE/"parliament-631.bdx"))
print("bdx",len(items),"fills",len(fills))
