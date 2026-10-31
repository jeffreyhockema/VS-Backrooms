# Level 31 brief: Roller Rink

Sources: Wikidot https://backrooms-wiki.wikidot.com/level-31 ("The Roller Rink", survival difficulty 0, "Devoid of Harmful Entities", rating +36; original by had86, with a twelve-entry diary of a lonely wanderer); Fandom https://backrooms.fandom.com/wiki/Level_31 (WindXD and Mike rewrite; class 1 Safe, Stable, "Minimal Entity Count"). Cleaned copies: scratchpad/lore/fandom-Level_31.clean.txt and wd-31.txt. Entity background: docs/design/entity-ai-overhaul/lore-2026-10.md (Facelings, section 3).

## 1. Lore where the wikis agree
- A 1990s roller rink, "infinitely looping" (Wikidot) / "spans hundreds of miles... rumored to be infinite" (Fandom). The rink is the largest part. Safe, stable.
- Muffled pop through ceiling speakers; DJ station on the **south side of the rink** with a docile Faceling; skate sounds and laughter (Fandom: heard "from above"); pizza and soda smell near the food court.
- Rink floor smooth **wood** (Wikidot: a short wooden gate with flaps onto rough black carpet); surroundings smooth, shiny, recently cleaned concrete, slippery (Fandom).
- Many coloured fluorescent tubes, a different hue per room (Fandom); Wikidot: a **star-shaped fixture at the rink's centre**, lights often dimmed "just bright enough for the skaters". Neon in the connecting halls; reflective surfaces.
- **Arcade** to the east, loops to its north entrance; modern cabinets (ski-ball, wheels, air hockey, movie-themed pinball), a few 1980s cabinets (Q*bert, Donkey Kong, Space Invaders). Wikidot: free with a **green card** from a blue-button dispenser. Fandom: doors carry handmade "OUT OF ORDER" signs; exposed wiring.
- **Food court**: small; cheese/pepperoni pizza, wings, foot-long hot dogs, a soda fountain pouring **almond water**; safe; a Faceling serves free and "will begrudgingly clean" litter and refuses free food to litterers. Square tables, orange plastic chairs, orange and green park benches bolted to walls, condiment stand, bins with a taped sign "Please throw away trash and uneaten food here!". The safest spot to camp.
- **Skate Rental**: past blue walls near the food court; tile floor; shelves of skates, counter, US size chart, ads for brands that do not exist (Fandom); the skates are anomalous and make falling hard.
- **Cinema** (Wikidot, north, TV screens): dark, small, one big TV, **three stepped rows of single continuous metal benches**; plays your favourite film; leave southward.
- Non-Euclidean: halls of inconsistent lengths, loops, two halls crossing without connecting.

## 2. Where they differ (choices in bold)
- Wikidot only: the **Coach** (Faceling, brown hair, striped coach's uniform, name tag; friendly, free skating lesson, remembers names, leads you out if asked or when you stay too long); Venosha temporary camps; the theme "do not stay".
- Fandom only: **Employees Lounge** behind the food court kitchen (exposed brick or concrete, lockers, grey carpet, closets, kitchenettes, CCTV that can set off the fire alarm, silent); HVAC ducts, leaks, flooded rooms, about 8 C; **glowing carpet** as in Level 25; shadow figures with knives ("Paranoia"); unconfirmed Hounds; no outposts because groups get split.
- **Choice:** Safe class 0, Wikidot's Coach and diary tone, Fandom's lounge, cold pockets, glowing carpet and Paranoia as atmosphere. Paranoia figures cosmetic only (Fandom calls even their existence unconfirmed); no Hounds.
- Exits (notes only): Wikidot: noclip into a working arcade game to Level 40, white door "70" to Level 70, "Employees only!" door in the food court to Level 232. Fandom: deeper in the arcade to Level 25, the Revolving Door to 9/10/11, stealing skates noclips you to Level 0 without them. Entrances: a wooden door with 2000s bubblegum pop behind it (Levels 2/3/6/26/27/28), stairs from Level 30, Level 67 pastry, a hyperlink in Level 210.
- Confidence: layout and sounds agree strongly; scale and loops are vague; the Coach and the diary carry Wikidot's meaning.

## 3. Prototype and gap list
Built (`WorldLayout.Level31.cs`, 31-plan Status): neon halls every 128 blocks (Level 3999 galaxy carpet, neon rails), 121x121 complexes with a wood-oval rink (dasher, skirt, DJ booth, mirror ball, tubes), service ring, snack bar, rental, lobby, arcade (3999 cabinets), baths, HVAC (8 C), stores, cinemas, lounges, glowing-carpet rooms, emptiness complexes, one synthesized music loop, stability 1.1, 12 C; no entities, loot, notes, handbook.

Mismatches with lore: (1) no green-card dispenser, no OUT OF ORDER signs; (2) DJ booth on "the far skirt", lore says south; (3) no star fixture, no wooden gate with flaps, skirt is retro carpet where lore has rough black carpet; (4) food court furniture is generic cafe, lore is orange plastic chairs and orange/green benches, with condiment stand, bins and the taped sign; (5) no Facelings, no Coach; (6) cinema rows are not stepped; (7) the 3999 galaxy-carpet halls and neon identity leaks; (8) "Employees Lounge" exists but lacks CCTV, lockers on brick and silence; (9) shared corridor and arcade at 65% where lore says arcade is rarer to enter.

**Must**
1. Coach: reuse `faceling` with a new striped-uniform texture and name tag (new texture, `faceling-teacher` as base); invulnerable, never hostile; right-click dialogue: lesson, how to live here, "lead me out" (points to a threshold-note, no real exit), remembers the player name. Stands behind the rental counter.
2. Faceling employees: food-court server giving free food (reuse 3999 tray-meal logic; items: pizza slice, wings, hot dog, almond water), DJ Faceling at the south booth; litter rule (dropped items in the food court revoke free food for that player for a while).
3. Food court proper: orange chairs and benches, condiment stand, bins, taped sign, soda fountain with almond water; arcade: green-card dispenser, OUT OF ORDER signs on some doors, a few 1980s-style cabinets (generic art, not trademarked names).
4. Rink: star-shaped fixture, short wooden gate with flaps, rough black carpet outside, DJ station on the south skirt.
5. Skates: anomalous item from the Coach (worn: no slipping on smooth blocks, small speed bonus); lore line for the penalty goes into notes only.
**Should**
6. Cinema with three stepped rows of continuous metal benches and a big TV (loop texture); darker room tone.
7. Employees Lounge behind the kitchen: brick or concrete, lockers, grey carpet, closets, kitchenettes, CCTV props, silence.
8. Cold HVAC pockets with leaking pipes, puddles and flooded rooms (shallow water blocks), dead radiators; ads of non-existent brands in the rental.
9. Paranoia: still black figures at the edge of dark rooms that vanish on approach (client-side visual; no AI).
10. Sounds: speaker pop (exists), skates rolling and laughter "from above", ballast hum, CCTV chirp, fire alarm blip.
**Nice**
11. Non-Euclidean halls (two halls crossing, a hall that loops) with seamless teleports; Venosha camp prop; revolving door prop; glow carpet "mirror" rooms toward Level 25.

**Wanderer note ideas (suggestions from Wikidot's diary):** (a) the wooden door and the music before the rink; (b) the free hot dog, and the Faceling that cleans up after you; (c) a green card and an old cabinet high score; (d) the Coach taught me to spin, he remembers my name; (e) "nothing feels good anymore, and the Coach says go"; (f) "do not take the skates".

**Handbook outline:** Safe, but do not stay / the Rink and the DJ / Arcade and green cards / Food court etiquette / The Coach and the skates / Cinema / Cold rooms and the Lounge / Shadows are only paranoia / Threshold lines for notes.

## 4. Open questions
1. Coach: only on Wikidot. Recommendation: include, the heart of the level and a safe talking NPC.
2. Hostile shadows: Fandom "unconfirmed". Recommendation: cosmetic only.
3. Hounds: unconfirmed. Recommendation: none.
4. Infinite loop: keep the lattice; fake the loops with signs and mirrors; real teleports later.
5. Hall look: lore says reflective neon halls, so the 3999 reuse is acceptable; recommend swapping the galaxy carpet for a plain dark rink carpet so it does not read as Level 3999. Ask the user if the shared look is intended.
