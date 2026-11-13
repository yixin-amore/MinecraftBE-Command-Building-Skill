# 高斯滤波 / NX 地形平滑（样本拆解）

> 来源：用户提供的 5 条高斯滤波命令 + 地形组  
> [n叉随机地形生成](https://www.bilibili.com/video/BV18DoSY3Es8)  
> [[MC BE] 地形平滑 5cb 两种滤波](https://www.bilibili.com/video/BV1Gqgf6EEhV)

## 1. 它解决什么问题

NX 随机地形往往有：

- 单格尖刺
- 相邻高度跳变
- 边缘锯齿

高斯滤波 = **取邻域高度加权平均**，把尖刺压平，保留大形体。

## 2. 实体角色

| 名字/标签 | 作用 |
|---|---|
| `cow` | 地形中心/触发源 |
| `egg` / `snowball` / `fishing_hook` | 输入/投射物触发 |
| `t` | 2 个相背盔甲架，提供方向分叉 |
| `boat` | 一个向上、一个向下，提供垂直分叉 |
| `f` | 四个带标签的锚点实体（t/boat 组合） |
| `a` / `b` | 地形组的方向/高度参考 |
| `k` | 滤波采样点/标记 |
| `o` | 其它值噪声核的临时采样点 |

## 3. 命令 1：表面搜索 + 采样

```text
execute at @e[type=cow] positioned ~-0.5 -28.5 ~-0.5
  rotated as @e[name=t] positioned ^^^0.5
  rotated as @e[name=t] positioned ^^^1
  rotated as @e[name=t] positioned ^^^2
  rotated as @e[name=t] positioned ^^^4
  rotated as @e[name=t] positioned ^0.5^^
  rotated as @e[name=t] positioned ^1^^
  rotated as @e[name=t] positioned ^2^^
  rotated as @e[name=t] positioned ^4^^
  rotated as @e[type=boat] positioned ^^^16 align xz
  unless block ~~-16~ air if block ~~16~ air
  ... 8/4/2/1/0.5 ...
  positioned ~0.5~~0.5
  facing ~1000 -60 ~
  run summon armor_stand ~ -60~ ~~ k k
```

拆解：

1. **t 分支**：2 个相背装甲架 → 左右/前后方向分叉。
2. **boat 分支**：向上/向下 → 垂直方向分叉。
3. **二分表面搜索**：
   - 16 → 8 → 4 → 2 → 1 → 0.5
   - 每次 `unless block ~ ~-d~ air` / `if block ~ ~d~ air`
   - 找到“下面是实体、上面是空气”的表面
4. `align xz` 把采样点吸附到方块格。
5. `summon armor_stand ... k` 把结果落成 k。

> 本质是 **NX 方向树 + 二分高度搜索**，不是高斯公式本身。

## 4. 命令 2：邻域高斯加权

```text
execute at @e[type=cow]
  as @e[name=k,x=~-6,y=-64,z=~-6,dx=10,dy=1000,dz=10]
  at @s
  at @e[name=k,x=~-2,y=-64,z=~-2,dx=3,dy=1000,dz=3]
  positioned ...
  rotated ~180~
  ...
  tp @s ~~~
```

拆解：

1. 先在 **10×10** 范围选 k。
2. 再在 **3×3** 内选邻域 k。
3. 嵌套 `positioned/rotated/facing` 把邻域点做**加权/平均**。
4. `tp` 把中心 k 移到平滑后的高度。

样本的 3×3 邻域对应常见高斯核：

```text
1 2 1
2 4 2
1 2 1   / 16
```

或 5×5 近似：

```text
1  4  6  4 1
4 16 24 16 4
6 24 36 24 6
4 16 24 16 4
1  4  6  4 1  / 256
```

具体权重由命令里的偏移量/重复次数决定；样本没有显式乘权重，而是用**多次 positioned 采样**近似。

## 5. 命令 3-4：应用高度

```text
execute at @e[type=cow]
  at @e[name=k,x=~-6,y=-64,z=~-6,dx=10,dy=1000,dz=10]
  run fill ~ -60~ ~ 60~ air replace grass

execute at @e[type=cow]
  at @e[name=k,x=~-6,y=-64,z=~-6,dx=10,dy=1000,dz=10]
  run fill ~ -61~ ~ ~-0.1~ grass replace air
```

整理成正常坐标：

```mcfunction
fill ~ -60 ~ ~ 60 ~ air replace grass
fill ~ -61 ~ ~ ~-0.1 ~ grass replace air
```

作用：

- 先清掉旧的草
- 再在平滑后的高度铺草
- `replace air` 避免覆盖实体/其它方块

## 6. 命令 5：清理

```mcfunction
kill @e[tag=!f]
```

意图是保留 f 标签，杀其它临时实体。  
**不要直接照抄**：这会杀掉所有没有 f 标签的实体，包括玩家/宠物/展示实体。实际要写成：

```mcfunction
kill @e[tag=k]
kill @e[tag=o]
kill @e[tag=!f,tag=!k,tag=!o]
```

并限定 `type=armor_stand`/区域。

## 7. 地形组：把滤波结果铺成地形

```text
execute as @e[type=egg] at @p positioned ~ -50 ~
  rotated as @e[name=a] ... 0.5/1/2/4/8 ...
  facing entity @e[name=b] feet
  positioned ^ ^ ^-30 rotated ~180~
  positioned ^ ^ ^-30
  run setblock ~ ~ ~ grass keep
```

- `egg`/`snowball`/`fishing_hook`：输入/投射物。
- `a`：方向/分叉锚点。
- `b`：高度参考。
- 嵌套 `rotated as @e[name=a]` 是 NX 树，生成多点采样。
- `setblock ... keep` / `fill ... keep`：不覆盖已有方块。
- 粒子组用 `hasitem` 检测主手 egg/snowball，播放 `balloon_gas_particle`。

## 8. 系统化归类

| 层 | 作用 | 样本 |
|---|---|---|
| L0 触发 | cow/egg/snowball/fishing hook | 命令 1-5、地形组 |
| L1 NX 分叉 | t/boat/a/b 的方向树 | 命令 1、地形组 |
| L2 表面搜索 | 16→8→4→2→1→0.5 二分 | 命令 1 |
| L3 高斯邻域 | 3×3/5×5 采样加权 | 命令 2 |
| L4 应用 | fill grass/stone | 命令 3-4、地形组 |
| L5 清理 | kill 临时实体 | 命令 5 |

## 9. 风险

- `tag=!f` 清理过宽，可能杀玩家。
- `x=~-6`/`dx=10` 选择器在部分版本行为不同，先小范围测。
- 二分搜索依赖 `unless block`/`if block` 顺序；写错会得到空气/实体错位。
- 高斯权重是近似，不是严格数学卷积；地形会偏平滑。
- 大量 `egg/snowball/boat/armor_stand` 会超实体上限。
- `fill` 范围大，必须限高/限区。
- 需要 tickingarea/区块加载。

## 10. 一句话

> **高斯滤波 = NX 方向树采样 + 二分找表面 + 3×3/5×5 邻域加权 + 重新铺块。**  
> 样本的 5 条命令重点在“邻居采样和权重”，不是单个高度。
