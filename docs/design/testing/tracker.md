# Testing tooling: tracker

One section per tool built for the human play-tests, appended by its worker.

### Telemetry

Branch `testing-telemetry` (the name `testing/telemetry` was impossible: a branch called `testing` exists), off `testing` at 889d453. Worktree `VS Backrooms-testing-telemetry`.

- Built: `src/Telemetry/TelemetrySystem.cs` (server event log plus the F8 / `/backrooms mark` marker on the client), one-line hooks in MenaceSystem (spawn), EntityBehaviorMenace (kind, contact), ZeroSystem (blackout), CrossingSystem (cross), NoteSystem (note); `tools/telemetry/report.py`; docs in DEVELOPING.md ("Play telemetry") and GUIDE.md.
- Checked headless on port 42795: session, spawn, kind and mark events from a straw dummy (`/backrooms mark` from the console marks the latest dummy), report.py on that file and on a synthetic player file, harness `--only iso` 2/2.
- Not checked without a real client: F8 and `.mark`, damage, death, eat and drink, loot, trade, contact, needs, stability, level and pos events (they need a player).
- Left for later: `--compare` against `docs/design/balance-spec.yaml` (stub in `compare()`).
- Blind review (sonnet): fixed the logger-thread trade parse (queued, drained on the tick), throttle exemptions for level/stab/need/damage, layout version read without writing config, damage hook retry/rejoin, spawn/kind arguments guarded by `Telemetry.On`, rates pruned on leave, report.py respawn/join/dummy handling. Left: F8 needs the `controlserver` privilege (it is a `/backrooms` subcommand), loot detection is by block name, eat/drink counts are lower bounds, report time-to-first-encounter is spawn-based wall clock.
