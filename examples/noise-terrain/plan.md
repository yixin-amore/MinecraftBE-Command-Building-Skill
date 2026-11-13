# Build Plan: value-noise-terrain

256 根柱子 + 32 位整数值噪声 fBm（3 层）+ 2 遍 3×3 邻域均值平滑 → 2..18 高度 → 32×32 地形。boot impulse 抽种子；grid 每 tick 两根柱子；calc 分 stage 并行算；draw 每 4 tick 一档。

## Summary

- Blocks: **429** (repeat 9, impulse 1, chain 419)
- Heads: 10 — `boot00`, `prep00`, `grid00`, `calc100`, `calc200`, `calc300`, `calc400`, `calc500`, `calc600`, `draw00`
- Max chain depth: 81
- Result: **0 error(s), 1 warning(s)**, 2 info

## Issues

### Warnings

- **LONG_CHAIN**: chain depth is 81; consider splitting into stages

### Notes

- LONG_COMMAND `draw70`: command is 1146 chars; consider splitting it
- MANY_BLOCKS: 429 blocks; split into functions or multiple chains

## Chain map

`boot00` (impulse/uncond/redstone/d0)
    └─ `boot01` (chain/uncond/always/d0)
        └─ `boot02` (chain/uncond/always/d0)
            └─ `boot03` (chain/uncond/always/d0)
                └─ `boot04` (chain/uncond/always/d0)
                    └─ `boot05` (chain/uncond/always/d0)
                        └─ `boot06` (chain/uncond/always/d0)
                            └─ `boot07` (chain/uncond/always/d0)
                                └─ `boot08` (chain/uncond/always/d0)
                                    └─ `boot09` (chain/uncond/always/d0)
                                        └─ `boot10` (chain/uncond/always/d0)
                                            └─ `boot11` (chain/uncond/always/d0)
                                                └─ `boot12` (chain/uncond/always/d0)
                                                    └─ `boot13` (chain/uncond/always/d0)
                                                        └─ `boot14` (chain/uncond/always/d0)
                                                            └─ `boot15` (chain/uncond/always/d0)
                                                                └─ `boot16` (chain/uncond/always/d0)
                                                                    └─ `boot17` (chain/uncond/always/d0)
                                                                        └─ `boot18` (chain/uncond/always/d0)
                                                                            └─ `boot19` (chain/uncond/always/d0)
                                                                                └─ `boot20` (chain/uncond/always/d0)
                                                                                    └─ `boot21` (chain/uncond/always/d0)
                                                                                        └─ `boot22` (chain/uncond/always/d0)
                                                                                            └─ `boot23` (chain/uncond/always/d0)
                                                                                                └─ `boot24` (chain/uncond/always/d0)
                                                                                                    └─ `boot25` (chain/uncond/always/d0)
                                                                                                        └─ `boot26` (chain/uncond/always/d0)
                                                                                                            └─ `boot27` (chain/uncond/always/d0)
                                                                                                                └─ `boot28` (chain/uncond/always/d0)
                                                                                                                    └─ `boot29` (chain/uncond/always/d0)
                                                                                                                        └─ `boot30` (chain/uncond/always/d0)
                                                                                                                            └─ `boot31` (chain/uncond/always/d0)
                                                                                                                                └─ `boot32` (chain/uncond/always/d0)
                                                                                                                                    └─ `boot33` (chain/uncond/always/d0)
                                                                                                                                        └─ `boot34` (chain/uncond/always/d0)
                                                                                                                                            └─ `boot35` (chain/uncond/always/d0)
                                                                                                                                                └─ `boot36` (chain/uncond/always/d0)
                                                                                                                                                    └─ `boot37` (chain/uncond/always/d0)
                                                                                                                                                        └─ `boot38` (chain/uncond/always/d0)
                                                                                                                                                            └─ `boot39` (chain/uncond/always/d0)
                                                                                                                                                                └─ `boot40` (chain/uncond/always/d0)
                                                                                                                                                                    └─ `boot41` (chain/uncond/always/d0)
                                                                                                                                                                        └─ `boot42` (chain/uncond/always/d0)
                                                                                                                                                                            └─ `boot43` (chain/uncond/always/d0)
                                                                                                                                                                                └─ `boot44` (chain/uncond/always/d0)
                                                                                                                                                                                    └─ `boot45` (chain/uncond/always/d0)
                                                                                                                                                                                        └─ `boot46` (chain/uncond/always/d0)
                                                                                                                                                                                            └─ `boot47` (chain/uncond/always/d0)
                                                                                                                                                                                                └─ `boot48` (chain/uncond/always/d0)
                                                                                                                                                                                                    └─ `boot49` (chain/uncond/always/d0)
                                                                                                                                                                                                        └─ `boot50` (chain/uncond/always/d0)
                                                                                                                                                                                                            └─ `boot51` (chain/uncond/always/d0)
                                                                                                                                                                                                                └─ `boot52` (chain/uncond/always/d0)
                                                                                                                                                                                                                    └─ `boot53` (chain/uncond/always/d0)
                                                                                                                                                                                                                        └─ `boot54` (chain/uncond/always/d0)
                                                                                                                                                                                                                            └─ `boot55` (chain/uncond/always/d0)
                                                                                                                                                                                                                                └─ `boot56` (chain/uncond/always/d0)
                                                                                                                                                                                                                                    └─ `boot57` (chain/uncond/always/d0)
                                                                                                                                                                                                                                        └─ `boot58` (chain/uncond/always/d0)
                                                                                                                                                                                                                                            └─ `boot59` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                └─ `boot60` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                    └─ `boot61` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                        └─ `boot62` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                            └─ `boot63` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                └─ `boot64` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                    └─ `boot65` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                        └─ `boot66` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                            └─ `boot67` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                └─ `boot68` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                    └─ `boot69` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                        └─ `boot70` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                            └─ `boot71` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                └─ `boot72` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                    └─ `boot73` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                        └─ `boot74` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                            └─ `boot75` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                └─ `boot76` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                    └─ `boot77` (chain/uncond/always/d0)

`prep00` (repeat/uncond/always/d2)
    └─ `prep01` (chain/uncond/always/d0)
        └─ `prep02` (chain/uncond/always/d0)
            └─ `prep03` (chain/uncond/always/d0)
                └─ `prep04` (chain/uncond/always/d0)
                    └─ `prep05` (chain/uncond/always/d0)
                        └─ `prep06` (chain/uncond/always/d0)
                            └─ `prep07` (chain/uncond/always/d0)
                                └─ `prep08` (chain/uncond/always/d0)
                                    └─ `prep09` (chain/uncond/always/d0)
                                        └─ `prep10` (chain/uncond/always/d0)
                                            └─ `prep11` (chain/uncond/always/d0)
                                                └─ `prep12` (chain/uncond/always/d0)
                                                    └─ `prep13` (chain/uncond/always/d0)

`grid00` (repeat/uncond/always/d1)
    └─ `grid01` (chain/uncond/always/d0)
        └─ `grid02` (chain/uncond/always/d0)
            └─ `grid03` (chain/uncond/always/d0)
                └─ `grid04` (chain/uncond/always/d0)
                    └─ `grid05` (chain/uncond/always/d0)
                        └─ `grid06` (chain/uncond/always/d0)
                            └─ `grid07` (chain/uncond/always/d0)
                                └─ `grid08` (chain/uncond/always/d0)
                                    └─ `grid09` (chain/uncond/always/d0)
                                        └─ `grid10` (chain/uncond/always/d0)
                                            └─ `grid11` (chain/uncond/always/d0)
                                                └─ `grid12` (chain/uncond/always/d0)
                                                    └─ `grid13` (chain/uncond/always/d0)
                                                        └─ `grid14` (chain/uncond/always/d0)
                                                            └─ `grid15` (chain/uncond/always/d0)
                                                                └─ `grid16` (chain/uncond/always/d0)
                                                                    └─ `grid17` (chain/uncond/always/d0)
                                                                        └─ `grid18` (chain/uncond/always/d0)
                                                                            └─ `grid19` (chain/uncond/always/d0)
                                                                                └─ `grid20` (chain/uncond/always/d0)
                                                                                    └─ `grid21` (chain/uncond/always/d0)
                                                                                        └─ `grid22` (chain/uncond/always/d0)
                                                                                            └─ `grid23` (chain/uncond/always/d0)

`calc100` (repeat/uncond/always/d0)
    └─ `calc101` (chain/uncond/always/d0)
        └─ `calc102` (chain/uncond/always/d0)
            └─ `calc103` (chain/uncond/always/d0)
                └─ `calc104` (chain/uncond/always/d0)
                    └─ `calc105` (chain/uncond/always/d0)
                        └─ `calc106` (chain/uncond/always/d0)
                            └─ `calc107` (chain/uncond/always/d0)
                                └─ `calc108` (chain/uncond/always/d0)
                                    └─ `calc109` (chain/uncond/always/d0)
                                        └─ `calc110` (chain/uncond/always/d0)
                                            └─ `calc111` (chain/uncond/always/d0)
                                                └─ `calc112` (chain/uncond/always/d0)
                                                    └─ `calc113` (chain/uncond/always/d0)
                                                        └─ `calc114` (chain/uncond/always/d0)
                                                            └─ `calc115` (chain/uncond/always/d0)
                                                                └─ `calc116` (chain/uncond/always/d0)
                                                                    └─ `calc117` (chain/uncond/always/d0)
                                                                        └─ `calc118` (chain/uncond/always/d0)
                                                                            └─ `calc119` (chain/uncond/always/d0)
                                                                                └─ `calc120` (chain/uncond/always/d0)
                                                                                    └─ `calc121` (chain/uncond/always/d0)
                                                                                        └─ `calc122` (chain/uncond/always/d0)
                                                                                            └─ `calc123` (chain/uncond/always/d0)
                                                                                                └─ `calc124` (chain/uncond/always/d0)
                                                                                                    └─ `calc125` (chain/uncond/always/d0)
                                                                                                        └─ `calc126` (chain/uncond/always/d0)
                                                                                                            └─ `calc127` (chain/uncond/always/d0)
                                                                                                                └─ `calc128` (chain/uncond/always/d0)
                                                                                                                    └─ `calc129` (chain/uncond/always/d0)
                                                                                                                        └─ `calc130` (chain/uncond/always/d0)
                                                                                                                            └─ `calc131` (chain/uncond/always/d0)
                                                                                                                                └─ `calc132` (chain/uncond/always/d0)
                                                                                                                                    └─ `calc133` (chain/uncond/always/d0)
                                                                                                                                        └─ `calc134` (chain/uncond/always/d0)
                                                                                                                                            └─ `calc135` (chain/uncond/always/d0)
                                                                                                                                                └─ `calc136` (chain/uncond/always/d0)
                                                                                                                                                    └─ `calc137` (chain/uncond/always/d0)
                                                                                                                                                        └─ `calc138` (chain/uncond/always/d0)
                                                                                                                                                            └─ `calc139` (chain/uncond/always/d0)
                                                                                                                                                                └─ `calc140` (chain/uncond/always/d0)
                                                                                                                                                                    └─ `calc141` (chain/uncond/always/d0)
                                                                                                                                                                        └─ `calc142` (chain/uncond/always/d0)
                                                                                                                                                                            └─ `calc143` (chain/uncond/always/d0)
                                                                                                                                                                                └─ `calc144` (chain/uncond/always/d0)
                                                                                                                                                                                    └─ `calc145` (chain/uncond/always/d0)
                                                                                                                                                                                        └─ `calc146` (chain/uncond/always/d0)
                                                                                                                                                                                            └─ `calc147` (chain/uncond/always/d0)
                                                                                                                                                                                                └─ `calc148` (chain/uncond/always/d0)
                                                                                                                                                                                                    └─ `calc149` (chain/uncond/always/d0)
                                                                                                                                                                                                        └─ `calc150` (chain/uncond/always/d0)
                                                                                                                                                                                                            └─ `calc151` (chain/uncond/always/d0)
                                                                                                                                                                                                                └─ `calc152` (chain/uncond/always/d0)
                                                                                                                                                                                                                    └─ `calc153` (chain/uncond/always/d0)
                                                                                                                                                                                                                        └─ `calc154` (chain/uncond/always/d0)
                                                                                                                                                                                                                            └─ `calc155` (chain/uncond/always/d0)
                                                                                                                                                                                                                                └─ `calc156` (chain/uncond/always/d0)
                                                                                                                                                                                                                                    └─ `calc157` (chain/uncond/always/d0)
                                                                                                                                                                                                                                        └─ `calc158` (chain/uncond/always/d0)
                                                                                                                                                                                                                                            └─ `calc159` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                └─ `calc160` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                    └─ `calc161` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                        └─ `calc162` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                            └─ `calc163` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                └─ `calc164` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                    └─ `calc165` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                        └─ `calc166` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                            └─ `calc167` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                └─ `calc168` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                    └─ `calc169` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                        └─ `calc170` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                            └─ `calc171` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                └─ `calc172` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                    └─ `calc173` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                        └─ `calc174` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                            └─ `calc175` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                └─ `calc176` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                    └─ `calc177` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                        └─ `calc178` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                            └─ `calc179` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                                └─ `calc180` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                                    └─ `calc181` (chain/uncond/always/d0)

`calc200` (repeat/uncond/always/d0)
    └─ `calc201` (chain/uncond/always/d0)
        └─ `calc202` (chain/uncond/always/d0)
            └─ `calc203` (chain/uncond/always/d0)
                └─ `calc204` (chain/uncond/always/d0)
                    └─ `calc205` (chain/uncond/always/d0)
                        └─ `calc206` (chain/uncond/always/d0)
                            └─ `calc207` (chain/uncond/always/d0)
                                └─ `calc208` (chain/uncond/always/d0)
                                    └─ `calc209` (chain/uncond/always/d0)
                                        └─ `calc210` (chain/uncond/always/d0)
                                            └─ `calc211` (chain/uncond/always/d0)
                                                └─ `calc212` (chain/uncond/always/d0)
                                                    └─ `calc213` (chain/uncond/always/d0)
                                                        └─ `calc214` (chain/uncond/always/d0)
                                                            └─ `calc215` (chain/uncond/always/d0)
                                                                └─ `calc216` (chain/uncond/always/d0)
                                                                    └─ `calc217` (chain/uncond/always/d0)
                                                                        └─ `calc218` (chain/uncond/always/d0)
                                                                            └─ `calc219` (chain/uncond/always/d0)
                                                                                └─ `calc220` (chain/uncond/always/d0)
                                                                                    └─ `calc221` (chain/uncond/always/d0)
                                                                                        └─ `calc222` (chain/uncond/always/d0)
                                                                                            └─ `calc223` (chain/uncond/always/d0)
                                                                                                └─ `calc224` (chain/uncond/always/d0)
                                                                                                    └─ `calc225` (chain/uncond/always/d0)
                                                                                                        └─ `calc226` (chain/uncond/always/d0)
                                                                                                            └─ `calc227` (chain/uncond/always/d0)
                                                                                                                └─ `calc228` (chain/uncond/always/d0)
                                                                                                                    └─ `calc229` (chain/uncond/always/d0)
                                                                                                                        └─ `calc230` (chain/uncond/always/d0)
                                                                                                                            └─ `calc231` (chain/uncond/always/d0)
                                                                                                                                └─ `calc232` (chain/uncond/always/d0)
                                                                                                                                    └─ `calc233` (chain/uncond/always/d0)
                                                                                                                                        └─ `calc234` (chain/uncond/always/d0)
                                                                                                                                            └─ `calc235` (chain/uncond/always/d0)
                                                                                                                                                └─ `calc236` (chain/uncond/always/d0)
                                                                                                                                                    └─ `calc237` (chain/uncond/always/d0)
                                                                                                                                                        └─ `calc238` (chain/uncond/always/d0)
                                                                                                                                                            └─ `calc239` (chain/uncond/always/d0)
                                                                                                                                                                └─ `calc240` (chain/uncond/always/d0)
                                                                                                                                                                    └─ `calc241` (chain/uncond/always/d0)
                                                                                                                                                                        └─ `calc242` (chain/uncond/always/d0)
                                                                                                                                                                            └─ `calc243` (chain/uncond/always/d0)
                                                                                                                                                                                └─ `calc244` (chain/uncond/always/d0)
                                                                                                                                                                                    └─ `calc245` (chain/uncond/always/d0)
                                                                                                                                                                                        └─ `calc246` (chain/uncond/always/d0)
                                                                                                                                                                                            └─ `calc247` (chain/uncond/always/d0)
                                                                                                                                                                                                └─ `calc248` (chain/uncond/always/d0)
                                                                                                                                                                                                    └─ `calc249` (chain/uncond/always/d0)
                                                                                                                                                                                                        └─ `calc250` (chain/uncond/always/d0)
                                                                                                                                                                                                            └─ `calc251` (chain/uncond/always/d0)
                                                                                                                                                                                                                └─ `calc252` (chain/uncond/always/d0)
                                                                                                                                                                                                                    └─ `calc253` (chain/uncond/always/d0)
                                                                                                                                                                                                                        └─ `calc254` (chain/uncond/always/d0)
                                                                                                                                                                                                                            └─ `calc255` (chain/uncond/always/d0)
                                                                                                                                                                                                                                └─ `calc256` (chain/uncond/always/d0)
                                                                                                                                                                                                                                    └─ `calc257` (chain/uncond/always/d0)
                                                                                                                                                                                                                                        └─ `calc258` (chain/uncond/always/d0)
                                                                                                                                                                                                                                            └─ `calc259` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                └─ `calc260` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                    └─ `calc261` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                        └─ `calc262` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                            └─ `calc263` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                └─ `calc264` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                    └─ `calc265` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                        └─ `calc266` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                            └─ `calc267` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                └─ `calc268` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                    └─ `calc269` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                        └─ `calc270` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                            └─ `calc271` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                └─ `calc272` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                    └─ `calc273` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                        └─ `calc274` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                            └─ `calc275` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                └─ `calc276` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                    └─ `calc277` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                        └─ `calc278` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                            └─ `calc279` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                                └─ `calc280` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                                                    └─ `calc281` (chain/uncond/always/d0)

`calc300` (repeat/uncond/always/d0)
    └─ `calc301` (chain/uncond/always/d0)
        └─ `calc302` (chain/uncond/always/d0)
            └─ `calc303` (chain/uncond/always/d0)
                └─ `calc304` (chain/uncond/always/d0)
                    └─ `calc305` (chain/uncond/always/d0)
                        └─ `calc306` (chain/uncond/always/d0)
                            └─ `calc307` (chain/uncond/always/d0)
                                └─ `calc308` (chain/uncond/always/d0)
                                    └─ `calc309` (chain/uncond/always/d0)
                                        └─ `calc310` (chain/uncond/always/d0)
                                            └─ `calc311` (chain/uncond/always/d0)
                                                └─ `calc312` (chain/uncond/always/d0)
                                                    └─ `calc313` (chain/uncond/always/d0)
                                                        └─ `calc314` (chain/uncond/always/d0)
                                                            └─ `calc315` (chain/uncond/always/d0)
                                                                └─ `calc316` (chain/uncond/always/d0)
                                                                    └─ `calc317` (chain/uncond/always/d0)
                                                                        └─ `calc318` (chain/uncond/always/d0)
                                                                            └─ `calc319` (chain/uncond/always/d0)
                                                                                └─ `calc320` (chain/uncond/always/d0)
                                                                                    └─ `calc321` (chain/uncond/always/d0)
                                                                                        └─ `calc322` (chain/uncond/always/d0)
                                                                                            └─ `calc323` (chain/uncond/always/d0)
                                                                                                └─ `calc324` (chain/uncond/always/d0)
                                                                                                    └─ `calc325` (chain/uncond/always/d0)
                                                                                                        └─ `calc326` (chain/uncond/always/d0)

`calc400` (repeat/uncond/always/d0)
    └─ `calc401` (chain/uncond/always/d0)
        └─ `calc402` (chain/uncond/always/d0)
            └─ `calc403` (chain/uncond/always/d0)
                └─ `calc404` (chain/uncond/always/d0)
                    └─ `calc405` (chain/uncond/always/d0)
                        └─ `calc406` (chain/uncond/always/d0)
                            └─ `calc407` (chain/uncond/always/d0)
                                └─ `calc408` (chain/uncond/always/d0)
                                    └─ `calc409` (chain/uncond/always/d0)
                                        └─ `calc410` (chain/uncond/always/d0)
                                            └─ `calc411` (chain/uncond/always/d0)
                                                └─ `calc412` (chain/uncond/always/d0)
                                                    └─ `calc413` (chain/uncond/always/d0)
                                                        └─ `calc414` (chain/uncond/always/d0)
                                                            └─ `calc415` (chain/uncond/always/d0)
                                                                └─ `calc416` (chain/uncond/always/d0)
                                                                    └─ `calc417` (chain/uncond/always/d0)
                                                                        └─ `calc418` (chain/uncond/always/d0)
                                                                            └─ `calc419` (chain/uncond/always/d0)
                                                                                └─ `calc420` (chain/uncond/always/d0)
                                                                                    └─ `calc421` (chain/uncond/always/d0)

`calc500` (repeat/uncond/always/d0)
    └─ `calc501` (chain/uncond/always/d0)
        └─ `calc502` (chain/uncond/always/d0)
            └─ `calc503` (chain/uncond/always/d0)
                └─ `calc504` (chain/uncond/always/d0)
                    └─ `calc505` (chain/uncond/always/d0)
                        └─ `calc506` (chain/uncond/always/d0)
                            └─ `calc507` (chain/uncond/always/d0)
                                └─ `calc508` (chain/uncond/always/d0)
                                    └─ `calc509` (chain/uncond/always/d0)
                                        └─ `calc510` (chain/uncond/always/d0)
                                            └─ `calc511` (chain/uncond/always/d0)
                                                └─ `calc512` (chain/uncond/always/d0)
                                                    └─ `calc513` (chain/uncond/always/d0)
                                                        └─ `calc514` (chain/uncond/always/d0)
                                                            └─ `calc515` (chain/uncond/always/d0)
                                                                └─ `calc516` (chain/uncond/always/d0)
                                                                    └─ `calc517` (chain/uncond/always/d0)
                                                                        └─ `calc518` (chain/uncond/always/d0)
                                                                            └─ `calc519` (chain/uncond/always/d0)
                                                                                └─ `calc520` (chain/uncond/always/d0)
                                                                                    └─ `calc521` (chain/uncond/always/d0)

`calc600` (repeat/uncond/always/d0)
    └─ `calc601` (chain/uncond/always/d0)
        └─ `calc602` (chain/uncond/always/d0)
            └─ `calc603` (chain/uncond/always/d0)
                └─ `calc604` (chain/uncond/always/d0)

`draw00` (repeat/uncond/always/d4)
    └─ `draw01` (chain/uncond/always/d0)
        └─ `draw02` (chain/uncond/always/d0)
            └─ `draw03` (chain/uncond/always/d0)
                └─ `draw04` (chain/uncond/always/d0)
                    └─ `draw05` (chain/uncond/always/d0)
                        └─ `draw06` (chain/uncond/always/d0)
                            └─ `draw07` (chain/uncond/always/d0)
                                └─ `draw08` (chain/uncond/always/d0)
                                    └─ `draw09` (chain/uncond/always/d0)
                                        └─ `draw10` (chain/uncond/always/d0)
                                            └─ `draw11` (chain/uncond/always/d0)
                                                └─ `draw12` (chain/uncond/always/d0)
                                                    └─ `draw13` (chain/uncond/always/d0)
                                                        └─ `draw14` (chain/uncond/always/d0)
                                                            └─ `draw15` (chain/uncond/always/d0)
                                                                └─ `draw16` (chain/uncond/always/d0)
                                                                    └─ `draw17` (chain/uncond/always/d0)
                                                                        └─ `draw18` (chain/uncond/always/d0)
                                                                            └─ `draw19` (chain/uncond/always/d0)
                                                                                └─ `draw20` (chain/uncond/always/d0)
                                                                                    └─ `draw21` (chain/uncond/always/d0)
                                                                                        └─ `draw22` (chain/uncond/always/d0)
                                                                                            └─ `draw23` (chain/uncond/always/d0)
                                                                                                └─ `draw24` (chain/uncond/always/d0)
                                                                                                    └─ `draw25` (chain/uncond/always/d0)
                                                                                                        └─ `draw26` (chain/uncond/always/d0)
                                                                                                            └─ `draw27` (chain/uncond/always/d0)
                                                                                                                └─ `draw28` (chain/uncond/always/d0)
                                                                                                                    └─ `draw29` (chain/uncond/always/d0)
                                                                                                                        └─ `draw30` (chain/uncond/always/d0)
                                                                                                                            └─ `draw31` (chain/uncond/always/d0)
                                                                                                                                └─ `draw32` (chain/uncond/always/d0)
                                                                                                                                    └─ `draw33` (chain/uncond/always/d0)
                                                                                                                                        └─ `draw34` (chain/uncond/always/d0)
                                                                                                                                            └─ `draw35` (chain/uncond/always/d0)
                                                                                                                                                └─ `draw36` (chain/uncond/always/d0)
                                                                                                                                                    └─ `draw37` (chain/uncond/always/d0)
                                                                                                                                                        └─ `draw38` (chain/uncond/always/d0)
                                                                                                                                                            └─ `draw39` (chain/uncond/always/d0)
                                                                                                                                                                └─ `draw40` (chain/uncond/always/d0)
                                                                                                                                                                    └─ `draw41` (chain/uncond/always/d0)
                                                                                                                                                                        └─ `draw42` (chain/uncond/always/d0)
                                                                                                                                                                            └─ `draw43` (chain/uncond/always/d0)
                                                                                                                                                                                └─ `draw44` (chain/uncond/always/d0)
                                                                                                                                                                                    └─ `draw45` (chain/uncond/always/d0)
                                                                                                                                                                                        └─ `draw46` (chain/uncond/always/d0)
                                                                                                                                                                                            └─ `draw47` (chain/uncond/always/d0)
                                                                                                                                                                                                └─ `draw48` (chain/uncond/always/d0)
                                                                                                                                                                                                    └─ `draw49` (chain/uncond/always/d0)
                                                                                                                                                                                                        └─ `draw50` (chain/uncond/always/d0)
                                                                                                                                                                                                            └─ `draw51` (chain/uncond/always/d0)
                                                                                                                                                                                                                └─ `draw52` (chain/uncond/always/d0)
                                                                                                                                                                                                                    └─ `draw53` (chain/uncond/always/d0)
                                                                                                                                                                                                                        └─ `draw54` (chain/uncond/always/d0)
                                                                                                                                                                                                                            └─ `draw55` (chain/uncond/always/d0)
                                                                                                                                                                                                                                └─ `draw56` (chain/uncond/always/d0)
                                                                                                                                                                                                                                    └─ `draw57` (chain/uncond/always/d0)
                                                                                                                                                                                                                                        └─ `draw58` (chain/uncond/always/d0)
                                                                                                                                                                                                                                            └─ `draw59` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                └─ `draw60` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                    └─ `draw61` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                        └─ `draw62` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                            └─ `draw63` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                └─ `draw64` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                    └─ `draw65` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                        └─ `draw66` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                            └─ `draw67` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                └─ `draw68` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                    └─ `draw69` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                        └─ `draw70` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                            └─ `draw71` (chain/uncond/always/d0)
                                                                                                                                                                                                                                                                                                └─ `draw72` (chain/uncond/always/d0)


## Build sheet

| # | id | type | condition | redstone | delay | next | command |
|---|---|---|---|---|---|---|---|
| 1 | `boot00` | impulse | unconditional | needs_redstone | 0 | `boot01` | `setblock 0 64 0 air` |
| 2 | `boot01` | chain | unconditional | always_active | 0 | `boot02` | `scoreboard objectives add ctl dummy` |
| 3 | `boot02` | chain | unconditional | always_active | 0 | `boot03` | `scoreboard objectives add nz dummy` |
| 4 | `boot03` | chain | unconditional | always_active | 0 | `boot04` | `scoreboard objectives add px dummy` |
| 5 | `boot04` | chain | unconditional | always_active | 0 | `boot05` | `scoreboard objectives add pz dummy` |
| 6 | `boot05` | chain | unconditional | always_active | 0 | `boot06` | `scoreboard objectives add hgt dummy` |
| 7 | `boot06` | chain | unconditional | always_active | 0 | `boot07` | `scoreboard objectives add u dummy` |
| 8 | `boot07` | chain | unconditional | always_active | 0 | `boot08` | `scoreboard objectives add ix dummy` |
| 9 | `boot08` | chain | unconditional | always_active | 0 | `boot09` | `scoreboard objectives add fx dummy` |
| 10 | `boot09` | chain | unconditional | always_active | 0 | `boot10` | `scoreboard objectives add fx2 dummy` |
| 11 | `boot10` | chain | unconditional | always_active | 0 | `boot11` | `scoreboard objectives add iz dummy` |
| 12 | `boot11` | chain | unconditional | always_active | 0 | `boot12` | `scoreboard objectives add fz dummy` |
| 13 | `boot12` | chain | unconditional | always_active | 0 | `boot13` | `scoreboard objectives add fz2 dummy` |
| 14 | `boot13` | chain | unconditional | always_active | 0 | `boot14` | `scoreboard objectives add base dummy` |
| 15 | `boot14` | chain | unconditional | always_active | 0 | `boot15` | `scoreboard objectives add hh dummy` |
| 16 | `boot15` | chain | unconditional | always_active | 0 | `boot16` | `scoreboard objectives add bi dummy` |
| 17 | `boot16` | chain | unconditional | always_active | 0 | `boot17` | `scoreboard objectives add acc dummy` |
| 18 | `boot17` | chain | unconditional | always_active | 0 | `boot18` | `scoreboard objectives add cnt dummy` |
| 19 | `boot18` | chain | unconditional | always_active | 0 | `boot19` | `scoreboard players set k1 nz 1` |
| 20 | `boot19` | chain | unconditional | always_active | 0 | `boot20` | `scoreboard players set k2 nz 2` |
| 21 | `boot20` | chain | unconditional | always_active | 0 | `boot21` | `scoreboard players set k4 nz 4` |
| 22 | `boot21` | chain | unconditional | always_active | 0 | `boot22` | `scoreboard players set k65536 nz 65536` |
| 23 | `boot22` | chain | unconditional | always_active | 0 | `boot23` | `scoreboard players set k251 nz 251` |
| 24 | `boot23` | chain | unconditional | always_active | 0 | `boot24` | `scoreboard players set k127 nz 127` |
| 25 | `boot24` | chain | unconditional | always_active | 0 | `boot25` | `scoreboard players set k311 nz 311` |
| 26 | `boot25` | chain | unconditional | always_active | 0 | `boot26` | `scoreboard players set kbias nz 625` |
| 27 | `boot26` | chain | unconditional | always_active | 0 | `boot27` | `scoreboard players set kdiv nz 30` |
| 28 | `boot27` | chain | unconditional | always_active | 0 | `boot28` | `scoreboard players set kmidraw nz 38` |
| 29 | `boot28` | chain | unconditional | always_active | 0 | `boot29` | `scoreboard players set koffraw nz 28` |
| 30 | `boot29` | chain | unconditional | always_active | 0 | `boot30` | `scoreboard players set ksalty nz 20000` |
| 31 | `boot30` | chain | unconditional | always_active | 0 | `boot31` | `scoreboard players set ko1 nz 127` |
| 32 | `boot31` | chain | unconditional | always_active | 0 | `boot32` | `scoreboard players set ko2 nz 311` |
| 33 | `boot32` | chain | unconditional | always_active | 0 | `boot33` | `scoreboard players set ko3 nz 438` |
| 34 | `boot33` | chain | unconditional | always_active | 0 | `boot34` | `scoreboard players set kd1 nz 8` |
| 35 | `boot34` | chain | unconditional | always_active | 0 | `boot35` | `scoreboard players set kl1 nz 32` |
| 36 | `boot35` | chain | unconditional | always_active | 0 | `boot36` | `scoreboard players set ks1 nz 11` |
| 37 | `boot36` | chain | unconditional | always_active | 0 | `boot37` | `scoreboard players set ka1 nz 2` |
| 38 | `boot37` | chain | unconditional | always_active | 0 | `boot38` | `scoreboard players set kox1 nz 2` |
| 39 | `boot38` | chain | unconditional | always_active | 0 | `boot39` | `scoreboard players set koz1 nz 1` |
| 40 | `boot39` | chain | unconditional | always_active | 0 | `boot40` | `scoreboard players set kd2 nz 4` |
| 41 | `boot40` | chain | unconditional | always_active | 0 | `boot41` | `scoreboard players set kl2 nz 64` |
| 42 | `boot41` | chain | unconditional | always_active | 0 | `boot42` | `scoreboard players set ks2 nz 47` |
| 43 | `boot42` | chain | unconditional | always_active | 0 | `boot43` | `scoreboard players set ka2 nz 2` |
| 44 | `boot43` | chain | unconditional | always_active | 0 | `boot44` | `scoreboard players set kd3 nz 2` |
| 45 | `boot44` | chain | unconditional | always_active | 0 | `boot45` | `scoreboard players set kl3 nz 128` |
| 46 | `boot45` | chain | unconditional | always_active | 0 | `boot46` | `scoreboard players set ks3 nz 83` |
| 47 | `boot46` | chain | unconditional | always_active | 0 | `boot47` | `kill @e[tag=nt_col]` |
| 48 | `boot47` | chain | unconditional | always_active | 0 | `boot48` | `kill @e[tag=nt_cursor]` |
| 49 | `boot48` | chain | unconditional | always_active | 0 | `boot49` | `tickingarea remove noise` |
| 50 | `boot49` | chain | unconditional | always_active | 0 | `boot50` | `tickingarea add 0 60 0 31 104 59 noise` |
| 51 | `boot50` | chain | unconditional | always_active | 0 | `boot51` | `scoreboard players add fb_seed nz 1` |
| 52 | `boot51` | chain | unconditional | always_active | 0 | `boot52` | `scoreboard players operation fb_seed nz %= ksalty nz` |
| 53 | `boot52` | chain | unconditional | always_active | 0 | `boot53` | `scoreboard players random fb_seed nz 0 20000` |
| 54 | `boot53` | chain | unconditional | always_active | 0 | `boot54` | `scoreboard players set bn2 ctl 0` |
| 55 | `boot54` | chain | unconditional | always_active | 0 | `boot55` | `scoreboard players set bn3 ctl 0` |
| 56 | `boot55` | chain | unconditional | always_active | 0 | `boot56` | `scoreboard players set bn4 ctl 0` |
| 57 | `boot56` | chain | unconditional | always_active | 0 | `boot57` | `scoreboard players set bn5 ctl 0` |
| 58 | `boot57` | chain | unconditional | always_active | 0 | `boot58` | `scoreboard players set bn6 ctl 0` |
| 59 | `boot58` | chain | unconditional | always_active | 0 | `boot59` | `scoreboard players set bn7 ctl 0` |
| 60 | `boot59` | chain | unconditional | always_active | 0 | `boot60` | `scoreboard players set bn8 ctl 0` |
| 61 | `boot60` | chain | unconditional | always_active | 0 | `boot61` | `scoreboard players set bn9 ctl 0` |
| 62 | `boot61` | chain | unconditional | always_active | 0 | `boot62` | `scoreboard players set bn10 ctl 0` |
| 63 | `boot62` | chain | unconditional | always_active | 0 | `boot63` | `scoreboard players set bn11 ctl 0` |
| 64 | `boot63` | chain | unconditional | always_active | 0 | `boot64` | `scoreboard players set bn12 ctl 0` |
| 65 | `boot64` | chain | unconditional | always_active | 0 | `boot65` | `scoreboard players set bn13 ctl 0` |
| 66 | `boot65` | chain | unconditional | always_active | 0 | `boot66` | `scoreboard players set bn14 ctl 0` |
| 67 | `boot66` | chain | unconditional | always_active | 0 | `boot67` | `scoreboard players set bn15 ctl 0` |
| 68 | `boot67` | chain | unconditional | always_active | 0 | `boot68` | `scoreboard players set bn16 ctl 0` |
| 69 | `boot68` | chain | unconditional | always_active | 0 | `boot69` | `scoreboard players set bn17 ctl 0` |
| 70 | `boot69` | chain | unconditional | always_active | 0 | `boot70` | `scoreboard players set bn18 ctl 0` |
| 71 | `boot70` | chain | unconditional | always_active | 0 | `boot71` | `scoreboard players set fb_cx ctl 0` |
| 72 | `boot71` | chain | unconditional | always_active | 0 | `boot72` | `scoreboard players set fb_cz ctl 0` |
| 73 | `boot72` | chain | unconditional | always_active | 0 | `boot73` | `scoreboard players set fb_n ctl 0` |
| 74 | `boot73` | chain | unconditional | always_active | 0 | `boot74` | `scoreboard players set fb_b ctl 0` |
| 75 | `boot74` | chain | unconditional | always_active | 0 | `boot75` | `scoreboard players set fb_t ctl 0` |
| 76 | `boot75` | chain | unconditional | always_active | 0 | `boot76` | `scoreboard players set fb_cur ctl 0` |
| 77 | `boot76` | chain | unconditional | always_active | 0 | `boot77` | `scoreboard players set fb_state ctl 10` |
| 78 | `boot77` | chain | unconditional | always_active | 0 | — | `tellraw @a {"rawtext":[{"text":"§e值噪声 fBm 启动 §7\| 种子 "},{"score":{"name":"fb_seed","objective":"nz"}},{"text":" §7\| 32×32 扫描"}]}` |
| 79 | `prep00` | repeat | unconditional | always_active | 2 | `prep01` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 80 | `prep01` | chain | unconditional | always_active | 0 | `prep02` | `execute if score fb_cur ctl matches 10 run fill 0 64 24 31 64 55 minecraft:stone` |
| 81 | `prep02` | chain | unconditional | always_active | 0 | `prep03` | `execute if score fb_cur ctl matches 10 run fill 0 65 24 31 84 55 air` |
| 82 | `prep03` | chain | unconditional | always_active | 0 | `prep04` | `execute if score fb_cur ctl matches 10 run kill @e[tag=nt_col]` |
| 83 | `prep04` | chain | unconditional | always_active | 0 | `prep05` | `execute if score fb_cur ctl matches 10 run kill @e[tag=nt_cursor]` |
| 84 | `prep05` | chain | unconditional | always_active | 0 | `prep06` | `execute if score fb_cur ctl matches 10 run summon armor_stand 1 65 25` |
| 85 | `prep06` | chain | unconditional | always_active | 0 | `prep07` | `execute if score fb_cur ctl matches 10 positioned 1 65 25 run tag @e[type=armor_stand,r=0.6] add nt_cursor` |
| 86 | `prep07` | chain | unconditional | always_active | 0 | `prep08` | `execute if score fb_cur ctl matches 10 run effect @e[tag=nt_cursor] invisibility 999999 0 true` |
| 87 | `prep08` | chain | unconditional | always_active | 0 | `prep09` | `execute if score fb_cur ctl matches 10 run scoreboard players set fb_cx ctl 0` |
| 88 | `prep09` | chain | unconditional | always_active | 0 | `prep10` | `execute if score fb_cur ctl matches 10 run scoreboard players set fb_cz ctl 0` |
| 89 | `prep10` | chain | unconditional | always_active | 0 | `prep11` | `execute if score fb_cur ctl matches 10 run scoreboard players set fb_n ctl 0` |
| 90 | `prep11` | chain | unconditional | always_active | 0 | `prep12` | `execute if score fb_cur ctl matches 10 run scoreboard players set fb_b ctl 0` |
| 91 | `prep12` | chain | unconditional | always_active | 0 | `prep13` | `execute if score fb_cur ctl matches 10 run scoreboard players set fb_state ctl 1` |
| 92 | `prep13` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 10 run titleraw @a actionbar {"rawtext":[{"text":"§b值噪声 fBm §7· 扫描 256 格"}]}` |
| 93 | `grid00` | repeat | unconditional | always_active | 1 | `grid01` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 94 | `grid01` | chain | unconditional | always_active | 0 | `grid02` | `execute if score fb_cur ctl matches 1 as @e[tag=nt_cursor] at @s run summon armor_stand ~ ~ ~` |
| 95 | `grid02` | chain | unconditional | always_active | 0 | `grid03` | `execute if score fb_cur ctl matches 1 as @e[tag=nt_cursor] at @s run tag @e[type=armor_stand,r=0.6,tag=!nt_cursor] add nt_col` |
| 96 | `grid03` | chain | unconditional | always_active | 0 | `grid04` | `execute if score fb_cur ctl matches 1 as @e[tag=nt_cursor] at @s positioned ~2 ~ ~ run summon armor_stand ~ ~ ~` |
| 97 | `grid04` | chain | unconditional | always_active | 0 | `grid05` | `execute if score fb_cur ctl matches 1 as @e[tag=nt_cursor] at @s positioned ~2 ~ ~ run tag @e[type=armor_stand,r=0.6,tag=!nt_cursor] add nt_col` |
| 98 | `grid05` | chain | unconditional | always_active | 0 | `grid06` | `execute if score fb_cur ctl matches 1 run scoreboard players operation fb_t ctl = fb_cx ctl` |
| 99 | `grid06` | chain | unconditional | always_active | 0 | `grid07` | `execute if score fb_cur ctl matches 1 run scoreboard players operation fb_t ctl *= k4 nz` |
| 100 | `grid07` | chain | unconditional | always_active | 0 | `grid08` | `execute if score fb_cur ctl matches 1 run scoreboard players operation fb_t ctl += k1 nz` |
| 101 | `grid08` | chain | unconditional | always_active | 0 | `grid09` | `execute if score fb_cur ctl matches 1 as @e[tag=nt_cursor] at @s run scoreboard players operation @e[tag=nt_col,r=0.6,c=1] px = fb_t ctl` |
| 102 | `grid09` | chain | unconditional | always_active | 0 | `grid10` | `execute if score fb_cur ctl matches 1 run scoreboard players operation fb_t ctl += k2 nz` |
| 103 | `grid10` | chain | unconditional | always_active | 0 | `grid11` | `execute if score fb_cur ctl matches 1 as @e[tag=nt_cursor] at @s positioned ~2 ~ ~ run scoreboard players operation @e[tag=nt_col,r=0.6,c=1] px = fb_t ctl` |
| 104 | `grid11` | chain | unconditional | always_active | 0 | `grid12` | `execute if score fb_cur ctl matches 1 run scoreboard players operation fb_t ctl = fb_cz ctl` |
| 105 | `grid12` | chain | unconditional | always_active | 0 | `grid13` | `execute if score fb_cur ctl matches 1 run scoreboard players operation fb_t ctl *= k2 nz` |
| 106 | `grid13` | chain | unconditional | always_active | 0 | `grid14` | `execute if score fb_cur ctl matches 1 run scoreboard players operation fb_t ctl += k1 nz` |
| 107 | `grid14` | chain | unconditional | always_active | 0 | `grid15` | `execute if score fb_cur ctl matches 1 as @e[tag=nt_cursor] at @s run scoreboard players operation @e[tag=nt_col,r=0.6,c=1] pz = fb_t ctl` |
| 108 | `grid15` | chain | unconditional | always_active | 0 | `grid16` | `execute if score fb_cur ctl matches 1 as @e[tag=nt_cursor] at @s positioned ~2 ~ ~ run scoreboard players operation @e[tag=nt_col,r=0.6,c=1] pz = fb_t ctl` |
| 109 | `grid16` | chain | unconditional | always_active | 0 | `grid17` | `execute if score fb_cur ctl matches 1 run scoreboard players add fb_n ctl 2` |
| 110 | `grid17` | chain | unconditional | always_active | 0 | `grid18` | `execute if score fb_cur ctl matches 1 run scoreboard players add fb_cx ctl 1` |
| 111 | `grid18` | chain | unconditional | always_active | 0 | `grid19` | `execute if score fb_cur ctl matches 1 if score fb_cx ctl matches 8.. run scoreboard players set fb_cx ctl 0` |
| 112 | `grid19` | chain | unconditional | always_active | 0 | `grid20` | `execute if score fb_cur ctl matches 1 if score fb_cx ctl matches 0 as @e[tag=nt_cursor] at @s run tp @s ~-28 ~ ~2` |
| 113 | `grid20` | chain | unconditional | always_active | 0 | `grid21` | `execute if score fb_cur ctl matches 1 if score fb_cx ctl matches 0 run scoreboard players add fb_cz ctl 1` |
| 114 | `grid21` | chain | unconditional | always_active | 0 | `grid22` | `execute if score fb_cur ctl matches 1 if score fb_cx ctl matches 1.. as @e[tag=nt_cursor] at @s run tp @s ~4 ~ ~` |
| 115 | `grid22` | chain | unconditional | always_active | 0 | `grid23` | `execute if score fb_cur ctl matches 1 if score fb_n ctl matches 256.. run scoreboard players set fb_state ctl 2` |
| 116 | `grid23` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 1 if score fb_n ctl matches 256.. run titleraw @a actionbar {"rawtext":[{"text":"§b值噪声 fBm §7· 计算高度"}]}` |
| 117 | `calc100` | repeat | unconditional | always_active | 0 | `calc101` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 118 | `calc101` | chain | unconditional | always_active | 0 | `calc102` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players set @s acc 0` |
| 119 | `calc102` | chain | unconditional | always_active | 0 | `calc103` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s ix = @s px` |
| 120 | `calc103` | chain | unconditional | always_active | 0 | `calc104` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s ix += kox1 nz` |
| 121 | `calc104` | chain | unconditional | always_active | 0 | `calc105` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s ix /= kd1 nz` |
| 122 | `calc105` | chain | unconditional | always_active | 0 | `calc106` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx = @s px` |
| 123 | `calc106` | chain | unconditional | always_active | 0 | `calc107` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx += kox1 nz` |
| 124 | `calc107` | chain | unconditional | always_active | 0 | `calc108` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx %= kd1 nz` |
| 125 | `calc108` | chain | unconditional | always_active | 0 | `calc109` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx *= kl1 nz` |
| 126 | `calc109` | chain | unconditional | always_active | 0 | `calc110` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players set @s fx2 256` |
| 127 | `calc110` | chain | unconditional | always_active | 0 | `calc111` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx2 -= @s fx` |
| 128 | `calc111` | chain | unconditional | always_active | 0 | `calc112` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s iz = @s pz` |
| 129 | `calc112` | chain | unconditional | always_active | 0 | `calc113` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s iz += koz1 nz` |
| 130 | `calc113` | chain | unconditional | always_active | 0 | `calc114` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s iz /= kd1 nz` |
| 131 | `calc114` | chain | unconditional | always_active | 0 | `calc115` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz = @s pz` |
| 132 | `calc115` | chain | unconditional | always_active | 0 | `calc116` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz += koz1 nz` |
| 133 | `calc116` | chain | unconditional | always_active | 0 | `calc117` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz %= kd1 nz` |
| 134 | `calc117` | chain | unconditional | always_active | 0 | `calc118` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz *= kl1 nz` |
| 135 | `calc118` | chain | unconditional | always_active | 0 | `calc119` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players set @s fz2 256` |
| 136 | `calc119` | chain | unconditional | always_active | 0 | `calc120` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz2 -= @s fz` |
| 137 | `calc120` | chain | unconditional | always_active | 0 | `calc121` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s base = @s ix` |
| 138 | `calc121` | chain | unconditional | always_active | 0 | `calc122` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s base *= k127 nz` |
| 139 | `calc122` | chain | unconditional | always_active | 0 | `calc123` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s u = @s iz` |
| 140 | `calc123` | chain | unconditional | always_active | 0 | `calc124` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s u *= k311 nz` |
| 141 | `calc124` | chain | unconditional | always_active | 0 | `calc125` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s base += @s u` |
| 142 | `calc125` | chain | unconditional | always_active | 0 | `calc126` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s base += ks1 nz` |
| 143 | `calc126` | chain | unconditional | always_active | 0 | `calc127` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s base += fb_seed nz` |
| 144 | `calc127` | chain | unconditional | always_active | 0 | `calc128` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 145 | `calc128` | chain | unconditional | always_active | 0 | `calc129` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 146 | `calc129` | chain | unconditional | always_active | 0 | `calc130` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 147 | `calc130` | chain | unconditional | always_active | 0 | `calc131` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 148 | `calc131` | chain | unconditional | always_active | 0 | `calc132` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 149 | `calc132` | chain | unconditional | always_active | 0 | `calc133` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx2` |
| 150 | `calc133` | chain | unconditional | always_active | 0 | `calc134` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz2` |
| 151 | `calc134` | chain | unconditional | always_active | 0 | `calc135` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s bi = @s hh` |
| 152 | `calc135` | chain | unconditional | always_active | 0 | `calc136` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 153 | `calc136` | chain | unconditional | always_active | 0 | `calc137` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh += ko1 nz` |
| 154 | `calc137` | chain | unconditional | always_active | 0 | `calc138` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 155 | `calc138` | chain | unconditional | always_active | 0 | `calc139` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 156 | `calc139` | chain | unconditional | always_active | 0 | `calc140` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 157 | `calc140` | chain | unconditional | always_active | 0 | `calc141` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 158 | `calc141` | chain | unconditional | always_active | 0 | `calc142` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx` |
| 159 | `calc142` | chain | unconditional | always_active | 0 | `calc143` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz2` |
| 160 | `calc143` | chain | unconditional | always_active | 0 | `calc144` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 161 | `calc144` | chain | unconditional | always_active | 0 | `calc145` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 162 | `calc145` | chain | unconditional | always_active | 0 | `calc146` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh += ko2 nz` |
| 163 | `calc146` | chain | unconditional | always_active | 0 | `calc147` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 164 | `calc147` | chain | unconditional | always_active | 0 | `calc148` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 165 | `calc148` | chain | unconditional | always_active | 0 | `calc149` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 166 | `calc149` | chain | unconditional | always_active | 0 | `calc150` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 167 | `calc150` | chain | unconditional | always_active | 0 | `calc151` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx2` |
| 168 | `calc151` | chain | unconditional | always_active | 0 | `calc152` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz` |
| 169 | `calc152` | chain | unconditional | always_active | 0 | `calc153` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 170 | `calc153` | chain | unconditional | always_active | 0 | `calc154` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 171 | `calc154` | chain | unconditional | always_active | 0 | `calc155` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh += ko3 nz` |
| 172 | `calc155` | chain | unconditional | always_active | 0 | `calc156` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 173 | `calc156` | chain | unconditional | always_active | 0 | `calc157` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 174 | `calc157` | chain | unconditional | always_active | 0 | `calc158` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 175 | `calc158` | chain | unconditional | always_active | 0 | `calc159` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 176 | `calc159` | chain | unconditional | always_active | 0 | `calc160` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx` |
| 177 | `calc160` | chain | unconditional | always_active | 0 | `calc161` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz` |
| 178 | `calc161` | chain | unconditional | always_active | 0 | `calc162` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 179 | `calc162` | chain | unconditional | always_active | 0 | `calc163` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s bi /= k65536 nz` |
| 180 | `calc163` | chain | unconditional | always_active | 0 | `calc164` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s bi *= ka1 nz` |
| 181 | `calc164` | chain | unconditional | always_active | 0 | `calc165` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s acc += @s bi` |
| 182 | `calc165` | chain | unconditional | always_active | 0 | `calc166` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s ix = @s px` |
| 183 | `calc166` | chain | unconditional | always_active | 0 | `calc167` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s ix /= kd2 nz` |
| 184 | `calc167` | chain | unconditional | always_active | 0 | `calc168` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx = @s px` |
| 185 | `calc168` | chain | unconditional | always_active | 0 | `calc169` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx %= kd2 nz` |
| 186 | `calc169` | chain | unconditional | always_active | 0 | `calc170` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx *= kl2 nz` |
| 187 | `calc170` | chain | unconditional | always_active | 0 | `calc171` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players set @s fx2 256` |
| 188 | `calc171` | chain | unconditional | always_active | 0 | `calc172` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fx2 -= @s fx` |
| 189 | `calc172` | chain | unconditional | always_active | 0 | `calc173` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s iz = @s pz` |
| 190 | `calc173` | chain | unconditional | always_active | 0 | `calc174` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s iz /= kd2 nz` |
| 191 | `calc174` | chain | unconditional | always_active | 0 | `calc175` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz = @s pz` |
| 192 | `calc175` | chain | unconditional | always_active | 0 | `calc176` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz %= kd2 nz` |
| 193 | `calc176` | chain | unconditional | always_active | 0 | `calc177` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz *= kl2 nz` |
| 194 | `calc177` | chain | unconditional | always_active | 0 | `calc178` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players set @s fz2 256` |
| 195 | `calc178` | chain | unconditional | always_active | 0 | `calc179` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s fz2 -= @s fz` |
| 196 | `calc179` | chain | unconditional | always_active | 0 | `calc180` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s base = @s ix` |
| 197 | `calc180` | chain | unconditional | always_active | 0 | `calc181` | `execute if score fb_cur ctl matches 2 as @e[tag=nt_col] run scoreboard players operation @s base *= k127 nz` |
| 198 | `calc181` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 2 run scoreboard players set fb_state ctl 3` |
| 199 | `calc200` | repeat | unconditional | always_active | 0 | `calc201` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 200 | `calc201` | chain | unconditional | always_active | 0 | `calc202` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u = @s iz` |
| 201 | `calc202` | chain | unconditional | always_active | 0 | `calc203` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u *= k311 nz` |
| 202 | `calc203` | chain | unconditional | always_active | 0 | `calc204` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s base += @s u` |
| 203 | `calc204` | chain | unconditional | always_active | 0 | `calc205` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s base += ks2 nz` |
| 204 | `calc205` | chain | unconditional | always_active | 0 | `calc206` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s base += fb_seed nz` |
| 205 | `calc206` | chain | unconditional | always_active | 0 | `calc207` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 206 | `calc207` | chain | unconditional | always_active | 0 | `calc208` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 207 | `calc208` | chain | unconditional | always_active | 0 | `calc209` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 208 | `calc209` | chain | unconditional | always_active | 0 | `calc210` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 209 | `calc210` | chain | unconditional | always_active | 0 | `calc211` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 210 | `calc211` | chain | unconditional | always_active | 0 | `calc212` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx2` |
| 211 | `calc212` | chain | unconditional | always_active | 0 | `calc213` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz2` |
| 212 | `calc213` | chain | unconditional | always_active | 0 | `calc214` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s bi = @s hh` |
| 213 | `calc214` | chain | unconditional | always_active | 0 | `calc215` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 214 | `calc215` | chain | unconditional | always_active | 0 | `calc216` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh += ko1 nz` |
| 215 | `calc216` | chain | unconditional | always_active | 0 | `calc217` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 216 | `calc217` | chain | unconditional | always_active | 0 | `calc218` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 217 | `calc218` | chain | unconditional | always_active | 0 | `calc219` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 218 | `calc219` | chain | unconditional | always_active | 0 | `calc220` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 219 | `calc220` | chain | unconditional | always_active | 0 | `calc221` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx` |
| 220 | `calc221` | chain | unconditional | always_active | 0 | `calc222` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz2` |
| 221 | `calc222` | chain | unconditional | always_active | 0 | `calc223` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 222 | `calc223` | chain | unconditional | always_active | 0 | `calc224` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 223 | `calc224` | chain | unconditional | always_active | 0 | `calc225` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh += ko2 nz` |
| 224 | `calc225` | chain | unconditional | always_active | 0 | `calc226` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 225 | `calc226` | chain | unconditional | always_active | 0 | `calc227` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 226 | `calc227` | chain | unconditional | always_active | 0 | `calc228` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 227 | `calc228` | chain | unconditional | always_active | 0 | `calc229` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 228 | `calc229` | chain | unconditional | always_active | 0 | `calc230` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx2` |
| 229 | `calc230` | chain | unconditional | always_active | 0 | `calc231` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz` |
| 230 | `calc231` | chain | unconditional | always_active | 0 | `calc232` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 231 | `calc232` | chain | unconditional | always_active | 0 | `calc233` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 232 | `calc233` | chain | unconditional | always_active | 0 | `calc234` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh += ko3 nz` |
| 233 | `calc234` | chain | unconditional | always_active | 0 | `calc235` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 234 | `calc235` | chain | unconditional | always_active | 0 | `calc236` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 235 | `calc236` | chain | unconditional | always_active | 0 | `calc237` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 236 | `calc237` | chain | unconditional | always_active | 0 | `calc238` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 237 | `calc238` | chain | unconditional | always_active | 0 | `calc239` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx` |
| 238 | `calc239` | chain | unconditional | always_active | 0 | `calc240` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz` |
| 239 | `calc240` | chain | unconditional | always_active | 0 | `calc241` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 240 | `calc241` | chain | unconditional | always_active | 0 | `calc242` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s bi /= k65536 nz` |
| 241 | `calc242` | chain | unconditional | always_active | 0 | `calc243` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s bi *= ka2 nz` |
| 242 | `calc243` | chain | unconditional | always_active | 0 | `calc244` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s acc += @s bi` |
| 243 | `calc244` | chain | unconditional | always_active | 0 | `calc245` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s ix = @s px` |
| 244 | `calc245` | chain | unconditional | always_active | 0 | `calc246` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s ix /= kd3 nz` |
| 245 | `calc246` | chain | unconditional | always_active | 0 | `calc247` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s fx = @s px` |
| 246 | `calc247` | chain | unconditional | always_active | 0 | `calc248` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s fx %= kd3 nz` |
| 247 | `calc248` | chain | unconditional | always_active | 0 | `calc249` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s fx *= kl3 nz` |
| 248 | `calc249` | chain | unconditional | always_active | 0 | `calc250` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players set @s fx2 256` |
| 249 | `calc250` | chain | unconditional | always_active | 0 | `calc251` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s fx2 -= @s fx` |
| 250 | `calc251` | chain | unconditional | always_active | 0 | `calc252` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s iz = @s pz` |
| 251 | `calc252` | chain | unconditional | always_active | 0 | `calc253` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s iz /= kd3 nz` |
| 252 | `calc253` | chain | unconditional | always_active | 0 | `calc254` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s fz = @s pz` |
| 253 | `calc254` | chain | unconditional | always_active | 0 | `calc255` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s fz %= kd3 nz` |
| 254 | `calc255` | chain | unconditional | always_active | 0 | `calc256` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s fz *= kl3 nz` |
| 255 | `calc256` | chain | unconditional | always_active | 0 | `calc257` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players set @s fz2 256` |
| 256 | `calc257` | chain | unconditional | always_active | 0 | `calc258` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s fz2 -= @s fz` |
| 257 | `calc258` | chain | unconditional | always_active | 0 | `calc259` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s base = @s ix` |
| 258 | `calc259` | chain | unconditional | always_active | 0 | `calc260` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s base *= k127 nz` |
| 259 | `calc260` | chain | unconditional | always_active | 0 | `calc261` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u = @s iz` |
| 260 | `calc261` | chain | unconditional | always_active | 0 | `calc262` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u *= k311 nz` |
| 261 | `calc262` | chain | unconditional | always_active | 0 | `calc263` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s base += @s u` |
| 262 | `calc263` | chain | unconditional | always_active | 0 | `calc264` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s base += ks3 nz` |
| 263 | `calc264` | chain | unconditional | always_active | 0 | `calc265` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s base += fb_seed nz` |
| 264 | `calc265` | chain | unconditional | always_active | 0 | `calc266` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 265 | `calc266` | chain | unconditional | always_active | 0 | `calc267` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 266 | `calc267` | chain | unconditional | always_active | 0 | `calc268` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 267 | `calc268` | chain | unconditional | always_active | 0 | `calc269` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 268 | `calc269` | chain | unconditional | always_active | 0 | `calc270` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 269 | `calc270` | chain | unconditional | always_active | 0 | `calc271` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx2` |
| 270 | `calc271` | chain | unconditional | always_active | 0 | `calc272` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz2` |
| 271 | `calc272` | chain | unconditional | always_active | 0 | `calc273` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s bi = @s hh` |
| 272 | `calc273` | chain | unconditional | always_active | 0 | `calc274` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 273 | `calc274` | chain | unconditional | always_active | 0 | `calc275` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh += ko1 nz` |
| 274 | `calc275` | chain | unconditional | always_active | 0 | `calc276` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 275 | `calc276` | chain | unconditional | always_active | 0 | `calc277` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 276 | `calc277` | chain | unconditional | always_active | 0 | `calc278` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 277 | `calc278` | chain | unconditional | always_active | 0 | `calc279` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 278 | `calc279` | chain | unconditional | always_active | 0 | `calc280` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx` |
| 279 | `calc280` | chain | unconditional | always_active | 0 | `calc281` | `execute if score fb_cur ctl matches 3 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz2` |
| 280 | `calc281` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 3 run scoreboard players set fb_state ctl 4` |
| 281 | `calc300` | repeat | unconditional | always_active | 0 | `calc301` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 282 | `calc301` | chain | unconditional | always_active | 0 | `calc302` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 283 | `calc302` | chain | unconditional | always_active | 0 | `calc303` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 284 | `calc303` | chain | unconditional | always_active | 0 | `calc304` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh += ko2 nz` |
| 285 | `calc304` | chain | unconditional | always_active | 0 | `calc305` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 286 | `calc305` | chain | unconditional | always_active | 0 | `calc306` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 287 | `calc306` | chain | unconditional | always_active | 0 | `calc307` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 288 | `calc307` | chain | unconditional | always_active | 0 | `calc308` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 289 | `calc308` | chain | unconditional | always_active | 0 | `calc309` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx2` |
| 290 | `calc309` | chain | unconditional | always_active | 0 | `calc310` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz` |
| 291 | `calc310` | chain | unconditional | always_active | 0 | `calc311` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 292 | `calc311` | chain | unconditional | always_active | 0 | `calc312` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh = @s base` |
| 293 | `calc312` | chain | unconditional | always_active | 0 | `calc313` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh += ko3 nz` |
| 294 | `calc313` | chain | unconditional | always_active | 0 | `calc314` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s u = @s hh` |
| 295 | `calc314` | chain | unconditional | always_active | 0 | `calc315` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players add @s u 1` |
| 296 | `calc315` | chain | unconditional | always_active | 0 | `calc316` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s u` |
| 297 | `calc316` | chain | unconditional | always_active | 0 | `calc317` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh %= k251 nz` |
| 298 | `calc317` | chain | unconditional | always_active | 0 | `calc318` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fx` |
| 299 | `calc318` | chain | unconditional | always_active | 0 | `calc319` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hh *= @s fz` |
| 300 | `calc319` | chain | unconditional | always_active | 0 | `calc320` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s bi += @s hh` |
| 301 | `calc320` | chain | unconditional | always_active | 0 | `calc321` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s bi /= k65536 nz` |
| 302 | `calc321` | chain | unconditional | always_active | 0 | `calc322` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s acc += @s bi` |
| 303 | `calc322` | chain | unconditional | always_active | 0 | `calc323` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s acc -= kbias nz` |
| 304 | `calc323` | chain | unconditional | always_active | 0 | `calc324` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s acc /= kdiv nz` |
| 305 | `calc324` | chain | unconditional | always_active | 0 | `calc325` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s acc += kmidraw nz` |
| 306 | `calc325` | chain | unconditional | always_active | 0 | `calc326` | `execute if score fb_cur ctl matches 4 as @e[tag=nt_col] run scoreboard players operation @s hgt = @s acc` |
| 307 | `calc326` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 4 run scoreboard players set fb_state ctl 5` |
| 308 | `calc400` | repeat | unconditional | always_active | 0 | `calc401` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 309 | `calc401` | chain | unconditional | always_active | 0 | `calc402` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s run scoreboard players operation @s acc = @s hgt` |
| 310 | `calc402` | chain | unconditional | always_active | 0 | `calc403` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s run scoreboard players set @s cnt 1` |
| 311 | `calc403` | chain | unconditional | always_active | 0 | `calc404` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~-2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 312 | `calc404` | chain | unconditional | always_active | 0 | `calc405` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~-2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 313 | `calc405` | chain | unconditional | always_active | 0 | `calc406` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~-2 ~ ~0 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 314 | `calc406` | chain | unconditional | always_active | 0 | `calc407` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~-2 ~ ~0 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 315 | `calc407` | chain | unconditional | always_active | 0 | `calc408` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~-2 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 316 | `calc408` | chain | unconditional | always_active | 0 | `calc409` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~-2 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 317 | `calc409` | chain | unconditional | always_active | 0 | `calc410` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~0 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 318 | `calc410` | chain | unconditional | always_active | 0 | `calc411` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~0 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 319 | `calc411` | chain | unconditional | always_active | 0 | `calc412` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~0 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 320 | `calc412` | chain | unconditional | always_active | 0 | `calc413` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~0 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 321 | `calc413` | chain | unconditional | always_active | 0 | `calc414` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 322 | `calc414` | chain | unconditional | always_active | 0 | `calc415` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 323 | `calc415` | chain | unconditional | always_active | 0 | `calc416` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~2 ~ ~0 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 324 | `calc416` | chain | unconditional | always_active | 0 | `calc417` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~2 ~ ~0 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 325 | `calc417` | chain | unconditional | always_active | 0 | `calc418` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~2 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 326 | `calc418` | chain | unconditional | always_active | 0 | `calc419` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s positioned ~2 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 327 | `calc419` | chain | unconditional | always_active | 0 | `calc420` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s run scoreboard players operation @s acc /= @s cnt` |
| 328 | `calc420` | chain | unconditional | always_active | 0 | `calc421` | `execute if score fb_cur ctl matches 5 as @e[tag=nt_col] at @s run scoreboard players operation @s hgt = @s acc` |
| 329 | `calc421` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 5 run scoreboard players set fb_state ctl 6` |
| 330 | `calc500` | repeat | unconditional | always_active | 0 | `calc501` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 331 | `calc501` | chain | unconditional | always_active | 0 | `calc502` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s run scoreboard players operation @s acc = @s hgt` |
| 332 | `calc502` | chain | unconditional | always_active | 0 | `calc503` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s run scoreboard players set @s cnt 1` |
| 333 | `calc503` | chain | unconditional | always_active | 0 | `calc504` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~-2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 334 | `calc504` | chain | unconditional | always_active | 0 | `calc505` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~-2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 335 | `calc505` | chain | unconditional | always_active | 0 | `calc506` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~-2 ~ ~0 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 336 | `calc506` | chain | unconditional | always_active | 0 | `calc507` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~-2 ~ ~0 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 337 | `calc507` | chain | unconditional | always_active | 0 | `calc508` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~-2 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 338 | `calc508` | chain | unconditional | always_active | 0 | `calc509` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~-2 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 339 | `calc509` | chain | unconditional | always_active | 0 | `calc510` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~0 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 340 | `calc510` | chain | unconditional | always_active | 0 | `calc511` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~0 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 341 | `calc511` | chain | unconditional | always_active | 0 | `calc512` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~0 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 342 | `calc512` | chain | unconditional | always_active | 0 | `calc513` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~0 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 343 | `calc513` | chain | unconditional | always_active | 0 | `calc514` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 344 | `calc514` | chain | unconditional | always_active | 0 | `calc515` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 345 | `calc515` | chain | unconditional | always_active | 0 | `calc516` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~2 ~ ~0 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 346 | `calc516` | chain | unconditional | always_active | 0 | `calc517` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~2 ~ ~0 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 347 | `calc517` | chain | unconditional | always_active | 0 | `calc518` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~2 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt` |
| 348 | `calc518` | chain | unconditional | always_active | 0 | `calc519` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s positioned ~2 ~ ~2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1` |
| 349 | `calc519` | chain | unconditional | always_active | 0 | `calc520` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s run scoreboard players operation @s acc /= @s cnt` |
| 350 | `calc520` | chain | unconditional | always_active | 0 | `calc521` | `execute if score fb_cur ctl matches 6 as @e[tag=nt_col] at @s run scoreboard players operation @s hgt = @s acc` |
| 351 | `calc521` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 6 run scoreboard players set fb_state ctl 7` |
| 352 | `calc600` | repeat | unconditional | always_active | 0 | `calc601` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 353 | `calc601` | chain | unconditional | always_active | 0 | `calc602` | `execute if score fb_cur ctl matches 7 as @e[tag=nt_col] run scoreboard players operation @s hgt -= koffraw nz` |
| 354 | `calc602` | chain | unconditional | always_active | 0 | `calc603` | `execute if score fb_cur ctl matches 7 as @e[tag=nt_col] if score @s hgt matches ..1 run scoreboard players set @s hgt 2` |
| 355 | `calc603` | chain | unconditional | always_active | 0 | `calc604` | `execute if score fb_cur ctl matches 7 as @e[tag=nt_col] if score @s hgt matches 19.. run scoreboard players set @s hgt 18` |
| 356 | `calc604` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 7 run scoreboard players set fb_state ctl 8` |
| 357 | `draw00` | repeat | unconditional | always_active | 4 | `draw01` | `scoreboard players operation fb_cur ctl = fb_state ctl` |
| 358 | `draw01` | chain | unconditional | always_active | 0 | `draw02` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 0 as @e[tag=nt_col] if score @s hgt matches 2 at @s run fill ~-1 ~1 ~-1 ~0 ~1 ~0 minecraft:dirt` |
| 359 | `draw02` | chain | unconditional | always_active | 0 | `draw03` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 0 as @e[tag=nt_col] if score @s hgt matches 2 at @s run fill ~-1 ~2 ~-1 ~0 ~2 ~0 minecraft:grass` |
| 360 | `draw03` | chain | unconditional | always_active | 0 | `draw04` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 0 as @e[tag=nt_col] if score @s hgt matches 2 at @s run scoreboard players add bn2 ctl 1` |
| 361 | `draw04` | chain | unconditional | always_active | 0 | `draw05` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 1 as @e[tag=nt_col] if score @s hgt matches 3 at @s run fill ~-1 ~1 ~-1 ~0 ~1 ~0 minecraft:stone` |
| 362 | `draw05` | chain | unconditional | always_active | 0 | `draw06` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 1 as @e[tag=nt_col] if score @s hgt matches 3 at @s run fill ~-1 ~2 ~-1 ~0 ~2 ~0 minecraft:dirt` |
| 363 | `draw06` | chain | unconditional | always_active | 0 | `draw07` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 1 as @e[tag=nt_col] if score @s hgt matches 3 at @s run fill ~-1 ~3 ~-1 ~0 ~3 ~0 minecraft:grass` |
| 364 | `draw07` | chain | unconditional | always_active | 0 | `draw08` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 1 as @e[tag=nt_col] if score @s hgt matches 3 at @s run scoreboard players add bn3 ctl 1` |
| 365 | `draw08` | chain | unconditional | always_active | 0 | `draw09` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 2 as @e[tag=nt_col] if score @s hgt matches 4 at @s run fill ~-1 ~1 ~-1 ~0 ~2 ~0 minecraft:stone` |
| 366 | `draw09` | chain | unconditional | always_active | 0 | `draw10` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 2 as @e[tag=nt_col] if score @s hgt matches 4 at @s run fill ~-1 ~3 ~-1 ~0 ~3 ~0 minecraft:dirt` |
| 367 | `draw10` | chain | unconditional | always_active | 0 | `draw11` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 2 as @e[tag=nt_col] if score @s hgt matches 4 at @s run fill ~-1 ~4 ~-1 ~0 ~4 ~0 minecraft:grass` |
| 368 | `draw11` | chain | unconditional | always_active | 0 | `draw12` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 2 as @e[tag=nt_col] if score @s hgt matches 4 at @s run scoreboard players add bn4 ctl 1` |
| 369 | `draw12` | chain | unconditional | always_active | 0 | `draw13` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 3 as @e[tag=nt_col] if score @s hgt matches 5 at @s run fill ~-1 ~1 ~-1 ~0 ~3 ~0 minecraft:stone` |
| 370 | `draw13` | chain | unconditional | always_active | 0 | `draw14` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 3 as @e[tag=nt_col] if score @s hgt matches 5 at @s run fill ~-1 ~4 ~-1 ~0 ~4 ~0 minecraft:dirt` |
| 371 | `draw14` | chain | unconditional | always_active | 0 | `draw15` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 3 as @e[tag=nt_col] if score @s hgt matches 5 at @s run fill ~-1 ~5 ~-1 ~0 ~5 ~0 minecraft:grass` |
| 372 | `draw15` | chain | unconditional | always_active | 0 | `draw16` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 3 as @e[tag=nt_col] if score @s hgt matches 5 at @s run scoreboard players add bn5 ctl 1` |
| 373 | `draw16` | chain | unconditional | always_active | 0 | `draw17` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 4 as @e[tag=nt_col] if score @s hgt matches 6 at @s run fill ~-1 ~1 ~-1 ~0 ~4 ~0 minecraft:stone` |
| 374 | `draw17` | chain | unconditional | always_active | 0 | `draw18` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 4 as @e[tag=nt_col] if score @s hgt matches 6 at @s run fill ~-1 ~5 ~-1 ~0 ~5 ~0 minecraft:dirt` |
| 375 | `draw18` | chain | unconditional | always_active | 0 | `draw19` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 4 as @e[tag=nt_col] if score @s hgt matches 6 at @s run fill ~-1 ~6 ~-1 ~0 ~6 ~0 minecraft:grass` |
| 376 | `draw19` | chain | unconditional | always_active | 0 | `draw20` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 4 as @e[tag=nt_col] if score @s hgt matches 6 at @s run scoreboard players add bn6 ctl 1` |
| 377 | `draw20` | chain | unconditional | always_active | 0 | `draw21` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 5 as @e[tag=nt_col] if score @s hgt matches 7 at @s run fill ~-1 ~1 ~-1 ~0 ~5 ~0 minecraft:stone` |
| 378 | `draw21` | chain | unconditional | always_active | 0 | `draw22` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 5 as @e[tag=nt_col] if score @s hgt matches 7 at @s run fill ~-1 ~6 ~-1 ~0 ~6 ~0 minecraft:dirt` |
| 379 | `draw22` | chain | unconditional | always_active | 0 | `draw23` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 5 as @e[tag=nt_col] if score @s hgt matches 7 at @s run fill ~-1 ~7 ~-1 ~0 ~7 ~0 minecraft:grass` |
| 380 | `draw23` | chain | unconditional | always_active | 0 | `draw24` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 5 as @e[tag=nt_col] if score @s hgt matches 7 at @s run scoreboard players add bn7 ctl 1` |
| 381 | `draw24` | chain | unconditional | always_active | 0 | `draw25` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 6 as @e[tag=nt_col] if score @s hgt matches 8 at @s run fill ~-1 ~1 ~-1 ~0 ~6 ~0 minecraft:stone` |
| 382 | `draw25` | chain | unconditional | always_active | 0 | `draw26` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 6 as @e[tag=nt_col] if score @s hgt matches 8 at @s run fill ~-1 ~7 ~-1 ~0 ~7 ~0 minecraft:dirt` |
| 383 | `draw26` | chain | unconditional | always_active | 0 | `draw27` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 6 as @e[tag=nt_col] if score @s hgt matches 8 at @s run fill ~-1 ~8 ~-1 ~0 ~8 ~0 minecraft:grass` |
| 384 | `draw27` | chain | unconditional | always_active | 0 | `draw28` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 6 as @e[tag=nt_col] if score @s hgt matches 8 at @s run scoreboard players add bn8 ctl 1` |
| 385 | `draw28` | chain | unconditional | always_active | 0 | `draw29` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 7 as @e[tag=nt_col] if score @s hgt matches 9 at @s run fill ~-1 ~1 ~-1 ~0 ~7 ~0 minecraft:stone` |
| 386 | `draw29` | chain | unconditional | always_active | 0 | `draw30` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 7 as @e[tag=nt_col] if score @s hgt matches 9 at @s run fill ~-1 ~8 ~-1 ~0 ~8 ~0 minecraft:dirt` |
| 387 | `draw30` | chain | unconditional | always_active | 0 | `draw31` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 7 as @e[tag=nt_col] if score @s hgt matches 9 at @s run fill ~-1 ~9 ~-1 ~0 ~9 ~0 minecraft:grass` |
| 388 | `draw31` | chain | unconditional | always_active | 0 | `draw32` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 7 as @e[tag=nt_col] if score @s hgt matches 9 at @s run scoreboard players add bn9 ctl 1` |
| 389 | `draw32` | chain | unconditional | always_active | 0 | `draw33` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 8 as @e[tag=nt_col] if score @s hgt matches 10 at @s run fill ~-1 ~1 ~-1 ~0 ~8 ~0 minecraft:stone` |
| 390 | `draw33` | chain | unconditional | always_active | 0 | `draw34` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 8 as @e[tag=nt_col] if score @s hgt matches 10 at @s run fill ~-1 ~9 ~-1 ~0 ~9 ~0 minecraft:dirt` |
| 391 | `draw34` | chain | unconditional | always_active | 0 | `draw35` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 8 as @e[tag=nt_col] if score @s hgt matches 10 at @s run fill ~-1 ~10 ~-1 ~0 ~10 ~0 minecraft:grass` |
| 392 | `draw35` | chain | unconditional | always_active | 0 | `draw36` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 8 as @e[tag=nt_col] if score @s hgt matches 10 at @s run scoreboard players add bn10 ctl 1` |
| 393 | `draw36` | chain | unconditional | always_active | 0 | `draw37` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 9 as @e[tag=nt_col] if score @s hgt matches 11 at @s run fill ~-1 ~1 ~-1 ~0 ~9 ~0 minecraft:stone` |
| 394 | `draw37` | chain | unconditional | always_active | 0 | `draw38` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 9 as @e[tag=nt_col] if score @s hgt matches 11 at @s run fill ~-1 ~10 ~-1 ~0 ~10 ~0 minecraft:dirt` |
| 395 | `draw38` | chain | unconditional | always_active | 0 | `draw39` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 9 as @e[tag=nt_col] if score @s hgt matches 11 at @s run fill ~-1 ~11 ~-1 ~0 ~11 ~0 minecraft:grass` |
| 396 | `draw39` | chain | unconditional | always_active | 0 | `draw40` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 9 as @e[tag=nt_col] if score @s hgt matches 11 at @s run scoreboard players add bn11 ctl 1` |
| 397 | `draw40` | chain | unconditional | always_active | 0 | `draw41` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 10 as @e[tag=nt_col] if score @s hgt matches 12 at @s run fill ~-1 ~1 ~-1 ~0 ~10 ~0 minecraft:stone` |
| 398 | `draw41` | chain | unconditional | always_active | 0 | `draw42` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 10 as @e[tag=nt_col] if score @s hgt matches 12 at @s run fill ~-1 ~11 ~-1 ~0 ~11 ~0 minecraft:dirt` |
| 399 | `draw42` | chain | unconditional | always_active | 0 | `draw43` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 10 as @e[tag=nt_col] if score @s hgt matches 12 at @s run fill ~-1 ~12 ~-1 ~0 ~12 ~0 minecraft:grass` |
| 400 | `draw43` | chain | unconditional | always_active | 0 | `draw44` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 10 as @e[tag=nt_col] if score @s hgt matches 12 at @s run scoreboard players add bn12 ctl 1` |
| 401 | `draw44` | chain | unconditional | always_active | 0 | `draw45` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 11 as @e[tag=nt_col] if score @s hgt matches 13 at @s run fill ~-1 ~1 ~-1 ~0 ~11 ~0 minecraft:stone` |
| 402 | `draw45` | chain | unconditional | always_active | 0 | `draw46` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 11 as @e[tag=nt_col] if score @s hgt matches 13 at @s run fill ~-1 ~12 ~-1 ~0 ~12 ~0 minecraft:dirt` |
| 403 | `draw46` | chain | unconditional | always_active | 0 | `draw47` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 11 as @e[tag=nt_col] if score @s hgt matches 13 at @s run fill ~-1 ~13 ~-1 ~0 ~13 ~0 minecraft:grass` |
| 404 | `draw47` | chain | unconditional | always_active | 0 | `draw48` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 11 as @e[tag=nt_col] if score @s hgt matches 13 at @s run scoreboard players add bn13 ctl 1` |
| 405 | `draw48` | chain | unconditional | always_active | 0 | `draw49` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 12 as @e[tag=nt_col] if score @s hgt matches 14 at @s run fill ~-1 ~1 ~-1 ~0 ~12 ~0 minecraft:stone` |
| 406 | `draw49` | chain | unconditional | always_active | 0 | `draw50` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 12 as @e[tag=nt_col] if score @s hgt matches 14 at @s run fill ~-1 ~13 ~-1 ~0 ~13 ~0 minecraft:dirt` |
| 407 | `draw50` | chain | unconditional | always_active | 0 | `draw51` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 12 as @e[tag=nt_col] if score @s hgt matches 14 at @s run fill ~-1 ~14 ~-1 ~0 ~14 ~0 minecraft:snow` |
| 408 | `draw51` | chain | unconditional | always_active | 0 | `draw52` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 12 as @e[tag=nt_col] if score @s hgt matches 14 at @s run scoreboard players add bn14 ctl 1` |
| 409 | `draw52` | chain | unconditional | always_active | 0 | `draw53` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 13 as @e[tag=nt_col] if score @s hgt matches 15 at @s run fill ~-1 ~1 ~-1 ~0 ~13 ~0 minecraft:stone` |
| 410 | `draw53` | chain | unconditional | always_active | 0 | `draw54` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 13 as @e[tag=nt_col] if score @s hgt matches 15 at @s run fill ~-1 ~14 ~-1 ~0 ~14 ~0 minecraft:dirt` |
| 411 | `draw54` | chain | unconditional | always_active | 0 | `draw55` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 13 as @e[tag=nt_col] if score @s hgt matches 15 at @s run fill ~-1 ~15 ~-1 ~0 ~15 ~0 minecraft:snow` |
| 412 | `draw55` | chain | unconditional | always_active | 0 | `draw56` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 13 as @e[tag=nt_col] if score @s hgt matches 15 at @s run scoreboard players add bn15 ctl 1` |
| 413 | `draw56` | chain | unconditional | always_active | 0 | `draw57` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 14 as @e[tag=nt_col] if score @s hgt matches 16 at @s run fill ~-1 ~1 ~-1 ~0 ~14 ~0 minecraft:stone` |
| 414 | `draw57` | chain | unconditional | always_active | 0 | `draw58` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 14 as @e[tag=nt_col] if score @s hgt matches 16 at @s run fill ~-1 ~15 ~-1 ~0 ~15 ~0 minecraft:dirt` |
| 415 | `draw58` | chain | unconditional | always_active | 0 | `draw59` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 14 as @e[tag=nt_col] if score @s hgt matches 16 at @s run fill ~-1 ~16 ~-1 ~0 ~16 ~0 minecraft:snow` |
| 416 | `draw59` | chain | unconditional | always_active | 0 | `draw60` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 14 as @e[tag=nt_col] if score @s hgt matches 16 at @s run scoreboard players add bn16 ctl 1` |
| 417 | `draw60` | chain | unconditional | always_active | 0 | `draw61` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 15 as @e[tag=nt_col] if score @s hgt matches 17 at @s run fill ~-1 ~1 ~-1 ~0 ~15 ~0 minecraft:stone` |
| 418 | `draw61` | chain | unconditional | always_active | 0 | `draw62` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 15 as @e[tag=nt_col] if score @s hgt matches 17 at @s run fill ~-1 ~16 ~-1 ~0 ~16 ~0 minecraft:dirt` |
| 419 | `draw62` | chain | unconditional | always_active | 0 | `draw63` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 15 as @e[tag=nt_col] if score @s hgt matches 17 at @s run fill ~-1 ~17 ~-1 ~0 ~17 ~0 minecraft:snow` |
| 420 | `draw63` | chain | unconditional | always_active | 0 | `draw64` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 15 as @e[tag=nt_col] if score @s hgt matches 17 at @s run scoreboard players add bn17 ctl 1` |
| 421 | `draw64` | chain | unconditional | always_active | 0 | `draw65` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 16 as @e[tag=nt_col] if score @s hgt matches 18 at @s run fill ~-1 ~1 ~-1 ~0 ~16 ~0 minecraft:stone` |
| 422 | `draw65` | chain | unconditional | always_active | 0 | `draw66` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 16 as @e[tag=nt_col] if score @s hgt matches 18 at @s run fill ~-1 ~17 ~-1 ~0 ~17 ~0 minecraft:dirt` |
| 423 | `draw66` | chain | unconditional | always_active | 0 | `draw67` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 16 as @e[tag=nt_col] if score @s hgt matches 18 at @s run fill ~-1 ~18 ~-1 ~0 ~18 ~0 minecraft:snow` |
| 424 | `draw67` | chain | unconditional | always_active | 0 | `draw68` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 16 as @e[tag=nt_col] if score @s hgt matches 18 at @s run scoreboard players add bn18 ctl 1` |
| 425 | `draw68` | chain | unconditional | always_active | 0 | `draw69` | `execute if score fb_cur ctl matches 8 run scoreboard players add fb_b ctl 1` |
| 426 | `draw69` | chain | unconditional | always_active | 0 | `draw70` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 17.. run scoreboard players set fb_state ctl 99` |
| 427 | `draw70` | chain | unconditional | always_active | 0 | `draw71` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 17.. run tellraw @a {"rawtext":[{"text":"§a地形完成 §7\| 高度分布 "},{"text":"§72:"},{"score":{"name":"bn2","objective":"ctl"}},{"text":"§73:"}…` |
| 428 | `draw71` | chain | unconditional | always_active | 0 | `draw72` | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 17.. run title @a title §a地形生成完成` |
| 429 | `draw72` | chain | unconditional | always_active | 0 | — | `execute if score fb_cur ctl matches 8 if score fb_b ctl matches 17.. run playsound random.levelup @a` |

## Layout

| id | pos | facing |
|---|---|---|
| `boot00` | 0 64 1 | east |
| `boot01` | 1 64 1 | east |
| `boot02` | 2 64 1 | east |
| `boot03` | 3 64 1 | east |
| `boot04` | 4 64 1 | east |
| `boot05` | 5 64 1 | east |
| `boot06` | 6 64 1 | east |
| `boot07` | 7 64 1 | east |
| `boot08` | 8 64 1 | east |
| `boot09` | 9 64 1 | east |
| `boot10` | 10 64 1 | east |
| `boot11` | 11 64 1 | east |
| `boot12` | 12 64 1 | east |
| `boot13` | 13 64 1 | east |
| `boot14` | 14 64 1 | east |
| `boot15` | 15 64 1 | south |
| `boot16` | 15 64 2 | west |
| `boot17` | 14 64 2 | west |
| `boot18` | 13 64 2 | west |
| `boot19` | 12 64 2 | west |
| `boot20` | 11 64 2 | west |
| `boot21` | 10 64 2 | west |
| `boot22` | 9 64 2 | west |
| `boot23` | 8 64 2 | west |
| `boot24` | 7 64 2 | west |
| `boot25` | 6 64 2 | west |
| `boot26` | 5 64 2 | west |
| `boot27` | 4 64 2 | west |
| `boot28` | 3 64 2 | west |
| `boot29` | 2 64 2 | west |
| `boot30` | 1 64 2 | west |
| `boot31` | 0 64 2 | south |
| `boot32` | 0 64 3 | east |
| `boot33` | 1 64 3 | east |
| `boot34` | 2 64 3 | east |
| `boot35` | 3 64 3 | east |
| `boot36` | 4 64 3 | east |
| `boot37` | 5 64 3 | east |
| `boot38` | 6 64 3 | east |
| `boot39` | 7 64 3 | east |
| `boot40` | 8 64 3 | east |
| `boot41` | 9 64 3 | east |
| `boot42` | 10 64 3 | east |
| `boot43` | 11 64 3 | east |
| `boot44` | 12 64 3 | east |
| `boot45` | 13 64 3 | east |
| `boot46` | 14 64 3 | east |
| `boot47` | 15 64 3 | south |
| `boot48` | 15 64 4 | west |
| `boot49` | 14 64 4 | west |
| `boot50` | 13 64 4 | west |
| `boot51` | 12 64 4 | west |
| `boot52` | 11 64 4 | west |
| `boot53` | 10 64 4 | west |
| `boot54` | 9 64 4 | west |
| `boot55` | 8 64 4 | west |
| `boot56` | 7 64 4 | west |
| `boot57` | 6 64 4 | west |
| `boot58` | 5 64 4 | west |
| `boot59` | 4 64 4 | west |
| `boot60` | 3 64 4 | west |
| `boot61` | 2 64 4 | west |
| `boot62` | 1 64 4 | west |
| `boot63` | 0 64 4 | south |
| `boot64` | 0 64 5 | east |
| `boot65` | 1 64 5 | east |
| `boot66` | 2 64 5 | east |
| `boot67` | 3 64 5 | east |
| `boot68` | 4 64 5 | east |
| `boot69` | 5 64 5 | east |
| `boot70` | 6 64 5 | east |
| `boot71` | 7 64 5 | east |
| `boot72` | 8 64 5 | east |
| `boot73` | 9 64 5 | east |
| `boot74` | 10 64 5 | east |
| `boot75` | 11 64 5 | east |
| `boot76` | 12 64 5 | east |
| `boot77` | 13 64 5 | east |
| `prep00` | 0 65 1 | east |
| `prep01` | 1 65 1 | east |
| `prep02` | 2 65 1 | east |
| `prep03` | 3 65 1 | east |
| `prep04` | 4 65 1 | east |
| `prep05` | 5 65 1 | east |
| `prep06` | 6 65 1 | east |
| `prep07` | 7 65 1 | east |
| `prep08` | 8 65 1 | east |
| `prep09` | 9 65 1 | east |
| `prep10` | 10 65 1 | east |
| `prep11` | 11 65 1 | east |
| `prep12` | 12 65 1 | east |
| `prep13` | 13 65 1 | east |
| `grid00` | 0 66 1 | east |
| `grid01` | 1 66 1 | east |
| `grid02` | 2 66 1 | east |
| `grid03` | 3 66 1 | east |
| `grid04` | 4 66 1 | east |
| `grid05` | 5 66 1 | east |
| `grid06` | 6 66 1 | east |
| `grid07` | 7 66 1 | east |
| `grid08` | 8 66 1 | east |
| `grid09` | 9 66 1 | east |
| `grid10` | 10 66 1 | east |
| `grid11` | 11 66 1 | east |
| `grid12` | 12 66 1 | east |
| `grid13` | 13 66 1 | east |
| `grid14` | 14 66 1 | east |
| `grid15` | 15 66 1 | south |
| `grid16` | 15 66 2 | west |
| `grid17` | 14 66 2 | west |
| `grid18` | 13 66 2 | west |
| `grid19` | 12 66 2 | west |
| `grid20` | 11 66 2 | west |
| `grid21` | 10 66 2 | west |
| `grid22` | 9 66 2 | west |
| `grid23` | 8 66 2 | east |
| `calc100` | 0 68 1 | east |
| `calc101` | 1 68 1 | east |
| `calc102` | 2 68 1 | east |
| `calc103` | 3 68 1 | east |
| `calc104` | 4 68 1 | east |
| `calc105` | 5 68 1 | east |
| `calc106` | 6 68 1 | east |
| `calc107` | 7 68 1 | east |
| `calc108` | 8 68 1 | east |
| `calc109` | 9 68 1 | east |
| `calc110` | 10 68 1 | east |
| `calc111` | 11 68 1 | east |
| `calc112` | 12 68 1 | east |
| `calc113` | 13 68 1 | east |
| `calc114` | 14 68 1 | east |
| `calc115` | 15 68 1 | south |
| `calc116` | 15 68 2 | west |
| `calc117` | 14 68 2 | west |
| `calc118` | 13 68 2 | west |
| `calc119` | 12 68 2 | west |
| `calc120` | 11 68 2 | west |
| `calc121` | 10 68 2 | west |
| `calc122` | 9 68 2 | west |
| `calc123` | 8 68 2 | west |
| `calc124` | 7 68 2 | west |
| `calc125` | 6 68 2 | west |
| `calc126` | 5 68 2 | west |
| `calc127` | 4 68 2 | west |
| `calc128` | 3 68 2 | west |
| `calc129` | 2 68 2 | west |
| `calc130` | 1 68 2 | west |
| `calc131` | 0 68 2 | south |
| `calc132` | 0 68 3 | east |
| `calc133` | 1 68 3 | east |
| `calc134` | 2 68 3 | east |
| `calc135` | 3 68 3 | east |
| `calc136` | 4 68 3 | east |
| `calc137` | 5 68 3 | east |
| `calc138` | 6 68 3 | east |
| `calc139` | 7 68 3 | east |
| `calc140` | 8 68 3 | east |
| `calc141` | 9 68 3 | east |
| `calc142` | 10 68 3 | east |
| `calc143` | 11 68 3 | east |
| `calc144` | 12 68 3 | east |
| `calc145` | 13 68 3 | east |
| `calc146` | 14 68 3 | east |
| `calc147` | 15 68 3 | south |
| `calc148` | 15 68 4 | west |
| `calc149` | 14 68 4 | west |
| `calc150` | 13 68 4 | west |
| `calc151` | 12 68 4 | west |
| `calc152` | 11 68 4 | west |
| `calc153` | 10 68 4 | west |
| `calc154` | 9 68 4 | west |
| `calc155` | 8 68 4 | west |
| `calc156` | 7 68 4 | west |
| `calc157` | 6 68 4 | west |
| `calc158` | 5 68 4 | west |
| `calc159` | 4 68 4 | west |
| `calc160` | 3 68 4 | west |
| `calc161` | 2 68 4 | west |
| `calc162` | 1 68 4 | west |
| `calc163` | 0 68 4 | south |
| `calc164` | 0 68 5 | east |
| `calc165` | 1 68 5 | east |
| `calc166` | 2 68 5 | east |
| `calc167` | 3 68 5 | east |
| `calc168` | 4 68 5 | east |
| `calc169` | 5 68 5 | east |
| `calc170` | 6 68 5 | east |
| `calc171` | 7 68 5 | east |
| `calc172` | 8 68 5 | east |
| `calc173` | 9 68 5 | east |
| `calc174` | 10 68 5 | east |
| `calc175` | 11 68 5 | east |
| `calc176` | 12 68 5 | east |
| `calc177` | 13 68 5 | east |
| `calc178` | 14 68 5 | east |
| `calc179` | 15 68 5 | south |
| `calc180` | 15 68 6 | west |
| `calc181` | 14 68 6 | east |
| `calc200` | 0 69 1 | east |
| `calc201` | 1 69 1 | east |
| `calc202` | 2 69 1 | east |
| `calc203` | 3 69 1 | east |
| `calc204` | 4 69 1 | east |
| `calc205` | 5 69 1 | east |
| `calc206` | 6 69 1 | east |
| `calc207` | 7 69 1 | east |
| `calc208` | 8 69 1 | east |
| `calc209` | 9 69 1 | east |
| `calc210` | 10 69 1 | east |
| `calc211` | 11 69 1 | east |
| `calc212` | 12 69 1 | east |
| `calc213` | 13 69 1 | east |
| `calc214` | 14 69 1 | east |
| `calc215` | 15 69 1 | south |
| `calc216` | 15 69 2 | west |
| `calc217` | 14 69 2 | west |
| `calc218` | 13 69 2 | west |
| `calc219` | 12 69 2 | west |
| `calc220` | 11 69 2 | west |
| `calc221` | 10 69 2 | west |
| `calc222` | 9 69 2 | west |
| `calc223` | 8 69 2 | west |
| `calc224` | 7 69 2 | west |
| `calc225` | 6 69 2 | west |
| `calc226` | 5 69 2 | west |
| `calc227` | 4 69 2 | west |
| `calc228` | 3 69 2 | west |
| `calc229` | 2 69 2 | west |
| `calc230` | 1 69 2 | west |
| `calc231` | 0 69 2 | south |
| `calc232` | 0 69 3 | east |
| `calc233` | 1 69 3 | east |
| `calc234` | 2 69 3 | east |
| `calc235` | 3 69 3 | east |
| `calc236` | 4 69 3 | east |
| `calc237` | 5 69 3 | east |
| `calc238` | 6 69 3 | east |
| `calc239` | 7 69 3 | east |
| `calc240` | 8 69 3 | east |
| `calc241` | 9 69 3 | east |
| `calc242` | 10 69 3 | east |
| `calc243` | 11 69 3 | east |
| `calc244` | 12 69 3 | east |
| `calc245` | 13 69 3 | east |
| `calc246` | 14 69 3 | east |
| `calc247` | 15 69 3 | south |
| `calc248` | 15 69 4 | west |
| `calc249` | 14 69 4 | west |
| `calc250` | 13 69 4 | west |
| `calc251` | 12 69 4 | west |
| `calc252` | 11 69 4 | west |
| `calc253` | 10 69 4 | west |
| `calc254` | 9 69 4 | west |
| `calc255` | 8 69 4 | west |
| `calc256` | 7 69 4 | west |
| `calc257` | 6 69 4 | west |
| `calc258` | 5 69 4 | west |
| `calc259` | 4 69 4 | west |
| `calc260` | 3 69 4 | west |
| `calc261` | 2 69 4 | west |
| `calc262` | 1 69 4 | west |
| `calc263` | 0 69 4 | south |
| `calc264` | 0 69 5 | east |
| `calc265` | 1 69 5 | east |
| `calc266` | 2 69 5 | east |
| `calc267` | 3 69 5 | east |
| `calc268` | 4 69 5 | east |
| `calc269` | 5 69 5 | east |
| `calc270` | 6 69 5 | east |
| `calc271` | 7 69 5 | east |
| `calc272` | 8 69 5 | east |
| `calc273` | 9 69 5 | east |
| `calc274` | 10 69 5 | east |
| `calc275` | 11 69 5 | east |
| `calc276` | 12 69 5 | east |
| `calc277` | 13 69 5 | east |
| `calc278` | 14 69 5 | east |
| `calc279` | 15 69 5 | south |
| `calc280` | 15 69 6 | west |
| `calc281` | 14 69 6 | east |
| `calc300` | 0 70 1 | east |
| `calc301` | 1 70 1 | east |
| `calc302` | 2 70 1 | east |
| `calc303` | 3 70 1 | east |
| `calc304` | 4 70 1 | east |
| `calc305` | 5 70 1 | east |
| `calc306` | 6 70 1 | east |
| `calc307` | 7 70 1 | east |
| `calc308` | 8 70 1 | east |
| `calc309` | 9 70 1 | east |
| `calc310` | 10 70 1 | east |
| `calc311` | 11 70 1 | east |
| `calc312` | 12 70 1 | east |
| `calc313` | 13 70 1 | east |
| `calc314` | 14 70 1 | east |
| `calc315` | 15 70 1 | south |
| `calc316` | 15 70 2 | west |
| `calc317` | 14 70 2 | west |
| `calc318` | 13 70 2 | west |
| `calc319` | 12 70 2 | west |
| `calc320` | 11 70 2 | west |
| `calc321` | 10 70 2 | west |
| `calc322` | 9 70 2 | west |
| `calc323` | 8 70 2 | west |
| `calc324` | 7 70 2 | west |
| `calc325` | 6 70 2 | west |
| `calc326` | 5 70 2 | east |
| `calc400` | 0 71 1 | east |
| `calc401` | 1 71 1 | east |
| `calc402` | 2 71 1 | east |
| `calc403` | 3 71 1 | east |
| `calc404` | 4 71 1 | east |
| `calc405` | 5 71 1 | east |
| `calc406` | 6 71 1 | east |
| `calc407` | 7 71 1 | east |
| `calc408` | 8 71 1 | east |
| `calc409` | 9 71 1 | east |
| `calc410` | 10 71 1 | east |
| `calc411` | 11 71 1 | east |
| `calc412` | 12 71 1 | east |
| `calc413` | 13 71 1 | east |
| `calc414` | 14 71 1 | east |
| `calc415` | 15 71 1 | south |
| `calc416` | 15 71 2 | west |
| `calc417` | 14 71 2 | west |
| `calc418` | 13 71 2 | west |
| `calc419` | 12 71 2 | west |
| `calc420` | 11 71 2 | west |
| `calc421` | 10 71 2 | east |
| `calc500` | 0 72 1 | east |
| `calc501` | 1 72 1 | east |
| `calc502` | 2 72 1 | east |
| `calc503` | 3 72 1 | east |
| `calc504` | 4 72 1 | east |
| `calc505` | 5 72 1 | east |
| `calc506` | 6 72 1 | east |
| `calc507` | 7 72 1 | east |
| `calc508` | 8 72 1 | east |
| `calc509` | 9 72 1 | east |
| `calc510` | 10 72 1 | east |
| `calc511` | 11 72 1 | east |
| `calc512` | 12 72 1 | east |
| `calc513` | 13 72 1 | east |
| `calc514` | 14 72 1 | east |
| `calc515` | 15 72 1 | south |
| `calc516` | 15 72 2 | west |
| `calc517` | 14 72 2 | west |
| `calc518` | 13 72 2 | west |
| `calc519` | 12 72 2 | west |
| `calc520` | 11 72 2 | west |
| `calc521` | 10 72 2 | east |
| `calc600` | 0 73 1 | east |
| `calc601` | 1 73 1 | east |
| `calc602` | 2 73 1 | east |
| `calc603` | 3 73 1 | east |
| `calc604` | 4 73 1 | east |
| `draw00` | 0 90 1 | east |
| `draw01` | 1 90 1 | east |
| `draw02` | 2 90 1 | east |
| `draw03` | 3 90 1 | east |
| `draw04` | 4 90 1 | east |
| `draw05` | 5 90 1 | east |
| `draw06` | 6 90 1 | east |
| `draw07` | 7 90 1 | east |
| `draw08` | 8 90 1 | east |
| `draw09` | 9 90 1 | east |
| `draw10` | 10 90 1 | east |
| `draw11` | 11 90 1 | east |
| `draw12` | 12 90 1 | east |
| `draw13` | 13 90 1 | east |
| `draw14` | 14 90 1 | east |
| `draw15` | 15 90 1 | south |
| `draw16` | 15 90 2 | west |
| `draw17` | 14 90 2 | west |
| `draw18` | 13 90 2 | west |
| `draw19` | 12 90 2 | west |
| `draw20` | 11 90 2 | west |
| `draw21` | 10 90 2 | west |
| `draw22` | 9 90 2 | west |
| `draw23` | 8 90 2 | west |
| `draw24` | 7 90 2 | west |
| `draw25` | 6 90 2 | west |
| `draw26` | 5 90 2 | west |
| `draw27` | 4 90 2 | west |
| `draw28` | 3 90 2 | west |
| `draw29` | 2 90 2 | west |
| `draw30` | 1 90 2 | west |
| `draw31` | 0 90 2 | south |
| `draw32` | 0 90 3 | east |
| `draw33` | 1 90 3 | east |
| `draw34` | 2 90 3 | east |
| `draw35` | 3 90 3 | east |
| `draw36` | 4 90 3 | east |
| `draw37` | 5 90 3 | east |
| `draw38` | 6 90 3 | east |
| `draw39` | 7 90 3 | east |
| `draw40` | 8 90 3 | east |
| `draw41` | 9 90 3 | east |
| `draw42` | 10 90 3 | east |
| `draw43` | 11 90 3 | east |
| `draw44` | 12 90 3 | east |
| `draw45` | 13 90 3 | east |
| `draw46` | 14 90 3 | east |
| `draw47` | 15 90 3 | south |
| `draw48` | 15 90 4 | west |
| `draw49` | 14 90 4 | west |
| `draw50` | 13 90 4 | west |
| `draw51` | 12 90 4 | west |
| `draw52` | 11 90 4 | west |
| `draw53` | 10 90 4 | west |
| `draw54` | 9 90 4 | west |
| `draw55` | 8 90 4 | west |
| `draw56` | 7 90 4 | west |
| `draw57` | 6 90 4 | west |
| `draw58` | 5 90 4 | west |
| `draw59` | 4 90 4 | west |
| `draw60` | 3 90 4 | west |
| `draw61` | 2 90 4 | west |
| `draw62` | 1 90 4 | west |
| `draw63` | 0 90 4 | south |
| `draw64` | 0 90 5 | east |
| `draw65` | 1 90 5 | east |
| `draw66` | 2 90 5 | east |
| `draw67` | 3 90 5 | east |
| `draw68` | 4 90 5 | east |
| `draw69` | 5 90 5 | east |
| `draw70` | 6 90 5 | east |
| `draw71` | 7 90 5 | east |
| `draw72` | 8 90 5 | east |

## Setup

Run once before building:

```mcfunction
gamerule commandblocksenabled true
导入后 setblock 0 64 0 redstone_block 触发
```

## Tests

- [ ] 导入后 15 秒内地形长出来
- [ ] chat 的高度分布与 design.md 一致
- [ ] 再触发一次换种子、换地形

## Design notes

- 值噪声 + 邻域平滑；除法朝 0 截断；中间量 < 2^31

---

Generated by `scripts/chain_lint.py`. Static checks only — verify in-game before shipping.
