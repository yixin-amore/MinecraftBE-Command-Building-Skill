# Java → Bedrock 方块映射（重点：雪）

> 不要凭 Java 经验猜 Bedrock 方块名。  
> 数据来源：[Bedrock Edition data values/Blocks](https://minecraft.wiki/w/Bedrock_Edition_data_values/Blocks)、
> [Microsoft block enum](https://github.com/MicrosoftDocs/minecraft-creator/blob/main/creator/Commands/enums/Block.md)。

## 1. 雪：最容易错

| 用途 | Java | Bedrock（正确） |
|---|---|---|
| 完整雪块 | `snow_block` | **`minecraft:snow`** |
| 薄雪层/顶层雪 | `snow` | **`minecraft:snow_layer`** |

所以：

```mcfunction
# ✅ 完整雪块
setblock 0 64 0 minecraft:snow

# ✅ 薄雪层
setblock 0 64 0 minecraft:snow_layer

# ❌ Java 名，Bedrock 不认
setblock 0 64 0 minecraft:snow_block
```

## 2. 常见 Java → Bedrock 改名

| Java | Bedrock |
|---|---|
| `snow_block` | `snow` |
| `snow`（顶层雪） | `snow_layer` |
| `grass_block` | `grass` |
| `note_block` | `noteblock` |
| `cobweb` | `web` |
| `spawner` | `mob_spawner` |
| `magma_block` | `magma` |
| `slime_block` | `slime` |
| `bricks` | `brick_block` |
| `nether_bricks` | `nether_brick` |
| `end_stone_bricks` | `end_bricks` |
| `terracotta` | `hardened_clay` |

> 这张表只列高置信度差异。`oak_planks`、楼梯、台阶、墙等受方块状态/扁平化影响，
> 以实际版本 `/setblock` 测试或 Bedrock block data 表为准。

## 3. 代码里的归一化

`scripts/block_map.py`：

```python
from block_map import normalize
normalize("snow_block")   # -> "snow"
normalize("grass_block")  # -> "grass"
normalize("snow")         # -> "snow"（不猜；顶层雪请显式写 snow_layer）
```

`buildgen.py` / `bdxgen.py` 写 BDX 前会对 `BuildBlock.block` 做归一化；  
`schematic_blocks.py` 输出调色板时也会归一化。

## 4. 自检

- [ ] 雪块：`minecraft:snow`
- [ ] 雪层：`minecraft:snow_layer`
- [ ] 没有 `snow_block`、`grass_block` 等 Java 名
- [ ] 不确定的方块先 `/setblock` 验证
- [ ] 方块状态用 Bedrock 的 `["state"="value"]`，不要 Java `[facing=east]`

## 5. 来源

- [Bedrock Edition data values/Blocks](https://minecraft.wiki/w/Bedrock_Edition_data_values/Blocks)
- [Microsoft Minecraft Creator — block enum](https://github.com/MicrosoftDocs/minecraft-creator/blob/main/creator/Commands/enums/Block.md)
