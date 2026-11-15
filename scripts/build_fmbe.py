#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FMBE 指令展示 —— spec 生成 / 世界打包。

FMBE（Fox MBE）= 用狐狸当载体、playanimation 注入 Molang 变量，
纯指令渲染任意方块展示体。本结构把「渲染链 + 三组展示 + 开关面板」做成可粘贴的机器。

用法：
    python build_fmbe.py --dump-spec out/spec.json
    python build_fmbe.py --spec out/spec.json --template t.mcworld --out out/_build.mcworld
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 依赖同目录的 build_cbworld.py —— 用相对路径，项目级 / 用户级都能跑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cbworld as B

# ---------------------------------------------------------------- 展示体布局
# 全部相对 init 链第 0 格（{T:init:0}）：
#   A 组 自转     (-4, +3, -8)  diamond_block
#   B 组 呼吸     (-1, +3, -8)  gold_block
#   C 组 拼装     (2..3, +3..+4, -8) 四个方块拼成 2x2 面
# 相互间距 >= 1 格，配置命令用 @e[r=2,c=1] 精确定位「刚生成的那一只」。
FOXES = [
    # (组, x, y, z, 主手方块)
    (1, -4, 3, -8, "minecraft:diamond_block"),
    (2, -1, 3, -8, "minecraft:gold_block"),
    (3, 2, 3, -8, "minecraft:polished_andesite"),
    (3, 3, 3, -8, "minecraft:stone_bricks"),
    (3, 2, 4, -8, "minecraft:iron_block"),
    (3, 3, 4, -8, "minecraft:gold_block"),
]

SEL = "@e[scores={fmbe_display=1}]"          # 全部展示体
G1 = "@e[scores={fmbe_group=1}]"             # A 组
G2 = "@e[scores={fmbe_group=2}]"             # B 组
G3 = "@e[scores={fmbe_group=3}]"             # C 组


def at_fox(dx, dy, dz, cmd):
    """把命令的执行位置挪到某只展示体的生成点（相对 init 第 0 格）。"""
    return ("execute positioned {T:init:0} positioned ~%d ~%d ~%d run %s"
            % (dx, dy, dz, cmd))


def init_cmds(ta):
    c = [
        # 1) 聊天栏灰字：sendcommandfeedback 必须第一条
        "gamerule sendcommandfeedback false",
        "gamerule commandblockoutput false",
        "gamerule showdeathmessages false",
        "gamerule announceadvancements false",
        "gamerule showrecipemessages false",
        "gamerule showcoordinates false",
        # 2) 计分项（打标一律用计分，全库零 tag）
        'scoreboard objectives add fmbe_display dummy "FMBE 展示体"',
        'scoreboard objectives add fmbe_group dummy "FMBE 分组"',
        # 3) 常加载：先删后加，保证重复按按钮也幂等
        "tickingarea remove fmbe_demo",
        ta,
        # 4) 清理旧展示体（首次按按钮时没有目标，静默失败，不影响后续）
        "kill @e[type=fox,scores={fmbe_display=1}]",
    ]

    # 5) 逐只生成 + 配置（每条都定位到自己的生成点，靠 r=2,c=1 锁定）
    for group, dx, dy, dz, item in FOXES:
        c.append("execute positioned {T:init:0} run summon fox ~%d ~%d ~%d" % (dx, dy, dz))
        c.append(at_fox(dx, dy, dz,
                        "replaceitem entity @e[type=fox,r=2,c=1] "
                        "slot.weapon.mainhand 0 %s" % item))
        c.append(at_fox(dx, dy, dz,
                        "scoreboard players set @e[type=fox,r=2,c=1] fmbe_display 1"))
        c.append(at_fox(dx, dy, dz,
                        "scoreboard players set @e[type=fox,r=2,c=1] fmbe_group %d" % group))

    # 6) 伪装：隐身 + 抗性（一次性，对全部展示体生效）
    c += [
        "effect %s invisibility 999999 1 true" % SEL,
        "effect %s resistance 999999 255 true" % SEL,
        # 7) 狐狸的十种叫声全清（FMBE 的必备收尾）
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.aggro",
        "stopsound @a mob.fox.bite",
        "stopsound @a mob.fox.death",
        "stopsound @a mob.fox.eat",
        "stopsound @a mob.fox.hurt",
        "stopsound @a mob.fox.screech",
        "stopsound @a mob.fox.sleep",
        "stopsound @a mob.fox.sniff",
        "stopsound @a mob.fox.spit",
        'tellraw @a {"rawtext":[{"text":"§eFMBE 已就绪 §8· §f三组展示体已生成，'
        '§7上方按钮可开关各组动画"}]}',
    ]
    return c


def render_cmds():
    """FMBE 前置 8 条：把 v.* 变量灌进原版动画通道。必须每刻跑。"""
    return [
        'playanimation %s animation.player.sleeping none 0 "" '
        'controller.animation.fox.move' % SEL,
        'playanimation %s animation.creeper.swelling none 0 '
        '"v.xbasepos=v.xbasepos??0;v.ybasepos=v.ybasepos??0;v.zbasepos=v.zbasepos??0;'
        'v.xpos=v.xpos??0;v.ypos=v.ypos??0;v.zpos=v.zpos??0;'
        'v.xrot=v.xrot??0;v.yrot=v.yrot??0;v.zrot=v.zrot??0;'
        'v.scale=v.scale??1;v.xzscale=v.xzscale??1;v.yscale=v.yscale??1;'
        'v.swelling_scale1=2.1385*math.sqrt(v.xzscale*v.scale);'
        'v.swelling_scale2=2.1385*math.sqrt(v.yscale*v.scale);" fmbe.scale' % SEL,
        'playanimation %s animation.ender_dragon.neck_head_movement none 0 '
        '"v.head_rotation_x=0;v.head_rotation_y=0;v.head_rotation_z=0;'
        'v.head_position_x=(v.xbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);'
        'v.head_position_y=(10.05185375+v.ybasepos*0.467625)*math.sqrt(v.yscale*v.scale);'
        'v.head_position_z=(17.108-v.zbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);" '
        'fmbe.shift_pos' % SEL,
        'playanimation %s animation.warden.move none 0 '
        '"v.body_x_rot=90+v.xrot;v.body_z_rot=90+v.yrot;" fmbe.xrot' % SEL,
        'playanimation %s animation.player.attack.rotations none 0 '
        '"v.attack_body_rot_y=-v.zrot;" fmbe.zrot' % SEL,
        'playanimation %s animation.parrot.moving none 0 '
        '"v.wing_flap=(16-v.xpos)*3.3333333;" fmbe.xpos' % SEL,
        'playanimation %s animation.minecart.move.v1.0 none 0 '
        '"v.rail_offset.x=0;v.rail_offset.y=1.6485+v.ypos/16;v.rail_offset.z=0;" '
        'fmbe.ypos' % SEL,
        'playanimation %s animation.parrot.dance none 0 '
        '"v.dance.x=-v.zpos;v.dance.y=0;" fmbe.zpos' % SEL,
        # 锁位锁朝向：狐狸一旦被推走或转头，方块会跟着甩出去
        "execute as %s at @s run tp @s ~ ~ ~ 0 0" % SEL,
        # 渲染过程中仍会触发叫声，每刻补刀（只清最吵的三条）
        "stopsound @a mob.fox.ambient",
        "stopsound @a mob.fox.aggro",
        "stopsound @a mob.fox.bite",
    ]


def spec(ta="tickingarea add circle ~ ~ ~ 4 fmbe_demo"):
    return {
        "meta": {"name": "FMBE 指令展示", "spawn": [8, -58, 7], "gametype": "creative"},
        "chains": [
            {"id": "init", "kind": "impulse", "button": True, "label": "初始化",
             "cmds": init_cmds(ta)},

            {"id": "render", "kind": "gated", "label": "渲染",
             "gate": "execute if entity %s" % SEL,
             "cmds": render_cmds()},

            {"id": "anim_a", "kind": "gated", "label": "动画·自转",
             "gate": "execute if entity %s" % G1,
             "cmds": ['playanimation %s animation.player.attack.positions none 0 '
                      '"v.ypos=24;v.yrot=math.mod(q.life_time*90,360);" fmbe.anim_a' % G1]},

            {"id": "anim_b", "kind": "gated", "label": "动画·呼吸",
             "gate": "execute if entity %s" % G2,
             "cmds": ['playanimation %s animation.player.attack.positions none 0 '
                      '"v.ypos=8;v.scale=1.2+0.4*math.sin(q.life_time*120);'
                      'v.zrot=12*math.sin(q.life_time*60);" fmbe.anim_b' % G2]},

            {"id": "anim_c", "kind": "gated", "label": "动画·拼装",
             "gate": "execute if entity %s" % G3,
             "cmds": ['playanimation %s animation.player.attack.positions none 0 '
                      '"v.ypos=8*math.sin(q.life_time*120);" fmbe.anim_c' % G3]},
        ],
        "panels": [
            {"label": "面板·自转断开", "cmds": ["{SET:anim_a:dis}"]},
            {"label": "面板·自转接通", "cmds": ["{SET:anim_a:arm}"]},
            {"label": "面板·呼吸断开", "cmds": ["{SET:anim_b:dis}"]},
            {"label": "面板·呼吸接通", "cmds": ["{SET:anim_b:arm}"]},
            {"label": "面板·拼装断开", "cmds": ["{SET:anim_c:dis}"]},
            {"label": "面板·拼装接通", "cmds": ["{SET:anim_c:arm}"]},
        ],
    }


def to_system(s):
    chains = []
    for ch in s["chains"]:
        cmds = list(ch["cmds"])
        if ch["kind"] == "gated":
            cmds = ["{RESET}"] + cmds      # 三段式标记：第 3 格是重置块
        chains.append({"id": ch["id"], "kind": ch["kind"], "label": ch.get("label"),
                       "gate": ch.get("gate"), "cmds": cmds,
                       "button": ch.get("button", ch["kind"] == "impulse")})
    for p in s["panels"]:
        chains.append({"id": "panel", "kind": "impulse", "label": p["label"],
                       "cmds": p["cmds"], "button": True})

    props = [
        {"kind": "sign", "front": ["§l§6FMBE 指令展示", "§7纯指令 · 零附加包",
                                   "§8先按上方「初始化」按钮", "§8下方是断链面板"]},
        {"kind": "sign", "front": ["§l§b三组展示", "§71 自转 · 钻石块",
                                   "§72 呼吸 · 金块", "§73 拼装 · 四个方块"]},
        {"kind": "sign", "front": ["§l§a可调变量", "§7xpos/ypos/zpos 位移",
                                   "§7xrot/yrot/zrot 旋转", "§7scale 缩放"]},
        {"kind": "chest", "name": "展示物", "items": [
            B.item_nbt("diamond_block", display_name="§b展示物 · 钻石块",
                       lore=["§7塞进狐狸主手即换展示内容"]),
            B.item_nbt("gold_block", display_name="§6展示物 · 金块", lore=["§7同上"]),
            B.item_nbt("stone_bricks", display_name="§7展示物 · 石砖", lore=["§7同上"]),
            B.item_nbt("iron_block", display_name="§f展示物 · 铁块", lore=["§7同上"]),
            B.item_nbt("polished_andesite", display_name="§7展示物 · 磨制安山岩", lore=["§7同上"]),
        ]},
    ]
    return {"chains": chains, "props": props, "props_pedestal": True}


def measure_ta(s):
    """按实际排版量出指令区范围，生成覆盖全区的矩形常加载命令。

    init 第 9 条固定落在 (9, 2)，所以相对它算偏移即可。
    命令条数不变 → 排版不变，两趟结果一致。
    """
    blocks, _, _ = B.build_scene(to_system(s))
    xs = [x for (x, y, z) in blocks]
    zs = [z for (x, y, z) in blocks]
    return ("tickingarea add ~%d ~-4 ~%d ~%d ~4 ~%d fmbe_demo"
            % (min(xs) - 9, min(zs) - 8 - 2, max(xs) - 9, max(zs) - 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-spec")
    ap.add_argument("--spec")
    ap.add_argument("--template")
    ap.add_argument("--out")
    a = ap.parse_args()

    if a.dump_spec:
        s = spec(measure_ta(spec()))
        os.makedirs(os.path.dirname(os.path.abspath(a.dump_spec)), exist_ok=True)
        with open(a.dump_spec, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
        n = sum(len(c["cmds"]) for c in s["chains"]) + sum(len(p["cmds"]) for p in s["panels"])
        print("[spec] %s  链 %d 条 / 面板 %d 个 / 命令 %d 条"
              % (a.dump_spec, len(s["chains"]), len(s["panels"]), n))
        return

    if not (a.spec and a.template and a.out):
        ap.error("生成世界需要 --spec / --template / --out")
    with open(a.spec, encoding="utf-8") as f:
        s = json.load(f)
    s = spec(measure_ta(s))
    m = s["meta"]
    B.CHAIN_SUMMARY["init"] = "计分项 / 规则 / 常加载 / 生成三组展示体"
    info = B.build(a.template, a.out, m["name"], m.get("spawn"), 1, to_system(s))
    print("[完成] %s" % info["out"])
    print("        区块 %d / 命令方块 %d / 按钮 %d / 说明区 %d"
          % (info["chunks"], info["blocks"], info["buttons"], info["props"]))


if __name__ == "__main__":
    main()
