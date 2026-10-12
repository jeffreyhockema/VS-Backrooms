# Visual review, 2026-10-11

Every level was photographed in the real game client (376 shots: three random arrivals per level, four headings and
a look up each, plus caches, dens and refuges), then reviewed level by level against the lore (Wikidot first,
Miraheze and the Fandom API as second opinions) and each level's design doc. Clear improvements were made the same
night; the rest were done in round 2 later that day (see below). Every changed level was photographed again afterwards in a new
world. The review sheets (before above a magenta line, after below) are not part of the public repository; the
tables still name them.

## What changed

**One bug hit several levels:** a blocktype's `textures: { all: ... }` overrides *every* texture code of a JSON shape
(confirmed in the decompiled `ResolveTextureDict`), so 3D detail was being painted in the wall's texture. Fixed on
Level 2's tunnel walls (pipes, risers, valves), Level 3's wall fixtures (panels, fans, pipe runs), Level 5's hotel
fixtures (candle sconces, portraits) and Level 1's damaged concrete (rebar).

| Level | Changes | Sheet |
|---|---|---|
| 1 | rust rebar on damaged walls; the new car (below) | `level1.jpg` |
| 2 | wall pipework in colour; 3D gauge cabinets instead of painted dials; darker, quieter concrete; arrivals under a working light | `level2.jpg` |
| 3 | panels/fans/pipes in their own materials; rounder caged bulkheads; black "sludge" pipe bundles; arrivals in lit sections | `level3.jpg` |
| 4 | cable droops moved up into the ceiling gap, thinner, and 0.8% of tiles instead of 2.5% (layout v5); fabric cubicle partitions with an aluminium rail | `level4.jpg` |
| 5 | real 3D beams and coffers in the grand rooms; 64 px damask (no more "plus signs"); brass number plates on doors; mirror glass | `level5.jpg` |
| 6.1 | skylights read as skylights (dark panes, glowing frame); 3D snack machine | `level6-1-and-level8-camps.jpg` |
| 7 | darker fog: no more glowing horizon strip; entry room floor is soaked carpet | `level7.jpg` |
| 7, 8 (+ camps on 1/3/9) | burn barrel is a steel drum with fire inside, not a lava cube | |
| 8 | road lamp on a bracket; Almond Water seep as a wet stain with trickles and a pool (matches the rock stratum); glossy tar | `level8.jpg` |
| 9 | clouds no longer glow grey at midnight; puddles read as water; arrivals out in the open | `level9.jpg` |
| 10 | leaden overcast sky (fog over the whole dome, full cloud deck); grass strip between tyre tracks kept short | `level10.jpg` |
| 11 | mirror towers without the diamond quilt (plain panes + alternates); arrivals clear of trees and cars | `level11.jpg` |
| 1, 9, 11 | the car has wheel arches, round wheels, raked glass, door seams, mirrors (same footprint and codes) | |
| 37 | white 64 px mosaic with pale grout; chrome handrails and ladders; slits recessed into the wall; whiter slit light; arrivals never in the dark corners | `level37.jpg` |
| 94 | terraces without the clay band on every step; Motion's own grass tint (deep green) | `level94.jpg` |
| ! | bright EXIT sign in the start room; hall door reads as closed; fuller hospital bed (also Level 1's first-aid rooms) | `level-run.jpg` |
| Fun | grey steel gone from the lobbies (it was the elevator block's side); brushed brass elevator doors; soffits over the hall openings | `level-fun.jpg` |
| End | troffers read as lit | `the-end.jpg` |
| Hub | lamps show amber glass; ceiling no longer reads as planks | `the-hub.jpg` |
| 974 | brighter lights and paint, so the house reads pink, not maroon; deeper sky in the clouds painting | `level974.jpg` |
| 3999 | pillars are continuous vertical neon, not stacks of rings; brighter pillars and base strips; faint form ties with alternates; subtler glass streaks; plain gallery fascias | `level3999.jpg` |
| 188 | lighter, softer moss tufts; grey blind cords; bollards light the deck | `level188.jpg` |

**Layout version 5.** `WorldLayout.CurrentVersion` is now 5. Only two things are behind it: the arrival preferences
(Levels 2, 3, 9, 11, 37, 94) and Level 4's droop density. The `layouthash` lines for versions 1 and 4 are unchanged,
and the harness `links`, `deep` and `validatelevel` checks pass as before. Everything else is assets or block choice
at the same positions, so existing worlds pick it up in chunks not yet generated (old chunks keep the old look; Motion's
tint only applies to map regions not yet generated).

Committed as version 0.512.2019.

## Round 2: the decisions, done (2026-10-11, afternoon)

You asked for "your best suggestions based on lore and available capabilities" on the list that was here. Eight
agents did one group each; everything below was then regenerated together, built (0 errors, 0 warnings), checked with
the harness and photographed again in a new world (sheets in `round2/`). Layout changes are behind version 5 (still
unreleased). The `layouthash` lines for versions 1 and 4 are unchanged, and `links`, `deep` and `validatelevel` show no new failures.

| Level | What was done (the choice, and why) | Sheet |
|---|---|---|
| Fun | Every elevator lobby dressed for the party: string lights over the doors, confetti, balloons and streamers, a TIME 4 FUN =) poster, a new ship's directory board, a palm; one pair of doors per lobby says OUT OF ORDER =) (Wikidot: balloons, streamers, confetti from the first frame) | `round2/levels-run-fun.jpg` |
| ! | Start-room lamp of its own, red, brighter (bed and doors read; Red Rooms unchanged); crash rail, VISITING HOURS and hand-washing notices, a sanitiser dispenser. The hallway is now photographed | same |
| 3999 | Pillars every 10 blocks rather than 5; neon tubes across lobby and food-court ceilings; six arcade cabinets on each lobby's back wall; a black-and-gold marble storey line at rel 6-7 | `round2/levels188-3999.jpg` |
| 9 | About a third of houses are two-storey (hall, stairs, three bedrooms and a bath upstairs); 40-48% have porches; a coach lamp by every front door (lit in the houses with power); three window rhythms; 3D windows (frame, recessed glass, sills; also on Level 94 and The End); street-name signs at every junction and DOWNTOWN signs at 1 in 6 | `round2/level9.jpg` |
| 94 | The castle shows on the horizon: its walls and roofs glow a little, a client renderer draws it beyond the view distance where the real one would stand, and the fog is thinner. The mountain was not raised (only 8 blocks below the world ceiling); turf tops lost the thumbprint rings | `round2/levels37-94.jpg` |
| End | Partition walls (the store's painted wall with ghost marks and posters, openings every 8-12) along about one department border in three; EXIT doors in vestibules; neutral, slightly cool fog; first lights-out 3-4 game hours after arriving | `round2/end-hub.jpg` |
| Hub | Arrivals turn toward the road; sigils cut deeper with a darker recess | same |
| 37 | Arrivals in rotundas, pillar halls and natatoriums (a wall within 2 blocks: 57 → 7 per 100). The dark corners stay dark (no tile glow) | `round2/levels37-94.jpg` |
| 10 | Its own deep-green grass tint; the sun no longer shows (a fog sphere round the player); fog spells about one half-day in three, lasting 3-6 minutes. **No rain**: vanilla rain falls by weather region, so it would leak into neighbouring Level 9 and 11 cells and it wets players. A second thing per crop field: a tool shed, a trough with a pump, or a fallen gate | `round2/levels10-11.jpg` |
| 11 | Billboards on 35% of low brick roofs (four posters) and round advertising pillars at about 15% of inside corners | same |
| 8 | The 9th Road is an arch with caves biting into its roof; settlements are round domes; lamps hang their arm over the road; ore lies in veins and pockets (metal yield 96% of before; halite untouched); 3D blood-red and multicoloured glowcaps (Wikidot) | `round2/levels6-1-7-8.jpg` |
| 7 | Ceiling glow in patches; islands rise in steps; rock pillars into the ceiling and sea stacks; faceted basalt island rock; Fort Surrender (a ring of furniture stuck down with tar) at one camp in two | same |
| 6.1 | One store in four is a vending-machine room, piled and unenterable (Wikidot); the drinks fridge is 3D. The diner palette is kept | same |
| 2 | Round wall pipes with flanges, struts and clamps (thinner, higher); steel doors in white, grey, cream; the B.N.T.G. tramway with dead trams; jogs in about one main in eight (walkability unchanged); candles in rat warrens | `round2/level2.jpg` |
| 3 | Blue-grey round steel bars; the Purpified (rare purple carcass half in a wall); the Sanctum statue 3 blocks tall with a halo, and a ribbed vault | `round2/level3.jpg` |
| 4 | Hotel red ramps in toward Level 5 (solid within 5 blocks, frayed to 14) instead of islands; refuges are camps. No new windows (your earlier call) | `round2/levels4-5.jpg` |
| 5 | A front hall in one lobby cell in four: desk on axis with a 3D key rack, twin grand staircases up through the ceiling (they lead to Level 4, as the lore's "back up the stairs"), runners; a rare locked 666 door; blank plates on the Beverly Room's doors | same |
| 0, 1 | The damp wallpaper is close to the plain one's brightness; Level 1's abandoned cars are wrecks of the new car model | |
| 974, 188 | You wake on the rug before the bed; a third hall light; the `hills` painting deeper. 188's EXIT sign hangs over the courtyard door | `round2/level974.jpg` |

**After the round-2 re-shoot** (no new screenshots taken, at your request; not yet seen in a client):
- **Pipe and rail corners** (your report): Level 2/3 wall pipes now wrap outer corners with a mitred elbow, meet
  cleanly in inner corners, and end in a blind flange at an unpiped wall or door (`wallpipecorner-*`, chosen from the
  neighbouring walls by `WallPipeCorner`; to cap at doorways instead of wrapping is a one-line rule there). Audit of
  everything else that runs along walls and ceilings: Level 2 overhead bundles get junction boxes and end caps; Level 3
  trays, tar pipes, wall cables, risers and gauge pipes end or join cleanly; Level 1 bundles, drip pipes and conduit
  are capped; Level !'s crash rail turns its corners; 3999's neon base strip has corner pieces; 188's downpipe has a
  hopper head; Level 9 porch railings close their gaps. Left as they are: tram rails (rail mains never jog), the
  baseboards and trims painted into wall textures, Level 37 handrail ends. Nearest targets: `pipecorner`, `pipewrap`,
  `pipeend`, `neoncorner`, `downpipe`.
- **Light no longer follows the clock indoors.** Level 188 went black at night: the mod held fog and scene brightness
  but not the ambient light colour, so unlit areas darkened with vanilla's night. Every level except 10, 11 and 94 now
  holds the day's ambient (`AtmosphereSystem.DayAmbient`); Level 9 also keeps its tuned look at midnight. Check: the
  inside of Level 94's castle now keeps the noon ambient at night.

New `/backrooms nearest` targets for checking these (also F7 buttons): `runhall`, `funparty`, `endwall`, `endexit`,
`foodcourt`, `courtdoor`, `l9house`, `l9stairs`, `streetname`, `citysign`, `fieldthing`, `billboard`, `adpillar`,
`castle`, `seapillar`, `shelter`, `vendingroom`, `glowcaps`, `tram`, `purpified`, `fronthall`, `door666`, `hotelturn`;
plus `/backrooms light [lantern|torch|candle]` (a lit light in hand) and `/backrooms fogspell`.

## Still for you

- **Level 6 with a lantern:** even with the large lantern (light 20) you see about 2 blocks (`round2/level6-lantern.jpg`).
  That is Wikidot's "light sources dim significantly", but it is very dark; the fog in `AtmosphereSystem` thins only
  down to density 0.06 at full light. Your call whether a lantern should reach further.
- **Level 4's hotel ramp** was not caught on camera (the `hotelturn` target landed short of it); the harness confirms
  the layout.
- Yellow specks drift in Level 10's air (vanilla particles, as on Level 9); harmless, but visible in the grey sky.
