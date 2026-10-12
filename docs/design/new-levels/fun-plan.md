# Level Fun =): research, design and integration plan

**Level Fun =)** (tag `fun`, internal id **15**, constant `WorldLayout.FunLevel`, shown as "Fun") is an endless warren of
children's party rooms. Every table is laid, every cake has candles, and nobody comes to the party. Nobody except
the Partygoers: tall yellow things with a smile carved into the face and arms that end in mouths. Their tables are
the best larder in the Backrooms. The level asks you to steal from them without being seen, and the posters say you
are very welcome. =)

Section 9 lists the decisions for the user. The user took every recommendation; `LINKS.md` overrides the plan on
cross-level links (the Hub's Fun door and The End's "=)" terminals are one-way into a lobby, and there is no way from
Level Fun to the Hub).

## Status (2026-10-09): phase 2 code built (assets by the asset agent)

Checked with the layout harness and a headless server (port 42475, seed 12345): chunks were dumped and rendered.
**Not yet played in a client.**

**Built (C#):**
- **Layout** (`WorldLayout.LevelFun.cs`):
  - The region keeps the scaffold's placement and size (north-east, radius `max(60, spawnMacroX/40)`), with a hull rim.
  - 96-block plans are cached by block.
  - Promenades on the block lines and halls every 32 blocks. Both jog every 12 blocks and run straight at crossings.
  - Elevator lobbies at the promenade crossings, with brass doors and a deck sign. People arrive only here.
  - 3 × 3 squares per block. Each is a party suite (1, 2 or 4 rooms, partitions two thick), mural, themed (movie night, Halloween with vanilla pumpkins, tea party), play (ball pit; deep 1 in 4), bounce (walk-in houses, blowers, cords), arcade, kitchen, gift room, crew corridors (Carnivorous Balloons in the dark), open deck over the sea, waiting room, FUN-door vestibule or service stairs.
  - Cloned hallway in 1 block in 8.
  - Reversed posters in half the blocks.
- **Furnishing:** every party is furnished as in 3.3: tables, cloths, chairs, cakes, plates, cookies, gifts, ceiling balloons, streamers, bunting spelling HAPPY BIRTHDAY, string lights, speakers on or off, posters, smileys, and a balloon arch over doors with guests.
- **Generator** (`WorldGenerator.Fun.cs`): its own prop and wall-item tables, so no shared prop bytes are used inside the region.
- **Thresholds** (`ThresholdNetwork.Fun.cs`):
  - Level 0 poster → lobby, one-way.
  - Level 1 confetti stairs ↔ service stairs, two-way.
  - Level 5 FUN door ↔ vestibule, two-way.
  - Level 11 mascot doors ↔ waiting room, two-way.
  - Reversed poster → Level 4, one-way.
  - Overboard → Level 7, one-way.
  - Deep ball pit → the castle ball pit in Level 94, one-way.
- **Runtime** (`src/Regions/FunSystem.cs`):
  - Guests are put down at each party, out of sight, and come back a day after they are killed.
  - Party Fever: a poultice or bandage cancels a bite within 30 s. Fever adds hunger and lowers the stability cap, decays only outside the level, and Almond Water helps. At 1.0 you "joined the party =)", and a guard intern stands where you fell.
  - The hat-and-balloon disguise.
  - Familiar-voice chat lines.
  - Block classes: cakes and cookies, popper gifts, Carnivorous Balloons, the torch-burnable poster, Red Velvet.
- **AI** (`src/Entities/AiTaskPartygoer.cs`):
  - States: party, patrol, gaze, hunt, search, return.
  - A nearsighted sight cone, and the pack joins by line of sight.
  - The latch, berserk claws, and a body behaviour (fireproof hide; carapace opens at half health).
- **Shared edit points:** fog, deck air and the sound bed; `Danger` 0.9; roster packs; distant sounds; `MenaceSystem.Rate`; bounty; roof protection.

**Checked:**
- `funstats` (6 × 6 blocks, 2 ms per block):
  - 54% of the area is floor.
  - No walkable floor is unreachable from a lobby.
  - Longest straight corridor view: 17 blocks (the cloned halls 106).
  - 53% of possible rooms have guests.
- `regions`: 60/60 arrivals, 0.16 ms per cell.
- `links`: every new kind leads where it should; the two-way ones are paired.
- `funlinks`: Level 0 posters lead into a lobby; Level 1 stairs climb back home.
- `layouthash`: with the Fun entrances switched off (`BACKROOMS_NO_FUN_ENTRANCES=1`) against on, only the Level 1 line (confetti on 1 in 20 stair cores) and the Level 5 line (FUN doors) change. The Level 0 and 11 entrances are too rare to fall in its sample.
- **Headless renders** in `scratchpad/fun/shots`: a party room, the mural room, a bounce hall, an open deck.
- **Headless encounter test:** gaze → hunt, the pack joins by sight, and the latch lands for 5.0.

**Deviations:**
- **The region keeps the scaffold's placement and radius**, not the plan's own numbers.
- **`FunDrop` stays 0.** `FunBandDepth` is 12 instead, which leaves room for the deck's 14-high void and the sea 10 below.
- **No lure balloon AI, and no Host or LUCA tears yet.** Their models and JSON exist; this is the planned later phase.
- **The centipede at death** is particles only (decision 9: only if cheap).
- **Guests and the 30-second window are untested.** Both need a real player, which a headless server does not have.
- **Wall items are stored in `Tile.Roof`** on the floor tile in front of the wall (Fun-local).
- **Level 5's FUN door is one leaf.** That is the `fun-door-fun-single-*` block (manifest change C3).

---

## 1. What the lore says

Sources, by weight: the Wikidot wiki first, then Fandom, then Miraheze, then well-known depictions. Pages were
fetched on 2026-10-07. Copies of the pages, the Wayback snapshots and the canon images are in that session's
scratchpad (`scratchpad/fun/`). Quotes are marked and kept short.

### 1.1 The original "Level Fun =)" (Wikidot, 1000dumplings, 2020): the canon that defined the meme

Source: https://backrooms-wiki.wikidot.com/level-fun as archived in 2020-2022
(`https://web.archive.org/web/2020*/backrooms-wiki.wikidot.com/level-fun`).

- **The page is written by the Partygoers themselves.** Its whole text:
  - "We have so much fun here! =)" and "Level fun is the most fun level in the whole backrooms!"
  - Description: "Small party room. Lots of cake and cookies and almond water. We have so much fun here! =) Don't upset the host."
  - Community: "The Party: The partygoers of the fun level. ... Come join us!"
- **Entrances.**
  - "Noclip through the ceiling in Level 1 and you may just end up here!"
  - "If you see confetti falling out of a window on Level 188, that's us having a party!"
  - "Our main entrance is in Level 283 where there's a set of double doors with letters that spell the words FUN in big bold multi-colored font in The Lounges!"
- **Exits:** "Why would you want to leave? =)"
- **The two images that *are* Level Fun to most people:**
  - A long yellow room. Painted on the walls are cartoon murals: a grey mouse with a cup, a grinning yellow man with a hot dog, a cheese block kicking a ball, a pink stork. The carpet is red with race tracks and toy cars, the skirting is white tile, a low bench stands in the corner, and the drop ceiling has fluorescent troffers (`i.redd.it/h0qi1m19hfz41.jpg`).
  - Flickr's "Birthday party room": orange walls, tables in blue and green striped plastic cloths, white, orange, lime and red plastic chairs, orange cups, paper plates, a "HAPPY BIRTHDAY" balloon banner.
- **Level 283 "PlayLand" (Wikidot) still carries the Partygoers' graffiti in its Lounges:**
  - "One Lounge leads to the best Party in all the Backrooms =)"
  - "Come join us if you see a double wooden door with colorful big text that says 'FUN' =) ... hamburgers and fries but inside we have cakes and cookies! =)"
  - Source: https://backrooms-wiki.wikidot.com/level-283

### 1.2 Entity 67, the Partygoers (Wikidot)

**Original (1000dumplings, 2020; archived at `backrooms-wiki.wikidot.com/entity-67`):**

- **Look:** "tall, bipedal creatures with a smooth leathery skin". Usually bright yellow, but also red, green, blue or white, with "a cartoonish smile carved into the 'face'". Their arms end in "openings with several teeth inside, similar to ... a bloodworm or lamprey eel's mouth".
- **The canon picture:** "Yellow, holds a red balloon, covered in blood". It is a Gumby-like slab of a body standing in a Level-0-like room, with noodle arms and a red balloon on a string.
- **Behaviour:**
  - "extremely quiet and stealthy, but they lack in speed. The moment you think one is nearby, run the opposite direction."
  - "If one latches on to you, its already too late. You will be transformed into one within an hour."
  - They operate machinery and **edit the M.E.G. database**. "These changes all have a smile =) typed into them, if you see one anywhere in an entry do not trust it."
- **Advice:**
  - "Avoid balloons if you see them floating on their own ... these are almost always bait."
  - Don't "follow the sound of laughter or balloons".
- **Level Fun as the original describes it:** "balloons, tables, chairs, and other party favors". The Partygoers' base, where they turn corpses "into cakes and cupcakes".
- **Habitats:** Level Fun, 119, 188.

**Rewrite (Robert Goerman and MC_Crafter_24_7, current; https://backrooms-wiki.wikidot.com/entity-67):**

- **Body:**
  - "These tall, bipedal nightmares have smooth, leathery skin", typically bright yellow (red, blue, green and white exist).
  - "a carved smiley face smeared with blood".
  - Legs of "a thick, blocky shape".
  - "The chest area is shielded by a subtle carapace."
  - "long, noodle-like arms that end in sucker mouths full of hooked teeth".
- **Berserker mode.** Cut the arms off and it can no longer transform anyone, but a hidden chest carapace flips open: "a pair of anomalous arms with powerful clawed hands" (a Phobic Centipede inside). Then go for the face and head.
- **Inside**, a human body is fused with a Phobic Centipede and crustaceans:
  - "The insides ... burn fiercely": "Flares, black powder, **firesalt**, and pyroil have all been proven to reliably initiate combustion."
  - The hide itself is "fireproof and resistant to cuts and punctures".
  - A dead one "slowly walking away on little centipede legs".
- **Senses:** "Partygoers are nearsighted and slow"; "hearing is reduced, and vision turns nearsighted".
- **Telepathy.** It needs gaze ("Partygoers must fix their gaze on the intended receiver"). It is heard as speech "in familiar voices". "This is why Partygoers hunt humans in tight packs and always keep one another in sight. You can never catch a Partygoer alone."
- **Red balloons:** "most newly transformed Partygoer 'interns' carry a floating red balloon".
- **The Bakery:** their cakes are made of people ("Royal Velvet Cake", "Royal Icing"), captioned "**DO NOT EAT**".
- **Misinformation:** "Partygoers display their '=)' symbol whenever they alter official M.E.G. information =)". Rumoured entrances such as "no-clipping into the ceiling of Level 1" are called false and planted.
- **Do's and Don'ts:**
  - "Run! Distance is your best chance for survival."
  - "Tell anyone immediately if you are bitten. Seconds count!"
  - "Just because you see them, doesn't mean that they can see you."
  - "Keep something, anything between you and them".
  - "Forget to have fun =)" is the planted last line.
- **The Party Hosts.** Partygoer Zero's chat: immobile Party Hosts, fed on Facelings, "Once Party Hosts turn golden, they are perfect", and their "LUCA tears", "spinach for Popeye".

### 1.3 Level Fun today on Wikidot: Level 26, "The SS Fun =)" (SD 5)

Source: https://backrooms-wiki.wikidot.com/level-26 (the `level-fun` slug now shows it). Goerman and MC_Crafter_24_7,
"Original Level Fun page by 1000dumplings".

- **Survival Difficulty 5:** "Unsafe. Unsecure. Entity Infestation."
- **The ship.** The cruise liner *Adventure* (about 150 m), its name crudely crossed out and replaced with "SS Fun =)". It travels by noclipping, vanishing in a green fog, and its power never fails.
- **Exterior decks:** trashed "perpetual demonic frat party", blood spatter, garbage-dump cabins, "a crimson pool", ruined restaurant, bar and lounge.
- **Interior** (the part that matters for us):
  - "Lower decks appear infinite, as screams echo down endless corridors and countless party rooms."
  - "Most chambers feature typical party décor, while others reflect a theme, such as popular movies or holidays. There are even rooms with booby-trapped party favors and decorations."
  - "The elevators are the hub of these lower decks, opening into a labyrinth of hallways that branch off to every compass point."
  - "One particular party room was cloned thirty-eight times in a row along a particular hallway" (Liminal Echo).
  - "infestation of **Entity 110** in the darkest corners", the Carnivorous Balloons, which the Partygoers "pop".
- **April Showers' escape:**
  - A "TIME 4 FUN" poster noclipped her sister. "There's no smiley face on it ... It's safe!"
  - "about forty assorted staterooms" on the main deck.
  - A suite with "a huge monster filling the ceiling ... like a golden fried egg with an eye-and-mouth combination in the middle". That is a Party Host, fed live Facelings.
  - A poster whose "writing was reversed, and I couldn't get my eyes to focus ... I touched it. The next thing that I knew, I found myself on **Level 4**."
- **Entrances:** "Finding and touching party paraphernalia (balloons, party hats, decorations, and posters) anywhere in the Backrooms might no-clip you here." You can also board when it materialises. A B.N.T.G. scout "no-clipped when she picked up a party hat".
- **Exits:** "Touch a reversed, out-of-focus party poster, and you will no-clip to another level. You can also jump overboard."
- **The ship has been sighted** on water levels (134, 180, 230, 422, 711) and land levels, including **Level 10 "The Bumper Crop"**.
- **Countermeasure:** M.E.G. "incinerated the party decorations by holding flaming torches near, but not touching" them.

**Entity 110, "Carnivorous Balloons"** (https://backrooms-wiki.wikidot.com/entity-110):
- They look like balloons with a ribbon, "any shape, color and size".
- They are baited with a sac of strong-smelling food ("onions or garlic").
- **Touch:** the ribbon stings with a paralysing toxin, then the balloon digests with ammonia.
- "Don't try to pop them, as it will release toxic ammonia gas."
- Keep 2 m away; poke them with a long stick.
- "experienced wanderers tend to steer clear of balloons because of The Partygoers."

### 1.4 Second opinions

**Fandom, current** (https://backrooms.fandom.com/wiki/Level_Fun, via the API; Nex and egglord). Level Fun is three parts:
1. **A warehouse of bounce houses:**
   - "The constant drone of inflating air and overhead lights", "frigid air-conditioning", "faded, retro carpeting".
   - Extension cords "in snakelike formations".
   - Inside the inflatables, the floor deflates "gradually sinking them up to waist-height". A slide inside leads on.
2. **The Play Rooms:** indoor playground structures, mats, slides, nets, ball pits "much deeper than they appear". Wanderers resurface "in a different location". A "dreamy melody" plays.
3. **The Party Rooms:**
   - "a mazelike series of twisting corridors and side rooms lined with multicolored, vinyl tiles".
   - "the soft, yellow glow of the ceiling lights buzzing above".
   - Tables "dressed in colorful cloths and decorative paper plates", rows of plastic chairs, holographic streamers, balloons "never seeming to deflate", inflatable thrones for guests of honour.
   - A "soft, hazy, and quite pleasant" melody from loudspeakers.
   - Elusive **double doors** lead to a waiting-room lobby with grey carpet, cushioned chairs and "a lone secretary desk ... separated by a layer of glass". Its other door is the exit.
- **Partygoers (Entity 67, "Sanguine Festivus"):**
  - Victims of a hunger virus that spreads from the level itself.
  - In the Party Rooms they hide under "a large cloth" (yellowed tablecloths) with "a smile-like stain over their face".
  - "Move in a deliberate wading motion", babble, and "rely on auditory cues".
- **Entrances:** gymnasium-style double doors painted with "animal mascots such as tigers, parrots, and giraffes", in "structures in **Level 11** resembling parking garages", and in 18, 21, 25, 52, 257, 800. **The exits** from the Party Rooms lead back to the same list.

**Fandom, previous version** (oldid 738790, KosefSturre):
- **Rooms:** "a vast and complex network of rooms and hallways adorned with wallpapers of wildly variating colors and patterns".
- **Furnishings:**
  - Dining and picnic tables with plastic chairs, "packed full of food, drink and messily-wrapped gifts".
  - "Balloons can be found practically every five feet".
  - Streamers, banners, confetti, arcade cabinets, "checkerboard" mats.
- **Food:** "more often than not edible, albeit usually having a peculiar aftertaste of rust or meat".
- **Music:** "the constant sound of music from one direction or another, near or far".
- **Flooding:** flooded lower sections hold contaminated grey water. The infected bottle it and leave it on the tables.
- **The infected:** they offer drinks and urge you to "join the celebration", then turn violent if refused.
- **Entrances and exits:** "a vibrantly-colored wooden door with multicolored flashing lights and the faint sound of music". Near one you may see "a crudely-painted design of a red smiley face".

**Fandom's earliest versions (2021)** copy the original's entrances (the Level 1 ceiling, the Level 188 window, the Level 283 FUN doors). They add "The cake ... avoid it at all costs" and "DO NOT UPSET THE HOST!".

**Miraheze** (https://backrooms.miraheze.org/wiki/Level_Fun): a protected joke page, an "Endless suffering" GIF and nothing else. No second opinion there.

**Well-known depictions.**
- **Escape the Backrooms** (Fancy Games, 2022) has a Level Fun of orange halls and white plastic tables. Partygoers stand still with balloons, nodding. One that sees you alerts the pack, you hide under the tables, and the level ends in a chase. That stealth loop is what many players expect.
- No Kane Parsons film covers it.

### 1.5 What everyone agrees on, and the contradictions

**Agreed:**
- Endless party rooms: balloons, tables, cake, streamers, confetti.
- Cheerful music with no source.
- The "=)" as the Partygoers' signature on lies.
- Food as bait.
- Partygoers are slow and transform people.
- Getting out is hard.

**Contradictions:**

| Question | Wikidot (original) | Wikidot (rewrite) | Fandom |
|---|---|---|---|
| What the level is | "Small party room" (the Partygoers' own words) | Infinite party decks inside a noclipping cruise ship | Bounce-house warehouse → Play Rooms → Party Rooms |
| What a Partygoer is | Yellow carved-smile creature, lamprey arms, red balloon | Same, plus chest carapace and centipede berserker | Virus-infected humans under tablecloths |
| Senses | Quiet and stealthy | Nearsighted, reduced hearing, gaze-telepathy | Hunt by sound |
| Exits | "Why would you want to leave? =)" | Reversed poster (→ Level 4), jump overboard | Lobby door → 11, 18, 21 ... |
| Ceiling of Level 1 | The way in | Planted rumour | (not mentioned) |

The mod follows Wikidot throughout: the original's party rooms and creature, and the rewrite's interior decks, senses, carapace and exits. Fandom contributes furnishing detail (vinyl tiles, waiting-room lobby, mascot doors, bounce houses, extension cords, the cold AC).

---

## 2. Where it fits

### 2.1 A noclip region, like 37 and 94

Level Fun is somewhere you are *taken*. You touch a poster, climb into a ceiling or walk through a door that should not be there. It is a region, not a ring, exactly like the city, 37 and 94.

**Region**
- **Predicate:** `InFun(mx, mz)`, checked in `ComputeLevel` after `InMotion`, so it replaces only Level 10 cells.
- **Centre:** north-east of spawn on the diagonal:
  - `FunCentreX = spawnMacroX + D`, `FunCentreZ = spawnMacroZ - D`;
  - `D = Math.Max(680, spawnMacroX * 33 / 140)`, about 0.236·S per axis, so 0.33·S from spawn.
- **Clearance:** this keeps it clear of the city (0.25·S east, radius 0.15·S) and of Motion (0.25·S north). Centre-to-centre distance is about 0.234·S against 0.216·S of combined radii including the shape noise.
- **Radius:** `FunRadius = Math.Max(80, spawnMacroX / 20)`, the same as 37 and 94, so it is endless to anyone inside. Shape noise `Fbm(mx/40, mz/40, SaltFunShape)`.
- **Harness check:** the `regions` mode must confirm there is no overlap with the city, Motion or the other new regions.

**Rim: the ship's hull**
- White-painted riveted steel with round brass-ringed portholes onto black (`fun-hull`, `fun-hull-porthole`).
- It is the canon wink: the interior "is infinitely larger than the ship itself".

**Floor and sky**
- **Floor:** `FunDrop = 10`, so `FloorFor(Fun) = FloorY − 10`. The tallest space (the open deck, section 3.2) tops out at about `FloorY + 4`.
- **Band bottom:** `FloorFor(Fun) − 12`, for the deck's water.
- **Sky:** enclosed. `IsOpenSky` must *not* include 15.

**Display**
- `DisplayNumber(15) = "Fun"`, and the title "Level Fun =)".
- `/backrooms goto` and `find` parse ints through `FromDisplayNumber(int)`, so they need a string alias: "fun" maps to 15. This is shared with the other named levels (!, End, Hub); CONTRACT.md should settle it.

### 2.2 Its part in the threshold network

Canon ties Level Fun to levels the mod lacks (188, 283, 26's sea and land sightings, Fandom's 18, 21, 25 ...). Each link is
redirected to the nearest level the mod has, keeping canon's *method*. Rule: "walked through = two-way; fell, dived
or taken = one-way". Every threshold always leads to the same place (ThresholdNetwork).

**Ways in**

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| Level 0 | A **"TIME 4 FUN =)" poster** on the wall of a rare party-dressed room in the outer Lobby. Touch it (right-click) | A Level Fun elevator lobby | None (one-way: taken) | Wikidot 26: touching party posters/paraphernalia anywhere noclips you; April's sister and the poster |
| Level 1 | One of Level 1's **stairs that climb into the ceiling**, about 1 in 20 of them (own salt): confetti trickles down the steps and a red balloon is tied to the rail | A Level Fun service stair that climbs into the ceiling | The same stairs (two-way: walked) | Original Wikidot: "Noclip through the ceiling in Level 1" |
| Level 5 | **Wooden double doors with big raised multicoloured letters F-U-N** in a hotel corridor (about 1 in 150 locked rooms, own salt `SaltL5Room + 15`) | The FUN doors on the Level Fun side | Those doors (two-way: walked) | Original Wikidot and Level 283: the FUN doors in "The Lounges" (283 → the hotel, our lounge-and-function-room level) |
| Level 11 | **Gymnasium double doors painted with a tiger, a parrot and a giraffe** at the back of a parking-garage lot (own salt `SaltCityBlock + 15`, replanned over the top as the cinema was) | The exit door of a Level Fun **waiting-room lobby** | That door (two-way: walked) | Fandom: mascot doors in Level 11's parking garages; the lobby exit of the Party Rooms |
| The Hub | A door painted in crayon colours, "FUN =)" (proposed; the Hub plan decides) | A Level Fun FUN door | Two-way | The Hub links to many levels |

**Ways out**

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| Level Fun | A **reversed, out-of-focus poster** (mirror-written, blurred), about 1 per two plan blocks, in quiet rooms. Touch it | Level 4 | None (one-way: taken) | Wikidot 26: April Showers' escape to Level 4 |
| Level Fun | **Overboard**: climb the rail of an open deck and drop into the black water below | Level 7, surfacing in the open sea | None (one-way: fell) | Wikidot 26: "You can also jump overboard"; the ship's sea sightings |
| Level Fun | **Diving to the bottom of a deep ball pit** in a play room | Level 94, surfacing in the castle's ball pit | None (one-way: dived) | Fandom: ball pits that resurface you elsewhere; 94's castle is the other funhouse |
| Level Fun | The FUN doors | Level 5 | Two-way | (the Level 5 row) |
| Level Fun | The service stairs into the ceiling | Level 1 | Two-way | (the Level 1 row) |
| Level Fun | The waiting room's exit door | Level 11 | Two-way | (the Level 11 row) |

Level Fun ends up with two clean, walkable ways home (Levels 1 and 5) and one into the city. All three are rare and far
apart. The one-way exits are commoner but drop you somewhere bad: Level 4's offices, Level 7's open sea, or 94's
guarded castle. "Why would you want to leave? =)"

**Tells near the entrances in other levels.** The old Fandom version says an entrance is near when there is faint music, a red painted smiley or a lone balloon. Within 12 blocks of each entrance the dressing shows:
- a red "=)" on a wall;
- one deflated balloon on the floor;
- a little confetti;
- the Level 5 and Level 11 doors play `funtune` faintly through the wood.

**Burning the trap.** A lit torch held to a Level 0 poster burns it and its room's dressing away for good: the M.E.G. method in Wikidot 26. Level 0 is the home level, and a player who has learnt the lore can make it safe.

---

## 3. Design

### 3.1 The experience

You touch a cheerful poster and the room is suddenly full of balloons.
- **The first impression.** You are in a brass-doored elevator lobby on a ship that cannot be this big. A deck sign reads "DECK 4 · PARTY ROOMS 1–38 →". The corridor beyond has vinyl tiles in every colour and turns every dozen steps. Through the walls, a tinny "Happy Birthday" plays on a loop, far off, then nearer.
- **The tells.** The rooms with the music on have balloon arches over their doors. Inside, tables are laid with cake and cookies, and a pile of gifts stands in the corner. Three tall yellow figures stand around the head table, swaying, nodding to the beat, one of them holding a red balloon.
- **How it plays.** They have not seen you. They can barely see at all. Everything you need is on that table.

**Design goals, in order:**
1. **Unmistakably Level Fun from the first screenshot:** the classic yellow mural room, the birthday-party tables, real 3D balloons, streamers and cakes.
2. **A stealth larder.** The best food in the Backrooms sits in plain view, guarded by slow, nearsighted, pack-hunting things. Distance, sight lines and darkness are the skills; fire and a disguise are the tools.
3. **The lie as atmosphere.** The level smiles at you: =) on the walls, "altered" notes, hints that might be planted. Teach the player that **=) means a lie**.

### 3.2 Structure: blocks of 96, planned by id (the Level 37 pattern)

`WorldLayout.Fun.cs` (file name per CONTRACT.md). Plan blocks of **96 × 96** (3 × 3 cells), each planned once from
`(bi, bj)` and cached: `FunPlan(bi, bj) => (funPlans ??= new PlanCache<Tile[]>(32, PlanFunBlock)).Get(bi, bj)`.
Blocks count from `FunOriginX/Z` as `PoolBlockOf` does. The `FunPlanner` helper class holds `Floor`, `Wall`,
`Owner[]` per room, `Reserved[]` and `Zone[]`.

**The skeleton**

- **Promenades** run on the block lines (every 96).
  - 3 wide with a 3-high ceiling. Floor: multicoloured vinyl. Walls: a 1-high colour band, white tile skirting, pale cream above.
  - **They jog.** The centre line steps sideways by 2–4 blocks every 10–16 blocks (hashed per segment, both directions possible). No sight line along a promenade runs further than about 16 blocks. This answers the user's dislike of long straight halls and Fandom's "twisting corridors".
  - Promenades are always continuous; they are how you cross the level.
- **Elevator lobbies** sit at every block-line crossing (Wikidot: "the elevators are the hub").
  - 9 × 9, 4 high, carpeted in deep red with brass trim.
  - Two pairs of brass elevator doors (props; they never open; one says "OUT OF ORDER =)").
  - A deck sign pointing down each promenade, a ship's directory board and a potted palm.
  - **They are the region's arrival points:** safe-feeling, lit, and never a party room.
- **Inner halls** run on the 1/3 and 2/3 lines, each present with p = 0.6 (hashed). They are 2 wide, jog like the promenades and connect the squares.
- **Squares.** Each block holds 3 × 3 squares (as Level 37: `SquareLo = {9,35,67}`, `SquareHi = {29,61,86}`, about 20 × 20 inside). Each square is filled by one **suite** (table below). Every suite has at least one door onto a promenade or hall. `EdgeHall` is kept along the rim and region boundaries, as every region does.

**Suites** (weights per square)

| Suite | Weight | Size | What it is |
|---|---|---|---|
| **Party rooms** | 34% | 2–4 rooms of 8–12 × 8–14 off a short spur | Birthday party rooms (3.3). The bread and butter |
| **Mural room** | 10% | one room 12–18 × 10–14 | The classic image: yellow walls with 2×2-block cartoon murals, red race-track carpet, white tile skirting, a low bench along a wall, troffers. Often empty, always uncanny |
| **Themed room** | 9% | one room 14–20 square | "Popular movies or holidays" (Wikidot 26): **Movie night** (rows of plastic chairs facing a blank pull-down screen, a popcorn cart), **Halloween** (orange and black streamers, *real vanilla pumpkins*), **Tea party** (one long table of china for dolls) |
| **Play room** | 9% | 16–20 square, 5 high | Soft-play foam blocks, a climbing net, a slide (reusing Motion's `slide`), checkerboard mats and a **ball pit**. One ball pit in 4 is deep: the dive to Level 94 |
| **Bounce hall** | 6% | 20 square, 8 high | Fandom's warehouse in miniature: 1–2 inflatable bounce houses (3 × 3 × 3 blocks, walk inside), blowers droning, orange extension cords snaking to the walls, faded retro carpet, colder air |
| **Arcade** | 6% | 12 × 16 | Arcade cabinets (Motion's `arcade`) along the walls, an air-hockey table, sticky floor, half the screens dead |
| **Kitchen ("bakery")** | 5% | 10 × 14 | Stainless counters, ovens, cooling racks of cake tins full of something red. The Royal Velvet comes from here |
| **Gift room** | 5% | 8 × 10 | A cloakroom heaped with wrapped gifts: the belongings of the guests who never left (loot) |
| **Service corridors** | 8% | 2-wide loops behind other suites | "Crew only": grey riveted steel, pipes, dead lights. Linen carts, supply shelves of party goods. **The Carnivorous Balloons' corners** |
| **Open deck** | 4% | 6–8 wide × 20–30 along one side of a square | Teak planks, a white ship's rail, deck chairs, a life ring, caged deck lamps. Beyond the rail is black water 6–10 below under a black void 14 high, with sea wind. **Overboard → Level 7** |
| **Waiting room** | 2% (at most 1 per 2 × 2 blocks) | 10 × 8 | Fandom's lobby: grey carpet, rows of cushioned teal chairs, a magazine table, a reception desk behind glass, a white exit door: **→ Level 11** |
| **FUN doors** | 2% (at most 1 per 3 × 3 blocks) | a 6 × 6 vestibule | The Level 5 doors' partner: wooden double doors with raised F-U-N letters, a balloon arch over them, posters reading "COME JOIN US =)" |
| **Service stair** | 2% (at most 1 per 3 × 3 blocks) | a 3 × 8 stairwell | Steps climbing into the ceiling, confetti on every tread: **→ Level 1** |

**Rare set pieces** (replace a whole block's middle 3 squares when rolled):
- **The cloned hallway** (1 block in 8). One straight 2-wide hall, 90 blocks long, with the *same* party room repeated ten times along one side: identical tables, identical cake, identical balloon in the identical corner. It is Wikidot 26's "cloned thirty-eight times in a row". It is the one deliberate long sight line in the level, and it should feel wrong.
- **The Host's hall** (1 block in 12, only beyond 50% of the region's radius). See 3.6.

**Room doors**
- Party-room doorways are 2 wide, framed in white.
- A room with guests (3.5) wears a **balloon arch** over its door, and its wall speaker plays. A room without guests has a deflated balloon or two on the floor and half its lights off ("the party is over").
- This is the level's readable risk signal: **arch and music = guests.**

### 3.3 The party room, in real 3D

A birthday party room (8–12 × 8–14, 4 high), furnished by `PlanPartyRoom(room, ref rng)`.

**Walls and floor**
- **Walls:** one bright paint per room (orange, sky blue, lime, pink, sunshine yellow or lilac), white tile skirting (a real 1-voxel lip).
- **Floor:** vinyl in four-colour checks, red race-track carpet, or grey carpet.

**Tables**
- 1–3 rows of folding party tables, 2 blocks long, 3 blocks apart.
- Each table wears a plastic tablecloth (blue, green stripe, pink, yellow or red check) whose skirts hang 6 voxels down the sides. Steel tube legs and folding braces.
- **Chairs:** white, orange, lime, red or black plastic stacking chairs line both long sides, and one stands at the head. Some are pushed back or knocked over (5%).

**On the tables** (props in the block above, starting at y = −3)
- **The cake** sits on the head table. It is round, with frosting drips, a piped border and four striped candles that burn (light 4).
- **Plates and cups:** paper plates with yellow and blue rims, orange plastic cups, napkins.
- **Cookie plates.**
- **Sealed Almond Water bottles:** one table in 6. "Lots of cake and cookies and almond water."
- **Mess:** spilled cups and a red smear, on 1 table in 5.

**Overhead**
- **Balloons:** clusters of three against the ceiling over about 20% of the ceiling tiles, their strings hanging to head height. A few rest on the floor; some are tied to chair backs, floating at shoulder height.
- **Streamers:** crepe paper streamers cross the room at the ceiling every other row, sagging in a catenary, two colours twisted.
- **Bunting:** pennant bunting runs along the head wall. On one room in two the pennants spell **HAPPY BIRTHDAY**.
- **String lights:** coloured bulbs along the top of one or two walls.

**On the walls and floor**
- **Wall speaker** above the door.
- **Gifts:** a heap of 2–5 wrapped gifts in a corner.
- **Confetti** on the floor near the tables (a thin layer).
- **"=)" graffiti:** 0–2 red smileys on the walls, but only in rooms with guests. Sometimes they read "COME JOIN US =)" or "TIME 4 FUN =)".

**Variation**
- Each room's look is picked from its room id: paint, cloth colour, cake kind and balloon palette.
- The **cloned hallway** forces the same id for every room in it.

### 3.4 Light, fog, sound, temperature, stability

**Light**

| Place | Light |
|---|---|
| Promenades, lobbies | Existing fluorescent troffers every 4 blocks (`fluorescentlight-*`), so Level Fun hums the same quiet hum as Level 0. 1 in 12 flickers |
| Party rooms with guests | Troffers all on, plus string lights (light 5, warm), plus candles |
| Party rooms without guests | Half the troffers off; candles out |
| Mural room | Troffers only, bright and flat, like the photo |
| Bounce hall | High troffers, dim (light 8) |
| Service corridors, gift rooms | Dead or flickering: about 70% of floor below light 4 |
| Open deck | Caged deck lamps on the bulkhead every 8 blocks (light 9, warm); the water and void beyond are black |
| Host's hall | Chandeliers (existing) plus the Host's own gold glow |

**Darkness:** about 25% of floor is below light 4 (service halls, dead rooms, the deck's far side). Darkness helps you here: the Partygoers are nearsighted, and less so in the dark (3.5). It also hides the Carnivorous Balloons.

**Fog** (`AtmosphereSystem.Levels[15]` and zone overrides)
- **Level:** warm and dusty: `new(0.004f, 0.96f, 0.90f, 0.74f, 0f)`.
- **Open deck:** `new(0.03f, 0.05f, 0.07f, 0.12f, 0.2f)`, night sea with low fog over the water.
- **Host's hall:** golden: `new(0.008f, 0.95f, 0.80f, 0.40f, 0f)`.
- **Map colours:** promenades warm cream, party rooms by their paint, service halls grey, the deck dark teak, the hull white.

**Sound.** The user likes quiet hums; this level is loud only in the lore. Ours is a quiet hum with a party *somewhere else*.
- **The bed:** a relative loop at volume 0.3 whenever you are in the region, like `poolroom`. It is `fun/partydistant`, a 24 s seamless loop: an original cheerful party tune on a music box and toy organ, heavily low-passed as if through two walls, slightly detuned, under a faint crowd murmur.
- **The speakers:** each `fun-speaker-on` is a positional block ambient playing `fun/funtune`, a 20 s loop of the public-domain "Happy Birthday to You" melody on a tinny toy organ with tape warble. You hear it about 16 blocks off, so music on means guests.
- **Distant one-shots** (`Roster.SoundsByLevel[Fun]`, every 25–60 s, from a random direction 40–80 blocks away): a cheer, a party horn, a balloon pop, laughter (reusing Motion's `laughter`), and very rarely many voices singing "happy birthday" far away.
- **Local:**
  - the blower drone near bounce houses;
  - wind and hull-slap on the open deck;
  - the Host's wet breathing in its hall.
- **The Partygoers make almost no sound.** Canon: "extremely quiet and stealthy". Soft rubbery creaks underfoot, the creak of a balloon string. **What you hear when one has seen you** is a thin high whine (`gaze`), and then a line of chat in a familiar voice (3.5).

**Temperature:** 17 °C, the air conditioning set too cold as in every party venue (Fandom's "frigid air-conditioning"). The bounce hall is 13 °C, the open deck 11 °C and the Host's hall 26 °C, warm and wet. No heat hunger anywhere.

**Reality Stability** (`StabilityAt`, `case Fun`)

| Place | Stability |
|---|---|
| Promenades, lobbies | 0.75 |
| Waiting room | 0.9 (oddly calm) |
| Party rooms | 0.55 |
| Within 8 blocks of a Partygoer that sees you | −0.2 more |
| Service corridors | 0.5 |
| Open deck | 0.6 |
| Host's hall | 0.15 |

Party Fever (3.5) lowers your stability cap by fever × 0.5.

### 3.5 Partygoers (Entity 67)

**What they are in this mod.** The Wikidot creature:
- tall, yellow (rarely red, blue, green or white), with a carved, bloody "=)";
- noodle arms ending in lamprey mouths;
- a chest carapace hiding a centipede's clawed arms;
- new "interns" carry a red balloon.

They are the dominant life in Level Fun and appear **nowhere else** (decision 9.8).

**Two kinds of presence**
1. **Guests** stand in party rooms in groups of 2–4. Of party rooms: 40% have none, 35% two, 20% three and 5% four, picked from the room id.
   - They gather loosely around the head table, facing random ways, swaying and nodding to the music. Now and then one turns slowly to face another way. Half are interns with balloons.
   - **Spawning** is by `FunSystem`, not the director. When a player comes within 32 blocks of a guest room, its guests are spawned at their spots (never within the player's view). They are removed again when nobody is within 64.
   - **Persistence:** a small saved dict `(roomKey → guests alive, refillAtHours)`. A killed guest stays dead until a day later, when "we can easily create another hundred".
2. **Roaming packs**, from the director (`Roster.ByLevel[Fun]`): packs of 2–3 at band Approach and above. They walk the promenades and halls slowly, the leader wandering and the others following within 6 blocks. "You can never catch a Partygoer alone."

**Senses: nearsighted, poor hearing** ("Just because you see them, doesn't mean that they can see you")
- **Sight**, in a 140° cone in front of the head, with line of sight:
  - 12 blocks if you stand in light ≥ 8;
  - 7 blocks in light 4–7;
  - 4 blocks below light 4.
- **Modifiers:**
  - Sneaking multiplies the range by 0.6.
  - Holding a lit torch or lantern sets your light to its own, so a torch makes you visible at 12.
  - Sneaking right beside a clothed table (the hide-under-the-table nod to Escape the Backrooms) multiplies by 0.5 again.
- **Hearing:** only sprinting, landing from a height, fighting, a balloon popping or a party popper, within 6 blocks (16 for a popper). Walking and sneaking are silent to them.
- **The disguise** (decision 9.4). Wear a **party hat** *and* hold a **red balloon** and you look like an intern to anything further than 3 blocks away, unless you run, attack or eat at their table. Not running is the test: interns don't run.

**From noticed to hunted**
1. **The gaze.** A Partygoer that sees you stops, tilts its head 20° and stares for 1 s (the `gaze` animation and sound). Telepathy needs gaze.
2. **The voice.** You get a line of chat, pink, in "a familiar voice". It is signed with the name of another player online, else one of *Mum*, *Dad*, *your sister*, *an old friend*, rate-limited to one per 20 s:
   - "Come join us! =)"
   - "We have so much fun here!"
   - "There's cake! =)"
   - "It's your birthday! =)"
   - "Don't upset the host."
   - "Why would you want to leave? =)"
   - "They're dead! You're next! =)"
3. **The pack joins.** Every Partygoer within 16 blocks *that can see the one staring* joins the hunt within 1 s. A pack that cannot see its spotter does not join, so breaking sight lines between them matters.
4. **The hunt.**
   - **Speed:** they come at their run speed, slower than your sprint but faster than your walk (base 0.031, about 79% of a sprint at danger 0.9). "Run! Distance is your best chance."
   - **Losing you:** they lose you when none of them has seen you for 6 s. They walk to the last place you were seen, search for 12 s, then go back to the party. The room's music, which skipped when they started hunting, resumes.
   - **Doors:** they never open doors (the mod-wide rule), so a door shut behind you is the best escape.
   - **Fire:** `fearsFire` (Wikidot: they burn). Firesalt or a lit firepit makes a camp they will not enter.

**The latch, and Party Fever** ("If one latches on to you, its already too late"; "Tell anyone immediately if you are bitten. Seconds count!")
- **The latch.** Range 1.6, wound up for 700 ms, so it can be dodged like every other attack.
  - It does 5 damage (tier 1, after danger), and the arm holds you for 1.5 s at 30% walk speed.
  - Hitting the latching Partygoer breaks the hold early.
- **Fever.** Each latch adds **0.34 Party Fever** (a player attribute, `backrooms:funFever`, 0–1, saved in calendar hours).
  - **The 30-second window.** For 30 real seconds the new fever is *pending*. Applying any **poultice or bandage** (vanilla healing items) in that window cancels it: "seconds count".
  - **Effects while fever > 0:**
    - a yellow tint at the screen edges, growing with fever;
    - hunger +25% ("insatiable hunger", Fandom);
    - stability cap −fever × 0.5;
    - now and then a whispered "come join us" in chat.
  - **Decay:** fever falls 0.1 per in-game hour *outside* Level Fun; Almond Water takes off 0.1 more. Inside Level Fun it never falls.
  - **At 1.0 you transform.** You die with the message "**{player} joined the party =)**", and you wake in the Lobby as always (the anchor rule).
  - **What stays behind.** Where you fell, the items you dropped are gathered into a **wrapped gift** (`fun-gift`, a container), and a new **intern Partygoer**, with a red balloon, stands guard over it at the next party room. Its guest slot is permanent until killed. Your belongings are now the party's presents (decision 9.3).

**Berserker mode** (Wikidot rewrite)
- **The switch.** Below 50% health, the chest carapace swings open (`berserk`, with a heavy crack) and the centipede's clawed arms unfold.
- **While open:**
  - it no longer latches (no fever);
  - it claws instead: 8 damage at tier 2 after danger, attacks every 0.65 s, and it is 15% faster;
  - head hits take ×2 damage;
  - **fire damage ×3** (the centipede "burns fiercely and completely").
- **While closed:** the hide is fireproof (fire damage ×0.25).
- **On death:** black, sulphur-smelling smoke (particles). The body falls face down, and **the carapace pushes up as something small skitters out from under it** (a 2-second animation; optional separate entity, decision 9.9).

**Stats** (base, before `Danger.OfLevel(Fun) = 0.9`; see `docs/design/entity-difficulty.md`)

| | Base | In Level Fun (×danger) |
|---|---|---|
| Walk / run speed | 0.016 / 0.031 | 0.020 / 0.039 (79% of a sprint) |
| Health | 30 | 68, armour tier +1 |
| Latch | 2.5, tier 1, windup 700 ms, cooldown 1500 ms | 5.0, cooldown 1100 ms |
| Berserk claws | 4.0, tier 2, windup 450 ms, cooldown 900 ms | 8.0, cooldown 650 ms |
| Bounty | 1.0 + 2.5 d gears | about 3.3 rusty gears |
| Drops | party hat (40%), red balloon (interns), 0–1 rusty gear | |

**Counters, in one list** (for the handbook):
- distance;
- darkness and sneaking;
- breaking sight lines between them;
- a shut door;
- Firesalt or a firepit;
- the disguise;
- a poultice within 30 s of a bite;
- fire through the open carapace.

**Implementation.** A new AI task `backrooms-partygoer` (`src/Entities/AiTaskPartygoer.cs`):
- **States:** party/patrol, gaze, hunt, search, return, berserk.
- **Reuse:** `Senses` (sight cone, light, sneaking), `Wards` (fearsFire) and `EntityBehaviorMenace` (despawn out of sight, encounter end). `AiTaskMenace` has no gaze or pack-by-sight; extending it would complicate every other entity.

### 3.6 Other dangers and set pieces

- **Carnivorous Balloons (Entity 110), in the dark.**
  - **Where:** in service corridors and dark corners (light < 4), about one per 40 dark floor tiles. Each looks like a tied balloon floating at chest height, but it is tied to nothing, and its ribbon is a **curly ribbon**, not a string.
  - **Touch:** walking into one, or right-clicking it: 3 damage, and you are "paralysed" (20% speed) for 3 s.
  - **Popping it** (breaking the block): ammonia gas, 1 damage per second for 4 s within 2 blocks, and a cough. Its food sac drops 1–2 **vanilla onions** ("onions or garlic").
  - **Poking it:** with anything long (a spear, or a 2-block reach from a stick held out) it stings the air harmlessly. That is the canon advice: poke them with a long stick.
- **Booby-trapped gifts** ("booby-trapped party favors"). One gift in 5 is a **party popper**: opening it bangs (a noise spike to `MenaceSystem`, heard by Partygoers within 16), showers confetti and contains nothing.
- **The Host** (decision 9.7). In the Host's hall, a 30 × 30 ballroom 8 high:
  - **The room:** a parquet floor, round banquet tables, a stage with an inflatable throne, chandeliers.
  - **The Host:** the **Party Host** fills the middle of the ceiling. It is a golden fried egg 3 blocks across: a white rim, a gold yolk dome bearing one huge eye and a mouth together, and drips hanging. It never moves; its eye follows you.
  - **The pool:** beneath it a shallow golden basin (`fun-lucapool`) collects its **LUCA tears**.
  - **Guests:** four guests always attend (no 40% empty roll).
  - **"Don't upset the host."** Breaking any block in the hall, any fight noise, or taking tears while a guest can see you **alarms the hall**. Every Partygoer within 64 blocks hunts you (band Threshold) for 3 minutes, as Motion's castle alarm does.
  - **The reward.** One bottle of LUCA tears per in-game day per Host ("spinach for Popeye"). Drinking it: +4 max health and +25% melee damage for one in-game day, and +0.3 stability.

### 3.7 What there is to find (loot and vanilla hooks)

Level Fun is **the larder you steal from**: more food than any level but 94, all of it in rooms watched by Partygoers.

| Find | Where | What it does |
|---|---|---|
| **Birthday cake** (`fun-cake-birthday`, 4 slices) | Head table of most party rooms | Right-click cuts a slice: `fun-cakeslice-birthday`, satiety 260, Grain. "Tastes faintly of rust." Safe |
| **Red Velvet cake =)** (`fun-cake-velvet`) | One party cake in 5; every kitchen's racks | `fun-cakeslice-velvet`: satiety 420, Protein, but −0.2 stability and +0.2 Party Fever. Handbook: **DO NOT EAT** |
| **Cookie plates** | 1–2 per party room | `fun-cookie` ×3: satiety 60 each, Grain |
| **Almond Water** (existing, sealed) | One table in 6 | As everywhere. Open cups of punch are props only (Fandom: never drink from an open cup) |
| **Candles** | On the birthday cakes | Salvaging a cake's candles gives 2–4 `game:candle` (vanilla) |
| **Gifts** (`fun-gift-*`, containers) | Party rooms, gift rooms | Wanderers' belongings: canned food, crackers, bandages, a knife, twine, rusty gears, a wanderer note; 1 in 5 is a popper. Uses the existing loot rules (`PickedOverShare(Fun) = 0.2`: the party keeps its presents) |
| **Tablecloths** | Salvaging a table | 1 linen (`block:game:linen-normal-down`) for poultices, the vanilla way |
| **Party supplies** (`fun-supplyshelf`, container) | Service corridors | Candles, `game:flaxtwine` (balloon string), party hats, red balloons, confetti, now and then Firesalt (the crew's) |
| **Party hat** (`fun-partyhat-{stripes,dots}`) | Supply shelves, Partygoer drops | A head-slot clothing item. Half of the disguise |
| **Red balloon** (`fun-balloon-red`) | Interns' drops, supply shelves | A held item. The other half of the disguise |
| **Onions** (`game:vegetable-onion`) | Popped Carnivorous Balloons | Vanilla food |
| **Pumpkins** (vanilla) | Halloween rooms | Vanilla food |
| **Confetti** (`fun-confetti` handful) | Everywhere | Places a thin confetti layer: a path marker, the party's own chalk |
| **LUCA tears** | The Host's pool | See 3.6 |
| **Salvage** | Furniture | Arcade cabinets as in 94 (wire, glass, brackets); stainless counters and ovens give `metalbracket` and `scrapwire`; folding tables give `metalbracket`; plastic chairs give nothing |

**Wanderer notes here are altered.**
- **Altered notes** in Level Fun's gifts mark the nearest *party room with guests* as a refuge, and their text carries a "=)". Example: "Level Fun is completely safe =) the party room is a refuge".
- **Real notes** (without =)) mark the nearest exit.
- **The lesson:** "**=) means a lie**", taught by the handbook and by experience. Implemented as a `WandererNote` variant (`wanderernote-altered`) whose `NearestRefuge` is replaced by the nearest guest room.

### 3.8 Runtime rules (`src/Regions/FunSystem.cs`)

A server tick of 500 ms over players in the region (`layout.LevelAt(...) == FunLevel`), plus event hooks:
- **Guests:** spawn and despawn per room, with the saved alive counts.
- **Party Fever:** latch hook, pending window, poultice cancel, effects, decay (everywhere, not only in Fun), and transformation on death (gift box plus intern).
- **The disguise check:** hat slot plus held balloon, for `AiTaskPartygoer`.
- **Cakes:** right-click cuts a slice; the block steps from `-4` to `-1` and then to the empty board.
- **Inflatable floors bounce:** landing on `fun-inflatable-floor` with downward speed > 0.2 sets the motion up to 0.25. Walking on it is at 0.7 speed (Fandom's sinking floor, made fun instead of deadly).
- **Carnivorous Balloons:** a collide/interact behaviour (sting) and a break hook (gas).
- **Poppers:** gift open hook → noise spike via `MenaceSystem`'s noise input.
- **The Host's alarm:** `DidBreakBlock` and noise in the hall, as `MotionSystem` does for the castle.
- **Torch-burning:** Level 0 posters and their dressing (a block interaction with a lit torch held).
- **Music skips:** the speakers in a room whose guests are hunting stop (client: `AtmosphereSystem` reads a room-state flag, or the speaker block swaps `-on` to `-off`).

---

## 4. Asset manifest (`tools/gen_fun.py`)

Everything new is prefixed `fun-` and lives in `block/fun/`, `blocktypes/fun/`, `itemtypes/fun/`,
`shapes/block/fun/`, `sounds/ambient/fun/`, `sounds/entity/partygoer/`. Textures are 32 × 32 (`texlib.S`) unless
stated; shapes are in voxels (16 per block, `bx(name, from, to, tex)` as in `gen_motion.py`). "{side}" means the four
orientations `north|east|south|west` (Pier-facing). "Real 3D" means the detail is elements, not paint.

### 4.1 Surfaces (cube blocks)

| Code | Texture | Notes |
|---|---|---|
| `fun-vinyl-{a,b,c,d}` | 2 × 2 tiles of 16 px per face in the six party colours (red `#D64541`, yellow `#F2C641`, blue `#3C7DD9`, green `#4CAF6A`, orange `#F08A3C`, purple `#8E5BC4`), 1 px darker grout, scuffs, a sheen streak; a–d are different arrangements | Promenades, halls, party rooms. Floor |
| `fun-racecarpet` | Red `#B3201E` loop-pile carpet with darker race-track lanes `#8A1512`, dashed yellow centre lines `#E8C43A`, two tiny toy cars (blue, yellow) per tile; tiles seamlessly | The mural room (classic image) |
| `fun-retrocarpet` | Faded 1990s carpet: teal ground, pink and yellow squiggles and triangles, worn | Bounce hall, arcade |
| `fun-checkermat-{a,b}` | Foam play mats, 16 px squares red/blue and yellow/green with jigsaw edges | Play rooms (reuse `FloorKind.Checker` if it reads right) |
| `fun-paint-{orange,sky,lime,pink,yellow,lilac}` | Eggshell paint, subtle roller texture, faint scuffs at chair height | Party room walls |
| `fun-paint-{colour}-skirted-{side}` | As above, plus a **real 3D** white tile skirting element `(0,0,15)→(16,3,16)` on the room side (white 8 px tiles, grey grout) | The wall's lowest block |
| `fun-promwall`, `fun-promwall-band-{side}` | Cream paint; the band variant has a 1-block-high colour stripe (four-colour checks) and the skirting lip | Promenade walls |
| `fun-mural-{mouse,hotdog,cheese,stork}-{tl,tr,bl,br}-{side}` | **Original** cartoon murals on sunshine yellow `#F3E27A`, each 64 × 64 over 2 × 2 blocks. A grey mouse in a green jumper and orange trousers holding a red cup; a grinning yellow man in a white vest and blue jeans with a hot dog; an orange cheese block with arms kicking a football; a pink stork in a dark jacket and top hat. Flat-shaded, black outlines, slightly naive | The mural room. Paint is right here: murals are paint |
| `fun-hull`, `fun-hull-porthole-{side}` | White ship paint over steel, rivet rows every 8 px, rust weeping from two rivets. The porthole variant has a **real 3D** brass ring (8 elements, inner 10 voxels across, 1.5 proud) around recessed dark glass `#0B1018` with a faint reflection | The rim |
| `fun-steel`, `fun-steel-sign-{crewonly}-{side}` | Grey riveted steel `#7B8288`, scuffed; a stencilled "CREW ONLY" plate variant | Service corridors |
| `fun-deckplank` | Teak planks `#9A6A3E` with black caulk seams, salt-bleached | Open deck |
| `fun-nightvoid` | Near-black `#05070B` with 2–3 dim star texels | The deck's ceiling 14 up |
| `fun-parquet` | Herringbone parquet, honey wood | Host's hall |
| `fun-lobbycarpet` | Deep red carpet `#6E1018` with a gold diamond motif | Elevator lobbies |

Ceiling tiles and lights reuse Level 0's drop ceiling and `fluorescentlight-*` (same quiet hum).

### 4.2 Props (shapes)

| Code | Shape (voxels) | Behaviour |
|---|---|---|
| `fun-balloons-ceiling-{mixed,pastel,red}` | Three balloons in the block's top half, each an ellipsoid of 3 elements (core 6×7×6, caps 4×1×4 above and below) plus knot 1×1×1, at about (3–9, 9–16), (8–14, 8–15), (4–10, 10–16). Strings 0.25 × 8–12 hanging, each in 2 segments bent 6°. Latex texture with a white highlight spot | Non-solid, small selection box; breaking pops (sound, no drop) |
| `fun-balloons-floor-{mixed,pastel}` | Two balloons resting on the floor, one half-deflated (squashed 7×4×6); strings lying in 3 flat segments | Non-solid |
| `fun-balloon-tied-{red,yellow,blue,green,pink}` | One balloon on a string rising from y 0 to the balloon at y 22–30 (allowed above 16) | Tied to chair backs and stair rails |
| `fun-balloonarch-{l,r}-{side}` | A quarter-arc each of 6 balloons (5×5×5 approximations) climbing from the floor beside the doorway to its top, alternating colours | Marks rooms with guests |
| `fun-streamer-{redyellow,bluegreen,pinkpurple}-{ns,ew}` | A twisted crepe band 1.5 wide × 0.25 thick crossing the block, in 4 segments rotated ±8–15° to sag 3 voxels at the middle (y 16 → 13); alternate segments in the two colours | Ceiling level, non-solid |
| `fun-bunting-{h,a,p,y,b,i,r,t,d,blank}-{side}` | A string 16 × 0.25 at y 15 along the wall face, with 3 pennants, each a stepped triangle (4×1, 3×1, 2×1, 1×1 × 0.25), colours cycling; the letter variants carry one letter on the middle pennant (white, bold) | Spells HAPPY BIRTHDAY along a head wall |
| `fun-table-{blue,greenstripe,pink,yellow,redcheck}-{a,b}-{side}` | One block of a 2-block folding table: top (0,12,0)→(16,13,16) white plastic, tablecloth top 0.2 proud with skirts (16 × 6 × 0.25) on the long sides and on the end (part a or b), steel tube legs (1×12×1) and a folding brace at that end | Solid to y 13 |
| `fun-tableware-{plates,cups,mess}` | Sits on a table; elements start at y −3. Plates: 3 paper plates 5×0.25×5 (yellow or blue rims), napkins. Cups: 3 orange cups 2×3×2 with a rim. Mess: two cups on their sides, a smeared plate, a red stain decal, a little confetti | Non-solid decoration |
| `fun-cake-{birthday,velvet}-{4,3,2,1,0}` | On a table (y −3 up). A cardboard board 12×0.5×12; a round cake tier about 10 across and 6 high as an octagon (10×6×6 plus 6×6×10); a frosting cap 0.6 thick; 6 drips (1×1.5×0.3) down the sides; a piped bead border; birthday: 4 striped candles 0.6×2.5×0.6 with flames 0.6×0.8×0.6 (glow, block light 4). Slices are removed per quadrant (each quadrant is its own elements); 0 is an empty board with crumbs. Velvet: red sponge `#7A1420` showing at the cuts, pink-white frosting, "=)" piped in red on top, no candles, a cake knife beside it | Right-click cuts a slice (3.8) |
| `fun-cookieplate-{3,2,1,0}` | A paper plate 8×0.3×8 with up to 3 cookies (3×0.6×3, chocolate chips in the texture) | Right-click takes a cookie |
| `fun-chair-{white,orange,lime,red,black}-{side}` | Plastic stacking chair: shell seat 12×1×12 at y 8, curved back of 3 stacked boxes 12×3×1 tilted −8°, 4 chrome legs 0.8×8×0.8 | Solid to the seat |
| `fun-chairtipped-{colour}-{side}` | The same chair on its back | Rare |
| `fun-gift-{red,blue,green,yellow,purple}-{small,tall}` | Box 10×8×10 or 8×12×8; ribbon cross of four slabs 1.5 wide, 0.2 proud, wrapping around; a bow of two loops (3×2×1 rotated ±30°) and a knot 1×1×1. Paper patterns: stripes, dots, stars | Container (4 slots), loot; 1 in 5 popper (3.6) |
| `fun-speaker-{on,off}-{side}` | Wall speaker 6×8×4 on a bracket, black grille texture | `-on` carries the `funtune` block ambient |
| `fun-stringlights-{side}` | Wire 16×0.25×0.25 sagging in 2 segments along the top of a wall, 4 bulbs 1×1.5×1 (red, green, blue, yellow; glow) | `lightHsv` about [5,4,6] |
| `fun-poster-{time4fun,happybday,comejoin}-{side}` | Paper 12×10×0.2 with one corner curling (an element rotated 20°), tape strips 2×1×0.3 at the corners. time4fun: the Wikidot poster (an orange clock, "4 Fun =)" in four colours, a rainbow banner) plus a red handprint | Decoration in Fun; the Level 0 trap uses `time4fun` (below) |
| `fun-poster-trap-{side}` | Identical to `fun-poster-time4fun` | Threshold `funposter` (Level 0), one-way; burnable with a torch |
| `fun-poster-reversed-{side}` | Same shape; the texture is a party poster **mirrored and blurred** (2-px box blur), so the eye won't focus on it | Threshold `funposter-reversed` → Level 4, one-way |
| `fun-smiley-{1,2,3,4}-{side}` | Wall plate 0.1 thick with red paint: three hand-daubed "=)" (6–14 voxels tall) with drips, and one "COME JOIN US =)" | Writing is paint |
| `fun-inflatable-wall-{yellow,blue,red}-{side}` | Puffy vinyl wall: 4 horizontal tubes 16×3.5×4 stacked with 0.5 overlap, alternate tubes shifted 0.5 out | Solid |
| `fun-inflatable-tower-{colour}` | A column of 3 stacked rounded drums (14×5×14 with 12×5×16 and 16×5×12 crosses) and a cone top of 3 shrinking boxes with a pennant | Bounce-house corners |
| `fun-inflatable-arch-{side}` | An arched entrance: two tower stubs and a curved top of 5 tube segments | |
| `fun-inflatable-floor` | Cube, top quilted vinyl, collision 12 high | Walk 0.7; bounces (3.8) |
| `fun-blower-{side}` | A blower housing (an octagon of 2 boxes, 8×8×10) on a stand, with a fabric tube 4×4×12 to the inflatable | Block ambient `blower` |
| `fun-extensioncord-{straight,corner,plug}-{side}` | An orange cable 1×1 voxel lying on the floor (straight, a rounded corner of 3 segments, or ending in a plug 2×1.5×1.5) | Non-solid |
| `fun-foam-{red,blue,yellow,green}` | Soft-play block: a 14×14×14 core with 1-voxel bevel crosses (16×12×12, 12×16×12, 12×12×16) | Solid, `Cloth` |
| `fun-net-{side}` | Climbing net: rope strands 0.5 thick every 4 voxels on a plane, knots 1×1×1 | `climbable: true` |
| (reused) `ballpitfill`, `ballpit`, `slide`, `arcade` from `gen_motion.py` | | Ball pits, slides, arcades |
| `fun-airhockey-{a,b}-{side}` | A 2-block table: top 16×2×16 at y 10, raised rails 1×1, a puck and two strikers | Salvage: metalbracket |
| `fun-popcorncart-{side}` | A red cart 12×20×10 with a glass box on top full of popcorn texture, two wheels | Movie room |
| `fun-screen-{l,m,r}-{side}` | A pull-down white screen on a black roller bar, 3 blocks wide, 0.25 thick | Movie room |
| `fun-counter-{side}`, `fun-oven-{side}`, `fun-caketins-{side}` | Stainless counter 16×14×12 with kickplate; black oven with a window; a cooling rack 14×1×10 on legs holding three tins 5×2×5 of red sponge | Kitchen; the tins drop `fun-cakeslice-velvet` |
| `fun-waitingchair-{side}` | Two cushioned teal seats on a chrome frame with armrests, one block wide | Waiting room |
| `fun-reception-{side}` | Desk 16×12×10 with a glass screen 16×12×0.5 above and a slot | Waiting room |
| `fun-magazinetable` | Low table 12×6×12 with fanned magazines | Waiting room |
| `fun-door-exit-{lower,upper}` | A plain white door with a push bar and a small sign, via `door_block` (gen_deep) | Threshold `funlobbydoor` ↔ Level 11, two-way |
| `fun-door-fun-{l,r}-{lower,upper}` | Wooden double doors with **raised plywood letters** F, U, N (2 voxels proud, red, yellow, blue; F and U on the left leaf, N on the right) and brass handles | Threshold `fundoor` ↔ Level 5, two-way; used in both levels |
| `fun-door-mascot-{l,r}-{lower,upper}` | Green-painted gym double doors with push bars, small square windows and painted tiger, parrot and giraffe (paint) | Threshold `mascotdoor`, Level 11 side |
| `fun-elevator-{l,r}-{lower,upper}-{side}` | Brass elevator doors (2 blocks wide, 3 high in total with the frame), an arrow dial above, "OUT OF ORDER =)" sign variant | Decoration |
| `fun-decksign-{side}` | Brass plate 12×5×0.5: "DECK 4 · PARTY ROOMS 1–38 →" | Decoration |
| `fun-shiprail-{side}` | White steel railing: posts 1×16×1 every 8, rails at y 6, 11, 16, 1 thick | `Bars`-style, solid |
| `fun-lifering-{side}` | A ring of 8 boxes about 12 across, 2.5 thick, red and white quarters, a rope loop | Decoration |
| `fun-deckchair-{side}` | A wooden slatted lounger, 2 blocks long (`-a/-b`) | |
| `fun-decklamp-{side}` | Caged bulkhead lamp 4×6×3, light [6,3,9] | |
| `fun-linencart`, `fun-supplyshelf-{side}` | A canvas cart on castors; a steel shelf of boxes (balloon packs, hats, candles) | Shelf is a container: party supplies |
| `fun-cballoon-{red,yellow,blue,green,pink}` | As `fun-balloon-tied` but floating at y 16–24 with nothing below; the ribbon is a **curly ribbon** (a helix of 6 small boxes 1×1.5×0.3 rotated 60° apart) hanging 16 voxels | Carnivorous Balloon (3.6); non-solid |
| `fun-confetti` | A layer 16×0.5×16 with a transparent texture of multicoloured flecks | Placeable from the handful |
| `fun-lucapool` | A basin 16×2×16 with a gold liquid top, light [7,6,8] | The Host's pool (bottle → tears once a day) |
| `fun-hostthrone-{side}` | An inflatable throne, purple and gold, 2 blocks tall | Host's hall stage |

**Budget:** keep each prop ≤ 14 elements. Balloon density targets 20% of party-room ceiling tiles and 10% of floor tiles,
with string lights on 1–2 walls. Check chunk mesh time in phase 2.

### 4.3 Items (`itemtypes/fun/`)

| Code | Kind | Values |
|---|---|---|
| `fun-cakeslice-birthday` | Food | Grain, satiety 260 |
| `fun-cakeslice-velvet` | Food | Protein, satiety 420; on eaten: stability −0.2, Party Fever +0.2 (item class `BackroomsVelvetCake`) |
| `fun-cookie` | Food | Grain, satiety 60 |
| `fun-balloon-red` | Held item | Shape: the tied balloon on a string held in the hand. Half of the disguise |
| `fun-partyhat-{stripes,dots}` | Clothing, head slot | A cone hat 6×9×6 with an elastic and a pompom; the other half of the disguise |
| `fun-lucatears` | Drink (bottle) | +4 `maxhealthExtraPoints` and +25% `meleeWeaponsDamage` for 1 in-game day; +0.3 stability (item class `BackroomsLucaTears`) |
| `fun-confetti` | Placeable | Places `fun-confetti` |
| `wanderernote-altered` | Note variant | The lying note (3.7); text from lang |

### 4.4 Entities (`tools/gen_fun_models.py` importing `rig` and the helpers of `gen_models.py`; entity JSON from `gen_fun.py` using `gen_entities.py`'s builders)

**`backrooms:partygoer`** (shapes `partygoer` and `partygoer-intern`; textures `partygoer` plus variants `-red`, `-blue`, `-green` and `-white`, 3% each, made the way the Hound and Death Rat variants are)

Model brief (rig conventions: 16 px per block, model faces −X, left is +Z, feet at y = 0):

| Part | From → size (px) | Parent | Notes |
|---|---|---|---|
| Pelvis | (−2, 12, −3.75) 4 × 3 × 7.5 | – | Pivot (0, 13.5, 0) |
| Torso | (−2, 15, −3.5) 4 × 10 × 7 | Pelvis | A Gumby slab: as wide as the head, no neck |
| CarapaceL / CarapaceR | (−2.4, 17, 0) 0.6 × 6 × 3.25 (mirrored) | Torso | Chest plates hinged at their outer edges (pivots z = ±3.5); rest closed, berserk swings them 100° outward |
| Cavity | (−1.6, 17.5, −3) 0.4 × 5 × 6 | Torso | Dark maroon inside, seen only when open |
| ClawArmL / ClawArmR | (−1.5, 18, 0.5) 1 × 1 × 5 plus a Claw 1.5 × 1 × 2 | Torso | Folded inside (rest pitched back 80°); berserk unfolds them forward. Chitin brown-black `#2B1A12` |
| Head | (−2, 25, −3.25) 4 × 9 × 6.5 | Torso | Continuous with the torso. The **face on −X**: two tall slit eyes and a wide grin, carved: dark maroon `#3A0606` insets 0.3 deep (separate thin parts set into a 0.3 recess of the face), blood drips below each |
| HeadTop | (−2, 34, −3.25) 4 × 1.5 × 6.5 | Head | Rolled −15° about X so the top slopes down to the right (the Gumby slant of the canon sketch) |
| ThighL / ThighR | (−1.75, 6, 0.25) 3.5 × 7 × 3.5 | Pelvis | Thick and blocky |
| ShinL / ShinR | (−1.75, 0, 0.25) 3.5 × 6 × 3.5, foot lip (−2.75, 0, 0.25) 1 × 1.5 × 3.5 | Thigh | Barely a knee |
| Arm1L … Arm4L (+R) | (−0.75, 21, 3.5) 1.5 × 5 down, then 1.4, 1.3, 1.2 thick, lengths 5, 5, 5, 4 | Torso → chain | Noodle arms in 4 links that curl in waves; they hang to the knees (19 px) |
| SuckerL / SuckerR | 2.2 × 1.2 × 2.2 disc at the arm's end, and 4 teeth 0.4 × 0.6 × 0.4 around the rim | Arm4 | The lamprey mouth: inner `#5A0A14`, a ring of hooked teeth `#E8E0C8` painted on the end face |
| BalloonString (intern) | 0.25 × 14 × 0.25 rising from SuckerR | Arm4R | Gentle sway |
| Balloon (intern) | Core 4 × 5 × 4, caps 3 × 1 × 3, knot 1 × 1 × 1 | String | Red `#C8141E` with a highlight |

- **Overall:** about 36 px (2.25 blocks) tall. Hitbox 0.8 × 2.2, eye height 2.0.
- **Skin:**
  - colours: yellow `#E8C82A` with leathery mottling `#C9A41E` and sheen `#F6E27A`;
  - blood: smears `#7A1010`/`#A01818` round the mouth, down the chest and on the suckers;
  - texture: fine wrinkle noise (it is leather, not plastic).
- **Variants:** red `#C8332B`, blue `#2F6FD0`, green `#3FA34D`, white `#E8E8E0` (bone).

**Animations** (every keyframe names every part, via `full()`):
- `idle` ("party"): sways ±4° side to side; the head nods to an unheard beat every 1.2 s; arms float in slow phase-shifted waves (each link lags the last); the balloon bobs. 60 frames.
- `walk`: the deliberate wading gait (Fandom). Stiff legs, torso leaning back 4°, arms trailing and curling. 48 frames.
- `run`: hunched 15° forward, arms reaching ahead and rippling, suckers pulsing (scale 1 ↔ 1.15). 28 frames.
- `gaze`: all sway stops; the head tilts 20° and holds. 20 frames, held at end.
- `latch`: both arms whip forward in 6 frames, suckers clamp (scale), hold, pull back. 24 frames.
- `berserk`: the carapace swings open over 12 frames and the claw arms unfold; ends held.
- `berserkidle`: claws twitch in short bursts.
- `claw`: two fast slashes. 16 frames.
- `hurt`: almost nothing, a 3° head jolt ("never flinched").
- `die`: topples forward face down; the carapace heaves twice; one leg twitches; held.

**Sounds** (`sounds/entity/partygoer/`):
- `step1-3`: soft rubbery creak, very quiet;
- `gaze`: thin high whine, 1.5 s;
- `latch`: wet suction plus crunch, 0.8 s;
- `carapace`: heavy crack plus hiss, 1 s;
- `claw`: a skittering slash;
- `die`: hiss and sizzle, 2 s.

**AI and stats:** the task `backrooms-partygoer` (3.5). JSON built like `motion_body(...)`: health 30, `taskai` with the new task, `backrooms-menace` behaviour with `huntSeconds 90`.

**`backrooms:lureballoon`** ("Avoid balloons floating on their own")
- **Model:** a red balloon (core 4 × 5 × 4) with a 16 px string; no texture variants.
- **Behaviour:** a *glimpse* entity (`Roster.ByLevel[Fun]`, Heartland and up, Encounter Glimpse). It floats at head height at a corridor's end, then drifts away round a corner toward the nearest guest room when you look at it, and is gone out of sight.
- **Movement:** flying like the Deathmoth (`AiTaskMoth`'s movement, or a simple flying drift).

**`backrooms:partyhost`** (decision 9.7)
- **Model:** a flattened white disc 48 px across and 4 px thick, a gold yolk dome 24 × 10 × 24, one huge eye 8 × 6 (iris dark red, glow 40) fused with a lipless mouth 10 × 4 below it, and 6 hanging drips 1 × 4–8 × 1.
- **Animations:** `idle` (a slow pulse, the eye tracking via the head part's yaw and pitch), `weep` (drips lengthen), `upset` (the mouth opens, a shudder).
- **Behaviour:** no movement, no AI task; `FunSystem` aims its eye and runs the alarm. Immortal (`immortal: true`).
- **Sounds:** `hostbreath` loop, `hostweep`, `hostupset` (a long low wail).

### 4.5 Sounds (`tools/gen_fun_sounds.py`, importing `RATE`, `band`, `place`, `reverb`, `seconds`, `vowel` and `write` as `gen_level_sounds.py` does; mono OGG, written in chunks)

| File | Length | Character |
|---|---|---|
| `ambient/fun/partydistant` | 24 s seamless loop | An *original* cheerful 3/4 party tune on a music box and toy organ, low-passed at about 600 Hz as if through two walls, detuned −15 cents, under a faint crowd murmur (vowel noise). Peak 0.10 |
| `ambient/fun/funtune` | 20 s loop | "Happy Birthday to You" (public-domain melody) on a tinny toy organ through a small speaker (band-passed 400–3500 Hz), tape warble ±8 cents at 0.7 Hz. Peak 0.25 |
| `ambient/fun/funtune-skip` | 1.5 s | The tape catching and stopping (when guests start hunting) |
| `ambient/fun/blower` | 6 s loop | Blower fan: broadband rush plus a 140 Hz motor whine. Quiet |
| `ambient/fun/deckwind` | 12 s loop | Low wind, gusts, water slapping a steel hull far below |
| `ambient/fun/cheer` | 3 s | A distant small crowd's cheer, reverberant |
| `ambient/fun/partyhorn` | 1.2 s | One party blowout horn, far off |
| `ambient/fun/balloonpop` | 0.4 s | A pop plus a short room reflection (also used for breaking balloons) |
| `ambient/fun/popper` | 1.5 s | A party-popper bang and a confetti rustle |
| `ambient/fun/singing` | 9 s | Many voices singing a wordless "happy birthday" far away (vowel chorus), very reverberant, rare |
| `ambient/fun/hostbreath` | 8 s loop | Slow, wet, enormous breathing |
| `ambient/fun/hostweep`, `hostupset` | 3 s, 4 s | A dripping sob; a long low wail |
| `ambient/fun/cballoon-sting`, `cballoon-gas` | 0.6 s, 2 s | A rubber squeak and whip; an ammonia hiss with a cough |
| `entity/partygoer/*` | as 4.4 | |

Reused: Motion's `laughter` as a distant one-shot; the existing hum through the fluorescent lights.

### 4.6 Lang (`assets/backrooms/lang/en.json`, Fun's block only)

| Key | English |
|---|---|
| `level-15` | Level Fun =) |
| `levelhint-15` | They are slow and nearsighted. Distance is your best chance. |
| `levelname-fun` | Level Fun |
| `funposter` | You touch the poster. Suddenly the room is full of balloons. |
| `funposter-reversed` | The letters swim into focus under your hand. |
| `funposter-burnt` | The poster curls, blackens and is gone. |
| `funstairs` | The steps climb into the ceiling, and on, through confetti. |
| `fundoor` | Music, and the smell of cake. |
| `mascotdoor` | The doors swing shut behind you on a quiet room full of chairs. |
| `overboard` | Black water closes over you. |
| `funballpit` | You push down through the balls, and down, and down. |
| `fun-latched` | It has latched on to you. Seconds count! |
| `fun-fever-pending` | The bite burns. A poultice, now! |
| `fun-fever-cleared` | You bind the bite in time. |
| `fun-fever` | You are so hungry. Everything smells of cake. |
| `fun-joined` | {0} joined the party =) |
| `fun-voice-1` … `fun-voice-7` | Come join us! =) / We have so much fun here! / There's cake! =) / It's your birthday! =) / Don't upset the host. / Why would you want to leave? =) / They're dead! You're next! =) |
| `fun-voice-from` | {0}'s voice: {1} |
| `fun-voice-familiar-1` … `-4` | Mum / Dad / your sister / an old friend |
| `fun-hostupset` | The Host is upset. |
| `fun-disguised` | In a party hat, with a red balloon, you could pass for one of them. Don't run. |
| `block-fun-*`, `item-fun-*` | Names: "Birthday Cake", "Red Velvet Cake =)", "Slice of Birthday Cake", "Slice of Red Velvet Cake =)", "Cookie", "Party Hat", "Red Balloon", "LUCA Tears", "Handful of Confetti", "Wrapped Gift", "Party Supplies", "Balloons", "Streamer", "Bunting", "Party Table", "Plastic Chair", "Wall Speaker", "String Lights", "TIME 4 FUN =) Poster", "Reversed Poster", "Inflatable Wall", "Blower", "Extension Cord", "Soft-Play Block", "Climbing Net", "Ship's Rail", "Life Ring", "Deck Lamp", "Ship's Hull", "Porthole", "FUN Doors", "Gym Doors", "Elevator Doors", "Balloon" (the carnivorous one is just "Balloon") |
| `itemdesc-fun-cakeslice-velvet` | Sweeter than it should be. M.E.G. archives: DO NOT EAT. |
| `itemdesc-fun-lucatears` | Golden, faintly warm. "Think of it as spinach for Popeye." |
| `creature-partygoer`, `item-creature-partygoer`, `deadcreature-partygoer` | Partygoer / Partygoer / Dead Partygoer |
| `creature-lureballoon` | Balloon |
| `creature-partyhost` | The Host |
| `wanderernote-altered-text` | Level Fun is completely safe =) There is a party in the room I marked. Come join us! |

---

## 5. Code plan

### 5.1 Files Fun owns (names as CONTRACT.md fixes them)

- `src/Worldgen/WorldLayout.Fun.cs`:
  - region (`InFun`, centre, radius, origin, salts `0xF501..0xF50F`);
  - `BuildLevelFun(b, mx, mz)` (rim → hull; else `CopyPlan` from `FunPlan`);
  - `PlanFunBlock` and `FunPlanner`, `PlanPartyRoom` and the other suites;
  - `FunArrivalCell` / `IsFunArrivalSpot` (elevator lobbies and promenades only);
  - guest rooms (`GuestsOf(roomKey)`);
  - helpers for `StabilityAt` and `TemperatureAt`.
- `src/Worldgen/WorldGenerator.Fun.cs`: `InitFun()` (ids by code) and `LevelFunBlock(t, gx, gz, rel, out fluid)`.
- `src/Regions/FunSystem.cs`: section 3.8.
- `src/Entities/AiTaskPartygoer.cs`: section 3.5; registered in `EntityClasses.cs` (one line).
- `tools/gen_fun.py`: textures, shapes, blocktypes, items, entity JSON and lang. It uses `texlib`, the `gen_motion`/`detail_kit` prop helpers, `gen_deep.door_block`/`threshold`, and `gen_entities` builders. Salvage goes inline via `extra={"drops": ...}`.
- `tools/gen_fun_models.py`: `partygoer()`, `lureballoon()`, `partyhost()` and the variant textures. It imports `rig` and helpers from `gen_models` and does not edit `gen_models.py`'s `MODELS`.
- `tools/gen_fun_sounds.py`: section 4.5.
- `tools/mapgen`: modes `regionmap fun` (render) and `funstats`, in their own file if the harness allows (`FunStats.cs`).

### 5.2 Encodings: keep Fun's own byte spaces

The shared enums are nearly full: `WallPattern` has 62 of 64, `PropTable` has about 40 free bytes ≥ 40 shared by six levels, and `FloorKind` has 31 left. So **inside the region, `LevelFunBlock` interprets the tile in Fun's own terms:**
- `Tile.Zone` = `FunZone` (Promenade, Lobby, Party, Mural, Themed, Play, Bounce, Arcade, Kitchen, Gifts, Service, Deck, Waiting, Clone, Host, Hull).
- `Tile.Variant` = a Fun-local prop byte (its own `FunProps` table → `funPropIds[256, kinds, 4]`).
- `Tile.Detail` = the room's palette (paint, cloth, balloon set).
- `Tile.Height` = ceiling height.
- `Tile.Pattern`/`Floor` resolved through Fun-local lookups.

Shared allocations are needed **only for the entrances in other levels and the walked thresholds**. Ask CONTRACT.md for:
- **Unders:** `FunBallPit`, `Overboard`. Next free is 29; Unders are read by `Walked` everywhere.
- **Prop bytes, 4** (Level 0 party-room dressing): `FunBalloonsFloor`, `FunStreamer`, `FunPosterTrap`, `FunConfetti`. They are reused for the Level 1 stair dressing plus `FunBalloonTied`, so 5 in all.
- **One `WallPattern`** (`FunDoor`), for Level 5's door, as `PoolDoor` was done. Or, if 62/63 must be kept, a Level 5 door `Variant` value; CONTRACT decides.
- **Level 11's mascot door:** a city lot feature built as `Cinema` was (a frame plus a door prop byte from the shared pool, or the city's door encoding).

### 5.3 Hooks in shared code (small, local edits in Fun's reserved block)

| Where | Change |
|---|---|
| `WorldLayout.cs` | `FunLevel = 15`; `LevelCount`; `DisplayNumber` "Fun"; the string alias for `goto`/`find`; `ComputeLevel` (`InFun` after `InMotion`); `GetEdge` (`Edge{Pattern = hull}`); `LevelBoundaryEdge`; `BuildMacro` case; `LevelTemperatures[15] = 17` and `TemperatureAt` zone overrides. **Not** in `IsOpenSky` |
| `WorldGeometry` | `FunDrop = 10`; `FloorFor(15)`; `BandBottomFor(15) = FloorFor(15) − 12` |
| `WorldLayout.Reality.cs` | `StabilityAt` case; `FindArrival` branch (`FunArrivalCell`, `IsFunArrivalSpot`); `ArrivalHeight` (floor + 1) |
| `WorldLayout.Entities.cs` | `IsSanctuary` (waiting room is *not* a sanctuary; wards still work); `DarkPlaceAt` for Fun; `LevelDepth` stays 0.5 |
| `WorldLayout.Loot.cs` / `Notes.cs` | `PickedOverShare(Fun) = 0.2`; the altered-note rule |
| `WorldGenerator.cs` | `InitFun()`; `Generate` bottom (`FloorFor − 12`) and band top; `ColumnBlock` case |
| `WorldLighting` | Nothing beyond `BandBottomFor` (light comes from blocks) |
| `AtmosphereSystem` | `Levels[15]`; deck and Host overrides; `LevelSounds` Fun branch (the `partydistant` bed, deck wind); title `level-15` |
| `Roster.cs` | `ByLevel[Fun]`: Partygoer pack (MinBand Approach, Stalk|Hunt, PackMin 2, PackMax 3), lure balloon (Heartland, Glimpse); `SoundsByLevel[Fun]`; `Danger.OfLevel(Fun) = 0.9`; codes in `AllCodes` |
| `MenaceSystem.cs` | `Rate` for Fun: Approach in promenades and halls; Threshold within 12 blocks of a guest room and while the Host's hall is alarmed; Heartland in the waiting room and on deck. A noise input for poppers and pops |
| `Rewards.cs` | Partygoer bounty (1.0 + 2.5 d) |
| `ThresholdNetwork.cs` | `Walked`: `FunBallPit` → 94 castle ball pit (`OneWay`, `SaltDeep + 15`); `Overboard` → Level 7 sea (`OneWay`, `+16`); Level 1 Fun stairs → Fun (`BothWays`, return `Stairs`, `+17`). `Used`: `funposter` (L0 → Fun, one-way, `SaltDoor + 15`), `funposter-reversed` (Fun → 4, one-way), `fundoor` (L5 ↔ Fun, return `FunDoor`), `mascotdoor`/`funlobbydoor` (L11 ↔ Fun waiting room, return `FunLobbyDoor`). New return features `FunDoor`, `FunLobbyDoor`. Salt numbers to be confirmed against CONTRACT.md |
| `ThresholdSystem.Arrive` | Nothing special (no sky drop) |
| Level 0 / 1 / 5 / 11 layouts | Entrances with their own salts so nothing else shifts (2.2). Level 0: the party room is an overlay like `IsRedRoom` (`IsFunRoom(mx, mz)`, about 1/600 of Lobby macros beyond 40% of Level 0's radius, never a Red Room or Manila Room); it walls nothing off, so no `EdgeHall` is needed. Level 1: a hash on the existing ceiling stairwells chooses Fun (1/20) and adds dressing props. Level 5: `SaltL5Room + 15` like the POOL door. Level 11: `OddLot` style with `SaltCityBlock + 15`, replanned over the top |
| `BackroomsMapLayer`, `MapMarks.LevelName` | Sampling uses `FloorFor` already; colours; "Level Fun" |
| `BackroomsModSystem` dump y-range | Include the deck water |
| `EntityClasses.cs` | Register `backrooms-partygoer` |
| `lang/en.json` | Fun's keys (4.6) |

### 5.4 Harness and verification

1. **`layouthash`:** levels 0–14 and 16–19 are byte-identical before and after, except Levels 0, 1, 5 and 11, which differ only at the new entrances. Verify by listing the differing tiles.
2. **`regions`:** 60/60 arrivals in Fun, none in a pocket. Fun's region overlaps no other region.
3. **`links`:** every new kind leads somewhere and back where two-way; it survives save and load.
4. **`funstats`** (new). Targets:
   - promenade floor about 18%;
   - party-room floor ≥ 35%;
   - floor below light 4 at 20–30%;
   - longest straight sight line in promenades and halls ≤ 18 blocks (cloned halls excluded);
   - every room door reaches a promenade (BFS);
   - guest rooms at about 60% of party rooms;
   - plan-block cost < 2 ms.
5. **`regionmap fun`** plus `render_region.py`: an overview and three close-ups (a party-room suite, a cloned hall, a deck).
6. **Headless server** on port **42475** with its own data path in the scratch folder:
   - dump and render chunks (a party room, the mural room, the deck, the Host's hall);
   - `/backrooms goto fun`;
   - `/backrooms encounter partygoer hunt` against a straw dummy;
   - check that fever ticks and a poultice cancels it;
   - check a gift box appears on death.
7. **Model previews:** `entrender.py` for `partygoer` (side, 3/4, front; idle, run, berserk) and the review sheets in `docs/entity-review/`.

### 5.5 Phases

| Phase | Work | Verify |
|---|---|---|
| 1. Region | Id 15 wiring (scaffold), region, hull rim, promenades, lobbies, empty squares, arrivals, fog, sound bed | `regions`, `layouthash` |
| 2. Rooms | All suites, party-room furnishing, lighting, every asset in 4.1–4.2, sounds | `funstats`, renders, headless dumps |
| 3. Partygoers | Model, AI task, guests and packs, latch and fever, disguise, gift box on death, lure balloon | `encounter` headless; entrender sheets |
| 4. Thresholds | Level 0 poster (plus torch-burning), Level 1 stairs, Level 5 FUN doors, Level 11 mascot doors, reversed posters, overboard, ball pit | `links` |
| 5. Extras | Carnivorous Balloons, poppers, cakes and cookies, altered notes, cloned hallways, the Host and LUCA tears | headless |
| 6. Words | Handbook, README rows, lang, version bump | handbook renders |

### 5.6 Risks

- **Prop element count** (balloons, streamers, bunting, tableware) may make chunk meshing slow. Keep ≤ 14 elements per shape and density at the targets; measure in phase 2 (Level 8 precedent).
- **Partygoer pack AI cost:** LoS checks between pack members. Limit to every 500 ms and 16 blocks.
- **The flying lure balloon:** VS flying entities need care. Fallback: a block-like entity that "drifts" by small server-side moves and despawns once out of sight.
- **Bounce on inflatables:** server-set motion may jitter on the client; test in a client early. Fallback: no bounce, just slow.
- **The gift box on death** must not eat items when a gravestone-style mod or keepInventory is on. Only collect item entities that drop within 1 s and 3 blocks; skip if none.
- **Telepathy chat** must stay rare: one line per player per 20 s.

---

## 6. Survival role

| | Level Fun |
|---|---|
| Teaches | Stealth: sight lines, distance, darkness, patience. Reading tells (arches, music, =)). Distrust of the friendly |
| Gives | Food in plenty (cake, cookies, Almond Water, pumpkins, onions), wanderers' gear in gifts, linen and candles (vanilla), party supplies, Firesalt now and then, LUCA tears, two walkable ways home |
| Takes | Bites that become a clock, packs that outlast a walk, lies on the walls, exits that drop you somewhere worse, Red Velvet for the desperate |
| Fits the loop | An expedition, never a home: no anchor, no respawn, and fever only falls once you are out. A larder you raid and leave |

---

## 7. Handbook text (for `tools/gen_guide.py`)

**`PAGES["levels"]`, one paragraph:**

> **Level Fun =).** Endless party rooms on a ship that cannot be this big: balloons, streamers, cake on every table, and a tinny "Happy Birthday" somewhere through the walls. A room with a **balloon arch** over its door and **music** playing has guests: tall yellow **Partygoers** with a smile carved into the face. They are **slow and nearsighted** (about 12 blocks in light, 4 in the dark; less if you sneak) and barely hear anything but running, fighting and pops. One that sees you stares for a second, then its pack joins in. Run: they are slower than a sprint, never open doors, and keep away from fire. Their tables are the best larder in the Backrooms. **Anything marked =) is a lie**, notes included. It is cold here (17 °C).

**`PAGES["thresholds"]`, new bullets:**

- Two-way: **Level 1** stairs into the ceiling with confetti on the steps ↔ Level Fun. **Level 5** wooden double doors marked **FUN** ↔ Level Fun. **Level 11** gym doors painted with a tiger, a parrot and a giraffe, in a parking garage ↔ a Level Fun waiting room.
- One-way: touching a **TIME 4 FUN =)** poster in a party-decorated room of Level 0 → Level Fun (burn it with a torch to be rid of it). In Level Fun: touching a **reversed, blurred poster** → Level 4; going **overboard** from an open deck → Level 7's sea; **diving to the bottom of a deep ball pit** → the castle in Level 94.

**`PAGES["entities"]`, a Partygoers entry:**

> **Partygoers** (Level Fun). Slow, nearsighted, quiet, always in packs. If one **latches on**, you have **30 seconds** to use a poultice or bandage, or the bite becomes Party Fever. Three bites' worth and you join the party: your things are left behind, gift-wrapped, guarded by a new Partygoer with a red balloon. Below half health a Partygoer's chest opens: it stops biting and claws instead, but fire then burns it badly. **Firesalt** or a firepit keeps them away. A **party hat** and a **red balloon** let you pass for one of them beyond a few steps, as long as you don't run. Balloons floating on their own are bait. Balloons tied to nothing in the dark are worse: don't touch them, don't pop them.

**`PAGES["salvage"]`, food notes:**

> **Level Fun:** birthday cake (cut slices), cookies, sealed Almond Water, pumpkins in the Halloween rooms, onions from popped balloons. **Red Velvet cake =) — do not eat** (it feeds you well and the party gets into you). Gifts hold wanderers' belongings, but one in five is a popper, and the bang carries. Tablecloths give linen, and cakes give candles.

**README:** a "## Level Fun =)" section from 3.1–3.7. Threshold rows as in 2.2 go in the two-way, thin-spot and one-way groups. The items go in the items list.

---

## 8. Integration with the other new levels

- **The Hub:** a crayon-coloured "FUN =)" door ↔ a Level Fun FUN door (two-way), if the Hub plan wants it. Fun's side is the same `fun-door-fun` block and `FunDoor` return feature as Level 5's.
- **Level !, The End, Level 974 ("Kitty's House"), Level 3999:** canon gives no link to Level Fun. None proposed.
- **Level 94:** one-way in from Fun's ball pits (2.2). Nothing back: canon has no link, and 94 already has many exits.
- **Level 10:** Wikidot 26 lists Level 10 among the *Adventure*'s land sightings. A stranded cruise ship in the wheat with a gangway into Level Fun would be a superb landmark, but it is a large asset (decision 9.10).

---

## 9. Decisions for the user

1. **Which canon is the body of the level.**
   - **Recommended:** Wikidot. The original's party rooms and creature, plus the rewrite's infinite interior decks (elevator hubs, themed rooms, the cloned hallway, booby traps, Carnivorous Balloons, the reversed-poster and overboard exits), with the cruise ship as nods: the hull rim, open decks and deck signs.
   - Alternatives: Fandom's three-part sequence (bounce-house warehouse → Play Rooms → Party Rooms) as zones; or a literal cruise ship.
2. **The Partygoers' form.** **Recommended:** Wikidot's yellow carved-smile creature with lamprey arms, carapace and red balloon. Alternative: Fandom's tablecloth-covered virus husks that hunt by sound.
3. **Transformation.** **Recommended:** Party Fever (3 latches), cancelled by a poultice within 30 s, falling only outside Level Fun. Death by fever leaves your items gift-wrapped and guarded by a new intern. Alternative: plain bite damage, no fever.
4. **The disguise** (party hat + red balloon, works beyond 3 blocks unless you run or attack). **Recommended:** yes. It is the level's counter, as standing still is Level 94's.
5. **The Level 0 poster trap** (one-way from the home level). **Recommended:** yes, rare (about 1/600 Lobby macros, outer 60% only), with tells, and burnable with a torch. Alternative: put it in Level 2 or 4 instead, away from home.
6. **Red Velvet cake.** **Recommended:** edible, with a stability and fever cost. Alternative: inedible (salvage only).
7. **The Host and LUCA tears.** **Recommended:** yes, in phase 5 (immobile; alarm; one bottle a day). Alternative: skip, leaving "Don't upset the host" as a line of chat.
8. **Partygoers outside Level Fun.** **Recommended:** no. Only tells near the entrances. Alternative: packs at the Threshold band within 48 blocks of an entrance in other levels (canon: "Like us, they are able to move across levels").
9. **The skittering thing at death** (a tiny centipede entity that runs off and vanishes). **Recommended:** yes if cheap (one small model); otherwise keep it as part of the death animation only.
10. **The SS *Adventure* stranded in Level 10** as a second entrance. **Recommended:** not now; a good later addition.
11. **Music.** **Recommended:** an original tune for the distant bed, and the public-domain "Happy Birthday to You" melody for the speakers. Alternative: original tunes only.
12. **Danger 0.9** (the level's entity scaling, like Levels 10 and 11). **Recommended:** yes, scaled further by the *Backrooms entities* world setting.
13. **Order of work.** **Recommended:** phases 1–2 (the look) first, then the Partygoers (3), then thresholds (4). Level Fun is only playable once phase 4 opens it.

---

## Manifest changes (phase 2)

Written by the **code** agent for the asset agent. Codes not listed here are used exactly as section 4 names them.

**C1. Block and item classes the code registers** (put `"class": ...` in the blocktype / itemtype; the classes are
registered by `src/Regions/FunSystem.cs`):

| Code(s) | Class | What the class does |
|---|---|---|
| `fun-cake-{birthday,velvet}-{4,3,2,1,0}` | `BackroomsFunCake` | Right-click with an empty hand takes `fun-cakeslice-{kind}` and swaps the block to the next stage down (`-0` gives nothing). Give the `-4..-1` blocks `drops: []` |
| `fun-cookieplate-{3,2,1,0}` | `BackroomsFunCookies` | Right-click takes one `fun-cookie`, steps down |
| `fun-gift-{colour}-{small,tall}` | `BackroomsFunGift` | Break to open: the blocktype's own `drops` are the contents; one gift in five (by position) is a popper instead (bang, confetti, no drops) |
| `fun-cballoon-{colour}` | `BackroomsCarnivorousBalloon` | Stings on touch, gasses when broken. Needs a selection box but **no collision box** (`collisionbox: null`) so the code's collide hook fires; drops: 1-2 `game:vegetable-onion` |
| `fun-poster-trap-{side}` | `BackroomsFunPoster` | Plus the threshold behaviour `funposter`. A lit torch in hand burns it instead |
| `fun-cakeslice-velvet` (item) | `BackroomsVelvetCake` | On eaten: stability −0.2, Party Fever +0.2 |

**C2. Threshold kinds** (`BlockBehaviorThreshold` `kind`): `funposter` (`fun-poster-trap-*`), `funposter-reversed`
(`fun-poster-reversed-*`), `fundoor` (every `fun-door-fun-*`), `funlobbydoor` (`fun-door-exit-*`), `mascotdoor`
(`fun-door-mascot-*`).

**C3. One more door:** `fun-door-fun-single-{lower,upper}`, a single leaf carrying all three letters F-U-N, for
Level 5's hotel corridors (hotel doors are one block wide). Same kind `fundoor`. Doors are cubes like `door_block`,
so no `{side}` variants.

**C4. Entities.** Two codes, both class `EntityAgent`, the same AI:
- `backrooms:partygoer` (shape `partygoer`, the colour variants as texture alternates);
- `backrooms:partygoer-intern` (shape `partygoer-intern`, with the red balloon).

`taskai` tasks, in priority order:
1. `{"code": "backrooms-partygoer", "priority": 1.6}`. Optional config keys, defaults in brackets:
   - speeds: `walkSpeed` [0.016], `runSpeed` [0.031];
   - sight: `sightLit` [12], `sightDim` [7], `sightDark` [4];
   - attacks: `latchDamage` [2.5], `clawDamage` [4], `attackRange` [1.6];
   - sounds: `gazeSound` ["backrooms:entity/partygoer/gaze"], `latchSound` ["backrooms:entity/partygoer/latch"], `carapaceSound` ["backrooms:entity/partygoer/carapace"], `clawSound` ["backrooms:entity/partygoer/claw"].
2. Vanilla `idle` with animation `idle`.

Behaviours:
- **Server:** `health` (30), `backrooms-menace` with `huntSeconds 90`, `deaddecay`, `despawn`-free.
- **Client:** `controlledphysics`, `interpolateposition`.

Animation codes: `idle, walk, run, gaze, latch, berserk, berserkidle, claw, hurt, die`.

`backrooms:lureballoon`: animation `idle`; no taskai needed (the code moves it). `backrooms:partyhost` stays for a
later phase.

**Asset agent's changes and notes (A1-A12).** Built by `tools/gen_fun.py` (+ `gen_fun_models.py`, `gen_fun_sounds.py`).
C1-C4 above are all built as asked.

- **A1. Orientation.** `{side}` = the direction the prop's face points. Wall blocks (`fun-paint-*-skirted-*`,
  `fun-promwall-band-*`, `fun-mural-*`, `fun-hull-porthole-*`, `fun-steel-sign-crewonly-*`) carry their decoration on the
  side face (the room is that way). The two trim blocks (`fun-paint-*-skirted-*`, `fun-promwall-band-*`) also come in
  every set of faces (`ne`, `ns`, `nes`, `nesw`, ... letters in n-e-s-w order), so the skirting turns outside corners;
  the generator picks the set from which neighbours are floor (`FunOpenFaces`). Wall-hung props (posters, `fun-smiley`, speaker, string lights, bunting, deck sign,
  life ring, deck lamp, balloon arch) stand in the air cell in front of the wall, their back against it. Murals: `tl/tr/bl/br`
  as seen by someone facing them. Tables: `-a` is the west end of a north-facing table, `-b` the east (one block east).
- **A2. Doors** follow C3: cubes with no `{side}`; their raised letters, push bars and handles repeat on all four faces.
  `fun-door-fun-{l,r,single}-{lower,upper}` (l/r as seen from whichever face), `fun-door-exit-*`, `fun-door-mascot-{l,r}-*`.
  The elevators keep `{side}`, and gain an `uppersign` part: `fun-elevator-{l,r}-{lower,upper,uppersign}-{side}` (the OUT
  OF ORDER =) sign is on `l-uppersign`); the upper part's lintel and dial rise 8 voxels above it.
- **A3. Table-top props** (`fun-tableware-*`, `fun-cake-*`, `fun-cookieplate-*`) go in the block above a table
  (their elements start at y -2.75). `fun-tableware` has no `{side}`. `fun-caketins-{side}` stands on a counter (block above).
- **A4. Same-code families split across files** (allowed, as vanilla `clothes`): `fun-paint-{c}` and
  `fun-paint-{c}-skirted-{side}`; `fun-hull` and `fun-hull-porthole-{side}`; `fun-steel` and `fun-steel-sign-crewonly-{side}`;
  `fun-promwall` and `fun-promwall-band-{side}`; `fun-inflatable-{wall-{c}-{side},tower-{c},towertop-{c},arch-{side},floor}`.
- **A5. New:** `fun-inflatable-towertop-{yellow,blue,red,green}` (cone + pennant) on top of `fun-inflatable-tower-*`
  (one block of drums; stack 2 + top). Tower colours also include green. `fun-screen-{l,m,r}-{side}` hangs from the block
  under the ceiling down nearly a block. `fun-balloonarch` has 8 balloons a side (6 looked sparse).
- **A6. `fun-confetti`** is one placeable block (stack 64, drops itself); there is no separate item. Loot: `type: block`.
- **A7. The altered note** is `fun-wanderernote-altered` (class `BackroomsWandererNote`, `Variant["kind"] = "altered"`;
  a `wanderernote` file of our own would overwrite the shared one). Text key `wanderernote-altered-text`.
- **A8. Lang:** `levelname-15` (CONTRACT's key) instead of `levelname-fun`. Plus `blockdesc-fun-confetti`,
  `creature-partygoer-intern`, `creature-lureballoon` etc. with `item-creature-*`/`deadcreature-*`.
- **A9. Entities:** files `entities/fun-{partygoer,partygoer-intern,lureballoon,partyhost}.json`, codes as C4. Shapes and
  textures are `entity/fun-partygoer[-intern]` with alternates `-red,-blue,-green,-white` (alternate index 1-4); the intern
  has its own texture set. Server behaviours include the code's `backrooms-partygoer` behaviour before `health`. Drops:
  party hat 40%, rusty gear, red balloon (interns). Lure balloon: `habitat: Air`, health 1, no taskai, anims `idle`, `drift`.
  The Host (`partyhost`, no health = unhurtable, no physics): its top is at y 1 block, the egg hangs below with the eye on
  its underside: spawn it with its feet one block below the ceiling; anims `idle`, `weep`, `upset`; the eye is part `Head`.
- **A10. Gifts** (C1) are break-to-open with a wanderer's-belongings `drops` list; `fun-supplyshelf-{side}` is a vanilla
  8-slot generic container (empty: fill it from code if wanted). `fun-cake`'s birthday stages 1-4 give light [7,4,4].
- **A11. Sounds** as 4.5; entity sounds in `sounds/entity/partygoer/` (`step1-3, gaze, latch, carapace, claw, die`).
  `fun-speaker-on-*` plays `ambient/fun/funtune` as a block ambient; `fun-blower-*` plays `ambient/fun/blower`.
- **A12. Not class-wired yet** (attributes only, the code may register later): `fun-lucapool` (`BackroomsFunLucaPool`
  is used if registered), `fun-lucatears` (`BackroomsLucaTears` if registered; attributes `maxhealthExtraPoints 4`,
  `meleeWeaponsDamage 0.25`, `durationHours 24`, `stabilityRestored 0.3`). Re-run `gen_fun.py` after registering them.

**C5 (code agent).** No `backrooms-partygoer` *entity behaviour* is needed in the JSON: the code attaches the body
behaviour (fire, carapace) to every Partygoer as it spawns or loads.
