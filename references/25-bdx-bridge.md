# 25 · BDX 桥：cb.json → .bdx

## 结论

BDX **不是不能放命令方块**。`bdxgen.py` 本来就有：

```text
ID_PLACE_COMMAND_BLOCK = 27
Block(mode=impulse/repeat/chain, command, facing, delay,
      conditional, needs_redstone, custom_name, last_output, track_output)
```

所以“BDX 只能放建筑、不能放命令方块”是错的。

## 本次补的桥

```text
mct cbc 布局
  → .mcworld
  → dump_cbworld.py
  → cb.json
  → cbjson_to_bdx.py
  → .bdx
```

`cbjson_to_bdx.py` 映射：

| cb.json | BDX |
|---|---|
| `block` | mode：impulse/repeat/chain |
| `fd` | facing（0..5 与 bdxgen 一致） |
| `auto` | `needs_redstone = not auto` |
| `cond` | `conditional` |
| `tick` | `delay` |
| `name` | `custom_name` |
| `last` | `last_output` |
| `track` | `track_output` |

## 零偏移硬规则

`bdxgen.write_bdx` / `write_build_bdx` 会检查所有方块的局部最小坐标：

```text
minPos 必须是 (0,0,0)
否则直接拒绝生成
```

原因：BDX 导入偏移不会重写命令文本，带偏移的 BDX + 绝对命令会让整个系统错位。

正确做法：

```text
方块：平移到 (0,0,0) 起点
命令：使用 ~ / ^ 相对坐标
导入：由导入器指定世界起点
```

## 本地验证

mct demo：

```text
.mcworld        99 个命令方块
cb.json         99 条
demo-cb.bdx     99 个命令方块
readbdx 回读    99/99
命令文本         全部一致
条件位           全部一致
needs_redstone   全部一致
```

> 本 skill 的交付边界是 `.bdx` 文件本身；导入和导入后的回读由使用方负责。文件已本地回读，导入器差异不计入本 skill 缺陷。
