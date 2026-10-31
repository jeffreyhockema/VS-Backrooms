# P7 round 2: isolation

Written 2026-10-20 from the user's second play-test note and a lore review. Part of the [entity AI overhaul](README.md);
the user's calls are in [decisions.md](decisions.md) items 10 to 18. Four workers in parallel (section 7), each in its
own worktree and branch `iso/<piece>`, merged to `main` by the overseer. Nothing here needs a layout version or breaks a
save: it is all runtime numbers and director logic.

## 1. The note, and what the code does today

The user: *"too many entities overall. Level 0 (Class 1 by lore): 4 or 5 monsters at the edge (1-2 Bacteria, 3 Hounds),
a few Hounds and a Bacteria on the way; in Level 4, at the end of the session, 2 Dullers and a pack of Hounds at once.
Encounters should be rare and terrifying; the player escapes only by skilful evasion or a special technique; running in
a straight line should not work on the dangerous ones (Hounds). Facelings should be a rare occurrence in the vast
emptiness (several in one big room of Level 1 today). Make seeing any living creature an event."*

Why it is like that now (`MenaceSystem.Direct`, `Roster`):

- The director rolls every 2 s with chance `(0.02 + 0.12 * menace) * (1 + 0.8 * danger) * setting`: in the approach band
  (menace about 0.5 to 0.9) that is a roll every 10 to 25 s. Each roll is a sound (45 %), a glimpse (25 %), a stalker
  (25 %) or a hunter (5 %); a failed or capped spawn still plays a sound. So a body about once a minute, a sound every
  half minute.
- Caps are 2 / 4 / 6 (heartland / approach / threshold) menacing entities within 64 blocks, so bodies pile up to the
  cap; nothing stops a second kind joining the first.
- Level 0's edge rosters Hound packs of 1 to 2 plus the Bacteria, at the threshold cap of 6.
- Ambient creatures (Facelings, scavenger rats, moths, fed Skin-Stealers) are rolled every tick at 25 %, with a cap of
  3 within 48 blocks and 2 Facelings within 48 blocks, so every big room refills.
- Hounds run at 0.05 base, exactly a sprint, and slow to 0.7 x while the player holds a torch: a lit straight run works.
  On sight they hunt at once (`huntsOnSight`), so the stare-down and the walk-away never come into play.

## 2. Lore (Wikidot, fetched 2026-10-20; see lore-2026-10.md section 11 for the fuller quotes)

| Level | Survival Difficulty | What the page says about how many |
|---|---|---|
| 0 | 1 (Safe, Secure, Unconfirmed Entities) | "It is unknown whether or not entities exist in Level 0" |
| 1 | 1 (Safe and Secure) | "Entities don't tend to wander within the corridors"; "entities tend to hunt during Flickering events" |
| 2 | 3 | "a variety of common and exclusive entities" |
| 3 | 4 | "Seeing one entity wandering by itself almost never happens" (brigades) |
| 4 | 1 | "mostly devoid of entities; Hounds and Dullers are the only ones" |
| 5 | 2 | "Normal entities are fairly scarce"; a large Deathmoth population in nests |
| 6 | pending | "no entities have been found on this level" |
| 6.1 | 1 | Facelings only, none hostile |
| 7 | 4 | "only one" (the Thing) |
| 8 | 4 (Extreme Hostile Presence) | "Some portions of Level 8 appear empty, devoid of entities altogether" |
| 9 | 5 | the streets "the most dangerous area" |
| 10 | 1 (No Hostile Entities) | "very few unique entities" |
| 11 | 2 (Safe, Unsecure, Low Entity Count) | "Facelings and Hounds, are the most numerous entities" |
| 37 | 0 (Devoid of Entities) | "entirely devoid of life" |
| 94 | 3 | "no entities during the day" |
| Fun | 5 (Entity Infestation) | "Partygoers are the dominant lifeform" |
| Hub, 974 | 1, 0 | one named entity each, rarely met |

Hounds (Entity 8, Level 1 and 3 pages): sight and hearing, **no smell anywhere**; "Hounds become hostile the moment they
see a human"; "intimidated when you give direct eye contact and stare them down. This won't work for long however, but
it should be enough time to get your bearings and make a run for it"; "if you hear a growling noise, its safest to stay
out of sight"; Don't "Run away from Hounds the second you see one"; Level 1: "intimidate it by visual contact and
noise. Otherwise, stay away from its path"; Level 3: "pouncing at them from behind", "When alone, Hounds will often
camouflage or hide themselves very well", packs bark to coordinate. Nothing on doors or climbing.

Where the lore is silent or in doubt, this round sides with isolation and desolation (the user's instruction).

## 3. The user's calls (decisions.md 10 to 18)

1. **Level 0: the Bacteria only.** Hounds removed from the Lobby. Smilers only in Red Rooms and while a Reality Shift
   has the lights out.
2. **Rate:** about one body (glimpse, stalker or hunter) per 20 to 30 real minutes in the heart of a Class 1 level;
   more toward the edge; deeper levels scale up from this.
3. **Hound counters:** stay out of sight (no scent, ever); the stare-down buys a head start; walking away calmly does
   not start the hunt, running or turning your back does; a shut door stops a Hound (it has no hands). Climbing a
   perch is **not** a counter (Level 3's Hounds pounce). **Light no longer slows Hounds**; light stays the Smiler's wall.
4. The Level 4 sighting was the same over-spawning; no bug hunt in The End.
5. **Facelings:** one at a time within about 100 blocks, about 15 real minutes apart per player. Level 11 keeps small
   groups (the lore's "most numerous"); the Snackrooms keep their staff.
6. **Wanderers** (traders) are untouched.
7. **Difficulty:** every setting is thinned by the same factor (the `Spawns` multipliers stay 0.6 / 0.6 / 1 / 1.5).
8. **One kind at a time:** while anything menacing is about a player, nothing else is put down; set-pieces (the
   Flickering, the Screaming, hive alarms, dens' dwellers, the Mangled's fog, the Beast, the King's trial, Level !'s
   horde) are the exceptions.
9. **Distant sounds cut hard too:** about one every 5 to 10 real minutes in a Class 1 level's heart; long stretches of
   nothing but the hum.

## 4. Design

### 4.1 Rates, not per-tick odds (piece A)

Replace the per-tick spawn chance with two independent rolls, each with a **mean real-minute interval** (exponential:
each 2 s tick rolls with `p = 2 s / mean`) and a **hard minimum gap** of 40 % of the mean after the last of its kind:

| Band | Bodies, mean min | Sounds, mean min |
|---|---|---|
| Heartland | 25 | 7.5 |
| Approach | 12 | 5 |
| Threshold | 6 | 3.5 |
| In a den | 3 | 2 |

Both intervals are multiplied by the level's **solitude** (bigger = lonelier; the lore table above):

| Level | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 37 | 94 | Fun | End | 3999 | 188 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Solitude | 1.5 | 1.0 | 0.7 | 0.6 | 1.5 | 1.2 | 3.0 | 1.0 | 0.8 | 0.6 | 2.0 | 1.2 | 4.0 | 1.0 | 0.7 | 4.0 | 0.8 | 1.0 |

and by the menace value: `x (1.5 - menace)` clamped to 0.5..1.5 (a calm player in the heartland waits longer, a noisy
unsteady one at the edge less), and divided by `Setting.Spawns` (off/low 0.6: longer; high 1.5: shorter). The
`Danger` curve no longer multiplies the spawn chance (solitude replaces it); the rest of `Danger` is untouched.

Worked examples (menace typical of the band): Level 1 heart 25 x 1.2 = 30 min; Level 1 approach 12 x 0.9 = 11 min;
Level 1 edge 6 x 0.6 = 3.6 min; Level 4 approach 18 x 0.9 = 16 min; Level 0 heart (Bacteria glimpses only) 37 min;
Level 9 edge 2.2 min; Level 6 anywhere 75 min. Sounds: Level 1 heart 9 min, edge 2 min.

The body roll picks **glimpse / stalk / hunt only** (the `Sound` share of `Roster.Weights` is dropped from it; the
split between the three keeps today's proportions, including the danger-added stalk and hunt shares). The sound roll is
its own. **No fallback sounds anywhere**: a capped or failed spawn is silence (`NoFallbackSound` generalised; the
Level 0 gap of 75 s stays as a floor).

### 4.2 One kind at a time, smaller caps (piece A)

- A body roll is skipped while `CountMenacing(target) > 0` (anything Glimpse / Stalk / Hunt / Investigate / Search /
  Leave within 64 blocks), and while the hard gap after the last body has not passed.
- Caps: heartland 1, approach 2, threshold 3; +1 from danger 0.5 (Level 5) and +1 from 0.8 (Level 9), as today's
  bonuses. Packs are still clipped to the cap. Set-pieces use the threshold cap as today.
- The Flickering (Level 1) and the Screaming (Levels 1 and 2) count as the place's body event: they set the last-body
  time and the hard gap, and they wait for the one-kind rule like any body. Flickering cooldown 14 -> 20 in-game hours,
  Screaming 14 -> 24. (The Flickering is the lore's Level 1 hunt: "entities tend to hunt during Flickering events".)
- Dens: a player in a den rolls at the den row above (dens are where things live); the dweller rule (75 %) stays.
- `CalmMs` after a close call stays.

### 4.3 Rosters (piece A)

`Roster.ByLevel`, exact edits; everything not listed stays:

- **Level 0:** remove the Hound entry. Smiler gets a new flag `LightsOutOnly` (put down only while `a.Worst` (a Red
  Room) or `a.Shift`). Bacteria unchanged (approach, Glimpse | Stalk, 0.6).
- **Level 1:** Death Rat 0.6 -> 0.4, pack 2-3; Hound `Level1HoundWeight` 0.35 -> 0.2, pack 1-2; Wretch 0.3 -> 0.2;
  Smiler 0.5 -> 0.4; Skin-Stealer 0.4 -> 0.3; Deathmoth female 0.4 -> 0.3, pack 2-4; Duller 0.5 -> 0.4; Clump 0.2.
- **Level 2:** Death Rat 1.0 -> 0.6, pack 2-4; Hound 0.6 -> 0.4, pack 1-2; Clump 0.5 -> 0.4; moth female pack 2-4.
- **Level 3:** weights unchanged (Class 4, brigades); Hound pack stays 2-3.
- **Level 4:** Duller 1.0 -> 0.6; Hound 0.3 -> 0.2, pack 1-1.
- **Level 5:** Hound 0.8 -> 0.5, pack 1-2; Skin-Stealer 0.6 -> 0.4; moth female 0.6 -> 0.5, pack 2-4; Wretch 0.3 -> 0.2;
  Death Rat pack 2-3; moth male ambient pack 1-2.
- **Level 8:** Death Rat 0.8 -> 0.5, pack 2-3; Wretch 1.2 -> 0.8, pack 1-2; Duller 0.5 -> 0.3; Smiler 0.6 -> 0.4;
  Hound 0.8 -> 0.5 (pack 2-3 stays); Giant Spider 0.7 -> 0.5.
- **Level 9:** Neighborhood Watch 0.7 -> 0.5; Watcher 0.4 -> 0.3; Death Rat pack 2-3; moth female pack 2-4; the rest
  unchanged (Class 5).
- **Level 10:** Hound pack 1-2; Clump 0.6 -> 0.4.
- **Level 11:** Hound ambient pack 1-1; Death Rat 0.6 -> 0.4, pack 2-3; subway Duller and Wretch unchanged, Wretch pack
  1-2 stays.
- **Motion (94):** Hound pack 1-2; moth male pack 1-2; the Animations unchanged (the level's own balance).
- **Dens:** Pack 2-3, Hive 2-4, Warren 2-4 (Dark, Lair, Nest unchanged).
- Levels 6, 7, 37, End, 188, 3999, Fun, Hub, 974, Run: unchanged (solitude does the work).
- `Cap`, `Weights`, `SoundGapSeconds`, `NoFallbackSound`: reworked as 4.1 and 4.2 say; new `Solitude(level)`,
  `BodyMinutes(band)`, `SoundMinutes(band)`.

### 4.4 Ambient creatures (piece C)

`SpawnAmbient` moves to a new partial `MenaceSystem.Ambient.cs` with its own per-player state (so piece A's edits to
`MenaceSystem.cs` and the `Watch` class do not collide):

- A per-player **ambient cooldown**: after any ambient creature is put down for a player, none for `AmbientMinutes`
  real minutes: 15 by default, 3 in Level 11 and the Snackrooms, 5 in Level 94 by day (the stop-motion rats are its
  charm). Jitter 0.7..1.3. The roll itself happens once when the cooldown has passed (no 25 % per tick).
- `AmbientCap` 3 -> 1 within 48 blocks (Level 11 and the Snackrooms 3).
- Facelings: at most **1 within 100 blocks** (Level 11: 3 within 48; Snackrooms as today). The ambient cooldown covers
  the "15 minutes apart".
- Scavenger rat packs: `MaxRatPacks` 2 -> 1; a pack counts as one ambient spawn for the cooldown. The heartland's
  menacing-roll rats that become scavengers (`SpawnPack`) obey the same pack cap.
- Fed Skin-Stealers put down as wanderers count against the cap and cooldown like any ambient.
- The Snackrooms and the "near a wanderer" allowance keep today's behaviour but for the cap and cooldown above.
- Nothing changes for wanderers (`WandererSystem`).

### 4.5 Hounds (piece B)

`tools/gen_entities.py` `hound()` and `AiTaskMenace.cs`:

- **Faster than a sprint:** `runSpeed` 0.05 -> 0.062 (1.24 x a sprint at danger 0; 1.28 x in Level 1; 1.5 x in Level 9),
  `walkSpeed` unchanged. A straight run loses about a block a second at Level 1: a 20-block head start is gone in half
  a minute. Update the comment and docs/design/entity-difficulty.md 3b (piece D does the doc).
- **Light does nothing:** `slowedByLight` False. (A carried light still makes you visible from farther: `carriedLight`
  1.5 stays.) Check `fearsFire` stays: fire is a different counter.
- **No instant hunt on sight.** `huntsOnSight` is replaced for the Hound by a new task flag `chargesWhenBacked` (other
  entities keep `huntsOnSight` as is). A Hound that sees its target in the approach band or worse closes to
  `stalkMin` at a walk, growling (the growl before the charge stays), and turns to the hunt only when one of these
  holds:
  1. the target runs (`runningFor > 1`, within 28 blocks: today's rule);
  2. the target's back is turned (not `Senses.LooksAt` the Hound within a 70-degree cone) for more than 2 s while
     within 16 blocks and seen;
  3. its nerve breaks under a stare (today's `StaredDown`, 4 to 8 s, spent for good: the charge that follows is the
     lore's "won't work for long");
  4. the target is within 5 blocks;
  5. the existing stability and menace rolls (unsteady, or menace 0.8 and worse).
  Facing it and backing away at a walk is therefore safe for the few seconds of its nerve, which is the head start.
  Record the trigger in the entity log line ("hunts: ran" / "back turned" / "nerve" / "too close").
- **Stay out of sight works.** `memorySeconds` 8 -> 10, `searchSeconds` 10 -> 14. New task flag `leavesAfterSearch`
  (Hound True): a Search that ends without a sighting goes to **Leave**, not back to Stalk (today `EndSearch` may
  return it to following, and the vague track brings it near again). A hunt that loses its belief still goes to
  Search as today. Bacteria: set `leavesAfterSearch` True too (the Lobby fright should end when you hide).
- **Doors.** Hounds have no `opensDoors`; a closed door is a pathing wall. Verify headless that a Hound sent on a hunt
  with a shut door between it and the dummy ends in Search then Leave (no path through, no pacing forever: `NoPathLately`
  rules), and that a door noise sends a stalker to Investigate the door. Fix what is broken; add nothing new.
- Give-up distance (40 + 25 d), patience (20 s without blood + 15 d), the pack bark, the stare, `fearsFire`, doors and
  armour stay. No model change. No new sound.
- Harness: cases in `tools/aitest/run.py` (append after the P7 cases): (a) a stalking Hound with a dummy facing it and
  still does not hunt for 6 s and does by 12 s (nerve); (b) a dummy with its back turned within 16 blocks is hunted
  within 4 s; (c) a dummy that runs is hunted; (d) after `/backrooms dummy` goes dark and out of line while hunted, the
  Hound reaches Search and then Leave (no return to Stalk). The headless server does not move entities, so test the
  decisions by timeouts as earlier batches did (tracker Lessons).

### 4.6 The rate check (piece A)

The roll logic becomes a pure, testable piece: `EncounterRoll` (a static class or a small struct in
`MenaceSystem.Roll.cs`) that, given band, level, menace, setting, the elapsed gaps and a `Random`, says "nothing",
"sound" or "body: glimpse / stalk / hunt". `Direct` calls it; so does a new console command
`/backrooms ratecheck <level> <band> [hours]` that runs it over N simulated hours of 2 s ticks (menace at the band's
typical value: heartland 0.3, approach 0.6, threshold 0.9) and prints bodies per hour by kind, sounds per hour and the
mean gap. Cheat-menu button in the Creatures tab ("Rate check here" for the player's current level and band). A
harness case `t_iso_rates` asserts: Level 1 heartland 1.4 to 3.4 bodies/h; Level 1 threshold 10 to 22; Level 4
approach 2.5 to 5.5; Level 0 heartland 1 to 2.5 (glimpses only); Level 9 threshold 18 to 40; Level 6 under 1.2; sounds
Level 1 heartland 4 to 10 per hour. A second case `t_iso_one_kind`: `/backrooms encounter hound stalk` on a dummy in
Level 1's approach band, `/backrooms dummies on`, director running two real minutes with `entitylog on`: no entity of
another kind is placed for that dummy while the Hound is about.

### 4.7 Docs (piece D)

- `tools/gen_guide.py`: the Hounds entry of the entities page (today lines near "**Hounds** (Level 1's dark
  sections…"): drop "glimpsed at the edge of Level 0"; the counters become the lore's: stay out of sight (they have no
  nose: break the line, stop, go dark and quiet, and it searches where it lost you, then gives up); stare it down for a
  few seconds and back away at a walk, facing it (running or turning your back brings it); a shut door stops it; light
  no longer slows it; from Level 1 it outruns you. The "Every level is worse than the last" bullet: "from Level 3 a
  Hound outruns you" -> "a Hound always outruns you". Level 0's and Level 4's level lines say how empty they are. Run
  `python tools/gen_guide.py` and `python tools/gen_notes.py --check`.
- `docs/design/entity-difficulty.md`: a section 3c with the Hound's new speed row and the rate table of 4.1.
- `docs/design/entity-ai-overhaul/playtest.md`: a section 9 "Round 2: isolation" check-list (rates felt, one kind at a
  time, Hound counters one by one, Facelings, Level 0 and 4 empty, sounds rare).
- `CHANGELOG.md` under Unreleased: one entry for the whole round, in the changelog's voice (what the player notices,
  not the mechanism).
- `docs/design/entity-ai-overhaul/README.md`: the Status row for P7 says "round 2 (isolation) in progress".

## 5. Not in this round

Hound pounce from behind; Level 3 Hound camouflage; noise intimidation ("intimidate it by… noise": no shout in the
game); scent for anything; Level 1 corridor-versus-hall spawn weighting (the halls are where the lore puts entities,
but the layout does not expose that cheaply); any model, sound or layout change; the handbook rewrite (P8).

## 6. Save and setting compatibility

No code, class, behaviour, attribute key or world setting renamed or removed. `backroomsMenace` values keep their
meaning (all thinned alike, decision 16). Entities loaded from a save still despawn at once (unchanged). New task
flags default to today's behaviour for every entity but the Hound and the Bacteria.

## 7. Pieces, owners and files

| Piece | Model | Branch | Files it owns |
|---|---|---|---|
| A director, rates, rosters, rate check | sonnet | iso/director | `src/Entities/MenaceSystem.cs` (not `SpawnAmbient`), new `MenaceSystem.Roll.cs`, `src/Entities/Roster.cs`, `src/Cheats/GuiDialogCheats.cs`, `tools/aitest/run.py` (cases inserted before `smoke`) |
| B Hounds | sonnet | iso/hound | `tools/gen_entities.py` (`hound()`, `bacteria()` flag only; regenerate), `src/Entities/AiTaskMenace.cs`, `tools/aitest/run.py` (cases appended after the P7 cases) |
| C ambient | sonnet | iso/ambient | new `src/Entities/MenaceSystem.Ambient.cs` (moves `SpawnAmbient`, `RatPacksNear`, `AmbientCap`, `MaxRatPacks` out of `MenaceSystem.cs`; the only edit to `MenaceSystem.cs` is that removal) |
| D docs | haiku | iso/docs | `tools/gen_guide.py`, `docs/design/entity-difficulty.md`, `docs/design/entity-ai-overhaul/playtest.md`, `CHANGELOG.md`, README Status row, lang files gen_guide writes |

Each worker: worktree `../VS Backrooms-iso-<piece>` on its branch off `main`, builds with `bash tools/locked.sh mod
iso-<piece>` from inside the worktree, runs the harness against its build, spawns a blind reviewer (sonnet, the prompt
in prompts.md with "iso/<piece>" for the branch), fixes, re-runs, appends a report to tracker.md under "P7, round 2",
commits on its branch, and stops. The overseer merges A, then C, then B, then D, builds, runs the full harness and the
0.514.0-world load, and rebuilds the play-test zip.
