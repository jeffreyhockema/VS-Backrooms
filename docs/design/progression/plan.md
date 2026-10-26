# Progression pressure: a Vintage Story climb through the levels

Written 2026-10-25 from the user's note after the dial-in play-test ("the balance is pretty good, but nothing pressures
you to stay in lower levels and build tech and a base; you can just run and run and be done") and twenty answers the
same day ([decisions.md](decisions.md)). Folds into **0.515.0**. Branch `progression`, worktree `../VS Backrooms-prog`.

## 1. What is wrong today

A read-only survey (2026-10-25) found no gate anywhere that asks for a tool, key, item or skill. Every ring boundary has
a free, two-way, walk-through gate that chalk arrows point to. Every pressure is a drain or a spawn rate, and each is
beaten by walking on: heat only taxes the thirst bar, cold bites only if you stand still, stability is low only in
pockets (Level 6, Level 3's tunnels, Red Rooms, the Reservoir, Level 7's depths) and an Almond Water fixes it, the
corpse always waits. Two leaks: a copper pickaxe tunnels through level walls (kept, by decision), and the vanilla
underground puts copper, tin and iron under every level, so Level 8's strata are optional. Deeper levels pay better,
so the incentive points down and nothing pushes back. Mod-page feedback said the same: flint tools last to the end
because every entity can be outrun.

## 2. The model

Two soft gates, no hard gates (decision 2):

1. **Reality Stability is the depth meter.** Each level has a required *ward tier*. At or below your tier the level
   is as it is today. One tier beyond, your stability runs to zero in about ten real minutes; two beyond, about three.
   At zero the level's hunters come, and if it stays at zero you black out and wake at a random place in the previous
   level with your inventory. You can enter anywhere and grab something, but you cannot stay, cross, or mine without
   the tier. (Subnautica's oxygen; the Backrooms' own loss of grip on reality.)
2. **Lethality that armour answers.** From Level 3 down a catch kills the unarmoured in two or three hits, by Level 8
   in one or two, and every hunter but the lore-slow ones outruns a sprint. Encounters stay rare; surviving one needs
   the tier's armour, the counters that exist, or luck, as with vanilla's wolves and bears.

The ladder, with what the tier needs and where it comes from:

| Tier | Ward | Levels it holds | What the tier needs | Where it is |
|---|---|---|---|---|
| 0 stone | none | 0, 1, 2, Hub, 974, Snackrooms | flint, glass, candles, rat hides, pleather | Levels 0 to 2 |
| 1 copper | copper anchor | 3, 4, 5 | copper, clay, coal, a temporal gear | scrap copper in Level 2; clay and coal by raids into Level 3 (or the slow pottery-shard route in Levels 4 and 5); gears from caches, the Level ! prize, Level 3999, wanderers |
| 2 bronze | bronze anchor | 6, 7, 8, 37, 94 | tin for bronze, leather armour, a second gear | tin by a dash off the 9th Road (its lamps keep stability up: the raid is the design) |
| 3 iron | iron anchor | 9, 10, 11, End, 188, Fun, !, 3999 | iron, so fire clay (94), sand (7), ore and coal (8), a third gear | the bronze tier's three expeditions |
| steel | (iron ward) | the same, with steel armour | the vanilla road | home |

Level 2 is tier 0 so the copper source (cable drums, fans, pipes) is reachable; Level 94 is tier 2 so the fire clay
that makes iron is a bronze-tier climax, not a circle. Target pace: a competent player reaches Level 8 in **8 to 12 real
hours** (decision 8): home and farm in Level 0, copper by hour 3 or 4, bronze and the first ward by about hour 8.

## 3. Mechanics

### 3.1 The drain (piece A)

- `Roster.WardTier(level)` (or `WorldLayout`): the table above. Noclip-only places take the tier of the table; the
  Hub, Level 974 and the Snackrooms stay stability-safe as today.
- The player's ward tier = the best anchor worn (3.2); armour of a tier adds half a tier when the whole set is worn,
  and the half tier is fractional: leather + copper anchor = 1.5, so a bronze level (0.5 beyond) lasts roughly twice as long
  as with the anchor alone (about 20 minutes, not 10), and an iron level (1.5 beyond) drains at the one-and-a-half-tier rate.
- `RealitySystem.OnGetStability` keeps `StabilityAt` for the pockets and adds the **depth deficit**: 0 at or below the
  tier, and for each tier beyond a deficit that makes vanilla's drain take about 10 minutes (one beyond) or 3 minutes
  (two or more) from full to zero. Calibrate against vanilla's own rate headless (a dummy cannot: use an `EntityPlayer`
  on a test client, or read vanilla's `SystemTemporalStability` formula and compute; the harness then checks the
  area value, not the clock). Reality Shifts keep their own drain on top.
- The exposure clock (`OutHours`) and the needs' stability effects stay as they are.

### 3.2 Wards (piece A)

- Three worn items in the **neck** slot (vanilla wearable slot): `backrooms:anchor-copper`, `-bronze`, `-iron`. No
  durability. Lore name "anchor": the thing that keeps a thread back to you (the mod's `AnchorSystem` already uses the
  word for the Level 0 spawn rule; the handbook ties the two).
- Recipes chain: copper anchor = 2 copper ingots + 1 temporal gear + 1 candle; bronze = copper anchor + 2 bronze ingots
  + 1 gear; iron = bronze anchor + 2 iron ingots + 1 gear. Gears are vanilla `game:gear-temporal`, found and bought
  (decision 4): raise the cache odds a little in Levels 1 to 5 (today 6 % in deep caches), the Level ! prize's two stay,
  Level 3999's tickets stay, and wanderers sell a gear for rusty gears (3.6). Never a finished anchor or armour for sale.
- `/backrooms ward` prints the player's tier and the level's; the HUD's stability bar is enough otherwise. The handbook
  explains the tiers ("What holds you here").

### 3.3 Almond Water (piece A, in `Drinks.ApplyDrink`, which vs-backrooms-b2 moved there in b3efe1a)

Restore = today's amount x max(0.2, 1 - 0.4 x (tiers beyond)), and never above a ceiling: 1.0 at or below the tier,
0.6 one beyond, 0.3 two beyond. Blue and Green Almond Water follow the same rule on their own amounts. First aid,
not the ladder (decision 6).

### 3.4 Zero (piece A)

- At zero stability in a level beyond the tier the director treats the player as "unsteady" (today's rolls already
  favour hunts at low stability): send the level's worst hunter at once (`MenaceSystem.SpawnHunter`, set-piece rules).
- After **60 s at zero** (any cause, in any level but 0, the Hub, Kitty's House and the Snackrooms: the user's decision, see decisions 15): blackout (the client's `flickerUntil`
  darkening for 3 s, a sound), then the player is moved to a **random walkable spot in the previous level** (`level - 1`
  for rings; for a noclip place, the level its way in came from; from Level 1, a random spot in Level 0), inventory
  intact, stability set to 0.5, no thin spot and no way back placed (decision 3). Vanilla's temporal-storm damage at
  zero is left as it is (it is off in Backrooms worlds today: check `temporalStorms`).
- Log line and a chat line ("You lose your grip on the place. When you come to, the walls are the wrong colour").

### 3.5 Lethality and speed (piece B)

- `Danger` stays the curve; the multipliers in `EntityBehaviorMenace` change so that a hunter's hit on an unarmoured
  player is about 6 at Level 3 (15 HP: 2 to 3 hits), 8 at Level 5, 10 to 12 at Level 8, 14 at Level 9 and deeper
  (decision 5). Vanilla armour then does the work: a leather set halves the Level 3 hit; a copper or bronze lamellar or
  chain set is needed to stand two hits at Level 8; iron plate at Level 9 and deeper. Measure hits-to-kill per level
  and armour set headless (`armourtest`: a dummy with the set, the level's hunter striking) and put the table in the
  tracker; tune the armour's vanilla protection only if the vanilla numbers cannot give the table.
- Speed: from danger 0.36 (Level 3) every hunter's run speed is at least 1.15 x a sprint (0.058), rising to 1.4 x at
  Level 9, **except** Wretch, Clump and Duller (lore-slow: they ambush or reach). Hounds already run 0.062 base.
  Deathmoths fly; the Thing swims; both already outpace.
- The one-kind rule, rates and the Hound counters are untouched: encounters stay rare.

### 3.6 Resources and trade (piece C)

- **Ore only in Level 8** (decision 2): `UndergroundSystem` skips vanilla `GenDeposits` for chunk columns outside
  Level 8 (the ring test per chunk column; Level 8's own "wrong strata" ore stays). Already-generated chunks keep what
  they have. Halite, quartz, lime, coal under other levels go with it (the levels' own sources remain: Level 3 coal,
  Level 8 halite and quartz, Level 94 fire clay).
- **Pleather** (decision 10): new item `backrooms:pleather` (cap, jerkin, leggings cost 5 / 8 / 7) salvaged from Level 1 car seats, Level 4 office chairs and
  Level 5 hotel chairs and sofas (`tools/salvage.py`), 1 to 2 a piece. Its own armour set (`pleather jerkin/leggings/
  boots`): about 40 % of leather's protection and a quarter of its durability, repairable only with pleather. It is
  **not** leather: no vanilla recipe accepts it (bags, straps, backpacks keep needing leather), so tanning rat hides
  and Level 9's hides stays the real road. Handbook says so plainly.
- Early leather: Death Rats drop a small hide (vanilla `hide-raw-small`) at a modest rate in Levels 1 and 2.
- **Wanderers** sell a temporal gear for 6 rusty gears (about eight mid-level Hound bounties) and a candle (prices in the wanderer trade table), never anchors
  or armour.
- Cache and crate tables: thin copper tools out of Level 1 toolboxes (a hammer or chisel now and then, never a
  pickaxe); temporal gears a little commoner in Levels 1 to 5 caches.

### 3.7 Settings (piece B)

Lethality is not a setting (decision 8). The entity setting's names shift up one step: `Spawns` off 1, verylow 2, low
3.5, normal 5.5, high 8.5, veryhigh 13; the mix and cap bonuses stay on high and veryhigh. Lang descriptions updated
(en, es-419, es-es). Worlds keep their code string, so a "normal" world gets the new normal (decision 9). Set-pieces (night visits, hive waves, the Mangled's fog, the Beast) scale by the square root of the setting's multiplier, so Normal is about 2.3 times their original values, not 5.5 times (decision 14).

### 3.8 Respawn (piece A)

Decision 9: you wake in the **last bed you slept in**, anywhere, else your Level 0 home. `AnchorSystem` drops the
Level-0-only rule; sleeping in a bed (the needs system's beds) sets the spawn point there; a temporal gear still sets
it where used. Corpses stay untouched (decision 9). The handbook's "home" page and the anchor-lost message change.

### 3.9 Docs (piece D)

Handbook (`tools/gen_guide.py`): a new page "What holds you here" (tiers, anchors, Almond Water, the blackout), the
Progression Guide's ladder rewritten to section 2's table, the levels page's per-level line gains its tier, the
entities page's armour paragraph, the home page's respawn rule, pleather in Salvage. GUIDE.md, README level table,
CHANGELOG Unreleased, `docs/design/entity-difficulty.md` section 5, `playtest.md` section 11.

## 4. Not in this round

Hard gates and key items (decision 2); camps and placed wards as a mechanism (not chosen); corpse looting (decision
9); M.E.G. outposts as shops; a second lethality setting; any new entity, model or layout change; the Level 1 clay
source (raids into Level 3 are the intended way; revisit after the play-test).

## 5. Save and setting compatibility

No code, attribute or setting value renamed or removed. New items only. Generated chunks keep their ore. The spawn
point rule loosens (a spawn outside Level 0 is no longer cleared). Entities loaded from a save still despawn at once.
A world on any setting keeps its code string.

## 6. Pieces, owners, files

| Piece | Model | Branch | Files |
|---|---|---|---|
| A reality: tiers, drain, anchors, Almond Water, zero, respawn | sonnet | prog/reality | `src/Reality/RealitySystem.cs`, `AnchorSystem.cs`, new `src/Reality/Wards.cs` (tier logic) and `ItemAnchor.cs`, `src/Needs/Water/Drinks.cs` (the restore rule only), `src/Worldgen/WorldLayout.Reality.cs` (tier table), `src/Entities/MenaceSystem.cs` (one call: the zero hunter; coordinate with B), assets for the three anchors (`tools/gen_entities.py` or a new `tools/gen_wards.py`: itemtypes, recipes, textures), lang |
| B entities: lethality, speed, settings shift, armour test | sonnet | prog/lethality | `src/Entities/EntityBehaviorMenace.cs`, `Roster.cs` (Danger comments), `MenaceSystem.cs` (Difficulties), `tools/gen_entities.py` (run speeds), `assets/game/lang/worldconfig-*.json`, `tools/aitest/run.py` (`armourtest`, speed cases) |
| C resources: ore, pleather, hides, trade, caches | sonnet | prog/resources | `src/Worldgen/UndergroundSystem.cs`, `tools/salvage.py`, `tools/gen_breakdown.py` or `gen_detail.py` (pleather item and armour), `src/Entities/WandererSystem.cs` trade table, `src/Entities/Rewards.cs` and the cache tables, rat drops in `tools/gen_entities.py` |
| D docs | haiku | prog/docs | `tools/gen_guide.py` and lang, `docs/GUIDE.md`, `README.md`, `CHANGELOG.md`, `docs/design/entity-difficulty.md`, `docs/design/entity-ai-overhaul/playtest.md` |

Each worker: worktree `../VS Backrooms-prog-<piece>` on its branch off `progression`, `tools/locked.sh mod prog-<piece>`,
own harness port, a blind sonnet reviewer, a report in `docs/design/progression/tracker.md`, commits on its branch.
The overseer merges, runs the full harness plus the new cases, loads a copy of an existing world, rebuilds the zip,
tells the peer sessions (vs-backrooms-b2 owns the play-test fixes; vs-backrooms-2e the needs code), merges to main.

## 7. Gates before the zip

- Harness: `armourtest` table per level and armour set; speed cases (a Level 3 Smiler closes on a running dummy);
  the zero blackout moves a dummy-stand-in (or is checked by code path) to the previous level; `iso` and `felt` still
  pass; ore absent in a Level 0 dump column, present in a Level 8 one.
- Calibration: the drain's minutes measured on a client once (the user's play-test confirms the feel).
- Old world load: 0 errors; a spawn point outside Level 0 survives a join.
- Client check-list (`playtest.md` section 11): raid Level 3 unwarded and feel the ten minutes; the blackout and the
  wake-up; the copper anchor; a Level 3 Hound in leather and in pleather; the 9th Road tin dash; Level 8 in bronze;
  Level 9 in iron; wanderer prices.
