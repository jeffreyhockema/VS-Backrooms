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
