# 箱子 / 告示牌 / 物品 NBT（98~101 章）

> 把说明做进世界的完整写法、`givenbt` 物品结构、伪无鱼竿枪逐行拆解、换弹双变量模型、组队十进制键盘。
**什么时候读**：要放箱子/告示牌、写 Lore、做复杂物品、实现换弹或组队。

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

---

## 98. 箱子 / 告示牌 / 物品 NBT：把说明做进世界 ★

> 交付物里最容易被忽略的一件事：**玩家拿到手不知道怎么用。**
> 用聊天栏 tellraw 说一遍没用（会被刷掉），写在文档里更没用（没人看）。
> 正确做法是**把说明做成世界里的实物**：一个箱子（装带 Lore 的成品物品）+ 几块告示牌。

### 98.1 先澄清：`/givenbt` 不是原版指令

网上流传的写法长这样：

```
/givenbt @s leather_chestplate 1 0 "{display:{Name:'§r§n⫸§f暴怒',Lore:['...']},Unbreakable:1b}"
```

**`givenbt` 是插件 / 服务端 / 整合包提供的指令，不是原版基岩版指令。**
原版的 `give` **不接受 NBT**：

```
give @s leather_chestplate 1 0          ← 只能给物品 ID + 数量 + data
give @s leather_chestplate 1 0 {...}    ← ❌ 直接 Syntax error
```

所以带名字、带 Lore、带 `Unbreakable` 的物品，**指令发不出来**。三条路可选：

| 路线 | 能不能带 NBT | 依赖 | 适用 |
|---|---|---|---|
| `/givenbt`（插件） | ✅ | 服务器装了插件 | 只在自己服务器玩，换服就废 |
| 行为包 + `/give` 自定义物品 | ✅ | 要行为包，网易服导入麻烦 | 国际服 / 允许加包的服 |
| **容器方块实体**（本章） | ✅ | **零依赖** | **本项目默认** |

**为什么容器路线最稳**：物品的 NBT 是写在**箱子方块实体**里的，
随 `.mcstructure` 一起粘出去。玩家开箱、拿走、放进背包，NBT 全程不掉。
不需要插件、不需要行为包、不挑服务器。

### 98.2 一行代码做一件注释物品

`build_cbworld.py` 提供 `item_nbt()`：

```python
import build_cbworld as B

B.item_nbt(
    "leather_chestplate",              # 物品 ID（带不带 minecraft: 都行）
    count=1,
    damage=0,                          # 就是 data 值
    display_name="§r§n⫸§f暴怒",       # 显示名（可带 § 码）
    lore=[                             # 描述，一行一条
        "§r§7-§4∅ §l§7| §r§1 ∅ 级 §l§7| §r§g饰品：胸部",
        "§r§7——————————————————",
        "§r§7-当周围10格有敌人时伤害变为1.15倍",
        "§o§8............他又能做什么呢？",
    ],
    unbreakable=True,                  # 不可破坏
    extra={"暴怒": 1},                 # 追加自定义键（可选）
    slot=4,                            # 放进箱子第几格（可选）
)
```

生成的 NBT（这就是 `givenbt` 那段字符串的真实结构）：

```
{
  Name: "minecraft:leather_chestplate",   ← TAG_String
  Count: 1b,                              ← TAG_Byte（不是 Int）
  Damage: 0s,                             ← TAG_Short（不是 Int）
  WasPickedUp: 0b,
  Slot: 4b,
  tag: {
    display: { Name: "§r§n⫸§f暴怒", Lore: ["...", "..."] },
    Unbreakable: 1b
  }
}
```

❗ **`Count` 必须是 Byte、`Damage` 必须是 Short。** 写成 Int 游戏能读，但
某些版本会把整件物品判为无效直接删掉。

❗ **`display` / `Unbreakable` 在 `tag` 里面**，不是和 `Name` 平级。
写成平级 = 不显示名字、不生效。

### 98.2b 直接把 `givenbt` 那段字符串搬进来（`item_from_snbt`）


98.2 是"用 Python 参数拼"，但网上抄来的原文都是**一长串 SNBT**：

```
/givenbt @s leather_chestplate 1 0 "{top_layer_1:'feather',display:{Name:'§r§n⫸§f暴怒',Lore:['§r§7-§4∅ §l§7| §r§1 ∅ 级 §l§7| §r§g饰品：胸部','§r§7——————————————————','§r§7-当周围10格有敌人时伤害变为1.15倍，当周围10格无敌人时伤害变为0.75倍','§r§7——————————————————','§o§8............他又能做什么呢？']},Unbreakable:1b}"
```

**不用手动翻译**，`parse_snbt()` 直接吃这段字符串：

```python
import build_cbworld as B

item = B.item_from_snbt(
    "leather_chestplate",                      # 物品 ID
    "{top_layer_1:'feather',display:{Name:'§r§n⫸§f暴怒',Lore:[...]},Unbreakable:1b}",
    count=1, damage=0, slot=0,                 # slot = 箱子第几格
)
```

三个新函数：

| 函数 | 作用 |
|---|---|
| `parse_snbt(text)` | SNBT → `(tag, value)` 类型树（可直接喂 `nbt_compound`） |
| `snbt_to_tag(text)` | SNBT → 可直接当 `tag:` 用的复合字典 |
| `item_from_snbt(id, snbt, count, damage, slot)` | SNBT → 一件完整的容器物品 |

命令行也能直接看类型树（排查"类型对不对"最快）：

```bash
python scripts/build_cbworld.py --snbt "{display:{Name:'§b测试'},Unbreakable:1b}"
```

```
{
  display: {
    Name:       "§b测试"
  }
  Unbreakable:     byte(1)
}
```

#### SNBT 后缀 → NBT 类型（唯一要记的一张表）

| SNBT 写法 | NBT 类型 | 什么时候必须这么写 |
|---|---|---|
| `1b` / `true` | Byte | `Unbreakable`、`Count`、`Slot`、所有 `*_bit` |
| `1s` | Short | `Damage` |
| `1`（无后缀） | Int | 颜色值、坐标、`CustomModelData` 类 |
| `1L` | Long | 时间戳、种子 |
| `1.0f` | Float | 音调、缩放 |
| `1.0d` / `1.0` | Double | 位移、朝向 |
| `'文本'` / `"文本"` | String | `Name`、`Lore` 每一行、`top_layer_1` |
| `[...]` | List | `Lore`（元素类型由第一项决定，混类型直接报错） |
| `[B;1,2]` / `[I;1,2]` | Byte/Int 数组 | 地图颜色、大位图 |
| `{...}` | Compound | `display`、`tag`、`Trim` |

❗ **列表里不能混类型。** `['文本', 1b]` 会直接 `SnbtError`——NBT 列表是同构的。

#### 实测：上面那件暴怒饰品，全链路通过

```
解析 → 容器物品 → .mcworld → .mcstructure → check_props 回读
```

`check_props.py` 输出（`.mcworld` 与 `.mcstructure` 各跑一遍，结果一致）：

```
· Chest @ (0,-60,0)  方块=chest
  自定义名: §e暴怒饰品 · 说明箱
  物品 3 件
     1. leather_chestplate           ×1  data=0  slot=0   不可破坏=1
        名: §r§n⫸§f暴怒
        述: §r§7-§4∅ §l§7| §r§1 ∅ 级 §l§7| §r§g饰品：胸部
        述: §r§7——————————————————
        述: §r§7-当周围10格有敌人时伤害变为1.15倍，当周围10格无敌人时伤害变为0.75倍
        述: §r§7——————————————————
        述: §o§8............他又能做什么呢？
        其他 NBT: top_layer_1='feather'
结论：✓ 说明区正常
```

> `其他 NBT:` 这行是 2026-11 新加的：除 `display` / `Unbreakable` 之外的
> `tag` 键全部打印出来，否则**纹饰、自定义键这类"看不见的 NBT"根本没被验证过**。

**这条路能带的东西**：显示名、多行 Lore、`Unbreakable`、纹饰（`top_layer_1`）、
附魔、`CustomModelData`、任意自定义键——**只要它是物品 NBT，就跟着结构文件走**。
带不了的只有"行为"：Lore 上写的"伤害变 1.15 倍"是给人看的，
真逻辑还得靠计分板 + 命令方块（第 21 / 44 章）。

### 98.3 箱子：容器方块实体

```python
items = [B.item_nbt("paper", display_name="§b操作卡", lore=[...], slot=0)]
B.container_entity(x, y, z, items, custom_name="潮汐 · 说明箱")
```

完整结构：

```
{
  id: "Chest",              ← 固定大写 C，不是 minecraft:chest
  x: 0, y: -60, z: 0,       ← **世界坐标**，不是区块内坐标
  Findable: 0b,
  CustomName: "潮汐 · 说明箱",
  Items: [ {Name, Count, Damage, WasPickedUp, Slot, tag}, ... ]
}
```

❗ **`id` 是 `"Chest"`**（实体名），方块 ID 才是 `minecraft:chest`。写错 = 箱子是空的。

❗ **坐标是世界坐标。** 和命令方块实体一个规矩（第 4 章）。

❗ **`Slot` 建议写。** 不写就按数组顺序填格子，写在哪个格子不由你控制；
写了 `Slot: 0..26` 才能精确布局。

### 98.4 告示牌：FrontText / BackText

```python
B.sign_entity(x, y, z, front=["§8«§b潮汐§8»", "§f鱼竿枪 §7v2", "§8—————", "§7副手壳切枪"])
```

```
{
  id: "Sign",
  x, y, z,                  ← 世界坐标
  FrontText: {
    Text: "第1行\n第2行\n第3行\n第4行",   ← **用 \n 分行，不是数组**
    PersistFormatting: 1b,
    SignTextColor: -16777216,               ← 文字颜色（int，ARGB）
    HideGlowOutline: 0b,
    IgnoreLegacy: 0b
  },
  BackText: { ... },
  IsWaxed: 0b
}
```

**四条硬限制：**

1. **每面最多 4 行**，超出的行会被丢掉（代码里已经 `[:4]` 截断）
2. **一行大约 15 个全角字符**，超了会被裁掉，不会自动换行
3. **`Text` 是字符串，行之间用 `\n`**，不是字符串数组
4. 1.19 及以前的版本没有 `FrontText`，只有 `Text`（本章按 1.20+ 写）

### 98.5 方块 ID 与状态：唯一需要试的地方

| 方块 | 本项目用的 ID | 备选（显示成空气时换） |
|---|---|---|
| 箱子 | `minecraft:chest`，states `{}` | `minecraft:trapped_chest` |
| 立式告示牌 | `minecraft:oak_standing_sign`，`{"ground_sign_direction": 8}` | `minecraft:standing_sign` |

`ground_sign_direction` 是 0..15 的朝向（8 = 面向南）。
**箱子故意留空 states**：让游戏填默认值，比猜 `cardinal_direction` 稳。

❗ 状态名写错（比如给 1.21 的方块写 `facing_direction`）会让方块变成空气，
**不报错、不崩溃，就是没了** —— 所以必须用 `check_props.py` 回读确认。

### 98.6 说明区怎么摆（`props`）

给 spec 加一个 `props` 列表，`build_scene()` 会**在地板最前面预留 2 行**，
链整体往后挪，说明区摆在 `z = 0` 那一排：

```python
"props": [
    {"kind": "chest", "at": (0, 0), "name": "潮汐 · 说明箱", "items": items},
    {"kind": "sign",  "at": (2, 0), "front": ["标题", "第二行"]},
    {"kind": "sign",  "at": (3, 0), "front": ["操作", "说明"]},
]
```

- `at` 可省略，省略就按顺序找第一个空格
- 位置不合法会直接 `raise`（不会静默摆到别处）
- 坐标是**局部坐标**（地板坐标系的 x, z），y 固定在第 4 层（世界 -60）

### 98.7 结构导出必须带走非命令方块实体（踩过的坑）

`mcworld_to_structure.py` 原来有一行：

```python
if e.get("id") != "CommandBlock":
    continue          # ← 箱子 / 告示牌全被丢掉
```

结果：世界里有箱子，导出成 `.mcstructure` 之后**箱子是空的、告示牌是空白的**。
已修成「所有方块实体都带走」，并加了 `(x,y,z) in blocks` 的判断（防止给空气格挂实体）。

**判断方法**：导出后跑一次

```bash
python scripts/check_props.py 潮汐鱼竿枪.mcstructure
```

它会逐个打印箱子里每件物品的名字 / Lore / data / slot，以及告示牌每一行。
**`.mcworld` 和 `.mcstructure` 都要跑一遍** —— 前者验证生成，后者验证搬运。

### 98.8 三种"东西不见了"的排查表

| 现象 | 原因 | 修法 |
|---|---|---|
| 箱子是空的 | `id` 写成 `minecraft:chest` | 改 `"Chest"` |
| 箱子里有物品但没名字 | `display` 写到 `tag` 外面了 | 挪进 `tag` |
| 物品名显示了、Lore 没有 | `Lore` 写成字符串不是列表 | 改成列表 |
| 告示牌一片空白 | 版本没有 `FrontText` | 换 `standing_sign` + 加 `Text` 键 |
| 告示牌方块变成空气 | 方块 ID 在你这版不存在 | 换备选 ID（98.5） |
| 结构粘出来箱子空了 | 导出时只带命令方块 | 修 `mcworld_to_structure.py`（98.7） |
| 物品拿出来就消失 | `Count` / `Damage` 类型写错 | Byte / Short |
| 纹饰 / 自定义键没生效 | 键写在了 `tag` 外面，或类型写错（`'feather'` 写成 `feather`） | 用 `item_from_snbt` 让解析器定类型（98.2b） |
| `SnbtError: 列表元素类型不一致` | `Lore` 里混了字符串和数字 | NBT 列表必须同构，全部加引号 |

---

## 99. 伪无鱼竿枪：真实原理（原文逐行拆解）★

> 出处：`refs/伪无鱼竿枪.txt`（453 行）+ `refs/伪无判定.txt`（467 行）+ `refs/伪无粒子 - 副本.txt`（134 行）。
> **这一章推翻本 skill 第 85 章的旧描述**，以原文为准。

### 99.0 一句话

> **钩子是扳机，`xp_orb` 是"弹道载体"——它不飞，它承载朝向和散射偏移，射线每刻从它身上重算。**

### 99.1 三件东西各干什么

| 东西 | 真实职责 | 不是什么 |
| --- | --- | --- |
| `fishing_hook` | **扳机信号**。存在 = 有人抛竿了，取完就 `kill` | 不是子弹 |
| `xp_orb` | **弹道载体**。存 `uid / 伤害 / 射程 / 粒子 / 队伍uid / 水平 / 垂直`，朝向 = 瞄准方向 | 不是"会飞的子弹模型" |
| 空 `tp @s` | **刷新玩家**。强制客户端重新同步，HUD / 状态立刻生效 | 不是"传送" |

**"伪无"的含义**：钩子一出现就被杀，玩家**永远看不到浮漂**，视觉上就是"手里鱼竿直接开枪"。

### 99.2 完整流水线（12 步，顺序不能乱）

```
① testfor @e[type=fishing_hook]                       ← 扳机
② execute at @e[type=fishing_hook] as @p ...          ← 钩子旁最近的玩家 = 开火者
③ 没子弹 → tellraw 提示 + 空枪音效（先判，后开火）
④ kill @e[type=fishing_hook]                          ← 立刻杀钩子 = 伪无
⑤ testfor @e[scores={连发备份=1..}]                    ← 连发闸门
⑥ 弹丸循环：summon xp_orb ^^^1.45 facing ^^^1000      ← 眼前 1.45 格，朝向 = 视线远点
⑦ tp ~~500~                                          ← 球垂直顶到 y+500（离开视野/碰撞）
⑧ tag @e[r=1,type=xp_orb] add 子弹                    ← 打标（此时球在玩家身边 1 格内）
⑨ 灌参数：uid / 伤害 / 射程 / 粒子 / 队伍uid / 水平 / 垂直
⑩ 散射：random -10000 10000 → 除以枪的散布值 → 二分法转成角度
⑪ 枪口粒子 + 后坐力 + 音效 + 缓慢 + 间隔复位
⑫ 连发倒计时 / 子弹数递减
```

**❗ ③ 必须在 ④ 之前**：钩子杀了就取不到 `@p`，没子弹的提示会丢失。

### 99.3 散射：随机数 → 角度（本系统最值钱的一段）★★

**两个计分项就是散射量，单位是 1/100 度。**

```
scoreboard players random @e[tag=子弹] 水平 -10000 10000
scoreboard players random @e[tag=子弹] 垂直 -10000 10000
scoreboard players operation @e[tag=子弹] 水平 /= @s 水平      ← 除以枪的散布值
scoreboard players operation @e[tag=子弹] 垂直 /= @s 垂直
```

枪的 `水平`/`垂直` 越大越准（分母），子弹的 `水平`/`垂直` 是随机偏移。

**然后每刻用二分法把"分数"分批加到旋转上**：

| 分数剩余 | 动作 | 等于 |
| --- | --- | --- |
| `水平 >= 512` | `tp ~~~~5.12` | yaw **+5.12°** |
| `水平 >= 256` | `tp ~~~~2.56` | yaw +2.56° |
| `水平 >= 128` | `tp ~~~~1.28` | yaw +1.28° |
| … 64 / 32 / 16 / 8 / 4 / 2 / 1 | `~~~~0.64` … `~~~~0.01` | 逐档减半 |
| `水平 <= -512` | `tp ~~~~-5.12` + `add 512` | 负方向 |
| … 对称 10 档 | | |

`tp ~~~~N` 的**第 4 个参数是 yRot**，`~5.12` = 相对旋转 +5.12 度。
`tp ~~~~~N` 的**第 5 个参数是 xRot**（俯仰），写法完全对称。

> **❗ 散射不是"每刻位移偏移"，是"出生时把朝向拧一下"。**
> 一次 tick 内 10 档全部跑完，`水平` 归零，之后不再匹配——子弹带着一个**固定偏角**飞出去。
> 这就是"经验球确定散射"的全部意思：**球是那个被拧了角度的载体**。

**为什么用二分法而不是直接 `tp ~~~~5`**：`tp` 的旋转参数只吃小数，一次只能加一个值；
用 512/256/…/1 的二进制分解，**10 条命令覆盖 -10000..10000 全部整数**，且每档减完就不再多减。

### 99.4 弹道：球被推到 y+500，射线每刻重算

**关键：`tp ~~500~` 是 `y + 500`，不是 `z + 500`。** 三个参数是 `x=~`、`y=~500`、`z=~`。

球召唤在玩家眼前（`^^^1.45`）、朝向 = 瞄准方向，然后**垂直往上顶 500 格**——
离开地面、离开视野、不进碰撞、不会被捡。之后它**再也不动**。

所有计算都用 `y - 498.5` 把它拉回来，所以**和朝向无关，任意方向都能打**：

| 偏移 | 实际含义 | 结果 |
| --- | --- | --- |
| `tp ~~500~` | **y + 500** | 球升到 500 格高空 |
| `~~-498.5~` | **y - 498.5** | 球原位 **+1.5**（射线起点 / 头顶） |
| `~~-500.5~` | **y - 500.5** | 球原位 **-0.5**（腿） |
| `~~-499.5~` | y - 499.5 | 球原位 **+0.5**（胸） |
| `~~-499~` | y - 499 | 球原位 **+1.0**（头） |

所以 `~~-500.5~` / `~~-499.5~` / `~~-499~` 三段 = **腿 / 胸 / 头**，
相对差 0.5 / 1.5 / 2.0 —— 这正是第 85.3 节的三段肢体判定。

**净偏移 = 500 − 498.5 = 1.5**：所有计算点都比"球原位"高 1.5 格。
球原位是 `^^^1.45`（眼睛沿朝向 1.45 格），所以射线起点落在眼前上方一点，
**不会从自己脚底下穿出去**。这个 1.5 是刻意留的抬头量，不是凑数。

> 这套"顶到高空 + 减回来"的写法好处是：**补偿量是纯 y**，
> 不依赖 `^` 局部坐标，所以球在空中被任何方式推动都不会算错。


### 99.5 四步：碰撞穷举 → 三段肢体 → 粒子 → 收尾

原文的执行顺序是**固定的四步**，顺序换一位就会"有特效没伤害"：

```
① 穷举判定前方有无碰撞 → 截断射程
② 穷举判定 + positioned 偏移 → 三段肢体（腿 / 胸 / 头）
③ 按射程逐格生成粒子（弹道可视化）
④ 收尾：结算伤害、清归属、kill 球
```

**① 碰撞穷举**（`射程备份` = 剩余射程，枪的 `射程` 值）：

```
execute as @e[tag=子弹,scores={射程备份=10..}] at @s positioned ~~-498.5~ positioned ^^^10 \
  unless block ^^^ air unless block ^^^ scaffolding unless block ^^^ ladder \
  ... 共 40 多种可穿透方块 ... \
  run scoreboard players set @s 射程备份 10
```

- 一长串 `unless block` = **穿透白名单**（空气、草、铁栏杆、铁轨、水、岩浆、按钮、地毯、藤蔓、门…）
- N 格处不是白名单方块 → 把 `射程备份` 截断到 N
- 从大 N 往小 N 依次执行，最后留下的是**最近的那个障碍**
- **一 tick 内 10 档全扫完**，不是每刻走一格

**② 三段肢体**：同一命中点做三次 y 偏移，只差 `~~-499~`（头）/ `~~-499.5~`（胸）/ `~~-500.5~`（腿）。
**顺序必须从高到低**（头 → 胸 → 腿），命中就打 `命中` tag，后两段靠 `tag=!命中` 跳过，
保证一发只结算一次、不会三段全中扣三次血。

**③ 粒子**：`positioned ^^^N` + `particle <名> ~~-498.5~`，N 从 1 到 `射程`。
粒子和判定共用同一个 `射程备份`，所以**看到打中就是真打中**。

**④ 收尾**：`damage ... 0 override` → `reset 攻击uid` → `kill @e[tag=子弹]`。

### 99.6 命中 + 伤害 + 归属

```
# 在截断点找最近的实体（排除掉落物、钩子、船、经验球、雪球、药水、狐狸）
execute as @e[tag=子弹,scores={射程备份=1..}] at @s positioned ^^^ positioned ~~-500.5~ \
  at @e[r=1.5,c=1,type=!item,type=!fishing_hook,type=!boat,type=!xp_orb,...] \
  unless score @e[c=1] 队伍uid = @s 队伍uid \
  run scoreboard players operation @e[r=1.5,c=1,type=!item] 攻击uid = @s uid

# 打中就把射程清零（子弹失效）
... run scoreboard players set @s 射程备份 0

# 结算：谁身上有攻击uid，就让攻击者打它
execute as @e[tag=子弹,scores={受伤=1..}] at @s at @e[scores={攻击uid=1..}] \
  if score @e[c=1] 攻击uid = @s uid run damage @e[c=1] 0 override

# 收尾
scoreboard players reset @e[scores={攻击uid=1..}] xuid
kill @e[tag=子弹]
```

四条铁律：

1. **`damage ... 0 override`** —— 伤害自己算，`0` 只是占位，死亡交给引擎判
2. **`队伍uid` 相同不结算** —— 这就是组队免伤
3. **`uid` → `攻击uid`** —— 击杀归属靠这一跳，多人混战才不会算错
4. **`type=!...` 黑名单必须齐** —— 少排一个 `xp_orb`，子弹会"命中"自己

### 99.7 后坐力 / 音效 / 枪口：三个查表

**后坐力**（分数 → 镜头抖动，二分法同上）：

| 分数 | 命令 |
| --- | --- |
| `32..` | `camerashake add @s 0.32 0.2 rotational` + `remove 32` |
| `16..` | `camerashake add @s 0.16 0.2 rotational` + `remove 16` |
| 8 / 4 / 2 / 1 | `0.08 / 0.04 / 0.02 / 0.01` |

**音效**：`playsound` 计分项 1..15，**每档 2–4 层**叠加（这就是"音效必须 2-4 层"的出处）：

```
playsound=1 → mob.blaze.hit 0.8/1.5  +  cauldron.explode 1/6  +  crossbow.shoot 1/4  +  cauldron.explode 1/2.2
playsound=10 → mob.skeleton.step 1/1.3 + random.explode 1/8 + mob.irongolem.hit 1/2 + random.explode 1/5
```

**枪口粒子**：`枪口` 1..6，`anchored eyes positioned ^^^1`：

| 枪口 | 粒子 |
| --- | --- |
| 1 | `blue_flame_particle` |
| 2 | `large_explosion`（`positioned ~~-0.9~` 下压） |
| 3 | `basic_flame_particle` |
| 4 | `sparkler_emitter` |
| 5 | `colored_flame_particle` |
| 6 | `basic_smoke_particle` |

**缓慢**：`缓慢` 1..5 → `effect slowness 1 <0..4> true`（瞄准时减速，5 档）

### 99.8 连发与射速

```
连发   = 这一次要打几颗（霰弹数）
连发备份 = 剩余颗数，每刻 -1
间隔   = 射速冷却，每刻 -1，到 0 才能再开火
```

开火时 `连发备份 = 连发`、`间隔 = 开枪间隔`；
`连发备份=1..` 是弹丸循环的闸门——**一 tick 出一颗**，所以霰弹是"逐帧散开"的。

### 99.9 本 skill 旧版错在哪（对照表）

| 项目 | ❌ 旧版（第 85 章，错） | ✅ 原文（本章） |
| --- | --- | --- |
| 弹丸 | `xp_orb` 当会飞的子弹 | `xp_orb` 当**载体**，位置固定在远处 |
| 朝向继承 | 两次 `tp`：`tp @e ~~~ ~ ~` 再 `tp @e ^ ^ ^1.2` | 召唤时 `facing ^^^1000` 直接定朝向 |
| 散射 | 每刻 `^±0.03^0^0.9` 位移累加 | **旋转 yaw/pitch**，1/100 度，二分法 10 档 |
| 命中 | `@e[r=3.5]` 一次性结算 | 射线扫描 + 40 项穿透白名单 + `r=1.5` |
| 伤害 | `/damage` 分档表 | `damage ... 0 override`，伤害存计分项 |
| 归属 | `@p[r=48,hasitem=鱼竿]` 近似 | `uid` → `攻击uid` 精确归属 |
| 免伤 | 无 | `队伍uid` 比对 |

### 99.10 照抄原文会坏的 6 处

| # | 问题 | 修法 |
| --- | --- | --- |
| 1 | `tp ~~500~` 读成 `z+500` | 它是 **`y+500`**（垂直顶高），配套的 `~~-498.5~` 是 y 减回去 |
| 2 | `positioned ^^^wooden_button` 少空格 | 全部补空格，否则解析失败静默 |
| 3 | 白名单里混了 `water` / `lava` | 想打水面就别放进去；放了等于子弹穿水 |
| 4 | `scoreboard players remove` 写重复（256 减两次） | 每档只减一次，重复减会让散射偏 |
| 5 | 用 `#` 开头命名假玩家 | 网易服当注释符，整条语法错误 |
| 6 | `tag` 当状态存 | 网易服不保证 `tag` 持久，状态一律计分板 |

---

## 100. 换弹：`zd` / `zdmax` 双变量模型 ★

> 出处：`refs/换弹部分666.txt`（72 行）。

### 100.1 四个变量

| 变量 | 含义 |
| --- | --- |
| `zd` | **弹匣里现在有几颗** |
| `zdmax` | **备弹还剩几颗**（不在弹匣里） |
| `弹匣容量` | 常量，这个弹匣最多几颗 |
| `换弹` | 换弹倒计时，`0` = 没在换 |

临时量：`zd备份`、`zd备份2`（算差值用）。

### 100.2 溢出回灌（换弹前必做）

```
execute as @a[scores={枪械编号=1..,zd=1..}] if score @s zd > @s 弹匣容量 run tag @s add 子弹溢出
execute as @a[tag=子弹溢出] run scoreboard players operation @s zd备份2 = @s zd
execute as @a[tag=子弹溢出] run scoreboard players operation @s zd = @s 弹匣容量
execute as @a[tag=子弹溢出] run scoreboard players operation @s zd备份2 -= @s 弹匣容量
execute as @a[tag=子弹溢出] run scoreboard players operation @s zdmax += @s zd备份2
```

**为什么要有这段**：换枪 / 改容量后 `zd` 可能大于新容量，多出来的必须退回 `zdmax`，
否则那几颗子弹凭空消失。

### 100.3 触发条件（五个必须同时成立）

```
execute as @a[scores={枪械编号=1..,zdmax=1..},rxm=88,hasitem={item=fishing_rod,location=slot.weapon.mainhand}] \
  if score @s zd < @s 弹匣容量 \
  unless score @s 换弹 matches 1.. \
  unless score @s 连发a matches 1.. \
  run scoreboard players operation @s 换弹 = @s 换弹时间
```

| 条件 | 为什么 |
| --- | --- |
| `zdmax=1..` | 没备弹就不换 |
| `rxm=88` | **低头**触发（Bedrock 用 `rxm=88`，Java 的 `rx=-88` 不对） |
| `hasitem=鱼竿` | 手持枪 |
| `zd < 弹匣容量` | 弹匣没满 |
| `换弹` 不是 `1..` | 不在换弹中 |
| `连发a` 不是 `1..` | 不在连发中（否则中途换弹会丢弹） |

### 100.4 结算：倒计时到 1 时两条分支

```
# 每刻递减 + 音效（两层：过程 1.5，最后一刻 0.8）
scoreboard players remove @a[scores={换弹=1..}] 换弹 1
execute at @a[scores={换弹=1..}] run playsound armor.equip_iron @a[r=20] ~~~ 1 1.5
execute at @a[scores={换弹=1}] run playsound armor.equip_iron @a[r=20] ~~~ 1 0.8

# 差值 = 容量 - 现有
execute as @a[scores={换弹=1}] run scoreboard players operation @s zd备份 = @s 弹匣容量
execute as @a[scores={换弹=1}] run scoreboard players operation @s zd备份 -= @s zd
```

| 分支 | 条件 | 动作 |
| --- | --- | --- |
| **A · 备弹不够补满** | `zdmax < zd备份` | `zd += zdmax`；`zdmax = 0`；`换弹 = 0` |
| **B · 备弹够** | `zdmax >= zd备份` | `zd = 弹匣容量`；`zdmax -= zd备份`；`换弹 = 0` |

```
# 分支 A
execute as @a[scores={换弹=1}] if score @s zdmax < @s zd备份 run tag @s add addzd
execute as @a[tag=addzd] run scoreboard players operation @s zd += @s zdmax
execute as @a[tag=addzd] run scoreboard players set @s zdmax 0
execute as @a[tag=addzd] run scoreboard players set @s 换弹 0

# 分支 B
execute as @a[scores={换弹=1}] if score @s zdmax >= @s zd备份 run tag @s add addzd2
execute as @a[tag=addzd2] run scoreboard players operation @s zd备份 = @s zd
execute as @a[tag=addzd2] run scoreboard players operation @s zd = @s 弹匣容量
execute as @a[tag=addzd2] run scoreboard players operation @s zd -= @s zd备份
execute as @a[tag=addzd2] run scoreboard players operation @s zdmax -= @s zd
execute as @a[tag=addzd2] run scoreboard players operation @s zd = @s 弹匣容量
execute as @a[tag=addzd2] run scoreboard players set @s 换弹 0
```

> **B 分支的写法很绕但必须照抄**：先算差值存回 `zd`，再从 `zdmax` 扣掉差值，
> 最后把 `zd` 覆盖成容量。顺序反了就会扣错。

### 100.5 为什么单变量会"无限装填"

旧版（潮汐鱼竿枪 v2 早期）只用 `tg_mag` 一个变量：

```
换弹 → tg_mag = 容量 → 开一枪 tg_mag -1 → 空了又换弹 → ...
```

问题在**换弹触发条件里没有"备弹 > 0"**，也没有"容量"参照物：

1. `tg_mag` 同时承担"弹匣"和"备弹"，补满后永远补得满 → 没有打空的可能
2. 副手放了 `data=0` 的鹦鹉螺壳 → 四条赋值命令都不命中 → `tg_type` 停在 0 → `tg_mag` 也是 0
3. 换弹补 0 发 → 下一 tick 又是空 → **无限循环，整条链卡死**

**修法三条一起上**：

1. 拆成 `zd` / `zdmax` 两个变量（本章模型）
2. 换弹触发加 `zdmax=1..` 守卫
3. `state` 链首给所有人一个**默认枪型**兜底（`set @a[hasitem=鱼竿] tg_type 1`），
   别让 `tg_type` 停在 0

---

## 101. 组队系统：`队伍uid` + 十进制键盘

> 出处：`refs/组队系统.txt`（111 行）。

### 101.1 队伍编号

```
scoreboard players random @a[scores={menu=35},rx=-88] 队伍uid 10000 99999
```

**5 位随机数当队伍 ID**，不建队伍表、不存名单——`队伍uid` 相同就是同队。
免伤、组队提示、成员查询全靠 `队伍uid` 比对。

### 101.2 输入队伍编号：十进制移位

菜单只有 0–9 十个数字键，要输 5 位数，用**乘十 / 加数 / 除十**：

```
# 除最后一位：设置队伍 /= 10   （退格）
scoreboard players operation @s 设置队伍 *= 十 定值      # 进一位
scoreboard players add @s 设置队伍 1                    # 按 1
scoreboard players add @s 设置队伍 2                    # 按 2
...
scoreboard players operation @s 设置队伍 /= 十 定值      # 退格
```

`十` 是假玩家常量，`定值` 是它的计分项，值是 `10`。

> **这是"没有输入框"的通用解法**：任何需要玩家输数字的场景（金额、坐标、密码）都用这一套。

### 101.3 申请 / 通过 / 退出

| 步骤 | 命令要点 |
| --- | --- |
| 发起申请 | `random 申请倒计时 200 200`（开一个窗口） |
| 申请中 | `at @a[申请倒计时=1..] if score @a[c=1] 设置队伍 = @s 队伍uid` → 打 `申请中` |
| 对方确认 | 手持 `experience_bottle` + `dy=0,y=~1.48` 站立高度 → 打 `申请通过` |
| 入队 | `队伍uid = 设置队伍`，然后 `reset 设置队伍` |
| 退出 | `random 队伍uid 10000 99999`（直接换一个新编号 = 单人队） |

**退出 = 换随机号**：不需要维护"队伍空了要删除"这类逻辑，一个人一个号天然成立。

### 101.4 空 `tp` 刷新

```
execute as @a[tag=组队menu] at @s run tp @s
execute as @a[scores={menu=21..32},rx=-88] at @s run tp @s
```

`tp @s`（原地传送）会强制客户端重新同步实体状态，**HUD / 动作栏立刻刷新**。
菜单按一下就调一次，比等下一次 `titleraw` 快一帧。

---
