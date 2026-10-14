# Graphics pass: bringing the mod's own art up to vanilla fidelity

Written 2026-10-13. Owner: the user. Planning and gate reviews: a Fable session. The work: Opus sessions, one per
batch, following [prompts.md](prompts.md). Progress: [tracker.md](tracker.md).

## 1. Scope

**In scope:** every texture, block model, entity model and item icon that this mod adds (`assets/backrooms/`), and
the Python generators that produce them (`tools/`). The aim is that a mod block standing next to a vanilla block
(the camp tent, the lantern, a chest) does not look like it came from a different game.

**Out of scope, never touched:** vanilla textures, shapes and shaders; the game's lighting and post-processing; the
mod's palette and lore decisions (one chevron wallpaper on Level 0, Level 2's heat haze, 3999's blue neon, the
night on Level 9 and so on); the world layout (no new layout version unless a batch cannot avoid it; dressing is not
layout). A batch that wants to change a colour scheme or a level's mood asks first in its report rather than doing it.

**Saves must keep working.** The mod is released and players have worlds on it (`docs/DEVELOPING.md`, "Keeping saves
working"). For this pass that means: textures and shapes may change freely; block, item and entity codes, variant
groups and class names never change (add a code beside the old one if a prop needs a new footprint); a new texture
`alternates` list or a new shape on an existing code is fine; anything that changes what a chunk generates goes
behind a new layout version, which this pass avoids.

## 2. What is actually wrong (the diagnosis)

Measured on 2026-10-13, before any work:

- **Resolution is not the problem.** The mod's block textures are 32 px, the same as vanilla's, and all on the 8 px
  atlas grid. The gap is in how the pixels are painted.
- **Textures are noise fills.** Nearly every surface is `noise_fill(colour, amplitude)` or `flat()` with a few
  blotches or lines on top (`tools/gen_textures.py`, `detail_textures.py`, `deep_textures.py`, the far levels'
  `gen_*_tex.py`). Magnified 4x next to vanilla cobblestone, planks or brick, the mod's concrete is uniform grain with
  no aggregate or cracks, the ceiling tile is a flat cream square with specks, an arcade cabinet body is one flat
  navy. Vanilla textures have *structure* (stones, planks, panels, seams), *shading* on each element (light on top,
  shadow below, darkened borders), *hue* variation rather than only value noise, and *wear* (chips, highlights on
  edges).
- **Models are flat boxes.** The food court's chairs and tables, Level 2's gauge cabinets, most furniture: a box
  with the same flat texture on every face. Vanilla furniture has bevels, insets, legs with thickness, distinct top
  and side textures, hardware as geometry. Some 3D detail is still painted into textures (dials, grilles, handles).
- **What is already at the standard:** the Level 1 white brick wall (`block_wall`), the marble in `texlib.py`, the
  round pipes in `gen_shapes.py`, the car, the Level 9 windows. These are the mod's own reference for what "done"
  looks like, besides vanilla.

Because everything is generated, the fix is not to hand-paint 2,200 PNGs. It is to raise the quality of the
primitives the generators use, then go level by level deciding what each surface and prop should be built from,
and keep what is special about each one.

## 3. The standard (the review rubric)

Grade every surface and prop A to D. The pass is done when nothing is below B and the hero assets (what the gallery
shows) are A.

| Grade | Meaning |
|---|---|
| A | Indistinguishable in painting quality from the vanilla block beside it |
| B | Reads as a finished asset; a minor thing could be better |
| C | Obviously a noise fill or a flat box next to vanilla |
| D | Wrong: painted-on 3D, broken tiling, off the atlas grid, z-fighting, wrong scale, misleading reading |

What a reviewer checks, per item:

1. **Structure.** Readable elements: bricks, panels, planks, seams, bolts, tiles, weave. Not uniform grain.
2. **Shading.** Elements lit from above: lighter top edge, darker bottom edge; borders between elements darkened;
   highlights on bevels. Baked, because the engine only shades by face direction.
3. **Colour.** Hue varies, not just brightness. Vanilla's palette is desaturated and mid-warm; no pure greys, pure
   blacks or saturated primaries except where the lore wants them (neon, EXIT red).
4. **Grain.** Fine noise at low amplitude (about 3 to 6 levels), on top of structure, never instead of it.
5. **Tiling.** Seamless; nothing repeats visibly over eight blocks; large surfaces use two or three `alternates`.
6. **Scale.** Pixel density matches vanilla (32 px per block). Lettering is readable from two blocks.
7. **Models.** Hardware, dials, grilles and handles are geometry, not paint. Furniture has bevels or insets, legs
   with thickness, and different top and side textures. Thin parts are at least 1 px thick. `check_zfight.py`
   is clean for the model.
8. **Context.** In the screenshot, does the mod block beside a vanilla block (tent, lantern, chest, torch) look like
   it belongs? This is the one that decides the grade.
9. **Lore.** The change stays within the level's design doc and the palette decisions in section 1.

## 4. Tooling to build first (Phase 0)

All new tools go in `tools/` and are documented in `docs/DEVELOPING.md` when the pass ends. Review output lives in
a git-ignored `review/` folder at the repo root (add `/review/` to `.gitignore`), never in the repo.

- **`tools/texsheet.py <folder or glob>... --out sheet.png [--ref <vanilla png>...] [--tile]`**: a contact sheet at
  4x nearest-neighbour with the file name under each tile, vanilla references in the first row for comparison, and
  with `--tile` each texture shown as a 3x3 repeat so seams and repetition are visible. This is the offline check
  for every texture change; it takes seconds, the client takes minutes.
- **`tools/preview_shapes.py`** exists but fills each face with its texture's average colour. Extend it (or add
  `tools/propsheet.py`) to map the real textures onto the faces, so bevels, insets and hardware can be judged
  without the client. Keep the average-colour mode as a fallback.
- **`tools/shotbot/batch.py --spots review/spots/<name>.json --build <mods dir> --out review/<batch>/<before|after>`**:
  writes `commands.txt` from a spot list, launches the client straight into the review world, waits for
  `status.txt` to report the last shot, copies the shots out, and builds the contact sheet. The spot list is JSON:
  `{"name", "tp": [x, y, z] or "nearest": "<target>", "look": [heading, pitch], "fov", "pre": ["/time set noon", ...]}`.
  Everything about a spot is fixed so before and after shots line up pixel for pixel.
- **`tools/shotbot/compare.py before/ after/ --out sheet.jpg`**: before above a magenta line, after below, one column
  per spot, named. The convention of the 2026-10-11 review.
- **Spot lists, one per level**, in `review/spots/`, made once in Phase 0 and committed to
  `docs/design/graphics-pass/spots/` so they survive: for each level, 6 to 10 wide shots from `tools/shotbot/pick.py`
  with the fixed seed (long, furnished views), every `/backrooms nearest` target that belongs to the level
  (`CheatSystem.Targets`) shot twice (wide at 6 blocks, close at 2 blocks, pitch slightly down), and 3 to 5
  **close-ups** of the level's most common surfaces (a wall, the floor, the ceiling, a light) from 1.5 blocks so the
  texture fills the frame. Open-sky levels get `/time set 12:00` first (VS 1.22 has no `noon`). Levels 6 and 7 get a second pass with the
  shotbot `daylight` command and `/backrooms light lantern` for inspection, marked `inspection` in the name; those
  shots judge the asset, not the level's look.

## 5. Phases

**Phase 0: tooling and baseline (one Opus session).** Build the tools above. Build `main` into a scratch Mods dir
(`tools/locked.sh mod gfx`), create the review world (fixed seed, `-o gfxreview -p backrooms`), make the spot lists,
shoot every level into `review/baseline/<level>/`, make the sheets and texsheets for every texture folder. Gate 0:
the Fable overseer confirms the shots line up when retaken (shoot one level twice) and that the texsheets cover every
texture folder.

**Phase 1: inventory (one Opus session, a fresh one that did not build the tools).** From the baseline sheets and
texsheets, write `review/inventory.md` (copied to `docs/design/graphics-pass/inventory.md` when accepted): one row per
asset family, with the generator function that makes it, where it is seen, its grade, the specific fault, the fix
idea, and a priority (how much of the game it covers times how bad it is). Group rows by batch (section 7). Gate 1:
Fable reads the inventory against a sample of the sheets, corrects grades that look anchored or lenient, and
approves the batch order.

**Phase 2: the material kit (one Opus session).** A new `tools/matlib.py` (leave `texlib.py` as it is) with
structured, seamless, 8 px-grid primitives that every generator can call:

- surfaces: `concrete` (aggregate, hairline cracks, darker borders), `plaster`, `painted_metal` (panel, edge
  highlight, chips), `brushed_metal`, `galvanised`, `wood_planks` (grain, seams, knots), `fabric` (weave),
  `carpet` (pile, direction), `tile` (grout, slight unevenness), `glass`, `paper`, `rubber`, `asphalt`;
- operations on an image: `ao_border(px, strength)`, `bevel(box, light_from_top)`, `inset(box)`, `hue_jitter`,
  `grime`, `scratches`, `drips`, `rust`, `chip_edges`, `emboss_lines`;
- rules every primitive obeys: tileable, multiple of 8 px, amplitude of grain 3 to 6, hue varies with value,
  deterministic from a seed.

Build a texsheet for each primitive beside its closest vanilla texture (cobblestone, planks, brick, cloth, metal
plates, glass). Gate 2: Fable judges the primitives on that sheet before any level batch starts. Nothing in the
levels changes in this phase.

Also in Phase 2, in `tools/gen_shapes.py` / `detail_kit.py`: model helpers reused by every kit: `bevelled_box`,
`inset_panel`, `frame_and_panel`, `handle`, `knob`, `hinge`, `grille(bars)`, `dial` and `gauge` as geometry,
`leg(thickness)`, `rim`. Preview them with the extended preview tool.

**Phase 3: level batches (one Opus session per batch, section 7).** Each batch runs the loop in section 6.

**Phase 4: entities and items (one batch).** Entity textures through `tools/gen_models.py` and `rig.py`, judged on
`tools/entrender.py` sheets and `tools/lineup.py`; item icons on a texsheet beside vanilla item icons. Entities
cannot be photographed by the bot (they never showed for a creative player), so the renders are the evidence.

**Phase 5: finish.** Full reshoot of the gallery (`docs/screenshots/`, same shots as today, retaken through the
spot lists), the ModDB description's images, `docs/DEVELOPING.md` for the new tools, `CHANGELOG.md`, and the release
zip. The version stays `0.512.2019`.

## 6. The batch loop

Every level batch is one Opus session on a branch `gfx/<batch>` off `main`, in the main working tree (the build and
asset locks in `tools/locked.sh` assume one tree; do not use worktrees for batches).

1. **Read** this document, the batch's rows in the inventory, the tracker's *lessons* section, the level's design
   doc (`docs/design/`), and the baseline sheets for the level. Look at the vanilla references named in the
   inventory rows (`G:\Games\Vintagestory\assets\survival\textures\block\...`).
2. **Work offline first.** Change the generators (textures and shapes), run `texsheet.py --tile` and the preview
   tool after each change, run `tools/check_zfight.py` for changed models. Do not start the client until the offline
   sheets pass your own reading of the rubric. Most iterations happen here.
3. **Regenerate and build.** `bash tools/locked.sh run python tools/<generator>.py` for each changed generator;
   restore `blocktypes/detail/exitlintel*.json` from git if only their key order changed; `bash tools/locked.sh mod
   gfx`; zero warnings. Run the harness checks that guard layout: `layouthash` for versions 1 and 4 unchanged,
   `validatelevel <n>` for the batch's levels. A batch does not change layout, so these must not move.
4. **Shoot.** `batch.py` with the level's spot list into `review/<batch>/after`, then `compare.py` against the
   baseline. The client must be closed before the next build (it locks the DLL); no builds or harness runs while a
   batch is shooting (their console windows steal focus and pause the game).
5. **Blind review.** Spawn a reviewer (prompt in [prompts.md](prompts.md)) that gets the compare sheet and the
   rubric, not the diff or the worker's opinion, and returns a grade per spot and per asset family with the specific
   fault. The worker fixes what the reviewer found and reshoots. At most three rounds; what is still below B after
   three goes into the tracker as *carried*, with the reason.
6. **Report.** Append to the tracker: what changed per asset family, final grades, what was carried, and any
   *lesson* that later batches should inherit (a primitive that needed a new option, a VS gotcha). Leave the
   branch unmerged with the compare sheet path in the report.
7. **Gate.** The Fable overseer reads the report and the final compare sheet, spot-checks the diff for scope creep
   (vanilla assets, layout, palette), and either merges to `main` or sends the batch back with specific items.

Every change stays in the generators. If a texture must be hand-finished, remove it from its generator first, as
`DEVELOPING.md` already says, and record that in the tracker.

## 7. Batches, in order

Ordered by how much of a playthrough each covers. Shared assets (carpet, ceiling tiles, troffers, concrete, the
camp kit, EXIT signs) are done in the first batch that uses them and only re-judged afterwards.

| Batch | Covers | Main generators |
|---|---|---|
| B0 | Phase 0 tooling and baseline | new tools |
| B1 | Phase 1 inventory | none |
| B2 | Phase 2 material kit and model helpers | `matlib.py`, `gen_shapes.py`, `detail_kit.py` |
| B3 | Level 0: carpet, wallpapers, baseboard, outlets, ceiling tiles, troffers, supply boxes, pits, Red Rooms, Manila Room, arch areas | `gen_textures.py`, `gen_l0_walls.py`, `gen_loop.py` |
| B4 | Level 1: concrete floors and walls, pillars and bay letters, crates, EXIT signs, cars and wrecks, cameras, traffic signs, puddles, first-aid rooms, the camp kit (tent, bags, burn barrel) | `detail_textures.py`, `gen_detail.py`, `gen_lore.py`, `gen_shapes.py` |
| B5 | Level 2: tunnel walls, wall and overhead pipes, gauge cabinets, steel doors, trams and rails, candles, clutter | `gen_shapes.py`, `gen_lore.py`, `detail_textures.py` |
| B6 | Level 3: panels, fans, pipe runs, trays, boilers, plaques, statue and vault, the Purpified | `gen_blocktypes.py`, `gen_shapes.py`, `detail_*` |
| B7 | Level 4: cubicle partitions, desks and chairs, office clutter, cable droops, portraits, hotel-red ramp blocks | `gen_detail.py`, `detail_textures.py` |
| B8 | Level 5: damask, beams and coffers, sconces, portraits, doors and number plates, key rack, staircases, elevators, boiler bays | `gen_detail.py`, `detail_textures.py`, `gen_blocktypes.py` |
| B9 | Levels 6 and 6.1: light switches, chalk, skylights, store fixtures, snack machine, fridge, vending rooms, diner | `gen_deep.py`, `deep_textures.py` |
| B10 | Levels 7 and 8: basalt, tar, sea stacks, Fort Surrender, caves, ore veins, glowcaps, road lamps, seeps, domes | `gen_deep.py`, `deep_textures.py` |
| B11 | Levels 9 and 10: house exteriors and interiors, windows, porches, coach lamps, street signs; barns, silos, sheds, tractor, trough, gates, fields | `gen_deep.py`, `deep_textures.py` |
| B12 | Level 11: façades, roofs, billboards, ad pillars, subway, diner, mirror rim | `gen_city.py` |
| B13 | Levels 37 and 94: mosaic, handrails, ladders, POOL doors, slits; turf, roads, castle, towers, fountains, 1950s furniture, milk vans | `gen_pool.py`, `gen_motion.py` |
| B14 | Level ! and Level Fun: hospital set pieces, crash rail, notices; lobbies, elevator doors, party dressing, speakers, directory | `gen_run.py`, `gen_fun.py` and their kits |
| B15 | The End and The Hub: store walls, partitions, EXIT vestibules, troffers; lamps, sigils, tower, doors | `gen_end.py`, `gen_hub.py` and their kits |
| B16 | Levels 974, 3999, 188: house interiors and paintings; neon, marble, arcade cabinets, food court furniture, vending; moss, blinds, bollards, courtyard | `gen_974.py`, `gen_3999.py`, `gen_188.py` and their kits |
| B17 | Entities and items | `gen_models.py`, `gen_entities.py`, `rig.py`, item icons |
| B18 | Phase 5 finish | gallery, docs, changelog, zip |

B3 to B16 are independent of each other once B2 is merged, so two can run at once on different branches if the user
wants, with the shooting serialised (one client at a time, one build at a time through `locked.sh`). One at a time
is the safe default.

## 8. Orchestration

The user's preference: Opus does the work, Fable plans and oversees.

**Mode A (recommended): one Fable overseer session drives the batches.** The overseer spawns one Opus worker per
batch with the Agent tool (`model: "opus"`, the worker prompt from [prompts.md](prompts.md) with the batch filled
in), waits for its report, spawns a fresh Opus reviewer for the gate when it wants a second opinion, reads the compare
sheet itself, and merges or sends back. The overseer never edits assets. Blind reviewers inside a batch are spawned
by the worker, also as Opus.

**Mode B: the user opens the sessions.** An Opus session per batch, started with the same worker prompt pasted in,
and a Fable session for each gate given the report and the sheet path. Same documents, same loop.

Either way the three roles are kept apart: the worker changes assets and shoots; the reviewer sees only the sheet
and the rubric; the overseer sees the report, the sheet and the diff, and holds the merge.

**When batches can run.** The shotbot needs the game window in front and the user not playing: a batch's shooting
takes a few minutes per level and the bot gives up fighting a human at the keyboard after three Escapes. The
overseer asks the user before a batch starts shooting if the user may be at the machine.

## 9. Gotchas the workers inherit (from the previous reviews)

- A blocktype's `textures: { all: ... }` overrides every texture code of its shape. Give each material its own code.
- Block textures must be multiples of 8 px on both sides; `gen_textures.save` and the 3999 `save` refuse others.
- `fit_atlas_grid` / `pad_to_atlas_grid` for pictures that are not 32 px.
- Close the client before rebuilding into the same Mods dir (it locks `backroomsss.dll`). Build with
  `tools/locked.sh mod <tag>`; never into `bin/Debug` while the user's game is open.
- `PreserveNewest` never removes deleted assets; delete the scratch Mods dir when an asset is renamed.
- Python writes must pass `encoding="utf-8"`.
- `gen_detail.py` rewrites `exitlintel*.json` with another key order; restore from git.
- Do not `git stash` the user's tree. Compare against `main` by reading, or against a snapshot tree.
- `/backrooms goto <level>` arrives somewhere random; spot lists use absolute `tp` or `nearest` so shots repeat.
- `/tp =x =y =z` is absolute; feet y is sea level + 1 on the ring levels, 48 lower in the city, lower again in
  Levels 37 and 94 (`WorldGeometry`).
- Spawned creatures never appear in bot shots; entities are judged on `entrender.py` renders.
- Subagents told to wait on a running batch with sleep loops stalled; shoot first, then hand the sheets over.
- Levels 6 and 7 photograph dark by design; use the `daylight` bot command only for inspection shots.
- `/time set noon` does not exist in VS 1.22; `batch.py` fixes June, 12:00 and stops the clock, so retakes are pixel-identical indoors.
- The far levels' generators run through `tools/locked.sh run` because they rewrite `lang/en.json`.

## 10. Done

- Every row of the inventory is B or better, hero rows A, or carried with a reason the user accepted.
- `layouthash` for versions 1 and 4 unchanged; `links`, `deep`, `validatelevel` pass; build has zero warnings;
  `gen_notes.py --check` passes.
- No file under `assets/game/` or any vanilla path changed; no shader or lighting change.
- Gallery retaken, docs and changelog updated, release zip built, version still `0.512.2019`.
