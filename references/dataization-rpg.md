# 数据化 RPG：计分板属性 / 伤害 / T显

> 这里的“数据化”指：**用 dummy 计分板把生命、攻击、防御、暴击、等级、经验、装备加成等游戏数据变成可计算、可显示、可复用的数值**。
> 它不是 Mod、不是 NBT，也不是 Java 的 attribute；服务端只认计分板、tag、`hasitem` 和实体选择器。
> 语料来源：`数据化相关指令合集包` 的 99 个文件（数据化一~十五、T显、血条、装备、等级、修仙等）。

## 1. 最小模型

```
基础属性（永久）
   + 装备加成（每 tick 从 hasitem 重建）
   + Buff/职业加成
   = 最终属性（只读缓存）
        ↓
   伤害/治疗事务 → 生命
        ↓
   T显 / 血条 / 死亡 / 经验
```

| 层 | 例子 | 谁写 | 注意 |
|---|---|---|---|
| 基础 | `生命基础` `攻击基础` `防御基础` | 初始化/升级/加点 | 不要每 tick 清零 |
| 装备 | `攻击装备` `防御装备` | `hasitem` 检测 | 每 tick 先清零再重建 |
| Buff | `攻击buff` `防御buff` | 技能/药水 | 有持续时间 |
| 最终 | `攻击` `防御` `生命上限` | 汇总链 | 只读，供伤害/T显 |
| 派生 | `暴击` `闪避` `吸血` | 装备/天赋 | 注意百分比范围 |
| 事务 | `计算` `最终伤害` | 攻击链 | 每次攻击清空 |
| 展示 | `血条` `百分比` `T显` | T显链 | 只读，限频 |

**核心原则**：基础值永久，装备/Buff 每 tick 重建，最终值只读，事务值用完即清。

## 2. 计分板与常量

```mcfunction
scoreboard objectives add 生命 dummy
scoreboard objectives add 最大生命 dummy
scoreboard objectives add 攻击 dummy
scoreboard objectives add 防御 dummy
scoreboard objectives add 暴击 dummy
scoreboard objectives add 暴伤 dummy
scoreboard objectives add 吸血 dummy
scoreboard objectives add 等级 dummy
scoreboard objectives add 经验 dummy
scoreboard objectives add 经验需求 dummy
scoreboard objectives add 计算 dummy
scoreboard objectives add uid dummy

# 常量假玩家：整数运算没有小数，先放大再除
scoreboard players set 百 计算 100
scoreboard players set 十 计算 10
scoreboard players set 二 计算 2
```

- 网易/基岩只有 **dummy**；没有自动生命、自动击杀、自动经验。
- 中文 objective 能用，但新图建议 ASCII（`hp`、`hp_max`、`atk`、`def`、`crit`），命令更好维护。
- `scoreboard players operation` 是**整数除法/截断**；百分比先乘后除。
- 计分板是 32 位有符号整数；大数值要缩小比例或分段。

## 3. 初始化与装备层

```mcfunction
# 玩家首次进入
execute as @a[tag=!初始化] run scoreboard players set @s 生命 1000
execute as @a[tag=!初始化] run scoreboard players set @s 最大生命 1000
execute as @a[tag=!初始化] run scoreboard players set @s 攻击 50
execute as @a[tag=!初始化] run scoreboard players set @s 防御 20
execute as @a[tag=!初始化] run scoreboard players set @s 暴击 5
execute as @a[tag=!初始化] run scoreboard players set @s 暴伤 200
execute as @a[tag=!初始化] run scoreboard players set @s 吸血 5
execute as @a[tag=!初始化] run tag @s add 初始化

# 每 tick 先清空“装备层”
scoreboard players set @a 攻击装备 0
scoreboard players set @a 防御装备 0

# 主手武器
execute as @a[hasitem={item=iron_sword,location=slot.weapon.mainhand}] run scoreboard players add @s 攻击装备 20
execute as @a[hasitem={item=diamond_sword,location=slot.weapon.mainhand}] run scoreboard players add @s 攻击装备 35

# 护甲：注意槽位名字
execute as @a[hasitem={item=iron_helmet,location=slot.armor.head}] run scoreboard players add @s 防御装备 4
execute as @a[hasitem={item=iron_chestplate,location=slot.armor.chest}] run scoreboard players add @s 防御装备 8
execute as @a[hasitem={item=iron_leggings,location=slot.armor.legs}] run scoreboard players add @s 防御装备 6
execute as @a[hasitem={item=iron_boots,location=slot.armor.feet}] run scoreboard players add @s 防御装备 3

# 汇总最终值
execute as @a run scoreboard players operation @s 攻击 = @s 攻击基础
execute as @a run scoreboard players operation @s 攻击 += @s 攻击装备
execute as @a run scoreboard players operation @s 防御 = @s 防御基础
execute as @a run scoreboard players operation @s 防御 += @s 防御装备
```

- **槽位**：`slot.armor.head` / `slot.armor.chest` / `slot.armor.legs` / `slot.armor.feet`。样本里常把胸甲写成 `slot.armor.legs`，这是错的，照抄会漏防御。
- `hasitem={item=...,quantity=0}` 在样本中表示“有该物品”（0 作为任意数量/存在性）；要精确数量用 `quantity=1..`。
- `hasitem` 每个实体每 tick 扫描背包，实体多时很贵；可 5~20 tick 重建一次，或只在装备变化时重建。
- 不要把 `攻击最终` 又写回 `攻击基础`，否则装备会越叠越高。

## 4. 伤害事务（现代 execute 版）

样本多用旧 `execute @a ~ ~ ~`；下面是 1.21.130 可用的新语法骨架。

```mcfunction
# 1) 攻击触发：这里用 tag 代表“本 tick 挥击”（实际可用钓鱼钩/冷却/技能触发）
tag @e[tag=生物,tag=!玩家] remove 被攻击
execute as @a[tag=攻击] at @s run tag @e[tag=生物,c=1,r=6,tag=!攻击] add 被攻击

# 2) 目标防御：先标记再计算，避免 c=1 在目标死亡后漂移
execute as @a[tag=攻击] run scoreboard players operation @s 计算 = @s 攻击
execute as @a[tag=攻击] run scoreboard players operation @s 计算 -= @e[tag=被攻击] 防御

# 3) 最低伤害 1
execute as @a[tag=攻击,scores={计算=..0}] run scoreboard players set @s 计算 1

# 4) 暴击：random 1..100 <= 暴击率
# 注意：假玩家“暴击”是全局随机；多人同 tick 会共用同一个随机值。
# 要每玩家独立，改成：execute as @a[tag=攻击] run scoreboard players random @s 随机 1 100
scoreboard players random 暴击 计算 1 100
execute as @a[tag=攻击] run scoreboard players operation 暴击 计算 -= @s 暴击
execute as @a[tag=攻击] if score 暴击 计算 matches ..0 run scoreboard players operation @s 计算 *= 二 计算

# 5) 浮动 75%~125%
scoreboard players random 浮动 计算 75 125
execute as @a[tag=攻击] run scoreboard players operation @s 计算 *= 浮动 计算
execute as @a[tag=攻击] run scoreboard players operation @s 计算 /= 百 计算

# 6) 吸血
execute as @a[tag=攻击] run scoreboard players operation @s 吸计算 = @s 吸血
execute as @a[tag=攻击] run scoreboard players operation @s 吸计算 *= @s 计算
execute as @a[tag=攻击] run scoreboard players operation @s 吸计算 /= 百 计算
execute as @a[tag=攻击] run scoreboard players operation @s 生命 += @s 吸计算

# 7) 扣目标生命
execute as @e[tag=被攻击] run scoreboard players operation @s 生命 -= @e[tag=攻击] 计算

# 8) 目标死亡 / 经验
execute as @e[tag=被攻击,scores={生命=..0}] run scoreboard players set @s 生命 0
execute as @a[tag=攻击] run scoreboard players operation @s 经验 += @e[tag=被攻击] 经验
execute as @e[tag=被攻击,scores={生命=..0}] run kill @s

# 9) 清理事务 tag（必须）
tag @e[tag=被攻击] remove 被攻击
tag @a[tag=攻击] remove 攻击
```

### 关键点

- **先标记再计算**：`tag @e[...] add 被攻击` 一次，后续都读 `@e[tag=被攻击]`，不要每一步重新 `c=1`。
- **最低伤害 1**：防御高于攻击时仍扣 1，否则永远打不死。
- **暴击/浮动/吸血顺序**：先防御，再暴击，再浮动，最后吸血；顺序不同结果不同。
- **整数百分比**：`计算 *= 暴击率; /= 100`，不要直接 `*= 0.5`。
- **多个攻击者**：`tag=被攻击` 是全局的，两只玩家同时攻击会串；高并发用 `被攻击_<uid>` 或每 tick 只处理一个攻击者。
- **一击只结算一次**：触发 tag 在链尾统一移除；不要在中间移除，否则后续读不到。
- **`kill` 只对生命 <=0 的目标**；先设 0，再 kill，再重置生命，避免重复经验。
- **不要混用 vanilla 生命**：数据化生命是计分板；vanilla 血量用抗性/隐身保护，或用 `/hud` 隐藏，避免两套血条打架。

## 5. 目标、UID 与击杀归属

### UID 分配（每玩家唯一）

```mcfunction
scoreboard players add @a uid 0
execute as @r[scores={uid=0}] run scoreboard players operation @s uid = 计算 uid
scoreboard players add 计算 uid 1
```

- `@r[scores={uid=0}]` 每 tick 只给一个未分配玩家；`计算 uid` 是全局自增。
- 给怪物也分配 uid：`scoreboard players add @e[tag=生物] uid 0`，或初始化时写入。
- 击杀归属：攻击时把攻击者 uid 写到目标 `killer`，死亡时只给 `uid` 相同的玩家经验；样本 `数据化四` 用这个。
- 不要用玩家名做唯一键；改名/重进会出问题。

### 目标标记

```mcfunction
tag @e[tag=目标a] add 目标
tag @e[tag=目标a] remove 目标a
tag @e[tag=目标] remove 目标
```

- 三步：旧目标转正、清临时标记、清最终标记；具体按你的链顺序调整。
- 目标实体过滤要排除掉落物/箭/船/盔甲架/火焰球等，样本 `数据化四` 有一长串 `type=!...`；新图建议用 `tag=生物` 白名单而不是黑名单。

## 6. T显 / 血条 / HUD

### 基础 T显

```mcfunction
execute as @a run titleraw @s actionbar {"rawtext":[
  {"text":"§cHP "},
  {"score":{"name":"@s","objective":"生命"}},
  {"text":"§7/"},
  {"score":{"name":"@s","objective":"最大生命"}},
  {"text":"  §eATK "},
  {"score":{"name":"@s","objective":"攻击"}}
]}
```

- `titleraw` 的 JSON 可以很长；**普通 `title` 的纯文本参数约 512 字节会静默失败**，大面板用 `titleraw`。
- 每 tick 发 actionbar 会刷屏/吃带宽；T显用 `repeat delay 4~10`（5~10 Hz），事件提示才用 `title`。
- 只在需要时显示：样本用 `rxm=88`（低头）触发个人面板；或 `hasitem` 手持“面板书”切换。
- 大标题 `title @s title` 只用于升级/击杀等事件；菜单类不要每次交互都弹大标题。

### 百分比血条

```mcfunction
scoreboard players set 百 计算 100
execute as @a run scoreboard players operation @s 百分比 = @s 生命
execute as @a run scoreboard players operation @s 百分比 *= 百 计算
execute as @a run scoreboard players operation @s 百分比 /= @s 最大生命
execute as @a[scores={百分比=101..}] run scoreboard players set @s 百分比 100
execute as @a[scores={百分比=..-1}] run scoreboard players set @s 百分比 0
```

- 10 格血条：用 10 个条件分支/`translate` 选不同字符串。
- 100 格血条：先算 0..100，再用 `translate`/11 个 objective 选段；样本 `百格血条.txt`、`数据化十五` 有完整写法。
- `titleraw` 的多分支常用：

```json
{"translate":"%%2","with":{"rawtext":[
  {"selector":"@s[scores={hp=1..}]"},
  {"text":"§a"}
]}}
```

这是样本里的“选择器 + 文本”二选一模板；不同版本行为可能有差异，先在目标版本实测。

### 侧边栏/头顶血条（不用 titleraw）

样本 `血条.txt` 用 11 个 objective（`hp0`~`hp10`）预置 ❤ 字符串，然后：

```mcfunction
scoreboard objectives setdisplay belowname hp0
scoreboard objectives setdisplay list hp0
```

- `belowname` 在玩家头顶显示；`list` 在 Tab 列表显示。
- 优点：不需要每 tick 发 titleraw；缺点：占 objective、只能显示固定字符、多人/怪物不灵活。
- 适合玩家血条；怪物头顶血条还是 `titleraw` + `@e` 更灵活。

### 隐藏原版 HUD

```mcfunction
hud @a hide health
hud @a hide hunger
hud @a hide armor
hud @a hide status_effects
hud @a hide item_text
```

- `/hud <target> <hide|reset> [element]`；元素还有 `hotbar`、`crosshair`、`paperdoll`、`air_bubbles`、`horse_health`、`progress_bar`、`tooltips`、`touch_controls`、`all`。
- **网易边界**：`hud` 在 Bedrock 1.21 稳定版有文档，但**不在网易官方命令列表**；`数据化四` 使用了它。先在网易 `/help hud` 验证；不支持就不要把原版血条藏掉，改用资源包/布局避让。
- 隐藏后必须有恢复路径（重生/退出/关闭面板时 `hud @s reset health`），否则玩家看不到原版血量。

## 7. 等级 / 经验

```mcfunction
# 需求：100 + 等级*10（可换成你自己的曲线）
execute as @a[scores={等级=..0}] run scoreboard players set @s 经验需求 100
execute as @a run scoreboard players operation @s 经验需求 = @s 等级
execute as @a run scoreboard players operation @s 经验需求 *= 十 计算
execute as @a run scoreboard players add @s 经验需求 100

# 升级：一次只升一级，tag 防重复
execute as @a if score @s 经验 >= @s 经验需求 run tag @s add 升级
execute as @a[tag=升级] run scoreboard players add @s 等级 1
execute as @a[tag=升级] run scoreboard players operation @s 经验 -= @s 经验需求
execute as @a[tag=升级] run scoreboard players add @s 天赋点 5
execute as @a[tag=升级] run playsound random.levelup @s
tag @a[tag=升级] remove 升级
```

- 用 `execute if score ...`，不要用旧 `scoreboard players test`。
- 一次只升一级；大经验包用循环/多 tick，不要 `while` 硬跑。
- 经验需求要单调递增；否则会卡级/刷级。
- 击杀经验用目标 `经验` 字段；先结算再 `kill`。

## 8. 装备 / 自定义物品

### 装备槽位与展示

- 样本 `数据化装备穿戴系统` 用盔甲架 + 二进制定位（1/2/4/8/16/32/63）做装备槽 UI；思路是“用盔甲架当槽位标记，`tp` 到对应格子”。
- 简单方案：直接用 `hasitem` 读 `slot.armor.*` / `slot.weapon.mainhand`，不需要盔甲架。
- 装备属性层每 tick 重建（见第 3 节），不要直接改基础值。

### 锁定物品 / 死亡保留

```mcfunction
replaceitem entity @s slot.weapon.mainhand 0 keep iron_sword 1 0 {"minecraft:item_lock":{"mode":"lock_in_slot"},"minecraft:keep_on_death":{}}
```

- 样本里的 `keep`/`destroy` 是网易/旧版扩展写法；国际版标准 `replaceitem` 没有这个位置参数，跨版本要改。
- `item_lock` 防止移动/丢弃；`keep_on_death` 死亡保留。
- 锁物品要提供“解锁/卸下”路径，否则玩家背包被卡死。

### 随机词条装备

- 用 `uid`/`装备ID` 记录装备，用 scoreboard 存词条数值，T显时拼出来。
- 不要把词条写进物品 NBT（基岩读不到）；用“物品 + 计分板”绑定。
- 样本 `随机词条装备二代` 分生成/回收/强化/套装/ID/T显五部分；核心是“物品只是外观，数值在计分板”。

## 9. 数据化怪物

```mcfunction
# 白名单：只给真正的生物打 tag
tag @e[type=!player,type=!armor_stand,type=!item,type=!arrow,type=!boat,type=!fishing_hook] add 生物

# 按等级初始化
execute as @e[tag=生物,tag=!初始化] run scoreboard players set @s 等级 1
execute as @e[tag=生物,tag=!初始化] run scoreboard players operation @s 最大生命 = @s 等级
execute as @e[tag=生物,tag=!初始化] run scoreboard players operation @s 最大生命 *= 百 计算
execute as @e[tag=生物,tag=!初始化] run scoreboard players operation @s 生命 = @s 最大生命
execute as @e[tag=生物,tag=!初始化] run scoreboard players operation @s 攻击 = @s 等级
execute as @e[tag=生物,tag=!初始化] run scoreboard players operation @s 攻击 *= 十 计算
execute as @e[tag=生物,tag=!初始化] run tag @s add 初始化

# 防 vanilla 死亡/燃烧
effect @e[tag=生物] resistance 5 255 true
effect @e[tag=生物,type=!player] fire_resistance 5 255 true
```

- 样本用超长 `type=!...` 黑名单；新图用 **`tag=生物` 白名单**，由刷怪/生成链打 tag，避免把箭/船/掉落物算进去。
- 怪物血条/等级/攻击可以按等级缩放；注意 `最大生命` 不要超过 32 位/显示上限。
- 死亡时给击杀者经验、掉落、清理 tag；`kill` 后实体消失，tag 自动没了，但计分板数据可能残留，必要时 `scoreboard players reset @e[...]`。

## 10. 性能与架构

- **一个 repeat 头 + 一条 chain**；不要每个功能一个 repeat 头，20 Hz 会爆。
- 攻击事务每 tick 一次；T显 5~10 Hz；血条 2~5 Hz；经验/回血 1 Hz。
- 选择器从窄到宽：`tag=生物` + `r` + `c=1`；避免 `@e` 全图扫描。
- 每个事务结束清 tag；否则下一 tick 重复结算。
- 实体多时 `hasitem`/`@e` 很贵；装备层可 5 tick 重建一次。
- `titleraw` 大 JSON 只给需要的玩家（`rxm`、`hasitem`、`tag`），不要 `@a` 每 tick 发。
- 计分板整数：先乘后除、及时 clamp、避免溢出；百分比用 100/1000 放大。
- 把大链拆成多个独立命令方块链；单条链不要塞 200 条。

## 11. 旧语法 → 新语法（样本地图重灾区）

| 样本旧写法 | 1.21.130 新写法 |
|---|---|
| `execute @a ~ ~ ~ cmd` | `execute as @a at @s run cmd` |
| `execute @a[scores={x=1..}] ~ ~ ~ cmd` | `execute as @a[scores={x=1..}] at @s run cmd` |
| `execute @e[tag=目标] ~ ~ ~ cmd` | `execute as @e[tag=目标] at @s run cmd` |
| `scoreboard players test @s obj 1 5` | `execute if score @s obj matches 1..5` |
| `scoreboard players test @s obj * 0` | `execute if score @s obj matches ..0` |
| `execute @a ~ ~ ~ scoreboard players operation ...` | `execute as @a run scoreboard players operation ...` |
| `@p[r=3]` | 仍可用；跨维度/多人要加 `c=1` 并确认最近目标 |
| `replaceitem ... keep ...` | 网易样本扩展；国际版改标准 `replaceitem`/`clear`+`give` |
| `hud @a hide health` | Bedrock 1.21 有；**网易先 `/help hud` 验证** |
| `scoreboard players operation ... tick 10` | 不是标准参数；用命令方块 delay/`schedule`/计分板倒计时 |

> 样本里还有 `execute @a[c=1]`、`@e[c=1]` 等旧写法；新图统一 `as/at`，并明确“谁执行、以谁的位置”。

## 12. 样本地图

| 文件 | 学什么 |
|---|---|
| `数据化一.txt` | 最小攻击/防御/生命/受击/T显；旧语法 |
| `数据化二/三/五/七` | 属性、装备、暴击、闪避、攻速、特效；13 个 objective |
| `数据化四.txt` | UID、HUD 隐藏、等级/经验、远程、击杀归属；175 步 |
| `数据化六[新语法].txt` | 新 execute 的攻击/受击/技能/死亡/等级/初始化分段 |
| `数据化八/十三` | 小麦版，GBK 编码；职业/技能/阶段 |
| `数据化十(新execute).docx` | 生命/回血/T显/怪物初始化，新语法 |
| `数据化十一.txt` | UID、`damage` 命令的 512/256/… 二进制分段 |
| `数据化十四(主体部分系统).txt` | 多职业（剑/斧/法）、攻速、暴击、T显、怪物属性 |
| `数据化十五.docx` | 生命/攻击/防御/暴击/吸血/经验/血条的完整主链 |
| `数据化cps_幻沐制作.docx` | CPS 显示：盔甲架计时 + 计分板 + T显 |
| `数据化装备穿戴系统.docx` | 盔甲架装备槽、二进制定位 |
| `血条.txt` / `百格血条.txt` | 头顶/Tab 血条、百分比、10/100 格 |
| `T显4.0/6.0` / `好几种T显示信息` / `修仙菜单T显示` | 多行 actionbar、条件颜色、`translate` 分支 |
| `二分法显示经验指令文档.doc` | 二分法/分段显示经验 |
| `随机词条装备二代` | 词条生成/回收/强化/套装/ID/T显 |
| `攻击源检测` / `弓箭数据化` | 近战/远程命中判定与误判 |
| `体力系统` / `等级系统` / `技能` | RPG 子系统拆分 |

## 13. 检查清单

- [ ] 所有 objective 都是 `dummy`，常量假玩家已设置。
- [ ] 基础/装备/Buff/最终四层分开；装备层每 tick 先清零。
- [ ] 攻击目标先 tag 再计算，事务结束清 tag。
- [ ] 防御后最低伤害 1；生命 clamp 到 0..最大生命。
- [ ] 暴击/浮动/吸血顺序明确，百分比先乘后除。
- [ ] 死亡只结算一次经验；击杀归属用 uid，不用玩家名。
- [ ] T显限频、按需显示；没有每次交互弹大标题。
- [ ] `hud` 在目标版本 `/help` 验证；隐藏后有恢复。
- [ ] 旧 `execute @a ~ ~ ~` 已升级为 `as/at`。
- [ ] 实体过滤用 `tag=生物` 白名单，不把箭/船/掉落物算进去。
- [ ] 性能：repeat 头数量、`@e` 范围、`hasitem` 频率、T显频率都测过。

## 14. 来源

- 用户提供的 `数据化相关指令合集包`（数据化一~十五、T显、血条、装备、等级、修仙等 99 个文件）。
- [Minecraft Wiki: Scoreboard](https://minecraft.wiki/w/Scoreboard)（dummy、operation、display slot）。
- [Microsoft Learn: `/hud`](https://learn.microsoft.com/en-us/minecraft/creator/commands/commands/hud?view=minecraft-bedrock-stable)（HUD 元素/可见性）。
- [Bedrock Wiki: Rawtext](https://wiki.bedrock.dev/commands/rawtext.html)（`titleraw`/`translate`/`with`）。
