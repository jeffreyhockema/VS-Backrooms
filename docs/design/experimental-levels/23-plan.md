# Level 23 "The Petrified Garden": plan

Internal id **28**, `WorldLayout.Level23`, tag `23`, blocks `l23-`, method infix `L23`, region far south-west beyond
Level 974 (`spawn + (-F, +F)`, see the README). Disconnected: cheats menu / `/backrooms goto 23` only. Reserved: the
L23 column of the README's table (`WallPattern`/`FloorKind`/... 480-511, `Props` 1400-1499, title keys 2801-2899,
salts 0x2800-0x28BF, ports 43170-43179). Lore brief: `lore/23-brief.md`; decisions: `lore/DECISIONS.md` (Wikidot only:
Fandom's Level 23 is an unrelated Vienna; crust-patch plus core-basin reading; Gardener's Sorries as light props).

## 1. What the lore says (Wikidot, "The Petrified Garden", Kitty Rika and Beep Bot)

https://backrooms-wiki.wikidot.com/level-23, difficulty "4?", Unsafe, Overgrown, Medium Entity Count. A planetoid-sized
superorganism of intertwined trees (Ceres-sized, Earth gravity), with pockets of air and winding tunnels inside its
surface like a cave system. The surface is an extremely dense forest letting little to no light through; no day/night;
a star that never moves; species from Douglas fir and redwood to extinct and unknown ones. **Glow rooms** below: big
caverns like underground forests, lit by **Gardener's Sorries** (glowworm-like, many colours, always whispering
"sorry"), glowing fungi and bushes, damp and cool, the most entities. **Ancient ruins** deep in glow rooms, mossed: a
pyramidal Lighthouse of Alexandria, a spherical Great Pyramid, a square Colosseum, a triangular Parthenon; pottery,
damaged paintings, cloth; hasty Latin; the plaque at the Great Sphere (quoted in the block's description). **Buried
sentries** trapped in wood and bark scream like rusty chainsaws when someone says "it's only a matter of time". The
**Heart of Water**: the hollow core under a spherical ceiling held up by the **Green Giants** (do not tamper), a huge
reservoir feeding the level. **Base Seedling** (M.E.G.): a glow room, ~30 members, trades, Almond Water squirt guns,
cleared of sentries, limited food, steady water, guards the only consistent exit (a hollow tree to Level 135).
Entities: Volpes, Hounds, Clumps, Smilers, Death Rats, Deathmoths, Curabitur Birds, natives, rare Wranglers. Ways in:
hollow green-barked trees in Levels 37 and 47, a hollow tree in 135, a hollow log in 121; out: the reservoir (to the
ocean of Level 7 or 121, or an exhibit in 43), the hollow tree at Seedling (to 135).

## 2. The level in this mod (the scale reading)

A planet cannot be modelled: the region is a patch of the planet's crust. Its open sky is the canopy lid, the walkable
layer is the forest floor and root maze, the glow rooms are caverns carved under it, and the Heart of Water is a basin
in the middle of the patch. Everything is a pure function of the block position and the seed
(`WorldLayout.Level23.cs`), shared by the layout, the generator (`WorldGenerator.L23.cs`) and the client's air
(`AtmosphereSystem.L23.cs`).

**Heights.** `L23Drop = 10`: the level's floor is ten below the shared floor, so the world's top lies 48 above it. The
band is lit from 20 below the floor (`L23BandDepth = 20`, the usual 40 tall: rel -20..+20) and its columns are built on
up to the top of the world (one line in `WorldGenerator.Band`, Level 23 only). Ground rel 0-3, glow rooms -14 (floor)
to -3 (roof), ruins -18 to about -3, the lid from 33-41 to 48.

## 3. Detail pass (2026-10-30)

**Built.**
- *Region.* Round, a fixed 13 cells (416 blocks) whatever the world's size; the forest is the disc 320 blocks round the
  Heart of Water (jittered 12 blocks from the region's centre) with an Fbm wander of 20; beyond it, and in every cell at
  the region's edge, the **tangle**: fused roots and dark bark to the lid (`l23-tangle`, `l23-bark-dark`, `l23-root`).
- *The forest floor.* Humus in humps (0-3) with root ridges along the zero line of a noise; moss in patches, leaf litter in
  drifts; under it dark earth, then earth and roots mixed with tangle down to the band's bottom.
- *Trunks* on a jittered 15-block lattice (11% clearings): radius 2-6 (6% 6.5-7.5), so 4-14 wide; bark grey 45%,
  redwood red 20%, pale oak 20%, dark cypress 15%; they lean and twist as they climb; buttress fins (3-5 lobes) and a
  swollen foot over the first few blocks; 10% are broken snags 10-24 high; the rest go up through the lid. Each has 3-4
  roots crawling out over the ground (a one-block step), 2-3 limbs rising into the lid; 30% of neighbouring pairs are
  joined by a **root arch** high enough in its middle (3-6 clear) to walk under. Gaps between trunks are mostly 3-8.
- *The lid.* Dense leaves (`l23-leaves-dense`, light absorption 2) from rel 41 to 48, so the sun reaches the forest floor
  at about 6 of 24 (a headless dump: 6 on most columns, 3-5 in the shade of roots, up to 22 under the holes); a loose underside of `l23-leaves` (absorption 0)
  hanging down to 33-41 in lumps; lichen strands hang from it. **Holes**: on a 48-block lattice, 45% of points, radius
  2.2-4.5: full sunlight in a shaft, grass, ferns and a few daisies under it. Over the pool a hole of radius 7.
- *Glow rooms.* On a 72-block lattice, 70% of points (none near the Heart of Water, Base Seedling or the ruins; 20 in the
  seed-12345 world, merging where two meet): a dome, radius 18-32 (36-64 across) with a wandering edge, floor -14 rising to the edge, roof -3 sinking to it. Moss and earth floors with
  puddles, pillars where a trunk comes down through (55% of trunks), **little petrified trees** (a 7-block lattice, 45%,
  2-4 high, a crown of leaves), glowcaps of the room's colour in patches (`l23-glowcap-*`, light 7), vanilla mushrooms
  (mostly edible, a few fly agarics and earthballs) and ferns; **Gardener's Sorries** (`l23-sorry-*`, light 11, teal,
  violet, amber or green) on 2.4% of the roof, lichen and hanging roots. Two **root tunnels** each (three for the special
  caverns), from near the edge at the floor up to the forest floor 26 blocks out, 3-5 wide, 4 high, lined with roots,
  turned until their mouth is clear of trunks; they cut through any trunk in their way (an archway).
- *The ruins* (four caverns 228 blocks from the middle, 90 degrees apart, radius 34, floor -18, roof up to -3; plaza of
  mossy pale limestone within 17): the **Lighthouse** as a stepped pyramid nine high with a lamp on top (an ember until round 2) and a
  passage into a chamber at its heart; the **Great Pyramid** as a hollow sphere 13 across, door south, the **bronze
  plaque** beside it (its description is the lore's translation); the **Colosseum** square (two arcaded walls, two tiers,
  a corridor between, a sanded arena, a stretch fallen in); the **Parthenon** on a triangle (stepped platform, colonnade
  round three sides, a cella with a south door, roof partly fallen). Stones fall out of them (3.5%), moss creeps up them;
  **Latin** inscribed stones (`l23-latin-a..d`) in their walls; **pottery** (`l23-pottery-amphora/-shards`) on the plaza
  and in the rooms; more supply boxes than a glow room.
- *Base Seedling* (165 blocks from the middle; radius 30, flat floor -12): the **hollow tree** of green bark (a ring with a
  door south, its hollow going up dark into the ground), three M.E.G. **tents** (`Props.CampTent`) facing it, eight vanilla
  lanterns, a table, a spring, five supply boxes (the stores), and the M.E.G.'s **quartermaster**, a wanderer of the
  "camp" site (`L23WandererSite`, one line in `WorldLayout.WandererSite`). Safe band and a sanctuary (`IsSanctuary`).
- *The Heart of Water.* A clearing of radius 54 ringed by seven **Green Giants** (radius 7-8, green mossy bark, wide
  buttresses, through the lid), the ground falling to a shore at -6 and a pool (radius 26, surface -7, bed to -14) under
  the radius-7 hole; the lid over the clearing hangs no lumps (a high vault); long roots hang from it.
- *Buried sentries.* 11% of trunks of radius 3+ have a face (`l23-sentry-<side>`) between two buttresses at head height.
  **The phrase**: `src/Regions/L23Sentries.cs` (a server ModSystem of the level's own) reads chat: "only a matter of time"
  said in the level within 12 blocks of a sentry makes them scream (`sounds/ambient/23/sentryscream`, heard 96 blocks
  off) and gives everyone within 10 blocks a blow of 3 and a line about their ears.
- *Water.* All of the level's water counts as clean (`WaterClass`, one arm): the reservoir feeds the whole level.
- *Air* (client): forest fog dim green (0.014; 0.10, 0.15, 0.08), a ground mist, scene 0.75, no day or night; the sky
  hidden in a sphere of pale gold-green so the holes show only glare. Glow rooms take their Sorries' colour (teal,
  violet, amber; 0.016, scene 0.85); tunnels close and brown; Base Seedling warm; ruins grey-green; the Heart of Water
  the clearest (0.007, scene 0.9). Titles: "The Heart of Water" (2801), "Base Seedling" (2802), "Ruins of the Architects"
  (2803). Temperature 17 C (forest), 12 C (glow rooms, tunnels, ruins), 15 C (Seedling), 14 C (the Heart). Stability
  0.93, 0.86 in the ruins, 0.97 at the Heart, 1 at Seedling.
- *Sound bed.* Vanilla `wind-leafy` low overhead (the lid), Level 974's creaks, a synthesised wood groan, a sentry's
  scream far off every 2.5-5.5 minutes; below ground drips and the Sorries whispering "sorry" (three synthesised takes,
  `tools/gen_23_sounds.py`: noise through moving formants); at Seedling murmured talk; at the pool vanilla `creek`.
- *Dangers* (the director): Danger 0.55, survival class 4 (Wikidot's "4?": two kinds at once, scarcity of class 4),
  solitude 0.9. Bands: forest Heartland, glow rooms and tunnels Approach, ruins Threshold, Seedling Safe. Roster: Death
  Rats (heart, 2-3), male Deathmoths (heart, glimpses), Hounds (approach, 1-2), Smilers (approach, in the dark), Clumps
  (approach, ambush), female Deathmoths (edge, 2-4). Distant sounds: howls, scuttles, wings, groans, drips, whispers.
- *Loot.* Supply boxes at the foot of a tree in one cell in seven, at the edges of glow rooms (0.16% of their tiles),
  among the ruins (0.4%), five at Seedling; 30% picked over. Bark gives a little firewood, roots and tangle sticks, the
  ground soil; amphorae a scrap of cloth and red clay; mushrooms to forage.
- *Content.* Six wanderer notes (`gen_notes.py` track `l23`, one block for the level): leaves and holes (anon), the
  Sorries (Tom), the sentries (Dez), the four ruins (A.L.), Base Seedling (M.E.G.), the Heart (Nell). A handbook page
  "Level 23: The Petrified Garden" (`gen_guide.py` `PAGES["level23"]`, added to `GuideSystem.Added`). Block names and
  descriptions, title and hint lines (`tools/gen_23.py`, which writes the level's whole lang block).
- *Assets* (`tools/gen_23.py`, matlib): 22 blocktypes: five barks (sides: furrowed petrified bark, two alternates; ends:
  grey rings), root, tangle, humus, moss, litter, earth, rooted earth, leaves (three greens), dense leaves, ruin stone,
  mossy ruin stone, inscribed stones (four texts), plaque, sentry (four sides), glowcaps (three colours, json model of
  four mushrooms), Sorries (four colours, json model of hanging strands with glowing beads), pottery (amphora, shards).
- *Harness:* `23stats` and `23map` in `tools/mapgen/L23Stats.cs`. Map layer: Level 23 has its own case (each column on its
  ground; underground, the floor the player stands on). `/backrooms dump` reaches the top of the world in Level 23.

**Choices against the brief.**
- The lid reaches the top of the world (48 above the forest floor, the brief's ~+50) through a ten-block drop and the
  band built on above its lit part, rather than a taller band.
- The tunnels cut straight through any trunk in their way (archways) rather than steering round them.
- Surface light: sky light about 6 under the lid (as the brief asks), with the fog and a scene of 0.75 over it; to be
  judged in a client.
- No "exotic flora set pieces", falling leaves or spores, branch walkways (the limbs are not walkable paths), damaged
  paintings, cloth props or the squirt-gun prop. Volpes, Curabitur Birds, Wranglers and the natives are left for later
  (the handbook says so).

**My own inventions** (not in the lore): the specific shapes of everything (trunk lattice, arches, the lid's holes,
caverns as domes, little trees in the glow rooms); the four bark kinds; glowcaps' and Sorries' colours as lights; the
puddles; the tangle as the region's edge; the Latin texts (HORTVS SACER, VENIAM PETIMVS, OCVLI VIRIDES, NON DELEMVR);
the ruins' floor plans; pottery dropping cloth and clay; bark dropping firewood; the edible mushrooms (the lore names no
food); the sentry's damage (3) and reach; Seedling's quartermaster as a vanilla-trading wanderer of the "camp" site, its
three tents, lanterns, spring and stores; the water counting as clean everywhere; the sound bed's details; the six notes'
texts; the title keys' hints.

**What to check in-game (screenshots).**
1. The forest floor under the lid: is it dim green but readable (sky light about 8, scene 0.75)? Are the trunks'
   barks, buttresses, roots and arches convincing; is it dense enough? A shaft of light under a hole.
2. Looking up: the lid's underside (loose leaves, lichen), limbs going into it; the glare through a hole (the sky sphere).
3. A glow room: colour, Sorries' models and light, glowcaps, little trees, pillars, puddles; a tunnel mouth.
4. Each ruin from its plaza (Lighthouse, Sphere with the plaque, Colosseum, Parthenon); the inscriptions' legibility.
5. Base Seedling: hollow tree, tents, lanterns; the quartermaster (appears when a player comes within 20-72 blocks in
   the cavern).
6. The Heart of Water: the Green Giants, the basin and pool under the shaft, the vault.
7. The tangle at the edge.

**Checks (2026-10-31).** `expclash.py` clean. Mod and mapgen build with 0 errors. `layouthash` (seed 12345, 16000;
layout versions 1 and 12): every line for levels 0-20 and the `layout hash` line identical to main's (only the far places
hash moves). `regions`: Level 23 60/60 arrivals, none in the wrong level or in small pockets, at full size and at 1000.
`23stats` (seed 12345): 505 cells, 5.5 ms a cell; tiles forest 51.8%, glow rooms 5.3%, tunnels 1.0%, Seedling 0.3%,
ruins 2.4%, Heart 1.8%, tangle 37.4%; trunks and roots stand in 33% of the forest's tiles; 91 supply boxes, 12 tent
tiles; 25 caverns (20 glow rooms), 55 tunnels, no mouth in a wall. Headless (port 43170): `/backrooms dummy place 23`
lands with 0 error lines (light 6 under the lid, 12 near a hole); `blocksweep` 0 threw; `/backrooms encounter hound|deathrat
hunt` against a dummy puts them down; dumps of a glow room (37 Sorries, 33 glowcaps, puddles, a tunnel), Base Seedling
(hollow tree, 3 whole tents, 8 lanterns, table, spring, 5 boxes), the Lighthouse and the Sphere, and the Heart of Water
(7 Green Giants, the pool) show everything as planned. `GATE_TAG=l23 gate.py --fast --port-base 43170`: pass.
Not tested: anything on a client (the air, the sky sphere, the sounds, the models' looks), the sentry phrase (needs a
player's chat), the quartermaster's appearance (needs a player near Seedling).

### Round 2 (2026-10-31): looking at it in the client

The lead's first look (`round1-23`) was murky to the point of unreadable: a thick dark-green fog, everything near-black
green, every trunk the same wavy bark, and none of the set pieces in view. What changed:

- *Showcase spots* (`WorldLayout.Level23.Showcase.cs`, all from the layout): the Heart of Water with a Green Giant, a long
  view through the forest, a light shaft (the nearest good hole with an open way to it), a buried sentry's face, a glow
  room of each colour (a Hound put down in the amber one), Base Seedling from inside one of its tunnels (so the
  quartermaster is put down out of sight) and then the camp, the four ruins from the south of their plazas, and the
  tangle at the edge. The layout gained `L23HoleAt` and `L23LittleTreeAt` (the generator's lattices, unchanged) for them.
- *Air*: the forest's fog thinned (0.014 to 0.0065) and paled to the grey-green of the light through the lid, scene 0.75
  to 0.95; the ground fog nearly gone (it thickens with depth below its surface, so it closed in the basin and the
  caverns entirely: none there now). Glow rooms: their colour kept but darkened and thinned (0.016 to 0.007), so the
  Sorries and glowcaps light the room rather than a coloured murk; ruins, tunnels, Seedling and the Heart thinner too.
- *The lid*: its dense leaves start at 41 to 44 by a broad noise (`L23DenseFrom`) instead of 41 everywhere, so the forest
  floor has pools of about 8 to 12 of the sun's light and deeper dark between, besides the shafts under the holes.
- *Light shafts*: motes of dust and pollen drift down through the sunlight under the nearest holes (client particles,
  faintly self-lit), so a shaft reads through the green air as a pale column (my invention, from the brief's "nice"
  falling spores). In the glow rooms, a few motes of the Sorries' light drift about in the room's colour.
- *Bark*: each kind its own grain (`tools/gen_23.py`): grey deep straight furrows (a fir's), redwood long fibres and
  narrow furrows, pale oak blocky plates with wandering cracks, cypress thin strips twisting up the trunk; the Green
  Giants keep the wavy mossy grain. Each bark's alternate has a ragged patch of lichen or moss, so trunks are patched.
- *Silhouettes* (`L23TrunkAt`, `L23InTrunk`): 14% of trees thin (2-3 wide), the rest oval (up to 22%), narrowing toward
  the lid by 10-40%, a third swelling and pinching as they climb, a quarter of the thick ones forked into two stems at
  13-22 up. (The level's layout moves; Levels 0-20 do not.)
- *Ruins*: nearly black before; now more Sorries over them (4.5% of the roof against 2.4%), the glow room's own floor
  (glowcaps, mushrooms, ferns) round the plazas, glowcaps of the room's colour coming up through the moss on the paving
  (the lore's "overgrown with moss and fungi"; without a torch the plazas were black), and a lantern on the Lighthouse's
  top where an ember gave no light (my invention: a lamp still burning).
- *Base Seedling's tunnels*: the M.E.G. keep a lantern by the wall now and then on the ways down to the camp (my
  invention; the tunnels were pitch black without a torch).
- *Arrivals* face the most open way of the eight round them (up to 32 blocks of forest floor), not the trunk beside them
  (`ThresholdSystem.L23.cs`).

**What the shots showed** (`%TEMP%/backrooms-shots/`: `23-r2a-torch` first, `23-r2b-torch` and `23-r2c-notorch` after
the air, `23-r2d-notorch` after the ruins' glowcaps, final `23-r2e-torch-final`): the forest reads as a forest (trunks one
behind another in different barks and shapes, roots, arches, ferns, the shafts' glare), dim green but legible without a
torch, as the lore wants; the glow rooms are the best of it (each colour's light, Sorries, glowcaps, little trees,
pillars); the four ruins read from their plazas with or without a torch, the plaque and the Latin legible at the
Sphere; Base Seedling shows its hollow tree, tents, lanterns, stores, spring and the quartermaster standing at the
tree's door. Still weak: with the rig's short view distance the edge of the loaded world shows the pale glare of the sky
sphere through gaps (seen across the Heart of Water's clearing, whose air is the thinnest); the little trees' crowns are
plain cubes; the Hound brought into the amber glow room was put down out of view; the light shaft's motes barely show in
a still frame.

## 4. Links (2026-10-31)

LINKS.md's Level 23 section, built. Code: `WorldLayout.Level23.Links.cs` (layout: the trees in Level 37 through
`L23Entrances`, the hollow trunks, the well, the arrival finders), `WorldGenerator.L23.Links.cs` (the trees' blocks through
`L23EntranceBlock`), `ThresholdNetwork.L23.cs` (the thresholds), `ThresholdSystem.L23.cs` and `Regions/L23System.cs` (the
dev test `/backrooms l23walk x z [rel]`), `tools/mapgen/L23Stats.cs` (`23links`), showcase spots `link-*`. Unders
480-489 (`Unders.L23Pool*`, `L23SeedlingHollow/Door`, `L23HollowTrunk`, `L23Well`); layout salts 0x2860-0x2862, generator
0x2864-0x2865, threshold salts 0x28C0-0x28C3.

**Built.**
- *In, from Level 37 (one-way).* A huge hollow tree of green bark (the Green Giants' `l23-bark-green`) growing up through the
  Poolrooms' tiles: a ring of bark 7-9 blocks across (radius 3.6-4.4) through floor and ceiling, a dry hollow 5 across
  (humus and leaf litter on bark) going up into the dark three blocks past the room's ceiling, a mouth three wide and three
  high facing the most open way, and round its foot three roots crawling out over the tile and the tile broken into earth
  and moss (the ceiling round the trunk broken by roots too); the way out of the mouth is left clear. At most one to a
  square of 16 x 16 plan blocks (1536 blocks a side), in three squares of five, in the middle half of the square each way,
  in a plan block's floor with the most room round it (dry or a step deep, ceiling 6 or more, in the light where it can be),
  never in the Sanguine Reservoir or a cell at the edge. Climbing into the hollow (any of its tiles, at the water's level)
  takes you up through the dark and out of a hollow trunk in the forest, beside its mouth (chosen by key among them).
- *Where they come out.* Hollow trunks in the forest: one of the thick trunks (radius 3.4+, whole, unforked, no sentry) in
  twelve is hollowed out from its foot to nine up (bark 1.3 thick), with a mouth between two buttresses three high; its
  roots leave the hollow and the way out open. Seed 12345: 21 of them on the forest floor.
- *Base Seedling's hollow tree (two-way, our substitution for Level 135).* Climbing up into its hollow (the doorway and the
  hollow are one threshold) comes out beside the mouth of the Poolrooms tree nearest the Poolrooms' middle, and that one
  tree (its own Unders) leads back to the camp, in front of the doorway; every other tree is one-way into the forest.
- *Out, the Heart of Water (one-way).* In the middle of the pool's bed a well (radius 3.5) goes on down to 19 below the
  level's floor, its floor dark root tangle, under the light from the lid's one wide hole; at the bottom (within two of it)
  the reservoir takes you and you come up swimming in Level 7's open sea (water at least 8 deep, no entry room, nothing
  afloat).
- *Text.* Messages `l23-tree-in`, `l23-tree-camp`, `l23-tree-home`, `l23-well`; the handbook page's "Ways in and out"
  (rumours: Level 47's trees, Level 121's log and ocean, Level 43's exhibit); the M.E.G. notice (l23-5) says where the
  camp's tree comes out; a new note in the level (l23-7, Dez, the tree in the water) and one in Level 37's own track
  (l23-p1, A.L.: green bark through the tile, nobody comes back out of it).

**Numbers (seed 12345, full size, `23links`).** In the inner two fifths of the Poolrooms (where people arrive): 65 trees
in 340 km2, one per 5.2 km2; nearest neighbour 965 blocks at least, median 1443, most 3050. The nearest to spawn are on
the Poolrooms' near edge, 102.8 km out (409301,517261). Base Seedling's tree: 384527,511276, 899 blocks from the
Poolrooms' middle. Every arrival finder found its place for 20 keys of 20 (beside a hollow trunk's mouth, at the camp's
door, in Level 7's open sea, beside Seedling's tree in 37). No placard: Level 37's own ways have none.

**My inventions.** Every shape and number above (the tree's size, roots, broken tile and ceiling, the dry hollow, where in
a plan block it stands, the rarity); the hollow trunks the way in comes out of (the lore says only "you climb out of a
hollow trunk"); the well at the bottom of the pool as the reservoir's way down; the camp's tree coming out at the tree
nearest the Poolrooms' middle (LINKS.md: "a Poolrooms tree"); the texts.

**Fixed on the way.** Round 2's tree silhouettes read their extra hash bits from the low end (`Hashing.Unit(h >> 20)` is
always nearly 0): every thick trunk forked, all along the same line, every trunk swelled, all leaned the least, and the
thin trees were all 1.2 across. Now as the plan says (a quarter forked, each its own way; a third swelling; leans 0.6-1.6).
The level's own layout moved; levels 0-20 did not.

**Rows for the guide's ways-between-levels table.**

| From | Threshold | To | Way back |
|---|---|---|---|
| Level 37 | Climbing into the hollow of a huge green-barked tree growing up through the tile (kilometres apart) | Level 23, out of a hollow trunk in the forest | None |
| Level 37 | Climbing into the hollow of the green-barked tree nearest the Poolrooms' middle | Level 23, Base Seedling, in front of its hollow tree | That tree |
| Level 23 | Climbing up into Base Seedling's hollow tree (the lore's way to Level 135) | Level 37, beside the green-barked tree nearest the Poolrooms' middle | That tree |
| Level 23 | Diving to the bottom of the well in the middle of the Heart of Water's pool | Level 7, swimming in the open sea | None |

**Checks (2026-10-31).** `expclash.py` clean; mod and mapgen build, 0 errors. `layouthash` (seed 12345, 16000; layout 1 and
12), with and without `BACKROOMS_NO_EXP_ENTRANCES=1`: every line for levels 0-20 and the `layout hash` line identical to
main's (no level line moved: the sample of Level 37 holds no tree). `regions`: Level 23 60/60. `23stats` ok, `23links` ok.
Headless (port 43172, `/backrooms l23walk`): each way gone through twice (first time and as written down): a tree in 37
comes out beside a hollow trunk on the forest floor (air at feet and head); Base Seedling's tree comes out in the water
beside Seedling's tree in 37 and that tree leads back to the camp's doorway (each the other's way back); the well comes
out swimming in Level 7's sea; 0 error lines. `GATE_TAG=l23 gate.py --fast --port-base 43170`: PASS.
Shots (`%TEMP%/backrooms-shots/23-links-a`, `link-*`): the trees in 37 read as huge green trunks through the tile with a
dark hollow and a mouth; the hollow trunk in the forest read as one, but its floor showed the bark's cut end (now leaf
litter and humus, not reshot); the well is hard to see from the shore under the dark water.

## 5. Round 3 (2026-11-01): the detailed visual pass

The user asked for more detailed visuals, multi-block objects and signs where a real place would have them, more
realistic layouts, and closer alignment with the lore and the released levels. The lead's notes on round 2's final sheet:
the ruins and glow rooms read well; the forest floor and the random arrivals are murky and close to trunks; the forest
floor wants variety (fallen stone logs, stone mushrooms, root flares, boulders, petrified undergrowth, leaf litter, light
shafts as landmarks, trunks of several girths and barks, the canopy from below); the Heart of Water spot shows no water;
Base Seedling wants its sign, a notice board, a quartermaster's table, a water barrel, bedrolls and a path of flat stones;
more sights in the vein of the sentry's face; arrivals facing open space.

### List

Tiers: A must, B should, C nice. Inventions are marked (inv.).

**1. Layout realism**
1. [A] [done: by a glade, 5x5 open and 7 out each way] Arrivals in the open: a surface tile is an arrival spot only with open forest floor all round it (a 9 x 9 square
   free of trunks and roots), so whichever way a player (or the rig's fixed headings) looks there is forest to see, not bark.
2. [A] [done] Glades: some holes in the lid much wider (radius 6-9), with a sunlit glade under them (grass, flowers, young
   saplings, no trunks inside), landmarks seen from afar as pale columns of light. (inv.: their size and planting)
3. [B] [partly: flagstone path, counter by the door, barrels at the spring, fire ring; the tents stay where round 1 put them] Base Seedling laid out as a working camp: the hollow tree in the middle, the tents in a row on one side with
   bedrolls, the quartermaster's counter by the main tunnel's foot, the water barrels at the spring, a fire ring with
   seats as the camp's middle, a path of flat stones from the main tunnel to the tree.
4. [B] [done] A worn trail from Base Seedling's tunnel mouths out over the forest floor (trodden earth and litter where the
   ground is open), so the camp's ways read as used. (inv.)
5. [C] [skipped: the trails and way-signs carry it] The M.E.G.'s way-marks: blazes on the trunks along those trails. (inv.)

**2. Multi-block objects**
6. [A] [done] Fallen petrified logs across the forest floor: trunks lying on their side (1-2 high, 7-18 long) with their ring
   ends showing, some broken in two, moss on their tops; the low ones a step to climb over, the thick ones to go round.
7. [A] [done: forest, and one glow-room little tree in four] Stone mushrooms: giant petrified mushrooms (a stem 1-2 across, a cap 3-7 across and 3-7 up, gills under it),
   alone or in clusters, in the forest and the glow rooms. (inv.: the lore has glowing fungi; these are the petrified kind)
8. [A] [done] Boulders: lumps of mossy stone and broken petrified wood, 2-4 across, half sunk in the humus.
9. [A] [done] Petrified undergrowth in several shapes (models): a stone shrub, a stone sapling with bare twigs, stone fern
   fronds, a broken stump; in patches at the trees' feet and along the logs.
10. [B] [done] Bracket fungi on the trunks: shelves of pale stone fungus stepping up a trunk's side (a few stacked).
11. [A] [done] Base Seedling's things: the camp sign on two posts, a notice board, the quartermaster's counter (tables, crates
   stacked behind, a ledger), water barrels, bedrolls by the tents, a fire ring with log seats, a path of flat stones.
12. [B] [done: the body; hands are in its texture] Sentries as people trapped in the bark: under some faces a body pushed out of the bark (shoulders, arms, hands
   reaching), so a sentry reads as a person and not a mask. (the lore's "trapped in wood and bark")
13. [B] [done] Cypress knees: little conical stumps standing round the dark cypress trunks' feet.
14. [C] [done: a quarter are stone mushrooms; the rest rounder, a layer above and below] Rounder crowns for the glow rooms' little trees (no plain cubes).
15. [C] [done: one forest cell in twenty, bedroll, crate, bones] A lost wanderer's camp in the forest: a bedroll, a dead lantern, a crate, bones. (inv.)

**3. Signs and text**
16. [A] [done] "BASE SEEDLING" on the camp's sign, with the M.E.G.'s name, facing the way in.
17. [A] [done] The M.E.G.'s notice board at Seedling: the camp's rules (do not say it; water free, food by ration; the tree is
   the way out; report sentries), legible from in front of it.
18. [B] [done] Way-signs at the surface mouths of Base Seedling's tunnels: "BASE SEEDLING" and an arrow down. (inv.)
19. [B] [done] A warning plate at the Heart of Water: the Green Giants are not to be tampered with (the lore's warning), from the M.E.G.
20. [B] [done: WATER on the barrels, M.E.G. on the crates] Stencils: "DRINKING WATER" on the camp's barrels, "M.E.G." on its crates.
21. [C] [done: inscribed stones in the tunnels' walls, not bark] Hasty Latin scratched into the bark of the tunnels down to the ruins (the lore's "hasty messages in Latin").
22. [C] [done] A plank nailed by a sentry or two, painted "DON'T SAY IT". (inv.)

**4. Detail visuals**
23. [A] [done] Aspen: a fifth bark, white with black eyes (the lore lists aspen), and a wider spread of girths (more thin
   young trunks, a few very thick).
24. [B] [done: the red-brown alternate; twigs were there] Leaf-litter variety: a second, red-brown litter in drifts against roots and logs; twigs.
25. [B] [done] Moss collars: moss creeping up the trunks' feet and over the roots.
26. [B] [partly: more and lower limbs; the underside's tints unchanged] The canopy from below: limbs fanning out under the lid, the lid's underside in two tints, more lichen.
27. [B] [done] The forest's air a little less murky at eye level so the depth of trunks reads (fog paler and thinner, the dim kept).
28. [A] [done] The Heart of Water's showcase spot shows the reservoir (from the shore, looking down across the pool under its shaft).
29. [C] [partly: stones in the shallows] The pool's shore: root islands and stepping stones at its edge; long roots dipping into the water.

**5. Lore alignment**
30. [B] [done] Glowing bushes in the glow rooms (the lore's "glowing fungi and bushes").
31. [B] [done] The ruins' finds: damaged paintings (faded frescoes on the inner walls) and cloth (rags) besides the pottery.
32. [C] [done: a long root from roof to floor now and then, a pool at its foot] The vault's pipes: roots hanging into the glow rooms with water at their foot (the lore's trees that pipe water down).
33. [C] [done: a rack of three on the counter's crates] Almond Water squirt guns on a rack at the quartermaster's (the lore's arms of Seedling).

**6. Released-level alignment**
34. [A] [done] Every new block named in the HUD and creative tab (lang), sensible drops (logs and stumps firewood, boulders
   stone, the camp's things nothing), pick-block as the released levels.
35. [A] [done] Showcase spots for the new set pieces (a fallen log, stone mushrooms, a glade, the camp's sign and board, the
   Heart's warning plate), all from the layout.
36. [B] [done] The handbook page and a note mention the new sights where they matter (the camp's rules board, the logs).
37. [B] [done] Balance notes for the lead: anything that is food, water or shelter (the camp's barrels are only looks).
38. [C] [skipped: time] A trickle in the sound bed near the glades' and the pool's water.
39. [B] [done] (The lead, from the balance review) Base Seedling's lanterns (the camp's, its tunnels', the Lighthouse's lamp) a
    block of the level's own that gives the same light and breaks to nothing, not vanilla lanterns to pick up.

### What was built

- *The forest floor* (`WorldLayout.Level23.Features.cs`): a lattice of its own (13 blocks) between the trees, each point
  clear of trunks, hollow trunks' ways, tunnels, the Heart of Water and the tangle: **fallen logs** (24%; along x or z,
  7-18 long, one block, two by two, or three across with the top corners off; their own blocks `l23-log-<bark>-<axis>`
  with the bark along their length and the rings at their ends; a third broken in two; half of the thick ones with the
  **root plate** they tore up standing at one end), **stone mushrooms** (13%; one to three, stem and cap `l23-mushstem`,
  `l23-mushcap` with gills under; 3-7 high, caps 3-7 across, the big ones a second layer) and **boulders** (15%;
  `l23-boulder`, mossy, half sunk). They are drawn into `L23Wood` like the trees, so the layout's walls and the blocks
  agree; a one-high log or boulder is a step (`L23Steppable`). Trees and floor features are cached per lattice point
  (the regions harness went from 13 s to 4 s for Level 23's 60 arrivals).
- *Trees*: **aspen** (`l23-bark-aspen`, white with black eyes) among the thinner trunks; **cypress knees** round the dark
  cypresses; **moss** grown up over the trunks' feet in a band one or two high and over the roots' tops
  (`l23-mossbark`); **bracket fungi** of stone stepping up one tree in three (`l23-bracket-<side>`); three to five limbs
  fanning out under the lid from 17 up (was two or three from 20).
- *Glades*: one hole in five on the lid's lattice is 6-9 wide; no trunk stands in it; grass and five kinds of flowers,
  ferns and stone saplings under it; a paler, clearer air when standing in one.
- *Undergrowth of stone* (`l23-stoneplant-*`: shrub, sapling, fern fronds, stump) in patches of its own; a second, red-brown
  leaf litter as the litter block's alternate.
- *Arrivals*: aimed at the glade nearest the old random point and put down on a tile with a five by five square of open
  floor round it and open floor seven out along each of the four ways (`L23MarkOpen`, `Tile.Detail` = `L23OpenGround`).
- *Base Seedling*: a path of flagstones from the south up to the hollow tree's door; the camp's sign (BASE SEEDLING,
  M.E.G. outpost 23-1, three boards on two posts) and the notice board (camp rules, a missing-person notice, a map scrap)
  facing the way the camp is seen from; the quartermaster's counter (three tables, his ledger, crates stencilled M.E.G.
  behind it, a rack of Almond Water squirt guns on the last); water barrels stencilled WATER by the spring; a fire ring
  with glowing embers and two log seats; six bedrolls by the tents. The M.E.G.'s **trails** run out forty blocks from each
  of its tunnels' mouths as trodden earth, and a **way-sign** (BASE SEEDLING and an arrow) stands beside each mouth.
- *The lead's balance item*: every lantern of the level (the camp's, its tunnels', the lamp on the Lighthouse) is now
  `l23-lantern`, a model of the level's own with the same light that breaks to nothing.
- *Sentries*: under each face its body (`l23-sentrybody-<side>`: shoulders and two hands pressed against the inside of
  the bark); by one sentry in three the M.E.G. have nailed a plank on a post, DON'T SAY IT.
- *The Heart of Water*: the M.E.G.'s red warning between two Green Giants (GREEN GIANTS / DO NOT CUT, CLIMB, CARVE),
  facing the way in; mossy stones standing in the shallows round the pool.
- *Glow rooms*: glowing bushes of the room's colour (`l23-glowbush-*`, light 9); one little tree in four a stone mushroom.
- *Ruins*: damaged frescoes (`l23-fresco-<side>`: a garden and people with green eyes, mostly flaked off) round the
  Sphere's inside at eye height and on the Lighthouse chamber's walls; rags of cloth (`l23-cloth`) among the pottery;
  inscribed stones set in the walls of the tunnels down to the ruins.
- *More*: a lost M.E.G. explorer's last camp in one forest cell in twenty (bedroll, crate, bones); long roots now and
  then from a glow room's roof to its floor with a pool at their foot (the lore's trees piping water down); rounder
  crowns on the little trees; stumps for seats round the fire ring.
- *Showcase spots* (from the layout): heart-of-water (now from up the slope across the pool), heart-warning,
  boulder-undergrowth, stone-mushrooms, fallen-log, glade, seedling-sign, seedling-board, seedling-counter,
  seedling-waysign, besides round 2's.
- *Handbook*: the page's forest, sentries and Base Seedling paragraphs mention the logs, mushrooms, glades, the planks,
  the camp's signs and rules board.

### Inventions (round 3)

All shapes and numbers above; the glades; the stone mushrooms, boulders, stone undergrowth, bracket fungi, knees and
moss as the petrified forest's floor (the lore names the tree species, not the floor); the M.E.G.'s signs, notice board,
rules, missing-person notice, ledger line, trails, way-signs, warning plate and planks by the sentries; the camp's
furniture; the frescoes' subject (the lore says only "damaged paintings"); the sentries' bodies; the stones in the
pool's shallows; the inscribed stones in the tunnels.

### Balance notes for the lead

- The lanterns are no longer loot (the review's item, done). The camp's barrels, crates, bedrolls, squirt guns, ledger
  and fire ring are looks only: no water, no storage, no sleep spot, no light source to take (the fire ring gives light
  but drops nothing).
- New drops: fallen logs and mossy bark give a little firewood (as the bark does), boulders granite stones (2 +- 1),
  stone undergrowth a stick now and then, rags of cloth a scrap of cloth (half the time), the signs a plank. None is food.
- **Water**: every water block in Level 23 counts as Clean (`WaterClass`, Level 23's arm, round 1: the reservoir feeds the
  whole level), so besides the spring at Seedling and the Heart of Water's pool, the puddles in every glow room and the
  stones' shallows are drinkable Clean water. The review proposes Tainted outside the spring and the Heart: a user
  decision, not changed.
- Arrivals are now in or by a glade: lit, open, so a newcomer sees what is coming.

### What the shots showed

Runs (`%TEMP%/backrooms-shots/`, all with a torch; the no-torch look judged from the spots with light of their own: the
glades, the light shaft, the Heart of Water, the glow rooms, the camp): `23-r3a-torch` (first), `23-r3c-torch-final`
(after the first fixes), `23-r3d-torch-final` (the last).

- *Arrivals* now open onto forest every way: the random arrivals stand in or by a glade or on open floor with aspens,
  arches, stone mushrooms and undergrowth in view, no longer nose to a trunk (round 2's `r0b` was a wall of bark).
- *The forest floor* reads as a floor with things on it: fallen logs (the rotated bark and ring ends read as logs; the thick
  ones are walls to walk round), stone mushrooms with their gills, the stone undergrowth's shapes (shrubs, saplings,
  fronds, stumps), moss over the trunks' feet, bracket fungi, white aspens among the grey and red trunks. Glades are pale,
  grassy and flowered, landmarks seen from afar under the canopy.
- *Base Seedling* reads as a working camp: the flagstone path to the hollow tree, BASE SEEDLING on its posts, the rules
  board (legible), the quartermaster at his counter with the ledger, M.E.G. crates and the squirt guns behind, barrels by
  the spring, the M.E.G.'s lanterns; the way-sign at a tunnel mouth reads from the forest.
- *The Heart of Water* spot now shows the reservoir under its shaft, the shore and the Giants beyond.
- Fixed after the first shots: the sentry's body was buried behind the buttress under its face (now on the outermost bark
  a block lower, and its relief stronger after the second); the Heart's warning was hidden behind roots and then behind a
  fern in front of the camera; the fire ring's log seats read as plain cubes (now stumps). The final run still showed a
  fern in front of the warning's camera (its clear-line test gave up on the basin's slope and fell back to nine blocks
  out); after it, the test counts only wood above the local ground and no fern grows within twelve blocks of the warning.
  Checked headless (a block dump: both boards and their posts stand at the spot's target, the camera four blocks in
  front), not reshot: the three runs were used.
- The sentry's body reads in the final run: shoulders and two hands under the face.
- Still weak: the forest is dim and its far trunks fog into one grey-green (as the lore wants, but it flattens a still
  frame); the thick fallen logs are blocky walls; the barrel's stencil wraps round the bulge; the sentry's body is subtle
  at a distance; with the rig's short view distance the sky sphere's glare shows through gaps at the loaded world's edge.

### Questions for the user

1. Water: every water block in the level is Clean (the reservoir feeds it all); the balance review proposes Tainted outside
   Seedling's spring and the Heart of Water. Keep Clean, or make the glow rooms' puddles Tainted?
2. Arrivals now favour the glades (lit, open): good for a first look, but the lore's surface is "extremely dense... little to
   no light". Keep them by the glades, or put arrivals in the dim forest again (with open floor round them)?
3. The M.E.G.'s signs, notice board, trails, planks by the sentries and the lost explorer's camp are inventions in the
   lore's spirit (the M.E.G. hold Base Seedling): keep them all?

### Checks (2026-11-01, commit 028fb88d)

`expclash.py` clean; mod and mapgen build, 0 errors; `layouthash` (seed 12345, 16000; layout 1 and 12,
`BACKROOMS_NO_EXP_ENTRANCES=1`): every line for levels 0-20 and the `layout hash` line identical to main's saved files;
`regions`: Level 23 60/60 (3.6 s, round 2's build 13 s); `23stats` ok (3.8 ms a cell, trunks and things in the way on
29.8% of the forest's tiles); headless (port 43174): `/backrooms dummy place 23 5` lands in a glade (light 22), the
showcase lists its 28 spots, 0 error lines; `GATE_TAG=l23 gate.py --fast --port-base 43170`: PASS. List: A 13/13 done;
B 15 done, 2 partly; C 6 done, 1 partly, 2 skipped.

## 6. Round 4 (2026-11-02): the asset-quality pass

The user asked for AAA assets, multi-block pieces, more level design and lore/level alignment. The lead's notes on round
3's sheet: the trunks are flat-textured columns (bark relief, root flares, buttress roots, limbs as rotated elements);
fallen logs rounded with rings; mushrooms and boulders sculpted; glow fungi as models; Base Seedling's tents, counter,
crates, barrels, fire ring, bedrolls and lanterns to the bar; the ruins' columns, lintels, a statue, frescoes; the
Heart's pool with lily pads and a rim; the sentries' faces sculpted; the forest's flatness (light shafts, the ground's
variety). Since round 3, Level 47's green giants' hollows lead here (their link files are not mine; their look is).

The trunks stay voxel (a trunk is 4-14 wide and 48 high); the bar is met by model blocks on their skin: the outermost
bark layer near eye height becomes relief blocks, and the air at their foot and under the lid takes flares and limbs.

### List

Tiers: A must, B should, C nice. Inventions are marked (inv.).

**1. Assets to rebuild to the bar**
1. [A] [done: `l23-barkface-<bark>-<a|b>-<side>`, six profiles] Bark relief: the trunks' outermost bark from the ground to ~10 up as model blocks (`l23-barkface-<bark>-<side>`):
   deep vertical fissures and raised plates (redwood fibrous ridges, oak blocky plates, cypress stringy strips, grey
   furrows, aspen smooth with eyes), the outward side only, so the silhouette breaks; five barks plus the green.
2. [A] [done: `l23-logpart`, eleven slices of 1-3 wide sections] Fallen logs rounded: one-high logs as an octagonal/round section model with the rings on its ends and moss on
   top (`l23-loground-<bark>-<axis>`); the thick logs' corner cells as quarter-rounds, so no log reads as a box.
3. [A] [done: `l23-caprim` side/corner/upper; the stem's foot not flared] Stone mushroom caps: the cap's rim cells as rounded, drooping edge models with gills under (`l23-caprim-<side>`),
   the stem's foot flared.
4. [A] [done: `l23-boulderpart` cap/edge/corner] Boulders: the outer cells as rounded, chunky stone models (several rotated lumps, a moss cap) instead of cubes
   (`l23-boulderlump`).
5. [A] [done: four-mushroom clusters, glowing gills, spores] Glowcaps (`l23-glowcap-*`): rebuilt as a cluster of three to five mushrooms with stems, caps with an underside,
   gills that glow, a lit spot on the ground; the colour only where the light is.
6. [A] [done: `l23-tent`, from the detail kit's `camptent`, re-detailed as a wall tent] Base Seedling's tents: an M.E.G. ridge tent of the level's own (`l23-tent-*`, similar to Level 8's `camptent`,
   but canvas olive with M.E.G. stencil): two A-frame poles, a ridge pole, sloped canvas, one flap tied open, pegs,
   guy lines; three blocks long (inv.: from `camptent`, re-detailed).
7. [A] [done: `l23-campcrate`, `l23-campbarrel`] Crates and barrels: crates with frame boards, corner irons, a lid with a gap; barrels with staves, two iron
   hoops, a lid and a tap; WATER stencil flat on the staves (round 3's wrapped round the bulge).
8. [A] [done: `l23-campfire`] The fire ring: a ring of stones, charred logs crossed, ash with embers, and a tripod with a pot over it.
9. [A] [done: `l23-campbed`] Bedrolls: a rolled blanket at the head, a pillow, the mat with quilting, a strap.
10. [A] [done: `l23-camplamp`, a hurricane lantern; its glass glows opaque (one block, one pass)] The lantern (`l23-lantern`): frame, glass panes (translucent), a wire handle, a bright flame, base and cap.
11. [B] [done: `l23-counter` l/m/r] The quartermaster's counter as one piece (`l23-counter-*`): plank top, front boards, posts, a shelf under, the
    ledger open on it, a cash tin and a scale (inv.), replacing the vanilla tables.
12. [B] [done: `l23-sentryface`] The sentry faces (`l23-sentry-*`) sculpted: brow, eye sockets, nose, open mouth in relief, bark folding round.
13. [B] [done] Bracket fungi with real shelf curves (several stepped half-discs, a pale rim, zoning bands on top).
14. [B] [partly: the fern rebuilt with pinnae; shrub, sapling, stump as round 3] Stone undergrowth (`l23-stoneplant-*`): more elements; rotated twigs on the sapling, frond curves on the fern.
15. [B] [partly: battens top and bottom, nails, a capped post with a mossy foot; no roof] The signs and the M.E.G. board: framed boards with bevels, nails and a little roof over the notice board.
16. [C] The squirt-gun rack and ledger: more detail (trigger, tank, nozzle).

**2. Multi-block set pieces**
17. [A] [done: `l23-flare`] Root flares: round every trunk's foot, wedge models in the air next to the bark (`l23-flare-<bark>-<side>`,
    rotated slopes from the bark down into the ground), so a trunk grows out of the ground instead of standing on it.
18. [A] [done: `l23-limb`, two to five a tree] Limbs: broken petrified branch stubs and dead limbs (rotated elements) out of the trunks between 6 and 16 up
    (`l23-limb-<bark>-<side>`), so the trunks have branches under the canopy.
19. [B] [done: `l23-rootknuckle`, the roots' tops near the ground] Buttress roots: the roots crawling out from the foot get a rounded top (half-round root caps, `l23-roottop`)
    where they are one high, so they read as roots and not steps of cubes.
20. [A] [partly: columns (base, fluted shaft, capital) and two broken ones on the plaza; no carved lintel] The ruins: Parthenon columns as fluted drums with a capital and base (`l23-column-*`), a carved lintel/frieze
    over the cella door, a fallen column on the plaza.
21. [B] [done: `l23-statue`, two at each ruin's way in] A statue in the ruins: a weathered robed figure on a plinth (two blocks), mossed, one arm broken (inv.).
22. [A] [partly: lily pads; no stone rim] The Heart of Water: lily pads on the pool's edge water, and a stone rim of mossy blocks where shore meets water.
23. [B] The hollow trunks (the way in from Level 47 and out): a mouth with a lip of bark relief and flare blocks round
    it, moss at its sill, the inside lined with dark relief, so the arrival reads as stepping out of a tree.
24. [B] The Heart's warning: the board framed, on two posts with a little roof, chained to a Giant's root (inv.).
25. [C] The Lighthouse's lamp as a brazier with a fire bowl on its top, not a lantern.

**3. Level design**
26. [A] [done: `l23-sunbeam`, translucent] Light shafts under the holes: pale translucent sun-beam planes (`l23-sunbeam`) hanging from the lid's holes to
    the floor, so the glades and holes read as columns of light from afar (inv.: the lore's star never moves).
27. [B] Ground variety: stone outcrops (bare petrified stone patches), leaf drifts against the trunks' windward side,
    more red litter, puddles in hollows.
28. [B] Far trunks fading in steps: the fog's density and colour tuned so the near, mid and far trunks separate.
29. [B] Arrivals keep their open floor; the first view takes in a flared, relief trunk close by.
30. [C] The glow rooms' floors: a few lit pools of light under the Sorries; moss carpets with glowing specks.

**4. Lore**
31. [B] Curabitur birds' nests (twigs in the limbs) as a sign of the birds the lore lists (inv.: nest only).
32. [B] Base Seedling's Almond Water: a water butt with a tap by the spring labelled for squirt-gun refills (looks only).
33. [C] Pottery: the amphora with handles and a neck, painted bands; a bowl.
34. [C] Cloth rags hung over stones, not only on the floor.

**5. Alignment with the other levels**
35. [A] [done: trunk-foot, trunk-limbs, seedling-tent, seedling-fire, ruin-statue; F7 entries] Showcase spots and F7 entries for the new and rebuilt pieces (tent, fire ring, counter, columns, statue, lily
    pads, a flared trunk, a limb, a fallen log, the sunbeam), from the layout.
36. [A] [done] Lang names for every new block (HUD), drops as round 3 (bark firewood, stone stones, camp things nothing).
37. [B] Level 47 shares the forest kind: note for the lead which of my relief/flare/limb blocks 47's giants could take.
38. [B] Shared things kept shared: supply boxes, notes, placards, chalk, Almond Water: unchanged.
39. [C] Shared assets below the bar: write up Level 8's `camptent` and anything else seen.
40. [A] [done: also fixed round 3's crate, barrel and the Sorries' strands] Opaque textures with no translucent texels (alpha 0 or 255 only) except the sunbeam and the lantern's glass.

### What was built (round 4)

- *The trunks' skin* (`WorldLayout.Level23.Skin.cs`, `WorldGenerator.L23.Skin.cs`, models in `tools/gen_23_r4.py`): the outermost
  bark from the ground to nine up is `l23-barkface-<bark>-<a|b>-<side>`: a core with the fissures' floor 3.5 px in and
  ridges standing out to the block's face, each bark its own profile (grey furrows with plates broken across, redwood's
  soft fibres, oak's blocky plates, cypress's stringy strips, aspen smooth with a black eye, the Green Giants' deep
  furrows, the mossed band with cushions of moss); the fissures' walls and floor a darker copy of the bark; two patterns
  that meet above and below. Root flares (`l23-flare`) in the air at every trunk's foot: a concave slope of mossy bark
  (green on the Giants), or a lower one with a root running out; a step (half a block). Broken limbs (`l23-limb`): two
  to five a tree, six to fifteen up, an octagonal limb tilted up out of a collar of bark, its broken end showing rings,
  a fork on the long ones. The roots' tops near the ground rounded (`l23-rootknuckle`).
- *The floor's things*: fallen logs as slices of their round section (`l23-logpart`, eleven pieces for logs one, two and
  three blocks across, rings on their ends, moss along their tops); stone mushroom caps with a drooping rim, gills under
  and a sloped upper layer (`l23-caprim`); boulders' rounded tops and edges (`l23-boulderpart`); the stone fern rebuilt
  with pinnae; bracket fungi as half-disc shelves narrowing outward.
- *Base Seedling* (`tools/gen_23_r4_camp.py`): the M.E.G.'s wall tents (`l23-tent`, two by two on the layout's tent tiles:
  canvas walls, a pitched fly on a ridge pole, the door flaps tied back under a valance, guy lines to pegs, a stovepipe
  with its rain cap and the stove under it, M.E.G. 23-1 stencilled by the door; a cot, blanket, pillow and footlocker
  inside); the quartermaster's counter (`l23-counter`, three blocks, plank top, boarded front, a shelf of tins, a brass
  balance and a cash tin, the ledger on it); the fire (`l23-campfire`: stones, ash, crossed charred logs, embers and
  flames glowing, a tripod of poles with a pot on a chain); water barrels (`l23-campbarrel`: staves, two iron hoops, a lid,
  a brass tap, DRINKING WATER on a flat label); crates (`l23-campcrate`: boards, battens, corner irons, a lid, M.E.G.);
  bedrolls (`l23-campbed`); hurricane lanterns (`l23-camplamp`) at the camp and down its tunnels; the signs framed with
  battens and nails, their posts capped and mossed at the foot.
- *The sentries*: faces sculpted (`l23-sentryface`): bark folds round a mask, brow, sunken shut eyes, cheekbones, nose,
  the mouth open, a chin; paler stone than the bark.
- *The ruins*: the Parthenon's colonnade as columns (`l23-column`: a base with plinth and torus, fluted octagonal shafts,
  Doric capitals with echinus and abacus; mossy at the foot), two broken columns standing apart on its plaza; two statues
  of Architects at every ruin's way in (`l23-statue`, three blocks: an inscribed plinth, HORTVLANO MAGNO; a robed figure
  with a sapling held to its chest, one arm broken, two green stones for eyes); the Lighthouse's fire is Level 47's brazier.
- *Glow rooms*: glowcaps as clusters of four with glowing gills and spores on the ground.
- *The Heart of Water*: lily pads with a flower on the shallows.
- *Light*: shafts of light (`l23-sunbeam`, translucent crossed planes, glowing, no light given) under a scatter of every
  hole's columns, from four over the ground to the top.
- *Fixes*: round 3's crate and barrel stencils and the Sorries' strands had translucent texels (now opaque); the lost
  explorer's camp never had its bones (the block was looked up in the wrong domain).
- *Showcase*: trunk-foot, trunk-limbs, seedling-tent, seedling-fire, ruin-statue (F7: Forest floor, Base Seedling, the
  Parthenon).

### Shared assets below the bar

- The detail kit's `camptent` (Level 8's camps) is good; the wall tent here is a sibling, not a replacement.
- Level 47's `l47-brazier`, reused on the Lighthouse, is a fine fit; Level 47's giants could take this level's skin
  blocks (`l23-barkface-green-*`, `l23-flare-green-*`) round their feet the same way (the lead's call: their link files
  and layout are Level 47's).

### Inventions (round 4)

All shapes, profiles and numbers; the bark's relief by species; the root flares, limbs and knuckles; the wall tent's
stove and cot, the counter's balance and tins, the tripod and pot; the statues (an Architect holding a sapling, the
green stones for eyes after the plaque, the inscription HORTVLANO MAGNO), their places at the ruins' ways in and the two
broken columns; the lily pads (the lore names no plants on the reservoir); the shafts of light (the lore's star never
moves, so they stand still); the brazier on the Lighthouse (shared from Level 47).

### Balance notes for the lead

- Nothing to eat, drink, sleep in or carry away was added. The root flares are a half-block step at every trunk's foot;
  the limbs, lily pads and shafts of light have no collision; the camp's things block like round 3's (the tent its four
  tiles, the counter like the tables it replaces). Drops: relief bark, flares and limbs firewood as the bark; root
  knuckles a stick; boulders' tops stones as boulders; the camp's crates and barrels planks as before; tents, counter's
  ledger, statues, columns, lanterns, fire nothing (columns and statues are ruin stone: no drop).
- The camp fire gives light 11 (round 3's ring 10); the lanterns the same as before; the Lighthouse's brazier is Level
  47's (light as there, drops nothing).
