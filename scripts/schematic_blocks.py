#!/usr/bin/env python3
"""Print dimensions + block palette/counts for one .schematic/.schem.

Supports:
- Sponge v2: Palette + BlockData (varint palette indices)
- Classic MCEdit: Blocks byte array (numeric IDs)
"""
from __future__ import annotations
import argparse, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from sunrain_index import nbt_root

# common classic IDs (partial; enough for style summaries)
CLASSIC = {
 0:"air",1:"stone",2:"grass_block",3:"dirt",4:"cobblestone",5:"oak_planks",6:"oak_sapling",7:"bedrock",8:"water",9:"water",10:"lava",11:"lava",12:"sand",13:"gravel",14:"gold_ore",15:"iron_ore",16:"coal_ore",17:"oak_log",18:"oak_leaves",19:"sponge",20:"glass",21:"lapis_ore",22:"lapis_block",23:"dispenser",24:"sandstone",25:"note_block",26:"red_bed",27:"golden_rail",28:"detector_rail",29:"sticky_piston",30:"cobweb",31:"grass",32:"dead_bush",33:"piston",34:"piston_head",35:"white_wool",37:"dandelion",38:"poppy",39:"brown_mushroom",40:"red_mushroom",41:"gold_block",42:"iron_block",43:"stone_slab",44:"stone_slab",45:"bricks",46:"tnt",47:"bookshelf",48:"mossy_cobblestone",49:"obsidian",50:"torch",51:"fire",52:"spawner",53:"oak_stairs",54:"chest",55:"redstone_wire",56:"diamond_ore",57:"diamond_block",58:"crafting_table",59:"wheat",60:"farmland",61:"furnace",62:"furnace",63:"oak_sign",64:"oak_door",65:"ladder",66:"rail",67:"stone_stairs",68:"oak_wall_sign",69:"lever",70:"stone_pressure_plate",71:"iron_door",72:"oak_pressure_plate",73:"redstone_ore",74:"redstone_ore",75:"redstone_torch",76:"redstone_torch",77:"stone_button",78:"snow",79:"ice",80:"snow_block",81:"cactus",82:"clay",83:"sugar_cane",84:"jukebox",85:"oak_fence",86:"pumpkin",87:"netherrack",88:"soul_sand",89:"glowstone",90:"nether_portal",91:"jack_o_lantern",92:"cake",93:"repeater",94:"repeater",95:"white_stained_glass",96:"oak_trapdoor",97:"infested_stone",98:"stone_bricks",99:"brown_mushroom_block",100:"red_mushroom_block",101:"iron_bars",102:"glass_pane",103:"melon",104:"pumpkin_stem",105:"melon_stem",106:"vine",107:"oak_fence_gate",108:"brick_stairs",109:"stone_brick_stairs",110:"mycelium",111:"lily_pad",112:"nether_bricks",113:"nether_brick_fence",114:"nether_brick_stairs",115:"nether_wart",116:"enchanting_table",117:"brewing_stand",118:"cauldron",119:"end_portal",120:"end_portal_frame",121:"end_stone",122:"dragon_egg",123:"redstone_lamp",124:"redstone_lamp",125:"oak_slab",126:"oak_slab",127:"cocoa",128:"sandstone_stairs",129:"emerald_ore",130:"ender_chest",131:"tripwire_hook",132:"tripwire",133:"emerald_block",134:"spruce_stairs",135:"birch_stairs",136:"jungle_stairs",137:"command_block",138:"beacon",139:"cobblestone_wall",140:"flower_pot",141:"carrots",142:"potatoes",143:"oak_button",144:"skeleton_skull",145:"anvil",146:"trapped_chest",147:"light_weighted_pressure_plate",148:"heavy_weighted_pressure_plate",149:"comparator",150:"comparator",151:"daylight_detector",152:"redstone_block",153:"nether_quartz_ore",154:"hopper",155:"quartz_block",156:"quartz_stairs",157:"activator_rail",158:"dropper",159:"white_terracotta",160:"white_stained_glass_pane",161:"dark_oak_leaves",162:"dark_oak_log",163:"acacia_stairs",164:"dark_oak_stairs",165:"slime_block",166:"barrier",167:"iron_trapdoor",168:"prismarine",169:"sea_lantern",170:"hay_block",171:"white_carpet",172:"terracotta",173:"coal_block",174:"packed_ice",175:"sunflower",176:"white_banner",177:"white_wall_banner",178:"daylight_detector",179:"red_sandstone",180:"red_sandstone_stairs",181:"stone_slab",182:"stone_slab",183:"spruce_fence_gate",184:"birch_fence_gate",185:"jungle_fence_gate",186:"dark_oak_fence_gate",187:"acacia_fence_gate",188:"dark_oak_fence",189:"acacia_fence",190:"spruce_fence",191:"birch_fence",192:"jungle_fence",193:"spruce_door",194:"birch_door",195:"jungle_door",196:"acacia_door",197:"dark_oak_door",198:"end_rod",199:"chorus_plant",200:"chorus_flower",201:"purpur_block",202:"purpur_pillar",203:"purpur_stairs",204:"purpur_slab",205:"purpur_slab",206:"end_stone_bricks",207:"end_stone_brick_fence",208:"end_stone_brick_stairs",209:"end_stone_brick_wall",210:"white_glazed_terracotta",211:"orange_glazed_terracotta",212:"magenta_glazed_terracotta",213:"light_blue_glazed_terracotta",214:"yellow_glazed_terracotta",215:"lime_glazed_terracotta",216:"pink_glazed_terracotta",217:"gray_glazed_terracotta",218:"light_gray_glazed_terracotta",219:"cyan_glazed_terracotta",220:"purple_glazed_terracotta",221:"blue_glazed_terracotta",222:"brown_glazed_terracotta",223:"green_glazed_terracotta",224:"red_glazed_terracotta",225:"black_glazed_terracotta",251:"white_concrete",252:"white_concrete_powder",
}

def varints(data):
    out=[]; v=0; sh=0
    for b in data:
        v |= (b & 0x7f) << sh
        if not (b & 0x80): out.append(v); v=0; sh=0
        else: sh += 7

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--top",type=int,default=15); ap.add_argument("--include-air",action="store_true")
    a=ap.parse_args()
    name,root=nbt_root(a.file, full=True)
    w=root.get("Width",0); h=root.get("Height",0); l=root.get("Length",0)
    print(f"{os.path.basename(a.file)}  {w}x{h}x{l}  keys={len(root)}")
    if "Palette" in root and isinstance(root["Palette"],dict):
        pal={int(v):k for k,v in root["Palette"].items()}
        print("format=sponge palette",len(pal),"blockdata",len(root.get("BlockData",("",0,b""))[2]) if isinstance(root.get("BlockData"),tuple) else "?")
        data=root.get("BlockData")
        if isinstance(data,tuple) and len(data)>=3 and isinstance(data[2],(bytes,bytearray)):
            c=Counter(varints(data[2]))
            if not a.include_air:
                c.pop(0,None)
            total=sum(c.values()) or 1
            for i,n in c.most_common(a.top): print(f"{100*n/total:5.1f}% {pal.get(i,'?'+str(i))}")
    elif "Blocks" in root:
        data=root["Blocks"]
        raw=data[2] if isinstance(data,tuple) and len(data)>=3 else b""
        c=Counter(raw)
        if not a.include_air:
            c.pop(0,None)
        total=sum(c.values()) or 1
        print("format=classic blocks",len(raw),"non-air",total)
        for i,n in c.most_common(a.top): print(f"{100*n/total:5.1f}% {CLASSIC.get(i,'id:'+str(i))}")
    else:
        print("format=unknown", root.keys())

if __name__=="__main__": main()
