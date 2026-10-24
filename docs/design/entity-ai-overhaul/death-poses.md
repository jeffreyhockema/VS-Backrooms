# Death poses: the standard

Written 2026-10-24 after the play-test note on the Hound ("just the Hound in its standing position, knocked over on
its side, with the legs sticking straight out"). Every killable entity's `die` animation is held to this. The body
lies where it fell until it decays or is harvested, so the last frame is the one the player looks at longest.

## What a good death reads like

A death is a **collapse with weight**, not a model tipped over.

1. **The hit** (2-5 frames): a flinch or a stiffening, the head jerking, the jaw dropping. Small.
2. **The give**: one end goes first. A quadruped's front legs buckle at the elbows and the chest drops onto them, or
   the hind legs give and the hips sit; a biped's knees go. The feet stay planted while the joints fold: what was
   holding the body up folds under it.
3. **The fall**: the body drops and rolls or slumps onto its side, chest or back. This part is fast (6-8 frames);
   falling is not slow.
4. **Impact and settle**: a little past the rest pose on impact (a few degrees more roll), a rock back, then a few
   frames of settling as the limbs go slack. **The head drops last**, onto the floor.
5. **The rest pose** (held): every joint relaxed and a little different from its partner. Upper and lower limb bent at
   different angles, paws, hands and claws curled, the spine slightly curved, a tail limp along the floor, the jaw
   slack. Limbs on top fall across the ones beneath them; limbs underneath lie flat on the floor. Nothing rigid,
   nothing symmetrical, nothing sticking up into the air.

**Contact.** At every keyframe after the hit the body is on the floor: the lowest solid part at the floor (y = 0, or
a quarter pixel into it so it does not hover), never floating and never sunk into it. In the held pose the torso
itself rests on the floor or on the limbs under it (a pixel or two up, propped on a shoulder, is natural; five is
floating). Hair, cloth, wings' membranes and other soft parts may bend where they meet the floor and do not hold the
body up, but they should lie along it, not pass through it.

**Timing.** 0.8-1.5 s to the rest pose at 30 frames a second (24-45 frames at `animationSpeed` 1). Vanilla's wolf is
51 frames with 10 keyframes, its bear 90 frames with 6; ours use 6-12 keyframes.

**Easing.** The game interpolates keyframes linearly, so easing is made with keyframe spacing: keyframes close
together where the motion starts or stops (the hit, the impact, the settle), further apart through the fall, and a
small overshoot and rock back rather than stopping dead.

## By body type

- **Quadruped** (Hound, Death Rat, Clump): front buckles or hind gives, the body tips onto its side (rolling 80-95
  degrees about the spine), the legs folded and loose: on the side the body lies on they lie on the floor, on the top
  side they fall across them. Knees drawn a little toward the belly, elbows bent, paws curled. Back slightly curled,
  head on the floor, jaw open, tail along the floor.
- **Biped / humanoid** (Skin-Stealer, Duller, Wretch, Beast, Mangled): the knees go, the body folds at the hips and
  falls forward (onto the chest, turned a little to one side) or sideways; the arms do not stay at its sides: one
  under the body or out to the side, one bent near the head. The head turned to one side on the floor. A crumple to a
  kneel that ends kneeling is a stun, not a death: it ends lying down.
- **Insect / arachnid** (Giant Spider, Deathmoth on the ground, Bacteria): the legs curl in under the body, the tips
  toward the middle, as a dead spider's do; the body settles onto the floor (on its back for an insect if it fits the
  lore). Legs curled, not straight up.
- **Flier** (Deathmoth): stops flying where it is, falls out of the air (`airborne` keyframes, accelerating: the
  keyframes closer together as it falls), lands with a small bounce, the wings folding or splaying flat on the floor.
- **Blob / amorphous** (Clump's body, The Thing if it ever dies): sags and spreads: stretched wide and low (`stretch`),
  sliding down onto the floor, a last quiver.
- **Mechanical** (Roboman): seizes (a stiff jerk, joints locking), then topples as one piece onto its side or front,
  bounces once, a last twitch of one joint. Rigid is right here.
- **Stop-motion** (Level 94's clay, wooden and paper figures): the same reading in held poses, ten a second, with no
  easing, as everything else they do.

## How it is made

- On death the game plays the client animation with `code: "die"` (`triggeredBy: { onControls: ["dead"] }`), and the
  shape's animation has `onAnimationEnd: "Hold"`, so the last frame stays while the body lies there. The last keyframe
  must be frame `quantityframes - 1`: past the last keyframe the game interpolates back toward frame 0.
- An animation offset is applied *inside* the element's rotation (`ShapeElement.GetLocalTransformMatrix`): moving a
  rotated root down needs the move turned back through its rotation. `rig.settle(model, keyframe, floor, ignore)` does
  this (it moves the root so the lowest drawn box sits at `floor`), and `rig.posed_extent` gives a pose's lowest and
  highest point.
- `gen_models.death(m, frames, names, keys, floor=-0.25, airborne=(), standing=(), soft=())` writes a death to this
  standard: every keyframe names every part, every keyframe but frame 0 is settled onto the floor (frames in
  `standing` onto the rest pose's own lowest point, so the feet do not pop; frames in `airborne` are left in the air),
  and parts in `soft` do not hold the body up. Write the poses as joint rotations; let `death` put the body on the
  floor.
- Shapes are generated: change the generator (gen_models.py, gen_beast.py, gen_spider.py, gen_watch.py,
  gen_fun_models.py, gen_entities.py for the Facelings) and run it for that model; never hand-edit the JSON.
- Element names and animation codes are referenced by code and saves: do not rename them. Other animations do not
  change.

## Checklist

- [ ] Starts from the rest pose at frame 0 and ends on frame `quantityframes - 1`, `Hold`.
- [ ] 24-45 frames at speed 1 (0.8-1.5 s), 6-12 keyframes, spaced for easing; an overshoot and a settle.
- [ ] One end gives first; the feet stay on the floor while the legs fold; the head lands last.
- [ ] Every keyframe after the hit has the body on the floor: lowest solid part at 0 to -0.3 px, nothing below -0.5.
- [ ] The held pose: torso on the floor (or propped a pixel or two on the limbs under it), limbs folded at the joints
      with upper and lower parts at different angles, left and right different, paws/hands curled, spine curved, jaw
      slack, tail and hair along the floor. No limb sticking straight out or up.
- [ ] Looked at from several sides and from above at the held frame, and at the frames between keyframes.
- [ ] No other animation changed; no element or animation renamed.

## Where each entity stands

Audited and upgraded 2026-10-24. Before/after sheets for each are in `previews/death-<entity>-before.png` and
`-after.png`, and `previews/death-contact-sheet.png` shows every death (frames 0, a third, two thirds and the held
frame from the side, the held frame from two angles above).

| Entity | Type | State |
|---|---|---|
| Hound | quadruped | Redone 2026-10-24: the arms buckle and the chest drops onto the forearms, the hips drop onto the folded legs, it tips onto its left side, rocks and settles; arms reaching forward past the head, knees drawn up, top limbs fallen across the lower, hair spilled over the face. 42 frames, 9 keyframes. |
| Skin-Stealer | biped | Redone: 40 frames, 11 keyframes (was 30/4, a kneeling ball 6 px in the floor). A jolt, the knees go over planted feet, it kneels folding at the hips, pitches onto its chest turned onto its left side, arms flung out, rocks and settles: left arm out along the floor, right hand by the face, right knee drawn up, head on its cheek, jaw open. Held pose -0.25..5.8 px. |
| Duller | biped | Redone: 40 frames, 12 keyframes (was 36/4, a ball 16 px in the floor). One knee gives, it lurches, the other caves, it kneels, a hand hits the floor with the elbow buckling, and it pitches onto its chest rolled onto its right side, wobbling twice like something badly put together: the long right arm out along the floor, the left bent round the head, a knee drawn up. Arm extensions stay retracted. Held pose -0.25..5.8 px. |
| Death Rat | quadruped | Redone: 36 frames, 10 keyframes (was 24/5, sank onto its belly in the standing pose). A jerk, the front buckles, the haunches give, it rolls onto its left side, rocks and settles: paws drawn in, the right legs across the left, back curved, tail limp in a curve along the floor, head down last, jaw open. Held pose -0.25..8.2 px (whiskers soft). |
| Deathmoth (male, female) | flier | New (had none, though killable): 34 frames, 10 keyframes. A last spasm with the wings up, the wings close over the back, the legs give and it topples onto its side, slaps down, bounces once and settles: wings shut like a closed book along the floor, legs curled in, head bowed, antennae limp. Registered as `die` in the deathmoth entity for both genders. Held pose -0.25..4.0 px. The game's butterfly client code keeps its fly loop going on a dead moth (see below). |
| Wretch | biped | Redone: 40 frames, 12 keyframes (was 40/8: face down but both legs straight and parallel, 2.7 px in the floor mid-fall). Knees go, it sways on its knees, pitches forward with the left elbow buckling, lands face down turned onto its left side, rocks and settles: one arm past the head, one by the face, a knee drawn up, head on its cheek; the eyes still. Held pose -0.25..6.9 px. |
| Beast of Level 5 | biped | Redone: 40 frames, 12 keyframes (was 40/6, ended kneeling with its claws 5 px in the floor). A jolt with the wings and tentacles flaring, the knees go with the feet planted, he pitches forward over his knees bracing on a hand, lands face down rolled onto his right side, rocks and settles: a hand by the head, a knee drawn up, wings slumped open, tentacles and beard limp along the floor (soft). Held pose -0.25..6.8 px. Both looks share it. |
| Clump | blob / many-legged | Redone: 40 frames, 9 keyframes (was 40/6, 7 px in the floor). A jerk, a leg gives, the mass sags wide and low (stretched), the limbs go slack and splay along the floor each at its own slope and bent at the joints, flaps hanging open, fingers curled. Held pose 0..9.8 px. |
| Giant Spider | arachnid | Redone: 60 frames, 15 keyframes (was 60/6, 6 px in the floor, legs stiff). It stiffens, loses its footing, rolls over onto its back, rocks, and the legs curl in over the belly a pair at a time, knees up and tips hooked toward the middle, palps up, jaws slack. Held pose -0.25..21.3 px. Keyframes close together through the roll keep it on the floor (worst in-between -1.6 px). |
| Bacteria | thin biped | Redone: 60 frames, 11 keyframes (was 60/11, ended 27 px below the floor). A convulsion with the head snapping back, the knees go, it topples forward, lands a little past, rocks and goes slack: prone, arms splayed in different bends, legs trailing bent, head turned, fingers curled; the stain keeps spreading. Held pose -0.25..12.3 px (wire loops). |
| The Mangled | many-legged | Redone: 54 frames, 12 keyframes (was 60/6, a heap with legs and spines standing up). Every mouth gapes, the legs buckle one after another, the body falls from 123 px to the floor, the legs thrown wide on impact, a rock, then the legs fold into loose zigzags lying along the floor, no two alike; the stalk swings the knot of faces down beside the body; tendrils, claws and hooks soft (worst in-between: a leg tip 2 px into the floor). Held pose -0.25..37.1 px; the folded legs still span about six blocks. (Its own comment says it never dies; the animation is there all the same.) |
| Neighborhood Watch | eye on legs | Redone: 40 frames, 8 keyframes (was 40/5, the eye held 13 px up on stiff legs). The eye jerks and the pupil pinches, the legs buckle with the feet planted and slide out, the eye drops onto the floor and rolls about 100 degrees to look up and aside, the legs arched and bent at different radii, points curled in. Held pose -0.25..23.4 px (the nerve, soft, dips 5 px into the floor for a frame mid-fall). |
| Faceling (and child) | humanoid | Left: the seraph body kneels and falls forward over 120 frames, 9 keyframes, ending on the floor (-1.3 px). It reads like a person collapsing; it could be quicker. |
| Partygoer (and intern) | costume shell | Left: a deliberate beat (60 frames, 15 keyframes): it topples stiffly onto its face (it never flinched alive), the carapace heaves twice, a leg twitches, and something small walks out from under it. On the floor (-1.7..6.1 px). |
| Roboman | mechanical | Left: seizes and topples rigid in stepped stop-motion poses (27 frames, 18 keyframes), on the floor (-0.5 px). Rigid is right for a machine. |
| Clay, wooden and paper figures (Level 94) | stop-motion | Left: they crumple and fall in held poses ten a second, as everything they do, ending on the floor (clay -1.1, wooden 0, paper 0.2 px). |
| Smiler, Watcher, The Thing, Kitty, the Keymaster, the Attendant, the Party Host | | No death: they have no health and cannot be killed. The Level 188 arm counts blows instead of dying, and the lure balloon pops (both are removed). |

**Known in-game gap.** The Deathmoth is the game's butterfly entity underneath (`EntityDeathmoth : EntityButterfly`), whose client tick restarts its fly loop whenever no feed or rest animation is playing, alive or dead. A dead moth will likely play `die` (weight 10) blended with the fly loop (weight 1): a small shiver of the shut wings. Fixing it needs the client tick to skip the butterfly's flight handling once the moth is dead; not done here (behaviour unchanged).
