# Experimental levels (branch `experimental-levels`)

Three prototype levels, built cheaply to try out ideas. They are **disconnected**: no thresholds in or out, no
entities, no notes, no handbook text. The only way in is the cheats menu (F7) or `/backrooms goto 73|basement|52`.
If an idea works, it gets a proper pass (lore polish, entrances, dangers) later; if not, its commit is dropped.

This branch is not meant to merge into `main` for a long time. Each level is its own commit after the shared
scaffolding commit, so one can be cherry-picked or reverted on its own.

| Level | Internal id | Constant | Shown as | Tag (files, block codes) | Method infix | Region |
|---|---|---|---|---|---|---|
| Level 73 "The Redlands" | 21 | `WorldLayout.Level73` | `73` | 73 (blocks `l73-`) | `L73` | north-north-west, mirror of Level 188: centre `R * 1.1` out, 22.5 degrees west of north |
| The Basement (unnumbered) | 22 | `WorldLayout.Basement` | `Basement` | basement (blocks `basement-`) | `Basement` | south-south-west: centre `R * 1.1` out, 22.5 degrees west of south |
| Level 52 "School Halls" | 23 | `WorldLayout.Level52` | `52` | 52 (blocks `l52-`) | `L52` | south-south-east: centre `R * 1.1` out, 22.5 degrees east of south |

All three are round noclip regions (like 37/94/188), radius `max(40, spawnMacroX / 50)` unless the level's plan says
otherwise. `R = RegionReach` (see `docs/design/new-levels/CONTRACT.md`, which this branch follows: same hooks, same
file naming, same rules for shared files).

## Reserved values (append-only, after Level 188's)

| Range | 73 | Basement | 52 |
|---|---|---|---|
| `WallPattern` | 192-207 | 208-223 | 224-239 |
| `FloorKind` | 212-227 | 228-243 | 244-255 |
| `CeilingKind` | 72-79 | 80-87 | 88-95 |
| `Props` (ushort) | 580-619 | 620-659 | 660-699 (`Props.Limit` = 700) |
| `Decor` | none: the byte is full (Limit 256). Build wall detail as wall-block variants or props instead. |
| `Unders` | 120-129 | 130-139 | 140-149 |
| `Overheads` | 110-119 | 120-129 | 130-139 |
| `Pipes` | 90-99 | 100-109 | 110-119 |
| Title keys | 2101-2199 | 2201-2299 | 2301-2399 |
| Layout salts | 0x2100-0x21BF | 0x2200-0x22BF | 0x2300-0x23BF |
| Headless ports | 42481 | 42482 | 42483 |

## Budget rules for this branch

- Prototype quality: get the space, its blocks, light, fog and a sound bed right. Skip anything the contract lists
  that the level does not need (thresholds, entities, dens, loot tables, notes, handbook).
- Reuse existing blocks and textures wherever they fit (Level 0-11 walls, floors, lights, props); generate new
  assets only for what defines the level's look.
- Existing levels 0-20 must stay byte-identical (`layouthash`): no entrances in other levels.

## Scaffolding (done 2026-10-17)

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

## Scaffolding, batch 2 (done 2026-10-17)

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
