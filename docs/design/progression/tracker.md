# Progression pressure: tracker

One report per piece, appended by its worker. See [plan.md](plan.md) and [decisions.md](decisions.md).

### Piece B (lethality, speed, settings)

Branch `prog/lethality`, 2026-10-25.

**Damage curve.** `Danger.Damage(d)` (Roster.cs) is now a line through points instead of `1 + 1.1 d`: (0, 1), (.24, 1.264), (.36, 1.264), (.52, 1.40), (.74, 1.75), (.82, 2.2), (.95, 2.6), carried on at the last slope. Levels 0 to 2 are exactly as before. Per-entity base damages are untouched. Hit for the median hunter (Smiler, base 6; a Hound, base 7.2, hits a fifth harder), unarmoured:

| Level (danger) | Multiplier | Smiler | Hound | Plan |
|---|---|---|---|---|
| 1 (.12) | 1.13 | 6.8 | 8.2 | as before |
| 3 (.36) | 1.264 | 7.6 | 9.1 | about 6 |
| 5 (.52) | 1.40 | 8.4 | 10.1 | 8 |
| 8 (.74) | 1.75 | 10.5 | 12.6 | 10 to 12 |
| 9 (.82) | 2.20 | 13.2 | 15.8 | 14 |
| 11 (.95) | 2.6 | 15.6 | 18.7 | |

Level 3 is above the plan's 6 on purpose: Level 2 already hits at 1.26, and a dip at Level 3 would make the first ring below the old levels the softest. A Smiler at 7.6 still takes two blows (15 / 7.6), inside decision 5's "2 to 3". Before the change Level 3 was 1.40 (Hound 10.1), Level 5 1.57, Level 8 1.81, Level 9 1.90: so Levels 3 to 5 are 9 to 11 % softer, Level 8 4 % softer, Level 9 and deeper 16 to 27 % harder. Side effects: the same function feeds Deathmoth bites, spiders, Partygoers, the Watch and Level !'s rats (their hits scale the same way).

**Armour test.** `/backrooms armourtest <entity> <level> [set]` (cheat-menu buttons for three cases; harness case `prog-armour`). A straw dummy has no character inventory, and vanilla's armour code (`ModSystemWearableStats.handleDamaged`) only hooks players, so the command re-runs vanilla's rules on the real items' `ProtectionModifiers`: a blow lands on head 20 %, body 50 % or legs 30 %, only that piece protects, flat reduction and relative share worn down per tier of the blow beyond the piece's tier, an empty slot protects nothing. The blow is the entity's task damage x curve x damage setting at damage tier + the depth bonus. Mean damage per blow / mean blows to kill a 15-health player:

| Hound | L1 | L3 | L5 | L8 | L9 | L11 |
|---|---|---|---|---|---|---|
| none | 8.2 / 1.8 | 9.1 / 1.6 | 10.1 / 1.5 | 12.6 / 1.2 | 15.8 / 0.9 | 18.7 / 0.8 |
| jerkin leather (body, legs) | 6.0 / 2.5 | 6.7 / 2.2 | 7.5 / 2.0 | 9.9 / 1.5 | 12.4 / 1.2 | 14.7 / 1.0 |
| sewn leather | 3.5 / 4.3 | 3.9 / 3.8 | 4.4 / 3.4 | 6.1 / 2.5 | 7.7 / 2.0 | 9.1 / 1.7 |
| copper lamellar | 3.0 / 4.9 | 3.4 / 4.4 | 3.8 / 4.0 | 6.0 / 2.5 | 7.5 / 2.0 | 8.9 / 1.7 |
| bronze lamellar | 2.1 / 7.0 | 2.4 / 6.3 | 2.7 / 5.6 | 4.8 / 3.1 | 6.0 / 2.5 | 7.1 / 2.1 |
| bronze chain | 1.6 / 9.2 | 1.9 / 8.1 | 2.1 / 7.2 | 4.1 / 3.7 | 5.2 / 2.9 | 6.2 / 2.4 |
| bronze plate | 0.9 / 16.5 | 1.0 / 14.5 | 1.2 / 12.9 | 2.2 / 6.7 | 2.9 / 5.2 | 3.5 / 4.3 |
| iron plate | 0.6 / 23.3 | 0.7 / 20.4 | 0.8 / 18.1 | 1.4 / 10.8 | 1.8 / 8.4 | 2.1 / 7.0 |

The Smiler table is in the harness output (Level 3: none 7.6 / 2.0, sewn leather 3.6 / 4.2; Level 8: none 10.5 / 1.4, bronze lamellar 5.0 / 3.0, iron plate 1.7 / 8.6; Level 9: iron plate 2.3 / 6.7). Targets: unarmoured 2 blows at Level 3 and 1 to 2 at Level 8 (met); sewn leather 0.47 x the Level 3 hit (met: "halves"); copper and bronze lamellar need 3 blows even when every blow lands on the worst piece at Level 8 (met); iron plate at Level 9 needs 5 or more (met). Vanilla's armour numbers were enough, so no armour value was changed.

**Speed floor.** `Danger.RunFloor(d)` = 0.05 x (1.15 + 0.25 x min(1, (d - .36) / .46)) from d .36: Level 3 .0575, Level 5 .0620, Level 8 .0680, Level 9 and deeper .0700. Applied in `AiTaskMenace.Go` (the task, not the behaviour, owns the speed): any move at 0.75 x the entity's run speed or more is raised to the floor, a stalker's 0.8 x run keeping its share. Exempt (`Danger.NoRunFloor`): wretch, clump, duller (plan), plus mangled, roboman, faceling, faceling-child and the three Animations. The entity log prints `pace: danger, run, walk, hit, tier` at the start of every menace task. Measured: Smiler Level 3 .0575 (was .0554), Skin-Stealer .0575 (was .0399), Death Rat .0575, Hound .0687 (already above), Smiler Level 9 .0700, Wretch Level 3 .0532 (untouched).

**Settings.** Spawns off 1, verylow 2, low 3.5, normal 5.5, high 8.5, veryhigh 13; damage, mix and cap bonuses unchanged. Lang descriptions updated (en, es-419, es-es). `iso-rates` re-baselined at the new normal (+-35 %): Level 1 heartland bodies 8.5, threshold 73, Level 4 approach 20, Level 0 heartland 7.4, Level 9 threshold 330, Level 6 heartland 4.0, Level 1 heartland sounds 27; hard gap floor 1.6 min.

**Harness.** After the review fixes (pace line in invariant culture; Robo-Man exempt): `iso, iso-hound, p7, felt, needs, prog-armour, prog-speed`, 16 of 16 pass, 0 backrooms error lines. The blind reviewer (sonnet) found no save-compatibility problem; its real findings (iso-rates baselines, culture-dependent log line, Robo-Man's x2.4 jump) were fixed; the rest (Level 3 at 7.6 not 6, entities with their own tasks unfloored, `prog-speed` checking the formula not `Go`) are recorded here as decisions or open points.

**Not checked / open.** Spawns also drives spider nest refills (`MenaceSystem.Colony.cs`), hive waves (`round(Spawns)`: 4 becomes 6 on normal) and the Level ! difficulty mapping in `RunSystem.cs:360` (by setting code); all scale with the shift, not tuned. Entities with their own task (Bacteria and Giant Spider via Lurkers/Spider tasks, Watch, Partygoer, Deathmoth) get no run floor. Robo-Man and the Animations are exempt: a decision for the user (their base runs are .024 to .031). Vanilla's armour is strong enough that sewn leather and copper lamellar are close to each other (6.1 vs 6.0 at Level 8); the tier gap only opens at plate. Not run on a client: the felt result of 7.6-hit Level 3 Smilers with a 15-health player.

**Lessons.** Today's curve already met "2 to 3 blows at Level 3" for every hunter; the real gaps were the Level 9 plateau and the lack of a number to check armour against. Headless entities cannot walk, so speed is asserted from the log's `pace:` line, which computes from the same fields `Go` uses (a floor bug in `Go` itself would not show; a client or a movement trace would). A dummy near a level border can put an entity in the neighbouring level: derive expectations from the entity's logged danger.
