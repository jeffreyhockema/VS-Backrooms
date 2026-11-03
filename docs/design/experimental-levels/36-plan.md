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

## Round 3 (2026-11-01): the detailed visual pass

The user: "more detailed visuals, multi-block objects and signs where necessary; new more realistic layouts; continue to
align with lore". The lead's notes on round 2's sheet: the big halls are bright and empty; gates want a counter with its
screen and the gate sign over it, seat rows, bins, charging posts, a window wall onto a jet bridge and a plane's nose; shops
along the concourses with their names; phones, ATMs, lost and found, restrooms with stalls, a prayer room, an information
desk; hanging signs with arrows and words; departure boards in more places; pillars with posters; planters, trolleys,
benches, fountains, a shoe-shine stand; the Meeting Place's purple cube; the claim hall's carousels, screens and customs;
ceilings all slats.

### List

Tiers: A must, B should, C nice. Ticks: `[done]`, `[partly: ...]`, `[skipped: why]`.

**1. Layout realism**
1. (A) [done] Concourse frontage: the superblocks' faces onto the concourses are blank walls for 240 blocks. Carve units along
   every superblock edge (not the service mazes, not where a hall opens): shops with glass fronts and fascias (newsstand,
   cafe, pharmacy, duty free, bureau de change), a services alcove (payphones, ATMs, a drinking fountain), restrooms, a
   prayer room, an information desk, a shoe-shine stand, so a concourse reads as an airside street.
2. (A) [done] Gate counter: each holdroom's lone podium becomes a gate counter (two desks and the podium in a row, the screen on a
   post) with the gate's sign (letter and number) hung over it, as at a real gate.
3. (A) [done] Claim hall flow: customs at the claim hall's way out (green NOTHING TO DECLARE and red GOODS TO DECLARE channels
   over the openings into the landside hall), a customs bench on the red side.
4. (B) [done] Check-in: an information desk with the "i" over it in check-in (one module in 32, opposite the Agency's).
5. (B) [done] Trolley bays in the claim hall (a row of nested luggage trolleys by every other column).
6. (C) [done] Pier corridors: moving walkways in runs down the middle of long piers.
7. (C) [skipped: the M.E.G. placard is a danger-class sign, not a lounge; the lore gives no look to build from] A Concourse M lounge for the M.E.G.'s Track Mappers (lore) rather than a plain lounge when the pier letter is M.

**2. Multi-block objects**
8. (A) [done] The plane at the gate: the window panels round each jet-bridge door painted as one picture (the bridge's tunnel
   running out to a parked airliner's nose, cockpit windows, the fuselage), 9 wide x 5 high, so a holdroom looks out at
   its plane.
9. (A) [done] The Meeting Place's marker: the classic meeting-point sign, a tall pillar topped by a lit cube with the pictogram
   and MEETING POINT on four faces, instead of the stubby column.
10. (A) [done] The Travel Agency kiosk (Meeting Place) and booth 0 (check-in): today a solid purple box from floor to the band
    (the canopy's wall runs up to the atrium's ceiling). A real kiosk: purple panels five high, the canopy, open air above,
    the BTA logo on its outer faces.
11. (A) [done] Departure boards: a big wall-mounted DEPARTURES board (4 x 2 blocks) in check-in and facing every junction, an
    ARRIVALS / baggage board in the claim hall.
12. (B) [done] Carousel screens: a screen at each carousel's head naming its flight (FROM LEVEL .., FLIGHT .., ON BELT).
13. (B) [done] Restroom stalls: toilet cubicles (partitions and doors) instead of toilets in the open.
14. (B) [done] Charging posts between the holdrooms' seat rows (the lore's outlets and USB ports).
15. (B) [done] Payphone bank and ATMs as models (in the services alcoves).
16. (B) [done] A drinking fountain model (stainless, bi-level) for the lore's Almond Water fountains.
17. (B) [done] Shoe-shine stand (two raised chairs on a platform).
18. (B) [done] The food court's stalls: menu boards over each counter (lit, two blocks wide), more stall kinds (noodles, burgers,
    coffee, pizza) with their fascias.
19. (C) [done: duty-free units have gondolas of bottles and perfume counters; news units shelves] A shop's interior: duty free gondolas of bottles, a newsstand's magazine racks.

**3. Signs and text**
20. (A) [done] Wide hanging wayfinding signs with words and arrows (three blocks: pictogram, words, arrow): GATES A-Z ->,
    BAGGAGE CLAIM, EXIT, SECURITY, CHECK-IN, TOILETS, MEETING POINT, FOOD COURT, DUTY FREE, LOUNGES, TRANSFERS, in place
    of the one-block pictogram boxes over the concourses.
21. (A) [done] Fascias for every new unit: NEWS, CAFE, PHARMACY, DUTY FREE, BUREAU DE CHANGE, PRAYER ROOM, INFORMATION, LOST
    AND FOUND, TOILETS, SHOE SHINE, PHONES.
22. (A) [done] Posters on walls between the units: the Backrooms Travel Agency's purple posters (lore: "every level is only one
    flight away", "remember to eat"), invented ads, a lost-luggage notice, a BTA notice that the clocks have stopped.
23. (B) [done] Pillars (the columns of the claim hall, check-in, food court, Meeting Place) carrying posters.
24. (B) [done] The Lost and Found office's own fascia over its door.
25. (B) [done] Customs signs (item 3) and a "Welcome" banner over the claim hall's openings (the lore's multilingual placards:
    WELCOME / BIENVENUE / WILLKOMMEN / BIENVENIDOS).
26. (C) [skipped: the TOILETS fascia and hanging sign say it] Restroom doors with the men/women pictogram.

**4. Detail visuals**
27. (A) [done] Ceilings: the steel slats everywhere. Coffered ceilings (deep square coffers) in check-in, the junctions and the
    Meeting Place; skylights (the lore's dim grey sky) down the food court and over the Meeting Place's atrium; wood slats in
    the lounge; plain tiles in the shops (kept).
28. (B) [done] Walls: a stone (travertine) dado on walls facing the concourses, piers and streets (up to four blocks), so the panel
    grid is not the only finish.
29. (B) [done] More bags on the running belts and round the carousels (Fandom: "luggage seemingly abandoned").
30. (C) [skipped: the halls stay evenly lit (round 2 chose that); the blackouts are the dark] Light rhythm: brighter pools over the seating, the corridor between dimmer (the halls still read as lit).
31. (C) [skipped: the grey border rows already frame the concourses] Floors: a marble border pattern along the concourses' edges.

**5. Lore alignment**
32. (A) [done] The Meeting Place is one place in 47 positions: the same marker, kiosk and benches every time (kept), its marker now
    reads as a meeting point.
33. (B) [done] BTA's purple signs: the posters and the kiosks' outer panels (lore: "purple signs").
34. (B) [done] Charging posts: the lore's "seats and tables with outlets and USB ports" (item 14).
35. (C) [done] Water fountains give Almond Water (as the coolers do): the fountain model takes the cooler's behaviour if it has one.
36. (C) [done] "Clothing laying all over the chairs": more coats on seats in some holdrooms.

**6. Released-level alignment**
37. (A) [done] Every new block named in the HUD (en.json, `block-l36-...`), pick-block works (creative inventory entries).
38. (A) [done] Showcase spots for each new set piece (the frontage, a gate counter with its plane, the departures board, the
    meeting marker, the customs channels, a restroom's stalls), computed from the layout.
39. (B) [done] The handbook page mentions the Meeting Place's marker and the BTA's posters (one line, in the page's voice).
40. (B) [done] New blocks unbreakable where they are structure (`l36structure`), like the rest of the level.

### What was built (round 3)

- **Concourse frontage** (`L36LayFrontage`): every superblock but the service mazes carves units 17 wide into its edges where
  its own plan left them solid (a unit is skipped where a pier's corridor, a hall's way in or anything else comes through),
  fronts on the concourse: shops behind glass with a fascia over the door (news & books, duty free, the cafe, the pharmacy,
  a bureau de change with a departures board behind its counter, books, tech, fashion, snacks; a quarter shuttered), a
  TELEPHONES alcove (payphones, cash machines, Almond Water fountains, benches), restrooms (cubicles, basins), a prayer room
  (rows of chairs, books, plants), an INFORMATION alcove (the desk, screens, the "i", a departures board), a SHOE SHINE
  alcove (six raised chairs); a fifth of the stretches are plain wall with a departures board or posters. Alcoves are six
  deep, shops and rooms ten. A poster on the wall between each two units.
- **Gates**: the gate counter (two check-in desks and the podium facing the room, the gate's letter and number hung over
  it); charging posts at the ends of the seat rows; the nine window panels round the jet-bridge door are one painted
  picture (`l36-apron`): the jet bridge running out to a LIMINAL AIR airliner parked nose-in; one holdroom in four has
  coats left over a third of its seats; pier corridors have moving walkways in two runs each way.
- **Landside**: customs on the way out of the claim hall (green NOTHING TO DECLARE / red GOODS TO DECLARE wide signs over
  the openings, a customs bench; one opening in four the EXIT that leads into check-in); the ARRIVALS board or the WELCOME
  banner (five languages) on the claim hall's side of its east wall, DEPARTURES boards on check-in's side; a screen at each
  carousel's head (BAGGAGE BELT n, from where, ON BELT); more bags on the belts; trolley bays; posters on the columns; the
  Lost and Found's fascia; an information desk under its "i" in check-in one module in 32; notices on security's wall.
- **Meeting Place**: the meeting-point sign (a lit 2 x 2 x 2 cube on a post, the pictogram and MEETING POINT on four
  faces) in place of the stubby column; the Travel Agency's kiosk is five high with open air above it (it had been a solid
  purple box to the atrium's ceiling: walls are columns in this generator), its canopy purple, the Agency's posters on
  its back; the same for booth 0's back wall in check-in.
- **Signs**: four-block wide wayfinding signs (pictogram, words, arrow: All Gates, Baggage Claim, Exit, Meeting Point, Food
  Court, Duty Free, Lounges, Toilets, Transfers...) over the concourses in place of four boxes each saying something else;
  twelve new fascias; eight posters (three of the Agency's: "Every level is one flight away", "Remember to eat", "The
  clocks have stopped"; three invented ads; the unattended-baggage notice; a wanderer's taped-up "Don't trust the exit
  signs / Empty sign = no good"); four menu boards; and a fix to every hanging sign and screen: their faces showed only
  the top five eighths of their picture (the lettering cut off at the bottom since round 1).
- **Finishes**: coffered ceilings in check-in, the junctions and the Meeting Place; skylights down the duty-free streets,
  in bands across the food courts and over the meeting point; oak slats in the lounges; a travertine dado (two blocks and
  a capped course) on the panel walls of the public halls.
- **Food court**: stalls are cafes, snack bars, noodles, burgers or pizza, each with two menu boards beside its fascia.
- **New blocks** (`tools/gen_36_detail.py`): `l36-art`, `l36-apron`, `l36-colposter`, `l36-meetbox`, `l36-meetpost`,
  `l36-finish`, `l36-charger`, `l36-payphone`, `l36-atm`, `l36-fountain` (BackroomsDispenser, as the coolers),
  `l36-shoeshine`, `l36-stall`; Tiles.cs: `Props.L36KioskWall`...`L36Stall` (1218-1224), `Overheads.L36Art`/`L36Apron`
  (420-421), `CeilingKind.L36Coffer`/`L36Skylight`/`L36Wood` (417-419); `Tile.Detail` bit 7 on a wall is the dado.

### Inventions (round 3)

The airline LIMINAL AIR on the plane (it was on the check-in counters already); the stall brands (Noodle Gate, Burger Bay,
Slice) and their menus and prices; the posters' words (the Agency's are the lore's own phrases); the frontage's mix of
units; customs at all (the lore has the belt as the way in; a claim hall without customs read wrong); the meeting-point
sign's look (the lore says only that the 47 positions are one place).

### Balance notes for the lead

- More Almond Water: every TELEPHONES alcove (about one frontage unit in eight) has two drinking fountains
  (`l36-fountain`, the coolers' dispenser). The concourses already had a cooler every 72 blocks.
- More supply boxes: an open shop on a concourse has a 10 % chance of one (as the duty-free shops' 12 %). A frontage unit
  is about every 20 blocks of concourse wall, so roughly one box per 400 blocks of wall more.
- No beds, safe rooms or food sources were added; the restrooms' basins in the new units are decorative (not the linked
  sinks).

### What the shots showed

- Run 1 (`%TEMP%/backrooms-shots/36-r3a`): the frontage, gate counters, the plane at the gate, boards, posters and the
  meeting-point sign all read; the customs signs, the wide signs and the gate signs had their lettering cut off at the
  bottom: every hanging sign and screen face mapped only the top five eighths of its picture (the shape's default UV, a
  round-1 bug, visible in round 2's "T 5" too). Fixed by mapping the whole picture. The services and shoe-shine alcoves
  were big empty boxes (now six deep, more chairs, benches, fountains, boards); columns mixed two posters (now one per
  column); the kiosks' canopy showed a white band (now purple); the information desk's spot looked at a column.
- Run 2 (`36-r3b`): signs read in full ("Nothing to Declare / Goods to Declare", "Food Court", "T 5"); restrooms' cubicles,
  shallow alcoves, the purple canopies; arrivals and departures boards legible.
- Run 3 (`36-r3c`, final, sheet `%TEMP%/backrooms-shots/36-r3c/sheet.jpg`): as run 2, plus the duty-free gondolas and
  the pier walkways. Still weak: the concourse walls above the shopfronts (rel 6-9) are plain panel; the halls stay evenly
  bright (round 2's choice); the meeting-point cube is small in its 14-high atrium; the information desk spot frames it
  from the side.

### Checks (round 3)

`expclash` clean; mod and mapgen build, 0 errors; `layouthash` (12345, 16000; layout versions 1 and 12;
`BACKROOMS_NO_EXP_ENTRANCES=1`): every line for levels 0-20 and the `layout hash` line identical to main's saved files;
`regions` 60/60 in Level 36; `36stats 3` runs (unreached tiles are shuttered shops and rooms cut by the sampled square's
edge); headless (port 43157): `/backrooms dummy place 36 5` lands (light 12), 0 error lines, 0 missing blocks,
`blocksweep` 12435 blocks, 0 threw; `GATE_TAG=l36 gate.py --fast --port-base 43150`: PASS (be6c01c5).

### Questions for the user

1. Customs on the way out of the claim hall (green and red channels) is my invention: the lore brings you in by the belt
   and says nothing of customs, but a claim hall without it read wrong. Keep it?
2. The new restrooms along the concourses have plain basins, not the linked sinks (Level 37): the links' frequency is not
   this round's. Should they become linked sinks later (many more ways to the Poolrooms)?
3. The Meeting Place's sign is the real airports' meeting-point cube. The lore's "47 positions, one place" could also be
   shown (a placard naming the position, "MEETING PLACE 23 OF 47"): wanted?

## Round 4 (2026-11-02): the asset-quality pass

The user: "another in depth visual pass ... multi block elements where necessary ... high quality, AAA quality, assets ...
continue refining level design ... general Backrooms lore, specific lore ... aligning to our other levels (sharing assets
where possible ...)". The lead's notes on round 3's sheet: seat rows with armrests, legs and a beam; check-in counters with
monitors, scales, belts; security's X-ray with belt and curtains, an arch, trays; the carousel with a sloped belt and bags; the
jet bridge as a run of elements with a glazed side; the information desk with a screen; trolleys with baskets; shops with
goods behind glass, a till, a lit fascia; cafe counters with coffee machines, a display case, stools; vending; planters; the
prayer room's mats; restroom cubicles and basins; the big halls' structure (a space frame or coffers with skylights, clad
columns, a floor pattern that breaks the field, hanging wayfinding, a mezzanine edge); the meeting-point sign tall enough for
the atrium; the kiosk's canopy; the departures boards lit.

Round 3's own "still weak": the concourse walls above the shopfronts are plain panel; the halls evenly bright; the meeting
point small in its atrium; the information desk framed from the side.

### List

Tiers: A must, B should, C nice. Ticks: `[done]`, `[partly: ...]`, `[skipped: why]`. Element counts are round 3's.

**1. Assets to rebuild to the bar**
1. (A) [done: edge / corner / deck by its neighbours] `l36-carousel-island` (1 box): the carousel's centre as a real object: a stainless hood with a sloped top, a raised
   spine, a black rubber bumper at the belt, a kick plate, bolted seams, rounded end caps.
2. (A) [skipped: the round-1 crescent-plate texture holds up in the shots] `l36-belt-run/still-*`: the belt as overlapping crescent plates (rubber seams, scuffs, a sheen), not stripes.
3. (A) [done] `l36-carousel-flap-*` (6): the belt's mouth in the wall: a steel portal with a hazard-striped lintel and a curtain of
   separate rubber strips (one swung aside).
4. (A) [done: checked, already at the bar (monitor, printer, belt, hood, lit scale display)] `l36-checkin-desk-*` / `l36-checkin-scale-*` (23 / 15): bevelled laminate front with a stainless kick and top rail,
   the agent's monitor on a stand (lit screen, back), a boarding-pass printer, the bag belt behind under its hood, the
   scale's lit weight display on its stalk.
5. (A) [done: the curtains as separate strips; the rest was already modelled] `l36-xray-body/belt-*` (23 / 19): the tunnel with lead curtain strips at both mouths, the rounded hood, a warning
   label, the operator's monitor on an arm; the roller bed as separate rollers on side rails.
6. (A) [done: checked, already at the bar] `l36-scanner-*` (9 / 11): the arch with LED zone bars on its uprights, a crown housing with a lit status lamp, foot
   plates.
7. (A) [done: the seats were at the bar; the coat is an olive parka now (the camel read as a box)] `l36-seat-*` (16-31): seat pans with a seam and a perforated back, armrests on posts between the seats, the beam
   with end caps, splayed legs with feet; `-coat` a draped jacket (sleeves, collar) instead of a beige box; `-bag` a real
   backpack (pocket, straps).
8. (A) [partly: magazine racks, the till counter, a newsstand's mix; the duty-free gondolas kept] Shops: `l36-gondola` (27) as shelving with rows of goods (bottles, boxes, packets) and price rails; a till counter
   `l36-till` (register, card reader, bag hooks); goods behind the glass front.
9. (A) [done: `l36-coffee`, `l36-pastry`, `l36-stool` (Level 15's coffee machine is 8 boxes: not reused)] Cafe: a coffee machine (group heads, steam wand, cups on top), a glass pastry case (translucent, cakes inside), bar
   stools; reuse Level 15's `l15-appliance-coffee` if it meets the bar, else `l36-coffee` / `l36-pastry` / `l36-stool`.
10. (A) [done] Fascias `l36-shopsign-*` (1 box): a light box with depth, an edge frame and a lit face only where the letters are.
11. (A) [done] Hanging signs and screens `l36-sign-*`, `l36-fids-*`, `l36-fidspole` (1-3 boxes): a housing with depth, a back,
    hanger rods to the ceiling; the screens lit, the bezels dark.
12. (B) [skipped: checked, the podium already has its screen and microphone] `l36-gatedesk-*` (25): a boarding-pass reader with its LED, a phone, the screen lit.
13. (B) [done] `l36-payphone-*` (8), `l36-atm-*` (6): a hood, the handset on its cord, keypad, coin slot; the ATM with a screen
    recess, keypad shelf, card slot and canopy.
14. (B) [done] `l36-fountain-*` (9): the stainless bi-level fountain with bubblers and push bars.
15. (B) [skipped: kept (a column of sockets reads at its size)] `l36-charger` (3): a post with sockets, USB ports and a lit ring.
16. (B) [done: checked, already at the bar] `l36-stanchion-*`, `l36-trays`: weighted bases, chrome posts, belt cassettes; trays with lips.
17. (B) [skipped: checked, the door has its frame, push bar and vision panel] `l36-gatedoor-*` (15/16): a frame, a push bar, a wired-glass vision panel, a card reader with its LED.
18. (B) [done: `l36-trolley`] Trolleys with baskets: a luggage trolley `l36-trolley` (frame, handle, basket, wheels) for the claim hall's bays,
    unless a shared one meets the bar.
19. (B) [done: basins with a mirror panel and soap; the cubicles were round 3's] Restrooms: cubicle partitions with doors, legs and locks; basins `l36-sink-*` with a mirror over them.
20. (B) [done: information pylons] The information desk: a counter with the "i" totem and a lit screen.
21. (C) [done] Prayer room: mats laid in rows and a rolled one, a shoe rack.
22. (C) [done] `l36-wallclock-*`: a bezel with depth.
23. (C) [done: checked; the shoe-shine chair rebuilt instead] `l36-lostfound-*`, `l36-booth-rack-*`: check them against the bar; touch up.

**2. Multi-block set pieces**
24. (A) [done] The carousel as one object: island (1), belt (2), flap (3), its number hung over it on rods, bags on the plates.
25. (A) [done] The jet bridge: the bridge between the gate door and the cabin dressed as a bridge: ribbed tunnel walls, a glazed
    side (window strips onto the grey apron), the floor's tread strips, a lit ceiling strip, the cabin door's frame
    (`l36-bridge-*`).
26. (A) [done] The security lane as one object: X-ray (5), roller tables, curtains, the arch (6), the tray stack, the podium.
27. (A) [done: checked] The check-in island: desks back to back with the bag belt's hood between them, the flight screens on their pole.
28. (A) [done: and pendant lights, roof lights in it] The big halls' ceiling: a space frame (tubes, nodes, diagonals under a dark deck, a 2 x 2 module) over the claim
    hall, security and the concourses (`l36-frame-*`); coffers kept in check-in and the junctions.
29. (A) [done] The meeting-point sign tall enough for the 14-high atrium (post and cube raised, the cube framed).
30. (B) [done] Clad columns in the claim hall, check-in and the food court: a stainless plinth, a capital flaring into the ceiling
    (`l36-column-*`).
31. (B) [done: check-in, concourses, junctions, piers (not the Meeting Place's stepped round wall)] A mezzanine edge round the tall halls (check-in, the Meeting Place): a slab lip with a glass balustrade and
    handrail, the band above dark glass (`l36-mezz-*`).
32. (B) [done] The Travel Agency kiosk's canopy: a fascia edge with downlights.
33. (C) [skipped: time; the wall boards cover it] The departures board on a two-legged totem at the junctions.

**3. Level design**
34. (A) [done: bands; no border round the carousels] Floor pattern: dark marble inlay bands across the claim hall and check-in at each module, a border round each
    carousel and island, so the white field breaks.
35. (B) [done: the gallery over the shopfronts] The concourse walls above the shopfronts (round 3's weak point): the mezzanine band (31) or a clerestory.
36. (B) [partly: pendants from the frame; the halls stay evenly lit] Light rhythm: the space-frame halls lit from the frame (pendants on the nodes), the strip between darker.
37. (B) [done] The information desk's showcase spot frames it from the front.
38. (C) [done: roof lights in the frame over the streets and food courts (not the claim hall)] Skylights in the claim hall.

**4. Lore**
39. (B) [skipped: round 3's question 3 is still open] "MEETING PLACE n OF 47" placard at the marker (round 3's question 3; lore phrasing only).
40. (B) [partly: the chalk cross in one bridge in four; no sleeping bag] Wanderer touches: taped notes and chalk on the bridge walls ("do not board"), a sleeping bag under a seat row.
41. (C) [done (22)] The clocks with no hands as a real wall clock with a bezel (22).

**5. Alignment with the other levels**
42. (A) [partly: fire cabinets in the dado; the EXIT signs are the level's own hanging ones (no panel-wall variant of the shared extinguisher)] Shared kit kept: EXIT signs, extinguishers, hose cabinets, placards, supply boxes, the Almond Water coolers;
    check the concourses carry the mod's EXIT signs and extinguishers like the released levels; add where missing.
43. (B) [partly: Level 974's basins kept; the others checked and not taken (below the bar or another level's look)] Reuse: Level 15's coffee machine and serving line, Level 31's condiments and stools, Level 52's fountain, the
    detail kit's trolleys, cafe chairs and drink fridges where they meet the bar; note the family in "Shared assets".
44. (B) [done: checked (57 and 25 elements), kept] Level 4's vending machine / water cooler as placed here: check against the bar; note under "Shared assets below
    the bar" if not.
45. (A) [done] Showcase spots for every rebuilt set piece (carousel, check-in, security, bridge, cafe, shop, frame, meeting
    point) and the F7 entries to match.
46. (A) [done] HUD names (en.json) and creative-inventory entries for every new block.

### What was built (round 4)

All new blocks are in `tools/gen_36_r4.py` (run by `gen_36.py`, its textures first); rebuilds are in the generators that
made the block before. Element counts in brackets.

- **The big halls' structure.** A **space frame** (`l36-frame-{ee,oe,eo,oo}`, 13 each) over the claim hall, the concourses,
  the piers' corridors, the duty-free streets and the food courts: a dark acoustic deck with white tubes hung under it,
  square on square, 2 x 2 blocks a module, the top nodes on even block corners, the bottom ones on odd corners, one
  diagonal through each block (rotated in two axes: VS turns an element Z first, then Y, then X). Their light panels are
  now **pendants** hung from the frame (`l36-framelight-*`, a dark housing on two cables, the diffuser lit). **Clad
  columns** (`l36-colfoot-*`, `l36-colhead-*`): every 2 x 2 column of the claim hall, check-in, the food courts and the
  Meeting Place's ring (those two were plain wall: now poster columns too) stands on a stainless plinth and flares into the
  ceiling in a stepped capital with a steel band, white cladding between (under a space frame the capital sits in the
  frame's own block, under the deck, and every wall's block at that height is dressed instead of left as concrete). A **gallery** (`l36-gallery-{lip,glass}-*`) round the halls nine high
  and more (check-in, the concourses, the junctions, the piers, the streets, the Meeting Place): at seven a slab edge
  stands out of the wall with a glass balustrade and a chrome rail, and over it the upper level's dark glazing behind
  mullions (dim shelves, a reflection band): a level nobody reaches. A **floor pattern**: charcoal marble bands across
  the claim hall and check-in on every module line and every eighth row, so the white field reads as bays. The runway
  windows and the plane at the gate have a **real mullion** standing proud at each block's edge. The roof lights down the
  duty-free streets and across the food courts are frame blocks whose deck is the glazing (`l36-framesky-*`), and every
  skylight now gives daylight (the Meeting Place's floor was dark under its own). The holdrooms' side walls take the
  halls' travertine dado; the baggage wall carries posters between the carousels. The Meeting Place gets lights among its
  skylight's panes (the floor round the marker was dark) and the marker's light is brighter; the Travel Agency's posters
  on a kiosk's outer walls are on purple cubes (from inside the kiosk their backs read as grey boards).
- **The carousel** as one object: the island is now an edge / corner / deck by its neighbours (`l36-carousel-island`,
  `-island-edge-*`, `-island-corner-*`): a skirt, a kick plate, a black rubber bumper over the belt, a plate sloping up to
  the deck with bolts; its mouth in the wall (`l36-carousel-flap-*`, 15) a steel portal with a hazard-striped lintel,
  guards, and a curtain of six separate rubber strips, one swung back; **unclaimed luggage** on the plates
  (`l36-luggage-*`: hard-shell spinners on their side, a canvas duffel, a garment bag, a spinner standing with its handle
  out; decor only, on belts where no lootable case is); seats on beams facing the belt instead of lone benches; airport
  **trolleys** (`l36-trolley-*`, 23: castors, tread deck, wire basket, handle) in the bays.
- **The jet bridge** (the bridge between the gate door and the cabin): walls `l36-bridge-{lower,glass,upper}-*` faced
  toward the bridge (corrugated panels with ribs, a rubber skirting and a handrail on brackets; a glazed band with a sill,
  a header, a mullion and a tinted pane, the wet apron and the parked plane's flank beyond; an LED cove under the
  ceiling), a studded rubber floor `l36-bridgefloor`, a ribbed ceiling with its light `l36-bridgeceil`; in one bridge in
  four a wanderer's chalk cross just inside the door.
- **Cafes**: `l36-coffee-*` (an espresso counter: red enamel machine, two group heads with portafilters, a steam wand,
  cups warming on top, a grinder of beans), `l36-pastry-*` (a lit glass case of cakes on a wood-fronted base),
  `l36-till-*` (register with its screen toward the clerk, card reader, receipt, carrier bag), `l36-stool` (chrome, red
  vinyl seat, foot ring). Frontage cafes: espresso counters on the back wall, a pastry case and the till by the door;
  every frontage shop's till is now the till counter. Food-court cafe stalls: pastry cases and a till along the counter,
  espresso counters in the kitchen, stools along the counter (every stall kind has stools).
- **Shops and services**: a newsstand's **magazine racks** (`l36-magrack-*`), the **payphone** (22: hood with cheeks and a
  lit header, keypad, coin slot and return, instruction card, handset on an armoured cord, directory binder), the **cash
  machine** (22: privacy hood, inset lit screen with side keys, sloping keypad shelf, card slot with its LED, receipt and
  cash slots, lit topper), the **drinking fountain** (17: two basins on brackets with noses, bubblers and push bars, a
  bottle filler with its lit panel), **information pylons** (`l36-infopylon-*`: a lit yellow "i" over a slanted touch
  screen) either side of every information desk, **prayer mats** (`l36-prayermat-*`) laid in rows on one side of the
  prayer room's aisle (chairs on the other, one rolled), **fire cabinets** (`l36-firecab-*`) recessed in the travertine
  dado about one wall block in forty, the restroom basins (`l36-sink-*`) with a mirror and a soap dispenser over them.
- **Signs**: the hanging wayfinding and gate signs (`l36-sign-*`, `l36-gatesign-*`, 9) have a housing (lips standing proud
  top and bottom of both faces, ceiling plates on the rods); the flight screens (`l36-fids-*`, 4) bezel lips and a hanger
  bar; the **shop fascias** (`l36-shopsign-*`) are light boxes standing 1.5 out of the wall with aluminium trims and end
  caps, lit only on the face; the **meeting-point sign** stands on a post seven high (its cube at eight and nine, so it
  reads across the 14-high atrium) in a brushed aluminium frame along its outer edges (`l36-meetbox-*` now a model); the
  Travel Agency kiosks' canopy (`l36-canopy-{plain,lit}`) has a downlight every other block; the **station clocks**
  (`l36-wallclock-*`) stand out of the wall in a dark case with a steel bezel.
- **Benches**: the level's own airport bench (`l36-bench-*`: oak slats on a steel rail, cast leg frames, a seat divider)
  wherever the layout puts the shared bench (the Meeting Place's ring, the concourses, the services alcoves).
- **Lost and Found**: the office under its own four-high tiled ceiling (it stood under the claim hall's seven) with its
  lights, unclaimed luggage heaped between the shelves and the counter.
- **Food courts**: the travertine dado and the gallery round their walls too (the stalls' menu boards keep their place
  under it).
- **The lounge**: its own cognac leather sofas (`l36-sofa-{left,right}-*`: plinth on chrome feet, a deep seat with its
  seam, a back cushion leaning on the padded back, a rolled arm) in place of Level 3999's purple couch halves.
- **Smaller**: the restroom basins (free-standing in the pier restrooms) carry their mirror on a panel; the shoe-shine
  chair rebuilt (step, buttoned leather, brass-capped arms, chrome shoe rests, the shiner's kit box); the X-ray's lead curtains are separate strips (one pushed back), the coat left on a gate seat is a dark
  olive parka (the camel read as a cardboard box), the frontage's restroom basins keep Level 974's.
- **Showcase / F7**: new spots `carousel-flap`, `space-frame`, `column` (F7 "Baggage carousel"), `bridge` (new F7 entry
  "Jet bridge"), `cafe` (new F7 entry "Cafe stall (espresso bar)"); `info-desk` now from the front, `meeting-place`
  looks up to the raised sign.

### Inventions (round 4)

The space frame, the gallery round the tall halls with its dark upper level (nobody gets up there: an upper floor the
lore never mentions, shown only as glazing), the floor bands, the cafe brand's counters (Terminal Brew's were only a
fascia and a menu), the cognac sofas, the information pylons, the fire cabinets, the chalk cross in some jet bridges (a
wanderer's warning; the lore says only that flights land elsewhere), the luggage nobody can open.

### Shared assets below the bar (for the lead)

- `detail/suitcase` (4 elements) and `detail/bench` (3): a box with a picture of a suitcase, a plank on two blocks. They
  are the mod's lootable cases and its everywhere bench. Level 36 keeps the suitcases (their loot) and now puts its own
  decorative luggage (`l36-luggage-*`: ribbed hard shells with seams, handles, wheels and tags) beside them, and gate
  seats on beams where it had benches. A suitcase at the bar: a rounded shell in two halves with a seam and zip, corner
  guards, a telescoping handle, wheels, a tag; the bench: a slatted seat on two cast legs with armrests.
- `detail/luggagecart` (13): a flat cart. Level 36 uses its own `l36-trolley` now (castors, tread deck, wire basket,
  handle bar with its brake grip, leaning back).
- `tools/preview_shapes.py` turns an element X first, then Y, then Z; the game's tesselator (decompiled
  `ShapeTesselator`: `Translate, Rotate X, Rotate Y, Rotate Z` on the stack matrix) applies Z first, then Y, then X. For
  an element turned about one axis it makes no difference; for two (a space frame's diagonal, a tilted and turned arm)
  the preview draws it wrong. A one-line swap in `rotate()` fixes it (I used a local copy, not the shared tool).

### Balance notes for the lead

None of round 4's blocks is a source of anything: the luggage, the tills, pastry cases, espresso counters, magazine
racks, fire cabinets and prayer mats are decor (no drops, no containers). The drinking fountains keep the coolers'
dispenser (unchanged count). The claim hall's lone benches became rows of three gate seats (seats, not beds). No safe
rooms, beds, water or food were added; no loot table or supply rate moved.

### What the shots showed (round 4)

- Run 1 (`%TEMP%/backrooms-shots/36-r4a`, after the A items): the space frame changes the halls most (the claim hall, the
  concourses, the piers, the food courts read as a terminal's roof now), with the clad columns, the gallery's dark band
  over the concourses and check-in, the floor bands, the carousel's rim and belt mouth, the cafe stalls (pastry cases,
  tills, espresso counters, stools), the fire cabinets, the trolleys. Wrong: the frame is not a full cube, so the wall's
  block at its height showed concrete as a grey strip under the deck, and the capitals sat a block under it; the Meeting
  Place's round wall got the gallery in single stepped blocks (little dark windows); the jet bridge's glazing was a
  deep recess whose sides read as grey boxes down the run; the kiosk canopy had a downlight in every block (polka dots);
  the floor under the meeting point was dark; the restroom basins stand free in the room (the mirror would have floated);
  the skylight bands were flat white planes in the frame; the holdroom walls bare panel; the lounge's 3999 couches.
- Run 2 (`36-r4b`): the walls dressed under the frame, the capitals under the deck, the roof lights glazed into the
  frame, the cognac sofas, the clocks, the holdrooms' dado; still the kiosk's posters' backs grey inside the kiosk, the
  floor round the meeting point dark (the skylight's light is 14 up), the bridge's grey boxes.
- Run 3 (`36-r4c`, final, sheet `%TEMP%/backrooms-shots/36-r4c/sheet.jpg`): the holdrooms under the frame with the
  dado, the food courts with the gallery's glazing over the stalls and their menu boards, the Lost and Found an office
  heaped with hard shells, duffels and garment bags, the airport benches round the meeting point, the floor round it lit,
  the jet bridge's glazing flush with the wall and the parked plane's flank beyond, the kiosk posters on purple.

**Still weak** (after round 4): the halls are still evenly bright (round 2's choice, the frame's pendants do not change
it); the Meeting Place's round wall is stepped plain cladding (the gallery could not follow its curve); the gate seats
read heavy from behind (their backs are flat shells); the Lost and Found's lootable suitcases (the shared `detail/suitcase`)
stand beside the new luggage and look cruder; the restrooms are large tiled boxes (cubicles along one wall only); the
blackout and the service maze were not touched this round.

### Questions for the user (round 4)

1. The space frame now roofs the claim hall, the concourses, the piers, the holdrooms, the streets and the food courts
   (check-in and the junctions keep their coffers). Is one structural language through the airside right, or should
   some halls keep a different ceiling for variety?
2. The gallery shows an upper level behind dark glass that nobody can reach. Keep it as a sight only, or should a later
   round open some of it (a mezzanine lounge, a viewing deck)?
3. Round 3's question 3 is still open: a "MEETING PLACE n OF 47" placard at the marker?

### Checks (round 4)

`expclash` clean; mod and mapgen build, 0 errors; `layouthash` (12345, 16000; layout versions 1 and 12;
`BACKROOMS_NO_EXP_ENTRANCES=1`): every line for levels 0-20 and the `layout hash` line identical to main's saved files;
`regions` 60/60 in Level 36; `featurecheck 3 36`: 18/18 features found from every arrival (new: `l36bridge`, `l36cafe`);
headless (port 43157): `/backrooms dummy place 36 5` lands (light 10), 0 error lines, 0 missing blocks, `blocksweep`
15769 blocks, 0 threw; `GATE_TAG=36g gate.py --fast --port-base 43150`: PASS (5e22690a).
