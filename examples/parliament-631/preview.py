#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import gen_parliament as G
COL={"smooth_quartz":(235,230,216),"stone_bricks":(142,139,131),"calcite":(232,228,212),
     "polished_andesite":(143,141,134),"andesite":(132,130,124),"tuff":(112,108,98),
     "blackstone":(38,37,43),"polished_deepslate":(58,57,64),"deepslate_tiles":(48,47,54),
     "weathered_copper":(82,165,143),"red_terracotta":(150,70,55),"oxidized_copper":(65,145,125),
     "blue_stained_glass":(60,120,210),"purple_stained_glass":(125,75,180),
     "black_stained_glass":(25,24,30),"gold_block":(232,190,62),
     "sea_lantern":(168,240,208),"water":(48,105,180),
     "grass_block":(84,132,62),"dark_oak_leaves":(45,95,52),"dark_oak_log":(76,55,36),
     "dark_oak_planks":(70,48,30),"polished_diorite":(180,178,170),"quartz_block":(225,220,205)}
pts=list(G.V.items())
# front elevation from south
front={}
for (x,y,z),b in pts:
    k=(x,y)
    if k not in front or z>front[k][0]: front[k]=(z,b)
minx=min(x for x,y in front); maxx=max(x for x,y in front); miny=min(y for x,y in front); maxy=max(y for x,y in front)
F=5; W=(maxx-minx+1)*F+30; H=(maxy-miny+1)*F+30
img=Image.new('RGB',(W,H),(14,18,28)); d=ImageDraw.Draw(img)
for yy in range(H):
    t=yy/H; d.line([(0,yy),(W,yy)],fill=(int(14+18*t),int(18+24*t),int(28+38*t)))
for (x,y),(z,b) in front.items():
    c=COL.get(b,(255,0,255)); px=(x-minx)*F+15; py=(maxy-y)*F+15
    d.rectangle([px,py,px+F-1,py+F-1],fill=c)
d.text((20,10),"匈牙利国会大厦 · 河岸立面 · 多层凹进/拱廊/尖顶",fill=(240,244,250))
img.save(HERE/'front.png'); print('front',img.size)

# isometric (S=2) for a readable but not huge view
S=2
def proj(x,y,z): return ((x-z)*S,(x+z)*S//2-y*S)
xs=[p[0][0] for p in pts]; ys=[p[0][1] for p in pts]; zs=[p[0][2] for p in pts]
corner=[proj(x,y,z) for x in (min(xs),max(xs)) for y in (min(ys),max(ys)) for z in (min(zs),max(zs))]
minpx=min(c[0] for c in corner)-20; maxpx=max(c[0] for c in corner)+20
minpy=min(c[1] for c in corner)-20; maxpy=max(c[1] for c in corner)+60
W=maxpx-minpx; H=maxpy-minpy
img=Image.new('RGB',(W,H),(10,14,24)); d=ImageDraw.Draw(img)
for yy in range(H):
    t=yy/H; d.line([(0,yy),(W,yy)],fill=(int(10+20*t),int(14+24*t),int(24+38*t)))
ox,oy=-minpx,-minpy
for (x,y,z),b in sorted(pts,key=lambda p:(p[0][0]+p[0][2]+p[0][1],p[0][1],p[0][0])):
    sx,sy=proj(x,y,z); sx+=ox; sy+=oy
    base=COL.get(b,(255,0,255)); top=tuple(min(255,int(c*1.08)) for c in base)
    left=tuple(int(c*.72) for c in base); right=tuple(int(c*.50) for c in base)
    d.polygon([(sx,sy-S//2),(sx+S//2,sy),(sx,sy+S//2),(sx-S//2,sy)],fill=top)
    d.polygon([(sx-S//2,sy),(sx,sy+S//2),(sx,sy+S//2+S),(sx-S//2,sy+S)],fill=left)
    d.polygon([(sx+S//2,sy),(sx,sy+S//2+S),(sx+S//2,sy+S)],fill=right)
img=img.resize((W*2,H*2),Image.Resampling.LANCZOS)
d=ImageDraw.Draw(img); d.text((30,24),"匈牙利国会大厦 · 631 / 深度立面 / 中央圆顶",fill=(240,244,250))
img.save(HERE/'iso.png'); print('iso',img.size)
