# Level 183 "Clean Sewers": prototype plan

Internal id **27**, `WorldLayout.Level183`, infix `L183`, blocks `l183-`, tag `183`, region far north-west beyond The End
(`spawn + (-F, -F)`). Reserved (BACKLOG batch 2): WallPattern 243, FloorKind 252, CeilingKind 120-127, Props 820-859,
Unders 180-189, Overheads 170-179, Pipes 150-159, salts 0x2700-0x27BF, threshold salt 0x27C0, title keys 2701-2799,
port 42488. Disconnected: cheats menu / `/backrooms goto 183` only. No entities, thresholds, loot or handbook.

## 1. What the lore says

**Neither wiki has a "Clean Sewers" Level 183.** Conflict, found by direct checks:
- Wikidot https://backrooms-wiki.wikidot.com/level-183 : "THIS PAGE DOES NOT EXIST YET" (182 "Aromatherapy" and
  184 "Field of Forgotten Forts" exist there). https://backrooms.wikidot.com/level-183 : page does not exist. Guessed
  slugs (level-183-1, clean-sewers, level-183-clean-sewers) are empty too.
- Fandom https://backrooms.fandom.com/wiki/Level_183 (API wikitext) is a different level: "Juvenile Imagination" /
  "Paper Houses", a colourless field of white paper houses under a dusk sky. Not sewers.
- Fandom title/text searches for "Clean Sewers" and "sewer", and a web search, found nothing on point. Nearest
  pages (Level 2, Level 49 roads) are unrelated. So **there is no canon text to cite**; the user's list name is the only
  source. Survival class, entities, items and sub-zones are unknown.

What we take from the name alone (invention, not lore):
- "Clean": the tunnels carry fresh, clear water; no waste, no stench. The counter-image of Level 2 and the Basement.
- Arched brick-and-concrete sewers: a central channel, walkways either side, side tunnels, junction chambers.
- Quiet running water, drips, echo, sparse steady lights. Feels safe, but endless and repetitive: that is the unease.
- Survival class: leave unset for a later proper pass.

## 2. The level in this mod

Round noclip region, radius `max(40, spawnMacroX / 50)` cells (about 320 full-size), cell = 32 blocks. A pure function
of world coordinates, `Hashing`, `Noise2` and `PlanCache` with the L183 salts; no stored state.

**Layout (per cell, 8-block node grid, 4 x 4 nodes a cell, as the Basement's Flood and Level 2):**
- Hash-ordered union-find spanning tree over the node grid (`PlanLatticeTree`) plus about 25% extra links for loops, and
  2 openings per cell border at hash-chosen offsets so cells join. Each link is a tunnel segment; corners and tees fall
  out of the links.
- **Main** links (about 25%): whole node rows/columns picked as "trunks" by hash (every 2-3 nodes), so mains run straight
  for many cells. **Side** links: the rest.
- Zones (`Tile.Zone`, Fbm of cell/5, salt 0x2700): 2701 Trunk Tunnels (default, mains common), 2702 The Channels (mains
  rare, many narrow sides), 2703 Junction Halls (extra chambers).
- **Main**: 9 wide: 3-wide channel in the middle, 3-wide walkway each side, with a 1-block curb. Arched ceiling.
- **Side**: 5 wide: 1-wide channel plus a 2 and a 1 wide walkway. About 1 side link in 6 is a **dry gallery**: 3 wide, no
  water, pipes overhead (a rest spot).
- **Junction chamber**: where 3 or more links meet, the node becomes an 11 x 11 chamber with an inner water basin; zone
  2703 gives a 16 x 16 Hall with 4 pillars and a sump.
- Decoration only: ladders (`level3/rungs`) up to a sealed manhole lid at about 1 junction in 8, `ironbars`/grate across
  some side-tunnel mouths (walkable gap kept), `level2/pipes` along ceilings, `detail/ventgrate`, `detail/drippipe`.

**Water:** channel bed at rel -2, vanilla `game:water-still-7` in the fluid layer at rel -1 only (one deep, clear, bed
visible). Walkways at rel 0 never hold water. The Basement's handling of water in the fluid layer is the template (it
went two deep; here one). No real current; flow arrows are painted on the bed.

**Heights:** walkway rel 0. Main ceiling stepped: rel 3 at the walls, 4 over the channel edges, 5 in the centre line (5 high).
Side: flat rel 3. Junction chambers domed to rel 6. Fits the 40-block band; no per-level band depth needed.

**Light:** clean cool white, no dead lamps (a maintained place). `l183-lamp` wall lamps every 6 blocks on mains (V8), every
12 on sides (V7), a ring of 4 in chambers (V9); about 8% flicker (the `BackroomsFlicker` look swap).

**Air:** fog `#c9d6d6` (pale blue-grey), density 0.025 Mains, 0.04 Sides, 0.03 Chambers (long straight mains need low
density to not feel closed in). Temperature 12 C (11 C Sides). Stability neutral 1.0, +0.1 in Halls. Arrival: first
walkway tile in a Main, spiralling out from the region centre.

**Sound:** new loop `ambient/l183/sewer.ogg` made in `tools/` (a `gen_level_sounds.py`-style script: `tile_room` reverb,
filtered noise for running water, a low tone); reuse `ambient/poolroom` under channels, `pooldrip` and `poollap` one-shots,
and a rare far clank (every 3-8 minutes, `pooldrip` pitched down).

**Wire:** `WallPattern` 243 (`Tile.Detail`: 0 brick, 1 stained, 2 lamp bracket, 3 ladder, 4 grate mouth); `FloorKind` 252
(`Tile.Variant`: 0 walkway, 1 curb, 2 channel bed, 3 chamber floor, 4 sump, 5 dry gallery); `CeilingKind` 120-123 (flat,
arch low, arch high, dome); `Props` 820-829 (ladder, manhole, grate, lamp, pillar, sump); `Pipes` 150-151 (run, leak).
Unders and Overheads unused.

## 3. Assets

**Reuse:** Level 2 `tunnelwall`, `tunnelceiling`, `tunnellight` (reference for shapes), `pipes` (run, leak), `oildrum`;
Level 3 `ironbars`, `manhole`, `rungs`, `cables`; Level 1 `concretewall`, `concreteceiling`, `concretepillar`,
`concretestairs` (curb steps); `detail/` `ventgrate`, `drippipe`, `poolladder`, `pooltile` (curb accent), `waterpump`;
vanilla `game:water-still-7`.

**New blocks (5, `l183-`):**
- `l183-wall` (plain / stained / tide): glazed off-white and pale grey-green brick, damp, a clean waterline one block up.
- `l183-floor` (walkway / curb / bed): pale scored concrete with a yellow-green edge band; bed = clean grey-blue cement.
- `l183-ceiling` (flat / arch / dome): dark grey-green brick rings with a lighter keystone line.
- `l183-grate`: flat black iron grate, floor or wall, see-through (reuses the `ironbars` shape).
- `l183-lamp` (on / flicker): caged white tube on a wall bracket, steady cool glow.

Textures with `tools/texlib.py` / `matlib`; draw brick courses and mortar explicitly (textures here are noise fills).

## 4. Lang strings (`assets/backrooms/lang/en.json`; the Spanish files fall back)

```
"level-27": "Level 183: Clean Sewers",
"levelhint-27": "The water is clear. Follow the current.",
"levelname-27": "Level 183",
"level-2701": "The Trunk Tunnels",
"level-2702": "The Channels",
"level-2703": "The Junction Halls",
"levelname-2701": "Level 183, the Trunk Tunnels",
"levelname-2702": "Level 183, the Channels",
"levelname-2703": "Level 183, the Junction Halls"
```

Plus `block-l183-*` names, as the Basement did. Hints for 2701-2703 only if the Basement-style titles need them.

## 5. Open questions

1. Lore: no such page on either wiki. Recommendation: build on the name only, say so in the commit and any later
   handbook text, leave survival class unset.
2. Water depth: 1 (wade) or 2 (neck, as the Basement)? Recommendation: 1; "clean" means safe, and 320 cells of
   slow wading would be tiresome.
3. Flowing water? Recommendation: no; still water plus the sound, flow arrows painted on the bed.
4. Fog tint: pale cool blue-grey or something warmer? Recommendation: pale cool, so "clean" reads against the
   Basement and Level 2.
5. Mains 9 wide and 5 high, or tighter? Recommendation: 9 x 5; narrow walkways to 2 if it feels too open.
6. Stepped brick arch or flat ceiling plus pillars? Recommendation: stepped 3-4-5 over the channel; no new model needed.
7. Rename if canon appears later? Recommendation: keep `l183-` and id 27 regardless; the display name is only lang strings.
