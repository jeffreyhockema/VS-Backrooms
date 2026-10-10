# The Mangled (Entity 63): design brief, second pass

## Sources
- Wikidot, "Entity 63 - The Mangled" (Spectre48 and Nikuchan, art by Poliacci): https://backrooms-wiki.wikidot.com/entity-63
  - "a spider-like creature roughly the size of a house, with a thick smokescreen masking its presence"; "a sudden temperature decrease in the air right before noticing the creature"; size reports disagree.
  - The misreading: "a massive tree ... the size of a giant redwood. Wait a minute. That isn't a tree - the bark is too black, and it has no branches or leaves." On camera: "a massive black pillar, reaching up far out of sight". The pillar vanishes leaving "a crater in the middle of the street" (a foot), with thunder (its steps). "It's so large, it's generating its own weather."
  - Body: "Faces. Merging together into a singular mass - a brain for this unholy thing"; "one face aside from the others ... screaming ... calling out to me".
  - Capture: "snatched by a tendril and lifted up into the sky". Its roar "is human speech".
  - The article's drawing (Tournesol's sketch, tournesoldrawing.png): thin, jointed, near-vertical black legs standing in a suburban street, the body lost in cloud, a knot hanging beneath it trailing curling tendrils.
- Wikidot, Level 9: https://backrooms-wiki.wikidot.com/level-9 ("Be aware of the foggy mist ... the fog being the spawning mechanism for The Mangled").
- Fandom, Entity 163 "The Mangled" (API wikitext; the page is Cloudflare-blocked): https://backrooms.fandom.com/wiki/Entity_163 . "A spider the size of a house? A giant tree?"; "several black limbs are walking ... the craters are just footprints"; dense black fog; a "tree" whose "gnarled branches stabbed into the gray sky, like countless hands".
- Fandom, Level 9 summary: https://backrooms.fandom.com/wiki/Level_9 .
- Miraheze: no Entity 63 / Mangled page (search returns nothing).

## Decisions
- A harvestman, not a tarantula: eight legs rise steeply to knees above the body (the crown), then drop near-vertical as long knotted black trunks tapering to points. In fog: a stand of black trees that do not belong.
- The brain hangs on a stalk under the front of the body (as in the sketch): a knot of black flesh with fourteen modelled human faces turned every way; one on its own lobe, paler, screaming (Clara). Two more faces sunk in the abdomen.
- Faces are geometry: mask, two brow halves (inner ends lifted in anguish), eyes (open eyeballs with irises, or shut lids), nose, cheekbones, upper lip, hinged jaw (talks, screams). Pale, cold-toned, each a different person; edges sink into the flesh.
- Seven tendrils from the knot's underside, curling outward and hooking back; three capture tendrils end in three hooked fingers.
- The cold: frost on everything that faces up. The smoke: left to the event's fog (cut-out smoke planes look like paper).

## Proportions (model px, 16 = 1 block; drawn x1.5)
- Knees 118-125 (11.5-11.7 blocks drawn), body 82-108, knot 51-76 (4.8-7.1 drawn), tendril tips 1-10.
- Feet on an ellipse ~59 x 54 px (5 blocks wide drawn; a Level 9 street is 8; the side legs are the widest).
- Legs 3.8-5 px thick (0.36-0.47 blocks drawn), the points 1.2-1.6.

## Palette
Bark black (14,12,14)/(24,21,22), ridges (50,43,42), cracks (5,4,6), street mud (58,50,42); flesh (30,23,25), wet maroon (86,30,40), frost (122,126,134); skins ash/cold/warm/sallow/grey/pale; lips (122,86,90); mouth (34,8,12); teeth (206,196,172); irises brown/blue/grey/green/milk.

## Parts (314)
Body, Carapace, Crest, Abdomen, AbdomenTip, Brisket, Belly, 18 Lumps; 8 legs x (Hip, Femur, Knee, Tibia, Ankle, Meta, Spur, Tip); Stalk, StalkSinew, Knot, 13 KnotLobes, Lobe0; 16 faces x (Face, Brow a/b, Eye or Lid a/b, Nose, Cheek a/b, Lip, Jaw); 7 tendrils (9/9/9/6/6/7/5 segments), 9 Claws, 9 Hooks.

## Animations
walk (120 f: one leg at a time in the order L1 R3 L2 R4 L3 R1 L4 R2, a lift, hang and slam each 0.5 s; body rolls off the lifted leg and settles on the footfall; the knot swings; faces murmur), run (64 f, two legs in the air), idle (150 f: breathing, the knot turning, all the jaws talking, faces surfacing), despair (100 f search: the knot swings out and turns, every face pushes out of the mass, capture tendrils lift and feel forward), attack (27 f: coil back, lash forward-down to 3 blocks model / 4.5 drawn at frame 11-13, fingers close at 15, haul up overhead by 23), hurt (16 f: every mouth opens), die (60 f: the legs buckle in order, the body comes down, the legs curl up like a dead spider's).
