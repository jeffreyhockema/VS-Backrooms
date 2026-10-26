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

### Client rig: first full run

Build: the `testing` branch plus this branch's `/backrooms rig` helpers (`%TEMP%/backrooms-build/build-rigrun`), main's client fix included. Seed 424242, port 42797, player eXception386 (opped by the driver). Client window off-screen (x = -4000), never minimized, focus handed back. Reports, screenshots, logs, telemetry and chat per scenario are in `review/clientrig/2026-10-26/<scenario>/`.

| Scenario | Result | What the screenshots and chat show |
|---|---|---|
| boot | PASS (14/14). 0 captured startup issues (the FindOwnDrops crash is fixed) | `boot-world`: Level 0, yellow chevron wallpaper with dark skirting, beige carpet, ceiling tiles with fluorescent panels; `/backrooms menace` and `where` answer |
| placards | PASS (16/16) | `placard-near`: a legible steel plate "M.E.G. - LEVEL 2 - CLASS 3 / HOSTILE. / LIGHT AND A WEAPON" screwed to the near-side wall right beside the black steel door of the Level 1 gate to Level 2, facing the viewer from 3 blocks; `past-gate`: Level 2's pipe tunnel. Crossing line (by `/backrooms goto 2`): "Level 2. It is hostile in here, and dark in places. Bring a light and a weapon. You are wearing nothing that would turn a blow." |
| armour | PASS (21/21) | jerkin-leather worn (2 pieces: body, legs); Hound hunt at Level 3: three hits of "Lost 6.13 hp by a Hound (Creature)" then "got killed by a Hound". `armourtest` predicts body 6.1 / legs 6.1 / head 9.1 (bare) and 2.2 blows to kill: matches. The damage lines are in the Damage log tab. `hound-hunt`: the death view, red vignette |
| respawn | PASS (26/26) | slept in a Level 5 hotel bed (`rig sleep`, rest 0.1), sent to Level 1, died, pressed Respawn (new shotbot `respawn`): woke in Level 5 two blocks from the bed (513672.5,507407.5 vs bed 513674,507407), chat "Your belongings lie with your body, where you fell...". `woke`: the hotel corridor with the bed in the foreground |
| blackout | PASS with 1 known finding (142/142 + 1) | stability 0 held in Level 3: the hunter is sent at once, the lights go after 61 s, and the player comes to in Level 2 3 s later (server log). `after-blackout`: Level 2 pipe tunnel, lit. FINDING below: the chat line is the raw key |
| scarcity | PASS (12/12) | supply box rolled 400 times where the player stands: Level 1 (class scale 1): almond water 0.815, canned beans 0.328, crackers 0.498; Level 3 (class scale 0.5): 0.403, 0.140, 0.278 (about half). No screenshot (data only) |
| telemetry | PASS (56/56) | session, join, level, pos, spawn, kind, damage, death, respawn, mark all recorded; `tools/telemetry/report.py` run on the file by the driver (`telemetry-report.md`) |
| handbook | PASS (11/11) | `handbook-entities`: the Survival Handbook open on "What lives in the Backrooms" (How danger works...); `handbook-levels` the levels page |

## Findings (mod, not changed)

1. **`zero-blackout` chat line is the raw key.** `src/Reality/ZeroSystem.cs:204` calls `Say.T(woken, "zero-blackout")`; the lang key is `backrooms:zero-blackout`, so without the domain `Lang.GetL` returns the key and the chat shows `zero-blackout`, never "You lose your grip on the place...". Evidence: `blackout/chat.txt` lines "zero-blackout" (twice), no "grip" line; server log shows the blackout and wake itself work (61 s, Level 3 to Level 2). Fix: `Say.T(woken, "backrooms:zero-blackout")`. Level of the crossing line uses the right prefix.
2. Log label: after waking in Level 2 the next hunter line says "sending backrooms:hound for eXception386 (Level 3)" (the label is stale for a few seconds; harmless).
3. Telemetry `respawn` event records `level "3"` (where the player died) with the spawn coordinates of Level 0; the level field of that event is stale.
4. Hound hunts started with an explicit distance (`encounter hound hunt 0 0 8`) go to Search within 50 ms and never close in (setpiece false); the default distance hunts hit within seconds. Hunts at default distance sometimes turn to Search without a blow (1 of 4 runs). Not a bug by itself.
5. Handbook text: "The setting.Backrooms entities (a world setting..." is missing a space after the bold "The setting." (entities page, "The setting" bullet).
6. `/backrooms stat rest 0.1` then `rig sleep` works after a 2.5 s pause (the vanilla tiredness copy runs on a tick).

## Needs a human

- F8 itself (the bot cannot press a key; `/backrooms mark` is the same path).
- Whether the placards, the Level 2 and Level 3 pipes and tunnels, the hotel corridor and the hound feel right to play (the rig checks they exist, read and arrive, not feel).
- Walking through a gate on foot: the scenario uses `goto 2`, whose crossing line fired; walking is untested because the camera faces the plate, not the opening.
- Real sound, controller or mouse play, anything needing two players.
