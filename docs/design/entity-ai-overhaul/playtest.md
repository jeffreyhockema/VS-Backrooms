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

## 9. Round 2: isolation

What round 2 (`isolation.md`, decisions 10 to 18) should feel like: a creature is an event, and two kinds are never about
you at once. Play a fresh world on the build from the merged round. The rates are in minutes; `/backrooms ratecheck` (below)
gives the numbers to set against what you feel.

1. Level 0's heart: walk it for half an hour. Expect at most one creature, a dark figure, and never a Hound. A Smiler
   appears only in a Red Room or while a Reality Shift has the lights out.
2. Level 1's heart: about one body every 20 to 30 minutes and a sound about every 9 minutes. Two bodies in a quarter of
   an hour is too many.
3. Level 1's edge: a body every few minutes, more than one in a minute is too many. Note what came and where.
4. Level 4: mostly nothing. A Duller now and then in the walls, the odd Hound, both seldom. Note how long you walked before
   the first.
5. Never two kinds at once outside the Flickering, the Screaming and dens: while a Hound is about, no Smiler, Wretch, rat
   or moth joins it. Check with `/backrooms encounter hound stalk` on a dummy (`/backrooms dummies on`, `entitylog on`).
6. Each Hound counter, one at a time, with `/backrooms encounter hound stalk` in Level 1:
   a. Out of sight: break the line of sight, stop, go dark and quiet. It searches where it lost you, then gives up and
      goes away. It does not drift back.
   b. The stare: hold its eye for a few seconds, then walk backwards at a walk, facing it. It backs off and holds until
      its nerve breaks; then it comes.
   c. Turn your back, or run: it comes at once.
   d. A shut door between you: it stops at the door and does not come through.
   A torch does not slow it: check that it closes as fast in a lit corridor as in the dark.
7. A straight run from a Hound fails. Start it hunting, a head start of 20 blocks, run straight down a lit corridor:
   it catches you well before any gate.
8. Facelings: in Level 1, one at a time and minutes apart; never two in one room. In Level 11, small groups.
9. Sounds: minutes apart at the least. Long stretches of nothing but the hum are the norm.
10. Paste the output of `/backrooms ratecheck` for Levels 0, 1, 4 and 9, in the heartland band (say 20 hours each), and
    say how it compares with what you saw. The Creatures tab's "Rate check here" button runs the same for where you stand.

## 10. Round 5: dial-in

What round 5 (`dialin.md`, decisions 19 to 34) should feel like: on Normal, a creature about every ten to twelve minutes
in Level 1's heart, Level 3 busy, Level 10 empty, and a Level 94 night with something in it. Play a fresh world on the
build from the merged round, on Normal unless a step says otherwise. The rates are in minutes; `/backrooms ratecheck`
gives the numbers to set against what you feel, and `/backrooms feltrate` (below) the spawns that actually land.

1. Level 1's heart, Normal: walk it for half an hour. Expect a creature about every 10 to 12 minutes and a sound every
   few. A quarter of an hour with nothing is normal; two creatures in a quarter of an hour is too many. Note when.
2. Level 1's edge: a creature every 4 to 5 minutes or so. More than two in a minute is too many.
3. The Flickering: when a section's lights fail, Hounds come and hunt until the lights return. It never starts while
   something else is about you. If one begins a few seconds after a sighting, that is a bug: note the time and what came
   before it.
4. Level 1 has no Hound packs in its dens. The bones and the grey hives are still there, with rats or nothing inside. A
   Hound in Level 1 comes from a dark section or a Flickering, never from a den.
5. The Screaming is Level 2's: rare, near its edges, a pack of Death Rats that runs past. It never happens in Level 1.
6. Level 3 is busy: expect something on most walks (a Duller, Skin-Stealers, a Clump). Compared with Level 4, it should
   feel like a different place. Two kinds at once are allowed here.
7. Level 4 stays calm: a Duller now and then, a Hound seldom.
8. Level 10 is empty of anything hostile. No Hounds at its edge, no Clumps by the barns. Only the worms underfoot.
9. Levels 8 and 9 are busy: off the lit road in Level 8, and in the Suburbs' dark streets, something turns up on most walks.
10. Level 94 at night: stand in the hills after dusk for ten minutes (the first visit was five, partly still). Expect
    something in sight within that time, often sooner. Standing still for a few seconds is the doll's protection, so
    test that too. By day, and indoors, nothing comes. If ten real minutes pass with nothing in sight, say so, with
    where you stood.
11. Two kinds at once: never in Levels 0, 1, 4, 5, 6, 10 and 11 (outside the set-pieces); allowed in Levels 2, 3, 7, 8,
    9, 94 and Fun. The entity log (`entitylog on`) shows which kind came first.
12. Settings: in new worlds, compare Very low, Normal and Very high for half an hour each in Level 1's heart. Very low
    should feel about three and a half times rarer than Normal; Very high about two and a half times busier, with more
    hunters and harder hits.
    Off leaves only sounds. Say which setting you played.
13. Creative: `/backrooms creativehunts` toggles whether a creative player is hunted (the Creatures tab button "Creative is
    hunted on/off" does the same). Off: creative sees glimpses only, as before. On: stalkers and hunters, and the set-pieces,
    reach you in creative too. Check both, and that toggling back restores the glimpses.
14. Facelings: in Levels 1, 4 and 5 about one every 8 minutes, and about one every 15 elsewhere. Level 11 keeps its small
    groups.
15. Paste the output of `/backrooms feltrate <level> [band]` for Levels 1, 3, 9 and 94 (Level 1 and 3 in the heartland,
    Level 9 at the edge, Level 94 in the hills at night), and of `/backrooms ratecheck` for the same four, and say how
    they compare with what you felt. Any count of refused spawns (no floor, in sight, den dweller) goes in too.
    `/backrooms menace` shows the refused body rolls for your level.

## 11. Progression

What the climb (`docs/design/progression/plan.md`, section 7) should feel like: the stone levels free, copper a raid
you can make without an anchor, bronze and iron a trip you prepare for, and a minute at zero a fair price, not a trap.
Play a fresh world on the build from the merged round, with a Copper Anchor, Bronze Anchor and Iron Anchor made (or
`/give` for the test, and say so). Note the time on your watch for each step.

1. Raid Level 3 with no anchor, carrying nothing you mind losing. Walk in from Level 2 and dig for clay for about ten
   minutes. Say when the stability gear started to turn back and when it reached zero. Expect about ten minutes from
   full, one tier beyond. Then walk out; a raid is not a stay.
2. The blackout and the wake-up: stay in Level 3 at zero for a full minute (wear nothing, or stand in the open). Expect
   the walls to go dark for a moment, a sound, and a wake-up in Level 2 at a random spot with your inventory. Check
   that no thin spot was left where you were, and that your stability is about half. Say how long the minute felt.
3. The copper anchor: craft it (2 copper ingots, a temporal gear, a candle) and wear it at the neck. Walk into Level 3
   and stay for half an hour. The gear should stay put; the Level 3 pockets (the flooded tunnels) still drain you as
   before. Check the `/backrooms ward` line for tier 1.
4. A Level 3 Hound in leather and in pleather: meet one with each set (or a Hound and then a Skin-Stealer if the Hound
   is shy). Leather should halve the blow you feel; pleather should help, but less. Say how many blows each took, and
   whether you could stand two.
5. The 9th Road tin dash: from the lit road in Level 8, go off it for a short run into the rock with a copper anchor,
   and back. The road's lamps should keep you steady on it; off it, the drain should be about the one-tier rate. Say
   where the tin was and how long it took.
6. Level 8 in bronze: with a Bronze Anchor on, walk off the road for ten minutes and check that the gear holds. Level 8's
   hunters (Wretches in packs, Giant Spiders) should still be the hard part, with two blows or fewer to kill you
   unarmoured and a bronze set standing two.
7. Level 9 in iron: with an Iron Anchor on, walk the Suburbs' streets for ten minutes. Strider and Hounds should run
   you down faster than a sprint, and the Wretches, Clumps and Dullers should not chase you that way. Note any hunter that
   outran you that did not.
8. Wanderer prices: trade with a wanderer for a temporal gear (rusty gears) and for a candle. Note the price asked, and
   check that no anchor or armour is on offer.

Add anything else you notice about the climb, and say which settings you played.
