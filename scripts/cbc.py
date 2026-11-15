#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cbc —— 命令方块编译器（Command Block Compiler）

**这个模块存在的唯一理由：断链结构不许再靠人手写。**

以前每条链的命令串是我一条条敲的，结果反复出现「复位块没条件位」「自断块漏了」
「`execute if entity @a` 没删」——因为结构藏在几百条字符串里，改一次漏一次。
现在把结构收进编译器：**你只写业务，编译器负责闸门 / 复位 / 自断 / 条件位**。

--------------------------------------------------------------------------
目标码（唯一合法布局，2026-11 用户定稿）

    gated 链（有闸门条件）：

        [0]   循环块  cond=0   检测  execute if entity <选择器>
        [1]   链块    cond=1   连接  setblock ~1 ~ ~ chain_command_block["facing_direction"=5]
        [2]   链块    cond=0   重置  setblock ~ ~ ~ chain_command_block["facing_direction"=4]
        [3..] 链块    cond=0   业务

    loop 链（闸门恒真 / 常驻）：

        [0]   循环块  cond=0   <业务第一条>
        [1..] 链块    cond=0   <业务>
        —— 没有闸门、没有复位块、没有自断块，链自己绕回来（U14）

--------------------------------------------------------------------------
三段式为什么能成立（关键在"朝向在触发那一刻就定了"）

    检测通过 → 连接块把 [2] 摆成朝东(5) → 连接块按**当时**的朝向激活 [2]
    → [2] 执行，把自己摆成朝西(4) → 本刻 [3] 照跑（触发关系已定，改朝向不影响本刻）
    → 下一时刻：连接块又把 [2] 摆回朝东，重新接上。

    所以"重置"块的语义是：**每刻把断点重置为断开**，再由"连接"块在检测通过时接回去。
    检测不通过 → 连接块被跳过（cond=1）→ [2] 保持朝西 → 业务一条都不跑。

`selftest()` 用模拟器验证这一点（朝向快照必须在执行前取）。
"""

from __future__ import annotations

# ---------------------------------------------------------------- 语句层
# 业务命令用这些函数拼，比裸字符串好读；编译器不解析它们，只负责排布。

def raw(cmd):
    """原样输出一条命令。"""
    return cmd


def setv(sel, obj, val):
    return "scoreboard players set %s %s %s" % (sel, obj, val)


def addv(sel, obj, val):
    return "scoreboard players add %s %s %s" % (sel, obj, val)


def subv(sel, obj, val):
    return "scoreboard players remove %s %s %s" % (sel, obj, val)


def opv(a_sel, a_obj, b_sel, b_obj, operator="="):
    return "scoreboard players operation %s %s %s %s %s" % (
        a_sel, a_obj, operator, b_sel, b_obj)


def when(cond, cmd):
    """`execute <cond> run <cmd>`，cond 不带 `run`。"""
    return "execute %s run %s" % (cond, cmd)


def as_(sel, cmd):
    return "execute as %s at @s run %s" % (sel, cmd)


def at(sel, cmd):
    return "execute at %s run %s" % (sel, cmd)


def tell(sel, rawtext):
    return "tellraw %s %s" % (sel, rawtext)


# ---------------------------------------------------------------- 链
class Chain:
    """一条功能链。`when=None` 或 `loop=True` → 常驻链（直接循环）。"""

    def __init__(self, cid, body, when=None, loop=False, button=False,
                 reset=None, note="", impulse=False):
        # when 只写**选择器**（如 `@a[hasitem=...]`），编译器负责补
        # `execute if entity ` 前缀——不许多写，免得拼出 `execute if entity entity @a`。
        self.id = cid
        self.body = [c for c in body if c]
        self.when = when
        # impulse 优先：它靠按钮触发，不是循环链
        self.loop = (not impulse) and (loop or when is None)
        self.button = button
        self.impulse = impulse
        self.reset = reset
        self.note = note
        if self.impulse and (self.when or loop):
            raise ValueError("%s：impulse 链不许带 when / loop（它靠按钮触发）" % cid)
        if self.loop and self.when:
            raise ValueError("%s：loop 链不许带 when（那等于没删 execute if entity）"
                             % cid)
        if self.when and (self.when.lstrip().startswith("execute")
                          or self.when.lstrip().startswith("entity ")):
            raise ValueError("%s：when 只写选择器，不要写 execute（编译器自己加）"
                             % cid)
        if not self.body:
            raise ValueError("%s：空链" % cid)

    # ---- 编译：链 → 命令方块规格 ----
    def compile(self):
        if self.impulse:
            # 脉冲链：链首是脉冲块（auto=0，等按钮），没有闸门 / 复位 / 自断
            return {"id": self.id, "kind": "impulse", "button": True,
                    "cmds": list(self.body)}
        if self.loop:
            # 常驻链：循环块直接装第一条业务，后面接链块。无闸门 / 无复位 / 无自断。
            return {"id": self.id, "kind": "repeat", "button": self.button,
                    "cmds": list(self.body)}
        return {
            "id": self.id, "kind": "gated", "button": self.button,
            "gate": "execute if entity " + self.when,
            "reset": self.reset,
            # 三段式（用户 U3 定稿）：检测 → 连接 → **重置** → 业务
            # 重置块紧跟在连接块的**下一条**，不在链尾。
            "cmds": ["{RESET}"] + list(self.body),
        }


class Program:
    def __init__(self, name=""):
        self.name = name
        self.chains = []

    def chain(self, cid, body=None, when=None, loop=False, button=False,
              reset=None, note="", impulse=False):
        c = Chain(cid, body or [], when=when, loop=loop, button=button,
                  reset=reset, note=note, impulse=impulse)
        self.chains.append(c)
        return c

    def emit(self):
        """给 build_cbworld 的 system 字典。"""
        return {"chains": [c.compile() for c in self.chains]}

    def report(self):
        rows = []
        for c in self.chains:
            if c.loop:
                rows.append("  %-10s loop   业务 %2d 条（无闸门 / 无连接 / 无重置）"
                            % (c.id, len(c.body)))
            elif c.impulse:
                rows.append("  %-10s 脉冲   业务 %2d 条（按钮触发）"
                            % (c.id, len(c.body)))
            else:
                rows.append("  %-10s gated  业务 %2d 条（检测+连接+重置）  检测 %s"
                            % (c.id, len(c.body), c.when))
        return "\n".join(rows)


# ---------------------------------------------------------------- 模拟器
# 只模拟"链会不会跑"，不模拟具体游戏效果：业务命令一律算成功，
# 唯一有副作用的是 setblock（改朝向 = 物理断开 / 接通）。

FD_NEXT = 5      # 朝东 = 指向下一格
FD_PREV = 4      # 朝西 = 指回上一格


class _Blk:
    __slots__ = ("kind", "fd", "cond", "cmd", "auto", "gate")

    def __init__(self, kind, cmd, cond=0, fd=FD_NEXT, auto=1, gate=False):
        self.kind, self.cmd, self.cond, self.fd, self.auto, self.gate = (
            kind, cmd, cond, fd, auto, gate)


RESET = ('setblock ~ ~ ~ chain_command_block["facing_direction"=%d]' % FD_PREV)


def _layout(chain_spec):
    """把 compile() 的产物摊成一条直线上的方块序列（+x 方向）。

    真实生成器里 `{RESET}` / `{CUT}` 由 build_cbworld 按几何现算（蛇形换行时
    "朝后"是南/北），这里整条链沿 +x 摆，所以"朝后"固定是西(4)。
    """
    blks = []
    if chain_spec["kind"] in ("repeat", "impulse"):
        for i, c in enumerate(chain_spec["cmds"]):
            blks.append(_Blk("rep" if i == 0 else "chain", c,
                             auto=0 if (i == 0 and chain_spec.get("button")) else 1))
        return blks
    blks.append(_Blk("rep", chain_spec["gate"], gate=True))          # [0] 检测
    blks.append(_Blk("chain", chain_spec.get("reset") or
                     'setblock ~1 ~ ~ chain_command_block["facing_direction"=%d]'
                     % FD_NEXT, cond=1))                            # [1] 连接（有条件）
    for c in chain_spec["cmds"]:                                    # [2] 重置 + [3..] 业务
        blks.append(_Blk("chain", RESET if c == "{RESET}" else
                         RESET if c == "{CUT}" else c))
    return blks


def _target(i, cmd):
    """解析 setblock 的相对偏移 → 目标索引。"""
    if not cmd.startswith("setblock"):
        return None
    tok = cmd.split()[1]
    if not tok.startswith("~"):
        return None
    if tok == "~":
        return i
    return i + int(tok[1:])


def _fd_of(cmd):
    if '"facing_direction"=' not in cmd:
        return None
    return int(cmd.split('"facing_direction"=')[1][0])


def tick(blks, gate_ok):
    """跑一刻，返回本刻真正执行过的业务命令列表。

    ❗ 关键语义：**朝向在触发那一刻就定了**。命令方块执行完自己的命令后，
       "下一格"是沿它**进入执行时**的朝向找的 —— 重置块执行时把自己摆成朝西，
       只影响下一刻，本刻 [3..] 照跑。所以这里先存 fd_before 再跑命令。
    """
    ran, done = set(), []

    def run(i, prev_ok=True):
        if not (0 <= i < len(blks)) or i in ran:
            return False
        b = blks[i]
        if b.cond == 1 and not prev_ok:
            return False                      # 连接块：检测失败就跳过
        ran.add(i)
        fd_before = b.fd                      # ← 朝向快照，必须在跑命令之前取
        if b.kind == "rep":
            ok = gate_ok
            if not b.gate:
                done.append(b.cmd)          # 常驻链：循环块装的就是业务
        else:
            ok = True
            tgt = _target(i, b.cmd)
            if tgt is not None:
                fd = _fd_of(b.cmd)
                if fd is not None and 0 <= tgt < len(blks):
                    blks[tgt].fd = fd          # 物理改朝向（下一刻生效）
            else:
                done.append(b.cmd)
        # 沿朝向传播：朝东 → i+1，朝西 → i-1
        nxt = (i + 1 if fd_before == FD_NEXT
               else i - 1 if fd_before == FD_PREV else None)
        if nxt is not None and 0 <= nxt < len(blks):
            nb = blks[nxt]
            if nb.cond == 1 and not ok:
                return ok
            run(nxt, ok)
        return ok

    run(0)
    return done


def simulate(chain_spec, ticks, gate=lambda t: True, script=None):
    """跑 n 刻，返回 (业务执行次数, 每刻明细)。

    script: {刻号: 动作}，动作 "dis" = 断开（把复位块摆朝西）、"arm" = 接通。
    """
    blks = _layout(chain_spec)
    total, log = 0, []
    for t in range(ticks):
        act = (script or {}).get(t)
        if act == "dis":
            blks[1].fd = FD_PREV
        elif act == "arm":
            blks[1].fd = FD_NEXT
        n = len(tick(blks, gate(t)))
        total += n
        log.append(n)
    return total, log


# ---------------------------------------------------------------- 自检
def selftest():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print("  %s %-46s %s" % ("✓" if cond else "✗", name, detail))
        ok = ok and cond

    p = Program("selftest")
    p.chain("demo", ["A"], when="@a[tag=x]")
    p.chain("clock", ["T1", "T2"], loop=True)
    spec = p.emit()["chains"]

    gated = [c for c in spec if c["id"] == "demo"][0]
    loopc = [c for c in spec if c["id"] == "clock"][0]

    print("编译产物：")
    for c in spec:
        if c["kind"] == "gated":
            print("  %s: 闸门=%s / 业务=%d / 末条=%s"
                  % (c["id"], c["gate"], len(c["cmds"]) - 1, c["cmds"][-1]))
        else:
            print("  %s: kind=repeat / 业务=%d（无闸门）" % (c["id"], len(c["cmds"])))

    print("\n行为验证（模拟器）：")
    n, log = simulate(gated, 5, gate=lambda t: True)
    check("检测恒通 → 业务每刻跑 1 次", n == 5, "5 刻跑了 %d 次 %s" % (n, log))

    n2, _ = simulate(gated, 5, gate=lambda t: t < 2)
    check("检测第 3 刻起失败 → 业务停", n2 == 2, "5 刻跑了 %d 次" % n2)

    n3, _ = simulate(gated, 6, gate=lambda t: True, script={3: "dis"})
    check("第 4 刻外部断开 → 业务停", n3 == 3, "6 刻跑了 %d 次" % n3)

    n4, _ = simulate(gated, 8, gate=lambda t: True, script={3: "dis", 5: "arm"})
    check("断开后再接通 → 业务恢复", n4 == 6, "8 刻跑了 %d 次" % n4)

    # 反例：连接块（[1]）丢了 conditional_bit → 检测失败也每刻把重置块接回去
    # → 业务照样跑 = 「闸门形同虚设 / 枪永远在响」。这条是 U3 里最容易漏的一位。
    bad = _layout(gated)
    bad[1].cond = 0
    nb = 0
    for _ in range(5):
        nb += len(tick(bad, False))
    check("反例：连接块没条件位 → 检测失败也跑", nb == 5,
          "检测恒假还跑了 %d 次（这就是「空转」）" % nb)

    # 常驻链：没有闸门 / 复位 / 自断
    check("常驻链没有闸门字段", "gate" not in loopc)
    check("常驻链不带重置块", "{RESET}" not in loopc["cmds"])
    check("常驻链首块是循环块", loopc["kind"] == "repeat")
    nl, _ = simulate(loopc, 4, gate=lambda t: True)
    check("常驻链每刻都跑", nl == 8, "4 刻 × 2 条 = %d" % nl)

    # 三段式的排布断言：检测 → 连接 → 重置 → 业务
    lay = _layout(gated)
    check("布局 [1] 是连接块（有条件）", lay[1].cond == 1, lay[1].cmd[:40])
    check("布局 [2] 是重置块（无条件）", lay[2].cmd == RESET and lay[2].cond == 0,
          lay[2].cmd)
    check("布局 [3] 起才是业务", lay[3].cmd == "A", lay[3].cmd[:40])

    print("\n结论：%s" % ("全部通过" if ok else "有失败项"))
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
