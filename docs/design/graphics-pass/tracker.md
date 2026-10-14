# Graphics pass: tracker

Status of every batch in the [plan](README.md). Workers append their report under their batch; the overseer
records the gate decision. Keep entries short; the sheets and the diff carry the detail.

## Lessons (read before every batch)

Things later batches inherit. Add a line when you learn one; do not remove lines.

- The shotbot's `look` was 180 degrees off before B0 (compass heading h is yaw pi - h, not -h); fixed in
  `ShotBot.cs`. Headings in spot lists, `pick.py` and `/backrooms nearest` replies are now what the shots face.
- VS 1.22 has no `/time set noon` ("Unable to convert noon"): use `/time set 12:00`. Each `/time set` also jumps to the
  next day once the hour has passed, so a long batch walked the calendar through months. `batch.py`'s header now does
  `/time setmonth jun`, `/time set 12:00`, `/time stop`; with that, an indoor retake of the same build is pixel-identical.
  Do not compare shots taken under the old header (anything before 2026-10-13 17:00) with new ones.
- Outdoors (Levels 9, 10, 11, 94) grass, crops and leaves sway, so even a retake of the same build differs by about
  5-10% of the frame there (`compare.py --stats`). Judge them by eye, not by the numbers.
- Never run `mkspots.py make` or the harness while a batch shoots: it starts `mapgen.exe`. Build or remake lists between
  runs. A client run of about 170 spots takes 25 minutes.
- Shell heredocs passed through the agent's Bash tool turn an escaped `\n` (a doubled backslash) into a real newline; write files that contain backslash
  escapes with the Write/Edit tools.

## Batches

| Batch | Branch | Status | Rounds | Below B carried | Gate |
|---|---|---|---|---|---|
| B0 tooling and baseline | gfx/B0 | merged | 1 | | passed 2026-10-13 (Fable): tram/close/prop shots verified, no asset changes |
| B1 inventory | main | in progress | | | |
| B2 material kit | | not started | | | |
| B3 Level 0 | | not started | | | |
| B4 Level 1 | | not started | | | |
| B5 Level 2 | | not started | | | |
| B6 Level 3 | | not started | | | |
| B7 Level 4 | | not started | | | |
| B8 Level 5 | | not started | | | |
| B9 Levels 6 and 6.1 | | not started | | | |
| B10 Levels 7 and 8 | | not started | | | |
| B11 Levels 9 and 10 | | not started | | | |
| B12 Level 11 | | not started | | | |
| B13 Levels 37 and 94 | | not started | | | |
| B14 Level ! and Fun | | not started | | | |
| B15 The End and The Hub | | not started | | | |
| B16 974, 3999, 188 | | not started | | | |
| B17 entities and items | | not started | | | |
| B18 finish | | not started | | | |

Status values: not started, in progress, review, sent back, merged.

## Reports

### B0

Worker report (Opus, 2026-10-13). Branch `gfx/B0`, uncommitted. Nothing under `assets/` changed and no generator ran.

**Tools built**
- `tools/texsheet.py`: textures at 4x nearest-neighbour, with the file name and size under each, vanilla `--ref`s
  framed in gold in the first row, `--tile` for 3x3 repeats, `--per-page` paging, and `--all --out <dir>`, which does
  every texture folder with its vanilla counterparts (`FOLDER_REFS`: cobblestone, andesite brick, oak planks, wool,
  carpet, plaster, iron/copper plates, walnut wallpaper).
- `tools/preview_shapes.py`: now maps the real textures onto the faces through each face's UV (or the auto UV the game
  would give it), with element rotations and child elements. The first version ignores a face's own `rotation`, reads
  textures from the shape only (not blocktype overrides), and sorts faces by mean depth. `--flat` gives the old
  average-colour mode.
- `tools/shotbot/batch.py`: does the whole run from spot lists, as in README section 4: it sets up the data dir, makes
  the world with a dedicated server at the fixed seed if missing, copies the shotbot beside the mod, writes
  commands.txt, launches, waits, copies out JPEGs and `sheet.jpg`, and closes the client with `/stop`. Several lists go
  in one launch, into `--out/<list>/`. `--only` takes name patterns.
- `tools/shotbot/compare.py`: puts before above a magenta line and after below, one column per spot, in bands of 6.
  `--stats` prints how much each pair differs (the repeatability check).
- `tools/shotbot/mkspots.py`: `discover` runs every `/backrooms nearest` target from each level's anchor in the client
  and records the replies and positions. `make` writes the lists. Its harness side is `tools/mapgen/ShotGrid.cs`: the
  `shotgrid <level> [x z]` mode dumps tiles plus feet height around a level's first arrival, and `feet x z...` gives
  heights for given columns.
- `ShotBot.cs`: heading fix (see lessons), a `mark name` command (position to marks.txt), `waitchat` (waits for a
  command's reply), and the spawn added to ready.txt.
- Docs: `docs/DEVELOPING.md`, in the "Unattended screenshots" bullet and the Assets list. The "Keeping saves working"
  section was kept. `.gitignore`: `/review/`, `tools/shotbot/out/`, `tools/shotbot/harness/`.

**Review world**
- Seed **1672613597**, sea level 216, spawn 512016.5 217 512016.5, layout version 6.
- Data dir `%LOCALAPPDATA%\backrooms-gfxreview` (582 MB); world `Saves/gfxreview.vcdbs`.
- Mods: `%TEMP%\backrooms-build\build-gfx\Mods` (`backroomsss` from `main` plus `shotbot`).
- Shots are 1920x1080 at FOV 70 and view distance 256, in creative mode with the director paused, at 12:00 on a June day
  with the clock stopped.

**Spot lists**
Lists are in `review/spots/<level>.json` and `docs/design/graphics-pass/spots/`, with `discovery.json` beside them.
There are 499 spots in all, each an absolute `tp`.

| level | spots | wide | close | prop | targets (wide+close) | inspection |
|---|---|---|---|---|---|---|
| 0 | 25 | 8 | 4 | 1 | 12: cache, den, gate, redroom, refuge, threshold | |
| 1 | 31 | 8 | 5 | 2 | 16: cache, den, gate, pipeend, refuge, sleepingbag, tent, threshold | |
| 2 | 28 | 8 | 4 | 2 | 14: cache, den, gate, pipecorner, pipeend, pipewrap, tram | |
| 3 | 34 | 8 | 4 | 2 | 20: cache, den, gate, pipecorner, pipeend, pipewrap, purpified, refuge, sleepingbag, threshold | |
| 4 | 27 | 8 | 5 | 2 | 12: cache, gate, hotelturn, refuge, sleepingbag, threshold | |
| 5 | 31 | 8 | 5 | 2 | 16: cache, den, door666, fronthall, gate, refuge, sleepingbag, threshold | |
| 6 | 32 | 8 | 3 | 2 | 8: gate, refuge (a Snackrooms cell), sleepingbag, threshold | 11 |
| 6.1 | 24 | 8 | 4 | 2 | 10: gate, refuge, sleepingbag, threshold, vendingroom | |
| 7 | 34 | 8 | 2 | 0 | 12: cache, gate, seapillar, shelter, sleepingbag, tent | 12 |
| 8 | 25 | 8 | 3 | 2 | 12: cache, den, glowcaps, refuge, sleepingbag, tent | |
| 9 | 28 | 8 | 4 | 2 | 14: cache, citysign, den, l9house, l9stairs, sleepingbag, streetname | |
| 10 | 14 | 8 | 2 | 2 | 2: fieldthing | |
| 11 | 22 | 8 | 4 | 2 | 8: adpillar, billboard, refuge, threshold | |
| 37 | 14 | 8 | 4 | 2 | none belong | |
| 94 | 15 | 8 | 3 | 2 | 2: castle | |
| run | 15 | 8 | 3 | 2 | 2: runhall | |
| fun | 17 | 8 | 5 | 2 | 2: funparty | |
| end | 18 | 8 | 4 | 2 | 4: endexit, endwall | |
| hub | 11 | 8 | 3 | 0 | none belong | |
| 974 | 15 | 8 | 5 | 2 | none belong | |
| 3999 | 21 | 8 | 5 | 2 | 6: cache, foodcourt, neoncorner | |
| 188 | 18 | 8 | 4 | 2 | 4: courtdoor, downpipe | |

What the columns mean:
- **wide**: `pick.py`'s scoring on the harness grid round the level's anchor. Levels whose rooms are too small for
  pick.py's 10-block rays (974, the Snackrooms) fall back to the longest views there are.
- **close**: the commonest wall pattern (and the second where there is one), the floor, the plain ceiling, a ceiling
  light, and water where there is much of it. All are from 1.5 blocks.
- **prop**: an extra kind. It shows the two commonest floor props from 1.5 blocks.
- **targets**: every target the command found from the anchor within its default radius. Two needed a bigger radius
  (`RADIUS` in mkspots.py: Level 3's pipeend at 1024, 6.1's vendingroom at 256). Objects are shot from about 6 and
  2 blocks, looking at the object. Views (castle, billboard, downpipe, runhall, funparty, hotelturn, fronthall,
  door666, endexit, foodcourt) keep the command's own spot and heading, and their `-close` narrows the FOV to 35.
  Where no nearer spot to stand exists, `-close` keeps the wide spot at FOV 40.
- **Open sky** (9, 10, 11, 94): these levels also get `"pre": ["/time set 12:00"]`.
- **Inspection** (Levels 6 and 7): wide-01..04, every close-up and every target close shot are taken again with
  `daylight` and a lantern in hand.

**Baseline**
- `review/baseline/<level>/` holds the shots and `sheet.jpg` for every level: 499 shots, none missing. All were taken
  under the final header, with the clock stopped.
- `review/baseline/texsheets/`: 177 sheets covering all 31 texture folders that hold PNGs, plain at 48 per page
  (`<folder>-N.png`) and tiled at 24 per page (`<folder>-tile-N.png`). Each has its vanilla references.
- `review/baseline/props/`: 42 textured preview sheets of every block shape folder, 48 per page.
- Logs are `review/baseline-*.log`. Runs A-D were superseded by E-G after the time fix; only E-G and repeat2 are in
  the baseline.

**Repeatability**
- Levels 0 and 10 were shot twice under the same build and header: `review/repeat/` vs `review/repeat2/`, with
  `compare-0.jpg` and `compare-10.jpg` in repeat2.
- Level 0: all 25 spots line up pixel for pixel (`--stats` mean difference 0.0-0.4 out of 255, 0% of the frame moved).
- Level 10: every spot has the same framing by eye (the offset was measured as 0,0 only for Level 0). They differ by mean 4-26 because the wind
  moves the crops, grass and leaves. close-wall (a hedge) is the worst at 26.
- Before the clock was stopped, the same Level 0 spots differed in light by up to 45 (A vs the repeat). That is why
  the whole baseline was retaken.

**Not done / for later batches**
- `/backrooms nearest` found no target for 37, hub or 974, and none of the generic ones in the far places except a cache in 3999. The
  generic targets are missing in some levels too, e.g. no tent in 0 and no cache in 6 near the anchor; see
  `discovery.json`.
- Some frames are weak:
  - Level 7 and parts of 2 and 6 are dark by design; the inspection shots cover 6 and 7.
  - Level 974's eight wide shots are eight houses with the same plan.
  - A few wide shots open on a near wall (e.g. Level 7 wide-01, Level 94 wide-04).
  - Level 2's close shots often have the wall pipes in front.
  - B1 can name spots to add; `mkspots.py make <level>` regenerates a list without the client.
- `preview_shapes.py` ignores face rotation (see above).
