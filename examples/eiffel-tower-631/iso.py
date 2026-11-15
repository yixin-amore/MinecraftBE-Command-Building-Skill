#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import gen_eiffel as G

COL={
 "deepslate_tiles":(64,64,74),"polished_deepslate":(46,46,54),
 "iron_bars":(165,171,180),"polished_blackstone":(27,26,32),
 "chiseled_deepslate":(86,86,96),"gold_block":(231,189,69),
 "sea_lantern":(168,240,208),"glass":(165,215,230),
 "smooth_stone":(169,169,162),"grass_block":(93,138,75),
 "oak_leaves":(62,116,65),"oak_log":(107,81,52),"water":(63,120,200),
 "redstone_lamp":(216,84,69),"blue_wool":(53,88,184),
 "white_wool":(232,232,226),"red_wool":(184,60,70),
}
S=5
pts=[]
for (x,y,z),b in G.V.items():
    pts.append((x,y,z,b))
pts.sort(key=lambda p:(p[0]+p[2]+p[1],p[1],p[0]))
def proj(x,y,z):
    return ((x-z)*S, (x+z)*S//2 - y*S)
# bounds
minx=min(p[0] for p in pts); maxx=max(p[0] for p in pts)
miny=min(p[1] for p in pts); maxy=max(p[1] for p in pts)
minz=min(p[2] for p in pts); maxz=max(p[2] for p in pts)
corners=[proj(x,y,z) for x in (minx,maxx) for y in (miny,maxy) for z in (minz,maxz)]
minpx=min(c[0] for c in corners)-20; maxpx=max(c[0] for c in corners)+20
minpy=min(c[1] for c in corners)-20; maxpy=max(c[1] for c in corners)+80
W=maxpx-minpx; H=maxpy-minpy
img=Image.new("RGB",(W,H),(8,12,22)); d=ImageDraw.Draw(img)
for yy in range(H):
    t=yy/H
    d.line([(0,yy),(W,yy)],fill=(int(8+16*t),int(12+20*t),int(22+34*t)))
ox,oy=-minpx,-minpy
for x,y,z,b in pts:
    sx,sy=proj(x,y,z); sx+=ox; sy+=oy
    base=COL.get(b,(255,0,255))
    # top/left/right with simple lighting
    top=tuple(min(255,int(c*1.14)) for c in base)
    left=tuple(int(c*.72) for c in base)
    right=tuple(int(c*.50) for c in base)
    d.polygon([(sx,sy-S//2),(sx+S//2,sy),(sx,sy+S//2),(sx-S//2,sy)],fill=top)
    d.polygon([(sx-S//2,sy),(sx,sy+S//2),(sx,sy+S//2+S),(sx-S//2,sy+S)],fill=left)
    d.polygon([(sx+S//2,sy),(sx,sy+S//2),(sx,sy+S//2+S),(sx+S//2,sy+S)],fill=right)
img=img.resize((W*2,H*2),Image.Resampling.LANCZOS)
d=ImageDraw.Draw(img)
d.text((30,24),"埃菲尔铁塔 · 631 / 黄金比例 · 64×64×192",fill=(230,240,250))
d.text((30,48),"60% 基座 / 30% 塔身 / 10% 塔冠 · 深色 60 / 铁栏 30 / 金灯 10",fill=(150,175,195))
d.text((30,72),"StartPos 256 0 256 · center 300 0 300 · flag top 199",fill=(120,150,170))
img.save(HERE/"iso.png")
print("wrote iso.png",img.size)
