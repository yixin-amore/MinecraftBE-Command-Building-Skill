#!/usr/bin/env python3
"""Query a Sunrain-style index.jsonl by category/tag/size."""
import argparse, json, os, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("index")
    ap.add_argument("--category")
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--ext", action="append", default=[])
    ap.add_argument("--min-width", type=int)
    ap.add_argument("--min-height", type=int)
    ap.add_argument("--min-volume", type=int)
    ap.add_argument("--paired", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    a=ap.parse_args()
    rows=[]
    for line in open(a.index,encoding="utf-8"):
        r=json.loads(line)
        if a.category and r.get("category")!=a.category: continue
        if a.ext and r.get("ext") not in a.ext: continue
        if a.paired and not r.get("paired_image"): continue
        if a.min_width and (r.get("width") or 0)<a.min_width: continue
        if a.min_height and (r.get("height") or 0)<a.min_height: continue
        if a.min_volume and (r.get("width",0)*r.get("height",0)*r.get("length",0))<a.min_volume: continue
        if any(t not in r.get("tags",[]) for t in a.tag): continue
        rows.append(r)
    rows.sort(key=lambda r:(-r.get("score",0), r.get("path","")))
    rows=rows[:a.limit]
    if a.json:
        print(json.dumps(rows,ensure_ascii=False,indent=2)); return
    for r in rows:
        dim=f"{r.get('width')}x{r.get('height')}x{r.get('length')}" if r.get('width') else "-"
        print(f"{r.get('score',0):5.1f} {r.get('category',''):12} {dim:14} {r.get('bytes',0)//1024:6}KB {r['path']}")
        if r.get("paired_image"): print(f"      image: {r['paired_image']}")
        if r.get("tags"): print(f"      tags: {', '.join(r['tags'][:10])}")

if __name__=="__main__": main()
