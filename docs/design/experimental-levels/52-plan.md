# Level 52 "School Halls": plan

Internal id **23**, `WorldLayout.Level52`, tag `52`, blocks `l52-`, method infix `L52`, region south-south-east (see README).
Built and connected (see Links).

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

### Round 2 (2026-10-31): looked at in the client, fixed

Shots: `%TEMP%/backrooms-shots/52-r2a` (arrivals only: the showcase shots were lost to a rig bug), `52-r2b` (first full
tour), `52-r2c`, `52-r2d` (after the fixes below), final `52-r2-final` (`sheet.jpg`). Showcase: `WorldLayout.Level52.Showcase.cs`, 14 spots worked out from
the plans: the way in at Marshall David's fence, the quad's entrance, the campus across its lawns, the courtyard, a locker
corridor, the M.E.G.'s top floor, a classroom (first floor up), a stairwell, the canteen, the view from the quad's roof, a
pedestrian bridge, the hills on the road east, J. Turner's basketball court, J. Barry's warehouse.

What the lead's review and the first shots showed, and what changed:
- **Dry olive grass and leaves** (vanilla's mild climate tint): the level now has its own plant tint
  (`BackroomsModSystem.LevelTintMap`, as Motion and Level 10 have): hot on paper, so the seasonal yellowing drops out, and
  wet, a natural deep green varying a little cell by cell. The courtyards' artificial turf (its own texture) stays the
  brighter green, so it reads as artificial beside the real grass.
- **Uniform grey slabs**: every building now has its own look (`L52AddBuilding`): the campus's façade mostly, now and then
  another of the lore's colours (white concrete, beige render, pale brown brick, grey precast; J. Barry blue and white by
  turns; Marshall David and J. Turner all white, as the lore has it); a precast trim colour (off-white, grey or sandstone)
  for a cornice under the parapet and, by building, string courses at every floor line or the first only; window rhythm
  by building (pairs, a ribbon, singles); a dark stone base course on three in four. New blocks `l52-band-{light,grey,stone}`,
  `l52-plinth`, `l52-canopy` (gen_52.py / gen_52_tex.py).
- **Entrances that read as entrances**: a precast surround either side of every outside door and a lintel over it, and a
  flat cantilevered canopy (charcoal fascia, pale soffit with downlights) over the paving in front at the first floor line.
  No signs with a campus name: the lore says there is none anywhere ("no subject and no campus name").
- **Pedestrian bridges** (the lore's, a "nice" item of round 1): from the quad to a teaching block or lodgings 8-24 blocks
  off it, face to face, a glazed walkway three wide at the first floor up (`L52LayBridges`; 44 in the 68 campuses of
  `52stats 4`). Nothing is furnished within two blocks of a bridge's opening on its floor.
- **Arrivals facing a wall**: players put down in the level now face the cardinal way with the longest clear run
  (`ThresholdSystem.L52ArrivalYaw`, one line in the shared arrival code, as the Hub's).
- **Roads stepping over the hills** (seen in the hills shot): the hills are graded down within 14 blocks of a road's
  middle line (`L52RoadDistance`), so the gravel roads run level with banks either side.
- **The sky**: bluer (the sky sphere's blue deeper and denser); the horizon keeps a pale haze.
- Shared fixes: mapgen compiles `src/Cheats/Showcase.cs`; the rig copies the showcase step's shots out (both the same
  change as exp/36's a404577b, so the merges are clean).

What held up in the first tour: the locker corridors, the classrooms (board, desks, the 2000s television, daylight
through the windows with the lights off), the stairwells, the canteen's rows of tables and empty food stands, J. Barry's
warehouse, J. Turner's court, the fence and its gaps, the hills with their flowers.

Inventions added this round (not in the lore): the trim, base course and canopies; the bridges' glazing and placement
(the lore has bridges but not their look); the arrival facing.

Still weak after round 2: the roof shot (the parapet and an air-conditioning unit; the campus below hardly shows over the
parapet); the courtyards' trees stand on a visible grid; Marshall David reads light grey rather than white in shade; the
M.E.G.'s top floor is plain offices (no outpost signage: the lore names none for it); vanilla's falling-leaf particles
drift across the sky near trees; the rig's random arrivals still face a wall now and then (the rig turns the camera
itself; players get `L52ArrivalYaw`).

Checks (round 2): expclash clean; mod and mapgen 0 errors; layouthash v1 and v12: levels 0-20 and the layout hash identical
to main's; `regions` 60/60 for 52; `52stats 4` OK (0 doorless rooms, 60 unreached ground tiles of ~2 million, 44 bridges);
headless dummy (`/backrooms dummy place 52 5`, port 43125) lands at 565922,217,642274 with 0 error lines;
`GATE_TAG=52 python tools/gate.py --fast --port-base 43120` passes.

## Links (2026-10-31): the ways in and back

As LINKS.md settles it ("Level 52"): two ways in, both doors you open and walk through, so both two-way; the ways out are
those two, back. Code: `WorldLayout.Level52.Links.cs` (the entrances in the hosts, through the scaffold's `L52Entrances`
hook, and the campus doors that can lead back), `WorldGenerator.L52.Links.cs` (their blocks, `L52EntranceBlock`),
`ThresholdNetwork.L52.cs` (`L52Used`, `L52Walked`, `IntoL52Door`), `ThresholdSystem.L52.cs` (arrival facing, the dev test),
`Regions/L52Sun.cs` (`/backrooms l52 waytest`), assets in `tools/gen_52.py` / `gen_52_tex.py`. Unders 322-326, layout
salts 0x2380-0x2389, threshold salts 0x23C1-0x23C2.

### What was built
- **Level 11, a high school.** A city block of lots in midtown or the low-rise streets is drawn for one (1 in 640 by its
  hash, its own salt; 1 in 80 until the links tune of 2026-11-01); one of its street-front lots (an apartment block, an office or a shop, 14-30 wide, nothing else's
  on it, every cell it touches city and not the rim) is planned again over the top as a brick (red, dark) or stone
  building three or four storeys high, its outside walls kept where they were (corners, party walls) with no doors in
  them, sealed inside; in the middle of its front a pair of grey steel doors (`l52-door`, the End's exit door's shape,
  threshold kind `l52-door`) under a four-block HIGH SCHOOL sign (`l52-schoolsign`: cream letters on maroon in a brass
  frame). The host tiles stay walls. Rarity after the tune: 0.12 per km2 of city, about 1.75 km apart on average (`52links`), in line with the other
  levels' ways; the nearest to spawn are 49.8-51.2 km out (the city's near edge).
- **Level 4, an EMERGENCY EXIT door.** A cell drawn for one (1 in 500, its own salt; never two within 8 cells: the
  lower roll keeps it) puts it in a straight office wall (drywall; three wall tiles in a line, clear floor in front, and
  where the cell has one, nothing open behind): the same steel door, and over it at rel 3 a green EMERGENCY EXIT sign on
  the office wall (`l52-exitsign`). Level 4 is mostly open floor, so only about a quarter of the cells drawn have a wall
  for it: 0.49 per km2 of Level 4 (about five in the whole level in a full-size world); the nearest to spawn are 2.2, 2.7,
  3.8, 4.2 and 4.7 km out.
- **Arriving.** The school's doors put you just inside the front doors of a campus quad (its lobby), the exit door just
  inside the end doors of a standalone teaching block (its corridor), on Marshall David or a campus beside it (the lore:
  "each entrant will land in the same building or one nearby"), facing into the building as if just come through.
  Messages `l52-arrive-school`, `l52-arrive-exit`.
- **Back.** Those campus doors (`Unders.L52QuadDoor`, `L52WingDoor`, marked on every campus by `L52MarkWaysBack`) lead
  anywhere only once something came in by them: walk out through them and you are back where you stood when you opened
  the school's or the office's door (`l52-back-city`, `l52-back-office`). Every other door is only a door.
- **Rumours** (handbook, notes): a door on almost any level, a lift in Levels 1-4; out, a door to Level 53 now and then,
  noclipping in Marshall David to Level 556.
- **Text.** Handbook "Ways in and out" rewritten (gen_guide.py); notes: `l52-7` "The doors you came in by" (Dez, in the
  level's track), and one each at the end of the hosts' tracks, `l52-in-11` "High school" (A.L.) and `l52-in-4`
  "Emergency exit" (Tom), added from the level's own block in gen_notes.py.
- **Harness.** `mapgen <seed> 16000 52links`: the five schools and exits nearest spawn (checked built), density in a
  121 x 151-block window of the city and over Level 4, Marshall David's way-back doors, ten arrivals by each way (all just
  inside one of those doors). **Showcase:** `way-in-school` (from across its street), `way-in-exit` (from the office floor),
  `way-back-quad` and `way-back-wing` (from just inside, looking out).
- **No placard**: Level 52 (danger 0) is not more dangerous than either host.

### Inventions (not in the lore)
The school's look (brick, three or four storeys, the maroon HIGH SCHOOL sign, steel doors); the exit door's green sign;
arriving inside the campus building rather than outside it; the quad's front doors for the city and a teaching block's
end doors for the emergency exit; Dez's, A.L.'s and Tom's notes.

### Rows for the guide's ways-between-levels table
| From | Threshold | To | Way back |
|---|---|---|---|
| Level 11 | A high school's pair of steel doors under HIGH SCHOOL (one city block in a hundred or so, midtown and the low-rise streets) | Level 52, just inside the front doors of a campus quad, on Marshall David Campus or one beside it | Those doors, back to the sidewalk in front of the school |
| Level 4 | A steel door under a green EMERGENCY EXIT sign in an office wall (rare) | Level 52, just inside the end doors of a teaching block | Those doors, back in front of the exit |

### Checks (links round)
- expclash clean; mod and mapgen 0 errors.
- layouthash with `BACKROOMS_NO_EXP_ENTRANCES=1`, versions 1 and 12: every line for levels 0-20 and the layout hash equal
  to main's. Without it only `world 777/16000 level 11` (and so the layout hash) moves, in both versions (the hosts'
  other sample cells hold no school or exit).
- `regions`: 60/60 for Level 52. `52links` OK.
- Headless (port 43121, seed 12345, full size): `/backrooms l52 waytest school` and `waytest exit` (the school and the exit
  nearest spawn): the school's column is `citypier-brickdark / l52-door-lower / l52-door-upper / l52-schoolsign-1-north`,
  the exit's `officecarpet-plain / l52-door-lower / l52-door-upper / l52-exitsign-east`; each leads just inside a campus
  door (a quad's lobby, zone 16; a teaching block's corridor, zone 13: `l52-slab-hall`, air above), and walking out
  through that door (an open doorway) leads back to where the opener stood, in front of the school / the exit
  (`l52-back-city`, `l52-back-office`). Dummy in Level 52 lands; `blocksweep` 11181 blocks, 0 threw; 0 error lines.
- `GATE_TAG=52 python tools/gate.py --fast --port-base 43120`: PASS.

## Round 3 (2026-11-01): the detailed visual pass

Looked at first: round 2's final sheet (`%TEMP%/backrooms-shots/final-r2/sheets/52.jpg`), the lead's notes for Level 52, the
brief, DECISIONS.md, this plan's open points, and the released levels with the same kind of place (Level 11's stores and
signs, Level 5's lobby, Level 4's offices, Level 188's street furniture).

**Signs and the lore.** The lore says a door's sign carries four digits and "no subject and no campus name" anywhere. So
this round's text keeps to what that allows: numbers (building numbers over the entrances, floor numbers in the
stairwells, room ranges on the directories), the words any building has (EXIT, STAIRS, the restroom pictograms, NO
RUNNING), and the people's own signs, which the lore names: the M.E.G.'s outpost, Cool Mart Co. at J. Barry, the
abandoned bases' boards, and the M.E.G.'s stencilled boards giving the three named campuses their names at their gates
(the names are the M.E.G.'s, not the buildings'). No subject over a classroom door, no name cast into a building.

### List
Tiers: A must, B should, C nice. Ticks: `[done]`, `[partly: ...]`, `[skipped: why]`.

**1. Layout realism**
1. (A) Rooms by function in the quad: a front office (reception counter, waiting chairs, the principal's office behind) beside the main lobby on the ground floor. [done] (`L52AssignRoles`: the rooms nearest the lobbies are the front office, the principal's office, the staff room, the library)
2. (A) Restrooms by every stairwell (a pair per storey: stalls with partitions, toilets, a row of basins) instead of a classroom. [done] (the rooms nearest each stairwell's two doors, on every storey; stalls, basins, mirrors, a poster)
3. (A) A real library: the biggest ground-storey room of a block, rows of shelving, reading tables with chairs, a circulation desk. [done] (stacks on one side, reading tables and chairs, an issue desk; nearest the fourth lobby, 50 tiles or more)
4. (A) A staff room on each building's ground storey (sofa, coffee table, kitchenette counter, fridge, a table and chairs). [done] (one a building, nearest a lobby or door)
5. (A) The gym with changing rooms walled off at one end (benches, lockers, two doors) and bleachers along a long side. [done] (`L52LayChanging`: a cross wall nine in, a passage from the end door, lockers, benches, pictograms; two rows of bleachers on the far long side)
6. (A) Paths that lead between entrances and the fence gaps (a walk joining every building's doors), not only straight out across the lawns. [done] (an L-shaped walk three wide from each building's nearest door to the quad's nearest)
7. (A) A sports field with goals inside a running track on campuses with the room for one. [done] (`L52LayPitch`: where a plot has 62 x 44 left; a track, lines, goals, a three-row stand)
8. (B) A lecture theatre: a hall building with raked rows of seats facing a long board. [done] (`L52LayLecture`: a two-storey hall, doors at the front, tiers of desks to five up, stairs up both aisles; 28 in `52stats 4`)
9. (B) Labs grouped on one storey with benches along both walls and fume hoods. [done] (a lab storey in buildings of three or more; fume hoods)
10. (B) An outdoor seating area by the canteen (tables, chairs, benches) and a canteen serving line. [partly: café tables outside the canteens; the food stands were already the serving line]
11. (B) Lodging blocks: a desk and a chair in each room, a shared washroom on each floor. [partly: a desk and chair in each room; the washrooms are the restrooms by the stairs]
12. (C) Courtyard trees off their visible grid. [done] (`L52TreeSpot`)

**2. Multi-block objects**
13. (A) Roofs: air-handling units (several blocks, fan grilles), a stair bulkhead with a roof door over each stairwell, vents. [done] (`L52LayRoofs`)
14. (A) A clock tower on Marshall David's quad (and on some other quads): a square tower over the roofline, a clock face on each side. [done] (`L52LayTower`: Marshall David always, about one other quad in three; clocks stopped at 3:52)
15. (A) A fountain in the middle of a courtyard without a court (a stone basin with water, a jet column). [done] (`L52LayFountain`)
16. (A) Flagpoles in front of the quad's main entrance (pole, base, flag at the top). [done] (`L52LayFlags`)
17. (A) A campus map board at the main gap of every campus (a framed board on two posts). [done] (at every wide gap, beside the path in)
18. (B) Bleachers (stepped rows) by the J. Turner court and the sports field. [done] (two rows by every court, three by every pitch)
19. (B) The trophy case in the quad's lobby (glass case on a plinth) and benches. [partly: two trophy cases across the corridor from each front door whose lobby stops there; no bench]
20. (B) Elevator doors (closed: the lore has lifts; stairs carry people) beside the quad's first stairwell, a call button and a floor indicator. [done] (lift doors and an unlit floor indicator by the quad's first stairwell, every storey)
21. (B) A car park outside each named campus's main gap (paved bays, painted lines, a few cars) and a bus shelter by the road. [done] (a car park where a plot has no room for a pitch: two rows of bays, lines, a few of the mod's cars; a bus shelter by each east road)
22. (B) Glazed courtyard roof on some quads (the lore's "translucent ceiling"). [done] (about one ordinary quad in three without a court)
23. (C) Bike racks and planters by the entrances. [partly: bike racks along the wall beside teaching and lodging blocks' doors; no planters]

**3. Signs and text**
24. (A) EXIT signs over every outside door and every stairwell door, inside. [done]
25. (A) Building numbers over the entrances (big numerals on the canopy fascia). [done] (the building's number on the front of every canopy)
26. (A) Floor numbers in the stairwells (painted on the landing walls) and a floor directory beside each stairwell door (FLOOR n, the room ranges, arrows). [done] (floor number on the first landing; the directory gives the floor, which way the stairs go, the way out)
27. (A) Restroom signs (pictograms) by their doors. [done]
28. (A) The M.E.G. outpost's own sign at Marshall David's top floor (and its barrier notice), the M.E.G.'s placard conventions. [partly: the M.E.G. OUTPOST sign by the stairwells on Marshall David's top floor; no barrier (item 41)]
29. (A) J. Barry's warehouse sign (COOL MART CO.) over its doors, and its alarm bells. [done] (COOL MART CO. over the warehouse's doors; red alarm bells along J. Barry's corridors)
30. (A) The named campuses' names at their main gaps (the M.E.G.'s stencilled boards). [done]
31. (B) Notice boards along the corridors (cork, pinned sheets) and posters (NO RUNNING, a fire plan). [done]
32. (B) The abandoned bases' boards (Base Sunfire, Emberwatch, Blackcross) on a few ordinary campuses, with what they left (crates, a tent, a barricade). [done] (about one ordinary campus in six: the board at the main gap, a tent, crates, a pallet, a burn barrel, a lantern)
33. (C) A wall clock over each chalkboard. [partly: a wall clock over every room's door, inside (over the board there is no room under the ceiling)]

**4. Detail visuals**
34. (A) Break the locker runs: fire-hose cabinets, extinguishers, notice boards, doors, bins (the lead's note). [done] (`L52LayCorridorFittings`: every 19 blocks along a wall, a hose cabinet with an extinguisher, a notice board, a poster)
35. (A) Marshall David worn, as the lore has it: dirt prints and cracks in its corridors' floor, rubbish here and there. [done] (worn tile in patches, bin bags and boxes)
36. (B) Hedges along the quad's front and the main walk. [done] (`L52LayHedges`: a step beyond the quad's paving, broken at every path)
37. (B) Door leaves standing open against the wall beside classroom doors (wood with a narrow window). [done] (about two rooms in three)
38. (B) The lobby's floor: an entrance mat inside each outside door, a different floor from the corridors. [done] (a ribbed entrance mat on the two tiles inside every outside door)
39. (C) Fresh paint patches over the Crash's bullet holes at J. Barry (the aftermath text). [done] (`l52-wallpatch`, about one wall block in sixteen along J. Barry's corridors)

**5. Lore alignment**
40. (A) Classrooms stay identical and dark (the lore); the new room kinds take the places the lore lists (offices, faculty rooms, labs, libraries, utility rooms). [done] (classrooms untouched; the new kinds take the places of classrooms, as the lore's room list)
41. (B) The M.E.G.'s locked top floor: a barrier at the top flight with its notice ("outsiders are sent back a floor"). [skipped: the sign says it; a barrier would shut the M.E.G.'s floor the showcase needs]
42. (C) The roof's view: the campus below reads from the roof (a lower parapet on the roof-door side). [partly: the bulkheads and units now give the roof something to see; the parapet unchanged]

**6. Released-level alignment**
43. (A) Block names in the HUD for every new block (lang), pick-block works, sounds by material. [done] (en.json names; materials and sounds per block)
44. (A) Showcase spots for every new set piece, computed from the layout. [done] (13 new spots: front office, restroom, library, staff room, lab, stair hall, gym, lecture theatre, clock tower, gate boards, abandoned base, pitch, J. Barry's sign; two link spots dropped)
45. (B) The handbook page and notes mention the new sights where the lore has them (the M.E.G.'s sign, Cool Mart Co.). [done] (the handbook page: building and floor numbers, restrooms by the stairs, the M.E.G.'s sign, the tower clock, COOL MART CO., the alarm bells, the bases' boards)

Beyond the list (seen in run 1): the quad's ways in get a glazed bay the height of the building (not at Marshall David,
all white concrete by the lore); outside walls show the room's paint on their inward face (before, brick or façade
panels showed inside the rooms and halls).

### How it is built
- `WorldLayout.Level52.Detail.cs` (new): the room roles (`L52AssignRoles`, from `L52Partition`), and every fitting laid once
  per campus plan by `L52LayDetails` (before the grounds are furnished). A fitting (`L52Fixture`) is a block code at a
  height on a campus tile: `rel` above the floor, or the height in every storey; outdoors the height above the ground.
  The generator looks a tile's fittings up first (`L52FixtureAt`; `=water`, `=hedge`, `=stair-<side>` are the vanilla
  blocks). So the tower, the bulkheads, the air handlers, the lecture theatres' tiers, the boards, flags, goals and the
  stand are blocks laid by the plan, seed-independent, and the same in the harness.
- `tools/gen_52_r3.py` (new, called from `gen_52.py`): `l52-sign-{kind}-{side}` (61 kinds of plate or fitting hung on the
  wall behind its block; text drawn into the textures at 64 px a block, reading left to right from in front; signs two or
  three blocks wide are cut at the seam), `l52-stall`, `l52-fumehood`, `l52-bleacher`, `l52-goal`, `l52-flagpole`,
  `l52-post` (boards on two posts: the map, the M.E.G.'s campus names, the bases), `l52-jet`, `l52-vent`, `l52-hvac`,
  `l52-track`, `l52-skylight`, `l52-bikerack`; new slab kinds `worn` and `mat`; turf with pitch lines.
- Values (Level 52's blocks): `FloorKind` 335-341, `Props` 1103-1105. Lang: block names in Level 52's block of en.json.

### Inventions (round 3; not in the lore)
The room roles' places (restrooms by the stairs, the front office by the lobby); the signs' wording beyond the lore's
plaques (EXIT, FLOOR n, the directory, the posters, NO RUNNING, FIRE EXIT PLAN, WASH YOUR HANDS, QUIET PLEASE); the M.E.G.
OUTPOST sign's wording ("visitors report to floor below", after the brief's note idea); the M.E.G.'s boards naming the
three campuses at their gaps; COOL MART CO.'s sign (the lore names the trader, not the sign); the abandoned bases'
boards and camps (the lore names the bases, not where they stood); the clock tower and its stopped clocks; the courtyard
fountain; the flagpoles and their nameless flag; the campus maps; the lecture theatres (the lore's campus houses "a
university"); the pitch and running track; the bleachers; the glazed bays and courtyard roofs (the lore allows "a
translucent ceiling" over a courtyard); the bus shelters; the trophy cases, hedges, bike racks, entrance mats, café
tables; the lifts' doors (the lore has lifts; these do not run).

### Balance notes for the lead
- No new food, water or loot source: the restrooms' basins, the staff rooms' kitchenettes and fridges, the trophy
  cases and the reception desks are scenery (no dispenser, no container). The canteens, fountains, vending machines and
  supply boxes are as they were.
- More desks and filing cabinets (front offices, staff rooms, lodging rooms' desks, lecture theatres' lecterns): if
  notes are rolled per desk or cabinet, a little more note-finding on Level 52.
- No new beds (the lodging rooms' beds were there). No shortcut, no threshold, no safe room beyond the level's own Safe.
- The lecture theatres' tiers and the stands are climbed with jumps or the aisle stairs; no fall higher than five.

### What the shots showed
- **Run 1** (`%TEMP%/backrooms-shots/52-20261101-014255`, `sheet.jpg`): the new rooms read as what they are (front office
  counter, restroom stalls and basins, library stacks and reading tables, staff room, lab with fume hoods, the lecture
  theatre's tiers, the gym's bleachers and changing-room doors with their pictograms); the corridor's hose cabinets and
  notice boards break the lockers; floor numbers in the stairwells; the clock tower over Marshall David's corner; the
  campus map and the M.E.G.'s MARSHALL DAVID CAMPUS board at the gate; Base Sunfire's board and camp; the pitch with its
  track, goal and stand; hedges, bike racks, door leaves and wall clocks seen through the windows; building numbers on
  the canopies. Wrong: two EXIT signs (and two numbers) over a three-wide door; openings over the changing rooms' doors
  at the gym's upper level and notice boards on its walls; the entrance spot looked into the back of the campus map; the
  roof spot looked at the parapet; J. Barry's sign spot stood in the fence; the roof membrane too speckled; the courtyard
  crowded with trees. All fixed for run 2.
- **Run 2** (`%TEMP%/backrooms-shots/52-r3b`, `sheet.jpg`): one EXIT and one number over each run of doors; the
  entrance with its canopy number, hedges and bike racks; the fountain with its water; the roof with a stair bulkhead
  and its door, vents and air handlers on a calmer membrane; the stair hall (EXIT over the stairwell doors, the lift, the
  FLOOR 1 directory, a notice board); the car park with the mod's cars; the gym's upper walls closed. Wrong: COOL MART
  CO. stood on the façade just over the canopy, where the canopy hid it from the ground (the dump showed the block
  there): moved onto the canopy's front. Seen but left: the random arrivals (the rig's own camera) face a wall now and
  then; the tower spot looks steeply up.
- **Run 3, final** (`%TEMP%/backrooms-shots/52-r3c`, `sheet.jpg`): COOL MART CO. across the warehouse's canopy; everything
  else as run 2. Tally of the list: A 23 done, 1 partly (the M.E.G.'s barrier); B 12 done, 3 partly, 1 skipped; C 2 done,
  3 partly.
- **Still weak:** the random arrivals' framing (the rig's camera, not the level's facing); the hall buildings' upper
  string course shows inside the two-storey halls; the toilets are simple shapes; the courtyard spot still looks into
  the trees; the sky sphere's seam shows over the open pitch.

### Checks (round 3)
- `python tools/expclash.py`: clean. Mod and mapgen build with 0 errors.
- layouthash (`BACKROOMS_NO_EXP_ENTRANCES=1`, versions 1 and 12): every line for levels 0-20 and the layout hash equal to
  main's saved files (only the experimental levels' lines differ).
- `regions`: 60/60 for Level 52, none wrong or in pockets. `52stats 4`: 68 campuses, 305 buildings (28 lecture theatres),
  0 doorless rooms, 121 of about 1.95 million ground tiles unreached (single tiles boxed in by furniture), arrivals 60/60.
- Headless (port 43128): `blocksweep` 12088 blocks, 0 threw; 0 missing blocks or items; `/backrooms dummy place 52 5`
  lands at 565923,217,642303 with 0 error lines; `/backrooms showcase 52` lists every spot.
- `GATE_TAG=52 python tools/gate.py --fast --port-base 43120`: PASS (generators, lang, build, boot, harness).

### Balance, layout 16 (0.700.0-pre.11)

Level 52 is a safe level with a lot of green, so its trees were cut (every world, `ExpVersion` 16): hill trees from 7 % to
1.4 % of squares (a fifth), the quad courtyards' trees from 50 % to 10 % of spots with a 45 % chance of a shrub in the
place of a tree, lawn trees from 0.4 % to 0.08 % with shrubs 0.2 % (`WorldLayout.Level52.cs`). The courtyards no longer
crowd their lawns. Its snack machines never restock and its food props are found stripped (feedback-2026-11/README.md).

### Questions for the user
1. **Names on the buildings.** The lore says the doors carry four digits and "no subject and no campus name" anywhere,
   so the buildings show their numbers (on the canopies) and the campuses' names appear only on the M.E.G.'s boards at
   three gates. Should campuses (or buildings) have names cast over their doors anyway, as real schools do?
2. **The clock tower, lecture theatres, pitch, car parks and bus shelters** are inventions for a campus that "houses a
   university"; keep them all, or trim any that feel too much like a real campus and not enough like the Backrooms?
3. **The lifts** are closed doors (the lore has lifts; DECISIONS says stairs first). Should they ever open?


## Round 4 (2026-11-02): the asset-quality pass

Looked at first: round 3's final sheet (`%TEMP%/backrooms-shots/final-r3/52/sheet.jpg`), the lead's round-4 notes, the
"Still weak" of round 3, the brief and DECISIONS.md, and the props that set the bar (188's street furniture, the detail
kit, 15's lab benches and seats, 31's lockers and trophy case, 14's hospital kit). Nearly every Level 52 shape was 1-5
boxes (a plate with a picture); the gym showed no hoop at all from its spot (the shared `basketballhoop` is one block with
a 12-px board). Lore guard rails kept: digits-only signage (names only on the M.E.G.'s boards), classrooms dark with
their electrical gear off, libraries and labs "vacant and missing contents".

### List
Tiers: A must, B should, C nice. Ticks: `[done]`, `[partly: ...]`, `[skipped: why]`.

**1. Assets to rebuild to the bar**
1. (A) `l52-desk` (student desk-and-chair, classrooms and lecture tiers): tube frame, moulded seat and back, desktop with lip, book rack under, glides. [done] (32 boxes: tube frame on glides, laminate top at 0.76 with edge band and pencil groove, book box, moulded seat at 0.5)
2. (A) `l52-chalkboard-*` (keep the codes: the coloured-chalk system uses them): aluminium frame, chalk tray with chalk and a felt eraser, map rail on top, a board surface with ghosts of old writing. [done] (aluminium frame, chalk tray with sticks and an eraser, map rail with clips, a map roller case; the slate one 3x2 picture with eraser swirls and ghost sums; chalk drops kept in the generator)
3. (A) `l52-locker-*` lockers: a JSON front in relief (door panels inset, louvre vents, a handle and a dial lock, number plates, hinges, kick base); the odd door ajar. [done] (JSON in relief: doors, latches, louvres, vents, number plates, hinges, top trim; `l52-lockerajar-*` with the middle door open on about one bank in fourteen)
4. (A) `l52-fountain` drinking fountain: a stainless wall basin on a back plate, bubbler, push bar, drain, a refill spout. [done] (44 boxes: splash plate, stepped bowl, bubbler and guard, push bar, trap into the wall, bottle filler)
5. (A) `l52-bleacher` (gym and courts): seat planks with gaps, foot planks, risers, aisle steps and a frame of uprights and braces; an end rail. [done] (seat boards, foot planks, kick plate, steel frames with diagonals and gussets)
6. (A) `l52-sign-hose` / `l52-sign-ext` fire hose cabinet and extinguisher: a recessed cabinet with a glazed door and a coiled hose on a reel; the extinguisher on its bracket (or the shared ones if they meet the bar). [done] (the shared detail hose cabinet and extinguisher, without their wall cube, as Level 52's wall fittings; the reel rebuilt as a drum with coils)
7. (A) `l52-sign-exit` EXIT: a lit box with a canopy mount (or the shared EXIT sign if it meets the bar; same vocabulary as the released levels). [done] (replaced by the mod's own hanging EXIT sign, `exithanging-*`, under the ceiling in front of the door: the released levels' vocabulary)
8. (A) `l52-window-*`: frames, mullions, a transom, sill and the glass set in, not a pane with lines drawn on it. [done] (jambs, mullion, transom, beads, sill with drip ledge and window board, latches)
9. (B) `l52-stall-*` restroom stall: a real pan (bowl, seat and lid), a flush valve, the partition with its door, hinges and latch, chrome feet. [done] (stepped pan, open seat, lid up, chrome flushometer, partition off the floor with shoe, roll holder, headrail, coat hook)
10. (B) `l52-fumehood-*` fume hood: framed sash with a handle, baffle slots, cabinet doors with handles, a gas tap and the airflow gauge. [done]
11. (B) `l52-sign-notice-*` notice boards: aluminium frame, cork, pinned sheets as raised layers, pins. [done]
12. (B) `l52-sign-wallclock` and the tower's dials: a round body with a bezel and the hands as elements. [done] (the wall clock: bezel, hands at 3:52, red second hand; the tower's dials: a stone surround and bezel ring across the nine pieces, raised batons and hands)
13. (B) `l52-goal-*` football goal: round-section posts (bevelled), stanchions and the ground frame behind, a net with depth. [done]
14. (B) `l52-flagpole-*`: a plinth with a plaque, the pole's taper, a cleat and halyard, the flag cloth in folds (rotated elements). [done]
15. (B) `l52-post-*` boards on posts: posts with caps and feet, a framed board with a canopy and bolts. [done]
16. (B) `l52-vent` / `l52-hvac-*` roof plant: a gooseneck/mushroom vent; air handlers as one unit with louvres, fan shroud, access panels and a duct into the roof. [done] (the vent: a mushroom cap on a flashed curb; the air handlers in relief: louvres, posts, the fan shroud and grille)
17. (C) `l52-jet` / courtyard fountain: a tiered bowl on a fluted column, the basin rim with coping. [done] (`l52-jet` rebuilt; `l52-basinrim-{edge,corner}-*`: a coped precast rim, wet and green at the water line inside)
18. (C) `l52-bikerack-*`: fine as it is (16 boxes); leave. [skipped: already at the bar]

**2. Multi-block set pieces**
19. (A) **Basketball hoop, outdoor** (courtyard courts, J. Turner): a padded steel post on a base plate, a gooseneck arm, the backboard (1.8 blocks wide, its bottom padded, the shooter's square), the rim at 3 blocks with its bracket, the net hanging into the air block in front. Several blocks that read as one. [done] (`l52-hoop-pole-*`, `-board-yard`, `-rim-yard`: weathered green post on a base plate with gussets and a pad, parallel arms, a rust-streaked board, rim and torn net in front)
20. (A) **Basketball hoop, gym**: wall-mounted on the end wall with a braced truss out to the board, the same board, rim and net; wall mats under it. [done] (`l52-hoop-truss-*`, `-brace`, `-board-gym`, `-rim-gym`: a three-block braced truss off the end wall, orange-framed board with a bottom pad)
21. (A) Court markings: the key (painted lane), free-throw line and circle, the three-point arc and the centre circle, as flat decals on the court and on the gym floor. [done] (`l52-mark-{gym,yard}-*`: 82 cells about each hoop and the centre circle, painted key)
22. (A) The gym's scoreboard on the long wall (lit digits, HOME / GUEST, PERIOD) and wall mats along the end walls. [done] (`l52-score-*`, lit, HOME 00 GUEST 00, clock 3:52; `l52-wallmat-*` either side of each hoop)
23. (A) The outside courts fenced: chain-link round the courtyard court with a gap for the path. [done] (chain-link two tiles out, gaps mid-side)
24. (B) The lecture theatre's seats: flip seats with a writing tablet on the arm, in rows on the tiers. [done] (`l52-lseat-*` on the tiers instead of the desks)
25. (B) A ceiling projector in classrooms (off, as the lore's dark classrooms) on a drop pole, and a pull-down screen case over the board. [partly: `l52-projector-*` in every classroom, off; no pull-down screen case (the map roller on the board stands in)]
26. (B) A dugout at the pitch: a bench under a curved shelter with a back wall. [done] (`l52-dugout-*` either side of the stand)
27. (B) Entrance canopies with columns at their front corners. [done] (`l52-column-*` under the outer corners; `l52-planter` beside each canopy)
28. (B) Stairwell handrails along the flights (a rail on posts), the treads' nosings. [done] (`l52-stairrail-{l,r}-*`: a steel rail at 45 degrees on brackets and rosettes, on the walls beside both flights, laid per storey in `L52LayStair`; nosings not done)
29. (C) The trophy case rebuilt: glass, shelves, trophies (cups, a plate, a ball) and a light. [done] (`l52-trophy-*`, glass, cups, figures, medals, a lit header)
30. (C) The library: a rolling ladder on the stacks; a few books left on the shelves (the lore's rooms are "vacant and missing contents", so a handful, not full shelves). [partly: the rolling ladder (`l52-ladder-*`, Props.L52Ladder); shelves stay empty (the lore)]

**3. Level design**
31. (A) The gym reads as a gym from its spot: hoops at both ends, the scoreboard, mats, the key on the floor, the bleachers. [done] (run 1: `gym` and `gym-hoop`; the façade's grey over the end doors now the room's paint inside)
32. (A) The courtyard court as the heart of J. Turner (lore: "basketball court and courtyard at the core"): fenced, marked, hoops facing. [done] (fence with a post every third block, like the campus fences now)
33. (B) The two-storey halls' upper string course showing inside (round 3's Still weak). [done] (no band at a hall's middle line; the room's paint inside)
34. (B) The courtyard spot looks into the trees (round 3's Still weak): move the spot. [done] (from a corner along the diagonal)
35. (B) The sky sphere's seam over the open pitch (round 3's Still weak): look at the sphere's radius against the view. [done] (it was the game's cloud layer meeting the sky sphere as white slabs: Level 52's clouds are off)
36. (C) The roof: gravel patches by the plant, parapet caps. [partly: gravel patches; the parapets as they were]

**4. Lore**
37. (A) Keep digits-only signage: the scoreboard and court use numbers and generic words (HOME, GUEST), no campus or school names. [done]
38. (B) Classrooms' 2000s audiovisual gear: the projector (item 25) and the corner TV on its wall bracket or cart (shared `Tv` today). [done] (the projector; the corner TV now a CRT strapped on an AV cart with a VCR, `l52-tvcart-*`, off; a poster on the back wall of half the classrooms)
39. (C) The M.E.G.'s presence on the top floor: their placards (shared `megplacard`) by the outpost sign. [skipped: time]

**5. Alignment with the other levels**
40. (A) Shared EXIT signs, extinguishers and hose cabinets: use the mod's own where they meet the bar, else write them under "Shared assets below the bar" and keep ours. [done] (EXIT the shared hanging sign; hose cabinet and extinguisher are the shared detail shapes without their wall cube)
41. (B) Lab benches: from `l15-labbench-sink` (Level 15), retinted to the campus's grey-white resin and steel (similar but unique: Level 15 is clean futurist white). [done] (`l52-labbench-{plain,sink,gas}`, Props.L52LabBench, instead of kitchen counters: Level 15's are 6-box blocks, so ours are new, grey cupboards and black epoxy)
42. (B) Lockers: compared with `l15-locker-*` (ajar) and Level 31's; ours stay the campus's palette. [done]
43. (B) Lecture seats: compared with `l15-seat-*` and Level 36's seat rows; ours a timber-and-steel flip seat with a tablet. [done]
44. (A) Showcase spots and F7 entries for the new set pieces (gym hoop, court hoop, scoreboard, dugout); `featurecheck`. [done] (`gym-hoop`, `court-hoop`; F7 `l52court`)
45. (B) Block names in en.json (Level 52's block) for every new code; pick-block; sounds by material. [done]

### How it is built (round 4)
- `tools/gen_52_r4.py` (new, called from `gen_52.py` after round 3): the hoops (`l52-hoop-{piece}-{side}`: pole-base/mid/neck/top,
  board-yard, rim-yard; truss-wall, truss-mid, brace, board-gym, rim-gym), the court decals (`l52-mark-{gym,yard}-{cell}-{side}`, one
  flat shape, the texture by type; the cells drawn from the court's geometry at 32 px a block), the scoreboard, wall mats, the
  lockers in relief (they replace round 1's cube lockers under the same codes, plus `l52-lockerajar-*`), and the blocktypes of the
  kit's new pieces. `tools/gen_52_r4_kit.py` (new; built by an Opus model worker to this round's bar and checked in
  `preview_shapes.py` renders and `check_zfight`): 91 shapes and 139 `r4k-*` textures that override round 1-3's shapes of the same
  names (desk, chalkboard, fountain, windows, stall, fume hood, bleacher, goal, flagpole, boards on posts, hose cabinet,
  extinguisher, notice board, wall clock, mirror, pictograms, the tower dials, roof vent, air handler) and the new pieces
  (lecture seat, projector, trophy case, dugout, canopy column, ladder, planter, lab benches).
- The coloured-chalk drops (a2b5a948 edited the generated desk and chalkboard JSON by hand) are now written by `gen_52.py`
  (`chalk_drops`), so regenerating keeps them.
- Layout: `WorldLayout.Level52.Courts.cs` (new): `L52LayHoop`, `L52LayMarks`, `L52LayCentreCircle`, `L52LayYardCourt` (the
  courtyard court's hoops, markings and fence), `L52LayGym` (hoops off the end walls, markings, mats, the scoreboard on a long wall
  with no window behind it), `L52LayProjectors` (and the classroom posters), `L52LayCanopyColumns` (and the planters). In
  `Detail.cs`: the EXIT signs are the shared `exithanging-*` (`L52Exit`), the trophy cases, the pitch's dugouts, the lecture seats.
  In `WorldLayout.Level52.cs`: the library ladder (`Props.L52Ladder` 1106), the lab benches (`Props.L52LabBench` 1107), the gym's
  old one-block hoops gone. In `WorldGenerator.L52.cs`: the ajar lockers (7%, the same on both halves), no string course inside a
  two-storey hall, the ladder and lab bench props.

### Inventions (round 4; not in the lore)
The hoops' make (a weathered green post with parallel arms outdoors, a wall truss in the gym), the court markings' colours
(a stained key in the gym, a green key on the red courts), the fence round the courtyard courts, the scoreboard (HOME/GUEST at
00, its clock stopped at 3:52 like the tower's), the wall mats, the dugouts, the canopy columns and planters, the trophy
case's contents, the library's rolling ladder, the classroom projectors (the lore's "audiovisual gear, mostly 2000s"), the
classroom posters, the lab benches' gas taps and eyewash, a locker door left open now and then, the stair handrails.

### Shared assets below the bar
- `exithanging` (the shared EXIT sign, 5 boxes): now used on Level 52 too; a frame with a canopy mount and a lit diffuser
  would lift it everywhere.
- `detail/basketballhoop` (one block, a 12-unit board on a 3-block pole): Level 52 no longer uses it; if other levels do, the
  `l52-hoop-*` pieces (yard set) could replace it.
- The detail kit's `foldingtable`/`foldingchair`, `officechair`, `desk`, `bench`, `streetlight` and `tv` (Level 52's canteen,
  offices, courtyards, classrooms' corner TV) are 6-15 boxes; they read, but sit below the new Level 52 pieces up close.
- `l15-labbench-*` (6 boxes each) and `l31-trophycase` (box trophies, no glass): Level 52 made its own instead of reusing them;
  the lead may want 15 and 31 to borrow `l52-labbench-*` / `l52-trophy-*` (retinted) or have them rebuilt.

### Balance notes for the lead
- No new food, water or loot source: the lab sinks, eyewash, trophy case, planters and dugouts are scenery; the drinking
  fountain is rebuilt but still the same block (it dispenses as before). Ajar lockers are scenery (lockers were never containers).
- The desk and chalkboard keep their coloured-chalk drops (now written by the generator).
- The library ladder is climbable (a way onto the bookstacks' tops; no new place reached). No shortcut, threshold or safe room.

Beyond the list (from run 1): the libraries' stacks were the shared office bookshelf seen from behind as blank slabs: now
double-sided steel bookstacks (`l52-stack-{a,b}-*`, Props.L52Stack 1108), near bare with dust marks where the books stood; the
front office's and library's counter was the hotel reception desk with WELCOME on it (words the lore does not allow): now
`l52-counter-*`; the chain-link fences (campus and courts) get a galvanised post every third block (`l52-chainpost-*`); flat roofs
get ballast gravel in patches (`l52-roofgravel`; item 36 after all); the gym's scoreboard, which found no window-free stretch of
long wall, falls back to the changing rooms' cross wall beside the hoop (then over windows); a hall's interior walls are plain
upper paint on their upper storey (the cross wall showed a second skirting band at the hoop's height); the canteens' folding
tables and chairs became long folding lunch tables with their benches (`l52-lunch-{table,seat}-*`, Props.L52LunchTable 1109,
L52LunchSeat 1110).

### What the shots showed
- **Run 1** (`%TEMP%/backrooms-shots/52-r4a`, `sheet.jpg`): the gym hoop (truss, orange-framed board with its pad, rim and
  net, wall mats, the painted key) and the court hoop (green post with its pad, rusty board, torn net, the fence, the green key on
  the red court) read as the real things; lockers in relief with a door open; the classroom's desks, board, projector and wall
  clock; stair handrails; the hanging EXIT signs; lab benches and fume hoods; lecture seats; restroom stalls; columns and a planter
  at the entrance; the dugout by the pitch. Wrong: the library's stacks (blank slabs: shared bookshelves seen from behind) and the
  ladder standing clear of them; WELCOME on the front office counter; white cloud slabs over open views; the façade's grey
  showing inside the gym over its end doors; the courtyard spot behind a lamp post; the pitch spot looking at empty turf.
- **Run 2** (`%TEMP%/backrooms-shots/52-r4b`, `sheet.jpg`): the library's double-sided stacks with their few leftover books and
  the ladder against them; the school counter (but its bell repeated on every block: now three variants); the trophy case in
  Marshall David's worn lobby; the gym's scoreboard on the changing rooms' cross wall over the far hoop; the fence posts; the
  pitch's goal with its net; the clouds gone (no more slabs in the sky). Wrong: the roof gravel's 8-block patches read as a
  patchwork (now gravel all over, membrane walkways every eleventh block); two random arrivals stood inside a lawn tree's crown
  (arrivals now on paths and corridors only; `regions` still 60/60).

### Checks (round 4)
- `python tools/expclash.py`: clean. Mod and mapgen build with 0 errors. `gen_52.py` check: 2552 codes defined and expected, 0
  problems; `langcheck` clean.
- layouthash (`BACKROOMS_NO_EXP_ENTRANCES=1`, versions 1 and 12): every line for levels 0-20 and the layout hash equal to
  main's saved files.
- `regions`: 60/60 for Level 52, none wrong or in pockets (full size and `SPAWN=1000`). `52stats 4`: 68 campuses, 305 buildings,
  0 doorless rooms, 121 of about 1.94 million ground tiles unreached (single tiles boxed in by furniture), arrivals 60/60.
  `featurecheck 2 52`: 17 of 17 features found from every arrival (the new `l52court`; `gym-hoop`, `court-hoop`, `trophy-case`
  spots in their entries).
- Headless (port 43128): `blocksweep` 16501 blocks, 0 threw; 0 missing blocks or items; `/backrooms dummy place 52 5` lands
  at 565925,217,642287 with 0 error lines; `/backrooms showcase 52` lists every spot. (Four earlier blocksweeps with this
  round's builds hit a crash in the game's own `Relight` thread (`ChunkIlluminator.UpdateLightAt`, a null light layer) while
  the sweep set and cleared 16,000 blocks in one tick; two later sweeps of the same builds and the final one passed, and
  swapping DLLs and assets between builds did not pin it on any block: a race in the engine under load, noted for the lead.)
- `GATE_TAG=52g python tools/gate.py --fast --port-base 43120`: PASS at 90db15a3 (generators, lang, build, boot, harness).

### Questions for the user

Answered 2026-11-14: see OPEN-QUESTIONS.md (this list and the earlier ones). Clouds stay off; arrivals stay on paths and corridors; libraries stay bare; no names over doors; lifts closed.
1. **Clouds.** Level 52's few white clouds are off: the game's cloud layer met the blue sky sphere as white slabs over every
   open view. The lore asks for "few clouds"; would you rather have them back (and the seam) or keep a clear sky?
2. **Arrivals** now land on paths and in ground-floor corridors only (never on a lawn, where one stood inside a tree's
   crown). Fine, or should some still land on the grass?
3. **The libraries** stay nearly bare (the lore: "vacant and missing contents"), with dust marks where the books stood and a
   few left behind. Should they hold more books, as a real school library would?
- **Run 3, final** (`%TEMP%/backrooms-shots/52-r4c`, `sheet.jpg`): the canteen's long lunch tables with their orange benches on
  folding frames; the classroom's CRT on its AV cart beside the teacher's desk; the courtyard fountain's coped rim; the roofs
  gravelled with membrane walkways; everything from run 2 as it was; the arrivals in corridors, at a window and on a path. The rig
  hit a `PermissionError` writing a file after the 30th spot, so `car-park`, `barry-sign`, `way-in-school` and `way-back-quad` are
  missing from this run (they are in run 2's folder and did not change). Tally of the list: A 18 done; B 20 done, 1 partly
  (the projector's screen case); C 2 done, 2 partly, 2 skipped (the bike rack already at the bar; the M.E.G. placards).
- **Still weak:** the shared props Level 52 still uses (folding chairs in some rooms, office chairs, the staff room's sofa,
  the street lights, benches and bins outdoors, the cars) are a step below the new pieces up close; the locker number plates
  read as dark dots; the stair treads have no nosings; the courtyard's trees crowded its lawns (fixed by the layout 16 tree balance, see "Balance, layout 16" below); the canteens' food stands
  are the shared snack counter.
