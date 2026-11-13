# 命令数学：整数、坐标、几何与概率

> 基岩版命令没有浮点表达式、没有 `sin/cos`、没有运行时数组。  
> 数学必须落成**整数运算 + 查表 + 几何分解**。

## 1. 整数运算

`scoreboard players operation` 支持：

```text
=  +=  -=  *=  /=  %=
```

- 都是 **32 位整数**；乘法/累加会溢出。
- 除法是整数除法；除数为 0 时基岩版不改变目标值。
- 负数取模的符号跟被除数一致；环形数组要写 `((x % n) + n) % n` 的等价逻辑。
- 先乘后除会放大；百分比先 `*100` 再 `/max`，并钳制到 0..100。

**钳制模板**：

```mcfunction
execute if score fb_hp obj matches ..0 run scoreboard players set fb_hp obj 0
execute if score fb_hp obj matches 100.. run scoreboard players set fb_hp obj 100
```

**安全减法**：

```mcfunction
execute if score fb_cost obj <= fb_gold obj run scoreboard players operation fb_gold obj -= fb_cost obj
```

> 如果不确定 `<=` 在当前版本的选择器/execute 支持，改成 `unless score fb_gold obj < fb_cost obj`。

## 2. 定点数

没有浮点变量时，用放大整数：

```text
真实值 12.34 → 存 12340（×1000）
加法直接加；乘法后 /1000；比较用同一放大倍数
```

适合：百分比、距离平方、概率、曲线采样、伤害小数。

## 3. 坐标与向量

- 世界坐标 `x y z`；局部坐标 `^left ^up ^forward` 随执行者朝向。
- `positioned ^ ^ ^n` 沿视线前进；`rotated as ...` 改朝向；`anchored eyes` 改起点。
- 距离比较优先用**距离平方**避免开方：
  ```text
  dx*dx + dy*dy + dz*dz <= r*r
  ```
  命令侧没有直接向量运算；小范围可用 `r=` 选择器，精确判定用预计算表/分区。
- 朝向：`facing x y z` 或 `rotated as`；不要假设 `yaw` 的符号，先在游戏里测。

## 4. 几何

| 形状 | 参数化 | 命令侧 |
|---|---|---|
| 直线/射线 | `p = o + t·d` | 嵌套 `positioned ^^^t` |
| 圆 | `(r cosθ, r sinθ)` | 预计算偏移表/对称象限 |
| 椭圆 | `(a cosθ, b sinθ)` | 预计算表，x/y 分别缩放 |
| 球/半球 | 经纬采样 | 预计算层表，避免运行时三角 |
| 螺旋 | `θ` 递增 + 半径/高度 | 每 tick 推进角度表 |
| 抛物/曲线 | 采样点表 | 表驱动，不现场算浮点 |

**不要在命令里现场算 sin/cos**：命令没有可靠浮点数学；用外部脚本/表格生成离散偏移，再让 N 叉树遍历。

**对称技巧**：圆/椭圆只算第一象限，再镜像：

```text
(+x,+z) (+x,-z) (-x,+z) (-x,-z)
```

分支数从 4N 降到 N。

## 5. 概率与随机

- `scoreboard players random <target> <obj> <min> <max>` 产生闭区间整数。
- 概率用百分比整数：
  ```mcfunction
  scoreboard players random fb_roll obj 1 100
  execute if score fb_roll obj matches ..25 run ...
  ```
- 保底/伪随机：用计数器 + 取模，避免连续空窗。
- 随机表：`fb_loot` 权重表 + 前缀和 + 随机数落点。

## 6. 布尔与位集

- tag = 布尔；分数 = 多值状态。
- 位标志：`1,2,4,8,...`；置位 `+=`，检查 `matches` 范围不直观，优先用独立分数或 tag。
- 位集适合“已访问/已点亮/已收集”的 31 个以内集合；超过 31 个拆多个整数。

## 7. 数制与编码

- 十进制分数存 ID；需要打包时用 `id = type*1000 + index`。
- 字符串不能计算；名字只用于显示/选择器，不要当数据。
- 队列/数组索引用整数，不要用实体 UUID 当数组下标。

## 8. 常见错误

| 错误 | 后果 | 修复 |
|---|---|---|
| `hp / max * 100` | 先除后乘丢精度 | 先 `*100` 再 `/max` |
| 不钳制 | 负数/溢出 | 每步上下限 |
| 浮点写进分数 | 解析失败/截断 | 定点放大 |
| 现场算三角函数 | 没有函数/不稳定 | 预计算表 |
| `@e` 全图扫描算距离 | 卡顿 | 分区/`r=`/`tickingarea` |
| 用字符串当 ID | 不能运算 | 整数 ID + 名字表 |
