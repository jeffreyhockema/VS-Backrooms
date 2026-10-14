# Graphics pass: inventory (B1)

Written 2026-10-13 by the B1 session (Opus), from the B0 baseline. It is graded against the rubric in
[README.md](README.md) section 3, applied strictly: a noise fill with no structure is C; painted-on 3D, broken
tiling or visible repetition is D; A means "matches the vanilla block beside it". Nothing in the mod is A today.

## How to read this

- **Evidence.** The level sheets and shots are in `review/baseline/<level>/`. The texture sheets (4x, vanilla
  framed in gold, plain and `-tile`) are in `review/baseline/texsheets/`, and the textured model previews are in
  `review/baseline/props/`. The hero shots are in `docs/screenshots/`. Spot names are the shot names (`wide-03`,
  `close-floor`, `tent-close`, `wide-01-inspection` and so on); "hero NN" is `docs/screenshots/NN-*.png`.
- **Rows.** There is one row per asset family, grouped by the generator functions that make it, so a worker can take
  a section and know which functions to change. `*` marks a hero asset, one that a gallery shot shows.
- **Generator.** `file:function` is relative to `tools/`. Line numbers are as of the B0 commit. Most
  `detail_textures.py` and `deep_textures.py` painters are one long function per level (`level1`, `level61`, ...),
  so those rows give the texture key or a line range inside the function.
- **Vanilla reference.** Paths are relative to `G:\Games\Vintagestory\assets\survival\textures\` (for example
  `block/stone/plaster/plain.png`). A folder means "any file in it".
- **Priority.** 1 means seen in most playthroughs and below B, or a hero asset below B. 2 means seen in a level
  most players reach, or a D anywhere. 3 means rare, small, or already B. A `—` in the priority column marks a
  cross-reference to a row in another batch; those rows are left out of the counts.
- **Grade.** "not seen" means no baseline shot shows the asset. Each such row names a spot to add.
  `tools/shotbot/mkspots.py make <level>` rebuilds a list; add the spots by hand to `review/spots/<level>.json`
  and `docs/design/graphics-pass/spots/`.
- **Frames to re-spot before a batch shoots.** These are black or useless in the baseline:
  - Level 1: close-wall, close-wall2, close-ceiling.
  - Level 3: close-floor, den-wide, den-close, pipeend-close.
  - Level 6.1: gate-wide, gate-close, threshold-wide, threshold-close, sleepingbag-wide, sleepingbag-close.
  - Level 7: gate-wide, gate-close, tent-close, close-water. Use the `-inspection` shots.
  - Level 11: refuge-wide, refuge-close.
  - Level !: wide-07, prop-1, prop-2.
  - Level 9: every wide shot is at night, under grass. Add two or three day spots on a street, facing houses (as in
    hero 19 and 20).
  - Level 974: the eight wide shots are the same plan. Add the kitchen, the bathroom and Kitty's room.
  - Level 2: wide-05, wide-06 and wide-07 are too dark to judge.

## B3 Level 0

Generators: `tools/gen_textures.py`, `tools/gen_l0_walls.py`, `tools/gen_loop.py`. Shots: `review/baseline/0/`, hero 01, 02, 03.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Chevron wallpaper (yellow, all five parts and `-damp`) | gen_textures.py:pattern_chevron, :wallpapers, :damp | 0 wide-01..08, close-wall, cache-*, prop-1; hero 01, 02 | C | A yellow-green ground of value noise with a low-contrast chevron stamp; no paper grain, no seam between strips, no hue drift. Next to the vanilla wallpaper it reads as a flat colour. | Keep the chevron and the colour (lore). Paint it as printed paper: `matlib.paper` ground with fibre grain, a 1 px seam with a lifted edge every 16 px, slight hue drift between strips, and a darker scuffed band near the floor. Give the `-damp` copies real tide lines. | block/wallpaper/normal/blue1.png, block/wallpaper/aged/walnut.png | 1 |
| Other papers (manila, dotted, cream, stripped) | gen_textures.py:pattern_manila, :pattern_dotted, :pattern_cream, :pattern_stripped | manila in 0 refuge-wide, refuge-close (the spot is the Manila Room); cream (arch areas), dotted and stripped are not in any shot | C | Same construction as the chevron: one value-noise ground plus a pixel motif. | Same paper primitive. Add a spot: Level 0 near a stripped stretch and a dotted cell (pick a wide shot from `pick.py`). | block/wallpaper/aged-peeled/walnut1.png (for stripped) | 2 |
| Manila Room furnishing (wood floor, round table, chandelier) | floor: Level 0 wood floor block; table: gen_detail.py:level4 (roundtable); chandelier: gen_shapes.py:level5 (chandelier) | 0 refuge-wide, refuge-close | C | The floor reads as planks but each board is a flat fill; the round table is a flat slab on a post; the chandelier is a flat plate with glowing cubes. | Floor from `matlib.wood_planks`; table with an edge lip; chandelier as in B8. | block/wood/planks/oak1.png, block/metal/chandelier/ | 3 |
| Baseboard, chair rail, outlet | gen_textures.py:add_baseboard, :add_rail, :add_outlet | 0 wide-01..08 (baseboard), wide-03 (outlet); hero 01 | C (outlet D) | The baseboard is a flat 3 px dark-brown band with no top highlight or bottom shadow. The outlet is painted on the wall, so the plate and screws have no depth. | Bevel the baseboard: a 1 px lit top edge and a darker foot. Make the outlet a thin 1 px plate shape on the wall face (a wall decor box) instead of paint. | block/wood/planks/oak1.png (for the moulding tones) | 1 |
| *Carpet (normal, soaked, threadbare) | gen_textures.py:carpet, :carpet_threadbare | 0 wide-01..08, close-floor, threshold-*; hero 01, 02 | C | Tan speckle noise with a faint 4 px diagonal; no pile, no direction, no hue variation. It is a noise fill. | `matlib.carpet`: tufted pile with a nap direction, two-tone fibre hue, darker wear lanes. Keep the colour. Keep the rotation alternates. | block/cloth/smallcarpet/brown.png, block/cloth/wool/brown1.png | 1 |
| Carpet, stained | gen_textures.py:carpet("stained") | 0 wide-02 | D | The tile sheet shows the same 3x3 grid of blotches in every block, so a stained patch reads as a regular polka-dot grid. | One soft stain per texture at a random offset, crossing the edge seamlessly, and two or three alternates. | (none, overlay) block/overlay/grime/ | 1 |
| *Ceiling tile (1, 2, 3 and stain) | gen_textures.py:ceiling_tile | 0 wide-01..08, close-ceiling, close-light; hero 01, 02 | C | A flat cream square with worm specks. The T-bar grid is a 1 px dark line with no lit side, and the tile has no tegular edge shading. | Paint the tile as fissured mineral board with a soft recess at the edge (lighter on the lit side, darker on the other). Paint the T-bar as a 2 px light-grey rail with a highlight. Keep three alternates and the stain. | block/stone/plaster/plain.png, block/stone/plaster/square.png | 1 |
| *Troffer lights (on, off, dim, red) | gen_textures.py:troffer | 0 close-light, wide-*; hero 01, 02, 03 | C | A flat pale square with a faint diagonal. The prismatic lens has no grid and the housing frame is painted, not raised. | A lens with a visible prism grid (small cells) and a 2 px bevelled frame with a light rim. Better still, a recessed frame shape around the lens face. | block/glass/plain.png (for the lens), block/metal/sheet-plain/steel1.png | 1 |
| *Red Rooms wallpaper and red troffer | gen_textures.py:pattern_red, :troffer("red") | 0 redroom-wide, redroom-close; hero 03 | C | The same chevron construction in blood red. It reads as a red noise wall. | Use the same paper primitive as the chevron in this palette, with darker streaks. | block/wallpaper/normal/blue1.png | 2 |
| Arch areas (arch header, paper join) | gen_l0_walls.py:arch_header, :paper_join | Not in any shot. | not seen | Unknown. The preview (`props/block-1.png` archheader) shows an 8-step soffit with stepped pixels. | Add a spot: Level 0, under an arch looking along it, wide and close. Then judge the steps against vanilla stairs. | block/stone/plaster/plain.png | 2 |
| Supply boxes (box, torn box, flap) | gen_textures.py:box; gen_loop.py:torn_box_textures, :torn_box_shape | 0 cache-wide, cache-close, den-*; 1 cache-*; 3999 cache-close | C (torn inside D) | Flat tan cardboard with painted tape; no corrugation or edge wear. The torn box's straw and red wrapper are painted on the inside floor. | Cardboard: corrugation flutes at the edges, darker crushed corners, a tape strip with a sheen. Make the contents of the torn box a few small geometry pieces. | block/cloth/burlap/sides.png, block/wood/crate/label-empty.png | 1 |
| Threshold pits | (blocks use the carpet and wallpaper above) | 0 threshold-wide, threshold-close | C | The pits are carpet-lined holes; they inherit the carpet's flatness. | Fixed by the carpet row. Optionally add a darker AO band one block down the pit wall. | — | 3 |
| Concrete (Level 0 gate surround) | gen_textures.py:concrete | 0 gate-wide, gate-close | C | Grey noise with pores; the doorframe rust runs are paint. | Use `matlib.concrete` (aggregate, hairline cracks, darker borders). Shared with B4. | block/stone/polishedrock/andesite.png | 2 |

## B4 Level 1, and the shared camp kit

Generators: `tools/gen_textures.py` (Level 1 surfaces, crates, cars), `tools/gen_shapes.py` (level1, parking), `tools/gen_detail.py` + `tools/detail_textures.py` (level1, exit_signs, camp_tent, sleeping_bag), `tools/gen_lore.py` (cameras, traffic signs), `tools/gen_loop.py` (open crate). Shots: `review/baseline/1/`, hero 04, 05. close-wall, close-wall2 and close-ceiling are black (an unlit spot) and must be re-spotted. The camp kit also appears in Levels 0, 3, 4, 7, 8 and on the B4 hero 05, 10 and 16.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *White block wall (whiteblock, -base, -lintel) | detail_textures.py:level1 (L138-147, block_wall) | 1 wide-01..08, tent-*, den-*, cache-*, close-light; hero 05 | B | The README's own reference: structured blocks and mortar. The blocks themselves are flat fills with no lit top edge, and the grey dado band is a flat stripe. | Per-block shading from the shared `brick`/`block` primitive; keep the layout. | block/stone/brick/limestone1.png, block/clay/brick/four/running/ | 3 |
| *Concrete floor (plain, wet, dark, line, dash, arrows, oil, drain) and hall floor | gen_textures.py:concrete_base, :concrete_floor, :props_textures, :parking_textures; detail_textures.py:level1 (L148-153 l1hallfloor, L176-198 parkarrow/parkoil/parkdrain) | 1 close-floor, tent-close, wide-*, refuge-*; hero 04, 05 | D | tent-close shows the short scuff dashes at the same place in every block, so the floor reads as a grid; the rest is noise with pores and a tyre band. The drain grate is painted. | `matlib.concrete` (aggregate, hairline cracks, power-trowel swirl), scuffs at random positions with two or three alternates beside the rotations; the drain as an inset grate. | block/stone/polishedrock/andesite.png | 1 |
| *Concrete walls, pillars, bay letters, pillar light, ceiling | gen_textures.py:concrete_wall, :pillar, :pillar_light, :concrete_ceiling; gen_shapes.py:level1 (pillarlight, concretewall-damaged) | 1 refuge-*, gate-*, wide-* (pillars), close-light; hero 04 | C | Noise with tie holes. The bay letters read well. The conduit lines are painted on the ceiling beside a 3D conduit, and the damaged wall paints its rebar under 3D rebar. | `matlib.concrete` with form-board joints; drop the painted conduit and rebar. | block/stone/polishedrock/andesite.png | 1 |
| *Cars and wrecks | gen_textures.py:parking_textures, :car_wreck_textures; gen_shapes.py:parking | 1 refuge-wide (far), wide-*; hero 04 | B | The README's reference: ~68 elements with seams, handles and mirrors as geometry. The paint is a noise fill with grime blotches. | Paint with a soft top-to-bottom gradient and a clear-coat highlight on the bonnet and roof. | — | 3 |
| *Crates (closed, open) | gen_textures.py:crate; gen_loop.py:open_crate; blocktypes/level1/crate.json | 0 cache-close; 1 cache-*, prop-1, prop-2; 2 cache-close | C (open crate D) | Planks with seams but a flat fill per plank; the frame and diagonal brace are painted on a cube. The open crate's straw and nails are painted on its inside floor. | Frame and brace as raised boxes on a crate shape; planks with grain and a lit edge; open crate contents as a few boxes. | block/wood/crate/oak-sides.png, block/wood/crate/frame-generic.png | 1 |
| Metal shelving | gen_shapes.py:level1 (metalshelf) | 1 prop-2, cache-*, wide-06 | C | Grey posts and shelves of flat metal; no perforations, no lips. | Slotted uprights (painted holes are fine at this scale), shelf lips as 1 px boxes. | block/metal/sheet-plain/steel1.png | 2 |
| *EXIT signs (lintel, lintel pair, hanging) | gen_detail.py:exit_signs; detail_textures.py:shared (exithousing, exitface) | 1 close-light, wide-*; 0 gate-close; hero 05 | C | A white box with red EXIT letters; no housing bevel, no diffuser, no glow halo at range. | A housing with a 1 px bevel and a recessed face; letters with a halo (as the Level ! signs do). | block/metal/sheet-plain/steel1.png | 1 |
| *Camp tent (2x2) and old tent | gen_detail.py:camp_tent; detail_textures.py:level1 (tentfly, tentinside, tarp) | 1 tent-wide, tent-close; 7 tent-close-inspection; 8 wide-01..03, prop-2, tent-*; hero 05, 10, 16 | C | Real geometry (~55 boxes), but the gable ends are stepped boxes that show as a staircase, the fly is one flat green with painted seams, and the groundsheet is flat orange. Beside a vanilla lantern it reads as a toy. | Fly from `matlib.fabric` (ripstop weave, slight sag shading toward the ridge); smooth the gable with a rotated triangle of thinner steps; groundsheet with folds. | block/cloth/linen/green.png, block/cloth/burlap/sides.png | 1 |
| *Sleeping bag and bedroll | gen_detail.py:sleeping_bag, :level1 (bedroll); detail_textures.py:level1 (sleepingbag, sleepingbaglining, sleepingbagzip, bedroll, bedrollpillow) | 1 sleepingbag-*, tent-*; 3 sleepingbag-close; 4 refuge-*, sleepingbag-*; 7, 8; hero 10 | C | Faded red with dark quilting lines on every face; beside the vanilla lantern in Level 4 the bag has no folds or sheen. | Quilted fabric with a puffed shade per channel (lighter centre, darker seam), a lining with a different weave. | block/cloth/bed/ (vanilla bed), block/cloth/linen/red.png | 1 |
| *Burn barrel | gen_detail.py:level1 (burnbarrel); detail_textures.py:level1 (burnbarrel, burnbarrelrim, burnbarrelinside, embers) | 1 den-close; 8 wide-04, cache-wide, sleepingbag-wide | C | The octagon of plates and rims is good geometry; the steel is near-black noise with soot runs; little rust structure. | `matlib.rust` over painted metal, a lit rim. | block/metal/corroded/rusty1.png | 2 |
| Camp lantern, folding table and chair, workbench, toolbox, cardboard boxes, pallet, plywood | gen_detail.py:level1 (camplantern, foldingtable, foldingchair, workbench, toolbox, cardboardboxes, pallet, plywood); detail_textures.py:level1 (L219-250) | 1 den-close, wide-05 (plywood), sleepingbag-close; 8 wide-06 | C | Plain boxes; the pegboard's tools and the toolbox latches are painted. | Table with legs of thickness and a top lip; tools as small geometry. | block/wood/table/normal/ | 2 |
| First-aid rooms (hospital bed, medical cabinet) | gen_detail.py:level1 (hospitalbed, medcabinet); detail_textures.py:level1 (L330-349) | not in any shot | not seen | The preview shows the cabinet's cross, handle and seam painted. | Add a spot: Level 1 first-aid room (WorldLayout.Level1.cs places them), wide and close. Cabinet door as an inset with a handle box. | block/cloth/bed/mattress-normal.png | 2 |
| Wall decorations (power box, breaker, outlet, extinguisher, alarm, hose cabinet, level signs, stairs sign, banners, paintings) | gen_detail.py:level1 (l1deco, concretedeco, pillardeco); detail_textures.py:level1 (L351-476) | 1 wide-03, wide-08, den-wide (banner) | C (breaker, hose cabinet, alarm D) | Breaker switches, hose reel and alarm pull handle are painted on plates. Level signs and banners read. | Switches as toggles, the reel as a ring of boxes behind glass, the pull handle as a box. | block/metal/sheet-plain/steel1.png | 2 |
| Metal doors, fire doors | gen_detail.py:doors (metaldoor, firedoor); detail_textures.py:level1 (L155-174) | 1 wide-03, wide-05, wide-08 | D | `metaldoor` is a cube with the frame, push bar, wired glass, lever and kick plate all painted. The fire door has a real frame. | A door shape: frame, leaf, push bar, window inset. | block/metal/door/ | 1 |
| Cameras and traffic signs | gen_lore.py:textures, :level1 | not identifiable in any shot | not seen | Lens painted on a box face. | Add a spot: Level 1 camera on a pillar, close. Lens as a short cylinder with a glass disc. | — | 3 |
| Parking furniture (wheel stops, speed bumps, pay station, cones, clearance bar) | gen_textures.py:parking_textures (wheelstop); detail_textures.py:level1 (speedbump, paybody, payface, conewhite); gen_shapes.py:parking (wheelstop) | 1 prop-1, refuge-*; hero 04 | C (pay station D) | Hazard-striped wheel stops read; the pay station's keypad, slot and coin return are painted. | Pay station face as geometry; wheel stops with rounded top shading. | — | 2 |

## B5 Level 2

Generators: `tools/gen_textures.py`, `tools/gen_shapes.py`, `tools/gen_lore.py`. Shots: `review/baseline/2/`, hero 06, 07. Level 2 is dark by design; wide-05..07 are too dark to judge and the close shots often have pipes in front.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Tunnel walls (plain, brick, warning) and ceiling | gen_textures.py:tunnel_concrete, :tunnel_wall, :tunnel_ceiling, :props_textures (tunnelwall-warning) | 2 wide-01..08, close-wall, gate-*, den-*; hero 06, 07 | C | Dark grey value noise with pores, tie holes and two water streaks; no aggregate or form-board seams. The brick variant is dark staggered rectangles with no per-brick shading. The ceiling paints a rust pipe band beside the real 3D pipes. | `matlib.concrete` with form-board joints every 16 px and efflorescence at the joints; brick from a shared `brick` helper (lit top edge, dark bed joint, hue per brick). Drop the painted pipe band from the ceiling. | block/stone/polishedrock/andesite.png, block/clay/brick/four/running/ | 1 |
| *Machinery wall and machine cabinet | gen_textures.py:tunnel_wall("machinery"), :props_textures (props/cabinet-front); gen_shapes.py:level2 (tunnelwall-machinery, machinecabinet) | 2 wide-01, wide-03, wide-04, den-wide, tram-wide, prop-1; hero 07 | D | The gauges, needles, vent slots and labels are painted on a flat panel. This is the clearest painted-on 3D in the mod, and it is in a hero shot. | Gauges as geometry (`dial`/`gauge` helper from B2: bezel ring, glass, needle box), vents as a `grille(bars)`, labels as thin plates, the panel as `inset_panel` with a bevelled door seam. | block/metal/sheet-plain/steel1.png, block/metal/riveted/iron1.png | 1 |
| Ceiling pipe bundles and tunnel lights | gen_textures.py:pipe_tex; gen_shapes.py:level2 (pipes-*, tunnellight-*) | 2 wide-01..08, close-ceiling, close-light | B | The banded pipe() shading works. The flanges and bolts are painted on the pipe skin, and the tube fixture is a flat box with a glowing face. | Add flange rings as 0.5 px collars. Make the light a housing with a diffuser plate. | block/metal/plate/copper.png | 3 |
| *Wall pipes (round, corners, caps, brackets, valves, risers) | gen_textures.py:wall_pipe_tex, :wall_pipe_flange; gen_shapes.py:round_pipe, :wall_pipe_turning, :wall_pipe_cap, :wall_pipe_corners, level2 (tunnelwall-pipes*, riser*, valve) | 2 wide-*, pipecorner-*, pipewrap-*, pipeend-*; 3 the same; hero 06, 07, 09 | B | At the README's standard: shaded, round, flanged. At 1.5 blocks the 7 slabs read as a faceted cylinder, and the lagged pipe's straps are painted. | Keep. Re-judge after the lighting of B2's primitives; possibly 9 slabs. | block/metal/plate/copper.png | 3 |
| Oil drums | gen_textures.py:drum | 2 wide-02, wide-05 (blue drums) | C | The hoops, lid ring and bung are painted on a box. | Hoops as 0.5 px rings; lid as an inset disc; per-face shading. | block/wood/barrel/ (barrel hoops) | 2 |
| *Steel doors (tunnel door, white, grey, cream) | gen_lore.py:tunnel_door, :textures | 2 (not clear in any frame); 3 threshold-wide | D | The lever handle, kick plate and wired-glass window are painted on the door face. | A door shape with a handle box, a raised kick plate, and an inset wired-glass window with a 1 px frame. | block/metal/door/ (vanilla iron door) | 2 |
| *Tram (dead tram front, rear, wagon, trolley) and rails | gen_lore.py:tram_textures, :tramway (deadtram-*, tramwagon, trolley, tramrails-*) | 2 tram-wide, tram-close, wide-01..03 (rails), close-floor; hero 06 | D (tram) / C (rails) | The grille and windows are painted on the body box, and the body is one flat green with a painted yellow band. The rails are rusty boxes on sleepers; they read but are flat. | Windows as inset panes with frames; grille as bars; headlamp as a bezel; a lit roof edge and darker skirt. Rails: a rail profile (head, web) and sleepers with wood grain. | block/metal/riveted/iron1.png, block/wood/planks/oak1.png (sleepers) | 1 |
| Clutter (machine parts, gear, candle stubs, cartons) | gen_lore.py:textures (gearflat, candlewax), :level2 (machineparts, candlestubs) | 2 gate-wide, cache-close | C | The gear is drawn on a flat 1.2 px box; the parts are small flat boxes. | Gear as a ring of tooth boxes; candles with a drip lip; per-face shading. | block/candle.png | 3 |
| Wooden crates (Level 2 caches) | gen_textures.py:crate (see B4) | 2 cache-close, wide-01 | C | See B4. | See B4. | block/wood/crate/oak-sides.png | — |
| Floor (gravel concrete) | gen_textures.py:tunnel_concrete or concrete (Level 2 floor) | 2 close-floor, wide-* | C | Brown-grey noise. | `matlib.concrete` with grit and oil stains. | block/stone/gravel/ | 2 |

## B6 Level 3

Generators: `tools/gen_textures.py`, `tools/gen_shapes.py`, `tools/gen_blocktypes.py`, `tools/gen_lore.py`, `tools/gen_detail.py` (sanctum). Shots: `review/baseline/3/`, hero 08, 09. close-floor, den-wide, den-close and pipeend-close are black and must be re-spotted.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Walls: brick, glazed tile, cinder | gen_textures.py:level3_textures (l3wall-brick, l3wall-glazed, l3wall-cinder) | 3 wide-01..08, close-wall, close-wall2, pipe*; hero 09 | C | Structured (bricks, courses) but each brick is a flat fill with no lit edge. The glazed tile's 8 px courses read as big tan bricks, about twice the scale of vanilla brick. Cinder is noise with lines. | One shared `brick` primitive (B2) with per-brick shading and hue. Glazed tile: a highlight on each tile's top edge and a crazed glaze. Cinder: 16x8 blocks with pitted faces. | block/clay/brick/four/running/, block/stone/brick/sandstone1.png | 1 |
| Floor, plaster ceiling, cables, insulators | gen_textures.py:level3_textures (dustyfloor, plasterceiling, cable, insulator) | 3 wide-*, close-light (close-floor is black) | C | Noise fills with one blotch. | `matlib.concrete`/`plaster`; cables with a lit stripe. | block/stone/plaster/plain.png | 2 |
| Electrical panel, fan, transformer | gen_textures.py:level3_textures (panel, fan, transformer); gen_shapes.py:level3 (transformer), walls (l3wall-*-panel, -fan) | 3 wide-03, wide-05, wide-06, cache-wide (fan), threshold | D | The breakers and the fan grille are painted; the transformer paints its fins over 3D fins. | Breakers as small toggle boxes in an inset panel; the fan grille as `grille(bars)`; delete the painted fins. | block/metal/sheet-plain/iron1.png | 2 |
| Iron bars, manhole, ladder rungs | gen_textures.py:bars_steel, level3_textures (manhole); gen_shapes.py:level3 (ironbars, manhole, rungs) | 3 sleepingbag-wide, threshold-wide | B (bars) / C | The bars are shaded analytically and read as round. The manhole's ring and bars are painted. | Manhole as a ring of boxes with an inset lid. | block/metal/fence/ | 3 |
| Room plaques and OUT OF BOUNDS plaque | gen_textures.py:level3_textures (roomsign-N); gen_lore.py:textures (plaque), :level3 | 3 cache-wide (318) | C | White plate with text, screws painted; reads at 2 blocks. | A 1 px plate with a bevel and screw heads as geometry. | block/wood/sign/ | 3 |
| Cable trays and hanging lights | gen_shapes.py:level3 (cables-*, cablelight-*) | 3 close-light, pipecorner-wide | C | Flat boxes; the tube is one glowing box. | Tray with lips, cables round-shaded, the light with a housing. | block/metal/sheet-plain/steel1.png | 3 |
| Window glow | gen_textures.py:level3_textures (windowglow) | not seen in any shot | not seen | Painted frame and mullions on a glowing pane. | Add a spot: Level 3 near a lit window wall. Frame as geometry. | block/glass/plain.png | 3 |
| *Sanctum (refuge): sandstone walls, red runner, candelabras, coffered vault ceiling | gen_detail.py:level3 (sanctumstone, l3floor-carpet, candelabra, sanctumceiling-vault/-boss); detail_textures.py:level3 (sanctumwall, sanctumcarpet, sanctumvault, l3stone, stone) | 3 refuge-wide, refuge-close; hero 08 | C | Sandstone block wall is flat beige rectangles; the runner is flat red with painted gold bands; candelabras are thin boxes with glow cubes. The vault's stepped haunches and ribs are real geometry (good). | Sandstone as `matlib` ashlar with chisel marks; the runner as carpet pile with a woven border; candelabras with a drip pan and a stem with thickness. | block/stone/brick/sandstone1.png, block/cloth/rug/red/ | 2 |
| Angel statue | gen_detail.py:level3 (angelstatue, ~35 boxes); detail_textures.py:level3 (stone, stonewing, stonefold, pedestal) | 3 refuge-wide (far, end of the hall); hero 08 | not seen close | Visible only as a silhouette. | Add a spot: Level 3 Sanctum statue from 2 blocks. | block/stone/polishedrock/limestone.png | 2 |
| Machine-room props (generator, control desk, switchgear, floor fan, coil unit, conveyor, cable spool) | gen_detail.py:level3 props (L740-865); detail_textures.py:level3 (generatorpanel, controlpanel, switchgear*, fancage, conveyorbelt) | 3 prop-2, wide-05 (far); previews in props/block-detail-3 | D | The generator panel, control desk, switchgear dials and the floor fan's grille are painted on flat plates. | `dial`/`grille` geometry from B2; buttons as small boxes. | block/metal/sheet-plain/iron1.png | 2 |
| Wall decorations (gauges, knife switch, junction box, burnt outlet, bulkhead light, alarm bell, danger sign) | gen_detail.py:level3 (Decor list L676-735); detail_textures.py:level3 (gauge, dangersign, outletburnt, bulkheadglass) | 3 wide-03, wide-05, wide-06, sleepingbag-close | D (gauges) / C | The gauge dial is painted on a plate; the bulkhead light's cage is geometry (good). | Gauge as geometry. | — | 2 |
| Boilers and vault (lore list) | gen_shapes.py:level5 (boiler, line ~935) and gen_blocktypes.py (`level5/boiler`, line ~372); the Level 3 boiler rooms reuse the Level 5 boiler (gate note) | not seen | not seen | — | Add a spot: Level 3 boiler room (and the Sanctum vault). Judge with the B8 boiler row. | block/metal/riveted/iron1.png | 3 |
| The Purpified (wall growth) | gen_detail.py:level3 (purpified decor, 13 boxes + stain decal); detail_textures.py:level3 (purpskin, purpwall-lower/upper) | 3 purpified-wide, purpified-close | C | A purple noise blob with a few dark lines; reads as a stain, not a growth. | Veined, wet-looking skin with a raised lump shape and a glowing pore or two. | block/creature/rot/ | 3 |
| Sleeping-bag cell (gauges on cabinets) | gen_shapes.py:level2 (machinecabinet) reused | 3 sleepingbag-close | D | Painted gauges again. | Fixed by the B5 cabinet row. | — | — |

## B7 Level 4

Generators: `tools/gen_textures.py` (level4_textures), `tools/gen_shapes.py` (level4), `tools/gen_detail.py` + `tools/detail_textures.py` (office clutter, portraits, cable droops, hotel-red ramp). Shots: `review/baseline/4/`, hero 10.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Office wall, carpet (plain, ghost), laminate | gen_textures.py:level4_textures (officewall, officecarpet-*, laminate) | 4 wide-01..08, close-wall, close-floor; hero 10 | C | close-wall shows nothing but even noise; the carpet is a grey-beige noise fill. Whole rooms of it. | Wall as `matlib.plaster` painted (very low-amplitude roller texture, scuffs at hip height, a darker band at the floor). Carpet as `matlib.carpet` loop pile in a grid of 2x2-block carpet tiles with slightly different nap direction (alternates). | block/stone/plaster/plain.png, block/cloth/wool/gray1.png | 1 |
| *Office ceiling tile, vent, sprinkler, stain; troffer | gen_textures.py:level4_textures (officeceiling, officelight-*); detail_textures.py (officeceiling-vent, -sprinkler, -stain) | 4 close-ceiling, close-light, wide-*; hero 10 | C (vent D) | 2x4 tile with a 1 px grid. The diffuser vent is concentric painted squares and the sprinkler is a painted dot. | Share the B3 ceiling tile and T-bar. Vent and sprinkler as small geometry (louvred box, a sprinkler head). | block/stone/plaster/square.png | 1 |
| Cubicle partitions | gen_textures.py:level4_textures (partition); gen_shapes.py:level4 (partition) | 4 prop-1, wide-02, wide-05, wide-07, hotelturn-*; hero 10 | C | A 2-element grey box with a faint basket weave; no metal frame, no top cap, same texture on top and sides. | `frame_and_panel`: aluminium top cap and end posts, fabric panel inset 1 px with `matlib.fabric`. | block/cloth/wool/gray1.png, block/metal/sheet-plain/steel1.png | 1 |
| Desks, chairs, filing cabinets, CRT, water cooler, vending machine, conference table | gen_textures.py:level4_textures (crt, crt-screen, chairfabric, filing, cooler, vending); gen_shapes.py:level4 (desk, officechair, filingcabinet, watercooler, vendingmachine, conferencetable) | 4 prop-2, wide-08, refuge-*, sleepingbag-wide; hero 10 | C (vending D) | Plain boxes, same flat texture on all faces. The vending machine's window, bottles and coin slot are painted on one box. The filing cabinet's drawers are painted seams. | Desk with a top slab overhang, modesty panel and drawers as inset boxes; chair with a seat cushion, back and a 5-star base; vending machine with an inset glass window and shelves of bottle boxes behind it. | block/wood/table/normal/, block/wood/cabinet/1block/ | 1 |
| Elevator doors and floor indicator | gen_textures.py:level4_textures (elevatordoor-*); gen_detail.py:doors (lift, header, dial); detail_textures.py:level4 (L727-754) | 4 threshold-wide, threshold-close; 11 threshold-* | C | Brushed-steel noise with a centre seam; the frame is flat grey. Indicator readable. | `matlib.brushed_metal` with vertical grain; the frame as a bevelled surround shape. | block/metal/sheet-plain/steel1.png | 2 |
| Office windows (rain, blinds, blackout) | gen_textures.py:level4_textures (officewindow); gen_detail.py:level4 (officewindowalt); detail_textures.py:level4 (L686-702) | 4 hotelturn-wide, hotelturn-close | D | The rain window reads as TV static at range (60 random streaks on grey). | Glass with a sky gradient and a few long rain runs; a frame as geometry. | block/glass/plain.png | 2 |
| Office clutter: paper scatter, ficus, chair stack, copier, bookshelf, server rack, kitchen counters, fridge, reception, wall decor (clock, whiteboard, corkboard, phone, light switch) | gen_detail.py:level4 (cubes L871-881, officedeco L883-908, props L910-983); detail_textures.py:level4 (L660-887) | 4 wide-01, wide-05, cache-wide, prop-2 | C (copier, microwave, server D) | Paper sheets are flat white pixels; the copier panel, microwave window and keypad, server LEDs and cabinet handles are painted; the fridge is flat white. | Paper with a fold shadow; appliance fronts as inset panels with button boxes. | block/cloth/paper/blank-small.png | 3 |
| Portraits and wall pictures | gen_detail.py:level4 (officedeco poster0-2), :level1 (painting0-3); detail_textures.py:level4 (L807-813), :level1 (L376-406) | 4 wide-01 (red abstract), cache-wide | C | Frames are painted borders on a flat plate. | Frame as 4 bevelled strips (like the Level 5 portrait); canvas with a varnish sheen. | block/painting/ | 3 |
| Hotel-red ramp blocks (Level 4 to 5 seam) | reuses the Level 5 textures (gen_textures.py:damask_panel, :level5_textures) | 4 gate-wide, gate-close, hotelturn-* | C | See B8 (wainscot and damask). | Fixed in B8. | — | — |
| Camp kit in the refuge (bedroll, crates) | see B4 | 4 refuge-*, sleepingbag-* (next to a vanilla lantern) | C | The bedroll beside the vanilla lantern is the clearest context test: the lantern has shading and metal; the bedroll is flat red with dark stripes. | See B4. | block/cloth/bed/ | — |

## B8 Level 5

Generators: `tools/gen_textures.py` (level5_textures, damask_panel, portrait), `tools/gen_shapes.py` (level5), `tools/gen_blocktypes.py`, `tools/gen_detail.py` + `tools/detail_textures.py` (key rack, number plates, elevators, staircases). Shots: `review/baseline/5/`, hero 11, 12.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Damask wall panel (64 px) and frieze | gen_textures.py:damask_panel, :level5_textures (hotelwall-frieze) | 5 close-wall, gate-*, threshold-*, cache-*, wide-06..07; hero 11, 12 | C | The damask itself is structured and good. The gilt frame's bevel is painted on a flat wall, and every block repeats the same panel at the same place, so a corridor is a row of identical framed squares. The frieze is a flat cream band. | Make the gilt frame a 1 px raised moulding shape (`frame_and_panel`) and keep the damask as the inset. Two or three damask alternates that shift the pattern phase. Frieze with a cornice shape. | block/wallpaper/normal/blue1.png, block/metal/plate/brass.png | 1 |
| Wainscot | gen_textures.py:level5_textures (hotelwall-wainscot) | 5 every corridor shot; hero 12 | C | The moulded panel is painted on mahogany noise. | `inset_panel` geometry with `matlib.wood_planks` (mahogany grain). | block/wood/planks/oak1.png (structure), block/wood/cabinet/ | 1 |
| *Hotel carpets (damask medallion, maroon, lobby) | gen_textures.py:level5_textures (hotelcarpet-*) | 5 close-floor, every corridor shot, frontdoor; hero 11, 12 | C | The medallion carpet is a clean pattern but with no pile: flat red with crisp gold rings. Repetition is by design. | Pile texture under the pattern (`matlib.carpet` as a base, pattern multiplied in), slight wear in the walking line. | block/cloth/rug/red/, block/cloth/mediumcarpet/blue.png | 1 |
| Hotel floorboards and ceiling (cream, beams, coffers) | gen_textures.py:level5_textures (hotelwood, hotelceiling-*); gen_shapes.py:level5 (hotelceiling-beam, -beamcross, -coffer) | 5 wide-01..05 (floor), refuge-*; hero 11 | C | The floor is brown noise with dark board lines, no grain, no stagger. The ceiling is flat cream; the beams are plain boxes. | `matlib.wood_planks` (grain, staggered ends, knots); beams with a chamfer. | block/wood/planks/oak1.png | 1 |
| Red marble pillars | gen_textures.py:level5_textures (marble) via texlib.py:marble | 5 close-wall2, frontdoor-*; hero 11 | B | At the README's standard. The veins are wide at 1.5 blocks. | Keep. | block/stone/polishedrock/redmarble.png | 3 |
| *Hotel doors and number plates (201-208, 666) | gen_textures.py:level5_textures (hoteldoor-lower, hoteldoor-upper0..9); gen_blocktypes.py (hoteldoor) | 5 door666-wide, door666-close; hero 12 | D | The panel mouldings and the brass plate are painted (with a highlight line) on a flat 64 px door. | A door shape with two inset panels, a raised brass plate with screws as geometry, and a knob. Keep the numbers as text. | block/wood/door/plain/, block/metal/plate/brass.png | 1 |
| Cage door / elevator gate | gen_textures.py:level5_textures (cagedoor-*); gen_detail.py:doors (cagelift); detail_textures.py:level5 (cagegate-*, cagedial-*, L905-927) | 6 gate-close-inspection (lattice); 5 not seen | D | The copper lattice is painted on a cube. | A lattice of thin bars as geometry with the shaft visible behind. | block/metal/fence/ | 2 |
| Furniture: dining chairs and tables, bed, nightstand, wardrobe, wing chair, sofa, mahjong table, turntable, palm | gen_shapes.py:level5 (bed-*, nightstand, wardrobe, wingchair, sofa, mahjongtable, turntable, pottedpalm); level5_textures (velvet, linen, mahogany, blanket, palmleaf, pot, felt) | 5 wide-01..05 (dining), prop-2, threshold-wide, refuge-close; hero 11 | C | Boxes with one flat texture each: the dining chair is a tall red box, the table a white box. The wardrobe's seam and handles are thin boxes (good). | Chairs with legs, seat cushion, back frame; tables with a cloth drape edge; `matlib.fabric` velvet with sheen. | block/wood/chair/normal/, block/wood/table/normal/ | 1 |
| Chandeliers, sconces, dome lights, floor lamps | gen_shapes.py:level5 (chandelier, hotelfixture-sconce, domelight-*) | 5 wide-01..05, close-light; hero 11 | C | Chandelier is a flat gold plate with glowing cubes; the dome light preview is a full cream cube. | Chandelier as arms and a ring with candle cups (the vanilla chandelier has the style); sconce with a backplate and a shade. | block/metal/chandelier/ | 2 |
| Staircases (marble, runner) | gen_shapes.py:level5 (hotelstairs-*) | 5 frontdoor-wide; hero 11 | C | The runner is flat red with a painted rod; the preview shows black triangles (preview artifact). | Stair rods as geometry; runner with pile. | block/stone/polishedrock/ | 2 |
| Portrait, Beverly sign, staff sign | gen_textures.py:portrait, level5_textures (beverly, staffsign); gen_shapes.py:level5 (hotelfixture-portrait, -beverly) | 5 door666 (landscape), sleepingbag-wide | B (portrait) / C (signs) | The portrait painting is good and its frame is 4 strips. The signs are flat. | Signs with a bevel and screws. | block/painting/ | 3 |
| Boiler bays (boiler, furnace) | gen_textures.py:level5_textures (boiler, fire); gen_shapes.py:level5 (boiler, furnace) | not in any shot | not seen | The preview shows a brown box with a painted rivet grid. | Add a spot: Level 5 boiler bay. Riveted plates from `matlib.painted_metal` and rivets as a texture with lit tops. | block/metal/riveted/iron1.png | 2 |
| Key rack, hotel wall decorations (phone, speaker, clock, call plate, mirror, fire hose) | gen_detail.py:level5 (hoteldeco L1026-1044, keyrack ~35 boxes); detail_textures.py:level5 (speakergrille, phonedial, ornateclock, callplate, hotelhosecab, mirrorglass) | not in any shot | not seen | The key rack is real geometry (its old `keyrack` texture, detail_textures.py:level5 L969-981, is orphaned). The speaker grille, phone dial and clock face are painted. | Add a spot: Level 5 front desk and a corridor with the house phone, close. Delete the orphan texture. | block/wood/shelf/wood.png | 3 |
| Hotel props (console table, bookshelf, curio cabinet, luggage cart, trolley, radiator, writing desk, grandfather clock, reception, piano, dining table) | gen_detail.py:level5 (props L1061-1174), :long_sofa; detail_textures.py:level5 (books, curioglass, clockface-old, pianokeys, receptionmahogany, radiator) | 5 wide-01..05 (dining tables), frontdoor-close (reception) | C | Plain boxes; books, curio contents and piano keys are painted (acceptable for books at this scale). | Mahogany from `matlib.wood_planks`; reception with inset panels. | block/wood/bookshelves/bookshelf.png | 2 |

## B9 Levels 6 and 6.1

Generators: `tools/gen_deep.py` (level6, level61, refinements), `tools/deep_textures.py` (level6, level61). Shots: `review/baseline/6/` (judge on the `-inspection` shots; wide-01..08 and the close shots are black by design) and `review/baseline/6.1/`, hero 13, 14. In 6.1, gate-*, threshold-* and sleepingbag-* are black and must be re-spotted.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Level 6 walls, floor, ceiling, wet floor | gen_deep.py:level6 (l6block); deep_textures.py:level6 (L33-40), :refinements (L799-803) | 6 wide-01..04-inspection, close-wall-inspection, close-floor-inspection, close-ceiling-inspection; hero 13 | C | Dark slate panels with faint dashes; the floor is grey noise. Dark by design, so the flatness shows only under the lantern. | Cold concrete from `matlib.concrete` with panel joints and damp; keep the darkness. | block/stone/polishedrock/andesite.png | 2 |
| Chalk marks and handprints | gen_deep.py:level6 (l6deco, chalkmark); deep_textures.py:level6 (L42-79) | 6 sleepingbag-close-inspection (DEAD END); hero 13 | B | Readable chalk decals with a dusty edge. | Keep. | — | 3 |
| Light switches (dead switch, office switch) | gen_deep.py:level6 (deadswitch); gen_detail.py:level4 (switch); detail_textures.py:level4 (switchplate, L801-806) | not in any shot | not seen | — | Add a spot: Level 6, a dead switch on a corridor wall, close with the lantern (inspection). | — | 2 |
| *Snackrooms walls (mall, panel, tile, window) | gen_deep.py:level61 (L141-159); deep_textures.py:level61 | 6.1 wide-01..08, close-wall, refuge-*; 6 refuge-*; hero 14 | C | Flat mint with pink stripes in value noise; the wood panel valance is flat. | Painted plaster with the stripes as a slightly raised dado rail shape; a scuffed lower band. | block/stone/plaster/plain.png | 1 |
| *Snackrooms floors (terrazzo, checker, quarry) | gen_deep.py:level61; deep_textures.py:level61 | 6.1 close-floor, wide-03, wide-04, wide-07, prop-*; hero 14 | C | Terrazzo is single-pixel specks on cream (it reads, but there are no chips of different sizes and no polish); the checker is pure black and white squares with no grout or wear; quarry tile is good-ish. | Terrazzo with chips of 1-3 px in four hues and a polish highlight; checker with off-white and charcoal, grout and scuffs. | block/stone/tiles/travertine1.png | 1 |
| *Snackrooms ceiling grid and skylight | gen_deep.py:level61 (snackceiling); deep_textures.py:level61 (L126-140) | 6.1 close-ceiling, close-light, wide-*; hero 14 | C (skylight D) | The grid tile is flat; the skylight's panes, mullions and glowing frame are painted on a tile. | Share the B3 ceiling tile; the skylight as a recessed box with a mullion cross and a lit pane. | block/glass/plain.png | 2 |
| *Store fixtures (counters, food case, stove, fryer, shelf, café tables and chairs) | gen_deep.py:level61 (L170-201); deep_textures.py:level61 (L174-217) | 6.1 wide-01..08, prop-1, prop-2; hero 14 | C (food case, stove D) | Navy fabric chairs and tables are flat boxes on chrome legs; the till, the food case's pastries, the burners, knobs and fryer mesh are painted. | Chairs with a padded seat and back (`matlib.fabric`), stove knobs and burners as geometry, pastries as small boxes behind glass. | block/wood/chair/normal/ | 1 |
| *Snack machine and drinks fridge | gen_deep.py:level61 (snackvending, drinkfridge); deep_textures.py:level61 (L218-295) | 6.1 vendingroom-close, wide-01, wide-02; hero 14 | B | Deep glass fronts with real packet and can boxes on shelves (26 and 40 elements). The keypad, coin slot and price display are painted. The old `drinkfridge` texture (L258-265) is orphaned. | Keypad as a small plate with button boxes. Delete the orphan. | — | 3 |
| Vending rooms (dead machines, vending piles) | gen_deep.py:dead_machine, :vendingpile; deep_textures.py:level61 (L296-323) | 6.1 vendingroom-wide | C | Re-posed machine boxes; fine at range. | Inherit the snack machine fixes. | — | 3 |
| Planters / ficus | gen_detail.py:level4 (ficus); detail_textures.py:level4 (ficusleaves, planter) | 6.1 wide-06, wide-08; 4 | C | Foliage is stacked olive cubes, which reads as blocky next to vanilla leaves. | Crossed leaf planes with an alpha leaf texture (as vanilla plants do). | block/plant/potted/ | 2 |
| Store signs and menu board | gen_deep.py:level61 (snackdeco); deep_textures.py:level61 (L324-345) | 6.1 wide-05, wide-06 | B | Readable glowing signs. | Keep. | — | 3 |

## B10 Levels 7 and 8

Generators: `tools/gen_deep.py` (level7, level8, refinements), `tools/deep_textures.py` (level7, level8), `tools/gen_lore.py` (seeps). Shots: `review/baseline/7/` (use the `-inspection` shots) and `review/baseline/8/`, hero 15, 16, 17. Level 7 gate-*, tent-close and close-water are black.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Island rock / basalt (also the sea stacks) | gen_deep.py:level7 (islandrock); deep_textures.py:level7 (L383-411) | 7 wide-01-inspection, wide-04-inspection, close-floor-inspection, cache-close-inspection, seapillar-*; hero 15 | D | Voronoi facets with cracks and lit lips, but one dark diagonal crack crosses the whole texture, so even with the four rotations every block shows the same crack and a stack reads as a grid of identical cubes. | Facets without a dominant crack; two or three seeds as alternates (beside the rotations); basalt column joints on the side faces. | block/stone/rock/basalt1.png | 1 |
| Tar | gen_deep.py:level7 (tar); deep_textures.py:level7 (L412-450) | not in any shot | not seen | — | Add a spot: Level 7 tar pool near the shelter, inspection. | — | 3 |
| *Fort Surrender (the junk pile) | no generator of its own: filing cabinet (gen_shapes.py:level4), hotelchair and hotelbookshelf (gen_detail.py:level5), wardrobe (gen_shapes.py:level5), bedroll and camp lantern (gen_detail.py:level1); placed by WorldLayout.Level7.cs:Shelter | 7 shelter-*, seapillar-*, wide-03-inspection; hero 15 | C | Inherits the furniture of B7 and B8: flat boxes with painted drawers and books. | Fixed by the B7/B8 furniture rows; re-judge here. | — | 2 |
| Seabed clutter (bones, ribcage, jaw, scrap, backpack, wreck crate), jetty, driftwood, buoy | gen_deep.py:level7 (L331-363), :refinements (jetty, driftwood, buoy); deep_textures.py:level7 (wetwood L458-462), :refinements (jetty L806-811) | 7 sleepingbag-close-inspection (jetty), shelter-close | C | The wreck crate is one box with its plank frame and brace painted. | Share the B4 crate. | block/wood/crate/oak-sides.png | 3 |
| *Settlement tents, bedrolls, crates, barrels | see B4 (camp kit) | 8 wide-01..06, tent-*, cache-*; hero 16 | C | See B4. | Fixed by B4. | — | — |
| *Road lamps | gen_deep.py:level8 (roadlamp, roadlamparm); deep_textures.py:level8 (lampglass L475-477) | 8 wide-03, wide-05, prop-1, tent-close, sleepingbag-wide; hero 17 | C | 14-box caged lantern on a post (good geometry), but the post is flat dark grey and the glass a flat cream panel. | Painted-metal post with a lit edge; glass with a glow gradient and a frame shadow. | block/metal/lantern/iron.png | 2 |
| *Glowcaps | gen_deep.py:level8 (glowcap, glowcap_floor, glowcap_wall); deep_textures.py:level8 (L479-495) | 8 glowcaps-wide, glowcaps-close, wide-08; hero 17 | C | Caps are boxes with a rim outline and specks; at range they read as orange cubes. | Domed caps (stepped boxes), gills as a darker skirt texture, a soft glow gradient. | block/plant/mushroom/ | 2 |
| Cave walls, moss and hay walls in the refuge corridor | (vanilla rock plus mod blocks in the refuge) | 8 refuge-wide, refuge-close, wide-05 | C | The refuge corridor's walls are a huge-grain green noise that reads as a blur at 1 block. | Identify the block (likely a mod hedge or moss block) and use a leaf/moss alpha texture. | block/plant/leaves/ | 2 |
| M.E.G. marker and signs | gen_deep.py:level8 (megmarker); deep_textures.py:level8 (megplate L468-474) | 8 wide-01, wide-08, prop-2, tent-wide | C | A flat plate on a post. | Plate with a bevel and bolts. | block/wood/sign/ | 3 |
| Almond Water seeps | gen_lore.py:textures (almondseep, seepstain, seeppool...), :level8 | not in any shot | not seen | — | Add a spot: Level 8 seep (`/backrooms nearest` has no seep target; take the nearest from discovery or WorldLayout.Level8). | — | 3 |
| Ore veins, domes | none (vanilla ores; terrain shape) | — | — | Out of scope for this pass. | — | — | — |

## B11 Levels 9 and 10

Generators: `tools/gen_deep.py` (level9, level10, refinements), `tools/deep_textures.py` (level9, level10, shingles, refinements), `tools/gen_city.py` (barn noclip wall). Shots: `review/baseline/9/` (night by design: every wide shot is under grass at night), `review/baseline/10/`, hero 18, 19, 20, 21, 22. Add two or three day spots in Level 9 facing a house from the street (`/time set 12:00`), like hero 19 and 20.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *House exteriors: siding and brick (housewall, housecorner) | gen_deep.py:level9 (L475-485), :refinements (housecorner); deep_textures.py:level9 (L549-557) | 9 close-wall, close-wall2, l9house-*, prop-2; 94 wide-01, close-wall2; hero 18, 19, 20 | C (brick B) | Clapboard is flat colour with dark lap lines and no shadow under each board; the brick (block_wall) is structured but flat per brick. | Lap siding with a lit top and a shadow under each board and slight paint wear; brick from the shared brick primitive. | block/wood/planks/oak1.png (for lap shading), block/clay/brick/four/running/ | 1 |
| *Roofs (slopes, shingles, flat roof) | gen_deep.py:level9 (L508-526), :refinements (roofslope); deep_textures.py:shingles | 9 l9house-wide, den-wide, cache-wide; hero 19, 20 | B | Shingle tabs with per-tab shading read well in hero 19. | Keep; check the eave edge at close range. | block/clay/shingles/red.png | 3 |
| *Windows (housewindow dark, lit) | gen_deep.py:level9 (L489-507); deep_textures.py:level9 (L581-613) | 9 close-wall, l9house-*; hero 19, 20 | B | The README's reference: frame the depth of the wall, glass recessed, bars inside and out. | Keep. | block/glass/plain.png | 3 |
| *Porches, posts, rails, coach lamps | gen_deep.py:level9 (L541-576); deep_textures.py:level9 (L609-621) | 9 sleepingbag-wide; hero 19 | C | Square white posts and rails as flat boxes; the coach lamp is not identifiable in any shot. | Posts with a base and capital (stepped boxes), painted-wood texture; check the lamp in a day spot. | block/wood/planks/oak1.png | 2 |
| House doors, garage doors | gen_deep.py:level9 (L513-514); deep_textures.py:level9 (L658-675) | 9 l9house-close (far); hero 19 | D | Cube doors with panels, knob, window and house number painted; every house shows the same number. | A door shape with inset panels and a knob; vary the number per house (needs a variant, not layout). | block/wood/door/plain/ | 2 |
| House interiors: wallpapers, floors, stairs, furniture (kitchen cabinet, dresser, TV, bath, toilet, pantry, tool shelf), pictures | gen_deep.py:level9 (L486, L469-473, L527-540, L602-633), :refinements (housedeco); deep_textures.py:level9 (L526-580, L677-725) | 9 l9stairs-*, close-light; 94 close-wall, prop-2 (rose paper, bed) | C (dresser, TV, cabinets D) | Flat wallpapers with a stamped motif (rose dots); dresser drawers, TV screen and knobs, cabinet doors are painted. The ceiling light is a painted circle. | Paper primitive from B3; furniture with inset drawers and knobs; a light fitting as geometry. | block/wallpaper/normal/blue1.png | 2 |
| *Streets: asphalt and markings, sidewalk, street lights, signs, mailboxes, hydrants, bins | gen_deep.py:level9 (L463-469, L577-656), :refinements (stopsign, L768-829); deep_textures.py:level9 (L501-525, L622-653), :refinements (L814-829) | 9 wide-06, streetname-*, citysign-*, sleepingbag-*; hero 19, 20 | C | Asphalt is dark speckle; sidewalk slabs are flat with a joint line; the mailbox is a flat navy box; signs read (B). Asphalt is painted twice (deep_textures level9 L501 and refinements L814). | `matlib.asphalt` (aggregate, tar seams, tyre polish) in one place; sidewalk with slab edges and cracks. | block/stone/gravel/, block/stone/path/ | 1 |
| Yard props (grill, swing set, hoop, doghouse, patio chair, washer, toy box) | gen_deep.py:level9 (L634-656), :refinements (L768-829) | not in any frame | not seen | Washer porthole painted. | Covered by the day spots above. | — | 3 |
| *Level 10 barns, silos, sheds | gen_deep.py:level10 (L662-683), :refinements (silo L709, barn roofslope); deep_textures.py:level10 (L731-761), :refinements (L914-918) | not in any shot (10 has only one target, fieldthing) | not seen | The texsheet shows barn walls as plank lines on red/grey noise. | Add spots: Level 10 barn and silo, wide and close. | block/wood/planks/aged1.png | 2 |
| Level 10 tractor, trough, pump, gates, scarecrow, hay rolls, power poles | gen_deep.py:level10 (L684-698), :refinements (L832-892); deep_textures.py:level10, :refinements (L869-891) | 10 prop-2, fieldthing-*; hero 21, 22 | C | The trough is a grey box with painted plank lines and flat water; the hand pump is black boxes; the tractor has square wheels (not seen). | Trough boards as geometry, water with a surface gradient; tractor wheels as octagons. | block/wood/barrel/ | 2 |
| *Fields: dirt road, stubble, farmland | gen_deep.py:level10, :refinements (fieldstubble); deep_textures.py:level10, :refinements (L919-925) | 10 wide-04..08, close-floor; hero 21, 22 | C | The dirt road is vanilla farmland in the shots (fine); stubble and dirt road textures are speckle noise. Crops are vanilla. | `matlib` soil with clods. | block/soil/farmland/ | 3 |

## B12 Level 11

Generator: `tools/gen_city.py`. Shots: `review/baseline/11/`, hero 23, 24. refuge-wide and refuge-close are black and must be re-spotted.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Façades: brick, stone, concrete, glass, mirror (wall, window, lit, blinds, band), piers | gen_city.py:facade_textures (with bricks, glass_pane, sash), :facades | 11 wide-01, close-wall, billboard-*, adpillar-*; hero 23, 24 | C (brick B) | Brick is structured and per-brick shaded (B). Stone and concrete are flat panels with lines. The windows, sashes, curtains, reveals and cornices are all painted: the towers are flat walls with a window picture, so at street level they have no depth. | Windows as recessed boxes in the near storeys (a window block with a 2 px reveal), cornices as stepped boxes; stone as ashlar with lit edges. | block/clay/brick/four/running/, block/stone/brick/limestone1.png | 1 |
| *Streets, plaza, sidewalks, crossings | gen_city.py:street_textures (reads asphalt.png from deep_textures) | 11 wide-01, wide-07, adpillar-wide, close-floor; hero 23 | C | Asphalt speckle; crossings are clean white bars; plaza tile is flat with joints. | Shared asphalt and tile from B11/B2. | block/stone/path/ | 1 |
| *Billboards and ad pillars | gen_city.py:poster_textures, :props (billboard, adpillar) | 11 billboard-*, adpillar-*, wide-01; hero 23 | B | Billboards have a frame, struts, catwalk and lamps; the ad pillar's posters read. The pillar's green cap is a flat box. | Pillar cap with a moulding and a finial. | — | 3 |
| *Street props (traffic lights, phone booth, newsbox, mailbox, bus shelter, parking meter, bins, cars) | gen_city.py:prop_textures, :props | 11 wide-01, wide-08, adpillar-wide; hero 23 | C | Flat boxes: the traffic signal is a yellow box with no lenses visible at range; the newsbox and mailbox are flat colour. | Lenses as recessed discs with hoods; painted-metal textures. | block/metal/sheet-plain/steel1.png | 2 |
| *Storefront fascia and signs | gen_city.py:sign, :sign_wide, :sign_textures, :decorations | 11 close-wall, close-wall2, wide-03; hero 24 | C | The green fascia with a gold border is a flat panel; the shop signs read (B). | Fascia with a raised border moulding. | — | 2 |
| *Diner (interior reuses Snackrooms props) | gen_deep.py:level61 props, gen_detail.py:level4 (kitchencounter); gen_city.py:sign_textures (signdiner), :poster_textures (billboard-diner) | hero 24 only | C | See B9 fixtures. | Fixed by B9. | — | — |
| Lobby interiors (ceiling, troffers, elevators, marble floor, pews) | gen_city.py:street_textures (cityfloor-marble), facades; gen_detail.py (liftdoor) | 11 threshold-*, close-light, wide-03 | C (marble floor D) | The hotel/lobby marble floor shows the same vein scribble per block in threshold-wide. | texlib.marble at 32 px with alternates. | block/stone/polishedrock/ | 2 |
| Subway (walls, floor, rails, signs, map, lamps) | gen_city.py:street_textures (subway*), :sign_textures, :decorations (subwaydeco) | not in any shot | not seen | Rails and sleepers are painted on the floor. | Add a spot: Level 11 subway platform, wide and close. Rails as geometry. | — | 2 |
| Mirror rim, fountain rim, rooftop props | gen_city.py:facades (fountainrim), :props (watertank, antenna, acunit) | not in any shot | not seen | — | Add a spot: Level 11 plaza fountain. | — | 3 |

## B13 Levels 37 and 94

Generators: `tools/gen_pool.py`, `tools/gen_motion.py`. Shots: `review/baseline/37/` (several frames very dark or under water), `review/baseline/94/`, hero 25, 26, 27, 28.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Pool mosaic tile (plain, sunlit, red, void, coping) | gen_pool.py:tile_texture, :textures (L57-61), :blocks (L154-159) | 37 every shot; hero 25, 26 | C | Structured (64 px tiles with grout and a glaze highlight) and right for the level, but flat and uniform: every tile the same tone, so a wall is a perfect grid. At range in wide-02/03 the dark walls turn into large-pixel noise. | Per-tile hue and value drift, an occasional chipped or darker tile, grime in the grout near the water line. | block/clay/tile/2x2/plain/ | 1 |
| Coping and slits, arches | gen_pool.py:textures (poolcoping, slitglow, archglow), :blocks (poolwall-slit, -arch) | 37 close-ceiling, wide-02, wide-03; hero 25, 26 | B | The slit is a real recess with tile reveals. The coping lip is painted. | Coping as a rounded box edge. | — | 3 |
| Handrails, ladders | gen_pool.py:blocks (L172-178, L186-189, poolladder L211-216), :textures (poolchrome) | 37 prop-2, wide-03; hero 26 | B | Real geometry with chrome glints. | Keep. | — | 3 |
| POOL doors | gen_pool.py:blocks (pooldoor), :textures (L99-110) | not in any shot | not seen | The porthole, push plate and kick plate are painted. | Add a spot: Level 37 POOL door, close. | block/metal/door/ | 2 |
| Lost things, Epsom crust, red sprouts | gen_pool.py:blocks (L212-240) | 37 wide-03, wide-04 (far) | C | Small flat boxes. | — | — | 3 |
| *Turf (clay turf light, dark, side) and soil | gen_motion.py:textures (L51-73), :blocks (L258-269) | 94 wide-02..08, close-floor, close-wall2; hero 27, 28 | D | A thumbprint swirl is stamped once per texture, so every hill face shows the same swirl in the same place; with the flat green, the hills read as a grid. | Grass-turf texture with blade strokes and two or three alternates; the clay thumbprint (lore) as a rarer alternate, not every block. | block/soil/ (vanilla grass top/side) | 1 |
| *Roads, kerbs, paths, concrete | gen_motion.py:textures (motionasphalt, motionkerb, motionpath, motionconcrete) | 94 castle-*, wide-01; hero 27, 28 | C | Flat grey with a faint thumbprint; the kerb is flat white. | Keep the plasticine look but add a soft top-to-bottom shade and edge highlights. | — | 2 |
| *Houses (castle wall, siding), picket fences, water towers, fountains | gen_motion.py:textures (L110-188), :blocks (L291-405) | 94 wide-01, wide-02, wide-05; hero 27 | C | Siding as in Level 9; picket fence reads (B). Water towers and fountains not seen close. | Shared siding fix from B11. | — | 2 |
| Castle | gen_motion.py:blocks (L291-307), :props (L493-546), :far_castle | 94 castle-wide, castle-close (far, behind hills) | not seen | Only a far silhouette is visible. | Add a spot: Level 94 castle gate from 8 blocks. | block/stone/brick/limestone1.png | 2 |
| 1950s furniture (bed, nightstand, lamps, icebox, radio, arcade, diorama) and wallpaper | gen_motion.py:textures (L190-253), :props (L408-563) | 94 close-wall, prop-2 | C (icebox, radio D) | The bed is a flat red slab; the rose wallpaper is a dot stamp; icebox handles and radio grille and knobs are painted. | Furniture with insets and knobs as geometry; paper primitive from B3. | block/wood/cabinet/1block/ | 2 |
| Milk vans, old cars | gen_motion.py:props (milkvan L418-428, oldcar L430-443) | not in any shot | not seen | Wheels are square boxes. | Add a spot: Level 94 street with a milk van; octagonal wheels. | — | 3 |

## B14 Level ! (run) and Level Fun

Generators: `tools/gen_run.py`; `tools/gen_fun.py` (gen_fun_models.py is entities, B17). Shots: `review/baseline/run/`, `review/baseline/fun/`, hero 29, 30, 31, 32. Level ! is lit red by design; prop-1, prop-2 and wide-07 are black and must be re-spotted; judge Level ! textures mainly on the texsheets.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Hospital walls and cove base | gen_run.py:textures (254-275), :paint, :cove, :walls | run close-wall, wide-01..08; hero 29, 30 | C | Paint stipple over noise with a 2 px cove; no corner guard, no scuff band where trolleys hit. | `matlib.plaster` painted, a scuffed band at rail height, a real cove shape. | block/stone/plaster/plain.png | 2 |
| *Vinyl floor, borders, scuffed, cracked | gen_run.py:textures (278-335), :vinyl | run close-floor, wide-*; hero 29 | C | Speckled vinyl reads (it is the right material), but the speckles are uniform single pixels on flat ground and each block repeats with a 1 px seam. | `matlib.tile` sheet vinyl with chip clusters of two sizes and a faint wax sheen; drop the per-block seam. | block/stone/tiles/travertine1.png | 2 |
| Ceiling tile, T-bar, diffuser, vents | gen_run.py:textures (338-363), :walls (run-ceiling-*) | run close-light | C (T-bar D) | The T-bar grid is painted into the tile. | Share the B3 tile and T-bar treatment. | block/stone/plaster/square.png | 2 |
| *EXIT signs (hanging, wall, lit, dim, dead) | gen_run.py:exit_face, :signs | run wide-01..08, runhall-*; hero 29 | B | The bitmap EXIT with chevrons and halo reads well in red light. The case is a plain box. | A case with a bevel and a diffuser lip. | block/metal/sheet-plain/steel1.png | 3 |
| *Doors (side, dented, exit, marked, chained, hall) | gen_run.py:textures (384-508), :side_doors, :exit_doors, :chained_door, :hall_door | run wide-01..08, runhall-*; hero 29, 30 | C (side door D) | The side door paints its wired window and kick plate; the frame and lever are geometry (good). | Window as an inset pane with a bead; kick plate as a box (it exists for the exit door). | block/wood/door/plain/, block/metal/door/ | 2 |
| Crash rail | gen_run.py:rail, :walls (run-wall-rail*) | run wide-* | C | Oak rail on brackets is geometry, but the rail has the same flat grain on every face. | `matlib.wood_planks` along the length with a rounded top highlight. | block/wood/planks/oak1.png | 3 |
| *Set pieces: gurneys, wheelchairs, IV stands, crash carts, shelves, bedside, cabinet, curtains, cots, barricades, collapse | gen_run.py:props (1219), :gauntlet (1494), textures (511-645) | run wide-01..08 (gurneys, barricades), runhall-*; hero 29, 30 | C (cart, defib, med cabinet D) | Plenty of geometry, but the cart drawers and labels, the defib screen and the medicine cabinet's mirror and cross are painted. Sheets and mattresses are flat. | Drawers as inset boxes with pulls; defib screen as an inset glowing plate; mattress with quilting shade. | block/cloth/bed/mattress-normal.png | 2 |
| Notices (hand wash, visiting hours, safe-zone sign) | gen_run.py:notice, :startroom, :safe_sign | run close-wall (VISITING HOURS) | B | Readable lettering, supersampled; paper is flat but these are posters. | A paper curl and pin. | block/cloth/paper/blank-large.png | 3 |
| *Fun vinyl floor tiles (a-d) and checker mats | gen_fun.py:vinyl_textures, :checkermat_textures | fun wide-01..03, wide-07, prop-*, funparty-*; hero 32 | C | Flat saturated squares with a grout line and a few scuffs; no sheen variation, and the colours are pure primaries. | Vinyl with a soft sheen gradient per tile, slight colour drift, darker grout; lower saturation a step (palette question to ask). | block/clay/tile/2x2/plain/ | 1 |
| *Lobby carpet, race carpet, retro carpet | gen_fun.py:lobbycarpet_texture, :racecarpet_texture, :retrocarpet_texture | fun close-floor, wide-05; hero 31 | C | The pattern is good; the pile under it is noise, the toy cars are painted. | Pile from `matlib.carpet` under the pattern. | block/cloth/rug/red/ | 2 |
| *Paint walls (six colours, -low), prom wall and band, skirting | gen_fun.py:paint, :surface_textures, :promwall_textures, :skirting_texture, :surfaces | fun wide-04..08, close-wall, close-wall2; hero 31, 32 | C | Eggshell paint with roller laps; the "-low" scuffs are small repeated dash pairs in the same place on every block. | Fewer, larger scuffs at random offsets; two alternates. | block/stone/plaster/plain.png | 2 |
| Ceiling tile (Fun) | gen_fun.py (ceiling via the shared tile or prop_textures) | fun close-ceiling, close-light, wide-01..03 | C | Fissured tile with painted grid. | Share the B3 tile. | block/stone/plaster/square.png | 2 |
| *Party dressing: balloons, streamers, bunting, tables, tableware, cakes, chairs, gifts | gen_fun.py:prop_textures (latex, crepe, pennant, gift_paper), :balloons, :streamers, :bunting, :tables, :tableware, :cakes, :chairs, :gifts | fun prop-1, prop-2, funparty-*, wide-04, wide-07; hero 32 | C | Balloons are crossed boxes with a radial latex texture (good idea); chairs are flat orange/red boxes; the gingham cloth is crisp. | Chairs with a moulded seat and tube legs; tables with cloth drape. Keep the balloons. | block/wood/chair/normal/ | 2 |
| Speakers | gen_fun.py:wall_props (fun-speaker-*), prop_textures (grille, speakerbody) | fun funparty-wide (far) | D | The grille is a painted dot texture on a box. | A recessed grille of bars and a cone as geometry. | block/metal/sheet-plain/steel1.png | 3 |
| *Elevator doors (brass) and directory | gen_fun.py:brushed_brass, :prop_textures (elevator-*, liftdial, fundirectory), :doors, :wall_props (fun-directory) | fun wide-01 (far); hero 31 | C | The brass gradient reads; the seam is darkened in the texture although a seam box exists; the dial is painted. | Remove the painted seam; dial as a bezel and needle. | block/metal/plate/brass.png | 2 |
| Kitchen, waiting room, playroom, inflatables, deck | gen_fun.py:rooms, :inflatables, :playroom, :deck, :service | fun wide-05 (inflatable), wide-06 (crew corridor) | C (oven D) | The oven's window, handle and knobs are painted. | Oven front as geometry. | — | 3 |
| Murals | gen_fun.py:mural | fun close-wall (poster), not the murals | not seen | — | Add a spot: Level Fun mural wall in a party room. | block/painting/ | 3 |

## B15 The End and The Hub

Generators: `tools/gen_end.py`; `tools/gen_hub_kit.py`, `gen_hub_doors.py`, `gen_hub_sigils.py`, `gen_hub_tower.py`. Shots: `review/baseline/end/`, `review/baseline/hub/`, hero 33, 34, 35.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *Carpet (plain, dusty, worn, stained, snowy) and runway | gen_end.py:carpet_tex, :textures (283-342) | end wide-01..08, close-floor; hero 33 | C | Grey-green loop pile is a fine noise; at range it is a flat green. The runway's squiggles read. | `matlib.carpet` with a pile direction and darker wear lanes along the aisles. | block/cloth/smallcarpet/black.png, block/cloth/wool/gray1.png | 2 |
| *Store walls (lower, base, upper, band, cracked, ghost, block) | gen_end.py:textures (373-412), :structure (end-wall) | end close-wall, endwall-*, endexit-*; hero 34 | C | Off-white and mustard bands of noise with a few dash scuffs; the band edge has no lip. | Painted block wall (`matlib` block courses, shallow), a raised band shape. | block/stone/plaster/plain.png | 2 |
| *Ceiling tile and troffers | gen_end.py:textures (446-485), :structure (end-ceiling, end-troffer) | end close-ceiling, close-light, wide-*; hero 33 | C (T-bar D) | Painted T-bar grid; lens prism and frame painted. | Share the B3 tile, T-bar and troffer treatment. | block/stone/plaster/square.png | 2 |
| *Gondola shelving, tall shelves, endcaps (tapered towers) | gen_end.py:shelving, :gondola, :pyramid, :books, textures (maple, slatwall, pricechannel) | end wide-01..08, prop-1, prop-2; hero 33 | C | Maple has streak grain and the shelves have lips (geometry), but the slatwall grooves are painted and the endcap towers read as a stack of identical slices. | Slatwall as grooved geometry or a shaded groove texture with a lit lip; endcap slices with a top trim. | block/wood/planks/oak1.png, block/wood/shelf/wood.png | 2 |
| *EXIT door, EXIT sign, the red vestibule walls | gen_end.py:door_tex, :doors_and_ways (exitdoor), :wall_words (end-exitsign), :neon | end endexit-wide, endexit-close; hero 34 | C | The neon EXIT built from tube boxes is good (B). The door's panel line is painted; the vestibule red is flat. | Door panel as a shallow inset; vestibule walls with a painted-block texture. | block/metal/door/ | 2 |
| Posters, closing-down signs, staff plate | gen_end.py:posters, :signs | end endexit-close (THE END) | B | Bold readable posters. | Paper curl. | block/cloth/paper/blank-large.png | 3 |
| Desks, terminals, furniture, catalogue, stock, escalator, letters | gen_end.py:desks, :terminal, :furniture, :catalogue, :stock, :atrium, :wall_words | not in any shot (hero 33 far) | not seen | The keyboard keys and CRT vents are painted. | Add spots: The End info desk and reading room (close). | block/wood/table/normal/ | 3 |
| *Hub concrete walls (panels, false wall) and ceiling | gen_hub_kit.py:concrete, :wall_textures, :tunnel_blocks | hub wide-01..08, close-wall, close-ceiling; hero 35 | C | Formwork sine and bug holes over noise; the panel seams are painted 1 px lines with no shadow. | `matlib.concrete` with a recessed seam (dark line plus a lit lip). | block/stone/polishedrock/andesite.png | 2 |
| *Hub asphalt, studs, kerb, sidewalk | gen_hub_kit.py:road_textures, :tunnel_blocks (asphalt-stud, curb, sidewalk) | hub wide-*, close-floor; hero 35 | C | Dark speckle noise; studs are geometry (good). | `matlib.asphalt` (aggregate, tar bleed, tyre polish). | block/stone/gravel/ | 2 |
| *Lamps (caged sodium), jet fans, lane signals | gen_hub_kit.py:fixture_textures, :tunnel_blocks (lamp, jetfan, signal) | hub wide-01, wide-04, wide-06, wide-08; hero 35 | B | The caged lamp and jet fan are real geometry. The signal's LED matrix is painted (fine for LEDs). | Keep. | block/metal/lantern/iron.png | 3 |
| Hub doors (carved, service, ornate) and sigils | gen_hub_doors.py:carved_doors, :service_door, :ornate_doors, :sigils; gen_hub_sigils.py | hub wide-01, wide-04, wide-06 (far); hero 35 | B | Height-map relief: the carving is real geometry. The door leaf's concrete is the same noise as the walls. | Keep the relief; new concrete from B2. | block/stone/wallcarving/ | 3 |
| Tower (ashlar, pilasters, arch, cornice, marble floor, statue, pedestals) | gen_hub_tower.py:stone_blocks, :statue, :pedestals; gen_hub_kit.py:tower_textures | not in any shot | not seen | — | Add spots: The Hub tower atrium, wide and close (the hub list has no targets). | block/stone/brick/limestone1.png | 2 |
| Stencils and plaques | gen_hub_kit.py:stencil_textures | hub wide-01..08 (numbers on the floor) | B | Spray overspray reads well. | Keep. | — | 3 |

## B16 Levels 974, 3999, 188

Generators: `tools/gen_974.py` + `gen_974_tex.py`; `tools/gen_3999_*.py`; `tools/gen_188*.py`. Shots: `review/baseline/974/`, `/3999/`, `/188/`, hero 36, 37, 38, 39, 40, 41. Level 974's eight wide shots are the same plan; add wide shots in the kitchen, the bathroom and Kitty's room.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| *974 walls (pink paint), trim, ceiling | gen_974_tex.py:paint, :trim, :ceiling; gen_974.py:structure | 974 wide-01..08, close-wall, close-ceiling; hero 36, 37 | C | Baker-Miller pink roller paint is a noise fill; the trim and crown are geometry (good, B-). | Painted plaster with very soft roller marks and corner shading; keep the colour. | block/stone/plaster/plain.png | 2 |
| *974 carpet, checker, bath tile, hex, backsplash | gen_974_tex.py:carpet, :checker, :bathhex, :backsplash, :squaretile | 974 close-floor, close-wall2, prop-1; hero 36, 37 | C | Blush carpet is diagonal flecks on noise; tiles are flat squares with grout. | `matlib.carpet` pile; `matlib.tile` with glaze highlight per tile. | block/cloth/smallcarpet/red.png, block/clay/tile/2x2/plain/ | 2 |
| *974 window paintings, curtains, valance | gen_974_tex.py:painting, :windows; gen_974.py:structure.window | 974 wide-01..08, prop-2; hero 36 | B | The recessed window with reveals, mullions and curtains is real geometry; the paintings are soft and good. Eyelets painted. | Keep. | block/glass/plain.png | 3 |
| *974 furniture: bed, desk and computer, chair, dresser, kitchen, bathroom, shelves, plush | gen_974.py:furniture (bed, desk, chair, dresser, fridge, stove, counter, toilet, bathtub...), :plush; gen_974_tex.py:soft_things, :hard_things | 974 prop-1, prop-2; hero 36, 37 | C | Many boxes with knobs as geometry (good), but every surface is a flat pastel; the computer screen and keyboard are painted. | `matlib.painted_metal`/`wood_planks` for the furniture bodies, fabric weave for the soft things; inset screen. | block/wood/cabinet/1block/ | 2 |
| *3999 neon tubes, signs, pillars | gen_3999_tex.py:neons, :neon_core; gen_3999_blocks.py:neon | 3999 wide-01..08, close-wall, close-ceiling, neoncorner-*; hero 38, 39 | B | Glowing tube boxes with a core-to-hue band; the letters are raised geometry. Lore. | Keep. | — | 3 |
| *3999 carpets (cosmic, galaxy, rotten) | gen_3999_tex.py:carpets | 3999 close-floor, wide-04..08, neoncorner-*; hero 38 | B | Seamless black-light carpet with fibre noise; reads as the intended material. | Keep. | block/cloth/mediumcarpet/blue.png | 3 |
| *3999 marble floors (white, black) | gen_3999_tex.py:marbles | 3999 wide-01, wide-02, foodcourt-*; hero 39 | D | The tile sheet shows the same vein scribble in every 16 px tile, so the food court floor is a visible grid of identical scrawls. | Use texlib.marble at 32 px with joints at the block edge only, two or three alternates. | block/stone/polishedrock/greenmarble.png | 1 |
| *3999 food court chairs, tables, booths | gen_3999_blocks.py:lobby (table, chair, booth); gen_3999_tex.py:mall (plastic-*, vinyl-pink, whitegloss) | 3999 wide-01, wide-02, foodcourt-*; hero 39 | C | The chair has a tilted back and round legs, but every face is one flat plastic colour; seat and back have no moulding. | Moulded seat with a rolled front lip, a back with a bevel, legs with feet; a gloss highlight in the plastic texture. | block/wood/chair/normal/ | 1 |
| *3999 arcade cabinets and games | gen_3999_tex_arcade.py:marquee, :screen_a..f, :side_art, :panel; gen_3999_arcade.py:cabinet, :games | 3999 wide-04..08, prop-1; hero 38 | B | Real geometry (deck, stick, buttons, marquee box, T-moulding) with strong pixel art. The coin door slots and speaker cone are painted. | Coin door as an inset with slot boxes. | — | 3 |
| *3999 vending | gen_3999_tex.py:vending; gen_3999_blocks.py:food.vending | 3999 (not clearly in frame) | C | Product rows painted behind glass. | Product boxes on shelves behind the glass. | block/glass/plain.png | 3 |
| 3999 walls, ceilings, concrete, lane wood, asphalt, pool mosaic, facades | gen_3999_tex.py:concretes, :walls, :ceilings, :lanewood, :asphalts, :pools, :facades | 3999 close-wall2, close-light, cache-*, foodcourt-* | C | Noise fills; the acoustic ceiling has speckles. | `matlib` concrete/plaster. | block/stone/plaster/plain.png | 3 |
| *188 building walls (cladding plain, band, streak) | gen_188_tex.py:facade; gen_188.py:structure | 188 wide-01..03, close-ceiling, downpipe-*, courtdoor-*; hero 40, 41 | C | Warm render with trowel sweeps; it reads as render at night, flat by day. The band line is painted. | Render from `matlib.plaster` with a raised floor-line band shape; rain streaks under each sill. | block/stone/plaster/plain.png | 2 |
| *188 windows and blinds | gen_188_tex.py:window_parts, :figures; gen_188.py:windows, :courtyard_window, :blind_composite | 188 wide-*, courtdoor-wide, downpipe-close; hero 40, 41 | B | Composite frames, mullions and sills are geometry; the blind is one plane with painted slats. | Slats as thin boxes in the near windows only. | block/glass/plain.png | 3 |
| *188 courtyard: pavers, moss, deck, hatch, edging | gen_188_tex.py:pavers, :turf, :timber, :iron; gen_188.py:deck, :hatch, :structure.edging | 188 prop-1, prop-2, wide-03; hero 40, 41 | C | Pavers have painted joints and flat faces; moss is green joints. The deck's bolts and the hatch rivets are painted. | Pavers from `matlib.tile` with lit edges; moss as alpha tufts in joints. | block/stone/path/ | 2 |
| 188 bollards, downpipes, benches | gen_188_props.py:courtyard (bollard, downpipe, downpipe_top, bench) | 188 prop-2 (bollard), downpipe-*; hero 40 | C | Bollard is cylinder boxes with flat black and a glow band; downpipe flat. | Painted-metal texture with a lit edge; downpipe joints as collars. | block/metal/sheet-plain/iron1.png | 3 |
| 188 corridors: carpet, walls, skirting, doors, lights | gen_188_tex.py:floors, :walls, :lights, :doors; gen_188.py:structure, :doors | 188 wide-04..08, close-wall, close-wall2 | C | Plain flat walls and a diamond-pattern carpet of noise. | `matlib.plaster`, `matlib.carpet`. | block/stone/plaster/plain.png | 3 |
| 188 rooms (bed, minibar, wardrobe) | gen_188_props.py:bedroom | 188 close-wall2 (TV), wide-07 | C | Boxes; minibar bottles painted. | Inset doors and real bottle boxes. | — | 3 |

## B17 Entities and items

Generators: `tools/gen_models.py` with `tools/rig.py` (painter `rig.py:fill`, 259, puts one colour and a fixed brightness per face plus mottle), `tools/gen_entities.py`, `tools/gen_fun_models.py`, `gen_hub_keymaster.py`, `gen_3999_attendant.py`, `gen_974_kitty.py`, `gen_188_models.py`; item icons in the files named per row. Evidence: hero 42 (the lineup, rendered by `tools/lineup.py`) and `review/baseline/texsheets/entity-*`, `item-*`. The bot cannot photograph entities, so this batch must make `tools/entrender.py` sheets first. Nothing here was seen in game for B1.

| family | generator (file:function) | where seen | grade | fault | fix idea | closest vanilla reference | pri |
|---|---|---|---|---|---|---|---|
| Shared painter (affects 17 of 60 entity textures) | rig.py:fill, :speckle, :hlines, :rect; `gradient_down` (305) is never called | hero 42 | C | One colour per face times a fixed face brightness plus mottle: no gradient inside a face, no AO where limbs meet the body, no rim light. | Add `vgrad`/AO to `fill` (light toward the top of each part, darker at joints) and call `gradient_down`; rebuild the 17 per-face painters on it. | entity/humanoid/ (vanilla drifter, seraph) | 2 |
| *Hound (and starved, elder) | gen_models.py:hound, :hd_skin, :hound_variant_textures | hero 42 | C | Pale boxes with a black hair cape; flat per face. | Muscle shading per part, darker belly and joints; hair with strand streaks. | entity/animal/mammal/wolf/ | 1 |
| *Skin-Stealer, Duller, Clump, Death Rat, Deathmoth, Smiler, Bacteria | gen_models.py:skinstealer, :duller, :clump, :deathrat, :deathmoth, :smiler, :bacteria (and their variant functions) | hero 42 | C (Smiler B) | Per-face constant shade with blotches; at lineup size they read as flat-coloured boxes (Skin-Stealer and Duller especially). Smiler is black by lore and the teeth read. | The shared painter fix above, then per-creature details (ribs, bruising, wet sheen). | entity/animal/ (vanilla wolf, bear) | 1 |
| *The Thing, The Mangled, Wretch, Partygoers, Keymaster, Attendant | gen_models.py:thething, :mangled, :wretch; gen_fun_models.py:partygoer, :partyhost, :lureballoon; gen_hub_keymaster.py:build; gen_3999_attendant.py:attendant | hero 42 (Thing, Mangled, Wretch, Partygoer) | B | Already shaded inside each face (countershading, gradients, fold ridges). | Re-judge after the shared painter work; little to do. | — | 3 |
| *Facelings | gen_entities.py:paint_look, :faceling_textures | hero 42 | B | Vanilla seraph body with clothing painters and a face light map. | Keep. | entity/humanoid/seraph | 3 |
| *Kitty | gen_974_kitty.py:build | hero 42 | C | Pure black with a one-texel weave and no face shading; a silhouette with no edge light. Black is the lore; the flatness is not. | Keep near-black, add a faint rim/sheen on the up faces and a cloth fold gradient. | — | 2 |
| 188 arm | gen_188_models.py:build | not in hero 42 | C | Smoky noise. | Probably fine for a phantom; check with entrender. | — | 3 |
| Item icons, survival (almond water, crackers, beans, salvage, notes, pry bar, seed packets) | gen_textures.py:salvage_items, :almond_water, :crackers, :canned_beans; gen_loop.py:notes, :pry_bar, :seed_packets; gen_breakdown.py:rubble_sprite; gen_notes.py:write_assets | texsheets item.png, item-salvage.png | C | Flat PIL shapes with an outline and at most one highlight line; vanilla icons are shaded with a light direction and a darker outline. | An `icon` helper: outline darker than the fill by hue, a top-left light, a bottom-right shadow, 1 px specular on glass and metal. | item/ (vanilla food, tools) | 2 |
| Item icons, far places (Snackrooms, 3999, 974, End, Fun, Run, 188, pool, motion) | deep_textures.py:level6, :level61; gen_3999_tex.py:items_tex; gen_974_tex.py:items; gen_end.py:item_textures; gen_fun.py:item_textures; gen_run.py:item_textures; gen_188_tex.py:items; gen_pool.py:item_textures; gen_motion.py:items | texsheets item-*.png | C | Same flat construction; the 974 and Fun ones are supersampled and a little better. | Same `icon` helper. | item/ | 3 |
| Level keys (hub) | gen_hub_items.py:materials, :bows | texsheets item-hub-*.png | B | Material tiles on a 3D key shape; read as metal. | Keep. | item/tool/ | 3 |

## Summary

### Counts per grade per batch

Rows are asset families. Cross-reference rows (priority `—`) are not counted. "Hero rows" counts the `*` rows by
grade.

| batch | A | B | C | D | not seen | rows | hero rows B / C / D |
|---|---|---|---|---|---|---|---|
| B3 | 0 | 0 | 11 | 1 | 1 | 13 | 0 / 5 / 0 |
| B4 | 0 | 2 | 10 | 2 | 2 | 16 | 2 / 6 / 1 |
| B5 | 0 | 2 | 4 | 3 | 0 | 9 | 1 / 1 / 3 |
| B6 | 0 | 1 | 6 | 3 | 3 | 13 | 0 / 2 / 0 |
| B7 | 0 | 0 | 7 | 1 | 0 | 8 | 0 / 2 / 0 |
| B8 | 0 | 2 | 8 | 2 | 2 | 14 | 0 / 2 / 1 |
| B9 | 0 | 3 | 7 | 0 | 1 | 11 | 1 / 5 / 0 |
| B10 | 0 | 0 | 6 | 1 | 2 | 9 | 0 / 3 / 1 |
| B11 | 0 | 2 | 6 | 1 | 2 | 11 | 2 / 4 / 0 |
| B12 | 0 | 1 | 5 | 0 | 2 | 8 | 1 / 4 / 0 |
| B13 | 0 | 2 | 5 | 1 | 3 | 11 | 0 / 3 / 1 |
| B14 | 0 | 2 | 13 | 1 | 1 | 17 | 1 / 9 / 0 |
| B15 | 0 | 4 | 7 | 0 | 2 | 13 | 1 / 7 / 0 |
| B16 | 0 | 5 | 11 | 1 | 0 | 17 | 5 / 7 / 1 |
| B17 | 0 | 3 | 7 | 0 | 0 | 10 | 2 / 3 / 0 |
| all | 0 | 29 | 113 | 17 | 21 | 180 | 16 / 63 / 8 |

No row is A. 29 of 180 families are B. Almost all of those are geometry the README already names as the standard (the
wall pipes, cars, Level 9 windows, marble), or things whose look is the lore (neon, arcade art, chalk, stencils,
posters). 113 are C: noise fills and flat boxes, as the diagnosis said. 17 are D, for two reasons:
- **Painted-on 3D:** gauges and dials, grilles, door hardware and the tram front.
- **A single feature stamped once per texture,** with no alternates, so it repeats on every block. This is the
  Level 1 floor scuffs, the stained carpet, the Level 7 rock crack, the Level 94 turf swirl, and the 3999 and
  Level 11 marble veins.

21 families are not in any shot. Each of their rows names a spot to add.

### The ten highest-priority rows

Ordered by how much of a playthrough they cover times how bad they are. Every one is priority 1.

| # | batch | family | grade | why first |
|---|---|---|---|---|
| 1 | B3 | *Chevron wallpaper (gen_textures.py:pattern_chevron, :wallpapers, :damp) | C | Every playthrough starts here. Hero 01 and 02 are this wall. |
| 2 | B3 | *Carpet and stained carpet (gen_textures.py:carpet) | C / D | The floor of the first hour; the stained variant repeats a blotch grid. |
| 3 | B3 | *Ceiling tile and troffer (gen_textures.py:ceiling_tile, :troffer) | C | Also the model for the painted T-bar ceilings of Levels 4, 6.1, !, Fun, The End and 3999. |
| 4 | B4 | *Level 1 concrete floor (gen_textures.py:concrete_floor; detail_textures.py:level1) | D | The scuffs repeat on every block; hero 04 and 05. |
| 5 | B4 | *Camp tent and sleeping bag (gen_detail.py:camp_tent, :sleeping_bag; detail_textures.py:level1) | C | The camp kit is in six levels and three hero shots. It is the clearest failure of the context test, beside the vanilla lantern. |
| 6 | B5 | *Machinery wall and machine cabinet (gen_textures.py:tunnel_wall, :props_textures; gen_shapes.py:level2) | D | The worst painted-on 3D, front and centre in hero 07; the same cabinet recurs in Level 3. |
| 7 | B5 | *Dead tram (gen_lore.py:tram_textures, :tramway) | D | Painted grille and windows; hero 06. |
| 8 | B8 | *Hotel doors and number plates (gen_textures.py:level5_textures; gen_blocktypes.py) | D | Painted panels and brass plate; every Level 5 corridor; hero 12. |
| 9 | B10 | *Island rock (gen_deep.py:level7; deep_textures.py:level7) | D | The same crack on every block of every sea stack; hero 15. |
| 10 | B13 | *Level 94 clay turf (gen_motion.py:textures, :blocks) | D | The same thumbprint swirl on every hill block; hero 27 and 28. |

Next in line:
- B16 3999 marble floor (D, hero 39).
- B4 crates and EXIT signs (C, in most caches and every Level 1 corridor).
- B4 metal doors (D).
- B7 office wall, carpet and partitions (C, hero 10).
- B8 damask panel, wainscot and hotel carpet (C, hero 11 and 12).

### Things that cut across batches

These belong in B2 (the material kit and model helpers), so that every level batch inherits them instead of
solving them again.

1. **`noise_fill` has no hue.** `gen_textures.py:noise_fill` (80) adds one offset to all three channels. Every
   texture built on it (most of the mod) varies only in brightness, against rule 3 of the rubric. The `noisy`
   helpers in gen_end, gen_974_tex, gen_3999_tex and gen_188_tex are copies of the same idea.
   - Give `matlib` a noise that shifts hue a little with value.
   - Make it the base for everything new.
   - Leave `noise_fill` as it is for untouched assets.
2. **Shared surface primitives, needed by most levels.**

   | primitive | needed in |
   |---|---|
   | `concrete` | Level 0 gate, 1, 2, 3, 6, the Hub, 3999 |
   | `brick` / `block` (per-brick lit top and dark bed joint, hue per brick) | Level 1 white block, 2, 3, 9, 11, 3999 façades |
   | `carpet` (pile and nap direction, with a pattern multiplied in) | Level 0, 4, 5, The End, 974, 188, Fun, 3999 |
   | `paper` (wallpaper: grain and strip seams, with the motif printed on it) | Level 0, 9, 94 |
   | `plaster` (painted wall) | Level 4, 6.1, !, Fun, The End, 974, 188 |
   | `asphalt` | Level 9, 11, the Hub, 3999 |
   | `wood_planks` | Level 5, the Manila Room, The End shelving, crates, porches |
   | `fabric` | tent, sleeping bag, chairs, partitions |

3. **One ceiling module.** Seven places paint the T-bar grid into the tile and paint the troffer's lens and frame:
   - Level 0, 4 and 6.1;
   - Level !, Fun and The End;
   - 3999.

   Build the tile, the T-bar and the troffer once in B3, as a texture with a lit rail and a recessed tile edge, or as
   a thin T-bar shape. The later batches then reuse it.
4. **Hardware as geometry, in `detail_kit.py`.** One set of B2 helpers covers most of the 17 D rows and many of the
   C rows:
   - `dial`/`gauge` (bezel, glass, needle): Level 2, 3, 5, the 3999 generator.
   - `grille(bars)`: fans, speakers, vents, the tram, the AC unit.
   - Door hardware (`handle`, `kick_plate`, `inset_window`, `push_bar`): metal and tunnel doors, hotel, house and
     side doors, POOL doors, office doors.
   - `keypad`: pay station, vending machines, microwave.
   - `inset_panel`/`frame_and_panel`: wainscot, damask frame, cabinets, drawers.

   The detail_kit has no bevel or inset helper today; every bevel in the mod is a painted 1 px line.
5. **One furniture kit.** The same flat-box chair and table appear in many places. A shared kit (chair with seat
   cushion, back frame and legs of thickness; table with a top overhang and an apron; desk with inset drawers) would
   serve them all:
   - Level 4 (office), 5 (dining, hotel), 6.1 (café), Fun (party), 3999 (food court), 974, 188.
6. **Tiling rule: no single feature per texture without alternates.** All six tiling D rows have the same cause:
   one stain, crack, swirl, scuff or vein drawn once per texture.
   - The rule for B2: a distinctive feature either appears at a random offset in two or three `alternates`, or it
     is small and frequent enough to read as texture.
   - `texsheet.py --tile` shows the problem at once. Run it on every changed texture before the client.
7. **Shading convention.** Every surface element should be lit from above:
   - a 1 px lighter top edge;
   - a 1 px darker bottom edge and darker joints;
   - a highlight on bevels;
   - colour shifting warm in the light and cool in the shadow.

   Bake it into each primitive (`bevel`, `ao_border`) rather than into each texture. The same goes for entities:
   `rig.py:fill` shades each face one flat value. A gradient and AO there (`gradient_down` exists but is never
   called) would lift 17 entity textures at once.
8. **Shared textures to change with care.** One change reaches several levels:
   - `landscape`, `clockface` and `mirrorglass` hang in Level 5 and in the Level 9 houses.
   - `switchplate` is Level 4's switch and Level 6's dead switch.
   - `lampglass` is used by road lamps, coach lamps, cars, the milk van and the flashlight.
   - `fridgewhite` is the Level 4 fridge, the Level 9 laundry machines and the Level 94 icebox.
   - `grate` is Level 3's grating and the tractor's grille.
   - Asphalt is painted twice: `deep_textures.py:level9` (L501) and `:refinements` (L814). `gen_city.py` also
     reads `asphalt.png` from disk.
9. **Orphans and dead code for the batches to clean up:**
   - `gen_textures.py:strip_light`, `:cage_light`, and the `tunnel_wall("pipes")` branch;
   - `detail_textures.py:level5` `keyrack` (L969-981);
   - `deep_textures.py:level61` `drinkfridge` (L258-265).
10. **Not in scope here, but noticed:**
    - The Level 9 front doors all carry the same house number.
    - `preview_shapes.py` ignores face rotation, so the hotel stairs and escalator rails preview with artifacts.
      Check those in game before changing them.
