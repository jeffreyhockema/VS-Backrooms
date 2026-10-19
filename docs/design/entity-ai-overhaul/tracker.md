# Entity AI overhaul: tracker

One row per batch, kept current by the overseer; one report per batch, appended by its worker. Lessons at the end are
inherited by every later batch. The plan is [README.md](README.md).

## Batches

| Batch | Branch | Worker | State | Gate | Notes |
|---|---|---|---|---|---|
| P0 Senses, noise, harness | ai/p0-senses (worktree VS Backrooms-ai) | Opus (code), Sonnet (harness), Haiku (buttons, docs) | done | passed: harness 11/11 | merged into ai/p1-machine |
| P1 State machine v2; Hound and Smiler | ai/p1-machine (VS Backrooms-ai1) | Sonnet x2 (task; director and profiles) | built, under review and test | | integration branch for the release |
| P2 Skin-Stealer, Duller, Death Rat, Wretch | | | waiting on P1's fixes (edits the same task) | | |
| P3a Deathmoth hives, Clumps | ai/p3a-hives-clumps (VS Backrooms-ai3a) | Sonnet | running | | off P1's first commit |
| P3b Facelings | ai/p3b-facelings (VS Backrooms-ai3b) | Sonnet | running | | off P1's first commit |
| P4 The Watch (Strider refined, Watcher built), the Spider, the Beast, the Thing, Partygoers | | | not started | | the three entity branches are on main |
| P5 Levels | ai/p5-levels (VS Backrooms-ai5) | Haiku | part 1 done (ed4e259) | passed: roster diff matches section 8 | Level 5's extra hive dens dropped: den frequency is worldgen and would need a layout version; the splash for Level 7 skipped (no such sound) |
| P6 Harvest and materials | | | not started | | |
| P7 Play-test tuning | | | not started | | needs the user's play notes |
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

## Lessons

(Engine gotchas, profile fields that had to be added, harness quirks. Start here before P0: the gotchas in README
section 9 and in `docs/design/entity-models-todo.md` section 5.)

- **Never stop Vintage Story servers by image name** (`taskkill //IM VintagestoryServer.exe`, `Get-CimInstance ... | Stop-Process` on the name): several agents run headless servers at once, and two batches killed everyone's, which looked like a crash in the gate run. Stop only your own server, by PID, or by a command-line filter on your own data folder.
- Headless entities think but never walk, so paths "fail" and a hunt goes Hunt -> Stalk by the old no-path rule; test decisions by timeouts, and retry spots.
- With several agents' servers and builds running, everything is slow: a build may wait minutes for the lock; a harness run takes 15 to 20 minutes.
