# Level 36 "Airport": plan

Internal id **25**, `WorldLayout.Level36`, tag `36`, blocks `l36-`, method infix `L36`, region west-south-west (Level 55's old
slot, README batch 3). Linked since 2026-10-31 (see "Links" at the end): doors under an airplane sign in Levels 9 and 11 in,
the gates' flights and a restroom sink out.
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
  when the count wraps flies for 55 s (ding, cruise, descent, touchdown) and lands on a baggage carousel (`FindArrival`)
  (links, 2026-10-31: now in the gate's own level of six instead; see "Links").
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

### Round 2 (2026-10-31): looked at in the client, fixed

**Showcase spots** (`WorldLayout.Level36.Showcase.cs`, 21 spots, all from the layout): a carousel (it waits there, out of
sight of booth 0, so the Travel Planner is put down before the booth's shot), the claim hall, a blackout stretch with a
Smiler put down (`/backrooms encounter smiler glimpse`), check-in, the Travel Agency's booth 0 with its Planner, security,
a Lost and Found office, a concourse's long view and its travelators; the nearest lit pier (its corridor, a holdroom from
the back, the runway window and jet-bridge door, the gate's sign from the corridor, the cabin from the back of the aisle),
duty free, the food court, the lounge, the Meeting Place (from behind its kiosk first, waiting for its Planner, then from
the north), a service maze, the Absolute Limit at the end of the centre line's concourse. `mapgen 36shots` prints them
with the tile at each one's feet and how far the view runs clear.

**What changed after looking** (shots `%TEMP%/backrooms-shots/36-r2b`, final `36-r2c`):
- Light (the review's dark wedges): the halls' lights were 17 bright and only every other panel gave light, rows 13 apart
  in the claim hall. Now every panel in a row gives light, rows six apart (claim hall four rows, check-in three, the
  concourses three, a grid in each junction and over the whole Meeting Place, six apart in the food court, duty free and
  the corridors), and rooms seven high and more take a new `l36-light-high` (20; `on` 18 for the low rooms). Security two
  rows, still dimmer. The halls are now lit evenly; a first try at 26 washed them out white.
- Columns (my invention, for scale and landmarks): 2 x 2 between the claim hall's modules and down check-in's middle,
  eight in the food court, a ring of eight round the Meeting Place's atrium.
- The Travel Agency: its fascia hung nine high was out of sight. Booth 0 now stands under its own purple canopy five
  high (the fascia hangs from it over the desk); the Meeting Place's desk is a purple kiosk (canopy, back and side walls,
  open to the meeting point; the flight screens over the Planner) instead of a desk in the open with its sign and the
  atrium's screens fourteen high where nobody could see them.
- Duty free: the shop fronts either side of the door are glass (Level 3999's storefront glass), so the stock shows.
- The gate screen's board named gate C14 at every gate (against the sign over each holdroom): it now names the flight
  and where it goes, gate "--".
- The rim: where a concourse ran into the next region its end was open (the other level's sky and a tree showed). The
  tiles on the region's very edge are now a wall of static, floor to band.
- Arrivals face east, out over the claim hall (`L36Arriving`), not wherever the player last looked.

**Checked in the shots**: carousel number (not mirrored), belt and flaps; check-in screens' halves read FLIGHT TO GATE
COUNT left to right; the gate sign reads letter then number from the corridor ("T 5"); holdroom seats face the window,
the podium and the gate screen at the window; cabin seats face the nose, portholes on the cabin's sides; security lane
(X-ray, arch, podium) faces right; travelators run, comb plates at the ends; the Absolute Limit's static; the blackout
is black but for its failing ends and the lit junction beyond. Not seen: the Smiler in the blackout (put down out of
frame), the boarding and the flight (need a player to wait for a count).

## Links (2026-10-31)

LINKS.md's "Level 36" section, built. Code: `src/Worldgen/WorldLayout.Level36.Links.cs` (the hook `L36Entrances`, the
doors, the flights' levels), `WorldGenerator.L36.Links.cs` (the door's blocks in a host), `src/Thresholds/ThresholdNetwork.L36.cs`
(the four kinds), `src/Regions/L36System.cs` (landing a flight, the sinks), harness `mapgen 12345 16000 36links [rings]`.

**In: a door under an airplane sign (Levels 11 and 9), two-way.** In a few host cells (`L36EntranceChance`: the city one
cell in 1400, the Suburbs one in 3000; own salt 0x2530, so nothing else moves) one tile of plain outside wall becomes
`Unders.L36AirportDoor` (416): in the city a building's front (an office, hotel, apartment, rowhouse or sealed block; not
a corner, storefront, party wall, column, open deck or set-back) on a sidewalk or plaza; in the Suburbs a house's plain
siding (no window, corner or chimney) over open ground (no porch, pool, roof). The wall must run on either side, facing
the same way. It is drawn as `l36-airportdoor-lower/upper` (a glazed aluminium door, a full wall cube) under
`l36-airportsign` (a backlit charcoal box, the terminal's yellow airplane tile and an arrow down); the host's wall goes on
above. Used (kind `l36-airport`), it opens on the claim hall, off the belts, beside one of the doors under the same sign
in the baggage wall (`L36Mat.LandDoor`, every fourth carousel module: one every 128 blocks), which becomes its way back
(the network's `ReturnFeature`); arriving faces east over the hall. A baggage-wall door nothing has come in by is
locked ("It's locked."). The Level 36 arrival finder is `IntoL36Landside` (the anchored `FindArrival` round the claim
hall's arrival cells). No M.E.G. placard: neither host's own gates carry one, and 36 (class 1) is no more dangerous
than either.

**Out: the flights, one-way.** Each gate's flight lands in one level, always the same for that gate, by a hash of its
jet-bridge door (`L36FlightTo`, salt 0x2532): 11, 9, 37, 3999, 188 or 10 (the user's six). The gate's screen names it
(`l36-fids-to<level>`; the `gate` board is gone, the check-in boards list only the six); the screens' chat list and
the door's lines say it too; Gate C32 still says 186 and never leaves. When the count runs out L36System asks the
threshold network (kind `l36-flight`, at the jet-bridge door, key salt 0x25C2), so a gate's flight always comes down
in the same place: standing on the level's own arrival spots (in the Poolrooms a dry deck, never the water), with
"The wheels touch. The door opens, and the airport is not there any more."

**Out: a restroom sink, one-way.** The restrooms' basins (a pair of restrooms in every pier, the lounges' showers; they
were kitchen-counter sinks) are now `l36-sink-dry|overflow` (`Props.L36Sink` 1217, `BlockBehaviorL36Sink`). Used, the
tap runs and will not turn off: the block becomes its overflowing state for 45 s (water to the rim, over the front,
a puddle). Held for 2.5 s while it overflows (the head under, as the Fandom page has it), it takes you to the
Poolrooms (kind `l36-sink`, key salt 0x25C3, each sink always to the same place), up in the water or on a deck.

**Text**: the handbook page's "Ways in and out" and the screens' and flights' paragraphs (written by gen_36_lang.py,
over gen_guide.py's PAGES["level36"], which the links brief keeps out of the level agents' hands: the lead may move the
text back at the merge), the hint line, notes l36-3 and r-l36-1, the Travel Planner's `exitssite` and `home` lines, the
new messages (`l36-arrive-door`, `l36-leave-door`, `l36-sink-overflow`, `l36-sink-arrive`, the sink's two help lines).
The Metro train, apartment doors in 11.2, luggage that falls, the hotel's glass doors (Level 42): rumours only. No notes
were added to the hosts' pools.

**My inventions**: the doors in the baggage wall as the way back (the lore gives the sign, not the far side); their
being locked until someone comes in; the door's look (an airport's glazed door, the terminal's own sign style); which
walls take a door; the flights' levels by a hash of the gate; the sink's overflow lasting 45 s and the 2.5 s hold.

**Ways between levels (rows for the guide)**:

| From | To | Way | Kind |
|---|---|---|---|
| Level 11 | Level 36 | a door under a lit airplane sign in a building's front, very rarely | two-way (back by the door in the baggage wall) |
| Level 9 | Level 36 | a door under a lit airplane sign in a house's wall, very rarely | two-way (back by the door in the baggage wall) |
| Level 36 | Level 11, 9, 37, 3999, 188 or 10 | a gate's flight, the level on the gate's screen | one-way |
| Level 36 | Level 37 | a restroom sink: turn the tap, hold your head under the overflow | one-way |

**Checks (2026-10-31)**: `expclash` clean; mod and mapgen build, 0 errors. `layouthash` (12345, 16000), layout versions 1
and 12, with `BACKROOMS_NO_EXP_ENTRANCES=1`: every line for levels 0-20 and the `layout hash` line identical to main's;
without it, no level line moved either (the hash's 24 sample cells a level hold no door). `regions` 60/60 in Level 36.
`36links` (seed 12345, full size): the city 0.30 doors a km2 (one to 3.3 km2, about 1.8 km apart; nearest the city's
middle 0.33 km off it, nearest the spawn 51.8 km), the Suburbs 0.34 a km2 (about 1.7 km apart; nearest the spawn 6.5 km,
at 507758,516974); 16 doors in 2048 blocks of the baggage wall; 152 gates in 4 x 7 superblocks: 11 x22, 9 x18, 37 x33,
3999 x25, 188 x22, 10 x32; 78 sinks. Generic `links`: L9 and L11 doors paired with a baggage-wall door each, the
baggage-wall doors locked. Headless (ports 43152, 43154; `/backrooms wayback`): the Level 9 and Level 11 doors come out
on the claim hall's floor beside a door in the baggage wall (dumped: the door and sign blocks there); those doors, used,
lead back to the spot before each host door ("written down before"); an unused one is locked; a gate of each of the six
levels lands in 188, 37 (pool tile, dry), 9 (road), 11 (sidewalk), 10 (field), 3999 (lobby carpet), feet and head in air;
a sink comes up on the Poolrooms' coping; `column` shows the door, its upper part and the sign at rel 1-3 in both hosts;
a dummy in the level; `blocksweep` 11219 blocks, 0 threw; 0 error lines. `GATE_TAG=l36 gate.py --fast --port-base 43150`:
PASS. Client shots (`shots1`, seed 424242): the city door in a mirror-glass front, the Suburbs door in a brick house
between its windows at night, the baggage wall's door, a gate's screen "TO LV3999", the restroom's sinks, the landings.
Not tested with a player: the flight's landing through `Use` (exercised as the network sees it), the sink's hold.
