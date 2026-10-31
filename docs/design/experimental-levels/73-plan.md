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
