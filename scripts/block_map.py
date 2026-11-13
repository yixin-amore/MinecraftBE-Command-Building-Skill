"""Small Java-name -> Bedrock-name map used by building/BDX tools.

Bedrock is not Java: snow_block is `snow`; top snow is `snow_layer`.
The table is deliberately curated; for unknown blocks, verify in game or
consult the Bedrock block data table instead of guessing.
"""
from __future__ import annotations

# no `minecraft:` prefix; canonical Bedrock block names
JAVA_TO_BEDROCK = {
    "snow_block": "snow",
    "grass_block": "grass",
    "note_block": "noteblock",
    "cobweb": "web",
    "spawner": "mob_spawner",
    "magma_block": "magma",
    "slime_block": "slime",
    "bricks": "brick_block",
    "nether_bricks": "nether_brick",
    "end_stone_bricks": "end_bricks",
    "terracotta": "hardened_clay",
    "oak_planks": "oak_planks",
}


def normalize(name: str) -> str:
    n = name.strip()
    if n.startswith("minecraft:"):
        n = n[len("minecraft:"):]
    return JAVA_TO_BEDROCK.get(n, n)


def with_namespace(name: str) -> str:
    return "minecraft:" + normalize(name)
