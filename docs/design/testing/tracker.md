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

### Balance spec

Branch `testing-spec`, 2026-10-26. `docs/design/balance-spec.yaml` (status: proposed, awaiting the user's approval), gate stage `scorecard` (`python tools/gate.py --only scorecard`, about 6 minutes), `tools/telemetry/report.py --compare docs/design/balance-spec.yaml`. Numbers come from the user's decisions where they exist (the Level 1 rows: a creature about every 7 minutes in the heart on Normal, 2.55 minutes at the edge; the settings table; the lethality anchors; the class scale; kinds allowed; danger, class and solitude) and from today's measurements otherwise (`basis: measurement`; ratecheck 200 h, three feltrate dummies per level, armourtest, the v12 shortcut counts of `tools/gate.hashes.json`). Other dial-in figures (Level 3 heartland, Level 4 approach and so on) were first labelled decisions, but the review found them taken from the superseded dial-in factors, so they are measurements now. Run on commit `620d166` plus the review fixes; 253 rows, 238 ok, 0 outside, 15 not measured (the class scale of levels where no dummy is placed, kept honest rather than guessed).

Notes: felt rates vary 2x with the dummy spot (Level 9: 39 to 94 an hour), hence the 45 to 55 % tolerance and a mean of two to four dummies. A rolls row outside its tolerance after 20 hours is re-measured over 100 hours before it fails. Level 4's and Level 94's heartland, Level 3999's heartland and approach, and the armour rows of Levels 6, 37 and The End (no hunter that hits) are left out. `compare()` is a coarse check: the thirst-and-fatigue multiplier and the one-kind rule are not modelled, and the armour tier is the best piece worn.

| Group | Row | Spec | Measured | |
|---|---|---|---|---|
| settings | off | spawns 1 damage 0 mix 0 caps 0/0 | spawns 1 damage 0 mix 0 caps 0/0 | ok |
| settings | verylow | spawns 2 damage 0.5 mix 0 caps 0/0 | spawns 2 damage 0.5 mix 0 caps 0/0 | ok |
| settings | low | spawns 3.5 damage 0.75 mix 0 caps 0/0 | spawns 3.5 damage 0.75 mix 0 caps 0/0 | ok |
| settings | normal | spawns 5.5 damage 1 mix 0 caps 0/0 | spawns 5.5 damage 1 mix 0 caps 0/0 | ok |
| settings | high | spawns 8.5 damage 1.3 mix 0.3 caps 1/0 | spawns 8.5 damage 1.3 mix 0.3 caps 1/0 | ok |
| settings | veryhigh | spawns 13 damage 1.6 mix 0.6 caps 1/1 | spawns 13 damage 1.6 mix 0.6 caps 1/1 | ok |
| settings | the scorecard server's setting | normal | normal | ok |
| rolls | L0 heartland bodies/h [measurement] | 7.2 +-25% | 7.3 | ok |
| rolls | L0 heartland sounds/h [measurement] | 24.4 +-25% | 24.4 | ok |
| rolls | L0 approach bodies/h [measurement] | 20.4 +-25% | 19.9 | ok |
| rolls | L0 approach sounds/h [measurement] | 48.4 +-25% | 47.2 | ok |
| rolls | L0 threshold bodies/h [measurement] | 61.5 +-25% | 64.6 | ok |
| rolls | L0 threshold sounds/h [measurement] | 105.0 +-25% | 102.5 | ok |
| class | L0 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L1 heartland bodies/h [decision] | 8.6 +-25% | 8.8 | ok |
| rolls | L1 heartland sounds/h [decision] | 28.2 +-25% | 27.2 | ok |
| rolls | L1 approach bodies/h [decision] | 23.5 +-25% | 22.6 | ok |
| rolls | L1 approach sounds/h [measurement] | 57.7 +-25% | 58.3 | ok |
| rolls | L1 threshold bodies/h [measurement] | 71.4 +-25% | 73.8 | ok |
| rolls | L1 threshold sounds/h [measurement] | 123.2 +-25% | 123.9 | ok |
| class | L1 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L2 heartland bodies/h [measurement] | 16.2 +-25% | 15.8 | ok |
| rolls | L2 heartland sounds/h [measurement] | 53.4 +-25% | 54.9 | ok |
| rolls | L2 approach bodies/h [measurement] | 44.0 +-25% | 44.6 | ok |
| rolls | L2 approach sounds/h [measurement] | 104.3 +-25% | 103.5 | ok |
| rolls | L2 threshold bodies/h [measurement] | 134.0 +-25% | 136.3 | ok |
| rolls | L2 threshold sounds/h [measurement] | 212.6 +-25% | 211.6 | ok |
| class | L2 kinds allowed at once [decision] | 2 | 2 | ok |
| rolls | L3 heartland bodies/h [measurement] | 24.8 +-25% | 24.7 | ok |
| rolls | L3 heartland sounds/h [measurement] | 81.9 +-25% | 84.8 | ok |
| rolls | L3 approach bodies/h [measurement] | 69.4 +-25% | 70.9 | ok |
| rolls | L3 approach sounds/h [measurement] | 169.1 +-25% | 170.1 | ok |
| rolls | L3 threshold bodies/h [measurement] | 209.8 +-25% | 210.7 | ok |
| rolls | L3 threshold sounds/h [measurement] | 336.8 +-25% | 330.9 | ok |
| class | L3 kinds allowed at once [decision] | 2 | 2 | ok |
| rolls | L4 approach bodies/h [measurement] | 20.3 +-25% | 21.4 | ok |
| rolls | L4 approach sounds/h [measurement] | 48.8 +-25% | 46.8 | ok |
| rolls | L4 threshold bodies/h [measurement] | 61.7 +-25% | 63.3 | ok |
| rolls | L4 threshold sounds/h [measurement] | 104.9 +-25% | 105.6 | ok |
| class | L4 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L5 heartland bodies/h [measurement] | 9.2 +-25% | 8.8 | ok |
| rolls | L5 heartland sounds/h [measurement] | 30.6 +-25% | 31.7 | ok |
| rolls | L5 approach bodies/h [measurement] | 25.6 +-25% | 26.1 | ok |
| rolls | L5 approach sounds/h [measurement] | 60.5 +-25% | 62.5 | ok |
| rolls | L5 threshold bodies/h [measurement] | 79.6 +-25% | 80.0 | ok |
| rolls | L5 threshold sounds/h [measurement] | 130.8 +-25% | 129.9 | ok |
| class | L5 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L6 heartland bodies/h [measurement] | 3.6 +-36% | 2.8 | ok |
| rolls | L6 heartland sounds/h [measurement] | 12.4 +-25% | 12.0 | ok |
| rolls | L6 approach bodies/h [measurement] | 10.2 +-25% | 10.9 | ok |
| rolls | L6 approach sounds/h [measurement] | 24.4 +-25% | 25.0 | ok |
| rolls | L6 threshold bodies/h [measurement] | 30.8 +-25% | 30.4 | ok |
| rolls | L6 threshold sounds/h [measurement] | 52.8 +-25% | 55.1 | ok |
| class | L6 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L7 heartland bodies/h [measurement] | 11.3 +-25% | 10.5 | ok |
| rolls | L7 heartland sounds/h [measurement] | 36.8 +-25% | 35.7 | ok |
| rolls | L7 approach bodies/h [measurement] | 31.2 +-25% | 33.1 | ok |
| rolls | L7 approach sounds/h [measurement] | 73.5 +-25% | 70.5 | ok |
| rolls | L7 threshold bodies/h [measurement] | 96.5 +-25% | 95.5 | ok |
| rolls | L7 threshold sounds/h [measurement] | 162.9 +-25% | 165.9 | ok |
| class | L7 kinds allowed at once [decision] | 2 | 2 | ok |
| rolls | L8 heartland bodies/h [measurement] | 22.1 +-25% | 21.3 | ok |
| rolls | L8 heartland sounds/h [measurement] | 73.0 +-25% | 73.6 | ok |
| rolls | L8 approach bodies/h [measurement] | 61.2 +-25% | 63.0 | ok |
| rolls | L8 approach sounds/h [measurement] | 143.7 +-25% | 148.8 | ok |
| rolls | L8 threshold bodies/h [measurement] | 193.0 +-25% | 190.9 | ok |
| rolls | L8 threshold sounds/h [measurement] | 310.0 +-25% | 307.8 | ok |
| class | L8 kinds allowed at once [decision] | 2 | 2 | ok |
| rolls | L9 heartland bodies/h [measurement] | 36.2 +-25% | 36.0 | ok |
| rolls | L9 heartland sounds/h [measurement] | 126.7 +-25% | 123.6 | ok |
| rolls | L9 approach bodies/h [measurement] | 103.6 +-25% | 103.8 | ok |
| rolls | L9 approach sounds/h [measurement] | 262.0 +-25% | 263.2 | ok |
| rolls | L9 threshold bodies/h [measurement] | 332.1 +-25% | 331.5 | ok |
| rolls | L9 threshold sounds/h [measurement] | 569.3 +-25% | 578.0 | ok |
| class | L9 kinds allowed at once [decision] | 2 | 2 | ok |
| class | L10 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L11 heartland bodies/h [measurement] | 9.0 +-25% | 10.0 | ok |
| rolls | L11 heartland sounds/h [measurement] | 30.3 +-25% | 30.5 | ok |
| rolls | L11 approach bodies/h [measurement] | 25.6 +-25% | 25.4 | ok |
| rolls | L11 approach sounds/h [measurement] | 60.8 +-25% | 61.9 | ok |
| rolls | L11 threshold bodies/h [measurement] | 79.4 +-25% | 81.0 | ok |
| rolls | L11 threshold sounds/h [measurement] | 130.6 +-25% | 131.5 | ok |
| class | L11 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L37 heartland bodies/h [measurement] | 2.7 +-41% | 2.5 | ok |
| rolls | L37 heartland sounds/h [measurement] | 9.4 +-25% | 8.9 | ok |
| rolls | L37 approach bodies/h [measurement] | 7.8 +-25% | 7.5 | ok |
| rolls | L37 approach sounds/h [measurement] | 18.5 +-25% | 17.9 | ok |
| rolls | L37 threshold bodies/h [measurement] | 23.0 +-25% | 23.5 | ok |
| rolls | L37 threshold sounds/h [measurement] | 39.2 +-25% | 39.3 | ok |
| class | L37 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L94 approach bodies/h [measurement] | 51.7 +-25% | 53.7 | ok |
| rolls | L94 approach sounds/h [measurement] | 124.5 +-25% | 120.6 | ok |
| rolls | L94 threshold bodies/h [measurement] | 166.3 +-25% | 162.6 | ok |
| rolls | L94 threshold sounds/h [measurement] | 271.9 +-25% | 266.7 | ok |
| class | L94 kinds allowed at once [decision] | 2 | 2 | ok |
| rolls | Lfun heartland bodies/h [measurement] | 27.9 +-25% | 28.4 | ok |
| rolls | Lfun heartland sounds/h [measurement] | 94.8 +-25% | 93.6 | ok |
| rolls | Lfun approach bodies/h [measurement] | 79.1 +-25% | 78.9 | ok |
| rolls | Lfun approach sounds/h [measurement] | 185.8 +-25% | 189.1 | ok |
| rolls | Lfun threshold bodies/h [measurement] | 262.6 +-25% | 261.0 | ok |
| rolls | Lfun threshold sounds/h [measurement] | 360.3 +-25% | 358.3 | ok |
| class | Lfun kinds allowed at once [decision] | 2 | 2 | ok |
| rolls | Lend heartland bodies/h [measurement] | 2.7 +-41% | 2.5 | ok |
| rolls | Lend heartland sounds/h [measurement] | 9.2 +-25% | 8.9 | ok |
| rolls | Lend approach bodies/h [measurement] | 7.8 +-25% | 7.9 | ok |
| rolls | Lend approach sounds/h [measurement] | 18.1 +-25% | 17.5 | ok |
| rolls | Lend threshold bodies/h [measurement] | 22.9 +-25% | 24.1 | ok |
| rolls | Lend threshold sounds/h [measurement] | 39.3 +-25% | 37.7 | ok |
| class | Lend kinds allowed at once [decision] | 1 | 1 | ok |
| class | Lhub kinds allowed at once [decision] | 1 | 1 | ok |
| class | L974 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L3999 threshold bodies/h [measurement] | 121.6 +-25% | 122.0 | ok |
| rolls | L3999 threshold sounds/h [measurement] | 190.8 +-25% | 192.2 | ok |
| class | L3999 kinds allowed at once [decision] | 1 | 1 | ok |
| rolls | L188 heartland bodies/h [measurement] | 10.8 +-25% | 11.6 | ok |
| rolls | L188 heartland sounds/h [measurement] | 36.4 +-25% | 35.8 | ok |
| rolls | L188 approach bodies/h [measurement] | 30.9 +-25% | 31.3 | ok |
| rolls | L188 approach sounds/h [measurement] | 72.8 +-25% | 71.6 | ok |
| rolls | L188 threshold bodies/h [measurement] | 95.4 +-25% | 96.8 | ok |
| rolls | L188 threshold sounds/h [measurement] | 162.1 +-25% | 161.9 | ok |
| class | L188 kinds allowed at once [decision] | 2 | 2 | ok |
| class | L! kinds allowed at once [decision] | 1 | 1 | ok |
| danger | L0 danger | 0.00 | 0.00 | ok |
| armour | L0 smiler vs none: hit / blows [measurement] | 6.00 / 2.5 | 6.00 / 2.5 | ok |
| armour | L0 smiler vs sewn-leather: hit / blows [measurement] | 2.79 / 5.4 | 2.79 / 5.4 | ok |
| armour | L0 smiler vs lamellar-tinbronze: hit / blows [measurement] | 2.23 / 6.7 | 2.23 / 6.7 | ok |
| armour | L0 smiler vs plate-iron: hit / blows [measurement] | 0.57 / 26.3 | 0.57 / 26.3 | ok |
| danger | L1 danger | 0.12 | 0.12 | ok |
| armour | L1 deathrat vs none: hit / blows [measurement] | 1.36 / 11.0 | 1.36 / 11.0 | ok |
| armour | L1 deathrat vs sewn-leather: hit / blows [measurement] | 0.30 / 49.4 | 0.30 / 49.4 | ok |
| armour | L1 deathrat vs lamellar-tinbronze: hit / blows [measurement] | 0.17 / 86.0 | 0.17 / 86.0 | ok |
| armour | L1 deathrat vs plate-iron: hit / blows [measurement] | 0.00 / never | 0.00 / never | ok |
| danger | L2 danger | 0.24 | 0.24 | ok |
| armour | L2 smiler vs none: hit / blows [measurement] | 7.58 / 2.0 | 7.58 / 2.0 | ok |
| armour | L2 smiler vs sewn-leather: hit / blows [measurement] | 3.58 / 4.2 | 3.58 / 4.2 | ok |
| armour | L2 smiler vs lamellar-tinbronze: hit / blows [measurement] | 2.84 / 5.3 | 2.84 / 5.3 | ok |
| armour | L2 smiler vs plate-iron: hit / blows [measurement] | 0.77 / 19.6 | 0.77 / 19.6 | ok |
| danger | L3 danger | 0.36 | 0.36 | ok |
| armour | L3 hound vs none: hit / blows [measurement] | 9.10 / 1.6 | 9.10 / 1.6 | ok |
| armour | L3 hound vs sewn-leather: hit / blows [measurement] | 3.92 / 3.8 | 3.92 / 3.8 | ok |
| armour | L3 hound vs lamellar-tinbronze: hit / blows [measurement] | 2.40 / 6.3 | 2.40 / 6.3 | ok |
| armour | L3 hound vs plate-iron: hit / blows [measurement] | 0.74 / 20.4 | 0.74 / 20.4 | ok |
| danger | L4 danger | 0.44 | 0.44 | ok |
| armour | L4 duller vs none: hit / blows [measurement] | 4.00 / 3.8 | 4.00 / 3.8 | ok |
| armour | L4 duller vs sewn-leather: hit / blows [measurement] | 1.41 / 10.6 | 1.41 / 10.6 | ok |
| armour | L4 duller vs lamellar-tinbronze: hit / blows [measurement] | 0.88 / 17.0 | 0.88 / 17.0 | ok |
| armour | L4 duller vs plate-iron: hit / blows [measurement] | 0.16 / 91.0 | 0.16 / 91.0 | ok |
| danger | L5 danger | 0.52 | 0.52 | ok |
| armour | L5 hound vs none: hit / blows [measurement] | 10.08 / 1.5 | 10.08 / 1.5 | ok |
| armour | L5 hound vs sewn-leather: hit / blows [measurement] | 4.37 / 3.4 | 4.37 / 3.4 | ok |
| armour | L5 hound vs lamellar-tinbronze: hit / blows [measurement] | 2.67 / 5.6 | 2.67 / 5.6 | ok |
| armour | L5 hound vs plate-iron: hit / blows [measurement] | 0.83 / 18.1 | 0.83 / 18.1 | ok |
| danger | L6 danger | 0.60 | 0.60 | ok |
| danger | L7 danger | 0.66 | 0.66 | ok |
| armour | L7 thething vs none: hit / blows [measurement] | 12.98 / 1.2 | 12.98 / 1.2 | ok |
| armour | L7 thething vs sewn-leather: hit / blows [measurement] | 5.08 / 3.0 | 5.08 / 3.0 | ok |
| armour | L7 thething vs lamellar-tinbronze: hit / blows [measurement] | 3.16 / 4.7 | 3.16 / 4.7 | ok |
| armour | L7 thething vs plate-iron: hit / blows [measurement] | 0.78 / 19.2 | 0.78 / 19.2 | ok |
| danger | L8 danger | 0.74 | 0.74 | ok |
| armour | L8 wretch vs none: hit / blows [measurement] | 9.63 / 1.6 | 9.63 / 1.6 | ok |
| armour | L8 wretch vs sewn-leather: hit / blows [measurement] | 4.16 / 3.6 | 4.16 / 3.6 | ok |
| armour | L8 wretch vs lamellar-tinbronze: hit / blows [measurement] | 2.54 / 5.9 | 2.54 / 5.9 | ok |
| armour | L8 wretch vs plate-iron: hit / blows [measurement] | 0.79 / 19.1 | 0.79 / 19.1 | ok |
| danger | L9 danger | 0.82 | 0.82 | ok |
| armour | L9 hound vs none: hit / blows [measurement] | 15.84 / 0.9 | 15.84 / 0.9 | ok |
| armour | L9 hound vs sewn-leather: hit / blows [measurement] | 7.66 / 2.0 | 7.66 / 2.0 | ok |
| armour | L9 hound vs lamellar-tinbronze: hit / blows [measurement] | 6.01 / 2.5 | 6.01 / 2.5 | ok |
| armour | L9 hound vs plate-iron: hit / blows [measurement] | 1.79 / 8.4 | 1.79 / 8.4 | ok |
| danger | L10 danger | 0.88 | 0.88 | ok |
| danger | L11 danger | 0.95 | 0.95 | ok |
| armour | L11 deathrat vs none: hit / blows [measurement] | 3.12 / 4.8 | 3.12 / 4.8 | ok |
| armour | L11 deathrat vs sewn-leather: hit / blows [measurement] | 1.05 / 14.3 | 1.05 / 14.3 | ok |
| armour | L11 deathrat vs lamellar-tinbronze: hit / blows [measurement] | 0.66 / 22.6 | 0.66 / 22.6 | ok |
| armour | L11 deathrat vs plate-iron: hit / blows [measurement] | 0.10 / 143.4 | 0.10 / 143.4 | ok |
| danger | L37 danger | 0.50 | 0.50 | ok |
| danger | L94 danger | 0.40 | 0.40 | ok |
| armour | L94 animation-clay vs none: hit / blows [measurement] | 5.19 / 2.9 | 5.19 / 2.9 | ok |
| armour | L94 animation-clay vs sewn-leather: hit / blows [measurement] | 1.90 / 7.9 | 1.90 / 7.9 | ok |
| armour | L94 animation-clay vs lamellar-tinbronze: hit / blows [measurement] | 1.19 / 12.6 | 1.19 / 12.6 | ok |
| armour | L94 animation-clay vs plate-iron: hit / blows [measurement] | 0.25 / 60.7 | 0.25 / 60.7 | ok |
| danger | Lfun danger | 0.90 | 0.90 | ok |
| danger | Lend danger | 0.40 | 0.40 | ok |
| danger | Lhub danger | 0.00 | 0.00 | ok |
| danger | L974 danger | 0.00 | 0.00 | ok |
| danger | L3999 danger | 0.80 | 0.80 | ok |
| armour | L3999 smiler vs none: hit / blows [measurement] | 12.53 / 1.2 | 12.53 / 1.2 | ok |
| armour | L3999 smiler vs sewn-leather: hit / blows [measurement] | 6.53 / 2.3 | 6.53 / 2.3 | ok |
| armour | L3999 smiler vs lamellar-tinbronze: hit / blows [measurement] | 5.97 / 2.5 | 5.97 / 2.5 | ok |
| armour | L3999 smiler vs plate-iron: hit / blows [measurement] | 2.13 / 7.1 | 2.13 / 7.1 | ok |
| danger | L188 danger | 0.45 | 0.45 | ok |
| armour | L188 skinstealer vs none: hit / blows [measurement] | 14.21 / 1.1 | 14.21 / 1.1 | ok |
| armour | L188 skinstealer vs sewn-leather: hit / blows [measurement] | 6.24 / 2.4 | 6.24 / 2.4 | ok |
| armour | L188 skinstealer vs lamellar-tinbronze: hit / blows [measurement] | 3.80 / 3.9 | 3.80 / 3.9 | ok |
| armour | L188 skinstealer vs plate-iron: hit / blows [measurement] | 1.23 / 12.2 | 1.23 / 12.2 | ok |
| danger | L! danger | 0.90 | 0.90 | ok |
| anchor | smiler L3 none [decision] | 2 to 3 blows | 2.0 blows (2) | ok |
| anchor | smiler L8 none [decision] | 1 to 2 blows | 1.4 blows (2) | ok |
| anchor | smiler L3 sewn-leather [decision] | <= 0.60 x the unarmoured blow | 0.47 x | ok |
| anchor | smiler L8 lamellar-tinbronze [decision] | >= 3 blows even on the worst piece | 3 | ok |
| anchor | smiler L9 plate-iron [decision] | >= 3 blows even on the worst piece | 7 | ok |
| scarcity | L0 class scale | 1 | (no dummy placed here) | not measured |
| felt | L1 approach felt/h [measurement] | 18.3 +-45% | 13.3 (mean of 14.8, 11.8) | ok |
| scarcity | L1 class scale [decision] | 1 | 1 | ok |
| felt | L2 approach felt/h [measurement] | 20.4 +-45% | 22.0 (mean of 20.2, 23.9) | ok |
| scarcity | L2 class scale [decision] | 0.7 | 0.7 | ok |
| felt | L3 approach felt/h [measurement] | 42.8 +-45% | 44.1 (mean of 45.9, 42.3) | ok |
| scarcity | L3 class scale [decision] | 0.5 | 0.5 | ok |
| scarcity | L4 class scale | 1 | (no dummy placed here) | not measured |
| felt | L5 approach felt/h [measurement] | 20.1 +-45% | 22.1 (mean of 25.1, 19.2) | ok |
| scarcity | L5 class scale [decision] | 1 | 1 | ok |
| scarcity | L6 class scale | 1 | (no dummy placed here) | not measured |
| scarcity | L7 class scale | 0.5 | (no dummy placed here) | not measured |
| felt | L8 approach felt/h [measurement] | 37.6 +-55% | 42.5 (mean of 37.0, 48.1) | ok |
| scarcity | L8 class scale [decision] | 0.5 | 0.5 | ok |
| felt | L9 approach felt/h [measurement] | 89.7 +-55% | 89.7 (mean of 91.5, 87.8) | ok |
| scarcity | L9 class scale [decision] | 0.35 | 0.35 | ok |
| scarcity | L10 class scale | 1 | (no dummy placed here) | not measured |
| scarcity | L11 class scale | 1 | (no dummy placed here) | not measured |
| scarcity | L37 class scale | 1 | (no dummy placed here) | not measured |
| scarcity | L94 class scale | 1 | (no dummy placed here) | not measured |
| scarcity | Lfun class scale | 0.35 | (no dummy placed here) | not measured |
| scarcity | Lend class scale | 1 | (no dummy placed here) | not measured |
| scarcity | Lhub class scale | 1 | (no dummy placed here) | not measured |
| scarcity | L974 class scale | 1 | (no dummy placed here) | not measured |
| scarcity | L3999 class scale | 1 | (no dummy placed here) | not measured |
| scarcity | L188 class scale | 0.7 | (no dummy placed here) | not measured |
| scarcity | L! class scale | 1 | (no dummy placed here) | not measured |
| shortcuts | L1 stair cores to Fun | 4 +-15% (min 2) | 4 | ok |
| shortcuts | L1 stair flights down (to L2: 1 in 4 of the bottom floor's) | 292 +-15% (min 2) | 292 | ok |
| shortcuts | L1 stair flights up (to L4: from the top floors) | 288 +-15% (min 2) | 288 | ok |
| shortcuts | L2 steel doors: locked | 397 +-15% (min 2) | 397 | ok |
| shortcuts | L2 steel doors: open to L1 | 30 +-15% (min 2) | 30 | ok |
| shortcuts | L2 steel doors: open to L3 | 15 +-15% (min 2) | 15 | ok |
| shortcuts | L2 steel doors: open to L4 | 6 +-15% (min 2) | 6 | ok |
| shortcuts | L3 elevators: to L3 (same level) | 115 +-15% (min 2) | 115 | ok |
| shortcuts | L3 elevators: to L4 | 16 +-15% (min 2) | 16 | ok |
| shortcuts | L3 elevators: to L5 | 10 +-15% (min 2) | 10 | ok |
| shortcuts | L4 elevators: to L3 | 24 +-15% (min 2) | 24 | ok |
| shortcuts | L4 elevators: to L4 (same level) | 107 +-15% (min 2) | 107 | ok |
| shortcuts | L4 elevators: to L5 | 22 +-15% (min 2) | 22 | ok |
| shortcuts | L6 tripwires | 42 +-15% (min 2) | 42 | ok |
| shortcuts | L7 cave mouths | 11 +-15% (min 2) | 11 | ok |
| shortcuts | L7 stone circles | 3 +-15% (min 2) | 3 | ok |
| shortcuts | L7 tiled seabeds | 2 +-15% (min 2) | 2 | ok |
| shortcuts | placards on L1 floors (plate 0) | 3 +-15% (min 2) | 3 | ok |
| shortcuts | placards on L1 floors (plate 1) | 1 +-15% (min 2) | 1 | ok |
| shortcuts | placards on L2 floors (plate 0) | 4 +-15% (min 2) | 4 | ok |
| shortcuts | placards on L2 floors (plate 1) | 17 +-15% (min 2) | 17 | ok |
| shortcuts | placards on L3 floors (plate 1) | 10 +-15% (min 2) | 10 | ok |
| shortcuts | placards on L4 floors (plate 1) | 32 +-15% (min 2) | 32 | ok |
| shortcuts | placards on L5 floors (plate 1) | 96 +-15% (min 2) | 96 | ok |
| shortcuts | placards on L6 floors (plate 2) | 8 +-15% (min 2) | 8 | ok |
| shortcuts | placards on L7 floors (plate 2) | 5 +-15% (min 2) | 5 | ok |

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
