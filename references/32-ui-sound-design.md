# 32 · UI + 音效设计（并入）

> 来源：协作者提供的 `bedrock-ui-sound-design.skill`。
> 与 `30-command-ui-design.md`（版式/配色/符号）和 `31-command-ui-modern.md`（现代 execute）互补：30 管“长什么样”，31 管“命令怎么写”，本篇管“通道调度、标题顺序、UI/音效联动”。
>
> **网易色码安全线**：默认只用标准 16 色。扩展色 `§g §i §p §q §u §v` 先在目标版本/目标设备实测；不支持时按下面降级：
>
> | 扩展 | 安全替代 | 用途 |
> |---|---|---|
> | `§p` | `§d` | 菜单竖条 |
> | `§g` | `§6` | 金币/碎片 |
> | `§i` | `§8` | 字段名/弱提示 |
> | `§q` | `§a` | 成功箭头 |
> | `§u` | `§b` | 分隔线/强调 |
> | `§v` | `§e` | 警告/换弹 |
>
> **音效白名单**：本篇列出的 57 个音效名中，`block.anvil.land`、`block.beehive.shear`、`entity.player.attack.strong`、`hit.amethyst_block`、`mob.enderdragon.flap`、`random.door_open`、`random.enderchestclosed`、`random.totem`、`ui.loom.take_result` 不在当前 `scripts/lint_commands.py` 的 `SOUNDS` 白名单内；原文也标了“先实机验证”。未验证前不要用。
>
> 原文的 `%%2` 兜底、`title times → subtitle → title` 顺序、动作栏同刻互斥、音量预算、旋律 `pitch=2^(n/12)` 全部保留。

# 基岩版 UI + 音效设计

做两件事：**让界面好看且读得懂**，**让声音有层次且有节奏**。示例都是可直接粘贴的基岩版命令，计分项 / 变量名自行替换。声音与粒子只用 §6.3 与 lint 白名单里的名字（写错不报错，只是没声音 / 没画面）。

> 诚实说明：音量、音高、层间延迟是**起点**，不是定论。必须进游戏用耳朵再调；不同设备听感不同。

---

## 0. 工作流

1. **选通道**（§1）：常驻 → 动作栏；一次性大事件 → 标题 + 副标题；说明 / 结算 → 聊天栏。
2. **选版式**：从 §4 示例库挑最像的，改字改色，不要凭空发明骨架。
3. **定主题色**（§2.2）：一个子系统一套色，全程不变。
4. **接机制**（§3）：条件显示 `%%2`，档位条 `%%9`，多档用 §8 生成器，不手写嵌套。
5. **配声音**（§6、§7）：先定事件情绪，再选叠加方式（同刻叠加 / 时间递进 / 旋律式 §6.9 / 抽丝剥茧逐层展开 §6.10）。
6. **查清单**（§9）。

---

## 1. 硬约束

| 事实 | 后果 |
|---|---|
| `title` / `subtitle` / `actionbar` **同一刻只有一个生效**，后发覆盖先发 | 常驻 HUD 每刻刷动作栏会盖掉同刻横幅 → 横幅期间 HUD 让位（§5） |
| `subtitle` 需要 `title` 才有位置；**发送顺序固定：`title @s times …` → `titleraw subtitle` → `titleraw title`**（先副后主，先发 title 会让副标题错位/不显示） | 横幅 = times + subtitle + title 三条成组，顺序不能错 |
| `rawtext` 是 JSON 唯一顶层键 | `{"text":"x"}` 直接当顶层会静默失败 |
| 只有 `§` 样式码，没有 Java 的 `color`/`bold`/`clickEvent` | 样式靠 `§l §o §r` 与色码 |
| 扩展色 `§g §i §p §q §u §v` 版本不一，网易不一定有 | **只用标准 16 色** |
| 全角占 2 格；动作栏约 40 半角宽 | 单行 ≤ 20 全角；副标题 ≤ 30 |
| 不用 `\t` | 用空格 |
| `with` 里带 `{}` 的选择器可能被 JSON 校验误判 | 能放进外层 `execute as @a[...]` 就放外层 |
| `playsound` 写错名字不报错 | 只用白名单 |
| 命令方块链每刻最多执行一次 | 动画靠「计数器 + 每刻递增」 |

| 通道 | 半角宽 | 全角上限 | 建议行数 |
|---|---|---|---|
| actionbar | ≈40 | 20 | 3–6 |
| subtitle | ≈60 | 30 | ≤ 9 |
| title | — | 1 行大字 | 1 |
| tellraw | 不限 | — | 不限（会刷屏） |

---

## 2. 审美系统

### 2.1 五条原则

1. **层级**：一级（阶名、事件名）最显眼，二级（数值）次之，三级（提示）最弱。改不了字号，只能靠亮度 + `§l` + 全角间隔字：一级亮色加粗，三级 `§8`/`§7`。
2. **克制**：主色 1 + 辅色 1 + 强调 1 + 中性（§7 §8 §f）。彩虹界面廉价。
3. **一致**：同一含义永远同色同符号（能量 §b、危险 §4）。
4. **留白**：标题 / 内容 / 提示三段之间留空行；动作栏顶部加 `\n\n` 把 HUD 抬离视野中央。
5. **对齐**：一个界面只用一种括号、一种竖条、一种分隔线；全角半角混排补空格。块字符宽度因字体不同，**必须在目标设备上看一眼**。

### 2.2 六套主题

| 主题 | 主色 | 辅色 | 强调 | 分隔线 | 适合 |
|---|---|---|---|---|---|
| 赤刃 | `§c` | `§4` | `§e` | `§4▔` | 近战、血、暴击 |
| 寒霜 | `§b` | `§3` | `§f` | `§3▔` | 法术、冰、科技 |
| 鎏金 | `§6` | `§e` | `§f` | `§6▔` | 商店、奖励、史诗 |
| 翠影 | `§a` | `§2` | `§e` | `§2▔` | 治疗、队伍、自然 |
| 幽紫 | `§d` | `§5` | `§b` | `§5▔` | 神秘、传送、虚空 |
| 墨灰 | `§f` | `§7` | `§e` | `§8▔` | 系统、设置、日志 |

**数值分档色**（低→高）：`§4 → §c → §6 → §e → §2 → §a`；空槽 `§8`。
**资源固定色**：经验 §b、金币 §e、碎片 §6、钻石 §2、灰烬 §8、等级 §a、能量 §b、生命 §c。

### 2.3 符号库

| 用途 | 字符 |
|---|---|
| 括号（选一种贯穿） | `◁╢ ╟▷` · `〖 〗` · `【 】` · `｛ ｝` · `《 》` · `◢［ ］◣` |
| 竖条 | `▏ ▎ ▍ │ ┆ ┃ ║` |
| 分隔线 | `▔`×20 · `────` · `━━━━` · `▁▁▁▁` · `- - -`（50–75 个，竖条菜单） |
| 进度块 | `▰ ▱ █ ■ □ ● ○` |
| 指示 | `▶ ➤ ◇ ◈ ◆ ❖ >>` |
| 装饰 | `☾ ☽ ✦ ✧ ☬ ◥ ◤ ╱ ╲` |
| 状态 | `✔ ✘ ⚠ ★ ☆ ♥ ⚔ ☠`（部分字体缺字，先测） |
| 间隔字 | `尾　刺`、全角字母（制造大标题感） |

### 2.4 三段式版面

```
<标题行>   括号体系 + 名称 + 灰色英文副标
<分隔线>   同主题色
<内容区>   字段行 / 选项行 / 进度条
<提示行>   §8[ 操作说明 ]
```
字段行：`§c▎ §7字段名 §f值`。

---

## 3. 机制速查

### 3.1 片段
```json
{"text":"§a文字"}
{"score":{"name":"@s","objective":"hp"}}
{"selector":"@s"}
{"translate":"%%2","with":{"rawtext":[ ... ]}}
```

### 3.2 条件显示 `%%2`
`with` 里 `selector` 未命中会被**丢弃**，参数列表变短；`%%2` 取第 2 个。命中 → `[选择器结果, 文本]` → 显示文本；未命中 → 只剩 `[文本]` → 显示空。
```json
{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={mode=2}]"},{"text":"§e双刺"}]}},{"text":""}
```
规则：
- 每个 `%%2` 后跟 `{"text":""}` 兜底。
- **文字和数值分两块**：`%%2` 只显示一个参数；要「条件显示 `冷却 ` + 数值」写两个条件块（常见错误：二者塞进同一个 with，数值永不显示）。
- 选项写法：**默认色 → 条件染色 → 文字**。
```json
{"text":"§7"},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=1}]"},{"text":"§f"}]}},{"text":"# 选项一 "}
```

### 3.3 分档 `%%9`
8 个累进选择器 + 8 个候选文本，译文串 `%%9`。选择器写 `{x=..上限}`，成立个数 k，取第 `9-k` 个候选。通则：m 个候选 → 译文串 `%%(m+1)`，m 个选择器，上限递增，最后一个 99 兜底。超过 8 档就嵌套：第 8 个候选换成下一级 translate（数字 = 该级选择器数 + 1）。**别手写，用 §8 `tiered()`。** 10 格能量条（11 档）= `%%9` 套 `%%5`。

### 3.4 流光 `%%1…%%8`
译文串写 `%%1…%%8`，`with` 放 8 个条件 translate：第 n 个在 `dh=n` 时输出亮色码，否则为空。`dh` 每刻 +1，到 8 清零，亮点逐格移动。

### 3.5 计数器时间轴（所有「循序渐进」的底座）
```mcfunction
scoreboard players set @s fx_t 1
execute as @a[scores={fx_t=1}] at @s run <第 1 帧>
execute as @a[scores={fx_t=7}] at @s run <第 7 帧>
scoreboard players add @a[scores={fx_t=1..}] fx_t 1
scoreboard players set @a[scores={fx_t=41..}] fx_t 0
```
❗ 递增必须放在**同一条链的最后**；放另一条链会因执行顺序不定而跳过第 1 帧。
❗ 时间轴期间别再触发同一计时；防重入：触发时加 `scores={fx_t=0}`。

---

## 4. UI 示例库

### 4.1 聊天栏

**U01 系统公告**
```mcfunction
tellraw @a {"rawtext":[{"text":"\n§lVlad >§r§f系统已就绪 §7· §f主手 §b钓鱼竿§f + 副手 §d鹦鹉螺壳"}]}
tellraw @a {"rawtext":[{"text":"§lWave >§r§f第 §e"},{"score":{"name":"fb_wave","objective":"arena"}},{"text":" §f波即将开始"}]}
```

**U02 资源变动卡**
```mcfunction
tellraw @s {"rawtext":[
 {"text":"§f｜§e〖§e金币 §f> "},{"score":{"name":"@s","objective":"gold"}},
 {"text":" + "},{"score":{"name":"@s","objective":"gold_add"}},
 {"text":"\n §eGold coin ：§f "},{"score":{"name":"@s","objective":"gold_prev"}}
]}
```

**U03 卡片（头 → 斜切分隔 → 字段 → 操作）**
```mcfunction
tellraw @s {"rawtext":[
 {"text":"§c< §f尾刺·升阶 §c>\n§4▔▔▔▔▔▔▔▔╲▁▁▁▁▁▁\n§c▎ §7阶位 §e双刺\n§c▎ §7连击 §f"},
 {"score":{"name":"@s","objective":"combo"}},
 {"text":"\n§4➤ §8[§f保持连击，鱼漂更狠§8]"}
]}
```

**U04 错误 / 轻提示 / 危险**
```mcfunction
tellraw @s {"rawtext":[{"text":"§l§c| §r§f申请失败 §7未查询到该队伍"}]}
tellraw @s {"rawtext":[{"text":"§8[§7§o 道具操作不合法 §r§8]"}]}
tellraw @a {"rawtext":[{"text":"> §4Danger §f前方区域危险，请注意安全"}]}
```

**U05 战斗结算**
```mcfunction
tellraw @s {"rawtext":[
 {"text":"\n§6◁〖§f战斗结算§6〗▷\n§6▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"},
 {"text":"§6▎ §7击杀 §f"},{"score":{"name":"@s","objective":"kills"}},
 {"text":"\n§6▎ §7最高连击 §f"},{"score":{"name":"@s","objective":"best_combo"}},
 {"text":"\n§6▎ §7获得 §e金币 §f"},{"score":{"name":"@s","objective":"gold_add"}},
 {"text":"\n§6➤ §8[§f下蹲领取奖励§8]\n"}
]}
```

**U06 加入广播**
```mcfunction
tellraw @a {"rawtext":[{"text":"§f>§b> §f"},{"selector":"@s"},{"text":" §7加入了战场 §8("},{"score":{"name":"online","objective":"arena"}},{"text":"§8/10)"}]}
```

### 4.2 动作栏 HUD

**U07 五行武器 HUD**（能量条用 §8 `bar10()` 生成后拼入 `<能量条>` 位置）
```mcfunction
execute as @a[scores={equip=1,ban=0}] run titleraw @s actionbar {"rawtext":[
 {"text":"\n\n§c◁╢ §f尾　刺 §c╟▷ §8VLAD · 弗拉迪\n§4▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n§c▶ "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={stage=1}]"},{"text":"§f§l刺击§r"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={stage=2}]"},{"text":"§e§l双刺§r"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={stage=3}]"},{"text":"§6§l刺环§r"}]}},{"text":""},
 {"text":" §8│ §7连击 §f"},{"score":{"name":"@s","objective":"combo"}},
 {"text":" §8│ §7命中 §f"},{"score":{"name":"@s","objective":"hits"}},
 {"text":"\n§b* §7>> §7能量 "},<能量条>,{"text":" §f"},{"score":{"name":"@s","objective":"energy"}},{"text":"§7/100"},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={energy=100..}]"},{"text":" §e§l◆ 终结就绪"}]}},{"text":""},
 {"text":"\n§8[ "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={energy=100..,cd=0}]"},{"text":"§e抛竿 §f触发终结"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd=1..}]"},{"text":"§c冷却 §f"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd=1..}]"},{"score":{"name":"@s","objective":"cd"}}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={energy=..99,cd=0}]"},{"text":"§f抛竿，鱼漂即尾刺"}]}},{"text":""},
 {"text":" §8]§r"}
]}
```

**U08 极简单行 HUD**
```mcfunction
execute as @a run titleraw @s actionbar {"rawtext":[
 {"text":"§c❤ §f"},{"score":{"name":"@s","objective":"hp"}},
 {"text":" §8│ §b◆ §f"},{"score":{"name":"@s","objective":"mp"}},
 {"text":" §8│ §e✦ §f"},{"score":{"name":"@s","objective":"gold"}}
]}
```

**U09 四技能栏（就绪 / 冷却互斥）**
```mcfunction
execute as @a[scores={equip=1}] run titleraw @s actionbar {"rawtext":[
 {"text":"\n§8[ "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_q=0}]"},{"text":"§aQ§8·§f斩 "}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_q=1..}]"},{"text":"§8Q·§7斩 "}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_w=0}]"},{"text":"§aW§8·§f盾 "}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_w=1..}]"},{"text":"§8W·§7盾 "}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_e=0}]"},{"text":"§aE§8·§f跃 "}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_e=1..}]"},{"text":"§8E·§7跃 "}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_r=0,ult=100..}]"},{"text":"§e§lR·终结"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_r=1..}]"},{"text":"§8R·§7终结"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_r=0,ult=..99}]"},{"text":"§8R·§7蓄力 "}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={cd_r=0,ult=..99}]"},{"score":{"name":"@s","objective":"ult"}}]}},{"text":""},
 {"text":" §8]"}
]}
```

**U10 连击计数（≥2 才出现，分档变色）**
```mcfunction
execute as @a run titleraw @s actionbar {"rawtext":[
 {"text":"\n\n\n"},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={combo=2..4}]"},{"text":"§f"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={combo=5..9}]"},{"text":"§e§l"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={combo=10..}]"},{"text":"§c§l§o"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={combo=2..}]"},{"score":{"name":"@s","objective":"combo"}}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={combo=2..}]"},{"text":" COMBO"}]}},{"text":""}
]}
```

**U11 区域信息条**：用 §8 `tiered("area", [...])` 生成，前缀 `§8｜ §7Regional ｜ §f > §e<地名> §8｜`。

### 4.3 菜单

**U12 竖条菜单**
```mcfunction
execute as @a[scores={menu=1..3}] at @s run titleraw @s actionbar {"rawtext":[
 {"text":"§d▏§7 * §d我的菜单 §7*§r menu §8>>> information§r\n§7--------------------------------------------------\n\n "},
 {"text":"§7"},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=1}]"},{"text":"§f"}]}},{"text":"# 传送主城  "},
 {"text":"§7"},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=2}]"},{"text":"§f"}]}},{"text":"# 设重生点  "},
 {"text":"§7"},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=3}]"},{"text":"§f"}]}},{"text":"# 接受传送"},
 {"text":"\n\n§b* §7>> §f低头切换 §8│ §f抬头确认\n§7--------------------------------------------------\n§r"}
]}
execute as @a[scores={menu=1..},rxm=88] at @s run titleraw @s actionbar {"rawtext":[{"text":">>> §7我的菜单已关闭§f <<<"}]}
```

**U13 箭头菜单（选中项 `▶`；写两套互斥条件块，不依赖退格 `\b`）**
```mcfunction
execute as @a[scores={menu=11..13}] run titleraw @s actionbar {"rawtext":[
 {"text":"\n\n§d◁╢ §f主　菜　单 §d╟▷ §8Main menu\n§5▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=11}]"},{"text":"§d  ▶ §f"}]}},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=12..13}]"},{"text":"§8    "}]}},{"text":"治疗系统\n"},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=12}]"},{"text":"§d  ▶ §f"}]}},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=11}]"},{"text":"§8    "}]}},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=13}]"},{"text":"§8    "}]}},{"text":"组队系统\n"},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=13}]"},{"text":"§d  ▶ §f"}]}},{"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=11..12}]"},{"text":"§8    "}]}},{"text":"商店\n"},
 {"text":"§8[ 低头切换 · 抬头确认 ]§r"}
]}
```

**U14 拨号盘**
```mcfunction
execute as @a[scores={pad=21..35}] run titleraw @s actionbar {"rawtext":[
 {"text":"\n§2◁╢ §f组队系统 §2╟▷ §8Team-up\n§a▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n§8 "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={pad=21}]"},{"text":"§f"}]}},{"text":"1 "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={pad=22}]"},{"text":"§f"}]}},{"text":"2 "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={pad=23}]"},{"text":"§f"}]}},{"text":"3 §2▏§8 "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={pad=33}]"},{"text":"§f"}]}},{"text":"队员查询\n§8 "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={pad=24}]"},{"text":"§f"}]}},{"text":"4 "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={pad=25}]"},{"text":"§f"}]}},{"text":"5 "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={pad=26}]"},{"text":"§f"}]}},{"text":"6 §2▏§8 "},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={pad=34}]"},{"text":"§f"}]}},{"text":"申请加入"}
]}
```

**U15 菜单开启动画（4 帧，`dh` 每刻 +1）**
```mcfunction
execute as @a[scores={open=1..,dh=1..4}] run titleraw @s actionbar {"rawtext":[
 {"translate":"%%5\n\n\n\n§r §r","with":{"rawtext":[
  {"selector":"@s[scores={dh=1..1}]"},{"selector":"@s[scores={dh=1..2}]"},{"selector":"@s[scores={dh=1..3}]"},{"selector":"@s[scores={dh=1..4}]"},
  {"text":"§9§o ┌──────┐\n │ ◇  ◇ │\n └──────┘"},
  {"text":"§9§o ┌──────┐\n │ ◈  ◇ │\n └──────┘"},
  {"text":"§b§o ┌──────┐\n │ ◈  ◈ │\n └──────┘"},
  {"text":"§b§o ┌─Run──┐\n │ ◆  ◆ │\n └──────┘"}
 ]}}
]}
```
（4 个选择器 + 4 个候选，译文串 `%%5`。）

### 4.4 标题 / 横幅（times → subtitle → title，顺序固定）

> 先 `title @s times 渐入 停留 渐出`，再发 `subtitle`，最后发 `title`（title 一发就触发显示）。只发 title 时可省略 subtitle。

**U16 进入地点**
```mcfunction
title @a[scores={zone=1}] times 6 40 12
titleraw @a[scores={zone=1}] subtitle {"rawtext":[{"text":"§7Next: Generation."}]}
titleraw @a[scores={zone=1}] title {"rawtext":[{"text":"§6◁§7།§f§l 交易市场 §7།§6▷"}]}
```

**U17 事件横幅**
```mcfunction
title @s times 3 22 8
titleraw @s subtitle {"rawtext":[{"text":"§7双刺 §8→ §6刺环"}]}
titleraw @s title {"rawtext":[{"text":"§c◁§7།§e§l 阶位提升 §7།§c▷"}]}
```

**U18 倒计时大数字**
```mcfunction
execute as @a[scores={cd3=3}] run titleraw @s title {"rawtext":[{"text":"§e§l３"}]}
execute as @a[scores={cd3=2}] run titleraw @s title {"rawtext":[{"text":"§6§l２"}]}
execute as @a[scores={cd3=1}] run titleraw @s title {"rawtext":[{"text":"§c§l１"}]}
execute as @a[scores={cd3=0,go=1}] run titleraw @s title {"rawtext":[{"text":"§a§l◁ 开　始 ▷"}]}
```

**U19 死亡 / 失败**
```mcfunction
titleraw @s subtitle {"rawtext":[{"text":"§8下蹲复活 §7· §8Hold sneak to respawn"}]}
titleraw @s title {"rawtext":[{"text":"§4§l你 已 倒 下"}]}
```

### 4.5 进度 / 装饰

**U20 5 格进度条**
```mcfunction
execute as @a[scores={load=5}]  run titleraw @s actionbar {"rawtext":[{"text":"§7[§f装填§7] §a▰§8▰▰▰▰ §7- 20%"}]}
execute as @a[scores={load=15}] run titleraw @s actionbar {"rawtext":[{"text":"§7[§f装填§7] §a▰▰§8▰▰▰ §7- 40%"}]}
execute as @a[scores={load=25}] run titleraw @s actionbar {"rawtext":[{"text":"§7[§f装填§7] §a▰▰▰§8▰▰ §7- 60%"}]}
execute as @a[scores={load=35}] run titleraw @s actionbar {"rawtext":[{"text":"§7[§f装填§7] §a▰▰▰▰§8▰ §7- 80%"}]}
execute as @a[scores={load=45}] run titleraw @s actionbar {"rawtext":[{"text":"§7[§f装填§7] §a▰▰▰▰▰ §7- 100%"}]}
```

**U21 8 格流光线**
```mcfunction
execute as @a[scores={dh=1..8}] run titleraw @s actionbar {"rawtext":[
 {"translate":"§2%%1▔%%2▔%%3▔%%4▔%%5▔%%6▔%%7▔%%8▔","with":{"rawtext":[
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={dh=1}]"},{"text":"§a"}]}},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={dh=2}]"},{"text":"§a"}]}},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={dh=3}]"},{"text":"§a"}]}},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={dh=4}]"},{"text":"§a"}]}},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={dh=5}]"},{"text":"§a"}]}},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={dh=6}]"},{"text":"§a"}]}},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={dh=7}]"},{"text":"§a"}]}},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={dh=8}]"},{"text":"§a"}]}}
 ]}}
]}
scoreboard players add @a[scores={dh=1..}] dh 1
scoreboard players set @a[scores={dh=9..}] dh 1
```

**U22 状态面板（聊天栏）**
```mcfunction
tellraw @s {"rawtext":[{"text":"\n§d▁▁▁▁▁▁▁▁▁▁§b◢［§3ＰＲＯＦＩＬＥ§b］◣§d▁▁▁\n§d│ §7个人信息 §d│ §7- 战斗数据 - §d╱\n §d╢§b▷ §f击杀 §b◁§d╟│§b➤ §f"},{"score":{"name":"@s","objective":"kills"}},{"text":"\n §d╢§b▷ §f连击 §b◁§d╟│§b➤ §f"},{"score":{"name":"@s","objective":"best_combo"}},{"text":"\n§d▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ §3☬\n"}]}
```

**U23 像素图标（副标题，需配 title）**
```mcfunction
titleraw @s subtitle {"rawtext":[{"text":"§7◢▃▃▃▃▃▃◣\n▌◤▔▔▔▔▔◥▌\n▌┃     ┃▌\n▊ §c☉§7 §0▊\n▌┃     ┃▌\n▌◣▁▁▁▁▁◢▌"}]}
titleraw @s title {"rawtext":[{"text":""}]}
```

**U24 边框库**

| 样式 | 写法 |
|---|---|
| 青蓝花括号 | `§b◁｛ §fＳｔａｒｔ　Ｇａｍｅ§b ｝▷` |
| 金色书名号 | `§6◁〖§f武器图鉴§6〗▷` |
| 三竖条 | `§8§o▎§7▎§b▎ ＰＶＰ　Ｇａｍｅ §b§o▎§7▎§8▎` |
| 红帝王框 | `§4◁《｛§f帝王§4｝》▷` |
| 粗斜体称号 | `§l§o§e▎§7▍ §r§l§f匠神 §r§o§7▍§e▎` |
| 对阵条 | `§4〈▷ 【§f红队§4】 §7〈§f3：2§7〉 §b【§f蓝队§b】 ◁〉` |
| 状态标签 | `- §7【 §f填装中 §7】 -` |
| 进度横线夹标题 | `§8▰▰§7▰▰▰§f▰▰▰▰▰§e▰§f▰▰▰▰▰§7▰▰▰§8▰▰` |

---

### 4.5 组件化思维（参考 mcui 组件库）

不要手拼 JSON：把界面拆成「组件 → 版式 → 包装命令」，每个构建器返回组件列表，最后由包装函数输出整条命令。

| 要点 | 做法 |
|---|---|
| 命令包装 | `actionbar(sel, …)` / `subtitle(sel, …, pad=14)` / `title(sel, main, sub, times)` / `chat(sel, …)`；`sel` 是**显示条件**，其中 `@s[scores=…]` 指被选中的玩家 |
| 副标题上推 | 副标题条会贴近屏幕中下方：末尾补 `pad` 个 `\n`，把条推到上方（Boss 血条常用 14 个） |
| 定宽数字 | `num(obj)`：固定 3 位，前导零用暗色 `§8`，数字跳动时不抖动；条在前、数在后 |
| 条样式 | block `▍` / pip `● ○` / dia `◆ ◇` / slim `━ ─` / box `▰ ▱` / full `█`；颜色可「分档自动变色 / 固定色 / 每格渐变」；空槽 `§8`，数值 0 时整条 `§7` |
| 条件染色顺序 | 默认色 → 条件染色 → 文字，如 `§7` + cond(选中→`§d`) + `# 传送主城` |
| 页签 | 标签行 + 下划线行，**两行逐块等宽**，用 `\n` 连接，选中项下划线点亮 |
| 菜单 | 竖向（选中行 `▶ … ◀`，未选缩进对齐）/ 横向 / `# 选项` 哈希菜单 |
| 版式 | 三段式：标题行 / 内容区 / 提示行；行 = 主色箭头 + 白标签 + 内容 |
| 动画 | 一个每刻 +1 的计数器 + 条件文本：流光线 `flow_line`、闪烁 `blink`、打字机 `typewriter`（每刻多出 2 字）、`spinner`（0..3 循环） |
| 主题 | 同一子系统固定一个主题：vladi / ember / frost / forest / royal / shadow / cyber / mono |
| 计数器顺序 | **先 advance（`add`、到顶 `set 0`）再 trigger**：清零后下一刻才由触发置 1，避免同刻重入 |
| 新玩家 | 常驻链写 `scoreboard players add @a <obj> 0`，否则 `scores={x=0}` 匹配不到 |
| 译文数字 | `%%N` 的 N = 选择器个数 + 1；选择器写累进上限（`1..10`、`1..20`…），末个兜底 `1..99999` |
| 质检 | 写完先 lint 再渲染预览，逐状态确认（满 / 半 / 空 / 0 / 未装备） |

示例：`actionbar("@a[scores={hud=1..}]", "§c♥ ", num("hp"), "§7/200 ", bar("hp", 200, 20))`。

---

## 5. 通道调度：HUD 与横幅互不抢

横幅用计时器 `ban`，横幅期间 HUD 让位：
```mcfunction
# 触发（事件发生时）
scoreboard players set @s ban 1
title @s times 3 22 8
titleraw @s subtitle {"rawtext":[{"text":"§7双刺 §8→ §6刺环"}]}
titleraw @s title {"rawtext":[{"text":"§c◁§7།§e§l 阶位提升 §7།§c▷"}]}
# HUD 只在无横幅时画
execute as @a[scores={equip=1,ban=0}] run titleraw @s actionbar {...HUD...}
# 计时（同一条链最后）
scoreboard players add @a[scores={ban=1..}] ban 1
scoreboard players set @a[scores={ban=31..}] ban 0
```
- 停留时间用 `title @s times 5 30 10`（淡入/停留/淡出，刻），与计时器对齐。
- 聊天卡片不抢通道，适合承载需回看的明细。
- 菜单占用动作栏时 HUD 也让位（HUD 加 `scores={menu=0}`）。

---

## 6. 音效系统

### 6.1 语法与投放
```
playsound <音效> [玩家] [位置] [音量] [音高] [最小音量]
```
| 写法 | 效果 |
|---|---|
| `playsound X @s` | 只给自己，不受距离影响（UI 声） |
| `playsound X @a ~ ~ ~ 1 1` | 以坐标为中心衰减（战斗/环境，别人也能听到） |
| `playsound X @a ~ ~ ~ 4 1 0.5` | 第 6 参数最小音量：远处也能听到 → **远传层** |

音高越大越尖；音量越大传得越远。常规用 0.5–2.0；参考资料里的实际服务器写法还用到 0.35、0.47（低于 0.5）以及 3、6（高于 2），基岩版下可用，但先在目标服务器上听一遍确认不被截断。

### 6.2 三个叠加维度（先频谱，再时间，最后音高）

| 维度 | 补的是 | 做法 |
|---|---|---|
| 频谱 | 频段 | 低/中/高各一条，同刻播 |
| 时间 | 包络（起音→余响） | 错开 1–5 刻，高频延后 |
| 音高 | 厚度 | 同音效不同 pitch 同刻播（叠八度 0.5 + 1.0） |

| 层 | 作用 | 常用音效 | 音量 | 音高 |
|---|---|---|---|---|
| 低频 | 有多重 | `random.explode` `cauldron.explode` `mob.irongolem.hit` `note.bass` | 0.4–0.7 | 0.5–0.9 |
| 中频 | 是什么动作 | `random.anvil_use` `mob.wither.shoot` `random.bowhit` `mob.blaze.hit` | 1.0 | 1.0–1.2 |
| 高频 | 多快多利 | `random.orb` `note.chime` `note.iron_xylophone` `random.glass` | 0.5–0.9 | 1.4–1.9 |

**音量预算**：同刻总量 ≲ 1.6–2.0；中频 1.0，其余压到 0.4–0.7，低频最容易叠爆。
**听感→参数**：更重=低频 0.7/pitch 0.7；更亮=高频 pitch 1.6；更厚=同音效叠 0.5+1.0；更钝=砍高频；更锐=换 `note.iron_xylophone`；更长=+3 刻补轻低频；更远=+5 刻补 0.25 高频。

### 6.3 音效名清单（以当前 `scripts/lint_commands.py` 的 `SOUNDS` 为准；文首 9 个未验证名不要直接用）

| 角色 | 音效 |
|---|---|
| 低频冲击 | `random.explode` `cauldron.explode` `mob.irongolem.hit` `random.anvil_land` `ambient.weather.thunder` `item.trident.thunder` `note.bass` `dig.stone` |
| 中频主体 | `random.anvil_use` `mob.wither.shoot` `mob.blaze.hit` `mob.ghast.fireball` `mob.shulker.shoot` `mob.irongolem.throw` `random.bowhit` `random.break` `item.shield.block` `random.bow` `item.trident.throw` |
| 高频点缀 | `random.orb` `note.pling` `note.bell` `note.chime` `note.iron_xylophone` `note.bit` `note.harp` `note.flute` `random.glass` `random.pop` `random.click` `random.toast` |
| 仪式/氛围 | `beacon.activate` `beacon.power` `beacon.deactivate` `totem.use` `mob.enderdragon.growl` `portal.trigger` `portal.travel` `raid.horn` `random.levelup` |
| 火/水/杂 | `fire.ignite` `fire.extinguish` `random.fizz` `random.splash` `random.hurt` `random.chestopen` `random.chestclosed` |

**不要用**（参考资料里出现过但不在白名单）：`mob.enderdragon.flap`、`entity.player.attack.strong`、`block.anvil.land`、`random.totem`。`ui.button.click` 在 lint 白名单内，可直接用作通用按钮声；更轻的点击用 `random.click`。
新增任何音效名前，先用 `scripts/lint_commands.py` 检查。

### 6.4 音阶与和弦
`pitch = 2^(n/12)`（n 为半音数，`note.*` 乐器音适用）：

| n | 0 | 2 | 4 | 5 | 7 | 9 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|
| pitch | 1.000 | 1.122 | 1.260 | 1.335 | 1.498 | 1.682 | 1.888 | 2.000 |

- 大三和弦 同刻 `1.000 + 1.260 + 1.498`（明亮、成功）
- 小三和弦 `1.000 + 1.189 + 1.498`（暗、危险）
- 纯五度 `1.000 + 1.498`（空旷、史诗）
- 叠八度 `0.5 + 1.0`（厚）

### 6.5 同刻叠加配方（S 系列）
```mcfunction
# S01 挥空（一层）
playsound mob.shulker.shoot @a ~ ~ ~ 0.7 1.4

# S02 普通命中（低+中+高）
playsound mob.irongolem.hit @a ~ ~ ~ 0.4 0.9
playsound random.anvil_use  @a ~ ~ ~ 1.0 1.1
playsound random.orb        @a ~ ~ ~ 0.6 1.5

# S03 暴击（更重低频 + 低八度 bell 加厚）
playsound random.explode    @a ~ ~ ~ 0.7 0.7
playsound random.anvil_use  @a ~ ~ ~ 1.0 1.0
playsound random.orb        @a ~ ~ ~ 1.0 1.6
playsound note.bell         @a ~ ~ ~ 0.8 0.5

# S04 重击/破甲（只加低频厚度）
playsound random.anvil_land @a ~ ~ ~ 0.8 0.6
playsound mob.irongolem.hit @a ~ ~ ~ 0.9 0.5
playsound item.shield.block @a ~ ~ ~ 1.0 0.9

# S05 技能释放（冲击+龙吼+神圣感+纯五度）
playsound random.explode        @a ~ ~ ~ 1.0 0.6
playsound mob.enderdragon.growl @a ~ ~ ~ 0.8 1.0
playsound totem.use             @a ~ ~ ~ 0.9 1.0
playsound note.pling            @a ~ ~ ~ 0.7 1.000
playsound note.pling            @a ~ ~ ~ 0.7 1.498

# S06 大招爆发（远传层）
playsound ambient.weather.thunder @a ~ ~ ~ 4 0.8 0.5
playsound item.trident.thunder    @a ~ ~ ~ 1 1.0
playsound mob.enderdragon.growl   @a ~ ~ ~ 1 1.2
playsound beacon.activate         @a ~ ~ ~ 4 1.6 0.5
playsound random.explode          @a ~ ~ ~ 1 0.5

# S07 获得/开箱
playsound random.orb     @s ~ ~ ~ 1.0 1.0
playsound random.levelup @s ~ ~ ~ 0.6 1.2

# S08 受伤（闷、短、不加高频）
playsound random.hurt @s ~ ~ ~ 1.0 0.9
playsound random.fizz @s ~ ~ ~ 0.5 0.7

# S09 死亡（下沉，只低频）
playsound beacon.deactivate @s ~ ~ ~ 1.0 0.8
playsound note.bass         @s ~ ~ ~ 0.9 0.5

# S10 传送
playsound portal.travel @s ~ ~ ~ 0.6 1.4
playsound random.orb    @s ~ ~ ~ 0.6 1.8

# S11 警告（小二度不协和 + 嘶声）
playsound note.bass @s ~ ~ ~ 1.0 0.5
playsound note.bass @s ~ ~ ~ 0.8 0.53
playsound random.fizz @s ~ ~ ~ 0.5 0.7

# S12 UI 组
playsound random.click @s ~ ~ ~ 0.6 1.2   # 点击
playsound random.click @s ~ ~ ~ 0.5 1.6   # 选中切换
playsound random.orb   @s ~ ~ ~ 0.8 1.3   # 确认
playsound random.pop   @s ~ ~ ~ 0.7 0.8   # 取消
playsound note.bass    @s ~ ~ ~ 0.8 0.6   # 错误
```

### 6.6 循序渐进配方（P 系列，用 §3.5 时间轴 `fx_t`）

**P01 上行琶音（每 2 刻一音）**
```mcfunction
execute as @a[scores={fx_t=1}] at @s run playsound note.pling @s ~ ~ ~ 1 1.000
execute as @a[scores={fx_t=3}] at @s run playsound note.pling @s ~ ~ ~ 1 1.260
execute as @a[scores={fx_t=5}] at @s run playsound note.pling @s ~ ~ ~ 1 1.498
execute as @a[scores={fx_t=7}] at @s run playsound note.pling @s ~ ~ ~ 1 2.000
```

**P02 升级（先硬一下，3 刻后和弦铺开）**
```mcfunction
execute as @a[scores={fx_t=1}] at @s run playsound random.levelup @s ~ ~ ~ 1.0 1.0
execute as @a[scores={fx_t=1}] at @s run playsound note.bell @s ~ ~ ~ 0.8 0.5
execute as @a[scores={fx_t=4}] at @s run playsound note.pling @s ~ ~ ~ 0.9 1.260
execute as @a[scores={fx_t=4}] at @s run playsound note.pling @s ~ ~ ~ 0.9 1.498
execute as @a[scores={fx_t=4}] at @s run playsound note.pling @s ~ ~ ~ 0.9 2.000
```

**P03 蓄力（pitch 0.6 → 1.8 爬升，蓄满一声「叮」）**
```mcfunction
execute as @a[scores={fx_t=1}]  at @s run playsound note.harp @s ~ ~ ~ 0.8 0.60
execute as @a[scores={fx_t=5}]  at @s run playsound note.harp @s ~ ~ ~ 0.8 0.84
execute as @a[scores={fx_t=9}]  at @s run playsound note.harp @s ~ ~ ~ 0.8 1.12
execute as @a[scores={fx_t=13}] at @s run playsound note.harp @s ~ ~ ~ 0.9 1.50
execute as @a[scores={fx_t=17}] at @s run playsound note.harp @s ~ ~ ~ 1.0 1.80
execute as @a[scores={fx_t=19}] at @s run playsound random.orb @s ~ ~ ~ 1.0 1.9
```

**P04 连击阶梯（按分数选，不用时间轴）**
```mcfunction
execute as @a[scores={hit=1,combo=2..4}]   at @s run playsound note.chime @s ~ ~ ~ 0.8 1.00
execute as @a[scores={hit=1,combo=5..9}]   at @s run playsound note.chime @s ~ ~ ~ 0.9 1.26
execute as @a[scores={hit=1,combo=10..14}] at @s run playsound note.chime @s ~ ~ ~ 1.0 1.50
execute as @a[scores={hit=1,combo=15..}]   at @s run playsound note.chime @s ~ ~ ~ 1.0 2.00
execute as @a[scores={hit=1,combo=10..}]   at @s run playsound note.bell  @s ~ ~ ~ 0.8 0.5
```

**P05 倒计时（数字越小越高，最后一声最亮）**
```mcfunction
execute as @a[scores={cd3=3}] run playsound note.pling @s ~ ~ ~ 1 0.84
execute as @a[scores={cd3=2}] run playsound note.pling @s ~ ~ ~ 1 1.00
execute as @a[scores={cd3=1}] run playsound note.pling @s ~ ~ ~ 1 1.26
execute as @a[scores={cd3=0,go=1}] run playsound note.pling @s ~ ~ ~ 1 2.00
execute as @a[scores={cd3=0,go=1}] run playsound random.levelup @s ~ ~ ~ 0.7 1.2
```

**P06 大招三段：前摇 → 爆发 → 余响**
```mcfunction
execute as @a[scores={fx_t=1}]  at @s run playsound beacon.power @a ~ ~ ~ 1 0.6
execute as @a[scores={fx_t=6}]  at @s run playsound beacon.power @a ~ ~ ~ 1 0.9
execute as @a[scores={fx_t=10}] at @s run playsound beacon.power @a ~ ~ ~ 1 1.3
execute as @a[scores={fx_t=13}] at @s run playsound random.explode @a ~ ~ ~ 1 0.5
execute as @a[scores={fx_t=13}] at @s run playsound ambient.weather.thunder @a ~ ~ ~ 4 0.8 0.5
execute as @a[scores={fx_t=13}] at @s run playsound mob.enderdragon.growl @a ~ ~ ~ 1 1.2
execute as @a[scores={fx_t=20}] at @s run playsound note.chime @a ~ ~ ~ 0.4 1.8
execute as @a[scores={fx_t=26}] at @s run playsound note.bell @a ~ ~ ~ 0.25 1.9
```

**P07 心跳加速（血越低间隔越短）**
```mcfunction
execute as @a[scores={hp=11..20,beat=0}] run playsound mob.irongolem.hit @s ~ ~ ~ 0.5 0.5
execute as @a[scores={hp=6..10,beat=0}]  run playsound mob.irongolem.hit @s ~ ~ ~ 0.7 0.5
execute as @a[scores={hp=1..5,beat=0}]   run playsound mob.irongolem.hit @s ~ ~ ~ 0.9 0.6
execute as @a[scores={hp=11..20,beat=0}] run scoreboard players set @s beat 20
execute as @a[scores={hp=6..10,beat=0}]  run scoreboard players set @s beat 12
execute as @a[scores={hp=1..5,beat=0}]   run scoreboard players set @s beat 6
scoreboard players remove @a[scores={beat=1..}] beat 1
```

**P08 渐强铺底（3 级音量抬升）**
```mcfunction
execute as @a[scores={amb=1}]  at @s run playsound beacon.activate @s ~ ~ ~ 0.2 0.8
execute as @a[scores={amb=21}] at @s run playsound beacon.activate @s ~ ~ ~ 0.5 0.8
execute as @a[scores={amb=41}] at @s run playsound beacon.activate @s ~ ~ ~ 0.9 0.8
```

**P09 Boss 阶段切换（压低 → 警报 → 重击）**
```mcfunction
execute as @a[scores={fx_t=1}]  at @s run playsound note.bass @a ~ ~ ~ 1 0.5
execute as @a[scores={fx_t=5}]  at @s run playsound raid.horn @a ~ ~ ~ 1 0.9
execute as @a[scores={fx_t=14}] at @s run playsound random.explode @a ~ ~ ~ 1 0.6
execute as @a[scores={fx_t=14}] at @s run playsound mob.enderdragon.growl @a ~ ~ ~ 1 0.8
execute as @a[scores={fx_t=16}] at @s run playsound mob.irongolem.hit @a ~ ~ ~ 1 0.5
```

**P10 抽奖滚动（间隔变慢，最后重音）**
```mcfunction
execute as @a[scores={fx_t=1}]  run playsound random.click @s ~ ~ ~ 0.6 1.4
execute as @a[scores={fx_t=3}]  run playsound random.click @s ~ ~ ~ 0.6 1.4
execute as @a[scores={fx_t=5}]  run playsound random.click @s ~ ~ ~ 0.6 1.4
execute as @a[scores={fx_t=7}]  run playsound random.click @s ~ ~ ~ 0.6 1.4
execute as @a[scores={fx_t=10}] run playsound random.click @s ~ ~ ~ 0.7 1.2
execute as @a[scores={fx_t=14}] run playsound random.click @s ~ ~ ~ 0.8 1.0
execute as @a[scores={fx_t=19}] run playsound random.click @s ~ ~ ~ 0.9 0.8
execute as @a[scores={fx_t=25}] run playsound random.orb @s ~ ~ ~ 1.0 1.5
execute as @a[scores={fx_t=25}] run playsound random.levelup @s ~ ~ ~ 0.8 1.1
```

### 6.7 UI ↔ 音效映射

| UI 事件 | 声音 | 备注 |
|---|---|---|
| 选中切换 | `random.click` 0.5/1.6 | 最轻，别叠 |
| 确认 | `random.orb` 0.8/1.3 | 带上扬 |
| 取消/关闭 | `random.pop` 0.7/0.8 | 下沉 |
| 错误 | `note.bass` 0.8/0.6 | 低而短；严重加 `random.fizz` |
| 弹出面板/横幅 | `random.toast` | 与 title 同刻 |
| 升阶/升级 | P02 | 配 U17 |
| 倒计时 | P05 | 配 U18 |
| 能量满 | `note.chime` 1.0/1.9 + `beacon.power` 0.5/1.6 | 只播一次 |
| 冷却结束 | `random.orb` 0.5/1.9 | 极轻 |

### 6.8 限流与多人
- 战斗声 `@a ~ ~ ~`，UI 声 `@s`。
- 一次打击 3–4 条 × 多人 = 几十次音频事件：2–3 刻内不重复触发（`fx_cd` 触发置 3，每刻 −1，=0 才播）。
- 人多时降级只留中频。
- 远传层只给大事件（大招、Boss 阶段）。

### 6.9 旋律式复合音效（一个音色、按刻错开、半音换算 pitch）

来自实际服务器的写法：**同一个音色（如 `note.pling`）按固定刻间隔连播若干音，每个音只改 pitch**，听起来是一小段旋律 / 提示音。例（间隔 3 刻，共 6 音）：

```mcfunction
1刻  execute at @a run playsound note.pling @p ~~~ 1 0.353553
4刻  execute at @a run playsound note.pling @p ~~~ 1 1.334840
7刻  execute at @a run playsound note.pling @p ~~~ 1 0.899
10刻 execute at @a run playsound note.pling @p ~~~ 1 0.471937
13刻 execute at @a run playsound note.pling @p ~~~ 1 1.189207
16刻 execute at @a run playsound note.pling @p ~~~ 1 1.189207
```

**怎么读**：pitch = 2^(n/12)，反推 n = 12·log2(pitch)：0.353553→−18，1.334840→+5，0.899→约−2（标准值 0.890899，原值略偏），0.471937→−13，1.189207→+3。旋律即 `[-18,+5,-2,-13,+3,+3]`，每 3 刻一音。「N刻」是累计刻数（即每块的累计延迟）。

**两种落地**：① 链式延迟块（每块 Delay = 间隔刻数，适合固定旋律）；② 计数器时间轴（推荐，可限流 / 防重入，见 §3.5）。`execute at @a run playsound X @p ~~~` 在多人站得很近时 `@p` 可能取到别人，更稳的是 `execute as @a at @s run playsound X @s ~~~ 1 pitch`。

**半音 → pitch**（1.0 = 主音，每 +12 升一个八度）

| n | -24 | -18 | -13 | -12 | -7 | -5 | -2 | 0 | 2 | 3 | 4 | 5 | 7 | 9 | 12 | 16 | 19 | 24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pitch | 0.25 | 0.353553 | 0.471937 | 0.5 | 0.66742 | 0.749154 | 0.890899 | 1.0 | 1.122462 | 1.189207 | 1.259921 | 1.33484 | 1.498307 | 1.681793 | 2.0 | 2.519842 | 2.996614 | 4.0 |

**旋律配方**（起点，需耳听调整）

| 用途 | 半音列表 | 间隔刻 | 音色 |
|---|---|---|---|
| 参考资料提示音 | `-18 +5 -2 -13 +3 +3` | 3 | `note.pling` |
| 成功 / 获得 | `0 +4 +7 +12` | 2 | `note.pling` |
| 失败 / 错误（下行） | `+7 +3 0 -5` | 3 | `note.bass` |
| 警报 | `+5 0 +5 0 +5 0` | 2 | `note.bit` |
| 倒计时 3-2-1-开始 | `-2 0 +4 +12` | 20 | `note.pling` |
| 升级 | `-12 0 +7 +12 +16` | 2 | `note.harp` |
| 蓄力（逐渐加快） | `-12 -7 -2 +3 +7 +12 +16 +19` | 3→2→1 | `note.harp` |
| 开箱滚动（越来越慢） | 同一音 `+7` | 2,2,3,4,6,8 | `random.click` |

同一旋律再用另一个音色重播一遍（如 `note.bell` 低八度 n−12 音量 0.6、`note.chime` 高八度 n+12 音量 0.4）就是合奏。

```python
import math
def pitch(n): return round(2 ** (n / 12), 6)

def melody(obj, sound, notes, gap, start=1, vol=1.0):
    """notes: 半音列表；gap: int 或同长列表。递增与复位放链尾。"""
    gaps = gap if isinstance(gap, (list, tuple)) else [gap] * len(notes)
    t, out = start, []
    for n, g in zip(notes, gaps):
        out.append("execute as @a[scores={%s=%d}] at @s run playsound %s @s ~ ~ ~ %s %s" % (obj, t, sound, vol, pitch(n)))
        t += g
    out.append("scoreboard players add @a[scores={%s=1..}] %s 1" % (obj, obj))
    out.append("scoreboard players set @a[scores={%s=%d..}] %s 0" % (obj, t, obj))
    return out
```

参考资料里还出现 `block.beehive.shear`、`ui.loom.take_result`、`random.enderchestclosed`、`respawn_anchor.deplete`、`hit.amethyst_block`、`random.door_open`，它们**不在** lint 白名单里，先实机验证再用；`camera.take_picture` 在白名单内。音量写 17024 是「超大音量全图可闻」，等价远传层，只给大事件。

### 6.10 抽丝剥茧：逐层展开（声音与 UI 一层一层加信息）

思想：不要一次把所有东西砂过来，每一层只多给**一个新维度**，让玩家感觉「越剥越深」。

| 层 | 加了什么 | 例音色 | 音量 | 感觉 |
|---|---|---|---|---|
| L1 | 节拍（单音等距） | `random.click` | 0.5 | 有事要发生 |
| L2 | 低音垫底 | `note.bass` | 0.5 | 分量重了 |
| L3 | 主旋律 | `note.pling` | 0.8 | 有方向 |
| L4 | 和声（同刻三度 / 五度） | `note.harp` | 0.5 | 饱满 |
| L5 | 高频闪光 + 终音 | `note.chime` / `random.orb` | 0.6 | 到顶点 |

同刻最多响 3 层，层越多每层越轻（见 §6.2 音量预算）。两种展开方式：**按进度常驻叠加**（连击 / 能量越高开着的层越多，掉回去就剥掉一层）与**按时间一次性递进**（计数器 `fx_t` 每 N 刻加入一层）。

**按进度叠层生成器**
```python
def stack(score, period, layers):
    """layers: [(阈值, 音色, 音量, 半音n, [节拍刻...])]。分数>=阈值该层才响；fx_beat 在链尾递增并按 period 复位。"""
    out = []
    for thr, snd, vol, n, beats in layers:
        for b in beats:
            out.append("execute as @a[scores={%s=%d..,fx_beat=%d}] at @s run playsound %s @s ~ ~ ~ %s %s"
                       % (score, thr, b, snd, vol, round(2 ** (n / 12), 6)))
    out.append("scoreboard players add @a fx_beat 1")
    out.append("scoreboard players set @a[scores={fx_beat=%d..}] fx_beat 0" % period)
    return out

LAYERS = [
    (2,  "random.click", 0.5, 12,  [0, 10]),
    (5,  "note.bass",    0.5, -12, [0]),
    (10, "note.pling",   0.8, 0,   [0, 5, 10, 15]),
    (15, "note.harp",    0.5, 4,   [0, 10]),
    (25, "note.chime",   0.6, 12,  [5, 15]),
]
print("\n".join(stack("combo", 20, LAYERS)))   # 放循环命令方块；先 scoreboard players add @a fx_beat 0 建档
```

**按时间逐层进入（一次性事件，每 10 刻加入一层）**
```mcfunction
execute as @a[scores={fx_t=1}]  at @s run playsound random.click @s ~ ~ ~ 0.5 2
execute as @a[scores={fx_t=11}] at @s run playsound note.bass @s ~ ~ ~ 0.5 0.5
execute as @a[scores={fx_t=21}] at @s run playsound note.pling @s ~ ~ ~ 0.8 1
execute as @a[scores={fx_t=31}] at @s run playsound note.harp @s ~ ~ ~ 0.5 1.26
execute as @a[scores={fx_t=41}] at @s run playsound note.chime @s ~ ~ ~ 0.6 2
execute as @a[scores={fx_t=61}] at @s run playsound random.levelup @s ~ ~ ~ 1 1
```

**UI 同步剥茧：每层多显示一行**：第 k 行只在 `fx_t >= T_k` 时显示，前面的行保留、后面的逐步出现。
```mcfunction
execute as @a[scores={fx_t=1..60}] run titleraw @s actionbar {"rawtext":[
 {"text":"\n\n§6◁〖§f鉴定中§6〗▷\n§6▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={fx_t=11..}]"},{"text":"§6▎ §7品质 §e史诗\n"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={fx_t=21..}]"},{"text":"§6▎ §7类型 §f近战·穿刺\n"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={fx_t=31..}]"},{"text":"§6▎ §7技能 §f刺环·刺阵\n"}]}},{"text":""},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={fx_t=41..}]"},{"text":"§6▎ §7名称 §e§l终焉之刺\n"}]}},{"text":""},
 {"text":"§8[ 正在揭示… ]§r"}
]}
```
把它和上面的五条声音放进同一个 `fx_t` 时间轴：一行文字出现的那一刻，正好进来一层声音；`fx_t=61` 时发最终横幅（times → subtitle → title）并让 HUD 让位。

**原则**：每层只加一个维度；层越多每层越轻，顶点用明显更亮的终音收束；进层间隔约 10 刻最自然（太快像同刻叠加，太慢会分心）；常驻叠加要可逆，指标下降时自动剥掉一层。

### 6.11 旋律级音效目录（统一质量标准：刻 / 音色 / 音量 / 半音 n / pitch）

**质量标准**（参考资料里那段 `note.pling` 的写法）：每一个音效都要写成**一张事件表**，每行一个声音，列出 `刻`（累计刻数）、`音色`、`音量`、`半音 n`（相对主音的整数半音）、`pitch`（= 2^(n/12)，由生成器算，不手算）。设计时先写 n 和刻，再算 pitch。每个音效至少 2 个音且有**走向**（上行 = 成功 / 兴奋，下行 = 失败 / 沉低，小二度 = 不安 / 错误，跟几个八度 = 分量），而不是把几个声音堆在同一刻。

**写法套路**
1. 先定**走向和情绪**（上行 / 下行 / 摆动 / 不协和），再定音程：纯五度 `+7` 空旷、大三度 `+4` 明亮、小三度 `-3` 黑暗、小二度 `-1` 不安、八度 `±12` 分量。
2. 节奏：紧凑 2 刻（菜单、确认）、自然 3 刻（参考段的间隔）、拖慢 4–7 刻（死亡、余响）、加速（蓄力，间隔逐步缩短）。
3. 同刻可以叠多个声音（和弦 / 频谱叠加），但总量仍≲ 2.0。
4. 低于 0.5 和高于 2 的 pitch 在参考资料里都有用到（如 0.353553 = n -18），用来做低音垫底和顶点闪光，进服耳听确认。

**目录数据（生成器直接输出表格和命令）**
```python
import math
P, B, H, K, BE, CH, XY, BI, CB, FL = ("note.pling", "note.bass", "note.harp", "random.click", "note.bell",
    "note.chime", "note.iron_xylophone", "note.bit", "note.cow_bell", "note.flute")

# 分组 -> [(名称, 设计意图, [(刻, 音色, 音量, 半音n), ...])]
CAT = [
("UI 与系统", [
 ("点击", "一个主音 + 一个高八度气泡，极短", [(1, K, .6, 7), (1, "random.pop", .4, 12)]),
 ("确认", "上行：根音 → 纯五度 → 八度", [(1, P, 1, 0), (3, P, 1, 7), (5, P, 1, 12)]),
 ("取消", "下行：五度 → 根音 → 低四度", [(1, P, 1, 7), (3, P, 1, 0), (5, P, 1, -5)]),
 ("错误", "小二度不协和，重复一次像蜂鸣", [(1, B, 1, -5), (3, B, 1, -6), (6, B, 1, -5), (8, B, 1, -6)]),
 ("通知", "高位两音，下行，轻", [(1, CH, .7, 12), (4, CH, .6, 7)]),
 ("开关·开", "双击上行", [(1, K, .5, 7), (3, K, .5, 12)]),
 ("开关·关", "双击下行", [(1, K, .5, 12), (3, K, .5, 7)]),
 ("菜单打开", "快速上行琶音", [(1, H, .8, 0), (2, H, .8, 4), (3, H, .8, 7), (4, H, .8, 12)]),
 ("菜单关闭", "打开的镜像", [(1, H, .8, 12), (2, H, .8, 7), (3, H, .8, 4), (4, H, .8, 0)]),
 ("倒计时 3-2-1-开始", "每 20 刻一拍，逐拍抬升，最后跳八度加升级声", [(1, P, 1, -2), (21, P, 1, 0), (41, P, 1, 4), (61, P, 1, 12), (61, "random.levelup", .7, 3)]),
 ("成就解锁", "toast 弹出 → 琶音 → 收起", [(1, "ui.toast.in", .8, 0), (3, "random.levelup", .6, 2), (5, P, .9, 12), (8, P, .9, 16), (11, P, .9, 19), (40, "ui.toast.out", .5, 0)]),
]),
("近战与受击", [
 ("普通命中", "金属起音 + 闷响 + 高频火花", [(1, "random.anvil_use", .9, 3), (1, "mob.irongolem.hit", .5, -5), (2, XY, .5, 14)]),
 ("暴击", "命中 + 高低两个八度 bell + 余响 chime", [(1, "random.anvil_use", 1, 0), (2, BE, .8, -12), (2, BE, .8, 12), (3, "mob.irongolem.hit", .7, -9), (6, CH, .5, 19)]),
 ("重锤砸地", "撷击 → 碎石 → 爆 → 渣落 → 余震", [(1, "random.anvil_land", 1, -12), (2, "dig.stone", .8, -7), (3, "random.explode", .5, -9), (6, "dig.gravel", .5, -3), (9, B, .4, -24)]),
 ("格挡 / 弹反", "盾响 + 脆 bell；弹反成功才有尾部上扬", [(1, "item.shield.block", 1, 3), (2, BE, .7, 14), (4, "random.orb", .6, 19)]),
 ("击杀确认", "上行三音", [(1, "random.orb", .9, 7), (3, BE, .6, 12), (5, P, .6, 19)]),
 ("受伤", "闷：下沉 → 低音 → 嘶", [(1, "random.hurt", 1, -3), (2, B, .7, -12), (3, "random.fizz", .4, -5)]),
 ("死亡", "下行小调琶音，越拖越慢", [(1, B, .9, 0), (4, "beacon.deactivate", .6, -4), (4, B, .9, -3), (7, B, .9, -7), (11, B, .9, -12)]),
 ("复活", "上行：深音起步 → 大三 → 八度 → 升级声", [(1, H, .8, -12), (4, H, .8, 0), (7, H, .8, 7), (10, H, .8, 12), (13, H, .9, 16), (13, "random.levelup", .7, 0)]),
 ("心跳（低血量，每 20 刻循环）", "两下，第二下更轻", [(1, "mob.irongolem.walk", 1, -12), (5, "mob.irongolem.walk", .7, -13)]),
]),
("法术与技能", [
 ("蓄力（8 级爬升）", "间隔 3→2 加快，踏满一声高音", [(1, H, .8, -12), (4, H, .8, -7), (7, H, .8, -2), (10, H, .8, 3), (12, H, .8, 7), (14, H, .9, 12), (16, H, .9, 16), (18, H, 1, 19), (20, "random.orb", 1, 24)]),
 ("大招释放", "前摇三声低到高，13 刻后三层爆发，再接高频余响", [(1, "respawn_anchor.charge", 1, -12), (5, "respawn_anchor.charge", 1, -5), (9, "respawn_anchor.charge", 1, 0), (13, "random.explode", 1, -12), (13, "item.trident.thunder", 1, -3), (13, "mob.enderdragon.growl", .9, 5), (17, CH, .5, 12), (20, BE, .3, 19)]),
 ("火球", "点燃 → 呼吸 → 发射 → 爆炸 → 余燃", [(1, "fire.ignite", .6, -3), (3, "mob.blaze.breathe", .6, -5), (8, "mob.ghast.fireball", .9, 0), (14, "random.explode", .9, -3), (16, "fire.fire", .5, 0)]),
 ("寒霜新星", "冰晶五连音在高位来回，下面垫冻结低音", [(1, "random.glass", .9, 7), (2, XY, .6, 12), (3, B, .4, -12), (4, XY, .6, 16), (6, XY, .6, 19), (8, XY, .5, 12)]),
 ("雷击", "预兆两声上行 → 落雷 → 余电", [(1, "respawn_anchor.charge", .8, 7), (4, "respawn_anchor.charge", .8, 12), (9, "ambient.weather.thunder", 1, -2), (9, "item.trident.thunder", 1, 0), (12, "random.fizz", .5, 17)]),
 ("治疗", "柔和长笛上行 + 光点", [(1, FL, .7, 0), (3, FL, .7, 4), (5, FL, .7, 7), (7, FL, .7, 12), (8, "random.orb", .6, 16)]),
 ("增益 Buff", "高位两音上行 + 光环", [(1, P, .8, 7), (2, "beacon.power", .5, 5), (3, P, .8, 12)]),
 ("减益 / 诅咒", "下行小三度 + 沉响", [(1, B, .8, 0), (3, B, .8, -3), (4, "beacon.deactivate", .6, -4), (5, B, .8, -7)]),
 ("传送（起点 + 落点）", "起点：吸入上扬；落点：低位出现 + 高音确认", [(1, "random.pop", .6, 12), (2, "portal.travel", .5, 5), (8, "portal.travel", .5, -7), (9, "random.orb", .7, 19)]),
 ("弓：拉弦→放箭→命中", "拉弦三声逐步抬高，放箭，命中", [(1, "crossbow.loading.start", .5, 0), (6, "crossbow.loading.middle", .5, 3), (12, "crossbow.loading.end", .6, 7), (14, "random.bow", .8, 0), (17, "random.bowhit", .8, -2)]),
]),
("奖励与经济", [
 ("升级", "六级上行大音阶 + 升级声", [(1, P, 1, 0), (3, P, 1, 4), (5, P, 1, 7), (7, P, 1, 12), (9, P, 1, 16), (12, P, 1, 19), (12, "random.levelup", .8, 0)]),
 ("任务完成", "高位起步的上行四音，末端低八度 bell 垫底", [(1, P, .9, 7), (4, P, .9, 12), (7, P, .9, 16), (10, BE, .6, -12), (10, P, .9, 19)]),
 ("任务失败", "半音下滑，越慢越沉", [(1, B, .9, 0), (4, B, .9, -1), (7, B, .9, -5), (10, B, .9, -12)]),
 ("购买成功", "两下硬币感", [(1, "random.orb", .8, 4), (3, CB, .5, 12)]),
 ("余额不足", "低位双响，像摇头", [(1, B, .9, -5), (4, B, .9, -5), (6, "mob.villager.no", .6, 0)]),
 ("稀有开箱", "开箱声 + 五连上行 + 低八度 bell 余响", [(1, "random.chestopen", .8, 0), (4, P, .8, 0), (6, P, .8, 4), (8, P, .8, 7), (10, P, .8, 12), (12, BE, .6, -12), (12, P, .9, 16)]),
]),
("Boss 与氛围", [
 ("Boss 登场", "极低一声 → 号角 → 吼声 + 爆炸 → bell 沉响", [(1, B, 1, -24), (12, "raid.horn", 1, -5), (24, "mob.enderdragon.growl", 1, -7), (24, "random.explode", .8, -12), (27, BE, .6, -12)]),
 ("Boss 狂暴", "五拍警报：高—低—高—低—高，最后重击", [(1, BI, .8, 5), (3, BI, .8, 0), (5, BI, .8, 5), (7, BI, .8, 0), (9, BI, .8, 5), (12, "random.explode", 1, -12)]),
 ("Boss 倒下", "吼声 → 爆 → 沉寂 → 胜利 chime", [(1, "mob.enderdragon.growl", 1, -9), (10, "random.explode", 1, -12), (20, "beacon.deactivate", 1, -9), (40, CH, .6, 7)]),
 ("地下城底噪（每 200 刻）", "洞穴声 + 远处低音，音量很小", [(1, "ambient.cave", .4, -3), (60, B, .2, -24)]),
]),
]

def pitch(n): return round(2 ** (n / 12), 6)

def table(rows):
    lines = ["| 刻 | 音色 | 音量 | 半音 n | pitch |", "|---|---|---|---|---|"]
    for t, s, v, n in sorted(rows):
        lines.append("| %d | `%s` | %s | %+d | %s |" % (t, s, v, n, ("%.6f" % pitch(n)).rstrip("0").rstrip(".")))
    return "\n".join(lines)

def commands(rows, obj="fx_t"):
    """时间轴命令：触发时 obj=1；递增与复位放链尾。每个效果用独立计时分数。"""
    out = ["execute as @a[scores={%s=%d}] at @s run playsound %s @s ~ ~ ~ %s %s" % (obj, t, s, v, pitch(n))
           for t, s, v, n in sorted(rows)]
    last = max(r[0] for r in rows)
    out += ["scoreboard players add @a[scores={%s=1..}] %s 1" % (obj, obj),
            "scoreboard players set @a[scores={%s=%d..}] %s 0" % (obj, last + 1, obj)]
    return out
```

**目录走向速查**（写新音效时对照已有的选定音程）

| 情绪 | 音程走向 | 例 |
|---|---|---|
| 成功 / 确认 / 升级 | 上行大三和弦 / 纯五度 / 八度 | 确认 `0 +7 +12`，升级 `0 +4 +7 +12 +16 +19` |
| 取消 / 关闭 | 下行 | `+7 0 -5` |
| 错误 / 警告 | 小二度不协和、重复 | `-5 -6 -5 -6` |
| 死亡 / 失败 | 小调下行、越拖越慢 | `0 -3 -7 -12` |
| 蓄力 | 逐级爬升且间隔缩短 | `-12 -7 -2 +3 +7 +12 +16 +19` |
| 压迫 / 登场 | 极低音 + 号角 + 低八度沉响 | `-24 / -5 / -7 / -12` |
| 紧迫警报 | 两音来回、间隔 2 刻 | `+5 0 +5 0 +5` |

### 6.12 单个音效的方块预算（每组 ≤20 块）与增强配方

一个音效 = **按钮链 + 时间轴链**，合计预算 20 命令方块（用户可改，按需缩放）。

| 部分 | 方块数 | 内容 |
|---|---|---|
| 按钮链（impulse） | 2 | `scoreboard players set @p <fx> 1` + `scoreboard players set @p sd_ban <末帧+30，≤60>`（让 HUD 让位） |
| 时间轴链（repeat） | ≤18 | 各帧命令 + 链尾 2 块（`add` 递增、`set 0` 复位） |

额度分配顺序（先保骨架，再加料，超预算就舍弃后面的）：
1. **骨架音符**（目录里的行，最多约 9 条）——不可删。
2. **字幕**（1 块，第 1 刻）：`titleraw @s actionbar` 显示效果名 + 设计意图 + 分隔线；靠 `sd_ban` 不被 HUD 盖掉。
3. **回声层**（≤4 块）：音量 ≥0.8 的 `note.*` 音符，在 **+2 刻**、**×0.35 音量**、**n−12（低八度）** 再响一次，听感更厚但不增加同刻音量。
4. **粒子**（1–2 块）：落在最响那一刻；近战 `critical_hit_emitter`，法术 `enchanting_table_particle`，奖励 `totem_particle`，Boss `huge_explosion_emitter`，收尾补 `villager_happy` / `soul_particle`。粒子只用 lint 白名单。
5. **轻震动**（1 块）：`camerashake add @s 0.25 0.15 positional`（近战）、`0.2 0.3`（法术）、`0.5 0.8`（Boss）；UI 音效不加。

生成时写一条断言：`len(时间轴命令) + 按钮命令数 <= 预算`，超了就 fail，不要靠肉眼数。

**层数（楼层）**：一层一条链占一行，100 条链会把深度顶到 100+，超出 64×64×100。给链设 `level`（`1 + (k-1)//14` 分 3 层），深度从 109 降到 31。按钮放在高层也能用（创造模式飞行）。

**演示结构的编排**：初始化（建所有计分项 + `add @a x 0` + 说明卡）→ 时钟（`ban` 递减，HUD 仅 `ban=0` 时画）→ HUD 调节按钮 → 联动演示（升阶横幅 / 鉴定揭示 / 倒计时 / 蓄力条 / 结算卡片 / Boss 登场 / 菜单切换）→ 每个音效一组按钮 + 时间轴。每个演示各用自己的计数器。

---

## 7. 联动配方（UI + 声音 + 粒子/震动同刻对齐）

触发时 `fx_t=1`，各帧按刻写命令。

**R01 升阶**
```mcfunction
execute as @a[scores={fx_t=1}] run title @s times 3 22 8
execute as @a[scores={fx_t=1}] run titleraw @s subtitle {"rawtext":[{"text":"§7双刺 §8→ §6刺环"}]}
execute as @a[scores={fx_t=1}] run titleraw @s title {"rawtext":[{"text":"§c◁§7།§e§l 阶位提升 §7།§c▷"}]}
execute as @a[scores={fx_t=1}] at @s run playsound random.levelup @s ~ ~ ~ 1.0 1.0
execute as @a[scores={fx_t=1}] at @s run playsound note.bell @s ~ ~ ~ 0.8 0.5
execute as @a[scores={fx_t=1}] at @s run particle minecraft:totem_particle ~ ~1 ~
execute as @a[scores={fx_t=1}] at @s run camerashake add @s 0.3 0.4 positional
execute as @a[scores={fx_t=4}] at @s run playsound note.pling @s ~ ~ ~ 0.9 1.260
execute as @a[scores={fx_t=4}] at @s run playsound note.pling @s ~ ~ ~ 0.9 1.498
execute as @a[scores={fx_t=4}] at @s run playsound note.pling @s ~ ~ ~ 0.9 2.000
```

**R02 技能就绪（用上一刻值检测 1→0）**
```mcfunction
execute as @a[scores={cd_q=0,cd_q_prev=1..}] run playsound random.orb @s ~ ~ ~ 0.5 1.9
execute as @a[scores={cd_q=0,cd_q_prev=1..}] run titleraw @s actionbar {"rawtext":[{"text":"§a✔ §fQ·斩 §7已就绪"}]}
scoreboard players operation @a cd_q_prev = @a cd_q
```

**R03 倒计时开场（每 20 刻一拍）**
```mcfunction
execute as @a[scores={fx_t=1}]  run titleraw @s title {"rawtext":[{"text":"§e§l３"}]}
execute as @a[scores={fx_t=1}]  run playsound note.pling @s ~ ~ ~ 1 0.84
execute as @a[scores={fx_t=21}] run titleraw @s title {"rawtext":[{"text":"§6§l２"}]}
execute as @a[scores={fx_t=21}] run playsound note.pling @s ~ ~ ~ 1 1.00
execute as @a[scores={fx_t=41}] run titleraw @s title {"rawtext":[{"text":"§c§l１"}]}
execute as @a[scores={fx_t=41}] run playsound note.pling @s ~ ~ ~ 1 1.26
execute as @a[scores={fx_t=61}] run titleraw @s title {"rawtext":[{"text":"§a§l◁ 开　始 ▷"}]}
execute as @a[scores={fx_t=61}] run playsound note.pling @s ~ ~ ~ 1 2.00
execute as @a[scores={fx_t=61}] run playsound random.levelup @s ~ ~ ~ 0.7 1.2
```

**R04 Boss 阶段切换**
```mcfunction
execute as @a[scores={fx_t=1}]  run title @s times 3 30 10
execute as @a[scores={fx_t=1}]  run titleraw @s subtitle {"rawtext":[{"text":"§7它开始认真了"}]}
execute as @a[scores={fx_t=1}]  run titleraw @s title {"rawtext":[{"text":"§4§l◁ 第二阶段 ▷"}]}
execute as @a[scores={fx_t=1}]  at @s run playsound note.bass @a ~ ~ ~ 1 0.5
execute as @a[scores={fx_t=5}]  at @s run playsound raid.horn @a ~ ~ ~ 1 0.9
execute as @a[scores={fx_t=14}] at @s run playsound random.explode @a ~ ~ ~ 1 0.6
execute as @a[scores={fx_t=14}] at @s run camerashake add @s 0.8 0.6 positional
execute as @a[scores={fx_t=14}] at @s run particle minecraft:huge_explosion_emitter ~ ~1 ~
```

**R05 稀有获得**
```mcfunction
execute as @a[scores={fx_t=1}] run tellraw @s {"rawtext":[{"text":"\n§6◁〖§f稀有获得§6〗▷\n§6▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n§6▎ §7物品 §e终焉之刺\n§6➤ §8[§f已放入背包§8]\n"}]}
execute as @a[scores={fx_t=1}] at @s run playsound note.pling @s ~ ~ ~ 1 1.000
execute as @a[scores={fx_t=3}] at @s run playsound note.pling @s ~ ~ ~ 1 1.260
execute as @a[scores={fx_t=5}] at @s run playsound note.pling @s ~ ~ ~ 1 1.498
execute as @a[scores={fx_t=7}] at @s run playsound note.pling @s ~ ~ ~ 1 2.000
execute as @a[scores={fx_t=7}] at @s run playsound random.levelup @s ~ ~ ~ 0.6 1.2
```

---

## 8. 生成器（别手写 JSON）

```python
import json, re

def J(parts):
    return json.dumps({"rawtext": parts}, ensure_ascii=False, separators=(",", ":"))
def txt(s): return {"text": s}
def score(obj, name="@s"): return {"score": {"name": name, "objective": obj}}

def cond(selector, node):
    """%%2 条件显示，自带兜底；node 只会显示一个参数。"""
    return [{"translate": "%%2", "with": {"rawtext": [{"selector": selector}, node]}}, txt("")]

def tiered(obj, states, base=0):
    """states[i] = 数值 base+i 时显示的字符串/节点。>8 档自动嵌套。"""
    if len(states) <= 8:
        m, texts = len(states), list(states)
        caps = [base + i for i in range(m - 1)] + [99]
    else:
        m = 8
        texts = list(states[:7]) + [tiered(obj, states[7:], base + 7)]
        caps = [base + i for i in range(7)] + [99]
    sels = [{"selector": "@s[scores={%s=..%d}]" % (obj, c)} for c in caps]
    nodes = [t if isinstance(t, dict) else txt(t) for t in texts]
    return {"translate": "%%%d" % (m + 1), "with": {"rawtext": sels + nodes}}

def bar_color(n, total=10):
    r = n / total
    return "§4" if r <= .2 else "§c" if r <= .4 else "§6" if r <= .6 else "§e" if r <= .8 else "§a"

def bar10(obj):  # 0–10，11 档 = %%9 套 %%5
    return tiered(obj, ["%s%s§8%s§r" % (bar_color(n), "▰" * n, "▰" * (10 - n)) for n in range(11)])

hud = J([txt("§b* §7>> §7能量 "), bar10("bar"), txt(" §f"), score("energy")])
print("execute as @a run titleraw @s actionbar " + hud)
```

**自检**（嵌套最容易错位，必跑）：
```python
def evalt(node, v):
    w = node["with"]["rawtext"]
    sels = [x for x in w if "selector" in x]; texts = [x for x in w if "selector" not in x]
    k = sum(1 for s in sels if v <= int(re.search(r"\.\.(\d+)", s["selector"]).group(1)))
    idx = int(node["translate"][2:]) - k
    if idx < 1: return ""
    t = texts[idx - 1]
    return evalt(t, v) if "translate" in t else t["text"]
for v in range(11): print(v, evalt(bar10("bar"), v))   # 应 0..10 格递增
```

**时间轴生成 / 和弦**：
```python
def timeline(obj, frames, who="@a"):
    """frames: {k: [命令...]}。递增与复位放最后，保证第 1 帧只执行一次。"""
    out = ["execute as %s[scores={%s=%d}] at @s run %s" % (who, obj, k, c) for k in sorted(frames) for c in frames[k]]
    end = max(frames) + 1
    out.append("scoreboard players add %s[scores={%s=1..}] %s 1" % (who, obj, obj))
    out.append("scoreboard players set %s[scores={%s=%d..}] %s 0" % (who, obj, end, obj))
    return out

def chord(sound, root, semitones, vol=0.8):
    return ["playsound %s @s ~ ~ ~ %s %.3f" % (sound, vol, root * 2 ** (n / 12)) for n in semitones]
# 大三 (0,4,7)  小三 (0,3,7)  纯五度 (0,7)
```

---

## 9. 检查清单

**UI**
- [ ] 通道选对；同刻无两通道互相覆盖（横幅计时器让 HUD 让位）
- [ ] 横幅顺序 = times → subtitle → title；rawtext 是顶层
- [ ] 主色 1 + 辅色 1 + 强调 1；资源色与 §2.2 一致；无扩展色
- [ ] 同界面一种括号/竖条/分隔线；三段式齐全；有操作提示
- [ ] 单行宽度在预算内；全角半角对齐；块字符已在目标设备看过
- [ ] 每个 `%%2` 有 `{"text":""}` 兜底；文字与数值分块；互斥分支不会同时出现
- [ ] 分档条用 `tiered()` 生成并用 `evalt()` 逐档模拟

**音效**
- [ ] 名字在 §6.3 / lint 白名单；无 Java 名
- [ ] 先频谱、再时间、最后音高；同刻总量 ≲ 2.0；中频 1.0，低频压低
- [ ] 轻事件 1 层、普通 2–3 层、重事件 4–6 层；挥空不加低频、受伤不加高频
- [ ] 时间轴递增在链尾；有复位；防重入
- [ ] 每个音效组的方块数 ≤ 预算（按钮 2 + 时间轴），生成脚本里有断言
- [ ] 层数合理：链多时用 `level` 分层，包围盒 ≤ 64×100×64（`check_bounds.py`）
- [ ] 回声 / 粒子 / 震动只在预算有余量时加；粒子名在白名单内
- [ ] 每个音效都有「刻 / 音色 / 音量 / 半音 n / pitch」表，至少 2 个音且有走向，pitch 由生成器算，不手算
- [ ] 旋律式用半音列表 + `melody()` 生成，不手算 pitch；逐层展开每层只加一个维度、同刻≤ 3 层
- [ ] 战斗声 `@a ~ ~ ~`，UI 声 `@s`；远传层仅大事件；多人有限流
- [ ] 同一事件永远同一种声音（§6.7）

**常见坑**

| 现象 | 原因 | 处理 |
|---|---|---|
| 横幅闪一下就没 | HUD 同刻覆盖 | §5 横幅计时器 |
| 副标题不显示 / 错位 | 没配 title，或先发了 title | 顺序 times → subtitle → title |
| 条件文字不出现 | 选择器没命中 / 缺兜底 | 单独验证选择器；补兜底 |
| 冷却数字不显示 | 文字与 score 同一个 `%%2` | 拆两块 |
| 分档条错位 | 选择器/候选数不符 | `tiered()` + `evalt()` |
| 动作栏一闪而过 | 没每刻刷新 | 放循环命令方块 |
| 第 1 帧偶尔不响 | 递增在别的链 | 递增放链尾 |
| 声音一坨 | 全部同刻 | 高频延后 1–2 刻，余响 3–5 刻 |
| 声音塑料 | 单层 | 补低/高频或叠八度 |
| 声音刺耳/糊 | 总量过大 | 低频 0.4–0.7，总量 ≤ 2 |
| 全图都在响 | 滥用最小音量 | 仅大事件 |
| 改名后没声音 | 名字错不报错 | 对照白名单 |