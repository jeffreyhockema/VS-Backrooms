# Level 120 "Broken Servos": plan (prototype, then the detail pass)

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

## Status (2026-10-17, prototype built)

Built as planned, with these choices and deviations:
- **Lattice period 96, not 128**: corridors 4 wide at x/z mod 96 in 1-4, halls 90 x 90 (mod 96 in 6-95), two 3-wide
  doors onto each corridor, a 3-wide walk round the inside of every hall. Plans in `PlanCache` (`L120PlanOf`), flipped by hash.
- **Hall kinds** (`Hash(seed, hx, hz, 0x2610)`): rack hall 70%, control room 10%, cold vault 8%, great hall 7% (air 6,
  ceiling rel 7, longer rows, trays at rel 6 over the cold aisles and at rel 3 on rods over the hot aisles; only where
  the hall and every cell round it are Level 120), dead store 5%. `120stats 8`: 72 / 10 / 7 / 6 / 5%.
- **Rack rows**: pitch 6 across (cold aisle 3, rack row, hot aisle 1, rack row), cross-aisles every 8-14 racks (16-24 in
  a great hall). Racks are props (`WorldLayout.L120Rack` = 780, `L120Terminal` 781, `L120Chair` 782, declared in the
  level's own file, no Tiles.cs edit); LED state in `Detail`, floor panel in `Depth`, air in `Height`, trays in
  `Overhead` (160-163), ducts in `Pipe` (140-142), the dim lamp `(CeilingKind)113`. 1 in 6 racks wrecked (gutted,
  machine parts, scrap metal); 22% of standing racks lit (about 20% overall, ~280 light sources a rack hall).
- **Light**: lit racks' upper block gives light 4-6 (green, amber, cyan); fittings are mostly off/flickering/glow-only
  with the odd dim (Manila-orange) or working tube; every other corridor crossing keeps a working tube. Vaults: lights
  on a 6-grid, 8% working. Control rooms: lit terminals (light 6, cyan, 28% of desks, half the wall of screens).
- **Temperature** (`L120Temperature`, by zone): hot aisle 38 C, dead store 33, corridor 27, control 23, cold aisle 22,
  vault 15. **Fog**: base `(0.014, 0.035, 0.075, 0.08)`; hot aisle warm haze, vault pale, great hall thinner.
  **Titles** 2601-2605 (the corridors keep the level's own title; 2606 not used). **Sound**: one loop,
  `sounds/ambient/120/serverhum.ogg` (`tools/gen_120.py`), volume by zone; no one-shot clicks (skipped).
- **Floor holes** are a painted panel (`l120-floor-hole`), not a real hole. No white voids, black hallways,
  thresholds, entities, loot, notes or handbook.
- **Blocks (5)**: `l120-wall` (base/stained/rot), `l120-floor` (clean/dirty/vent/hole), `l120-rack` (lower/upper x
  off/leda/ledb/both/gutted x 4 sides), `l120-tray` (we/ns/rodwe/rodns), `l120-terminal` (dead/lit x 4 sides).
  Reused: officeceiling, fluorescentlight (on/lit/off/flicker/dim), Level 2 pipes, machinecabinet, officechair,
  crate, oildrum, trashcan, cardboardboxes, scrapmetal, machineparts.

Verified: mod and mapgen build with 0 errors; `regions` 60/60 for Level 120 (none wrong or trapped) full size and
`SPAWN=1000`; `layouthash` lines for 0-23 unchanged; `120stats` (7x7 and 17x17 halls round the centre, the east rim,
`SPAWN=1000`): every hall and every walkable tile reached from the corridors, 0 sealed, 60/60 arrivals in a corridor or
cold aisle. Headless boot (port 42487): blocksweep 0 threw, no Level 120 missing blocks/shapes/textures; dumps of a
corridor crossing, a control room and a great hall show the blocks and light as intended.

To check in a client: whether the dark is playable (LED pools of light 4-6 are small); the rack model and its LED
glow; tray rods meeting the ceiling; terminal and office-chair facings (screen to the chair; the sitter looking at
the wall of screens); the machine cabinets' facing in corridors; fog colour and the hum's loudness by zone; the hot
aisle's hunger cost; the stained-wallpaper texture (its streaks can read as a ring).


## Detail pass (2026-10-30)

The prototype's bright rack-hall lattice is brought back to the lore (Wikidot "Broken Servos" only; Fandom's
"Chokepoint" is not used). Title now "Level 120: Broken Servos". The sections above describe the prototype; where
they differ, this section wins.

### Built
- **Clusters of 15-23 server rooms** (`L120LayCluster`): every 90-square hall between the passages is cut by a
  split of its square into 15-23 rooms (no room narrower than 9; 19 on average), joined by one- or two-wide doorways
  (a spanning tree of the rooms' shared walls, then about a third of the other pairs as loops), with one or two
  three-wide doors onto each passage. Room kinds: server rooms 50% (banks of racks back to back, two-wide aisles,
  45% of banks wrecked: racks gutted, toppled, torn open, pulled out as machine parts or scrap, cables spilled over
  the aisles), rack aisle rooms 12% of the big ones (the prototype's cold and hot aisles, in miniature), terminal
  rooms 14% (rows of dead or smashed CRTs and chairs), wrecked stores 12%, cable rooms 12%. A flood from the doors
  walls off or fills anything a rack bank shuts in, so every open tile is reachable (`120stats`: 0 unreached).
- **Look**: the lore's dirty white floor (off-white vinyl tiles, two to a block, scuffed and stained; raised-floor
  vents and lifted panels among the racks), dirty yellow paper on rotting boards (soot-black paper in the hallways),
  office ceiling tiles (plain, water-stained, fallen through) with every fitting dead or smashed (a new smashed-fitting
  block). New props: a rack toppled on its back, a rack torn open (two high, units hanging out, door half off), spilled
  cables and drive caddies (walked over), a smashed CRT, the whole terminal (green BOOT prompt, light 5).
- **Pitch dark**: lit racks 4% of standing racks (was 22%) and light 3-4 (was 4-6); room and passage fittings are
  off (45%), smashed (45%), failing (3%) or dim (2%), never working; one passage crossing in four keeps a working
  tube (was one in two). Base fog near black, scene dimmed to 0.8.
- **The boot mechanic** (built as the brief proposes, a pocket generated from the terminal's hash, not wings behind
  doors): about 1 hall in 17 is a **White Void** and 1 in 17 a **Pitch-Black Hallway**, only where the hall and the
  cells round it are all Level 120; pocket halls have no doors, so they are reached only by booting. A cluster has a
  whole terminal 85% of the time (in a terminal room if it has one). Right-click: boot sound and a chat line, two
  seconds later you are carried (ThresholdSystem's fade and load, `L120Carry`; nothing written to the threshold
  network) to the nearest pocket hall of the kind the terminal's hash picks (void 60%, hallway 40%; the other kind
  if none within 8 halls). Where you stood is remembered on the player (`backrooms:l120Back`); walking into any
  broken window of a pocket brings you back there (else to the nearest whole terminal, else anywhere in the level).
  - White Void: 6-12 rooms 11 square and 4 high, grown on a 7x7 grid, pure white with a glowing ceiling panel
    (light 14) every third block, black doors standing open between neighbours (a tree and some loops), a broken
    window in the middle of every outside wall ("travel in one direction"), black solid round it. White fog, a clean
    high tone. Stability 0.97.
  - Pitch-Black Hallway: 2 wide, 86-long lanes folded back and forth (6-14 lanes, 500-1200 blocks), unlit, 14 C,
    cables underfoot, a broken window closing each end; you arrive halfway along the middle lane. Black fog, near
    silence. Stability 0.94.
- **Tripping** (L120System): running in a hallway, a 17% chance per 8 blocks (walking 2%), and running over spilled
  cables in the dark anywhere in the level 25% a crossing: 1 damage, slowed for 1.4 s, a stumble sound, the noise of
  a fall for the director.
- **The Misglitch** (the key new creature): `l120-misglitch`, model by `tools/gen_120_misglitch.py` (a gaunt black
  humanoid about 2 blocks tall, a five-segment tentacle right arm ending in a point, twelve glowing pixel cubes
  floating round it and four on its surface; two looks: red wound marks, or all black), animations idle, lurk,
  glitch, walk, run, attack, hurt, die; sounds by `tools/gen_120_sounds.py` (three static bursts, a corrupted shriek,
  a slice, hurt, death, a glitch blip). `L120System` puts one down wherever a player dies in Level 120 (all black for
  an internal death: hunger, poison, suffocation, drowning), at most six within 24 blocks (three from round 3, the balance review). `AiTaskMisglitch`
  (`src/Regions/L120Misglitch.cs`): stands slumped by the place, crackling static every 4-10 s (the warning in the
  dark); wakes for anyone within 6 blocks (3.5 sneaking), running within 18, or carrying light 7+ in its line of
  sight within 16; chases at 0.043 (x Danger.Speed: just under a sprint), and every 4.5 s may skip 2.2 blocks straight
  at its prey; slices with a 2.4-block reach (5 x Danger.Damage, tier 2, slashing); leashed 32 blocks to its place,
  gives up after 25 s without blood or by a fire; lasts 24 in-game hours (watched attribute), then comes apart.
  Health 20 (+42% at the level's danger 0.3). No drops (the victim's body holds the loot). Never the director's.
- **Smilers in the voids**: 1-3 per void (by its hash) while anyone is in it, put down by L120System out of sight,
  10-40 blocks away, as Ambient wanderers (the menace task never runs for them: they stand lost in the light; struck,
  they withdraw as every Smiler). The director puts nothing down in Level 120 (band stays Safe, roster empty);
  `Danger.OfLevel` is 0.3 (Survival Difficulty 2).
- **Sound bed**: one loop by where you are (server hum by zone, the void tone, the hallway's near silence) and, among
  the server rooms, one-shots somewhere off in the dark every 7-29 s (two hard drives seeking, a relay, a fan spinning
  up, far static), all client-side in `AtmosphereSystem.L120.cs`.
- **Loot**: racks, wrecks, terminals, trays, spilled cables and smashed fittings drop scrap wire, metal brackets,
  glass and (racks, wrecks, terminals) now and then a circuit board (Level 3999's, which wanderers buy); a supply box
  in about one room in five (wrecked stores 45%), 2.6 a cluster; picked over 30%.
- **Notes**: a Level 120 track of six (M.E.G.'s death-rule notice, Dez's one screen, A.L.'s windows, Tom's hallway,
  Nell's Smilers, an unsigned one on light and salvage) and one folded note (the lore's ways in and out and the
  Sub-Misglitches, as unconfirmed reports). **Handbook**: its own page, "Level 120: Broken Servos" (`guide-l120`,
  after What Lives Here; one line in `GuideSystem.Added`). Titles: The Hot Aisle, The Terminal Room, A White Void,
  A Pitch-Black Hallway.
- **Temperatures** (not lore; kept from the prototype): hot aisle 38, wrecked store 26, passage 25, terminal room 23,
  server room 22, void 21, hallway 14 C.
- **Testing**: `/backrooms l120 misglitch [x z]`, `void`, `hallway`, `boot [x z]`, `back` (from the console they use
  the latest straw dummy); `120stats` checks clusters, pockets (unreachable from the passages, wholly reachable from
  their arrival, windowed) and the whole terminals.

### Choices against the brief
- The passages (4 wide, every 96 blocks) are kept from the prototype: the lore has no connective tissue between
  clusters, and they guarantee every cluster is reached. They are dark now, and dressed as the rooms are.
- The prototype's hall kinds (control room, cold vault, great hall, dead store) are gone; the aisle layout survives as
  one room kind among five. No "Server Room" door to Level 4 (DECISIONS: no thresholds in or out).
- Sub-Misglitches: not built (DECISIONS); the handbook and the folded note name them.
- The brief's boot-disk key, blinking LEDs, floor pits and corrupted wall screens (nice): not built.
- Smilers are "dazzled" by being put down as Ambient wanderers rather than by a new state in the shared menace AI.

### My inventions (not lore)
- The Misglitch's senses (drawn by light and running), its glitch-skip, its leash, its 24-hour life and six-cap.
- The trip numbers, and that spilled cables trip runners outside the hallways.
- Void 60% / hallway 40%, the nearest-pocket rule, arriving mid-hallway with a window at both ends.
- The windows' remembered return spot (the lore: "the computer block that brought you").
- The stability drain in the pockets, the temperatures, every sound, the salvage table, the room kinds.

### To check in-game (the lead's screenshots)
- A server room in the dark with a torch: the banks, wrecks, spills, the dirty white floor; whether 4% lit racks read
  as pitch black or too black. A terminal room with the one green BOOT screen.
- `/backrooms l120 void` and `/backrooms l120 hallway` (or boot a terminal; `/backrooms l120 boot` names the nearest):
  the white rooms, glow, black doors, the broken windows (frame and shards; black beyond), Smilers standing about;
  the hallway's soot walls and black fog.
- `/backrooms l120 misglitch`: the model in the dark (pixel glow, red marks), its static, the slice, the skip.
- The fog colours (base, void white, hallway black), the loops' loudness, the one-shots' frequency.

### Round 2 (2026-10-31): looked at in the client, by torchlight

Shot with `tools/clientrig/shots.py 120 --torch` (a lit torch in hand, creative, HUD off). Without a light the level is
black, as the lore says (round 1); with a torch it reads as the lore's place: dirty white floor (cream under the torch's
warm light), yellow paper with its faint stripe and print, office tiles with water rings and holes, racks in banks.

**Showcase spots** (`WorldLayout.Level120.Showcase.cs`, all found from the plans of the cluster halls round the region's
centre, nearest ring first, seed independent): `server-aisle` (down an aisle between two banks), `wrecked-bank`,
`lit-rack`, `cold-aisle` (a rack aisle room under its tray), `terminal-room`, `boot-screen` (the nearest whole terminal),
`spilled-cables`, `passage-tube` (to a crossing that keeps its tube), `passage-dark`, `void-doors`, `void-window`,
`void-smiler`, `hallway-lane`, `hallway-window`, `misglitch`. A spot is scored over a cone of tiles ahead and never faces
a wall within two blocks. New test command `/backrooms l120 smiler [x z]` (a Smiler lost in the light, turned to you);
`/backrooms l120 misglitch x z` from a player now turns it to face them.

**What the shots showed, and what changed:**
- **The White Voids were not lit at all** (brown walls by torchlight only): the panel block had absorption 99, and the
  mod's own lighting (WorldLighting) takes a source's absorption off its first step, so the light never left the panel.
  Fixed: the panel absorbs nothing and glows (`vertexFlags` glow 255).
- **One torn-paper stamp repeated on every wall** (the same hourglass of boards, block after block): now three tears
  (the old one, a blob low on one side, the paper peeled from the top in a ragged hem) and fewer of them (9% of wall
  blocks, was 12%); the water streaks are redone as soft vertical runs that carry on from block to block (the old ones
  made a ring).
- **The BOOT screen showed only a slice of its texture** (the screen face mapped the top-left corner): the screen now
  maps the texture's whole width, and the dead, smashed and BOOT textures are drawn for it ("BOOT" and a cursor, the
  crack centred).
- **Arrivals faced walls**: anyone put down in the level (goto, the cheats menu, a boot into a pocket, a window back)
  is turned to face the longest open run of floor round them (up to 24 blocks), once they are down
  (`ThresholdSystem.L120.cs`). The rig's random-arrival shots still look at fixed headings, so some of those still show
  a wall.
- Read well and left alone: the rack banks and wrecks, the cold aisles and trays, the terminal rooms, the spills, the
  passages with their ducts, the hallway's soot walls, the broken windows (frame, shards, black beyond), the
  Misglitch (black body, the pixel cubes glowing) and the Smiler in the void.

Shared files touched: `tools/mapgen/mapgen.csproj` (compiles `src/Cheats/Showcase.cs`, which the levels' showcase files
need; mapgen did not build after the showcase stubs) and `tools/clientrig/rig.py` (the showcase step's shots are copied
to the run's folder; they were left in the rig's scratch folder and overwritten by the next run).

**Final shots** (`%TEMP%/backrooms-shots/120-r2d/`, `sheet.jpg`): the void is now pure white under its glowing panels,
the black door standing open, two Smilers in the light; the BOOT screen reads "BOOT_" across the CRT; the walls show the
three tears here and there rather than one hole on every block. Checks: expclash clean, mod and mapgen 0 errors,
layouthash for 0-20 and the layout hash identical to main's, `regions` 60/60 for Level 120, a headless dummy in the level
(misglitch, void, blocksweep 10906 blocks, 0 threw) with 0 error lines, gate `--fast` PASS.

Still weak: the passages are long bare yellow runs (a cabinet, a bin, a duct; true to "connective tissue" but the
plainest part of the level); the rig's random arrivals look at fixed headings, so some still show a wall close up (in
play the arrival now turns you to the open floor).

## Links (2026-10-31)

The ways in and out LINKS.md settles for Level 120, built from Wikidot's Level 120 ("a door labelled 'Server Room' in Level
4.3"; "doors in server rooms or black hallways back to Level 4.3"), with Level 4 standing in for 4.3. Code:
`WorldLayout.Level120.Links.cs` (layout, both sides), `WorldGenerator.L120.Links.cs` (blocks), `ThresholdNetwork.L120.cs`
(the two kinds), `tools/gen_120.py` (`door_textures`, `link_blocktypes`), `tools/mapgen/L120Links.cs` (`120links`).

### Built
- **In: the door marked SERVER ROOM (Level 4, two-way).** Level 4's office blocks already have server rooms (one room in
  twenty, an open doorway, a few racks). In one office cell in 150 that has one (`L120ServerDoorChance`, salts 0x2680/0x2681;
  worked out from the office grid's own hashes, `L120ServerDoorOf`, then checked on the built cell), that room's doorway is a
  grey steel door marked SERVER ROOM, a cold green light in the gap under it (`l120-door-office-*`, kind `l120-serverroom`,
  `Unders.L120ServerDoor`); the room behind is sealed as a locked office is. From layout 12 an M.E.G. placard stands on
  the corridor wall beside it (`l120-megplacard`, `Unders.L120Placard`: "M.E.G. - LEVEL 120 - CLASS 2 / PITCH DARK. / DO NOT
  DIE HERE"), as the offices' elevators down to Level 3 have theirs; `SurvivalClass(Level120)` is now 2 (Wikidot's Survival
  Difficulty 2), one line in `WorldLayout.Gates.cs`. Used, it opens on a server room of Level 120 beside one of the
  level's doors back (`FindArrival` anchored on it), and that door becomes its way back (`ReturnFeature`): it leads to the
  corridor in front of the SERVER ROOM door, every time.
- **Out: the doors back (Level 120, one-way).** One cluster in three-odd (`L120ExitClusterChance` 0.3, salt 0x2682) has a
  steel door in a room's wall (a server room, cable room or rack aisle room: clear floor in front, the wall going on either
  side, solid behind where it can be), a line of warm office light under it (`l120-door-dark-*`, kind `l120-door`,
  `Unders.L120ExitDoor`, light 3); every Pitch-Black Hallway has one in the wall of its first or last lane (salt 0x2683).
  Used, it opens on Level 4 beside a locked office door (`In(4, PlainDoor)`): one-way, as LINKS.md has it. The door that a
  SERVER ROOM door paired with leads back to that door instead.
- **Rumours** (notes, handbook): the smashed arcade screen of Level 25, noclipping into Level 70, the Sub-Misglitches.
- **Text:** arrival lines `l120-serverroom-arrive`, `l120-door-arrive`; the block names; the folded note `r-l120-1` now
  "Ways in and out" (the door and the doors back confirmed, 25 and 70 not); a seventh common note, `l120-7` "A line of
  light" (Dez: look low for the light under a door); the handbook page's "Ways in and out" (en.json; see below).
- **Showcase:** `serverroom-door` (in Level 4, across the corridor from the door nearest spawn, its placard beside it),
  `door-back` (the nearest door back in a cluster round the centre), `hallway-door` (the nearest hallway's).

### Numbers (seed 12345, full size; `mapgen 12345 16000 120links`)
- Level 4 is about 15.5 km2 (5.5 km2 of it office blocks): **8 SERVER ROOM doors in the whole of it** (0.52 per km2 of
  Level 4, 1.46 per km2 of offices), every one built and with its placard; nearest neighbours median 1290 blocks apart
  (least 598); the nearest to spawn is 2472 blocks off (513092 514242), then 3072, 3492, 3709, 3801.
- Level 120: 72 of the 257 clusters round the centre (28%) have a door back, 16/16 hallways; from an arrival the nearest
  door back is a median 77 blocks off in a straight line (most 270).
- The network (the harness's own `ThresholdNetwork`): the four nearest SERVER ROOM doors each arrive in Level 120 beside a
  door back that leads home; four doors back used first each land in Level 4 beside a locked office door.

### Inventions (not lore)
- The look: grey steel, the SERVER ROOM plate, the green light under it (Level 4's side), the warm light under the doors
  back ("look low"); the placard's wording; the rarity numbers; that the doors back come out beside a locked office door;
  that the arrival is beside a door back which becomes the way back (the network's own rule for two-way doors).

### For the guide's ways-between-levels table (the lead merges these)
- Two-way: **Level 4, a grey steel door marked SERVER ROOM on one of the offices' server rooms (very rare; an M.E.G.
  placard beside it): Level 120, beside a steel door that leads back.**
- One-way: **Level 120, a steel door in a server room's wall (a line of light under it), or in a Pitch-Black Hallway:
  Level 4, out of a locked office door.**
- Rumoured: Level 25's smashed arcade screens (in); noclipping a server room's wall into Level 70 (out).

The handbook page's "Ways in and out" is changed in en.json only (`guide-l120-text`), since `tools/gen_guide.py` is the
lead's this round; its `PAGES["l120"]` block needs the same paragraph, in its markdown:

```
**Ways in and out**
- **In:** the office blocks of Level 4 have server rooms of their own, open doorways onto a few racks. Very rarely (a handful in the whole of Level 4, kilometres apart) one has a grey steel door instead, marked SERVER ROOM, a cold green light in the gap under it and an M.E.G. placard beside it. <hk>rightmouse</hk> it and you are in a server room here, beside a steel door: that door takes you back to the corridor you left, every time.
- **Out:** now and then a server room has a steel door in its wall, a line of warm light under it: in the dark, look low. Every Pitch-Black Hallway has one too, in its first lane or its last. Each opens on Level 4, and the door behind you there is only an office door, and locked: one way.
- The reports also speak of the smashed screen of an arcade machine in Level 25 leading in, and of noclipping through a server room's wall into Level 70: neither is known to work.
```

### Checks
- `expclash` clean; mod and mapgen 0 errors. `BACKROOMS_NO_EXP_ENTRANCES=1` layouthash (versions 1 and 12): levels 0-20 and
  the layout hash identical to main's. Without it, no line moves either: layouthash's 24 sample cells of Level 4 hold no
  SERVER ROOM door (8 in the world); `120links` finds and checks each one on its built cell instead.
- `regions`: Level 120 60/60; `120stats 3`: OK (0 unreached, 60/60 arrivals).
- Headless (port 43140, `/backrooms wayback`): the SERVER ROOM door at 513092 514242 leads to Level 120 at 656533 368289,
  beside the door back (the dump shows `l120-door-dark-*` beside the arrival); that door leads back to the corridor in
  front of the SERVER ROOM door (the dump shows the door, its placard and the sealed room's racks); a fresh door back
  and the nearest hallway's door each land in Level 4, one-way. A dummy in Level 120, blocksweep 11167 blocks, 0 threw,
  0 error lines. Gate `--fast --port-base 43140`: PASS.
- Shots (`%TEMP%/backrooms-shots/120-links2/`, `--torch`): `serverroom-door` (the grey door marked SERVER ROOM in the office
  corridor, the green line under it, the placard beside it), `door-back`, `hallway-door`. The first run showed a door in
  a wall along z as a plain slab (its door faces were north and south only): fixed, the door is on all four sides, the
  lever painted beside the lock.

## Round 3 (2026-11-01): the detailed visual pass

The user's ask: more detailed visuals, multi-block objects and signs where a real place has them, more realistic
layouts, still to the lore (Wikidot "Broken Servos" only). Round 2's shots (`final-r2/sheets/120.jpg`): the server rooms,
terminal rooms and cold aisles read by torchlight; the passages are long plain yellow runs; nothing anywhere has text but
the BOOT screen (and that reads mirrored, "ƎOOT"); the White Void rooms are the same bare white box every time.

### List
Tiers: A must, B should, C nice. A real data centre is the model where the lore is silent (marked as invention below).

**1. Layout realism**
1. [A] [done] Each cluster has a front: its terminal room (the operators' room, NOC) is moved next to a door onto a passage when it has one, so you meet the screens first.
2. [A] [done] A new room kind, one per cluster where a small room is free: the **UPS / battery room** (UPS cabinets and battery strings in rows, a switchgear panel, warning plates).
3. [B] [done] Server rooms get **cooling units** (CRAC) standing against the walls at the ends of the aisles, ducting up into the ceiling, as a real hall's perimeter cooling.
4. [A] [done] Every standing bank of racks gets its **cable tray over it** (the tray runs the bank's length at rel 3), so a row reads as one object with its trays, not loose cabinets.
5. [B] [done] **Row-end panels**: each bank ends in a blank end cabinet with the row's letter on it.
6. [B] [done] The wrecked stores become **storage / staging**: steel shelving along the walls with boxed drives, a KVM cart, crates, a mop bucket left in a corner.
7. [B] [done] Passages are **service corridors**: equipment parked along the walls (a KVM cart, a mop bucket, a UPS cabinet wheeled out, crates, a toppled rack against the wall), fire points by the doors.
8. [C] [done: the DATA HALL plates] Now and then a room's doorway onto the passage has a "SERVER ROOMS" plate and the cluster's letter, so the passages read as a building with halls, not a maze.
9. [C] [done (round 2's turn; the rig's random arrivals still use fixed headings)] The void and hallway arrivals keep facing into their space (already done in round 2: check in the shots).

**2. Multi-block objects**
10. [A] [done] **UPS cabinet** (two high: status panel with a dead LCD, vent grilles, the warning plate), new block.
11. [A] [done] **Cooling unit (CRAC)** (two high: grilles, a control panel, a square duct from its top up into the ceiling: three blocks as one object).
12. [A] [done] **KVM cart** (a trolley with a monitor and keyboard, a cable trailing).
13. [B] [done] **Battery cabinet** (two high, rows of sealed batteries behind a mesh door) for the UPS room.
14. [A] [done] **Real holes in the raised floor**: a lifted panel shows the plenum below (pedestals, cable runs), a shallow step down, not a painted panel.
15. [B] [done] **Floor cable ports** (a grommet with a cable tail) in the server rooms' floors.
16. [B] [done] **Fallen ceiling tiles** on the floor under a tile broken through (the hole above it).
17. [B] [done] **Mop bucket** with its mop (a cleaner's forgotten thing).
18. [B] [done] **Cable bundles down the walls** (floor to ceiling, three blocks) in passages and cable rooms.
19. [A] [done] Passages: a **second cable tray** along the other side (over the conduit) and **conduit** on the walls under the ceiling.
20. [C] [done] A **wall of screens** in the terminal room's front wall (big dead monitors side by side; now and then one shows a corrupted frame of a corridor: the brief's nice item).

**3. Signs and text**
21. [A] [done] The BOOT screen reads mirrored ("ƎOOT"): fix its UV so it reads BOOT_.
22. [A] [done] **Room plates** beside the doors: SERVER ROOM B (the cluster's letter), TERMINAL ROOM, UPS / BATTERY, CABLE ROOM, STORAGE.
23. [A] [done] **Passage doors**: a DATA HALL plate with the cluster's letter on one side, AUTHORIZED PERSONNEL ONLY on the other.
24. [A] [done] **EXIT signs** over the doors onto the passages, inside: dead, one in five still glowing a faint green on its battery (light 2: a little rhythm in the dark).
25. [A] [done] **The door back** (Level 120's side) gets its plate too: the same plate as the SERVER ROOM door's, reading EXIT / OFFICES, and an EXIT sign over it: the plate at both ends.
26. [A] [partly: the row letters on the end panels; the racks' own labels are one texture, not numbered] **Rack and row labels**: row-end plates with the row letter (25's panels); rack fronts with a numbered asset label.
27. [A] [done] **Warning plates** on the UPS and battery cabinets (DANGER / HIGH VOLTAGE, UPS 2), the CRAC's unit number.
28. [B] [done] **A hand-written note** taped on a wall by a door, now and then (DON'T BOOT THEM, WALK ONE WAY, NOT AGAIN...).
29. [B] [done (no arrow: it pointed the same way on both walls)] **Wayfinding stencils** on passage walls by the crossings (the hall letter).
30. [B] [done] **Fire points**: an extinguisher on its bracket with the red FIRE EXTINGUISHER sign over it, by the passage doors.
31. [C] [done] An evacuation plan by some passage doors.

**4. Detail visuals**
32. [A] [done] Passages dressed (items 7, 18, 19, 29, 30): no long plain stretch.
33. [B] [done] **Water damage**: a wet stain on the floor under a stained ceiling tile, now and then.
34. [B] [done] **Skirting**: a dark wooden skirting board along the foot of the yellow walls (their lowest block), rotting where the paper is torn.
35. [A] [done] **The White Void rooms differ**: one small thing per room by its hash: a crack in a wall, a glitched floor tile, a lone office chair, a single CRT on the floor, one ceiling panel dead, a smudge on a wall, a sheet of paper; some rooms nothing.
36. [C] [done: fittings moved off the banks onto the aisles] Ceiling rhythm in the server rooms: the fittings line up over the aisles rather than on a grid.
37. [B] [done] The faint green EXIT signs (24) as the passages' only light rhythm: rare and dim, the dark kept.

**5. Lore alignment**
38. [A] [done] Still "usually pitch-black": every new light is 2 or less and rare (EXIT signs on battery, a corrupted screen).
39. [B] [partly: UPS cabinets torn open; the CRACs stand whole] "Massive blocks of computers ripped apart": the new cabinets come wrecked too (a UPS torn open, a CRAC with its panel off).
40. [B] [done] The void oddities stay small: the lore's voids are "pure white"; nothing in them a player could take for a feature.
41. [C] [done] The hand-written notes stay in the level's voice (the six wanderer notes' authors), not new lore.

**6. Released-level alignment**
42. [A] [done] Every new block has its name in en.json (HUD, pick-block), salvage like the racks' (scrap wire, brackets, glass), sounds.
43. [A] [done] Showcase spots for every new set piece (UPS room, CRAC, KVM cart, floor hole, a dressed passage, door plates, the door back's plate, a void oddity, the wall of screens), computed from the layout.
44. [B] [done (no placard on this side, as the released levels' exits)] The M.E.G. placard convention: Level 4's side has one; Level 120's door back gets its EXIT plate (25), no placard (an exit, as released levels' exits).
45. [C] [done] The handbook page mentions the plates and the faint EXIT signs as a way to read the dark (en.json only).
46. [C] [skipped: nothing the map needs] Map: nothing new (the map draws the plan's walls and floors; the new props are props).

### Built (round 3)
Code: `WorldLayout.Level120.Dress.cs` (new: the dressing's layout), `WorldGenerator.L120.Dress.cs` (new: its blocks), hooks in
`WorldLayout.Level120.cs` and `WorldGenerator.L120.cs`; assets `tools/gen_120_detail.py` (new, run from the end of
`gen_120.py`): 11 new blocktypes (`l120-ups`, `-battery`, `-crac`, `-kvm`, `-mop`, `-debris`, `-paper`, `-rowend`, `-shelf`,
`-floorhole`, `-walldeco` with 49 kinds), new states on `l120-wall` (skirting), `l120-floor` (port, wet), `l120-void`
(glitch, paneldead). One Tiles.cs member in Level 120's block (`CeilingKind.L120VoidPanelDead` 388). Props 807-815, Decor
384-395 (declared in the level's file, as its other props are).
- **A cluster as a data hall.** The room on the hall's edge at the middle of one side (where the first door onto that
  passage opens) is the terminal room (the operators' room, with a wall of big dead screens two high on the wall the desks
  face; one screen in eight shows a corrupted frame of a corridor, glowing faintly); the smallest other room is the **UPS /
  battery room** (a row of UPS cabinets, one in four torn open, rows of battery cabinets behind with two-wide aisles, the
  PDU panel DANGER 480 V, a fire point). Server rooms: every standing bank has its cable tray along its top and an end panel
  at each end with its row's letter (ROW A, B...); cooling units (CRAC 3: louvres, control panel, a duct up into the
  ceiling, three blocks) at half the aisles' ends; cable ports in the floor; lifted panels are now real holes into the
  plenum (pedestals, cables, half a block down). Stores have steel shelving of boxed drives along both long walls, a KVM
  cart or two, a mop bucket. Cable rooms have cables down their walls and a panel.
- **Signs.** Beside the doors between rooms a plate naming the room behind (SERVER ROOM + the hall's letter, TERMINAL ROOM,
  UPS / BATTERY, CABLE ROOM, STORAGE; on most doors, both sides); at every door onto a passage an EXIT sign over it inside
  (one in five still faintly green, light 2), the blue DATA HALL plate with the hall's letter on one side outside,
  AUTHORIZED PERSONNEL ONLY on the other, often a fire point (extinguisher on its bracket, the red sign over it) and now and
  then an evacuation plan; the hall's letter stencilled (HALL B and an arrow) on the passage walls by each crossing; in six
  clusters in ten one pencilled note taped up beside a door (DON'T BOOT THEM, WALK ONE WAY, NOT AGAIN, IT GETS UP WHERE
  YOU FALL). The doors back to the offices carry their plate too (EXIT / OFFICES, the SERVER ROOM door's plate style) and an
  EXIT sign over them (lit over one in two). The BOOT screen's B no longer loses its back to the screen's edge.
- **Passages** are service corridors now: a cable tray down the far side over two runs of conduit on the wall, cables down
  the walls, things parked along the walls (KVM carts, mop buckets, a UPS wheeled out, crates, boxes, a rack dumped on its
  back, a wet-floor sign), fallen ceiling tiles (the hole above them), lifted panels and leaks (a wet patch under a stained
  tile) down the middle.
- **Detail.** A dark wooden skirting board along the foot of every yellow wall (rotting where the paper is torn); leaks and
  fallen tiles in the rooms too.
- **The White Voids**: about two rooms in three get one small thing wrong (List 35): a crack, a smudge, a glitched floor tile, a chair, a desk with
  its dead CRT, one panel gone dark, a sheet of paper, a rack on its own; the rest as white as ever.
- **Handbook** (`guide-l120-text`, and `gen_guide.py`'s `PAGES["l120"]` alike): the rooms and plates, and the EXIT signs as
  marks to steer by. Showcase: `hall-door`, `hall-exit`, `noc-screens`, `ups-room`, `crac`, `row-ends`, `storage`,
  `floor-hole`, `void-odd`.

### Inventions (round 3; not lore)
The lore says only "broken server rooms", "massive blocks of computers ripped apart", yellow paper, office tiles, dark.
Everything that makes a cluster a data hall is mine, from real ones: the operators' room by the way in with its wall of
screens, the UPS / battery room, CRACs, trays over the banks, row letters, the plates and their wording (SERVER ROOM + a
hall letter, DATA HALL, AUTHORIZED PERSONNEL ONLY, UPS 2, CRAC 3, PDU-2 480 V, EXIT / OFFICES), the EXIT signs still on
their batteries, the fire points, evacuation plans, stencils, the four pencilled notes (in the wanderer notes' voice, no
new lore), the passages' parked equipment, leaks, fallen tiles, skirting; and the White Voids' small wrong things (the
lore's voids are "pure white": these are one thing at a time, and a third of the rooms have none).

### Balance notes for the lead
- **Misglitch cap** (the balance review): at most **3** within 24 blocks of a death (was 6), `L120System.L120MisglitchCap`;
  the console/test command's message follows.
- **Supply boxes**: room kinds shifted (one operators' room and one UPS room a cluster), so the box roll for those two
  kinds is 10% (others unchanged: 22%, stores 45%); `120stats 8` (257 clusters) gives 2.8 boxes a cluster against 3.0
  before (718 against 761; the table and picked-over share are untouched).
- **Salvage**: the new cabinets drop what racks drop (scrap wire, metal brackets; KVM carts and smashed screens glass):
  more breakable salvage per cluster (a UPS row, battery rows, CRACs, shelving, end panels). No circuit boards from any new
  block; no food, water, beds or safe rooms.
- **Light**: EXIT signs over one door out in five (light 2, green) and over one door back in two; a corrupted screen
  now and then (light 1). The level stays pitch dark; the lit EXIT over a door back is a tell for the way out.
- **Floor holes**: a lifted panel is now a real half-block step down (2% of server-room aisle tiles, was a painted 3%;
  0.3% of passage tiles). Walkable; the trip rule (L120System) does not look at them.
- **Racks**: standing racks per cluster fell from 970 to 710 (`120stats 8`: the two new rooms, the end panels); lit racks
  3.8% of standing (was 4.1%), so lit racks per cluster about 27 (was 40).
- `regions`: Level 120 60/60, but 1 of the 60 arrivals now counts as "in a pocket under 3000 tiles": the harness's own
  walk-through list (`tools/mapgen/Regions.cs`, shared) counts every Level 120 prop as a wall (spilled cables, fallen tiles,
  paper); in the game they are walked over, and `120stats` (the level's own check, with the game's rule) finds every
  walkable tile reached from the passages.

### Questions for the user
1. The hall letters (A-H) repeat every eight halls (x + 3z mod 8: no two neighbours alike): enough, or should the halls
   carry numbers too (DATA HALL B4)?
2. The pencilled notes say DON'T BOOT THEM / WALK ONE WAY / NOT AGAIN / IT GETS UP WHERE YOU FALL: more, or other words?
3. Should the lit EXIT sign over the doors back to the offices be rarer (it makes the way out easier to find in the dark)?
