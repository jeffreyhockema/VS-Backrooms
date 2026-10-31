# Level 0 arch areas: redesign plan

Status: sections 2-4 describe the first attempt, replaced by section 5 ("Second redesign", what layout version 10 does now; the stucco look, the joins and the header stay). First attempt: built in layout version 10 (`WorldLayout.Level0.Arches.cs`; `archcheck` in the harness). Changes from the plan: rows of rooms stack behind the street's rooms (each opens through two or more bays onto the row before it) where a side is deeper than nine blocks; an end gap opens onto whatever lies behind it, so no vestibule is carved; of two gaps side by side the second is closed. Goal: arch areas that read as a distinct place (plain cream stucco, not pale wallpaper) and whose rooms and arches meet in a way a player can move through. All layout changes sit behind layout version 10 (`Version >= 10`, unreleased); versions 1-9 stay byte for byte.

## 1. What the lore and depictions show

- Wikidot Level 0 (https://backrooms-wiki.wikidot.com/level-0) is the only source that mentions them: "The first notable differentiation is pale walls with archway holes decorating them."; "they generally show up in dead ends or adorn transition rooms."; "Carpet depth is notably extensive in these sections"; "Archway rooms are the most stable; they tend not to shift or change behind you". Photo caption: "A yellowish beige room with a wall of archways." So: pale (not yellow) walls, arch holes as decoration of a wall, plush carpet, calm and stable, found at dead ends and between regions.
- The Fandom Level 0 page and its API could not be fetched (HTTP 402), and a web search found no arch material beyond Wikidot. Treat Wikidot as the whole canon here. Miraheze was not reachable in this pass.
- Kane Pixels' footage and the 2025/26 film: no arched doorways turned up in what I could find (production design by Danny Vermette, about 50 wallpaper tests for the yellow: https://www.motionpictures.org/2026/06/how-production-designer-danny-vermette-made-backrooms-real-portals-platforms-practical-terror/). The mod's rule stands: yellow paper is the baseline and the arches are the one sanctioned departure.
- Not to borrow from: the Poolrooms (Level 37, tile) and the Level 3 Sanctum (stone vault).

Takeaway: arches are a transition architecture (calm, pale, plush), and the signature image is a wall of archways. They are not a labyrinth variant.

## 2. What is wrong today

Source: `src/Worldgen/WorldLayout.Level0.cs`. An Arches district (`ZoneKind.Arches`, 9% of regions, `Region` roll `r < 0.91`) runs the ordinary labyrinth planner: `LabSplit` cuts rooms, `LabWall` makes every wall an `ArchWall` (a pier every third tile, pairs of `ArchWindow` half walls, one or two pairs forced to `ArchDoor` at a random offset), `Worm` carves 2-wide halls from the district gaps (`wormChance` 0.5), and `MendArches` plus the door passes patch the result. Walls are `WallPattern.Cream` (`gen_textures.pattern_cream`, `CREAM_DIM` 0.94) with the yellow's baseboard.

Plans from the harness (`mapgen <seed> <cells> peek x z r`, seed 1; `%` pale wall or pier, `n` half wall, `a` arch opening, `#` yellow wall). Crop of the district around 512476,512884:

```
.%..................%..........%.........%....
.%..................n..........%.........n....
.%%nn%nn%nn%nn%nn%nn%nn%nn%nn%nn%na%aa%nn%....   <- 35 blocks of wall, one 2-wide way through
.%.....................%.................a....
.%.....................n.................n....
#%..%%%%%%%%%..........n.................n....
.a..........%..........n.................%....
.a..........%..........%.................n....
.%..%%%..%..%.%nn%na%nn%nn%nn%nn%nn%nn%nn%nn%n
.%...............%.....%.......%.....%........
```
Around 511541,512251:
```
%%%%%%%%%aa%%aa%%%%%%%%%%%%%%%%%%%%%
%.......%..%%..%%....%..............%
%.......%..%%..%n....%..............%   <- doubled "%%" walls where a hall was cut through
%..........%%..%%....%..%%%..%%%%%..%
%.......%%%%%%%%%%%%%%%..%...........
%%nn%nn%an%nn%nn%nn%nn%%..%.........a   <- a wall of windows, its one door at an end
%.........n........n...%..%.........a
```
Stubs and orphans, 512476,512884 again:
```
.%..%%%%%%%%%..........n...........
.%..%....%.............%...........     boxes of wall with no way in, piers standing alone
.%..%....%.............%.........a.
```

Faults:
1. **Walls of windows hide rooms.** `LabWall` makes a whole wall of half walls with one or two pairs of doors. A 35-block wall has one way through; rooms are seen but not reachable and nothing says where the door is.
2. **Arches with no shape.** Openings are 2 wide at random offsets, then `MendArches` converts mismatched halves to wall, so arches are lost and rooms end with a lone 2-wide slit as the only exit.
3. **Worms cut through arcades.** The 2-wide halls run into arch walls, leaving doubled walls (`%%`), stubs, orphan piers, and halls that end in a row of windows.
4. **Same planner, same texture.** Rooms are labyrinth cells with a tinted wallpaper (the `CREAM_DIM` fix shows the pale paper was "a fifth brighter than the yellow", a tint, not a place). Half walls are used everywhere, not where a parapet makes sense.
5. **Joins are right in principle.** `PaperJoins`/`ArchGap` make a 2-wide `ArchDoor` at district gaps and flip each face (`L0FlipBits`, `Tile.Detail`). Keep it, but what lies behind the arch should be a vestibule, not a random room.
6. **Lights and boxes ignore the piers.** The region light grid (spacing 3 or 4, random phase) lands over piers, and `PlaceBoxNearWall` drops boxes in the middle of an opening's floor.

## 3. The redesign

### 3.1 Look

Plain cream stucco on every wall, pier and soffit; no print.

- **New pattern `WallPattern.Stucco`** (layout 10), parts `plain`, `upper`, `baseboard`, `rail`, `outlet` (the engine looks all of them up), plus `soffit`. Made in `tools/gen_textures.py` beside `pattern_cream`, on `matlib.plaster` as ground: `M.plaster(seed, base=(226,216,182), grain=3, mottle=7, roller=0.15, bumps=0.02)`, then a sand-float layer: short trowel arcs of +-3 levels, tiny pale and dark grains on about 6% of pixels, a hairline crack in one version of three (and a `-damp` version like the others). Edges tile (shared ground and `turn_safe`/`inside_block` as the plaster ceiling does).
- **Colour.** Yellow paper ground `D7D48A` (215,212,138); today's pale paper averages about (219,212,175). Stucco mean (225,216,182): clearly less saturated than the yellow (blue +44 over it against the paper's +37) and within 2% of the paper's luminance, so block light is unchanged (the `CREAM_DIM` lesson: judge by measured mean, not by eye). The difference from the wallpaper is texture: paper is smooth with strip seams and a print; stucco is stippled, seamless, no motif.
- **Baseboard:** a rendered plinth: the bottom 3 px a step (about 10%) darker with heavier grain and a lit, rounded top edge, in place of the paper's thin dark board. Same height as the yellow's, so trim lines still run across a join. Outlets: the stucco ground.
- **Arch header and piers:** header model unchanged (`gen_l0_walls.arch_header`, 11 px rise), `#wall` becomes `stucco-plain`, soffit `stucco-soffit` (smooth plaster on the same base).
- **Carpet and ceiling:** unchanged (standard `Carpet`; the lore says deep; ceiling tile with the troffer grid).
- **Join walls:** `gen_l0_walls.paper_join` gets a `stucco` state beside `chevron` and `cream`.

### 3.2 Layout: the arcade district

The unit is a **bay**: one pier tile and a two-tile opening (3 along the wall), the existing `ArchWall` rhythm, so `ArchPier`, the header model and the pier-pair rule stay. On v10 an Arches district is planned by a new `PlanArches` in place of `LabSplit`/`LabWall`:

1. **A spine (the "street").** A 5-wide hall along the district's longer axis, offset 0-6 blocks from the middle, from one district gap toward the other (the `openings` list). Both long walls are **full arcades**: every opening an `ArchDoor`, no half walls. The street ends in a threshold arch (3.3) or, at most once per district, a plain stucco **dead end** 5 wide (the lore's "dead ends"), with a supply box.
2. **Rooms off the arcade.** Each side of the street is cut into rooms 8 wide (three bays) by 6-9 deep. Dividers sit on piers, so a divider never ends against an opening. A room opens through three bays, all `ArchDoor`, except that in about half the rooms **one outer bay is an `ArchWindow`** (a half wall). That is the only place half walls occur. Every room therefore has at least two walkable arches (4 blocks of opening), never a lone slit. About 30% of the dividers between neighbouring rooms get a 2-wide `ArchDoor` (an enfilade), so rooms form loops.
3. **Cloister variant** (one district in four, W and H >= 30): instead of a street and rooms, 2 or 3 parallel arcade rows cross the hall every 5-6 blocks, all `ArchDoor`, piers aligned, so you walk through repeated arches either way. The hall's edge follows the district walls and the openings join at its ends.

Size: the district's own size (30-58 blocks), so 6-10 rooms. Arch areas span one to three districts because zones come from regions. Frequency unchanged (9% of regions). `wormChance` for Arches is irrelevant (the street is the hall).

### 3.3 Meeting the yellow rooms

`PaperJoins`/`ArchGap` stay: where a pale district meets any other, the gap becomes a 2-wide `ArchDoor` and each face takes the finish it looks onto. New: **the opening lands on a vestibule.** A gap in the arch district's west or north wall is joined to the street (or cloister) by a straight 2-wide hall at most 6 long, never carved through an arcade, ending on the first open tile, so an arch is never in front of a wall. The header is visible from the yellow room.

### 3.4 Lights and boxes

- Lights: for Arches on v10, force `LightSpacing` 3 and place the piers by the region's `LightPhaseX/Z` (bay origin chosen so a fixture sits over the second opening tile of every bay along the street). The street gets the standard fixtures. Blackout is untouched.
- Supply boxes: only inside rooms, on a tile against a wall that is not next to an `ArchDoor`, about one per two rooms; none in the street.

### 3.5 Plans at block scale

Legend: `#` wall, `%` pier, `a` arch opening (walkable), `n` half wall, `A` threshold arch to another district, `B` supply box, `y` yellow wall.

Plan 1, arcade street (28 x 23: three rooms to a side, street 5 wide):
```
############################
#........#........#........#
#........#........#........#
#........a........#........#
#...B....a....B...#........#
#........#........#........#
#........#........#........#
#........#........#........#
#nn%aa%aa#aa%aa%aa#aa%aa%aa#
#..........................#
#..........................#
#..........................A
#..........................A
#..........................#
#aa%aa%aa#aa%aa%nn#aa%aa%aa#
#........#........#........#
#........#........#........#
#........#........#........#
#........#........a........#
#....B...#........a........#
#........#........#........#
#........#........#........#
############################
```
Plan 2, cloister (25 x 17): arcade rows across a hall, all open, thresholds at both ends.
```
#########################
#.......................#
A.B.....................#
A.......................#
#.......................#
#aa%aa%aa%aa%aa%aa%aa%aa#
#.......................#
#.......................#
#.......................#
#.......................#
#.......................#
#aa%aa%aa%aa%aa%aa%aa%aa#
#.......................#
#.......................A
#.....................B.A
#.......................#
#########################
```
Plan 3, threshold (a yellow room west of an arch district, the vestibule, then a dead end):
```
yyyyyyyyyyy###########
y.........y#.........#
y.........y#.........#
y.........A..........#      A: 2-wide arch in the shared wall, pale on the east face, yellow on the west
y....B....A..........#
y.........y#.........#
y.........y#.........#
yyyyyyyyyyy#########a#      (the way on to the street is south)
                    ..
```
(Plan 3 is a fragment: the vestibule is the 2-wide stretch through the arch and joins the street one row south.)

### 3.6 Rules a generator follows

- Write `Kind` (`Wall`, `ArchDoor`, `ArchWindow`, `Floor`), `Pattern = Stucco`, `Base = L0Base(...)`, and `Pier` in the same way as `ArchWall`. Coordinates are district-local (`L0Plan.At(u, v)`; the west and north walls are the district's own, as in `PlanL0`).
- Every `ArchDoor` has floor on both faces; every pier is a wall tile with wall or district wall at its ends; no `ArchWindow` outside a room's own arcade wall; an arcade never touches another wall at an opening.
- Every room has at least two `ArchDoor` bays; all floor is one connected component (reuse `LabComponents` and the join passes). `MendArches` must be a no-op (assert it in the harness).
- No hall under 2 wide; the street is 5.
- `p.Rng` is used in a fixed order; for `Version < 10` the old path draws exactly what it does today.

## 4. Implementation outline

Files:
- `src/Worldgen/Tiles.cs`: append `WallPattern.Stucco` as the last value (existing numbers do not move; check every table indexed by pattern: `Paper()` in `WorldGenerator.cs`, `wallIds[pattern, part]`, decor tables).
- `src/Worldgen/WorldLayout.Level0.cs`: `PlanL0` (`Primary = Stucco` for Arches on v10), new `PlanArches` and `PlanArchCloister`, bypass of the arch branches of `PlanLabyrinth`/`LabWall`/`Worm` on v10, `PaperJoins` (`Paper(zone)` returns `Stucco` on v10), `L0Base`, `L0FlipBits` (stucco states), `PlaceBoxNearWall` and the light placement near `SaltLight` (about line 1345).
- `src/Worldgen/WorldGenerator.cs`: `Paper()`, `Level0Block` (`paperJoinIds` for stucco, `archIds`), block registration.
- `assets/backrooms/blocktypes/wallpaper.json` (add `stucco` to `pattern` states and `allowed`) and the `paperjoin` blocktype; lang entries if block names are shown.
- `tools/gen_textures.py`: `pattern_stucco`, plinth, `PATTERNS["stucco"]`, damp version, `stucco-soffit`. `tools/gen_l0_walls.py`: `paper_join` states and `#wall`. Run through `bash tools/locked.sh run python tools/<file>`.
- `tools/gen_guide.py` and `docs/GUIDE.md` (Level 0 arches line), plus the release notes.

Gating: everything above is `Version >= 10`. For versions below 10 Arches keep `WallPattern.Cream`, `ArchWall`/`LabWall`/`Worm`, and the current lights. The `Region` constructor's rolls must not change.

Verification:
1. `bash tools/locked.sh mapgen p7arches`; `LAYOUT_VERSION=1..9 mapgen.exe 1 6 layouthash` before and after: identical. The v10 hash will change (expected).
2. `peek x z r` on arch districts (`archspots` lists them); extend `Peek` to print a letter for `Stucco`. Add an `archcheck` mode over a 30-cell radius counting: rooms, rooms with fewer than two `ArchDoor` bays, `ArchDoor` with a wall on a face, `ArchWindow` outside a room's arcade, orphan piers, `MendArches` conversions, unreachable floor. Target: all zero.
3. `validate`, `validatelevel 0`, and `dark 0` (arch light must not fall below its neighbours); then shotbot at `archspots` cameras in a fresh v10 world, only when the client is free.
4. Texture: stucco mean luminance within 2% of `cream(0xE9E1BA)`; side by side with the yellow at 2, 6 and 12 blocks.

Risks:
- **Planner tail coupling.** `PlanLabyrinth` runs doors, scrap filling and component joins after the rooms; the new planner must meet their assumptions (`piece` masks, `noDoor`, openings reachable) or it gets filled in.
- **Gap symmetry.** District gaps are fixed by `L0Gaps`; a gap on a pier needs the vestibule to bend. If no way within 6, the neighbour must close the same gap (check `PaperJoins` and `L0Gaps` agree on both sides).
- **Block id arithmetic.** A new pattern changes `wallIds` and `paperJoinIds` sizes; a wrong order changes old worlds' wall textures (a visual regression, not a save break).
- **Legibility.** Stucco at 16 px can read as noise at a distance; compare before committing.
- **Lights.** Forcing spacing 3 may make arch regions brighter or dimmer than their surroundings; check with `dark 0`.


## 5. Second redesign

User feedback on the arcade street: "I still don't like the Level 0 arch area. Let's align it closer to the Wikidot example ... I like our walls and arch shape, but maybe closer to the half-height walls with arch, just as walls. And ... way more loot in the arch area this time." The stucco, the arch header and the joins stay; the layout goes.

### 5.1 What the photo shows

The wiki's "A yellowish beige room with a wall of archways" (http://backrooms-wiki.wikidot.com/local--files/level-0/2, 640x480): one big, empty, carpeted room (tan, stained carpet, a bucket and a bin at the left, a plain beige end wall with a rail, a drop-tile ceiling with troffers), perhaps 15 blocks wide and long. Down its right-hand side runs one long wall, and that wall is the arches: a half-height wall (about 55% of the room's height) with a row of round-headed openings above it, nine or more in the view, each opening a little narrower than the square pier between it and the next (openings about a block, so a bay is about three blocks of ours), and one continuous plaster band (the header) running over the whole row. Behind the openings is another room, lit yellow-green, with a patterned panel at the far end: the openings are windows onto a neighbouring room, not doors. Nothing in the picture is walked through; the room has its own plain walls and entrances elsewhere. The wall and arches are the same cream as the room.

So an arch area is an ordinary room with one wall of arched windows onto the next room. It is not an arcade you walk along.

### 5.2 Rules (layout version 10)

- An arch district is planned exactly as a Lobby district (`PlanLabyrinth`: rooms from `LabSplit`, the hall worms at the Lobby's chance, the Lobby's doorway passes), in `WallPattern.Stucco`, so room shapes, doorways and connectivity are the Lobby's. (Versions 1-9 keep the old arch labyrinth: `L0Plan.LegacyArches`.) No big rooms or cell rows, and no pits.
- Then `ArchWalls` (`WorldLayout.Level0.Arches.cs`) turns some walls into walls of archways. A candidate is a maximal run of wall tiles with floor on both faces (a window therefore always looks onto a room or a hall, never a wall, a pier or a sealed space), at least seven long (two bays); a wall crossing the run's end is the last pier, else the end tile stays a pier. A run is laid out as pier, `ArchWindow`, `ArchWindow`, pier, ... (the existing tile and header), the leftover 0-2 tiles plain wall at a random end, so most of the wall is arches. The floor is untouched, so connectivity and doorways are exactly the Lobby plan's.
- Which walls: each room (a floor piece before the doorways are cut) in random order gets one candidate wall, the longest first, and a room an opening of the district leads into (a transition room) or one with a single way out (a dead end) wants a second one half the time. No room has more than two arch walls (a hall three), so every room keeps plain stucco walls (corners, the district's boundary walls and walls with a wall behind are never candidates). A wall with three or more bays has a one in four chance of one `ArchDoor` bay, a full-height arch to walk under.
- Doorways are the Lobby's: the ordinary 1-2 wide gaps. Every room therefore has a real walkable opening, and the district is one piece of floor.
- Thresholds: unchanged (`PaperJoins`/`ArchGap`: a 2-wide arch in the shared wall, each face in its own finish, never onto a wall; the second of two gaps side by side is closed).
- Lights: the Lobby's region light grid, room moods and hall light rows (the first redesign's lamp lattice is gone). `dark 0` mean floor light, seed 1: arches 12.9, Lobby 12.4 (12.8 and 12.4 for seed 12345); no dark stretch of Level 0 lies in an arch district.
- Loot: the plan places no supply boxes of its own any more; arch districts get the same per-cell stash roll as the Lobby (`PlaceStash`, which keeps boxes off arches), so they are no richer.

### 5.3 Numbers

`mapgen <seed> 6 archcheck 30` (30 cells round spawn; targets zero):

| | seed 1 | seed 12345 |
|---|---|---|
| rooms (floor pieces with the doorways taken out) | 291 | 408 |
| rooms with no walkable opening (doorway or arch door) | 0 | 0 |
| arch windows with a wall or sealed space on either face | 0 | 0 |
| arch doors with a wall on a face | 0 | 0 |
| arches with no pier or no partner (`MendArches` would change) | 0 | 0 |
| unreachable floor of the arch districts | 0 | 0 |
| orphan piers (single free-standing pillars) | 21 | 25 |
| window tiles per room | 15.1 | 14.1 |

The orphans are single wall tiles the Lobby plan leaves where a wall stops short or a doorway is cut beside a crossing, not arch faults; the Lobby has 3.4 per 1000 wall tiles, the arch districts 0.5.

Loot, `mapgen <seed> 6 archloot 30`, supply boxes per 1000 floor tiles (Level 0's plan has no other loot containers):

| | first redesign, arch districts | second redesign, arch districts | Lobby |
|---|---|---|---|
| seed 1 | 4.17 (579 boxes / 138,962 tiles) | 0.57 (73 / 127,997) | 0.56 |
| seed 12345 | 3.43 (610 / 177,974) | 0.45 (72 / 160,460) | 0.56 |

(The first plan put a box in half its rooms and at every dead end on top of the stash roll: seven times the Lobby's density.)

`layouthash` 1-9 unchanged against the parent commit; `validate` and `validatelevel 0` clean (0 unreachable); headless world (seed 12345, `/backrooms dump 511764 511780 24`): an arch window is `wallpaper-stucco-baseboard` at floor level, air, `archheaderstucco` above (half wall, opening, header), and the doorways between are plain columns of air.

### 5.4 Plans

Legend as in 3.5 (`%` wall or pier, `n` half wall with arch, `a` full-height arch, `B` supply box). Seed 1, district at 511790,511714 (crop):

```
......................%%%%%..%%%%%%%%%%%%%%%%%.......................%..%..%%%%%%....
......................%...%..................%%%%%%%%%%%..%%%%..%%%%%%..%..%%%.......
......................%...%%%%%%%%%..%%%%%%..%.....%......n..........%..%..%%%.......
......................%...................n..%.....n......%..........%..%..%%%.......
......................%...................n..%.....n......n..........%..%..%%%..n...%
......................%...........%.......n..%B....%..........n......%%%%..%.%......%
......................%...........%.......n..%BB...n..........n......a.....%.%.......
......................%..%%%%%%%%%%nn%nn%%%..%%%%..n..........%......a.....%.%.......
```

Seed 12345, district at 511741,511758 (crop): rooms with a wall of arches on one side onto the next room, doorways in the plain walls.

```
..%.......%.......n..%%..%..........%........n......%......%........%...#
..n.......%%%%%%%%%..%%..%..........%........n......%......%..%%%%%%%...#
..%......%%%%%%%%%%..%%..%..........%........%......%.........n...%.....#
..n..................%%..%...................%%%%%..%.........n.........#
..%......%%%%%....%%%%%..%nn%nn%..%%%nn%nn%nn%.............%..n.........#
..n.......%...........%..%..........%........%......%%%%%%%%..n.........#
..%.......%...........%..%..........%........%......%......n..%%%%%%%%%%#
..n.......%..%nn%nn%nn%..%%%%%%%%%..%........%......%......%..%%%%%%%%%%#
```
