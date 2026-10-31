# Level 120 "Broken Servos" - brief for the release-quality pass

Sources: Wikidot https://backrooms-wiki.wikidot.com/level-120 (the source; the page is marked "being rewritten"; about 700 words). Fandom https://backrooms.fandom.com/wiki/Level_120 is "Chokepoint", a 153 x 137 km Brutalist megastructure with the settlement New Banbury: **mention only, do not use or mix.** Everything marked (mine) is my suggestion, not lore.

## 1. Lore summary (Wikidot)

- **Class:** survival difficulty 2. "the chance of stumbling upon one or making one [a Misglitch] is relatively low, hence why Level 120 only has a survival difficulty of 2."
- **Look:** "broken server rooms with massive blocks of computers ripped apart on the dirty, white floor. The walls have dirty yellow wallpaper plastered onto rotting wood. The roof is primarily made up of regular office ceiling tiles, with smashed or inactive fluorescent lights within them." Server rooms "come in clusters of 15-23."
- **Light:** "These rooms are usually pitch-black, with the only light coming from the second, rarer type of room."
- **Second room type, White Voids:** "pure white voids", clusters of 6-12 rooms, "black doors that lead to other white-void rooms". They emit light; they "tend to attract Smilers, though they will often be too indulged in the light this room naturally emits to attack you."
- **Third type, Pitch-Black Hallways:** "thin and very long corridors that connect to different server rooms." Entities rarely live there, but "it's easy to trip, and if that happens, you have a large chance of injuring yourself and accidentally spawning Sub-Misglitches."
- **Mechanic:** reaching voids or black hallways "only requires finding an intact computer block. Booting this up will 'load in' either" one. To leave, travel in one direction to the cluster edge: "windows that will lead back to the computer block that brought you" (usually already broken).
- **Entities (three):** Smilers (in the voids). **Misglitches**: "glitched, zombie-like versions of those who die in the Backrooms ... anyone who dies here instantly becomes a Misglitch." Black humanoids "surrounded by pixels", red marks where the victim died (all black if the death was internal); they attack with a pointed tentacle-like arm that slices. **Sub-Misglitches** spawn "whenever someone's internal fluids or organs are exposed to the air of this Level ... a mere drop of blood to one's whole intestinal tract"; same attack, "far more hostile and efficient."
- **Groups:** none known. **Temperature, sound, items, resources:** not stated.
- **Entrances:** a smashed arcade-machine screen in Level 25 (any colour; you can break one yourself); a door labelled "Server Room" in Level 4.3. **Exits:** doors in server rooms or black hallways back to Level 4.3; noclip through server-room walls to Level 70. (25, 4.3 and 70 are not in this mod: write them as rumours, e.g. "a door marked Server Room in the offices".)

## 2. What exists now (branch experimental-levels, prototype 2026-10-17)

Id 26, `WorldLayout.Level120`, far north-east, cheats menu only. From `docs/design/experimental-levels/120-plan.md` (Status) and `src/Worldgen/WorldLayout.Level120.cs`: lattice period 96 (4-wide dirty-yellow service corridors, 90x90 halls, two 3-wide doors per hall edge, a walk round each hall). Hall kinds: rack hall 70, control room 10, cold vault 8, great hall 7, dead store 5 %. Racks in rows (cold aisle 3 wide, hot aisle 1, cross-aisles), 1 in 6 wrecked, about 20 % LED-lit (light 4-6), cable trays, ducts, raised-floor panels (one painted "hole" variant). Five blocks (`l120-wall/floor/rack/tray/terminal`), `serverhum.ogg` by zone, fog by zone, temperatures 38/33/27/23/22/15 C, calm stability. **Missing: entities, thresholds, loot, notes, handbook, white voids, black hallways, the boot mechanic, one-shot sounds.**

**Contradicts or drifts from the lore:**
- Floor: lore says "dirty, white floor"; ours is mid-grey perforated raised-floor tile. Re-tint toward dirty off-white (cheap).
- Light: lore says "usually pitch-black"; about 20 % lit racks plus a working tube at every other crossing is much brighter. Fine for playability, but the release should go darker and make light a resource.
- Layout: lore has clusters of 15-23 separate rooms; ours is open rack halls. Rack aisles are our extrapolation (the wiki says nothing about aisles).
- Temperatures and the fan hum are invented; harmless but not lore.
- Walls (yellow wallpaper on rotting wood, `l120-wall` base/stained/rot): matches.

## 3. Build list

**Must**
1. **Entities.** (a) *Misglitch*: new entity, black humanoid with a pixel-noise shimmer and red marks; melee with a long reach lunge (reuse the Wretch/Hound melee AI shape, reach about 2.5). (b) *Death rule*: a player who dies in Level 120 leaves a Misglitch by the body (hook the existing `CorpseSystem` death path; the body and map skull already exist). (c) *Sub-Misglitch*: spawned (cap 1-2 per player) when a player is bleeding or damaged below a threshold; chance low, to honour class 2. (d) Smilers in white voids use the existing `smiler` entity with a "dazzled by light" state (no attack while the room is lit).
2. **The boot mechanic.** An intact computer (a lit `l120-terminal` variant, rare) right-clicked takes the player to a White Void cluster or a Black Hallway; the cluster's end has broken windows that return to that terminal.
3. **Level exit and entrance text**: a "Server Room" door threshold back to the offices (Level 4) for the release test; handbook page and notes below.
4. **Wanderer notes and a loot table.**

**Should**
5. **White Void rooms** (clusters 6-12): pure white blocks (reuse the End's white tile), no features, emissive light about 14, black doors between rooms (joined grid of 12x12 rooms), a broken window pane at the cluster edge. Smilers spawn here.
6. **Black Hallways**: 2 wide, 3 high, 60+ long, light 0, black fog; a "trip" roll while sprinting (small chance per 10 m: stumble, 1 damage, bleed) which can spawn a Sub-Misglitch (mine; lore only says trips are easy). A black door at the end opens into a server cluster.
7. **Server-room clusters**: partition some rack halls into 15-23 rooms with doors (Level 4's BSP plan via `PlanCache`) so the lore's "clusters" read as room after room.
8. **Light as the scarce thing**: darker base, lit LEDs 5-10 %, a few working tubes marking safer corridors.
9. **One-shot sounds**: HDD clicks, relay clunk, fan spin-up; a static stinger near Misglitches; a clean high tone in white voids.
10. **Loot (mine)**: circuit boards, copper wire, dead hard drives (junk for wanderer traders), batteries, ethernet cable, plastic scrap; a rare intact boot disk if the portal needs a key.

**Nice**
11. True blinking LEDs; real floor holes (shallow pits); a corrupted wall screen showing a few frames of a corridor; a pixel-dither overlay in the voids.

**Wanderer notes (mine):** "Do not die here. I watched what the floor does with you." / "One screen still said BOOT. I pressed it. Everything went white and the doors are black." / "A papercut was enough. Tape your knuckles." / "Smilers hang in the white rooms and stare at the light. They do not turn. I held my breath and walked past." / "Walk one way. The window at the end is always already smashed." / "Someone smashed an arcade screen and fell in. The machine behind me is not there."

**Handbook outline:** What it is (broken servers, dark) - Reading the dark (lit racks, tubes) - Computer blocks (booting to Void or Hallway; walking out to the broken window) - What lives here (Misglitches, dying here, Sub-Misglitches and blood) - Class 2: short but unforgiving of the injured - Ways in and out.

## 4. Open questions

1. **Where do voids and hallways live?** Lore: separate clusters loaded by booting a computer. Recommendation: a pocket sub-region in the level's band generated from the terminal's hash; windows teleport back. If costly, ship them as wings behind doors in dead-store halls first.
2. **Misglitch on every death?** Wikidot: "instantly". Recommendation: every player death in 120; it despawns after a day or when killed.
3. **Ambient danger.** Recommendation: very few ambient entities; danger is the dark, trips and the death rule.
4. **Temperature**: lore silent; keep the prototype's, not advertised as lore.
5. **Fandom "Chokepoint"**: no content borrowed.

Confidence: lore coverage high (short page); mechanics-in-this-mod are my design.
