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
