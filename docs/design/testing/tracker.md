# Testing tooling: tracker

One section per tool built for the human play-tests, appended by its worker.

### Telemetry

Branch `testing-telemetry` (the name `testing/telemetry` was impossible: a branch called `testing` exists), off `testing` at 889d453. Worktree `VS Backrooms-testing-telemetry`.

- Built: `src/Telemetry/TelemetrySystem.cs` (server event log plus the F8 / `/backrooms mark` marker on the client), one-line hooks in MenaceSystem (spawn), EntityBehaviorMenace (kind, contact), ZeroSystem (blackout), CrossingSystem (cross), NoteSystem (note); `tools/telemetry/report.py`; docs in DEVELOPING.md ("Play telemetry") and GUIDE.md.
- Checked headless on port 42795: session, spawn, kind and mark events from a straw dummy (`/backrooms mark` from the console marks the latest dummy), report.py on that file and on a synthetic player file, harness `--only iso` 2/2.
- Not checked without a real client: F8 and `.mark`, damage, death, eat and drink, loot, trade, contact, needs, stability, level and pos events (they need a player).
- Left for later: `--compare` against `docs/design/balance-spec.yaml` (stub in `compare()`).
- Blind review (sonnet): fixed the logger-thread trade parse (queued, drained on the tick), throttle exemptions for level/stab/need/damage, layout version read without writing config, damage hook retry/rejoin, spawn/kind arguments guarded by `Telemetry.On`, rates pruned on leave, report.py respawn/join/dummy handling. Left: F8 needs the `controlserver` privilege (it is a `/backrooms` subcommand), loot detection is by block name, eat/drink counts are lower bounds, report time-to-first-encounter is spawn-based wall clock.

### Client rig

Branch `testing-clientrig` (the name `testing/clientrig` cannot exist while the branch `testing` does). 2026-10-25.

Built: `tools/clientrig/rig.py` (driver, `--dry-run` validates a scenario without launching anything), six scenarios under
`tools/clientrig/scenarios/`, `src/Cheats/RigCommands.cs` (`/backrooms rig equip|sleep|face|walk|classdrops`), DEVELOPING.md "Client rig".

What ran (one real run, then the user asked for no more on-screen testing):

- Run 1 (boot.yaml, the first attempt): the driver waited for the bot's `status.txt`, which the bot writes only after its first command, so the
  window stayed on-screen for two minutes and was closed (by the user, "window close event"). Fixed: the driver waits for `ready.txt`
  (level finalized), then moves the window. No scenario step ran.
- Run 2 (boot.yaml, build of this branch): server up in 35 s, client in the world 26 s later, window moved to x = -4000 (not iconic), player
  eXception386 read from the join line and opped, 12 of 13 steps passed. The one failure is a correct detection:
  **"Captured 3 issues during startup": NullReferenceException in `Backrooms.Salvage.Breakdown.FindOwnDrops` (Breakdown.cs:288)** via
  `ProtectionSystem.AssetsFinalize`; the fix is on `fix/client-drops`, not in this branch. `/backrooms menace` and `/backrooms where` answered
  in the client's chat. The screenshot `boot-world` (1015 KB, taken off-screen and unfocused) shows Level 0: yellow patterned wallpaper
  with a dark skirting, beige carpet, ceiling tiles with two fluorescent panels, a room opening into corridors; clean, lit, no HUD.

Untested (written against the code, only validated with `--dry-run`): placards, armour, respawn, blackout, scarcity. Things to check on their first
real run: whether `nearest gate` from Level 1 lands in front of a gate to Level 2 (placard kind 3-2) and the placard is within `rig face`'s 16 blocks;
the crossing line text ("in here") after `rig walk 6`; the damage-log chat wording (`expect_chat: damage` is a guess); `rig equip jerkin-leather`
(a slot may refuse; the scenario falls back to `armourtest` output); `rig sleep` (needs rest low; refuses otherwise); the blackout wake level (Level 2).
`expect_telemetry` skips with a note until the telemetry branch is merged.

Blind review (sonnet) fixed: off-screen target left of the whole virtual screen, `SWP_NOSIZE`, focus back to the launching window and checked,
cleanup in `finally`, report written when the server never started, crash recorded when the client dies after the world loads, `cmd` steps fail
on no reply, `expect_chat` consumes only up to the matched line, `rig face` pitch sign, a wait after every `goto` before `ready`, a pause
before `rig sleep`. Not done: forcing windowed mode (the rig copies the user's fullscreen setting), a per-run data dir and port check, `rig walk`
refusing solid blocks. All after the one real run; none re-run (no more on-screen testing for now).

### Gate

`tools/gate.py` (see docs/DEVELOPING.md "The gate"): generators --check, lang, build, boot, mapgen, oldworld, harness, zip. Branch `testing-gate` (the name `testing/gate` could not be created: a branch `testing` exists). Baselines in `tools/gate.hashes.json` (layout hashes v1, 9, 10, 11, 12: far places hash v1 `fc427d581f53ea30`, v9 and v10 `29d61d9ae6a6664e`, v11 and v12 `8808cf5b8452ad21`, matching the progression tracker; validatelevel 0-20, deep and shortcut counts of v12). `run.py` gained `--groups all|smoke` and `--rerun-failed N`; `locked.sh` a `release` mode.

**First full run** (`python tools/gate.py --zip`, 2026-10-25, commit 10639ca): PASS in 44m41s.

| Stage | Result | Time |
|---|---|---|
| generators | pass | 0m00s |
| lang | pass (9 files) | 0m00s |
| build | pass | 1m00s |
| boot | pass (fresh seed, 0 missing, 0 errors) | 0m40s |
| mapgen | pass (hashes match, baselines recorded) | 2m19s |
| oldworld | pass (sunny cave tales copy, ratecheck answered) | 0m41s |
| harness | pass, 44/44 (prog-speed failed once, passed on the rerun) | 36m58s |
| zip | pass (bin/backroomsss_0.610.0.zip, 19.1 MB, version matches) | 3m00s |

**`--fast`**: PASS in 4m26s (build 2m00 under lock contention, boot 0m36, harness smoke 1m48; about 2m40 with a build already made).

Flaky case seen: `prog-speed` (a pace measurement, not a placement case). Reviewer (sonnet, blind): 15 findings; fixed: zip stage deletes only the current version's zip, baselines written only by a problem-free run and `--update-baselines` covers deep/spawn, parsers fail when expected lines are missing, ratecheck reply matched exactly, reader thread joined before reading logs, stdin closed on children, build error regex, harness log kept on timeout, second-resolution stamps, rerun skips cases without a function. Not changed: a missing old-world save skips (loudly) rather than fails; the boot log scan is 10 s after ready; no stale-build check for `--only` runs on an old build.
