# P7 round 5: dial-in

Written 2026-10-23 from the user's play-test after rounds 1 to 4 and eighteen answers taken the same evening
([decisions.md](decisions.md) items 19 to 34). Part of the [entity AI overhaul](README.md). Three workers in parallel
(section 6), each in its own worktree on a branch `dialin/<piece>` off `p7/dialin`; the overseer merges into
`p7/dialin`, runs the harness and the felt-rate check, loads a 0.514.0 world, rebuilds the zip, then merges to `main`.
Nothing here needs a layout version or breaks a save: runtime numbers, director logic, one new world-setting value
(worlds store the code string; old codes keep their meaning).

## 1. The note, and what the code does today

The user: *"the overall level of entities has ended up at the other extreme from where we started. It's a bit too rare
to see anything now, compared to 0.514. I like the new mechanics, but we need to dial them in. Today's setting could be
'very low'. Level 1 seemed more dangerous than any other level, maybe because of the lights-out event. Double check
spawning is aligned with lore. I never saw enemies in Level 94."*

What the numbers are (normal setting, Level 1):

| | 0.514 | today |
|---|---|---|
| Heart: mean wait for a body | ~2.3 min | ~34 min |
| Heart: mean wait for a sound | ~1.2 min | ~10 min |
| Approach: body | ~0.7 min | ~12 min |
| Threshold: body | ~0.4 min | ~4 min |
| Menacing cap (heart / approach / threshold) | 2 / 4 / 6 | 1 / 2 / 3 |

Three filters cut the felt rate below the table and none is logged: the one-kind rule skips the roll while anything
menacing is about; a stalker or hunter is dropped when any ray from the player's eyes reaches the spot; a roll with no
fitting floor is silence. `/backrooms ratecheck` counts rolls, not spawns.

Why Level 1 feels worst: it is the only level with guaranteed hunts outside dens. The Flickering fires in the outer
40 % of the ring; since round 4 it ignores the one-kind rule and the hard gap, always brings Hounds, retries until they
are placed, and they hunt until the lights return. The Screaming (Levels 1 and 2) brings Hounds in Level 1 too. Level 1
has four den kinds including Hound packs. Level 2 (Class 3) and Level 3 (Class 4) get bodies only from the ordinary
roll, half of them glimpses, with a solitude only 30 to 40 % below Level 1's.

Level 94: the user's visit was five minutes, in creative (creative players only get glimpses), partly standing still
(a doll: band Safe) or indoors (Safe). Level 94 has danger 0. Section 7 has the headless night test.

## 2. Lore (Wikidot Survival Difficulty; isolation.md section 2 has the quotes)

| Class | Levels | Solitude today | Solitude now |
|---|---|---|---|
| 0 / 1 | 0, 4, 6, 10, 37, End, Hub, 974 | 1.5 / 1.5 / 3.0 / 2.0 / 4.0 / 4.0 | unchanged |
| 1 | 1 | 1.0 | **1.3** |
| 2 | 5, 11 | 1.2 / 1.2 | unchanged |
| 3 | 2, 94 | 0.7 / 1.0 | 0.7 / **0.6** |
| 4 | 3, 7, 8 | 0.6 / 1.0 / 0.8 | **0.45** / 1.0 / **0.5** |
| 5 | 9, Fun | 0.6 / 0.7 | **0.3** / **0.4** |
| (3999: 1 with a Class 4 blackout; 188: 2 to 5) | 3999, 188 | 0.8 / 1.0 | unchanged |

`Roster.LoreClass(level)` is new: the table above as code, used by the one-kind rule (section 3.5). Level 10 loses its
barn-edge Hounds and Clumps ("No Hostile Entities"); Level 94 gets danger 0.4 (Class 3; the King's trial is unchanged).

## 3. Design

### 3.1 Six settings (piece A)

`worldconfig.json` values `["off", "verylow", "low", "normal", "high", "veryhigh"]`, names Off, Very low, Low, Normal,
High, Very high; `worldconfig-en.json` and both Spanish files get `worldconfig-backroomsMenace-Verylow` / `-Veryhigh`
and new descriptions; `GuiDialogCheats.Settings` lists the six. `MenaceSystem.Difficulties`:

| Code | Spawns | Damage | Entities | Mix | Cap bonus |
|---|---|---|---|---|---|
| off | 1 | 0 | no | | |
| verylow | 1 | 0.5 | yes | | |
| low | 2 | 0.75 | yes | | |
| normal | 3.5 | 1 | yes | | |
| high | 5.5 | 1.3 | yes | +0.3 danger on the body mix | +1 approach and threshold |
| veryhigh | 8.5 | 1.6 | yes | +0.6 danger on the body mix | +1 every band |

`Spawns` divides both mean intervals as today. New `Difficulty.MixDanger` and `Difficulty.CapBonus(band)`: `Weights(band,
level)` takes `d + MixDanger` (clamped to 1), `Cap(band, level)` adds the bonus. Unknown codes fall back to normal as
today. Resulting normal rates with the new solitude (menace typical of the band):

| Level 1 | Body | Sound |
|---|---|---|
| Heart | 25 x 1.3 x 1.3 / 3.5 = **12 min** | 7.5 x 1.3 x 1.3 / 3.5 = 3.6 min |
| Approach | 12 x 1.3 x 1.0 / 3.5 = **4.5 min** | 1.9 min |
| Threshold | 6 x 1.3 x 0.65 / 3.5 = **1.4 min** | 0.8 min |

Level 3 heart 25 x 0.45 x 1.3 / 3.5 = 4.2 min; Level 9 edge 0.3 min; Level 4 approach (its heart is Safe) 12 x 1.5 x 1.0
/ 3.5 = 5.1 min; Level 6 anywhere 25 x 3 x 1.3 / 3.5 = 28 min; Level 94 night hills 12 x 0.6 / 3.5 = 2.1 min, towns
(threshold) 1 min. `BodyMinutes` / `SoundMinutes` are unchanged. The user's target was "10 to 12 in Level 1's heart,
the edge 4 to 5": the approach band is that edge; the threshold is the last fifth and the gates.

### 3.2 The hard gap (piece A)

`EncounterRoll.HardGapShare` 0.4 -> 0.25. The exponential part uses `1 - HardGapShare`, so the mean stays as stated.

### 3.3 Bands (piece A)

`MenaceSystem.Rate`: approach from `Depth >= 0.5` (was 0.6), threshold from `Depth >= 0.8` (was 0.85). The den
frequency's `depth < 0.6` in `WorldLayout.Dens.cs` stays (worldgen).

### 3.4 Set-pieces and dens (piece A)

- **Flickering**: the start takes `BodyAllowed(target, watch, a)` again (round 4 removed it): no Flickering while
  anything menacing is about or inside the hard gap. Once started it is unchanged (Hounds always come, retried, hunt until
  the lights return). Cooldown stays 20 in-game hours. Chance per tick unchanged.
- **Screaming**: `a.Level == 2` only. `StartScreaming` keeps its Level 1 branch dead or drops it (worker's call; the rats'
  cues and rat hunters are what Level 2 uses). Guide text and CHANGELOG say so (piece C).
- **Level 1 Hound dens**: runtime only. `DenAt` is worldgen too (`PlaceDen` lays out bones and caches), so `DensL1` must
  not change: an existing world's cells would change kind under their decor. Instead `MenaceSystem.Rate` treats a
  Level 1 `DenKind.Pack` as no den (`a.Den = None`, no Threshold band, no den intervals, no dweller): the bones stay as
  a den whose pack has moved on. Put the rule in one place (`Roster.DenActive(level, kind)`), and use it wherever
  `DenNear` feeds the director or the hive/den systems (check `MenaceSystem.Hives.cs` and `Hives.cs` for a Pack case: a
  Pack den has no heart block, so probably nothing).

### 3.5 One kind at a time, by class (piece A)

`Roster.MaxKinds(level)` = `LoreClass(level) >= 3 ? 2 : 1`. `CountMenacing` stays (caps); new `CountMenacingKinds`
(distinct entity codes among the menacing entities within 64 blocks). `EncounterRoll.BodyMayCome(kinds, maxKinds,
sinceBodyMs, gapMs)` = `kinds < maxKinds && sinceBodyMs >= gapMs`; `Roll` and `BodyAllowed` pass the kinds count and the
level's max. The rate check's `menacing=<n>` becomes the kinds count. `iso-one-kind` (Level 1, Class 1) still holds.

### 3.6 Rosters and danger (piece A)

- Level 10: `Array.Empty<RosterEntry>()`; its sounds stay. Guide line (piece C).
- `Danger.OfLevel(Motion)` 0 -> 0.4 (comment: Class 3; its Animations hit and chase like Level 4's creatures).
- `Solitude`: 1 -> 1.3, 3 -> 0.45, 8 -> 0.5, 9 -> 0.3, Fun -> 0.4, Motion -> 0.6.
- The `iso-rates` harness expectations in `tools/aitest/run.py` are recomputed for the normal setting (`_rate` runs
  with the world's setting, which the test server leaves at normal): Level 1 heartland about 4 to 7 bodies/h, Level 1
  threshold 30 to 60, Level 4 approach 8 to 16, Level 0 heartland (no entry: rolls only) 3 to 7, Level 9 threshold 80
  to 160, Level 6 under 3, sounds Level 1 heartland 12 to 22. Run it once to centre the ranges rather than trusting
  these numbers.

### 3.7 Ambient Facelings (piece B)

`MenaceSystem.Ambient.cs`: `AmbientMinutes` becomes per level: 8 in Levels 1, 4 and 5 (`AmbientMinutesLived`), 15
elsewhere, 3 in Level 11 and the Snackrooms, 5 in Level 94 by day, as today. Caps unchanged.

### 3.8 Creative gets hunted (piece B)

`MenaceSystem.CreativeHunted` (bool, default false), `/backrooms creativehunts [on|off]` (toggles without an argument),
a button in the Creatures tab of `GuiDialogCheats` ("Creative is hunted on/off"). Where `creative` gates bodies and
set-pieces (`Direct`: the Flickering, the Screaming, `creative && kind != Glimpse`), `creative` is replaced by
`creative && !CreativeHunted`. The Level 94 doll rule and the rest are untouched.

### 3.9 The felt rate (piece B)

The headless server never moves entities, but the director's placement is deterministic enough to sample: a dry run.

- `TrySpawn(..., bool dryRun = false)`: finds the spot as today and, when `dryRun`, returns true without `SpawnPack`.
  Refusal counters (`refusedSpot`, `refusedSeen`, `refusedView`) are returned through an out struct `SpawnTry`.
- New partial `MenaceSystem.FeltRate.cs`: `/backrooms feltrate <level|here> [band] [tries=60]`: for the caller (or the
  latest dummy) runs `tries` dry runs for each of glimpse, stalk and hunt against the level's roster at that spot, and
  prints placement success per kind and why spots were refused (no floor / in sight / den dweller); then multiplies the
  success by `RateCheck`'s bodies per hour to print a **felt bodies per hour**. Cheat-menu button "Felt rate here".
- A **silent-failure counter**: `MenaceSystem` keeps per-level counts of body rolls that found no spot (`refused` by
  reason); `/backrooms menace` prints them for the player's level, and with the entity log on each failed ordinary body
  logs one line like the set-pieces' (`"{code}: no spot after 18 looks (...)"`).
- Harness case `felt-rates` (append to `tools/aitest/run.py`, selector `--only felt`): a dummy in each of Levels 1, 2,
  3, 4, 5, 8, 9 and 94 at night (`/time set 23` first, `/time set 12` after), in the approach band where the level has
  one (`min_band` as `Enc` does; Level 94: the hills), `feltrate` with 40 tries, asserting stalk-or-hunt placement
  succeeds at least 25 % of the time in every level, and recording the table in the tracker. The Level 94 row is the
  check on section 7's finding.

### 3.10 Docs (piece C)

- `tools/gen_guide.py`: the entities page's difficulty paragraph names six settings; Level 10's line says nothing
  hostile lives there; the Level 1 / Level 2 lines: the Screaming is Level 2's; the "What lives here" lines for Levels
  3, 8, 9 say they are busy. Run `python tools/gen_guide.py` and `python tools/gen_notes.py --check`.
- `docs/design/entity-difficulty.md`: section 3d, the six settings and the rate tables of 3.1.
- `playtest.md`: section 10 "Round 5: dial-in" (what each setting should feel like; Level 1 heart 10 to 12 min; Level 3
  busy; Level 10 empty; Level 94 night; the Flickering never on top of another encounter; creative toggle).
- `CHANGELOG.md` under Unreleased: one entry in the changelog's voice.
- README Status row: "P7 round 5 (dial-in) in progress".
- The Spanish `worldconfig-es-419.json` / `worldconfig-es-es.json`: piece A adds the keys; piece C checks the wording.

## 4. Not in this round

Model, sound or layout changes; the handbook rewrite (P8); Hound pounce or camouflage; progression pressure (tracker:
Pool_Party_Doge); corridor-versus-hall weighting in Level 1; Level 94's open-ground placement fix, unless section 7 shows
it is needed (then piece B owns it: a stalker or hunter in the open may be put down behind a hill crest or a house,
the sight test deciding; or at a greater distance, 30 to 48, when every nearer spot is in view).

## 5. Save and setting compatibility

No class, behaviour, attribute key or world-setting code renamed or removed. "off", "low", "normal", "high" keep their
code strings; a world on "normal" gets the new normal (decision 20). `DensL1` untouched (3.4). New task or roster
flags default to today's behaviour. Entities loaded from a save still despawn at once.

## 6. Pieces, owners and files

| Piece | Model | Branch | Files it owns |
|---|---|---|---|
| A director, settings, rosters, bands, set-pieces, dens | sonnet | dialin/director | `src/Entities/MenaceSystem.cs` (not `TrySpawn`'s body), `MenaceSystem.Roll.cs`, `Roster.cs`, `worldconfig.json`, `assets/game/lang/worldconfig-*.json`, `src/Cheats/GuiDialogCheats.cs` (the Settings list only), `tools/aitest/run.py` (`iso-rates` expectations only) |
| B ambient, creative toggle, felt rate, harness | sonnet | dialin/felt | `MenaceSystem.Ambient.cs`, new `MenaceSystem.FeltRate.cs`, `TrySpawn`'s signature and body (dry run) and the `creative` gates in `Direct` (small, coordinated edits to `MenaceSystem.cs`), `GuiDialogCheats.cs` (Creatures tab buttons), `tools/aitest/run.py` (append `felt-rates`) |
| C docs | haiku | dialin/docs | `tools/gen_guide.py` and the lang files it writes, `docs/design/entity-difficulty.md`, `playtest.md`, `CHANGELOG.md`, README Status row |

Each worker: worktree `../VS Backrooms-dialin-<piece>` on its branch off `p7/dialin`, builds with
`VINTAGE_STORY='G:\Games\Vintagestory' bash tools/locked.sh mod dialin-<piece>` from inside the worktree, runs its
harness cases against its build (`python tools/aitest/run.py --mods <build>/Mods --port <own port>`), spawns a blind
reviewer (sonnet, prompts.md), fixes, appends a report to tracker.md under "P7, round 5", commits on its branch, and
stops. Never stop a Vintage Story server by image name. The overseer merges A, B, C into `p7/dialin`, builds, runs the
full harness, `felt-rates`, a 0.514.0-world load, rebuilds `bin/backroomsss_0.515.0.zip`, and merges to `main` after
telling the peer sessions.

## 7. The Level 94 night test (overseer, before the workers start)

A straw dummy at a Level 94 arrival spot, `/time set 23`, entity log on, `dummies on`, ten real minutes: the band the
director gives it, how many sight tests were refused for a clear line, what was put down.

**Result (22:48, build from p7/dialin):** dummy at 512197 187 384248 (within 400 blocks of the mountain: band
**Threshold** on all 19 status lines, menace about 0.85 to 1.0). Sight tests **38 refused for a clear line, 1 hidden**:
every stalker or hunter spot within the 14 to 30 block band was in a clear line from the dummy's eyes. Bodies in ten
minutes: **one glimpse** (animation-clay, which wants to be seen) where two or three were due; the rest was silence with
no log line. The hypothesis holds: in the open at night the Animations cannot be put down as stalkers or hunters.
Piece B implements the section 4 fix (a wider second pass, 30 to 48 blocks, under open sky, the sight test still
deciding) and the `felt-rates` case's Level 94 row checks it (band Threshold at the arrival spots).

**Rerun on the merged build (23:53, the same test, dummy at 511979 187 383730, band Threshold):** sight tests 10 refused, 8 hidden; **seven bodies in ten minutes** (Hound hunt, Skin-Stealer glimpse, wooden Animation stalk, clay Animation hunt, a pair of clay stalkers, a paper stalker), one ambient. The open-sky second pass works; a night near a town at normal is busy, as decisions 25 and 27 intend (the user's play-test judges whether it is too busy).
