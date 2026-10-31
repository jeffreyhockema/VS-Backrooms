# Level 52 brief: The Greenfield Campus (Fandom)

Source: https://backrooms.fandom.com/wiki/Level_52 (WindXD rewrite; fetched as wikitext via api.php). Also read https://backrooms.fandom.com/wiki/Sanguine_Festivus (Entity 67, Partygoers). Wikidot's level-52 ("Destination Reached", a limestone cave, entrance from Plane #445) is NOT used: mention only. Cleaned fetch copy: scratchpad/lore/fandom-Level_52.clean.txt.

## 1. Lore summary
Class 1e Environmental, **Safe**, Stable, "Minimal Non-Entity Hazards". "a vast school campus of buildings nestled in verdant plains housing a university... and several collections of apartments." Euclidean, "easily navigable and convenient to map". "Each entrant will land in the same building or one nearby within a radius of one to ten miles." Called "a paradise of sorts". Discovered 1954 by Dr. Greenfield and Marshall David (M.E.G.).

**Layout.** Campuses are separate sectors joined by "a neatly systematized exterior pathway". Buildings sometimes "merge into a singular edifice", branch, form a "pedestrian bridge", or touch when close. "A few meters height of a concrete barrier and a chain link fence encircle and separate each campus"; low enough to climb; no gate, and some fence sections are misplaced so you can walk through. Buildings have 2 to 10 floors (stairs and elevators). Interiors: "solid concrete structures and smooth concrete/tiles/multicolored carpets", pristine, no mold. Colours "pale brown, gray, beige, and off-white". Classrooms are identical: writing boards, audiovisual gear (mostly 2000s: a time-dilation hypothesis), desks, seats. **"Upon entering the classroom, all electrical equipment and ceiling lights remain closed in contrast to the building's other parts, wherein all appliances and instruments are perpetually in function."** Other rooms: principal's and admin offices, faculty rooms, labs, libraries, utility rooms, "generally vacant and missing contents" (no chemicals, books, tools). About 100 rooms per campus. Door signs: four digits, first two = rooms counted, third = floor, last = building number; no subject and no campus name anywhere. **Courtyards:** merged buildings enclose one with "artificial grass and sidewalks", a translucent or missing ceiling, lampposts, benches, bins, trees; or a sports court. **Canteen** on every campus (ground floor, standalone, or in the courtyard): plenty of seating, "vacant food stands", nothing sold; water fountains, vending machines and lockers there and in hallways.

**Outside.** Plain green, "wavy-like pattern hillscape", some unbuilt plains, a rubble/gravel/sand road between campuses, a little flora, "a long fence that serves no use". **No day-night cycle**; the sun is the only celestial light and its intensity drifts (dimmer at Terra's night). Sky constantly blue with few clouds. **10 to 32 C**, varying over time. "Soft gales blow inconsistently", severe when temperature changes abruptly.

**Landmarks.** *Marshall David Campus*: all-white concrete, five floors, endless locker halls ("looks like a high school"), where newcomers end up, M.E.G. outpost (locked top floor, offices in classrooms), now worn (dirt prints, cracks, rubbish). *J. Barry Campus* (the Asylum, named for the Level 16 proprietor): blue or white painted concrete, gritty floor, trade hub and warehouse (Cool Mart Co.; medical supplies, almond water), strict alarms, many false ones. *J. Turner Campus*: like Marshall David, two floors, basketball court and courtyard at the core, a mile away, classrooms converted to lodging.

**History/people.** Sanguine Festivus: First Crash 1959 (100-200 dead), Great Crash 5 Feb 1997 (~3000 residents, began at J. Barry Asylum), Operation Blindside 11 Nov 2002 (700+ killed). Now under 100 residents; outposts all abandoned: Backroom Colonists "Base Sunfire", Party Crashers "Base Emberwatch", Backrooms Red Cross "Base Blackcross", P.E.A. HQ, M.E.G. "Base Blindside" (abandoned since The Flicker). Aftermath text: bullet holes and blood stains repainted, "modern furniture" installed; "few resources, particularly meals and drinks".

**Entities.** None today. Past: Partygoers (Entity 67). The mod already has `partygoer`, `partygoer-intern`, `faceling` (with a `faceling-teacher` texture).

**Entrances/exits (notes only).** Doors on many levels (small chance); emergency exits or lifts in Levels 1-4; "entering any sort of a high school building in Level 11". Exits: random doors, "generally Level 53"; noclip in Marshall David to Level 556.

Confidence: high for look and rules (one clear page); the history is long, mostly note fodder.

## 2. Prototype now vs lore
Built (`WorldLayout.Level52.cs`, 52-plan Status): a windowless interior school filling the whole round region: 7-wide locker halls every 96 blocks, 87x87 wings of dark classrooms (desks, chalkboards), store rooms, gym, canteen, edge hall; grey-beige fog, 18 C, stability 1.1, a rare school bell; no entities, loot, notes or handbook. Lang says "School Halls".

**How far from Greenfield: far.** The prototype is one indoor labyrinth; the lore is a campus of separate buildings in open green hills under a blue sky. What must change:
- **The outdoors is the level.** Grass hills, blue sky, sun, wind, 10-32 C; buildings sit in it. The plan's open question 3 ("skip outdoors, solid rim") contradicts the lore and should be reversed.
- **Separate fenced campuses** joined by paths and a gravel road, not a lattice of halls through everything; buildings of 2-5+ floors (prototype: one).
- Building interiors can reuse the prototype's pieces (lockers, desks, boards, gym, canteen), but as discrete buildings with windows and a **courtyard** (skipped now).
- Palette: pale brown/grey/beige/off-white; the mint dado `l52-wall` should be retinted. Halls lit, ALL classrooms dark (prototype has 1 in 6 lit: a mismatch, though a playability concession).
- No windows and no sky is wrong; the grey indoor fog and bell are the prototype's invention.

## 3. Gap list
**Must**
1. Exterior: rolling grass terrain, blue sky and sun, wind bed, 10-32 C drifting slowly (no day-night). Needs a technical check of how Level 94/188 do open sky in the band; if true open sky is not possible, fake it as 188 does and say so.
2. Campus layout: campuses on a jittered lattice (suggest 250-400 blocks apart, 120-200 across), gravel/path network, concrete low wall plus chain-link ring with a few gaps.
3. Buildings: 2-5 floors with stairwells, windows in outer walls, door plaques coded rooms/floor/building, lit halls, dark classrooms (windows give daylight so they stay playable).
4. Courtyards: artificial grass, paths, benches, lamp posts, trees, bins; a sports court in some.
5. No hostile spawns; empty roster except optional Facelings.
**Should**
6. The three named campuses as fixed variants: white five-floor locker campus (arrival zone), blue/white warehouse with fire doors and cages (trade), two-floor campus with basketball court and lodging rooms.
7. Canteen with empty food stands, fountains, vending (almond water as in Levels 4/3999), lockers.
8. Loot is sparse by lore: lockers hold a few school/office scraps; J. Barry warehouse crates of medical supplies and almond water; admin, lab and library rooms deliberately empty.
9. Entities: rare `faceling` (teacher/student textures); an optional ruined "Crash wing" with bullet holes and stains, and at most a trace of `partygoer` (my invention, lore says extinct). No new entity needed.
10. Handbook page and notes (below); classroom TVs/projectors of the 2000s as the time-dilation hint.
**Nice**
11. Pedestrian bridges between near buildings; dorm apartment blocks; abandoned outposts (Base Blindside, Emberwatch, Blackcross, with signage); the "fence that serves no use".
12. Elevators (recommend stairs first).

**Wanderer note ideas (suggestions):** (a) a student decoding the plaque numbers and finding no subject on any door; (b) "classroom lights are always off; the hall lights never go out"; (c) a trader at the warehouse on almond water and false alarms; (d) a survivor scrap from Blindside, "bullet holes behind the fresh paint"; (e) someone who climbed the fence and found it fences nothing; (f) an M.E.G. notice: outsiders on the top floor are sent back a floor.

**Handbook outline:** What it is (safe, Euclidean, outdoors) / reading the plaques / lights on in halls, off in classrooms / weather and temperature / fences and gaps / landmark campuses / what to scavenge (little) / history in a few lines / threshold lines.

## 4. Open questions
1. Number clash: Fandom campus vs Wikidot cave. Recommendation: Fandom; mention the cave in the handbook as a rumour at most.
2. Sanguine Festivus: history says extinct. Recommendation: no live infection; props and notes; optional rare partygoer flagged as invention.
3. Size: lore gives "one to ten miles" arrivals only. Recommendation: the sizes above.
4. Open sky in this engine: needs a decision before building (see Must 1).
5. Elevators: lore has them; recommend stairs first.
