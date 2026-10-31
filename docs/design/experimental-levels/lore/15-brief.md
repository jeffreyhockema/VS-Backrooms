# Level 15 "Futuristic Halls": lore brief and build plan

Sources read in full: Wikidot https://backrooms-wiki.wikidot.com/level-15 (French-wiki rewrite, the "Enric" version; its difficulty field is an unfilled template) and Fandom https://backrooms.fandom.com/wiki/Level_15 (Class 1, "Rewrite in Progress", read via API wikitext). They are two quite different pages with the same bones.

## 1. Lore

**Agreement (build these first).**
- A labyrinth of clean, white, "futuristic" corridors. Wikidot: "white or gray concrete, with beams of white steel lining up against the walls and ceilings", large lights "on the walls, ceilings, or ground". Fandom: white walls of "aluminum alloys, composite materials, stainless steel", floor "usually ceramic with occasional carpet or non-slip coatings".
- Constant mechanical noise. Wikidot: "Sounds of engines can be heard from afar". Fandom: "A constant buzz echoes through the hallways", with distant beeping; sound carries far.
- Side rooms of machines behind heavy security gates (Wikidot: reinforced metal doors, one wall of thick glass; Fandom: "large, futuristic security gate ... disabled"). Machines "range in size from a laptop to devices of monolithic proportions". Many do nothing; Fandom says they are ordinary appliances (coffee machines, 3D printers, computers) "stripped of their inner machinery".
- Lights flicker, spark and short out when big machines draw too much power; whole areas can go dark (Fandom); Wikidot has "occasional pitch-black areas created by the absence of any lighting".
- Other room types: laboratories, storage, control rooms, dormitories, kitchens (Wikidot); lecture hall with stage, desks, vaults, food-service appliances (Fandom "The Facility"). Mostly empty of furniture.
- Computers and display panels on walls and machines. Fandom control panel text: "Access denied: Level 5 clearance required to change reality."
- Wall codes: Fandom scribbled arrows in vents ("H15", "eco3x10c", H = lab, e = storage); Wikidot arabesque symbols etched on beams. Fandom: black (vantablack) numbers on room walls.
- Entrance (both pages, near-identical): an immense white wall rises at the edge of Level 10's field, with a small reinforced door in it. The door later vanishes. Leaving is very hard. The level is practically infinite.
- Nothing native alive: Wikidot "No entities have yet been discovered"; Fandom "lacks any sort of life whatsoever". Resources scarce (Fandom "devoid of resources"; Wikidot says Almond Water is "notable by its absence"). Both are low-violence, high-isolation.

**Disagreement and my choice.**
| Topic | Wikidot | Fandom | Choice |
|---|---|---|---|
| People | Lab-coat corpses with dried blood, makeshift knives and spears, no firearms though some wounds are gunshots; abandoned camps; burnt Hounds in a crematorium room; stranded wanderer Enric in a control room | No people; isolation effect, no two wanderers can meet, electronics fail | Corpses and abandoned camps for storytelling; no living base |
| Air | Not described | Immaculate, AQHI 1.00; self-cleaning (trash vanishes); bradycardia, dizziness and CO2 rising in dark or power-out zones | Clean air in lit halls; bad air in the dark (a mild fatigue/slow effect is my suggestion) |
| Machine rooms | Some work (steel rods), some exploded, glass cracked not broken | Dead and empty | Mostly dead; a few "running" for sound; some wrecked |
| Geometry | Normal | Non-euclidean: oddly angled beams, pillars out of the floor, wooden doors in walls | Normal grid with a few of Fandom's oddities |
| Space exit | Doorframe in an empty machine room, night sky, blue star, 2 hours from camp | Absent | Include as one landmark room (nice) |

Other Fandom details: wall panels show other levels (Level 18 as rainbow hallways, the Storm Chaser); when power drops the machines emit "a faint, persistent ticking sound that resembles a human heartbeat" that slows until power returns; ventilation grilles, axial fans, AHUs; "Disappearances are common." Other Wikidot details: terminals run "Avalon 2.4" and show a radar of levels as shapes with green connection lines.

Confidence: high on look and sound (both agree), medium on entities (no canon; only the burnt Hounds hint). Survival class: Fandom Class 1; I would treat it as Class 1-2: scarcity and darkness are the threat, not violence. Exits: Fandom lists a dozen contradictory, "unstable" exits; Wikidot has only the star door. Because this level is cheats-only, write the Level 10 wall door as the entrance and leave the exit as unknown or the star door.

## 2. Build plan (mod terms)

Round region, indoor, 32-block cells, band ~40 blocks, hall height 4, machine halls 6 to 8.

**Must**
- Layout: lit main corridors every 4 cells (4 wide, 4 high) with side branches, each guaranteeing connectivity; between them, wings chosen by hash and planned once through the PlanCache pattern used by L120/L52: machine room 35%, lab/storage 25%, dormitory/kitchen 10%, control room 8%, lecture hall 5%, wrecked machine room 7%, blank white room 10%. A machine room is entered through an always-open gate prop with a dead hand scanner beside it. Rim carved passable.
- Zones: lit white halls; power-out clusters (2-4 cells, pitch black, ticking heartbeat); bare concrete service/vent corridors with grating floor.
- Blocks/textures: white panelled concrete wall, steel beam trim with arabesque etching, ceramic floor, grating, ceiling panel with LED strip (steady and flicker variants), black room-number decals, dead wall display. Reuse glass.
- Light: cool white, bright (about 10-12) in halls, some flicker, zero in outages; cool fog tint, no dust haze.
- Sound bed: low machine hum, distant engine thrum, sparse far beeps, air-handler whoosh in vents, heartbeat ticking in outage zones.
- Loot: lockers and cabinets in storage rooms with scarce water and food; reuse metal parts (brackets, nails, copper from cabinets as in Level 2). Almond Water rare.

**Should**
- Props: machine cabinets in several sizes (reuse L120/Level 2 models), rod press and conveyor, desks, lab benches, cots, stainless counters, wall panels, vent grilles, dead terminals, lab-coat corpses (reuse corpse entity) with makeshift spears, abandoned camps, a crematorium room with bone piles, one "radar" screen prop, the "ESCAPE" panel as a readable prop.
- Entity (lore says none): reuse `roboman` (mechanical, existing) as a rare slow patrol in the dark zones, plus bones. That is my suggestion, not lore; keep it light. Handbook and notes should say "nothing alive that anyone has proven."
- 4-6 notes, one handbook page.

**Nice**
- Star-door room: empty machine room, doorframe onto a black sky and a small blue emissive sphere, mild glow only, far from the middle.
- Oddities: angled beams, pillar stubs in floors, a wooden door set in a wall.
- Wall panels cycling images of other levels; items dropped in lit halls vanish later (self-cleaning).

**Wanderer note ideas** (mine, built on lore hooks)
1. "A white wall at the edge of the field, and a small door in it. The door was gone two days later."
2. "The hum never stops. When the lights die the machines tick like a heart, slower and slower. Do not wait for it to stop."
3. "Letters and numbers on the vents. Someone here had a system. I don't."
4. "Lab coats, spears, months dead. Some were shot, but I found no guns."
5. "Two hours out: a frame with no door, and a blue star. I did not stay."
6. "Everything is clean. Even the tin I dropped is gone by morning."

**Handbook outline**: look and air; the hum and the dark; machine rooms and gates; what the dead left; water and food; the Level 10 wall door; the star door; advice (stay lit, mark your way, never rest in an outage).

## 3. Open questions
1. Living base (Enric) or isolation: recommend isolation and notes only.
2. Entities: lore has none. Recommend sparse Roboman plus bones; a larger roster contradicts both pages.
3. Star door: include as flavour only; no entrance or exit wiring (cheats-only).
4. Self-cleaning and non-euclidean oddities: keep light odd geometry, drop or make optional the cleaning.
5. Radiation worry near the star: flavour text only, no mechanic.
