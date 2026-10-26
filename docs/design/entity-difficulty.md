# Entity difficulty

2026-10-06. Why entities were no threat, and what changed so that every level below the Lobby is more dangerous
and more rewarding than the last. Code: `Danger` in `src/Entities/Roster.cs`, `src/Entities/Rewards.cs`, the
director in `MenaceSystem.cs`, the tasks in `AiTaskMenace.cs`, `AiTaskMoth.cs`, `AiTaskLurkers.cs`; base stats in
`tools/gen_entities.py`.

## 1. What was wrong

**Speed.** Players and walking AI go through the same ground physics. A player's movement step is 0.025 walking
and 0.05 sprinting; an AI's path speed is the same quantity. So an entity with a run speed under 0.05 can always be
outrun. Before:

| Entity | Run speed | Share of a sprint |
| --- | --- | --- |
| Hound | 0.042 | 84 % |
| Skin-Stealer | 0.024 | 48 % (slower than walking) |
| Death Rat | 0.040 | 80 % |
| Smiler, Duller | 0.050 | 100 % |
| Clump (crawl) | 0.020 | 40 % |

For reference, the vanilla wolf chases at 0.045.

**Damage.** A player has 15 health. A vanilla wolf bites for 8 at tier 2. Ours: Hound 2.5 at tier 1, Skin-Stealer
5, Death Rat 0.75, Deathmoth 1, Clump 3, Duller 2. Most fights needed six to twenty hits to kill an unarmoured
player.

**Nothing scaled with depth.** A Hound on Level 9 was the Hound of Level 1. Depth changed only which entities could
appear. Loot already got less picked over deeper down, but nothing else rewarded going deeper.

**Odds.** In the "approach" band only 5 % of encounters were hunts, and stalkers turned to the hunt mostly when the
player ran: which, being faster than everything, they could always do.

## 2. Level danger

Each level has a danger value, set on every entity as it is put down:

| Level | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 37 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Danger | 0 | .12 | .24 | .36 | .44 | .52 | .60 | .66 | .74 | .82 | .88 | .95 | .50 |

Level 94 keeps its own balance (the King's trial) and has danger 0. The far places: Level ! .90, Fun .90, The End .40,
the Hub 0, 974 0, 3999 .80 (only its Neon Blackout has anything in it), 188 .45. The bonus pool below goes by danger
(under .4, under .7, the rest), not by level number.

What danger `d` does:

| Effect | Formula | Level 1 | Level 5 | Level 9 |
| --- | --- | --- | --- | --- |
| Speed | x(1 + 0.3 d) | 1.04 | 1.16 | 1.25 |
| Damage | x(1 + 1.1 d) | 1.13 | 1.57 | 1.90 |
| Time between attacks | x(1 - 0.3 d) | 0.96 | 0.84 | 0.75 |
| Health | x(1 + 1.4 d) | 1.17 | 1.73 | 2.15 |
| Armour tier | +1 from d 0.6 (Level 6) | | | +1 |
| Gives up the chase at | 40 + 25 d blocks | 43 | 53 | 61 |
| Chance it turns to the hunt unprompted | x(1 + 2 d) | 1.2 | 2.0 | 2.6 |
| Director's spawn chance | x(1 + 0.8 d) | 1.10 | 1.42 | 1.66 |
| Calm after a close call | 90 s x(1 - 0.5 d) | 85 s | 67 s | 53 s |
| Encounters that are hunts (approach / edge) | | 7 % / 28 % | 13 % / 38 % | 17 % / 42 % |
| Most entities near you at once | +1 from Level 5, +1 from Level 9 | | | |
| Pack size | +1 at most from Level 5 | | | |

`/backrooms menace` shows the current level's danger and multipliers.

## 3. New base stats (Level 0) and what they become

Speeds are shares of a sprint; "hits" is how many land on an unarmoured player with 15 health. (The Hound, Skin-Stealer, Wretch, Clump, Giant Spider and Bacteria rows are superseded by section 3b.)

| Entity | Level | Speed | Damage | Hits | Health |
| --- | --- | --- | --- | --- | --- |
| Hound (in the dark; light slows it to 0.7) | 1 | 95 % | 4.0 | 4 | 16 |
| | 3 | 102 % | 4.9 | 4 | 21 |
| | 5 | 106 % | 5.5 | 3 | 24 |
| | 9 | 115 % | 6.7 (tier 3) | 3 | 30 |
| Smiler (stops at light 8 or more) | 0 | 100 % | 6.0 | 3 | immortal |
| | 2 | 107 % | 7.6 | 2 | |
| | 9 | 125 % | 11.4 (tier 4) | 2 | |
| Skin-Stealer (slow, strong; a hit of 5 stuns it for 1.2 s, 8 s apart; fed, it is docile; 2026-10-18) | 1 | 70 % | 7.9 | 2 | 60 |
| | 5 | 79 % | 11.0 | 2 | 88 |
| | 9 | 85 % | 13.3 (tier 3) | 2 | 110 |
| Death Rat (packs of 2 to 6) | 1 | 99 % | 1.4 | 11 | 6 |
| | 8 | 117 % | 2.2 (tier 1) | 7 | 10 |
| Duller (grab through a wall; takes no damage from players but from its grab to 1.5 s after; flees at 1.3 x a sprint; 2026-10-18) | 3 | 120 % | 4.2 | 4 | 30 |
| | 8 | 132 % | 5.4 (tier 2) | 3 | 41 |
| Clump (grab; crawl) | 2 | 60 % | 6.3 | 3 | 27 |
| Deathmoth female (bite) | 1 | | 1.7 | | 3 |
| Wretch (bite; packs in Level 8) | 1 | 96 % | 4.0 | 4 | 19 |
| | 8 | 112 % | 6.3 (tier 2) | 3 | 33 |
| Bacteria (hunts only a runner near the Lobby's exits, briefly: see §4) | 0 | 92 % | 6.0 | 3 | 20 |
| Neighborhood Watch (Level 9; chases only what it sees, never indoors) | 9 | 110 % | 12.4 (tier 3) | 2 | 64 |
| Giant Spider (bite + venom 5 x 0.9 over 6 s; lies in wait, leashed to 24 blocks of its home; 2026-10-18) | 8 | 122 % | 6.3 + 4.5 (tier 3) | 2 | 41 |

The Mangled (5, plus being lifted 7 blocks and dropped; slower than a walk since 2026-10-10) and The Thing are events and keep their own numbers.

## 3b. Play-test pass: killable creatures as real threats (2026-10-20, batch P7)

The first play-test found a Hound met in Level 0 that did not fight (even struck, with a stick), a Wretch that was easy
to outrun, and Hounds that were "not a true threat". The vanilla yardsticks (assets/survival/entities/animal/mammal):

| Vanilla | Health | Bite | Tier | Cooldown | Run |
| --- | --- | --- | --- | --- | --- |
| Wolf | 15 | 8 | 2 | 0.5 to 1.5 s (wind-up 0.9 s at x1.5 anim speed) | 0.045 chase, 0.052 flee |
| Black bear | 44 | 10 | 2 | 1.5 s | 0.040 |
| Brown bear | 64 | 12 | 2 | 1.5 s | 0.055 |
| Polar bear | 66 | 16 | 2 | 1.5 s | 0.060 |

Effective values (base x the level's danger multipliers of section 2; speed / damage per hit / health; a player has
15 health and sprints at 0.05). Tier is 2, and 3 from Level 6.

| Entity (base before, after) | Level | Before | After |
| --- | --- | --- | --- |
| Hound (run .046 -> .050, bite 3.5 -> 7.2, health 16 -> 26, cooldown 1.2 -> 1.1 s) | 1 | .048 / 4.0 / 19 | .052 / 8.2 / 30 (a wolf's bite and speed, twice its health) |
| | 3 | .051 / 4.9 / 24 | .055 / 10.1 / 39 (a black bear: its bite and nearly its health, a brown bear's run) |
| | 5 | .053 / 5.5 / 28 | .058 / 11.3 / 45 |
| | 9 | .057 / 6.7 / 34 | .062 / 13.7 / 56 (tier 3; a brown bear) |
| Skin-Stealer (run .034 -> .036, hit 7 -> 10.6, health 51 -> 55) | 1 | .035 / 7.9 / 60 | .037 / 12.0 / 64 (a brown bear) |
| | 3 | .038 / 9.8 / 77 | .040 / 14.8 / 83 |
| | 5 | .039 / 11.0 / 88 | .042 / 16.7 / 95 |
| | 9 | .042 / 13.3 / 110 | .045 / 20.2 / 118 (tier 3) |
| Wretch, common look (run .046 -> .048, bite 3.5 -> 5.5, health 16 -> 18) | 1 | .048 / 4.0 / 19 | .050 / 6.2 / 21 |
| | 3 | .051 / 4.9 / 24 | .053 / 7.7 / 27 (outruns a sprint) |
| | 5 | .053 / 5.5 / 28 | .055 / 8.6 / 31 |
| | 9 | .057 / 6.7 / 34 | .060 / 10.5 / 39 |
| Wretch, far-gone look (x1.15 -> x1.2) | 3 | .059 / 4.9 / 24 | .064 / 7.7 / 27 |
| | 9 | .066 / 6.7 / 34 | .072 / 10.5 / 39 |
| Clump (grab 5.5 -> 6.5, health 13 -> 15; crawls at .028) | 1 | 6.2 / 15 | 7.4 / 18 |
| | 3 | 7.7 / 20 | 9.1 / 23 |
| | 5 | 8.6 / 22 | 10.2 / 26 |
| | 9 | 10.5 / 28 | 12.4 / 32 |
| Giant Spider (bite 3.5 -> 4.5, plus the venom; health 20, run .050) | 1 | .052 / 4.0 / 23 | .052 / 5.1 / 23 |
| | 5 | .058 / 5.5 / 35 | .058 / 7.1 / 35 |
| | 9 | .062 / 6.7 / 43 | .062 / 8.6 / 43 |
| Bacteria (Level 0, danger 0; run .046 -> .050, hit 6 -> 8, health 20 -> 30) | 0 | .046 / 6.0 / 20 | .050 (x0.92 in the Lobby's fright, a full sprint once struck) / 8.0 / 30 |

Unchanged: the Death Rat, Deathmoths, Smilers, Dullers, the Partygoer (Fun, danger .9: claw 4 x 1.99 = 8, health
30 x 2.26 = 68, a slow 0.031 walk: already past the Hound's bite there) and the events. The Hound stays killable
(18 health base against a wolf's 15) because the player has no armour to speak of, and its counters stay: a torch or
lantern slows it, fire wards it, a steady stare buys a few seconds (unless it is struck), doors stop it.

Why a candle seemed to scare them: it did not, in code (it gives light 7, under the 8 and 10 thresholds; held light
only widens what a creature sees). The Hound's `slowedByLight` slowed it to 70 % whenever the player was not in the
dark, and the Level 0 halls are lit, so it was slow with or without a candle; and a struck Hound still obeyed the
stare-down (a player facing it, as one does with a stick, held it back) and its hunt was refused by the Lobby rules
(no hunting outside the Red Rooms) once it lost track, while the Bacteria's hunt was called off at the first wound
unless it already counted as provoked. All fixed in `AiTaskMenace.cs`.

## 3c. Isolation pass (2026-10-20, P7 round 2)

The second play-test found too many creatures, in pairs and packs, and a Level 4 that was full of them. The fix is in
the director's rates and the Hound's behaviour, not in the danger numbers above. Full design: `isolation.md` in
`docs/design/entity-ai-overhaul/`, sections 4.1 to 4.5. Where this section and 3b disagree, this one wins.

**Hound run speed.** The base goes from .050 to .062: faster than a sprint everywhere, and a carried light no longer
slows it (it was 70 % in a lit place). Its walk, bite and health are unchanged.

| Hound run speed | Run | Share of a sprint |
| --- | --- | --- |
| Danger 0 (base) | .062 | 124 % |
| Level 1 (danger .12) | .064 | 128 % |
| Level 9 (danger .82) | .077 | 155 % |

**Rates (`EncounterRoll`).** Each roll is a mean interval in real minutes (each 2 s tick rolls with a chance of 2 s
divided by the mean), with a hard gap after the last of its kind of 40 % of the mean. Bodies are glimpse, stalk or
hunt; sounds are their own roll, and a capped or failed spawn is silence, with no sound in its place.

| Band | Bodies, mean min | Sounds, mean min |
| --- | --- | --- |
| Heartland | 25 | 7.5 |
| Approach | 12 | 5 |
| Threshold | 6 | 3.5 |
| In a den | 3 | 2 |

Both intervals are multiplied by the level's **solitude** (bigger is lonelier), by the menace factor (1.5 - menace,
clamped to 0.5 to 1.5: a calm player in the heartland waits longer, a noisy one at the edge less), and divided by the
setting's spawn multiplier (off and low 0.6: longer; high 1.5: shorter) (0.514 values; see 3d).

| Level | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 37 | 94 | Fun | End | 3999 | 188 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Solitude | 1.5 | 1.0 | 0.7 | 0.6 | 1.5 | 1.2 | 3.0 | 1.0 | 0.8 | 0.6 | 2.0 | 1.2 | 4.0 | 1.0 | 0.7 | 4.0 | 0.8 | 1.0 |

Worked examples (menace typical of the band; factor = 1.5 - menace):

| Place | Calculation | Body | Sound |
| --- | --- | --- | --- |
| Level 1 heartland (menace .3, factor 1.2) | 25 x 1.0 x 1.2 | 30 min | 9 min |
| Level 1 approach (menace .6, factor .9) | 12 x 1.0 x .9 | 11 min | 4.5 min |
| Level 1 edge, threshold (menace .9, factor .6) | 6 x 1.0 x .6 | 3.6 min | 2.1 min |
| Level 4 approach (menace .6, factor .9) | 12 x 1.5 x .9 | 16 min | 7 min |
| Level 0 heartland, Bacteria only (menace .3, factor 1.2) | 25 x 1.5 x 1.2 | 45 min | 13.5 min |
| Level 6 heartland (menace .3, factor 1.2) | 25 x 3.0 x 1.2 | 90 min | 27 min |
| Level 9 threshold (menace .9, factor .6) | 6 x 0.6 x .6 | 2.2 min | 1.3 min |

**Caps.** Heartland 1, approach 2, threshold 3 menacing things within 64 blocks; +1 from danger 0.5 (Level 5) and +1
from 0.8 (Level 9), as before. Packs are clipped to the cap.

**One kind at a time.** No body is rolled while anything menacing is already about the player, whatever its kind; the
Flickering, the Screaming, hive alarms, dens' dwellers and the other set-pieces are the exceptions.

## 3d. Dial-in (2026-10-23, P7 round 5)

The play-test after round 4 found 0.515 at the other extreme from 0.514: too rare to see anything on the normal setting. The
rates are dialled back toward the middle, the setting gets six values, and the bands, solitude and one-kind rule move
with them. Full design: `dialin.md` in `docs/design/entity-ai-overhaul/`, sections 3.1 to 3.6. Where this section and
3c disagree, this one wins.

**Six settings.** `backroomsMenace` in `worldconfig.json` is `off`, `verylow`, `low`, `normal`, `high` or `veryhigh`
(Off, Very low, Low, Normal, High, Very high). Spawns divides both mean intervals; damage multiplies every hit; the mix
adds danger to the body mix (more hunters); the cap bonus adds to the caps. Old worlds keep their codes: "normal" is the
new normal.

| Setting | Spawns | Damage | Entities | Mix | Cap bonus |
| --- | --- | --- | --- | --- | --- |
| Off | 1 | 0 | sounds only | | |
| Very low | 2 | 0.5 | yes | | |
| Low | 3.5 | 0.75 | yes | | |
| Normal | 5.5 | 1 | yes | | |
| High | 8.5 | 1.3 | yes | +0.3 danger on the body mix | +1 approach and threshold |
| Very high | 13 | 1.6 | yes | +0.6 danger on the body mix | +1 every band |

The progression round shifted the names up one step (decision 8 of `docs/design/progression/decisions.md`): the table above is the current one, and the dial-in's own numbers (1 / 2 / 3.5 / 5.5 / 8.5) now belong to the step below. Every setting is one step busier than in the previous build (a Normal world gets about 1.6 times the old spawns). Set-pieces (night visits, hive waves, the Mangled's fog, the Beast) scale by the square root of the multiplier, so Normal is about 2.3 times their original values, not 5.5 times.

**Bands.** Approach now starts at a depth of 0.5 (was 0.6) and threshold at 0.8 (was 0.85). **Hard gap:** 25 % of the
mean (was 40 %); the mean stays as stated.

**Solitude, changed:** Level 1 1.3 (was 1.0), Level 3 0.45 (was 0.6), Level 8 0.5 (was 0.8), Level 9 0.3 (was 0.6),
Level Fun 0.4 (was 0.7), Level 94 at night 0.6 (was 1.0), Level 10 with no hostile roster, and Level 94's danger 0.4
(was 0). Everything else in the table in section 3c is unchanged.

**Rates on Normal, Level 1.** Mean wait in real minutes, with menace typical of the band:

| Level 1 | Body | Sound |
| --- | --- | --- |
| Heartland | 25 x 1.3 x 1.2 / 5.5 = **7.1 min** | 7.5 x 1.3 x 1.2 / 5.5 = 2.1 min |
| Approach | 12 x 1.3 x 0.9 / 5.5 = **2.55 min** | 1.1 min |
| Threshold | 6 x 1.3 x 0.6 / 5.5 = **0.85 min** | 0.5 min |

The dial-in's target was a creature every 10 to 12 minutes in Level 1's heart (now about 7 on Normal after the shift), and
the edge every 4 to 5 minutes (now about 2.5): the approach band is that edge; the threshold is the last fifth and the gates.

Other places, Normal, bodies (dial-in values, divide by 5.5 / 3.5 = 1.57 for the current ones): Level 3 heartland 25 x 0.45 x 1.3 / 3.5 = 4.2 min; Level 4 approach (its heartland is
Safe) 12 x 1.5 x 1.0 / 3.5 = 5.1 min; Level 6 anywhere 25 x 3.0 x 1.3 / 3.5 = 28 min; Level 9 edge about 0.3 min;
Level 94 night hills 12 x 0.6 / 3.5 = 2.1 min, and its towns (threshold) about 1 min. `BodyMinutes` and `SoundMinutes`
are unchanged. Currently Very low spawns once where Normal spawns 2.75 times, so it is about 2.75 times rarer on every band (about 20 minutes in Level 1's heart); Low
about 1.6 times rarer (11); High about 1.5 times busier (4.5); Very high about 2.4 times busier (3).

**One kind at a time, by class.** Strict in Class 0 to 2 levels (0, 1, 4, 5, 6, 10, 11, 37, The End, the Hub, 974); two
kinds may be about together in Classes 3 to 5 (2, 3, 7, 8, 9, 94, Fun). Levels 3999 and 188 follow their own rows in
the class table (section 2 of `dialin.md`). The Flickering starts only with nothing menacing about
and outside the hard gap; its Hounds still always come.

## 4. Skill: what keeps you alive now

- **Running only works early.** From Level 3 a Hound outruns you, and running is what turns a stalker into a hunter.
- **Nothing chases for ever** (2026-10-10). A hunt that draws no blood for 20 seconds (35 at the bottom) is given up: the
  hunter goes back to following and will not hunt again for a minute. The Lobby's Bacteria hunts only while you keep
  running near the way out: walk for four seconds, head back towards the heart, take one blow, or last 25 seconds,
  and it sinks back into the mould (strike it and it fights, bounded only by the 20 seconds).
- **Light**: a torch or lantern in hand (light 10 or more; not a candle, which is 7, and not the lit halls) slows Hounds to 70 %; Smilers stay out of light 8 or more, and rats keep clear of a carried torch (10). A candle scares nothing. **Fire** still wards off Hounds,
  Skin-Stealers, rats and moths.
- **Stare a Hound down** for a few seconds' grace (not one you have struck: that one fights).
- **Struck, it fights** (2026-10-20): anything killable that is hit turns on the striker and stays on it (no stare-down,
  no Lobby call-off, no band or sanctuary rule, patience restarted), knowing where they are while they stay within 16
  blocks, for `retaliateSeconds` (60) after the last blow.
- **Doors**: nothing hostile opens one but the Skin-Stealer (2026-10-10): hunting someone shut in, out towards the
  edge of a level or worse, it knocks on the nearest door near them, waits two seconds, and opens it. A door barred
  from the inside (a vanilla bar lock) only gets the knock; fire keeps it away from the door altogether.
- **Dodge**: every attack is wound up (600 ms for a Hound, 650 for a Skin-Stealer). Being more than 0.4 blocks
  beyond its reach when the blow lands makes it miss (was 0.6).
- **Almond Water** keeps Dullers off; **quiet** keeps Clumps buried; **indoors** is safe from the Mangled.
- **Armour** matters more from Level 6, where every blow is one tier harder.

## 5. Progression pressure (2026-10-25, progression round)

The climb's lethality, from `docs/design/progression/plan.md` 3.5 (decisions 5 and 8). Lethality is not a setting: the
world's *Backrooms entities* setting still multiplies damage and spawns on top, with the values in 3d (the progression round's shifted ones). The stability side of the climb
(the blackout at zero stability, `ZeroSystem`) is in the handbook's *Reality Stability*, not here. The depth drain, the ward
tiers and the anchors were removed after the play-test (`docs/design/progression/revision.md`); the curve below stayed.

**Damage targets** (a hunter's blow on an unarmoured player, at the level's danger; 15 HP):

| Level | Danger | Blow (target) | Blows to kill, unarmoured | What answers it |
| --- | --- | --- | --- | --- |
| 3 | .36 | about 6 | 2 to 3 | leather halves the blow |
| 5 | .52 | about 8 | 2 | leather, then bronze |
| 8 | .74 | 10 to 12 | 2 | a bronze lamellar or chain set, to stand two blows |
| 9 and deeper | .82 and up | about 14 | 2 | iron plate |

The handbook says "about two blows at Level 3, one or two by Level 8, and a Hound kills in one at Level 9" (the 2026-10-25 text pass; a Hound
is the fastest, hardest case, so the table's two-blow figure at Level 9 is the average hunter). At 15 HP a blow of 10 to 12 needs two, so
"one or two" at Level 8 holds only for a player already hurt, or a second blow in the same breath. Decide which when
`armourtest` (below) prints the table: either the Level 8 blow rises to 15 or more, or the handbook's line changes.

**Speed floor.** From danger .36 (Level 3) every hunter's run speed is at least 1.15 x a sprint (0.058, so 0.067), rising
to 1.4 x a sprint (0.081) at Level 9. The exceptions are Wretch, Clump and Duller, which ambush or reach and keep their
own speeds. Hounds already run 0.062 at base; Deathmoths fly and the Thing swims, so both already outpace the player.
The curve between the two ends is the code's (`Danger` in `Roster.cs`, the run speeds in `tools/gen_entities.py`).

**Measure.** `armourtest` (piece B, `tools/aitest/run.py`) gives hits-to-kill per level and armour set with a dummy and
the level's hunter striking; the speed cases check that a Level 3 Smiler closes on a running dummy. The table above is the
target those numbers are tuned to, and the play-test check-list is `playtest.md` section 11.

## 6. Rewards

- **Bounty** (`Rewards.Bounty`), on whatever a player kills, in rusty gears (the wanderers' coin), expected value:

| Entity | At danger 0 | Extra per unit of danger | Level 5 |
| --- | --- | --- | --- |
| Hound (old ones double) | 0.25 | 1.0 | 0.8 |
| Skin-Stealer (plus one or two belongings) | 1.0 | 2.5 | 2.3 |
| Duller | 0.5 | 2.0 | 1.5 |
| Clump | 0.5 | 2.0 | 1.5 |
| Death Rat | 0.05 | 0.25 | 0.2 |
| Deathmoth female | 0.05 | 0.2 | 0.15 |
| Wretch (plus one or two belongings) | 0.3 | 0.8 | 0.7 |
| Bacteria | 1.0 | 2.0 | 2.0 |
| Neighborhood Watch (Level 9: 3.05) | 1.0 | 2.5 | |
| Giant Spider (Level 8, danger .74: 2.85) | 1.0 | 2.5 | 2.3 |
| Partygoer, intern (Fun, danger .9: 3.25) | 1.0 | 2.5 | 2.3 |

  Facelings carry no bounty, and neither does any of Level !'s horde.
- **Caches** (`Rewards.OnBrokeBlock`): any of our blocks whose drops include food, medicine, metal, seeds or gears
  (132 kinds). Broken by a player in survival below Level 0:
  - with chance 0.7 d, its contents drop a second time;
  - with chance 0.15 + 0.35 d, one extra from the level's pool:
    - Levels 1 to 3: bandage, candles, crackers, twine, a rusty gear;
    - Levels 4 to 7: rusty gears, copper bits, a poultice, Almond Water, Firesalt;
    - Level 8 on: rusty gears, tin bronze bits, bandages, iron bits, very rarely a temporal gear.
- Already there: deeper levels' boxes are less picked over (80 % in Level 1, 60 % to Level 5, 40 % below).

## 7. To tune after play

All in one place: `Danger.OfLevel` (the curve) and the multipliers beside it; the base stats in
`tools/gen_entities.py`; the bounty and cache tables at the top of `Rewards.cs`. The world setting *Backrooms
entities* (Off, Very low, Low, Normal, High, Very high) still multiplies damage (0, 0.5, 0.75, 1, 1.3, 1.6) and spawns (1, 2, 3.5, 5.5, 8.5, 13; the 0.514 values were 0.6, 0.6, 1, 1.5, see 3d) on top of all
this; Off also keeps the entities themselves away, leaving only their sounds.
