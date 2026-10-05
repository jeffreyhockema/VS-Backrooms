# The Backrooms (Vintage Story mod)

Wake up in the Backrooms with nothing. You start in Level 0, an endless, procedurally generated expanse of mono-yellow rooms under buzzing fluorescent lights. Walk far enough and it gives way to deeper levels, one after another: the concrete car park of Level 1, the pipe tunnels of Level 2, the Electrical Station, the Abandoned Office, and the Terror Hotel. Scavenge supply boxes and crates for Almond Water, food and basic materials.

Targets Vintage Story 1.22 (.NET 10).

![Top-down overview of the levels](docs/levels-overview.png)

*About 1,300×1,300 blocks around spawn, from the centre outwards: Level 0 (yellow), Level 1 (grey), Level 2 (dark), Level 3 (brown and brick red), Level 4 (light grey), and Level 5 (red), which has tan lobbies and boiler halls.*

## Playing

Create a new world and pick the **The Backrooms** playstyle. It only affects worlds created with that playstyle. Normal worlds are untouched.

- **Map (M / F6):** the map only shows what you have actually seen. It reveals the area around you along your line of sight, so walls block it. Explored areas are remembered between sessions, so you can find your way back.
- **Starting waypoint:** "Where I woke up" marks your starting point.
- **Your own waypoints:** right-click the map to add one.
- **Dark areas** are easier to explore with a candle.

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
| Dry grass (tinder) | 2 wallpaper strips |
| 2 sticks | rotten wood |
| Firewood | 2 rotten wood |

With tinder, sticks and firewood, the vanilla fire starter, firepit and torches work as usual.

### Reality Stability

The gear on the HUD shows how firmly you are anchored. It is Vintage Story's temporal stability, with the Backrooms' own geography.

- **Each area has its own stability.** Where it is low the gear turns backwards and your stability drains. When yours is low the world distorts, and at zero you take damage.
  - Kind places: the Manila Room, the Level 1 car park, all of Level 4, the Beverly Room.
  - Bad places: Level 0's blackout zones, Level 2, Level 3 (worst in its flooded tunnels), the hotel corridors and above all the boiler halls.
- **Almond Water** restores some stability when you drink it.
- **Reality Shifts:** about once every 30 in-game hours the lights fail for a few hours. Everything beyond a few steps is lost in black, and stability drains everywhere.

### The topology lies

The levels are rings, but some thresholds put you down somewhere else. Each one always leads to the same place, so you can learn them and mark them on the map.

- **Elevators** (Levels 3, 4 and 5): use the doors. Most arrive beside another elevator on another level, and the way back is rarely the same.
- **Hotel doors:** most are locked, but a few open onto another part of the hotel, the Electrical Station or the Lobby.
- **Pits in Level 0:** falling in drops you into Level 2.
- **Level 4 stairwells:** climbing the stairs brings you out of another stairwell on the same floor, or now and then back in Level 0.

## How the levels fit together

The levels nest like blobs within blobs around the spawn point. Each ring is currently only about 100 blocks wide, to make testing quick, so Level 5 starts roughly 500 blocks from spawn and continues forever.

The boundaries follow noise-warped distances. Where two levels meet there is a full-height wall with a few doorways through it.

Some areas next to a boundary blend, as the wikis describe the transitions:

| Boundary | What blends |
|---|---|
| Level 0 to 1 | Level 0's carpet wears through to concrete and ceiling tiles go missing. |
| Level 1 to 2 | Pipes start running along Level 1's ceiling. |
| Level 2 to 3 | Level 3 keeps Level 2's pipe bundles instead of cables. |
| Level 4 to 5 | The office carpet turns to hotel red and wood panelling creeps in. |

To space the levels out, multiply `LevelRadii` in `src/Worldgen/WorldLayout.cs`. The values are in 32-block cells.

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
  - the Manila Room: 8×8, wooden floor, a door on each side, and one dim orange lamp.

## Level 1: the Habitable Zone

An endless cross between an underground car park and an abandoned warehouse.

- **Materials:** grey concrete everywhere: painted parking-bay lines, puddles, cracks, and rusty rebar sticking out of damaged walls in 3D.
- **Halls:** laid out like a real multi-storey car park.
  - Columns every 9 blocks, with painted bay letters A–F and concrete beams spanning between them under the slab. Some sectors have massive 2×2 columns.
  - Rows of 3-wide parking stalls with painted dividers and wheel stops, back to back along the column lines.
  - 6-wide two-way driving aisles with dashed yellow centre lines, and cross aisles every five bays so you can drive between rows.
  - A few abandoned cars (red, blue, white or black), crates left in stalls, the odd shear wall between columns, and rarely a short flight of concrete stairs climbing straight into a wall.
- **Lights:**
  - Twin-tube fluorescent fixtures hang on chains over the aisles and stalls, with thin white conduit along the column lines.
  - Columns carry tube lights on their faces.
  - Lights are on shared circuits, so whole sections are dead or failing together.
- **Supplies:** wooden crates, alone or stacked, are the best source of food and Almond Water.
- **Corridor sectors:** a grid of tight 2-wide concrete corridors with small rooms off them.
  - The rooms have bare bulbs on cords, and some are storerooms with shelving.
  - Doorways into these sectors sit under glowing green EXIT signs.
- **Atmosphere:** grey fog, with a low ground fog hanging over the concrete. Humid, 28 °C.

## Level 2: Pipe Dreams

Narrow, dark concrete utility tunnels, 1–2 blocks wide, with straight runs in multiples of 5 blocks. Every tunnel connects; hubs, dead ends and cramped machine rooms branch off.

- **3D pipework:**
  - Bundles of cream lagged, rusty and red fire-line pipes run along the top of every tunnel and meet at junction boxes where tunnels turn or branch. They sit above head height, so they never block the way.
  - Whole stretches of wall carry continuous horizontal pipes, with risers and red valve wheels along them; other stretches are machinery, brick or hazard signs.
  - Here and there a cracked joint hisses and puffs steam.
- **Lights:** sparse buzzing fluorescent fixtures in white or orange, wired in series, so long sections are completely dark.
- **Props:** machine cabinets line the machine rooms. There are oil drums (some still hold Almond Water) and the rare forgotten supply box. Food is scarce.
- **Atmosphere:** a dark, murky haze. Hot, 38 °C.

## Level 3: the Electrical Station

A hot (35 °C), cramped maze of brick and two-tone glazed-tile corridors.

- **Layout:** 2-wide corridors on a lattice, joined into one connected maze.
  - Some links are 1-wide squeezes.
  - Many side routes are blocked by indestructible white bars, so the way on is visible but out of reach.
- **Machinery:** pipe runs on the walls, electrical panels and industrial fans, cable bundles in trays overhead, and humming transformers.
- **Lights:** sparse amber fixtures; whole stretches are dark.
- **Rooms:** the solid blocks hold numbered machine rooms (white signs over the doors), supply caches (this is a loot-rich level), and barred window rooms glowing with impossible daylight.
- **Rare:** a whole cell becomes a vast transformer hall.
- **Manholes:** these drop into flooded utility tunnels beneath the corridors, where the water is freezing (−4 °C). Ladder rungs lead back up.

## Level 4: the Abandoned Office

One endless, quiet, cool (15 °C) office floor.

- **Feel:** grey carpet with darker marks where furniture once stood, drywall columns, and a drop ceiling with fluorescent troffers. About half the troffers are dead, and the odd tile is missing.
- **Windows:** walls of windows show rain and fog that never end. Their grey storm light is often the main light, and you can hear the rain.
- **Open-plan floors:** cubicle farms of desks, office chairs and old CRT computers.
- **Office blocks:** corridors of small lit offices with filing cabinets, glass conference rooms, stairwells under EXIT signs whose stairs climb into the ceiling, and elevator lobbies whose doors never open.
- **Almond Water:** vending machines and water coolers still dispense it. Use them to take a bottle; each has a few left.

## Level 5: the Terror Hotel

A 1930s grand hotel that never ends (20 °C).

- **Corridors:** long, double-loaded corridors (rooms on both sides) with red-and-gold damask carpet, mahogany wainscot under red panels in gilt frames, candle sconces, dome lights, and unsettling portraits. Copper-cage elevator gates stand on the cross corridors.
- **Guest rooms:** numbered brass-plaqued doors, about two-thirds locked. The open rooms are cramped and sometimes furnished with a bed, a nightstand lamp and a wardrobe. Now and then a turntable plays jazz.
- **Grand lobbies:** a taller ceiling, red faux-marble columns, chandeliers, potted palms, wingback chairs and sofas.
- **The Beverly Room:** a ballroom with a half-finished game of Mahjong on a small table under its great chandelier, with placards beside its four doors.
- **Boiler halls:** STAFF ONLY doors lead into hot (42 °C) halls of stained plaster. Barred machinery bays hold boilers and glowing furnaces, under pipes and steam leaks.

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
- **`WorldLayout.Level0.cs` … `.Level5.cs`:** how each level lays out a cell.
- **`WorldGenerator.cs`:** turns layout tiles into blocks, with one block rule per level.
- **`WorldLighting.cs`:** computes block light directly with a flood fill over the column and its neighbours' light sources.
  - Vintage Story's engine is far slower with this many lights.
  - Light sources are registered with each chunk, so relighting after block changes still works.
- **`src/Lights/`:** failing lights.
  - A block entity swaps the panel's look on the client.
  - Only lights near the player are animated.
- **`src/Salvage/`:** makes structural blocks unbreakable, and the behaviour that strips wallpaper and carpet.
- **`src/Reality/`:** Reality Stability per area, Reality Shifts (scheduled from the seed and calendar, so nothing needs syncing), and Almond Water's effect.
- **`src/Thresholds/`:** elevators, hotel doors, pits and stairwells that teleport, with arrival points checked to be walkable away from.
- **`src/Props/`:** vending machines and water coolers that dispense Almond Water.
- **`src/AtmosphereSystem.cs`:** per-level fog on the client, blended as you cross between levels.
- **`src/Map/`:** the explored-areas map layer, which replaces the vanilla terrain map in Backrooms worlds.
- **`src/BackroomsModSystem.cs`:** world type registration, climate, spawn, the starting waypoint and debug commands.

## Debugging

- `/backrooms column [x z]` (admin) prints the block stack, block entities and light levels of a column, from the ceiling of a grand room down into Level 3's tunnels. If the chunk isn't loaded, it loads it.
- `/backrooms where` names the level and zone you're in, and its stability.
- `/backrooms goto <0-5>` teleports you into a level.
- `/backrooms shift [hours]` starts a Reality Shift (default 2 in-game hours; 0 ends it).
- `.tfedit` in-game lets you tweak how held and dropped items are positioned.

## Assets

Textures, 3D models, block definitions and sounds are generated by scripts:

- `tools/gen_textures.py` (needs Pillow)
- `tools/gen_shapes.py`: block models such as pipes, fixtures, furniture and machinery, built from boxes
- `tools/gen_blocktypes.py`: block definitions for Levels 3–5
- `tools/gen_sounds.py` (needs numpy and soundfile): hum, flicker crackle, steam, transformer, rain and jazz

Re-running them overwrites the files, so remove an asset from its script once you replace it by hand.

The playstyle's name and description must live in `assets/game/lang/worldconfig-en.json`, because the world-creation screen reads them before mod assets load.
