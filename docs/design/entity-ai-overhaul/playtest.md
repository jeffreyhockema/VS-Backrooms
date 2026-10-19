# Entity AI overhaul: play-test check-list (P7)

What the headless harness cannot check, gathered from every batch's report. Play on a fresh world made with the branch
`ai/p1-machine` build, with the cheat menu (F7) to hand. Note what feels wrong, not only what is broken: P7 turns your
notes into numbers. Everything here can also be found with `/backrooms encounter <entity> <kind>` and the Creatures
tab's **Perceive** button (it reports every second what a creature sees, hears and believes of you).

## 1. Senses (all perceiving creatures)

1. In the dark, still and quiet, a Hound 20 blocks off does not find you; with a torch it sees you from about 60.
2. Crouching halves how far you are seen. Running is heard within about 13 blocks of a Hound.
3. Break line of sight, stop, go dark: a hunting Hound loses you after about 8 seconds and searches where it last
   saw you, then goes back to following at a distance.
4. Throw a stone well away from you: a stalking Hound goes to where it landed (Investigate) and looks about.
5. Slam a door behind you and it is heard; close it while sneaking and it is not.
6. Two players together are not hunted by twice as much.

## 2. Hounds, Smilers, the Bacteria (P1)

1. A Hound that sees you growls before it comes; a pack barks and the rest come to the bark. In Level 3 they bark
   while hunting, faster when close.
2. Stare a Hound down: it still holds for 4 to 8 seconds, then comes.
3. A Smiler that has seen your light gathers at the edge of it, grinning, and never steps in; it never walks into a
   lit room after a noise.
4. A creature you strike turns on you, and about a minute later goes back to what it was doing (a Faceling to its
   routine, not to following you).

## 3. Skin-Stealers, Dullers, Death Rats, Wretches (P2)

1. A fed Skin-Stealer (`/backrooms feed fed`) wears clothes, wanders and says "hello?"; hungry, it stalks in the waxy look.
2. Strike a Skin-Stealer: a pale, clear burst (check whether vanilla's red blood still shows under it). A blow of 5 or
   more freezes it for 1.2 seconds.
3. A Duller faced in Level 1 runs fast and vanishes; swinging at it in the open does nothing; for about 1.5 seconds
   after it grabs you through a wall, you can hurt it.
4. Drop food in a Level 1 or 2 hallway: rats come and eat; walking up or a torch scatters them; cornered, one bites
   once. Level 2's hairless rats never bite.
5. A Wretch pleads from out of sight; the dressed ones are slower, the far-gone faster.

## 4. Deathmoths, Clumps, Facelings (P3)

1. Enter a hive den (Levels 1, 5, 9): two or three resin hive hearts appear near its middle, not in doorways; they break
   by hand but slowly; breaking one brings the females and waves of them for a minute; the den does not refill.
2. Male moths settle on dropped food and take off when you come near; in Level 3 males bite too.
3. One runner past a buried Clump at 10 blocks does not wake it; two do. A Clump that has grabbed you buries itself again
   and leaves you be for a minute.
4. A killed Clump leaves a flesh patch that grows a new small Clump in about 20 hours; a torch, a firestarter or a fire
   close by burns it away.
5. Break a block near a Level 4 Faceling: it turns, stretches and shoves you once, then goes back to its routine. Being
   bitten by something near one does not set it off.
6. Hit a Faceling child, then give it food: it calms, waves, and follows you for a minute.
7. Level 3's Facelings have a half-formed face and are hostile and weak.

## 5. The Strider, the Watcher, the Spider, the Beast, the Thing (P4)

1. Near a Strider (the six-legged eye), Hounds, Smilers, Skin-Stealers and moths turn tail. Arrows hurt it twice as much.
2. The floating Watcher drifts silently over the Suburbs' streets with a hum. In its view within 12 blocks it turns its
   eye on you, the tone rises and the pupil glows for 2 seconds, then the beam turns you to dust. A wall in those two
   seconds saves you; behind glass it only watches. Check the glow is a round disc (no square) and the beam pose holds.
3. In a Level 8 nest, a loud noise wakes the whole nest and more come out of the dark.
4. Refuse the Beast and hide: a calm runner in a dark room is lost for a while; an unsteady one is found.
5. Dive in Level 7 until the Thing rushes; a lit lantern held under water turns it away for about 20 seconds.

## 6. Materials (P6)

1. Hive hearts give 2 to 4 quills (in Level 5, now and then moth jelly); a female moth 0 to 1 quill; a Giant Spider
   silk and meat; a Clump patch 1 to 2 sinew; a Hound a bone.
2. Quill + spear: "(envenomed, 3)"; quill + 8 arrows: envenomed arrows. A hit poisons for 6 seconds and spends a charge.
   A creature killed by the poison still pays its bounty.
3. 2 silk make twine; 4 sinew make rope; sinew strings a bow and a sling.
4. Moth jelly set down draws male moths and rats for a minute, even off a hunt.

## 7. Levels (P5)

1. Level 6 shows nothing but, rarely, a grin far off in the dark that never comes closer.
2. Level 94 at night has Smilers, Skin-Stealers, Hounds and male moths besides the Animations.
3. Dullers behind Level 1's room walls; Wretches more common in Level 9, rarer in Level 3.

## 8. Feel, overall

- Is a dark corridor now a place you can hide in, and a lit one a place you are seen?
- Does anything still find you "by magic"? (A stalker drifts towards you vaguely now and then; it should never hunt
  you without having seen, heard or sensed you.)
- Are hunts too easy to shake off, or too hard? Too few encounters, or too many?
- Performance: `/backrooms menace` ends with a cost line (director milliseconds a tick, perception checks a second).
