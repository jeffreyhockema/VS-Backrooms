# The Basement (unnumbered): lore and gap brief

The two wikis describe two quite different things under this name. Sources read in full:
- Wikidot: https://backrooms-wiki.wikidot.com/the-basement ("Unnumbered Level: The Basement", Dr Bierre; "Original fandom level written by anonymous fandom user"). A story told as Backforums threads. No survival class stated. (Earlier plan said Fandom returned 402; the API works now with a Mozilla user agent.)
- Fandom: https://backrooms.fandom.com/wiki/The_Basement (wikitext via API; classes 2/2/2: "Somewhat Difficult to Exit", "Lack of Needed Resources", "Decent Amount of Entities"; rewrite by Lunon, "direct antithesis of The Attic"). A location, an Area of Interest, not a numbered level.
Confidence: high on both texts; the reconciliation is my judgment.

## 1. Lore

### Wikidot (narrative)
- Entry: "I managed to break through the floor on Level 0 ... dug up the carpet with an old crowbar and smashed the paneling below it." "It's a small little basement ... pitch black when I got here first, but the lights turned on and scared the hell out of me ... Only way forward is a staircase of sorts."
- The stairs lead into water: "It's flooded. Smells terrible down there." He waded "like 2 hours"; to a "dry patch a little above the rest" with no way out ("I jumped down. Didn't bring any rope").
- Deeper: "the water rose to my neck ... I was barely even touching the ground"; he finds "a staircase under the water"; "Walls are really tight down here. Still a basement, but everything is cramped as hell. I'm fucking freezing and my clothes are completely soaked." Laptop ditched; camera drenched; phone battery low.
- Entities: "something standing in the fucking distance"; "some... corpse? ... pics of drowned people after they've been in a lake for like, a week. It chased me for a while." A wailing "in the distance" twice.
- End: "THERE'S A FUCKING ELEVATOR IN THE DISTANCE." Then his account is deleted. A clipping follows: a flooded bar basement in Cincinnati, six workers died, "the sixth victim, Gary Moors, has yet to resurface"; "patches of it still suffer from large pools of water." (Implied: the corpse is Gary Moors. The clipping's dates are muddled: "January 6th", "January 1951".) Thread #45 is missing. Final post: the poster is banned.
- Sounds/smell/temperature: foul smell, freezing, wailing; no other sounds given.

### Fandom (encyclopedia)
- "A strange location ... thought to lay beneath most of its levels", "the Backrooms' 'bottom point'". Resembles a house basement, "much larger than any known man-made basement": "a seemingly infinite amount of rooms ... mainly composed of wooden or concrete walls, concrete floors blanketed by dusty carpets, and wooden doors which lead to more spaces with similar architecture."
- Non-Euclidean: layout changes unseen; "exiting a room may lead right back into the same one". Rooms hold "brick stairwells ... escherian": going up or down leads back to the same floor.
- Light: "barely any light sources save for the occasional light bulb and window. Despite this, every part ... is illuminated by a light which has no determined source." Sounds: "babies crying, footsteps" behind doors that vanish when the door is opened.
- Water: partly or fully submerged areas, "a substance ... similar to Almond Water" but "not safe to drink ... contaminated by various germs that come from the level's carpet"; drinking dehydrates more.
- Resources: none (food, drink). Out-of-place objects: "ropes, random wires serving no purpose, caution signs". A "large amount of human corpses" whose smell "can suffocate one if it is inhaled for long enough".
- Entities: "devoid of all entities except for the occasional Windows" (maybe anomalous, with "Window Shadows"); smart entities (Facelings, Skin-Stealers, Smilers) enter the same way as humans and land in a random existing instance. Each person gets their own instance (sound travels between them), so no outposts.
- Entrance: breaking through "the floor of most levels"; the drop is "often several tens of feet". Exit: climb back up the crack, "near impossible"; bring a ladder.
- A "Recovered Document": a lonely, nostalgic note (grandpa's basement, emptiness, "3 bottles worth of water ... a couple of vegetables"; "do not ... jump into random holes").

### Where they agree
Entered by breaking the floor from above and a drop with no easy way back; a basement-house look, concrete; foul flooded sections; corpses and their smell; scarce or no supplies; dark with some bulbs and a mystery of light; few entities; cold, damp; being stuck. Differences: Wikidot is one linear flooded route ending at an elevator and a drowned corpse; Fandom is an endless dry-ish carpeted maze with loops, Escherian stairs, rare Windows. Neither names sub-zones.

### My reconciliation (a choice, not lore)
Keep both: the Fandom basement as the normal level (dry rooms, dusty carpet, wooden doors, brick Escherian stairs, noises behind doors, ghost-light, corpses, rope/wire/caution props), with Wikidot's flood as the lower part and its long, tight flooded corridors, dry patch, drowned corpse, wail and elevator as one set piece. This is what the prototype is already shaped like.

Survival difficulty: Fandom's 2/2/2 suggests class 2 (poor on resources). Wikidot's story is lethal for an unprepared person. I recommend class 3 (my judgment): easy to hold if supplied, hard to leave, and the flood is deadly.

## 2. Prototype now (basement-plan.md Status and Harness)
Round region; Cellar (57%) of BSP concrete rooms with 2-wide open gaps, no doors, crates, boilers, drums, shelves, cabinets, pillars; Flood (33%) as a lattice-tree maze of 3-wide passages in real water two blocks deep with slime walls and pipes; Dry Patch (9%) 16x16 rooms with pump, boiler, bulb; two-step stairs between cellar and flood; flicker bulbs; fog 0.045/0.07; temps 8/5/9 C; wail every 3-8 min in the Flood; arrivals on dry Cellar floor. Six block families. No entities, loot, notes, handbook, doors, elevator, drop/crack, Spanish strings.

## 3. Gap list

**Must**
1. **Carpet and doors.** Fandom's signature is "dusty carpets" over concrete and wooden doors; the Cellar has bare concrete and open gaps. Add a carpeted-floor variant (reuse Level 0 dusty carpet) in about half the Cellar rooms and real wooden doors in the BSP gaps (some jammed or locked).
2. **Entities.** Existing: `corpse` (use for the drowned corpse; chase it through the Flood, slow in air, fast in water) and skinstealer / faceling / smiler as rare visitors (Fandom: they enter by falling through). Windows are not in the mod outside Level 188 (rare lit window panes on far walls with Window behaviour is the best fit; optional). Keep the roster sparse: "decent amount" only in Fandom, Wikidot says one corpse.
3. **Drop from above and the stuck feeling.** Arrive at the bottom of a shaft: a cracked ceiling hole tens of feet above, with a hanging scrap of carpet and a chunk of floor (a lore-faithful "rope needed" moment); a rope or ladder in the level is the way up (but no real threshold). A note: "bring a ladder".
4. **Corpse smell hazard.** Corpse piles (Fandom) cause a suffocation/stability drain when inhaled for long; place bone/corpse props (reuse corpse props) in the corners and in the Flood's dead ends; a Gary Moors name tag on a bar worker's apron (my idea from the Wikidot clipping).
5. **Water rule.** Flood water must not be potable: drinking it adds thirst and a disease-like debuff (Fandom: dehydrates more; Wikidot: disease fear). Check the mod's thirst needs.
6. **Lights.** The Fandom "light without a source" suggests faint ambient everywhere; Wikidot suggests the lights switching on abruptly. Suggest the first-seconds darkness then lights-on event on arrival (my idea) plus a general low ambient floor in the Cellar.

**Should**
7. **Escherian stairs.** Brick stairwells that loop back (a stair whose top teleports to the same room one cell over, pure function of coordinates): the prototype's stairs are honest ones, and should not be, in the dry part. Keep the flood stairs as real.
8. **Out-of-place props:** ropes, loose wires, caution signs (reuse hazard signs from Level 2), a coil of rope, a forgotten ladder.
9. **Sounds behind doors:** baby cries and footsteps from closed doors that vanish when opened (existing footsteps/squeak; a baby sound would be new); the Flood's wail.
10. **The elevator:** the Wikidot ending. A dead or working elevator in the Dry Patch zone; the prototype plan chooses a dead prop; keep dead (no threshold) with a plaque.
11. **Loot:** nothing beyond the "no resources" lore: empty crates, a few empty water bottles, a half-rotten vegetable, a dead flashlight, an old crowbar (from the narrator), rope. Supply boxes mostly torn.
12. **Wanderer notes (suggestions):** "Do not jump down without a rope."; "The water tastes like almond and tastes wrong."; "I counted the doors. The count changes."; "Something is standing at the end of the corridor. It has been standing there a while."; "Elevator. I saw it. I never reached it."; "Babies crying behind the doors. I stopped opening them."
13. **Handbook outline:** The Basement (class 3, my pick); how you get there (breaking the floor; no threshold built); the carpeted maze; the Flood and the dry patch; the corpse; the Windows; resources; leaving (the crack, a ladder).

**Nice**
14. A bar cellar room (kegs, barrels, ledger, Cincinnati sign) as a nod to the clipping.
15. The Recovered Document as a long note ("my grandpa's basement").
16. Slow pump/drain sounds; rising water in the Flood (Wikidot: "the water was rising") as a slow tide.

**Contradictions in the prototype:** open doorless gaps (lore: wooden doors); Flood at "waist to neck deep" is full swimming depth; Cellar is bare concrete not carpet; "Dry Patch" is bright and equipped (lore: just a raised patch with no way out, "there isn't a good spot to rest"); pump and boiler give it a habitat feel, so consider fewer comforts. The Wikidot account's "walls really tight" matches the Flood.

## 4. Open questions
1. **Which wiki wins?** The pages describe different things. Recommend the combination above; record the choice in the handbook as "two accounts of the same place".
2. **Elevator:** exit or just a tease? Wikidot ends on deletion; recommend prop only.
3. **Survival class:** none on Wikidot, 2/2/2 on Fandom. Recommend 3; a decision for the user.
4. **Escherian loops:** cheap to fake with a stair that returns the player; may annoy. Recommend only in a few dry rooms, with a note.
5. **Windows:** unclear whether true Windows. Recommend omit or very rare.
