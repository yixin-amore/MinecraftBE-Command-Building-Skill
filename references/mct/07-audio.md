# 音效（52~57 / 76 章）

> 音效清单、`note.pling` 音阶表、为什么单音效塑料、环境音、位置衰减与限流、真实参数。
**什么时候读**：挑音效名、调音高音量、设计声音层次。

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

---

## 52. 归属与播报

### 52.1 谁打的谁拿奖励

用 `uid` + 最近攻击者记录：

```
# 记录最近打我的玩家
execute as @e[type=zombie] at @s if entity @a[r=4] run scoreboard players operation @s 归属 = @p[tag=!] uid
# 死亡时按归属发奖
execute as @e[type=zombie,scores={hp=..0}] run scoreboard players operation @a[scores={uid=0}] ...
```

更简单的做法：**伤害结算时就记下攻击者**，死亡时直接给那个人。

### 52.2 播报

```json
{"rawtext":[{"text":"§f｜§3〖§b经验 §f> "},{"score":{"name":"@s","objective":"xp"}},
 {"text":" + "},{"score":{"name":"@s","objective":"经验奖励"}},
 {"text":"\n §bEoxp ： §f"},{"score":{"name":"经验前置","objective":"计算"}}]}
```

渲染：

```
｜〖经验 > 120 + 30
 Eoxp ： 120
```

「当前值 + 增量」+「前置值」两行，玩家能看懂这一下加了多少。

### 52.3 五种货币的播报配色

| 货币 | 前缀色         | 标签            |
| -- | ----------- | ------------- |
| 经验 | `§3` + `§b` | `§bEoxp`      |
| 金币 | `§g` + `§e` | `§eGold coin` |
| 灰烬 | `§7` + `§8` | `§7Ashes`     |
| 钻石 | `§a` + `§2` | `§2Diamond`   |
| 碎片 | `§g` + `§6` | `§6Fragment`  |

---

# 第七部分 · 音效

## 53. 音效清单

| 类别        | 音效                                       | 用途     |
| --------- | ---------------------------------------- | ------ |
| **UI 点击** | `random.click`                           | 按钮、菜单项 |
|           | `random.orb`                             | 拾取、确认  |
|           | `note.pling`                             | 音阶旋律   |
|           | `random.levelup`                         | 升级     |
| **战斗**    | `random.anvil_use`                       | 重击     |
|           | `mob.enderdragon.flap`                   | 挥砍风声   |
|           | `random.explode`                         | 爆炸技能   |
|           | `random.totem`                           | 大招     |
|           | `block.anvil.land`                       | 落地重击   |
| **环境**    | `random.door_open` / `random.door_close` | 传送门、开箱 |
|           | `ambient.nether_wastes.mood`             | 区域氛围   |
|           | `block.end_portal.spawn`                 | 死亡     |
|           | `random.glass`                           | 破碎     |
| **提示**    | `note.bass`                              | 警告     |
|           | `random.pop`                             | 弹出     |

❗ **`ui.button.click` 是 Java 版音效，Bedrock 不存在。** 点击音用 `random.click`。

---

## 54. `note.pling` 音阶表

音调参数 `pitch = 2^(n/12)`，`n` 是半音数。

| n   | pitch    | 音名    |
| --- | -------- | ----- |
| -12 | 0.500000 | 低八度 C |
| -11 | 0.529732 |       |
| -10 | 0.561231 |       |
| -9  | 0.594604 |       |
| -8  | 0.629961 |       |
| -7  | 0.667420 |       |
| -6  | 0.707107 |       |
| -5  | 0.749153 |       |
| -4  | 0.793701 |       |
| -3  | 0.840896 |       |
| -2  | 0.890899 |       |
| -1  | 0.943874 |       |
| 0   | 1.000000 | C     |
| 1   | 1.059463 | C#    |
| 2   | 1.122462 | D     |
| 3   | 1.189207 | D#    |
| 4   | 1.259921 | E     |
| 5   | 1.334840 | F     |
| 6   | 1.414214 | F#    |
| 7   | 1.498307 | G     |
| 8   | 1.587401 | G#    |
| 9   | 1.681793 | A     |
| 10  | 1.781797 | A#    |
| 11  | 1.887749 | B     |
| 12  | 2.000000 | 高八度 C |

### 54.1 同一刻多个 = 和弦

同刻发多个 `note.pling` 会**叠加成和弦**，不是依次播放。

```
playsound note.pling @p ~~~ 1 1.000000
playsound note.pling @p ~~~ 1 1.259921     ← 大三度
playsound note.pling @p ~~~ 1 1.498307     ← 纯五度
```

三个同刻 = C 大三和弦。

### 54.2 旋律

按顺序每 2–4 刻发一个，就是一段旋律：

```
note.pling 0.353553  →  note.pling 1.334840  →  note.pling 0.899
```

（这三个值来自实战文档，分别是 n=-18、n=5、n≈-2）

---

## 55. 音效叠加：单音效为什么"塑料"

### 55.1 单条 `playsound` 缺三样东西

一条 `playsound` 是**一个采样点**：一个频段、一个时刻、一个音量。  
听感上就是"叮"一声，像电子表报时。

真实的物理撞击有三样它没有的东西：

| 缺什么    | 真实声音里                     | 单条 `playsound` |
| ------ | ------------------------- | -------------- |
| **包络** | 起音（attack）→ 衰减（decay）→ 余响 | 只有一个瞬态，没有尾巴    |
| **频段** | 低频震动 + 中频摩擦 + 高频碎裂，三层同时   | 只有一个频段         |
| **空间** | 近处干、远处带反射                 | 距离只改音量，不改音色    |

所以"有质感"不是换一个更好的音效，而是**把缺的三样补上**——三样正好对应三个可叠的维度：

| 维度     | 补的是 | 怎么做               |
| ------ | --- | ----------------- |
| **频谱** | 频段  | 低 / 中 / 高各一条，同刻播  |
| **时间** | 包络  | 错开 1–5 刻，造出起音与余响  |
| **音高** | 厚度  | 同音效不同 `pitch` 同刻播 |

❗ 顺序很重要：**先补频谱，再补时间，最后补音高**。  
只加音高不音频谱，结果是"更响的叮"，不是"更重的一击"。

### 55.2 频谱三层模型

| 层      | 听感上是什么             | 决定什么         | 音效                                                                          | 音量  | 音调      |
| ------ | ------------------ | ------------ | --------------------------------------------------------------------------- | --- | ------- |
| **低频** | "咚"——胸腔能感到的闷响      | 这一下**有多重**   | `random.explode` / `block.anvil.land` / `note.bass`                         | 0.6 | 0.7–0.9 |
| **中频** | "啪"——能听出是刀、是拳、还是金属 | 这是**什么动作**   | `random.anvil_use` / `entity.player.attack.strong` / `mob.zombie.woodbreak` | 1.0 | 1.0–1.2 |
| **高频** | "嚓"——空气被划开的那一下     | 这一下**有多快多利** | `random.orb` / `block.amethyst_block.chime` / `note.pling`                  | 0.5 | 1.4–1.8 |

三层同刻播，听感就是一次"有重量、有身份、有锐度"的击打。

#### 听感 → 参数 对照表

不要说"更带感"，直接改参数：

| 想要的听感       | 改什么       | 具体数值                                   |
| ----------- | --------- | -------------------------------------- |
| **更重**      | 加/加厚低频层   | `random.explode` 音量 0.7，pitch 0.7      |
| **更亮**      | 加高频层      | `random.orb` 音量 0.5，pitch 1.6          |
| **更厚**      | 同音效叠八度    | 同一音效 pitch 0.5 + 1.0 同刻                |
| **更钝**      | 砍掉高频层     | 只留低 + 中                                |
| **更锐**      | 换高频素材     | `block.amethyst_block.chime` pitch 1.7 |
| **更长（有尾巴）** | 延迟补一层     | +3 刻播 `note.bass` pitch 0.5，音量 0.3     |
| **更近**      | 去掉延迟，音量拉满 | 只播中频，音量 1.0                            |
| **更远**      | 延迟 + 降音量  | +5 刻播高频，音量 0.25                        |
| **更脆**      | 换玻璃/敲击类   | `random.glass` / `note.hat`            |
| **更闷**      | 全层降 pitch | 所有层 pitch × 0.8                        |

```
# 一次斩击 = 三层叠加
playsound random.explode           @s ~ ~ ~ 0.6 0.8      ← 低频：闷响
playsound entity.player.attack.strong @s ~ ~ ~ 1.0 1.1   ← 中频：挥砍主体
playsound block.amethyst_block.chime @s ~ ~ ~ 0.5 1.6    ← 高频：破空
```

### 55.3 时间错位：让声音"散开"

同刻三个音效还是"一坨"。把高频**延后 1–2 刻**，就有了"先破空、后余响"的层次。

| 时机     | 播什么              |
| ------ | ---------------- |
| 第 0 刻  | 低频 + 中频（冲击 + 主体） |
| 第 +2 刻 | 高频（余响 / 金属震颤）    |
| 第 +5 刻 | 极轻的环境反射（可选）      |

实现：用一个短计数器。

```
# 触发时置 2
scoreboard players set @s fx_t 2
# 每刻递减
scoreboard players remove @a[scores={fx_t=1..}] fx_t 1
# fx_t=1 那一帧播高频
execute as @a[scores={fx_t=1}] run playsound block.amethyst_block.chime @s ~ ~ ~ 0.5 1.6
```

❗ 计数器递减要放在**段内必成功区**（第 8.3 节），否则一次 `titleraw` 失败就卡住不降。

### 55.4 音高分层：八度叠加

同一音效用 `pitch 0.5` 和 `pitch 1.0` **同刻**播，等于原音 + 低八度，  
听感上**厚度翻倍**，而且不会有"两个声音"的错位感。

```
playsound note.bell @s ~ ~ ~ 0.8 0.5      ← 低八度
playsound note.bell @s ~ ~ ~ 0.8 1.0      ← 原音
```

这是最快的"加厚"手段，成本只有两条命令。

**三度 / 五度叠加**（做和弦，用于奖励、升级）：

```
playsound note.pling @s ~ ~ ~ 1.0 1.000000    ← C
playsound note.pling @s ~ ~ ~ 1.0 1.259921    ← E（大三度）
playsound note.pling @s ~ ~ ~ 1.0 1.498307    ← G（纯五度）
```

### 55.5 八套实战配方

#### ① 挥空（轻，音调高）

```
playsound mob.enderdragon.flap @s ~ ~ ~ 0.7 1.4
```

**听感**：一声空响，没有落点。  
**为什么只有一层**：挥空本来就该"空"。加低频反而会让人以为打中了。

#### ② 普通命中（三层）

```
playsound random.explode              @s ~ ~ ~ 0.4 0.9     ← 低频
playsound entity.player.attack.strong @s ~ ~ ~ 1.0 1.1     ← 中频
playsound random.orb                  @s ~ ~ ~ 0.6 1.5     ← 高频
```

**听感**：有重量、有落点，但不算狠。  
低频音量压到 0.4，是为了给暴击留出"更重"的余量——普通命中不能顶格。

#### ③ 暴击（四层 + 时间错位）

```
playsound random.explode              @s ~ ~ ~ 0.7 0.7     ← 更重的低频
playsound entity.player.attack.strong @s ~ ~ ~ 1.0 1.0     ← 中频
playsound random.orb                  @s ~ ~ ~ 1.0 1.6     ← 高频更亮
playsound note.bell                   @s ~ ~ ~ 0.8 0.5     ← 低八度加厚
```

**听感**：比普通命中重一档，而且"嗡"的一下有尾巴。  
**和普通命中的差别只有两处**：低频音量 0.4→0.7、pitch 0.9→0.7，再加一条低八度 `note.bell`。  
改两个数就够了，不需要换素材。

#### ④ 技能释放（五层，含和弦）

```
playsound random.explode              @s ~ ~ ~ 1.0 0.6     ← 冲击
playsound mob.enderdragon.growl       @s ~ ~ ~ 0.8 1.0     ← 龙吼主体
playsound random.totem                @s ~ ~ ~ 0.9 1.0     ← 神圣感
playsound note.pling                  @s ~ ~ ~ 0.7 1.000000
playsound note.pling                  @s ~ ~ ~ 0.7 1.498307 ← 五度
```

**听感**：大、有仪式感，像"这件事很重要"。  
**关键在 `random.totem` + 纯五度**：这两个一加，任何动作都会显得"被祝福过"。  
只给技能和大招用，普通攻击用了会掉价。

#### ⑤ 开箱 / 获得物品（明亮，上行音阶）

```
playsound random.orb   @s ~ ~ ~ 1.0 1.0
playsound random.levelup @s ~ ~ ~ 0.6 1.2
```

**听感**：亮、有期待感。`random.levelup` 自带"变好"的暗示，音量压到 0.6 免得抢戏。

要"上行"就用错位的 `note.pling`：

```
playsound note.pling @s ~ ~ ~ 1.0 1.000000     ← 第 0 刻
# 第 2 刻
playsound note.pling @s ~ ~ ~ 1.0 1.259921
# 第 4 刻
playsound note.pling @s ~ ~ ~ 1.0 1.498307
# 第 6 刻
playsound note.pling @s ~ ~ ~ 1.0 2.000000
```

#### ⑥ 升级（大，五层 + 和弦 + 错位）

```
# 第 0 刻：冲击
playsound random.levelup @s ~ ~ ~ 1.0 1.0
playsound note.bell      @s ~ ~ ~ 0.8 0.5
# 第 3 刻：和弦铺开
playsound note.pling @s ~ ~ ~ 0.9 1.259921
playsound note.pling @s ~ ~ ~ 0.9 1.498307
playsound note.pling @s ~ ~ ~ 0.9 2.000000
```

**听感**：先一下硬的，然后三个音"铺"开来，像舞台灯亮。  
**第 3 刻是关键**：同刻播三个音会和第一下糊在一起，错开 3 刻才有"展开"的感觉。

#### ⑦ 受伤（闷，低频为主）

```
playsound entity.player.hurt @s ~ ~ ~ 1.0 0.9
playsound random.fizz        @s ~ ~ ~ 0.5 0.7
```

**听感**：闷、短、不舒服。  
**故意不加高频**：高频会让受伤听起来"清脆"，那就变成"打别人"了。

#### ⑧ 死亡（下行，拉长）

```
playsound block.end_portal.spawn @s ~ ~ ~ 1.0 0.8
playsound note.bass              @s ~ ~ ~ 0.9 0.5
```

**听感**：下沉、拉长，像"掉下去"。  
**只有两层，但都在低频**：死亡不需要锐度，需要的是"往下坠"。

### 55.6 音量预算：别把叠加成噪音

叠加不是越多越好。**同刻总音量建议 ≤ 1.5**，超过就是噪音。

| 层数  | 单层音量            | 总音量       |
| --- | --------------- | --------- |
| 2 层 | 0.6 + 0.9       | 1.5       |
| 3 层 | 0.5 + 1.0 + 0.4 | 1.9 ⚠️ 偏大 |
| 3 层 | 0.4 + 0.8 + 0.4 | 1.6 ✅     |

原则：

1. **中频永远是 1.0**（主体音量），其余层压到 0.4–0.7
2. 低频最容易被叠爆——它穿透力强，音量要比中频小
3. 高频可以稍大（人耳对高频不敏感），但别超 1.0

### 55.7 限流：叠加的代价

一次击打 3–4 条 `playsound`，10 个人同时打 = 40 次音频事件。**必须限流**。

| 方法         | 做法                     |
| ---------- | ---------------------- |
| **只给最近玩家** | `@p[r=8]` 代替 `@s`      |
| **节流**     | 用 `fx_t` 计数器，2 刻内不重复触发 |
| **分层降级**   | 人多时只播中频那一条             |

```
# 同一玩家 3 刻内不重复播（fx_cd）
execute as @a[scores={fx_cd=0}] run playsound entity.player.attack.strong @s ~ ~ ~ 1.0 1.1
execute as @a[scores={fx_cd=0}] run scoreboard players set @s fx_cd 3
scoreboard players remove @a[scores={fx_cd=1..}] fx_cd 1
```

### 55.8 叠加设计速查

| 想要的感觉  | 叠加方式                                                  |
| ------ | ----------------------------------------------------- |
| **重**  | 加低频（`random.explode` / `note.bass`），音量 0.6，pitch 0.7  |
| **亮**  | 加高频（`random.orb` / `amethyst chime`），音量 0.5，pitch 1.6 |
| **厚**  | 同音效 pitch 0.5 + 1.0 同刻                                |
| **远**  | 延迟 3–5 刻播一条轻的高频                                       |
| **神圣** | `random.totem` + `note.pling` 大三和弦                    |
| **危险** | `note.bass` pitch 0.5 + `random.fizz`                 |
| **成功** | `random.levelup` + 上行音阶                               |
| **失败** | `note.bass` 下行 + `random.fizz`                        |

---

## 56. 环境音

```
playsound ambient.nether_wastes.mood @s ~ ~ ~ 1 1 1
playsound random.door_open @s ~ ~ ~ 1 2 1
```

第三个参数是**最小音量**（`1`），保证远处的玩家也能听到一点，  
不会因为距离衰减完全消失。

**区域氛围**：进入某区域时循环播放，配合 `camera fade` 做沉浸感。

---

## 57. 位置、衰减与限流

### 57.1 播放模式

| 写法                           | 效果                 |
| ---------------------------- | ------------------ |
| `playsound X @s`             | 只在执行者处播，**不受距离影响** |
| `playsound X @a ~ ~ ~`       | 以坐标为中心播，**受距离衰减**  |
| `playsound X @a ~ ~ ~ 1 1 1` | 同上，但最小音量为 1        |

### 57.2 衰减半径

```
衰减半径 ≈ 16 × 音量
```

音量 1 → 16 格内可闻；音量 0.5 → 8 格。

### 57.3 三种限流

| 方法       | 做法                                                       |
| -------- | -------------------------------------------------------- |
| **最近玩家** | `playsound X @p[r=16]` 只给最近的人                            |
| **节流**   | 用 `matches 4..` 每 4 刻才播一次                                |
| **开关**   | `execute unless score @s 静音 matches 1 run playsound ...` |

❗ **别让 20 个人同时响**。20 个人各播一次 = 20 次音频事件，  
客户端会卡。用 `@p` 限流。

---

# 第八部分 · 工程化

---

## 76. 真实音效参数

真实地图的 `playsound` 几乎都带满 6 个参数：

```
playsound <音效> <目标> <坐标> <音量> <音高> <最小音量>
```

| 写法                                               | 效果                          |
| ------------------------------------------------ | --------------------------- |
| `playsound random.orb @s ~~~ 1 1`                | 正常，随距离衰减                    |
| `playsound random.orb @a[r=10] ~~~ 1 0.3`        | 低沉（音高 0.3）                  |
| `playsound random.explode @a ~~~ 100 1 100`      | **全图可闻**（音量 100 + 最小音量 100） |
| `playsound random.explode @a[r=20] ~ ~ ~ 1 10 1` | 音高 10 = 极尖锐的爆裂              |

**`最小音量` 是关键**：不给它，远处的玩家听到的是 0；给了它，多远都是这个响度。  
**爆炸/雷击这类"全场事件"必须写 `100 1 100`。**

### 76.1 用计分板当音效索引

指令区 −10000 用一条 367 块的竖直链当**音效表**：

```mcfunction
execute as @e[scores={sound=1,ss1=1..,zd=1..}] at @s run playsound cauldron.explode @a[r=50] ~~~ 1 2.5
execute as @e[scores={sound=2,ss1=1..}] at @s run playsound tile.piston.out @a[r=20] ~ ~ ~ 1 3 1
execute as @e[scores={sound=3,ss1=1..,zd=1..}] at @s run playsound random.explode @a[r=20] ~ ~ ~ 1 10 1
execute as @e[scores={sound=4,ss1=1..,zd=1..}] at @s run playsound random.explode @a[r=20] ~ ~ ~ 1 5 1
execute as @e[scores={sound=5,ss1=1..,zd=1..}] at @s run playsound mob.ghast.fireball @a[r=20] ~ ~ ~ 1 5 1
execute as @e[scores={sound=1..1145,ss1=1..,zd=1..}] at @s run playsound mob.ravager.step @a[r=5] ~~~ 1 1
```

`sound` 的值决定播哪个音效，`1..1145` 是"所有情况都加一层底噪"。  
**这是"音效表"最朴素的实现**：N 个音效 = N 条命令，一行一条，好改。

---
