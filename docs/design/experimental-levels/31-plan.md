# Level 31 "Roller Rink": prototype plan

Internal id **24**, `WorldLayout.Level31`, tag `31`, blocks `l31-`, method infix `L31`, region west-north-west (BACKLOG batch 2).
Prototype only: disconnected, cheats menu / `/backrooms goto 31`, no entities, thresholds, loot or handbook.
Reserved: `WallPattern` 240, `FloorKind` 249, `CeilingKind` 96-103, `Props` 700-739, salts 0x2400-0x24BF, title keys 2401-2499.

## 1. What the lore says

**No conflict:** Wikidot's Level 31 is the roller rink, and Fandom's text is the same page.
- Wikidot, https://backrooms-wiki.wikidot.com/level-31 ("Roller Rink"); Fandom, https://backrooms.fandom.com/wiki/Level_31
  (via `api.php?action=parse`). Class 1, **Safe**, Stable, minimal entity count. Cold in places: about 8 C where HVAC leaks.
- A 1990s roller rink "hundreds of miles" wide, probably looping (non-Euclidean: corridors loop or cross without joining).
  Many chambers of shiny surfaces (floor, walls, ceiling reflect the light). Floor: smooth, freshly cleaned concrete (slippery),
  the rink itself wooden, bordered by polymer covering. Some rinks huge, some tiny. Some rooms carpeted with glowing carpet
  (as Level 25, whose "mirror" this level is called).
- Light: fluorescent tubes in coloured mixes, a different hue per room; neon strips in the connecting hallways. Silent when
  healthy, a ballast hum sometimes. Dim "emptiness" rooms exist.
- Sound: muffled pop radio from ceiling speakers, chosen by a DJ station on the south side of the rink (a docile Faceling at
  times); skates and laughter heard "from above". Pizza and soda smell near the food court.
- Sub-zones: **Rink** (largest, loops); **Arcade** to the east (loops back to its north entrance; modern cabinets and pinball, a
  few 1980s cabinets: Q*bert, Donkey Kong, Space Invaders; green-card dispenser at the entrance); **Food Court** off the arcade
  (small dining area, counter: pizza, wings, foot-long hot dogs, soda fountain); **Skate Rental** past blue walls near the food
  court (counter, US size chart, the Coach); **Cinema** to the north (dark, TV screens, big TV, three stepped rows of metal
  benches); a back arcade area with covered machines. HVAC ducts and pipes in corners, puddles, flooded rooms.
- Entities: docile Facelings, the Coach. Items: free food, skates, green cards. Exits to Levels 40, 70, 232: not built.

## 2. The level in this mod

Round noclip region, radius `max(40, spawnMacroX / 50)` cells (320 full size), cell 32 blocks, band 40 tall. Everything derives
from world coordinates and `Hashing.Hash(seed, a, b, salt)` (salts 0x2400 up); no per-region state.

**Skeleton: complexes on a jittered lattice.** A complex is 5 x 4 cells (160 x 128 blocks), one per lattice slot, its origin
jittered +-1 cell by `Noise2`/hash so the grid does not read. Each is a `PlanCache` plan (like 52's wings), laid out once from
`Hash(seed, cx, cz, 0x2410)`, possibly transposed. Contents:
- **Rink hall** (always): 88 x 56 blocks, 8 high. Floor `l31-rinkwood` as a stadium-shaped oval track (turn radius ~10) with a
  painted centre island; a 6-wide **skirt** (polymer tile) with a low rail; bench rows and a **DJ booth** on the south skirt
  (speaker stacks, turntable, glass); mirror strips on the walls and a disco ball at the centre. One rink in five is the
  "tiny" variant (40 x 28, 5 high).
- **Lobby** (always, on the side facing the next complex): 24 x 20, carpet, front counter, lockers, poster wall, size-chart sign.
  Doors to the rink and to the back corridor.
- **Annexes**, 1-3 per complex from the hash, packed in the ring around the rink (rooms 20-30 wide, 4 high): food court (tables,
  counter, soda machine) with skate rental (blue walls, counter, shelves) beside it, 40%; arcade (a 40 x 30 room of cabinet rows,
  two doors on opposite sides so the walk is a loop), 55%; cinema (dark, big screen, stepped benches), 12%; bathrooms (tile), 60%;
  storeroom / HVAC room (ducts, a puddle), 35%.
- **Back corridors:** a 4-wide service ring (concrete, pipes, a dead neon) joining lobby, annexes and an `EdgeHall`-style carve to
  the neighbours at the complex rim, so a plan wall never seals a neighbour.
- **Neon halls between complexes:** on each lattice line a 5-wide, 5-high hall with neon rails, a carpet runner and mirror panels;
  1-3 cells of filler (bend, alcove, empty lit room). One hall in four gets a **non-Euclidean touch**: a slow 20-block sidestep, two
  halls drawn crossing at a junction with no door between them, or a hall that curls back to its own start. Cosmetic only: no portals.
- **Emptiness rooms:** 1 slot in 10 is a dim bare room (concrete, one flickering tube) instead of a complex; a glowing-carpet room
  (`l31-glowcarpet`) is 1 in 15.
- **Heights:** halls 5, annexes 4, rink 8 (ceiling at rel 9, no band depth change, as 52's gym), tiny rink 5, cinema rows step up
  1 block each (ceiling 6 there). Floor level, no drop. At the rim a hallway is carved inside the edge (`CarveEdgeHall`); solid
  nothing outside, as 188 and 52.

**Tile fields** (`FloorKind` 249 = `L31Floor`, `WallPattern` 240 = `L31Wall`; the builder reads the tile): `Zone` = rink, skirt, lobby,
rental, food, arcade, cinema, bath, hvac, corridor, neonhall, empty, carpetroom; `Detail` = hue index 0-5 (the room's tube colour,
from `Hash(room cell)`) and fixture state; `Variant` = prop facing or court stripe direction.

**Light.** Tube strips every 8 blocks; each room has one of six hues (magenta, cyan, amber, green, violet, white) as `l31-tube`
variants, so the hue is the block. Rink: a ring of coloured tubes plus a lit disco ball block. Arcade: mostly the cabinet screens.
Cinema nearly black (screen only). Halls: neon rails. 7% dead, 5% flickering per fixture, as 52.
**Fog:** indigo, about `(0.008, 0.10, 0.07, 0.19)` in the 52 format (r g b), thicker and darker in cinema and emptiness rooms
(0.02), a warm tint in the food court. **Temperature:** flat 12 C (lore's 8 C only in HVAC rooms). **Stability** 1.1, danger 0.
**Sound** (new `tools/gen_31.py` in the `gen_level_sounds.py` style): a ~100 s synth pop loop (four-chord tune, kick/snare/hat,
saw bass, square lead) low-passed near 1.8 kHz so it reads as ceiling speakers; a ballast hum bed; rare skate-roll rumble and
distant laughter (reuse `laughter()` from Level 94, filtered); an arcade bleep bed (reuse `gen_3999_sounds` if suitable); cinema
room tone. Music in rink, lobby and halls; arcade bed only in the arcade; the cinema gets room tone only.

## 3. Assets

**Reuse (no new files):** Level 3999 `neonrail`, `neonrailcorner`, `neonsign`, `neonlamp`, `neondead`, `neonceiling`, `neonwall`,
`cabinet` (+ `cabinet-dead`), `skeeball`, `pinball`, `claw`, `airhockey`, `prizecounter`, `ticketpile`, `dance`, `magentatile`,
`pooltile`, `reception`, `vending`, `bench`, `booth`, `couch`, `trashbin` (all `l3999-`); Level Fun `fun-speaker`, `fun-stringlights`,
`fun-retrocarpet`, `fun-parquet`, `fun-vinyl`, `fun-screen`, `fun-counter`, `fun-table`, `fun-chair`, `fun-poster`; `level5/hotelwood`,
`turntable`; `level4/officeceiling`, `officeglass`, `partition`, `vendingmachine`; `fluorescentlight`; `concrete`; `detail/` props from
`tools/detail_manifest.json` (`cafetable`, `cafechair`, `snackvending`, `snackcounter`, `bench`, `foldingchair`, `trashcan`,
`wetfloorsign`, named in 52's Status; confirm each exists before use).

**New (5, all `l31-`):**
1. `l31-rinkwood`: polished maple boards, 8 px planks with a glossy highlight and 6 px lane stripes; variants plain, stripe NS, stripe WE,
   centre-island swirl.
2. `l31-mirror`: wall mirror panel, silver with a faint blue tint, bevelled edge and a diagonal sheen; variant `ball`: 16 px facet grid, lit.
3. `l31-tube`: ceiling light strip, 4 x 1 shape, white housing with an emissive tube; six hues x on / flicker / dead.
4. `l31-glowcarpet`: dark carpet with 1990s teal and magenta confetti squiggles and an emissive speckle, light level 5.
5. `l31-skatewall`: rink wall with a painted stripe band (blue lower, chrome rail); variants `blue` (rental wall) and `chart` (flat
   sign with a size chart of numbers).
Optional 6th, drop if over budget: `l31-skates`, a shelf prop of roller skates with coloured wheels.

## 4. Lang strings (`en.json`)

- `"level-24": "Level 31: Roller Rink"`
- `"levelhint-24": "The music never reached the rink. The rink keeps skating anyway."`
- `"levelname-24": "Level 31"`
- `"level-2401": "The Rink"`, `"level-2402": "The Arcade"`, `"level-2403": "The Food Court"`, `"level-2404": "Skate Rental"`,
  `"level-2405": "The Cinema"` (a `Zone` maps to one of these)
- Blocks: `"block-l31-rinkwood-*": "Rink Boards"`, `"block-l31-mirror-*": "Mirror Panel"`, `"block-l31-tube-*": "Coloured Tube"`,
  `"block-l31-glowcarpet-*": "Glowing Carpet"`, `"block-l31-skatewall-*": "Rink Wall"`.

## 5. Open questions (recommendation each)

1. **Rink size?** Recommendation: 88 x 56 and 8 high: fits the band untouched. A giant single track would need a per-level band depth.
2. **One huge rink or one per complex?** Lore: loops, the largest part. Recommendation: one per complex, repeating every ~160 blocks,
   joined by neon halls.
3. **Music: one loop or per zone?** Recommendation: one muffled pop loop (~100 s) everywhere but cinema and rental, plus an arcade bed;
   no DJ-choice system.
4. **Non-Euclidean halls?** Real loops need teleports or overlapping plans. Recommendation: wall-only crossings and a curl-back hall;
   no portal logic in the prototype.
5. **Room colour: block hue or fog?** Recommendation: block hue (six `l31-tube` variants); fog stays a fixed indigo.
6. **Level 25 mirror carpet?** Level 25 is not built. Recommendation: glowing carpet as a rare room only; the "mirror" link is lore text.
7. **8 C cold?** Recommendation: 12 C flat; the cold only in HVAC rooms, with a puddle prop, if time.
8. **Are `l3999-cabinet` textures right for the 1990s?** Recommendation: reuse as they are; revisit only if a screen looks too modern.

## Status (prototype built, 2026-10-17)

**Built.** `WorldLayout.Level31.cs`: neon halls on a lattice every 128 blocks each way (5 wide, 5 high, x or z mod 128 in
1-5): Level 3999's galaxy carpet, black ceiling, a 3999 neon tube down the middle every 4 blocks (one colour per stretch
between crossings, 7% dead), 3999 neon strips at the foot of both walls wherever there is wall behind, mirror panels on the
complexes' outer walls every 8, the odd bench or bin; crossings in black marble under a magenta panel. Between them a
**complex** (121 x 121 inside, a `PlanCache` plan, mirrored and/or transposed by hash): the **rink hall** in the middle
(85 x 69, 7 high; an oval of `l31-rinkwood` with rounded corners inside an `l31-skatewall-dasher` barrier with four 3-wide
gaps, a painted lane line along the straights and a swirl centre circle; a 6-wide retro-carpet skirt with benches along
the near wall; the DJ booth on the far skirt (3999 reception desk and dance screens); `l31-mirror` panels round the walls;
two rings of coloured `l31-tube`s, white panels over the skirt, the `l31-mirror-ball` disco ball over the centre); round it
a 4-wide concrete **service corridor** (fluorescent panels, 10% dead / 8% flickering, a pipe run along its outer wall) with
passages out to the halls on three sides; and the rooms: front band **snack bar** (55%; snack counters, fryers and stoves,
café tables and chairs, machines), **skate rental** (55%; blue walls, counter, shelves, benches, size chart), the **lobby**
(always: 7-wide front doors onto the hall, counter, couches, lockers (Level 52's), size chart, vending machines) and an
**arcade** (65%; rows of 3999 cabinets back to back with aisles, pinball and claw machines at the row ends, skee-ball, a
prize counter; a second door onto the hall makes the loop); sides and back: bathrooms (glazed tile, toilets, sinks; at least
one per complex), HVAC (concrete, wet floor, machinery; 8 C), store rooms, cinemas (dark, 6 high, Level Fun's screen,
bench rows), second arcades and snack bars, lounges, glowing-carpet rooms. One complex in ten is an **emptiness** (one dim
bare 121 x 121 room, concrete pillars every 12, 13% of its panels alive; a third of them in glowing carpet and unlit).
The rink is the 5-high "tiny" one in one complex in five and wherever the complex or the cells round it are not all Level
31. Every room's door is onto the corridor; wall height and material follow the most telling room beside each wall.
Rim: `CarveEdgeHall`. Arrivals: halls, crossings and lobbies only. Stability 1.1; temperature 12 C (in `L31Temperature`;
`LevelTemperatures[24]` still holds the scaffold's 16, left alone because the line is shared), 8 C in HVAC rooms.
Air: indigo `(0.008, 0.10, 0.07, 0.19)`; cinema, emptiness and glowing-carpet rooms `(0.02, 0.04, 0.03, 0.08)`; snack bar
warm. Titles 2401 The Rink, 2402 The Arcade, 2403 The Snack Bar, 2404 Skate Rental, 2405 The Cinema. Sound: one new loop
(`sounds/ambient/31/rinkmusic.ogg`, 32 s of 120 bpm four-chord synth pop, low-passed at 1.5 kHz with a room tail, seamless),
loudest on the rink, quieter in lobby/halls, rooms and corridor, gone in cinema/emptiness/carpet rooms (End's room tone
there); Level 3999's attract jingles now and then in arcades; the coloured tubes that give light hum.

**Assets** (`tools/gen_31.py`, 5 codes): `l31-rinkwood` (plain/stripens/stripewe/centre), `l31-skatewall`
(stripe/plain/blue/chart/dasher), `l31-mirror` (north/east/south/west mirror on one face of a wall cube; `ball`, a JSON
shape, light 16), `l31-tube` (6 hues x on/lit/flicker/off; flicker is `BackroomsFlicker`), `l31-glowcarpet` (light 5).
Reused: Level 3999's neon ceiling/dead/rail, carpets, black marble, black and acoustic ceilings, midnight wall, cabinets
(and dead), pinball, claw, skee-ball, prize counter, reception desk, dance screen, vending, couch, trash bin; Level Fun's
retro carpet, vinyl, checker mats, screen; hotelcarpet-maroon; Level 52's lockers; Level 3's glazed tile; concrete floor
plain/wet/dark; fluorescentlight; pipes-run; detail props bench, cafetable, cafechair, snackcounter, fryer, stove,
snackvending, drinkfridge, toilet, kitchencounter (sink), pipestack, generator, floorfan, cardboardboxes, metalshelf.
Not used: `turntable` (it plays jazz), `fun-speaker` (it plays Happy Birthday), `fun-stringlights`, `fun-parquet`,
`officeglass`, `partition`, posters, neon signs.

**Skipped:** non-Euclidean halls (sidesteps, crossings without doors, curl-backs), hall filler rooms, stepped cinema rows,
flooded rooms and puddle props (HVAC has wet floor blocks only), the skates shelf (`l31-skates`), DJ speakers, a per-zone
arcade bed and cinema loop (End's room tone and 3999's jingles stand in), skate-roll rumble and distant laughter.

**Harness.** `31stats` (5 x 5 complexes round the centre, full size): 25 complexes, Rink 15 / TinyRink 7 / Empty 3; zones
Hall 8.8%, Crossing 0.2%, Lobby 3.1%, Corridor 8.0%, Rink 18.7%, Skirt 12.2%, Snack 3.1%, Rental 1.1%, Arcade 4.3%, Cinema
2.4%, Bath 4.7%, HVAC 2.8%, Store 4.2%, CarpetRoom 4.2%, Lounge 6.9%, Empty 7.0%, Wall 8.1%; 377 rooms, every room and all
367768 walkable tiles reached from the halls, none sealed. `SPAWN=1000 31stats 3`: 49 complexes, 721 rooms, all 718332
walkable tiles reached. `31stats 2 rim` (west rim): 281 whole rooms (96 clipped by the rim), all walkable tiles reached.
Arrivals 60/60 in a hall or lobby in each. `regions`: 60/60 arrivals for 31, none wrong or in small pockets, full size and
SPAWN=1000; 0.16-0.29 ms a cell. `layouthash`: overall hash `18cfdbc1c530f039` and levels 0-23 unchanged. Headless (port
42485): `blocksweep` 8002 blocks, 0 threw; dumps at 381891,458179 (a rink: boards, centre circle, stripes, barrier, ball,
tubes) and 381840,458130 (a crossing, halls with rails, snack bar, rental, bathroom, cinema): no missing blocks, shapes or
textures, no errors. Floor light: halls 11, rooms 8-13, the rink 2-11 in patches (dimmest between the two rings), dark
rooms 0.

**Found on the way:** the band's top block (rel 9 with the usual band) gets sunlight through the mantle cap, so a light
block with no absorption there (a tube in an 8-high room's ceiling) let a shaft of light 22 down into the room. The rink was
lowered to 7 high (ceiling at rel 8, concrete at rel 9). Level 52's gym (ceiling and its fluorescent panels at rel 9) likely
has the same leak; worth a look.

**Known gaps / check in a client:** facings of the borrowed 3999 props (cabinets, reception desks as counters, couches,
skee-ball lane vs target, prize counter, dance screens), the cinema's hung screen (rel = air) and bench rows, snack
counters and cafe chairs, toilets and sinks; whether the lobby lockers face into the lobby; the mirror panels' side (they
should face into the rink and out to the halls); the disco ball's shape (`drawtypeByType` json, glow) and whether its light
reads; the tube textures (cube panels, not strips); the rink's darkness in the middle; the music's volume and loop seam;
the dasher barrier as full cubes (one block high: players jump it or use the gaps).

## Detail pass (2026-10-30)

Lore: both wikis, reconciled as `lore/31-brief.md` proposes, with the user's decisions (`lore/DECISIONS.md`): Safe
(class 1 / difficulty 0), the Coach (Wikidot) as the one new person, Fandom's Employees Lounge, cold HVAC rooms, glowing
carpet and "Paranoia" as atmosphere only, no Hounds, Level 3999's galaxy carpet replaced by the level's own.

**Built.**
- **Orientation fixed to the lore.** Complexes are never transposed any more (only mirrored north-south), so the arcade
  is always east of the rink, the DJ station always on the rink's south side, and a cinema only in a back band that lies
  north of its rink. The front band's arcade is rarer (45%, was 65%: "the arcade being rarer to enter").
- **Halls and floors:** the level's own dark rink carpet (`l31-carpet-rink`: black with 1990s confetti) in the halls and
  lobbies instead of 3999's galaxy carpet; the crossings in shiny just-cleaned concrete (`l31-floor-polished`); rough
  black carpet round the rink (`l31-carpet-black`, Wikidot); vinyl tile in Skate Rental; quarry tile in the kitchens;
  grey carpet and exposed brick in the lounges.
- **The rink:** the disco ball gave way to Wikidot's star-shaped light at the centre (`l31-star`, three blocks across);
  a short wooden gate with flaps (`l31-gate`, walk-through) in each gap of the barrier; the DJ station on the south skirt
  (two turntables and a mixer facing the boards, PA speakers, the DJ Faceling behind); benches along both skirts, clear
  of the doors.
- **The food court** (Wikidot): kitchen along the far wall on quarry tile (stoves, fryers, a sink, a fridge), its
  EMPLOYEES ONLY door and a lit menu board on the wall behind, the counter with the soda fountain (`l31-fountain`, a
  refilling Almond Water dispenser), the server's spot behind it, the condiment stand by the queue, square tables with
  four orange plastic chairs each, orange and green park benches along both side walls, bins either side of the way out
  under the taped "Please throw away trash and uneaten food here!" sign. Warm light.
- **Skate Rental:** cubby shelves of skates along the far wall, the counter with the Coach's spot behind it, benches,
  the size chart and adverts for brands that do not exist on the blue walls.
- **The arcade:** the green-card dispenser at each door (`l31-dispenser`, gives a green card to anyone without one), a
  handmade OUT OF ORDER sign either side of the corridor door in half of them, 1980s box cabinets (three invented games)
  among the rows (14%), a white door marked 70 on the east wall in one in three (painted, closed).
- **The cinema:** one big 3x2 TV on the far wall (`l31-tv`, lit), three rows of continuous metal benches each a step
  higher (1, 2, 3 blocks), steps down again behind them to the door.
- **The Employees Lounge** (Fandom; every Lounge room): brick, grey carpet, lockers along one wall, kitchenette, a table
  and two chairs, the CCTV desk and two cameras under the ceiling, a custodian's corner (shelf, wet floor sign, boxes),
  a supply box in 40%; silent (no music, room tone, a camera's servo now and then); titled "Employees Lounge".
- **HVAC:** dead radiators along a wall, a pipe run along the far wall, puddles, one in three flooded (a layer of water
  over its middle); 8 C.
- **Loot:** supply boxes in store rooms (0-2), lounges and HVAC rooms; picked over 30% (the level's existing share). The
  food court's free food and the fountain are the level's own supply; notes come from the boxes as everywhere.
- **People** (`src/Regions/L31System.cs`, `tools/gen_31_content.py`): **the Coach** (`l31-coach`: the Faceling model
  with a new striped shirt and name tag; vanilla dialogue `config/dialogue/l31-coach.json`: first meeting and his name
  for you (`{{playername}}`, remembered per player), the free lesson which gives **rink skates**, techniques, how to live
  here, the shadows, the way out (the lore's exits, "not there today"), why he tells people to go; he sighs if you
  decline); **staff Facelings** (`l31-staff`: the food court's server in red with a blank name tag, and the DJ): put
  down at their marked spots while anyone is within 40 blocks, never saved, cannot be hurt. The server feeds a player
  for free every 1.5 in-game hours (pizza, pepperoni, wings or a foot-long hot dog, 60% with an Almond Water); anything
  left on a food court's floor for 9 s is swept up and its dropper refused for a day. After 36 in-game hours in the
  level (and every 12 after) the Coach finds the player by name and says it is time to go. The director puts down
  ambient Facelings (Safe band, one within 100 blocks), nothing hostile.
- **Rink skates** (`l31-skates`, foot clothing with its own shape): +30% walk speed in this level on boards, tile and
  concrete, nothing on carpet. The Fandom penalty (stolen skates send you to Level 0) is in the notes and handbook only.
- **Paranoia:** about once a minute per player in the level, a still black figure (`l31-shadow`) at a dark spot (light
  5 or less in the cinema, empties, glow rooms, HVAC, store rooms or the corridor) 13-23 blocks off; gone at 9 blocks or
  after 25 s. No AI.
- **Sound:** skates on boards and laughter "from above" (one-shots 9 blocks overhead every 25-60 s on the rink, halls,
  lobbies and food court; the laughter reuses the mod's existing laughter); a CCTV servo and chirp in the lounge.
- **Notes:** six (`gen_notes.py`, track `l31`, level 24): the diarist J. (Wikidot's Jonathan), Dez, the M.E.G.
- **Handbook:** its own page "Level 31: The Roller Rink" (`gen_guide.py` `PAGES["level31"]`, registered in
  `GuideSystem.Added`). Titles 2401-2406 (2403 is now The Food Court, 2406 Employees Lounge). The level's lang lines are
  one block after `levelname-24`; `tools/gen_31_lang.py` moves the lines gen_notes/gen_guide append back into it.
- **Assets:** `tools/gen_31_props.py` (20 new blocks: carpets, floors, brick, signs, chair, table, park bench,
  condiments, fountain, DJ desk, speaker, gate, star, card dispenser, retro cabinet, skate shelf, cinema bench, TV, CCTV,
  monitors), `tools/gen_31_content.py` (people, dialogue, items, sounds, the lang block).

**Choices against the brief.** Every food court has its server and every rental its Coach (the level loops, so "the"
Coach is met in every rental, as Wikidot's Coach is found "almost everywhere"); the Coach's "lead me out" names the
lore's exits but leads nowhere (no thresholds on this branch); the green card is a keepsake (the reused Level 3999
cabinets and prize counters keep their ticket rules); the lounge is every Lounge room, off the service corridor, not
literally behind the kitchen (the kitchen's EMPLOYEES ONLY door is painted shut); the skates give no "no slipping"
(nothing in the mod slips). Left out: non-Euclidean halls (teleports), Venosha camps, the revolving door, glow-carpet
"mirror" rooms, exposed wiring, the fire alarm.

**Own inventions** (not in the lore): the three invented 1980s cabinet games and the advert brands; the Coach's exact
lines (built from Wikidot's account); the food cooldown and the day's refusal; the skates' +30% and the carpet rule; the
36-hour "time to go"; the cinema's step-down behind the rows; the CCTV servo sound.

**Check in-game (screenshots):** the star's shape and light over the rink centre; the gates' flaps and axis; the DJ
desk facing the boards and the DJ standing behind; the food court's chairs facing their tables, benches facing into
the room, the fountain on the counter line, the menu board and staff door on the far wall, the taped sign over the
bins; the rental's shelves, counter and the Coach facing the customers; the TV's columns left to right and its light;
the cinema benches facing the TV on their steps; the retro cabinets (two blocks tall); the sign faces (not mirrored);
the CCTV cameras' tilt; the Coach's and staff textures; the skates on a player's feet (attached to LowerFootL/R, toe
toward -x); the flooded HVAC water staying put.

### Round 2 (2026-10-31): looked at in the client

The lead's review: every arrival landed in the neon halls (the rink and the rooms were never seen), and the halls' walls
were flat saturated colour planes with mirror tiles that barely read. Four screenshot runs with `tools/clientrig/shots.py`
(showcase spots and random arrivals); what was changed after looking:

- **Showcase spots** (`WorldLayout.Level31.Showcase.cs`, 14): the rink along its boards, the star from a corner of the
  oval, the DJ station with its DJ, the lobby from the hall, the food court and Skate Rental (staff put down by the new
  `/backrooms l31 staff`), an arcade, a cinema (from the top step), the Employees Lounge, HVAC, a bathroom, a glowing-carpet
  room, an emptiness, a neon hall with a Faceling. Each the nearest of its kind to the region's centre, from the plans.
  `/backrooms l31 shadow` puts a Paranoia figure down for testing.
- **Arrivals** may also land on a rink's carpet (about half now do), and every arrival is turned to the longest open
  view (`ThresholdSystem.L31.cs`), not the wall beside it.
- **The halls' walls** are clad (a new `l31-cladding`, thin panels on the hall side, `tools/gen_31_walls.py`), per side of
  each stretch by hash: three in five a 1990s rink mural in UV paint on gloss black (6 x 4 blocks, seamless, its paint
  glowing a little), the rest black lacquer with chrome-framed mirrors two wide and three high in every five blocks
  ("reflective surfaces", "many chambers of shiny surfaces"). The rink's walls the same (each side by hash), and the lobby
  in the mural; the cladding runs over doorways above their openings. The one-block mirror tiles are gone. Every outside
  wall shows the halls the navy rink band at its foot behind the neon strip; doorway lintels take their wall's finish
  (they were pale lavender squares).
- **The DJ station** has a lit neon "DJ" sign on the wall behind it (3 x 2).
- **The cinema** is walled in to sixteen across (it was the back band's full 28: lore says small), with four small lit TVs
  along each side wall (Wikidot's "TV screens"), a red EXIT sign over the way out and a brighter big TV.
- **The Employees Lounge** was one table in a 27- or 45-wide room: now lockers, the kitchenette and two machines, tables
  with chairs in a grid, a bin, the custodian's corner; a wide one is walled off at sixteen across behind a wall of lockers
  with a doorway, past which is the staff's stock room (shelves in rows, boxes at the aisles' ends, maybe a supply box).
- `31stats` takes the rink's carpet as an arrival and names unreached tiles. All tiles reached (a Stack on a sign tile had
  cut the cinema off; signs are marked in Detail instead).
- Checked in the shots: the mural's continuity across blocks (columns run the right way on every face), the DJ facing
  the boards behind his desk, the Coach behind the rental counter facing in, the adverts not mirrored, the food court's
  chairs at their tables, the TV picture the right way round.

**Own inventions this round:** the mural and its design, the lacquer-and-mirror walls, the DJ sign, the cinema's EXIT sign
and small TVs as wall-hung sets, the lounge's stock room, arrivals turned toward the view.

**Still weak:** the rink's upper walls and ceiling are a dark void above the lit boards (as a dimmed rink is, but large);
bathrooms are open rows of toilets with no stalls; HVAC and store rooms are plain; the cinema stays very dark away from
its screens (by the lore).

## Links (2026-10-31)

The level stops being cheats-only: the ways in and out LINKS.md settles for it ("Level 31"), from the lore.

**Built.**
- **In: the wooden door** (Wikidot: "a wooden door in Level 2 or Level 3 that has music playing on the other side";
  Fandom: Levels 3 and 6, "even less frequent in Level 6", "simpler to locate when it occurs"). A varnished four-panel
  wooden door (`l31-door`, `tools/gen_31_links.py`) set in one wall tile of the host's own wall: Level 2's tunnel
  concrete, Level 3's red brick where the cell has any ("the wooden door within the brick walls of a long-forgotten
  electrical station"; else its cinder block or glazed tile), Level 6's dark wall. Solid wall behind it and on either
  side, open floor in front, so it reads as a door that should not be there. Within 18 blocks you hear 2000s bubblegum
  pop through it (`sounds/ambient/31/doorpop.ogg`: 128 bpm, claps, octave bass, a sing-song lead, low-passed and boomy as
  through a door; a positional loop on the client, `AtmosphereSystem.L31.cs`). One cell in 1200 of Levels 2 and 3 rolls
  one, one in 2400 of Level 6 (`WorldLayout.Level31.Links.cs`, salts 0x2420/0x2424; never the spawn cell, the
  Snackrooms, or a tile anything else took; `Unders.L31HostDoor` 352). **Two-way** (walked through): it opens in a lobby of
  the rink beside the lobby's own wooden door (`Unders.L31LobbyDoor` 353, in every lobby's back wall), which leads back to
  where you stood. A lobby door nobody came in by is locked.
- **Out: the Revolving Door** (Fandom: "Going through The Revolving Door will land one in either Level 9, 10, or 11"). In
  the front wall of one lobby in twelve, east of the front doors: Level 3999's glass drum (its shapes, `l31-revolvingdoor`
  with its own threshold kind `l31-revolving`; `Unders.L31Revolving` 354, three tiles, the middle one draws it). Use it:
  **one-way**, to Level 9, 10 or 11, each door always the same one (a third each by the hash of its middle tile, salt
  0x2429). The Coach's "Can you lead me out?" now walks you to the nearest and marks it on your map (Wikidot: he "leads
  you out if asked"; the dialogue's `l31-leadout` trigger, `Regions/L31System.cs`).
- **Out: stealing skates** (Fandom: "trying to steal any roller skates ... an immediate noclip to Level 0, without skates").
  Skate Rental's cubbies now give a pair on right-click; walk out of the rental with it and you noclip into the Lobby, the
  skates gone (`ThresholdSystem.L31Steal`, one-way). The Coach's skates are on loan: leave the level by any way with them
  about you and you come out in Level 0 instead of where the way leads, without them (`ThresholdSystem.L31Redirect`; what
  the way leads to stays written down for the next one through).
- **Text:** the handbook's "Ways in and out" paragraph (en.json only: `tools/gen_guide.py`'s `PAGES["level31"]` still has
  the old one, see below), the hint ("Safe, and it feels like home. Don't stay. The revolving doors lead out; the skates
  do not."), the Coach's out lines and lesson line, arrival and passage messages, the cubbies' help, block names. Three
  notes in the hosts' own tracks under the level's keys (`gen_notes.py`, the L31 block): `l31-in2` (Dez, Level 2: music in
  the pipes, "Pell would have"), `l31-in3` (M.E.G. notice, Level 3: the door in the brick, safe, leads back; the revolving
  doors one way), `l31-in6` (a hand in the dark, Level 6: "Go toward the music"). Levels 40, 70, 232, 25 and 30 stay
  rumours (the white 70 door and the EMPLOYEES ONLY door are painted shut).
- **Harness:** `mapgen <seed> <cells> 31links [reach]`; `L31UseKind` for the `links` mode. **Showcase:** `lobbydoor`,
  `revolving` (inside the lobby), `door-l2`, `door-l3`, `door-l6` (four steps in front of the nearest to spawn).
- **Dev:** `/backrooms l31 door2|door3|door6|door|revolving|skates|steal|where` go through the ways as a player and log
  where they end up.

**Numbers** (seed 12345, full size, `31links`): Level 2 about 6.5 km2, 8 doors (1.2 per km2, one per 900 blocks
square), nearest 1369 blocks from spawn; Level 3 about 10.8 km2, 6 doors (0.56 per km2, one per 1340), nearest 2333;
Level 6 about 18.6 km2, 7 doors (0.38 per km2, one per 1630), nearest 3730. In the level: 20092 complexes, 17997 lobbies
with a wooden door, 1448 revolving doors (4.4 per km2, about one per 480 blocks square; 518 to Level 9, 456 to 10, 474 to
11), the nearest 39 blocks from the region's centre.

**Own inventions:** the door's look (four panels, brass knob), the music itself and its 18-block reach; Level 3's brick
preferred; the lobby's wooden door as the way back and its place in the lobby's back wall; one lobby in twelve with a
revolving door, in its front wall; the thirds between 9, 10 and 11; the cubbies giving a pair (how one "steals"); the
Coach marking the revolving door on your map; the rates (the progression rule's quarter, Level 6 half that).

**Rows for the guide's ways-between-levels table** (for the lead):

| From | Way | To | |
|---|---|---|---|
| Level 2, 3, 6 | a wooden door with pop music playing faintly behind it (rare; rarer in Level 6) | Level 31, a lobby | two-way |
| Level 31 | the Revolving Door in the front of some lobbies | Level 9, 10 or 11 (each door always the same) | one-way |
| Level 31 | walking out of Skate Rental with skates from the cubbies, or leaving the level with the Coach's | Level 0, without the skates | one-way |

**For `tools/gen_guide.py`** (`PAGES["level31"]`, the last section), the text en.json now has:

> **Ways in and out**
> In: a wooden door where no door should be, in the tunnels of Level 2, the brick of Level 3 or the dark of Level 6
> (rarer there), with bubblegum pop playing faintly behind it. You hear it before you see it. It opens on one of the
> rink's lobbies, beside a wooden door that takes you back the way you came. Out: the **Revolving Door** in the front of
> some lobbies, to the Suburbs, the fields of Level 10 or the Endless City (each door always to the same one, and no way
> back through it); ask the Coach the way out and he marks the nearest on your map. **Do not steal the skates:** walk out
> of Skate Rental with a pair from the cubbies, or leave the level by any way wearing the Coach's, and you noclip into the
> Lobby, without them. Wanderers also tell of stairs up from Level 30, a white door marked 70 behind the arcades, an
> EMPLOYEES ONLY door in the food court and an arcade that goes on until it is Level 25; none of them has been found to open.

**Checks.** `expclash` clean; mod and mapgen build, 0 errors. `BACKROOMS_NO_EXP_ENTRANCES=1` layouthash, layout versions 1
and 12: every line for levels 0-20 and the layout hash identical to main's; with the entrances, the Level 2 and Level 6
lines and the layout hash move (no door falls in the sampled Level 3 cells), nothing else. `regions` 60/60 for 31;
`31stats` OK. Headless (port 43132): `/backrooms wayback l31-door` at a door in each of Levels 2, 3 and 6 arrives in a
lobby beside its wooden door, and that door leads back to the floor in front of the host's door; three revolving doors
lead to Levels 10, 11 and 10, each of their tiles to the same place; a dummy in 31, `blocksweep` 11175 blocks, 0 threw,
0 error lines. As a player (client rig, port 43134, `/backrooms l31 ...`): in and back by the doors of Levels 2, 3 and
6 (back exactly where they stood), out by a revolving door to Level 11, out by it with the Coach's skates to Level 0
with the skates gone, a pair from the cubbies outside Skate Rental to Level 0 at once, 0 error lines; the shots show the
lobby's door under the mural, the revolving door's drum in the lobby's front wall, the doors in Level 2's tunnel and
Level 3's brick (Level 6's door spot shoots black: the level is dark). Gate `--fast` PASS. Not tried in a client: the
Coach's "lead me out" waypoint (the dialogue trigger), the door music's loudness.

## Round 3 (2026-11-01): the detailed visual pass

The user: more detailed visuals, multi-block objects and signs where a real place has them, more realistic layouts, still
the lore. Looked at: round 2's final sheet and full shots (`%TEMP%/backrooms-shots/final-r2/31/`), the lead's notes, the
brief and DECISIONS.md, this plan's open points, and Level 3999's arcade and food court, Level 36's signs and Level 52's
rooms as the released/finished levels of the same kind.

### List

Tiers: A must, B should, C nice. One mechanism carries most of the signs and wall things: a **wall mount** (a thin panel or
fixture in the air block in front of a wall, at its own height; `Tile.Pipe` = `Pipes.L31Mount*` with the way it faces,
`Tile.Depth` which part of which mount), so signs several blocks wide can hang over doors and on the cladding.

**1. Layout realism**
1. (A) [done] Skate Rental laid out as a real one: the counter across the room with a pass-through, racks of cubbies behind it in
   rows (not one shelf along the wall), the Coach behind the counter; the customers' side with shoe benches in facing rows
   and coin lockers along a side wall.
2. (A) [done: tables in groups either side of the walk; no queue rail] Food court: a clear walk from the door to the counter (a queue line with stanchions before the till), fewer tables
   in groups, the counter's end with a popcorn machine and a drinks fridge, napkin and straw dispensers on the tables'
   side of the counter.
3. (A) [done] Arcade: a redemption (prize) corner as one object: glass prize cases as a counter, the prize wall behind it, plush
   on top; a pinball row along a wall; the green-card (token) machines at the doors; a photo booth.
4. (B) [done] Rink-side: a snack window on the skirt (a counter against the wall with its menu and the SNACKS sign), skate
   lockers and benches on the side skirts so the skirt reads as the place people sit and lace up.
5. (B) [partly: no lost and found box] Lobby: the admission counter facing the front doors with its price board over it, a trophy case, a jukebox, a lost
   and found box; the couches as a waiting corner.
6. (B) [done] Bathrooms as real restrooms: a row of stalls (partitions and doors), a vanity of sinks under mirrors, hand dryers,
   a bin; the stalls on the far wall, sinks by the door.
7. (C) [partly: the units read weakly in the shots] HVAC rooms with an air handler (a big unit) and pressure tanks rather than scattered props; store rooms as the
   rink's stock and skate-repair room (a workbench, a toolbox, wheels).
8. (C) [done] The cinema's door outside with lit NOW SHOWING poster cases either side (the "ticket booth" the lead asks for, in
   the lore's free cinema: no tickets).

**2. Multi-block objects**
9. (A) [done] Cinema: a bigger "one big TV" (Wikidot): 5 x 3 blocks with a frame and a speaker bar under it on a low cabinet, in
   place of the 3 x 2; the three stepped rows' risers with amber aisle lights.
10. (A) [done] Bathroom stall (a partitioned cubicle with its door ajar and the toilet inside, two blocks tall) and a vanity (basin
    counter with the mirror over it, two blocks).
11. (A) [done] Arcade photo booth (two blocks tall, a curtain, a lit sign) and the prize counter (cases + wall + plush).
12. (B) [done] Jukebox (1990s neon-arch style, taller than a block) and a trophy case (glass, two blocks, trophies on shelves).
13. (B) [done] Disco balls over the rink: the star stays at the centre (Wikidot), a mirror ball hangs over the middle of each
    turn (the lead's "disco ball over the centre"; the star keeps the centre).
14. (B) [done] Rink-side snack window: counter + menu board + sign as one set piece.
15. (C) [done: Level Fun's popcorn cart at the counter's end, the shared drinks fridge] A popcorn machine on the food counter (Level Fun's popcorn cart reused) and a soda / drinks fridge beside it.
16. (C) [done as lighting trusses with par cans] PA speaker clusters hung under the rink's ceiling at its corners (the rink's upper dark was "a void").

**3. Signs and text** (every sign drawn in the generator, read from where a player stands)
17. (A) [done] Over each room's door on the corridor side: SKATE RENTAL, SNACK BAR, ARCADE, RESTROOMS, CINEMA, EMPLOYEES ONLY
    (lounge), STORAGE, MECHANICAL (HVAC).
18. (A) [done] Inside: SKATE RENTAL over the counter (lit), the size boards over the cubbies (SIZES 1-5, 6-9, 10-13), the
    SNACK BAR sign over the food counter, ARCADE in neon over the doors inside, PRIZES over the redemption corner.
19. (A) [partly: one cinema EXIT, the cinema has one door] EXIT signs: over the passages from the service corridor to the halls, over the lobby's front doors inside, both
    of the cinema's (one more).
20. (A) [done] The rink's name (an invention: STARDUST ROLLER RINK, from the star) in neon over the lobby's front doors on the
    hall side and on the rink's north wall facing the DJ.
21. (A) [done] Rink rules board (SKATE COUNTER-CLOCKWISE, NO RUNNING, NO FOOD ON THE FLOOR, ...) on the skirt by the gates, and a
    NO RUNNING / NO STREET SHOES plate at each rink door.
22. (A) [done] The Coach's whiteboard behind the rental counter ("LESSONS TODAY", the session times, a smiley).
23. (B) [done] Session board by the DJ (ALL SKATE / COUPLES SKATE / SPEED SKATE / LIMBO), the lit one now on.
24. (B) [done] RESTROOMS figures plate (MEN | WOMEN) by the bathroom's door, hand-dryer PUSH plates.
25. (B) [done] Admission price board over the lobby counter; WELCOME / hours board in the lobby.
26. (B) [done] EMPLOYEES ONLY on the lounge door; a staff notice board inside (rota, a memo, "DO NOT TOUCH THE SKATES").
27. (C) [done] Fire-extinguisher plates and a fire alarm pull on the corridor walls; posters along the corridor (rink events).
28. (C) [done] Arcade: TOKENS / GREEN CARDS plate over the dispenser.

**4. Detail visuals**
29. (B) [done] The service corridor: rubber skirting/kick plate is too much; instead the door signs, extinguishers, a mop bucket
    and the EXIT signs give it rhythm.
30. (B) [done: food court posters; rental adverts kept] Food court and rental walls: posters and the blue walls' adverts more often; the food court's bare beige walls
    get a menu-side neon and posters.
31. (B) [done] The lounge: posters, notice board (item 26), CCTV stays.
32. (C) [skipped: kept] Arcade carpet / lighting: cabinets give the light; keep.
33. (C) [skipped: kept] Rink: aisle lights / lit floor edge under the barrier? Keep the boards as they are (they read well).

**5. Lore alignment**
34. (A) [done] Keep: star at the centre, DJ on the south, food court's taped sign, orange chairs and park benches, condiments,
    the Almond Water fountain, the green-card dispenser, OUT OF ORDER signs, the cinema's TV and three stepped rows of
    continuous metal benches (no projector: the lore's cinema is a TV), the EMPLOYEES ONLY kitchen door painted shut.
35. (B) [done] The lead's "projector window" and "ticket booth" against the lore's TV-and-benches cinema: no projector; poster
    cases outside instead (item 8).
36. (B) [done] The Coach in a showcase spot close up behind his counter, with the whiteboard.
37. (C) [done] Skates: the cubbies are the "steal" way out (Links); the rack rows keep that use (a cubby rack is still
    right-clickable).

**6. Released-level alignment**
38. (A) [done] Block names in the HUD and pick-block for every new block (lang keys `block-l31-...`).
39. (B) [done: TrueType lettering as Level 36's, the old pixel font kept for the old signs] Signs in the same 3x5 lettering family the level already uses, lit where a real sign is lit, as Level 36/3999 do.
40. (C) [skipped: unchanged] Supply boxes, notes, handbook, sound bed: unchanged (they hold); the handbook page gets one line on the signs if
    space (no; text unchanged).

**7. The lead's balance items (added 2026-11-01 during the round, from the balance review)**
41. (A) [done] The food court's server feeds a player every 6 game hours (`L31System.ServeHours`, was 1.5).
42. (A) [done] A screen over each revolving door naming where it goes (TO LV9 / LV10 / LV11), in Level 36's gate-screen style.
43. (A) [done] The Coach's line about the doors names the Suburbs' danger.

### How it is built

- **Wall mounts** (`WorldLayout.L31Mounts`, `L31MountRun`; `tools/gen_31_round3.py` draws them as `l31-plate-<sign><col><row>`):
  a thin panel or fitting in the air block in front of a wall (or hung in the middle of it), at its own height, its
  columns placed from the viewer's left by the way it faces in the world, so text reads the right way round through
  the plans' mirroring. A floor tile carries one column (`Tile.Pipe` = `Pipes.L31Mount` + facing, `Tile.Depth` the
  column); a doorway's tile carries one for the hall tile in front of it (the rink's name over the lobby's front
  doors, ARCADE over the arcade's hall door, the revolving doors' screens). A mount wins over the halls' cladding at
  its own rows only. Lettering is TrueType (as Level 36's), lit signs glow and give a little light.
- **Set pieces as tall models** (two blocks tall where they need it): `l31-stall`, `l31-vanity` (+ mirror plate),
  `l31-photobooth`, `l31-jukebox`, `l31-trophycase`, `l31-mediacab` under the 5 x 3 TV, `l31-riser` (the cinema's
  step blocks with amber aisle lights), `l31-truss` (`Overheads.L31TrussWE/NS`). Reused: Level 3999's prize cases
  (with plush on them), prize wall; Level Fun's popcorn cart; the shared drinks fridge, AC unit, pressure tanks,
  water tank, workbench, toolbox; the Basement's duct (`Overheads.L31DuctWE/NS`).
- New props `L31Props` 729-737; `Overheads` 352-355 and `Pipes` 352 (the mount; 352-355 with its facing) in Level 31's
  ranges; `expclash` clean.

### Inventions (round 3)

The rink's name STARDUST ROLLER RINK (from Wikidot's star light; the lore names no rink); the rink rules, session
board, prices, hours, posters (couples skate, birthday parties, lessons with the Coach, retro night) and the staff
notice board's notes ("DO NOT TAKE THE SKATES" points at the Fandom rule); the Coach's whiteboard; the NOW SHOWING
cases ("your favorite movie", from Wikidot's cinema that plays your favourite film); the mirror balls over the turns,
the lighting trusses, the rink-side snack window, skate lockers, trophy cases, jukebox, photo booth, restroom stalls
and vanities, the rental's racks and benches, HVAC air handlers and ducts, the store room's repair bench; the
revolving doors' TO LV screens (asked for by the lead).

### Balance notes for the lead

- **The server** (lead's item): `L31System.ServeHours` 1.5 -> **6** game hours between free meals per player (the
  refusal after littering stays 24 h).
- **New water**: the shared drinks fridge (`detail/drinkfridge`, a restocking `BackroomsDispenser`: soda, water,
  Almond Waters) now stands at the end of every food court's counter and at each full rink's snack window (one per
  complex with a full rink, about 60% of complexes, and 23 food courts in `31stats`'s window). The food
  court already had the restocking Almond Water fountain, so the level had water; this adds more of it. If that is
  too much, swap the fridge for a non-dispensing look (one line each in `L31LayRoom`/`L31LayRink`).
- No new food, beds or safe rooms. The skate cubbies on the new free-standing racks give skates like the wall ones
  (the "steal" way out is unchanged).

### What the shots showed

- **Run 1** (`%TEMP%/backrooms-shots/31-r3a/`, 26 spots + arrivals): the mounts read the right way round everywhere
  (room signs, SKATE RENTAL, size boards, the whiteboard, PRIZES, Snacks, the rink's name over the lobby doors from
  the hall and on the rink's wall, TO LV11 over a revolving door, the 5 x 3 TV, the session board by the DJ); the
  trusses and mirror balls fill the rink's dark ceiling; the Coach close up behind his counter. Wrong: the restrooms
  were still 28 x 20 halls with a row of stalls at the far end (walled in to 14 x 11 round their doors since, stalls
  on both sides, vanities and dryers by the door); HVAC rooms read as scattered props and a water tower on legs
  indoors (air handlers and tanks along the far wall under the duct since, no tower); the size boards ran from the
  right in a mirrored complex (fixed); the extinguisher was a red box (rounder since); the food court's front third
  was empty (a fourth row of tables and a jukebox since); the snack window's menu touched its frame (fixed).
- **Run 2** (`31-r3b/`): the rig stopped after five spots on a PermissionError of its own (not the level's); its
  shots (rink, star, DJ, lobby, lobby front) matched run 1's.
- **Run 3** (final, `%TEMP%/backrooms-shots/31-r3-final/`, `sheet.jpg`; the rig counts 27 of 28 spots shot though
  every spot it logs, Level 6's door included, reports ok): the restrooms now read as restrooms (two runs of stalls,
  the vanity under its mirrors); the corridor's SKATE RENTAL and SNACK BAR signs over their doors; the food court
  fuller; the Coach, the prize corner, the snack window, the trophy cases, the cinema's TV, the revolving door's
  TO LV11 screen and a random arrival facing the RINK RULES board all hold. **Still weak:** the HVAC rooms (the
  shared AC unit reads as a low white slab along the far wall; the duct and pipes carry the room), the bare
  glowing-carpet and emptiness rooms (as the lore wants them), the hall arrivals the rig turns to a wall.

### Questions for the user

1. The rink's name STARDUST ROLLER RINK is an invention (the lore names none). Keep it, rename it, or leave the
   neon nameless?
2. The lead asked for a projector window and a ticket booth at the cinema; the lore's cinema is one big TV and
   three metal benches, free. Built: a bigger TV and NOW SHOWING cases outside. Is a projector wanted anyway?
3. Drinks fridges (restocking) at every food court and rink snack window add water to a level that already had the
   Almond Water fountain: keep, or make them look-only?

## Round 4 (2026-11-02): the asset-quality pass

The user: AAA assets, multi-block pieces read as one object, keep refining the level and its lore, share assets with the
other levels where they fit. Looked at: round 3's final sheet and full shots (`%TEMP%/backrooms-shots/final-r3/31/`,
`31-r3-final/scenario/`), the lead's notes, the brief, DECISIONS.md, the element counts of every `l31-` shape (round 3's
"tall models" are 4-14 boxes: the speaker 4, the cinema bench 4, the media cabinet 4, the dispenser 4, the disco ball 6,
the photo booth and jukebox 9, the stall 12, the DJ desks 13, the retro cabinets 14; the TV and the riser one box) and
the other levels' folders for what can be shared (52's lockers already, 120's CRAC units, 36's stanchions, Level 3999's
arcade, Level Fun's popcorn cart). Most rebuilds keep their block codes, so the layout does not move;
`tools/gen_31_round4.py` owns them from now on (run after `gen_31.py`, `gen_31_props.py` and `gen_31_round3.py`; it
overwrites their files for the codes it rebuilds).

### List

Tiers: A must, B should, C nice.

**1. Assets to rebuild to the bar**
1. (A) [done] `l31-skateshelf`: the skates as a real model (boot with a padded collar and tongue, laces, a sole plate, two
   trucks with four coloured wheels each, a toe stop), pairs in the cubbies, the odd pair lying on its side.
2. (A) [done] `l31-skatewall-dasher` (a full cube) -> `l31-barrier`: the rink's barrier as a thin padded wall along the
   boards' edge (kick plate, panel body, a padded bumper on the rink side, a rounded padded top rail, stiles), with
   straight, corner and post pieces chosen from the neighbours so the oval's stair-steps read as one continuous rail.
3. (A) [done: the leaf swung open at each end of a gap, the sill between] `l31-gate`: gates as real gates (end posts with caps, a hinged half-door with a padded top, a latch, swung open)
   in the barrier's gaps.
4. (A) [done] `l31-djdesk` (deck, mixer): a booth fascia with a lit strip, turntables with platter, slipmat, tonearm and pitch
   fader; a mixer with channel faders, knobs, VU LEDs; CD players beside the decks (1990s).
5. (A) [done] `l31-speaker` (4 boxes): a PA cabinet with woofers (cone, dust cap, surround), a horn, corner protectors,
   handles, a grille band.
6. (A) [done] `l31-discoball` / `l31-mirror-ball`: a faceted mirror ball (stepped rings of facets) on a drop rod with a motor.
7. (A) [done] `l31-truss`: a box truss (four chords, rotated diagonal lacing), par cans on clamps and yokes with coloured,
   glowing lenses, a cable loom.
8. (A) [done] `l31-rinkwood` (4 variants): maple strip floor at 32 px with lane sheen, board ends staggered, the lane stripe
   and centre swirl as painted inlays with wear where skaters turn.
9. (A) [done] `l31-retrocab` (shooter, barrels, pyramid): 1980s uprights to the bar: side art, T-moulding, lit marquee in
   its bezel, a recessed CRT with a bezel, a control panel with a ball-top joystick and buttons, a coin door with lit
   coin slots, a kick plate.
10. (A) [done] `l31-pinball` (new; replaces Level 3999's 13-box pinball in the arcade): legs with levellers, a playfield
    cabinet with lock-down bar and plunger, a lit backglass head on its neck, flipper buttons.
11. (A) [done] `l31-photobooth` (9 boxes): a booth with a curtain on a rail (folds), a lit sign, the camera window, a stool
    inside, the photo-strip slot, the coin box.
12. (A) [done] `l31-cinemabench` (4 boxes): the lore's continuous metal bench with cup holders, a perforated seat and back,
    legs bolted down; `l31-riser` with an amber aisle light strip on its nosing.
13. (A) [done: the 5 x 3 TV mount gets a bezel; the media cabinet rebuilt] `l31-tv-*` and `l31-mediacab` (1 and 4 boxes): the big TV with a real bezel and depth, a speaker bar, and a
    media cabinet with doors, a VCR and a DVD deck with lit displays.
14. (A) [done] HVAC air handler: the shared `acunit` (3 boxes) is round 3's "still weak"; reuse Level 120's CRAC unit
    (`l120-crac-lower/upper`, two high, grilles and fans) along the far wall.
15. (B) [done] `l31-stall` (12) and `l31-vanity` (8): partition feet, a door with lock indicator and hinges, the toilet with
    a lid and cistern; the vanity's basins with taps, soap pumps.
16. (B) [done: the table; the chair kept (it holds)] `l31-chair` / `l31-table`: food-court chair with a tube frame and moulded shell; table on a pedestal and a
    cross foot, a napkin holder.
17. (B) [done] `l31-jukebox` (9): a 1990s neon-arch jukebox with bubble tubes, a selector window and grille.
18. (B) [done] `l31-dispenser` (4): the green-card machine with a lit header, a bill acceptor, buttons and a card tray.
19. (B) [done: dispenser kept] `l31-fountain`: the Almond Water soda fountain with its tower, drip tray and taps (the level's own restocking
    dispenser; the shared Almond Water fountain is a wall fountain, so it stays ours).
20. (C) [done: trophy case and CCTV rebuilt; the security desk kept] `l31-trophycase` (26), `l31-cctv` (7), `l31-monitors` (17): check up close, finish if they fall short.

**2. Multi-block set pieces**
21. (A) [partly: lit fascia, decks, mixer, CD decks, stacks; no raised deck (the DJ would float)] The DJ booth as one object: a raised deck under the desks, the fascia with a lit strip facing the rink, the
    speaker stacks either side, the DJ sign over it on the wall.
22. (A) [done] The rink barrier and its gates as one continuous object round the oval (items 2-3).
23. (A) [done] The lighting rig: trusses, par cans and mirror balls read as one rig under the dark ceiling.
24. (A) [done: the till is the shared register, already there] The snack bar: a slushie machine (`l31-slushie`, new: two bowls with augers, lit tops), a till (`l31-till`,
    new: a 1990s register with a pole display), with the menu board and the popcorn cart as one counter.
25. (B) [done: kept] The arcade's prize corner: Level 3999's prize cases and prize wall stay (they hold), plush on them, the PRIZES
    sign; the photo booth beside them.
26. (B) [done] The cinema as one object: TV, speaker bar, media cabinet, three risers with aisle lights and the benches.
27. (C) [done] Restrooms: stalls, vanity and a hand-dryer model (`l31-dryer`, new) in place of the flat plate.

**3. Level design**
28. (A) [done: the rink's name, Arcade, Prizes, Snack Bar and the DJ sign] The neon signs as emissive tubes: the rink's name and the DJ sign drawn as raised tube strokes with glow over a
    dark backing, not a lit flat plate.
29. (B) [done: the fascia's lit strips] The DJ booth reads from across the rink (raised, lit fascia): today a dark strip on the far wall.
30. (B) [done] The rink floor carries the lit look: the lane sheen (item 8) under the ring lights' colours.
31. (B) [done] The cinema: a little more light on the benches (the aisle lights) so the room reads, still dark (lore).
32. (C) [skipped: arrivals are the links' (settled)] Arrival views in the halls still face a wall at times; check after run 1.

**4. Lore**
33. (A) [done] Keep: the star at the centre, the DJ on the south (a docile Faceling), the Coach behind the rental counter,
    three stepped rows of continuous metal benches and one big TV, the green-card dispenser, free food. Nothing new
    may contradict the lore.
34. (B) [done] The skates on the shelves (the "steal" way out) must read as skates: item 1.
35. (C) [done] The arcade's "few 1980s cabinets" (Q*bert, Donkey Kong, Space Invaders) stay as our look-alikes (pyramid,
    barrels, shooter) at the bar of item 9.

**5. Alignment with the other levels**
36. (A) [done] Reuse Level 120's CRAC unit (item 14) rather than a fork: the same make of machine in another building.
37. (B) [done: the EXIT, extinguisher and alarm mounts now use the shared models] EXIT signs, extinguishers, placards, supply boxes, the Almond Water fountain stay the mod's shared ones; note
    any below the bar under "Shared assets below the bar".
38. (B) [done] Queue posts in front of the rental and snack counters: Level 36's `l36-stanchion`, reused.
39. (C) [changed: the rink's own coin lockers, l31-locker] The lockers: Level 52's `l52-locker` stays (the school's and the rink's lockers are one family).
40. (C) [done: kept] The Basement's duct (`basement-duct`) stays for the HVAC ceiling run.

**Added during the round**
41. (B) [done] `l31-popcorn`: the rink's own kettle popcorn machine (case, kettle, heap, lit header) in place of Level
    Fun's cart, similar but the rink's.
42. (B) [done] `l31-locker`: coin lockers set in the rink's walls (doors in frames, louvres, numbers, keys on tags, one
    ajar) in place of Level 52's school lockers.
43. (C) [done] The DJ sign's tubes (gen_31_walls.py's cladding kinds `dj<c><r>`, patched by round 4).
44. (B) [done] `l31-counter`: the rental's and lobby's counter in the rink's style (navy front in the rink's stripes, a
    laminate top with a pink nose, bell, size tags) in place of Level 3999's reception desk.
45. (B) [done] Lore: Wikidot's "back arcade area with covered machines": half of the store rooms are now the back arcade,
    rows of uprights and pinballs under dust sheets (`l31-covered`), an aisle down the middle.
46. (B) [done] `l31-skatebench`: the rink's carpeted lacing-up bench (padded top, piping) in place of the shared slatted
    bench on the skirts and in Skate Rental (Level 31 only).
47. (C) [done] Skate trainers (`l31-walker`, the PVC walker frames learners push) parked inside the barrier at the gaps.

### How it is built (round 4)

- `tools/gen_31_round4.py` (run after `gen_31.py`, `gen_31_props.py`, `gen_31_round3.py`; `gen_31_walls.py` too, whose
  cladding blocktype it patches for the DJ sign) owns the rebuilt codes and the new ones; its textures are `r4-*` in
  `textures/block/31/`, all saved with alpha 0 or 255 only. Helpers: `octo` (an octagonal prism of four boxes, two
  of them turned 45 degrees, ends from one box only so they do not z-fight), `disc_tex` (round pictures on a clear
  background: wheels, records, cones, jog wheels, cup holders), `mirror_x`. `tools/preview_shapes.py` and
  `tools/check_zfight.py` checked every shape (no same-plane pairs over a pixel or two left).
- **The barrier** (`WorldGenerator.L31.Round4.cs`): a rink tile with the barrier (`L31Props.Dasher`) finds the sides
  off the boards and draws a straight piece (one side), a corner (two sides) or, on a board tile whose only
  off-board neighbour is diagonal, the post where two runs meet; the gaps' gate tiles draw the hinge post and leaf
  (left or right, by which neighbour is the barrier) or the sill. The layout is unchanged (the same tiles), only
  the blocks.
- **Placed by the layout (new prop ids in Level 31's range):** `L31Props.AirHandler` 738 (Level 120's CRAC, rel 1-3+
  lower, upper, duct; two per HVAC room in place of four AC boxes), `Slushie` 739 (one counter section in the food
  court and at the rink's snack window), `Stanchion` 740 (Level 36's queue posts in front of the rental counter).
  `l31-pinball`, `l31-popcorn` and `l31-counter` replace Level 3999's pinball, Level Fun's cart and Level 3999's
  reception desk through the same props (fallbacks kept); `l31-locker` replaces Level 52's lockers in the rink's walls
  (fallback kept).
- **Showcase / F7:** new spots `djbooth`, `gate`, `skates`, `pinball`, under the existing F7 entries (DJ station, The
  Rink, Skate Rental, Arcade).

### Shared assets below the bar (for the lead; not touched)

- `detail/acunit` (3 boxes: a grey cube with a fan ring painted on top): reads as a slab. Level 31 now uses Level 120's
  CRAC instead; any other level that uses it would gain from a cabinet with grilles, a fan guard and service panels.
- Level Fun's `fun-popcorncart` (the popcorn is one cube, no case): Level 31 has its own `l31-popcorn` now; the cart
  could take the same case, kettle and heap.
- Level 3999's `l3999-pinball` (13 boxes, no legs' levellers, a flat head): Level 31 has `l31-pinball` now.
- Level 52's `l52-locker` (a cube with the lockers painted on): Level 31 has its own coin lockers now; 52's lead note
  asks for lockers with vents, dials and the odd open door, which `l31-locker`'s build (doors in frames, an ajar one)
  could share.
- The shared `detail/snackcounter-register` till is fine; the `drinkfridge` is fine.

### Inventions (round 4)

The look of every rebuilt object is ours (the lore names a DJ station, skates, arcade machines and pinball, a food
counter, a TV and benches; not their make): the STARDUST pinball backglass (after the round-3 rink name), the
rental's tan and white skates with coloured wheels, the 1990s CD decks beside the turntables, the slushie machine's
two flavours, the coin lockers' 25-cent keys, the VCR blinking 12:00, the trophy case's skater figures. Nothing in
the lore is contradicted: the cinema is still one big TV over three stepped rows of continuous metal benches (the
cup holders are on the bench backs), the DJ still on the south, the star at the centre.

### Balance notes for the lead

- **Salvage:** the HVAC rooms' air handlers are now Level 120's CRAC blocks, whose blocktype drops a metal bracket
  (avg 0.5) and scrap wire (avg 0.3) per block broken; two units of three blocks per HVAC room. The shared AC boxes
  they replace dropped themselves. If Level 31 should give no salvage there, the lead can give Level 31 a look-only
  copy (or keep the AC boxes).
- No new food, water, beds or safe rooms: the slushie and popcorn machines and the till are look-only; the soda
  fountain (Almond Water) and the drinks fridges are unchanged. The rink's barrier is thinner than the old cube
  (the boards' edge tiles are now walkable inside it), with the same gaps.
