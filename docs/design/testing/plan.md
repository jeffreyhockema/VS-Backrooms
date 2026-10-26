# Testing stack: less play-testing, same quality

Written 2026-10-25 from the user's note ("so many things need testing after our changes; how far can we push past
human testing without degrading the output; I want to keep using my computer") and their answers the same evening.
Branch `testing`, worktree `../VS Backrooms-testing`. Lives beside the harness docs in DEVELOPING.md.

## 1. Decisions

| # | Decision |
|---|---|
| 1 | Five layers, cheapest first: the one-command **gate**, a **balance spec** as data, **telemetry** of the user's own play with an F8 marker, **scripted client batches** on this PC with the game window off-screen, **simulated players** headless |
| 2 | Order: telemetry and gate first, then the client rig, then the spec, then simulated players |
| 3 | Client batches run on this PC: the client is a multiplayer client of a dedicated test server (so losing focus never pauses it), its window is moved off-screen and never minimized (a minimized window stops rendering and the screenshot comes back empty), keyboard focus is handed back to the shell. Verified 2026-10-25 22:53: the game's own screenshot works off-screen and unfocused |
| 4 | Telemetry: a local JSON Lines event log in the game's data folder, never sent anywhere; F8 marks a moment, `.mark <text>` adds words |
| 5 | The gate runs on demand after every merge (about 30 to 40 minutes), not scheduled |
| 6 | The balance spec: the overseer proposes numbers from today's measurements and the user's past calls; the user approves; the gate asserts |
| 7 | Humans keep the exploratory play and the "does it feel right"; everything repeatable moves down the stack |

## 2. The layers

### 2.1 Gate (`tools/gate.py`)

Generators' checks, lang files, build, boot smoke (missing blocks/items, errors), every harness group with one rerun of
failures, mapgen validation and layout hashes against `tools/gate.hashes.json`, the shortcut counts, an old-world load
from a configured save copy, optionally the zip. One report under `review/gate/`. Non-zero exit on any failure.

### 2.2 Telemetry (`src/Telemetry/`, `tools/telemetry/report.py`)

Events: session, level and band changes, every director spawn and kind change, first contact, damage, death, respawn,
stability thresholds and zero, blackout, needs thresholds and sleep, eat/drink, loot opened, trades, notes, class
crossings, marks (with the last minute of events and what is about). The report gives per-level felt rates, time to
first encounter, damage by source, supplies per hour, loot per distance, a timeline of marks.

### 2.3 Client rig (`tools/clientrig/`)

- A driver starts a dedicated server on its own data dir and port with a stdin pipe (so it can `/op` the player, set
  time, run `/backrooms` commands), launches `Vintagestory.exe --dataPath <rig data> --addModPath <mods> -c
  localhost:<port>` with the shotbot beside the mod, moves the window off-screen (`SetWindowPos` to x = -4000, no
  activate; `ShowWindow` SW_SHOWNOACTIVATE if minimized) and hands focus to the shell, then runs a **scenario**: a list
  of bot lines (shotbot's commands: cmd, tp, look, shot, waitchat, movewait, mark) and server console lines, with
  checks (a chat line contains, a screenshot exists, a log line appears, a telemetry event happened).
- Scenarios cover what the headless harness cannot: the client boot log has no captured issues (today's trial found a
  client-only crash in `Breakdown.FindOwnDrops`, fixed on `fix/client-drops`), HUD and chat lines (the class crossing),
  the placards' look and facing, real armour worn and hits taken, the vanilla stability clock in a pocket and the
  blackout, respawn at a bed, scarcity in opened caches, the handbook pages rendering. The screenshots are read by the
  overseer; a contact sheet per scenario goes under `review/clientrig/<date>/`.
- The user's own account is used on the local server (the client's settings are copied from the user's); nothing
  touches the user's saves.
- Known limits: GPU and sound are shared with the user's session (mute the rig client via its clientsettings); a
  focus-stealing launch happens once per batch; console windows of other tools must not be launched while a batch
  runs (they take focus but the multiplayer client does not pause, so this is now only cosmetic).

### 2.4 Balance spec (`docs/design/balance-spec.yaml`)

Per level and band: felt bodies per hour, sounds per hour, hits to kill per armour set, time to first encounter,
supplies per 1000 blocks, shortcut density, class and solitude. `tools/gate.py` asserts it (a scorecard stage) and
`tools/telemetry/report.py --compare` grades real sessions against it.

### 2.5 Simulated players (`tools/aitest` walkers)

Straw dummies that walk a route gate to gate with hunger, health and an armour inventory, taking the director's
encounters and logging through the telemetry; a headless two-hour session per level, reported like a real one.

## 3. Status

| Layer | Branch | State |
|---|---|---|
| Gate | testing/gate | building |
| Telemetry | testing/telemetry | building |
| Client rig | testing/clientrig | building (trial done by hand 2026-10-25) |
| Balance spec | | after the above |
| Simulated players | | after the above |
