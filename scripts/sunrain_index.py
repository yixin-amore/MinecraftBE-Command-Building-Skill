#!/usr/bin/env python3
"""Index a mixed Minecraft BE/Java building + command corpus.

- .schematic: classic MCEdit NBT or Sponge v2 (Palette/BlockData)
- .schem: Sponge NBT
- .bdx: command blocks (uses mcbeextract if available)
- images: dimensions/pairing
Outputs index.jsonl, stats.json, catalog.md, contact-sheet.jpg
"""
from __future__ import annotations
import argparse, gzip, io, json, math, os, re, struct, subprocess, sys
from collections import Counter, defaultdict

TAG_NAMES = {0:"end",1:"byte",2:"short",3:"int",4:"long",5:"float",6:"double",7:"byte_array",8:"string",9:"list",10:"compound",11:"int_array",12:"long_array"}

def _read(f, t, keep=True, full=False):
    if t == 1: return struct.unpack(">b", f.read(1))[0]
    if t == 2: return struct.unpack(">h", f.read(2))[0]
    if t == 3: return struct.unpack(">i", f.read(4))[0]
    if t == 4: return struct.unpack(">q", f.read(8))[0]
    if t == 5: return struct.unpack(">f", f.read(4))[0]
    if t == 6: return struct.unpack(">d", f.read(8))[0]
    if t == 7:
        n = struct.unpack(">i", f.read(4))[0]
        if keep and full: return ("bytes", n, f.read(n))
        f.seek(n, 1); return ("bytes", n)
    if t == 8:
        n = struct.unpack(">H", f.read(2))[0]
        return f.read(n).decode("utf-8", "replace")
    if t == 9:
        et = struct.unpack(">b", f.read(1))[0]
        n = struct.unpack(">i", f.read(4))[0]
        if (not keep) or (not full):
            for _ in range(n): _read(f, et, False, False)
            return ("list", et, n)
        return ("list", et, n, [_read(f, et, True, True) for _ in range(n)])
    if t == 10:
        d = {}
        while True:
            tt = struct.unpack(">b", f.read(1))[0]
            if tt == 0: return d
            ln = struct.unpack(">H", f.read(2))[0]
            name = f.read(ln).decode("utf-8", "replace")
            d[name] = _read(f, tt, keep, full)
    if t == 11:
        n = struct.unpack(">i", f.read(4))[0]
        if keep and full: return ("ints", n, f.read(n * 4))
        f.seek(n * 4, 1); return ("ints", n)
    if t == 12:
        n = struct.unpack(">i", f.read(4))[0]
        if keep and full: return ("longs", n, f.read(n * 8))
        f.seek(n * 8, 1); return ("longs", n)
    raise ValueError(f"tag {t}")

def nbt_root(path, full=False):
    raw = open(path, "rb").read(2)
    if raw == b"\x1f\x8b":
        f = gzip.open(path, "rb")
    else:
        f = open(path, "rb")
    with f:
        t = struct.unpack(">b", f.read(1))[0]
        n = struct.unpack(">H", f.read(2))[0]
        name = f.read(n).decode("utf-8", "replace")
        return name, _read(f, t, True, full)

def count_len(v):
    if isinstance(v, tuple):
        return v[2] if len(v) >= 3 else 0
    return len(v) if hasattr(v, "__len__") else 0

def classify(path, ext):
    p = path.lower()
    if ext in (".png",".jpg",".jpeg",".webp",".bmp",".gif"): return "visual"
    if ext == ".bdx": return "command"
    if "/音乐" in path or "music" in p: return "music"
    if "像素画" in path: return "pixelart"
    if "空岛" in path: return "skyblock"
    if "起床" in path: return "bedwars"
    if "lobby" in p or "大厅" in path or "主城" in path: return "lobby"
    if "game" in p or "游戏" in path: return "game"
    if "建筑" in path or "高质量" in path or "归寻" in path or "珍品" in path: return "architecture"
    if "schematic杂项" in path: return "misc_build"
    if "更新" in path: return "update"
    return "misc"

FUNC = ["主城","lobby","大厅","空岛","起床","战场","游戏","商店","菜单","出生点","传送","boss","跑酷","迷宫","塔防","竞技场","生存","阵营","副本","大厅"]
STYLE = ["中世纪","现代","中式","日式","欧式","幻想","蒸汽","赛博","自然","废墟","卡通","简约","哥特","和风","国风","魔幻","末日","未来","蒸汽朋克"]
ELEM = ["树","雕像","桥","门","塔","墙","喷泉","花园","内饰","家具","灯光","红石","命令","像素画","城堡","村庄","城市","森林","雪山","海岛","浮空","宫殿","神庙","庭院"]

def tokens(name):
    return re.findall(r"[\u4e00-\u9fff]+|[A-Za-z0-9_]+", name)

def tags_for(path):
    name = os.path.basename(path)
    tags = set()
    for t in FUNC:
        if t.lower() in name.lower() or t in path: tags.add("func:"+t)
    for t in STYLE:
        if t in name or t in path: tags.add("style:"+t)
    for t in ELEM:
        if t in name: tags.add("elem:"+t)
    return sorted(tags)

def image_meta(path):
    try:
        from PIL import Image
        with Image.open(path) as im: return {"w": im.width, "h": im.height, "format": im.format}
    except Exception as e:
        return {"error": str(e)[:80]}

def bdx_meta(path, tool):
    if not tool or not os.path.exists(tool): return {"error":"mcbeextract missing"}
    try:
        r = subprocess.run([tool, path], capture_output=True, text=True, timeout=20)
        d = json.loads(r.stdout)
        cbs = d.get("command_blocks") or []
        types = Counter(x.get("type") for x in cbs)
        starts = Counter((x.get("command") or "").strip().split()[0] if (x.get("command") or "").strip() else "" for x in cbs)
        return {"commands": len(cbs), "size": d.get("size"), "types": dict(types), "starts": dict(starts.most_common(12)), "error": d.get("error")}
    except Exception as e:
        return {"error": str(e)[:120]}

def schematic_meta(path):
    try:
        name, root = nbt_root(path)
        out = {"root": name, "keys": sorted(root.keys())}
        for k in ("Width","Height","Length"):
            if k in root: out[k.lower()] = root[k]
        out["materials"] = root.get("Materials")
        out["dataversion"] = root.get("DataVersion")
        out["format"] = "sponge" if "Palette" in root else ("classic" if "Blocks" in root else "unknown")
        if "Palette" in root and isinstance(root["Palette"], dict):
            pal = root["Palette"]
            out["palette_size"] = len(pal)
            out["palette_sample"] = list(pal.keys())[:30]
        if "BlockData" in root: out["blockdata_len"] = count_len(root["BlockData"])
        if "Blocks" in root: out["blocks_len"] = count_len(root["Blocks"])
        if "Data" in root: out["data_len"] = count_len(root["Data"])
        for k in ("TileEntities","Entities","TileTicks"):
            out[k.lower()+"_count"] = count_len(root.get(k))
        if "BlockIDs" in root: out["blockids_count"] = count_len(root["BlockIDs"])
        if "ItemIDs" in root: out["itemids_count"] = count_len(root["ItemIDs"])
        out["has_command"] = "Command" in root
        if "Command" in root: out["command"] = str(root["Command"])[:200]
        return out
    except Exception as e:
        return {"error": str(e)[:120]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("out")
    ap.add_argument("--mcbeextract", default="/tmp/mcbeextract")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-image-meta", action="store_true")
    ap.add_argument("--skip-bdx-meta", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    files = []
    for dp, dn, fn in os.walk(args.root):
        for f in fn:
            if f.startswith("."): continue
            p = os.path.join(dp, f)
            ext = os.path.splitext(f)[1].lower()
            files.append((p, ext))
    files.sort()
    if args.limit: files = files[:args.limit]

    images = {}
    for p, ext in files:
        if ext in (".png",".jpg",".jpeg",".webp",".bmp",".gif"):
            images.setdefault(os.path.splitext(os.path.basename(p))[0], []).append(p)

    rows = []
    for i, (p, ext) in enumerate(files):
        rel = os.path.relpath(p, args.root)
        try: size = os.path.getsize(p)
        except: size = 0
        cat = classify(rel, ext)
        row = {"path": rel, "ext": ext, "bytes": size, "category": cat, "tags": tags_for(rel), "stem": os.path.splitext(os.path.basename(p))[0]}
        if not rel.startswith("."):
            if ext in (".schematic",".schem"):
                row.update(schematic_meta(p))
                if row["stem"] in images: row["paired_image"] = images[row["stem"]][0]
            elif ext == ".bdx":
                row["bdx"] = {"skipped": True} if args.skip_bdx_meta else bdx_meta(p, args.mcbeextract)
            elif ext in (".png",".jpg",".jpeg",".webp",".bmp",".gif"):
                row["image"] = {"skipped": True} if args.skip_image_meta else image_meta(p)
        rows.append(row)
        if (i+1) % 200 == 0: print(f"{i+1}/{len(files)}", file=sys.stderr)
    with open(os.path.join(args.out,"index.jsonl"),"w",encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+"\n")

    ext_counts = Counter(r["ext"] for r in rows)
    cat_counts = Counter(r["category"] for r in rows)
    tag_counts = Counter(t for r in rows for t in r["tags"])
    formats = Counter(r.get("format","-") for r in rows if r["ext"] in (".schematic",".schem"))
    paired = sum(1 for r in rows if r.get("paired_image"))
    bdx_cmds = sum((r.get("bdx") or {}).get("commands",0) for r in rows)
    dims = [r for r in rows if r.get("width") and r.get("height") and r.get("length")]
    stats = {"root":args.root,"files":len(rows),"bytes":sum(r["bytes"] for r in rows),"ext":dict(ext_counts),"category":dict(cat_counts),"tags":dict(tag_counts.most_common(80)),"schematic_formats":dict(formats),"paired_images":paired,"bdx_commands_total":bdx_cmds,"schematic_with_dims":len(dims),"total_volume":sum(r["width"]*r["height"]*r["length"] for r in dims)}
    json.dump(stats, open(os.path.join(args.out,"stats.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

    def score(r):
        s = 0
        if r["category"] == "architecture": s += 30
        if r["category"] in ("lobby","skyblock","bedwars","game","misc_build"): s += 10
        if r.get("paired_image"): s += 20
        if r.get("bytes"): s += min(20, math.log2(max(1,r["bytes"]))*2)
        if r.get("width"): s += min(15, math.log2(max(1,r["width"]*r["height"]*r["length"]))/2)
        if any(t.startswith("quality:") for t in r["tags"]): s += 10
        if any(x in r["path"] for x in ("珍品","高质量","[全]","服务器","推荐")): s += 15
        return s
    for r in rows: r["score"] = round(score(r),1)
    with open(os.path.join(args.out,"index.jsonl"),"w",encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+"\n")

    bycat = defaultdict(list)
    for r in rows:
        if r["ext"] in (".schematic",".schem") and r.get("width"):
            bycat[r["category"]].append(r)
    lines = ["# Sunrain 建筑/指令语料索引","",f"- 文件：{len(rows)}；总大小：{sum(r['bytes'] for r in rows)/1024/1024:.1f} MB",f"- 建筑/结构：{sum(1 for r in rows if r['ext'] in ('.schematic','.schem'))}；BDX：{sum(1 for r in rows if r['ext']=='.bdx')}；图片：{sum(1 for r in rows if r['ext'] in ('.png','.jpg','.jpeg','.webp','.bmp','.gif'))}","","## 分类",""]
    for k,v in cat_counts.most_common(): lines.append(f"- {k}: {v}")
    lines += ["","## 结构格式",""] + [f"- {k}: {v}" for k,v in formats.most_common()]
    lines += ["","## 高价值样板（按类别）",""]
    for cat, items in sorted(bycat.items(), key=lambda kv:-len(kv[1])):
        items.sort(key=lambda r:-r["score"])
        lines += [f"### {cat}（{len(items)}）","","| # | 名称 | 尺寸 W×H×L | 大小 | 标签 | 配对图 |","|---:|---|---:|---:|---|---|"]
        for i,r in enumerate(items[:12],1):
            dim = f"{r.get('width')}×{r.get('height')}×{r.get('length')}" if r.get('width') else "-"
            lines.append(f"| {i} | {r['stem'][:40]} | {dim} | {r['bytes']//1024} KB | {', '.join(t for t in r['tags'][:4])} | {'✅' if r.get('paired_image') else ''} |")
        lines.append("")
    lines += ["## 标签分布（Top）",""] + [f"- {k}: {v}" for k,v in tag_counts.most_common(40)]
    open(os.path.join(args.out,"catalog.md"),"w",encoding="utf-8").write("\n".join(lines))

    try:
        from PIL import Image, ImageDraw
        picks = [r for r in rows if r.get("paired_image") and r["category"] in ("architecture","lobby","skyblock","bedwars","game","misc_build")]
        picks.sort(key=lambda r:-r["score"]); picks = picks[:40]
        cols, tw, th = 5, 240, 180
        sheet = Image.new("RGB",(cols*tw, ((len(picks)+cols-1)//cols)*th),(30,30,30))
        for i,r in enumerate(picks):
            try:
                im = Image.open(os.path.join(args.root,r["paired_image"])).convert("RGB")
                im.thumbnail((tw,th-20))
                x=(i%cols)*tw; y=(i//cols)*th
                sheet.paste(im,(x+(tw-im.width)//2,y))
                ImageDraw.Draw(sheet).text((x+4,y+th-16), f"{i+1}", fill=(255,255,255))
            except Exception: pass
        sheet.save(os.path.join(args.out,"contact-sheet.jpg"),quality=88)
    except Exception as e:
        print("contact sheet failed",e,file=sys.stderr)

    print("indexed",len(rows),"files ->",args.out)
    print("stats",json.dumps(stats,ensure_ascii=False)[:1000])

if __name__ == "__main__":
    main()
