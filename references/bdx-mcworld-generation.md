# 生成可导入的 BDX / MCWorld

> 目标：AI 不只会写指令，还能把指令变成 Minecraft 能导入的 **`.bdx`** 或 **`.mcworld`**。
> 核心原则：**BDX 是命令流，不是 NBT；MCWorld 是 level.dat + LevelDB，不要手写 LevelDB。**

## 1. BDX 的真实格式

```
BD@ + brotli( "BDX" + 0x00 + 0x00 + command-stream )
```

- 前 3 字节固定 `BD@`。
- 后面是 **brotli 压缩** 的流；不是 gzip/zip。
- 解压后：
  - `BDX`（3 字节）
  - 一个 `0x00`（空 author）
  - 一个额外的 `0x00`（解析器会跳过）
  - command-stream，最后以 `ID 88`（Terminate）结束。
- **没有 NBT 头**；方块和命令方块都是 command-stream 里的“放置命令”。
- **author 建议保持空**：非空 author 在 AuroraStructure 的 BDX 读取器上实测会被判“文件无效”；脚本为了兼容直接不写 author。

### 1.1 命令流基础

| ID | 命令 | 载荷 |
|---:|---|---|
| 1 | `CreateConstantString` | UTF-8 字符串 + `0x00`；按出现顺序分配 string ID 0,1,2... |
| 21 | `AddInt32X` | int32 BE |
| 23 | `AddInt32Y` | int32 BE |
| 25 | `AddInt32Z` | int32 BE |
| 27 | `PlaceBlockWithCommandBlockData` | 见下 |
| 88 | `Terminate` | 无 |

- 读取器从 `(0,0,0)` 开始；每个方块前先用 AddInt32X/Y/Z 移动到目标坐标。
- 只写需要的轴；dx=0 不发命令。
- `PlaceBlockWithCommandBlockData` 载荷：

```
u16 block_name_string_id
u16 block_data             # facing 0..5 + (conditional ? 8 : 0)
u32 mode                   # 0 impulse / 1 repeat / 2 chain
cstr command
cstr custom_name
cstr last_output
u32 tick_delay
u8[4] flags                # [execute_on_first_tick, track_output, conditional, needs_redstone]
```

- 方块名字符串：`command_block`、`repeating_command_block`、`chain_command_block`。
- facing：0 down / 1 up / 2 north / 3 south / 4 west / 5 east。
- 所有多字节整数是 **大端**。

### 1.2 Python 最小生成器

技能里带了一个无依赖（除 `brotli`）的实现：

```bash
python3 scripts/bdxgen.py --spec blocks.json demo.bdx
```

`blocks.json`：

```json
{"blocks":[
  {"pos":[0,0,0],"type":"repeat","command":"scoreboard objectives add demo dummy","facing":"east"},
  {"pos":[1,0,0],"type":"chain","command":"scoreboard players add @a demo 1","facing":"east"}
]}
```

等价的 Python：

```python
from bdxgen import Block, write_bdx

blocks = [
    Block(0, 0, 0, "repeat", "scoreboard objectives add demo dummy", facing="east"),
    Block(1, 0, 0, "chain",  "scoreboard players add @a demo 1",     facing="east"),
    Block(2, 0, 0, "chain",  'titleraw @a actionbar {"rawtext":[{"text":"demo"}]}', facing="east"),
]
write_bdx(blocks, "demo.bdx")
```

脚本位置：`scripts/bdxgen.py`。
它只处理**命令方块**；普通方块/箱子/告示牌请用 AuroraBuild/BDump 的完整 writer。

## 2. MCWorld 的真实格式

`.mcworld` 本质是一个 **zip**，根目录直接放：

```
level.dat          # NBT（little-endian），世界设置/生成器/命令开关
levelname.txt      # 世界名
db/                # LevelDB（CURRENT、MANIFEST、*.log/*.ldb）
world_icon.jpeg    # 可选
```

- **不是**把 BDX 改名；也**不是**只放一个 `.mcstructure`。
- LevelDB 里存 chunk/section/block/NBT；不要手写。
- 用 AuroraBuild 的 `bedrock-world-operator`：

```go
bw, _ := world.Open(worldDir, nil) // 空目录会 FillDefault
bd := &structure.BDX{}
f, _ := os.Open("demo.bdx")
bd.FromFile(f)
bd.ToMCWorld(bw, bwo.SubChunkPos{0, 4, 0}, nil, nil) // y=64
bw.LevelDat().LevelName = "BDX Import"
bw.LevelDat().SpawnX, SpawnY, SpawnZ = 0, 65, 0
bw.CloseWorld()
// 把 worldDir 的内容 zip 成 .mcworld
```

技能仓库的工具：`work/repo/cmd/bdx2mcworld`（输入 BDX、输出 MCWorld、起始坐标）。

### 2.1 世界设置

- `Generator=2`（flat）适合演示/机关；`CommandsEnabled=true`、`CommandBlocksEnabled=true`。
- `SpawnX/Y/Z` 设到结构附近；`GameType=1` 创造。
- 默认 `level.dat` 由 `world.Open` 的 `FillDefault()` 生成；不需要手写 NBT。

## 3. 完整流水线

1. **写方块表**：坐标、mode、facing、command、delay、conditional、needs_redstone。
2. **生成 BDX**：`scripts/bdxgen.py`（命令方块）或 AuroraBuild（混合方块）。
3. **回读验证**：`mcbeextract` / `structure.BDX.FromFile`，核对方块数、坐标、mode、命令。
4. **转 MCWorld**：`bdx2mcworld`，指定起点（如 `0 64 0`）。
5. **回读 MCWorld**：`world.Open` + `LoadChunk`/`LoadNBT`，确认 `id=CommandBlock`、命令一致。
6. **进游戏**：导入 `.mcworld`，确认命令方块已启用；或把 `.bdx` 交给 BuildTask。

## 4. 最容易错的点

- `BD@` 后必须 brotli；直接写 zip/gzip 会解析失败。
- 元数据是 `BDX + author + 0 + 0`；少一个 0 会把第一条命令 ID 吃掉。
- 所有整数大端；坐标移动是相对当前点，不是绝对坐标。
- `PlaceBlockWithCommandBlockData` 的 block_data 要带 facing；conditional 加 8。
- mode：0/1/2 对应 impulse/repeat/chain；不要和方块名混。
- 命令字符串 UTF-8 + null；内部不能有裸 null。
- MCWorld 的 zip **根目录** 必须是 `level.dat`/`db`，不能套一层文件夹。
- MCWorld 不要手写 LevelDB；用 `world.Open` + `ToMCWorld`。
- 网易/国际版的 block runtime ID/level.dat 版本可能不同；生成后在目标版本回读/导入验证。

## 5. 实测

- `demo.bdx`：3 个命令方块，回读坐标 `0/1/2 64 0`，mode repeat/chain/chain。
- `demo.mcworld`：zip 内 `level.dat`、`levelname.txt`、`db/`；回读 chunk 存在，NBT 3 条，`id=CommandBlock`，命令与 BDX 一致。
- 工具：`scripts/bdxgen.py`、`examples/bdx-generator/`、`work/repo/cmd/bdx2mcworld`。
