# 35 · 建筑组件库：8 个语义组件

> 这些不是“形状函数”，是可组合的建筑语法单元。
> 实现：`scripts/arch_compile.py`；每个组件返回 `ComponentResult`（bbox / ports / openings）。

## 组件表

| 组件 | 作用 | 关键参数 | 输出 |
|---|---|---|---|
| `curtain_wall` | 城堡幕墙 | 起止、厚度、门洞、垛口、扶壁 | 墙段 + 门洞 + 墙顶通道 |
| `gatehouse` | 门楼 | 宽/深/高、门洞宽、塔半径 | 双塔 + 穿门 + 闸门 + 桥 |
| `keep` | 主堡 | 平面、高、尖顶、角塔 | 主塔 + 角塔 + 玫瑰 + 入口 |
| `cloister` | 回廊庭院 | 矩形、开间、层高 | 柱列 + 拱 + 中央空院 |
| `bay_z` | 立面开间 | 宽、高、窗、扶壁、山墙 | 背墙 + 深窗 + 扶壁 + 山墙 |
| `portal_z` | 门廊 | 宽、高、拱层数、台阶 | 多层尖拱 + 门 + 台阶 |
| `flying_buttress` | 飞扶壁 | 起止、方向、高度 | 墩柱 + 飞券 + 尖饰 |
| `dormer_z` | 老虎窗 | 位置、宽、屋面 | 屋顶小窗 + 小山墙 |

## 最小调用

```python
b.curtain_wall(12,12,108,108,2,26,4,gate_center=60,gate_width=26)
b.gatehouse(60,108,width=36,depth=18,y0=2,height=58,passage_width=10)
b.keep(60,40,size=28,y0=2,height=78,spire=24)
b.cloister(20,62,44,86,2,5,7)
b.bay_z(108,28,2,7,18,True,True,True)
b.portal_z(128,60,2,10,14,3,3)
b.flying_buttress(98,64,2,36,1)
b.dormer_z(78,70,41,3)
```

## 端口

每个组件返回：

```python
ComponentResult(
  component='gatehouse',
  bbox=(x0,y0,z0,x1,y1,z1),
  ports=[ComponentPort(name, pos, normal, width)],
  openings=[...],
)
```

当前端口是**元数据**：

- 用来做布局检查/拼装提示；
- 还没有自动吸附、净空求解、碰撞图；
- 调用方需要保证组件不互相穿插。

## 示例

`examples/arch-castle/` 用 8 个组件拼出：

```text
curtain_wall + gatehouse + keep + cloister
+ bay + portal + flying_buttress + dormer
```

结果：

```text
13 个组件实例
134,935 体素
BDX 134,935 方块
回读 134,935 / issues []
```

预览：

- `examples/arch-castle/out/building-front.png`
- `examples/arch-castle/out/building-top.png`
- `examples/arch-castle/out/building-iso.png`

## 当前边界

- 组件目前是**方块的组合**，还没有用 stairs/slabs 做收分和弧线；
- 风格变体、LOD、自动材质 resolver 还没接；
- 端口/开口只是数据，不是自动连接器；
- `curtain_wall` 的门洞会切南墙，其他朝向需要改参数/扩展；
- 复杂塔楼/穹顶/飞扶壁的受力逻辑仍由几何近似表达。

## 下一步

1. 给 `ComponentResult` 加 `ports` 自动吸附；
2. 用 stairs/slabs 优化拱、垛口、屋顶；
3. 加风格变体：gothic / romanesque / japanese；
4. 用组件重做 castle benchmark，和手写版对比。
