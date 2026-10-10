# The new levels: contract for the per-level agents

Written by the scaffolding agents. Ids 14-20 are registered everywhere a level is switched on; each level has stub
files of its own and reserved value ranges. **Work in your own files. In shared files, make only small, local `Edit`s
inside your level's own line, case or block, re-reading the file right before each edit.** Never reformat, reorder or
regenerate a shared file. Never renumber anything.

**Ids 19 and 20 (2026-10-09):** Level 3999 is restored as id 19 and Level 188 added as id 20, registered exactly as
14-18 were (a second scaffolding pass): constants, regions, stub files, ranges, lang placeholders, every per-level
switch. Where this document says "the five" or "14-18", read "14-20" unless it says otherwise.

## The levels

| Level | Id / constant | Shown as | Tag | Method infix `<N>` | Region now (placeholder) |
|---|---|---|---|---|---|
| Level ! | 14 `WorldLayout.RunLevel` | `!` | run | `Run` | due south, centre `spawn + (0, R)`, 3 x 19 cells (96 x 608 blocks), the hallway north-south |
| Level Fun =) | 15 `WorldLayout.FunLevel` | `Fun` | fun | `Fun` | north-east, centre `spawn + (+D, -D)`, round, radius `max(60, spawnMacroX/40)` (400 cells full-size) |
| The End | 16 `WorldLayout.TheEnd` | `End` | end | `End` | north-west, centre `spawn + (-D, -D)`, round, same radius |
| The Hub | 17 `WorldLayout.Hub` | `Hub` | hub | `Hub` | south-east, centre `spawn + (+D, +D)`, round, radius 24 cells |
| Level 974 | 18 `WorldLayout.Level974` | `974` | 974 | `L974` | south-west, centre `spawn + (-D, +D)`, round, `max(60, spawnMacroX/40)` |
| Level 3999 | 19 `WorldLayout.Level3999` | `3999` | 3999 (blocks `l3999-`) | `L3999` | far south-east, beyond the Hub: centre `spawn + (+F, +F)`, `F = round(R * 1.6 / sqrt 2)` (4525 full-size, 905 small; 6400 cells, 205 km, out), round, radius `max(60, spawnMacroX/40)` |
| Level 188 | 20 `WorldLayout.Level188` | `188` | 188 (blocks `l188-`) | `L188` | north-north-east, between Motion and Fun: centre `R * 1.1` out, 22.5 degrees east of north (`spawn + (+1684, -4065)` full-size, `(+337, -813)` small), round, radius `max(40, spawnMacroX/50)` (placeholder) |

`R = RegionReach = max(800, spawnMacroX / 4)` (the city's distance; 4000 cells in a full-size world, 800 in a small
one); `D = DiagonalReach = R * 1.25 / sqrt 2` (3536 full-size, 707 small). Both are in `WorldLayout.cs` (shared; don't
change them). Checked: no region overlaps another, the city (`spawn + (R, 0)`, radius up to 2880 cells full-size, 288
small), the Poolrooms (`-R, 0`) or Motion (`0, -R`), for spawnMacroX 1000, 2000, 4000 and 16000 (3999 and 188
re-checked the same way: 3999 has ~760 cells to spare toward the Hub full-size (~150 small) and stays inside the map at
spawnMacroX 1000, its far rim ~966 cells out; 188 has ~340 cells to spare toward Motion full-size, ~85 at
spawnMacroX 4000). **If you resize or move
your region**, keep clear of those: the diagonal regions have about 200 cells of room toward the city in a full-size
world (radius 400 * 1.2 lumpiness is already counted), and run `SPAWN=1000 ... overview 1300 overview 1` and
`... 6200 overview 8` (see below) to see the bounds of every region. Rings are checked first in `ComputeLevel`, so in
extreme directions a ring could cut into a region, as for the Poolrooms.

Regions are noclip regions (`IsNoclipRegion` is `level >= 11`): no gates in their rims; the rim against Level 10 is a
solid, tall rock wall (`LevelBoundaryEdge`). None is open-sky (`IsOpenSky` has a line for each).

## Files each level owns (`<N>` from the table, e.g. `Run`, `L974`)

| What | File | Holds now |
|---|---|---|
| Layout | `src/Worldgen/WorldLayout.Level<Run|Fun|End|Hub|974|3999|188>.cs` | centre/size, `In<N>(mx, mz)`, `MayReach<N>(x0, z0, size)`, `<N>ArrivalCell(h)`, `Is<N>ArrivalSpot(t)`, `<N>ArrivalHeight(t, stand)`, `<N>Edge(mx, mz, west)`, `BuildLevel<Run|Fun|End|Hub|974|3999|188>(b, mx, mz)`, `<N>WalkThrough(variant)`, `<N>Temperature(...)`, `<N>Stability(..., drift)` |
| Blocks | `src/Worldgen/WorldGenerator.<N>.cs` | `Init<N>()` (block ids, called from the constructor), `Level<Run|Fun|End|Hub|974|3999|188>Block(in Tile t, int gx, int gz, int rel, out int fluid)` |
| Thresholds (network) | `src/Thresholds/ThresholdNetwork.<N>.cs` | `<N>Walked`, `<N>Used`, `Into<N>(beside)`, salt `Salt<N>Threshold` |
| Thresholds (game) | `src/Thresholds/ThresholdSystem.<N>.cs` | `<N>Arriving`, `<N>Redirect`, `<N>MayPass` |
| Air and sound | `src/AtmosphereSystem.<N>.cs` | `<N>Air`, `<N>Sounds` |
| Runtime rules (create when needed) | `src/Regions/<Run|Fun|End|Hub|L974|L3999|L188>System.cs` | (like `PoolSystem.cs` / `MotionSystem.cs`) |
| Harness modes | `tools/mapgen/<N>Stats.cs` | `<N>Modes` (`runstats`, `funstats`, `endstats`, `hubstats`, `974stats`, `3999stats`, `188stats`), `<N>LinkLabel`, `<N>UseKind` |
| Assets (create) | `tools/gen_<tag>.py`; `assets/backrooms/{textures,shapes}/block/<tag>/`, `blocktypes/<tag>/`, `sounds/ambient/<tag>/` | block codes prefixed `<tag>-` (3999 and 188: `l3999-`, `l188-`) |
| Plan | `docs/new-levels/<tag>-plan.md` | |

Your layout salts: `0x1400-0x14BF` (Run), `0x1500-0x15BF` (Fun), `0x1600-0x16BF` (End), `0x1700-0x17BF` (Hub),
`0x1800-0x18BF` (974), `0x1900-0x19BF` (3999), `0x2000-0x20BF` (188); threshold salts `0x<id>C0-0x<id>FF`
(`Salt<N>Threshold` = `0x14C0` ... `0x19C0`, `0x20C0`). Use them for entrances
you add to other levels too, each its own salt, so nothing else shifts.

The placeholders (`PlaceholderEdge`, `BuildPlaceholderCell` in `WorldLayout.cs`; `PlaceholderRegionBlock` in
`WorldGenerator.cs`) are shared scaffolding: stop calling them from your files; phase 3 deletes them. `InRoundRegion`
and `RoundArrivalCell` (`WorldLayout.cs`) are shared helpers you may keep using.

## Reserved values (append-only; explicit values; inside your block only)

| Range | Run | Fun | End | Hub | 974 | 3999 | 188 | Placeholder member / markers |
|---|---|---|---|---|---|---|---|---|
| `WallPattern` (byte enum) | 64-79 | 80-95 | 96-111 | 112-143 | 144-159 | 160-175 | 176-191 | `RunWall`, `FunWall`, `EndWall`, `HubWall`, `L974Wall`, `L3999Wall`, `L188Wall` |
| `FloorKind` (byte enum) | 100-115 | 116-131 | 132-147 | 148-163 | 164-179 | 180-195 | 196-211 | `RunFloor` ... `L974Floor`, `L3999Floor`, `L188Floor` |
| `CeilingKind` (byte enum) | 16-23 | 24-31 | 32-39 | 40-47 | 48-55 | 56-63 | 64-71 | `RunCeiling` ... `L974Ceiling`, `L3999Ceiling`, `L188Ceiling` |
| `Props` (`Tile.Variant`, now **ushort**) | 300-319 | 320-359 | 360-399 | 400-439 | 440-479 | 480-539 | 540-579 | `Props.RunFirst/RunLast` ... `Props.L188First/L188Last`; `Props.Limit = 580` |
| `Decor` (wall decorations, byte) | 176-183 | 184-195 | 196-207 | 208-223 | 224-235 | 236-247 | 248-255 | `Decor.RunFirst/RunLast` ...; `Decor.Limit = 256` (now full) |
| `Unders` (byte) | 40-49 | 50-59 | 60-69 | 70-89 | 90-99 | 100-109 | 110-119 | `Unders.RunFirst/RunLast` ... |
| `Overheads` (byte) | 40-49 | 50-59 | 60-69 | 70-79 | 80-89 | 90-99 | 100-109 | `Overheads.RunFirst/RunLast` ... |
| `Pipes` (byte) | 20-29 | 30-39 | 40-49 | 50-59 | 60-69 | 70-79 | 80-89 | `Pipes.RunFirst/RunLast` ... |
| Title keys (`level-<key>` in lang) | 1401-1499 | 1501-1599 | 1601-1699 | 1701-1799 | 1801-1899 | 1901-1999 | 2001-2099 | |

The 3999 and 188 blocks in `Tiles.cs` are appended after the 974 blocks, each marked "Levels 3999 and 188 (19, 20)".
Raising `Props.Limit` resized the generator's prop tables (`propIds`, `propKinds`, `propHeadFirst`); nothing else is
sized by it. `decorIds` grows with the largest `WallPattern` (now 176).

**The Props solution.** `Tile.Variant` is widened from `byte` to `ushort`; every existing `Props` constant stays a
`byte` with its old value (they convert implicitly), new levels declare `public const ushort` props in their block. The
generator's prop tables are sized `Props.Limit`; `PropTable` entries are `(ushort Prop, ...)`. Wall decorations stay
below 256 (`decorIds[pattern, decor, rel, facing]`, pattern dimension sized by the largest `WallPattern`). Decoration
codes are looked up by name across all families, so give yours names no other family uses. Per-level fields stay
per-level: `Zone`, `Detail`, `Height`, `Depth`, `Roof`, `Stack` mean what your level says on your tiles. Harness `.bin`
writers clamp `Variant` to a byte; write your own format in your stats file if you need props >= 256 there.

`IsWalkThroughProp` asks `<N>WalkThrough(variant)` for any variant >= 300: say there which of your props people walk
through (it decides sealed pockets, arrivals and entity spots).

## Geometry (`src/Worldgen/WorldGeometry.cs`, your own line only)

- `RunDrop, FunDrop, EndDrop, HubDrop, L974Drop, L3999Drop, L188Drop`: how far below the shared floor (`FloorY`) your
  floor is. `FloorFor(level) = FloorY - <N>Drop`. Set at scaffolding: End 6, 3999 20 (its plan: 18-high atria), the
  rest 0 (levels have since changed their own; change your own constant).
- `RunBandDepth, ..., L974BandDepth, L3999BandDepth, L188BandDepth`: how far below your floor your band starts.
  `BandBottomFor(level) = FloorFor - <N>BandDepth` (at scaffolding: End 24, 3999 4 as its plan asks, the rest
  `ShaftDepth` = 30). The band is always 40 blocks tall: `BandTopFor(level) = BandBottomFor + 39`
  (capped at `TopY - 1`). The generator builds your columns over `[min(BandBottom, BandBottomFor), BandTopFor]`, lights
  `[BandBottomFor, BandTopFor]`, and puts the mantle cap at `BandTopFor + 1` (= the usual `CapY` with the usual band).
  So a shallower band depth makes room for tall spaces above your floor.
- Your column builder gets `rel = y - FloorFor(level)`; return solid (e.g. `concreteId`) wherever nothing is.
- Other heights to know: `RoomHeight` 3, `MaxRoomHeight` 4; `ArrivalHeight` hook `<N>ArrivalHeight(t, stand)`.

## Hooks and where they are called from

| Hook (your file) | Called from (shared) |
|---|---|
| `In<N>` | `WorldLayout.ComputeLevel` (after city, Poolrooms, Motion) |
| `<N>Edge` | `WorldLayout.GetEdge` (edges between two of your cells); your rim: `LevelBoundaryEdge` (solid, `WallPattern.<N>Wall` unless next to an open-sky level, then rock) |
| `BuildLevel<...>` | `WorldLayout.BuildMacro`; after it, shared passes run on your tiles: `OrientDoorways`, `ClearDoorways`, `SealPockets`, `MarkPickedOver`, `PlaceDen` (none), chalk (none past Level 6) |
| `<N>ArrivalCell`, `Is<N>ArrivalSpot` | `WorldLayout.FindArrival` (`Reality.cs`); every arrival must be walkable 48 blocks away (`CanWalkAway`) unless `checkEscape: false` |
| `<N>ArrivalHeight` | `WorldLayout.ArrivalHeight` |
| `<N>Temperature` | `WorldLayout.TemperatureAt` (default `LevelTemperatures[id]`, your entry in that array) |
| `<N>Stability` | `WorldLayout.StabilityAt` (1 is neutral; <1 drains) |
| `<N>WalkThrough` | `WorldLayout.IsWalkThroughProp` |
| `Init<N>`, `Level...Block` | `WorldGenerator` constructor, `WorldGenerator.ColumnBlock` (also used by lighting) |
| `<N>Walked(x, z, tile, rel)` | `ThresholdNetwork.Walked`, **before** every other level's case, every tick per player: match only your own `Unders`/`Props`/patterns (on any level) and return a `Passage` |
| `<N>Used(x, z, level, kind, ref refusal)` | `ThresholdNetwork.Used`, before the built-in kinds: answer only your own block kinds (`BlockBehaviorThreshold` `kind` property, e.g. `"hub-door"`) |
| `Into<N>(beside)` | yours: an arrival finder in your level for a `Passage.Find` |
| `<N>MayPass(player, passage)` | `ThresholdSystem.OnTick` before going through a walked threshold (false holds it shut) |
| `<N>Redirect(player, passage, destination)` | `ThresholdSystem.Go` (walked, used, vending, trial) and each elevator rider in the elevator callback, **just before landing**: return a different `Link` to send them there instead, or null. The network's written link is unchanged. Asked for every arrival everywhere: answer only for your cases. (Not called by `/backrooms goto`.) |
| `<N>Arriving(player, link, ref drop)` | `ThresholdSystem.Arrive`, when the destination is in your level: raise `drop` to fall in from above (Motion), etc. |
| `<N>Air(dt, pos, ref target, ref titleKey)` | `AtmosphereSystem.OnTick` while the player is in your level: swap the `Atmosphere` for a sub-zone, set a title key from your range |
| `<N>Sounds(dt, pos, here)` | `AtmosphereSystem.LevelSounds` every tick (stop your loops when `!here`) |
| `<N>Modes`, `<N>LinkLabel`, `<N>UseKind` | `tools/mapgen/LevelModes.cs` (from `Program.cs` and `Links.cs`) |

### Adding a threshold

1. Layout: mark it on tiles (an `Unders` value from your block, a prop, a `WallPattern` door); in another level's
   layout file, add the entrance with a salt of your own and gate it so nothing else in that level moves (check
   `layouthash`, below: only the cells holding your entrance may change).
2. Network: in `<N>Walked` / `<N>Used` build the `Passage`: `Source` from `layout.FeatureOrigin(x, z, part)` (one origin
   per threshold), `Key = Hashing.Hash(seed, src.X, src.Z, Salt<N>Threshold + k)` via the private `KeyOf`, `Find =
   Into<N>(beside)` or `In(level, beside)`; two-way (walked through) = `TwoWay = true` with a `ReturnFeature` if one
   exists, one-way (fell, dived, taken) otherwise; `Message` a lang key, `Sound` an asset.
3. Blocks used by hand need `BlockBehaviorThreshold` with your `kind` in the blocktype.
4. Harness: `<N>LinkLabel` / `<N>UseKind` so `links` names it, then run `links` (each kind: paired, one-way, back).

### Fog, sound, lighting, map, stability, danger: the edit points

- **Fog**: your base `Atmosphere` is your line in `AtmosphereSystem.Levels` (marked `// Level !` ...); sub-zones in `<N>Air`.
- **Sound**: `<N>Sounds`; distant entity sounds: your entry in `Roster.SoundsByLevel`.
- **Lighting**: comes from your blocks' light (`LightHsv`) over your band; flicker blocks need `flickerIds`/block entities.
- **Map**: `BackroomsMapLayer.SampleHeights` has one grouped case for the five (floor to floor + 5); take your case out of
  the group if you need other heights. Colours come from blocks (`MapColors`). Names: `MapMarks.LevelName` uses lang
  `levelname-<id>`.
- **Stability**: `<N>Stability`. **Temperature**: `<N>Temperature` / `LevelTemperatures`.
- **Danger**: `Danger.OfLevel` (your line, 0 now), `Roster.ByLevel` (your entry, empty), `MenaceSystem.Rate` (your
  case, `Safe` now), `IsSanctuary`, `DenAt`, `PickedOverShare` (your lines), `CreatureSystem.ByLevel` (add an entry +
  a `TrySpawn` case for animals). Wanderer sites and refuges (`WandererSite`, `NearestRefuge`) default to none.
- **Salvage**: `Protection.RoofFrom` (your line: `RoomHeight + 1`).
- **Commands**: `/backrooms goto !|fun|end|hub|974|3999|188` and `/backrooms find <feature> <level>` accept names
  (`WorldLayout.FromDisplayName`); the cheat dialog lists all seven.
- **Lang** (`assets/backrooms/lang/en.json`, placeholders to replace): `level-<id>` (title), `levelhint-<id>`,
  `levelname-<id>` (map/waypoint name), ids 14-20.

## Shared-file edit points you may touch (your own line/case/block only)

`Tiles.cs` (your enum/const blocks), `WorldGeometry.cs` (your drop/band constants), `WorldLayout.cs` (nothing but your
`LevelTemperatures` value; ask the coordinator for anything else), `WorldLayout.Reality.cs`, `.Entities.cs`, `.Dens.cs`,
`.Loot.cs` (your lines), other levels' `WorldLayout.Level*.cs` (only to add your salted entrance), `WorldGenerator.cs`
(`PropTable` rows for your props, decor families/codes), `AtmosphereSystem.cs` (your `Levels` line), `Roster.cs`,
`MenaceSystem.cs`, `Protection.cs`, `BackroomsMapLayer.cs`, `CreatureSystem.cs`, `lang/en.json` (your keys).

## Build and harness

```
bash tools/locked.sh mod <tag>                     # build the mod
bash tools/locked.sh mapgen <tag>                  # build the harness to $TEMP/backrooms-build/mapgen-<tag>/
M=$TEMP/backrooms-build/mapgen-<tag>/mapgen.exe
$M 12345 14 regions                 # every region past the rings: where, arrivals found / wrong level / trapped, ms per cell
SPAWN=1000 $M 12345 14 regions      # the same in a small world (SPAWN = spawn macro cell = half the map in cells)
$M 12345 6200 overview 8            # level grid (overview.bin) + bounds of every region (step 8 cells)
$M 12345 14 regionmap <37|94|!|fun|end|hub|974|3999|188> [dx dz]   # region.bin for tools/mapgen/render_region.py
$M 12345 14 <tag>stats              # your own mode(s)
$M 12345 14 links                   # the threshold network (labels from your LinkLabel/UseKind)
$M 12345 14 layouthash              # fingerprint of levels 0-13 in three worlds (field values of tiles, arrivals,
                                    #   temperature, stability, the level grid with 14-20 folded into 10); after the
                                    #   overall hash, the same per-level hash for 14-20 in each world (not in the
                                    #   overall hash): compare the lines of the levels you did not touch
```

**Existing levels must stay byte-identical.** The baseline `layouthash` (from the tree before the scaffolding) ends
`layout hash d4a0005bf8137db6`; it was identical after the scaffolding. Re-run it after your changes: if you added an
entrance to an existing level, only the per-level line of that level may change, and you must say so in your report.
The `links` table for levels 0-13 was also unchanged (only the sample size grew by the new regions' cells).

## Second scaffolding pass: Levels 3999 and 188 (2026-10-09)

**Verification.** `layouthash` before and after was identical for levels 0-13 (`layout hash 35ae17fa657e4787`, the
tree as it stood then, with the level agents' entrances), and the new per-level lines for 14-18 matched a build with
the two new regions switched off. `regions`: 60/60 arrivals for 3999 and 188, none wrong or in small pockets, in
full-size, spawnMacroX 1000 and 4000 worlds. `overview` (spawnMacroX 1000, 2000, 4000, 16000): no region's bounds
overlap another's.

**Notes for Level 3999's agent.** Your plan was written against the first scaffold; the contract wins where they
differ: the region is far south-east beyond the Hub (`F` above), not due south; props are 480-539 (not 480-519);
layout salts `0x1900-0x19BF`, threshold salts `0x19C0-0x19FF` (as the plan already uses); `L3999Drop = 20` and
`L3999BandDepth = 4` are set (the plan's `BandBottomFor = FloorFor - 4`); `LevelTemperatures[19] = 24`;
`IsSanctuary` is `false` and `PickedOverShare` 0.4 for now (your lines). Hooks are named exactly as for the others
(`InL3999`, `L3999Edge`, `BuildLevel3999`, `Level3999Block`, `L3999Walked`/`Used`/`Redirect`/`MayPass`/`Arriving`,
`L3999Air`/`Sounds`, `IntoL3999`, `L3999Modes`).

**Notes for Level 188's agent.** Your region is a placeholder (radius `max(40, spawnMacroX/50)`, drop 0, the usual
band): size and move it in your own file, keeping clear of Motion (`0, -R`, radius up to 1.2 x `max(80, S/20)`) and
Fun. `LevelTemperatures[20] = 18` is a placeholder.

**Shared spots the Hub owns** that still stop at 974 (the Hub's agent may extend them): `HubSystem`'s level names
(`<= Level974`), `HubStats` and the Hub's door lists (`WorldLayout.LevelHub.cs`, `HubTower.cs`).

