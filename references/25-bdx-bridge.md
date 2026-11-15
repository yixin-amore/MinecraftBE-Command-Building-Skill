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

## 为什么之前没做

不是技术不可行，是**优先级 + 服务端验证风险**：

1. mct 默认交付 `.mcstructure`；结构方块加载命令方块 NBT 是它验证过的路径。
2. 我们原来的网易租赁服路径是 **逐块 `setblock` + `CommandBlockUpdate`**；BDX 对命令方块 NBT 的导入没有真机验证。
3. BuildTask/AuroraBuild 对 ID27 的处理、命令方块实体 NBT 是否保留、`auto/cond/delay` 是否落对，必须在测试区回读，不能在主城赌。
4. 所以先把 BDX 桥做成**本地可验证**，再接服务器。

## 下一步

```text
1. 测试区导入 demo-cb.bdx
2. 回读 99 个命令方块：command/cond/auto/delay/facing/name
3. 用红石块触发 init 链，确认链头
4. 通过后再接主城
```

在真机通过前，**不要对外说 BDX 命令方块已经可导入**。
