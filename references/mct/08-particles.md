# 粒子（77 章）

> 粒子三条铁律、10 种轮换写法、网易服实测能出/不能出的名单。
**什么时候读**：粒子不出、要换配色、要确认某个粒子名能不能用。

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

---

## 77. 真实粒子用法

### 77.0 三条铁律（血泪版）

1. **名字写错 = 静默不出，不报错。**
   比音效更隐蔽：音效错了至少还能靠耳朵发现"没响"，粒子错了你会以为"是位置/条件的问题"，
   然后去查坐标、查 `tg_point`、查锚点——全查对了还是不出。
   **唯一的防线是白名单**：`lint_commands.py` 的 `PARTICLES`，写错就报。
2. **一律带 `minecraft:` 前缀。**
   实测参考（第 91 章）里全是 `particle minecraft:endrod ...`。不带前缀有时也能跑，
   但跨版本/跨端（网易服）不稳。
3. **粒子必须画在玩家看得见的地方。**
   `at @s run particle ~ ~ ~` 的 `@s` 如果是**被顶到 y+500 的子弹**，
   粒子就画在 500 格高空 —— 玩家什么都看不到。要挂就挂**目标实体**身上（A26）。

**已知在网易服静默不出**（踩过）：`electric_spark_particle`。
它只在较新版本存在，老客户端直接忽略。同类的还有 `colored_flame_particle`、
`mobflame_single` 这类新版 id —— 用之前先在 `PARTICLES` 里登记并实测。

### 77.0.1 一条弹道用 10 种粒子轮换

单色弹道看不出"打了多远、偏了多少"。按格轮换 10 种，一条射线就是彩虹色，长度一眼可读：

```python
TRAIL10 = ["minecraft:endrod", "minecraft:basic_flame_particle",
           "minecraft:basic_smoke_particle", "minecraft:critical_hit_emitter",
           "minecraft:redstone_wire_dust_particle", "minecraft:sparkler_emitter",
           "minecraft:balloon_gas_particle", "minecraft:villager_happy",
           "minecraft:soul_particle", "minecraft:note"]

for n in range(1, RANGE + 1):                 # 第 n 格
    cmds.append("execute as @e[tag=子弹,scores={射程=%d..}] at @s "
                "positioned ^^^%d run particle %s ~~-498.5~"
                % (n, n, TRAIL10[(n - 1) % len(TRAIL10)]))
```

100 格 = 100 条命令，只占 10 个粒子 id，比"每型一套 100 条"省 2/3。

### 77.1 粒子种类分布（1040 次）

| 次数  | 粒子                            | 用在哪        |
| --- | ----------------------------- | ---------- |
| 189 | `balloon_gas_particle`        | 拖尾、飘带（最长用） |
| 104 | `mobflame_single`             | 火焰         |
| 76  | `colored_flame_particle`      | 彩色火        |
| 63  | `redstone_wire_dust_particle` | 红色粉末（血/魔法） |
| 56  | `sonic_explosion`             | 大招冲击波      |
| 47  | `cauldron_explosion_emitter`  | 爆炸         |
| 46  | `sparkler_emitter`            | 火花         |
| 40  | `basic_flame_particle`        | 基础火        |
| 36  | `sculk_soul_particle`         | 灵魂         |
| 31  | `knockback_roar_particle`     | 冲击环        |

### 77.2 只给位置就够

```mcfunction
execute at @e[type=armor_stand] run particle minecraft:villager_happy ~2.5 ~1.25 ~0.85
execute as @a[scores={进度=98..}] at @s run particle minecraft:totem_particle ~ ~1 ~
```

**不给 count / dx / dy / dz 时 = 1 个点。** 要铺开才写后三个：

```mcfunction
particle minecraft:balloon_gas_particle ~ ~ ~ 0.3 0.3 0.3 0.05 20
#                                  ↑坐标    ↑散布半径    ↑速度 ↑数量
```

### 77.3 摆点靠"多块多命令"，不靠单块多粒子

弗拉迪的刀光：**每格一个方块、一个粒子、一个局部坐标**，8 个方向 = 8 条命令。  
**不要试图用一条命令的 `dx dy dz` 画出形状**——那是随机散布，不是图案。

---
