# Player-feedback round, 2026-11 (0.700.0-pre.10)

The mod page's comments of 3 to 10 November 2026, reviewed on 13 November. Everything here ships in the 0.700 branch
(`experimental-levels`) only. The new-world parts take **layout version 16** on this branch (15 is its food round, main's 14
is the 0.611 review), so main's next layout bump is **17**; the new levels' balance of pre.11 reads it in every world from
pre.13 (see below). Built in four packages (`exp/fb-late`, `exp/fb-small`, `exp/fb-armour`,
`exp/fb-props`) and merged together for pre.10.

## What players said, and what the code showed

- **"The late game is punishing" (Hounds in Levels 8 and 9).** At Normal, spawns 5.5 (the dial-in's old High), a Hound pack
  reached a player in Levels 8 and 9 about every 45 s to 2 min, against 3 to 25 min in Levels 1 to 5. A full cap still let one
  Hound through (`max(1, cap - present)`).
- **"I can't find the way to the city".** Level 10's noclip wall was in about one barn in nine (layout 12 on), a typical search of
  5.6 km, and the notes still said "a little under half".
- **"No way back from the Suburbs".** The Suburbs door you arrive beside from a city rowhouse was a plain locked door with no
  threshold (every world since layout 9); the pry bar just deleted it.
- **"Carpet armour and bags are useless".** Gambeson, sewn from Level 0's carpet fibre, beat sewn leather and bronze lamellar, and
  three wanderer lists sold it. Pleather turned only about a fifth of a blow.
- **Smaller:** butter was only edible in meals; no borax anywhere; vanilla drinks gave no water; Facelings shoved for no visible
  reason; nothing dropped rot for a farm; the props were decoration only.

## Decisions (the user's, 2026-11-13)

1. **Hounds in Levels 8 and 9:** their share of what comes is halved (Level 9 1.0 to 0.5, Level 8 0.5 to 0.25); one pack at a time
   per player or party, then a quiet spell of 3 to 5 minutes at Normal (scaled by the spawn setting and party size); a second pack
   only rarely (5 %), in Level 8's worst off-road ground and Level 9's threshold band and dens. A full cap now sends nothing.
2. **Barns:** one in five has the wall in new worlds; the wall shows (orange seams, a faint glow at night, the city's hum within
   about 30 blocks); the notes search farther; the stale wording is fixed.
3. **City rowhouses:** a door that leads to Level 9 is the Suburbs' red door with a lamp behind its glass (every world); from layout
   16 one in four leads there and the rest are the city's own locked front door. The way back is fixed in every world, and the pry
   bar refuses a door that leads somewhere.
4. **Armour is a trade-off, not a must.** Metal is loud: chain, lamellar, brigandine and scale are heard 40 % farther as you run,
   plate twice as far, and both clank as you walk (sneaking halves it); cloth, carpet and leather are silent.
5. **The carpet ladder:** twine costs 18 carpet fibre; crouching with a blade cuts a whole carpet square and leaves bare floor;
   carpet armour (squares, fibre, twine) stops what a leather jerkin does (0.4 / 0.25, tier 1); bedrolls take squares; the carpet
   bag holds 4 and (the user, later the same day) is 4 squares + 2 fibres, no twine, so four bags cost about 20 cuts, not
   about 46; gambeson (linen) comes next. Wanderers no longer sell gambeson.
6. **Pleather is retired.** Its codes stay registered and hidden; every pleather stack in an old world is remapped once at load
   (`config/remaps.json`, the game's own remapper): pleather to carpet squares, each pleather piece to the same carpet piece.
   Chairs, sofas and car seats give cloth instead.
7. **Food and needs:** butter is out of iceboxes and Kitty's fridge (more cheese, Almond Milk); flour and salt stay with a handbook
   line. Vanilla drinks fill the water bar per litre (water and juice 600 of 1500, milk 500, cider/wine/mead 300, spirits 50,
   vinegar -200). Torn supply boxes and emptied crates drop rot about 1 in 6.
8. **Borax:** washing machines drop it about 15 % of the time (every world); Level 8 holds more borax ore in new worlds (layout 16).
9. **Facelings** keep the noise shove but stare at you for a second first; the handbook explains it, and that Level 3's half-faced
   Evolved attack.
10. **Working props** (every world, no worldgen): fire alarms ring 25 s and set off the sprinklers within 12 blocks (fires and torches
    go out, Deathmoths react); steam valves scald a corridor for 5 s (about 10 damage); breakers really put a section's lights out
    until a new `fuse` (or a day) restores them; car alarms, radios, record players and a new wind-up alarm clock are lures.
11. **Not now:** loneliness hallucinations.

## Changelog, 0.700.0-pre.10

- Hounds in Levels 8 and 9 come about half as often, one pack at a time, with a quiet spell after each.
- The way back from the Suburbs to the city works again, in every world; the pry bar no longer destroys a working door.
- City rowhouse doors that lead to the Suburbs are marked by a red door and a lamp; in new worlds only a quarter lead there.
- One Level 10 barn in five has the way to the city in new worlds, and you can see, and at night hear, which.
- Carpet: twine costs 18 fibre; crouch to cut whole carpet squares; new carpet armour; bedrolls from squares; a 4-slot carpet bag.
- Pleather is gone; any you have becomes carpet squares and carpet armour. Seats give cloth.
- Metal armour is loud. Wanderers no longer sell gambeson.
- Vanilla drinks fill the water bar. Butter is replaced by cheese and Almond Milk. Borax from washers and in Level 8. Rot from
  torn boxes.
- Facelings stare before they shove.
- Fire alarms and sprinklers, steam valves, breakers and fuses, car alarms, radios and alarm clocks all work.

## After pre.10

- The carpet bag is 4 carpet squares + 2 carpet fibres (it was 5 fibres + a twine, 23 fibres a bag). The tutorial's bag
  steps follow: cut 4 squares, cut 2 fibres, craft the bag (its twine step is gone).

- **Balance of the new levels (0.700.0-pre.11).** A read-only review of the ten new levels (reports kept by the lead) found
  resources too easy to come by and shortcuts built at full rate; the user's calls: fix them, shortcuts rarer but lore kept,
  Level 52 far fewer trees, Level 73's table once per player.
  - All worlds: Basement food x0.25 (was x0.5); Level 36 food x0.35 (its ways in are Levels 9 and 11); Level 14's caches pay the
    Level 4-6 pool (no bronze, iron or temporal gears); Level 15's seats, curtains, lockers and corpses give carpet fibre, not
    twine; Level 120's racks and wrecks half the scrap wire and circuit boards; Level 31's server every 12 game hours (was 6)
    with Almond Water 30 % (was 60 %); Level 52's snack machines never restock; Level 73's table feeds each player once per 12
    game hours; Coran's kills leave no carcass; Level 23's amphorae a third of the clay, its water clean only in the Heart's
    pool and Base Seedling (puddles tainted); green giant bark gives firewood, not planks; Level 47's moose follow the food
    setting and class; Black Shuck hide 0.5 (was 1.5).
  - Layout 16, and from 0.700.0-pre.13 in every world (the user's decision of 2026-11-13: older worlds get the new levels'
    ways in, so they get these new levels' rules too; `WorldLayout.ExpVersion`, LINKS.md "Layout 16"; the released levels'
    own layout 16 changes above, barns, rowhouse doors and borax, stay new worlds only): the Basement's food props found stripped (0.75), its workshop tools about a thirteenth (1.45 to
    0.11 whole tools a cell) and seed sacks a seventh; Level 52's trees a fifth (shrubs where they were) and its shelves
    stripped at Level 4's share; the earlier-to-later shortcuts a quarter as common: Level 31's revolving doors, Level 15's
    pane to 11, stairs to 4 and MEDICAL CENTER door, Level 14's collapse to 73, Level 6's deepest dark to 73 (at least one
    kept), Level 36's flights to 10 and 11 (see LINKS.md "Layout 16"). Level 0's EMERGENCY EXIT to 14 was already built rare
    and is unchanged.
  - Headless group `--only bal` in tools/aitest/run.py checks the table, Coran, the drops, Level 14's pool, Level 23's water and
    Level 52's machines.
- Carpet armour's cap wears the gambeson's hood (the jerkin has no head shape); the jerkin and leggings show the carpet.

- **0.700.0-pre.13: the item pass and new clothes** (a mod-page comment of 2026-11-13 asked for "more refined items, with
  actual models" and modern, lab and hazmat clothing; the user: model pass yes, lab coat and hazmat yes, modern clothes yes, no
  firearms). 81 of the 82 items drawn as flat sprites got real 3D models (only the retired pleather stays flat), and the crude
  ones were remade: Almond Water and its bottle family, canned beans, crackers, the Lobby's salvage and tools, notes, chalk,
  cards and the levels' own food. Generators `tools/gen_items_{salvage,pantry,treats,paper,wear}.py`; the gate's `lang` stage
  fails on a new flat item (`tools/itemcheck.py`). New wearables: t-shirts, jeans, a hoodie, a work jacket, sneakers, work
  boots, a cap (cosmetic, a little warmth; dressers, wardrobes, racks, suitcases, luggage, backpacks), a lab coat (Level 14 and
  15 lockers, Level 120 shelves) and a hazmat suit and hood (rare; 75 % off Level 14's contamination poison and stability
  drain, the hood slows the Basement's smell of the dead; hot and a little slow, no armour, wears out). Loot is rolled at
  runtime, so every world gets it. The Spanish is written for every key (machine-made, to be reviewed); the Basement's
  emptied icebox has its own block.
- **0.700.0-pre.14: the 2026-11b review and the decisions round** (2026-11-14). The held items checked from the front in the
  client (treats, notes and chalk held in the palm), the whole-project review of pre.13 (review/2026-11b) and the user's
  answers to the ten levels' open questions, built (D1-D13, D15; docs/design/experimental-levels/OPEN-QUESTIONS.md).

## Known gaps

- The Spanish is machine-made and wants a native reader's review.
- Held items are checked in third person only, from the front on the side of the right hand (all 105 items, 2026-11-14; the game draws the first-person hand with the same transform; the rig's first-person shot shows no hand).
- The smallest salvage (ceramic grit, rubble, moth jelly, glass shard) and the wrapped sweet sit mostly inside the fist in third person, as vanilla's stones and fat, whose holds they copy.
- Restart resets the props' cooldowns (in memory); tripped breakers persist.
- A converted pleather piece keeps its remaining uses, not its share (full pleather shows as 175/250 carpet armour).
