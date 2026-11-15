# 存档格式与自检（0~7 章）

> 写 `.mcworld` / `.mcstructure` 的字节格式、子区块与方块实体、17 项自检。
**什么时候读**：自己生成或修存档文件、校验报错看不懂、加新方块类型。

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

---

## 0. 交付路线与硬约束

路线只有两条（结构文件 / 世界存档），见「第一部分 · 一、两条路线」。  
行为包路线已删除。

### 硬约束（违反即返工）

1. **不用 `.mcfunction` / 函数 / `tick.json`** —— "每刻运行"用**循环命令方块**
2. **不用 tag** —— 状态一律用计分板布尔位，建档时 `add @a 位 0` 兜底
3. **断链 = 三段式** —— 检测（无条件）→ 连接块（**有条件**）→ 重置块（无条件）→ 业务（**全部无条件**）。断开由外部同类型 `setblock` 打 **`[1]`** 改朝向完成（第 8 章）
4. `/damage` `/camera` `/hud` `/structure` 已实装，可直接用
5. **聊天栏关灰字、方块控制台保留输出**（见第 10 章）

---

## 1. `.mcworld` 容器

`.mcworld` 就是一个 zip，**必须 9 项**：

```
level.dat
levelname.txt
world_behavior_packs.json
world_resource_packs.json
db/CURRENT
db/LOCK
db/LOG
db/MANIFEST-000000
db/000001.log
```

❗ `level.dat` 必须在 **zip 根**，不能嵌套 `world/` 目录。嵌套了世界就不出现在列表里。

`world_behavior_packs.json` / `world_resource_packs.json` 写 `[]` 即可——  
本 skill 不用行为包，这两个文件只是让世界能正常加载。

---

## 2. `level.dat`

```
0A 00 00 00     ← uint32 版本号 10，小端
XX XX XX XX     ← uint32，后面 NBT 的字节数
0A 00 00 ...    ← TAG_Compound，无名，小端 NBT
```

❗ **不能用 gzip 压缩**。压缩了导入直接失败。

改造时只需要动几个键：

| 键                      | 值                         |
| ---------------------- | ------------------------- |
| `LevelName`            | 世界显示名                     |
| `SpawnX/Y/Z`           | 出生点                       |
| `GameType`             | 0 生存 / 1 创造 / 2 冒险 / 3 旁观 |
| `commandsEnabled`      | 1                         |
| `commandblocksenabled` | 1                         |
| `cheatsEnabled`        | 1                         |
| `FlatWorldLayers`      | `""`（地形全由 db 决定）          |

真实存档的 `level.dat` 有 120 个键，**不要从零构造**，拿一份真实存档当模板改。  
（本项目的 `_template.mcworld` 就是干这个的。）

---

## 3. LevelDB 日志记录

`db/000001.log` 是 LevelDB 的预写日志。每条记录的字节布局：

```
seq(uint64, 8) + batch(uint32, 4) + type(uint8, 1)
  + varint(keylen) + key
  + varint(vallen) + val
```

❗ **key 从偏移 13 + varint 开始，不是 8**。  
这一条错了，解析器会把 `seq` 的低字节当成 key 的第一个字节，全盘错位。

### 记录类型与 key

| type   | key 结构                      | 内容                      |
| ------ | --------------------------- | ----------------------- |
| `0x2f` | `x(4) + z(4) + 0x2f + y(1)` | 子区块（地形与方块）              |
| `0x31` | `x(4) + z(4) + 0x31`        | 方块实体列表                  |
| `0x2c` | `x(4) + z(4) + 0x2c`        | 区块版本                    |
| `0x36` | `x(4) + z(4) + 0x36`        | `FinalizedState`（int 2） |

### 32KB 分片

❗ **单条记录超过 32KB 必须拆成 FIRST / MIDDLE / LAST 分片**，否则判损坏、导入失败。  
方块实体动辄 50–80KB，必然触发。

```
片头: 0x01/0x02/0x04 + uint16 长度 + 数据   （块内最后一片用 0x04）
```

### MANIFEST（VersionEdit）

同样是日志格式，payload 是若干 `varint tag + 值`。真实存档是**两条**记录：

```
记录1: 1=comparator("leveldb.BytewiseComparator")  2=log 0  3=next 1  4=last_seq 0
记录2:                                             2=log 1  3=next 2  4=last_seq 0
```

只写一条（把三者合并）在某些客户端上会被判无效，照抄两条最稳。

---

## 4. 子区块与方块实体

### 4.1 子区块

```
版本(1) + 层数(1) + y(1) + [ 每层 ... ]
```

每层：

```
storageVersion(1) + 索引数组 + 调色板计数(uint32,4) + 调色板 NBT 数组
```

- `bits = storageVersion >> 1`
- 每格 `bits` 位，每 uint32 装 `32 / bits` 格
- **索引数组在前，调色板在后**（顺序反了必崩）
- 调色板第 0 项 **必须是 `minecraft:air`**，否则整片变石头

❗ **`bits == 0` 是单值层**：只有 `sv` 一个字节 + **一个完整的 NBT 调色板条目**。  
只跳 1 字节的话，后面的字节全错位（这是最隐蔽的一个坑）。

### 4.2 方块实体

key = `x(4) + z(4) + 0x31`，值是 NBT 复合标签的串联。

命令方块的方块实体：

```json
{"id":"CommandBlock",
 "x":8,"y":-60,"z":7,
 "Command":"say hi",
 "auto":1,
 "conditionalMode":0,
 "conditionMet":1,
 "ExecuteOnFirstTick":0,
 "powered":0,
 "TickDelay":0,
 "TrackOutput":1,
 "LastOutput":"",
 "LastOutputParams":[],
 "LastExecution":0,
 "SuccessCount":0,
 "CustomName":"",
 "Version":39}
```

❗ `x/y/z` 必须是**世界坐标**，不是区块局部坐标。用局部坐标跨区块时会挂错位置。

### 4.3 方块状态的类型

| 状态                             | 类型          | 说明                                |
| ------------------------------ | ----------- | --------------------------------- |
| `facing_direction`             | **TAG_Int** | 0 下 / 1 上 / 2 北 / 3 南 / 4 西 / 5 东 |
| `conditional_bit`              | TAG_Byte    | 0 无条件 / 1 有条件                     |
| `button_pressed_bit` 等 `*_bit` | TAG_Byte    |                                   |


❗ 写成 Byte 时游戏**不报错**，直接回落成 0（朝下）。  
表现是"所有命令方块都朝下、链全断、按钮吊顶"。

### 4.4 `FinalizedState`

❗ 每个区块必须写 `0x36` → `int 2`。不写的话区块被判"未生成"，  
游戏重新生成地形，你放的方块全没。

---

## 5. `.mcstructure` 结构文件

### 5.1 结构

```json
{
  "format_version": 1,
  "size": [x, y, z],
  "structure": {
    "block_indices": [ [方块层...], [水层...] ],
    "entities": [],
    "palette": {
      "default": {
        "block_palette": [ {"name":"...","states":{...},"version":...}, ... ],
        "block_position_data": { "<索引>": {"block_entity_data": {...}} }
      }
    }
  },
  "structure_world_origin": [x, y, z]
}
```

- 索引公式：**`x * sizeY * sizeZ + y * sizeZ + z`**（x 最外层）
- 空气写 **-1**，不是调色板下标
- 第二层（水层）没有方块时整层填 -1
- 命令方块挂在 `block_position_data`，**不放在 `entities` 里**
- `block_entity_data` 里的 `x/y/z` 置 0（位置由索引决定）

### 5.2 文件头：不加

❗ **`.mcstructure` 前面不加任何头。** NBT 直接从 `0a 00 00`  
（TAG_Compound + 2 字节空名）开始。

曾经试过在 NBT 前加 8 字节 `int32 version=10 + int32 size`，实测会被判"文件损坏"。  
`mcworld_to_structure.py` 的 `--header` 参数保留但空转，只为兼容旧命令。

### 5.3 方块状态的 NBT 类型

**必须和游戏里注册的类型一致，不能一律写 INT：**

| 状态                                                                    | 类型         | 写错的后果                     |
| --------------------------------------------------------------------- | ---------- | ------------------------- |
| `conditional_bit` / `button_pressed_bit` / `infiniburn_bit` 等 `*_bit` | **BYTE**   | 状态非法 → **整个结构加载失败**       |
| `facing_direction`                                                    | **INT**    | 写成 BYTE 会静默回落成 0（朝下），链直接断 |
| `dirt_type` / `sand_type` 等枚举                                         | **STRING** | 加载失败                      |

导出器里用一张 `STATE_TYPES` 表按状态名查类型，不要靠值的 Python 类型猜。

### 5.4 命令方块的 `conditionalMode`

结构里 `block_entity_data.conditionalMode` 要和方块的 `conditional_bit` **一致**，  
否则粘贴后条件行为可能不对。

---

## 6. 自检 17 项

**原则：全部从文件回读，不看生成时的内存数据。** 内存里对不代表文件里对。

| #  | 检查项                    | 判据                                                           | 不过的后果                |
| -- | ---------------------- | ------------------------------------------------------------ | -------------------- |
| 1  | 包结构                    | 9 项齐全，`level.dat` 在 zip 根                                    | 世界不出现在列表             |
| 2  | `level.dat` 头部         | `version=10`，声明长度 = 实际长度，NBT 未压缩                             | 导入失败                 |
| 3  | 关键键                    | `commandsEnabled`/`commandblocksenabled`/`cheatsEnabled` = 1 | 命令不可用                |
| 4  | db 五件套                 | `CURRENT`/`LOCK`/`LOG`/`MANIFEST`/`000001.log`               | 存档损坏                 |
| 5  | CRC32C                 | 每条记录校验通过                                                     | 记录被丢弃                |
| 6  | 子区块字节消费                | 解析完恰好等于总长                                                    | 方块错位 / 丢块            |
| 7  | 调色板首项                  | `minecraft:air`                                              | 全图变石头                |
| 8  | `facing_direction` 类型  | **TAG_Int**                                                  | 方块朝下、链断开             |
| 9  | 实体坐标                   | 世界坐标，`(x,z)` 不重复                                             | 实体挂错位置               |
| 10 | 无 `function` / 无 `tag` | 命令里搜不到                                                       | 网易服不执行               |
| 11 | JSON 合法                | `json.loads` 通过，且无真换行                                        | HUD 静默不显示            |
| 12 | 链末端数                   | = 链数（init + 各功能链 + 面板组数）                                     | 链断或互相触发              |
| 13 | 条件位分布                  | `conditionalMode=1` 的块数 **= 功能链数**（每条链只有连接块）                 | 全条件位会连坐 / 一个都没有则每刻全跑 |
| 14 | 控制台可查                  | 全部方块 `TrackOutput=1`                                         | 出问题无法定位              |
| 15 | 聊天栏灰字                  | 6 条 gamerule 齐全                                              | 系统提示漏进聊天栏            |
| 16 | 空闲条数                   | **循环块个数 = 功能链数，≤3 条**                                        | 全塞一条链                |
| 17 | `setblock` 只改朝向        | 全部是 `chain_command_block[...]` → 同类型，没有 `... air` / 跨类型      | 换类型会重建方块、擦掉 NBT      |

### 实现要点

**检查 6**：子区块是 `版本(1) + 层数(1) + y(1) + [每层...]`，  
`bits = storageVersion >> 1`，`bits == 0` 是单值层（`sv` + 一个完整 NBT 条目）。

**检查 8**：`facing_direction` 必须是 `TAG_Int`。写 Byte 时游戏**不报错**，  
直接回落成 0（朝下）。

**检查 12**：对每个命令方块，看它朝向所指的下一格有没有命令方块。没有 = 链末端。

**检查 16**：数循环块个数。三段式断链下，**空闲开销 = 检测块个数**——  
检测失败时后面的块根本不被触发。循环块个数应等于功能链数。

**检查 17**：全图搜 `setblock` 且目标为 `chain_command_block`。有就是错的：  
`setblock` 只给方块状态会重建方块、清空方块实体，下一格的 `Command` 直接消失。

---

# 第三部分 · 执行机制

## 7. 三种命令方块

| 方块           | 颜色 | 触发                      | 用途      |
| ------------ | -- | ----------------------- | ------- |
| 脉冲 `impulse` | 橙  | 红石一次                    | 初始化链、按钮 |
| 循环 `repeat`  | 紫  | 有信号 / 始终活动 → **20 次/秒** | 主循环，链首  |
| 链 `chain`    | 绿  | 前一块执行完                  | 链身      |

- `auto=1`（始终活动）让循环块不用红石信号就跑
- 链方块必须**紧挨着指向前一块**，朝向由 `facing_direction` 决定
- 一个循环块驱动一整条链，这就是"每刻运行"的实现方式

---
