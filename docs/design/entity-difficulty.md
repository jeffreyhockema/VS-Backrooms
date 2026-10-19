# Entity difficulty

2026-10-06. Why entities were no threat, and what changed so that every level below the Lobby is more dangerous
and more rewarding than the last. Code: `Danger` in `src/Entities/Roster.cs`, `src/Entities/Rewards.cs`, the
director in `MenaceSystem.cs`, the tasks in `AiTaskMenace.cs`, `AiTaskMoth.cs`, `AiTaskLurkers.cs`; base stats in
`tools/gen_entities.py`.

## 1. What was wrong

**Speed.** Players and walking AI go through the same ground physics. A player's movement step is 0.025 walking
and 0.05 sprinting; an AI's path speed is the same quantity. So an entity with a run speed under 0.05 can always be
outrun. Before:

| Entity | Run speed | Share of a sprint |
| --- | --- | --- |
| Hound | 0.042 | 84 % |
| Skin-Stealer | 0.024 | 48 % (slower than walking) |
| Death Rat | 0.040 | 80 % |
| Smiler, Duller | 0.050 | 100 % |
| Clump (crawl) | 0.020 | 40 % |

For reference, the vanilla wolf chases at 0.045.

**Damage.** A player has 15 health. A vanilla wolf bites for 8 at tier 2. Ours: Hound 2.5 at tier 1, Skin-Stealer
5, Death Rat 0.75, Deathmoth 1, Clump 3, Duller 2. Most fights needed six to twenty hits to kill an unarmoured
player.

**Nothing scaled with depth.** A Hound on Level 9 was the Hound of Level 1. Depth changed only which entities could
appear. Loot already got less picked over deeper down, but nothing else rewarded going deeper.

**Odds.** In the "approach" band only 5 % of encounters were hunts, and stalkers turned to the hunt mostly when the
player ran: which, being faster than everything, they could always do.

## 2. Level danger

Each level has a danger value, set on every entity as it is put down:

| Level | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 37 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Danger | 0 | .12 | .24 | .36 | .44 | .52 | .60 | .66 | .74 | .82 | .88 | .95 | .50 |

Level 94 keeps its own balance (the King's trial) and has danger 0. The far places: Level ! .90, Fun .90, The End .40,
the Hub 0, 974 0, 3999 .80 (only its Neon Blackout has anything in it), 188 .45. The bonus pool below goes by danger
(under .4, under .7, the rest), not by level number.

What danger `d` does:

| Effect | Formula | Level 1 | Level 5 | Level 9 |
| --- | --- | --- | --- | --- |
| Speed | x(1 + 0.3 d) | 1.04 | 1.16 | 1.25 |
| Damage | x(1 + 1.1 d) | 1.13 | 1.57 | 1.90 |
| Time between attacks | x(1 - 0.3 d) | 0.96 | 0.84 | 0.75 |
| Health | x(1 + 1.4 d) | 1.17 | 1.73 | 2.15 |
| Armour tier | +1 from d 0.6 (Level 6) | | | +1 |
| Gives up the chase at | 40 + 25 d blocks | 43 | 53 | 61 |
| Chance it turns to the hunt unprompted | x(1 + 2 d) | 1.2 | 2.0 | 2.6 |
| Director's spawn chance | x(1 + 0.8 d) | 1.10 | 1.42 | 1.66 |
| Calm after a close call | 90 s x(1 - 0.5 d) | 85 s | 67 s | 53 s |
| Encounters that are hunts (approach / edge) | | 7 % / 28 % | 13 % / 38 % | 17 % / 42 % |
| Most entities near you at once | +1 from Level 5, +1 from Level 9 | | | |
| Pack size | +1 at most from Level 5 | | | |

`/backrooms menace` shows the current level's danger and multipliers.

## 3. New base stats (Level 0) and what they become

Speeds are shares of a sprint; "hits" is how many land on an unarmoured player with 15 health.

| Entity | Level | Speed | Damage | Hits | Health |
| --- | --- | --- | --- | --- | --- |
| Hound (in the dark; light slows it to 0.7) | 1 | 95 % | 4.0 | 4 | 16 |
| | 3 | 102 % | 4.9 | 4 | 21 |
| | 5 | 106 % | 5.5 | 3 | 24 |
| | 9 | 115 % | 6.7 (tier 3) | 3 | 30 |
| Smiler (stops at light 8 or more) | 0 | 100 % | 6.0 | 3 | immortal |
| | 2 | 107 % | 7.6 | 2 | |
| | 9 | 125 % | 11.4 (tier 4) | 2 | |
| Skin-Stealer (slow, strong; a hit of 5 stuns it for 1.2 s, 8 s apart; fed, it is docile; 2026-10-18) | 1 | 70 % | 7.9 | 2 | 60 |
| | 5 | 79 % | 11.0 | 2 | 88 |
| | 9 | 85 % | 13.3 (tier 3) | 2 | 110 |
| Death Rat (packs of 2 to 6) | 1 | 99 % | 1.4 | 11 | 6 |
| | 8 | 117 % | 2.2 (tier 1) | 7 | 10 |
| Duller (grab through a wall; takes no damage from players but from its grab to 1.5 s after; flees at 1.3 x a sprint; 2026-10-18) | 3 | 120 % | 4.2 | 4 | 30 |
| | 8 | 132 % | 5.4 (tier 2) | 3 | 41 |
| Clump (grab; crawl) | 2 | 60 % | 6.3 | 3 | 27 |
| Deathmoth female (bite) | 1 | | 1.7 | | 3 |
| Wretch (bite; packs in Level 8) | 1 | 96 % | 4.0 | 4 | 19 |
| | 8 | 112 % | 6.3 (tier 2) | 3 | 33 |
| Bacteria (hunts only a runner near the Lobby's exits, briefly: see §4) | 0 | 92 % | 6.0 | 3 | 20 |
| Neighborhood Watch (Level 9; chases only what it sees, never indoors) | 9 | 110 % | 12.4 (tier 3) | 2 | 64 |
| Giant Spider (bite + venom 5 x 0.9 over 6 s; lies in wait, leashed to 24 blocks of its home; 2026-10-18) | 8 | 122 % | 6.3 + 4.5 (tier 3) | 2 | 41 |

The Mangled (5, plus being lifted 7 blocks and dropped; slower than a walk since 2026-10-10) and The Thing are events and keep their own numbers.

## 4. Skill: what keeps you alive now

- **Running only works early.** From Level 3 a Hound outruns you, and running is what turns a stalker into a hunter.
- **Nothing chases for ever** (2026-10-10). A hunt that draws no blood for 20 seconds (35 at the bottom) is given up: the
  hunter goes back to following and will not hunt again for a minute. The Lobby's Bacteria hunts only while you keep
  running near the way out: walk for four seconds, head back towards the heart, take one blow, or last 25 seconds,
  and it sinks back into the mould (strike it and it fights, bounded only by the 20 seconds).
- **Light** still slows Hounds to 70 % and keeps Smilers and rats back. **Fire** still wards off Hounds,
  Skin-Stealers, rats and moths.
- **Stare a Hound down** for a few seconds' grace.
- **Doors**: nothing hostile opens one but the Skin-Stealer (2026-10-10): hunting someone shut in, out towards the
  edge of a level or worse, it knocks on the nearest door near them, waits two seconds, and opens it. A door barred
  from the inside (a vanilla bar lock) only gets the knock; fire keeps it away from the door altogether.
- **Dodge**: every attack is wound up (600 ms for a Hound, 650 for a Skin-Stealer). Being more than 0.4 blocks
  beyond its reach when the blow lands makes it miss (was 0.6).
- **Almond Water** keeps Dullers off; **quiet** keeps Clumps buried; **indoors** is safe from the Mangled.
- **Armour** matters more from Level 6, where every blow is one tier harder.

## 5. Rewards

- **Bounty** (`Rewards.Bounty`), on whatever a player kills, in rusty gears (the wanderers' coin), expected value:

| Entity | At danger 0 | Extra per unit of danger | Level 5 |
| --- | --- | --- | --- |
| Hound (old ones double) | 0.25 | 1.0 | 0.8 |
| Skin-Stealer (plus one or two belongings) | 1.0 | 2.5 | 2.3 |
| Duller | 0.5 | 2.0 | 1.5 |
| Clump | 0.5 | 2.0 | 1.5 |
| Death Rat | 0.05 | 0.25 | 0.2 |
| Deathmoth female | 0.05 | 0.2 | 0.15 |
| Wretch (plus one or two belongings) | 0.3 | 0.8 | 0.7 |
| Bacteria | 1.0 | 2.0 | 2.0 |
| Neighborhood Watch (Level 9: 3.05) | 1.0 | 2.5 | |
| Giant Spider (Level 8, danger .74: 2.85) | 1.0 | 2.5 | 2.3 |
| Partygoer, intern (Fun, danger .9: 3.25) | 1.0 | 2.5 | 2.3 |

  Facelings carry no bounty, and neither does any of Level !'s horde.
- **Caches** (`Rewards.OnBrokeBlock`): any of our blocks whose drops include food, medicine, metal, seeds or gears
  (132 kinds). Broken by a player in survival below Level 0:
  - with chance 0.7 d, its contents drop a second time;
  - with chance 0.15 + 0.35 d, one extra from the level's pool:
    - Levels 1 to 3: bandage, candles, crackers, twine, a rusty gear;
    - Levels 4 to 7: rusty gears, copper bits, a poultice, Almond Water, Firesalt;
    - Level 8 on: rusty gears, tin bronze bits, bandages, iron bits, very rarely a temporal gear.
- Already there: deeper levels' boxes are less picked over (80 % in Level 1, 60 % to Level 5, 40 % below).

## 6. To tune after play

All in one place: `Danger.OfLevel` (the curve) and the multipliers beside it; the base stats in
`tools/gen_entities.py`; the bounty and cache tables at the top of `Rewards.cs`. The world setting *Backrooms
entities* (Off, Low, Normal, High) still multiplies damage (0, 0.5, 1, 1.3) and spawns (0.6, 0.6, 1, 1.5) on top of all
this; Off also keeps the entities themselves away, leaving only their sounds.
