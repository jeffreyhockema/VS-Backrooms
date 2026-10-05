# The Backrooms (Vintage Story mod)

Wake up in the Backrooms with nothing. You start in Level 0, an endless, procedurally generated expanse of mono-yellow rooms under buzzing fluorescent lights. Walk far enough and it gives way to deeper levels, one after another: the concrete car park of Level 1, the pipe tunnels of Level 2, the Electrical Station, the Abandoned Office and the Terror Hotel. Beyond them are the lightless maze of Level 6, the endless sea of Level 7, the caves of Level 8, the night-time Suburbs of Level 9 and the farmland of Level 10. Further still, reached only by noclipping, lies Level 11, the Endless City. Scavenge supply boxes and crates for Almond Water, food and basic materials.

Each deeper level opens up a different way to survive: darkness and navigation in Level 6, water in Level 7, geology and mining in Level 8, scavenging in Level 9 and farming in Level 10.

Targets Vintage Story 1.22 (.NET 10).

![Top-down overview of the levels](docs/levels-overview.png)

*About 1,300×1,300 blocks around spawn, from the centre outwards: Level 0 (yellow), Level 1 (grey), Level 2 (dark), Level 3 (brown and brick red), Level 4 (light grey), and Level 5 (red), which has tan lobbies and boiler halls.*

## Playing

Create a new world and pick the **The Backrooms** playstyle. It only affects worlds created with that playstyle. Normal worlds are untouched.

- **Map (M / F6):** the map only shows what you have actually seen. It reveals the area around you along your line of sight, so walls block it. Explored areas are remembered between sessions, so you can find your way back.
- **Handbook (H):** in a Backrooms world the Guides tab is rewritten for the Backrooms. The Starter Guide, the Progression Guide and Reality Stability replace their vanilla pages, and three reference pages are added: Salvage and Recipes, The Levels, and Ways Between Levels. Other worlds keep the vanilla handbook.
- **Starting waypoint:** "Where I woke up" marks your starting point.
- **Your own waypoints:** right-click the map to add one.
- **Dark areas** are easier to explore with a candle.
- **Arriving in a level** shows its name, with a word of advice for the dangerous ones.
- **Surveyor's chalk** (sometimes found in crumbled ceiling tiles, or crafted from a vanilla chalk stone) marks walls with an arrow, a cross or a circle. Choose the mark with the tool mode key (F), and click a mark again to change it. Chalk marks show bright white on the map.

## Surviving

### You are a scavenger

The Backrooms itself cannot be broken: walls, floors, slabs, pipes and doors are permanent. What you can take is salvage.

- **Loose objects break as normal:** supply boxes, crates, furniture, ceiling tiles and dead light fixtures.
  - Dead fixtures give glass shards, and sometimes a bracket or wire.
  - Ceiling tiles mostly give nothing, but the void above sometimes hides scrap wire, a metal bracket or rotten wood.
- **Walls and carpet can be cut:** right-click papered walls or carpet with a blade to cut away wallpaper strips or carpet fibres. The wall or floor stays, visibly bare.
  - A glass shard works as a blade, but may snap each time.

| Make | From |
|---|---|
| Glass shiv (a knife) | glass shard + wallpaper strip + carpet fibres |
| Improvised scraper (a tougher knife) | metal bracket + wallpaper strip + 2 carpet fibres |
| Twine | 3 carpet fibres |
| Carpet bag (3 slots, like a hand basket) | 5 carpet fibres + twine |
| Dry grass (tinder) | 2 wallpaper strips |
| 2 sticks | rotten wood |
| Firewood | 2 rotten wood |
| Firewood | 3 planks + an axe |
| 2 sticks | a plank + a knife |
| Nails and strips | 2 metal brackets |

With tinder, sticks and firewood, the vanilla fire starter, firepit and torches work as usual.

### A Vintage Story player wakes in the Backrooms

Breaking things down feeds Vintage Story's own progression, so the usual path from knapped flint to bronze still works. What changes is where each material comes from.

- **Level 0 (the Lobby):** wanderers' supply boxes hold flint, sticks and dry grass. Knap a flint knife and axe, then make a fire starter, torches and a firepit. Furniture breaks into planks, sticks and nails, so a chest or a barrel is possible before you own a saw.
- **Level 1:** the crumbling concrete leaves loose stones and flint about. Crates and shelves hold sticks, tinder, flint, charcoal and brackets.
- **Levels 2 and 3:** cable drums, pipe stacks, fans and machine cabinets give copper and lead bits. Scrap wire smelts to copper. The flooded tunnel under Level 3 is floored with clay for pottery, moulds and a crucible. The generator rooms have coal heaped beside them, enough to smelt with.
- **Level 4:** office furniture gives lumber and paper. Fridges hold fruit and cheese. Toolboxes sometimes hold a copper hammer, chisel, saw or knife. Storerooms sometimes hide a supply box.
- **Level 5:** coal piles in the boiler halls. The beds come away as real beds you can sleep in. Wardrobes and suitcases hold clothes. Silverware, candelabras and luggage carts give silver and brass.
- **Level 7:** driftwood is firewood, and the sea has fish.
- **Level 8:** real ore veins (copper, tin, iron, gold, silver, coal…) run through the strata, with loose ores and stones on the cave floors and clay in places. Limestone and chalk grind to lime, and halite grinds to salt.
- **Level 9:** houses to strip, wardrobes and dressers of clothes, berry bushes gone wild in the gardens, and wildlife: hares, foxes, raccoons, and now and then a wolf.
- **Level 10:** crops ready to harvest, livestock in the paddocks, cattails at the ponds and clay in their beds, bee skeps for honey and wax, and an old quern in the barns.

Some limits:

- The Level 10 crops grow in old, exhausted farmland, so seeds planted back in it will not grow. Hoe fresh soil instead.
- Temporal gears are very rare: a supply box gives one about once in a hundred.

### Reality Stability

The gear on the HUD shows how firmly you are anchored. It is Vintage Story's temporal stability, with the Backrooms' own geography.

- **Each area has its own stability.** Where it is low the gear turns backwards and your stability drains. When yours is low the world distorts, and at zero you take damage.
  - Kind places: the Manila Room, the Level 1 car park, all of Level 4, the Beverly Room.
  - Bad places: Level 0's blackout zones and above all its Red Rooms, Level 2, Level 3 (worst in its flooded tunnels), the hotel corridors and above all the boiler halls.
- **Almond Water** restores some stability when you drink it.
- **Reality Shifts:** about once every 30 in-game hours the lights fail for a few hours. Everything beyond a few steps is lost in black, and stability drains everywhere.

### The topology lies

The rings are only how the world is built; the network of ways between the levels is the real map. It follows two rules, so you can learn it, mark it on your map and build routes out of what you have found.

**Every threshold always leads to the same place.** Where it leads is fixed the first time anyone goes through it, and saved with the world. A threshold is one thing however big it is: both halves of a gate, every step of a stairwell and every part of a lake's bottom lead to the same spot.

**If you walked through it, you can walk back. If you fell, dived or were taken, you cannot.**

- **Two-way thresholds with a partner:** an elevator arrives beside another elevator, a stairwell beside another stairwell, a door beside a locked door. That partner becomes the way back, whatever it would have led to otherwise. Go through it and you come out where you left.
- **Two-way thresholds without a partner** leave a **thin spot** where they put you down: a pale, wavering seam in the air that hums like a translocator. Right-click it to step back through. It stays there for good.
- **One-way thresholds** drop you somewhere fixed, with no way back from there.

This is how Vintage Story's own translocators behave: a repaired one picks its exit once, a partner appears at the far end, and the pair is fixed from then on.

| From | Threshold | To | Way back |
|---|---|---|---|
| Levels 3, 4, 5 | An elevator (everyone standing in the car rides along) | Another elevator in Level 3, 4 or 5; from the hotel, now and then Level 1 | The elevator you arrive beside (in Level 1, a thin spot) |
| Level 1 | Climbing a stairwell | Another stairwell in Level 1, or now and then in Level 4 | The stairwell you arrive beside |
| Level 4 | Climbing a stairwell | Another stairwell on the same floor, or now and then Level 0 | That stairwell (in Level 0, a thin spot) |
| Level 5 | A hotel door: most are locked for good, a few open | Another part of the hotel, Level 3 or Level 0 | The hotel door you arrive beside, which now opens (elsewhere, a thin spot) |
| Level 5 | Climbing the staff stairs behind an open door under a STAFF sign | Level 6 | Thin spot |
| Level 2 | A steel door in a tunnel wall: most are locked, some open | Level 3, Level 4 or Level 1 | Thin spot |
| Level 8 | A vent beside the 9th Road | Level 2 | Thin spot |
| Level 9 | The gate at the end of a field behind the houses | Level 10 | Thin spot |
| Level 10 | Walking into a stretch of barn wall that isn't quite there (in some barns, on the east wall between the stalls) | Level 11, the Endless City | Thin spot |
| Level 11 | An office tower's elevators / a hotel's elevators | Level 4 / Level 5 | The elevator you arrive beside |
| Level 11 | A rowhouse's front door | Level 9 | The locked front door you arrive beside, which now opens |
| Level 11 | A diner's kitchen door | Level 6.1 | The kitchen door you arrive beside in the food court |
| Level 11 | An apartment block's basement door / a substation's steel door / a subway maintenance door | Level 0 / Level 3 / Level 2 | Thin spot |
| Level 11 | A parking garage's ramp down / a dark doorway off an alley / standing in a patch of wheat in a park | Level 1 / Level 6 / Level 10 | Thin spot |
| Level 0 | Falling into a pit | Level 2 | None |
| Level 4 | Pressing the buttons of one of the few hungry vending machines (it takes you every time) | Level 6.1, the Snackrooms | None |
| Level 6 | A wire strung low across a corridor | Level 6.1 | None |
| Level 6 | Stairs down in a chamber, where you can hear waves | An entry room in the ceiling of Level 7, over the sea | None |
| Level 6.1 | Rusty doors / glass doors / kitchen doors / vents (they shut behind you) | Level 6 / Level 4 or 5 / another food court / Level 3 | None |
| Level 7 | Diving into the circle of standing stones / swimming into a cave mouth in the deep | Level 9 / the 9th Road in Level 8 | None |
| Level 10 | Diving to the bottom of a lake | Level 7 | None |
| Level 11 | Falling into an open manhole / a street that has caved in | Level 2 / Level 8 | None |
| Level 11 | Diving into the deep middle of a park fountain | Level 7 | None |

Two things to know:

- A threshold that has become someone's way back no longer leads where it would have. An unused elevator in Level 4 that a city elevator arrived beside now goes to the city.
- Using a temporal gear sets your respawn point, as in any Vintage Story world. Set it near a thin spot or an elevator you know, and dying no longer sends you back to the Lobby.

## How the levels fit together

The levels nest like blobs within blobs around the spawn point, and they are vast. Level 0 alone runs somewhere between about 650 and 4,000 blocks from spawn to its edge, depending on the direction you walk. Each later ring is roughly 600 to 1,000 blocks across on average, so Level 10 lies something like 7 to 15 km out, and then goes on forever.

No ring is a circle. Each one is stretched and lopsided in its own way: a level may end after a few hundred blocks in one direction and go on for several times that in another, and the short way through one level need not line up with the short way through the next. Finding the way on is a matter of mapping, supplies, and luck.

Level 6.1 is not a ring: it is rare sealed cells scattered through Level 6. Where two levels meet there is a full-height wall with a few doorways through it, lined up with the corridors on either side where there are any.

Some areas next to a boundary blend, as the wikis describe the transitions:

| Boundary | What blends |
|---|---|
| Level 0 to 1 | Level 0's carpet wears through to concrete and ceiling tiles go missing. |
| Level 1 to 2 | Pipes start running along Level 1's ceiling. |
| Level 2 to 3 | Level 3 keeps Level 2's pipe bundles instead of cables. |
| Level 4 to 5 | The office carpet turns to hotel red and wood panelling creeps in. |

To resize the levels, change `RingWidths` in `src/Worldgen/WorldLayout.cs` (the average width of each ring in 32-block cells); `Stretch` sets how lopsided they are.

## Level 0: the Lobby

The rules come from the original 2002 photos behind the 2019 creepypasta, the Backrooms Fandom and Wikidot wikis, and Kane Pixels' depiction.

- **Walls and floor:**
  - dingy pale yellow wallpaper with the photo's beaded-line and chevron stripes, or a dot-grid alternate;
  - each wallpaper always has the same trim: chevron walls a thin dark baseboard, dotted walls a low brown chair rail;
  - each area mostly uses one wallpaper, so trim stays consistent;
  - brownish-beige Berber carpet with water stains, and a fissured drop ceiling 3 blocks up.
- **Lights:** recessed fluorescent troffers in a regular grid. Their spacing and orientation change between areas.
  - Most rooms are bright and even.
  - Some are dim, some have failing lights that stutter, buzz or die and flash back on (with a crackle), and a few have gone dark.
  - The hum fades where the lights are dead.
- **Layout:** large carpeted rooms broken up by partition walls that stop abruptly, connected by doorless gaps.
- **Zones:**
  - Lobby;
  - open office, like the famous photo;
  - pillar halls;
  - arches, with cream walls and half-height arched openings;
  - blackout areas: dark, silent, soaked carpet, flooded rooms and the odd sputtering light.
- **Rare rooms:**
  - pit rooms, a grid of 2×2 shafts 30 blocks deep (falling in lands you in Level 2);
  - the Manila Room: 8×8, wooden floor, a door on each side, and a table under a chandelier;
  - the Red Rooms: a block of rooms papered in red and lit by a few dim red lamps, walled off but for one narrow gap in each side. Stability drains there faster than almost anywhere, and the supply boxes inside are untouched.

## Level 1: the Habitable Zone

An endless cross between an underground car park and an abandoned warehouse.

- **Halls:** grey concrete laid out like a real multi-storey car park.
  - Columns every 9 blocks, with yellow-and-black striped feet, painted bay letters A–F and concrete beams under the slab. Some sectors have massive 2×2 columns.
  - Rows of 3-wide stalls with painted dividers, wheel stops and oil stains, back to back along the column lines.
  - 6-wide two-way aisles with dashed yellow centre lines, lane arrows, floor drains and speed bumps. Cross aisles every five bays pass under striped clearance bars.
  - A few abandoned cars (red, blue, white or black), crates and pallets left in stalls, shear walls carrying fire hose cabinets and power boxes, puddles with wet-floor signs and cones.
  - Traffic signs (ONE WAY, no entry, EXIT) stand about, pointing at walls and dead ends, and dead security cameras look down from the walls.
  - **Stair cores** stand at regular intervals: white-painted boxes with black fire doors propped open under lit EXIT signs. Inside are a fire standpipe, a painted "P2" and a flight of stairs that climbs into the ceiling.
  - **Landmarks:** wanderer groups tie coloured cloths with their emblem round columns and leave supplies at the foot.
- **Overhead:** twin-tube fluorescents on chains (whole sections dead or failing together), tube lights on columns, white conduit and red sprinkler mains under the slab.
- **Maintenance halls** fill whole sectors. They are entered through black fire doors under EXIT signs.
  - Walls are white-painted block with a grey dado and a yellow stripe, much brighter than the car park.
  - Tight 2-wide corridors run in a grid, with pipes along one side (some joints drip), power boxes, breaker panels, outlets, fire alarms and extinguishers. There are crude drawings and old portraits on string and nails, loose wiring, hanging EXIT signs at crossings, and plywood and toolboxes against the walls. Their lights stay on through blackouts.
  - Between the corridors are small side rooms behind open doorways or locked steel doors. Most are empty and dark. Others are storerooms, electrical rooms, workshops (workbench, pegboard, plywood), pump rooms with leaking pipes, first-aid rooms with hospital beds, little offices and break rooms, wanderers' camps, and stairwells.
  - Some blocks are big, littered maintenance halls, encampments of tents and bedrolls round a burning barrel, or corridors cutting straight through between rows of rooms.
- **Supplies:** wooden crates, alone or stacked, are the best source of food and Almond Water.
- **Atmosphere:** grey fog, with a low ground fog hanging over the concrete. Humid, 28 °C.

## Level 2: Pipe Dreams

Narrow, dark concrete utility tunnels, 1–2 blocks wide, with straight runs in multiples of 5 blocks. Every tunnel connects; hubs, dead ends and cramped machine rooms branch off.

- **3D pipework:**
  - Bundles of cream lagged, rusty and red fire-line pipes run along the top of every tunnel and meet at junction boxes where tunnels turn or branch. They sit above head height, so they never block the way.
  - Whole stretches of wall carry continuous horizontal pipes, with risers and red valve wheels along them; other stretches are machinery, brick or hazard signs.
  - Here and there a cracked joint hisses and puffs steam.
- **Lights:** sparse buzzing fluorescent fixtures in white or orange, wired in series, so long sections are completely dark.
- **Doors:** now and then a steel door is set in a tunnel wall. Most are locked. Some stand open on a small storeroom of shelving, boxes and a dead computer. A few, which look no different, open onto Level 3, Level 4 or Level 1.
- **Props:** machine cabinets line the machine rooms. Where tunnels widen there are oil drums (some still hold Almond Water), flatbed trolleys, toolboxes, wooden crates and cardboard boxes, and the pieces of dismantled machines lie against the walls. There is the rare forgotten supply box. Food is scarce.
- **Atmosphere:** a dark, murky haze. Hot, 38 °C.

## Level 3: the Electrical Station

A hot (35 °C), cramped maze of derelict brick and two-tone glazed-tile maintenance halls fitted with electrical machinery.

- **Layout:** 2-wide corridors on a lattice, joined into one connected maze.
  - Some links are 1-wide squeezes. Some stretches are floored with steel grating.
  - Many side routes are blocked by indestructible white bars, so the way on is visible but out of reach. Some have a plaque beside them: OUT OF BOUNDS, DO NOT ENTER.
- **Machinery:** transformers, conductor coils, switchgear cabinets, industrial fans, generators and cable spools stand in niches lining the corridors, on hazard-striped floors.
  - The walls carry pipe runs, cable bundles, pressure gauges, knife switches, junction boxes, DANGER HIGH VOLTAGE signs, alarm bells, caged bulkhead lamps and the odd sparking outlet.
  - Cable bundles in trays overhead droop in loops and loose ends. More cables trail across the floor.
- **Lights:** sparse amber fixtures; whole stretches are dark.
- **Electrical rooms:** the solid blocks hold rooms of cinder block, each with a small sign beside its door bearing a number and a line of jumbled text.
  - Room types: machine rooms of switchgear and transformers, generator rooms, boiler rooms (with a pool of the scalding black sludge they make), control rooms (an operator's desk facing the meters), assembly lines whose conveyors still carry parcels, transformers caged behind bars, supply caches (this is a loot-rich level), freight elevators, and barred window rooms glowing with impossible daylight.
- **Rare:** a whole cell becomes a vast transformer hall. Rarer still is a **Sanctum**: a hushed hall of pale masonry with a red carpet between columns and candelabra, leading to a winged statue on a pedestal.
- **Manholes:** these drop into flooded utility tunnels beneath the corridors, where the water is freezing (−4 °C). Ladder rungs lead back up.

## Level 4: the Abandoned Office

One endless, quiet, cool (15 °C) office floor, almost completely devoid of furniture.

- **Feel:** grey carpet with darker marks where desks once stood, scattered papers and coffee stains, drywall with a dark skirting.
  - The drop ceiling has fluorescent troffers (about half dead), air diffusers, sprinkler heads and water-stained tiles, and the odd tile is missing.
- **Windows:** most are papered over or shut behind blinds. The few left clear look out on rain and fog that never end; their grey storm light is often the main light, and you can hear the rain.
- **Walls:** evacuation maps, fire alarms with strobes, extinguisher cabinets, stopped clocks, light switches by the doors, wall phones, framed motivational posters, and the pale marks of pictures long taken down.
- **Open-plan floors:** columns with dead plants beside them, chairs and boxes left behind, cubicle farms (some cubicles cleared out), and now and then a deserted reception.
- **Office blocks:** a corridor grid of small rooms. Most offices are emptied out and some are locked. There are also glass conference rooms, break rooms (counter, sink, microwave, fridge), copy rooms, humming server rooms, storerooms, a manager's office, stairwells under EXIT signs whose stairs climb into the ceiling, and elevator lobbies with two-wide lift doors.
- **Almond Water:** drinking fountains, water coolers and vending machines still give it. Use them to take a bottle; each has a few left.
  - A few vending machines give nothing. They take whoever presses their buttons to the Snackrooms, every time, and always to the same food court.

## Level 5: the Terror Hotel

A 1930s grand hotel that never ends (20 °C), oddly clean and well kept.

- **Corridors:** long, 3-wide, double-loaded corridors (rooms on both sides).
  - Red-and-gold damask carpet, or walnut boards under a runner.
  - Mahogany wainscot under red panels in gilt frames, candle sconces and dome lights.
  - On the walls: portraits, gilt mirrors, landscapes, house phones, fire hose cabinets, clocks, and brass speakers playing jazz from nowhere.
  - Along the walls: console tables with lamps and dried flowers, bookshelves, curio cabinets, sofas and armchairs, radiators, luggage carts, room-service trolleys, laundry carts and ice machines.
  - Room-service trays left on the carpet outside doors, the plates still covered.
- **Elevators** are rare. Each is two blocks wide in a cross-corridor wall, with a call plate beside it. Most are antique copper cages under a floor dial; a few are modern lifts.
- **Guest rooms:** numbered doors with gold plaques, more than half locked. A ceiling fan turns over each furnished room. Open rooms are often fully furnished: the bed's head against the back wall, nightstands with lamps, a wardrobe, a writing desk with a green banker's lamp, an armchair or floor lamp, a suitcase, and a rug on bare boards. Now and then a turntable plays jazz.
- **Grand lobbies:** a taller ceiling, red faux-marble columns over white marble, and chandeliers.
  - Seating groups round coffee tables, a front desk with a guest book and bell, a grandfather clock, palms, luggage carts and bookshelves.
- **Dining halls:** round tables laid with china and candles for a dinner nobody comes to, chairs drawn up, chandeliers, a grand piano.
- **The Beverly Room:** a ballroom lined with doors on every side, most locked, a few opening onto somewhere else. On the small table under its great chandelier are a half-finished game of Mahjong and drinks nobody has touched. Placards stand beside its four real doors.
- **Boiler halls:** STAFF ONLY doors lead into hot (42 °C) halls of stained plaster crowded with pipes, valves and gauges. Barred machinery bays hold boilers, glowing furnaces and coal, under pipes and steam leaks.

## Level 6: Lights Out

A maze of grey concrete corridors (16 °C) in darkness that light barely reaches: a candle shows the floor at your feet, a torch a few steps, a lantern a stretch of corridor. Now and then the dark lifts for a heartbeat. Things scuttle, breathe and whisper out of sight. Stability is low and drifts.

- **Navigation fails:** the map only records what is within arm's reach. Chalk marks are the one thing that stays where you left it.
- **M.E.G. markings:** earlier explorers left arrows to the exits, crosses at dead ends, handprints and scratches on the walls.
- **A light switch** turns up on a wall now and then. It does nothing.
- **Chambers** open off the corridors. Deep in the level, some hold stairs down toward the sound of waves.
- **Tripwires** strung low across straight corridors drop you into the Snackrooms.
- **What others left:** at some dead ends lie a dead flashlight, a backpack or a bedroll. Water stands on the floor in places.

## Level 6.1: the Snackrooms

A rare, sealed food court inside Level 6 (21 °C), bright and safe, with the highest stability anywhere.

- Restaurants with counters, registers, stoves and fryers; convenience stores with shelves; seating areas with café tables, ficus trees and vending machines; a mall map.
- Vending machines and drink fridges give chips, candy bars, crackers, soda, bottled water, Almond Water and cashew water, and restock once a week. Shelves, stoves and fryers can be salvaged.
- Getting in is unreliable, and so is getting out: every exit leads somewhere different.

## Level 7: Thalassophobia

A dark, endless sea under a concrete ceiling (12 °C, 6 °C below the surface). It gets deeper and darker the further out you go: shallows near the walls, then the twilight zone, the midnight zone and the abyss, with trenches and the odd rocky island.

- **Entry rooms** hang in the ceiling, furnished like a forgotten study, with an open doorway onto the drop.
- **The seabed** holds bones, scrap metal, skeletons, lost backpacks and wreck crates to salvage, and pools of scalding tar.
- **Stability** falls the deeper you dive.
- **Camps** stand on some of the islands, after the manner of Fort Surrender: tents, bedrolls, a lantern, a supply box.
- **Old jetties** run out from the ledges over the water and simply stop. Driftwood and buoys float in the shallows; kelp rises from the twilight zone.
- Saltwater fish swim here. Boats and fishing work as in vanilla.

## Level 8: Cave Systems

Real Vintage Story geology (12 °C): strata of real rock with ores, flooded pockets, stalactites, tar pools, and strata that are wrong, such as office carpet layers and vertical coal seams. Drifters roam the dark.

- **Almond Water** seeps out of the rock beside the road in places. Use a seep to fill a bottle; it comes back.
- **The 9th Road:** a gravel road through the caves, lit by lamps and marked by M.E.G. waypoints, with camps at its crossings. Stability is high on the road and lower off it. Where it reaches another level, it runs on through the wall.
- **In the caves:** cobwebs under the ceilings, quartz and amethyst growing from the rock, mushrooms and loose stones, and now and then the remains of somebody who went off the road.

## Level 9: the Suburbs

An endless neighbourhood at midnight (14 °C) under an open sky that never gets light.

- **The streets:** two-lane roads with a dashed centre line, zebra crossings and stop signs at the junctions, manhole covers, fire hydrants, street lamps (mostly dead), wheelie bins at the kerb and cars parked along it.
- **The houses** differ: siding in white, blue, yellow or green, or brick, with a chimney; a porch with chairs or a garage with a drive and a basketball hoop; flower beds and shrubs out front, sometimes a white picket fence.
- **Houses are dungeons:** living rooms with a sofa and a TV that doesn't work, dining tables, kitchens with cupboards and pantries to search, bathrooms, a main bedroom and sometimes a child's room with a toy box, a laundry, garages with tools and sometimes a car. Family photos, paintings, clocks and mirrors hang on the walls; the ceiling lights are dead. Some houses are locked.
- **Backyards** are fenced: a patio with a grill, and a swing set, a vegetable patch, a garden shed, a dog house or a drained pool.
- Raccoons, foxes and hares roam at night, and now and then a wolf.
- Behind some houses, a path through a field leads to a gate.

## Level 10: Bumper Crop

Endless farmland under a grey overcast sky (18 °C), and one of the safest places in the Backrooms.

- **The fields are vast**, some two hundred blocks across and irregular: spelt, rye and flax with furrows and tractor tramlines running to the horizon, a scarecrow keeping watch; stubble fields with round bales left in rows; meadows of long grass and wildflowers. Hedgerows with the odd oak, or strips of rough grass, divide one field from the next.
- **Farm roads** wander for kilometres, lined with telegraph poles that carry no wires.
- **Farmsteads** stand alone: a farmhouse, a red barn with hay and stalls, a grain silo, a tool shed, an old tractor and plough in the yard. Fenced paddocks hold livestock; ponds lie in hollows ringed with reeds.
- **The soil is thin:** a metre down is a mass of worms. Dig into it and they erupt, biting and killing the crops around.
- **Some barns are thin too:** in some, a stretch of the east wall between the stalls isn't quite there. Its boards look slightly out of true, and dust hangs in front of it. Walk into it and you noclip into Level 11.

## Level 11: the Endless City

A Western metropolis that goes on forever (17 °C), with its own day and night under a thin haze, and the safest, best-connected place in the Backrooms. It is not a ring: it lies some fifty kilometres out past the fields, behind a wall of black glass that no one has been beyond, and the only way in is to noclip. Its streets lie 48 blocks below the other levels' floor, so its towers can rise almost to the top of the world.

- **The grid:** an avenue every hundred blocks and a street every seventy-six, so every block is the same size, cut in two by an alley. Many blocks look alike, and some are identical at a glance.
- **Districts:** downtown, always near the middle and elsewhere in patches, is all towers, up to 80 blocks high, of curtain glass, limestone or concrete, stepping back as they rise; some stand alone on granite plazas. Midtown is apartment blocks over stores, offices and hotels. Further out the buildings are brick, no higher than three storeys: rowhouses behind railed yards, corner stores, churches, garages and substations.
- **A third of the buildings can never be entered.** Their windows are dull black mirrors and they have no doors.
- **The rest have their lights on and their shelves stocked:**
  - office lobbies (reception desk, benches, ficus, stairs that climb into the ceiling and stop);
  - hotel lobbies under a chandelier;
  - apartment halls with mailboxes, a directory and a missing-person poster;
  - diners, grocery stores and bodegas, pharmacies (and farmacias), hardware stores, clothing stores and laundromats;
  - churches with pews and candles, a museum whose galleries hang paintings of the other levels, parking garages with cars on every deck.

  The floors above the ground floor are dark behind their windows, and nobody has been up to them.
- **The streets are empty:**
  - cars are parked along every curb;
  - the traffic lights are dead, stuck on red or blinking amber, and most street lamps are out;
  - there are bus shelters, newspaper boxes, parking meters, phone booths, hydrants and mailboxes;
  - street signs are in English and Spanish;
  - the only sound is a hum like distant traffic that isn't there.
- **Anomalies:** now and then a stretch of sidewalk has come loose and runs on up into the sky.
- **Almond Water is everywhere:** in vending machines, on street vendors' carts (nobody is minding them), in the fridges of every grocery.
- **The subway** runs under every avenue, two tracks in a tiled tunnel, with a station at every third street: platforms, benches, maps, an Almond Water machine, and stairs up to both sidewalks at both ends.
- **Parks:**
  - lawns behind iron railings, gravel paths, trees, benches and lamps;
  - a statue among flowers and a playground;
  - a fountain where the paths meet;
  - in some, a corner of wheat that nobody planted.
- **Scavenging:**
  - Grocery and pharmacy shelves hold canned food, flour and salt, and bandages.
  - Hardware stores hold copper tools, nails, rope and wire. Clothing racks and wardrobes hold clothes.
  - Dumpsters and bags of rubbish in the alleys give paper, rotten wood, glass and bones.
  - Parking meters give copper and silver bits.
- **The ways out are as many as they are hard to notice:** see the table above.

## Building and running

- **Build:** `dotnet build` (needs the .NET 10 SDK). The mod is output to `bin/Debug/Mods/backrooms/`.
  - Close the game first: a running game locks the mod DLL.
- **Run with the debugger from VS Code:** use the *Vintage Story (client + mod)* launch config (F5).
- **Run without VS Code:** `Vintagestory.exe --addModPath "<repo>/bin/Debug/Mods"`
- **Release zip:** `dotnet build -c Release` writes `bin/backrooms_<version>.zip`.

If the game isn't installed at `G:\Games\Vintagestory`, set the `VINTAGE_STORY` environment variable to its folder.

## Code map

- **`src/Worldgen/WorldLayout.cs`:** deterministic layout with no game dependencies. Contains:
  - the level map;
  - one 32×32 "macro cell" per chunk;
  - shared edges, which are a pure function of the edge so neighbours always agree;
  - per-position temperature.
- **`WorldLayout.Level0.cs` … `.Level11.cs`:** how each level lays out a cell. Level 6.1 is in `.Level6.cs`.
  - Level 11 is a separate region rather than a ring (`InCity`), planned a whole city block at a time (`BlockPlan`).
- **`WorldGenerator.cs`:** turns layout tiles into blocks, with one block rule per level. Levels 6 to 10 are in `WorldGenerator.Deep.cs`, including Level 8's 3D caves and geology and Level 7's sea.
  - Level 11 is in `WorldGenerator.City.cs`: façades storey by storey, ground floors, roofs and the subway. Its streets lie `WorldGeometry.CityDrop` blocks lower, so its columns are generated (and lit) over a band of their own.
- **`WorldLighting.cs`:** computes block light directly with a flood fill over the column and its neighbours' light sources.
  - Vintage Story's engine is far slower with this many lights.
  - Light sources are registered with each chunk, so relighting after block changes still works.
- **`src/Lights/`:** failing lights.
  - A block entity swaps the panel's look on the client.
  - Only lights near the player are animated.
- **`src/Salvage/`:** makes structural blocks unbreakable, and the behaviour that strips wallpaper and carpet.
- **`src/Reality/`:** Reality Stability per area, Reality Shifts (scheduled from the seed and calendar, so nothing needs syncing), and Almond Water's effect.
- **`src/Thresholds/`:** the ways between the levels, with arrival points checked to be walkable away from.
  - `ThresholdNetwork.cs` has no game dependencies: what each threshold is, where it leads, which are two-way, and the links written down so far (saved with the world as `backrooms-thresholds`).
  - `ThresholdSystem.cs` notices players going through thresholds, moves them and leaves thin spots.
- **`src/Props/`:** vending machines, water coolers and Snackrooms shelves that dispense items and restock.
- **`src/Deep/`:** surveyor's chalk, the worm mass under Level 10, scalding tar, and the creature spawner (fish, drifters, wildlife and livestock, each only on its own level).
- **`src/AtmosphereSystem.cs`:** per-level fog and sky on the client, blended as you cross between levels: Level 6's darkness, Level 7's depth, the Suburbs' night and Level 10's overcast.
- **`src/Map/`:** the explored-areas map layer, which replaces the vanilla terrain map in Backrooms worlds.
- **`src/GuideSystem.cs`:** swaps the Backrooms pages into the handbook's Guides tab, in Backrooms worlds only.
- **`src/BackroomsModSystem.cs`:** world type registration, climate, spawn, the starting waypoint and debug commands.

## Debugging

- `/backrooms column [x z]` (admin) prints the block stack, block entities and light levels of a column, from the ceiling of a grand room down into Level 3's tunnels. If the chunk isn't loaded, it loads it.
- `/backrooms where` names the level and zone you're in, and its stability.
- `/backrooms goto <0-10>` teleports you into a level.
- `/backrooms shift [hours]` starts a Reality Shift (default 2 in-game hours; 0 ends it).
- `/backrooms dump x z [radius]` (admin) writes the blocks and light of a square of the world to `ModData/backrooms/dump-x-z.bin`, for rendering previews outside the game. Run it twice: the first time loads the chunks.
- `.tfedit` in-game lets you tweak how held and dropped items are positioned.

## Assets

Textures, 3D models, block definitions and sounds are generated by scripts:

- `tools/gen_textures.py` (needs Pillow)
- `tools/gen_shapes.py`: block models such as pipes, fixtures, furniture and machinery, built from boxes
- `tools/gen_blocktypes.py`: block definitions for Levels 3–5
- `tools/gen_sounds.py` (needs numpy and soundfile): hum, flicker crackle, steam, transformer, rain, jazz, waves, and the squelch, scuttle, breath, whisper and chalk effects
- `tools/gen_lore.py`: details added to match the lore more closely (Level 2's doors and clutter, cameras, traffic signs, plaques, ceiling fans, Almond Water seeps).
- `tools/gen_guide.py`: the text of the handbook pages, in a light markup, written into the lang file. Its numbers (uses, recipe amounts, where things are found) come from the block types, recipes and code, so update it when those change.
- `tools/gen_detail.py`: the detail props, wall decorations, signs, doors, elevators and floor variants of Levels 1 and 3–5. Each item is defined once (textures in `detail_textures.py`, helpers in `detail_kit.py`) and gets its texture, model, block definition and English name. It also writes `src/Worldgen/DetailBlocks.g.cs`, the table the world generator uses to find the wall decorations. It calls `tools/gen_deep.py` (textures in `deep_textures.py`) for everything in Levels 6 to 10, including the Snackrooms food and the chalk.
- `tools/preview_shapes.py out.png shapes/block/detail/*.json`: renders rough isometric previews of models, to check them without starting the game.

- `tools/texlib.py`: shared texture helpers (tileable veined marble, gradients).

Large surfaces vary from block to block so they do not tile visibly: floors and carpets are turned at random, ceiling tiles come in several versions (one in a while water-stained) and one stretch of wallpaper in three is older and damp-stained. These use Vintage Story's texture `alternates`.

Re-running them overwrites the files, so remove an asset from its script once you replace it by hand.

The playstyle's name and description must live in `assets/game/lang/worldconfig-en.json`, because the world-creation screen reads them before mod assets load.
