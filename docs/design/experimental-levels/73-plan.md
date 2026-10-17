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
