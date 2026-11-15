#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze the local command corpus and generate a corpus-informed reference."""
import json, os, re, collections
from pathlib import Path
def _corpus():
    env=os.environ.get('CMD_CORPUS')
    if env: return Path(env)
    for base in [Path.cwd(), *Path(__file__).resolve().parents]:
        p=base/'work'/'command-corpus'
        if p.is_dir(): return p
    return Path('work/command-corpus')
CORPUS=_corpus()
OUT=Path(__file__).resolve().parents[1]/'references'/'20-corpus-patterns.md'
rows=[]
for fn in ('train.jsonl','valid.jsonl','test.jsonl'):
 p=CORPUS/fn
 if p.exists():
  for line in p.open(encoding='utf-8'):
   try: rows.append(json.loads(line))
   except Exception: pass
cats=collections.Counter(r.get('category','other') for r in rows)
subs=collections.Counter((r.get('category'),r.get('subcategory')) for r in rows)
heads=collections.Counter(); bycat=collections.defaultdict(collections.Counter)
flags={
 'old_execute':re.compile(r'(^|\s)execute\s+@[aeprs]',re.I),
 'new_execute':re.compile(r'(^|\s)execute\s+(as|at|positioned|rotated|facing|if|unless|align)\b',re.I),
 'testfor':re.compile(r'(^|\s)testfor\b',re.I),
 'hasitem':re.compile(r'hasitem\s*=',re.I),
 'tagmark':re.compile(r'\btag\s*=',re.I),
 'replaceitem':re.compile(r'(^|\s)replaceitem\b',re.I),
 'titleraw':re.compile(r'(^|\s)(titleraw|tellraw)\b',re.I),
 'playanim':re.compile(r'(^|\s)playanimation\b',re.I),
 'particle':re.compile(r'(^|\s)particle\b',re.I),
 'scoreboard':re.compile(r'(^|\s)scoreboard\b',re.I),
 'summon':re.compile(r'(^|\s)summon\b',re.I),
 'structure':re.compile(r'(^|\s)structure\b',re.I),
 'fmbe':re.compile(r'\b(fmbe|smbe|mbe|playanimation|展示体)\b',re.I),
 'old_selector':re.compile(r'@[aeprs]\[[^\]]*\b(r|rm|dx|dy|dz|x|y|z)=',re.I),
}
flagc=collections.Counter(); examples=collections.defaultdict(list)
for r in rows:
 text=r.get('text','')
 for line in text.splitlines():
  t=line.strip()
  if not t or t.startswith('#') or t.startswith('//'): continue
  t=re.sub(r'^/+','',t).strip()
  m=re.match(r'([A-Za-z_]+)',t)
  if m:
   h=m.group(1).lower(); heads[h]+=1; bycat[r.get('category','other')][h]+=1
  for k,rx in flags.items():
   if rx.search(t): flagc[k]+=1
  if len(examples[r.get('category','other')])<3 and len(t)<=220 and re.match(r'^(execute|scoreboard|summon|effect|replaceitem|titleraw|tellraw|playsound|particle|structure|playanimation|fill|setblock|tp)\b',t):
   if t not in examples[r.get('category','other')]: examples[r.get('category','other')].append(t)
lines=[]
lines.append('# 20 · 语料蒸馏：这批资料里真正反复出现的模式\n')
lines.append('> 由 `scripts/analyze_corpus.py` 从本地语料自动生成；只统计模式，不复制整篇原文。\n')
lines.append('## 规模\n')
lines.append('| 类别 | 记录 |\n|---|---:|\n')
for c,n in cats.most_common(): lines.append(f'| `{c}` | {n} |\n')
lines.append('\n## 高频命令头\n')
lines.append('| 命令 | 次数 |\n|---|---:|\n')
for h,n in heads.most_common(20): lines.append(f'| `{h}` | {n} |\n')
lines.append('\n## 语料里的语法断层\n')
lines.append('这些资料横跨多个版本，**不能直接照抄**：\n')
labels={'old_execute':'旧 `execute @a ~ ~ ~` 语法','new_execute':'新 `execute as/at/... run` 语法','testfor':'`testfor`','hasitem':'`hasitem=` 选择器','tagmark':'`tag=` 选择器','replaceitem':'`replaceitem`','titleraw':'`titleraw/tellraw`','playanim':'`playanimation`','particle':'`particle`','scoreboard':'`scoreboard`','summon':'`summon`','structure':'`structure`','fmbe':'FMBE/展示体','old_selector':'旧半径/坐标选择器'}
for k,n in flagc.most_common():
 lines.append(f'- **{labels.get(k,k)}**：{n} 行；DSL 里必须显式建模，不直接拼字符串。\n')
lines.append('\n## 按任务的检索入口\n')
lines.append('| 任务 | 先检索 | 再用 |\n|---|---|---|\n')
lines.append('| 武器/拔刀剑/鱼竿枪 | `weapon` | `dsl.py` + `build_cbworld.py` + CHelper |\n')
lines.append('| 数据化/属性/T显 | `data` | `cbc.py` + score actions |\n')
lines.append('| 菜单/公告/进度条 | `ui` | `dsl` Context + `titleraw/tellraw` |\n')
lines.append('| 商店/开箱/经济 | `economy` | `inventory` / `scoreboard` / `structure` |\n')
lines.append('| 传送/圆规/二分 | `teleport` / `math` | `positioned/rotated/facing` |\n')
lines.append('| FMBE/展示体 | `fmbe` | `auxiliary/fmbe-nxs.md` + `build_fmbe.py` |\n')
lines.append('| 防护/管理 | `protection` | `scoreboard`/`tag` 审计 + 回读 |\n')
lines.append('\n## 各类代表命令片段\n')
for c in sorted(examples):
 lines.append(f'### `{c}`\n')
 for e in examples[c]: lines.append(f'- `{e[:220]}`\n')
lines.append('\n## 结论\n')
lines.append('- 这里不是“让模型背 1,600 篇”；是让 DSL 提供结构，语料提供**模式与命名**。\n')
lines.append('- 旧语法资料只能作为意图参考；生成前用 CHelper 复核，再进 `cbc.py`。\n')
lines.append('- FMBE/NXS 仍缺类型层：模型部件、绑定、动画、命中核心，见 `auxiliary/fmbe-nxs.md`。\n')
OUT.write_text(''.join(lines),encoding='utf-8')
print('wrote',OUT,'records',len(rows))
print('flags',flagc.most_common())
