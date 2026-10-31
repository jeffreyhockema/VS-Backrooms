# Experimental levels (branch `experimental-levels`)

Eight prototype levels, built cheaply to try out ideas. They are **disconnected**: no thresholds in or out, no
entities, no notes, no handbook text. The only way in is the cheats menu (F7) or
`/backrooms goto 73|basement|52|31|120|36|15|23`. If an idea works, it gets a proper pass (lore polish, entrances,
dangers) later; if not, its commits are dropped.

This branch is not meant to merge into `main` for a long time. Each level is its own commit after the shared
scaffolding commit, so one can be cherry-picked or reverted on its own. Levels 55 and 183 were built in batch 2 and
dropped on 2026-10-30 (their plans are in `dropped/`); their ids 25 and 27 now hold Levels 36 and 15.

| Level | Internal id | Constant | Shown as | Tag (files, block codes) | Method infix | Region |
|---|---|---|---|---|---|---|
| Level 73 "The Redlands" | 21 | `WorldLayout.Level73` | `73` | 73 (`l73-`) | `L73` | north-north-west, mirror of Level 188: `R * 1.1` out, 22.5 degrees west of north; open sky |
| The Basement (unnumbered) | 22 | `WorldLayout.Basement` | `Basement` | basement (`basement-`) | `Basement` | south-south-west: `R * 1.1` out, 22.5 degrees west of south |
| Level 52 "School Halls" | 23 | `WorldLayout.Level52` | `52` | 52 (`l52-`) | `L52` | south-south-east: `R * 1.1` out, 22.5 degrees east of south |
| Level 31 "Roller Rink" | 24 | `WorldLayout.Level31` | `31` | 31 (`l31-`) | `L31` | west-north-west: `R * 1.1` out, 22.5 degrees north of west |
| Level 36 "Airport" | 25 | `WorldLayout.Level36` | `36` | 36 (`l36-`) | `L36` | west-south-west: `R * 1.1` out, 22.5 degrees south of west (Level 55's old slot); big indoor level |
| Level 120 "Server Room" | 26 | `WorldLayout.Level120` | `120` | 120 (`l120-`) | `L120` | far north-east beyond Level Fun: `spawn + (+F, -F)`, `F = round(R * 1.6 / sqrt 2)` |
| Level 15 "Futuristic Halls" | 27 | `WorldLayout.Level15` | `15` | 15 (`l15-`) | `L15` | far north-west beyond the End: `spawn + (-F, -F)` (Level 183's old slot); big indoor level |
| Level 23 "Petrified Garden" | 28 | `WorldLayout.Level23` | `23` | 23 (`l23-`) | `L23` | far south-west beyond Level 974: `spawn + (-F, +F)`; open sky (`IsOpenSky`), a landscape of stone trees |

All are round noclip regions (like 37/94/188), radius `max(40, spawnMacroX / 50)` unless the level's plan says
otherwise. `R = RegionReach` (see `docs/design/new-levels/CONTRACT.md`, which this branch follows: same hooks, same
file naming, same rules for shared files). Level 23 = 28 is the last id: every `>= RunLevel && <= ...` name check ends
at `WorldLayout.Level23`.

## Reserved values (2026-10-30; supersedes every older table in this folder)

`WallPattern`, `FloorKind`, `CeilingKind` and `Tile.Under` / `Overhead` / `Pipe` are ushorts since commit `d43628e`
(0.700.0-pre.1), and `Decor` values may pass 255. **Each level owns one block of 32 past 255 in every one of those
tables** (block `k` = `256 + 32k` to `287 + 32k`, `k` in the order of the columns), Props one block of 100. Values a
level kept from before the widening are listed as "kept": they are the level's too, but put new values in the block.
`Tiles.cs` has each level's `<N>First/<N>Last` (Unders, Overheads, Pipes, Props, Decor) and placeholder enum members.
Every `Limit` is one past the last block (Unders, Overheads, Pipes, Decor 512; Props 1500); the generator's tables are
sized by them (`floorIds` by the largest `FloorKind`; `decorIds` makes a pattern's row only when a decoration is
registered on it).

| Range | 73 | Basement | 52 | 31 | 120 | 36 | 15 | 23 |
|---|---|---|---|---|---|---|---|---|
| `WallPattern` | 256-287 | 288-319 | 320-351 (kept 224) | 352-383 (kept 240) | 384-415 (kept 242) | 416-447 | 448-479 | 480-511 |
| `FloorKind` | 256-287 | 288-319 (kept 228-231) | 320-351 (kept 244-248) | 352-383 (kept 249) | 384-415 (kept 251) | 416-447 | 448-479 | 480-511 |
| `CeilingKind` | 256-287 | 288-319 | 320-351 (kept 88) | 352-383 (kept 96) | 384-415 (kept 112) | 416-447 | 448-479 | 480-511 |
| `Unders` | 256-287 | 288-319 | 320-351 | 352-383 | 384-415 | 416-447 | 448-479 | 480-511 |
| `Overheads` | 256-287 | 288-319 | 320-351 | 352-383 (kept 140-149: `L31Legacy`) | 384-415 (kept 160-169: `L120Legacy`) | 416-447 | 448-479 | 480-511 |
| `Pipes` | 256-287 | 288-319 | 320-351 | 352-383 | 384-415 (kept 140-149: `L120Legacy`) | 416-447 | 448-479 | 480-511 |
| `Decor` (wall decorations) | 256-287 | 288-319 | 320-351 | 352-383 | 384-415 | 416-447 | 448-479 | 480-511 |
| `Props` (`Tile.Variant`) | 900-999 | 1000-1099 | 1100-1199 | 700-799 | 800-899 | 1200-1299 | 1300-1399 | 1400-1499 |
| Title keys (`level-<key>`) | 2101-2199 | 2201-2299 | 2301-2399 | 2401-2499 | 2601-2699 | 2501-2599 | 2701-2799 | 2801-2899 |
| Layout salts | 0x2100-0x21BF | 0x2200-0x22BF | 0x2300-0x23BF | 0x2400-0x24BF | 0x2600-0x26BF | 0x2500-0x25BF | 0x2700-0x27BF | 0x2800-0x28BF |
| Threshold salts | 0x21C0-0x21FF | 0x22C0-0x22FF | 0x23C0-0x23FF | 0x24C0-0x24FF | 0x26C0-0x26FF | 0x25C0-0x25FF | 0x27C0-0x27FF | 0x28C0-0x28FF |
| Headless ports | 43100-43109 | 43110-43119 | 43120-43129 | 43130-43139 | 43140-43149 | 43150-43159 | 43160-43169 | 43170-43179 |
| Lang keys, block codes | `l73-` | `basement-` | `l52-` | `l31-` | `l120-` | `l36-` | `l15-` | `l23-` |

Title keys and salts go by the internal id (`<id>01`..., `0x<id>00`...), which is why 36 (id 25) and 15 (id 27) have the
dropped levels' numbers; the old 55 and 183 keys are gone from the lang file. A gate run for one level uses
`--port-base` at the start of its range with `--fast` (base and base+1; a full run also takes base+2 and base+10,
the next level's).

**Main's room.** Main's values are released and never move; it appends after its last values: `WallPattern` 193-223 (Stucco
is 192), `FloorKind` 204-227 (Level 188's block ends at 211), `CeilingKind` 72-87, `Unders` 120-139, `Overheads`
110-139, `Pipes` 90-139, `Props` 600-699, `Decor` (none left below 256: main would
widen into 512+). The kept experimental values above sit just past that room; if main ever needs them, the
experimental side moves.

**Moved on 2026-10-30** (they sat in main's room; nothing else moved, and blocks are looked up by name, so no block
changed): `WallPattern` L73Wall/L73Rim 196/197 to 256/257, the Basement's 208-212 to 288-292; `FloorKind` Level 73's
212-221 to 256-265; `CeilingKind` L73Ceiling 72 to 256, the Basement's 80-86 to 288-294; `Pipes` the Basement's 100-103
to 288-291; `Props` the Basement's 640-644 to 1000-1004, Level 52's 680-681 to 1100-1101. Level 31's props (700-713) and
Level 120's (800-802) kept their values (their blocks start there). Every First/Last range without members moved to its
block.

`python tools/expclash.py` checks all of it: an experimental value shared with main's or with another experimental
level's, a range overlapping another, a value at or past its `Limit`, and any experimental member, constant or range
outside its level's block and kept values (its `RESERVED`/`KEPT` tables mirror this one: change both together).

## Rules for the detail agents

Each of the eight levels gets one agent working in parallel with the others; keep out of each other's way.

1. **Your ranges only.** Values from your level's column above, nothing else. Name every member and constant with your
   prefix (`L36Gate`, `Props.L36Bench`, `Unders.L36Belt`): `expclash.py` decides whose a value is by that prefix.
   Explicit values, never implicit ones. Never renumber anything that is not yours.
2. **Your own files.** Level code goes in your partial files: `src/Worldgen/WorldLayout.Level36.cs`,
   `src/Worldgen/WorldGenerator.L36.cs`, `src/AtmosphereSystem.L36.cs`, `src/Thresholds/ThresholdNetwork.L36.cs` /
   `ThresholdSystem.L36.cs` (no thresholds on this branch: leave them stubs), `tools/mapgen/L36Stats.cs` (your
   harness modes), `tools/gen_36.py` (and helpers `tools/gen_36_*.py`) for assets, written under
   `assets/backrooms/{blocktypes,shapes/block,textures/block,sounds/ambient}/36/`, and your plan
   `docs/design/experimental-levels/36-plan.md`. (The Basement's tag is `basement`, its infix `Basement`.)
3. **Shared files: single lines in your level's arm.** In `Tiles.cs` add members inside your level's block (after its
   placeholder, or next to its `First/Last` line); elsewhere (`WorldGeometry.cs` drop and band depth,
   `AtmosphereSystem.Levels` haze, `LevelTemperatures`, `Roster`, `Danger`, `MenaceSystem`, `Protection.RoofFrom`,
   `IsOpenSky`, the map's case, `WorldGenerator`'s `PropTable` rows and decor families) change only the line or arm
   of your level, with a small `Edit`, re-reading the file right before. Never reformat, reorder or regenerate a
   shared file, and never move another level's line.
4. **Lang:** your keys in **one contiguous block** in `assets/backrooms/lang/en.json`, right after your level's
   `level-<id>` / `levelhint-<id>` / `levelname-<id>` lines (replace those placeholders): title keys from your range,
   block names `block-l36-...`, item names `item-l36-...`. en.json only; the Spanish files fall back.
5. **Levels 0-20 must not change.** Before and after: `LAYOUT_VERSION=1` and `LAYOUT_VERSION=12`
   `mapgen-<tag>/mapgen.exe 12345 16000 layouthash` (see 6 for the build): every line for
   levels 0-20 and the `layout hash` line identical (only your level's line and the `far places hash` may move).
   No entrances in other levels.
6. **Builds in a shared tree.** Several agents may share one worktree, and builds share `obj/`: build only through
   `bash tools/locked.sh mod <tag>` and `bash tools/locked.sh mapgen <tag>` with your level's tag (`l36`, `basement`
   ...; output in `$TEMP/backrooms-build/build-<tag>/Mods` and `mapgen-<tag>/mapgen.exe`), never a plain
   `dotnet build`/`dotnet run`; run your asset generator as `bash tools/locked.sh run python tools/gen_36.py`; point
   headless servers at your own build (`--addModPath $TEMP/backrooms-build/build-<tag>/Mods`) and your own scratch
   data path. Run the gate with `GATE_TAG=<tag>` set so it builds into its own folder. A build broken by another level's
   half-done edit is theirs: wait for it, or report it; never fix another level's files.
7. **Before you hand back:** `python tools/expclash.py` prints `clean`; the mod and `tools/mapgen` build with 0 errors;
   `regions` finds 60/60 arrivals in your level; a headless dummy (`/backrooms dummy place 36 5`, repeated once if the
   first only loads chunks) lands with 0 error lines, on a port from your range; `python tools/gate.py --fast
   --port-base <your first port>` passes. Commit only your own paths (`git add <paths>`, never `-A`), small commits,
   on `experimental-levels`; never push, never switch branches in a shared checkout.
8. **Region and size** are yours to change in your layout file (centre, radius, drop, band depth), as long as
   `mapgen 12345 6200 overview 8` and `SPAWN=1000 ... 1300 overview 1` show no overlap with any other region.

## Budget rules for this branch

- Prototype quality: get the space, its blocks, light, fog and a sound bed right. Skip anything the contract lists
  that the level does not need (thresholds, entities, dens, loot tables, notes, handbook).
- Reuse existing blocks and textures wherever they fit (Level 0-11 walls, floors, lights, props); generate new
  assets only for what defines the level's look.
- Existing levels 0-20 must stay byte-identical (`layouthash`): no entrances in other levels.

## History

The sections below record each scaffolding pass as it was done. **Their value tables are superseded by "Reserved
values" above** (several values have moved since), and Levels 55 and 183 have been dropped.

### Scaffolding (done 2026-10-17)

Ids 21-23 are registered everywhere Level 188 (20) is: constants (`LevelCount` now `RingWidths.Length + 14`),
`DisplayNumber`/`FromDisplayNumber`/`FromDisplayName` ("basement", "the basement"), `ComputeLevel` (after 188),
`IsOpenSky`, `GetEdge`, the rim's `WallPattern`, `TemperatureAt`, `LevelTemperatures` (21: 30, 22: 14, 23: 18),
`BuildMacro`, `IsWalkThroughProp`, `StabilityAt`, `FindArrival`, `ArrivalHeight`, `DenAt` (null), `IsSanctuary` (false),
`PickedOverShare` (0.3), `WorldGeometry` (drop 0, band depth `ShaftDepth`), the generator's `Init`, `Band` and
`ColumnBlock`, `Danger.OfLevel` (0), `Roster` (empty, no distant sounds), `MenaceSystem` (Safe), `Protection.RoofFrom`,
the map's grouped case, every `>= RunLevel && <= Level52` name check (map marks, notes, Hub names, block dump),
threshold dispatch (walked, used, may-pass, redirect, arriving), `AtmosphereSystem.Levels` (a neutral haze each) and
its air and sound dispatch, the cheats dialog ("Level 73", "The Basement", "Level 52"), command help, the harness
(`LevelModes`, `regions`, `links`, `regionmap` names), and lang placeholders `level-`, `levelhint-`, `levelname-21..23`
(en.json only; the Spanish files fall back). Tiles.cs has a placeholder member per range: `WallPattern.L73Wall` 192,
`BasementWall` 208, `L52Wall` 224; `FloorKind.L73Floor` 212, `BasementFloor` 228, `L52Floor` 244; `CeilingKind.L73Ceiling`
72, `BasementCeiling` 80, `L52Ceiling` 88; `Props.<N>First/Last` (`Props.Limit` = 700), `Unders`, `Overheads` and
`Pipes` `<N>First/Last` as in the table above.

**Hooks per level** (`<N>` = `L73`, `Basement`, `L52`; build/block names use `73`, `Basement`, `52`):

| File | Hooks |
|---|---|
| `src/Worldgen/WorldLayout.Level73.cs`, `.LevelBasement.cs`, `.Level52.cs` | `Salt<N>Shape`, `<N>Reach`, `<N>CentreX/Z`, `<N>Radius`, `In<N>`, `<N>ArrivalCell`, `Is<N>ArrivalSpot`, `<N>ArrivalHeight`, `<N>Edge`, `BuildLevel73` / `BuildLevelBasement` / `BuildLevel52`, `<N>WalkThrough`, `<N>Temperature`, `<N>Stability` |
| `src/Worldgen/WorldGenerator.<N>.cs` | `Init<N>`, `Level73Block` / `LevelBasementBlock` / `Level52Block` |
| `src/Thresholds/ThresholdNetwork.<N>.cs` | `Salt<N>Threshold` (0x21C0, 0x22C0, 0x23C0), `<N>Walked`, `<N>Used` (both null), `Into<N>` |
| `src/Thresholds/ThresholdSystem.<N>.cs` | `<N>Arriving` (no-op), `<N>Redirect` (null), `<N>MayPass` (true) |
| `src/AtmosphereSystem.<N>.cs` | `<N>Air`, `<N>Sounds` (empty) |
| `tools/mapgen/<N>Stats.cs` | `<N>Modes` (false), `<N>LinkLabel`, `<N>UseKind` (null) |

The placeholder layout is one open floor (`<N>Edge` all open, so walls only at the region's rim); the blocks are plain
concrete floor and walls, a concrete ceiling at rel 4 with a fluorescent light every eight blocks (`(gx & 7) == 4 &&
(gz & 7) == 4`). Each level replaces both in its own commit.

**Harness results.** `layouthash` before and after: identical (`layout hash 18cfdbc1c530f039`, the same level grids,
every per-level line for 0-20 unchanged; only the new lines for 21-23 were added). `regions`: 60/60 arrivals for each
of the three, none in the wrong level or in small pockets, at full size, `SPAWN=1000` and `SPAWN=4000`. `overview`
(region bounds from spawn, in cells): full size 73 at x -2016..-1352, z -4384..-3736 (536 cells clear of Motion's
x -816, 1120 of the End's x -3136); the Basement at x -2000..-1352, z 3744..4384 (1120 clear of 974, 1344 of Level !);
52 at x 1352..2008, z 3744..4392 (1472 clear of the Hub, 1344 of Level !). `SPAWN=1000`: 73 at x -377..-299 (220 clear of
Motion's -79), the Basement x -377..-297 (271 clear of 974's -648), 52 x 297..378 (270 clear of the Hub's 648).
`SPAWN=4000`: likewise clear. No region's bounds overlap another's.

### Scaffolding, batch 2 (done 2026-10-17)

Ids 24-27 (Level 31 "Roller Rink", Level 55 "Land of Ice", Level 120 "Server Room", Level 183 "Clean Sewers"; see
BACKLOG.md for the table and the reserved values) are registered everywhere ids 21-23 are, in the same way:
`LevelCount` is now `RingWidths.Length + 18`; `DisplayNumber`/`FromDisplayNumber` ("31", "55", "120", "183");
`ComputeLevel` (after 52); `IsOpenSky` (false); `GetEdge`; the rim's `WallPattern`; `TemperatureAt`; `LevelTemperatures`
(24: 16, 25: -8, 26: 26, 27: 12); `BuildMacro`; `IsWalkThroughProp`; `StabilityAt`, `FindArrival`, `ArrivalHeight`;
`DenAt` (null), `IsSanctuary` (false), `PickedOverShare` (0.3); `WorldGeometry` (drop 0, band depth `ShaftDepth`); the
generator's `Init`, `Band` and `ColumnBlock`; `Danger.OfLevel` (0), `Roster` (empty), `MenaceSystem` (Safe);
`Protection.RoofFrom`; the map's grouped case; every `>= RunLevel && <= ...` name check now ends at `Level183` (map
marks, notes, Hub names, block dump, the generator's region flag); threshold dispatch; `AtmosphereSystem.Levels` (a
neutral haze each) and its air and sound dispatch; the cheats dialog ("Level 31", "Level 55", "Level 120", "Level 183":
28 buttons, four full rows of seven); command help; the harness (`LevelModes`, `regions`, `links`, `regionmap` and
`shotgrid` names); lang `level-`, `levelhint-`, `levelname-24..27` (en.json only).

Tiles.cs, one value each from this batch on: `WallPattern.L31Wall` 240, `L55Wall` 241, `L120Wall` 242, `L183Wall` 243;
`FloorKind.L31Floor` 249, `L55Floor` 250, `L120Floor` 251, `L183Floor` 252; `CeilingKind.L31Ceiling` 96, `L55Ceiling`
104, `L120Ceiling` 112, `L183Ceiling` 120; `Props.<N>First/Last` 700-739, 740-779, 780-819, 820-859 (`Props.Limit` =
860); `Unders` 150-189, `Overheads` 140-179, `Pipes` 120-159, ten each, in that order.

**Hooks per level** (`<N>` = `L31`, `L55`, `L120`, `L183`; build/block names `Level31`, `Level55`, `Level120`, `Level183`):

| File | Hooks |
|---|---|
| `src/Worldgen/WorldLayout.Level31.cs`, `.Level55.cs`, `.Level120.cs`, `.Level183.cs` | `Salt<N>Shape` (0x2401, 0x2501, 0x2601, 0x2701), `<N>Reach`, `<N>CentreX/Z`, `<N>Radius`, `In<N>`, `<N>ArrivalCell`, `Is<N>ArrivalSpot`, `<N>ArrivalHeight`, `<N>Edge`, `BuildLevel31` / `BuildLevel55` / `BuildLevel120` / `BuildLevel183`, `<N>WalkThrough`, `<N>Temperature`, `<N>Stability` |
| `src/Worldgen/WorldGenerator.<N>.cs` | `Init<N>`, `Level31Block` / `Level55Block` / `Level120Block` / `Level183Block` |
| `src/Thresholds/ThresholdNetwork.<N>.cs` | `Salt<N>Threshold` (0x24C0, 0x25C0, 0x26C0, 0x27C0), `<N>Walked`, `<N>Used` (both null), `Into<N>` |
| `src/Thresholds/ThresholdSystem.<N>.cs` | `<N>Arriving` (no-op), `<N>Redirect` (null), `<N>MayPass` (true) |
| `src/AtmosphereSystem.<N>.cs` | `<N>Air`, `<N>Sounds` (empty) |
| `tools/mapgen/<N>Stats.cs` | `<N>Modes` (false), `<N>LinkLabel`, `<N>UseKind` (null) |

The placeholder layout and blocks are batch 1's (one open floor, rim walls, concrete, a fluorescent light every eight
blocks).

**Regions** (all round, radius `max(40, spawnMacroX / 50)`: 320 cells full size, 40 at `SPAWN=1000`, 80 at `SPAWN=4000`):

| Level | Centre | Full size (R = 4000) | `SPAWN=1000` (R = 800) |
|---|---|---|---|
| 31 | `R * 1.1` out, 22.5 degrees north of west: `spawn + (-round(1.1 R cos 22.5), -round(1.1 R sin 22.5))` | (-4065, -1684) | (-813, -337) |
| 55 | the same, 22.5 degrees south of west: `spawn + (-round(1.1 R cos 22.5), +round(1.1 R sin 22.5))` | (-4065, +1684) | (-813, +337) |
| 120 | `spawn + (+F, -F)`, `F = round(R * 1.6 / sqrt 2)` (as 3999's), beyond Level Fun | (+4525, -4525) | (+905, -905) |
| 183 | `spawn + (-F, -F)`, beyond the End | (-4525, -4525) | (-905, -905) |

**Harness results.** `layouthash` before and after: identical (`layout hash 18cfdbc1c530f039`, the same level grids,
every per-level line for 0-23 unchanged; only the lines for 24-27 were added). `regions`: 60/60 arrivals for each of
the four, none in the wrong level or in small pockets, at full size, `SPAWN=1000` and `SPAWN=4000` (Level 3999's 59/60 at
`SPAWN=4000` is as it was before). `overview` (region bounds from spawn, in cells), full size: 31 at x -4384..-3744,
z -2008..-1368 (528 clear of the Poolrooms' z -840, 1120 of the End's z -3128); 55 at x -4392..-3744, z 1368..2016 (552
clear of the Poolrooms' z 816, 1112 of 974's z 3128); 120 at x 4200..4848, z -4848..-4200 (264 clear of Fun on both axes,
1720 clear of the city's z -2480; Level 188 is at x about 1684); 183 at x -4848..-4200, z -4848..-4200 (248 and 240 clear
of the End; Level 73 is at x about -1690). `SPAWN=1000`: 31 at x -852..-772, z -377..-297 (216 clear of the Poolrooms'
z -79, 271 of the End's z -648); 55 at x -852..-774, z 298..375 (217 clear of the Poolrooms' z 81, 273 of 974's z 648);
120 at x 865..944, z -946..-866 (98 clear of Fun's x 767, 99 of its z -767; 525 of Level 188's x 340); 183 at
x -944..-865, z -944..-866 (98 clear of the End's x -767, 100 of its z -766; 513 of Level 73's x -352). In the
`SPAWN=1000` world (2000 cells across) 120 and 183 stay 54-56 cells inside the map's edge. No region's bounds overlap
another's.

### Scaffolding, batch 3 (done 2026-10-30)

Levels 55 and 183 were dropped (on neither main lore wiki as built; their plans are in `dropped/`), and their ids reused.
Three new levels are registered everywhere ids 21-26 are, the same way as batch 2 (the commits `0d688ae` and `7ef8571`
are the pattern): `LevelCount` is now `RingWidths.Length + 19`; `DisplayNumber`/`FromDisplayNumber` ("36", "15", "23");
`ComputeLevel` (after 120); `IsOpenSky` (23 true, the others false); `GetEdge`; the rim's `WallPattern`; `TemperatureAt`;
`LevelTemperatures` (25: 21, 27: 20, 28: 16); `BuildMacro`; `IsWalkThroughProp`; `StabilityAt`, `FindArrival`,
`ArrivalHeight`; `IsSanctuary` (false), `PickedOverShare` (0.3); `WorldGeometry` (drop 0; band depth `ShaftDepth` for 36
and 15, 12 for 23, as Level 73's, so its sky reaches 27 above the floor); the generator's `Init`, `Band` and
`ColumnBlock`; `Danger.OfLevel` (0), `Roster` (empty), `MenaceSystem` (Safe); `Protection.RoofFrom` (23: `int.MaxValue`,
open sky); the map's grouped case; every `>= RunLevel && <= ...` name check now ends at `Level23` (28, the last id);
threshold dispatch; `AtmosphereSystem.Levels` (a neutral haze each) and its air and sound dispatch; the cheats dialog
("Level 36", "Level 15", "Level 23"); `BackroomsModSystem.LevelList`; the harness (`LevelModes`, `regions`, `links`,
`regionmap` and `shotgrid` names); `tools/expclash.py`'s names; lang `level-`, `levelhint-`, `levelname-25`, `-27`, `-28`
(en.json only). `WorldLayout.Dens` has no per-level lines any more (main folded them into its default), so none were added.

| Level | Id | Constant | Shown as | Tag (files, block codes) | Method infix | Region |
|---|---|---|---|---|---|---|
| Level 36 "Airport" | 25 | `WorldLayout.Level36` | `36` | 36 (`l36-`) | `L36` | Level 55's old slot: west-south-west, `R * 1.1` out, 22.5 degrees south of west; big indoor level |
| Level 15 "Futuristic Halls" | 27 | `WorldLayout.Level15` | `15` | 15 (`l15-`) | `L15` | Level 183's old slot: far north-west beyond the End, `spawn + (-F, -F)`; big indoor level |
| Level 23 "Petrified Garden" | 28 | `WorldLayout.Level23` | `23` | 23 (`l23-`) | `L23` | the free far south-west slot beyond Level 974, `spawn + (-F, +F)`; open sky (stone trees) |

Placeholders: 36 and 15 are batch 1's (one open floor, rim walls, concrete, a fluorescent light every eight blocks); 23
is a concrete floor under the open sky with a 12-high concrete rim wall (`WorldGenerator.L23.cs`, `L23RimTop`). Each
level's files are named as batch 2's: `WorldLayout.Level36.cs`, `WorldGenerator.L36.cs`, `AtmosphereSystem.L36.cs`,
`ThresholdNetwork.L36.cs`, `ThresholdSystem.L36.cs`, `tools/mapgen/L36Stats.cs` (and the same for `15`, `23`). Salts:
`SaltL36Shape` 0x2501 / `SaltL36Threshold` 0x25C0, `SaltL15Shape` 0x2701 / 0x27C0, `SaltL23Shape` 0x2801 / 0x28C0.

**Harness results.** `layouthash` (seed 12345, 16000; layout versions 1 and 12) before and after: every line for levels
0-20 and the `layout hash` line identical. `regions`: 60/60 arrivals for each of the three, none in the wrong level or
in small pockets, at full size and `SPAWN=1000`. `overview` (bounds from spawn, in cells), full size: 36 at x
-4392..-3744, z 1368..2016 (as 55 was); 15 at x -4848..-4200, z -4848..-4200 (as 183 was); 23 at x -4856..-4208, z
4200..4848 (272 cells clear of 974's x -3936, 264 of its z 3936; 2184 of 36's z 2016). `SPAWN=1000`: 36 x -852..-774,
z 298..375; 15 x -944..-865, z -944..-866; 23 x -946..-864, z 864..943 (98 clear of 974's x -766 and 97 of its z 767,
54 inside the map's edge). No region's bounds overlap another's. Headless (port 43010): `/backrooms dummy place <level> 5`
put a dummy in each of 73, the Basement, 52, 31, 120, 36, 15 and 23, 0 error lines.
