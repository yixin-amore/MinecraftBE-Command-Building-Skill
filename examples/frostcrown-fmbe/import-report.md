# 导入报告 · 霜冠·维丝佩拉 v3（FMBE 移动版）

服务器：`28890143` · 2026-11-14 · 逐块导入（`tp → setblock → CommandBlockUpdate`）

## 1. 最终导入

| 项 | 结果 |
|---|---|
| 建筑 `frostcrown-arena.bdx` | 导入在 `500 0 500`，沿用 |
| 命令方块 | **446/446**（`init_a 62` + `init_b 53` + `main 107` + `pose_idle 112` + `pose_cast 112`） |
| StartPos | `506 42 506` |
| 触发 | `505 43 506` 与 `505 43 516` 两块红石；`init_b` 链尾自动拔掉 |
| 部件/载体 | `PARTS 14 / CORES 1 / UNIQUE 14` |

> 115 块单条 init 链在真机会吞掉中间几条 `tag` 命令；拆成 59/53 两条后复查 14/14/1。

## 2. 实测

```text
PARTS 14 / CORES 1 / UNIQUE 14
ST 1  HP 6000                  ← bot 放到 520 2 516，僵尸 AI 自己追
僵尸 AI 移动标记：AT_520_516
damage @e[tag=boss_core] 10 entity_attack
AFTER HP 5960  HIT 0           ← 真实命中扣 40；hit 在链尾清 0
```

关键结论：

- **僵尸自己追**：没有任何载体移动 `tp`；原版 AI 锁定玩家后走到 `AT_520_516`。
- **转身**：位置用 `^` + `facing feet`（僵尸/玩家同在地面，pitch=0），yaw 用 `facing eyes`；模型绕僵尸旋转。
- **真实命中仍成立**：载体戴 1 耐久头盔，碎后 `replaceitem ... keep` 补回，conditional 置 `hit=1` 才扣血。
- **一次命中只扣一次**：`hit` 读回 0。

## 3. 未验收

无头机器人不能看客户端 FMBE 模型。需要在客户端确认：

- 14 个部件是否拼成完整冰霜女王（位置/缩放/遮挡）；
- 移动时模型朝向（当前用 `~` 世界轴偏移，模型保持南向）；
- `idle` 与 `cast` 两套姿态；
- 二阶段冰晶/冰地板、三阶段暴雪、胜利/团灭演出。

## 4. 复现

```bash
python3 build_frostcrown_fmbe.py
python3 ../../scripts/chain_lint.py spec.json --format markdown --write lint.md
python3 readbdx.py frostcrown-commands.bdx
```

导入器属于本地工作区工具，未随本示例提交；示例提供 BDX + spec + 生成器，可按 `manual-build` 逐块 repair。
