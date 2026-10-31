> **Dropped 2026-10-30:** on neither main lore wiki as built; the user dropped it. Its code, assets and generator were removed (id 25 reused); this plan is kept for the record.

# Level 55 "Land of Ice": prototype plan

Internal id 25, `WorldLayout.Level55`, infix `L55`, blocks `l55-`, region per BACKLOG (WSW, `R * 1.1` out, 22.5 deg south
of west). Disconnected, cheats menu / `/backrooms goto 55` only. No entities, thresholds, loot, notes, handbook.
Reserved: `WallPattern` 241, `FloorKind` 250, `CeilingKind` 104-111, `Props` 740-779, title keys 2501-2599,
salts 0x2500-0x25BF, port 42486. Research only; nothing touched.

## 1. What the lore says

**Source conflict: neither wiki has a "Land of Ice" at Level 55.**
- Wikidot Level 55 is **"Pit Stop"**, survival difficulty 0, a safe abandoned restaurant (Safe Room entry, food from the
  Frontrooms): https://backrooms-wiki.wikidot.com/level-55 . `backrooms.wikidot.com/level-55` does not exist.
- Fandom Level 55 is **"Hills of Synthetic Verdure"**, Class 2E, 0 entities: concrete hills under fake grass, blue
  cloudless sky, identical two-storey houses, silent (0 dB), roads, water towers:
  https://backrooms.fandom.com/wiki/Level_55 (API wikitext). Fandom search for "Land of Ice" returns nothing.
- So "Land of Ice" is the user's own name (or an older/other-wiki page I could not reach; the Wayback lookup was rate
  limited). The plan therefore **invents Level 55 as an ice level, borrowing from the nearest canon ice levels**:
  - Fandom Level 202 "Snowy Glaciers": https://backrooms.fandom.com/wiki/Level_202 . Glaciers and icebergs on a still sea,
    cloudless clear blue sky with no visible sun yet a day/night cycle without sunrise colours, air a constant -15 C,
    water 10 C and deadly, snow about 30 cm thick and too compact to sink into, bare slippery ice near edges, crevasses
    (some hidden under thin snow and ice), ice spikes, caves inside glaciers with no snow, giant skeletons in the ice,
    no entities, no outposts possible.
  - Fandom Level 44 "Under the Ice": https://backrooms.fandom.com/wiki/Level_44 . Blue-green ice tunnels, dim blue glow,
    very slippery, snow blockages, ice rooms shaped like furniture rooms, colours sometimes shift like an aurora.
  - Wikidot's 202 is "Halls of Chalk" and 44 "Corroding Retail Outlet", so these two are Fandom-only.
- Prototype scope: a bright, deadly-cold, silent-ish glacier plain with crevasses, a frozen sea, one abandoned hut and
  one ice cave. The hut and the aurora are my invention and are flagged as such.

## 2. The level in this mod

**Region.** Fixed 16-cell (512 block) radius round region, like Level 73 (a world-size radius would be miles of
ice). Open sky: add `Level55` to `IsOpenSky`; vanilla sun floods the ground. Rim: a rime cliff to rel +18, built
per cell as 73's basalt rim is.

**Band.** Drop 0 (`FloorFor` = ice-sheet datum, rel 0). `L55BandDepth = 14` so the 40-block band runs rel -14 to +25
(crevasses reach -14, glacier crests +20, hut roof about +24). One constant beside `L73BandDepth`.

**Heightfield `L55Ground(x,z)`, a pure function of block position (like `L73Ground`), with a `Zone` per column:**
1. Plateau base 0. Hut centre `C` jittered within 16 blocks of the region centre by `Hashing`.
2. Glacier swells: low-frequency `Fbm(x/90, z/90)` mapped to 0..12 (zone 2 above 6), plus the Level 94 jittered
   parabolic hill lattice (pitch 48, radius 14-28, height 2-7, own salt 0x2502) for snow dunes (zone 1).
3. Ridges: where `Noise2(x/40, z/40)` is within 0.015 of 0.5, +4 (ice spikes without a model).
4. Crevasses: along the zero lines of `Noise2(x/55, z/55)` (width 2-4 blocks, depth 6-14, wider at depth). Roughly
   half are covered by a 1-block `game:snowblock` bridge where `Noise2(x/7, z/7) > 0.6` (hidden crevasse). Zone 3.
   None within 40 blocks of the hut or of the arrival spots.
5. Frozen sea: where the basin noise `Fbm` < -0.25 (about 20% of the area), height -2, surface `game:lakeice` over
   2 blocks of `game:glacierice`, pressure ridges (+2 ice walls) along the basin lines. Zone 4. Solid below, no real
   water (no flooding risk; the sea is decorative).
6. Ice cave: one per ~150 block square (hash), entered by a 5-wide sloping tunnel into a glacier swell (carved:
   floor `l55-blueice`, 4-6 high, 20-30 long, curved by a noise offset, ending in a small round chamber). Zone 6.
   Walls `l55-blueice`, no snow.

**Surface.** Zone 0/1: `game:snowblock` top, `l55-windcrust` where `Noise2(x/9, z/9) > 0.7`, 3 deep, then
`game:packedglacierice`, then `game:glacierice` to the floor of the band. Zone 2: `l55-windcrust` capped by snow, bare
`l55-blueice` on steep faces (slope over 2 blocks per block) and crevasse walls. Occasional `game:snowlayer-1..3`
on the dunes for relief. No props at first.

**Structures (invented, flagged).** One abandoned **research hut** (zone 5), about 24 x 12 and one storey of 4, near `C`
on a levelled pad: `l55-frostplank` walls and floor, a stove (`game:ember` in a stone box as in 73's hearth), 2 bunks
(Level 5 beds), a table and chairs, 4 `l55-lamp`. A snow drift against the north wall, door facing south. The **ice
cave** above is the second place. Nothing else is built.

**Light.** Polar day: a fixed bright sky. The mod pins scene brightness per level (Level 9, 73), so pin **0.90 at every
hour** and hide sun and stars in a pale-blue fog sphere (the 73/10 trick) so there is no sun gradient or sunrise.
Aurora (Level 44) later as a slow fog-tint drift in blue/green; skip for the prototype. Ice cave: scene 0.55, cold
blue `#7fb4d8` air; `l55-blueice` in the cave carries light 4 so the cave reads under open-sky flooding. Hut: scene 0.8,
warm lamps (light 9) and the stove (12).

**Atmosphere.** Fog pale blue-white `#d8e6f2`, density 0.0025 (visibility about 400). **Whiteout:** one slot in four
of a 2-game-hour clock (hash of the world hour, as 73's dark spell): density 0.02, fog `#f2f6fa`, scene 0.8 for about
0.3 h; cut by 90% inside the hut or cave. Temperature: **-15 C outside** (Fandom 202), 4 C in the cave, 10 C in the hut,
18 C within 3 blocks of the stove. `HeatSystem` does the freezing; `L55Temperature` just returns the numbers. Test
that an unclothed player loses health in about 2 minutes outside. Stability 0.9 outside, 1 in the hut.
**Sound bed:** vanilla wind loop (as Levels 9/10) at low gain, louder in whiteouts. An ice creak or boom every
60-140 s (Level 974's creaks pitched down), a faint crystalline tinkle near crevasses; hut: stove crackle (the
`fireplace` positional sound). The 0 dB silence of Fandom's Level 55 does not apply here. **Slipperiness:** check the
vanilla `lakeice`/`glacierice` JSON for a friction field; if neither slips, add a speed multiplier on `l55-blueice` only
(a block field, no code).

**Arrival.** Zone 0/1 dry plain, height 0-3, 60-220 blocks from the hut, at least 40 blocks from any crevasse
(`IsL55ArrivalSpot`).

## 3. Minimal asset list

**Vanilla reuse** (present under `G:\Games\Vintagestory\assets\survival\blocktypes`): `snowblock`, `snowlayer-1..7`
(variant group `height`), `glacierice`, `packedglacierice`, `lakeice`; plus `game:rock-*` (filler, stove box) and
`game:gravel-*` (cave dust). Mod: `l188-wall-corridor` for hut interior trim, the Level 5 bed, `l188-chair` and
`l188-roundtable`; the `l73-sconce` shape is reused for `l55-lamp` (new texture only).

**New (5 codes, textures via `tools/gen_55.py`, matlib/texlib):**
- `l55-windcrust`: wind-packed snow, fine ripples, faint blue shadow in the grooves (the common walkable crust).
- `l55-blueice`: deep glacier blue-green with white bubble streaks and hairline cracks (cave and crevasse walls).
- `l55-rimecliff`: grey-white rime-coated rock-ice, for the region rim so it differs from the walkable ice.
- `l55-frostplank`: weathered grey planks furred with white frost, for the hut walls and floor.
- `l55-lamp`: black iron lantern with a warm yellow glow (light 9); reuses the `l73-sconce` shape.

## 4. Lang strings (`en.json`)

```
"level-25": "Level 55: Land of Ice",
"levelhint-25": "Do not stop walking. The cold does not.",
"levelname-25": "Level 55",
"level-2501": "The Research Hut",
"levelhint-2501": "Someone left in a hurry. The stove is still warm.",
"levelname-2501": "Level 55, the Research Hut",
"level-2502": "The Ice Cave",
"levelhint-2502": "Blue light, no wind. Nothing here is alive.",
"levelname-2502": "Level 55, the Ice Cave"
```
Keys 2503-2599 stay free (e.g. 2503 "The Frozen Sea").

## 5. Open questions (with recommendations)

1. **Which Level 55?** Neither wiki matches "Land of Ice". Recommend: build it as the user's own level with 202/44 as
   reference; ask whether the name comes from another source. It changes nothing in the plan.
2. **Scene brightness vs whiteout.** A pinned 0.90 can wash the snow out. Recommend: start at 0.90, tune in a client;
   the whiteout drops it to 0.8.
3. **Frozen sea solid or real water.** Recommend solid (ice over rock): no flooding, no seams at the edge.
4. **Hidden crevasses.** Deaths from falls feel unfair in a prototype. Recommend: keep the snow bridge, cap depth at 14
   (vanilla fall damage, not an instakill) and tint bridge `snowblock` slightly by noise so careful players can spot it.
5. **Aurora.** Recommend: skip, add later as fog tint drift.
6. **Slipperiness.** Recommend: read vanilla ice friction first; add the multiplier only if it is missing.
7. **Hut contents.** Recommend: stove, 2 bunks, table; no notes. The giant skeleton in the ice (Fandom 202) is a
   possible later prop (`Props` 740-779 reserved).
8. **Cost.** Nested noise plus lattice hills at 512 radius is about the same as 73 (0.6 ms a cell). Recommend a
   `55stats` hook like `73stats` to confirm.

## Status (prototype built, 2026-10-17)

**Built.**
- *Region and geometry.* Round, a fixed 16 cells (512 blocks) radius at the README's centre (as Level 73), open sky
  (`IsOpenSky(Level55)` true). Drop 0: rel 0 is the ice sheet's datum. `L55BandDepth = 14`, so the band runs rel -14 to
  +25 (the generator still builds from the usual band bottom; below rel -14 is the ground as vanilla laid it). The rim
  cells are a cliff of `l55-rimecliff` to rel 18 under a snow cap, built per cell as 73's is.
- *Ice* (`WorldLayout.L55Column`, a pure function of the block position, from the hut's middle): swells (`Fbm` /90, to 12),
  a jittered dune lattice (pitch 48, radius 14-28, height 2-7, none within 60 of the hut), roughness, thin ice ridges
  (+4) on the high swells; levelled round the hut (to rel 1, a drift against its north wall) and round the cave. Frozen
  sea where a basin noise falls below -0.26 (never within ~140 of the hut or ~100 of the cave): `game:lakeice` at rel -2
  (-1 in a shallow margin, so the shore is one-block steps) over two of `game:glacierice` over granite; pressure ridges
  of glacier ice to rel 0. Crevasses along the zero lines of a noise inside crevasse fields (another noise > 0.1, tapered
  at the field's edge, well inland, none within 45 of the hut or 60 of the cave): 2-4 wide, 3-12 deep (floor at rel -12
  at most), blue-ice walls, a soft snow floor; about a third bridged by one block of `game:snowblock` at lip level.
  Surface: `game:snowblock` (with `game:snowlayer-1..3` softening the steps) or `l55-windcrust` patches, two of crust
  under it, then `game:packedglacierice`; `l55-blueice` on steep faces (a step of 2+), under crevasse lips and in the
  cave's dome.
- *Ice cave* (`L55CaveAt`): one, 120-160 blocks from the hut, in a dome of blue ice (radius 46, 15 high over a levelled
  floor at rel 2): a round chamber (radius 9, ceiling 5-8 above its floor) and a 5-wide, 5-high tunnel winding about 40
  blocks out toward the hut, ending in an open cut through the dome's foot. Walls and ceiling `l55-glowice` (light 4,
  `lightAbsorption` 0 so its light spreads), floor blue ice. Zone 6, title key 2502.
- *Research hut* (`L55HutAt`, hut-local): 20 x 12, one storey (roof slab at +5, snow on it), `l55-frostplank` walls,
  `game:planks-aged-ud` floor, a 2-wide doorway (no door) in the south wall, `game:glass-plain` windows (east, west,
  south). A stove against the north wall: `game:ember` in a `game:cobblestone-granite` box with a hood and a chimney
  through the roof. Two bunks (Level 5 beds) on the west wall, a round table with four hotel chairs, four `l55-lamp`
  (light 9). Title key 2501.
- *Sky and air* (client, `AtmosphereSystem.L55.cs`): fog `#d8e6f2` 0.0025, scene 0.90 held at every hour (no day/night),
  the sky (sun, moon, stars) hidden in a fog sphere of the fog's colour (73's trick, its own flag). Whiteouts
  (`L55Whiteout`): one 2-game-hour slot in four, 0.3 h, eased: fog to 0.02 and `#f2f6fa`, scene 0.80. Hut: warm air
  0.003, scene 0.80. Cave: blue `#7fb4d8` air 0.006, scene 0.55.
- *Sound bed* (all reused): vanilla `wind` (0.30 outside, +0.40 in a whiteout, 0.10 in the cave, 0.06 in the hut); every
  60-140 s a far groan or crack (vanilla `heavyice` or Level 974's creaks, pitch 0.45-0.6); the `fireplace` loop at the
  stove. No new synth loop.
- *Rules:* temperature -15 C outside, 4 C in the roofed cave, 18 C in the hut, 24 C round the stove (vanilla body
  temperature does the freezing; the ember is also a vanilla heat source). Stability 0.9 outside, 1 in the hut.
  Arrivals (`IsL55ArrivalSpot`): snow or glacier tiles flagged safe (crevasse-field noise below -0.2, more than 40 from
  the hut, 50 from the cave), not steep, not on the dome, 70-210 blocks from the hut by the arrival cell.
- *Assets* (`tools/gen_55.py`, matlib/texlib): 6 codes, `l55-windcrust`, `l55-blueice`, `l55-glowice`, `l55-rimecliff`,
  `l55-frostplank`, `l55-lamp` (4 sides, Level 73's sconce model with its own textures); 10 textures; lang keys 25,
  2501, 2502 and the block names. Blue and glow ice have vanilla ice's `dragMultiplier` 0.02 (slippery, as vanilla's
  ice already is).
- *Harness:* `55stats` and `55map` in `tools/mapgen/L55Stats.cs`.

**Numbers.** `55stats` (seed 12345, full size): 819 cells, 0.7 ms a cell; snow 47.0%, glacier 14.0%, crevasse 1.3%, sea
22.2% (7300 ridge tiles), rim 15.4%, hut 240 tiles, cave 448 (370 roofed, 78 in the cut); 30 crevasses of 12+ tiles,
10809 tiles, 35% bridged, deepest floor rel -12; peak 20; arrivals 60/60 on snow or crust, all at least 40 blocks from
any crevasse (nearest 42), all on gentle ground, 50-266 blocks from the hut. `SPAWN=1000`: the same ice (it is laid out
from the hut), 60/60. `regions`: Level 55 60/60, wrong level 0, pockets 0 (full size and `SPAWN=1000`). `layouthash`:
every per-level line for 0-23 unchanged. Headless (port 42486): `blocksweep` 0 threw; dumps of the hut, the cave and a
crevasse show every block as planned; no missing Level 55 blocks, shapes or textures logged.

**Skipped / deviations.** Thresholds, entities, dens, loot, notes, handbook; the aurora; the crystalline tinkle near
crevasses; crevasses are vertical-walled, not wider at depth (columns only); one cave, not one per 150-block square; the
hut is 20 x 12 rather than 24 x 12, its floor is aged planks (the frost planks are the walls and roof), no interior trim.

**Known gaps / to check in a client.** Untested in a client: that the sky sphere really hides the sun at noon and the
pinned 0.90 does not wash the snow out (whiteout 0.80); that an unclothed player freezes outside in about two minutes and
warms in the hut; the lamp's orientation and glow on the 73 sconce model; how the cave reads at light 4 and scene 0.55.
Snow bridges are vanilla `snowblock`, which has vanilla's falling behaviour: a neighbour change (breaking a block beside
one) drops the bridge into the crevasse, block by block. The headless dump shows the hut's inside at full light although
it is roofed (as 73's keep did): check in a client whether sunlight really floods it. The map layer's grouped case
(floor to floor + 5) is not taught the ice's heights (to 20). Vanilla snow, ice, ember and glass bypass the salvage
Breakdown.
