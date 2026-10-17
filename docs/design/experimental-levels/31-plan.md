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
