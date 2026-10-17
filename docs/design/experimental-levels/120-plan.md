# Level 120 "Server Room": prototype plan

Internal id **26**, `WorldLayout.Level120`, tag `120`, blocks `l120-`, method infix `L120`, region far north-east
(`spawn + (+F, -F)`, see BACKLOG batch 2). Prototype only: disconnected, cheats menu / `/backrooms goto 120`, no
entities, thresholds, loot or handbook. Reserved: `WallPattern` 242, `FloorKind` 251, `CeilingKind` 112-119, `Props`
780-819, `Unders` 170-179, `Overheads` 160-169, `Pipes` 140-149, salts 0x2600-0x26BF, port 42487.

## 1. What the lore says

**Conflict:** the two wikis disagree about what Level 120 is. Wikidot has the server room, Fandom has a megastructure.
- Wikidot, https://backrooms-wiki.wikidot.com/level-120, "Broken Servos" (marked "being rewritten"): survival
  difficulty 2. Repeating rooms of broken servers: massive computer blocks ripped apart on a dirty white floor, dirty
  yellow wallpaper on rotting wood, office ceiling tiles with smashed or dead fluorescents. Rooms are usually pitch
  black; server rooms come in clusters of 15-23.
- Wikidot sub-zones: white-void rooms (clusters of 6-12, black doors, self-lit, draw Smilers) and Pitch-Black
  Hallways (thin, very long, easy to trip in). Both are loaded by booting an intact computer block; windows at the
  cluster ends (usually broken) lead back. Entities: Misglitches, Sub-Misglitches (and Smilers). No bases.
- Wikidot entrances: a smashed arcade screen in Level 25, a "Server Room" door in Level 4.3. Exits: doors back to 4.3,
  or noclip the server room walls to Level 70.
- Wikidot says nothing on rack aisles, cold aisles, cable trays, raised floor, temperature or sound. The brief's
  rack/aisle/raised-floor layout is our extrapolation; the lore's tone is wrecked, dark and dirty.
- Fandom, https://backrooms.fandom.com/wiki/Level_120 (via `api.php?action=parse`): "Chokepoint", class Habitable
  (Safe): a 153 x 137 km Brutalist megastructure floating in an endless sky, The Plaza, New Banbury. Not a server
  room; not used.

## 2. The level in this mod

Round noclip region, radius `max(40, spawnMacroX / 50)` cells (~320 full size), cell = 32 blocks, band 40 blocks.
All from world coordinates and `Hashing.Hash(seed, a, b, salt)`; no per-region state. Default room height 3 (rel 0..3).

**Skeleton: a rack hall grid** (two scales, like Level 52's halls and wings).
- **Service corridors** every K = 4 cells (128 blocks) on both axes, 4 wide, 3 high: bare dirty-yellow walls, dead
  cabinets and panels, `CarveEdgeHall` at the rim so it stays passable. They guarantee connectivity; arrivals here.
- **Halls** fill each 124 x 124 block between corridors. Kind per hall from `Hash(seed, hx, hz, 0x2610)` (laid out
  once through `PlanCache` as `L120PlanOf`, possibly transposed): **rack hall** 70%, **control room** 10% (desks,
  monitors), **cold vault** 8% (empty white tile, humming), **huge hall** 7% (the lore's "clusters": 5 high, ceiling
  rel 5, racks in long rows; only if every neighbour cell is Level 120 so a tall room never meets the rim),
  **dead store** 5% (toppled racks, crates, rubble).
- **Rack hall (the lattice):** rows of racks, each 1 wide x 1 deep x 2 high, in back-to-back pairs. Between pairs a
  3-wide **cold aisle** (raised-floor tiles, rack fronts); behind each pair a 1-wide **hot aisle** (rear cables).
  Pair pitch 6 blocks. Each row is cut every 8-14 racks by a 3-wide cross-aisle (hash-placed) so a hall is never a
  maze of dead ends; a 3-wide walk rings the hall; each hot aisle opens at both ends. 1 in 6 racks is ripped apart
  (`Detail`: toppled, gutted, missing) per the lore. Row ends get a blank cabinet.
- **Hot zones:** `Tile.Zone = Hot` on the hot aisles and dead store. `L120Temperature` reads it: hot aisle 38 C, cold
  aisle 24 C, corridor 28 C, cold vault 16 C. HeatSystem drains food at 38 C; hot aisles are 1 wide and short, so
  it is a cost, not a trap. Zones: 0 Corridor, 1 Cold, 2 Hot, 3 Control, 4 Vault, 5 Store, 6 Huge (Zone drives title,
  fog, temperature and sound).
- **Overheads / Pipes / Unders:** cable trays (`Overheads`, `l120-tray`) over each cold aisle and bridging each
  cross-aisle (in 3-high rooms trays replace ceiling tile in strips, never over doorways; huge halls get a second
  tray level); ducts (`Pipes`, Level 2 `pipes`) along corridors; `Unders` is a missing raised-floor tile 1 deep (1 in
  40 aisle tiles, never blocking, cable bundle visible).
- **Ceiling (`CeilingKind` 112+):** office tile, mostly dead; corridor fixtures every 6 blocks, 1 in 3 dead, 1 in 6
  flickering. **Wall 242:** `l120-wall`, dirty yellow wallpaper over rotting wood; `Variant` = clean / rot / bare concrete.
- **Light** (lore: pitch black; prototype: playable dark): nearly all ceiling lights dead. The light is **rack LEDs**:
  `l120-rack` lit variants (block light 4-6, green/blue/amber), 1 in 3 racks, so a lit rack makes a ~5 block pool in a
  dark aisle. "Blinking" is faked statically: four variants (off, bank A, bank B, both) hashed per rack, so a long
  aisle looks like a field of uneven lights. Control rooms: lit monitors (6, cyan). Every other corridor crossing
  keeps one working fluorescent so the player can orient.
- **Fog** (`AtmosphereSystem.Levels`): near-black cold blue-green `(0.016, 0.07, 0.09, 0.10)`; cold vault lighter
  `(0.009, 0.35, 0.40, 0.42)`; huge hall thinner (0.007) so racks recede; hot aisle a warm sodium haze.
- **Sound:** constant fan/AC drone bed (brown noise plus a ~100 Hz hum and a faint 3-4 kHz whine), new
  `serverhum()` in `tools/gen_level_sounds.py`, quieter in corridors, louder in huge halls; rare HDD clicks, relay
  clunks and a far fan spin-up every 0.5-4 min. Corridors also use `fluorescentlight` ambient. Output to
  `sounds/ambient/120/`; `L120Sounds` picks by zone.
- **Stability / danger:** calm, +0.001/s, danger 0 (no entities).
- **Skipped lore sub-zones:** white-void rooms and black hallways (need a computer-boot portal); follow-up if kept.

## 3. Assets

**Reuse (no new files):** `ceilingtile`, `fluorescentlight` (on/lit/off/flicker), `concrete`, `level1/concretefloor`,
`level1/crate`, `oildrum`, `metalshelf`, `level2/machinecabinet` (dead corridor cabinets), `level2/pipes` (ducts),
`level3/transformer` and `cables`, `level3/plasterceiling`, `end/end-terminal` and `end-desk` (control rooms),
`end/end-vent`, `level4/officechair`, `partition`, `wallpaper`; detail props `wallcables`, `pipecluster`, `keyrack`,
`standpipe`, `trashcan`, `wetfloorsign`, `chairstack`, `cardboardboxes`.

**New (5, all `l120-`, built by `tools/gen_120.py` with `texlib` + `modelkit`):**
1. `l120-rack`: server rack, 1 x 1 x 2 (lower/upper blocks), dark steel frame, 8-10 slotted 1U units on the front with
   vent slits; variants off / ledA / ledB / both x 4 facings (lit ones light 4-6) and a `gutted` one (door hanging, wires out).
2. `l120-floor`: raised-floor tile, 16 px light grey perforated square panel, seams and dirt (FloorKind 251; `Detail`:
   clean / dirty / cable-hole).
3. `l120-wall`: dirty yellow wallpaper on rotting wood (WallPattern 242), base / stained / bare-patch variants.
4. `l120-tray`: overhead cable tray, thin shape: yellow-grey mesh channel with a dark cable bundle; X, Z, cross, end pieces.
5. `l120-monitor`: dead or lit CRT on a desk, cyan scanline screen, facing variants (droppable: reuse `end-terminal`).

## 4. Lang strings (`en.json`)

- `"level-26": "Level 120: Server Room"`
- `"levelhint-26": "The machines are broken. Something still hums."`
- `"levelname-26": "Level 120"`
- `"level-2601": "The Cold Aisle"`, `"level-2602": "The Hot Aisle"`, `"level-2603": "The Control Room"`,
  `"level-2604": "The Cold Vault"`, `"level-2605": "The Great Hall"`, `"level-2606": "The Service Corridor"`

## 5. Open questions

1. **Which lore?** Wikidot "Broken Servos" (server room) vs Fandom "Chokepoint". Recommendation: Wikidot; do not mix.
2. **Aisle structure is invented** (lore has none). Recommendation: keep it; it is the point of the prototype, with
   wreckage (toppled racks, floor holes) to keep the lore's tone.
3. **Blinking LEDs:** true animation needs a ticking block entity. Recommendation: static LED variants now; try
   alternating variants or animated textures only if the look lands.
4. **White voids / black hallways:** Recommendation: skip in the prototype, revisit with thresholds.
5. **Too dark to play?** Recommendation: keep it dark but with LED pools and a lit corridor every other crossing;
   add ambient light 2 in cold vaults; reassess in a client.
6. **3-high rooms vs trays:** Recommendation: trays only over cold aisles (never doorways); huge halls take a second level.
7. **Rack as two blocks or one?** Recommendation: two (lower/upper) so lit LEDs sit at eye height and the model stays simple.
