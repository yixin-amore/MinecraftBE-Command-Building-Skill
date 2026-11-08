# Build Plan: arena-countdown

Button starts a 3-second countdown; a repeat clock advances one second at a time, shows 3/2/1/GO, then switches the arena to running state.

## Summary

- Blocks: **18** (repeat 1, impulse 2, chain 15)
- Heads: 3 — `clock`, `start_btn`, `reset_btn`
- Max chain depth: 9
- Result: **0 error(s), 0 warning(s)**, 0 info

## Chain map

`clock` (repeat/uncond/always/d0)
    └─ `tick_wrap` (chain/cond/always/d0)
        └─ `pulse` (chain/cond/always/d0)
            └─ `show3` (chain/uncond/always/d0)
                └─ `show2` (chain/uncond/always/d0)
                    └─ `show1` (chain/uncond/always/d0)
                        └─ `go` (chain/uncond/always/d0)
                            └─ `start_running` (chain/uncond/always/d0)
                                └─ `count_down` (chain/uncond/always/d0)
                                    └─ `clear_pulse` (chain/uncond/always/d0)

`start_btn` (impulse/uncond/redstone/d0)
    └─ `start_count` (chain/cond/always/d0)
        └─ `start_tick` (chain/cond/always/d0)
            └─ `start_title` (chain/cond/always/d0)

`reset_btn` (impulse/uncond/redstone/d0)
    └─ `reset_count` (chain/cond/always/d0)
        └─ `reset_tick` (chain/cond/always/d0)
            └─ `reset_title` (chain/cond/always/d0)


## Build sheet

| # | id | type | condition | redstone | delay | next | command |
|---|---|---|---|---|---|---|---|
| 1 | `clock` | repeat | unconditional | always_active | 0 | `tick_wrap` | `scoreboard players add #tick arena 1` |
| 2 | `tick_wrap` | chain | conditional | always_active | 0 | `pulse` | `execute if score #tick arena matches 20.. run scoreboard players set #tick arena 0` |
| 3 | `pulse` | chain | conditional | always_active | 0 | `show3` | `scoreboard players set #second arena 1` |
| 4 | `show3` | chain | unconditional | always_active | 0 | `show2` | `execute if score #second arena matches 1 if score #state arena matches 1 if score #count arena matches 3 run title @a title §e3` |
| 5 | `show2` | chain | unconditional | always_active | 0 | `show1` | `execute if score #second arena matches 1 if score #state arena matches 1 if score #count arena matches 2 run title @a title §e2` |
| 6 | `show1` | chain | unconditional | always_active | 0 | `go` | `execute if score #second arena matches 1 if score #state arena matches 1 if score #count arena matches 1 run title @a title §e1` |
| 7 | `go` | chain | unconditional | always_active | 0 | `start_running` | `execute if score #second arena matches 1 if score #state arena matches 1 if score #count arena matches 0 run title @a title §aGO!` |
| 8 | `start_running` | chain | unconditional | always_active | 0 | `count_down` | `execute if score #second arena matches 1 if score #state arena matches 1 if score #count arena matches 0 run scoreboard players set #state arena 2` |
| 9 | `count_down` | chain | unconditional | always_active | 0 | `clear_pulse` | `execute if score #second arena matches 1 if score #state arena matches 1 if score #count arena matches 1.. run scoreboard players remove #count arena 1` |
| 10 | `clear_pulse` | chain | unconditional | always_active | 0 | — | `scoreboard players set #second arena 0` |
| 11 | `start_btn` | impulse | unconditional | needs_redstone | 0 | `start_count` | `scoreboard players set #state arena 1` |
| 12 | `start_count` | chain | conditional | always_active | 0 | `start_tick` | `scoreboard players set #count arena 3` |
| 13 | `start_tick` | chain | conditional | always_active | 0 | `start_title` | `scoreboard players set #tick arena 19` |
| 14 | `start_title` | chain | conditional | always_active | 0 | — | `title @a title §6Get ready!` |
| 15 | `reset_btn` | impulse | unconditional | needs_redstone | 0 | `reset_count` | `scoreboard players set #state arena 0` |
| 16 | `reset_count` | chain | conditional | always_active | 0 | `reset_tick` | `scoreboard players set #count arena 0` |
| 17 | `reset_tick` | chain | conditional | always_active | 0 | `reset_title` | `scoreboard players set #tick arena 0` |
| 18 | `reset_title` | chain | conditional | always_active | 0 | — | `title @a clear` |

## Setup

Run once before building:

```mcfunction
scoreboard objectives add arena dummy
scoreboard players set #state arena 0
scoreboard players set #count arena 0
scoreboard players set #tick arena 0
scoreboard players set #second arena 0
```

## Tests

- [ ] Press start once: 3, 2, 1, GO appear one second apart.
- [ ] Press start twice quickly: countdown restarts at 3 without skipping.
- [ ] Press reset during countdown: title clears and state returns to idle.
- [ ] Two players online: both see the same countdown titles.
- [ ] Leave and rejoin during countdown: state stays consistent.

## Design notes

- State: #state 0=idle, 1=counting, 2=running.
- The #second flag is the key: display blocks are unconditional, so they run every tick, but the flag gates them to one second.
- If you prefer fewer blocks, titleraw with a score component can show #count directly.

---

Generated by `scripts/chain_lint.py`. Static checks only — verify in-game before shipping.
