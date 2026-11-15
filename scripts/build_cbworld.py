#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_cbworld.py —— 生成「已内置命令方块」的基岩版 .mcworld（纯命令方块，无行为包）。

原理：直接写出 LevelDB 数据库（子区块地形 + 方块实体），游戏导入后命令方块就在世界里。
逆向格式见 SKILL.md 第 1–4 章（容器 / level.dat / LevelDB / 子区块）；
布局规则见 SKILL.md 第 9 章与「第一部分 · 四、摆放规范」。

用法：
  python build_cbworld.py --template <任一真实存档.mcworld> --name "世界名" \
         --spawn 8 -60 7 --out 输出.mcworld

注意：
  · --template 必须是**真实游戏导出的存档**（借它的 level.dat 键集与版本号）
  · 命令方块放在 y=-60、按钮 y=-59、地面 y=-61（与平地世界对齐）
  · 链超出一行会自动蛇形拐弯并跨区块，无需手工分块
"""
import argparse
import math
import re
import struct
import zipfile

# ---------------------------------------------------------------- CRC32C
_POLY = 0x82F63B78
_TABLE = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ _POLY if _c & 1 else _c >> 1
    _TABLE.append(_c)


def crc32c(data):
    crc = 0xFFFFFFFF
    for b in data:
        crc = (crc >> 8) ^ _TABLE[(crc ^ b) & 0xFF]
    return crc ^ 0xFFFFFFFF


def _mask(c):
    return (((c >> 15) | (c << 17)) + 0xA282EAD8) & 0xFFFFFFFF


def _varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


# ---------------------------------------------------------------- NBT（小端）
TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG = 1, 2, 3, 4
TAG_FLOAT, TAG_DOUBLE, TAG_BYTE_ARRAY, TAG_STRING = 5, 6, 7, 8
TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY = 9, 10, 11
BLOCK_VERSION = 0x01150100


def _wstr(s):
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def nbt_value(tag, v):
    if tag == TAG_BYTE: return struct.pack("<b", v)
    if tag == TAG_SHORT: return struct.pack("<h", v)
    if tag == TAG_INT: return struct.pack("<i", v)
    if tag == TAG_LONG: return struct.pack("<q", v)
    if tag == TAG_FLOAT: return struct.pack("<f", v)
    if tag == TAG_DOUBLE: return struct.pack("<d", v)
    if tag == TAG_STRING: return _wstr(v)
    if tag == TAG_BYTE_ARRAY: return struct.pack("<i", len(v)) + bytes(v)
    if tag == TAG_INT_ARRAY:
        return struct.pack("<i", len(v)) + b"".join(struct.pack("<i", x) for x in v)
    if tag == TAG_LIST:
        et, items = v
        out = struct.pack("<b", et) + struct.pack("<i", len(items))
        for it in items:
            out += nbt_value(et, it)
        return out
    if tag == TAG_COMPOUND:
        return nbt_compound(v, named=True)
    raise ValueError(f"unsupported tag {tag}")


def nbt_compound(d, named=True):
    body = b""
    for k, (t, v) in d.items():
        body += struct.pack("<b", t) + _wstr(k) + nbt_value(t, v)
    body += b"\x00"
    return body if named else b"\x0a" + _wstr("") + body


def pack_block_entry(name, states):
    d = {
        "name": (TAG_STRING, name),
        "states": (TAG_COMPOUND, dict(states)),
        "version": (TAG_INT, BLOCK_VERSION),
    }
    return nbt_compound(d, named=False)


# ---------------------------------------------------------------- 方块定义
# 状态值必须带正确类型：facing_direction 是 INT，*_bit 是 BYTE
EAST, SOUTH, WEST, NORTH, UP = 5, 3, 4, 2, 1
BLOCK_DEFS = {
    "air": ("minecraft:air", {}),
    "bedrock": ("minecraft:bedrock", {"infiniburn_bit": (TAG_BYTE, 0)}),
    "dirt": ("minecraft:dirt", {"dirt_type": (TAG_STRING, "normal")}),
    "grass": ("minecraft:grass_block", {}),
    "imp_E": ("minecraft:command_block",
              {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, EAST)}),
    "imp_S": ("minecraft:command_block",
              {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, SOUTH)}),
    "imp_N": ("minecraft:command_block",
              {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, NORTH)}),
    "rep_E": ("minecraft:repeating_command_block",
              {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, EAST)}),
    "rep_S": ("minecraft:repeating_command_block",
              {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, SOUTH)}),
    "rep_W": ("minecraft:repeating_command_block",
              {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, WEST)}),
    "rep_N": ("minecraft:repeating_command_block",
              {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, NORTH)}),
    "ch_E": ("minecraft:chain_command_block",
             {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, EAST)}),
    "ch_W": ("minecraft:chain_command_block",
             {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, WEST)}),
    "ch_S": ("minecraft:chain_command_block",
             {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, SOUTH)}),
    "ch_N": ("minecraft:chain_command_block",
             {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, NORTH)}),
    # 末块专用：朝上指空气 = 天然终点，永不回指前一块（手册第 66.3 节）
    "ch_U": ("minecraft:chain_command_block",
             {"conditional_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, UP)}),
    "chc_E": ("minecraft:chain_command_block",
              {"conditional_bit": (TAG_BYTE, 1), "facing_direction": (TAG_INT, EAST)}),
    "chc_W": ("minecraft:chain_command_block",
              {"conditional_bit": (TAG_BYTE, 1), "facing_direction": (TAG_INT, WEST)}),
    "chc_S": ("minecraft:chain_command_block",
              {"conditional_bit": (TAG_BYTE, 1), "facing_direction": (TAG_INT, SOUTH)}),
    "chc_N": ("minecraft:chain_command_block",
              {"conditional_bit": (TAG_BYTE, 1), "facing_direction": (TAG_INT, NORTH)}),
    "chc_U": ("minecraft:chain_command_block",
              {"conditional_bit": (TAG_BYTE, 1), "facing_direction": (TAG_INT, UP)}),
    "btn": ("minecraft:stone_button",
            {"button_pressed_bit": (TAG_BYTE, 0), "facing_direction": (TAG_INT, UP)}),
    # 指令区地板（3 层，比原来 4 层省 25% 方块）
    # 中间黑玻璃 + 边缘深色石边框：暗底托亮 UI，粘贴后边界清楚
    # 若游戏里显示成空气，把 black_stained_glass 换成 black_concrete（只改这一行）
    "stone": ("minecraft:stone", {}),
    # ❗ 不要用 black_stained_glass：网易服部分版本认不出，粘出来是「未知方块」。
    #    地板一律用 concrete / 石头系（全版本都有）。
    "floor": ("minecraft:black_concrete", {}),
    "floor_fill": ("minecraft:black_concrete", {}),
    "floor_edge": ("minecraft:polished_blackstone", {}),
    # 染色玻璃：每 10 行一条，用来给指令区分段。
    # ❗ 用基础 id `stained_glass`，不用 `black_stained_glass` 那种带颜色的命名 id
    #    （网易服部分版本认不出，粘出来是「未知方块」）。
    "floor_band": ("minecraft:stained_glass", {}),
    "floor_btn": ("minecraft:stone_bricks", {}),
    # 说明区：箱子（容器实体装注释物品）+ 立式告示牌（注释文字）
    # 若游戏里显示成空气，按注释换备选 ID（只改这一行）：
    #   箱子  minecraft:chest              → minecraft:trapped_chest
    #   告示牌 minecraft:oak_standing_sign → minecraft:standing_sign
    "chest": ("minecraft:chest", {}),
    "sign": ("minecraft:oak_standing_sign",
             {"ground_sign_direction": (TAG_INT, 8)}),
}


# 指令区宽度（每行摆多少个命令方块）。
#
# ❗ 为什么不是 16：蛇形链的**深度 = 方块数 / 宽度**。一条 100 格射程的枪
#    要 6000 多个方块，16 宽就是 400 多行 —— 远超区块加载范围，
#    链尾那些方块根本不 tick，表现就是「只有最前面几条命令在跑」。
#    加宽到 128 后 6000 个方块只有 47 行，整块指令区都在加载范围内。
#    （加载范围看模拟距离，通常 4~12 区块 = 64~192 格；128 宽 × 75 行能整块装下。）
W = 64

# 二楼（第二层指令区）的垂直间距。命令方块在 y0，按钮 y0+1，地板 y0-1。
# 14 格：两层之间留 12 格净空，抬头能看见、不影响红石/射线。
FLOOR_GAP = 14

# 每隔多少行铺一条染色玻璃带（视觉分段，找链的时候好数）
BAND_EVERY = 10


def make_floor(blocks, w=None, d=16, top=3, single=False):
    """铺指令区地板：3 层 + 边缘一圈深色边框 + 按钮位标记。

    top = 子区块局部 y 的地板顶面（世界 y = top - 64）。
    命令方块放 top+1，按钮放 top+2。

    层次：
        top-2  bedrock                兜底，防止挖穿掉虚空
        top-1  black_concrete         衬底（透过玻璃看到的是黑，不是灰）
        top    black_stained_glass    面层：黑玻璃，暗底托亮 UI
               边缘一圈 polished_blackstone → 粘贴后边界一眼可见
               按钮正下方 stone_bricks     → 一眼看出哪里能按
    """
    w = W if w is None else w
    for x in range(w):
        for z in range(d):
            if single:
                # 二楼：**只铺一层染色玻璃**，不垫 bedrock / 混凝土（用户要求）
                blocks[(x, top, z)] = "floor_band"
                continue
            blocks[(x, top - 2, z)] = "bedrock"
            blocks[(x, top - 1, z)] = "floor_fill"
            edge = (x in (0, w - 1)) or (z in (0, d - 1))
            # 每 BAND_EVERY 行铺一条染色玻璃带：站在机器上一眼数得清第几段
            band = (z % BAND_EVERY == 0)
            blocks[(x, top, z)] = ("floor_edge" if edge else
                                   ("floor_band" if band else "floor"))

def encode_subchunk(y, blocks):
    """blocks: {(局部x, 局部y, 局部z): 方块键}。调色板第 0 项必须是空气。"""
    used = ["air"] + sorted({v for v in blocks.values() if v != "air"})
    remap = {k: i for i, k in enumerate(used)}
    bits = max(1, math.ceil(math.log2(max(2, len(used)))))
    bpw = 32 // bits
    words = math.ceil(4096 / bpw)
    arr = [0] * words
    for (x, yy, z), key in blocks.items():
        slot = (x << 8) | (z << 4) | yy
        arr[slot // bpw] |= remap[key] << ((slot % bpw) * bits)

    out = bytearray()
    out += bytes([9, 2, y & 0xFF])            # 版本 9 / 两层 / y
    out += bytes([(bits << 1) | 0])           # storageVersion（bits 在 bit1 起）
    out += struct.pack("<" + "I" * words, *arr)
    out += struct.pack("<I", len(used))       # 调色板计数（4 字节，不是 varint）
    for key in used:
        out += pack_block_entry(*BLOCK_DEFS[key])
    out += bytes([0])                         # 第二层：单方块空气
    out += pack_block_entry("minecraft:air", {})
    return bytes(out)


# ---------------------------------------------------------------- 方块实体
# 命令方块控制台（方块界面里的「上一个输出」）是否保留：
#   1 = 保留，交付默认。出问题点开方块就能看 Syntax error / No targets matched，
#       这是唯一的内置日志，删了只能靠猜。代价只是每个方块几十字节。
#   0 = 静默。只在"方块摆在玩家能点到的公共区域"时才用。
# 注意：这是**方块 NBT**，`gamerule commandblockoutput` 只管聊天栏，管不到这里。
TRACK_OUTPUT = 1


def cb_entity(x, y, z, cmd, auto, cond=0, track=None, name=""):
    """`name` → CustomName：每个方块的作用自述（见 CHAIN_LABEL / _tag）。"""
    t = TRACK_OUTPUT if track is None else track
    d = {
        "id": (TAG_STRING, "CommandBlock"),
        "x": (TAG_INT, x), "y": (TAG_INT, y), "z": (TAG_INT, z),
        "Command": (TAG_STRING, cmd),
        "auto": (TAG_BYTE, auto),
        "conditionalMode": (TAG_BYTE, cond),
        "conditionMet": (TAG_BYTE, 1),
        "ExecuteOnFirstTick": (TAG_BYTE, 0),
        "powered": (TAG_BYTE, 0),
        "TickDelay": (TAG_INT, 0),
        "TrackOutput": (TAG_BYTE, t),
        "LastOutput": (TAG_STRING, ""),
        "LastOutputParams": (TAG_LIST, (TAG_STRING, [])),
        "LastExecution": (TAG_LONG, 0),
        "SuccessCount": (TAG_INT, 0),
        "CustomName": (TAG_STRING, name),
        "LPCommandMode": (TAG_BYTE, 0),
        "LPCondionalMode": (TAG_BYTE, 0),
        "LPRedstoneMode": (TAG_BYTE, 0),
        "Version": (TAG_INT, 39),
        "isMovable": (TAG_BYTE, 1),
    }
    return nbt_compound(d, named=False)


# ---------------------------------------------------------------- 说明区（箱子 / 告示牌）
# 为什么说明要写进世界：
#   `/givenbt` 是**插件/服务端指令**，不是原版指令；原版 `give` 不接受 NBT，
#   所以带 Lore 的物品没法用指令发。唯一稳的做法是把物品写进**容器方块实体**，
#   随 .mcstructure 一起粘出去 —— 玩家开箱拿到的是成品，取出来 NBT 也不掉。
#
# 这条路线的好处：不依赖任何插件、不改行为包、结构文件粘过去就有。

# ---------------------------------------------------------------- SNBT 解析
# 用途：网上流传的 /givenbt 写法里那段 SNBT 字符串
#   "{top_layer_1:'feather',display:{Name:'§r§n⫸§f暴怒',Lore:['...']},Unbreakable:1b}"
# 可以直接解析成 NBT 类型树，塞进容器方块实体（原版无 givenbt，见 SKILL.md 第 98 章）。

class SnbtError(ValueError):
    pass


def _skip_ws(s, i):
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    return i


def _snbt_quoted(s, i):
    q = s[i]
    i += 1
    out = []
    esc = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'", '"': '"', "0": "\0"}
    while i < len(s):
        c = s[i]
        if c == "\\":
            if i + 1 >= len(s):
                raise SnbtError("转义符后面没东西了")
            out.append(esc.get(s[i + 1], s[i + 1]))
            i += 2
            continue
        if c == q:
            return "".join(out), i + 1
        out.append(c)
        i += 1
    raise SnbtError("字符串没有闭合引号")


def _snbt_key(s, i):
    i = _skip_ws(s, i)
    if i < len(s) and s[i] in "'\"":
        return _snbt_quoted(s, i)
    st = i
    while i < len(s) and s[i] not in ": \t\r\n":
        i += 1
    if st == i:
        raise SnbtError("位置 %d 处缺键名" % i)
    return s[st:i], i


def _snbt_bare(s, i):
    st = i
    while i < len(s) and s[i] not in ",}] \t\r\n":
        i += 1
    if st == i:
        raise SnbtError("位置 %d 处缺值" % i)
    return s[st:i], i


def _is_int(x):
    try:
        int(x)
        return True
    except ValueError:
        return False


def _is_float(x):
    try:
        f = float(x)
    except ValueError:
        return False
    return f == f and f not in (float("inf"), float("-inf"))


def _snbt_scalar(raw):
    if raw in ("true", "True"):
        return (TAG_BYTE, 1)
    if raw in ("false", "False"):
        return (TAG_BYTE, 0)
    if len(raw) > 1:
        suf, body = raw[-1], raw[:-1]
        if suf in "bB" and _is_int(body):
            return (TAG_BYTE, int(body))
        if suf in "sS" and _is_int(body):
            return (TAG_SHORT, int(body))
        if suf in "lL" and _is_int(body):
            return (TAG_LONG, int(body))
        if suf in "fF" and _is_float(body):
            return (TAG_FLOAT, float(body))
        if suf in "dD" and _is_float(body):
            return (TAG_DOUBLE, float(body))
    if _is_int(raw):
        return (TAG_INT, int(raw))
    if _is_float(raw):
        return (TAG_DOUBLE, float(raw))
    return (TAG_STRING, raw)


def _snbt_value(s, i):
    i = _skip_ws(s, i)
    if i >= len(s):
        raise SnbtError("值缺失")
    c = s[i]
    if c == "{":
        return _snbt_compound(s, i)
    if c == "[":
        return _snbt_list(s, i)
    if c in "'\"":
        v, i = _snbt_quoted(s, i)
        return (TAG_STRING, v), i
    raw, i = _snbt_bare(s, i)
    return _snbt_scalar(raw), i


def _snbt_compound(s, i):
    i += 1
    d = {}
    i = _skip_ws(s, i)
    if i < len(s) and s[i] == "}":
        return (TAG_COMPOUND, d), i + 1
    while True:
        k, i = _snbt_key(s, i)
        i = _skip_ws(s, i)
        if i >= len(s) or s[i] != ":":
            raise SnbtError("键 %r 后面缺冒号" % k)
        node, i = _snbt_value(s, i + 1)
        d[k] = node
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == ",":
            i += 1
            continue
        if i < len(s) and s[i] == "}":
            return (TAG_COMPOUND, d), i + 1
        raise SnbtError("复合里少了逗号或 }")


def _snbt_list(s, i):
    i += 1
    i = _skip_ws(s, i)
    if i + 1 < len(s) and s[i] in "BIL" and s[i + 1] == ";":
        kind = s[i]
        i += 2
        vals = []
        while True:
            i = _skip_ws(s, i)
            if i < len(s) and s[i] == "]":
                i += 1
                break
            node, i = _snbt_value(s, i)
            vals.append(node[1])
            i = _skip_ws(s, i)
            if i < len(s) and s[i] == ",":
                i += 1
                continue
            if i < len(s) and s[i] == "]":
                i += 1
                break
            raise SnbtError("数组里少了逗号或 ]")
        if kind == "B":
            return (TAG_BYTE_ARRAY, bytes(v & 0xFF for v in vals)), i
        if kind == "I":
            return (TAG_INT_ARRAY, vals), i
        raise SnbtError("[L; 长整数组暂不支持（用不到）")
    if i < len(s) and s[i] == "]":
        return (TAG_LIST, (TAG_STRING, [])), i + 1
    items = []
    while True:
        node, i = _snbt_value(s, i)
        items.append(node)
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == ",":
            i += 1
            continue
        if i < len(s) and s[i] == "]":
            i += 1
            break
        raise SnbtError("列表里少了逗号或 ]")
    et = items[0][0]
    for t, _ in items:
        if t != et:
            raise SnbtError("列表元素类型不一致：%d 与 %d" % (et, t))
    return (TAG_LIST, (et, [v for _, v in items])), i


def parse_snbt(text):
    """SNBT 字符串 → (tag, value)。

    支持：`{}` 复合 / `[]` 列表 / `[B;` `[I;` 数组 / `'x'` `"x"` 字符串 /
    数字后缀 `b s L f d` / `true` `false`。
    """
    s = text.strip()
    if not s:
        raise SnbtError("空字符串")
    node, i = _snbt_value(s, 0)
    i = _skip_ws(s, i)
    if i != len(s):
        raise SnbtError("末尾有多余字符：%r" % s[i:])
    return node


def snbt_to_tag(text):
    """SNBT → 可直接塞进 `tag:` 的复合字典。"""
    node = parse_snbt(text)
    if node[0] != TAG_COMPOUND:
        raise SnbtError("顶层必须是复合 {...}")
    return node[1]


def item_from_snbt(item_id, snbt="", count=1, damage=0, slot=None):
    """把 givenbt 那段 SNBT 直接做成一件容器物品。

    例子：
        B.item_from_snbt("leather_chestplate",
            "{top_layer_1:'feather',display:{Name:'§r§n⫸§f暴怒',"
            "Lore:['§r§7第一行','§r§7第二行']},Unbreakable:1b}", slot=0)
    """
    tag = snbt_to_tag(snbt) if snbt and snbt.strip() else {}
    d = {
        "Name": (TAG_STRING, item_id if ":" in item_id else "minecraft:" + item_id),
        "Count": (TAG_BYTE, count),
        "Damage": (TAG_SHORT, damage),
        "WasPickedUp": (TAG_BYTE, 0),
    }
    if slot is not None:
        d["Slot"] = (TAG_BYTE, slot)
    if tag:
        d["tag"] = (TAG_COMPOUND, tag)
    return d


def dump_tag(node, indent=0):
    """NBT 类型树 → 人看的文本（排查类型错用）。"""
    names = {1: "byte", 2: "short", 3: "int", 4: "long", 5: "float",
             6: "double", 7: "byte[]", 8: "string", 9: "list",
             10: "compound", 11: "int[]"}
    pad = "  " * indent
    t, v = node
    if t == TAG_COMPOUND:
        lines = ["{"]
        for k, sub in v.items():
            sub_lines = dump_tag(sub, indent + 1).splitlines()
            lines.append("%s  %s: %s" % (pad, k, sub_lines[0]))
            lines.extend(sub_lines[1:])
        lines.append(pad + "}")
        return "\n".join(lines)
    if t == TAG_LIST:
        et, items = v
        lines = ["list<%s> [%d]" % (names.get(et, et), len(items))]
        for it in items:
            lines.append("%s  %s" % (pad, dump_tag((et, it), indent + 1)))
        return "\n".join(lines)
    if t == TAG_STRING:
        return "%s  \"%s\"" % (pad, v)
    return "%s  %s(%r)" % (pad, names.get(t, t), v)


def _tv(v):
    """Python 值 → (tag, value)。只用于 tag 里的自定义键。"""
    if isinstance(v, bool):
        return (TAG_BYTE, 1 if v else 0)
    if isinstance(v, int):
        return (TAG_INT, v)
    if isinstance(v, float):
        return (TAG_FLOAT, v)
    if isinstance(v, str):
        return (TAG_STRING, v)
    if isinstance(v, dict):
        return (TAG_COMPOUND, {k: _tv(x) for k, x in v.items()})
    if isinstance(v, list):
        if v and isinstance(v[0], dict):
            return (TAG_LIST, (TAG_COMPOUND, [{k: _tv(x) for k, x in d.items()} for d in v]))
        return (TAG_LIST, (TAG_STRING, [str(x) for x in v]))
    raise ValueError("不支持的 NBT 值：%r" % (v,))


def item_nbt(name, count=1, damage=0, display_name=None, lore=None,
             unbreakable=False, extra=None, slot=None):
    """一件容器物品的 NBT。

    name          物品 ID（`leather_chestplate` 或 `minecraft:leather_chestplate`）
    display_name  显示名，可带 § 颜色码
    lore          描述行列表，每行一条，可带 § 码
    unbreakable   不可破坏（饰品 / 纪念品）
    extra         追加进 tag 的自定义键，如 {"暴怒": 1}
    """
    tag = {}
    disp = {}
    if display_name:
        disp["Name"] = (TAG_STRING, display_name)
    if lore:
        disp["Lore"] = (TAG_LIST, (TAG_STRING, list(lore)))
    if disp:
        tag["display"] = (TAG_COMPOUND, disp)
    if unbreakable:
        tag["Unbreakable"] = (TAG_BYTE, 1)
    for k, v in (extra or {}).items():
        tag[k] = _tv(v)

    d = {
        "Name": (TAG_STRING, name if ":" in name else "minecraft:" + name),
        "Count": (TAG_BYTE, count),
        "Damage": (TAG_SHORT, damage),
        "WasPickedUp": (TAG_BYTE, 0),
    }
    if slot is not None:
        d["Slot"] = (TAG_BYTE, slot)
    if tag:
        d["tag"] = (TAG_COMPOUND, tag)
    return d


def container_entity(x, y, z, items, custom_name=""):
    """箱子方块实体。x/y/z 必须是**世界坐标**。"""
    d = {
        "id": (TAG_STRING, "Chest"),
        "x": (TAG_INT, x), "y": (TAG_INT, y), "z": (TAG_INT, z),
        "Findable": (TAG_BYTE, 0),
        "CustomName": (TAG_STRING, custom_name),
        "Items": (TAG_LIST, (TAG_COMPOUND, list(items))),
    }
    return nbt_compound(d, named=False)


def sign_entity(x, y, z, front, back=None, color=-16777216):
    """告示牌方块实体（1.20+ 的 FrontText / BackText）。

    front / back：字符串列表，最多 4 行，可用 § 颜色码。
    color：文字颜色，默认 -16777216（黑）。
    """
    def side(lines):
        return {
            "Text": (TAG_STRING, "\n".join(list(lines)[:4])),
            "PersistFormatting": (TAG_BYTE, 1),
            "SignTextColor": (TAG_INT, color),
            "HideGlowOutline": (TAG_BYTE, 0),
            "IgnoreLegacy": (TAG_BYTE, 0),
        }

    d = {
        "id": (TAG_STRING, "Sign"),
        "x": (TAG_INT, x), "y": (TAG_INT, y), "z": (TAG_INT, z),
        "FrontText": (TAG_COMPOUND, side(front)),
        "BackText": (TAG_COMPOUND, side(back or [])),
        "IsWaxed": (TAG_BYTE, 0),
    }
    return nbt_compound(d, named=False)


def place_props(blocks, depth, props, y=4, pedestal=False):
    """把说明区摆到**最前面几行**（z 小的方向），返回 [(wx, wy, wz, nbt_bytes)]。

    props 每项：
        {"kind": "chest", "items": [item_nbt(...)...], "name": "自定义名"}
        {"kind": "sign",  "front": ["第一行", ...], "back": [...]}
    可选 "at": (x, z) 指定位置，不指定就按顺序找空格。

    ❗ `pedestal=True`：先垫一格黑混凝土，物品抬到 `y+1`。
      命令方块在 y=4，玩家站在机器上往下看，同层的箱子/告示牌**在脚边**，
      很容易被当成"没生成"（踩过）。垫高一层后告示牌正好在视线高度。
    """
    out = []
    top = y + 1 if pedestal else y          # 物品实际所在的层
    free = []
    for z in range(depth):
        for x in range(W):
            if (x, y, z) not in blocks and (x, top, z) not in blocks \
                    and (x, top + 1, z) not in blocks \
                    and (x, y - 1, z) in blocks:
                free.append((x, z))

    used = set()
    for p in props:
        if "at" in p:
            x, z = p["at"]
            if (x, z) not in free or (x, z) in used:
                raise ValueError("props 位置 (%d,%d) 不是空格" % (x, z))
        else:
            pick = [c for c in free if c not in used]
            if not pick:
                raise ValueError("地板放不下更多 props 了")
            x, z = pick[0]
        used.add((x, z))
        if pedestal:
            blocks[(x, y, z)] = "floor"

        if p["kind"] == "chest":
            blocks[(x, top, z)] = "chest"
            out.append((x, top - 64, z,
                        container_entity(x, top - 64, z, p.get("items", []),
                                         p.get("name", ""))))
        elif p["kind"] == "sign":
            blocks[(x, top, z)] = "sign"
            out.append((x, top - 64, z,
                        sign_entity(x, top - 64, z, p.get("front", []),
                                    p.get("back"))))
        else:
            raise ValueError("未知 props 类型：%s" % p["kind"])
    return out


# ---------------------------------------------------------------- LevelDB 日志
def log_records(pairs, block_size=32768):
    """LevelDB 日志；单条记录超过块容量时拆成 FIRST/MIDDLE/LAST 分片（关键）。"""
    out = bytearray()

    def emit(body):
        pos, first = 0, True
        while pos < len(body):
            avail = block_size - (len(out) % block_size)
            if avail < 7:
                out.extend(b"\x00" * avail)
                avail = block_size
            take = min(len(body) - pos, avail - 7)
            last = (pos + take) == len(body)
            typ = 1 if (first and last) else (2 if first else (4 if last else 3))
            chunk = body[pos:pos + take]
            out.extend(struct.pack("<IHB", _mask(crc32c(bytes([typ]) + chunk)), take, typ))
            out.extend(chunk)
            pos += take
            first = False

    for seq, key, val in pairs:
        body = (struct.pack("<QI", seq, 1) + bytes([1]) + _varint(len(key)) + key
                + _varint(len(val)) + val)
        emit(body)
    return bytes(out)


def manifest_bytes(last_seq=0):
    """两条 VersionEdit：第一条建库（log=0/next=1），第二条指向日志。"""
    def rec(fields):
        payload = bytearray()
        for tag, val in fields:
            if tag == 1:
                comp = b"leveldb.BytewiseComparator"
                payload += bytes([1]) + _varint(len(comp)) + comp
            else:
                payload += bytes([tag]) + _varint(val)
        return struct.pack("<IHB", _mask(crc32c(bytes([1]) + bytes(payload))),
                           len(payload), 1) + bytes(payload)

    return rec([(1, None), (2, 0), (3, 1), (4, 0)]) + rec([(2, 1), (3, 2), (4, last_seq)])


# ---------------------------------------------------------------- level.dat
def _parse_value(b, o, t):
    if t == TAG_BYTE: return struct.unpack("<b", b[o:o + 1])[0], o + 1
    if t == TAG_SHORT: return struct.unpack("<h", b[o:o + 2])[0], o + 2
    if t == TAG_INT: return struct.unpack("<i", b[o:o + 4])[0], o + 4
    if t == TAG_LONG: return struct.unpack("<q", b[o:o + 8])[0], o + 8
    if t == TAG_FLOAT: return struct.unpack("<f", b[o:o + 4])[0], o + 4
    if t == TAG_DOUBLE: return struct.unpack("<d", b[o:o + 8])[0], o + 8
    if t == TAG_BYTE_ARRAY:
        n = struct.unpack("<i", b[o:o + 4])[0]
        return list(b[o + 4:o + 4 + n]), o + 4 + n
    if t == TAG_STRING:
        n = struct.unpack("<H", b[o:o + 2])[0]
        return b[o + 2:o + 2 + n].decode("utf-8", "replace"), o + 2 + n
    if t == TAG_LIST:
        et = b[o]; n = struct.unpack("<i", b[o + 1:o + 5])[0]; o += 5
        arr = []
        for _ in range(n):
            v, o = _parse_value(b, o, et)
            arr.append(v)
        return (et, arr), o
    if t == TAG_COMPOUND:
        d = {}
        while True:
            tt = b[o]
            if tt == 0:
                return d, o + 1
            nl = struct.unpack("<H", b[o + 1:o + 3])[0]
            nm = b[o + 3:o + 3 + nl].decode("utf-8", "replace")
            o += 3 + nl
            v, o = _parse_value(b, o, tt)
            d[nm] = (tt, v)
    if t == TAG_INT_ARRAY:
        n = struct.unpack("<i", b[o:o + 4])[0]
        return list(struct.unpack("<" + "i" * n, b[o + 4:o + 4 + 4 * n])), o + 4 + 4 * n
    raise ValueError(f"tag {t}")


def load_level_dat(raw):
    """兼容「8 字节头 + 裸 NBT」（1.21+）与 gzip 两种格式，返回 root dict。"""
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
        off = 0
    else:
        off = 8
    root, _ = _parse_value(raw, off + 3, TAG_COMPOUND)
    return root


def build_level_dat(template_path, world_name, spawn, gametype=1):
    with zipfile.ZipFile(template_path) as z:
        raw = z.read("level.dat")
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
        ver, body = 10, raw
    else:
        ver, ln = struct.unpack("<II", raw[:8])
        body = raw[8:8 + ln]
    root, _ = _parse_value(body, 3, TAG_COMPOUND)

    root["LevelName"] = (TAG_STRING, world_name)
    root["SpawnX"] = (TAG_INT, spawn[0])
    root["SpawnY"] = (TAG_INT, spawn[1])
    root["SpawnZ"] = (TAG_INT, spawn[2])
    root["GameType"] = (TAG_INT, gametype)
    root["commandsEnabled"] = (TAG_BYTE, 1)
    root["cheatsEnabled"] = (TAG_BYTE, 1)
    root["FlatWorldLayers"] = (TAG_STRING, "")   # 与真实存档一致：地形全由 db 决定
    out = nbt_compound(root, named=False)
    return struct.pack("<II", ver, len(out)) + out


# ---------------------------------------------------------------- 二分法
def binsplit(objective, action, hi=20, lo=0, selector="@a"):
    """把计分项按 2 的幂次拆分执行（同帧版）。

    原理：任何整数都是 2 的幂次和（53 = 32+16+4+1）。从高位往低位试，
    够减就执行动作并扣掉，减完自然归零。hi 位覆盖到 2**hi。

    action 是模板串：{p} 换成 2**k 的数值，{k} 换成幂次。
      例：binsplit("score", "tp @s ~{p} ~ ~")          → 分数转坐标
          binsplit("exp",   "setblock ~ ~ ~{p} stone") → 分数转方块高度

    用法：放进【脉冲链】（按钮触发），不要放循环链。
    每个幂次 2 条，全无条件——前一条失败不影响后一条，这是级联下唯一安全的写法。
    20 位 = 40 个方块，覆盖 1048576，按一次跑一次，空闲 0 开销。
    """
    out = []
    for k in range(hi, lo - 1, -1):
        p = 1 << k
        pre = "execute as %s if score @s %s matches %d.." % (selector, objective, p)
        out.append(pre + " run " + action.format(p=p, k=k))
        out.append(pre + " run scoreboard players remove @s %s %d" % (objective, p))
    return out


def bits2blocks(objective, bits=6, on="minecraft:black_concrete",
                off="minecraft:white_concrete", origin=(0, 4, 0), tmp="_bit"):
    """把计分项的低 bits 位写成一行黑白方块（黑=1，白=0）。

    位序：第 k 位放在 x = origin.x + k（低位在左）。
    取位公式：bit_k = (score % 2**(k+1)) >= 2**k —— 必须先取模，
    直接写 matches 2**k.. 是错的（5 也满足 matches 4..）。

    返回的列表已含所需常量（虚拟玩家 "2"/"4"/"8"...），放进脉冲链即可。
    """
    ox, oy, oz = origin
    consts = []
    for k in range(bits):
        m = 1 << (k + 1)
        if m > 2:
            consts.append("scoreboard players set %d sys %d" % (m, m))
    out = consts
    for k in range(bits):
        p = 1 << k
        m = 1 << (k + 1)
        out += [
            "scoreboard players operation @a %s = @a %s" % (tmp, objective),
            "scoreboard players operation @a %s %%= %d sys" % (tmp, m),
            "execute as @a if score @s %s matches %d.. run "
            "setblock %d %d %d %s" % (tmp, p, ox + k, oy, oz, on),
            "execute as @a unless score @s %s matches %d.. run "
            "setblock %d %d %d %s" % (tmp, p, ox + k, oy, oz, off),
        ]
    return out


# ---------------------------------------------------------------- 命令体检
def _escape(cmd):
    """JSON 文本里必须写 \\n 两个字符；源码里若写成真换行会导致 titleraw 整条失效。"""
    return cmd.replace("\r", " ").replace("\n", "\\n")


def check_commands(cmds):
    """检查 tellraw / titleraw 的 JSON 是否合法，返回 [(命令片段, 错误)]。"""
    import json as _json
    bad = []
    for c in cmds:
        for kw in ("tellraw", "titleraw"):
            i = c.find(kw)
            if i < 0:
                continue
            j = c.find("{", i)
            if j < 0:
                continue
            try:
                _json.loads(c[j:])
            except Exception as e:
                bad.append((c[:70], str(e)))
            break
    return bad


# ---------------------------------------------------------------- 布局
# 补齐用的空命令：选择器永远匹配不到，每刻立即失败、无副作用。
# 业务块是无条件的，所以它失败不会连坐后面的块（这一点很关键）。
PAD = "execute if entity @e[tag=__pad_never__] run tag @e[tag=__pad_never__] add pad"


def serpentine(count, start_z, width=None):
    width = W if width is None else width
    path, x, z, step = [], 0, start_z, 1
    for _ in range(count):
        path.append((x, z))
        if len(path) == count:
            break
        nx = x + step
        if 0 <= nx < width:
            x = nx
        else:
            z += 1
            step *= -1
    return path


def _facing(a, b):
    if b[0] > a[0]: return "ch_E"
    if b[0] < a[0]: return "ch_W"
    if b[1] > a[1]: return "ch_S"
    return "ch_N"


def expand_segments(seg_list):
    """把 segments 展开成 [(cmd, cond)]。

    每段 = [无条件闸门] + [全条件正文]。闸门失败时正文级联跳过，
    直到下一个无条件块（即下一段的闸门）。这就是断链。
    """
    out = []
    for seg in seg_list:
        gate = seg.get("gate")
        if gate:
            out.append((gate, False))       # 闸门必须无条件，否则被上一段连坐
        out.extend((c, True) for c in seg["cmds"])
    return out


def _fd(dx, dz):
    """位移 → facing_direction（0下 1上 2北 3南 4西 5东）。"""
    if dx > 0:
        return 5
    if dx < 0:
        return 4
    if dz > 0:
        return 3
    return 2


def _fkey(dx, dz, cond=0):
    """位移 → 链块键名。cond=1 返回 conditional 变体（chc_*）。"""
    pre = "chc_" if cond else "ch_"
    if dx > 0:
        return pre + "E"
    if dx < 0:
        return pre + "W"
    if dz > 0:
        return pre + "S"
    return pre + "N"


def _norm_chains(system):
    """统一成 [{"kind","gate","brk","cmds","button"}]。

    兼容旧写法：init / tick（列表或 segments）/ panel / shop 自动转成多条链。
    segments 的每一段 → 一条 gated 链（不再用条件块）。
    """
    if "chains" in system:
        # ❗ 兜底：链缺 `id` 时自动补一个。
        #    否则 `chain_fds[ch["id"]]` 会 KeyError，而报错信息只有一行 'id'，
        #    很难定位到是哪条链 —— 这是「示例生成器跑不通」的常见原因。
        out = []
        for i, ch in enumerate(system["chains"]):
            if not ch.get("id"):
                ch = dict(ch)
                ch["id"] = "chain%d" % i
            out.append(ch)
        return out

    out = [{"kind": "impulse", "cmds": system["init"], "button": True}]
    tick = system["tick"]
    if isinstance(tick, dict):
        for seg in tick["segments"]:
            gate = seg["gate"]
            out.append({"kind": "gated", "gate": gate,
                        "brk": gate.replace("execute if ", "", 1),
                        "cmds": seg["cmds"]})
    else:
        out.append({"kind": "gated", "gate": "execute if entity @a",
                    "brk": "entity @a", "cmds": tick})

    # 面板与商店：每条命令自带选择器，全部无条件块
    for label, cmds in system.get("panel", []):
        out.append({"kind": "impulse", "cmds": cmds, "button": True})
    for label, cost, item, count in system.get("shop", []):
        out.append({"kind": "impulse", "button": True, "cmds": [
            f'execute as @p[scores={{money={cost}..}}] run scoreboard players remove @s money {cost}',
            f'give @p {item} {count}',
            f'execute as @p[scores={{money=..{cost - 1}}}] run tellraw @s '
            f'{{"rawtext":[{{"text":"§c金币不足，需要 {cost}"}}]}}',
        ]})
    return out


# ---------------------------------------------------------------- 方块自述（U27）
# 用户要求：**每个命令方块都注明自己在干什么**，方便后续维护。
#
# 为什么写在方块上而不是注释文件：
#   交付物只有 `.mcstructure`，说明必须**长在世界里**——打开世界就能看到，
#   不依赖任何外部文档。写进方块实体的 `CustomName`，`dump_cbworld.py` 会把它
#   读成 `cb.json` 的 `name` 字段，于是**世界内**和**JSON 里**两边都能查。
#
# 命名：`<链标签>#<链内序号> <作用>`，例：`开火#12 音效`
CHAIN_LABEL = {
    "init": "初始化", "clock": "主循环", "join": "入服", "state": "状态",
    "trigger": "扳机", "shot": "开火", "bullet": "弹道", "reload": "换弹",
    "dmg": "结算",
    "p_supply": "面板·补弹", "p_reset": "面板·清弹", "p_purge": "面板·卸载",
    "p_cut": "面板·断开", "p_join": "面板·接通", "p_diag": "面板·自检",
    "p_test": "面板·试射",
}

# 链头（第 0 格）不写「检测」——那一格代表**整条链在干什么**（U31）。
# 站在世界里看第一条方块的 CustomName，就知道这条链负责什么，不用一条条翻。
CHAIN_SUMMARY = {
    "init": "计分板 / 规则 / 常加载 / 锚点 / HUD 初始化",
    "clock": "计时 + 冷却 + 血量镜像 + 相机倒计时",
    "join": "新人 uid / 队伍 / 弹药 / 血量建档",
    "state": "副手壳→枪型+参数 → 溢出回灌 → 换弹 → HUD",
    "trigger": "抛竿即开火：自愈建档 → 空仓提示 → 置 tg_fire → 连发数",
    "shot": "出弹 → 打标 → 顶高 → 灌参数 → 散射 → 枪口 → 音效 → 后坐",
    "bullet": "碰撞穷举 → 三段肢体 → 同分 → 受击/碰墙特效 → 粒子（50 把枪共用）",
    "dmg": "二分法扣血：256/128/…/1 逐档 damage + 减分",
    "reload": "换弹音效 + 装填完成 HUD",
    "p_supply": "按一下补满备弹",
    "p_reset": "清空弹药 / 在飞弹丸 / 伤标 / 视角",
    "p_purge": "卸载：删计分项 + 常加载 + 锚点",
    "p_cut": "断开全部功能链（连接块朝后）",
    "p_join": "接通全部功能链（连接块朝前）",
    "p_diag": "自检：把关键计分项打到聊天栏",
    "p_test": "试射：绕过抛竿检测直接出一发",
}

# 作用判定：**顺序即优先级**，先命中先算。
# 断链三条必须排最前——它们的命令里没有别的关键词，但 `execute if entity`
# 这类包装词到处都是，不排前面会被误判成「检测」。
_TAG_RULES = (
    ('chain_command_block["facing_direction"=5]', "连接"),
    ('chain_command_block["facing_direction"=4]', "重置"),
    ("chain_command_block", "断链"),
    ("particle", "粒子"),
    ("playsound", "音效"),
    ("camerashake", "震屏"),
    ("camera", "相机"),
    ("titleraw", "HUD"),
    ("tellraw", "提示"),
    ("scoreboard objectives", "计分板"),
    ("scoreboard players operation", "计分运算"),
    ("scoreboard players random", "随机"),
    ("scoreboard players remove", "减分"),
    ("scoreboard players add", "加分"),
    ("scoreboard players set", "置分"),
    ("scoreboard players", "计分"),
    ("summon", "召唤"),
    ("kill", "清理"),
    ("damage", "伤害"),
    ("tickingarea", "常加载"),
    ("gamerule", "规则"),
    ("effect ", "效果"),
    ("tp ", "位移"),
    ("tag ", "打标"),
    ("setblock", "铺块"),
)


def _tag(cmd):
    """从命令正文猜一个 2-3 字的作用词（给维护者扫一眼用）。"""
    for pat, label in _TAG_RULES:
        if pat in cmd:
            return label
    return "业务"


def build_scene(system):
    """把 chains 排成蛇形链，返回 (blocks, entities, prop_ents)。

    末块一律朝上（ch_U / chc_U），指向空气，永不回指。

    **断链实现（2026-11 定稿，前后推翻过两次）**：

        [0]   循环闸门   无条件   execute if <条件>
        [1]   复位块     **有条件**   setblock ~1 ~ ~ chain_command_block["facing_direction"=<运行方向>]
        [2..] 业务       无条件   一条失败不影响后面

    为什么只有复位块带条件位：
      · 闸门失败 → 复位块被跳过 → 复位块"没执行" → 下一格根本不被触发
      · 业务块一条都不跑，与它们有没有条件位无关
      · 业务块保持无条件 → 不会因为前面一条 `damage` 没打中就整段瘫痪

    ❗ 两个反例（都被实测否掉过）：
      1. 复位块写成无条件 → 闸门失败也每刻复位一次，白跑一条 `setblock`
      2. 业务块全部 conditional_bit=1（gate_mode="cascade"）→ 业务块互相连坐
    """
    chains = _norm_chains(system)

    # 说明区（箱子 / 告示牌）占最前面 2 行，链整体往后挪
    props = system.get("props") or []
    reserve = 2 if props else 0

    # ---- 按楼层分组（U53）----
    # 50 条单枪链把深度顶到 150 行，一层摆不下也太长。拆成两层：
    # 第 0 层放主干 + 面板，第 1 层放 50 条单枪赋值链。
    levels = {}
    for ch in chains:
        levels.setdefault(ch.get("level", 0), []).append(ch)

    def _depth_of(sub, extra):
        rows = 0
        for ch in sub:
            n = len(ch["cmds"]) + (1 if ch["kind"] == "gated" else 0)
            if ch["kind"] == "gated" and ch.get("gate_mode", "reset") == "reset":
                n += 1
            rows += (n + W - 1) // W
        return rows + len(sub) + 4 + extra

    depth = max(_depth_of(sub, reserve if lv == 0 else 0)
                for lv, sub in levels.items())

    blocks, entities = {}, {}
    for lv in sorted(levels):
        make_floor(blocks, W, depth, 3 + lv * FLOOR_GAP, single=(lv > 0))

    # 链 ID → 该链的 path（坐标列表）。供 {T:链ID:索引} 占位符做跨链相对定位。
    chain_paths = {}
    # 链 ID → (朝前 fd, 朝后 fd)。{SET:链ID:arm|dis} 用它，避免写死 5 / 4
    # （蛇形换行处下一格在 +z，朝前是 3 不是 5）
    chain_fds = {}

    def add_chain(ch, start_z, y0):
        body = ch["cmds"]
        gated = ch["kind"] == "gated"
        # 自述用的链标签（三段式前两格由下面 put(..., tag=) 显式指定）
        label = ch.get("label") or CHAIN_LABEL.get(ch.get("id", ""), ch.get("id") or "链")
        # gate_mode：
        #   "reset"（默认）= 闸门无条件 → 复位块有条件 → 业务全部无条件（第 8 章定稿范式）
        #   "cascade"      = 闸门无条件 → 业务全部有条件（变体，业务块会连坐）
        #   "loop"         = 闸门无条件 → 业务全部无条件 → **不插复位块**
        #                    专供闸门恒真的链（`execute if entity @a`）。恒真闸门每刻
        #                    成功，复位块只是每刻白跑一条 setblock；断链对它也没意义，
        #                    直接让它循环（用户 U14）。
        mode = ch.get("gate_mode", "reset")
        use_reset = gated and mode == "reset"
        use_cascade = gated and mode == "cascade"

        # ---- 补齐行数：让链尾落在**朝东**的那一行 ----
        # 只有**老的四段式**（自断块在链尾，`{CUT}` 收尾）才需要这段：
        # 自断块写的是"朝后"，行向不同朝向就不同（蛇形第 1 行朝西 → 朝后是东=5），
        # 而用户 U3 要求字面写 `=4`，所以得把链尾顶到朝东的行上。
        #
        # **三段式（2026-11 新定稿）不需要**：重置块紧跟在连接块的第 3 格，
        # 前三格永远在第 0 行（朝东），"朝后"恒为西(4)，字面 `=4` 天然成立。
        three_part = bool(body) and body[0] == "{RESET}"
        if use_reset and not three_part:
            body = list(body)
            cut = body.pop() if body and body[-1] == "{CUT}" else None
            for _ in range(32):
                n = len(body) + 3          # 闸门 1 + 复位 1 + 自断 1
                p = serpentine(n, 0)
                dx = p[-1][0] - p[-2][0]
                dz = p[-1][1] - p[-2][1]
                if dx > 0 and dz == 0:     # 朝东进入链尾 → "朝后"恒等于朝西(4)
                    break
                body.append(PAD)
            if cut:
                body.append(cut)
            body = tuple(body)

        n = len(body) + (1 if gated else 0) + (1 if use_reset else 0)
        path = serpentine(n, start_z)
        if ch.get("id"):
            chain_paths[ch["id"]] = path

        def put(i, cmd, auto, cond=0, tag=None):
            x, z = path[i]
            # ---- 占位符解析（跨链引用一律走这里，禁写死绝对坐标）----
            #   {T:<链ID>:<k>}       → 该链第 k 格的**相对坐标** `~dx ~ ~dz`
            #   {CUT}                → 自断块：把自己摆成"朝后"（朝向上游）
            #   {SET:<链ID>:arm}     → `setblock <第1格相对坐标> chain_command_block["facing_direction"=<朝前>]`
            #   {SET:<链ID>:dis}     → 同上，但朝后（断开）
            #
            # ❗ 结构文件粘贴后世界坐标整体平移，写死 `setblock 2 -60 7 ...` 只在原地有效。
            # ❗ 朝向也不能写死 5：蛇形换行处下一格在 +z，得写 3。所以 arm/dis 由这里现算。
            if "{" in cmd:
                def _rel(tx, tz):
                    dx, dz = tx - x, tz - z
                    return "%s ~ %s" % ("~" if dx == 0 else "~%d" % dx,
                                        "~" if dz == 0 else "~%d" % dz)

                def _rel_at(m):
                    tp = chain_paths.get(m.group(1))
                    k = int(m.group(2))
                    if not tp or k >= len(tp):
                        return "~ ~ ~"
                    return _rel(*tp[k])

                def _set_at(m):
                    tp = chain_paths.get(m.group(1))
                    if not tp or len(tp) < 3:
                        return "setblock ~ ~ ~ chain_command_block"
                    fwd = chain_fds.get(m.group(1), (5, 4))
                    fd = fwd[0] if m.group(2) == "arm" else fwd[1]
                    return ('setblock %s chain_command_block["facing_direction"=%d]'
                            % (_rel(*tp[1]), fd))

                def _self_cut(_m):
                    # 朝后 = 进入方向的相反方向（不是固定的西，蛇形换行时会变）
                    px, pz = path[i - 1] if i else (x, z)
                    dx, dz = x - px, z - pz
                    fd = 5 if dx > 0 else 4 if dx < 0 else 3 if dz > 0 else 2
                    back = {5: 4, 4: 5, 3: 2, 2: 3}[fd]
                    return ('setblock ~ ~ ~ chain_command_block["facing_direction"=%d]'
                            % back)

                def _self_reset(_m):
                    # 三段式的"重置"块（[2]，紧跟连接块）。
                    # 用户 U3 要求字面写 `=4`：它永远在第 0 行，运行方向朝东，
                    # 所以"朝后"恒为西(4)。这里断言一次，几何不对就报错，
                    # 不许悄悄写成别的数字（那是"=4 又不见了"的根因）。
                    nx = path[i + 1] if i + 1 < len(path) else None
                    if nx:
                        dx, dz = nx[0] - x, nx[1] - z
                        fd = 5 if dx > 0 else 4 if dx < 0 else 3 if dz > 0 else 2
                        if {5: 4, 4: 5, 3: 2, 2: 3}[fd] != 4:
                            raise SystemExit(
                                "%s：重置块不在朝东的行上（第 %d 格），"
                                "字面 `=4` 会写错方向" % (ch.get("id"), i))
                    return 'setblock ~ ~ ~ chain_command_block["facing_direction"=4]'

                cmd = re.sub(r"\{T:([A-Za-z0-9_]+):(\d+)\}", _rel_at, cmd)
                cmd = re.sub(r"\{SET:([A-Za-z0-9_]+):(arm|dis)\}", _set_at, cmd)
                # ❗ 必须先判存在再调：`cmd.replace("{X}", f())` 会**无条件求值**
                #    f()，而 _self_reset 带几何断言 → 每条命令都在自己的下标上
                #    报一次错（踩过：join 链第 17 格莫名报"重置块不在朝东行上"）。
                if "{CUT}" in cmd:
                    cmd = cmd.replace("{CUT}", _self_cut(None))
                if "{RESET}" in cmd:
                    cmd = cmd.replace("{RESET}", _self_reset(None))
            if i == 0:
                key = "rep_E" if gated else (
                    "imp_E" if ch["kind"] == "impulse" else "rep_E")
            elif i + 1 < len(path):
                key = _fkey(path[i + 1][0] - x, path[i + 1][1] - z, cond)
            else:
                # 末块朝上：指向空气 = 天然终点，永不回指前一块（第 66.3 节）
                key = "chc_U" if cond else "ch_U"
            blocks[(x, y0, z)] = key
            # 自述：
            #   第 0 格（链头）= `<链标签> · <整条链的概括>`，一眼看出这条链干什么
            #   其余格        = `<链标签>#<序号> <作用>`，定位到具体一步
            # 链头自述：**优先用链自己带的 `summary`**，其次查硬编码表。
            # 硬编码表只覆盖通用 id（init/clock/…）；自定义系统（拔刀剑、演出）
            # 在生成器里写 `summary=` 就能覆盖，不用回来改这张表。
            summary = ch.get("summary") or CHAIN_SUMMARY.get(ch.get("id", ""))
            if i == 0 and summary:
                desc = "%s · %s" % (label, summary)
            else:
                desc = "%s#%02d %s" % (label, i, tag or _tag(cmd))
            entities[(x, y0, z)] = (_escape(cmd), auto, cond, desc)

        if gated:
            # 闸门：循环块，无条件。失败时它后面那条复位块会被跳过
            put(0, ch["gate"], 1, tag="检测")
            if use_reset:
                # 复位块：全链唯一的有条件块。按 path[1]→path[2] 的相对方向现算
                dx = path[2][0] - path[1][0]
                dz = path[2][1] - path[1][1]
                rel = ("~1 ~ ~" if dx > 0 else "~-1 ~ ~" if dx < 0 else
                       "~ ~ ~1" if dz > 0 else "~ ~ ~-1")
                fd = 5 if dx > 0 else 4 if dx < 0 else 3 if dz > 0 else 2
                chain_fds[ch["id"]] = (fd, {5: 4, 4: 5, 3: 2, 2: 3}[fd])
                put(1, ch.get("reset") or
                    'setblock %s chain_command_block["facing_direction"=%d]' % (rel, fd),
                    1, cond=1, tag="连接")
                # 业务：全部无条件 —— 一条失败不影响后面
                for i, cmd in enumerate(body):
                    put(2 + i, cmd, 1, tag="重置" if cmd in ("{RESET}", "{CUT}") else None)
            else:
                # 变体 loop：恒真闸门，不插复位块，业务全部无条件，链自己循环
                for i, cmd in enumerate(body):
                    put(1 + i, cmd, 1, cond=1 if use_cascade else 0)
        else:
            for i, cmd in enumerate(body):
                put(i, cmd, 0 if (i == 0 and ch["kind"] == "impulse") else 1)

        if ch.get("button", not gated):
            bx, bz = path[0]
            blocks[(bx, y0 + 1, bz)] = "btn"
            blocks[(bx, y0 - 1, bz)] = "floor_btn"
        return path[-1][1]

    for lv in sorted(levels):
        z = reserve if lv == 0 else 0
        y0 = 4 + lv * FLOOR_GAP
        for ch in levels[lv]:
            z = add_chain(ch, z, y0) + 1

    prop_ents = (place_props(blocks, depth, props,
                             pedestal=system.get("props_pedestal", False))
                 if props else [])
    return blocks, entities, prop_ents


# ---------------------------------------------------------------- 主流程
def build(template, out, name, spawn, gametype, system):
    blocks, entities, prop_ents = build_scene(system)

    chunks = {}
    # ❗ 方块按**子区块**分组：一个子区块 = 16 格高。
    #    二楼在 local y=18，属于子区块 -3（不是 -4），必须单独写一条记录，
    #    否则二楼那些方块在存档里根本不存在（校验会报"实体下面是 ?"）。
    for (x, y, z), key in blocks.items():
        ck = (x // 16, z // 16)
        chunks.setdefault(ck, {}).setdefault("blocks", {}) \
              .setdefault(y // 16, {})[(x % 16, y % 16, z % 16)] = key
    for (x, y, z), val in entities.items():
        chunks.setdefault((x // 16, z // 16), {}).setdefault("ents", {})[(x % 16, y, z % 16)] = val

    pairs, seq = [], 0
    for (cx, cz) in sorted(chunks):
        c = chunks[(cx, cz)]
        kb = struct.pack("<ii", cx, cz)
        for tag, val in ((b"\x2c", b"\x28"), (b"\x2b", b"\x00" * 632),
                         (b"\x36", struct.pack("<i", 2))):
            seq += 1
            pairs.append((seq, kb + tag, val))
        # 每个子区块一条 `\x2f` 记录（索引从 -4 往上）
        for sy, sub_blocks in sorted(c.get("blocks", {}).items()):
            sub = encode_subchunk(-4 + sy, sub_blocks)
            seq += 1
            pairs.append((seq, kb + b"\x2f" + struct.pack("<b", -4 + sy), sub))
        body = b"".join(cb_entity(cx * 16 + lx, ly - 64, cz * 16 + lz, cmd, auto, cond, name=desc)
                        for (lx, ly, lz), (cmd, auto, cond, desc)
                        in sorted(c.get("ents", {}).items()))
        # 说明区（箱子 / 告示牌）的方块实体，必须落在自己区块的记录里
        for (wx, wy, wz, nb) in prop_ents:
            if (wx // 16, wz // 16) == (cx, cz):
                body += nb
        if body:
            seq += 1
            pairs.append((seq, kb + b"\x31", body))

    all_cmds = [v[0] for v in entities.values()]
    bad = check_commands(all_cmds)
    if bad:
        print(f"[警告] {len(bad)} 条 tellraw/titleraw 的 JSON 不合法，游戏里会静默失败：")
        for frag, err in bad[:5]:
            print(f"    {frag} ... → {err}")

    level = build_level_dat(template, name, spawn, gametype)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("level.dat", level)
        zf.writestr("levelname.txt", name)
        zf.writestr("world_behavior_packs.json", "[]")
        zf.writestr("world_resource_packs.json", "[]")
        zf.writestr("db/CURRENT", "MANIFEST-000000\n")
        zf.writestr("db/LOCK", b"")
        zf.writestr("db/LOG", b"")
        zf.writestr("db/MANIFEST-000000", manifest_bytes(0))
        zf.writestr("db/000001.log", log_records(pairs))

    return {"chunks": len(chunks), "blocks": len(entities),
            "buttons": sum(1 for v in blocks.values() if v == "btn"),
            "props": len(prop_ents), "cmds": len(entities), "out": out}


# ---------------------------------------------------------------- 参考实现
def bar(obj, color, segments=20):
    """20 格条状图：第 i 格在分数 >= i 时上色。

    用字符串拼接而不是 % 格式化 —— % 会把 %%2 吃成 %2，条件拼接就失效了。
    """
    out = []
    for i in range(1, segments + 1):
        out.append('{"translate":"%%2","with":{"rawtext":['
                   '{"selector":"@s[scores={' + obj + '=' + str(i) + '..}]"},'
                   '{"text":"' + color + '"}]}},')
        out.append('{"text":"ࡇ"},')
    return "".join(out)


HUD = _escape('{"rawtext":['
       '{"text":"§8● §f"},{"selector":"@s"},'
       '{"text":" §8LV.§f"},{"score":{"objective":"level","name":"@s"}},'
       '{"text":"  §c"},{"score":{"objective":"hp","name":"@s"}},'
       '{"text":"§8/"},{"score":{"objective":"hp_max","name":"@s"}},'
       '{"translate":"%%2","with":{"rawtext":['
       '{"selector":"@s[scores={hp_hurta=1..,hp_hurt=..-1}]"},'
       '{"translate":"§c%%1","with":[{"score":{"objective":"hp_hurt","name":"@s"}}]}]}},'
       '{"text":"\n§8▏"},' + bar("hp_t", "§c") +
       '{"text":"\n§8LV.§f"},{"score":{"objective":"level","name":"@s"}},'
       '{"text":"  §b"},{"score":{"objective":"xp","name":"@s"}},'
       '{"text":"§8/"},{"score":{"objective":"xp_max","name":"@s"}},'
       '{"text":"\n§8▏"},' + bar("xp_t", "§b").rstrip(",") +
       ']}')

STATS = ('{"rawtext":['
         '{"text":"§8======= §6角色数据 §8=======\\n"},'
         '{"text":"§7等级 §f"},{"score":{"objective":"level","name":"@s"}},'
         '{"text":"   §c生命 §f"},{"score":{"objective":"hp","name":"@s"}},'
         '{"text":"§8/"},{"score":{"objective":"hp_max","name":"@s"}},'
         '{"text":"\\n§b经验 §f"},{"score":{"objective":"xp","name":"@s"}},'
         '{"text":"§8/"},{"score":{"objective":"xp_max","name":"@s"}},'
         '{"text":"\\n§6金币 §f"},{"score":{"objective":"money","name":"@s"}},'
         '{"text":"   §e在线 §f"},{"score":{"objective":"playtime","name":"@s"}},{"text":"秒"},'
         '{"text":"\\n§4攻击 §f"},{"score":{"objective":"attack","name":"@s"}},'
         '{"text":"   §d暴击 §f"},{"score":{"objective":"crit","name":"@s"}},{"text":"%%"},'
         '{"text":"   §5暴伤 §f"},{"score":{"objective":"attack_crit","name":"@s"}},'
         '{"text":"\\n§a击杀 §f"},{"score":{"objective":"killtotal","name":"@s"}},'
         '{"text":"\\n§8========================="}]}')


def demo_system():
    """一套完整的数据化系统：血量/经验/等级/属性/击杀奖励/商店/排行榜。

    约定：**不使用 tag**，所有布尔状态用计分板（建档 / 礼包），
    每刻 `add @a 建档 0` 保证"从未赋值"的玩家也能被 scores={建档=0} 匹配到。
    """
    return {
        "init": [
            # 数据项
            'scoreboard objectives add health health',
            'scoreboard objectives add hp dummy',
            'scoreboard objectives add hp_max dummy',
            'scoreboard objectives add hp_now dummy',
            'scoreboard objectives add hp_hurt dummy',
            'scoreboard objectives add hp_hurta dummy',
            'scoreboard objectives add hp_counta dummy',
            'scoreboard objectives add hp_t dummy',
            'scoreboard objectives add hp_ta dummy',
            'scoreboard objectives add xp dummy',
            'scoreboard objectives add xp_max dummy',
            'scoreboard objectives add xp_now dummy',
            'scoreboard objectives add xp_t dummy',
            'scoreboard objectives add xp_ta dummy',
            'scoreboard objectives add level dummy',
            'scoreboard objectives add level_old dummy',
            'scoreboard objectives add attack dummy',
            'scoreboard objectives add crit dummy',
            'scoreboard objectives add attack_crit dummy',
            'scoreboard objectives add award dummy',
            'scoreboard objectives add killcount dummy',
            'scoreboard objectives add killtotal totalKillCount',
            'scoreboard objectives add money dummy "金币"',
            'scoreboard objectives add playtime dummy "在线"',
            'scoreboard objectives add 建档 dummy',
            'scoreboard objectives add 礼包 dummy',
            'scoreboard objectives add sys dummy',
            # 常量（虚拟玩家）
            'scoreboard players set ten sys 10',
            'scoreboard players set hundred sys 100',
            'scoreboard players set five sys 5',
            'scoreboard players set twenty sys 20',
            'scoreboard players set two sys 2',
            # 世界与界面
            'gamerule commandblocksenabled true',
            # 聊天栏灰字屏蔽（gamerule 只管聊天栏，管不到方块控制台）
            'gamerule sendcommandfeedback false',
            'gamerule commandblockoutput false',
            'gamerule showdeathmessages false',
            'gamerule announceadvancements false',
            'gamerule showrecipemessages false',
            'gamerule showcoordinates false',
            'gamerule dodaylightcycle false',
            'gamerule doweathercycle false',
            'gamerule keepinventory true',
            'hud @a hide health',
            'hud @a hide hunger',
            'hud @a hide armor',
            'hud @a hide status_effects',
            'hud @a hide item_text',
            'effect @a saturation 1 255 true',
            'scoreboard objectives setdisplay sidebar level',
            'setworldspawn 8 -60 7',
            'tellraw @a {"rawtext":[{"text":"§a数据化系统已启动，HUD 将显示血条与经验条"}]}',
        ],
        "tick": {"segments": [
            # ---- 段 A：每刻必做（总闸门 = 有人在线；没人时整链只跑 2 条）----
            {"gate": 'execute if entity @a',
             "cmds": [
                 'scoreboard players add #tick sys 1',
                 # 布尔位兜底：保证未赋值玩家也能被 scores={x=0} 匹配
                 'scoreboard players add @a 建档 0',
                 'scoreboard players add @a 礼包 0',
                 # 血量：引擎 health(0..20) → hp(0..100)
                 'execute as @a run scoreboard players operation @s hp = @s health',
                 'execute as @a run scoreboard players operation @s hp *= five sys',
                 # 受伤差值（飘字用）：只有这一组真正需要每刻跑
                 'execute as @a unless score @s hp_counta = @s hp run scoreboard players operation @s hp_hurt = @s hp',
                 'execute as @a unless score @s hp_counta = @s hp run scoreboard players operation @s hp_hurt -= @s hp_counta',
                 'execute as @a unless score @s hp_counta = @s hp run scoreboard players set @s hp_hurta 20',
                 'execute as @a run scoreboard players operation @s hp_counta = @s hp',
                 'scoreboard players remove @a[scores={hp_hurta=1..}] hp_hurta 1',
             ]},
            # ---- 段 B：每秒（时钟闸门）。复位必须放段首 ----
            {"gate": 'execute if score #tick sys matches 20..',
             "cmds": [
                 'scoreboard players set #tick sys 0',
                 'scoreboard players add @a playtime 1',
                 # 血条动画（秒级足够，肉眼看不出差别）
                 'execute as @a run scoreboard players operation @s hp_now = @s hp',
                 'execute as @a run scoreboard players operation @s hp_now /= five sys',
                 'execute as @a if score @s hp_t < @s hp_now run scoreboard players add @s hp_t 1',
                 'execute as @a if score @s hp_t > @s hp_now run scoreboard players remove @s hp_t 1',
                 # 经验条
                 'scoreboard players operation @a xp_now = @a xp_max',
                 'scoreboard players operation @a xp_now /= twenty sys',
                 'scoreboard players operation @a xp_t = @a xp',
                 'scoreboard players operation @a xp_t /= @a xp_now',
                 'execute as @a run titleraw @s actionbar ' + HUD,
                 # 升级
                 'execute as @a if score @s xp >= @s xp_max run scoreboard players operation @s level_old = @s level',
                 'execute as @a if score @s xp >= @s xp_max run scoreboard players add @s level 1',
                 'execute as @a if score @s xp >= @s xp_max run scoreboard players operation @s xp -= @s xp_max',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s xp_max += hundred sys',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s attack = @s level',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s attack *= @s level',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s attack += ten sys',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s crit = @s level',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s crit %= hundred sys',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s attack_crit = @s level',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s attack_crit *= ten sys',
                 'execute as @a unless score @s level = @s level_old run titleraw @s actionbar {"rawtext":[{"text":"§e§lLEVEL UP §r§f"},{"score":{"objective":"level_old","name":"@s"}},{"text":" §8>§f> "},{"score":{"objective":"level","name":"@s"}}]}',
                 'execute as @a unless score @s level = @s level_old run playsound random.levelup @s',
                 'execute as @a unless score @s level = @s level_old run scoreboard players operation @s level_old = @s level',
                 # 击杀奖励
                 'execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s award = @s level',
                 'execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s award *= two sys',
                 'execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s award += ten sys',
                 'execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s xp += @s award',
                 'execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s money += @s award',
                 'execute as @a unless score @s killtotal = @s killcount run tellraw @s {"rawtext":[{"text":"§6击杀奖励 §e+"},{"score":{"objective":"award","name":"@s"}},{"text":" §6经验/金币"}]}',
                 'execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s killcount = @s killtotal',
                 # 建档（用 建档 分数，不用 tag）。level_old 必须跟着 level 一起置 1，
                 # 否则下一秒 `unless level = level_old` 成立，白送一次 LEVEL UP + xp_max+100
                 'execute as @a[scores={建档=0}] run scoreboard players set @s level 1',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s level_old 1',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s hp_max 100',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s hp 100',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s hp_t 20',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s xp 0',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s xp_max 100',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s money 100',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s playtime 0',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s killcount 0',
                 'execute as @a[scores={建档=0}] run tellraw @s {"rawtext":[{"text":"§7已建立角色档案：§e100 §7金币 / §bLV.1"}]}',
                 'execute as @a[scores={建档=0}] run scoreboard players set @s 建档 1',
             ]},
        ]},
        "panel": [
            ("我的数据", ['execute as @p run tellraw @s ' + STATS]),
            ("等级榜", ['scoreboard objectives setdisplay sidebar level']),
            ("金币榜", ['scoreboard objectives setdisplay sidebar money']),
            ("攻击榜", ['scoreboard objectives setdisplay sidebar attack']),
            ("新手礼包", [
                'execute as @p[scores={礼包=0}] run scoreboard players add @s money 50',
                'execute as @p[scores={礼包=0}] run tellraw @s {"rawtext":[{"text":"§d新手礼包 §e+50 §d金币"}]}',
                'execute as @p[scores={礼包=0}] run scoreboard players set @s 礼包 1',
            ]),
            ("重置数据", [
                'scoreboard players reset @p',
                'scoreboard players operation @p killcount = @p killtotal',
                'scoreboard players set @p 建档 0',
                'tellraw @p {"rawtext":[{"text":"§c数据已重置，将重新建档"}]}',
            ]),
        ],
        "shop": [
            ("苹果 ×5", 10, "apple", 5),
            ("钻石剑", 50, "diamond_sword", 1),
            ("金苹果 ×3", 30, "golden_apple", 3),
        ],
    }


def tick_stats(chains):
    """返回 (功能链总块数, 空闲每刻执行条数)。

    gated 链 = 1 个循环闸门 + 1 个有条件复位块 + 若干无条件业务。
    空闲开销 = **循环块个数**：闸门失败时复位块被跳过，下一格不被触发，
    业务一条都不跑，所以空闲每刻只跑闸门那一条命令。

    百条级系统的目标线是 ≤3 条。
    """
    total = idle = 0
    for ch in chains:
        n = len(ch["cmds"]) + (1 if ch["kind"] == "gated" else 0)
        if ch["kind"] == "gated" and ch.get("gate_mode", "reset") == "reset":
            n += 1
        total += n
        if ch["kind"] in ("gated", "repeat"):
            idle += 1
    return total, idle


def main():
    ap = argparse.ArgumentParser(description="生成内置命令方块的 .mcworld")
    ap.add_argument("--template", help="真实存档 .mcworld，用作 level.dat 模板")
    ap.add_argument("--name", default="指令世界", help="世界显示名")
    ap.add_argument("--spawn", nargs=3, type=int, default=[8, -60, 7], metavar=("X", "Y", "Z"))
    ap.add_argument("--gametype", default="creative",
                    choices=["survival", "creative", "adventure", "spectator"])
    ap.add_argument("--out")
    ap.add_argument("--snbt", help="只解析一段 SNBT 并打印 NBT 类型树（不生成世界）")
    args = ap.parse_args()

    if args.snbt:
        node = parse_snbt(args.snbt)
        print(dump_tag(node))
        return
    if not args.template or not args.out:
        ap.error("生成世界需要 --template 与 --out（或用 --snbt 只做解析）")

    gt = {"survival": 0, "creative": 1, "adventure": 2, "spectator": 3}[args.gametype]
    sysdef = demo_system()
    info = build(args.template, args.out, args.name, args.spawn, gt, sysdef)
    tot, res = tick_stats(_norm_chains(sysdef))
    print(f"[完成] {info['out']}")
    print(f"        区块 {info['chunks']} 个，命令方块 {info['blocks']} 个，按钮 {info['buttons']} 个")
    print(f"        共 {tot} 块，空闲每刻 {res} 条（{res / tot * 100:.1f}%），"
          f"空闲时只有这 {res} 条在跑")
    print("        下一步：python verify_mcworld.py <文件> 做回读校验")


if __name__ == "__main__":
    main()
