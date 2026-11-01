# The Basement (unnumbered): prototype plan

Internal id **22**, `WorldLayout.Basement`, infix `Basement`, blocks `basement-`, tag `basement`, region south-south-west.
Reserved ranges are in README.md (WallPattern 208-223, FloorKind 228-243, CeilingKind 80-87, Props 620-659, Unders
130-139, Overheads 120-129, Pipes 100-109, salts 0x2200-0x22BF, title keys 2201-2299, port 42482).
Disconnected: cheats menu / `/backrooms goto basement` only. No entities, thresholds, loot or handbook.

## 1. What the lore says

Pages found and chosen:
- **Chosen:** Wikidot "Unnumbered Level: The Basement", https://backrooms-wiki.wikidot.com/the-basement. It is the only
  Basement entry on the unnumbered list (https://backrooms-wiki.wikidot.com/unnumbered-levels, whose blurb is a
  placeholder: "has yet to be discovered by anyone that can catalogue it").
- backrooms.wikidot.com/the-basement returned 404. The Fandom API returned HTTP 402, so there is no second opinion.
  No Level 0 or Level 1 "Basement" sub-level page turned up (searched lightly; none linked from the chosen page).

Content (no survival class is stated; tags: horror, interior, mystery, tragedy):
- Told as ten "Backforums" threads (#37-46, #45 missing) by a user, Havocstride, who tears up Level 0's carpet and
  drops into a small basement room. The only way on is a staircase.
- Beyond it everything is flooded: a wade of about two hours through waist-to-neck-deep, foul, cold water in cramped
  corridors. One raised dry patch where he rests. He loses his laptop to the water.
- Pitch black at first; later the lights switch on abruptly. A wailing is heard twice.
- Entities: a bloated drowned corpse that chases him; an unseen figure standing far off.
- To find: a staircase rising out of the water, and an elevator seen in the distance at the end. No items.
  The account ends in deletion.
- No named sub-zones; the three below are inferred from the narrative.

## 2. The level in this mod

Round noclip region, radius `max(40, spawnMacroX / 50)` cells (about 320 full-size), cell = 32 blocks, rooms 3 high.
Everything is a pure function of world coordinates + `Hashing` / `Noise2` with the Basement salts; no stored state.

**Zones (per cell, `Noise2` of (cellX, cellZ) at 1/6 cell scale, salt 0x2200; thresholds tuned to about 55/35/10%):**
- **2201 The Cellar** (dry, about 55%): concrete cellar rooms from a per-cell BSP plan through `PlanCache`
  (as Level 0/1 plans in `WorldLayout.Plans.cs`): 4-9 rooms, open doorway gaps 2 wide, no door blocks. Props: crate
  stacks, a few pillars, a boiler or floor drain in about 1 room in 4.
- **2202 The Flood** (about 35%): water-filled passages as a Level 2 lattice-tree maze. An 8-block node grid per
  cell; a hash-ordered union-find per cell picks a spanning set of the 4-neighbour links, plus a few extra links
  (hash < 0.2) for loops. Cell borders always hold 2 openings at hash-chosen offsets so neighbouring Flood cells join.
  Passages 3 wide, walls tight, pipes (`Pipes` 100-101) along the ceiling.
- **2203 The Dry Patch** (about 10% of cells, only inside Flood areas): one raised 16 x 16 room with the floor at
  Cellar height, a ledge, a pump or boiler and one bulb. This is the lore's resting place.
- **Joins:** where a Cellar cell borders a Flood cell, the shared border gets a 2-wide `basement-steps` stair
  descending into the water (the lore's "staircase"). Cellar-to-Cellar and Flood-to-Flood borders are flat.

**Heights:** Cellar floor 0, ceiling +3. Flood floor -2, ceiling +3 (5 tall), water surface at 0 (2 deep, neck-deep to
the player). Dry Patch floor 0, ceiling +3. No band taller than 5.

**Light:** dark. Cellar: a bare bulb per about 3 rooms (light 6), 20% of those dead; the live ones flicker
(as Level 1). Flood: lamp on the ceiling 1 per about 20 passage blocks (light 3). Dry Patch bulb light 7. Skip the
lore's sudden lights-on event.

**Air:** fog colour `#0d1614` (dark blue-green), density 0.045 Cellar, 0.07 Flood (visible about 15 blocks). Sound
bed: low room tone with distant drips in the Cellar; add sloshing in the Flood and a rare far wail sting (pick from
the existing sounds under `assets/backrooms/sounds`). Temperature 8 C Cellar, 5 C Flood, 9 C Dry Patch. Stability:
Cellar neutral, Flood slow drain (copy Level 2's rate), Dry Patch slow gain.

**Layout kinds to wire:** `FloorKind` 228 dry, 229 damp, 230 flood bed, 231 patch; `CeilingKind` 80 plain, 81 stained;
`WallPattern` 208-211 (cinder, concrete, stained, pipe-clad); `Props` 620-639 (crate stack, boiler, drain, pillar,
lamp, pump, ledge, steps, dead elevator door). Arrival: spiral out from the region centre to the first Cellar cell,
stand on the Cellar floor.

## 3. Assets

**Reuse (existing mod blocks):** Level 1 `concretewall` (plain, damaged), `concretefloor`, `concreteceiling`,
`concretepillar`, `concretestairs`, `crate`, `crate-open`, `metalshelf`, `hangingbulb`, `hanginglight`, `conduit`;
Level 2 `pipes` (run, leak), `oildrum`, `machinecabinet`; Level 3 `ironbars`, `manhole`, `rungs`, `dustyfloor`;
Level 5 `boiler`, `furnace`; `detail/` `drippipe`, `waterpump`, `watertank`, `ventgrate`, `flooddoor`, `basementdoor`;
Level 4 `elevatordoor` (dead prop). Vanilla: `game:water-still-7` for the flood.

**New blocks (6, `basement-` prefix):**
- `basement-wall` (plain / stained): damp painted cinder block, dark green-grey, vertical rust streaks.
- `basement-floor` (dry / damp / bed): bare cracked concrete with damp patches; bed = slimy algae film.
- `basement-ceiling`: low concrete with joist shadows and drip stains.
- `basement-steps` (stairs): concrete steps with a wet shine and a rust handrail line.
- `basement-slime` (flood walls below the waterline): green-brown slime over concrete.
- `basement-lamp`: bare bulb with wire cage on a cable, weak yellow glow; a dead variant.

Textures generated with `tools/texlib.py`; stairs reuse the `concretestairs` shape.

## 4. Lang strings (`assets/backrooms/lang/en.json`, es-419 later; keys follow `level-20` / `level-2001` patterns)

```
"level-22": "The Basement",
"levelhint-22": "The water rises as you go down. Find the dry ground.",
"levelname-22": "The Basement",
"level-2201": "The Cellar",
"level-2202": "The Flood",
"level-2203": "The Dry Patch",
```

## 5. Open questions

1. Real water or a look-alike? Vanilla water may fight the mod's fog, light and swim physics. Recommendation: try
   `game:water-still-7` first; fall back to a `basement-slime` fill if it misbehaves.
2. Depth: the lore says waist to neck. Recommendation: 2 blocks (neck-deep, slow) with no air meter, so players can
   still walk.
3. Start in the Cellar or flooded? Recommendation: Cellar, as the lore opens with a small room and a staircase.
4. The lights-on event. Recommendation: skip it for the prototype.
5. The elevator. Recommendation: a dead `level4/elevatordoor` in about one Dry Patch per 40 cells, prop only.
6. Survival class: the page gives none. Recommendation: leave unset; decide in a later proper pass.

## Status (prototype built, 2026-10-17)

**Built.** `WorldLayout.LevelBasement.cs`, `WorldGenerator.Basement.cs`, `AtmosphereSystem.Basement.cs`,
`tools/mapgen/BasementStats.cs`, `tools/gen_basement.py` (textures with `matlib`/`texlib`, blocktypes, the lamp's shapes,
one sound); small lines in `Tiles.cs`, `AtmosphereSystem.cs` (the base fog line, the loops in `Dispose`) and `en.json`.
- Zones per cell from `Fbm(mx/6, mz/6, 0x2200)` (wet below -0.06) and a hash (22% of wet cells hold a Dry Patch): over
  the whole region 57% Cellar, 33% Flood, 9% Dry Patch, as planned.
- **Cellar**: BSP rooms (min 5 wide, about 6-8 a cell), every split wall with a 2-wide gap (two in a long one), no door
  blocks; damp rooms (30%), drip-stained ceiling tiles, a squat `concretepillar` in big rooms, crate stacks, boilers,
  oil drums, metal shelves, machine cabinets against walls (`SafeToBlock`). Cellar-to-Cellar sides: two 2-wide gaps.
- **Flood**: lattice-tree maze on the 8-block node grid (4 x 4 nodes a cell, hash-ordered union-find + 20% extra links),
  passages 3 wide, `TileKind.Water` tiles, bed at rel -2 (`basement-slime-bed`), vanilla `game:water-still-7` in the
  fluid layer at rel -1 and 0 (Level 7's handling), walls slimed below the waterline and tide-marked just above it,
  Level 2 pipes (run/leak) along the top of most links. Wet-to-wet sides open on two of the four node lines.
- **Stairs**: every Cellar/wet side opens on one node line with a stair of two steps (`basement-steps` stair blocks in the
  water, at rel 0 and -1, `Tile.Height` 2/1, climbing toward `Pier`), 3 wide (the passage's width, not 2).
- **Dry Patch**: the middle 16 x 16 of a wet cell (floor 14 x 14 at the Cellar's height, cinder ring wall), two steps up
  from every passage that reaches it, one bright bulb, a hand pump, a boiler, crates, a shelf, a drum.
- **Light**: `basement-lamp` caged bulbs hanging at rel 3: Cellar about one room in two (on V11 / flicker V10 with the
  `BackroomsFlicker` look swap / 20% dead), Flood dim V7 over a third of the nodes, Dry Patch bright V14.
- **Air**: fog #0d1614 at 0.045 (Cellar, the `Levels` line), 0.07 Flood, 0.035 Dry Patch. Temperature 8 / 5 (4 in the
  water) / 9 C (`BasementTemperature`; `LevelTemperatures[22]` left at 14, unused). Stability 1 Cellar, Level 2's
  0.7 + 0.2 drift in the Flood, 1.15 in the Dry Patch. Titles: level 22 on arriving, then 2202 The Flood, 2203 The Dry
  Patch, 2201 The Cellar on coming back up. Sound: new loop `sounds/ambient/basement/cellar.ogg` (rumble, boiler throb,
  far drips) everywhere, louder in the dry; `ambient/poolroom` wash in the Flood; `pooldrip`/`poollap` one-shots pitched
  down; every 3-8 minutes in the Flood a far wail (`entity/groan` at pitch 0.55).
- Arrivals: `IsBasementArrivalSpot` = dry Cellar floor only.

**New block codes (6)**: `basement-wall` (plain/stained/tide), `basement-floor` (dry/damp/patch), `basement-ceiling`
(plain/stained), `basement-steps` (4 sides, the `concretestairs` shape retextured), `basement-slime` (wall/bed),
`basement-lamp` (on/dim/bright/flicker/off). Values used: WallPattern 208-212, FloorKind 228-231, CeilingKind 80-86,
Pipes 100-103, Props 620-624, salts 0x2200-0x2207, title keys 2201-2203; no Unders or Overheads.

**Skipped**: the dead elevator door (Level 4's `elevatordoor` carries the threshold behaviour, so it would be a usable
threshold), floor drains, the ledge, the plan's "pipe-clad" wall pattern (a pillar took 211), the lights-on event,
entities, thresholds, loot tables, notes, handbook, Spanish strings.

**Harness** (`mapgen 12345 14 basementstats [window]`, `basementmap [window]` writes basement.ppm):
- Full size, 24 x 24 cells round the centre: 74% Cellar here (57% over the region), 126 stairs, 0 sealed tiles; reach
  100% of 438,955 walkable tiles in one piece (steps of one level at most: dry 0, upper step 0, lower -1, bed -2), 0
  pockets, 0 places where dry floor meets deep water without a step; 60/60 arrivals on dry Cellar floor.
- `SPAWN=1000`, the whole region (100 x 100 window): 3.43 M walkable tiles in one piece, 0 pockets; `SPAWN=4000` seed
  777 (60 x 60): one piece, 0 pockets, 60/60 dry arrivals.
- `regions`: Basement 60/60 arrivals, 0 wrong level, 0 trapped, full size and `SPAWN=1000`; 0.07 ms a cell.
- `layouthash`: every line for levels 0-20 and the overall hash identical to the baseline.
- Headless (port 42482, seed 12345): `blocksweep` 7825 blocks, 0 threw; `dump 458104 642069 24` and `dump 458128
  642096 24` show the maze, the bed, water in both layers, stairs (with water in their fluid layer), the Dry Patch, lamps
  and pipes as laid out; no missing Basement blocks, shapes or textures in the logs (block names added to en.json after
  the run).

**Known gaps / check in a client**: water is two full blocks deep, so the player swims (head just over the surface)
rather than wading neck-deep, and climbs out by the steps; whether the flicker bulb's look swap and its kept light read
well; the stair blocks sitting in water (fluid layer) and the tide line's height against the water surface; the
boiler's 2-high model under the 3-block ceiling; fog density (0.045 / 0.07 may be too thick with lights this sparse);
the wail's loudness.

## Detail pass (2026-10-30)

Lore: both wikis combined as `lore/basement-brief.md` proposes (Fandom's endless basement as the level; Wikidot's flood,
dry patch, drowned body and distant elevator as its lower part). The user's decisions (`lore/DECISIONS.md`): survival
class **2** (Fandom's 2/2/2), the elevator a prop only, Escherian loops only in a few dry rooms, Windows omitted (named in
the handbook), no new creature. Values used (the Basement's column of README.md's table): `WallPattern` 293-295,
`FloorKind` 288-289, `CeilingKind` 295-296, `Overheads` 288-291, `Props` 1005-1010, salts 0x2208-0x220B.

**Built**
- **The Cellar as the Fandom basement.** Rooms by kind: *finished* (about 45%: dusty carpet, olive shag or worn brown,
  `basement-carpet`; bare joists overhead, `basement-ceiling-joists`; a house's cast-offs from other levels' props: coffee
  table, TV, toy box, washer or dryer, radiator, icebox, rotary phone, boxes, stacked chairs), *utility* (bare or damp
  concrete, boilers, drums, shelves, cabinets, crates mostly gone through) and *store* rooms (boxes, furniture piles,
  suitcases). Split walls are cinder block, old knotty pine panelling (`basement-panel`, a third) or stained block.
- **Wooden doors** (`basement-door`, closed / open / jammed x hinge x half x side; behaviour `BackroomsBasementDoor` in
  `src/Regions/BasementSystem.cs`, hyphen-safe through `BlockCodes.WithVariant`): every BSP wall has one (a long wall now
  and then two); about 30% stand open; the second door of a two-door wall is swollen shut one time in three (a pry bar in
  hand forces it, for good). Every room stays reachable without the jammed ones (harness: 100% in one piece).
- **Sounds behind doors** (client, `AtmosphereSystem.Basement.cs`): every half minute or so in the Cellar, behind a shut
  door 3-12 blocks off, on its far side: a baby crying (new `sounds/ambient/basement/cry.ogg`, synthesised, muffled as if
  through a door), footsteps pacing (`entity/footsteps`), a knock. It stops the moment the door opens or the player comes
  right up to it.
- **The crack** (about 40% of Cellar cells, in the biggest room of 7 x 7 or more): its middle 3 x 3 open up to rel 20,
  where the Lobby's ceiling tiles and a lit fluorescent panel show; round the hole at rel 16 the Lobby's soaked carpet, its
  chevron wallpaper beyond; the frayed end of a rope hanging at rel 12-16 (`basement-rope`), rubble under it
  (`basement-debris`: boards with a scrap of yellow carpet, or chunks of the slab), and in about half of them a vanilla
  ladder two blocks high against a wall, far too short. **Arrivals are under the crack** (`IsBasementArrivalSpot`): you
  come in as the lore says, by falling.
- **Escherian stairwells** (about 18% of Cellar cells, in a room of 9 x 9 or more): a brick tower five by five
  (`basement-brick`, `basement-bricksteps`) with a door in its north wall; inside, brick steps climb round a brick core, a
  block a step, eight to a turn, from rel -8 to 23. Stepping onto the landing a turn up or down puts the player back on
  the landing by the door (`BasementSystem.OnLoopTick`, an 8-block teleport; the tower repeats every turn, with a jammed
  door on the door's line a turn above and below, so it looks the same). Dim bulbs under every turn's fifth step.
  `WorldGeometry.BasementBandDepth` is 14 (band top rel 25) to make room for the cracks and towers.
- **The dead** (Fandom's "large amount of human corpses", the Wikidot account's drowned body): about one Cellar cell in
  seven has a room of the dead (bone piles, ribcages and jaws against its walls, reused props, and 2-4 bodies); one in
  five a lone body in a room, a backpack or a dead flashlight by it; in the Flood about a third of the dead ends hold a
  drowned body, and about one in sixteen of those is Gary Moors (the man the Wikidot clipping says never resurfaced).
  Bodies are the existing `corpse` / `corpse-bones` entities, laid down by `BasementSystem` the first time a player comes
  within a cell of them (cells done kept in the save, key `backrooms-basement-bodies`), owner `backrooms-basement-dead`,
  named "someone who came before", "a drowned man", "Gary Moors"; they hold a few scraps (rot, carpet fibre, a candle, a
  rusty gear or two, now and then a note) and crumble when emptied, as every corpse does.
- **The smell** (Fandom: it "can suffocate one if it is inhaled for long enough"): with two or more of the dead within
  four blocks, exposure builds a second a second (eases two a second): a chat warning at 15 s, another at 45 s, then 0.5
  suffocation damage every 5 s. The fog near them turns a sick brown (client).
- **Water not safe to drink** (Fandom: drinking it dehydrates): `WaterClass` gives the Basement its own `WaterKind.Foul`:
  -150 hydration, the tainted stability cost, sickness one time in two (`drink-foul`). A bottle filled there is murky.
- **Light:** dark (a bulb in about every other room), but about one ceiling block in seven (a fixed lattice, looking like
  every other) gives off a faint light (`basement-ceiling-faint`, V 6, absorption 0 so it reaches the room): "a light
  which has no determined source". Arriving, it is pitch black for 2.4 s, then the lights come on with a relay's clunk
  and the hum swelling (new `lightson.ogg`): the Wikidot account's first moments.
- **The Dry Patch** brought to the lore: no pump, no boiler, a plain bulb instead of the bright one; a crate or two, a
  shelf, a drum, sometimes someone who stayed. **The elevator in the distance:** in about half of them a dead cage lift
  (`basement-lift`: Level 5's cage lift shapes in the Basement's cinder block, no threshold) in the middle of a wall.
- **Out of place:** coils of rope (break: `game:rope`), empty bottles (`emptybottle`), jars gone bad (`game:rot`), now
  and then an old crowbar (a `prybar`: the narrator's) as `basement-junk`, 0-2 a Cellar cell; wires hanging from the
  ceiling (`wiredroop`, a room in three); a wet floor sign or a traffic cone in a dry room (one in ten); floor cables.
- **Loot** (class 2, "Lack of Needed Resources"): a stash of one or two supply boxes in about one Cellar cell in five,
  `PickedOverShare` 0.75 (most torn open); crates mostly opened; no food of the level's own.
- **Director** (`Roster`, `MenaceSystem`, `Danger`): danger 0.3, solitude 1.3; the Cellar is the Heartland band, the
  Flood the Approach. Cellar: Smilers in the dark, now and then a Skin-Stealer, Facelings (Fandom: they fall in as people
  do). Flood: the Bacteria's dark figure, seen far off and following ("something standing in the distance"), and Wretches
  that stalk and hunt through the water. Distant sounds: footsteps, a knock, a scratch, the groan, drips. `SurvivalClass` 2.
- **Notes:** a track of six (`lbasement`, its own block in gen_notes.py): the hole and the ladder, Tom on the water, A.L.
  on doors that are not a system, the M.E.G. on the stairwells and the dead, the flood account, the newspaper cutting
  (Cincinnati, six drowned, Gary Moors). **Handbook:** its own page `guide-basement` (gen_guide.py, its own block; listed
  in `GuideSystem.Added`). Lines: `levelhint-22` rewritten, `levelhint-2202` and `levelhint-2203` added.
- **Harness:** `basementstats` also counts doors (and jammed), cracks, stairwells, bodies by kind, things dropped, boxes,
  elevator leaves, carpet share and panelled walls, and walks doors (not jammed ones), rubble, bodies and the stairwells'
  tiles. Dev command `basementbodies x z` (console-safe) lays down the bodies of the nine cells round x z.

**Choices against the brief**
- Class 2 (the user's decision), not the brief's 3: sparser director, scarce loot.
- The drowned body that chased the Wikidot poster: the existing `corpse` entity cannot move, so the bodies lie still and
  the chase is the director's Wretch in the Flood (Stalk/Hunt). The handbook says "something follows people through the
  water" without naming it.
- No Windows (decision); the handbook says they are told of and none has been found.
- Left out for time (brief "nice"): the rising tide, the bar cellar room, the long Recovered Document note (its "don't
  jump into random holes" is in the first note).
- The lights switching on abruptly is a client fog effect on arrival (block light does not change).

**My inventions** (in neither wiki): the Lobby's ceiling and light showing at the top of the crack, the dangling cut rope
and the too-short ladder; the jammed doors and forcing them with a pry bar; the turn-repeating jammed doors in the
stairwell; Tom's, A.L.'s and the M.E.G.'s notes in their usual voices; the bodies' names and what is on them; Wretches as
the Flood's follower; the cage lift's look; the brown fog near the dead.

**Check in a client**
- The door model (frame, leaf, knobs) shut and open, both hinges and four sides; that an open door does not block the
  doorway; the jammed message and forcing with a pry bar.
- The sounds behind doors: loudness, that the far-side placement reads as "behind the door", that they stop on opening.
- The crack: how far the Lobby's light carries down (it is dark at the bottom), the rope, the ladder, the rubble model.
- The stairwell: walking the spiral (at the corners the high half of a step leads on), the teleport at the landing a
  turn up or down (seamless but for how deep the fog lets you see), the fake doors.
- Carpet, panelling and joist textures (the panelling may read too orange against the cold fog), the faint ceiling
  light's strength, the length of the blackout on arrival.
- Bodies: the drowned are laid on the Flood's bed under the water (whether they float, how they look); Gary's name.
- The smell's timing, and the brown fog near the dead.

### Round 2 (2026-10-31): looked at in the client

The lead's review of round 1: it reads right (brick, joists, wooden doors, panelling, dim), but the rooms were big, bare
and samey, and the crack, the stairwells, the Flood and the dead never came up in the random arrivals.

**Showcase spots** (`WorldLayout.LevelBasement.Showcase.cs`): walking the cells out from the region's middle, the first
of each: the crack (from the room, and from under it looking up), a finished room, a utility room, a store room, a door in
panelling, the longest look through the rooms, an Escherian stairwell (its door, and down its stairs from the landing),
a room of the dead and a lone body (each with `/basementbodies` first), the stairs down into the Flood, the Flood from a
Dry Patch's doorway (once more with `/backrooms encounter bacteria glimpse`), the Dry Patch and its dead elevator. Every
spot looks from a free floor tile along its longest clear line, or back at its subject.

**What changed**
- **Smaller rooms, six kinds.** The BSP now splits down to rooms four across (stop chances by area 30/70/130/240), but
  keeps a 9x9-15x15 room whole for a cell's crack or stairwell. Rooms are *finished* (carpet, a sitting room round a
  coffee table, a house's cast-offs: TV, radio cabinet, dresser, bookshelf, desk, coat stand, icebox, phone, toy box,
  radiator, washer), *utility* (boiler, pressure tanks, gauge frames, old pumps, drums, cabinets, coal), *workshop*
  (workbench, tool shelf and rack, toolbox, nail barrel, plywood, pipe stock, cable spool, a pallet or folding table in the
  middle), *laundry* (washer and dryer pairs, a utility sink, basket, rack), *store* (boxes, furniture piles, suitcases,
  chairs, crates, aisles of metal shelving down the middle) and *pantry* (shelves of jars, an icebox, sacks). Small rooms
  are laundries, pantries and store rooms. Things stand round the walls tile by tile (a third to a half of the wall
  tiles), never in front of a door or on a landing; a last pass walks the cell from its gaps and clears anything (or
  unsticks any swollen door) that closes a pocket off.
- **Overhead:** a heating duct of galvanised sheet metal (new `basement-duct`, we/ns, `Pipes.BasementDuctWE/NS` 292-293)
  straight across every Cellar cell and on through the walls, a water main along another line in two cells of three
  (Level 2's pipes, a leak now and then), pipes along a wall of most workrooms. Joists bare over 60% of workrooms and 35%
  of finished rooms (real basements are that way round).
- **Floors:** damp comes up through the slab in noise patches (most in a laundry), and the olive carpet is worn brown in
  patches, instead of whole rooms of one.
- **Light:** a bulb in a little over half the rooms, two in a long one; the crack's shaft is lined with a broken slab
  (`basement-ceiling-shaft`, light 10) that carries the Lobby's yellow light down to the floor under it, so the place
  you arrive is lit and the crack reads from across the room.
- **The Dry Patch:** four squat pillars on its node lines, and in about half of them a bedroll with a pack or a dead
  flashlight by it ("where he rests").
- **The dead:** rooms of the dead in 18% of Cellar cells (was 14%), a lone body in 28% (was 20%).
- Panelling darker and greyer (it read as fresh orange pine under a torch).
- Shared, one line each: `tools/mapgen/mapgen.csproj` compiles `src/Cheats/Showcase.cs` (mapgen did not build on the
  merged branch without it); `tools/clientrig/rig.py` copies the showcase step's shots into the run's folder (they were
  left in the rig's scratch folder and overwritten by the next run). `BasementStats` walks props as the layout does.

**Inventions (round 2):** the room kinds beyond the brief's (workshop, laundry, pantry), the duct and mains, the lit
shaft, the Dry Patch's pillars and the sleeper's camp.

**What the shots showed** (`%TEMP%/backrooms-shots/basement-r2-*`, three look-fix cycles, with a torch and without):
- Round 1's look holds: cold green fog, cinder block, panelling, joists, doors. Without a torch the Cellar is dim but
  readable (the faint ceiling, bulbs in about half the rooms); with one, warm and clear.
- First cycle: the crack was a black square in the ceiling (the Lobby's light, twenty blocks up, never reaches the
  floor): fixed with the lit shaft, which now shows from across the room and puts a pool of light where you land. The
  panelling read orange under a torch: darkened. The Dry Patch was a bare 14x14 box: pillars and a camp. The look inside
  a stairwell (one block of view) was useless: it now looks down the stairs from the landing.
- The rooms now have things along their walls, pipes and the duct overhead, workshops, laundries, store aisles; the
  Flood (stairs into the water, passages from a Dry Patch's door), the elevator and the dead all read.

**Still weak:** big finished rooms are still emptier in the middle than a real cellar; the brick inside a stairwell is
bright and plain under a torch; the duct is the only new model (a furnace, water heater, a bar cellar's kegs and the
brief's rising tide are still left out); the Bacteria put down by `encounter ... glimpse` did not land in the frame.

## Links (2026-10-31)

After `LINKS.md` ("The Basement"): one way in, from five levels, and one way out, both one-way.

**In: the floor gives way** (Fandom: "breaking through the floor of most levels"; the Wikidot account starts by breaking
through Level 0's floor). Very rarely a cell of Level 0, 1, 2, 4 or 5 holds a patch of cracked floor five by five
(`WorldLayout.LevelBasement.Links.cs`, `BasementEntrances`, salts 0x2280-0x2282): the host's own floor, with a flat decal
over each tile (`basement-floorcrack`, two drawings, each also turned half about by a hash of the patch's middle; dark
only, so it reads on yellow carpet, office carpet, hotel rugs and concrete): in the middle a hole broken through to the
dark, the floor sagging round it, cracks running out across the edge, rings of fracture, hairline cracks over the edge.
Each tile's `Under` is its piece (`Unders.BasementCrack` 288 + 5 dz + dx, to 312). Step onto the middle three by three
and it gives way (`ThresholdNetwork.BasementWalked`, feet under rel 1.6): a crumbling sound and the floor's dust where you
stood, the chat line "The floor gives way under you...", and you are put down ten blocks up the shaft of a crack in the
Basement's ceiling (`IntoBasement`: under a crack, on dry Cellar floor) and fall the rest: about six health of fall
damage, never a killing one (the pit's fall grace, `FallGraceKey`). One-way; the patch is one threshold (its middle tile)
and always drops into the same crack. Placement takes free plain floor only, clear of the cell's edge: a whole free five
by five if the cell has one (a room), else a free middle three by three (a wide hall), else the middle tile and two more
(across one of Level 2's narrow tunnels); never the spawn cell, nor a Red Room, the Manila Room or a party cell in
Level 0. A patch only gives way where its decal lies on the floor (`BasementMayPass`): a stretch of a world generated
before this build, or a patch whose cracks someone dug up, holds.

**Out: up the crack** (Fandom: "near impossible", bring a ladder). Whoever gets to the top of a crack's shaft (feet at rel
16 or more over its open middle or the torn carpet round it, level with the floor of the room up there), by a ladder,
blocks or anything else, hauls themselves out into Level 0 ("...into yellow light and the hum of the fluorescents. The
hole is gone behind you."), at an open spot of the Lobby (`In(0)`), always the same one for that crack. One-way.

**Level 2:** `ThresholdSystem.OnTick` does not look at Levels 2, 3 and 8 for walked thresholds, so `BasementSystem` looks
at whoever is in Level 2 every quarter second and, on a patch's middle, sends them through the same passage
(`ThresholdSystem.BasementCrackInLevel2`). No shared line was needed.

**Text:** the handbook page's *Getting here* and *Leaving* say how (gen_guide.py's own `PAGES["basement"]` block: the note
"Nothing leads here yet" is gone); a folded note in the Lobby (`r-l0-basement`, "Soft floor", appended to `rare-l0` by
a self-contained block in gen_notes.py: a wanderer who watched Kel go through); the two chat lines and the block's name
in en.json. The level's own notes already said "bring a ladder".

**Numbers** (`mapgen <seed> 16000 basementlinks`: the cells within 400 of spawn): a cell in 1500 of Levels 0 and 2, in
2000 of Level 1, in 3000 of Levels 4 and 5. Seed 12345: Level 0 1 patch (3.8 km², nearest 1922 m from spawn), Level 1 3
(6.7 km², 1859 m), Level 2 1 (6.5 km², 2040 m), Level 4 7 (15.6 km², 2728 m), Level 5 4 (18.5 km², 3188 m): 16 in the
world, 0.15-0.45 per km², a median of 0.8-2.6 km to the next in the same level. Over six seeds each level has 1-10, 0.1-1.2
per km², and every cell picked for one held one (Level 2's narrow tunnels needed the third fallback). For comparison
layout 11's ways were a few hundred blocks apart: these are a few kilometres. The mode also goes through every tile of
the nearest three patches of each host (only the middle gives way, every tile to the same crack, never a block and a half
over the floor, the same again) and up each landing crack (not from the floor, nor at rel 15.2; at the top of the middle
and on the torn carpet, to Level 0): 11 falls and 11 climbs, 0 bad.

**Checks:** `layouthash` with `BACKROOMS_NO_EXP_ENTRANCES=1` at layout versions 1 and 12: every line for levels 0-20 and
the layout hash equal main's saved files. Without it only a Level 1 line and the layout hash move at both versions (the
sample's cells hold no patch in the other hosts). `regions`: Basement 60/60. `expclash` clean.

**In the client** (rig, seed 12345, port 43115, `%TEMP%/backrooms-shots/basement-links-20261031-230525/links`): the
showcase's `link-l0`, `link-l2`, `link-l4`, `link-l5` show the patch on the Lobby's carpet, across a Level 2 tunnel, on
office carpet and on the hotel's (Level 1's nearest had no free tile three steps off: the spot now looks from up to five);
in survival, put on Level 0's patch: "The floor gives way...", down under the Basement crack the harness predicted
(455526, 643302), about four health lost of fifteen; put at the top of that shaft: "You haul yourself...", out in the
Lobby (512154, 511901, as predicted); Level 2's patch (BasementSystem's tick) and Level 5's both dropped into their
predicted cracks. 54/54 steps, no server or client error lines. Gate `--fast` (port 43110): PASS.

**Inventions:** the look of the patch (sagging, broken through, cracks and hairlines; the lore says only that people
break through the floor), only its middle giving way, ten blocks of fall from the shaft (the lore's "several tens of
feet", made survivable), coming out somewhere in the Lobby rather than beside a hole, the decal check, the Lobby note
and Kel.

**Ways between levels (rows for the guide's table, One-way):**
- Levels 0, 1, 2, 4 and 5, very rarely a patch of cracked floor a few paces across, its middle broken and sunk: step onto
  the middle and it gives way, a long fall into the Basement under a crack in its ceiling.
- The Basement, the top of a crack in its ceiling, sixteen blocks over the floor (bring a ladder, or blocks to stand
  on): Level 0.

## Round 3 (2026-11-01): the detailed visual pass

The user asked for more detailed visuals, multi-block objects and signs, more realistic layouts, closer to the lore and
the released levels. Read against round 2's final sheet (`%TEMP%/backrooms-shots/final-r2/sheets/basement.jpg`), the
lead's notes, the brief, DECISIONS.md and Levels 1, 2 and 5 (the concrete halls, the pipes, the hotel's boiler bays).

### List

Tiers: A must, B should, C nice. `[lead]` marks the lead's notes.

**1. Layout realism**
1. (A) [done] [lead] Smaller rooms: split the Cellar's BSP further (most rooms 4-8 across); keep a big room only for a crack,
   a stairwell or the rec room.
2. (A) [done] [lead] Rooms by function, not by chance alone: in each cell at most one boiler room, one laundry, one rec room,
   the laundry and the boiler room near each other (the water and the flue), the rest workshop / storage / pantry /
   root cellar / plain finished rooms.
3. (A) [done] [lead] Corridors: now and then a cell's first split is a hallway two wide right across it, rooms off it on both
   sides, each with its own door onto it; unfinished walls of bare studs with insulation between, joists overhead, the
   duct and conduit running along it.
4. (A) [done] [lead] The crack room reads from where you land: the shaft visibly lit (its lining glowing with the room
   above's light), the Lobby's fluorescent seen at the top, a pool of light on the rubble.
5. (B) [done] [lead] A root cellar: earth floor, shelves of jars, sacks, bins of old potatoes (rot).
6. (B) [done] [lead] A coal chute in a boiler room's outer wall: the iron hatch high up, the coal heaped under it.
7. (B) [done] [lead] A sump pit in a utility room's corner: the floor's iron grate over black water.
8. (B) [partly: wine racks in root cellars; no keg room or bar sign (the clipping names no bar)] A bar cellar (the Wikidot clipping's flooded bar basement, brief nice 14): kegs, a wine rack, crates, rarely.
9. (C) [partly: sodden boxes awash in some dead ends] The Flood's long passages broken now and then by a submerged door frame or a fallen shelf in the water.
10. (C) [skipped: the lore wants it bare] The Dry Patch: a few more of the lore's signs of the man who rested there (a wrung-out shirt, a dead phone).

**2. Multi-block objects**
11. (A) [done] [lead] The boiler room's set piece: an old "octopus" gravity furnace, its round body two blocks high and its
    ducts rising from the top into the joists (three blocks, one object), a cast plate on its door.
12. (A) [done] [lead] A water heater: a tall tank two blocks high, its flue and pipes going up into the joists, its plate.
13. (A) [done] [lead] The workshop's bench: a long bench (two tiles) with a vice, and a pegboard of tools on the wall over it.
14. (A) [done] [lead] The laundry: washer and dryer side by side (reused), a utility sink, and a clothesline across the room
    with things hanging on it.
15. (A) [done] [lead] Storage: steel shelving with boxes, jars and paint cans; cardboard boxes stacked two high (labelled).
16. (A) [done] [lead] The rec room: an old sofa facing a TV, a pool table (two tiles) under a hanging lamp, a rug.
17. (A) [done] [lead] A fuse box on the wall with conduit running up from it into the joists.
18. (B) [done] [lead] A wine rack against a wall (two blocks high, dusty bottles).
19. (B) [done] [lead] Cobwebs in the corners of the ceiling.
20. (C) [skipped: no bar room] Kegs for the bar cellar (stacked on their sides).

**3. Signs and text**
21. (A) [done] [lead] The fuse box's door open on its breakers, each with a hand-written label (FURNACE, WASHER, KITCHEN,
    BASEMENT LTS, ? , DON'T).
22. (A) [done] [lead] A hand-written "DO NOT ENTER" on a board nailed across some of the swollen-shut doors.
23. (A) [done] [lead] The furnace's cast plate (an invented maker in Cincinnati: the clipping's city).
24. (B) [partly: on the heater's pipes, not the mains] [lead] Pipe tags on the risers by the furnace and heater (HOT, COLD, GAS).
25. (B) [done] The water heater's plate and a "DANGER HOT" sticker.
26. (A) [done] Caution signs on walls (Fandom's "caution signs" among the out-of-place things): CAUTION, LOW CEILING; at the
    stairs down to the water DANGER DEEP WATER.
27. (B) [done] Box labels in marker on the stacked boxes (XMAS, TAXES, MOM'S, KEEP).
28. (C) [done] A calendar on a wall stopped at January 1951 (the clipping's muddled date).

**4. Detail visuals**
29. (A) [done] [lead] The stairwell's bright red brick toned down to the palette (old sooty brown-grey brick).
30. (A) [done] [lead] Hanging bulbs with rhythm: a corridor's bulbs every few tiles, lit / flickering / dead in runs; lit rooms
    a little warmer and brighter, dark rooms darker (less flat).
31. (B) [done] [lead] Stains, damp and cracks: crack alternates on the cinder and the concrete floor, damp blooms low on walls.
32. (B) [partly: the fuse box's conduit up into the joists; no runs along walls] [lead] Conduit runs on the walls up to the joists (with the fuse box) and along corridors.
33. (B) [done] A rug under the rec room's sofa and table (a finished room's floor changing in its middle).
34. (C) [done: wet floor under a leak] Puddles under a leaking pipe.
35. (C) [skipped: the panel texture repeats every block, a baseboard line would show three times] Baseboards on the panelled walls.

**5. Lore alignment**
36. (A) [done] The out-of-place things of the Fandom page that are thin: caution signs (26), ropes and wires (kept).
37. (B) [partly: the crack-room spot looks at the lit shaft; arrivals face where the client faces] The arrival (falling through the crack): face into the room from the rubble (the rig's arrivals look where the
    client looks; the showcase spot looks at the lit crack and the room together).
38. (B) [done] Keep the Dry Patch bare (the lore's resting place): no new comforts there.
39. (C) [done] The Wikidot clipping's bar (8, 20) marked as an invention of the place, not its name.

**6. Released-level alignment**
40. (A) [done] Every new block named in en.json (HUD, pick-block), drops like the released props (scrap, sticks, nothing for
    fixtures), sounds by material.
41. (A) [done] Showcase spots for every new set piece (boiler room, laundry, workshop, rec room, corridor, root cellar, fuse box).
42. (B) [done] The handbook page and notes untouched in voice; a line on the house's rooms if it helps.
43. (B) [done] The Basement's lamps and new lights stay within the level's light budget (no fullbright rooms).
44. (C) [skipped: the map keeps one colour for the Cellar] The map colours of the new room kinds (the Cellar keeps one colour).

