# Level Fun entity models: lore brief

## Sources
- Wikidot Entity 67 (current rewrite): https://backrooms-wiki.wikidot.com/entity-67
  - "tall, bipedal ... smooth, leathery skin", "typically ... bright yellow", "a carved smiley face smeared with blood that perfectly matches the grin of a Phobic Centipede", legs of "a thick, blocky shape", "The chest area is shielded by a subtle carapace", "long, noodle-like arms that end in sucker mouths full of hooked teeth".
  - Berserker: "A hidden chest carapace ... flipped open, and a pair of anomalous arms with powerful clawed hands shot out". The insides are "human, Phobic Centipede, and crustaceans". A corpse was seen "slowly walking away on little centipede legs".
  - Interns "carry a floating red balloon, seemingly tied to their arm by a cord or string".
  - Party Hosts are created when "A Partygoer will mistakenly bite a Faceling". "The Party Hosts are immobile". They shed "LUCA tears". The plan notes the line "Once Party Hosts turn golden, they are perfect".
  - Canon images viewed:
    - `partygoerdarla.jpg` (Daniel Kebab's first sketch): a Gumby slab with no neck and a rounded top that slants to one side; bent noodle arms ending in round red discs with a star of teeth; blood under the grin; long square-ended legs.
    - `Berserker.jpg` (Myra Oberlyn): a door-like chest plate lined inside with hooks; pink cavity; the green inverted face of the centipede; a black centipede body; long grey-black whip arms ending in 3 sickle talons.
    - `FUNposter.jpg`: the "=)" drawn as two horizontal dashes and a paren, which supports the user's face.
- Wikidot Entity 134, Phobic Centipede: https://backrooms-wiki.wikidot.com/entity-134. It is "a non-reflective black", with the "head and face of a smiling woman ... eyes softly glowing white", and its arms "materialize from the center of its abdomen ... strike targets several meters away".
- Wikidot Level 26 "SS Fun =)": https://backrooms-wiki.wikidot.com/level-26. "a huge monster filling the ceiling. It looked like a golden fried egg with an eye-and-mouth combination in the middle. Partygoers were feeding an inverted Faceling, alive and feet first, into the maw."
- Fandom Entity 67 ("Sanguine Festivus", via the API): https://backrooms.fandom.com/wiki/Sanguine_Festivus. A different canon: virus-infected husks under yellowed sheets with a "smile-like stain". Not used, except as support for the stain-smile and the wading gait.
- Miraheze: no Partygoer page (the site search for "partygoer" finds nothing), and Level Fun is a joke page. No second opinion there.

## Verdict on the Party Host
The Host is lore, not an invention. The plan's design is right. The important detail it missed is that the eye and the mouth are ONE organ, and a maw wide enough to take a Faceling. Facelings are faceless and pale, so the "white" is pale flesh.

## Keep
- The face grid and Face* geometry, exactly as they were.
- Every code and every animation code.
- The variant palettes.
- The carapace plate names and the claw-arm names.

## Change (16 px = 1 block)
**Partygoer (36 px tall)**
- Canon proportions:
  - Legs are 16 of the 36 px: thigh 8, shin 7.4, sole 1.2, and the crotch is at 16. Before: 13 px, crotch at 12.
  - The torso is 7 px. The head and face stay at y 25–36.
  - The arms leave the body at y 23.8, just under the face.
- Arms:
  - Thicker: 2.0 → 1.6 px over 4 links, 17.8 px long.
  - The rest pose bows the elbows out by about 2.7 px and brings the mouths back in by the shins.
  - The mouths flare into a 3 px lip with a star of teeth and 6 hooked teeth.
- Chest:
  - The cavity is real: the front 1.4 px of the torso is a frame of skin around a 5.8 × 5.2 opening, with flesh walls.
  - The two doors are lined inside with hooks, and their outer faces are banded amber.
  - Inside: the black centipede, its inverted pale grinning face with two eyes at glow 200, and the folded claw arms.
- Claw arms:
  - Black with a grey-blue sheen: upper arm 5 px, forearm 5.2 px, hand 1.5 px, and 3 sickle talons of 2 segments each. The reach is about 14 px.
  - Folded fully out of sight at rest. When berserk opens, they swing out of the open chest, never through the face.
- Skin: brighter and cleaner. A soft vertical grade, rounded slab edges, and fainter creases.
- Head top: a gentler -10° Gumby roll with a brow and crown, instead of a box that floated above the head.

**Lure balloon:** a rounded latex egg made of 6 layers, 6.6 × 7.6 px, centred at y 24.5 (head height). Glossy shading with one highlight per face. The string hangs in 3 lagging links.

**Party Host (48 px across):**
- A pale fleshy white with blisters, veins and a crisp golden lace edge.
- A 3-tier glossy gold dome.
- At its crown, the eye-and-mouth organ:
  - an almond eyeball with a large red-gold iris;
  - a lashed lid on one side and a toothed jaw on the other;
  - a dark throat behind.
- `upset` gapes the lid and jaw apart and rolls the eye back, so the organ becomes a maw.
- 10 glowing LUCA tears hang from the corners of the eye and from the tiers.
