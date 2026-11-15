#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dsl —— 指令 DSL 编译器（从「写字符串」到「写代码」）

**为什么要有这个模块**

以前业务命令是这么写的：

    "execute as @a[scores={tg_shot=1,tg_type=%d}] at @s run playsound %s @a[r=32] ~~~ %s %s"
    % (t, snd, vol, pitch)

问题不在长，在**它只是一段文本**：

  · `scores=` 写两次 → 语法错，整条失效（A33 踩过）
  · `scores=` 写在选择器外 → 语法错，收镜全废（A35 踩过）
  · 忘了 `at @s` 却用了 `~ ~ ~` → 粒子画在命令方块上，不是玩家脚下
  · `@s` 没有 `as` → 无目标，静默不跑
  · 改一个字段要全局搜字符串

这些**都不是"写错字"，是"结构没被表达出来"**。字符串里没有"选择器""上下文""动作"
这些概念，所以编译器帮不上忙，只能靠人记住规则。

--------------------------------------------------------------------------
现在的写法

    from dsl import P, SetScore, PlaySound, Particle

    # 选择器是结构化的：条件塞进同一个 scores 花括号，不可能拼错
    shot = P("@a", scores={"tg_shot": 1, "tg_type": 3})

    # 动作有语义：谁、哪个计分项、什么值
    As(shot).at("@s").run(
        SetScore("@s", "tg_cooldown", 12),
        PlaySound("random.explode", P("@a", r=48), volume=1.0, pitch=0.55),
        Particle("minecraft:basic_flame_particle", "~ ~1 ~"),
    )

    # → execute as @a[scores={tg_shot=1,tg_type=3}] at @s run scoreboard players set @s tg_cooldown 12
    # → execute as @a[scores={tg_shot=1,tg_type=3}] at @s run playsound random.explode @a[r=48] ~~~ 1.0 0.55
    # → execute as @a[scores={tg_shot=1,tg_type=3}] at @s run particle minecraft:basic_flame_particle ~ ~1 ~

**一个 execute 前缀，多条动作自动展开** —— 这是最直接的收益：
以前 3 条命令要写 3 遍选择器，现在写 1 遍。

--------------------------------------------------------------------------
分层

    Sel      选择器（`@a` + 条件）        →  "@a[scores={...},r=3]"
    Act      动作（命令体）                →  "scoreboard players set @s x 1"
    Ctx      execute 上下文（as/at/...）   →  "execute as ... at ... run <动作>"
    Chain   一条链（业务列表）             →  交给 cbc.py 生成三段式
    Program 整个系统                       →  spec

`cbc.py` 负责**结构**（闸门 / 连接 / 重置 / 条件位），
本模块负责**内容**（选择器 / 上下文 / 动作）。两者不重叠。
"""
import re


# ============================================================ 选择器
class Sel:
    """结构化选择器。所有条件都进**同一个方括号**，语法天然正确。

    用法：
        P("@a")                                   → @a
        P("@a", scores={"x": 1, "y": "1.."})      → @a[scores={x=1,y=1..}]
        P("@e", type="xp_orb", r=1, c=1)          → @e[type=xp_orb,r=1,c=1]
        P("@a", hasitem={"item": "fishing_rod"})  → @a[hasitem={item=fishing_rod}]
        P("@s", scores={"tg_aim": 1})             → @s[scores={tg_aim=1}]

    `scores` 的 key 是计分项名，value 是：
        数字 / 字符串（"1.." "..0" "-1" 原样输出）
        None → 跳过（方便条件式构造）
    """

    # 只允许这些键（拼错立刻报错，而不是生成一条废命令）
    ALLOWED = {"scores", "type", "name", "r", "rm", "dx", "dy", "dz", "c",
               "m", "l", "lm", "tag", "hasitem", "family", "has_property",
               "haspermission", "x", "y", "z", "distance"}

    def __init__(self, base="@a", **kw):
        if not base.startswith("@"):
            raise ValueError("选择器必须以 @ 开头：%r" % base)
        self.base = base
        self.kw = {}
        for k, v in kw.items():
            if v is None:
                continue
            if k not in self.ALLOWED:
                raise ValueError("未知选择器参数 %r（允许：%s）"
                                 % (k, " / ".join(sorted(self.ALLOWED))))
            self.kw[k] = v

    def __str__(self):
        if not self.kw:
            return self.base
        parts = []
        for k in sorted(self.kw):
            v = self.kw[k]
            if k == "scores":
                parts.append("scores={%s}" % ",".join(
                    "%s=%s" % (n, x) for n, x in v.items() if x is not None))
            elif k == "hasitem":
                inner = ",".join("%s=%s" % (n, x) for n, x in v.items() if x is not None)
                parts.append("hasitem={%s}" % inner)
            else:
                parts.append("%s=%s" % (k, v))
        return "%s[%s]" % (self.base, ",".join(parts))

    def __repr__(self):
        return "Sel(%r)" % str(self)


def P(base="@a", **kw):
    """`P` = Player/实体选择器。短名字，因为到处都在用。"""
    return Sel(base, **kw)


# ============================================================ 动作
class Act:
    """动作基类。子类实现 `body()`，返回**不带 execute 前缀**的命令体。"""

    def body(self):
        raise NotImplementedError

    def needs_at(self):
        """这条动作是否要求有 `at`（用了 `~` 相对坐标就必须有）。"""
        return False

    def needs_as(self):
        """是否要求有 `as`（用了 `@s` 就必须有）。"""
        return "@s" in self.body()


# ---- 计分板
class SetScore(Act):
    def __init__(self, target, obj, value):
        self.t, self.o, self.v = target, obj, value

    def body(self):
        return "scoreboard players set %s %s %s" % (self.t, self.o, self.v)


class AddScore(Act):
    def __init__(self, target, obj, value=1):
        self.t, self.o, self.v = target, obj, value

    def body(self):
        return "scoreboard players add %s %s %s" % (self.t, self.o, self.v)


class SubScore(Act):
    def __init__(self, target, obj, value=1):
        self.t, self.o, self.v = target, obj, value

    def body(self):
        return "scoreboard players remove %s %s %s" % (self.t, self.o, self.v)


class OpScore(Act):
    """`scoreboard players operation <目标> <项> <op> <来源> <项>`"""

    OPS = {"=", "+=", "-=", "*=", "/=", "%=", "<", ">", "><"}

    def __init__(self, target, obj, operator, src, src_obj):
        if operator not in self.OPS:
            raise ValueError("不支持的运算符 %r（允许：%s）"
                             % (operator, " ".join(sorted(self.OPS))))
        self.t, self.o, self.op, self.s, self.so = target, obj, operator, src, src_obj

    def body(self):
        return "scoreboard players operation %s %s %s %s %s" % (
            self.t, self.o, self.op, self.s, self.so)


class ResetScore(Act):
    def __init__(self, target, obj):
        self.t, self.o = target, obj

    def body(self):
        return "scoreboard players reset %s %s" % (self.t, self.o)


# ---- 表现
class PlaySound(Act):
    def __init__(self, sound, target, pos="~~~", volume=1, pitch=1, min_volume=None):
        self.s, self.t, self.pos = sound, target, pos
        self.vol, self.pitch, self.mv = volume, pitch, min_volume

    def body(self):
        if self.mv is not None:
            return "playsound %s %s %s %s %s %s" % (
                self.s, self.t, self.pos, self.vol, self.pitch, self.mv)
        return "playsound %s %s %s %s %s" % (
            self.s, self.t, self.pos, self.vol, self.pitch)

    def needs_at(self):
        return self.pos.startswith("~")


class Particle(Act):
    def __init__(self, name, pos="~ ~ ~"):
        if not name.startswith("minecraft:") and ":" not in name:
            name = "minecraft:" + name
        self.n, self.pos = name, pos

    def body(self):
        return "particle %s %s" % (self.n, self.pos)

    def needs_at(self):
        return "~" in self.pos


class Title(Act):
    """`titleraw` / `tellraw` —— 传 rawtext 结构，自动序列化。"""

    def __init__(self, target, kind, rawtext):
        self.t, self.k, self.r = target, kind, rawtext

    def body(self):
        import json
        return "titleraw %s %s %s" % (
            self.t, self.k, json.dumps(self.r, ensure_ascii=False))


class Tellraw(Act):
    def __init__(self, target, rawtext):
        self.t, self.r = target, rawtext

    def body(self):
        import json
        return "tellraw %s %s" % (self.t, json.dumps(self.r, ensure_ascii=False))


class Camera(Act):
    """`camera <目标> <动作> ...` —— 只覆盖最常用的 set / fov / clear。"""

    def __init__(self, target, action, *args):
        self.t, self.a, self.args = target, action, args

    def body(self):
        return " ".join(["camera", str(self.t), self.a] + [str(a) for a in self.args])


class CameraShake(Act):
    def __init__(self, target, intensity, seconds, kind="positional"):
        self.t, self.i, self.s, self.k = target, intensity, seconds, kind

    def body(self):
        return "camerashake add %s %s %s %s" % (self.t, self.i, self.s, self.k)


# ---- 实体
class Summon(Act):
    def __init__(self, etype, pos="~ ~ ~", name=None, facing=None):
        self.e, self.pos, self.name, self.facing = etype, pos, name, facing

    def body(self):
        s = "summon %s %s" % (self.e, self.pos)
        if self.facing:
            s += " facing %s" % self.facing
        if self.name:
            s += " " + self.name          # 第 4、5 参数（生成事件 / 名字）
        return s

    def needs_at(self):
        return "~" in self.pos or (self.facing or "").startswith("^")


class Tp(Act):
    def __init__(self, target, dest):
        self.t, self.d = target, dest

    def body(self):
        return "tp %s %s" % (self.t, self.d)


class Kill(Act):
    def __init__(self, target):
        self.t = target

    def body(self):
        return "kill %s" % self.t


class Damage(Act):
    def __init__(self, target, amount, cause="entity_attack", source=None):
        self.t, self.a, self.c, self.s = target, amount, cause, source

    def body(self):
        s = "damage %s %s %s" % (self.t, self.a, self.c)
        if self.s:
            s += " entity %s" % self.s
        return s


class Effect(Act):
    def __init__(self, target, effect, seconds, amplifier, hide=True):
        self.t, self.e = target, effect
        self.sec, self.amp, self.hide = seconds, amplifier, hide

    def body(self):
        return "effect %s %s %s %s %s" % (
            self.t, self.e, self.sec, self.amp, "true" if self.hide else "false")


class Tag(Act):
    def __init__(self, target, tag, remove=False):
        self.t, self.g, self.rm = target, tag, remove

    def body(self):
        return "tag %s %s %s" % (self.t, "remove" if self.rm else "add", self.g)


# ---- 世界
class SetBlock(Act):
    def __init__(self, pos, block, states=None):
        self.pos, self.b, self.st = pos, block, states or {}

    def body(self):
        if not self.st:
            return "setblock %s %s" % (self.pos, self.b)
        st = ",".join('%s=%s' % (k, v) for k, v in self.st.items())
        return "setblock %s %s[%s]" % (self.pos, self.b, st)

    def needs_at(self):
        return "~" in self.pos


class Fill(Act):
    def __init__(self, a, b, block):
        self.a, self.b, self.blk = a, b, block

    def body(self):
        return "fill %s %s %s" % (self.a, self.b, self.blk)


class ReplaceItem(Act):
    def __init__(self, target, slot, item, count=1, data=0):
        self.t, self.s, self.i = target, slot, item
        self.c, self.d = count, data

    def body(self):
        return "replaceitem entity %s %s %s %s %s" % (
            self.t, self.s, self.c, self.i, self.d)


class Gamerule(Act):
    def __init__(self, rule, value):
        self.r, self.v = rule, value

    def body(self):
        return "gamerule %s %s" % (self.r, self.v)


class ScoreboardObj(Act):
    def __init__(self, action, obj, criteria=None, display=None):
        self.a, self.o, self.c, self.d = action, obj, criteria, display

    def body(self):
        if self.a == "add":
            return 'scoreboard objectives add %s %s "%s"' % (self.o, self.c, self.d or self.o)
        return "scoreboard objectives %s %s" % (self.a, self.o)


class Raw(Act):
    """逃生口：真的需要手写时用。**能不用就不用**，用了就失去校验。"""

    def __init__(self, cmd):
        self.c = cmd

    def body(self):
        return self.c


# ============================================================ 上下文
class Ctx:
    """execute 上下文。链式累积，`run()` 时一次性展开。

        Ctx().as_(P("@a")).at("@s").run(a, b, c)
        → 三条命令，共用同一个 `execute as ... at ... run`

    校验（编译期就报，不等进游戏）：
        · 用了 `@s` 却没 `as` → 报错
        · 用了 `~` 却没 `at`  → 报错
    """

    def __init__(self, parent=None):
        self.parts = list(parent.parts) if parent else []

    # ---- 累积
    def as_(self, sel):
        self.parts.append(("as", str(sel)))
        return self

    def at(self, sel):
        self.parts.append(("at", str(sel)))
        return self

    def positioned(self, pos):
        self.parts.append(("positioned", str(pos)))
        return self

    def rotated(self, rot):
        self.parts.append(("rotated", str(rot)))
        return self

    def facing(self, dest):
        self.parts.append(("facing", str(dest)))
        return self

    def align(self, axes):
        self.parts.append(("align", axes))
        return self

    def if_(self, cond):
        """`execute if ...` —— cond 是完整条件片段，如 `entity @a[scores={x=1}]`"""
        self.parts.append(("if", cond))
        return self

    def unless(self, cond):
        self.parts.append(("unless", cond))
        return self

    # ---- 展开
    def prefix(self):
        if not self.parts:
            return ""
        return "execute " + " ".join("%s %s" % (k, v) for k, v in self.parts) + " run "

    def run(self, *acts):
        """展开成命令列表。返回 list[str]，可直接塞进 `Chain(cmds=...)`。"""
        has_as = any(k == "as" for k, _ in self.parts)
        has_at = any(k == "at" for k, _ in self.parts)

        out = []
        for a in acts:
            if isinstance(a, str):
                a = Raw(a)
            if a.needs_as() and not has_as:
                raise ValueError(
                    "动作用了 `@s` 但没有 `as`：%s\n"
                    "  → 加 `.as_(P('@a'))`，否则命令无目标、静默不跑" % a.body())
            if a.needs_at() and not has_at:
                raise ValueError(
                    "动作用了 `~` 相对坐标但没有 `at`：%s\n"
                    "  → 加 `.at('@s')`，否则坐标相对命令方块" % a.body())
            out.append(self.prefix() + a.body())
        return out


def As(sel):
    return Ctx().as_(sel)


def At(sel):
    return Ctx().at(sel)


# ============================================================ 便捷：一次生成多条
def each(sels_acts):
    """把 [(选择器, [动作...]), ...] 展开成命令列表（批量枪型/批量距离用）。"""
    out = []
    for sel, acts in sels_acts:
        out.extend(Ctx().as_(sel).at("@s").run(*acts))
    return out


def selftest():
    """自检：结构正确性 + 校验规则。跑 `python dsl.py`。"""
    n = 0

    def eq(got, want, label):
        nonlocal n
        n += 1
        if got != want:
            print("  ✗ %s\n     得到 %r\n     期望 %r" % (label, got, want))
        else:
            print("  ✓ %s" % label)

    print("[选择器]")
    eq(str(P("@a")), "@a", "裸选择器")
    eq(str(P("@a", scores={"x": 1, "y": "1.."})),
       "@a[scores={x=1,y=1..}]", "scores 合并成一个花括号")
    eq(str(P("@e", type="xp_orb", scores={"b": 1}, r=1)),
       "@e[r=1,scores={b=1},type=xp_orb]", "多条件按 key 排序")
    eq(str(P("@a", scores={"x": None, "y": 1})),
       "@a[scores={y=1}]", "None 跳过")

    print("[上下文]")
    cmds = As(P("@a", scores={"s": 1})).at("@s").run(
        SetScore("@s", "cd", 12),
        PlaySound("random.orb", P("@a", r=20), pitch=2))
    eq(len(cmds), 2, "一个前缀展开两条")
    eq(cmds[0], "execute as @a[scores={s=1}] at @s run scoreboard players set @s cd 12",
       "计分板动作")
    eq(cmds[1], "execute as @a[scores={s=1}] at @s run playsound random.orb @a[r=20] ~~~ 1 2",
       "音效动作")

    print("[编译期校验]")
    for label, fn in [
        ("@s 无 as 报错", lambda: Ctx().at("@s").run(SetScore("@s", "x", 1))),
        ("~ 无 at 报错", lambda: As(P("@a")).run(Particle("endrod", "~ ~1 ~"))),
        ("未知选择器参数报错", lambda: P("@a", scroes={"x": 1})),
        ("未知运算符报错", lambda: OpScore("@s", "x", "===", "@s", "y")),
    ]:
        try:
            fn()
            print("  ✗ %s（应当报错却没报）" % label)
            n += 1
        except ValueError:
            print("  ✓ %s" % label)
            n += 1

    print("\n自检 %d 项完成" % n)
    return n


if __name__ == "__main__":
    selftest()
