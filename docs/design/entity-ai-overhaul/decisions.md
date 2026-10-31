# Entity AI overhaul: decisions

The user's calls, with the date, so no batch reopens them. Open questions and the planner's recommendation are at the
end; a worker that reaches one stops and asks.

## Taken (2026-10-18)

| # | Question | Decision | Why |
|---|---|---|---|
| 1 | Giant Spider, Neighborhood Watch, Beast of Level 5: build in this release? | **Already in the works** on branches `l8-spider`, `l9-watch`, `l5-beast` (another session, as part of the graphics overhaul: the base entity and model). This release **refines** them (P4), it does not build them | The user: "i mostly just wanted the base entity and model to be implemented in the graphics overhaul then this will refine them" |
| 2 | Skin-Stealer and Duller: killable or evade-only? | **Both stay killable, much harder.** Skin-Stealer: a stun window, higher health, hunts only when hungry; Duller: in reach only at the wall, flees otherwise. Hides keep their place in leather | ChatGPT proposed evade-only; the lore lists no weakness but never says they cannot be killed; the leather progression counts on the large hide |
| 3 | Smilers and light: the mod's wall, the lore's attraction, or both? | **Hybrid.** A carried light is seen from farther and draws them to its edge, where they stop; eye contact freezes them; running or noise brings them to the edge faster. Light stays a wall | Wikidot: "attracted to light"; the mod's thesis: light keeps the eyes away. Both hold |
| 4 | Entity drops: vanilla only, a few materials, or a full material economy? | **A few new materials with real uses.** Vanilla drops first, plus Deathmoth quills (venom coating), spider silk (twine), Clump sinew (bow and sling string, rope), optional moth jelly (bait). Each with a recipe on day one | ChatGPT's chitin, glands and tissue have nothing to feed in the game; quills, spiders as food and rats as food are the lore |

| 5 | Level 6: a rare Smiler glimpse, nothing at all, or as today? | **Eyes only.** Rare Smiler glimpses that never approach or hunt; Dullers removed; the Mimicry sounds stay | Wikidot: "no entities have been found", but the page keeps an archived note of an unidentified attacker; eyes never confirmed are what "found" means |
| 6 | The floating Watcher (own model, the beam, evade-only) in P4? | **Yes, committed.** A required part of P4 with its own model, sounds and beam, not a stretch goal | The user wants the lore's Watcher in this release; the branch's six-legged eye is a Strider and is kept as one |
| 7 | Moth jelly as a bait item? | **Yes.** A fourth material, found in Level 5's hive hearts, not crafted | Cheap, and a second tool for drawing rats and moths off |
| 8 | Hive hearts and web blocks: worldgen behind a layout version, or runtime on first entry to a den? | **Runtime**, like Level 188's arm | Saves and the layout hash untouched; existing worlds get them too. The spider branch may already place webs by worldgen behind layout version 9: P4 reconciles, and leaves those as they are |

## Open (recommendations in bold)

| # | Question | Recommendation | Who decides |
|---|---|---|---|
| 9 | Version number | **0.515.0** | the user, at P8 |

## Taken (2026-10-20, P7 round 2: isolation; see isolation.md)

| # | Question | Decision | Why |
|---|---|---|---|
| 10 | Level 0's roster | **The Bacteria only.** Hounds removed from the Lobby; Smilers only in Red Rooms and during a Reality Shift's dark | Wikidot: "unknown whether or not entities exist"; only "dark figures" claimed |
| 11 | How rare is rare | **About one body per 20 to 30 real minutes in the heart of a Class 1 level**; more at the edge; deeper levels scale up | the user's "seeing any living creature is an event" |
| 12 | Hound counters | **Stay out of sight; the stare-down buys a head start; walk away calmly (running or a turned back sets it off); a shut door stops it.** No climbing counter. **Light no longer slows Hounds** | Entity 8: sight and hearing only, no smell; "stay out of sight"; the stare "won't work for long"; "Don't run away… the second you see one"; Level 3's Hounds pounce |
| 13 | The Level 4 sighting (2 Dullers and a Hound pack) | The same over-spawning, not a bug in The End | the user confirmed it was Level 4 at the end of the session |
| 14 | Facelings | **One at a time within about 100 blocks, about 15 real minutes apart**; Level 11 keeps small groups; the Snackrooms their staff | Level 11: "Facelings and Hounds, the most numerous"; elsewhere the emptiness |
| 15 | Wanderers (traders) | **Untouched** | already sparse; the only trade |
| 16 | The backroomsMenace setting | **Every setting thinned alike** (the Spawns multipliers stay) | the user's call |
| 17 | More than one kind of menace at once | **One kind at a time** (a pack is one); set-pieces, dens and events are the exceptions | the user's call |
| 18 | Distant sounds | **Cut hard**: about one per 5 to 10 real minutes in a Class 1 heart | the user: "cut sounds hard too" |

## Taken (2026-10-23, P7 round 5: dial-in; see dialin.md)

The user's play-test after rounds 1 to 4: "the other extreme" from 0.514 (too rare to see anything), Level 1 the most
dangerous level (the Flickering), nothing seen in Level 94. Eighteen answers, all taken the same evening.

| # | Question | Decision | Why |
|---|---|---|---|
| 19 | The normal setting's rate | **A creature every 10 to 12 real minutes in Level 1's heart**, a sound every 4, the edge one creature every 4 to 5 minutes | the geometric middle of 0.514 (2 to 3 min) and 0.515 (34 min) |
| 20 | The settings | **Six**: off, **very low = today's numbers**, low, normal, high, very high (about 2x, 3x, 5x, 8x today). High and very high also change the glimpse/stalk/hunt mix and the caps; the others only the rate. Existing "normal" worlds get the new normal | the user's first thought was "today = very low"; the code string is what a world stores, so a new value is save-safe |
| 21 | What hurt in Level 1 | The Flickering's Hounds; otherwise "just tense" | the user's play-test |
| 22 | The Flickering | **Respects the hard gap and the one-kind rule again** (round 4 took the gate off); cooldown stays 20 in-game hours; the Hounds still always come | the lore's Level 1 hunt, but not on top of another encounter |
| 23 | The Screaming | **Level 2 only** | Level 1 keeps one set-piece; the rats' event belongs to Pipe Dreams |
| 24 | Level 1's dens | **Drop Hound packs**; Warren, Hive and Lair stay | Hounds in Level 1 come only from the dark sections and the Flickering. Dens are runtime: no layout version |
| 25 | Solitude spread | **Level 1 1.3, Level 3 0.45, Level 8 0.5, Level 9 0.3, Level Fun 0.4, Level 94 nights 0.6**; the rest unchanged | Classes 4 and 5 about 2 to 3 times busier than Class 1, not 1.5 |
| 26 | Level 10's barn-edge Hounds and Clumps | **Removed: Level 10 is empty** | Wikidot: "No Hostile Entities"; the worms are its hazard |
| 27 | Level 94's danger | **0.4** (was 0) | Class 3; Animations about Level 4's strength; the King's trial unchanged |
| 28 | Level 94 before tuning | **A headless night test in the hills** (open-ground sightline hypothesis) | the user's visit was 5 min, partly still or indoors |
| 29 | One kind at a time | **Strict in Class 0 to 2 levels; two kinds may be about in Classes 3 to 5** | the deep levels should be genuinely busy |
| 30 | The hard gap | **25 % of the mean** (was 40) | lucky clusters may happen; the mean stays |
| 31 | Ambient Facelings | **About one per 8 real minutes in Levels 1, 4 and 5**; 15 elsewhere; Level 11 keeps its groups | harmless set dressing where people live |
| 32 | The bands | **Approach from 50 % of the ring's width, threshold from 80 %** (were 60 / 85) | more of each level in the livelier bands; the band only changes rates and rosters |
| 33 | Acceptance test | **A felt-rate harness mode**: actual spawns and refused spots per level and band over a simulated hour, run before the zip; plus a log counter for silent spawn failures | the rate check counts rolls, not spawns |
| 34 | Creative mode | **A cheat-menu toggle** so creative also receives stalkers and hunters (off by default) | the user tours levels in creative |

## Taken (2026-10-25, play-test: Hounds in narrow places)

| # | Question | Decision | Why |
|---|---|---|---|
| 35 | Hounds in narrow places | **Hounds fit 1-wide gaps everywhere (collision box 0.9 wide, was 1.1; the box the player hits stays 1.1) and squeeze through anything under 2 wide at ~60 % speed** (AiTaskMenace.Squeeze: free width across the heading at body height, measured every 0.2 s; `/backrooms squeeze` reports it) | the user's call: Hounds could not pass 1-wide service tunnels in Level 2 (about 60 % of them) or the aisles clutter narrows, but obstacles should still slow them. Pathgrid, Hound, before/after: Level 2 maze 57-61 % to 70-74 % found, Level 4 cubicles 87-91 % to 100 %, Level 5 hotel 12-13 % to 20-24 % |
| 36 | Hounds and 1-wide gaps, again | **Hound collision box 0.58 wide (was 0.9); what the player hits stays 1.1** | 2026-10-27, the user's call after the Partygoer fix: the game's A* sets the box down at a random 0.3 to 0.7 across each cell, so a box over 0.6 wide fits a 1-wide gap only about half the time (the 0.9 box was still balked at Level 2's service tunnels on half its searches). Shipped as 0.610.1 with the Partygoer width |
