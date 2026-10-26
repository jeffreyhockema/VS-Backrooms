# Testing stack tracker

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
