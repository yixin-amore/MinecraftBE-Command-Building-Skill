# 指令计算机：实体像素、栅格与时钟

> 案例来源：你提供的“沃利噪声-计算机部分”截图。  
> 它不是普通机关，而是把**实体当显示/存储介质**的指令计算机思路。

## 1. 截图里的三条命令

```mcfunction
execute unless block ~~1~ air run fill ~~1~ ~~1~ air destroy

execute as @e[type=item,x=55.0,y=-53.0,z=-2.0,r=2,rxm=0,rym=0] at @s align xyz positioned 55.0 -53.0 -2.0 run tp @s 55.0 -53.0 -2.0

execute as @e[type=item,x=55.0,y=-53.0,z=-2.0,r=2,rxm=0,rym=0] at @s unless entity ...
```

（第三条截图被截断；结构是“选中同一批 item → 检查/过滤 → 执行”。）

### 结构拆解

| 命令 | 作用 | 关键点 |
|---|---|---|
| `execute unless block ~~1~ air run fill ~~1~ ~~1~ air destroy` | 上方不是空气时清掉 | `~~1~` 是相对执行者上方 1 格；`destroy` 会**掉落**方块 |
| `execute as @e[type=item,...] at @s align xyz positioned ... run tp @s ...` | 把区域内 item 吸到栅格点 | `align xyz` 把实体对齐到方块角；`positioned` 再给绝对坐标 |
| `execute as @e[...] at @s unless entity ...` | 过滤/检测 | 同一批 item 作为“像素/信号” |

## 2. 它为什么像“计算机”

- **显示**：item 实体是像素/灯；item 的类型/数量/位置编码状态。
- **内存**：真正可靠的状态仍应放在计分板/标签；item 只是显示层。
- **时钟**：repeat 命令方块推进 `fb_tick`；按 tick 刷新像素。
- **总线**：`x/y/z/r` 选择器把区域内的 item 选中；`tag` 分组。
- **栅格**：`align xyz` + `positioned x y z` 把像素对齐到格点。
- **噪声/图案**：预计算表或伪随机序列驱动像素。

## 3. 先修正一个危险点

`fill ... air destroy` 会**掉落方块**，掉落的物品可能再次进入 `@e[type=item]` 选择器，形成反馈/卡顿。

- 只想删除：用 `fill ... air` 或 `fill ... air replace`，不要 `destroy`。
- 想保留掉落：明确清理范围/加 tag 过滤，避免掉落物被误吸。

## 4. 更稳的栅格吸附

```mcfunction
# 只吸附带 tag 的 item，不用裸 @e[type=item]
execute as @e[type=item,tag=px, x=55, y=-53, z=-2, r=2] at @s align xyz positioned 55 -53 -2 run tp @s 55 -53 -2
```

- `r=2` 是球形范围；如果要方形范围，用 `dx/dy/dz`。
- `rxm=0,rym=0` 是旋转下限，不是“没有旋转”；确认你要的过滤条件。
- `tp` 多个 item 到同一点会堆叠/合并/消失；像素点应错开，或每次只吸一个 `c=1`。
- 远处像素需要区块加载；用 `tickingarea`，但不要覆盖过大区域。

## 5. 指令计算机的分层

```text
输入层：玩家操作 / 物品 / 按钮 / 区域
控制层：时钟、状态机、指令计数器
存储层：计分板数组、tag、位集（不要用 item 当唯一存储）
显示层：item/方块/粒子/标题
清理层：回收临时实体、恢复默认、防止反馈
```

### 时钟

```mcfunction
scoreboard players add fb_tick cpu 1
execute if score fb_tick cpu matches 20.. run scoreboard players set fb_tick cpu 0
execute if score fb_tick cpu matches 1 run function/或调用刷新链
```

没有行为包时，用 repeat + 条件链；刷新频率按显示规模降级（5 Hz/1 Hz），不要 20 Hz 全量重绘。

### 存储

- 小状态：`fb_*` 分数。
- 数组：`fb_a0..fb_aN`；索引用整数。
- 位图：一个 32 位分数存 31 个像素/标志。
- item 实体只做**可见像素**；不要依赖它的 NBT/数量做关键存储。

### 噪声/图案

- 预计算表：把噪声值/像素坐标写进数组或命令表。
- 伪随机：`scoreboard players random` + 固定种子表；可复现。
- 帧动画：不要每 tick 重建全部 item；只改变化的像素。

## 6. 检查清单

- [ ] 删除用 `air`，不是 `air destroy`
- [ ] 选择器带 tag/type/范围，不用裸 `@e`
- [ ] item 不会堆叠/合并/掉入反馈
- [ ] 显示层与存储层分离
- [ ] 刷新频率有上限
- [ ] 区块加载/`tickingarea` 已处理
- [ ] 退出重进后能恢复显示
- [ ] 多人时不会抢同一批 item

## 7. 与“纯指令”的关系

这是**纯命令 + 实体**的显示技巧，不需要行为包/资源包；  
但它对实体数量、区块加载、客户端渲染很敏感，属于“高阶但昂贵”的方案，优先用计分板/标题做逻辑，item 只做像素。
