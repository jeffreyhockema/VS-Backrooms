# Entity AI overhaul: tracker

One row per batch, kept current by the overseer; one report per batch, appended by its worker. Lessons at the end are
inherited by every later batch. The plan is [README.md](README.md).

## Batches

| Batch | Branch | Worker | State | Gate | Notes |
|---|---|---|---|---|---|
| P0 Senses, noise, harness | ai/p0-senses | | not started | | |
| P1 State machine v2; Hound and Smiler | ai/p1-machine | | not started | | needs P0 merged |
| P2 Skin-Stealer, Duller, Death Rat, Wretch | ai/p2-stealers | | not started | | needs P1 |
| P3 Deathmoths, Clumps, Facelings | ai/p3-hives | | not started | | needs P1; may run beside P2 |
| P4 The Watch (Strider refined, Watcher built), the Spider, the Beast, the Thing, Partygoers | ai/p4-newcomers (may split: ai/p4a-senses, ai/p4b-watcher) | | not started | | needs P1 and l5-beast, l8-spider, l9-watch merged |
| P5 Levels | ai/p5-levels | | not started | | needs P1 |
| P6 Harvest and materials | ai/p6-materials | | not started | | needs P3, P4 |
| P7 Play-test tuning | ai/p7-tuning | | not started | | needs the user's play notes |
| P8 Finish | ai/p8-finish | | not started | | |

## Reports

(Appended by each worker: what changed per entity, harness results, the client check-list with what was seen, numbers
changed, what was carried and why.)

## Lessons

(Engine gotchas, profile fields that had to be added, harness quirks. Start here before P0: the gotchas in README
section 9 and in `docs/design/entity-models-todo.md` section 5.)
