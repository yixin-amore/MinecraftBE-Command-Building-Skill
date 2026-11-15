# 演出类技能：展示体 + 粒子 + 运镜（实测版）

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **这是本 skill 实测过的版本**；`14-fmbe.md` 是外部教程的原理版，`SKILL.md` 第十一章讲编排。
>
> **什么时候读我**：要做"技能演出"——凭空渲染方块、粒子绘阵、电影运镜、几十秒到两分钟的长演出。
>
> 参考产物（四个，规模递增）：
> `屏障咒典` 1075 块 / `十方剑阵` 1533 块 / `万剑归宗` 2513 块 / `紫晶天穹` 21769 块。

---

## 一、展示体：一只狐狸 = 一个方块

狐狸隐身、主手拿要展示的方块，用 `playanimation` 篡改动画变量来平移 / 旋转 / 缩放。

8 条前置（每刻跑，**选择器按组共享，不是逐只**）：

```mcfunction
playanimation @e[scores={fmbe_gem=1..}] animation.player.sleeping none 0 "" controller.animation.fox.move
playanimation @e[scores={fmbe_gem=1..}] animation.creeper.swelling none 0 "v.xbasepos=v.xbasepos??0;v.ybasepos=v.ybasepos??0;v.zbasepos=v.zbasepos??0;v.xpos=v.xpos??0;v.ypos=v.ypos??0;v.zpos=v.zpos??0;v.xrot=v.xrot??0;v.yrot=v.yrot??0;v.zrot=v.zrot??0;v.scale=v.scale??1;v.xzscale=v.xzscale??1;v.yscale=v.yscale??1;v.swelling_scale1=2.1385*math.sqrt(v.xzscale*v.scale);v.swelling_scale2=2.1385*math.sqrt(v.yscale*v.scale);" fmbe.scale
playanimation @e[scores={fmbe_gem=1..}] animation.ender_dragon.neck_head_movement none 0 "v.head_rotation_x=0;v.head_rotation_y=0;v.head_rotation_z=0;v.head_position_x=(v.xbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);v.head_position_y=(10.05185375+v.ybasepos*0.467625)*math.sqrt(v.yscale*v.scale);v.head_position_z=(17.108-v.zbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);" fmbe.shift_pos
playanimation @e[scores={fmbe_gem=1..}] animation.warden.move none 0 "v.body_x_rot=90+v.xrot;v.body_z_rot=90+v.yrot;" fmbe.xrot
playanimation @e[scores={fmbe_gem=1..}] animation.player.attack.rotations none 0 "v.attack_body_rot_y=-v.zrot;" fmbe.zrot
playanimation @e[scores={fmbe_gem=1..}] animation.parrot.moving none 0 "v.wing_flap=(16-v.xpos)*3.3333333;" fmbe.xpos
playanimation @e[scores={fmbe_gem=1..}] animation.minecart.move.v1.0 none 0 "v.rail_offset.x=0;v.rail_offset.y=1.6485+v.ypos/16;v.rail_offset.z=0;" fmbe.ypos
playanimation @e[scores={fmbe_gem=1..}] animation.parrot.dance none 0 "v.dance.x=-v.zpos;v.dance.y=0;" fmbe.zpos
```

变量：`xpos/ypos/zpos`（**1/16 格**）、`xrot/yrot/zrot`（**度**）、`scale/xzscale/yscale`、
`xbasepos/ybasepos/zbasepos`。

---

## 二、五条硬结论（每条都是踩过坑才定的）

### 1. `basepos` 必须每刻重写

一次性 `playanimation` 赋值会被渲染链的 `??0` 当"没值"重置，方块全掉回生成点
（实测症状：**"拉了一地海晶灯"**）。

### 2. 锁位：逐只 tp，每刻都跑，不许兜底

```mcfunction
# ✅ 每只一条，锚点用"整场演出都在的人"
execute at @a[scores={cam_t=0..},c=1] positioned ~0 ~ ~-2 run tp @e[scores={fmbe_gem=1}] ~ ~ ~ ~ ~
execute at @a[scores={cam_t=0..},c=1] positioned ~-2 ~ ~0 run tp @e[scores={fmbe_gem=2}] ~ ~ ~ ~ ~
# ... 20 只 20 条
# ❌ 绝对不要再来一条兜底：tp @e[scores={fmbe_gem=1..}] ~ ~ ~ ~ ~
```

两个致命细节：

| 坑 | 症状 | 原因 |
|---|---|---|
| **锚点用了一次性触发位** | 狐狸坠落 | `cam_cast` 在施法链末尾被清零，整场匹配不到人 → tp 全部静默失败 |
| **加了兜底 tp** | 全挤在一起 + 一抽一抽 | 兜底把所有狐狸拉回原点，前 20 条刚摆好又被拽回 |

**锁位链必须是 `kind="repeat"` 纯循环链**（第 0 格就是重复块，无闸门 / 无按钮 / 无重置块）：

```python
{"id": "lock", "kind": "repeat", "button": False, "cmds": [20 条 tp, resistance, stopsound]}
```

- 用 `gated` + `execute if entity @a` → `check_chain_break` 判"常驻链还留着恒真闸门"
- 用 `gate_mode="loop"` → `to_system` 给 gated 链加的 `{RESET}` 会变成**重置块**，多占一格

### 3. 公转只改 `v.yrot`

```text
世界偏移 = R(yrot) · basepos
```

basepos 固定 `(0, −R·16, y·16)`，只让 `v.yrot` 变 → 位置绕玩家公转、朝向同步转，**整圈一条命令**。

### 4. 倾斜轨道 = `v.xrot` 当倾角

| 轨道 | `v.xrot` |
|---|---|
| 水平 | 0 |
| 倾斜 | 30 |
| 陡斜 | 60 |
| 垂直 | 90 |

倾角是常数、公转是累加，每轨道每刻 1 条命令。

### 5. 自转写累加，不写绝对值

`v.yrot=v.yrot+2.25`（45°/s @20tps）。写 `math.mod(q.life_time*45,360)` 会把施法时种的
相位冲掉，整座变成同刻起转。转速换算：**每刻转 `度/20`**。

---

## 三、多轨道怎么分组

用 `fmbe_orb` 打组号（0=主体 1-5=轨道 6=副阵），阶段链按组一次控一整队：

```mcfunction
playanimation @e[scores={fmbe_orb=1}] ... "v.yrot=v.yrot+0.9;v.scale=3.2;" fmbe.s1
playanimation @e[scores={fmbe_orb=2}] ... "v.yrot=v.yrot-0.7;v.scale=4.2;" fmbe.s2
```

**块数 × 阶段数 = 命令数**：7 块 × 4 阶段 = 28 块，每刻只跑 1 条。

---

## 四、规模从哪来（四个来源）

| 来源 | 说明 | 实例 |
|---|---|---|
| **阶段链** | 一条链一个互斥时间窗口 | 85 格 × 6 阶段 = 510 块 |
| **粒子逐点绘图** | 一圈 40 点 = 40 个命令方块 | 结印 9 环 = 360 块 |
| **按格施法** | 每格 5~7 条（summon / 物品 / 序号 / 初始态 / 相位） | 20 格 = 140 块 |
| **多幕叙事** | 每幕一套粒子 + 镜头 + 音效 | 六幕 = 数千块 |

**每刻执行数不随规模涨**：紫晶天穹 21769 块，每刻只有「渲染 8 + 锁位 21 + 轨道 5 + 阶段 1」≈ 35 条。

---

## 五、粒子绘阵

```python
def tilt_ring(r, n, h, tilt, particle, t0, t1, phase=0.0):
    """倾斜圆：绕 X 轴倾斜 tilt 度。tilt=90 就是竖直圆。"""
    out = []
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    for k in range(n):
        th = 2 * math.pi * k / n + math.radians(phase)
        x = r * math.cos(th)
        y = h + r * math.sin(th) * st
        z = r * math.sin(th) * ct
        t = t0 - round((t0 - t1) * k / max(1, n - 1))
        out.append('execute as @a[scores={cam_t=%d}] at @s run particle %s ~%.2f ~%.2f ~%.2f'
                   % (t, particle, x, y, z))
    return out
```

三条规矩：
1. **一圈一条链**（窗口闸门 + 链内按 `cam_t=N` 逐点错开），别全塞一条。
2. **坐标用 `~` 世界轴**（法阵相对地面固定）；要跟朝向才用 `^`。
3. **粒子只在关键帧炸**，不参与每刻循环。

### 14 种粒子怎么分配

只用 `endrod` + `enchanting` 两种 = 画面单色。按功能分配：

| 功能 | 粒子 | 用在哪 |
|---|---|---|
| 结构描边 | `endrod` | 所有环的骨架线 |
| 魔法紫雾 | `enchanting_table_particle` / `dragon_breath_trail` | 法阵填充、剑雨轨迹 |
| 空间感 | `basic_portal_particle` / `portal_directional_particle` | 球壳、外环、肩环 |
| 神圣金光 | `totem_particle` / `sparkler_emitter` | 冲击波、符文 |
| 打击感 | `critical_hit_emitter` / `explosion_manual` | 垂直剑阵、核心阵 |
| 法术溅射 | `splash_spell_emitter` | 腰环交替 |
| 收尾 | `basic_flame_particle` / `lava_particle` / `basic_smoke_particle` | 余波、归寂 |
| 音符 | `note` | 高空符文交替 |

**同一条环上交替两种粒子**（`i % 2`）就能出层次，不用加倍点数。
实测分布：主色两种各 4000~6000，辅色十二种各几百——**主色两种，辅色十二种，不会花**。

---

## 六、可读性：先让人看懂，再谈震撼

用户原话："我看不出来你这个 FMBE 想要表达什么"——这是堆粒子堆出来的典型翻车。

### 五条构图规矩

| # | 规矩 | 反例 → 正例 |
|---|---|---|
| 1 | **层与层半径至少差 2 格** | 五组轨道挤在 4~7 格 → 三条轨道 6.5 / 9.0 / 13.0 |
| 2 | **删掉遮挡主体的"雾"** | 晶壳、晶晕、流线、剑迹四套全删 |
| 3 | **环少而粗**：环数减半、每环点数翻倍 | 10 环 × 44 点 → 6 环 × 72 点 |
| 4 | **加连线表达关系** | 12 剑各拉一条线到神剑，一眼看出"护剑阵" |
| 5 | **主体放大并居中** | 神剑 scale 3 → 4.2，剑环锚点整体前移，环心落在剑上 |

### 三层构图（可直接套）

```
远景：3 条紫晶轨道（6.5 水平 / 9.0 倾斜30° / 13.0 倾斜15°）
中景：12 剑环（半径 3.2）+ 12 条指向中心的连线
焦点：1 把神剑（scale 4.2，垂直悬浮）
地面：6 环 + 双六芒 + 十二芒
```

**每一层只表达一件事**，层与层之间留空。粒子只做"描边"和"连线"，不做氛围雾。

### 反例清单

- ❌ 每个晶体表面撒 48 个碎晶 → 像噪点，不像晶体
- ❌ 每个晶体套一圈光晕 → 和轨道线混在一起
- ❌ 16 条螺旋流线 → 把所有结构糊成一片
- ❌ 12 剑各自 14 点拖尾 → 剑本身反而看不清

---

## 七、运镜

```text
camera <目标> set minecraft:free ease <秒> <缓动> pos <^左 ^上 ^前> facing <坐标>
camera <目标> fov_set <角度> [缓动秒] [曲线]
camera <目标> clear
camerashake add <目标> <强度> <秒> positional
inputpermission set <目标> movement disabled|enabled
```

- 机位用 `^`（局部坐标），`facing ~ ~2.5 ~` 锁中心。
- **法阵半径 9 格时，机位至少 16~32 格**，贴脸拍只会糊一脸粒子。
- 镜头要**成组**：推进 → 俯视 → 环绕 → 拉远 → 大远景 → 收，不要随机跳。
- 缓动：`out_cubic` 起手 / `in_out_sine` 平移 / `out_quad` 收尾 / `out_elastic` 回弹。
  长演出用 3~6 秒缓动，短演出用 0.5~1.2 秒。
- **收尾五件套**：`camera clear` → `fov_clear` → `movement enabled` → 清展示体 → `cam_t -1`。

---

## 八、音效

120 秒演出 **60~210 个音效点**，关键拍 3~4 层：

| 层 | 音效 | 作用 |
|---|---|---|
| 底噪 | `ambient.cave` / `random.fizz` / `note.bass` | 空间感 |
| 中频主体 | `conduit.activate` / `beacon.power` / `bell.ring` | 法阵运转 |
| 高频金属 | `note.pling` / `note.chime` / `mob.irongolem.hit` | 剑鸣、符文点亮 |
| 低频冲击 | `raid.horn` / `random.explode` / `mob.wither.shoot` | 阶段转折、解封 |

```mcfunction
execute as @a[scores={cam_t=360}] at @s run playsound random.explode @a[r=48] ~ ~ ~ 1 0.6
```

**关键帧音效必须和镜头共用同一条 `cam_t` 闸门**，否则整段每刻都在响。

音效可以循环生成，不必手写 200 行：

```python
for i, t in enumerate(range(2388, 360, -22)):
    cues.append((t, "ambient.cave", 0.45, 0.5 + (i % 6) * 0.05))       # 底噪
for i, t in enumerate(range(2370, 340, -12)):
    cues.append((t, ["note.pling","note.chime","note.bell","note.harp"][i % 4],
                 0.55, 0.8 + min(0.8, i * 0.008)))                     # 递升音阶
```

---

## 九、清理：不用 `kill`

```mcfunction
scoreboard players set @e[scores={fmbe_gem=1..}] fmbe_gem 0
tp @e[scores={fmbe_gem=0}] ~ -400 ~
```

**先摘标记**：不摘的话渲染链的锁位会把它们钉在 -400 不动，永远不消失。

---

## 十、常加载区：单块上限 100 区块

`tickingarea add` 一次最多 **100 区块**，全服最多 **10 个**区域。
两万块的结构是 128×283 → 8×18 = **144 区块**，一次 add 直接报"无法创建"。

```python
seg = ceil((z1 - z0 + 1) / 8)
for i in range(8):
    a, b = z0 + i*seg, min(z1, z0 + (i+1)*seg - 1)
    out.append("tickingarea add ~%d ~-4 ~%d ~%d ~4 ~%d amethyst%d" % (x0, a, x1, b, i+1))
```

实测：8 段 × 每段 8×3 = **24 区块**，全部创建成功。

两个坑：
1. **`remove` 要逐名删**（`amethyst1` … `amethyst8`）；`remove_all` 会把玩家自己的也删掉。
2. **量范围前先设好 `B.W`**：写在 `measure_ta()` 之后 → 量的是旧布局（64 宽 → 深度翻倍）。

---

## 十一、链数决定结构深度

命令方块数只决定"行数"，**链数决定"行距"**——每条 gated 链都要占一整行 + 1 行间隔。

实测：103 条链 → 结构深 277 行；合并到 49 条 → 深 137 行，方块数不变。

合并办法：把「同一条轨道 × 5 个阶段」压成一条链，阶段闸门挪进命令内部：

```mcfunction
# 链闸门恒为"演出中"
execute if entity @a[scores={cam_t=0..}]
# 命令内部再判阶段
execute as @a[scores={cam_t=400..900}] run playanimation @e[scores={fmbe_orb=1}] ... "v.yrot=v.yrot+2.2;" fmbe.s1
```

**代价**：窗口外这 5 条命令每刻都跑（只有 1 条命中）。**收益**：深度砍一半。
另外 `B.W = 128`（布局宽度翻倍）也能直接砍一半深度。

---

## 十二、实体预算

| 说法 | 实际 |
|---|---|
| "限制 N 个实体" | 影响的是**每刻 Molang 求值次数**（N×8），不是命令方块数 |
| 65 只实体 | 每刻仍只跑 8 条渲染命令（按组共享选择器） |
| 压到 20 只 | 省的是求值，不是块数；画面用**轨道粒子**补回来 |

**实体少 ≠ 画面差**：紫晶天穹把 52 块晶体压到 7 块，用三条倾斜粒子轨道补，
观感不掉反升，实体从 65 降到 20。

**实体名额先给主体**：要"万剑归宗"就把名额全给剑，符文 / 法阵 / 核心交给粒子。

---

## 十三、四个产物的规模对照

| 产物 | 命令方块 | 链 | 实体 | 粒子 | 音效点 | 结构 |
|---|---|---|---|---|---|---|
| 屏障咒典 | 1075 | 17 | 85 | ~750 | 20 | 64×5×24 |
| 十方剑阵 | 1533 | 40 | 10 | 1148 | 79 | 64×5×61 |
| 万剑归宗 | 2513 | 48 | 10 | 2115 | 79 | 64×5×128 |
| 紫晶天穹 | 21769 | 70 | 20 | ~20500 | 210 | 128×5×283 |

**两万块的代价**：结构 12MB，导出要 5 分钟，游戏内粘贴也要等，常加载要拆 8 块。
超过 1 万块就该反问自己：**真的需要这么多吗**，还是把镜头做慢一点、粒子做少一点。

---

## 十四、踩坑速查（按症状查）

| 症状 | 根因 | 定稿做法 |
|---|---|---|
| 方块全堆在生成点、贴地一片 | basepos 只赋了一次 | 每刻重写 basepos |
| 狐狸坠落 | 锁位锚点用了一次性触发位 `cam_cast` | 锚点用 `cam_t=0..` |
| 全挤在一起 + 一抽一抽 | 逐只 tp 后面加了兜底 tp | 删掉兜底 |
| 转起来整齐划一 | 自转写绝对值 | 写累加 `v.yrot+2.25` |
| Molang 整条不生效 | 表达式以 `+` 开头，或 `v.R*-14` | 常数去掉前导 `+`；负系数加括号 |
| 朝向乱七八糟 | 绕玩家水平排一圈却都朝同一方向 | 让狐狸跟随施法者朝向，或改成正面法阵 |
| 看不出想表达什么 | 层挤在一起 + 粒子雾 | 五条构图规矩（半径拉开 / 删雾 / 环少而粗 / 加连线 / 主体放大） |
| 运镜糊脸 | 机位 2~4 格，法阵半径 9 格 | 机位 16~32 格，`facing` 锁中心 |
| 演出"没声音" | 只有十几个单层 `playsound` | 60~210 个点，关键拍 3~4 层 |
| 常加载无法创建 | 单块 >100 区块 | 按 z 切 8 段 |
| `check_chain_break` 报"常驻链还留着恒真闸门" | 锁位用了 `gated` + `@a` | 改 `kind="repeat"` |
| 结构深到加载不到 | 链太多 | 合并同轨道的阶段链 + `B.W` 翻倍 |

## 十五、生成器（`scripts/` 里可直接跑）

五个演出都是**生成器产物**，不是手搓的。改参数重跑就能出新的：

| 脚本 | 产物 | 块 | 实体 | 特点 |
|---|---|---|---|---|
| `build_fmbe.py` | FMBE 展示体 | 69 命令 | 3 组 | 最小可用版：渲染链 + 三组展示 + 开关面板 |
| `build_shield_cam.py` | 屏障咒典 | 1075 | 85 | 千格穹顶、五阶段、八段运镜、附魔书触发 |
| `build_sword_array.py` | 十方剑阵 | 1533 | 10 | 正前方竖直法阵、十剑平行突刺 |
| `build_sky_sword.py` | 万剑归宗 | 2513 | 10 | 120 秒九层法阵、2115 条粒子 |
| `build_amethyst.py` | 紫晶天穹 | 2451 | 20 | 五条倾斜轨道（0/30/60/90°）、`fmbe_orb` 分组 |

**统一接口**：

```bash
# 只出规格（快，用来检查链数/命令数）
python scripts/build_amethyst.py --dump-spec out.json

# 打包成世界（要模板）
python scripts/build_amethyst.py --spec out.json --template _template.mcworld --out 世界.mcworld

# 再导结构
python scripts/mcworld_to_structure.py --input 世界.mcworld --out 紫晶天穹.mcstructure
```

**五个脚本的共同结构**（改新演出照这个骨架）：

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # 找同目录的 build_cbworld
import build_cbworld as B

def spec():
    chains = [...]          # 每条链一个 dict：id / kind / cmds / gate
    return {"name": "...", "chains": chains, "panels": [...], "props": [...]}

def build(...):  ...        # B.build_world(spec(), ...) → .mcworld
```

**改哪里能变出新演出**：

| 想改 | 改哪 |
|---|---|
| 展示体的形状 | `basepos` 表达式（设计坐标 × 16） |
| 轨道倾角 | `v.xrot`（0/30/60/90） |
| 转速 | 累加步长 `v.yrot+2.25`（45°/s @20tps） |
| 时长 | 阶段链的时间窗口长度 + `cam_t` 起点 |
| 画面密度 | 粒子条数（不用加实体，见第五节） |
| 运镜 | `camera ... pos ^ ^ ^` 的五段模板（见主文件十一.2） |

---

## 十六、外部作品的四个可借用点

拆了七个实战作品（见 `16-case-studies.md`），只有四条值得吸收，其余我们已有更优解：

| 借用 | 写法 | 为什么好 |
|---|---|---|
| **`hasitem` 的 `data=` 变体** | `give @s enchanted_book 1 104` + `hasitem={item=enchanted_book,data=104,…}` | 一本书一个技能，不冲突。**推翻"特殊物品只能靠类型唯一"的旧结论** |
| **`summon` 直接带名字** | `summon fox ~~~ 0 0 minecraft:ageable_grow_up FM核心` | 省一条命令，`name=` 可精确点名 |
| **`damage … 0 … entity @p`** | 0 伤害当"被打了一下"的触发器 | 不扣血也能触发受击/阶段切换 |
| **`unless blocks` 落地检测** | `unless blocks ~1~-0.3~1 ~-1~-0.3~-1 ~ 300 ~ all` | 比 `if block ~~-1~ air` 稳，不会站在边缘误判 |

**不借的**：一条命令叠 10 个 `rotated as`（不可维护）、全库 tag（687 处，命名混乱）、
`@p` 当施法者（多人打错人）、`kill` 清几百个展示体（卡帧）。

**一条新路线**：盔甲架 + `replaceitem … slot.weapon.mainhand 0 slime` 也能当方块展示体——
无声、不会自己走、可精确摆位，适合几十个静态道具；代价是物品模型小，要放大 5~12 倍。
