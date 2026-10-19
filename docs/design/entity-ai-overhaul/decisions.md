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
