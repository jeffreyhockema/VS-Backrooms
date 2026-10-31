# Level 36 "Airport" - brief and design plan

Nothing is built (a scaffold with placeholder blocks is in progress), so this is both the lore digest and the plan. Marked (mine) = my suggestion, not lore.

Sources
- Wikidot "Timeless Airport", by Endrew1, https://backrooms-wiki.wikidot.com/level-36 (class 1: Exit 1/5, Environment 2/5, Entities 0/5).
- Fandom "Desolate Terminal", https://backrooms.fandom.com/wiki/Level_36 (class Undetermined, via `api.php?action=parse`; WindXD and SavouryXD rewrite).

## 1. Lore

### What the two agree on
- An endless airport terminal complex, the Backrooms' travel hub. Wikidot: "the biggest safe hub where every level is only one flight away." Fandom: "a secondary hub of the Backrooms, similar to the Hub."
- Gates, rows of waiting seats, shops, cafes and food courts; carpeted floors with marble tile (Fandom: "marble-tiled flooring periodically covered in carpet"); check-in desks with screens showing only flight numbers (Wikidot: countdown, flight number, gate, status; Fandom: "only display the flight number about to depart"); multilingual placards; signs that lead nowhere ("Don't trust any 'exit' signs" / "the exit sign never goes to the actual exit, instead blocking the doorway").
- Non-Euclidean, self-overlapping concourses; dead ends where signs go empty or broken.
- Almond Water from fountains; vending machines free to take from.
- Fluorescent lights in ceiling tiles plus sign light; flicker; stretches of dark. Smilers may lurk in dark corners.
- Quiet, empty, abandoned; background hum, distant sounds.
- Nobody lives here long: Wikidot only the Gate C32 Support Group and BTA staff; Fandom no groups.

### Where they differ (and my choice)
| Topic | Wikidot "Timeless Airport" | Fandom "Desolate Terminal" | Choice |
|---|---|---|---|
| Purpose | Gates are real: boarding opens Sublevel 36.1 (the plane), which flies you to a level | "the flights don't actually exist"; waiting rooms "serve no purpose"; exits are odd (sink to Level 37, glass hotel doors to Level 42) | Wikidot's gates and countdown screens are the core mechanic; keep Fandom's desolation as the look. |
| Time | Heavy time dilation, a week = 1 second in Level 11, clocks freeze, cannot sleep | not mentioned | Wikidot (but see fatigue in 3). |
| Windows | not mentioned | corner windows onto a runway; grass hills in fog; unbreakable; no road; plane sounds but no planes | Fandom (agrees with "Timeless" mood; Wikidot is silent). |
| Hazards | Cold/warm patches, light distortion, afterimages | blackouts "for miles", poisoned food, vents with fans, hallucinations in the deep "Absolute Limit" | Both, light touch. |
| Food | Shops mostly worthless; clothes, bags, snacks useful | Cafe food is mostly spoiled, some poisoned (cyanide); machine drinks and bars safe | Merge: spoilage on tables, safe in machines. |
| Cleanliness | not stated | marble self-cleans out of sight | Fandom. |
| Entities | none hostile (0/5) | Smilers, Hounds, Deathmoths, rare, in dark/vents | Rare Smilers only in blackouts and vents. |

### Key lore quotes
- Arrival: "you're brought in by conveyor belt; they import every being and object that no-clips into Level 36. Endless rows of baggage carousels stretch out in both directions, attached to a wall that is the only known bounded edge of the level." Luggage left 10 rounds goes to Lost and Found.
- Check-in: "an infinite row of deserted service counters"; "When a flight's countdown reaches 1000, it will begin 'boarding'"; at 0 the gate closes. Screens use "a simple unitless number" rather than time.
- Security: "defunct security checks."
- Concourses: "contradictory signs ... loss of cardinality"; "Empty sign = no good!"; "Different areas ... drastically different temperatures"; "Light behaves strangely ... reflections that don't line up ... afterimages ... of wanderers who recently walked by."
- Duty-free: shops are Frontrooms brands, "most products are actually worthless" (tinted-water perfumes). Useful: clothes, storage, snacks; rarely Worn Sacks, Almond Water, Lucky O' Milk, ChocoBytes, Babel Balm.
- Travelators: "often one-way", some "stutter or aren't moving at all."
- The Meeting Place: "at least 47 distinct positions ... all actually one singular place"; BTA staff pass through.
- Terminals: 26, A to Z, "infinitely numbered gates"; waiting areas with bathrooms, water fountains, seats and tables with outlets and USB ports; Wi-Fi "prone to disconnecting every hour"; lounges (books, magazines, games, showers, buffets, fridges, rare gyms).
- Time: "Any timekeeping devices brought into the level instantly freeze"; clocks "showing random times (or missing the hands altogether)"; "It is physically impossible to sleep throughout the entire airport"; wounds heal slowly "purely a mental perception."
- Fandom desolation: "clothing laying all over the chairs, and luggage seemingly abandoned"; "stores were closed, the lights were flickering"; cafes the only places with left-behind objects, half-eaten meals, "cups paired with deformed paper straws"; "sound of plane taking off or arriving can be heard in the distance."
- Fandom vents: crawlable, clean, no light, fast fans, "short cut"; something may hit the steel.
- Fandom Absolute Limit: far out the boundaries "become absent, leaking an undetermined force of static"; glitching, hallucinations, devices corrupt.
- Fandom steel queue barriers form "a maze-like labyrinth of nothingness."

### People and groups
- **Backrooms Travel Agency (BTA)**, purple signs, booth 0 in the check-in area; Travel Planners and Guides; flight catalogue; a "Pilot Passenger" job (board undocumented flights).
- **Major Explorer Group** Track Mappers in a Concourse M lounge; **BNTG** couriers with hidden first-class lounge stockpiles; **Gate C32 Support Group**: about 150 waiting for flight 1784XBA8JLP to Level 186, countdown 94,612,753.

### Entrances and exits
Wikidot entrances: airplane-symbol signs in Levels 11, 9, 159; apartment doors in 11.2; transport levels; luggage in 902; jet in 103; Level 20 exit door. Fandom: train in the Metro, Level 35 airport structures, Level 597, Level 188.2 stairwell falls. Exits: any gate door to Sublevel 36.1 (Wikidot); sink-dunk to 37 and glass hotel doors to 42 (Fandom). The cheats menu is the only way in for this mod.

### Survival class
Wikidot class 1 (easy); Fandom undetermined. Use **class 1**, low danger, with environment 2 (cold/warm patches, blackouts).

## 2. What exists now
Only a scaffold with placeholder blocks. No layout, no blocks, no sound, no entities.

## 3. Design plan and build list (mine, scaled to this mod)

### Scale and skeleton
Round noclip region, radius `max(40, spawnMacroX/50)` cells, one cell = 32 blocks, band about 40 high. Level 4's 48-block concourses and Level 3999's 12-wide, 18-high mall concourses are the scale reference. Layout comes from `Hashing.Hash` of world coordinates and `PlanCache` plans; no per-region state.

The lore is "orderly" near the arrival wall and "non-Euclidean" beyond. Zones, in order from the rim inward:
1. **Baggage claim (the bounded edge).** The westmost 3 cells: a long hall 24 wide, 7 high, the outer wall lined with carousels (a 2-wide slow loop of belts with rubber flaps, number plates, a few abandoned bags). Arrivals spawn on a belt (it carries you out; mine). Lost and Found office at one end. Dead belts mostly; a few "active" ones hum.
2. **Check-in.** Next 3 cells: an 18-wide, 8-high hall, desks in rows with counters, stanchions, and flight-information screens above every row (the signature prop). Booth 0 (purple BTA) at the centre line. Marble tile, a carpet strip. Dozens of screens show countdowns.
3. **Security.** A 12-wide band of defunct scanners, belts, trays and stanchion mazes (the Fandom "queue barriers").
4. **Concourse lattice.** The rest of the region: concourses every 4 cells (128 blocks), 16 wide, 9 high, with lamps in steel ceiling tiles, signs, carpet over marble, windows to the runway on one side of the hall ends. Lattice holds: duty-free shopping halls, travelator runs (moving walkway, one-way pairs; reuse 3999's), the **Meeting Place**, food courts, lounges, and **terminals A-Z** as pier wings (gate rows of 12 seats each, gates numbered; "26" is a wing label, with gates unbounded in principle).
5. **Out of bounds.** Dead-end loops with blank/broken signage (cheap trap-free dead ends); vents; blackout stretches; and the rim where static "leaks".

Non-Euclidean feel (mine): use the mod's existing "topology lies" tricks (see `docs/GUIDE.md` "The topology lies") for a few wrap-around concourses and contradictory signs; keep the first third orderly as the lore says.

### Blocks and props (Must)
- **Floor**: white marble tile (shiny, slippery look), carpet (grey/blue, patterned) as a second kind, mixed in strips.
- **Walls/ceiling**: white plaster, glass curtain wall for runway windows (unbreakable), steel ceiling tiles with fluorescent fittings, fluorescent on/off/flicker (reuse existing).
- **Props**: check-in desk, flight-information screen (animated text is the hero; a texture with random flight rows, several variants), gate seat rows (metal bench, upholstered), gate desk, stanchions/queue barriers, baggage carousel (belt with flaps), luggage (suitcase variants, backpack), trolley, signs (gate arrows, "Exit" that points to a blocked door), vending machine, soda machine, water fountain (Almond Water, reuse), shop shutters, shop fronts (duty-free, cafe, bookshop, clothing), potted plants, bins, wet-floor signs, travelator, clock with no hands, power outlet strips.
- **Runway view**: a painted windowscape as in 3999's car park and Level 4's windows: concrete apron, runway lights, grass hills in fog; sky dim grey. Unbreakable.
- **Sound**: a steady HVAC hum bed with fluorescent buzz and a faint high murmur; one-shot PA chime (androgynous monotone voice: flight updates, "now boarding at gate L67") every minute or two; distant jet taking off/landing; belt clunk in baggage claim; escalator and travelator hum; a cold-patch breeze. Calm, so quiet, per Fandom.

### Mechanics (Must / Should)
- **Must: flight screens and gates.** Screens in check-in and at gates show a list; boarding at 1000 opens a gate door into a stub "Sublevel 36.1" cabin (rows of seats, aisle, tiny windows showing cloud); at 0 the player is "shuttled". Since this level has no outbound links, landing returns the player to a baggage belt, with a lang line "The flight lands. It's already the airport again." (mine). Or, if the Opus agent has time, offer random existing levels via the cheats menu only.
- **Must: no sleep** (lore). Bed/sleep refused: "You cannot sleep here." The mod has thirst and fatigue (see `docs/design/needs/decisions.md`): fatigue should not fill in Level 36 (the body does not age; time dilation) but hunger and thirst stay normal, since the BTA says "Remember to eat" (mine; avoids a death trap).
- **Must: frozen clocks.** Held clock items (if the mod has them) stop; wall clocks show random times or no hands.
- **Should: time dilation feel.** Cosmetic: day cycle off; wounds heal slowly (halve health regen; lore says it only appears slow, so keep it mild); a drifting "afterimage" effect (a translucent copy of a previous wanderer's silhouette) as a light-distortion treat.
- **Should: temperature patches.** Cold/warm bands (10 C and 28 C) in concourses; use the mod's existing heat/cold systems; a couple of bands overlap (hot and cold messages at once).
- **Should: blackouts.** Stretches of dead lights 100+ blocks long deeper into the region, with flicker at the edges; Smilers, Hounds or Deathmoths may stand in them (rare, class 1 level, so 1-2 per blackout, never in lit concourses).
- **Should: vents.** Crawlable 1x1 vent runs between concourses with spinning fan blocks (damage if you hurry past? not lore; instead slow/blocked path), no light, rare noises (mine).
- **Nice: the Absolute Limit.** At the far rim: static, glitching geometry, hallucinations (non-human figures at the periphery), device corruption (screens garble). The sky is the "border". A one-way trap into a "missing" state; for safety make it a sanity drain and nothing worse.

### Entities and people
- Mod entities reused: `smiler`, `hound`, `deathmoth` (rare, blackouts and vents).
- **New NPCs**: *BTA Travel Planner* (purple vest, invulnerable, at booth 0 and the Meeting Place; right-click for a tip about a "flight" and a gate pointer; reuse the 3999 Arcade Attendant pattern). *Support Group members* at gate C32: 10-20 seated figures with luggage and bedrolls, mildly talkative (reuse wanderer NPC); the countdown on the C32 screen is 94,612,753.
- Food: spoiled meals on cafe tables (poison/gut-rot chance, mine), machine drinks and bars safe and free (Almond Water, energy drinks, energy bars), shop stock mostly junk, useful bits (clothes, packs, snacks).

### Loot (mine)
Almond Water, energy bars/drinks (machines); luggage: clothes, worn sack, packs, phone/charger junk, magazines (paper), toiletries, tinted-water perfume (junk); lounge buffets: tray meals; Lucky O' Milk, ChocoBytes, Babel Balm rarely in shops. Wanderers buy junk (see the traders design).

### Wanderer notes (mine)
1. "Screen says 1000. I've been standing at G47 since the screen said 1,000,000. I do not know if my watch is lying; it stopped."
2. "Never trust an exit sign. I followed one for a day and got a blank door."
3. "A woman at C32 gave me soup. The countdown is nine digits. She says she will see the valley."
4. "The floor is so clean it hurts. I dropped a cup and when I looked back it was gone."
5. "Blackout ahead. Back to the last coherent sign. Empty sign means no good."
6. "I tried to sleep. I closed my eyes for what felt like hours and opened them in the same second."

### Handbook page outline
Arriving (the belt; leave your bag alone) - Reading the screens (countdown, gate, status, unitless numbers) - Signs (follow the latest; empty means turn back; never the exit) - Time here (clocks stop; no sleep; slow healing) - Food and water (safe from machines; tables are bad) - Meeting Place and the Travel Agency - Blackouts and vents - Getting out (gates).

## 4. Open questions
1. **Does boarding lead anywhere?** Wikidot: yes, to arbitrary levels; this mod's levels are disconnected. Recommendation: board to a plane cabin and land in the airport (stub); revisit when thresholds exist.
2. **Runway view.** Wikidot silent, Fandom has it. Recommendation: include, painted, unbreakable.
3. **Time dilation in play.** Recommendation: no sleep, fatigue paused, hunger/thirst normal; do not freeze the world clock.
4. **Entities.** Wikidot none, Fandom three rare. Recommendation: rare Smilers/Hounds/Deathmoths only in blackouts, none in lit concourses.
5. **Terminal count.** 26 wings A-Z with unlimited gates is infinite in lore. Recommendation: label wings A-Z around the region in a hash order, gates 1-60 each, no true infinity.
6. **Absolute Limit vs "infinite horizontally".** Recommendation: the rim is the Absolute Limit (static); the baggage wall is the west rim.

Confidence: lore reconciliation high; layout, numbers, NPCs and mechanics are my design.
