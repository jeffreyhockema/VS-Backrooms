# Experimental levels: the candidate list

The user's list of levels to try (2026-10-17). Each gets a cheap prototype on this branch, a few at a time; the
rest wait here. Tick a level off (move it to "Built") when its commit lands.

## Built

| Level | Id | Batch |
|---|---|---|
| Level 73 "The Redlands" | 21 | 1 |
| The Basement (unnumbered) | 22 | 1 |
| Level 52 "School Halls" | 23 | 1 |
| Level 31 "Roller Rink" | 24 | 2 |
| Level 120 "Server Room" (Wikidot "Broken Servos") | 26 | 2 |
| Level 36 "Airport" (scaffolded; detail pass to come) | 25 | 3 |
| Level 15 "Futuristic Halls" (scaffolded; detail pass to come) | 27 | 3 |
| Level 23 "Petrified Garden" (scaffolded; detail pass to come) | 28 | 3 |

## Dropped

| Level | Id | Why |
|---|---|---|
| Level 55 "Land of Ice" | 25 (now Level 36) | on neither main lore wiki as built; the user dropped it (2026-10-30). Plan kept in `dropped/55-plan.md`. |
| Level 183 "Clean Sewers" | 27 (now Level 15) | the same. Plan kept in `dropped/183-plan.md`. |

None has been played in a client yet; each plan's Status section lists what to check in-game.

## Regions

All eight levels' regions are in the table at the top of [README.md](README.md).

## Waiting

| Level | Notes |
|---|---|
| Level 28 "Stormstone Keep" | a second castle; wait until Level 73's Silver Castle has been judged |
| Level 68 "Theater, The Eater" | |
| Level 70 "Deposit" | |
| Level 72 "Call of the Crabs" | beach; crabs would be an entity |
| Level 108 "Spire Complex" | |
| Level 119 "Average Waterpark" | could reuse Level 37's pool blocks |
| Level 242 "Fields of Rot" | could reuse Level 10's farms |
| Level 276 "The Hive" | organic; likely the most expensive to make look right |
| Level 352 "bHZsMzUy" | the name is base64 for "lvl352" |
| Level 402 "Plastic City" | a city; expensive, Level 11 machinery could be reused |
| Level 404 "My Dearly Fragmented" | glitch level |

Free region slots after batch 3: none of the `R * 1.1` or `F` diagonal slots is left (73, the Basement, 52, 31, 36,
188 hold the eight `R * 1.1` directions but east-north-east and east-south-east, which the city fills; 120, 15, 23 and
3999 hold the four far diagonals). New regions go to other radii: check `overview` for overlaps (the city east of spawn
is huge, radius up to 0.72 R).

## Reserved values

See [README.md](README.md), "Reserved values" (2026-10-30): the enums and Tile.Under/Overhead/Pipe are ushorts now,
each level has a block of 32 past 255 in every table and a block of 100 props, and `python tools/expclash.py` checks it.
Main's values never move; check for clashes at every merge of main (`expclash.py`, and `layouthash` for 0-20).
