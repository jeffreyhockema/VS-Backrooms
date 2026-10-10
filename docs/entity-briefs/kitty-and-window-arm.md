# Model briefs: Kitty (Level 974) and the Window's arm (Level 188)

16 px = 1 block. Models face -X, left +Z, up +Y.

## 1. Kitty (`l974-kitty`)

**Sources (fetched 2026-10-09/10)**
- Wikidot, Level 974 "Kitty's House": https://backrooms-wiki.wikidot.com/level-974
  - "a 3.2m tall, humanoid entity with unnaturally long, lanky limbs which lack hands or feet."
  - "skin is matt-black and has a texture similar to that of mosou black fabric."
  - "lack any semblance of facial features".
  - "travels smoothly and swiftly ... appearing in close vicinity"; it stalks people as they explore and rest.
- Wikidot photo `newkitty.jpg` (http://backrooms-sandbox-2.wikidot.com/local--files/fragment:andromedeadwips-1/newkitty.jpg), "Kitty standing in the bedroom", which I looked at. It shows:
  - a flat black cut-out;
  - an egg-shaped head carried forward of the shoulders on a short, thin neck;
  - shoulders that slope (they are not square);
  - a narrow torso;
  - arms hanging close to the body, tapering, with no hands, reaching well below the crotch;
  - very long legs, close together, thinning to the ankle.
- Fandom (via the 974 plan, §1.4): a shapeshifter; it holds out its arm "as if it were asking for something".
- Escape the Backrooms (https://www.playnews.gg/en/guides/escape-the-backrooms-the-walkthrough-for-the-secret-levels-the-bunker-overgrowth-the-grassrooms-level-974): tall, lanky, pitch black, no features or clothes. Its two white eyes are not canon, so they are left out.

**Verdict.** The current design matches the Wikidot brief: 51 px tall, faceless, matt black, limbs ending in points, and no walk cycle. Everything below is a quality change; none of these points changes.

**Keep**
- the height and all the limb lengths;
- the flat cloth texture;
- every part name and every animation code.

**Change**
- **Shoulders.** The two square blocks become slabs sloping 17° down from the neck, as in the photo.
- **Hunch.** A new part, 1 × 4.4 × 6 px, sits between the shoulder blades, so the side view has the stoop.
- **Head.** It becomes an egg: a core of 4.4 × 5.4 × 4.0, with a cap, chin, brow, crown and cheek slabs set in 0.5 px. The top is at y 51.1.
- **kneel.** It was floating, with the arms through the floor. Now the thighs lie along the floor (y 0.6–5), the shins are folded under them, the forearms rest along the thighs and the points hang over the knees.
- **take.** Both forearms now cross in front of the breastbone, and the head bows.
- **Lag and overshoot.** ask (the forearm lags), headtilt (it overshoots, then a listening turn), and stoop, peek, sleepwatch and kneel all get easing keys.
- **idle.** Adds a sway of the weight, a turn of the head, and curls of both arm points at different times.
- **glide.** The arms trail less, and the points trail a little more.
- **vanish/appear.** The neck lifts and the arms tuck in, together with the 1.05 stretch.

**Counts:** 31 parts (was 30) and 11 animations.

## 2. The Window's arm (`l188-arm`)

**Sources**
- Wikidot, Entity 2 "The Windows": https://backrooms-wiki.wikidot.com/entity-2
  - "a dark, indistinct human silhouette"; the photos show "few identifiable physical features".
  - It lures with whispers and hand gestures.
  - "Once within a range of one to two meters, the Window will manifest a physical representation of an arm to grasp and pull the victim into itself."
  - Instances "gain visual density" after a victim.
- Miraheze, Entity 2: https://backrooms.miraheze.org/wiki/Entity_2
  - The panes are black, and the silhouette is "an even darker black".
  - Victims are covered in pitch-black "window fluid". It describes no arm.
- Miraheze, Level 188: https://backrooms.miraheze.org/wiki/Level_188. The Figures are "humanoid silhouettes" that watch.
- Fandom (search summaries; the API returns 402): "a seemingly normal window that is pitch black which can grab you and drag you into the window".
- Wikidot, Level 188: does not exist. It is covered in the 188 plan §1.1.

**Verdict.** No wiki describes the arm itself. Lore-accurate here means:
- the arm of a dark human silhouette;
- human in shape, but indistinct and smoky where it leaves the glass, and densest at the hand;
- matte near-black;
- it grasps, then drags.

"Too long" and "wrong" are the plan's own choices, and they are kept.

**Change**
- **Thickness.** The arm was 1.6 px, a pencil. It now reads as an arm: 2.2 → 1.8 → 1 (palm 3 × 1 × 2.8) → 0.55 (fingers).
- **New anatomy.**
  - An Elbow knob, the Wrist, and a Knuckles ridge.
  - A fourth finger joint (Finger*d: one joint too many, as in plan §4.7). The fingers are 4.3–5.2 px.
  - A thumb that splays out.
- **Shoulder stump.** 5 px reaching back into the glass. The courtyard root is about 0.25 blocks in front of the glass, so the stump closes that gap.
  - Its texels thin to nothing, so it frays like smoke.
  - The upper arm also fades a little toward the glass.
- **Root.** The Root box, its pivot (0, 1, 0), and the reach along -X are unchanged, so the yaw contract holds.
- **Length.** About 34 px straight (2.1 blocks). The poses are solved so that:
  - in the hold, the wrist is 19 px out and 3–5 px below the root (the victim's chest);
  - in the drag, the elbow rises "like a spider's knee" and the hand comes in to 10 px.
- **Animations.**
  - reach: it is extruded out of the glass (a stretch of the upper arm about the root). It folds the wrong way, lunges with the fingers splayed, then hooks into the hold and closes. It ends closed, because the C# never plays grab.
  - pull: a heavy drag with a sideways tug and a re-grip.
  - recoil: a flinch with spasming fingers, then it is sucked back into the root.
  - idle: an additive finger flex and tremble.

**Counts:** 26 parts (was 18) and 5 animations.
