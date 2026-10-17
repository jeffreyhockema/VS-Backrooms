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
