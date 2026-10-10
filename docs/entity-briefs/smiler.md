# Smiler (Entity 3): model brief

## Sources
- Wikidot, Entity 3 "Smilers": https://backrooms-wiki.wikidot.com/entity-3
  "a long smile with multiple sharp teeth, and have white glowing eyes"; "reflective eyes and teeth gleaming in the
  dark"; body "rumored ... cannot be seen with the human eye"; "non-human, alien-like bodies, with arms and legs bent in
  unnatural ways, but this is unconfirmed". Behaviour: in dark areas (Levels 2, 3); "attracted to light" and chases a
  light carrier; attacks only if you panic and retreat or make a loud noise; keep eye contact and back away slowly.
- Miraheze: https://backrooms.miraheze.org/wiki/Smilers. Same baseline ("a long glowing smile"), lunges at
  flashlights, sudden moves or noise raise aggression, keep eye contact.
- Fandom, Entity 3 (fetch blocked, read through search summaries): https://backrooms.fandom.com/wiki/Entity_3
  *Subridens tenebris bestia*, amorphous "spectral entity" common where light is low; two organs: the *Ardenti risu*
  (the "burning smile", which can shift to other faces) and the *Nigrum ignem* ("black fire", most of its mass).
  Variants: 3-A Frowners (foxes that mimic the glowing face), 3-B Clypto, 3-C Rattlers.
- A secondary fan wiki adds "a black humanoid arm to pull their victims into the dark":
  https://a-syncbackroomsinvestigationwiki.webador.es/entity-3-smiler

## Conflicts and choices
- Light: Wikidot and Miraheze say light *attracts* it; the mod (and much popular art) makes it shun light. The game
  rule stays as it is (lightBound); the model does not depend on it.
- Body: unseen, alien-limbed (Wikidot) vs. amorphous black fire (Fandom). Combined: a too-thin, wrong-jointed black
  body that comes apart into black-fire tatters at the hips and off the back of the skull. In the dark only the face
  shows.
- Face: all sources agree: a wide glowing grin of many sharp teeth and two white glowing eyes. Popular art: a
  Cheshire crescent running ear to ear, eyes slanted with no pupils. That is the identity, and the face gets most of
  the parts.
- Eye contact freezes it: `idle` is also the frozen pose, so it is almost motionless.

## Proportions (model px, 16 = 1 block)
- Height 31 px (1.95 blocks), feet (points) at 0. Hips 12.4-14.6, waist 1.2 x 1.6 (wasp-thin), chest 2.3 x 3.6,
  shoulders 6.2 wide, neck 3.8 long craned forward 30 degrees, skull 4 x 3.7 x 4.8.
- Grin 9.6 px wide (twice the skull), crescent: gum at 27.55 + 0.072 z^2 (ends rising to eye level), wrapping back
  round the head (x = -2.3 + 0.062 z^2). Glowing face spans 24.1-28.9 px in the rest pose.
- Arms 9.4 + 9.9 + hand + 3.2-3.7 px fingers: they hang to the ankles. The elbows bend backwards; the knees bend
  backwards.

## Palette
Body (13,11,16) with sheen (34,30,44) and deep (4,3,6); smoke (17,15,21); mouth interior (30,6,12); teeth (238,234,218)
to (255,255,250) at the tips, flanks darkened; eyes (255,255,252) with a (214,226,236) rim. Glow 255 on the teeth and
eyes, 210 on the inner rows, 0 everywhere else.

## Parts (92)
Hips, Waist, Chest, Collar, Neck, Head, Cranium, Throat, Jaw, Chin; EyeL/R; CheekL/R, JawCheekL/R (black webs behind
the grin's ends); 17 upper + 16 lower outer teeth (ToothU*, ToothD*: 4 fangs), 7 + 6 inner teeth (InnerU*, InnerD*)
hidden until the jaw opens; Flame0-3 (black fire off the skull); ArmL/R, ForearmL/R, HandL/R, Finger0-2 L/R; ThighL/R,
ShinL/R, FootL/R; Tatter0-7 (the body dissolving below the hips).

## Animations
- idle (120 f): the frozen stare. A slow head tilt that twitches back, the jaw parting a hair, fingers curling one at
  a time; only the black fire keeps flickering.
- walk (40 f, also run at 2x): a glide. The body leans and sways, the legs trail without stepping, the arms hang late,
  the smoke streams back; the head cancels the body's sway and bob, so the grin comes on level.
- attack (21 f = 0.7 s; damageAtMs 300 = frame 9): the head draws back and the grin splits into two crescents with
  the second rows showing, the arms rise; a lunge with the arms raking in, and the jaw slams shut on frame 9.
- hurt (14 f, extra): the face jerks back and aside, the fire flares.
