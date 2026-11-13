# 渲染控制器变量：用 `playanimation` 改实体外观

> 来源：社区发现的 `playanimation` 渲染控制器变量技巧。  
> 参考视频：[【MCBE】原来原版指令也可以改渲染控制器?丨playanimation](https://www.bilibili.com/video/BV1THjb6zEnN)

## 1. 它是什么

`playanimation` 不只是播放动作。它可以把一个 Molang 表达式写进实体的**动画/渲染变量**，而实体的 **render controller** 会读取这些变量，改变：

- 发光/透明度
- UV 贴图坐标
- 变体/职业/装饰纹理索引
- 触须/斑点/心脏等部件 alpha
- 头部/手持物/缩放

关键区别：

| 变量 | 作用域 | 典型用途 |
|---|---|---|
| `v.*` | 动画/表达式局部变量 | FMBE 部件位置、缩放、UV |
| `variable.*` | 实体渲染控制器变量 | 实体材质/变体/发光/部件 alpha |
| `q.*` | 查询实体/世界状态 | `q.life_time`、`q.is_sneaking`、`q.is_item_name_any` |

**规则**：

- 变量必须属于**对应实体**的 render controller；写到错误实体上通常无效。
- 有些变量是游戏预设/只读的，**不能修改**；不要假设所有 `variable.*` 可写。
- 只影响客户端渲染，不影响服务端碰撞/伤害/计分板。
- 用窄选择器；`@e` 会作用到所有实体，性能和副作用都不可控。

## 2. 基本命令

```mcfunction
playanimation @e[type=glow_squid,tag=glow_demo] animation.player.attack.positions none 0 "variable.glow_alpha=variable.glow_alpha-0.03;" anim
```

- 动画名：`animation.player.attack.positions` 只是一个**载体**；变量不依赖这个动作的语义。
- `none`：混合模式；`0`：速度/时间参数。
- 最后的 `anim` / `anim2` / `anim3` 是**控制器标签**，用来分组变量写入；不是必须和某个动作同名。
- 表达式里可以用 `math.sin/cos/min/max/random_integer`、`q.life_time`、`q.is_sneaking`、`q.is_item_name_any(...)` 等。

## 3. 实体变量示例

以下为社区示例，**逐实体实测**后再用；不同版本可能预设/只读。

### 发光鱿鱼：`glow_alpha`

```mcfunction
playanimation @e[type=glow_squid] animation.player.attack.positions none 0 "variable.glow_alpha=variable.glow_alpha-0.03;" anim
playanimation @e[type=glow_squid] animation.player.attack.positions none 0 "variable.glow_alpha=math.sin(q.life_time*100)*5-5;" anim
```

### 羊驼 / 村民 / 马：纹理/职业/装饰索引

```mcfunction
playanimation @e[type=llama] animation.player.attack.positions none 0 "variable.armor_texture_slot=q.life_time*30;variable.DecorTextureIndex=q.life_time*30;" anim2
playanimation @e[type=villager] animation.player.attack.positions none 0 "variable.profession_index=q.life_time*30;" anim2
```

单个递增：

```mcfunction
playanimation @e[type=llama] animation.player.attack.positions none 0 "v.n=v.n??0;v.n=v.n+1;return 1;" anim
playanimation @e[type=llama] animation.player.attack.positions none 0 "variable.DecorTextureIndex=v.n;" anim2
```

- `??` 是 Molang 的空值回退，用来初始化。
- `return 1` 只用于表达式控制；不要把它当服务端状态。

### 经验球：UV 随机

```mcfunction
playanimation @e[type=xp_orb] animation.player.attack.positions none 0 "v.u=math.sin(q.life_time*172*3)*0.4+0.4;v.v=math.cos(q.life_time*102*3)*0.4+0.4;" anim
playanimation @e[type=xp_orb] animation.player.attack.positions none 0 "v.indexu=math.random_integer(0,3)*4/16;v.indexv=math.random_integer(0,3)*4/16;return 1;" anim
playanimation @e[type=xp_orb] animation.player.attack.positions none 0 "v.u=v.indexu;v.v=v.indexv;" anim2
```

### 监守者：部件 alpha

```mcfunction
playanimation @e[type=warden] animation.player.attack.positions none 0 "variable.tendrils_alpha=math.sin(q.life_time*1000);variable.spots_2_alpha=math.cos(q.life_time*800);variable.spots_1_alpha=math.sin(q.life_time*800);variable.heart_alpha=math.cos(q.life_time*1000);" anim
```

### 鸡 / 猪 / 牛 / 鸡蛋：`v.index`

```mcfunction
playanimation @e[type=chicken] animation.player.attack.positions none 0 "v.index=q.life_time*20;" anim3
```

### 头部/手持物/缩放

```mcfunction
playanimation @a animation.creeper.swelling none 0 "v.swelling_scale1=v.swelling_scale1??1;v.off=v.off??0;v.swelling_scale1=q.is_sneaking ? math.min(v.swelling_scale1+0.35,5)+math.sin(q.life_time*200)*0.25+v.off : 1;v.off=q.is_item_name_any('slot.weapon.mainhand',0,'minecraft:nether_star') ? math.min(v.off+0.12,4) : math.max(v.off-0.12,0);v.swelling_scale2=v.swelling_scale1;" anim1
```

## 4. 设计步骤

1. **定实体**：变量属于谁；先 `summon`/`tag` 一只测试。
2. **查 render controller**：变量名、范围、只读/可写；不存在就换实体/变量。
3. **写单变量**：一次只改一个，用 `say`/`titleraw` 记录 `q.life_time` 或数值。
4. **加时间/状态**：`q.life_time`、`q.is_sneaking`、`q.is_item_name_any`。
5. **限制选择器**：`type=` + `tag=` + `c=1`，不要裸 `@e`。
6. **清理**：恢复默认值/移除 tag/删除测试实体。
7. **客户端验证**：服务端只能验证命令成功，不能验证外观；必须进游戏看。

## 5. 不能做/不要假设

- 不能改**服务端**伤害、碰撞、生命；它只是渲染。
- 不是所有 `variable.*` 都可写；预设/只读变量可能静默失败。
- 不是所有实体都有同名 render controller；跨实体复制通常无效。
- 变量值可能被原版 render controller 每帧覆盖；如果无效，先确认是否被覆盖。
- 高频率 `playanimation` 对实体多时很贵；按需/低频更新。
- 不要用 `@e` 对全图实体刷变量；用 tag/区域/`c=1`。

## 6. 与 FMBE 的关系

- FMBE 的部件模型用 `v.xpos/ypos/...` 做**几何**；
- 本技术用 `variable.*`/部分 `v.*` 改**实体渲染参数**；
- 两者可以叠加：FMBE 做形状，render controller 变量做材质/变体/发光。

参考：

- [playanimation 渲染控制器变量（Bilibili）](https://www.bilibili.com/video/BV1THjb6zEnN)
- [FMBE/MBE reference](fmbe-mbe.md)
