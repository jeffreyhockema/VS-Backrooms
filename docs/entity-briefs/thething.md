# The Thing on Level 7 (Entity 20): model brief

## Sources
- Wikidot, Level 7 (primary): https://backrooms-wiki.wikidot.com/level-7. The Thing lives in the Midnight Zone and upper Abyss. It "appears to have killed off any other life in the ocean". "Its life in perpetual darkness makes its eyes much more sensitive to light", so light drives it off. It shares the sea with Tiny (Entity 720, shallows). The page gives no description of its body.
- Miraheze, Entity 20: https://backrooms.miraheze.org/wiki/Entity_20. "A huge fish or sea monster". Its "mouth alone is 825 feet tall ... when opened" (the page says this is exaggerated). It eats everything and is territorial.
- Fandom, Entity 20: https://backrooms.fandom.com/wiki/Entity_20. The page blocks fetching, so this comes from search summaries. A fish-like creature, the only one of its kind, its body "more closely resembles an eel", about 11 km long.
- Backrooms Pantheon, Entity 20: https://backrooms-pantheon.wikidot.com/entity-20. A predatory fish about 35 m long with massive jaws and barbed teeth. Its jaw dislocates forward to snap. It has "many spikes ... especially on its tail", poor light-sensitive eyes, and a yellow lure.
- Fan versions: http://faithfulbackrooms.wikidot.com/entity:ttol7 ("colossal, shadowy shape", glowing eyes, "large, murky eyes surface beneath swimmers", tendril-like limbs or long fins) and https://sites.google.com/view/backroomsentitydatabase/home/the-thing-on-level-7 ("eel-like creature").

## Conflicts and the baseline chosen
- Size: the sources range from 35 m to kilometres. The model is 11 blocks long, and its look is "too big to take in", not a literal scale.
- Body: some versions are an anglerfish or viperfish, others an eel. I chose an eel-like leviathan, which most sources agree on. From the fish versions it takes a huge undershot jaw, needle teeth and spines.
- Lure: left out. A bright lure works against the canon point that its eyes are hurt by light. A faint glow on the barbel tips and dim photophores stand in for it.

## Design decisions
- Thalassophobia first. At a distance it is a long dark silhouette with a dim row of photophores. Up close you see the face: milky, cataract-clouded eyes, and too many of them, placed differently on each side (the "something wrong"). Pale needle teeth show even when the mouth is shut (an overbite along the cheeks, fangs up the front). When it rises at you, you see the pale belly and the red throat.
- The jaw is undershot and hinged far back. Open, it gapes about 58 degrees, enough to swallow a person.
- Scars from what it killed: claw rakes in threes, and sucker rings.

## Proportions (model px, 16 = 1 block)
- Length about 178 px (11.1 blocks). The root is at the middle of its length, at the hitbox centre (spine at y=10).
- Head: skull 31x20x26, snout 10x13x20, jaw 40x11x23. Head and jaw together are 34 px tall (2.1 blocks).
- Body: 10 segments, spaced 12 px apart and 14-15 px long. They taper from 28x25 to 6.5x4.5 in cross-section.
- Main eye 6 px. Fangs up to 9 px. Dorsal ribbon up to 7.5 px. Tail spear 28x26.

## Palette
| Use | RGB |
|---|---|
| Back | 7,8,12 |
| Flank (blue-black) | 16,19,26 |
| Slate mottle | 36,42,54 |
| Belly (dirty ivory) | 112,110,102 |
| Scars | 96,100,104 |
| Mouth | 104,54,62 |
| Gums | 156,106,106 |
| Teeth | 224,218,198 |
| Eyes (milky) | 208,218,212 / 140,160,166 |
| Photophores (glow 95) | 150,212,200 |

## Parts (135)
- 10 body segments.
- Head: skull, snout, sloped forehead, brow, gullet, jaw.
- 50 tooth parts (long teeth have curved tips).
- 7 eyes and 2 lids.
- 6 barbel parts (the tips glow).
- 4 pectoral fin parts.
- 4 shoulder spines, 8 dorsal and 5 ventral ribbon parts, 1 tail spear.
- 22 photophores.

## Animations
- `swim`: 90 frames, loops. A slow wave travels head to tail. The middle holds course and the body rises and falls slightly. The jaw works, the fins ripple, and the pectoral fins scull.
- `rush` (new): 30 frames, loops. A quick, deep wave with the mouth open about 32 degrees and the fins and barbels laid back.
- `attack`: 36 frames, plays once. It draws back into an S with the jaw dropping, lunges about 1.5 blocks forward with the mouth fully open, snaps shut at frame 15, shakes its head, and settles.
