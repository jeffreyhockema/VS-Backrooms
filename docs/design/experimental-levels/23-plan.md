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
