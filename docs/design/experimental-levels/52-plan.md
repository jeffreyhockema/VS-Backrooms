# Level 52 "School Halls": prototype plan

Internal id **23**, `WorldLayout.Level52`, tag `52`, blocks `l52-`, method infix `L52`, region south-south-east (see README).
Prototype only: disconnected, cheats menu / `/backrooms goto 52`, no entities, thresholds, loot or handbook.

## 1. What the lore says

**Conflict:** the two wikis disagree about the number. Wikidot's Level 52 is not a school, and Fandom's is.
- Wikidot, https://backrooms-wiki.wikidot.com/level-52, "Destination Reached": a dark limestone cave with
  stalactites, ceilings under 2 m in places, dripping water, little food. It has no named sub-zones and no classed
  entity, only a sense of being watched. Finds: three human remains, a dead campfire, crude tools, a courier's
  notebook (57 entries, 43 legible, degrading into drawings of eyes). Entrance: a shallow passage from Plane #445.
  No survival class could be read from the page.
- Fandom, https://backrooms.fandom.com/wiki/Level_52 (fetched through the `api.php?action=parse` wikitext call),
  "Greenfield Campus": class 1e Environmental, **Safe**, Stable, minimal non-entity hazards. A vast university /
  school campus of merged buildings on green hills under a permanent blue sky, 10-32 C, light wind, no day-night cycle.
- Fandom interiors: smooth concrete, tile and multicoloured carpet floors in pale brown, grey, beige and off-white,
  all pristine. Classrooms hold desks, chairs and teaching supplies, but their lights and electrics are OFF, while
  the corridors' appliances and lights work. Labelled signs over doors carry 4 digits: rooms counted, floor,
  building. About 100 rooms a campus. Admin offices, faculty rooms, labs, libraries and utility rooms are mostly
  empty or stripped of their contents.
- Fandom courtyards: merged buildings enclose a courtyard of artificial grass, paths, benches, lamp posts, trees,
  or a sports court (J. Turner has a basketball court). The canteen is a hall with seating and empty food stands.
  Water fountains, vending machines and lockers line the canteen and halls.
- Fandom landmarks: Marshall David Campus (white concrete, five floors, endless locker corridors, "looks like a high
  school", M.E.G. outpost), J. Barry Campus (blue and white painted concrete, trade hub), J. Turner Campus (2 floors).
- Fandom entities: none today. The history is a Sanguine Festivus outbreak (1959 and later), which is out of scope.

Use Fandom's Greenfield Campus (the user's brief: "School Halls"). Wikidot's cave is not used.

## 2. The level in this mod

Round noclip region, radius `max(40, spawnMacroX / 50)` cells, one cell = 32 blocks, band 40 blocks tall. Everything
is derived from world coordinates and `Hashing.Hash(seed, a, b, salt)` (salts 0x2300 up). No per-region state.

**Skeleton (the "campus", one shared school like 188's building).** A global lattice of main halls:
- Hall lines every **K = 3 cells** (96 blocks) on both axes, each 7 blocks wide (double-loaded: lockers on both walls,
  5 blocks clear), 4 high. A line at index `i` runs through the whole region, so halls cross at every lattice point
  and the school reads as a grid of long straight corridors. Cross points get a 9 x 9 hub with a pillar and a fountain.
- Each lattice block between halls (88 x 88 after hall width) is a **wing**. Use `Noise2` (scale ~3 cells) to pick
  a wing kind from the hash: classroom wing (60%), gym (6%), canteen (8%), library (8%), courtyard (10%), admin /
  utility (8%). The kind is fixed per wing from `Hash(seed, wx, wz, 0x2310)`, never from a neighbour.
- **Classroom wing:** use `PlanCache` + BSP, as Level 4's office plans do, over the 88 x 88 wing but with a fixed
  bias: split first into two rows of 11-block-deep rooms against each hall wall, then split each row along its length
  into classrooms 9-11 blocks wide with a hash-chosen width. Each room has one door to its hall (centred, hash
  jitter of +-2), and a second door to the next room in 1 in 5 pairs. The strip between the two rows (about 66 x 11)
  becomes a **second-tier hall** (3 wide) or a row of labs and storerooms: 70% a hall, linking to the main hall at
  both ends via `EdgeHall`-style carving so a wing's rim is always passable if its plan walls cut off a neighbour.
- **Classroom contents** from `Hash(room cell)`: grid of desks (row spacing 2, 4 columns by 3-5 rows), a chalkboard
  along the shorter wall, teacher desk, 1 in 6 has chairs stacked, 1 in 8 has dead lights, 1 in 10 empty and stripped.
- **Gym:** one 28 x 20 room, 9 high (the floor of the neighbouring wing rises to match the ceiling), wood floor, hoops
  (`basketballhoop`) at both ends, bench rows, high windows glowing.
- **Canteen:** 40 x 24, 5 high, long tables (`cafetable`, `cafechair`), vending machines on one wall, a dark serving counter.
- **Library:** 30 x 24, 4 high, rows of shelves (`officebookshelf`), reading tables.
- **Courtyard:** 40 x 40 open room, no ceiling in the cut, a lit false-sky skylight ceiling at rel 12 (like 188's
  open spaces), grass floor (`parkfloor`), paths, benches, a tree prop. Windows in the surrounding halls look in.
- **Storeys:** one floor in the prototype (rel 0..4 hall height), plus a stairwell every second lattice point leading
  to a second storey (two floors, band 40 gives room). The prototype may start with one floor and add the stairs if time.
- **Heights:** halls 4, classrooms 3.5 (a bulkhead is not needed: treat as 4), gym 9, canteen 5, courtyard open to rel 12.
  Floor stays level (no drop). Outside the campus rim: solid nothing, as in 188.
- **Room signs:** 4-digit plaque over each door (the lore's `rooms-floor-building` code) via a `Props` slot.

**Light.** Hall fluorescent troffers every 6 blocks on the centreline. Per fixture from `Hash`: 7% dead, 5% flickering
(a `Props` or light-variant block). Classrooms dark by default, per the lore (their lights are off), lit only when the
room hash says so (1 in 6) and by windows. Canteen / gym: rows of troffers and window light.
**Fog:** cold neutral grey-beige (`#b8b2a4`), light density (fog 0.012), slightly denser in empty classrooms.
**Sound:** a low steady fluorescent buzz bed in halls, rare distant door slams and a far-off bell, a faint ventilation
hum in the classrooms. Open courtyard: wind and birds. Reuse `fluorescentlight` hum and `officehum` loops if they exist.
**Temperature** 18 C inside (neutral), courtyard 22 C. **Stability:** safe and calm: +0.001 per second, never a drain.
Danger 0.0 (the prototype has no entities).

## 3. Assets

**Reuse (no new files):** `ceilingtile`, `fluorescentlight`, `concrete`, `level4/officeceiling` + `officelight`,
`level4/officecarpet` (classroom floor variant), `level4/officewall` (rooms), `level4/officeglass` (door and hall
windows), `level4/officechair`, `level4/partition`, `level4/vendingmachine` and `watercooler`, `level5/hotelwood`
(gym floor), `detail/officedoor` and `metaldoor` (doors), `detail/cafetable`, `cafechair`, `basketballhoop`, `bench`,
`chalkmark`, `easel`, `trashcan`, `wetfloorsign`, `parkfloor`, `officebookshelf`, `foldingchair`, `exitlintel`, `ficus`.
Vanilla `game:` trees / grass only if a tree is wanted in the courtyard (`game:log-placed-*` is enough; or skip).

**New (6 max, all `l52-`):**
1. `l52-locker`: a bank of three tall steel lockers, grey-blue, vents at the top, door seams and a latch, shape with
   2 or 3 doors per wall tile (`modelkit`). Variants by facing, and one with an ajar door.
2. `l52-tile`: school vinyl floor, 16 px beige and cream checks with grout lines and scuffs (`texlib` noise on a base).
3. `l52-chalkboard`: green-black slate in a thin wood frame with chalk ghost-marks and a ledge (a thin shape on the wall).
4. `l52-desk`: a student desk and attached chair in one block (flat top, tube legs), 1 collider, facing variants.
5. `l52-wall`: school wall, two-tone painted concrete (mint lower two blocks, off-white above, a dark rail line) so
   long halls read as a school and not an office. Also reused for the pilasters at hall crossings.
6. `l52-fountain`: a drinking fountain on the wall, steel with a bowl (optional: drop it if the budget is tight).

## 4. Lang strings (add to `en.json`)

- `"level-23": "Level 52: School Halls"`
- `"levelhint-23": "Every door is a classroom. Every classroom is empty."`
- `"levelname-23": "Level 52"`
- `"level-2301": "The Gymnasium"` (for the gym and canteen zone title)
- `"level-2302": "The Courtyard"` (for the open courtyard)

## 5. Open questions

1. **Level number:** Wikidot has the cave, Fandom has the campus. Recommendation: keep "School Halls" (Fandom's Greenfield
   Campus) as the brief says. Put the Wikidot cave on a later list; do not mix them.
2. **Storeys in the prototype?** Recommendation: one floor first; add the second storey only if the grid looks too flat.
3. **Outdoors or no?** The lore has a green hillscape outside the campuses. Recommendation: skip it: solid rim, like 188.
4. **Dark classrooms (lore) vs lit (playable)?** Recommendation: 5 in 6 dark, with the doors open and the hall light
   spilling in, so exploring them reads as tense but not unplayable.
5. **Locker walls: block or model?** Recommendation: one block per wall tile (3 lockers wide) with a model, not a prop, so
   a hall is a few hundred blocks and not thousands of props.
6. **Time of day / windows:** Recommendation: a constant bright window glow (no day cycle in the lore), no sky.

## Status (prototype built, 2026-10-17)

**Built.** `WorldLayout.Level52.cs`: a lattice of main halls every 96 blocks each way (7 wide, lit down the middle every
6 blocks, 7% dead, 5% flickering, one in two emitting; banks of lockers on both walls; a pillar where two cross; now and then
a vending machine or water cooler just past a crossing, a bin or a wet-floor sign). Between the halls, 87 x 87 **wings**,
each laid out once from its own hash (`L52PlanOf`, a `PlanCache`), possibly transposed: six rows of rooms 12-13 deep (two
facing the main halls, four along two 3-wide secondary halls that cross the wing and open into the main halls at both
ends), split along the row into rooms 9-12 wide. Every room has a door onto a hall; about one in five a second into the
next room. Classrooms (78%): rows of `l52-desk` facing a chalkboard (`l52-chalkboard`, 2 high, framed ends) on a side wall,
Level 4's desk for the teacher, a wastebasket, one in six with chairs stacked at the back; store rooms (shelves, boxes) and
stripped rooms the rest. Rooms are dark (lights off) but one in six. **Gym** (one wing in ten) and **canteen** (one in
eight) take the middle two rows and the hall between them on one half of a wing (43 x 30): the gym 8 high (ceiling at
the band's top, rel 9) on maple boards with court lines, hoops at both ends, benches, high lights; the canteen 5 high with
four rows of folding tables and chairs, vending and snack machines, a serving counter with stoves and fryers. Neither is
laid out unless the wing and the cells round it are all Level 52 (no tall room ever meets the rim). Where the region ends,
the shared `CarveEdgeHall` runs a hallway inside the rim. Arrivals: main halls only. Stability 1.1, temperature 18.
Fog: light grey-beige `(0.0065, 0.72, 0.70, 0.64)`; classrooms and store rooms a darker, closer air; title keys 2301 "The
Gymnasium", 2302 "The Canteen". Sound: the hall panels' own hum (`fluorescentlight` ambient), Level End's room tone quiet in
classrooms, and a new distant school bell (`sounds/ambient/52/bell.ogg`) every 2.5-6.5 minutes.

**Assets** (`tools/gen_52.py`, 6 codes): `l52-wall` (base/dado/upper cubes), `l52-locker` (lower/upper x side, cubes with the
lockers on one face and the wall's paint on the others), `l52-tile` (hall/room), `l52-gymfloor` (plain/linens/linewe),
`l52-desk` (JSON shape, by side), `l52-chalkboard` (lower/upper x l/m/r x side, JSON shape). Reused: officeceiling,
fluorescentlight on/lit/off/flicker, concreteceiling, Level 4 desk/vending/cooler, metalshelf, detail props (chairstack,
wastebasket, cardboardboxes, trashcan, wetfloorsign, basketballhoop, bench, foldingtable/chair, snackvending,
snackcounter, stove, fryer). The plan's `parkfloor`, `officebookshelf`, `ficus`, `exitlintel` exist but are not used;
`officehum` does not exist (the hum is fluorescentlight's).

**Skipped:** library, admin, courtyard, second storey, room-number plaques, windows, drinking fountains, door leaves (all
doorways are open gaps), title keys beyond 2302. Band unchanged (depth 30: the gym is 8 high, not the plan's 9).

**Harness.** `52stats` (7 x 7 wings round the centre, SPAWN=1000): 49 wings, Classrooms 67% / Canteen 18% / Gym 14% (before
the shares were lowered to 10% / 12%; full size after: 84 / 8 / 8); 2232 rooms, doors 1: 1559, 2: 594, 3: 63, 4: 16;
every room and every walkable tile reached from the main halls, none sealed. At the east rim (`52stats 3 rim`): 1346 whole
rooms, all reached; 273 walkable tiles (0.12%) in rim pockets not reached (never arrival spots). `regions`: 60/60 arrivals
for 52, none wrong or in small pockets, full size and SPAWN=1000; 0.11 ms a cell. `layouthash`: levels 0-20 and the overall
hash unchanged. Headless (port 42483): `blocksweep` 7869 blocks, 0 threw; dumps at 565904,642096 and 565828,642096 show the
hall (light 14 under a panel), lockers, desks, boards, dark classrooms (light 0); no missing blocks, shapes or textures.

**Known gaps / check in a client:** the facing of the desks (student faces the board), chalkboard ends (l/r), hoops,
benches, canteen chairs and the snack counter; the gym line texture's direction (NS/WE) on the floor; whether classrooms
are too dark to read (only hall light through one door); lockers are flat cubes (no relief); the rim's carved hallway
cuts through classrooms.

## Detail pass (2026-10-30): the Greenfield Campus

A rebuild to the Fandom lore (brief: `lore/52-brief.md`; decisions: `lore/DECISIONS.md`). The prototype's windowless
lattice is gone; its useful pieces (lockers, desks, chalkboards, the gym floor, the canteen's tables and counters, the
bell) live on inside the new buildings. Everything above this section (1-5 and the prototype's status) is history.

### How open sky works here (checked against 94, 188, 73 and 10 first)
- Level 94 is open sky with the real day and night (`dayNight: true`). Level 188 is not open sky: its "sky" is a block
  roof (`l188-sky`) under the band's top. Level 73 is open sky (`IsOpenSky`) with the outside sky hidden in a fog sphere
  of the fog's colour and its own moon drawn by `Regions.L73Moon`; Level 10 hides its sun the same way.
- Level 52 follows 73: `IsOpenSky(Level52)` (no mantle cap; the rain height is the top block), no roof protection
  (`Protection.RoofFrom` int.MaxValue), band depth 3 (`L52BandDepth`), so the lit band runs from rel -3 to rel 36: eight
  storeys of four blocks (slab + 3 air) with a roof and a parapet fit under it (top slab at rel 4N, roof membrane 4N+1,
  coping 4N+2; N <= 8).
- No day or night: the level's `Atmosphere` keeps `dayNight` false (the ambient is held at noon, as on every such
  level), and the real sky is hidden in a fog sphere of a **fixed** sky blue (`AtmosphereSystem.L52SkySphere`; not the
  fog's colour, so the sky stays blue seen through windows from indoors). `Regions.L52Sun` draws the sun
  (`textures/environment/l52-sun.png`) fixed high in the south-south-east, a little dimmer while it is night on Terra
  (the lore's drifting intensity); the scene dims by up to 12% then too. A few white clouds (`clouds: 0.2`).
- The map: Level 52 has its own case in `BackroomsMapLayer.SampleHeights` (each column on its own ground, as Motion).

### What was built
- **Land** (`WorldLayout.Level52.cs`): campuses on a 352-block lattice, about one lattice cell in six left as open plain;
  low wavy hills between them (0-7 blocks: an fbm plus a long wave), level for 40 blocks round each campus; a gravel and
  sand road 4 wide from each campus to the next east and south through the gaps in their fences; lone trees; tall grass
  and wild flowers in patches (generator); "a long fence that serves no use" on some empty plains; toward the region's rim
  the hills rise into a ridge (rel 26) instead of a wall.
- **Campus** (150-212 blocks a side; `L52Campus`, a `PlanCache` of 12): a concrete barrier with two blocks of chain-link
  over it (not climbable), a 5-wide gap in the middle of each side and a 3-wide one beside a section set a step out of
  line; no gate. Lawns, paved aprons round every building, paths from every outside door and every gap, streetlights,
  benches and bins along the paths, a few trees.
- **Buildings** (a storey is a slab and three of air; the plan is the ground storey, the storeys above repeat it):
  - the **quad**: four teaching wings 21 deep merged round a courtyard (a corridor ring 3 wide, rooms 7 deep on both
    sides), a lobby through the outer rooms in the middle of each side, courtyard doors on two opposite sides, a scissor
    stairwell (7 x 7) in each inner corner; the courtyard is artificial turf with paths, benches, bins, lamps and trees,
    or (J. Turner, and 30% of ordinary campuses) a basketball court;
  - standalone **teaching blocks** and **lodging blocks** (21 deep, a corridor down the length, doors at both ends, a
    stairwell at one end), and **halls** two storeys high: the canteen (long tables, the empty food stands, vending
    machines, a cooler, a drinking fountain), the gym (court lines, hoops, benches) and J. Barry's warehouse (shelving,
    pallets, medical cabinets, a few supply boxes).
  - Storeys 2-8 (weighted to 3-4); Marshall David 5, J. Barry 3, J. Turner 2.
  - Rooms are cut every 8-11 blocks along each stretch; each has a door onto the corridor (or into a neighbour that has
    one); a **4-digit plaque** (rooms counted, storey, building) on the corridor wall to the right of every door
    (`l52-plaque`, two blocks meeting at a seam); **lockers** down the corridor walls (every corridor at Marshall David,
    about two in three elsewhere); corridor lights every 4 blocks (45% on, 43% glowing, 7% dead, 5% failing);
    **classroom troffers always dark**; window bays (two, then a pier) on every storey of every outside wall, so the
    rooms are lit by daylight.
  - What a room is, storey by storey (`L52KindOn`, `L52Furnish`): classroom 70% (student desks facing a chalkboard, a
    teacher's desk, a 2000s television in the corner, a wastebasket, now and then stacked chairs), lab, library (empty
    shelving), office, store room (shelves, boxes, sometimes a supply box), stripped; lodgings in the lodging blocks and
    (45%) at J. Turner; the M.E.G.'s abandoned offices on the top floor of Marshall David's quad. A room that is not a
    rectangle (round a quad corner) is left empty. Corridors: now and then a drinking fountain, vending machine, cooler
    or bin against the wall.
  - Palettes: interior paint beige / white / blue / grey (`l52-wall-*`, `l52-locker-*`), façades white / beige / pale
    brown brick / grey / blue (`l52-facade-*`); floors hall vinyl checks, room vinyl, four carpets ("multicoloured
    carpets"), lab lino, concrete, maple.
- **The named campuses**: Marshall David (the lattice cell of the region's centre; white, 5 storeys, lockers
  everywhere, the M.E.G. offices; every arrival is on it or on a campus next to it), J. Turner (4 lattice cells, about
  0.9 mile, away: 2 storeys, a basketball court in the quad, lodgings), J. Barry (3 cells away: blue and white paint, the
  warehouse, false alarms). In a small world they are as near as the region allows.
- **Air and sound** (`AtmosphereSystem.L52.cs`): a thin clear blue haze outdoors; warmer, closer air indoors, dimmer in
  classrooms; the wind over the hills gusting over minutes and stronger when the temperature turns fast (muffled
  indoors); the corridor lights' hum (their own ambient); a classroom's room tone; the school bell far off now and then
  (indoors); false alarms at J. Barry. Titles: the three campuses; in an ordinary campus, its gym, canteen, courtyard.
- **Temperature**: 10-32 °C drifting over hours (`L52OutdoorTemperature`, read at `L52Hours`, which `Regions.L52System`
  keeps on the server and the client from the calendar); indoors 21 °C plus 30% of the outside's difference. Stability 1.1.
- **Content**: no hostile spawns (band Safe); a rare Faceling (roster weight 0.4, rarity 0.15) in a teacher's (75%) or
  office worker's clothes (`MenaceSystem.ChooseLook`, `EntityBehaviorFaceling.TeacherLook`); loot sparse by lore (store
  rooms' and the warehouse's boxes, 30% picked over; teacher's desks and filing cabinets drop notes as everywhere;
  vending machines, coolers and fountains give Almond Water and water); six wanderer notes (track `l52`, one block in
  `tools/gen_notes.py`) and a loose note on about one campus cell in eight (`NoteSpots`, kind "cache"); a handbook page
  (`PAGES["level52"]` in `tools/gen_guide.py`, registered in `GuideSystem.Added`); lang: title, hint, the campuses'
  titles and hints, block names.
- **Assets** (`tools/gen_52.py`, `tools/gen_52_tex.py`; drawn by a Sonnet worker to a written contract): palette walls
  and lockers, façades and coping, windows (2 high), slabs and troffers per floor finish, the roof, turf, the court,
  paving, chain-link, the barrier, plaques (ten digit textures; 800 variants), a wall drinking fountain (a dispenser like
  the cooler), the sun. The prototype's palette-less `l52-locker-{lower,upper}-*` codes are kept (beige) because Level
  31's generator borrows them.

### Choices against the brief, and inventions
- Storeys are 2-8, not the lore's 2-10: the lit band (40 blocks) holds eight storeys of four with a roof.
- Elevators: none (stairs only, as the brief recommends).
- The courtyard roof ("translucent or missing") is left open; pedestrian bridges, the abandoned bases (Sunfire,
  Emberwatch, Blackcross, Blindside, P.E.A.) and apartment complexes beyond the lodging blocks are left out (nice-to-have).
- No Crash wing and no partygoers: the Sanguine Festivus is history only (notes, handbook), per the decisions.
- **Inventions** (not in the lore): the school bell (kept from the prototype); the lodging blocks and J. Turner's beds
  standing in for the lore's apartments; J. Barry's alarm reuses Level !'s far alarm; the ridge at the rim; the window
  rhythm; the misplaced fence section set a step inside the line; the sun's place; the AC units on the roofs; the loose
  notes.

### Checks
- `52stats 4` (SPAWN=16000): 68 campuses (13 open plains), 282 buildings, 3792 ground-storey rooms (none without a door),
  3675 plaques, 369 stairwells; 60 of about 2 million walkable ground-storey tiles not reached from the fences' gaps
  (single tiles boxed in by furniture); arrivals 60/60, all on a campus. `52stats 3` at SPAWN=1000: 28 campuses, fine.
- `layouthash` (versions 1 and 12): levels 0-20 and the layout hash identical to main's. `regions`: 60/60 arrivals, none
  wrong or in pockets (full size and SPAWN=1000), 0.5-0.6 ms a cell.

### To check in a client (screenshots)
- The sky: blue at every hour, the sun's disc and glow; whether the sky sphere also hides the clouds; the sky seen through
  windows from inside.
- Window glass and chain-link alpha (render passes); the plaques' digits reading left to right on every side; the
  chalkboards' ends; desks facing their boards; beds; canteen chairs facing their tables.
- Classrooms: lit enough by their windows (rooms are 7 deep; the corridor side gets little daylight).
- The stairwells (scissor flights, headroom, the landings' doors) on buildings of three storeys and more.
- The hills: one-block steps between grass levels; tree crowns; the tall-grass patches; the rim's ridge.
