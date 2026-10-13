# Developing Backrooms: Survival Story

How to build the mod, how the code is laid out, the debug commands and the scripts that generate the assets. The design plans and research the mod was built from are in [design/](design/README.md); how it plays now is in the [player guide](GUIDE.md).

## Building and running

You need the .NET 10 SDK and Vintage Story 1.22. The asset generators also need Python 3.10+ with the packages in `tools/requirements.txt` (`pip install -r tools/requirements.txt`).

- **Where the game is:** the build, the VS Code launch config and the generators look for Vintage Story in the `VINTAGE_STORY` environment variable, and otherwise in `%APPDATA%\Vintagestory` (the build and the generators only). Set the variable if the game lives elsewhere. For the build alone you can instead put the path in a git-ignored `Backrooms.csproj.user`: `<Project><PropertyGroup><VintageStory>D:\Games\Vintagestory</VintageStory></PropertyGroup></Project>`.
- **Build:** `dotnet build`. The mod is output to `bin/Debug/Mods/backroomsss/`.
  - Close the game first: a running game locks the mod DLL.
- **Run with the debugger from VS Code:** use the *Vintage Story (client + mod)* launch config (F5). It needs `VINTAGE_STORY`.
- **Run without VS Code:** `Vintagestory.exe --addModPath "<repo>/bin/Debug/Mods"`
- **Release zip:** `dotnet build -c Release` writes `bin/backroomsss_<version>.zip`, ready to upload.
- **Version number:** kept the same in `modinfo.json` and `Backrooms.csproj`. The build check (`src/BuildCheckSystem.cs`) compares a fingerprint of the build (the assembly's id and the names of its assets), not the version, so a server and client with different copies are warned in chat even when the version matches.

## Keeping saves working

The mod is released, and players have worlds made with it. Every change must leave those worlds loading and playing as before:

- **Codes:** never rename or remove a block, item or entity code, or change a block's variant groups. A world stores blocks and items by code, so a missing code loses them. Add new codes beside the old ones; if something has to go, keep a stub or remap the old code to the new one.
- **Class names:** never rename a registered block, item, block entity, entity or behaviour class that saved chunks refer to.
- **World generation:** a change that would alter what an existing world generates goes behind a new layout version (see *Layout versions* below). Run `layouthash` before and after: the output for every older version must not change.
- **Saved data:** `backrooms-thresholds`, `backrooms-notes`, block entity attributes, the client's explored-map store and anything else saved must still read the old format. Add fields with defaults; never change what an existing key means.
- **World settings:** keep their codes and option values. A new setting's default must give the old behaviour, because existing worlds don't have it set.
- **The asset domain** stays `backrooms`.

When in doubt, load a world made with the last release and check it.

## Code map

- **`src/Worldgen/WorldLayout.cs`:** deterministic layout with no game dependencies. Contains:
  - the level map;
  - one 32×32 "macro cell" per chunk;
  - shared edges, which are a pure function of the edge so neighbours always agree;
  - per-position temperature.
  - **Ring sizes:** to resize the levels, change `RingWidths` (the average width of each ring in 32-block cells); `Stretch` sets how lopsided they are.
  - **Layout versions** (`WorldLayout.CurrentVersion`, `Version`): a world keeps the layout version it was made with, recorded in its world config (`backroomsLayoutVersion`, by `BackroomsWorld.LayoutVersion`; worlds made before versions are 1). A fix that would move what an existing world holds goes in behind a new version, never in place, so chunks generated later still match the ones already there. Version 2 rolls Level 37's deep halls apart from their width and Level 5's boiler-bay fittings by row; version 3 gives Level 0 more and fewer picked-over supply boxes. In version 4 a doorway wider than one block has one sign over its middle (EXIT, STAFF ONLY, a store's sign, a Level 3999 unit's neon), drawn in halves over the middle two blocks of an even width (`WorldGenerator.Signs.cs`). Version 5 is the visual-review pass: arrival points picked where you can see the level (`WorldLayout.ArrivalPreference`), Level 4's thinner cable droops, and dressing across many levels. Version 6 makes camp tents and sleeping bags full size (with `WorldLayout.Parts.cs` removing any multi-tile prop that lost a part) and packs Level !'s hallway with set pieces. Version 7 lets the *Backrooms scarcity* setting thin Level 9's gardens and Level 10's crops and berry bushes (`WorldLayout.ThinFood`, from the `FoodScale` the game side passes in); at Normal and Plentiful it lays out as 6. The full list is in the doc comment on `WorldLayout.CurrentVersion`. The harness takes `LAYOUT_VERSION=<n>`; `layouthash` hashes version 1 unless told otherwise.
- **`WorldLayout.Level0.cs` … `.Level11.cs`:** how each level lays out a cell. Level 6.1 is in `.Level6.cs`.
  - Level 11 is a separate region rather than a ring (`InCity`), planned a whole city block at a time (`BlockPlan`).
  - Levels 37 and 94 are regions too, kept as levels 12 and 13 (`WorldLayout.Poolrooms`, `.Motion`; `DisplayNumber` gives the number players see). `.Level37.cs` plans 96-block blocks (`PoolPlan`); `.Level94.cs` works out its hills, roads and towns from coordinates and plans each hilltop (`HillPlan`), each town and the castle. Their floors lie lower than the others' (`WorldGeometry.PoolDrop`, `MotionDrop`).
- **`WorldGenerator.cs`:** turns layout tiles into blocks, with one block rule per level. Levels 6 to 10 are in `WorldGenerator.Deep.cs`, including Level 8's 3D caves and geology and Level 7's sea.
  - Level 11 is in `WorldGenerator.City.cs`: façades storey by storey, ground floors, roofs and the subway. Its streets lie `WorldGeometry.CityDrop` blocks lower, so its columns are generated (and lit) over a band of their own.
  - Levels 37 and 94 are in `WorldGenerator.Pool.cs` and `WorldGenerator.Motion.cs`; each is lit over its own band (`WorldGeometry.BandBottomFor`).
- **`WorldLighting.cs`:** computes block light directly with a flood fill over the column and its neighbours' light sources.
  - Vintage Story's engine is far slower with this many lights.
  - Light sources are registered with each chunk, so relighting after block changes still works.
  - What lighting needs of a cell (absorption and light sources) is kept in a small cache: each cell is wanted by nine chunks, and the generator hands over the cell it has just built rather than having it recomputed.
- **Vanilla dressing in the generator:**
  - **`WorldGenerator.Vegetation.cs`:** grass, flowers, ferns, round tree crowns and pond plants for the open-sky levels (9, 10, 11 and 94). Plants are chosen per column from hashes and noise, and the crowns come from the neighbouring trunk tiles.
  - **`WorldGenerator.Caves.cs`:** Level 8's speleothems, glowworms, lichen, fungi, boulders and crystals, and Level 7's seagrass, dead reef and shore litter.
  - **`WorldGenerator.Interior.cs`:** Level 5's boiling sumps.
  - Vanilla plants only sway where they get sunlight (`BlockPlant`), so swaying grass belongs on the open-sky levels. Water plants sway anywhere.
  - Anything placed underneath a plant needs `fertility` above 0.
- **`UndergroundSystem.cs`:** the ground under the levels: `WorldGenerator.FoundationDepth` (8) blocks of concrete under every floor, then vanilla's own terrain, strata, caves and ores from its generators, with the land's sea level put at the floor; no surface features or soil deposits. `/backrooms ground x z` counts what lies under a chunk.
- **`CaveColumn.cs`:** Level 8's cave and ore noise worked out once per column (the few lattice layers a column crosses) instead of once per block, which made Level 8 generate nine times faster.
- **`src/Lights/`:** failing lights.
  - A block entity swaps the panel's look on the client.
  - Only lights near the player are animated.
- **`src/Salvage/`:** salvage and the behaviour that strips wallpaper and carpet; `Breakdown.cs` (what the building breaks down to, with which tool) and `Protection.cs` (the roofs, the tops of the walls between levels and the fixed blocks that never break: a Harmony postfix on the required tool tier, so the client never starts cracking what it cannot break). `/backrooms canbreak x z [y]` lists a column with each block's tier and drops. Assets for rubble from `tools/gen_breakdown.py`.
- **`src/Reality/`:** Reality Stability per area, Reality Shifts (scheduled from the seed and calendar, so nothing needs syncing), and Almond Water's effect. `AnchorSystem` keeps waking up to Level 0 (the temporal gear is swapped for a subclass by `patches/temporalgear.json`); `HeatSystem` raises the `hungerrate` stat in hot places.
- **`WorldLayout.Gates.cs`, `.Loot.cs`, `.Dens.cs`, `.Notes.cs`:** gates and the chalk arrows to them; which boxes and crates were picked over, and Level 0's stashes; dens; what wanderers' notes find.
- **`src/Map/MapMarks.cs`, `WandererNote.cs`:** waypoints made for the player, and the wanderer's note item.
- **`src/Notes/`:** notes and the journal: `NoteCatalog` (loads `config/notes.json`), `NoteSequencer` (pure: which entry is due; shared with the harness's `notes` mode), `NoteSystem` (reading, the journal's data in save data `backrooms-notes`, the pocket note, commands; the client's journal on J), `MarkResolver` (what a note marks), `NoteSystem.Spots` (extra and folded drops, loose notes), `BlockLooseNote`, `NoteDialogs`.
- **`src/Salvage/PryBar.cs`, `ScarcitySystem.cs`:** the pry bar (a behaviour put ahead of every locked door's own), and the *Backrooms scarcity* setting: it scales food drops, and its `FoodScale` is read by the dispensers, Level 974's fridge, the creature spawner and the layout.
- **`src/Thresholds/`:** the ways between the levels, with arrival points checked to be walkable away from (and, in worlds from layout version 5, picked where you can see the level where one is near: under a working light in Levels 2 and 3, in a slit's light in Level 37, out in the open and clear of trees, cars and house walls in Levels 9, 11 and 94; see `WorldLayout.ArrivalPreference`).
  - `ThresholdNetwork.cs` has no game dependencies: what each threshold is, where it leads, which are two-way, and the links written down so far (saved with the world as `backrooms-thresholds`).
  - `ThresholdSystem.cs` notices players going through thresholds, moves them and leaves thin spots.
- **`src/Props/`:** vending machines, water coolers and Snackrooms shelves that dispense items and restock.
- **`src/Deep/`:** surveyor's chalk, the worm mass under Level 10, scalding tar, and the creature spawner (fish, drifters, wildlife and livestock, each only on its own level).
- **`src/Entities/`:** the Backrooms' own entities.
  - `MenaceSystem.cs` is the director: every two seconds it rates each player's danger (band and menace) and plays a distant sound or puts down an entity for a glimpse, a stalk or a hunt. `Roster.cs` says which entities and sounds each level has.
  - `AiTaskMenace.cs` is what an entity does about its player; `AiTaskMoth.cs` is the Deathmoths' flight. Each entity's counters (light, fire, Almond Water...) are switched on in its task config.
  - `EntityBehaviorMenace.cs` ends encounters and despawns entities out of sight; `Senses.cs` has light, sight and the wards (fires, Firesalt, angel statues).
  - `WorldLayout.Entities.cs` (in Worldgen) gives the director depth into a level, distance to the next, sanctuaries and nearby thresholds.
- **`src/AtmosphereSystem.cs`:** per-level fog and sky on the client, blended as you cross between levels: Level 6's darkness, Level 7's depth, the Suburbs' night and Level 10's overcast. Every level but 10, 11 and 94 holds its fog and ambient light at the day's, so it looks the same at any hour.
- **`src/Map/`:** the explored-areas map layer, which replaces the vanilla terrain map in Backrooms worlds, and the *Backrooms map* world setting (`MapSetting`): `BackroomsMapSystem` turns vanilla's `allowMap` off for None, and `MapMarks.Add` makes no waypoints unless it is Seen areas.
- **`src/GuideSystem.cs`:** swaps the Backrooms pages into the handbook's Guides tab, in Backrooms worlds only (their text is from `tools/gen_guide.py`).
- **`src/Tutorial/BackroomsTutorial.cs`:** *Backrooms: First Steps*, the 15-step tutorial on the game's own tutorial system that replaces the vanilla First Steps in Backrooms worlds and starts by itself on a client's first join; progress is kept per client in `ModConfig/tutorial-tutorial-backrooms-firststeps.json`.
- **`src/Regions/`:** what Levels 37 and 94 do. `PoolSystem.cs`: the water's relief, the Reservoir's viscous water, red water's mark. `MotionSystem.cs`: day and night, playing doll, the castle's alarm, the throne room's doors, the soft landing, and the King's trial; `MotionLandmark.cs` draws the castle where it would be past the view distance. And the seven far places: `RunSystem.cs` (Level !'s chase, over the pure model `RunChase` in `WorldLayout.LevelRun.cs`), `FunSystem.cs` (parties, Party Fever, the disguise; the Partygoers' AI is `src/Entities/AiTaskPartygoer.cs`), `EndSystem.cs` (computers, distortions, isolation, the Junkies), `HubSystem.cs` and `HubTower.cs` (keys, doors, the Tower, the Keymaster, the manifest door), `L974System.cs` (the houses and Kitty, `EntityKitty`; what counts as cute is patched in by `assets/backrooms/patches/l974-cute.json`), `L3999System.cs` (machines, tickets, prizes, stalls, vending, walkways, attendants, `BackroomsAttendant`; tickets and prizes come from the block types' attributes, and blocks marked `l3999structure` never break), `L188System.cs` (the windows, blinds, the arm, Peripherals, doors, the hatch; `L188.IsFabric` is the building fabric that `Protection.cs` never lets break).
  - **Level !'s gauntlet:** in layout version 6 each lane is packed with set pieces by `PlanRunGauntlet` (`WorldLayout.LevelRun.cs`), every straight kept passable at a sprint; the harness's `runstats` mode checks it and prints the least weaving and jumping a lane takes.
  - **Not finished yet:** Level Fun's Host's hall and its LUCA tears (the Host entity breathes already; its `hostweep` and `hostupset` sounds wait for the hall's alarm), and the lure balloons' AI; the Hub's endless stair, museum pedestals and Camp Amber's wandering. The End's looping aisle and the Turnaround are built but off until tried in a client (`/endloop on`). Not yet tried in a client: Level 3999's walkway carrying, attendants and hold-to-play; Level 188's arm pull over the network, the Peripheral HUD and its sound levels.
- **The seven far places' own files** (levels 14-20, `docs/design/new-levels/CONTRACT.md`): `WorldLayout.Level<Run|Fun|End|Hub|974|3999|188>.cs` (3999's entrances in other levels in `WorldLayout.Level3999.Ways.cs`), `WorldGenerator.<Run|Fun|End|Hub|L974|L3999|L188>.cs`, `ThresholdNetwork.<…>.cs` and `ThresholdSystem.<…>.cs`, `AtmosphereSystem.<…>.cs`, and harness modes in `tools/mapgen/<…>Stats.cs`.
- **`src/BackroomsModSystem.cs`:** world type registration, climate, spawn, the starting waypoint and debug commands.

## The layout harness

`tools/mapgen` is a console program that compiles the game-independent layout code (`WorldLayout*.cs`, `Tiles.cs`, `ThresholdNetwork*.cs`, …) on its own, so layouts can be checked in seconds without starting the game.

- **Build:** `dotnet build tools/mapgen -c Release -o tools/mapgen/out`
- **Run:** `tools/mapgen/out/mapgen <seed> <cells> [mode …]` from any working folder. It writes its output files (`tiles.bin`, `overview.bin`, …) there. With no mode it writes `tiles.bin`, the tiles of a square of `<cells>` macro cells round spawn, which `render.py`, `metrics.py` and `reachmap.py` read.
- **Environment:**
  - `LAYOUT_VERSION=<n>` lays out a world made with that layout version.
  - `FOOD_SCALE=<x>` lays out a world with that scarcity multiplier (0.6 Sparse, 0.33 Scarce; default 1).
  - `SPAWN=<cells>` sets the spawn cell; 16000 is a full-size world.
  - `AT=<mx>,<mz>`, `AT=L<level>` or `AT=S` centres the area on a cell, on a level's first arrival, or on a Snackrooms food court.
- **Checks:**
  - **`layouthash`** hashes every level's layout. Run it before and after any change to world generation: for every layout version but the newest, the output must not change (see *Layout versions* above).
  - `validate` and `validatelevel <n>` check reachability, blocked doorways, elevator pairs and decor facing.
  - `links` goes through every threshold kind and back.
  - `reach` and `path` look for sealed pockets.
- **Maps:** `overview <R> [step]` writes `overview.bin`, the level of every cell within R cells of spawn, and prints how far out each level starts; `render_overview.py overview.bin out.png` draws it (`docs/levels-overview.png` is `mapgen 12345 360 overview`). `region <level> [angle]`, `citymap`, `regionmap 37|94` and the per-level modes have their own `render_*.py`.
- The other modes, such as `stats`, `loot`, `dens`, `gates` and the far places' own (`runstats`, `funstats`, …), print statistics. They're listed in `tools/mapgen/Program.cs`. `report.sh [seed] [cells] [angle] [levels…]` renders the middle of each level's ring and prints its layout metrics.

## Debugging

- **Cheat menu:** press **F7** (rebindable under Controls, "Backrooms: cheat menu") or type `.cheats`. The Travel, Creatures, Events and Player tabs are buttons for the commands below plus `/time` and `/gm`; they go through the server like typed commands, so you need the controlserver privilege, and the replies show in chat. The View tab acts on your client only: a **debug HUD** (level, depth through it, blocks to the next, cell and tile under your feet, Level 0 zone, dens, sanctuaries, stability, temperature), **fog off**, and **reveal map** (maps every loaded column round you). Code in `src/Cheats/`.
- `/backrooms find <elevator|stairs|pit|descent|snackrooms|entryroom> [level]` teleports you beside that feature, in its usual level unless you name one.
- `/backrooms nearest <gate|threshold|cache|refuge|den|redroom|runhall|funparty|endwall|endexit|fronthall|door666|hotelturn|seapillar|shelter|vendingroom|glowcaps|pipecorner|pipewrap|pipeend|neoncorner|downpipe|tent|sleepingbag> [radius]` teleports you to the nearest one in the level you're in (threshold = any non-gate way out; cache = an unopened box or crate; runhall = your Level ! lane's hallway, radius blocks down it from the start room's door, and the heading that looks on down it; funparty = a Level Fun party room with guests, in its north-west corner; endwall = in front of The End's nearest partition wall, and the heading that looks at it; endexit = in front of the central hall's north-west EXIT vestibule; fronthall = a Level 5 front hall, from its axis, and the heading that looks at the desk and the stairs; door666 = across the corridor from a Level 5 door with 666 on its plaque, and the heading that looks at it; both from layout version 5; hotelturn = where Level 4's carpet starts turning to hotel red, and the heading on toward the hotel; seapillar, shelter, vendingroom and glowcaps = a rock pillar on a Level 7 island, a Level 7 camp's furniture-and-tar shelter, a Level 6.1 vending machine room (from the hall in front of its door; use `find snackrooms` first) and glowcaps beside Level 8's road, each from the nearest place to stand with the heading that looks at it, from layout version 5; pipecorner and pipewrap = Levels 2 and 3's wall pipes turning an inner and an outer corner, pipeend = an overhead bundle in Levels 1-3 ending with open space beyond it, neoncorner = a Level 3999 unit's neon base strip turning a corner, downpipe = the head of Level 188's downpipe, each from a few blocks off with the heading that looks at it; tent and sleepingbag = a camp tent, from three blocks out in front of its door, and a sleeping bag, from the nearest place to stand, in any level, from layout version 6).
- `/backrooms home` takes you back to where you wake up; `/backrooms heal` restores health, food, body temperature and stability and resets your time out; `/backrooms kit` gives light, food, a pry bar, chalk, a shiv and Firesalt; `/backrooms light [lantern|torch|candle]` puts a lit light straight into your active hotbar slot (only a light in hand lights Level 6); `/backrooms clear [radius]` removes Backrooms creatures round you (default 64); `/backrooms die` kills you, to test waking up.
- `/backrooms director [on|off]` pauses or resumes the entity director (no new encounters or distant sounds; what is already out stays).
- `/backrooms stat <health|food|stability> <0-1>`, `/backrooms exposure <hours>` (your time out since resting, which raises menace) and `/backrooms noise` (as loud as you can be) set up survival and menace situations.
- `/backrooms column [x z]` (admin) prints the block stack, block entities and light levels of a column, from the ceiling of a grand room down into Level 3's tunnels. If the chunk isn't loaded, it loads it.
- `/backrooms where` names the level and zone you're in, and its stability.
- `/backrooms goto <0-11, 37, 94, !, fun, end, hub, 974, 3999 or 188>` teleports you into a level.
- `/backrooms note read <kind>`, `give`, `status`, `reset`, `probe <reader> x z`, `log`: test the notes sequence and journal.
- `/backrooms shift [hours]` starts a Reality Shift (default 2 in-game hours; 0 ends it).
- `/backrooms menace` shows your danger band and menace value, and the entities around you.
- `/backrooms encounter <entity> [ambient|glimpse|stalk|hunt] [x z [distance]]` puts an entity down for you (any Backrooms entity code; a hunt by default), 14 blocks off unless you give a distance. From the server console, give x and z: it targets a straw dummy put down there and keeps the area loaded, so the AI can be watched without a client.
- `/backrooms flicker` starts a Level 1 Flickering round you (the lights go out and Hounds hunt until they come back); `/backrooms scream` starts the Death Rats' Screaming (the lights fail in Levels 1 and 2 and a pack runs past); `/backrooms mangled` brings the Mangled's cold weather down on you (in the Suburbs, it then comes).
- `/backrooms entitylog [on|off]` logs what the director and the entities decide to the server log.
- `/backrooms dump x z [radius]` (admin) writes the blocks and light of a square of the world to `ModData/backrooms/dump-x-z.bin`, for rendering previews outside the game. Run it twice: the first time loads the chunks.
- `/backrooms ground x z` counts what lies under the foundations of the chunk round x, z (rock, ore and caves, by depth).
- `/endloop [on|off]` (admin) turns The End's looping long aisles, and the Turnaround, on or off.
- `.tfedit` in-game lets you tweak how held and dropped items are positioned.
- **Unattended screenshots:** `tools/shotbot/` is a small client-only helper mod that drives the game from a text file (teleport, aim, hide HUD, wait for chunks, screenshot), so the `docs/screenshots/` gallery can be retaken without anyone at the keyboard. Build it with `dotnet build tools/shotbot`, put the output folder beside the Backrooms build, set `SHOTBOT_DIR`, and launch the client straight into a world: `Vintagestory.exe --dataPath <dir> --addModPath <mods> -o shots -p backrooms` (the world is created if missing). Commands are listed at the top of `ShotBot.cs`; `pick.py` finds camera spots with long, furnished views from the layout harness, and `sheet.py` makes contact sheets.

## Assets

Textures, 3D models, block definitions and sounds are generated by scripts:

- **Block textures must be a multiple of 8 pixels on both sides**, as every vanilla one is. The block atlas is packed edge to edge and mipmapped down to 8-pixel texels, so a single texture off that grid shifts what is packed after it, and far off those blocks' edges shine as a grid (it once did on Level 0's carpet). `gen_textures.save` and the Level 3999 `save` refuse such a texture; `fit_atlas_grid` scales a picture up by a whole number, and `pad_to_atlas_grid` pads it and gives the face UV that shows only the picture.
- Sounds are written through `tools/oggutil.py`, which leaves a sound file alone when it has not changed.

- `tools/gen_textures.py` (needs Pillow)
- `tools/gen_l0_walls.py`: Level 0's arched areas: the arch header model, and the wall block between an arched area and a papered one, pale on one side and yellow on the other. Run it on its own.
- `tools/gen_shapes.py`: block models such as pipes, fixtures, furniture and machinery, built from boxes
- `tools/gen_blocktypes.py`: block definitions for Levels 3–5
- `tools/fire_fx.py`: candle flames, fire, embers, smoke, steam and `HeatSource` for the props that burn. gen_detail.py and gen_blocktypes.py use it, and the particles are copied from vanilla's candle and firepit.
- `tools/gen_sounds.py` (needs numpy and soundfile): hum, flicker crackle, steam, transformer, rain, jazz, waves, and the squelch, scuttle, breath, whisper and chalk effects
- `tools/gen_loop.py`: the survival loop's assets (torn boxes, emptied crates, the moth hive, wanderers' notes, the pry bar, seed packets, and their text).
- `tools/gen_lore.py`: details added to match the lore more closely (Level 2's doors and clutter, cameras, traffic signs, plaques, ceiling fans, Almond Water seeps).
- `tools/gen_guide.py`: the text of the handbook pages, in a light markup, written into the lang file. Its numbers (uses, recipe amounts, where things are found) come from the block types, recipes and code, so update it when those change.
- `tools/gen_detail.py`: the detail props, wall decorations, signs, doors, elevators and floor variants of Levels 1 and 3–5. Each item is defined once (textures in `detail_textures.py`, helpers in `detail_kit.py`) and gets its texture, model, block definition and English name. It also writes `src/Worldgen/DetailBlocks.g.cs`, the table the world generator uses to find the wall decorations. It calls `tools/gen_deep.py` (textures in `deep_textures.py`) for everything in Levels 6 to 10, including the Snackrooms food and the chalk, `tools/gen_city.py` for Level 11, and then `gen_lore.py`, `gen_pool.py`, `gen_motion.py` and `gen_guide.py`.
- `tools/salvage.py`: what breaking each piece of furniture and clutter gives, in one place. It rewrites the drops of the generated block types at the end of gen_detail.py and gen_blocktypes.py.
- `tools/gen_breakdown.py`: rubble, rubble masonry and its recipe, and the words for breaking the building down (`src/Salvage/Breakdown.cs`). Run it on its own.
- `tools/gen_models.py`: the entities' own animated models, built from the lore's descriptions (Smiler, Hound, Skin-Stealer, Duller, Death Rat, Deathmoths, Clump, the Mangled, The Thing), with their textures painted per face. `tools/rig.py` is the small rigging kit it uses: parts as boxes in model space, an automatic texture atlas, keyframed animations (models face -X, left is +Z).
- `tools/gen_entities.py`: runs gen_models.py, then writes the entity types, the Facelings (the game's faceless body with a wardrobe of hair, clothing and accessory boxes, each of 14 looks painting the ones it wears), Firesalt, and their names.
- `tools/gen_entity_sounds.py`: the entities' sounds and the noises heard down the hall (footsteps, scratching, a murmur of voices, a cough, a mimic's "hello?", knocks, a phone, a Smiler's ringing, a Duller's grab...).
- `tools/preview_shapes.py out.png shapes/block/detail/*.json`: renders rough isometric previews of models, to check them without starting the game.
- `tools/check_zfight.py [filters]`: lists z-fighting candidates in the block models: faces of one model in the same plane, facing the same way and overlapping, and faces lying exactly on a neighbouring block's face (an element reaching out of its block). Faces buried inside another element, and undersides on the floor, are left out; what is left still needs judging (a top face against the ceiling never shows).
- `tools/entrender.py shape.json texture.png out.png [anims=walk,idle] [frames=8] [views=side,34,front,back] [scale=70]`: renders an entity model in its animations the way the game composes them, a sheet of frames per animation, to check models and animations without starting the game.
- `tools/lineup.py out.png [yaw=65] [pitch=8] [px=150]`: the mod page's "What lives here" lineup (`docs/screenshots/42-what-lives-here.png`): every creature at its true size (the two giants at half scale), facing the viewer, named underneath. Add a new creature to its `ROSTER`.

- `tools/gen_pool.py` and `tools/gen_motion.py`: Level 37's tile, slits, POOL doors, ladders, Epsom salt and red water; Level 94's turf, roads, backdrop, glass mountain, castle, water towers, fountains, doors, 1950s furniture, milk vans and Almond Milk. Both are run by gen_detail.py.
- `tools/gen_level_sounds.py`: Level 37's drips, lapping, room tone and the Reservoir's chanting; Level 94's siren-pole tune (and its flat dusk version), laughter, "All glory to the King!" and the Robo-Men's wind-up.
- `tools/gen_run.py`, `gen_fun.py`, `gen_end.py`, `gen_hub.py`, `gen_974.py`, `gen_3999.py`, `gen_188.py` (each with its own helper modules): the seven far places' textures, shapes, blocks, items, entities, sounds and names, in their own `<tag>/` folders; run them through `bash tools/locked.sh run python tools/gen_<tag>.py`.
- `tools/gen_notes.py`: every wanderer's note (the tracks, writers, classes, gates and marks), written to lang, `config/notes.json`, the folded note and the loose note block, and `docs/design/notes-catalogue.md`; `--check` validates them, including the facts they rely on against the handbook, the README and the player guide (`docs/GUIDE.md`).
- `tools/texlib.py`: shared texture helpers (tileable veined marble, gradients).
- Every item can be set down on the floor (vanilla's ground storage): the generators give their items the behaviour through `detail_kit.ground_storable` (the layout, the boxes and the `groundStorageTransform`), and the hand-written item types in `itemtypes/` and `itemtypes/salvage/` carry the same by hand. A new item needs it too.

Large surfaces vary from block to block so they do not tile visibly: floors and carpets are turned at random, ceiling tiles come in several versions (one in a while water-stained) and one stretch of wallpaper in three is older and damp-stained. These use Vintage Story's texture `alternates`.

Re-running them overwrites the files, so remove an asset from its script once you replace it by hand.

Known churn when re-running: `gen_detail.py` rewrites `blocktypes/detail/exitlintel.json` and `exitlintelpair.json` with a different key order but the same content. Restore them from git.

The playstyle's name and description must live in `assets/game/lang/worldconfig-en.json`, because the world-creation screen reads them before mod assets load.
