# 维护这份 skill 的操作手册

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> 主文件末尾的 **Z.5 是八条规矩**，本文件是**具体怎么执行**（脚本、流程、验证）。
> 主文件的结论永远优先；这里的操作细节可以随工具变化。

> **什么时候读我**：要往 skill 里加内容、改结构、合并别的会话的成果、
> 或者发现文档自相矛盾时。

---

## 一、先判断：这条经验该进哪

```
新经验
 ├─ 是「以后该怎么做」的决策？        → SKILL.md（基线 / 硬规则 / 对应章节）
 ├─ 是用户明确提过的要求？            → SKILL.md 的 Z.1 台账（U 编号）
 ├─ 是踩过的坑（症状 → 根因 → 解法）？ → 易错点表（A~G）+ references/12-ledger
 ├─ 是一张全表 / 原文 / 代码清单？     → references/ 对应文件
 ├─ 能写成一条检查规则的？            → scripts/lint_commands.py（最优先）
 └─ 是外部来源（别人做的）？          → 单独成文，文件头标「未实测 + 出处 + 版本依赖」
```

**判据**：主文件是「每次开工都要看的」，references 是「用到才查的」。
拿不准就问自己——**下次开工时，不看这条会不会做错？** 会 → 主文件。

---

## 二、四个编号体系（别混）

| 体系 | 范围 | 含义 | 加新条目时 |
|---|---|---|---|
| **基线** | 1 ~ 34 | 唯一正确做法，冲突时以它为准 | 追加到末尾，编号连续 |
| **U** | 1 ~ 70 | 用户明确提过的要求 | 追加到 Z.1 末尾 |
| **A ~ G** | A1~41 / B1~8 / C1~9 / D1~5 / E1~11 / F1~4 / G1~16 | 易错点，按工序分组 | 找到对应字母组，接在组内末尾 |
| **章号** | 0 ~ 102 + 一~十一 | 内容定位，**永不重排** | 新内容优先挂已有章，实在没有才加新章 |

**易错点分组**：A 断链/命令方块 · B 存档格式 · C 计分板 · D UI · E 音效粒子 · F 报错开关 · G 展示体演出。

**章号不重排的理由**：正文里到处是「见第 55 章」，重排一次全断。

---

## 三、改之前必做的三件事

### 1. 搜一遍，别重复加

```bash
# 在 skill 目录下
grep -rn "关键词" SKILL.md references/ | head
```

### 2. 看基线，确认没被推翻

新做法如果和基线某条冲突，**要么改基线，要么别加**。两条并存就是灾难。

### 3. 看 12-ledger，确认不是老坑重提

`references/12-ledger.md` 是按时间序的踩坑记录，同一个坑可能已经踩过两次。

---

## 四、编辑：只用文本锚点，**禁用行号区间**

**事故**：一次 `idx[0]`~`idx[-1]` 的区间替换，因为 `| 34 |` 在另一张表里也出现，
一次删掉 1176 行（110KB → 32KB）。

```python
# ✅ 正确：唯一文本锚点
anchor = "| 24 | **两层布局**：方块按子区块分组写、走查索引带 `y`"
i = s.index(anchor)
s = s[:i] + new_rows + s[i:]

# ❌ 错误：模糊区间
idx = [i for i, l in enumerate(lines) if re.match(r"\| (25|26|...) \|", l)]
lines[idx[0]:idx[-1]+1] = new      # idx[-1] 可能匹配到别的表！

# ⚠️ 非要用区间，必须先断言连续
nums = [int(re.match(r"\| (\d+) \|", lines[i]).group(1)) for i in range(a, b+1)]
assert nums == list(range(25, 35)), nums
```

---

## 五、改完必做的三项验证

```bash
# 1. 行数 / 字节变化是否符合预期
wc -l SKILL.md && wc -c SKILL.md

# 2. 编号连续 + 结构完整（可直接跑）
python - <<'PY'
import io, re
s = io.open("SKILL.md", encoding="utf-8").read(); lines = s.split("\n")
i = next(i for i, l in enumerate(lines) if l.startswith("| # | 结论"))
bn = []
for l in lines[i+2:]:
    m = re.match(r"\| (\d+) \|", l)
    if not m: break
    bn.append(int(m.group(1)))
print("基线 %d 条 连续=%s" % (len(bn), bn == list(range(1, len(bn)+1))))
for p in "ABCDEFGU":
    n = sorted({int(m.group(1)) for l in lines for m in [re.match(r"\| %s(\d+) " % p, l)] if m})
    if n: print("%s 1~%d 缺 %s" % (p, max(n), [x for x in range(1, max(n)+1) if x not in n]))
print("行数 %d / 字节 %d" % (len(lines), len(s.encode())))
PY

# 3. 项目级 / 用户级一致
md5sum SKILL.md "C:/Users/Administrator/.workbuddy-ai/skills/mct/SKILL.md"
```

**行数变化超过预期就停手**，先查是不是误删。

---

## 六、多会话冲突（真实发生过两次）

同一个 skill 会被多个会话同时改。症状是 md5 不一致、内容莫名消失。

### 处理流程

```bash
# 1. 先比，别急着覆盖
diff <(grep "^#" 项目级/文件) <(grep "^#" 用户级/文件)

# 2. 取更全的那份作基底（通常行数多的）

# 3. 把另一份独有的内容「追加」，不要整文件覆盖
#    典型：A 版有 14 节，B 版有 12 节 + 你加的 1 节
#    → 以 A 为基底，把 B 独有的那 1 节追加进去

# 4. 双向同步，再比一次
```

**教训**：不要假设「用户级就是最新的」。两个会话都在写时，
用户级可能是 A 的旧版、项目级是 B 的新版，或者反过来。

### 判断谁更新

```bash
ls -la 项目级/SKILL.md 用户级/SKILL.md     # 看修改时间
grep -c "^## " 项目级/SKILL.md 用户级/SKILL.md   # 看章节数
```

时间新 + 章节多 = 大概率更全。但**必须看内容差异**，不能只看时间。

---

## 七、从 jsonl 转录恢复内容

会话被中断、内容被覆盖时，从转录里挖。

**路径**：`C:\Users\Administrator\.workbuddy-ai\projects\<项目目录>\<session>.jsonl`

**结构**：

| `type` | 里面有什么 |
|---|---|
| `message` | `role` + `content[]`，元素 `{type:"input_text"/"output_text", text}` |
| `function_call` | `name` + `arguments`（`file_path` / `content` / `old_string` / `new_string` / `command`） |
| `function_call_result` | 工具输出 |
| `reasoning` | 思考过程（有时含完整方案） |

**常用挖掘脚本**：

```python
import json, io, re

p = r"C:\Users\Administrator\.workbuddy-ai\projects\<项目>\<session>.jsonl"

# ① 提取用户提问
with io.open(p, encoding="utf-8") as fh:
    for line in fh:
        o = json.loads(line)
        if o.get("type") != "message" or o.get("role") != "user": continue
        c = o.get("content")
        txt = "".join(x.get("text","") for x in c if isinstance(x, dict)) if isinstance(c, list) else (c or "")
        m = re.search(r"<user_query>(.*?)</user_query>", txt, re.S)
        if m: print(m.group(1).strip()[:100])

# ② 提取某段内容的完整写入（Write 工具）
with io.open(p, encoding="utf-8") as fh:
    for line in fh:
        o = json.loads(line)
        if o.get("type") != "function_call": continue
        a = o.get("arguments") or {}
        if isinstance(a, str):
            try: a = json.loads(a)
            except: continue
        if "content" in a and "关键词" in str(a["content"]):
            io.open("recovered.md", "w", encoding="utf-8").write(a["content"])
            break

# ③ 从 Bash 脚本里的 '''...''' 提取
cmd = a.get("command", "")
m = re.search(r"'''(.+?)'''", cmd, re.S)
if m: io.open("recovered2.md", "w", encoding="utf-8").write(m.group(1))
```

**注意**：脚本里的换行是字面 `\n`（两个字符），提取后要 `.replace("\\n", "\n")`。

---

## 八、拆分 / 重构时的守恒校验

把大文件拆成多个时，**必须验证标题数守恒**：

```python
old_h = {l for l in io.open("SKILL.md.bak", encoding="utf-8").read().split("\n") if l.startswith("## ")}
now_h = {l for l in io.open("SKILL.md", encoding="utf-8").read().split("\n") if l.startswith("## ")}
for f in glob.glob("references/*.md"):
    now_h |= {l for l in io.open(f, encoding="utf-8").read().split("\n") if l.startswith("## ")}

missing = old_h - now_h
print("丢失:", len(missing))
for m in missing: print("  ✗", m)
```

**教训**：上次拆分时漏了 4 章（59/60/64/65），因为没做守恒校验，
靠"关键标记抽查"才发现。**守恒校验是唯一可靠的**。

---

## 九、同步与备份

```bash
P="项目级/skills/mct"; U="C:/Users/Administrator/.workbuddy-ai/skills/mct"

# 同步（先确认方向！）
cp "$P/SKILL.md" "$U/SKILL.md"
cp "$P/references/"*.md "$U/references/"
cp "$P/scripts/"*.py "$U/scripts/"

# 逐个核对
for f in SKILL.md $(cd "$P/references" && ls *.md); do
  a=$(md5sum "$P/$f" | cut -d' ' -f1); b=$(md5sum "$U/$f" | cut -d' ' -f1)
  [ "$a" = "$b" ] || echo "DIFF $f"
done
```

**改大结构之前**先备份：

```bash
cp SKILL.md "$TEMP/SKILL-$(date +%m%d-%H%M).md"
```

（用 `$TEMP` 而不是 `/tmp`：Windows 下 Git Bash 的 `/tmp` 和 Python 的 `/tmp` 不是同一个地方。）

---

## 十、文档自相矛盾的排查

比"缺内容"更害人的是"文档自己打架"。定期查：

```bash
# ① 已废弃术语是否还在
for k in tg_hit tg_spread 副手望远镜 "W=128" "射程上限 1000"; do
  printf "%-16s %s\n" "$k" "$(grep -c "$k" SKILL.md)"
done

# ② 同一概念在「基线 / 验收表 / 示例代码 / 台账」四处是否一致
#    典型：验收表还要求虚拟血量，但基线已经改成原版 damage

# ③ 重复标题（章节编号撞车）
grep '^### ' SKILL.md | sort | uniq -d

# ④ 超长表格行（可能粘连）
python -c "
import io
for i, l in enumerate(io.open('SKILL.md', encoding='utf-8').read().split('\n'), 1):
    if l.startswith('|') and len(l) > 420: print(i, len(l), l[:60])
"
```

**编号撞车的教训**：新章节先确认编号空间——第一部分用中文（一~十一），
第二~十一部分用数字（0~102），Z 用 Z.x。

---

## 十一、每次维护的收尾清单

- [ ] 新内容归位（主文件 / references / lint）
- [ ] 编号连续（基线 / U / A~G）
- [ ] 交叉引用没断（「见第 N 章」指向的文件存在）
- [ ] 行数变化符合预期
- [ ] 项目级 / 用户级 md5 一致
- [ ] 工作区记忆（`.workbuddy-ai/memory/`）追加一条
- [ ] 如果改了结构，`references/` 索引表同步
