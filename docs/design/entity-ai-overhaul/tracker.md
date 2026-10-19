# Entity AI overhaul: tracker

One row per batch, kept current by the overseer; one report per batch, appended by its worker. Lessons at the end are
inherited by every later batch. The plan is [README.md](README.md).

## Batches

| Batch | Branch | Worker | State | Gate | Notes |
|---|---|---|---|---|---|
| P0 Senses, noise, harness | ai/p0-senses | Opus (code), Sonnet (harness), Haiku (buttons, docs) | merged | harness 11/11 | |
| P1 State machine v2; Hound and Smiler | ai/p1-machine | Sonnet x2, Sonnet blind review and fix round | merged (integration branch) | review fixed 9 findings; harness p1 cases pass but for one timing expectation | the integration branch for the release |
| P2 Skin-Stealer, Duller, Death Rat, Wretch | ai/p2-stealers | Sonnet | merged | headless decisions checked | health read as level-scaled effective values (Skin-Stealer base 51, Duller 20) |
| P3a Deathmoth hives, Clumps | ai/p3a-hives-clumps | Sonnet | merged | headless incl. blocksweep and save data | hive heart code is `mothhiveheart` (`mothhive` was taken by a worldgen prop); juvenile Clumps are full size (scale is per type) |
| P3b Facelings | ai/p3b-facelings | Sonnet | merged | headless: Evolved look, outburst trigger | outbursts only from breaking and fighting |
| P4a The Strider, the Spider, the Beast, the Thing, Partygoers | ai/p4a-senses | Sonnet | merged | headless: fear, colony | Partygoer hearing and the spider's lurk test kept bespoke (a like-for-like move would change them) |
| P4b The floating Watcher | ai/p4b-watcher | Sonnet | merged | headless: charge and beam; render reviewed | |
| P5 Levels | ai/p5-levels | Haiku | merged | roster diff matches section 8 | Level 5's extra hive dens dropped (worldgen, would need a layout version); Level 7 splash skipped (no such sound) |
| P6 Harvest and materials | ai/p6-materials | Sonnet | merged | headless: recipes load, harvest configs, venom on an arrow | venom via a Harmony patch on ReceiveDamage (under final review) |
| P7 Play-test tuning | | | waiting for the user's play-test | | client check-lists from every batch are the starting point |
| P8 Finish | | | not started | | |

## Reports

(Appended by each worker: what changed per entity, harness results, the client check-list with what was seen, numbers
changed, what was carried and why.)

### P0 (2026-10-18)

- **Code:** `src/Entities/Perception.cs` (SenseProfile from a task's `senses`, Belief, NoiseBus, sight / sense / hearing),
  `MenaceSystem.Probe.cs` (noise listening: doors via DidUseBlock, Firesalt via DidPlaceBlock, thrown things landing via
  OnEntitySpawn of IProjectile, jumps; the cost line; `/backrooms perceive`, `/backrooms dummy ...`); the director raises
  break, run and test noises; hits raise fight noise (AiTaskMenace.Hit, Strike.Hit except poison, a player striking a
  menace entity); a hunt cry raises cry noise. `Senses`: glass-aware ClearLine, Sneaking, test-dummy overrides.
- **Harness:** `tools/aitest/run.py`, 11/11 (dark and lit range, facing away, sneaking, noise heard and not, losing the
  trail after memory, fear, running, a director smoke run); 363 s on a fresh world.
- **Deviations from the plan:** thrown-object impact is 0.5 (plan 0.2), so a stone actually draws things off; lighting a
  firepit is not heard (no server event for it; Firesalt placement is); landing from a fall is not heard (only jumps:
  OnGround is not reliable server side).
- **Lessons:** console lines keep their trailing CR glued to the last argument, but int and double parsing tolerate it;
  give argument-less leaves an `OptionalWord("ignored")`. A generator run rewrites every file it touches with LF
  endings: restore line-ending-only files with `git checkout HEAD -- <files>` after checking `git diff
  --ignore-cr-at-eol --stat`. A dummy spot whose chunks never load answers "No floor"; pick another key.

### P4a (2026-10-19): senses for the Partygoer, the Strider, the Spider, the Beast, the Thing

- **Onto `Perception`:** the Partygoer's `Notices` (sight = `Perception.Sight` with `senses` 12/7/4, cone 70, sneak 0.6; while
  hunting a copy with all three ranges 12, cone 360); the Strider's `Visibility` (`Perception.Sensed` for touch, `Perception.Sight`
  with its own lit/dark light reckoning passed in through the new `light` argument, `glass` special, scan and chase cones as
  profile copies; its notice accumulation, lit and eye-contact multipliers stay on top); the Spider's trespass and hearing
  numbers now come from its `senses` (`touch`, `hearing`, `sneakFactor`); the unveiled Beast gets `senses` (30/20/10, fear 24,
  hearing 20), so the common menace task works from belief for him.
- **Kept bespoke, and why:** the Partygoer's hearing (running or a bang within `hearing`, flat: `Perception.Heard` would cut
  running from 6 to 2.4 blocks) and its disguise; the Spider's lurk test (gap-based, vertical limit, no line needed; `Sensed`
  would need a clear line and use the centre distance); the Strider's window peering, search and feint; the Strider's light
  (lamps and fires only, not the sky: `Sight` gets it through its `light` argument); the Thing's `senses` (`water`, hearing
  40) is read by `/backrooms perceive` only, since its task goes by depth and not by what it hears.
- **Strider:** fear (Hound, Smiler, Skin-Stealer, Deathmoths within 24 go to Leave, once a second, in its own tick);
  never placed within 200 blocks of Level 10's wall (`FindSpot`); `rangedDamageMul: 2` on its menace behaviour (any
  `IProjectile` source); names are "Strider of the Neighborhood Watch" (entity code unchanged).
- **Spider:** a noise of 0.5 or more within 24 blocks of a nest heart (`WorldLayout.NestHeartNear`, `MenaceSystem.Colony.cs`,
  hooked in `RaiseNoise`) wakes the nest's spiders (`AiTaskSpider.WakeFor`) and puts down one or two more from the nest's dark
  if fewer than three are about (45 s between); raw bushmeat x1 drop.
- **Thing:** a lit lantern or oil lamp under water within 12 blocks breaks the rush off for 20 s (`lampRange`, `lampBreakSeconds`).
- **Harness:** `/backrooms dummy place nest` (cheat-menu button "Dummy at a nest"). Headless: see the report to the overseer.
- **Lessons:** a headless world made without `backroomsLayoutVersion: 9` in `WorldConfig` is layout version 1 and has no
  spider nests. `encounter` leaves entities behind: filter log lines by position when counting.

## Lessons

(Engine gotchas, profile fields that had to be added, harness quirks. Start here before P0: the gotchas in README
section 9 and in `docs/design/entity-models-todo.md` section 5.)

- **Never stop Vintage Story servers by image name** (`taskkill //IM VintagestoryServer.exe`, `Get-CimInstance ... | Stop-Process` on the name): several agents run headless servers at once, and two batches killed everyone's, which looked like a crash in the gate run. Stop only your own server, by PID, or by a command-line filter on your own data folder.
- Headless entities think but never walk, so paths "fail" and a hunt goes Hunt -> Stalk by the old no-path rule; test decisions by timeouts, and retry spots.
- With several agents' servers and builds running, everything is slow: a build may wait minutes for the lock; a harness run takes 15 to 20 minutes.
