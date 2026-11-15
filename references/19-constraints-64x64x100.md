# 19 · 指令区 64×64×100 硬约束与大规模装箱（寒冰拔刀实战）

> **什么时候读我**：指令区方块数上万、要堆到 5 万块、或动画要 60~120 秒、或你遇到了
> 「常加载覆盖不全 / 部分特效不跑 / 上层粒子没动静」——先读这一篇，再动手。
> 配套脚本：`scripts/check_bounds.py`（导出前断言包围盒 + 打印常加载区命令）。

---

## 一、为什么要卡死 64×64×100

基岩版 `tickingarea`（常加载区）**必须是单个矩形**（或少数几个矩形）才稳。指令区靠常加载区
驱动——**区域外的链根本不 tick**。

实战踩过的坑：旧版寒冰拔刀 `B.W = 128`、单层展开、Z 深到 ~300，再加一个只盖 Y -4~4 的薄常加载区
→ 上层（y=18 那一层）的粒子链永远不跑，表现就是「常加载覆盖不全 / 部分特效不跑」。

**结论**：指令区底面压进 64×64，`tickingarea` 用一个矩形罩住整个盒子，是杜绝覆盖不全的唯一
可靠做法。任何「靠多块常加载拼」的方案都容易漏层，别碰。

---

## 二、三条硬规则

1. **X 宽 ≤ 64，Z 深 ≤ 64**：`B.W = 64`。底面 X[0..63]、Z[0..63]。
2. **Y 高 ≤ 100**：靠「分层堆叠」在 100 高度内塞下所有块。
3. **一个矩形常加载区全覆盖**：`tickingarea add <x1> <y1> <z1> <x2> <y2> <z2>` 取整个包围盒。

---

## 三、装箱：把上万块塞进 64×64×100

- **层高间隔压到最小**：`B.FLOOR_GAP = 5`（地板 3 厚 + 1 间隙 + 1 按钮位）。
  100 高度内可叠约 20 层 → 底面仍是 64×64 却能塞 ~5 万块（寒冰拔刀 120s 版实测 51,857 块）。
- **best-fit 装箱（别用 greedy-first-fit）**：每条链按「行数」（Z 向占多少行）分到
  「还能放下且最满」的那一层。
  - 每层 Z 行数上限 `cap`（如 62，留边）。
  - 顶层下标硬上限 `MAXLV`（如 19）→ 顶层层高 = `4 + FLOOR_GAP*MAXLV = 4 + 5*19 = 99 ≤ 100`。
  - 放不下且没有新层空间时，**强制塞进 MAXLV 层**（宁可单层更挤，也别溢出高度）。
  - greedy-first-fit 的毛病：先塞满低层再堆叠，容易把 Z 深顶到 108、Y 高顶到 109——双双越界。
- **`window_chains(..., win=N)` 调参**：时间窗口切链会把每条链拆成多个子链，每个子链有固定分离
  开销（rows + count + 4）。子链太多 → 分离开销累加 > 单层容量 → Z 溢出。把 `win` 翻倍
  （10→20）子链数减半、开销减半，18 层内就能装下 5 万块。

> 越界排查顺序：先看 Y 高（层数与 FLOOR_GAP）→ 再看 Z 深（cap 与 win 的分离开销）→ 最后看 X 宽。

---

## 四、计算常加载区（measure_ta）

初始化块一定是 level0 首链首格 `local(0, 4, 2)`。世界 y = local y - 64，相对偏移 == 局部偏移：

```python
xs = [x for (x, y, z) in blocks]
ys = [y for (x, y, z) in blocks]
zs = [z for (x, y, z) in blocks]
ox, oy, oz = 0, 4, 2
aX = min(min(xs) - ox, 0) - 2;  bX = max(max(xs) - ox, 0) + 2
aY = min(min(ys) - oy, 0) - 2;  bY = max(max(ys) - oy, 0) + 2
aZ = min(min(zs) - oz, 0) - 2;  bZ = max(max(zs) - oz, 0) + 2
tickingarea add ~%d ~%d ~%d ~%d ~%d ~%d yy % (aX, aY, aZ, bX, bY, bZ)
```

实测寒冰拔刀 120s 版：包围盒 **X64 / Y89 / Z62**，tickingarea `~-2 ~-5 ~-4 ~65 ~87 ~61 yy`，
✓ 全在 64×64×100 内。

---

## 五、长演出必须复位摄像机

`6.5` 只讲了 `fov_clear`，但 60~120 秒运镜（FMBE / camera）**结尾必须全套复位**，否则玩家视角
卡死：

```text
execute as @a[scores={yy_done=1}] run camerashake stop @s
execute as @a[scores={yy_done=1}] run camera @s clear
execute as @a[scores={yy_done=1}] run camera @s fov_clear 0 default
```

顺序无所谓，`stop` + `clear` + `fov_clear` 三个都给到就行。

---

## 六、粒子白名单：写错不报错、静默不出

`lint_commands.PARTICLES` 才是合法名。用了 `conduit_particle` / `snow_powder_particle` /
`white_smoke_particle` 之类**不在白名单的名字，lint 不报、游戏直接不出粒子**。冰风格合法替代：
霜雾 → `basic_smoke_particle`、雪沫 → `snowballpoof`、青微光 → `basic_bubble_particle`、
雪花 → `snowflake`、末地烛柱 → `endrod`、灵魂火 → `soul_particle` + `basic_flame_particle`。
**交付前必跑 `lint_commands.py`**（见 `08-particles.md` 全名单）。

---

## 七、验收流水线（缺一不可）

```bash
python build_x.py --dump-spec out/spec.json            # 出 spec（顺带 measure_ta）
python build_x.py --spec out/spec.json --template T.mcworld --out out/_b.mcworld
python verify_mcworld.py out/_b.mcworld                # 回读：块数/链尾/CRC
python lint_commands.py out/spec.json                  # 粒子+音效+JSON 白名单
python dump_cbworld.py out/_b.mcworld --json out/cb.json
python check_chain_break.py out/cb.json --expect 999 --func 999   # 先看真实链数
# 用真实链数重跑：--expect <gated 数> --func <面板 setblock 数 或 0>
python check_bounds.py out/_b.mcworld                  # 断言 ≤64×64×100 + 打印 tickingarea
python mcworld_to_structure.py --input out/_b.mcworld --out 指令区.mcstructure
```

> `check_chain_break` 的 `--expect` / `--func` 是**设计相关数**，先跑一次拿真实值再核对，别拍脑袋填。
> 寒冰拔刀 120s 版：131 可断 / 6 常驻 / 4 面板，`--expect 131 --func 0` 通过。
> `check_bounds.py` 不支持 spec / mcstructure，只吃已构建的 `.mcworld`（它直接读存档方块算盒子）。
