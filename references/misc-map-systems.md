# 杂项地图系统：菜单 / 商店 / 开箱 / 反作弊 / 小游戏

> 这批语料不是单一系统，而是服务器地图里反复出现的“杂项”套路：
> 菜单选人、免举商店、纸条/矿物开箱、反穿墙/防矿透、工会领地、匹配选队、密室杀手、拔刀剑、死亡动画、公告栏等。
> 重点不是照抄，而是抽出可复用的**触发器、计分板事务、UI 和防误判**。

## 1. 菜单与选人（最常用）

### 1.1 触发器：鸡蛋 / 雪球 / 纸 / 钓鱼钩

```mcfunction
# 只给有权限的玩家发“菜单触发器”，并锁住快捷栏
replaceitem entity @a[tag=管理] slot.hotbar 0 destroy egg 16 0 {"minecraft:item_lock":{"mode":"lock_in_slot"}}

# 鸡蛋落地/命中时，给附近玩家开菜单
execute at @e[type=egg] run scoreboard players add @p[tag=管理,r=2] 管理菜单 1
execute at @e[type=egg] run playsound random.orb @p[tag=管理,r=2]
execute as @a[scores={管理菜单=1..}] run kill @e[type=egg,c=1,r=3]
```

- 鸡蛋/雪球是“无 UI 按钮”：投掷物事件 + `@p[r=2]` 找投掷者附近玩家。
- 触发器物品要 `item_lock`，否则玩家可以丢掉/换槽。
- 投掷物要 `kill` 清理，否则越积越多。
- 权限用 `tag` 最省事，但 **tag 不是安全边界**：能执行 `/tag` 的玩家可以自己加。正式服用 `haspermission`/OP/菜单物品白名单。

### 1.2 分数即页面

```mcfunction
# 1..5 = 主菜单项；6 = 关闭；51..57 = 子页面
execute as @a[scores={管理菜单=1..6}] at @s run titleraw @s actionbar {"rawtext":[...]}

# 低头关闭
execute as @a[scores={管理菜单=!0},rxm=88] run scoreboard players set @s 管理菜单 0
# 抬头确认
execute as @a[scores={管理菜单=1..5},rx=-88] run ...
```

- 页面/选项/确认全部塞进 **一个整数 objective**，用区间分支；比每个页面一个 tag 好维护。
- `rxm=88`（低头）关闭、`rx=-88`（抬头）确认，是网易菜单最常见的交互。
- 用 `titleraw actionbar`，不要每次交互弹 `title @s title` 大标题。
- 选项高亮用 `translate %%2` + 选择器列表；具体行为先实测。

### 1.3 选人：`选人` 分数映射

```mcfunction
execute if entity @p[scores={选人=-1}] at @r run scoreboard players operation @a 选人 -= @a 选人
scoreboard players add @a 选人 1

execute if entity @a[scores={菜单=57},rx=-85] run scoreboard players set @a 选人 -1
execute as @a[scores={菜单=52..56},rx=-88] run scoreboard players operation @a 选人 -= @a[scores={菜单=52..56},rx=-88] 菜单
execute as @a[scores={选人=0}] run tag @a[scores={选人=0}] add 选中
scoreboard players set @a[scores={选人=0}] 选人 -1
```

- `选人` 从 -1 开始，每 tick +1；菜单项 52..56 映射到 0..4；0 就是被选中的玩家。
- `@r` 重置、`tag=选中` 标记、`选人=-1` 防重复。
- 多玩家同 tick 选人可能撞分；高并发用 UID 或每 tick 只处理一个管理员。
- 样本 `8CB选人菜单` 用 `雪球菜单=201..206` 做页面，`选人` 做玩家序号；适配雪球菜单时只改页面号。

### 1.4 公告栏：用 sidebar 假玩家当“行”

```mcfunction
scoreboard objectives remove 公告栏
scoreboard objectives add 公告栏 dummy "<◁｛ §b公告栏§f ｝▷>"
scoreboard objectives setdisplay sidebar 公告栏 ascending

scoreboard players set "    ▶一一一一一一一一◀" 公告栏 -5
scoreboard players set "    丨 服主 : XXX" 公告栏 -4
scoreboard players set "    ▶一一一一一一一一◀ " 公告栏 -1
scoreboard players set "    ▶一一一一一一一一◀  " 公告栏 999
```

- **行名 = 假玩家名**，行值 = 排序；`ascending` 让 -5 在上、999 在下。
- 动态数字要改“行名”本身（如 `" | 在线人数 §a１§f/１０"`），所以每 100~200 tick **remove + add** objective 清掉旧行；会有轻微闪烁。
- 比每 tick `titleraw @a` 省性能，适合全服公告；不适合每玩家不同内容。
- 人数/掉落物/实体数用 `execute as @a` / `execute as @e` 累加假玩家，再分支设置行名。

## 2. 商店与经济

### 2.1 免举商店：木桶 + clone + item 传送

```mcfunction
# 前台：按钮下是磁石，读价格
execute as @p[r=2] at @s if block ~~-1~ lodestone run scoreboard players set @p 价格 <数值>

# 后台：钱够就复制木桶，清掉原木桶，把物品 tp 给玩家
execute as @a[scores={价格=1..}] at @s run execute if score @s 金币 >= @s 价格 run clone ~~-2~ ~~-2~ ~~1~
execute as @a[scores={价格=1..}] at @s run execute if score @s 金币 >= @s 价格 run setblock ~~1~ air destroy
execute as @a[scores={价格=1..}] at @s run execute if score @s 金币 >= @s 价格 run scoreboard players operation @s 金币 -= @s 价格
execute as @a[scores={价格=1..}] at @s run execute if score @s 金币 >= @s 价格 run tp @e[type=item,r=2,c=1] @s
scoreboard players set @a[scores={价格=1..}] 价格 0
```

- “免举”= 不用手上举货币物品，直接读计分板金币。
- 商品源是**木桶**：桶里放物品；`clone` 复制到输出位，`setblock ... air destroy` 让物品掉落，再 `tp` 给玩家。
- `@e[type=item,r=2,c=1]` 只拿一个；多物品用 `c=N` 或循环。
- 失败分支：金币不足/价格为 0 要给提示并清 `价格`，否则会反复触发。
- **多人同时买**会抢同一个输出位的物品；V1 暗区样本明确写了这个 bug。正式服要按玩家分配输出坐标，或串行化购买。

### 2.2 批量购买

```mcfunction
# 菜单 1..9 选个位/十位，10 确认，11 清零，12 购买，13 退出
execute as @a[scores={菜单=1..11,菜单=!10},rx=-88] run scoreboard players operation @s 金额 *= 十 金额
execute as @a[scores={菜单=1..9},rx=-88] run scoreboard players operation @s 金额 += @s 菜单
execute as @a[scores={菜单=10},rx=-88] run scoreboard players operation @s 金额 /= 十 金额
execute as @a[scores={菜单=1..10}] run scoreboard players operation @s 数量 = @s 金额
execute as @a[scores={菜单=1..10}] run scoreboard players operation @s 总价 = @s 数量
execute as @a[scores={菜单=1..10}] run scoreboard players operation @s 总价 *= @s 价格
```

- 用“数字键盘”式分数拼数量：每位乘 10 再加；确认时除 10 修正。
- 先算总价再扣钱；扣钱前检查 `总价 <= 金币`。
- 大数量分批 `clone`/`tp`，不要一次生成上千掉落物。

### 2.3 二次确认 / 折扣

```mcfunction
execute as @a[tag=!已查询,tag=!购买,scores={价格=1..}] at @s run tellraw @s ...
tag @a[scores={价格=1..},tag=!已查询] add 已查询
tag @a[tag=已查询] add 购买

execute as @a[scores={价格=1..}] run scoreboard players operation @s 优惠价格 = @s 价格
execute as @a[scores={价格=1..}] run scoreboard players operation @s 优惠价格 *= @s 折扣
execute as @a[scores={价格=1..}] run scoreboard players operation @s 优惠价格 /= 百 折扣
```

- 第一次点=查询，第二次点=购买；`已查询`/`购买` 两个 tag。
- 离开磁石/按钮范围要清 tag，否则下次直接购买。
- 折扣用 100 基准：80=8 折，88=88 折；先乘后除。
- 样本里 `差价` objective 没在开头创建，是常见漏写；交付前跑一遍 objective 清单。

### 2.4 金币变动提示

```mcfunction
# 金币处理 = 本次变化量（正=加钱，负=扣钱）
execute as @a unless score @s 金币 = @s 金币计算 run scoreboard players operation @s 金币处理 = @s 金币
execute as @a unless score @s 金币 = @s 金币计算 run scoreboard players operation @s 金币处理 -= @s 金币计算
execute as @a unless score @s 金币 = @s 金币计算 run tellraw @s {"rawtext":[{"text":"金币变动 "},{"score":{"name":"@s","objective":"金币处理"}}]}
execute as @a run scoreboard players operation @s 金币计算 = @s 金币
```

- 用“影子分数”比较余额变化，避免每笔交易都写提示。
- 上面是最小正确版：`金币处理 = 当前金币 - 上次金币`；提示后用 `金币计算 = 金币` 更新影子。
- 样本 `金币后处理` 用 `负` 分数取反、逻辑更绕；照抄容易把正负号弄反，建议用上面的差值版。
- 多个经济系统同时写金币时，影子分数要统一，否则提示会重复/漏。

### 2.5 彩票

- 购买：金额→倍率→随机 4 位号码；开奖：倒计时到 0 随机开奖号；逐位匹配，中奖位数 1/2/3/4 对应不同奖池；`最终中奖金额 = 中奖金额 * 最终倍率`。
- 关键：期号 `彩票期数` 必须匹配，避免上一期票领本期奖；未匹配的票要 `reset` 号码。
- `scoreboard players random` 是**闭区间**；样本开奖号用 1..9，购买号用 0..9，注意 0 的概率差。
- 下线玩家会丢票；要持久化就得把号码/倍率存到外部（行为包/数据库），纯计分板做不到跨会话。
- 经济风险：倍率、奖池、四位数匹配概率要算清楚；先做上限/审计。

## 3. 开箱 / 摸索

### 3.1 纸条/矿物开箱：进度 + clone + tp

```mcfunction
execute as @a[hasitem={item=paper,location=slot.weapon.mainhand}] at @s run scoreboard players add @s 摸索 1
execute as @a[scores={摸索=10..}] at @s run scoreboard players random @s 物品 1 100
execute as @a[scores={物品=1..10}] run clone ~~1~ ~~1~ <输出坐标>
setblock <输出坐标> air destroy
execute positioned <输出坐标> run tp @e[name=!木桶,r=2,type=item,c=1] @p[scores={物品=1..}]
/clear @a[scores={摸索=10..}] paper 0 1
scoreboard players set @a[scores={摸索=10..}] 摸索 0
```

- 进度条：手持纸/站在矿物块上，每 5~10 tick +1；松手/离开就中断清零。
- 概率：`random 1..100` 映射到 10/20/30/40 四档；四档和必须 100。
- 输出：木桶里放战利品，`clone` 到统一输出位，`setblock air destroy` 掉物品，`tp` 给玩家。
- 多玩家同时开箱会拿错物品；样本 V1 明确写了。正式服按玩家分配输出坐标/结构，或一次只处理一个玩家。

### 3.2 视角/结构开箱

```mcfunction
execute as @a at @s anchored eyes positioned ^^^1 if block ~~~ beehive if block ~~1~ light_blue_carpet run scoreboard players add @s 开箱 3
execute at @a[scores={开箱=100..}] anchored eyes positioned ^^^1 run structure load 开启箱子 ~~~
execute at @a[scores={箱子种类=1..,开箱=100..}] anchored eyes positioned ^^^1 run structure load 刷新箱子 ~~~ 0_degrees none block_by_block <秒>
```

- 用 `anchored eyes positioned ^^^1` 检查**视线前方**的蜂箱/地毯；适合“看着箱子开”。
- `structure load` 可带旋转/动画参数；网易版本先用小结构测试。
- 结构刷新有延迟时，用 `setblock`/`clone` 重置；别让多个玩家共用同一个结构输出位。

### 3.3 分级鉴宝（V3）

- 纸的 `data=1..4` 表示等级；`珍宝等级`；`最大时间` 100/80/50/30；`鉴定时间` 递增；达到最大时间后按等级 `random` 不同区间，再 `clone` 对应战利品。
- 等级/概率/最大时间要三处同步改；样本提醒“很麻烦”。
- `clear @s paper <data> 1` 要带 data，否则清错等级。
- 适合地铁/暗区；要有“中断/退出”路径，否则纸被卡在手里。

## 4. 保护与反作弊

### 4.1 反穿墙（XP 球探针）

```mcfunction
execute as @r at @s run summon xp_orb ~~0.5~ ~~ abort_sheltering
execute as @e[type=xp_orb] at @s run tp ~~0.01~ true
execute as @e[type=xp_orb] at @s run execute as @p[r=1.5] at @s run scoreboard players add @s VL 1
execute as @e[type=xp_orb] at @s run kill @e[r=1.5,type=!item]
```

- 用经验球的碰撞/穿透特性做“穿墙探针”；命中附近玩家就加 `VL`。
- 已知误判：楼梯/台阶（小）、栅栏拐角（大）。**只当嫌疑分，不要自动永封**。
- 样本的惩罚是 `kill`，正式服应改成人工审核/传送/记录。

### 4.2 防矿透

```mcfunction
# 追踪自然矿物物品的存在时间
testfor @e[type=item,name=钻石,rym=0,ry=0]
scoreboard players add @e[type=item,name=钻石,ry=0,rym=0] 矿物生成时间 1
execute at @e[type=item,name=钻石,scores={矿物生成时间=1}] run scoreboard players add @p[r=10] 矿物处理 1
scoreboard players add 钻石 矿物计时 1
scoreboard players reset 钻石 矿物计时

# 转成玩家分数，定时衰减，阈值警告/标记
scoreboard players add @a[scores={矿物处理=1..}] 玩家矿物分数 1
scoreboard players reset @a 矿物处理
scoreboard players add @a 玩家矿物分数 -1   # 每 45s 一次
execute as @a[scores={玩家矿物分数=21..}] at @s run titleraw @a[tag=审核权限] actionbar ...
tag @a[scores={玩家矿物分数=31..}] add 矿透
```

- 原理：自然生成的矿物物品“年龄” + 附近玩家加分；短时间大量矿 = 可疑。
- 普通玩家挖矿也会加分；阈值/衰减要按服务器经济调。
- 样本有审核员模式（旁观 + 经验瓶）、白名单 `矿物白名单`；惩罚需自己加。
- 隐私/误封风险高：只做“嫌疑 + 人工审核”，不要直接自动封禁。

### 4.3 工会 / 领地

```mcfunction
# 会长站基岩上抬头，绑定 NPC 的领地编号
execute as @e[type=npc,name=...领地中心...] at @s run execute as @a[r=3,tag=会长,scores={领地=0},rx=-88] at @s if block ~~-1~ bedrock run scoreboard players operation @s 领地 = 领地数量 领地

# 非本工会玩家靠近领地中心，推开
execute as @e[type=npc,scores={领地=1..},tag=!关闭] at @s run execute as @a[r=150,scores={领地数据=!0}] at @s run tp @s ^^^-5
```

- 领地“中心”是 NPC + 基岩；`领地` 编号绑定；`领地数据 = 玩家领地 - NPC领地`，0 表示自己的。
- 保护只是把非成员推开/提示，不是真正的方块保护；要真保护得配合 `fill` 回滚/`structure`/行为包。
- 工会邀请用 `邀请计时` + `选择类型` + `选人`；会长/成员离线要中断，样本有专门链。
- 范围 300×300 是硬编码；大范围 `r=150` 选择器很贵，建议分区/边界盒。

### 4.4 卡密门

```mcfunction
execute as @a[tag=破译] run scoreboard players add @s 破译进度 1
execute as @a[tag=破译] at @s unless block ^^1^ iron_door run scoreboard players set @s 破译进度 0
execute as @a[scores={破译进度=100..,卡门=1}] ... tp 黑门内坐标
/clear @a[scores={破译进度=100..,卡门=1}] black_candle 0 1
```

- 颜色羊毛 + 铁门 + 同色蜡烛当钥匙；`卡门` 1..5 区分门；`破译进度` 到 100 传送并清钥匙。
- `^^1^` 是**本地坐标**（玩家朝向），检查面前的门；玩家转身会失败，这是预期。
- 多个门要各自独立 objective/tag；样本明确警告“不能两个黑卡门”。
- 钥匙 `clear` 带 data，避免清错颜色。

### 4.5 封禁 / 协管菜单

```mcfunction
# 管理员鸡蛋开菜单；选中玩家用 选人/数据检测 映射
execute as @a[tag=!op] at @s if score @s 数据检测 = 选人 数据检测 run kick @s §c您已被踢出游戏
```

- 基岩没有持久 `/ban`；样本“封禁”实际是 `kick` + tag/分数黑名单，重进还能进。
- 真要封禁：维护 `封禁名单`（行为包/外部服务），玩家进服时比对 XUID/名字再 `kick`。
- 权限用 tag 只是示意；正式服必须用 OP/`haspermission`/菜单物品，不能让玩家自己 `/tag`。
- 选人映射用 `数据检测`；多人同分可能踢错，建议 UID。

## 5. 小游戏 / 匹配

### 5.1 匹配区 + 倒计时

```mcfunction
scoreboard players set 匹配人数 匹配区 0
execute as @a[x=,y=,z=,dx=,dy=,dz=] run scoreboard players add 匹配人数 匹配区 1
execute unless score 匹配人数 匹配区 matches 2.. run scoreboard players set 匹配倒计时 匹配区 30
execute if score 匹配人数 匹配区 matches 2.. run scoreboard players remove 匹配倒计时 匹配区 1
```

- 用 `x/y/z/dx/dy/dz` 框匹配区；**样本用 `@e` 会把非玩家算进去**，正式服改 `@a`/`type=player`。
- 人数不足重置倒计时；到 0 标题/音效/传送。
- 选队：`最低人数 = 匹配人数 / 4`；红/蓝/黄/绿人数不足就补一个；全满后随机/重排；`队伍` 0..4。
- 整数除法会丢余数；4 队不整除时要处理落单玩家。

### 5.2 密室杀手

- 角色：1 杀手、2 侦探、3 平民；匹配人数→`@r` 分配；开局 `title` 身份；T显剩余人数。
- 平民 10 绿宝石换一次性弓；侦探有限弓箭冷却；杀手近战秒人。
- 友伤/误杀逻辑靠 tag+距离+“触发检测”，样本明确说“没办法检测弓箭射出者与射中者”，会有误判。
- 胜负：杀手全灭→好人胜；好人全灭/时间到→杀手胜；奖励金币。
- 这类社交推理图最难的是**死亡检测/观战/离场**；先做最小闭环，再补误杀规则。

### 5.3 固定点随机传送

```mcfunction
scoreboard players random @p 随机传送 1 3
tp @a[scores={随机传送=1}] 坐标1
tp @a[scores={随机传送=2}] 坐标2
tp @a[scores={随机传送=3}] 坐标3
scoreboard players reset @a[scores={随机传送=1..}] 随机传送
title @a[scores={随机传送=1..}] actionbar §f[§a✔§f] 传送成功
```

- 随机 1..N 映射到固定坐标；适合大厅/随机出生点。
- 加 `r`/`rm` 限定触发区域，避免全图玩家被传。
- 传送后重置分数，防止重复触发。

### 5.4 地毯撤离

```mcfunction
execute as @a at @s if block ~~~ carpet 5 run scoreboard players add @s 撤离 1
execute as @a[scores={撤离=1..}] at @s unless block ~~~ carpet 5 run scoreboard players set @s 撤离 0
title @a[scores={撤离=100}] title §l§a撤离成功
tp @a[scores={撤离=100}] 坐标
```

- 黄绿色地毯 data 5；站上去计时，离开清零；100 传送到撤离点。
- 进度用 actionbar；成功用 title；适合塔科夫/暗区。
- `if block ~~~ carpet 5` 只检查脚下方块；地毯被破坏/替换会中断。

### 5.5 空岛 / 仓库 / 坐标分解

```mcfunction
execute as @a[scores={x=10000..}] at @s run tp ~10000~~
scoreboard players remove @a[scores={x=10000..}] x 10000
execute as @a[scores={x=1000..}] at @s run tp ~1000~~
scoreboard players remove @a[scores={x=1000..}] x 1000
...
```

- 把 x/y/z 分数按 10000/1000/100/10/1 分解成多次相对 `tp`；适合“自闭链”/无坐标参数传送。
- 负数分支用 `..-10000` 等，方向和正数相反；顺序必须从大到小，否则会多传。
- 空岛/仓库用盔甲架当“坐标标记”，`记录坐标` 自增分配，`structure load` 生成；用 `tag=创建/返回/已有` 做状态。
- 样本里 `tp ~10000~~` 一次移动 10000 格，可能跨区块/卡加载；大坐标要分段/`tickingarea`。

### 5.6 死亡动画 / 狗牌

```mcfunction
# 立即重生后，用“自己位置没有玩家实体”检测死亡
execute as @a at @s unless entity @e[r=0.01,c=1,type=player] run scoreboard players set @s 死亡动画 1
execute as @a[scores={死亡动画=1..13}] at @s run titleraw @s title {"rawtext":[...]}
/scoreboard players set @a[scores={死亡动画=1}] 等待时间 30
```

- 前提：开启立即重生；死亡瞬间旧玩家实体消失，用 `unless entity @e[r=0.01,c=1,type=player]` 检测。
- 狗牌：结构保存掉落物，死亡时 `structure load 狗牌 ~~~`；4cb 版可靠，1cb 版有漏。
- 样本用 `/camera fade color` 做黑屏；**网易未验证 camera**，用 title/粒子/`fog`（若支持）替代。
- 死亡检测会和其他死亡系统冲突；全图只保留一个“死亡检测”头。

## 6. 拔刀剑 / 钓鱼钩触发器

```mcfunction
# 副手特殊值鹦鹉螺壳 + 主手钓鱼竿 = 武器
execute as @a[hasitem=[{item=nautilus_shell,location=slot.weapon.offhand,data=31},{item=fishing_rod,location=slot.weapon.mainhand}],tag=!保护] at @s run execute as @e[type=fishing_hook,r=2] at @s run tag @s add 拔刀斩

# 以钩子为原点，沿视线方向放粒子/伤害
execute as @a[tag=拔刀斩] at @s positioned ^^0.75^5 run tag @e[r=5,family=!inanimate,c=1] add 击中
damage @e[tag=击中] 15 suicide entity @p[tag=拔刀斩]
tag @e[tag=击中] remove 击中
tag @a[tag=拔刀斩] remove 拔刀斩
kill @e[type=fishing_hook,r=2]
```

- **钓鱼钩**是“挥刀”触发器：抛竿/收竿产生实体；副手特殊值物品区分武器；`data` 是网易常用的物品 ID。
- 剑气/刀光：两个盔甲架 `n`（其中一个 `tag=旋转`）+ `tp`/`rotated as` 计算方向；粒子沿 `^^^` 排布。
- 伤害：`damage` 命令（可带 cause/entity）；或数据化伤害链。
- 结构 `structure load 拔刀剑船1` 可做弧形刀光；船/盔甲架是标记，不是真船。
- 冷却/时停/魂刀/吸血/破甲都是“tag + 分数 + 效果”的组合；先做单武器闭环，再复制。
- 坑：`execute as@e` 缺空格会解析失败；`data` 在国际版逐渐被组件替代；`kill` 钩子要放在链尾。

## 7. 可复用套路速查

| 需求 | 套路 |
|---|---|
| 无 UI 按钮 | 鸡蛋/雪球/纸 + 投掷物事件 + `@p[r=2]` |
| 页面/选项 | 一个整数 objective + 区间分支 + `rx`/`rxm` |
| 选人 | `选人` 从 -1 递增，0=选中，`tag=选中` |
| 全服公告 | sidebar + 假玩家行名 + 定期 remove/add objective |
| 商店 | 木桶装商品 + `clone` + `setblock air destroy` + `tp` item |
| 批量购买 | 数字键盘分数 + 总价 + 余额检查 |
| 折扣 | `优惠价 = 价格 * 折扣 / 100` |
| 金币提示 | 影子分数比较余额变化 |
| 开箱 | 进度 + `random` + `clone` + `tp` item + `clear` 钥匙 |
| 反穿墙 | XP 球碰撞探针 + VL |
| 防矿透 | 矿物年龄 + 附近玩家分 + 衰减 + 阈值审核 |
| 领地 | NPC+基岩+编号；靠推开/提示，不是真保护 |
| 卡密门 | 颜色羊毛+铁门+蜡烛；`^^1^` 检查面前门 |
| 封禁 | `kick` + 外部黑名单；Bedrock 无持久 ban |
| 匹配 | 区域计数 + 倒计时 + 队伍人数均衡 |
| 随机传送 | `random 1..N` + 固定坐标表 |
| 撤离 | 地毯 `if block` + 进度 + 传送 |
| 死亡动画 | 立即重生 + 无玩家实体检测 + title 序列 |
| 狗牌 | `structure load` 在死亡点 |
| 拔刀剑 | 钓鱼钩 + 副手 data + 盔甲架方向 + `damage` |

## 8. 常见坑

- **权限用 tag 不是安全边界**：玩家能 `/tag` 就能给自己权限；正式服用 OP/`haspermission`/菜单物品。
- **投掷物触发器要清理**：鸡蛋/雪球/钩子不 kill 会堆积。
- **多人共用输出位**：商店/开箱的 `clone`/`tp` 会拿错物品；按玩家分配坐标或串行化。
- **`@e` 不筛玩家/实体**：匹配区、领地、开箱选择器要加 `type=player`/`tag=生物`。
- **`data` 物品值**：网易常用，国际版逐渐组件化；跨版本要改。
- **`camera`/`hud`**：网易未验证/未列；死亡动画的 `camera fade`、数据化的 `hud hide` 先 `/help` 验证。
- **`title` 纯文本 512 字节**：大菜单用 `titleraw`。
- **`scoreboard players test` 旧语法**：新链用 `execute if score`。
- **自动封禁风险**：反穿墙/防矿透都有误判；只做嫌疑分 + 人工审核。
- **结构加载重复**：狗牌/开箱/空岛结构要 once 标记，避免每 tick 重复加载。

## 9. 文件索引

| 文件 | 学什么 |
|---|---|
| `8CB选人菜单` / `选人踢出菜单` | 选人分数映射、`@r` 重置、`tag=选中` |
| `协管菜单-优化版` / `我的世界封禁菜单` | 鸡蛋菜单、页面分数、选人、`kick` |
| `我的世界选队菜单&均分匹配` / `我的世界匹配区指令` | 区域计数、倒计时、四队均衡 |
| `密室杀手指令` | 角色分配、T显、误杀判定、胜负 |
| `免举批量购买商店` / `免举购买商店` / `二次免举折扣商店` | 木桶 clone、批量、折扣、二次确认 |
| `仿现实彩票系统` | 随机号码、期号、匹配、倍率 |
| `我的世界金币后处理系统` | 影子分数、余额变动提示 |
| `纸条开箱 V1/V2/V3` / `矿物块开箱` / `视角开箱` | 进度、概率、clone、structure |
| `反穿墙` / `防矿透指令` | XP 球探针、矿物年龄、审核 |
| `工会菜单&领地保护` | NPC 领地、邀请、推开 |
| `我的世界卡密门指令` | 本地坐标、门/蜡烛、进度 |
| `我的世界地毯撤离点` / `固定地点随机传送` | 地毯计时、随机坐标表 |
| `我的世界二分法创建空岛` / `二分法仓库菜单` / `自闭链自定义坐标传送` | 盔甲架标记、坐标分解、结构 |
| `我的世界死亡等待动画` / `死亡掉落概率返还` / `狗牌指令` | 死亡检测、结构、UID 返还 |
| `拔刀剑` 系列 | 钓鱼钩、副手 data、盔甲架刀光、`damage` |
| `高质简洁公告栏` | sidebar 假玩家行、定期重建 |

## 10. 触屏/屏幕坐标检测（二代）

来源：`二代触屏检测.docx`。核心不是读取真实触摸事件，而是用**烟花火箭**当“屏幕射线标记”，通过**二分法**反推它在屏幕上的水平/竖直比例。

### 原理

```mcfunction
scoreboard objectives add 水平视角 dummy
scoreboard objectives add 竖直视角 dummy
scoreboard objectives add 水平上限 dummy
scoreboard objectives add 竖直上限 dummy
scoreboard players set 百 水平视角 100

# 1) 识别触屏者：主手烟花
execute as @a[hasitem={item=firework_rocket,location=slot.weapon.mainhand,quantity=1}] run tag @s add 触屏者
replaceitem entity @a[tag=触屏者] slot.weapon.mainhand 0 firework_rocket 2 1
tag @e[type=fireworks_rocket] add 触摸点

# 2) 把触摸点放到视线前方 15 格
execute as @e[tag=触摸点] at @s facing entity @p[tag=触屏者] eyes run tp @s ^^^ ~ ~
execute as @a[tag=触屏者] at @s anchored eyes run tp @e[tag=触摸点] ~~~
execute as @e[tag=触摸点] at @s run tp @s ^^^-15

# 3) 二分测水平：先判左右，再 128/64/32/.../1 逐级加/减
execute as @a[tag=触屏者] at @s anchored eyes positioned ^100000^^ as @e[tag=触摸点,r=100000] run tag @s add 左
execute as @a[tag=触屏者] at @s anchored eyes positioned ^-100000^^ as @e[tag=触摸点,r=100000] run tag @s add 右
execute as @a[tag=触屏者] at @s anchored eyes positioned ^100012.8^^ as @e[tag=触摸点,r=100000,tag=左] run scoreboard players add @s 水平视角 128
execute as @a[tag=触屏者] at @s anchored eyes positioned ^100012.8^^ as @e[tag=触摸点,r=100000,tag=左] at @s rotated as @p[tag=触屏者] run tp @s ^-12.8^^
# ... 64/32/16/8/4/2/1，负方向对称 ...

# 4) 归一化成百分比
execute as @a[tag=触屏者] run scoreboard players operation @s 水平视角 *= 百 水平视角
execute as @a[tag=触屏者] run scoreboard players operation @s 水平视角 /= @s 水平上限
execute as @a[tag=触屏者] run titleraw @s actionbar {"rawtext":[{"text":"x:"},{"score":{"name":"@s","objective":"水平视角"}},{"text":" y:"},{"score":{"name":"@s","objective":"竖直视角"}}]}

# 5) 清理
kill @e[type=fireworks_rocket]
tag @a[tag=触屏者] remove 触屏者
```

### 关键点

- **不是真正读取触摸屏**，而是把烟花火箭放到视线前方，用二分法测出它在屏幕上的角度比例；所以只能得到“瞄准点/触摸点”的近似。
- 先 `tag=校准` 记录 `水平上限/竖直上限`，再算百分比；换分辨率/视角要重新校准。
- 二分从 **128** 开始，逐级 64/32/16/8/4/2/1；每级都要把触摸点沿视线方向 `tp` 回相应偏移，否则下一级基准错误。
- `positioned ^100000^^` + `r=100000` 是“沿视线方向无限远”的判断技巧；大半径选择器很贵，只适合小游戏/低频。
- 只对**主手烟花**生效；生存最后一格放 2 个火箭，取校准点；用完 `kill` 烟花。
- 移动端屏幕比例、FOV、视角摇晃都会影响精度；按钮区间要留死区。
- `stopsound @a firework.shoot` 关掉火箭声。

## 11. 检查清单

- [ ] 触发器物品锁定，投掷物/钩子有清理。
- [ ] 页面分数有初值/关闭/重置；不会卡在旧页面。
- [ ] 权限不是仅靠可自加的 tag。
- [ ] 商店/开箱先检查余额/钥匙，再 clone/扣分；失败有提示。
- [ ] 多玩家输出位不共用，或已串行化。
- [ ] 反作弊只做嫌疑，不自动永封；有审核/白名单。
- [ ] 领地/保护不是只靠提示；需要真保护时用结构/回滚/行为包。
- [ ] 死亡检测全图唯一；不会和其他系统重复触发。
- [ ] `camera`/`hud`/`data` 在网易 1.21.130 已验证。
- [ ] 旧 `execute @a ~ ~ ~` 已升级为 `as/at`。
- [ ] 大菜单用 `titleraw`，没有每次交互弹大标题。
- [ ] 性能：`@e` 范围、clone/结构频率、sidebar 重建频率都测过。
