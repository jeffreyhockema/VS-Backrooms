# Level 36 "Airport": plan

Internal id **25**, `WorldLayout.Level36`, tag `36`, blocks `l36-`, method infix `L36`, region west-south-west (Level 55's old
slot, README batch 3). Disconnected: the cheats menu / `/backrooms goto 36` only, no thresholds in or out.
Reserved (README): `WallPattern`/`FloorKind`/`CeilingKind`/`Unders`/`Overheads`/`Pipes`/`Decor` 416-447, `Props` 1200-1299,
title keys 2501-2599, layout salts 0x2500-0x25BF, threshold salts 0x25C0-0x25FF, headless ports 43150-43159.

The lore digest is `lore/36-brief.md` (Wikidot "Timeless Airport", Fandom "Desolate Terminal"), the user's answers
`lore/DECISIONS.md`: boarding leads to a cabin stub and back to a baggage belt; no sleeping (fatigue paused, hunger and
thirst normal), clocks frozen but not the world clock; rare Smilers/Hounds/Deathmoths only in blackouts; wings A-Z, gates
1-60; the rim is the Absolute Limit; the one new character is the **Travel Planner**, a wanderer-style NPC.

## 1. The level in this mod

Round noclip region, radius `max(40, spawnMacroX / 50)` cells (320 full size), as the scaffold. Drop 0; **band depth 14**
(`WorldGeometry.L36BandDepth`), so the band reaches 25 above the floor (the Meeting Place is 14 high; nothing lit sits in
the band's top block). Everything derives from world coordinates and `Hashing.Hash(seed, a, b, salt)` (salts 0x2501,
0x2510-0x2518, 0x2520 for flights); superblocks are `PlanCache` plans. No per-region state.

**Landside** (x in blocks east of the baggage wall `L36WallX`, a straight north-south line 3/4 of the radius west of the
centre; everything west of it is solid; modules counted from the centre line `L36LineZ`):
- 0: the baggage wall. 1-24: **Baggage Claim**, 7 high: a carousel every 32 blocks (a loop of `l36-belt` round a steel
  island, out of the wall through its flap at row 10, back in at row 14; 30 % running (they carry you), the rest stopped;
  bags on the belts; its number hung over the island); one module in 12 a **Lost and Found** office (shelves of luggage,
  a counter, heaped bags, a supply box). Benches, trolleys, a fountain, a clock with no hands on the wall every 64.
- 25: wall with 8-wide openings (one in four with an EXIT sign that leads only into check-in). 26-43: **Check-in**, 9 high:
  an island of desks every 32 (desks back to back over a bag belt, flight screens over the middle), queue mazes of
  stanchions; one module in 32 a **Backrooms Travel Agency** booth (purple wall, counter, brochure racks, the backlit
  fascia; booth 0 on the centre line), the Travel Planner behind it.
- 44: wall, wide openings. 45-56: **Security**, 5 high, dimmer: a serpentine queue, then lanes every 16 (X-ray belt and
  tunnel, the walk-through arch, the officer's podium, trays). 57: wall open where the lanes come out.

**Airside** from 58: **concourses** 16 wide, 9 high every 256 blocks each way; the north-south ones carry a pair of
travelators (Level 3999's moving walkway; one run in five stopped, all stopped in a blackout), the others a carpet runner;
seats, planters, bins, vending machines and fountains along the sides; back-to-back flight screens half way; hanging
wayfinding signs near each junction (contradicting each other; one stretch in nine its signs blank or broken); a junction
of dark marble inlay with a cluster of screens. Between them a **superblock** (240 square) of one kind:
- **Pier** (44 %, 60 % next to security): a wing letter A-Z over its mouth and twenty gates numbered within 1-60 (a third of
  the range by hash). A corridor 12 wide runs into it, ending at a runway window (or through, 30 %); either side ten
  holdrooms (seat rows facing the window, the podium, the gate screen, the letter and number hung over the mouth), the
  runway window wall with the **jet-bridge door**; behind it a short bridge and the plane's **cabin** (2-2 economy seats,
  porthole windows, overhead bins), sealed in the solid apron. One holdroom is a pair of restrooms. The **Gate C32 Support
  Group**'s camp (bedrolls, sleeping bags, lanterns, bags, two supply boxes, the c32 screen) at every C32.
- **Duty free** (14 %): a street 24 wide, 8 high, ten shops each side (perfume, fashion, books, snacks, tech, bags, cafe,
  pharmacy), each with its fascia over its door, a third shuttered (Level 3999's shutter), stocked.
- **Food court** (11 %): a hall 120 square, 10 high, stalls round the walls (counter, kitchen, fascia), tables with spoiled
  meals and paper cups, machines in the middle; ways in from all four concourses.
- **Lounge** (9 %): a first-class lounge: red carpet, reception desk, sofa groups, bookshelves, a buffet, showers, and a
  store room with a courier group's stockpile (2-4 supply boxes).
- **Meeting Place** (6 %; 12 % next to security): always the same plan (the lore's 47 positions are one place): a round atrium
  14 high, the meeting-point columns in the middle, benches, planters, the Travel Agency's desk with the Planner.
- **Service** (16 %, never next to security): out of bounds: a maze of 3-wide service corridors (dead ends on purpose), one
  stretch in eight a 2-high **vent** with fans, junk, blank signs at crossings, half of them dark.

**Blackouts**: from the third superblock east, a concourse stretch is dark with chance 0.08 + 0.02 per superblock (at most
0.3), a superblock (not the Meeting Place) 0.05 + 0.015 per superblock (at most 0.25), half of the service mazes. Lights
die, the stretch's ends flicker. **The Absolute Limit**: cells within 3 of the rim: static blocks in walls, floors and
ceilings (85 % / 40 % / 12 % by distance), lights failing; the rim wall itself static.

**Tile fields** (`L36Zone` in `Zone`; `Detail` bits 0-3 the material (`L36Mat`), 16 blackout, 32 drawn as static, 64 the
Limit; `Height` air or dressed wall height; `Overhead` 416-419 (gate sign, wayfinding sign, flight screen half, the
Agency's fascia) with `Depth` its glyph/board and `Roof` its part; `Pier` facing; `Stack` a prop's kind). Props
`Props.L36*` 1200-1216 (in Tiles.cs). Walls are dressed by `L36Dress` from their eight neighbours (height, material by
the most telling zone; a cabin's wall faces the cabin).

**Mechanics** (`src/Regions/L36System.cs`):
- Flights: each gate's countdown is a unitless number, ten a second at the default day length (`TotalHours * 1200`), with
  a period of 6,000-36,000 and a phase from the door's position; boarding under 1,000; at 0 the next flight. Using the
  jet-bridge door while boarding takes you to the cabin's aisle; from inside it lets you off again; whoever is aboard
  when the count wraps flies for 55 s (ding, cruise, descent, touchdown) and lands on a baggage carousel (`FindArrival`).
  Gate C32: 1784XBA8JLP to Level 186, 94,612,753 counting down by one every five seconds; never boards.
- Flight screens: right-click lists the six nearest flights (number, level, gate, count, status).
- No sleep, no tiring: awake hours held from arrival while in the level; anyone lying down is stood up with a line. Hunger and
  thirst untouched. The world clock is not touched; the clocks are blocks without hands.
- `l36structure` blocks (floors, walls, windows, ceilings, gate doors, flaps, static, fascias) are unbreakable.
- The handbook page is added by L36System's client side after "The Levels: Beyond the Rings" (GuideSystem's list untouched).

**Danger**: `MenaceSystem`: Threshold in a blackout, Safe elsewhere. `Roster`: Smiler (dark only), Hound (1-2), Deathmoth
female (1-2), all from Threshold; level weight 0.35. Class 1 (default). Temperature 21 C; one concourse stretch in seven
10 C and one in seven 28 C; cabins 18, vents 12. Stability 1.05, blackouts 0.95, the Limit 0.6 (drains).

**Air and sound** (`AtmosphereSystem.L36.cs`): base fog cool pale grey `(0.0045, 0.80, 0.82, 0.84)`; blackout blue-black,
service dim, lounge/food court warm, cabin bright, the Limit static grey. Titles 2501-2514 (Baggage Claim ... Lost and Found).
Beds: hum (terminal), static (Limit), cabin, service; silence in a blackout. PA chime + babble every 70-150 s, distant jets
by the windows every 90-210 s; the running belts' clatter is their block's ambient sound.

## 2. Assets

`tools/gen_36.py` runs `gen_36_surfaces.py` (+ `_tex`, `_signs`), `gen_36_props.py` (+ `_tex`), `gen_36_sounds.py`, then
`gen_36_lang.py` (the level's en.json block). Blocks (all `l36-`): marble, carpet, belt, carousel, static, wall, window
(painted runway view, 4 rows), cabinwall, wallclock, ceiling, light, gatesign (A-Z, 1-60), sign (13 glyphs), shopsign
(8 shops), fids (6 boards), fidspole; checkin, seat, gatedesk, gatedoor (`BackroomsL36GateDoor`), stanchion, scanner, xray,
trays, booth, perfume, mealtable, meetingpoint, cabinseat, lostfound. Sounds `ambient/36/{hum,belt,static,cabin,service}`,
`effect/36/{chime1-2,pa1-3,jet1-2,clunk,ding,touchdown,boarding}`. Borrowed: Level 3999's walkways, couches, planters,
bins, shutters; Level 4's vending machine and water cooler; shared detail props (benches, suitcases, backpacks, trolleys,
conveyors, café chairs, snack counters and shelves, fridges, bookshelves, clothes racks, toilets, boxes, fans...).

## 3. Content

- **Travel Planner**: a wanderer (`WandererSystem`) with site key `36`: put down behind every Travel Agency booth and desk
  (`WorldLayout.L36WandererSite`), names "Planner Ines/Okoro/Wren/Halvard", its own trade list (`config/trade/wanderer-36.json`:
  water, crackers, candy, soda, bandages, a linen sack, candles, chalk; buys circuit boards, coin mechanisms, cloth, glass,
  wire, paper) and lines in the wanderer dialogue (gen_dialogue.py's `L36_LINES`).
- **Notes** (gen_notes.py, track `l36`, 7 entries + 1 folded): the belt, the numbers, flights, Gate C32, signs, no sleep,
  the edge; folded: ways in as told. Spots: by each Planner, in each Lost and Found office, folded by each C32 podium.
- **Handbook**: "Level 36: the Airport" (gen_guide.py `PAGES["level36"]`).
- **Loot**: suitcases and backpacks on belts, floors and shelves (their own drops), supply boxes in Lost and Found offices,
  one holdroom per pier, C32 (two), lounge stockpiles (2-4), food courts (half), dark concourse stretches, service mazes,
  open shops (12 %); machines and fountains give Almond Water.

## Detail pass (2026-10-30)

**Built**: everything above, from an empty scaffold.

**Choices against the brief**: baggage claim is a straight hall along a straight west wall (the brief's "westmost 3 cells"
of a round region): the lore's one bounded edge, so arrivals and booths line up; the rest of the rim is the Limit.
Concourses every 256 (brief: 128) so superblocks are big enough for a 20-gate pier. Pier gates are numbered within one
third of 1-60 per wing (20 gates a wing) rather than 60 per wing. The cabin is parked behind each gate (not a separate
pocket): you are teleported through the door, which keeps the fiction physical. Landing is on any carousel near the hall's
middle (`FindArrival`), not the nearest. Fatigue is held rather than paused in code (no change to the needs system). Held
clock items: the mod has none, so only the wall clocks. Temperature bands are per concourse stretch (no overlapping
hot/cold messages). The Travel Planner wears the wanderers' clothes (no purple vest: that would need its own entity type).

**My inventions** (not lore): carousels that carry you; the Lost and Found offices' layout; Travel Agency booths every 1024
blocks besides booth 0; flight periods, the 55 s flight and its lines; the trade list; the note texts and writers; the Limit
draining stability; temperatures; the Planner's names; the shop brands ("Maison Veau", "Lostwear", "Page & Gate", ...).

**Left out**: slow healing and afterimages (should: no cheap mechanism); the Meeting Place's BTA staff walking through;
the Support Group as people (props and notes only, as DECISIONS allows); non-Euclidean wrap-around concourses; Wi-Fi;
lounges' gyms; poisoned cafe food as an item (the tables are props, the handbook warns); the hallucinations at the Limit
beyond the stability drain; held clocks.

**Check in-game** (screenshots): a carousel (belt direction and the flap, the island, its number), check-in islands and their
screens over the desks (halves left/right), the Travel Agency booth and fascia order, the security lane (scanner arch walk
through, X-ray facing), a concourse (travelator ends, side seats facing in, screens back to back, signs facing travellers),
a holdroom (seats facing the window, podium, gate sign letter left of number from the corridor, the runway window rows),
the cabin (seats facing the nose, portholes on the cabin side), a duty-free street (fascia l/m/r order, shutters), the
food court stall fascias, the Meeting Place, a service maze and a vent, a blackout stretch, the Limit's static. Boarding:
use a boarding door, wait for 0, the flight, the landing on a belt. Sleep refusal on a bed placed in the level.

**Harness** (2026-10-31): `expclash` clean. Mod and mapgen build, 0 errors. `layouthash` (seed 12345, 16000; layout
versions 1 and 12): every line for levels 0-20 and the `layout hash` line identical to main's (`18cfdbc1c530f039`,
`26f51e4b3d0326bf`). `regions`: 60/60 arrivals, none wrong or in small pockets, full size and `SPAWN=1000`; 0.5-0.8 ms a
cell (cold). `36stats 3` (landside and 3 x 3 superblocks): walls 61 %, concourses 11 %, holdrooms 8 %, shops 4 %; every
floor tile reached from a carousel but the cabins and bridges (sealed: boarding only), shuttered shops and what the window
cuts off; `36stats 5`: 10 piers (190 gates), 4 duty frees, 4 food courts, 3 lounges, 3 Meeting Places, a service maze;
blackout 12 % of the floor. `36map` (+ `tools/mapgen/render_36.py`) drawn round the centre line and at the south rim
(the static band follows the rim's curve). Headless (ports 43152-43153, seed 12345): `/backrooms dummy place 36 5` lands
on a carousel at 374246,564154 (light 9), 0 error lines, 0 missing blocks; `blocksweep` 9365 blocks, 0 threw;
`encounter smiler|hound hunt`, `deathmoth-female stalk` put each down by the dummy (danger 0.35); `wanderers spawn` gives
"Planner Ines", site 36, 7 wares for sale and 5 wanted. `GATE_TAG=l36 python tools/gate.py --fast --port-base 43150`:
PASS (generators, lang, build, boot, harness smoke). Not tested headless (needs a player): boarding, the flight and the
landing, the flight screens' list, the sleep refusal, the handbook page, the Planner put down at its booth.
