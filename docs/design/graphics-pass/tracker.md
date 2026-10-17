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

- (B12) A window recessed into a solid wall block (`lightAbsorption` 99, drawn as JSON) takes good light in its reveals
  and on its pane; Level 11's façades read with real depth and no dark ring. Two things make it work. The opening must
  leave its open sides to the neighbours (`sideopaqueByType` false on the outside face, up and down, and the ends of a
  ribbon), so the blocks above and below draw the head and sill. And a part that stands proud of the wall (a cornice,
  a string course) must stop short of the block's top plane (y 15.75), so it takes its own light, not the block
  above's.
- (B12) When a `cube_block` kind becomes a JSON model through `drawtypeByType`, remove its `texturesByType` entry: it is
  an `all`, and it paints every part of the model with one texture. Round 1's subway sleepers and rails all showed
  ballast, and were graded D.
- (B12) A floor whose joints are drawn along two edges only (top and left) cannot be turned. A turned block doubles a
  joint or loses one, and the grid goes uneven. Turn only surfaces whose edges are symmetric.
- (B12) A modelled window narrower than the painted one read to the blind reviewer as a change of the buildings' look.
  Keep the old opening's width and the frame's colour and breadth, and add only depth.
- (B12) Two of six client runs came out 45-135 levels darker in every shot (the B10 darkness; the chat log was
  normal). Retakes minutes later were normal. A billboard on a low roof stands behind its parapet from the street, so
  it is shot from the parapet (feet at roof + 2).

- (B13) Texture `alternates` are picked by a hash of the block's x and z only, unless the blocktype says `randomizeAxes:
  "xyz"` (decompiled cube tesselator: `MurmurHash3(x, RandomizeAxes == XYZ ? y : 0, z)`). Without it every block of a
  wall's column shows the same version, so a feature in one version stacks into a vertical line. B13 sets it on Level
  37's tile and Level 94's turf, clay, castle, glass and tank; earlier batches' walls with versions do not have it.
- (B13) Each face picks its own alternate (the same hash, modulo that face's list length), so a cube's top, sides and
  bottom can list different numbers of versions and weights.
- (B13) Compass headings in spot lists: north is -z. A spot meant to face a wall at a larger z looks south (180).
- (B13) Level 94's siren poles are written to the town's plaza corners and then overwritten by the house lots, so none
  stands in a world (layout; the tune still plays from `NearestSirenPole`). Its model is judged on the preview.

- (B14) Level ! is lit only by its EXIT signs, every ~10 blocks, with a 30-block dark stretch in the first hall: a spot
  there is black (B0's prop-1). Find the sign tiles on the harness grid (ceiling `RunExitSign`) and stand within two
  tiles of one, or the asset cannot be graded.
- (B14) A wall decoration placed beside an opening (a lobby's elevator pair ends at an archway) cannot reach past its own
  block: B14's first call-button plate stood beyond the right leaf's jamb and floated in the opening. Put such hardware
  on the block's own frame.
- (B14) A shape that lists another prop's whole texture dict (gen_shapes' Level 5 `t`) changes every shape that shares the
  dict when a key is added to it: give the new prop its own copy (`dict(t, key=...)`).
- (B14) A faceless parent element turned 45 degrees about the trunk (as `officechairtipped` uses for its 90) lets
  children keep a rotation of their own: the palm's diagonal fronds droop as the axis ones do.
- (B14) The texture keys of a far level's generator that its painters save last must be known before its shapes are
  written (`tpath` checks the set of saved keys): gen_run registers its B14 keys in `MINE` up front.

- (B15) `matlib.wood_planks` with `planks=1` still draws the plank's lit top edge and dark gap on the texture's border:
  on a prop face that spans a whole block (a shelf's side panel two blocks tall) that is a dark seam at every block
  height, and the run reads as stacked crates. Clear the border rows (`gen_end.no_edge`).
- (B15) A decoration kind the layout puts on a large share of blocks (The End's ghost mark, 30% of a partition's eye-level
  blocks) is itself a per-block repeat: give it several different marks at different places. Marks under about 10 levels
  vanish in the game's light; 12-15 levels read as faint.
- (B15) Shared-ground versions must share only the broad field: when the ground carried the aggregate too, every Hub
  panel showed the same speckle. Draw each version's own fine structure and blend its broad field with `matlib.turn_safe`.
- (B15) The Hub is lit by monochrome sodium light, which flattens texture changes in its shots; judge its surfaces on the
  offline mocks as well. The Tower's approaches are black at floor level (only the dusk light from the cornice): spot
  them as `-inspection`.
- (B15) Copying a batch's output folder into `review/baseline/<level>` copies its `sheet.jpg` too; rebuild the baseline
  sheet with `batch.make_sheet`. A version dropped from `gen_end` leaves its PNG behind (gen_end does not clear its
  folder, gen_hub does): delete it by hand.

- (B16) A north face shows its texture's left edge at the block's east end (x 16), so a picture split across several boxes
  needs u = (x_right_of_picture - x) / width * 16, not (x - x_left). B0's vending glass, keypad and coin slot were placed as
  if u ran with x and stood over the wrong parts of their own picture; round 1 of B16 repeated the mistake and cut the
  sign to "RINKS". Check a split picture in the preview before the client.
- (B16) The darkness (B6, B10, B12) hit two of six B16 client runs, a full baseline run and a three-spot run, 20-115
  levels down everywhere; retakes minutes later matched B0 within 0.1. Level 188 differs by 5-15 levels in a few spots
  on every run of the same build (its windows change state and its corridor lights flicker at runtime): judge its
  brightness on spots without a window in frame.
- (B16) Tiled stone (marble, slate) is best cut from one large slab that need not tile: draw veins over a 384 px field,
  cut each 15 px tile from a different place, turn it, even its tone toward the stone's, and let the 1 px joints hide
  the edges. Every tile differs and nothing has to meet across a joint. Short branch veins at a fine wavelength read as
  dashes on a dark stone; keep them off it.
- (B16) The far levels' generators check every vanilla code they name against the game's assets: run them with
  `VINTAGE_STORY=G:\Games\Vintagestory` (gen_3999_kit reads that, else %APPDATA%), or the check reports 20 vanilla
  codes as unknown. gen_3999 paints the arcade's textures after the building's, so a painter for an arcade key must hook
  into `gen_3999_tex_arcade.generate`, or the old one overwrites it.

- (D2) A light plate at the foot of a door, in the tone of the wall beside it, reads as a gap under the leaf (the POOL door's kick plate): give foot hardware its own darker tone and take it down to the floor. A kind that the layout places rarely (The End's stained ceiling, one in sixteen) can be made commoner without layout by listing its versions in the plain kind's alternates with a weight.

- (D3) A prop bigger than a block can be one model cut into a block per tile and level (`gen_motion.tower_d3_cells`): unrotated
  parts are clipped at the block edges and given the UV the game would lay on a block there, so their texture runs on
  across blocks; turned parts go whole into the block that holds their middle; a cone's plates are a parent turned about
  the axis carrying a child tilted about x (B14). `check_zfight` per shape misses pairs across blocks: also check the
  whole model put back together (D3's scratch `d3_combine.py`).
- (D3) A white matched to a neutral mean (235, 235, 231) read grey beside the cream houses and ivory legs in Level 94's
  light, and was graded C+; Level 94's whites want a warm mean (236, 233, 222). Rust speckle at rivets read as a realistic
  steel tower, not a clay prop: runs only.
- (D3) Level 94's water tower tiles carry their place in the tower in `Stack`, already as the world runs: a hill lot laid
  out mirrored north to south mirrors the rows back (`PlanHill`). The siren poles (B13's lesson) stand from layout
  version 8.
- (D3) The user's game can open between a batch's build and its shooting: check `tasklist` right before `batch.py`, and
  wait for it to close (never end it).

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
| B12 Level 11 | gfx/B12 | merged | 2 | mirror glass (lore), roofs C+, asphalt C+, traffic-light fronts unseen, lobby marble C+; shelter, dumpster, booth, cart, bench, doors untouched | passed 2026-10-15 00:40 (Fable): façade windows and bands verified as geometry at the old look |
| B13 Levels 37 and 94 | gfx/B13 | merged | 2 | L94 asphalt and dirt path C+; siren pole stands in no world (layout bug, report to user); earlier batches' walls lack randomizeAxes xyz (follow-up) | passed 2026-10-15 01:55 (Fable): turf swirl gone, mosaic at B |
| B14 Level ! and Fun | gfx/B14 | merged | 2 | L! walls and Fun paint plain (C+); gurney, wheelchair, IV, collapse untouched; Fun brass leaves C+; balloons and streamers untouched; fire doors unseen | passed 2026-10-15 03:15 (Fable): bed, doors, cart as geometry; floor seam gone |
| B15 The End and The Hub | gfx/B15 | merged | 2 | End walls/carpet and Hub concrete/road/carved leaves C+ (plain by nature); End furniture, escalator, Hub pink door, outpost, statue untouched; ornate ring pulls | passed 2026-10-15 04:40 (Fable): repeats gone, EXIT door hardware verified |
| B16 974, 3999, 188 | gfx/B16 | merged | 2 | 3999 paint, 974 ceiling and furniture bodies (C+); food court furniture at distance and 188 blinds (B-, runtime) | passed 2026-10-16 06:30 (Fable): marble repeat gone, furniture as geometry |
| D2 follow-up on B13, B14, B15 decisions (POOL door, Fun chair back, End ceiling stains, Hub worn asphalt) | gfx/D2 | merged | offline only | | | passed 2026-10-16 (Fable): door foot and lettering verified on previews; built into 0.514.0 test zip |
| D3 Level 94 follow-up (yellow houses, siren poles, water towers) | gfx/D3 | merged | 2 | siren pole speakers C+ (B13's model, not in scope); castle glass at the mountain's foot (B13, unchanged); layout version 8 | | passed 2026-10-17 00:15 (Fable): tower matches the lore photo in game; houses yellow; poles stand |
| B17 entities and items | gfx/B17 | in progress | | | |
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

### B12

Worker report (Opus, 2026-10-15). Branch `gfx/B12` from `main` (16c5f56), uncommitted. Phase 1 was offline. Phase 2 was one blind review (round 1), then fixes and one reshoot. After the reshoot, one more fix (the pavers stopped turning, the gravel calmed) was checked by retaking the six spots it touches. The round-2 grades are mine.

- **Final sheets:**
  - `review/b12/compare-round2.jpg`: every spot.
  - `review/b12/compare-round2-detail-a.jpg`: the façades at twice the size.
  - `review/b12/compare-round2-detail-b.jpg`: roofs, props, asphalt, floors, the subway and the diner at twice the size.
  - Shots: `review/b12/final`. Six of them (close-floor, threshold-wide, bench-close, billboard-roof-close, billboard-roof-wide, wide-01) come from the retake in `review/b12/final-fix`; the round-2 run as shot is kept in `final-r2`.
  - Round 1: `review/b12/compare-round1*.jpg`, with its shots in `review/b12/after/`.
- **Per-family pairs:** `review/b12/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B12.json`. The B12 section is added to `review/compare.html`.
- **Decision table:** twelve rows added to `decisions.md`, decision column empty. Each row says how to revert its family: every B12 painter runs after the old one under the same keys, so dropping one call from `gen_city.generate_textures` reverts that family's textures.
- **Offline evidence** (`review/b12/offline/`):
  - `tex-*-{before,after}.png`: texsheets of the façades, streets, subway and props.
  - `tex-round2.png`
  - `preview-facades*.png`: a stretch of each façade style, main beside the tree.
  - `preview-props.png`, `preview-tall.png`, `preview-heads.png`: the tracks, lamp, traffic light and street light.
  - `pair*-*.jpg`: in-game before and after pairs, stacked.
  - `harness/`
  - The scratch tools in `tools/`: `findspots_b12.py`, `map_at.py`, `depthmap.py`, `billboards.py`, `facade_scene.py`, `heads.py`, `addspots_b12.py`, `churn.py`, `docs_b12.py`, `tracker_b12.py`.

**Checks**
- **Build:** 0 warnings and 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir). `build-gfxbase` was built from unchanged `main` before any edit.
- **`layouthash`:** v1 and v4 are unchanged against main's output, line for line, in both rounds. No C# changed; `DetailBlocks.g.cs` and `lang/en.json` are unchanged.
- **`validatelevel 11`** (24 cells): no doorways to nowhere, no bad elevators, and no decor facing walls. One doorway is blocked by a prop. That is main's output, since no C# changed.
- **Saves:** no code, kind, variant group or class was added, renamed or removed, and there is no layout version. The changes are shapes, texture lists, new texture keys, `drawtypeByType`, `shapeByType` and `sideopaqueByType`. `cityfacade`'s brick, limestone and concrete windows and its brick and limestone bands now draw as JSON, as do `subwayfloor`'s two track kinds. Everything was shot in `gfxreview`, with no new world.
- **`check_zfight`:** no same-shape pairs on any new or changed shape. The neighbour flags left are the cornice and string-course ends and the sleeper ends, in the air in front of or above their block.
- **Churn:** line endings and the `exitlintel*` key order were restored from git. The full regeneration leaves every other generator's output byte-identical.
- **Brightness:** every final shot is within 6.3 levels of the new baseline (`review/b12/luma-final.txt`). The largest drops, -6.3 on facade-stone-close and -4.3 on facade-brick-close, are the window reveals' shade.
- **Texture keys:** every new key was checked against all generators.
  - New keys: `citypane-*`, `cityframe-*`, `citycornice`, `cityroof-2/-3`, `cityfloor-plaza-2/-3`, `cityfloor-marble-2/-3`, `facade-{brick,brickdark,stone,concrete}-wall-2/-3`, `facade-glass-window-2/-3`, `subwaywall-tile-2..4`, `subwaysleeper`, `subwayrail`, `subwayrailtop`, `billboard-*-2`.
  - Old keys the models no longer use (still written): `facade-{brick,brickdark,stone,concrete}-{window,lit,blinds}`.
  - Shared paint that changed with the same mean: `trafficyellow` (also Level 94's prop sides, `gen_motion`) and `streetgreen` (also Level 9's sign poles).

**Baseline and spots**
- `review/baseline/11` was reshot on `build-gfxbase`; the B0 set is kept in `review/baseline/11-b0`.
  - A retake of three spots first (`review/b12/base-check`) matched B0 within 2.
  - The first full baseline run came out dark everywhere (kept in `review/b12/baseline-dark`). The second matched B0 within 2.5.
- **Re-spotted:** `refuge-wide`/`-close` were black. The refuge is inside a dark apartment, so they are now `-inspection` shots.
- **Added** (`review/spots/11.json` and the docs copy), all found on the harness grid:
  - a close-up of each façade style: `facade-brick-close`, `-brickdark-`, `-stone-`, `-concrete-`, `-glass-`, `-mirror-`;
  - the diner: `shopfront-close`, `diner-inside`;
  - the billboard from the substation's parapet: `billboard-roof-close`, `-wide`;
  - `streetlight-close`, `bench-close` and `asphalt-close`;
  - the subway: `subway-wide`, `-close`, `-tracks`.
- **Moved after the first base frames:** `streetlight-close` and `subway-close`.
- **Not added:**
  - The mirror rim is at the city's edge, far from every spot. It shares `pier-mirror` with the towers' corners, which are in `facade-mirror-close`.
  - There are no turnstiles in the layout.
- The old `billboard-wide`/`-close` frame the substation's brick front. Its billboard stands behind the parapet from the street.

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| Brick façades (red, dark) | B (blind r1: B, B) | better | Bricks at the old units are shaded and in three versions. The sash windows are modelled: set back in brick reveals, with broad cream or green frames and a meeting rail. Round 2 restored the old width, after round 1's narrow slots read as a new look. The stone string course projects. |
| Limestone façades | B (r1: B-) | better | Shaded ashlar in three versions; rusticated piers; windows set 2.5 units deep in pairs with bronze frames (round 2 widened them); the cornice is a crown and a dentil course as geometry. |
| Concrete façades | B- (r1: C, a tie-hole grid) | better | Board-marked concrete. Round 2 removed the tie-hole grid; one hole is left, with a rust run, in one version in seven. The ribbon windows are geometry, and the lit ones show an office. |
| Curtain glass, columns | B (r1: B) | better | The reflections vary across three versions under a shaded mullion and transom; the columns are brushed aluminium. The lit and blinds panes are still the same in every block. |
| Mirror towers, rim | C (r1: C) | same | The panes are unchanged (lore). The corners and rim are black glass in a faint grid. Carried. |
| Storefront fascia | B- (r1: C, a mark per panel) | slightly better | A painted board with a raised gilt bead. Round 2 removed the worn spot that printed in every panel. The green field is still plain paint. |
| Roofs | C+ (r1: C) | same / slightly better | Shaded pebbles over tar, turned at random. Round 2 calmed them. Still no seams or flashing: carried. |
| Billboard | B- (r1: D, the peeled corner) | better | Weathered frame, poster sheets, crisp small type, the city slogan redrawn. Round 2's second version is the same poster a summer older. The middle lamp hides part of the slogan from the parapet, as on main. |
| Advertising pillar | B (r1: B) | better | Crisp poster type and painted green. The cap is unchanged. |
| Traffic lights | C+ (r1: C, provisional) | slightly better | A back plate and hoods as geometry, and lenses without a black square. Only their backs and sides are in a shot. |
| Street light | B- (r1: B-) | better | Stepped base with a door, collar, cap and brace; a cobra head with a skirt round a flush lens (`gen_deep`, shared with Level 9). |
| Street props' faces and paint | B- / C | better (faces) | Newsbox, mailbox, meter, phone, cart and street-sign faces are in a pixel face. The paint is worn metal. The props are still the old boxes. |
| Cracked asphalt, markings | C+ (r1: C) | better | The square patch is gone. A soft patch and cracks are now one cracked block in seven. The markings take the road's grain. The road itself is B7's. |
| Plaza pavers | B- (r1: C, speckle) | same / slightly better | Shaded pavers with their own hue, in three versions. Round 2 calmed the speckle and stopped turning them (it doubled joints). |
| Lobby marble | C+ | slightly better | Three cuts, so the same scribble is no longer in every block. Still the old veining style. |
| Subway walls, sign, ad, lamps | B (r1: B) | better | Glazed tiles with grime one block in eight; a crisp station name; lamps caged with real bars. |
| Subway platform and edge | B- (r1: B-, C) | better | Concrete platform. Round 2 raised the tactile domes. |
| Subway tracks | B (r1: D, the texture bug) | much better | Timber sleepers and rails with a bright head as geometry. Round 1's blocktype `all` texture painted them as ballast. |
| Diner | B (r1: B) | same | B9's fixtures; not changed. |

**Rounds**
1. **Round 1, blind** (Opus; given only the sheets, texsheets, previews and the rubric):
   - **No change in:** brightness, z-fighting, holes (apart from the billboard corner) or layout.
   - **Geometry:** the windows and cornices were seen as real geometry. The narrower openings were called a change of look.
   - **D:**
     - the subway tracks: sleepers and rails painted with the ballast (my texture bug);
     - the billboard's peeled corner, which read as a missing chunk.
   - **C:**
     - the plaza speckle;
     - the flat tactile strip;
     - a new square mark in every fascia panel;
     - the concrete tie-hole grid;
     - the roofs, the plain road and the mirror glass.
2. **Round 2 fixed:**
   - the track textures;
   - the billboard's second version and slogan;
   - the window widths and frames;
   - the fascia mark;
   - the tie holes;
   - the domes;
   - the plaza speckle;
   - the brick tones (a little less orange, the dark brick warmer);
   - the overflowing stencils.

   I reshot once. Then the pavers' doubled joints, seen in the round-2 frames, were fixed (not turned) and the gravel calmed, and those six spots were retaken. The retake's first run was dark (`review/b12/final-fix-dark`), the second normal.

**Carried below B, with reasons**
- **Mirror glass (C):** the lore's plain black panes (visual-review.md); only the corners and rim changed.
- **Roofs (C+):** pebbles with no seams or flashing. Roofs are seen mostly from the parapet spots.
- **Asphalt (C+):** B7's road, judged plain by the reviewer. B12 changed only the cracked floor's mix and the markings.
- **Traffic lights (C+):** no spot shows their front. The yellow housing is painted metal over the old boxes.
- **Lobby marble (C+):** `texlib.marble`'s worm-like veins. Three cuts now, but the same style.
- **Not touched:**
  - the bus shelter, dumpster, phone booth and vendor cart models (their faces and paint changed);
  - the bench and trash can (gen_detail, shared);
  - the stained glass;
  - the row-house and steel doors, which are still cubes (only their paint and stencils changed);
  - the cinema;
  - the water tanks and AC units (paint only);
  - the mirror rim, which is in no shot.
- The maintenance door's stencil now reads STAFF ONLY. AUTHORIZED PERSONNEL does not fit a block in crisp type.

**Tool changes:** none to shared tools.
- **New in `gen_city`:** the B12 section:
  - `OLD_MEAN`, `matched`, the pixel faces `CITY_F5`/`CITY_F3` with `ptext`/`ptext_c`, `painted_board`;
  - the painters `b12_brick`, `b12_glass`, `b12_windows`, `b12_stone`, `b12_concrete`, `b12_fascia_roof_plaster`, `b12_streets`, `b12_subway`, `b12_props`, `b12_posters`, `b12_doors`;
  - the models `wbox` (world-aligned UVs), `window_shape`, `band_shape`, `WALL_ALTS`;
  - the track and lamp models;
  - the `asphalt.json` cracked mix.
- **`gen_deep.streetlight`:** the new model (B11's generator; shared with Level 9).
- **`gen_detail.TURNED`/`ALTS`:** entries are added from `gen_city.facades` for the roofs, pavers, marble and subway tiles.

**Lessons:** five lines added above.

### B13

Worker report (Opus, 2026-10-15). Branch `gfx/B13` from `main` (94ff2b5), uncommitted. Phase 1 was offline. Phase 2 was one blind review (round 1), then fixes and one reshoot. The round-2 grades are mine.

- **Final sheets:**
  - `review/b13/compare-round2-37.jpg` and `review/b13/compare-round2-94.jpg`: every spot.
  - `review/b13/compare-round2-37-detail.jpg` and `-94-detail.jpg`: the close spots at twice the size.
  - Shots: `review/b13/final/{37,94}`. Round 1: `review/b13/compare-round1-*.jpg`, with its shots in `review/b13/after/`.
- **Per-family pairs:** `review/b13/sidebyside/<family>.jpg`, from `docs/design/graphics-pass/sidebyside/B13.json` (it works on `review/b13/sbs/{before,after}`, where shots carry a `37-` or `94-` prefix). The B13 section is added to `review/compare.html`.
- **Decision table:** eleven rows added to `decisions.md`, decision column empty. Every B13 painter runs after the old one under the same keys (`gen_pool.b13_textures`, `gen_motion.b13_textures`), and each model is one `*_b13` function, so a family reverts by dropping its call.
- **Offline evidence** (`review/b13/offline/`):
  - `tex-{pool,ground,motion-props}-{before,after}.png`, `tex-round2.png`: texsheets, tiled 3x3, with vanilla references.
  - `mock-*-6x3.png`: the mosaic, red tile, coping, turf tops and sides, clay, asphalt, kerb, path and concrete in their real mix of versions and turns, main above B13, with seam ratios (turf top 1.33 on main, 1.09 now; path 2.31 on main, 1.14 now).
  - `preview-pool-*.png`, `preview-motion-*.png`, `preview-round2.png`: every changed model beside main's.
  - `zoom-mosaic.png`, `crop-*.png`, `harness/`, and the scratch tools in `tools/` (`enums.py`, `explore.py`, `map_at.py`, `query.py`, `findspots_b13.py`, `addspots_b13.py`, `mocks_b13.py`, `churn.py`, `luma.py`, `prev.py`, `docs_b13.py`, `tracker_b13.py`).

**Checks**
- **Build:** 0 warnings and 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir). `build-gfxbase` was built from unchanged `main` before any edit. No C# changed.
- **`layouthash`:** v1 and v4 unchanged against main's output, line for line, in both rounds (`review/b13/offline/harness`).
- **`validatelevel 12` and `13`** (Levels 37 and 94, `SPAWN=16000`, 24 cells): main's output, since no C# changed. Level 37: no faults. Level 94: four doorways blocked by props, as on main.
- **Saves:** no code, kind, variant group or class was added, renamed or removed, and there is no layout version. The changes are textures, new texture keys and versions, shapes, `alternates`, `randomizeAxes` and one `drawtype`: `pooldoor` (lower and upper) now draws a model and stays a full solid block (`sideopaque` and `sidesolid` true, `lightAbsorption` 99, the same threshold behaviour). Shot in `gfxreview`; no new world was needed.
- **`check_zfight`:** no same-shape pairs on any new or changed shape (round 1's milk van bumpers were fixed). The neighbour flags left are the wheels' outer faces (as on main), the handrail's ends where it runs on into the next block, and the door stiles' tops where the upper half continues them.
- **Churn:** line endings and the `exitlintel*` key order restored from git after every regeneration; nothing outside the two generators' output changed.
- **Brightness:** every final shot is within 2.6 levels of the new baseline except `94-castle-wall-wide` (-8.9: the glass no longer draws a bright outline round every block) and `94-castle-close` (+4.8, far, outdoor sway) (`review/b13/luma-final.txt`).
- **Texture keys:** every new key was checked against all generators and `git ls-files`.
  - New keys: `pooltile-2/-3`, `poolsunlit-2/-3`, `poolred-2/-3`, `poolcoping-2`, `poolsteel`, `pooltread`, `poolporthole`; `clayturf-{light,dark}-2/-3`, `clayturf-side-{light,dark}-2..4`, `claysoil-2/-3`, `motion{path,concrete,asphalt,kerb}-2/-3`, `castlewall-2/-3`, `castleroof-2/-3`, `towertank-2/-3`, `glassmountain-2..4`, `fountaincap`, `fountainwater`, `iceboxenamel`, `iceboxdoor`, `radiowalnut`, `radiocloth`, `radiodial`, `milkvangrille`.
  - No longer used by any shape (still written): `icebox-front`, `radio-front`.
  - `milkvan-side` is now 112 x 40 (on the 8 px grid), so its letters stay square on the van's side.

**Baseline and spots**
- `review/baseline/37` and `/94` were reshot on `build-gfxbase`; the B0 sets are kept as `37-b0` and `94-b0`. A retake of three spots per level first (`review/b13/base-check`) matched the full run within 3. Against B0, Level 37's wide shots drift 7-15 levels either way (water and fog), the close ones within 3; Level 94 matches within 1 except the castle on the horizon.
- **Added** (`review/spots/37.json`, `94.json` and the docs copies; found on the harness grid with the scratch tools):
  - Level 37: `slit-close`, `mosaic-close` (the deck and wall foot between slits), `rail-close`, `pooldoor-close`.
  - Level 94: `turf-close`, `watertower-wide`, `watertower-close`, `fountain-close`, `milkvan-close`, `road-close`, `house-close`, `castle-wall-close`, `castle-wall-wide`, `icebox-close`, `radio-close`.
- **Re-aimed after the base frames:** `castle-wall-close` faced away from the castle (north is -z); it now looks south at the wall.
- **Not added:** a siren pole (none stands in a world: see the lessons), the telephone table (no clear view), the Reservoir's red tile (not near the anchor). The house front is Level 9's (B11) and is shot for context only.
- No run came out dark.

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| L94 turf tops (hero 27, 28) | B (blind r1: B) | better | The repeating swirl is gone. Smooth plasticine in the old greens covered in small pressed tool strokes at every angle, and a few thumb drags (round 2). Three versions on one ground, turned at random; seam ratio 1.09. |
| L94 turf sides | B- (r1: C) | better | No swirl on every block. A lit rounded lip, strokes running up, a slight bulge and a darker foot. Round 2 removed the clay line at the foot (it read as a line on every step), added thumb drags, and made the thumbprint version (one block in eight) fainter. |
| L94 clay | B- (r1: B-) | better | Small partial thumbprints, smears and lumps; three versions turned. |
| L94 asphalt | C+ (r1: C) | better | Smooth dark clay with a fine grit; no swirl. A faint crack in one version listed one block in seven (round 2 dropped a square patch: square marks read badly). Still plain: carried. |
| L94 kerbs, concrete paths, plaza | B (r1: B) | better | One slab to a block with a sunk joint on all sides; the kerb's arris rounded; round 2 removed the faint trowel arcs. |
| L94 dirt path | C+ (r1: C+) | better | Clay pebbles and smears; round 2 thinned the pebbles. |
| L94 castle wall | B (r1: B) | better | Shaded white ashlar at the old courses, three versions by tone; round 2 removed the pits that sat in every stone. Glow kept. |
| L94 castle roofs | B- (r1: C, small bricks) | better | Round 2: clay tiles 8 x 8 breaking joint, rounded tails, a lit lip and the overlap's shadow, at the old red mean (the red is the lore's). Glow kept. |
| L94 glass mountain | B (r1: B) | better | No outline round every block; a short soft glint in two versions of four. |
| L94 water tower | B+ (r1: B+) | better | Riveted white tank, painted steel legs with a foot flange and band. |
| L94 fountain | B (r1: B) | better | A capped cast-stone rim; a moulded spout with an octagonal shaft and a bowl of Almond Water. |
| L94 icebox, radio, telephone | B+ / B+ / B (preview) (r1: B+, B+) | much better | Doors, latches, hinges, grille, dial and knobs as geometry; the painted fronts are retired. |
| L94 milk van, old cars' wheels | B (r1: B) | better | Octagonal wheels under mudguards, chrome grille and round lamps, cab windows, a square-pixel livery. |
| L94 siren pole, NO OUTLET sign | B- (preview) | better | Flared horns; crisp sign letters. The pole stands in no world. |
| L37 mosaic, sunlit, coping (hero 25, 26) | B (r1: B-) | better | The same white 64 px mosaic and pale grout, now each tile a hair different, glazed at its edges with a glint, the grout recessed and (round 2) a step darker; three versions on one ground, picked by height too. Crazing in about one tile in twelve; nothing chipped (the lore's tile is pristine). The coping is a larger bullnose tile, not a painted frame per block. |
| L37 red film tile | B- (offline only) | better | The film in the grout, heavier along some joints; the blotch that sat in every block is gone. Not in a shot. |
| L37 POOL door | B (r1: C) | much better | A model on the old codes: stiles, an octagonal stainless porthole ring over one pane, push and kick plates, on all four sides 0.05 short of the block's edges. Round 2 replaced the plus-shaped glass, removed stray chips and moved POOL above the porthole, where the push plate no longer covers it. |
| L37 handrail, ladder | B / B (r1: B, B) | better | Round rail on arms from roses (round 2 hid the roses' points behind the rail); round ladder rails on stays, ribbed treads with a nosing. |
| L37 Epsom crust, lost things | B (preview; r1: B) | better | Crystal crust in sheets with lumps; a folded towel, V-strap flip-flops, a round noodle. Too dark to judge in game. |
| L37 slit, arch glow | B | same | Not changed: lights stay cubes. |

**Rounds**
1. **Round 1, blind** (Opus; given only the sheets, texsheets, mocks, previews and the rubric; asked whether the turf still repeats, whether the mosaic reads as tile, and about the door, rail and ladder):
   - **No change in:** layout or brightness.
   - **Turf:** no frame shows the swirl repeating any more; the tops are seamless. The sides read as streak noise, the thumbprint version was visible, and a thin line ran along every step.
   - **C:** the door's plus-shaped porthole glass and two chips; the turf sides; the asphalt (plain); the castle roof (small bricks, saturated); the path's pebble rhythm.
   - **Mosaic:** clean tile with no repeat, but too flat to read as glazed ceramic.
   - **Minor:** the rail's rose points above the rail, a dot in every castle stone, the kerb's faint arcs.
2. **Round 2 fixed:** the porthole (one pane under a broader ring), the door's chips and lettering; the turf sides (no foot line, thumb drags, a slight bulge, a fainter thumbprint) and thumb drags on the tops; the mosaic's glaze and grout; the castle roof as tiles; the stone pits; the rail's roses; the kerb's arcs; the asphalt's speckle (and a square patch tried and dropped). Reshot once.

**Carried below B, with reasons**
- **Asphalt (C+):** plain clay asphalt by design of the level; the reviewer wanted wear (tracks, patches). Square patches read as square marks (`decisions.md`), so only a faint crack was added.
- **Dirt path (C+):** short paths from house to road; pebbles and smears only.
- **Not touched:** the houses (Level 9's, B11), the bed and nightstands (Level 9's), the castle's funhouse inside (no shot), the backdrop, the doll's and flooded houses' doors, the picket fence (B), the slit and arch glow (lights stay cubes), the item icons (B17).
- **Layout, reported not changed:** Level 94's siren poles are overwritten by the town's house lots, so none stands in a world.

**Tool changes:** none to shared tools.
- **New in `gen_pool`:** the B13 section: `POOL_MEAN`, `mosaic_b13`, `b13_mosaic`, `b13_chrome`, `b13_door`, `b13_lost`, `b13_textures`; the models `octo_bar`, `rail_b13`, `ladder_b13`, `pool_door_b13`, `pool_door_block_b13`, `epsom_b13`, `lost_b13`; `gen_detail.ALTS` entries for the tile versions.
- **New in `gen_motion`:** the B13 section: `MOTION_MEAN`, `stroke`, `arcs`, `smear`, `clay_ground`, the painters `turf_top_b13`, `turf_side_b13`, `clay_b13`, `path_b13`, `asphalt_b13`, `slab_b13`, `castle_b13`, `roof_b13`, `tower_b13`, `fountain_tex_b13`, `glass_b13`, `furniture_tex_b13`, `van_tex_b13`, `nooutlet_b13`, `b13_textures`, `alts`, `tex_entry`; the models `octo_wheel`, `milkvan_b13`, `oldcar_wheels_b13`, `sirenpole_b13`, `icebox_b13`, `radio_b13`, `phone_b13`, `fountain_b13`, `towerleg_b13`; `gen_detail.TURNED`/`ALTS` entries for the roads and the castle.

**Lessons:** four lines added above.

### B14

Worker report (Opus, 2026-10-15). Branch `gfx/B14` from `main` (82b4613), uncommitted. Phase 1 was offline. Phase 2 was one blind review (round 1), then fixes and one reshoot. The round-2 grades are mine.

- **Final sheets:**
  - `review/b14/compare-round2-run.jpg` and `review/b14/compare-round2-fun.jpg`: every spot.
  - `review/b14/compare-round2-run-detail.jpg` and `-fun-detail.jpg`: the close spots at twice the size.
  - Shots: `review/b14/final/{run,fun}`. Round 1: `review/b14/compare-round1-*.jpg`, with its shots in `review/b14/after/`.
- **Per-family pairs:** `review/b14/sidebyside/<family>.jpg` (18 families), from `docs/design/graphics-pass/sidebyside/B14.json` (it reads `review/b14/sbs/{before,after}`, where shots carry a `run-` or `fun-` prefix). The B14 section is added to `review/compare.html`.
- **Decision table:** eighteen rows added to `decisions.md`, decision column empty. The textures are B14 painters that run after the old ones under the same keys (`gen_run.b14_textures`, `gen_fun.b14_textures`), so a family reverts by dropping its call; each row names its functions.
- **Offline evidence** (`review/b14/offline/`):
  - `tex-{run,fun}-{surf,props}-{before,after}.png`: texsheets, the surfaces tiled 3x3, with vanilla references.
  - `mock-*-6x3.png`: the run vinyl, wall, wall foot and ceiling, and Fun's cream wall, vinyl tiles, painted wall foot and carpets in their real mix of versions and turns, main above B14, with seam ratios (run vinyl 2.05 on main, 0.96 now).
  - `preview-run-{1,2,3}.png`, `preview-bed*.png`, `preview-palm.png`, `preview-fun-{1,2}.png`: the changed models beside main's.
  - `notices.png`, `fun-signs.png`, `poster.png`, `round2-tex.png`, `crop-*.jpg`, `harness/`, `main/` (main's textures and shapes), `spots-{run,fun}-before.json`.
  - The scratch tools in `tools/`: `addspots_b14.py`, `near_sign.py`, `explore.py`, `map_at.py`, `query.py`, `enums.py`, `patch_*.py`, `insert_run.py`, `mocks_b14.py`, `sheets_b14.py`, `prev.py`, `luma.py`, `churn.py`, `docs_b14.py`, `tracker_b14.py`.

**Checks**
- **Build:** 0 warnings and 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir, both rounds). `build-gfxbase` was built from unchanged `main` before any edit. No C# changed.
- **`layouthash`:** v1 and v4 unchanged against main's output, line for line, in both rounds (`review/b14/offline/harness`).
- **`validatelevel 14` and `15`** (Levels ! and Fun, `SPAWN=16000`, 24 cells): no doorways to nowhere, none blocked, no bad elevators, no decor facing walls (main's output: no C# changed).
- **Saves:** no code, kind, variant group or class was added, renamed or removed, and there is no layout version. The changes are textures, new texture keys and versions, shapes, `alternates` and `randomizeAxes`. Shot in `gfxreview`; no new world was needed.
- **`check_zfight`:** no new same-shape pairs (Level ! 8 and Level Fun 34 before and after, all in unchanged models: the chained door's padlock, the wheelchair's feet, the exit door's jambs, Fun's old props). The bed and the palm are clean.
- **Churn:** line endings, `lang/en.json` and the `exitlintel*` key order restored from git after every regeneration (`churn.py`); gen_detail, gen_textures and gen_shapes left every other output byte-identical (gen_shapes' first palm run also rewrote four Level 5 shapes' texture lists: fixed, see the lessons).
- **Brightness:** every final shot is within 0.3 levels of the new baseline on Level ! and within 4 on Level Fun (`review/b14/luma-final.txt`), except `funparty-close` (-11: a different party-goer stands in front of the camera each run; spawned entities vary).
- **Texture keys:** every new key was checked against all generators and `git ls-files`. Level ! and Fun keys live in their own folders (`block/run/`, `block/fun/`).
  - New in `block/run/`: `wall-2..4`, `wallbase-2..4`, `safewall-2..4`, `safewallbase-2..4`, `vinyl-2/-3`, `border-<side>-2`, `scuffed-2`, `cracked-2`, `ceiltile-2/-3`, `railunder`, `exitlip`, `runbead`, `cartdrawer`, `cartlabel`, `defibscreen`, `cabmirror`, `cablabel`, `dispensergel`.
  - New in `block/fun/`: `paint-<colour>-2/-3`, `paint-<colour>-low-2..4`, `promwall-2/-3`, `confetti-2/-3`, `liftdialface`, `liftneedle`, `liftbutton`, `liftplate`, `speakercloth`, `speakercone`.
  - New shared: `block/detail/hospbed-*` (9), `block/level5/palmtrunk`, `potsoil`.
  - No longer used by any shape (still written): run `cartfront`; Fun `liftdial` (`grille` is still the blower's).

**Baseline and spots**
- `review/baseline/run` and `/fun` were reshot on `build-gfxbase`; the B0 sets are kept as `run-b0` and `fun-b0`. A retake of five spots first (`review/b14/base-check`) matched B0 within 1; the full run matched within 1 (Fun's wide shots within 1.5). No run came out dark.
- **Re-spotted** (B0's black frames): `wide-07` (the x 511824 hall past the collapse and gurneys), `prop-1` (a barricade under the sign at 736), `prop-2` (the collapsed ceiling under the sign at 744).
- **Added** (`review/spots/run.json`, `fun.json` and the docs copies; found on the harness grid with the scratch tools):
  - Level !: `bed-close`, `startdoor-wide` (the start room's door wall: the hall door, the hand-washing notice, the dispenser), `notice-close`, `sanitiser-close`, `rail-close`, `exit-close`, `wheelchair-close`, `ivstand-close`, `gurney-close`.
  - Level Fun: `elevator-close`, `elevator-wide` (the lobby's string lights, confetti, floor balloons), `lobbyfloor-close`, `party-ceiling` (the balloon cluster and streamers), `poster-close`, `directory-close`, `palm-close`, `speaker-close`.
- **Re-aimed after the base frames:** `rail-close` (its first place was black), `bed-close` (closer), `sanitiser-close`, `directory-close`, `palm-close`, `speaker-close` (narrower fields of view).
- **Not added:** the fire doors (the true and fake exits are far from the anchor in the dark); the crash cart (one in the area, in the dark).

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| L! hospital walls, cove base (hero 29, 30) | C+ (blind r1: C) | better | Paint over plaster in the old tone, four versions on one ground (`randomizeAxes: xyz`); the dash scuffs that printed on every foot block are gone; a 3 px cove with a lit roll, a soft dirt gradient, soft scuffs in two versions of eight. A hospital wall is plain: the reviewer called it pristine. |
| L! vinyl floor, border, scuffed, cracked (hero 29) | B- (r1: C) | better | The per-block seam is gone (seam 2.05 to 0.96); chips of two sizes and four tones in a calm ground, three versions turned; the border an inlay with a groove. Round 2: scuffed and cracked have two versions each, turned. |
| L! ceiling tiles | B- (r1: B-) | better | `matlib.ceiling_tile` at 16 px, four to a block in the T-bar, three versions, a stain in one block in six. |
| L! crash rail | B- (r1: B-) | better | Oak along its length with a round shading, a lit top roll, a dark underside, wall plates. Round 2 calmed the grain flecks that sat in the same place on every block. |
| L! steel side doors (hero 29) | B (r1: B) | better | The painted window is an opening with a wired-glass pane in a bead; the kick plate a plate; worn paint, raised outer edges; the flung leaf the same. |
| L! hall door | B- (r1: B-) | better | A flush wood leaf with its vision panel set in; round 2 calmed the grain (r1 read as barn planks). |
| L! fire, marked and chained doors | B- (not in a shot) | better (offline) | Worn red paint and a crisp stencil; the painted kick plate (a copy of the Kick box) removed. |
| L! EXIT signs (hero 29) | B+ (r1: B+) | slightly better | A lip round each face; lights and faces unchanged. |
| Hospital bed (hero 30; Level 1 too) | B (r1: D on the preview's cut end) | better | Tube posts and rails, moulded boards with a recessed panel, castors, a vinyl mattress, sheet, a cellular blanket hanging over the sides, a pillow. The reviewer's "floating planes" are the preview of one half cut at the block edge, where the other half joins; in `bed-close` the bed is whole. |
| L! notices, dispenser | B (r1: B / C) | better | Pixel lettering; round 2 moved the pins off PLEASE and drew the hands as hands. The dispenser's window is a pane, the paddle hinged. |
| L! crash cart, cabinets, mattresses | B (preview; r1: B, C) | better | Drawers as boxes, an inset defibrillator screen, the medicine cabinet's mirror inset, the supply cabinet's label holder a box (round 2: r1 called the painted one a hardware icon); woven sheets and curtain, quilted vinyl mattress. |
| L! gurney, wheelchair, IV stand, collapse | C (r1: too dark) | same | Their models are unchanged; their paint (chrome, steel, sheet) changed. Too dark to grade in the shots. |
| Fun lobby walls, band, skirting (hero 31) | B (r1: C / B / B-) | better | Plaster paint in three versions; the band glazed tiles in the old colours under a cream cap; the skirting glazed white tile. The reviewer missed B0's roller laps on the cream wall ("a stripe"); they were a texture, not a pattern. |
| Fun painted walls | C+ (r1: C) | better | The repeated dash scuffs are gone; plaster paint in three versions; the low block a little dirtier toward the floor with rare rubs. Plain by nature. |
| Fun vinyl tiles (hero 32) | B- (r1: B-) | better | Each tile shaded and tinted, a recessed joint, no diagonal streak through every block; one faint scuff in two kinds of four. |
| Fun lobby, race and retro carpets (hero 31) | B- (r1: B-) | better | The patterns dyed into a pile; round 2 removed the block-sized mottle (r1: dark patches on the block grid) and kept the lines whole. |
| Fun elevator doors (hero 31) | C+ (r1: C; dial B+) | better | Round 2: brushed brass with a soft sheen instead of the painted pale stripe; raised frames on the leaves; a modelled dial; call buttons in the jamb (r1's plate floated past the wall's end: D). |
| Fun OUT OF ORDER, directory, deck sign | B+ / B / B (r1: B+ / B / B) | better | Pixel lettering; the deck sign's whole line fits now, its brass back to the old tone (round 2); the directory's last line lifted off the frame. |
| Fun TIME 4 FUN poster | B- (r1: D) | better | Pixel lettering on B0's picture; round 2 restored the "=)" (r1's read as an arrow) and moved TIME below the tape (the corner tape still clips its first letter at an angle). |
| Fun palm (hero 31; Level 5 too) | B+ (r1: B+) | much better | An octagonal terracotta pot with a rim and soil, a ringed trunk, eight drooping fronds and a spear. |
| Fun speaker | B- (r1: B-) | better | A bezel, a recessed cloth, woofer and tweeter behind wire bars; the body lifted from near black (round 2). |
| Fun chairs | B- (r1: C+) | better | A moulded seat and one back shell, stretchers, glides; round 2 shaded the plastic and lifted the black chair to dark grey. |
| Fun confetti | B- (r1: B-) | better | Crisp bits in three versions, turned. |
| Fun balloons, streamers, string lights | C (r1: C) | same | Not changed (the lights stay cubes). |

**Rounds**
1. **Round 1, blind** (Opus; given only the sheets, texsheets, mocks, previews and the rubric):
   - **D:** the call-button plate floating past the wall's end; the poster's "=)" reading as "=>" with TIME under the tape; the bed's preview (the cut end); the scuffed and cracked floor variants (B0's, unchanged).
   - **C:** the walls (plain), the vinyl (structure "lost": it never had tiles, only a seam per block), the cove's smudges, the elevator leaves (plywood), the chairs' flat plastic and pure black, the hall door's grain, the cabinet's painted label, the carpet mottle on the block grid.
   - **B or better:** the dial, the notices, the side doors, the EXIT signs, the cart, the band, the palm, the signs.
2. **Round 2 fixed:** the call buttons into the jamb; the poster's "=)" and TIME; the hand-washing notice's pins and hands; two versions of the scuffed and cracked floor; the cove's second scuff in place of the bracket-shaped rub; the rail's flecks; the hall door's grain; the cabinet label as a box; the elevator brass; the chairs' plastic and the black chair; the speaker body; the deck sign's tone; the directory's last line; the carpets' mottle. Reshot once.

**Carried below B, with reasons**
- **L! walls and Fun painted walls (C+):** institutional and party paint are plain surfaces; structure would change the look. Grime is kept subtle at the foot.
- **L! gurney, wheelchair, IV stand, collapse rubble (C):** their models are B0's; they stand in the dark and could not be graded.
- **Fun elevator leaves (C+):** brass in the old tone; the reviewer read the round-1 leaves as plywood, and the palette is kept.
- **Fun balloons, streamers (C):** not changed; the inventory said keep the balloons.
- **Not touched:** the fire doors' models (in no shot), the oven, the inflatables, the playroom, the deck, the murals (still in no shot), the beacons, the curtains' and gurney's models, the Safe Zone's props.
- **Palette question for the user:** Fun's party colours (vinyl, band) are still saturated primaries; the inventory asked whether to lower them a step. Kept.

**Tool changes:** none to shared tools.
- **New in `gen_run`:** the B14 section: `OLD_MEAN`, `RUN_F3`/`RUN_F5`, `ptext`, `matched`, `edges`, `fine`, `smudge`, `wall_versions`, `cove_b14`, `wallbase_versions`, `vinyl_b14`, the painters `b14_walls`, `b14_floor`, `b14_scuffed_cracked`, `b14_ceiling`, `b14_rail`, `b14_signs`, `door_paint`, `b14_doors`, `b14_props`, `b14_startroom`, `b14_textures`; the models `b14_versions`, `b14_floor_versions`, `sign_lip`, `wbx`, `side_leaf`; edits in `rail`, `walls`, `signs`, `side_doors`, `hall_door`, `props`, `gauntlet`, `startroom`.
- **New in `gen_fun`:** the B14 section: `FUN_OLD`, `FUN_F3`/`FUN_F5`/`BIG`, `ftext`, `fine`, `paint_b14`, `glazed`, the painters `b14_paint`, `b14_tiles`, `b14_vinyl`, `crisp`, `b14_carpets`, `b14_elevator`, `b14_signs`, `b14_party`, `b14_textures`; the models `b14_wall_versions`, `confetti_alts_b14`, `wbx`, `elevator_frame_b14`, `lift_dial_b14`, `call_buttons_b14`, `speaker_b14`, `chair_b14`.
- **Shared generators changed:** `gen_detail.hospital_bed_b14` (the bed is shared with Level 1's first-aid rooms), `gen_shapes.palm_b14` and `gen_textures.palm_textures_b14` (the palm is Level 5's).

**Lessons:** five lines added above.

### B15

Worker report (Opus, 2026-10-15). Branch `gfx/B15` from `main` (a20a0a3), uncommitted. Phase 1 was offline. Phase 2 was one blind review (round 1, `review/b15/review-round1.md`), then fixes and one reshoot. The round-2 grades are mine.

- **Final sheets:**
  - `review/b15/compare-round2-end.jpg` and `review/b15/compare-round2-hub.jpg`: every spot.
  - `review/b15/compare-round2-end-detail.jpg` and `-hub-detail.jpg`: the close spots at twice the size.
  - Shots: `review/b15/final/{end,hub}`. Round 1: `review/b15/compare-round1-*.jpg`, with its shots in `review/b15/after/`.
- **Per-family pairs:** `review/b15/sidebyside/<family>.jpg` (14 families), from `docs/design/graphics-pass/sidebyside/B15.json` (it reads `review/b15/sbs/{before,after}`, where shots carry an `end-` or `hub-` prefix). The B15 section is added to `review/compare.html`.
- **Decision table:** fourteen rows added to `decisions.md`, decision column empty. The textures are B15 painters that run after the old ones under the same keys (`gen_end.b15_textures`, `gen_hub_kit.b15_textures`). Their versions go to the block types through `ver()` / `versions_of()`, which fall back to the one old texture when a painter is dropped. Each model change sits behind a flag (`B15_SLATS`, `B15_EXITDOOR`, `B15_LAMP`, `B15_SERVICE`; B0's EXIT door is kept as `exitdoor_b0`). Each row names its functions.
- **Offline evidence** (`review/b15/offline/`):
  - `tex-end-walls-{before,after}.png`, `tex-end-props-after.png`, `tex-end-round2.png`, `tex-hub-after.png`: texsheets with vanilla references.
  - `mock-*.png`: The End's wall stack, partition, block wall, carpets, runway, ceiling, concrete and columns, and the Hub's walls (as laid: seams every 2 along, 3 up), roof, road and ashlar. Each is in its real mix of versions and turns, main above B15, with seam ratios (End wall stack 1.27 on main, 0.92 now; Hub asphalt 1.89 on main, 1.68 now). Round 1's copies are in `round1/`.
  - `preview-end-{endcap,exitdoor}.png`, `preview-hub-lamp-door.png`, `preview-hub-lamp-side.png`.
  - Also `harness/`, `main/` (main's textures and shapes), and the scratch tools in `tools/` (`addspots_b15.py`, `mocks_b15.py`, `churn.py`, `luma.py`, `prev.py`, `explore.py`, `map_at.py`, `query.py`, `enums.py`).

**Checks**
- **Build:** 0 warnings and 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir, both rounds). `build-gfxbase` was built from unchanged `main` before any edit. No C# changed.
- **`layouthash`:** v1 and v4 unchanged against main's output, line for line (`review/b15/offline/harness`).
- **`validatelevel 16` and `17`** (The End and the Hub, `SPAWN=16000`, 24 cells): no doorways to nowhere, none blocked, no bad elevators, no decor facing walls (main's output: no C# changed).
- **Saves:** no code, kind, variant group or class was added, renamed or removed, and there is no layout version. The changes are textures, new version texture keys, shapes on existing codes, `alternates` and `randomizeAxes`. Shot in `gfxreview`; no new world was needed.
- **`check_zfight`:**
  - The new endcap shapes are clean (round 1's corner-trim tops were moved under the top's plane).
  - The EXIT door's only flags are the lower half's jamb tops, which the upper half continues. Every part stops 0.05 short of the block's sides, and the head stops under the block's top.
  - The Hub lamp is clean.
  - The service door's flags are B0's posts only.
- **Churn:** `lang/en.json`, the End itemtypes and line endings restored after every regeneration (`churn.py`). Nothing outside the two levels' folders and the generators changed.
- **Brightness:** every final shot is within 0.9 levels of the new baseline (`review/b15/luma-final.txt`), and so was round 1. No run came out dark, and The End's lights-out did not fall in a run.
- **Texture keys:** The End's keys live in `block/end/` and the Hub's in `block/hub/`; no other generator writes there. The only outside reference is Level 3999's use of the End terminal's shape, which is unchanged.
  - New in `block/end/`:
    - `wall-{lower-2..6, ghost-2..4, cracked-2, base-2..4, band-2/-3, upper-2..4, uppercracked-2, block-2/-3}`;
    - `column-{sage,slate}-2/-3`;
    - `carpet-plain-2/-3`, `carpet-{dusty,worn,stained}-2`, `runway-2`, `concrete-2`;
    - `ceiling-plain-2/-3`, `ceiling-stained-2`;
    - `poster-yellow-2/-3`.
  - New in `block/hub/`: `wall-{plain,left,bottom,corner}-2..4`, `ceiling-2/-3`, `asphalt-plain-2/-3`, `asphalt-{worn,patch}-2`, `ashlar-{plain,worn}-2/-3`.
  - `poster-notice` is now 48 x 64, `poster-fixtures` 48 x 56, `poster-closing` 40 x 48 and `poster-near` 48 x 56, all on the 8 px grid.

**Baseline and spots**
- `review/baseline/end` and `/hub` were reshot on `build-gfxbase`; the B0 sets are kept as `end-b0` and `hub-b0`. A retake of seven spots first (`review/b15/base-check`) matched B0 within 0.1, and the full run within 0.4.
- **Added** (`review/spots/end.json`, `hub.json` and the docs copies; found on the harness grid with the scratch tools):
  - The End:
    - `ghost-close`: the partition at z 398774 from the north, ghost marks at x 857, 861 and 864;
    - `poster-close`: its south face, a card poster;
    - `shelf-close`: a gondola run;
    - `exitdoor-close`: the EXIT door at 398844,398842 in its vestibule;
    - `troffer-close`.
  - The Hub:
    - `door-close` and `sigil-close`: the carved door at 625176-178, z 624795;
    - `service-close`;
    - `lamp-close`;
    - `ornate-close-inspection`: the Tower's entrance doors at 625171-172, z 625144;
    - `tower-base` and `tower-stair`: inside the Tower.
- **Re-spotted after the base frames:** the ornate approach was black at floor level (only the Tower's dusk light reaches it), so it became an inspection spot. `lamp-close` was re-aimed. Both were retaken on `build-gfxbase`.
- **Not added:** the pink door to Level 974 (one per world, far from the anchor) and the M.E.G. outpost.

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| End store walls and columns (hero 33, 34) | C+ (blind r1: C) | better | Eggshell paint over plaster in the old tones. One ground is shared by the base, lower, ghost and cracked kinds, so the rows meet (seam 1.27 to 0.92). There are four versions picked by height (`randomizeAxes: xyz`). The dash scuffs that sat in the same place on every block are gone; plugs or a scuff appear in about one block in nine. The base has a 5 px vinyl cove under a soft dirt gradient. The band edges are clean. Plain by nature: the reviewer wanted more structure. |
| End partition ghost marks | B- (r1: D, invisible) | better | B0's one rectangle on 30% of a partition's eye-level blocks is now four different marks at different places: a sign, shelf standards, a clock, plugs and tape. Round 2 raised them to 12-15 levels and dropped the two blank versions. |
| End posters | B (r1: B-) | better | Paper with the same pixel lettering. The yellow poster has three versions (plain, folded, sun-faded). Round 2 fixed lettering that ran off the sheet on the yellow, card, notice and Level 11 posters. |
| End painted block wall (stockrooms) | B (r1: B) | better | 16 x 8 painted block in three versions by tone, quieted (`calm`). |
| End carpet and runway (hero 33) | C+ (r1: C) | slightly better | Loop pile, lightly dingy, three versions turned (`turn_safe`). Dusty, worn and stained kinds; round 2 strengthened the ring and the wear. The navy runway has its squiggles dyed into a cut pile. Dusty and worn still sit in whole-block patches, which is layout (B3's lesson). |
| End ceiling (hero 33) | B (r1: B-) | better | B3's module: four 2 x 2 ft tiles to a block, means evened, three versions. Round 2 brought the water rings back at the old strength. |
| End troffers | B- (r1: B-) | same | Level 0's D1 troffer (the user approved it): no dark ring, still cubes, same glow. The reviewer missed a busier prismatic lens; kept as the approved look. |
| End shelving (hero 33) | B- (r1: C, seams) | better | Maple veneer and real slats. Round 1's maple printed matlib's plank edge as a dark seam at every block height; round 2 removed it (`no_edge`). |
| End slatwall display towers (hero 33) | B (r1: B) | better | Slats one groove period tall, each a lit board edge over its slot. Before, there were 15 thin slices out of step with the grooves. |
| End EXIT door (hero 34; also Level 1, the Hub, Level !) | B (r1: B) | better | Hardware as geometry on every face: frame and stops, hinges, kick plate with screws, panic bar and lock cylinder, window bead, closer and arm. Round 2 put the wired glass's crack back. |
| Hub tunnel walls (hero 35) | C+ (r1: C) | better | Cast concrete with each version's own aggregate over one shared broad ground. Round 1 shared the aggregate, so every panel was the same speckle. There is a rare efflorescence run, the seams are recessed joints, and round 2 added a row of form-tie holes along each panel's lowest lift. The amber light flattens it in the shots. |
| Hub tunnel roof | C+ (r1: C, too dark in play) | same | Concrete with no board lines (the 2026-10 review had the roof stop reading as planks), three versions turned. |
| Hub road, sidewalk, kerb (hero 35) | C+ (r1: C / C+) | slightly better | `matlib.asphalt` (round 2: calmer chips), three versions turned. The worn kind is polished. The patch is an irregular tar blot (B0's was a square), off centre and at a different place in each version. The sidewalk joint is recessed and the kerb arris lit. Light worn squares are layout. |
| Hub lamps (hero 35) | B (r1: B) | better | Amber glass, glow and cage unchanged. Added a bolted wall plate, a bracket strut each side and a crown on the hood, with chipped paint. |
| Hub carved doors (hero 35) | C+ (r1: C) | same | Geometry unchanged. The slab is smooth warm concrete; round 2 added a fine horizontal shutter grain, and it has damp with a tide line. The escutcheon is brushed brass. |
| Hub sigils | B- (r1: B-) | same | Relief and deep recess unchanged; the faces are dressed stone at the old depth tones. |
| Hub service door | B- (r1: B-) | better | Chipped grey paint, hinge knuckles and a closer as geometry. |
| Hub ornate doors | B- (r1: B-) | same | Dark oiled oak in vertical boards. The ring pulls (B0's) still read as square loops. |
| Hub Tower ashlar and stair | B / B- (r1: B / B-) | better / same | Ashlar as stones in running bond, three versions by height, quieter than brick; the worn kind grimier. The marble stair is unchanged. |

**Rounds**
1. **Round 1, blind** (Opus; given only the sheets, texsheets, mocks, previews and the rubric):
   - **D:** the ghost marks, invisible in play (drawn at 6-8 levels, two of six versions blank).
   - **C:**
     - a dark seam at every block height on the shelving (matlib's plank edge on the maple);
     - the plain End walls, columns, carpet and runway;
     - the Hub walls (the same speckle on every panel), roof, asphalt and carved door leaves;
     - the stains and wear washed out; clipped poster lettering.
   - **B or better:** the EXIT door, endcap towers, block wall, lamps and ashlar.
   - **No dark ring and no layout change.**
2. **Round 2 fixed:**
   - the ghost marks (stronger, four marks, no blank versions);
   - the maple's seam;
   - the ceiling rings, carpet stain and wear;
   - all clipped lettering, and the wired-glass crack;
   - the Hub walls' own aggregate per version and their form-tie holes;
   - the door leaves' grain;
   - calmer asphalt and patches off centre.
   
   Reshot once.

**Carried below B, with reasons**
- **End walls, columns, carpet, runway (C+):** plain painted and carpeted surfaces in the old tones. The reviewer's fixes do not fit the user's rules:
  - multi-block joints or a per-block vertical gradient would repeat on every block row (B9's lesson);
  - stronger wear would be a per-block feature.
  
  Grime is kept subtle, as the user asked.
- **Hub walls, roof, road, carved leaves (C+):** concrete and asphalt under monochrome sodium light. Board lines on the roof were removed on purpose (2026-10 review). Panel-scale structure (seams, ties) is all a per-block texture can carry without a grid.
- **Not touched:**
  - The End: desks, the terminal, furniture, catalogue, escalator, railing, stock trolley, trees, rubble (none in a shot; there is no checkout in the level).
  - The Hub: the pink door (in no shot), jet fans' geometry, stencils, plaques, outpost furniture, the statue, pedestals, the Keymaster.
  - Troffers and lamps stay as they were (the lights-as-cubes rule; Level 0's approved troffer).

**Tool changes:** none to shared tools.
- **New in `gen_end`:**
  - Helpers and registration: the B15 section's `OLD_MEAN`, `VERSIONS`, `ver`, `register`, `matched`, `calm`, `b15_fine`, `b15_bumps`, `paint_ground`.
  - Marks and wear: `wall_plugs`, `soft_rect`, `soft_disc`, `ghost_mark`, `scuffs`, `no_edge`, `bevel_sheet`.
  - Painters: `b15_walls`, `b15_floors`, `b15_ceiling`, `b15_wood`, `b15_metal`, `b15_posters`, `b15_textures`.
  - Flags: `B15_SLATS`, `B15_EXITDOOR`.
  - Edits:
    - `exitdoor` rebuilt, B0's kept as `exitdoor_b0`;
    - the endcap tower built from slats;
    - `structure()` reads versions through `ver()`;
    - `backed_block` gives the wall behind a decoration its versions;
    - `AXES` on the wall and column block types.
- **New in `gen_hub_kit`:**
  - The B15 section's `OLD_MEAN`, `VERSIONS`, `versions_of`, `matched`, `b15_fine`, `groove_left`, `groove_bottom`, `tie_hole`, `tooled`.
  - Painters: `b15_walls`, `b15_road`, `b15_fixtures`, `b15_doors`, `b15_tower`, `b15_textures`.
  - `B15_LAMP` (the lamp's bracket).
  - `cube_family` and the ceiling read `versions_of`.
- **Also:** `gen_hub_doors.B15_SERVICE` (the service door's hinges and closer); `gen_hub_tower` (`randomizeAxes` on `hub-ashlar`); `gen_hub.main` calls `K.b15_textures()`.

**Lessons:** five lines added above.

### B16

Worker report (Opus, 2026-10-15). Branch `gfx/B16` from `main` (5f23817), uncommitted. Phase 1 was offline. Phase 2 was one blind review (round 1), fixes and one reshoot (round 2), and one retake of `3999/vending-close` after a last fix to the vending machine (with two unchanged spots to check the light). The round-2 grades are mine.

- **Final sheets:**
  - `review/b16/compare-round2-974.jpg`, `-3999.jpg`, `-188.jpg`: every spot.
  - `review/b16/compare-round2-<level>-detail.jpg`: six close spots per level at twice the size.
  - Shots: `review/b16/final/{974,3999,188}`. Round 1: `review/b16/compare-round1-*.jpg`, its shots in `review/b16/after/`.
- **Per-family pairs:** `review/b16/sidebyside/<family>.jpg` (20 families), from `docs/design/graphics-pass/sidebyside/B16.json` (it reads `review/b16/sbs/{before,after}`, shots prefixed `974-`, `3999-`, `188-`). The B16 section is added to `review/compare.html`.
- **Decision table:** nineteen rows added to `decisions.md`, decision column empty. Each level's B16 work is in its own new module (`tools/gen_974_b16.py`, `gen_3999_b16.py`, `gen_188_b16.py`): painters that run last under the same keys (plus new version keys), model parts behind flags in the old builders (`B16_COMPUTER`, `B16_FRAME`, `B16_FURNITURE`, `B16_VENDING`, `B16_CABINET`, `B16_COURTYARD`), and a `COUNTS` table of versions the block types read. Each row names its functions and how to revert.
- **Offline evidence** (`review/b16/offline/`):
  - `tex-{974,3999,188}-{before,after}.png`: texsheets, tiled 3x3, with vanilla references.
  - `mock-*.png`: the marble (white, black), 974's paint, carpet, ceiling, checker and bath tile, 3999's midnight paint, 188's pavers (plain, mossy, cracked) and render, in their real mix, main above B16, with seam ratios (188 render 2.38 on main, 0.74 now; marble white 0.79 to 1.03, black 0.86 to 0.87, both now without the per-tile scribble); `marble-versions.png`.
  - `preview-*.png`: the chair, booth and table, cabinet, vending machine (`-r3` is the final one), computer and frame, bollard and downpipe, main beside B16.
  - `newspots-base.jpg` (the new spots' base frames), `crop-vending-*.jpg`, `harness/`, `main/` (main's textures, shapes and block types), and the scratch tools in `tools/` (`addspots_b16.py`, `mock.py`, `t3999.py`, `decisions_b16.py`, `tracker_b16.py`, and B15's `churn.py`, `luma.py`, `prev.py`, `explore.py`, `map_at.py`, `query.py`).

**Checks**
- **Build:** 0 warnings and 0 errors (`tools/locked.sh mod gfx`, a clean scratch dir, both rounds). `build-gfxbase` was built from unchanged `main` before any edit. No C# changed.
- **`layouthash`:** v1 and v4 unchanged against main's output, line for line (`review/b16/offline/harness`).
- **`validatelevel 18`, `19`, `20`** (974, 3999, 188; `SPAWN=16000`, 24 cells): no doorways to nowhere, none blocked, no bad elevators, no decor facing walls, before and after.
- **Saves:** no code, kind, variant group or class was added, renamed or removed; no layout version. The changes are textures, new version texture keys, shapes on existing codes, `alternates` and `randomizeAxes`. Shot in `gfxreview`; no new world was needed.
- **`check_zfight`:** no new pair. Per level, main against B16: 974 17 and 17 same-shape pairs; 3999 489 and 487; 188 27 and 27 (all in unchanged models: the cabinets' T-moulding and crest, the old `cyl` posts). Round 1's two new pairs (the chair's spine against its back, the downpipe socket's lip) were fixed. The booth's back and the vending machine's top reach the block above, as B0's did.
- **Churn:** `lang/en.json`, the 3999 item types and line endings restored after every regeneration (`churn.py`); nothing outside the three levels' folders, their generators, the spot lists and the docs changed.
- **Brightness:** 974 and 3999 within 1.4 levels of the new baseline in every final shot (`review/b16/luma-final.txt`). 188 is within 1 except where a window or a flickering light changed state at runtime (`downpipe-foot` -12, `downpipe-close` +8, `downpipe-wide` -6, `wide-02` -6), the same spots in both rounds.
- **Texture keys:** every new key is in the level's own folder (`block/974/`, `block/3999/`, `block/188/`), which only its generator writes.
  - 974: `paint-3`, `paint-4`, `ceiling-2/-3`, `carpet-2/-3`, `checker-2`, `bathtile-2`, `keycap`.
  - 3999: `marble-white-2..4`, `marble-black-2..4`, `wall-{violet,midnight,teal}-2/-3`, `plastic-{white,pink,cyan}-side`, `fc-top`, `fc-edge`, `fc-chrome`, `fc-glide`, `fc-kick`, `vinyl-pink-side`, `vinyl-piping`, `coindoor-plate`, `coinmech`, `coinbutton`, `cab-bumper`, `cab-trim`, `vendback-{snack,drink}`, `vendshelf`, `vendprod-snack-0..5`, `vendprod-drink-0..4`.
  - 188: `paver-plain-2/-3`, `paver-moss-2`, `paver-cracked-2/-3`, `cladding-plain-2/-3`, `cladding-band-2`, `hopper`.
  - No longer used by any shape (still written): 974 `keyboard`; 3999 `coindoor`.

**Baseline and spots**
- `review/baseline/974`, `/3999` and `/188` were reshot on `build-gfxbase`; the B0 sets are kept as `974-b0`, `3999-b0`, `188-b0`. A first retake of four spots per level matched B0 within 0.2 (974, 3999). The first full run came out 20-115 levels dark everywhere (kept as `review/b16/baseline-dark1`) and was retaken; the retake matched B0 within 0.1 on 974 and 3999. 188 differs at runtime (see the lessons).
- **Added** (`review/spots/974.json`, `3999.json`, `188.json` and the docs copies; found on the harness grid):
  - 974: `kitchen-wide`, `kitchen-close` (the stove and counter run), `bath-wide`, `kittyroom-wide` (Kitty's room: the bed alcove, nightstand, plush, posters), `bed-close`, `hall-wide`, `master-wide` (the cat bed).
  - 3999: `marble-close`, `table-close`, `cabinet-close`, `fascia-close` (a concourse gallery's white marble fascia and its neon, from the food court), `vending-close`.
  - 188: `moss-close`, `bollard-close`, `paving-close`, `blind-close`, `blind-close2` (ground-floor windows; their state changes at runtime, both were up in every run), `downpipe-foot`.
- **Re-spotted after the base frames:** `fascia-close` (its first place framed the underside of a gallery).
- **Not added:** the hopper head (rel 21, in no shot; judged on the preview), a window with its blind down (runtime state).

**What changed, per family**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| 3999 marble floor, gallery fascias, storey line (hero 39) | B (blind r1: B) | much better | B0's one vein scribble per tile and diagonal gloss band (inventory D) are gone. Tiles are cut from one large slab, each a different piece, turned, tone evened, 2 x 2 to a block with 1 px joints; four versions per colour, `randomizeAxes: xyz`. Round 2 calmed the white's branch veins and took them off the black (r1: dashes). Answer to the reviewer's question: it no longer repeats. |
| 3999 food court chairs, tables, booths (hero 39) | B- (r1: B- chair, B table, D booth preview) | better | Shell chair with a dished seat, rolled lip, spine, leaning back with a rolled top, tube legs on glides, rails and a stretcher; octagonal table top with an edge band, collar, four-star foot; booth with a kick strip, rolled seat, piping and buttoned channels. Round 1's booth preview predated a fix (its base and back panel are closed in the shapes shot). Round 2 softened the plastic sheen and thickened the legs. At food-court distance they still read close to B0's silhouettes (the reviewer's point); the lore's colours kept. |
| 3999 arcade cabinets (hero 38) | B (r1: B) | better | Coin door as a plate with chrome coin entries and slots, coin buttons, a lock; a trim rim round the screen, an aluminium marquee frame, a rubber panel bumper and lip; painted-wood body. Screens, marquees, glow unchanged. |
| 3999 vending machines | B (r1: D sign, B body) | better | The window an opening with five shelves and packs behind the glass; round 2 fixed the picture's mirrored UVs (r1 cut the sign to "RINKS"), put the glass over the window and modelled the keypad (twelve keys) and the ALMOND WATER ONLY label on their painted places. |
| 3999 painted plaster (fascias, gallery walls) | C+ (r1: C) | same | Paint over plaster in three versions on one ground; plain by nature, mostly too dark to judge in the shots. |
| 974 pink paint (hero 36, 37) | B- (r1: B-) | same | Four versions on one ground, `randomizeAxes`; the base and crown kinds take them by key. Mean kept: the house reads as before. |
| 974 carpet | B- (r1: B-) | better | Cut pile, lightly lived-in, three versions turned. |
| 974 ceiling | C+ (r1: C) | same | Plaster in three versions; plain by nature. |
| 974 checker, bath tile | B (r1: B) | slightly better | Glazed tiles, shaded, recessed grout; two versions, never turned. |
| 974 computer | B (r1: B) | better | Screen set in a bezel; the keys as keys. |
| 974 photo frames | B (r1: B) | better | A moulding with a bead and a lip; the gilt burnished. |
| 974 furniture bodies (desk, dresser, bed, kitchen) | C+ (r1: C desk) | slightly better | Only the trim paint changed (a faint grain); the models are B0's (already modelled: knobs, drawers, rails). |
| 188 pavers (hero 40, 41) | B (r1: B plain, C cracked, C+ moss) | better | Slabs in running bond, lit edges, recessed joints, aggregate on one ground; round 2 deepened the joints (r1: they faded at a distance), gave the cracked kind three versions with the crack and a faint stain at a different place each (r1: per-block repeat) and the moss more runs, kept inside the block (r1 seam 1.94, now 0.53). |
| 188 moss tufts | B- (r1: not graded) | slightly better | Eighteen fronds instead of twelve, darker roots, lit tips; the 2026-10 review's light tone kept. |
| 188 render (hero 40, 41) | B- (r1: B-) | better | Three versions by height on one ground; seam 2.38 to 0.74 (B0 drew a joint on every block's edge); the band a clean groove; the streak fades before the block's foot (it is under a sill, so it stands where the sill is). |
| 188 blinds and window aluminium | B- (r1: same, runtime) | same in shots | The blind a woven roller fabric (B0 painted slats), the lit blind without slat lines; brushed aluminium. Every window in the new spots was open in both runs, so the blind is judged on the texsheet. |
| 188 bollards | B (r1: B) | better | Bolted octagonal plinth, octagonal body, stepped cap; the lit band and its light unchanged (no ring). |
| 188 downpipe and hopper | B- (r1: B-) | better | Clips bolted to the wall, socket collars, round paint; the hopper flared with a rim and water. Its back faces are left off (it hangs on a wall, as B0's did). |
| 188 courtyard door, EXIT sign | B- (r1: same) | slightly better | Push bar on brackets, brushed aluminium and kick plates with screws; the sign's box painted; face and light unchanged. |

**Rounds**
1. **Round 1, blind** (Opus; given only the sheets, texsheets, mocks, previews and the rubric):
   - **D:** the vending sign cut to "RINKS"/"NACKS"; the booth's preview (rendered before a fix, the shapes shot were closed).
   - **C:** the cracked pavers' stain and crack in one place; the cladding streak; the mossy pavers' seam; 3999's plain paint; 974's ceiling and desk bodies.
   - **B- or better:** the marble (no longer repeats), the table, chair, cabinets, vending body, 974's tiles, computer and frames, 188's plain pavers, render, bollard, downpipe.
   - **No dark ring, no layout change, nothing off palette.**
2. **Round 2 fixed:** the vending machine's UVs, glass, keypad and label; three cracked-paver versions; the moss runs; deeper paver joints; the marble's branch veins; the plastic's sheen; the chair's legs; the streak's fade. Reshot once; the vending spot retaken after its last fix.

**Carried below B, with reasons**
- **3999 painted plaster (C+), 974 ceiling (C+):** plain paint and plaster in the old tones; structure would change the look, and per-block marks repeat (the user's rule).
- **974 furniture bodies (C+):** the models were already modelled; B16 changed only their paint. A bevel or inset pass on the desk, dresser and kitchen units is left for a follow-up.
- **3999 food court furniture at a distance (B-):** modelled now, but at 10+ blocks in the food court's single-colour light it reads close to B0. Kept the lore's colours rather than two-toning the seat.
- **188 blinds (B-):** no window in the spots had its blind down in any run (runtime state); judged on the texsheet.
- **Not touched:** 3999's neon (tubes, signs, pillars, base strips: lights stay as they are), carpets, concrete, lane wood, the other machines (racer, dance, pinball, claw, skee-ball, air hockey, prize counters), lobby furniture; 974's windows and paintings, plush, kitchen and bath models, lights; 188's corridors, rooms, deck, hatch, windows' frames, outer windows, lobby, EXIT sign face.

**Tool changes:** none to shared tools.
- **New modules:** `tools/gen_974_b16.py`, `tools/gen_3999_b16.py`, `tools/gen_188_b16.py` (each documented in its docstring).
- **Hooks:** `gen_974_tex.generate`, `gen_3999_tex.generate`, `gen_3999_tex_arcade.generate` and `gen_188_tex.generate` call the B16 painters last; `gen_974.B16_ALT` gives a texture entry its versions; `gen_188_kit._tex_entry` does the same for every 188 cube block.
- **Edits:** `gen_974` (`B16_COMPUTER`, `B16_FRAME`, the wall, floor and ceiling block types' versions and `randomizeAxes`); `gen_3999_blocks` (`B16_FURNITURE`, `B16_VENDING`, the marble and wall versions and `randomizeAxes`); `gen_3999_arcade` (`B16_CABINET`); `gen_188` (cladding `randomizeAxes`, the courtyard door's push-bar brackets); `gen_188_props` (`B16_COURTYARD`).

**Lessons:** four lines added above.

### D2

Worker report (Opus, 2026-10-16). Follow-up batch on four "tweak" decisions for B13, B14 and B15 (`decisions.md`, each
row now ends with a "D2:" note). Branch `gfx/D2` from `main` (fed0a6b), uncommitted. **Offline only: nothing was shot**
(the user is at the machine; the game was not running, but no client was started and nothing was built into
`bin/Debug`). The grades are my own reading of the offline previews and mocks, not a blind review; every item still
wants an in-game look.

**Evidence** (all in `review/d2/offline/`)
- `preview-pooldoor.png`: the door in a tile wall on a tile floor, pre-B13 (cube, `3dc539f^`), B13 (main) and D2, each
  head-on, from 35 degrees to the left, from a low viewpoint near the floor, and a close-up of the foot. Rendered with
  `preview_shapes`' textured rasteriser from any camera (`tools/scene.py`). `crop-pooldoor-b13-foot.png` is the B13
  in-game close shot's foot: the diagnosis.
- `preview-funchair.png`: the red, white and black chairs, pre-B14 (`abc1e6f^`), B14 (main) and D2, from the front-left,
  back-right and side, and the tipped chair.
- `mock-end-ceiling-6x3.png`: The End's ceiling as 6x3 blocks in its real mix (a stained block with the layout's one in
  sixteen, else a pick from the plain kind's weighted list), two seeds, pre-B15, B15 and D2, at 4x and averaged down 4x,
  each labelled with its stain share. `ceiling-stain-versions.png`: every stain version among plain blocks, beside
  itself and below itself, to see the joins.
- `mock-hub-road-6x6.png`: the Hub road as 6x6 blocks in the layout's mix (3% patch, 8% worn, else plain, versions and
  turns at random), pre-B15, B15 and D2, two seeds (the second forces six worn blocks), at 4x, averaged down 4x, and
  averaged under a rough sodium tint at 2.2x gain (which exaggerates contrast). `road-means.txt`: each texture's mean
  and spread.
- `layouthash-v1.txt`, `layouthash-v4.txt`, `zfight-after.txt`. Scratch tools in `tools/` (`scene.py`, `door.py`,
  `chair.py`, `ceiling.py`, `stain_try.py`, `road.py`, `churn.py`, `crlf.py`, `docs_d2.py`, `report_text.py`).

**Checks**
- Build (`tools/locked.sh mod gfx`, the scratch dir): 0 warnings, 0 errors. No C# changed.
- `layouthash` v1 `18cfdbc1c530f039` and v4 `ca047189969b69db`: identical line for line to B16's output (the existing
  `mapgen-gfx` harness).
- `check_zfight pooldoor fun-chair`: no same-shape pairs. The only flags are the door's stile tops where the upper half
  continues them, as on B13. The new kick plate has no down face; it rests on the floor.
- Saves: no code, variant group, kind or class added, renamed or removed; no layout version. The changes are shapes on
  existing codes, textures, a new texture key (`poolkick`), two new version keys (`end/ceiling-stained-3`, `-4`) and
  alternates lists.
- Churn: `gen_detail` (which runs `gen_pool`), `gen_end`, `gen_fun` and `gen_hub` were run through `locked.sh run`
  (`VINTAGE_STORY=G:\Games\Vintagestory`). Their line-ending rewrites, `lang/en.json` and the `exitlintel*` key order
  were restored from git. `gen_detail` also rewrote `detail/hospbed-blanket.png` (B14's, not in scope), which was
  restored too. `git status` shows only the four families' files and their generators.

**Per item**
1. **Level 37 POOL door: done. My grade B+; meets the request on the previews.**
   - Diagnosis. The B13 leaf did reach the floor; the read came from its foot. Two things made the leaf look raised:
     - The kick plate was `poolsteel`, the wall tile's own pale tone. In the shot it read as the wall seen through a gap
       under the door.
     - A mid rail in the leaf colour sat above the plate, with a lit edge that read as the bottom of the door.
   - The fix:
     - The kick plate now starts at the floor (y 0 to 4; B13: 0.6 to 5). It is a darker brushed stainless with a lit
       top edge, a shaded foot and four screws (`poolkick`, new key).
     - The mid rail is removed.
     - From the low viewpoint the cyan stiles and the plate both meet the floor line.
   - The porthole moved up (centre 11.3, radius 3.2; B13: 7.25 and 3.6). POOL sits under it, rows 17-23 of the upper
     leaf, about 1.4 m up the door; B13 had it at the top, 1.8-1.9 m. This is the old door's order (porthole, then
     POOL).
   - The push plate, stiles, ring and glass are B13's.
   - Risk: the plate's tone under Level 37's warm light. It should read as metal, not as a shadow; check it in game.
2. **Level Fun chairs: done. My grade B; meets the request.**
   - The back is the pre-B14 geometry: three stepped slats, each set 0.4 further back, the top one narrower, all tipped
     8 degrees. The first slat starts at the B14 seat's top (8.8 instead of 9) so it sits on the new seat.
   - It is drawn in the B14 shaded plastic. Each slat shows the texture's lit top band, so every step has its own lit
     edge.
   - The rest of the B14 chair is kept: the seat, rolled front, skirts, tube legs, stretchers and glides. B14's one
     shell, rolled top and foot are gone.
   - The tipped chairs follow, all five colours.
3. **The End ceiling stains: done. My grade B; meets the request, with one limit on joins.**
   - Four stain versions (`D2_STAINS`, `d2_stain`), each drawn over a plain version's tiles:
     - large and faint over all four tiles, with an inner tide line;
     - strong and round over the centre rail;
     - a long seep with three tide lines that runs out across the east edge;
     - two drips run together, with a small ring beside them.
   - Each has a darker tide line about 1.2 px wide, like the old ceiling's rings, inside an even tan fill. The T-bar takes
     the stain at half strength.
   - Stains are drawn on the block's torus, so whatever leaves one edge comes back at the other. The seep is the one
     that crosses a block edge: two seep blocks side by side make one stain.
   - The limit: two stained blocks only join when the game happens to put the same version side by side. Next to a
     plain block, the seep stops at the T-bar, where a real tile's stain stops.
   - Frequency:
     - the stained kind lists all four versions;
     - the plain kind lists them once each, beside each plain version eleven times (`ceiling-mix`);
     - with the layout's own stained blocks (one in sixteen) that comes to about one block in six (measured 0.17).
   - Pre-B15 and B15 were both one in sixteen. The brief said "as before"; the share is now 0.17. Lowering it is one
     constant (`D2_PLAIN_WEIGHT`).
   - The mezzanine deck's underside keeps the plain list.
4. **Hub road: done. My grade B- for the worn kind (the road stays C+ as carried in B15); meets the request.**
   - The worn kind is the plain road's own asphalt: the same chips, binder and grain on the same ground. It is 3 levels
     lighter (`D2_WORN_LIFT`).
   - B15's worn kind was polished smooth (half the grain contrast) and 13 levels lighter, so it stood out as a smooth
     light square.
   - The plain versions now sit on one mean within 0.4 levels; B15 had them up to 1.2 apart. The first version and the
     patches are byte-identical.
   - On the mock the worn squares no longer show at 1x. Under the exaggerated sodium tint they are a faint trace.

**Not done, for the overseer**
- No in-game shots or side-by-sides (the user's screen). To shoot:
  - the POOL door close (`37/pooldoor-close`), and one from a crouch;
  - a Fun party table with chairs (`fun/prop-1`, `prop-2`);
  - The End's ceiling (`end/close-ceiling`, `wide-03`);
  - the Hub road (`hub/close-floor`, `wide-04`).
- Mean brightness: the door's lower half is a little darker (the plate); the End's stained share rose from 6% to 17%;
  the worn asphalt is 10 levels darker than B15's. Nothing else moved.

**Lessons:** one line added above.

### D3

Worker report (Opus, 2026-10-17). Follow-up on Level 94 from the user's three requests: every house yellow, the siren
poles standing, and the water towers redesigned to the lore pictures. Branch `gfx/D3` from `main` (c68f794), uncommitted.
Phase 1 offline (gated by the overseer), then one blind review (round 1), fixes and one reshoot in a fresh world.

**User decisions on the way (2026-10-17):** no lettering on the hill towers: the Sikeston idea (Miraheze: the castle
"resembles a white water tower, with the word 'Sikeston' on it") is kept for the castle later, and is not added anywhere
now. The new tower is placed in every world (no version gate).

- **Final sheets:**
  - `review/d3/compare-round2-vs-main.jpg`: every spot, before = main as the user played it (`review/b13/final/94`).
  - `review/d3/compare-round2-vs-baseline.jpg`: the same against `review/baseline/94` (pre-B13).
  - `review/d3/detail-round2.jpg`: the tower, pole and house spots at a larger size.
  - Shots: `review/d3/final` (world `gfxd3`, layout version 8). Round 1: `review/d3/after`, `compare-round1-*.jpg`,
    `detail-round1.jpg`, the reviewer's packet in `review/d3/review1/`.
- **Per-family pairs:** `review/d3/sidebyside/{watertower,houses,sirenpoles}.jpg` from
  `docs/design/graphics-pass/sidebyside/D3.json`; the D3 section is in `review/compare.html`. The five new spots have no
  before (marked MISSING on the left).
- **Decision table:** three rows added to `decisions.md`, decision column empty.
- **Offline evidence** (`review/d3/offline/`): `tower-preview.png` and `-close.png` (the tower beside B13's from three
  angles, and close views, from the written shapes), `tex-tower-round2.png`, `town-poles-v7-v8.png` (the harness town at
  layout 7 and 8, poles in red, `NearestSirenPole`'s corners ringed), `siding-counts-v7-v8.txt`, `town-map-v7/v8.txt`,
  `lore/` (`lore.txt` with the URLs and what each picture shows, the pictures and zooms), `harness/` (layouthash,
  links, deep, validatelevel), and the scratch tools in `tools/`.

**Lore found:** Wikidot's Level 94 says only "a water tower, which seems to contain Almond Water"; its picture "94 CC 1"
shows a white, squat, rounded tank on four tall, nearly vertical white legs with a riser between them and a band round its
waist. Miraheze's picture is the same scene, clearer: a catwalk round the tank, white columns and ties. Both show
cream-yellow houses. Fandom was unreachable (402) and is a different level anyway.

**What changed**

| Family | Grade | vs before | What changed |
|---|---|---|---|
| L94 water tower | B (blind r1: tank C+, legs and frame B, tower-far B) | much better | The tower of the pictures, one model cut into a block per tile and level over the old 5 x 5 tiles and 14 levels: four legs on concrete footings with base plates, bolts, and rust and dirt at the feet; girders at two heights and crossed tension rods with a ring at each crossing; a flanged riser over the Almond Water tap (still `watertower-tap`); a sixteen-sided riveted tank on a half-ellipse bottom; a catwalk with a grating deck, posts and two rails; a low cone of a roof with a crown, vent, red beacon and lightning rod; a ladder up a leg to the catwalk and one up the tank. Plain warm white, no lettering; rust runs from the rivets in one tank version in three, a faint weep in another. Round 2 warmed every white (the tank read grey beside the ivory legs), dropped the rust speckle at the rivets and the roof's seam lines (they broke into dashes where the cone's plates overlap). |
| L94 houses | B (r1: yes, every house yellow) | better | Layout version 8: every hill and town house cream-yellow (`SidingYellow`); in 1-7 three in ten hill houses and a third of the town houses were white. 40 cells round the anchor: 0 white siding tiles at v8 against about 4,300 at v7. |
| L94 siren poles | placement B (r1: yes, at the ringed corners); the pole model C+ (r1, carried) | better | Layout version 8 places the poles after the town's house lots (`PlaceSirenPoles`), on the lots' front corners across the crossroads from the plaza's corners, where `NearestSirenPole` has always put them (in 1-7 the lots covered them: none stood). The B13 pole model is not changed. |

**Rounds**
1. **Round 1, blind** (Opus; given the compare sheet against main, eight larger shots, the offline previews, the town map
   and the two lore pictures, and asked the user's three questions):
   - Houses: yes, every house yellow (wide-05, -07, -08 had white siding before). Poles: yes, at the ringed corners.
   - Tower: partly. Reads as an elevated municipal tank close to the lore silhouette, no z-fighting, gaps or floating
     parts; but the tank was a cool grey beside the ivory legs, the rust speckle and fine lattice read realistic rather
     than clay, and the roof's seams read as scratches. watertower-name faced into the sun.
   - Out of scope, reported: the siren pole's speakers are plain grey boxes (C+), the castle's glass at the mountain's
     foot (B13), wide-01 now has a pole in its foreground (layout), radio-close, prop-1 and wide-06 too dark or blocked.
2. **Round 2 fixed:** one warm white for tank, legs, deck and roof (`TW_WHITE`); rust runs only; the roof's seams
   removed; `watertower-name` re-aimed as `watertower-west` (sun behind the camera). Reshot once; my grades above.

**Checks**
- **Layout:** `WorldLayout.CurrentVersion` 8, in its doc comment, `docs/DEVELOPING.md` and `CHANGELOG.md`. `layouthash`
  v1, v4 and v7 identical line for line to main's output; v8 differs from v7 only on the two Level 94 lines and the total
  (`review/d3/offline/harness/`). `links` and `deep` identical to main's but for timing. `validatelevel 13` (Level 94,
  SPAWN=16000, 24 cells) as on main: four doorways blocked by props (B13's).
- **Saves:** no code, variant group or class renamed or removed. New: block `watertowerframe` (variant group `part`,
  222 states `x<i>z<j>y<level>`, one shape each under `shapes/block/detail/watertowerframe/`), placed by
  `WorldGenerator.WaterTowerFrameBlock` where the old tower's legs, tank and roof went, in every world; chunks generated
  before keep the old tower (a tower straddling the edge of explored ground at the moment it generates can come out half
  old, half new). The old `watertower` codes are unchanged; with the new blocks missing the generator falls back to them.
  `NearestSirenPole` reads the same `SirenPoleOffsets` as the poles, so it is right in every version.
- **Build:** 0 warnings, 0 errors (`tools/locked.sh mod gfx`, clean scratch dir); the harness rebuilt clean.
- **check_zfight:** clean on all 222 shapes, and on the whole tower put back together.
- **Texture keys:** `towershell` (-2, -3), `towerpaint`, `towerfoot`, `towerroof`, `towergrate`, `towerfooting`,
  `towerlamp` are new and used by no other generator; `towersteel` (B13) is reused for rods, bolts and plates.
- **Churn:** line endings, JSON key order and `hospbed-blanket.png` (gen_run's) restored from git after every run.
- **Brightness:** within 1.2 levels of round 1 on every spot but the castle's (glass and sky, -5.6); against main within
  1 level except where the tower or the poles are new in frame (watertower-close +7.7, wide-01 -7.1, the castle within 3).
  No run came out dark.

**Carried below B:** the siren pole's speakers (C+, B13's model: plain boxes in pure grey); out of scope, unchanged.

**Tool changes:** none to shared tools. **New in `gen_motion`:** the D3 section: `TW_*` constants, `tower_d3_textures`,
`_tw_box`, `_tw_octo`, `_tw_whole`, `_tw_yaw`, `_tw_facet`, `_tw_cone`, `_tw_profile`, `_tw_rod`, `_tw_level_spans`,
`tower_d3_model`, `_tw_world_box`, `_tw_local`, `_tw_auto_uv`, `tower_d3_cells`, `_tw_bounds`, `tower_d3_blocks`.

**Lessons:** four lines added above.

**For later (user, 2026-10-17):** the Sikeston water tower is kept for the castle; nothing carries the name yet.
