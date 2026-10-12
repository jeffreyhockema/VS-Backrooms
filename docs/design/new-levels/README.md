# Seven new levels: shared brief for the agents

The user asked for six new Backrooms levels (Level 3999 was dropped for a while, then restored on 2026-10-09, when Level 188 was
added too: seven in all), each researched thoroughly, planned, given generated assets and then
implemented, with the work split among parallel agents (one or two per level):

| Level | Internal id | Constant | Shown as | Region (provisional) | Owner tag |
|---|---|---|---|---|---|
| Level ! "Run For Your Life!" | 14 | `WorldLayout.RunLevel` | `!` | south of spawn | `run` |
| Level Fun =) | 15 | `WorldLayout.FunLevel` | `Fun` | north-east | `fun` |
| The End | 16 | `WorldLayout.TheEnd` | `End` | north-west | `end` |
| The Hub | 17 | `WorldLayout.Hub` | `Hub` | south-east | `hub` |
| Level 974 | 18 | `WorldLayout.Level974` | `974` | south-west | `974` |
| Level 3999 "The Neon Paradise" | 19 | `WorldLayout.Level3999` | `3999` | far south-east, beyond the Hub (restored 2026-10-09: an ordinary level, see the end of `3999-plan.md`) | `3999` (blocks `l3999-`) |
| Level 188 "The Courtyard of Windows" | 20 | `WorldLayout.Level188` | `188` | north-north-east, between Motion and Fun (added 2026-10-09) | `188` (blocks `l188-`) |

**User requirement for Level !:** the lore's hallway is ten miles long; ours must be far shorter, about **one to two
minutes of sprinting** end to end (a Vintage Story player sprints at roughly 5.5-6 blocks a second, so aim for
roughly 400-700 blocks).

## How the work is split

1. **Phase 1 (parallel): research and design.** One agent per level writes `docs/design/new-levels/<tag>-plan.md`.
   At the same time one **scaffolding agent** registers ids 14-18 (a second pass later 19 and 20) everywhere a level is switched on, with stub
   per-level files, and writes `docs/design/new-levels/CONTRACT.md` (exact file names, reserved enum/prop/under ranges,
   hook methods). Phase 1 research agents **do not edit code or assets**.
2. **Phase 2 (parallel): implementation.** Per level, a code agent (layout, generator, systems, thresholds) and an
   asset agent (`tools/gen_<tag>.py`: textures, shapes, blocktypes, sounds, lang) work from the plan's asset
   manifest.
3. **Phase 3: integration and review.** Handbook (`tools/gen_guide.py`), README, cross-checks, harness runs.

## Read first

- `docs/design/level-37-94-plan.md`: the precedent. Two noclip-only regions (ids 12, 13) added the same way, with
  research, a design, decisions and a Status section. Copy its structure and its level of care.
- The user's memory notes are summarised below; the codebase is the ground truth.
- Code to study: `src/Worldgen/WorldLayout.cs` (levels, regions, `DisplayNumber`), `WorldLayout.Level37.cs` /
  `Level94.cs` (region shape, arrivals, plans), `WorldGenerator.Pool.cs` / `.Motion.cs` (column builders),
  `src/Regions/PoolSystem.cs` / `MotionSystem.cs` (runtime rules), `src/Thresholds/ThresholdNetwork.cs` +
  `ThresholdSystem.cs` (the noclip network), `src/AtmosphereSystem.cs` (fog, sound), `src/Worldgen/WorldLighting.cs`,
  `src/Entities/` (menace director, roster, AI tasks), `tools/gen_pool.py`, `tools/gen_motion.py`,
  `tools/gen_shapes.py`, `tools/texlib.py`, `tools/rig.py` + `tools/gen_models.py` (entity models),
  `tools/gen_level_sounds.py`.

## The user's standing preferences (from past sessions)

- Lore-accurate and beautiful. **Wikidot** (backrooms.wikidot.com / backrooms-wiki.wikidot.com) is the primary canon;
  Miraheze is a second opinion; Fandom blocks direct fetches (HTTP 402/403) but its API works:
  `https://backrooms.fandom.com/api.php?action=parse&page=Level_Fun&format=json&prop=wikitext`.
- **Real 3D detail, not detail painted into textures.** Shapes are generated in Python.
- "A normal Vintage Story player wakes in the Backrooms": engage vanilla mechanics (food, tools, crafting, temporal
  stability = Reality Stability) wherever lore allows.
- Thresholds: **"walked through = two-way; fell, dived or taken = one-way"**, every threshold always leads to the
  same place (saved in `ThresholdNetwork`). Canon links to levels the mod lacks are redirected to the nearest
  existing level, keeping canon's method.
- Entities: menacing, rarely aggressive except near transitions; friendly traders like vanilla unless lore clearly
  says otherwise. New models are built with `tools/rig.py` / `tools/gen_models.py` (previews with
  `tools/entrender.py`), never recoloured vanilla models.
- Dark areas are fine with a light source; occasional flicker, not brighter areas. Quiet hums.
- The user dislikes long straight sightlines in Level 0 (Level ! is a deliberate exception: it is *the* hallway).
- No thirst. Almond Water is a food item.

## Rules for working in parallel (all phases)

- **Stay in your own files.** Each level owns files named after its tag (see CONTRACT.md once it exists). Shared
  files (`Tiles.cs`, `WorldLayout.cs`, `WorldGenerator.cs`, `ThresholdNetwork.cs`, `ThresholdSystem.cs`,
  `AtmosphereSystem.cs`, other levels' layout files, `lang/en.json`) are edited only with small, local `Edit`s inside
  the block reserved for your level, re-reading the file right before each edit. Never reformat, reorder or
  regenerate a shared file wholesale.
- **Never** run another level's generator, or the shared ones (`gen_detail.py`, `gen_blocktypes.py`, `gen_guide.py`,
  `gen_lore.py` ...), and never `git stash`, `git checkout --` or `git reset` anything. Other Claude sessions also
  work in this tree.
- **Build only through the lock:** `bash tools/locked.sh mod <tag>` (mod) or `bash tools/locked.sh mapgen <tag>`
  (harness, then run `$TEMP/backrooms-build/mapgen-<tag>/mapgen.exe`). Run asset generators as
  `bash tools/locked.sh run python tools/gen_<tag>.py`. If the build fails only in another level's files, wait a
  minute and retry; don't fix their code (tell the coordinator in your report instead).
- Python that writes files uses `encoding="utf-8"`.
- New block codes must be prefixed with your tag (`fun-balloon`, `end-bookshelf` ...): an existing code silently
  overwrites another blocktype file. Assets go in `.../block/<tag>/`, `.../blocktypes/<tag>/`, `sounds/ambient/<tag>/`.
- Headless server tests (see the memory notes in the plan docs): use your own data path in your scratch folder and
  port `42460 + id` (Level ! 42474, Fun 42475, End 42476, Hub 42477, 974 42478, 3999 42479, 188 42480); asset agents
  use `42470 + id` (... 3999 42489, 188 42490).
- Existing levels must stay byte-identical except for the entrances you add: give every new entrance its own hash
  salt (as 37/94 did) so nothing else shifts.

## Phase 1 deliverable: `docs/design/new-levels/<tag>-plan.md`

Follow `docs/design/level-37-94-plan.md`'s shape:

1. **What the lore says**: canon (Wikidot) with its survival class, description, sub-zones, entities, items,
   entrances and exits; second opinions (Miraheze, Fandom) and contradictions; well-known depictions (images,
   videos, the Kane Parsons films if relevant). Cite URLs. Quote sparingly and mark quotes.
2. **The level in this mod**: how big it is, where its region lies and its shape, the layout algorithm (plans,
   lattices, cell sizes; reuse `PlanCache` & co. from `WorldLayout.Plans.cs`), heights (floor drop, ceilings),
   lighting, fog and sound, temperature, Reality Stability, loot and vanilla-mechanic hooks, dangers and entities
   (reuse the menace director where possible; new entities only if lore demands them, with a model brief),
   runtime rules (a `src/Regions/<Tag>System.cs` if needed).
3. **Ways in and out**: every entrance and exit mapped onto existing levels 0-11, 6.1, 37, 94 and onto each other
   (the six new levels may link to one another; the Hub in particular should link to many levels), one-way or
   two-way per the rule above, with the threshold kind and its block/prop.
4. **Asset manifest** (exact, so a separate asset agent can build it without guessing): every block code with
   variants, textures (size, palette, what they show), shapes (dimensions in voxels, parts), sounds (length,
   character), items, entities, lang keys and their English text.
5. **Code plan**: the files you will create, the hooks you need in shared code, new tile fields/enum members
   needed, harness checks to add (`tools/mapgen` mode), and how you'll verify (harness + headless dump + render).
6. **Decisions for the user**, each with your recommendation (they usually say "proceed with your recommendations").
7. **Handbook text** for `gen_guide.py` (concise, exact).

## Decisions (2026-10-07)

The user chose the recommended answer on the four questions put to them: Level ! caught = death (respawn in
Level 0); Level Fun's Party Fever with the hat-and-balloon disguise; the rare Level 0 "TIME 4 FUN =)" poster trap;
Kitty's random detour (1 in 20, 1 in 6 if held) plus the Hub's pink door. Every other decision in the plans takes the
plan's recommendation, except where `LINKS.md` reconciles cross-level links (it wins over the plans). Level 3999 was
dropped, then restored (2026-10-09) as an ordinary level without the ending; Level 188 was added the same day.

## Status (2026-10-10, final integration pass)

All seven levels are built, wired into the threshold network, in the handbook (`tools/gen_guide.py`: The Levels, Ways
Between Levels, What Lives Here, Salvage and Recipes, Reality Stability) and in the top-level `README.md`. None has been
played in a client yet.

| Level | Built | Verified (harness, seed 12345) | Needs a client play-test |
|---|---|---|---|
| ! (14) | 17 lanes, chase, hazards, Safe Zone, exits | `runstats` all good (60/60 arrivals), `runlinks` all good, `runsim` | the chase's feel, tripping, fire signs |
| Fun (15) | party ship, Partygoers, fever, disguise, balloons, exits | `funstats`, `funlinks` (2/2 stair cores climb back) | Partygoer AI, Party Fever HUD |
| End (16) | library, EXIT doors, fake realities, computers, distortions | `endstats` (60/60 beside an EXIT door), `endloop` (9 aisles periodic) | distortions, the Turnaround (off by default) |
| Hub (17) | tunnels, carved doors, Tower, Keymaster, outposts, the window to 188, the 3999 door | `hubstats` (no door missing or unreachable; window placed and reached) | the Keymaster's escort, key chimes |
| 974 (18) | per-player houses, Kitty, refilling kitchen | `974stats` (60 houses, 0 faults) | Kitty's movement, DreamSleep |
| 3999 (19) | arcade-mall, tickets/prizes/stalls/vending, walkways, attendants, 3999.1, ways in Levels 10/11/37 and The End | `3999stats` (40/40 lobby arrivals, 40/40 afloat), `3999ways` (TRUEEND 5.8% of non-"=)" computers; Hub door beside a staff door) | walkway carrying, attendants, hold-to-play |
| 188 (20) | the building, live windows, blinds, the arm, Peripherals, fire exits, hatch, windows in Levels 0/1/Fun/Hub | `188stats` all good (full size and spawnMacroX 1000) | the arm's pull over the network, the Peripheral HUD, sound levels |

- **Shared checks:** `mod final` and `mapgen final` build with 0 errors; `regions` 60/60 arrivals for all nine regions,
  none in the wrong level, in full-size and spawnMacroX 1000 worlds (the "pockets" counted for Level ! and 974 are
  their lanes and houses, by design); `links` 891 thresholds, 1410 links, no row with a missing home, nowhere, repeat,
  tile or back fault, save/load 1410/1410; headless boot (port 42492): no errors or missing blocks, items, shapes or
  textures, every block of a dump in each of the seven levels resolved.
- **Level 3999's light** (integration pass): the neon was dim (floors 5-6). Tubes now light 16, wall tubes and pillars
  13, base strips 10, and the Level 37 magenta tiles absorb 0 (a lit block with absorption 99 spreads no light).
  Measured floor light (nine 129-block dumps of the centre): lobbies 5.1 → 9.9, food courts 4.6 → 9.8, game areas
  4.8 → 9.7, concourses 5.1/5.9 → 9.1/10.1 (open/under galleries); medians 10, the low end of the plan's 10-13.
- **Notes and the journal:** `tools/gen_notes.py` now has every track filled: 205 entries (160 common, 34 rare, 10
  scraps, 1 special), including `l3999` (7), `l188` (7), `rare-l3999` (2), `rare-l188` (2) and `l10-6` (the windmills).
  `--check` passes; harness `notes` OK (two scripted players, 4,000,000 random reads). Loose notes added by Kitty's
  kitchen table, the Hub's outposts and Level 3999's camps. Not tried in a client: the dialogs, J, the links, the drops.
- **`layouthash`** now `18cfdbc1c530f039` (baseline `d4a0005bf8137db6`). Levels 0, 7-10 and 13 are identical in all
  three worlds. Level 1 (all worlds), 4, 5, 11 (777) and 12 move by the reported entrances (Fun's stairs and doors,
  The End's doors and doorframe, Run's and the Hub's doors and corridor ends, 3999's glitch wall and magenta tiles),
  checked with `runhash`, `endhash`, `3999hash` and the Fun/188 switches. Levels 2, 3 and 5 also move in every world
  by another session's vanilla machinery in the pump galleries, Level 3's niches and Level 5's boiler bays (salts
  0x1E01-0x1E03), not by an entrance; Level 4 (777) and 6 (small world) keep a residue after the entrances are off,
  most likely the same fittings in neighbouring sample cells.
- **Known gaps:** sources for `hub-key-fun`, Memory Juice and LUCA Tears; the Fun Host and lure balloons; the Hub's
  endless stair, museum and Camp Amber's wandering; door notes in 3999 and 188 fall back to the nearest threshold
  (`MarkResolver` has no line for them); notes at Level 1 and Level 7/8 camps.
