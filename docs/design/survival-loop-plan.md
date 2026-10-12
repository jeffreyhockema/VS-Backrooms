# The survival loop: design and implementation plan

The Backrooms should be survived from a home, in expeditions. Today they are crossed: pick a direction, sprint, and the next level arrives on its own. This plan turns the mod's existing pieces (the rings, the threshold network, the menace director, salvage, Reality Stability, the traders) into a loop where hunger sends you out, what you find decides where you go next, and every trip starts and ends in Level 0.

Everything here reuses a Vintage Story system where one exists. New code is listed per phase in section 9, with the files it touches. Numbers are starting points for the tuning pass, not conclusions.

## Status (2026-10-06)

All five phases are built, with the section 10 decisions taken as recommended. Checked with the layout harness (every sampled gate opens on both sides on four seeds; reachability and threshold links unchanged) and on a headless server (assets, the gear patch and recipes load with no errors; torn boxes, sealed boxes and emptied crates generate where the layout puts them; the scarcity setting scales 101 drops). **Not yet tried in a client:** the gear refusing outside Level 0, prying doors, reading notes, the waypoints, the chalk arrows' direction, and how dens and exposure feel.

Where the build differs from the plan:

- **Gates** are one per stretch of boundary per 10×10-cell block (about 10 boundary edges per gate on every gated boundary), which also guarantees islands a way in. Both cells beside a gate open the same doorway, and break a short way through to open floor if it would meet a wall or a locked room.
- **Exposure** is +0.03 per in-game hour (not 0.08): an hour is two real minutes, so the full +0.3 comes after about twenty real minutes out.
- **Loot shares picked over:** Level 0 65% (blackout zones 40%), Level 1 80%, Levels 2–5 60%, deeper 40%; untouched in Red Rooms, the Manila Room, the spawn cell, the Snackrooms, behind locked doors and in dens. Level 0 stashes in 11% of cells (22% in blackouts; retuned once the rooms gained real corners and stashes stopped failing to find one). Measured: Level 0 has about 0.15 sealed boxes per cell, a third of them den caches; Level 1 still has the most food, about 0.85 sealed crate stacks per cell plus 0.25 sealed boxes, half of those den caches.
- **Dens** only where the roster already has the dweller: Smilers' dens only where it is already dark (Level 0's blackouts, Levels 2 and 8); none in Levels 4, 6, 7, 10, 11. Tells are bone piles, ribcages, a bedroll, a new moth hive prop, and chalk crosses on the walls 8–15 blocks out. In Level 0 a den's hunts are still turned into stalks (the Lobby stays empty).
- **Heat** is +0.06 hunger rate per degree over 30 °C, at most +0.5. Levels 6 and 8 are now 8 °C and 9 °C.
- **Farming at home** was checked in the decompiled game rather than in play: with underground farming on, growth uses the brighter of block and sky light, so under a working troffer (15) crops grow at about 60% of daylight speed, and growth pauses in the cold.
- **Not built:** the draft particles at gates and the map fragment (chalk arrows and notes do the job), and notes resolved where they were found (they are resolved where they are read, so one carried elsewhere still works).
- **Ring widths** are the proposed ones: every world's layout changed.

Reviewed afterwards (2026-10-06), checking against the decompiled game; fixed: a Reality Shift only darkens the client, so Smilers could never be put down in lit Level 0 rooms and would have fled "light" everywhere (the world's light now counts as out while a Shift is on, `Senses.LightsOut`; what you carry still counts); running could never build up noise (its gain was below the decay); a stalking Smiler could still turn to a hunt in Level 0 when stability fell (now never, outside the Red Rooms). Verified rather than assumed: the hunger-speed value format, that `hungerrate` is a registered player stat summed over a base of 1, that spoilage reads the position's temperature (a blackout-zone chest spoils food at ~0.38× against ~0.86× in the Lobby), and the chalk arrows' handedness on six samples.

## 1. Diagnosis: why it plays as a walk

Measured against the code, not impressions.

| What | Now | Effect |
|---|---|---|
| Level boundaries | `LevelBoundaryEdge` pierces every 32-block stretch of boundary wall with 2–3 doorways (`doors = rng.Range(2, 3)`), aligned with corridors where there are any. | The wall between two levels is never an obstacle. Walking outward in any direction reaches the next level. Nothing has to be found. |
| Reaching the edge | `Outward()` is a straight line; the threshold band is the last 15% of the ring plus 40 blocks from the wall. At sprint speed the band is 20–40 s wide. | Spawn rolls run every 2 s at `0.015 + 0.085·m`; at `m ≈ 0.85` that is ~8.7% per tick, a quarter of them hunts. A sprinter sees perhaps one hunt attempt per crossing, spawned 14–24 blocks away and already behind them. |
| Level 0 loot | 7% of rooms ≥ 3×3 get a box, plus boxes per zone (pillar halls 25% of cells, arches 12%, 2 guaranteed in the spawn cell). A box averages 1.2 Almond Water, 0.6 crackers, 0.3 beans (≈ 315 satiety) and a wanderer's kit. | The Lobby is ~4 km²: thousands of boxes. Food is never binding; within 100 m of spawn there is more than a player eats in a day. |
| Level 1 loot | A crate gives 1.5 Almond Water, 1 crackers, 0.8 beans, 1.5 planks and more; stacks are 1–2 high, in stalls, at landmarks, in camps. | Level 1 is a buffet. Nothing in Level 2+ is *needed* for food. |
| Hunger | Vanilla default (`playerHungerSpeed` unset = 1). Only two food groups exist before Level 4 (grain, protein). Nothing spoils. | Hunger is a slow tick with no shape to it. The nutrition system, which is vanilla's own pull toward variety, has nothing to pull with. |
| Respawn | Vanilla world spawn (Level 0 centre), `deathPunishment: drop`. A temporal gear (1% per box) moves it anywhere. | Level 0 is already where you come back to, but there is nothing to come back *for*: no storage, no fire, no water, no reason to have left anything there. |
| Gates between levels | None. Level 6 (dark) and Level 7 (water) are soft gates; everything before them is open to a player with nothing. | The whole chain 0 → 5 is walkable on day one. |
| Entities | Band from ring fraction, dark places, thresholds. Caps 2/4/6. Hunters spawn 14–24 blocks away. Sprinting raises menace but the band is left before anything happens. | Threat is tied to *where* you are, never to *how long* you have been out or *what you are doing*. Running is the counter. |

Five levers come out of this, and they are the five sections that follow: **anchor** the player to Level 0; make the edges **hard** and the way through something you find; turn loot into **caches**, not crumbs; make menace come from **exposure**; and give hunger a **shape** that leads into tools, farming and infrastructure.

## 2. Level 0 is home

### 2.1 The anchor rule

**You only ever wake up in Level 0.** Lore: Level 0 is where you noclipped in, the one place the Backrooms still has a loose thread back to you. Deeper levels do not remember you.

- Respawn always goes to the player's **anchor**: the world spawn until they set one, and never outside Level 0.
- A **temporal gear still sets the anchor, but only when used in Level 0.** Elsewhere it refuses ("This place will not hold you") and is not consumed. This keeps vanilla's own "set your spawn" mechanic and gives the rare gear a purpose: move home to a better room (the Manila Room, a room beside a flooded one for water, beside a thin spot you have learnt).
- `deathPunishment` stays `drop`: your kit lies where you died, in a level you can no longer wake up in. A corpse run is an expedition with a deadline.
- Implementation: a `CollectibleBehavior` patched onto `game:gear-temporal` (`OnHeldInteractStart` → prevent outside Level 0, with a message), and `sapi.Event.PlayerRespawn` as the safety net (a spawn set outside Level 0 in an older world is cleared). `temporalGearRespawnUses` is left at vanilla's value.

### 2.2 What a home needs, and where each piece comes from

Level 0 has light, carpet and wallpaper, and nothing else. Every amenity is an import, which is what makes expeditions have purposes:

| Need at home | Vanilla thing | Level 0 has | Must be brought from |
|---|---|---|---|
| A door that keeps things out (entities do not open doors) | vanilla door, planks | — | planks: Level 1 crates, Level 4 furniture |
| Storage | chest (planks), vanilla crate, baskets (reeds), shelves | carpet bag (3 slots) | Level 1/4 planks; reeds from Level 10 cattails |
| Fire | firepit, fuel | rotten wood (sparse) | Level 1 charcoal, Level 3/5 coal, Level 4 lumber → charcoal pit |
| Light during a Reality Shift | candles, lantern, Firesalt | candles found in boxes | Firesalt (Level 3 coal piles), beeswax (Level 10 skeps) |
| Water | water block within 3 of farmland; buckets | **flooded rooms in blackout zones** (`TileKind.Water` already) | buckets need planks (Level 4) |
| Soil | `soil-low-none` | — | potted plants (ficus, palms: 1 each, already in `salvage.py`), Level 9 yards, Level 10 topsoil |
| Seeds | vanilla seeds | — | **seed packets** (new drop, §6.3): Level 4 break rooms, Level 9 sheds, Level 10 barns; traders |
| A bed | vanilla bed | — | Level 5 beds carry away; or planks + linen (Level 5) |
| Cold storage | vanilla perish rate falls with temperature and in cellars | blackout zones (cold, see §6.2) | — |
| A cooking pot | clay | — | Level 3 flooded tunnels, Level 8, Level 10 pond beds |

Nothing new is needed to make a home; what is needed is for the home to *want* these things, which is what §6 (hunger) and §5 (visits) do.

### 2.3 Routes out

With hard edges (§3) a doorway out of Level 0 is an asset, not a direction. The home's value is the routes known from it:

- **Auto-waypoints** for every threshold the player has used and every boundary doorway they have walked through (`ThresholdSystem` already knows both moments; add the waypoint through `WaypointMapLayer`, titled with the destination level once known). Thin spots that arrive in Level 0 from Level 4 stairwells, Level 5 doors and Level 11 basements are two-way: they are the home's elevator lines, and they should show on the map as such.
- **The Manila Room** is the natural seat: safe, four doors, a table. No new mechanics; mention it in the Starter Guide as a place worth moving the anchor to.

### 2.4 Lore note

The wikis put wanderers' bases in Level 1 (the Habitable Zone) and Level 4, not Level 0. The anchor rule does not contradict that: outposts and traders stay where the lore has them (§4.5 keeps Level 1 camps as the first rest stops); only *waking up* is Level 0's. The framing "Level 0 is the nearest place to the world you came from" is consistent with every account of how people arrive.

## 3. Hard edges: the way on is found, not walked to

### 3.1 Gate cells

`LevelBoundaryEdge` keeps its wall but opens doorways only in **gate cells**: boundary cells chosen by hash so that about **one boundary cell in ten** has a doorway (2 wide, aligned with a corridor where there is one). A ring's inner boundary is some 200–800 cells round, so each level still has dozens of ways in, but they are 250–400 blocks apart along the wall. Exceptions stay: Level 8's wall opens only where the 9th Road runs through; the Suburbs and the fields have no wall; Level 1's maintenance-hall crossings count only in gate cells.

Consequences, all wanted:

- Reaching the wall is not reaching the next level. The player walks *along* the wall, which is where the threshold band is, for minutes rather than seconds (§5).
- The short way through a ring is a fact to learn and record, which the persistent map and waypoints already support.
- The threshold network (elevators, stairs, doors, pits) becomes genuinely the better way, which is what "the entrance/exit network is the game" meant.

The harness validator must confirm, per ring and per world seed, that every ring has gate cells and that each gate opens onto floor on both sides (the existing reachability check extended with a `gates` mode).

### 3.2 Tells near a gate

The lore's Backrooms are full of what earlier wanderers left. Within three cells of a gate:

- **M.E.G. chalk arrows** on walls pointing toward it (the chalk-mark block exists; generate it on wall tiles with `Pier` toward the gate, about one per cell). They also mark the map white, so a found arrow is a lead.
- Level 1's EXIT signs already sit over its boundary doorways; keep them *only* there, so the sign means something.
- A **draft**: a particle emitter block in the doorway (dust drifting through) seen from 20 blocks.

### 3.3 Notes: information as loot

A new item, **a wanderer's note** (`wanderernote`), four variants by what it reveals: *a door* (the nearest gate on this level), *a way* (the nearest elevator, stairwell or door threshold), *a cache* (the nearest den cache or Red Room, §4.3), *a refuge* (the nearest sanctuary or camp). Right-click reads it (a short hand-written line in the lore's voice) and adds a **vanilla waypoint** at the place; the note is used up. The target is resolved from the layout at the place the note was *picked up* (hashed with the note's spot so two notes from one room differ), so notes are useful anywhere. Found in boxes (0.15), desks and filing cabinets (0.1), backpacks and bedrolls at Level 6 and 7 dead ends (0.5), camps (1 per camp), bodies in Level 8.

Why this and not a compass: it is a decision ("600 m north-east, with the food I have?"), it fits the lore (M.E.G. documents, journals), and it reuses waypoints.

Optional: **a map fragment** that marks a 64×64 area as explored on our map layer (the layer already keeps seen areas per world).

### 3.4 Smaller rings

The brief says the levels are large, possibly too large, and that distance is boring once the edge is nothing. With hard edges the distance no longer has to be the gate. Recommended: cut `RingWidths` by about a third, keeping `Stretch`:

```
now:      { 36, 28, 20, 24, 30, 30, 24, 30, 24, 30 }
proposed: { 24, 18, 14, 16, 20, 20, 16, 22, 18, 24 }
```

Level 0's average radius drops from about 1.15 km to 770 m; Level 10 starts around 5–10 km out instead of 7–15. Every world's layout changes; do it in the same release as the gate cells so it is one break, not two.

### 3.5 Locked doors and the pry bar

Every level already has locked rooms whose contents are generated and unreachable: Level 1's steel-doored side rooms, Level 2's locked storerooms, Level 4's locked offices, Level 5's locked guest rooms, Level 9's locked houses. They become the "containers you have to work for":

- **Pry bar** (`prybar`): 2 metal brackets + nails and strips; 20 uses. Hold right-click on a locked door for 5 s: a loud screech (noise, §5.3), then the door opens for good. Doors that only *look* like doors (Level 2's doors onto nothing, hotel doors with no room) say "solid behind it" and cost nothing.
- Locked rooms get slightly better loot than open ones (they are untouched), which is what makes the noise a decision.
- Vanilla lock-picking does not exist; the pry bar is the Backrooms equivalent of vanilla's "break in with a tool".

## 4. Caches, not crumbs

### 4.1 Supply boxes and crates

Two visual states each, decided in the layout so the tell is honest from a distance:

| Block | Looks | Ratio | Gives |
|---|---|---|---|
| `supplybox` (sealed) | lid on, strap intact | 1 in 4 | current table at the reduced numbers below |
| `supplybox-torn` | lid off, straw out | 3 in 4 | carpet fibre, wallpaper strip, paper, 0.1 flint; **no food** |
| `crate-sealed` | lid nailed | 1 in 4 | current crate table, reduced |
| `crate-open` | open, empty | 3 in 4 | 1.5 planks, 0.3 nails |

Reduced numbers for a sealed box: Almond Water 1.2 → 0.6, crackers 0.6 → 0.4, beans 0.3 → 0.25, flint 0.6 → 0.4, candle 0.15 → 0.1; the gear, shiv and temporal gear stay. Sealed crate: Almond Water 1.5 → 0.7, crackers 1 → 0.5, beans 0.8 → 0.4; planks stay 1.5. Dispensers: stock 4–8 → 2–4 (Snackrooms keep 4–8 and the weekly restock).

### 4.2 Where boxes are

Boxes stop being sprinkled and start being *left*. Level 0: the 7%-per-room box goes; boxes come in **stashes** of 2–3 at ~1 per 8 cells, always at a feature (a pillar hall corner, an arch alcove, a dead end against a wall, a Red Room, the Manila Room), plus the two guaranteed in the spawn cell and a sealed one in every Red Room. Level 1: stall crates mostly open; sealed ones at landmarks, in camps and in locked storerooms. Levels 2–5: unchanged placement, with the sealed/open split applied. Overall density target: a player walking at random finds a sealed container about every 150–250 blocks in the heartland and more often near dens and in locked rooms.

### 4.3 Dens and their caches

Danger with loot in it (§5.2 defines dens). Every den has a **cache** at its centre: 2–3 sealed boxes or a toolbox, never torn. It is the simplest risk/reward there is, and the lore has it (Hound packs around supplies, Deathmoth hives in rooms with few entrances).

### 4.4 Food that renews, and where

Nothing in Levels 0–5 renews. That is the point: the early game is scavenging, the mid game is bringing renewal home.

| Source | Level | Renewable | Perishable |
|---|---|---|---|
| boxes, crates, fridges, dispensers | 0–5 | no (Snackrooms weekly) | canned and crackers: no; fruit, cheese: yes |
| Death Rats | 1, 2, 8, 9, 11 | yes (spawned) | yes |
| fish | 7 | yes | yes |
| berry bushes, hares, raccoons | 9 | yes (vanilla regrowth) | yes |
| crops, livestock, skeps | 10 | yes | yes |
| a farm at home | 0 | yes | yes |

### 4.5 Traders

Keep them as they are (sparse, friendly, at camps). They buy salvage and sell seeds, candles, Firesalt and bandages, which is the economy the loop needs; rusty gears are the currency and come from receptions, curios and toy boxes. No change except seed packets added to their lists (§6.3).

## 5. Exposure: pressure from time, noise and place

The director keeps bands and the menace value. Three terms are added so that *how* the player moves matters as much as *where* they are:

### 5.1 The exposure clock

`exposure` per player: hours since they last **rested** (a minute within 6 blocks of a lit firepit, burning Firesalt, a wanderer, or anywhere in Level 0 within 48 blocks of their anchor; or sleeping). It adds `0.08 × hours` to menace, capped at +0.3. Lore: the longer you are out, the more the Backrooms notice you.

What it does to play: a long walk gets worse the longer it runs, which makes a firepit halfway (an **outpost**: firepit, chest, a bit of Firesalt) a real thing to build, and makes "turn back now" a decision. It resets at home, which is the pull back to Level 0.

### 5.2 Dens

Deterministic per cell from the layout (`WorldLayout.Entities.cs`: `Den? DenAt(mx, mz)`), roster-matched, about 1 cell in 25 in the heartland and 1 in 12 in the approach band. A den is a 20-block radius that is **Threshold band regardless of ring fraction**, with its own small roster (one Hound pack, a Deathmoth hive, a Smiler's dark, a rat warren, a Skin-Stealer's lair) and a cache (§4.3).

Tells, generated in the cell so the player can decide before entering: bones and a carcass prop (Hounds), a hive block on the ceiling and moth males fluttering (Deathmoths), gnawed boxes and droppings (rats), the lights of the cell dead (Smiler), a bedroll and a human voice (Skin-Stealer). The glimpse and sound encounters already exist; a den biases them so you hear it two cells off.

The director's `Rate` gains one line (`if (layout.DenAt(...) is { } den && Within(den)) band = Threshold`); spawns inside a den draw from the den's roster first.

### 5.3 Noise

`noise` per player in [0, 1], decaying 0.05/s: breaking a block +0.3, prying a door +1.0, sprinting +0.02/s, a firepit being lit +0.2. Menace adds `0.3 × noise`. Scavenging a room is therefore a choice between speed and quiet, which is the right choice to be making in a den.

### 5.4 Hunters that cut you off

In the threshold band the director knows the nearest gate (§3.1) and the player's heading. Hunt spawns are placed **between the player and the gate** when the player is heading for it (10–16 blocks instead of 14–24), so running for the door runs into the pack. Stalkers in the approach band turn to hunters when the player sprints for more than 4 s (the plan already has running as a trigger; make it fire).

Spawn chance moves from `0.015 + 0.085·m` to `0.02 + 0.12·m`; caps stay. With gates rare, the player is in the band for minutes, which is what the numbers were always sized for.

### 5.5 Visits at home

Level 0 stays empty, as the lore says, with one exception: **during a Reality Shift** the heartland of Level 0 is Approach band for Smilers only (eyes at the edge of your light, never a hunt). A door, a lit room and a bit of Firesalt make the home safe; without them a Shift at home is two hours of being watched. This is the reason to outfit the home, and it costs nothing new: the Shift and the Smiler already exist.

### 5.6 What is not changing

No combat buffs, no weapon progression beyond what the entity plan has, no new entities. Threat goes up through time, noise and place, and the answers stay avoidance: light, fire, doors, routes, timing, Almond Water.

## 6. Hunger with a shape

### 6.1 Rates

- `playerHungerSpeed`: 1.25 (world config; tune 1.25–1.5 after the loot cut).
- **Heat**: in places at or above 30 °C (Level 2, Level 3, the boiler halls) satiety drains ×1.5. Vanilla has no heat harm and thirst was ruled out; this is a small entity behaviour that reads `TemperatureAt` and scales the hunger tick. It makes Levels 2 and 3 cost food, which is the gate they need: carry rations, or go round by elevator.
- **Cold** is vanilla already: body temperature, clothing warmth, freezing damage. Level 3's tunnels at −4 °C and Level 7's water at 6 °C already bite. Consider Level 6 at 8 °C and Level 8 at 9 °C so that the deep levels want the clothes Level 5 and Level 9 give (lore for both is "cool", not a fixed figure).

### 6.2 Spoilage and storage

- Canned beans, crackers, Almond Water, chips, candy: no transition (lore-correct and already so). Fruit, cheese, meat, fish, harvests: vanilla perishable.
- `foodSpoilSpeed` 1. Vanilla's perish rate falls with temperature and in cellars; set **Level 0's blackout zones to 10 °C** in `TemperatureAt` (they are described as cold and damp) so a chest there is a cold store, and Level 3's freezing tunnels become a natural one on the way (verify `GetPerishRate` reads the position's climate temperature; if it only reads room cooling, give the blackout zone's walls the cellar material instead).
- Preservation chain, all vanilla: crock (clay) sealed with fat or beeswax; pickling in a barrel with brine (salt: Level 8 halite through a quern, or Level 11 shelves); honey (Level 10 skeps).

### 6.3 Nutrition as the pull toward variety

Vanilla's five groups raise maximum health when balanced; the Backrooms' early diet is grain and protein only. Nothing to add except making sure each food has its group (they do) and that the groups are reachable in order: fruit from Level 4 fridges and Level 9 bushes, vegetables from Level 9 patches and Level 10, dairy from Level 4 cheese and Level 10 livestock. The health bonus is the reward for the first farm.

**Seed packets** (new item, `seedpacket-<crop>`: turnip, carrot, onion, flax, spelt): a Level 4 break-room drop (0.1), Level 9 shed and kitchen (0.3), Level 10 barn (1), traders (sold). Opening one gives 4 vanilla seeds. Without them farming at home waits on a Level 10 harvest.

### 6.4 Farming at home

Checked against what exists: Level 0 is 22 °C, `allowUndergroundFarming` is on, troffers give light 15 under a lamp, flooded rooms are real water, `soil-low-none` drops from potted plants, hoes come from Level 4 toolboxes or knapping. Verify before relying on it: `BlockEntityFarmland`'s light check with underground farming on, and that crops grow with the `backrooms` climate's lack of seasons. If both hold, a farm in Level 0 is 10 pots' worth of soil, a hoe and a flooded room, which is a shopping list for two expeditions and exactly the kind of goal the loop wants.

Fertility: vanilla nutrients N/P/K; compost from rot (spoiled food, a compost bin from planks), bone meal from bones (Level 9 bins, Level 11 rubbish). Level 10's exhausted farmland stays exhausted (already so).

### 6.5 Livestock

Level 10's animals can be led home with rope (verify vanilla rope-leading in 1.22) through the Suburbs gate, the field gate and whatever route home the player has built. It is the longest expedition in the game and should be: it is the one that ends scavenging for protein and dairy.

## 7. The loop, stage by stage

Each row is a need, what answers it, and the new need that answer creates.

| Stage | Need | Answer | Where | Creates |
|---|---|---|---|---|
| Waking | food, light, a knife | the two spawn boxes, shards, a candle | spawn cell | boxes within 200 m are gone in a day |
| Widening | more food | stashes at features; notes; a Red Room's sealed boxes | Level 0 | a route map; the first Smiler; the first Shift at home |
| The first door | planks for a door and a chest; charcoal | find a gate (arrows, a note); Level 1 crates, camps, a trader | Level 1 | a safe room at home; rusty gears; a corpse to retrieve |
| Fruit and cheese | nutrition, perishable food | Level 4 fridges by a lucky stairwell or Level 2's doors | Level 4 | spoilage → cold store (blackout chest); seeds found |
| A farm | soil, water, seeds, a hoe | pots from 4 and 5, a flooded room, packets | 4, 5, home | harvests → quern, cooking pot (clay) |
| Metal | tools that last; a pick | copper bits (2, 3), clay and coal (3), crucible, moulds | 2, 3 | Firesalt; the boiler halls' heat wants rations |
| Outposts | the exposure clock on long routes | firepit + chest + Firesalt at a junction; a known elevator pair | anywhere | a network drawn on the map |
| Ore | bronze, iron | Level 8's strata; halite → salt | 8 | pickling; armour; the deep levels open |
| Renewal | food that comes back | fish (7), berries (9), crops, skeps, livestock (10) | 7–10 | rope, baskets, a barn at home |

The arrival order of levels is unchanged; what changes is that each level is entered *for* something and left *with* it.

## 8. Lore and Vintage Story

- Everything added has a source: M.E.G. chalk and documents, Firesalt, Almond Water, locked doors, packs around supplies, hives in closed rooms, Smilers at the edge of light, Level 0 as the arrival. Nothing added is a game-ism with a lore coat on it.
- Vanilla systems carried the weight: temporal gear (anchor), waypoints (notes, auto-waypoints), doors and pathing (the safe room), hunger and nutrition, body temperature, perishability and cellars, farmland, compost, crocks and pickling, traders, translocator-style links (already), `playerHungerSpeed` and `foodSpoilSpeed`.
- New code is small and local: a gate-cell rule, a loot split, three menace terms, a den table, two items (note, pry bar), one drop (seed packets), one behaviour (heat), one respawn rule.

## 9. Implementation plan

### Phase 1: the numbers (one sitting; playable on its own)

- `WorldLayout.cs` `LevelBoundaryEdge`: gate cells (hash of the boundary cell and level; 1 in 10; 2-wide doorway; keep the corridor alignment, Level 8 and open-sky rules).
- `WorldLayout.cs` `RingWidths`: the proposed values.
- Loot: `supplybox.json` and `crate.json` reduced; new `supplybox-torn`, `crate-open` blocktypes (textures in `gen_textures.py`); a `Torn`/`Open` bit on the tile (`Tiles.cs`) set in each level's placement; `WorldGenerator` picks the block. Level 0 placement rewritten to stashes (`WorldLayout.Level0.cs`: `PlaceBoxNearWall` → `PlaceStash`); `Dispensers.cs` stock range.
- `worldconfig.json`: `playerHungerSpeed: 1.25`.
- Anchor: `src/Reality/AnchorSystem.cs` (the gear behaviour via a JSON patch on `game:itemtypes/resource/gear-temporal.json`, and `PlayerRespawn`); lang strings.
- Menace: spawn chance; hunters placed toward the gate; sprint → hunt trigger (`MenaceSystem.cs`, `AiTaskMenace.cs`).
- Harness: `gates` mode (count and reachability per ring); re-run `validate` and `overview`.
- README and `gen_guide.py`: the Starter Guide's first steps (the anchor, torn versus sealed boxes, the wall is solid but for a few doors).

### Phase 2: finding the way

- `wanderernote` item and its four resolvers (`WorldLayout` queries for nearest gate, threshold, cache, sanctuary; `ThresholdNetwork` already lists thresholds); drops added in `salvage.py`, boxes, camps, Level 6/7 props.
- Auto-waypoints in `ThresholdSystem` (used thresholds, gates walked through); the map layer marks gates seen.
- Gate tells: chalk arrows within three cells (`WorldLayout.Entities.cs` knows gates; generator places the chalk block), the draft particle block, Level 1 EXIT signs only at gates.
- Handbook page *Finding the Way* (notes, arrows, thin spots, outposts).

### Phase 3: exposure

- `MenaceSystem.cs`: exposure clock (rest detection reuses `Senses` wards and the anchor), noise (block-break, door-pry, sprint and firepit events), den band; `Roster.cs`: den rosters.
- `WorldLayout.Entities.cs`: `DenAt`; per level, which den kinds and where (never in sanctuaries, camps or the spawn cell's neighbours).
- Den tells: props from `gen_detail.py`/`gen_lore.py` (bones, carcass, hive, droppings, a gnawed box); den caches in the layout.
- Level 0 Shift visits (Smiler only, Approach, heartland, during `ShiftStrength > 0`).
- `/backrooms menace` prints exposure, noise and den.

### Phase 4: needs

- Heat behaviour (`EntityBehaviorBackroomsHeat` on the player: scales the hunger tick by temperature); Level 6/8 temperatures; blackout zones at 10 °C.
- Pry bar item and the `Sealed`-door interaction (`SalvageSystem` already owns block interaction; locked doors per level need a "room behind" check in the layout).
- Seed packets (item, drops, trader lists).
- Verify farming at home (light, climate) and fix what is needed; verify perish rate against position temperature; verify rope-leading.
- Handbook: *Making a Home* (door, chest, cold store, farm shopping list), *Food* (what spoils, how to keep it).

### Phase 5: tuning

- Play-test the first two in-game days from a fresh world with the logs (`client-chat.log` for damage, the entity log for encounters), then Levels 1–4.
- World setting **Backrooms scarcity** (Plentiful / Normal / Sparse): a `BlockBehavior` on our containers that scales food drops at break time; in `worldconfig.json` beside `backroomsMenace`.
- Numbers to revisit with data: gate density, stash spacing, hunger speed, exposure slope, noise weights, den density.

## 10. Decisions

Recommendations in bold.

1. **Anchor rule: hard, or gear-anywhere?** **Hard: the gear only works in Level 0.** Gear-anywhere keeps the current game, where nothing is home.
2. **Shrink the rings now?** **Yes, with the gate cells, as one world-breaking change.** Waiting means breaking worlds twice.
3. **Heat as hunger?** **Yes.** It is the lightest mechanic that makes Levels 2 and 3 cost something, and it reuses the temperatures already set.
4. **Pry bar and locked rooms?** **Yes.** It gives every level containers to search that already exist, and it makes noise a choice.
5. **Hunger speed 1.25 or 1.5?** **Start at 1.25**; the loot cut does most of the work, and 1.5 with sparse loot risks the first day being lost to arithmetic.
6. **Scarcity setting?** **Yes, in phase 5**, once the Normal values are played.
7. **Level 0 Shift visits?** **Yes, Smilers only, never a hunt.** Without some pressure at home there is no reason to fit a door.
