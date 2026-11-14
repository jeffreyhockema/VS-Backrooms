# Level 15 "Futuristic Halls": plan

Internal id **27**, `WorldLayout.Level15`, tag `15`, blocks `l15-`, method infix `L15`, region far north-west beyond the
End (`spawn + (-F, -F)`, Level 183's old slot), round, radius `max(40, spawnMacroX / 50)` (320 cells full size). Built and connected (see
Links). Reserved: `WallPattern`, `FloorKind`, `CeilingKind`, `Unders`, `Overheads`,
`Pipes`, `Decor` 448-479, `Props` 1300-1399, title keys 2701-2799, salts 0x2700-0x27BF (thresholds 0x27C0-0x27FF), ports
43160-43169. Lore brief: `lore/15-brief.md`; the user's decisions: `lore/DECISIONS.md` ("isolation and notes, no living
base; sparse Roboman and bones; star door as flavour").

## 1. What the lore says

Both wikis (Wikidot https://backrooms-wiki.wikidot.com/level-15, the French rewrite; Fandom
https://backrooms.fandom.com/wiki/Level_15, Class 1), reconciled as the brief proposes:
- A labyrinth of clean white "futuristic" halls: white or grey concrete, beams of white steel along walls and ceilings,
  large lights on walls, ceilings and the ground; ceramic floors, now and then carpet or a non-slip coating.
- A constant mechanical hum, engines far off, distant beeping; sound carries.
- Side rooms of machines behind heavy security gates (reinforced doors, a wall of thick glass), machines from laptop to
  monolith size, most dead or stripped; laboratories, storage, control rooms, dormitories, kitchens, a lecture hall.
- Lights fail; whole areas go pitch black (Fandom: CO2 rises, dizziness, a slowing heart there; the machines tick like a
  heartbeat that slows until the power returns).
- Computers and wall displays (Fandom: "Access denied: Level 5 clearance required to change reality"; panels showing
  Level 18 and the Storm Chaser; Wikidot: terminals running "Avalon 2.4" with a radar of the levels).
- Codes on the walls (Fandom: "H15", "eco3x10c" by the vents, H = lab, e = storage; black numbers on room walls) and
  symbols etched on the beams (Wikidot).
- Nothing native alive (both); resources scarce, Almond Water "notable by its absence".
- Wikidot: lab-coat corpses with makeshift knives and spears, gunshot wounds but no guns; abandoned camps; burnt Hounds in
  a crematorium; a doorframe in an empty machine room onto a night sky and a blue star, two hours from camp.
- Entrance (both): a small reinforced door in an immense white wall at the edge of Level 10's field, which later vanishes.

## 2. The level in this mod

**Layout** (`WorldLayout.Level15.cs`). Main halls every 128 blocks each way (x or z mod 128 in 1-5): five wide, five
high, a strip of LED panels down the middle (every sixth gives light, the rest only look lit), floor lights along the foot
of both walls, a white steel I-beam rib across the top every eight blocks with a pilaster under each end. Between four
halls a **wing**, 121 blocks square, planned once (`PlanCache`, `L15PlanOf`) by recursive cuts: each cut is a side
corridor (three wide, four high, panels every six, ribs every eight) or, from the third level of cuts, a service passage
(two wide between its own grey concrete walls, three high, grating floor, a duct along one side, caged lamps half dead,
air-handler grilles) running the whole width of the piece it splits, its ends opened onto the corridor or main hall beyond,
so every corridor connects. The pieces left are rooms with their own walls and one door (a second in a big room) onto a
corridor beside them or through the wing's wall onto a main hall. About 40 rooms a wing.

**Rooms** (kind by size; the window of 81 wings round the middle: machine rooms 24%, stores 20%, bare rooms 16%, labs 12%,
control rooms 9%, kitchens 7%, wrecked machine rooms 5%, dormitories 4%, lecture halls 2%, crematoria 1%):
- *Machine room* (tall, 5 or 7 high): a security gate (the shutter rolled up into the lintel, a tread plate, a dead hand
  scanner on one side, the room's code on the other) and thick glass (some cracked) along the door wall; a grid of
  machines with two-wide aisles, stacked from casing blocks (1x1 cabinets to 3x3 monoliths up to six high): dead (most),
  running (lit screens and lamp banks that hum, one in five where there is power), wrecked (burnt, top missing, the
  floor scorched); switchgear, gauges, generators and tanks along the walls; one room in five or six has a rod press
  feeding a conveyor to a heap of steel rods (Wikidot's working machine).
- *Wrecked machine room*: the same, nearly all burnt, scrap and machine parts strewn, lights mostly gone.
- *Laboratory*: rows of lab benches (plain, sink, instrument, glassware) with stools, cabinets; blood now and then.
- *Store*: rows of steel shelving, a few steel lockers (shut or ajar), boxes, crates, a sealed supply box in one in three.
- *Dormitory*: cots head to the wall, lockers, carpet.
- *Kitchen*: counters, a fridge, a stove, round tables and chairs; all stripped.
- *Control room*: rows of consoles (dead; ACCESS DENIED; the radar) with chairs, facing a wall of displays (the radar
  "AVALON 2.4", the ESCAPE panel, views of Level 18, a storm, the Lobby, dead screens).
- *Lecture hall*: a half-block stage along the front wall under a big display, rows of benches, an aisle.
- *Bare white room*: empty, or a pillar stub out of the floor, or a wooden door set in a wall (the oddities).
- *Crematorium* (rare): an incinerator against the back wall, bones and skulls over a sooty floor, lights mostly gone.
- *The star door*: one wing in about thirty past 55% of the radius gives its biggest room (14 square or more) to it: an
  empty, unlit, dusty machine room with a free-standing steel doorframe in the middle, a night sky and a blue star in it
  (glowing a little blue). Flavour only: it does not let you through.

Abandoned camps (a tent or a sleeping bag, a bag, chairs, boxes, a cold barrel, a supply box nearly always gone
through; a corpse one time in three; a loose note) in dormitories, bare rooms, stores and now and then elsewhere, 1.5 a
wing. The dead in lab coats (sitting against a wall, or lying across two blocks; one in three with a pipe-and-glass
spear; dried blood round them) about 4.7 a wing, a few in the main halls against the walls, with dropped bags and bones.
Steel beams set in at a wrong angle now and then in the halls and corridors (an oddity).

**The dark.** One 64-block square in about six (never within 160 blocks of the middle, so arrivals are lit) has no power:
every light dead (a few still stuttering), the floor lights dark, the machines stopped, consoles and displays dead. A room
is dark or lit as a whole (by its middle); corridors and halls by the square they are in. 14-16% of the level's tiles.

**Blocks** (`WorldGenerator.L15.cs`, `tools/gen_15.py`, textures `block/15/`): `l15-wall` (white panel, a variant with a
service plate, the skirting row's kick plate, bare grey concrete, scorched, white steel pilaster, etched pilaster),
`l15-walldeco` (one face dressed: scanner, display, radar, ESCAPE, three views, vent, vent with "eco3" scrawled, wooden
door lower and upper, blood, sixteen room codes "H15", "e03", "M12"... in tall black stencil), `l15-glass` (clear,
cracked; transparent), `l15-floor` (ceramic, worn, coating, carpet, grating, floor light lit-looking and dead, blood,
scorch, gate tread, dust), `l15-ceiling` (panel, LED on (light 18, cool white), lit-looking, failing (the mod's flicker
entity), dead, service concrete, air-handler grille), `l15-rib`, `l15-oddbeam`, `l15-gate`, `l15-machine` (twelve casing
faces), and JSON-shape props `l15-console`, `l15-labbench`, `l15-locker`, `l15-corpse`, `l15-rods`, `l15-stage`,
`l15-stardoor`. Reused: Level 1's shelving, crates, boxes, folding chairs, burn barrel, camps (tent, sleeping bag, bag),
Level 3's switchgear, gauges, generators, tanks and conveyor, Level 4's office chairs, filing cabinets, counters, fridge,
Level 6.1's stove, Level 7's bones and scrap, Level !'s cots, the supply boxes, Level 2's ducts.

**Light and air** (`AtmosphereSystem.L15.cs`, the `Levels` line): a thin cool-white haze in the light; a near-black
stale fog in the dark; grey in the service passages; smoky in a crematorium; a deep blue round the star door. 20 °C, 16 in
the dark. Stability 1.05 in the light; 0.7-0.8 in the dark (Fandom's bad air: it drains).

**Sound** (`sounds/ambient/15/`, generated): the hum (mains hum and harmonics, the engines' 31 Hz thrum, a beat between
two machines; everywhere, louder among the machines, faint in the dark); a running machine's whir on its lit casing
blocks (block ambient); the air handlers in the service passages; far-off beeps every 18-48 s where the power is on; and in
the dark the heartbeat ticking, its pitch falling from 1 to 0.7 over four minutes there (Fandom: it slows). The director's
distant sounds: machinery turning over, a beep.

**Danger.** Class 1. `Danger.OfLevel` 0.3, solitude 3.0 (the emptiest after the Poolrooms and The End). MenaceSystem gives
the dark squares the Approach band and everywhere else Safe; the roster is one entry, the existing Robo-Man (glimpse,
stalk, hunt), `NeedsDark`. No new creature (DECISIONS.md).

**Loot.** Scarce ("devoid of resources"): supply boxes 4.4 a wing (half picked over: `PickedOverShare` 0.5), mostly in
stores and camps; steel lockers about 22 a wing (a shut one may hold a bracket, nails, wire, twine, now and then Almond
Water, crackers or a candle; an open one only scrap); machine casing gives scrap wire, a little copper, now and then a
bracket; consoles wire, glass and copper; lab glassware glass shards; steel rods brackets and nails; the dead bones and
twine and, with a spear, a glass spear; thick glass shards; dead LED panels glass and wire.

**Notes and handbook.** Seven common notes for the level and one folded (`tools/gen_notes.py`, Level 15's block): the
white wall and its door that goes (A.L.), the hum and the ticking (Tom), the codes on the vents (Dez), lab coats and no
guns (M.E.G.), the machine rooms, the dark squares and what walks there (Nell), the star door (Dez); the folded fair copy
of the halls (A.L.). A loose note lies by each camp (`NoteSpots`), and the dead give notes when broken (`NoteSystem.Spots`
source `l15-corpse`). Handbook page `level15` ("Level 15: the Futuristic Halls", `tools/gen_guide.py`, listed after
What Lives Here in `GuideSystem.Added`). Title and hint lines: `level-27`, `levelhint-27`, sub-zone titles 2701-2708.

**Harness** (`tools/mapgen/L15Stats.cs`): `15stats [wings] [rim] [map]` (rooms by kind, machines, the dead, camps, boxes,
lockers, dark share, the star door, every room and tile reached from the main halls, 60 arrivals in a lit hall or
corridor; `map` writes `l15map.ppm`), `15dump x z [r]` (the tiles round a place as letters).

## 3. Choices against the brief, and inventions

- Main halls every **4 cells** as the brief says, but five wide (not four) so the light strip runs down a middle, and five
  high; side corridors three wide and four high. Machine halls 5 or 7 high (the band allows up to 7).
- Room shares by size rather than the brief's flat percentages: by count the machine rooms are 24% (the brief's 35%), but
  by floor area they are the largest share. Crematoria rarer (1%) than any other kind: the lore has one.
- The brief's "PlanCache as in L120/L52" kept; the wing plan is a recursive cut (my invention) so every corridor ends on
  another or on a main hall, which makes the maze connected by construction.
- **Inventions** (not in the lore): the rod press's conveyor and heap of rods (Wikidot only says some machines make steel
  rods); the security gate's tread plate and rolled shutter; the floor lights' look; the views on the displays as three
  fixed pictures (Fandom says they cycle); the Robo-Men in the dark (the brief's suggestion; the lore has no entities);
  stability drain and the 4 °C drop in the dark (the brief's suggestion for Fandom's bad air); the heartbeat's pitch
  slowing over four minutes; codes "D", "K", "C", "L", "S" beside the lore's H and e; the radar's and the ESCAPE panel's
  text read as block descriptions; the camps' loose notes; the wrong-angled beams as the cheap oddity.
- Left out: the self-cleaning effect (optional in the brief; not built), wall panels that cycle images, the isolation
  effect (no two wanderers meet), Enric and any living base (DECISIONS.md), entrances and exits (cheats only; the notes
  and handbook describe the Level 10 wall door), the radiation worry by the star.

## 4. Lang strings (`en.json`, one block after `levelname-27`)

`level-27` "Level 15: Futuristic Halls", `levelhint-27`, `levelname-27`; sub-zones `level-2701` The Power Is Out (and
its hint), 2702 A Machine Room, 2703 The Service Passages, 2704 A Control Room, 2705 A Lecture Hall, 2706 A Laboratory,
2707 The Crematorium (hint), 2708 The Star Door (hint); `block-l15-*` names; `blockdesc-l15-*` for the ESCAPE panel, the
consoles, the radar, the views, the scrawled vent, the wooden door, the scanner, the star door and the dead; the notes'
and the handbook page's keys (filled by the generators).

## Detail pass (2026-10-30)

Built from the scaffold in one pass (branch `exp/15`), to the brief's must and should lists and most of its nice list.

**Built.** Everything in section 2: the lattice of main halls and the wings cut into corridors, service passages and
eleven kinds of room; the power-out squares; machine rooms behind open security gates with dead hand scanners, room
codes and thick glass, machines stacked from twelve casing faces (dead, running and humming, wrecked, an incinerator, a
rod press with its conveyor and rods); labs, stores, dormitories, kitchens, control rooms (the radar, the ESCAPE panel and
ACCESS DENIED consoles, readable as block descriptions), lecture halls, bare rooms, crematoria, the star door; the dead in
lab coats with pipe-and-glass spears, abandoned camps, bones; wrong-angled beams, pillar stubs and a wooden door in a
wall as the oddities. Blocks, textures, shapes and sounds from `tools/gen_15.py`; air, titles and the sound bed (hum,
air handlers, beeps, the slowing heartbeat in the dark) in `AtmosphereSystem.L15.cs`. Robo-Men in the dark only; loot
scarce; seven notes and a folded one; the handbook page; the title, hint and sub-zone lines.

**Shared files touched** (one line or arm each, Level 15's): `Tiles.cs` (members in the L15 blocks), `AtmosphereSystem.cs`
(the `Levels` line), `Roster.cs` (danger, roster, distant sounds, a solitude line), `MenaceSystem.cs` (the case),
`WorldLayout.Loot.cs` (picked-over share), `WorldLayout.Notes.cs` (a `NoteSpots` arm), `NoteSystem.Spots.cs` (a source line
for the dead), `GuideSystem.cs` (`"level15"` in `Added`), `tools/gen_notes.py` and `tools/gen_guide.py` (one block each),
`lang/en.json` (one block after `levelname-27`; `config/notes.json` and `docs/design/notes-catalogue.md` regenerated).

**Checks** (2026-10-31). `expclash` clean; mod and mapgen build, 0 errors; `layouthash` at layout versions 1 and 12:
every line for levels 0-20 and the `layout hash` line identical to main's; `regions` 60/60 arrivals, none wrong or in a
pocket (full size and `SPAWN=1000`); `15stats 4`: 81 wings, 0 rooms cut off, 0.35% of walkable tiles unreached (one-tile
corners behind props), 60/60 arrivals lit; `15stats 3 rim`: the same at the rim, one star door. Headless (port 43162):
a dummy placed in the level (light 13), `blocksweep` 0 threw, 0 error lines; `ratecheck 27 approach 50` 10.5 bodies an
hour (Level 6's dark measures 10.2), heartland 3.5 (the director never places in Safe); `encounter roboman hunt` at a
dark doorway placed it; `feltrate 27 approach`: stalk 100%, hunt 98%, glimpse 0% (no long sight lines in the dark).
`GATE_TAG=l15 python tools/gate.py --fast --port-base 43160`: PASS.

**What to check in game** (screenshots): a main hall (the LED strip, the floor lights, the ribs and pilasters: does it
read clean, white and "futuristic", not hospital-plain?); a corridor and a service passage; a machine room from its gate
(the shutter, the scanner, the code, the glass, the monoliths, a running machine's lit faces); a control room's wall of
displays; a lecture hall; a dark square (black, the ticking audible, a Robo-Man now and then); a crematorium; the star door
(`15stats 3 rim` prints its wing); a camp with a body. Sounds: is the hum too loud in the machine rooms, the heartbeat too
quiet? Light: about 10-13 at the floor in the halls (measured 7-14 at rel 1 round an arrival).

**Open questions for the user.** Is one dark square in six right, and should the dark drain stability (my invention from
Fandom's bad air)? Should the self-cleaning effect be built (items left in the lit halls vanish)? Are Robo-Men the right
borrowed creature, given the lore has none? Should the star door ever lead anywhere?

### Round 2 (2026-10-31): looked at in the game client, then fixed

The lead's review of round 1: clean and on-lore, but every surface the same white panel, and arrivals facing a wall
point-blank. What changed (all of it in the level's own files, plus the lines named below):

- **Showcase spots** (`WorldLayout.Level15.Showcase.cs`, found from the layout round the middle, seed independent): a main
  hall's long view, a crossing with its signs, a side corridor, a service passage, a machine room from its gate and from
  inside (one with at least 24 machine blocks ahead, some running), a control room, a lecture hall, a laboratory, a camp
  with its tent and its dead, a crematorium, a dark hall, a Robo-Man in it (`/backrooms l15 roboman x z`, the level's own
  testing command in `src/Regions/L15System.cs`), and the nearest star door. `mapgen 15showcase` lists them offline.
- **The main halls dressed** (`WorldGenerator.L15.cs`, from coordinates; one face of the wings' walls): a graphite band at
  waist height with a pale cyan line along it (wayfinding), a graphite cornice under the ceiling with a strip of light, a
  tall wall light in the middle of every bay (one in two gives light, by turns on the two walls; dead in the dark: the
  lore's "large lights on walls"), and by every crossing a sign, "HALL" and a letter and number. Inventions: the band, the
  cornice, the signs (the lore has codes on the walls, not hall names).
- **Light rhythm**: each stretch of main hall between two crossings is lit its own way: one strip of panels, two strips,
  or a square of nine panels in the middle of each bay; a square of nine panels over every crossing.
- **Doors**: every doorway has steel jambs with a strip of light down them and a lit lintel (dead in the dark); the room's
  code and the gate's scanner moved one block out, beside the jambs.
- **Room walls** (both wikis' "white or grey concrete"): machine rooms, wrecked ones, stores and crematoria in pale grey cast
  concrete (form-tie holes), kitchens and half the labs in white wall tiles over a grey row, a quarter of the bare rooms in
  cast concrete; the rest white panels. A room's own walls only, so corridors now run past stretches of concrete, glass,
  tiles and panels. One side corridor in four has the dark non-slip coating for its floor.
- **The dark** fixed: the squares are now centred on the hall lines (round 1 put a hall along each square's edge, and the
  lit rooms beside it lit the "dark" hall through their doors: light 6-9 measured there), and a room whose door opens into
  the dark goes dark with it. Measured headless: light 0 in a dark hall. One square in about seven (0.15) is dark now, 17%
  of the tiles with the rooms that follow them.
- **Arrivals**: only in a lit main hall, off its foot strips, and facing along the longest way clear (`ThresholdSystem.L15.cs`,
  as the Hub does for its sidewalks).
- Smaller: the crematorium floor is worn ceramic so its soot reads (it was the dark coating); new blocks named in `en.json`.

Shared files: `tools/mapgen/mapgen.csproj` compiles `src/Cheats/Showcase.cs` (the showcase stubs broke the harness for every
level; exp/36 made the same one-line fix) and `tools/clientrig/rig.py` takes exp/36's fix (a404577b) so the showcase shots are
copied out; `lang/en.json` (twelve block names in the level's block).

**What the shots showed** (`%TEMP%/backrooms-shots/15-r2b`, `15-r2c`, `15-r2c-torch`, final `15-r2-final`; three look-fix
cycles): round 1's corridors read as one white panel; now the halls read as halls (the band and its line running away, the
cornice, the wall lights' rhythm, the lit door frames, the crossings' light squares), and corridors alternate panels, cast
concrete, tiles and glass. The first pass found the dark hall fully lit (lit rooms' doors, fixed above) and a near-empty
machine room picked for the showcase (now one with running machines); the crematorium's scorch on the dark coating read as
pale patches (now worn ceramic); the first cast concrete's four tie holes a block looked like rivets (now one); the wall
tiles were busy (now larger and softer). Torch shots: the dark hall with a Robo-Man reads well, the lit hall glowing at its
far end.

**Checks** (2026-10-31): `expclash` clean; mod and mapgen build, 0 errors; `layouthash` v1 and v12: no line for levels 0-20
or the `layout hash` line differs from main's; `regions` 60/60 (none wrong, none in a pocket); `15stats 4`: 0 rooms cut
off, 60/60 arrivals in a lit hall, dark 17.3%; headless (port 43165): a dummy placed in the level at light 13, a Robo-Man
put down on it, 0 error lines; light in a dark hall measured 0 (port 43164); `GATE_TAG=l15 python tools/gate.py --fast
--port-base 43160`: PASS.

**Still weak.** Rooms are furnished as in round 1 (the machine rooms' monoliths are the best of it; stores, bare rooms and
dormitories are plain). The rig's random arrivals look at fixed headings, so an arrival shot can still face a hall wall two
blocks off even though the player arriving faces along the hall. The wall lights read as dark-framed panels more than glowing
fittings at a distance.

**Open questions for the user** (round 1's stand). Is the dark share right now (one square in seven, 17% of tiles with the
rooms that open into it)? Should the halls' cyan line and the hall signs stay (inventions)?

## Links (2026-10-31)

LINKS.md's "Level 15" section, built (branch `exp/15`). Every way is one-way and rare: the level is "extremely hard to get
into and out of". Code: `WorldLayout.Level15.Links.cs` (the layout of all of it, the arrival finder, the showcase spots),
`WorldGenerator.L15.Links.cs` (the blocks), `ThresholdNetwork.L15.cs` (the thresholds), `Regions/L15System.cs` (the ESCAPE
panel, the breaking pane, test commands), `tools/gen_15_links.py` (seven new blocks and their textures),
`tools/mapgen/L15Stats.cs` (`15links`). Unders `L15Wall10` 448 to `L15Stairs` 457; layout salts 0x2780-0x2785; threshold
salts 0x27C1-0x27C5.

**Ways in.**
- *Level 10, the white wall* (Wikidot, Fandom). Now and then an immense wall of Level 15's own white panels stands across
  the fields: the main halls' wall seen from outside (the kick plate, the graphite band and its pale line, a wall light in
  every other bay, the cornice light, white panels on up, a white steel pilaster every eight blocks, a steel coping), two
  blocks thick, ten high (rel 1-10: Level 10's band ends there, so it cannot be taller) and 384 long, laid in the middle of
  a block of the farm roads so that it never crosses one and runs from its door out of sight into the haze both ways. One
  small reinforced door in one face, lit jambs and a lit lintel round it, a steel tread plate before it. At most one to a
  square of the fields 2048 blocks a side (half the squares try; it must lie wholly on crops, stubble or meadow, clear of
  trees, scarecrows, field sheds and troughs, farmsteads, paddocks, ponds, Level 3999's arcade and windmills, and 64 blocks
  inside Level 10). Used: one way into Level 15.
- *Level 3, a door* (Fandom: "opening numerous doors in Level 3 has, in rare instances, led to Level 15"; and its first
  entrance, the shock from a door handle). About one cell in 1500 has a painted steel door (HIGH VOLTAGE) set in a straight
  wall, solid wall behind it and either side, clear floor before it, cold white light under it. Used: a jolt, and Level 15,
  one way.
- *Where they come out*: in a lit main hall, beside a reinforced door that does not open, one in the wall of nearly every
  wing (93%), between two pilasters, lit jambs either side (`L15SealedArrival`: the nearest such door to a place near the
  middle picked by the key, its hall tile lit). Used, it is locked.

**Ways out** (Fandom; each one-way; one wing in about 21 has one, a third of them each kind (layout 16, every world from pre.13: the pane and the
stairs a quarter of that, one wing in 256 each, LINKS.md "Layout 16"); none within about 200 blocks
of the middle, where people are put down):
- *ESCAPE* ("a control panel will occasionally contain a button labeled ESCAPE ... a nearby locked gateway available,
  leading to Level 3"): in a lit control room one ESCAPE panel on the wall of displays is live (`l15-escapelive`: the
  button lit, a green lamp). The room's side wall (else the wall across from the panel) holds a locked security gateway two
  wide and three high (`l15-gatewayshut`, the hazard band at its foot), with more wall behind it where a service passage
  allows. Pressed (`BlockBehaviorL15Escape`, a threshold block so it never breaks), the gateway's blocks are swapped for
  `l15-gatewayopen` (dark, a warm glow low down, no collision) for good; walking into it, or using it: Level 3.
- *Breaking a window* ("can result in transportation to Level 11"): one pane of a lit machine room's thick glass wall onto a
  corridor is `l15-cityglass`: orange, a sodium lamp's bloom and far lit windows in it, as if a street lay past the machine
  room (our invention, so the pane can be found). Broken (`DidBreakBlock`): taken through, to a city sidewalk; once broken,
  climbing onto its sill does the same.
- *An office staircase* ("descending an office staircase may take you to Level 4"): a lit bare room, store, dormitory or
  lab (7 to 28 blocks, at least 12 the long way) turned into an office out of place: Level 4's carpet, filing cabinets along
  the long walls, a desk or two with chairs, Level 4's ceiling tiles between the lights; down its middle a two-wide flight
  of concrete stairs through the floor (six steps, a landing, drywall round the stairwell). Three steps down, out of sight
  of the room: Level 4, at the foot of a stairwell's flight up where one is near.
- The star door stays a sight. Level 14's MEDICAL CENTER door, Level 0.8's blue door, a hospital door, THE ARCHIVES and the
  spilt Almond Water: rumours in a note and on the handbook page.

**Numbers** (seed 12345, full size; `mapgen 12345 16000 15links`). Level 10: 563,470 km2 of fields, 38,506 walls, one per
14.6 km2 (about 3.8 km apart); the nearest door 7.6 km from spawn (518940,508868, facing west). Level 3: 10.7 km2, 5 doors,
one per 2.1 km2 (about 1.5 km apart); the nearest 2.6 km from spawn (514533,511314, facing south). Level 15, the 841 wings
round the middle: a door that does not open in 93% of wings; ESCAPE panels 9 (1.1% of wings, one per 1.5 km2), the nearest
598 blocks from the middle; street panes 16 (1.9%, one per 0.86 km2), nearest 186; office stairs 14 (1.7%, one per 0.98
km2), nearest 435. Arrivals beside a door that does not open: 40/40. Every way gone through in the network (`15links`
trips): both ways in come out beside a door that does not open; those doors and the shut gateway are locked; the gateway
(walked or used) leads to Level 3, the pane (broken or climbed) to Level 11; the stairs do nothing at their top and lead to
Level 4 four steps down; every one is one way and the same place again.

**Our inventions.** The wall's dress (the halls' own: the lore's "identical to the one from Level 15's interior") and its
door's lit frame; the doors that do not open in every wing (the arrival's "reinforced door that does not open"); the Level 3
door's look; the live panel's lit button and green lamp; the gateway's place in the panel's room; the street pane's orange
light; the office's furniture and the depth at which the stairs take you. The wall does not vanish after use (the lore's
"the door later vanishes" is told in the notes; in the world it stays).

**Text.** Handbook page: "Ways in", "Ways out", "The star door" (the experimental line gone). Notes: l15-1 rewritten (the
door you come out beside does not open), l15-8 ESCAPE (M.E.G.), l15-9 the office (Dez), l15-10 orange glass (Tom), l15-11
the camps' rumours; the folded r-l15-1 ends "Ways out: none I found. The M.E.G. claim three"; in the hosts' pools, through
our own keys appended to their tracks from Level 15's block of gen_notes.py: l15-h10 (Level 10, Nell: the white wall) and
l15-h3 (Level 3: white light under a door, the handle's jolt). A message for each arrival and for the panel.

**Rows for the guide's ways-between-levels table.**

| From | Threshold | To | Way |
|---|---|---|---|
| Level 10 | the small reinforced door in an immense white wall across the fields (one per ~15 km2) | Level 15, beside a door that does not open | one way |
| Level 3 | a steel door with white light under it; its handle shocks (one per ~2 km2) | Level 15, beside a door that does not open | one way |
| Level 15 | the gateway a live ESCAPE panel rolls up, in a control room | Level 3 | one way |
| Level 15 | breaking an orange pane in a machine room's glass wall | Level 11, a sidewalk | one way |
| Level 15 | down an office's staircase through the floor | Level 4, the foot of a stairwell | one way |

**Shared files touched.** `Tiles.cs` (the Unders members in Level 15's block, one line); `lang/en.json` (Level 15's block);
`tools/gen_notes.py` and `tools/gen_guide.py` (Level 15's blocks only; the two host notes are appended from there;
`config/notes.json` and `notes-catalogue.md` regenerated). Level 15's own: `WorldLayout.Level15.cs` (`L15Plan` partial,
`L15LinkPlan` after a wing is laid), `WorldGenerator.L15.cs` (the links' blocks first), the showcase (one line), the
level's test command (`/backrooms l15 escape|break|l15-<kind> x z`).

**Checks** (2026-10-31/11-01). `expclash` clean; mod and mapgen build, 0 errors. `BACKROOMS_NO_EXP_ENTRANCES=1` layouthash at
layout versions 1 and 12: every line for levels 0-20 and the `layout hash` line identical to main's saved files; without the
variable no line moves either (the hash's sample cells hold none of these rare entrances). `regions` 60/60 in Level 15;
`15stats 4` OK (0 rooms cut off, 60/60 lit arrivals). `GATE_TAG=l15 python tools/gate.py --fast --port-base 43160`: PASS
(boot: 0 missing blocks, 0 error lines). In the game (two client-rig runs, ports 43163-43164, the op player): the showcase's
`trip-*` spots went through every way: the white wall's door and the Level 3 door put the player down in a lit hall beside a
door that does not open (the arrival messages shown), ESCAPE rolled its gateway up (6 blocks) and walking into it led to
Level 3, the office's stairs to Level 4, breaking the orange pane to a night sidewalk of Level 11; 0 error lines. The shots
(`%TEMP%/backrooms-shots/15-links1`, `15-links2`): the wall reads as a white hall wall standing in the wheat and running into
the haze; the doors that do not open, the live panel, the gateway shut and open, the pane and the office read as meant. Fixed
after the first run: the stairs' step numbers drawn as crates over the stairwell; the Level 3 door's light too faint to see in
Level 3's dark (now light 7; it is still a dim door in a dim level, which is right for it).

## Round 3 (2026-11-01): the detailed visual pass

The user asked for more detailed visuals, multi-block objects and signs where a real place has them, more realistic
layouts, and the lore kept. The lead's notes for Level 15 (from round 2's final sheet): on-lore and clean, the wayfinding
stripe and door numbers help, but monotonous between the set pieces. Compared with the released levels of the same kind
(Level 4's offices and their signs, Level 5's hotel corridors, Level 3999's halls, Level 11's store signs). Tiers: A must,
B should, C nice. "Lead" marks an item from the lead's notes.

### List

**1. Layout realism**
1. (A, lead) [done] New room kind, a **cafeteria**: the big kitchens turned into a serving line (counter with a sneeze-guard and
   steel wells, trays, a menu board over it), long tables with stools, the kitchen behind (counters, stove, fridge).
2. (A, lead) [done] New room kind, a **medical bay** (the Level 14 MEDICAL CENTER rumour): hospital beds with curtain rails
   between them, an IV stand by each, a medicine cabinet wall, a red-cross sign over the door. A sight only (no link).
3. (A, lead) [done] New room kind, a **hydroponics bay**: rows of two-high grow racks with dead and withered plants under
   magenta grow lights, a nutrient tank with pipes up into the ceiling. Invention (the lore has kitchens and food-service
   appliances, not farms): food is NOT harvestable (balance unchanged).
4. (A, lead) [done] **Dormitories with bunks**: an upper bunk frame over each cot (the cot stays the bed, so the number of beds
   does not change), a locker at the foot, a footlocker now and then.
5. (A, lead) [done] **Lecture hall raked**: rows of seats with backs and fold-down writing tablets on stepped risers rising away
   from the stage (half a block a row, an aisle of steps up the middle), the projection display over the stage kept.
6. (B) [partly: the canteen has its own kitchen behind the serving line; AUTHORIZED by every control room's door; fire extinguisher cabinets in the corridors; no pairing of rooms across walls] Rooms placed by adjacency where it is cheap: a kitchen or cafeteria pairs up with a store next to it; a control
   room's door onto a main hall gets an AUTHORIZED plate; machine rooms keep their gate.
7. (B, lead) [done] **Elevator lobbies** on the main halls: a pair of brushed-steel lift doors (2 wide, 3 high, a seam down the
   middle) that do not open, a call-button panel beside them and a floor indicator over them, now and then near a
   crossing.
8. (B) [done: the DECONTAMINATION plate and a rolled-up shutter like the machine rooms' over those doors] **Decontamination** look on labs: the lab door's lintel in yellow/black and a DECONTAMINATION plate.
9. (C) [skipped: time; the hanging signs and floor lines do the landmark work] A recurring landmark without a visible grid: a big atrium-like crossing now and then (taller light square).

**2. Multi-block objects**
10. (A, lead) [done] **Robot charging docks** in the main halls: a recess in the wall with contacts and a status lamp, a
    powered-down Robo-Man standing in it (the existing creature's model as a block), a dock number plate; in the dark the
    lamp is dead. Invention (the Robo-Men are our borrowed creature).
11. (A) [done] **Serving line** (item 1): counter blocks with glass guards reading as one run.
12. (A) [done] **Bunk beds** (item 4): cot + upper frame reading as one bed.
13. (A) [done] **Raked seating** (item 5): riser + seat rows reading as one tiered block.
14. (A) [done: hospital beds, drip stands, bedside cabinets, a curtain on its rail between the beds, cabinets and a crash cart] **Hospital beds with curtain rails** (item 2): bed and the rail and curtain reading as one bay.
15. (B, lead) [done] **Cable trays** along the side corridors' ceilings (a ladder tray with bundled cables, a run the length of
    the corridor).
16. (B) [done] **Grow racks** (item 3) two blocks high with the light strip under each shelf.
17. (B) [done] **Lift doors** (item 7) as a 2 x 3 set with the indicator over them.
18. (C) [done: three wide, two high, over the panels] A big **wall display** in the control rooms spanning three blocks (the radar large: "AVALON 2.4").

**3. Signs and text**
19. (A, lead) [done: the name plate under the room's stencilled code; the code is the number] **Room name plates by every door**: LABORATORY, STORAGE, MACHINE ROOM, DORMITORY, KITCHEN, CAFETERIA,
    CONTROL, LECTURE HALL, MEDICAL, HYDROPONICS, and the door number (wing letter and number, "B-114"), a white plate with
    the wing's colour bar.
20. (A, lead) [done] **AUTHORIZED PERSONNEL ONLY** plate on each machine room's gate side, "MACHINE ROOM" on its name plate.
21. (A, lead) [done] **Holographic-looking signs** at the crossings: a glowing cyan sign hanging from the ceiling over each
    approach to a crossing (the hall's name, arrows), readable from both ways.
22. (A, lead) [done] **Floor arrows and zone colours**: each main hall line its own colour (cyan, amber, green, violet), a line
    of that colour down the middle of the floor with a chevron every 16 blocks; the hall signs take the same colour.
23. (B, lead) [done] **ESCAPE control panel labels**: the panel redrawn with small print ("EMERGENCY", "EGRESS"), the radar and
    ACCESS DENIED consoles stay.
24. (B, lead) [done: blank brushed steel, as on the bare rooms and the crematoria] **Star door's plate**: a blank brushed-steel plate by the room's door (the lore names nothing).
25. (B) [partly: HIGH VOLTAGE in machine rooms; no NO ENTRY] **Warning plates**: "HIGH VOLTAGE" and "CAUTION" on machine-room walls; "NO ENTRY" at service passages.
26. (B, lead) [done] "MACHINE ROOM" and "DECONTAMINATION" text (items 8, 20).
27. (C) [partly: a two-block SECTOR MAP near a crossing on half the wings' walls, half lost to static (no directory: the lore's codes are "somebody else's system")] Directory boards at crossings listing the wing's rooms.

**4. Detail visuals**
28. (A, lead) [done] **Glass walls into the labs and control rooms** from the corridors (as the machine rooms have), so the
    rooms show from the hall.
29. (B, lead) [done] **Vents, pipes behind grilles, service hatches** on the halls' and corridors' walls (a hatch with a handle
    and hazard corner, a grille with pipes behind it).
30. (B) [done] Wall lights brighter (round 2: they read as dark-framed panels at a distance).
31. (B) [done] Floors that change by room: the medical bay in pale blue-grey vinyl, the cafeteria in a warm terrazzo,
    hydroponics on grating.
32. (B) [done] Clutter that tells a story: stripped appliances (Fandom: coffee machines and 3D printers emptied of their
    insides) on kitchen counters and lab benches.
33. (C) [done: a corridor in three has a continuous slot of panels, one in six giving light] Lighting rhythm in the corridors: a continuous slot of light in a few, the panels in others.
34. (C) [done] Dust on the dark squares' floors.

**5. Lore alignment**
35. (A) [done] Keep the halls clean and white; the new rooms marked as inventions where the lore lacks them (hydroponics, docks,
    medical bay, signage text).
36. (B, lead) [done: bags and bones 2.6 times as often in the dark halls; docked Robo-Men; the roster untouched] "More Roboman and bones where the lore puts them": bones and dropped bags in the dark squares' halls more
    often (visual); the Robo-Men's numbers are the balance agent's (noted below), so the docks carry the extra Robo-Men as
    powered-down hulks.
37. (B) [done] "Appliances stripped of their inner machinery" (Fandom), item 32.
38. (C) [skipped: time] A crematorium's door plate left blank, a hand-written "DON'T" by its door.

**6. Released-level alignment**
39. (A) [done] Every new block named in `en.json` (HUD names, pick-block) in the level's block.
40. (B) [done] Sub-zone titles for the new rooms (A Cafeteria, The Medical Bay, A Hydroponics Bay) as the other rooms have.
41. (B) [done] The handbook page mentions the medical bay, the docks and the signs (no new mechanics).
42. (B) [done] Showcase spots for each new set piece (cafeteria, medical bay, hydroponics, raked lecture hall, a dock, a lift
    lobby, a hanging sign), all computed from the layout.
43. (C) [done: machine rooms still 23% of rooms by count and the most floor] The new rooms' share kept so the level's room mix still reads as machines first.

### What was built (code)

Commits on `exp/15`: 048bcdd2 (the list), a3c190fa, then the fixes after each run (see `git log`).

Layout (`WorldLayout.Level15.cs`): three new room kinds (`L15Zone.Canteen`, `Medical`, `Hydro`, codes F, R, G) in the
size ladders; the lecture hall raked (its stage now by its door, rows of seats on steps half a block higher each row,
three aisles of steps; `Props.L15Seat`, `L15Riser`, the steps walkable); glass walls by the doors of labs, control rooms,
hydroponics bays and canteens; a name plate under every door's code, AUTHORIZED PERSONNEL ONLY by gates and control rooms,
DECONTAMINATION by labs and hydroponics bays, HIGH VOLTAGE in machine rooms (`L15WallAuth` ... `L15WallBigScreen`, 16-25);
a big radar display over each lit control room's panels; service hatches and pipe grilles on the corridors' walls; cable
trays along six side corridors in ten (`Overheads.L15TrayWE/NS`); robot docks on the main halls (`Props.L15Dock`,
`L15HallDockAt`); lifts in the wings' walls onto the halls, placed after the links so no link moves (`L15Lifts`); stripped
appliances on counters and benches; curtains between the medical bay's beds (`Overheads.L15Curtain`, its edge in `Roof`);
dust in the dark; bags and bones more often in the dark halls; the lecture halls' projection screen (three by three, an induction slide), decontamination shutters, a continuous light slot in a corridor in three, sector maps by the crossings, fire extinguisher cabinets. Generator (`WorldGenerator.L15.cs`): the hall line's colour
on the band and down the floor with chevrons every 16 blocks toward the nearer crossing; a hanging sign three blocks wide
across each hall ten blocks out from each crossing, its name both ways (lit, dead in the dark); the bunks over the dorms'
cots; the new props and dress. Assets: `tools/gen_15_r3.py` (run after `gen_15.py` and `gen_15_links.py`): `l15-sign`,
`l15-floormark`, `l15-hangsign`, `l15-bunk`, `l15-riser`, `l15-seat`, `l15-serve`, `l15-growrack`, `l15-dock` (the
Robo-Man's own model in the block), `l15-tray`, `l15-appliance`, `l15-curtain`, vinyl and terrazzo floors, the ESCAPE
panels redrawn at 64 px with their labels, and the wall lights brighter (`gen_15.py`). Titles 2709-2711; the handbook page
names the new rooms, the docks and the lifts.

### Inventions

The hydroponics bays (the lore has kitchens and food-service appliances, not farms), the medical bays (only the lore's
rumoured MEDICAL CENTER door suggests one), the robot docks and their powered-down Robo-Men (the Robo-Men are our borrowed
creature), the lifts, the hall lines' colours, floor lines and chevrons, the hanging hall signs, every word on the plates,
the menu board ("SERVICE SUSPENDED") and the big display ("LINKS 214"), the curtains, the dust in the dark (against
Fandom's self-cleaning, which we did not build), and the canteen as a room of its own. The radar display's ACCESS DENIED
line and "Avalon 2.4" are the lore's.

### Balance notes for the lead

- **Beds**: the medical bays add hospital beds (a `BedSystem` family) to Level 15, about 0.5 bays a wing with 2-6 beds
  each, in lit rooms. The dorm cots are unchanged (the upper bunk is a look only, not a second bed).
- **Loot-like drops**: the docked Robo-Men drop scrap wire and a bracket when broken (about 0.4 docks a wing on the main
  halls); the cable trays, appliances, bunks, serving line and racks drop a little scrap wire, brackets or twine. Nothing
  edible or drinkable: the hydroponics bays' plants are dead and drop no food.
- The roster is untouched: "more Roboman" was done with powered-down hulks in docks, not more live ones.
- Dark halls hold more dropped bags (props only, not containers) and bones.

### What the shots showed

Three client-rig runs (`%TEMP%/backrooms-shots/15-r3a`, `15-r3b`, final `15-r3-final` with a torch in hand).
- **Run 1** (stopped by a rig error after 13 spots): the halls' floor line and the hanging HALL signs read at once, the
  plates by the gates ("M27" over MACHINE ROOM) read as a facility's, and the raked lecture hall read as one, rows of blue
  seats climbing away. The docked Robo-Man stood sideways in its dock: the model's own turn was not drawn; now the model
  is flattened and turned in the generator.
- **Run 2** (all 42 spots): the big radar over the control room's panels, the lift with its B3 indicator and lit call
  button, DECONTAMINATION and LABORATORY plates by a lab's door, the dorm's bunks over the cots, the canteen (long tables,
  terrazzo, the serving line and menu far off), the medical bay's beds and cabinets, the hydroponics bay's magenta racks
  all read; the random arrivals now face along the halls. Fixed after it: the hydroponics plants read as cardboard boxes
  (now stalks and drooping dry leaves); the canteen's serving line was too far to see (a spot of its own); the medical bay
  had no curtains (now on rails between the beds); the lecture hall's stage had three small displays (now a projection
  screen three by three).
- **Final run** (`15-r3-final`, 44 shots, a lit torch in hand so the dark squares show; the torch warms the white halls
  to cream near the camera, which the unlit runs do not have): the curtains between the medical bay's beds, the serving
  line's glass guard and trays, the projection screen over the lecture hall's stage seen from the top of the aisle, the
  sector map with its static by HALL N6, the hydroponics racks' dead plants under magenta light, and the dark hall with a
  Robo-Man in it, its floor line and dead floor lights, all read. After it, only the dry leaves were made smaller (they
  read a little too large and stiff); no shot was taken of that.

**Still weak.** The main halls between crossings are better dressed but still long and regular (the lore's labyrinth);
the docks, lifts and maps are rare by design. The menu board and the canteen's kitchen are far from the canteen's door
spot. The bed curtains are one fixed shape (always drawn the same way). The service passages' caged lamps are warm and
read orange next to the white halls (round 2's choice, kept).

### Questions for the user

- The medical bays are an invention from the lore's rumoured MEDICAL CENTER door, and their beds are real beds: keep
  them sleepable, or make them a look only?
- The hydroponics bays and the robot docks are inventions: keep both?
- The induction slide's "DO NOT ENTER THE STAR ROOM" ties the lecture halls to the star door: too much of a hint?

**Checks** (2026-11-01). `expclash` clean; mod and mapgen build, 0 errors; `BACKROOMS_NO_EXP_ENTRANCES=1` layouthash at
layout versions 1 and 12: no line for levels 0-20 and no `layout hash` line differs from main's saved files; `regions`
60/60 in Level 15 (none wrong, none in a pocket); `15stats 4` OK (0 rooms cut off, 0.43% of walkable tiles unreached,
60/60 lit arrivals, dark 17.7%); headless (port 43165) a dummy placed in the level twice (light 13) and a Robo-Man put
down on it, 0 error lines; `GATE_TAG=l15 python tools/gate.py --fast --port-base 43160`: PASS (c60b752a).

## Round 4 (2026-11-02): the asset-quality pass

The user asked for AAA-quality assets, multi-block objects that read as one thing, level design refined, the lore and
the other levels kept in line (sharing assets where they fit, "similar but unique" where 15's clean white needs its own).
Looked at: round 3's final sheet and full shots (`15-r3-final`, `15-r3b` for the halls without a torch), the lead's notes
for Level 15, round 3's "Still weak", the brief and DECISIONS.md. What the full shots show: the halls read as clean but
flat (panel texture, a band, ribs); the consoles are white boxes with a picture on the front; the serving line's guard
reads as a white frame, its trays as grey slabs; the hydroponics racks are plain square frames and the dry leaves are
big planks; the medical bay's curtains are flat slabs hung from a bar with no track, the beds have no monitor; the lift
and ESCAPE panels are pictures on the wall; the docked Robo-Man stands in a plain steel niche. Tiers: A must, B should,
C nice. "Lead" marks an item from the lead's notes. New shapes go in `tools/gen_15_r4.py` (run after `gen_15_r3.py`);
block codes stay where they are (no save break), new blocks are added.

### List

**1. Assets to rebuild to the bar**
1. (A, lead) [done] `l15-console` (dead, denied, radar): a real console desk: a plinth with a kick recess, a sloped keyboard
   deck with a keyboard and a trackball, a monitor in a bezel on a neck and foot, tilted back, its screen glowing where
   lit, cable to the floor, edge wear.
2. (A, lead) [done] `l15-dock`: the charging dock rebuilt: a back plate with sprung contact arms at the robot's shoulders, a
   charging pad with guide rails and contact studs, a cable conduit up into a hood, the status lamp and a small lit
   display, chamfered cheeks; the docked Robo-Man's eye lit when the dock has power.
3. (A, lead) [done] `l15-seat` / `l15-riser`: lecture seats as real seats: two steel side standards, an upholstered pan and a
   curved back (rotated, stitched seams), a hinged writing tablet on a swing arm, aisle step lights in the risers.
4. (A, lead) [done] `l15-serve`: the serving line: a tubular tray rail on brackets, a steel-framed angled sneeze guard (glass in
   the translucent pass), heat lamps glowing under the top shelf, wells with pans and a ladle, a till with a screen.
5. (A, lead) [done: `l15-stool` and `l15-ctable` in place of the folding chairs and tables in canteens] New `l15-stool`: the canteen's tables get fixed steel stools (pedestal, foot ring, round seat) in place of
   the office chairs at the long tables.
6. (A, lead) [done] `l15-growrack`: hydroponics racks: NFT gutters with net pots and small, varied dead plants, a feed pipe
   with drippers and a return pipe, LED bars on hangers with a cable, end posts with feet.
7. (A, lead) [done] `l15-curtain`: the bay curtains on a ceiling track with end stops and hangers, gathered folds (rotated), a
   mesh top band, the hem clear of the floor.
8. (A, lead) [done] New `l15-medmonitor`: a vitals monitor on a wall arm (or a roll stand) at each medical bed's head, its screen
   lit (flatline and dead) where there is power (similar to `l14-monitor`, clean white for 15).
9. (A, lead) [done] Lifts: the doors in a proud brushed-steel portal (jambs, header, sill plate) as model blocks; the call
   panel and the floor indicator as lit models (bezel, buttons, glowing digits).
10. (A, lead) [done: and every wall display (dead, radar, views) in a bezel] The ESCAPE panels and the big radar display as lit models (a bezel standing off the wall, the screen
    glowing, buttons and a key switch), not pictures flat on the panel.
11. (A, lead) [done] `l15-hangsign`: hall signs as lit models: a frame with a lit edge, the face glowing, ceiling rods with
    plates and a cable, read both ways.
12. (A, lead) [done: `l15-glazing`] Glass walls with frames: `l15-glass` (clear, cracked) gets a steel sill, a head rail and a mullion every
    block, glass kept translucent.
13. (A, lead) [done: seams folded back and corner fasteners on the panel (every texture drawn on it regenerated); the pilasters as I-section columns with a plinth (`l15-panel-pil*`)] `l15-wall` panels: real panel seams (bevelled joints, recessed fasteners), scuffs at hand height, grime at
    the foot; the pilaster as a shaped column (chamfers, a plinth).
14. (B) [done] `l15-labbench`: lab benches with a reagent-shelf upright, gas taps, a gooseneck tap over the sink, drawer fronts
    with pulls.
15. (B) [done: the open one hollow, a lab coat left hanging] `l15-locker`: lockers with vents, a handle, a number plate, the ajar door swung open (rotated).
16. (B) [done: three bundles, ties, trapezes on threaded rods] `l15-tray`: cable trays with coloured bundles and ties, hung on threaded rods with a channel.
17. (B) [done: `l15-lectern` beside the screen on stages 9 wide or more] `l15-stage`: a lectern on the stage with a reading lamp (new `l15-lectern`).
18. (B, lead) [partly: the dock's copy has its eyes lit; the creature itself is the Castle's too (below, for the lead)] Robo-Man: the creature is shared with the Castle (`roboman`), so its model is the lead's; the dock's copy
    gets the lit eye; a rebuild note for the lead.
19. (C) [done] `l15-stardoor`: the frame with bolts, a threshold plate and the star's halo.
20. (C) [done] `l15-corpse`: lab coats with folds, a lanyard, the spear's binding.
21. (C) [done: every casing kind a model, same codes] `l15-machine` casings: a few faces with relief (louvres, a handle) as shapes.

**2. Multi-block set pieces**
22. (A, lead) [done: `l15-bulkhead` headers and `l15-panel` jambs on the rib every 32 blocks, a tread plate across the floor] **Bulkheads** across the main halls every 32 blocks: a heavy portal frame (jamb blocks proud of both walls,
    a deep header under the ceiling with a light bar and a hazard band, the hall's line code stencilled on the jamb).
23. (A, lead) [done] **Lift lobby** as one object: portal, doors, call panel, indicator, sill (item 9).
24. (A, lead) [done] **Medical bed bay** as one: bed, monitor on its arm, drip stand, curtain on its track (items 7, 8).
25. (A, lead) [done] **Serving line** as one: counter run, guard, heat lamps, tray rail, the menu board over it (item 4).
26. (B, lead) [partly: the console desks stand side by side as one run with their cheeks; no separate end caps] **Control desk run**: consoles side by side join into one desk (end caps at the row's ends), the big radar
    display over the panels (items 1, 10).
27. (B) [done: feed and return lines on each rack; `l15-tank` in place of Level 3's pressure tanks in the bays] **Hydroponics feed**: the nutrient tank with a pipe run along the racks' ends (item 6).
28. (C) [done: `l15-projector` over the middle aisle's fourth row] Lecture hall: a ceiling projector over the aisle aimed at the screen.

**3. Level design**
29. (A, lead) [done: bulkheads, and a hall tag on the band a few blocks past each] The main halls' rhythm: bulkheads (22) break the long runs; the colour band stops at the bulkheads and
    doors and carries the hall's code every 16 blocks.
30. (A, lead) [done] Inset floor lights: the lit floor lights as recessed fixtures (a steel rim, a lens glowing), dead ones
    with a dark lens.
31. (A, lead) [done] The dark squares' edges: the change reads as a power fault, not a hard cut: battery emergency lamps
    (amber) on the walls for a few blocks into the dark, a tripped breaker panel at the boundary.
32. (B, lead) [done: `l15-ceiling-trough*` along both edges of the halls' ceilings] Cable trays behind grilles: runs of ceiling grilles along the halls' light strips (the trays seen through
    them).
33. (B) [done: spots `bulkhead`, `dark-edge`] Arrival views and spot check: the random arrivals keep facing along a hall; every new set piece in a showcase
    spot.
34. (C) [skipped: time] A recurring taller crossing (an atrium-like light square) now and then (round 3's skipped 9).

**4. Lore**
35. (B) [partly: an etched pilaster that falls on a bulkhead keeps its marks] Symbols etched on the beams (Wikidot): some bulkhead jambs carry the etched marks.
36. (B) [done] The codes by the vents ("eco3x10c", Fandom) and "H15": kept; the bulkheads carry the line code in the same
    stencil.
37. (C) [done: `L15WallScrawl` beside a crematorium's door, in black marker] The crematorium's hand-written "DON'T" by its door (round 3's skipped 38).
38. (C) [skipped: the placards describe levels; a camp's would read as a M.E.G. base, against DECISIONS.md] A M.E.G. placard (the shared `MegPlacard`) at a camp now and then, the Wikidot camps' explorers.

**5. Alignment with the other levels**
39. (A) [done: the detail kit's extinguisher model on 15's panel] Fire extinguishers: the level's own flat picture swapped for the mod's shared extinguisher cabinet
    (`officedeco` extinguisher / `Decor.ExtCabinet`), as the brief's shared list asks.
40. (A) [done: the block over the door, a portal on both faces with lit strips and a green cross lamp] The Medical Center door (Level 14's link in a medical bay): its surround and plate in 15's white and steel so it
    sits in the bay's wall (the door block itself is Level 14's).
41. (B) [done] The vitals monitor (8) from `l14-monitor`'s family, retinted clean; note the source.
42. (B) [done: below] "Shared assets below the bar": the hospital bed, drip stand, crash cart and bedside cabinet (Level Run), Level
    1's camp props, Level 4's office chairs: listed for the lead with what to change.
43. (B) [partly: spots done; no new F7 entries (bulkheads are everywhere, not a place to go to)] Showcase spots and F7 entries for the bulkhead, the lift lobby, the console desk, the medical bed bay, the
    serving line, the hydroponics feed and the dark edge.
44. (C) [done: rebuilt; `l120-tray` is its own level's, darker, so 15 keeps its own] Cable trays: compare with `l120-tray` and share the better one.

### What was built (code)

`tools/gen_15_r4.py` (run after `gen_15.py`, `gen_15_links.py`, `gen_15_r3.py`: it rewrites some of their shapes in place and
post-edits `l15-machine.json` and `l15-serve.json`, so the codes stay; `gen_15.py`'s panel texture gained folded seams and
corner fasteners, and every texture drawn on it was regenerated). Rebuilt shapes, same block codes: `l15-console`,
`l15-dock` (the Robo-Man's eyes lit while the dock has power), `l15-seat`, `l15-riser` (aisle step light), `l15-serve`
(now in the opaque pass, its guard a cut-out), `l15-growrack`, `l15-curtain`, `l15-hangsign`, `l15-labbench`,
`l15-locker`, `l15-tray`, `l15-machine` (every casing kind a model), `l15-stardoor`, `l15-corpse`; the lab glassware and
the spears' blades opaque (they were translucent in the opaque pass). New blocks: `l15-panel` (a white wall block with a
model on its face: the extinguisher, the ESCAPE panel, the lift's leaves in a portal with its lit indicator and call
panel, the big display's bezel, the wall displays in bezels, the hall wall lights in housings, the bulkheads' jambs and
code plates, the hall tags, the battery emergency lamp, the tripped breaker, the MEDICAL CENTER door's surround),
`l15-bulkhead`, `l15-glazing`, `l15-medmonitor`, `l15-lectern`, `l15-projector`, `l15-tank`, `l15-cagelamp`, `l15-stool`, `l15-ctable`, `l15-ceiling-trough{ns,we}`.
Generator (`WorldGenerator.L15.cs`, `InitL15Round4`, `L15WallRound4`): bulkheads on the rib every 32 blocks along the
main halls (jambs, header, tread plate), a hall tag on one wall 4 blocks after each, the cable troughs along the halls'
ceiling edges, the battery lamps and the breaker at the dark squares' edges (`L15DarkEdge`), the medical monitors over
the beds' heads, stools and tables in canteens, the lectern; layout (`WorldLayout.Level15.cs`): the lectern's flag
on one stage tile, the projector's on one aisle step, DON'T by the crematoria's doors (`L15WallScrawl`). Showcase: `bulkhead`, `dark-edge`.

### Inventions

The bulkheads (the lore has white steel beams; a portal every 32 blocks is ours), the hall tags, the cable troughs, the
battery emergency lamps and the tripped breaker tagged DO NOT RESET at the edge of the dark (the lore says lights fail
and areas go black, not why), the vitals monitors (ASYSTOLE), the lectern, the canteen's stools and tables, the door
surround of Level 14's door, the lift indicator's B3, the dead's ID cards and lanyards.

### Shared assets below the bar (for the lead)

- **Robo-Man** (`roboman`, shared with the Castle): one root element and its children, painted toy-robot boxes; the lead
  asked for joints, panels and a lit eye. Rebuilding it would change the Castle's guard too, so it is left alone here;
  what I would do: disc joints at shoulders, elbows, hips and knees, a riveted chest plate standing off the torso, the
  key turning on its back, the eyes as emissive lenses (glow) with a visor, the antenna bulb glowing.
  Done 2026-11-14: rebuilt in `gen_models.roboman`; the docks' copy follows it through `gen_15_r4.dock_shape`. The castle it guards is Level 94's (Motion).
- **Hospital bed, drip stand, crash cart, bedside cabinet** (`hospitalbed`, `run-ivstand`, `run-crashcart`,
  `run-bedside`): they read well enough beside 15's new monitors and curtains; the bed's bedding is plain slabs (a
  folded blanket and a dented pillow would lift it) and the drip stand's bag is small at a distance.
- **Level 1's camp props** (tent, sleeping bag, cardboard boxes, folding chairs): the boxes are cubes with a picture of
  tape on them (no flaps, no crushed corner); the tent is good.

### Balance notes for the lead

- Light: the battery emergency lamps (`l15-panel-emerglit`, amber, light 7): one still burns on one wall within 8
  blocks of the lit side (the others there, within 16 blocks, have run flat); it lights a few blocks round it at the very edge of the dark. The Robo-Man
  needs the dark: these edges are a little less dark than before. The vitals monitors (light 4), the lectern's lamp (5)
  and the door surround's cross (6) are in lit rooms.
- Drops: the glazing drops shards as the old thick glass did; the new stools, tables, lectern and monitors a little scrap
  wire or a bracket, like round 3's props; nothing edible or drinkable.
- The service passages' lit lamps were the shared warm dim lamp; they are now `l15-cagelamp-lit` (cool white, light 13),
  so the passages are a little brighter where they had a lamp (the dead and failing ones stay dark).
- No bed, water or shortcut changed. The canteen's folding chairs became stools (no seat behaviour lost: neither sits).

### What the shots showed

Three client-rig runs, no torch (the halls' own white): `%TEMP%/backrooms-shots/15-r4a`, `15-r4b`, final `15-r4c`.
- **Run 1** (after the A items): the control room read at once as a room of operators' desks (monitors on necks, keyboards,
  the radar in its bezel), the medical bay as a ward (monitors over the beds' heads, pleated curtains on their tracks), the
  lift as a lift (portal, B3 lit, call panel), the bulkheads and the inset floor lights as the halls' new rhythm, the
  dock's Robo-Man with its eyes lit, the framed glass along the corridors. Wrong: the serving line was ghostly white (the
  whole block in the translucent pass) and its keyboard-like trays read as slabs; the consoles' keyboards were four big
  keys (UV); the lift indicator was two boxes with a gap; the bulkhead header too like a rib; the battery lamps tiny.
  Fixed: the serving line moved to the opaque pass with a cut-out guard, keyboards remapped, the indicator joined, the
  header made deep with its hazard strip, the lamps larger.
- **Run 2**: all those read; the hall tags, the troughs along the ceiling edges (coloured cables behind the grille), the
  machine casings' relief (corner posts, louvres, bezels) and the lectern beside the screen showed. Wrong: the first
  bays of the dark were lit amber from wall to wall by the battery lamps (the dark-hall spot was no longer dark). Fixed:
  one lamp still burns on one wall at the very edge, light 7; the others have run flat.
- **Final run** (`15-r4c`, 46 shots): the edge of the dark now reads as a power fault (one amber pool on the wall, then
  black), the dark hall is dark again, the projector hangs over the lecture hall's aisle with the lectern on the stage,
  the star door has one star with its halo, the pilasters stand off the walls as I-section columns, the nutrient tanks
  and the caged service lamps are in. Not looked at closely in a shot: the MEDICAL CENTER door's surround and the DON'T
  by a crematorium door (no spot reaches them; checked in the shape previews).

**Still weak.** The service passages are still bare grey concrete with Level 2's warm duct; the hydroponics racks' posts
read heavy close up; the side corridors between the halls are plainer than the halls; the Robo-Man itself (shared).

### Questions for the user

Answered 2026-11-14: see OPEN-QUESTIONS.md (this list and the earlier ones). Robo-Man rebuilt once for Level 15 and Level 94's castle (done 2026-11-14); bulkheads every 32 blocks; keep the battery lamp and DO NOT RESET breaker; medical bays sleepable.

- The Robo-Man is shared with the Castle: rebuild the one model for both (joints, panels, lit eyes), or give Level 15 a
  service-robot look of its own and leave the Castle's toy robot as it is?
- The bulkheads cross the main halls every 32 blocks: the right rhythm, or should they be rarer (every 64) so each one
  is more of a landmark?
- At the edge of the dark, one battery lamp still burns and a breaker is tagged DO NOT RESET (our invention, telling the
  power fault): keep it, or keep the edge a hard cut into black as the lore has it?

**Checks** (2026-11-03). `expclash` clean; mod and mapgen build, 0 errors; `BACKROOMS_NO_EXP_ENTRANCES=1` layouthash at
layout versions 1 and 12: levels 0-20 and the `layout hash` line identical to main's saved files; `regions` 60/60 in
Level 15; `15stats 4` OK (0 rooms cut off, 60/60 lit arrivals, dark 17.7%); headless dummy (port 43166) twice and a
Robo-Man put down on it: 0 missing blocks, 0 error lines; no translucent texels in any opaque-pass texture of the level's
blocks; `GATE_TAG=15g python tools/gate.py --fast --port-base 43160`: PASS (17257a86).
