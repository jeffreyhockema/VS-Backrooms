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


### What was built

- **Rooms by what they are for** (`BasementAssignKinds`): per cell one furnace room, one laundry (beside the furnace
  room where a room fits), a rec room in the biggest room six by six or more, root cellars (trodden earth) for half the
  pantries, the rest store rooms, workshops, utility and finished rooms. **Smaller rooms**: the BSP's stop chances by
  area are now 24/48/90/160 (most rooms four to eight across).
- **Hallways** (`BasementHall`, 45% of Cellar cells): two wide right across the cell between unfinished stud walls
  (`basement-studs`, studs with fibreglass batts; `WallPattern.BasementStuds` 296), the rooms split off both sides, a door
  onto each room that touches it (`BasementHallDoors`, never swollen shut), bare joists, the duct the length of it, a bulb
  every four steps in runs lit, flickering and dead, now and then stacked boxes, a stack of chairs, WATCH YOUR HEAD.
- **Set pieces** (`BasementSetPieces`): the furnace room's octopus furnace (`basement-furnace`, three blocks: the round
  body and its lagged arms climbing to the joists, a cast HEARTHMASTER No. 6 CINCINNATI plate), the water heater two
  along the same wall (`basement-heater`, three blocks, its plate, DANGER HOT, pipes tagged HOT and COLD), the coal chute's
  hatch over a heap of coal, the fuse box (door open on breakers labelled in pencil: FURNACE, WASHER, KITCHEN, BSMT LTS,
  PUMP, ?, UPSTAIRS, DON'T; its conduit up into the joists), the sump's grate in a corner; the laundry's washer and dryer
  side by side, the sink, a clothesline across the room with a shirt, a sheet or a towel on it; the workshop's two-tile
  bench (vice, a can of nails, a hammer, a toolbox and paint under it) under two pegboards of tools; the rec room's
  two-tile pool table under two green-shaded lamps (lit) on a braided rug, an old sofa facing a TV; wine racks in root
  cellars; steel shelving two high (boxes, jars, paint cans, odds and ends) down store aisles and round walls; cardboard
  boxes stacked two high, labelled in marker (XMAS, TAXES '84-'91, MOM'S DON'T, KEEP).
- **Writing on the walls** (`BasementWallSigns`): caution signs (CAUTION KEEP OUT, CAUTION WATCH YOUR HEAD), DANGER DEEP
  WATER NO WADING beside every stair down into the Flood, a calendar stopped at January 1951 with its first six days
  crossed off, a fuse box in a cell with no furnace room; DO NOT ENTER in red marker on a board nailed across every
  swollen-shut door (one face). Cobwebs in ceiling corners (more in halls, store rooms, root cellars, furnace rooms).
- **Detail**: a cracked block wall alternate with damp wicking up; wet floor under a leaking main; sodden boxes awash
  in some of the Flood's dead ends; a rug under a sitting room's coffee table now and then; no washers in finished rooms.
- **The crack**: its shaft's lining glows (`vertexFlags glowLevel` 150, light 12), so it reads lit from across the room;
  a broken joist and a board come down with the floor lean in the rubble (`basement-fallen`).
- **Palette**: the stairwell brick toned to a sooty brown-grey; bulbs V12 (was 11), the faint sourceless ceiling V5 (was 6)
  for more contrast between lit and unlit rooms.
- **Showcase**: new spots furnace, fusebox, laundry (a washer with its dryer), workshop, rec-room, hall, root-cellar,
  store-shelves; the crack-room spot closer and steeper.
- Values: `Props` 1011-1019, `Overheads` 292-305, `WallPattern` 296, `FloorKind` 290-291; asset script
  `tools/gen_basement_r3.py` (called from `gen_basement.py`), 15 new block codes, en.json names, one sentence in the
  handbook page (gen_guide.py's own block and en.json alike).

### Inventions (round 3)

The furnace's maker and its Cincinnati plate (the clipping's city), the heater's maker and year, the fuse labels, the box
labels, the calendar's January 1951 (the clipping's muddled date), DO NOT ENTER on the swollen doors, the caution signs'
wording, the rec room, the root cellars, the hallways of studs, the fallen joist, the sodden boxes in the Flood. The
room functions follow a real house basement (the lead's notes), not either wiki.

### Balance notes for the lead

No new food, water, beds or safe rooms. New drops (all small): wine racks 0-1 empty bottle each (a water container, in
root cellars, about one rack a root cellar); shelving, furnace, heater, fuse box and signs scrap metal and wire; stud walls
sticks and carpet fibre; rugs carpet fibre; trodden earth a block of soil. The supply boxes, crates and loot tables are
unchanged. Hallways give long straight sightlines (two wide, up to 31 long) where the Cellar had none: the director's
stalkers may see further there.

### What the shots showed

Three runs, all with a torch (`%TEMP%/backrooms-shots/basement-r3-run1`, `-run2`, and the final
`%TEMP%/backrooms-shots/basement-r3-final`, `sheet.jpg` there; 33 shots, no server or client error lines).
- **Run 1:** the set pieces read (the workshop's bench under its pegboard, the rec room, the fuse box's labels legible,
  the hall of studs, the root cellar's earth and CAUTION sign, DANGER DEEP WATER by a stair down), but the furnace was a
  thin pale figure with a crown of arms, the rug garish and patchy (rotated alternates), the pool lamps square boxes high
  up, paint cans showing their bare tin, green slime showing under the stud walls, the brick still red, the store aisles
  the old one-high shelf, the laundry spot finding a lone washer in a finished room. All fixed before run 2.
- **Run 2:** the furnace was wider but its arms read as floating cubes; one hall had its bulbs mostly dead (a long dead
  run is too common at a third dead); the crack's shaft lining was grey concrete. Fixed: the arms in fine steps (five,
  and one up the back), bulbs dead one in five, the shaft a warm broken slab with rebar ends, the crack spot lower.
- **Final:** the octopus furnace reads, with the fuse box beside it and the sump's grate; the laundry's washer and dryer,
  washing on the line, the danger sign; the rec room's pool table under its two lamps on the rug, the sofa; the stud
  hallway with its duct; steel shelving of paint and boxes; the crack's shaft lit from across the room with the joist
  in the rubble. The Flood, the Dry Patch, the lift and the links look as in round 2.

**Still weak:** the furnace's arms are stepped, not smooth (no rotated elements, to be safe of the rotation sign); the
water heater stands two tiles from the furnace only where the wall has room, and no shot caught one; halls end flat
against the cell's outer wall when no gap is there; the brick stairwell is still the brightest material under a torch;
the Flood and the Dry Patch got only the sodden boxes this round.

### Questions for the user

1. The hallways of bare studs and insulation (45% of Cellar cells): keep that share, or fewer, as the Fandom page speaks
   of rooms, not corridors?
2. DO NOT ENTER is on every swollen-shut door (one face): keep on all, or only some?
3. The nods to the Wikidot clipping (the furnace's Cincinnati maker's plate, the calendar stopped in January 1951): keep?

### Checks (round 3, commit a9134958)

`expclash` clean; mod and mapgen build with 0 errors; `layouthash` with `BACKROOMS_NO_EXP_ENTRANCES=1` at layout versions
1 and 12: every line for levels 0-20 and the layout hash equal main's saved files; `regions` Basement 60/60; `basementstats`
(seed 12345 and seed 777 `SPAWN=4000`) 100% of walkable tiles in one piece, 0 sealed, 60/60 arrivals; headless (port
43114) `blocksweep` 11589 blocks, 0 threw, a dummy placed in the Basement, 0 error lines; `GATE_TAG=basement gate.py
--fast --port-base 43110` PASS. The last two commits after the final shots (the earth's drop, the unsealing walk) change
nothing that shows.

## Round 4 (2026-11-02): the asset-quality pass

The user asked for AAA assets, multi-block objects that read as one, more level-design refinement, lore and alignment
with the other levels. Read against round 3's final sheet (`%TEMP%/backrooms-shots/final-r3/basement/sheet.jpg`), the
lead's round-4 notes, the round-3 "Still weak" above, the briefs and the bar (Level 188's street furniture, Fun's set
pieces, the detail kit, `modelkit`).

### List

Tiers: A must, B should, C nice. `[lead]` marks the lead's notes.

**1. Assets to rebuild to the bar**
1. (A) [lead] `basement-furnace` top: the arms as rotated round (octagonal) ducts climbing out of the bonnet at an angle, with collar flanges and foil tape at the joints, ending in the joists; the body's bands, a real fire door (hinges, latch handle, draft slide), a sight glass.
2. (A) [lead] `basement-heater`: the tank's jacket seam and feet, the T&P valve with its discharge pipe down the side, the gas control (knob, pilot window), the draft hood and the flue rising, a shut-off valve (round handwheel) on the cold inlet, copper elbows up into the joists.
3. (A) [lead] `basement-washer` / `basement-dryer` (new, replace the shared `laundry` in this level only): real appliances with a back console (dials, a chrome trim), the washer's lid and the dryer's round door with a drum window and handle, feet, the hoses (hot red, cold blue) to a hose bib on the wall, the dryer's foil vent duct up into the joists.
4. (A) [lead] `basement-pooltable`: cushions (bevelled inner rails) with diamond sights, six pockets as cups with leather drops, a racked triangle of balls and a cue ball, turned legs; a cue rack on the wall (`basement-wallthing-cuerack`, cues and a chalk cube).
5. (A) [lead] `basement-sofa` (new, two tiles, replaces the shared `longsofa` here): an old plaid sofa with arms, three seat cushions and three back cushions (sagging), a skirt, a crocheted throw.
6. (A) [lead] `basement-tv` (new, replaces the shared `tv` here): a 1960s wooden console set on legs, its picture tube's back hump behind, a domed grey screen, the dial knobs and speaker grille, and a rabbit-ear aerial on top (two rotated rods).
7. (A) [lead] `basement-shelving` jars and tins with real printed labels (PEACHES, PICKLES, TOMATOES '58, BEANS, COFFEE) as textures, jar lids, paint cans with labels and drips.
8. (A) [lead] `basement-bench`: the vice modelled (jaws, slide, screw, T-handle), the pegboard's tools as models hanging on pegs (`basement-wallthing-pegboard-a/b`: hammer, saw, wrenches, screwdrivers, pliers, a coil of extension cord), not painted on.
9. (A) [lead] `basement-overhead-line*`: the clothesline as a sagging line with wooden pegs, the washing with folds (several boxes), hooks into the joists at the ends.
10. (A) [lead] The cinder wall (`basement-wall-plain/stained/tide`) and the stairwell brick (`basement-brick`): darker, more varied blocks with whitewash patches, white efflorescence bloom, water lines, mortar loss; no longer the brightest material under a torch.
11. (A) [lead] `basement-studs`: kraft-paper facing on the batts with staple flanges, the studs' grain and a top/bottom plate, one bay with the batt sagging out.
12. (A) [lead] The joists (`basement-ceiling-joists`, `-joistsfaint`): a modelled joist ceiling (subfloor boards over 2x8 joists with depth), with NM cable stapled along a joist, a junction box now and then, nail points through the subfloor.
13. (A) [lead] The hall's pipe run (`basement-duct-*`): beside the duct a water main and a black gas pipe on hangers, with a gate valve (handwheel) and a pressure gauge on some blocks.
14. (B) [done: porcelain rose and socket, pull chain, pear bulb with a filament, cage on a hook] `basement-lamp`: porcelain socket, pull chain, cage wires round a glowing bulb with a filament; the dead one dusty.
15. (B) [skipped: the door already has four raised panels, knobs on both faces and hinges; it held up in the shots] `basement-door`: the door's panels, knob and escutcheon, hinges, scuffed paint at the lock edge and a gap at the foot.
16. (B) [done] `basement-boxes`: flaps, packing tape, a crushed corner, damp bottoms.
17. (B) [done] `basement-winerack`: bottles with labels and foil capsules, dust on the shoulders.
18. (B) [done] `basement-wallthing-fusebox`: the door as a hinged, opened element, breakers in rows, the conduit with straps.
19. (B) [done] `basement-sump`: the grate's bars, and a sump pump (float, discharge pipe up the wall).
20. (B) [done] `basement-wallthing-chute`: the coal chute's iron hatch with hinges and a handle, the trough.
21. (C) [done] `basement-poollamp`: the shade on chains, lit underside, a brass cap.
22. (C) [skipped: round 3's web reads in the shots] `basement-overhead-cobweb`: a sagging web with strands.
23. (C) [skipped: time went to the set pieces] The floors (`basement-floor-*`): control joints, a floor drain now and then, oil stains by the furnace.

**2. Multi-block set pieces**
24. (A) [lead] The furnace room as one object: the furnace's arms ending in the joists in the furnace's own block, the heater beside it with its flue, both flues into a chimney thimble on the wall where they can.
25. (A) [lead] The laundry as one: washer and dryer side by side, a concrete laundry tub on legs with its taps (`basement-sink`, new, replaces the shared sink here), hoses and the dryer's vent, the clothesline over the room.
26. (A) [lead] The rec room as one: the pool table under its lamp on the rug, the cue rack on a wall, the sofa facing the TV.
27. (A) [lead] The stairs into the Flood: a pipe handrail sloping down the stair on its wall side and a newel post at the top that leans (the wobbling post) (`basement-steps` rail parts).
28. (A) [lead] The crack rooms: a sculpted edge of broken slab round the hole at the ceiling (jagged concrete, bent rebar ends hanging down) (`basement-slabedge`, new).
29. (A) [lead] The Flood's surface: scum, floating boards, a floating box, a bottle and leaves on the water (`basement-scum`, new, walked and swum through).
30. (B) [done] The Escherian stairwell: a handrail on the core side of the steps.
31. (B) [done] The workbench as one: the bench, the two pegboards, a shop light hung on chains over it.
32. (C) [skipped: the furnace room's coal chute says the house burned coal; an oil tank would contradict it] An oil tank on legs in the furnace room (275 gallons, its fill pipe through the wall).

**3. Level design**
33. (A) [lead] The Dry Patch stays bare (the lore's resting place): no new props there.
34. (B) [done] Halls that end flat on the cell's outer wall: end them on something (a stack of boxes, shelving, a swollen door).
35. (B) [done: scum, boards, sodden boxes, a bottle, a sunken chair] The Flood's samey passages: the scum and the floating things (29) vary it; a submerged chair or a door frame now and then.
36. (B) [done] Lighting rhythm: the workbench's shop light, the pool lamps; dark store rooms stay dark.
37. (C) [skipped: an invention with no lore behind it; the TV stays dead] The TV's screen faintly lit with snow in one rec room in a few (an invention; the house still has power).

**4. Lore**
38. (A) [done] Keep the Fandom page's out-of-place things (ropes, purposeless wires, caution signs) and its sourceless light; no M.E.G. presence (each wanderer has their own instance: no outposts), as before.
39. (B) [done] The flood water "smells terrible": the scum and the stains carry it; no new mechanic.
40. (C) [done: under a third of the sodden boxes in the Flood's dead ends] The Wikidot clipping's laptop lost to the water: a laptop on the bed of one Flood dead end (an invention of placement).

**5. Alignment with the other levels**
41. (A) [done] Shared things stay shared: supply boxes, notes, chalk, placards, the handbook voice; the Basement's own appliances are "similar but unique" copies (washer/dryer/sofa/TV/sink from the shared props, re-made here) and their source noted.
42. (B) [done] Look at 120's pipes, trays and fuse boxes and the detail kit's gauges and valves before making the hall's pipe run; reuse `modelkit.gauge`/`dial` rather than inventing.
43. (B) [done] "Shared assets below the bar" written for the lead: the Level 5 boiler, the Level 2 oil drum, the machine cabinet, the Level 1 metal shelf, the coal pile, the shared washer/dryer/TV/sofa, as used here.
44. (A) [done] Every new block named in en.json, drops like the released props (scrap, sticks, nothing for fixtures), sounds by material.
45. (A) [done] Showcase spots for the rebuilt set pieces (stairs into the Flood, the crack's edge, the Flood's surface, the laundry, the rec room) and F7 entries to match; `featurecheck` clean.

**Added while working (round 4)**
46. (B) [done] [lead: "the boiler with gauges"] The utility rooms' own boiler: a cast-iron sectional boiler (`basement-boiler`, two blocks) with its tridicator, relief valve, supply with a gate valve, return and flue into the wall, in place of Level 5's.
47. (B) [done] The crack's rubble heaped (`basement-debris`): slab chunks with rebar, a stained ceiling tile and a strip of the yellow wallpaper from the room above, wet carpet, splintered boards.
48. (B) [done] The rec room's home bar (`basement-bar`, `basement-stool`): red vinyl counter, arm and foot rails, the mirror and bottle shelves, a lit COLD BEER neon; the Wikidot clipping's bar cellar as a family rec room has one.
49. (A) [done] [shots] True octagons for every round body (the square-and-turned-square of round 3 was an eight-pointed star).

### What was built (round 4)

All in `tools/gen_basement_r4.py` (run after round 3's script by `gen_basement.py`, which also got the darker walls), the
generator's round-4 lines in `WorldGenerator.Basement.cs`, three small layout changes and the showcase.

- **Rebuilt to the bar (same codes, new shapes):** the octopus furnace (`basement-furnace`: five round lagged arms
  climbing at 34-40 degrees out of the bonnet, each with galvanised collars and a band of foil tape, turning level under
  the joists; a galvanised return trunk up the back; the flue elbowing into a cast thimble in the wall; the fire door on
  hinges with its latch bar, draft slide and ash door; a lit sight glass; cast feet), the water heater (`basement-heater`:
  feet, jacket seam, gas control with a lit pilot window and a red knob, the gas line with its tee, drip leg and a
  yellow-handled valve on the riser, the T&P valve and its copper discharge down the side, the draft hood on three legs
  and its galvanised flue, dielectric nipples, a gate valve with a red handwheel and a MAIN SHUT OFF tag on the cold), the
  pool table (`basement-pooltable`: turned legs, rails split at six pockets with leather drops, felt cushions, ivory
  sights, fifteen balls racked in a wooden triangle, the cue ball, chalk), the steel shelving (`basement-shelving`: angle
  posts, lipped shelves, jars with hand-written labels and lids, tins with printed labels, paint cans with labels, lids
  and bails, a roller tray, boxes with a flap open), the workbench (`basement-bench`: a modelled vice with its jaws,
  slide, screw and T-handle; a backboard; a rag) and its pegboards (`basement-wallthing-pegboard-a/b`: hand saw,
  wrenches, extension cord, claw hammer, screwdrivers in a rack, pliers, square, tape measure, all modelled, on hooks),
  the clothesline (`basement-overhead-*`: wooden pegs with springs; a shirt with yoke, collar, placket, pocket and hanging
  sleeves; a sheet folded over the line with creases; a towel and a sock), the caged bulb (`basement-lamp`: porcelain
  rose and socket, pull chain, a pear bulb with a glowing filament, the cage on a hook), the pool lamps
  (`basement-poollamp`: a flared shade of four tilted panels, lit underneath, brass cap and rims), the fuse box (door
  swung open on two hinges, main switch, locknut), the coal chute (framed hatch hinged at the top, propped open), the
  boxes (tape, a crushed corner, a sprung flap), the wine rack (bottles with shoulders and foil capsules, dust), the sump
  (`basement-sump`, now turned to its corner: the pump in the pit with its float, the discharge pipe up through the grate).
- **New, the house's own** ("similar but unique" to the shared props, used only in this level, in place of them):
  `basement-laundry` (from the shared `laundry`: a 1950s porthole washer and a dryer with consoles, dials, feet, hoses
  to a hose bib, a shelf of SUDZO and bleach over the washer, the dryer's foil vent into the wall under a hood; from the
  shared `kitchencounter-sink`: a concrete laundry tub on legs with its faucet and trap, a soap dish and brush over it),
  `basement-sofa` (from `longsofa`: plaid, sagging cushions, rolled arms, a crocheted throw), `basement-tv` (from `tv`:
  a console set on tapered legs, a domed screen in its bezel, speaker cloth, knobs, the tube's hump; rabbit ears, a doily
  and a photograph on top), `basement-cuerack`, `basement-shoplight` (lit, over the workbench), `basement-sumppipe`.
- **New, the structure:** `basement-joists` (the finished rooms' ceilings as a model: subfloor with nail points, two
  joists a block, NM cable stapled along whole joist lines, junction boxes, cross bridging with a cobweb; the joists run
  one way in a cell and the other way in the next), `basement-ductrun` (the hall's duct narrowed, a copper water main and
  a black gas line on hangers beside it, a gate valve with handwheel and tag or a gauge on some blocks; round 2's
  `basement-duct` kept as it was, Level 31 reuses it), `basement-studs` (kraft-faced batts with flanges, staples, R-11
  print and a tear; a bottom plate, a doubled top plate, fire blocks; turned to the way the wall runs), `basement-rail`
  (the stairs into the Flood: a pipe rail at 45 degrees from a leaning newel down into the water, a baluster standing in
  the water, a wall bracket), `basement-wallrail` (the Escherian stairwell's handrail on its outer wall),
  `basement-slabedge` (the crack's ring: the slab broken back in chunks, two blocks deep, rebar bent down into the hole),
  `basement-scum` (on about a quarter of the Flood's surface: scum and leaves; rarely a board, a sodden box, a bottle, a
  sunken chair; under a third of the sodden boxes, a laptop on the bed).
- **Surfaces:** the cinder block darker and more varied (whitewash left in patches, salt bloom, a water line in some
  alternates, washed-out joints), the stairwell brick darker and sootier.
- **Also new:** `basement-boiler` (the utility rooms' cast-iron sectional boiler, in place of Level 5's), `basement-bar` and
  `basement-stool` (the rec room's home bar, in about 70% of rec rooms), the crack's rubble rebuilt as a heap (`basement-debris`).
- **Layout:** the rec room gets a cue rack on a wall and most a bar with stools; halls that end on the cell's wall end on steel shelving and boxes.
- **Showcase / F7:** new spots heater, tv, cue-rack, joists; F7 `bsmheater` (Water heater); `bsmrec` also finds the TV
  and the cue rack.

### Inventions (round 4)

The washer's and dryer's maker (HOMEMAID SPINMASTER / TUMBLEMASTER), SUDZO soap flakes, the jar labels' years (1957,
'58), the tins' and paint cans' brands (SHERWOOD, DUTCH BOY: generic period names), the MAIN SHUT OFF tag, the R-11
print on the batts, the photograph on the TV, the laptop on the bed under some sodden boxes (the Wikidot account loses
his laptop to the water; where it lies is mine), the sunken chair, the cue rack. The rest is what a real 1950s house
basement has (the lead's notes).

### Shared assets below the bar

- `detail/laundry-washer`, `laundry-dryer`, `tv`, `longsofa-l/r`, `kitchencounter-sink`: boxes with a picture; the Basement
  now places its own (`basement-laundry`, `basement-tv`, `basement-sofa`). Other levels that use them (Level 4's break
  rooms, Level 11's flats) would gain from the same treatment; the Basement's versions could be shared if the lead wants.
- `detail/furniturepile-*` (a slab and a box), `detail/laundrycart` (a box on casters), `detail/icebox` (reads as a modern
  fridge, not a 1950s icebox: rounded top, chrome latch handle wanted).
- Level 5's `boiler` reads as a stove rather than a house boiler; the Basement now places its own sectional boiler. Level 2's
  `oildrum`, the `machinecabinet` and Level 1's `metalshelf` are fine.

### Balance notes for the lead

No new food, water, beds or safe rooms. New drops are small and follow the props: the laundry, TV, boiler, rails, duct run
and shelving drop scrap metal and wire (the sump pipe nothing), the sofa carpet fibre, the cue rack and joists sticks, the bar an empty bottle now and then (half a bottle on average, in rec rooms only; a water container); the scum, slab edge,
sump and laptop drop nothing. The halls' dead ends now hold shelving and boxes (boxes drop carpet fibre, as before).

### What the shots showed (round 4)

Three runs, all with a torch (`%TEMP%/backrooms-shots/basement-r4a`, `-r4b`, and the final `basement-r4c`, `sheet.jpg`
there; 37-38 shots each, no unhandled exceptions).
- **r4a:** the washer and dryer with their consoles and SUDZO shelf, the pool table with its racked balls, the cue rack,
  the plaid sofa and its throw, the console TV with rabbit ears, the workbench with the modelled vice, tools and shop
  light, the joists with their cable and junction boxes, the hall's duct and mains, the kraft-faced studs, the stairs'
  rails with the leaning newel, the scum on the Flood all read. Wrong: every round body (furnace, heater, tins, cans) was
  an eight-pointed star (a square plus the same square turned an eighth), so the labels broke up; the furnace's arms ended
  in loose boxes under the ceiling; the crack's edge bristled with rebar; the pool lamps' brass rims hung under the shade;
  the block walls were still bright under a torch. All fixed before r4b (true octagons from four bars, the arms running
  into the ceiling under boots, one or two rebar ends a block, the rims on the shade's edge, darker block).
- **r4b:** the round furnace with its plate and fire door, the sectional boiler, the bar with its COLD BEER neon and
  stools, the heaped rubble, the stairwell's wall rail. Wrong: the store-shelves spot looked through a doorway at its
  frame; one bar stood hard by a door, its casing cutting the mirror. Fixed (and a smaller bulb in the cage) before r4c.
- **r4c (final):** as r4b with those fixed.

**Still weak:** the furnace body is one block across (a real octopus furnace is wider); the slab edge's jagged steps
repeat block to block round the crack; the shared stools, rug and floor textures are round 3's; the Flood's passages are
still long and alike between the scum and the floating things.

### Questions for the user (round 4)

1. The home bar with its lit COLD BEER neon in about 70% of rec rooms: keep, or rarer (it is the brightest spot in the
   Cellar)?
2. The Basement's own washer, dryer, sofa, TV and boiler could replace the shared ones in other levels (Level 4's break
   rooms, Level 11's flats): worth doing in a later round?
3. The laptop on the bed of some Flood dead ends (the Wikidot account loses his to the water): keep?

### Checks (round 4, commit b13e513b)

`expclash` clean; mod and mapgen build with 0 errors; `layouthash` with `BACKROOMS_NO_EXP_ENTRANCES=1` at layout versions
1 and 12: every line for levels 0-20 and the layout hash equal main's saved files; `regions` Basement 60/60;
`basementstats` (seed 12345, and seed 777 `SPAWN=4000`) 100% of walkable tiles in one piece, 0 sealed, 60/60 arrivals;
`featurecheck` 14/14 Basement features from every arrival; headless (port 43118) `blocksweep` 15778 blocks, 0 threw, a
dummy placed in the Basement, 0 error lines, 0 missing blocks; `GATE_TAG=basementg gate.py --fast --port-base 43110` PASS.
