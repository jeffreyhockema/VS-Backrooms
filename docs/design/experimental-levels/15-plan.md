# Level 15 "Futuristic Halls": plan

Internal id **27**, `WorldLayout.Level15`, tag `15`, blocks `l15-`, method infix `L15`, region far north-west beyond the
End (`spawn + (-F, -F)`, Level 183's old slot), round, radius `max(40, spawnMacroX / 50)` (320 cells full size). Disconnected:
the cheats menu / `/backrooms goto 15` only. Reserved: `WallPattern`, `FloorKind`, `CeilingKind`, `Unders`, `Overheads`,
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
