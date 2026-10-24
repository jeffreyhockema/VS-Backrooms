# Needs: thirst and fatigue

Written 2026-10-24 from three research passes (the decompiled VS 1.22.7 engine, the Backrooms wikis and prior
Vintage Story mods, and a survey of this mod's code; the raw notes lived in a session scratchpad) and twelve
decisions the user made before any code ([decisions.md](decisions.md)). Owner: the user. Planning, briefs and
gate reviews: a Fable session. The work: parallel Sonnet/Haiku workers (one Opus piece), one per section of
[prompts.md](prompts.md). Progress: [tracker.md](tracker.md). Target: the release after 0.515.0 (0.516.0),
unless the user folds it into 0.515.0.

The player now has four needs: health and food (vanilla), **water** and **rest** (this plan). Both are on by
default in every world, including worlds made before this update, and each can be switched off when a world is
made (or later with `/worldconfig`). Thirst and fatigue reuse what the engine already has (vanilla hunger's
drain shape, the `tiredness` stat and bed mounting, temporal stability as sanity) and what the mod already has
(Almond Water, the entity director, the heat system).

## Status

| Piece | What | State |
|---|---|---|
| A | Core: thirst and fatigue behaviours, settings, stability drain, director multiplier, night visits, commands | not started |
| B | Beds: every bed-like block sleepable, own bed block entity, wake rules, carpet bedroll | not started |
| C | Drinks and water: bottles, world water by class, boiling, Blue and Green Almond Water, supply | not started |
| D | HUD meters and exhaustion visuals, cheat-menu buttons | not started |
| E | Glass spear | not started |
| F | Handbook, guide, README, changelog, world-setting text, developer notes | not started |

## 1. Why

The mod's survival pressure is food, light and the entities. Food is a solved loop (boxes, caches, farming);
nothing makes a player stop, and nothing makes a camp matter. Canon says wanderers die of thirst as readily as
hunger ("Frequently consume Almond Water to prevent dying of starvation or thirst", Object 1) and treats sleep as
the moment of greatest risk ("sleep in shifts, and only if you absolutely must", Level 8; "barricade your door",
Level 1). Two new needs give the mod both: water that must be found and carried, and sleep that must be found a
place for.

Canon has no numeric sanity and no rule that sleep loss costs sanity; that part is the mod's invention, with
Green Hell and Don't Starve as precedent. "Sanity" here is Reality Stability, as everywhere else in the mod.

## 2. The clock

Everything below is in game hours, so sleep (which runs the calendar fast) and a changed day length behave.
At the default calendar 1 game hour is 2 real minutes and a day 48 real minutes.

| Thing | Game hours | Real minutes at default |
|---|---|---|
| Water, full to empty, walking | 12.5 | 25 |
| Water, full to empty, idle | 50 | 100 |
| Rest: rested | 0 to 24 awake | 0 to 48 |
| Rest: drowsy (can sleep) | 24 to 45 awake | 48 to 90 |
| Rest: exhausted | 45 to 60 awake | 90 to 120 |
| Rest: dead on your feet | 60 awake and on | 120 and on |
| A full sleep in a good bed, from empty | 8 slept | a few real seconds while the clock runs fast (about 284x) |

## 3. Thirst

**Meter.** `hydration` 0..1500 on the player (watched tree `backrooms-thirst`, keys `hydration`, `maxhydration`;
synced to the client). New players and old saves start full. Respawn sets it to half, like food.

**Drain.** The same shape and scale as vanilla hunger: 1.0 per real second while moving, 1.5 while sprinting,
0.25 when idle for more than 3 seconds, all multiplied by the calendar factor `SpeedOfTime * CalendarSpeedMul /
30` (1 at the default calendar, about 284 while everyone sleeps), so a full night's sleep costs about 240
hydration, as it costs about 290 satiety. Not multiplied by `playerHungerSpeed`. Multiplied by the player stat
category `thirstrate` (additive on a base of 1, like `hungerrate`): heat sets it (below), sickness sets it.
Nothing drains in Creative or Spectator.

**Heat.** `HeatSystem` moves its penalty from `hungerrate` to `thirstrate` while thirst is on (same numbers: 0.06
per degree above 30 C, at most 0.5). With thirst off it stays on `hungerrate`, as today. Its class comment
("thirst was left out") is rewritten.

**Bands** (fraction of the meter):

| Band | Effect |
|---|---|
| above 40% | nothing |
| 40% to 0 | `walkspeed` stat falls linearly to -25% at empty (`Stats.Set("walkspeed", "backrooms:thirst", x)`) |
| below 20% | the HUD bar flashes |
| empty | 0.2 damage every 6 s (`EnumDamageSource.Internal`, `EnumDamageType.Poison`, death message "died of thirst"); a stability offset of -0.2 (section 5); the Wretch's roster weight is tripled as it is for starving (parched = below 25%) |

**Drinks.** Any collectible with `attributes.hydration` hydrates by that much when consumed; the mod's drink
classes call `Needs.Hydrate(entity, amount)` from their `tryEatStop`. Almond Water's class (`ItemAlmondWater`,
registered as `BackroomsAlmondWater`) becomes the general drink class:

| Item | Hydration | Satiety with thirst on | Stability | Leaves |
|---|---|---|---|---|
| `almondwater` | 600 (40%) | 0 (was 120) | +0.15 | empty bottle |
| `almondwaterblue` (new) | 600 | 0 | +0.25; makes you drowsy at once (rest set to 24 awake hours if lower) | empty bottle |
| `almondwatergreen` (new) | 600 | 0 | +0.10; caffeine: fatigue stops growing for 10 game hours and the exhaustion penalties lift; when it wears off, 8 awake hours land at once (stacks) | empty bottle |
| `cashewwater` | 600 | 0 (was 140) | +0.08 | empty bottle |
| `waterbottle` | 600 | 0 (was 100) | 0 | empty bottle |
| `bottledwater-clean` (new) | 600 | 0 | 0 | empty bottle |
| `bottledwater-murky` (new) | 300 | 0 | -0.05, 25% chance of gut rot | empty bottle |
| `bottledwater-salt` (new) | -300 | 0 | 0 | empty bottle |
| `almondmilk` | 500 | 300 (unchanged, it is food) | +0.10 | nothing |
| `soda`, `l3999-soda-*` | 300 | unchanged | 0 | nothing |
| `l188-juicebox` | 350 | unchanged | 0 | nothing |
| `l974-strawberrymilk` | 400 | unchanged | 0 | nothing |
| `redwater` | 200 | unchanged | its own | nothing |
| `end-memoryjuice`, `fun-lucatears` | 100 | unchanged | their own | nothing |

With thirst off every item keeps today's satiety and nothing leaves a bottle; `GetNutritionProperties` picks the
satiety by the world setting (attribute `satietyWhenThirst`, default 0, applies only to items that have it).
Drinks keep `nutritionProps` (satiety 0 where needed) so vanilla's eat pipeline, `ScarcitySystem.IsFood` and the
rats' bait logic keep treating them as consumables; hydration is read from `attributes.hydration`. Item tooltips
gain a "Hydration: 40%" line.

**World water.** Crouching, with empty hands, hold right-click on a liquid block for one second to drink one litre. The
client makes liquids selectable only while thirst is on, the active slot is empty and the player crouches (`ForceLiquidSelectable`; otherwise items on a pool floor could not be picked); a
`BlockBehavior` added to every `game:water-*`, `saltwater-*` and `boilingwater-*` block on both sides handles
start/step/stop and the server applies the effect. What you get depends on the water's **class**, decided by
level and block (`WaterClass.At(world, pos)`):

| Class | Where | Drink |
|---|---|---|
| Clean | Level 8 cave pools, Level 10 ponds, Level 37 pools, Level 94's town fountain basin, Level 974 | +600 |
| Tainted (the default for anything unlisted) | Level 1 to 5 sumps and puddles, Level 3 flooded tunnels, Level 9 house pools, Level 11 city water and fountains, Level 94 flooded houses, Level 3999 natatorium, Level 188 | +300, stability -0.05, 25% chance of **gut rot**: `thirstrate` and `hungerrate` +0.5 for 10 game hours (watched `backrooms:sickUntil`, calendar hours; message "Your stomach turns") |
| Salt | Level 7's sea, Level Fun's sea | -300 ("It's brine") |
| Scalding | `boilingwater-*` (Level 5 sumps) | 2 damage, nothing else |

Lore: Level 0 carpet fluid and Level 1 drips are unsafe; Level 8 pools and Level 10 lakes are "safe to drink";
Level 7's salinity is unstated, so real seawater applies.

**Bottles.** Drinking a bottled drink leaves `emptybottle` (stack 16). Right-click a liquid block with it to
fill: `bottledwater-clean`, `-murky` or `-salt` by the water's class (boiling water fills a clean bottle). A murky
bottle **boils clean in a firepit** (`combustibleProps` on `bottledwater-murky`: melting point 100, duration 10,
smelts to `bottledwater-clean`); salt water never does. This is how water travels from the wet levels into the
dry ones.

**Supply.** The user wants water "as scarce as food". Today it is renewable and dense. Changes (all at run time,
no layout version):

- Dispensers that hand out drinks (Level 4 machines and coolers, Level 10 pumps, Level 94 fountain spouts and
  tower taps, vendor carts, drink fridges, milk vans) hold their one-time stock (`Next(1,4)` portions scaled by
  scarcity) and **never restock** while thirst is on. Level 8 almond seeps still restock, every 14 days instead
  of 7, holding 1 to 3. Food-only dispensers are unchanged. Level 974's taps and Level 3999's vending are
  unchanged (far, earned).
- Supply boxes keep their Almond Water (0.8 per sealed Lobby box, 0.6 per Level 1 crate). Each sealed box and
  crate adds `almondwaterblue` and `almondwatergreen` at 0.05 each; drink fridges and vendor carts list both;
  the Rewards deep-cache table and `IsLoot` code lists learn the new codes; the Wanderer sells Blue (price 2,
  stock 2) and Green (price 2, stock 2).
- Food scarcity: Almond Water was about a quarter of box satiety. The user judged that not significant enough
  to rebalance, so box food tables are unchanged.

## 4. Fatigue

**Meter.** `awakeHours` on the player (watched tree `backrooms-fatigue`, keys `awakeHours`, `caffeineUntil`,
`crashHours`; synced). The HUD shows **Rest** = `1 - awakeHours / 60`, clamped. New players and old saves start at
0 awake. Respawn sets awake hours to 12 (half rested). Nothing grows in Creative or Spectator.

**Growth.** +1 awake hour per game hour awake (so the Rest bar is the clock itself). Paused while caffeinated.
While asleep it falls (below).

**Vanilla tiredness.** The fatigue behaviour overwrites the vanilla `tiredness` value every tick from awake
hours: `8 * awake/24` below 24 hours, `8 + 4 * (awake-24)/36` above, capped at 12. Vanilla's bed gate (`Tiredness
<= 8` refuses) therefore opens at exactly 24 awake hours, and vanilla's own +0.75/h growth is overwritten before
it matters. Nothing else in vanilla reads tiredness.

**Bands:**

| Band | Awake hours | Effects |
|---|---|---|
| rested | 0 to 24 | none; you cannot sleep ("not tired enough", vanilla text) |
| drowsy | 24 to 45 | you can sleep; a one-time hint "You could sleep now"; nothing else |
| exhausted | 45 to 60 | `walkspeed` -10%; stability offset ramps from 0 at 30 h to -0.5 at 60 h (section 5); director multiplier ramps (section 6) |
| dead on your feet | 60 and on | `walkspeed` -20%; stability offset -0.5; director multiplier keeps rising to 84 h; the Rest bar flashes; the screen dims and blinks (section 7); the Wretch's weight is tripled as for starving |

Awake hours keep counting to 84 (a hard cap) so the penalties can keep ramping; they never kill directly.

**Sleeping.** Mounting any bed (section 8) sets vanilla `IsSleeping`, so vanilla's all-asleep time skip and the
eyes-closing overlay work unchanged. While a player is asleep the fatigue behaviour's tick does the resting:
every tick `awakeHours -= sleptHours * 7.5 * quality` where `quality` is the bed's `IRestPlace.RestQuality`
(section 8), so a quality 1 bed restores 60 hours of wakefulness in 8 slept hours. The sleeper is woken (`TryUnmount`)
and told why when:

- awake hours reach 0 ("You wake rested");
- they take damage (hook `EntityBehaviorHealth.onDamaged`; "Pain wakes you");
- a menacing creature (`EntityBehaviorMenace.KindOf` is Stalk or Hunt) comes within 6 blocks ("Something is in
  the room");
- hydration or satiety falls below 10% ("Thirst wakes you" / "Hunger wakes you"); the same two refuse sleep;
- they sneak (vanilla).

**Night visits.** Each slept game hour outside the director's Safe band rolls a visit with probability
`0.06 * Danger.OfLevel(level) * Setting.Spawns * doorFactor`, `doorFactor` 0.5 when a closed door stands within 4
blocks of the bed (Level 1's "barricade your door"). A visit asks the director to place a Hunt-kind creature from
the level's roster 12 to 18 blocks away, out of sight, hunting the sleeper; the proximity rule above then wakes
them as it closes. Over a full sleep that is about 6% in Level 1, 22% in Level 5, 37% in the deepest levels, 0 in
Level 0 (danger 0), 0 near a wanderer, in Level 974, Level 37 or the Level 0 home base (all Safe band). A visit
respects the one-kind rule and the hard gap like any other body, and counts as the body.

## 5. Sanity

Stability is per player and position based, so the needs push the player's `stabilityOffset` (the field vanilla's
rifts use; `here = offset + area value`, draining while below 1). Level 974 already writes that field, so a shared
`StabilityOffsets` registry (named contributions per player, summed into the field once per tick) replaces the
direct writes, and Level 974 moves onto it.

| Source | Offset |
|---|---|
| fatigue | -0.5 * clamp((awake - 30) / 30, 0, 1) |
| thirst empty | -0.2 |
| caffeine active | fatigue term suppressed |

A -0.5 offset turns Level 0's 1.0 area into a 0.5 drain, and even Level 4's 1.25 becomes 0.75, a slow drain: no
level recovers a player who is dead on their feet. Below 0.3 stability the mod's own fog cue and vanilla's visuals begin; below 0.13
vanilla's stability damage begins. That is how exhaustion kills: through the Backrooms.

## 6. Entities

`MenaceSystem` gains a per-player `NeedsMult(player)` applied where `Setting.Spawns` enters the roll
(`MenaceSystem.cs` call sites of `EncounterRoll.Roll` and `BodyGapMs`):

| Awake hours | Multiplier |
|---|---|
| below 24 | 1.0 |
| 24 to 60 | ramps 1.0 to 2.5 |
| 60 to 84 | ramps 2.5 to 3.5 |
| plus thirst empty | +0.5 |
| caffeine active | multiplier held at 1.0 |

The mean body interval divides by it, so it stacks with the other inputs. `/backrooms ratecheck` takes an optional
`awake=<hours>` to show the effect; `tools/aitest` `t_iso_rates` is unchanged because the multiplier is 1 at 0 awake.

The Wretch (Entity 15, "starved, parched, sleepless") triples its weight when the target is starving **or** parched
**or** dead on your feet.

## 7. HUD and client

A `HudElement` (`HudNeeds`) with the same 850-wide `CenterBottom` frame as vanilla's `HudStatbar`:

- **Thirst** above hunger: `Statbar(RightTop, 850*0.41)`, height 10, offset (-1, -15), fills right to left like
  hunger (`AddInvStatbar`), colour (0.22, 0.52, 0.86). Hover text "Hydration 1200 / 1500".
- **Rest** above health: `Statbar(LeftTop, 850*0.41)`, offset (0, -15), colour (0.56, 0.44, 0.78), hover "Rest 72%".
  Vanilla's oxygen bar uses (0, -15) only while oxygen is not full; when the `breathe` tree says so, Rest moves to
  (0, -35) until oxygen is full again.
- Bars flash below 20%. Each bar is hidden when its mechanic is off, and both in Creative and Spectator.
- Values come from the watched trees; a 100 ms client tick recomposes only on change.

Exhaustion visuals (AtmosphereSystem, client, from the synced awake hours): at 60 h and beyond the ambient dims by
up to 25% and desaturates slightly, and every 30 to 60 s the view blinks dark for 0.3 s. Caffeine lifts it.

## 8. Beds

Today only `l974-bed` and `l188-bed` are real beds (vanilla `BlockBed` plus block entity `Bed`); every other
bed-like block is decor. All of them become sleepable through the mod's own classes, registered as
`BackroomsBed` (block) and `BackroomsBed` (block entity), with `api.RegisterMountable("backroomsbed", ...)`:

| Block | Parts | Quality | Where |
|---|---|---|---|
| `bed-head-*` + `bed-foot-*` | 2 (head holds the entity) | 1.0 | Level 5 hotel rooms, Level 9, 94, 11 houses and flats |
| `l974-bed-*` | 2 (vanilla layout, `head`/`feet`) | 1.0 | Kitty's bedroom (keeps DreamSleep: `L974System` checks the mod's entity type) |
| `l188-bed-*` | 2 x 2 (each half head/feet) | 1.0 | Level 188 rooms |
| `hospitalbed-*` | 2 | 0.9 | Level 1 camp rooms, Level ! |
| `run-safecot-*`, `hub-cot-*` | 2 | 0.75 | Level ! Safe Zone, the Hub |
| `sleepingbag-*` | 2 (`BackroomsPartnered`) | 0.75 | Level 4 outposts, camps |
| `improvbed-*` | 1 | 0.6 | Level 1, 4, 6, 7 camps and dens |
| `bedroll-*` | 1 | 0.6 | Level 1, 4, 7, 8 camps |
| `carpetbedroll-*` (new, craftable) | 1 | 0.6 | wherever you put it |

Rules:

- The block entity subclasses vanilla `BlockEntityBed` (so `MountedOn is BlockEntityBed` keeps working for the sleep
  overlay, the director's rest check and anything else), re-implements the seat so that a one-block bed's seat is the
  block's centre and a two-block bed's seat is the head's edge toward the foot, does **not** run vanilla's
  `RestPlayer` (resting belongs to the fatigue behaviour), sets `IsSleeping` on mount and clears it on unmount, wakes
  on sneak, and exposes `IRestPlace.RestQuality` from the block attribute `restQuality` (falling back to
  `sleepEfficiency`, then 0.6).
- Worldgen never spawns block entities, and old worlds have none (or a vanilla `Bed`), so the block **creates or
  replaces the entity lazily on first interaction**.
- Clicking a foot/feet block resolves to its head. A two-block bed's head direction comes from the block's
  attributes (`bedFoot: "side"` means the foot lies in the direction of the side code; `bedFoot: "opposite"` the other
  way), set per family in the generators.
- Refusals use the vanilla "not tired enough" text at under 24 awake hours, plus the hunger/thirst/menace reasons
  from section 4 (`Needs.CanSleep(player, pos)` returns the reason or null).
- The vanilla BlockBed interaction gate is not used (our block class is not a BlockBed), so Blue Almond Water's "drowsy
  at once" works by setting awake hours, nothing else.
- Blocks keep their codes, variant groups, shapes and drops. Generators (`gen_blocktypes.py`, `gen_detail.py`,
  `gen_974.py`, `gen_188_props.py`, `gen_run.py`, `gen_hub_tower.py`) are the source of truth: they write the class,
  `entityClass`, `restQuality` and `bedFoot`; regenerate and keep the CRLF churn out of the commit.

**Carpet bedroll** (`carpetbedroll-{north,east,south,west}`, item of the same name): the `bedroll` shape with Level 0's
chevron carpet texture; recipe `FF / WW / FF` (4 carpet fibres, 2 wallpaper strips, shaped 2 wide 3 tall); placed
with `BlockBehaviorOrientable`; breaks back into itself (not into cloth and grass like the found ones). Handbook text
calls it what it is: enough to sleep on, not enough to sleep well.

## 9. Glass spear

`glassspear` (lang "Glass spear"): class `ItemSpear` with `AnimationAuthoritative` and `GroundStorable`, `tool:
spear`, `attackpower` 2.0, thrown `damage` 4.0, `damageTier` 0, `attackRange` 3.5, `durability` 12, damaged by
attacking and by impact (vanilla `DamageStackOnImpact`), `spearEntityCode: backrooms:glassspear` (own projectile
entity copied from vanilla `spear.json`, class `EntityProjectile`, the item's shape). Shape: vanilla's stone spear
shape with the glass shard's texture on the head. Recipe, shaped 1 wide 3 tall: glass shard / carpet fibre / stick
(the fibre is the lashing). Between flint (2.0, 4.0, 32) and nothing; it breaks after a dozen hits. Venom applies to
it like any `spear-*`? No: `venom-spear.json` matches `game:spear-*` only; leave it.

## 10. Settings

`worldconfig.json`: two `dataType: "bool"` attributes in `survivalchallenges`, `backroomsThirst` and
`backroomsFatigue`, default `"true"`, and both `"true"` in the playstyle's `worldConfig`. Lang
`worldattribute-backroomsThirst` "Thirst", `-desc` "Players need water as well as food. Almond Water is a drink."
and `worldattribute-backroomsFatigue` "Fatigue", `-desc` "Players need sleep. Going without costs Reality Stability
and draws entities." in `assets/game/lang/worldconfig-en.json` (Spanish files get the English text).

Read live with `Config.GetBool(code, true)` (bool attributes; `GetString` would return null). **Old worlds get both
on** (the user's call, decisions 1): the first time a player joins a world that lacks the keys, a chat line says the
two needs are on and how to turn one off (`/worldconfig backroomsThirst false`, takes effect at once because the
settings are read live). `docs/DEVELOPING.md`'s "new settings default to the old behaviour" rule gets these two as
the stated exception.

With thirst off: no drain, HUD bar hidden, drinks are food again (today's satiety), no empty bottles, world water
cannot be drunk, bottles already in hand still work as drinks, dispensers restock as today, heat drains hunger.
With fatigue off: no growth, bar hidden, beds still work (vanilla's own `tiredness` gate and a fixed 8-hour
rest), no night visits, no penalties. With fatigue off beds still wake you for pain, something close, hunger or
thirst.

## 11. Save compatibility

- New codes only: items `emptybottle`, `bottledwater-clean/murky/salt`, `almondwaterblue`, `almondwatergreen`,
  `glassspear`, `carpetbedroll`; block `carpetbedroll-*`; entity `glassspear`.
- Bed blocks gain a class, an `entityClass` and attributes; codes, variant groups and drops are unchanged. Chunks
  that hold a vanilla `Bed` entity load it and the block replaces it on first use.
- New player attributes (`backrooms-thirst`, `backrooms-fatigue`, `backrooms:sickUntil`, `backrooms:needsNotice`)
  have defaults that mean "full and fine".
- Two new world settings; absent means on (section 10).
- No worldgen change, so no layout version. Dispenser restocking is a run-time rule.

## 12. Debugging

`/backrooms needs [player]` prints hydration, awake hours, band, caffeine, sickness, bed under the player and its
quality, the director multiplier. `/backrooms stat thirst <0-1>` and `/backrooms stat rest <0-1>` set the meters.
`/backrooms heal` fills both. `/backrooms needstest` runs the pure-math self-checks (drain per hour, band edges,
tiredness mapping, visit odds) and prints pass/fail, so the headless harness has something to assert. Cheat menu,
Player tab: "Thirst 10%", "Rest 10%", "Drowsy (25 h)", "Dead tired (60 h)", "Needs". `tools/aitest/run.py` gains
`t_needs_selftest` and `t_needs_boot` (every new item, block and entity resolves; `blocksweep` clean).

## 13. Out of scope, noted for later

- Red Almond Water (medicine) and Grey/Blue/Green as a full colour system with textures per thermos.
- Thinning Level 8 seeps in the layout (would need layout version 12); done at run time instead.
- Vanilla containers (bowls, jugs, buckets) as drink vessels; waterskins; kegs.
- A `sleep safety` flag per level beyond the director's Safe band; sleeping in shifts in multiplayer.
- A tutorial step for thirst and sleep (the handbook covers it).
