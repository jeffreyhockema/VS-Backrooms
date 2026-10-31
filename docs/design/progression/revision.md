# Progression revision: no depth drain

Written 2026-10-25 from the user's play-test of 0.610.0 ("it's so common to find a path to later levels, then your
stability gear spins like crazy with no explanation; the mechanic feels wrong; doors and exits are too plentiful") and
their answers the same evening ([decisions.md](decisions.md) items 18 to 24). Branch `progression2`, worktree
`../VS Backrooms-prog2`. Still 0.610.0 (unpublished).

## 1. Decisions

| # | Decision |
|---|---|
| 18 | **The depth drain, the ward tiers, the anchors, the Almond Water ceiling and the "What holds you here" page are removed.** Lethality, armour, ore only in Level 8, needs and scarcity are the gate |
| 19 | **The blackout at zero stability stays, from any cause** (pockets, Reality Shifts, exhaustion), and so does the hunter sent at zero; neither depends on a tier |
| 20 | **Earlier-to-later shortcuts become about a quarter as common**; later-to-earlier ways stay; no new one-way ways. Ring-boundary gates keep their count. New chunks only, behind layout version 12 |
| 21 | **Scarcity deepens with the levels**: Almond Water and food in caches and dispensers thin out in Class 3 to 5 levels, on top of the world setting |
| 22 | **Lethality curve unchanged** (2 blows unarmoured at Level 3, 1-2 by Level 8; hunters outrun a sprint from Level 3). Play-test before pushing |
| 23 | **Telegraph the danger in-world**, in four voices: M.E.G. placards at boundary gates into a higher class, a story note at the first such gate, wanderer dialogue, a chat line on crossing |
| 24 | Ways down stay findable (chalk arrows unchanged) |

## 2. Pieces

### A. Remove the drain (sonnet, branch `prog2/undrain`)

Per the inventory (tracker.md "Inventory 2026-10-25"): delete `src/Reality/Wards.cs` (WardTiers), `WorldLayout.WardTier`/`WardTierAt`
(`WorldLayout.Reality.cs`), `DepthDeficit`/`PlayerAt` and the deficit line in `RealitySystem.OnGetStability` (restore the
clamp to its pre-round values), `src/Reality/RealitySystem.Ward.cs` and its registration, the "Ward tier" cheat button,
`tools/gen_wards.py` and every anchor asset (itemtypes/ward/anchor.json, the three recipes, six textures), the anchor and
`guide-holds-*` lang keys in all three lang files, `"holds"` in `GuideSystem.Added[]`. `Drinks.ApplyDrink` goes back to a
plain restore clamped to 1. `ZeroSystem`: the hunter is sent at zero wherever the band is not Safe (no `Beyond` gate), the
blackout stays as is (any cause; not in Level 0, the Hub, 974, the Snackrooms); `WakeLevel` and `SafePlace` move into
ZeroSystem. Harness: drop `prog-ward` and the `_ward` helper; keep `prog-zero` (hunter + move) and `prog-zero-safe`, fixing
them for the new condition. Temporal gears stay as trade goods and spawn-setters (the cache `EarlyGearChance` and the
wanderer gear at 6 stay: a gear is still worth having for a bed-less respawn point). Comments and XML docs that mention
tiers go. Build, `--only prog,iso,needs`, report in tracker.md "### Revision: piece A".

### B. Shortcuts, scarcity, placards, chat line (sonnet, branch `prog2/world`)

- **Layout version 12** (`WorldLayout.CurrentVersion`): every change below is `Version >= 12` so existing chunks are
  untouched (layout hashes for v1/v9/v10/v11 must not change: check with the mapgen harness as earlier rounds did).
- **Shortcuts to a quarter** (earlier -> later only; the later -> earlier ways and the Hub, 974, 188 and 3999 links stay):
  Level 0 pit rooms 10 % -> 2.5 %; Level 1 stairs down to Level 2 25 % -> 6 %, up to Level 4 15 % -> 4 %, stair core to
  Fun 1 in 20 -> 1 in 80, EXIT doors to Level ! and doors to The End a quarter of today's; Level 2 steel doors: the shares
  to Levels 3 and 4 quartered (the share to Level 1 kept, the remainder closed); Level 3 elevators to 4 and 5 and locked
  doors to 5 quartered (the rest same-level); Level 4 elevators to 5 quartered, hungry vending 6 % -> 1.5 %; Level 5
  staff stairs to 6 and POOL doors a quarter; Level 6 stairwells to 7 and tripwires a quarter; Level 7 stone circles,
  tiled seabed and cave mouths a quarter; Level 9 field gates one per four Field lots, pool dives 6 % -> 1.5 %; Level 10
  barn walls 45 % -> 11 %. Where a quarter would leave a level with no way down within a 10x10-cell block, keep at least
  one (the boundary gates remain the normal way). Record the before/after per-threshold counts from the mapgen `links`
  or `deep` mode in the tracker.
- **Scarcity by class**: a `Roster.LoreClass`-based factor on Almond Water and food in caches, crates, supply boxes and
  the one-time dispenser stocks: Class 0-2 x1, Class 3 x0.7, Class 4 x0.5, Class 5 x0.35, multiplied with the existing
  `ScarcitySystem.FoodScale`. Refilling dispensers (fountain spouts, seeps, pumps, Snackrooms, carts, milk vans) keep
  their refill but their stock takes the same factor. Level 94's and the Snackrooms' abundance are deliberate: exempt
  them (and the Hub, 974). Document the factor in one place (`ScarcitySystem.ClassScale(level)`).
- **Placards**: a wall plate block `backrooms:megplacard-<n>` (one shape, texture per class, generated like the Level 1
  NO ENTRY plate in `tools/gen_detail.py` or `gen_lore.py`) placed by worldgen at every ring-boundary gate whose far side
  has a higher `LoreClass` than the near side (`WorldLayout.Gates.cs OpenGate`, Version >= 12), on the near-side wall
  beside the opening, facing the approach. Text on the plate: "M.E.G. — LEVEL <n> — CLASS <c>" and a second line:
  Class 3 "THINGS HERE OUTRUN YOU", Class 4 "ARMOUR OR DON'T", Class 5 "NO UNARMOURED TRAVEL". Also at the shortcuts
  that lead deeper where a wall is at hand (steel doors, stairwells, elevators), as the same plate; where there is no
  wall (pits, tripwires, seabed) nothing.
- **Chat line on crossing**: `MenaceSystem` (or a small `CrossingSystem`) notices a player's level change to a higher
  LoreClass and, once per level per session, says (lang key) e.g. "Level 3. Everything here is faster than you and
  hits harder. In flint and cloth you will not outrun it." The armour clause is chosen from the worn set's tier
  (`MenaceSystem.Armour.cs` can read the player's worn armour; reuse its protection reading). A second line for Class 5.
- Build, mapgen hash check, `--only iso,p7,felt`, a headless `dump` of one v12 gate with its placard, report in
  tracker.md "### Revision: piece B".

### C. Text (haiku, branch `prog2/docs`)

- `tools/gen_guide.py`: remove the "What holds you here" page and every tier/anchor sentence (the levels page tier tags
  "*Stone, tier 0*" etc., the entities armour bullet's half-tier line, the home page's anchor mentions, the salvage
  page's gear-for-anchors sentence); keep temporal gears as spawn-setters; add to the entities page the placards and
  what the classes mean, and to the food page that food and Almond Water thin out from Class 3 down. `gen_guide.py` and
  `gen_notes.py --check` must pass.
- **Story note**: one new ordered note in `tools/gen_notes.py` for the first gate into a higher class (piece B places the
  note's marker spot; coordinate the key name `note-gate-class` with B): a wanderer who went down in flint and pleather,
  what met them, "come back with metal on you".
- **Wanderer dialogue** (`tools/gen_dialogue.py`): the camp and outpost traders answer "What lives around here?" with a
  line about the classes and armour; the gear line stays.
- `docs/GUIDE.md`, `README.md`, `CHANGELOG.md` (the 0.610.0 "The climb." bullet becomes the new gate: placards,
  classes, scarcity, armour; no anchors), `docs/moddb-description.md/.html` (the "climb" bullets and cards reworded; no
  anchors), `docs/design/entity-difficulty.md` section 5, `playtest.md` section 11 (rewritten: placards, the chat line,
  scarcity, Level 3 in pleather vs leather, shortcuts rarer, blackout in a pocket), `plan.md` status note at the top
  pointing here, `decisions.md` items 18-24 (from this file), `DEVELOPING.md`, `handbook-audit-0.610.md` addendum.

## 3. Gates before the zip

Harness full set; mapgen layout hashes v1/v9/v10/v11 unchanged and v12 recorded; a copy of an existing world loads;
`gen_notes --check`; the three lang files parse; zip rebuilt as 0.610.0.
