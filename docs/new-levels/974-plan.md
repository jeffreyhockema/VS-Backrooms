# Level 974, "Kitty's House": research, design and integration plan

**Level 974** is a small pink house with no way outside. Its windows show paintings of a sky. Wanderers who carry
something *cute* across a threshold are sometimes taken there instead of where they were going. It is the safest
place in the Backrooms. It has food that comes back, running water, a working bed and electric light, and it has one
resident: **Kitty**, a faceless matt-black figure 3.2 m tall that never harms anyone. Kitty only watches. Wanderers
leave by giving Kitty the cute thing they brought, and then they fall asleep. The danger is staying too long:
the pink that calms you at first wears your mind down, and the food slowly turns to sugar.

Kept as level **18** (`WorldLayout.Level974`), shown as **974**, tag `974`. This is a design only. Section 9 lists the
decisions for the user, each with a recommendation.

## Status (2026-10-07): phase 2 code done, waiting for the assets

The user approved every recommendation in section 9 (with the Hub's pink ribbon door; Level 3999 is dropped).
**Code is in, and builds** (checked in a copy of the tree, because the shared build was failing at the time on another
level's file, `Rewards.cs`). **The assets are not built yet**: `tools/gen_974.py` is the asset agent's. Until it runs,
every missing block falls back to concrete or air (logged once per code), and Kitty does not appear (its entity type
is missing). **Nothing has been played in a client.**

**Built:**
- **The houses** (`WorldLayout.Level974.cs`): one house per cell, with the plan of §3.2 (17 × 15 inside, 4-block
  ceilings), mirrored east–west in half of them.
  - Bedding, three of the six posters, frame colour, plush heap and window paintings are picked per house.
  - The alcove's sloping ceiling, the arrival tile, and Kitty's spots (`L974Spots`).
- **The blocks** (`WorldGenerator.L974.cs`), looked up softly.
- **Kitty's detour, the Hub's door and waking** (`ThresholdSystem.L974.cs`, `ThresholdNetwork.L974.cs`,
  `L974Redirect` / `L974Arriving`):
  - the detour is 1 in 20, or 1 in 6 when the cute thing is held, with 48 in-game hours between visits;
  - companions who carry something cute come along;
  - anyone arriving in the level is put in their own house;
  - `KittyWake` sends you to a safe place fixed per house: Level 4's heart, Level 37 or Level 6.1;
  - after waking, 3 minutes of "Kitty's watch" (a line in `MenaceSystem.Assess`).
- **The rules** (`src/Regions/L974System.cs`):
  - each player is given their own house, saved with the world as `backrooms-l974-houses`;
  - visits, with the stacks you brought marked as possible gifts;
  - the pink's drain, through vanilla's `stabilityOffset`;
  - the fridge and pantry: stock of 6, one back every 2 h, turning half to sugar after 24 h and all of it after 48 h;
  - smells, memories, and a remembered meal at most once a day;
  - taps that fill buckets, jugs and bowls;
  - the dresser's cute clothes (vanilla pink and flowered clothing, marked as Kitty's);
  - the computer: e-mail dialog, the Internet's map mark of where you will wake, and DreamSleep's +0.3 after a
    sleep;
  - offence: lights out (blocks swapped), food gone, −0.4 stability, gift refused for a day, then forgiven;
  - the safety valve: after a day without the brought gift, any cute thing will do, and you wake in Level 0.
- **Kitty** (`EntityKitty`, driven by `L974System`; there is no AI task):
  - it appears 30–90 s after you arrive, out of sight at a watch spot 4–10 blocks off;
  - it leaves once it has been watched for 2–6 s or you come within 3 blocks, and only when unseen;
  - it glides out of your way, sneaks up behind you every 4–8 minutes, and watches you sleep;
  - it kneels by the cat bed, and stoops or peeks in doorways;
  - to call it, sneak and right-click with something cute in hand (or right-click Kitty): it comes, holds out its
    arm, and takes the gift, then you have 4 s of drowsiness and wake elsewhere;
  - it cannot be hurt, and is not saved with the world.
- **Elsewhere:**
  - the house is sanctuary (`IsSanctuary`);
  - `Protection`: the house's fabric (walls, floors, ceilings, windows, lights, door frames and the concrete round
    it) never breaks, only furniture;
  - the fog line, and the client's pink fog after 18 h;
  - the lullaby (warped after 36 h), the fridge hum near the kitchen, creaks;
  - `L974.IsCute` / `CarriesCute` for the Hub;
  - plushies in `tools/salvage.py`: toy boxes about 35%, suitcases 3%, lost backpacks 2%.

**Checked:**
- `974stats` (40 houses, seed 12345): every house has its 7 rooms and its arrival tile, everything inside is
  reachable from the arrival, no doorway is blocked, and all of Kitty's spots are floor.
  - Wake-ups: Level 4 18, Level 6.1 9, Level 37 13 (of 40), each the same every time.
  - `goto 974` lands on the arrival tile.
- `regions`: Level 974 arrivals 60/60. All 60 are "in pockets under 3000 tiles", which is intended: the houses are
  sealed. 0.05 ms per cell.
- `layouthash`: levels 0–11 and 13 unchanged. Level 12 moved (`b70276cd…` → `189a9e6a…`), but from the Hub/Run agents'
  `PoolCorridorEndKind` in `WorldLayout.Level37.cs`, not from Level 974.
- `links`: unchanged in kind, save/load 1247/1247.
- **Headless server** (port 42478, seed 12345): it starts with no exceptions; `/backrooms dump` round the arrival
  shows the house's walls, rooms and doorways, in concrete until the assets exist. No render with real blocks yet.

**Deviations from the plan:**
- **Kitty is driven by `L974System`**, ticked every 100 ms, rather than by an AI task. It never paths: it appears,
  vanishes and glides.
- The entity JSON needs no `taskai` (see Manifest changes).
- **No door leaves and no arch casing.**
- The Internet hint marks **where you will wake** (75% of the time), not the nearest gate there.
- The detour still writes the threshold's own link. Because `Go` remembers the redirected destination, the
  departure waypoint says "Level 974", and a thin spot meant for the original arrival is not placed until someone
  really arrives there. Fixing either needs a change to the shared `Go` (coordinator).

**Still to do:**
- Assets (asset agent).
- Then: render a house, put Kitty down headless, and play-test the gift in a client.
- After the shared generators run, check that the salvage drops reach toy boxes, suitcases and backpacks.
- The handbook (phase 3).

Reserved ranges used (from `Tiles.cs`): `WallPattern` 144–148, `FloorKind` 164–166, `Overheads` 80, `Unders` 90,
`Props` 440–456; salts 0x1801, 0x1810–0x1811, 0x18C1.

---

## 1. What the lore says

### 1.1 Which Level 974

Each wiki has a different Level 974:

| Wiki | Level 974 | Weight |
|---|---|---|
| **Wikidot, backrooms-wiki** ([level-974](https://backrooms-wiki.wikidot.com/level-974)) | **"Kitty's House"**, written by jikupa and rewritten and expanded by AndromedeadReal and jikupa. Rated +60. A sub-level, [974.1 "DreamSleep"](https://backrooms-wiki.wikidot.com/level-974-1), is rated +30. | **Primary canon. This is the one used.** |
| Wikidot, the older backrooms.wikidot.com | No page: `/level-974` returns 404 | — |
| Fandom ([Level 974](https://backrooms.fandom.com/wiki/Level_974), read through the API) | "Memories Left Behind // A Child's Abnormality", by SherlsF, rewritten by IceCraft2022. A town of houses, some sunk in the ground and some floating, and within it a pink house, **The Loving Household**, home to **Kitty** | A second opinion. The same Kitty and the same pink house, set in a town |
| Miraheze ([Level 974](https://backrooms.miraheze.org/wiki/Level_974)) | An ice cave of snow as hard as diamond that floods, with exits to 970, 975 and 977 | Unrelated, and the least known. Ignored |
| *Escape the Backrooms* (Fancy Games), wiki pages [Level 974](https://escapethebackrooms.fandom.com/wiki/Level_974), [Mr. Kitty](https://escapethebackrooms.fandom.com/wiki/Mr._Kitty) and [Toy](https://escapethebackrooms.fandom.com/wiki/Toy) | A secret level, "Kitty's House", released on 23 October 2025 in version 1.0 | The best-known depiction. A game adaptation, not canon |

**Why Kitty's House.** It is the Wikidot canon. Fandom's page is built round the same entity and the same pink house.
*Escape the Backrooms* made Kitty one of the most recognisable Backrooms entities: its pink bedroom teasers from
2022–23 and its 2025 secret level both used the Wikidot design. The Miraheze ice cave shares only the number.

### 1.2 Canon: Wikidot, Level 974 "Kitty's House"

**Survival Difficulty 0: Safe, Secure, Devoid of harmful entities.**

- **A home, finite and sealed.**
  - About 970 sq ft (≈ 90 m²), "with pink theming throughout the interior".
  - "No physical door leading to an outdoor area."
  - The windows "simply reveal artwork depicting what one would typically see outdoors, except with a notably coquette
    theming". The page's photo shows a blue sky and a towering white cloud, framed by sheer white curtains tied back
    with a cream bow.
- **Personal.**
  - Each wanderer usually gets their own near-identical home, with "subtle variations that are tailored to the
    individual Wanderer": cooking utensils, **empty photo frames**, posters of their childhood, and other small things.
  - Several wanderers share a home only rarely, but always if they are "all holding the 'cute' item together".
- **Memory.** Childhood memories come often but "fuzzy", and grow clearer after you leave.
- **Rooms.** A bedroom, a master bedroom, two bathrooms, a living room and a kitchen-dining room. Only the dining room
  and the bedroom are furnished.
  - **The bedroom** has:
    - a twin bed "nestled in between two walls that jut out from the sides of the room";
    - an **open closet** next to the door, with a dresser holding cute clothes in the wanderer's size;
    - many plushies and a few cute posters;
    - a desk opposite the bed with an old Windows 95-style **computer**.
  - **The master bedroom** is empty except for "a pink and white **cat bed** at the back wall".
  - **The dining room** has "pink wooden **banquette** seating that wraps around two sides of a table".
- **Amenities.** Plumbing, electricity and Wi-Fi all work, and are safe. "Wanderers are encouraged to use them."
- **The pink** is "Baker-Miller pink". It calms you for short periods, but "after prolonged durations of time, the
  color can induce anxiety and (within the Backrooms only) reduce sanity".
- **Food.**
  - The fridge and pantries hold Greasy Marshmallows and ordinary Frontrooms food, all safe to eat. "Anything taken
    from the pantries or fridge will eventually replace itself."
  - Stay a long time and the food "will lower in nutritional quality, becoming mainly sugar".
  - Near the kitchen you smell meals from your youth. It is mostly a hallucination, but rarely the meal is really
    there on the counter or the table.
- **Branding.** Things carry mascots from the Frontrooms ("Sanrio and San-X"). The mod uses original look-alikes (§9).
- **The computer** has two profiles:
  - **Owner**, behind an unknown password; clues to it are in this level and in 974.1;
  - **Guest**, with no password.

  Guest's apps include Internet, DreamSleep and Mail; the others are My Computer, Settings, Minesweeper, Recycle Bin,
  MS Paint, Notepad, and some knock-off games of your own.
  - **Mail** shows a welcome e-mail from someone who knows the level (images
    [Email4K](http://backrooms-sandbox-2.wikidot.com/local--files/fragment:andromedeadwips-1/Email4K) and
    [Email3K](http://backrooms-sandbox-2.wikidot.com/local--files/fragment:andromedeadwips-1/Email3K)). Its points:
    - you came because you picked up something cute, and "whatever you found belongs to it" now;
    - Kitty "wishes to observe you and take the offering you inadvertently brought". It is "that shadow that stalks
      you through the halls", "that dark presence just within your view that watches you while you sleep";
    - "Do not disrespect Kitty or its home, clean up after yourself, and try not to scream too loudly when it sneaks
      up behind you";
    - staying long is "ill advised": sanity depletes, and the food turns to sugar;
    - to leave, hold out the cute item and call "Here Kitty, Kitty, Kitty!". It takes the offering, and "the next
      time you fall asleep you will find yourself somewhere just as safe".
  - **Internet** is like old Internet Explorer: vague, often redacted, sometimes in a cryptic script, but now and then
    it has given valuable answers.
  - **DreamSleep** shows a bright, pretty loading screen for about a minute, then "Your dreams are ready, sleep to
    start". Sleeping in *that* bed leads to 974.1.
- **Children are treated differently.** The pink does not harm them, the food stays food until they grow up, and
  Kitty is nurturing. This does not apply in the mod.

**Kitty, the only entity.**
- **Look.** 3.2 m tall, humanoid, with "unnaturally long, lanky limbs which lack hands or feet". Its skin is matt
  black, like "mosou black fabric". No facial features, yet it sees, hears and smells.
- **Movement.** It moves "smoothly and swiftly", and often surprises wanderers by "appearing in close vicinity to
  them".
- **Behaviour.** Never hostile: it "stalk[s] Wanderers as they explore and rest".
- **If you are aggressive to Kitty, or damage the house,** Kitty no longer stalks you, the food disappears, and you
  lose "large amounts of sanity".
- **The Owner** (974.1's entity) can appear here if you do certain things in the sub-level.

**Ways in and out.**
- **Entrance.** "If a Wanderer has anything perceived as 'cute' on their person upon entering a new level, there is a
  slight possibility of being transported to Level 974 instead."
- **Exit.** The only one: give Kitty a cute item "obtained before your visit", at any time. "You will immediately
  fall asleep and wake up in a safe level."

### 1.3 Sub-level 974.1, "DreamSleep" (Wikidot)

**Survival Difficulty 2** (minimal entities, Safe\*, Secure\*). It becomes 3 if you find many clues, or if you enter
the Dwellings.

- **Reaching it.** Run DreamSleep on the Guest computer, then sleep in the bedroom's bed.
- **Leaving it.** Wake at will (except in the Dwellings), or after 8 hours.
- **The dream rooms.** Endless segmented rooms, each woven from the wanderer's dreams, past or future. Physics and
  time vary from room to room. There are no nightmares until your actions bring them.
- **Clues** glow with significance:
  - a cat plushie;
  - an empty bowl and an empty plate;
  - a damaged map of a forest;
  - a syringe;
  - a crimson flower;
  - a small, withered white dress.

  Finding them provokes **the Owner**: nightmares in the rooms, hallucinations, insomnia, and Kitty keeping further
  away.
- **Nothing comes back.** Nothing obtained there survives waking.
- **The Dwellings**
  ([render](http://backrooms-sandbox-2.wikidot.com/local--files/fragment:andromedeadwips-2/sub974picture.png)):
  - floating, drifting room frames, walls and doorways in greyscale and lavender, clipping into one another but
    solid;
  - low gravity, total silence, growing darkness and dread;
  - theorised shadow "Dwellers".
- **The Owner** has never been properly seen; its head is described as "an eye encapsulated in a star shaped
  covering".
  - A credentialed log describes it as broken, a soul "shattered into fragments", with screams "like the screams of a
    little girl".
  - It never explored beyond one or two places, and hid in the computer. Its level grew "once a single room, now an
    entire home", and "it even made a bed for… 'Kitty'. I almost see a part of it in Kitty."

### 1.4 Second opinion: Fandom, "Memories Left Behind // A Child's Abnormality"

- **Class** undetermined. Level-exclusive entities.
- **The town.** Houses in perpetual daylight, set side by side at random, some stuck in the ground or floating
  (shifting gravity). It has a cartoonish, artificial look: the clouds never move. Streetlights flicker, driverless
  cars roam, and footsteps and knocking come from inside the houses. Other people are invisible. Tumblers (Entity
  301) roll about.
- **The Loving Household** is a dollhouse-like home coated in pink and white.
  - Silence, with now and then a creak.
  - The bedroom doors are open and cannot be locked. Plushies carry illegible messages.
  - Hallways have turns that shift. Food is plentiful and never expires.
  - Drawings hang on the walls, and the wardrobes hold feminine clothes that fit any wanderer.
  - Some feel nostalgic, others uneasy.
- **Kitty**:
  - a slender figure that can shapeshift from a child's size to 3 m;
  - it hides in the basement at first, then stalks the upper floors;
  - "panicking will only impede the chances" of escape;
  - harm the house and it stops stalking, items vanish and the lights go out. It then appears and vanishes by turns
    to scare the offender out;
  - it may be the one who decorated the house.
- **The twist (narrative).** A brother brings his lost little sister's plush. Kitty holds out its arm "as if it were
  asking for something", takes the plush, and speaks: "Brother? … I'm your sister." He wakes in **Level 4**.
- **Ways in and out:**
  - entrances: parts of Level 39 fade into it; a noclipped door in Level 45;
  - exits: houses lead to Level 16 and to Level 60 (the houses full of coloured spheres); houses with Frontrooms
    names lead to **Level 94**; grid patterns lead to Level 690.

  None of these levels, except 94 and 4, exist in the mod.
- **Pictures:**
  - a peeking-Kitty photo, *smth2.jpg*: a black figure leaning out from behind a wall at the end of a pink-lit carpeted
    hall with recessed ceiling lights;
  - a pink bedroom with plush backpacks;
  - a tilted yellow house.

### 1.5 The best-known depiction: *Escape the Backrooms*, Level 974

- **The level.** A two-storey, run-down pink house: hallways with wainscot, a bunk-bed bedroom, and a basement stage
  room with 12 audience seats. It was first a lore-accurate pink bedroom, then redesigned as run-down "so players who
  don't know the lore aren't confused".
- **Mr. Kitty.**
  - Tall, black and lanky, with pointed limbs, two white eyes and no mouth.
  - It will not move while looked at. Look away and it closes in and kills.
  - It teleports about and opens doors.
  - The wiki notes that the lore's Kitty is never hostile, and that the game's darker version may be named
    differently on purpose.
- **The objective.** Seat 12 glowing-eyed teddy bears (which mew) in the stage room's seats. The curtain opens on 4
  seated wanderers, a projector reads "Sweet dreams little one", and gas puts you to sleep. You wake in the Bunker.
- **Its contribution.** A fixed picture of Kitty standing in a doorway of a pink bedroom, a door ajar beside it.

### 1.6 Contradictions, and how they are settled

| Question | Wikidot | Fandom | *Escape the Backrooms* | Mod |
|---|---|---|---|---|
| Size and setting | One sealed 970 sq ft house | A town; the pink house within it | A two-storey house | **One sealed house per wanderer**, larger than canon to suit Vintage Story's scale (§2.2) |
| Kitty | Faceless, 3.2 m, never hostile, stalks | A shapeshifter, maybe a lost sister | Two white eyes; kills whoever looks away | **Wikidot**: faceless, never harms. It never moves while you watch (§4) |
| The exit | Give the cute item, then sleep, then a safe level | Give the plush, then wake in Level 4 | 12 toys, gas, then the Bunker | Give the brought item, then fall asleep, then **a safe place fixed for that house** |
| When you fall asleep | "Immediately" (article) | Dizzy at once | Gas | **At once, a few seconds of drowsiness** (§9.4) |
| Food | Restocks, turns to sugar | Never expires | — | Restocks, turns to sugar |
| Damage | Kitty leaves, food gone, sanity lost | + lights off, scared out | — | All of these, and the gift refused for a day |

**The deception.** Nothing in canon lies outright. The house *is* safe. The trap is the comfort:
- free food that comes back;
- a soft bed;
- a host "that welcomes you to stay as long as you like".

Only slowly do you notice the rest:
- the pink grows close;
- the food goes to sugar;
- your memories blur;
- the cute thing you carried "belongs to it" now.

Under the pink, both wikis tell of a lost child: the Owner's shattered girl, and Fandom's little sister. The mod
keeps that only as a hint, in the e-mail and in the handbook.

### 1.7 Pictures

These were downloaded to the session scratchpad and looked at:
- the Wikidot photo
  ([newkitty.jpg](http://backrooms-sandbox-2.wikidot.com/local--files/fragment:andromedeadwips-1/newkitty.jpg));
- the two e-mail images;
- the Dwellings render;
- Fandom's peeking photo and its bedroom;
- *Escape the Backrooms*' "Former Mr. Kitty at the Door", "Bunk Bed Bedroom" and "Big guy" renders, and its
  transparent model.

What they fix:
- **The bedroom** (Wikidot photo): a sloped attic ceiling on one side and Baker-Miller pink walls. A white window with
  sheer curtains, a cream bow and a painted cloud sky, and pastel pony figurines on the sill. Floating white shelves
  with plush toys and boxed figures. A round grey cat poster in a heart behind the bed, a plush backpack hung on the
  wall, and pink patterned bedding heaped with plushies. A small white bedside table, and a vanity mirror.
- **Kitty**: a solid flat black silhouette, a small round head on a thin neck, narrow shoulders, and arms hanging to
  the knees and tapering to points. Its legs are as long as its torso and head together.

---

## 2. Where it fits

### 2.1 A noclip region of sealed houses

Like Levels 37 and 94, Level 974 is not a ring. The scaffolding puts the region south-west of spawn
(`L974CentreX/Z`, radius `max(60, spawnMacroX / 40)` cells).

- **One house per macro cell.** The region is a lattice of identical-plan houses. Each sits in the middle of its
  32×32 cell, and the rest of the cell is solid, unbreakable fill. Nothing is outside: no street, no sky, no gap
  between houses.
- **Your house is yours.** The first time a player is taken, `L974System` assigns them a house cell (a hash of the
  player's UID, probing past cells already assigned). This is saved with the world (`backrooms-l974-houses`), so every
  later visit is to the same house. What you left there is still there, and Kitty keeps it.
- **Its variations are yours.** A house's variations (posters, plush set, bedding, utensils, window paintings, which
  way it is mirrored) come from its cell hash. Since a house belongs to one wanderer, they are that wanderer's
  variations.
- **Sharing.** Anyone taken at the same moment as you, carrying something cute (§2.3), is put in *your* house.
  Otherwise houses are private.
- **The region's rim** is solid like the rest. From Level 10's side the boundary is the usual rock cliff
  (`LevelBoundaryEdge`, open meets enclosed), with no gates. As for 37 and 94, check that no gate pairs the rim with
  Level 10.
- **Floor height.** The shared floor (`L974Drop = 0`). Rooms have **4 blocks of air** (Kitty is 3.2 tall), and the
  ceiling slab is at rel 5. That fits inside the usual band.

### 2.2 Size

Canon's 90 m² would be cramped in Vintage Story, where furniture is a block, Kitty is 3.2 blocks tall and the player
is 1.85. The house is **17 × 15 inside** (19 × 17 with its outer walls), on one storey with 4-block ceilings. That is
about 200 m² of floor after partitions, about twice canon. It has every room canon lists and no others, and you can
walk round all of it in under a minute. (Decision 9.8.)

### 2.3 Its part in the threshold network

**Getting in: Kitty's detour.** It is not a threshold of its own. It is something that happens *on top of* the
network, so the network's two rules stay intact:

- **When.** On any network crossing (`Walked`, `Used`, a vending machine, an elevator ride) by a player who has
  something **cute** on them, from any level, including 37, 94 and the other new levels.
  - It does not happen on: thin spots (going back the way you came), the King's trial, Kitty's own wake-up passage,
    the Hub's pink door, `/backrooms goto`, or gates (which are not thresholds).
- **How often.** A chance of **1 in 20**, or **1 in 6** if the cute thing is *held in the hand*. It never happens
  within 2 in-game days of last leaving the house.
- **What still happens.** The threshold's link is still worked out and written down (`network.Take`), and the waypoint
  for it is still marked. Every threshold still leads to the same place: Kitty simply takes you before you arrive.
- **Where you go.** Your own house, standing in the bedroom beside the bed. There is no way back (you were *taken*:
  one-way).
- **Who comes with you.** Players taken with you (elevator riders, or anyone within 4 blocks who crossed the same
  threshold in the last 5 s) and carrying something cute come too, into the same house.

**What counts as cute.** The item or block type has the attribute `backroomsCute: true`, or the stack has it:
- **the mod's plush toys** (`l974-plush-*`, new; §3.5) and the clothes from Kitty's dresser (marked per stack);
- **vanilla:** flowers and seashells, if they exist in 1.22 (the asset agent checks the codes and patches them;
  `patches/l974-cute.json`);
- **the other new levels' items,** if their agents nominate them (Level Fun's party favours and balloons, for
  instance).

**Getting out.** Kitty's gift takes you one-way to a **safe place fixed for that house**. It is worked out once, like
the King's table (`ThresholdNetwork.KittyWake(house)`), and saved:

| From | Threshold | To | Way back | Canon basis |
|---|---|---|---|---|
| **Any level** (0–11, 6.1, 37, 94, Level !, Fun, the End, the Hub, 3999) | Crossing any threshold with something cute on you: 1 in 20, or 1 in 6 if held | Your house in Level 974, beside the bed | None (taken) | Wikidot entrance |
| Level 974 | **Giving Kitty the cute thing you brought**: you fall asleep within seconds | A safe place fixed per house: **Level 4's heart** (50%), **Level 37** on a lit deck (25%), **Level 6.1** (25%) | None | Wikidot exit ("a safe level"); Fandom wakes in Level 4 |
| Level 974 | Dying | Level 0 (the anchor rule) | — | Mod rule |
| *The Hub* (optional, §9.11) | A pink door tied with a ribbon bow, which opens only for someone carrying something cute | Your house (the door is gone behind you) | None (taken) | *Escape the Backrooms*' secured door; Fandom's door in Level 45 |

Canon links the mod cannot use are dropped:
- Fandom's entrances from Levels 39 and 45;
- Fandom's exits to Levels 16, 60 and 690;
- Fandom's exit to Level 94, which comes from a different, town-sized level (the mod's house has no outside to hold
  those houses).

**Waking.**
- A few seconds of drowsiness, then black (the existing blink fog), then you arrive standing.
- For **3 minutes after waking, Kitty's watch** holds: the director treats you as in a sanctuary (band Safe), and
  your exposure clock is reset as if you had slept. This is canon's "somewhere just as safe".
- "You wake somewhere else, rested. For a while, you feel watched over."

---

## 3. Level 974: design

### 3.1 The experience

You step through a door in the hotel with a plush rabbit in your hand, and wake standing in a pink bedroom that is
somehow yours. Plushies are heaped on a narrow bed in an alcove, fairy lights run under the ceiling, and a music box
is playing somewhere. The window shows a sky too blue to be real. There is no door out. There is food in the fridge,
a bed, a computer with one unread e-mail. And at the end of the hall, in a doorway, something very tall and very
black is standing quite still. When you look again it is gone.

Design goals, in order:

1. Comfort first, unease second, never a monster.
2. It must read instantly as Kitty's House: Baker-Miller pink, plushies, a painted window, a faceless black figure in
   a doorway.
3. A rest stop with a price. You can heal, sleep and eat here. Every visit costs a cute thing, and every hour too
   many costs your mind.

### 3.2 The house plan

The plan is fixed, as canon says ("nearly identical homes"). It is drawn once in plan coordinates (u east, v south),
then mirrored east–west for half the houses (by cell hash) and placed at cell offset (6, 7). 19 × 17 including the
outer walls.

```
     u 0         1
       0123456789012345678
v  0   ###WW#########WW###
   1   #.......#..#d.....#      Living room (u1-7, v1-7): EMPTY but a ceiling light
   2   #.......#..#kq..xx#      Hall (u9-10, v1-15): two wide, empty photo frames, a night light
   3   #.......#..#.RR.BB#      Bedroom (u12-17, v1-6)
   4   #.......D..#.RR.pn#        k desk with computer, d desk, q chair, R heart rug
   5   #.......#..D....xx#        x stub walls: the bed alcove; B twin bed (head east)
   6   #.......#..#rox...#        p plush heap, n bedside table and lamp
   7   #.......#..########        r dresser in the open closet, o clothes rod over (walkable)
   8   ###AAA###..#i.w#iw#      Bath 1 (u12-14, v8-10): i basin, w toilet, t tub
   9   #.......#..D...#..#      Bath 2 (u16-17, v8-10): basin and toilet, its door from the master
  10   #F......#..#.tt#..#
  11   #P......#..#####D##      Kitchen-diner (u1-7, v9-15):
  12   Wc......D..#......#        F fridge, P pantry, c counter, s sink and tap, S stove, u utensils
  13   Ws....hb#..D......W        b banquette (L round two sides of the table T), h chairs
  14   #c...hTb#..#.....mW      Master bedroom (u12-17, v12-15): EMPTY but m, the cat bed
  15   #cSu.bbb#..#......#
  16   ###################      # walls, W windows (2 wide), D doorways, A archway (3 wide)
```

- **Doorways** (1 wide, 3 high, white casing, lintel at rel 4):
  - the living room (8,4), the kitchen (8,12), the bedroom (11,5), bath 1 (11,9) and the master (11,13), all off the
    hall;
  - bath 2 (16,11), off the master;
  - an archway 3 wide between the living room and the kitchen (3–5, 8).
- **Doors** stand **open**: a white six-panel leaf (decorative) against the wall beside the bedroom, bath and master
  doorways. Nothing locks, as Fandom says.
- **Windows** (2 wide, at rel 2–3) are paintings behind glass: the living room (north), the bedroom (north), the
  kitchen over the sink (west) and the master (east).
- **The bed alcove** (canon's "between two walls that jut out"): two stub walls, 2 long, from the bedroom's east wall
  at v2 and v5. The bed lies in it head to the wall. Over it the ceiling slopes down to the east, from 4 to 3 to 2
  blocks, with real slope blocks. That is the attic slope in the Wikidot photo.
- **Kitty's spots** are kept in the plan for the AI (§4.2):
  - watch spots: every doorway, the archway's ends, the hall's two ends, the living room's far corners, (15,3) at the
    foot of the bed, and (16,14) beside the cat bed;
  - the sleep-watch spot: (15,4), by the bed;
  - the gift spot: whichever watch spot is nearest the caller.
- **Arrival**: (14,5), facing the bed. `IsL974ArrivalSpot` accepts only that tile. `checkEscape` must be false, since
  a sealed house has no escape.

**Variations per house** (cell hash, salt 0x1810+):

| What | Options |
|---|---|
| Mirror | east–west, 50% |
| Bedding | hearts, strawberries or stars, on pink |
| Posters | 3 of 6 designs (§5.2), hung on the bedroom walls at (12,0), (17,0) and (13,6) |
| Plush heap and shelves | two arrangements; the plushies' colours are drawn from the pastel palette |
| Utensils on the counter | mint, lilac or butter yellow (canon's "unique cooking utensils") |
| Window paintings | one of 4 per window (§5.2) |
| Hall photo frames | white or gold, always empty |

### 3.3 Light, sound and air

- **Light.** Electricity works.
  - Recessed round ceiling **downlights** (light 13, warm white with a hint of pink): one in the middle of each room,
    two in the hall.
  - A pink-shaded **bedside lamp** (light 8).
  - **Fairy lights** along the bedroom's north and east walls under the ceiling (light 5).
  - A cloud-shaped **night light** in the hall (light 4).

  Nowhere is dark. Now and then (once in ~10 minutes, near Kitty) the nearest downlight flickers twice, the user's
  "occasional flicker". It is also a quiet tell that Kitty is in the room.
- **Air** (`L974Air`):
  - clear, a faint warm pink, fog density 0.0015, colour (0.98, 0.88, 0.92);
  - after the calm period (§3.4) the fog thickens to 0.005 and the tint deepens to (0.98, 0.70, 0.80): the pink
    pressing in;
  - while drowsy after the gift, the blink fog.
- **Sound** (`L974Sounds`). No hum, and no distant entity sounds (the director is silent here).
  - A **music-box lullaby** (Brahms' *Wiegenlied*, in the public domain; a 32 s loop), faint and muffled, from the
    bedroom. It is heard from anywhere in the house, louder near the bedside table.
  - After the calm period it plays a **warped** version: slowed, detuned, with wow and flutter. The parallel is Level
    94's siren tune going flat.
  - The fridge's hum within 6 blocks of it; a creak of the house now and then.
  - Kitty's soft cloth rustle when it relocates near you.
- **Temperature.** 21 °C (`L974Temperature`).

### 3.4 Mechanics

| Mechanic | Rule | Why |
|---|---|---|
| Safe | `IsSanctuary` true everywhere in the level. No dens, no director, no glimpses, no distant sounds. Reality Shifts still darken it (lights out on the client) and drain stability, but nothing comes | Canon: Safe, Secure, no harmful entities |
| Rest | Being in the house counts as resting (exposure clock rewinds). The **bed is a real bed**: sleep the night through as in vanilla | "Encouraged to use them … may not encounter another safe spot for a while" |
| The pink (stability) | `L974Stability` = **1.3** (it restores you). `L974System` adds an **overstay drain** by hours since you arrived: 0–18 h none; 18–36 h as if 0.9; 36–60 h as if 0.6; over 60 h as if 0.3. Messages at each step: "The pink is very calming." / "The pink is starting to feel close." / "You can't remember the last colour you saw that wasn't pink." | Baker-Miller pink: calming at first, then anxiety and lost sanity |
| Food that comes back | The **fridge** and **pantry** each hand out one item per right-click. Each holds up to 6, and refills one item every 2 in-game hours (counted while anyone is in the house). What they give depends on the hours since you arrived: under 24 h, real food; 24–48 h, half sugar; over 48 h, sugar only ("The food in the cupboards is all sweets now.") | Canon restocking and the sugar decline |
| Remembered meals | Every ~3 in-game hours spent within 8 blocks of the kitchen, a smell message ("You smell pancakes, the way someone used to make them for you."). One in five of them is real: a **remembered meal** lies on the table, at most once per in-game day | Canon olfactory hallucination, with rare real meals |
| Water | Every **tap** (kitchen sink, the basins, the tub) fills a held bucket, jug or bowl with fresh water (vanilla `waterportion`) | Plumbing works. There is no thirst, but water is for cooking, clay and crops |
| Cute clothes | The **dresser** gives one piece of clothing per visit: a vanilla clothing item, the asset agent picks 4–6 light or bright ones. It is marked `backroomsCute` and `l974Kitty` (Kitty's, so it does not count as a gift) | Canon's dresser of cute clothes in your size |
| The computer | Right-click: the Guest desktop (§3.6) | Canon |
| Damage is an offence | Breaking any of the house's things (furniture, plushies, lamps, posters), or hitting Kitty: see §4.4. Walls, floor, ceiling, windows, lights and door frames **cannot be broken** (`Protection`, the whole level's structure) | "Do not disrespect Kitty or its home" |
| Memories | On arrival and every few in-game hours, a soft memory message ("A memory surfaces, soft at the edges: a kitchen table, and someone humming.") | Canon's fuzzy childhood memories |
| Death | You wake in Level 0, as always. What you carried stays in the house, which will still be yours next time | The anchor rule |

### 3.5 What there is to find, here and elsewhere

**In the house:**
- **Real food** (vanilla, verified codes): bread, cheese, a red apple, a carrot, cooked meat, and the new
  **strawberry milk**.
- **Sugar**: the new **Greasy Marshmallows** (named in canon) and **pastel candy**.
- **Remembered meals**: pancakes (grain), chicken soup (vegetable) or macaroni and cheese (dairy). These are big
  meals, the best food in the house, and rare.
- **Water** from the taps. **Cute clothes** from the dresser. **Sleep** in the bed.
- Salvage: the house's furniture breaks like any (planks, sticks, cloth, brackets), but that is the offence.

**Elsewhere** (so there is something cute to carry). These are small edits to other levels' loot, made in phase 2
with the coordinator's agreement:
- **Plush toys** (`l974-plush-{cat,bunny,bear,star}`, cute):
  - Level 9's toy boxes (35% when broken, `tools/salvage.py` `toybox`);
  - Level 5's suitcases (3%);
  - Level 11's clothing racks (2%);
  - lost backpacks (2%).
- A plush is also a **cute thing to hold** on purpose: hold one in your hand as you go through a door, and you are
  more likely to be taken.

---

## 4. Kitty

### 4.1 Role

Kitty is **not a menace entity**: the director never puts it down. `L974System` keeps exactly **one Kitty per occupied
house**. It appears 30–90 s after the first wanderer arrives (Kitty "conceals its presence" at first), and despawns
when the house is empty. It cannot be killed: it is invulnerable, and damage only counts as an offence. It never
attacks. Its "counters" are good manners.

### 4.2 Behaviour brief (`AiTaskKitty`, server; `EntityKitty`)

It uses `Senses.Sees` (in view, with a clear line) and `Senses.LooksAt` (stared at), as the Smiler and Hound
stare-downs do.

| State | What it does |
|---|---|
| **Hidden** | Not spawned. 30–90 s after arrival, and after each vanishing for 20–120 s |
| **Watch** | Appears at a watch spot (§3.2) that is **out of the player's view** and 4–10 blocks away, preferring doorways and the hall's ends. It stands still facing the player, idling (sway, a slow curious head tilt). **It never moves while seen.** After being seen for 2–6 s, or when the player comes within 3 blocks, it relocates: the next moment nobody in the house is looking at it, it is gone (`vanish`, rustle), and it reappears at another spot out of view. In a doorway it plays `stoop` (its head would touch the lintel) or `peek` (leaning out from behind the jamb, as in Fandom's photo) |
| **Sneak-up** | Every 4–8 minutes, it appears directly **behind** the player, 1.5–2 blocks off, facing their back, with a rustle at 30% volume, so attentive players hear it. It stays until it is seen, plus 2 s, then vanishes once unobserved. Canon: "try not to scream too loudly when it sneaks up behind you" |
| **Make way** | If a player walks straight at it within 2 blocks (for instance it stands in the doorway they need), it **glides** back out of the way, smoothly and swiftly (0.06, faster than a sprint, a straight slide with no steps). This is the only time it is seen moving |
| **Sleep watch** | While a player sleeps in the bed, it stands at the sleep-watch spot, bent over the bed (`sleepwatch`). Canon: "watches you while you sleep" |
| **Resting** | Now and then, when no player can see the master bedroom, it kneels folded beside the cat bed (`kneel`). Whoever walks in finds it there, and it is gone the next time they look away |
| **Called** | Sneak + right-click with a cute item in hand anywhere in the house sends "Here Kitty, Kitty, Kitty!" to nearby chat. Within 2–6 s Kitty appears at the gift spot nearest the caller, glides to 1.5 blocks and **holds out a long arm** (`ask`), as Fandom's brother saw. Right-click Kitty (or call again) with the gift in hand to give it |
| **Take** | If the held stack is a cute item **you brought** (§4.3), Kitty takes it (`take`) with a soft purr. "Kitty takes the plush cat. You are suddenly, overwhelmingly sleepy." 4 s of drowsiness (slow, blink fog), then away to the house's safe place (§2.3). Otherwise: "Kitty does not want that. It wants what you brought." It lowers its arm and vanishes |
| **Offended** | §4.4 |

Multiplayer: Kitty watches one player at a time (the one it saw least recently), as *Escape the Backrooms*' Kitty
alternates. Each player's gift is their own.

### 4.3 "Obtained before your visit"

On arrival, every cute stack in the player's inventory (hotbar, backpack, held) is marked with this visit's id
(`l974Brought = visitId`, a stack attribute). Kitty accepts only a stack carrying the current `visitId`, which is
canon's rule exactly. Things got inside the house (the dresser's clothes, a plush from a broken heap) are marked
`l974Kitty` and never count.

**If the brought thing is lost** (dropped and despawned, for instance), a safety valve applies (decision 9.7). Once
the player has gone a full in-game day with no marked stack, Kitty accepts *any* cute item, the dresser's clothes
included, but then the wake-up is in **Level 0** (home), not the house's safe place. Dying is the other way out.

### 4.4 Offence

Breaking any of the house's things, or striking Kitty, offends it:
- Kitty vanishes at once with a long exhale. **The lights go out** (the house's downlights, lamp and fairy lights are
  swapped to their off states; the night light stays). "The lights go out. The house is very quiet now."
- The **fridge and pantry empty**, and stop restocking for this visit.
- **Stability −0.4** at once, and the house's stability counts as **0.4** for the offender until forgiven.
- Kitty **refuses the gift for one in-game day**. Following Fandom, now and then it appears in the dark at the far end
  of the hall and is gone, to "scare off the offender".
- After that day, a light comes back on ("Somewhere in the house, a light comes back on."), and calling it works again.

### 4.5 Model brief (`tools/rig.py`; builder in the level's own model script, §6)

The model faces −X. 16 px to a block, feet at y = 0. **Total height 51 px (3.2 blocks).** It is a silhouette before
anything else: it must read as a flat black cut-out from across a room.

| Part | Box (w × h × d px) | y range | Notes |
|---|---|---|---|
| Leg tips (points) | 1.2 × 2 × 1.2, tapering | 0–2 | No feet: it stands on points |
| Shins | 2.2 × 11 × 2.2 | 2–13 | Legs apart, the hips 5 px wide |
| Thighs | 3 × 13 × 3 | 13–26 | |
| Pelvis | 5 × 3 × 3.5 | 26–29 | |
| Waist → chest | 5 → 8 wide × 12 × 3.5 (two boxes) | 29–41 | Narrow; shoulders 9 px across, hunched up 1 px |
| Neck | 2 × 3 × 2 | 41–44 | Thin, angled 10° forward |
| Head | 5 × 7 × 5.5 core, a 4 × 1 × 4 cap and a 3 × 1 × 3 chin | 44–51 | A small rounded oval, **no features at all** |
| Upper arms | 2.5 × 12 × 2.5 | from the shoulder at 40 down to 28 | Hanging 4° out from the body |
| Forearms | 2 × 13 × 2 | 28–15 | |
| Arm tips | 1.2 → 0.6, 3 long | 15–12 | No hands: the arms end in points at about knee height |

- **Rest pose:** chest pitched 6° forward, neck 10°, a slight stoop; the arms hang a little away from the body.
- **Texture:** matt black, `#0A0A0C`. A faint cloth weave, 1-texel cross-hatch in `#121216` at 20% alpha. No
  highlights and no glow: canon's "mosou black" fabric. The top faces are no lighter than the sides.
- **Hitbox:** collision 0.7 × 2.9 (it fits a 3-high doorway by stooping), selection 0.8 × 3.2, eye height 2.9.
- **Animations** (no walk or run cycle; it is never seen walking):
  - `idle`: an 8 s loop, the chest breathing 1.00 → 1.01, a ±3° head drift, now and then one arm tip curling;
  - `headtilt`: 1.2 s, the head rolls 22° and back; curious, cat-like;
  - `glide`: a 1 s loop, the body leaning 8° forward, the legs barely shifting ±4°, the arms trailing 6° back, no
    bob;
  - `stoop`: in over 0.6 s, then held; chest +30°, neck +15°;
  - `peek`: leaning 35° sideways from the hips, head rolled −15°, one arm tip resting on the jamb at shoulder height;
  - `ask`: 1.5 s, then held; the right arm rises to horizontal, its tip curls up 30°, the head tilts 15°;
  - `take`: 1.2 s; the arm draws back to the chest, both tips cross over it, the head bows 20°;
  - `sleepwatch`: hips pitched 35°, chest 25°, head 20° down, the arms hanging straight;
  - `kneel`: thighs 90° forward, shins folded back, about 30 px tall, the arm tips resting on the knees;
  - `vanish` / `appear`: 0.25 s, a stretch of the Y scale 1 → 1.05, before it despawns and after it spawns.
- **Previews:** `tools/entrender.py shape.json texture.png out.png anims=idle,headtilt,ask,peek,stoop,sleepwatch
  views=front,side,34`.
- **Lang:** `item-creature-l974-kitty` "Kitty", `creature-l974-kitty` "Kitty". It cannot kill, so there is no death
  line.
- **Sounds:** `l974-kitty-rustle` (0.6 s, a soft cloth whisper), `l974-kitty-purr` (2.5 s, a low soft purring hum),
  `l974-kitty-exhale` (2 s, a long breath out: the offence), `l974-lightsout` (a relay clunk).

---

## 5. Asset manifest (`tools/gen_974.py`)

All block textures are 32 × 32. Paths:
- textures: `assets/backrooms/textures/block/974/`;
- block types: `blocktypes/974/`;
- shapes: `shapes/block/974/`;
- sounds: `sounds/ambient/974/` and `sounds/creature/974/`;
- items: `textures/item/974/` and `itemtypes/974/`.

Every code starts with `l974-`. Mascots are original (§9.12): **no Sanrio or San-X characters**.

### 5.1 Palette

| Name | Hex | Used for |
|---|---|---|
| Baker-Miller pink | `#F09AB0`, shading `#E48AA2` / `#F7AEC1` | Walls (canon's paint, a little desaturated so it isn't neon in game) |
| Trim white | `#F8F3F0` | Baseboards, crown moulding, casings, doors, furniture |
| Blush carpet | `#EDD5D2`, flecks `#E2C4C2` | Bedrooms, hall, living room |
| Checker | `#F4B6C6` / `#FBF6F4` | Kitchen floor |
| Bath | white hexagons `#FAF7F5`, the odd pink `#F2BFCB` | Bathroom floors and wall tile |
| Ceiling | `#FAF6F4` | Every ceiling |
| Pastels | mint `#BFE8D7`, lilac `#D9C6F0`, butter `#FBEBA8`, sky `#BCD8F2` | Plushies, utensils, posters |
| Kitty | `#0A0A0C` | Kitty |

### 5.2 Blocks

**Structure** (protected; full blocks unless noted). One code with variants where noted:

| Code | Variants | Texture / shape | Notes |
|---|---|---|---|
| `l974-wall` | `plain`, `base` (white baseboard 5 px), `crown` (white crown moulding 3 px at the top), `backsplash` (white subway tile, lower 20 px), `bathtile` (pastel square tile, whole face), `bathtilecap` (tile with a pink rail at 24 px) | Paint with a soft roller stipple, 2 alternates | rel 1 `base` (bathrooms `bathtile`), rel 2–3 `plain`, rel 4 `crown`. Kitchen walls behind the counters: `backsplash` at rel 2. Bathrooms: `bathtile` rel 1, `bathtilecap` rel 2, `plain` above |
| `l974-floor` | `carpet` (4 rotations as alternates), `checker`, `bathhex` | As in the palette | rel 0 |
| `l974-ceiling` | — | Flat white plaster, faint texture | rel 5 |
| `l974-slope` | `n`, `e`, `s`, `w` | A shape: a 45° wedge in 4 steps of 4 px, pink paint below, white crown along its low edge | The alcove's attic slope at rel 3–4 |
| `l974-lintel` | `ns`, `we` | Pink wall with a white casing header 3 px deep on both faces | rel 4 over doorways |
| `l974-casing` | `ns`, `we` | A shape: two white jamb boards, 1.5 × 16 × 3 px, at the sides of the opening; no collision | rel 1–3 in each doorway |
| `l974-archcasing` | `ns`, `we` | The same, wider, for the 3-wide archway: header plus end jambs | |
| `l974-window` | `bl`, `br`, `tl`, `tr` × 4 facings × 4 paintings (`clouds`, `hills`, `rainbow`, `sunset`) | A shape: a white frame 2 px recessed 3 px, a cross mullion, a glass plane (cutout glints), and the painting plane behind; sheer white curtains gathered at both outer edges, tied with a cream bow (`t*`), a valance across the top (`t*`), a sill 3 px deep with two tiny pastel pony figurines (`b*`) | Paintings are 64 × 64, split into 4 quadrants: **clouds** (the Wikidot photo: sky blue, a towering white cumulus), **hills** (pink and green hills, a heart-shaped cloud), **rainbow** (a pastel rainbow over a flower field), **sunset** (peach sky, a pink sun, one star). Flat on purpose: canon's "artwork" |
| `l974-doorleaf` | `lower`, `upper` × 4 facings × `l`/`r` hinge | A white six-panel door standing open against the wall, 2 blocks tall, a brass knob | Decorative, thin collision |

**Lights** (protected):

| Code | Variants | Shape | Light |
|---|---|---|---|
| `l974-downlight` | `on`, `off` | A ceiling block with a round lens 6 px across, 1 px proud, a white trim ring | `on`: light 13, `lightHsv [4, 2, 13]` (warm, faintly pink) |
| `l974-fairylights` | `n`, `e`, `s`, `w`, × `on`/`off` | A thin wire along the top of a wall face, 7 bulbs of 1 × 1.5 px (pink, butter, white), sagging 1 px between pins | `on`: 5 |
| `l974-nightlight` | 4 facings | A cloud-shaped plug-in, 5 × 4 px, on the wall at rel 1 | 4 |

**Furniture and things** (breakable, which is an offence; salvage per `tools/salvage.py`). Placed as `Props`
440–479 (P) and `Decor` 224–235 (D):

| Code | Variants | Size / shape | Notes |
|---|---|---|---|
| `l974-bed` | `head`, `foot` × 4 facings × bedding (`hearts`, `strawberries`, `stars`) | 1 × 2. A white rounded-rail frame, a 9 px mattress, a pink duvet with its pattern, two pillows, plushies heaped on the head (3 small plush boxes) | **A real bed**: vanilla bed class and attributes (sleep, spawn not set: the anchor rule) |
| `l974-nightstand` | 4 facings | A small white table, 12 × 10 × 12, a drawer; on top a pink-shaded lamp, a water bottle and two vitamin jars (the photo) | The lamp emits 8 |
| `l974-plushheap` | `a`, `b` | 4–6 plush shapes (cat, bunny, bear, star) on the floor, the tallest 9 px | Decor; breaking it drops `l974-plush-*` marked as Kitty's |
| `l974-desk` | `plain`, `computer` × 4 facings | A white desk with a drawer column; `computer` carries a beige CRT (9 × 8 × 8, a dark blue-grey screen with a faint pink-lit desktop), a keyboard and a mouse | `computer` opens the Guest desktop |
| `l974-chair` | `desk` (a pink swivel chair), `dining` (white with a pink cushion) × 4 facings | | |
| `l974-dresser` | 4 facings | 14 × 14 × 10, white, three drawers, pink knobs | Gives the cute clothes |
| `l974-closetrod` | 4 facings | A rod at rel 3 with 5 hangers of pastel clothes (simple garment shapes) and a plush backpack hanging at the end | Over the closet's second tile; walk-through |
| `l974-shelf` | `plush`, `figures` × 4 facings | A white floating shelf, 16 × 1.5 × 5, with 2 plushies or 3 boxed figures | Wall decor at rel 3 (D) |
| `l974-poster` | `cat` (a round grey cat in a heart), `bunny` (a bunny holding a strawberry), `rainbow`, `star` (a smiling star), `toast` (a smiling toast slice), `frog` (a frog in a mushroom hat) × 4 facings | A 1 px panel, 14 × 14, with taped corners | Wall decor at rel 2 (D) |
| `l974-frame` | `white`, `gold` × 4 facings | An **empty** photo frame, 10 × 12, a pale grey mat inside | The hall (D) |
| `l974-rug` | `0`–`3` (quarters of a 2 × 2 heart) | A 1 px slab, pink with a white edge | Bedroom |
| `l974-fridge` | `lower`, `upper` × 4 facings | A rounded 1950s fridge in pink, 1 × 1 × 2, a chrome handle | The food dispenser (`l974food: "fridge"`) |
| `l974-pantry` | `lower`, `upper` × 4 facings | A tall white cupboard with pink knobs, 1 × 1 × 2 | The food dispenser (`l974food: "pantry"`) |
| `l974-counter` | `plain`, `corner`, `sink` (basin and a chrome tap), `canisters` (3 cute canisters), `utensils` (a utensil crock: mint, lilac or butter) × 4 facings | White top, pink cupboard fronts | `sink` is a tap |
| `l974-stove` | 4 facings | A pink retro stove, 4 coil rings, an oven window | Decor |
| `l974-banquette` | `straight`, `corner` × 4 facings | Pink-painted wood, seat at 7 px, a cushioned back to 18 px | Canon |
| `l974-table` | — | Square white table, 14 × 12 × 14, a heart placemat and a little vase of pink flowers | Where remembered meals appear |
| `l974-catclock` | 4 facings | A cat-shaped wall clock with a hanging tail, 8 × 14 | Kitchen wall (D) |
| `l974-toilet` | 4 facings | White, with a fluffy pink lid cover | |
| `l974-basin` | 4 facings | A white pedestal basin with a chrome tap | A tap |
| `l974-bathtub` | `head`, `foot` × 4 facings | A white clawfoot tub, 1 × 2, a rubber duck on the rim, a pink bath mat beside it | `foot` is a tap |
| `l974-mirror` | 4 facings | A round mirror, pink frame, 12 across | Wall decor (D) |
| `l974-towelrail` | 4 facings | A chrome rail with a folded pink towel | Wall decor (D) |
| `l974-catbed` | — | A round cushion bed, 12 × 5 × 12, pink and white, a small heart pillow | Canon: the master bedroom's back wall |

### 5.3 Items (`itemtypes/974/`)

| Code | What | Notes |
|---|---|---|
| `l974-plush` | variants `cat`, `bunny`, `bear`, `star` | Held shapes about 7 px. Attribute `backroomsCute: true`. Not edible. 32 × 32 icons |
| `l974-marshmallow` | Greasy Marshmallows | Food, `NoNutrition`, satiety 80. A glossy paper bag |
| `l974-candy` | Pastel candy | Food, `NoNutrition`, satiety 50 |
| `l974-strawberrymilk` | Strawberry milk in a little carton | Food, `Dairy`, satiety 160 |
| `l974-meal` | variants `pancakes` (`Grain`, 520), `soup` (`Vegetable`, 480), `macaroni` (`Dairy`, 480) | A plate or bowl; "A Remembered Meal" |

Vanilla food used by the fridge and pantry (the asset agent verifies the codes in 1.22): bread, cheese, red apple,
carrot, cooked red meat. The dresser's vanilla clothing is 4–6 light or bright pieces.

Patch: `patches/l974-cute.json` adds `backroomsCute: true` to vanilla flowers and seashells (only if those codes exist).

### 5.4 Entity

`entities/974/l974-kitty.json`:
- class `EntityKitty`;
- the shape and texture from §4.5;
- AI task `kitty` only;
- `invulnerable`, no drops;
- `despawn` handled by `L974System`.

### 5.5 Sounds (synthesised, `.ogg`)

| Code | Length | Character |
|---|---|---|
| `ambient/974/lullaby` | 32 s loop | Brahms' *Wiegenlied* (public domain) on a music box, distant and muffled, slight room reverb |
| `ambient/974/lullaby-warped` | 36 s loop | The same, 0.9× speed, detuned, with wow and flutter; a note now and then missing |
| `ambient/974/fridge` | 6 s loop | A low compressor hum, 60 Hz with a soft rattle |
| `ambient/974/creak` | 1–2 s, 3 variants | Wood settling |
| `ambient/974/chime` | 2.5 s | An original four-note start-up chime, 90s PC style (computer boot) |
| `ambient/974/mail` | 0.6 s | A soft "new mail" ding |
| `ambient/974/drowsy` | 3 s | A descending celesta glissando into a soft pad |
| `creature/974/rustle` | 0.6 s, 3 variants | Cloth whisper |
| `creature/974/purr` | 2.5 s | A soft purring hum at 25 Hz modulation |
| `creature/974/exhale` | 2 s | A long, low breath out |
| `ambient/974/lightsout` | 0.5 s | A relay clunk and a tick of cooling filament |

### 5.6 Lang (`lang/en.json`, inside the level's reserved block)

| Key | English |
|---|---|
| `level-18` | Level 974: Kitty's House |
| `levelhint-18` | You are a guest here. Be a good one. |
| `l974-arrive` | You wake in a pink bedroom that feels as if it has always been yours. Somewhere, a music box is playing. |
| `l974-taken` | Something takes an interest in what you are carrying. |
| `l974-call` | "Here Kitty, Kitty, Kitty!" |
| `l974-ask` | Kitty holds out a long black arm. |
| `l974-gift-taken` | Kitty takes the {0}. You are suddenly, overwhelmingly sleepy. |
| `l974-gift-wrong` | Kitty does not want that. It wants what you brought. |
| `l974-gift-refused` | Kitty does not come. Not today. |
| `l974-wake` | You wake somewhere else, rested. For a while, you feel watched over. |
| `l974-wake-home` | You wake in the Lobby, rested, with less in your pockets than you remember. |
| `l974-offended` | The lights go out. The house is very quiet now. |
| `l974-forgiven` | Somewhere in the house, a light comes back on. |
| `l974-pink-1` | The pink is very calming. |
| `l974-pink-2` | The pink is starting to feel close. |
| `l974-pink-3` | You can't remember the last colour you saw that wasn't pink. |
| `l974-sugar` | The food in the cupboards is all sweets now. |
| `l974-smell-1` | You smell pancakes, the way someone used to make them for you. |
| `l974-smell-2` | You smell chicken soup, the kind you were given when you were ill. |
| `l974-smell-3` | You smell macaroni and cheese, straight from the pot. |
| `l974-smell-4` | You smell birthday cake. |
| `l974-smell-5` | You smell hot cocoa, and a little burnt milk. |
| `l974-meal` | There is a plate on the table that was not there before. |
| `l974-memory-1` | A memory surfaces, soft at the edges: a kitchen table, and someone humming. |
| `l974-memory-2` | A memory surfaces, soft at the edges: a night light, and a door left open a crack. |
| `l974-memory-3` | A memory surfaces, soft at the edges: a toy you lost, and never stopped looking for. |
| `l974-memory-4` | A memory surfaces, soft at the edges: being carried up to bed, half asleep. |
| `l974-pc-title` | Guest |
| `l974-pc-mail` | Mail |
| `l974-pc-internet` | Internet |
| `l974-pc-dreamsleep` | DreamSleep |
| `l974-pc-owner` | Owner: password required. |
| `l974-mail-from` | From: Microsoft · To: New Windows Customer · Subject: Welcome! |
| `l974-mail-body` | *The mod's own paraphrase of the canon e-mail (do not copy the CC-BY-SA text verbatim):* "Greetings, wanderer. If you are reading this, you picked up something cute on your travels, and Kitty liked it. Whatever you found is Kitty's now.<br><br>Kitty is the tall dark shape at the edge of your eye, the one that watches you sleep. It will not hurt you. You are its guest: do not hurt it, do not break its things, and try not to scream when it comes up behind you.<br><br>Kitty keeps the fridge and the cupboards full. Do not stay too long. The food turns to sugar, and the pink stops being kind.<br><br>When you want to leave, hold out the thing you brought and call: Here Kitty, Kitty, Kitty! It will take its gift, and you will wake somewhere just as safe." |
| `l974-internet-1` … `-4` | "Searching… 1 result. A place to start lies near where you will wake." / "Searching… ▒▒▒ ▒▒ ▒▒▒▒▒▒ ▒▒▒▒▒." / "Searching… The page cannot be displayed." / "Searching… ᚲᛁᛏᛏᛁ ᛁᛋ ᚺᛟᛗᛖ." |
| `l974-dreamsleep` | Your dreams are ready. Sleep to start. |
| `l974-dream` | You dream of rooms you have never been in, and some you have. You wake steadier. |
| `block-l974-wall-*` | Pink Wall |
| `block-l974-floor-carpet` / `-checker` / `-bathhex` | Carpet / Checkered Floor / Bathroom Tile |
| `block-l974-ceiling` | Ceiling |
| `block-l974-window-*` | Window |
| `block-l974-downlight-*` | Ceiling Light |
| `block-l974-fairylights-*` | Fairy Lights |
| `block-l974-nightlight-*` | Night Light |
| `block-l974-bed-*` | Little Bed |
| `block-l974-desk-computer-*` | Old Computer |
| `block-l974-fridge-*` | Pink Fridge |
| `block-l974-pantry-*` | Pantry |
| `block-l974-banquette-*` | Banquette |
| `block-l974-catbed` | Cat Bed |
| `block-l974-plushheap-*` | Plushies |
| *(the rest: plain names from §5.2)* | |
| `item-l974-plush-cat` / `-bunny` / `-bear` / `-star` | Cat Plush / Bunny Plush / Teddy Bear / Star Plush |
| `itemdesc-l974-plush-*` | Soft, a little worn, and cute. Something in the Backrooms likes cute things. |
| `item-l974-marshmallow` | Greasy Marshmallows |
| `itemdesc-l974-marshmallow` | Sweet, slick and filling for about a minute. |
| `item-l974-candy` | Pastel Candy |
| `item-l974-strawberrymilk` | Strawberry Milk |
| `item-l974-meal-pancakes` / `-soup` / `-macaroni` | A Remembered Meal (pancakes) / (chicken soup) / (macaroni and cheese) |
| `itemdesc-l974-meal-*` | Exactly the way it used to be made for you. |
| `item-creature-l974-kitty`, `creature-l974-kitty` | Kitty |
| `blockhelp-l974-call` | Call Kitty (sneak, with something cute in hand) |
| `blockhelp-l974-tap` | Fill with water |

---

## 6. Code plan

**Files the level owns** (names per the scaffolding; CONTRACT.md wins):

| File | What |
|---|---|
| `src/Worldgen/WorldLayout.Level974.cs` | The house plan. `PlanKittyHouse(mx, mz)`, cached in `PlanCache<HousePlan>`, with mirror and variations. `BuildLevel974`: the house at offset (6, 7) and solid shell everywhere else. `L974Edge` (shell). Exposed to the systems: `IsHouseCell`, `HouseOrigin`, `HouseSpots(mx, mz)` (watch, sleep-watch, arrival, table, light positions). `L974Stability` 1.3. `L974Temperature` 21. `IsL974ArrivalSpot` (the arrival tile only). `L974WalkThrough` (casings, rug, closet rod) |
| `src/Worldgen/WorldGenerator.L974.cs` | `InitL974`, and `Level974Block`, by rel: floor at 0; walls 1–4 (base, plain, crown, backsplash, tile); ceiling at 5; above it, shell. Doorways: casings at 1–3, lintel at 4. Windows at 2–3. Props at 1 (and 2 for the fridge and pantry), shelves and posters at 2–3, fairy lights at 4, the alcove's slope at 3–4 |
| `src/Thresholds/ThresholdNetwork.L974.cs` | `KittyWake((int X, int Z) house)`, one-way, fixed per house: Level 4's heart (an arrival with `RingFraction` < 0.5, `IsSanctuary` or calm), Level 37 (`IsPoolArrivalSpot`), or 6.1 (`FindSnackroomsArrival`). `L974Walked` / `L974Used` return null: the house has no thresholds of its own |
| `src/Thresholds/ThresholdSystem.L974.cs` | `L974Arriving`: the arrival message. **New hook (ask the coordinator):** `L974Detour(player, passage, ref Link destination)`, called in `Go` and in the elevator riders' callback before `Arrive`. It rolls the detour (§2.3), stores nothing in the network, and redirects to the house |
| `src/Regions/L974System.cs` | Server: house assignment (saved), visits (`l974Visit`, `l974Arrived`, `l974House`, `l974OffendedUntil` as watched attributes), marking brought stacks, Kitty's spawning, the call and gift, drowsiness and waking (`KittyWake`, Kitty's watch for 180 s), offence (`BreakBlock` in level 18, damage to Kitty), lights out (swapping the house's light blocks, a known box of 19 × 17 × 5), overstay drain, smells, memories and meals, the `l974food` pool switch, the dresser, the safety valve. Client: the overstay fog and warped lullaby read `l974Arrived` |
| `src/Entities/AiTaskKitty.cs`, `EntityKitty` (in the same file or `src/Entities/Kitty.cs`) | §4.2. Invulnerable; damage is reported to `L974System`; interact handles the gift |
| `src/Props/L974Blocks.cs` | Block behaviours: `L974Tap` (fills liquid containers with `game:waterportion`), `L974Computer` (opens the dialog), `L974Food` (dispenser stock and pool by hours), `L974Dresser` |
| `src/Regions/L974ComputerDialog.cs` | The client GUI: the Guest desktop with Mail (the e-mail), Internet (once per visit: marks on the map the nearest gate, cache or way out near where this house wakes you, using `WandererNote`'s logic on the `KittyWake` arrival; otherwise a cryptic line) and DreamSleep (sets a flag; the next sleep in the bed gives `l974-dream` and +0.3 stability, once per visit; 974.1 itself is deferred). Owner: "password required" |
| `tools/gen_974.py` | Every asset in §5 (textures, shapes, block types, items, sounds, lang), the Kitty model via `rig.py` (in this script, or in `gen_models.py` if CONTRACT.md says so), `patches/l974-cute.json` |

**Hooks needed in shared code** (most are scaffolded already):

| Where | Change |
|---|---|
| `BuildMacro` | **Skip `ClearDoorways`, `SealPockets` and `OpenGates` for level 18**, as for the Snackrooms. A sealed house reaches no cell edge, so every tile would otherwise be marked Sealed |
| `IsSanctuary` | `Level974 => true` |
| `MenaceSystem` | Band Safe in 18, and for 180 s after a `KittyWake` (`L974System.Watched(player)`) |
| `Roster` | No entities, no sounds for 18 |
| `Protection` | Level 18: everything except the furniture codes in §5.2 is unbreakable. Breaking furniture is allowed, and is reported |
| `MapColors` | Walls `#F09AB0`, floor `#EDD5D2` |
| `AtmosphereSystem` | `L974Air` and `L974Sounds` (scaffolded) |
| `ThresholdSystem` | The `L974Detour` hook (new) |
| `FindArrival` | For level 18, keyed by player (used by `/backrooms goto 974`): the player's own house, `checkEscape: false` |
| `tools/salvage.py` | The `toybox` drop gains `l974-plush-*` at 0.35; suitcases, clothing racks and backpacks as in §3.5 (small, agreed edits) |
| `tools/gen_guide.py` | The handbook text in §8 |

**Harness** (`tools/mapgen`, mode `l974`):
- render one house from above, with its plan legend;
- `validatelevel 974`:
  - every house cell has the 6 rooms and 1 arrival tile;
  - the whole interior is reachable from the arrival tile (a flood fill inside the house);
  - no tile is marked Sealed;
  - no prop blocks a doorway;
  - the doorways are 3 high under 4-high ceilings;
- `links`: `KittyWake` for 50 houses lands on walkable, sanctuary floor in 4, 37 or 6.1, and survives save and load;
- a layout hash showing levels 0–13 byte-identical.

**Verification:**
- headless server (port 42478): `/backrooms goto 974`, `/backrooms dump` round the house, rendered room by room;
- `/backrooms encounter l974-kitty` beside a straw dummy, to check that it spawns, idles, and vanishes when unseen;
- the gift run with a scripted plush.

What only a client can show: its look, the sneak-up, the drowsy fade.

---

## 7. Survival role

| | Level 974 |
|---|---|
| Teaches | Manners, and the cost of comfort |
| Gives | The one truly safe house: sleep, light, running water, food that comes back, a fixed route to a safe place, cute clothes |
| Takes | A cute thing per visit; hours (the pink); nutrition (sugar); everything, if you break its things |
| Fits the loop | A lucky refuge you cannot plan on (unless you hold a plush on purpose), never a home: the anchor rule still wakes you in Level 0, and a temporal gear will not take hold here |

---

## 8. Handbook text (`tools/gen_guide.py`)

**The Levels: Level 974**

> **Level 974, Kitty's House.** Not a ring, and not a place you can walk to. Cross into any level with something
> cute on you (a plush, a flower) and, once in a while, you are taken here instead: more often if you hold it in
> your hand. A small pink house with no way outside; its windows are paintings. It is the safest place in the
> Backrooms: lights, running water from every tap, a bed you can sleep in, and a fridge and a pantry that fill
> themselves again. **Kitty** lives here: very tall, faceless, black as cloth, and it will never hurt you. It
> watches. **Be a good guest:** break anything in the house, or strike Kitty, and the lights go out, the food is
> gone, and Kitty will not see you for a day. **Do not stay long:** after a day the pink stops being calming and
> starts to wear on you, and the food turns to sugar. **To leave**, hold the cute thing you brought, sneak and use
> it, and call. Give Kitty what it holds out its arm for, and you fall asleep, and wake somewhere safe, always the
> same place for your house. The old computer's e-mail says the same.

**Ways Between Levels**, a new section, *Taken*:

> - Any level, any threshold, carrying something cute: now and then, Kitty's House (Level 974) instead. No way
>   back.
> - Level 974, giving Kitty the cute thing you brought: you fall asleep and wake in a safe place (Level 4, 37 or
>   6.1), the same one every time for your house.

**What Lives Here**:

> **Kitty** (Level 974). A figure three metres tall, faceless, matt black, its arms and legs ending in points. You
> will rarely see it move: it is simply somewhere else when you look again, in a doorway, at the end of the hall, by
> your bed while you sleep, behind you. It never harms anyone. Leave its things alone. Hold out what you brought and
> call it ("Here Kitty, Kitty, Kitty!") and it comes to take its gift.

**Salvage and Recipes**, finds:

> Plush toys (Level 9's toy boxes, now and then a suitcase or a lost backpack) are cute. So is what you find in
> Kitty's dresser. Strawberry milk, Greasy Marshmallows and remembered meals come only from Kitty's kitchen.

---

## 9. Decisions for the user

1. **Which Level 974.**
   - **Recommended:** the Wikidot "Kitty's House", a sealed pink house with a harmless Kitty.
   - Alternatives: Fandom's town with the Loving Household inside it (bigger, but the sealed house is the famous
     image); *Escape the Backrooms*' look-away killer (contradicts canon).
2. **How you get in.**
   - **Recommended:** any network crossing with something cute on you, 1 in 20 (1 in 6 if held), never within 2
     in-game days of the last visit. Thin spots, gates, the King's trial and the debug teleport are excluded.
   - Alternative: also a deliberate door (see 11).
3. **Where you wake.**
   - **Recommended:** a safe place fixed per house: Level 4's heart (50%), Level 37 on a lit deck (25%), the
     Snackrooms (25%). This is canon's "a safe level", and Fandom wakes in Level 4.
   - Alternative: wake where the threshold you were crossing was taking you (the detour as a pure delay).
4. **When you fall asleep.**
   - **Recommended:** at once, after 4 s of drowsiness (the article).
   - Alternative: the next time you sleep in the bed (the e-mail).
5. **Kitty never harms anyone, and is never seen walking**: it is simply elsewhere, and it glides only to make way
   or to take its gift. **Recommended:** yes.
6. **Offence.** **Recommended:** lights out, food gone, −0.4 stability, and the gift refused for one in-game day,
   then forgiven.
7. **If the brought thing is lost.** **Recommended:** after a day without it, Kitty takes any cute thing (the
   dresser's clothes too), but you wake in Level 0. Dying is the other way out.
8. **Size.** **Recommended:** 17 × 15 inside, one storey, 4-block ceilings (about twice canon), to fit Vintage
   Story's scale and Kitty's 3.2 m.
9. **Level 974.1 (DreamSleep and the Dwellings).**
   - **Recommended:** defer. The computer's DreamSleep gives a one-off dream (+0.3 stability) after a sleep in the
     bed.
   - The Dwellings (floating lavender room frames, low gravity) would make a striking later sub-level.
10. **Multiplayer.** **Recommended:** one house per player, kept for good. Players taken together share the taker's
    house.
11. **A deliberate way in from the Hub** (a pink door that opens only for someone carrying something cute; one-way,
    "taken"). **Recommended:** yes, if the Hub's agent agrees; otherwise the detour alone.
12. **Mascots.** **Recommended:** original look-alikes (a round grey cat, a strawberry bunny, a smiling star…), no
    Sanrio or San-X characters.
13. **The computer's Internet hint** (marks a gate, cache or way out near where you will wake). **Recommended:** yes,
    once per visit.
14. **Timings.**
    - **Recommended:** the pink is kind for 18 in-game hours, then wears on you.
    - Food turns half to sugar after 24 h and all of it after 48 h.
    - Remembered meals at most once a day.
15. **Order of work.**
    - **Recommended:** the house and its blocks first, then the threshold detour and the gift with a placeholder Kitty
      (a tall black box).
    - Then the Kitty model and AI, then food, the computer and the pink's timers.

---

## Manifest changes (phase 2)

Written by the **code agent** (2026-10-07). The generator and systems look up exactly these codes; they override §5
where they differ. A missing block falls back to plain concrete/air and is logged once, so the level works before
the assets exist.

**Facing suffix** `-{north,east,south,west}` = the way the object's *front* faces (into the room). Things that
hang on a wall (shelf, poster, frame, mirror, towel rail, cat clock, night light, fairy lights) and the closet rod
are placed in the room-side block next to the wall, so their shape sits against the side **opposite** the facing.
VS `rotateY` is counter-clockwise from above: model the north-facing shape, then east = 270, south = 180, west = 90.

**Structure and lights** (no facing unless shown):
`l974-wall-{plain,base,crown,backsplash,bathtile,bathtilecap}`, `l974-floor-{carpet,checker,bathhex}`, `l974-ceiling`,
`l974-slope-{north,east,south,west}` (suffix = the side the slope *descends* toward: its low edge),
`l974-lintel-{ns,we}` and `l974-casing-{ns,we}` (`ns` = the passage runs north-south, i.e. through a west-east wall),
`l974-window-{bl,br,tl,tr}-{clouds,hills,rainbow,sunset}-{facing}` (left/right as seen from inside the room, b = rel 2,
t = rel 3), `l974-downlight-{on,off}`, `l974-fairylights-{on,off}-{facing}`, `l974-nightlight-{facing}`.

**Props:**
- `l974-bed-{hearts,strawberries,stars}-{head,feet}-{side}`: **copy vanilla `game:blocktypes/wood/bed.json`**
  (class `BlockBed`, `entityClassByType "*-head-*": "Bed"`, variant groups in this order: bedding, `part`, `side`).
  `side` is vanilla's: the direction from the head toward the feet.
- `l974-nightstand-{f}`, `l974-plushheap-{a,b}-{f}`, `l974-desk-{plain,computer}-{f}`, `l974-chair-{desk,dining}-{f}`,
  `l974-dresser-{f}`, `l974-closetrod-{f}` (at rel 3), `l974-rug-{nw,ne,sw,se}` (a 1 px slab, walked over, no
  collision), `l974-fridge-{lower,upper}-{f}`, `l974-pantry-{lower,upper}-{f}`,
  `l974-counter-{plain,corner,sink,canisters,utensils}-{f}`, `l974-stove-{f}`, `l974-banquette-{straight,corner}-{f}`,
  `l974-table`, `l974-toilet-{f}`, `l974-basin-{f}`, `l974-bathtub-{head,foot}-{f}` (f = the way the foot end points),
  `l974-catbed`.
- **Corner pieces** (counter, banquette): backs on the side *opposite* the facing and on the facing's *right*
  (clockwise: a north-facing corner has backs south and east).
- Wall things: `l974-shelf-{plush,figures}-{f}` (rel 3), `l974-poster-{cat,bunny,rainbow,star,toast,frog}-{f}` (rel 2),
  `l974-frame-{white,gold}-{f}` (rel 2), `l974-mirror-{f}` (rel 2), `l974-towelrail-{f}` (rel 2), `l974-catclock-{f}` (rel 3).

**Dropped:** `l974-archcasing` (the archway has a lintel only) and `l974-doorleaf` (doorways are open casings).
The counter's utensil colours are one variant (`utensils`), not three.

**Block classes** (registered by the code in `src/Regions/L974System.cs`; set them in the blocktypes):
`BackroomsL974Food` on `l974-fridge-*` and `l974-pantry-*` (attribute `l974food`: `"fridge"` / `"pantry"`),
`BackroomsL974Tap` on `l974-counter-sink-*`, `l974-basin-*`, `l974-bathtub-*`, `BackroomsL974Computer` on
`l974-desk-computer-*`, `BackroomsL974Dresser` on `l974-dresser-*`. Everything else: plain `Block` (the house's
structure is made unbreakable by `Protection`; furniture breaks, and breaking it is the offence).

**Entity** `entities/l974-kitty.json` (code `l974-kitty`): `class: "EntityKitty"`; **no `taskai`** (Kitty is driven by
`L974System`); server behaviors `controlledphysics` only (no `repulseagents`, no `health`, no `harvestable`); client
`interpolateposition` and the animations by name: `idle` (default), `headtilt`, `glide`, `stoop`, `peek`, `ask`,
`take`, `sleepwatch`, `kneel`. Hitbox 0.7 × 2.9, eye height 2.9, `"attributes": {"invulnerable": true}`.

**Sounds** looked up by the code: `backrooms:sounds/ambient/974/{lullaby,lullaby-warped,fridge,creak*,chime,mail,drowsy,lightsout}`,
`backrooms:sounds/creature/974/{rustle*,purr,exhale}`.

**Items**: `l974-plush-{cat,bunny,bear,star}`, `l974-marshmallow`, `l974-candy`, `l974-strawberrymilk`,
`l974-meal-{pancakes,soup,macaroni}`. Cute = item attribute `backroomsCute: true` (or the same bool on a stack).
The Hub's pink door calls `Backrooms.Regions.L974.CarriesCute(IPlayer)` (and `L974.IsCute(ItemStack)`).

**Lang keys** the code uses: all of §5.6, plus `l974-gift-none` ("You have nothing cute to give."),
`l974-detour` (shown on arrival by detour: "Something takes an interest in what you are carrying, and the world goes pink.").

More keys and names the code uses (2026-10-07, code agent):
- Lang: `l974-waypoint` ("Where Kitty will let you wake"), `l974-internet-searching` ("Searching… (it takes a while)"),
  `blockhelp-l974-tap` (as §5.6). `l974-internet-1` is the hint that comes with the map mark; 2-4 are the cryptic ones.
- Random sounds are played as `creak*` and `rustle*`: name the files `creak1.ogg`…`creak3.ogg`, `rustle1.ogg`…`rustle3.ogg`.
- The plush items: `itemtypes/974/l974-plush.json` with variant group `type` (`cat`, `bunny`, `bear`, `star`), so the
  codes are `l974-plush-cat` etc. (`tools/salvage.py` already drops them from toy boxes, suitcases and backpacks).
- Meals: `l974-meal-{pancakes,soup,macaroni}`; the code spawns one on the dining table now and then.

**Asset agent (2026-10-07), `tools/gen_974.py`** (with `gen_974_tex.py`, `gen_974_kitty.py`, `gen_974_sounds.py`). Built to the code
agent's list above, which won over §5 everywhere they differ:
- 34 block types, 274 variants, 84 shapes; 143 textures; 4 item types (11 items); Kitty (`entities/l974-kitty.json`, shape and
  texture in `entity/974/`); 15 sounds; `patches/l974-cute.json`; 114 lang keys (the level's placeholders replaced, the code
  agent's extra keys included).
- Wall hangings (`shelf`, `poster`, `frame`, `mirror`, `towelrail`, `catclock`, `nightlight`, `fairylights`) are thin
  non-solid blocks in the room-side tile, against the side opposite their facing, as listed above; no collision.
- `l974-slope-{side}`: a smooth 45-degree plane (backed by fine steps) with a white trim strip along its low edge;
  collision two stepped boxes.
- The counter `utensils` crock is mint. `l974-nightstand` has no on/off state: its lamp is always lit (light 8).
- Block classes as listed (`BackroomsL974Food`, `BackroomsL974Tap`, `BackroomsL974Computer`, `BackroomsL974Dresser`);
  extra attributes the code may use: `l974structure: true` on the house's fabric, `l974furniture: true` on furniture,
  `l974light: true` on downlights and fairy lights, `l974clothes` (six vanilla codes) on the dresser.
- Kitty's animations: `idle` (default), `headtilt`, `glide` (also mapped as `walk`), `stoop`, `peek`, `ask`, `take`,
  `sleepwatch`, `kneel`, plus `vanish` / `appear` (0.25 s stretch) if wanted.
- Vanilla cute things checked against 1.22.7: `game:blocktypes/plant/flower.json`, `plant/flower-lupine.json`,
  `aquatic/seashell.json` get `attributes.backroomsCute = true`.
- Not built (dropped above): `l974-archcasing`, `l974-doorleaf`; the bath mat was not added.
