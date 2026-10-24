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

See the table at the end of this file (filled in as each is done).

| Entity | Type | State |
|---|---|---|
| Hound | quadruped | Redone 2026-10-24: the arms buckle and the chest drops onto the forearms, the hips drop onto the folded legs, it tips onto its left side, rocks and settles; arms reaching forward past the head, knees drawn up, top limbs fallen across the lower, hair spilled over the face. 42 frames, 9 keyframes. |
