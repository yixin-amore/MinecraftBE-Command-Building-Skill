#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_commands.py —— spec 指令体检器（通用，任何 spec 都能跑）

不生成世界，只把 spec 里每条命令按「静默失败清单」过一遍。查的是那些
游戏里不报错、只是**什么都不做**的写法：

  1. `@s` 出现在没有 `execute ... as <目标>` 的命令里（命令方块没有实体，
     `@s` 直接 No targets matched，而且方块界面里只显示一行灰字）
  2. `titleraw` / `tellraw` 的 JSON 解析失败，或 JSON 里有真实换行
  3. `%%N` 索引越界（N > 参数个数），或参数个数与 `%%N` 最大值不匹配
  4. 计分项用了但初始化链里没 `objectives add`
  5. 音效 id 不在白名单里（Java 音效在 Bedrock 静默不响）
  6. `execute` 里 `if`/`unless` 之后又跟 `run` 前缺 `run`
  7. 选择器参数拼写（`hasitem` 用了 `slot.` 之外的位置名等）
  8. 条件方块 conditional_bit 被用到（本项目铁律：断链只改朝向）

用法：
  python lint_commands.py spec.json
  python lint_commands.py spec.json --strict     # 有 warning 也判失败
"""
import argparse
import io
import json
import re
import sys

# Bedrock 真实存在的音效（网易服实测可用）。Java 独有的一律不收。
SOUNDS = {
    "random.spyglass_use", "random.click", "random.orb", "random.pop", "random.bow", "random.bowhit",
    "random.break", "random.burp", "random.chestopen", "random.chestclosed",
    "random.explode", "random.fizz", "random.hurt", "random.levelup",
    "random.splash", "random.swim", "random.toast", "random.anvil_use",
    "random.anvil_land", "random.glass", "random.drink", "random.eat",
    "note.pling", "note.bass", "note.harp", "note.bell", "note.chime",
    "note.flute", "note.guitar", "note.xylobass", "note.iron_xylophone",
    "note.cow_bell", "note.didgeridoo", "note.bit", "note.banjo",
    "mob.blaze.hit", "mob.blaze.breathe", "mob.ghast.fireball",
    "mob.irongolem.hit", "mob.irongolem.death", "mob.irongolem.throw",
    "mob.irongolem.walk",
    "mob.enderdragon.growl", "mob.wither.shoot", "mob.zombie.wood",
    "mob.skeleton.hurt", "mob.creeper.say", "mob.shulker.shoot",
    "armor.equip_iron", "armor.equip_chain", "armor.equip_generic",
    "beacon.activate", "beacon.power", "beacon.deactivate",
    "block.beacon.activate", "block.beacon.power", "block.beacon.deactivate",
    "item.trident.thunder", "item.trident.throw", "item.shield.block",
    "item.bucket.empty", "item.bucket.fill", "item.bottle.fill",
    "fire.ignite", "fire.fire", "fire.extinguish",
    "liquid.lava", "liquid.water", "liquid.lavapop",
    "ambient.weather.thunder", "ambient.cave", "ambient.weather.rain",
    "cauldron.explode", "conduit.activate", "conduit.ambient",
    "crossbow.shoot", "crossbow.loading.start", "crossbow.loading.middle",
    "crossbow.loading.end", "crossbow.quick_charge.start",
    "elytra.loop", "elytra.loop.rock", "totem.use", "respawn_anchor.charge",
    "ui.button.click", "ui.toast.in", "ui.toast.out",
    "camera.take_picture", "bell.ring", "raid.horn", "horn.call.0",
    "bottle.dragonbreath", "dig.stone", "dig.wood", "dig.gravel",
    "step.stone", "step.wood", "step.grass", "step.sand",
    "hit.stone", "hit.wood", "hit.cloth",
    "mob.wolf.bark", "mob.cat.meow", "mob.villager.yes", "mob.villager.no",
    "portal.travel", "portal.trigger", "shulker.close", "shulker.open",
    "soul_escape", "sculk.sensor", "sculk.shrieker_shriek",
}

# Bedrock 真实存在的粒子（网易服实测出粒子）。
#
# ❗ 粒子名写错**不会报错**，只是什么都不显示 —— 比音效更难查，必须靠白名单兜。
#    踩过：`electric_spark_particle`（较新版本才有的 id）在网易服上静默不出，
#    而默认枪型正好用它 → 表现成「枪口焰有、弹道粒子一条没有」。
PARTICLES = {
    # 基础
    "basic_flame_particle", "basic_smoke_particle", "basic_bubble_particle",
    "basic_crit_particle", "basic_portal_particle",
    # 命中 / 爆炸
    "critical_hit_emitter", "huge_explosion_emitter", "explosion_manual",
    "cauldron_explosion_emitter", "knockback_roar_particle",
    # 弹道 / 线状
    "endrod", "balloon_gas_particle", "redstone_wire_dust_particle",
    "sparkler_emitter", "dragon_breath_trail", "villager_happy",
    # 实战样本里验证过的（七个 mcworld 实测）
    "snowflake_particle", "basic_flash", "mobflame_single", "wind_explosion_emitter",
    "egg_destroy_emitter", "dragon_death_explosion_emitter", "trial_spawner_detection",
    "sonic_explosion", "shulker_bullet", "electric_spark_particle",
    # 常见装饰
    "heart", "note", "snowballpoof", "splash_spell_emitter",
    "totem_particle", "enchanting_table_particle", "lava_particle",
    "water_wake_particle", "soul_particle", "portal_directional_particle",
}

# Java 独有、Bedrock 里静默不响的常见音效
JAVA_ONLY = {
    "entity.player.attack.strong", "entity.arrow.shoot", "block.note_block.pling",
    "ui.button.click.java", "block.note_block.bass", "entity.generic.explode",
    "item.trident.riptide_1", "entity.experience_orb.pickup",
}

OBJ_RE = re.compile(r"\bobjective[s]?\s+(?:add\s+)?([a-z0-9_]+)")
SEL_OBJ_RE = re.compile(r"objective\s*[:=]\s*\"?([a-z0-9_]+)")
SCORE_OBJ_RE = re.compile(r"\"objective\"\s*:\s*\"([a-z0-9_]+)\"")
AS_RE = re.compile(r"\bas\s+@[aeprs]")
TITLERAW_RE = re.compile(r"^(titleraw|tellraw)\s+(\S+)\s+(\w+)\s+(.*)$", re.S)


def parse_json_tail(cmd):
    """取出 tellraw/titleraw 的 JSON 部分并解析，返回 (ok, obj_or_err)。"""
    m = TITLERAW_RE.match(cmd)
    if not m:
        return None, None
    tail = m.group(4).strip()
    try:
        return True, json.loads(tail)
    except Exception as e:
        return False, str(e)


def walk_pct(obj, out):
    """递归收集 %%N 的 N 值。"""
    if isinstance(obj, dict):
        if "translate" in obj and isinstance(obj["translate"], str):
            for n in re.findall(r"%%(\d+)", obj["translate"]):
                out.append(int(n))
        for v in obj.values():
            walk_pct(v, out)
    elif isinstance(obj, list):
        for v in obj:
            walk_pct(v, out)


def lint(spec, strict=False):
    errs, warns = [], []

    def E(chain, idx, msg):
        errs.append("[%s#%d] %s" % (chain, idx + 1, msg))

    def W(chain, idx, msg):
        warns.append("[%s#%d] %s" % (chain, idx + 1, msg))

    declared = set()
    for c in spec["chains"]:
        for cmd in c.get("cmds", []):
            if "objectives add" in cmd:
                declared.add(cmd.split("objectives add", 1)[1].split()[0])

    used = set()
    ncmd = 0
    for c in spec["chains"]:
        cid = c.get("id", "?")
        for i, cmd in enumerate(c.get("cmds", [])):
            ncmd += 1

            # 1 @s 越界
            if "@s" in cmd and not AS_RE.search(cmd):
                E(cid, i, "@s 没有 execute as 上下文，命令方块里 No targets matched")

            # 8 conditional_bit
            if c.get("cond") or "conditional_bit" in cmd:
                E(cid, i, "用了条件方块，铁律只允许改朝向断链")

            # 2 JSON 解析 + 真实换行
            if cmd.startswith(("titleraw", "tellraw")):
                if "\n" in cmd:
                    E(cid, i, "JSON 里有真实换行（源码里必须写 \\n 转义）")
                ok, obj = parse_json_tail(cmd)
                if ok is False:
                    E(cid, i, "JSON 解析失败：" + str(obj)[:80])
                elif ok:
                    pct = []
                    walk_pct(obj, pct)
                    # 3 %%N 越界
                    if pct:
                        withs = _collect_with(obj)
                        if withs is not None and max(pct) > len(withs):
                            E(cid, i, "%%%%%d 越界（只有 %d 个参数）" % (max(pct), len(withs)))

            # 4 计分项
            for o in SEL_OBJ_RE.findall(cmd) + SCORE_OBJ_RE.findall(cmd):
                used.add(o)
            for o in re.findall(r"scores=\{[^}]*\}", cmd):
                for k in re.findall(r"([a-z0-9_]+)\s*=", o):
                    if k != "scores":
                        used.add(k)
            for m in re.finditer(r"scoreboard players (?:set|add|remove|reset|operation|random|test)\s+\S+\s+([a-z0-9_]+)", cmd):
                used.add(m.group(1))

            # 4b `scores=` 写在选择器外面 —— execute 没有这个子命令，整条语法错误
            #    踩过：`... if entity @s[y=~1.5,dy=1] scores={tg_aim=1} run ...`
            for m in re.finditer(r"scores=\{", cmd):
                head = cmd[:m.start()]
                if head.rfind("]") > head.rfind("["):
                    E(cid, i, "scores= 在选择器方括号外面（execute 没有 scores 子命令），"
                              "整条会语法错误：%s" % cmd[max(0, m.start()-40):m.start()+20])

            # 5 音效
            for s in re.findall(r"playsound\s+([a-z0-9_.]+)", cmd):
                if s in JAVA_ONLY or s not in SOUNDS:
                    W(cid, i, "音效 %s 不在白名单（Java 音效在 Bedrock 静默不响）" % s)

            # 5b 粒子 —— 名字写错**不报错、静默不出粒子**，只能靠白名单兜住。
            #    踩过：`electric_spark_particle` 在网易服上完全不显示，
            #    默认枪型正好用它 → 玩家以为"粒子功能坏了"。
            for pt in re.findall(r"particle\s+([a-z0-9_:]+)", cmd):
                if pt.split(":")[-1] not in PARTICLES:
                    W(cid, i, "粒子 %s 不在白名单（写错不报错、静默不出粒子）" % pt)

            # 9 假玩家名带 # —— 网易服把 # 当注释符，整条语法错误
            for m in re.finditer(r"scoreboard players (?:set|add|remove|reset|operation|random|test)\s+(?:\S+\s+)?(#\w+)", cmd):
                E(cid, i, "假玩家名 %s 带 #，网易服会判语法错误（改 sys_ 前缀）" % m.group(1))

            # 10 with 写成裸数组组件 —— 游戏不解析，%%N 原样打在屏幕上
            if re.search(r'"with"\s*:\s*\[\s*\{', cmd):
                E(cid, i, '"with" 用了裸数组组件，必须写成 "with":{"rawtext":[...]}')

            # 11 同一选择器里重复 scores= —— 游戏报「重复的 scores 命名」，整条不执行
            #    正确：@a[scores={tg_fire=1,tg_type=1}]
            #    错误：@a[scores={tg_fire=1},scores={tg_type=1}]
            #    注意：多个 scores= 分属**不同选择器**是合法的（HUD 的 27 个 @s[scores=...]）
            for m in re.finditer(r"@[a-z]", cmd):
                j = m.end()
                if j >= len(cmd) or cmd[j] != "[":
                    continue
                depth, k = 0, j
                while k < len(cmd):
                    if cmd[k] in "[{":
                        depth += 1
                    elif cmd[k] in "]}":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                seg = cmd[j:k + 1]
                n = seg.count("scores=")
                if n > 1:
                    E(cid, i, "选择器 %s 里有 %d 个 scores=，游戏会报「重复的 scores 命名」"
                              "（合并成一个：scores={a=1,b=1}）" % (m.group(0), n))

            # 12 translate %%N 越界 —— selector 失败被剔除后数组变短，游戏把 %N 打上屏
            #    每个 with.rawtext 末尾必须挂 {"text":""} 兜底（C9 / 70.2 / U13）
            if re.search(r'"translate":"%%\d+"', cmd) and '{"text":""}' not in cmd:
                E(cid, i, 'translate 用了 %%N，但 with 里没有 {"text":""} 兜底；'
                          'selector 失败时会漏 %N 到屏幕上')

            # 6 execute 结构
            if cmd.startswith("execute") and " run " not in cmd:
                E(cid, i, "execute 缺 run（后面会被当成参数，整条不执行）")

            # 7 hasitem 位置名
            for loc in re.findall(r"location=([a-z_.]+)", cmd):
                if loc not in ("slot.weapon.mainhand", "slot.weapon.offhand",
                               "slot.armor.head", "slot.armor.chest",
                               "slot.armor.legs", "slot.armor.feet",
                               "slot.container", "slot.hotbar", "slot.inventory",
                               "slot.enderchest"):
                    W(cid, i, "hasitem 位置名可疑：%s" % loc)

    for o in sorted(used - declared):
        errs.append("[objectives] %s 被使用但初始化链没 add" % o)

    return ncmd, errs, warns


def _collect_with(obj):
    """粗略统计 rawtext 里的组件总数（用于 %%N 越界判断）。"""
    if isinstance(obj, dict) and "rawtext" in obj:
        return obj["rawtext"]
    if isinstance(obj, list):
        return obj
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    spec = json.load(io.open(args.spec, encoding="utf-8"))
    n, errs, warns = lint(spec, args.strict)

    print("体检 %d 条命令" % n)
    for e in errs:
        print("  \u2717 " + e)
    for w in warns:
        print("  ! " + w)
    if not errs and not warns:
        print("  \u2713 无问题")
    elif not errs:
        print("  \u2713 无致命问题（%d 条提示）" % len(warns))
    print()
    bad = bool(errs) or (args.strict and bool(warns))
    print("结论：" + ("不合格，需返工" if bad else "通过"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
