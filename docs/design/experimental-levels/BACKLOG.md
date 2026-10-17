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
| Level 55 "Land of Ice" (on neither wiki; built from the name) | 25 | 2 |
| Level 120 "Server Room" (Wikidot "Broken Servos") | 26 | 2 |
| Level 183 "Clean Sewers" (on neither wiki; built from the name) | 27 | 2 |

None has been played in a client yet; each plan's Status section lists what to check in-game.

## Batch 2 regions (built 2026-10-17)

| Level | Id | Tag | Constant | Region |
|---|---|---|---|---|
| Level 31 "Roller Rink" | 24 | 31 (`l31-`) | `WorldLayout.Level31` | west-north-west, `R * 1.1` out, 22.5 degrees north of west |
| Level 55 "Land of Ice" | 25 | 55 (`l55-`) | `WorldLayout.Level55` | west-south-west, `R * 1.1` out, 22.5 degrees south of west |
| Level 120 "Server Room" | 26 | 120 (`l120-`) | `WorldLayout.Level120` | far north-east beyond Level Fun: `spawn + (+F, -F)`, `F = round(R * 1.6 / sqrt 2)` (as Level 3999 lies beyond the Hub) |
| Level 183 "Clean Sewers" | 27 | 183 (`l183-`) | `WorldLayout.Level183` | far north-west beyond The End: `spawn + (-F, -F)` |

## Waiting (batch 3 and later: widen the byte enums first, see below)

| Level | Notes |
|---|---|
| Level 23 "The Petrified Garden" | stone trees; vanilla petrified wood / rock could do most of it |
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

Free region slots after batch 2: far south-west beyond Level 974 (`-F, +F`); otherwise new regions go to other radii
(check `overview` for overlaps; the city east of spawn is huge, radius up to 0.72 R).

## Reserved values (append-only)

Batch 1 used WallPattern up to 239, FloorKind up to 248 (byte enums), CeilingKind up to 95, Props up to 699, Unders
up to 149, Overheads up to 139, Pipes up to 119. The bytes are nearly full, so **from batch 2 each level gets one
`WallPattern` value (240-255) and one `FloorKind` value (249-255)**; sub-kinds of floor and wall go in the level's own
`Tile.Zone` / `Tile.Detail` / `Tile.Variant`, read only by that level's block builder. When these run out (7 floor
kinds), widen the enums to ushort in one deliberate change (Tile struct size, harness `.bin` writers, `decorIds`).

| Range | 31 | 55 | 120 | 183 |
|---|---|---|---|---|
| `WallPattern` | 240 | 241 | 242 | 243 |
| `FloorKind` | 249 | 250 | 251 | 252 |
| `CeilingKind` | 96-103 | 104-111 | 112-119 | 120-127 |
| `Props` (ushort) | 700-739 | 740-779 | 780-819 | 820-859 (`Props.Limit` = 860) |
| `Unders` | 150-159 | 160-169 | 170-179 | 180-189 |
| `Overheads` | 140-149 | 150-159 | 160-169 | 170-179 |
| `Pipes` | 120-129 | 130-139 | 140-149 | 150-159 |
| Title keys | 2401-2499 | 2501-2599 | 2601-2699 | 2701-2799 |
| Layout salts | 0x2400-0x24BF | 0x2500-0x25BF | 0x2600-0x26BF | 0x2700-0x27BF |
| Threshold salts | 0x24C0 | 0x25C0 | 0x26C0 | 0x27C0 |
| Headless port | 42485 | 42486 | 42487 | 42488 |
