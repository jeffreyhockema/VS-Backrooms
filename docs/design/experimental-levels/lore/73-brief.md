# Level 73 "The Redlands": lore and gap brief

Sources: Wikidot https://backrooms-wiki.wikidot.com/level-73 (Kitty Rika, survival difficulty 5; the mod's source). Fandom's current Level 73 (https://backrooms.fandom.com/wiki/Level_73) is the unrelated "Shooting Gallery" level under a rewrite notice: NOT a source. Fandom has no Redlands page. Confidence: high on the lore (the page is short and I read all of it); anything marked (suggestion) is mine, not lore.

## 1. Lore

**Frame.** The article is "uploaded ... from the confines of the Silver Castle" by "the Children of Coran": "We are safe here. We are loved here. Someday, we will meet on the other side. When we do, we'll be bringing him with us." Tone: warm, cultish, desperate. An M.E.G. audio log ends the page: Coran, newly recovered from the Gloom, asks them to call off expeditions ("they won't be able to get out. They'll just be trapped with the rest of us"). A related tale, "The Crimson Family, Part I", is linked; I did not read it.

**Look.** "Commonly known as 'The Redlands,' due to the crimson-stained ground." One "medium-sized island that every wanderer will no-clip into"; an unexplored ocean around it, "incredibly dangerous to enter due to the presence of unidentified aquatic entities"; no other land known. Ground "squalid black-red", "blackened fields". Only one photo survives; the others were "deemed too upsetting". No scale numbers or terrain detail beyond "highest point" (the castle).

**Light and sky.** "Near-perpetual state of darkness. There is no day or night cycle. Instead, a full moon constantly lights up the squalid black-red ground below, never changing from its position. The moon is prone to being blocked out by suffocating, thick black clouds, plunging the entire level into darkness." Hard rule: "DO NOT use an artificial light source. YOU DO NOT WANT TO SEE until you reach the doors of the Silver Castle."

**Sounds, smells, temperature.** Not stated. Inside, the dining-hall fireplace "provides heat to the rest of the castle"; Hound meat is the fuel.

**Hazards.** Density "one per 35 square feet (3.3 square meters)", all "extremely hostile", gathering "in large groups to attack the nearest human ... hunting them relentlessly until they die". Listed: Windows, Smilers, male and female Deathmoths, Clumps, Dullers, Hounds, Skin-Stealers, Death Rats, Camo Crawlers; unidentified aquatic entities offshore. Unique: CORAN, and the Great Hound (dead, slain by Coran).

**Procedure.** "You will almost always find yourself within eyesight of the Silver Castle ... run straight to the castle. DO NOT look around. DO NOT stop moving. ... If you reach the doors without being immediately mauled by a horde of entities, bang on the door as loud as possible, and you will be safe." "Follow the hard sensation on the bottom of your feet" (the stone path).

**The Silver Castle.** Only known building; builder unknown. "Expansive gothic-style", "fully furnished and lit"; "high and thin stone walls" around it with "a singular open gatehouse in front of the entrance"; stone path gate to door. Outside and door "impenetrable and invincible ... including Dullers trying to reach through". Named for banners on the walls: "a silver heart with ram's horns on a black field". A weak Wi-Fi signal inside. Interior "well-maintained and lavishly decorated": main hall, dining hall, six guest bedrooms "with two large beds each", the master bedroom (Coran's, third floor); three floors and an attic opening onto a balcony ("CORAN has declared the attic off-limits"); two guest rooms per floor, one on each side. "Glasses of potable water and portions of food for each human ... appear on the silverware at the grand mahogany table at regular intervals, and seem to be infinite." Two bathrooms with "large, infinitely-refilling barrels ... warm water" for bathing and washing clothes. "Numerous paintings of locations in The Frontrooms, but none of them lead outside." "Red velvet curtains in front of every window ... the windows behind them are completely boarded with wooden planks. CORAN states that this is to dispel Entity 2 Instances. Do not look outside."

**CORAN.** Unique, male-identifying, "extremely aggressively towards other entities but never towards humans"; calls the humans his children, feeds and cares for them; spends his time outside slaughtering the hordes; the strongest entity there. Looks like a middle-aged man, heavily muscular, 7'9", slicked black hair, two horn protrusions. No arms: "gigantic golden chain links which connect his shoulder to his hands, ... enormous, black spiked gauntlets"; a black exoskeleton over most of the body; three hearts (two in the gauntlets, one exposed on the chest) that regenerate almost all injury while one works. A face scar gouged out his eyes, so he is blind; he wears the two eyes on a necklace "as an act of defiance". Goal: exterminate every entity, or find an exit.

**People.** Coran's Children: "exactly 37 as of right now. There is nobody here but us."

**Entrances/exits.** In: "Stay near the Gloom for too long on Level 9.1"; others "from Level 14 and Level 6". Out: "no known way". Survival difficulty 5; only the castle is safe.

**Items.** Only the castle's infinite food and water, warm bath water, Hound-meat fuel, paintings. Nothing outdoors.

## 2. Prototype now (from 73-plan.md Status)
Region 512 blocks radius, open sky; island radius ~230, peak ~12, in a still-water sea ringed by a basalt cliff; Silver Castle with 48x40 curtain wall, towers, gatehouse, paved path, 28x20 two-storey keep (hall, dining hall with ember hearth and 12-chair table, stair, two bedrooms, bathroom, boarded windows, 32 sconces); crimson-black fog, brightness 0.30, hidden sky with a fixed moon (src/Regions/L73Moon.cs) and dark spells; reused sound bed; temps 4 C outside, 15/22 C inside; arrivals 85-165 blocks from the gate. Six blocks plus a moon picture. No entities, thresholds, loot, notes, handbook, doors, curtains, banners, upper floors, attic, master bedroom, food or water.

## 3. Gap list

**Must**
1. **Hostile horde.** Roster entries exist for smiler, hound, deathmoth-male/female, skinstealer, duller, deathrat, clump. 1 per 3.3 m2 cannot be simulated; give the island a top-band table with large packs (high PackMax) that converge on the nearest player ("hunting them relentlessly") and no solitude relief outside the wall. Inside the wall, nothing hostile spawns (suggestion). Windows exist only in Level 188 and Camo Crawlers not at all: see open questions.
2. **CORAN** (new entity; biggest item). Blind ~4-block giant: horned head, black exoskeleton, golden chain arms, black spiked gauntlets, exposed chest heart, necklace. Never hostile to players, never killable by them; kills any hostile within range outside the wall, regenerates, patrols the plateau and returns. Blind means he hunts by sound (suggestion). Heavy chain-and-boot sound (one new loop). A few dialogue lines: attentive, protective ("Do not look outside").
3. **Door and knock rule.** The castle door is shut and impregnable; banging on it (repeated right-clicks or hits) opens it and spawns/awakens a welcome (suggestion on the mechanic; lore only says bang and be safe). The gate stays open.
4. **Table of plenty.** The dining table refills a glass of water and a meal at each seat at intervals, infinite (reuse vanilla/mod food and Almond Water items); bath barrels with infinite warm water (a warmth/stability gain is a suggestion). This is the level's only resource; wire it in the supply/loot terms of the mod.
5. **Finish the castle to lore:** three floors, six guest rooms (two per floor, one each side) with two large beds each, master bedroom on floor 3, attic shut off-limits with a balcony, two bathrooms, red velvet curtains (new block) over planks, silver-heart-and-ram-horns banners on the wall (new banner block/texture), Frontroom paintings (reuse painting props), the pitched or flat roof.
6. **The light rule.** Carried or placed light outdoors draws the horde much faster and detects from afar (as Level 9 treats lit players); optional stability cost for lingering (suggestion).

**Should**
7. **Wanderer notes (suggestions):** "I did not look around. I think that is why I am writing this."; "The ground is wet and it is not water."; "Bang until your hands bleed. He hears, he cannot see."; "The moon went out for what felt like an hour. Something breathed against my sleeve."; "Thirty-seven, they say. They never say thirty-eight."; "Hound is the fuel. Do not ask about the stew."
8. **Children of Coran:** ~37 peaceful wanderer NPCs in the castle (existing wanderer entity), warm cultish dialogue ("We are loved here"), no or token trade.
9. **Sounds.** Far howls and the crash of hordes met by Coran, chains, wind and surf; inside, fire and heavy steps overhead (mostly reuse, as built).
10. **Handbook page outline:** The Redlands (class 5); the island and the moon; the one rule (run, no light, bang); the castle and its table/baths/curtains; Coran ("do not be afraid"); the Children; entrances (Gloom 9.1, 14, 6) and no exit; the M.E.G. transcript.
11. **Guide/class:** class 5, only the castle is safe.

**Nice**
12. Aquatic hazards offshore (reuse Level 7 swimmers).
13. The Great Hound's skeleton on the plateau, tying to Coran's scar (my idea).
14. Gear and dark bones scattered on the fields; one note about the "upsetting photograph".
15. Feed Hound meat to the hearth for warmth.

**Contradictions in the prototype:** bedrooms have one bed (lore: two large beds each); windows boarded but not curtained; keep is two storeys (lore: three plus attic); castle door open (lore: impregnable, bang to enter); no banners.

## 4. Open questions
1. **Windows:** hostile on the island, yet the curtains/boards exist to "dispel" them. Recommend a rare outdoor Window on the black rock using the Level 188 behaviour, or omit and say so in the handbook.
2. **Camo Crawlers:** no mod entity and I did not fetch their page. Recommend omit unless a cheap model is wanted.
3. **Density vs playability.** The lore reads as near-certain death. Recommend lethal packs but a short run (arrival 85-165 blocks) so a fast player makes it.
4. **Coran's model:** recommend simplified (horned head, cuirass, chain arms ending in gauntlet blocks).
5. Wikis do not conflict on the Redlands; keep Wikidot.
