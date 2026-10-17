# Changelog

## Unreleased

- Spanish translation (es-419 and es-es), by NeoB. The handbook pages and other text that changed in 0.513 stay in English until the translation catches up.
- Fixed: breaking a torch (or anything else) you had put down yourself in the Hub's Tower counted as vandalism, and the Keymaster threw you out with nothing and closed the Tower to you for good. Only the Tower's own blocks count now; what you place there is yours to take up again.
- For admins: `/backrooms hub reset [player]` lets a player into the Tower again as if they had never been (the Keymaster offers them a key once more). In singleplayer, type it yourself. For anyone thrown out by the bug above.
- Wanderers' notes are no longer used up when read: the note stays in your pockets and remembers who has read it, so on a server it can be passed on and every player gets the next page in their own sequence from the same paper (one read per player per note; reading one again only says it is in your journal). A read note is named "(read)" to whoever has read it and stacks apart from fresh ones, which stack as before. The pocket note and notes lying loose follow the same rule. Existing notes keep working.
- Fixed: the game's own low-stability look (dark brown fog and a darkened world, which comes on whenever your Reality Stability is low, as after every Reality Shift) was laid over each level's own air and followed you through every elevator, door and stairway, so Level 4's gloom seemed to stay on in Level 5 and fog seemed to come through a door with you. The level's air now always shows; the distortion, whispers and rust still tell you your stability is low. The Mangled's fog lifts as soon as you leave the Suburbs, however you leave.
- Low Reality Stability shows in the air again, now each level's own: below 0.3 the fog of whatever level you are in thickens and turns a dull, dark brown-grey of its own colour, and the world dims by nearly a third, more the lower your stability falls. It fades in and out over a second or so, clears as your stability comes back, and lamps still light the room.
- Fixed: two players together were hunted by twice as much, and more. The director counted what was about each player only among the entities put down for them, so a pair at the edge of a level could have twelve menacing things about them where one player has six; and an entity struck by the other player became theirs, which took it off the first player's count and let the director put down more. The count is now of everything menacing about the place, whoever it was put down for. Playing alone, nothing changes.
- Fixed: a Hound stared at by the other player, a Smiler held in their gaze or a glimpse they watched took no notice: only a stare from the one it was put down for counted. Anyone's does now.
- Fixed: a hunter put down 14 blocks from one player could land right beside the other. Nothing is put down within 12 blocks of anyone now.
- Dev: `/backrooms dummies` has the director direct the straw dummies that `/backrooms encounter` puts down from the console, so what gathers round one or two players can be watched on a headless server.

## 0.513.2 — fixes

- Fixed: looking at a Level Fun party-supply shelf, a Level 3999 neon lamp or a plush crashed the game: the game's own container and orientation code rebuilt their block codes wrongly and asked for a block that does not exist. The shelves also showed missing textures, and the lamps and plushes could not be placed. A dev command, `/backrooms blocksweep`, now asks every block what the block-info HUD asks, so this cannot hide again.
- Fixed: The End's computers never went dead after a party was carried off, and Level 3999's generator never switched on: both looked for their next block by the same wrong name. Existing worlds keep working.

## 0.513.1 — fixes

Two fixes from the first reports on 0.513.0. Existing worlds keep working.

- Fixed: harvesting a Death Rat, Hound or Skin-stealer with a knife gave nothing (the body opened empty). The knife stopped after the client's 2 seconds while the server's copy of the body wanted 5, so the drops were never generated; both sides now take 2 seconds. Bodies that never had anything to give (Facelings, Smilers and the rest) no longer offer to be harvested.
- Fixed: a crash every tick (and a save that would no longer load) while a player stood in Level Fun whose player object was not attached yet, as when joining; the Partygoers' disguise check and the light and moth senses now treat such a player as empty-handed.

## 0.513.0 — first update

Fixes and balance from the first players' feedback, a mapless mode and a harsher scarcity setting. Existing worlds keep working, with the layout they were made with.

- Fixed: scrap wire, circuit boards and coin mechanisms can go in a crucible, as the handbook says.
- Fixed: the ladder down a Level 3 manhole can be climbed, all the way up through the manhole to the street.
- Every item of the mod can be set down on the ground (shift + right-click; ctrl + shift for tools, chalk and plush toys).
- For admins: the cheat menu (F7) is reorganised, with a status line, a Back button, the world settings and a Dev tab of tests.
- *Backrooms scarcity* now reaches all food: a new Scarce setting (about a third of the food); every food and drink in boxes, crates and fridges counts, not just a list; vending machines, water coolers, fountains and Kitty's fridge hold less and restock more slowly on Sparse and Scarce; Level 10 has less livestock; and new worlds on Sparse or Scarce have thinner gardens, fields and berry bushes in Levels 9 and 10 (fixed at world creation). Worlds are now created at layout version 7.
- Flint is a Level 1 find: a sealed supply box holds one about one time in twenty (was two in five), a torn one one in fifty. The glass shiv and the improvised scraper carry you through the Lobby.
- The shiv and the scraper cut wallpaper and carpet cleanly: two strips or fibres a cut, where any other knife, a flint one too, gives one.
- Metal brackets are about half as common from supply boxes, Level 1's crates, ceiling tiles, light fixtures and broken metal and wiring.
- The First Steps tutorial no longer asks for flint in the Lobby: steps 11 to 13 are now the scraper, tinder and a torch, and the last step points to Level 1 for flint. Progress is kept, and anyone who had made the flint knife counts the new steps as done.
- Pottery shards: the potted plants of Levels 4 and 5 break for them. Two shards pounded with a stone make ceramic grit, and two grit and a block of soil make a blue clay: about four plants a clay, a slow way to clay without the trip to Level 3.
- New world setting *Backrooms map* (under Survival challenges), for players who want to feel lost: *Seen areas* (the map as before, the default), *Seen areas, no waypoints* (the map fills in but marks nothing for you) or *None* (no map or minimap at all, and a little more chalk). Without waypoints, notes and the things that marked the map tell you the direction and paces instead.
- Without waypoints, vanilla's "You died here" waypoint is off too; the First Steps note step and The End's computers are worded for it (the way out told, not marked); Kitty's computer and Level 3999's attendants speak before the way is told; and item texts, the handbook and a few notes no longer promise a map mark.
- Furniture and clutter of the later levels give what is in them again, where breaking them used to give the sticks, rubble or brackets of the wall they stand against: Level 188's minibars (juice, Almond Water, crackers), carts, wardrobes and beds; Level 3999's bins, prize cases, lost and found, dead cabinets and ticket piles; Level Fun's cake tins, gifts and carnivorous balloons; The End's desks, card catalogues, shelves and furniture; Kitty's furniture and plush heaps; the Hub's props; wanderers' loose notes. Scarcity scales the food among it too. Level 3999's plush and neon-lamp prizes and rubble masonry come back whole when broken, instead of breaking down like the building.

## 0.512.2019 — first public release

The first release on the Vintage Story mod database. Everything in the [README](README.md) and the [player guide](docs/GUIDE.md) is in it:

- Twenty-two levels: Levels 0 to 11, the Snackrooms, Level 37 (the Poolrooms), Level 94 (Motion), Level !, Level Fun =), The End, The Hub, Level 974 (Kitty's House), Level 3999 (the Neon Paradise) and Level 188 (the Courtyard of Windows).
- More than seventy kinds of threshold between them, each always leading to the same place and saved with the world.
- Scavenger survival on Vintage Story's own systems, with Level 0 as the only place you wake up.
- The Backrooms' creatures, each with its own behaviour and counters, run by a director that keeps them quiet in the heart of a level and dangerous near its edges.
- A map that shows only what you have seen, wanderers' notes and a journal, a handbook rewritten for the Backrooms, and a First Steps tutorial.
- World settings for creature activity (*Backrooms entities*) and resource scarcity (*Backrooms scarcity*).
- A build check that warns in chat when a server and a player have different copies of the mod.

Worlds are created at layout version 6.
