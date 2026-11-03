# Level 73 "The Redlands": prototype plan

Internal id 21, `WorldLayout.Level73`, infix `L73`, blocks `l73-`, region per README (NNW, mirror of 188). Disconnected,
cheats menu / `/backrooms goto 73` only. No entities, thresholds, loot, notes, handbook. Research only; nothing touched.

## 1. What the lore says

**Source conflict.** Wikidot has "The Redlands" at Level 73 (by Kitty Rika, subtitle "The home of Coran and his
Children"): https://backrooms-wiki.wikidot.com/level-73. Fandom's Level 73 is a different level, "Shooting Gallery"
(by Lambda, rewrite in progress): https://backrooms.fandom.com/wiki/Level_73 (checked through the API wikitext).
Fandom has no Redlands, so this plan follows Wikidot only.

- **Survival difficulty 5.** Only the Silver Castle is safe; everywhere else is lethal.
- **Shape.** One reachable medium-sized island that every wanderer noclips into. An unexplored ocean surrounds it, with
  unidentified aquatic entities. No other land is known. The ground is crimson-stained, "squalid black-red".
- **The Silver Castle** stands on the island's highest point and is the only building. Gothic, with high thin stone walls
  round it, one open gatehouse and a stone path from the gatehouse to the door. Banners show a silver heart with ram's
  horns on black. Inside: main hall, dining hall with a big fireplace, three floors with two guest bedrooms each, a
  master bedroom on floor 3, two bathrooms, an attic with a balcony. Red velvet curtains hang over every window, and
  the windows behind them are boarded up.
- **Climate / light.** Near-perpetual darkness, no day/night cycle. A full moon hangs fixed and lights the ground. Thick
  black clouds sometimes cover it and it goes fully dark. The text forbids artificial light outside.
- **Entities** (all hostile, about one per 3.3 m2): Windows, Smilers, Deathmoths, Clumps, Dullers, Hounds, Skin-Stealers,
  Death Rats, Camo Crawlers. Unique: CORAN, a 7'9" horned giant with golden chain links for arms, and the Great Hound.
- **To find.** Safety, water and food that refill at the castle table, warm baths, paintings of Frontrooms places.
  Entrances: the Gloom in Level 9.1, and Levels 14 and 6. No known exit.
- **Prototype scope.** The island, the dark red-black air, the moon-dim light and the castle. No CORAN, no children.

## 2. The level in this mod

**Region.** Round noclip region, radius ~320 cells (README default), centre per README. Open sky (add `Level73` to
`IsOpenSky`, so no mantle fill and no ceiling). Inside the region is one island in a sea. The edge uses the existing
open-sky `WallPattern.Rock` rule in `WorldLayout.cs`. Local coordinates: `(ux,uz)` = block offset from the region
centre. Island centre `C` = a hash-jittered point within 40 blocks of the region centre
(`Hashing.Hash(seed, 0, 0, 0x2101)`).

**Heights.** The island rises above sea level, so the default 40-block band is too short. Use a floor drop like Motion's:
`L73Drop = 20`, so `FloorFor(Level73) = FloorY - 20` is the sea surface (water top at rel 0). The island rises at most
24 blocks above that; the castle on the summit adds about 20, so the top is near rel +44. Give the band 56 blocks (an
`L73BandDepth`-style constant, like `L188BandDepth`) and close it with a solid `l73-sky` cloud lid at rel +56 with no
lights behind it. Seabed is at most 12 blocks below the surface. This is a small change in `WorldGeometry` beside
`MotionDrop`.

**Heightfield `H(ux,uz)`, blocks above sea level, a pure function of world coordinates:**
1. `d = distance((ux,uz), C)`. Island radius `Ri = 480 + 120 * (Noise2(ux/160, uz/160) - 0.5)` (a lumpy outline).
   Coast factor `c = smoothstep(clamp((Ri - d) / 90, 0, 1))`, a 90-block beach ramp.
2. Dome: `dome = 16 * (1 - d / Ri)^1.5` for `d < Ri`. The highest point is near `C` (about 16).
3. Hills: copy Level 94's jittered lattice (`HillCentre`/`HillAt`, pitch 40, salt 0x2102): each lattice point has a hill
   with radius `R` 14 to 28 and height `hh` 3 to 8, as parabola `hh * (1 - (r/R)^2)`; take the max over the 3x3
   neighbours. No hills within 70 blocks of `C`, so the castle ground stays calm.
4. Roughness: add `2.5 * (Noise2(ux/24, uz/24) - 0.5)`. Then `H = max(dome + hills, 0) * c`, rounded, capped at 24.
5. Gullies: where `Noise2(ux/60, uz/60) > 0.8` and `H > 3`, lower `H` by up to 6 over a narrow band (red gullies to
   walk along).
6. Sea: where `c = 0`, seabed depth `= -3 - 9 * smoothstep((d - Ri) / 120)`. Fill with `game:water-still-7` up to rel 0.
7. Castle plateau: within 34 blocks of `C`, blend `H` to a constant (the dome value at `C`, rounded) so the castle
   stands level.

**Surface.** `H <= 1`: `l73-ash-sand` (beach). Else `l73-redearth` over 3 blocks of `game:rock-basalt`. Where
`Noise2(ux/9, uz/9) > 0.72`, or `H >= 14`, use `l73-blackrock` instead (outcrops, hill tops). In gullies:
`l73-bloodmud`. Seabed: `game:sand` / `game:gravel` mix by noise.

**The Silver Castle** (fixed plan at `C`, aligned to the axes). A wall ring 56 x 44, 7 high (`l73-silverwall`), a
gatehouse gap in the south wall, and a 4-wide `hub-ashlar` path 26 blocks long from the gate to the door. Main block
40 x 28: three storeys of 6 blocks plus a 5-block attic, a pitched roof of `hub-ceiling`/slate-like dark block, four
corner turrets. Interior from one ASCII template per storey (as in the L188 rooms): hall, dining hall (fireplace),
stair, two bedrooms for the prototype (see question 5), master bedroom as a stub, two bathrooms. Windows are slit
glass with a red curtain block inside; the outside shows plank boarding. Banners on the ring wall.

**Light.** Outside, sky light only and low: sky light about 4 (the "moonlight"), no sun gradient, no block lights outside.
If sun flooding cannot be tuned per level, set the level's open-sky brightness cap to 4. Inside the castle: `l73-sconce`
lamps (block light 7) every 8 blocks along corridors, and the fireplace at 12 in the dining hall.

**Atmosphere.** Fog colour deep crimson-black `#1a0709`, density about 0.0035 outside (visibility ~250 blocks), 0.006
over the sea. Inside the castle: `#1f1209`, density 0.0012. No day cycle. Dark spell: every few game minutes (hash of
the world hour) the fog density rises and sky light falls to 1 for ~40 seconds, the cloud over the moon. Temperature:
about 4 C outside, 22 C in the dining hall, 15 C elsewhere inside. Stability: a small drain (-0.01 per second) outside,
none in the castle. **Sound bed.** Outside: low wind and distant surf, an occasional faint wet pulse (heartbeat-like,
~0.07 volume), far-off howls and scrapes too distant to place. Inside: fireplace crackle in the dining hall, creaking
timber, heavy steps muffled overhead. Reuse the Level 9/10 wind loop and the Hub's dusk bed if they suit; add one new
loop only if neither does.

**Arrival.** Spawn on land with `H > 1`, 60 to 180 blocks from the gatehouse, castle in sight where possible.

## 3. Minimal asset list

**Reuse (vanilla `game:` codes; check against `%VINTAGE_STORY%\assets\survival\blocktypes` before use):**
`rock-basalt` (filler), `sand-*` and `gravel-*` (seabed), `water-still-7` (sea), `planks-aged` or
`agedwallpaperplanks` (castle floors), clear glass (window slits), `banner` (heart banner if the colours allow), a red
wool/carpet variant for curtains if one exists. From the mod: `hub-ashlar` (path), `hub-ceiling` / `l188-roof` (roof),
`l188-sky` as the template for `l73-sky`, `l188-turf` as the template for a ground block, `l188-wall-corridor` for plain
interior walls, `l188-bed`, `l188-roundtable`, `l188-chair` for furniture, `l188-door`-style doors (`l188-guestdoor`).

**New (6 codes, textures via `tools/texlib.py`):**
- `l73-redearth`: packed dark-crimson soil with black speckle and thin blood-red cracks.
- `l73-blackrock`: wet black basalt with a faint maroon sheen and white mineral veins.
- `l73-ash-sand`: grey-pink ash sand with darker clumps (beach).
- `l73-bloodmud`: glossy dark red-brown mud with puddle highlights (gullies).
- `l73-silverwall`: silvery-grey ashlar masonry, cool and bright, with chiselled mortar lines.
- `l73-sconce`: black iron wall lamp with a dim amber glow (light 7).
`l73-sky` (the cloud lid) is a recolour of `l188-sky` and is a 7th code only if the recolour needs its own block.

## 4. Lang strings (`en.json`)

```
"level-21": "Level 73: The Redlands",
"levelhint-21": "Run for the castle. Do not look around.",
"levelname-21": "Level 73",
"level-2101": "The Silver Castle",
"levelhint-2101": "He is the reason you are alive.",
"levelname-2101": "Level 73, the Silver Castle"
```
Key `2101` is for the castle interior only; the island uses `level-21`.

## 5. Open questions (with recommendations)

1. **Fixed moon / sky tint.** Can a per-level sky tint and a moon shape be done without a client change?
   Recommend: tint only (sky near `#0b0507`, sky light 4) now; no moon, as it needs a client shape.
2. **Band height.** Raise the band to 56 or flatten the island to fit 40?
   Recommend: raise it with a 20 block drop; it is a one-constant change like Motion's.
3. **Island vs region size.** A 480 block island in a ~10,000 block region is mostly ocean. Recommend: keep it; sea
   chunks are cheap (water plus a flat seabed). If the generation time shows, shrink the region.
4. **Real water.** `water-still-7` may start flowing at the shore. Recommend: try it, fill during generation only, and
   fall back to a solid `l73-seawater` block if it floods.
5. **Castle interior size.** Eight bedrooms is a lot for a prototype. Recommend: build the hall, dining hall, stair and two
   bedrooms; the rest are plain stubs behind closed doors.
6. **Outdoor darkness.** The lore forbids outdoor lights. Recommend: keep sky light at 4 so terrain is readable but
   frightening, and add no lamps outside.

## Status (prototype built, 2026-10-17)

**Built.**
- *Region and geometry.* Round region of a fixed 16 cells (512 blocks) radius at the README's centre, so it is the same
  in every world size (much smaller than the plan's 320 cells: a 10 km region would be all sea). Open sky
  (`IsOpenSky(Level73)` true). Drop 0, so the floor (`FloorFor`) is the sea's surface; `L73BandDepth = 12`, so the
  usual 40-block band runs rel -12 to +27. The plan's heights did not fit: the island is scaled down (see below). The
  rim cells are a basalt cliff to rel 16 round the sea (built per cell as Motion's backdrop is, since the open-sky edge
  rule would leave the rim open onto Level 10).
- *Island* (`WorldLayout.L73Ground`, a pure function of the block position): centre jittered within 16 blocks of the
  region centre; radius 230 +-20% (Fbm coast); dome to about 9.5 plus hills on a jittered 44-block lattice (radius
  12-22, height 2-4.5, none within 90 of the castle), roughness, a 40-block beach ramp; summit levelled to rel 9 within
  36 blocks (blend to 56); gullies of `l73-bloodmud` along the zero lines of a noise (up to 3 deep); cap 12. Surface:
  `l73-ash-sand` at rel 0-1, `l73-blackrock` on outcrops and at 11+, else `l73-redearth`, over basalt. Sea beyond the
  coast falling to 10 deep over 110 blocks, bed of basalt sand / gravel, still water (`water-still-7`) to rel 0.
- *Silver Castle* (castle-local arithmetic, `L73CastleAt` / `L73KeepAt` / `L73UpperAt`): 48 x 40 curtain wall, 2
  thick, 7 high with merlons; four 6x6 corner towers (10 high); a gatehouse (two 4x5 towers, a 4-wide gate under a
  lintel) in the south wall; a 4-wide `hub-ashlar-worn` path from 26 blocks outside the gate to the keep's 2-wide door.
  Keep 28 x 20, two storeys of 6 and 5 blocks, flat roof with parapet and four 3x3 turrets (top at rel 24). Ground: main
  hall (maroon hotel carpet, bookshelves, grandfather clock, candelabras, two chandeliers) with a hotel-carpet stair up
  its north wall through a hole in the floor above; dining hall (aged planks, a 6 x 2 dining table with 12 chairs, a
  hearth of `game:ember` in a silver-ashlar chimney breast at its east end). Upper: landing, two bedrooms (Level 5 beds,
  nightstands, wardrobes), a bathroom (bathtub, toilet). Windows boarded with aged planks. 32 `l73-sconce` (light 8).
- *Sky and air* (client): fog crimson-black 0.0035 (0.006 over the sea, ground mist at sea level), scene brightness 0.30,
  held at every hour like Level 9's; the outside sky (sun, moon, stars, blue) hidden in a fog sphere of the fog's colour
  (Level 10's trick); a fixed full moon drawn by `src/Regions/L73Moon.cs` (bearing 200, 24 degrees up, 5 degrees across,
  `textures/environment/l73-moon.png`); dark spells (one 2-game-hour slot in three, ~0.35 h) hide the moon, double the
  fog, scene 0.12. Keep: warm brown air 0.0015, scene 0.85, title key 2101 "The Silver Castle".
- *Sound bed* (all reused): vanilla wind, `waterwaves` surf louder toward the coast, wolf howls far off every 45-105 s, the
  Run heartbeat at 0.07; in the keep, wind muffled, `fireplace` positional at the hearth, Level 974 creaks, the End's
  echo step overhead.
- *Rules:* temperature 4 C outside, 15 C in the keep, 22 C in the dining hall; stability 0.9 outside, 1 within the castle.
  Arrivals: 85-165 blocks from the gate on dry land (`IsL73ArrivalSpot`: land zone, height >= 2, not mud).
- *Assets* (`tools/gen_73.py`, matlib/texlib): `l73-redearth`, `l73-blackrock`, `l73-ash-sand`, `l73-bloodmud`,
  `l73-silverwall`, `l73-sconce` (4 sides, json shape `shapes/block/73/sconce.json`), the moon picture, lang keys.
- *Harness:* `73stats` and `73map` in `tools/mapgen/L73Stats.cs`.

**Numbers.** `73stats` (seed 12345, full size): 783 cells, 0.6 ms a cell; land 25.5%, sea 58.9%, castle 0.24% (1920
tiles), rim 15.3%; peak 11, deepest sea 10; arrivals 60/60 on dry land, 67-172 blocks from the gate. `SPAWN=1000`: 748
cells, land 26.7%, sea 57.0%, arrivals 60/60. `regions`: Level 73 60/60, wrong level 0, pockets 0 (both sizes).
`layouthash`: every per-level line for 0-20 unchanged. Headless: `blocksweep` 7825 blocks, 0 threw; dumps of the castle
and the island show every block as planned, no missing blocks, shapes or textures logged for 73.

**Skipped.** Thresholds, entities (CORAN, the children), dens, loot, notes, handbook; banners; red curtains (the
windows are only boarded); the attic and balcony, the third storey, the master bedroom; food and water at the table;
doors (doorways are open).

**Known gaps / to check in a client.** The moon renderer, the sky sphere and the night's brightness are untested in a
client (headless only): check the moon's place, size and glow, that the sky really hides (no sun at noon), that the
island reads at scene 0.30, and the sconce model's orientation. The map layer (`BackroomsMapLayer`, the grouped case
of floor to floor+5) is not taught the island's heights. Sunlight floods the keep's ground storey through its door
(as it would). Vanilla basalt and ember bypass the salvage Breakdown.

## Detail pass (2026-10-30)

World + content, still unlinked (cheats menu / `/backrooms goto 73` only). Lore source: Wikidot only
(`lore/73-brief.md`, `lore/DECISIONS.md`).

**Built**
- *The island.* Unchanged in shape; the sea now falls to 6 deep (was 10) so the level's band could start 6 below the
  floor (`L73BandDepth` 12 to 6) and reach rel 33 for the keep's three storeys and attic. Summit flat within 40 blocks
  (blend to 62) for the bigger castle. Arrivals now 60-120 blocks from the gate (was 85-165: "a short run so a fast
  player can make the door"; `73stats`: 62-181 before, see the numbers below). Old bones on the fields (a bone pile in
  about 260 land tiles, a ribcage in 900, a backpack in 3000) and a loose note in about 2850 ("gear and dark bones").
- *The Silver Castle* (castle-local plan in `WorldLayout.Level73.cs`): curtain 56 x 48 (was 48 x 40), corner towers,
  gatehouse, path; the keep 36 x 24 with **three storeys of five blocks** (`L73RoomAt`): six **guest rooms** (two per
  floor, one at each end, **two beds each**, nightstands, wardrobe, dresser, chair), the **main hall** (banners, clock,
  sofas, candelabras), the **dining hall** with the hearth and the **table of plenty** (12 x 2, 24 places), a **gallery**
  of paintings, two **bathrooms** (G and 1st floor: two warm barrels each, toilet, cabinet), a **sitting room** round the
  chimney breast, a **library**, the **master bedroom** (Coran's: a bed of two, desk, wardrobes, bookshelves) and a
  **store-room** off it (three supply boxes, crates, Hound bones). Three flights of stairs, each landing where the next
  begins. Flat roof terrace with parapet, turrets and the chimney stack; on it the **attic** (walls 3 high, stepped slate
  roof, crates, bones, a great skull, a pack) **chained shut**, with its **balcony** over the front door. Every outer
  window (40) is **boarded** (`l73-boards`) with **red velvet curtains** inside (pelmet, gold fringe); **banners**
  (silver heart with ram's horns on black, two blocks long) inside and on the walls outside and round the courtyard;
  **paintings of the Frontrooms** (six scenes). The castle's masonry, boards, slate, doors, table, barrels, curtains,
  banners and paintings never break (attribute `l73Fixed`, one line in `Salvage/Breakdown.cs`).
- *The door* (`Regions/L73System.cs`, `BlockL73Door`): two studded oak leaves three high with the emblem; four blows in
  3.5 s from outside open it ("bang on the door as loud as possible"), one touch from inside; it shuts itself after 6 s
  (not on anyone in the doorway). The attic's doors only say it is off-limits.
- *The table and the baths*: a place set (stew, bread, a glass of water) feeds 600 satiety and 700 hydration and is set
  again 4 game hours later (`BlockEntityL73Table`); a barrel washes and warms (body temperature to normal) or fills an
  empty bottle with clean water.
- *The light rule*: a light of 8+ in hand outside the walls raises a 0.7 noise every 4 s (MenaceSystem's noise bus: the
  hordes come to it), and a warning the first time.
- *The hordes* (director, single lines in shared files): band Threshold everywhere outside the walls, Safe within
  (`L73System.BandAt`); danger 0.9; solitude 0.15 (busiest of all); Survival Class 5 (two kinds at once); roster from the
  page: Hounds 3-5, Smilers 1-2 (dark), Death Rats 3-5, female Deathmoths 3-5, male Deathmoths, Skin-Stealers, Dullers,
  Clumps (ambush); distant sounds of howls, wings, drag, hurt.
- *CORAN* (`tools/gen_73_coran.py`: rig model 38 px tall, horned head, black shell, glowing chest heart, eyes on a cord,
  gold chain arms of five links ending in spiked gauntlets; animations idle, walk, run, attack, sweep, listen, bow,
  hurt; synthesised sounds: steps, chains, strikes, voice, roar, hurt). `EntityCoran` never takes damage and is not saved
  with the world; `L73System` keeps one about outside the gate while anyone (or a test dummy) is in the level and
  removes him a minute after. `AiTaskL73Coran`: hears every hostile within 40 blocks of him that is outside the walls
  and within 140 of the castle, runs it down and kills it (a gauntlet strike, a sweep of both when there are several);
  otherwise walks a round 36-75 blocks from the castle and stops to listen; bows and greets a wanderer within 5 blocks
  (every 4 minutes); right-click: one of eight lines.
- *Content*: six common notes and one folded note (`gen_notes.py` Level 73 block), loose notes in the castle (4) and on
  the fields; a handbook page "Level 73: The Redlands" (`gen_73_lore.py`, registered in `GuideSystem.Added`); title and
  hint lines kept. Loot: the store-room's supply boxes (the castle's food is the table).
- *Assets*: `tools/gen_73_castle.py` (15 block types in all now, 30 shapes, 30 more textures), `gen_73_lore.py`
  (messages, Coran's lines, handbook page).

**Choices against the brief**
- Children of Coran (37 peaceful NPCs): not built (DECISIONS: one key creature per level); the notes and the handbook
  speak of them. Windows, Camo Crawlers and the sea's creatures: omitted, named in the handbook.
- The knock is right-click (four within 3.5 s); a left-click on a door does nothing.
- Food at the table is eaten at the table (not handed out as items), so the castle cannot be farmed for stock.
- No Great Hound skeleton on the plateau (small props would not read as giant); a great skull lies in the attic instead.

**My inventions** (not in the lore): the room plan beyond what the page names (gallery, sitting room, library,
store-room, which floor holds which bathroom); the four-knock rule; the 4-hour refill; the light rule's noise; the
balcony's place over the door; Coran's patrol ring, hearing range and greeting lines; the bones and dropped packs on the
fields; the note texts (from the brief's suggestions) and the M.E.G. folded note (after the page's audio log).

**To check in-game (screenshots)**: the door leaves' orientation and the open leaves' swing; curtains' folds and
pelmet against the window boards; banners hanging two blocks (inside, the court, the outer walls); paintings' frames;
the table's place setting and the cleared one; the bath barrels; the attic's stepped slate roof, the chimney and the
balcony from the courtyard; Coran's model and animations (walk, run, strike, bow), his size against the gate; the
island's bones; that light from the castle does not spill out (all windows boarded).

**Checks (2026-10-31)**: `expclash` clean; mod and mapgen build with 0 errors; `layouthash` at layout versions 1 and 12:
every line for levels 0-20 and the `layout hash` identical to main's (only 21-28 and `far places hash` differ);
`regions` 60/60 arrivals in Level 73, none in the wrong level or in pockets; `73stats` OK (12 guest beds, 4 barrels,
24 places, 40 windows, nothing misplaced; arrivals 62-181 before the change to 60-120); headless (ports 43100/43101):
dummies land with 0 error lines, `blocksweep` 8718 blocks 0 threw, the director sends Hound packs (3-5), Deathmoths
and Dullers within seconds of a dummy outside the walls, Coran is put down by the gate and hears them (`entitylog`);
`GATE_TAG=l73 gate.py --fast --port-base 43100` PASS. Untested headless (no movement without a player, no clicks):
Coran's run and strike, the door, the table, the baths.

### Round 2 (2026-10-31): looked at in the client, fixed

Round 1's shots (the lead's review): huge blurry white cloud boxes over the whole sky, the ground a flat featureless
dark-red plate, the castle a small grey silhouette.

**What changed**
- *Sky.* Vanilla's clouds are off in the level (`clouds: 0` on the island's, the sea's and the keep's air and the
  level's base line; the dark spell now carries them through rather than dropping back to vanilla's). The lore's black
  cloud stays what it was: the dark spell takes the moon away and thickens the murk. The moon moved to bearing 10, 18
  degrees up (was 200 / 24), so that from the gate's side, where most runs end, it hangs just over the castle.
- *Ground.* Hills on a 34-block lattice (was 44), 2.5-6.5 high (was 2-4.5), rougher ground (1.8, was 1.2); **tors** of
  black rock (a jagged core and a lower spur, 3-8 above the ground, on a 26-block lattice, half of the points, none near
  the castle's hill or along the path's line; `FloorKind.L73Tor`, black rock right down; never an arrival); the fields
  in **blackened stretches** (`l73-burnt`, charred earth flecked with ash: the lore's "blackened fields") and patches of a
  **crust of dried blood** (`l73-crust`) also fringing the gullies; **dead grass** (`l73-deadgrass`, short/mid/tall,
  black-red withered blades, fixed colours, no climate tint) in broad patches on the red earth, a burnt stubble on the
  blackened stretches; more bones (piles 1 in 170 tiles, jaw skeletons 1 in 1100), fewer of the upright ribcages.
- *The Great Hound's bones* (`L73HoundBones`, `l73-bone`): a skeleton 39 long, lying on its belly on the fields
  south-east of the castle beside the path: skull, neck, an arched spine over seven pairs of ribs reaching to the ground
  (two broken), pelvis, legs stretched out, tail. Its footprint is sealed (no arrivals, no props); it sinks into the
  ground where the ground rises.
- *The castle's outline:* steep slate roofs tapering to spires on the four corner towers, slate caps and spires on the
  gate towers, slate caps and needle spires on the keep's four turrets (their tops one under the band, as the attic's
  ridge), so it reads as gothic, not as a box, from the fields.
- *The keep up close:* buttresses against its walls between the windows (slate-capped), a pointed slate canopy over the
  door, string courses of smooth stone at every floor; inside, every room's walls are **mahogany panelling** to the chair
  rail and **red damask** above (`l73-wainscot`, `l73-damask`: the outer wall's blocks lined on the room's side only,
  silver outside; partitions lined both sides; the chimney stays stone), where round 1 showed bare grey brick ("well
  maintained and lavishly decorated"); two round tables with chairs in the main hall, which was bare.
- *Arrivals* face the castle's gate (`L73ArrivalYaw`, one line in `ThresholdSystem.cs` beside the Hub's).
- *Showcase spots* (`WorldLayout.Level73.Showcase.cs`, 14): the run with the moon over the castle, the path's foot, Coran
  on the hill, the gatehouse, the keep's front, the main hall, the dining hall, a guest room, a bathroom, the master
  bedroom, the roof terrace and attic, the Great Hound, the fields, the north shore under the moon.
  `/backrooms l73coran x z [heading]` puts Coran down standing still for 30 s (for the Coran spot).

- *Moonlight:* the island's scene brightness 0.30 to 0.36, the sea's 0.28 to 0.33, so the fields read by the moon alone.
- *Shared files (one line or one block each):* `ThresholdSystem.cs` (the arrival facing), `AtmosphereSystem.cs` (the
  level's base line: clouds off, scene), `Tiles.cs` (three floor kinds 268-270 in the level's block), `mapgen.csproj` and
  `tools/clientrig/rig.py` (exp/36's fix, cherry-picked: mapgen compiles `Showcase.cs`, the rig keeps the showcase shots).

**What the shots showed** (four client runs, no torch: `%TEMP%/backrooms-shots/73-r2a`, `-r2b`, `-r2c`, `-r2-final`).
Run a: the clouds gone, a black sky with the moon over the castle; grass too pale and wheat-like, the blood crust like
cobbles; the tower tops flat chimneys. Run b (first with showcase spots): the castle and its rooms read, the dining
hall the best shot; the keep's front a flat box with slits, the rooms bare grey brick, the main hall empty, the Great
Hound like standing stones from too close, Coran small. Run c: buttresses, canopy and string courses make the keep read
gothic; the panelling and damask make the rooms the lore's "lavish"; the damask's motif too coarse. Final: a finer
damask, a little more moonlight, the Hound from off its head (skull and arched ribs read). Still weak: the fields far
from the castle are very dark and fairly even (by the lore's light rule); the bathroom is only its two barrels; the
pale stone path is brighter than anything else outdoors; the attic is a plain slate-roofed box.

**My inventions (round 2):** the tors, the blackened stretches and crust patches as surfaces, the dead grass (the lore
says only "blackened fields"), the Great Hound's skeleton on the fields (the lore names it slain by Coran, nothing of
its remains), the spires, buttresses and canopy, the panelling and damask (the lore: "lavishly decorated"), the moon's
bearing, the arrival facing.

**Checks (round 2):** `expclash` clean; mod and mapgen build with 0 errors; `layouthash` v1 and v12: every line for
0-20 and the layout hash identical to main's; `regions` 60/60 in Level 73 (0 wrong, 0 in pockets); `73stats` OK (peak
17 on a tor, arrivals 52-121 from the gate, the Hound's 615 tiles sealed, 12 beds, 4 barrels, 24 places, 40 windows);
headless dummies in the level with 0 error lines, Coran put down and moved by `/backrooms l73coran`;
`GATE_TAG=l73g gate.py --fast --port-base 43100` PASS (a separate build tag so the gate did not rebuild under a
queued screenshot run).

## Links (2026-10-31)

The ways in and out of LINKS.md's Level 73 section (the lore: "Stay near the Gloom for too long on Level 9.1"; "from Level 14
and Level 6"; no known way out; the user chose "Coran leads you out"). Code: `WorldLayout.Level73.Links.cs` (layout, the
finders), `WorldGenerator.L73.Links.cs` (blocks), `ThresholdNetwork.L73.cs` / `ThresholdSystem.L73.cs` (the network),
`Regions/L73System.Links.cs` (the lingering, the night's rest, Coran's lead, the north door), `AtmosphereSystem.L73.cs`
(`L73Lingering`: what the player sees and hears), assets `tools/gen_73_links.py`.

**Built**
- *The Gloom (Level 9, one way).* One Suburbs cell in 2000 rolls it (own salt 0x2140, the hook last in precedence); where the
  cell has a clear round of 4 blocks of lawn, pavement or asphalt with nothing on it, a lumpy pool 5-7 across is marked
  (`Unders.L73Gloom` its heart, `L73GloomRim` its rim; nothing else in the cell changes: the harness checks every tile).
  Blocks: black dull ground (`l73-gloom`, never breaks) and over the heart a black murk 2 high (`l73-gloomair`: no body,
  `BlendNoCull` so it is dark from inside too, faces between two of it merged). Standing in it: warnings at 12, 40 and 70 s,
  taken at 90 s ("a minute or two, warned"); stepping out says so, and 20 s out lets it go. On the client a black fog sphere
  closes in round the player (tighter the longer they stay) and a heartbeat comes, quicker and louder. Arrival: on the island's
  dry land (the level's own arrival finder, facing the gate), the same place for the same Gloom.
- *Level 6's deepest dark (one way, no tile).* One cell of Lights Out in 2500 (salt 0x2142; never the Snackrooms; only where
  the cell's north-west corner is wall, which stands for it in the network). Lingering there with no light in hand and block
  light <= 3 at the eyes: warnings at 60, 120 and 160 s, taken at 180 s. The client plays a faint, slow heartbeat there with no
  light in hand (nothing marks it otherwise: it is Level 6).
- *A night under his roof.* Hours asleep in a bed inside the keep add up (`backrooms:l73Slept`, watched); at 4 the player is
  `backrooms:l73Rested` and told so ("If you would go, he is the one to ask"). Both are cleared on any arrival in the level.
- *Coran leads you out (one way, to Level 9).* Sneak + right-click Coran: not rested, he says to rest first; rested, he says
  he will take you and walks round the walls on a ring 44 blocks out (a step of 0.55 rad at a time, the short way), waiting
  and calling when you fall more than 10 blocks behind, still killing whatever comes; at the north door he tears the chain off
  (strike, chain) and the door opens for 20 s (never shutting on anyone in it). Gives up after 5 minutes, or 30 s with you
  more than 64 blocks off. The north door: two leaves two high in the outer course of the north curtain wall (castle u 27-28,
  v 0), black iron-bound oak chained and padlocked (`l73-postern-*`, class BackroomsL73Door, `l73Door: postern`); its inner
  course is silver on the courtyard side and black on the door's (`l73-postern-back`), so from the courtyard the wall is only
  wall. Open, the leaves swing out against the wall and the doorway is black all round. Walking into it while open
  (`L73Walked` + `L73MayPass`) takes you to an open spot in the Suburbs, the same one every time. Right-clicked shut: "black
  and chained ... no door shows there" (rested: "ask him to lead you out").
- *Text.* Handbook page: "Ways in" (the Gloom, Level 6, Level 14 as the page's rumour) and "Ways out" (Coran). Messages for
  every warning, arrival and line of Coran's (`l73-gloom-*`, `l73-dark-*`, `l73-arrive-*`, `l73-coran-lead-*`, `l73-rested`,
  `l73-postern-*`, `l73-out-arrive`). Notes: one at the end of Level 9's track ("The Gloom", Nell) and one at the end of
  Level 6's ("Deeper"), with this level's keys (`l73-l9`, `l73-l6`).
- *Dev commands.* `/backrooms l73way gloom x z | dark mx mz | out` (where a way leads, written down), `l73dummy gloom|dark` (a
  straw dummy in the nearest one, carried to the island when it is taken), `l73rest [player]`, `l73lead [player]`,
  `l73postern open|shut`.
- *Harness* `73links`; *showcase*: `north-door`, `north-door-open`, `gloom`, `gloom-inside`, `deepest-dark`.

**My inventions** (not in the lore): the Gloom's look (black ground, a murk two high) and its timings; the Level 6
way's place (rare cells, no light) and timings; the whole way out: the night's rest as the condition, sneak-and-speak to ask,
the lead round the walls, the north door in the outside of the curtain wall with no courtyard door behind it, and Level 9 as
where it leads (Coran "newly recovered from the Gloom" in the page's M.E.G. log: he knows the way back to where the Gloom is).

**Rows for the guide's ways-between-levels table** (for the lead to merge into docs/GUIDE.md / gen_guide.py):

| From | Threshold | To | Way back |
|---|---|---|---|
| Level 9 | Standing a minute and a half in the Gloom, a rare pool of darkness in a yard or a street (black ground, a black murk over it; warned three times) | Level 73, on the island in sight of the castle | None (one way) |
| Level 6 | Lingering three minutes with no light in the very deepest dark of Lights Out (one cell in 2500; warned three times) | Level 73, on the island in sight of the castle | None (one way) |
| Level 73 | Asking Coran to lead you out (sneak and right-click him) after a night asleep in the castle: he walks you to the chained north door in the outside of the curtain wall and opens it | Level 9, out in the Suburbs | None (one way) |

**Numbers (seed 12345, full size, `73links`)**: the Gloom: 9 of the 20 Level 9 cells that roll it hold one, about 0.22 a km² of
Level 9 (some 2 km apart, about nine in the world); 20-29 tiles each, mostly on streets (asphalt 85, lawn 55, pavement 26 of 200
tiles); nearest to spawn 6.72, 6.81, 7.37, 7.48 km. Level 6's deepest dark: 0.39 a km² of Level 6 (about 1.6 km apart; five
in the world); nearest 4.25, 4.28, 4.45 km. Every way in leads onto the island's dry land; the north door to an open street
in Level 9.

**Checks**: `expclash` clean; mod and mapgen build, 0 errors; `BACKROOMS_NO_EXP_ENTRANCES=1` layouthash at layout versions 1
and 12: every line for 0-20 and the layout hash identical to main's; without it, no line for 0-20 moves either (the hash's
sample cells hold no Gloom); `regions` 60/60 in Level 73; `73stats` OK; `73links` OK (every Gloom changes only its own tiles'
Under). Headless (port 43100): `l73way` for all three ways, a straw dummy taken by the Gloom (90 s) and by the dark (180 s),
0 error lines. Client rig (two runs, port 43105, seed 12345): a player in survival warned three times and taken by the
Gloom, and by Level 6's dark; rested, led by Coran (he ran from the gate round the walls to the door) and through the open
north door into the Suburbs; showcase shots of the north door shut and open, the Gloom from outside and inside.
`GATE_TAG=l73g gate.py --fast --port-base 43100` PASS.

**To look at**: the Gloom's murk from outside is a flat black slab over black ground: it reads as wrong, but blocky; a
softer edge would need a shape of its own. The door opens only once whoever he leads is within 12 blocks of it.

## Round 3 (2026-11-01): the detailed visual pass

From the round-2 final sheet (`%TEMP%/backrooms-shots/final-r2/73`), the lead's notes, the brief and DECISIONS.md, and
the released levels of the same kind (Level 5's hotel rooms and furniture, Level 11's signs, Level 10's open fields).
Tier A must, B should, C nice. Inventions are marked (inv.).

### List

**1. Layout realism**
1. [A] [done] The ground floor's north-east room becomes the **kitchen** off the dining hall (inv.: the lore's food "appears", but a
   castle has one): a cooking hearth with its chimney breast, a cauldron, a worktable, shelves of pots, a butcher's block
   (the lore: "Hound is the fuel"); the gallery's paintings go to the halls and landings.
2. [A] [done: the pantry; no sink] A **pantry / scullery** at the kitchen's north end behind a partition (sacks, barrels, shelves, a sink).
3. [A] [done] The **master bedroom** (now a 25 x 10 hall) is cut in two: Coran's bedchamber in the east (8 x 10) and his solar
   (a study round the chimney breast) in the middle, the partition and its doorway restored.
4. [A] [done: a laundry behind a wall, linen racks] The **bathrooms** (8 x 10 tiled boxes) get a laundry end (the lore: the barrels are for "bathing and washing clothes"):
   wash tubs, a drying rack with linen, a partition screen.
5. [B] [done] A **cellar** under the kitchen, by a stair down (wine racks, barrels, the Hound-meat store: "Hound is the fuel").
6. [B] [done] The **courtyard** used like one: a covered well (dry, boarded: inv.), a cart, barrels and a pile of Hound carcasses
   by the kitchen side (the fuel), flagstone walks from the gate round the keep; never in front of a window or banner.
7. [B] [skipped: the gate towers are solid masonry; time] A **guard room** in the gatehouse passage's flank (racks, a bench, a brazier) (inv.).
8. [C] [skipped] A **chapel / shrine** corner of the Children (candles, the emblem) on a landing (inv.: the "cultish" frame).

**2. Multi-block objects**
9. [A] [done] **Canopied beds**: the lore's "two large beds each" as two hotel beds side by side (sleepable, so the night's rest
   still counts) under one four-poster frame: four posts, a tester, a valance and drapes tied at the posts, a carved headboard.
10. [A] [done] **Fireplaces with chimney breasts** in every guest room (the end wall), the solar, the sitting room and the master
    bedroom: jambs, a firebox with burning logs and firedogs, a mantel with candlesticks, the breast rising to the ceiling,
    stacked storey over storey into chimney stacks on the roof at both ends.
11. [A] [done] The **grand stair** with a balustrade (balusters and a sloped rail on its open side, a rail round the stairwell
    on the floor above) and panelled sides instead of a solid stone mass.
12. [A] [done: one beam size] **Beamed ceilings**: dark oak beams across every room under a plaster ceiling (the plain plank ceiling the lead
    named), a bigger cross-beam over the main hall.
13. [A] [done] **Rugs** in the rooms (bordered, red, blue and gold), each a rectangle with its border.
14. [A] [done] The **kitchen hearth** as one object: a wide arched hearth with a cauldron on a chain and a spit.
15. [B] [done] **Tapestries** two blocks by two on the main hall's and the landings' walls (the castle under the moon; the emblem).
16. [B] [done] **Chests** at the foot of the beds (iron-bound oak).
17. [B] [done: no towel rail] A **washstand** with a basin and a mirror over it in each guest room and the bathrooms; a towel rail.
18. [B] [done] The **Great Hound's skeleton** remade with thin bones (spine, ribs, legs as bones, not cubes) so it reads; a darker,
    aged bone texture; its spot from where its profile shows (the lead: "an unreadable pale block shape").
19. [B] [done] **Dead trees** on the island: charred trunks with bare twisted branches, several shapes, alone or in twos.
20. [C] [partly: a chest added] Attic: trunks, sheeted furniture, stacked frames, dust (seen only through the shut door's gap and the roof).

**3. Signs and text**
21. [A] [done: by the keep's door and on the gatehouse] An **M.E.G. placard** in the mod's convention beside the keep's door and the north door: "M.E.G. - LEVEL 73 -
    CLASS 5", second line "RUN. NO LIGHT. BANG ON THE DOOR" (inv.: placing; the lore's procedure is the M.E.G.'s).
22. [A] [done] A **needlework sampler** in the main hall: "WE ARE SAFE HERE. WE ARE LOVED HERE." (the page's own words).
23. [B] [done] **Brass plates** by the guest rooms' doorways ("I" to "VI"), "BATH", "LIBRARY", "KITCHEN" (as a house of this kind).
24. [B] [done] A **notice** by the curtains on each landing in a careful hand: "DO NOT LOOK OUTSIDE. - C." and by the attic stair
    "THE ATTIC IS HIS" (the lore: "CORAN has declared the attic off-limits"; "Do not look outside").
25. [B] [partly: the lectern and book, no text to read] A **visitors' book** on a lectern in the main hall, the Children's tally ("37", "There is nobody here but us").
26. [C] [skipped] Coran's tally of kills scratched on the solar's wall (inv.).

**4. Detail visuals**
27. [A] [done] **The island's relief**: a shore shelf (a step down of black rock to the beach in places), rolling rises and
    long ridges between the hills, deeper gullies, so arrivals see a landscape, not a plate.
28. [A] [done] **Worn paths** toward the castle: trodden tracks of dark mud with footprints winding in from the shore from
    several bearings and joining the stone path (the lore: everyone runs straight to the castle).
29. [A] [done] **Rocks and boulders** on the fields (black rock, one to three blocks), beside the tors.
30. [A] [done] A **cornice** at the top of the keep's walls (the damask's top course with a carved moulding) and a skirting.
31. [B] [done] The **stone path** darkened and worn (it is the brightest thing outdoors): stained, cracked slabs.
32. [B] [done] **Floors by room**: flagstones in the kitchen and the pantry, boards elsewhere, carpet in the hall, tiles in the baths.
33. [B] [done] **Candle light with rhythm**: the corridors' sconces, candles on the mantels, the kitchen's fire glow; dark corners
    in the store-room and pantry.
34. [C] [partly: heaps of the dead in the courtyard and cellar] Fresher carcasses near the castle's hill (what Coran leaves; the brief's "gear and dark bones").

**5. Lore alignment**
35. [A] [done] Lore check of every room: main hall, dining hall, six guest rooms with two large beds, master bedroom on the
    third floor, two bathrooms with barrels, attic off-limits with balcony, curtains and boards at every window, banners,
    paintings (the gallery's moved to the halls, still "numerous").
36. [B] [done: a close spot] Coran up close and at distance (his idle, his heart's glow); a spot close to him.
37. [B] [done] Showcase spots for every new set piece (kitchen, solar, cellar, a canopied bed, the stair, the fields' trees and
    tracks, the shelf), all from the layout.

**6. Released-level alignment**
38. [A] [done] Block names for every new block in the HUD (en.json), pick-block works, nothing breaks (the castle's `l73Fixed`).
39. [B] [done] The handbook page and the notes name what is new (the kitchen and cellar are not lore: no; only what the page
    says). The notes' voice unchanged.
40. [B] [done: the nearest fire on one's storey] Hearth crackle near the fires (the sound bed inside), if a loop exists to reuse.
41. [C] [skipped] The title and hint lines and the map's colour for the new floor kinds (tracks, flagstones).

### What was built (round 3)

- *The keep by function* (`L73RoomAt`): the ground floor's north-east room is now the **kitchen** off the dining hall (a
  cooking hearth with a cauldron and a spit, worktables under a rack of copper pots, larder shelves) with a dark **pantry**
  behind a wall and, down a stair from it, a **cellar** (barrels, crates, heaps of the hordes' dead kept for the fires);
  the bathrooms got a **laundry** behind a wall (racks of linen drying); the third floor's 25-wide "master bedroom" is now
  Coran's **solar** (study round the chimney breast's fireplace) and his **bedchamber** behind the restored partition; the
  gallery's paintings went to the hall and the landings.
- *Multi-block objects*: **four-poster canopies** over every large bed (two hotel beds side by side under posts, tester,
  valance, drapes; Coran's in black; the beds stay the mod's sleepable beds); **fireplaces** in every guest room, the
  library, the master bedroom and the kitchen (jambs, a fire of logs on firedogs, a carved mantel with candles, the
  chimney breast to the ceiling, stacked storey over storey into **chimney stacks** on the roof), and in the chimney over
  the dining hearth on the two upper storeys (the sitting room's, the solar's); the dining hearth's fire and mantel;
  **rugs** with borders; **oak beams** under plaster ceilings (every floor slab is now boards on top, plaster below);
  a **cornice** at the top of every papered wall; the **grand stair's balustrade** (balusters and a stepped rail on its
  open side, rails round each stairwell above), panelled under its treads; **tapestries** two by two (Coran over the slain
  Great Hound; the castle under the moon); chests, washstands with mirrors, wing chairs, sideboards, a lectern with the
  visitors' book; in the courtyard a flagged walk round the keep, a boarded **well** under a roof, the kitchen yard with
  heaps of the dead, a hand cart and barrels; dust-sheeted furniture in the attic; carcasses hung on hooks in the cellar;
  the kitchen and pantry limewashed instead of papered.
- *Text*: an **M.E.G. placard** ("M.E.G. - LEVEL 73 - CLASS 5 / RUN TO THE CASTLE. / NO LIGHT. BANG ON THE DOOR") on the
  gatehouse beside the gate and beside the keep's door; the **sampler** "WE ARE SAFE HERE. / WE ARE LOVED HERE." by the
  main door; **brass plates** by the doorways (guest rooms I-VI, BATH, LAUNDRY, KITCHEN, PANTRY, DINING, LIBRARY, SOLAR);
  **pinned notes** in a careful hand ("DO NOT LOOK OUTSIDE. - C." by the curtains, "THE ATTIC IS HIS. DO NOT GO UP." by
  its stair, "IF THEY BANG, LET THEM IN." by the door, "WE ARE THIRTY-SEVEN." on a landing).
- *The island*: long low **ridges** across the fields, a **shelf** (a scarp of black rock 2-3 high over the beach) along
  stretches of the coast, deeper **gullies**; six **worn tracks** of trodden mud winding in from the shore and round the
  hill to the foot of the stone path (`FloorKind.L73Track`, 271); **dead trees** (charred trunks with a root flare, two or
  three crooked branches, a forked top; 112 on seed 12345); **black boulders** (one or two high, some with a smaller stone
  beside); the stone path relaid in **darker, stained flags**; the **Great Hound** redrawn in thin bones joined to their
  neighbours (spine, ribs, legs, tail; the skull solid) in an older, darker bone.
- *Sound*: the fire's crackle now comes from the nearest fire on one's storey, not only the dining hearth.
- *Showcase*: new spots `coran-close`, `keep-door`, `stair`, `kitchen`, `cellar`, `guest-fire`, `library`, `solar`,
  `track`, `dead-tree`; `great-hound` now side on; `gatehouse`, `bathroom`, `master-bedroom` re-aimed.
- *Text from the balance review (lead's request)*: the third warning in Level 6's deepest dark now says where it leads is
  worse than here; the handbook page: "Near the castle, where CORAN hunts, the hordes are thinner; beyond the hill they are
  not." It also names the kitchen, the study, the large curtained beds and the sampler.

### Inventions (round 3)

The kitchen, pantry, cellar, laundry and solar (the lore names the main hall, dining hall, guest rooms, master bedroom,
bathrooms and attic only); the fireplaces in the guest rooms and the rest (the lore names the dining hall's); the
canopies; the tapestries and their pictures; the sampler's place (its words are the page's); the plates, the notes' words
(after the lore's "Do not look outside", "CORAN has declared the attic off-limits", "exactly 37"); the M.E.G. placards
and their wording (the M.E.G.'s procedure from the page); the courtyard's well (boarded, dry), cart and heaps of the dead
("Hound is the fuel"); the tracks, ridges, shelf, dead trees and boulders (the lore says only "blackened fields").

### Balance notes for the lead

- No new food or water: the larder shelves, sacks, barrels, heaps of the dead, the cart and the well are the level's own
  fixed blocks (`l73Fixed`, no drops); the well is boarded. The kitchen's pantry deliberately does not use the mod's
  `PantryShelf`/`SeedSacks` props (they drop canned beans, flour, seeds).
- The new hotel furniture (wing chairs, coffee tables, sideboards) can be salvaged like the castle's existing hotel
  furniture (chairs, sofas, bookshelves) already could.
- The guest rooms now hold two hotel beds per large bed (24 beds where there were 12): more places to sleep the night's
  rest, same safety.
- Dead trees and boulders on the fields are cover and obstacles on the run (trunks block, boulders 1-2 high); they give
  nothing. The tracks change nothing but the floor's look.
- The cellar is inside the keep (safe, 10 C).

### What the shots showed (three client runs, no torch: `%TEMP%/backrooms-shots/73-20261101-013959`, `-024808`, final `-033416`)

- Run 1: the rooms read as a lived-in castle at last (canopied beds, fires, beams, cornices, rugs, the stair's balustrade,
  the tapestry of Coran over the Hound, the plates and the sampler); the island reads as a landscape from the arrivals
  (ridges, gullies, dead trees against the sky, boulders, the castle on its hill); the Great Hound reads as a skeleton
  (arched ribs, spine, the skull). Wrong: every rug's border ran through its middle (the up face shows its texture turned
  half round); the mantels carried a picket of candles; the kitchen was papered in damask; the bathroom and cellar were
  near black and the cellar bare; the dead trees' branches stood a little off their trunks.
- Run 2 (after the fixes): rugs right, kitchen limewashed, the cellar's carcasses on hooks and barrel rows, the bath lit.
  The kitchen's hearth was a low room fireplace.
- Final: the kitchen's hearth open two high under its mantel. Still weak: the far fields and two of the four random
  arrivals are nearly black (the lore's dark: no torch, and a black-cloud spell may have been on); the kitchen's pots and
  the heaps of the dead are blocky; the attic is still only seen from the roof; the `deepest-dark` link spot (Level 6,
  `WorldLayout.Level73.Links.cs`, not this round's to touch) failed its shot in all three runs.

### Checks (round 3)

`expclash` clean; mod and mapgen build with 0 errors; `layouthash` (`BACKROOMS_NO_EXP_ENTRANCES=1`) at layout versions 1
and 12: every line for 0-20 and the layout hash identical to main's; `regions` 60/60 in Level 73 (0 wrong, 0 in
pockets); `73stats` OK (24 guest beds = 12 large, 4 bath barrels, 24 places, 32 windows, 0 misplaced, 112 dead trees,
arrivals 57-133 from the gate); headless (port 43102) dummy placed in Level 73 with 0 error lines;
`GATE_TAG=l73g gate.py --fast --port-base 43100` PASS.

### Questions for the user

- The kitchen, pantry, cellar and Coran's solar are inventions (the page names none of them): keep them?
- Should the visitors' book on the lectern be readable (a right-click line, like the castle's doors)? It would need a line
  in `Regions/L73System.cs`, which this round did not touch.
- The far fields stay as dark as the lore asks (no light outside): is that the look you want in screenshots, or should
  the moonlight be a shade brighter away from the castle?

## Round 4 (2026-11-02): the asset-quality pass

From the round-3 final sheet (`%TEMP%/backrooms-shots/final-r3/73/sheet.jpg`), the lead's round-4 notes, round 3's
"Still weak", the brief and DECISIONS.md, and the released levels' best props (188's street kit, Fun's set pieces, the
detail kit, the Hub). Tier A must, B should, C nice. Inventions are marked (inv.).

### List

**1. Assets to rebuild to the bar**
1. [A] [done] `l73-sconce`: a real wall candle-lamp (back plate, curled iron arm, drip pan, candle with wax drips, a flame
   that glows) instead of a box with a picture.
2. [A] [done: l73-chandelier, l73-candelabrum] A real **chandelier** (`l73-chandelier`: an iron ring of candles with drip cups and flames, a central boss,
   hung on a chain from a ceiling rose) and a floor **candelabrum** (`l73-candelabrum`) for the halls, replacing the
   hotel's crystal ones the castle borrowed.
3. [A] [done] `l73-fire`: logs crossed on firedogs as rotated round logs (bark, cut ends), layered flame planes with glow,
   embers bright only where they burn; the dining hearth's and the kitchen's as the same family.
4. [A] [done] `l73-tapestry`: cloth hung from an iron rod on brackets with finials, a hem and a fringe, a slight belly, not a
   flat painted board.
5. [A] [done] `l73-canopy`: four-posters with turned posts (bases, collars, finials), a carved tester, drapes in folds held
   by tie-backs.
6. [A] [done: l73-highchair at both ends] `l73-table` (set): pewter plates with rims, goblets with stems, a candlestick in the middle, knife and spoon;
   a carved **high chair** (`l73-highchair`) at the head of the table (Coran's place, inv.).
7. [A] [done] `l73-barrel` / `l73-bath`: staved barrels with a bulge, three iron hoops and a chime; the bath's water sunk
   inside the rim.
8. [A] [done: l73-hound-0..9, ten anchor blocks] `l73-bone` (the Great Hound): sculpted skull with jaw, teeth, sockets and brow, vertebrae with processes,
   ribs as rotated curved segments, limb bones with knuckled ends, as one multi-block piece.
9. [A] [done: 164 elements, was 65] Coran's model (`gen_73_coran.py`): more elements: chain links with depth, gauntlets with knuckles, fingers and
   spikes, the eye necklace, a tattered mantle (see 41 on the lantern and hood).
10. [A] [done] `l73-silverwall`: masonry with wear: weathering variants for the plinth course (moss, damp), streaks under
    the crenels, quoins at the corners in a paler dressed stone.
11. [B] [done: l73-bookcase-{a,b}] A **bookcase** of the castle's own (`l73-bookcase`): shelves with spines of varied height, colour and lean,
    a book lying flat, for the library and the solar (the hotel's shelves are a picture).
12. [B] [done] `l73-hookmeat` / `l73-carcass`: an iron rail with S-hooks and sculpted carcasses (ribs, hide, a limb); heaps
    of the dead as bones and rags, not blocks.
13. [B] [done] `l73-deadwood` / `l73-deadbranch`: silhouettes with forking rotated branches and twigs.
14. [B] [done] `l73-boulder`: faceted rocks of several boxes, a moss-dark foot.
15. [B] [done] `l73-potrack`: copper pots and pans with handles and lids on hooks.
16. [B] [done: straps, studs, ring pull] `l73-door`: iron strap hinges, studs and a ring pull as real boxes.
17. [C] `l73-chest`, `l73-washstand`, `l73-well`: edge banding, straps, a windlass on the well.

**2. Multi-block set pieces**
18. [A] [done] **The attic** (the lead: "fix that first"): a pitched slate roof with gables, a ridge with cresting, dormers
    with leaded windows, the balcony with a stone balustrade and its door, the chimney stacks rising through it.
19. [A] [done] **The gatehouse**: two drum towers (round in plan), a pointed arch with a **portcullis** hanging into it,
    machicolations over the gate, arrow slits, banners on the towers.
20. [A] [done] **Machicolations and crenels**: corbelled parapets on the curtain wall's towers and the keep, merlons with
    caps, arrow slits in the towers.
21. [A] [done] **The keep's front**: quoins, string courses, buttresses, the pointed window heads with the boards behind and
    a warm glow between the boards (see 28).
22. [B] [done] **A dry ditch and stone bridge** before the gate (inv.: the page has a gatehouse, no ditch).
23. [B] [partly: conical roofs; the towers stay square] The corner towers round (drum) with conical slate roofs.
24. [B] [done] The **dining hall** as one set: the high chair, the place settings, candelabra on the table, the hearth.
25. [B] [done] The **chandeliers** hung on chains through the beams in the main hall and the dining hall.
26. [C] The well with a windlass and bucket; the cart with spoked wheels.

**3. Level design**
27. [A] [done: scene 0.44 / 0.40] **The island at night**: keep the lore's dark but let things read: a faint moon rim (scene brightness a shade
    up on the fields, lighter top texels on ridges and rocks), the castle as the one warm thing.
28. [A] [done] **Windows glow**: light leaks between the boards of the keep's windows (emissive cracks, a low warm light on
    the outside face) so the path and courtyard read; no lamp outside (the lore).
29. [B] [done] **The shore**: black rocks at the waterline and wreckage (ribs of a boat, planks, a crate) on the beaches.
30. [B] [done] **Heaps of the dead** on the fields sculpted (bones, rags, a pack), near the castle's hill where Coran leaves
    them.
31. [B] The arrival view: the castle's outline and glow read from 60-120 blocks.
32. [C] A guard room in a gatehouse tower (racks, a bench, a brazier) (inv.).

**4. Lore**
33. [A] [done: the banners were already on rods; two moved beside the drums] Coran's device on the gatehouse and keep: large banners (silver heart, ram's horns, black field) hung from
    poles with finials.
34. [A] [done] The attic reads "off-limits" from the roof: the chained door, the balcony.
35. [B] [done] The paintings in real gilt frames with depth.
36. [B] [done] The table of plenty: "silverware at the grand mahogany table": silver plates and goblets.
37. [C] The visitors' book readable.

**5. Alignment with the other levels**
38. [A] [done] Look for shared candles, lanterns, braziers, banners (Level 47's `candles`, `lantern`, `brazier`, `banner`) and
    the Hub's / 188's lights; reuse or retint before building new.
39. [B] Barrels and crates: share with 23/47 where theirs are better; else 73's to the bar.
40. [B] [done] Showcase spots and F7 entries for the rebuilt set pieces (attic, gatehouse, chandelier, the Hound up close,
    the shore).
41. [B] [done] Coran stays to the lore (no arms but chains, blind): no lantern and no hood (the lead's note; a lantern
    outside breaks the light rule and he has no eyes); a mantle instead.
42. [C] [done; and the hotel furniture replaced by the castle's own, beds and clock excepted] "Shared assets below the bar" written for the lead (the hotel chandelier, bookshelves, beds).

### What was built (round 4)

- *The castle from outside* (`tools/gen_73_r4_castle.py`, `src/Worldgen/WorldGenerator.L73.Outside.cs`): the ashlar redone
  larger and darker (two courses a block, each stone its own shade, tooled, `r4castle.ashlar`), moss and damp on the foot
  courses (`l73-silverfoot`), rain streaks under every parapet (`l73-silverstreak`), pale dressed quoins at every corner
  (`l73-quoin`); machicolations under every parapet (`l73-corbel-{straight,corner}-*`: three stepped corbels carrying a
  projecting floor, its underside dark between them) with the merlons standing out on them (`l73-merlon-{plain,slit,corner}-*`,
  sloped caps, some with arrow slits); arrow slits in the curtain and the towers (`l73-slit-*`); conical slate roofs with an
  iron finial and vane on the corner towers, the drums and the keep's turrets (`l73-cone-*`, the turrets now pepper-pots
  on corbels).
- *The gatehouse*: two half-round **drum towers** standing two out before the gate (`l73-drum-{cell}-{course}`, cut cell
  by cell from a circle: foot, body, a string course, a corbelled parapet, merlons round the curve), the gate under a
  **pointed arch** (`l73-arch-*`) with the **portcullis** raised in its slot, its spiked foot hanging into the arch; the
  machicolations over the gate; the two outer banners moved to the curtain beside the drums. Before it a **dry ditch**
  (two deep, one at its ends) and the **stone bridge** that carries the path over it (inv.).
- *The attic* (the lead: "fix that first"): a 45-degree **slate roof** (`l73-roof-*`: the slates in laps, an eave with
  its fascia and lead gutter, the ridge with a roll and **iron cresting**, rafters underneath), **stone gables** coped and
  crowned with a **cross** at each end, four **dormers** with leaded windows under little gabled roofs (`l73-dormer-*`);
  the chimney stacks capped with a corbelled cornice and **clay pots** (`l73-chimneycap`).
- *The keep's windows* (`l73-window-{low,high}-*`): a stone reveal, a sill with its drip, a **pointed head** with a hood
  mould and keystone, the boards set back in it with the rooms' **warm light showing between them** (light 5 on the path
  and the courtyard; nothing outside the walls); iron **strap hinges**, studs and a ring pull on the keep's door leaves.
- *The castle's own furniture* (`gen_73_r4_castle.py`) in place of the Level 5 hotel's: carved side chairs with pointed
  backs at the table (24), settees, wing chairs, low tables, sideboards with silver on them, armoires, bedside cabinets,
  chests of drawers with swing mirrors, writing desks with pigeonholes; a gabled stone hood on brackets over the keep's
  door, coped weatherings on the buttresses, candle-sconces in the gate passage.
- *Inside* (`tools/gen_73_r4_props.py`, rebuilt shapes in `gen_73_interior.py` / `gen_73_castle.py`): the castle's own
  **chandelier** (an iron ring of eight candles on a chain from a ceiling rose) and **candelabrum** (five-armed, on a
  tripod) in place of the hotel's crystal ones; the **sconce** a real candle-sconce; **fires** of round logs crossed on
  firedogs, the cauldron on its crane; **tapestries** hung from iron rods on brackets with finials, hemmed and fringed;
  **four-posters** with turned posts, a carved tester and tied-back drapes; the **table of plenty** set with pewter plates,
  goblets, knife and spoon and a napkin, a carved **high chair** at each end (`l73-highchair-*`); **barrels** staved with
  hoops; **bookcases** of the castle's own with books of every height and lean (`l73-bookcase-{a,b}-*`); hooks and
  carcasses, the heaps of the dead, the pot rack with copper pots and lids.
- *Coran* (`tools/gen_73_coran.py`, 164 elements, was 65): ring links of four bars each, gauntlets with fingers, thumb,
  knuckle and back spikes, layered plates (pauldrons, lames, abdomen, thighs, shins, knees, sabatons), five-segment
  curled horns, the eye necklace bigger, a tattered black mantle; no lantern and no hood (see the list, 41).
- *The Great Hound* (`tools/gen_73_r4_hound.py`): sculpted, carried by ten anchor blocks along its axis (`l73-hound-0..9`):
  the skull (cranium, crest, brows, dark sockets, cheekbones, snout, nose, the jaw dropped open, fangs and teeth), neck
  vertebrae, the arched spine (centra, leaning spines, processes), nine pairs of ribs curving to the ground (two broken,
  the pieces lying below), shoulder blades, the pelvis, the legs flat out with knobbed joints and clawed toes, the tail.
- *The island*: dead trees with crooked forking limbs and twigs on an eight-sided trunk with a root flare; faceted
  boulders; black rocks and **wreckage** on the beaches (a boat's ribs sunk in the sand, planks and rope; `l73-wreck-*`);
  **heaps of the dead** on the hill's flanks where Coran leaves them; the moonlit scene a shade brighter (0.44, was 0.36).
- *Showcase* spots `gate-arch`, `corner-tower`, `chandelier`, `attic-roof` (F7: under the gate, the hall and the attic).

### Inventions (round 4)

The dry ditch and its stone bridge (the page has "a singular open gatehouse", no ditch); the drum towers, portcullis,
machicolations and conical roofs (the page says only "gothic", "high and thin stone walls"); the attic's pitched roof,
gables, crosses and dormers (the page: "an attic opening onto a balcony"); the light between the boards (the page: the
windows are "completely boarded"; the light here is the rooms' own, seen through the cracks, and falls only inside the
walls); the high chairs at the table's ends; the wreckage on the beaches (the page: an unexplored ocean); the heaps of
the dead on the hill's flanks; Coran's mantle.

### Shared assets below the bar

- The Level 5 hotel pieces the castle still borrows: the beds under the canopies (they must stay the mod's sleepable
  beds for the night's rest; a castle frame round them would need the shared bed shape to change), the grandfather
  clock and the toilet. Round 4 replaced the rest with the castle's own (`l73-chair`, `-settee`, `-wingchair`,
  `-lowtable`, `-sideboard`, `-armoire`, `-bedside`, `-drawers`, `-desk`, `-bookcase`, `-highchair`); the hotel's
  versions (`hotelchair`, `longsofa`, `wingchair`, `coffeetable`, `consoletable`, `dresser`, `writingdesk`, `nightstand`,
  `wardrobe`, `hotelbookshelf`) are one-box legs and flat fronts next to them, if Level 5 wants a pass.
- The field bones (`Props.BonePile`, `Ribcage`, `JawSkeleton`) and `Props.WreckCrate`: low-detail boxes; a bone pile of
  several rotated bones and a skull would serve every level that uses them.
- The hotel's crystal `chandelier` (top-level `shapes/block/chandelier.json`): no longer used here; still a flat ring.

### Balance notes for the lead

- The **dry ditch** before the gate (two deep, one at its two ends) is an obstacle on the run: whoever misses the bridge
  (4 wide, on the path) drops in and must walk to an end to climb out. Hounds and the rest path round it or follow in.
  If that is too cruel for the run, make it one deep (`WorldLayout.L73Ditch`).
- The **windows** give light 5 inside the walls (the courtyard and the path to the keep's door); nothing outside the
  curtain wall changes; the light rule (a light in hand outside the walls) is untouched.
- The **heaps of the dead** (about one tile in 240 on the hill's flanks, 44-88 out from the castle's middle) and the
  shore's **rocks and wreckage** are fixed blocks that give nothing; they are sealed tiles (no arrivals on them).
- The castle's new blocks are all `l73Fixed` (never break, drop nothing).
