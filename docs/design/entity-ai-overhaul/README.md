# Entity AI overhaul: the release after 0.514.0

Written 2026-10-18 from a review of the current code (`src/Entities/`, `src/Regions/`, the three entity branches in
progress), the current Wikidot pages (fetched 2026-10-18; Fandom and Miraheze as second opinions) and a ChatGPT
analysis the user brought. Owner: the user. Planning and gate reviews: a Fable session. The work: Opus sessions, one
per batch, following [prompts.md](prompts.md). Progress: [tracker.md](tracker.md). The user's calls:
[decisions.md](decisions.md). Target version: **0.515.0**.

**Not started.** This is a plan for agents to carry out when the user says so. Nothing below is built.

## Status

| Phase | Batch | State |
|---|---|---|
| 0 | P0 Senses, noise, harness | not started |
| 1 | P1 State machine v2; Hound and Smiler | not started |
| 2 | P2 Skin-Stealer, Duller, Death Rat, Wretch | not started |
| 3 | P3 Deathmoths, Clumps, Facelings | not started |
| 4 | P4 The Watch (Strider refined, Watcher built), the Spider, the Beast, the Thing | not started |
| 5 | P5 Levels: rosters, sounds, danger | not started |
| 6 | P6 Harvest and materials | not started |
| 7 | P7 Play-test tuning | round 1 merged 2026-10-20; round 2 (isolation) in progress, see isolation.md |
| 8 | P8 Finish: handbook, guide, changelog, release | not started |

## 1. Why, and what this is not

The mod already has an entity director (`MenaceSystem`) that rates each player's danger every two seconds by band
(heartland, approach, threshold), depth into the level, light, Reality Stability, noise, exposure and Reality
Shifts, and puts down distant sounds, glimpses, stalkers and hunters from a per-level roster (`Roster.cs`). Every
roster entity has its own model, sounds, counters and a share of special code. The far places have scripted
creatures of their own. `docs/design/entity-plan.md` (the original plan and its status), `entity-difficulty.md` (the
danger curve) and `entity-models-todo.md` (behaviour follow-ups) record how it got here.

**What is wrong is not the roster. It is that the entities are omniscient.** A stalker or hunter put down by the
director always knows exactly where its player is (`target.Pos`) and paths straight there. Nothing in `AiTaskMenace`
sees or hears; line of sight is used only to place spawns, to check a stare and to land a blow. Only three creatures
perceive today: the Partygoers (a real sight cone by light, hearing of running and bangs), the Clumps (a noise
threshold) and, on their branches, the Neighborhood Watch (sight by light, through glass, with a search and a feint)
and the Giant Spider (noise within earshot). So an encounter cannot be *lost*: you cannot slip round a corner, put
the torch out and wait, or draw a Hound off with a noise. Hiding, which every wiki page tells the wanderer to do,
does nothing. That is the overhaul.

The second thing is that the lore has moved on, and the ChatGPT analysis the user brought is a less-informed version
of the roster we have (it did not know the mod, the engine or half the lore). Section 3 says where it is right, where
the current Wikidot pages contradict it, and what we do.

**This is not:** a new roster (the three new creatures, the Strider of the Watch, the Spider and the Beast, are being
built on their own branches now and are refined here, not made here; the one creature this plan adds is the floating
Watcher, in P4); a layout change (no new layout version: runtime placement instead); a rewrite of the far places'
scripted creatures (Kitty, the Keymaster, the attendants, the Windows' arm and the Level ! horde stay as they are); a
change to any existing entity's model (texture looks excepted where the plan says so).

**Saves must keep working** (`docs/DEVELOPING.md`, "Keeping saves working"): no entity, item or block code changes,
no renamed behaviour or class, new entity attributes with defaults, world config codes unchanged. Section 10 lists
the surface.

## 2. Pillars

The five pillars of `entity-plan.md` stand (menace before harm; the edge is where it gets dangerous; every entity has
a counter the player can earn; lore first, then Vintage Story; cheap where it can be). Three are added:

6. **They find you the way a thing with eyes and ears would.** Every entity has senses, and what it does follows from
   what it has seen and heard, not from where you are. Dark, quiet and out of sight are real counters.
7. **An encounter can be lost, by either side.** You can lose them; they can lose you. Nothing follows you for ever,
   and nothing finds you by magic.
8. **Killable means hard and worth it; evade-only means the game tells you why.** Eight entities can be fought and
   harvested with a reason to; the rest are not fought, and the reason is shown (no body to hit, it flees through a
   wall, it is too large, it is not of this place), never a wall of hit points.

## 3. Lore reconciliation: ChatGPT, Wikidot, the mod

Source order, as the user asked: the current Wikidot page first; older Wikidot revisions and Fandom where Wikidot is
silent, trimmed or under rewrite; then Vintage Story adaptation, marked as such. The lore researcher's full brief is
reproduced in [lore-2026-10.md](lore-2026-10.md).

**Entity numbers.** ChatGPT's and the old plan's numbers are wrong. Wikidot: Deathmoths 4, Clumps 5, Dullers 6, Hounds
8, Facelings 9, Skin-Stealers 10, Beast 18, Death Rats 24, Mangled 63, Partygoers 67, Neighborhood Watch 96. There is
no spider entity page (Level 8's arachnid link is a dead `entity-xxx`). Handbook text that quotes a number must use
these.

### 3.1 Where ChatGPT is right and the mod already does it

Facelings as neutral people who turn when provoked, with children (built); Hound stare-down (built); Deathmoth males
passive and females defending the hive with an alarm (built); Smilers frozen by eye contact and roused by running
(built); Dullers fleeing when faced, grabbing through walls, stealing (built); Clumps buried with a limb out, hunting
by noise, feeding (built); Partygoers as a lure, a pack, a latch, a berserk chest and a disguise (built, more than
ChatGPT asked); the Thing as territory, light as its counter (built except the light); the Mangled as an escalation
event with its own weather, not a mob (built); Kitty peaceful and offended by vandalism (built); Level 0 empty but for
the Bacteria (built); Level 4 mostly peaceful (built, Safe heartland); Level 6.1 Facelings only (built); Level 10's
fields safe (built); Level 11 passive (built); Level 37 and the Hub entity-free (built); Level ! as a scripted horde
(built); the End's deceptive exits with Partygoers behind the terminals (built); Level 94's Animations (built, which
ChatGPT did not know); no Partygoers in Level 3 (we never had them there).

### 3.2 Where the current Wikidot pages correct ChatGPT, and what we do

| Topic | ChatGPT | Current Wikidot | Mod today | This plan |
|---|---|---|---|---|
| Dullers' home | Primary Level 1, occasional 2, 3, rare 4 | Level pages name **1 and 4** ("Hounds and Dullers are the only ones" in 4); the entity page says "lower levels" | 3, 4, 6, 8, subway | Add Level 1 (approach band, behind room walls); keep 3, 4, 8, subway; **drop 6** (below) |
| Level 6 | "No confirmed entities": agree | "no entities have been found on this level"; the sounds are hallucinations | Smiler (0.3) and Duller (0.8) spawn there | **Eyes only (user's call).** The Mimicry stays; Dullers go; the one body ever put down is a rare Smiler *glimpse* that never approaches or hunts, since the page itself keeps an archived note of an unidentified attacker |
| Smilers and light | Attracted to light; calm eye contact holds them | "attracted to light", pursue a light carrier; eye contact, do not run | Never enter light ≥ 8; frozen by a stare | **Hybrid (user's call):** a carried light is seen from farther and draws them to its edge, where they stop; eye contact freezes; running or noise brings them to the edge faster. Light stays a wall |
| Skin-Stealers in Level 2 | Keep them there as the older reading | Left Level 2 after the two-year blackout ("do not appear to have returned") | Not in Level 2 | No change: the mod already agrees with Wikidot |
| Skin-Stealer and Duller killability | Evade-only | Wikidot lists no weakness and never kills one | Both killable; Skin-Stealer hide feeds leather | **Both stay killable, much harder (user's call)**, section 6 |
| Hounds | Moderate, pairs dangerous; flesh unsafe | "hostile the moment they see a human"; "made aggressive when they see someone in an aggressive state"; hide when you hear growling; Level 3 packs **bark to coordinate**; Fandom: the pelt is "one of the only sources of leather" | Pack of 2–3, stare-down, fire, light slows | Sight-driven hostility, growl as a warning before it has you, bark-and-answer pack coordination, hiding works. Hide and bushmeat stay (the pelt is lore) |
| Deathmoths | Castes, light attraction, Praetorians rare | Current rewrite: males 30–35 cm scavengers, females 40–45 cm hunters with caustic fluid and rally pheromones, **larvae with paralytic quills**, Praetorians (~15%), one Empress per level; light attracts; Level 5 is "one of the many central hives"; Level 3's males are aggressive too; Level 2 declining | Males and females built; hives are dens | Hive dens get a heart (larval columns as blocks), waves on disturbance; **quills as the lore-grounded harvest** (section 7); Praetorian as an optional den guardian (own model, deferred to a later release unless time allows) |
| Death Rats | Scavengers that flee healthy players | Under rewrite; "most Death Rats are harmless and can be a food source"; Level 2's are bald and "virtually zero threat"; Level 3's are capybara-sized engineers; they eat male Deathmoths and mould; the Screaming | Packs that nip; hairless in 2; Screaming | Skittish scavengers: they go for food on the floor and bodies, scatter from a walking player, nip only when cornered, hungry-pack or at the edge; Level 2 harmless; engineer rats deferred |
| Clumps | Fragile grapplers, dormant after feeding, burn remains | "bundle of human limbs", brittle bones, "within eight feet", dormant after a meal "leaving only their longest limb out", **remnants left uncleaned grow a new smaller Clump**; "retreat at the sound of multiple people running"; Levels 2 and 10 (rewrite), 1, 2, 3 (level pages) | Buried, hunts by noise, grabs, feeds, buries | Lower health, harder grab; **remnant** mechanic (a killed Clump leaves a remnant block that grows a juvenile unless burnt); hearing of running tuned to the lore |
| Wretches | Killable, former humans, some weapons | Entity 15 as the brief has it; "very rare" in Level 3; "many" in Level 9; first found in Level 2 | Built, looks by depth | Speech fragments (pleas), stage speed, weight shifts: rarer in 3, more in 9, a few in 2 |
| Facelings | Peaceful; juveniles impulsive | "easily angered by even small disturbances"; **children "the most aggressive and unstable"** but "traditional techniques to calm human children" work (the 6.1 log: snacks); Level 3's are all Evolved and hostile; Shadow Facelings drawn to light in the dark; 6.1 Facelings are staff | Ambient, greet, kin defence, curious children | Outbursts from disturbance (breaking things near them), children's tantrums calmable with food; Level 3's Facelings hostile with an Evolved look (texture only); Shadow Facelings deferred |
| Partygoers | Killable with stages, internal parasite | Current rewrite as the Fun brief has it | Built | Minor: senses move onto the shared model; no design change |
| The Beast | Invulnerable; event controller; deals | Wikidot: voice only, deals, "He only makes himself seen to those he wants to be seen by"; Fandom: physical, hostile when refused, holds Level 5's key | On branch `l5-beast`: an event with the deal, the gaze, the unveiled hunt (killable, drops the Level 5 key) | Refine, keep killable-when-unveiled (impractical, rewarded) |
| Neighborhood Watch | Watchers first (float, beam, immune), Striders and Swimmers later | Three kinds; **no hearing or smell**; Watchers float and disintegrate with a beam, no weapon has destroyed one; Striders six 8-ft legs, reach into buildings, can be fended off; Swimmers dog-sized in drains; Hounds, Smilers, Skin-Stealers and Deathmoths fear them; found "in dark corners… dead ends and lots of houses", not near Level 10 | On branch `l9-watch`: one six-legged eye three blocks tall, sight by light and through glass, taps at windows, killable | What is built is a **Strider** in all but name: keep it, call it so in the handbook, make its killability match the lore (ranged works; it can be fended off). The floating **Watcher** (evade-only, the beam) is **built in P4 (user's call)**, the one new model of the release; Swimmers deferred. Add the fear: other hostiles leave when one is near |
| Giant Spider | Territorial, webs, nests, killable, silk and venom | Level 8: colonies "aggressively territorial", "HIGHLY venomous", "Spiders can't swim", nests of thousands; the cookbook's "Deep fried Arachnid" | On branch `l8-spider`: nests as dens with webs, lurk, rear, chase, venom, water stops it, mends while waiting | Refine: noise draws the colony (several come), silk harvest (section 7), the cookbook's spider as food |
| Level 94 night | Not covered | "Smilers, Skin-Stealers, Hounds and male Deathmoths" besides the Animations | Animations only | Add the four at low weight at night (section 8) |
| Level 10 | No hostile roster spawns | "No Hostile Entities"; worms; **no livestock and no animals** in lore | Hounds at the edge, Clumps by the barns, livestock | Keep all three (the livestock is a deliberate adaptation; the edge Hounds come from Level 11's roster side; Clumps are in the rewrite's "Levels 2 and 10") |
| Level 9 fog | Mangled after prolonged fog exposure | "the fog being the spawning mechanism for The Mangled" | The event brings its own fog | No change: the fog comes first and the Mangled walks out of it, which is the lore read from the other end |
| The Hub | Entirely entity-free | "Numerous entities have been seen to successfully enter The Hub… but never re-emerged" | Safe | No change |
| Level 0 | Empty, Bacteria as a rare crossover | "unknown whether or not entities exist"; "dark figures stalking them" | Bacteria as the dark figures | No change |
| HP and damage table | Fixed numbers per entity | n/a | A per-level danger curve scales every entity | Keep the curve; retune the bases in P7 |
| Drops | Chitin, glands, silk, sinew, tissue per entity | Only quills (darts), Death Rats as food, spiders as food, Hound pelts (Fandom) are lore | Hides, bushmeat, bone, belongings, gears | **A few materials with real uses (user's call)**, section 7 |

### 3.3 What ChatGPT missed that the mod has

The danger curve (every level worse and better paid); dens and their caches; Flickering, the Screaming, the Mangled
event; the wanderers as safe company; exposure and noise feeding menace; the Level ! horde as puppets; Level 94's
Animations, Robo-Men and the King's nightmare; Level 3999.1's Threshold band; Level 188's Windows and Peripherals;
Reality Shifts as the hour the things that hate light come out. None of these change here, except as noted.

## 4. The perception model (P0)

One server-side model, in `src/Entities/Perception.cs` (new) beside `Senses.cs`, used by every menace task. The
Partygoers' `Notices`, the Watch's plainness-by-light and the Clump's noise threshold are the three existing
implementations; P0 generalises them so that the roster entities get the same thing from JSON.

### 4.1 Senses, per entity

A `SenseProfile` read from the entity's task config (all optional, with the defaults giving today's behaviour where
no profile is given, so untouched entities do not change):

| Field | Meaning | Hound example |
|---|---|---|
| `sightLit`, `sightDim`, `sightDark` | Range in blocks at which a target standing in light ≥ 8, in 4–7, in < 4 is seen | 40, 18, 8 |
| `sightCone` | Half-angle of the gaze in degrees, from the entity's yaw (the body; the Watch keeps its own eye) | 70 |
| `sightNeedsLine` | Whether a clear block line is needed (`Senses.ClearLine`); `glass` lets windows through | true |
| `carriedLight` | Multiplier on sight range when the target holds a lit item (torch 1.0, lantern 0.8, candle 0.4 as `Senses.MothDraw` grades them) | 1.5 |
| `hearing` | Range in blocks at which a noise of loudness 1.0 is heard; a noise of loudness `l` is heard within `hearing × l` | 32 |
| `hearsRunning` | Whether sprinting footsteps count as noise (loudness 0.4 per second of running within range) | true |
| `fearSense` | Range within which a target with stability below 0.4 is sensed whatever the light (the Beast "smells fear", Smilers come for the unsteady, Hounds for "an aggressive state") | 12 |
| `touch` | Range within which the target is known regardless (2 blocks: bumping into it) | 2 |
| `sneakFactor` | Multiplier on every range while the target sneaks | 0.5 |
| `memorySeconds` | How long a last-known position is believed after contact is lost | 8 |
| `special` | `wall` (the Duller: senses through one wall thickness within 2.6, no line needed), `noiseOnly` (Clumps), `glass` (the Watch), `water` (the Thing: hears swimming and dive depth, nothing above water) | |

Light at the target is the block light at the player's feet and eyes (max of the two) plus the carried light. The
engine has no hearing; noise is the mod's own bus (4.2). Sight is a cone test against the entity's yaw, a range by
light, and a block ray (the Partygoer's `Notices` as the template).

### 4.2 The noise bus

`MenaceSystem.MakeNoise` already adds to a player's menace value. P0 makes it an event too: `NoiseEvent {Pos,
Loudness, Source, Player?}` kept for 2 s in a list the director owns; each menace task's think asks
`Perception.Heard(entity, profile)` for the loudest event within its range. Sources and loudness:

| Source | Loudness | Where it is raised today |
|---|---|---|
| Sprinting (per second, at the player) | 0.4 | `Assess` adds 0.08/s to `Noise` |
| Jumping, landing from a fall | 0.3 | new, from `EntityPlayer` controls server side |
| Breaking a block | 0.5 (0.3 today) | `OnBrokeBlock` |
| Forcing a door with the pry bar | 1.0 | `PryBar` |
| A melee hit landing (on either side) | 0.6 | new, from the attack code and `OnEntityHurt` |
| A door opened or closed | 0.3 | new, from the door behaviour patch |
| Lighting Firesalt or a firepit | 0.4 | new |
| Throwing or dropping something | 0.2 | new (a stone thrown as a distraction: the lore's "throw bottles to distract Deathmoths") |
| Level Fun bang, The End's shelves | 0.5, 0.2–0.3 | `FunSystem`, `EndSystem` |
| A Hound's bark, a Smiler's victim screaming | 0.6 | new: entities make noise too, so a fight draws more |

Noise is heard by entities, and it still raises menace. A thrown stone (vanilla `stone-*` items are throwable) is
the player's first tool for drawing something off.

### 4.3 Belief, not truth

Every menace task keeps `Belief {LastKnownPos, LastSeenMs, Confidence 0–1}` instead of reading `target.Pos`:

- **Seen** (in the sight test this think): confidence 1, position exact.
- **Heard**: confidence 0.6, position the noise's position with ±3 blocks of error; a second noise narrows it.
- **Sensed** (fear, touch, wall): confidence 0.8, position exact.
- **Nothing**: confidence decays to 0 over `memorySeconds`; the position is kept. When it reaches 0 the entity has
  lost the target.

Stalk, Hunt and Search path to `LastKnownPos`, never to `target.Pos`. The attack still requires a clear line and
reach, as today. Every entity in a pack shares its belief with the pack (4.4).

A player who breaks line of sight, stops running and stands dark and still is lost in `memorySeconds`; one who keeps
sprinting is heard; one who carries a torch down a corridor is seen from the far end. These are the new counters, and
the handbook teaches them (P8).

### 4.4 Packs

Pack members (same `FrenzyKey`/pack id, within 20 blocks) share the best belief among them each think. A Hound that
sees you tells the pack by barking (a sound, and a noise event of its own that other Hounds hear); Level 3's packs
bark faster as they close (the lore's coordination), which is the player's warning. The `RallyPack` call stays as the
switch to Hunt.

### 4.5 Harness

`/backrooms perceive <entity> [x z]` (console-safe) puts a dummy and an entity down and prints, every second for 30 s,
what the entity sees, hears and believes, as the dummy is moved by the command's script (`/backrooms dummy move`,
`dummy light`, `dummy noise`, `dummy sneak`). The headless perception tests in `tools/aitest/` (new, Python like the
other harnesses) drive these and assert: a dark still dummy at 20 blocks is not seen by a Hound within 10 s; a lit one
is; a noise of 0.5 at 15 blocks is heard at `hearing` 32 but not at 8; a dummy that moves 10 blocks behind a wall is
lost after `memorySeconds`. The tests run on the headless server with `--withconfig` as `DEVELOPING.md` describes.

## 5. The encounter state machine v2 (P1)

`AiTaskMenace` keeps its structure (one task, one `Encounter` kind owned by `EntityBehaviorMenace`) and gains two
kinds and a budget. The `Encounter` enum's existing integer values are kept (section 10); the new ones are appended.

| Kind | What it does | Enters from | Leaves to |
|---|---|---|---|
| Ambient | Vanilla idle; Facelings, guests, moths at rest | the director | any, by perception |
| Glimpse | As today, but a glimpse that *sees* the player for more than its patience may turn to Stalk (lore: Hounds "hostile the moment they see a human") in the approach band or worse | the director | Leave, Stalk |
| Stalk | Keeps `stalkMin..stalkMax` from `LastKnownPos`; prefers dark and unseen points (today's `StalkPoint`); closes when confidence is high and the counters allow | the director, Glimpse, Investigate | Hunt, Investigate, Search, Leave |
| **Investigate** (new) | Heard something: walks to the noise, looks about (the `despair`/`lurk`/`alert` animation each model has), 6–10 s, then back to Stalk or Leave | Stalk, Ambient (for dwellers of dens) | Stalk, Hunt (if it sees), Leave |
| Hunt | As today, to `LastKnownPos`; needs confidence > 0.3 | Stalk, Investigate, retaliation, the director | Search, Stalk, Leave |
| **Search** (new) | Lost the target during a hunt: goes to the last known position, sweeps 8–12 s (two or three nearby points, looking), with the pack converging; the Watch's search is the template | Hunt | Hunt (sees again), Stalk, Leave |
| Leave | As today | any | despawn |

Rules that change:

- **An encounter has a budget.** `EncounterMs` counts from the first non-Ambient kind and is never reset by a kind
  change; `maxEncounterSeconds` (default 300, per entity) sends the entity to Leave. This closes "a stalker set off by
  running again and again never expires".
- **Spawn attempts are per place.** `Direct` rolls once per occupied place (players within 24 blocks of each other
  share a roll, the most endangered one's menace), so two players together are not hunted by twice as much.
- **Packs are clipped to the current band's cap**, not the Threshold cap.
- **Hunt requires belief.** A hunt that has lost its target goes to Search, not straight to Leave; `patienceMs` (no
  blood) still returns it to Stalk with calm. Give-up distance stays.
- **Retaliation is bounded.** A struck entity turns on its attacker (today), but a `retaliateSeconds` (60) limit returns
  it to its owner's encounter or to Leave, so a struck entity does not follow a second player across the level.
- **Hold-backs stay** (light, fire wards, Almond Water, doors, sanctuaries, wanderers), checked against the belief
  position where they are about the target and against the entity's own position where they are about it.
- **Doors stay** as pathing walls (Skin-Stealer excepted). Noise from a door closing is heard, so slamming one behind
  you tells them where you went; closing it quietly (sneaking) does not.
- **Stare-down generalises.** `staredDown` (Hound) and the Smiler freeze become one `gaze` block: `gazeHolds`
  (freeze while looked at), `gazeNerveSeconds` (the Hound's spent nerve), `gazeShocks` (the Beast's 5 s to shock), all
  using `Senses.LooksAt` from any player (multiplayer rule kept).

The task keeps its attack (wind-up, `damageAtMs`, dodge window), `Hold`, door work, the Duller grab, the Mangled lift
and the Bacteria's Lobby fright; they are reached from the new kinds as before.

## 6. Entity by entity

Each row: what is kept, what changes, which lore line it answers. Health and damage bases are retuned in P7 against
play; the numbers here are starting points for `gen_entities.py`.

### 6.1 Killable and harvestable (eight, plus three that are hard)

**Hound** (P1). Senses: 40/18/8, cone 70, hearing 32, hears running, fear 12, memory 8 s. Hostile on sight in the
approach band and worse; in the heartland a glimpse that sees you growls and watches. Growl (`growl`, the existing
animation) is played when it first sees you and before every charge: the warning. Barks on seeing (noise 0.6) and
the pack answers; Level 3 packs bark every 2 s while hunting and faster under 8 blocks. Stare-down kept with the
`gaze` block (nerve 4–8 s). Fire, light slows, doors, armour as today. Health 14→16, damage 3.5 (unchanged), speed
unchanged. Harvest: bushmeat 3±1, medium hide 1 (the pelt is lore), bone 1. Elder and starved looks kept. Levels
unchanged (0 edge glimpse, 1–5, 8, 9, 10 edge, 11 passive, 94 night, 3999.1).

**Faceling** (P3). Ambient as today; the greeting, kin defence and children stay. New: an **outburst** when a player
breaks blocks or fights within 6 blocks of one (Wikidot: "easily angered by even small disturbances"): it turns, waves
its arms (`stretch`/`facepalm` gestures) and shoves (1 damage, knockback) once, then calms unless struck. Children's
tantrums (`AiTaskCurious` already flees and tantrums): right-clicking a tantruming child with any food calms it (the
6.1 log), and it follows the player for a minute. **Level 3's Facelings are hostile and Evolved** (Wikidot: "every
single one… hostile"): a texture look with a half-formed face, `Passive` false, approach band, weak (health 12, damage
2, slow). Health unchanged otherwise. No harvest, no bounty; killing a docile Faceling provokes the rest and raises
menace by 0.3 for ten minutes (the only penalty, and enough). Shadow and Memory variants deferred.

**Deathmoth** (P3). `AiTaskMoth` stays the flight; senses are light-only (`sightLit` 24 for a flame, nothing dark)
plus hearing 10 for the alarm. Hive dens (`DenKind.Hive`) get a **heart**: two or three `backrooms:mothhive` blocks
(new; the nest's resin wall with larval columns, from the current rewrite) that break for quills and eggs (7.1) and
whose breaking raises the alarm so every female within 16 comes in waves of 3–5 every 20 s for a minute. Males are
ambient and scavenge (settle on bodies and spilled food, drink at Almond Water); females hunt the light carrier in the
approach band near a hive and at the edge. Smoke, lantern and candle rules kept. Health 3, damage 1.7 (unchanged).
Praetorian: a den guardian, nearly a metre tall, eight legs, paralytic venom (the spider's venom code), spits (no:
melee only); **optional**, needs a model, deferred unless P3 finishes early. Levels: 1, 5 (central hive: hive dens
more common), 9, 3 (males aggressive too: `Passive` false for Level 3 males), 2 (rare), 94 night males.

**Death Rat** (P2). Senses: 14/10/6, cone 120, hearing 24, memory 4 s. Behaviour: **scavenger first**. Ambient packs
in the heartland go to food on the floor (dropped food items, carcasses, spilled boxes) and eat it; they scatter from
a walking player at 6 blocks and from a carried torch; they nip only when cornered (the player within 2 blocks and
the rat with no exit), when a pack of four or more has a player below half health, or in the threshold band and dens.
Level 2's are bald and never bite (the lore: "virtually zero threat", corpses more common than rats: a few rat
carcasses as props is a P5 note). The Screaming kept. Health 6, damage 1.4. Harvest kept (bushmeat, small hide,
bone). Engineer rats of Level 3 deferred (traps and a model). Levels unchanged.

**Clump** (P3). `AiTaskClump` stays; hearing becomes the shared model (`noiseOnly`, hearing 14, running 0.4/s, so
two players running are heard twice as far: "retreat at the sound of multiple people running"). Health 27→18 (brittle
bones), grab damage 6.3→7, reach kept. After feeding (a grab that lands), it buries again within 10 s (dormant: lore).
**Remnant:** a killed Clump drops a `backrooms:clumpremnant` block where it died (new); after 20 in-game hours it
grows a juvenile Clump (0.6 scale, health 8) unless the block was burnt (right-click with a torch or firestarter, or a
fire within 2 blocks) or broken (which yields sinew, 7.1). Levels: 2, 3, 10 kept; 1 added (eyeless, fast, approach
band, rare 0.2).

**Wretch** (P2). Senses: 24/12/6, cone 90, hearing 20, fear 10 (they come for the starving: today's 3× weight, kept).
Speech fragments: the `gurgle` and a new synthesised plea (`entity/plea`: a word-shaped groan) while stalking. Stage
speed: early 0.9×, common 1.0×, far-gone 1.15× of today's run. Health 19, damage 4. Levels: 1, 3 (rarer, 0.2), 5, 8
packs, 9 (more, 0.6), 11 subway, 2 added (rare). Belongings and bounty kept. Weapons deferred.

**Giant Spider** (P4; refining branch `l8-spider`). Keep the branch's lurk, rear, chase, venom, water and return.
Refine: a noise of 0.5 or more within 24 blocks of a nest wakes every spider within it (the lore's "loud sounds…
attracting large numbers"), so a fight in a nest is a swarm; silk harvest (7.1); the cookbook's spider as food (its
drop `bushmeat-raw` 1, "singe off the hairs": cooked only). Keep the branch's numbers until P7.

**Partygoer** (P4). Move `Notices` and `Hear` onto the shared perception (same ranges: 12/7/4, cone 140, sneak 0.6,
hearing 6 for running and bangs) so that one code path exists. No design change.

**Skin-Stealer** (P2; killable, much harder). Senses: 30/14/8, cone 80, hearing 24, memory 12 s (patient). **Hunger
cycle:** a server-side `backrooms:fedUntilHours` on the entity; fed (within 24 in-game hours of a kill of any
creature or player) it is docile, wanders, and is Ambient even in the approach band; hungry it stalks and hunts. The
director puts down fed ones in the heartland (a wanderer-like figure standing at a camp) and hungry ones from the
approach band out. **Disguise:** a `skinstealer` texture look with clothes and a fresher skin for the fed state; the
tells are the lore's: it barely speaks (the mimic voices, kept), repeats a phrase, stands a little wrong (`skinadjust`
idle), and **bleeds clear** (a pale particle burst on a hit instead of the red one, through `EntityBehaviorMenace`).
**Harder:** health 40→60 base, damage 7.9 (unchanged), speed unchanged (slow and strong is the lore); a hit of 5 or
more damage **stuns** it (a 1.2 s `hurt` hold, 8 s cooldown) which is the opening; it opens doors (kept), fears fire
(kept). Harvest kept: large hide 1 and belongings; bounty kept. Levels 1, 3, 5, 9, 188, 94 night.

**Duller** (P2; killable, hard). Senses: `wall` special (senses a player within 2.6 blocks through one wall), sight
20/12/6 for fleeing, hearing 16. Behaviour kept (wall-listen, grab, theft, flee when faced, Almond Water). **Hard:**
when faced it flees at 1.3× sprint and despawns out of sight, so it cannot be caught in the open; it is in reach only
during and 1.5 s after a grab (the window), and health 23→30. Add Level 1 (approach band, behind the side rooms'
walls), remove Level 6. Bounty kept; drops stolen items (kept).

### 6.2 Evade-only (the game shows why)

**Smiler** (P1). Hybrid light rule: senses `sightLit` 48 (a carried light or a lit tile is seen from far), `sightDim`
16, `sightDark` 6, fear 16, hearing 24; it is drawn to the edge of the light and stops there (today's `lightBound`
hold-back), gathers (a stalker that sees a light comes to 1 block outside the lit area and waits, grinning), freezes
under a stare, and hunts a runner or a loud or unsteady player who is in the dark. Immortal and withdraws when struck
(kept); a hit shows the black-fire flare (`hurt`) and nothing else, so the player learns there is nothing to hit.
Level 6: glimpse only, never Stalk or Hunt (user's call). Everything else kept.

**The Thing** (P4). Add the lore counter: a lit torch or lantern held under water within 12 blocks of its rush breaks
the rush off (`Senses` already grades held light; a vanilla torch goes out in water, so this needs the lantern or the
oil lamp, and the handbook says so). Senses `water`: it hears swimming (any player below the surface within 40) and
nothing above. Otherwise kept.

**The Mangled** (P5, numbers only). Kept as an event. Its `despair` search already exists; it now searches the last
known position when the player gets indoors (the tendril needs a line) instead of standing at the house.

**Bacteria** (P1, with the Smiler). Senses 32/16/10, hearing 28, hears running (the Lobby fright is about running:
kept). Otherwise kept; killable (kept, 20 health, the user never asked to change it).

**The Neighborhood Watch** (P4; refining branch `l9-watch`). The branch's creature is a Strider: keep its sight model
(it becomes the shared one's `glass` special), its search, feint and window peering. Add: **fear** (Hounds, Smilers,
Skin-Stealers and Deathmoths within 24 blocks of one go to Leave), the lore's "never near Level 10" (not placed within
200 blocks of Level 10's wall), ranged weapons count double against it (the lore: "Ranged weapons work on them"). The
floating **Watcher** (`backrooms:watcher`, new) is **built in P4** (user's call), the one new model of the release:
a gigantic eyeball with trailing optic veins, `habitat: "Air"` as the Deathmoths are, levitating at walking speed over
the streets and above the houses, silent, sight-only (the shared profile with `glass`, 14/40 dark/lit, cone 90). Seen,
you get a 2 s charge (the pupil brightens, a rising tone: the warning and the dodge window), then a beam along a clear
line up to 12 blocks that kills outright whoever it fully covers; a Strider or another Watcher in the beam is unharmed.
Immune to everything, Firesalt and fire included (the page says so), so a hit shows nothing and the handbook says why.
It breaks off when it loses sight (the shared Search), never enters a house (too large for doors; it peers through
windows like the Strider), and keeps to the streets away from Level 10's wall. Its own model, texture and sounds
(`gen_models.py`, `gen_entity_sounds.py`: a charge tone, the beam, a low hum), its roster entry (Level 9, approach band
and worse, weight 0.4, `Outdoors`, never two within 48 blocks) and a bounty of nothing. Reviewed on an `entrender.py`
sheet like the other models.

**The Beast** (P4; refining branch `l5-beast`). Keep the event, the deal, the gaze and the unveiled hunt. Refine: the
unveiled hunt uses the shared perception (fear 24: he smells fear; sight 30/20/10), so hiding in a dark room works for
a while and the lore's "he discovers you" is the fear sense finding the unsteady. Killable when unveiled stays (120
health, the Level 5 key).

**Kitty, the Keymaster, the attendants, the arm, the horde, Robo-Men, the King's nightmare:** unchanged.

**Animations** (P5): onto the shared senses (sight 24/16/16, since they hunt what moves; `hearing` 0), with "standing
still is a doll" as a sight failure rather than a special case where the code allows.

## 7. Harvest and materials (P6)

The user's call: vanilla drops first, plus a few Backrooms materials that feed existing recipes, each with a recipe
on day one. Every new item is a new code (save-safe). Lore grounds: larval quills as darts (Wikidot Entity 4), spiders
and Death Rats as food (Wikidot), Hound pelts as leather (Fandom), Clump remnants (Wikidot, read as a resource).

| Item (code) | From | Use | Recipe |
|---|---|---|---|
| **Deathmoth quill** (`backrooms:mothquill`) | Breaking a hive heart block (2–4), harvesting a female (0–1) | **Venom coating.** A quill on a spear or an arrow stack makes an *envenomed* one: the next 3 hits add the spider branch's venom (1 damage every 2 s for 6 s). Implemented as an item attribute on the stack (`backrooms:venom = 3`), consumed per hit; the spear's name shows "(envenomed)" | grid: spear + quill → the same spear with the attribute; arrows ×8 + quill likewise |
| **Spider silk** (`backrooms:spidersilk`) | Harvesting a Giant Spider (2±1), breaking a web block in a nest (0–1) | Twine: 2 silk → 1 `game:flaxtwine` (bow strings, linen is still flax) | grid |
| **Clump sinew** (`backrooms:clumpsinew`) | Breaking a Clump remnant (1–2) | Binding: 1 sinew replaces the flax twine in the vanilla bow and sling recipes (a recipe copy with sinew), and 2 sinew + 1 small hide → 1 `game:leather`-equivalent? **No:** leather stays vanilla; sinew is only the bow and sling string, and a `game:rope` recipe (4 sinew → 1 rope) | grid |
| **Moth jelly** (`backrooms:mothjelly`; user's call: in) | Hive heart blocks in Level 5 (1 in 3) | Bait: thrown or placed, it draws every male Deathmoth and Death Rat within 24 blocks to it for a minute (a `NoiseEvent` of a special kind), which pulls a rat pack off you or clears a hall of moths | none (a found item) |

Kept as they are: Hound bushmeat and medium hide, Death Rat bushmeat, small hide and bone, Skin-Stealer large hide and
belongings, Wretch belongings, the Animations' clay, sticks, planks and parchment, Robo-Men's nails and brackets, the
Partygoers' hats and gears, every bounty. Added vanilla drops: Hound bone 1; Giant Spider `bushmeat-raw` 1 (eat it
cooked). Facelings, Smilers, the Thing, the Mangled, the Watch and the Beast drop nothing beyond what their branches
give (the Watch's bounty, the Beast's key). Handbook: a "What they leave" paragraph per killable entity and item
pages for the four materials. Chitin, glands and tissue are not added: nothing in the game would use them.

## 8. Levels (P5)

Roster edits, in `Roster.ByLevel` and `SoundsByLevel`. Everything not listed stays.

| Level | Change | Lore |
|---|---|---|
| 0 | None. Smilers in Reality Shifts and the Bacteria stay | "unknown whether entities exist"; dark figures |
| 1 | Add Duller (approach, 0.5, behind room walls); Clump (approach, 0.2, ambush, eyeless look optional); Death Rats scavenge the halls as ambient | Level 1's table: Dullers, Clumps "rushing… no eyes" |
| 2 | Death Rats never bite; Wretch (approach, 0.2); Smilers "almost the main entity" (weight 1.2 kept); Deathmoth female rare (edge, 0.2) | the blackout's aftermath |
| 3 | Facelings hostile Evolved (approach, 0.4, `Passive` false, own look); Wretch rarer (0.2); male Deathmoths aggressive (ambient→glimpse|stalk, 0.4); Hound packs bark to coordinate | Level 3's page |
| 4 | None (Hounds and Dullers only, Facelings ambient as Base Omega's people) | "mostly devoid… Hounds and Dullers" |
| 5 | Hive dens more common (1 in 15 cells); Death Rats added (heart, 0.3, boiler halls); normal entities a little scarcer (Hound 1.0→0.8) | "normal entities are fairly scarce"; "central hives"; Deathrats listed |
| 6 | **Remove Duller; Smiler becomes glimpse-only (0.2)** (user's call: eyes only) | "no entities have been found", and an archived note of an unidentified attacker |
| 6.1 | None | Facelings with the 11 Effect |
| 7 | None (the Thing; Tiny is a sound: a far splash) | one entity |
| 8 | Spider nests (branch); Smilers in the Handyland-like pockets kept | arachnids; Smilers in Handyland |
| 9 | The Strider (branch) and the new Watcher (P4), the Mangled (event) kept; Wretch 0.4→0.6; Death Rats scavenge bins; Hounds, Smilers, Skin-Stealers and Deathmoths leave when the Watch is near | "many Wretches"; the Watch; the fog; the fear |
| 10 | None | adaptation kept |
| 11 | None | Facelings and Hounds most numerous |
| 37 | None (Smilers in the Reservoir stay: it is the one zone the plan keeps "rumoured") | "devoid of life" |
| 94 | Night: add Smiler (approach, 0.3, dark), Skin-Stealer (approach, 0.3), Hound (approach, 0.4, 2–3), Deathmoth male (ambient, 0.4) | "Smilers, Skin-Stealers, Hounds and male Deathmoths" |
| !, Fun, End, Hub, 974, 3999, 188 | None beyond the shared perception for the Partygoers | as built |

Distant sounds: add a Hound bark-and-answer pair (two barks from two directions) to 1, 3, 9; a far splash to 7; moth
wings in 5's hive dens; the Watch's steps to 9 (branch). The danger curve (`Danger.OfLevel`) is unchanged until P7.

## 9. Engine capabilities and what the mod builds

What the 1.22.7 engine gives and what P0 and P1 have to write, verified against decompiled sources on 2026-10-18
(the full survey, with file and line references, is [engine-2026-10.md](engine-2026-10.md)).

**Two task systems exist.** The legacy tasks (`seekentity`, `meleeattack`, read through `taskConfig`) are what every
vanilla creature uses. The new "-R" tasks (`seekentity-r`, `meleeattack-r`, typed `*Config` classes) add light-scaled
detection (`TargetLightLevels`), sneak scaling (`SneakRangeReduction`) and herd filters, but no vanilla creature uses
them yet. **The mod keeps its own `AiTaskMenace`** (it already does far more than either) and borrows ideas, not base
classes: the R config shape for `SenseProfile`, and the trapezoid light multiplier.

| Need | Vanilla | The mod builds |
|---|---|---|
| Line of sight | `hasDirectContact` casts up to 3 rays against block collision boxes (glass blocks sight), used only by attack tasks; `seekentity` seeks through walls | Keep `Senses.ClearLine`; add the `glass` option for the Watch (a ray that ignores glass blocks) |
| View cone | None anywhere (only aim-angle limits) | The cone test (4.1) |
| Range by light at the target | R only: `TargetLightLevels` trapezoid on world light; a held torch is not counted | `sightLit/Dim/Dark` on `Senses.LightAt` plus carried light (`Senses.WithCarried`, which already exists) |
| Sneaking | Legacy: hard-coded 0.6; R: `SneakRangeReduction` | `sneakFactor`, read from `ServerControls.Sneak` |
| Last-known position, memory | None: seek re-reads `target.Pos` every tick | `Belief` (4.3) |
| Hearing | None. `PlaySoundAt` only sends packets to clients; `bellalarm` guesses from player controls (still 0.25, sneak 0.5) | The noise bus (4.2). Delivery can use `Entity.Notify(key, data)`, which reaches every task's `Notify`, or the task can poll the bus each think (simpler; chosen) |
| Smell, fear | Only `lowStabilityAttracted` / `RequiredTemporalStability` in `fleeentity`, and the `spawnCloserDuringLowStability` attribute | `fearSense` on the player's `temporalStability` |
| Player state tags | `entitystatetags` behaviour keeps `state-sprinting`, `state-sneaking`, `has-open-fire` and others on the player for JSON `entityTags` conditions | Not needed; the profile reads the controls directly |
| Emotion states | `emotionstates` with `slot`, `priority`, `duration`, `whenHealthRelBelow`, `accumType`, engine-triggered `aggressiveondamage`, `fleeondamage`, `alarmherdondamage`, `saturated`; tasks gate on `whenInEmotionState`. Quirk: `healthRel` starts at 0, so `whenHealthRelBelow` passes before the first hit | Not adopted for the state machine (the `Encounter` kind is the state); may be used for the Skin-Stealer's fed state if cheaper than an attribute (worker's call) |
| Pack coordination | `HerdId` plus two broadcasts: `alarmHerd` on seek (`Notify("seekEntity", target)`) and `alarmherdondamage`. Wolves use only the latter. No flanking | Shared `Belief` per pack (4.4); `RallyPack` kept |
| Pathfinding | `WaypointsTraverser`, `NavigateTo(_Async)`, `FleeFrom`; A* uses the collision box, `StepHeight`, `maxFallHeight`; per-block `Block.GetTraversalCost(pos, EnumAICreatureType)` (above 10000 is impassable) | `Investigate` and `Search` points use the existing `NavigateTo_Async` (never the synchronous one on the hot path: P1 moves Hunt's repath to async too); mod blocks may override `GetTraversalCost` to keep creatures out of places (a Sanctum, a lit room) |
| Doors | No AI opens doors; A* treats a closed door as solid; `BlockBehaviorDoor.Activate` exists as a hook | The Skin-Stealer's `WorkDoor` already exists; nothing new |
| Through walls, flight | `NoClip` is honoured only by player physics; `controlledphysics` always collides; flight is `habitat: "Air"` with no gravity | Nothing new (the Duller's reach is an animation; a floating Watcher would be `habitat: "Air"` as the Deathmoths are) |
| Melee | `meleeattack(-R)`: `damage`, `damageTier`, `knockbackStrength`, `damagePlayerAtMs`, `attackDurationMs`, `minDist`, line of sight at hit time; `attackTarget` is virtual | `AiTaskMenace`'s own attack stays |
| Ranged | `throwatentity`, `shootatentity-r`, `turretmode(-r)`, `EntityProjectile*` | The Watcher's beam, if built, is a timed ray, not a projectile |
| Venom, bleeding | `DamageSource.Duration`, `TicksPerDuration`, `DamageOverTimeType` → `EntityBehaviorHealth.ApplyDoTEffect` (`Poison`, `Bleeding`; bandages stop bleeding). No melee config sets them | The spider branch's venom and P6's envenomed weapons call `ApplyDoTEffect` with `Poison`, so vanilla's own display and cure rules apply |
| Slows, stuns | `Entity.Stats.Set("walkspeed", …)`; a task `Hold` | The Skin-Stealer stun is a `Hold` |
| Harvest drops | `harvestable` with `drops`, `duration` (client and server must match), `fixedweight`, quantity scaled by `animalWeight`, `deathByMultiplier` (0.4 when a non-player kills), `animalLootDropRate`; `Tool` filter per drop; **`IHarvestableDrops.GetHarvestableDrops`** on any behaviour adds stacks by code | Look-dependent drops (elder Hound, fed Skin-Stealer) through `IHarvestableDrops` on `EntityBehaviorMenace`; `sync_harvestable` in `gen_entities.py` keeps both sides equal |
| Spawn conditions | `RuntimeSpawnConditions` (`MinLightLevel`, `HerdSize`, `MaxQuantity`, `MinDistanceToPlayer`) | Not used: the director places everything |
| Is the player looking at me | Each position packet carries `Yaw`, `Pitch`, `HeadYaw`, `BodyYaw`; the server writes them to `player.Pos`, so `Pos.GetViewVector()` is the look direction (first-person accurate; free-look unverified) | `Senses.LooksAt` as today |
| Sensing helpers | `EntityPartitioning.GetNearestEntity/WalkEntities`, `GetLightLevel(pos, type)`, `ServerControls`, `EntityPlayer.LightHsv` (throws with a null `Player`: keep `Senses.RightHand`), `WorldManager.GetNextUniqueId()` for herd ids | As today |

**Gotchas carried from the survey:** `ServerPos` is an obsolete alias of `Pos`; `GetLightLevel` never includes held
light; `harvestable.duration` must match on both sides; `NavigateTo_Async` only enqueues (`Active` is false until a
later tick); `HandleNoPath` does not stop the traverser (the mod's `OnNoPath` handles it); emotion-state eviction
removes the wrong attribute (do not rely on it).

## 10. Save compatibility

Kept exactly: every entity code (section 8 of the code map), the behaviour names `backrooms-menace`,
`backrooms-faceling`, `backrooms-partygoer`, `backrooms-junkie`, the entity classes, the `Encounter` integer values
(Ambient 0, Glimpse 1, Stalk 2, Hunt 3, Leave 4; Investigate 5 and Search 6 are appended), the attribute keys
`backrooms:kind`, `:owner`, `:passive`, `:born`, `:session`, `:untilHours`, `:duringShift`, `:kindSinceMs`,
`:rallied`, `:stolen`, `:struckMs`, `:danger`, `:frenzy`, `:alarmed`, `:provoked`, `:horde`, `:funRoom`, `:funHome*`,
`:nightmareOf`, `textureIndex`, the player attributes (`backrooms:restedAt`, `:almondDrankHours`, `:flickerUntil`,
`:mangledFog`, `:killedBy`, the Run and Fun keys), the world data `backrooms-wanderers` and `backrooms-fun`, and the
world config `backroomsMenace` with its four values.

Added with defaults: `backrooms:encounterSinceMs`, `:firstOwner` (bounded retaliation), `:fedUntilHours` (Skin-Stealer), the behaviour attributes `maxEncounterSeconds` (0 = off), `investigateCapSeconds`, `searchCapSeconds`, the world data `backrooms-dens` (dens whose hive hearts were placed), `:venom` on item
stacks, the new item codes (7), the new entity code `backrooms:watcher`, the new block codes `backrooms:mothhive`,
`backrooms:clumpremnant`, `backrooms:spiderweb` (if the spider branch does not already add one).

Menace entities are despawned on load by the session check, so no saved entity ever runs the new state machine from
an old attribute set. The Clump remnant and the hive heart are blocks placed **at runtime** (user's call): the remnant
where a Clump dies, the hive heart the first time a player enters a hive den (recorded per den in the world's
`backrooms-dens` save data, new), like Level 188's arm. No layout version. Web blocks the spider branch already places
by worldgen behind layout version 9 stay as they are.

## 11. Phases and batches

Each batch is one Opus session on a branch `ai/<batch>` off `main` in the main working tree (the build and asset locks
in `tools/locked.sh` assume one tree), following the loop in section 12. The three entity branches (`l5-beast`,
`l8-spider`, `l9-watch`) must be merged to `main` before P4; P0–P3 do not depend on them but P0 must not break them
(the Partygoer, Watch and Spider senses are left alone until P4 moves them onto the shared model).

| Batch | Covers | Main files | Depends on |
|---|---|---|---|
| **P0** Senses, noise, harness | `Perception.cs` and `SenseProfile`; the noise bus and its sources; `Belief`; `/backrooms perceive`, `dummy *`; `tools/aitest/` with the four assertions of 4.5; no behaviour change for any entity (profiles not yet given) | `Senses.cs`, `MenaceSystem.cs` (noise), new `Perception.cs`, `Cheats`, `tools/aitest/` | nothing |
| **P1** State machine v2; Hound and Smiler | Investigate and Search; the encounter budget; per-place spawn rolls; pack cap by band; bounded retaliation; the `gaze` block; profiles for Hound, Smiler and Bacteria; the Smiler's hybrid light; Hound growl-before-charge and bark coordination; Level 0–3 tuned until a dark corridor feels right | `AiTaskMenace.cs`, `EntityBehaviorMenace.cs`, `MenaceSystem.cs`, `Roster.cs`, `gen_entities.py` (hound, smiler, bacteria), `gen_entity_sounds.py` (bark pair) | P0 |
| **P2** Skin-Stealer, Duller, Death Rat, Wretch | Hunger cycle, disguise look, clear blood, stun; Duller wall sense, flee speed, Level 1; rat scavenging and skittishness, Level 2 harmless; Wretch pleas, stage speeds, weights | `AiTaskMenace.cs` (stun, scavenge), `gen_entities.py`, `gen_models.py` (the fed Skin-Stealer look only: a texture), `Roster.cs` | P1 |
| **P3** Deathmoths, Clumps, Facelings | Hive hearts (block placed at runtime on first entry to a hive den, drops, alarm waves), male scavenging, Level 3 males; Clump remnant block and juvenile, dormancy after feeding, health; Faceling outbursts, child calming, Level 3 Evolved look | `AiTaskMoth.cs`, `AiTaskLurkers.cs`, `Facelings.cs`, `AiTaskCurious`, new blocks in `gen_blocktypes.py`, `gen_entities.py`, `gen_models.py` (textures only), `MenaceSystem.cs` (den entry hook); no layout change | P1 |
| **P4** The Watch, the Spider, the Beast, the Thing, Partygoers | Move the branches' senses onto the shared model (behaviour identical; the harness proves it); the Strider's fear aura, lore killability and Level 10 distance; **the floating Watcher** (model, sounds, beam, roster entry; the one new model); the spider colony's noise response; the Beast's fear sense; the Thing's light counter | `NeighborhoodWatch.cs`, `AiTaskSpider.cs`, `AiTaskBeast.cs`/`BeastSystem.cs`, `AiTaskLurkers.cs`, `AiTaskPartygoer.cs`, `gen_models.py` (the Watcher only), `gen_entities.py`, `gen_entity_sounds.py` | P1 and the three branches merged; the largest batch, and may be split into P4a (senses, Spider, Beast, Thing) and P4b (the Watcher) |
| **P5** Levels | Section 8's roster and sound edits; Level 6 emptied; Level 94's night; the Animations' profile; the Mangled's search | `Roster.cs`, `gen_entity_sounds.py`, `MangledEvent.cs` | P1 (P2–P4 for their entities' weights, but the edits can land first) |
| **P6** Harvest and materials | The four items, their icons (the icon kit from the graphics pass), recipes, the venom attribute and its hit hook, harvest tables, handbook item pages | `gen_entities.py` (drops), new `gen_materials.py` or a section of an existing item generator, `src/Entities/Venom.cs` (new; reuse the spider's DoT), `assets/backrooms/recipes/` | P3 (hive heart, remnant), P4 (spider) |
| **P7** Play-test tuning | The user plays; the worker turns the user's notes into number changes (`gen_entities.py` bases, `Danger` multipliers, profiles, weights); two-player check with `/backrooms dummies`; the `entity-difficulty.md` tables rewritten | numbers only | P1–P6 |
| **P8** Finish | Handbook "What Lives Here" rewritten for senses, hiding, noise, the new drops and the corrected entity numbers; `docs/GUIDE.md` and README; `CHANGELOG.md` 0.515.0; the Spanish handbook note for NeoB; the creature lineup if a look changed; the release zip | `gen_guide.py`, docs, `modinfo.json` | P7 |

P2 and P3 are independent once P1 is merged and may run in parallel on two branches if the user wants, with builds
serialised through `locked.sh`. P5 can start once P1 is merged. One at a time is the safe default.

## 12. The batch loop

1. **Read** this document, the batch's rows, the tracker's *lessons*, `docs/design/entity-plan.md` (status section),
   `entity-difficulty.md`, `entity-models-todo.md`, the code map in `docs/DEVELOPING.md`, and the engine survey
   (section 9). Read the code the batch touches before changing it.
2. **Headless first.** Build into a scratch Mods dir with `bash tools/locked.sh mod ai`; run `tools/aitest/` and
   `/backrooms perceive` and `/backrooms encounter … x z` against straw dummies (`/backrooms dummies on` for the
   director) for every behaviour the batch claims. Movement cannot be tested headless (the server moves entities only
   near a player), so the batch states which checks are headless and which need the client.
3. **Client check-list.** Each entity batch writes a numbered list of what to see in the client (as
   `entity-models-todo.md` section 2 does), using the cheat menu (`/backrooms encounter`, `/backrooms light`,
   `/backrooms noise`, `/backrooms stat stability`), and runs it itself where a client is free (the shotbot can
   teleport and aim but cannot judge AI; the worker plays). What it could not check is listed for the user.
4. **Blind review.** A reviewer (prompt in [prompts.md](prompts.md)) reads the diff against sections 4–8 and the
   lore brief, not the worker's report, and returns: behaviour that contradicts the plan or the lore, save-compat
   violations, omniscience that crept back (`target.Pos` read where `Belief` should be), and any `/backrooms` command
   or world setting added without a cheat-menu button. The worker fixes and re-runs the harness. At most three rounds.
5. **Report.** Append to the tracker: what changed per entity, the harness results, the client check-list with what
   was seen, numbers changed, *lessons* (engine gotchas, a profile field that needed adding), what was carried.
6. **Gate.** The Fable overseer reads the report, the harness output and the diff, checks scope (no model changes, no
   layout version, no code renames), and merges to `main` or sends it back with specific items.

## 13. Orchestration

The user's direction (2026-10-18): distribute the work to agents, on the least expensive model that can do it. One
overseer session plans, briefs, integrates and gates; within a batch it splits the work into pieces with disjoint
files and runs them as parallel agents in the batch's worktree (builds serialise through `tools/locked.sh`).

| Work | Model |
|---|---|
| Mechanical edits that follow a pattern: cheat-menu buttons, docs, lang text, generator number changes | haiku |
| Most implementation, the headless harness and its runs, blind reviews | sonnet |
| The hardest design-heavy code (state machine v2 if a sonnet attempt falls short, cross-file refactors) | opus |

Every Agent call names its `model`. The overseer reads each piece's report and the diff, and holds the merge. One
blind review round plus one fix round per batch. Branch work happens in a worktree beside the main tree
(`../VS Backrooms-ai`), never by switching the main tree's branch.

Other sessions share the tree (memory: `peer-sessions-git`): a batch stages only its own paths, never switches
branches in the main tree while another session is in it, and messages the owning session before touching
`MenaceSystem.cs` or `Roster.cs` if the tracker shows another batch active.

## 14. Testing

- **Headless:** `tools/aitest/` (P0) on the headless server: perception assertions (4.5), encounter budget (a dummy
  that runs every 10 s for 6 minutes is left alone after `maxEncounterSeconds`), per-place spawn rolls (two dummies 10
  blocks apart get one roll's worth), pack cap by band, `harvesttest` for every killable entity (the 0.513.0 empty
  harvest bug), `blocksweep` after new blocks.
- **Client:** per batch check-lists (12.3). The one play-through the plan asks of the user is P7.
- **Performance:** the perception test is a cone check, a light read and at most one block ray per entity per think
  (0.3 s); the noise bus is a short list. The budget: no more than today's cost plus one ray per entity per think.
  `/backrooms menace` gains a line with the director's and the tasks' time per tick.
- **Save:** load a 0.514.0 world at every gate; nothing in it may fail to load, and its entities (none are saved but
  the wanderers) and items must be intact.

## 15. Decisions

Taken (details and reasons in [decisions.md](decisions.md)): Skin-Stealer and Duller stay killable but harder; the
Smiler's light rule is the hybrid; drops are vanilla plus a few materials with real uses, moth jelly included; the
Strider, Spider and Beast are refined here, not built; **the floating Watcher is built in P4**; Level 6 keeps eyes only
(rare Smiler glimpses, no Dullers); hive hearts and remnants are placed at runtime, with no layout version.

Open, with a recommendation in bold:

1. **Version:** **0.515.0**, as the graphics pass shipped as its own release. The user decides at P8.
