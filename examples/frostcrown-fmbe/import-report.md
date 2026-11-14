# 导入报告 · 霜冠·维丝佩拉 v2（FMBE）

服务器：`28890143` · 2026-11-14 · 逐块导入（`tp → setblock → CommandBlockUpdate`）

## 1. 最终导入

| 项 | 结果 |
|---|---|
| 建筑 `frostcrown-arena.bdx` | 导入在 `500 0 500`，沿用 |
| 命令方块 | **436/436**（`init_a 63` + `init_b 53` + `main 96` + `pose_idle 112` + `pose_cast 112`） |
| StartPos | `506 42 506` |
| 触发 | `505 43 506` 与 `505 43 516` 两块红石；`init_b` 链尾自动拔掉 |
| 结果 | `PARTS 14 / CORES 2 / UNIQUE 14` |

> 为什么拆两条 init：v1 的 115 块单链在真机会吞掉中间几条 `tag` 命令，导致
> 14 只部件都在、但只有 9 个唯一 tag。拆成 63/53 两条后复查为 **14/14/2**。

## 2. 实测

```text
HP_OK
ST_IDLE
HEAD_OK
PARTS 14 / CORES 2 / UNIQUE 14
ST 1  HP 6000                  ← 机器人走进 515 2 515
damage @e[tag=boss_core_body] 10 entity_attack
AFTER HP 5960  HIT 0           ← 真实命中扣 40；hit 在链尾清 0
```

关键结论：

- **FMBE 14 部件全部注册**，2 个隐形核心就位。
- **真实命中成立**：头盔碎 → 下一 tick `replaceitem ... keep` 补回 → conditional 块置 `hit=1` → 扣 40。
- **一次命中只扣一次**：`hit` 读回 0。
- **复位/状态机**：`st=0`、`hp=6000`；进圈 `st=1`。

## 3. 未验收

无头机器人不能看客户端 FMBE 模型。需要在客户端确认：

- 14 个部件是否拼成完整冰霜女王（位置/缩放/遮挡）；
- `idle` 与 `cast` 两套姿态；
- 二阶段冰晶/冰地板、三阶段暴雪、胜利/团灭演出。

## 4. 复现

```bash
python3 build_frostcrown_fmbe.py
python3 ../../scripts/chain_lint.py spec.json --format markdown --write lint.md
python3 readbdx.py frostcrown-commands.bdx
```

导入器属于本地工作区工具，未随本示例提交；示例提供 BDX + spec + 生成器，可按 `manual-build` 逐块 repair。
