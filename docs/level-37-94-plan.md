# Levels 37 and 94: research, design and integration plan

Two new levels. **Level 37, "Sublimity" (the Poolrooms)** is an endless white-tiled water complex with no entities, where the danger is the dark and the depth. **Level 94, "Motion"** is a stop-motion diorama of round green hills, 1950s houses and a castle on a glass mountain. Its days are safe; its nights belong to the Animations.

This is a design only; nothing is implemented yet. Section 9 lists the decisions for the user, each with a recommendation.

## Status (2026-10-06): implemented, with the recommended answers to section 9

Verified with the layout harness and a headless server (chunks generated and rendered from dumps); **not yet played in a client.**

**Built:** both regions (ids 12 and 13, 102 km west and north of spawn in a default-size world), their layouts, blocks, lighting, fog and sounds, every threshold in section 2.2 (both ways where two-way), Level 37's relief, Reservoir and red water, Level 94's day and night, playing doll, the castle's alarm, the daily throne-room door and the King's trial, the handbook pages and the README.

**Checked:**
- `tools/mapgen` `regions`: 60/60 arrivals in each level, none in a pocket.
- `links`: every new threshold leads somewhere and back, and survives save and load.
- `motionstats`: no step higher than one block between neighbouring ground tiles.
- `poolstats`: about 54% of Level 37 is floor, and 70% of that is lit.
- A before/after layout hash: Levels 1–4, 6, 8 and 10 are byte-identical; 5, 7, 9 and 11 differ only by the new entrances.
- Cells cost 0.35 ms (Level 37) and 3 ms (Level 94) to lay out.

**Polish pass (2026-10-06), at the user's request (look, feel, lore, Vintage Story mechanics), checked against server dumps rendered room by room:**

*Level 37*
- The tile is now a mosaic of 12 cm squares, as in the Wikidot renders.
- Rooms have rounded corners.
- A serpentine hall was added: a winding channel with slits down the outside of each bend.
- Coping tile runs along deck edges over deep water.
- The water is tinted teal through the map region's climate.

*Level 94*
- Houses have two storeys (cream or white clapboard; one shingle colour per house, red or brown).
- Fences are white pickets, and the front yards have flower beds.
- The turf and the clay under it can be dug: soil and red clay, a Vintage Story clay source. The rim is sealed underground.
- The heaps near the mountain are bigger, with cars on their sides and staircases climbing to nothing.

*The castle*
- The ball pit is sunk into the floor; you wade through it at half speed.
- The throne room is a dim dining hall: panelling, a maroon carpet, two chandeliers.
- The blinding halls are white throughout.

*Rules*
- Shelter now means being under a house's own roof; a porch no longer counts.

**Deviations from the design:**
- **Level 37's plan blocks** are a strict 3×3 grid of squares, each filled by one room (a natatorium or a tunnel can take two), with halls on the lattice between. Placing rooms at random left them as islands in solid tile.
- **Level 37.1 is not one-way inside.** Its water slows wading to half pace, but nothing pulls you down and retracing your steps works.
- **Water is vanilla water.** The teal is in the underwater fog, and the red in the Reservoir's fog and its red-filmed tile.
- **The salt bath at home was not built.** The salt poultice was.
- **Level 94's hills are 4–13 blocks high,** not 8–24, so they can be walked: parabolic domes no steeper than one block per block. Houses stand on level lots whose yards ramp down to the hill. (Two storeys tall, so they read as the pictures do.)
- **No "carelessly set down" houses, and no glass spiral steps.** The mountain is climbed by its one-block terraces.
- **Shelter is simply being under a roof.** Level 94's houses have doorways, not doors.
- **The castle is one storey.** Its slides are props.
- **All four throne-room doors look the same.** Only the day's door opens.
- **The nightmare is the ordinary entity at one and a half times its health,** not a clay version.
- **Signs are scattered at junction corners** (8% of the tiles there; three in four are STOP), not placed one per junction.
- **Twilight is fixed hours:** 19:00–21:00 and 04:30–06:30.
- **Cinemas and baths:** 7% of midtown apartment lots become cinemas, and 40% of substations become public baths.
- **Animations and Robo-Men** are new models built in `tools/gen_models.py` (see the entity review sheets). Their choppy movement is authored in their animations as held keyframes.


---

## 1. What the lore says

Sources, in order of weight: the Wikidot wiki (primary canon, as for every other level in the mod), then Miraheze and Fandom as second opinions, then the well-known depictions. The full research briefs, with citations, came from two research passes on 2026-10-06. The pages they fetched are kept in that session's scratchpad.

### 1.1 Level 37: Sublimity

**Canon (Wikidot, by egglord; Survival Difficulty 0: Safe, Unsecure, Devoid of Entities)**

- "An expansive complex of interconnected rooms and corridors submerged in undulating, lukewarm water."
- **Tiles.**
  - White ceramic tile on floor, walls and ceiling. "Eerily pristine", every tile identical and undamaged, and practically indestructible.
  - The only other colour is the blue-green of the water.
- **Structure.** The rooms are "varied, but strict in design", connected "in a senseless manner", none with an identifiable purpose, and "much too large to properly serve the function of a pool". Specifically:
  - far too many pillars rising out of the water;
  - open water with no ledge to climb out onto;
  - light from irregular angles that leaves some areas in complete darkness;
  - staircases that descend straight into deep pits of water;
  - deep zones entered by stairs or by holes underwater, where "one could easily drown" for want of light and of ways out.
- **The water.**
  - Epsom salt, plus unidentified compounds, relieve pain and calm.
  - A constant gentle ripple with nothing to cause it.
- **Sound** is "severely altered": it cuts off abruptly with no echo, and speech is muted. Now and then the water grows loud enough to drown everything else out.
- **The journal "My Musings"** is the theme of the page. It begins as "My first breathing point in a storm of chaos" and "a warm embrace". Then: "Another cannot help but notice a feeling of dread wash over them as they notice the strange, lightless corners." Peace that turns to dread is the whole level.
- **No entities, and no other wanderers, have ever been met here.** There are no bases and no resources.
- **The four Wikidot renders** define the look:
  - a curved serpentine hall with tall rectangles of warm light falling on the wall from unseen slit windows;
  - a flooded corridor with a steel handrail;
  - a tunnel of tiled arch rings with steps rising out of the water, ending in a black round tunnel mouth;
  - a domed rotunda round a circular pool with a pool ladder, ringed by arched openings glowing white.
- **Sub-level 37.1, "The Sanguine Reservoir" (SD 3).**
  - An exact copy of 37 that you drift into without noticing. First the light fades, then the water turns viscous ("as if not letting go"), and retracing your steps no longer works. In full dark, a red tint shows in the water and bright red sprouts give light.
  - A distant chanting lures people in. "People lying at the bottom of that pool."

**Ways in and out**

| Source | Entrances | Exits |
|---|---|---|
| Wikidot | submerging in the waterparks (Levels 58, 119); the porcelain-tiled areas of the Lukewarm Hotel (233); underwater areas of 130; an arcade on 25 | dark enclosed tunnels → 43; immersion → 130's pools; corridors → 233 |
| Fandom | underwater spots in **Level 7**; oases (46); inflatable pools (54) | dark areas → 37.1; long corridors → **Level 4**; tunnels → 43; stairs → 34 |
| Miraheze | a cyan door marked **POOL** (Level 36); **Level 7**; staying in a 233 pool | dry corridors → **Level 4**; tunnels → 43; drowning → 98 or 67 |

All three wikis agree on one exit: **dark tunnels lead out**.

**Contradictions.**
- Class 0 on Wikidot, Class 1 on Fandom.
- Whether the water is drinkable: Fandom says it carries Legionella and E. coli.
- Windows and sunlight: never in Wikidot's text, but in all its renders.
- Fan art adds inflatables and pink sunsets, which Fandom's own 37.2 calls a misconception about 37.

### 1.2 Level 94: Motion

**Canon (Wikidot, by Stretchsterz et al.; Survival Difficulty 3)**

- **Three zones:** "a large town, a floating castle, and grass hills, but everything has a grainy effect, as if this place was crafted". The whole level looks like a 1930s–50s stop-motion puppet film.
- **The hills** go on forever, and they are what the Wikidot renders show:
  - perfectly round domes of mown grass with stripes, each crowned by one cream two-storey gabled house with a red shingle roof;
  - a straight path up to each house, and some houses set down tilted on the slope;
  - white picket fences, winding asphalt roads with kerbs, a STOP sign and a NO OUTLET sign;
  - a lone round tree, and a white water tower on a hilltop that holds Almond Water;
  - cars parked in the middle of nowhere, and furniture, or whole single rooms, standing alone on the grass.
- **The town:**
  - small houses furnished in 1930s–50s style, and 1930s cars;
  - **milk vans full of Almond Milk**;
  - a central **fountain running with Almond Water**;
  - **siren poles that play happy cartoon music** all day.
- **Day and night.** The town is safe by day with no entities. At nightfall the music stops, strange laughter comes from all around, and the Animations come out. The music returns in the morning.
- **The gradient.** The houses grow stranger the nearer you get to the castle. First ordinary houses, then a lone kitchen in a field, then a bedroom that is one wall and a floor, then random piles of furniture (discovery log).
- **The Castle of the Transparent Mountain.**
  - A small white castle with red roofs on a huge cone of glass that reflects the clouds.
  - Inside, nothing is animated: it is "normal". It is a seemingly endless funhouse:
    - halls that loop, and slides between rooms;
    - ball pits and playgrounds;
    - blindingly bright halls;
    - an **animation studio** holding a miniature replica of the town, with sketches "as if it was being made into a movie".
  - **Robo-Men**, 1930s tin-toy robots, guard it. They turn hostile if you touch or use anything there, and they lose people in the bright halls.
  - The **throne room's door appears at random**: each person found their own door, and all of them came out in the same room.
- **Animations (Entity 32).**
  - 1930s–50s puppets, clay and wooden figures that move in choppy stop-motion and hunt anything that does not look animated.
  - Clay ones smother; wooden ones club.
  - They are very strong and very dumb, so **hiding works best**. A metal pipe can still knock a wooden head off.
  - They chant "All glory to the King!"
  - The **Death Rats here have become stop-motion rats**, so the Animations ignore them.
  - Advice on the page: "Leave Level 94 before it becomes nighttime."
- **The Animated King (Entity 33).**
  - A twisted stone statue with a sword and a crown named Machination.
  - "The King is only what you imagine him to be. The King can only do what you think he can do." Fear feeds him.
  - His trial: you are seated at a table with two chairs and face your own nightmare in animated form.
    - Win, and he bursts into light: you are sent to a main level (Level 1 or Level 4 in the log) or back to the town.
    - Lose, and you become one of his puppets.

**Ways in and out**

| Source | Entrances | Exits |
|---|---|---|
| Wikidot | a rectangular hole in the ground of The Hub (you fall onto the hills and **land gently**); noclipping into the **cinema screen** of Level 68 | the King's trial → a random main level (**1**, **4**) or the town; houses → **Level 7** (a house flooded with water), **Level 9**, 53; a train table → 111; a **rusted gate at twilight** → 442; outskirt buildings → 208 |
| Miraheze | a childish house in **Level 9**; coloured grass (93); paintings (159) | the King's trials → **Level 9**; houses → Levels 0–16 |

**Contradictions.**
- The castle: a glass mountain with a funhouse inside (Wikidot), or a "Sikeston" water tower with a dining hall (Miraheze).
- The trial: a nightmare fight (Wikidot) or errands (Miraheze).
- Fandom's Level 94 is a different level altogether ("Haphazard Remnants") and is ignored here.

---

## 2. Where they fit

### 2.1 Not rings: noclip regions, like the city

Neither level belongs in the ring sequence. The rings model "walking deeper". These two are places you *fall into*: through water, a door that shouldn't be there, a cinema screen. Level 11 already set the pattern: its own region far out in the fields, a rim nobody passes, and reached only by thresholds. Both new levels follow it.

| | Level 37 | Level 94 |
|---|---|---|
| Region | West of spawn, as far out as the city is east | North of spawn, as far out |
| Size | Radius ≈ 1/3 of the city's, so endless to anyone in it | The same |
| Rim | Unbroken tile wall, indistinguishable from any other wall | **A painted backdrop**: a cyclorama of hills and sky, 50 blocks high. The edge of the film set |
| Floor | 14 blocks below the shared floor (`PoolDrop`), for domes up to 15 high and pits down to 22 | 30 blocks below (`MotionDrop`): valley floors at 0, hills to +26, the glass mountain to about +62 |
| Sky | Enclosed | Open, with vanilla day and night |

Internally they are levels **12** and **13**. Levels are array indices throughout the code, for temperatures, fog, stability and lang keys. A small `DisplayNumber(level)` map turns 12 into "37" and 13 into "94" for everything the player sees (titles, waypoints, notes, the handbook, `/backrooms tp 37`).

### 2.2 Their part in the threshold network

Canon connects them to levels the mod doesn't have (43, 58, 68, 130, 233, The Hub). Each of those links is redirected to the nearest equivalent the mod has, keeping the *method* canon describes (dive, corridor, door, screen, gate, trial). The two network rules hold throughout: every threshold always leads to the same place, and you can walk back through anything you walked through.

**Level 37: the safe crossroads with nothing to eat.** Five levels touch it, so it becomes a strong shortcut. Canon's own price keeps it fair: no food, deep dark water and getting lost.

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| Level 5 | A cyan door marked **POOL** in a cross corridor (about 1 in 12 Beverly regions) | A POOL door in Level 37 | The POOL door you arrive beside | Miraheze's POOL door; Wikidot's hotel (233) link |
| Level 7 | Diving into a patch of **white tile on the seabed** in the twilight zone | Level 37, surfacing in a rotunda pool | None (one-way) | Fandom and Miraheze: underwater spots in Level 7 |
| Level 9 | Diving to the bottom of the one backyard pool in a hundred that is **still full**, lit teal at midnight | Level 37 | None | Wikidot: submerging in pools (58, 119) |
| Level 11 | The changing-room door of a **public baths** building (low-rise districts) | Level 37 | The changing-room door you arrive beside | Wikidot: porcelain-tiled areas (233) |
| Level 37 | Walking into a **black round tunnel mouth** at the end of an arch-ring tunnel | Level 7, on a ledge over the sea | Thin spot | All three wikis: dark tunnels lead out (to 43, a water park; the sea is our water level) |
| Level 37 | A long **dry corridor** whose tiles give way to grey office carpet | Level 4 | Thin spot | Fandom and Miraheze: corridors → Level 4 |
| Level 37 | Sinking to the bottom of a **deep pit** | Level 9, surfacing in a full backyard pool | None | Wikidot: immersion → re-emerging in another level's pools |
| Level 37 | Stairs down into the dark, in the deepest districts | Level 37.1 (a zone, not a threshold) | Walk out where there is light | Wikidot 37.1 |

**Level 94: the generous level with deadly nights.** Getting in is a fall from the sky; the clean way out is the King.

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| Level 11 | Walking into the screen of a **cinema** (midtown) that is showing a stop-motion picture | Level 94: you drop out of a rectangle of black in the sky and **land softly** on the grass | Thin spot | Wikidot: Level 68's cinema screen; the Hub hole (falling onto the hills, landing gently) |
| Level 9 | The front door of the rare **doll's house**: a house that looks wrong, too clean, cream and gabled | A house's front door in Level 94 | That 94 door, which now opens | Miraheze: a childish house in Level 9; Wikidot: 94's houses → Level 9 |
| Level 94 | The front door of about 1 house in 40 | Level 9, out of a locked front door | The Level 9 door, which now opens | Wikidot (houses → Level 9) |
| Level 94 | Diving into a **house flooded to the ceiling** | Level 7 | None | Wikidot: a flooded house → Level 7 |
| Level 94 | A **rusted field gate** with no sign, open only at **twilight** (in-game dusk and dawn) | Level 10 | Thin spot | Wikidot: a rusted gate at twilight → 442, here the fields |
| Level 94 | **Winning the King's trial** | Level 1 (40%), Level 4 (40%), or back to a town in 94 (20%) | None (a burst of light) | Wikidot entity 33 and the discovery log |

The handbook's "Ways Between Levels" page and the README table both gain these rows.

---

## 3. Level 37: design

### 3.1 The experience

You surface in a domed room of white tile, waist-deep in lukewarm teal water, in warm light from nowhere. Nothing hurts here. Your wounds close while you wade, the hum of every other level is gone, and nothing will ever follow you. Then you notice that this hall goes on too long, and that the corner over there has no light at all. The way on is down a staircase that goes into black water. And you have eaten the last of your food.

Design goals, in order:

1. Calm first, dread second, never a monster.
2. It must read instantly as the Poolrooms: white tile, teal water, light shafts, black corners.
3. "Senseless but strict": the structure is regular, but it makes no sense as a building.

### 3.2 Structure (a skeleton above the cell, as in the level design plan)

The lesson of `docs/level-design-plan.md` applies: levels laid out per cell read as noise. Level 37 is planned in **blocks of 3×3 cells (96 blocks)**. Each block gets one plan from its id, cached with `PlanCache`, as the city does.

- **The spine.** A lattice of **flooded galleries** every 96 blocks, 5–7 wide and 6 high, with stainless handrails along one wall. They wander up to ±6 blocks along their length (sine offset by hash), so they read as curved, serpentine halls. Galleries are always continuous: they are how you cross the level.
- **The spaces.** Each block holds 2–5 of these, joined to the spine and each other by openings, short corridors and underwater holes:

| Space | Size | What it is |
|---|---|---|
| Rotunda | 15–25 across, dome up to 15 high | A circular pool (deep centre) under a stepped dome, ringed by 6–10 arched openings, a pool ladder, a dry rim 1–2 wide |
| Natatorium | 30–60 × 20–40, 8–12 high | A vast rectangular pool hall, shallow end to deep end, with no lanes and no reason. Often missing ledges along the deep side |
| Pillar hall | 20–50 square | Knee-deep, a forest of 2×2 pillars every 4 blocks, far too many |
| Arch-ring tunnel | 3 wide, 30–80 long | Tiled arch rings every 3 blocks over shallow water, steps rising out on one side. **The far end is a black round mouth**: the exit to Level 7 (1 in 3 tunnels), otherwise a dead end of deep water |
| Stair pit | 6–10 square | Broad steps descending into water too deep and dark to see the bottom (8–22 blocks). 1 in 4 is a deep pit (the exit to Level 9) |
| Serpentine corridor | 2–3 wide | Curved walls (rasterised arcs), joining spaces at odd angles |
| Dry corridor | 3 wide, long | Rare (1 per 4 blocks). Dry tile floor; at its far end the tile gives way to grey office carpet: the way to Level 4 |
| Slit hall | any | A wall of tall narrow slits 1 wide, 4–6 high, glowing warm white |

- **Water depth by area.**
  - About 20% dry (rims, steps, dry corridors).
  - 50% shallow: 1 block, knee-deep.
  - 20% chest-deep: 2 blocks, so you wade slowly.
  - 10% deep (pools, pits, natatorium deep ends).
- **Underwater holes** (2×2 openings in a pool's side, 3 blocks down) join some pools to the next space. They are a short swim in the dark, and the only way into a few spaces.
- **"Senseless but strict" in numbers.**
  - Every dimension is a multiple of the tile module, every space is symmetric about at least one axis, every opening is centred on its wall.
  - The *connections* are random: no space faces the way its neighbour does.

### 3.3 Light: shafts and black corners

There are no lamps. Light comes from one place: **slits**.

- A **slit window** is a 1-wide, 4–6-high opening in a wall onto a sealed light well of `poolglow` blocks (pure warm white, light 18). You never see the source, only the glare.
- Where a slit's light would fall, the floor and the opposite wall are laid with **sunlit tile**: the same tile, warmer and faintly emissive (light 6), in tall rectangles that line up with the slits. Vintage Story's light cannot cast shafts, so the shafts are painted into the tiles and backed by real light, like the first Wikidot render.
- Rotunda openings glow the same way: arches onto light wells.
- **Dark corners.** About 30% of floor is out of reach of any slit (light 0–2). The plans place them deliberately: the far end of a natatorium, behind pillar forests, the bottoms of stair pits, every arch tunnel's end. Darkness grows with distance from the region centre, so the level slowly turns from "Sublimity" into the Reservoir.

### 3.4 Mechanics

| Mechanic | Rule | Why |
|---|---|---|
| Safe | Menace band **Safe** everywhere outside 37.1. No dens, no glimpses, no spawns, ever. Not even in a Reality Shift | Canon: devoid of entities; the only level where that holds absolutely |
| Relief | Standing in water in light ≥ 6: heal 0.5 HP every 4 s, stability +0.02/s, and the exposure clock rewinds as if resting | Epsom salt and "a warm embrace". Makes 37 the place to recover between expeditions |
| Stability | 1.35 in light; 0.6 in the dark corners; 0.15 in 37.1 | Peace turns to dread |
| No food | Nothing edible anywhere: no boxes, crates, fridges or fish | Canon: "cannot sustain life". The price of the shortcut |
| Temperature | Air 29 °C, water 31 °C, no heat hunger (below the 30 °C threshold for air) | Lukewarm, and kind |
| Sound | No hum. A soft ambient of ripples and distant drips, which in the dark swells now and then into a roar that covers everything (the `MenaceSystem` noise level is ignored for that time) | Canon: sound cuts off; the water sometimes drowns everything out |
| Ripple | Ambient lapping sounds near water; a very slow current (flowing water at the edges of natatoriums) nudges anyone floating | "Undulating", "its own tides" |
| Drowning | Vanilla breath. Deep pits and underwater holes are dark, so getting lost underwater is the real killer | Canon's one hazard |
| Indestructible | All tile, as structure is everywhere (`SalvageSystem`) | Canon footnote |

### 3.5 What there is to find

Canon gives Level 37 nothing. The mod gives it very little, and only for those who go into the dark:

- **Epsom salt crust** (new item) forms on dry rims in the dark corners, 1–2 per corner. Grind it, or use it as is:
  - a **salt poultice**: Epsom salt + linen = a poultice that heals more than the vanilla one (new recipe);
  - a **salt bath** at home: a barrel of water + Epsom salt, which gives the relief effect for an in-game hour.
- **Drowned wanderers' gear** at the bottom of stair pits and natatorium deep ends: a backpack (the existing `backpack` detail block with its drops), now and then a wanderer's note (which marks a POOL door, a dry corridor or a dark tunnel). Diving for it in the dark is the risk.
- **Lost things on the rims:** a towel, a flip-flop, a pool noodle. Salvage only (cloth, plastic as nothing); there for the eerie human trace.

### 3.6 Level 37.1: the Sanguine Reservoir (a zone)

Like the Red Rooms in Level 0, 37.1 is a zone inside its level, not a separate place. It covers about 1 block in 20, and only beyond 60% of the region's radius.

- **The drift in.** Its border is never a wall. Over the last 64 blocks before it:
  1. the slits thin out and the sunlit tile stops;
  2. then the water turns **viscous**: a custom liquid, `reservoirwater`, that slows you to 40% and pulls you down gently;
  3. then, in full dark, the water is tinted red and **red sprouts** glow on the pool floors (light 5, red). You see by them and nothing else.
- **The chanting** is heard from up to 160 blocks away, from the direction of the nearest Reservoir. It works like the waves in Level 6, but it is a lure, not a guide. Close in, the slithering and whimpering sounds start.
- **Retracing your steps doesn't work.** Inside the zone, the plan's openings are one-way by layout: stairs go down only and holes only lead deeper. The way out is to find light: a stair pit at the zone's far side climbs back into normal 37.
- **Stability** is 0.15 and drains fast. Smilers can appear here; they are the only thing that ever does in Level 37 (canon's "rumoured many-limbed thing" stays a sound).
- **What draws you in.** At the bottom of the Reservoir's pools lie the people (skeleton props) and their gear: the best caches in Level 37, untouched. There is also **red water**: fill a bottle from a sprout pool. Drinking it heals fully and grants an hour of regeneration, but permanently lowers your stability ceiling by 5% (stored on the player). "All visitors are changed permanently."

### 3.7 Look and assets (`tools/gen_pool.py`)

- **Tile:**
  - white, 4×4 tiles per block face (25 cm), thin warm-grey grout, faint glaze highlight;
  - variants: plain, sunlit (warm, emissive 6), rim edge (bullnose), step;
  - 37.1 variants with a dark red film on the grout.
- **Water:** `poolwater`, a copy of vanilla water tinted blue-green, so it reads teal against white tile (fallback: vanilla water with the teal underwater fog below). `reservoirwater` is red-tinted and viscous.
- **Shapes:**
  - quarter-round tile pieces for curved walls and arch rings;
  - stepped dome pieces;
  - stainless handrail and pool ladder (gen_shapes style, real 3D);
  - poolglow (a full emissive block);
  - red sprout (a small glowing plant);
  - towel, flip-flop and noodle props.
- **Atmosphere:** fog very thin and pale (0.003, 0.88/0.92/0.90); underwater, a clear teal (0.04, 0.25/0.55/0.50); 37.1 is close and dark red (0.03, 0.18/0.02/0.03).
- **Map colour:** white with teal water; 37.1 dark red.

---

## 4. Level 94: design

### 4.1 The experience

You fall out of the sky and land softly on a lawn. Everything is too saturated, too smooth, made. Round hills, each with one cream house. Somewhere a siren pole is playing a cheerful little tune that never changes. There is food everywhere: milk vans, iceboxes, a fountain of Almond Water. On the horizon, a castle sits on a mountain of glass. Then, late in the afternoon, the tune slows and goes flat. At dusk it stops, the laughing starts, and you need to be behind a door.

Design goals:

1. The diorama look, unmistakable from the first screenshot.
2. **Day and night as the survival system**: vanilla Vintage Story's oldest lesson (shelter by nightfall) reintroduced.
3. A destination, the castle and the King, that rewards preparation.

### 4.2 Structure

All of it is computed from world coordinates (heights, hills, roads), so it is seamless across cells.

- **Hills.**
  - A jittered lattice of hill centres about 56 blocks apart.
  - Each hill is a smooth dome: radius 18–28, height 8–24, cosine profile, with a flat summit plateau 9–11 across.
  - The ground is the *maximum* of the domes over a flat valley floor, which gives the flat-bottomed valleys Miraheze describes and the separate round hills of the Wikidot renders.
- **Mown stripes.** Grass comes in two shades, in 3-wide stripes at a random angle per hill, so every dome is striped like the render.
- **Roads** follow the valleys, along the Voronoi borders between hill centres, which are the low ground.
  - Asphalt 5 wide with kerbs, winding because the borders do.
  - A **STOP sign** at every junction.
  - A **NO OUTLET** sign wherever a road ends (about 1 border in 5 is dropped, leaving dead ends).
  - Picket fences along about a third of the road edges.
- **Houses.**
  - About 70% of summits have one cream two-storey gabled house (7×9, red or brown shingle roof, dark multi-pane windows).
  - A straight dirt or concrete path runs from its door down to the nearest road.
  - About 15% of houses are **set down carelessly**. Voxels cannot tilt, so the house sits off the plateau instead: sunk into the slope to the windowsills on one side, or with a corner hanging in the air over bare clay.
- **Hilltop landmarks** on the summits without a house:
  - a **water tower** (1 in 12, white, holding Almond Water);
  - a lone round tree;
  - a parked 1930s car;
  - or bare grass.
- **Towns.**
  - One town per region of about 6×6 hill cells, in a valley, never within 400 blocks of the castle.
  - A plaza with the **Almond Water fountain** at its centre.
  - 8–16 small houses round it on flattened lots, a general store and a diner.
  - **Siren poles** at the corners, **milk vans** and old cars along the kerbs.
- **The unravelling (the gradient).** Coherence falls with distance to the castle:

| Distance from the castle | What stands on the hills |
|---|---|
| > 700 | Whole houses, towns |
| 400–700 | Mostly houses; sometimes a lone room (a kitchen on the grass, walls on two sides) |
| 200–400 | Lone rooms; a bedroom that is one wall and a floor; furniture sets with no walls at all |
| 90–200 | Piles of furniture, cars on their sides, a staircase going nowhere |
| < 90 | The foot of the glass mountain |

The gradient is the compass. Things getting stranger means the castle is that way, even when it is out of sight. This replaces chalk arrows as Level 94's navigation tell.

- **The castle** stands at the region's centre:
  - a **glass mountain**: a cone of glass, base radius 70, 58 high, its surface a stepped cone of slightly tinted glass that catches the sky;
  - a **spiral of clear glass steps** winding up the cone, hard to see;
  - on the top, a white castle with red conical roofs, 40 across.
- **The rim** is the painted backdrop: a wall 50 high, painted as more hills under more sky. Walking up to it is the moment the level admits it is a set.

### 4.3 Day and night

Level 94 uses the vanilla calendar: open sky, sun and moon.

| Time | What happens |
|---|---|
| Day (sunrise to 2 h before sunset) | Siren poles play the tune (heard 60 blocks off). Menace band **Safe** everywhere. Stop-motion rats potter about |
| Late afternoon (last 2 h) | The tune slows and drifts flat. The warning |
| Dusk | The music cuts out mid-bar. Distant laughter all round. The Animations come out: band **Approach** in the hills, **Threshold** in towns and within 400 of the castle |
| Night | Animations hunt anything not indoors. "All glory to the King!" heard now and then |
| Dawn | Music starts again. Animations still out are gone the moment nobody is looking at them |

**Shelter is the counter.**

- **Indoors with the door shut is Safe**: inside a house (`Roof > 0`) with every door of that house closed.
  - Animations never open doors; they gather outside and wait. Their shapes pass the windows.
  - A house with a broken-in door is not shelter.
- **Standing still works too.** At night outdoors, a player who has not moved for 4 seconds is a doll to them. An Animation that has not yet reached them loses interest and wanders off.
  - Moving again, or being lit by a held torch, breaks it.
  - Canon: they hunt "anything that does not appear animated". The fan reading: survivors play dead as dolls.
- Sleeping in a Level 94 bed passes the night as in vanilla.

### 4.4 What there is

Level 94 is the opposite of 37: **abundant food, deadly nights**. It is a place to stock up, if you can get out again.

- **Almond Water:**
  - the town fountains and the water towers, which refill a bottle and come back like Level 8's seeps;
  - **Almond Milk** in the milk vans: a new food item (dairy, satiety 300, +0.1 stability). Each van has a few bottles, which restock weekly like the Snackrooms.
- **Houses as pantries.** Each house has:
  - an icebox (cheese, canned goods, butter);
  - a pantry (bread, preserves);
  - a retro TV, a radio cabinet and a rotary phone (salvage: wire, glass, wood);
  - a coin dated 1953 now and then (a trade curiosity the wanderers buy).
- **Stop-motion rats**: edible, harmless, ignored by the Animations.
- Clay-turf grass and clay soil under it: **real clay** (vanilla blue and fire clay) a block down. Level 94 is literally made of clay, which gives the mod a second clay source besides Level 3's tunnel and Level 8.

### 4.5 Entities (`tools/gen_models.py`, `tools/gen_entities.py`)

| Entity | Look | Behaviour |
|---|---|---|
| **Animation, clay** | Lumpy faceless grey-brown figure, thumbprinted | Night only. Slow, grabs and smothers (hold + damage over 3 s). Shatters to clay balls on death |
| **Animation, wooden** | A 1930s jointed mannequin, painted face | Night only. 25% faster than a walking player, clubs hard. Weak to fire. A good hit can knock its head off (instant kill on a critical) |
| **Animation, paper** | A flat cut-out with a crayon face, edge-on it vanishes | Night only. Weak, comes in groups of 3–5, dissolves in water |
| **Stop-motion Death Rat** | The common rat with a clay texture | Day and night, ambient, edible |
| **Robo-Man** | A 1930s tin toy robot with wind-up key and tread feet | Castle only. Passive until anything in the castle is broken or used, then hunts. Loses you in the bright halls |
| **The Animated King** | A twisted stone statue with sword and crown | Throne room only. See 4.6 |

**Stop-motion movement** without engine hacks:
- **Animations:** every keyframe is a **hold**, so poses jump instead of easing (each pose authored twice, 3 frames apart).
- **Locomotion:** walking is a stepped animation over a smooth slide, so the eye reads stepping.
- **AI:** moves in bursts of 0.15 s, the pathing task pausing between them.
- Everything else in Level 94 animates normally, so the Animations stand out.

### 4.6 The castle and the King

- **Getting in.** Climb the glass steps (hard to see; a fall from high on the cone can kill). The castle's gate is open.
- **Inside, nothing is animated**: real textures, real proportions, no grain. It is a funhouse of looping halls on a hidden plan:
  - blue-and-yellow checkerboard floors;
  - pink-and-yellow striped pillars with porthole rings;
  - a red-and-white striped carpet path, star medallions in the floor;
  - slides between floors (chutes of a slippery block);
  - **ball pits** (a non-solid block you sink into, slowing like deep snow);
  - **blinding halls**: light 22 and white fog, where Robo-Men lose you and you lose your way;
  - arcade cabinets (salvage).
- **The animation studio**: a room with a table-sized **diorama of a town** (a large prop), sketches pinned round the walls, and a camera on a tripod. It is pure lore, and the most screenshotted room in the castle.
- **Robo-Men stand guard.** Break or use anything in the castle (a door, a cabinet, a prop) and every Robo-Man within 40 blocks wakes and hunts until you leave the castle or lose them in a blinding hall. The castle is a stealth level.
- **The throne room door** appears in a different hall each in-game day (picked by hash of the day). It is the only door in the castle that is a real door. Through it, everyone arrives in the same throne room: a long dim dining hall, red carpet, a table set for two, and the King, a stone statue at its head.
- **The trial.**
  1. Sit in the second chair (right-click). The door closes. The King speaks: lines from canon, as chat.
  2. He animates **your nightmare**: the kind of entity that has killed you most often (tracked per player; Hounds if nothing ever has). It comes in clay, at 1.5 times its health.
  3. **"He can only do what you think he can do."** The nightmare's damage scales with your Reality Stability at the moment it strikes. At full stability it does a quarter of its damage; near zero, double. Drink Almond Water before you sit down.
  4. **Win:** the King bursts into light (a flash, then the translocation sound). You are carried one-way to Level 1 (40%), Level 4 (40%) or back to a town in Level 94 (20%), each fixed for you by the network's first rule. The first time, you also get **Machination's Crown Shard**: while carried, Animations ignore you in Level 94 (Miraheze's King's Artifact).
  5. **Lose:** you become one of his puppets, which means you die. You wake in the Lobby as always (the anchor rule), and what you carried stays at the table.

### 4.7 Look, sound and assets (`tools/gen_motion.py`)

- **Clay turf:**
  - grass in two stripe shades, saturated green, with a plasticine thumbprint texture;
  - clay soil beneath;
  - dirt and concrete paths;
  - asphalt with kerbs.
- **The houses:** cream clapboard with fingerprinted paint, red and brown shingles, multi-pane windows, white picket fence, 1950s interior wallpapers. Everything is slightly too saturated and slightly grainy: noise in every texture, which is the canon's "grainy, as if this place was crafted".
- **Props:**
  - icebox, retro TV, radio cabinet, rotary phone, 1950s sofa, wood stove;
  - milk van and 1930s car (multi-block, like Level 1's cars);
  - siren pole, water tower, STOP and NO OUTLET signs;
  - fountain;
  - in the castle: glass, white castle wall, red roof, checkerboard, striped pillar, ball pit, slide chute, arcade cabinet, diorama table, easel sketches, camera, throne table and chairs.
- **The backdrop:** a set of large painted panels (sky gradient, distant hills).
- **Sounds** (`gen_sounds.py`, synthesised like the hum):
  - the **siren tune**: a looping 20-second cheerful 1930s-cartoon melody in a music-box and calliope voice, plus its slowed, flattened dusk version;
  - distant laughter, the "All glory to the King!" murmur, the King's light burst.
- **Atmosphere:**
  - by day, crystal clear and saturated: fog 0.002, a sky-blue tint;
  - by night, deep blue;
  - inside the castle, neutral and bright, with white fog in the blinding halls.

---

## 5. Integration: everything that has to know about the new levels

The audit of places that assume the levels are 0–11 and that everything past 9 is open sky:

| Where | Change |
|---|---|
| `WorldLayout.ComputeLevel` | `InPoolrooms` / `InMotion` checked alongside `InCity`, replacing only Level 10's cells |
| `WorldLayout.LevelCount`, `IsOpenSky` | Count 14. `IsOpenSky` becomes explicit (9, 10, 11, 13): **today `level >= 9` would make Level 37 open-sky** |
| `GetEdge`, `BuildMacro`, `ColumnBlock` | New cases. Today's defaults would build Level 10 fields with rock edges in both regions |
| `WorldGeometry.FloorFor` | 12 → FloorY − 14, 13 → FloorY − 30. Every caller already uses it (city work) |
| `WorldGenerator.Generate` | Band bottom and top per level (pits, glass mountain); rain and terrain height maps for 94's hills |
| `WorldLighting.BandBottomFor` | Per level instead of "city or default" |
| `LevelTemperatures`, `AtmosphereSystem.Levels`, `StabilityAt` | Entries for 12 and 13, plus 37.1 and the castle overrides |
| `MenaceSystem`, `Roster`, `Dens`, `Loot`, `Notes`, `Entities.IsSanctuary` | Level 37 Safe outside 37.1. Level 94 band by time of day and shelter. No dens or picked-over loot in either. Notes in 37's drowned bags point to its exits |
| `ThresholdNetwork.Walked` / `Used` | The cases in section 2.2. New `Used` kinds: `pooldoor`, `bathsdoor`, `dollhouse`, `cinemascreen` (walked), `twilightgate` |
| `FindArrival` | Region arrival cells like `CityArrivalCell`. 94 arrivals are high above the ground with a soft landing (no fall damage for 10 s after a threshold drops you) |
| Gates | None: neither region borders a ring through a gate. `IsGate` already skips non-adjacent levels; check that rims never pair with Level 10 |
| `BackroomsMapLayer.SampleHeights`, `MapColors` | Sight sampling for 37's lowered floor and 94's terrain (sample the ground height at the column); colours |
| `MapMarks.LevelName`, `WandererNote`, `AnnounceLevel`, lang | `DisplayNumber`: "Level 37", "Level 94", "Level 37.1"; level titles and hints |
| `/backrooms` commands | `tp`, `level`, `dump` take display numbers |
| `HeatSystem` | 37 stays under the heat threshold; 94 is 21 °C by day, 12 °C at night |
| `CreatureSystem` | Stop-motion rats in 94; nothing in 37 |
| Level 5, 7, 9, 11 layouts | The new threshold features: POOL door, tiled seabed patch, full pool, public baths, cinema, doll's house |
| `tools/gen_guide.py` | Two level pages, rows in Ways Between Levels, Salvage and Recipes (Epsom salt, salt poultice, Almond Milk), What Lives Here (Animations, Robo-Men, the King) |
| `README.md` | Level sections, threshold rows, the new items |
| `tools/mapgen` | Modes `pool <angle>`, `motion`, `castle`, extended `links` and `validatelevel 37/94` |

---

## 6. Survival role

The mod's rule is that each deep level unlocks a survival system. These two are a matched pair:

| | Level 37 | Level 94 |
|---|---|---|
| Teaches | Recovery, and swimming in the dark | Shelter and the clock |
| Gives | Healing, safety, shortcuts between five levels, Epsom salt, the best poultice | Food in plenty, Almond Milk, clay, a free road home (the King) |
| Takes | Nothing to eat; drowning; getting lost; 37.1's pull | The night; the castle's guards; the King, if you sit down afraid |
| Fits the loop | A place to heal on the way out, never a home (no food, no respawn) | A larder you raid by day; the anchor rule still sends you home to Level 0 |

Both keep the survival-loop plan's principle: they are expeditions, not new homes. A temporal gear still only takes hold in Level 0.

---

## 7. Phases

| Phase | Work | Verify |
|---|---|---|
| 1. Regions | Ids 12/13, `DisplayNumber`, explicit `IsOpenSky`, regions, floors, lighting band, map sampling, empty placeholder layouts | Harness `overview` shows both regions; every existing harness mode unchanged (levels 0–11 byte-identical dumps) |
| 2. Level 37 layout | Block plans, spaces, water depths, slits and sunlit tile, dark corners, assets | `pool` renders; `reach` and `validatelevel 37` show no pockets; dry-floor and dark-floor shares within targets |
| 3. Level 37 systems | Relief, stability, sound, Epsom salt, drowned caches, 37.1, thresholds into and out of 37 | `links` round trips; in a headless server, arrival → relief ticks |
| 4. Level 94 land | Heightfield, stripes, roads and signs, houses, landmarks, towns, the gradient, the rim, assets | `motion` renders; sight lines; arrivals land on grass, never on a roof |
| 5. Level 94 nights | Siren music and dusk cue, Animations (3 models, stop-motion animations), shelter and stillness rules, rats, Almond Milk, fountains and towers | Headless: dusk switches the band; a shut house is Safe |
| 6. The castle | Glass mountain, funhouse plan, studio, Robo-Men, daily throne door, the King's trial and the Crown Shard, thresholds out of 94 | Trial run headless with `/backrooms encounter` |
| 7. Words | Handbook, README, lang, version bump | Handbook pages render; README tables match the code |

Phases 1–3 make Level 37 playable on its own, and Level 94 can follow later.

---

## 8. Risks

- **Custom liquids** (`poolwater`, `reservoirwater`). Copying vanilla water into the mod's domain is supported, but viscosity is not a plain liquid property. **Fallback:** vanilla water, with a walk-speed and sink effect applied by the 37.1 zone check in a server tick.
- **Hills cost generation time.** Hill height is a small max over nearby domes per column. Cache each cell's heightfield as the city caches block plans.
- **Glass mountain draw cost.** A 70-radius glass cone is many transparent faces. Make it a hollow shell 2 blocks thick, the inside dark.
- **Choppy movement may look like lag.** It is authored in the animations, not the network, and only the Animations do it. Test in a client early (phase 5) before building all three.

---

## 9. Decisions for the user

1. **Placement.** **Recommended:** noclip regions like the city. Alternatives: Level 37 as rare pockets inside Level 7 or Level 5, like the Snackrooms in Level 6; or both as new outer rings.
2. **Level 37 food.** **Recommended:** none, as canon says, with Epsom salt and drowned caches as the only finds. The alternative is a few sealed boxes in the dark corners.
3. **Level 37.1, the Sanguine Reservoir.** **Recommended:** include it as a zone, with red water's permanent cost.
4. **Level 37's isolation in multiplayer.** Canon: no other wanderer has ever been met there. **Recommended:** skip. Optional: other players are hidden beyond 24 blocks while both are in Level 37.
5. **The King's trial.** **Recommended:** the canon nightmare fight, scaled by stability. Alternative: Miraheze's errand quest (fetch 15 pebbles, kill 3 Death Rats). Either can be deferred, leaving the castle as a funhouse with the King silent.
6. **Night difficulty in Level 94.** **Recommended:** Approach in the hills, Threshold near towns and the castle, scaled by the existing *Backrooms entities* world setting.
7. **The gradient as the only compass to the castle**, with no chalk arrows in Level 94. **Recommended:** yes.
8. **Level 94.1** (the autumn hills, the Wizard, free-willed Animations). **Recommended:** not now; it would make a good later addition reached from the region's far side.
9. **Order of work.** **Recommended:** Level 37 first (phases 1–3). It needs no new entities and is the more famous of the two.
