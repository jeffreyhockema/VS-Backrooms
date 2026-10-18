# Level ! "Run For Your Life!": research, design and integration plan

**Level !** is one long hospital hallway, lit only by red EXIT signs, with an alarm blaring. A horde of entities bursts
out of a chained door behind you, and the only way out is the door at the far end. Kept as level **14**
(`WorldLayout.RunLevel`), shown as **"!"**, tag `run`.

The user asked for a hallway far shorter than the lore's: **one to two minutes of sprinting**. This plan sets it at
**about 520 blocks of running, roughly a minute and a half at a sprint** (section 3.2 has the arithmetic).

## Fairness pass (2026-10-18, 0.514.0), from the user's play-test

"Too difficult to make it to the other side", "is there a way to tell false exit from real?", a rest area where "the
entities just kept coming and killed me", and floor clutter that slowed you while looking like "a pile of papers".

- **The chase, every world:** the front's share of a sprint is 0.78 / 0.82 (was 0.90 / 0.94; Low 0.73 / 0.77, High
  0.84 / 0.88), 0.12 lower at the burst and back to it over 20 s (three of the horde shown meanwhile). Since the
  version 6 gauntlet nobody keeps a flat-floor sprint; `mapgen runfair` puts a runner who keeps 0.82-0.90 of one,
  snags on a barricade about once per 100 blocks and trips 4-9 times at 80 % escapes in the old 615-block hall and 88 %
  in the new one (0 % before); walkers and stoppers are still caught. Dented-door chasers run at 0.65 (were 0.8, faster
  than a weaving runner), a vent's Hound at 0.95 for 4 s from 4 behind (1.0 for 6 s from 3). A trip is -0.5 for 0.6 s
  at most every 3 s (-0.6, 0.8 s, 2 s), and the first one says why.
- **Shorter, layout version 9:** 15 rows of hall (`RunRows9`), about 485 blocks; trip junk a little rarer in the gaps.
- **The Safe Zone** is lore (Fandom 2022's Checkpoint, via the BGPD copy: "a room where the entities cannot enter, and
  you will be able to rest"; the 2025 rewrite's Safe Zone, about 6 % of reports), so it stays and is made safe: its
  second side room lay further along the course than the zone's far end, so resting by its cot counted as having left
  and the horde ran you down. Anywhere with `Zone == Safe` now holds the runner inside the zone's span, and chasers
  that followed you are dropped at its door.
- **The exits:** the lore's tell (a false exit has a bend beside it, the real one is a dead end with no turn either
  side; its sign "a little darker") is kept and made visible: the true exit's lower block shows daylight under the
  leaf and gives off pale light `[8, 2, 14]`, so the dead end is lit white; the false exits' dim sign has its X burnt
  out. In the handbook, the notes and the level hint.
- **Trip junk** keeps its codes and footprints with new shapes: a tipped toy crate with the toys strewn round it,
  dumped boxes, extension cord in loops with a power strip, a heap of fallen ceiling, up to half a block high.

## Status (2026-10-09): implemented (code phase 2), with the recommended answers to section 9

Checked with the layout harness and a headless server (chunks generated, dumped and rendered). **Not yet played in a
client:** the chase, the alarm, the beacons and the puppeted horde have only been exercised by the pure model
(`runsim`).

**Built:**
- `WorldLayout.LevelRun.cs`: the region (17 lanes × 21 rows), the lane planner, `RunChase` (the pure chase model),
  and the entrances in Levels 1 and 2.
- `WorldGenerator.Run.cs`: the columns, plus a hook in the shared `ColumnBlock` that draws Level !'s entrances in
  other levels.
- Thresholds: `ThresholdNetwork.Run.cs`, `ThresholdSystem.Run.cs`.
- `src/Regions/RunSystem.cs`:
  - the run's timeline: the bangs, the bulge, the burst, the stuck hall door;
  - the rubber-band front and the puppeted horde;
  - being caught means death;
  - every hazard: swinging doors, toppling shelves, dented doors, vent drops, the sign burst with its wall of fire,
    trip props;
  - the Safe Zone with its 3-hour limit;
  - escape once, separate lanes per runner;
  - the arrival door left at each exit;
  - the Energy Bar's second wind;
  - lanes put back ahead of each runner.
- `AtmosphereSystem.Run.cs`: red fog with a 1 Hz pulse during the alarm, blue for the Safe Zone; the alarm, horde,
  heartbeat and Safe Zone loops.
- Danger 0.9; Level 37's red corridor; the `runstats`, `runmap`, `runsim`, `runlinks` and `runhash` harness modes.

**Checked:**
- `runstats`: all 17 lanes pass.
  - Course 613-616 blocks.
  - A way through in every lane; no row more than 3 of 5 blocked.
  - Dark stretches ≤ 32 (≤ 40 in the last third).
  - 2 false exits each; 3 Safe Zones, 4 holes.
  - Exits: 9 to Level 1, 5 to Level 4, 3 to The End.
  - 60/60 arrivals, all on a start room's arrival tile; 0.18 ms per cell.
- `runlinks`: every exit is one-way and leads to its lane's destination every time; holes lead to Level 8. The ways in
  found (Level 1 ×2, Level 2 ×6, Level 37 ×6) all land on a start room, one-way.
- `runsim` (Normal):
  - a clean sprint escapes in 96 s, 36 blocks ahead at the closest;
  - 5 mistakes of 2.5 s escape with 1.8 blocks to spare; 8 are caught;
  - walking is caught in 18 s.
- `regions`: 60/60, none on the wrong level. The 32 "pockets under 3000 tiles" are the lanes themselves, sealed by
  design.
- `runhash` (layouthash without and then with Level !'s entrances): **only Level 37 (small world) moves**, by the red
  corridors. Levels 1 and 2 have no entrance in the sample cells, and every other level is unchanged.
- Headless server (port 42474): all `run-*` blocks resolve. Dumps of lane 8's start room, first dogleg and exit render
  as designed.

**Deviations:**
- **Longer: about 615 blocks (90 s clean sprint), not 520.** The decompiled physics gives a sprint of 6.79
  blocks a second, not the brief's 5.5-6 (`RunChase.SprintSpeed`). Section 3.2's rule (`RunRows = round(92 s × S /
  32)`) makes 19 hallway rows, so the region is 21 rows long instead of 17.
- The horde's speed follows the runner's own sprint: slowed by armour, not raised by an Energy Bar.
- **The Safe Zone has two rooms**, both on the inner side of the straight, not four.
- **Buried Clumps are not placed.**
- Side doors are flush in the walls; trays stand against the wall beside a door, not in recesses.
- The caught death message is the vanilla one, naming the horde entity.
- Lane reset: rows 40-80 blocks ahead of each runner (and the start room on arrival) are put back from the generator
  as they run, instead of a reset 30 s after the run.
- Level 2's false wall is noticed by `RunSystem` (a player standing in the block), because walked thresholds are not
  looked for in Level 2.
- The start room's red light also comes from a lit EXIT sign over its hall door.

**Small edits in shared files** (beyond the scaffolding's hooks):
- `ThresholdSystem.Use` hands Level !'s nowhere-doors to `RunUse`.
- `BackroomsModSystem` gains a public `Generator`.
- `Breakdown.KindOf` special-cases `run-*`: props keep their drops, everything else is fixed.
- `Rewards.Bounty` skips horde entities.
- `WorldLayout.Level1.cs` and `WorldLayout.Level2.cs` each call one entrance marker.
- `WorldLayout.Level37.cs`'s `CarveDryCorridor` draws the red corridor on the Hub's shared roll.
- `PropTable` rows; the `ColumnBlock` hook; the fog line; `Danger.OfLevel`; lang keys `level-1401`, `levelhint-1401`
  and `run-fell`.

---

## 1. What the lore says

### 1.1 Where the canon lives

Level ! is **not on the main English Wikidot.**
- `backrooms-wiki.wikidot.com/level-run-for-your-life` returns 404.
- No page with "!" or "Run" appears in its tag index.

It is a **Fandom original**, first written by Aunwyk (credited as "Aomwgud" in one rewrite) in March 2021. It was
rewritten on Fandom twice: in 2022, and again on 2025-06-01 by Everybox, a rewrite carried over from the Chinese
wiki. Several fan Wikidot sites copy one of its versions (Exploration, MGHC, BGPD, Noclip, Archive Unit), and BGPD
says outright that its copy was "recovered … via Wayback Machine" from Fandom. The Chinese Wikidot is reported to
have replaced its copy with a secret level, "尘封已久的感叹" ("Long-Sealed Exclamation"); this is unverified.

So for this level, **Fandom is the primary canon**. Its three versions are weighed together, Miraheze is the second
opinion, and *Escape the Backrooms* is the best-known depiction.

| Source | URL | What it is |
|---|---|---|
| Fandom, original (2021) | https://web.archive.org/web/20210323165251/https://backrooms.fandom.com/wiki/Level_! | Short. Class 5. The discovery log |
| Fandom, 2nd rewrite (2022) | https://web.archive.org/web/20221206232031/https://backrooms.fandom.com/wiki/Level_! | The start room, transformation, traps, fake exits, events |
| Fandom, current (2025 rewrite) | https://backrooms.fandom.com/wiki/Level_! (read via `api.php?action=parse&page=Level_!`) | Survival guides, safe zone, explosions, collapse, theories |
| Miraheze | https://backrooms.miraheze.org/wiki/Level_! and `/wiki/Level_!-!` | Class 5. Crimson doors; never from Level 0 |
| Wikidot forks | http://backrooms-exploration.wikidot.com/level-run, https://backrooms-mghc.wikidot.com/level-run, http://bgpd.wikidot.com/level-run-for-your-life | Copies of the 2021–22 Fandom text |
| Wikidot Pantheon tale | https://backrooms-pantheon.wikidot.com/long-forgotten-exclamation | The hallway long after: dark, silent, bones, claw marks, sinkholes |
| *Escape the Backrooms* wiki | https://escapethebackrooms.fandom.com/wiki/Level_! | The game level: Level 37 → Level ! → The End |

### 1.2 The canon, all versions together

**Classification.** Survival Difficulty 5 in 2021: "Unsafe, Unsecure, Entity infestation". By 2022 it is "Class !"
("Exceedingly Unsafe, Unsecure, Extreme Entity Count"), and in 2025 an alternative class (ext 4, env 5, ent 5). It is
"the most dangerous anomalous level", and nobody should enter it on purpose. Colonies and outposts are impossible.

**The hallway.**
- One long, narrow hallway "similar in design and architecture to that of a modern medical hospital".
- About 10 km long. The 2022 text adds "although this is disputed".
- Surfaces:
  - 2021: no detail.
  - 2022: floors of porcelain tile, apparently wooden walls and white ceiling tiles, which turn to concrete once the
    chase starts.
  - Search snippets of the 2025 text: "white walls, floors and ceilings".
- **Lighting:**
  - 2021: "out of power, with constant alarm noise and **red flashing lights**", and "every 10 meters are red exit
    signs being very bright".
  - 2022 and 2025: the EXIT signs are the *only* light source, a deep red, in "almost random positions, resulting in
    some areas being overly bright while some are plunged into complete darkness". Flashlights are useful.
  - Wikidot forks and Miraheze: "bright, flickering exit signs … each about ten meters from another".
  - 2022: in the later stretches the signs thin out and it gets darker.
- **Doors** line both sides, "every 3 meters" (2021). They are of unknown metal, indestructible and mostly locked.
  - 2022: behind them, talking and passing shadows before the chase starts.
  - 2025: opening one is a trap; behind it is a room you can't leave, or entities.
- **The alarm.** "An alarm of unknown origin is continuously playing … harmful to the mental state". Panic leads to
  being caught. Some say it is only in the runner's head (2025). In 2022 it starts faint and becomes "almost
  deafening".
- **Bends.** Rare, "likely to occur at least once" (2022), "every few kilometers" (2025).

**The start room** (2022, 2025):
- About 25 by 25 feet. Two versions:
  - 2022: reflective metal, dull red light.
  - 2025: a hospital room in red light, with a bed, neatly folded sheets, a bedside table, a privacy curtain and a
    medicine cabinet.
- Supplies (Almond Water, energy bars) lie in the bedside table and the cabinet. The 2025 survival guide: spend "a
  mere 5 seconds" gathering them, and don't carry too much.
- Doors:
  - Two doors face each other. One is **chained shut**, with "countless entities trying to break through".
  - The other is the way to the hallway, and it "rarely work[s] on the first try, or even the tenth".
  - The door you came in by slams shut, and shows "a huge red exclamation mark" on its inside.
- The chained door "will begin to decrease around five seconds after the person's arrival", with dents and bulging.
  It breaks "often just seconds after they leave the first room"; sometimes about 10 seconds after arrival.

**The chase.**
- The horde (lore name for the pursuers):
  - 2021: Hounds, Skin-Stealers, Facelings.
  - 2022 adds Smilers, Partygoers and Lighters.
  - 2025 adds Deathmoths overhead and Aranea Membri.
  - The forks add Clumps lying across the way.
- "Strangely, the speeds of these entities are nearly the same in this level" (2025).
- "The entities will adapt to one's capacity of running, to a point of giving difficulty even to the ones experienced
  at running" (2022, the forks, Miraheze).
- Further on they "decrease in number or fall behind … This may convince one that they have escaped, but this is an
  illusion" (2022). The 2025 guide: "They are still near, don't stop!"
- "If the horde of entities catch you, then they'll kill you in the most painful and brutal way possible" (2021).

**Obstacles and traps.**
- Chairs, hospital beds, gurneys, medical equipment and Clumps (2021, forks).
- Small things are "even more lethal": toy cars and boxes, hard to see, that trip you (2025).
- Obstacles "may slide around randomly" (2025).
- An electrical cord stretched across the hall, and gaping holes in the floor, mostly in the dark later stretch (2022).

**Supplies.**
- Energy bars (2021) and Almond Water on beds, chairs and tables, often out of view (2022).
- Miraheze adds Red Bull.
- A secondary fan site has "a vending machine every 4.5 kilometers".

**Events** (2022 and 2025):

| Event | Source | What happens |
|---|---|---|
| Doors burst | 19 reports | Rusted or dented side doors with noise behind them; an entity breaks out and joins the horde. Those that burst out are "much slower" than the horde |
| Vents | 2025 | Smaller entities (Hounds, Smilers) drop from ceiling vents |
| Explosion | 2025 | An EXIT sign flickers erratically, hisses, grows too bright, then explodes. The fire catches the strewn sheets and makes a wall of flame you must run through |
| Gray Halls | 2022 | The red fades to grey, the floor shakes, parts of the level combust |
| Collapse | 2025 | Cracks warn first. The floor gives way ("we never know where they end up"); walls and ceilings fall; live wires hang down |
| Fake exits | 2022, 2025 | An exit door with a bend beside it is false: "an empty room", and you are caught. The real exit is a dead end with no turn either side. The false EXIT sign is "a little darker" |
| Safe Zone | 2025, ~6 % of reports | A **blue**, well-lit stretch entities won't enter. Side rooms with a shelf and a bed, Almond Water and energy bars. Sign: "WELCOME to the safe zone. Please take a break before you continue running." Leave by its far door and the horde comes in through its entrance and carries on |
| Checkpoint | 2022, 9 reports | "Safety is near": a room where you can rest, but after about three hours its walls close in |
| Level ! EX | 2022 | The run loops |
| Nowhere To Go | 2022 | The whole level explodes |

**Multiplayer.**
- "When multiple people enter the level at the same time, they will be forced to separate" (2025).
- "The level will create a copy for each person that is in" (2022).
- The 2025 lecture: during a collapse, a wanderer saw through the wall "only another hallway, and another human
  running just like him".

**Ways in.**

| Source | Entrances |
|---|---|
| 2021 | "Through any level of the backrooms, when you least expect it". The discovery log is set in **Level 2**: a wall appears where none was, and Noah noclips |
| 2022 | Objects marked "!". Faulty elevators in unstable levels. A table in Level 521. A thought in Level 354. Out-of-bounds in 357. Noclipping in 2020. The fire alarms of Level 54 |
| 2025 | An **EXIT door incompatible with its surroundings**, appearing anywhere and moving. An **elevator with "!"** on it. **Noclipping through the floor in Level 2**. Phenomenon 354 |
| Miraheze | **Crimson doors** out of context with a faint static, in every stable level **except Level 0**, rarer the deeper you go. Red "EMERGENCY" doors in Level 16. Level !-! is entered from **Level 2** (50 %) |
| *Escape the Backrooms* | "Find the red short hallway in **Level 37**" |

**Ways out.**

| Source | Exits |
|---|---|
| 2021 | Run 10 km; the door returns you to the level you were last in, "with the backrooms never sending you back here ever again" |
| 2022 | A random level. Tripping noclips you to Level 52. A vent to the Maze of Vents. Side doors to 3635 / Level !-! / 419. A fake exit to Level Maker |
| 2025 | "Mostly … safer levels … the most reached levels being **Level 1 and Level 4**". The arrival is "like a warehouse … a resting area you've dreamed of". Close and mark the exit door, because "the exit door has been converted into an entrance door". "Once a wanderer leaves Level !, he will not re-enter. If he attempts to enter an entrance door … he will only reach another location in the level he was in" |
| Miraheze | A random safe level, often back where you came from; rarely Level -! or 0. Running back toward the horde → Level N/A. Noclip through the floor → Level 52 |
| *Escape the Backrooms* | The exit door → you fall into **The End** |

**History** (flavour only).
- Photo E, apparently from 1863, was found in Level 52.
- Operative Noah C. Boyle's 1963 discovery log ends: "Empty room! … OH SHI-". He opened a fake exit.
- The theories (Salvation, Grave Sin, Extraterrestrial Entertainment, the Kauer thesis that Level ! is the fear of
  every chase made real) and "Sub-level of Fourteen" (a hospital, like Level 14) are flavour.

### 1.3 Contradictions, and how this plan reads them

| Question | Versions | This plan |
|---|---|---|
| Length | 10 km everywhere (Miraheze's Level !-! says "10 miles"; *Escape the Backrooms* is "very short despite being 10 km") | About 520 blocks: the user's 1–2 minutes |
| Light | 2021: red *flashing* lights, signs every 10 m. Later: signs at random, clusters and black gaps | Both. Red EXIT signs every ~10 blocks, with clusters and gaps that grow darker toward the end. Emergency beacons on the walls flash while the alarm sounds |
| Surfaces | Wood, then concrete (2022); white (2025); reflective metal start room (2022) | Hospital: pale painted walls with a wooden crash rail (a nod to 2022's wood), white speckled vinyl floor, white ceiling tiles |
| Start | Chased at once (2021) or a start room first (2022, 2025) | The start room |
| Who chases | Hounds, Skin-Stealers, Facelings, Smilers, Partygoers, Deathmoths, Clumps … | The mod's own: Hounds, Skin-Stealers, Smilers, Death Rats, Deathmoths; Clumps as obstacles. No Partygoers (the mod has none; decision 11). Facelings are harmless in this mod, so they stay out |
| Where the exit leads | Your last level (2021), random (2022), safer levels, mostly 1 and 4 (2025), The End (*Escape the Backrooms*) | Fixed per hallway: Level 1, Level 4 or The End |
| Coming back | Never (2021, 2025); often back to your origin (Miraheze) | Never: once you escape, every way in fails for you |

---

## 2. The experience

You open a red steel door marked EXIT that has no business being in a car park. It slams behind you. You are standing
in a hospital room in red light, beside a bed with its sheets folded. Something on the other side of a chained door
hits it, hard. An alarm starts somewhere in the walls. The door to the hallway is stuck. You yank it again, and it
gives.

The hallway runs ahead into red murk, an EXIT sign every few steps, all saying the same thing. Behind you the chained
door bursts. The alarm is suddenly deafening, the beacons on the walls flash, and the roar of the horde comes down the
hall. Run. Swerve round the gurney and the wheelchair, jump the fallen shelving, don't trip on the toy car. The hallway
bends, and straight ahead is a door marked EXIT. Don't take it: the hall turns beside it. Run on. Somewhere in the
dark, an EXIT sign starts to hiss.

Design goals, in order:
1. **It must read as Level ! from the first second:** red EXIT signs repeating into the murk, the alarm, the horde.
2. **A fair chase in Vintage Story,** which has no stamina. A clean run never gets caught; every mistake costs ground
   you win back only slowly; a few mistakes, or stopping, are fatal. Every hazard is announced before it hits.
3. **Short:** one to two minutes, start to finish.
4. **Cheap:** a straight, narrow level; a handful of real entities; a chase that is mostly a number.

---

## 3. The level in this mod

### 3.1 Region and lanes: a copy for each runner

The region stays where the scaffolding put it: due south of spawn, `RegionReach` cells out
(`RunCentreZ = spawnMacroZ + RegionReach`), a noclip-only region like 37 and 94. Its rim is the usual solid boundary.

The lore's "a copy for each person" and "another hallway, and another human running just like him" become **lanes**:
seventeen parallel hallways, one per column of cells, separated by solid wall.

| Constant (in `WorldLayout.LevelRun.cs`) | Value | Meaning |
|---|---|---|
| `RunHalfWidth` | **8** | 17 columns, so **17 lanes** (lane `i` = column `RunCentreX − 8 + i`) |
| `RunHalfLength` | **8** | 17 rows, north to south: row −8 the start room, rows −7…+7 the hallway (15 cells, 480 blocks), row +8 the exit stretch |
| Region | 17 × 17 cells | 544 × 544 blocks. Only the lanes people use are ever generated |

- **Each lane is planned once** from `(seed, lane)` by `PlanCache<RunLanePlan>`: a 32 × 544 tile strip. Cells copy
  their slice of it, like the Poolrooms' blocks.
- **Edges:** inside the region, edges are open (`new Edge { Pattern = WallPattern.RunWall }` with Open tiles), and the
  plan lays every wall itself. Lanes are separated by 13 or more blocks of solid wall.
- **Arrival:** `RunArrivalCell(h)` becomes the start-room cell of lane `h % 17`. `IsRunArrivalSpot` accepts only the
  start room's arrival tile (`Zone == RunZone.StartRoom`, marked).
- **Rule 1 and the lanes.** Each entrance is written down as leading to one lane's start room. If that lane is in use
  when someone comes through, `RunSystem` sends them to the next free lane instead, and nothing is written down. This
  is canon's "forced to separate".
  - When a group goes through together (`ThresholdSystem.PlayersNear`), each person gets their own lane.
  - If all 17 are busy, the door won't open: "The door won't open. Someone else is running."

### 3.2 Length: about 520 blocks, a minute and a half

**Hallway rows.** Rows −7 to +7 hold 15 cells, which is 480 blocks.

**Hallway length, door to door:**
- It starts at the start room's hallway door, at local z 24 of row −8.
- It ends at the exit door, at local z 12 of row +8.
- In z, that is 8 + 480 + 12 = **500 blocks**.
- The two doglegs add 8–10 blocks each across, plus the corners.
- **Running length: 515–525 blocks.**

**Time.** A Vintage Story sprint is twice the walk (`GlobalConstants.SprintSpeedMultiplier = 2`), about 5.5–6 blocks
a second on flat floor.

| | Time |
|---|---|
| Clean sprint over 520 blocks | **87–95 s** |
| Weaving and the odd jump (5–8 % extra) | about 1:35–1:45 |
| From arrival to exit, with the start room | under 2 minutes |

**Why this length:**
- It sits in the middle of the user's window.
- Runs much shorter than 80 s give the horde no time to matter. Much over 110 s and a run with one recovered mistake
  breaks two minutes.
- The level spends exactly 15 whole cells on the hallway, so the lane plan, the cells and the region line up.
- One constant, `RunRows` (15), sets the length. If the sprint measured in the harness (section 8) comes out far from
  5.8 blocks a second, set `RunRows = round(92 s × S / 32)`.

**Hunger is no brake.** Vintage Story burns satiety about 2.6 times as fast while sprinting
(`EntityBehaviorHunger`: `0.96·t + 1.5·sprintTime` per 10 s). A whole run costs about 25 satiety of 1500, so
fairness has to come from the course (section 4.2).

### 3.3 The lane plan

Local coordinates: x 0–31 across the lane's column, and s (distance along the centreline) from the hallway door.

**Cross-section.**
- Floor at the shared `FloorY`, four blocks of air (`Grand`), then the ceiling.
- The clear width is **5** (local x 14–18 on the straights).
- Walls at x 13 and x 19 carry the doors.
- The EXIT signs hang in the fourth block of air. Head room is 3.4 blocks under a sign, so a jump onto a 0.9-block
  obstacle (head at about 3.05) never hits one.
- Everything outside the hallway and its rooms is solid `RunWall`.

**The start room** (row −8, `Zone = 1`):
- **Interior:** 7 × 7, local x 13–19, z 17–23, Grand.
- **Doors:**
  - Hallway door (`RunHallDoor`) in the south wall at (16, 24), in line with the hallway.
  - **Chained door** (`RunChainedDoor`) facing it, in the north wall at (16, 16).
  - **Marked door** you came in by (`RunMarkedDoor`, a big red "!" on its inner face) in the west wall at (12, 20).
- **Furniture:**
  - The hospital bed (existing `Props.HospitalBed`, head and foot) along the east wall at x 19, z 18–19.
  - **Bedside table** (`RunBedside`) at (19, 20).
  - **Medicine cabinet** on the east wall (`RunMedCabinet` at (20, 21), rel 2).
  - **Privacy curtain** on a ceiling rail, x 17, z 17–19, walk-through.
- **Light:** one red lamp (existing `CeilingKind.LampRed`) at (16, 20).
- **Arrival tile:** (14, 21), facing east.
- **Behind the chained door:** a sealed, black **antechamber** 5 × 3 (x 14–18, z 12–15, `Zone = 4`, `RunVoid`
  walls, no light). The horde comes out of it.

**The hallway.**
- **Straights.** The centreline runs due south down local x 16.
- **Two doglegs** (the lore's bends), one in each of rows −3 and +2, at a hashed local z:
  - At each, the hall turns 90°, runs across the lane 8–10 blocks, and turns back south.
  - The first dog-leg goes east or west by hash; the second comes back, to x 14–18 or offset by up to 4.
  - The x range always stays within 4–27.
- **Fake exits.** At each dog-leg's first corner, the end wall straight ahead holds a **fake exit** (`RunFakeExit`)
  under a **dim** EXIT sign (`RunExitDim`, a little darker, as canon says).
  - Behind it is a 3 × 3 closet (`Zone = 3`, sealed, dead ceiling panel, nothing in it).
  - The rule the player has to learn: **a door with a turn beside it is a lie.**
- **The real exit** (row +8). The hallway runs straight to a dead-end wall at local z 12, with walls unbroken either
  side for the last 24 blocks. The **true exit** (`RunTrueExit`) is in the end wall, under a bright EXIT sign. No turn
  either side.
- **Side doors** (`RunSideDoor`, locked, indestructible) on both walls along every straight:
  - one every 4 blocks, with the two sides staggered by 2 (canon's every 3 m);
  - never within 3 blocks of a corner or the exit;
  - one door in five has an **emergency beacon** above it (`RunWallBeacon`, facing the hall).
- **Wall trim.** Every wall face along the hall is `RunWallRail`: a wooden crash rail at hip height on the hall side.

**Light: the EXIT signs** (`CeilingKind.RunExitSign`, on centreline tiles):
- Spacing 10 ± 3 along s.
- Per 32-block segment, a hash decides one of:
  - a **dark gap** (no sign): 15 % in the first two thirds, 35 % in the last;
  - a **cluster** (spacing 4): 10 %.
- No dark stretch is longer than 32 blocks (40 in the last third).
- Every corner and every exit has a sign over it.
- The other ceiling tiles are plain tiles, dead troffers (one in six), and **air vents** (`RunVent`, one in 20, where
  vent drops can happen).

**Thirds of the run.** The plan places features by the third of the run they fall in:

| | First third (to dog-leg 1) | Middle (between doglegs) | Last third (to the exit) |
|---|---|---|---|
| Obstacle groups | every 16 ± 4 blocks | every 14 ± 4 | every 12 ± 4 |
| Kinds | gurneys, wheelchairs, chairs, IV stands | + crash carts, standing shelves that topple, swinging doors | + fallen shelving, trip props (toy cars, boxes, cords), debris, one hole (1 lane in 3) |
| Signs | normal | normal | fewer: the dark end the lore describes |
| Event doors | 1 dented door | 1–2 dented, 3–4 swinging | 1 dented, 3–4 swinging |

**Obstacle rules** (checked by the harness, section 8):
- In any tile row, at most 3 of the 5 tiles are blocked.
- Gaps in consecutive blocked rows overlap, or the rows are at least 4 apart, so there is always a line through at a
  sprint.
- A row the whole width blocked by a jumpable obstacle (toppled shelving, 0.9 high) counts as open.
- Nothing blocking within 6 blocks of a corner or a fake exit, or in the first 12 blocks after the start room.

**Layout version 6: the gauntlet** (the user's play-test: "there need to be way more obstacles ... it should be
difficult to get through"). `PlanRunGauntlet` replaces the obstacle groups above with a set piece every 3-7 blocks (2-5
in the last third). Lore: Fandom 2025, "Large obstacles (such as chairs, beds, etc.) may block the wanderers' progress
... smaller obstacles (such as toy cars, boxes, etc.) are even more lethal", and its collapses ("the walls and the
ceiling may also collapse ... power lines may hang from above"); the Wikidot forks' gurneys and medical tech; *Escape
the Backrooms*' hall (a set of chairs, an open cabinet, tables, "a whole line of objects" with fallen chairs to jump,
tables that "almost fully block your path", a blockade with the way round beside it).

| Set piece | What |
|---|---|
| Barricade | Beds, mattresses and chairs piled two blocks high (`RunBarricade` 0), 2-4 wide from a wall, sometimes 2 deep; something to jump on the other side |
| Collapse | The ceiling come down by a wall (`RunCollapse` 0: a slab from a hole onto rubble, floor to ceiling) with a heap of rubble beside it (`RunCollapse` 1, 0.75 high), broken ceiling tiles strewn after |
| Line | A whole row of things to jump (gurneys across, tipped gurneys, wheelchairs, IV stands, chairs, crash carts), one gap or none |
| Needle | Barricades and supply cabinets leaving one column |
| Cabinet | A tall supply cabinet against a wall, its door open into the hall (`RunBarricade` 1), with things beside and across |
| Gurneys | Two gurneys along the hall, staggered |
| Shelving | Fallen shelving across from a wall |
| Tipped gurney | A gurney on its side across the hall (`RunBarricade` 2-3, 0.94 high) |
| Feint | By a side door: the way past a barricade opens along the wall and ends at a cabinet two blocks on; the way on is back across, or over a gurney |

Every piece is kept only if the straight can still be run at a sprint (`RunSprintable`): a runner a block wide and two
high, one row forward at a time and at most one column across, never into what must be gone round (two blocks high, a
pit, a swinging door's leaf) nor between two such corner to corner; anything a block high or less is jumped (a
Vintage Story sprint-jump rises about 1.27 blocks and keeps its speed while jump is held; the step-up is 0.6). Trip
props come in the gaps (more in the last third); jumping over them avoids the trip. On seed 0 the best line through a
lane takes 33-57 column changes and 24-46 jumps (version 5: none and about 5). The horde's front is still a number;
the puppets you see now step round what can't be jumped and bound over what can.

**Supplies in the hall.** Two or three **supply trays** (`RunTray`: a kidney dish with an Energy Bar or Almond Water)
stand in door recesses, so you see them only as you pass ("hidden or out of one's view"). Each costs about a second.

**The runners who didn't make it.** Two to four **runner's remains** (`RunRemains`: a torn backpack, a single shoe, a
dark smear) lie along the hall. Floor tiles near them are **scuffed** (`RunScuffed`: heel marks, drag smears, claw
scratches). One in four remains holds a wanderer's note (section 5.5). Players who die here leave their own gear.

**The Safe Zone** (lore 2025, about 6 %; here **1 lane in 5**, by lane hash). In the middle third, between the
doglegs, a **24-block blue stretch** (`Zone = 2`):
- An open doorway at each end.
- Blue-grey floor (`RunSafeFloor`), pale blue walls (`RunSafeWall`), blue ceiling panels (`RunSafeLight`) every 4
  blocks.
- Four side rooms of 4 × 4 (two each side, through open doors `RunSafeDoor`), each with a **shelf** (`RunSafeShelf`:
  Almond Water and Energy Bars) and a **cot** (`RunSafeCot`).
- The sign "WELCOME to the safe zone. Please take a break before you continue running."
- Its rules are in section 4.4.

**Holes** (1 lane in 3, last third only): a 2 × 2 hole (`TileKind.Pit`, `Unders.RunHole`) against one wall, leaving
3 tiles to pass. It is preceded by 4 blocks of **cracked floor** (`RunCracked`) as the warning. Falling in is a way
out (section 5.2).

### 3.4 Look

| Surface | Look |
|---|---|
| Walls (`run-wall`) | Pale institutional paint, off-white with a faint green, a darker vinyl cove base 2 px high. The **crash rail** is real 3D: a rounded wooden bar on steel brackets at hip height |
| Floor (`run-floor`) | White-grey speckled hospital vinyl. A charcoal-blue border band along the walls. Scuffed, cracked and safe-zone variants |
| Ceiling (`run-ceiling`) | 2 × 2 white acoustic tiles in a T-bar grid. Dead troffers. Recessed louvred vents (3D louvres) |
| EXIT signs (`run-exitsign`) | Hanging double-sided boxes, dark housings with glowing red **EXIT** letters and chevrons pointing on down the hall |
| Beacons (`run-beacon`) | Small red domes on the walls, which flash while the alarm sounds |
| Doors | Grey brushed steel set in a recessed frame, a small wired-glass window, a push plate. Red-painted fire doors with panic bars for the exits |

Under the red light everything reads as shades of red and black. A held torch shows the true colours, and so does the
blue safe zone. The fog (section 3.6) closes the view at about 45 blocks, so on a straight the EXIT signs repeat into
red murk and are gone: canon's "the exit sign … kept repeating in your sight".

### 3.5 Temperature, stability and the menace director

| | Value | Why |
|---|---|---|
| Temperature | Hallway 20 °C, start room 18 °C, safe zone 21 °C | A hospital. Running is already enough |
| Reality Stability (`RunStability`) | Start room 0.35; hallway 0.45 + 0.05 × drift; exit stretch 0.8; safe zone 1.25 | The alarm "harmful to the mental state"; the safe zone a real rest |
| Menace band | **Safe** everywhere in the region (`MenaceSystem.Rate`: `level == RunLevel → Safe`) | The director stays out; `RunSystem` owns every entity here |
| `Danger.OfLevel(RunLevel)` | **0.9** | For the horde's stats when it catches you: Class 5 / "!" |
| Rest | The safe zone counts as rest for `TimeOut` (it is Safe and calm); nothing else does | |

### 3.6 Fog, light and sound

**Fog** (`AtmosphereSystem.Levels[14]`):
- Hallway and start room: `new(0.022f, 0.30f, 0.04f, 0.04f, 0f)`, a close red murk.
- While the alarm is on, the red channel pulses ±15 % at **1 Hz** (a smooth sine, never a hard flash).
- Safe zone: `new(0.006f, 0.42f, 0.56f, 0.85f, 0f)`, clear and blue.
- Titles: `level-14` on entering; the safe zone shows `level-141`.

**Light.**
- EXIT signs emit real block light, red (`lightHsv [0, 7, 9]`). Dim fake-exit signs `[0, 7, 5]`; bright true-exit
  sign `[0, 7, 12]`.
- That is about 50 sources per lane, lit with the rest of the cell by `WorldLighting`'s flood fill, like Level 0's
  panels.
- Safe-zone panels are blue, about `[42, 4, 14]`.
- **The flashing is glow-only,** never changes in block light:
  - Beacons are a block entity like `BlockEntityFlickerLight`. The client swaps their mesh between lit and dark,
    0.25 s on in each second, only within 32 blocks, and only while the alarm is on.
  - Telegraphing signs (section 4.3) reuse `BackroomsFlicker` itself.
- **Photosensitivity:** everything that flashes stays at or below 1 Hz and ramps, never a full-screen strobe.

**Sound.** No hum. The **alarm** is the level's voice (sounds in section 7.4):
- Before the chained door breaks, it is faint, muffled in the walls.
- After, it plays at full volume, **non-positional** ("in your head"), as a loop.
- The **horde roar** is positional at the front of the horde, so its loudness *is* the gap.
- A **heartbeat** starts when the horde is within 20 blocks and quickens within 10.
- The safe zone has its own quiet room tone, with the alarm a ghost far away.

**Map colour:** the hallway floor a dark red (#5A1012), walls black, the safe zone blue (#3A5C8C).

---

## 4. The chase (`src/Regions/RunSystem.cs`)

### 4.1 A run, second by second

`S` is the player's measured sprint speed in blocks per second (section 8; expected 5.6–6).

| Time | What happens |
|---|---|
| 0 | Arrival in the start room. The marked door slams (`slam`) and is locked for good ("It won't budge."). The faint alarm starts. The chained door is hit every 1.2–2 s (`bang1-3`) |
| 0 → | The **hallway door is stuck:** the first two uses rattle ("The door is stuck!"); the third opens it (a block swap to open). Canon: "rarely work on the first try" |
| 6 s | The chained door **bulges** (block swap); the blows come faster |
| **12 s, or 4 s after the player crosses the hallway door line** (whichever is first) | The chained door **bursts** (`doorbreak`). The alarm goes to full; the beacons and the fog pulse start; the roar starts. The horde's **front** starts at the antechamber, 8 blocks behind the hallway door |
| until the exit | The front runs down the centreline (section 4.2) |
| Exit door | The run ends; the horde is gone. The player is carried out (section 5.2) |

**Why the 4 seconds.** A player who leaves the room promptly reaches the hall about 23 blocks ahead when the door
breaks, so starts about 31 blocks ahead of the front, whatever they took from the room. A player who dawdles past 8
seconds starts closer. That is canon's "five seconds" of gathering, made a real trade.

**Before the break** the hallway is calm: a faint alarm, the beacons dark. Canon's pristine-hospital phase is kept to
these few seconds.

### 4.2 The front: a rubber band, as canon says

The horde is **one number**: the front's position `f` along the centreline. The player's position is projected onto
it as `p`, and the **gap** is `g = p − f`. Each server tick (100 ms):

| Situation | Front speed |
|---|---|
| First two thirds | **0.90 · S** |
| Last third | **0.94 · S** ("fewer, but more aggressive") |
| `g > 40` | **1.0 · S**: it keeps pace, out of sight ("They are still near!") |
| Player in the safe zone | Holds at the safe zone's entrance (section 4.4) |
| `g ≤ 1.5` | **Caught** (section 4.5) |

**What this means in play:**
- **A clean sprint is never caught.** It gains 0.1 S (about 0.6 blocks a second) until the gap reaches 40, then holds
  there.
- **A mistake costs ground you win back slowly.**

  | Mistake | Ground lost |
  |---|---|
  | Opening a fake exit | about 2.5 s, 14 blocks |
  | A trip | 0.8 s |
  | Snagging on a gurney | 1–2 s |

  The 40-block lead is a bank of about **7 seconds of mistakes**. It refills at a tenth of a second per second (less
  in the last third).
- **Stopping kills.** From 40 blocks ahead, a standing player is caught in about 8 s and a walking one in about 20 s.
- **The horde is never slower than "nearly the same speed"** as you, as canon says. It does not care how fast the
  entity it shows is.

**Scaling with the world setting** *Backrooms entities*:

| Setting | Front speed (two thirds / last third) | Break |
|---|---|---|
| Low | 0.85 / 0.90 S | 15 s |
| Normal | 0.90 / 0.94 S | 12 s |
| High | 0.93 / 0.97 S | 9 s |

The model is a small class with no game dependencies (`RunChase`, like `ThresholdNetwork`), so the harness can
simulate runs (section 8).

### 4.3 Hazards, all announced

| Hazard | Per lane or run | Warning, then effect |
|---|---|---|
| **Swinging door** (`RunSwingDoor`) | 6–9 per lane (middle and last thirds) | When the player is 9 blocks off, a side door ahead flies open into the hall (`swing`; a block swap to an open leaf filling the tile in front of it). At a sprint that is 1.5 s to swerve. (*Escape the Backrooms*' doors) |
| **Toppling shelf** (`RunShelfStanding` → `RunShelfFallen`) | 2 per lane | When the player is 10 blocks off, a tall blue shelf in a door recess tips across 3 tiles of the hall (`topple`). It is 0.9 high, so jump it |
| **Dented door** (`RunDentedDoor`) | 2–4 per lane | Heard banging from 20 blocks. When the player is 2 blocks past, it bursts and a Skin-Stealer (or Death Rats) comes out behind them at **0.8 S**: a scare that only catches someone who stops. Canon: those that burst out are "much slower" |
| **Vent drop** (`RunVent`) | 1 run in 2 | As the player passes under a vent, it bursts (`ventburst`) and a Hound lands 3 blocks *behind*. It runs at 1.0 S for 6 s, then falls back into the horde |
| **Sign burst** | 1 run in 3, middle or last third | A sign 25–35 blocks ahead hisses (`signhiss`) and flickers erratically (swap to the flicker variant) from 40 blocks. At 14 blocks it **bursts** (`signburst`, a white flash particle, the sign swapped to dead). A **curtain of fire** 3 blocks deep fills the hall for 10 s (fire particles). Crossing it sets you alight (`Entity.Ignite()`, vanilla burning, about 4–5 HP unless you put it out). Wait and the horde comes. Canon: "the only way out … was … through that wall of fire" |
| **Trip props** (toy car, boxes, cord) | 3–6 per lane, last third | Small and hard to see in the dark. Sprinting over one trips you: `walkspeed −0.6` for 0.8 s (`trip`). Walking over is safe |
| **Clump** | 1 lane in 3, last third | A buried Clump (existing entity, `quiet` rules) lies across 2 tiles: an obstacle that grabs whoever steps on it |
| **Hole** | 1 lane in 3, last third | Cracked floor for 4 blocks first. Falling in is an exit (section 5.2) |

**Timing.** Every swing, topple and burst triggers on distance *ahead*, at 9 blocks or more, which is 1.5 s at a
sprint. Nothing appears on top of the player or in front of their face.

Swaps are recorded per run and undone when the lane resets (section 4.6).

### 4.4 The safe zone

- **While the player is inside,** the front waits at its entrance. Up to three horde entities stand in the doorway,
  snarling, and never cross. The alarm is muffled; the zone's room tone plays.
- **Leaving** by the far doorway starts the front again from the *entrance*: the gap is the zone's 24 blocks plus the
  player's head start. Canon: "the entity will enter through the entrance of the safe zone and continue".
- **Staying.** It is lore 2022's Checkpoint as well:
  - at **2 in-game hours** the walls shudder ("The walls shudder. You can't stay here much longer."; dust particles);
  - at **3** the horde comes in through the entrance.
  - A Vintage Story day is 48 minutes by default, so that is about 6 real minutes.
- **The shelves** hold 2 Almond Water and 3 Energy Bars between them, restocked when the lane resets. The cots are
  decor, not beds: no sleeping through it.

### 4.5 The horde you see, and being caught

**What you see.** The front is invisible. What you see are **presentation entities**:
- **How many:** five while the gap is 48 or less in the first two thirds; three in the last third.
- **Where:** each at `f − U(0, 6)` along the centreline, spread across the width. Deathmoths fly at the fourth block.
- **When they come and go:** they are put down in the dark beyond sight. They are removed when the gap passes 60.
- **What they are:** mixed per lane by hash, from the mod's own:

  | Entity | Share |
  |---|---|
  | Hound | 35 % (always in front) |
  | Skin-Stealer | 20 % |
  | Smiler | 15 % (its glowing face in the dark stretches) |
  | Death Rat pack | 15 % |
  | Deathmoth | 15 % |

**How they move.** They are **puppeted, not path-found:**
- A pre-planned "racing line" (a BFS path through the lane's open tiles, smoothed) gives the line;
  `RunSystem` sets each one's server position along it every tick, with its run animation playing. The client
  interpolates the motion.
- This costs nothing, never gets stuck on a gurney, and shows canon's "speeds … nearly the same".
- Fallback, if puppeting looks wrong in a client: a straight-line AI task (`AiTaskHorde`) with its speed set each tick.

**Player-built walls.** The horde tears down anything a player builds in its way. When the front reaches a
player-placed block in the hall, it is broken and dropped, with a crash. The lane's own walls, floors, ceilings and
doors are indestructible, as Level 37's tile is (`SalvageSystem` structure).

**Horde entities are worth nothing.**
- They are flagged `backrooms:horde`: no bounty (`Rewards.Bounty` skips them), no drops, no director rules.
- One that is killed is replaced at the front 3 s later. Farming the horde is pointless.

**Caught** (`g ≤ 1.5`). The horde pins you:
- `walkspeed −0.9` (stat `backrooms-caught`);
- 2 damage every 0.5 s, × `Danger.Damage(0.9)` (≈ 4), on top of the presentation entities' own bites;
- an unarmoured player dies in about 2 s, an armoured one in a few more.
- The death message is "was caught by the horde". You wake in Level 0 by the anchor rule. What you carried stays in
  the hall for the next runner to find.
- Canon: "killed in the most painful and brutal way possible".

### 4.6 Runs, lanes and edge cases

| Situation | What happens |
|---|---|
| A run | Per player: lane, phase, start time, front `f`, events fired, block swaps made. Saved in the world's mod data, so a server restart doesn't lose it |
| **Lane reset** | 30 s after a run ends (escape, death or leaving) with nobody in the lane. Every swap is undone: doors shut, shelves upright, signs whole, the chained door chained, the hallway door stuck again. The start room's bedside table and cabinet, the trays and the safe-zone shelves are put back. Dropped items are left alone |
| Logging out mid-run | The run ends. On logging back in, the player is put back in the lane's start room and a fresh run starts (*Escape the Backrooms*' trivia: "the level will restart") |
| Creative or spectator | No run: the alarm plays, the horde stays behind its door |
| `/backrooms tp !` | Arrives in a free lane's start room and starts a run. Debug: `/backrooms run status \| start \| stop \| gap <n>` |

---

## 5. Ways in and out

### 5.1 Entrances: rare, and true to the lore's methods

The rules: walked through means two-way; fell, dived or taken means one-way. Canon is explicit that the way in
**slams and locks behind you** (the "!" appears on its inside), so every entrance is **taken: one-way**. Each feature
has its own hash salt (0x14xx), so nothing else in those levels shifts.

| From | Threshold | Rarity | To | Way back | Canon basis |
|---|---|---|---|---|---|
| **Level 1** | **A door that shouldn't be there**: a red steel fire door with a push bar and a glowing EXIT sign above it (`WallPattern.RunEntryDoor` on a `Door` tile), set into a solid district wall of the car park where no corridor runs. Kind `runentry` | About 1 car-park cell in 300 | Level !, a lane's start room | None: it slams. The inside face has the "!" | Fandom 2025: "an exit door that is incompatible with its surroundings"; Miraheze: crimson doors out of context, never in Level 0 |
| **Level 2** | **The wall that wasn't there**: a minor tunnel ends in a smooth, new concrete wall unlike the tunnel's, with a thin line of red light at its foot (`Unders.RunFalseWall`). Walk into it: you noclip | About 1 cell in 250 with a blind end | Level ! | None (noclip) | Fandom 2021 and 2022 discovery log ("That wall definitely was not there"); Fandom 2025 "noclipping … in Level 2"; Miraheze: Level !-! from Level 2 |
| **Level 37** | **The red corridor**: 1 dry corridor in 5 (instead of becoming office carpet) turns to hospital vinyl lit red by one EXIT sign, ending in a red EXIT door (`Unders.RunRedCorridor`, door kind `runentry`) | About 1 per 20 plan blocks | Level ! | None | *Escape the Backrooms*: "Find the red short hallway in Level 37" |
| **The exit's arrival door** (section 5.2) | The door you came out of, now marked with a red "!" (a block placed at runtime, kind `runentry`) | One per escape | Level ! (another runner's start room) | None | Fandom 2025: "the exit door has been converted into an entrance door" |
| *Optional:* Level 4 | An elevator with a red "!" painted on its doors | 1 in 40 elevator cores | Level ! | None | Fandom 2025: "an elevator with an exclamation mark printed on it" (decision 8) |
| *Optional:* The Hub | A door with a red "!" (if the Hub plan wants one) | One | Level ! | None | The Hub links to many levels |

**Escaped players can't come back** (Fandom 2021 and 2025):
- When a player escapes, the attribute `backrooms:ranOut` is set on them.
- For that player, every `runentry` threshold "will only reach another location in the level he was in": it carries
  them to `FindArrival(currentLevel, doorKey)`, the same place every time for that door.
- Message: "You have run this hall before. The door lets you out somewhere else."

### 5.2 Exits

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| The end of a lane | **The true exit door** (`RunTrueExit`, kind `runexit`) | Fixed per lane by hash: **Level 1** (9 lanes), **Level 4** (5 lanes), **The End** (3 lanes; to be agreed with the End plan) | None: canon's "never re-enter". You arrive out of a door with a red "!" (next row) | Fandom 2025 (Levels 1 and 4; "like a warehouse … a resting area"); *Escape the Backrooms* (The End) |
| The arrival | A red "!" door is placed on the wall beside the arrival (`run-exitdoor-marked`, like a thin spot but a door): the exit "converted into an entrance" | Leads into Level ! (section 5.1) for anyone who hasn't escaped | | Fandom 2025 |
| A lane's hole (1 lane in 3) | Falling in (`Unders.RunHole`, `rel < −1.5`) | **Level 8**, out of the rubble of a collapse | None (one-way) | Fandom 2022's "gaping hole"; 2025's collapse ("we never know where they end up"). Level 11's collapsed streets already lead to Level 8 |
| Anywhere | Being caught | Level 0 (the anchor rule) | | |
| A fake exit | Opens on an empty closet: not a threshold | | | Fandom 2022, 2025 |

**Map marks and messages:**
- Entrances are one-way: `waypoint-oneway`. The arrival in Level 1, 4 or The End is marked "The way out of Level !".
- On escaping: "No turn either side. This was the real exit. The Backrooms will never send you there again."

### 5.3 Rows for the handbook's "Ways Between Levels" and the README

| From | Way | To |
|---|---|---|
| Level 1 | A red EXIT door where no door should be (one-way) | Level ! |
| Level 2 | A dead end that wasn't there: walk into it (one-way) | Level ! |
| Level 37 | A dry corridor lit red, ending in an EXIT door (one-way) | Level ! |
| Level ! | The real exit (no turn either side) (one-way) | Level 1, Level 4 or The End |
| Level ! | A hole in the dark, after the cracks (one-way) | Level 8 |

### 5.4 Noise, sanctuaries, notes

- The start room and the safe zone are not sanctuaries for the director, because the director is silent here anyway.
- Wanderers (`WandererSystem`) never appear in Level !.

### 5.5 What there is to find

| Where | What |
|---|---|
| Start room | Bedside table: 1 Almond Water and 1–2 **Energy Bars**. Medicine cabinet: a clean bandage (`game:bandage-clean`). Break the table or cabinet open; it takes about a second |
| Hall | 2–3 trays in door recesses: an Energy Bar or Almond Water. Runner's remains: cloth salvage, and sometimes a note |
| Safe zone | The shelves (section 4.4) |
| Players' deaths | Whatever they dropped |

**The Energy Bar** (new item, `run-energybar`):
- Food: satiety 160, Grain.
- Eating it gives a **second wind**: `walkspeed +0.12` for 30 s (stat `backrooms-secondwind`). That is worth about 3
  seconds of ground over a run, which is why canon's runners save theirs for later.
- Found only in Level ! and its safe zones.

**Wanderer's note**, in one runner's remains in four: "Don't take the door if the hall turns beside it. The real one
is at a dead end. Don't stop. They're still there."

---

## 6. Survival role

| | Level ! |
|---|---|
| Teaches | Commitment, reading the course, and that some places you simply get through |
| Gives | A fast, fixed way from three levels to the Habitable Zone, the Abandoned Office or The End; Energy Bars; the gear of those who failed |
| Takes | Everything you carry, if you're caught; you can't stop, rest, loot or build |
| Fits the loop | An expedition of two minutes, once in a lifetime: escape and it's gone for you; die and you may stumble in again |

---

## 7. Asset manifest (`tools/gen_run.py`)

**Where things go:**

| What | Folder |
|---|---|
| Blocktypes | `assets/backrooms/blocktypes/run/` |
| Block textures | `assets/backrooms/textures/block/run/` (32 × 32, the mod's `S`) |
| Block shapes | `assets/backrooms/shapes/block/run/` |
| Items | `itemtypes/run/`, `textures/item/run/`, `shapes/item/run/` |
| Sounds | `sounds/ambient/run/`, `sounds/effect/run/` |

All codes are prefixed `run-`. Built with the existing kits (`detail_kit.py`, `detail_textures.py`, `texlib.py`).

**Structure blocks** (walls, floor, ceiling, doors) are unbreakable in Level ! (resistance 99999, no drops). They are
also kept out of `Salvage/Breakdown.cs`. Props salvage normally.

**Light** is given as VS `lightHsv` [hue 0–63, saturation 0–7, value].

### 7.1 Reserved enum values used (`Tiles.cs` blocks reserved by the scaffolding)

| Enum | Range | Members |
|---|---|---|
| `WallPattern` | 64–79 | 64 `RunWall` (exists), 65 `RunWallRail`, 66 `RunWallBeacon`, 67 `RunSideDoor`, 68 `RunDentedDoor`, 69 `RunSwingDoor`, 70 `RunFakeExit`, 71 `RunTrueExit`, 72 `RunChainedDoor`, 73 `RunHallDoor`, 74 `RunMarkedDoor`, 75 `RunMedCabinet`, 76 `RunSafeWall`, 77 `RunSafeDoor`, 78 `RunVoid`, 79 `RunEntryDoor` (Levels 1 and 37) |
| `FloorKind` | 100–115 | 100 `RunFloor` (exists; vinyl), 101 `RunBorder`, 102 `RunScuffed`, 103 `RunCracked`, 104 `RunSafeFloor` |
| `CeilingKind` | 16–23 | 16 `RunCeiling` (exists; tile), 17 `RunPanelDead`, 18 `RunExitSign`, 19 `RunExitDim`, 20 `RunVent`, 21 `RunSafeLight`, 22 `RunExitBright` |
| `Props` (ushort) | 300–319 | 300 `RunGurney`, 301 `RunGurneyFoot`, 302 `RunWheelchair`, 303 `RunIvStand`, 304 `RunChairs`, 305 `RunCrashCart`, 306 `RunShelfFallen`, 307 `RunShelfFallenB`, 308 `RunShelfStanding`, 309 `RunToyCar`, 310 `RunBoxes`, 311 `RunCord`, 312 `RunSheets`, 313 `RunRemains`, 314 `RunTray`, 315 `RunBedside`, 316 `RunSafeShelf`, 317 `RunSafeCot`, 318 `RunDebris`, 319 spare. Walk-through (`RunWalkThrough`): 309–312, 318 |
| `Unders` | 40–49 | 40 `RunFalseWall` (Level 2), 41 `RunRedCorridor` (Level 37), 42 `RunHole` |
| `Tile.Zone` (Level ! meaning) | | 0 hallway, 1 start room, 2 safe zone, 3 fake-exit closet, 4 antechamber, 5 exit stretch |

### 7.2 Blocks

**Structure.**

| Code | Variants | Texture (32 px, palette) | Shape |
|---|---|---|---|
| `run-wall` | `plain`; `rail-{n,e,s,w}` (rail on that face) | Paint `#D8DDD3` with fine roller stipple ±3; cove base 2 px `#5E6A62` at the bottom of the lowest block; faint scuffs at hip height | Cube. Rail variant adds the **crash rail**: a bar 16 × 2 × 2 voxels at y 12–14, 1 voxel off the face, warm oak `#8A5A32` with a rounded highlight; two steel brackets 1 × 3 × 2 at x 3 and x 12 |
| `run-wall-beacon` | `{n,e,s,w}` × `lit` / `dark` | Same wall; dome `#C81010` lit (glow 200), `#3A0A0A` dark; base `#2A2A2A` | Wall cube plus a beacon at y 11–15: a base 5 × 1 × 3, a dome 4 × 3 × 3 stepped (3 × 1 × 2 cap), a wire guard 2 bars 0.5 voxel. Block entity `RunBeacon`; no block light |
| `run-floor` | `vinyl`, `border`, `scuffed`, `cracked`, `safe` | `vinyl`: `#D4D4CC`, 3 % dark speckles `#6E6E6A`, 2 % light `#F0F0EA`, a faint sheet seam every 32 px. `border`: a band 10 px `#3E4A55` on one half. `scuffed`: black heel marks, two brown drag smears `#4A2A20` at 60 % alpha, three parallel claw scratches. `cracked`: a dark branching crack (2–3 px) with chipped edges. `safe`: blue-grey `#B4C2D2` with the same speckle | Cube |
| `run-ceiling` | `tile`, `panel-dead`, `vent`, `vent-burst` | `tile`: 2 × 2 tiles a block, fissured acoustic pattern `#E8E8E2`, T-bar grid `#CFCFC8`. `panel-dead`: a troffer with grey diffuser `#9A9C9A` and parabolic louvres. `vent`: a dark louvred grille `#8C8F8C` | `vent`: real louvres, 6 slats 14 × 1 × 2 angled 30° recessed 2 voxels into the block's underside, inside a frame. `vent-burst`: the grille hanging from one edge at 70°, 14 × 1 × 14 |
| `run-exitsign` | Axis `ns` / `we` × `lit`, `dim`, `bright`, `flicker`, `dead` | Housing `#1A1A1A`. Letters "EXIT" 3 px high, `#FF2A1E` (lit, glow 255), `#B01810` (dim, glow 150), `#FF5040` (bright, glow 255), soot-black with a cracked lens (dead). Chevrons "›" either side pointing down the hall, both faces | Box 14 × 7 × 2 at x 1–15, y 7–14 (the top block of air); two rods 1 × 2 × 1 at x 4 and 11, y 14–16. `flicker` has block entity `BackroomsFlicker` (lit and dark meshes). Light: lit `[0,7,9]`, dim `[0,7,5]`, bright `[0,7,12]`, flicker `[0,7,9]` (block light stays; only the glow flickers), dead none |
| `run-exitsign-wall` | `{n,e,s,w}` × `dim` / `bright` | As above, single face | Box 14 × 6 × 2 against the wall at y 8–14 of the block above a door |
| `run-safelight` | | Opal diffuser `#DCEAFF`, glow 160 | Recessed panel 14 × 1 × 14 under the ceiling face. Light `[42,4,14]` |
| `run-safewall` | `plain`, `sign-{n,e,s,w}-{l,r}` (two-block sign) | Pale blue paint `#C4D6E8`. The sign is white with blue text: "WELCOME / to the safe zone. / Please take a break before / you continue running." (`text()` from `detail_textures`) | Cube; the sign a 1-voxel plate across two blocks at eye height |

**Doors** (all 1 wide × 2 high, `lower` / `upper`, facing `{n,e,s,w}`; leaf 16 × 32 × 2 voxels set 1 voxel into the
wall face, in a frame 1 voxel proud):

| Code | States | Texture | Shape detail | Behaviour |
|---|---|---|---|---|
| `run-sidedoor` | `closed`, `dented`, `open` | Brushed steel `#8E9396` with vertical grain, frame `#5C6164`, a wired-glass window 6 × 8 px (`#1C2226`, wire grid) in the upper leaf | Push plate 4 × 6 × 0.5, lever 4 × 1 × 1 on a rose. **`dented`:** the leaf bulges 2 voxels outward in a 10 × 12 patch (stepped boxes), scratches. **`open`:** the leaf swung 90° into the hall, standing perpendicular to the wall, hinged at one edge, occupying the next tile (collision only on the leaf) | Unbreakable. Use → `rattle`, "Locked." |
| `run-exitdoor` | `fake`, `fake-open`, `true`, `marked`, `entry` | Fire-door red `#9E1C18`, scuffed paint; panic bar steel. `marked`: a huge red "!" painted across both blocks (`#E01810`, drips), on the inside face. `entry`: the same red door, plain (the "!" is only on the inside) | **Panic bar** 12 × 2 × 2 on two end cases 2 × 3 × 3, at y 13–15 of the lower block; kick plate 14 × 3 × 0.5 steel | Threshold kinds `runfake` (swaps to `fake-open`, showing the closet), `runexit`, `runmarked` ("It won't budge."), `runentry` |
| `run-chaineddoor` | `intact`, `bulging`, `broken` | Steel as above, rust streaks `#6A3A20`. Chains `#4A4A4A` | **Chains:** two diagonal runs of links (alternating 2 × 1 × 1 and 1 × 1 × 2 boxes) crossing in an X over both blocks; a padlock 3 × 4 × 2 at the crossing; two eye bolts in the frame. **`bulging`:** the leaf bowed 2 voxels into the room, chains taut. **`broken`:** the leaf lying flat on the floor in front of the doorway (16 × 2 × 30, tilted 8° by stepping), chain ends hanging from the frame, doorway open | Use: "Something on the other side wants in." |
| `run-halldoor` | `closed`, `open` | Pale wood-laminate leaf `#C9B48E`, steel frame `#7E8486`, kick plate | Lever handle, a small vision panel. `open`: leaf swung flat against the wall | Use 1, 2: `rattle`, "The door is stuck!"; use 3 → `open` |
| `run-medcabinet` | `{n,e,s,w}` | White enamel `#ECECE6`, a mirror front `#A8B4B8` with a streak, a small red cross | Box 12 × 12 × 4 at eye height on the wall (bottom of the upper block), hinge pins | Breakable in 1 s; drops `game:bandage-clean` (restocked on reset) |

**Props** (floor tiles; `{n,e,s,w}` facing unless noted):

| Code | Parts | Texture | Shape (voxels) | Collision |
|---|---|---|---|---|
| `run-gurney` | `head`, `foot` | Mattress sheet `#E6E6E0`, frame chrome `#B8BCC0`, black wheels | Mattress 14 × 3 × 30 at y 9–12 spanning both blocks; side rails 1 × 1 tubes on posts at y 12–16 (one side down); 4 legs 1 × 9 × 1; castors 3 × 3 × 2 | 0.8 high (vault it at a sprint-jump) |
| `run-wheelchair` | | Black vinyl seat, chrome frame, grey tyres | Seat 12 × 1 × 11 at y 7; back 12 × 8 × 1; two wheels 1 × 14 × 14 (stepped disc) on axles; castors; footplates | 0.9 |
| `run-ivstand` | | Chrome pole, clear bag `#DDEEEE` at 60 % alpha | Pole 1 × 16 × 1; hooks 3 × 1 × 1 at the top; 5-arm base 12 × 1 × 12 star; a bag 3 × 5 × 1 on a hook | 0.3 × 1 × 0.3 |
| `run-chairs` | | Moulded plastic, faded teal `#5E8C8A`, steel beam | Two seats on one beam: each seat 6 × 1 × 6, back 6 × 6 × 1, beam 14 × 1 × 2, 2 legs | 0.9 |
| `run-crashcart` | | Red `#B82820` drawer cart, drawer lines, yellow labels, defib box `#3A3A3A` | Body 12 × 13 × 10; 5 drawer handles 6 × 1 × 1 (3D); top rail 1 × 1 tubes; castors | 1.0 |
| `run-shelf` | `standing-lower`, `standing-upper`, `fallen-a`, `fallen-b` | Blue powder-coat steel `#2E5C9A`; cardboard boxes `#A07A4A` | `standing`: a frame 14 × 32 × 6 against the wall, 4 shelves 14 × 1 × 6, boxes on them. `fallen`: the same lying on its side across two blocks, 32 × 6 × 14, boxes spilled 4 × 3 × 4 beside | Standing: full. Fallen: **0.9** (jump it) |
| `run-toycar` | | Red and yellow plastic, black wheels | 6 × 3 × 4 body, 4 wheels 1 × 2 × 2 | none (walk-through; trip) |
| `run-boxes` | | Brown cardboard, tape | Two boxes 5 × 4 × 5 and 4 × 3 × 4 | none (trip) |
| `run-cord` | `ns` / `we` | Orange extension cord `#E07020`, black plug | 1 × 1 × 16 cord snaking ±1 voxel, a plug 2 × 2 × 3 | none (trip) |
| `run-sheets` | | Rumpled white sheet `#E8E6E0` with shadow folds | Low mound 1–2 voxels in stepped folds over 14 × 14 | none |
| `run-remains` | | Torn khaki backpack, one sneaker, a dark smear decal on the floor plate | Backpack 6 × 6 × 4 slumped, sneaker 3 × 2 × 6, a plate 14 × 0.2 × 10 | none. Drops `game:cloth-plain`, sometimes `wanderernote` |
| `run-tray` | | Steel kidney dish | Dish 6 × 1 × 3 on a stool 6 × 8 × 6; the item shown on it (an energy bar or almond bottle) | Breaks in 0.2 s; drops `run-energybar` or `backrooms:almondwater` |
| `run-bedside` | | Pale laminate `#D8CDB4` | Box 12 × 14 × 12, a drawer front with a 3D handle 4 × 1 × 1, a cupboard door | Breaks in 1 s; drops 1 Almond Water and 1–2 Energy Bars |
| `run-curtain` | `lower`, `upper`, axis | Pale green fabric `#9CC2A8` | Pleats: 8 alternating 2-voxel folds offset ±1, 16 × 30 × 2 over two blocks, hooks on a 1 × 1 rail at the ceiling | none |
| `run-safeshelf` | | White wire shelving | 14 × 16 × 5 with 3 shelves; bottles and bars on them | Breaks; drops 1 Almond Water and 1–2 Energy Bars |
| `run-safecot` | | Grey blanket, steel frame | 14 × 6 × 30 over two blocks | 0.5 |
| `run-debris` | | Broken ceiling tile, dust | Shards 3–6 voxels, a bent T-bar | none (trip) |

### 7.3 Item

`run-energybar`:
- Food: satiety 160, `Grain`, stack 16. Class `ItemEnergyBar` gives the second wind (section 5.5).
- Texture 32 px: silver-blue foil wrapper `#9AAAC0` with an orange stripe `#E07A20`, a crimped end, "ENERGY" in 3-px
  caps.
- Item shape: bar 10 × 2 × 4 voxels with crimped ends 1 × 2 × 4 (stepped).

### 7.4 Sounds

Synthesised in `gen_run.py`, which imports `band`, `reverb`, `vowel`, `seconds` and `RATE` from
`gen_entity_sounds.py`, as `gen_level_sounds.py` does.

| File | Length | Character |
|---|---|---|
| `ambient/run/alarm.ogg` | 8.0 s loop | Hospital emergency alarm: a two-tone square-ish wave, 880 Hz / 659 Hz, 0.5 s each, band-limited 400–3500 Hz through a cheap ceiling speaker; long-corridor reverb (RT60 1.4 s, slap echo at 60 ms). Harsh. Seamless loop |
| `ambient/run/alarm-far.ogg` | 8.0 s loop | The same, heavily low-passed (≤ 700 Hz), muffled as if in the walls. Before the break, and in the safe zone |
| `ambient/run/horde.ogg` | 6.0 s loop | The horde: 20–30 claw and foot impacts a second on vinyl, low growl bed (60–120 Hz with an "oo" formant), 2–3 Hound barks, 1–2 shrieks at 2–4 kHz, moth flutter (noise at 25 Hz AM). Positional, range 64 |
| `ambient/run/safezone.ogg` | 10.0 s loop | Quiet room tone: ventilation (120 Hz + airy noise), the alarm a ghost far off (`alarm-far` at −20 dB) |
| `effect/run/bang1.ogg`, `bang2.ogg`, `bang3.ogg` | 0.9 s each | A heavy blow on a steel door, chain rattle tail |
| `effect/run/doorbreak.ogg` | 2.2 s | Tearing metal, a chain snapping (ping and rattle), the door slamming onto the floor, a roar swelling |
| `effect/run/slam.ogg` | 1.2 s | A heavy door slamming shut, boom and latch |
| `effect/run/rattle.ogg` | 0.7 s | A stuck door handle yanked, latch clacking |
| `effect/run/swing.ogg` | 0.8 s | A door flung open, banging against its stop |
| `effect/run/topple.ogg` | 1.4 s | Steel shelving tipping and crashing, boxes spilling |
| `effect/run/signhiss.ogg` | 3.0 s loop | Arcing electrical buzz, crackles, a rising whine |
| `effect/run/signburst.ogg` | 1.6 s | Pop, glass shatter, a whoosh of flame |
| `effect/run/ventburst.ogg` | 1.0 s | Grille clang, a thud of something landing |
| `effect/run/heartbeat.ogg` | 2.0 s loop | Heart at 120 bpm (lub-dub, 40–60 Hz thumps). Pitched up for "within 10" |
| `effect/run/trip.ogg` | 0.5 s | A scuff and a stumbling thump |

Fire, footsteps and Hound barks are vanilla or the mod's own.

### 7.5 Lang keys (English)

| Key | Text |
|---|---|
| `level-14` | Level !: Run For Your Life! |
| `levelhint-14` | Run. Don't stop. A door with a turn beside it is not the way out. |
| `level-141` | The Safe Zone |
| `levelhint-141` | Please take a break before you continue running. |
| `run-arrive` | The door slams behind you. On its inside, a huge red exclamation mark. |
| `run-stuck` | The door is stuck! |
| `run-locked` | Locked. |
| `run-marked` | It won't budge. |
| `run-chained` | Something on the other side wants in. |
| `run-fake` | An empty room. This isn't the way out. |
| `run-escaped` | No turn either side. This was the real exit. The Backrooms will never send you there again. |
| `run-ranout` | You have run this hall before. The door lets you out somewhere else. |
| `run-full` | The door won't open. Someone else is running. |
| `run-rumble` | The walls shudder. You can't stay here much longer. |
| `run-caught` | was caught by the horde |
| `waypoint-runexit` | The way out of Level ! |
| `note-run` | Don't take the door if the hall turns beside it. The real one is at a dead end. Don't stop. They're still there. |
| `item-run-energybar` | Energy Bar |
| `itemdesc-run-energybar` | Dense, sweet, and gone in three bites. Keeps you running a little longer. |
| `block-run-wall-*` | Hospital Wall |
| `block-run-wall-beacon-*` | Emergency Beacon |
| `block-run-floor-*` | Vinyl Floor |
| `block-run-ceiling-*` | Ceiling Tile (vent variants: Air Vent) |
| `block-run-exitsign-*` | EXIT Sign |
| `block-run-sidedoor-*` | Steel Door |
| `block-run-exitdoor-*` | Exit Door |
| `block-run-chaineddoor-*` | Chained Door |
| `block-run-halldoor-*` | Hospital Door |
| `block-run-medcabinet-*` | Medicine Cabinet |
| `block-run-gurney-*` | Gurney |
| `block-run-wheelchair-*` | Wheelchair |
| `block-run-ivstand-*` | IV Stand |
| `block-run-chairs-*` | Waiting Room Chairs |
| `block-run-crashcart-*` | Crash Cart |
| `block-run-shelf-*` | Steel Shelving |
| `block-run-toycar-*` | Toy Car |
| `block-run-boxes-*` | Boxes |
| `block-run-cord-*` | Extension Cord |
| `block-run-sheets-*` | Bedsheets |
| `block-run-remains-*` | A Runner's Remains |
| `block-run-tray-*` | Supply Tray |
| `block-run-bedside-*` | Bedside Table |
| `block-run-curtain-*` | Privacy Curtain |
| `block-run-safeshelf-*` | Shelf |
| `block-run-safecot-*` | Cot |
| `block-run-debris-*` | Fallen Ceiling |
| `block-run-safelight-*` | Ceiling Light |
| `block-run-safewall-*` | Safe Zone Wall |

---

## 8. Code plan

**New files (the level's own, named per `CONTRACT.md`):**

| File | What |
|---|---|
| `src/Worldgen/WorldLayout.LevelRun.cs` (stub exists) | Region constants (17 × 17); `RunLanePlan` and its `PlanCache`; `PlanRunLane(lane)` (start room, centreline with doglegs, walls, doors, signs, obstacles by third, events, safe zone, hole, exit); `BuildLevelRun` copies the plan; `RunEdge` open; `RunArrivalCell`, `IsRunArrivalSpot`, `RunArrivalHeight`; `RunTemperature`, `RunStability`; `RunWalkThrough`. **Queries for `RunSystem`:** `RunLaneOf(x, z)`, `RunCentre(lane, s)` → (x, z), `RunProgress(lane, x, z)` → s, `RunRacingLine(lane)`, `RunEvents(lane)`, `RunExitDestination(lane)`, `RunSafeSpan(lane)`, `RunStartRoom(lane)` |
| `src/Worldgen/WorldGenerator.Run.cs` | `InitRun` (block ids); the column builder for Level ! tiles: floor, wall faces with rail or beacon by `Pier`, doors lower and upper, Grand air, signs in the top air block, ceiling kinds, the antechamber void |
| `src/Regions/RunChase.cs` | The pure chase model (front, gap, speeds, safe-zone hold, catch), no game dependencies |
| `src/Regions/RunSystem.cs` | Server: runs, lanes, timeline, events (block swaps and undo), presentation entities (puppeting), catching, lane reset, `ranOut`, persistence, debug commands. Client: alarm loops, horde emitter, heartbeat, beacon animation, the fog pulse (via a player attribute `backrooms:run`, with phase and gap) |
| `src/Regions/RunBlocks.cs` | `BlockEntityRunBeacon`; `ItemEnergyBar`; the threshold kinds `runentry` / `runexit` / `runfake` / `runmarked` / `runhall` / `runchained` |
| `tools/gen_run.py` | Every asset in section 7 |

**Hooks in shared code** (small edits in Level !'s reserved blocks only):

| File | Change |
|---|---|
| `ThresholdNetwork.Walked` | Level 2 `RunFalseWall` (rel 0.5–2.5) → one-way into Level !. `RunLevel` `RunHole` (rel < −1.5) → one-way Level 8 (`FindArrival(8)` near the 9th Road) |
| `ThresholdNetwork.Used` | `runentry` (one-way into a lane's start room; for `ranOut` players, another place in the current level); `runexit` (one-way to the lane's destination, with the marked door left at the arrival) |
| `ThresholdSystem` | `Passage` gains `ArrivalBlock` (a block code placed at the arrival instead of the thin spot: the marked door). Busy-lane redirect and per-person lanes for groups through a `RunSystem` call |
| `WorldLayout.Reality.FindArrival` | Uses `RunArrivalCell` and `IsRunArrivalSpot` (the scaffolding's hook) |
| `WorldLayout.Level1.cs`, `Level2.cs`, `Level37.cs` | The three entrance features, each with its own salt; Level 37's red corridor reuses `CarveDryCorridor` with `RunFloor` and an EXIT door at its end |
| `MenaceSystem.Rate` | `RunLevel → Safe` |
| `Danger.OfLevel` | `RunLevel => 0.9` |
| `Rewards` | Skip `backrooms:horde` |
| `WandererSystem` | Never in Level ! |
| `AtmosphereSystem` | `Levels[14]`, the safe-zone override and title 141, the alarm pulse |
| `WorldLighting` | Nothing new (the default band) |
| `BackroomsMapLayer`, `MapColors` | Colours |
| `SalvageSystem` | Level ! structure unbreakable |
| `gen_guide.py`, `README.md` | Phase 3 |

**Harness (`tools/mapgen`):**

| Mode | What it does |
|---|---|
| `run <lane>` | A PNG of a lane's plan, with signs, doors, events and the racing line |
| `runstats` | For all 17 lanes: running length (target 505–535), BFS from the hallway door to the true exit, the obstacle rules (≤ 3 of 5 blocked, overlapping gaps, clear zones), the longest dark stretch (≤ 32, or 40 in the last third), sign count, fake exits at both doglegs, safe zone and hole counts (about 1 in 5 and 1 in 3), start-room layout check |
| `runsim` | `RunChase` against scripted runners. Clean sprint: never caught. Sprint with 3 two-second mistakes: survives with a gap above 10. 5 mistakes: caught in the last third. Walking: caught in under 25 s. Standing: caught in about 8 s. Printed for Low, Normal and High |
| `regions`, `links` | 60/60 arrivals in start rooms; every new threshold resolves and survives save and load |
| Layout hash | Levels 0, 3–11, 13 byte-identical; 1, 2 and 37 differ only by the new entrance features |

**Headless server** (port 42474, own data path in the scratchpad):
- `/backrooms tp !` and a scripted run with a test target (`backrooms:testTarget`) moved along the centreline at
  fractions of `S`. Check the break time, the front, being caught, an escape, a lane reset (every swap undone), and
  group separation with two test players.
- `/backrooms dump` of a start room, a dog-leg with its fake exit, a safe zone and the exit, rendered with the
  scratchpad renderer (`runcam.py`).
- **Measure `S`:** sprint a test player 100 blocks on the hallway floor (client, or the server's physics with
  `Controls.Sprint`) and set `RunRows` if it is far from 5.8.

**Order of work:**
1. Layout and assets, with no runtime (walk the hallway).
2. Thresholds in and out.
3. `RunChase` with `runsim`.
4. `RunSystem` timeline, front and catching.
5. Events.
6. Safe zone, hole and polish.

**Risks:**

| Risk | Plan |
|---|---|
| **Puppeted entities may stutter** in a client | Test in phase 4 first; fallback is `AiTaskHorde` (straight-line pathing with the speed set every tick) |
| **Chunk generation at a sprint** | A lane is 16 chunks long; the server generates ahead within view distance. Preload the next 3 chunks along the centreline each second during a run |
| **The alarm is loud by design** | It follows the ambient volume slider. Its peak is set 3 dB under the loudest sound in the mod |

---

## 9. Decisions for the user

1. **Length.** **Recommended:** 15 hallway cells, about **520 blocks, 1½ minutes** at a sprint (1:35–1:45 with the
   course). Alternative: 20 cells, about 2 minutes.
2. **One hallway per runner.** **Recommended:** 17 parallel lanes, so players who enter together are separated, as
   canon says. Alternative: one shared hallway, where friends run (and die) together.
3. **The chase as a rubber band**: a virtual front at 0.90 S (0.94 in the last third) that keeps pace out of sight
   once 40 blocks behind. **Recommended**, as canon's "adapt to your running" and "they are still near". The
   alternative is ordinary pathing entities, which the hallway's obstacles would trap and a sprinter would leave
   behind.
4. **Caught means death within seconds** (pinned, then torn apart). **Recommended**, per canon.
5. **Escape once, and never again.** **Recommended:** after escaping, every way in leads that player somewhere else
   in their current level.
6. **Where the true exit leads**, fixed per lane: Level 1 (9 lanes), Level 4 (5), The End (3). **Recommended**,
   agreed with the End plan. One-way, leaving a red "!" door that is now an entrance for others.
7. **Entrances.** **Recommended:** Level 1's door that shouldn't be there (1 cell in 300), Level 2's wall that
   wasn't there (1 in 250), Level 37's red corridor (1 dry corridor in 5), and the marked arrival doors. All one-way.
8. **Optional extra entrances.** A Level 4 elevator with a red "!", and a Hub door. **Recommended:** the Hub door if
   the Hub plan wants it; skip the elevator.
9. **The safe zone** (blue, Checkpoint rules) in 1 lane in 5. **Recommended:** include.
10. **Events.** **Recommended:** all of section 4.3: swinging doors, toppling shelves, dented doors, vent drops, sign
    bursts with a wall of fire, trip props, Clumps, and holes to Level 8 in 1 lane in 3. A hole is a way out at the
    cost of the run.
11. **New entity.** Partygoers are in canon and in *Escape the Backrooms*' horde. **Recommended:** not now; the horde
    uses the mod's own entities.
12. **The Energy Bar's second wind** (+12 % speed for 30 s). **Recommended:** yes. It gives canon's supplies a
    purpose in a game without stamina.
13. **Difficulty from the *Backrooms entities* setting** (front speed and break time, section 4.2).
    **Recommended:** yes.

---

## 10. Handbook text (`gen_guide.py`)

**For "The Levels":**

> **Level !, Run For Your Life!** Not a ring: you are taken there, by a red EXIT door where no door should be
> (Level 1), a dead end that wasn't there a moment ago (Level 2), or a corridor of the Poolrooms that turns red. The
> door slams behind you. A hospital room in red light; something hammering at a chained door; an alarm. Take what is
> in the bedside table, and go: the hallway door sticks. Then **run**, and don't stop. The hallway is long and lit
> only by EXIT signs. Swerve round the beds and chairs, jump the fallen shelving, and don't sprint over small things
> in the dark. The horde behind you never tires: it falls back while you keep running, and catches you the moment you
> don't. A door with a turn in the hall beside it is not the way out. The real exit is a dead end with no turn either
> side, and it leads somewhere safe. Escape once, and the Backrooms will never send you there again. A blue stretch
> of hall, if you find one, is the Safe Zone: rest, eat, and go before the walls shudder.

**For "Ways Between Levels":** the rows of section 5.3.

**For "Food and Water":**

> **[Energy Bars](item-backrooms:run-energybar):** only in Level !: the bedside table, trays in the doorways, the
> Safe Zone's shelves. Eating one gives you a second wind, a little more speed for half a minute.

**For "What Lives Here":**

> **The horde (Level !).** Hounds, Skin-Stealers, Smilers, rats and moths, all running at the same speed, which is
> almost yours. It can't be fought off and it can't be outrun for long by anyone who stops. It doesn't enter the Safe
> Zone.

---

## Manifest changes (phase 2)

*Code agent, 2026-10-07.* These are **the exact block codes the C# asks for** (`WorldGenerator.Run.cs`, `RunSystem.cs`).
They replace the shorthand of section 7.2 where it differs. Sides are the mod's words `north|east|south|west` (as
`detail_kit.SIDES`), not n/e/s/w. Variant groups are listed in order, so the code is `base-<g1>-<g2>-...`.
`side` on a wall-mounted or door block is **the face that looks into the room or hall the player stands in**; on a
prop it is the usual `detail_kit.prop` facing (rotateY by side, the same as every other prop).

| Code (groups) | Notes |
|---|---|
| `run-wall-plain` | Cube |
| `run-wall-rail-{side}` | The crash rail on face `side`. Used at rel 1 (the lowest wall block) only |
| `run-wall-beacon-{lit,off}-{side}` | Wall cube with the beacon on face `side`, at rel 3. **`lit`** is the one placed: `entityClass: "BackroomsRunBeacon"`, glow on the dome, no `lightHsv`. **`off`** is its dark look, which the block entity draws (code found by replacing `-lit-` with `-off-`) |
| `run-floor-{vinyl,scuffed,cracked,safe}` | Cubes |
| `run-floor-border-{side}` | Vinyl with the charcoal-blue band (8 px) along edge `side` (the wall side) |
| `run-ceiling-{tile,paneldead,vent,ventburst}` | Cubes (vent louvres recessed into the underside) |
| `run-exitsign-{lit,dim,bright,flicker,dead}-{ns,we}` | Hanging sign in the top air block. `ns`: its two faces look north and south (the board spans west-east); `we`: faces look west and east. Light: lit `[0,7,9]`, dim `[0,7,5]`, bright `[0,7,12]`, flicker `[0,7,9]`, dead none. **`flicker`**: `entityClass: "BackroomsFlicker"`, `attributes: { offBlock: "backrooms:run-exitsign-dead-<axis>" }` (per type) |
| `run-exitsign-wall-{dim,bright}-{side}` | On a wall block at rel 3, over a door, face `side`. dim `[0,7,5]`, bright `[0,7,12]` |
| `run-safelight` | Ceiling block, light `[42,4,14]` |
| `run-safewall-plain`; `run-safewall-sign-{l,r}-{side}` | The sign is two blocks wide (left and right halves as seen facing it), at rel 2 |
| `run-void` | Matte black cube (antechamber and closet walls, the open fake exit's back) |
| `run-sidedoor-{closed,dented,open}-{lower,upper}-{side}` | In the wall. **`open`** is the empty frame (black beyond, no leaf). Indestructible. Behaviour `BackroomsThreshold` with `kind: "runlocked"` on `closed` and `dented` |
| `run-doorleaf-{lower,upper}-{side}` | The swung-open leaf, placed in the **hall tile** in front of an opened side door: a slab 16 wide × 2 thick standing on edge `side` of that tile (collision on the slab only) |
| `run-exitdoor-{fake,fakeopen,true,marked,entry}-{lower,upper}-{side}` | Kinds (`behaviorsByType`): fake → `runfake`, true → `runexit`, marked → `runmarked`, entry → `runentry`; fakeopen has none (frame, leaf swung into the closet) |
| `run-chaineddoor-{intact,bulging,broken}-{lower,upper}-{side}` | Kind `runchained` (intact, bulging). `broken`: the doorway open, the leaf lying in the lower block |
| `run-halldoor-{closed,open}-{lower,upper}-{side}` | Kind `runhall` on `closed` |
| `run-medcabinet-{side}` | Wall block at rel 2 with the cabinet on face `side`; breakable, drops `game:bandage-clean` |
| Props, `PropTable` style (`code[-kind]-{side}`) | `run-gurney-{head,foot}-{side}` (head first, like `hospitalbed`), `run-wheelchair-{side}`, `run-ivstand-{side}`, `run-chairs-{side}`, `run-crashcart-{side}`, `run-shelf-{a,b}-{side}` (fallen, two parts), `run-toycar-{side}`, `run-boxes-{side}`, `run-cord-{side}`, `run-sheets-{side}`, `run-remains-{side}`, `run-tray-{bar,almond}-{side}`, `run-bedside-{side}`, `run-safeshelf-{side}`, `run-safecot-{head,foot}-{side}`, `run-debris-{side}` |
| Two-high props (my builder) | `run-shelfstanding-{lower,upper}-{side}`, `run-curtain-{lower,upper}-{side}` |
| Item | `run-energybar`, `class: "BackroomsEnergyBar"` (registered by `RunSystem`) |

**Drops.** `run-remains`: `game:cloth-plain`, plus `backrooms:hub-key-run` with chance 0.15 (LINKS.md: each level
places its own Hub key; the Hub agent's assets create the item). `run-tray-bar`: one `run-energybar`;
`run-tray-almond`: one `backrooms:almondwater`. `run-bedside`: 1 Almond Water and 1–2 Energy Bars. `run-safeshelf`:
1 Almond Water and 1–2 Energy Bars.

**Collision** as in section 7.2: gurney 0.8 high, wheelchair and chairs 0.9, fallen shelf 0.9, toy car, boxes, cord,
sheets, debris and remains none (walk through), crash cart, bedside and standing shelf full.

**Sounds** as section 7.4, at `sounds/ambient/run/` and `sounds/effect/run/`, with the same names.

**Code agent, later the same day.** The C# now uses the codes `tools/gen_run.py` actually writes, where they differ
from the table above: `run-wall-void`, `run-ceiling-panel-dead`, `run-ceiling-vent-burst`,
`run-falsewall-{lower,upper}`, `run-wall-beacon-{lit,dark}-*` (the block entity class is registered under both
`RunBeacon` and `BackroomsRunBeacon`), `run-safewall-sign-{side}-{l,r}`, `run-shelf-fallen-{a,b}-*`,
`run-shelf-standing-{lower,upper}-*`, `run-curtain-{lower,middle,upper,top}-{ns,we}`, `run-sidedoor-leaf-*` (with the
door's own side), `run-exitdoor-fake-open-*`, `run-exitdoor-arrival-*` (placed on the arrival tile), and
`run-tray-{bar,water}-*`. The doors that lead nowhere keep `BackroomsThreshold` with kinds `runhall`, `runchained`,
`runmarked`, `runside`, `runfake`: `ThresholdSystem.Use` hands those to `RunSystem.UseDoor` before the network.
**Lang keys added by the code agent** (keep them): `level-1401`, `levelhint-1401` (the Safe Zone's title key, from
the level's own range 1401-1499) and `run-fell`.
**Still wanted from the assets:** `run-remains` drops `backrooms:hub-key-run` with chance 0.15 (LINKS.md: each level
places its own Hub key).

**Asset agent, final (2026-10-07).** `tools/gen_run.py` now writes exactly the codes the C# references (checked by
expanding every blocktype's variants against every `run-*` string in `src/`: nothing missing). The codes are frozen
here; please don't rename further without a note. What each one is:

- `run-exitsign-{lit,dim,bright,flicker,off,dead}-{ns,we}`: **`ns` = its two faces look north and south** (the board
  spans west-east), `we` = they look west and east, as in the table above. `flicker` carries `BackroomsFlicker` with
  `offBlock: run-exitsign-off-<axis>` (an extra unlit state; `dead` is the burst, sooty and cracked).
- `run-exitsign-wall-{dim,lit,bright,concrete}-{side}` and `run-medcabinet-{side}` are **wall blocks** (hospital paint)
  with the sign / cabinet on face `side`, at rel 3 / rel 2. Breaking the cabinet removes that wall block.
  **`concrete`** is the bright sign on a Level 1 concrete wall cube: suggested for `Unders.RunEntrance` rel 3 in
  Level 1, where `bright` would put a white hospital block in a concrete wall.
- `run-wall-beacon-{lit,dark}-{side}`: `entityClass: BackroomsRunBeacon` on `lit` only; `dark` is just its mesh.
- `run-wall-void` (matte black cube). Extras available: `run-wall-base` (cove base, no rail),
  `run-wall-railcorner-{side}` (rails on `side` and the next face clockwise: outside corners at the doglegs),
  `run-safewall-base`.
- `run-falsewall-{lower,upper}` (no side): no collision; `lower` has a thread of red light round its foot on all four
  faces and `lightHsv [0,7,3]`.
- `run-curtain-{lower,middle,upper,top}-{we,ns}` for rel 1-4: `we` = the curtain runs west-east (faces look north and
  south); `top` carries the mesh band and the ceiling track.
- `run-shelf-{standing-lower,standing-upper,fallen-a,fallen-b}-{side}`: standing has its back to the wall, front to
  `side`; **fallen-b lies one tile toward `side` from fallen-a** (the shelf's base at a, its top at b), as RunSystem's
  topple places them. Worldgen-placed fallen shelves (PropTable, kinds `fallen-a`, `fallen-b`) need b at `Step(side)`
  of a too. Collision: standing full, fallen 0.875 high and 0.4 wide.
- `run-sidedoor-leaf-{lower,upper}-{side}`: in the hall tile in front of the door, **the door's own side**; the leaf
  stands along that tile's edge at the door's hinge side (model x 0-2 for side north), collision a 0.15 slab there.
- `run-exitdoor-arrival-{lower,upper}-{side}`: flush on a wall's surface, in the air block in front of it, facing
  `side`, the red "!" on its face; collision a slab at the back. All other doors are set into the wall, facing `side`.
- Behaviours: all `BackroomsThreshold`: sidedoor closed/dented `runside`; exitdoor true `runexit`, fake `runfake`,
  marked `runmarked`, entry and arrival `runentry`; chaineddoor intact/bulging `runchained`; halldoor closed `runhall`.
  open / fake-open / broken / leaf states have none.
- Drops (in the JSON): remains `game:cloth-plain`, Almond Water 0.2, `hub-key-run` 0.15; tray-bar one Energy Bar,
  tray-water one Almond Water; bedside and safeshelf 1 Almond Water + 1.5 ± 0.5 Energy Bars; medcabinet one clean bandage.
  **Caveat for the code agent:** every Level ! block's `FirstCodePart()` is `run`, so `Breakdown.KindOf` (and anything
  keyed by the first code part) treats every non-threshold `run-*` block as Structure and `Breakdown.Apply` replaces the
  JSON drops, tier and resistance: as it stands the props lose their loot and the walls break like concrete. Special-case
  `run-` by `Code.Path` (props salvage with their own drops; walls, floors, ceilings and signs fixed).
- Lang: `level-1401` / `levelhint-1401` (the Safe Zone; `level-141` dropped), `run-fell` given text. Names for every block.
- Textures are 32 px except the Safe Zone sign plate (64 px a block, so its four lines can be read). The IV bag is opaque.
