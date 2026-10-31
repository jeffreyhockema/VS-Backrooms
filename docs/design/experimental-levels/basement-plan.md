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
