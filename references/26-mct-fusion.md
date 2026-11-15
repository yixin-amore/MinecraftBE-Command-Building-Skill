# mct-fusion · 试运行说明

## 定位

**主体**：协作者 mct-skill 的「语言优先」路线。

```text
Python DSL（选择器/上下文/动作）
  -> spec.json
  -> cbc.py 链布局
  -> .mcworld / .mcstructure
```

**语料层**（这次新加，本地）：

- `references/20-corpus-patterns.md`：1,644 条语料的分类、高频命令、旧/新语法断层、检索路由
- `scripts/corpus_search.py`：按任务/类别检索同类实现
- `scripts/analyze_corpus.py`：从语料重新生成上述参考
- `references/21-fmbe-nxs.md`：FMBE 模型层 / NXS 缺口
- `references/23-nxs.md`：**NXS 递归坐标架**（binaryTree2D/3D 为样本）
- `references/24-fmbe-model-ir.md` + `scripts/fmbe_matrix.py`：FMBE 13 变量/4x4 矩阵/8 顶点/playanimation 导出
- `references/25-bdx-bridge.md` + `scripts/cbjson_to_bdx.py`：命令方块 cb.json → BDX 本地桥（local-only）
- `fmbe-reverse/`：APK 逆向的本地资料；已脱敏，不提交、不分发

**辅助**（我们保留/补充的部分）：

- `scripts/chelper_check.mjs`：可选的本地语法 oracle（外部读取）
- `auxiliary/fmbe-nxs.md`：FMBE 模型层 / NXS 适配缺口
- `auxiliary/bdk-import.md`：BDX / 服务器导入的边界
- 原 `mcbe-command-blocks` 的 FMBE、BDX、真机回读经验
- 语料：`../command-corpus/`（2,517 文件 / 1,710 文本 / 1,644 训练记录；本地，不提交）

## 目录

```text
SKILL.md                 mct 主文档（头部加了 fusion 说明）
scripts/                 mct 的 DSL / cbc / build / lint / verify
references/              mct 的 19 篇专题
refs/                    mct 的原文素材（本地试运行，不提交）
trial/                   demo spec / mcworld / mcstructure / 语法报告
auxiliary/               语法 oracle + 我们补的 FMBE/BDX 说明
```

## 版权与分发

- **不提交 GitHub**；本目录是本地试运行副本。
- mct-skill 也先作为本地参考；若要分发，需向协作者确认。
