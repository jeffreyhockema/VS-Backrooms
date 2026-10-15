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
- (B2) A distinctive feature (crack, knot, joint, stain) in every texture of a surface tiles as a grid even at a random
  spot; give it to about one alternate in three beside plain ones (`matlib.alternates`; matlib defaults such features
  to 0). Model textures want wear scattered, not along the texture's edges.
- (B2) `preview_shapes.py` has a depth buffer since B2; earlier previews could hide thin plates and hardware.
- (B3) A JSON shape on a light block loses the cube's glow (face `glow` via `shapeByType` did not restore it) and the
  rooms round it went dark in the review world. Keep emissive fixtures as cubes; compare each shot's mean brightness
  with the baseline before any review, since a lighting fault makes every texture look worse.
- (B3) Judge large surfaces at playing distance (2-6 blocks in the wide shots), not on texsheets: low-frequency mottle
  and seams show more than expected and fine detail averages away. A motif dyed onto structured paper needs a darker
  print than the old flat colour.
- (B3) Floor variants placed in patches (stained carpet) have no good per-block texture answer: a tint shows hard
  squares, edge-faded stains a grid of spots. Keep the original look or solve it in the layout.
- (B3) Every batch makes per-family before|after pairs with `tools/shotbot/sidebyside.py` (map in
  `docs/design/graphics-pass/sidebyside/<batch>.json`, index `review/compare.html`) and adds its families to
  `decisions.md` for the user.
- (B11) A change to which block the world generator places does not show in a review world whose chunks already exist:
  shoot it in a fresh world (`batch.py --world <new name>` makes one at the same seed) and keep the baselines from `gfxreview`.
- (B11) Roofing built as tilted course boxes is seen at a grazing angle from the street, so the butt faces fill half the
  roof: keep them thin and in the shingle's own tone. Faces that must continue a wall's texture need world-aligned UVs
  (east u = 16 - z, west u = z, v = 16 - y; `preview_shapes.auto_uv`).

- (B4) Check a level's baseline before trusting it: retake two or three spots on a fresh build of unchanged `main`. Level 1's B0
  baseline had drifted 8-15 levels brighter than today's client; B4 reshot it (`review/baseline/1`, B0 set in `1-b0`).
- (B4) Painted lines across tiling blocks must be clean at the seams; wear on them breaks the line at every block edge.
- (B4) Removing a repeated painted feature reads as lost structure to a reviewer; keep it and shade it, let the user decide.
- (B4) On grey concrete keep `matlib.concrete`'s `patch_hue` and `hue` at 1.5 or less and aggregate at about 0.03, or it
  goes teal and olive with a coloured speckle at 2 blocks.

- (B5) A Reality Shift started in the review world never ends with the clock stopped and blacks out enclosed levels in
  every later session; `batch.py`'s header now runs `/backrooms shift 0` and `/backrooms stat stability 1`.
- (B5) Alternates of a large plain surface must share their low-frequency ground (same seed), only features differ,
  or the wall reads as a patchwork of block squares.
- (B5) A painted copy of a 3D feature beside the real one (a pipe band under pipe runs) reads as D; remove it.
- (B5) A block with no facing can carry modelled hardware on all four sides (`modelkit.turn`); against walls it is
  buried. Small vents want tilted louvres (`gen_shapes.louvre`), not `modelkit.grille` bars.

- (D1) A floor whose versions are turned at random shows every block edge if it has any broad mottle: a turned block's
  patches do not continue into its neighbour's, whatever the seed. `matlib.turn_safe` keeps each version's own broad
  field inside the block and blends it, toward the edges, into one shared field made four-fold symmetric, so any version
  at any turn meets any other. Build the shared `ground` without aggregate, pores or swirl (their ghosts symmetrise into
  a star), and on a grainless surface keep only part of the own mottle (`keep`), or a calm border round a mottled middle
  reads as cushions. Features on such a floor must fade out before the edge (`gen_textures.inside_block`).
- (D1) Judge tiling with a mock of the blocktype's real mix (versions and turns at random, 6x3 blocks or more) and the
  same mock averaged down 4x; a 3x3 repeat of one texture hides exactly the seams the player sees. The scratch helpers
  for this are described in the D1 report.
- (D1) A weighted alternates list is just the same texture listed more than once (`concretewall.json`: the cracked
  version once in eight). A per-pattern list on a shared blocktype goes in `texturesByType` (`wallpaper.json`).
- (D1) A JSON shape on a block that the generator stacks (crates) must stay inside its block, except for parts that
  lie inside the block above's own solid geometry (nail tips, straw on the rim under the next crate's walls).

- (B6) The first client session after a long gap shot the whole of Level 3 25-45 levels darker than every later one (the
  lights glowed, the rooms did not). Three spots retaken at once came out at the normal brightness, and a full reshoot
  was then pixel-identical to them. Always retake two or three spots before trusting a run, not only a baseline.
- (B6) A wall decoration is on one face of its wall only, the one toward its pier (West, East, North, South = 0..3 in
  the harness grid). A spot finder that faces any open side of the wall frames a bare wall.
- (B6) Overhead runs that repeat every block (cable trays) must read as a plain run from below: a ladder tray of rungs
  and tall rails made every ceiling a lattice at 3-6 blocks and was graded C. Give them a solid bottom.
- (B6) Versions of a wall drawn with `matlib.brick(tones=)` share one face and joint texture, so they mix without a
  patchwork. A unit that runs across the block edge keeps one shade in every version, or the version beside it cuts
  it in two. Shift every version by the same amount when matching the old mean (`gen_textures.match_rgb` with a key).

- (B7) `batch.py`'s header ended a Reality Shift and then set the clock, which can jump the calendar a day or a month
  past the next shift's start: two Level 4 runs came out 40-100 levels darker (a black fog beyond a few blocks). The
  header now ends the shift again after `/time stop`. A second "Reality Shift ended" in the run's chat log means one
  had started. Compare every run's mean brightness with the baseline before judging it.
- (B7) Texture `alternates` work on JSON-shaped blocks (decompiled `ShapeTesselatorManager`: `AltTexturesCount` feeds the
  JSON tesselation). A blocktype `textures` entry for one named key with alternates varies a decoration without layout
  (Level 4's posters). `drawtypeByType` lets one blocktype mix cube and JSON kinds without the `textures: { all: }`
  pitfall.
- (B7) Stepped geometry on a ceiling block (a diffuser of cones) reads as broken rings: its side faces take the light of
  the solid ceiling blocks beside it, so two sides go dark. Keep ceiling hardware shallow (one step) and put fine
  openings such as air slots in crisp pixels on a face plate. Cut-out foliage (a dead plant) reads as debris unless
  about half of each face is leaf, close round branches.

- (B8) Hardware copied onto all four sides of a block with no facing (`modelkit.turn`) must not reach the block's own
  side planes: a part flush with x 0 or 16 on the front becomes, on a buried side, a face exactly on the neighbouring
  wall's face, and it shimmers beside the door in the client. `check_zfight` lists these as "north-facing, on the north
  face of the block east"; stop such parts 0.05 short of the edge.
- (B8) A pattern on a floor that the blocktype turns at random must be four-fold symmetric about the block centre at the
  pixel: centre motifs on the half pixel (7.5, 23.5) with an even size. Odd-sized ones at whole pixels jump a pixel in a
  turned block, and the rows wobble.
- (B8) A spot found on the harness grid for a wall decoration can frame the wrong block (the pier convention): look at
  the first base frames of every new spot and re-spot before the after run. Dark rooms (boiler bays) get `-inspection`.

- (B9) Every level's prop textures share one folder (`textures/block/detail/`), so a new key can overwrite another level's
  texture without warning: B9's first `countertop` and `pegboard` replaced Level 4's, 974's and 3999's. Grep `tools/*.py`
  (and `git ls-files`) for a key before using it, and prefix new keys with the level (`snackcountertop`).
- (B9) Lettering drawn with `text()` (scaled-down antialiased type) smears on a sign under 10 px tall and does not survive
  any per-pixel treatment (chalk break-up turned EXIT and DEAD END into dots). Draw small lettering in a pixel face
  (`deep_textures.HEAD_FONT`, `CHALK_FONT`), and break up only strokes thicker than 2 px.
- (B9) Glass on a JSON prop is cut out, so it shows only by what is painted on it: long diagonal glints with a full UV
  read as rods in front of what is behind it. Use a few short glints and a lit edge row.
- (B9) A level whose look is one block row repeated up the wall (the Snackrooms' mint wall) cannot take a scuff band or a
  smudge in a texture: it prints on every row. That needs a different block for the lowest row, which is layout.
- (B9) Tripwires (and other props that span a passage) face along the passage: the passage runs along the pier's axis
  and the wire spans it, so a spot finder must stand along the pier axis. Check the first base frame of each new spot.

- (B10) A full after run came out 25-57 levels darker in every ordinary shot (a black fog beyond a few blocks). Its
  inspection shots were unchanged, and the chat log showed only the header's usual two "Reality Shift ended". A
  retake of three spots minutes later was normal, and so was the full reshoot. The darkness can hit any session, not
  only the first: compare every run's mean brightness with the baseline (`luma.py`) before anything else.
- (B10) Low-contrast structure that reads on a 4x texsheet flattens in the game: Voronoi facets a few levels apart with
  1 px joints looked like plain grain on a sea stack at 1.5 blocks under the inspection light. A faceted stone needs
  joints nearer the old texture's contrast (about 30 levels), spread so that no one joint leads the eye.
- (B10) When a model replaces a single box with panels, close every face the old box had. The wardrobe's carcass lost
  its back in round 1 and was graded D: from behind you could see straight into it.
- (B10) A broad sheen on a texture that is never turned wraps across block edges when it runs along (x + y) with
  period 32. An fbm sheen with 16 px cells read as vertical stripes.

## Batches

| Batch | Branch | Status | Rounds | Below B carried | Gate |
|---|---|---|---|---|---|
| B0 tooling and baseline | gfx/B0 | merged | 1 | | passed 2026-10-13 (Fable): tram/close/prop shots verified, no asset changes |
| B1 inventory | main | merged | 1 | | passed 2026-10-13 (Fable): L1 floor D confirmed on tent-close; boiler row corrected (generator exists) |
| B2 material kit | gfx/B2 | merged | 1 | concrete B-, basket weave, Berber, glass unverified | passed 2026-10-13 (Fable): models, ceiling, paper, carpet at B; B4 must push concrete (larger pour patches, more hue) |
| B3 Level 0 | gfx/B3 | merged | 3 | papers, carpet, Red Rooms (same/worse: user decides in decisions.md); troffer sides; gate concrete to B4 | passed 2026-10-13 23:30 (Fable): merged for per-family decision; round-2 troffer darkening was what the user played |
| B4 Level 1 | gfx/B4 | merged | 2 | steel door as model, floors/ceiling C+, pillar body, tent fly, emptied crate; cars/cameras/signs/first-aid untouched | passed 2026-10-14 02:00 (Fable): floor grid gone, walls formed; Level 1 baseline reshot (B0 one was brighter) |
| B5 Level 2 | gfx/B5 | merged | 2 | tunnel concrete/ceiling C+, door leaf painted, tram body C+; hazard panels, drums, trolley untouched | passed 2026-10-14 03:15 (Fable): gauges and tram verified as geometry on sidebyside |
| D1 follow-up on B3, B4, B5 decisions | gfx/D1 | merged | offline only (not shot) | | | passed 2026-10-14 13:20 (Fable): wallpaper and floor mocks seamless, box/crate previews checked; user approved in play |
| B6 Level 3 | gfx/B6 | merged | 2 | Purpified (C+), floor fan unseen, risers' painted roundness, OUT OF BOUNDS plaque unseen | passed 2026-10-14 15:40 (Fable): panels/fans verified as geometry, brick tone kept |
| B7 Level 4 (and Level 9's asphalt, after B11) | gfx/B7 | merged | 2 | ficus (C+), windows (C+), ghost-carpet patches (layout), elevator doors and small wall decor untouched; Level 11's asphalt-cracked square (B12) | passed 2026-10-14 17:45 (Fable): furniture verified as geometry, surfaces kept tone, asphalt fine and even |
| B8 Level 5 | gfx/B8 | merged | 2 | boiler bay C (B6's boiler: clay-orange shell, box flue; fix in a follow-up), red marble pillars repeat, furniture untouched | passed 2026-10-14 19:35 (Fable): doors and chandelier verified as geometry, damask tone kept |
| B9 Levels 6 and 6.1 | gfx/B9 | merged | 2 | mall wall C+ (row repeat is layout), shop windows C and skylights C+ (lights stay cubes), L6 wet floor C+ | passed 2026-10-14 21:30 (Fable): shelves, counters and kitchen verified as geometry; chalk lettering restored |
| B10 Levels 7 and 8 | gfx/B10 | merged | 2 | island rock C+ (facets need ~30 levels of joint contrast: follow-up), sea ceiling C+, glowcaps C+, wing chair fabric, seeps untouched | passed 2026-10-14 23:40 (Fable): repeat gone, furniture and lamps at B; user decides |
| B11 Levels 9 and 10 | gfx/B11 | merged | 2 | silo, tractor, asphalt tracks, house interiors, L10 field props (budget) | passed 2026-10-14 01:00 (Fable): gables and roofs verified on sidebyside; new pitchroof code beside roofslope, layout hashes unchanged |
| B12 Level 11 | gfx/B12 | in progress | | | |
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

### B1

Worker report (Opus, 2026-10-13). Nothing under `assets/`, `tools/` or `src/` changed, and nothing was built, generated
or run. Scratch notes and the hero contact sheets are in `review/b1/`.

**What was graded.** I graded every level sheet and its individual shots: 22 levels, including the `-inspection`
shots for Levels 6 and 7. I also graded the texsheets for every block folder, the textured prop previews, the 41
gallery shots, the "What lives here" lineup (hero 42), and the item and entity texsheets. Four read-only subagents
mapped each texture and shape to its generator function. The result is 180 asset families across B3 to B17, plus a
few cross-reference rows.

**Counts.**

| A | B | C | D | not seen |
|---|---|---|---|---|
| 0 | 29 | 113 | 17 | 21 |

- Hero rows: 16 B, 63 C, 8 D.
- The D rows are painted-on 3D (gauges, grilles, door hardware, the tram) and single features stamped once per
  texture: Level 1 floor scuffs, stained carpet, Level 7 rock, Level 94 turf, 3999 marble.

**File.** `docs/design/graphics-pass/inventory.md`. It is a copy of `review/inventory.md`, written now rather than
after Gate 1 as the batch prompt asked. The file ends with:
- the counts per batch;
- the ten highest-priority rows;
- ten things that cut across batches, for B2. These are a hue-aware noise to replace grey `noise_fill`, a set of
  shared surface primitives, one ceiling module, hardware and furniture kits, a tiling rule against features stamped
  once per texture, and the lit-from-above shading convention.

**Spots to fix before shooting.** Some baseline frames are black or useless:
- Level 1: close-wall, close-wall2, close-ceiling.
- Level 3: close-floor, den-*, pipeend-close.
- Level 6.1: gate-*, threshold-*, sleepingbag-*.
- Level 7: gate-*, tent-close, close-water.
- Level 11: refuge-*.
- Level !: wide-07, prop-1, prop-2.

Some levels need more shots:
- Level 9 has no day shot of a house. It needs two or three day spots on a street.
- Level 974's wide shots all show the same plan. It needs the kitchen, the bathroom and Kitty's room.

21 families appear in no shot. Each of their rows names a spot to add.

### B2

Worker report (Opus, 2026-10-13). Branch `gfx/B2`, uncommitted. Nothing under `assets/` changed. No generator was
edited; `gen_models.py` (the one generator importing a changed module, `rig.py`) was re-run and wrote byte-identical
files. Nothing was built, shot or run in the harness; this batch has no compare sheet and no blind round.

**Built**
- `tools/matlib.py` (new; `texlib.py` untouched). Pure Python and Pillow, deterministic from a seed (two full runs give
  identical bytes), sizes checked against the 8 px grid, every field periodic so everything tiles.
  - Base: `noise_hv` (soft periodic mottle + 3-6 level grain + slow hue wander; the replacement for `noise_fill`),
    `lift`/`shade_px` (warm light, cool shadow, drift 0.18 per level, capped at 6 levels), `value_noise`, `fbm`,
    `worley`, `points`, `roll`.
  - Surfaces: `concrete` (fines and aggregate lit on top, pores, `cracks`, form-board `joints`, trowel `swirl`, slab
    `border`), `plaster`, `paper` (fibres, strip seams with a lifted edge, per-strip hue), `painted_metal` (panel
    bevel and seam, edge chips or worn spots, screws), `brushed_metal`, `galvanised` (spangle facets), `riveted_plate`
    (edge rows or a vanilla-style grid, rust at the seams), `wood_planks` (per-board hue, streaks, flecks, grain lines
    bending round knots, lit top edge, dark gap, optional butt joints, upright option), `fabric` (plain, twill, basket,
    ripstop), `carpet` (tufts with a nap direction, two-tone, Berber loop, a `dye`d pattern, wear lanes), `tile`
    (per-tile shade, hue and tilt, bevel, glaze highlight, recessed grout, mosaic palette, running bond, crazing,
    speckle), `glass`, `rubber` (studs, ribs, diamond), `asphalt`, `brick` (per-unit hue and shade, lit top, shadowed
    bed joint, any stagger, chamfered block option; the `detail_textures.block_wall` idea as a primitive), `crack`,
    `screw`.
  - Operations: `ao_border`, `bevel`, `inset`, `hue_jitter` (field or per box), `grime` (with a bottom/top bias),
    `scratches`, `drips`, `rust`, `chip_edges`, `emboss_lines` (groove or rib), `stain` (seed or `at` offset, wraps,
    tide ring), `tideline`, `multiply`, `dye`, `spread`, `alternates(fn, seed, n)`.
  - Ceiling module: `tbar` (2 px rail split across neighbouring blocks, lit half at top/left), `ceiling_tile`
    (fissures, pin-holes, soft tegular recess, optional stain kept inside the tile), `troffer_lens` (bevelled frame,
    prism-cell lens, tube bands; on, dim and off by `lit`, any colour for the Red Rooms). Textures only; the T-bar
    shape is B3's call.
  - The module docstring gives a level batch the shading convention, the tiling rule (a feature in about one block in
    three, at a different offset each time, via `alternates` beside plain variants) and the grid rule.
- `tools/modelkit.py` (new; `detail_kit.py` and `gen_shapes.py` untouched). Elements in `detail_kit.bx`'s format (the
  superset of `gen_shapes.box`: the same dicts, UV from size, plus rotation), so they go straight into
  `detail_kit.shape`/`prop` or `gen_shapes.save`. Every face takes its key from a role spec (`top`, `side`, `front`,
  `back`, `bottom`) and the composites default to separate top/side/front keys, against the `textures: { all: }`
  pitfall. Helpers: `bevelled_box` (three crossed boxes, every edge stepped 1 px), `frame_members`, `inset_panel`
  (a grid of recessed panels), `frame_and_panel` (door leaf, fielded panels on both sides), `inset_window`, `handle`,
  `lever`, `knob`, `hinge`, `push_bar`, `kick_plate` (with screws), `grille` (upright, level or grid bars on a dark
  backing), `dial` (octagonal bezel, set-back face, needle at an angle, hub, optional glass) and `gauge` (bevelled
  body, stem), `keypad`, `leg` (foot, taper), `rim`; furniture: `chair` (panel, slats or stool), `table` (top, lip,
  apron, legs), `cabinet` (plinth, drawers, inset doors, handles, overhanging top), `door` (casing, panelled leaf,
  hinges, lever or push bar, kick plate, window). `turn` carries rotations and origins round (`detail_kit.turn` does
  not); `move`; `textures`.
- `tools/rig.py`: new `shade_fill(ctx, base, ...)`: vertical light on side faces, a 1 px lit top edge, a dark foot,
  AO at part borders weighted to the foot, a soft mottle, warm/cool drift. `fill` is unchanged; gen_models can opt in.
- `tools/preview_shapes.py`: faces now go through a per-pixel depth test instead of a mean-depth sort, which hid thin
  plates in front of big faces (a kick plate vanished behind its door). `--flat` still works.
- `tools/matlib_sheets.py` (new): makes every sheet below, prints a seam score per sample (the wrap edge's step over
  the strongest inner line; 1 or under is seamless), builds the model JSON and renders it with real sample textures.
  A later batch can add its own parameterisations to `FAMILIES`.
- `docs/DEVELOPING.md`: three lines for the new tools, and the depth test in the preview line.

**Inventory "Things that cut across batches"**
- Covered: 1 (hue-aware `noise_hv`; `noise_fill` left alone); 2 (every listed primitive, plus brick/block); 3 (the
  ceiling module, as textures); 4 (dial/gauge, grille, handle, kick_plate, inset_window, push_bar, keypad,
  inset_panel, frame_and_panel, plus knob, lever, hinge, rim, leg, bevelled_box); 5 (chair and table, plus cabinet
  and door); 6 (the tiling rule in the docstring, `stain`/`crack` take offsets, `alternates`, and the defaults for
  knots, joints and cracks are 0); 7 (the shading convention baked into the primitives and `bevel`/`inset`/
  `ao_border`; `rig.shade_fill` for entities).
- Not covered: the T-bar as geometry (B3 decides texture or shape); a one-call desk with drawers (`cabinet` with
  `drawers` beside `table` covers it); 8 (shared textures to change with care) and 9 (orphans) are level-batch work;
  10 (`preview_shapes` still ignores face rotation).

**Sheets** (`review/b2/`, indexed in `review/b2/README.md`): `<family>.png` and `<family>-tile.png` for noise,
concrete, plaster, paper, painted_metal, brushed_metal, galvanised, riveted_plate, wood_planks, fabric, carpet, tile,
glass, rubber, asphalt, brick, ceiling and alternates; `ops.png`; `models.png` (13 models; `check_zfight.py --root
review/b2/shapes` finds 0 candidates); `entity-shading.png`; `run.log` (seam scores: every surface 1.15 or under
except the panel, rivet and T-bar textures, whose seam sits on the edge by design, and two ops demos that are not
meant to tile).

**Self-review against the rubric** (my own reading; Gate 2 judges)
- B or better beside vanilla: `wood_planks` (oak reads close to vanilla oak, a little softer in contrast), `brick`
  (red running bond, the white block), `tile` (glazed and mosaic), `fabric` plain and twill (beside vanilla linen),
  `galvanised`, `riveted_plate` grid, `painted_metal` panels, `ceiling_tile` and `troffer_lens` (lit rail, recess,
  prism grid; far above today's flat square), `carpet` cut pile (tan, red patterned), and the model helpers (bevels,
  insets, hardware, dials and grilles all read as geometry in `models.png`).
- About B-: `concrete` (structured now, but the aggregate is still a little regular and it has less colour than
  vanilla andesite), `plaster` (right, but plain by nature), `paper` (seams and fibre read; the print is the
  caller's), `asphalt`, `brushed_metal`, `rubber`.
- Short of B: `fabric` basket (burlap) is a flat checker beside vanilla burlap's coarse threads; the grey Berber
  `carpet` is busy; `glass` is more visible than vanilla's near-invisible pane (default alpha lowered to 72; judge it
  in game); `rig.shade_fill` is a first version for B17 to tune (its AO rims show on large faces). The large mottle
  (16 px cells) repeats once per block: low in contrast, but it would show on a big uniform floor without rotation
  alternates.

**Lessons**
- A feature drawn into every texture of a surface (a crack, a knot, a butt joint, a stain) shows as a grid on `--tile`
  even when placed at random within the block: put it in about one alternate in three, beside plain variants.
  matlib's defaults for such features are 0 for that reason.
- An unclamped warm/cool drift turns deep shadows (cracks, gaps) blue; cap it (matlib caps it at 6 levels).
- Wear painted along a texture's edges (chips) lands mid-face on model parts, whose faces show the texture from its
  corner; for model textures scatter the wear instead (`painted_metal(panel=False)` does).
- `preview_shapes.py` sorted faces by mean depth until B2 and could hide thin parts; previews made before B2
  (`review/baseline/props/`) may be missing plates and hardware.
- The heredoc problem above also breaks Python edit scripts with nested quotes passed through the Bash tool; write
  such scripts to a file with the Write tool and run the file.

### B3

Worker report (Opus, 2026-10-13/14). Branch `gfx/B3` from `main`, uncommitted. Three rounds. Final sheet:
`review/b3/compare-round3.jpg` (after shots in `review/b3/final/`).
- **Per-family pairs** for the user's choice: `review/b3/sidebyside/<family>.jpg`, indexed in `review/compare.html`.
- **Decision table:** `docs/design/graphics-pass/decisions.md`, with the decision column left empty.

**Checks**
- Build: 0 warnings.
- `layouthash` is unchanged: v1 `18cfdbc1c530f039`, v4 `ca047189969b69db` (`review/b3/layouthash-*`).
- `validatelevel 0`: 0 unreachable, 0 doorways to nowhere.
- No C# changed. Nothing under `assets/game/` changed, and no block, item or entity code changed.
- The final shots match the baseline in brightness (mean luma per shot within 1-4 levels).

**Rounds**
1. The reviewer graded ceiling, T-bar and trims B. It graded D for the stained carpet (a uniform tint showed hard block squares) and C for most else. It also found:
   - a bright bar along one edge of the troffers;
   - a supply box that read as a box with an offset lid;
   - a chevron that did not carry past 3 blocks;
   - manila paper that read as panelling.
2. After the fixes, every shot came out 3-5x darker. The cause was the recessed-troffer JSON shape. Its faces lost the cube's glow, even after adding face `glow` through `shapeByType`, and the rooms went dark in the review world. The player who tried this build reported "not an improvement", which was largely this. The troffer went back to a cube.
3. Final round, on the coordinator's brief: where the reviewer judged a change same or worse, revert toward the original look and keep only the structural gains. The stained carpet went back to the original wrapped blotches, the T-bar is darker so the grid reads as before, and the paper mottle is calmer. The final blind review (at playing distance) found brightness matching and graded the families below.

**Per family: what changed, final grade, and how it compares to before at playing distance**
- **Chevron wallpaper** (`gen_textures.paper_wall`, `motif_chevron`): C+, same.
  - Changes: `matlib.paper` (fibre, faint strip seams every 16 px), the motif dyed in, the chevron printed darker (`CHEVRON_PRINT`), the beads at half strength.
  - Every part has base, `-2` and `-damp` versions (`wallpaper.json`, `paperjoin.json`). The damp stain stays inside the block.
  - Lore colours are kept; only the print is stronger.
- **Other papers:**
  - Pale arch paper: C+, same.
  - Manila: C, same. It now has a 4 px dot; the old 5 px dot did not tile.
  - Stripped: drywall with paste bands, scraps in one version of three.
  - Dotted: same build. Dotted only generates in layout v1-3 and stripped only by players, so neither is in any shot.
- **Baseboard and chair rail:** B-, same. A lit cap, a dark toe and a scuff band above.
- **Outlet:** B-, better (smaller, bevelled, with a shadow). Still painted; see Carried.
- **Carpet:** C, same. `matlib.carpet` Berber loop pile with the colour kept, two seeds matched in brightness, four turns each (`carpet.json` now lists 8).
- **Stained carpet:** C+, same. The original wrapped blotches on the new pile. Soaked and threadbare were reworked; the old threadbare used a 3 px grid that did not tile.
- **Ceiling tile and T-bar:** B, better. `matlib.ceiling_tile` (fissures, tegular recess, a 2 px split rail darker than the tile). Two stained tiles, each about one block in ten. A new `ceilingtile-side` for the faces seen where the ceiling layer ends.
- **Troffers:** B- from below, better.
  - A bevelled frame, a prismatic lens pulled toward its glow colour, and a painted dark gap round it.
  - Still a cube. The recessed-lens shape (`gen_l0_walls.troffer`) is kept in the code but not written.
- **Red Rooms paper:** C, worse past 3 blocks, because the paper lost its bright dashes. The red lights are the same.
- **Arch header:** C, slightly better. The soffit and risers have their own `cream-soffit` key (plain plaster instead of printed paper).
- **Supply box:** B-, same.
  - The shared cardboard got fibre, tape with a sheen and this-way-up arrows.
  - The box has its own worn-edge faces (`supplybox-box-*`).
  - `shapes/block/supplybox.json` is now written by `gen_loop.supply_box_shape`, as one box.
- **Torn box:** B, better, the clearest gain. The torn rim is geometry teeth, the inside is lighter, and the straw, wrapper and paper wad are boxes.
- **Concrete:** C, same. See Carried.
- **Shared by other generators:** `matlib.paper` has a new `seam` option (default 1.0, so B2's output is unchanged). The `item/salvage/wallpaperstrip.png` sprite follows the new paper.

**Carried below B, with reasons**
- **Chevron wallpaper, papers, carpet (C/C+, same):** the blind reviews and the player both found the big surfaces no better at playing distance. The user chooses per family in `decisions.md`.
  - Ideas the reviewer left: drop the pale vertical streaks on the paper; a faint 2-4 texel carpet structure; a lighter second element on the Red Rooms paper.
- **Troffer side faces:** where a light's side shows (gate-wide), the framed panel reads as a window. This needs a side texture like `ceilingtile-side`. That is a blocktype `north`/`east`/`south`/`west` override on `fluorescentlight`, and the flicker block entity tesselates the off block, so I left it to the next pass.
- **Outlet as geometry:** the wall block would have to become a JSON shape (different lighting and culling on every outlet wall), and a real plate is about a tenth of a pixel proud. Kept painted.
- **Gate concrete:** the gate wall is Level 1's `concretewall` (B4's `gen_textures.concrete_wall`), not the `concrete` block the inventory named. It is carried to B4.
- **Manila Room furnishing:**
  - The floor is vanilla `game:planks-aged-ud`.
  - The table (`gen_detail.py:level4`) is shared with B7.
  - The chandelier (`gen_shapes.py:level5`) is shared with B8, as the inventory row says.
- **Small items the final reviewer named:** arch soffit edge shading, the flap seam on the closed box's top, and the dark gap round the troffer lens (near-black).
- **Not seen in any shot:** dotted paper and stripped walls.
- **New spots:** `arch-wide` and `arch-close` are added to `spots/0.json`. Their befores are in `review/baseline/0/`, shot on a build of unchanged `main`.

**Lessons**
- A JSON shape on a light block loses the cube's `vertexFlags` glow. Face `glow` through `shapeByType` did not bring it back in the shots, and the review world's rooms went dark around the lights. Keep emissive fixtures as cubes, or check the light level in a shot (mean luma against the baseline) before judging anything else.
- Check every shot's mean brightness against the baseline before a review. A lighting regression makes every texture look worse, and a reviewer cannot separate the two.
- Stained floor blocks laid in patches have no good per-block answer. A tint shows the patch as hard squares, stains faded at the block edges show a grid of spots, and one blotch per texture is the original's look. A soft outline needs edge-aware blocks (layout), not textures.
- A motif dyed onto structured paper loses contrast against the fibre and seams. Print it darker than the old flat pixel colour, and keep seams and mottle faint on large walls, or the paper reads as stripes or panelling.
- Judge big surfaces at playing distance (2-6 blocks in the wide shots), not on 4x texsheets. Detail that reads on a sheet averages away in game, while low-frequency mottle and seams show more than expected.
- `tools/shotbot/sidebyside.py` with `docs/design/graphics-pass/sidebyside/<batch>.json` makes the per-family before|after pairs and appends the batch to `review/compare.html`. Later batches should add their map and their rows to `decisions.md`.
- A single 2-spot client run can shoot its first spot before the area's light or chunks have loaded (dark or fallen camera). Shoot new spots as part of the full list, or retake.

### B4

Worker report (Opus, 2026-10-14). Branch `gfx/B4` from `main`, uncommitted. Two rounds: one blind review, then a fix and a reshoot. Final sheet:
`review/b4/compare-round2.jpg`, with the after shots in `review/b4/final/`. The round-1 sheet is `review/b4/compare-round1.jpg`.
- **Per-family pairs:** `review/b4/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B4.json`. The B4 section is added to `review/compare.html`.
- **Decision table:** eleven rows added to `decisions.md`, decision column empty.

**Checks**
- Build: 0 warnings.
- `layouthash` is unchanged: v1 and v4 match B11's output line for line (`review/b4/layouthash-v*.txt`).
- `validatelevel 1`: Level 1 has 0 unreachable tiles and 0 doorways to nowhere (`review/b4/validate1.txt`).
- No C#, no `assets/game/`, and no block, item or entity code, variant group or class changed. New texture files sit beside the old ones, and the alternates are listed in the hand-written `blocktypes/level1/concrete{floor,wall,ceiling}.json`.
- Brightness: every final shot is within 0.6 levels of the refreshed baseline (`review/b4/luma-final.txt`).

**Baseline refreshed (read this before comparing anything with `review/baseline/1`)**
- The B0 baseline of Level 1 was 8-15 levels brighter than a build of unchanged `main` shoots today, in the rooms and the car park: den, tent, refuge, gate, threshold and prop-1.
- Shot again on unchanged `main` (`review/b4/base-check`), those spots matched B4's after shots within 0.6 levels. So the change was in the baseline, not in this batch.
- `review/baseline/1` is now the whole list reshot on `build-gfxbase` (unchanged `main`, built at the start of this batch). The B0 set is kept in `review/baseline/1-b0`.
- Other levels' baselines may have drifted the same way.

**Spots**
- Re-spotted: `close-wall` (white block, in a lit hall), `close-wall2` (concrete, the car park's fire wall) and `close-ceiling` (car park slab, under the lights).
  - The old spots were inside the unlit room round Level 1's arrival point; the B0 shots are in `review/b4/old-black/`.
- Added: `park-wide` and `firewall-wide`: the floor, the concrete wall and the ceiling at playing distance.
- These changes are in `review/spots/1.json` and `docs/design/graphics-pass/spots/1.json`.

**What changed, per family** (round-2 grades are mine; the round-1 blind grade is given where it differs)

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Car park floor (plain, wet, dark) | C+ (blind r1: C) | better | `matlib.concrete` with pour patches, three versions per kind, all turned. The crack and tyre scuff are in one plain version only, so the old grid of tyre-band crosses is gone. Hue pulled back to grey in round 2. Wet keeps its glints: round 1's smoothed water film read as flat squares. |
| Floor markings | B- | same (r1: D, worse) | Round 1's worn paint broke every dash at the block seams. The lines are clean now and take the concrete's tone. The drain is a recessed frame with shaded bars. |
| Painted hall floor | C+ (r1: C) | better | The six scuffs that sat in the same place in every block are gone. Three plain versions, all turned; scuffs are in one version only. No aggregate (it is painted). |
| Concrete walls | B- | better | Formed concrete with bug holes, a pour line and two tie holes per block. Three versions; the third has a crack and a rust run. |
| Damaged wall | B- | better | Spalled round the modelled rebar; no painted rebar. |
| Car park ceiling | C+ (r1: C, worse) | same | Round 1 dropped the painted conduits and the blind reviewer read that as lost structure. Round 2 brings them back, shaded as round runs with clips and a shadow. Three versions. |
| Pillars, letters, base, wheel stops | C+ / B- | same (r1: letters and base worse) | Smoother column concrete with lit and shaded arrises. Round 2 made the letter panel clean and wears the hazard band only at its foot. |
| Camp tent | C+ | slightly better (r1: same) | Ripstop fly with soft unevenness and stronger seams. Gable ends stepped 1 px at a time, not 16 steps. Woven poly groundsheet with folds, a little duller. |
| Sleeping bag, lining, bedroll | B- | better | Puffed 8 px channels with soft seams (the old 6 px did not tile), flannel tartan lining, rolled canvas bedroll, woven pillow. |
| Burn barrel | B- | same | Painted metal gone to rust (heaviest at the foot), runs from the rim, soot at the top. Geometry unchanged. |
| Crates (closed, emptied) | B- (emptied C+) | better | Grained boards in a raised, shaded frame, a brace sampled along its grain (round 1's brace broke up), nails. Still a cube, as vanilla's crate is. |
| EXIT signs | B | same | The face is lit from behind with a pink halo round the letters; the housing is enamelled steel. |
| Steel door | C (push bar still painted) | better | Shaded frame, raised push bar, kick plate and window bead. |

**Carried below B, with reasons**
- **Steel door as geometry (D to C):**
  - `metaldoor` has no facing variant, so a modelled door could not be turned to its wall.
  - It would need a new code with an `axis` group beside the old one, placed by the generator, and a fresh review world.
- **Car park floor, hall floor, ceiling (C+):** the per-block limit of B3's lesson on floors.
  - Saw-cut joints every few blocks, tyre-wear lanes and oil trails are layout-scale features.
  - A texture can only add them in every block or at random.
- **Pillar body (C+):** plain concrete that is mostly behind the letter and the band. It is noise-quiet now, but has no structure of its own.
- **Tent (C+):** still reads as a toy from 2 blocks, because the fly is a single flat slope. The next step is a sagging fly (two or three facets per side) and a smooth gable. That is a reshape of the 2x2 model, so it was left for budget.
- **Emptied crate (C+):** the straw and the missing plank are still painted. A modelled version needs a JSON shape on a block that is placed in stacks.
- **Not touched, for budget:**
  - cars and wrecks (already B)
  - cameras and traffic signs (in no shot)
  - first-aid rooms (in no shot)
  - metal shelving
  - wall decorations (breaker, hose cabinet, alarm)
  - pay station, cones
  - camp lantern, folding table and chair, workbench, toolbox
  - white block wall (B)
- **Shared assets that changed:**
  - `concretewall-plain` also shows behind Level 0's gates, in The End, in Level ! (its fallback) and in 188's Level 1 window.
  - `concretefloor-plain` is `FloorKind.Concrete` everywhere, and Level 9's `housefloor-garage` is drawn from it.
  - The camp kit textures appear in Levels 0, 3, 4, 7 and 8.
  - None of these levels was reshot.

**Lessons**
- Before trusting a level's baseline, retake two or three of its spots on a fresh build of unchanged `main` and compare mean brightness. Level 1's B0 baseline had drifted 8-15 levels brighter than today's client shoots the same build, which would have read as a lighting regression in this batch. Reshoot the level's baseline if it has drifted.
- Painted lines that run across tiling blocks (road markings, stripes) must be clean at the seams. Any wear on them shows as a break at every block edge at playing distance.
- Taking out a repeated painted feature, even a "painted 3D" one the inventory names (the ceiling conduits), reads to a blind reviewer as lost structure. Keep the structure and shade it, and leave the removal to the user's decision.
- On grey concrete, keep `matlib.concrete`'s `patch_hue` and `hue` at 1.5 or less, and aggregate at about 0.03 or less. More turns into teal and olive blotches and a coloured speckle at 2 blocks.
- Wood sampled for a diagonal part (a brace) must follow the board's length (x), not the diagonal. Otherwise the grain streaks alternate and the brace reads as a rope.
- Level 1's arrival point is inside an unlit room. When re-spotting with `mkspots.Grid`, count only `LightOn` ceiling tiles (kind 1) near the spot; `LightLit` glows but does not light the walls.

### B11

Worker report (Opus, 2026-10-14). Branch `gfx/B11` from `main`, uncommitted. Two rounds. Final sheets:
`review/b11/compare-9-round2.jpg` and `review/b11/compare-10-round2.jpg` (every spot), with the new day and farm spots in
`review/b11/compare-9-day-round2.jpg` and `review/b11/compare-10-farm-round2.jpg`. After shots are in `review/b11/final/<level>/`.
- **Per-family pairs:** `review/b11/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B11.json`. The B11 section is added to `review/compare.html`.
- **Decision table:** nine rows added to `decisions.md`, decision column empty.
- **Playtest:** both Level 9 rows point at `sidebyside/gables.jpg` and `sidebyside/roofs.jpg`.

**Checks**
- Build: 0 warnings.
- `layouthash` is unchanged: v1 and v4 match B3's final output line for line (`review/b11/layouthash-v*.txt`). No `WorldLayout*` or `Tiles.cs` file changed.
- `validatelevel 9` and `validatelevel 10`: 0 doorways to nowhere, 0 blocked (`review/b11/validate*.txt`).
- Nothing under `assets/game/` changed. No code, variant group or class was renamed or removed.
- Brightness: every final shot is within 4.3 levels of its baseline, except `day-eave` (-16). That spot looks up at the eave, and the eave now has an overhang with a soffit in shade where there was sky and wall before. Its lighting is unchanged (`review/b11/luma-final.txt`).

**New spots** (added to `review/spots/` and `docs/design/graphics-pass/spots/`; their befores were shot on a fresh build of unchanged `main` into `review/baseline/9` and `/10`)
- Level 9, at day (`pre: /time set 12:00, daylight`):
  - `day-street`
  - `day-front`
  - `day-gable`: close on a gable.
  - `day-eave`: the eave from below.
  - `day-porch`
- Level 10:
  - `barn-wide`, `barn-close`, `barn-roof`: a farmstead about 500 blocks east of the anchor, the nearest one with a red barn.
  - `silo-close`
  - `tractor`
  - `shed-wide`, `shed-close`: the field shed nearest the anchor.
- `batch.py` now records daylight from a spot's `pre`, so the next spot turns it off again. Before, only inspection spots did.

**What changed, per family**

*Gable ends* (playtest note 1). Final grade B; much better. The blind reviewer said yes, they match the walls.
- A new block, `pitchroof-<cover>-<gable>-<form>-<side>`, sits beside `roofslope`. Its `gable` group is the wall's siding (white, blue, yellow, green, brick, barnred, barngrey) or `none`. `allowedVariants` limits it to 21 cover-and-gable pairs.
- Over a gable wall, the roof block fills down to the wall with that siding in 2 px steps. The texture is laid on the wall's own grid (east u = 16 - z, west u = z, v = 16 - y), so boards and bricks run on unbroken. A white rake board runs along the edge.
- `WorldGenerator.Deep.cs` `RoofAt` and the new `PitchRoof` place it at the same positions where `roofslope` went. This is block choice only, with no layout version.
- The gable over a barn's or shed's doorway now closes with the barn's boards. Before, it was air from the top of the door to the roof: the "hayloft hole" in the stepped gable.

*Roofs* (playtest note 2). Final grade B; better. The reviewer: they read as pitched, shingled roofs with an eave.
- Shingles are courses of geometry: four to the block. Each course is pitched slightly flatter than the roof, so its butt stands 0.3 above the course below.
- There is a thin deck under the courses, and its underside is the soffit. Porch ceilings show it.
- `PitchRoof` picks the form from the neighbouring tiles:
  - *Eave*: the lowest row, when no lower roof leans on the wall. It has an overhang, a fascia, a boxed light soffit and a gutter.
  - *Peak*: two rows meeting at the ridge. Each carries half the cap.
  - *Ridge*: a ridge row of its own where both neighbours are half a block lower. It used to end in a half-block step.
- Collision is unchanged: half a block for a lower block, a full block for an upper one.
- Textures: `deep_textures.shingle_courses` (laminated tabs, three versions per colour), `roof_edge`, `ridge_cap`, `soffit` (light, vented) and `gutter`.
- The old `roofslope` block gets the same courses over its old fill, now in fine steps. Its gable fill in saved chunks stays trim-coloured, because that block has no siding variant.

*House siding*: B, slightly better.
- `lap_siding`: eight boards of 4 px to the block, a shadow under each butt, per-board shade.
- The old 5 px boards left a 2 px board at every block edge.
- Three versions per colour, used by walls, corners and gables alike. Colours are kept.
- Paint chips in the third version read as a grid of dots in round 1, so they were removed.

*Smaller families*

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Porch posts | B | better | Plinth, shaft and a stepped capital (`porch_post`). |
| Front door | B | better | Raised panels in an inset frame, casing, a brass knob, set-back glazing. The house number is gone (every house showed the same one). |
| Garage door | B- | better | Inset and bevelled panels. |
| Mailbox | B | better | Rounded top, door, latch and a flag on a pivot as geometry. |
| Asphalt | C+ | slightly better | One `matlib.asphalt` base for the road and all its markings (it was painted twice). Calmer speckle. A sealed crack and a patch as alternates among the turns. |
| Pavement | B | same | Concrete slabs with tooled joints. |
| Barn and shed boards | B- | better | Board and batten, uneven boards, three versions, a duller red. |
| Barn roof | B- | better | Corrugated tin courses with a galvanised ridge and a rough-board underside. One version in three has rust. |
| Silo | C | slightly better | Corrugated galvanised texture. The old 3 px ribs did not tile. |
| Tractor | C+ | better | Rounded wheels with hubs, a duller green. |

**Rounds**
1. **Round 1** found:
   - Tractor and silo at C.
   - Asphalt same.
   - The soffit read as more siding.
   - A ridge-cap stub at the apex.
   - Chip dots repeating on the siding.
   - Barn red too saturated.
   - The barn roof was not in any shot.

   No lighting change was found.
2. **Round 2** fixed:
   - A light vented soffit.
   - A lower cap.
   - No chips on the siding.
   - Warmer grey shingles.
   - Duller barn red and uneven boards.
   - Deeper garage panels.
   - Asphalt alternates.
   - A painted-steel tractor green.
   - A new `barn-roof` spot.

   The round-2 grades above are mine. Per the brief, there was no second blind review.

**Carried below B, with reasons**
- **Silo (C):** the footprint is layout. It is a ring of full cube blocks, so it stays square-ish.
- **Tractor (C+):** it still needs a modelled hood, grille and treads.
- **Asphalt (C+):** a flat road surface has no good per-block answer for wheel tracks. The blocks are turned at random (B3's lesson on floors).
- **Rake edge:** the course ends show as a fine sawtooth above the rake board. A taller rake would stand proud of the neighbouring block's roof.
- **Not touched, for budget:**
  - House interiors: wallpapers, the painted dresser, TV and cabinets, the ceiling light.
  - Windows (already B) and the coach lamp (kept; visible in `day-porch`).
  - Street signs (already B).
  - Yard props.
  - Level 10's trough, pump, gates, hay and the field textures.
- **Saved worlds:** chunks generated before this batch keep `roofslope`, now with the new courses but their old trim-coloured gable fill. A house that straddles old and new chunks shows both.
- **Shared with other batches:** Level 94's houses and The End use `Level9Block`, so they get the new roofs and gables too. `gen_city.py`'s `barnwall-noclip` derives from `barnwall-red` and follows it. Level 11's road markings (`asphalt-doublens`, `-bayns` and others) derive from `asphalt.png`, so the city's roads change too: about 5 levels lighter. Level 11 was not reshot; that is B12's to judge.
- **Small engine-side change:** `Breakdown.cs` lists `pitchroof` with the timber blocks beside `roofslope`.

**Lessons**
- A change to which block the world generator places does not show in a review world whose chunks already exist; they keep the old blocks. Shoot such a batch in a fresh world. This batch used `--world gfxb11`, made by `batch.py` at the same seed, and its baselines came from `gfxreview`.
- Roofing as tilted course boxes: from the street you look up the slope at a grazing angle, so the courses' butt faces take up nearly half the roof. Keep them thin (0.3) and in a shingle tone, not a dark edge colour, or the roof goes dark (round 1's test shot).
- A gable fill that must match the wall needs world-aligned UVs on the step faces (east u = 16 - z, west u = z, v = 16 - y). `preview_shapes.auto_uv` documents the same convention.
- `tools/shotbot/compare.py --only` takes exact names, not patterns. `sidebyside.py` reads one folder each side, so a two-level batch copies its shots into prefixed folders first (`review/b11/sbs/`).
- The client now writes 3840x2160 shots, while older baselines are 1920x1080. `compare.py` and `sidebyside.py` scale them, but compare brightness on resized copies.

### B5

Worker report (Opus, 2026-10-14). Branch `gfx/B5` from `main`, uncommitted. Two rounds: one blind review (round 1), then a fix and a reshoot. The round-2 grades are mine.

- **Final sheets:** `review/b5/compare-round2.jpg` (every spot) and `review/b5/compare-round2-detail.jpg` (18 key spots at twice the size). After shots are in `review/b5/final/`. Round 1 is in `review/b5/compare-round1*.jpg`.
- **Per-family pairs:** `review/b5/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B5.json`. The B5 section is added to `review/compare.html`.
- **Decision table:** seven rows added to `decisions.md`, decision column empty.
- **Texsheets and model previews:** `review/b5/texsheets/`.

**Checks**
- Build: 0 warnings.
- `layouthash`: v1 and v4 match B4's output line for line (`review/b5/layouthash-v*.txt`).
- `validatelevel 2`: 0 unreachable, 0 doorways to nowhere, 0 blocked (`review/b5/validate2.txt`).
- No C# changed. Nothing under `assets/game/` changed. No block, item or entity code, variant group or class was renamed or removed, and no generator-placed block changed. The doors keep their codes and switch from `drawtype: cube` to `json`, so the batch was shot in `gfxreview`.
- `check_zfight` is clean on every new shape. The one hit left, `deadtram-front` Cab/Roof south faces, was already there.
- Brightness: every final shot is within 1.7 levels of the new baseline (`review/b5/luma-final.txt`).

**Baseline and spots**
- `review/baseline/2` was reshot on `build-gfxbase` (unchanged `main`) at the start. The B0 set is kept in `review/baseline/2-b0`. It differed by 2-6 levels, mostly from B4's shared floor (`review/b5/drift-b0-vs-main.jpg`).
- Six spots were added to `spots/2.json`, found lit with the harness `shotgrid`:
  - `machinery-close` and `machinery-wide` (the hero 07 view)
  - `cabinet-close`
  - `door-close`
  - `brick-close`
  - `tram-inspection`: daylight and lantern. The tram stands in an unlit stretch, so this shot judges the model only.

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Machinery wall cabinets (hero 07) | B (blind r1: B-) | better | All hardware is geometry from `modelkit`:<br>- two dials (printed face, octagonal bezel, needle, hub)<br>- red and amber lamps<br>- an equipment plate<br>- a louvred vent with tilted blades (`gen_shapes.louvre`)<br>- a bar handle, a lock and a warning decal<br>- a cap, a gland and conduits<br>- a frame-and-panel door on a toe-recessed plinth<br>The blind reviewer: "now read as geometry". Round 2 made the paint grimy and darker. |
| Free-standing machine cabinets | B- (blind r1: C) | better | The same kit, in one block. Round 1's body was lighter and too clean ("green appliances"). Round 2 darkened and dirtied it, gave the top a dusty texture of its own, and made the bezels smaller and darker. In Level 3 too (not reshot). |
| Dead tram, cab front (hero 06) | B- | better | Windows set back in the frame, with seals and wipers; a barred grille; two headlamps in bezels under visors. The band has its own key, so it lines up with the sides. The blind reviewer: "read clearly at 4-6 blocks". |
| Tram body, hood, wheels, rails | C+ | better | Painted metal gone to rust, with grime and runs. The hood's painted grilles are louvred grilles now. Wheels read round (a square plus the square turned 45 degrees). Rails have a foot, web and head. The logo and the window glare are still painted. |
| Tunnel concrete walls | C+ (blind r1: C, same/worse) | same to slightly better | Round 1 was noisier. Round 2 has a quieter aggregate and broad soot. The three versions share one ground, so the round-2 test's block squares are gone. The lift line is in one version only. |
| Brick panels | B- | better | `matlib.brick`: shaded bricks, a hue for each, recessed 2 px joints, soot. Same mean. |
| Ceiling | C+ (blind r1: D) | better | The painted pipe band is removed (round 1 had shaded it). It is plain soot-stained concrete in three versions. |
| Wall-pipe flanges and brackets | B- | same | Rusted paint, banded light and dark, bolt heads. Hardly visible at distance. The pipes are unchanged. |
| Steel doors | C+ (blind r1: C) | better | Lever, kick plate, hinges and window bead are geometry, on all four sides of the leaf (no facing needed). The leaf is repainted with rust at the foot only. Round 2 made the hardware dark scuffed steel and the number larger. |
| Candle stubs, machine parts | C | slightly better | The gear is a toothed disc in geometry. Candles have a pool, a run and a hollow top. They are too small in every shot to judge. |

**Rounds**
1. **Round 1, blind:**
   - Better: the cabinets' hardware, the tram front, the brick and the door handle.
   - D for the ceiling's painted pipe band.
   - C for the free-standing cabinet body (lighter and clean).
   - C for the concrete (noisier, the one-block repeat showing).
   - Doors: the kick plate did not read and the number was a blur.
   - No layout change. Brightness matched except the cabinets.
2. **Round 2 fixed those items:**
   - Pipe band removed.
   - Darker, grimy cabinet paint and smaller, darker bezels.
   - Quieter concrete with soot.
   - Seam-free versions.
   - Dark kick plate and a larger number.
   - Grime and rust runs on the tram.

**Carried below B, with reasons**
- **Tunnel concrete and ceiling (C+):** a dark, plain cast surface. The tie holes sit on the block grid, as they did before, and moving them is the next step. B4's lesson on large surfaces applies.
- **Steel doors (C+):** the leaf is a cube with paint, as vanilla's iron door is. The four-sided hardware is the most a facing-less block allows.
- **Tram body (C+):**
  - The logo is lettering at 6 px, stretched over the side.
  - The window glare is painted.
  - The rear is in no shot.
- **Not touched, for budget:**
  - hazard warning panels (C; a stair-step halo; the blind reviewer flagged them)
  - oil drums (C)
  - tunnel lights (kept as before, B3's lesson)
  - overhead pipe bundles (B)
  - the trolley and the wagon's load
- **Shared assets:**
  - The floor is `concretefloor-plain` (B4's), unchanged here.
  - `machinecabinet` also stands in Level 3.
  - `wallpipe-flange` is also on Level 3's wall pipes.
  - Neither of those levels was reshot.
- **The old cube textures** `tunnelwall-machinery.png` and `props/cabinet-front.png` are still written, but no Level 2 face uses them. The blind reviewer saw the first on the texsheet only.

**Tool change:** `tools/shotbot/batch.py` header now also runs `/backrooms shift 0` and `/backrooms stat stability 1` (see Lessons).

**Lessons**
- A Reality Shift that starts in the review world never ends while `batch.py` holds the clock stopped, because it runs in in-game hours. It blacks out every enclosed level, and the save keeps it, so later sessions inherit it.
  - Two later Level 2 runs came out 10-45 levels darker, and one came out 4-10 levels brighter as the shift changed state.
  - The header now ends any shift and fills stability.
  - Before a review, compare every shot's mean brightness. If a whole run moves, retake it before judging anything.
- Alternates of a large plain surface must share their low-frequency ground (the same `matlib.concrete` seed), with only the features differing. Otherwise each block's mottle differs and the wall reads as a patchwork of squares at 2-3 blocks.
- A painted copy of a 3D feature that hangs right beside the real one (the ceiling's pipe band under the pipe runs) reads as D painted-3D. Shading it makes it worse. B4's "keep and shade" lesson holds only where nothing modelled stands next to it.
- A block with no facing (a door, a wall prop) can still carry modelled hardware. Put it on all four sides with `modelkit.turn`, as the pipe walls do; on the sides against walls it is buried. This is the way to model B4's `metaldoor` hardware without a new code, and it needs a fresh look at lighting in the shots (the doors here lit the same as the cubes).
- `modelkit.grille`'s bars overlap into a solid plate when the opening is under about 3 units tall. Small vents want tilted louvre blades (`gen_shapes.louvre`).

### D1

Worker report (Opus, 2026-10-14). Follow-up batch on the user's per-family decisions for B3, B4 and B5 (`decisions.md`,
each acted-on row now ends with a "D1:" note). Branch `gfx/D1` from `main`, uncommitted. **Offline only: nothing was
shot** (the user's game was running). The grades below are my own reading of the offline sheets, not a blind review,
and every item still wants an in-game look before it is called done.

**Evidence** (all in `review/d1/offline/`)
- `tile-<family>-<before|after>.png`: `texsheet.py --tile` for every changed family. "Before" is `main`, plus the
  parent of the batch that changed it (`pre-B3` for papers, troffers and the box; `pre-B4` for floors; `pre-B5` for the
  tunnel walls). The source PNGs are in `tex/<family>/<label>/`.
- `mock-wall-6x3.png`: the yellow wall as 6x3 blocks (two upper rows over a baseboard row, versions at random with the
  new weighting), pre-B3, main and D1, each at 4x and averaged down 4x for playing distance.
- `mock-floor-<plain|wet|dark|hall>-6x3.png`: each floor as 6x3 blocks with versions and turns at random, as the
  blocktype picks them, pre-B4, main and D1, at 4x and averaged down. The label gives a seam ratio: the colour step
  across a block edge over the step inside a block, where 1.0 is seamless. "Broad" is the same on 4 px averages.
- `preview-crates.png`, `preview-boxes.png`: `preview_shapes` renders from the north-west, from the south-east, and
  tipped toward the camera to see inside. The closed crate, main's emptied cube and D1's emptied crate; the sealed box,
  the pre-B3 torn box, main's B3 torn box and D1's opened box.
- `layouthash-v1.txt`, `layouthash-v4.txt`.

**Checks**
- Build (`tools/locked.sh mod gfx`): 0 warnings, 0 errors. The deleted `tunnelwall-plain-2/-3` were also removed from
  the scratch Mods dir.
- `layouthash` v1 `18cfdbc1c530f039` and v4 `ca047189969b69db`: identical to B5's files line for line (the
  existing `mapgen-gfx` harness; no C# changed).
- `check_zfight`: clean on `crate-open.json` and `supplybox-torn.json`.
- No code, variant group or class renamed or removed. `crate-open` changes from `drawtype: cube` to `json` with the same
  code, as B5's doors did. Generator JSON churn was restored from git: `exitlintel*.json` key order, and
  line-ending-only rewrites from `gen_loop` and `gen_detail`.

**Per item**
1. **Tunnel walls: done, meets the request.**
   - `gen_textures.tunnel_concrete` is the pre-B5 function again; `tunnel_cast` is removed.
   - `tunnelwall-plain.png` is byte-identical to `cce3222^`. So are `tunnelwall-warning.png` and the old
     `tunnelwall-machinery.png` cube texture, which are drawn on the same concrete.
   - `tunnelwall-plain-2/-3.png` are deleted.
   - `blocktypes/level2/tunnelwall.json` is restored to its pre-B5 text, so it has no `*-plain` alternates line.
   - Brick (`tunnel_brick`) and the B5 ceiling are kept.
2. **Emptied crate: re-imagined as a model. My grade B; meets the request, to be confirmed in game.**
   - `gen_loop.open_crate_shape`, `shapes/block/crate-open.json`.
   - Outside, it is the closed crate's own sides, as walls 1.5 thick (the frame's width). Their tops are the closed
     crate's top frame, so from above it reads as the same box with the lid boards gone.
   - Inside: dark board backs with nail points, darkest at the foot, and a floor with the walls' shadow.
   - One lid board has been thrown back in and leans against the east wall, its torn ends in pale split wood.
   - The middle board of the north side is broken out at its west end, clear of the painted brace: a stepped break with
     a splinter, and you see into the crate there.
   - Two of the lid's nails are bent up on the rim.
   - Straw is geometry: two heaps on the floor, and tufts pulled up over the north and west rims that droop inside.
     There is also a crumpled newspaper wad.
   - It is placed in stacks, so nothing stands above the block except the nail tips and the rim straw. Those lie inside
     the next crate's walls and floor.
   - Blocktype: `sidesolid` all false except down, `sideopaque` false, `lightAbsorption` kept at 99 (as B5's doors).
     The blocktype `textures` were dropped, since an `all` would paint every part.
   - Risk: the inside is lit by the neighbours in each face's direction, so it may read lighter in game than the dark
     textures suggest. The floor contents only show from fairly close and above, so at a distance the read rests on the
     open top, the rim straw, the board leaning inside and the broken side.
3. **Opened supply box: rebuilt from the pre-B3 design. My grade B; meets the request.**
   - `gen_loop.torn_box_textures`, `torn_box_shape`.
   - It has the sealed box's footprint, its 10 high walls, and its own faces outside (`supply_box_faces`: the worn
     sides with the tape and arrows, the plain ends).
   - It is opened the way it was sealed: the tape is slit along the seam at x 8, the stub on each side is cut through,
     and a ragged half of the tape stays on each flap's free edge (`supplybox-flap`, made from the sealed top).
   - The east flap stands up leaning out, with its south corner torn away (as geometry). The west flap is folded right
     back and hangs down the side. The two short inner flaps are bent up.
   - The inside is dark kraft like the original's: the walls darken toward the foot, and the floor shows the bottom
     flaps' seam and a water ring.
   - The contents are geometry: a straw heap, a tuft over the north rim, a few stalks dropped on the ground outside, the
     crackers wrapper crumpled in two pieces, and a newspaper wad.
   - There are no torn teeth. Everything stays inside the block.
   - The collision and selection boxes are 10/16 tall now, matching the walls; they were 9/16.
4. **Concrete walls: done, meets the request.**
   - The cracked version (`-3`) is listed once in eight in `blocktypes/level1/concretewall.json`.
   - Its crack is shorter (9-14 px) and fainter (0.14).
5. **Car park and hall floors: seamless offline. My grade: meets the request, pending the in-game look.**
   - The seam was not an edge darkening; there is none. Each texture wrapped on its own (unturned seam ratio 0.70).
     The edges came from two things:
     - the blocktype turns every version and mixes three seeds, and a turned block's broad pour patches do not
       continue into its neighbour's;
     - the hall floor has almost no grain to hide this.
   - The fix is a new `matlib.turn_safe`:
     - each version keeps its own broad patches in the middle;
     - toward the edges they blend into one shared field, made four-fold symmetric, so the edge is the same at every
       turn and in every version;
     - the crack, the scuff and the mould fade out before the edge (`gen_textures.inside_block`).
   - The hall floor keeps a quarter of its own mottle (`keep=0.25`). With all of it, a calm border round a mottled
     middle read as cushions.
   - Seam ratios, main to D1 (pixel / broad):

     | floor | main | D1 |
     |---|---|---|
     | plain | 1.41 / 1.19 | 1.05 / 0.69 |
     | wet | 1.04 / 1.22 | 0.97 / 1.00 |
     | dark | 1.25 / 1.51 | 1.20 / 0.97 |
     | hall | 1.95 / 2.04 | 1.24 / 1.32 |

   - On the mocks no block squares show in any of the four. The hall's ratio stays above 1 because its paint is so
     even inside a block that any fine difference counts.
   - The pour patches are a little calmer near the block edges than B4's.
   - Following the plain floor, these changed too: the line and dash blocks, `parkarrow`, `parkoil`, `parkdrain`, and
     Level 9's `housefloor-garage`.
6. **Troffers: done, meets the request.**
   - The near-black 1 px gap is gone. The frame's inner edge is now in soft shade: -0.16 on the top and left,
     -0.06 on the bottom and right.
   - The bevelled frame is kept, and the lights are still cubes.
7. **Ceiling tiles:** kept, untouched.
8. **Wallpaper: made seamless, not restored.** Musty tone and grain kept. My grade B; it meets the request on the mocks,
   to be judged at playing distance in game.
   - The chevron paper is a new `gen_textures.chevron_wall`. Every block of the yellow wall, every part and every
     version, shares one paper ground (`CHEVRON_PAPER`); only the fibre and the ink differ per block.
   - Gone from B3's paper:
     - each block's own mottle, strip shades and hue drift;
     - the butt seams every 16 px;
     - the 16 px hue jitter.
   - One faint seam is on the block edge in the `-2` version only. The yellow wall lists `-2` two blocks in five.
   - The chevron rows sit on the 8 px grid and line up across every edge.
   - Two calls of my own, each easy to undo:
     - The bead lines print at 0.8 (`CHEVRON_BEADS`; B3 had 0.5), nearer the old paper the user preferred.
     - The damp version, whose stain is the one mark that sits in the same place each time, is listed one block in five
       for this paper only (`texturesByType` in `blocktypes/wallpaper.json`). Its lifting seam moved to the block edge.
   - Seam ratio, B3 to D1: 0.81 / 1.08 to 0.98 / 1.01.
   - The other papers are byte-identical.
9. **Carpets: done, subtle. Meets the request.**
   - `gen_textures.dingy` on the normal and stained pile:
     - 10% duller and 3-4 levels darker (mean 145 to 141);
     - a faint tracked-in grime at tuft scale, so turned blocks still meet;
     - nine flecks of grit and lint.
   - Soaked and threadbare get a lighter dose.
10. **Outlet:** kept, untouched.

**Shared assets that changed with these**
- `supplybox-straw` (a little more muted) and `supplybox-paper` (new) are used by both the opened box and the emptied
  crate.
- The floor changes reach Level 9's garage floor and every Level 1 marking block built on the plain floor.

**Not done, for the overseer**
- No in-game shots or side-by-sides: they need the user's screen.
- To shoot:
  - Level 0: a long yellow wall at 2-6 blocks, a cache with sealed and opened boxes, troffers from below, the carpet.
  - Level 1: a car park floor and a hall floor at 3-8 blocks, a fire wall, a cache with closed and emptied crates
    (including a stack).
  - Level 2: a wall with brick and a warning panel.
- Mean brightness: the carpets are 3-4 levels darker by design; nothing else moved in mean.

**Scratch tooling** (not committed; copied to `review/d1/offline/tools/`):
- `d1kit.py`: mock walls and floors in the blocktype's real mix, and the seam ratios.
- `prev.py`: previews from any commit, with turned and tipped views.
- `evidence.py` and `evidence2.py`: they rebuild `review/d1/offline`.

If the mock floors and walls prove useful, they would belong in `tools/texsheet.py` as a `--mix` mode.

### B6

Worker report (Opus, 2026-10-14). Branch `gfx/B6` from `main`, uncommitted. Two rounds: one blind review (round 1), then a fix and a reshoot. The round-2 grades are mine.

- **Final sheets:** `review/b6/compare-round2.jpg` (every spot) and `review/b6/compare-round2-detail.jpg` (24 key spots at twice the size). After shots are in `review/b6/final/`. Round 1 is in `review/b6/compare-round1*.jpg` (shots in `review/b6/after/`).
- **Per-family pairs:** `review/b6/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B6.json`. The B6 section is added to `review/compare.html`.
- **Decision table:** twelve rows added to `decisions.md`, decision column empty.
- **Offline evidence** (`review/b6/offline/`):
  - `tile-<family>-<before|after>.png`: texsheets with vanilla references;
  - `mock-<surface>-6x3.png`: the blocktype's real mix, at 4x and averaged;
  - `preview-<family>.png`: models before and after;
  - `harness/`: layouthash and validate output;
  - the scratch tools in `tools/`.

**Checks**
- Build: 0 warnings, 0 errors (`tools/locked.sh mod gfx`).
- `layouthash`: v1 and v4 match D1's output line for line (`review/b6/offline/harness/layouthash-v*.txt`). No C# changed.
- `validatelevel 3` (`SPAWN=16000`, 24 cells): both arrivals have 0 unreachable tiles, 0 doorways to nowhere, 0 blocked doorways and 0 bad decor (`harness/validate3.txt`).
- No block, item or entity code, variant group or class was added, renamed or removed. No layout version. Only textures, shapes and texture lists changed, so B6 was shot in `gfxreview`. `DetailBlocks.g.cs` and `en.json` are unchanged.
- `check_zfight` is clean on every new shape. The hits left were already there: statue arms and wings, the control desk backboard and the switchgear cap on the block edge, and the coal heap against its shovel.
- Brightness: every final shot is within 3 levels of the new baseline except these (`review/b6/luma-final.txt`):
  - `close-wall` (-8): the wall itself is unchanged (55.2 to 55.6). The riser in frame now wears the wall pipes' own lagging skin, which is darker than the old flat cream.
  - `close-light` (-6), `tray-close` (-4), `risers-close` (-4): the trays and risers themselves.
- Deleted textures, only used by the replaced shapes: `level3/panel`, `level3/fan`, `detail/switchgearfront`, `detail/fancage`, `detail/controlpanel`. Round 2 also dropped `detail/l3stone-2`. None is in the scratch Mods dir.

**Baseline and spots**
- `review/baseline/3` is reshot on `build-gfxbase`: unchanged `main`, built from a `git archive` of `main` in `%TEMP%/b6main`, because the tree held B6.
- The B0 set is kept in `review/baseline/3-b0`. It differed by 2-6 levels except the re-spotted `close-floor` (`review/b6/drift-b0-vs-main.jpg`).
- The first baseline run was 25-45 levels darker throughout. It is kept in `review/b6/baseline-dark-run1`; see the lessons.
  - A retake of three spots came out at the normal brightness.
  - A full reshoot was then pixel-identical to that retake.
  - A Level 2 check against B5's baseline was within 3 levels.
- Re-spotted:
  - `close-floor` stands under a light; the arrival room is unlit.
  - `den-wide`, `den-close` and `pipeend-close` are now `-inspection` shots (daylight and a lantern). The den and the overhead pipe end are dark by design.
- Added, all found lit on the harness grid (`review/b6/offline/tools/findspots.py`): `boiler-wide/-close`, `statue-wide/-close`, `vault-close`, `fixtures-wide`, `panel-close`, `fan-close`, `gauges-close`, `tray-close`, `risers-close`, `roomsign-close`, `switchgear-close`, `transformer-close`, `coal-close`. 49 spots in all.
- `gauges-close` and `roomsign-close` were moved after round 1 (see the lessons) and reshot on both builds.

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Walls: brick, glazed tile, cinder | B / B / B- (blind r1: B, B, B-) | same / slightly better / better | Old tones and unit sizes kept; the blind reviewer measured the means unchanged within 1 level. Each unit is now shaded with recessed joints. Three versions per wall share one ground. Round 2 calmed the cinder's black pits and olive/grey swing. |
| Dusty floor, plaster ceiling | B (r1: B) | better | The blotch in every block (a polka-dot grid) is gone. The floor has three turned, seamless versions; the ceiling has five, with stains about one block in fourteen. Tones kept. The ceiling is flat. |
| Grating, hazard floor | B- / B (r1: B-, B) | same | Shaded bars; round 2 gave the bars and rods one weight (round 1 read as pinstripes). The stripes are clean at the seams. |
| Breaker panels | B (r1: B) | much better | Breakers, toggles, label, warning decal, main switch and gland are all geometry. Round 2 dulled the white toggles, which speckled at range. |
| Wall fans | B- (r1: B-) | better | Housing, rounded opening, four blades, hub, well and guard as geometry. Round 2 has one guard ring and lighter blades (round 1's guard read as a maze). |
| Cable trays and lights | B- (blind r1: C) | better up close, same at range | Round 1's ladder tray made every ceiling a lattice. Round 2 is a solid trough with low rails, round cables and a strut. The tube and its light are unchanged. |
| Gauges, risers, wall cables, junction boxes | B+ / B- / B / B | much better / better | Modelled gauges on a round pipe; round risers with feet and clamps; round cables in clips; the junction box with lid, screws and couplings. |
| Switchgear, control desk, transformer, generator | B+ / B / B+ / B | much better | Meters, lamps, toggles, buttons, louvres and handles are geometry. The transformer has real fins (it painted fins over flat ones) and bushings. |
| Boiler (shared with Level 5) | B (r1: B) | much better | Riveted octagonal shell, bands, crown, firebox door with hinges and latch, gauge, nameplate, safety valve. Footprint, collision box and steam position unchanged. |
| Room plaques, OUT OF BOUNDS | B+ (r1: B+) | better | Enamel faces, bevelled and chipped; screws as geometry. |
| Coal heap | B (r1: B) | same to slightly better | Faceted coal; lumps as boxes. |
| Sanctum ashlar, flagstones, runner, vault, candelabras | B- / original / B- / B / B- (blind r1: B-, C, C, B, B-) | same | Round 2 restored a mixed-length ashlar bond (r1's running bond lost the character). The flagstones are the original texture again (r1's square grid was worse). The runner has a short even pile (r1 read as red static). Candelabras have drip pans and wax; candles unchanged. |
| Statue | B (r1: B) | same | Limestone, shaded folds, scalloped feathers. Geometry unchanged. |
| The Purpified | C+ (r1: C+) | same | Veined wet skin, lumps and glowing pores as geometry. Round 2 gave the stain a ragged edge and fewer veins. It still reads as a stain from most angles. |

**Rounds**
1. **Round 1, blind** (Opus; asked specifically about tone and geometry):
   - **Tone:** walls, floors and ceilings kept their original tone within about 1 level of mean; only contrast rose.
   - **Geometry:** panels, gauges, switchgear, desk, transformer, boiler, generator and plaques read clearly as geometry ("the machine props are the clear win").
   - **C:** the tray lattice, the runner's grain and the square flagstones.
   - **B- / C+:** a generic ashlar bond, cinder speckle, grate pinstripes, the fan reading as a maze, and the Purpified as a stamped decal.
2. **Round 2 fixed those items:**
   - trays: a solid trough;
   - runner: a short pile;
   - flagstones: reverted;
   - ashlar: a mixed bond;
   - cinder: calmer;
   - grate: even weights;
   - fan: one guard ring and lighter blades;
   - toggles: duller;
   - Purpified: a ragged edge.

   Reshot once.

**Carried below B, with reasons**
- **The Purpified (C+):** it is a single decal on two wall blocks plus a small carcass. Reading as a growth wants a larger lumpy model across several blocks, which means a new decoration footprint (layout).
- **Floor fan:** in no shot (generator rooms only). Judged on the preview: the guard is dark and thin.
- **Risers:** the roundness is the wall pipes' baked gradient, as B5's wall pipes are; it is consistent with them.
- **Not touched:**
  - bulkhead lights (their cage was already geometry, and lights stay as they are)
  - iron bars (B)
  - manhole ring (painted, rare)
  - window glow (in no shot)
  - coil unit, conveyor, cable spool
  - knife switch, alarm bell, sparking outlet
  - the tar pipe bundles' painted joint (they are Level 2's shapes)
  - the doorway `roomsign-N` cubes
- **Clay:** the flooded tunnel's clay is vanilla raw clay, out of scope.
- **Shared assets that changed elsewhere:**
  - `dustyfloor`, `plasterceiling` and the boiler: Level 5's boiler bays (B8 should re-judge the boiler there);
  - `cable`: Level 4's cable droops;
  - `insulator`: the coil unit;
  - `stone`: a base in `gen_deep`;
  - the coal heap, wherever it is placed.

  None of those levels was reshot.

**Tool changes**
- `matlib.brick(tones=)`: versions that share one ground. Units across the block edge keep one shade. The default output is unchanged; every other texture regenerated byte-identical.
- New `gen_shapes.round_riser` (vertical round pipe) and `gen_textures.calm_hue` / `match_rgb`.
- `detail_kit.EXT` gains Level 3 and Level 2 material keys.

**Lessons:** four lines added above.

### B7

Worker report (Opus, 2026-10-14). Branch `gfx/B7` from `main`, uncommitted. Level 4, plus Level 9's asphalt, re-done at the user's request after B11 (a scope addition from the overseer). Phase 1 was offline; phase 2 was one blind review (round 1), then a fix and one reshoot. The round-2 grades are mine.

- **Final sheets:** `review/b7/compare-round2.jpg` (every spot) and `review/b7/compare-round2-detail.jpg` (20 key spots at twice the size).
  - After shots: `review/b7/final/4` and `review/b7/final/9`.
  - Both levels side by side: `review/b7/sbs/{before,after}` (the Level 9 shots prefixed `9-`).
  - Round 1: `review/b7/compare-round1*.jpg`, shots in `review/b7/after/`.
- **Per-family pairs:** `review/b7/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B7.json`; asphalt is its own family. The B7 section is added to `review/compare.html`.
- **Decision table:** ten rows added to `decisions.md`, decision column empty. The asphalt row says it was re-done at the user's request after B11.
- **Offline evidence** (`review/b7/offline/`):
  - `tile-<n>-<family>-{before,after}.png` for seven families, asphalt included;
  - `mock-*-6x3.png` (carpet, ghost, mixed carpet, ceiling, mixed ceiling, wall, road) and `mock-hotelramp.png`;
  - `preview-*.png`, the models beside main's;
  - `harness/`;
  - the scratch tools in `tools/`.

**Checks**
- **Build:** 0 warnings, 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir).
- **`layouthash`:** v1 and v4 match B6's output line for line (`review/b7/offline/harness/`). No C# changed and `DetailBlocks.g.cs` is unchanged.
- **`validatelevel 4`** (`SPAWN=16000`, 24 cells): Level 4 has 0 unreachable tiles, 0 doorways to nowhere, 0 bad elevators and 0 decor facing walls. The one blocked doorway reported in each arrival area is in Level 5, which this batch did not touch.
- **Saves:** no code, variant group or class was added, renamed or removed. No layout version. B7 was shot in `gfxreview`.
  - `officeceilingalt`'s vent and sprinkler kinds draw as JSON (`drawtypeByType`); the stain kind stays a cube.
  - `ficus` gets `renderpass: OpaqueNoCull`.
- **`check_zfight`:** clean on every new shape. The hits left are faces on a neighbour's plane that were already there (the partition's ends, as the old panel had, the counter splash and the whiteboard sides), and the cooler bottle's underside at y 16 (nothing stands above it).
- **Churn and scope:** generator churn (line endings, the `exitlintel*` key order) restored from git. `lang/en.json` and every other level's textures regenerate byte-identical.
- **Brightness:** every final shot is within 4 levels of the new baseline, except these (`review/b7/luma-final.txt`):
  - `sleepingbag-close` (-8): Level 4's wanderer stands at its camp in the after shots (an entity, not an asset).
  - `wide-01` (-4.7): the modelled extinguisher cabinet's shadowed tub.
  - `hotelturn-close` (+4.1): the partitions' aluminium.
  - `ficus-close` (+4.1): the ficus no longer hides the wall.

**Baseline and spots**
- `review/baseline/4` is reshot on `build-gfxbase` (unchanged `main`, built at the start of this batch). The B0 set is kept in `review/baseline/4-b0`.
  - It had drifted 2-7 levels, mostly darker in the dim corridors.
  - A retake of three spots was pixel-identical (`review/b7/base-check`).
- `review/baseline/9`'s `day-street` and the new `day-road-close` were shot on `build-gfxbase`. The earlier Level 9 set is kept in `review/b7/baseline9-before-b7`.
- Added to `spots/4.json`, all found lit on the harness grid (`review/b7/offline/tools/findspots.py`): `desk-close`, `cubicle-close`, `rail-close`, `filing-close`, `ficus-close`, `poster-close`, `poster-close2`, `extinguisher-close`, `whiteboard-close`, `hotelblend-wide`. Three of them were moved after their first frames: the filing cabinet was hidden, "cooler" turned out to be the ficus, and the blend was behind a partition.
- Added to `spots/9.json`: `day-road-close`.
- Two runs (`review/b7/after-dark-run1`) came out 40-100 levels darker throughout; see the lessons. Everything was reshot after the fix.

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Office walls, skirting | B- (blind r1: C/B-) | same | Plaster in the old off-white, hue held. Round 2 dropped the nail-hole specks. Grey vinyl cove base. |
| Carpet (plain, ghost, papers, stains) | B (r1: B) | better | Loop-pile heather, dingy, seamless versions. The tone held within 0.5 level. Papers and stains in several arrangements. Ghost patches stay block-shaped (layout). |
| Drop ceiling, troffers | B (r1: B) | better | Level 0's module in 2x4, the darker grid, three versions. Round 2 spread the stain over a block's two tiles. |
| Diffuser, sprinkler | B- (r1: D, worse) | better | Round 1's three stepped cones smeared at range, and their sides read as broken rings. Now a face plate with crisp painted slots and one cone. The sprinkler is a smaller head with a muted bulb. |
| Cubicle partitions | B- (r1: C, model B-) | better | Posts, a bevelled cap with a lit edge, a base raceway, world-UV fabric. Round 2 calmed the 1 px checker of the weave and dulled the aluminium. |
| Desk, terminal | B (r1: B) | much better | Pedestal and pulls, edge banding, a recessed screen and the tube's hump, keys, mouse, paper. |
| Office chair | B+ (r1: B+) | much better | Five-star base, gas lift, arms, cushions and shell. |
| Filing cabinet, cooler, vending, counters, copier, tables | B / B- (r1: B to B-) | better | All hardware is geometry. Round 2 gave the plastic and enamel fills a fine grain (r1 found them airbrushed). |
| Ficus | C+ (r1: D, worse) | better than r1 | Round 2 made the foliage denser and closed round two branches. It still reads as sparse, dead leaves. |
| Extinguisher cabinet | B (r1: B) | much better | Was a painting of one; now a tub, a bead and the extinguisher as geometry. |
| Posters, whiteboard | B (r1: B-) | better | Frame beads; nine prints as alternates. Round 2 draws the print at 64 px so the word reads from 2 blocks. Aluminium whiteboard frame. |
| Windows | C+ (r1: C) | slightly better | Fogged glass with rain runs in two versions. The blackout panes are unchanged (lore). |
| Hotel-red ramp | n/a (Level 5's blocks) | same | Checked only (`mock-hotelramp.png`). The blind reviewer graded the hotel carpet C; that is B8's. |
| Level 9 asphalt | B (r1: B, much better) | much better | Fine, even grain in the old tone. No square marks. Seamless versions; the soft patch and the faint crack each one block in sixteen. Round 2 made the crack fainter. |
| Level 9 markings | B- (r1: C) | same | They take the asphalt's grain and are clean at the seams. No wear, on B4's lesson. In no shot. |

**Rounds**
1. **Round 1, blind** (Opus; asked about tone, geometry and the road grain):
   - **Tone:** the office surfaces held their tone (means within about 0.5) with no grid at playing distance.
   - **Geometry:** "the furniture is now geometry".
   - **Road:** fine and even, with no square marks or seams.
   - **D:** the diffuser and the ficus.
   - **C:** the partition fabric's checker.
   - **B-:** airbrushed plastic and enamel fills, soft poster lettering, a loud red sprinkler bulb, wall pin specks, the ceiling stain too small.
   - **Out of scope:** the hotel carpet, elevator doors, ghost-carpet rectangles and Level 11's `asphalt-cracked` squares.
2. **Round 2 fixed those items:**
   - the diffuser rebuilt;
   - the ficus denser;
   - the weave calmed and the metal dulled;
   - grain on the fills;
   - 64 px posters;
   - the bulb muted and the head smaller;
   - no specks on the wall;
   - a larger stain;
   - two rain versions;
   - a fainter road crack.

   Reshot once.

**Carried below B, with reasons**
- **Ficus (C+):** a dead plant from three cut-out clumps. A convincing one needs real branch geometry, and the leaves read as sparse at any density, because the cut-out shows the room behind.
- **Ghost carpet:** the darker patches are placed by the layout as whole blocks, so they read as a block patchwork. B3's lesson: no per-block texture answer.
- **Windows (C+):** the blackout panes are a lore choice and stay as they are.
- **Not touched:**
  - elevator doors (C)
  - conference glass
  - corkboard, evacuation map, clock, phone, alarm
  - fridge, microwave, bookshelf
  - the reception desk's CRT box, chair stack, coat stand, server rack
- **Level 11:** `asphalt-cracked` (`gen_city.street_textures`, B12) still paints a square patch over the new asphalt.
- **Shared assets that changed** (none of these levels was reshot):
  - `officewall`, `drywall-base` and `officedeco`: Level 11's office buildings and the drywall EXIT lintels and elevator surrounds;
  - `officelight-on`: Level 11's subway lights;
  - `laminate`: the bookshelf and the reception desk;
  - the asphalt: Level 11's road markings.

**Tool changes**
- `tools/shotbot/batch.py`: the header ends a Reality Shift again after setting the clock (see the lessons).
- `matlib.asphalt`: new `chip`, `pits` and `shadow` options; the defaults are unchanged.
- `gen_textures.troffer`: new `rail`, `frame`, `table` and `tubes` options; the defaults are unchanged.
- `detail_kit.wall_family`: a `textures` option (texture alternates for a decoration's keys).
- `detail_kit.EXT`: the Level 4 furniture keys.

**Lessons:** three lines added above.

### B8

Worker report (Opus, 2026-10-14). Branch `gfx/B8` from `main` (fe39cf5), uncommitted. Phase 1 was offline; phase 2 was one blind review (round 1), then a fix and one reshoot. The round-2 grades are mine, from the round-1 review and the fixes.

- **Final sheets:** `review/b8/compare-round2.jpg` (every spot) and `review/b8/compare-round2-detail.jpg` (20 key spots at twice the size). After shots: `review/b8/final/`. Round 1: `review/b8/compare-round1*.jpg`, shots in `review/b8/after/`.
- **Per-family pairs:** `review/b8/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B8.json`. The B8 section is added to `review/compare.html`.
- **Decision table:** nine rows added to `decisions.md`, decision column empty.
- **Offline evidence** (`review/b8/offline/`):
  - `tile-<n>-<family>-{before,after}.png`: walls, floors, materials and doors, lifts and desk;
  - `mock-{wall,carpet,maroon,wood}-6x3.png`: the blocktype's real mix, at 2x and averaged;
  - `preview-*.png`: the models beside main's, and small scenes (`preview-door-scene.png`, `preview-door666-scene.png`, `preview-wall-scene.png`, `preview-chandelier-big.png`, `preview-desk.png`);
  - `harness/`; the scratch tools in `tools/` (a multi-block scene renderer `scene.py`, `mocks.py`, `findspots.py`, `churn.py`).

**Checks**
- **Build:** 0 warnings, 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir).
- **`layouthash`:** v1 and v4 match B7's output line for line (`review/b8/offline/harness/`). No C# changed; `DetailBlocks.g.cs` and `lang/en.json` are unchanged.
- **`validatelevel 5`** (`SPAWN=16000`, 24 cells): Level 5 has 8 unreachable tiles of 88,887 and no blocked doorways; the 27 blocked doorways reported are Level 6's. Main's output (no C# changed).
- **Saves:** no code, variant group or class was added, renamed or removed. No layout version. `hoteldoor` keeps its parts and draws as JSON; otherwise only shapes and texture lists changed. Shot in `gfxreview`.
- **`check_zfight`:** no same-shape pairs on any new shape. Round 1's door casing put faces on the neighbouring wall's plane on the buried sides (see the lessons); round 2 fixed it. The flags left are faces in corridor air or inside the neighbour.
- **Churn:** line-ending churn and the `exitlintel*` key order restored from git; full runs of `gen_textures.py` and `gen_shapes.py` leave every other texture and shape byte-identical.
- **Brightness:** every final shot is within 2.5 levels of the new baseline (`review/b8/luma-final.txt`).
- **Textures removed** (no longer referenced): `level5/hoteldoor-lower`, `-upper0..9`; `detail/receptionmahogany`, `detail/keyrack` (the orphan), `detail/callplate`, `detail/cagegate-l/-r`.

**Baseline and spots**
- `review/baseline/5` is reshot on `build-gfxbase` (unchanged `main`, built at the start of the batch). The B0 set is kept in `review/baseline/5-b0`; it had drifted 0-7 levels brighter, most in the dim rooms. A retake of three spots first (`review/b8/base-check`) matched the full run.
- Added to `spots/5.json` (found on the harness grid, `review/b8/offline/tools/findspots.py`): `door-close`, `sconce-close`, `portrait-close`, `chandelier-close`, `desk-close`, `keyrack-close`, `stairs-close`, `elevator-close`, `callplate-close`, `boiler-inspection`. After the first base frames, `portrait-close` and `elevator-close` were moved (they framed the wrong block) and the boiler bay became an inspection shot (13 levels mean: dark by design).
- `den-wide`/`den-close` press the camera into a panel and `prop-1` is too dark to judge (as on main).

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Guest-room doors, number plates | B (blind r1: body geometry, hardware D) | much better | Casing with plinths and a capped head, frame-and-panel leaf with raised fields, kick plate, knob and escutcheon, hinges, peephole; the brass plate a box with engraved numerals (per `upperN`). Round 2: slim hinges, a rounder knob, and the casing kept off the block's sides (its buried copies shimmered on the wall). |
| Damask panels, gilt frames | B (r1: B) | same / slightly better | Tone exact; the frame shaded as a moulding with its shadow; three cuts of the print and a rare water mark. Still 64 px. |
| Wainscot, frieze | B / B- (r1: B, B-) | better | Raised and fielded panels with grain; stiles across block edges; a picture-rail moulding on the frieze. One version (a second grain read as a patchwork). |
| Corridor carpet | B- (r1: C, a dot grid) | better | Pile with the old rings and hearts dyed in, seamless turned versions; round 2 adds gold rosettes between the medallions. |
| Maroon, lobby carpets, runner, rug | B- / C / B / B (r1: C, -, -, B) | same / better | Pile, dingy; round 2 calmed the maroon's noise. The lobby keeps its per-block red border (design; not in a shot). |
| Walnut floor | B (r1: B) | better | 8 px boards, grain, single butt joints in five versions. |
| Beams, coffers, ceiling | B- (r1: beams B-; ceiling C) | better (beams) / same | Grained beams with fillets round each coffer; the cream ceiling is plain plaster (the reviewer still reads it as flat). |
| Chandelier | B+ (r1: B+) | much better | Arms, cups, pans, column, chain and crystal drops as geometry. The drops are plain pale bars (what keeps it from A). |
| Sconces | B- (r1: C) | better | Backplate, boss, arm, pan and cup as geometry; round 2 made the candle slimmer (r1: twice too wide). |
| Portraits, painting, Beverly placard | B- / B- / B (r1: B-, B-, B) | better | Stepped gilt frames, recessed canvases, four prints as alternates; an engraved placard (it showed only "THE"). |
| Front desk, key rack | B / B- (r1: B, C) | better | Raised panels with brass beads, plinth, rail; the rack's frame, cornice, hooks and fobs (round 2: the fobs no longer clip the hook below). |
| Grand stairs | B- (r1: B-) | better | Plain veined marble with nosings (the black keystone triangles are gone), rods with finials. The runner's rings are cut at each riser. |
| Cage lift, call plate | B+ / B- (r1: B+, B-) | much better / better | Scissor gate as geometry over the dark shaft; buttons as geometry. The floor dial and the arrow sign are unchanged paint. |
| Modern lift leaves | not in a shot | - | Brushed steel with inset panels as geometry; round 2 warmed the steel a little. Shared with Levels 4 and 11. |
| Boiler bay | C (blind) | same | Not changed (B6's boiler and pipes); see carried. |

**Rounds**
1. **Round 1, blind** (Opus; asked about tone, per-block repetition, the doors and chandelier as geometry, and the boiler):
   - **Tone:** damask, wainscot, frieze and carpets within 1-4 levels of mean; no block-seam grid on wall, wood or carpet at playing distance.
   - **Geometry:** the chandelier "the best change in the batch"; the door body real geometry, its hardware wrong (D): oversized hinges, a stacked-cube knob, a shimmer down both casing sides.
   - **C:** the medallion carpet as a polka-dot grid, the sconce candle too wide, the key fobs clipping, the maroon's coarse noise; and, outside the batch's changes, the boiler bay, the marble pillars, the ceiling light and the lift dial.
2. **Round 2 fixed:** the casing shimmer (z-fighting on the buried sides), slim hinges and a round knob, gold rosettes in the carpet, a slimmer candle, shorter fobs, a calmer maroon, a warmer lift steel. Reshot once; the round-2 grades are my reading of the final frames.

**Carried below B, with reasons**
- **Boiler bay (C):** B6's boiler shell texture (clay-orange at a low density), box flue and large gauge, and the bay's white pipes with painted roundness. They are B6's generators (`boiler_textures`, `gen_shapes.boiler`, the wall pipes), shared with Level 3; left for a pass of their own.
- **Red marble pillars (C; B1 graded them B):** the veins repeat every block upward; `texlib.marble` is shared.
- **Not touched:** the furniture (dining chairs and tables, bed, wardrobe, wing chair, sofa, palm, mahjong table, turntable) and the hotel props (console table, bookshelf, curio, trolley, radiator, writing desk, grandfather clock, piano), except that their mahogany, brass and gilt now have grain; the dome lights; the boiler halls' plaster walls; the floor dial and arrow sign; the marble floor's keystones; the lobby carpet's per-block border.
- **Shared assets that changed elsewhere** (not reshot): `hotelreception` is Level 11's lobby desk; the `liftdoor` leaves are Levels 4's and 11's drywall lifts; `hotelcarpet-damask` and the hotel walls are Level 4's hotel ramp; mahogany, brass, gilt and crystal are on every Level 5 prop.

**Tool changes:** none to shared tools. New in `gen_textures`: `wood_grain`, `brass_metal`, `gilt_leaf`, `layered_pattern`, `PLACARD_FONT` (a 5x7 face for engraved plates); in `gen_shapes`: `four_sides`, `hotel_door`, `slim_hinge`, `door_knob`, `chandelier`; in `gen_detail`: `gilt_frame`, `lift_leaf_panels`, `cage_gate`.

**Lessons:** three lines added above.

### B9

Worker report (Opus, 2026-10-14). Branch `gfx/B9` from `main` (6475351), uncommitted. Phase 1 was offline. Phase 2 was one blind review (round 1), then a fix and one reshoot. The round-2 grades are mine.

- **Final sheets:**
  - `review/b9/compare-round2-6.1.jpg`: every Level 6.1 spot.
  - `review/b9/compare-round2-6.1-detail.jpg`: twelve close spots at twice the size.
  - `review/b9/compare-round2-6.jpg`: Level 6's inspection shots.
  - After shots: `review/b9/final/{6,6.1}`. Round 1: `review/b9/compare-round1-*.jpg`, with its shots in `review/b9/after/`.
- **Per-family pairs:** `review/b9/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B9.json`. That map works on `review/b9/sbs/{before,after}`, where Level 6's shots carry a `6-` prefix. The B9 section is added to `review/compare.html`.
- **Decision table:** twelve rows added to `decisions.md`, decision column empty.
- **Offline evidence** (`review/b9/offline/`):
  - `tile-{1,2,3}-*-{before,after}.png`: surfaces, Level 6 (with `-bright` copies at 2.6x) and the fixtures' materials.
  - `preview-1..6-*.png`: every changed model beside main's.
  - `mock-*-6x3.png`: ten surfaces in the blocktype's real mix, at 4x and averaged.
  - `round2-*.png`, `means.txt`, `zfight-after.txt` and `harness/`.
  - The scratch tools in `tools/` (`mocks_b9.py`, `findspots_b9.py`, `prev.py`, `churn.py`).

**Checks**
- **Build:** 0 warnings, 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir). `build-gfxbase` was built from unchanged `main` before any edit.
- **`layouthash`:** v1 and v4 match B8's output line for line. No C# changed; `DetailBlocks.g.cs` and `lang/en.json` are unchanged.
- **`validatelevel 6`** (`SPAWN=16000`, 24 cells): Level 6 has 2,345 unreachable tiles of 30,933, and the 43 blocked doorways are main's output (no C# changed).
- **Saves:** no code, kind, variant group or class was added, renamed or removed, and there is no layout version. Shot in `gfxreview`.
  - Shapes, texture lists and new texture keys only.
  - `snackshelf` gets a blocktype `textures` entry for `snackpacks` with two alternates.
  - `l6block`, `snackfloor` and `snackceiling` get alternates (ALTS).
- **`check_zfight`:** no same-shape pairs on any changed shape. The neighbour flags left are faces of tall props (splash, flue, shelf posts) in the air block above.
- **Churn:** line endings and the `exitlintel*` key order restored from git.
- **Brightness:** Level 6 is within 0.5 of the new baseline everywhere. Level 6.1 is within 4, except `prop-1`, `checkout-close` and `shelf-close` at +4.5 to +8.8, which is the new chrome and the packs (`review/b9/luma-final.txt`).
- **Textures removed** (no longer referenced): `register`, `foodcase`, `stovetop`, `stovefront`, `fryertop`, `snackshelf`, and the `drinkfridge` orphan.

**Baseline and spots**
- `review/baseline/6` and `/6.1` are reshot on `build-gfxbase`; the B0 sets are kept as `6-b0` and `6.1-b0`.
  - Level 6.1's B0 set was 14-32 levels brighter than today's client (Level 6's inspection shots matched).
  - A retake of five spots first (`review/b9/base-check`) was pixel-identical to the full run.
- **6.1:** the black `gate-*`, `threshold-*` and `sleepingbag-*` spots are gone; those targets are in dark Level 6, outside the sealed cell. Added: `shelf-close` (a store), `checkout-close`, `counter-close`, `booth-close`, `vending-close`, `fridge-close`, `kitchen-close`.
- **6:** added `switch-inspection`, `chalk-inspection`, `tripwire-inspection`, `wet-inspection`. The tripwire spot framed a bare wall at first and was re-spotted before the after run (see the lessons).
- The vending rooms' dead machines and the snack ceiling's stained versions are in no shot; they are judged on the previews.

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Chairs (also Level 11's diner) | B+ (blind r1: B, "A candidate") | much better | A chrome tube frame on glides, a padded navy vinyl seat with a welt, and a padded back on a navy panel. |
| Tables | B (r1: B) | better | A flecked navy laminate top with a chrome edge band, a spider, and an octagonal column, collar and foot. |
| Counters, cash register, store checkout | B / B+ (r1: B, B+) | better / much better | A kick, a cream laminate front, a band and rail, and a stainless top. The register is modelled (drawer, keys, display tower, roll). |
| Pastry case | B (r1: B, "glass not visible") | much better | Chrome frame, deck and shelf, and 18 pastries as boxes. Round 2 gave the glass a lit top edge and short glints. |
| Griddle, fryer | B (r1: B) | much better | Grates, griddle plate, knobs, an oven door with a window, legs, a sunk oil vat, cut-out mesh baskets and a pilot lamp. |
| Store shelves | B (r1: B-, "identical sequence") | much better | A gondola shelf with about 25 packs as geometry. Round 2 gave the pack atlas three arrangements as texture alternates, and shaded the packs. |
| Snack machine | B- (r1: C, header) | better | Coils, keypad, display, coin plate, bill slot and coin return as geometry. Round 2 drew the "SNACKS" sign in a crisp pixel face and shortened the glass streaks. The cabinet is still plain painted blue. |
| Drinks fridge | B- (r1: C, header, rods) | better | A louvred kick and bottle necks. Round 2 gave it a crisp "DRINKS" sign, and short glints in place of the long streaks that read as rods. |
| Dead vending machines | B- (preview only) | better | Dead keypad, display and coin plate as geometry; rusty, grimy paint; a crisp, faded "COLA". |
| Terrazzo | B- (r1: C, "square-looking chips") | same / slightly better | Round 2: mostly 1 px chips in the old four colours, a faint mottle, turned and seamless. |
| Chequered floor | B (r1: B) | better | Off-white and charcoal vinyl tiles with joints. A heel mark and a chip are each one block in eight. |
| Quarry tile | B (r1: B) | better | Unglazed tiles in the old grout; the thick double grout at the block edges is gone. |
| Mall wall | C+ (r1: C) | same | Plaster with the band painted clean; the tone is kept. Carried. |
| Wood panelling | B- (r1: B-) | same | Grained boards. |
| Shop windows | C (r1: C) | same | Frosted panes in brushed aluminium. Carried. |
| Ceiling tiles | B (r1: B) | better | B3's lay-in tile in the old grey and grid, three versions. |
| Skylights | C+ (r1: C, "pure black") | slightly better | Round 2: night-blue glass in place of black. Still a cube. Carried. |
| L6 walls, floor | B- (r1: B-) | better | Cast panels and slabs, means kept. The crack and damp run are one block in eight. |
| L6 ceiling | not judgeable (dark) | - | Slabs; a damp mark one block in six. |
| L6 wet floor | C+ (r1: C, "dashes") | slightly better | Round 2: three versions with soft sheen patches in place of the same dashes in every block. |
| Dead light switch | B (r1: B) | better | Plate, screws, slot and toggle as geometry. |
| Chalk | B (r1: D, lettering lost) | better | Broken, dusty thick strokes with a neutral dust. Round 2 draws EXIT and DEAD END in a crisp chalk face; the logo now reads MEG. |
| Tripwire | B- (r1: B-) | slightly better | Anchor plates, eye bolts and a dark 1 px wire. |

**Rounds**
1. **Round 1, blind** (Opus, asked about tone, repetition and painted geometry):
   - **No change in:** brightness, layout or z-fighting.
   - **Geometry:** the furniture, register, kitchen, case and switch are "solid B".
   - **D:** the chalk lettering (EXIT unreadable, DEAD END gone), from my chalk break-up.
   - **C:**
     - the blurry SNACKS and DRINKS signs (main's, not changed in round 1);
     - the fridge glass streaks, which read as rods;
     - the terrazzo's 2-3 px chips, which read as squares;
     - the wet floor's repeated dashes;
     - the pure-black skylight panes;
     - the flat windows and mint wall.
   - **B-:** the identical pack sequence on every shelf.
2. **Round 2 fixed those, except the windows and wall:**
   - crisp chalk and machine lettering;
   - short glints;
   - finer terrazzo chips;
   - wet-floor versions;
   - night glass in the skylights;
   - pack arrangements as alternates.

   Reshot once. The round-2 grades are my reading of the final frames.

**Carried below B, with reasons**
- **Mall wall (C+):** its rows repeat the same block one above the other, so a scuff band or smudge prints on every row. Grime near the floor needs a skirting block or a per-row variant, which is layout.
- **Shop windows (C):** emissive cubes, which the lights lesson keeps as cubes. A framed, recessed window needs a shape, and a shape loses the glow.
- **Skylights (C+):** the same reason. The panes "show only darkness" by lore, so they stay near black.
- **Wet floor (C+):** small and dark; better, but still faint paint.
- **Not touched:**
  - the rusty, glass and kitchen exit doors and the vent (old cubes; the kitchen door is also Level 11's diner);
  - the neon signs, menu board and mall map (graded B);
  - the drink cans' texture;
  - the ficus and trash can (B7's);
  - the descent stairs (the shared `concretestairs`).
- **Shared assets that changed elsewhere** (not reshot):
  - Level 11's diner uses the chairs, tables, counters, griddle, fryer, fridge, the snack ceiling and the mall wall;
  - Level 11's grocery tills are the register counter;
  - Level 188 places a `snackvending`;
  - chalk marks can be drawn on any level.

**Tool changes:** none to shared tools.
- **New in `deep_textures`:** the B9 section (`level6_b9`, `level61_b9`, `chalky`, `chalk_text`, `machine_header`, `glints`, `snack_packs`, the surface functions).
- **New in `gen_deep`:** `dead_switch`, `tripwire`, `snack_counter`, `cash_register`, `food_case`, `griddle`, `fryer`, `snack_shelf`, `cafe_chair`, `cafe_table`, `vend_keypad`.
- **`gen_detail.ALTS`:** B9 entries.

**Lessons:** five lines added above.

### B10

Worker report (Opus, 2026-10-14). Branch `gfx/B10` from `main` (57a80d2), uncommitted. Phase 1 was offline. Phase 2 was one blind review (round 1), then a fix and one reshoot. The round-2 grades are mine.

- **Final sheets:**
  - `review/b10/compare-round2-7.jpg` and `-7-detail.jpg`: every Level 7 spot, and nine inspection spots at twice the size.
  - `review/b10/compare-round2-8.jpg` and `-8-detail.jpg`: every Level 8 spot, and six close spots at twice the size.
  - After shots: `review/b10/final/{7,8}`. Round 1: `review/b10/compare-round1-*.jpg`, with its shots in `review/b10/after/`.
- **Per-family pairs:** `review/b10/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B10.json`. The map works on `review/b10/sbs/{before,after}`, where shots carry a `7-` or `8-` prefix. The B10 section is added to `review/compare.html`.
- **Decision table:** eight rows added to `decisions.md`, decision column empty.
- **Offline evidence** (`review/b10/offline/`):
  - `tile-{1-l7-rock,2-l7-ceiling,3-tar,4-wood,5-fort,6-l8}-{before,after}.png`, with bright copies of the dark Level 7 surfaces.
  - `mock-*-6x3.png`: the real mix of versions and turns, with seam ratios.
  - `preview-1..11-*.png` (round 1) and `round2-*.png`: every changed model beside main's.
  - `harness/`, and the scratch tools in `tools/`.

**Checks**
- **Build:** 0 warnings, 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir). `build-gfxbase` was built from unchanged `main` before any edit.
- **`layouthash`:** v1 and v4 match B9's output line for line, in rounds 1 and 2. No C# changed; `DetailBlocks.g.cs` and `lang/en.json` are unchanged.
- **`validatelevel 7` and `8`** (`SPAWN=16000`, 24 cells): main's output (no C# changed). Level 7 has one 9-tile pocket; Level 8's run shows Level 9's known pockets.
- **Saves:** no code, kind, variant group or class was added, renamed or removed, and there is no layout version. Only shapes, texture lists and new texture keys changed. Shot in `gfxreview`.
- **`check_zfight`:** no same-shape pairs on any changed shape. The neighbour flags left are the backs of the tall furniture on the block above's south face, as on `main`.
- **Churn:** line endings and the `exitlintel*` key order restored from git.
- **Brightness:** every final shot is within 3.3 levels of the new baseline (`review/b10/luma-final.txt`).
- **Texture keys:** every new key was checked against all generators.
  - New keys: `islandrock-2..4`, `oceanceiling-2/-3`, `tar-2/-3`, `tar-side-2/-3`, `l7wreckboards`, `hotelbookspines`, `hotelbookpages`, `l8lampiron`, `l8lampglass`, `glowcap*rim`, `glowcap*gills`.
  - No longer used by any shape: `books` (detail_textures still writes it).

**Baseline and spots**
- `review/baseline/7` and `/8` are reshot on `build-gfxbase`; the B0 sets are kept as `7-b0` and `8-b0`. They were 8-25 levels brighter than today's client, and the B0 shots predate B4's camp kit. A retake of five spots first (`review/b10/base-check`) matched the full run within 0.3.
- **New spots:**
  - Level 7: `entryroom-inspection`, the room set into the ceiling (its feet y worked out from the layout, and right on the first frame), and `shelter-inside-inspection`.
  - Level 8: `lamp-close`, `meg-close`, `seep-close`.
- **Re-spotted from the base frames:** `shelter-inside-inspection` faced the sea, and `meg-close` framed the marker's back.
- **Not added, with reasons:**
  - The road tar: the 9th Road is vanilla gravel; tar lies in cave pools that the harness grid cannot see.
  - A vein: vanilla ore.
  - A dome door: the domes are rock, with no walls or doors of their own.
  - The waterlogged crate and driftwood: none within reach; judged on the previews.
- **The round-1 after run came out 25-57 levels darker** in every ordinary shot (see the lessons). I retook it in full before the review; that is `review/b10/after`, and the dark run is kept as `after-dark`.

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Island rock, pillars, sea stacks (hero 15) | C+ (blind r1: C) | better | The repeated crack is gone. Seamless faceted basalt in three versions on one ground, plus a featured version one block in eight, turned at random. Round 2 calmed the dark facet that repeated on the stacks and gave each facet a lit lip and a shadowed foot. In the game the facets still read faintly at 1.5 blocks: carried. |
| Tar | B- (r1: C, "matte cube, studs") | better | Seamless versions with bubbles inside the block. Round 2 added a wrapping diagonal sheen that reads as gloss in `shelter-close-inspection`, and took the lit line off the top of the side. Still a cube. |
| Wardrobe | B (r1: D, open back) | much better | Plinth, cornice, raised-panel doors, pulls and escutcheon as geometry. Round 2 closed the back. |
| Bookcase | B (r1: B) | much better | The books are geometry: leaning, gapped, stacked. |
| Side chair, coffee table | B / B (r1: B, B) | better | Rails, crest and back pad; a moulded top, an apron and tapered legs. |
| Wing chair | C+ (r1: C) | better | Legs, skirt, cushion, rolled back and arms. The velvet is one flat fabric: carried (B8's texture). |
| Ceiling over the sea | C+ (r1: C) | better | The dashed stains that sat in every block are gone. Plain soffit concrete, turned and seamless, with features one block in seven. Plain enough to read as a fill: carried. |
| Road lamps | B (r1: B) | better | Modelled post, arm and lantern in old black iron; warm glass with no dark edge. Round 2 removed a scroll that read as a notch in the glass. |
| M.E.G. marker | B (r1: B) | better | Rim, bolts and post cap as geometry; crisp pixel lettering. Round 2 dirtied the plate. |
| Glowcaps | C+ (r1: C, same) | same at distance | Domed caps with a lighter brim, their own gills, round spots and an irregular mycelium patch. At playing distance they look as before: carried. |
| Waterlogged crate, driftwood | B- (preview only) | better | Frame and boards as geometry, wet grain; no painted frame on the log. |
| Almond Water seep, cave stone | C / not seen | same | The seep is not changed (shot for reference); the cave stone is a pale pitted limestone, in no shot. |

**Rounds**
1. **Round 1, blind** (Opus; asked about the rock's repetition, the tar's gloss and seams, and the lamp and furniture as geometry):
   - **No change in:** brightness, lore or layout.
   - **Geometry:** the lamp, marker, bookcase, side chair and coffee table read as geometry (B).
   - **D:** the wardrobe's missing back.
   - **C:**
     - the rock, whose dark blotch per version repeated and which read as mottled, not faceted;
     - the tar ("matte cube", bubbles like studs, a lit line on the side);
     - the glowcaps (flat primaries, a square backing);
     - the wing chair's flat velvet;
     - the plain ceiling.
   - **Minor:** the lamp's notch, a spotless plate.
2. **Round 2 fixed:**
   - the wardrobe's back;
   - the rock's facet spread and bevels;
   - the tar's sheen and side line;
   - the glowcaps' brim and crown, and their mycelium;
   - the lamp's scroll;
   - the plate's grime;
   - the crate's inside.

   Reshot once. The round-2 grades are my reading of the final frames.

**Carried below B, with reasons**
- **Island rock (C+, hero):** it no longer repeats, but the facets need more contrast to read in the game. The next step is joints of about 30 levels spread over many short edges (see the lessons). It was not done here because the batch allows two rounds.
- **Ceiling (C+):** plain concrete keeps the old tone. Board lines would cross at 90 degrees between turned blocks, so structure needs a different, unturned design.
- **Glowcaps (C+):** at range the glow, not the texture, decides how they look.
- **Wing chair (C+):** B8's shared velvet would need seams and piping in a texture of its own.
- **Seeps (C):** not touched. The stain is dithered for the cutout pass.
- **Not mod assets:** Level 8's cave rock and strata, ore veins and halite, the road gravel, the sea and kelp (all vanilla); the domes (rock).
- **Shared assets that changed elsewhere** (not reshot):
  - Level 5's wardrobe, wing chair, side chair, bookcase and coffee table (its rooms and the hotel lobby);
  - Level 8's tar pools;
  - the wet wood (driftwood).

**Tool changes:** none to shared tools.
- **New in `deep_textures`:** the B10 section (`island_rock`, `basalt_facets`, `ocean_ceiling`, `tar_top`, `tar_side`, `wet_wood`, `book_spines`, `meg_plate`, `lamp_iron`, `lamp_glass`, `glowcap_textures`, `cave_stone`).
- **New in `gen_deep`:** `wreck_crate`, `road_post`, `road_arm`, `road_lantern`, `meg_marker`.
- **New in `gen_detail`:** `hotel_bookshelf_b10`, `hotel_chair_b10`, `coffee_table_b10`, and `ALTS`/`TURNED` entries.
- **New in `gen_shapes`:** `wardrobe_b10`, `wing_chair_b10`.

**Lessons:** four lines added above.
