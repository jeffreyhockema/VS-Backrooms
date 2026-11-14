# The experimental levels' links (2026-10-31)

The eight levels stop being cheats-only: each gets the ways in and out its lore gives, wherever the lore names a level this
mod has. Where the lore names one it has not, the way is a rumour in the level's notes and handbook page, nothing more.
**Where a level's plan disagrees with this file, this file wins.** The user's decisions (2026-10-31): Level 73's way out
is Coran leading you out (our invention; the lore has none); Level 36's flights land in several levels, each gate's in
one; Levels 14 ("Paradise") and 47 (the old-growth forest) will be built later, so their links are rumours for now.

Rules, unchanged from docs/design/new-levels/LINKS.md: every threshold always leads to the same place; walked through =
two-way, fell / dived / taken = one-way. Exceptions are marked and come from the lore (a level that is "extremely hard
to leave" keeps its doors one-way). Ways into a more dangerous level are rare (the progression revision: a quarter as
common as in layout 11) and a walked one gets an M.E.G. placard beside it where the host's own gates have them.

## Host levels: where each entrance goes, and who wins a tile

`WorldLayout.ExpLinks.cs` calls each level's `partial void L<tag>Entrances(Builder b, int mx, int mz)` once per cell of
levels 0-20, in this order (an earlier one wins a tile; a later one skips any tile with `Under >= 256`): **15, 36, 52,
120, 31, 23, Basement, 73**. Each uses its own layout salts (README table), so nothing else in the host moves:
`BACKROOMS_NO_EXP_ENTRANCES=1 mapgen ... layouthash` must equal main's saved files exactly. The blocks are drawn by the
level's `partial void L<tag>EntranceBlock` (`WorldGenerator.ExpLinks.cs`), its Unders from its own block. Never take a
tile that already holds another level's entrance (Level !'s, The End's, Fun's, 3999's, 188's, the Hub's: their
`Unders` ranges, or a feature `Under`), a gate, a way to another level or the spawn cell.

| Host | Entrances in it (owner) |
|---|---|
| Level 0 | Basement: a crack in the floor |
| Level 1 | Basement: a crack in the floor |
| Level 2 | 31: a wooden door with music behind it; Basement: a crack in the floor |
| Level 3 | 15: a door that opens on Level 15; 31: a wooden door with music behind it |
| Level 4 | 120: a door marked SERVER ROOM; 52: an EMERGENCY EXIT door; Basement: a crack in the floor |
| Level 5 | Basement: a crack in the floor |
| Level 6 | 31: a wooden door with music behind it; 73: the dark (no tile: see 73) |
| Level 9 | 36: a door under an airplane sign; 73: the Gloom |
| Level 10 | 15: the white wall and its reinforced door |
| Level 11 | 36: a door under an airplane sign; 52: a high school |
| Level 37 | 23: the hollow green-barked tree |

## Each level

### Level 15, "Futuristic Halls" (owner `l15`) — "extremely hard to get into and out of"
- **In (Level 10):** rarely, an immense white wall of Level 15's own panels rises at the edge of a field and runs out
  of sight, with one small reinforced door (Wikidot, Enric; Fandom). One-way (the wall "disappeared, trapping him"):
  you arrive in a main hall beside a reinforced door that does not open.
- **In (Level 3):** rarely, one of Level 3's doors opens on Level 15 (Fandom: "opening numerous doors in Level 3 has,
  in rare instances, led to Level 15"). One-way.
- **Out:** the control panel's ESCAPE button opens a nearby locked gateway to Level 3 (Fandom); an office staircase
  down to Level 4 (Fandom); breaking a window to Level 11 (Fandom). One-way each ("unstable", "much harder to escape
  than the exits imply": keep them rare). The star door stays a sight with no way through (Wikidot: unknown); Level
  14 (the "Medical Center" door, Fandom) is a rumour until Level 14 exists.

### Level 36, "Airport" (owner `l36`)
- **In (Level 11, Level 9):** a door under an airplane-symbol sign (Wikidot: "airplane-symbol signs in Levels 11,
  9"). Two-way: it opens into the terminal's landside.
- **Out:** boarding at a gate (the countdown, the flight, Sublevel 36.1, already built): each gate's flight lands in
  one fixed level from Level 11, 9, 37, 3999, 188 and 10, and the gate's screen names it (`TO 3999`). One-way. The
  landing is standing, on open ground or a floor, never in water or a wall. Overflowing a restroom sink and putting
  your head under: Level 37 (Fandom). One-way. Glass hotel doors to Level 42, the Metro, Level 35, 597, 188.2: rumours.

### Level 52, "School Halls" / the Greenfield Campus (owner `l52`)
- **In (Level 11):** entering a high school building in the city (Fandom): one city lot in a few hundred is a high
  school, its front doors two-way into a campus building's entrance.
- **In (Level 4):** rarely, an EMERGENCY EXIT door in the offices (Fandom: "emergency exits or lifts in Levels 1-4").
  Two-way.
- **Out:** the two ways in, back. Random doors to Level 53 and the noclip in Marshall David to Level 556: rumours.

### Level 31, "Roller Rink" (owner `l31`)
- **In (Levels 2, 3, 6):** a wooden door with 2000s bubblegum pop playing faintly behind it (Wikidot). Two-way: it
  opens in the rink's lobby.
- **Out:** the Revolving Door to Level 9, 10 or 11 (Fandom; each revolving door always the same one). One-way.
  Stealing skates (leaving Skate Rental with a pair the Coach did not give you, or leaving the level with rented ones):
  you noclip to Level 0, without them (Fandom). One-way. Level 40 (a working arcade game), the white door "70", the
  Employees Only door to 232, Level 25 deeper in the arcade, the stairs from 30: rumours.

### Level 120, "Broken Servos" (owner `l120`)
- **In (Level 4):** a door marked SERVER ROOM in the offices (Wikidot: Level 4.3, which this mod stands in with Level
  4). Two-way.
- **Out:** doors in the server rooms and black hallways back to Level 4 (Wikidot), one-way each (besides the two-way
  door you came in by). A smashed arcade screen in Level 25 and noclipping into Level 70: rumours.

### Level 23, "The Petrified Garden" (owner `l23`)
- **In (Level 37):** a huge hollow tree with green bark growing up through the Poolrooms' tiles (Wikidot: "huge
  hollow green-barked trees in Levels 37 and 47"). Climb in: one-way, you climb out of a hollow trunk in the forest.
- **Out:** into the Heart of Water's core reservoir and out in Level 7's ocean (Wikidot). One-way. Base Seedling's
  hollow tree: the lore's way to Level 135 (no page, not in this mod) is stood in by the tree in Level 37 (two-way:
  the camp's tree and a Poolrooms tree; our substitution, marked as such). Level 47 (built later) and Level 121's
  hollow log: rumours.

### The Basement (owner `basement`)
- **In (Levels 0, 1, 2, 4, 5):** "breaking through the floor of most levels": rarely a patch of cracked floor that
  gives way under you; a long fall (several tens of feet: fall damage as the lore says, not death) into the Basement,
  under its crack. One-way.
- **Out:** climbing back up the crack (Fandom: "near impossible"; bring a ladder): someone who gets to the top of the
  shaft (by ladder, blocks, anything) comes out in Level 0, the light the shaft shows. One-way.

### Level 73, "The Redlands" (owner `l73`)
- **In (Level 9):** "stay near the Gloom for too long" (Wikidot: Level 9.1's; Level 9 stands in): rarely a yard or
  street holds the Gloom, a pool of darkness light does not reach; staying in it too long (a minute or two, warned)
  and you are on the island. One-way.
- **In (Level 6):** the lore names Level 6 with no detail: lingering long in Level 6's deepest dark, very rarely, ends
  the same way. One-way. Level 14 (built later): a rumour.
- **Out:** none in the lore. Coran leads you out (the user's choice, our invention): the condition and the way (for
  example his "lead me out" after a night under his roof, and a door he opens) are the 73 agent's to propose in its plan;
  where he leads you is a fixed level. One-way.

## What else each agent owns

- Its level's notes, handbook page and hint text: the ways in and out above, rumours as rumours. No more "the cheats
  menu is the only way in".
- Arrival finders in its own level for each way in (beside the matching feature), and in the host level for each way
  out (beside the matching feature where there is one, else an open spot; two-way ways come back beside their door).
- The placard beside a walked way into a more dangerous level, where the host's gates have them (layout 12+).
- Its showcase may add a few spots at its entrances in host levels (computed from the layout).

## What the lead does after the merge

`docs/GUIDE.md` / `tools/gen_guide.py`'s ways-between-levels text, the README, the map colours (done:
`MapMarks.LevelColors` 21-28), and the cross-level checks.

## Levels 14 and 47 (2026-11-01)

The user chose to fill two gaps the lore kept pointing at: **Level 14 from Fandom** (the abandoned hospital, class 4,
The Hunter; Wikidot's "Paradise" is a different place and is not used) and **Level 47 from Wikidot** ("The Adderwood",
class 3; Fandom's question-rooms are a different place and are not used). Ids 29 and 30; their reserved ranges are in the
README. Their ways, like the others: lore first, rumours where the lore names a level this mod has not.

### Level 14, the Hospital (owner `l14`, Fandom "Level 14", class 4)
- **In (Level 0):** "a rare emergency exit door found in Level 0": a hospital-style EMERGENCY EXIT door (push bar,
  green running-man sign) in a Lobby wall, very rare. One-way: you arrive in a **reception room** (Fandom: "all of Level
  14's entrants will first arrive" there), its stained-glass revolving door behind you showing nothing ("may never be
  entered again once left"). Precedence in Level 0: after the Basement's cracks (it is added at the end of the order).
  M.E.G. placard beside it (layout 12+: Level 0 is class 0, 14 is class 4).
- **In (Level 15):** Fandom 15: "walking into a futuristic door labeled 'Medical Center' will send you to Level 14".
  The door stands in or beside one of Level 15's medical bays (round 3 added them as a room kind). One-way, to a
  reception room. Its block lives under Level 14's own assets (`blocktypes/14/`), placed by Level 15's Links layout
  file (the visual pass owns Level 15's look and has agreed).
- **Out (to Level 15):** Fandom 14: "going through a rare futuristic-looking door will lead one to Level 15". One-way,
  to a Level 15 main hall beside a reinforced door that does not open (as 15's other ways in).
- **Out (to Level !):** Fandom 14: "finding a rare red exit door and entering it will lead to Level !". One-way; arrive
  as Level !'s other entrances do (a lane's start room), the door slamming.
- **Out (to Level 73):** Wikidot 73 names Level 14 as a way in, with no detail. Our invention: Fandom 14's collapsing
  floor tiles ("revealing hidden passageways or leading wanderers to plummet"): very rarely a patch that gives way drops
  you onto the Redlands. One-way, rare, warned by cracks.
- **Rumours:** the arrows on the floor to the main exit (Level 130), the glowing window (777), too far into the hospital
  (16), toying with equipment (268), the teddy bear (14.1), the torture chambers (4.4); in: Levels 13, 130, 39, 0.01.

### Level 47, the Adderwood (owner `l47`, Wikidot "Level 47", class 3)
- **In (Level 10):** the lore: "no-clipping to or from Level 47 is easier and more frequent than average; the hollows of
  dead trees appear especially prone". Our host: very rarely an ancient dead tree, hollow and mossy, stands in a Level
  10 tree line or field corner, far older than anything round it; step into its hollow and you noclip out of a dead
  tree's hollow in the Adderwood. One-way. Precedence: after Level 15's white wall.
- **Out (to Level 23):** Wikidot 23: "huge hollow green-barked trees in Levels 37 and 47". A rare giant with green bark
  and a hollow: climb in, out of a hollow trunk in the Petrified Garden (Level 23's existing arrival finder). One-way.
- **Out (to Level 10):** the dead trees' hollows (the lore's noclip points): some of them, now and then, put you out
  in Level 10 beside its own ancient dead tree. One-way. (Which hollows lead out, and how often, is the builder's;
  "unstable, but more frequent than average".)
- **Rumours:** the Ophion Occult Order's claim that the trail can be steered to any noclip point, even the Frontrooms.

## Layout 16: the shortcuts a quarter as common (2026-11-13)

The progression rule (docs/design/progression/decisions.md, decision 20; revision.md section B) cut the released levels'
earlier-to-later shortcuts to a quarter in layout 12. The new levels' ways were built after it, and most at full rate. From
layout version 16 the ways **from a level to a later one** are a quarter as common: the same kind of door, the same lore,
the kept ones the same places (the lowest rolls). Ways back toward the Lobby, ways between levels of the same depth, and
the 188/3999 flights are left alone.

**In every world (0.700.0-pre.13, the user's decision of 2026-11-13).** Worlds made before 0.700 (layout 1 to 15) get the
new levels' ways in, in their unexplored parts, so they get these rules too: the new levels' code reads
`WorldLayout.ExpVersion` (never below 16), not the world's own version, for these rates, for the Basement's and Level 52's
balance (food props stripped, tools, seed sacks, trees: feedback-2026-11/README.md) and for the M.E.G. placards beside
Level 0's EMERGENCY EXIT and Level 4's doors to 120 (layout 12 on before). The released levels' own generation is
untouched (layouthash 0-20 identical at v1, 9, 12, 14, 15, 16, with the ways in and without); the gate's
`layoutHashesExp` far places hashes of v1-15 moved, on purpose. Only Level 36's new cabin stays layout 16 only (a rebuild,
not a rule). A way already built in a world's chunks at the old rate that the quarter dropped from the layout (an
orphan: a revolving door, a MEDICAL CENTER door, a pane or office stairs of 15, a floor of 14 that gives way) still leads
where it did: the threshold network asks the world's `WorldLayout.PreBalance` twin (its new levels at the old rates) only
where the thing's own block shows it is built (the block used, the broken pane or the stairs stood in, the sagging floor's
block under you: ThresholdSystem.L14MayPass). `mapgen 12345 24 orphans <kind> x z [rel]` shows one. Level 6's deepest
dark has no block, so a dropped cell is simply Lights Out again; an already-built gate whose flight went from 10 or 11 to
9 or 37 keeps its old screen (the status line and the landing say the new level), and one flown before keeps its link.

Depth: a new level stands where it is entered and by its class. The Basement is the Lobby's cellar (out only to Level 0);
31 sits with Level 2 (Class 0, two-way doors in 2, 3, 6); 120 and 52 are pockets of Level 4 (two-way, back only to 4, or
to 11 for 52's city doors); 15 sits with Level 3; 14 (Class 4, danger 0.7) with Levels 7-8; 73 (Class 5, out only to 9)
with Level 9; 36 with Level 9 (entered from 9 and 11); 47 with Level 10 (out to 10 and 23); 23 with the Poolrooms (danger
0.55, out to 7 and 37).

| Way | Kind | Class | Layout 15 | Layout 16 (seed 12345, full size) |
|---|---|---|---|---|
| Level 31's Revolving Door to 9, 10, 11 | one way | 2 to 9-11: **quartered** | 1 lobby in 12; 1448 (4.4 a km2) | 1 lobby in 48; 354 (1.1 a km2: 130 / 110 / 114) |
| Level 15's orange pane to 11 | one way | 3 to 11: **quartered** | 1 wing in 64; 16, nearest 231 blocks from the middle | 1 wing in 256; 5, nearest 856 |
| Level 15's office stairs to 4 | one way | 3 to 4: **quartered** | 1 wing in 64; 14, nearest 467 | 1 wing in 256; 5, nearest 467 |
| Level 15's MEDICAL CENTER door to 14 | one way | 3 to 7-8: **quartered** | 1 wing in 64; 15 (1.09 a km2), nearest 550 | 1 wing in 256; 2 (0.15 a km2), nearest 550 |
| Level 14's floor that gives way, to 73 | one way | 7-8 to 9: **quartered** | 1 wing in 112; 36 (2.36 a km2), nearest 663 | 1 wing in 448; 5 (0.33 a km2), nearest 1362 |
| Level 6's deepest dark, to 73 | one way | 6 to 9: **quartered** | 1 cell in 2500; about 7 in Level 6 (0.39 a km2), nearest 4.25 km | 1 cell in 10,000, and where that leaves Level 6 none, the old rate's lowest roll stays; 1 (nearest 4.59 km) |
| Level 36's flights to 10 and 11 | one way | 9 to 10, 11: **quartered** | a sixth each; 32 and 22 of 152 gates | a 24th each; 9 and 9 of 152 (the rest fly to 9 or 37: 39 and 48) |
| Level 0's EMERGENCY EXIT to 14 | one way | 0 to 7-8: left | 1 cell in 1000 of the outer two fifths, 16 cells apart, none within 1.5 km: 2 in the Lobby, nearest 1.68 km | the same: built at the rule's rate already (its own comment); a quarter would leave most Lobbies none |
| Level 15's ESCAPE gateway to 3; 14's futuristic door to 15; 14's red door to Level !; 31's skates to 0; Basement climb to 0; 120's doors back to 4; 47's hollows to 10; 47's giants to 23; Coran to 9; 36's sink to 37 | one way | later to earlier, or level | | unchanged |
| Doors into 31 (2, 3, 6), 120 and 52 (4), 52 (11), 36 (9, 11); cracks into the Basement (0, 1, 2, 4, 5); Level 3's door and Level 10's white wall into 15; the Gloom (9) into 73; 10's dead trees into 47; 37's green trees into 23; 23's well to 7 (one in the level) | both | level, or later to earlier | | unchanged |
| Level 36's flights to 3999 and 188 | one way | the rule keeps those links | 25 and 22 of 152 | unchanged |

The ten-by-ten-cell clause (keep one where a quarter would leave a level no way down) does not bite: none of these is a
host level's way down (the ring gates and the released shortcuts are untouched), and every region keeps a way out at full
rate (31's lobby doors, 15's ESCAPE gateways, 14's futuristic and red doors). The only way that a quarter could leave a
whole world without is Level 6's deepest dark (about one world in six at full size, most at half size), so its kept cell
is guaranteed. Level 15's panes, stairs and MEDICAL CENTER doors are about three each in the level now: a world may have
none of one kind (a few in a hundred). `mapgen 12345 64 31links|14links|36links|73links`, `mapgen 12345 16000 15links`.
