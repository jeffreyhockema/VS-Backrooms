# Level layout redesign: review and implementation plan

The levels are built from the right materials and the right props, but most of them do not *read* as places. Level 0 is wall confetti; Level 6 is a one-block maze in the dark; Level 3 is a single 8-block lattice stamped to the horizon. This plan reviews every level's layout against the code, the renders and the Wikidot lore, names the one structural mistake that most of them share, and lays out the work to fix it, level by level, with numbers that can be measured before and after.

Numbers are starting points for tuning. Renders before and after are in `docs/level-review/`.

## Status (2026-10-06): implemented, with the recommended answers to section 9

Not yet play-tested in game; everything below is verified with the layout harness only.

**Harness.** Now in the repo: `tools/mapgen` (build with `dotnet build tools/mapgen -c Release -o tools/mapgen/out`). `report.sh [seed cells angle levels…]` renders and measures levels (`metrics.py`). New modes: `reach <level> <angle> [counted level]` (true pockets across a level's border, ignoring pieces that leave the window), `path ax az bx bz`, `l0 gx gz` (describes a Level 0 unit), `l6density`; `reachmap.py` overlays unreachable floor on a render. `validatelevel` windows (8–10 cells) are smaller than the Level 6 and Level 8 maze blocks, so it reports pieces that connect outside the window; check those with `path` in a 24–32-cell window.

**Shared.** `WorldLayout.Plans.cs`: `PlanCache` (Level 11 now uses it too), `PlanLatticeTree` (the minor-line maze for Levels 2, 6 and 8), `CopyPlan`, and the edge hallway (`EdgeHall`/`CarveEdgeHall`): a 2-wide hallway along the inside of every wall that cuts a plan (level borders; in Level 0 also round Red Rooms). Without it 0.2–2.3% of Level 0 floor near the border was cut off. `Tile.Low` (2-high) beside `Tile.Grand`.

| Level | Done | Deviations from the plan |
|---|---|---|
| 0 | Hallway lattice (pitch 36 ± 6, mains every 3rd, 3 wide), dropped minor stretches absorbed by the block beside them, blocks: rooms (one gap per wall, no stop-short), big room with free partitions, cell rows, pillar halls continuing through hallways, arches, pits, blackout; spawn is a big room with one partition; Manila gets a walkway round it | No jogs (dropped stretches already give hard corners). Red/Manila stay cell overlays, not "at a dead-end block". |
| 1 | Fire walls between 3×3-cell districts (gaps at alternate aisles and every cross aisle, rebar), hall sectors on the district grid | No racking/loading-dock districts, no coordinate signage, no hall hierarchy, clutter not regrouped. |
| 2 | Tunnel lattice (mains 3 wide every 64, service tunnels 1–2 wide every 16 as a tree), pump galleries at 1 in 3 main crossings, pipes per tunnel, lights and leaks per stretch | Mains don't wander ±4 per section. |
| 3 | Tight (8) and wide (16, 4-wide 4-high galleries) districts, 1-wide squeezes half 2-high, 2×2-cell transformer / assembly halls per 5×5 region, Sanctum per 8×8, straighter tree, lights die per stretch, barred shrine and sludge-pool rooms | No pitch-12 district (12 doesn't divide 32). |
| 4 | Concourse every 6 rooms (48 blocks), building cores (2 elevators, stairwell, restroom) per 2×2 cells, windows only on the level's outer wall, cubicle farms on a global module and 90% cleared, ghost-desk rows, cables hanging from missing tiles | Kept the 8-grid and 4×4 rooms (no double-loaded 4×5 rooms). Cores per 2×2 cells, not 4×4 (stairs and elevators feed the threshold network). |
| 5 | Halls 16 deep (rooms 5×5 with toilet alcoves), consecutive door numbers (plaques regenerated 201–208), mirror-ended corridors (1 in 8), Beverly once per 6×6 region and refitted between two corridors, dining once per 4×4 with the piano in a random corner, lobby columns on 8 with one desk in ~30 bays; bugs fixed: boiler halls no longer strip their bays next to boiler halls, wing-to-grand walls get doorways only where corridors cross them | No single authored lobby hub, no grand staircase, no service spine. |
| 6 | Trunk lattice (pitch 64, mains every 4th, 3 wide), minor trunks as a tree, wet 1-wide side passages, chambers at half the crossings with stairs (0.2 + 0.6·depth), chalk arrows toward stairs, X at 60% of dead ends; Snackrooms ~1.1% of cells, ≥ 4 apart, never across a trunk; waves sound from the nearest stairs within 160 blocks (`AtmosphereSystem`) | Pitch 64 instead of 96 (96 was 94% solid rock). Lighting unchanged (decision 3). |
| 7 | Entry room one per 4×4 region; boulders by hash | 4×4 not 8×8 (entry rooms are Level 6's arrivals). No island heights, seamounts or glow patches. |
| 8 | Road lattice keeps mains every 192 unbroken, side roads a tree, full lattice within a road block of the level's edge; camps only where roads meet | A sparse lattice instead of radial roads (same effect, far less risk to the systems that use the road). No tube/dome/road-height changes. |
| 9 | Unpainted roads, stop signs at 1 junction in 5, field lots 1% and only in the outer third | No landmark lots, clipped houses, curved streets or signs. |
| 10 | Roads are two tracks with grass between, hedge gaps every ~30 blocks whichever way a hedge runs | No barley (Vintage Story has none), no driveways or lone sheds. |
| 11 | Street lights 55% lit, 10% flickering | Not 85% (each lit lamp costs light propagation at generation). No canals or rail. |

**Verified** (seeds 56693014, 1234, 12345): zero unreachable floor around arrivals on every level except single tiles that the old build also had; `reach` zero true pockets across the borders of Levels 0–6; thresholds all paired and round-trip (`links`); mod builds clean. Level 0 cells generate in ~0.5 ms (was ~0.3; chunk generation is ~19 ms). Loot shifts: Level 0 stashes now succeed more often (d7 retuned `PlaceStash`); Level 2 and Level 3 hold ~25% fewer boxes (fewer rooms).

| Level | wall % | view p10/p50/p90 | width p50 | before: view p50, width |
|---|---|---|---|---|
| 0 | 18 | 10 / 24 / 189 | 8 | 31, 12 |
| 1 | 11 | 12 / 95 / 287 | 37 | 384, 159 |
| 2 | 82 | 31 / 127 / 384 | 3 | 29, 2 |
| 3 | 54 | 7 / 63 / 138 | 4 | 29, 2 |
| 4 | 10 | 95 / 255 / 384 | 95 | 127, 31 |
| 5 | 23 | 5 / 63 / 339 | 5 | 95, 3 |
| 6 | 93 | 10 / 65 / 384 | 2 | 7, 1 |

### Level 0 second pass (2026-10-06): the labyrinth

The user's complaint about the lattice above: "vast hallways that seem to stretch forever in a straight line"; Level 0 should be "a twisting and turning labyrinth of unlikely rooms and hallways", after the lore and the 2026 film. The film's sets were built as a "labyrinth", "endless corners", "one long corridor that turns into a never-ending labyrinth", with half-remembered architecture and some verticality (ramps, crawl spaces); Kane Pixels' footage is hallways that turn hard every few dozen feet and rooms that open into rooms. The cause was structural: every third lattice line was a three-wide main that was never broken, so it ran straight to the edge of the level.

Replaced (`WorldLayout.Level0.cs`) by:
- **Districts** about 44 blocks (± 7) each way, laid like bricks: each row is shifted by a hash, each wall between two districts is jittered on its own, so no wall line continues into the next row. District walls are gapped about every 11 blocks (always at least one gap per side); between two pillar halls there is no wall.
- **In each district:** a BSP of rooms with unbroken straight walls (22% stop short or have a 3–7 wide break, giving L-shaped rooms), some leaves kept as set pieces (big room, cell rows, pits). Then **hallways wind in from the gaps** (60–75% of gaps, 40% in open offices): 2 wide (15% 3), runs of 6–16 (15% 17–26), hard turns biased 3:1 to zigzag rather than coil, 2–5 turns; they stop on meeting another hallway, open into a set piece (60%), or end blind (chalk cross 40%). Hallways get flank walls. Scraps under 6 tiles or 1 wide are filled in. Then **every piece of floor is joined** by a spanning tree of doorless openings (2 wide 85%) plus extra openings (50% onto hallways, 60% into set pieces, 25% room to room); anything still cut off is broken through along the path with least wall.
- Lights: hallways keep a row of panels down the middle lane; rooms keep the per-area lattice. Region zones, Manila, Red Rooms, edge hallway, wear near Level 1 unchanged.

Measured (seeds 56693014 and 1234, 384×384 at ring middle): straight hallway runs p50 8–9, p90 15, max 26–29 (was unbroken for hundreds of blocks); view p50 17–21 (was 24); the remaining long views (p90 ~120–140) are pillar halls. `validatelevel 0` and `reach 0`: zero unreachable floor on three seeds. ~1 ms per cell. Renders: `docs/level-review/after-level0-labyrinth*.png` (green = hallway). Harness: `L0HALL=1` writes `hall.bin`, `hallview.py` overlays it; `timing` mode. Not yet play-tested; verticality from the film (ramps, low crawl passages) is not done: Level 0's column builder supports neither stairs nor `Tile.Low`.

## 1. Diagnosis

### 1.1 The shared mistake: structure that stops at the cell

The world is a grid of 32-block macro cells, each laid out from its own RNG (`WorldLayout.BuildMacro`). Edges between cells are a pure function of the edge. That guarantees chunks agree, but it also means that **anything decided inside `BuildLevelN` cannot be larger than 32 blocks**, and anything decided per cell switches on a 32-block line.

Compare the levels that read as places with those that do not:

| Reads as a place | Why |
|---|---|
| Level 1 car park | Columns, aisles, stair cores and paint are global functions of `gx, gz` (`Level1.cs:191-284`). A 45×51 unit repeats across cells seamlessly. |
| Level 5 hotel wings | `HallPeriod = 12`, `CrossPeriod = 33` are global; wing-to-wing edges copy the grid (`Level5.cs:61-95`). Corridors run 100+ blocks. |
| Level 9, 11 | Global street grids; Level 11 plans a whole 83×61 block once and caches it (`Level11.cs:154-170`). |

| Reads as noise | Why |
|---|---|
| Level 0 | Recursive split per cell, with 1–2 gaps *and* a 35% "stop short" per wall, a 30% merge per edge, and edges that are 50/50 wall/open in 3–8-block runs (`Level0.cs:127-161, 272-306`). Nothing encloses anything. |
| Level 2 | Every cell is a hub at a random point with 12-odd spokes to its edge passages (`Level2.cs:49-68`). Same topology every 32 blocks, jittered. |
| Level 6 | A perfect maze over 256 nodes *per cell*, 1-wide passages, 3–5 openings per edge (`Level6.cs:86-117`). |
| Level 4 office blocks | A global lattice, but period 8 with nothing above it: identical 4×4 rooms, 2-wide slots, no hierarchy (`Level4.cs:240-311`). |

The fix is the same everywhere: **a skeleton layer computed from world coordinates at a scale larger than a cell** (hallways, tunnels, corridors, roads), with a hierarchy (main / minor), and cells filling in between. Where a block of the skeleton spans cells, the block is planned once from its own id and cached, as Level 11 does.

### 1.2 Measured

`tools/layout_metrics.py` over a 384×384 render of each level (seed 56693014; L0 at spawn, others at ring middle, 40°). *view* is, for every open tile, how far you can see along the longer axis; *width* is the shorter; *wallrun* is the length of the straight wall a wall tile belongs to.

| Level | wall % | view p10 / p50 / p90 | width p50 | dead ends % | wallrun p50 / p90 | Verdict |
|---|---|---|---|---|---|---|
| 0 | 13 | 14 / 33 / 136 | 11 | 0 | 8 / 20 | Open, not cramped; the problem is that walls are *short* and nothing is enclosed. |
| 1 | 3 | 212 / 384 / 384 | 159 | 0 | 3 / 10 | An unbounded plane. Reads as a car park; nothing ever ends. |
| 2 | 75 | 13 / 29 / 48 | 2 | 0.3 | 20 / 42 | Cramped by design, but every cell is the same hub. |
| 3 | 58 | 4 / 29 / 74 | 2 | 3.7 | 14 / 22 | Cramped, uniform: 2-wide lanes, a wall never more than 6 blocks away. |
| 4 | 14 | 7 / 127 / 255 | 31 | 0 | 6 / 15 | Office blocks are jail cells; open plan is a void with furniture islands. |
| 5 | 23 | 5 / 95 / 384 | 3 | 0.1 | 11 / 31 | Corridors good; rooms 3 deep; 20% of floor is locked pockets. |
| 6 | 47 | 3 / 7 / 15 | 1 | 4.3 | 7 / 14 | **Median sightline 7 blocks, max 45, one decision every 2 blocks, in the dark.** |

### 1.3 What the lore actually says about the three you named

- **Level 0.** "Mile after mile of randomly segmented rooms, hallways and stairs"; "no two rooms identical" yet "all rooms appear uniform". The 2002 photo is a **large open room with a free-standing partition wall**, drop ceiling, no doors. Kane Pixels is **long hallways that turn at hard right angles and open into big empty rooms; doorways too numerous; rooms proliferating like a hall of mirrors**. Doors are hallucinations: every opening is doorless. Structural aberrations: pillar halls "in a lattice, stretching for miles", arches "in dead ends and transition rooms", pits "in close groups, in a grid", blackout zones with recessed flooded floors, Red Rooms as "closed loops", the Manila Room as a rendezvous dead end. Ceiling height and hallway width are not stated anywhere.
- **Level 3.** "Hallways extremely inconsistent in dimensions": some "5 feet tall and 14 inches wide", some "as big as a mall food court", one "hundreds of feet tall". Brick, cables, black-sludge pipes, dim fluorescents, "indestructible metal bars block off many hallways and rooms: an extremely frustrating maze", with statues, murals and sludge pools behind them. Generator rooms, assembly lines ("extremely open and large, factory-like"), boiler rooms, Sanctums. Entities "lure a wanderer to a dead end". **Cramped is canon; uniform is not.**
- **Level 6.** "A seemingly endless series of tight hallways made of a smooth, cold material", total darkness, "light sources have no function", silent. "Taking a wrong turn at an indeterminate point may block off access to Level 7 and the entrance back to Level 5" — i.e. the maze is **coarse**: a few big decisions, not thousands of small ones. Exits: stairs down, found by "the faint sound of waves"; a wire to 6.1. Width and height not stated.

## 2. Principles for every level

1. **Skeleton first.** Each enclosed level gets a global network of ways (hallways, tunnels, corridors) that is a pure function of `(seed, gx, gz)`, with segments longer than a cell. Cells fill the blocks between.
2. **Hierarchy.** Two or three widths with meaning: a main way is wider, straighter, better lit, and goes somewhere; a minor way is narrower and may dead-end.
3. **Closed walls, few openings.** Enclosure is what makes a room a room. A wall has one opening, rarely two; it does not stop short unless that is the point (the Level 0 photo).
4. **Nothing switches on a cell line.** Zones, districts and plans are decided per skeleton block or by noise with features ≥ 64 blocks, never `per (mx, mz)`.
5. **One of a kind means one per region.** Set pieces (a lobby, a Beverly Room, an entry house, a transformer hall) are placed at one hashed cell per N×N-cell region, not rolled per cell.
6. **A sightline budget.** Each level gets target *view* and *width* numbers (section 7) and the harness measures them.
7. **Verifiability.** Every connectivity guarantee stays: main skeleton lines are never broken; every room chain roots on a way; `SealPockets`, `OpenGates`, `validatelevel` keep working unchanged.

## 3. Level 0: hallways and rooms

### 3.1 Target experience

Walk out of spawn into a large carpeted room with one partition wall jutting into it. Leave by a doorless opening into a 2-wide hallway that runs 40 blocks, turns hard right, runs 20, and opens into another big empty room. Off the hallway, openings every few blocks into small identical rooms, some leading on to further rooms, some dead. Now and then the hallway just ends. Every few hundred blocks the character changes: a pillar hall, an arch area, a blackout zone. The geometry is office back-of-house: rectangles, right angles, consistent widths.

### 3.2 Structure

**Hallway lattice.** Global lines in both axes. Line *k* in X sits at `x = 36·k + jitter(k) ∈ [−6, +6]`, likewise Z; pitch varies 30–42 so the blocks between are 28–40 blocks each way (one to two cells; this is why blocks must be planned by id, see 3.4). Each line has a width per line: 2 (60%) or 3 (40%).

**Segments.** A hallway line is cut into segments between consecutive crossings. Each segment is kept by hash with `p = 0.7` on *minor* lines; every third line in each axis is a *main* line and is never broken. Main lines guarantee global connectivity; broken minor segments make T-junctions and dead ends. A kept segment whose far end is dropped is a dead end: Kane Pixels' "hallway that ends in a wall". Dead ends get the chalk X treatment that Level 6 already has.

**Jogs.** At 15% of crossings on minor lines, the line steps sideways 4–8 blocks before continuing: the hard right followed by a hard left.

**Blocks.** The rectangle between four hallway lines is a block, 28–40 blocks a side. Its kind is hashed per block id, with Voronoi over block ids at scale ~4 blocks (≈ 140 blocks) so kinds come in areas:

| Block kind | Share | Layout |
|---|---|---|
| Rooms | 50% | Subdivide into rooms (3.3). Every room chain opens onto a hallway. |
| Big room | 15% | No subdivision. One room the size of the block, with 1–3 free-standing partitions 6–14 long, 20% L-shaped (the photo). One or two 1-block columns. |
| Pillar hall | 12% | Block is open; pillars on a global lattice as now (`BuildPillars`), spacing 5–8, continuous across blocks of the same area. Hallway walls are dropped where a pillar hall meets a hallway: the hall "stretches for miles". |
| Arches | 8% | Rooms as above but every wall is an arch wall (`BuildArchWall`); carpet Soaked. Arch areas prefer blocks at the ends of dead-end hallways. |
| Blackout | 10% | Rooms, lights dead, recessed water rooms 15% as now, cold (`TemperatureAt`). |
| Pits | 3% | A big room with a grid of 2×2 shafts as now (`Room()` pit branch) but the room is the whole block and the carpet runs down the edges. |
| Red Room, Manila | rare | As now, but one per region and sited at a dead-end block. |

**Spawn block** is always Big room with one partition, two supply boxes as now.

### 3.3 Room subdivision rules (replaces `Split` / `BuildWall` / `Room`)

- Recursive binary split as now, but `MinRoom = 5`, and the stop chance biased so rooms are mostly 6–12 a side with a few 15–20.
- **One opening per wall** (2 wide; 1 wide for 15%), **two** only on walls ≥ 16 long. Never a "stop short" cut.
- No 30% edge merges, no 50/50 edge runs. Edges between cells are whatever the block plan says (3.4).
- Each room must be reachable from the hallway by a chain of openings; the split tree gives this for free if every split wall has an opening, so keep that invariant.
- 20% of rooms are **closets**: 3×3–4×4 with one opening, off a bigger room.
- 10% of blocks of kind Rooms are **cell rows**: a 2-wide internal corridor along one side with identical 5×4 rooms off it, every opening in the same place. "Doorways too numerous."
- Moods, stains, outlets, lights unchanged. Light lattices (`PlaceLights`) switch per *area* (Voronoi of block ids), not per 4-cell Region.

### 3.4 Implementation shape

- New `WorldLayout.Level0.cs` core: `L0Line(axis, k)` → position and width; `L0Segment(axis, k, j)` → kept / dropped / jogged; `L0Block(bx, bz)` → kind, and a cached `L0BlockPlan` (tile kinds for the whole block, computed from `Rng(seed, bx, bz)`), as `Level11.cs` caches block plans. A cell touches at most 9 blocks.
- `BuildLevel0` copies the plan tiles that fall in the cell; `Level0Edge` consults the same plan for its line so both neighbours agree (edges are no longer random).
- Keep `Region` only for `PrimaryPattern` and light lattice, re-keyed to areas.
- `WearAway`, `PlaceStash`, `PlaceDen`, `MarkWayToGates`, `IsRedRoom`, `IsManilaMacro` work on tiles and stay; Red Room and Manila selection move to "one per 12×12-cell region, at a dead-end block".
- Delete `BuildOffice` (becomes Big room) and the `sameRegion` merge logic.

### 3.5 Targets

wall % 25–35 · view p50 12–20, p90 ≥ 60 · width p50 4–8 · wallrun p50 ≥ 12 · hallway dead ends 10–20% of minor segments · `validate` reachability unchanged.

## 4. Level 6: a coarse maze you can navigate by touch

### 4.1 Target experience

Darkness is the level; the layout must be fair in it. You walk a smooth, 2-wide corridor for 40–80 blocks with your hand on the wall. Junctions are rare and you feel them: the floor turns wet in the side passages. Side passages are shallow mazes that mostly end, and the dead ends are chalked. The main corridors go somewhere: every few hundred blocks a chamber, and deeper in, stairs, with the sound of waves getting louder along the trunk. Take the wrong trunk and it ends after 300 blocks — that is the lore's wrong turn, and the way back is the wall you came along.

### 4.2 Structure

- **Trunks**: 2-wide corridors on a global lattice, pitch 96 blocks (3 cells), jittered ±10 per line, continuous across cells. Per 4×4-cell super-block (128 blocks), a spanning tree over trunk nodes decides which trunk segments exist (hash per super-block, straight-continuation bias 0.75 so trunks run 150–400 blocks before turning), plus 10% extra segments for loops. Trunk dead ends are allowed: 1 in 6 trunk ends is blind, and that is the "wrong turn".
- **Side mazes**: off a trunk, 1-wide passages on a 6-block pitch (not 2), depth ≤ 4 nodes, a growing-tree maze with straight bias 0.6, so a side maze is 20–40 blocks deep and mostly dead-ends. At most one side-maze entrance per 24 blocks of trunk. Side passages are `L6Wet` floor (the tactile cue); trunks are dry.
- **Chambers**: 5×5–9×9 at trunk nodes, 1 in 4; stairs down (`Unders.Descent`) in chambers with `depth > 0.5`, chance rising with depth as now; waves audible along the trunk leading to them (AtmosphereSystem already plays L6 sounds; add a wave cue scaled by distance to the nearest descent, which `FindArrival`/threshold code can locate).
- **Edges**: `Level6Edge` returns Open exactly where a trunk or side passage crosses, computed from the same lattice; no random 3–5 openings.
- **Snackrooms**: 5% → 1.5% of cells, must also be ≥ 4 cells from another; a tripwire always within 48 blocks of one along a trunk.
- **Chalk**: `MarkWayToGates` extended to mark the way to descents along trunks (arrows every ~40 blocks, 60% of segments), and X at every dead end (now 35%).

### 4.3 Targets

wall % 60–75 (sparser corridors; what matters is decisions, not wall) · view p50 ≥ 12, p90 ≥ 40 · width p50 2 · junctions ≤ 1 per 12 corridor blocks on trunks · dead ends ≤ 2% of open tiles · every cell's trunk tiles reachable from spawn arrival (`validatelevel 6`).

### 4.4 Lighting (decision for the user, section 9)

The geometry is the fix. Two cheap, lore-safe aids if it is still too hard in play: raise `BrightestLight` reach in `AtmosphereSystem` so a lantern shows 6–8 blocks instead of ~4, and let the Level 6 map remember the trunk you walked (`Level6RevealRadius` 1 → 2 along trunks).

## 5. Level 3: inconsistent on purpose

Cramped is canon. The change is **variance**: squeezes *and* halls, districts with different lattice pitch, and a few huge spaces.

- **Districts** by noise at scale 6 cells: pitch 8 (as now, 40%), pitch 12 (35%), pitch 16 (25%). Lanes 2 wide; in pitch-16 districts the main lanes (every second) are **galleries 4 wide and 4 high** (set `Tile.Grand`; `Level3Block` must honour it like `Level5Block` does, `WorldGenerator.cs:1150`).
- **Squeezes**: 15% of tree links are 1 wide as now, and half of those are **2 high** (a new `Tile.Low` flag, or `Height` byte: ceiling block at rel 3; the player fits, barely). Mark the far end with a danger sign.
- **Halls**: one per 5×5-cell region at a hashed 2×2-cell site: a transformer hall or an assembly line spanning 64×64, 4 high, with rows of machines and conveyors, 2–4 entrances. Replace the per-cell 4% `transformerHall` roll. The Sanctum stays rare but becomes one per 8×8 region, always at the end of a lane behind a doorway, never on a through route.
- **Bars** stay, but make the tree links straighter (DFS with continuation bias 0.7) so lanes run 24–60 blocks between turns; bars go on 50% of loops as now, plus at 1 in 5 room doors (the "behind bars" set pieces: statue, sludge pool, mural, train parts; the props exist except the mural).
- **Lights**: dark sections are already 35% of 20×20 squares; make them per lane segment instead, so a whole run goes dark.
- **Edges** follow the district pitch (`Level3Edge` lattice positions depend on pitch; both sides of an edge are in the same district by construction if districts are decided at the pitch-16 line granularity).

Targets: width distribution bimodal (p10 = 1, p90 = 4) · view p50 ≥ 20, p90 ≥ 90 · wall % 45–55.

## 6. The other levels, briefly

Each from its audit; these are smaller than sections 3–5 and can be ordered as the user likes.

### 6.1 Level 2 (Pipe Dreams): same machinery as Level 6
- Replace hub-and-spoke with a global lattice: **mains** 3 wide on a 64-block pitch (±4 jitter per section, so straight 60+ blocks), **secondaries** 1–2 wide on a 16 pitch kept with p ≈ 0.45 and tied to the mains by a spanning tree per 64×64, +20% loops. `Level2Edge` becomes "where the lattice crosses".
- Wide sections: a 5–7 × 12–20 pump gallery at 1 in 3 main/main crossings, machinery and steel doors there; 3×3 storerooms only off secondaries.
- Series wiring per segment: all on / all off / all flicker per run between junctions (`Level2.cs:276` uses 24×24 squares now). Pipes continuous through junctions; junction boxes only at lattice crossings. Leaks concentrated in "wet" segments.
- Targets: view p90 ≥ 100 on mains, width p50 2–3.

### 6.2 Level 1 (Habitable Zone): compartments and districts
- Districts 3×3 cells (snap to 90×102): car park (now), racking warehouse (1-wide pallet racks 2–3 high, 3-wide aisles, cross aisles every 27), open hall (2×2 columns on 18×17), loading dock band. Hall sectors use the same district grid, not cell noise (`Level1.cs:57`).
- Fire walls on district edges: full-height concrete, 4-wide openings every 27–36 aligned with aisles, rebar damage on 5–10% of tiles. Sightlines end somewhere.
- Main drive lanes: every 4th aisle 10 wide with a continuous light strip; every 2nd cross aisle a trunk that runs through fire walls.
- Signage with information: letter from `FloorDiv(gz, 17)`, number from `FloorDiv(gx, 9)` (now `Mod(px, 6)` cycles A–F, `Level1.cs:225`).
- Hall hierarchy: every 4th lattice line 4 wide; close 25% of minor segments; jog 10%.
- Cluster clutter: one staging row per district full of crates, 60% of rows empty; puddles under sprinkler mains.

### 6.3 Level 4 (Abandoned Office): hierarchy and cores
- Primaries 3 wide every 64 blocks, troffers every 3 (80% lit); secondaries 2 wide every 16; rooms double-loaded, 4×5 interiors, conference 6×8 at secondary ends. `L4OfficeGrid = 8` with 4×4 rooms goes.
- **Building core** one per 4×4 cells: elevator lobby 4 wide with 2+2 doors, restrooms (Toilet prop exists), signed stairwell, fountain, cooler. Remove Stairwell/Elevators from the per-room roll (17% of rooms now).
- Open plan bounded by primaries; columns on an 8 grid coinciding with corridors; ghost desks on a global 4×9 module so rows cross cells; 85% of cubicles cleared (lore: nearly no furniture), one intact farm per region.
- Windows only on global perimeter lines (every 192 blocks), continuous, with a 2-wide walkway; delete the 30% random window edges (`Level4.cs:41-49`).
- Hang `CableDroopX/Z` under missing ceiling tiles.

### 6.4 Level 5 (Terror Hotel): rooms, numbers, ends, one lobby
- **Bug:** boiler-to-boiler edges are fully Open, so `ToAisle` clears every column and strips the bays (`Level5.cs:584-595`). Clear only aisle-aligned indices.
- **Bug:** wing-to-grand west edges inside a cross corridor become 28 consecutive doorways (`Level5.cs:104-108`); the fallback at 15–16 can open into a sealed room.
- `HallPeriod` 12 → 16: rooms 5 deep with a 2×2 bathroom alcove.
- Sequential numbers from corridor and room index (odd one side, even the other), full digits; "Rooms 401–419 →" signs at cross corridors.
- Every 4 spans (132 blocks) a corridor ends in a set piece (glowing window, seating nook, or a 6×8 elevator lobby with one lift out of order) and the next segment is offset half a period.
- Lobby: one per 4×4 cells, 64×64 footprint: single front desk on axis, 3-wide grand staircase, columns on 8, 4–5 chandeliers on the axis, wings radiating from four doorways; Dining and Beverly attached to it, Beverly once per lobby (now 5% per cell).
- Service spine: every 3rd back wall a 2-wide staff corridor, STAFF ONLY doors, linen, leading to boilers (boilers reachable only from it).
- Light cross corridors at the 4-block cadence.

### 6.5 Level 7 (Thalassophobia)
- One entry house per 8×8-cell region (12×16, furnished like a Level 9 interior, trapdoor to the sea) instead of 14% of cells (`Level7.cs:139`).
- Islands with height `1 + 3·(Fbm−0.55)/0.45`, rock pillars to the ceiling where > 4: landmarks. Boulders by hash, not `(7gx+13gz) mod 11` (`:55`).
- Seamount ridges `1−|Noise(/120)|` up to +40; L8 cave mouths on their flanks; the canon wooden door at depth ≥ 75.
- Replace the 6×6 ceiling glow grid (`Deep.cs:325`) with noise patches.

### 6.6 Level 8 (Cave Systems)
- The 9th Road as **sparse radial roads** (one per ~400 blocks of circumference, meander ±60 at scale 200, L7 side → L9 side, cross-links at 1 in 3 settlements) instead of a 48-block lattice; gate the L8 boundary like other levels (now every road line is a doorway, `WorldLayout.cs:257-266`).
- Tubes from two noises (`|a| < 0.06 && |b| < 0.06`), cave band up to rel +20 so chambers swallow the road for 20–40 blocks; road y follows `Noise(/150)` ±12 with bridges.
- Settlements as domed chambers (r 14 × 9), named.

### 6.7 Level 9 (Suburbs)
- Lore roads are unpainted and leaf-covered: drop markings and 80% of stop signs (`Level9.cs:128-137`).
- Field lots 6% → 1%, only at `RingFraction > 0.66`.
- Landmark lot pairs 1 in 40 blocks (park, church, strip mall); the "two houses clipped inside each other" at 1 in 200; every 5th street curved ±8 or a cul-de-sac; arrow signs toward the city at 1 in 6 junctions.

### 6.8 Level 10 (Bumper Crop)
- Roads bound fields (hedges along `FarmRoadAt` 0 and 3); field kind per (field, road side); road profile track-grass-grass-track; flax → barley.
- Driveways from every farmstead to the nearest road; a lone shed at 20% of field vertices; hedge gaps hashed per segment (now `(gx+gz) mod 70`, `Level10.cs:166`); one road in 4 bends toward the city with mileposts.

### 6.9 Level 11 (Endless City)
- Lamps 85% lit (now 12%, `Level11.cs:1408`); lit windows in 40% of enterable buildings; a canal on one avenue in 8 with bridges; an elevated rail on one street in 6. Lowest priority; the level already reads.

## 7. Cross-cutting work

### 7.1 Block plans
A small generic `BlockPlanCache<TPlan>` (`ConcurrentDictionary<long, TPlan>`, factory from `(seed, bx, bz)`), extracted from the Level 11 pattern, used by Level 0 blocks, Level 6 super-blocks, Level 2 64-blocks and Level 1 districts. Bound it (e.g. keep the last 4096 plans) since the world is unbounded.

### 7.2 Tile height
`Tile.Grand` gives 4-high today (Level 1, hotel grand rooms). Generalise to a 2-bit `Height` (2, 3, 4) so Level 3 can have 2-high squeezes and 4-high galleries, honoured in `Level3Block` and in `WorldLighting`'s absorption. `MaxRoomHeight` stays 4, so the lighting band and `WorldGeometry.Contains` do not move.

### 7.3 Harness
- Promote the scratchpad `mapgen` harness into the repo (`tools/mapgen/`, compiling `src/Worldgen/*.cs` as it does now) so every session uses the same one. Decision for the user (9).
- Add a `metrics` mode mirroring `tools/layout_metrics.py` (wall %, view/width percentiles, dead ends, wallrun, small pockets) per level, and a `report` mode that renders every level and prints the metrics table, for before/after.
- Keep `validate`, `validatelevel`, `links`, `deep` green after every level.

### 7.4 Things that must keep working
Gates (`OpenGates`, `MarkWayToGates`), dens, stashes, picked-over marking, notes, Reality (`WorldLayout.Reality.cs`), thresholds (`FeatureOrigin` for multi-tile features), arrival search (`FindArrival`), entity placement (`WorldLayout.Entities.cs`), the map's line-of-sight reveal, and the guide text in `tools/gen_guide.py` ("The Levels" section) where descriptions change.

## 8. Phases

| Phase | Work | Files | Done when |
|---|---|---|---|
| 1 | Block-plan cache, `Tile.Height`, harness `metrics` + `report` modes, before-table committed | `WorldLayout.cs`, `Tiles.cs`, `WorldGenerator.cs`, `WorldLighting.cs`, `tools/mapgen` | `report` prints the table in 1.2 |
| 2 | **Level 0** per section 3 | `WorldLayout.Level0.cs`, `WorldLayout.cs` (`Level0Edge`), lights | targets 3.5; `validate` green; a render that looks like the photo |
| 3 | **Level 6** per section 4, plus wave cue and chalk | `WorldLayout.Level6.cs`, `WorldLayout.Gates.cs`, `AtmosphereSystem.cs`, `Map/BackroomsMapLayer.cs` | targets 4.3; `validatelevel 6` green; `links` green |
| 4 | **Level 3** per section 5 | `WorldLayout.Level3.cs`, `WorldGenerator.cs` (`Level3Block` heights) | targets in 5 |
| 5 | Level 2 lattice (shares phase-3 code), Level 5 bugs + rooms + lobby, Level 4 hierarchy + cores | `Level2.cs`, `Level5.cs`, `Level4.cs` | targets 6.1; hotel boiler bays intact in a render |
| 6 | Level 1 districts; Levels 7–10 touch-ups; Level 11 lamps | `Level1.cs`, `Level7-10.cs`, `Level11.cs`, `WorldGenerator.Deep.cs`, `CaveColumn.cs` | audits' problems closed |
| 7 | Guide text, README level descriptions, `docs/level-review/after-*.png`, play-test with the user | `tools/gen_guide.py`, `README.md` | user sign-off per level |

Each phase ends with the renders and the metrics table, so the user can judge a level from a picture before it is played.

## 9. Decisions for the user

1. **Level 0 hallway width**: 2 wide (Kane Pixels, claustrophobic, one player passes) or a 2/3 mix (recommended: 60/40 per line) so two players can pass in some.
2. **Level 0 ceiling**: keep 3 everywhere (recommended: the drop ceiling is the familiarity), or let Big rooms be 4 high.
3. **Level 6 light**: keep "light barely works" exactly as now and fix only the geometry (recommended), or also extend lantern reach to 6–8 blocks and remember trunks on the map (4.4).
4. **Level 3 squeezes 2 high**: yes (recommended; needs `Tile.Height`) or keep every passage 3 high.
5. **Level 8**: single radial 9th Road (lore, navigation becomes a search) or keep the lattice (easy to navigate; you have not complained). Recommended: radial roads, phase 6.
6. **Harness in the repo** (`tools/mapgen/`): recommended yes.
7. **Order of phases 5 and 6** against the survival-loop plan, which also touches Level 0 (gate cells, ring sizes). Recommended: this plan's phase 2 first, since the hallway skeleton is what gate cells and chalk arrows will live in.
