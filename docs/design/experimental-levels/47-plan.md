# Level 47 "The Adderwood": plan

Internal id **30**, `WorldLayout.Level47`, tag `47`, blocks `l47-`, method infix `L47`, region far south-south-east
(`1.35 R` out, 33.75 degrees east of south; see the README). Reserved: the L47 column of the README's table (`WallPattern`/
`FloorKind`/`Unders`/... 544-575, `Props` 1600-1699, title keys 3001-3099, salts 0x3000-0x30BF and 0x30C0-0x30FF, ports
43220-43229). Source: Wikidot only, https://backrooms-wiki.wikidot.com/level-47 ("The Adderwood", DrChandra, CC BY-SA 3.0;
fetched copy `%TEMP%/backrooms-lore/fetch/wd-47.txt`). Fandom's Level 47 (drywall question-rooms) is another place and is
not used. Links: `LINKS.md`, "Level 47, the Adderwood".

## 1. The lore, element by element (quoted), and what is built of it

| Lore (Wikidot) | Built |
|---|---|
| "a primeval, old-growth forest that is highly resistant to both entropy and man-made alterations" | The forest; "resistant to alterations" left to the notes and the handbook (see superposition below). |
| "a temperate forest consisting of both deciduous and coniferous trees. Many of these trees exceed a hundred feet in height and appear to be hundreds to thousands of years old" | Oak, beech, fir and spruce on a jittered 12-block lattice; old ones radius 1.3-3.8 with buttressed feet and roots, broadleaf crowns of round lumps, conifers in tiered cones, 30-47 blocks tall (the level is dropped 10 so the top of the world is 48 over the forest floor: a hundred feet is ~30 blocks); young trees among them; dead trees grey and bare. |
| "Thick green moss and lichens cover most surfaces suitable for their growth" | Moss floor carpets, moss bark up every trunk's foot and in patches far up, mossy logs, boulders and stones, lichen-patched bark alternates, old man's beard (vanilla hanging lichen) from crowns and boughs. |
| "During daylight hours, the forest is uniformly covered in a thick, damp fog, and no direct sunlight has ever been observed" | Day fog 0.034, pale grey-green, ground mist, the sky hidden in a fog sphere (no sun). |
| "Each night, however, the fog will disperse without fail to reveal a full moon ... several times closer and with the far side facing towards Level 47. Stars and the Milky Way are visible as well, but do not match any constellations ... rare, silvery-white auroras" | 19:00-20:30 the fog thins to a clear dark-blue night (5:00-6:30 it returns); `Regions/L47Sky.cs` draws a star dome of our own (no real constellations) with a Milky Way, the Moon's far side (generated: highland craters, Moscoviense and Tsiolkovskiy dark, South Pole-Aitken grey) 9 degrees across, rising east at dusk, south at midnight, west at dawn, and on one night in six silver aurora curtains in the north. |
| "Mapping Level 47 has proven to be impossible ... any part of the forest not under direct observation seems to be in a state of superposition ... returning to a state of superposition will often revert any damages or alterations ... campfires or improvised tools and weapons will often (though not always) vanish or revert" | **Rumour + sound** (the brief's "light, fair form or leave to the notes"): a soft displacement sound behind the player every few minutes; the notes ("It puts things back") and the handbook. Blocks the player places are NOT reverted (unfair, and the save would fight it). The Shucks' and the Adder's translocation when unobserved is built (below). |
| "Streams and other natural water sources are common ... generally safe for human consumption" | Winding streams (the zero line of a warped noise field), pebble beds, water at rel 0, banks sloping down; `WaterClass`: clean. Logs fall across them as bridges; the trail fords them on stepping stones. |
| "Mushrooms are the most plentiful and accessible food source, though some species are poisonous or hallucinogenic" | Vanilla mushrooms by the wood (about 9% of floor beside trunks and logs): field mushroom, king bolete, chanterelle, black trumpet, puffball, orange oak bolete; 30% poisonous (fly agaric, death cap, earthball, devil's bolete). Hallucinogenic: the fly agaric stands in (vanilla poisons it; no hallucination effect). |
| "numerous species of snakes ... none of them appear to be anomalous" | `l47-snake`, four species (grass snake, adder, black rat snake, ringed milk snake), up to four round each player, harmless, slip away, rear when cornered. |
| "Harming or killing any of the snakes ... immediate appearance of a bright crimson Titanoboa ... the Great Old Adder ... hunt and devour the offending parties. There is no known instance ... of anyone successfully evading it or fending it off" | `l47-greatadder`: put down out of the offender's sight 16-24 blocks behind them, rears and roars, hunts (faster than a sprint, 600 health, a 16-damage tier-5 strike), slips nearer when stuck or far and unobserved; once its quarry is dead or out of the level it devours/leaves. Only the offender (and whoever strikes it). |
| "the snakes' only natural predators on Level 47 are crows and ravens, and this predation does not appear to upset the Great Adder" | Crows and ravens as sound by day (synthesised calls). No bird entity (vanilla has none). |
| "packs of large black canids ... Black Shucks ... use the protean nature of the forest ... long, baleful howls travel for miles ... a scout ... will not let it out of their sight until they are joined by the rest of their hunting party ... stalking ... without ever attacking ... translocate short distances when unobserved ... climb the highest tree ... Shucks have never been encountered during the day ... return to their dens before daylight" | `l47-shuck` (the vanilla wolf shape, coal-black, pale eyes, size 1.3): at night, after ~70 s out in the forest, a scout is put down out of sight and stalks at 6-9 blocks, howling for the pack; more come every 30-55 s; with three together they hunt. Unobserved, a Shuck blinks a few blocks nearer. Out of reach (more than 2.6 above them: up a tree) they circle and wait. At dawn they run and are gone. Never in the glade. Far howls in the night's sound bed. |
| "a subspecies of Irish Elk ... Bucks and does with young can be highly aggressive ... break bi-directional line-of-sight ... Wanderers should not attempt to hunt these Elk unless they have the firepower to take them down in one shot" | **Substitution**: the vanilla moose (palmate antlers; bulls and cows charge), now and then by day 45-70 blocks off, a cow sometimes with a calf. No custom elk model. |
| "a single, serpentine trail ... does not exist in a state of superposition and will not vanish once spotted ... Some follow it for days ... Others have claimed that the trail ended at a glade after following it for as little as seven miles" | A spiral from the glade outward (turns 150 apart, swinging in a serpentine every ~70 blocks), 1600 blocks out (tens of km of trail): followed outward it never gets anywhere, inward it ends at the glade. Trodden earth 3 wide, kept clear of trunks and logs. |
| "This glade contains either a large manor house, or an ancient megalith. The two appear to exist simultaneously in a state of superposition ... the headquarters of ... the Ophion Occult Order" | **Our reading of "simultaneously"**: both built in one place. A meadow 46 blocks round; a two-storey manor (25 x 15, grey ashlar on a dark plinth, timber band, slate gable roof, leaded windows, chimneys, a hall with the Altar Stone, a great hall with a long table, lanterns and banners, an east room of shelves, a loft by ladder); an outer ring of 14 sarsens (lintels on paired stones, a gap at the south) and an inner horseshoe of 5 trilithons that stand through the manor's rooms, floors and roof. |
| "they hold The Great Old Adder in great reverence, believing it be a scion or avatar or emanation of a Divine World Snake" | The Order's preaching lines; banners and the clasp with an ouroboros (our sign for the World Snake). |
| "Members ... clad in hooded, crimson garb and ivory masks ... normally indifferent ... abduction to proselytization ... boast about ... the ability to travel The Backrooms at will ... an ability to summon and to some extent command The Great Adder ... the Black Shucks have been witnessed fleeing from even a lone member" | `l47-ophion`: four keepers at the glade (warn once, then drive out with blows, as far as the forest's edge); walkers on the trail now and then (indifferent: stop, look, preach eight boasts); struck, one fights and **brings the Great Adder** (our reading of "summon"); Shucks within 12 of one run. Abduction: rumour only. |
| "regard any promises of aid or salvation as duplicitous" | The preaching lines tempt (a way home, cut off mid-sentence, as the lore's silenced member). |
| "No-clipping is the only confirmed method to either enter or leave ... easier and more frequent than average. The hollows of dead trees appear to be especially prone" | The links (section Links). |
| "Members ... claim that it's possible to steer or summon [the trail] towards specific no-clip points ... even ... The Frontrooms" | Rumour (the preaching, the handbook). |

**Inventions (ours, marked):** the trail's spiral shape; the Order's way-stones (a snake carved on a granite post every
~120 blocks, notes at every third); manor and megalith built in the same place; the ouroboros as the Order's sign; the
moose for the Irish elk; the Adder summoned by harming an Order member; the hollow-tree host in Level 10 (LINKS.md).

## 2. Survival class and dangers

Class **3** (`SurvivalClass`; Wikidot's Survival Difficulty 3). `Danger.OfLevel` 0.45. The director puts nothing down
(band Safe): `Regions/L47System.cs` keeps the level's own as above. The day is safe enough (snakes, elk at a distance); the
night is the danger (Shucks); the glade is the Order's; the Adder only for those who harm a snake. Temperature 11 C (9 by
the streams, 12 in the glade, 15 in the manor); stability 0.86 in the forest, 0.92 on the trail, 0.95 in the glade.

Loot: a supply box at a tree's foot in about one cell in six (0.16 a cell), five in the manor (the Order's stores). Bark,
logs give a little firewood; boulders granite stones; the shelves parchment; the banners cloth. Food: mushrooms; the elk
(vanilla drops). Water: every stream.

## 3. Numbers

- Region: the scaffold's (radius `max(40, spawnMacroX/50)` cells: about 10 km at full size); the glade at its centre (+-12).
- Heights: `L47Drop` 10, band 10 deep (lit from rel -10 to +30), columns built to the top of the world (rel 48) as Level 23.
  Ground rel 1-4 (humps of fbm), streams rel -1/-2 with water to 0, the glade flat at 1.
- Trees: lattice 12 (10% gaps), oak 30%, beech 15%, fir 28%, spruce 18%, dead 9%; 12% young (radius 0.55-0.8). Within 300 of
  the glade (seed 12345): oak 524, beech 271, fir 518, spruce 355, dead 192 (73 hollow), young 191. Logs: lattice 23, 40%;
  boulders: lattice 19, 28%.
- Harness (`47stats`, seed 12345, 625 cells round the glade): forest 93.3%, trail 2.5%, glade 1.0%, stream 3.2%, manor
  0.1%; 8% of forest tiles blocked; open ground (arrival spots) 15%; 8.8 ms a cell; the trail walked out 2000 points with 0 in a wall.

## 4. Links

| Way | Host | Feature | Kind | Rarity | Nearest (seed 12345, full size) |
|---|---|---|---|---|---|
| In | Level 10 | an ancient dead tree, grey, hollow, 13-18 high, buttressed, bare limbs over the hedges, on a field's edge where it can (not on roads, farmsteads, paddocks, ponds) | one-way: out of a dead tree's hollow in the Adderwood (one of those within 520 of the glade, by key) | at most one to a square of 1408 blocks, in 3 of 5, inside the square's middle (250 margin): about 0.3 per km2, nearest neighbours at least 575 apart (median 1207) | 5.5 km from spawn (517496, 512084) |
| Out | Level 47 | a dead tree's hollow (about half the dead trees thick enough are hollow; 4 in 10 of those lead out) | one-way: Level 10, beside one of its ancient dead trees (the twelve nearest spawn, by key) | 62 of 173 hollows within 520 of the glade | 63 blocks from the glade |
| Out | Level 47 | a green giant: green bark, radius 4.2-4.8, to the top of the world, a hollow with a mouth between buttresses | one-way: Level 23, out of a hollow trunk in the forest (Level 23's own finder, `IntoL23Hollow`) | one at most to a square of 300, in half of them (41 within 1500 of the glade) | 387 blocks from the glade |

Rows for the guide's ways-between-levels table (added to `PAGES["thresholds"]`, one-way farther levels): "Level 10, an
ancient dead tree, grey and hollow, alone on a field's edge: Level 47, out of a dead tree's hollow. Level 47, some of its
dead trees' hollows: Level 10, beside its ancient dead tree; a green giant's hollow: Level 23, out of a hollow trunk in the
forest."

Rumours (notes and handbook): the Order's steering of the trail to any noclip point, the Frontrooms.

Layout hash: with `BACKROOMS_NO_EXP_ENTRANCES=1`, levels 0-20 and the layout hash identical to main (v1 and v12); with the
entrances on, only world 12345/16000's Level 10 line moves (and the layout hash), as expected.

## 5. Content

- Notes (`gen_notes.py` track `l47`, seven): fog by day (anon), not one snake (Dez), the black dogs (Tom), the trail and the
  glade (A.L. survey), red robes (Nell), water, food, ways (M.E.G. field notice), it puts things back (anon); and one in
  Level 10's track, the old tree (A.L.). They lie at the foot of every third way-stone and on the manor's long table, besides
  the boxes.
- Handbook page `PAGES["level47"]` (`GuideSystem.Added`), title and hint lines, the Glade (3001) and Trail (3002) titles.
- Lang: one block from `level-30` (`tools/gen_47.py` writes it: blocks, `tools/gen_47_lore.py` texts, the handbook, the notes).

## 6. Showcase spots

forest-long, trail, trail-walker, waystone, stream, glade, stones-through-roof, great-hall, east-room, entrance-hall,
keepers, snake, great-adder, elk, night-moon, night-glade, night-shucks, dead-hollow, green-giant, way-in-level10. The
creatures' spots put theirs down in front of the camera held still (`/backrooms l47 show...`).

## 7. Screenshot cycles (tools/clientrig/shots.py 47, port 43222)

1. `%TEMP%/backrooms-shots/l47-c1`: the day fog far too thick and white (the forest a blank); the night and the glade read
   well (manor and trilithons through its roof, stars); the moon off frame; the creatures' showcase spots put them where
   the camera was not yet looking (the tour turns after the setup); `/time set day` is dawn, half the "day" shots dark.
   Fixed: day fog 0.034 to 0.017, darker grey-green, less fog floor; night scene 0.45 to 0.85; `lunch`/`midnight`; the show
   commands take the shot's heading; lanterns in the entrance hall; a softer Milky Way (the dark lanes were blotches).
2. `l47-c2`: the moon's far side over the trees; still random dark shots. Cause: every `/time set` jumps a day forward
   and the light takes seconds to follow. Fixed: the tour sets the clock only where it changes (Level 10 first, the day's
   spots, the night's, a last day view). Under the green giant's crown it was black (twenty layers of leaves): crowns are
   now shells two blocks thick, as a real crown's gaps let light in.
3. `l47-c3`: no dark shots but two; the forest reads (ferns, moss, old man's beard, layered trunks into the fog); the
   Black Shucks on the trail at night with a walker; the green giant from 17 blocks. The roots' tops showed cut rings
   (stumps): mossy bark has a moss top now. Logs no longer span streams (a one-block trunk over water looked like a plank
   in the air).
4. `l47-c4`: every shot lit. The Great Adder was there but head on in the grass, reading as a red post: now put down side
   on. The stream shot stood on a log's end and looked through the flat ground fog (the level's floor is ten under the
   shared floor, so the vanilla fog floor lay at head height): the ground fog is now a hint (-0.07 by day), the stream spot
   keeps clear of wood.
5. `l47-final` (the final sheet: `%TEMP%/backrooms-shots/l47-final/sheet.jpg`): every shot lit; the Great Adder rearing
   crimson in the glade's meadow; the Order's keepers, a walker, the Shucks at night on the trail; the moon's far side
   over the giants; the manor and the trilithons by day and night. Still weak: the stream shot (a narrow brook seen across
   its bank, through mist); the dead trees' hollow mouths are square doorways; the aurora is faint; the Adder is a long
   rigid S (it cannot follow the ground behind its head).

## 8. Checks (2026-11-01)

expclash clean; mod and mapgen 0 errors; layouthash (seed 12345, 16000, v1 and v12) with `BACKROOMS_NO_EXP_ENTRANCES=1`
identical to main for 0-20 and the layout hash; with the entrances on, identical to the scaffold's (Level 10's trees are
kept two cells inside Level 10, so no other level's edge moves; only `level 30` and the far places hash change); `regions`
60/60 at full size and `SPAWN=1000`; `47stats` and `47links` ok; headless (port 43221/43223): a dummy in 47 with 0 error
lines, the three ways through `/backrooms l23walk` (Level 10's tree to 47 beside a hollow, a 47 hollow to Level 10, a green
giant to 23's hollow trunk); `GATE_TAG=47 tools/gate.py --fast --port-base 43220` PASS.

## 9. Balance notes for the lead

Food: mushrooms (about 9% of floor beside wood, 30% poisonous), the elk (vanilla moose, by day, rare); water: every stream
is clean (`WaterClass`). Supply boxes 0.16 a cell plus five in the manor (guarded). Wood: bark and logs give a little
firewood, so a fire is easy here. Danger: the director puts nothing down; the Shucks (5.5 damage scaled by Danger 0.45,
30 health, packs of three) are the night's threat; the Great Adder (16 damage tier 5, 600 health) only for those who harm
a snake or an Order member.

## Round 4 (2026-11-02): the asset-quality pass

Brief: `%TEMP%/backrooms-lore/BUILDER-ROUND4.md` (the user's "AAA quality assets, multi-block elements, keep refining,
share assets where possible"). Starting point: the round-0 build (2026-11-01, `l47-final` sheet): the forest reads, but
almost everything is a full cube with a picture on it (5 model shapes in the whole level).

### List

Tier A must, B should, C nice. Block codes are the ones to (re)build.

**1. Assets to rebuild to the bar**
1. [A] [done] Trunks read as square columns: `l47-fillet-<bark>-<moss>-<corner>`, a 45-degree bark chamfer (a rotated element) in
   every notch of a trunk's, root's, buttress's and limb's stepped outline, so trunks read round and roots flow.
2. [A] [done] Bark relief in the textures: deeper furrows and plates (oak), corky ridges (fir), scales (spruce), smooth beech
   with its eyes, split grey dead wood; light on the ridges, dark in the furrows, so the trunks have relief at 2 and 20 blocks.
3. [A] [done] Moss and lichen draped on the north side: `l47-mossdrape-<side>`, a cushion of moss on the trunk's face with
   ragged hanging fringes, on the north (and damp) faces at the foot and in patches up the trunk.
4. [A] [done] Bracket fungi on the trunks: `l47-bracket-<side>`, tiers of shelf fungus (cream, ochre, rust) on a trunk face.
5. [A] [done] Mushroom clusters on the ground and on logs as models: `l47-mushclump-<kind>` (fly agaric with white warts, a
   honey-fungus clump, a cluster of pale caps); decor only, the vanilla mushrooms stay the food.
6. [A] [done] The way-stone: `l47-waystone-lower/upper`, a dressed granite post (tapered, chamfered) with the snake carved in
   relief coiling up it (elements), its head over the top, moss at the foot; replaces the cube with a zigzag picture.
7. [A] [done] The manor's windows: `l47-window` as a model: stone mullion and surround, a sill, lead cames in diamonds over
   translucent green glass (translucent pass).
8. [A] [done] The manor's front door: `l47-door-*`, iron-strapped oak double door with ring handles and studs, in the 3-wide
   arch (one leaf open so the house stays walkable).
9. [A] [done: chimney pots too] The roof: `l47-roof-<side>` slate slopes (a rotated slate plate over a stepped fill) instead of stepped slate
   cubes; `l47-ridge` cap along the ridge; chimney pots on the stacks.
10. [A] [done] The shelves: `l47-bookcase-<side>` as a model (frame, shelves, book spines of different heights, scroll
   pigeonholes, bottles and jars, the snake skull), replaces the cube with a picture.
11. [B] [done] The banners: rod with finials and a cord, the cloth hanging in slight folds (several elements), the gold hem.
12. [B] [done: the dish of candles rebuilt; a candelabrum on the table] The candles: `l47-candelabrum` (iron stand, drip pan, five candles with drips and flames that glow).
13. [B] [done: a cleft narrowing over the walking rows] The hollow mouths: rounded, ragged arches (`l47-mouth-*` bark pieces at the mouth's top corners), not square doorways.
14. [B] [done: `l47-leafspray`] Leaf fringes: `l47-leafspray`, sprays of leaves/needles hanging under and beside the crowns' lumps, so the
   crowns' silhouettes are not cubes.
15. [B] [partly: boulders yes; logs not (their steps are vertical)] Boulders rounded with granite fillets (`l47-fillet-granite-*`); logs too (`l47-fillet` on their bark).
16. [B] [done: a helper agent, 35 -> 80 elements] The Order's figures (`l47-ophion`): fuller robe with sleeves, a peaked hood, the ivory mask with brow and nose.
17. [C] [done: brow scales, jowls, heavier jaw] The Great Adder's head: brow scales, a heavier jaw (check up close first).
18. [C] [done: `l47-streamstone-step`, and `-rock` in the streams] Stepping stones at the trail's fords as flat mossy slabs (`l47-steppingstone`), not boulder cubes in water.

**2. Multi-block set pieces**
19. [A] [done] The great hall's hearth wall: a chimney breast in the west gable with a stone surround, a timber mantel beam
   with candles, an iron fireback, firedogs and burning logs (lit), flagged hearth before it.
20. [A] [done] The great hall's long table as one piece: `l47-table` trestle table segments (top, trestles, stretcher) with
   `l47-bench` benches either side, set with pewter plates, cups and candles.
21. [A] [done: own sconce, not `l73-sconce` (6 boxes, below the bar)] The Order's tapestries: `l47-tapestry-*` 2x2 (the World Snake round the world), on rods, in the great hall;
   iron candle sconces on the walls (`l73-sconce` reused).
22. [A] [done] A fallen giant with its root plate: some old trunks lie fallen with the root plate torn up at one end (a
   vertical disc of roots and earth, a pit before it), the lead's example.
23. [B] [partly: weathered round tops on the stones with no lintel (`l47-sarsentop`); lintel ends left square] The megalith circle: sarsens with weathered rounded tops (`l47-sarsencap`), lintels that read as lintels
   (projecting ends), moss at the feet.
24. [B] [done: a pent roof of slate on two oak posts with braces (`l47-porchpost-*`)] A porch over the front door: a gabled timber porch on two oak posts with braces, slate roof, a lantern.
25. [B] [done: bookcases on three walls, the reading table] The east room as a library of scrolls and bottles: bookcases on three walls, a reading table with an open
   book, a lantern, scroll racks.
26. [C] [done: `l47-offering-bowl/skull/book` on the Altar Stone] The Order's shrine at the Altar Stone: offering bowls, candles all round, an ouroboros carved on its top.

**3. Level design**
27. [A] [done: hearth, tapestry, manor-door, root-plate, mossy-oak; F7 l47hearth, l47library, l47door, l47rootplate, l47mossy] Showcase spots and F7 entries for every new or rebuilt set piece (hearth, table, library, door/porch, roof,
   waystone, root plate, brackets/moss, mushrooms).
28. [B] [done: `l47-lamppost-*`, four pairs] The walk up to the manor: lanterns on posts along the flagstones, the braziers on stone bases.
29. [B] [done: the fire, the table's candles, the mantel, sconces in the hall; one candle in the library; the loft dark but for its lanterns] Light rhythm inside: the hearth lights the great hall warm, the entrance hall by the altar's candles, the east
   room by one lamp, the loft dark.
30. [B] [done: river stones, stepping stones] The stream: mossy stones and pebble shoals at its banks, so it reads as a brook, not a ditch.
31. [C] [done: `l73-chest`, `l73-sacks`, `l23-barrel`, `l23-crate`] The loft as the Order's store: chests, sacks, robes on pegs (reuse `l73-chest`, `l73-sacks`).
32. [C] [skipped: time] Pools where streams meet, wider water in places.

**4. Lore**
33. [B] [done] "Thick green moss and lichens cover most surfaces": moss drapes (3), lichen on the stones, moss on the roof's
   north slope and the waystones' feet.
34. [C] [done: one cell in sixteen, `l23-firering` alight, `l23-bedroll`, a log; spot `camp`] "campfires or improvised tools ... vanish or revert": an abandoned wanderer's camp half gone (a cold fire ring
   with a log missing, a dropped pack), rare.
35. [C] [skipped: left to the sound bed] Crows and ravens: a carved crow on the waystone tops? (left to sound unless time).

**5. Alignment with the other levels**
36. [A] [done] Reuse instead of forking: `l73-sconce` (wall candles), `l73-chest`, `l73-sacks` for the loft, `l23-lantern`'s
   shape (already), the mod's supply boxes and notes; similar-but-unique: the tapestry (from `l73-tapestry`'s 2x2
   layout, redrawn with the Order's World Snake), the fire (own logs model in our hearth, after `l73-fire-logs`).
37. [B] [done: below] "Shared assets below the bar" and the families written in this doc for the lead.
38. [A] [done: untouched] Lead's note: keep the day fog, the moon and the aurora as they are.

### What was built (round 4)

All of it is generated: `tools/gen_47_tex4.py` (the surfaces as lit relief), `tools/gen_47_props4.py` (the models, their
textures and blocktypes), both called from `tools/gen_47.py`; the creatures in `tools/gen_47_creatures.py`.

- **Surfaces**: every bark (oak plates and furrows, fir's corky ridges, spruce scales, smooth beech with lenticels and
  algae, split grey dead wood, the green giants' furrows) painted from a height field and lit from the upper left; moss as
  cushions with a shadow under each; lichen rosettes; granite rounded with feldspar specks and crazing; logs' furrows run
  along them now (the oak log's texture was standing up).
- **The forest's outline**: `l47-fillet-<bark>-<corner>` (14 barks incl. mossy and granite, 4 corners), a 45-degree plate
  over a stepped fill in every notch of a trunk's, root's, limb's or boulder's stepped outline (wood on two sides and the
  corner between), matching the neighbour's bark (and its moss); `l47-leafspray-<leaf>-hang/tuft` under and over the
  crowns' lumps (40% / 30% of the cells there). The generator caches each column's wood a thread
  (`WorldGenerator.L47.cs`, `L47WoodAt`) so the neighbours cost little.
- **On the trunks**: `l47-mossdrape-a/b-<side>` (the collar at the foot, patches higher up; on mossy north faces one in
  two, other mossy faces one in seven), `l47-bracket-zoned/sulphur-<side>` (one in eight dead-wood faces, one in forty
  living); `l47-mushclump-agaric/honey/inkcap` by the wood and on the logs (decor; the vanilla mushrooms stay the food).
- **The ground**: fallen giants with their root plates (`L47PlateOf`, `l47-rootearth` and root bark: a disc 2.6-4.2 in
  radius on edge at the foot of about half of the old, thick, long logs); `l47-streamstone-step` at the trail's fords and
  `-rock` mossy river stones (6% of stream cells), both standing in the water; the Order's way-stone `l47-waystone2`
  (two blocks: footing, dressed post, the carved snake coiling up it, its head over the top, turned to the trail).
- **The hollows**: the mouth a cleft narrowing over the two walking rows (not a square doorway); the walking rows, where
  the way is found, unchanged.
- **The manor**: slate roof slopes, eaves with fascia and gutter, the ridge, the gables' stone filled up under the slope
  (`l47-roof-*`; the north slope mossed); clay chimney pots; the chimney stacks now stand through the roof (the roof plate
  was drawn inside them); leaded windows in dressed stone surrounds with mullion, saddle bars, sill, head and hood mould
  (`l47-leaded-*`); the oak door, iron-strapped and studded, both leaves open into the hall (`l47-door-*`) in an oak frame
  with a Tudor head (`l47-doorjamb-*`); the great hall's hearth wall (a chimney breast four wide with the fire on andirons
  `l47-fire`, the hearthstone, the mantel beam on corbels with candles `l47-mantel-*`), the trestle table set with pewter,
  bread and lit candles (`l47-table-*`, four long) with benches (`l47-bench-*`), the World Snake tapestry (2x2,
  `l47-tapestry-*`) between the windows on both long walls, the banners either side of the hearth (the west gable's
  ground-floor windows moved to stand either side of the breast), iron sconces (`l47-sconce-*`); the east room as the
  Order's library (`l47-bookcase-*` on three walls: books, scroll stacks, bottles and jars, the snake's skull) with a
  reading table; the loft's stores; the banners in folds on an iron rod with finials and cord, tassels at the foot; the
  dish of candles with drips and pooled wax; the standing stones with no lintel end in a weathered round top
  (`l47-sarsentop`).
- **The Order's figures** (`l47-ophion`, 35 -> 80 elements: stepped skirt flaring to a frayed hem, pleats, a mantle,
  wide sleeves with cuffs, a peaked hood with a rim, the ivory mask with brow, nose, cheeks and eye slits, the ouroboros
  clasp with a garnet, the cord belt's tassels) and the Great Adder's head (27 -> 37: brow and supraocular scales, a
  rostral scale, jowls, a heavier jaw with chin and keels, an arrowhead on the crown): a helper agent, in
  `tools/gen_47_creatures.py`.

### Inventions (round 4, ours)

The World Snake tapestry's picture (a red serpent round a dark world under a pale moon), the library's contents, the
Order keeping a fire in the great hall, the fallen giants' root plates (the lore's forest reverts damage; a giant blown over
unseen is ours), the carved snake's head on the way-stones.

### Shared assets below the bar (for the lead)

- `l73-sconce` (6 boxes) is below the bar; 47 has its own `l47-sconce` (9 boxes: plate, scrolled arm, brace, pan, candle,
  drip, flame) the Redlands could share.
- `l73-chest` (5 boxes) and `l73-sacks` (5) are reused in 47's loft as they are; both would want hasps, bands and handles
  (the chest) and tied necks and folds (the sacks).
- `l23-crate` and `l23-barrel` are full cubes with pictures; reused in the loft, they are the weakest things in it.

### Balance notes for the lead (round 4)

Nothing the balance rests on changed: no new food, water or beds; the mushroom clumps drop nothing; the river stones and
stepping stones only make the streams easier to cross; the great hall's fire gives light and no warmth beyond what the
manor's 15 C already has. The loft's stores are props (chests, sacks, barrels, crates), not containers with loot.

### What the shots showed (round 4)

1. `%TEMP%/backrooms-shots/47-r4a` (after the A items): none of the new models were there. The generator looked the
   mod's own new blocks up with `OptionalId("l47-...")`, which resolves to the game's domain, so every one was air (the
   manor had no roof, the hall no hearth or table, the forest no fillets); only the new textures showed. Fixed with the
   `backrooms:` domain on every lookup. What the textures showed: the oak bark read as brick courses (its plate breaks
   were rows); the lichen rosettes on the alternates read as white polka dots; the stream spot stood on a dead root's cut
   end and looked at a bank of moss, not along the water. Fixed: the oak's furrows ragged and its breaks short slanting
   cracks, lichen fewer, smaller and greyer, the stream spot on clear ground looking along the brook.
2. `%TEMP%/backrooms-shots/47-r4b`: the models in place and reading as objects. The manor from the walk: slate roof with
   eaves and ridge, chimney pots, the porch on its posts, lamp posts with their lanterns hung over the walk; the door
   open in its oak frame with the Tudor head, strap hinges and studs; the great hall's hearth with fire, andirons,
   hearthstone and the mantel of candles, the trestle table set and lit, benches, sconces; the library's bookcases (books,
   scrolls, bottles) on three walls; the way-stone reads as a post with a snake coiling up it; the oak bark as furrowed
   bark; brackets and moss drapes on the trunks. Still wrong: the leaded windows' stone surrounds drew as ghosts (the
   translucent pass); the beard strands under the moss read as white sticks; the dead wood's bark strips as regular dark
   tiles; the tapestry spot looked at a trilithon (the north wall's tapestry is behind one from anywhere in the hall); the
   camp was behind a boulder from its spot (and its fire could lose its cell to a fern); the root plate's spot looked
   through a dead tree. All fixed for the third run.
3. `%TEMP%/backrooms-shots/47-r4c` (the final run): the windows solid, mullioned and barred in their surrounds (the door
   shot is the best of the level's); the World Snake tapestry shows, half behind a trilithon as everything in that hall is;
   the camp was still lost in ferns, read from the camera's own fern: after the run its site is trodden bare and cleared
   round the fire and the spot stands inside the clearing (not seen in a shot: the third run was the last). Still weak:
   the trunks' big flat faces between the fillets (the fillets round the notches only; a trunk of radius 3 still shows
   faces three blocks wide); the moss drapes read as flat green pads from a distance; the root plate's spot still looks
   past a dead tree; the dead trees' hollow mouths read nearly as before (the cleft's narrowing is a single block); the
   stream remains a narrow brook seen through mist.

Tally: A 17/17 done; B 12 done, 2 partly; C 5 done, 2 skipped.

### Checks (round 4, 2026-11-03 04:10, again at 06:10 after the camp fix: all the same)

expclash clean; mod and mapgen 0 errors; layouthash (seed 12345, 16000, `BACKROOMS_NO_EXP_ENTRANCES=1`, v1 and v12)
identical to main for levels 0-20 and the layout hash; `regions` 60/60 in Level 47; `47stats` ok (2.7 ms a cell, the
same zone shares, the trail walked with 0 in a wall); headless dummy in 47 (port 43221) with 0 problem lines;
`GATE_TAG=47g python tools/gate.py --fast --port-base 43220` PASS.

### Questions for the user (round 4)

Answered 2026-11-14: see OPEN-QUESTIONS.md (this list and the earlier ones). Manor windows stay opaque. Camp fires cold by default, alight in one camp in four (done, layout 16). Great Adder strike scaled by Danger, capped at 14 (done: 12 at the default).

1. The manor's windows are now opaque old glass (dark green-grey diamonds), since the translucent pass drew the stone
   round them as ghosts: keep them so, or would you rather have open leaded lattices (no glass, see-through)?
2. The wanderer's camp keeps its fire alight with nobody at it (the lore's things that "revert" or vanish, not yet): one
   cell in sixteen. Too often, too rare, or should the fire be cold?
