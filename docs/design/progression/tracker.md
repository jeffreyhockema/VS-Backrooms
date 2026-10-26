# Progression pressure: tracker

Reports from the pieces of [plan.md](plan.md), newest last.

### Piece C (resources)

Branch `prog/resources`. What changed:

- **Ore only in Level 8.** `UndergroundSystem.Borrow` wraps the borrowed `GenDeposits` column handler: for a chunk column whose middle lies in a macro cell that is not Level 8 it returns without generating deposits (ore, coal, minerals). Rock, caves and Level 8's own strata and ore (`WorldGenerator.Deep`) are untouched; soil deposits were already left out. Generated chunks keep what they have. `BackroomsModSystem.Layout` is a new public getter. `/backrooms ground` now also prints the level of the column (and works for a probe from the console).
- **Pleather.** `backrooms:pleather` (dark vinyl icon, `gen_breakdown.py`, like `rubble`), 1 to 2 from Level 1 wrecked cars (`Breakdown.Wreck`, C#), Level 4 office chairs (and tipped), Level 5 hotel chairs, wing chairs, sofas and long sofas (`salvage.py`). Armour `backrooms:armor-pleather-head/body/legs` reuses vanilla's leather shapes with a black recolour of vanilla's leather skin; recipes 5/8/7 pleather (no twine), repair recipes in vanilla's `armorrepair` pattern with pleather only. No vanilla recipe wildcard matches `pleather` (grepped `survival/recipes`).
- **Rat hides.** Death Rat's `game:hide-raw-small` drop was already 0.5 (every level); now 0.33 mean.
- **Wanderer** sells `game:gear-temporal` for 3 rusty gears (stock 1). Candles were already sold (1 rusty gear each).
- **Caches.** Levels 1 to 5: 12 % of a cache's "extra" is a temporal gear (`Rewards.EarlyGearChance`; the Level 1-6 pools had none before, Level 7+ keeps its 6 %). Toolboxes already held only a copper hammer (0.06), chisel (0.04), saw (0.04) and knife (0.08), never a pickaxe: left as they are.

Numbers, pleather against leather (vanilla "sewn" set, per piece): relative protection 0.24 against 0.60, flat reduction 0.24 against 0.60 (40 %), tier 1 both, durability 175 against 700 (a quarter). Cost: 5/8/7 pleather against 7/22/11 leather (+ twine).

Trade price: a Hound's bounty is 0.25 + danger rusty gears (0.4 at Level 1, 0.6 at Level 3, 0.8 at Level 5, doubled for an old one), so 3 gears is about four to five mid-level Hound kills.

Ore verification (headless, seed 12345, `/backrooms ground`): Level 0 column 512000,512000: y1-207 only `rock` and air, no `ore-*`; Level 8 column 516000,512000: bituminous coal, lignite, galena, native copper, sphalerite, cassiterite, hematite, quartz, olivine and so on. Startup log shows no errors.

Could not check: the pleather armour on a client (model, texture, repair, handbook), the recipe grid in game, the wanderer's trade window, rat drop counts in play (no `harvesttest` run; `harvesttest` needs a player), ore under a level boundary chunk (a column straddling Level 8's edge takes its middle's level).

Lessons: `tools/locked.sh run python gen_detail.py` and `gen_blocktypes.py` rewrite hundreds of files (EOL) and also pull drift from `salvage.py` into unrelated blocks (backpack, tent, camptent, seachest, desk, filing cabinet, writing desk, clump remnant): revert them with `git checkout HEAD --`; only `git diff --stat` shows real changes.

### Piece D (docs)

Branch `prog/docs` (worktree `VS Backrooms-prog-docs`), off `progression`. Model: haiku, per plan 3.9.

**What changed**
- `tools/gen_guide.py`: new page **What holds you here** (`PAGES["holds"]`, page code `backrooms-holds`): tiers, the
  three anchors and their recipes in words, the temporal gears, beyond-the-tier (about ten minutes to zero one tier
  beyond, three at two or more; hunters at zero; a minute at zero is a blackout into the level before, stability at
  half, no thin spot), Almond Water beyond the tier, armour as half a tier, `/backrooms ward`.
- Progression Guide: a "ladder of wards" section at the top (stone 0-2, copper 3-5, bronze 6-8/37/94, iron 9-11 and
  the far places, with where each tier's materials are and the Level 3 raid and 9th Road tin dash as the first trips);
  Pottery, Early Copper, Bronze and Iron Ages, the Late Copper ground paragraph, and the prospecting, smelting
  and stonelayers prefaces say that ore is only in Level 8.
- Levels page: each level's line gains its tier. Beyond-the-rings page: the same for 37, 94, !, Fun, The End, the Hub,
  974, 3999, 188 (the brief named only the levels page; the far places got the same line so the ladder reads whole).
- Entities page: an armour bullet (2-3 blows at Level 3, 1-2 by Level 8; leather, bronze, iron; pleather a little under
  half of leather; most hunters outrun a sprint from Level 3; Wretches, Clumps, Dullers the exceptions).
- Home page, Starter, Stability, Thresholds, tutorial step 14 (and its two no-waypoint variants): respawn is the last
  bed slept in, else Level 0; a temporal gear sets the waking place from any level. Home's "Where you wake" rewritten.
- Salvage: pleather (Level 1 car seats, Level 4 office chairs, Level 5 chairs and sofas, one or two a piece; never
  leather). Ore: only in Level 8, said where the rock and ore are listed.
- `assets/backrooms/lang/en.json`: regenerated by gen_guide (the only lang file it writes).
- `assets/backrooms/lang/es-419.json`, `es-es.json`: added `item-anchor-copper` "Ancla de cobre", `item-anchor-bronze`
  "Ancla de bronce", `item-anchor-iron` "Ancla de hierro", `item-pleather` "Polipiel". The check (the three anchors
  were absent from both files on this branch) found them missing, so they were added. Nothing else in the es files
  was touched; handbook text stays English there (P8).
- `docs/GUIDE.md`: a "What holds you here" subsection under Surviving (after Reality Stability); the progression
  section's ladder bullets; pleather in salvage; the Level 8 ore line; the armour bullet under Things that live here;
  tier lines under every level and far-place heading; the home and respawn bullets; "ten pages" in the handbook list.
- `README.md`: a "Levels and wards" table (README had no level table, so one was added under the features); the
  climb and respawn feature bullets.
- `CHANGELOG.md`: one Unreleased entry at the end of the section, "The climb.", in the what-you-notice voice.
- `docs/design/entity-difficulty.md`: new section 5 "Progression pressure" (damage targets per level, the speed floor,
  how to measure). Old 5 Rewards is now 6, old 6 To tune is now 7 (no references to those numbers elsewhere).
- `docs/design/entity-ai-overhaul/playtest.md`: section 11 "Progression", eight client steps from plan 7 (raid, blackout,
  copper anchor, pleather vs leather, tin dash, Level 8 bronze, Level 9 iron, wanderer prices).

**Results**
- `python tools/gen_guide.py`: writes en.json, 11 pages + 29 prefaces + 15 tutorial steps. `--check` reports
  **BROKEN LINKS: holds -> item-backrooms:anchor-copper, anchor-bronze, anchor-iron**, exit 1. Expected on this branch:
  the anchor item files are piece A's and do not exist here. Re-run `python tools/gen_guide.py --check` after piece A
  merges; it should then say "links ok".
- `python tools/gen_notes.py --check`: passes (exit 0, no output). No verbatim phrase needed restoring.
- Line endings: the edited files stay CRLF as before.

**Not checked / for the overseer**
- `src/GuideSystem.cs` (a .cs file, not touched by piece D): the `Added` array must gain `"holds"`, first, since the page
  follows the Progression Guide. Without it the page is in the lang file but not in the handbook's list. One line.
- Level 8's blow: the handbook says "one or two blows by Level 8" (decision 5, plan 3.5); plan 3.5's 10 to 12 at 15 HP
  is two blows. Wording is "one or two" in the handbook and the table in entity-difficulty.md says 2. Settle it with the
  `armourtest` numbers (piece B) and make the two match.
- Piece A and C claims the handbook makes: the three anchors and pleather items, the Level 3 raid numbers ("about ten
  minutes"), the wanderers selling a temporal gear for rusty gears (piece C), the ore change (piece C), respawn at the last
  bed (piece A), the gear working in any level (piece A). If any slips, the handbook text is what to fix.
- Flint: the knapping preface and the ground notes still say the ground under the floors "holds flint as any world
  does". Plan 3.6 does not list flint among the deposits skipped under the other levels; not verified, left as is.
- Spanish: the two es files already differ on two lines (`blockdesc-run-prize`, `run-prize-left`: "café" against
  "marrón") at HEAD. Not touched.
- Commit attribution: the session's attribution note names Claude Haiku 5.5, not the Fable 5.1 line in the brief; the
  commits carry the session's line.
- Not run: the game itself. The handbook renders only in game; the markup was checked by reading `to_vtml` and by the
  links check, not by looking at the handbook.

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

### Piece A (reality)

Branch `prog/reality` (off `progression`). Files: `src/Reality/Wards.cs` (tiers, deficits, Almond Water rule, wake table), `ZeroSystem.cs`, `RealitySystem.cs` (+ `.Ward.cs`, the `/backrooms ward` command), `src/Entities/MenaceSystem.Zero.cs` (`SendWorstHunter`), `WorldLayout.Reality.cs` (`WardTier`, `WardTierAt`), `Drinks.ApplyDrink` (one line), `BlockBackroomsBed` (spawn point, one line), `AtmosphereSystem` (blackout darkening), `tools/gen_wards.py` (anchor item, textures, recipes, lang), `AnchorSystem.cs` and `patches/temporalgear.json` removed.

**Tier table** (`WorldLayout.WardTier`): 0 for Levels 0, 1, 2, Hub, 974, and the Snackrooms (`WardTierAt`); 1 for 3, 4, 5; 2 for 6, 7, 8, 37, 94; 3 for 9, 10, 11, End, 188, Fun, !, 3999. Unknown ids (prototypes 21 to 23) ask 0. A wanderer's tier = worn anchor (copper 1, bronze 2, iron 3) + 0.5 for a full armour set (head, body, legs) whose lowest piece is at least max(1, anchor tier); armour tier from the material in the code (leather and hide 1; copper and the bronzes 2; iron, meteoric iron, steel 3; anything else, pleather included, 0). Tiers beyond = ceil(level tier - wanderer tier).

**Deficit derivation** (decompiled `EntityBehaviorTemporalStabilityAffected.OnGameTick`): each tick `V = (T - V) * dt` with `T = area - 1` (it assigns, it does not accumulate), the bar moves by `V/800` when V < 0 (`V/200` when positive). V settles at `T*dt/(1+dt)` and a second's ticks add up to 1 s of dt, so the bar drains `(1-area)/(800(1+dt))` per second whatever the tick rate (dt = 1/30 on the server; TickTime 33.3 ms). Full to zero = `826.7/(1-area)` s. Ten minutes needs area -0.378, three minutes area -3.593. Measured from the typical level baseline 0.75, the deficits are **1.128** (one beyond) and **4.343** (two or more); worse places drain faster, kinder ones slower (a Level 8 9th Road at 1.25 gives 15.7 min one beyond, 3.4 min two beyond). The hook's clamp is now -5..1.5 (a shift's own drain is still floored at -0.5 first). Side finding: vanilla's drain is slow (Level 3's 0.55 baseline alone takes about 30 minutes), so the deficits are what make depth bite. Vanilla's damage under 0.13 stability (0.15 HP per 4 s) is untouched; `temporalStorms` and rifts are off in `worldconfig.json`.

**Anchors**: `backrooms:anchor-copper|bronze|iron`, neck slot, vanilla Wearable on the rusty gear amulet model with generated gear and chain textures, no durability. Recipes (2x2 grid): copper = 2 copper ingots + temporal gear + candle; bronze = copper anchor + 2 of one bronze ingot (tin, bismuth or black) + gear; iron = bronze anchor + 2 iron ingots + gear. Lang en, es-419, es-es.

**Almond Water**: `WardTiers.Drink` in `ApplyDrink`: restore x max(0.2, 1 - 0.4 x beyond), ceiling 1.0 / 0.6 / 0.3 (a bar already above the ceiling is left alone). Blue and Green follow (same path).

**Zero**: `ZeroSystem` ticks each second over survival players and straw dummies. At stability <= 0.005 beyond the tier: `MenaceSystem.SendWorstHunter` once per zero episode (first of Giant Spider, Hound, Duller, Deathmoth, Skin-Stealer, Wretch, Smiler... that the roster hunts with; none in the Safe band, with entities off, or in Levels 6/7/10/!; retried each second until one is chosen; five placement tries). After 60 s at zero in any level but 0, Hub, 974, Snackrooms: the client darkens 3 s (`backrooms:blackoutUntil`, same 0.85 darkening and power-down sound as a Flickering, now in every level), then `ThresholdSystem.Send` (no thin spot, no way back, screen fade) to a random spot in `WakeLevel(level)`: level - 1; 1 -> 0; city -> 10, 37 -> 5, 94 -> 9, ! -> 37, Fun -> 1, End -> 4, 3999 -> 37, 188 -> 1. Stability 0.5, inventory untouched, lang `zero-blackout`, log lines. Respawn: any bed mount sets the spawn point; the temporal gear sets it anywhere (patch and class removed; `anchor-lost` and `anchor-refused` lang gone).

**Harness** (port 42781): `prog-ward` PASS (Level 3 tier 0: asks 1, beyond 1, deficit 1.13, bar lasts 494 to 565 s; ward 1: none; Level 8 tier 0: beyond 2, 4.34, 202 s; ward 2 none; Level 0 none), `prog-zero` PASS (Level 3 dummy at 0: Hound sent, lights go at 60 s, came to in Level 2, `/backrooms ward` then reports Level 2), `prog-zero-safe` PASS, `iso` PASS (both cases). Test hook: `/backrooms ward <0-3|clear>` gives the latest straw dummy a test ward.

**Could not check**: the actual drain clock (a dummy has no vanilla behaviour; verified by code path and the formula above, the harness checks the area value and the reported time); the worn anchor reading (inventory slots) and the player-matching of the stability hook by position (needs a client); the anchor's look on the model (UVs of the vanilla amulet sample only the corner of the texture, so it will read as a plain metal amulet); bed spawn on a real death; the client blackout darkening and sound; the crafting recipes in game (loaded without log errors only).

**Lessons**: command registration for a later system must wait for `ModsAndConfigReady` (`Get("backrooms")` is null in `StartServerSide` of an earlier mod system and the `?.` hides it). The stability hook only gets a position, so a player is found by exact position. The blind reviewer caught the bronze recipe syntax (wildcard code and `allowedVariants` belong in the ingredient). Left to piece D: `docs/DEVELOPING.md` and the survival-loop and 3999 plans still mention `AnchorSystem`; handbook text for tiers, anchors, the blackout and respawn.

Fix (Piece A): the armour half-tier was a no-op because Beyond() rounded up. Beyond is now fractional (0, 0.5, 1, ...); Deficit and the Almond Water ceiling interpolate linearly between the whole tiers (0.5 beyond = deficit 0.564). `/backrooms ward` prints beyond with one decimal; prog-ward checks ward 0.5 in Level 3 (beyond 0.5, bar 813 s against 523 s unwarded).

### Fix round (code)

1. Fractional beyond (above), harness updated.
2. AiTaskMenace run-speed floor guarded with `runSpeed > 0`.
3. WardTiers.Drink uses the cached layout (BackroomsModSystem.Layout), not CreateLayout per drink.
4. MenaceSystem.AtHome no longer needs Level 0 (home is the spawn point wherever it is).
5. ZeroSystem blackout callback skips the move if the player left or died.
6. Level ! difficulty: verylow/low -> 0, high/veryhigh -> 2.
7. Set pieces scale by `Difficulty.SetPieceScale` (sqrt of Spawns): night visits, hive waves, nest refills, Mangled and Beast event chances; comments say scale 1 and Normal 2.35. Ordinary spawn rolls unchanged. Needs self-test unaffected (it passes scale 1).
8. Death Rat raw small hide drop back to mean 0.5 (var 0.5); only deathrat.json regenerated.
9. Wanderer gear-temporal price 6 rusty gears (comment: about eight mid-level Hound bounties); only wanderer.json regenerated.
10. Comments: Difficulties note in MenaceSystem, iso-rates "about 7.1 minute mean".

Test: build OK; aitest --only prog,needs,iso: 10/10 passed (prog-ward, prog-zero, prog-zero-safe, prog-armour, prog-speed, needs-selftest 49/49, iso-rates, iso-one-kind), 0 backrooms errors in the log.

### Fix round (text)

- `tools/gen_guide.py` (and the regenerated `en.json`): the entities page's setting bullet has the new numbers (about 7 minutes on Normal, 20 / 11 / 4.5 / 3 for the others, one step busier than before, set-pieces by the square root); the home tagline, Kitty's House text and the rest-at-home lines no longer say Level 0 only; Skin-Stealers outrun a sprint from Level 3; the armour bullet has the hit counts and wear; the half-tier rule is fractional; "What holds you here" gains the variance and any-cause blackout sentences; temporal gear sources rewritten in the salvage, home and tier pages.
- Lang: `note-m14` no longer claims ore under every floor (also `tools/gen_notes.py`, its source); the Spanish respawn lines (home tagline, tutorial/threshold bullet, Kitty's text, the body paragraph) say you wake where you last slept; both files keep their BOM and comment lines and parse.
- Docs: GUIDE.md, DEVELOPING.md, CHANGELOG.md, entity-difficulty.md (3d table shifted, 5 and 7 wording), playtest.md section 10, dialin.md 3.1, plan.md 3.1 / 3.4 / 3.6 / 3.7, decisions 14 to 17, and the 5/8/7 pleather cost here.
- Results: `python tools/gen_guide.py` ran clean, `python tools/gen_notes.py --check` printed "links ok" and exited 0.

### Revision: piece C (text)

Branch `prog2/docs`, worktree `../VS Backrooms-prog2-docs` (from `progression2`). Text for the revision (revision.md 2.C).

- `tools/gen_guide.py`: `PAGES["holds"]` removed; the tier and anchor sentences gone from the starter, progression (now *The ladder of classes*), Reality Stability, the levels' tags, the far places' tags and the Lobby and first-climb text. Entities page: *Classes and placards* bullet. Food page: *Supplies by level*. Level 1 stairs shares in *Ways Between Levels* now one flight in sixteen down and in twenty-five up. Regenerated `en.json`; `python tools/gen_guide.py --check`: links ok. The `guide-holds-*` keys still sit in `en.json` until piece A's merge removes them (gen_guide does not delete keys it no longer writes).
- `tools/gen_notes.py`: new note `gate-class` (*Down in flint*, Pell, Level 2 track, last entry; text under 560 characters); `config/notes.json`, the catalogue and lang regenerated; `gen_notes --check`: passed.
- `tools/gen_dialogue.py`: the camp and outpost answers to *What lives around here?* gain a line on the classes and armour; regenerated; `--check`: 42 components, 121 lang keys, ok.
- `docs/GUIDE.md`, `README.md`: climb bullets replaced by the class list; *Classes and placards* section replaces *What holds you here*; the level tier lines removed; the README *Levels and wards* table is now *Levels and classes*.
- `CHANGELOG.md` 0.610.0: *The climb* bullet is the new gate (placards, classes, chat line, armour, scarcity by class, shortcuts a quarter as common in chunks not yet generated, blackout, respawn at bed), with the stability drain noted as tried and dropped after play-testing.
- `docs/moddb-description.md` and `.html`: the What's new climb bullet, the climb card, the feature bullet and the food card reworded; no anchors or tiers; no HTML comments.
- `docs/design/entity-difficulty.md` section 5: the stability side points to the blackout at zero; the handbook's blow wording updated (a Hound kills in one at Level 9).
- `docs/design/entity-ai-overhaul/playtest.md` section 11: rewritten for placards, the chat line, the story note, Level 3 pleather vs leather, scarcity, shortcuts, the blackout in a pocket, respawn, wanderer lines and prices.
- `docs/design/progression/plan.md`: status note at the top pointing to revision.md.
- `docs/DEVELOPING.md`: `WardTiers` removed from the `src/Reality/` line; `ZeroSystem` only.
- `docs/design/handbook-audit-0.610.md`: addendum for the revision.

Open for piece A's merge: `tools/gen_wards.py` (still names the anchors; piece A deletes it); `guide-holds-*` lang keys. Open for the play-test: the Level 2 placard reads THINGS HERE OUTRUN YOU (Class 3) while the Level 2 creatures are not from the outrun group; the brief's line for Class 3 was kept as written, so the wording may need a second look.

