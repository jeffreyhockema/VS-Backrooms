# Brief: the Bacteria (Howler, "the Lifeform"; Fandom Entity 1)

## Sources
- Fandom Entity 1 / Kane Pixels wiki (blocked to fetch; via search summaries): "very tall, thin and vaguely humanoid in
  shape, standing on two legs"; "limbs are very thin and stiff, but it can still move fast and quietly"; "the arms reach
  the floor and it has long, thin fingers, while its legs are relatively short and lack feet"; "a cable-like string wraps
  around the body and legs"; "seems to 'come to life' from a black substance resembling mold". While chasing it makes
  "a loud noise similar to distorted screaming or howling", sometimes words ("Wait, don't go!", "No, please!").
  https://backrooms.fandom.com/wiki/Entity_1 , https://kanepixelsbackrooms.fandom.com/wiki/The_Lifeform
- All Species wiki (Bacillus sapiens, via search summary): "around eleven feet", "two long arm-like limbs extending down to
  the ground, thin skinny fingers, and a slim vine-like anatomy akin to a tangle of black wires shaped into a humanoid
  form"; "movements appear stiff and mechanical"; ambushes from walls/ceilings, mimics voices.
  https://allspecies.fandom.com/wiki/Bacillus_sapiens
- The Ghost in My Machine timeline: "tall and spindly, and seemingly wrapped in wires", limbs "like... a tripod", head
  "resembles a camera"; black tendrils "appearing around corners"; it snatches Kane up and holds him aloft.
  https://theghostinmymachine.com/2022/06/13/backrooms-found-footage-an-updated-timeline-continued-exploration-of-kane-pixels-backrooms-universe/
- Taylor Holmes: "made of something dark and vine-like, all elongated limbs and bent torso"; it charges; screams made
  from edited chimpanzee audio. https://taylorholmes.com/2026/05/29/explaining-the-backrooms-youtube-videos-prior-to-watching-the-movie/
- A-Sync wiki (fan): "a long, black humanoid entity made from the wires of the ceiling of level 0", claws.
  https://a-syncbackroomsinvestigationwiki.webador.es/entity-1-bacteria-monster

## Conflicts and choices
- Height: "eleven feet" (~3.35 blocks, 54 px) vs Level 0's 3-block (48 px) headroom. Choice: ~54 px of body that cannot
  stand straight: it stoops (bent torso, head pitched forward on a long neck), so it stands ~45 px, the crown just under
  the ceiling tiles. Too tall for the room is the point.
- Gait: canon is bipedal ("standing on two legs"), stiff, fast. Walk: a stiff, stepped stride with hands dragging on the
  carpet. Run: the "charge", torso pitched far forward, the floor-length arms clawing at the carpet in turn like front
  legs (lurching), short legs scrabbling.
- Head: canon is faceless; one reading says camera-like. Choice: a small faceless lump pitched forward with a darker
  hollow at the front (a lens / socket, not an eye), loose wires off the crown, and a jaw seam that splits for the howl.
- No glow (nothing in the lore glows).

## Proportions (model px, 16 = 1 block; facing -X)
- Hips at y 16.8; legs ~17 px, footless, ending in frayed root-like strands.
- Torso (waist 7.4 + chest 10.6) leaning 18 deg; shoulders ~9.6 px across, hunched high; neck 4.6 px craned forward.
- Arms ~28 px + hand 2.2 + fingers 6.4 (4 per hand, 2 joints): the fingertips reach and splay on the carpet.
- Every limb is a bundle of 2-3 parallel twisted strands (0.3-0.9 px); cable wraps on thighs and chest; loose wires
  hang from shoulders, elbows, hips and head, their ends cut ragged to transparency.

## Palette
Near-black base (16,15,13); fibre (31,29,25); wire glint (64,60,50); deep (5,5,5); olive mould (26,28,18);
cable wrap (38,34,28). Stain: black centre, olive-black fuzzy rim, transparent ragged edge.

## Parts and animations
Hips root; waist, chest (+ribs/strands, wraps), shoulders L/R, neck, head (crown, lens, jaw, wires); arms (upper,
forearm, hand, 4 fingers x 2 joints, extra strands, tendril) L/R; legs (thigh, shin, root strands, wrap) L/R; floor
"Stain" root part buried under the floor at rest (shown only by emerge/die).
Animations: idle, lurk, walk, run, attack, hurt, die, emerge (+ howl).

## As built
- 106 parts, texture 128x256 (TEXEL 2), no glow. Stands 44.2 px (2.76 blocks) to the crown, under Level 0's 48 px
  ceiling; hips 15.6, shoulders ~35, arms 14.5 + 14.4 + hand 2.4 + fingers ~6.5, fingertips resting on the carpet.
- Animations (30 fps): idle 150 (loop), lurk 180 (loop), walk 40, run 20, attack 30 (grab closes on frame 13,
  damageAtMs ~440; hands 1.6 blocks ahead at chest height), hurt 15, die 60 (Hold, sinks into the stain), emerge 75
  (emergeMs 2500; arm poses solved numerically so the hands stay planted while it hauls itself out), howl 45.
- Recommend: hitbox 0.7 x 2.8, eyeHeight 2.55, attackRange ~2.0.
