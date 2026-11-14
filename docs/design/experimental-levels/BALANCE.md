# The experimental levels: balance review (2026-11-01)

(Updated 2026-11-14, the review: the figures that later rounds changed are corrected in place and say so; Levels 14 and 47 were added after this review and are not in it.)

The eight experimental levels (73, the Basement, 52, 31, 36, 120, 15, 23) as they stand at 0.700.0-pre.3 (`e3950fc3`), read
against the released game's progression rules: **lethality and armour by depth, ore only in Level 8, scarcity by survival
class** (progression decisions 2, 5, 18-21), one kind of menacing thing at a time in Classes 0-2 and two in 3-5 (entity
decision 29), earlier-to-later shortcuts about a quarter as common as in layout 11 and no new one-way ways down (decision 20).
Branch `exp/balance`. Lang text and the levels' own files (layouts, generators, region systems) were not touched: what they
need is under "Proposed" and "For the lead" below.

**How it was measured** (seed 12345, Normal setting, full-size world):
- `/backrooms ratecheck <id> <band> 100`: the director's rolls, bodies and distant sounds per real hour in a band (what the
  band would hold; a level whose map is all Safe never sees them).
- `/backrooms armourtest <hunter> <level>`: the mean blow on a 15-health player, unarmoured and in four sets, and blows to kill.
- `tools/aitest/walk.py`: a straw-dummy walker for 25 real minutes (felt bodies per hour, time to the first encounter).
  Headless creatures think but do not walk, so it measures what is sent, not deaths.
- A scratch copy of the mapgen harness (`%TEMP%/backrooms-lore/work-balance/boxdens`, not committed): supply boxes per 1000
  walkable tiles in 7 x 7 cells round six arrivals of every level. Boxes a level's generator places rather than its tiles
  (Level 52's upper storeys, Level 73's castle) are not in it.
- Code reading for everything else (loot tables, entity JSON, the region systems).

## At a glance

| Level | Lore class | Code class (food x) | Danger | Solitude | Where the director works | Commonest hunter's blow | Ways in (from) | Ways out (to) | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 73 Redlands | 5 | 5 (x0.35) | 0.9 | 0.15 | outside the castle: the edge; the hill Coran keeps now the Approach | Hound 17.6 (dead in 1) | 9 (the Gloom), 6 (deepest dark); one-way | 9 (Coran's lead); one-way | deadliest band in the game; the run made makeable (applied) |
| Basement | 2 | 2 (x1, now x0.25) | 0.3 | 1.3 | Cellar heartland, Flood approach | Smiler 7.6 (2 blows) | 0, 1, 2, 4, 5 (cracked floor); one-way | 0 (climb the crack); one-way | fine; food cut to a quarter (applied); a newcomer's trap (user) |
| 52 Campus | 1 | 1 (x1) | 0 | 1.0 | nowhere (Safe) | none | 4, 11; two-way | the same doors back | a sanctuary, as the lore says; fine |
| 31 Roller Rink | 0 | 0 now (x1) | 0 | 1.0 | nowhere (Safe) | none | 2, 3, 6; two-way | 9/10/11 (revolving door), 0 (skates); one-way | infinite free food next to Class 3-4 levels (proposed) |
| 36 Airport | 1 | 1 (x1) | 0.35 | 1.0, now 2.5 | blackouts and dark back of house (edge) | Hound 9.1 (1.6 blows) | 9, 11; two-way | 11, 9, 37, 3999, 188, 10 (flights), 37 (sink); one-way | blackouts too busy for "rare" (applied); a food hoard off Level 9 (user) |
| 120 Broken Servos | 2 | 2 (x1) | 0.3 | 1.0 | nowhere: Misglitches where players died, the voids' Smilers | Misglitch 6.3 at tier 2 | 4 (SERVER ROOM); two-way | 4; one-way | fine; a quiet copper mine |
| 15 Futuristic Halls | 1 | 1 (x1) | 0.3 | 3.0 | the dark wings (Approach) | Robo-Man 7.6 (2 blows) | 10 (white wall), 3 (door); one-way | 3, 4, 11; one-way | fine |
| 23 Petrified Garden | 4 | 4 (x0.5) | 0.55 | 0.9 | forest heart, glow rooms approach, ruins edge; Seedling safe | Hound 10.4 (1.4 blows) | 37 (hollow trees); one-way (Seedling's tree two-way) | 7 (the well); one-way | fine; water too easy for Class 4 (user) |

Released levels for comparison (same measurements): Level 9's approach 103 and edge 334 bodies an hour, Hound 15.8 (0.9
blows); Level Fun's approach 79, Smiler 14.7; Level 3999's Blackout 122, Smiler 12.5; Level 3's approach 69, Smiler 7.6 (2.0
blows); Level 1's heartland 8.6 and approach 23.5; Level 4's approach 21; Level 6's approach 10; the Poolrooms' heartland 2.9.

## Level 73, "The Redlands"

- **Class and danger.** Wikidot's Survival Difficulty 5; code: class 5, danger 0.9 (as Level Fun and Level !), solitude 0.15
  (the busiest in the game; Fun 0.4, Level 9 0.3), two kinds at once, a cap of five menacing things (3, +1 at danger 0.5, +1 at
  0.8). Safe within the walls. Matches the lore and the user's "deadly outside the castle".
- **Rates.** The edge band rolls **814 bodies an hour** (Level 9's edge 334, Fun's approach 79), the approach band 208. The
  walker, put down at an arrival and walking loops on the island, met **70 encounters in its first 10 minutes** (about 420 felt
  an hour, one every 9 s). A Hound pack (3-5) at danger 0.9 hits 17.6 a blow (dead in one unarmoured, 1.8 blows in leather, 2.2
  in bronze, 7.5 in iron plate) and runs at 0.079 against a sprint's 0.05. The arrival is 60-120 blocks from the gate. With a
  body every 9 s and nearly half of the edge's bodies hunters, the decision's "short run so a fast player can make the door"
  (lore/DECISIONS.md) is luck, not speed: Coran walks a ring 36-75 blocks out and hears 40 blocks round himself, so an arrival
  on the far side of the castle from him has no help.
- **Coran** (`l73-coran`): invulnerable, not saved with the world, never hostile; hears hostiles within 40 blocks of himself,
  outside the walls and within 140 of the castle's middle; a strike of 1000 on everything within 3.8 blocks (any of the roster
  dies; Smilers are immortal and only withdraw), nothing between strikes but a 450 ms swing; no bounty for his kills. Strong,
  and he has to be: he is the level's only counter. His lead out needs 4 game hours asleep in the keep. Fine.
- **Loot.** Three sealed supply boxes and crates in the store-room (never torn), crates in the attic, backpacks on the fields
  (one in about 3000 land tiles). The table of plenty (24 places, 600 satiety and 700 hydration each, set again every 4 game
  hours) is eaten at the table, so it cannot be stockpiled; two bath barrels a floor give clean water without end. **Deep
  caches:** at danger 0.9 every backrooms block that drops food, candles or gears is a cache (`Rewards.OnBrokeBlock`): 63 % its
  drops twice and 46 % an extra from the deepest pool (tin bronze bits 2-4 about one time in four, iron bits 1-3 one in nine, a
  temporal gear one in 75). The castle's 18 candelabras and its furniture are such blocks: a few bronze and iron bits in all, as
  from any cache in Levels 7-11. No ore. Not a breach for a Class 5 level (but see Level 6 below).
- **Restricted resources.** 14 real beds (a respawn point, decision 9) in the one safe building; cloth from the upholstery
  (it gave pleather before the feedback round retired it). 4 C outside, 16-22 inside; stability 0.9 outside, 1 within the walls. Fine.
- **Ways.** In: the Gloom in Level 9 (90 s in it, warned three times; about nine in the world, the nearest 6.7 km from spawn),
  Level 6's deepest dark (180 s without light; five in the world, the nearest 4.25 km). Out: Coran's lead to Level 9.
  **6 to 73 to 9** skips Levels 7 and 8 (and the only ore), but costs a class-5 run, a night's sleep and an unarmoured arrival in
  Level 9's streets: an expedition, not a shortcut, and the deep-cache bits are a handful. **9 to 73 and back to 9** is a safe
  restock loop for a Level 9 player (food eaten in place, clean water, sleep): fair for what the run costs.
- **Verdict.** Keep the class, danger, solitude and roster. **Applied:** the hill Coran keeps (within 140 blocks of the castle's
  middle, his own leash, which takes in 192 of 200 arrivals; the farthest is 159 blocks out) is the Approach band instead of the edge: the director rolls about a
  quarter as many bodies there (208 an hour against 814) and hunters are about a quarter of them instead of nearly half; still
  the busiest approach band in the game (twice Level 9's) at one-blow danger, with Coran in it. Beyond 140 blocks the island
  stays the edge.

## The Basement

- **Class and danger.** Fandom's 2/2/2 (Somewhat Difficult to Exit, Lack of Needed Resources, Decent Amount of Entities); code:
  class 2, danger 0.3 (between Level 2's 0.24 and Level 3's 0.36, so below the run floor: nothing outruns a sprint), solitude
  1.3, one kind at a time. Rates: heartland 8.5, approach 23.6 bodies an hour, Level 1's (8.6 / 23.5). Smiler 7.6 (2 blows
  unarmoured, 4.2 in leather), Wretch 7.0 (2.2), now and then a fed Skin-Stealer (13.4: one blow if it turns). Matches the lore's
  "decent amount" and the levels it is reached from.
- **Loot.** Supply-box stashes (1-2 boxes in about one Cellar cell in five) 75 % torn: 0.03 sealed and 0.22 torn per 1000
  walkable tiles (Level 0: 0.26 / 0.31; Level 4: 0.06 / 0.11). Crates mostly opened. **But the pantries** (a quarter of the small
  rooms) carry pantry shelves (1.2 canned beans, about 540 satiety each, with flour and salt), never picked over, and iceboxes:
  one pantry holds more food than ten sealed boxes, against the plan's own "no food of the level's own" and the lore's resource
  class. Workshops: cable spools (4 copper bits), tool shelves (copper tools 10-15 %), nail barrels, pipe stacks (copper and lead),
  all by hand: scrap copper, as Level 2 has (decision 13). Pry bars from junk. No ore, no bronze, no iron.
- **Water, fatigue, cold.** All its water is Foul (-150 hydration, sickness one time in two); drink only from boxes and packs.
  8 C in the Cellar, 4-5 in the Flood, 9 in the Dry Patch; stability 1 (Cellar), 0.7-0.9 (Flood), 1.15 (Dry Patch). Bedrolls in
  about half the Dry Patches. The smell of the dead: 0.5 suffocation every 5 s after 45 s beside two bodies.
- **Ways.** In: a cracked-floor patch in Levels 0, 1, 2, 4, 5 (one cell in 1500-3000; 16 in the world for seed 12345, the
  nearest 1.9 km from spawn), a fall costing about 4-6 of 15 health. Out: climbing 16 blocks up the crack's shaft, to Level 0.
  **Does the fall drop a new player into Class 2 too early?** By danger, no: 0.3, Level 1's rates. By **escape**, perhaps: the
  walls need an iron pick (`basement-wall` resistance 8, tier 3), the ladder by a crack is two blocks of sixteen, and the only
  water dehydrates. A Level 0 newcomer with an empty bag must gather a ladder's worth of placeable blocks (furniture salvage,
  rope) before thirst does its work: possible, but the likelier way out is death and the respawn. The patches are kilometres
  apart and a Lobby note ("Soft floor") warns of them, so it is rare. See "Proposed".
- **Verdict.** Director and danger fine. **Applied:** food from blocks in the Basement x0.5, cut to x0.25 in the balance fixes of 2026-11 (`ScarcitySystem.ClassScale`, the
  resource axis of its Fandom class; the pantries stay, a quarter as full). **Proposed** (user decision): a surer way out for the
  unequipped.

## Level 52, the Greenfield Campus

- **Class and danger.** Fandom class 1e, Safe; code: danger 0, band Safe everywhere, a rare harmless Faceling. Matches.
- **Loot.** Store rooms (a box one time in four, 30 % torn above the ground storey), J. Barry's warehouse (shelving, a few
  boxes), lockers and filing cabinets (brackets, notes), corridor fountains (3.5 % of corridor wall tiles, 1-3 Almond Water each,
  one time), coolers, vending machines (snack machines restock weekly), the canteen. Lodging blocks full of beds (and J.
  Turner's converted classrooms). No metal beyond brackets; no weapons or armour (the pleather chairs gave is gone with the feedback round). 10-32 C outdoors
  over the day, 21 C indoors; stability 1.1.
- **Ways.** In: an EMERGENCY EXIT in Level 4 (0.63 cells per km2 as `52links` counts it now; 0.49 at pre.3) and a high school in Level 11 (one city block in 640, 0.11 schools per km2 of city; one in 123 at pre.3); both two-way, back by the doors you came in by. Out: only those.
- **A free sanctuary?** Yes, and the lore says so. It sits beside Level 4, already the game's calm level (its heartland Safe in
  play, Facelings, camps) and Class 1, so it adds safe ground where the game already has it, not where scarcity is meant to bite:
  no level of Class 3 or more leads to it. Its beds are a respawn point beside Level 4, like Level 4's camps. Its food is weekly
  vending and one-time fountains: generous for a whole campus, but nothing to farm faster than a week. **Verdict: fine as
  built.** Its `PickedOverShare` (0.3) is left alone: its upper storeys roll their own 30 % in the generator, so changing the
  shared line alone would split the level.

## Level 31, the Roller Rink

- **Class and danger.** Wikidot's Survival Difficulty 0, "Devoid of Harmful Entities"; code: danger 0, Safe everywhere,
  docile Facelings. **Applied:** `SurvivalClass(Level31)` 0 (was the default 1; nothing reads the difference today: scarcity,
  kinds and placards are the same for 0 and 1).
- **The Coach** (`l31-coach`): invulnerable, stands still, gives one pair of skates free (+30 % walk speed on the rink's smooth
  floors, only in Level 31), marks the nearest revolving door on the map. Harmless to balance.
- **Food: the problem.** The food court's server hands every player a pizza, wings or hot dog (300-380 satiety) **every 1.5 game
  hours** (3 real minutes at the default day length), with Almond Water 60 % of the time (`L31System.ServeHours`; as measured at pre.3, since changed to 12 hours and 30 %, see P1), and its vending
  machines swap Almond Water for snacks without stock. That is 16 meals a game day, four or five times what a player eats, handed
  over as items that stack and keep: an infinite food and water farm. It is **two-way from Levels 2 and 3** (Class 3 and 4, where
  decision 21 thins food to x0.7 and x0.5) and from Level 6. Nothing else in the game feeds without limit but the Snackrooms'
  weekly restocks and Level 73's table (eaten in place, behind a class-5 run).
- **Ways.** In: a wooden door with pop music behind it in Level 2 (1.2 per km2, the nearest 1.4 km), Level 3 (0.56), Level 6
  (0.38); two-way. Out: the revolving door in one lobby in twelve (about one per 480 blocks square; one in 48 from layout 16, in every world from pre.13) to Level 9, 10 or 11, a third
  each, one-way; stealing skates, to Level 0. **2 to 31 to 10/11** skips Levels 3-9, but the released game already has that skip
  through the Hub (Levels 1 and 2's Hub doors, then the Hub's one-way door to Level 11), and far more often, so 31 adds no new
  kind of skip. What it adds: **a third of its revolving doors drop whoever takes them into Level 9 (Class 5, a Hound kills in one
  blow) without a word**, and the Coach's "lead me out" marks the nearest whatever its level.
- **Verdict.** Safe, as the lore says, but the server must not out-feed the scarcity of the levels next door. **Proposed** (the
  level's own `src/Regions/L31System.cs`, one constant): `ServeHours` 1.5 to 6 (four meals a game day, about 1360 satiety: enough
  to live on while there, nothing to carry away). For the lead: the revolving door's destination shown and said (below).

## Level 36, the Airport

- **Class and danger.** Wikidot class 1 ("0/5"), Fandom undetermined; code: class 1 (the default), danger 0.35, Safe but in a
  blackout and the dark back of house, which are the edge band: Smilers (dark only), Hounds 1-2, female Deathmoths 1-2.
  Blackouts are about 12 % of the floor (from the third superblock out). The lore: Smilers, Hounds and Deathmoths **rarely**, in
  blackouts.
- **Rates.** At the default solitude (1.0) the dark rolled **95.5 bodies an hour**, nearly 40 % hunters: Level 1's or Level
  188's edge, most of Level 3999's Blackout (122, in a danger-0.8 level whose lore makes its Blackout the dangerous part). Not
  "rare". **Applied:** solitude 2.5: 36.3 bodies an hour in the dark (61 sounds), between Level 1's approach (23.5) and Level 3999's Blackout (122). Hound 9.1 a blow (1.6 blows unarmoured), Smiler 7.6 (2.0).
  Danger 0.35 sits just under the run floor (0.36): they do not outrun a sprint, which suits a Class 1 level. The walker could not
  test the dark (it stays on the claim hall: its route needs a gate).
- **The Travel Planner** (the wanderer, site `36`): 25 health, flees, revives; sells Almond Water, crackers, candy, soda (1 rusty
  gear each), bandages, a linen sack, candles, chalk; buys circuit boards, coin mechanisms, cloth, glass, wire, paper. Camp
  Amber's and Level 3999's prices; no temporal gear. Fine.
- **Food.** One duty-free shop in eight is a snack shop of about 80 snack shelves (chips, candy, soda, crackers: about 450
  satiety a shelf, 36,000 a shop), never picked over (props are not), besides drink fridges, snack machines (weekly restock),
  food-court and lounge fridges; and at danger 0.35 every one of those is a cache (24 % double, 27 % an extra). A Snackrooms in
  every duty-free street. Class 1 by lore, so not thinned. Supply boxes (lounges' stockpiles of 2-4, Lost and Found offices, C32
  camps) are sparse: 0.06 sealed per 1000 walkable tiles. Pharmacies: about 30 brackets a shop. Lanterns at Gate C32.
- **Needs.** No sleep and no tiring (awake hours held while in the level); hunger and thirst as usual; 21 C with cold (10) and
  hot (28) concourse stretches; stability 1.05, blackouts 0.95, the Absolute Limit 0.6.
- **Ways.** In: a door under an airplane sign in Level 9's houses (0.34 per km2, the nearest 6.5 km) and Level 11's fronts (0.30);
  two-way. Out: flights to 11, 9, 37, 3999, 188, 10 (152 gates in 28 superblocks: 22, 18, 33, 25, 22 and 32), the gate's screen
  naming the level; a restroom sink to the Poolrooms. **Does a flight skip danger?** Entered only from Levels 9 and 11, every
  flight lands no deeper than that (10 and 11 are the next steps from 9; 37, 3999 and 188 are far places Level 9 and 11 players
  reach by other ways): a hub for deep players, not a way down. **A safe level to farm?** Yes: a two-way door from Level 9 (Class
  5, food x0.35) into a safe terminal of snack shops where fatigue is held. The Snackrooms are the precedent (a sanctuary of snacks
  inside Level 6), and the doors are as rare as the city's.
- **Verdict.** Blackout rate fixed (applied). The food hoard next to Level 9 is the user's call (below).

## Level 120, "Broken Servos"

- **Class and danger.** Wikidot's Survival Difficulty 2 ("the chance of stumbling upon [a Misglitch] is relatively low"); code:
  class 2, danger 0.3, band Safe, empty roster; its dangers are L120System's own: a Misglitch where a player died, and the White
  Voids' Smilers (too taken with the light to attack, as the lore has it). Pitch dark.
- **The Misglitch** (`l120-misglitch`): 20 health (28 at danger 0.3), 5 slashing at tier 2 (6.3 at danger 0.3) every 1.55 s,
  reach 2.4 (a Smiler's is 0.9), runs at 0.047 (just under a sprint) and skips 2.2 blocks toward you every 4.5 s; wakes at 6
  blocks (3.5 sneaking), to running within 18, to a held light within 16; gives up after 25 s without a hit, beyond 32 blocks of
  its home, or at a fire ward; lives 24 game hours; at most six alive within 24 blocks of a death. Killable, no drops, no bounty.
  Between a Wretch (18 health, 5.5 at tier 1) and a Neighborhood Watch (30, 6.5 at tier 2): fine for Class 2.
- **Loot.** Supply boxes in 22 % of server rooms (45 % in wrecks): 0.24 sealed and 0.08 torn per 1000 walkable tiles, Levels 3
  to 5's range. Racks, wrecks, spills, trays and terminals give scrap wire (0.3-0.7 each, ten to a copper ingot) and brackets by
  hand: the richest scrap copper of the eight. Scrap copper is not restricted (decision 13 makes it a Level 2 thing); no tin, no
  iron. No food or drink of its own (nothing to drink at all); 14-38 C by zone; stability 0.94-1.05.
- **Ways.** In: a SERVER ROOM door in Level 4's offices (0.52 per km2, the nearest 2.5 km, an M.E.G. placard beside it: "CLASS 2
  / PITCH DARK / DO NOT DIE HERE"), two-way. Out: doors back to Level 4 (one cluster in three, every hallway), one-way. Nothing to
  skip: in from and out to Level 4.
- **Verdict.** Fine: a dark, quiet copper mine beside Level 4 whose danger is the player's own death. **Proposed** (minor, the
  level's file): the cap of six Misglitches round a death down to three, so a player who keeps dying in one place does not meet
  more menacing things at once than a Class 2 level's director allows (one to three).

## Level 15, "Futuristic Halls"

- **Class and danger.** Fandom class 1 (the brief: 1-2, isolation and scarcity the threat); code: class 1, danger 0.3, solitude
  3.0, a Robo-Man now and then where the power is out (Approach): 10.2 bodies an hour in the dark, Level 6's rate. Robo-Man 7.6 a
  blow (2 blows unarmoured), 35 health (50 at 0.3), slow (no run floor). Matches.
- **Loot.** Supply boxes in storage, dorms and blank rooms (0.15 sealed, 0.15 torn per 1000 walkable tiles); storage crates never
  picked over; lockers (a little Almond Water and crackers, iron nails 0.4, brackets 0.6); `PickedOverShare` 0.5 ("devoid of
  resources"). Machines give scrap wire (0.8) and copper bits (0.4); rod presses brackets and nails; a **Robo-Man drops 3 iron
  nails and a bracket**, the best iron of the eight, but nails do not smelt: no iron for armour. A third of the corpses carry a
  glass spear (craftable from the start anyway). Dorm cots (rest 0.75), camps with sleeping bags. 20 C, 16 in the dark;
  stability 1.05 lit, 0.7-0.8 dark. Fine.
- **Ways.** In: the white wall in Level 10 (one per 14.6 km2, the nearest 7.6 km), a HIGH VOLTAGE door in Level 3 (one per 2.1
  km2, the nearest 2.6 km); one-way. Out: ESCAPE to Level 3, an office stair to Level 4, an orange pane to Level 11 (the nearest
  186 blocks from the middle); one-way. **3 to 15 to 11** skips 4-10 in a few hundred blocks, rarer than Level 3's own ways down,
  and the Hub's route to 11 exists already; 10 to 3 or 4 is later-to-earlier. The Level 3 door's rarity is the link session's
  lever.
- **Verdict.** Fine as built.

## Level 23, "The Petrified Garden"

- **Class and danger.** Wikidot's "4?", Unsafe, Medium Entity Count; code: class 4 (food x0.5), danger 0.55 (between the
  Poolrooms' 0.5 and Level 7's 0.66, the levels it lies between), solitude 0.9, two kinds at once. Rates: heartland 12.4, approach
  33.8, edge 102.5 bodies an hour (Level 3's approach is 69: a calmer Class 4, as "medium" says). Hound 10.4 (1.4 blows
  unarmoured, 3.3 in leather, 5.4 in bronze), Smiler 8.7, rats 1.7. The sentries scream (3 damage) at a phrase. Matches.
- **Loot.** Boxes at the foot of a tree in one cell in seven, in glow rooms and ruins (0.22 sealed, 0.09 torn per 1000 walkable
  tiles), Base Seedling's five; food thinned x0.5. No metal at all; wood, sticks, soil, clay and cloth from the forest. Base
  Seedling is a sanctuary (M.E.G., a camp trader, tents, a spring). **Water: every drop in the level is Clean** (600 a litre),
  puddles included: thirst is no issue in a Class 4 level whose lore gives the "steady water" to Base Seedling. The tunnels to
  Seedling carry vanilla lanterns (16 % of their wall tiles) and the camp eight more: lanterns a city trader sells for 6 gears,
  free for the taking.
- **Ways.** In: a hollow green tree in Level 37 (one per 5.2 km2 of the Poolrooms' inner part, the nearest 103 km from spawn),
  one-way; Seedling's tree two-way with one Poolrooms tree. Out: the well in the Heart of Water to Level 7's open sea, one-way.
  37 to 23 to 7 is two steps, each a class up or level: no skip worth the name at that distance.
- **Verdict.** Fine. **Proposed** (user decision): water Clean only at Base Seedling's spring and the Heart of Water, Tainted
  elsewhere; for the 23 agent: the tunnel lanterns as a level block that drops nothing (or glass), as the other levels' lights do.

## The eight together

- **The danger ladder.** The new danger values sit where their entrances are: the Basement, 120 and 15 (0.3) off Levels 0-5 and
  10; 36 (0.35, blackouts only) off 9 and 11; 23 (0.55) between 37 and 7; 73 (0.9) off 6 and 9. None is deadlier than its hosts
  but 73 from Level 6 (by design, warned three times in chat). The lethality anchors are untouched (no shared curve changed).
- **More safe space?** Yes: 52 (all of it), 31 (all), 120 (unless you die there), 36 (88 % of it), 15's lit halls, 73's castle,
  23's Seedling. Most of it is beside levels already calm (52 and 120 beside Level 4; 15 from 10) or deep and hard to reach (73,
  23). The two that change the game's pressure are **31** (a safe, fed level two-way from Levels 2 and 3) and **36** (a safe, fed,
  sleepless level two-way from Level 9). The released game's own refuges at those depths are Level 3's Sanctums (no food) and the
  Snackrooms (Level 6).
- **More easy loot?** Supply boxes are within the released range everywhere (0.03-0.24 sealed per 1000 walkable tiles against
  Level 0's 0.26 and Level 5's 1.5). The abundance is in **props, which are never picked over**: 36's snack shops, the Basement's
  pantries (now halved), 52's machines and fountains, and 31's server (infinite). Metal: no ore anywhere (decision 2 holds); scrap
  copper in 120, 15, the Basement and 31's HVAC rooms (allowed, decision 13); iron only as nails; tin bronze and iron bits only from
  Level 73's deep caches, as from any Level 7-11 cache. No armour or metal weapon is handed out anywhere.
- **The new creatures and the director's caps.** None of the four is put down by the director or counted in its caps: Coran, the
  Coach and the Planner are not menacing; Misglitches are L120System's own (up to six round a death, more than the director
  allows a Class 2 level at once: see Proposed). Level 73's packs fill the cap of five (two kinds) at once.
- **Map crowding.** The regions do not overlap (README). The hosts gain entrances: **Level 4** three kinds (52's exit 0.63 and
  120's SERVER ROOM 0.52 per km2, the Basement's crack one cell in 3000), all leading somewhere calm or back; **Level 2** two (31's
  door 1.2 per km2, the crack); **Level 3** two (15's door 0.48, 31's 0.56); **Level 9** two (36's door 0.34, the Gloom 0.22);
  **Level 11** two (52's schools 0.11, 36's door 0.30); Levels 0, 1, 5, 6, 10 and 37 one each. All are kilometres apart, rarer than
  layout 12's quartered shortcuts; the link session owns their numbers.
- **Warnings.** Of the ways into a more dangerous level, Level 120's door has a placard and 36's gates name their level; 31's
  revolving doors to Level 9, 15's ESCAPE to Level 3 and the Level 6 dark to Level 73 have none (the last is warned in chat).

## Prioritised changes

1. **Level 31's server: `ServeHours` 1.5 to 6** (`src/Regions/L31System.cs`). Infinite stackable food two-way from Class 3-4
   levels breaks decision 21 more than anything else here. Proposed (the level's file, not this review's).
2. **Level 73's run: the Approach within 140 blocks of the castle** (MenaceSystem's Level 73 arm). Applied.
3. **Level 36's blackouts: solitude 2.5** (`Roster.Solitude`). Applied.
4. **The Basement's food x0.5, then x0.25** (`ScarcitySystem.ClassScale`). Applied.
5. **Level 36's food hoard off Level 9**: either food x0.7 in 36 (`ScarcitySystem.ClassScale`, one line, as for the Basement) or
   fewer snack shops (1 in 8 to 1 in 24, its layout). User decision.
6. **31's revolving doors named** (which level each leads to, on a sign and in the Coach's line). For the lead and the 31 agent.
7. **A surer way out of the Basement** for the unequipped. User decision.
8. **Level 23's water** Tainted outside Seedling and the Heart; its tunnel lanterns not loot. User decision; the 23 agent.
9. **Misglitch cap** six to three round a death (`src/Regions/L120System.cs`). Proposed.
10. `SurvivalClass(Level31)` 0. Applied (lore alignment; no behaviour changes).

## Applied

Single lines or arms in this review's files; each builds, and nothing in Levels 0-20 moves (see Verification).

| # | Change | File | Before | After | Measured | Why |
|---|---|---|---|---|---|---|
| A1 | Level 73: the hill Coran keeps is the Approach band | `src/Entities/MenaceSystem.cs` (Level 73's arm of the band switch) | the edge (Threshold) everywhere outside the walls | the Approach within 140 blocks of the castle's middle (`L73IslandX/Z`; Coran's leash; the arrivals lie inside), the edge beyond | the director's rolls there 813 to 208 bodies an hour, hunters about 47 % to 24 % of them; the walker's felt hunts on the hill 289 to 131 an hour (Verification) | the user's decision asks for a run "a fast player can make"; at one body every 9 s it was luck. Still the busiest approach band in the game at one-blow danger |
| A2 | Level 36: solitude 2.5 | `src/Entities/Roster.cs` (`Solitude`, a new arm) | 1.0 (the default) | 2.5 | the blackouts' rolls 95.5 to 36.3 bodies an hour (sounds 161 to 61) | the lore's "rarely", in a Class 1 level; now between Level 1's approach (23.5) and Level 3999's Blackout (122) |
| A3 | The Basement: food from blocks x0.5 (now x0.25) | `src/Salvage/ScarcitySystem.cs` (`ClassScale`, a new line) | x1 (Class 2) | x0.5, then x0.25 | pantry shelves, iceboxes, boxes and dispensers there give half, then a quarter (the class-scale behaviour every food block carries) | Fandom's "Lack of Needed Resources" and the plan's "no food of the level's own"; its pantries held more than ten sealed boxes each |
| A4 | Level 31: survival class 0 | `src/Worldgen/WorldLayout.Gates.cs` (`SurvivalClass`, a new arm) | 1 (the default) | 0 | no behaviour: scarcity, kinds at once, placards and the crossing line are the same for 0 and 1 | Wikidot's Survival Difficulty 0; the table now says it |
| A5 | The eight levels in the balance spec | `docs/design/balance-spec.yaml` | no rows | a row each: class, solitude, danger, kinds at once, class scale, the director's bands (measured after A1-A4, 100 hours) and the commonest hunter's armour rows | the gate's scorecard reads them | so a later change to any of these numbers shows up in the gate |

## Proposed (user decision)

Each with the file it lives in and the number; none applied.

| # | Change | Where | Before | After | Why |
|---|---|---|---|---|---|
| P1 | Level 31's server feeds a player every 6 game hours (now 12, with Almond Water 30 %) | `src/Regions/L31System.cs` `ServeHours` | 1.5 (16 meals a game day) | 6 (4 a game day, about 1360 satiety), then 12 (2 a game day) and Almond Water 30 % in the balance fixes of 2026-11 | an infinite stockable food and water farm two-way from Class 3-4 levels (decision 21); 4 meals keep a resident fed and give nothing to carry away. If the user would rather keep the lore's generosity, the alternative is serving a dish eaten at the counter (as Level 73's table), not an item |
| P2 | Level 36's food thinned | `src/Salvage/ScarcitySystem.cs` `ClassScale` (one line, as the Basement's) or `WorldLayout.Level36.cs` (snack shops 1 in 8 duty-free shops to 1 in 24) | x1, 1 shop in 8 | x0.7, or 1 in 24 | a Snackrooms in every duty-free street, two-way from Level 9 (food x0.35), in a level where fatigue is held. Lore class 1 argues for leaving it: the user's call |
| P3 | A surer way out of the Basement | `WorldLayout.LevelBasement.cs` (the crack's ladder) | a 2-high vanilla ladder by half the cracks | at one crack in three, a ladder or rope that reaches rel 16 (or a stack of crates under the shaft) | a Level 0-2 newcomer who falls in with nothing has Foul water, tier-3 walls and a 16-block climb; the lore's "near impossible" is kept by most cracks, and the notes can point at the one that is not |
| P4 | Misglitches round a death | `src/Regions/L120System.cs` (the 6-within-24 cap) | 6 | 3 | a Class 2 level's director allows 1-3 menacing things at once; six faster-than-walking, long-reach hunters round a corpse is a death loop |
| P5 | Level 23's water | `src/Needs/Water/WaterClass.cs` (its arm) | Clean everywhere | Clean at Base Seedling's spring and in the Heart of Water's pool, Tainted elsewhere | a Class 4 level where every puddle is clean water undoes the thirst half of its scarcity; the lore gives the "steady water" to Seedling |
| P6 | Level 73's hill | applied as the Approach band (see Applied) | | | if the user wants the run deadlier again, revert the one MenaceSystem line; if gentler, widen 140 to 160 (every arrival inside) |
| P7 | Level 31's revolving doors to Level 9 | the link session / the 31 agent | a third of them to Level 9 | the same, but each named (see "For the lead"); or only Levels 10 and 11 for doors within 200 blocks of a lobby with a wooden door | a Class 0 level's ordinary door into Class 5 without a word is a trap; the Revolving Door's lore names 9, 10 and 11 |

## For the lead (text and other agents' files)

- **31 (lang and its system):** a line over or beside each revolving door naming where it leads (the 36 gates' "TO 3999" style:
  "TO LV9 / LV10 / LV11"), and the Coach's "lead me out" saying it ("This one goes to the Suburbs. People do not come back from
  the Suburbs the way they went in."). Its handbook paragraph already says "each door always to the same one".
- **73 (lang):** the Level 6 dark's third warning naming the danger ("...and the place it takes you is worse than this one").
  The handbook page might add: "Near the castle, where CORAN hunts, the hordes are thinner; beyond the hill they are not."
- **23 (its generator):** the tunnel lanterns as a block of the level's own that drops glass (the tunnels keep their light).
- **36 (its handbook):** nothing needed; the gate screens already name the level each flight goes to.
- **Basement (notes):** if P3 is taken, one note pointing at the crack with the long ladder.
- **The link session:** the rarities quoted here are the plans' (seed 12345); the ones that matter for balance are 31's doors in
  Levels 2 and 3 (the way to its server) and 15's door in Level 3 (Level 3 to 11). Nothing here asks for a change of number.

## Verification

- `bash tools/locked.sh mod balance`: 0 errors. `python tools/expclash.py`: clean.
- `BACKROOMS_NO_EXP_ENTRANCES=1 LAYOUT_VERSION=1|12 mapgen 12345 16000 layouthash`: every line for levels 0-20 and the
  `layout hash` line (26f51e4b3d0326bf at v12) identical to main's saved files; nothing in a layout was changed.
- `GATE_TAG=balance python tools/gate.py --only scorecard --port-base 43180`: **PASS**, 315 rows, 292 within the spec, 0
  outside, 23 not measured (felt rates and class scales where a dummy cannot be placed reliably, as before), the eight new rows
  included. `--fast --port-base 43180`: **PASS** (generators, lang, build, boot on a fresh seed with 0 missing blocks and 0 error
  lines, harness smoke).
- `/backrooms ratecheck`, 100 hours each, before and after: Level 36's edge 95.5 to 36.3 bodies an hour (sounds 161 to 61);
  every other band of the eight unchanged within noise (Level 73's bands are per band: 208 / 813).
- `tools/aitest/walk.py --level 73 --minutes 25` (ports 43183 before, 43187 after; 25 real minutes, unarmoured, light 7):

  | | Before | After |
  |---|---|---|
  | Minutes in the Approach / edge | 0 / 24.5 | 8.7 / 11.3 |
  | Felt bodies an hour, Approach | (none) | 290 (hunts 131) |
  | Felt bodies an hour, edge | 510 (hunts 289) | 563 (hunts 329) |
  | Seconds from an arrival to the first encounter (any kind) | 1, 2, 2, 3, 3, 9, 25, 27 | 1, 2, 2, 5, 7, 19, 24 |

  On the hill a hunt now comes about every 27 s instead of every 12 s (the dummy's 90-block run takes 15-20 s), with glimpses and
  stalkers still within seconds of arriving: deadly, but a run can be made, and beyond the hill nothing changed. (Headless
  creatures do not walk, so the walker's deaths are not a measure; Coran is not modelled.) The Level 36 walker stayed on the
  claim hall (its route needs a gate), so Level 36's change is measured by the rolls only.
