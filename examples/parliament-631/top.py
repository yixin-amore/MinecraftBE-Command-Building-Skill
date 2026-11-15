import sys
from pathlib import Path
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import gen_parliament as G
COL={"smooth_quartz":(235,230,216),"stone_bricks":(142,139,131),"calcite":(232,228,212),"polished_diorite":(180,178,170),"tuff":(112,108,98),"blackstone":(38,37,43),"polished_deepslate":(58,57,64),"deepslate_tiles":(48,47,54),"red_terracotta":(150,70,55),"weathered_copper":(82,165,143),"oxidized_copper":(65,145,125),"blue_stained_glass":(60,120,210),"purple_stained_glass":(125,75,180),"black_stained_glass":(25,24,30),"gold_block":(232,190,62),"sea_lantern":(168,240,208),"water":(48,105,180),"grass_block":(84,132,62),"dark_oak_leaves":(45,95,52),"dark_oak_log":(76,55,36),"dark_oak_planks":(70,48,30),"quartz_block":(225,220,205)}
top={}
for (x,y,z),b in G.V.items():
 k=(x,z)
 if k not in top or y>top[k][0]: top[k]=(y,b)
minx=min(x for x,z in top);maxx=max(x for x,z in top);minz=min(z for x,z in top);maxz=max(z for x,z in top)
img=Image.new('RGB',(maxx-minx+1,maxz-minz+1),(10,14,24));d=ImageDraw.Draw(img)
for (x,z),(y,b) in top.items(): d.point((x-minx,z-minz),fill=COL.get(b,(255,0,255)))
img=img.resize(((maxx-minx+1)*3,(maxz-minz+1)*3),Image.Resampling.NEAREST)
img.save(HERE/'top.png');print(img.size)
