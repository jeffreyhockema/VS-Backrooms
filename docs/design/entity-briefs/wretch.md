# Wretch (Entity 15): design brief

## Sources
- Wikidot, Entity 15 "Wretches" (primary): http://backrooms-wiki.wikidot.com/entity-15
  - "reddish-brown skin that is dry and flaky, covered in holes and pustules secreting a thick red-brown substance"; skeletal yet able to break through walls.
  - Cause: deprivation of food, water and sleep (the Wretched Cycle), weeks to months.
  - Stage 1: itch like poison ivy, then erratic, aggressive behaviour, a change of personality (reversible).
  - Stage 2: "skin and muscle tissue will begin to dissolve ... developing orifices and pustules"; itching "unbearable", some "scratching layers of their skin off"; eyes bloodshot; hair loss; speech only "pleas for water, food, and help".
  - Stage 3 (no return): "nails and teeth fall out ..., often regrowing elsewhere in unnatural quantities and sizes"; "eyelids, lips, and cartilage dissolve, forcing the eyes to remain open constantly and roll wildly in their sockets"; "constantly ooze a brown sludge-like substance from mouths and other orifices".
  - "clothing, supplies, and personal belongings will remain on the body, though often mutilated beyond recognition".
  - Behaviour: usually little intelligence, great strength; "slow shamble to sprints surpassing human capabilities"; gurgling and snarling (low and slow = dumb, high = clever/fast); some wield weapons; groups act in unison; live "in the shadows wherever humans gather".
  - Rare mutations (misplaced eyes, extra limbs, flesh "wings", a mass of eyes and mouths): not modelled; candidates for rare variants.
- Miraheze (https://backrooms.miraheze.org/wiki/Entity_15) has a different canon ("Insanities": dark red skin "as if the outer layer peeled off", a big toothy smile, eyes "popped out ... moving around constantly", stages 0-4). Used only to confirm the peeled red skin and the roving eyes.
- Fandom (https://backrooms.fandom.com/wiki/Entity_15, blocked; search summaries): "human-like ... acts like an undead zombie ... seeking water, sleep, and food", wandering aimlessly; also made by Entity 112 eye contact and the Beast of Level 5.

## Design decisions
- Once a person: shirt rags, jeans with a cinched belt, one sneaker / one bare foot, a backpack strap with a torn pouch (a red-and-white keyring tag on it).
- Starved and bent nearly double: waist 14 + chest 22 forward, neck 40 more, head back 70; spine and shoulder blades stand out as parts; knees bent.
- Face: no lips (gum and uneven teeth bare, one too long), no nose (two holes), ears shrivelled to stubs, lidless bloodshot eyes with diverging pupils in deep sockets under a heavy brow, a few strings of hair, three teeth growing from the left cheek, a nail growing out of the left forearm, a slack jaw (22 open) with brown sludge hanging from it.
- Pustules as real bumps (6), holes painted as pits that drip sludge, flaking and cracks, claw-mark scratches.
- Distinct from the others: warm red-brown (Skin-Stealer pale yellow, Duller grey, Smiler black), upright on two legs (Hound on all fours).

## Proportions (16 px = 1 block)
- 28.9 px tall hunched (1.8 blocks), ~32 if straightened. Hips at 14.4, chest 3.8 x 5.3 x 5.4, waist 2.6 x 4 x 4, head 4 x 4.4 x 4 (+crown), arms 7 + 7.6 + hand 2.1 + fingers 2.9 (hang to the knees), legs 7.2 + 6.8.
- Recommended hitbox 0.65 x 1.8, eyeHeight 1.6.

## Palette
Skin (136,70,50), shadow (86,40,30), raw (168,58,46), flakes (200,156,124), holes (26,9,7) with rim (100,28,22), pustules (214,174,88), sludge (84,52,22)/(140,98,48), gums (112,34,34), teeth (206,186,138), nails (178,158,114), sclera (212,166,148) with veins (182,30,30). Shirt off-white (160,152,134), jeans (66,84,112), sneaker (176,168,150), webbing (56,66,72).

## Parts (70)
Hips, Belly, Chest, SpineLow/High, BladeL/R, Collar, Neck, Head, Crown, Brow, Face, Bridge, EyeL/R, EarL/R, Maw, Jaw, ToothU0-3, ToothD0-2, CheekTooth0-2, HairA/B/C, Drool, DroolB, arms (Arm, Forearm, Hand, Finger0-2, Thumb) x2, legs (Thigh, Shin, Knee, Foot) x2, TrouserRagR, RagFront/RagFront2/RagSide/RagBack, Strap, Buckle, Pouch, PusA-F.

## Animations (30 fps)
idle 90 (loop), walk 48 (limping lurch, dragging the bare foot), run 24 (bent sprint, arms grabbing forward in turn), attack 30 (rear, lunge, rake, bite shut on frame 13 = ~430 ms, tear), hurt 12, die 40 (held: reels, kneels, falls on its face, one hand reaching), huddle 180 (6 s: squats hugging its shins, rocking; scratches its forearm), gnaw 60 (crouched, hands at the mouth, ripping and chewing, glances up), snarl 36 (alert: rears, arms out, gapes, shudders). Eyes roll in every loop.

## Looks (same atlas)
- common (wretch.png): stage 3; the shirt in rags across the shoulders, ribs bare, jeans torn at the knees, left sneaker only.
- early (wretch-early.png): stage 2; whole blue t-shirt and khaki trousers, boots on both feet, sallow skin with a red rash and fresh scratches, few holes, eyelids, thinning hair, a cracked lip, no sludge.
- fargone (wretch-fargone.png): deep stage 3; no shirt but its collar, hanging flaps of its own skin where the rags were, black rotten trousers, split sneaker, darker skin full of holes and pustules, yellowed eyes, bald, brown teeth.
