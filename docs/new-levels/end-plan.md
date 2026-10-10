# The End: research, design and integration plan

**The End** is the Backrooms' trap level: a library that goes on forever and looks like the way out. It is a closed-down bookstore with no books. A curved service desk holds an old CRT terminal, metal letters over it spell THE END, and the empty maple shelving runs off under fluorescent troffers into silence. Walk on far enough in one direction and the aisle loops. Turn round, and there is a wall.

In this mod it is **level 16** (`WorldLayout.TheEnd`), shown as **"End"**. It is a noclip region far to the north-west, owner tag `end`.

This is a design only; nothing is implemented yet. Section 9 lists the decisions for the user, each with a recommendation.

## Status (2026-10-09): code implemented (phase 2), headless-checked, not yet played in a client

**Built (C#):**
- **Layout** (`WorldLayout.LevelEnd.cs`): the region, departments of 64 blocks with the wandering runway and its jams, and the central hall. Department kinds:
  - stacks, open floor, service desk under a lettered soffit, reading room;
  - two-storey atrium (deck, railings, escalator, library stacks with ladders, pendants);
  - stockroom (EXIT doors, staff door, cooler, vent);
  - collapse, the long aisle pair (exactly periodic);
  - the six fake realities with their blend.
- **Blocks** (`WorldGenerator.End.cs`): the fake-reality cores are drawn by the imitated levels' own block code.
- **Thresholds** (`ThresholdNetwork.End.cs`, `ThresholdSystem.End.cs`). Entrances:
  - Level 1: EXIT door, 1 in 25 locked hall doors (salt 0x1610);
  - Level 4: lone doorframe, one-way (0x1611);
  - Level 11: a closed bookstore lot, `CityKind.Bookstore = 40` (0x1612).

  Exits:
  - EXIT doors: 2 in 3 locked; the rest lead to 1, the Hub (beside a service door), 11, 4 or 5;
  - fake-reality doors, to 0, 4, 5 and 9;
  - the vent, to 94;
  - "=)" computers, to Level Fun (one-way);
  - distortions (two-way).

  `IntoEnd()` now arrives beside an EXIT door by default, so Level !'s and the Hub's ways in do as LINKS.md says.
- **Runtime** (`Regions/EndSystem.cs`):
  - computers: one use; map marks of the nearest open exits;
  - distortions: watched attributes, the client's fog and shake, the noclip;
  - lights-out, the isolation drain, echo steps (client), fragile shelves (block class);
  - found books and `backrooms:hub-key-end` from desks and catalogues (8%);
  - catalogue cards and Memory Juice;
  - the Junkies: wanderer sites in Home; no juice, no trade.
- **Client air and sound** (`AtmosphereSystem.End.cs`).
- **Shared edit points:** temperature 19 °C, fog, Roster (Smiler glimpses in the collapses' dark; four distant sounds), menace band (Safe, Heartland in collapses), sanctuary, never picked over, roof from rel 5, the wanderer site hook, a `PropTable` row, and the `ColumnBlock` entrance hook.
- **The loop and the Turnaround are behind a flag, off by default (`/endloop on`). They are untested in a client.**

**Checked:**
- `endhash`: only Levels 1, 4 and 11 change, and only by The End's entrances (with them off, Level 4 and 11's lines equal the baseline `d4a0005bf8137db6` run; Level 1's other change is the Hub's and Run's).
- `regions`: 60/60 arrivals, none in a pocket, in both world sizes; 0.17–0.42 ms per cell.
- `links`: L1 endexit and L11 endbookstore paired, L16 endexit (open, two-way; locked), endvent to 94 (two-way), L4 endframe one-way. No failures.
- `endstats` (841 departments): kinds as planned; 81% of floor within 3 blocks of a working light; 1 shelf in 38 with books; 60/60 arrivals beside an EXIT door.
- `endloop`: 27/27 long aisles exactly periodic, a way out in every period.
- Headless server on port 42476, dumps rendered (stacks, central hall, atrium):
  - floor light averaged 6.7–6.9 in each dump, 60–63% of open floor at 7 or more;
  - the atrium's gallery averaged 9.5, but its void floor only 5.5, with the pendant at light 15. The pendant needs `lightHsv [8, 2, 20]` (asked for under Manifest changes).

**Deviations:**
- Region radius as scaffolded: `max(60, spawnMacroX/40)`.
- Posters, the EXIT sign and the vent are full wall blocks.
- Fake-reality exits are walk-through doorways, and the hotel's guest doors behave as Level 5's do.
- The Junkies are the ordinary wanderer, gated by a behaviour.
- No INFORMATION hang signs were placed.

---|---|
| Layout stub | `src/Worldgen/WorldLayout.LevelEnd.cs` |
| Generator stub | `src/Worldgen/WorldGenerator.End.cs` |
| Floor drop | `WorldGeometry.EndDrop` (0 for now) |
| `WallPattern` | 96–111 |
| `FloorKind` | 132–147 |
| `CeilingKind` | 32–39 |
| `Overheads` | 60–69 |
| `Unders` | 60–69 |
| `Props` | 360–399 |
| `Decor` | 196–207 |
| Hash salts | 0x1600–0x16FF |

This plan uses those blocks, and the code and asset agents should take the exact rules from `docs/new-levels/CONTRACT.md`. One shared line needs changing: **The End's band bottom must be `FloorFor(TheEnd) - 24`, not `- ShaftDepth`.** Section 3.3 explains why.

---

## 1. What the lore says

Sources, in order of weight: Wikidot (primary canon), Fandom, Miraheze, then well-known depictions. All pages were fetched on 2026-10-06. Copies are in this session's scratchpad (`end/`).

### 1.1 Which "The End"

There are many unrelated pages called "The End":
- fan wikis on Fandom: backrooms-freewriting, the-backrooms-random-level, backrooms-liminality, the-backrooms-fanmade, backrooms-redacted;
- Apeirophobia's Level 7 "The End?";
- Escape the Backrooms' level of that name;
- a pixiv dictionary entry.

**The canonical one is the empty bookstore-library with "THE END" over its service desk.** Three reasons:

1. **It is the original.** The Backrooms Fandom page "The End" (page id 464) was created on **2019-06-20 by Skivy123**, one of the wiki's first pages. It was built round a single photo, "Only known and first photo of The End" (`5e9dlekogg331.jpg`): an empty bookstore with a CRT on a curved desk under the metal letters THE END.
2. **Wikidot took it in.** The Wikidot page **Level 601 – "The End"** credits it: "The original author of this entry is skivy123, Rewritten by 1000dumplings". Wikidot has no page at `/the-end`. Level 601 is the only The End there.
3. **Everything else follows it.** Escape the Backrooms (the best-known game depiction) and the Wikidot render both reproduce the same photo. Fandom notes that "the actual location of The End's images are in a Borders bookstore" (a chain that closed in 2011).

The others are unrelated fan pages, and are ignored.

### 1.2 Canon: Wikidot, Level 601 "The End"

Source: https://backrooms-wiki.wikidot.com/level-601. Rewritten by 1000dumplings, original by skivy123. Survival difficulty: **unknown** (`{$one} {$two} {$three}`). The page carries a "being rewritten" banner, but its text has not changed since at least March 2024 (Wayback).

- **A trap.** The End is "supposedly a 'trap Level' that creates the illusion of escaping The Backrooms".
- **The look.** "A seemingly endless modern library, with the main area in the center decorated with metal letters spelling 'the end is near'."
- **Silence.** "Near complete silence, with some areas measuring at -6.2dB", but "the computer terminals within buzz loudly".
  - "It is recommended to stay here and not explore to prevent feelings of isolation."
- **The geometry is unstable.** "The Level seems to loop when walking in one direction. However, turning around at this point will cause you to run into a wall."
  - Random noclipping happens, but it never leads out.
  - "Exits do exist, but there is currently no way to document them."
  - Wanderers sometimes cannot perceive one another "even if they are within extremely close proximity".
- **Fake realities.** "Personalized sub-areas of The End that replicate familiar environments", corporeal and physical, close to one another.
  - They have a "transitional" effect: the areas between them "blend together the nearer you are to another fake reality, eventually transitioning completely".
  - "When a border of a fake reality is breached everything will return to normal."
  - The illustration ("corrupted") is an endless grass field with a vending machine standing in it.
- **No electricity.** "Anything that uses electricity to function immediately ceases all functionality", except the terminals, which "seem to be able to connect to any Wi-Fi source".
- **Partygoers.** "It is highly advised not to use the computer terminals... this area seems to be frequented by the Partygoers and quite possibly the 'host' Entity". There are "at least three different reports of Wanderers being taken by Partygoers after being chased into The End."
- **"The Junkies."** Six people with an outpost *in the fake realities*. They trade only with someone who has Memory Juice, and spend their time "intoxicating themselves on Memory Juice in an attempt to make themselves believe that they are home". The B.N.T.G. failed to rescue them.
- **Entrances.**
  - "Doors that would typically indicate an exit. Most commonly, this is any door with a neon sign above it."
  - Rarely, random noclipping.
- **Exits.** "The fake realities of The End can sometimes contain exits into other, safer Levels. However, this is not consistent. A reliable way to leave The End has not been discovered."
- **The addendum** is signed "=)" (the Partygoers' host): "They can leave, they can die, or they can go with my ideas."
- **Render** (pixelpurple, 2026), in effect the photo modelled:
  - grey-brown carpet with a patch of blue patterned carpet;
  - pale maple shelving, all empty, and tapered slatwall pyramid display towers;
  - a curved maple service desk with a beige 90s CRT and keyboard;
  - sage-green square columns clad in slatwall at the base, with yellow "THE END THE END THE END" sale posters and pink and green notices;
  - a cream wall with a yellow band, and a raised yellow soffit with the letters THE END;
  - a 2×2 acoustic tile ceiling densely set with 2×4 troffers.

**Other Wikidot pages that link here:**
- **Level 94** (https://backrooms-wiki.wikidot.com/level-94): "To Enter, you must first be in Level 601, and successfully escape, and make your way to the Hub", then fall through a hole into Level 94. So canon has a route **The End → The Hub → Level 94**.

### 1.3 Second opinion: Fandom, "The End"

Source: https://backrooms.fandom.com/wiki/The_End, read through the API. Current rewrite by ArbiTraitor (Arbi), previous by BBMBear, original by Skivy123. Class 3 (β): **"Inconstant Stability", "Inscrutable Security", "Devoid of All Life"**.

- **A library with no books.** It is "a presumably infinite library composed of open areas and wide corridors": bookshelves, stands and "the usual apparatus of a normal library".
  - "Furniture is often positioned randomly, sometimes converging with one another or connecting into the walls."
  - "The library is virtually devoid of books, leaving its shelves barren."
- **Its own name everywhere.** "Short texts and labels can be found meaninglessly placed on walls, commonly depicting the level's name."
- **Decay.** "Temporal decay": cracked walls, and "some shelves may collapse under slight pressure".
  - The lights are faulty: "occasionally flickering or sometimes shutting off temporarily".
- **The computers.** Old-style computers, "heavily resemblant to vintage personal computers", are sparse.
  - They are "pristine" and **indestructible**, and almost always inoperative or unplugged.
  - One that works turns on "for mere seconds before abruptly turning to a fading static", with "a light buzz before displaying the level's name in white text. Afterward, the computer cannot be turned on again."
- **Untouched things.** Chairs, ladders and posters lie about, "covered by a thin layer of fine dust or wrapped in plastic packaging".
- **Silence.** Sound is "severely muted", "around zero decibels", broken only by the computers and the "faint fluorescent lighting".
- **No direction.** Geometry is "loosely defined... twisting and warping in ways that cause all navigational methods to become fruitless".
  - Long exposure brings auditory and visual hallucinations.
  - It is "merely a facade of an empty shell... a spatial threshold—an in-between space between levels".
- **"Distortions"**, a recovered note: the lights flicker "in indiscernible patterns as the floor violently shook". For a few seconds the writer stood in "an endless snowscape" with barren trees. Later distortions showed "the dull infinity of the Lobby", or places "unknown to all databases".
- **Entrances.** Rare "indestructible wooden doorways that lack actual doors".
  - The view through one is distorted, and sound near it is weaker.
  - "Upon passing the threshold, the entrance will immediately vanish."
- **Exits.**
  - "Noclipping during distortions will... cause the wanderer to enter the scene presented during that distortion."
  - "An exit door that leads to a random level."

**The page's history** (500+ revisions) shows how fan pages accrete. In 2021 the page held a list of over 60 "run X.exe on the computer" exits: to the Hub, Level Fun, Level 11, the Frontrooms, a Volatile-infested sewer and a food court. They are noted as fan accretion, **not canon**. The one image they leave is the computer as a gateway, which Wikidot's terminals also suggest.

### 1.4 Miraheze

`backrooms.miraheze.org` has **no page** for The End or for Level 601 (checked by title and by full-text search). There is no second opinion from there.

### 1.5 Depictions

- **The two Borders photographs** (Fandom: `5e9dlekogg331.jpg`, `Borders-the-end-is-near.jpg`) define the look:
  - grey-green low-pile carpet, with a field of navy patterned carpet;
  - free-standing maple gondola shelves and wall shelving, all empty;
  - tapered slatwall pyramid towers;
  - square columns painted sage green and slate blue, clad in maple slatwall to about 2 m;
  - cream walls with ghost marks where fixtures were taken down, under a yellow band;
  - a lowered soffit with bronze letters "THE END" and, in the second photo, "THE END IS NEAR";
  - fluorescent troffers in a 2×2 acoustic tile ceiling;
  - neon-yellow "FOR SALE: ALL FIXTURES, FURNITURE & EQUIPMENT" posters and pink and green cards;
  - in the first photo, a CRT on the curved desk and a cable on the floor.
- **Escape the Backrooms** (https://escapethebackrooms.fandom.com/wiki/The_End, `/wiki/Scratcher`):
  - **The route.** On the main path **Level ! → The End → Level 94**: you reach it through the door at the end of Level !'s hallway, and leave by a vent at the top of a ladder in a damaged back room into Level 94.
  - **The room.** A big "abandoned library": a computer on the centre desk that counts the tapes you must collect off the bookshelves (24, 32 or 48), two tables to hide under, and two fire alarms that draw the entity.
  - **Lights Out** after 90 seconds: from then on, flashlight only.
  - **The Scratcher:** a blind, grey, quadrupedal humanoid with red eyes that hunts by sound. The game's own wiki says "On the Backrooms Fandom Wiki, the Scratcher doesn't exist in The End".
  - **Items:** Almond Water, energy bars, a flashlight.
  - **Sound:** the level's ambience is a near-silent loop.
- **Wikidot render** by pixelpurple: see 1.2.

### 1.6 Ways in and out

| Source | Entrances | Exits |
|---|---|---|
| Wikidot 601 | Doors that would usually be exits, **any door with a neon sign over it**; random noclip (rare) | Exits in **fake realities** into "safer" levels, not consistently; no reliable way out |
| Wikidot 94 | – | Escaping 601 → **the Hub** → a hole → **Level 94** |
| Fandom | **Doorless wooden doorways**, indestructible, distorted view, muted sound; they **vanish** once passed | **Noclipping during a distortion** into the scene shown; **an exit door to a random level** |
| Escape the Backrooms | The door at the end of **Level !** | A **vent up a ladder** in a back room → **Level 94** |
| Fandom 399 (fan) | – | "Run TRUEEND.EXE in The End's only computer" → Level 399 (not 3999) |

### 1.7 Contradictions

| Question | Answers |
|---|---|
| Survival class | Wikidot: unknown. Fandom: Class 3. ETB: Class 2 |
| Life | Fandom: "Devoid of All Life". Wikidot: Partygoers frequent it, and the Junkies live there. ETB: a Scratcher |
| The letters | "THE END" (first photo, Fandom, ETB, Wikidot render) or "THE END IS NEAR" (second photo, Wikidot text) |
| Exits | Wikidot: no reliable way out. Fandom: an exit door to a random level. ETB: a vent to Level 94 |
| Electricity | Wikidot: anything electric dies (except the terminals). Fandom: the troffers hum and flicker, so they do work, badly |
| Computers | Wikidot: terminals connect to any Wi-Fi, used by the Partygoers' host. Fandom: they show the name once, then die for good |

The design keeps Wikidot's structure: the trap, the loop, fake realities as the way out, terminals, Partygoers and Junkies. Fandom supplies the look, the decay, the distortions, the doorframe entrance and the exit doors. ETB supplies the vent to Level 94 and the Level ! link. Both letterings appear: THE END on the desks' soffits, THE END IS NEAR at the centre.

---

## 2. Where it fits

### 2.1 A noclip region, like the city, the Poolrooms and Motion

The End is not a ring. Like Levels 11, 37 and 94, it is a region far out that only thresholds reach. The scaffold already places it.

| | The End |
|---|---|
| Region | North-west of spawn: centre `spawn − DiagonalReach` on both axes (the scaffold's `EndCentreX/Z`). It touches no other region |
| Size | Radius `Math.Max(64, spawnMacroX / 25)` cells (≈ 2 km), so it is endless to anyone in it. The scaffold has 60; 64 makes the radius a whole number of 64-block departments |
| Rim | The store's back wall: cream wall under the yellow band, full height, lined with wall shelving and locked EMPLOYEES ONLY doors. No way through |
| Floor | **`EndDrop = 6`** below the shared floor, for the two-storey atrium (section 3.3) |
| Sky | Enclosed: a drop ceiling, its plenum, and the mantle cap at rel 16 |
| Shown as | "The End" (`DisplayNumber` "End"); `/backrooms goto end` |

### 2.2 Its part in the threshold network

The network rules hold throughout:
- every threshold always leads to the same place;
- **walked through = two-way; fell, dived or taken = one-way**.

Each entrance in another level gets its own hash salt from 0x1600–0x16FF, so no other level shifts except where the entrance stands.

**Ways in**

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| **Level 1** | A shut grey steel door under a **glowing EXIT sign**: about 1 in 25 of the locked room doors off the maintenance halls (`Unders.EndExitL1`) | The End, beside one of its EXIT doors | **Two-way:** the EXIT door you arrive beside (it becomes the way back) | Wikidot: "any door with a neon sign above it"; Level 1 is the mod's level of EXIT signs |
| **Level 4** | Walking through a **free-standing wooden doorframe** with no door, standing alone on the carpet of an open-plan floor (1 cell in about 60). Through it the room shimmers, and sound is muffled near it (`Props.EndFrame` + `Unders.EndFrame`) | The End, anywhere near the middle | **One-way:** "upon passing the threshold, the entrance will immediately vanish". You were taken (decision 10) | Fandom's wooden doorway |
| **Level 11** | The glass door of a **closed-down bookstore** (new `CityKind.Bookstore`, about 1 midtown lot in 120). Its windows are papered with yellow THE END IS NEAR and ALL FIXTURES FOR SALE posters; inside, empty maple shelves | The End, beside an EXIT door | **Two-way:** that EXIT door | The photos are a Borders bookstore, and the store front makes the joke physical |
| **Level !** (14) | **The door at the end of the hallway**, if the `run` plan agrees; otherwise a rare "special" false-exit door | The End, beside an EXIT door | **Two-way:** that EXIT door | Escape the Backrooms; Wikidot's exit-door entrance; Level !'s false exits "lead to some anomalous level" (Fandom) |
| **The Hub** (17) | One of the Hub's doors, its sign reading THE END (the `hub` plan's choice) | The End, beside an EXIT door | **Two-way:** that EXIT door | Wikidot Level 94: from The End you "make your way to the Hub" |

**Ways out**

| From The End | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| EXIT doors | A steel door under a red neon EXIT sign, in the stockrooms' back walls and the central hall's four corners (`WallPattern.EndExit`). **Two in three are locked** ("The EXIT sign glows. The door does not open.") | Fixed per door: Level 1 40% (beside a Level 1 EXIT door if one is near), **the Hub** 25%, Level 11 15% (beside a bookstore door), Level 4 10%, Level 5 10% (beside a locked guest door, which now opens) | **Two-way:** that door, or a thin spot | Fandom: "an exit door that leads to a random level". Wikidot: no *reliable* way out |
| A fake reality's door | The real door in the heart of a fake reality (`Unders.EndFakeDoor`). It works in 3 fake realities out of 5; the others are painted shut or open onto a wall | Lobby → **Level 0**; Office → **Level 4**; Hotel → **Level 5** (beside a locked guest door); House → **Level 9** (out of a locked front door) | **Two-way:** the partner door (5, 9) or a thin spot (0, 4) | Wikidot: fake realities "can sometimes contain exits into other, safer Levels" |
| The stockroom vent | A grille 3 blocks up a back wall, reached by a fixed steel ladder, in about 1 stockroom in 3 (`Decor.EndVent`) | **Level 94**: you fall out of the sky over the hills and land softly, as every arrival there does | **Two-way:** thin spot on the grass | Escape the Backrooms: the vent up the ladder into Level 94 |
| A "=)" terminal | Turning on a terminal that is one of the Partygoers' (1 in 4, fixed per terminal). Its screen says "=)" instead of THE END | **Level Fun** (15) | **One-way:** taken | Wikidot: wanderers "taken by Partygoers"; the addendum's "=)" |
| A distortion | Walking into a wall or a shelf **during a distortion** (section 3.6). Each department always shows the same scene | That scene's level: the Lobby (Level 0) 35%, the Office (4) 15%, a house (9) 15%, the Poolrooms (37) 10%, the hills (94) 5%. The snowscape (20%) leads nowhere | **Two-way:** thin spot | Fandom: "noclipping during distortions... enter the scene presented" |

**Cross-links with the other new levels.** These are proposals, to be agreed with each owner:
- **Level !** → The End (its end door). Two-way.
- **The Hub** ↔ The End. Hub door ↔ End EXIT door, both two-way.
- **The End → Level Fun.** One-way, through the "=)" terminals.
- **No link** with Level 974 or Level 3999: canon has none. Fandom's TRUEEND.EXE leads to Level 399, a different level.

The handbook's "Ways Between Levels" page and the README table gain these rows.

---

## 3. Design

### 3.1 The experience

You step through a door marked EXIT, and the air changes: cool, still and dry, smelling of carpet and dust. The hum is gone; what is left is a silence so complete you can hear the troffers tick. A long curved desk holds a beige computer, and its screen glows. Over it, in bronze letters: THE END. You made it out.

Then you see the shelves. They are all empty, and they go on in every direction.

There is no food. Your stability creeps down the longer you stay. A long aisle seems never to end, and when you turn round, it is a wall. Now and then the floor shakes and for a heartbeat you are standing somewhere else: in the Lobby, or in snow. Somewhere there are doors marked EXIT, and most of them are locked.

Design goals, in order:

1. **It must look like the photo at first sight:**
   - maple shelving, slatwall pyramids and sage columns;
   - a curved desk with a CRT, and the THE END letters;
   - grey-green carpet with a blue runway, under troffers.
2. **It is a trap, not a fight.** The danger is getting lost, the silence, hunger and the slow loss of stability, never a monster you can see (Fandom: devoid of all life).
3. **It is where you learn the network.** Terminals, catalogue cards and books tell you where the ways out are. It is also where a Vintage Story home gets its furniture: chairs, tables, ladders, shelves, paper and ink.

### 3.2 Structure: departments on a wandering racetrack

Layouts made cell by cell read as noise (`docs/level-design-plan.md`). The End is planned in **departments of 64×64 blocks (2×2 cells)**. Each department's plan is worked out from its id and cached with `PlanCache`, as Level 37 caches `PoolPlan`. Seams across cells come out right, as in `BuildLevel37`.

**The runway (the store's racetrack aisle).**
- **Where.** A 5-wide band of navy patterned carpet runs along every department line (`EndRunway` floor).
- **Its shape.** Like Level 37's galleries, each line *wanders* by a hashed sine: amplitude 0–4, period 30–50, as in `GalleryOffset`. It is computed from world coordinates, so it is seamless.
- **How it meets the departments.** Shelving runs end on it with end-caps. Corners open into 9×9 plazas, where there is often a column with posters.
- **Sightlines.** These are *the wide corridors* of the lore, so views are long, as in the photos.
  - About 1 runway stretch in 3 is **jammed**: furniture has "converged" across it (a shelving run, a desk and a trolley grown into one another), so you go round through the department.
  - Long straight views stop after 64–192 blocks, and the user's dislike of endless straight lines is respected outside the deliberate Long Aisles.

**Departments.** Each 64×64 block is one of the kinds below, by hash. Each kind has a strict internal grid, but its orientation and offsets differ from its neighbours'.

| Department | Share | Ceiling | What it is |
|---|---|---|---|
| **Stacks** | 34% | 5 | Rows of double-faced gondola shelving 2 high, in runs of 4–10 with 2-wide aisles, and cross-gaps every 5–7. An end panel or a pyramid end-cap at each row end. 1 run in 10 "converges": it bends diagonally into the next row, or runs straight into a wall or column |
| **Open floor** | 20% | 5 | The photo: open carpet with scattered slatwall pyramid towers, display tables, a few short shelves, slatwall-clad columns, a chair or ladder still in plastic. The blue carpet field lies in one corner |
| **Service desk** | 8% | 5, soffit 4 | A curved maple desk (7–11 tiles, ∩- or C-shaped) with **a CRT terminal** on it, under a lowered **soffit** with the bronze letters **THE END** on its face. Columns nearby carry THE END posters. The "labels depicting the level's name" |
| **Reading room** | 10% | 5 | Study tables with green banker's lamps (the only warm light), library chairs, study carrels along the walls, a **card catalogue**, a magazine rack, armchairs, low wall shelving |
| **Atrium** | 7% | 12 | Two storeys round a void: a **mezzanine** gallery 4 wide at rel 6 with a glass railing, a **dead escalator** up one side, **tall stacks** 4 high on the ground floor with **rolling library ladders**, pendant lamps hanging in the void |
| **Stockroom** | 8% | 5 | Back of house: sealed concrete, painted block walls, pallet racking with **shrink-wrapped stock** (chairs, ladders, shelving kits), book trolleys, an **Almond Water cooler** in a break nook. **EXIT doors** in the back wall; a **vent** up a steel ladder in 1 in 3 |
| **Long Aisle** | 4% | 6 | The loop: a straight 3-wide aisle 128 blocks long (it takes two departments), between tall stacks, repeating exactly every 32 blocks (see 3.6) |
| **Collapse** | 4% | 5 | Temporal decay: shelves fallen like dominoes, ceiling tiles down showing the black plenum, cracked walls, every light dead |
| **Fake reality** | 5% | varies | Only beyond 25% of the radius. See below |

**The central hall** replaces the departments within 48 blocks of the region's centre. It is a fixed plan, the photo at its grandest:
- a **round service desk** 9 across in the middle, with a terminal that only ever says THE END (never "=)");
- above it a ring soffit lettered **THE END IS NEAR** on all four faces;
- four sage columns plastered with yellow posters;
- open carpet with pyramid towers, and the blue carpet field round the desk;
- a ring of stacks;
- an **EXIT door in each of its four corner walls**, so that arrivals beside an EXIT door can always be found near the middle.

It is where most arrivals land. Wikidot: "stay here and not explore".

**Fake realities.** About 1 department in 20, only past a quarter of the way out, never two within 3 departments of each other.
- **The blend.** Over the outer 16 blocks of the department the library gives way to the imitation. The share of imitated tiles rises toward the core: first the floor (carpet), then the walls, then the ceiling and lights, and the shelving thins out. Wikidot's "transitional effect".
- **The core.** A 32×32 fragment of the place imitated. Leave its border and the library is back ("everything will return to normal").
- **Materials.** The imitations reuse the other levels' own blocks. They are copies of those places, so the asset cost is small.

| Fake reality | Share | Core | Exit (3 in 5 work) |
|---|---|---|---|
| **The Lobby** | 30% | Level 0's yellow chevron rooms, beige carpet and troffers, and its hum (the only hum in The End) | A doorway in a lone wall → **Level 0** (thin spot) |
| **The Office** | 15% | Level 4's grey carpet, cubicles, windows onto rain | A door marked STAIRS → **Level 4** (thin spot) |
| **The Hotel** | 15% | A stretch of Level 5 corridor, red damask carpet, guest doors | One guest door → **Level 5**, beside a locked guest door that now opens |
| **The House** | 15% | A Level 9 living room and hall, floral paper, a front door | The front door → **Level 9**, out of a locked front door |
| **The Snowfield** | 15% | Fandom's "endless snowscape": the carpet disappears under snow (vanilla snow layers), bare trees stand between the shelves, the ceiling lights go white and far apart. It is cold (−6 °C) | None: a vision you can walk in |
| **Home** | 10% | A warm living room from the real world: lamps, a sofa, a TV of static, a window glowing like an afternoon. **The Junkies' camp** (section 3.8) | None |

### 3.3 Heights

- **`EndDrop = 6`.** The End's floor lies 6 below the shared floor, so its ceiling can rise to rel 15 before the mantle cap at rel 16 (CapY = FloorY + 10).
- **The band.** It must reach that high: **`BandBottomFor(TheEnd) = FloorFor(TheEnd) - 24`**. The band is 40 tall, so it covers rel −24 to +15. With the scaffold's `- ShaftDepth` it would stop at rel 9, and the atrium's pendants and the mezzanine would get no light.
  - The generator's `bottom` for the level already follows `BandBottomFor`.
  - Nothing of The End lies below its floor, so the lost depth costs nothing.

| What | rel (above The End's floor) |
|---|---|
| Carpet | 0 |
| Ordinary rooms | air 1–4, ceiling (acoustic tile or troffer) **5**, plenum 6–15 (concrete) |
| Under a soffit | air 1–3, soffit block 4 (letters on its face), ceiling 5 |
| Long Aisles | air 1–5, ceiling **6** (tall stacks 4 high either side) |
| Atrium | ground air 1–5; mezzanine deck **6** (its underside carries troffers); gallery air 7–11; ceiling **12**; pendants hang to 9 in the void |
| Shelving | gondola 1–2 (cornice just under 3); tall stacks 1–4; desk 1 with the terminal on top at 2 |
| Walls | 1 base (vinyl cove), 2 off-white lower, 3 the **yellow band**, 4+ yellow-cream upper, to the ceiling |

### 3.4 Light

- **Troffers.** 2×4 fluorescent troffers in the acoustic tile, on a 4-block grid (orientation and offset per department). This is the photos' dense field of lights.
  - About 1 in 3 is `LightOn` (emits light 14, a neutral warm white). The rest are `LightLit` (glow only), as Level 0 does for speed.
  - About 6% are `LightOff` and 3% `LightFlicker` (the existing flicker block entity): the "faulty lights" of Fandom.
- **Warm accents.** Reading-room lamps (warm light 10) and the atrium's drum pendants (15).
- **Dark places.**
  - Collapse departments: all troffers dead.
  - Stockrooms: half dead.
  - Long Aisles: one line of troffers down the aisle, every 4 blocks.
- **Lights out.** Now and then the lights go out round you (section 3.6).
- **Terminals.** A terminal's screen glows faintly (light 4) while on.

### 3.5 Fog and sound

- **Fog.** Thin and warm-cream, like the photos' yellowish air: `new(0.004f, 0.84f, 0.80f, 0.64f, 0f)`. Overrides:
  - the Lobby fake reality takes Level 0's;
  - the Snowfield is bright and white-blue (0.02, 0.90/0.93/0.97);
  - Home is warm amber (0.006, 0.80/0.66/0.48);
  - during a distortion it swings to the scene's colours (3.6).
- **Silence is the sound of The End.**
  - **Room tone:** a loop at volume 0.25, nearly nothing: a faint 120 Hz ballast tick and a very high hiss.
  - **Terminals buzz** (Wikidot): each unused terminal plays a loud CRT whine within 10 blocks. You hear the central desk before you see it.
  - **Distant sounds** are rare and small: a book falling, a shelf creaking, a chair scraping, a page turning. The director plays them at a quarter of the usual rate.
  - **Echo steps.** When you stop after walking a while, now and then (1 in 6) two or three soft footsteps carry on somewhere close behind you, then stop. Nothing is there.
- **Noise.** With so little sound, noise counts double in the director's noise level. It only matters where something listens (a "=)" terminal's Partygoers, Smilers in the dark).

### 3.6 Mechanics

| Mechanic | Rule | Why |
|---|---|---|
| **Temperature** | 19 °C (an air-conditioned store); Snowfield −6 °C; Home 22 °C | Cool, dry, still |
| **Stability** | 1.2 in the central hall. Out in the library it falls from 1.0 to 0.75 toward the rim, ±0.15 drift ("Inconstant Stability"). Collapse departments 0.45, fake reality blend 0.6, cores 0.45, Snowfield 0.35, Home 0.9 | "Stay here and not explore". Isolation grows with distance |
| **Isolation** | After 2 in-game hours spent in The End without leaving, your stability drains a further 0.01 a minute, down to a floor of 0.25. It resets when you leave | Long exposure brings hallucinations; vanilla's low-stability distortion supplies them |
| **The loop** | In a **Long Aisle**, walking straight on (speed above 2 blocks/s, facing within 30° of the aisle) past 96 blocks along it moves you back 64, to a spot that looks exactly the same: the aisle repeats every 32 blocks (stacks, lights, posters, cross-gaps). It only happens with no other player within 48 blocks | Wikidot: "the Level seems to loop when walking in one direction" |
| **The Turnaround** | At the moment the loop moves you, a full-height bookcase (the same tall stacks the aisle is made of) is set across the aisle 5 blocks behind you, out of sight. Turn round, and you walk into it. The cross-gaps ahead (every 32 blocks, left and right in turn) always lead out. The bookcase is taken away again once nobody is within 48 blocks and none can see it | Wikidot: "turning around at this point will cause you to run into a wall" |
| **Distortions** | Once you have been in The End 20 real minutes, one comes every 8–15 minutes. For 12 seconds: <br>• the lights pulse in patterns, the camera shakes and a low rumble rises; <br>• the fog and the sound bed become the department's scene (the Lobby's yellow and hum, the snow's white and wind, the Poolrooms' teal and lapping, Motion's tune, the office's rain). <br>**Walk into a wall or a shelf during one** (pressing against it for half a second) and you go through, into that scene's level (2.2). Each department always shows the same scene, so the threshold is fixed | Fandom's "Distortions" note and its exit |
| **Lights out** | Every 60–120 in-game minutes, a breaker clunks and the lights round you go out for 60–120 s. This reuses Level 1's Flickering darkness ("round the player only") without the Hounds. Terminals stay lit | Fandom: lights "sometimes shutting off temporarily"; ETB's Lights Out |
| **Terminals** | Right-click a CRT. It buzzes, the screen shows **THE END** in white for 3 s, then fading static, then it is dead for good (the block becomes `dead`, saved with the world). <br>**What it gives:** your map is marked with the nearest *working* way out within 400 blocks (an unlocked EXIT door, a working fake-reality door, a vent), and up to two more beyond it. <br>**1 in 4** terminals (fixed by hash, never the central hall's) show **"=)"** instead, and you are taken to Level Fun (one-way) | Fandom's one-time computers. Wikidot: terminals "connect to any Wi-Fi source", and the Partygoers' host is behind them |
| **Fragile shelves** | `leaning` shelves (1 in 25 in Stacks) fall the moment anything pushes them: walk into one, or hit it once with anything. They come down as rubble and a few boards, with a crash that counts as noise | Fandom: "some shelves may collapse under slight pressure" |
| **Indestructible** | Terminals, EXIT and staff doors, vents, letters, the Level 4 doorframe, and the rim from the ceiling up. Everything else breaks down as usual (`Breakdown.cs`) | Fandom: the computers are indestructible |
| **Danger** | Menace band **Heartland** everywhere, with an almost empty roster (see 3.8). Sanctuary: the central hall and Home | "Devoid of All Life" |

### 3.7 What there is to find

There is no food in The End (lore says nothing of any), except Almond Water from the stockroom coolers (the existing `Props.Cooler` dispenser). **Nothing here was ever picked over**: "these objects appear untouched", so `MarkPickedOver` never marks The End. What The End gives is **the furniture of a home and the means to write and map**.

| Find | Where | What you get (vanilla where possible) |
|---|---|---|
| **Books (rare)** | 1 shelf in 30 holds a few (the `books` look); tall stacks 1 in 20 | 1–3 books: 60% blank writable `game:book-normal-*` (random colour), 30% a **found book** (pre-written; see below), 10% `game:book-aged-*` |
| **Found books** | As above, and 1 per Home fake reality | A vanilla book pre-filled with one of 12 short texts (title, signed "unknown"). Among them: the Distortions note, a log of the loop, "THE END IS NEAR" copied over and over, a Junkie's diary, a wanderer's list of which EXIT doors opened, the "=)" addendum. Readable in vanilla's book GUI |
| **Paper** | Desks, posters, catalogues | `game:paper-parchment` (blank, writable) |
| **Ink and quill** | Service desks (8%) | `game:inkandquill`: write your own notes and books |
| **Catalogue cards** | Card catalogues (1–2 each), desks (20%) | `end-cataloguecard`: read it like a wanderer's note, and it marks the nearest way out of The End on your map |
| **Memory Juice** | Desks (15%), Home camps | `end-memoryjuice`: a small unlabelled bottle. Drink it: +0.2 stability, and for 30 s everything looks warm and like home. The Junkies' currency |
| **Chairs** | Reading rooms; plastic-wrapped in stockrooms and open floors | `game:chair-plain` (wrapped ones always; open ones 50%, else sticks) |
| **Tables** | Reading rooms | `game:table-normal` (50%), else planks |
| **Ladders** | Rolling library ladders in atriums; wrapped step ladders in stockrooms | 2–3 `game:ladder-wood-oak-north` |
| **Shelves** | Wall shelving, tall stacks | `game:shelf-normal-north` (20%), else planks and sticks |
| **Planks and nails** | Gondola shelving, shelving kits | Sticks, planks, `game:metalnailsandstrips-iron` |
| **Cloth** | Armchairs | `game:cloth-plain` |
| **Almond Water** | Coolers in stockroom break nooks | The existing dispenser |

The vanilla codes are to be verified against the installed game's assets: `ladder-wood-{wood}-{side}`, `chair-{type}`, `table-{type}`, `shelf-{type}-{side}` and `book-{color}` were all seen there. **Written books:** check `ItemBook`'s attribute names (`text`, `title`, `signedby`, or pages) by decompiling. If block drops cannot carry attributes, `EndSystem` gives found books in `OnBlockBroken`.

### 3.8 Entities and the Junkies

- **No new entity.** Fandom's "Devoid of All Life" is the rule.
- **The Scratcher** (ETB) is on no wiki, and the user wants lore first, so it is left out (decision 7).
- **Partygoers** (Wikidot: they frequent The End and take people). If the `fun` agent builds them for Level Fun, The End borrows them, in two places only:
  - a "=)" terminal: before it takes you there is a 3-second "Hello friend =)" moment with one standing at the end of the aisle;
  - the dark of a lights-out within 24 blocks of a "=)" terminal: Glimpse and Stalk, never Hunt.

  Without Partygoers, these become Smiler glimpses in the dark (`NeedsDark`).
- **Smilers** in the dark of Collapse departments: Glimpse only.
- **The Junkies** (Wikidot), in each **Home** fake reality:
  - **Who.** A wanderer site: 2 traders (the vanilla trader model, `backrooms:wanderer-junkie`, with its own trade list). `WandererSystem` gains End sites through `WandererSite`.
  - **Gated trade.** They will only trade with someone carrying **Memory Juice**. Otherwise the right-click gives a line in chat ("Got any juice? No? Then what are you doing here.").
  - **They buy** Memory Juice (6 rusty gears), books, Almond Water.
  - **They sell** blank books, parchment, ink and quill, catalogue cards, candles, and a found book.
  - **Safety.** Nothing hostile comes near them (as for every wanderer).

---

## 4. Asset manifest (`tools/gen_end.py`)

Paths:

| Asset | Path |
|---|---|
| Textures | `assets/backrooms/textures/block/end/*.png`, 32×32 (`S = 32`), items in `textures/item/end/` |
| Shapes | `assets/backrooms/shapes/block/end/*.json` (`detail_kit.shape`/`bx`, 16-px block units) |
| Blocktypes | `assets/backrooms/blocktypes/end/*.json` |
| Items | `assets/backrooms/itemtypes/end/*.json` |
| Sounds | `assets/backrooms/sounds/ambient/end/*.ogg` |
| Lang | through `LANG` |

Further conventions:
- Large surfaces use texture `alternates` (rotated or varied), as the README describes.
- "Oriented" means `side` variants north/east/south/west, modelled facing north (`ROTATE`).
- All codes are prefixed `end-`.

### 4.1 Palette (from the photos and the render)

| Name | Hex | Use |
|---|---|---|
| carpet | #646B5F (±6), loops #5A6155 | the grey-green low pile |
| dust | #8C9086 | dusty carpet flecks, dust on tops |
| runway | #2E3968, squiggles #5868A4, dots #98A2C6 | the navy patterned carpet |
| wall lower | #EEEBE0, scuffs #D8D3C4 | off-white |
| ghost | #F6F4EC | paler rectangles where signs hung |
| band | #DDB03A, edges #B88E22 | the yellow band |
| wall upper | #EBD69C | yellow-cream |
| cove | #45413B | vinyl base |
| maple | #CD9A55, light #DDB06C, dark edge #A9763A | shelving, desk, tables |
| slatwall groove | #7A5428 | 1-px grooves every 4 px |
| sage | #9AAE86 / slate #8B9AB1 | columns |
| ceiling | #E8E5DC, grid #C2BDB0 | acoustic tile |
| lens | #F5F7F1 | troffer lens |
| bronze | #463B2C, highlight #75664C | letters |
| poster yellow | #F2E43C; pink #F09CC2; green #A6DE78 | notices |
| CRT beige | #CFC6AE, shade #A99F86; glass #1C2220 | terminals |
| desk kick | #2A2622 | desk base |

### 4.2 Blocks: structure (cube or near-cube)

| Code | Variants | Texture | Notes |
|---|---|---|---|
| `end-carpet` | `plain`, `dusty`, `worn`, `stained`, `snowy` | carpet loop pile; dusty: dust flecks 30%; worn: a flattened lighter path; stained: a tan water ring; snowy: carpet half under powder snow #F2F5FA | Floors `EndCarpet`, `EndCarpetDusty`, `EndCarpetWorn`, `EndCarpetStained`, `EndCarpetSnow`. Random rotation alternates. Carpet-fibre cutting like Level 0's (`Breakdown`) |
| `end-runway` | `plain` | navy commercial carpet with small irregular squiggles and dots | Floor `EndRunway` |
| `end-concrete` | `plain`, `line-ns`, `line-we` | sealed grey concrete #8C8A84; a 4-px yellow safety line | Stockrooms: `EndConcrete`, `EndConcreteLine` |
| `end-wall` | `base`, `lower`, `ghost`, `cracked`, `band`, `upper`, `uppercracked`, `block` | base: lower paint with a 4-px dark cove at the bottom; ghost: a paler 18×12 rectangle and 4 screw holes; cracked: a branching 1-px crack #8A8478; band: yellow with darker 1-px edges; block: painted concrete block (stockrooms) | Wall stack in 3.3. `WallPattern.EndWall` (rim too), `EndStockWall` |
| `end-column` | `sage`, `slate`, `slat` | flat paint with a faint roller texture; slat: maple slatwall, grooves every 4 px | `WallPattern.EndColumn`, `EndColumnSlate`: slat at rel 1–2, paint above |
| `end-ceiling` | `plain`, `stained`, `missing` | 2×2 ft acoustic tile (a grid line at the edges and the middle), fissured dots; stained: a tan ring; missing: the black plenum #1C1A18 with T-bar edges | Missing tiles in Collapse departments, and 1% elsewhere |
| `end-troffer` | `on`, `lit`, `off`, `flicker` | white frame, prismatic lens with a 1-px diamond pattern; off: lens #B8BAB2 | on: `lightHsv [8, 2, 14]`; lit and flicker: glow only; flicker: block entity class `BackroomsFlickerLight`; registered in `flickerIds` |
| `end-soffit` | `plain`, `edge-{side}` | sides yellow-cream with the band; underside white | The bulkhead at rel 4 |
| `end-deck` | `plain`, `troffer` | top: carpet; sides: white fascia with a 2-px maple trim; bottom: acoustic tile (troffer: a lens) | The mezzanine deck at rel 6; `troffer` emits `[8, 2, 13]` |

### 4.3 Blocks: shapes (real 3D)

| Code | Variants | Shape (16-px units) | Behaviour, drops |
|---|---|---|---|
| `end-shelf` | kind `empty`, `books`, `dusty`, `endpanel`, `leaning`; part `lower`/`upper`; oriented | **Gondola**, 1×1 footprint, 2 tall. Side panels 1.5 thick at x 0–1.5 and 14.5–16. Centre spine 2 thick (slatwall texture). 3 shelves each side in `lower` (y 1, 6.5, 12) and 2 in `upper` (y 2, 7.5). Base kick 2 high, cornice 16×1.5×16 at upper y 13.5. `books`: 3–6 book boxes (2–3 × 10–12 × 7, spines in 6 dull colours) leaning on one shelf. `dusty`: dust on the shelves and a cobweb in one corner. `endpanel`: a full slatwall end panel. `leaning`: the same unit rotated 8° about its base | Collide; hardness like wood. Drops: 2 sticks, 25% a plank. `books` adds the book loot. `leaning` has class `BackroomsFragileShelf`: it breaks on entity collision or any hit, crash sound, `end-rubble` left behind |
| `end-tallshelf` | kind `empty`, `books`, `rail`; part `base`, `mid1`, `mid2`, `crown`; oriented | Library stack 1×1, 4 tall. Single-faced against a back panel. 2 shelves per block. Crown moulding. `rail`: a brass rail 1×1 along the front at y 14 of `crown` | 20% `game:shelf-normal-north`, else planks. Also the Turnaround wall |
| `end-wallshelf` | kind `empty`, `books`; part `lower`/`upper`; oriented | Single-faced wall shelving 2 tall, 10 deep, against the wall behind | Like `end-shelf` |
| `end-endcap` | kind `plain`, `tagged`; part `lower`/`upper` | **Tapered slatwall pyramid** (the photos' towers). Lower: a 14×14 base tapering to 11×11 at y 16. Upper: 11×11 tapering to 6×6, a cap 7×1×7. Slatwall on all four faces. `tagged`: a 3×2 yellow price sticker | Sticks, planks |
| `end-desk` | kind `straight`, `curveout`, `curvein`, `end`, `gate`; oriented | **Service desk**, 1 high. A front panel of maple 2 thick, toward the customer. Kick plate 0–2 in #2A2622. Countertop 16×1.5×10 at y 14.5. A raised transaction ledge 16×3×4 at y 15.5–18.5 on the front edge. A staff shelf at y 7. `curveout`/`curvein`: the arc built from 4 stepped segments (22.5° each). `end`: a rounded end. `gate`: a flip-up countertop hatch | Planks; desk loot (paper 30%, ink and quill 8%, Memory Juice 15%, catalogue card 20%) |
| `end-terminal` | state `off`, `on`, `static`, `party`, `dead`; oriented | **CRT computer** on the desk top. Case 12×3×11 at y 0–3. Monitor body 10×9×9 at y 3–12, set back 2. Screen 8×6 inset 0.5 on the front (separate face, glow). Keyboard 11×1×4 in front. A cable box hanging off the back. Screens: off = black glass; on = "THE END" in white 5-px pixel letters on black (glow 220); static = grey noise (glow 140); party = "=)" white on black (glow 220); dead = black with a faint crack | Block entity `BackroomsEndTerminal`. `ambientSound: end/crtbuzz`, range 10 (off state only). `on`/`party`: `lightHsv [0, 0, 4]`. Indestructible (Protection). Help: "Turn on" |
| `end-furniture` | kind `table`, `lamptable`, `chair`, `wrapped`, `armchair`, `carrel`, `displaytable`, `magrack`; oriented | table: top 16×1.5×16 at y 12.5, 4 legs 1.5². lamptable: the table plus a **banker's lamp** (brass stem 1×5, a 6×2.5×3 green glass shade #2E7A4E glowing on its underside). chair: maple frame, teal seat #3E6E6A, slatted back to y 17. wrapped: the chair inside a translucent wrap box (#E8ECEE, alpha 110) with 2 tape strips. armchair: low, mustard #B8913A, arms. carrel: a desk with 3 panels to y 24. displaytable: low table at y 8 with 3 small book stands. magrack: sloped rack, 4 slanted shelves | Collide (not the magrack). Drops in 3.7. lamptable `lightHsv [8, 4, 10]` |
| `end-catalogue` | kind `shut`, `open`; oriented | **Card catalogue**, 15 high. 4×5 small drawers, each with a brass pull (1×1×0.5) and a label frame. `open`: one drawer pulled out 6 | 1–2 `end-cataloguecard`, 1 paper |
| `end-stock` | kind `pallet`, `trolley`, `ladderwrapped`, `kit`; oriented | pallet: a wooden pallet 16×2×16 with a wrapped stack of boxes to y 20 (translucent wrap over cardboard). trolley: a 3-shelf **book cart** on 4 castors, sloped shelves. ladderwrapped: a step ladder in plastic, leaning. kit: flat-pack shelving boxes on a pallet | pallet: planks + 1 supply-box roll. trolley: sticks, a metal bracket. ladderwrapped: 2 vanilla ladders. kit: planks 4, nails 1 |
| `end-escalator` | part `step`, `top`, `bottom`; oriented | **Dead escalator**, 1 wide. Steel steps with grooved treads (a 1-px rib texture), a comb plate at top and bottom, a balustrade each side (brushed steel skirt 1 thick, black handrail 1.5² on top at y 16+). Steps rise 1 per block, so it climbs like stairs | Collision as stairs. Indestructible |
| `end-railing` | oriented | Mezzanine railing: steel posts 1.5² every 8 px, a glass panel (pale blue, alpha 70), a handrail 2×1.5 at y 15 | Collide (full height) |
| `end-pendant` | — | Drum pendant: a rod 1×12 from the top, a drum 9×4×9 #2A2A2A with a glowing underside | `lightHsv [8, 2, 15]` |
| `end-ladder` | kind `rolling`, `wall`; part `lower`/`upper` (rolling); oriented | rolling: a **library ladder** leaning on a tall stack (maple rails 1.5×1.5, rungs every 4, a brass hook at the top on the rail, castors at the foot). wall: a steel ladder to a vent, 1 tall per block | Climbable (`climbable: true`). rolling drops 2–3 vanilla ladders |
| `end-letter` | letter `t`, `h`, `e`, `n`, `d`, `i`, `s`, `a`, `r`, `blank`; oriented | **Bronze metal letters** on the face of a soffit or wall: each block carries one letter 10 px tall, strokes 2 px wide, standing 1.5 px proud on standoffs, centred, on a transparent plate. The block also renders the soffit or wall face behind it (two shape families: `soffit` and `wall`) | Indestructible. THE END = T H E _ E N D across 7 tiles; THE END IS NEAR across 15 |
| `end-poster` | kind `yellow`, `pink`, `green`, `notice`; oriented | Wall decorations (`Decor`) 0.3 thick. yellow: THE END in rows of black bold text ×6, like the render. pink and green: small cards with THE END and 3 lines of scribble. notice: a white sheet "THE END — ALL FIXTURES, FURNITURE & EQUIPMENT" | Paper 50%. Also used on columns |
| `end-exitsign` | state `lit`, `dead`; oriented | A 3D **neon EXIT sign** over a door: a box 12×5×2 (black case), the letters EXIT glowing red (#FF3A28) on its face, two hanger rods | lit `lightHsv [0, 7, 8]`. Indestructible. Also used over Level 1's EXIT doors into The End |
| `end-exitdoor` | part `lower`/`upper` | `door_block` style: grey steel #8E9196, a push bar at y 15–17 on the lower, a small wire-glass window on the upper | `threshold("endexit")`. Indestructible. Also used in Level 1, the Hub (if they agree) and Level ! |
| `end-staffdoor` | part `lower`/`upper` | Maple-veneer door with a brushed steel kick plate; on the upper, a plate reading EMPLOYEES ONLY | `threshold("locked")` |
| `end-vent` | oriented | A wall vent grille, 12×8, 6 louvres angled 30°, recessed 2, dark behind | `threshold("endvent")`. Indestructible |
| `end-frame` | part `lower`/`upper`; oriented | **Free-standing wooden doorframe** (Level 4). Jambs 2×16×4 each side, a head 16×2×4, aged oak #7A5A3A. Inside, a "membrane": a 12×32 plane, glow 60, alpha 50, wavering texture (3 alternates) | The threshold is in its tile (`Unders.EndFrame`). Indestructible. Ambient: muffled room tone |
| `end-storedoor` | part `lower`/`upper` | Glass shop door for Level 11's bookstore: an aluminium frame, glass with a yellow THE END IS NEAR poster taped inside, a pull handle | `threshold("endbookstore")` |
| `end-storewindow` | oriented | Level 11 storefront glass papered with yellow and pink closing-down posters | — |
| `end-rubble` | kind `shelf`, `ceiling` | shelf: a heap of 6 boards at angles, a fallen side panel. ceiling: 3 broken acoustic tiles and a bent T-bar | Walk-through: no. Sticks |
| `end-tree` | part `trunk`, `top` | Snowfield **bare tree**: trunk 4×16×4 with bark #5E554C and snow on the up-facing ledges. top: 6 bare branches 1–1.5 thick reaching out to the block edge, snow tufts #F4F6FA | Sticks, firewood |
| `end-hangsign` | oriented | INFORMATION: a 14×5×1 sign hung on 2 chains over a desk (white text on navy) | Overhead decoration |

### 4.4 Items

| Code | What | Notes |
|---|---|---|
| `end-cataloguecard` | A cream index card #F1E8CF with a red top rule and typed lines. Item texture 32×32 | Class `BackroomsWandererNote`, variant `kind: endexit`. Reading it marks the nearest way out of The End. Stack 16 |
| `end-memoryjuice` | A small unlabelled glass bottle of cloudy amber liquid, a cork | Food, `NoNutrition`, satiety 20; class `BackroomsMemoryJuice` (+0.2 stability, a 30 s warm "home" fog on the client). Stack 8 |
| Found books | Not new items | Vanilla `book-normal-*` with attributes (3.7). Texts kept in `tools/gen_end.py` as `END_BOOKS` and written into the loot JSON, or into a `config/endbooks.json` the code reads |

### 4.5 Sounds (`tools/gen_level_sounds.py`, an `end` section; mono OGG, 44.1 kHz)

| File | Length | Character |
|---|---|---|
| `end/roomtone` | 20 s loop | Near silence: a 120 Hz ballast tick at −42 dB, a 7–9 kHz whisper of hiss, nothing else. Loops seamlessly |
| `end/crtbuzz` | 4 s loop | A CRT's 15.7 kHz flyback whine (pitched down to 11 kHz so it is audible), plus a 60 Hz hum and its harmonics. Loud up close |
| `end/crton` | 1.2 s | A degauss thunk and a rising whine |
| `end/crtstatic` | 2.5 s | White-noise static band-passed 1–6 kHz, fading out, with a click at the end |
| `end/shelfcreak` | 1.5 s | Particle board flexing: low creaks, a tick |
| `end/bookfall` | 0.8 s | One hardback on carpet: a soft thump, a riffle |
| `end/chairscrape` | 1.2 s | A chair dragged a short way on carpet |
| `end/pageturn` | 0.6 s | One page turning |
| `end/shelfcrash` | 2 s | A gondola shelf falling: a crack, a crash, boards clattering |
| `end/breaker` | 0.8 s | A large breaker clunk, then the ballast tick stopping |
| `end/distortion` | 5 s | A low rumble from 30 Hz rising, shelves rattling, a pressure swell, then a sudden drop to silence |
| `end/snowwind` | 12 s loop | Wind over open snow, soft gusts |
| `end/echostep` | 1.5 s | 2–3 soft footsteps on carpet, a little behind, slightly delayed |
| `end/turnaround` | 0.7 s | A heavy bookcase set down on carpet (played only where you cannot hear it) |

### 4.6 Lang (`LANG`, English)

| Key | Text |
|---|---|
| `level-16` | The End |
| `levelhint-16` | You found the exit. Didn't you? |
| `levelname-end` | The End |
| `level-161` | The End: a fake reality |
| `levelhint-161` | This is not where you think it is. |
| `endexit-locked` | The EXIT sign glows. The door does not open. |
| `endframe` | You step through the doorway. When you look back, there is nothing there. |
| `endexit-arrive` | You push the bar, and the door swings shut behind you on a library that goes on forever. |
| `endbookstore` | The bell over the door doesn't ring. Inside, the shelves go back much further than the shop. |
| `endvent` | You crawl into the dark. The vent ends in open air, and you are falling. |
| `endterminal-on` | The screen flickers on with a low buzz. In white letters: THE END. Then static, and nothing. |
| `endterminal-marked` | Before it dies, the screen shows a plan of the floor. You remember where the doors were. |
| `endterminal-dead` | The screen stays dark. It will not turn on again. |
| `endterminal-party` | The screen flickers on. It does not say THE END. It says =) |
| `endparty-taken` | Hands take you by the arms. Someone is laughing. "Don't leave yet, friend! =)" |
| `enddistortion` | The floor shakes. For a moment you are somewhere else. |
| `enddistortion-through` | You fall forward into the wall, and through it. |
| `endfake-door` | The door opens onto somewhere real. |
| `endfake-shut` | The door is painted shut. It was never a door. |
| `endjunkie-nojuice` | "Got any juice? No? Then what are you doing here." |
| `endjunkie-greet` | "Oh, you have some. Sit down. Stay a while." |
| `waypoint-note-endexit` | A way out of The End (from a catalogue card) |
| `note-endexit-1` | The card is typed: EXIT, {0}, about {1} paces. Someone has underlined it twice. |
| `note-endexit-2` | A catalogue card, filed under E: "Exit: see {0}, {1} paces." |
| `note-endexit-3` | Someone has written on the back of the card: "{0}. {1} paces. It opened for me." |
| `item-end-cataloguecard` | Catalogue Card |
| `itemdesc-end-cataloguecard` | From The End's card catalogue. Read it to mark the nearest way out on your map. |
| `item-end-memoryjuice` | Memory Juice |
| `itemdesc-end-memoryjuice` | An unlabelled bottle of something cloudy and amber. For a while after you drink it, everything feels like home. The Junkies of The End will trade with anyone who carries some. |
| `blockhelp-endterminal` | Turn on |
| Block names | `end-shelf-*` Empty Shelving, `end-shelf-books-*` Shelving with a Few Books, `end-shelf-leaning-*` Leaning Shelving, `end-tallshelf-*` Library Stack, `end-wallshelf-*` Wall Shelving, `end-endcap-*` Slatwall Display Tower, `end-desk-*` Service Desk, `end-terminal-*` Old Computer, `end-furniture-table-*` Study Table, `-lamptable-` Study Table with Lamp, `-chair-` Library Chair, `-wrapped-` Chair in Plastic, `-armchair-` Armchair, `-carrel-` Study Carrel, `-displaytable-` Display Table, `-magrack-` Magazine Rack, `end-catalogue-*` Card Catalogue, `end-stock-pallet-*` Wrapped Stock, `-trolley-` Book Trolley, `-ladderwrapped-` Ladder in Plastic, `-kit-` Shelving Kit, `end-escalator-*` Escalator (Stopped), `end-railing-*` Mezzanine Railing, `end-pendant` Pendant Lamp, `end-ladder-rolling-*` Library Ladder, `end-ladder-wall-*` Steel Ladder, `end-letter-*` Metal Letter, `end-poster-*` Poster, `end-exitsign-*` EXIT Sign, `end-exitdoor-*` EXIT Door, `end-staffdoor-*` Staff Door, `end-vent-*` Vent, `end-frame-*` Doorway, `end-storedoor-*` Shop Door, `end-storewindow-*` Shop Window, `end-rubble-*` Collapsed Shelving / Fallen Ceiling, `end-tree-*` Bare Tree, `end-hangsign-*` INFORMATION Sign, `end-carpet-*` Library Carpet, `end-runway-*` Patterned Carpet, `end-concrete-*` Stockroom Concrete, `end-wall-*` Painted Wall, `end-column-*` Column, `end-ceiling-*` Ceiling Tile, `end-troffer-*` Fluorescent Light, `end-soffit-*` Soffit, `end-deck-*` Mezzanine Floor |

The found books' 12 texts are written by the asset agent in the voice of the mod's notes. Each is 60–200 words, with titles:
1. Distortions (after Fandom)
2. The Long Aisle
3. Visitor's Log
4. THE END IS NEAR (one line copied over and over)
5. Catalogue: Section E
6. Which Doors Opened
7. Juice
8. Home
9. Don't Turn It On
10. =)
11. Shelf 4,812
12. Isolation

---

## 5. Code plan

### 5.1 Files the level owns

- **`src/Worldgen/WorldLayout.LevelEnd.cs`** (replaces the stub):
  - **The region.** `EndRadius` 64, `EndArrivalCell` (radius 0.35), `IsEndArrivalSpot`: carpet, lit, Zone 0 or 1, not `EndLoop`, not under a deck edge.
  - **Edges.** `EndEdge` gives `WallPattern.EndWall` edges with every tile open: the plans are laid over them, as Level 37 does.
  - **Plans.** `BuildLevelEnd` copies department plans and the runways into the cell; the rim cells are wall.
  - **Runways.** `RunwayAt(gx, gz)`, a wandering band computed from coordinates (like `GalleryAt`), and jams per stretch.
  - **Departments.** `EndPlan(di, dj)` through `PlanCache<Tile[]>(24, PlanEndDepartment)`, with one planner per kind; `CentralHallPlan()`.
  - **Fake realities.** `FakeRealityAt(di, dj)` (kind or none) and the blend function.
  - **Loop aisles.** `LoopAisle(gx, gz)` returns the axis, the aisle's start and its length for the loop and the Turnaround.
  - **Distortions.** `DistortionScene(di, dj)`, deterministic.
  - **Searches.** `NearestEndExit(x, z, radius)` (unlocked EXIT doors, working fake-reality doors, vents), for terminals and catalogue cards.
  - **The rest of the stub's hooks:** `EndWalkThrough` (rubble no; snow-layer floor yes), `EndTemperature`, `EndStability` (section 3.6), `EndArrivalHeight` (stand).
- **`src/Worldgen/WorldGenerator.End.cs`:**
  - `InitEnd` looks up the ids.
  - `LevelEndBlock` builds the column stacks of 3.3. Its branches: walls (base, lower, band, upper, cracked, ghost), columns, soffits and letters, troffers by `Ceiling`, decks and railings, tall stacks (`Stack` = part), escalator steps, the desk with a terminal on top, doors and EXIT signs, and fake-reality cores using the other levels' block ids (Level 0 wallpaper and troffers, Level 4 office, Level 5 hotel, Level 9 interiors, vanilla snow layers).
  - Props are registered in `PropTable` for 360–399.
- **`src/Regions/EndSystem.cs`** (server, with a small client part for the fog and camera shake):
  - terminals: block entity `BackroomsEndTerminal` (state saved), map marks, the "=)" passage;
  - the loop and the Turnaround (placing and removing the bookcase, out-of-sight checks with `Senses.ClearLine`);
  - distortions: a per-player schedule, a packet to the client, and the noclip check (horizontal collision against a wall);
  - lights-out (reusing the Flickering darkness message to the client);
  - the isolation drain;
  - fragile shelves (`BlockBehaviorFragileShelf`);
  - the Junkies' gate (`EntityBehaviorJunkie`);
  - Memory Juice (`ItemMemoryJuice`).
- **`tools/gen_end.py`:** everything in section 4, called from `gen_detail.py` as gen_pool and gen_motion are (through the lock).

### 5.2 Hooks in shared files

Small local `Edit`s, inside The End's reserved lines or blocks only.

| File | Change |
|---|---|
| `Tiles.cs` | **`WallPattern`** (96–111): `EndWall = 96`, `EndColumn`, `EndColumnSlate`, `EndStockWall`, `EndExit` (door), `EndStaff` (door), `EndStoreDoor`. <br>**`FloorKind`** (132–147): `EndCarpet = 132`, `EndCarpetDusty`, `EndCarpetWorn`, `EndCarpetStained`, `EndCarpetSnow`, `EndRunway`, `EndConcrete`, `EndConcreteLine`. <br>**`Overheads`** (60–69): `EndSoffit = 60`, `EndSoffitLetter`, `EndPendant`, `EndHangSign`, `EndMissingTile`, `EndDeck`, `EndDeckEdge`. <br>**`Unders`** (60–69): `EndLoop = 60`, `EndFakeDoor`, `EndFrame`, `EndExitL1`, `EndBookstore`, `EndVentWall`. <br>**`Props`** (360–399): `EndShelf = 360`, `EndTallShelf`, `EndWallShelf`, `EndEndcap`, `EndDesk`, `EndFurniture`, `EndCatalogue`, `EndStock`, `EndEscalator`, `EndRubble`, `EndTree`, `EndLadder`, `EndFrame`, `EndRailing`. <br>**`Decor`** (196–207): `EndPoster = 196` (4 kinds, 196–199), `EndGhost = 200`, `EndCrack`, `EndLetter`, `EndExitSign`, `EndVent`, `EndStaffSign`, `EndClock`. <br>**Tile fields used by The End:** `Height` = ceiling height; `Zone` 0 library, 1 central hall, 2 stockroom, 3 collapse, 4 fake blend, 5 fake core; `Detail` = fake kind or department kind; `Stack` = prop kind or part, letter index; `Pier` = facing |
| `WorldGeometry.cs` | `EndDrop = 6`; The End's `BandBottomFor` line `FloorFor(TheEnd) - 24` |
| `WorldLayout.cs` | `LevelTemperatures[16] = 19f`; nothing else (the scaffold did the rest) |
| `WorldLayout.Entities.cs` | `IsSanctuary`: the central hall, Home cores and wanderer sites; `Danger.OfLevel(16) = 0.4` |
| `WorldLayout.Loot.cs` | Never picked over in The End |
| `WorldLayout.Notes.cs` | `NearestThreshold` counts End exits; `NearestRefuge` counts the central hall and Junkie sites |
| `Map/WandererNote.cs` | `case "endexit"` → `layout.NearestEndExit` |
| `ThresholdNetwork.cs` | Predicates `EndExitDoor`, `EndStoreDoor`. <br>`Walked`: Level 4 `Unders.EndFrame` (one-way to 16, message `endframe`). <br>`Used`: `endexit` (from 1, 14, 17: two-way to 16 beside `EndExitDoor`; from 16: locked 2 in 3 unless claimed, else by hash to 1/17/11/4/5 with partners), `endbookstore` (11 ↔ 16), `endvent` (16 → 13, two-way), `fakedoor` (16 → 0/4/5/9 by `Detail`). <br>`EndTerminal((x, z))` one-way to 15; `EndDistortion((di, dj), scene)` two-way. Salts `SaltDoor + 0x1600…` |
| `ThresholdSystem.cs` | A public `Carry(IServerPlayer, Passage, bool twoWay)` wrapping `Go` + `Take`, for `EndSystem` (terminal, distortion); `kind == "endterminal"` routed to `EndSystem` like `thronedoor` |
| `AtmosphereSystem.cs` | `Levels[16]`; fake-reality and distortion overrides; End room tone and snow wind; lights-out darkness; distortion shake (`capi.World.AddCameraShake`) |
| `Entities/Roster.cs` | `[16]`: Smiler Glimpse (dark, Collapse only), Partygoer if present; sounds `BookFall`, `ShelfCreak`, `ChairScrape`, `PageTurn` |
| `Entities/WandererSystem.cs`, `WorldLayout.*` | `WandererSite` returns Home camps in The End (entity `wanderer-junkie`) |
| `Salvage/Protection.cs` | Roof height for 16: 13. Terminals, letters, doors, vents, frames and escalators fixed |
| `Salvage/Breakdown.cs` | `EndWall` → drywall rules; columns, concrete → rubble; carpet → fibres; ceiling tiles → as Level 0's |
| `Map/MapColors.cs`, `BackroomsMapLayer.cs` | Colours (carpet #646B5F, runway #2E3968, shelving #CD9A55, walls #E8DFC2, desk #B98A4E); sampling at The End's floor + 2 |
| `Map/MapMarks.cs` | "The End", and "The End (a fake reality)" |
| `WorldLayout.Level1.cs` | 1 in 25 locked hall doors become EXIT doors into The End (salt 0x1610) |
| `WorldLayout.Level4.cs` | The free-standing doorframe, 1 open-plan cell in 60 (salt 0x1611) |
| `WorldLayout.Level11.cs` | `CityKind.Bookstore`, about 1 midtown lot in 120 (salt 0x1612) |
| Level ! and Hub files | Their owners place the doors; The End only provides the `end-exitdoor` block and the `endexit` kind |
| `tools/gen_guide.py`, `README.md` | Phase 3 |

### 5.3 Harness (`tools/mapgen`)

- **`end [x z]`:** renders a 512×512 top-down PNG (floors, shelving, desks, letters, runways, fake realities).
- **`endstats`:** shares of each department kind; floor lit / dark; books per km²; EXIT doors per km² (locked and open); fake realities per km²; the central hall present; runway jams.
- **`endloop`:** for every Long Aisle in a 4 km square, checks tiles at `s` and `s + 32` are identical along the aisle and its 3 rows either side. Also checks that every 32-block segment has a cross-gap.
- **Existing modes:**
  - `regions`: 60/60 End arrivals, none in a pocket;
  - `links`: every new threshold leads somewhere and back, and survives save and load;
  - `validatelevel 16`: no pockets;
  - a before/after layout hash: Levels 0–13 byte-identical except Level 1, 4 and 11 where the entrances stand.

### 5.4 Verification

1. Harness: the modes above, plus timing (a department plan in under 2 ms).
2. Headless server on port **42476** with its own data path:
   - `/backrooms goto end`;
   - `/backrooms dump` round the central hall, an atrium, a Long Aisle and a fake reality;
   - render with the scratchpad `gfx/` tools.
3. Threshold round trips by console: Level 1 EXIT door ↔ End; End EXIT door → each target; vent → 94; terminal (normal and "=)").
4. Previews: `tools/preview_shapes.py` for every shape; side-by-side against the two photos.
5. **The loop and the Turnaround need a client** (teleport smoothness): test in phase D before polishing anything else there.

---

## 6. Survival role

| | The End |
|---|---|
| Teaches | Reading the network: maps, notes, which doors open |
| Gives | A home's furniture (chairs, tables, ladders, shelves), paper, ink and books to write your own maps, catalogue cards and terminals that show the ways out, shortcuts to Level 1, the Hub, Level 11 and Level 94 |
| Takes | Food (there is none), stability (isolation), time (loops, locked doors), and the "=)" terminals |
| Fits the loop | An expedition you plan for: bring food, mark your way. Never a home: no food, and the anchor rule still wakes you in Level 0 |

---

## 7. Phases

| Phase | Work | Verify |
|---|---|---|
| A. The library | Region (radius 64, drop 6, band), runways, the department kinds except fake realities and Long Aisles, the central hall, all structure and library assets, light, fog, room tone, temperature, stability, loot, protection, map | `end` renders; `endstats` shares; arrivals; layout hash |
| B. Ways in and out | Level 1 EXIT doors, Level 4 doorframe, Level 11 bookstore, End EXIT doors (locked or targets), vent → 94, terminals (`BackroomsEndTerminal`, map marks, "=)" → Fun), catalogue cards, network hooks, agreed links with `run`, `hub`, `fun` | `links`; headless round trips |
| C. Fake realities | Blend and cores (Lobby, Office, Hotel, House, Snowfield, Home), their doors, the Junkies, Memory Juice, found books | Renders of each; trades gated |
| D. The uncanny | Long Aisles, loop and Turnaround, distortions (fog, shake, scenes, noclip exits), lights-out, isolation drain, echo steps, fragile shelves | `endloop`; **client test of the loop teleport** |
| E. Words | Handbook page, Ways Between Levels rows, README, lang | Handbook renders; tables match the code |

A to C make The End complete and playable; D is the lore's strangeness, which can follow.

---

## 8. Risks

- **The loop's teleport may show.** `TeleportToDouble` within loaded chunks is near-instant, but the client may hitch.
  - **Fallback:** no teleport. The Long Aisle stays exactly periodic, so it still *reads* as a loop, and the Turnaround places its bookcase after 96 blocks of straight walking instead.
- **Placing and removing blocks at runtime** (the Turnaround) must never trap anyone. The bookcase goes only on a Long Aisle tile with cross-gaps either side of the player (always true by construction), never on a threshold. It is removed by a sweep if the server restarts with one standing (saved list).
- **Distortion noclip** depends on detecting someone pressing into a wall. Use horizontal collision (`entity.CollidedHorizontally`) plus the facing tile being wall-like, for 0.5 s.
- **Light cost.** The troffers are dense. Keep emitters to 1 in 3, as Level 0 does, and the band at 40.
- **Pre-written books** depend on vanilla `ItemBook` attributes. Verify by decompiling; the fallback is giving them in code.
- **Cross-level links** depend on three other agents (`run`, `hub`, `fun`). The End's own EXIT doors work without them: those targets fall back to Level 1 if the Hub has no door predicate yet.

---

## 9. Decisions for the user

1. **Which page is canon.** Wikidot Level 601 is primary (the trap, the loop, fake realities, terminals, Partygoers, the Junkies). Fandom's The End (the 2019 original by Skivy123, now Class 3) supplies the look, the decay, the distortions and its entrances and exits. **Recommended:** as described.
2. **Placement and size.** A noclip region to the north-west, radius 64 cells (≈ 2 km), floor 6 below, a two-storey atrium. **Recommended:** yes.
3. **The loop and the Turnaround.** A real loop (a teleport back 64 blocks in an exactly repeating aisle) and a bookcase that appears behind you. **Recommended:** yes, in phase D, tested in a client first; fallback periodicity only.
4. **Fake realities.** **Recommended:** all six (Lobby, Office, Hotel, House, Snowfield, Home); exits in the first four, 3 in 5 of them working.
5. **Distortions with noclip exits.** **Recommended:** yes (fog, shake and sound, and walking into a wall during one takes you to its scene; each department's scene is fixed).
6. **Terminals.** One use each, marking the nearest ways out on your map; 1 in 4 is a "=)" terminal that takes you one-way to Level Fun. **Recommended:** yes.
7. **Entities.** No new one; Partygoers borrowed from Level Fun if built, Smiler glimpses in the dark. ETB's Scratcher is on no wiki. **Recommended:** no Scratcher.
8. **Food.** None but Almond Water coolers in the stockrooms. **Recommended:** yes ("Devoid of All Life"; it is a trap).
9. **The Junkies and Memory Juice.** **Recommended:** include: 2 traders in each Home fake reality who trade only with someone carrying Memory Juice (a new drink found in desks). Alternative: an ordinary wanderer site, no Memory Juice.
10. **The Level 4 doorframe is one-way.** The user's rule says walked = two-way, but canon says the doorway vanishes behind you. **Recommended:** one-way ("taken"); the alternative is two-way with a thin spot.
11. **Not perceiving other wanderers** (Wikidot). **Recommended:** skip (as Level 37's isolation was skipped).
12. **Random noclip into The End** (Wikidot, rare). **Recommended:** skip; it would break "every threshold always leads to the same place".
13. **Level ! → The End**, through the door at the end of the hallway (Escape the Backrooms). **Recommended:** yes if the `run` plan has no stronger canon for that door; otherwise one rare special false exit.
14. **The Hub ↔ The End.** **Recommended:** a Hub door ↔ an End EXIT door, and 25% of End EXIT doors lead to the Hub.
15. **Furniture as vanilla blocks.** Chairs, tables, ladders and shelves drop as vanilla blocks you can place at home. **Recommended:** yes.
16. **Order of work.** **Recommended:** A → B → C → D, with D's loop tested in a client before the rest of D.

---

## 10. Handbook text (for `tools/gen_guide.py`)

**The Levels: The End**

A library that goes on forever, and the cruellest trap in the Backrooms: it looks like the way out. Empty maple shelving under fluorescent lights, slatwall towers, a curved desk with an old computer, and over it, in bronze letters, THE END. It lies far to the north-west; nobody walks there.

- **Getting in:**
  - a locked door under a glowing EXIT sign in Level 1's halls;
  - a lone wooden doorway standing in an office in Level 4 (it is gone once you are through);
  - a closed-down bookstore in the city;
  - doors elsewhere that promise an exit.
- **Getting out is the hard part:**
  - Doors marked EXIT stand in the back rooms and at the corners of the central hall. Two in three never open. The rest always lead to the same place: Level 1, the Hub, the city, the Office or the Hotel, and back again.
  - Out in the library are *fake realities*: places you know (the Lobby, an office, a hotel corridor, a house) that the shelves blend into. Some of their doors are real.
  - A vent at the top of a ladder in some stockrooms drops you into Level 94.
- **The computers** buzz until you turn one on. It shows the name of the place, then dies for good, but before it goes you will remember where the nearest doors were. Not every screen says THE END. If one says =), you are not staying.
- **Catalogue cards** from the card catalogues mark the nearest way out on your map.
- **There is no food.** Almond Water comes from the coolers in the stockrooms, nothing else.
- **The longer you stay, the less you are sure of yourself** (stability drains after two hours). It is kindest at the middle, under THE END IS NEAR.
- **The library is wrong:**
  - Some aisles never end, and if you turn round in one, there is a wall: leave by a gap at the side.
  - Now and then the floor shakes and for a moment you are somewhere else; walk into a wall then, and you will be.
  - The lights go out for a minute or two. Carry a light.
- **What is here:** chairs, tables, ladders and shelving to furnish a home, paper and ink, and now and then a book (most of them blank; some are not). In the Home fake realities live the Junkies, who trade only with someone carrying Memory Juice.

**Ways Between Levels** (rows):

| From | Threshold | To | Way back |
|---|---|---|---|
| Level 1 | A locked hall door under a glowing EXIT sign | The End | The EXIT door you arrive beside |
| Level 4 | Walking through a lone wooden doorway | The End | None |
| Level 11 | The door of a closed-down bookstore | The End | The EXIT door you arrive beside |
| The End | An EXIT door (most are locked) | Level 1, the Hub, Level 11, Level 4 or Level 5 | That door, or a thin spot |
| The End | A real door in a fake reality | Level 0, 4, 5 or 9 | That door, or a thin spot |
| The End | A vent up a ladder in a stockroom | Level 94 (from the sky) | Thin spot |
| The End | Walking into a wall during a distortion | The place it showed | Thin spot |
| The End | A computer that says =) | Level Fun | None |

## Manifest changes (phase 2)

Written by the End **code** agent for the End **asset** agent: these are the exact block and item codes, block classes
and attributes the C# looks up. Variant groups are joined with `-` in the order given. Where this list and section 4
differ, this list wins.

### Block codes the generator places (all `backrooms:`)

| Code | Variants (in code order) |
|---|---|
| `end-carpet-{v}` | v = plain, dusty, worn, stained, snowy |
| `end-runway-plain` | |
| `end-concrete-{v}` | plain, line-ns, line-we |
| `end-wall-{v}` | base, lower, ghost, cracked, band, upper, uppercracked, block |
| `end-column-{v}` | sage, slate, slat |
| `end-ceiling-{v}` | plain, stained, missing |
| `end-troffer-{v}` | on, lit, off, flicker |
| `end-soffit-plain` | (the `edge-{side}` variants are not used) |
| `end-deck-{v}` | plain, troffer |
| `end-shelf-{kind}-{part}-{side}` | kind = empty, books, dusty, endpanel, leaning; part = lower, upper |
| `end-tallshelf-{kind}-{part}-{side}` | kind = empty, books, rail; part = base, mid1, mid2, crown |
| `end-wallshelf-{kind}-{part}-{side}` | kind = empty, books; part = lower, upper |
| `end-endcap-{kind}-{part}` | kind = plain, tagged; part = lower, upper (not oriented) |
| `end-desk-{kind}-{side}` | kind = straight, curveout, curvein, end, gate |
| `end-terminal-{state}-{side}` | state = off, on, static, party, dead |
| `end-furniture-{kind}-{side}` | kind = table, lamptable, chair, wrapped, armchair, carrel, displaytable, magrack |
| `end-catalogue-{kind}-{side}` | kind = shut, open |
| `end-stock-{kind}-{side}` | kind = pallet, trolley, ladderwrapped, kit |
| `end-escalator-{part}-{side}` | part = step, top, bottom; side = the way the escalator climbs (up toward that side) |
| `end-railing-{side}` | side = the side of the block the railing stands on (the drop is beyond it) |
| `end-pendant` | |
| `end-ladder-{kind}-{part}-{side}` | kind = rolling, wall; part = lower, upper. The wall ladder uses `lower` only, one per block of height. Side = the side the ladder stands against |
| `end-letter-{family}-{letter}-{side}` | **new group** family = soffit, wall (the block is the soffit or the wall with the letter on its `side` face); letter = t, h, e, n, d, i, s, a, r, blank |
| `end-poster-{kind}-{side}` | kind = yellow, pink, green, notice. A **full wall block** (`end-wall-lower` look) with the poster on its `side` face, not a thin plane: the generator puts it in place of the wall block at rel 2 |
| `end-exitsign-{state}-{side}` | state = lit, dead. A full wall block (`end-wall-band` look) with the sign on its `side` face, at rel 3 over a door |
| `end-exitdoor-{part}` | part = lower, upper (`door_block` style) |
| `end-staffdoor-{part}` | lower, upper |
| `end-storedoor-{part}` | lower, upper |
| `end-vent-{side}` | a full wall block (`end-wall-block` look) with the grille on its `side` face, at rel 3 |
| `end-frame-{part}-{side}` | part = lower, upper |
| `end-storewindow-{side}` | |
| `end-rubble-{kind}` | kind = shelf, ceiling |
| `end-tree-{part}` | part = trunk, top |
| `end-hangsign-{side}` | |

Also used, from the game: `game:snowlayer-1` (on the Snowfield's carpet).

### Classes and attributes the code registers or reads

| Block or item | What to put in its JSON |
|---|---|
| `end-terminal-*` | `behaviors: [{ name: "BackroomsEndTerminal" }]` (right-click turns it on; `EndSystem` swaps the state variant). Unbreakable (`resistance` very high, no drops). `off` keeps its `ambientSound` |
| `end-exitdoor-*` | `behaviors: threshold("endexit")` |
| `end-storedoor-*` | `threshold("endbookstore")` |
| `end-vent-*` | `threshold("endvent")` |
| `end-staffdoor-*` | `threshold("locked")` |
| `end-shelf-leaning-*` | `class: "BackroomsFragileShelf"` (a block class: it comes down when walked into or struck; `resistance` low) |
| `end-troffer-flicker` | `entityClass: "BackroomsFlicker"`, `attributes: { offBlock: "backrooms:end-troffer-off" }` (as the Level 0 flicker light) |
| `end-cataloguecard` (item) | `class: "BackroomsCatalogueCard"` (no variants) |
| `end-memoryjuice` (item) | `class: "BackroomsMemoryJuice"`, plus `nutritionProps` as in section 4.4 |

Found books are given in code (`EndSystem`), not by block drops. Shelves of the `books` kind should still drop
1-3 `game:book-normal-*` as section 3.7 says; the code adds a written one now and then.

### More for the asset agent (code agent, phase 2, second note)

- `end-frame-*`: **no collision** (walked through; the threshold is the tile it stands on, in Level 4). Selection box only.
- `end-escalator-step-*` and `-top-*`: collision as a stair (a lower half block plus the back half of the upper half), so
  you walk up it without jumping; the generator stacks them one block higher per tile (`Tile.Stair` 1-5) with
  `end-wall-block` under each.
- Lang keys the code uses (`backrooms:` domain), with the English to give them:

| Key | English |
|---|---|
| `level-16` | The End |
| `levelhint-16` | You found the exit. Didn't you? |
| `levelname-16` | The End |
| `level-1601` | The End: a fake reality |
| `levelhint-1601` | This is not where you think it is. |
| `endframe` | You step through the doorway. When you look back, there is nothing there. |
| `endexit-arrive` | You push the bar, and the door swings shut behind you on a library that goes on forever. |
| `endexit-out` | The door opens. Somewhere else is on the other side. |
| `endbookstore` | The bell over the door doesn't ring. Inside, the shelves go back much further than the shop. |
| `endvent` | You crawl into the dark. The vent ends in open air, and you are falling. |
| `endfake-door` | The door opens onto somewhere real. |
| `endparty-taken` | Hands take you by the arms. Someone is laughing. "Don't leave yet, friend! =)" |
| `enddistortion` | The floor shakes. For a moment you are somewhere else. |
| `enddistortion-through` | You fall forward into the wall, and through it. |
| `endterminal-on` | The screen flickers on with a low buzz. In white letters: THE END. Then static, and nothing. |
| `endterminal-marked` | Before it dies, the screen shows a plan of the floor. You remember where the doors were. |
| `endterminal-dead` | The screen stays dark. It will not turn on again. |
| `endterminal-party` | The screen flickers on. It does not say THE END. It says =) |
| `endjunkie-nojuice` | "Got any juice? No? Then what are you doing here." |
| `endjunkie-greet` | "Oh, you have some. Sit down. Stay a while." |
| `waypoint-endterminal` | A way out of The End (from a computer) |
| `waypoint-note-endexit` | A way out of The End (from a catalogue card) |
| `note-endexit-1` | The card is typed: EXIT, {0}, about {1} paces. Someone has underlined it twice. |
| `note-endexit-2` | A catalogue card, filed under E: "Exit: see {0}, {1} paces." |
| `note-endexit-3` | Someone has written on the back of the card: "{0}. {1} paces. It opened for me." |
| `blockhelp-endterminal` | Turn on |

(`note-nothing`, `dir-*` and `door-locked` already exist.)

### Asset agent notes (phase 2, `tools/gen_end.py` built and run)

- Every code in the table above exists, with variant groups in the order given; `check()` in the generator confirms
  every shape, texture, sound and drop resolves (35 block types, 107 shapes, 2 item types, 14 sounds).
- `end-exitsign`'s first group is named `state` (lit, dead). `end-soffit` keeps its unused `edge-{side}` states.
- **Desk and terminal:** the desk's countertop runs 12.4 deep (to z 15.4 of the north-facing model) and the terminal
  sits behind the 3-high transaction ledge, its keyboard and mouse on the ledge. Place terminals on `straight` desks
  with the desk's facing (as the generator does).
- **Extra, optional:** `end-clock-{backing}-{side}` (backing = lower, upper, band, block, sage, slate, none): a wall
  clock stopped at a minute to midnight on that wall face (`none` = against the wall behind an air block). Unused.
- All sounds are in `sounds/ambient/end/` (roomtone, crtbuzz, crton, crtstatic, shelfcreak, bookfall, chairscrape,
  pageturn, shelfcrash, breaker, distortion, snowwind, echostep, turnaround); roomtone, crtbuzz and snowwind loop.
- Lang uses `levelname-16` (not `levelname-end`), `level-1601` / `levelhint-1601` for the fake realities, and adds
  `endexit-out` and `waypoint-endterminal`, which the code uses. The found books stay in `EndSystem.cs`.
- `end-catalogue` drops 1-2 `end-cataloguecard` and parchment by block drops; shelves of the `books` kind drop
  vanilla books by block drops.
- Done from the code agent's second note: `end-frame-*` has no collision (selection only); `end-escalator-top-*` is now
  the last step of the flight (stair collision, the comb plate and newels at its head); lang texts as listed there.

- `end-pendant`: **`lightHsv [8, 2, 20]`** (not 15). Checked in a headless dump: at 15 the atrium's void floor averaged
  light 4.7 under its 4-high stacks; the pendants now hang every 4 blocks at rel 9 under the 10-high ceiling.
