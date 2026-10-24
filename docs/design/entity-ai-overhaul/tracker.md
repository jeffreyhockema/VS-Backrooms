# Entity AI overhaul: tracker

One row per batch, kept current by the overseer; one report per batch, appended by its worker. Lessons at the end are
inherited by every later batch. The plan is [README.md](README.md).

## Batches

| Batch | Branch | Worker | State | Gate | Notes |
|---|---|---|---|---|---|
| P0 Senses, noise, harness | ai/p0-senses | Opus (code), Sonnet (harness), Haiku (buttons, docs) | merged | harness 11/11 | |
| P1 State machine v2; Hound and Smiler | ai/p1-machine | Sonnet x2, Sonnet blind review and fix round | merged (integration branch) | review fixed 9 findings; harness p1 cases pass but for one timing expectation | the integration branch for the release |
| P2 Skin-Stealer, Duller, Death Rat, Wretch | ai/p2-stealers | Sonnet | merged | headless decisions checked | health read as level-scaled effective values (Skin-Stealer base 51, Duller 20) |
| P3a Deathmoth hives, Clumps | ai/p3a-hives-clumps | Sonnet | merged | headless incl. blocksweep and save data | hive heart code is `mothhiveheart` (`mothhive` was taken by a worldgen prop); juvenile Clumps are full size (scale is per type) |
| P3b Facelings | ai/p3b-facelings | Sonnet | merged | headless: Evolved look, outburst trigger | outbursts only from breaking and fighting |
| P4a The Strider, the Spider, the Beast, the Thing, Partygoers | ai/p4a-senses | Sonnet | merged | headless: fear, colony | Partygoer hearing and the spider's lurk test kept bespoke (a like-for-like move would change them) |
| P4b The floating Watcher | ai/p4b-watcher | Sonnet | merged | headless: charge and beam; render reviewed | |
| P5 Levels | ai/p5-levels | Haiku | merged | roster diff matches section 8 | Level 5's extra hive dens dropped (worldgen, would need a layout version); Level 7 splash skipped (no such sound) |
| P6 Harvest and materials | ai/p6-materials | Sonnet | merged | headless: recipes load, harvest configs, venom on an arrow | venom via a Harmony patch on ReceiveDamage (under final review) |
| P7 Play-test tuning | | | waiting for the user's play-test | | client check-lists from every batch are the starting point |
| P8 Finish | | | not started | | |

## Reports

(Appended by each worker: what changed per entity, harness results, the client check-list with what was seen, numbers
changed, what was carried and why.)

### P0 (2026-10-18)

- **Code:** `src/Entities/Perception.cs` (SenseProfile from a task's `senses`, Belief, NoiseBus, sight / sense / hearing),
  `MenaceSystem.Probe.cs` (noise listening: doors via DidUseBlock, Firesalt via DidPlaceBlock, thrown things landing via
  OnEntitySpawn of IProjectile, jumps; the cost line; `/backrooms perceive`, `/backrooms dummy ...`); the director raises
  break, run and test noises; hits raise fight noise (AiTaskMenace.Hit, Strike.Hit except poison, a player striking a
  menace entity); a hunt cry raises cry noise. `Senses`: glass-aware ClearLine, Sneaking, test-dummy overrides.
- **Harness:** `tools/aitest/run.py`, 11/11 (dark and lit range, facing away, sneaking, noise heard and not, losing the
  trail after memory, fear, running, a director smoke run); 363 s on a fresh world.
- **Deviations from the plan:** thrown-object impact is 0.5 (plan 0.2), so a stone actually draws things off; lighting a
  firepit is not heard (no server event for it; Firesalt placement is); landing from a fall is not heard (only jumps:
  OnGround is not reliable server side).
- **Lessons:** console lines keep their trailing CR glued to the last argument, but int and double parsing tolerate it;
  give argument-less leaves an `OptionalWord("ignored")`. A generator run rewrites every file it touches with LF
  endings: restore line-ending-only files with `git checkout HEAD -- <files>` after checking `git diff
  --ignore-cr-at-eol --stat`. A dummy spot whose chunks never load answers "No floor"; pick another key.

### P4a (2026-10-19): senses for the Partygoer, the Strider, the Spider, the Beast, the Thing

- **Onto `Perception`:** the Partygoer's `Notices` (sight = `Perception.Sight` with `senses` 12/7/4, cone 70, sneak 0.6; while
  hunting a copy with all three ranges 12, cone 360); the Strider's `Visibility` (`Perception.Sensed` for touch, `Perception.Sight`
  with its own lit/dark light reckoning passed in through the new `light` argument, `glass` special, scan and chase cones as
  profile copies; its notice accumulation, lit and eye-contact multipliers stay on top); the Spider's trespass and hearing
  numbers now come from its `senses` (`touch`, `hearing`, `sneakFactor`); the unveiled Beast gets `senses` (30/20/10, fear 24,
  hearing 20), so the common menace task works from belief for him.
- **Kept bespoke, and why:** the Partygoer's hearing (running or a bang within `hearing`, flat: `Perception.Heard` would cut
  running from 6 to 2.4 blocks) and its disguise; the Spider's lurk test (gap-based, vertical limit, no line needed; `Sensed`
  would need a clear line and use the centre distance); the Strider's window peering, search and feint; the Strider's light
  (lamps and fires only, not the sky: `Sight` gets it through its `light` argument); the Thing's `senses` (`water`, hearing
  40) is read by `/backrooms perceive` only, since its task goes by depth and not by what it hears.
- **Strider:** fear (Hound, Smiler, Skin-Stealer, Deathmoths within 24 go to Leave, once a second, in its own tick);
  never placed within 200 blocks of Level 10's wall (`FindSpot`); `rangedDamageMul: 2` on its menace behaviour (any
  `IProjectile` source); names are "Strider of the Neighborhood Watch" (entity code unchanged).
- **Spider:** a noise of 0.5 or more within 24 blocks of a nest heart (`WorldLayout.NestHeartNear`, `MenaceSystem.Colony.cs`,
  hooked in `RaiseNoise`) wakes the nest's spiders (`AiTaskSpider.WakeFor`) and puts down one or two more from the nest's dark
  if fewer than three are about (45 s between); raw bushmeat x1 drop.
- **Thing:** a lit lantern or oil lamp under water within 12 blocks breaks the rush off for 20 s (`lampRange`, `lampBreakSeconds`).
- **Harness:** `/backrooms dummy place nest` (cheat-menu button "Dummy at a nest"). Headless: see the report to the overseer.
- **Lessons:** a headless world made without `backroomsLayoutVersion: 9` in `WorldConfig` is layout version 1 and has no
  spider nests. `encounter` leaves entities behind: filter log lines by position when counting.

### Integration (2026-10-19)

- All of P0 to P6 merged on `ai/p1-machine`; a final cross-batch blind review found 13 issues (the new blocks needed a
  copper pick through Breakdown's Structure class, venom kills paid no bounty, hive waves ignored the entities setting,
  Facelings shoved bite victims, statics surviving reloads, and smaller ones); all fixed in 8a4732a.
- Final harness on 26d667e: 20 of 21 pass, `p1-glimpse-to-stalk` skipped (no qualifying spot in 8 tries), and
  `p1-hunt-to-search` failed only because every spot's first path failed headless (entities never walk there, so the
  hunt fell back to Stalk by the old no-path rule); it passed in the previous full run (Search at 17 s). Treat it as
  flaky headless, and check hunts losing you in the play-test.
- Next: P7, the user's play-test with [playtest.md](playtest.md).

### P7, round 1 (2026-10-20): the user's first play-test

Six fixes, six Sonnet agents in parallel, each merged to main after its gate:
- **Spawning:** stalkers and hunters (and every pack member) are never put down where any player could see any part of
  them (seven rays per viewer, through glass too; no in-sight fallback); the Flickering retries its Hounds. Level 1 Hounds
  rarer (weight 1.0 to 0.35, Flickering cooldown 10 to 14 h); Level 0's distant sounds at most one per 75 s or more, no
  sound as a fallback there.
- **Combat:** nothing feared a candle (light 7 is under every threshold); what read as fear was the Hound slowed in any
  lit place, the stare-down still holding a struck Hound, and the Lobby rules refusing a struck creature's hunt. Now a
  struck creature hunts its striker anywhere, with a grudge (it keeps track of them within 16 blocks); a struck Bacteria
  runs at a full sprint. Hounds a wolf at Level 1 and a bear from Level 3 (bite 8 to 14, health 30 to 56, faster than a
  sprint), Skin-Stealers a brown bear from Level 1, Wretches outrun a sprint from Level 3 (table in entity-difficulty.md 3b).
- **Level 1 art:** cars were drawn in the Transparent pass whole; now opaque with cut-out (dithered) glass. The NO ENTRY
  plate is red with bold white NO / ENTRY and the roundel's bar.
- **Red Rooms:** the client eased into the red air over three to five seconds; it now switches at the wall in about half
  a second.
- **Way back:** the wall search stopped at doorways and refused one-block partitions, so half of Level 1's way-backs fell
  back to a thin spot; now 0% in Levels 0 to 3. Level 4's open office floors still fall back about 29% (no walls near).
- **Manhole:** each tunnel was one run inside one cell (9 to 34 blocks); from layout version 10 a flooded trunk tunnel with
  a clay bed runs through every Level 3 cell and every manhole joins it (at least 351 blocks reach). New worlds only.

Still to check in a client: the cars' dithered glass up close, the sign at 4 to 6 blocks, and the feel of the new
Hound, Skin-Stealer and Wretch. `p1-hunt-to-search` is flaky headless (fails on the unmodified build too).

### P7, round 2 (2026-10-20): piece A, director

Branch `iso/director`. The director rolls bodies and sounds as rates now (isolation.md 4.1 to 4.3, 4.6).

- **Code:** new `MenaceSystem.Roll.cs` (`EncounterRoll`: pure `Roll`, `BodyKind`, `BodyMeanMs`, `SoundMeanMs`, `BodyGapMs`; `/backrooms ratecheck`).
  `Direct` rolls once per tick for the place: body (glimpse/stalk/hunt, the `Sound` share of `Roster.Weights` dropped and the rest
  renormalised) or sound. A body is skipped while `CountMenacing(target) > 0` and within the hard gap; a successful `TrySpawn` sets
  `Watch.LastBodyMs`, a sound sets `LastSoundMs`. No fallback sounds anywhere (`NoFallbackSound` removed; `SoundGapSeconds(0) = 75` stays as a floor in
  `PlayDistantSound`). The Flickering and the Screaming wait for the one-kind rule and the hard gap, stamp `LastBodyMs`; cooldowns 20 and 24 in-game hours.
  `DirectByPlace` gives the roller the latest clocks of the group and stamps the result on every member. The `(1 + 0.8 * danger)` factor is gone.
- **Numbers (Roster.cs):** `BodyMinutes` 25 / 12 / 6 / den 3, `SoundMinutes` 7.5 / 5 / 3.5 / den 2, `Solitude(level)` per plan, `Cap` 1 / 2 / 3 (+1 at danger 0.5, +1 at 0.8),
  menace factor `1.5 - menace` clamped 0.5..1.5 and `/ Setting.Spawns` (in `EncounterRoll`). Hard gap 40% of the mean. One deliberate reading: the roll after the gap uses
  `p = tick / (0.6 x mean)`, so the overall mean interval stays the stated mean (gap 0.4 plus wait 0.6) instead of 1.4 x. (Confirmed by the overseer.) Rosters edited as 4.3 says; new `RosterEntry.LightsOutOnly`
  (Level 0 Smiler: Red Rooms and Reality Shift dark only); Level 0 Hound removed; `Level1HoundWeight` 0.2.
- **Ratecheck** (`/backrooms ratecheck <level> <heartland|approach|threshold|den> [hours]`, or `here`; button "Rate check here" in the Creatures tab; levels by internal id, Level 94 is 13). 50 h, setting normal, bodies/h (glimpse/stalk/hunt), sounds/h, mean and min body gap in min:
  - Level 0: heartland 1.5 (1.5/0/0), 4.7 snd, gap 40.3/18.2; approach 3.9 (1.8/2.1/0), 9.2 snd; threshold 11.4, 19.0 snd; den 22.0.
  - Level 1: heartland 2.2 (2.1/0.1/0), 6.8 snd, gap 27.5/12.1; approach 5.7 (2.2/3.0/0.4), 13.2 snd; threshold 16.7 (4.6/5.8/6.3), 29.8 snd, gap 3.6/1.5; den 33.8.
  - Level 4: heartland 1.2, approach 3.6 (1.5/1.6/0.5), 9.0 snd; threshold 11.5; den 22.3.
  - Level 9: heartland 3.2; approach 9.3; threshold 28.3 (5.8/9.0/13.5), 48.0 snd, gap 2.1/0.9; den 56.7.
  - Level 6: heartland 0.7 (gap 81/38), 2.3 snd; approach 1.9; threshold 5.7; den 11.5.
- **Harness:** `iso-rates` and `iso-one-kind` (inserted before `smoke`; `--only iso` runs both; port 42741 via the existing `--port`): both pass (iso-one-kind: a stalking Hound about a Level 1 approach dummy for 125 s, no other kind put down).
- **Decision taken (overseer):** Level 0's heartland keeps no body entry ("unknown whether entities exist"): the heart of the Lobby is sounds only, the Bacteria begins in the approach band.
- **Could not check:** these are rates of rolls, not of spawns: Level 0's heartland has no roster entry (by the decision above), so its 1.5 glimpses/h are silence in play,
  and a roll with no fitting spot (not-seen rule) is also silence, so the felt rate is lower than the table. `iso-one-kind` only proves anything if the director rolls a body in its two minutes
  (about 20% chance at that mean), so a pass is weak evidence; the code path is `CountMenacing > 0 -> return`. The rest of the harness (the old cases) was not re-run in full. No client play-test.
- **Review fixes (blind sonnet reviewer + overseer):** the gate is one pure function, `EncounterRoll.BodyMayCome(menacing, sinceBody, gap)`, used by `Roll` and the set-pieces; Level 0's hunt-to-stalk rule moved into `Roll` (`isWorst`); `ratecheck` takes a trailing `menacing=<n>`; the den row uses the Threshold band's kind split with the den intervals; ratecheck text is culture-invariant; a den dweller no longer bypasses `LightsOutOnly`. `iso-one-kind` is now deterministic (`menacing=1` gives 0 bodies, the control 5.3/h) plus the live Hound run compared by entity id. Not changed: two players' set-pieces starting in one tick (as before), `TickSeconds` duplicating `IntervalMs`.
- **Lessons:** the Bash heredoc fails on some content with quotes: write C# files with the Write tool; working tree is CRLF, index LF (autocrlf), so edit scripts must convert.
### P7, round 2 (2026-10-20): piece B, Hounds

- **Hound numbers (gen_entities.py `hound()`):** runSpeed 0.05 -> 0.062, `slowedByLight` removed, memorySeconds 8 -> 10, searchSeconds 10 -> 14; `huntsOnSight` replaced by `chargesWhenBacked` (+ `backTurnedRange` 16, `backTurnedSeconds` 2, `backTurnedCone` 70, `chargeCloseRange` 5) and `leavesAfterSearch`. Bacteria: `leavesAfterSearch` only. Other entities keep `huntsOnSight` and default to today's behaviour.
- **Code (AiTaskMenace.cs):** a Hound hunts only on: ran (today's rule, 1.5 s within 28), back turned (target not looking within 70 degrees of the Hound for more than 2 s, seen, within 16), nerve (StaredDown, spent for good), too close (believed within 5 with contact), or the existing unsteady / menace rolls. The trigger is in the entity log ("hunts: ran / back turned / nerve / too close / unsteady / menace"). Running beats the stare (a runner is not held). Re-sighting after Search / Investigate goes to Stalk, not Hunt (a struck Hound still goes straight to Hunt, and is not held by a stare while it has a grudge). It closes at a walk while it has them in sight (0.8 x run only out of sight). `EndSearch` -> Leave; a Hunt with no path (a shut door) -> Search (belief zeroed) -> Leave, for `leavesAfterSearch` entities (the Bacteria too: its Lobby fright with no path now ends in Search then Leave instead of a Stalk pause).
- **Test support:** `/backrooms dummy face toward|away|none` (Probe.cs, Senses.TestFaceKey; dummies can now stare a Hound down). **Needs a cheat-menu button in GuiDialogCheats.cs (piece A owns it), next to "Dummy: run": `B("Dummy: back turned", "/backrooms dummy face away", ...)` and `B("Dummy: looks at it", "/backrooms dummy face toward", ...)`.** (Done in 8cc9fbb as the buttons "Dummy: face toward" and "Dummy: face away".)
- **Harness:** new cases `iso-hound-nerve`, `-back-turned`, `-runner`, `-gives-up` (appended after the P7 cases, list `ISO_HOUND_CASES`, selector `--only iso-hound`); `p1-sight-hunt` now uses a dummy with its back turned (face away). Full suite on 8006df5: 27/29; the two failures were `p1-glimpse-to-stalk` (a crossing glimpse, flaky) and `p7-bacteria-chased` (never saw the dummy: spot-dependent); after the review fixes (build iso-hound2) the iso cases, p1-sight-hunt, p1-hunt-to-search, p1-glimpse-to-stalk, p7-hound-struck, p7-bacteria-chased all passed (a spot-finding failure of iso-hound-nerve and of bacteria-chased passed on rerun). Measured: nerve break 4.5 to 6.0 s after the stare begins; back turned 3.0 s after first sight (2 s + 0.9 s growl hold); runner 2.7 to 3.0 s. The plan's "no hunt for 6 s" is not testable (nerve is 4 to 8 s): the case asserts none before 3.2 s of stare.
- **Not verified headless:** doors (no way to place one on the console): shut-door behaviour is by the code path (no `opensDoors`; path fails -> Search -> Leave); the headless "gives up" case reaches Search by the same no-path rule, not by belief fade (`no way through` line). A door noise (0.3, heard within 9.6 blocks) goes through the same bus as `dummy noise`, which `p1-stalk-to-investigate` covers. `harvesttest` needs a player (client): not run; the Hound's harvestable block is unchanged (2 s both sides).
- **Review (sonnet, one round):** fixed a stare freezing a struck Hound after Spotted, `backTurnedFor` leaking across kinds, a noise behind a door bouncing Search -> Stalk -> Hunt (belief zeroed on no-path). Left: a player who keeps running audibly behind a door can still cycle Hunt/Search until the encounter budget ends; "too close" does not fire during a stare (the stare holds first).
- **Client check-list** (Level 1 outside the heartland so the band allows hunts; `/backrooms encounter hound stalk` then watch; /backrooms entitylog on shows the trigger):
  1. Stare-down: spawn a stalking Hound, stop and look straight at it. Expect: it growls, stops, backs a step; after about 4 to 8 s it howls and charges ("hunts: nerve"). Backing away at a walk while facing it for those seconds keeps it at distance.
  2. Back turned: spawn it, let it come into sight, turn your back and walk. Expect: about 2 s later (within 16 blocks) a growl and a charge ("hunts: back turned"). Walking away facing it never triggers this.
  3. Running: spawn it, sprint straight away (torch or not). Expect: it charges after a second or two ("hunts: ran") and catches you in under half a minute (it is faster than a sprint; light does not slow it).
  4. Out of sight: spawn a hunting Hound (`encounter hound hunt`), break the line (a corner, lights out, sneak, quiet). Expect: it goes to where it lost you, looks about for about 14 s, then leaves and does not come back; and with a shut door between you and it, it does not open it, searches at the door and goes.
- **Lessons:** the bash tool chokes on apostrophes in heredocs: write edit scripts with the Write tool. Generators need `VINTAGE_STORY=G:\Games\Vintagestory` in a worktree; a run rewrites all shape/entity files with LF (restore unrelated ones with `git checkout HEAD --`). Rebuild under a new tag while a harness runs on another build (the harness uses the build dir).

### Player feedback from the mod page (2026-10-23, relayed by vs-backrooms-ec)

- Kyle_Rick: entities spawn right in front of the player ("can see them spawn", has to keep looking behind). Covered by P7
  round 1's seven-ray rule and, for the Flickering, round 3's delay and recent-view rule; watch for more reports.
- Syfe: "constantly hunted even on the lower entity density". The isolation round (P7 round 2) thinned every setting.
- Pool_Party_Doge: flint tools from Level 1 lasted to the end because every entity can be outrun or outmanoeuvred, so there
  is no reason to progress tools or armour. Progression pressure, not spawn rate: P7 round 1 made Hounds wolf-to-bear and
  Skin-Stealers bear-strength; revisit once players have tried 0.515 (armour tiers by depth, creatures that cannot be
  outrun from Level 3).

### Spanish gaps for P8 (2026-10-23, noted by vs-backrooms-ec)

- es lang lacks `block-l3wallfixture-*-pipesbracket`, `-pipesjoint` and `block-run-wall-railshort-*`.
- `guide-levels-text`, `guide-entities-text`, `guide-farlevels-text`: the Spanish markup differs from the English.

### For P8, from vs-backrooms-ec's mod-page fact check (2026-10-23)

- The in-game handbook `guide-entities-text` (en.json) and the GUIDE's "What lives here" are stale for Dullers, rats,
  Facelings, Skin-Stealers and the Clump's levels.
- The mod page's lineup image `docs/moddb/img/42-what-lives-here.jpg` has no Watcher; re-render it if a new lineup is made.
- Fixed now: a fed Skin-Stealer turning hungry kept its clothed look (EntityBehaviorMenace).

### P7, round 5 (2026-10-23): piece A, director and settings

Branch `dialin/director` (off `p7/dialin`), not merged.
- **Settings:** six codes (off, verylow, low, normal, high, veryhigh) in `worldconfig.json`, the three worldconfig lang files and the cheat menu. `Difficulties`: spawns 1 / 1 / 2 / 3.5 / 5.5 / 8.5, damage 0 / 0.5 / 0.75 / 1 / 1.3 / 1.6; high adds 0.3 danger to the body mix and +1 cap in the approach and threshold bands, very high 0.6 and +1 in every band. Held in `Roster` statics set once by `Roster.ApplySetting` at world load (the rolls stay pure; `ratecheck` therefore always shows mix and caps of the world's setting). Unknown codes fall back to normal and log a line.
- **Director:** `HardGapShare` 0.25; bands from depth 0.5 / 0.8; the Flickering start takes `BodyAllowed` again; the Screaming starts only in Level 2 (the `scream` cheat still reaches the Level 1 Hound branch); Level 1 Pack dens are no den in `Rate` via `Roster.DenActive` (the only place `DenNear` feeds the director; Hives only look for Hive dens).
- **One kind by class:** `Roster.LoreClass` / `MaxKinds` (2 kinds in Classes 3 to 5: Levels 2, 3, 7, 8, 9, Fun, 94, 188), `CountMenacingKinds`, `EncounterRoll.BodyMayCome(kinds, maxKinds, sinceBodyMs, gapMs)`. Ratecheck's `menacing=<n>` is a kinds count; its output line says "n kinds of menacing thing about (of m allowed)".
- **Rosters:** Level 10 empty; Danger Motion 0.4; Solitude 1 1.3, 3 0.45, 8 0.5, 9 0.3, Fun 0.4, Motion 0.6.
- **Measured ratecheck (normal, 50 h; bodies/h):** L1 heartland 5.4 (11 min mean; sounds 18/h), L1 approach 14.2, L1 threshold 45, L3 heartland 16, L94 approach 33 / threshold 100, L9 heartland 23, L9 threshold 202, L5 approach 17, L2 approach 28, L4 approach 13, L0 heartland 4.5 (glimpses only), L6 heartland 2.2. Very high, L1 heartland: 13.5/h (2.4x normal), high 8.9, low 2.9, verylow 1.5, off 1.7 (rolls only; no bodies are put down).
- **Harness:** `iso` 2/2 (iso-rates recentred at +-35 % of the measured values, hard-gap floor 2.6 min; iso-one-kind), `iso-hound` 4/4, `p7` 4/4. All six setting codes load through `/worldconfig` plus restart with no warning; `bogus` logs the fallback and reads normal. Blind reviewer: no plan mismatches; fixed the stale ratecheck description and scream strings.
- **Could not check:** a client play (felt rate, Flickering gating live); the Flickering's new gate headless (the start needs a roll in the outer ring); the 0.514.0 world load (overseer).
- **Lessons:** `--withconfig` WorldConfig does not override the playstyle's `backroomsMenace`; to start a headless server on another setting run `/worldconfig backroomsMenace <code>`, stop and restart on the same data dir. An existing "low" world gets spawns 2 (was 0.6) and damage 0.75 (was 0.5): piece C's changelog should say so.

## Lessons

(Engine gotchas, profile fields that had to be added, harness quirks. Start here before P0: the gotchas in README
section 9 and in `docs/design/entity-models-todo.md` section 5.)

- **Never stop Vintage Story servers by image name** (`taskkill //IM VintagestoryServer.exe`, `Get-CimInstance ... | Stop-Process` on the name): several agents run headless servers at once, and two batches killed everyone's, which looked like a crash in the gate run. Stop only your own server, by PID, or by a command-line filter on your own data folder.
- Headless entities think but never walk, so paths "fail" and a hunt goes Hunt -> Stalk by the old no-path rule; test decisions by timeouts, and retry spots.
- With several agents' servers and builds running, everything is slow: a build may wait minutes for the lock; a harness run takes 15 to 20 minutes.

### P7, round 2 (2026-10-20): piece C, ambient

Branch `iso/ambient`. New `src/Entities/MenaceSystem.Ambient.cs` holds `SpawnAmbient`, `RatPacksNear`, `AmbientCap`, `MaxRatPacks` and a per-player `ambientNextMs` (cleared by one line in `PlayerDisconnect`); `MenaceSystem.cs` only lost the moved members.
- Numbers (all named constants): cooldown 15 real min (3 in Level 11 and the Snackrooms, 5 in Level 94 by day outside the castle), jitter 0.7..1.3, set only when `TrySpawn` succeeded; cap 1 within 48 (3 in Level 11 and the Snackrooms), counting every Ambient-kind creature (rats and fed Skin-Stealers included); Facelings 1 within 100 (Level 11: 3 within 48, Snackrooms 2 within 48); `MaxRatPacks` 1. A log line "ambient X put down by the wanderers' roll; the next in N s" with the entity log on.
- Headless (port 42743, seed 12345): Level 11 dummy, 3 cooldowns observed: hound at 21:50:02, faceling 21:53:39 (3m37), faceling-child 21:56:29 (2m50), so 2.1-3.9 min spacing and never above cap 3. Level 1 heartland dummy with a commanded Faceling, 200 s: no ambient from the wanderers' roll (log shows no "wanderers' roll" line). Smoke (`run.smoke`): 0 errors. Build 0 warnings.
- Not met: in Level 1 heartland a scavenger rat pack (x2, x4) still arrived at 150 s and 74 s. It comes from the menacing roll in `SpawnPack`, which only obeys `MaxRatPacks` (as the plan says), not the cap or cooldown.
- Could not check: a real client, the 15-minute cooldown end to end, Level 94 by day, the Snackrooms.
- Reviewer (sonnet, one round): no defects. Notes for the merge: the call site `rand.NextDouble() < 0.25` in `Direct` still exists (piece A's file; the cooldown gives the spacing, but the "roll once" wording needs that line removed); menacing-roll fed Skin-Stealers and scavenger packs do not start the cooldown; `--only smoke` in `run.py` runs nothing (smoke runs only without `--only`), I called `run.smoke` directly.
- Lessons: `Ctx.place` needs retries for a Heartland dummy (try several keys and read the band from `dummies off`).

### P7, round 2 (2026-10-20): integration (overseer)

- Merged to `main` in the order A (c5afcec), C (plus the removal of the 25 % pre-roll before `SpawnAmbient`, f3d9cb8), B
  (5547c56; conflicts in `tools/aitest/run.py` and this file resolved by keeping both sides, the case list now
  `ISO_CASES + ISO_HOUND_CASES`) and D. Cheat-menu buttons "Dummy: face toward / away" added for piece B's
  `/backrooms dummy face` (8cc9fbb).
- Gates: piece A had an independent blind review (shared body gate, den band, Level 0 rule folded into the roll: all
  fixed); the merged A + C build passed the full harness 26/27 (only the known-flaky `p1-hunt-to-search`); the Release
  build of the whole round (`bin/backroomsss_0.515.0.zip`, rebuilt 22:55) was run through the full harness again (see
  the session's final note below).
- Decisions taken on the way: the Lobby's heart is sounds only (no body entry; the Bacteria begins in the approach
  band); the 0.4 x mean hard gap plus a 0.6 x mean exponential keeps the stated mean; the Bacteria's Lobby fright with
  no way through ends in Search then Leave (it shares `leavesAfterSearch`); "too close" does not fire while a stare
  holds the Hound.
- Full harness on the Release build: 29/31, the two failures being `p7-bacteria-chased` (spot-dependent, passed on
  rerun) and `p7-hound-struck`: piece B's shut-door give-up sent a struck Hound to Search because an owner's blow clears
  the retaliation timer at once (`EndRetaliation`) and the grudge lives in `huntProvoked`. Fixed in 49e6dcb and 61cedfa
  (the give-up and the re-sighting rule key on `huntProvoked` too); rerun of `p7-hound-struck`, `iso-hound` and
  `p1-hunt-to-search` 6/6, zero error lines.
- Still to check in a client: everything in playtest.md section 9 (above all the four Hound counters, doors headless-
  untested, and the felt rate of bodies and sounds).
