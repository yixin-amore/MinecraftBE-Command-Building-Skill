# 拉伸：两点 → 旋转 + 长度（SMBE / 线性代数）

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**；跨文件的章号去主文件的「章号 → 文件 对照表」查。

> ⚠️ **交付边界先说清**：这套「真拉伸」需要**资源包里的自定义动画**，
> 不是纯 `.mcstructure` 能交付的。要纯结构文件，只能用 `14-fmbe.md` 的
> 轴对齐缩放（`v.scale` / `v.xzscale` / `v.yscale`）——**拉不了任意方向**。
> 本文件的价值在**数学部分**和**三个坑**，那两条对纯命令方块同样适用。

> **什么时候读我**：要做「两点之间连一根会动的杆 / 激光 / 锁链 / 触手」；
> 或者要在 Molang 里算「朝向某个点的旋转角」。

---

## 一、一句话原理

**拉伸 = 沿骨骼自身轴的 `scale` + 对准方向的 `rotation`**，两个都由线性代数算出来，
不需要手调关键帧。

```
d = B - A          目标向量
L = |d|            长度

yaw   = atan2(-dx, dz)      ← 必须 atan2，用 atan 会丢象限
pitch = -asin(dy / L)       ← 必须 clamp 到 [-1, 1]，否则 NaN
rotation = [pitch, yaw, 0]
scale    = [1, 1, L]
```

**前提**：几何体做成「pivot 在原点、沿 **+Z** 长 16px（= 1 格）」。
这样 `scale.z = L` 就正好是 L 格，不用再乘系数。

**Molang 写法**：

```text
v.dx = q.property('sbe:tx') - q.position(0);
v.dy = q.property('sbe:ty') - q.position(1);
v.dz = q.property('sbe:tz') - q.position(2);
v.L  = math.sqrt(v.dx*v.dx + v.dy*v.dy + v.dz*v.dz);
v.yaw   = math.atan2(-v.dx, v.dz) * 57.29578;      // 弧度 → 度
v.pitch = -math.asin(math.clamp(v.dy / v.L, -1, 1)) * 57.29578;
```

> `math.clamp` 不能省：`dy/L` 在浮点误差下可能到 1.0000001，`asin` 直接返回 NaN，
> 整根杆消失。

---

## 二、三个查证出来的关键点（老教程常写错）

### 1. 骨骼 rotation 与实体 pitch/yaw **同号**，没有负号

原版 `humanoid.look_at_target` 里直接写：

```json
"rotation": ["q.target_x_rotation", "q.target_y_rotation", 0]
```

没有任何取负。之前流传的「要取负」不成立 —— 取负会让杆反向。

### 2. 世界空间瞄准要 `"relative_to": {"rotation": "entity"}`

```json
"rotation": {
  "relative_to": { "rotation": "entity" },
  "expression": "[v.pitch, v.yaw, 0]"
}
```

**不写这个**，根骨骼会跟着实体 yaw 转（属性向量是局部空间的），
结果就是「杆永远朝实体正面」，怎么调数都不对。

### 3. `client_sync: true` 漏了**不报错**，只给一根隐形杆

```json
"bones": [{ "name": "beam", "parent": "root", "pivot": [0,0,0],
            "client_sync": true, "scale": [1, 1, "v.L"] }]
```

漏了之后 `scale` 恒为 `0.001`，模型长度永远是 0.001 格 —— **看不见，但不报错**。
这是这套技术最容易卡住的地方，排查时第一个查它。

---

## 三、和 FMBE 的关系（别混用）

| | FMBE（`14-fmbe.md`） | SMBE（本文件） |
|---|---|---|
| 载体 | 原版狐狸 + **原版动画** | 自定义实体 + **自定义动画** |
| 缩放 | `v.scale` / `v.xzscale` / `v.yscale`（**轴对齐**） | 沿骨骼 +Z 的 `scale.z = L`（**任意方向**） |
| 需要资源包 | ❌ 纯指令 | ✅ 必须有 |
| 能做什么 | 悬浮方块、展示柜、方块阵列 | 激光、锁链、触手、连线、鞭子 |
| 交付形态 | `.mcstructure` | `.mcaddon` + `.mcstructure` |

**结论**：
- 纯结构文件交付 → 只能 FMBE
- 要「两点连线 / 任意方向拉伸」→ 必须上资源包，走 SMBE

**顺带纠正一个说法**：原版 `animation.fox.pounce` 里只有一句
`q.vertical_speed * -7.0` 的固定俯仰，**根本没有真拉伸**（scale 只出现在幼体缩放里）。
所以「比狐狸更强」这个说法是准确的 —— 狐狸只是俯仰，不是拉伸。

---

## 四、mcstructure 部分的两个硬坑

这两个坑与拉伸无关，但那个会话是同时踩到的，值得记：

### 1. 命令方块执行原点的 0.5 格歧义

不同版本里，命令方块的执行原点可能是**方块中心**也可能是**方块角**。
直接写 `~0.5 ~ ~0.5` 会整体偏半格。

**解法**：先 `align xyz` 压回整数格，再 `+0.5`：

```mcfunction
execute align xyz positioned ~0.5 ~ ~0.5 run summon sbe:beam
```

两种约定都落到同一格中心 —— 这是「贴到任意位置都能对齐」的前提。

### 2. 方块实体 NBT 类型不能一律写 INT

| 字段 | 类型 |
|---|---|
| `conditional_bit` | **BYTE** |
| `button_pressed_bit` | **BYTE** |
| `facing_direction` | **INT** |
| `auto` | BYTE |

**写错不报错**，只会让按钮按下去没反应，或者链直接断掉 —— 和 A39（子区块写错）
一样属于「结构能加载，但行为不对」的那类。

---

## 五、烘焙 vs 实时（两套路径怎么选）

| | 实时（`scripts.animate`） | 烘焙（`playanimation`） |
|---|---|---|
| 怎么算 | Molang 每帧算 | 预先算好写进动画 JSON |
| 改目标点 | 立刻变 | 要重新烘焙 |
| 能否加缓动 | 不能 | 能 |
| 可靠性 | 依赖引擎对 `q.property` 的支持 | **纯静态数值，100% 可复现** |

**建议**：先用烘焙路径验证几何（数是对的、朝向是对的），
再切实时路径调手感。两套用布尔属性互斥，别同时开。

**离线烘焙工具**（那个会话写的，思路可复用）：

```python
# 两点 → 动画 JSON
d = (bx-ax, by-ay, bz-az)
L = math.sqrt(sum(v*v for v in d))
yaw   = math.degrees(math.atan2(-d[0], d[2]))
pitch = math.degrees(-math.asin(max(-1, min(1, d[1]/L))))
anim = {"rotation": [pitch, yaw, 0], "scale": [1, 1, L]}
```

---

## 六、验算方法（出问题先查这里）

| 现象 | 查什么 |
|---|---|
| 杆看不见 | `client_sync: true` 有没有写（坑 3） |
| 杆长度恒为 0.001 | 同上 |
| 杆朝反方向 | `atan2` 的符号（`-dx` 还是 `dx`） |
| 杆跟着实体转 | `relative_to` 有没有写（坑 2） |
| 杆角度差 90° 或 180° | 骨骼主轴是不是 `+Z`（不是 `+Y`） |
| 杆消失 / NaN | `asin` 的参数有没有 clamp |
| 整体偏半格 | 有没有 `execute align xyz` |

**标定台**：那个会话做了个 `13×3×13` 的结构 —— 骨骼起点在金块上，
6 格终点在另一个金块上方。按按钮召唤一根朝南的杆，**杆尖应该正好悬在
最后一格金块中心上方**。偏了按上表查。
