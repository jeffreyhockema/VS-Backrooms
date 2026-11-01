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

## 7. Screenshot cycles

(below)
