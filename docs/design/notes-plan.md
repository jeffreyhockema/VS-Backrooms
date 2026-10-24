# Notes and the journal: design and implementation plan

Designed 2026-10-09, revised and implemented the same day.

## Revision (user feedback, 2026-10-09)

The user took D1 (pocket note), D2–D6, D8 and D9 as recommended, and **changed D7**: "many writers, but maybe several
that repeat. maybe there should also be classes of notes (not necessarily visible to the user), but there could be a
series of common notes that are presented in order, but also more rare notes with more valuable information, etc."

So, against the first draft below:

- **A cast instead of one notebook.** The main series is carried by five recurring writers, each with a voice, a reason
  to be where they are and a small arc, plus many one-off hands (section 7.1). The order is unchanged: whatever paper
  is found, main 1 comes first and the main series always comes in order; it is simply written by several people. The
  pages are no longer numbered in the text ("Page 7"); the journal numbers them.
- **Classes of notes** (hidden; section 7.2):
  - **common**: the ordered series (main + one track per level), as designed;
  - **rare** ("folded notes"): more valuable, exact information (exact routes to the Hub doors, the food courts' four
    ways in, Kitty's cute-item rule, the Keymaster and the M.E.G.'s key prices, how locks give, the gear trick, The
    End's door odds, Level !'s and Fun's survival rules, ore by ore in Level 8, a marked untouched cache, the barn wall
    exactly). 16 level-local rare tracks plus one "any level" track, **each in a fixed order**, so nothing repeats;
  - **scrap**: flavour, only when the common tracks run dry (as before).
  - (A fourth, internal **special** class holds the one note Level Fun's altered paper always says, once.)
- **The class comes from the paper, not a roll at read time.** A rare note is written on its own paper,
  `wanderernote-folded` ("Wanderer's Note", folded small, taped, in ink: quietly different), which only comes from
  rare sources: deeper caches, den hearts, Red Rooms, rooms behind locked doors, lost packs, bedrolls, tents, runners'
  remains and the far edge of a ring (section 6). Reading one gives the next due entry of the rare track of the level
  it is read in, else of "rare-any", else (all rare notes read) an ordinary note. The very first note a player reads is
  always main 1, whatever the paper.
- **Rare notes mark better:** their entry's own mark is searched twice as far, a folded note with no mark of its own
  marks an unopened cache from twice as far, and their waypoints are a warmer gold.
- **Journal:** rare notes have their own chapter, **Folded notes**, in the order found (recommended over mixing them
  into the level chapters: the valuable ones are easy to find again, and finding one feels like a find).

## Status (2026-10-09)

Implemented as revised. What exists, and what differs from the first draft:

- (2026-10-11) **Every note marks somewhere new:** a search skips every place the reader's earlier notes marked (all
  marks in their log, `NoteSystem.TakenOf`, within 12 blocks = the same place: another doorway of a gate, another box of
  a stash), so the second supplies note names the next stash out, the second door note the next gate; only when nothing
  else is in range is the nearest named again (`MarkResolver.Resolve(..., skip)`, and the `skip` parameter on every
  `WorldLayout.Nearest*`). Headless-checked with `note probe`: three cache notes at spawn gave three stashes.
- (2026-10-11) **Stacks:** notes of one kind always stacked (16); the four ordinary kinds now carry their kind in the
  name ("Wanderer's Note (supplies)" …, `NOTE_KIND_NAMES` in gen_loop.py) so two that will not stack can be told apart.

- `tools/gen_notes.py`: every text (186 entries: 145 common, 30 rare, 10 scraps, 1 special), the writers, the classes,
  gates and marks; writes lang (`note-*`, `notetitle-*`, `journal-*`), `assets/backrooms/config/notes.json`, the
  folded note item and texture, the loose note block, and **`docs/design/notes-catalogue.md`** (every text, generated: read
  that rather than section 7 of this file for the wording). `--check` validates keys, gates, marks, lengths and the
  facts the notes rely on against the handbook and README.
- `src/Notes/`: `NoteCatalog` + `NoteSequencer` (pure, shared with the harness), `NoteSystem` (server: read flow,
  persistence in save data `backrooms-notes`, pocket note, commands; client: the journal on J, the reading dialog,
  links), `MarkResolver`, `NoteDialogs`, `BlockLooseNote`, `NoteSystem.Spots` (extra and folded drops, loose notes).
  `src/Map/WandererNote.cs` now only registers the item and hands reading to `NoteSystem`.
- **Drops are added in code, not in `tools/salvage.py`** (`NoteSystem.Spots.cs`: hashed from the block's position, by
  level, den, locked room and ring band), so the furniture JSON and the integration agent's regeneration are untouched.
- **Loose notes are set down at run time**, not by the world generator: the first time a player comes within a cell
  of a spot (`WorldLayout.NoteSpots`), the note block is placed on the floor there and the cell is remembered
  (`backrooms-notespots`), so old worlds get them too. Spots: half the den hearts (folded), the Manila Room, Red Room blocks
  (folded), 1 in 8 chalk-crossed dead ends in Level 0, Sanctums, the Beverly Room, food courts, and beside each Level !
  lane's arrival (it marks the lane's true exit); added by the integration pass: by Level 974's kitchen table (refuge),
  at the Hub's two outposts and Level 3999's camps (way). Not placed: Level 1 camps (tents already give 0.5), Level 7/8
  camps (no camp-centre helper outside those levels' own files).
- Gaps fixed: Level Fun's altered note now reads (once, marking a party: `fun-lie`); Level !'s `note-run` text lives on
  as `run-2`; door notes in Level 11, 37, 94 and the new levels now resolve (End: an opening EXIT door; Level !: the
  lane's true exit; Hub: a keyless carved door; elsewhere the nearest threshold).
- Not done: sources for `hub-key-fun`, Memory Juice and LUCA Tears (not trivial without running other agents' asset
  generators; listed in 11.2). Filled by the integration pass: `l10-6` (Nell: the red-lit windmills), `l3999` (7),
  `l188` (7), `rare-l3999` (2), `rare-l188` (2): 205 entries in all (160 common, 34 rare, 10 scraps, 1 special).
- Tested: `mapgen <seed> 4 notes` (two scripted players in different orders and levels, then 10,000 random players:
  main 1 always first, every track in order, no repeats, folded papers give rare entries while any are due, gates
  respected). Headless server (seed 12345, console `/backrooms note probe <reader> x z [kind] [levels been]` and
  `note log`): two readers in different orders and levels got main 1 first (bob's first paper was folded), the main
  series in order, local and rare entries where due, a gate mark 450 paces off in Level 0, a Hub door 800 paces off from
  a folded note in Level 1, and both logs survived a restart. Not yet tried in a client: the dialogs, J, the links,
  the drops and the loose notes (they need a player). Measured supply (seed 12345, 70×70 cells round spawn, boxes and loose
  notes only): Level 0 0.037 → 0.10 ordinary notes per cell, Level 1 0.07 → 0.13 (plus crates, tents and furniture),
  so both sit in the 6.1 targets.

**The user's brief:** "during one test playthrough i found a note that marked a location on my map and showed me the
exit to the level. i loved that. I want to be sure there is a detailed and complete system of notes. i want it well
thought out to offer the player appropriate hints. i think at least most of the notes should go in order. it shouldn't
matter which note the player finds first, they always find the same message first, and they come in order (most of
them anyway). each of the notes should be added into a book/journal so they can be reviewed. the notes can include
details or hints about how to find levels, how to escape, recipes, how to find certain resources, etc."

Contents

1. What exists today (and which note the user found)
2. The model in one page
3. Sequences: tracks, interleaving, gates, running out
4. Map marks: what a note points at
5. The journal
6. Placement and rarity
7. The catalogue (every note text)
8. Code plan
9. Tests
10. Decisions for the user
11. Counts, and gaps found on the way

---

## 1. What exists today

### 1.1 The note item

`backrooms:wanderernote-{door,way,cache,refuge}` (`tools/gen_loop.py` `notes()`, class `BackroomsWandererNote`,
`src/Map/WandererNote.cs`). Right-click reads it **on the server, where the reader stands**:

| Kind | Search (from `WayfindingSystem.Read`) | Radius | Waypoint (icon) |
|---|---|---|---|
| door | `NearestGate(x, z, level, 1200, level + 1)`, else any gate (`WorldLayout.Gates.cs`) | 1200 | "Gate to Level N (a note)" (x) |
| way | `NearestThreshold`: pits, noclip walls, Level 6 descents, elevators, L1/L4/L5 stairs | 320 | "Way out (a note)" (spiral) |
| cache | `NearestCache`: an unlooted sealed box or crate, at least 12 blocks away | 256 | "Something left (a note)" (vessel) |
| refuge | `NearestRefuge`: Manila Room, Sanctum, Beverly Room, Snackrooms, or a wanderer's site (L1, L4, L8, L11) | 1600 | "Refuge (a note)" (star1) |

It prints one of three lines per kind in chat (`note-<kind>-1..3`, with a compass direction and a distance in paces),
adds a yellow vanilla waypoint through `MapMarks.Add`, plays the writing sound and is used up. If nothing is found it
prints `note-nothing` and is **kept** (to read elsewhere). Nothing is remembered: there is no journal and no order.

**The note the user loved is the `door` kind**: it is the only one that marks "the exit to the level" (a gate in the
boundary wall, preferring the gate onward to level + 1). That behaviour is kept unchanged as the mark of every
`door` note (section 4).

Related readers that work the same way: The End's catalogue card (`ItemCatalogueCard` in `src/Regions/EndSystem.cs`,
`note-endexit-1..3`, marks the nearest EXIT door that opens) and the Level 974 computer's "Internet" (marks the nearest
gate, cache or way out near the house's wake point). The End's found books are vanilla `book-normal-*` stacks with a
title and text (readable in vanilla's book dialog). Level Fun ships a `fun-wanderernote-altered` whose kind
`altered` has **no case in `WayfindingSystem.Read`**, so today it only prints "the directions don't fit". Level !'s
`note-run` line exists in lang.

### 1.2 Where notes come from today

Drops only (no note is placed by world generation):

| Source | Kinds and average count per break |
|---|---|
| Sealed supply box | door 0.04, way 0.04, cache 0.04, refuge 0.03 (0.15 in all) |
| Torn supply box | door 0.03, way 0.03 |
| Desk (L4) | way 0.04 |
| Filing cabinet (L4) | door 0.05 |
| Writing desk (L5, L9) | refuge 0.05 |
| Tent (camps) | cache 0.3, door 0.2 |
| Bedroll | door 0.12 |
| Lost backpack (L6 dead ends, L7 seabed) | door 0.3, way 0.2 |
| Level Fun gifts | fun-wanderernote-altered 0.12, way 0.05 |

Rough supply in Level 0, from the measured stash densities (0.15 sealed boxes per cell, roughly twice that torn):
about **0.04 notes per cell**, one note per 25 cells (32×32 blocks) explored. A first week in the Lobby explores
perhaps 100–200 cells: 4–8 notes. That is right for one-shot map marks and too few for a sequence (section 6).

### 1.3 What vanilla offers (decompiled from 1.22.7)

- **The lore journal.** `ModJournal` (VSSurvivalMod) keeps a `Journal` per player UID in the save game
  (`journalItemsByPlayerUid`), sends it to the player on join, and opens `GuiDialogJournal` on **J**
  (hotkey `journal`, `GlKeys.J`). Entries (`JournalEntry`: `LoreCode`, `Title`, `Chapters`) are listed by title; each
  chapter's `Text` goes through `Lang.Get`, so it can be a lang key. `AddOrUpdateJournalEntry(player, entry)` is
  public. Vanilla lore (`config/lore/*.json`, `ItemRandomLore`) already reveals **the next undiscovered chapter in
  order**: the same idea as this brief, for vanilla's ruins. Its dialog is plain: a list of titles and a paged text,
  with no room for map marks, links or ordering control. Backrooms worlds have no vanilla lore, so J shows "No lore
  found".
- **Books.** `ItemBook` with `title`/`text`/`signedby` attributes and `GuiDialogReadonlyBook` (The End's found books
  use this). A book is an inventory item, so it is lost on death with everything else.
- **Discovery toast.** `sapi.SendIngameDiscovery(player, code, message, args)` shows a centred "discovered" banner;
  with `message` set the client shows that text as is.
- **Per-player persistence.** Three options all survive death and relog: save-game data keyed by UID (what
  `ModJournal`, `ThresholdNetwork`, the Hub and Level 974 use), `IServerPlayerData.CustomPlayerData`
  (`Dictionary<string,string>`, saved with the world's player data), and `Entity.WatchedAttributes` (synced to every
  client that sees the player, so only for small values: the Hub already keeps `backrooms:visitedLevels` there, a bit
  per level id).
- **Handbook links.** Rich text in any dialog can link `handbook://item-<code>` (the handbook registers the protocol),
  so a note can link "glass shiv" to its handbook page, as `tools/gen_guide.py`'s markup already does.
- **Map.** `GuiElementMap.CenterMapTo(BlockPos)` exists, so a journal entry can open the world map on its mark.

---

## 2. The model in one page

- **A physical note is blank until it is read.** The item keeps its four kinds (door, way, cache, refuge), and the
  kind now decides only **what it marks on the map** (exactly today's behaviour). What it **says** is decided when it
  is read: the next entry in that player's sequence.
- **Every player has their own sequence.** Two players reading the same kind of note in the same room read different
  pages if they are at different points. Progress lives on the server, per player UID, in the save game.
- **The sequence is made of tracks.**
  - **The Wanderer's Way** (`main`, 25 entries): written by a recurring cast (revision above), read anywhere.
    It walks a player from waking up to the far levels: blade, bags, fire, the gear, home, the wall, the dark, then
    Level 1, the doors, copper, clay, the ground, and so on. **The first note any player reads is always main 1**, and
    the series always comes in order.
  - **Level tracks** (one per level, 3–9 entries each): local knowledge (that level's dangers, resources, refuges and
    ways on), from many hands. A note read in Level N advances Level N's track, in order.
  - **Scraps** (a short flavour track) and **directions** (a plain map mark) take over when the tracks run out.
- **Interleaving:** the first three notes are Pages 1–3; after that a note alternates between the next page and the
  next entry of the level it is read in. A page can wait for the player to have **been somewhere** (e.g. Page 10,
  about the threshold network, waits until they have been in Level 1), so the right hint comes at the right time;
  while the next page waits, the level track serves, and vice versa.
- **Map marks stay.** Every note still marks the place its kind points at, from where it is read, as today; a few
  entries also mark something of their own (the Manila Room, a manhole for clay, the barn wall to the city). Page 7
  ("the wall") always marks the nearest gate, like the note the user found.
- **The journal** is per player, kept on the server, and opens with **J** (in Backrooms worlds the Backrooms journal
  replaces vanilla's empty one) or `.journal`. Chapters: The Wanderer's Way first, then the levels in level order,
  Scraps, Directions. Each note shows its text, where and when it was read, and its marks with **Show on map** and
  **Mark again**. It survives death, relog and server restarts, and works in multiplayer because nothing is stored on
  an item.
- **Reading** shows the note in a small paper dialog (and a one-line chat log and a "added to your journal" toast).
- **Text lives in lang**, generated from one table in a new `tools/gen_notes.py`, which also writes the track
  definitions (`assets/backrooms/config/notes.json`) the code reads. Edit a note there and existing journals show
  the new wording (chapters store keys, not text).
- **Placement:** notes stay scarce information loot, but supply roughly doubles in Level 0 (it did in Level 1 too until the 0.513.3 tuning: boxes and camp props there now give half, about one ordinary note per 10 cells with every container broken, the plan's "one per 10-15 deeper"; `mapgen notesupply` measures it), and a few
  are placed where a story says one would be (den hearts, the Manila Room, camps, the 9th Road camps, island camps).
  New players get one note in their pocket: Page 1, marking the nearest sealed box.

---

## 3. Sequences

### 3.1 Track ids

| Track id | Read in | Title in the journal |
|---|---|---|
| `main` | anywhere | The Wanderer's Way |
| `l0` … `l11` | Levels 0–11 (6.1 and 37.1 excluded, below) | Level 0: the Lobby … Level 11: the Endless City |
| `l61` | Level 6.1 (a Snackrooms cell inside Level 6: `IsSnackrooms`) | Level 6.1: the Snackrooms |
| `l37` | Level 37 and 37.1 (one track; its last entries are the Reservoir's) | Level 37: Sublimity |
| `l94` | Level 94 | Level 94: Motion |
| `run`, `fun`, `end`, `hub`, `l974` | Levels 14–18 | Level !, Level Fun =), The End, The Hub, Level 974 |
| `l3999`, `l188` | Levels 19, 20 (when built) | Level 3999, Level 188 |
| `scraps` | anywhere, only as a fallback | Scraps |
| `dir` | anywhere, only as a fallback | Directions (a log of plain marks) |

The level a note is read in is `layout.LevelAt(macro)` with two refinements (6.1 by `IsSnackrooms`, 37.1 folds into
37), the same rule `MapMarks.LevelName` already uses.

### 3.2 Entries

Each entry (in `tools/gen_notes.py`, written out to `notes.json`):

```python
E("m07", title="Page 7: The wall", mark="door", gate=None, text="...")
E("m10", title="Page 10: The doors are the map", gate=visited(1), text="...")
E("l3-2", title="Clay", mark="manhole", text="...")
```

- `key`: stable id; lang keys are `note-<key>` (text) and `notetitle-<key>` (short title for the journal index).
- `gate` (optional): a condition the reader must meet for the entry to be *due*. Only one kind is needed:
  **visited any of {levels}** (from the per-player visited bits the Hub already keeps). Level-track entries rarely
  need one; main pages use them to pace the notebook (section 7.1 lists every gate).
- `mark` (optional): an extra mark this entry makes besides the paper's own (section 4).
- Keys never change once shipped (journals store them). New entries are added at the end of a track, or inserted with
  a new key: a player's position is stored as the set of keys read, not an index, so an inserted entry is simply
  "not read yet" and comes next time (section 8.4).

### 3.3 Resolving a note

On the server, when player P reads a note of kind K in level L:

```
due(track)  = first entry of track not yet read by P, if its gate is met; else none
M = due(main); T = due(track of L)

if P has read fewer than 3 main pages and M:         pick M         # the same three messages first, always
elif M and T:  pick the one P did NOT pick last time                # alternate page / local
elif M or T:   pick whichever exists
elif due(scraps):          pick it                                  # flavour, ordered, 10 entries
else:                      directions only                          # today's plain note (§4)
```

Then: record the entry in P's journal (with level, position, calendar time), resolve the marks (section 4), show the
note, consume the item.

Properties this gives, all asked for:

- **The first message is always the same** (Page 1) whatever note is found where, and pages 2 and 3 follow.
- **Most notes come in order:** the main track always in order; each level's track in order; the only thing that
  varies is how the two are interleaved, which follows where the player reads them.
- **Hints arrive at the right time:** local hints where they are useful (a Level 3 note talks about Level 3), the
  notebook paced by gates so that, for instance, Page 18 (Level 6's darkness) waits until the player has reached the
  hotel or Level 6. A player who rushes deep before reading gets the early pages late; nothing is skipped.
- **Pacing in Level 0.** With 9 Level 0 entries and pages 1–9 ungated, a careful first week (10–16 notes) reads
  pages 1–9 interleaved with most of the Level 0 track, then the notebook waits for Level 1 (page 10). The pocket
  note plus the doubled supply (section 6) make that first week's count likely.

### 3.4 Running out

- **Level track done, page waiting (or the reverse):** the other serves. Both waiting or done: **Scraps**, ten
  ordered flavour notes from the lost (no hints; they make the world felt). Then **directions**: the note is
  today's plain note, one of the existing `note-<kind>-1..3` lines with direction and paces, logged under
  *Directions* in the journal (only the last 40 kept). Directions notes are never wasted: their mark is the point.
- **Everything read:** every further note is a directions note. A player who has read the whole catalogue (about
  160 entries) has played a very long game.
- **A new level visited later** reopens its track; a newly built level (3999, 188) brings its own track to old saves.

### 3.5 Multiplayer

- Sequences and journals are per player UID; reading happens on the server, which is authoritative.
- Physical notes are shared world loot: whoever reads one advances their own sequence. Handing a note to a friend
  works (it is blank until read).
- The pocket note is per player (first join), so a second player in a looted area still starts at Page 1.
- Visited bits are per player (`backrooms:visitedLevels`, already maintained by `HubSystem.OnTowerTick`; moved to a
  shared helper, section 8).

---

## 4. Map marks

### 4.1 The paper's kind always marks, as today

Every note marks according to its kind, from where it is read, with today's searches, radii, waypoint titles,
colour (`MapMarks.NoteColor`) and the 4-block dedupe. The entry's text and the mark are independent, so a `door` note
always shows "the exit to the level", whatever page it turns out to be. The direction-and-paces line (today's
`note-<kind>-1..3`) is kept and appended under the entry text as the writer's pencilled postscript:

> *(on the back, in pencil)* "If you're reading this you're lost like we were. The gap in the wall is north-east,
> maybe 350 paces. Go quiet."

When the search finds nothing in range: **door falls back to way and way to door** (both are "a way out"); cache and
refuge fall back to nothing. With no mark the postscript is `note-nothing` ("The directions on the back don't fit
anything round here."). **The note is still used up**, because its text is now the main value. (Today it is kept;
see decision D4.)

### 4.2 Entry marks (extra)

A few entries name a place of their own, marked in addition to the paper's (at most two marks per note). Existing
searches cover most; four small new ones are needed:

| Entry mark | Search | Radius | Waypoint title (icon) |
|---|---|---|---|
| `door`, `way`, `cache`, `refuge` | as 4.1 | as 4.1 | as 4.1 |
| `manila` | `NearestRefuge` restricted to Level 0 | 1600 | "The Manila Room (a note)" (star1) |
| `den` | nearest den heart (`WorldLayout.Dens.cs` already decides dens per cell) | 400 | "Keep out (a note)" (x, red-brown) |
| `manhole` | nearest Level 3 manhole tile | 320 | "Manhole: clay below (a note)" (spiral) |
| `barnwall` | nearest `Unders.Noclip` barn wall in Level 10 | 2000 | "The barn wall (a note)" (spiral) |
| `endexit` | `EndExitsNear(..., opens)` (the catalogue card's search) | 600 | "A way out of The End (a note)" (star1) |
| `hubdoor` | nearest Hub entrance in Levels 1/2 (`WorldLayout.LevelHub.cs` already finds these) | 600 | "A grey door (a note)" (spiral) |

`door` in a noclip region resolves through a per-level resolver instead. This matters: `NearestGate` only knows ring
boundaries and `IsNoclipRegion` excludes every level from 11 up, so **today a door note read in Level 11, 37, 94 or any
of the new levels finds nothing**. Resolvers: The End → `endexit`; Level ! → the lane's true exit; the Hub → the
nearest carved door that opens without a key; Level 37 → nearest POOL door or corridor end; Level 94 → nearest hilltop
gate; Level 11 → nearest exit threshold;
anything else falls back to `way` (`NearestThreshold`). The resolver table lives in one place (`MarkResolver`,
section 8) so 3999 and 188 add a line each.

### 4.3 Which notes mark

All of them, by kind. The catalogue (section 7) lists the extra entry marks; there are about 45 of them, chosen where
the text names a place. Page 7 ("the wall") carries `mark="door"` so that whatever paper it was written on, it shows
the gate out of the level, like the note the user found.

---

## 5. The journal

### 5.1 Recommendation: our own journal dialog on J, data on the server

Vanilla's journal is close but cannot order chapters, show map marks or link to the handbook, and its entries must
come from asset lore files. A Backrooms dialog (one class, the size of `GuiDialogCheats`) gives all three, and the
data stays server-side so it survives death and relog without an item.

**Opening it:** **J**. In Backrooms worlds the client re-binds the `journal` hotkey handler to the Backrooms journal
(`capi.Input.SetHotKeyHandler("journal", ...)` after `ModJournal` has registered it; vanilla lore cannot occur in
these worlds). Also `.journal`, and a button on the reading dialog. Other worlds keep vanilla's journal.

**Layout** (left list, right page, like the handbook):

```
+-- The Wanderer's Journal -------------------------------------------- [x] --+
| The Wanderer's Way  9/25 |  Level 3: the Electrical Station        2 / 7    |
| Level 0: the Lobby  5/9  |                                                  |
| Level 1             3/9  |  2. Clay                     read in Level 3,    |
| Level 3             2/7  |                              day 14, 06:00       |
|   ...                    |  "Clay is under the manholes. Down the rungs     |
| Scraps              0/10 |  into the flooded tunnels: freezing water, and   |
| Directions          12   |  the worst pull on the gear anywhere. Dig, and   |
|                          |  get out. I marked the nearest one."             |
|                          |                                                  |
|                          |  Marked: Manhole, clay below. 140 paces north    |
|                          |  of where you read it.  [Show on map] [Mark again]|
|                          |  ----------------------------------------------  |
|                          |  1. Hot brick                ...                 |
+--------------------------+--------------------------------------------------+
```

- Chapters: The Wanderer's Way, then levels in level order (0, 1, 2 … 11, 6.1 after 6, 37, 94, then the new levels by
  id), then Scraps and Directions. A chapter appears once its first note is read; its heading shows *read / total*
  (decision D3).
- Inside a chapter, notes are in track order (which is also the order read). Newest-first is a toggle.
- Each note: number and title, where and when read, the text (rich text: handbook links work), the postscript, and
  each mark with **Show on map** (opens the world map centred on it) and **Mark again** (re-adds the waypoint if the
  player deleted it; the server re-checks distance dedupe).
- Directions: a flat list of plain marks, newest first, last 40.
- The reading dialog: the note on a paper-coloured panel, its marks under it, buttons *Close* and *Journal (J)*.
  Closing it costs nothing; the note is already in the journal.

**Book item:** none needed. A "wanderer's journal" item would be lost on death with the inventory, and the data
lives on the server anyway. (Decision D2 offers an optional cosmetic item.)

### 5.2 Persistence and sync

- Server: `NoteSystem` keeps `Dictionary<string uid, NoteLog>` in save-game data `backrooms-notes` (JSON via
  Newtonsoft, which the game ships), written on `GameWorldSave` when dirty, like `ThresholdNetwork`.
- `NoteLog`: `List<NoteRead> Read` (key, track, level, x, z, calendar hours, kind, marks), `string LastPick`
  ("main"/"level"), `bool PocketGiven`, `List<NoteRead> Directions` (capped 40).
- `NoteRead.Marks`: `{ x, z, level, titleKey, titleArg, icon, dirKey, paces }`: enough to redraw the line and re-add
  the waypoint; no resolved text is stored, so wording edits show up in old journals.
- Client: channel `backrooms-notes`; the server sends the player's whole `NoteLog` on join and after each read (a few
  KB at most). Requests from the client: `MarkAgain(index)` only; reading is an item interaction already on the server.
- Death: nothing is on the entity or the inventory, so nothing is lost. Relog: sent on join. Server restart: save data.

---

## 6. Placement and rarity

Notes stay information loot: rarer than food, never in piles. The goal is the pacing in 3.3: about one note per
6–10 cells explored in Levels 0 and 1, one per 10–15 deeper, a handful in each noclip region, and the first hour
giving 3–5 (Pages 1–3 plus a Level 0 entry or two).

### 6.1 Drop changes (in `tools/gen_loop.py` and `tools/salvage.py`)

| Source | Today | Proposed |
|---|---|---|
| Sealed supply box | 0.15 (4 kinds) | **0.25** (door 0.07, way 0.06, cache 0.07, refuge 0.05) |
| Torn supply box | 0.06 | **0.12** (door 0.05, way 0.04, cache 0.03) |
| Desk, filing cabinet, writing desk | 0.04–0.05 | 0.06 each |
| Tent | 0.5 | unchanged |
| Bedroll | 0.12 | 0.15 |
| Lost backpack | 0.5 | unchanged |
| Level 4 reception desk, Level 5 front desk (guest book) | 0 | refuge 0.15 |
| Level 9 kitchen cupboard, dresser | 0 | door 0.03 (a house is a dungeon; notes are part of its loot) |
| Level 11 apartment mailbox | 0 | way 0.05 |
| Level 94 writing desks (they are L9 furniture) | via L9 | unchanged |

Measured target, not assumed: the harness `notes` mode (section 9) sums the drop averages of every block it generates
in sample windows per level and reports notes per cell; tune these numbers until Level 0 sits at 0.10–0.16 per cell,
Level 1 at 0.12–0.2, Levels 2–10 at 0.07–0.1.

### 6.2 Placed notes (new: a loose note block)

A new block, `backrooms:loosenote-<kind>` (a folded sheet lying flat; 1/16 high; break or right-click picks it up as
`wanderernote-<kind>`; drops nothing else). World generation places it where a story puts one, which also puts notes
where they cost something to reach:

| Where | Count | Kind | Why |
|---|---|---|---|
| Beside a den's heart caches (all levels with dens) | 1 per den | door | "the last thing they wrote"; dens are dangerous, so this pays for the risk |
| The Manila Room's table | 1 | way | the first refuge teaches the network |
| A Red Room block | 1 per block | cache | high drain, high reward |
| Level 1 camps (tent clusters, barrel encampments) | 1 per camp | refuge | the survival-loop plan's "1 per camp" |
| Level 3 Sanctum (on the pedestal steps) | 1 | way | |
| Level 5 Beverly Room (the Mahjong table) | 1 | door | |
| Level 6 dead ends with a backpack | already in the pack | | |
| Level 7 island camps | 1 per camp | way | |
| Level 8 9th Road camps; remains off the road | 1 per camp; 1 per remains | way; cache | |
| Level 6.1 food court (a café table) | 1 per court | way | |
| Level 10 farmhouse kitchen table | 1 in 4 farmsteads | door | |
| Level 37 rims, by an Epsom salt crust | 1 in 8 crusts | way | |
| Level ! start room (bedside table) | 1 per lane | door (marks the lane's true exit) | read before the chained door bursts, or not |
| Level ! runner's remains | drop 0.25 | way | |
| Level Fun gifts | today's 0.05 way + 0.12 altered | | unchanged |
| The End service desks | drop 0.06 | door (→ `endexit`) | catalogue cards stay separate |
| The Hub, the M.E.G. outpost table | 1 | way | the Hub has almost no loot otherwise |
| Level 974 kitchen table | 1, first visit only | refuge | |
| Level 11 apartment mailboxes | drop 0.05 | way | (6.1) |
| Level 94 houses' writing desks | via L9 furniture | | |

In Level 0, beside the existing chalk-cross dead ends of hallways, 1 in 8 gets a loose note (the cross says why the
writer turned back). This is the main Level 0 source besides boxes, and puts notes along the way rather than in
rooms. With the den, Red Room and Manila notes, Level 0 should land near the 0.12-per-cell target; the harness checks.

### 6.3 The pocket note

On a player's first join in a Backrooms world (`NoteLog.PocketGiven` false), one `wanderernote-cache` goes into their
inventory (decision D1). Read, it is Page 1 and marks the nearest sealed box: a first lesson in what notes do.

### 6.5 As built (rare and extra drops, `src/Notes/NoteSystem.Spots.cs`)

Added in code on top of each block type's own drops, rolled from a hash of the block's position:

| Broken | Extra ordinary note | Folded note (base) |
|---|---|---|
| Sealed supply box | +0.10 in Levels 0–1 | 0.012; +0.25 in a den's cache; +0.15 in a Red Room |
| Torn supply box | +0.06 in Levels 0–1 | 0 |
| Sealed crate / emptied crate | +0.03 / +0.02 in Levels 0–1 | 0.008 / 0 |
| Lost backpack, bedroll, tent | bedroll +0.03 | 0.08, 0.04, 0.04 |
| Desk, filing cabinet, writing desk | +0.02, +0.01, +0.01 | 0.01 each |
| Level !'s runner's remains | +0.25 (way) | 0.15 |
| The End's service desk | +0.06 (door) | 0.03 |

The folded chance is then multiplied by 1 + 2 × the level's danger (`Danger.OfLevel`: 0 in the Lobby, ~0.95 in the
deepest), by 3 behind a locked door (`Tile.Sealed`), by 1.5 in the outer 15% of a ring, and capped at 0.6. Loose notes
(6.2, as built in the status) add the den and Red Room folded notes. The harness `notes` mode prints notes per cell from
boxes and loose notes for its window.

### 6.4 What does not change

Food and tools are untouched. Notes never restock. No note is placed in the spawn cell's boxes beyond what they drop
already. Chalk arrows near gates stay the other way of finding a gate. Scarcity setting (`backroomsScarcity`) does not
scale notes (they are information, not food; decision D6).

---

## 7. The catalogue

**The wording lives in `tools/gen_notes.py` and is listed in full in `docs/design/notes-catalogue.md`** (generated, with
each entry's writer, gate and mark). The first draft's single-writer texts that stood here were re-voiced for the cast
below; every fact and recipe was kept and is checked by `gen_notes.py --check`.

Voice: first person, past wanderers, terse, plain words, no game-UI words except where a control must be named
(right-click, sneak, F). Exact where it counts.

### 7.1 The writers

| Writer | Who, and why they are where they are | Voice | Arc across their notes |
|---|---|---|---|
| **Dez** (signs "— Dez") | A scavenger who came through with a friend, Pell | Slangy, short sentences, lists of loot | Cocky rules in the Lobby (main 1–3), crates and stashes, loses Pell in Level 2 (l2-6), ends with a stall in the city (m22) |
| **A. Lindqvist** ("— A.L., survey") | A surveyor who treats the place as a system to map | Measured, numbered, "Finding:", "Fair copy" | Fire, the wall, the doors are honest (m10), copper, clay, the ground; her fair copies are many of the folded notes; last fair copy: every door honest, none leads out (ra12) |
| **M.E.G. Field Team 9** ("M.E.G. FIELD NOTICE", "— Field Team 9 (six of us)") | An expedition team leaving official notices and restricted briefings | Typed, imperative, exact | The count falls note by note, six to one (ra07: "one of us") |
| **Tom** (every note begins "Ruth,") | A man writing to his wife, not coping | Plain, hurt, tender | The gear, dying and waking (m06), the Manila Room, the gear trick, and at the end calls the Lobby home (m25) |
| **Nell** ("— Nell", "love") | A grower | Warm, practical | First turnip in the Lobby (m17), the fields (m21: "I'm staying"), the barn wall for her lad |
| One-off hands | Whoever was there | Varied | Most level entries, warnings, scraps |

The main series in order: Dez (1–3), Lindqvist (4), Tom (5–6), Lindqvist (7, the wall: marks the gate), Team 9 (8),
Dez (9), Lindqvist (10–12), Team 9 (13), Lindqvist (14), Dez (15–16), Nell (17), Team 9 (18), Lindqvist (19), Team 9
(20), Nell (21), Dez (22), Lindqvist (23), Team 9 (24), Tom (25).

### 7.2 Classes

| Class | Tracks | Entries | Paper | Chosen when |
|---|---|---|---|---|
| common | `main` and one per level (l0 … l11, l61, l37, l94, run, fun, end, hub, l974; l3999 and l188 empty slots) | 145 | `wanderernote-{door,way,cache,refuge}` | every ordinary note (3.3) |
| rare | `rare-<level>` (16: 0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 37, 94, End, Hub, !, Fun) and `rare-any` (12) | 30 | `wanderernote-folded` | a folded note: its level's rare track, else rare-any, else an ordinary note |
| scrap | `scraps` | 10 | any | an ordinary note when main and the level's track are both done or waiting |
| special | `fun-altered` | 1 | `fun-wanderernote-altered` | that paper, once (then it reads as an ordinary note) |

What the rare notes carry (all in `docs/design/notes-catalogue.md`): the Hub's three entrances exactly (ra01, marks one), the
food courts' four ways in (ra02), Kitty's rule (ra03), key prices and the Keymaster (ra04), how locks give (ra05), the
temporal gear trick (ra06), the door that wasn't there (ra07), every way to the Poolrooms (ra08), the barn wall exactly
(ra09, marks it), an untouched stash (ra10, marks it from twice as far), every way into Motion (ra11), and Lindqvist's
last fair copy (ra12); per level: Red Room keys (marks the Red Rooms), the Manila Room as home, Level 1's End and Hub
doors, keys under Level 3, the hungry machines, the hotel's doors, Level 6's ways down, Level 7's wrecks, Level 8's ores
mineral by mineral, the doll's house and the teal pool, the city's secrets, the Poolrooms' corridor odds, the King's
rules, The End's door odds and fake rooms, the Hub's key resonance, Level !'s seventeen halls (marks the true exit),
and how to get out of Level Fun.

## 8. Code plan

### 8.1 New files

| File | What |
|---|---|
| `tools/gen_notes.py` | The catalogue (section 7) as one Python table: tracks, entries (key, title, text, gate, mark), track titles. Writes lang (`note-*`, `notetitle-*`, `journal-*`, the reading dialog strings) through `detail_kit.LANG`, and `assets/backrooms/config/notes.json` (tracks with entry keys, gates, marks; no text). Same light markup as `gen_guide.py` (links to handbook pages), converted with its `to_vtml`. Run alone or from `gen_loop.py`. Includes the fact check (section 9). |
| `src/Notes/NoteCatalog.cs` | Loads `config/notes.json` (both sides). Track list, entry lookup, track for a level. No game logic. |
| `src/Notes/NoteSequencer.cs` | Pure logic, no game dependencies (like `ThresholdNetwork.cs`), so the harness runs it: `Resolve(NoteLog log, string levelTrack, Func<int,bool> visited) → (track, key)` implementing 3.3–3.4. |
| `src/Notes/NoteLog.cs` | `NoteLog`, `NoteRead`, `NoteMark` (JSON-serialisable). |
| `src/Notes/NoteSystem.cs` | Server: load/save `backrooms-notes`; `Read(player, kind, slot)`: level → sequencer → marks (MarkResolver) → log → send log + show packet → toast → consume. Pocket note on first join. Network channel `backrooms-notes` (`NoteLogPacket`, `ShowNotePacket`, `MarkAgainPacket`). Commands under `/backrooms note` (section 9). Client: holds own log, opens dialogs, re-binds J. |
| `src/Notes/MarkResolver.cs` | Today's `WayfindingSystem.Read` switch, generalised: `Resolve(markKind, x, z, level) → NoteMark?`, the fallbacks of 4.1 and the per-level `door` resolvers of 4.2. Direction/paces helpers (shared with `ItemCatalogueCard`, which has a copy). |
| `src/Notes/GuiDialogNote.cs` | The reading dialog. |
| `src/Notes/GuiDialogJournal.cs` | The journal (5.1). Named `GuiDialogBackroomsJournal` to avoid clashing with vanilla's class. |
| `src/Notes/BlockLooseNote.cs` | The placed note block (right-click or break → `wanderernote-<kind>`). |

### 8.2 Changed files

| File | Change |
|---|---|
| `src/Map/WandererNote.cs` | `ItemWandererNote.OnHeldInteractStart` calls `NoteSystem.Read`; `WayfindingSystem` shrinks to item registration (or is folded into `NoteSystem`). Kind `altered` (Level Fun) handled (section 7.18). |
| `src/Worldgen/WorldLayout.Notes.cs` | New searches: `NearestManhole`, `NearestDenHeart`, `NearestBarnWall`, `NearestHubEntrance`; placement rules for loose notes (`LooseNoteAt(tile)` deciding the 6.2 spots, hashed per feature, with their own salts so other layout stays byte-identical). |
| `src/Worldgen/WorldGenerator.cs` (+ level partials) | Place `loosenote-<kind>` where the layout says. |
| `src/Worldgen/Tiles.cs` | A tile flag or decor id for a loose note (reuse the Variant ≥ 40 prop scheme on floor tiles if a value is free; check `Kind` first). |
| `src/Regions/HubTower.cs` | Visited bits move to a shared `PlayerVisits` helper (same attribute key `backrooms:visitedLevels`, so existing saves keep their bits); the Hub keeps calling it. |
| `src/Regions/EndSystem.cs`, `src/Regions/L974System.cs` | Catalogue cards and the computer's Internet log their marks under Directions (`NoteSystem.LogDirection`). Behaviour otherwise unchanged. |
| `src/Cheats/CheatSystem.cs`, `GuiDialogCheats.cs` | `/backrooms note ...` subcommands and buttons (memory rule: every debug command gets a button). |
| `tools/gen_loop.py` | Item descriptions mention the journal; the loose note blocks; supply box drop changes (6.1). |
| `tools/salvage.py` | Drop changes (6.1). |
| `tools/gen_fun.py` | `fun-wanderernote-altered` keeps its code; its text moves to `gen_notes.py` (7.18). |
| `tools/gen_guide.py` | "Finding the Way": notes now also carry what earlier wanderers knew, in order, and go into the journal (J). Owned by the integration agent's handbook pass; send them the paragraph. |
| `README.md` | The "New" table row for the note; a short "Notes and the journal" paragraph under Surviving. |

### 8.3 The read flow

```
right-click note (server) -> NoteSystem.Read(player, kind, slot)
  level   = LevelOf(pos)                                   # 6.1 / 37.1 rules
  (track, key) = NoteSequencer.Resolve(log, TrackFor(level), PlayerVisits.Has)
  marks   = [MarkResolver.Resolve(kind, pos)] + [entry.mark] # dedupe, max 2
  for m in marks: MapMarks.Add(...)                         # unchanged helper
  log.Read.Add(NoteRead{key, track, level, pos, hours, kind, marks})
  send NoteLogPacket(log) ; send ShowNotePacket(index)      # client opens GuiDialogNote
  SendIngameDiscovery(player, message: "Added to your journal: <track title>, <n> / <total>")
  chat: "<title>: <first line…>" (a log line; the dialog has the whole text)
  play writing sound ; slot.TakeOut(1)
```

### 8.4 Migration

- **Items:** codes and kinds unchanged; notes already in chests and inventories become sequenced notes when read.
- **Existing worlds:** no `backrooms-notes` data → every player starts at Page 1, with their Hub visited bits already in
  place (so gated pages are due if they've been deep). No pocket note for players who already have a log or whose
  playtime suggests an old save? Simpler: pocket note only if the player has no log **and** has never been outside
  Level 0 (visited bits = just 0).
- **Waypoints** already placed by old notes stay (vanilla waypoints).
- **Catalogue edits:** keys are stable; positions are sets of keys, so inserting an entry mid-track later just makes it
  the next due entry for players past that point (it will arrive "out of order" once; acceptable). Removing an entry:
  keep its lang key so old journals still render it.
- **Fun's altered note** starts working (it does nothing today).

### 8.5 Levels 3999 and 188

Their agents (or a follow-up) add, in `tools/gen_notes.py`, a track `l3999` / `l188` with 4–6 entries in the format of
7.2, plus at most one main or Level 10/11 entry pointing the way in (7.13's `l10-6` is reserved for 3999). In code: one
line each in `MarkResolver`'s per-level `door` table (their exits), `NoteCatalog`'s level→track map (from
`notes.json`, so no code), and note drops in their salvage tables at the 6.1 rates (a note per 10–15 cells explored).
Drafts are in 7.21.

---

## 9. Tests

- **`python tools/gen_notes.py --check`** (also run on every generate):
  - every entry has text and a title, text ≤ 520 characters (fits the reading dialog without scrolling), keys unique;
  - gates name valid level ids; marks are known kinds;
  - **fact check:** a `FACTS` list of exact phrases the notes rely on (e.g. "5 carpet fibres + 1 flax twine", "2
    wallpaper strips", "each bottle restores 15%", "salt + powdered sulfur = 2 Firesalt", "2 metal brackets + 1 iron
    nails and strips", "one steel tunnel door in 40") must each appear in `gen_guide.PAGES` or `README.md`, so a recipe
    change in the guide breaks the build of the notes until they are re-checked.
- **Harness `notes` mode** (`tools/mapgen`, reusing `NoteSequencer.cs` and `NoteCatalog` via linked source):
  - simulate 10,000 players reading notes at random levels and orders: Page 1 is always first, pages always ascend,
    no entry repeats, every entry is reachable, gates respected; report the median notes read before each track runs
    out;
  - note supply: sum the note drop averages (from the generated block JSON) of every block generated in N sample windows
    per level, plus placed loose notes; print notes per cell per level against the 6.1 targets.
- **Headless server:** `/backrooms note give <kind> [n]`, `/backrooms note read <kind>` (reads one where the caller
  stands, without an item), `/backrooms note status [player]` (position per track, next due entry, waiting reasons),
  `/backrooms note reset [player]`, `/backrooms note set <track> <n>`. A script teleports a test player to the
  `probe2` coordinates of each level, reads one of each kind, and checks the log (keys, marks found, waypoints added),
  then restarts the server and checks the log survived; a second login checks per-player separation.
- **Client checklist** (first play-test): the reading dialog, J opening the Backrooms journal, Show on map, Mark again,
  journal after death and after relog, handbook links inside notes.

---

## 10. Decisions for the user

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | A note in every new player's pocket | (a) yes, Page 1 marking the nearest sealed box; (b) no, Page 1 is just the first note found | **(a)**: guarantees the same first message in multiplayer and teaches what notes do in the first minute |
| D2 | What the journal is | (a) our own journal dialog on J, data on the server; (b) vanilla's lore journal (J), fed by us; (c) a book item | **(a)**: ordered chapters, map marks with Show on map, handbook links, nothing lost on death. (b) is cheaper but has no marks or ordering; (c) is lost on death. Optional extra: a cosmetic "Wanderer's Journal" book that opens the same dialog |
| D3 | Show how many notes a chapter has ("Level 3: 2 / 7") | (a) yes; (b) only how many read | **(a)**: tells a player there is more to find in a level, a reason to search; it spoils nothing |
| D4 | A note whose map mark finds nothing in range | (a) used up anyway (its text is the value; the postscript says the directions don't fit); (b) kept, to read elsewhere (today's behaviour) | **(a)**: with sequenced text, keeping it would let a player re-read for free; door↔way fallbacks make "nothing" rare |
| D5 | How main pages and level entries interleave | (a) first 3 pages, then alternate page / local, with pages gated by levels visited; (b) strict single list; (c) level entries first, pages only when a level is exhausted | **(a)**: the same opening for everyone, local help where you stand, and the notebook arrives when it is useful |
| D6 | Note supply | (a) about double in Levels 0–1 plus placed notes at dens, camps, refuges and dead ends; (b) leave drop rates, add placed notes only; (c) leave as is | **(a)**: the main track and Level 0 track need 10–16 notes in a first week; today gives 4–8. Not scaled by the scarcity setting |
| D7 | The main track's writer | (a) one named writer, numbered pages; (b) anonymous | **Changed by the user:** a recurring cast plus one-off hands, and classes of notes (common series, rare folded notes, scraps): see the revision at the top |
| D8 | Shared reading in multiplayer | (a) each reader only; (b) players within 8 blocks also get the entry | **(a)**: simple and fair; notes can be handed over |
| D9 | Old one-line direction notes after everything is read | (a) keep as "directions" (mark only, logged); (b) stop dropping notes for that player | **(a)**: the mark is what the user loved, and still useful |

---

## 11. Counts, and gaps found on the way

### 11.1 Notes per track

| Track | Common | Rare | | Track | Common | Rare |
|---|---|---|---|---|---|---|
| Main | 25 | (rare-any 12) | | Level 10 | 5 (+1 slot for 3999) | 1 |
| Level 0 | 9 | 2 | | Level 11 | 7 | 1 |
| Level 1 | 9 | 1 | | Level 37 | 6 | 1 |
| Level 2 | 6 | 0 | | Level 94 | 7 | 1 |
| Level 3 | 7 | 1 | | Level ! | 5 | 1 |
| Level 4 | 6 | 1 | | Level Fun | 5 + the altered note | 1 |
| Level 5 | 7 | 1 | | The End | 5 | 1 |
| Level 6 | 6 | 1 | | The Hub | 5 | 1 |
| Level 6.1 | 4 | 0 | | Level 974 | 3 | 0 |
| Level 7 | 6 | 1 | | Level 3999, 188 | slots | |
| Level 8 | 6 | 1 | | Scraps | 10 | |
| Level 9 | 6 | 1 | | | | |

186 entries: 145 common, 30 rare, 10 scraps, 1 special. Every note also marks by its paper's kind.

### 11.2 Gaps found while checking the hints (for the level owners)

Found by reading the code on 2026-10-09; none is fixed by this plan except the first two, which the notes system
absorbs. The hint texts above avoid promising anything listed here.

- `fun-wanderernote-altered` does nothing when read (no `altered` case; not used up); its text is never shown. → fun-lie.
- `note-run` exists in lang but nothing shows it. → run-2.
- Door notes find nothing in Level 11, 37, 94 and all of 14–20 (`IsNoclipRegion`). → per-level resolvers (4.2).
- Nothing places `hub-key-fun` in Level Fun (HubSystem leaves Run, Fun and End to place their own; Fun does not). Only
  the Keymaster or the M.E.G. trader give it. hub-3 does not mention Fun.
- `end-memoryjuice` and `fun-lucatears` have no source, so The End's Junkies cannot be traded with in practice. No note
  mentions them.
- `hub-key-l1`, `-l11`, `-l61` exist, but those Hub doors open without a key.
- The Hub's End door lands anywhere in The End (`In(TheEnd)`), not beside an EXIT door as LINKS.md says.
- The End's Turnaround loop is off by default (`/endloop on`); no note mentions it.
