#!/usr/bin/env python3
"""Validate and render a Minecraft Bedrock Edition command-block chain spec.

Usage:
    python3 chain_lint.py spec.json
    python3 chain_lint.py spec.json --format json
    python3 chain_lint.py spec.json --write plan.md
    python3 chain_lint.py spec.json --strict

Exit codes:
    0  no errors (warnings allowed unless --strict)
    1  validation errors
    2  cannot load / usage error

The linter is intentionally conservative: it knows the common Bedrock/Java
differences and the NetEase 1.21.130 command boundary, but it cannot execute
Minecraft. Always test in-game.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

TYPES = ("impulse", "repeat", "chain")
CONDITIONS = ("unconditional", "conditional")
REDSTONE = ("always_active", "needs_redstone")
FACINGS = ("north", "south", "east", "west", "up", "down")

DIRS = {
    "north": (0, 0, -1),
    "south": (0, 0, 1),
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
    "up": (0, 1, 0),
    "down": (0, -1, 0),
}
OPPOSITE = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
    "up": "down",
    "down": "up",
}

ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
SPEC_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")

SUPPORTED_SELECTOR_ARGS = {
    "type", "family", "name", "tag", "scores",
    "x", "y", "z", "dx", "dy", "dz",
    "r", "rm", "rx", "rxm", "ry", "rym",
    "m", "l", "lm", "c",
    "hasitem", "haspermission", "has_property",
}

JAVA_SELECTOR_ARGS = {
    "distance": "use r/rm (Bedrock has no distance=)",
    "sort": "use c=1 (nearest) or c=-1 (furthest)",
    "limit": "use c=",
    "level": "use l=/lm= (l is max, lm is min)",
    "gamemode": "use m=",
    "x_rotation": "use rx=/rxm=",
    "y_rotation": "use ry=/rym=",
    "team": "Bedrock has no teams; use tag=",
    "nbt": "Bedrock has no NBT selectors; use tag=/scores=/hasitem=",
    "predicate": "Bedrock has no predicates",
    "advancements": "Bedrock has no advancements",
}

JAVA_ONLY_COMMANDS = {
    "data": "Bedrock has no /data; store state in scoreboard/tags",
    "item": "Bedrock uses /replaceitem",
    "attribute": "Bedrock has no /attribute; use effect or a behavior pack",
    "bossbar": "Bedrock has no /bossbar; use titleraw/actionbar or sidebar",
    "forceload": "Bedrock uses /tickingarea",
    "advancement": "Bedrock has no /advancement",
    "spectate": "Bedrock has no /spectate",
    "worldborder": "Bedrock has no /worldborder",
    "fillbiome": "Bedrock has no /fillbiome",
    "datapack": "Bedrock uses behavior packs",
    "placefeature": "Bedrock has no /placefeature",
    "return": "Bedrock functions have no return",
    "random": "Use scoreboard players random",
    "tick": "Bedrock uses tick.json / gamerule",
    "rotate": "Bedrock has no /rotate; use tp ... facing",
    "waypoint": "Bedrock has no /waypoint",
    "defaultgamemode": "Bedrock has no /defaultgamemode",
    "setidletimeout": "Bedrock has no /setidletimeout",
}

NETEASE_UNSUPPORTED = {
    "camera": "NetEase 1.21.130 does not list /camera; use camerashake + tp ... facing + title",
    "inputpermission": "NetEase 1.21.130 does not list /inputpermission; use tp/effect or a behavior pack",
    "dialogue": "NetEase 1.21.130 does not list /dialogue; use NPC components/ModSDK",
    "loot": "NetEase 1.21.130 does not list /loot; use give/replaceitem/clear",
    "place": "NetEase 1.21.130 does not list /place; use structure load",
    "recipe": "NetEase 1.21.130 does not list /recipe; use give or a behavior-pack recipe",
    "scriptevent": "NetEase 1.21.130 does not list /scriptevent; use ModSDK/behavior-pack events",
    "fog": "NetEase docs mark /fog as not implemented; use a resource pack or skip it",
}

EXECUTE_SUBCOMMANDS = {
    "align", "anchored", "as", "at", "facing", "in",
    "positioned", "rotated", "if", "unless", "run",
}

EXPENSIVE_RE = re.compile(
    r"^(fill|clone|structure|kill)\b|^execute\s+as\s+@a\b|^particle\b.*@a"
)


@dataclass
class Issue:
    severity: str  # error | warning | info
    code: str
    message: str
    block_id: str | None = None
    fix: str | None = None


@dataclass
class Block:
    id: str
    type: str
    command: str
    condition: str = "unconditional"
    redstone: str = "needs_redstone"
    delay: int = 0
    execute_first_tick: bool | None = None
    next: str | None = None
    pos: list[float] | None = None
    facing: str | None = None
    note: str | None = None
    index: int = 0


@dataclass
class Report:
    name: str
    description: str
    blocks: list[Block] = field(default_factory=list)
    setup: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    order: list[str] = field(default_factory=list)
    depth: dict[str, int] = field(default_factory=dict)
    heads: list[str] = field(default_factory=list)
    children: dict[str, list[str]] = field(default_factory=dict)
    parents: dict[str, list[str]] = field(default_factory=dict)
    cycle_nodes: list[str] = field(default_factory=list)
    unreachable: list[str] = field(default_factory=list)

    @property
    def errors(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def infos(self) -> int:
        return sum(1 for i in self.issues if i.severity == "info")

    def by_id(self, block_id: str) -> Block | None:
        return next((b for b in self.blocks if b.id == block_id), None)


class SpecError(Exception):
    pass


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def strip_slash(cmd: str) -> str:
    return cmd.strip()[1:].lstrip() if cmd.strip().startswith("/") else cmd.strip()


def split_top_level(value: str, sep: str = ",") -> list[str]:
    """Split on sep only at bracket/brace depth 0, respecting quotes."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False
    for ch in value:
        if quote is not None:
            buf.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts


def iter_selectors(cmd: str) -> Iterable[tuple[str, str | None]]:
    """Yield (variable, inner-args-or-None) for every target selector."""
    i = 0
    n = len(cmd)
    while i < n:
        if cmd[i] != "@":
            i += 1
            continue
        m = re.match(r"@([a-z]+)", cmd[i:])
        if not m:
            i += 1
            continue
        var = m.group(1)
        j = i + len(m.group(0))
        inner: str | None = None
        if j < n and cmd[j] == "[":
            depth = 0
            quote: str | None = None
            escaped = False
            k = j
            while k < n:
                ch = cmd[k]
                if quote is not None:
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote:
                        quote = None
                else:
                    if ch in "\"'":
                        quote = ch
                    elif ch == "[":
                        depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0:
                            break
                k += 1
            if k < n and depth == 0:
                inner = cmd[j + 1:k]
                i = k + 1
                yield var, inner
                continue
        yield var, None
        i = j


def strip_selectors(cmd: str) -> str:
    out: list[str] = []
    i = 0
    n = len(cmd)
    while i < n:
        if cmd[i] != "@":
            out.append(cmd[i])
            i += 1
            continue
        m = re.match(r"@([a-z]+)", cmd[i:])
        if not m:
            out.append(cmd[i])
            i += 1
            continue
        j = i + len(m.group(0))
        if j < n and cmd[j] == "[":
            depth = 0
            quote: str | None = None
            escaped = False
            k = j
            while k < n:
                ch = cmd[k]
                if quote is not None:
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote:
                        quote = None
                else:
                    if ch in "\"'":
                        quote = ch
                    elif ch == "[":
                        depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0:
                            break
                k += 1
            if k < n and depth == 0:
                out.append("@" + m.group(1))
                i = k + 1
                continue
        out.append("@" + m.group(1))
        i = j
    return "".join(out)


def first_word(cmd: str) -> str:
    m = re.match(r"^\s*([a-zA-Z][a-zA-Z0-9_-]*)", cmd)
    return m.group(1).lower() if m else ""


def is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def md_cell(text: str, limit: int = 100) -> str:
    text = text.replace("\n", " ").replace("|", "\\|")
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    if "`" in text:
        return text
    return f"`{text}`"


# ---------------------------------------------------------------------------
# Loading and structural validation
# ---------------------------------------------------------------------------

def load_spec(path: str) -> dict[str, Any]:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecError(f"cannot read {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SpecError("spec root must be a JSON object")
    return data


def add(report: Report, severity: str, code: str, message: str,
        block_id: str | None = None, fix: str | None = None) -> None:
    report.issues.append(Issue(severity, code, message, block_id, fix))


def parse_spec(data: dict[str, Any]) -> Report:
    report = Report(
        name=str(data.get("name", "unnamed")),
        description=str(data.get("description", "")),
    )

    if not SPEC_NAME_RE.match(report.name):
        add(report, "error", "SPEC_NAME",
            f"spec name {report.name!r} must be kebab/snake case (a-z, 0-9, _-)",
            fix="use e.g. arena-countdown")
    if not isinstance(data.get("description", ""), str):
        add(report, "error", "SPEC_DESC", "description must be a string")

    setup = data.get("setup", [])
    if isinstance(setup, list):
        report.setup = [strip_slash(str(c)) for c in setup]
    else:
        add(report, "error", "SPEC_SETUP", "setup must be an array of command strings")

    tests = data.get("tests", [])
    if isinstance(tests, list):
        report.tests = [str(t) for t in tests]
    else:
        add(report, "error", "SPEC_TESTS", "tests must be an array of strings")

    notes = data.get("notes", [])
    if isinstance(notes, list):
        report.notes = [str(n) for n in notes]
    else:
        add(report, "error", "SPEC_NOTES", "notes must be an array of strings")

    raw_blocks = data.get("blocks")
    if not isinstance(raw_blocks, list) or not raw_blocks:
        add(report, "error", "SPEC_BLOCKS", "blocks must be a non-empty array")
        return report

    seen: dict[str, int] = {}
    for idx, raw in enumerate(raw_blocks):
        if not isinstance(raw, dict):
            add(report, "error", "BLOCK_OBJECT", f"blocks[{idx}] must be an object")
            continue
        bid = raw.get("id")
        if not isinstance(bid, str) or not ID_RE.match(bid):
            add(report, "error", "BLOCK_ID",
                f"blocks[{idx}] id must be a-z/0-9/_/- and <=32 chars",
                block_id=str(bid) if isinstance(bid, str) else None)
            continue
        if bid in seen:
            add(report, "error", "BLOCK_DUP_ID",
                f"duplicate block id {bid!r} (also blocks[{seen[bid]}])", block_id=bid)
            continue
        seen[bid] = idx

        btype = raw.get("type")
        if btype not in TYPES:
            add(report, "error", "BLOCK_TYPE",
                f"type must be one of {', '.join(TYPES)}", block_id=bid)
            continue

        command = raw.get("command")
        if not isinstance(command, str) or not command.strip():
            add(report, "error", "BLOCK_COMMAND", "command must be a non-empty string", block_id=bid)
            continue
        command = strip_slash(command)

        condition = raw.get("condition", "unconditional")
        if condition not in CONDITIONS:
            add(report, "error", "BLOCK_CONDITION",
                f"condition must be one of {', '.join(CONDITIONS)}", block_id=bid)
            condition = "unconditional"

        redstone = raw.get("redstone")
        if redstone is None:
            redstone = "always_active" if btype == "chain" else "needs_redstone"
        if redstone not in REDSTONE:
            add(report, "error", "BLOCK_REDSTONE",
                f"redstone must be one of {', '.join(REDSTONE)}", block_id=bid)
            redstone = "always_active" if btype == "chain" else "needs_redstone"

        delay = raw.get("delay", 0)
        if not is_int(delay) or delay < 0 or delay > 65535:
            add(report, "error", "BLOCK_DELAY",
                "delay must be an integer in 0..65535", block_id=bid)
            delay = 0

        eft = raw.get("execute_first_tick")
        if eft is not None and not isinstance(eft, bool):
            add(report, "error", "BLOCK_EFT", "execute_first_tick must be true/false", block_id=bid)
            eft = None

        nxt = raw.get("next")
        if nxt is not None and not isinstance(nxt, str):
            add(report, "error", "BLOCK_NEXT", "next must be a block id or null", block_id=bid)
            nxt = None

        pos = raw.get("pos")
        if pos is not None:
            if (not isinstance(pos, list) or len(pos) != 3
                    or not all(is_number(v) for v in pos)):
                add(report, "error", "BLOCK_POS", "pos must be [x, y, z] numbers", block_id=bid)
                pos = None
            else:
                pos = [float(v) for v in pos]

        facing = raw.get("facing")
        if facing is not None and facing not in FACINGS:
            add(report, "error", "BLOCK_FACING",
                f"facing must be one of {', '.join(FACINGS)}", block_id=bid)
            facing = None

        note = raw.get("note")
        if note is not None and not isinstance(note, str):
            add(report, "error", "BLOCK_NOTE", "note must be a string", block_id=bid)
            note = None

        report.blocks.append(Block(
            id=bid, type=btype, command=command, condition=condition,
            redstone=redstone, delay=delay, execute_first_tick=eft,
            next=nxt, pos=pos, facing=facing, note=note, index=idx,
        ))

    return report


# ---------------------------------------------------------------------------
# Graph and semantics
# ---------------------------------------------------------------------------

def build_graph(report: Report) -> None:
    ids = {b.id for b in report.blocks}
    children: dict[str, list[str]] = {b.id: [] for b in report.blocks}
    parents: dict[str, list[str]] = {b.id: [] for b in report.blocks}

    for b in report.blocks:
        if b.next is None:
            continue
        if b.next == b.id:
            add(report, "error", "SELF_LOOP", "block points to itself", block_id=b.id)
            continue
        if b.next not in ids:
            add(report, "error", "NEXT_MISSING",
                f"next={b.next!r} does not exist", block_id=b.id,
                fix="add that block or set next to null")
            continue
        children[b.id].append(b.next)
        parents[b.next].append(b.id)

    report.children = children
    report.parents = parents
    report.heads = [b.id for b in report.blocks if not parents[b.id]]

    for b in report.blocks:
        if b.type == "chain" and not parents[b.id]:
            add(report, "error", "CHAIN_HEAD",
                "chain block has no upstream block and can never be triggered",
                block_id=b.id,
                fix="put a repeat/impulse block behind it, or change the type")
        if b.condition == "conditional" and not parents[b.id]:
            add(report, "warning", "COND_HEAD",
                "conditional block has no upstream block; its condition has nothing to check",
                block_id=b.id,
                fix="make it unconditional or add an upstream block")
        if len(parents[b.id]) > 1:
            add(report, "warning", "MULTI_PARENT",
                f"block has {len(parents[b.id])} upstream blocks; only the block directly behind it "
                "controls the conditional check",
                block_id=b.id,
                fix="split into separate chains or keep one upstream")

    if not report.heads and report.blocks:
        add(report, "error", "NO_HEAD",
            "no head block (every block has an upstream); the chain is a closed loop")

    # Reachability from heads.
    reachable: set[str] = set()
    queue = list(report.heads)
    while queue:
        cur = queue.pop(0)
        if cur in reachable:
            continue
        reachable.add(cur)
        queue.extend(children[cur])
    report.unreachable = [b.id for b in report.blocks if b.id not in reachable]

    # Cycle detection (Kahn) over all blocks.
    indeg = {b.id: len(parents[b.id]) for b in report.blocks}
    q = [bid for bid, deg in indeg.items() if deg == 0]
    removed: list[str] = []
    while q:
        cur = q.pop(0)
        removed.append(cur)
        for nxt in children[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    report.cycle_nodes = [b.id for b in report.blocks if b.id not in removed]
    if report.cycle_nodes:
        add(report, "warning", "CYCLE",
            f"cycle detected ({', '.join(report.cycle_nodes)}); "
            "a chain loop executes at most once per tick",
            fix="use a repeat block for continuous looping")
    for bid in report.unreachable:
        if bid not in report.cycle_nodes:
            add(report, "error", "UNREACHABLE",
                "block is not reachable from any head", block_id=bid,
                fix="connect it to a head or remove it")

    # Depth-first order per head: keeps each chain together in the build sheet.
    order: list[str] = []
    depth: dict[str, int] = {}

    def visit(bid: str, d: int) -> None:
        if bid in depth:
            depth[bid] = max(depth[bid], d)
            return
        depth[bid] = d
        order.append(bid)
        for nxt in children[bid]:
            visit(nxt, d + 1)

    for head in report.heads:
        visit(head, 0)
    for b in report.blocks:
        if b.id not in depth:
            depth[b.id] = 0
            order.append(b.id)
    report.order = order
    report.depth = depth


def check_command(report: Report, cmd: str, block_id: str | None) -> None:
    """Bedrock-vs-Java checks for one command."""
    word = first_word(cmd)
    if word in JAVA_ONLY_COMMANDS:
        add(report, "error", "JAVA_CMD",
            f"/{word} is not available in Bedrock: {JAVA_ONLY_COMMANDS[word]}",
            block_id=block_id)
    if word in NETEASE_UNSUPPORTED:
        add(report, "error", "NETEASE_UNSUPPORTED",
            f"/{word} is not available/verified on NetEase 1.21.130: {NETEASE_UNSUPPORTED[word]}",
            block_id=block_id)

    # execute internals
    if word == "execute":
        if re.search(r"\b(store|detect|runasync)\b", cmd):
            add(report, "error", "JAVA_EXECUTE",
                "Bedrock execute has no store/detect/runasync",
                block_id=block_id,
                fix="use execute if block / count via scoreboard")
        if re.search(r"\b(if|unless)\s+(data|items|predicate|biome|dimension|loaded)\b", cmd):
            add(report, "error", "JAVA_CONDITION",
                "Bedrock execute conditions are block/blocks/entity/score only",
                block_id=block_id)
        m = re.match(r"^execute\s+(\S+)\s+(\S+)", cmd)
        if m:
            first, second = m.group(1), m.group(2)
            looks_like_target = first.startswith("@") or re.match(r"^[A-Za-z0-9_]{2,16}$", first)
            looks_like_pos = bool(re.match(r"^([~^]|-?\d)", second))
            if first not in EXECUTE_SUBCOMMANDS and looks_like_target and looks_like_pos:
                add(report, "error", "LEGACY_EXECUTE",
                    "old execute syntax was removed in 1.19.50",
                    block_id=block_id,
                    fix="use execute as <target> at <target> run ...")

    # Java NBT / item components / block states
    if re.search(r"\bnbt\s*=", cmd):
        add(report, "error", "JAVA_NBT",
            "Bedrock selectors have no nbt= argument", block_id=block_id,
            fix="use tag=, scores= or hasitem=")
    if re.match(r"^summon\b", cmd) and "{" in cmd:
        add(report, "error", "JAVA_SUMMON_NBT",
            "Bedrock summon does not accept NBT", block_id=block_id,
            fix="summon, then use commands/tags to customize")

    # Block states: only check block-placing commands, with selectors removed.
    if re.match(r"^(setblock|fill|clone|testforblock)\b", cmd) or re.search(r"\bif\s+block\b", cmd):
        stripped = strip_selectors(cmd)
        if re.search(r"\[(?!\s*\")[A-Za-z_][A-Za-z0-9_]*\s*=", stripped):
            add(report, "error", "JAVA_BLOCKSTATE",
                "Java-style block state (e.g. [facing=east])",
                block_id=block_id,
                fix='use Bedrock form: ["minecraft:cardinal_direction"="east"]')

    if word == "give":
        stripped = strip_selectors(cmd)
        if re.search(r"\[[A-Za-z_]+\s*=", stripped):
            add(report, "error", "JAVA_GIVE_COMPONENT",
                "Java item component syntax in give", block_id=block_id,
                fix="use give + enchant, or the Bedrock components JSON")

    # scoreboard
    m = re.match(r"^scoreboard\s+objectives\s+add\s+(\S+)\s+(\S+)", cmd)
    if m:
        criterion = m.group(2).strip('"')
        if criterion.lower() != "dummy":
            add(report, "error", "SB_CRITERION",
                f"Bedrock only supports the dummy criterion (got {criterion!r})",
                block_id=block_id,
                fix="use dummy and update the score with commands")
    if re.match(r"^scoreboard\s+objectives\s+modify\b", cmd):
        add(report, "error", "SB_MODIFY",
            "Bedrock has no scoreboard objectives modify", block_id=block_id,
            fix="set the display name when creating the objective")
    if re.match(r"^scoreboard\s+players\s+(get|enable|display)\b", cmd):
        add(report, "error", "SB_PLAYERS",
            "Bedrock has no scoreboard players get/enable/display",
            block_id=block_id,
            fix="use test or execute if score")

    # text
    if re.match(r"^title\s+\S+\s+(title|subtitle|actionbar)\s+\{", cmd):
        add(report, "error", "TITLE_JSON",
            "Bedrock /title takes plain text with § codes, not JSON",
            block_id=block_id,
            fix="use titleraw for JSON, or title @a title §6Text")
    if re.match(r"^tellraw\s+\S+\s+\{", cmd) and '"rawtext"' not in cmd:
        add(report, "warning", "TELLRAW_ROOT",
            "Bedrock tellraw expects a rawtext root", block_id=block_id,
            fix='use {"rawtext":[{"text":"..."}]}')

    # effect namespace
    if re.match(r"^effect\s+\S+\s+minecraft:", cmd):
        add(report, "warning", "EFFECT_NS",
            "Bedrock effect names do not use the minecraft: namespace",
            block_id=block_id,
            fix="drop the minecraft: prefix")

    # particle arity: Bedrock = effect + optional x y z
    if word == "particle":
        parts = cmd.split()
        if len(parts) > 5:
            add(report, "error", "PARTICLE_ARGS",
                "Bedrock particle takes only <effect> [x y z]",
                block_id=block_id,
                fix="remove delta/speed/count; emit multiple commands")

    # selectors
    for var, inner in iter_selectors(cmd):
        if inner is None:
            if var == "e":
                add(report, "info", "BROAD_SELECTOR",
                    "@e without filters selects every loaded entity",
                    block_id=block_id, fix="add type=/family=/tag=/c=")
            continue
        args = {}
        for arg in split_top_level(inner):
            arg = arg.strip()
            if not arg:
                continue
            if "=" not in arg:
                add(report, "error", "SELECTOR_ARG",
                    f"selector argument {arg!r} has no '='", block_id=block_id)
                continue
            key, value = arg.split("=", 1)
            key = key.strip()
            value = value.strip()
            args[key] = value
            if key in JAVA_SELECTOR_ARGS:
                add(report, "error", "JAVA_SELECTOR",
                    f"selector argument {key}= is not Bedrock: {JAVA_SELECTOR_ARGS[key]}",
                    block_id=block_id)
            elif key not in SUPPORTED_SELECTOR_ARGS:
                add(report, "warning", "UNKNOWN_SELECTOR",
                    f"unrecognized Bedrock selector argument {key}=",
                    block_id=block_id)
            if key == "hasitem":
                if re.search(r"\bcount\s*=", value):
                    add(report, "error", "HASITEM_COUNT",
                        "Bedrock hasitem uses quantity=, not count=",
                        block_id=block_id, fix="replace count= with quantity=")
                if "item=" not in value and "[" not in value:
                    add(report, "error", "HASITEM_ITEM",
                        "hasitem needs an item= field", block_id=block_id)
            if key in ("r", "rm", "rx", "rxm", "ry", "rym") and not re.search(r"\d", value):
                add(report, "warning", "SELECTOR_NUM",
                    f"{key}= should be numeric", block_id=block_id)
        if var == "e" and not any(k in args for k in ("type", "family", "tag", "c", "name", "scores")):
            add(report, "info", "BROAD_SELECTOR",
                "@e is not narrowed by type/family/tag/c/name/scores",
                block_id=block_id, fix="add one of those filters")

    # resource limits / best practices
    if len(cmd) > 1000:
        add(report, "info", "LONG_COMMAND",
            f"command is {len(cmd)} chars; consider splitting it",
            block_id=block_id)
    if len(cmd) > 32500:
        add(report, "error", "COMMAND_TOO_LONG",
            "command exceeds the 32,500 character command-block limit",
            block_id=block_id)


def check_semantics(report: Report) -> None:
    by_id = {b.id: b for b in report.blocks}
    for b in report.blocks:
        if b.execute_first_tick is not None and b.type != "repeat":
            add(report, "warning", "EFT_NON_REPEAT",
                "execute_first_tick only applies to repeat blocks", block_id=b.id)
        if b.type == "repeat" and b.condition == "conditional":
            add(report, "info", "REPEAT_COND",
                "conditional repeat checks the block behind it every cycle",
                block_id=b.id)
        if b.type == "repeat" and b.redstone == "needs_redstone" and b.delay == 0:
            add(report, "info", "REDSTONE_10HZ",
                "redstone-activated repeat is sampled on even ticks (~10 Hz), not 20 Hz",
                block_id=b.id,
                fix="use Always Active for 20 Hz")
        if b.type == "chain" and b.redstone == "needs_redstone":
            add(report, "warning", "CHAIN_POWER",
                "this chain block also needs redstone power in addition to being triggered",
                block_id=b.id,
                fix="set it to Always Active unless you really want redstone gating")
        if b.type == "chain" and b.condition == "conditional" and b.delay > 0:
            add(report, "warning", "DELAYED_COND",
                "with a tick delay, the trigger continues even if the condition fails; "
                "the condition only decides whether this block runs",
                block_id=b.id)
        if b.delay > 20:
            add(report, "info", "LONG_DELAY",
                f"delay {b.delay} ticks (~{b.delay / 20:.1f}s); "
                "a scoreboard timer is easier to pause/reset",
                block_id=b.id)
        if b.type == "repeat" and b.redstone == "always_active" and b.delay == 0:
            if EXPENSIVE_RE.search(b.command):
                add(report, "warning", "EXPENSIVE_TICK",
                    "expensive command runs 20x/second on this repeat block",
                    block_id=b.id,
                    fix="gate it with execute if, slow the clock, or move it to a chain")
        if b.next and b.next in by_id and b.next == b.id:
            add(report, "error", "SELF_LOOP", "block points to itself", block_id=b.id)

    # chain depth
    if report.order:
        max_depth = max(report.depth.values()) if report.depth else 0
        if max_depth > 50:
            add(report, "warning", "LONG_CHAIN",
                f"chain depth is {max_depth}; consider splitting into stages")
    if len(report.blocks) > 200:
        add(report, "info", "MANY_BLOCKS",
            f"{len(report.blocks)} blocks; split into functions or multiple chains")

    # positions
    pos_blocks = [b for b in report.blocks if b.pos is not None]
    seen_pos: dict[tuple[float, float, float], str] = {}
    for b in pos_blocks:
        key = tuple(round(v, 4) for v in b.pos)  # type: ignore[arg-type]
        if key in seen_pos:
            add(report, "error", "POS_DUP",
                f"same position as {seen_pos[key]!r}", block_id=b.id)
        else:
            seen_pos[key] = b.id
    for b in report.blocks:
        if b.pos is None and b.facing is not None:
            add(report, "info", "FACING_NO_POS",
                "facing is set but pos is missing; adjacency not checked", block_id=b.id)
        if b.pos is not None and b.facing is None and b.next:
            add(report, "info", "FACING_MISSING",
                "pos is set but facing is missing; inferred from next block if possible",
                block_id=b.id)

    for b in report.blocks:
        if not b.next:
            continue
        nxt = by_id.get(b.next)
        if nxt is None or b.pos is None or nxt.pos is None:
            continue
        delta = tuple(round(nxt.pos[i] - b.pos[i]) for i in range(3))
        direction = next((name for name, vec in DIRS.items() if vec == delta), None)
        if direction is None:
            add(report, "warning", "NOT_ADJACENT",
                f"{b.id} -> {b.next} is not a 1-block step ({delta}); "
                "a chain block only fires when directly in front",
                block_id=b.id)
            continue
        if b.facing is not None and b.facing != direction:
            add(report, "error", "FACING_MISMATCH",
                f"facing={b.facing} but next block {b.next} is {direction}",
                block_id=b.id,
                fix=f"set facing to {direction} or move the next block")
        if nxt.condition == "conditional" and nxt.facing is not None:
            # In a straight line the conditional block must face the same way as
            # its upstream, so that the upstream sits directly behind it.
            if nxt.facing != direction:
                add(report, "error", "COND_BEHIND",
                    f"{nxt.id} is conditional but its upstream {b.id} is not behind it "
                    f"(it faces {nxt.facing}, upstream is {direction})",
                    block_id=nxt.id,
                    fix="put the condition block in a straight line or use execute if")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_markdown(report: Report, max_cmd: int = 200) -> str:
    lines: list[str] = []
    lines.append(f"# Build Plan: {report.name}")
    lines.append("")
    if report.description:
        lines.append(report.description)
        lines.append("")

    counts = {t: sum(1 for b in report.blocks if b.type == t) for t in TYPES}
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Blocks: **{len(report.blocks)}** "
                 f"(repeat {counts['repeat']}, impulse {counts['impulse']}, chain {counts['chain']})")
    lines.append(f"- Heads: {len(report.heads)}"
                 + (f" — {', '.join(f'`{h}`' for h in report.heads)}" if report.heads else ""))
    lines.append(f"- Max chain depth: {max(report.depth.values()) if report.depth else 0}")
    lines.append(f"- Result: **{report.errors} error(s), {report.warnings} warning(s)**, "
                 f"{report.infos} info")
    lines.append("")

    issues = [i for i in report.issues if i.severity != "info"]
    if issues:
        lines.append("## Issues")
        lines.append("")
        for sev, title in (("error", "Errors"), ("warning", "Warnings")):
            group = [i for i in report.issues if i.severity == sev]
            if not group:
                continue
            lines.append(f"### {title}")
            lines.append("")
            for i in group:
                loc = f" `{i.block_id}`" if i.block_id else ""
                lines.append(f"- **{i.code}**{loc}: {i.message}")
                if i.fix:
                    lines.append(f"  - fix: {i.fix}")
            lines.append("")

    infos = [i for i in report.issues if i.severity == "info"]
    if infos:
        lines.append("### Notes")
        lines.append("")
        for i in infos:
            loc = f" `{i.block_id}`" if i.block_id else ""
            lines.append(f"- {i.code}{loc}: {i.message}" + (f" — {i.fix}" if i.fix else ""))
        lines.append("")

    lines.append("## Chain map")
    lines.append("")
    by_id = {b.id: b for b in report.blocks}
    printed: set[str] = set()

    def label(b: Block) -> str:
        cond = "cond" if b.condition == "conditional" else "uncond"
        red = "always" if b.redstone == "always_active" else "redstone"
        return (f"`{b.id}` ({b.type}/{cond}/{red}/d{b.delay})")

    def walk(bid: str, prefix: str, path: set[str]) -> None:
        b = by_id.get(bid)
        if b is None:
            return
        printed.add(bid)
        connector = "└─ " if prefix else ""
        lines.append(f"{prefix}{connector}{label(b)}")
        if bid in path:
            lines.append(f"{prefix}    ↺ cycle (stops after one pass per tick)")
            return
        if not b.next:
            return
        walk(b.next, prefix + "    ", path | {bid})

    for h in report.heads:
        if h in printed:
            continue
        walk(h, "", set())
        printed.add(h)
        lines.append("")
    for b in report.blocks:
        if b.id not in printed:
            lines.append(f"- (detached) {label(b)}")
            printed.add(b.id)
    lines.append("")

    lines.append("## Build sheet")
    lines.append("")
    lines.append("| # | id | type | condition | redstone | delay | next | command |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for idx, bid in enumerate(report.order, 1):
        b = by_id.get(bid)
        if b is None:
            continue
        lines.append(
            "| {n} | `{id}` | {t} | {c} | {r} | {d} | {nx} | {cmd} |".format(
                n=idx, id=b.id, t=b.type,
                c="conditional" if b.condition == "conditional" else "unconditional",
                r="always_active" if b.redstone == "always_active" else "needs_redstone",
                d=b.delay,
                nx=f"`{b.next}`" if b.next else "—",
                cmd=md_cell(b.command, max_cmd),
            )
        )
    lines.append("")

    if any(b.pos for b in report.blocks):
        lines.append("## Layout")
        lines.append("")
        lines.append("| id | pos | facing |")
        lines.append("|---|---|---|")
        for b in report.blocks:
            if b.pos:
                lines.append(f"| `{b.id}` | {b.pos[0]:g} {b.pos[1]:g} {b.pos[2]:g} | "
                             f"{b.facing or '—'} |")
        lines.append("")

    if report.setup:
        lines.append("## Setup")
        lines.append("")
        lines.append("Run once before building:")
        lines.append("")
        lines.append("```mcfunction")
        lines.extend(report.setup)
        lines.append("```")
        lines.append("")

    if report.tests:
        lines.append("## Tests")
        lines.append("")
        for t in report.tests:
            lines.append(f"- [ ] {t}")
        lines.append("")

    if report.notes:
        lines.append("## Design notes")
        lines.append("")
        for n in report.notes:
            lines.append(f"- {n}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Generated by `scripts/chain_lint.py`. "
                 "Static checks only — verify in-game before shipping.")
    lines.append("")
    return "\n".join(lines)


def render_json(report: Report) -> str:
    payload = {
        "name": report.name,
        "description": report.description,
        "ok": report.errors == 0,
        "errors": report.errors,
        "warnings": report.warnings,
        "infos": report.infos,
        "heads": report.heads,
        "order": report.order,
        "depth": report.depth,
        "blocks": [
            {
                "id": b.id, "type": b.type, "condition": b.condition,
                "redstone": b.redstone, "delay": b.delay,
                "execute_first_tick": b.execute_first_tick,
                "next": b.next, "pos": b.pos, "facing": b.facing,
                "command": b.command,
            }
            for b in report.blocks
        ],
        "issues": [
            {
                "severity": i.severity, "code": i.code, "block": i.block_id,
                "message": i.message, "fix": i.fix,
            }
            for i in report.issues
        ],
        "setup": report.setup,
        "tests": report.tests,
        "notes": report.notes,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyze(data: dict[str, Any]) -> Report:
    report = parse_spec(data)
    # Setup commands share the command checks.
    for i, cmd in enumerate(report.setup):
        check_command(report, cmd, f"setup[{i}]")
    for b in report.blocks:
        check_command(report, b.command, b.id)
    build_graph(report)
    check_semantics(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Bedrock command-block chain spec and render a build plan.")
    parser.add_argument("spec", help="path to spec JSON")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--write", metavar="PATH", help="also write the output to PATH")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failure")
    parser.add_argument("--max-command-display", type=int, default=200,
                        help="truncate commands in the markdown table (default 200)")
    args = parser.parse_args(argv)

    try:
        data = load_spec(args.spec)
    except SpecError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = analyze(data)
    out = render_json(report) if args.format == "json" else render_markdown(
        report, max(20, args.max_command_display))
    print(out)
    if args.write:
        try:
            Path(args.write).write_text(out + ("\n" if not out.endswith("\n") else ""),
                                        encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot write {args.write}: {exc}", file=sys.stderr)
            return 2
    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
