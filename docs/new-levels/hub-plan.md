# The Hub: research, design and integration plan

**The Hub** (owner tag `hub`, internal id 17, `WorldLayout.Hub`, shown as "The Hub") is the hidden crossroads of the Backrooms. It is a network of dim, silent road tunnels, lined on both sides with great concrete doors, one for every level. Almost all of them are locked. Each opens only to its own **Level Key**, and only one way.

This is a design only. Nothing is implemented yet. Section 7 lists the decisions for the user, each with a recommendation.

## Status (2026-10-09): built; the Tower, the Keymaster, the M.E.G.'s keys and the register added (endless stair deferred)

Verified with the layout harness and a headless server (port 42477), rendered from a dump: `hub-tunnel-render.png` and `hub-door-render.png` here. **Not played in a client.**

**Built** (code: `WorldLayout.LevelHub.cs`, `WorldGenerator.Hub.cs`, `ThresholdNetwork.Hub.cs`, `ThresholdSystem.Hub.cs`, `AtmosphereSystem.Hub.cs`, `Regions/HubSystem.cs`, harness `tools/mapgen/HubStats.cs` + `render_hub.py`):

*The region*
- A fixed radius of 60 cells, `HubDrop` 28 and band depth 4 (room for the Tower later).
- A road graph worked out once per world: ten numbered spokes from a roundabout to the rim ring, five ring roads, and a 96-block jittered lattice of side tunnels. The lattice is pruned to pieces that reach a main tunnel; blind ends get a door.
- Cross-sections as §2.3, except the lamps (see below).
- Doors in slots every 24/16 blocks: 19 live doors, one per level (LINKS.md: no 3999; the 974 door is the pink door). Canon's three are in tunnels 7, 10 and 5.
- About 15,500 dead doors and about 1,400 grey service doors.
- Out in the Far Tunnels: 6 false walls (to Level 4), 4 holes (to 94) and tiled ends (to 37).

*Air and danger*
- Fog: Crossroads, Far Tunnels and Tower; titles 1701 and 1702.
- The near-silent drone, its pitch shifting every few minutes.
- 6 °C, 2 °C out in the Far Tunnels; stability 1.3 / 1.0.
- A sanctuary (Safe band). The roof breaks from the side-tunnel ceiling up (rel 6).
- Wanderers at the M.E.G. outpost (by the Level 11 door) and Camp Amber (by the Level 1 door).

*Doors and keys*
- The carved doors go through `ThresholdSystem.UseHubDoor`:
  - the open doors let anyone through;
  - keyed doors take the key from the inventory (three turns, the key is gone);
  - the pink door opens only for someone carrying something cute (`L974.CarriesCute`);
  - dead doors refuse;
  - every carved door is one-way.
- `HubSystem` swaps the doors' `BackroomsThreshold` for `BackroomsHubDoor` at asset load.
- Key resonance: a positional 500 Hz chime from the door's direction; within 8 blocks it rings at the door and marks it on the map.
- Keys for the existing levels drop from caches broken in their level: dens 4%, sealed rooms 1.5%, worst places 8%, elsewhere 0.2%.

*Ways in*
- Level 1: a grey door with sigil 0 on a maintenance-hall block wall, 1 hall block in 250 in the outer half of the corridor sectors, with chalk arrows. Two-way with a service door.
- Level 2: 1 steel door in 40, with a chalk circle. Two-way.
- Level 37: `PoolCorridorEndKind`, the one shared roll per dry corridor (15% Level ! / 20% Hub / 65% carpet; the Level ! share stays carpet until that level draws it). Asphalt end ↔ Hub, two-way.
- The rare temporary door (about once in 10 in-game days per player, 5 minutes, saved and cleaned up after a restart). One-way.

**Checked**
- `hubstats`: 11,277 cells at 0.12 ms each (the plan included). 100.00% of walkable tiles reachable from the roundabout. All 19 level doors placed and reachable, each leading where it should (6.1 via the Snackrooms finder).
- `regions`: 60/60 arrivals, none trapped.
- `links`: asphalt ↔ Hub two-way, false wall ↔ Level 4, hole → 94, Level 2 Hub door ↔ service door paired.
- `layouthash`: only Levels 1, 2 and 37 change from my edits (shown by rebuilding with them reverted). The tree's hash also differs in Level 5, from another agent's edit.

**Added in the second pass (2026-10-09):**
- **The Tower** (`BuildHubTower`; blocks worked out from the geometry in `WorldGenerator.Hub.cs`):
  - a rotunda of ashlar (inside radius 20, wall to 24) up to rel 35, with the headless statue in the middle and dusk light over it;
  - ten passages through the wall to the ornate doors;
  - a spiral marble stair (from just past tunnel 1, climbing one block in 1.5 to the meeting hall on rel 30);
  - four galleries (rel 8, 14, 20, 26) with balustrades and ten forbidden ornate doors each;
  - pilasters, and hidden dusk lights;
  - the balcony out of the meeting hall over a black void. Falling into it casts you out into the tunnels, one-way.
  - Render: `hub-tower-render.png`.
- **One visit per player** (`HubTower.cs`): whoever has been inside and is outside again, by any means, is refused at every ornate door. The ornate doors use `BackroomsHubDoor` (swapped in at asset load).
- **The Keymaster:** class `EntityKeymaster` (invulnerable, never saved), set on `hub-keymaster` at asset load.
  - He appears to a visitor carrying a Level Key, or reaching the meeting hall.
  - Right-click cycles the keys of levels you have been to (the visited set is tracked per player); sneak and right-click takes one, once.
  - He then escorts you to the sidewalk before that level's door.
  - Breaking anything in the Tower gets you thrown out with nothing.
- **The M.E.G. outpost** by the Level 11 door: the door register, doorstep carpet, banner and key cabinet. Camp Amber's sign by the Level 1 door.
  - The outpost's wanderer gets two Level Keys at a time in its selling slots, re-rolled weekly, 30–45 rusty gears, only for levels someone in the world has entered (saved as `backrooms-hub-entered`). They are put back if a restock pushes them out, until they are sold.
- **The register:** right-click marks the three open doors, the ten Tower doors and the outpost.
- **Wall-hung pieces** (lamps, stencils, plaques, banner, cabinet) now stand in the air cell in front of their wall, as the asset script builds them.
- **Checked:** `hubstats` 99.90% reachable (the rest is the sealed Tower and the void, as designed), `regions` 60/60, `links` unchanged, headless dump of the Tower rendered.
- **Not tested** (headless has no player): the Keymaster's interaction, the M.E.G.'s stocking and the register's marks.

**Round 2 (2026-10-09): Levels 3999 and 188.**
- **Level 3999:** an ordinary keyed carved door (sigil 19), placed after the others so they did not move. Its key `hub-key-l3999` (a chrome room key on a glowing magenta keychain) was added to `gen_hub_items.py` and regenerated. It drops from Level 3999's caches like the existing levels' keys.
  - The door lands anywhere in 3999 until the 3999 agent names its STAFF ONLY arrival finder; swap it in `ThresholdNetwork.HubDoor`.
  - 3999's STAFF ONLY doors arrive beside a service door with `ThresholdNetwork.HubServiceDoor`.
- **Level 188:** one open window per world (`HubSlotKind.Window`, on a spoke at 300–900 blocks). Two wall tiles carry `Unders.HubWindow188` (`Stack` 0 is the left tile, 1 the right; `Pier` is the facing; rel 2 is the lower half, rel 3 the upper).
  - Public lookup: `WorldLayout.HubWindowOf()`.
  - The generator draws `l188-window-lit-{ll|lr|ul|ur}-{facing}` when those blocks exist, else plain wall.
  - The 188 agent owns the threshold (its block kind, arrival and the way back).
- The level ranges in `HubSystem` (names, keys, the Keymaster's and the M.E.G.'s lists) and `HubStats` now reach ids 19 and 20.
- **Checked:** `hubstats` shows all 20 doors placed, reached and leading to the right level, and the window placed and reached. `regions` 60/60. `links` unchanged. `layouthash` identical with and without these changes.

**Deviations:** lamps are on rel 4, on both walls of main tunnels. The Level 1/2 entrances are a grey door with sigil 0 (not a carved 4-high door: Level 2's rooms are 3 high). No amber chalk (plain chalk arrows). No `hub-curb`, `hub-holelip` or crumb floors.

**Not built yet:**
- the endless stair (deferred);
- the museum pedestals;
- the storm's rain and lightning (the balcony has the black void, and thunder is heard in the Tower now and then);
- Camp Amber's daily wandering;
- shelters, notes and Facelings.

---

## 1. What the lore says

Sources, in order of weight: the Backrooms Wiki on Wikidot (primary canon), then Miraheze and Fandom as second opinions, then depictions. The pages fetched on 2026-10-07 are in that session's scratchpad (`hub-wd.txt`, `hub3.txt`, `hub-log.txt`, `tower.txt`, `key.txt`, `fandom.txt`, `mira.txt`).

> **Note on links.** `backrooms.wikidot.com/the-hub` returns 404. The canon page is on **backrooms-wiki.wikidot.com**. It is an "offset" page with four states:
> - `/the-hub`: the original file;
> - `/offset/1`: Discovery Log 1782;
> - `/offset/2`: "The Tower";
> - `/offset/3`: the updated, merged file.

### 1.1 Canon (Wikidot, "Unnumbered Level - The Hub", by Mctoran and Stretchsterz; originally u/DMKampf and u/FireMatch on Reddit)

URLs:
- https://backrooms-wiki.wikidot.com/the-hub
- https://backrooms-wiki.wikidot.com/the-hub/offset/1
- https://backrooms-wiki.wikidot.com/the-hub/offset/2
- https://backrooms-wiki.wikidot.com/the-hub/offset/3

**Survival difficulty**
- The original file's infobox says **1**; the updated file and the Tower say **2: "Safe. Unsecure."**
- The page tags say `sd-class-0` and `sd-class-2`.
- Every version calls it "a safe place for any wanderer looking to pass by and/or live in".

**What it is**
- "A hidden level which serves as the nexus to the entire Backrooms, containing an entrance to every single level."
- Two parts:
  - **The Crossroads**, the tunnels;
  - **The Tower** at their centre, where the Keymaster lives.
- Ancient groups such as The Lost call the whole place "The Crossroads".

**The Crossroads**
- "A vast subterranean complex, composed of an infinite interconnected network of dimly-lit tunnel systems."
- The road and walls:
  - a **dry asphalt road** "with three sections of yellow dotted lines";
  - walls of **large concrete slabs with seams between each one**;
  - **yellow industrial lights** along the walls, which give "an orange hue".
- The tunnels "twist into many directions" and split into many intersections. The dim light makes the layout "look very strange".
- **Sound:** "completely devoid of sound", apart from the wanderers who live there. This makes unpopulated areas eerie.
- **The canon photo** is Wikimedia Commons "Ventilation.jpg" (Dirif tunnels, CC BY-SA 3.0). It shows a French road tunnel in Île-de-France: concrete walls, orange sodium light, and **jet fans hanging from the ceiling**.

**The doors**
- **Large concrete doors on either side**, "large immovable slabs of concrete", each with **a strange symbol carved above**. The symbols are unrecognisable as language and look like **crop circles**.
- **Unlabelled.** The doors are "not numbered or otherwise labeled", and their order does not follow the levels' numbers.
- **Locks.** Every door has a keyhole. The lock "morphs its shape on the inside" so it cannot be picked; only that level's **Level Key** opens it.
- **Three doors are permanently unlocked:**
  - **Level 1**, in the **7th tunnel**;
  - **Level 11**, in the **10th tunnel**;
  - **Level 178**, in the **5th tunnel**.
- **Keys lead you to their door.** "If you enter The Hub while in possession of a level key, you can follow its resonance towards the respective level door."
- **Doors re-lock.** A door unlocked by hand "always become[s] locked once again for any subsequent entrants".
- **Exits are one-way:** "the doorway from within the entered level will disappear after being crossed — along with the level key that was used for it."

**The Tower** (offset 2, SD 2)
- A tall cylindrical tower in Greco-Roman style, at the centre of the Crossroads.
- **Ten entrances.** You reach it through "ten evenly-spaced entrances", which are ornate doors at the ends of certain tunnels.
- **Light:** no windows. It is lit dimly "by rays of perpetual dusk which radiate from an unknown source".
- **Statue:** a defaced **headless marble statue** stands at its centre.
- **Stair and doors:**
  - a spiral staircase winds up past **rows of ten ornate level doors**;
  - its height shifts: some climb "several hundreds of rows" and find no end, others reach the top in five;
  - the Tower's doors have never been identified with any level or unlocked. The Keymaster says "These thresholds are forbidden to wanderers".
- **Museum rows:** some rows are furnished like a museum, with artifacts on pedestals (in the log, a Scaraback and "a small Squid-like creature in a jar").
- **The top:** a meeting hall with a circle of doors whose number can't be counted: "One, two, three, five… eight!… eight? Wait is it… nine? Twelve!".
- **The outside:** a **balcony** looks out on "a dark void filled with wind, rain and lightning storms". Far below lie all the Crossroads' tunnels. In the log, rain soaks the tower's walls and lightning shakes it.
- **No second visit:** "Upon exiting The Tower, it will be impossible to re-enter afterwards."
- **Origin:** probably built by The Lost as a place of worship.

**Entities**
- **The Keymaster** ("Entity X") is the Hub's overseer and travels to other levels from it.
  - In the log he **descends slowly from above**, "with a faint jingling of his key ring", looms tall over the team, and his **cloak swoops** as he turns.
  - He is antisocial and impatient, and wants intruders gone. In the Tower he always appears to anyone carrying a Level Key.
  - He will **give a Level Key** and **guide you to its door**, so that you leave.
  - He is invulnerable ("that would be useless against me"), and "always know[s] which door leads what level".
  - In the log he shoves the team out through a door "that appeared outta nowhere", next to the Level 11 entrance.
- **Only benign entities.** "All hostile entities that have been seen attempting to enter The Hub are not found within the level, as if having disappeared." The level "may be able to detect the intent of all who enter".

**Groups and outposts**
- **M.E.G. Outpost "Doorstep Carpet":**
  - Regiment Lock Breakers deposit the Level Keys they collect there;
  - any wanderer may ask whether a key is available;
  - keys may be traded there.
- **Camp Amber Hub Outpost:**
  - it helps newcomers, teaches them which level they are about to walk into, and gives limited supplies;
  - it "doesn't really have a fixed point": it wanders.
  - Level 1's page agrees: Camp Amber left Level 1 in 2013 for "the Hub, a safe highway level".
- The M.E.G. log ends with the team "back in the public Hub Route… right next to the Level 11 entrance", heading for M.E.G. Base Beta in Level 11.

**Entrances (canon)**
- **Level 1:** "following a specific sequence of halls and doors" (Hub page; Level 1's page agrees).
- **Level 2:** the same scheme. Its footnote calls it "a trail of corridors that aligns with the 'Konami Code'" (from the third revision of the Hub page).
- **Any level, by noclipping:** hypothetically possible, "given its connection to every level".
- **A random level:** "a door to The Hub temporarily manifests" there, as a rare phenomenon.
- **Level 213:** exiting it can lead to Level 11 or the Hub (Level 11's page).

**Exits (canon)**
- Every level door, one way, with its key used up.
- **Level 4:** "No-Clip into a wall in The Hub" (Level 4's page).
- **Level 94:** "a rectangular-shaped hole will appear on the ground in a random area of The Hub", and you fall onto the hills and land gently (Level 94's page).

**Level Keys (Object 2)**
- https://backrooms-wiki.wikidot.com/object-2
- **What they look like.** Each key is tied to one level, and its design usually shows where it comes from. They are 3 to 20 cm long, usually metal (sometimes plastic or stone), and some are not keys at all (a key card, a USB stick).
- **Where they are found.** Found **only in the level they belong to**, extremely rarely, often in dangerous places.
- **Remote access.** Turned **clockwise three full rotations** in any lock, a key opens a door to its level from anywhere. There is no apparent limit to uses. This contradicts the Hub page, where the key is used up.
- **Harmonic resonance.** Struck, a key rings at **exactly 500 Hz** in its own level, plus about 20 Hz for every level away. Mappers use tuning forks.
- **Pseudo-magnetism.** A key pulls toward its level. A "key compass" floats a key on cork in salted water.
- **Damage.** Melting or damaging a key kills it; counterfeits are common.
- **Trade.**
  - The Stanley Key Exchange (Level 11, and Trader's Keep in Level 1) grades keys: Priority 2000, High 1500, Low 800, Unknown 700 and Null 400 Almond Waters.
  - Keys can also lock or unlock their level's door in the Hub.

### 1.2 Second opinions and contradictions

| | Wikidot (canon) | Fandom ([api](https://backrooms.fandom.com/api.php?action=parse&page=The_Hub&format=json&prop=wikitext), by Jamie/Accountus) | Miraheze ([api](https://backrooms.miraheze.org/w/api.php?action=parse&page=The_Hub&format=json&prop=wikitext)) |
|---|---|---|---|
| Class | 1 / 2 ("Safe, Unsecure") | custom "hubclass" | Habitable, Class 0 |
| Tunnels | concrete slabs, asphalt road, three yellow dotted lines, orange industrial lights | **brick** tunnels, sidewalks, concrete slabs; lights that sometimes turn red, purple or green; ceiling pipes of Almond Water and Liquid Pain; **neon traffic signs**, **TV screens** of news in changing languages | tunnels of doors |
| Doors | concrete, unnumbered, a crop-circle sigil, one level each | **steel**, **marked with the level's number or name**, tinted to match (Level 0 yellowish, Level 37 tiled); "hundreds of miles apart"; positions shift | each door "reflects the appearance" of its level; runic symbols; **the key bears the same symbol as its door** |
| Open doors | 1, 11, 178 | none | 1, 11, **154** |
| Air | silent | "a silent hum… changing in pitch every few minutes"; **−3.8 °C**, a vast grid of ventilation fans; antiseptically clean (filth sinks into the floor) | — |
| Entities | Keymaster, benign only | Skin-Stealers, Hounds, Deathmoths (rare), no Smilers | Keymaster as guardian |
| Tower | ten doors in, a headless statue, the Keymaster, no second visit | — | the statue is *of* the Keymaster, and wanderers leave offerings |
| Entrances | Level 1 sequence, Level 2, noclip, a door that appears | Level 1 corridors and stairwells; sections of **Level 37** and Level 154 that look like the Hub | Level 1; noclip; a door that appears; Level 92's note |
| Exits | one-way doors; Level 4 wall; Level 94 hole | doors (key); tunnels that fade into **Level 37** or 154; the Unconscious Hub in dreams | one-way doors |

**Resolved:**
- Wikidot is followed everywhere it speaks.
- From Fandom only the parts that fit Wikidot's tunnels:
  - the cold;
  - overhead lane signals (its "neon signs to indicate the flow of traffic"), which fit the road-tunnel photo;
  - the link with Level 37.
- From Miraheze: the key bears its door's sigil.
- The TVs, the coloured lights, the pipes, the self-cleaning floor and Fandom's hostile entities are left out (decision 7.15).

### 1.3 Depictions

- **Wikidot's images.**
  - The Crossroads photo is the Île-de-France road tunnel with jet fans described in §1.1.
  - The Tower image is a composite of the Roman arches of the El Jem colosseum (Serge Lévesque, CC BY-SA 2.0) and a headless antique sculpture (Pixabay).
- **Fandom's images** come from r/LiminalSpace: wide, orange-lit road tunnels.
- **Escape the Backrooms** (Fancy Games) has "The Hub": an underground tunnel lined with numbered doors that serves as its level select (playnews.gg guide, 2026). This is the best-known game depiction, and the "numbered doors" are Fandom's idea, not canon's.
- **Kane Parsons' films** have no Hub.

---

## 2. The level in this mod

### 2.1 The experience

You come through a door that should not be in Level 1, and it closes behind you on silence.

- **The tunnel:** a road tunnel, twelve blocks wide, lit orange by caged lamps on the walls, an asphalt road with three lines of yellow road studs, and jet fans hanging dead from the ceiling.
- **The doors:** down both walls, every twenty-odd blocks, huge concrete doors, each with a different carved crop circle over it. None of them has a number, and none of them opens.
- **The landmarks:** a stencilled **7** on the wall; further on, M.E.G. tape, a doormat, a radio playing nothing.
- **The rules:** nothing here will hurt you, but there is nothing to eat, and it is cold.
- **Getting out:** the way back is the plain grey door you came in by. The way on is any door you have the key for.

Design goals, in order:

1. **The crossroads of the network, not a shortcut through the survival loop.**
   - Getting in is rare.
   - Every carved door is one-way.
   - Most doors need a key that comes only from the level it opens, so the Hub mostly takes you back to places you have already reached the hard way.
2. **Unmistakable from the first screenshot:** an orange road tunnel, carved concrete doors, silence.
3. **A place with people and rules:** the M.E.G. and Camp Amber, the Tower and the Keymaster.

### 2.2 Region

- **Like the other new levels, a noclip region** (`IsNoclipRegion`: id 17 ≥ 11, so no gates and no ring wall pairs with it).
- **Where:** south-east of spawn, at the distance CONTRACT.md gives (the 37/94 pattern is `max(800, spawnMacro/4)` cells out).
- **Size:** unlike 37 and 94, **a fixed radius of 60 cells (1,920 blocks)**, because the Hub is planned round one centre: the Tower.
  - "Infinite" is faked with the shape (the tunnels twist and loop and nothing ends).
  - Its outer half is unlit and unmapped (the M.E.G. notice: "larger than originally believed… remain within the known area").
- **Floor:** `HubDrop = 28` below the shared floor (`FloorFor(Hub) = FloorY − 28`).
  - Tunnels rise 8 blocks; the Tower up to 36.
  - The default lit band (FloorY − 30 to CapY − 1) already covers floor − 2 to floor + 37, so `BandBottomFor(Hub)` stays the default.
  - Above the tunnels is solid concrete to the cap.
- **Rim:** solid concrete beyond the outermost ring road. Every spoke ends *on* that ring, so no tunnel visibly ends at the edge.

### 2.3 Layout: ten numbered tunnels round the Tower

Canon numbers its tunnels (Level 1 is "in the 7th tunnel") and gives the Tower "ten evenly-spaced entrances into different points of The Hub's tunnel system". So the Hub is a **hub and spoke**: ten tunnels leave the Tower, the Crossroads lie round them, and side tunnels twist between.

**Everything is axis-aligned.** Doors are 3 blocks wide and must sit in a straight wall, and a diagonal wall in voxels is a staircase. So every tunnel is a chain of straight **axis-aligned segments** (24–96 blocks) joined by **45°-chamfered corners**. This is also canon's "twist into many directions": the tunnels turn every few dozen blocks, which keeps sightlines to 30–90 blocks in orange haze.

The plan is a small **road graph built once per world** from the seed (about 3,300 segments in all, a few milliseconds), binned by 256-block squares and rasterised per cell. It is a pure function of the seed (like `PlanCache` plans; cache the graph on the layout).

| Element | Geometry | Interior |
|---|---|---|
| **The Tower** | centre; rasterised circle, radius 16 | §2.6 |
| **The Approaches** | the inner end of each spoke: a 9×9 vestibule against the Tower, the ornate door in its axis-aligned wall | 9 wide, 8 high, marble floor |
| **The Roundabout** | a rectilinear loop at r ≈ 60 round the Tower | main tunnel; the M.E.G. outpost opens off it |
| **Spokes = Tunnels 1–10** | from the Approach (r ≈ 25) to the rim ring (r ≈ 1,850), at angle θ0 + 36°·(k−1), numbered clockwise (θ0 per world). Each is a staircase of segments whose x- and z-runs follow cos/sin of its angle, with jittered lengths, so it wanders ±10 blocks off its ray | main tunnel |
| **Ring roads** | rectilinear loops at r ≈ 330, 700, 1,100, 1,500 and 1,850 (the rim), each jittered | main tunnel (rings 1–3), side tunnel (rings 4–5) |
| **Side tunnels** | a jittered 96-block lattice from r 120 to the rim. Each lattice edge is present with p = 0.55, drawn as an L (x-run, chamfered corner, z-run) between jittered nodes. A missing edge leaves a **dead end**, which always ends at a door | side tunnel |
| **Junctions** | wherever segments meet, cross or pass within 2 blocks, the union of the tunnels: wide irregular crossings (Fandom: "wider passageways") | |

**Zones** (`Tile.Zone`):
- **0** the Crossroads (r < 1,100, the "known area");
- **1** the Far Tunnels (r ≥ 1,100);
- **2** the Tower;
- **3** an outpost.

**Cross-sections** (from one wall to the other):

| | Main tunnel (spokes, Roundabout, rings 1–3) | Side tunnel |
|---|---|---|
| Width inside | 14: sidewalk 1, road 12, sidewalk 1 | 7: sidewalk 1, road 5, sidewalk 1 |
| Height | 8 (air rel 0–7), flat ceiling | 6 |
| Road | asphalt; **three dotted lines** of yellow road studs at −3, 0, +3 from the centre (four lanes), a stud every 2 blocks | asphalt, one dotted centre line |
| Sidewalk | half-height slab of pale concrete with a kerb; this is where people are put down | the same |
| Walls | concrete slab panels 2 wide × 3 high with seams | the same |
| Lights | a caged amber wall lamp every 8 blocks at rel 5, alternating sides | every 10 blocks at rel 4, one side |
| Overhead | a pair of **jet fans** every 48 blocks at rel 6–7; a **lane-signal** gantry (green ↓ over the lanes) every 96 blocks | none |
| Doors | a slot every 24 blocks along each wall (staggered between the two walls), skipping 6 blocks either side of corners and junctions | a slot every 16 blocks; every dead end ends in a door |

**Stencils.** The M.E.G. painted the tunnel's number on its walls: a white stencilled numeral at every junction a spoke meets, and every 64 blocks along it. Where a ring meets spoke k, the corners carry k. A stencilled arrow and "TOWER" point inward on spokes inside ring 1. This is the canon convention ("the 7th tunnel"), and the only labels in the Hub. The doors themselves stay unlabelled.

**The Far Tunnels (r ≥ 1,100).**
- **Lights die off:** from 1,100 to 1,850 the share of dead lamps rises from 20% to 75%.
- **No stencils.**
- **Colder** (§2.8).
- **What is out there:** the noclip walls, the hole and the tiled tunnels (§3.2). They are the rare exits that do not need a key, and finding them means going where the light runs out.

### 2.4 The doors

Every door slot holds one of these:

| Door | Block | Count | What it does |
|---|---|---|---|
| **Level door, open** | `hub-door-*` + `hub-sigil-<n>` | 3: Level 1 (Tunnel 7), Level 11 (Tunnel 10), "178" → Level 6.1 (Tunnel 5) | Opens for anyone; **one-way** to its level |
| **Level door, keyed** | the same | 17: Levels 0, 2–10, 37, 94, !, Fun, End, 974, 3999 | Locked. Holding that level's key, use the door: three turns of the key, the slab grinds aside, the key is gone, you are through, **one-way**. Without the key: "locked" |
| **Dead door** | the same, with one of 24 dead sigils | all other slots, about 2,000 | Locked forever ("Its key is somewhere else in the Backrooms"): the doors to the thousand levels the mod lacks |
| **Service door** | `hub-servicedoor` (plain grey steel, 1×2) | about 1 slot in 4 between r 150 and 1,100 | The way back. Locked unless someone came into the Hub beside it (existing `locked` kind) |
| **Ornate Tower door** | `hub-ornatedoor` | 10, at the Approaches | §2.6 |

**Live doors.**
- **One door per level, in the whole world**, always on a spoke between 120 and 900 blocks out from the Tower.
- **Tunnels:** canon's three are fixed (1 → Tunnel 7, 11 → Tunnel 10, 178 → Tunnel 5); the rest are picked by hash. At most 3 live doors per tunnel, and none within 40 blocks of another.
- **Lookup:** placement is a 20-entry table built once per world (`HubDoorSlots`), so the layout answers both `HubDoorAt(x, z) → level or −1` and `HubDoorOf(level) → position`.
- **Open doors:** the M.E.G. tagged them. A small stencil plaque beside each reads "LVL 1", "LVL 11", "178". Every other live door is as unlabelled as the dead ones.

**Sigils.**
- **What they look like:** crop-circle reliefs carved in a 3-wide panel over each door (only the middle block bears the sigil; the side blocks are carved border).
- **Fixed per level, the same in every world,** so the key in your hand bears the same sigil as its door (Miraheze), and the handbook can show them.
  - Ids 1–19 are the live doors (one per level, plus "178"); 0 is the Hub's own sigil; 20–43 are dead ones.
  - The table is in §4.3.

**Where the doors lead (rule 1).** Each live door's arrival is found on first use with `FindArrival(level, key)` and saved, like any threshold.
- **Level 6.1** uses `InSnackrooms`.
- **Level 94** gets its sky drop and soft landing (`Arrive` already does it).
- **The new levels** use their own arrival finders.
- **No way back.** Canon: the doorway disappears behind you. The arrival message says the door has gone, and no thin spot is left.

### 2.5 Level Keys

Each key is a new item, `hub-key-<tag>`, for 17 levels: 0, 2–10, 37, 94, run, fun, end, 974, 3999. Levels 1, 11 and 6.1 have open doors, so their keys are not made.

- **Origin in the look.** Each key shows its level and bears its sigil on the bow (§4.6).
- **Stack size 1.** A key does nothing anywhere but the Hub (decision 7.8).
- **Found only in its own level, rarely, where it is dangerous to look** (Object 2). A sealed container broken open in level L may hold L's key:

| Where | Chance per container |
|---|---|
| A den's cache (`WorldLayout.Dens`) | 4% |
| Behind a door forced with the pry bar (locked rooms) | 1.5% |
| Elsewhere, sealed boxes and crates | 0.2% |
| Special places: Level 0's Red Rooms; Level 7's island camps; the drowned of Level 37.1; Level 94's castle; Level 3's boiler rooms and Sanctums; Level 8's 9th Road camps | 8% |

  - It works through the `Rewards` bonus pass, as a hook keyed by level: the same moment that "fuller deep caches" already uses.
  - New levels name their own special places.
- **The M.E.G. outpost sells keys.**
  - It offers two keys at a time, re-rolled weekly, for **30–45 rusty gears** each. That is Stanley's "Priority" price in the wanderers' currency, and as much as a long expedition's bounties.
  - It never offers keys for 1, 11 or 6.1, nor for a level no player in the world has entered (tracked by the visited set below).
- **The Keymaster gives one** (§2.6).
- **Resonance (canon).** In the Hub, a key held in the active slot rings every 4 seconds: a bell-like 500 Hz chime (`hub-keychime`).
  - It is played as a positional sound 6 blocks from the player, **toward that key's door**, so the ear finds the way. There is no HUD and no compass.
  - It gets louder as you close in (volume 0.3–1.0 over 1,500 blocks).
  - Within 8 blocks it rings from the door itself, twice as often. The first time that happens, the door is marked on the map: "The door of Level 5".
- **Using a door with its key:**
  - three ratchet clicks (`hub-keyturn`: canon's three clockwise turns), then the slab grinding (`hub-doorgrind`), then the trip;
  - the key is consumed, and the door is locked again for everyone (canon).
  - The way is marked as a one-way waypoint (the existing `Remember`).

### 2.6 The Tower and the Keymaster

**The building.**
- **Footprint:** a cylinder of pale ashlar, radius 16 (inside radius 13), up to rel 36.
- **Ground floor:** a rotunda on a polished marble floor with an inlaid circle.
  - At its centre stands the **headless statue** on a plinth (3 blocks tall).
  - Ten arched passages run out to the ten ornate doors at the Approaches.
- **Light:** "perpetual dusk" from hidden `hub-dusklight` blocks behind the top cornice (rose-amber), and nothing else.
- **The stair:** a spiral of marble steps up the inside wall.
  - It climbs past **four rows of ten ornate doors** (rel 8, 14, 20, 26), each on a narrow gallery with a balustrade.
  - All are forbidden: "These thresholds are forbidden to wanderers."
- **Museum rows:** one or two rows (by hash) carry pedestals with artifacts under glass: a Scaraback, the squid thing in a jar (canon), and mod nods (a pool noodle, a stop-motion clay figure, an old radio, a crown shard, a level key, an M.E.G. badge).
  - They are decor only. Breaking one brings the Keymaster, who throws you out (below).
- **The meeting hall at the top** (rel 30–36): a ring of ornate doors and a round table.
  - **The balcony:** an arched opening onto the **storm void**, a black space where rain falls, wind blows and lightning flashes.
  - The view down to the tunnels is not built (decision 7.13).

**Rules.**
- **Getting in.** An ornate door opens (kind `towerdoor`) and you walk the passage to the rotunda.
- **Getting out.** Walking out through any passage flags you (`backrooms:towerVisited`) and leaves you outside that door.
  - **One visit per player:** from then on every ornate door refuses you ("It does not know you any more"). Canon: no re-entry.
  - Others can still come in.
- **The Keymaster** appears to every player on their one visit:
  - at once, if they carry a key;
  - otherwise when they reach the meeting hall.
- **How he appears:** he descends from above with a jingle of keys (`hub-keyjingle`), and speaks in chat in canon's voice: impatient, and wanting you gone.
- **What he gives.** Right-click him and he gives **one Level Key, of a level you have been to**, chosen from a short list (a simple dialog). The visited set is a player attribute `backrooms:visited`, a bitmask set when `AtmosphereSystem` announces a level.
- **Escort.** Then he escorts you: one-way, you are put on the sidewalk in front of that key's door, and the Tower is closed to you. Canon: he shows you the door, then shoves you out.
- **If you break anything in the Tower,** he appears and throws you out at once, with no gift.
- **What he is:** invulnerable and harmless. Not an AI entity, but a scripted presence spawned and removed by `HubSystem`.

### 2.7 Outposts and people

- **M.E.G. Outpost "Doorstep Carpet".** It stands in **Tunnel 10**, a few dozen blocks from the Level 11 door. Canon puts the M.E.G.'s "public Hub Route" by the Level 11 entrance, and its Base Beta in Level 11.
  - **The setting:** a lit alcove off the sidewalk, 12 × 8. A **doorstep carpet** (a worn doormat) lies in front of a service door, which is their way in.
  - **Furniture:** folding tables, cots, an M.E.G. banner, a field radio, a locked **key cabinet** (decor), and a whiteboard, the **door register**.
  - **The register:** right-click it to read it. It marks on your map the three open doors (with their tunnels), the ten Tower entrances, and the outpost. Optionally it also reveals the known area (decision 7.17).
  - **A wanderer trader:** existing wanderer, M.E.G. trade list. Sells Level Keys (§2.5), wanderer's notes and a little Almond Water; buys salvage.
- **Camp Amber Hub Outpost.** Canon: it "doesn't really have a fixed point".
  - **Where:** three camp sites on Tunnels 6–8 within r 500. Each in-game day (hash of the day) the camp's wanderer keeps to one of them; the other two stand empty, embers cold.
  - **A camp:** tents, bedrolls, a lit firepit (rest, warmth), a painted board ("CAMP AMBER: NEW? ASK US"), and **one sealed supply box that refills weekly** ("limited supplies").
  - **Amber chalk arrows** on the walls within 3 cells point to the camp. Amber arrows also mark the way to the Hub door in Level 1 (§3.1).
- **Shelters.** About one per 2 km of tunnel inside ring 3: a tarp and a bedroll on the sidewalk, sometimes a backpack. Wanderer's notes found there point to Hub features: an open door, the noclip wall, the hole, a tiled tunnel, the camp.
- **Benign things.** Now and then a Faceling walks the far sidewalk and turns its blank face to follow you (Safe-band ambient, rare). Nothing hostile is ever put down in the Hub.

### 2.8 Light, sound, air, stability

| | Crossroads | Far Tunnels | Tower |
|---|---|---|---|
| Light | caged sodium lamps, `lightHsv [5, 6, 11]` (amber, dim); a lane signal's faint green 4 | 20% → 75% of lamps dead with distance; long black stretches | dusk light `[2, 4, 13]` from above, nothing at floor level |
| Fog | density 0.010, colour (0.32, 0.21, 0.09): orange haze | 0.016, (0.14, 0.09, 0.05) | 0.006, (0.42, 0.31, 0.28): dusky rose |
| Sound | **silence**: no hum, no drips. Only, very faint, a low drone (`hub-silence`, 0.04 amplitude) whose pitch steps every few minutes (Fandom) | the same, fainter | wind outside (`hub-wind`), distant thunder through the walls every 1–3 minutes (`hub-thunder`), the jingle when the Keymaster is near |
| Temperature | **6 °C**: the jet fans are still, yet the air moves cold (Fandom's cold, short of its freezing; decision 7.7) | 2 °C | 14 °C |
| Reality Stability | **1.3**: a nexus; the level that "detects intent" | 1.0 + 0.1·drift | 1.2 |
| Menace | **Safe** everywhere (`IsSanctuary`): nothing hostile, and the Safe band already counts as rest, so the exposure clock resets here | Safe | Safe |

- **Lights fail like any lamp** (`FlickerSystem`), only rarely.
- **Reality Shifts** reach the Hub as everywhere else: the lamps die for a few hours and stability drains. Being Safe, nothing comes. It is just very dark.

### 2.9 Vanilla mechanics and loot

- **No food, no water.** The Hub is clean: there are no supply boxes in the tunnels. The only food is the camp's weekly box and what the traders sell.
  - **Cold:** 6 °C wants clothes on a long walk, and the camp's firepit is the warm place.
  - Together these are the Hub's price. It is safe, but you cannot stay.
- **Salvage** follows the usual rules (`Breakdown.cs`):

| What | Tool | Drops |
|---|---|---|
| Concrete wall panels, sidewalks, asphalt, ashlar, marble | copper pickaxe | rubble |
| Jet fans (machinery) | copper pickaxe | brackets, scrap wire, now and then a copper bit (the motor) |
| Lamps | any | glass, a bracket, wire |
| Lane signals | any | glass, wire |
| Doormat | any | carpet fibres |

- **Never broken** (`Protection.cs` Fixed, landmarks): every door (level, service, ornate), the sigil panels, the statue and the stencils. The roof is protected as on every level.
- **No anchor.** A temporal gear refuses here, as anywhere outside Level 0 (decision 7.6).

---

## 3. Ways in and out

All new links follow the two rules:
- **Fixed:** every threshold always leads to the same place, saved in `ThresholdNetwork`.
- **Walked = two-way; fell, dived or taken = one-way.**

The Hub's carved doors are one-way although you walk through them. Canon is explicit that "the doorway… will disappear after being crossed". The mod has a precedent: the Snackrooms' doors "shut behind you" and are one-way. See decision 7.2.

### 3.1 Into the Hub

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| **Level 1** | In Level 1's corridor sectors (`IsLevel1Corridors`), about 1 cell in 120 (roughly 8–12 per world): a **Hub door**, the same carved concrete door with the Hub's own sigil (id 0), at the dead end of a winding maintenance hall. **Amber chalk arrows** (Camp Amber's) within 3 cells point to it. Kind `hubdoor`; `HubSystem` routes it by level | The Hub, on a sidewalk beside a **service door** | That service door (two-way pair) | Wikidot: "a specific sequence of halls and doors in Level 1"; Camp Amber came from Level 1 |
| **Level 2** | One in 40 of Level 2's steel tunnel doors that would be locked is instead a Hub door (own salt) | The Hub, beside a service door | That service door | Wikidot Level 2: the same scheme (the "Konami" trail) |
| **Level 37** | One dry corridor in four (own salt) ends not in office carpet but where the white tile gives way to **concrete slabs and asphalt** (`Unders.PoolAsphalt`), walked into | The Hub: beside a tiled tunnel end where one is near, else on a sidewalk | The tiled tunnel end it arrives beside, else a thin spot | Fandom: Level 37 has sections that resemble the Hub and lead there |
| **Any level** (0–10, 6.1, 37, 94, the new levels; never the Hub) | **A door that wasn't there.** Rarely, a Hub door appears in a straight wall 10–24 blocks from a player, out of their sight. The odds are tuned so a player meets one about every 10 in-game days, never in a Safe band, never within 48 blocks of home. It stays 5 real minutes, then is gone (the blocks it replaced are put back) | The Hub, anywhere in the Crossroads | **None** (it is gone when you turn round) | Wikidot: "a door to The Hub temporarily manifests in a random level" |

The temporary door is runtime-placed (like thin spots), not part of the layout. Its link is saved under its position like any threshold, which does no harm once the door is gone.

### 3.2 Out of the Hub

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| Tunnel 7 | The open **Level 1** door | Level 1 | None | Wikidot (door 1, tunnel 7) |
| Tunnel 10 | The open **Level 11** door | Level 11, on a sidewalk | None | Wikidot (door 11, tunnel 10) |
| Tunnel 5 | The open door canon gives to **Level 178** (a safe, entity-free house with food, where people rest and restock) | **Level 6.1**, the Snackrooms, in a food court | None (the Snackrooms' doors are one-way out) | Wikidot (door 178, tunnel 5), redirected (decision 7.4) |
| A spoke | A keyed door, with its key: **Levels 0, 2–10, 37, 94, !, Fun, End, 974, 3999** | That level | None; the key is used up | Wikidot |
| A service door | The door you came in by | Where you came from (the Level 1 or Level 2 Hub door) | It is the way back | the network's pairing |
| Far Tunnels | A 3-wide **stretch of wall that isn't there** (`hub-falsewall`, seams that don't line up), walked into. 6 per world, on 6 different spokes, r 700–1,300 | **Level 4** | Thin spot | Wikidot Level 4: "No-Clip into a wall in The Hub" |
| Far Tunnels | A **rectangular hole** in the road (2 × 4, `TileKind.Pit`), falling in. 4 per world, in side tunnels, r 600–1,500, with M.E.G. chalk crosses on the walls | **Level 94**: out of the sky, landing softly | None | Wikidot Level 94: "a rectangular-shaped hole… on the ground… of The Hub" |
| Far Tunnels | A side tunnel's dead end where the concrete turns to **white tile** (`Unders.HubTileEnd`), walked into. 5 per world, r 700–1,600 | **Level 37**: beside an asphalt corridor end where one is near, else in the shallows | That corridor end, else a thin spot | Fandom: tunnels resembling 37 lead there |
| The Tower | The Keymaster's escort | The sidewalk before the door of the key he gave | None | Wikidot log |

**Not linked** (decision 7.9):
- No entrance from Level 11. Canon has none, and Level 11 is already the mod's other hub.
- Nothing from Levels 213, 601, 92 or 154, which the mod lacks.
- No generic noclip from anywhere: the temporary door stands in for it.

### 3.3 What this does to the network

| Can a player… | Without keys | With keys |
|---|---|---|
| reach the Hub early? | only by finding a Level 1 or Level 2 Hub door (rare, in Level 1's outer corridor sectors), by luck (the temporary door), or from Level 37 | the same: keys don't get you in |
| go from the Hub to… | Level 1, Level 11, the Snackrooms (open doors); Level 4, 94, 37 (the Far Tunnels) | any level they hold the key for: one-way, one key per trip |
| come back to the Hub? | only through a two-way Hub door they have found, or by luck | the same |

- **Level 1 ↔ Hub → Level 11** is the big shortcut: it takes you from the second ring to the city. It is canon (the M.E.G.'s route) and is paid for:
  - the Level 1 door is rare and must be found;
  - Tunnel 7 to Tunnel 10 is a few hundred blocks of cold walking with no food;
  - the Level 11 door is one-way, and nothing in the city leads back.
- **Keys are earned.** A key needs a trip to its level, deep and dangerous, or 30–45 gears. So the Hub mostly *returns* you to places you have already earned. That is the user's principle: "the entrance/exit network is the game".
- **A key back to Level 0** (found in Level 0's Red Rooms and stashes) turns the Hub into a way home. This is fine: home is where the loop wants you.

---

## 4. Asset manifest

Built by **`tools/gen_hub.py`**: textures in `textures/block/hub/`, shapes in `shapes/block/hub/`, blocktypes in `blocktypes/hub/`, items in `itemtypes/hub/`, sounds in `sounds/ambient/hub/` and `sounds/effect/hub/`. All textures are 32×32 (`texlib`), with fine noise and no painted 3D detail. Shapes come from `tools/gen_shapes.py` helpers. Every orientable block uses `horizontalorientation`-style variants {north, east, south, west}.

### 4.1 Tunnel blocks

| Code | Variants | Texture | Shape | Notes |
|---|---|---|---|---|
| `hub-wall-{seam}` | seam: plain, left, bottom, corner | Concrete (mid grey #8E8B84, cool, faint formwork grain). Seams 1 px dark (#5E5C57) with a 1 px highlight, on the left edge, the bottom edge, or both | cube | Panels 2 wide × 3 high: the generator picks `left` where (along-wall index mod 2 = 0), `bottom` where rel mod 3 = 0. Breaks to rubble |
| `hub-ceiling` | — | Darker concrete (#77746E), formwork board lines | cube | |
| `hub-asphalt-{state}` | plain, worn, patch | Dark asphalt (#2E2D2C) with light aggregate specks; `worn`: lighter tyre polish; `patch`: a darker tar rectangle | cube | Road surface |
| `hub-asphalt-stud` | — | asphalt top | cube + **road stud**: a 6×6 px dome, 2 px high, yellow ceramic (#E8B92A) with a 1 px reflector face | Botts' dot: "yellow dotted lines" in real 3D, any direction |
| `hub-sidewalk` | — | Pale concrete (#B5B0A6), a 1 px dark joint every block | half slab (8 px), top-flush kerb face on the road side | Arrivals stand here |
| `hub-curb-{facing}` | 4 | sidewalk + kerb face | half slab with a 2 px rounded kerb lip toward the road | Where the generator can tell the road side |
| `hub-lamp-{state}-{facing}` | state: on, dead; 4 | Amber glass (#FFB347, emissive when on), dark green-grey housing (#3D4A3F), steel cage wires | 10×6×7 px box on a 2 px wall plate, 4 cage bars over the glass | `lightHsv [5, 6, 11]` when on. Breaks like other lights |
| `hub-jetfan-{axis}` | ns, we | Galvanised steel (#A7ACAE), black intake mesh, two hanger brackets | an octagonal cylinder 18 px across, 44 px long (it overhangs its block along its axis), with intake rings and a mesh disc at each end, and two straps to the ceiling | Hung in pairs side by side at rel 6–7. Static and silent (Wikidot's silence). Salvage: brackets, wire, copper bit 20% |
| `hub-lanesignal-{sign}-{facing}` | sign: go, stop; 4 | Black housing; face a green ↓ arrow or a red X of 3 px lines, emissive | 12×12×6 px box on a 4 px hanger rod | `lightHsv` go `[22, 7, 4]`, stop `[0, 7, 4]`. Over each lane, every 96 blocks. "stop" only over lanes of a dead end |
| `hub-stencil-{n}-{facing}` | n: 1–10, tower; 4 | White spray-stencil numeral (stencil gaps), 12 px tall, slight overspray; `tower`: an arrow and "TOWER" | 1 px thin plate, 16×16, on the wall face | M.E.G. tunnel numbers |
| `hub-plaque-{lvl}-{facing}` | lvl: 1, 11, 178; 4 | Stencilled "LVL 1", "LVL 11", "178" in white on a grey M.E.G. plate with 4 rivets | 12×6×1 px plate, 4 raised rivets | Beside the three open doors |
| `hub-falsewall` | — | Like `hub-wall-plain`, but its seams are offset 3 px, so they don't meet the next panel's | cube, **no collision**, `lightAbsorption 99` | The noclip wall to Level 4 (barn noclip precedent) |
| `hub-tilecrumb-{stage}` | 1, 2 | Concrete with white pool tiles beginning (stage 1: scattered tiles, 2: mostly tile with concrete gaps) | cube | Leads into Level 37's own `pooltile` at the tiled tunnel ends |
| `hub-holelip-{facing}` | 4 | asphalt, with a broken black edge | cube minus a 2 px chamfered lip on the hole side | The rim of the hole to Level 94; the shaft below is black `hub-void` |

### 4.2 Doors

| Code | Variants | Texture | Shape | Behaviour |
|---|---|---|---|---|
| `hub-door-{col}-{row}-{facing}` | col: l, c, r; row: 1–4; 4 facings | Smooth cast concrete, slightly warmer than the walls (#9A958C), a darker damp stain at the bottom; **brass escutcheon** (#B08D57) | The leaf recessed 2 px inside a 3 px frame (frame on the outer edges of l/r and on row 4's top). Row 1 has a 0.5 block stone sill (it meets the half-slab sidewalk). Part c-2 carries a raised **escutcheon** plate 4×7 px with a keyhole slot and a ring of 6 tiny rivets | `BackroomsThreshold` kind `hubdoor`. Fixed. `blockmaterial Stone`, resistance high |
| `hub-sigil-{n}-{facing}` | n: 0–43; 4 | Carved concrete; recesses darker, the disc's floor darkest | A block whose wall face is cut 3 px deep in a 28 px disc (a 1.5 px step round its rim), with the sigil standing in **2.5 px relief** inside it: rings as voxel arcs, circles as discs, lines as 1 px ridges (2 px deep and 1 px relief until the visual review of 2026-10: too faint under the orange haze) | Above part c-4 (row 5). Decor, Fixed |
| `hub-sigilside-{side}-{facing}` | l, r; 4 | carved concrete | A carved border: a 2 px groove frame, and a half-circle flourish toward the middle | Above l-4 and r-4 |
| `hub-servicedoor-{part}-{facing}` | lower, upper; 4 | Grey-painted steel (#7F8589), chipped edges, push bar, a small wire-glass window in upper | A recessed leaf 1 px inside a 2 px frame; a 3D push bar on lower; the window in upper | kind `locked` (existing): opens only when linked |
| `hub-ornatedoor-{use}-{part}-{facing}` | use: entrance, forbidden; part: l1, l2, l3, r1, r2, r3 (2 wide × 3 high); 4 | Dark oiled oak (#4A3426) with **bronze** studs and bands (#8C6A3A), carved panels | Raised and fielded panels (2 px), bronze bands across, a ring pull on l2/r2, a carved lunette on l3/r3 | entrance: kind `towerdoor`; forbidden: kind `locked`, never linked |

### 4.3 Sigil table (fixed in every world)

Each sigil is a crop-circle composition made from a small vocabulary: a central disc (D), concentric rings (R), satellite circles (S) on a ring, arcs (A), straight ridges (L) and dot spirals (P). `gen_hub.py` draws them from these parameters into a 28 px disc. Dead sigils 20–43 are random compositions from a fixed seed, never repeating a live one.

| Id | Door | Composition |
|---|---|---|
| 0 | the Hub's own (entrances) | D + 1 R, 10 S on the ring (the ten tunnels) |
| 1 | Level 0 | D + 1 R |
| 2 | Level 1 | D + 2 R, 4 S in a square |
| 3 | Level 2 | 2 parallel L, 3 small S along them |
| 4 | Level 3 | D, 3 A as a broken ring, 1 L through |
| 5 | Level 4 | 3 R (no disc), a 2×2 grid of S inside |
| 6 | Level 5 | D + 1 R, 8 S, every other one larger |
| 7 | Level 6 | 1 thin R only, empty middle |
| 8 | Level 7 | 3 concentric A opening downward (waves) |
| 9 | Level 8 | P spiral of 9 dots |
| 10 | Level 9 | small D, 5 S in a row below (houses along a street) |
| 11 | Level 10 | 4 S in a 2×2 field, 1 L between |
| 12 | Level 11 | D + 3 R, 4 L as a cross |
| 13 | Level 37 | 2 R, 6 S *inside* the outer ring |
| 14 | Level 94 | 3 S of decreasing size on an A (hills) |
| 15 | Level ! | 1 long L with 1 D at its end |
| 16 | Level Fun | 3 S clustered (balloons), 3 short L hanging |
| 17 | The End | D + 1 R, a single L cutting the ring |
| 18 | Level 974 | 2 S side by side, 1 A beneath (a face) |
| 19 | Level 3999 | 4 R, nothing else |
| — | "178" (→ 6.1) | uses id 20, the first "dead" design, because its key does not exist |

(The level owners may swap a composition for their own if their lore suggests one; ids must stay.)

### 4.4 Tower and outpost blocks

| Code | Variants | Texture | Shape | Notes |
|---|---|---|---|---|
| `hub-ashlar-{state}` | plain, worn | Pale limestone-marble ashlar (#D9D2C3), 2 courses per block, 1 px joints | cube | Tower walls |
| `hub-pilaster-{part}-{facing}` | base, shaft, capital; 4 | ashlar, fluted | A half-column standing 5 px proud of the wall: a torus base, 5 flutes, a Doric echinus capital | Every 36° round the rotunda |
| `hub-arch-{part}-{facing}` | left, key, right; 4 | ashlar | voussoir quarter-arcs and a keystone, 4 px proud | Over the ten passages, after the El Jem arches |
| `hub-cornice-{facing}` | 4 | ashlar | an ogee moulding, 6 px out | Hides the dusk light |
| `hub-marble-{part}` | plain, inlay, centre | Polished marble (#E6E1D8) with grey veins; `inlay`: a dark green-grey band; `centre`: the inlaid circle | cube | Rotunda and Approach floors |
| `hub-marblestairs-{facing}` | 4 (up) | marble | stairs (vanilla stair profile) | The spiral |
| `hub-balustrade-{facing}` | 4 | marble | rail, 3 turned balusters, plinth | Galleries, balcony |
| `hub-statue` | — | weathered marble, broken neck stump | A 3-block-tall standing draped torso with no head on a 1-block plinth (multiblock: plinth anchor + 2 invisible collision fillers) | Fixed landmark |
| `hub-pedestal-{artifact}` | scaraback, squidjar, noodle, clayfigure, radio, crownshard, levelkey, megbadge | the artifact's own; glass bell | A 10×10 px pedestal 12 px high, a glass bell over a small modelled artifact | Breaking one ejects you (§2.6) |
| `hub-dusklight` | — | invisible / ashlar | inside the cornice, no visible face | `lightHsv [2, 4, 13]` |
| `hub-void` | — | pure black #050506 | cube, `lightAbsorption 99` | Storm void, hole shaft |
| `hub-doormat` | 4 | coir brown (#8A6A3F), faded "WELCOME" | 14×10×1 px mat | Doorstep Carpet. Breaks to carpet fibres |
| `hub-megbanner-{facing}` | 4 | Navy cloth (#22314F), a white eagle silhouette, "M.E.G." | 14×24 px cloth hanging from a rod, slight sag | Draw our own eagle, not the wiki's image |
| `hub-keycabinet-{facing}` | 4 | Steel cabinet, a glass front, 12 small keys on hooks | wall cabinet 14×16×5 px with modelled hooks and keys | Decor (locked) |
| `hub-whiteboard-{facing}` | 4 | Whiteboard on a stand; a hand-drawn ring-and-spoke sketch, "L1 – T7, L11 – T10, 178 – T5" in marker | board 16×12 px on a stand with feet | Right-click: marks the map (§2.7) |
| `hub-fieldradio` | 4 | olive drab, dials | 10×7×6 px box, an antenna | Salvage: wire, bracket |
| `hub-ambersign-{facing}` | 4 | Painted plywood, "CAMP AMBER: NEW? ASK US" in amber | board on two legs | Camp |
| `hub-amberarrow-{facing}` | 4 | Amber chalk arrow (#E8A33C), chalky texture | 1 px decal plate | Also used in Level 1 near Hub doors |

Reused existing blocks: tents, bedrolls, firepit, the folding table and cot (if Level 1 camps have them; otherwise `hub-foldtable` and `hub-cot`, simple shapes), supply box, `pooltile`, chalk crosses.

### 4.5 Sounds (`tools/gen_hub.py`, synthesised like `gen_level_sounds.py`)

| File | Length | Character |
|---|---|---|
| `ambient/hub/silence.ogg` | 60 s loop | Almost nothing: a 45 Hz sine at 0.04 with a slow 0.1 Hz swell; four loops at pitches 1.0, 0.94, 1.06, 0.89, swapped every 3 minutes (Fandom's hum that changes pitch) |
| `ambient/hub/wind.ogg` | 30 s loop | Wind round stone, low-passed, gusts |
| `ambient/hub/thunder1–3.ogg` | 4–6 s | Distant thunder through thick walls (low-passed, long tail) |
| `effect/hub/keychime.ogg` | 1.6 s | A struck key: 500 Hz fundamental, inharmonic partials (2.76×, 5.4×), fast attack, 1.4 s decay |
| `effect/hub/keyturn.ogg` | 1.2 s | Three heavy ratchet clicks with a metallic slide between |
| `effect/hub/doorgrind.ogg` | 2.2 s | A concrete slab grinding aside: low noise, scrape, a thud at the end |
| `effect/hub/keyjingle.ogg` | 1.0 s | A big ring of keys shaken |
| `effect/hub/manifest.ogg` | 1.5 s | A deep pressure thump, then near-silence (played where the temporary door appears) |
| `effect/hub/keymaster.ogg` | 0.8 s | A low, displeased "hm" (no words) |

### 4.6 Items: Level Keys

`itemtypes/hub/key.json`: `hub-key-{tag}`. Held shapes are 3D (gen_shapes), 6–14 px long, `maxstacksize 1`, held in the hand like a small tool. The bow of each bears its sigil, painted on the texture.

| Tag | Look |
|---|---|
| l0 | Brass Yale key with a yellowed paper tag on a string |
| l2 | Rusted iron T-handle valve key |
| l3 | Electrical cabinet key: triangular socket, red rubber grip |
| l4 | An **office key card** (Object 2's non-standard key): white card, a magnetic stripe, a clip |
| l5 | Ornate hotel room key with a red tassel and a brass number fob |
| l6 | Matte black iron skeleton key, hard to see |
| l7 | Corroded bronze key with barnacles, tied to a cork float |
| l8 | A key carved of slate (the stone keys of Object 2) |
| l9 | House key on a ring with a little plastic house tag |
| l10 | Old barn padlock key on a loop of twine |
| l37 | White ceramic locker key on a coiled teal wristband |
| l94 | A painted clay wind-up key |
| run | Red-tagged fire-brigade key, "IN EMERGENCY" (Level ! owner may change) |
| fun | A candy-coloured plastic toy key with a balloon ribbon (Fun owner may change) |
| end | A bronze library key with a book-shaped bow (End owner may change) |
| 974 | (974 owner to brief) |
| 3999 | (3999 owner to brief) |

### 4.7 The Keymaster (entity `backrooms:hub-keymaster`, `tools/gen_models.py` + `tools/rig.py`)

**Model brief.**
- **Height:** 43 px (2.7 blocks): canon's "too tall… inhuman".
- **Body:** a long, narrow, deep-hooded cloak, charcoal (#1E1D22) with a faint violet sheen (#2C2338). Its hem hangs 1 px off the floor: he floats.
- **Face:** in the hood's shadow, a gaunt, pale-grey lower face and **two faint pale eyes** (2×1 px, slightly emissive). Canon speaks of his eyes.
- **Arms and hands:** long, thin, grey hands with long fingers.
- **Keys:** at the hip, a **large iron key ring with about 15 keys**, each a tiny modelled key (3–5 px) in varied shapes; the ring is a separate bone so it can swing.
- **The cloak** is two layered panels front and back, so it can swing.

**Animations:**
- `idle`: a slow 2 px hover bob, cloak sway, keys swing;
- `descend`: limbs still, the cloak flutters up, keys jingle (the entity is moved down 6 blocks over 3 s by code);
- `point`: one long arm out;
- `shove`: both arms forward hard;
- `turn`: a fast spin, the cloak swooping;
- `jingle`: a hand on the key ring.

**Entity.**
- Class `EntityKeymaster` in `src/Entities/Keymaster.cs`: no health loss (invulnerable), no AI tasks but "look at the nearest player"; never saved with the world.
- Sounds: `keyjingle` on idle now and then, `keymaster` when he speaks.

### 4.8 Lang keys (`assets/backrooms/lang/en.json`, Hub block only)

Level names:

| Key | English |
|---|---|
| `backrooms:levelname-hub` | The Hub |
| `backrooms:levelhint-hub` | Safe, cold, and nothing to eat. Every door is a level; almost none will open. |
| `backrooms:levelname-hub-tower` | The Tower |
| `backrooms:levelhint-hub-tower` | You will only be let in once. |

Doors and keys:

| Key | English |
|---|---|
| `backrooms:hub-door-locked` | Locked. Its key is somewhere in the level it leads to. |
| `backrooms:hub-door-dead` | Locked. Whatever lies behind it, its key is nowhere you can go. |
| `backrooms:hub-door-turn` | The key turns three times. |
| `backrooms:hub-arrive-oneway` | You look back. There is no door, only wall. |
| `backrooms:hub-arrive` | The door shuts behind you on silence. |
| `backrooms:hub-arrive-manifest` | The door is gone. |
| `backrooms:hub-key-found` | This key hums faintly when you strike it. |
| `backrooms:waypoint-hubdoor` | The door to {0} |

The Tower:

| Key | English |
|---|---|
| `backrooms:hub-tower-refused` | The door does not know you any more. |
| `backrooms:hub-keymaster-1` | More intruders. Say what you want, quickly. |
| `backrooms:hub-keymaster-2` | A key, then. Choose, and go. |
| `backrooms:hub-keymaster-3` | Your door is this way. Do not come back. |
| `backrooms:hub-keymaster-angry` | Put that down. Out. |

The outposts:

| Key | English |
|---|---|
| `backrooms:hub-register-read` | The M.E.G. door register: the open doors and the Tower are now on your map. |
| `backrooms:hub-camp-sign` | Camp Amber: new here? Ask us. |

Names:

| Key | English |
|---|---|
| `block-hub-door-*` | Concrete door |
| `block-hub-sigil-*` | Carved symbol |
| `block-hub-servicedoor-*` | Service door |
| `block-hub-ornatedoor-*` | Ornate door |
| `block-hub-statue` | Headless statue |
| `block-hub-whiteboard-*` | Door register |
| `block-hub-doormat-*` | Doorstep carpet |
| `block-hub-falsewall` | Concrete wall |
| `block-hub-jetfan-*` | Jet fan |
| `block-hub-lamp-*` | Tunnel lamp |
| `block-hub-lanesignal-*` | Lane signal |
| `item-hub-key-{tag}` | Level Key ({level name}), e.g. "Level Key (Level 5)" |
| `itemdesc-hub-key-*` | Found only in its own level. In the Hub it opens that level's door, once. |
| `entity-hub-keymaster` | The Keymaster |

---

## 5. Code plan

### 5.1 New files (owned by `hub`)

| File | What |
|---|---|
| `src/Worldgen/WorldLayout.Hub.cs` | The region: `HubCentreX/Z`, `HubRadius` (60 cells), `InHub`, `MayReachHub`. The road graph (`HubRoads`: spokes, Roundabout, rings, side lattice; segments binned by 256 blocks; cached per layout). `BuildLevelHub` (rasterise segments into tiles: walls, sidewalk, road, studs, lamp/fan/signal/stencil positions in `Variant`/`Overhead`/`Detail`). Door slots and the live-door table (`HubDoorAt`, `HubDoorOf`, `HubDoorSlots`). Service doors; the Tower plan (rotunda, passages, Approaches); outposts and camp sites; Far Tunnel features (falsewall, hole, tiled ends). `HubArrivalCell`, `IsHubArrivalSpot` (sidewalk, Crossroads zone, not an outpost). `HubCampSiteOfDay`, `HubZoneAt` |
| `src/Worldgen/WorldGenerator.Hub.cs` | The column builder: floor at `FloorFor(Hub)`, sidewalk slabs, road and studs, wall panels with seams, ceiling, lamps, fans, signals, stencils, doors (3×4 parts and the sigil above, orientation from the slot), service doors, Tower blocks, the void, outposts |
| `src/Regions/HubSystem.cs` | Server: `UseDoor` (route by level: in the Hub, a level door (open, keyed or dead); in Levels 1 and 2, a Hub entrance; elsewhere, a temporary door), key consumption and the turn and grind sounds, key resonance (a 4 s tick), the temporary doors (scheduler, placement and restoration; saved so a server restart cleans up), the Tower rules (entry, the visited flag, the Keymaster's spawn and dialog, the escort, the ejection on break), the door register (map marks), the visited-levels bitmask, the M.E.G. key stock. Client: the Keymaster dialog (`GuiDialog`, a short list of levels) |
| `src/Entities/Keymaster.cs` | `EntityKeymaster`: invulnerable, scripted moves (descend, escort), the look-at task |
| `tools/gen_hub.py` | Every asset in section 4 |
| `docs/new-levels/hub-plan.md` | this |

### 5.2 Hooks in shared files (small local edits, inside the block CONTRACT.md reserves)

| Where | Edit |
|---|---|
| `WorldLayout.cs` | `ComputeLevel`: `if (InHub(mx, mz)) return Hub;`. `BuildMacro`: `case Hub`. `GetEdge`: Hub → `new Edge { Pattern = WallPattern.HubWall }` (the plan lays over edges, like 37). `LevelBoundaryEdge` pattern → HubWall. `TemperatureAt`: Hub 6 / Far 2 / Tower 14. `LevelTemperatures` entry. `DisplayNumber` "Hub" (the scaffold may already do it) |
| `WorldGeometry.cs` | `HubDrop = 28`; `FloorFor(17)`. `BandBottomFor` stays the default |
| `WorldLayout.Reality.cs` | `StabilityAt`: Hub cases. `FindArrival`: `level == Hub` → `HubArrivalCell`, `IsHubArrivalSpot`. `ArrivalHeight`: Hub sidewalk +0.5. `StandingSpotNear.Standable`: accept `FloorKind.HubSidewalk` |
| `WorldLayout.Entities.cs` | `IsSanctuary`: `Hub => true`. `WandererSite`: the M.E.G. outpost (fixed) and Camp Amber (the day's site) |
| `Tiles.cs` | `WallPattern`: HubWall, HubDoor, HubServiceDoor, HubOrnate, HubAshlar, HubFalseWall, HubVoid. `FloorKind`: HubAsphalt, HubSidewalk, HubMarble. `Unders`: HubHole, HubFalseWall, HubTileEnd, HubTowerExit, PoolAsphalt (37). `Props`: HubLamp, HubJetFan, HubLaneSignal, HubStencil, HubShelter, HubStatue, HubPedestal (in the ranges CONTRACT.md reserves). On a door tile, `Tile.Detail` = sigil id; on a stencil, the tunnel number |
| `ThresholdNetwork.cs` | `Walked`: Hub falsewall → 4 (BothWays); Hub hole → Motion (OneWay); Hub tiled end → Poolrooms (BothWays, ReturnFeature = PoolAsphalt end); Level 37 `PoolAsphalt` → Hub (BothWays, ReturnFeature = HubTileEnd); Hub `HubTowerExit` → outside its ornate door. New public `HubDoor(int x, int z, int target)` → a one-way Passage (`Find` = `In(target)`, `InSnackrooms()` for 6.1); `HubEntrance(x, z)` → `BothWays(door, key, Hub, HubServiceDoor)`; `HubManifest(x, z)` → OneWay into Hub. Salts `SaltHub = 0x4B00 + n` |
| `ThresholdSystem.cs` | In `Use`: `if (kind is "hubdoor" or "towerdoor") { HubSystem.UseDoor(player, pos, kind); return; }` (as `thronedoor` does). A public `GoThrough(player, passage, home)` wrapper over `Take` + `Go` for HubSystem |
| `WorldLayout.Level1.cs` | Hub doors at corridor-sector dead ends (own salt) + amber arrows within 3 cells |
| `WorldLayout.Level2.cs` | 1 in 40 would-be-locked tunnel doors → Hub door (own salt) |
| `WorldLayout.Level37.cs` | 1 in 4 dry corridors ends in `PoolAsphalt` instead of `PoolCarpet` (own salt) |
| `AtmosphereSystem.cs` | `Levels[17]` (Crossroads), Far and Tower overrides; announce keys `hub` and `hub-tower`; no hum |
| `MenaceSystem.cs` / `Roster.cs` | Hub Safe (through `IsSanctuary`); Faceling as a rare Safe-band ambient in the Hub |
| `Rewards.cs` | Key drop hook: on a container broken in level L, `HubSystem.KeyFor(L, container kind)` |
| `Map/MapColors.cs`, `MapMarks.LevelName` | Colours: asphalt #3A3836, sidewalk #A9A399, live door amber #D8902A, other doors #6E6A62, Tower #DCD3C2. `LevelName`: Hub → "The Hub" |
| `Salvage/Breakdown.cs`, `Protection.cs` | Breakdown classes for the hub blocks (§2.9); Fixed: doors, sigils, statue, stencils |
| wanderer trade lists | An M.E.G. list with keys (generated stock from HubSystem) |
| `lang/en.json` | Section 4.8 |

### 5.3 Harness (`tools/mapgen`)

| Mode | Checks |
|---|---|
| `regionmap hub` | Renders the region (`render_region.py`) |
| `hubdoors` | Exactly one live door per level; 1 in Tunnel 7, 11 in Tunnel 10, 178 in Tunnel 5. Each live door's sidewalk is reachable from the Roundabout without entering the Tower. No two live doors within 40. Every door slot faces a sidewalk tile |
| `reach` (Hub window) | Every tunnel tile is connected; no pockets |
| `regions` | 60/60 arrivals in the Hub on sidewalks, none in a pocket |
| `links` | Level 1 and Level 2 Hub doors ↔ service door round trip; falsewall ↔ Level 4; tiled end ↔ Level 37 `PoolAsphalt`; hole one-way to 94; Hub doors one-way; all survive save and load |
| byte-identity | Layout hash before and after: Levels 0, 3–11 and 94 unchanged; 1, 2 and 37 differ only by the new entrances |
| `timing` | Hub cells under 3 ms each |

### 5.4 Verifying

Headless server on port **42477** with its own data path in the scratchpad:
- `/backrooms tp hub` (display name) and `/backrooms dump x z r` at the Roundabout, a spoke with a live door, a ring junction, the Tower and a Far Tunnel. Render with the gfx renderer.
- Check door orientation and the sigil above, studs, lamps lit, fans, stencils.
- Script the M.E.G. register, a key door (give a key with `/giveitem`), a Level 1 entrance round trip, and the Keymaster sequence.
- Not playable in a client from here: list what is unchecked in the Status section.

### 5.5 Phases

| Phase | Work | Done when |
|---|---|---|
| 1. Tunnels | Region, road graph, cross-sections, walls, road, lamps, fans, stencils, dead doors, arrivals, atmosphere, temperature, stability, Safe | `regionmap`, `reach`, `regions` pass; dump renders read as the photo |
| 2. Doors and keys | Live doors, sigils, service doors, keys (items, drops, M.E.G. stock), resonance, Level 1 and 2 entrances, temporary doors, Far Tunnel exits, the 37 pairing | `hubdoors`, `links`, byte-identity |
| 3. People | M.E.G. outpost, register, Camp Amber, shelters, notes, Facelings | headless: the traders appear, the register marks |
| 4. The Tower | The building, the ornate doors and their one-visit rule, the Keymaster (model, entity, dialog, escort), pedestals, the balcony storm | headless scripted visit |
| 5. Words | Handbook, README rows, lang | `gen_guide.py` builds |

---

## 6. Survival role

| | The Hub |
|---|---|
| Teaches | Keys and routes: the network has a centre, and it charges for every door |
| Gives | Safety (Safe band, rest), a way to any level you hold a key for, the open doors to Level 1, the city and the Snackrooms, the Far Tunnels' doors to 4, 37 and 94, traders, one gift from the Keymaster |
| Takes | Food (none), warmth (6 °C), keys (consumed), and the way back (every carved door is one-way; getting in again means finding a Hub door again) |
| Fits the loop | A crossroads on an expedition, never a home: no respawn (the anchor stays in Level 0), nothing to eat, and the way out does not lead back in |

---

## 7. Decisions for the user

Recommendations in bold.

1. **Shape and size.** **A fixed region of radius 1.9 km, laid out as ten numbered tunnels round the Tower, with ring roads and twisting side tunnels, all axis-aligned with chamfered corners.**
   - Alternative: an endless lattice like Level 37's, 25 km across, which is less legible and has no numbered tunnels.
2. **Carved doors are one-way, though walked through.** **Yes, as canon says.** The precedent is the Snackrooms' doors. The plain service doors are the two-way way back.
3. **Keys.** **Required for every door but 1, 11 and "178"; one key per trip, consumed; found only in their own level; also sold by the M.E.G. and given once by the Keymaster.**
   - Alternative: no key items, and each door opens for anyone who has already been to its level. This is simpler, but loses canon's central object and the trade economy.
4. **Level 178's open door** (a safe house with food, which the mod lacks). **Redirect to Level 6.1, the Snackrooms** (safe, food).
   - Alternative: Level 37, which has the hot water but no food.
5. **The open Level 11 door** gives Level 1 → Hub → city. **Keep it, one-way:** the Level 1 door is rare, and nothing in the city leads back to the Hub.
   - Alternative: lock it like the others.
6. **A second home?** **No.** The temporal gear still refuses outside Level 0; the Hub is a rest stop with no food.
7. **Temperature.** **6 °C** (cold enough to want clothes on a long walk, Far Tunnels 2 °C).
   - Alternative: Fandom's −4 °C, which makes the Hub a hazard and contradicts "a safe place to live".
8. **Keys' "remote access"** (Object 2: a key opens a door to its level from any door, anywhere). **No:** a Level 0 key would be a free way home from everywhere, ending corpse runs and the anchor's point. Keys work only in the Hub.
   - Opening locked doors in their own level is also left out, for now.
9. **Entrances.** **Level 1 Hub doors with amber chalk; Level 2 Hub doors; Level 37's asphalt corridors (Fandom); the rare temporary door.**
   - **No entrance from Level 11, and no generic noclip.**
10. **Level 1's "specific sequence".** **A rare set piece** (a Hub door at the end of a winding maintenance hall, marked by Camp Amber's arrows).
    - A real puzzle (the "Konami" turns up, up, down, down, left, right, left, right through Level 1's halls) can come later.
11. **The Tower and the Keymaster.** **Build them in phase 4.** One visit per player, and one key of a level you have been to, of your choice.
    - The Keymaster is a new model (§4.7).
12. **The endless stair** (canon: hundreds of rows for some, five for others). **Defer.** A seamless teleport from row 4 back to row 2 for anyone the Keymaster has not met yet would fake it, but it needs client testing.
13. **The balcony's storm void.** **The simple version**: a black void, rain particles, wind and thunder, and a lightning flash as a brief fog brightening. The view down onto the tunnels is not built.
14. **The M.E.G. sells keys.** **Yes: two at a time, re-rolled weekly, 30–45 rusty gears, only for levels someone in the world has entered.**
15. **Fandom's extras.** **Only the lane signals** (real road-tunnel gear, which Fandom calls traffic signs).
    - Not built: the TVs, colour-shifting lights, ceiling pipes of Almond Water, the self-cleaning floor (dropped items vanishing), and Fandom's Hounds, Skin-Stealers and Deathmoths.
16. **Benign Facelings** on the far sidewalk. **Yes, rare.**
17. **The M.E.G. register.** **Yes:** it marks the three open doors, the ten Tower entrances and the outpost.
    - Optional: it also reveals the "known area" (the Roundabout and the spokes to ring 1) on the explored map.
18. **Hub door positions.** **Random per world, except canon's three tunnels; sigils fixed for every world** (the handbook can show them, keys match doors).

---

## 8. Handbook text (`tools/gen_guide.py`)

**The Levels → The Hub**

> **The Hub.** A hidden crossroads of road tunnels under orange lamps, silent and cold. Ten numbered tunnels run out from a tower at its centre. Both walls are lined with great concrete doors, each with a carved crop circle over it. Every door leads to a level, and almost all are locked.
>
> - **Safe.** Nothing hostile can follow you in, and resting here counts. But there is nothing to eat, and at 6 °C you will want clothes.
> - **Open doors.** Three doors are always open, each one way: Level 1 in Tunnel 7, Level 11 in Tunnel 10, and the Snackrooms in Tunnel 5. The M.E.G. marked them.
> - **Level Keys.** Any other door needs its level's key. A key is found only in its own level, in its most dangerous places, or bought from the M.E.G. outpost in Tunnel 10. Hold a key in the Hub and listen: it rings toward its door. The door takes the key, and does not open from the other side.
> - **The way back** is the plain grey door you came in by.
> - **The Far Tunnels.** Past the third ring road the lamps die out. Somewhere out there are a wall that isn't there (Level 4), a hole in the road (Level 94) and tunnels where the concrete turns to white tile (Level 37).
> - **The Tower.** Ten ornate doors at the inner ends of the tunnels lead in. You are let in once. Its keeper wants you gone, and will give you one key to make sure of it.

**Ways Between Levels (rows)**

| From | Threshold | To | Way back |
|---|---|---|---|
| Level 1 | A carved concrete door at the end of a winding maintenance hall (amber chalk arrows lead to it) | The Hub | The grey service door you arrive beside |
| Level 2 | A steel tunnel door with a carved symbol over it | The Hub | The service door you arrive beside |
| Level 37 | Walking on along a dry corridor whose tile gives way to concrete and asphalt | The Hub | A tiled tunnel end, or a thin spot |
| Anywhere | A concrete door that was not there a moment ago (rare; it does not stay) | The Hub | None |
| The Hub | The open doors: Tunnel 7 / Tunnel 10 / Tunnel 5 | Level 1 / Level 11 / Level 6.1 | None |
| The Hub | Any other carved door, with its level's key (used up) | That level | None |
| The Hub | Walking into a stretch of wall whose seams don't meet (Far Tunnels) | Level 4 | Thin spot |
| The Hub | Falling into a rectangular hole in the road (Far Tunnels) | Level 94, out of the sky | None |
| The Hub | Walking on where the concrete turns to white tile (Far Tunnels) | Level 37 | The asphalt corridor, or a thin spot |

**Salvage and Recipes → Level Keys**

> **Level Key.** Each is tied to one level and looks like it (a hotel key with a tassel, a clay wind-up key, a key carved of slate). The carved symbol on it is the one over its door in the Hub. Found only in its own level: in den caches, behind forced doors, and in that level's worst places. In the Hub it opens its level's door once, and is used up. Nowhere else does it open anything.

**What Lives Here → The Keymaster**

> **The Keymaster.** A tall cloaked figure with a ring of keys, the keeper of the Hub's Tower. He cannot be harmed and does not harm. He will give you one key to a level you have been to, and show you to its door, so that you leave. Break anything of his and he throws you out with nothing.

## Manifest changes (phase 2)

From the code agent (2026-10-07). The code uses these exactly; where it differs from section 4, this wins.

- **Facing:** every `-{facing}` variant (`north|east|south|west`) is the side the block's front looks toward: toward the tunnel, toward whoever uses it (as `poolwall-slit-{side}`). A door on the north wall of an east-west tunnel faces `south`.
- **`hub-door-{col}-{row}-{facing}`:** behaviour **`BackroomsHubDoor`** (registered by `HubSystem`; no `BackroomsThreshold`). Columns are as seen by someone facing the door: `l` on their left. Row 1 (and `hub-servicedoor-lower`) has an 8 px stone sill at the bottom, so the leaf starts at the sidewalk slab's top. The door stands on rel 1–4, the sigil panel on rel 5, in main tunnels and side tunnels alike.
- **The pink ribbon door (Level 974)** replaces the keyed 974 door (LINKS.md). It is a carved door with sigil 18, whose `c-3` part is **`hub-door-ribbon-{facing}`**: the same door panel with a pink satin ribbon tied in a 3D bow across it. Same behaviour.
- **Sigil ids: 0–44.**
  - 0 is the Hub (entrances).
  - 1–18 are as in the table in §4.3. 19 is unused (Level 3999 is dropped; don't build it).
  - **20 is "178"** (the open door to Level 6.1).
  - **21–44 are the 24 dead designs** (not 20–43).
- **`hub-servicedoor-{lower|upper}-{facing}`:** `BackroomsThreshold` kind `locked`. The same blocks are the Hub's entrance in **Level 1**, with `hub-sigil-0-{facing}` over them on rel 3. The code places them as wall decorations itself, so no DetailBlocks entry is needed.
- **`hub-ornatedoor-entrance-{l1|l2|l3|r1|r2|r3}-{facing}`:** `BackroomsThreshold` kind `towerdoor` (they refuse until the Tower is built in phase 4). The `forbidden` set is not needed yet.
- **Keys:** `itemtypes/hub/key.json` → `backrooms:hub-key-{tag}`, tags `l0 l2 l3 l4 l5 l6 l7 l8 l9 l10 l37 l94 run fun end`. There is no `974` key (the pink door needs none) and no `3999`.
- **Sidewalk:** `hub-sidewalk` is a half slab on rel 1 (the road's asphalt is a full block on rel 0). `hub-curb-*` is not used yet.
- **The hole:** `hub-void` at its bottom (rel −3). `hub-holelip-*` is not used yet.
- **Wall panels:** `hub-wall-{plain|left|bottom|corner}` everywhere in the tunnels; `hub-ceiling` over every tunnel; plain concrete (`concrete`) in the solid mass.
- **Lamps:** `hub-lamp-{on|dead}-{facing}` at rel 5 in main tunnels and rel 4 in side tunnels, `lightHsv [5, 6, 11]`.
- **Overheads:**
  - `hub-jetfan-{ns|we}` hangs on rel 7 of a main tunnel. The axis is the one the fan's length runs along.
  - `hub-lanesignal-{go|stop}-{facing}` is on rel 7 too.
- **Stencils:** `hub-stencil-{1..10|tower}-{facing}` and `hub-plaque-{1|11|178}-{facing}` go on rel 3.
- **Tiled ends:** `hub-tilecrumb-{1|2}` (and Level 37's `pooltile-plain`) at the tiled tunnel ends.
- **Level 37's asphalt corridor end:** `hub-asphalt-plain`, `hub-wall-*` and `hub-ceiling`.
- **Later notes from the code agent (2026-10-07, after reading what the asset script made):**
  - **The pink door:** `hub-pinkdoor-{col}-{row}-{facing}` is adopted for Level 974's door, in place of the ribbon part. Sigil 18 stays above it.
  - **Door behaviour:** `hub-door-*` and `hub-pinkdoor-*` may keep `BackroomsThreshold` kind `hubdoor`. `HubSystem.AssetsFinalize` swaps it for `BackroomsHubDoor` on both sides. Using `BackroomsHubDoor` directly is cleaner.
  - **Lang keys the code uses** beyond the asset script's: `hub-falsewall`, `hub-hole`, `hub-tileend`, `blockhelp-hubdoor`. They were added by hand; keep them. `level-1702` (the Far Tunnels) is used as the title out there.
- **From the asset agent (2026-10-07), what `tools/gen_hub.py` builds** (modules `gen_hub_kit.py`, `gen_hub_sigils.py`, `gen_hub_doors.py`, `gen_hub_tower.py`, `gen_hub_items.py`, `gen_hub_sounds.py`, `gen_hub_keymaster.py`, `gen_hub_lang.py`; run `bash tools/locked.sh run python tools/gen_hub.py`, which first empties its own `hub/` asset folders):
  - **Facing** as the code agent says: `-north` shows its face to the north. Blocks set into a wall (doors, sigils, sigil sides, service doors, ornate doors) are the wall cell; wall-hung pieces (lamps, stencils, plaques, amber arrows, banner, key cabinet, pilasters, cornice) are the air cell with their back against the wall behind them. `l` = the viewer's left.
  - **Doors:** `hub-door-*` and `hub-pinkdoor-*` now carry `BackroomsHubDoor` directly. The carved door's frame stands 1 px proud with a dark gap round the slab; row 1's sill reaches 1.2 px out over the sidewalk.
  - **Sigils:** `hub-sigil-{n}` for n = 0–18 and 20–44 (no 19). 20 is "178" and also the bow of the 6.1 key; 21–44 dead. Table in `gen_hub_sigils.py` (`LIVE`, `LEVEL_SIGIL`). The carved sides (`hub-sigilside-{l|r}`) have a groove frame and a straight groove leading into the disc, not half rings (they read as part of the sigil).
  - **Service door:** two parts only, `lower` (sill, kick plate) and `upper` (push bar, wired-glass window, frame head).
  - **Stencils:** `hub-stencil-tower` is an arrow pointing straight on (right on either wall); `towerl` / `towerr` point along the wall if the code ever knows the side.
  - **Lamps:** an extra state `hub-lamp-flicker-{facing}` (`BackroomsFlicker`, off block `hub-lamp-dead-{facing}`).
  - **Amber arrows:** `hub-amberarrow-{l|r}-{facing}` (a direction group was needed).
  - **Statue:** `hub-statue` is the plinth (anchor); the figure rises 2 more blocks, which take the invisible `hub-statuefill` for collision.
  - **Cot:** `hub-cot-{head|foot}-{facing}`, two blocks long (the head toward the facing). Folding tables: the existing `foldingtable`.
  - **Keys:** every level's key, not only the code's list: `hub-key-{l0 l1 l2 … l11 l61 l37 l94 run fun end}` (l1, l11 and l61 too, for the Keymaster and traders). `attributes.hubKey` = {level (internal id), tag, sigil, sub ("6.1" for l61)}. No 974 or 3999 key.
  - **Keymaster:** `entities/hub-keymaster.json`, class `EntityAgent` for now (swap in the code's class when it exists); no health and no physics behaviours; vanilla AI `lookatentity` (players) plus `idle` playing `jingle`. Animations: `idle`, `descend`, `point`, `shove`, `turn`, `jingle`. Lang `item-creature-hub-keymaster` / `creature-hub-keymaster`.
  - **Sounds:** `ambient/hub/{silence,wind,thunder1,thunder2,thunder3}`, `effect/hub/{keychime,keyturn,doorgrind,keyjingle,manifest,keymaster}`. `silence` is a seamless 60 s loop at nominal pitch; the code steps its pitch.
  - **Lang:** `level-17`, `levelhint-17`, `levelname-17` (replacing the scaffold's); `level-1701`/`1702` (the Tower, the Far Tunnels) with hints and names; §4.8's messages plus `hub-door-open`, `hub-key-near`, `hub-pinkdoor-refused`, `hub-pinkdoor-open`, `hub-tower-forbidden`, `hub-keymaster-choose`. The hand-added keys are left alone.
  - **Lamp brightness:** please raise `hub-lamp` `on`/`flicker` from `lightHsv [5, 6, 11]` to **`[5, 6, 14]`**. A headless dump showed light 0–5 at floor level with 11. The code now hangs lamps on rel 4, on both walls of a main tunnel (staggered every 8 blocks) and on one wall of a side tunnel.
  - **Correction (asset agent, 2026-10-09):** `hub-sigil-19` is built after all (its four-ring design), because `WorldGenerator.Hub.cs` looks up every id 0-44 and the server warned it was missing. Nothing places it. A headless server (port 42487) then loaded with no Hub or Keymaster warnings.
  - **Done (asset agent, 2026-10-09):** `hub-lamp` `on` and `flicker` now give `lightHsv [5, 6, 14]`.
