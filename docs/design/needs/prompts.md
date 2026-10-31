# Needs: worker briefs

One brief per piece of [README.md](README.md). Every worker gets the same preamble, then its section. The plan is
the specification; where a brief and the plan differ, the plan wins, and where the plan is silent the worker
decides and writes the decision in its report.

## Preamble (every worker)

You are implementing one piece of the "Needs" feature (thirst and fatigue) of a Vintage Story 1.22.7 mod,
"Backrooms: Survival Story". Read, in this order: `docs/design/needs/README.md` (the plan; your section and
sections 2, 10, 11), `docs/design/needs/decisions.md`, `src/Needs/NeedsApi.cs` (the shared surface every piece
codes against), and `docs/DEVELOPING.md` sections "Keeping saves working" and "Code map". The research the plan
rests on is summarised in the plan; if you need an engine fact, decompile: `DOTNET_ROOT="/c/Program Files/dotnet"
~/.dotnet/tools/ilspycmd -t <Type> "G:/Games/Vintagestory/Mods/VSSurvivalMod.dll"` (also VSEssentials.dll,
VintagestoryLib.dll, VintagestoryAPI.dll in G:/Games/Vintagestory).

Rules:

- Work only in your worktree (given in your prompt), on your branch. Never touch the main checkout or other
  worktrees. Commit on your branch with clear messages, staging only your own paths (`git add <paths>`, never
  `-A`). End commit messages with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Keep saves working (DEVELOPING.md): never rename or remove codes, classes or variant groups; new attributes have
  defaults; no worldgen change (no layout version).
- Build with `VINTAGE_STORY='G:\Games\Vintagestory' BACKROOMS_SCRATCH=<your scratch> bash tools/locked.sh mod
  <your tag>` from your worktree root (never plain `dotnet build` into bin/, the user's game may hold it). Asset
  generators run under `tools/locked.sh run python tools/<gen>.py` with `VINTAGE_STORY` set. Python that writes files
  uses `encoding="utf-8"`.
- Generators are the source of truth for generated JSON (`tools/gen_*.py` write `assets/backrooms/...`). Change the
  generator, run it, then discard CRLF-only churn (`git status` will show ~1,270 files after gen_detail.py; `git
  checkout -- <paths you did not mean to change>`; `git diff --stat` should list only your files).
- Headless test: `VintagestoryServer.exe --dataPath <scratch>/data --addModPath <scratch>/build-<tag>/Mods
  --withconfig "{ Port: <your port>, WorldConfig: { WorldType: 'backrooms', PlayStyle: 'backrooms', Seed: '12345' } }"`.
  Console lines need CRLF; in a piped .cmd use `ping -n <s+1> 127.0.0.1 >nul` as the delay and one command per
  `echo`. Never kill `VintagestoryServer` by image name (other agents run their own); kill your own PID.
  `/backrooms blocksweep` after adding blocks. The server log is `<data>/Logs/server-main.txt`.
- Lang: new keys go in `assets/backrooms/lang/en.json` (hand-written section; some generators merge their own
  `LANG` dicts, follow the file you touch). Do not edit the Spanish files unless your brief says so.
- When done: build clean (0 errors, no new warnings), run your headless check, commit, and report: what you built,
  file list, numbers you chose where the plan was silent, what you could not do, how you tested. Do not merge.

## A. Core (Opus)

Branch `needs-core`, worktree `../VS Backrooms-needs-core`, build tag `needs-core`, port 42781.

Own `src/Needs/` (replace `NeedsApi.cs`'s stubs with the implementation; keep every public member's name and
meaning, other pieces call them), plus the edits listed. Build:

1. `EntityBehaviorThirst` ("backrooms-thirst") and `EntityBehaviorFatigue` ("backrooms-fatigue"), registered in a
   `NeedsSystem : ModSystem` (`Start` both sides), added to the player with a JSON patch
   `assets/backrooms/patches/player-needs.json` on `game:entities/humanoid/player.json` (`/server/behaviors/-` and
   `/client/behaviors/-`; append, never insert). Both inert outside Backrooms worlds and when their setting is off
   (read live: `Needs.ThirstOn/FatigueOn`). Plan sections 3 and 4 give every number: drain shape (hunger's: 1.0/s
   moving, 1.5 sprinting, 0.25 idle after 3 s, times `SpeedOfTime*CalendarSpeedMul/30`, times the `thirstrate` stat
   blended), bands, walkspeed stats, damage at empty (0.2 per 6 s, Internal/Poison; add a death message lang key
   following the existing `prefixandcreature-*`/damage pattern you find for "died of thirst"), respawn values,
   Creative/Spectator exemption, awake-hours growth by calendar delta, caffeine pause and crash, the vanilla
   `tiredness` mapping (overwrite each tick), the sleeping branch (rest by `IRestPlace.RestQuality`, fall back to
   `Block.Attributes["sleepEfficiency"]` then 0.6 when the mount is a vanilla `BlockEntityBed`), the wake rules
   (rested, damage via `EntityBehaviorHealth.onDamaged`, menace within 6 blocks via `EntityBehaviorMenace.KindOf`,
   hunger/thirst under 10%) with chat messages (lang keys `backrooms:woke-rested`, `-pain`, `-menace`, `-thirst`,
   `-hunger`), `CanSleep` (refusal keys as in the API), and the one-time "You could sleep now" hint.
2. `Needs.SetStabilityOffset` registry summed into `EntityBehaviorTemporalStabilityAffected.stabilityOffset` once a
   second per online player; move `src/Regions/L974System.cs` lines ~348 and ~378 onto it (source "l974"); fatigue
   and thirst terms per plan section 5.
3. Director: `Needs.DirectorMult` per section 6; apply it in `src/Entities/MenaceSystem.cs` where `Setting.Spawns`
   feeds `EncounterRoll.Roll` and `BodyGapMs` (multiply there, nowhere else); the Wretch weight rule gains
   `Needs.Parched(target) || Needs.DeadOnFeet(target)`; `/backrooms ratecheck` gains an optional `awake=<hours>`
   argument. Night visits: a `MenaceSystem.NightVisit(IServerPlayer)` that places a Hunt-kind body from the level's
   roster 12 to 18 blocks away out of sight (reuse the existing hunter placement used by sent hunts), respecting the
   one-kind rule and hard gap and counting as the body; the fatigue behaviour rolls it per slept game hour outside the
   Safe band with `0.06 * Danger.OfLevel(level) * Setting.Spawns * doorFactor` (0.5 if a closed door block is within 4
   blocks of the bed; find how the mod detects closed doors, e.g. the Hound's door counter).
4. `HeatSystem`: `thirstrate` instead of `hungerrate` while thirst is on; rewrite its class comment.
5. `/backrooms heal` fills hydration and clears awake hours; `/backrooms stat thirst|rest <0-1>`; `/backrooms needs
   [player]`; `/backrooms needstest` (pure-math self-checks, prints PASS/FAIL lines). `tools/aitest/run.py`: cases
   `t_needs_selftest` (runs needstest, asserts all PASS) and `t_needs_boot` (server boots with the patch, no errors
   mentioning "needs" or "backrooms-thirst"/"-fatigue" in the log), in a `NEEDS_CASES` list wired into `main` with
   alias `needs`.
6. The one-time chat notice for worlds that lack the settings (player attribute `backrooms:needsNotice`), text per
   plan section 10. `docs/DEVELOPING.md`: add the commands to the Debugging list and the two settings to "Keeping
   saves working" as the stated exception.

Test headless: `/backrooms needstest` all PASS; `/backrooms stat thirst 0.1` then `/backrooms needs` shows the
band; with `/backrooms dummies on` and `ratecheck 1 heart 1 awake=70` the rates rise about 3x. Report the real
drain you measured over two minutes of a headless player (the console `/backrooms needs` on yourself via the
console player if that exists; else state that the drain was checked by the self-test only).

## B. Beds (Sonnet)

Branch `needs-beds`, worktree `../VS Backrooms-needs-beds`, build tag `needs-beds`, port 42782.

Plan section 8. Build `src/Needs/Beds/BlockBackroomsBed.cs` and `BlockEntityBackroomsBed.cs` (subclass vanilla
`BlockEntityBed`, implements `IRestPlace`; re-implement `IMountable.Position` and the seat members you need so a
one-block bed seats at the block centre and a two-block bed at the head's edge toward the foot; set
`EntityBehaviorTiredness.IsSleeping` on mount (enqueue on the main thread as vanilla does) and clear it on unmount;
no vanilla `RestPlayer` listener (if vanilla's `DidMount` registers it and you cannot avoid calling base, add a
Harmony prefix on `BlockEntityBed.RestPlayer` returning false for your type: Harmony is already referenced; follow
`src/Salvage/Protection.cs`); sneak unmounts; the sleeper is teleported beside the bed on unmount as vanilla does).
Register `api.RegisterBlockClass("BackroomsBed", ...)`, `api.RegisterBlockEntityClass("BackroomsBed", ...)`,
`api.RegisterMountable("backroomsbed", ...)` in a small `BedSystem : ModSystem`. Interaction: resolve foot to head
by the `bedFoot` attribute; create the block entity lazily if missing or if it is a plain vanilla `Bed`; call
`Needs.CanSleep(player, headPos)` and show its refusal (`TriggerIngameError` on the client side of a
`BlockBehavior`? no: do it in the block's `OnBlockInteractStart`, which runs on both sides; the server decides,
the client shows `not-tired-enough` from vanilla tiredness for the common case); mount via `TryMount`. Block info
("Sleep" help, `blockhelp` key) and `GetPlacedBlockInteractionHelp` never null.

Generators: set `class`, `entityClass` (on the head/single block only), `attributes.restQuality` and
`attributes.bedFoot` for every family in the plan's table: `tools/gen_blocktypes.py` (`bed-head`/`bed-foot`: read
`src/Worldgen/WorldGenerator.cs` near `Props.Bed` to learn which way the foot lies from the head for each side code,
and `gen_shapes.py` for the shape's orientation), `tools/gen_detail.py` (`improvbed`, `bedroll`, `sleepingbag`,
`hospitalbed`), `tools/gen_974.py` (`l974-bed`: switch class and entityClass to the mod's, keep `sleepEfficiency`),
`tools/gen_188_props.py` (`l188-bed`), `tools/gen_run.py` (`run-safecot`), `tools/gen_hub_tower.py` (`hub-cot`).
Regenerate each (under `tools/locked.sh run`), keep only the intended diffs. `src/Regions/L974System.cs` detects
sleeping via `MountedOn is BlockEntityBed`: your type subclasses it, so DreamSleep keeps working; verify the code
path and fix anything that casts to the vanilla block class. `src/Entities/MenaceSystem.cs` rest check
(`MountedOn is BlockEntityBed`) likewise.

Carpet bedroll: block `carpetbedroll-{north,east,south,west}` (hand-written JSON under
`assets/backrooms/blocktypes/needs/`, or add to gen_detail.py if that is cleaner), the `block/detail/bedroll` shape
with Level 0's chevron carpet texture (find the carpet texture the `carpet` block uses), `BlockBehaviorOrientable`
(the mod's own, `src/BlockBehaviorOrientable.cs`), drops itself, restQuality 0.6, single part; the matching item
(a block item is enough: the block in the inventory), recipe `assets/backrooms/recipes/grid/carpetbedroll.json`
shaped `FF / WW / FF` (F `backrooms:carpetfibre`, W `backrooms:wallpaperstrip`); lang `block-carpetbedroll-*` "Carpet
bedroll", a `blockdesc`. Run `/backrooms blocksweep` headless.

Test headless with a console-driven player if the harness has one (see `tools/aitest/run.py` for dummies; dummies
cannot mount). At minimum: boot clean, blocksweep clean, the recipe loads (no recipe errors in the log), and a unit
check that every bed family's head/foot resolution is right (a `/backrooms bedtest x y z` command that reports the
head position, quality and seat position for the bed at a position; run it against a Level 5 hotel bed found with
`/backrooms nearest`/`find` if available; otherwise against a bed you place with `/backrooms` block commands).

## C. Drinks and water (Sonnet)

Branch `needs-water`, worktree `../VS Backrooms-needs-water`, build tag `needs-water`, port 42783.

Plan section 3 (drinks, world water, bottles, supply) and 11. Build:

1. `src/Reality/RealitySystem.cs` `ItemAlmondWater`: generalise into the drink class (keep the registered name
   `BackroomsAlmondWater`): `GetNutritionProperties` returns a copy with satiety from `attributes.satietyWhenThirst`
   when thirst is on and the attribute exists; `tryEatStop` on the server, when the stack shrank: stability restore
   as today, `Needs.Hydrate(entity, attributes.hydration)`, `Needs.MakeDrowsy` if `attributes.sleepAid`,
   `Needs.Caffeinate(entity, attributes.caffeineHours)` if present, `Needs.MakeSick(entity, 10)` with the
   `attributes.taintChance` roll, and give back `attributes.leavesBottle` (`backrooms:emptybottle`) when thirst is on
   (into the inventory, else drop). Held item info gains "Hydration: N%" (and the stability line if not already). Add
   the attributes to every item in the plan's table; give `waterbottle` the class. Items with their own classes
   (`redwater`, `end-memoryjuice`, `fun-lucatears`) call `Needs.Hydrate` from their own `tryEatStop`.
2. New items: `almondwaterblue`, `almondwatergreen` (textures: tint the Almond Water texture blue/green with a small
   Python step in a new `tools/gen_needs.py`, keep the label readable), `emptybottle` (the bottle shape without the
   liquid, or a desaturated variant), `bottledwater-{clean,murky,salt}` (a `variantgroups` item `bottledwater` with
   `kind`, the Almond Water shape re-coloured: clear, brown, grey-green), with `combustibleProps` on murky as in the
   plan. Lang names and descriptions.
3. World water: `src/Needs/Water/WaterClass.cs` (`At(world, layout, pos)` by level and block per the plan's table;
   use `BackroomsWorld.CreateLayout`'s `LevelAt`, `Block.LiquidCode` for boiling), `BlockBehaviorDrinkable` added in
   `AssetsFinalize` on both sides to every block whose `LiquidCode` is water, saltwater or boilingwater (the server
   adds it to `BlockBehaviors`; behaviours added in AssetsFinalize are not sent to clients, so add on the client too):
   start only with empty hands and thirst on, hold one second (`OnBlockInteractStep` returns true until 1.0 s, with
   the eat animation and the player's "drink" sound as `ItemAlmondWater` does), stop on the server applies the class
   effect and sends the message. Client: `ForceLiquidSelectable` on while thirst is on and the active hotbar slot is
   empty (toggle each tick in a client system; restore when not). Also the empty bottle's `OnHeldInteractStart` on a
   liquid block (item `liquidSelectable: true`) fills it by class.
4. Supply: `src/Props/Dispensers.cs` restock rule per plan (drinks: no restock while thirst is on, except
   `almondseep*`: 14 days, 1 to 3 portions); `assets/backrooms/blocktypes/supplybox.json` and `level1/crate.json`
   add Blue and Green at 0.05 each; `tools/salvage.py` `drinkfridge` and `vendorcart` lists add both (regenerate the
   affected blocktypes under the lock; keep only intended diffs); `src/Entities/Rewards.cs` and
   `src/Regions/HubSystem.cs` `IsLoot` lists learn `almondwaterblue`, `almondwatergreen`, `bottledwater*`,
   `emptybottle`; `tools/gen_entities.py` Wanderer trade adds Blue and Green (price 2, stock 2, stack 1); regenerate
   `wanderer.json` under the lock.
5. `ScarcitySystem`: confirm drinks with satiety 0 still count as food for scaling (they have `nutritionProps`) and
   that nothing divides by satiety.

Test headless: boot clean; `/backrooms kit` or a give command to hold Almond Water and the log shows no errors;
`blocksweep`; verify by code reading that `BlockBehaviorDrinkable` is on `game:water-still-7` on both sides (log a
count at AssetsFinalize). Report the hydration-per-box arithmetic for Level 0 and Level 1 with the new tables.

## D. HUD and client (Sonnet)

Branch `needs-hud`, worktree `../VS Backrooms-needs-hud`, build tag `needs-hud`, port 42784.

Plan section 7 and the cheat buttons of section 12. Build `src/Needs/HudNeeds.cs` (client; opened from a client
`ModSystem` once the own player's data has arrived; `TryOpen`; recompose on `OnOwnPlayerDataReceived`), with the
exact bounds, colours, hover texts, flash rule, oxygen-aware Rest offset, hide rules (mechanic off, Creative,
Spectator) from the plan. Values from `Needs.Hydration/MaxHydration` and `Needs.RestFraction` (the API reads the
watched trees; they may be null for a moment after join: compose unconditionally and show full). Exhaustion visuals
in `src/AtmosphereSystem.cs` (client): from `Needs.DeadOnFeet`/`AwakeHours` and not `Caffeinated`: dim the ambient
up to 25% and desaturate slightly (follow how the Flickering darkening is applied there), and a blink (0.3 s dark)
every 30 to 60 s. Cheat menu `src/Cheats/GuiDialogCheats.cs` Player tab: buttons "Thirst 10%" (`/backrooms stat
thirst 0.1`), "Rest 10%" (`/backrooms stat rest 0.1`), "Drowsy" (`/backrooms stat rest 0.58`), "Dead tired"
(`/backrooms stat rest 0`), "Needs" (`/backrooms needs`); `src/Cheats/HudCheatInfo.cs` debug HUD gains a line
"hydration N awake H h (band)". The commands themselves are piece A's; the buttons just send the strings.

Test: build clean; a real client is not available to you, so verify by reading `HudStatbar`'s decompiled layout
against your bounds and by a headless boot (the client system must not throw on the server, so guard with
`ShouldLoad(EnumAppSide.Client)`).

## E. Glass spear (Sonnet)

Branch `needs-spear`, worktree `../VS Backrooms-needs-spear`, build tag `needs-spear`, port 42785.

Plan section 9. Item `assets/backrooms/itemtypes/salvage/glassspear.json`, projectile entity
`assets/backrooms/entities/projectile/glassspear.json` (copy vanilla
`G:/Games/Vintagestory/assets/survival/entities/nonliving/projectile/spear.json` for the flint variant, flatten the
variants, class `EntityProjectile`, the mod's shape), shape `assets/backrooms/shapes/item/glassspear.json` (copy
vanilla `shapes/item/tool/spear/stone.json`, rename texture codes so the head uses the glass shard's texture and the
shaft a stick/wood texture; check `tools/gen_shapes.py` conventions but a hand-written JSON is fine here), recipe
`assets/backrooms/recipes/grid/glassspear.json` shaped 1x3 (`G` glassshard / `F` carpetfibre / `S` game:stick),
lang `item-glassspear` "Glass spear", `itemdesc-glassspear` (flimsy, sharp, a dozen hits), creative inventory like
`glassshiv`. Handbook: in `tools/gen_guide.py` add one line to the "salvage" page's recipe list ("Glass spear =
glass shard + carpet fibre + stick") and to `tools/gen_notes.py` FACTS the phrase `glass shard + carpet fibre + stick`;
regenerate the guide under the lock (`python tools/gen_guide.py`) and run `python tools/gen_notes.py --check`.
Headless: boot clean, give yourself the item in a console test if possible, check the log for shape/texture errors.
Report the stats you set.

## F. Docs (Haiku)

Branch `needs-docs`, worktree `../VS Backrooms-needs-docs`, build tag `needs-docs` (no build needed unless a
generator is run), no port.

Plan sections 1 to 10 are the facts; write for players in the voice of the existing text. Edits:

1. `tools/gen_guide.py`: rewrite PAGES["food"] (title it "Food and water": there is thirst now; drinks, hydration,
   world water by class in plain words without level spoilers beyond what the page already gives, bottles, boiling,
   heat makes you thirsty); add PAGES["rest"] ("Rest and sleep": the clock in real minutes, drowsy/exhausted/dead on
   your feet, what each costs, beds and the carpet bedroll recipe "4 carpet fibres + 2 wallpaper strips", what wakes
   you, night visits and shut doors, Blue and Green Almond Water); "stability" page: a sentence on fatigue and thirst
   draining it; "starter" page: a sentence on water and sleep; "home" page: a bed at home. Keep every FACTS phrase of
   `tools/gen_notes.py` intact and add `4 carpet fibres + 2 wallpaper strips`. Regenerate under the lock, run
   `python tools/gen_notes.py --check`.
2. `assets/game/lang/worldconfig-en.json` (+ the same English text in `worldconfig-es-es.json` and
   `worldconfig-es-419.json`): the two settings per plan section 10.
3. `assets/backrooms/lang/es-es.json` and `es-419.json`: remove the stale `guide-food-text` and `guide-stability-text`
   keys so English shows (the project's rule for changed text).
4. `docs/GUIDE.md`: "Surviving" gets water and rest subsections mirroring the handbook; the world settings list gets
   Thirst and Fatigue; the Reality Stability section gets the fatigue line. `README.md` line 9 (hunger) mentions
   thirst and sleep. `CHANGELOG.md` under `## Unreleased`: one bullet each for thirst, fatigue and sleep, beds and the
   carpet bedroll, Blue and Green Almond Water, bottles and boiling, the glass spear, water supply, the two settings
   (old worlds get both on). `docs/moddb-description.md` and `.html`: a "Thirst and sleep" paragraph in the features
   and the settings list.
5. `docs/design/README.md` index: a row for `needs/`.

Commit. Report the pages you wrote (paste the handbook "rest" page text in your report).
