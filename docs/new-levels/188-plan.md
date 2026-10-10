# Level 188, "The Courtyard of Windows": research, design and integration plan

**Level 188** (tag `188`, internal id **20**, constant `WorldLayout.Level188`, method infix `L188`, block prefix `l188-`,
shown as "188") is a dark courtyard of four mossy lawns and a round wooden deck, walled in on every side by a five-storey
hotel with a hundred and sixty small square windows. Most of the windows have their blinds down. A few are lit. Some show
other places entirely: a yellow-wallpapered room, an orange road tunnel, a children's party with confetti drifting past
the glass. If you see someone standing in one, beckoning, do not go into that room.

This is a design only. No code or assets were touched (phase 1 rules). Section 9 lists the decisions for the user, each
with a recommendation.

## Status (2026-10-09): phase 2 code built, with the user's answers to section 9

The user chose the Courtyard of Windows, one shared building and death when pulled through a predatory window; every
other recommendation stands. Verified with the layout harness and a headless server (port 42480, seed 12345), rendered
from a dump. **Not played in a client.**

**Built** (code: `WorldLayout.Level188.cs`, `WorldGenerator.L188.cs`, `ThresholdNetwork.L188.cs`, `AtmosphereSystem.L188.cs`,
`Regions/L188System.cs`, harness `tools/mapgen/L188Stats.cs`; assets by the 188 asset agent):
- **The region:** a fixed radius of 4 cells; the building (88 × 58) in the three cells by two round its centre; solid
  nothing elsewhere. `L188BandDepth` 6, so the band reaches rel 33 (the black sky).
- **The building:** as 3.2-3.3 (the plan's coordinates exactly): five storeys of slab blocks, the scissor stair to the
  roof and its bulkhead, 32 courtyard windows a storey, inner and outer rooms furnished from one plan turned to each wing,
  corner suites, the lobby, the lift lobby (dead lifts: "out of order"), housekeeping and the linen store, the roof with
  its parapets, AC units and gravel. The courtyard: lawns with edging and moss, the deck with rounded edges, the hatch
  and its shaft, benches, bollards, the downpipe and drain.
- **Windows:** drawn in the world's state for the hour (3.4a); `L188System` keeps them in step while anyone is in the
  level (blinds, lamps, sealed doors), swaps a figure to beckoning when someone is within six blocks, and moves the
  predatory windows each in-game day (never into a room someone is in).
- **Ways in and out:** all of 2.2 and LINKS.md round 2: the twelve link windows; blinds (taken, one-way, a fixed place
  per window, the window then shows it and the room seals for three days, saved); the four fire exits (two-way; Level 5
  and 2 beside a door, 1 and 4 a thin spot); the hatch to Level 37; the windows in Level 0 (1 cell in 300, outer three
  fifths) and Level 1 (1 car-park cell in 250, last in Level 1's precedence); Level Fun's one confetti window (a one-line
  hook in `BuildLevelFun`); the Hub's window (`Unders.HubWindow188`, the Hub's layout: walked into, or right-clicked
  from the tunnel, through the blind behaviour on the Hub's `l188-window-lit` blocks).
- **The arm:** whispers within 6, grab within 2 after a second's grace; held, slowed, dragged and hurt; two blows on
  the arm or 3.5 blocks away frees you; six seconds at the glass is death.
- **Peripherals:** a client HUD shape at the screen's edge, gone when you turn toward it; −0.02 stability each.
- **Air, sound, danger:** fog (hotel, courtyard, roof), titles (courtyard = the level's own; 2001 the hotel; 2002 the
  roof), loops and positional sounds, distant sounds, temperatures, stability (plus a drain near a predatory window),
  danger 0.45, the roster (Skin-Stealers, Smilers in the dark), bands (safe in a room with its door shut), picked-over
  share 0.3, the building's fabric Fixed.

**Checked:**
- `188stats` (full-size and small world): building cells all level 20; courtyard 54 × 24; 32 windows a storey; twelve
  link windows (L0 ×3, L1 ×2, L2, L4, L5, L6, L9, Hub, Fun) with sealed rooms; every walkable ground-storey tile reached
  from the courtyard or sealed; 60/60 arrivals on the courtyard paving, 60/60 beside a Level 0 window when asked; every
  link window, blind (all storeys), fire exit, the hatch, the Hub window and the Fun window lead where they should; the
  windows in Levels 0 and 1 change no tile but their own two.
- `regions`: 60/60 arrivals, none in pockets, 0.05 ms per cell. `links`: every 188 threshold leads somewhere, repeats,
  and the two-way ones come back (paired or thin spot); no errors.
- `layouthash`: levels 0-13 identical with and without 188's entrances (`BACKROOMS_NO_188_ENTRANCES=1`); overall
  `1857df5df32e2d0f` in the tree as it stands.
- Headless dump: slices at every storey and vertical cuts through the stair (steps, fill, landings, headroom), light
  maps (corridors 7-10, lobby 7-10, the courtyard lit only by its windows and bollards), renders of the courtyard, a
  corridor, a room, the lobby and the stair.

**Deviations:** the courtyard's door, its windows and the lobby are the only differences between the storeys; the pod
door is one-sided (`l188-poddoor-{side}`), so in half the wings its glass faces the toilet rather than the bed; window
states are hour-based functions of the world, not stored (only opened blinds are saved).

**Not yet:** a client play-test (the arm's pull over the network, the Peripheral HUD, sound levels); the arm's
animation names (`reach`, `pull`, `recoil`) must match the asset agent's model.

---

## 1. What the lore says

Sources, by weight: the original Wikidot page (via its Fandom port, see 1.1), then Fandom's current page, then Miraheze,
then the depictions. Pages were fetched on 2026-10-09. Copies are in this session's scratchpad (`scratchpad/l188/web/`).
Quotes are marked and kept short.

### 1.1 Which Level 188: four unrelated pages share the number

| Source | Title | What it is | Status |
|---|---|---|---|
| Wikidot, 1000dumplings (2020) | "The Courtyard of Windows" / "The Windows" | A courtyard ringed by windows; the Hub window; the Level Fun confetti window | Gone from Wikidot; preserved by its Fandom port (Fandom's rewrite banner still credits "author=1000dumplings; ported to Fandom by Nick6978") and by the original Level Fun page |
| Wikidot, userunhacked (c. 2021-2023) | "August-1B" | A Mercury-like planet with a dead space station; the only way in is "a single window within Level 3" | Wayback snapshot of 2023-12-07 (`web.archive.org/web/20231207180900/http://backrooms-wiki.wikidot.com/level-188`); since deleted |
| Wikidot today | – | `backrooms-wiki.wikidot.com/level-188` returns "THIS PAGE DOES NOT EXIST YET"; the Normal Levels I list shows "Level 188 - [NO DATA]" | https://backrooms-wiki.wikidot.com/normal-levels-i |
| Fandom | "The Windows" | The Courtyard of Windows, rewritten as a hotel around a courtyard (rewrite in progress, 33%) | https://backrooms.fandom.com/wiki/Level_188 |
| Miraheze | (untitled) | The Courtyard of Windows, pentagonal, Survival Class 5 | https://backrooms.miraheze.org/wiki/Level_188 |
| Escape the Backrooms (Fancy Games) | "Courtyard of Windows" | A hotel with a glazed courtyard, TV puzzle, Window Entities | https://escapethebackrooms.fandom.com/wiki/Level_188 |
| Find the Chomiks (Roblox) | "The Windows" | An apartment block with windows; a game map, not canon | namu.moe |

**Chosen: the Courtyard of Windows.** It is what "Level 188" means to almost everyone:
- it rests on one of the best-known liminal photographs on the internet;
- it is the 188 that Level Fun's canon points at ("If you see confetti falling out of a window on Level 188, that's us
  having a party!");
- it is the 188 of Escape the Backrooms, whose level list this mod's new levels follow (37, 94, Fun, !, The End, The
  Hub, 974, 3999, 6.1 ...);
- Fandom and Miraheze both still describe it.

The August-1B page was a later, unrelated level on the same slot and is itself deleted. It shares only the motif (a window
is the way in), and its own text winks at the old one: "additional entrances and exits found on other pages are not to be
trusted. Their erroneous appearance has been attributed to the Mandela Effect." The mod nods to it once: Level 3 is among
the places a curtain can send you (3.4).

### 1.2 The original (Wikidot, 1000dumplings, 2020; Fandom port of 2020-10-20, revisions 22057-23674)

Fetched through the Fandom API (`action=parse&oldid=22084`):

- "Level 188, or the Courtyard of Windows, or just The Windows, is a highly unsafe place full of entities."
- **Look.** "a large courtyard that is, true to its name, full of windows. There are four grassy areas, with a wooden
  circle in the middle. There are walls surrounding the main courtyard, with all of them having lots of glass windows."
- **Windows.** "Sometimes, the windows have their blinds rolled down, and other times, the blinds are rolled up, revealing
  a bright room behind each window, containing an entity."
- **Entrance.** "Look for a window in The Hub, and climb in." Strongly discouraged: entities may lurk behind it.
- **Exit.** "Come out from where you came from. However, the more windows you search into, the least likely you'll be
  able to come out unharmed."
- **Notes.**
  - "near impossible to get out of this Level, due to the place swarming with entities";
  - "The wooden circle in the center of the courtyard is rumoured to be a trapdoor to another Level";
  - "If you see confetti falling out of a window on this Level ... The window belongs to ... Level Fun".
- No colonies. Two photographs.

### 1.3 Fandom today: "The Windows" (rewrite in progress, Class 2-3)

https://backrooms.fandom.com/wiki/Level_188 (wikitext via the API):

- **The building.** "an enclosed edifice, with architecture resembling that of a hotel. A large courtyard-like area is
  present in the center of the level, surrounded on all sides by numerous small square-shaped windows on each wall."
- **Open and closed windows.** Most windows are "obscured by curtains"; some become visible, "each seemingly looking into
  a different location entirely". Visible ones are "open", curtained ones "closed".
- **The interior.**
  - "a stairwell present near one end of the center courtyard" leads in.
  - The hallways, "each interconnected to reach five floors, loop around the level and lead to the interior rooms behind
    each window".
  - The rooms are behind "unmarked doors". Most open onto "a typical, albeit small, hotel-like interior".
- **The two rules of the windows.**
  1. When a window is open and shows another place, the door to its room "will be locked by unknown means"; forcing it
     has always failed.
  2. Opening the curtains of a closed window: "all who have attempted this have instantly disappeared, whilst the
     corresponding window simultaneously changes to display a new location behind it."
- **Size.** "relatively meager size"; colonies are difficult.
- **Entities.**
  - **The Windows** (Entity 2): "certain windows ... may be seamlessly replaced by a window entity". "Shadow-like figures
    have been spotted behind these windows, motioning for one to enter the room. Rooms correlating to these fake windows
    should be avoided at all costs."
  - **Peripherals**, exclusive to 188: no physical form; they "only appear in the mid and far peripheral views", one or
    several at a time; not hostile, "only caused minor feelings of paranoia".
- **Entrance:** "A window may similarly appear in Level 0".
- **Exits:** only the windows: the one you came in by, or another open window to "many unknown locations (this is
  strongly advised against)".
- **Photo credit.** The photograph is by Dominik Johann (@zerstoerer), taken at the Holiday Inn Express, Terminal 4,
  London Heathrow, and posted on 15 March 2019 (https://twitter.com/zerstoerer/status/1106521281908957189). The second
  image is captioned "Note the inconsistent number of windows."

### 1.4 Miraheze (Survival Class 5)

https://backrooms.miraheze.org/wiki/Level_188:

- **The building.** "a vast building characterized by a pentagon-shaped courtyard". The walls carry "an ever-changing
  array of windows, ranging from 90 to 200 at any given time". Active windows "emit light and contain peculiar
  entities"; the rest are "concealed by blinds".
- **The walls.** The walls round the courtyard "lack rooms"; their thickness is unknown.
- **The courtyard.**
  - "The sky above stretches into an infinite darkness" (some claim to have glimpsed Level 24).
  - The "grass" is "a growth of moss pushing through the concrete".
  - "pipes along one wall release a non-potable liquid".
  - "a central wooden circle is speculated to be a trap door leading to another level, though untested".
- **Entities:** the Windows above all; Skin-Stealers, Deathmoths, Smilers and Frowners; and **The Figures**, "humanoid
  silhouettes" that watch from exposed windows. Long looks cause "profound discomfort".
- **Entrances:** "a window appearing in The Hub, Level 0 or Level 1".
- **Exits:**
  - windows, best the one you came by;
  - an "emergency exit" door in the internal corridors, whose destination is in flux.
- **The photograph** is said to be from 2017 and kept in Level 11's Backrooms Museum. Two Figures are visible in one
  window.

### 1.5 Entity 2, "The Windows" (Wikidot)

https://backrooms-wiki.wikidot.com/entity-2:

- **What they are.** Predatory manifestations that occupy ordinary windows. Each shows a blurred landscape that differs
  for every observer.
- **The figures.** Occupied windows hold dark human silhouettes. They fade unless fed, and gain "visual density" after
  a victim.
- **How they hunt.**
  - Comforting telepathic whispers and hand gestures lure the victim.
  - Within 1-2 m, the entity "will manifest a physical representation of an arm to grasp and pull the victim into itself".
- **Advice:** avoid window-heavy areas; resist the compulsion.
- Level 188 is not named on the current page.

### 1.6 Depictions

- **The photograph.**
  - A night view up a narrow hotel courtyard: rows of identical small square windows in pale render, most with white
    blinds down, some glowing warm behind the blinds.
  - Below, rectangles of lawn and a round wooden deck.
  - The sky above is dark.
  - It is the look the level must have.
- **Escape the Backrooms (Part 4).** https://escapethebackrooms.fandom.com/wiki/Level_188 and
  https://www.playnews.gg/en/guides/escape-the-backrooms-advanced-levels-guide-94-fun-end:
  - **The hotel.** Grey and black carpets, grey walls, a grey ceiling with small white lights.
  - **The courtyard.** 114 windows; "every room on the inside of the hotel - that is, the side that faces the courtyard -
    is guaranteed to have a Window Entity in it". The Window Entities shake curtains; do not approach.
  - **Rooms.** A lobby with a desk, bathrooms, a laundry room, an elevator, hotel rooms. TVs A, B and C must be pushed to
    marks to open a metal door to "the very small courtyard".
  - **The hole.** It leads to Level 37.2. A wooden door guarded by the Aranea Membri (a game-original spider creature)
    leads on.
  - **The Hub.** A room of doors labelled with levels, of which only "H" opens.
  - Silence, a room-tone ambience, "the clicking of legs on the tiled floor".
- **Fandom's Level 188.8, "The Flooded Windows"** (https://backrooms.fandom.com/wiki/Level_188.8). A fan sub-level that
  blends 188 with Level 37:
  - the same hotel and courtyard in white ceramic tile, flooded with -2 °C water;
  - "4 squares with a circle in the center" on the floor;
  - one window labelled "run".
  - It supports the courtyard ↔ Poolrooms link (3.4, the hatch).

### 1.7 What everyone agrees on, and the contradictions

**Agreed:**
- A courtyard walled by many small windows, most with blinds down.
- Windows that light up or open onto rooms and other places.
- Figures in the windows are dangerous.
- The windows are the ways in and out.
- A wooden circle in the middle that may be a trapdoor.
- Very little else to the level.

| Question | Original (Wikidot/Fandom 2020) | Fandom today | Miraheze | Escape the Backrooms |
|---|---|---|---|---|
| Shape | Courtyard, four lawns, wooden circle | Rectangular courtyard in a hotel | Pentagon | Rectangular courtyard; a second, tiny one |
| Behind the windows | Bright rooms with entities | Hotel rooms (five floors) or other places | No rooms at all | Hotel rooms, a Window Entity in every inner one |
| Sky | – | – | Infinite darkness | Glazed roof |
| Danger | "Highly unsafe" | Class 2-3 | Class 5 | Class 3-4 |
| Entrances | Hub window | Level 0 window | Hub, Level 0, Level 1 windows | From Level !~! |
| Exits | The window you came by | Windows (your own, or others) | Windows; an emergency exit door | The hole (37.2); a guarded door |
| Entities | "Swarming" | Windows, Peripherals | Windows, Figures, Skin-Stealers, Deathmoths, Smilers, Frowners | Windows, Aranea Membri |

**The mod's reading.**
- **The body of the level:** the original's courtyard (four lawns, wooden circle, Hub window, confetti window) inside
  Fandom's five-storey hotel, with both window rules.
- **From Miraheze:** the darkness overhead, the moss, the pipe, the Figures, the Level 0 and Level 1 windows and the
  emergency exits.
- **From Escape the Backrooms:** the grey hotel look, the lobby and laundry, and the hole to the Poolrooms.
- **Left out:** Miraheze's pentagon (the photograph is a rectangle) and its roomless walls (Fandom's rooms are the heart
  of the window rules).

### 1.8 Ways in and out, by source

| Source | Ways in | Ways out |
|---|---|---|
| Original (2020) | A window in The Hub | The window you came in by; other windows, at risk; the wooden circle (rumoured trapdoor); a confetti window = Level Fun |
| Fandom today | A window in Level 0 | Your own window; other open windows (unknown places); opening a closed window's curtains (you vanish) |
| Miraheze | A window in The Hub, Level 0 or Level 1 | Windows; an emergency exit door (destination in flux) |
| Level Fun (Wikidot original) | – | A window with confetti falling from it (Level Fun's party) |
| Escape the Backrooms | From Level !~! | A hole in a tiny courtyard → Level 37.2; a guarded door; a door marked H → The Hub |
| Fandom 188.8 | – | (a flooded copy blending 188 with Level 37) |

---

## 2. Where it fits

### 2.1 A small noclip region: one building

Level 188 is somewhere you climb into through a window. It is a region, like the others since the city, but unlike all
of them it is **not endless**: canon is clear that it is of "relatively meager size". It is **one building**, the same for
everyone in the world, as the original's single courtyard is.

**Region** (the scaffolder placed it; only the radius changes):
- **Centre** as scaffolded: `L188Reach = RegionReach * 1.1`, 22.5° east of north, between Motion and Level Fun.
- **Radius:** a fixed **4 cells** (`L188Radius => 4`; the placeholder is `max(40, S/50)`), whatever the world size.
  - The building takes 3 × 2 cells in the middle.
  - Every other cell of the region is solid `l188-nothing`.
  - `RoundArrivalCell` picks within 0.4 × radius (1.6 cells) of the centre, so every arrival search starts on the
    building.
- **Building origin** (block coordinates of its north-west corner):
  - `L188BuildX0 = (L188CentreX - 1) * 32 + 4` and `L188BuildZ0 = (L188CentreZ - 1) * 32 + 3`;
  - size **88 × 58** (x × z), so it sits inside cells `cx-1 .. cx+1` × `cz-1 .. cz` with a margin of solid all round.
- **Rim:** as for every region. Against Level 10, the shared rock wall (`LevelBoundaryEdge`); between the level's own
  cells, `L188Edge` copies the building plan onto the edge (open where the building's floor crosses a cell line, solid
  elsewhere), as Level 0's planned edges do.
- **Check:** `regions` and `overview` must show no overlap with Motion or Fun (it is tiny, so the margin is huge).

**Heights** (`WorldGeometry`, own constants):

| Constant | Value | Why |
|---|---|---|
| `L188Drop` | 0 | The courtyard is at the shared floor |
| `L188BandDepth` | 6 | The hatch's shaft needs only 6 below. The band is then `FloorY - 6 .. FloorY + 33`, which is rel −6 to **33**: five storeys and a roof (rel 0-24) with darkness overhead up to rel 33 |

| rel | What is there |
|---|---|
| −6 .. −1 | Solid, except the hatch shaft (black) |
| 0 | Courtyard pavers and lawns; the ground storey's floors |
| 4s (s = 0..4) | Storey s's floor slab (the one-block slab is both the ceiling below and the floor above: 3.3) |
| 4s+1 .. 4s+3 | Storey s's air (3 high, `RoomHeight`) |
| 4s+1 | Window sills; 4s+2 .. 4s+3 the window panes (2 × 2 blocks) |
| 20 | Roof slab (stand at 21) |
| 21 | Parapet (1 block plus a coping lip) |
| 21-24 | The stair bulkhead on the roof |
| 22-32 | Open air over courtyard and roof |
| 33 | `l188-sky`: dead black, the "infinite darkness" (`BandTopFor`) |

`IsOpenSky(Level188)` stays **false**: the "sky" is a ceiling no light reaches.

### 2.2 Its part in the threshold network

Rules as always: every threshold always leads to the same place; walked (climbed) = two-way, fell/dived/taken = one-way.
Climbing through a window is walking, so **windows are two-way** (canon: "come out from where you came from").

**Ways in**

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| **The Hub** | **A lit window** in a tunnel wall, blinds half up, the dark courtyard beyond (one per world, in a door slot on a spoke, unlabelled) | 188's **Hub window**, climbing down into the courtyard | That window (two-way pair) | Original: "Look for a window in The Hub, and climb in"; Miraheze |
| **Level 0** | **A window where no window should be**: a 2 × 2 white-framed window in the yellow wallpaper, sill at knee height, no glass, a blind half up, a dark courtyard and lit windows beyond. Rare: about 1 cell in 300, outer 60% of Level 0, on a straight wall at least 4 long, facing a room | 188, beside a link window **showing Level 0** | That window; from 188, the window leads back to a Level 0 window if one is near the arrival, otherwise to a thin spot | Fandom: "A window may similarly appear in Level 0"; Miraheze |
| **Level 1** | The same in **bare concrete** (aluminium frame), on a warehouse-sector wall, about 1 cell in 250 | 188, beside a link window showing Level 1 | As above | Miraheze: "a window appearing in ... Level 1" |
| **Level Fun** | **A party-room window** with confetti on its sill and a red balloon tied to the latch, the courtyard visible through it (about 1 party room in 40, its own salt) | 188's **confetti window** | That window (two-way pair) | Fun canon ("confetti falling out of a window on Level 188"), reversed: the party is on Fun's side |

**Ways out**

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| Link windows (12, ground storey) | Climb in at the sill (walked, `rel ≥ 1.9` in the window tile) | Their level, shown in the window (3.4) | Two-way | Original and Fandom |
| A closed room window (≈140, any storey) | **Open the blind** from inside the room (used, kind `l188-blind-<storey>`) | A place fixed for that window, from a table weighted toward the main levels (3.4) | **None (taken)**. The window then shows where you went, and the room's door seals | Fandom: those who open the curtains "instantly disappeared" |
| Fire exits (4, one per upper storey) | A grey steel door with a push bar under a green running-man sign, at a corridor bend (used, kind `l188-fireexit`) | Storey 1 → Level 1; storey 2 → Level 5; storey 3 → Level 4; storey 4 → Level 2. Each lands beside a door, which becomes the way back | Two-way (the door you arrive beside) | Miraheze's emergency exit; "destination in flux" read as "each door goes somewhere else" |
| The hatch | Lift the round iron hatch in the middle of the wooden deck and drop into the black (walked into the pit, `rel < −1.5`) | Level 37, surfacing in a pool | None (fell) | Original and Miraheze: the wooden circle as a trapdoor; Escape the Backrooms' hole → 37.2; Fandom 188.8 |
| A Window's arm | Being pulled through a predatory window | Death (decision 9.5) | – | Entity 2 |

**Proposed rows for LINKS.md** (the coordinator merges):

| From | Threshold | To | Way back | Owners |
|---|---|---|---|---|
| The Hub | The window (one per world, a slot of its own on a spoke, open to anyone) | 188, beside its Hub window | Two-way: that window leads back to the Hub window | hub: places the window tile and gives `HubWindowOf()`; 188: blocks, network, arrival |
| Level Fun | The confetti window (1 party room in 40) | 188, beside its confetti window | Two-way | fun: one line calling 188's `MarkL188FunWindow`; 188: the rest |

Not linked: Level !, The End, 974 (Kitty's detour still applies to every threshold), 3999, Level 94.

**Shared entrance sites:**
- **Level 0:** the window must not share a cell with a Fun party cell (`IsFunPartyCell` wins) or a Red Room.
- **Level 1:** the window goes on a plain concrete wall in a warehouse sector, never a maintenance hall. It is after the
  Hub door, End door, Fun stairs and Run door in LINKS.md's precedence: a tile already claimed is skipped.

---

## 3. Design

### 3.1 The experience

You climb down from a window sill onto wet moss. It is night here and always will be. Above the rooftops there is
nothing: no stars, no glow, a black that the eye cannot focus on. Round you, on every side, rows of small square
windows go up five storeys. Most are blind, a few glow behind their blinds, and one, a little way along, shows the yellow
room you just left.

Somewhere a pipe runs into a drain. In the middle of the courtyard a round wooden deck sits on the paving, with an iron
ring set in its centre. Up on the third floor, a window you are sure was dark a moment ago is lit, and someone is
standing in it, waving you up.

The only way in is a door at the north-west corner. Inside is a budget hotel: grey carpet, round downlights, and
identical unnumbered doors that go on round the courtyard and back to where you started.

Design goals, in order:
1. **The photograph.** Pale render, rows of small square windows, white blinds, warm glows, lawns and a wooden circle, a
   black sky.
2. **The windows are the level.** Every rule, every exit and the one deadly danger are windows. Learn their states and
   you can read the whole building from the courtyard.
3. **Small and knowable.** One building, mapped in an hour. The tension is in which doors to open, not in getting lost.

### 3.2 The building plan

**Building-local coordinates** (X 0-87 east, Z 0-57 south; origin `L188BuildX0/Z0`). Each wing is 17 deep. From the
courtyard outward (`d`):

| d | What | North wing Z | South wing Z | West wing X | East wing X |
|---|---|---|---|---|---|
| 0 | Courtyard façade (windows) | 16 | 41 | 16 | 71 |
| 1-5 | **Inner rooms** (courtyard-facing) | 15-11 | 42-46 | 15-11 | 72-76 |
| 6 | Inner corridor wall (doors) | 10 | 47 | 10 | 77 |
| 7-9 | **Corridor**, 3 wide, a ring round the building | 9-7 | 48-50 | 9-7 | 78-80 |
| 10 | Outer corridor wall (doors) | 6 | 51 | 6 | 81 |
| 11-15 | **Outer rooms** | 5-1 | 52-56 | 5-1 | 82-86 |
| 16 | Outer façade (windows onto nothing) | 0 | 57 | 0 | 87 |

- **The courtyard** is X 17-70 × Z 17-40: **54 × 24** clear, its long axis east-west.
- **Inner rooms** come in modules of 5 along the façade: a 1-block partition, then 4 blocks of room.
  - North and south wings: partitions at X = 16 + 5k (k = 0..11); rooms at X 17-20, 22-25, ... 67-70. That is
    **11 rooms** a side.
  - West and east wings: partitions at Z = 16 + 5k (k = 0..5); **5 rooms** a side.
  - Each room is **4 wide × 5 deep**: small, as Fandom says.
  - Its window is the middle two blocks of its façade stretch (X = 18-19 + 5k, Z = 18-19 + 5k).
  - Its door is in the corridor wall at its u = 3 column.
- **Windows per storey:** 11 + 11 + 5 + 5 = **32**. Over five storeys that is **160** (Miraheze: 90-200; Escape the
  Backrooms has 114).
- **Outer rooms:** the same module along the outer corridor wall, 17 a side on the long wings and 9 on the short ones.
  Their windows face `l188-nothing`.
- **Inner corner squares** (5 × 5, d1-5 × d1-5):

| Corner | Rooms |
|---|---|
| **NW** | Part of the **main stair** (below) |
| **NE** | **Lift lobby**: two dead lifts (`liftdoor`, "OUT OF ORDER" card), an ice machine (`icemachine`), a vending machine (`snackvending`) |
| **SE** | **Housekeeping and laundry**: linen shelves, a laundry cart, a sink |
| **SW** | **Linen store** and a broom cupboard |

- **Outer corner squares** are corner suites: a 5 × 5 room, a bigger bed, an armchair.
- **The main stair.** It takes the NW inner corner and the first west-wing room slot together: X 11-15 × Z 11-20, a
  hall 5 × 10.
  - **Ground storey:** its west façade slot (X 16, Z 18-19) is a **glazed double door onto the courtyard**, the only
    one. Canon: "a stairwell present near one end of the center courtyard".
  - **Upper storeys:** the same slot is a window onto the stair, so a viewer in the courtyard still counts 32 a storey.
- **The lobby** (ground storey only) replaces the south wing's outer rooms: Z 52-56, X 7-80, an open hall.
  - A reception desk with key pigeonholes at its centre; a breakfast area of round tables (west); low lounge chairs and a
    dead TV (east).
  - Three 3-wide openings in the corridor wall (Z 51) join it to the corridor.
  - Its front doors, glass, in the outer façade at X 43-44, open onto nothing (they are locked: 3.8).
- **Doors per storey:** most room doors are ordinary doors (open, close). About 5% are locked guest doors that the
  housekeeping keycard opens (3.7). The doors of rooms whose window shows another place are **sealed** (Fixed; "will not
  open"). None are numbered (canon: "unmarked"). Each storey has a stencil at the stair: "1"-"5".

One corner, ground storey (NW; `#` wall, `.` floor, `w` window, `D` door, `G` glazed courtyard door, `S`/`s` stair
flights A/B, `=` landing, `|` stair core wall):

```
 X: 0    5    10   15 17
Z0  ################w#ww##     outer façade (windows onto nothing)
    #.....#....#....#....      outer rooms
    #.....#....#....#....
    #.....#....#....#....
    #.....#....#....#....
Z5  #.....#....#....#....
Z6  ######D####D####D####D     outer corridor wall
Z7  #......................     corridor (ring)
    #......................
Z9  #......................
Z10 #...D#=====#D###D####D     inner corridor wall; D at Z11-12 is the stair's north door
Z11 #...##=====#....#....      north landing (=); north-wing inner rooms east of X16
Z12 #...##=====w....w....
Z13 #...##SS|ss#.ww.#.ww.      (north-wing courtyard windows are at Z16)
    #...##SS|ss#
    #...##SS|ss#
Z16 #...##SS|ss###ww####ww     courtyard façade of the north wing
Z17 #...D#=====#  courtyard ...
Z18 #...D#=====G
Z19 #...##=====G
Z20 #...##=====#
Z21 #...######w#               the first west-wing room's partition
```

(Indicative. The generator agent places doors on the plan's rules. The harness checks the counts in 5.5.)

**The courtyard** (X 17-70, Z 17-40):

| Feature | Where | Detail |
|---|---|---|
| **Four lawns** | Quadrants X 19-41 / 46-68 × Z 19-26 / 31-38 | Moss-grass turf, a low timber edging; tufts of moss stand on about 15% of their tiles |
| **Paving** | A path 2 wide along every façade and a cross 2 wide (X 43-44, Z 28-29) | Pale concrete pavers, moss in the joints |
| **The wooden deck** | A circle 8 across, centred on the cross (X 40-47 × Z 25-32) | Radial boards a few px proud of the paving (`l188-deck`, with arc edge pieces) |
| **The hatch** | 2 × 2 at the deck's centre (X 43-44, Z 28-29) | An iron hatch with a ring handle (3.4) |
| **The downpipe** | On the north façade at X 55, from the roof gutter to a drain at its foot | Always running with dark water: the "non-potable liquid", and a compass (it is always north) |
| **Bollard lamps** | Four, at the deck's diagonals | Dim (3.5) |
| **Benches** | Two, facing the deck from the east and west lawns' edges | |

### 3.3 Storeys, slabs, stairs and roof

- **One plan, five storeys.** Every storey is the ground storey's plan, except:
  - the lobby (ground only);
  - the courtyard door (ground only);
  - the link windows (ground only);
  - the fire doors (storey 1-4, one per bend).
  The generator draws storey `s = rel / 4` from the same tile, varying furniture, light, door states, boxes and window
  states by `Hash(seed, gx, gz, s)`. The 2D layout passes (sealing, arrivals, spots, notes) see the ground storey only.
  That is enough, because every arrival is on the ground.
- **Slab blocks.** Storey s's ceiling and storey s+1's floor are the same block. `l188-slab-{corridor,room,lobby,stair}`
  has a ceiling-white underside and the floor (carpet, tile, concrete) as its top. Downlights are slab variants with a
  round light on the underside (`l188-downlight-*`), so a light costs no extra block.
- **The stair: a scissor stair**, two flights of 4 steps each 2 wide, side by side with a core wall between (X 13).
  - **Flight A** (X 11-12, Z 16 → 13) climbs north from the south landing (Z 17-20) to the north landing (Z 11-12): one
    full storey.
  - **Flight B** (X 14-15, Z 13 → 16) climbs south from the north landing to the south landing.
  - **Order:** storey 0 → 1 by A, 1 → 2 by B, 2 → 3 by A, 3 → 4 by B, 4 → roof by A.
  - **Landings:** both have a slab at every storey level and a door into the west corridor (Z 11-12 and Z 18-19 in wall
    X 10). Whichever landing a flight reaches, the corridor is through the door.
  - **Headroom:** at least 4 everywhere (each flight's next use is two storeys up).
  - **Blocks:** `l188-stair-{side}` (concrete with a steel nosing) and `l188-handrail-{side}`, drawn by
    `(storey parity, z)`.
- **The roof.** Flight A from storey 4 ends on the north landing at rel 20, inside a stair bulkhead (X 11-15 × Z 11-20,
  walls to rel 24). Its door (X 16, Z 11-12) opens onto the roof.
  - The roof is a 17-wide ring of dark membrane at rel 20 with gravel patches, AC units (`acunit`) and vent stacks.
  - A 1-block parapet runs round both edges.
  - Looking down into the courtyard you see the whole window grid at once: the place to read the windows (3.4).
  - Looking out, there is only black.
  - A fall into the courtyard is 20 blocks.
- **The sky.** `l188-sky` at rel 33 over the courtyard and roof: unlit, pure black with a faint grain. With the night
  fog, the eye reads it as a starless sky.

### 3.4 The windows

**What a courtyard window can be.** Each is a 2 × 2 block window in the façade (parts `ll lr ul ur`) on a sill block.

| State | Looks like (from the courtyard) | Looks like (from inside the room) | Light |
|---|---|---|---|
| `closed` | Glass, white roller blind down behind it | The blind, down | 0 |
| `glow` | Blind down, glowing warm from a lamp behind | The blind; the bedside lamp on | Blind 6 |
| `open` | Blind up: the **real room** behind, dark | The blind rolled up; the courtyard through the glass | 0 |
| `lit` | Blind up: the real room, lamp on | As `open`, lamp on | (lamp) |
| `figure` | Blind up, the room lit behind; **a dark silhouette in the window**, standing | The same silhouette in the glass, facing in | Room lamp |
| `beckon` | As `figure`, one arm raised, the hand curling | As `figure` | Room lamp |
| `scene-<place>` | **Another place**, seen through the window (a peep-box, 3.4b) | (the room is sealed; never seen) | Per scene |

- **The real room shows.** `open`, `lit` and the figures use real transparency: you see the actual room through the
  glass (real 3D, nothing painted). Only the `scene-*` states paint, because they show somewhere that is not there.
- **Outer-façade windows:** `l188-outerwindow-{closed,open}`. Open, they show black (`l188-nothing` directly behind).

**3.4a The rules** (canon's two, plus the Figures):

1. **Link windows** (ground storey, 12 per world). Their blinds are up and they show another place. Their rooms are
   **sealed**.
   - **Climb in** (jump onto the sill and walk into the window) to go there: walked, two-way.
   - **Destinations** (fixed counts, positions by hash among the 31 ground windows; the Hub window on the north façade,
     the confetti window on the east): Level 0 ×3 (yellow wallpaper, a fluorescent troffer), Level 1 ×2 (grey concrete,
     a caged light), the Hub ×1 (orange sodium light on concrete), Level Fun ×1 (an orange party room, balloons, confetti
     drifting down the glass, muffled music), Level 2 ×1 (pipes, a red glow), Level 4 ×1 (office carpet, a desk), Level 5
     ×1 (a red hotel corridor), Level 6 ×1 (**pure black**), Level 9 ×1 (a night street, a porch light).
   - **Arriving** from another level's window, you land on the courtyard paving beside the window that shows where you
     came from (`beside` = a link window of that destination). That window is your way back.
2. **Opening the blind** of a closed window from inside its room (right-click the window; kind `l188-blind-<storey>`) is
   being **taken**: one-way, at once, to a place fixed for that window.
   - **Destination table** (by the window's key): Level 0 .16, 1 .10, 2 .08, **3 .07** (the August-1B nod), 4 .10,
     5 .10, 6 .05, 7 .04, 8 .04, 9 .08, 10 .04, 11 .04, 37 .04, 94 .02, The End .02, Level Fun .02.
   - **What changes in 188:** that window now shows the place (`scene-<place>`), visible from the courtyard, and the
     room's door is **sealed**.
   - **Reset:** after 3 in-game days the blind comes down and the door unseals. The window still leads to the same place
     (rule 1 of the network).
   - Blinds can only be opened from inside the room (the block behaviour checks which side the player is on).
3. **Predatory windows (Entity 2).** Each in-game day at midnight, about 1 in 16 courtyard-facing rooms' windows become
   `figure`/`beckon` for the day, picked by `Hash(seed, window, day)`.
   - **Excluded:** link windows, the stair window, sealed rooms, and any room a player is in at that moment.
   - **From the courtyard** you see someone standing in a lit room, waving you up. **Count the windows** across and up,
     and stay out of that room.
   - Their rooms are not locked. Canon: "Rooms correlating to these fake windows should be avoided at all costs."
4. **The rest change on their own.** Every in-game hour, about 5% of the other windows switch between `closed`, `glow`,
   `open` and `lit` (lamp on or off with them). That is canon's "ever-changing array", and why the number of lit windows
   is never the same twice.

**3.4b Scenes (peep-boxes).** A scene block is the window's frame and sill at the front. Behind it is a box 12 voxels deep
with a few **real voxel features** and a painted back wall:
- Level 0: a troffer strip across the top, a doorway frame;
- Level 1: a caged bulb, a concrete pillar;
- Hub: a lamp, the tunnel's curve;
- Fun: two balloons, a table edge, plus confetti particles at the window;
- Level 2: two pipes;
- Level 4: a desk edge and a monitor;
- Level 5: a door frame, a wall sconce;
- Level 9: a porch post and a lamp;
- Level 6: nothing (black);
- Level 37: white tile, a pool edge;
- Level 94: a green hill and a blue sky;
- The End: shelving;
- void: black with a faint shimmer, for the rare place with no picture (3, 7, 8, 10, 11 use their nearest look).

They must read at 20-40 blocks.

**3.4c The hatch.** `l188-hatch-{closed,open}` is a 2 × 2 iron hatch with a ring handle at the deck's centre.
Right-click opens it, swinging the plate up; it stays open until closed. Below is a black shaft to rel −6. Falling past
rel −1.5 is the threshold (walked into the pit; one-way, fell) to **Level 37**, surfacing in a pool. Message: "You fall
through cold black air into warm water."

### 3.5 Light, fog, sound, temperature, stability

**Light.**

| Where | Source | Value |
|---|---|---|
| Corridors | Round recessed **downlights** in the slab, every 4 blocks along the corridor's centre line | `lightHsv [7, 2, 12]` (warm white). About 15% dead, 3% flicker (`flickerIds`) |
| Rooms | A **bedside lamp** (nightstand) | `[7, 3, 10]`, on when the window is `glow`, `lit` or a figure, else off. Ceiling downlight off (dead) |
| Lobby | Downlights every 3 and a lit reception fascia | `[7, 2, 14]` |
| Stair | Green emergency bulkheads on each landing; EXIT signs | `[22, 5, 7]` |
| Courtyard | **Only the windows**: glowing blinds (6), lit rooms (through glass), link-window scenes (8-11; Level 6's black, 0), and four bollards | Bollards `[8, 2, 7]`. The deck at the centre stays dim (2-4): the windows are the light |
| Roof | Nothing but what spills over the parapet | |
| Outer windows, sky, void | None | |

**Fog** (`AtmosphereSystem.Levels` line and `L188Air`):

| Zone | Atmosphere | Title |
|---|---|---|
| Hotel (base) | `new(0.005f, 0.60f, 0.58f, 0.55f, 0f)`: a faint neutral grey | `level-20` on arrival |
| Courtyard (outdoor tiles, below rel 20) | `new(0.014f, 0.05f, 0.06f, 0.09f, -0.15f)`: blue-black night, a little ground haze | `level-2001` "The Courtyard" |
| Roof (rel ≥ 21) | `new(0.020f, 0.03f, 0.03f, 0.05f, 0f)` | `level-2002` "The Roof" |

**Sound** (`L188Sounds`; no hum anywhere: the lights here are silent, as in 188.8):

| Where | Loops | Spots |
|---|---|---|
| Courtyard | `l188/courtyard`: near silence, the faint breath of air handling somewhere on the roof | Positional `l188/pipe` at the downpipe (16 blocks); now and then a **knock on glass** from a random window (`l188/knock`, 3 soft raps) |
| Corridors and rooms | `l188/corridor`: hotel room tone | Distant (Roster): a door closing, a TV through a wall, a vacuum cleaner far off, ice dropping in the machine, a lift chime from the dead lifts, footsteps on the floor above |
| Predatory window | `l188/whisper` (comforting, wordless) within 6 blocks | Blinds rattle when a figure turns |
| Confetti window | `l188/partymuffled` within 12 blocks | Confetti particles drift on the courtyard side |

**Temperature** (`L188Temperature`):

| Where | °C |
|---|---|
| Courtyard | 8 (cold enough that a long stay wants clothes, which the wardrobes have) |
| Roof | 6 |
| Stair | 15 |
| Corridors, rooms, lobby | 21 |
| Hatch shaft | 4 |

`LevelTemperatures[20]` = 21.

**Reality Stability** (`L188Stability`):

| Where | Value |
|---|---|
| Inside a room with its door shut | 1.1: rest |
| Corridors, lobby | 0.95 |
| Courtyard | 0.85 (watched from every side) |
| Roof | 0.8 |
| Within 6 blocks of a predatory window | 0.5 |

A Peripheral seen (3.6) costs −0.02 at once.

### 3.6 Dangers and entities

**The Windows (Entity 2): the arm.** The level's one real killer, and only for the careless.
1. **Approach.** Within 6 blocks of a predatory window (inside its room, or on the courtyard paving below a ground-storey
   one), the whispers start and the figure turns to face you (it swaps to `beckon`).
2. **Grab.** Within **2 blocks** for 1 second, an **arm** (`l188-arm`, 4.7) shoots out of the window and grabs. It
   pulls you toward the window at 1.5 blocks/s and does 1 HP/s, for at most 5 s.
3. **Breaking free:**
   - **hit the arm twice** (it recoils and withdraws); or
   - **get 3.5 blocks away** (sprinting beats the pull; walking does not).
4. **Pulled in.** If your body reaches the window plane, you are pulled through: **death** (decision 9.5). Your things
   drop on the sill inside the room, and the figure is a little darker the next day.

**The Figures** are the same windows, seen from afar (Miraheze). Long looks cost nothing more than the stability
already listed.

**Peripherals** (Fandom), harmless.
- A client-side **HUD overlay**: a dark, blurred, tall human shape (`gui/188/peripheral-{1,2,3}.png`) fades in at the far
  left or right of the screen, at 40-60% opacity, for 1.5-3 s, about once every 1-3 minutes in corridors and the
  courtyard.
- If you turn toward it, it is gone before you get there. It has no physical form, so no entity is used.
- It costs −0.02 stability each time ("minor feelings of paranoia").

**The menace director** (Miraheze's extras, kept light):

| Entity | Band | Encounters | Weight | Notes |
|---|---|---|---|---|
| Skin-Stealer | Approach | Stalk, Hunt | 0.5 | |
| Smiler | Heartland | Glimpse, Stalk | 0.6 | `NeedsDark`: dead-light stretches, rooms with the lamp off |

- **Bands** (`MenaceSystem` case): `Safe` in a room with its door shut, unless the room is predatory. `Heartland` in the
  courtyard, the lobby and corridors of storeys 0-1. `Approach` on storeys 2-4, on the roof, and within 8 blocks of a
  link window.
- **Danger** `0.45`. `PickedOverShare` 0.3 (few come here). No dens, no wanderers, no refuge.

### 3.7 What there is to find (loot and vanilla hooks)

Level 188 is a **hotel**: plenty of cloth, warmth and a little food, and the cold courtyard to make the clothes matter.

| Where | What | Notes |
|---|---|---|
| Guest room: suitcase (35% of rooms; existing `suitcase` detail block) | `game:cloth-plain`, a vanilla clothing piece (`game:clothes-upperbody-commoner-shirt`, `...-lowerbody-commoner-trousers`, `...-foot-commoner-boots` ...), Almond Water, a wanderer's note | Drops as the existing suitcase does, plus 188's clothing rolls |
| Guest room: wardrobe (`l188-wardrobe`) | A spare blanket (`game:cloth-plain` ×1-2), a clothing piece 15% | Container |
| Guest room: minibar (`l188-minibar`, 60% of rooms) | `almondwater` 50%, `l188-juicebox` 40%, `crackers` 30% | Container |
| Guest room: bed | Salvage: `game:cloth-plain` ×2, `game:linen-normal-down` 10% | `Breakdown.cs` class Bedding |
| Guest room: supply box (1 room in 12) | The usual box | Placed by the generator at `4s+1` |
| Bathroom pod | A towel (`game:cloth-plain`) | |
| Housekeeping cart (corridors, 1 per wing per storey, 50%) | Cloth ×2-4, **`l188-keycard`** 25%, `game:candle` | Container |
| Laundry room (SE corner, every storey) | Linen shelves: cloth ×3-6 each | Container |
| Lobby | **Breakfast**: a cereal dispenser (`l188-cerealdispenser`, three portions of `l188-cereal`, then empty) and a juice dispenser (`l188-juicebox`). **Reception**: one `l188-keycard`, the guest book (lore), wanderer notes | |
| Lift lobby | Vending machine (`snackvending`): `crackers` | |

**Vanilla hooks:**
- **Clothing and the cold.** The courtyard's 8 °C and the roof's 6 °C are survivable briefly; wardrobes and suitcases
  give the clothes.
- **Cloth** for bandages and poultices.
- **Beds** are real vanilla beds (`BlockBed`), so you can sleep. Respawn stays in Level 0 (the anchor rule): beds never
  set a spawn here.
- **Candles** from the housekeeping carts.

**The keycard** (`l188-keycard`): a housekeeping master card.
- It opens the ~5% of guest rooms that are plainly locked (kind `l188-guestdoor-locked`). Those rooms are never picked
  over.
- It does nothing to a **sealed** door: "The card reader blinks red." Canon: no known method opens them.
- It is kept on use and works only in 188.

**Notes** (lang, through the existing note system; one in four notes found in 188 is one of these):
- "Count the windows from the yard before you go up. Someone standing in one: count across, count up, and stay out of
  that room."
- "Marta opened the blinds in a room on three. She was just gone. From the yard I watched her window light up yellow."
- "The window you came in by goes back. Mark it before you leave the yard."
- "The fire doors work. Each one goes somewhere different. None of them come back here except the way you went."
- "The iron ring in the deck: it opens. I heard water down there."

### 3.8 Runtime rules (`src/Regions/L188System.cs`)

Server:
- **Window states.** A record per courtyard window: id = (façade tile, storey) → state, scene, sealed-until-day. It is
  saved with the world.
  - On chunk load, it re-applies the state.
  - Every in-game hour, it flips about 5% of the free windows (and their room lamps).
  - At midnight, it re-picks the predatory set (3.4a.3).
  - It also unseals rooms whose 3 days are up.
- **Blinds.** The behaviour `BackroomsL188Blind` (on every window block; registered by the system, as `HubSystem` does
  `BackroomsHubDoor`):
  - It refuses from the courtyard side.
  - From the room side, on a closed window, it plays `l188/blindup` and sends the player through the network
    (`L188Used` kind `l188-blind-<s>`), then swaps the window to `scene-<destination>` and seals the door.
  - On a link window from inside (impossible: sealed), or a predatory window, it does nothing but whisper.
- **The arm** (3.6). Proximity checks every 250 ms for players in the level, near predatory windows only. It spawns and
  drives `l188-arm` and applies the pull and damage.
- **Sealed and locked doors.** Kinds `l188-sealed` (refusal "It will not open. Something holds it from the other side.")
  and `l188-guestdoor-locked` (opens with the keycard: the door block swaps to its open state and stays unlocked).
- **The front doors** (lobby): kind `l188-frontdoor`, always refusing: "Beyond the glass there is nothing at all."
- **Dispensers:** cereal and juice, three uses each, by position, saved.

Client:
- the Peripherals HUD;
- confetti particles at the Fun window.

---

## 4. Asset manifest (`tools/gen_188.py`)

Everything new is prefixed `l188-` and lives in `block/188/`, `blocktypes/188/`, `itemtypes/188/`, `shapes/block/188/`,
`sounds/ambient/188/`, `sounds/effect/188/`, `textures/gui/188/`.
- Textures are 32 × 32 (`texlib.S`) unless stated.
- Shapes are in voxels (16 per block), `bx(name, from, to, tex)` as in `gen_motion.py`.
- `{side}` = `north|east|south|west`, the way the block's front faces (Pier-facing, as the Hub's).
- "Real 3D" means elements, not paint.
- Keep each prop ≤ 14 elements.

### 4.1 Surfaces (cube blocks unless stated)

| Code | Texture / shape | Notes |
|---|---|---|
| `l188-paver-{plain,moss,cracked}` | Pale concrete pavers `#A8A49B`, two 16 px slabs per face, 1 px darker joints; moss variant: green `#4E6B35` in the joints; cracked: a hairline crack and a dark stain | Courtyard floor (rel 0) |
| `l188-turf-{a,b}` | Top: dense moss-grass, dark green `#3B5530` with lighter blades `#5F7F45`, damp darker patches; sides soil | Lawns. b is slightly yellower |
| `l188-mosstuft` | Plant shape: 6 crossed tufts 3-6 voxels tall | Non-solid, on ~15% of lawn tiles |
| `l188-edging-{side}` | **Real 3D** timber edge board 16 × 3 × 1.5 at the lawn's edge, on a paver base | Lawn borders |
| `l188-deck`, `l188-deck-edge-{straight,outer,inner}-{side}` | A slab 3 voxels high: radial timber boards `#7A5A3C`, weathered grey at the ends, 1 px dark gaps, bolt heads. Edge pieces cut the slab along a real arc (stepped boxes) over the paver | The wooden circle, 8 across |
| `l188-hatch-{closed,open}` | 2 × 2 multiblock, 16 × 3 × 16 per part, flush with the deck: riveted iron plate `#3E3F42` rusting at the rim, a **real 3D** ring handle (8 boxes, 6 across) on the centre seam; open: the plate stands vertical on its hinge side | Kind none (class `BackroomsL188Hatch`: right-click toggles; open is passable) |
| `l188-shaft` | Pure black `#050506` | Lines the hatch shaft |
| `l188-cladding-{plain,band,streak}` | Pale warm-grey render `#C9C4B8`, faint trowel texture, panel joint every 16 px; band: a horizontal joint line at mid-height (floor lines); streak: a grey rain streak below a sill | Courtyard façades (every block that is not a window) |
| `l188-sill-{side}` | **Real 3D** concrete sill 16 × 2 × 3 projecting 2 voxels, a drip groove, on a cladding block | Under every courtyard window (rel 4s+1) |
| `l188-coping-{side}` | Parapet top: a 2 voxel cap overhanging 1 on both sides, cladding below | Rel 21 |
| `l188-roof`, `l188-roofgravel` | Dark grey membrane `#3B3C3E` with seams; grey gravel | Roof |
| `l188-nothing` | `#030304`, a 1 px very faint noise, no light | Fixed. Everything round the building, behind outer windows |
| `l188-sky` | `#020203`, faint grain | Rel 33 |
| `l188-carpet-corridor` | Charcoal `#3A3D42` loop pile with a lighter grey geometric lattice `#55595F` | |
| `l188-carpet-room` | Mid grey `#6E6F70` cut pile, flecked | |
| `l188-tile-lobby` | Large grey porcelain `#9C9A95`, 16 px tiles | |
| `l188-tile-bath` | White 8 px tiles, grey grout | Pods |
| `l188-concrete-stair` | Painted concrete floor, grey `#8C8C88`, a yellow edge line on landings | Stair landings |
| `l188-wall-corridor-{plain,base}` | Light grey vinyl wallpaper `#B9B8B3`, fine linen texture; base: a **real 3D** white skirting 16 × 2 × 1 | Corridor walls |
| `l188-wall-room-{plain,base,feature}` | White `#E3E1DC`; feature: slate-blue `#4D5D6E` (the headboard wall) | Rooms |
| `l188-wall-stair` | Painted blockwork, pale grey, 8 px courses | Stair hall |
| `l188-slab-{corridor,room,lobby,stair}` | Top face: that zone's floor; bottom: white ceiling `#EDEDEA`; sides: concrete | Every storey slab (3.3) |
| `l188-downlight-{corridor,room,lobby}-{on,off,flicker}` | As the slab, bottom face with a round downlight: a 10 px white disc in a 1 px chrome ring; `on` `lightHsv [7, 2, 12]` (lobby 14); `flicker` `BackroomsFlicker` with `off` | |

### 4.2 Windows

| Code | Variants | Shape (per part, voxels) |
|---|---|---|
| `l188-window-{state}-{part}-{side}` | state: `closed, glow, open, lit, figure, beckon`; part: `ll, lr, ul, ur`; side: 4 | **Real 3D.** Frame: dark aluminium `#3D4043`, 1.5 thick on the outer edges of the 2 × 2, a 1 voxel mullion at the centre; glass plane 0.5 thick 3 voxels in from the courtyard face (transparent, faint reflection streak). **Blind:** a white `#ECE9E0` roller blind plane 0.5 thick, 2 voxels in from the room face. Down: covers the part; up: rolled into a 2 × 2 roll at the top of the upper parts, with a bottom bar 1 × 1 and a pull cord. `glow`: the blind is warm-lit (emissive texture), `lightHsv [7, 3, 6]`. `figure` and `beckon`: a flat **silhouette panel** 1 voxel thick in the glass plane, near-black `#0B0B0D`, edges soft (2 px alpha falloff): a head and shoulders in the upper parts, a torso and arms in the lower; `beckon`'s right arm is raised in `ur`, the fingers bent. Light absorption low (glass) except where the blind is down |
| `l188-window-scene-{place}-{part}-{side}` | place: `l0, l1, l2, l4, l5, l6, l9, l37, l94, hub, fun, end, void`; parts; sides | The same frame and sill. Behind the frame, a **peep-box** 12 voxels deep across the whole 2 × 2: a painted back wall (32 × 32 per part, perspective) and the real voxel features listed in 3.4b. Emissive back wall: `lightHsv` per place (l0 [9,4,10], l1 [0,0,8], hub [5,6,11], fun [5,4,10], l2 [0,5,7], l4 [0,0,9], l5 [2,5,8], l9 [6,3,6], l37 [30,1,11], l94 [8,3,13], end [7,3,9], l6 and void 0) |
| `l188-outerwindow-{closed,open}-{part}-{side}` | | As the courtyard window; open shows black behind |
| `l188-stairwindow-{part}-{side}` | | As `open` but with wired glass; the stair hall's façade slot on upper storeys |
| `l188-courtyarddoor-{l,r}-{lower,upper}-{side}` | | Glazed aluminium double doors, push bars, kick plates (vanilla door behaviour) |

### 4.3 Doors and signs

| Code | Look | Behaviour |
|---|---|---|
| `l188-guestdoor-{lower,upper}` | Grey-oak laminate `#8A7D6E` with a dark frame, a card reader with a green LED, a lever handle, a peephole, **no number** (as `door_block`) | Ordinary door |
| `l188-guestdoor-locked-{lower,upper}` | The same, red LED | Kind `l188-guestdoor-locked`; keycard opens (3.7) |
| `l188-guestdoor-sealed-{lower,upper}` | The same, the LED dark | Kind `l188-sealed`, Fixed |
| `l188-stairdoor-{lower,upper}` | Grey fire door, a wired-glass vision panel, a closer arm | Ordinary door |
| `l188-firedoor-{lower,upper}` | Grey steel, a **real 3D** push bar across, "FIRE EXIT" stencil | Kind `l188-fireexit` (used, two-way) |
| `l188-exitsign-{side}` | Green running-man box sign 10 × 5 × 2, `lightHsv [22, 5, 7]` | Over fire doors and the stair doors |
| `l188-floorsign-{1,2,3,4,5,roof}-{side}` | Stencilled number on a grey plate at the stair landings | |
| `l188-frontdoor-{l,r}-{lower,upper}` | Frameless glass doors with long steel pulls; black beyond | Kind `l188-frontdoor` (refuses) |

### 4.4 Props

| Code | Shape | Notes |
|---|---|---|
| `l188-bed-{headl,headr,footl,footr}-{side}` | A double bed over 2 × 2: base 16 × 6 grey upholstered, mattress 4 thick, white duvet with a folded grey throw across the foot, two pillows | Vanilla `BlockBed` behaviour (no spawn set; 3.7) |
| `l188-headboard-{l,r}-{side}` | Wall panel 16 × 12 × 2, grey fabric, **real 3D** buttons (1 × 1 × 0.5 grid) | On the feature wall |
| `l188-nightstand-{on,off}-{side}` | Cube nightstand 10 × 9 × 10 with a drawer; a lamp: base 3 × 4 × 3, shade 5 × 4 × 5 (lit: emissive, `lightHsv [7, 3, 10]`) | |
| `l188-desk-{side}` | Wall desk 16 × 11 × 8 on a single leg; a flatscreen TV 12 × 7 × 1 on a foot (texture off or snow) | |
| `l188-chair-{side}`, `l188-armchair-{side}` | Desk chair; a squat tub armchair in teal | |
| `l188-wardrobe-{lower,upper}-{side}` | Open hanging niche 14 × 32 × 8: a rail, 3 hangers (2 with grey hotel robes), a shelf with an iron and a safe | Container |
| `l188-minibar-{side}` | Small fridge 10 × 9 × 10 under the desk, glass door showing bottles | Container |
| `l188-luggagerack-{side}` | Folding rack 12 × 8 × 8 with straps | |
| `l188-podwall-{plain,door}-{side}` | **Bathroom pod**: a frosted glass panel 16 × 32 × 1 (two blocks tall, upper/lower), white frame; `door`: a sliding panel with a handle | Encloses the 2 × 2 pod in the room's corner |
| `l188-sink-{side}`, `l188-shower-{side}` | A wall basin with a mirror above; a shower tray with a glass screen and a rail head | Toilet: existing `toilet` |
| `l188-housekeepingcart-{side}` | A grey cart 14 × 14 × 8: folded towels, a linen bag, bottles, a mop | Container |
| `l188-linenshelf-{side}` | Steel shelving with folded sheets and towels | Container |
| `l188-reception-{straight,end}-{side}` | Modern desk 16 × 14 × 10, light wood fascia `#B49A78` with a backlit strip | |
| `l188-keyrack-{side}` | Wall pigeonholes 16 × 12 × 3, a 4 × 3 grid of slots, some with key cards | |
| `l188-roundtable`, `l188-loungechair-{side}` | Breakfast table; low lounge chair | |
| `l188-cerealdispenser-{3,2,1,0}-{side}`, `l188-juicedispenser-{side}` | Three gravity cereal tubes on a stand; a juice dispenser with two drums | Class `BackroomsL188Dispenser` |
| `l188-downpipe-{side}`, `l188-drain` | A grey downpipe 3 × 16 × 3 with brackets on the façade; at its foot a shoe and a drain grate with a dark puddle | The drain carries the `l188/pipe` ambient |
| `l188-bollard` | A squat bollard 4 × 10 × 4 with a light band, `lightHsv [8, 2, 7]` | |
| `l188-bench-{side}` | A slatted timber bench on concrete legs | |
| `l188-ventstack`, (reuse) `acunit` | Roof furniture | |
| (reuse) `suitcase`, `luggagecart`, `roomservicetray`, `servicetrolley`, `laundrycart`, `icemachine`, `snackvending`, `wetfloorsign`, `liftdoor`, `toilet`, `wastebasket` | | Corridor and room dressing (the code places them) |

### 4.5 The windows into 188, in other levels

| Code | Look | Behaviour |
|---|---|---|
| `l188-entrywindow-{l0,l1,hub,fun}-{part}-{side}` | A 2 × 2 window with no glass, a blind half up; behind, a peep-box of **188's courtyard at night**: dark grass, the deck's edge, and the opposite façade with three lit windows, painted on the back plane with 2 real voxel window frames. Frame per host: `l0` white-painted wood in yellow wallpaper, `l1` aluminium in bare concrete, `hub` concrete reveal, `fun` white sash with confetti on the sill and a red balloon tied to the latch. The interior is passable; collision only on the frame and sill. Light: a faint blue `lightHsv [24, 3, 4]` | Walked threshold (the tile's `Unders.L188Entrance`) |
| `l188-entrysill-{l0,l1,hub,fun}-{side}` | The sill block below (rel 1), matching the host | |

### 4.6 Items (`itemtypes/188/`)

| Code | Kind | Values |
|---|---|---|
| `l188-keycard` | Held item | A white plastic card with a grey stripe, "HOUSEKEEPING". Stack 1. Class `BackroomsL188Keycard` (opens `l188-guestdoor-locked`) |
| `l188-cereal` | Food | Grain, satiety 180 ("Stale, but it is cereal.") |
| `l188-juicebox` | Food | Fruit, satiety 120 |

### 4.7 Entity: `backrooms:l188-arm` (`tools/gen_188_models.py`, importing `rig` and the helpers of `gen_models.py`)

The Window's physical arm (Entity 2: "a physical representation of an arm to grasp and pull the victim"). It has no feet.
It is **anchored at the window's centre**, its root inside the glass, and reaches along +X toward the target. Positioned
and driven by `L188System`, with no AI tasks and no physics.

| Part | From → size (px) | Parent | Notes |
|---|---|---|---|
| Root | (0, 0, −1) 2 × 2 × 2 | – | Pivot (0, 1, 0); hidden in the glass |
| UpperArm | (1, 0.2, −0.8) 14 × 1.6 × 1.6 | Root | Far too long; skin near-black `#1C1C20` with a faint smoky mottle; the edges' texels semi-transparent |
| Forearm | (14, 0.3, −0.7) 13 × 1.4 × 1.4 | UpperArm | Pivot at the elbow |
| Hand | (26.5, 0, −1.25) 3 × 1 × 2.5 | Forearm | Palm down |
| Finger1-4 | each 2 segments of 2 × 0.5 × 0.5, splayed along z | Hand | Long, thin, slightly too many joints |
| Thumb | 2 segments of 1.5 × 0.5 × 0.5 | Hand | |

Animations (held keyframes are not needed; it should move smoothly and wrongly):

| Animation | Length | What it does |
|---|---|---|
| `reach` | 0.5 s | From folded (upper arm and forearm doubled back inside the window) to straight, fingers opening |
| `grab` | 0.2 s | Fingers close |
| `pull` | loop 1 s | The elbow bends slowly while the hand holds |
| `recoil` | 0.3 s | Snaps back into the glass, fingers spasming |
| `idle` | loop | Fingers flex |

- **Stats:** health 6; drops nothing; immune to knockback.
- **Sounds:** `effect/188/grab`, `effect/188/recoil`.
- **Lang:** `item-creature-l188-arm` / `creature-l188-arm` "A Window's arm".
- **Preview:** `tools/entrender.py` review sheet, as for the other entities.

**HUD textures** (`textures/gui/188/peripheral-{1,2,3}.png`, 128 × 256, RGBA): a tall, thin, slightly hunched human shape
in soft black. It has no detail: a gaussian-blurred silhouette (one standing straight, one leaning out from a corner, one
with the head tilted), alpha 0.85 at the core falling to 0 over 24 px.

### 4.8 Sounds (`tools/gen_188_sounds.py`, synthesised like `gen_level_sounds.py`; mono OGG)

| File | Length | Character |
|---|---|---|
| `ambient/188/courtyard.ogg` | 45 s loop | Near silence: very low filtered air movement, a far roof fan's slow beat at −30 dB |
| `ambient/188/corridor.ogg` | 45 s loop | Hotel room tone: soft broadband air handling, a faint 120 Hz from a distant plant room, no light hum |
| `ambient/188/pipe.ogg` | 8 s loop | Water running from a downpipe into a grate: a thin stream, gurgle, drips |
| `effect/188/knock.ogg` | 1.5 s | Three soft knuckle raps on glass, a little reverb |
| `effect/188/whisper.ogg` | 10 s loop | Overlapping soft, warm, wordless whispers (formant-filtered noise, `vowel`), slow |
| `effect/188/blindup.ogg`, `blinddown.ogg` | 1 s | A roller blind's rattle and snap |
| `effect/188/grab.ogg` | 0.8 s | A wet, sinewy lunge and a glass creak |
| `effect/188/recoil.ogg` | 0.6 s | A hiss and a snap back |
| `effect/188/taken.ogg` | 2 s | A soft air rush, a muffled thump, a distant single chime (opening the blind) |
| `effect/188/hatch.ogg` | 1.2 s | A heavy iron plate scraping up on a rusty hinge |
| `effect/188/partymuffled.ogg` | 14 s loop | A party heard through glass: a tinny tune (original), cheers, low-passed hard |
| `effect/188/liftchime.ogg` | 1 s | A two-tone lift chime, distant |
| `effect/188/tvwall.ogg` | 6 s | Muffled TV voices and static through a wall |
| `effect/188/vacuum.ogg` | 8 s | A vacuum cleaner far down a corridor, starting and stopping |
| `effect/188/icedrop.ogg` | 1.5 s | Ice cubes dropping into a bin |
| `effect/188/thump.ogg` | 1 s | Footsteps on the floor above, three, heavy |

**Roster `SoundsByLevel[188]`:** `liftchime`, `tvwall`, `vacuum`, `icedrop`, `thump`, `knock`, and the existing
`Footsteps`.

### 4.9 Lang (`assets/backrooms/lang/en.json`, 188's block only)

| Key | English |
|---|---|
| `level-20` | Level 188: The Courtyard of Windows |
| `levelhint-20` | Count the windows. Never open a blind. |
| `levelname-20` | Level 188 |
| `level-2001` / `levelhint-2001` / `levelname-2001` | The Courtyard / Someone is always at a window. / Level 188, the Courtyard |
| `level-2002` / `levelhint-2002` / `levelname-2002` | The Roof / There is nothing out there at all. / Level 188, the Roof |
| `l188-window-in` | You climb through the window. |
| `l188-window-arrive` | You climb down from a sill into a dark courtyard. Behind you, the window still shows where you came from. |
| `l188-taken` | You lift the blind. |
| `l188-taken-arrive` | The room is gone. There is no window behind you. |
| `l188-blind-outside` | The blind is on the inside. |
| `l188-sealed` | It will not open. Something holds it from the other side. |
| `l188-locked` | Locked. The card reader blinks red. |
| `l188-keycard-open` | The reader blinks green and the lock clicks. |
| `l188-keycard-sealed` | The card reader stays dark. |
| `l188-fireexit` | The push bar gives, and the door opens onto somewhere else. |
| `l188-fireexit-arrive` | The fire door bangs shut behind you. |
| `l188-frontdoor` | Beyond the glass there is nothing at all. |
| `l188-hatch-open` | The hatch grinds open onto black. Far below, water. |
| `l188-hatch-arrive` | You fall through cold black air into warm water. |
| `l188-grabbed` | Something has your arm. |
| `l188-brokefree` | It lets go and is gone back into the glass. |
| `l188-consumed` | (death message) was pulled through a window |
| `l188-note-1` .. `l188-note-5` | The five notes of 3.7 |
| `l188-guestbook` | A guest book: two hundred pages of names in different hands, every one checking in, none checking out. The last page says only "=)" in red. (Do not trust it: that is the Partygoers' mark.) |
| `blockhelp-l188-blind` | Open the blind |
| `block-l188-*`, `item-l188-*` | Names: "Courtyard window", "Window (lit)", "Window (someone in it)", "Window onto elsewhere", "Housekeeping keycard", "Breakfast cereal", "Juice box", "Iron hatch", "Wooden deck", "Moss turf", "Fire exit", "Guest room door" ... |

---

## 5. Code plan

### 5.1 Files 188 owns (names as the scaffolder made them)

| File | What goes in |
|---|---|
| `src/Worldgen/WorldLayout.Level188.cs` | **Where it is:** radius 4, the building origin. **The building plan:** a pure function `L188At(X, Z)` of building-local coordinates → zone, wing, room index, (u, v), facing; cached as one `Tile[]` for the whole building (`PlanCache`). **Per cell:** `BuildLevel188` copies the plan, `L188Edge` copies the plan's edge. **Windows:** the link windows (counts and positions by hash, fixed per world) and `L188WindowAt(x, z, storey)`. **Arrivals:** `IsL188ArrivalSpot` = courtyard paving; anchored spots beside link windows; `L188ArrivalHeight` (storey 0; a corridor bend's tile beside a fire door: `4 × storey + stand`). **Air and safety:** `L188WalkThrough`, `L188Temperature`, `L188Stability`. **Entrances elsewhere:** `MarkL188WindowInLevel0/1(b, mx, mz)`, `MarkL188FunWindow(b, ...)`, each with its own salt |
| `src/Worldgen/WorldGenerator.L188.cs` | `InitL188` (block ids with fallbacks, as `EndBlock` does). `Level188Block`: storey from rel; slabs, walls, windows (initial state by hash), doors, furniture by (u, v, storey), stairs by parity, roof, sky, void. `L188EntranceBlock` for the windows in other levels |
| `src/Thresholds/ThresholdNetwork.L188.cs` | `L188Walked`: link windows; entrance windows elsewhere; the hatch shaft. `L188Used`: `l188-blind-<s>`, `l188-fireexit`, `l188-sealed`, `l188-guestdoor-locked`, `l188-frontdoor`. Return features `IsL188LinkWindowTo(level)`, `IsL188EntranceWindow`, `IsL188FireDoor`. Salts `0x20C0` + k |
| `src/Thresholds/ThresholdSystem.L188.cs` | `L188Arriving` (face away from the window; the arrival message), `L188Redirect` (none), `L188MayPass` (true) |
| `src/AtmosphereSystem.L188.cs` | `L188Air` (courtyard, roof), `L188Sounds` (loops, pipe, whispers, party, knocks) |
| `src/Regions/L188System.cs` (new) | 3.8: window states and their saving, the hourly and daily changes, blinds behaviour, the arm, keycard, dispensers, hatch class; client Peripherals HUD and confetti |
| `tools/mapgen/L188Stats.cs` | `L188Modes` (`188stats`, `188map`), `L188LinkLabel`, `L188UseKind` |
| `tools/gen_188.py` (+ `gen_188_models.py`, `gen_188_sounds.py`) | All of section 4. Empties only its own `188/` folders first |

### 5.2 Encodings (188's own value blocks, from `Tiles.cs`)

| Range | 188's block | Use |
|---|---|---|
| `WallPattern` | 176-191 | `L188Cladding` 176, `L188Window` 177, `L188OuterWall` 178, `L188OuterWindow` 179, `L188CorridorWall` 180, `L188RoomWall` 181, `L188StairWall` 182, `L188Nothing` 183, `L188GuestDoor` 184, `L188FireDoor` 185, `L188StairDoor` 186, `L188CourtyardDoor` 187, `L188FrontDoor` 188, `L188Parapet` 189 |
| `FloorKind` | 196-211 | `L188Paver` 196, `L188Turf` 197, `L188Deck` 198, `L188CarpetCorridor` 199, `L188CarpetRoom` 200, `L188TileLobby` 201, `L188TileBath` 202, `L188StairLanding` 203 |
| `CeilingKind` | 64-71 | `L188Slab` 64, `L188Downlight` 65, `L188DownlightDead` 66, `L188Open` 67 (the courtyard: sky at 33) |
| `Props` (ushort) | 540-579 | Furniture on the ground storey: bed parts, nightstand, desk, chair, armchair, wardrobe, minibar, luggage rack, pod walls, sink, shower, toilet, housekeeping cart, linen shelf, reception, key rack, round table, lounge chair, dispensers, bench, bollard, downpipe, drain, moss tuft (walk-through: moss tuft, drain) |
| `Unders` | 110-119 | `L188LinkWindow` 110 (façade tile; `Detail` = destination code), `L188Entrance` 111 (in other levels; `Detail` = host 0/1/Hub/Fun), `L188Hatch` 112, `L188Shaft` 113, `L188FireLanding` 114 (corridor bend beside a fire door; `Height` = its storey) |
| `Overheads` | 100-109 | `L188ExitSign` 100 |
| `Decor` | 248-255 | `L188FloorSign` 248, `L188KeyRack` 249, `L188Headboard` 250, `L188Downpipe` 251 |
| `Pipes` | 80-89 | unused |
| Tile fields on 188's tiles | | `Zone` = 0 solid, 1 courtyard, 2 courtyard façade, 3 inner room, 4 inner corridor wall, 5 corridor, 6 outer corridor wall, 7 outer room, 8 outer façade, 9 stair hall, 10 lift lobby, 11 housekeeping, 12 linen store, 13 corner suite, 14 lobby. `Detail` = room index in its wing (0-16). `Stack` = u \| (v << 3) inside a room. `Pier` = the way the wing faces the courtyard. `Height` = step index on stair tiles |
| Title keys | 2001-2099 | 2001 courtyard, 2002 roof |
| Salts | `0x2000-0x20BF` layout, `0x20C0-0x20FF` thresholds | `SaltL188Shape` 0x2001 (exists), `SaltL188Link` 0x2002, `SaltL188Furnish` 0x2003, `SaltL188Window` 0x2004, `SaltL188Prey` 0x2005, `SaltL188Lock` 0x2006, `SaltL188EntranceL0` 0x2010, `SaltL188EntranceL1` 0x2011, `SaltL188EntranceFun` 0x2012 |

(The ranges are the ones the scaffolder put in `Tiles.cs`. CONTRACT.md does not list ids 19-20 yet, so the coordinator
should confirm the salt and title ranges there.)

### 5.3 Hooks in shared code (small, local edits)

1. **`WorldGenerator.ColumnBlock`:** one line beside Run's and End's, for the windows into 188 in other levels:
   `if (t.Under is >= Unders.L188First and <= Unders.L188Last && t.Level != WorldLayout.Level188 && L188EntranceBlock(t,
   gx, gz, y - Geometry.FloorFor(t.Level), out fluid) is int w and >= 0) return w;`. Ask the coordinator; End and Run set
   the precedent.
2. **`WorldLayout.Level0.cs`** after `DressFunPartyCell`: `if (IsL188WindowCell(mx, mz)) MarkL188WindowInLevel0(b, mx,
   mz);`. **`WorldLayout.Level1.cs`** in the warehouse sector builder, likewise. Each has its own salt; `layouthash` will
   show only Levels 0 and 1 changing, at those cells.
3. **`WorldLayout.LevelFun.cs`** (Fun's file): one line in the party-room dresser calling `MarkL188FunWindow`, own salt.
4. **`WorldGeometry`:** `L188BandDepth = 6`.
5. **Your lines:**
   - `AtmosphereSystem.Levels` (base fog);
   - `Roster.ByLevel` and `SoundsByLevel`;
   - `Danger.OfLevel` (0.45);
   - `MenaceSystem` case (bands, 3.6);
   - `PickedOverShare` (0.3);
   - `LevelTemperatures[20]` = 21;
   - `Protection.RoofFrom` (`RoomHeight + 1` is fine per storey; mark façades, windows, doors, hatch, stair, sky and
     nothing **Fixed**);
   - `Breakdown.cs` classes (bedding, laminate, glass);
   - `BackroomsMapLayer` (the shared case shows the ground storey; enough).
6. **`IsWalkThroughProp`** already asks `L188WalkThrough`.

### 5.4 Requests to other agents

- **Hub agent:** one **window slot** on a spoke (not a carved door), placing a tile with `Unders.L188Entrance`,
  `Detail = 2`, facing the sidewalk, drawn with `l188-entrywindow-hub-*` and `l188-entrysill-hub-*`. Also a lookup
  `HubWindowOf()` → its position, so 188's Hub link window finds its arrival directly (`FindArrival`'s 6-cell search
  would rarely find one window). Optional: sigil **45** reserved for 188 should the user prefer a keyed carved door
  (decision 9.8): a small disc inside a **square** frame of 12 small circles (windows round a courtyard).
- **Fun agent:** the one-line hook above; agreement that the confetti window is two-way, and its arrival is a party room
  floor tile beside it.
- **Scaffolder / coordinator:** CONTRACT rows for id 20 (salts, title keys); the `ColumnBlock` hook; the region radius
  change (`L188Radius => 4`).

### 5.5 Harness and verification

`188stats` checks:
- the building fits its 3 × 2 cells, and every non-building cell of the region is solid;
- the courtyard is 54 × 24;
- every storey has 32 courtyard windows (11/11/5/5, the stair window counted);
- exactly 12 link windows with the listed destination counts, the Hub window on the north façade and the Fun window on
  the east;
- every link-window room is sealed and holds no arrival;
- the ground storey is reachable from the courtyard through the one door (2D flood);
- the stair reaches every storey and the roof (a 3D walk over the generator's blocks, done in the harness with
  `ColumnBlock`: a column scan per stair tile);
- 4 fire doors on storeys 1-4 at distinct bends;
- the hatch shaft;
- ms per cell.

Also:
- `188map` → `region.bin` for `render_region.py`: courtyard, windows by state, link windows coloured by destination.
- `regions` (SPAWN 1000/2000/4000/16000): 60/60 arrivals, none trapped, all in the courtyard.
- `links`: Hub window ↔ 188 Hub window; Fun window ↔ confetti window; L0/L1 windows ↔ link windows (or thin spot);
  blinds one-way; fire exits paired with a door; hatch → 37.
- `layouthash`: only Levels 0 and 1 change (and Fun's own hash, if its harness has one), at the entrance cells.
- **Headless server** (port 42480): dump the courtyard and a corridor, then render (`entrender.py` for the arm). Check:
  - window light and blind states;
  - the stair walk;
  - a blind opened from inside sends you and seals the door;
  - a predatory window grabs, and two hits free you.

### 5.6 Phases

| Phase | Work | Verify |
|---|---|---|
| 1. The building | Radius, origin, plan, edges, generator (surfaces, slabs, walls, windows in their initial states, doors, stair, roof, sky), lighting band, fog, sound loops | `188stats`, render; headless dump of courtyard and storey 3 |
| 2. Rooms and loot | Furniture by (u, v, storey), containers, dispensers, keycard, notes, lobby | Headless: open rooms on several storeys |
| 3. Windows and ways | `L188System` states, blinds, sealing, link windows, fire exits, hatch, the entrances in Levels 0 and 1, the Hub and Fun windows | `links`, `layouthash` |
| 4. Danger | The arm (model, animations), predatory windows, whispers, Peripherals HUD, roster | Headless: `/backrooms goto 188`, approach a predatory window |
| 5. Words | Handbook, README, lang | |

### 5.7 Risks

- **Multi-storey thresholds in a 2D network.** Blinds on five storeys share a façade tile. The fix:
  - each storey's blind uses a distinct source, the room tile at depth `s + 1` behind the window (unique per storey);
  - the kind string carries the storey.
  Fire doors sit at four different bends. Link windows are on the ground storey only.
- **Window block count.** 13 states × 4 parts × 4 sides plus scenes is about 400 variants: one blocktype with variant
  groups. Peep-box shapes: keep each ≤ 14 elements.
- **Transparency and light through glass.** Verify in a client that lit rooms read from the courtyard. Fallback: give
  `lit` a faint emissive inner blind roll.
- **The arm's pull** must not fight the player's movement badly over the network. Apply it as a capped velocity nudge
  each server tick, as `MotionSystem`'s soft landing does.
- **Fixed façades and grief.** Everything structural is Fixed. Furniture salvages as usual.

---

## 6. Survival role

| | Level 188 |
|---|---|
| Teaches | Reading a place before entering it: windows as information, counting, choosing which doors to open |
| Gives | A rest stop (rooms with doors that shut), clothes and cloth, a little food, a keycard's untouched rooms, and many ways on: twelve windows to six main levels, the Hub and Fun, four fire exits, the hatch to the Poolrooms |
| Takes | Warmth in the courtyard; the predatory windows; and the gamble of a blind (a one-way trip to anywhere) |
| Fits the loop | A crossroads and wardrobe, never a home: no farming, and the anchor rule as always |

---

## 7. Handbook text (for `tools/gen_guide.py`)

**`PAGES["levels"]`, one paragraph:**

> **Level 188: The Courtyard of Windows.** A dark courtyard of mossy lawns and a round wooden deck, walled in by a
> five-storey hotel with 160 small square windows, under a black sky. You come in through a window and climb down into
> the courtyard. **The window you came in by still shows where you came from, and leads back.** Other windows on the
> ground floor show other places, and lead there. The only door in is at the north-west corner; inside, grey corridors
> run round the courtyard past unnumbered rooms. **Never open a blind from inside a room:** whoever does is gone, and the
> window lights up with wherever they went. **If someone is standing in a window, waving, count which room it is and
> stay out.** Get close and an arm comes out of the glass; hit it twice or run. The rooms have clothes, cloth, beds and a
> little food; the courtyard is cold (8 °C). Fire exits on the upper floors lead out, each somewhere different, and the
> iron ring in the deck opens onto a long fall into water.

**`PAGES["thresholds"]`, new bullets:**

- Two-way: a **window where no window should be** in **Level 0** or **Level 1** ↔ Level 188's courtyard, beside a window
  showing where you came from. **The Hub's one window** ↔ Level 188. A **party-room window with confetti on the sill** in
  **Level Fun** ↔ Level 188's confetti window. Level 188's **fire exits** (storeys 2-5) ↔ Level 1, 5, 4 and 2.
- One-way: in Level 188, **opening a blind** from inside a room → somewhere (always the same place for that window);
  **dropping through the hatch** in the wooden deck → Level 37.

**`PAGES["entities"]`:**

> **The Windows** (Level 188). A window with someone standing in it, beckoning, in a lit room. Within two blocks a long
> black arm comes out of the glass and pulls. Hit it twice, or sprint clear, before it pulls you through. The figures move
> to other windows every night. **Peripherals** are only ever at the edge of your sight, and are gone when you look. They
> do nothing but unsettle you.

**`PAGES["salvage"]`:**

> **Level 188:** suitcases and wardrobes (clothes, cloth), minibars (Almond Water, juice, crackers), housekeeping carts
> and the laundry (cloth, candles, the **housekeeping keycard**, which opens the few locked guest rooms but never a
> sealed one), breakfast in the lobby (cereal, juice). Beds salvage to cloth.

**README:** a "## Level 188: The Courtyard of Windows" section from 3.1-3.7. The threshold rows as in 2.2 go in the
two-way, thin-spot and one-way groups. The items go in the items list.

---

## 8. Integration with the other new levels

- **The Hub (17):** the window (two-way), canon's original entrance. See 5.4 and decision 9.8.
- **Level Fun (15):** the confetti window (two-way), canon's own line, now real. Level Fun's curtain weight (2%) is a
  second, one-way way in.
- **The End (16):** 2% of blinds lead there. No fixed link.
- **Level 974 (18):** Kitty's detour applies to 188's thresholds like any.
- **Level ! (14), Level 3999 (19):** none. Escape the Backrooms reaches 188 from "Level !~!", a different level.
- **Level 37:** one-way in by the hatch (Escape the Backrooms; Fandom 188.8). Nothing back.

---

## 9. Decisions for the user

1. **Which Level 188.**
   - **Recommended:** the **Courtyard of Windows** (the photograph; the original 1000dumplings page via Fandom; Fandom,
     Miraheze, Escape the Backrooms; Level Fun's canon).
   - Alternative: Wikidot's later "August-1B" planet (deleted). Recommended only as a nod: Level 3 among the blinds'
     destinations.
2. **Size.**
   - **Recommended:** **one building**, shared by everyone: 88 × 58 blocks, five storeys and a roof, 160 courtyard
     windows. Canon calls it of "meager size", and the level's game is reading one place, not getting lost.
   - Alternative: an endless lattice of identical courtyards joined by corridors.
3. **Five storeys and a roof.**
   - **Recommended:** yes (Fandom's five floors; the roof view is where you read every window at once).
   - Alternative: ground storey and one more, cheaper.
4. **Opening a blind = taken, one-way, to a fixed place per window;** the window then shows it and the room seals for 3
   in-game days.
   - **Recommended:** yes (Fandom's rule, made fair by the network).
   - Alternative: blinds do nothing.
5. **Pulled through a predatory window.**
   - **Recommended:** **death**, as Level !'s capture is. Fair warning: the figure, the whispers, a 1-second grace and two
     ways to break free.
   - Alternative: taken one-way to Level 6 at 4 HP.
6. **Predatory windows move every in-game night** (about 1 in 16 rooms).
   - **Recommended:** yes. You must look again each day.
   - Alternative: fixed per world.
7. **Peripherals** as a client HUD effect with a small stability cost.
   - **Recommended:** yes.
   - Alternative: leave them out.
8. **The Hub link.**
   - **Recommended:** **a window, open to anyone, two-way**, as canon has it ("look for a window in The Hub, and climb
     in").
   - Alternative: a keyed carved door like the others (sigil 45, key `hub-key-l188` behind 188's reception desk), one-way.
9. **The confetti window to Level Fun, two-way.**
   - **Recommended:** yes.
10. **Windows in Level 0 (1 cell in 300, outer 60%) and Level 1 (1 in 250, warehouse sectors).**
    - **Recommended:** yes (Fandom and Miraheze).
    - Alternatives: Level 0 only; or also a window in Level 3 (the August-1B nod) as a third way in.
11. **Fire exits:** four, two-way, to Levels 1, 5, 4 and 2.
    - **Recommended:** yes (Miraheze's emergency exit).
    - Alternative: none, leaving only windows and the hatch.
12. **The hatch to Level 37, one-way.**
    - **Recommended:** yes (the original's rumoured trapdoor, Escape the Backrooms' hole).
    - Alternative: the hatch is painted shut (decor only).
13. **Other entities:** Skin-Stealers (stalk/hunt, upper floors) and Smilers in the dark (Miraheze).
    - **Recommended:** yes, light (weights 0.5 / 0.6).
    - Alternative: the Windows and Peripherals only (Fandom).
14. **The housekeeping keycard.**
    - **Recommended:** yes (opens only plainly locked rooms, never sealed ones).
15. **Lifts.**
    - **Recommended:** dead ("OUT OF ORDER"); stairs only.
    - Alternative: working in-level lifts between storeys (Escape the Backrooms).
16. **Danger 0.45**, scaled by the *Backrooms entities* world setting.
    - **Recommended:** yes.
17. **Order of work.**
    - **Recommended:** phases 1-3 first (the building and its windows are the level), then the arm (4).

---

## Manifest changes (phase 2)

Written by the **code** agent for the asset agent (append-only; newest last). Where this list and section 4 differ,
**this list wins**: it is exactly what `WorldGenerator.L188.cs` and `Regions/L188System.cs` look up. Every lookup has a
fallback, so a missing block shows as plain concrete or air (logged once as "Level 188: missing block").

**Conventions.** `{side}` = `north|east|south|west`, the direction the block's *front* faces (for a façade or wall block,
the face that shows the named finish; its opposite face is room white `#E3E1DC` unless stated). `l`/`r` in a part name =
left/right **as seen by someone standing in front of that face, looking at it**. Wall-hung pieces (signs, headboards,
the key rack, the downpipe) sit in the *air* cell with their back against the wall behind them, front = `{side}`.

**M1. Structure and surfaces**

| Code | Notes |
|---|---|
| `l188-nothing`, `l188-sky`, `l188-shaft` | As 4.1. No light |
| `l188-paver-{plain,moss,cracked}`, `l188-turf-{a,b}` | Courtyard ground, rel 0 |
| `l188-mosstuft` | rel 1 on lawns; non-solid, no collision |
| `l188-edging-{side}` | rel 1 on a lawn tile next to paving; the board stands on the block's `{side}` edge (toward the paving). Low, non-solid |
| `l188-deck` | rel 1: a slab 3 voxels high (collision 3/16) of radial boards |
| `l188-deck-round-{ne,se,sw,nw}` | As `l188-deck` with that corner cut off by a quarter circle of radius 16 voxels (stepped boxes) |
| `l188-hatch-{closed,open}-{nw,ne,sw,se}` | rel 1, one quarter each of the 2 × 2 hatch (nw = its north-west quarter). Closed: a plate 3 voxels high like the deck, the ring handle on the shared centre corner. Open: the plate stands up on its outer edge (nw/ne hinge on the north edge, sw/se on the south), **no collision over the opening**. Behaviour **`BackroomsL188Hatch`** (right-click opens or shuts all four) |
| `l188-cladding-{plain,band,streak}-{side}` | Courtyard façade: render on the `{side}` face (toward the courtyard) and both ends, room white opposite |
| `l188-sill-{side}` | rel 4s+1 under a courtyard window, the sill projecting toward `{side}` |
| `l188-coping-{side}` | Parapet, rel 21, drip toward `{side}` (inner and outer edges of the roof) |
| `l188-slab-{corridor,room,lobby,stair,bath,roof}` | Top = that floor (charcoal carpet, grey carpet, grey porcelain, painted concrete, white 8 px tile, dark roof membrane); bottom = white ceiling; sides concrete |
| `l188-downlight-{corridor,room,lobby}-{on,off,flicker}` | The matching slab with the round light on its bottom face. `on` lightHsv `[7, 2, 12]` (lobby `[7, 2, 14]`); `flicker` like `end-troffer-flicker` (same block entity), its dark state `-off` |
| `l188-wall-corridor-{plain,base}-{side}` | Grey vinyl wallpaper on the `{side}` face (toward the corridor), room white opposite; `base` adds the 3D skirting on `{side}` |
| `l188-wall-room` | White on every face (partitions, outer façade, lobby) |
| `l188-wall-room-feature-{side}` | Slate blue `#4D5D6E` on the `{side}` face (the headboard wall), white opposite |
| `l188-wall-stair` | Painted blockwork on every face (also the fill under the stair flights) |
| `l188-roofgravel` | rel 21: a loose gravel layer 2 voxels high, non-solid |

**M2. Windows** (2 × 2 blocks: parts `ll lr ul ur` = lower-left, lower-right, upper-left, upper-right as seen from the
`{side}`, i.e. from the courtyard for courtyard windows)

| Code | Notes |
|---|---|
| `l188-window-{closed,glow,open,lit,figure,beckon}-{ll,lr,ul,ur}-{side}` | As 4.2. Solid (glass). Behaviour **`BackroomsL188Blind`**. (The Hub also draws `l188-window-lit-*` as its window into 188; the same behaviour makes it climbable from there.) |
| `l188-window-scene-{l0,l1,l2,l4,l5,l6,l9,l37,l94,hub,fun,end,void}-{ll,lr,ul,ur}-{side}` | As 4.2. **Collision on the frame only**: these are walked into from the sill on the ground storey. Behaviour `BackroomsL188Blind` |
| `l188-stairwindow-{ll,lr,ul,ur}-{side}` | Wired glass, no blind, solid |
| `l188-outerwindow-{closed,open}-{ll,lr,ul,ur}-{side}` | `{side}` = the room side (the inside); the outside is black. Behaviour `BackroomsL188Blind` (it only rolls the blind) |

**M3. Doors and signs**

| Code | Notes |
|---|---|
| `l188-guestdoor-{closed,open,locked,sealed}-{lower,upper}-{side}` | `{side}` = the corridor face (card reader, lever); hinge on the left as seen from the corridor. `closed`, `locked`, `sealed`: a full solid leaf; `open`: the leaf swung 90° into the room along the hinge edge (a 2-voxel panel, collision only there). Reader LED green / red / dark. Behaviour **`BackroomsL188Door`** |
| `l188-stairdoor-{closed,open}-{lower,upper}-{side}` | Grey fire door, wired-glass panel; same rules and behaviour. Also the roof door |
| `l188-courtyarddoor-{closed,open}-{l,r}-{lower,upper}-{side}` | Glazed aluminium double door, `{side}` = the courtyard face, `l`/`r` leaves as seen from the courtyard; open leaves swing inward. `BackroomsL188Door` |
| `l188-firedoor-{lower,upper}-{side}` | `{side}` = the corridor face, push bar. `BackroomsThreshold` kind **`l188-fireexit`** |
| `l188-frontdoor-{l,r}-{lower,upper}-{side}` | `{side}` = the lobby face; black beyond. `BackroomsThreshold` kind **`l188-frontdoor`** |
| `l188-exitsign-{side}` | Wall-hung over fire doors and stair doors, at the door's top + 1 |
| `l188-floorsign-{1,2,3,4,5,roof}-{side}` | Wall-hung beside stair-landing doors, rel 4s+2 |
| `l188-stair-{side}` | A standard stair block that **ascends toward `{side}`** |

**M4. Props** (rel 4s+1 unless stated; `{side}` = the way the front faces)

| Code | Notes |
|---|---|
| `l188-bed-{l,r}-{head,feet}-{side}` | A double bed of two single halves side by side, each a vanilla-style 2-block bed (class **`BlockBed`**, `part` head/feet, `{side}` as vanilla beds use it, the direction from head to feet). `l`/`r` = the half on the left/right of someone lying in it |
| `l188-headboard-{l,r}-{side}` | rel 4s+2 over the head tiles, wall-hung |
| `l188-nightstand-{on,off}-{side}` | Lamp lit (`[7, 3, 10]`) or dark |
| `l188-desk-{side}`, `l188-armchair-{side}` | As 4.4 |
| `l188-wardrobe-{lower,upper}-{side}`, `l188-minibar-{side}` | Breakable stores: give them `drops` as 3.7's rolls (clothes, cloth / Almond Water, juice, crackers) |
| `l188-shower-{side}`, `l188-poddoor-{side}`, `l188-sink-{side}` | The bathroom pod's three pieces, each with its own frosted-glass panel(s): shower: a panel on its **right** edge (seen from its front); poddoor: a panel on its right edge and the sliding door on its **front** edge; sink: a panel on its **front** edge. Toilet: existing `toilet-{side}` |
| `l188-housekeepingcart-{side}`, `l188-linenshelf-{side}` | Breakable, drops as 3.7 (the cart: 25% `l188-keycard`) |
| `l188-reception-{straight,end}-{side}`, `l188-keyrack-{side}` (wall-hung, rel 2), `l188-roundtable`, `l188-loungechair-{side}` | Lobby |
| `l188-cerealdispenser-{3,2,1,0}-{side}`, `l188-juicedispenser-{3,2,1,0}-{side}` | Class **`BackroomsL188Dispenser`** (right-click gives one `l188-cereal` / `l188-juicebox` and steps down; `-0` is empty) |
| `l188-downpipe-{side}` (rel 2-20, in the courtyard cell against the north façade), `l188-drain` (rel 1 at its foot) | |
| `l188-bollard`, `l188-bench-{side}`, `l188-ventstack` | |
| Reused | `suitcase-{side}`, `roomservicetray-{side}`, `laundrycart-{side}`, `icemachine-{side}`, `snackvending-{side}`, `wetfloorsign-{side}`, `acunit-{side}`, `toilet-{side}`, `liftdoor-drywall-{lower,upper,header}-{l,r}-{side}` |

**M5. Windows into 188 in other levels**

| Code | Notes |
|---|---|
| `l188-entrywindow-{l0,l1,fun}-{ll,lr,ul,ur}-{side}` | As 4.5; `{side}` = the face toward the room the viewer stands in; **no collision in the opening** (walked into from the sill) |
| `l188-entrysill-{l0,l1,fun}-{side}` | rel 1 below it, solid |

(The Hub draws its own window with `l188-window-lit-*`; no `-hub` entry window is needed.)

**M6. Items, entity, textures, sounds:** as 4.6-4.8. The arm: `entities/l188-arm.json`, code `l188-arm`, **class
`BackroomsL188Arm`** (registered by the code), no AI tasks, no gravity or physics behaviours, health 6, hitbox about
0.6 × 0.6. The code puts it at the window's centre and turns it (yaw) toward its victim, so the arm reaches along the
model's **forward axis** (rig convention: the model faces −X). `l188-keycard`, `l188-cereal`, `l188-juicebox`: plain
items (the code checks the keycard by code). Peripheral textures: `textures/gui/188/peripheral-{1,2,3}.png`.

**M7. Lang the code uses:** the keys of 4.9, plus `blockhelp-l188-door` ("Open / close"), `blockhelp-l188-hatch`
("Lift the hatch"), `blockhelp-l188-window` ("Climb through"), `l188-blind-up` ("The blind is already up."),
`l188-dispenser-empty` ("Empty."), `l188-hub-window` ("You climb through the window into the dark.").

**M8. Titles (code agent, later):** the courtyard is announced with the level's own title (`level-20`), so arrivals see
"Level 188: The Courtyard of Windows". The sub-zone titles are therefore: **`level-2001` = "The Hotel"** (hint: "The
doors have no numbers. Count them.", name "Level 188, the Hotel") and `level-2002` = "The Roof" (as 4.9). Please replace
4.9's "The Courtyard" for 2001.

**M9. Downlight tops (code agent, later):** the code also looks up `l188-downlight-stair-{on,off,flicker}` (top = the
stair slab's painted concrete) and `l188-downlight-roof-{on,off,flicker}` (top = the roof membrane: the lights in storey
4's ceiling). Until they exist it falls back to the plain slab (no light there).

**A1. Asset agent, built (2026-10-09).** Every code of M1-M9 exists (M8's titles and M9's downlights included), from
`tools/gen_188.py` (+ `gen_188_kit/_tex/_props/_models/_sounds.py`); its check confirms every texture, shape and sound
resolves. Notes for the code:
- **Behaviours and classes** are written into the JSON only if the code registers them (`gen_188_kit.registered`); they
  were all registered when this ran. Re-run `bash tools/locked.sh run python tools/gen_188.py blocks` after adding a new one.
- **Wall-hung pieces** (exit sign, floor sign, key rack, headboard, downpipe) sit against the *south* edge of their air
  cell when facing north, i.e. their back is on the wall behind them; front = `{side}`. The headboard reaches 4 voxels
  down into rel 4s+1 behind the pillows.
- **`l188-drain`** has no side: it assumes the façade (and its downpipe) to its north, as on the north façade.
- **Doors:** open leaves swing 90° about the hinge and lie in the next cell (room side); collision only on the leaf.
  Closed doors collide on a 2-voxel slab in the middle of the wall. Fire, front and stair doors: as M3.
- **Windows:** courtyard windows collide on the full block; `lightAbsorption` 99 when `closed`, 0 for `glow`
  (`lightHsv [7, 3, 6]`), 1 otherwise; `renderpass` Transparent. Scene and entry windows collide on the frame only;
  scenes are lit per 4.2 (absorption 0), `l6` and `void` dark (99). Entry windows: `[24, 3, 4]`.
- **Hatch:** closed = 3/16 slab; open = the standing plate only (north quarters on z 0-0.2, south on z 0.8-1).
- **Additions** (unused by the code, free to place): `l188-edging-corner-{side}` (boards on `{side}` and the next edge
  clockwise), `l188-chair-{side}`, `l188-luggagerack-{side}`, cubes `l188-roof`, `l188-carpet-{corridor,room}`,
  `l188-tile-{lobby,bath}`, `l188-concrete-stair`. Reception desks emit `[7, 2, 7]`.
- **Breakable stores' drops** (3.7): wardrobe (lower) cloth 1-2, a commoner shirt/trousers/boots 15% between them;
  minibar Almond Water 50%, juice 40%, crackers 30%; cart cloth 2-4, keycard 25%, candle; linen shelf cloth 3-6; beds
  cloth 2, linen 10%.
- **The arm:** root at the entity's origin (y 0-2 px), reaching 35 px (about 2.2 blocks) along -X. Animations `reach`
  (0.5 s, hold), `grab` (0.2 s, hold), `pull` (1 s loop), `recoil` (0.3 s, hold), `idle` (default). Sounds: hurt/death
  `effect/188/recoil`; the code plays `effect/188/grab`.
