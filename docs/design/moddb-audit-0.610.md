# Mod page audit for 0.610.0

Audited 2026-10-26: `docs/moddb-description.md` and `.html` against CHANGELOG.md (0.610.0 section), README.md, docs/GUIDE.md, worldconfig.json and its lang file, `src/Entities/Roster.cs`, the progression, needs and traders design notes, and the testing plan. Version 0.610.0 and the "22 levels / 70+ ways / 25+ creatures" counts check out. Both files carry every change. `python tools/moddb_preview.py` ran and rendered the page (7 tiles).

| Claim | Old | New | Source |
|---|---|---|---|
| Where a temporal gear works | "moves where you wake, but only within the level" | "sets where you wake, from any level" | GUIDE.md Home and expeditions; `SetSpawnPosition` has no level limit |
| When you may sleep | "About an hour awake you can lie down" | "From about forty-eight minutes awake" | GUIDE.md Rest (drowsy at 48 minutes) |
| Handbook page list | "Food, Heat and Cold" and no Rest page | "Food and Water; Rest and Sleep" | GUIDE.md Playing (nine added pages) |
| Where Thirst and Fatigue sit (md only) | listed under World generation | listed under Survival challenges; only level size is World generation | worldconfig.json `category` |
| Level 6 card | "nothing found living in it" | "...but eyes that never come close" | Roster.cs level 6 (a Smiler glimpse) |
| The Beast | "deep in Level 5's boiler halls" | "above all in Level 5's boiler halls" | GUIDE.md entity table (rare in Level 5, anywhere for whoever owes him) |
| Pleather source | "car seats and hotel chairs" | "car seats and office and hotel chairs" | GUIDE.md Salvage (Level 1 cars, Level 4 office chairs, Level 5 chairs and sofas) |
| What's new: blows unarmoured | "two blows" in one bullet, "two or three" in another | "two or three blows" once | GUIDE.md entities (2-3 at Level 3, 1-2 by Level 8) |
| What's new: structure | 7 bullets plus "Also new"; climb and armour bullets overlapped; no glass spear, F8, Hound changes, Level !, The End | 10 bullets in player order: creatures, Hounds, armour, the climb, thirst and fatigue (glass spear), the people, body and last bed, settings, levels, building and handbook (F8 line) | CHANGELOG.md 0.610.0, testing/plan.md |
| What's new: closing line | "...and 0.514.0's graphics pass" (dangling) | "The changelog has the full list." | n/a |
| Ore | "copper from the pipes" in a bullet beside "no ore" | ore only in Level 8, copper from salvage, tin from the 9th Road (kept in the climb bullet) | progression/revision.md decision 18 and CHANGELOG |

Checked and left as is: the six entity names (worldconfig lang: Off, Very low, Low, Normal, High, Very high), Scarcity values, Map values, level size, Thirst and Fatigue defaults; class table; respawn at the last bed (Level 0 if none); blackout after about a minute at zero from any cause, waking a level back; placards; scarcity by class (Class 3 and deeper); shortcuts about a quarter as common in new worlds; corpse behaviour (never despawns, own skin, skull marker, three days to bones); traders' sites and the Junkies' Memory Juice rule; Level 10 nothing hostile; Level 94 houses; Level 4 panes; Hub tunnels; Level 188 windows; the roster table (every creature against Roster.cs and the GUIDE table). No depth drain, anchors or ward tiers appear anywhere.

Noted, not changed: GUIDE.md's entities bullet says bronze lets you stand "two blows" at Level 8, while the classes section and CHANGELOG say three. The page follows the changelog.
