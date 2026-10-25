# Progression pressure: tracker

Reports from the pieces of [plan.md](plan.md), newest last.

### Piece C (resources)

Branch `prog/resources`. What changed:

- **Ore only in Level 8.** `UndergroundSystem.Borrow` wraps the borrowed `GenDeposits` column handler: for a chunk column whose middle lies in a macro cell that is not Level 8 it returns without generating deposits (ore, coal, minerals). Rock, caves and Level 8's own strata and ore (`WorldGenerator.Deep`) are untouched; soil deposits were already left out. Generated chunks keep what they have. `BackroomsModSystem.Layout` is a new public getter. `/backrooms ground` now also prints the level of the column (and works for a probe from the console).
- **Pleather.** `backrooms:pleather` (dark vinyl icon, `gen_breakdown.py`, like `rubble`), 1 to 2 from Level 1 wrecked cars (`Breakdown.Wreck`, C#), Level 4 office chairs (and tipped), Level 5 hotel chairs, wing chairs, sofas and long sofas (`salvage.py`). Armour `backrooms:armor-pleather-head/body/legs` reuses vanilla's leather shapes with a black recolour of vanilla's leather skin; recipes 5/7/6 pleather (no twine), repair recipes in vanilla's `armorrepair` pattern with pleather only. No vanilla recipe wildcard matches `pleather` (grepped `survival/recipes`).
- **Rat hides.** Death Rat's `game:hide-raw-small` drop was already 0.5 (every level); now 0.33 mean.
- **Wanderer** sells `game:gear-temporal` for 3 rusty gears (stock 1). Candles were already sold (1 rusty gear each).
- **Caches.** Levels 1 to 5: 12 % of a cache's "extra" is a temporal gear (`Rewards.EarlyGearChance`; the Level 1-6 pools had none before, Level 7+ keeps its 6 %). Toolboxes already held only a copper hammer (0.06), chisel (0.04), saw (0.04) and knife (0.08), never a pickaxe: left as they are.

Numbers, pleather against leather (vanilla "sewn" set, per piece): relative protection 0.24 against 0.60, flat reduction 0.24 against 0.60 (40 %), tier 1 both, durability 175 against 700 (a quarter). Cost: 5/7/6 pleather against 7/22/11 leather (+ twine).

Trade price: a Hound's bounty is 0.25 + danger rusty gears (0.4 at Level 1, 0.6 at Level 3, 0.8 at Level 5, doubled for an old one), so 3 gears is about four to five mid-level Hound kills.

Ore verification (headless, seed 12345, `/backrooms ground`): Level 0 column 512000,512000: y1-207 only `rock` and air, no `ore-*`; Level 8 column 516000,512000: bituminous coal, lignite, galena, native copper, sphalerite, cassiterite, hematite, quartz, olivine and so on. Startup log shows no errors.

Could not check: the pleather armour on a client (model, texture, repair, handbook), the recipe grid in game, the wanderer's trade window, rat drop counts in play (no `harvesttest` run; `harvesttest` needs a player), ore under a level boundary chunk (a column straddling Level 8's edge takes its middle's level).

Lessons: `tools/locked.sh run python gen_detail.py` and `gen_blocktypes.py` rewrite hundreds of files (EOL) and also pull drift from `salvage.py` into unrelated blocks (backpack, tent, camptent, seachest, desk, filing cabinet, writing desk, clump remnant): revert them with `git checkout HEAD --`; only `git diff --stat` shows real changes.
