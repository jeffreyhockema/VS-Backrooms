# Entities: design and implementation plan

The Backrooms are meant to be survived, not fought. Entities exist to make the player listen, hesitate and plan: something heard down a corridor, eyes at the far end of a dark hall, a figure that was standing still a moment ago. They turn dangerous only where the lore says the Backrooms are dangerous: in the dark, when your grip on reality is weak, and at the edges, where one level gives way to the next.

Everything this plan proposes was checked against the lore (the Wikidot wiki, which the levels were built from, with the Miraheze wiki as a second opinion) and against what Vintage Story 1.22's entity and AI systems can express.

## Status (2026-10-05)

Phases 1 to 4 and the documentation are implemented (`src/Entities/`, `tools/gen_entities.py`, `tools/gen_entity_sounds.py`, the handbook page *What Lives Here*, the README). The decisions in section 8 were taken as recommended. Where the build differs from the plan:

- **The wildlife spawner stays separate.** `src/Deep/CreatureSystem.cs` still puts down fish, Level 8's drifters (the Wretches, unchanged), the Suburbs' animals (no longer wolves) and Level 10's livestock. The director handles only the Backrooms' own entities.
- **Thresholds:** pits and noclip walls count within 24 blocks, as planned, but elevators and stairs only within 10: Levels 3 to 5 have so many of them that 24 blocks put half of Level 4 in the threshold band.
- **Distant sounds** are heard by anyone near the spot, not only the player they were meant for. Level 6's Mimicry stays in `AtmosphereSystem` (client side).
- **Smoke** that scatters Deathmoths is any ward (a lit firepit, burning Firesalt).
- **Dullers** are kept off by Almond Water only, not by high stability: a player's stability sits at full all through Level 4, where Dullers live.
- **Firesalt** burns for 12 in-game hours, not one: an hour is two real minutes.
- **Built since:** the optional entities (Clumps, The Thing, The Mangled), Level 1's Flickering as a Hound event, glimpses that cross the way ahead, and wanderers keeping hostiles off (anyone within 12 blocks of one is in the safe band).
- **The Mangled** comes with Reality Shifts in Level 9's threshold band, not with fog (Level 9 has no fog events).
- **Wanderers after play-testing:** far fewer (one candidate cell per 8×8-cell district, and only some districts: about 0.4% of Level 1 cells, one every kilometre or two), and friendly (the vanilla trader's attack and chase are removed; struck, they back away). Wanderers saved from the denser placement are removed when loaded.
- **Behaviour pass** (2026-10-06, evening, after the models; follow-ups in `docs/entity-models-todo.md`): Facelings rarer (`RosterEntry.Rarity`, at most 2 at once, 3 in the city), Faceling children (`faceling-child`, curious, `AiTaskCurious`), head-only tracking on the client, greeting by right-click (wave, then point to the nearest gate), kin defence (`EntityBehaviorFaceling`); Hound stare-down (`staredDown`) and starved/old looks; Death Rats' glowing horns (`EntityDeathRat`), hairless look in Level 2, the Screaming (Levels 1 and 2); Deathmoths settle, males feed, females threaten and alarm (`AiTaskMoth`); Clumps buried with one arm out, hunting by sound, crawling (`AiTaskClump`); Duller plaster dust, theft, wall sounds, Almond Water sources; the Mangled as an event (`MangledEvent`: fog, cold, voices, lift, unkillable, ground shake), no longer put down by the director.
- **Models** (2026-10-06, after the first multiplayer play-test): every entity but the Facelings has its own animated model built from the lore's descriptions (`tools/gen_models.py`), replacing the recoloured vanilla creatures. Facelings stay on the game's faceless human body, which matches the lore, now with hair.
- **Reviewed** (2026-10-05, four parallel reviewers over the director, the AI, the smaller systems and the assets; findings verified against the decompiled engine before fixing). Fixed: thresholds missed by a 2-block sampling lattice (elevators and stairs are one tile deep); encounter phases timed from birth, which ended retaliation hunts at once; a Hunt↔Stalk flip-flop with a synchronous path search every 0.3 s when the target was unreachable (now a 4 s back-off); the glimpse crossing ending before its path search answered; the chase target aliasing the traverser's waypoint; no-path leaving the entity gliding; per-tick patience rates (now per second); The Thing's swim speed (~40 blocks/s); the Almond Water ward measured in server uptime; `harvestable` missing on the client (knives could not open our carcasses); Clumps pushed about by players; Deathmoth bites measured at the feet; Deathmoths uninteractable (own class now); Level 11's subway made passive; Level 8 without a heartland; Level 0 hunts outside the Red Rooms; pack spawns exceeding the cap; Facelings kept out of camps and sanctuaries; static state surviving a world reload; the director's tick without an error handler; a Flickering's fade never reaching zero.
- **Tested** on a headless server against a straw dummy (`/backrooms encounter ... x z`): spawning, placement, bands, the encounter state machine and attacks. Walking cannot be tested there (the server only moves entities near a player), so movement and the feel of each entity still need a play-through.

## 1. Design pillars

1. **Menace before harm.** Most encounters are sightings and sounds. An entity that is seen is far away, or still, or turning to leave. Damage is rare and always telegraphed.
2. **The edge is where it gets dangerous.** Each level is a ring; danger rises from its heartland to its outer edge, and peaks around the wall into the next level and around the thresholds (elevators, stairwells, doors that lead elsewhere). Getting through to the next level is the climax of each level.
3. **Every entity has a counter the player can earn.** Light, fire, Reality Stability, armour, doors and wards. Progress through the levels brings the counters, so later levels can field worse things without the game becoming a shooter.
4. **Lore first, then Vintage Story.** Entities behave as the wikis describe. Counters are vanilla mechanics wherever possible (light levels, temporal stability, armour, doors, herds, harvesting) so that a normal Vintage Story player's instincts work.
5. **Cheap where it can be.** Distant sounds and glimpses carry most of the fear and cost almost nothing. Real entities are capped per player and despawn when they have done their job.

## 2. The menace model

### 2.1 Bands

Every point in a ring level has a ring fraction `f` from 0 at the inner edge to 1 at the outer edge (`WorldLayout.RingFraction`, which already exists). Levels are divided into three bands:

| Band | Where | What happens |
|---|---|---|
| **Heartland** | `f < 0.6` | Sounds and glimpses. Entities spawn far away (24 to 40 blocks), stand or wander at the edge of sight, and leave or despawn when approached within about 14 blocks or watched for a few seconds. They never attack unless attacked. |
| **Approach** | `0.6 ≤ f < 0.85` | Stalkers. Entities follow at 8 to 14 blocks, keep out of the player's light, and test the player: they close in when the player is in the dark, running, or low on stability, and back off from light and fire. They attack only if cornered, attacked, or the player's stability is below 0.4. |
| **Threshold** | `f ≥ 0.85`, and anywhere within 40 blocks of a wall between two levels or 24 blocks of a threshold feature | Hunters. Entities seek and attack, in packs where the lore has packs. Their counters still work: a Smiler still will not enter light, a Hound still will not cross fire. |

Some places are a band of their own regardless of `f`:

- Always **Approach**: Level 0 blackout zones, Level 1 dark sections and Flickering events, Level 3's dark narrow stretches, Level 5 corridors next to boiler halls, Level 8 off the 9th Road, Level 9 streets in fog.
- Always **Threshold**: Level 0 Red Rooms, Level 7's midnight zone and the abyss, Level 8 dark pockets more than 30 blocks from the road.
- Always **safe** (no hostile spawns; hostiles that wander in turn passive and leave): the Manila Room, Level 3 Sanctums (the angel statues repel entities, as the lore says), Level 4's heartland, the Beverly Room, the Snackrooms, the 9th Road within 12 blocks of a lamp, Level 10's heartland, all of Level 11 (the "Level 11 effect": entities are present but will not attack unless provoked).

### 2.2 The menace value

The server keeps a **menace** value `m` in `[0, 1]` per player, recomputed every two seconds:

```
m = band base (heartland 0.15, approach 0.5, threshold 0.85)
  + 0.25 × (1 − player stability)        // Reality Stability, the gear on the HUD
  + 0.15 if the player stands in light level < 6
  + 0.4 × Reality Shift strength           // the lights are out everywhere
  − 0.3 while an encounter cooldown runs   // breathing room after a close call
  clamped to [0, 1]; forced to 0 in safe places
```

`m` drives three things: how often spawns are attempted, which encounter kind is spawned (glimpse, stalk, hunt), and the entities' own aggression (passed to them as an attribute they read each tick).

Reality Shifts become what they were always meant to be: the hour the lights go out and the things that avoid light come out.

### 2.3 Encounter kinds

| Kind | Spawn distance | Behaviour | Ends |
|---|---|---|---|
| **Sound** | none (no entity) | A one-shot sound played 15 to 40 blocks away, in a direction with open floor: a bark, wings, a skitter, a footstep that stops when you stop. Each level has its own set. | immediately |
| **Glimpse** | 24 to 40, out of the player's light, preferably just inside line of sight | Stands still facing the player, or crosses a doorway. Flees and despawns when the player comes within 14 blocks or looks at it for more than 3 seconds. | 10 to 30 s |
| **Stalk** | 18 to 30, behind cover | Keeps 8 to 14 blocks away, moves when the player moves, stops when they stop. Closes in the dark; retreats from light and fire. Attacks only when provoked, when the player runs, or when stability < 0.4. | 1 to 3 min, or when it attacks |
| **Hunt** | 14 to 24 | Seeks and attacks, respecting its counters. | death, flight, or 3 min |

Spawn attempts per player: every 2 s with chance `0.02 + 0.18 × m`, choosing Sound 60%, Glimpse 25%, Stalk 10%, Hunt 5% in the heartland and shifting to Sound 30%, Glimpse 20%, Stalk 25%, Hunt 25% at the threshold. Caps per player: 2 entities in the heartland, 4 in the approach band, 6 at the threshold. Entities despawn when more than 64 blocks from every player or after 3 minutes unseen. Nothing spawns within 12 blocks of a player, in light above level 7 (except Deathmoths and Facelings), or in a safe place.

### 2.4 Spawn placement

Spawns use the layout, not the chunk blocks, so they are cheap and never land inside walls:

- A candidate is a standable floor tile (`IsArrivalSpot`) at the right distance, matched to the entity: dark tiles for Smilers, corridor tiles for Hounds, tiles behind a wall from the player for Dullers and glimpses, lit tiles for Deathmoths.
- Line of sight is checked with a block ray from the player's eyes; glimpses want it, stalkers do not.
- At the threshold band, placement is biased toward the direction of the next level, so the danger reads as coming from where the player is going.

## 3. The roster

Eight entities carry the game. Three more are optional. Each is built on a vanilla model with a new texture and, where needed, a changed scale, because the game's animated creature models are far beyond what this project's box-model generator can do. New sounds are synthesised in `tools/gen_sounds.py` like everything else.

### 3.1 Core entities

| Entity | Lore | Behaviour in game | Counters | Model | Levels |
|---|---|---|---|---|---|
| **Smiler** | Reflective eyes and teeth in the dark; the body is never seen. Found in the dark of most levels, especially 2 and 3. | Exists only in light below level 7. Glimpse: a grin at the end of a dark corridor. Stalk: keeps to the dark, closes when the player's light fails or they run. Hunt: fast and hard-hitting, but stops dead at the edge of light. Cannot be killed; damage makes it withdraw. | Any light above level 7 (torch, lantern, firepit). Standing still facing it. Not running. | A custom shape: two glowing eyes and a glowing grin on an otherwise unrendered body (black, no texture, `glowLevel` on the face quads). No animation needed beyond a slow bob. | 0 (blackout zones, Red Rooms), 1 dark sections, 2, 3, 6 (eyes only, rare), 8 pockets, 9 unlit houses, 11 sealed-building interiors (rare) |
| **Hound** | Bald humanoids on all fours, white eyes, long limbs; hunt in packs; the first real predator a wanderer meets. | Packs of 2 to 3. Glimpse: one crossing a far doorway. Stalk: the pack shadows the player and circles. Hunt: chases, bites, tries to flank. Loud: barks announce it. Killable. | Fire (will not come within 6 blocks of a lit firepit or firesalt). Bright light slows them. Doors. Armour. A spear. | Own model (2026-10-06, to a design brief): a human body in a predator's stance, 23 px at the shoulder and 30 long. Human arms with elbows hold up the front on long clawed fingers; the legs are folded into a crouch with long flat feet; the back arches to tall bony shoulders, the highest point, with ribs and shoulder blades standing out. The head hangs below the shoulders inside a curtain of ragged black hair strands; the jaw is hinged at the back of the skull and opens to 75° with fang cuboids. Animations: an asymmetric crawl, a bounding run, alert (head snaps up through the hair), growl (head down, jaw parted, torso shaking, a step back: for the lore's eye-contact intimidation), attack (recoil, lunge, hair parts, bite), hurt, death, howl and a signature hind-leg scratch. | 1 (dark sections, corridors), 2 machine rooms, 3, 4 (rare), 5 corridors, 8 near the Level 9 edge, 9 streets, 11 (passive) |
| **Faceling** | Humanoids with no face; most of them passive; children harmless, adults can turn when provoked. Everywhere. | Ambient. They stand, wander, sit at tables, turn to look at the player, and go back to what they were doing. Never spawn as a hunt. Flee from Hounds (herd alarm) before the player can see the Hounds: an early warning. Attacking one turns the adults nearby hostile for a while. | Leave them alone. | The game's own faceless body (so they stand, walk, wave, nod, sit and stretch exactly like a player), with a wardrobe of attachment boxes (seven hair styles, jacket, coat, skirt, collar, backpack, bag, glasses, beanie, cap) painted per look or left transparent, 14 looks at 4 texels per pixel (2026-10-06, to a design brief). The face is skin lit like a face: forehead light, temples and jaw in shadow, warm cheeks, no features. Idle gestures from the vanilla set (wave, nod, stretch, a face wipe) and a `lookatentity` task so the blank face turns to follow a passing player. | 1 corridors and camps, 2, 3, 4 (many: the lore's settlement), 5 lobbies and dining rooms, 9 houses, 11 streets (crowds), 6.1 (friendly) |
| **Deathmoth** | Moths with a 40 cm wingspan; the males harmless scavengers, the females hunt in swarms; they nest in rooms with few entrances and come to bright light. | Males: flutter round the player's light and bump into it, harmless and unnerving. Females: swarms of 4 to 6 near hives, bite exposed players carrying bright light. Killable, fragile. | Put the torch away (a candle draws few, a lantern none). Smoke: standing in a firepit's smoke column scatters them. Leather or better armour cuts the bite to nothing. | Own models for both sexes (2026-10-06, to a design brief): 70% moth, 20% predatory insect, 10% Backrooms. Two pairs of wing planes (pointed forewings over rounder hindwings, stepped tips, worn edges) painted like water-stained wallpaper with a false eye spot on each forewing; a small head with faceted burgundy compound eyes and three ocelli, fuzz boxes on the thorax, a banded tapering abdomen, six clawed legs in three segments. Male: 21 px wingspan, broad plumed antennae (barb planes cut to transparency), a three-segment proboscis coiled under the head that uncoils to feed. Female: 28 px wingspan, heavier body, narrower antennae, chitin mandibles, darker markings, a dark red caustic tip. Animations fly (16 frames, the butterfly class plays it at 2.5x), glide, rest (wings folded in a roof over the abdomen, a shiver now and then), feed (per sex), and for the female bite (played by `AiTaskMoth.Bite`) and threat (wings snap open to the eye spots, abdomen curls under; not yet triggered). | 1 near lights, 5 (hives in some guest rooms and boiler halls), 9 round street lamps, 10 rare |
| **Skin-Stealer** | Large pale-yellow humanoids with sunken eyes; passive when fed, predatory when hungry; mimic speech. "Blood runs clear." | Wanders slowly like a lost person. Plays snippets of a human voice (a cough, "hello?", a sob) from out of sight. Hungry on a timer: then it stalks and, at the threshold band, hunts. Strong but slow. Killable; drops a hide. | Keep your distance; it is slow. Doors. Armour. Fire. | Own model (2026-10-06, to a design brief): 35.6 px tall, person-shaped but wrong: forearms too long, hands at the knees, a thin long neck, a narrow pitched head with sunken white eyes at two heights and a fold of loose skin under the jaw; waxy patchy skin. Walks like it learned by watching (flat careful feet, stiff elbows, head out of step); the idle has a delayed head tilt and a shoulder twitch, and a rare `skinadjust` where it drags a hand along its jaw and pulls at the skin. | 1 (near camps), 2, 3, 5 (as a guest), 9 (inside houses) |
| **Duller** | Tall skeletal grey humanoids, no face; hunt by reaching an arm through a wall; cowards that flee when faced; avoid Almond Water. | Spawns on the far side of a wall from a corridor the player is in. When the player passes within 2 blocks of that wall: a grab (2 damage, the player pulled one block toward the wall, a sound), then it flees at speed and despawns. Seen head-on it runs. | Walk down the middle of corridors. Drink Almond Water (ignored for 5 minutes after drinking, and always above stability 0.8). | Own model (2026-10-06, to a design brief): the architecture turned predator. 36 px drawn (39.5 raw at size 0.92), a narrow unfinished head with the skull long at the back and a narrow jaw (no brow, nose, ears or mouth), a long thin neck, sloping shoulders (the right lower), a torso too narrow to hold anything, arms to mid-shin ending in large ordinary four-fingered hands, thin legs with bent knees and feet not parallel, the pelvis drifting. Matte charcoal and ash with pale knuckles of bone at the joints, no warmth. Each forearm hides two extension segments that slide out along the arm in the grab: the attack animation raises the arm level and reaches 2.8 blocks with the body almost still, fingers snapping shut on frame 12 (the entity's 400 ms). Animations: idle (sway, a lagging head, one arm swinging more, knee corrections, fingers opening and closing), walk (feet inward, lateral sway, arms late, head level), run (long strides, hard forward lean, arms back), `despair` now the wall-listen (palm flat to the wall, head tilting, waiting), hurt, death (knees buckle, it folds, the long arms sprawl). | 4 (the lore's Dullers), 3, 6, 8, 11 subway |
| **Death Rat** | Rats the size of dogs; packs in tunnels and alleys. | Packs of 3 to 5; skittish; nip at the player's legs in the approach and threshold bands; scatter from light and noise. Killable; the one entity that is food (meat, bones). | Light. A club. Doors. | Own model (2026-10-06, to a design brief): 80% rat, 20% Backrooms. 8 px at the shoulder, 32 nose to tail; a low body on high haunches, a tapered head with a hinged jaw, four dirty incisors, round pink ears, six hairline whiskers, a six-segment hairless tail that does the acting, and two short keratin horns swept back from the crown, brown at the root with glowing crimson tips (glow 150; the eyes stay dark). Animations: idle, sniff, groom (sits back and washes its snout), rear-up (the signature: on its hind legs, nose in the air), eat, walk, scamper (wandering), run (a bound), attack (dart, bite, straight back), hurt, death (rolls over, legs curl, one tail twitch). A hairless grey-pink variant texture for Level 2's heat is painted on the same atlas (`deathrat-hairless.png`), not yet wired to spawns. | 1 halls, 2, 3, 5 boiler halls, 9 bins and yards, 11 alleys |
| **Wretch** (Level 8's drifters) | Level 8 is "savage, feral" and its dark holds things that hunt. | The vanilla drifters already spawning off the 9th Road, kept as they are and folded into the menace model (glimpse and stalk off the road, hunt in the dark pockets). | The lamps of the 9th Road (a safe place). Light. Armour. | Vanilla `drifter`, unchanged. | 8 |

### 3.2 Optional entities (after the core is in)

| Entity | Lore | Game | Model |
|---|---|---|---|
| **Clump** | A bundle of limbs that buries itself and grabs anything within 8 feet. Levels 2, 3 and 10. | Mostly dormant: one arm sticking out of the ground (a block-sized prop until disturbed). Wakes when a player comes within 2.5 blocks: grabs for 4 damage, then digs in again. Killable while dormant. | Own model (2026-10-06, to a design brief): human anatomy recombined with no front, back, top or bottom. Six overlapping flesh cores (no ribs, no pelvis) 14 px wide and 12 high, propped on ten limbs leaving the mass at conflicting angles with bent elbows and raised knees: arms, legs, a forearm ending in a foot, a thigh ending in a hand, a child's arm, each a different desaturated skin, cracked and dry out along the limb and raw and wet at the root. A mouth in the top of the knot under four flaps of flesh, lined with fourteen crooked human teeth. A 27 px capture arm folded along the floor in front. Two wet eyes and an ear in the mass; a second texture (`clump-blind`, a random alternate) has none. Animations: idle (fingers flex, a leg twitches, an arm reaches and a hand grips, eyes look about separately), stir (limbs re-plant in turn as someone comes near), grab (freeze, limbs spread, the arm snaps straight, the hand clenches, the arm sweeps up to the opening mouth), feed, crawl (three limb groups out of step), death (a limb fails, the mass tips, arms reach, one pushes and weakens, it sinks, a last finger moves). |
| **The Thing on Level 7** | Something vast in the deep water; it is why nothing else lives there. | Never fully seen. In the midnight zone and the abyss, a black shape circles the diver 20 blocks out. If the player stays below the twilight zone for more than 40 seconds with stability under 0.5, it strikes once (8 damage) and goes. A deep groan precedes it. | `fish-saltwater-adult` scaled ×8, black, no glow, `renderPass` dark. |
| **The Mangled** | Entity 63: a spider-like thing the size of a house in a smokescreen; the cold comes first; its legs pass for black trees or pillars; its body is faces merged into one mass; it snatches people with a tendril. Comes with the fog in Level 9. | Spawns only during fog events in Level 9's threshold band. A hunt that ends when the fog clears. Slower than a walking player (it is the reach that kills: a tendril 4.5 blocks out, lifted 7 blocks and dropped). | Indoors. Out of its reach. Keep moving. | Own model (second pass, 2026-10-10, to the Wikidot article and its sketch): a harvestman, not a tarantula. 314 parts, 11.7 blocks tall drawn; eight legs rise to a crown of knees above the body and drop as knotted black trunks that taper to points. Under the front of the body a knot of flesh on a stalk carries fourteen modelled faces (brows, open or shut eyes, noses, hinged jaws that talk and scream), one apart on its own lobe screaming, two more sunk in the abdomen; seven tendrils, three ending in hooked fingers; frost on every upward face. Animations: walk (one leg at a time, a footfall every half second; played 1.4x to match its speed), run, idle, `despair` as the search (every face pushes out and talks), attack (lashes forward to 4.5 blocks at 450 ms and hauls the victim overhead), hurt, death. | 9 (fog events) |
| **Bacteria** | The dark figures of Level 0 ("wanderers have claimed to have seen dark figures stalking them between the corridors"), as the Howler of Kane Parsons' found footage (Entity 1 on the Fandom wiki): very tall, thin, a tangle of black wires in a human shape, arms to the floor, rising out of black mould, a distorted howl. | Rare, outer bands of Level 0 only. Glimpse: rises out of the carpet's mould far down a hall, stands, is gone. Stalk: follows at 12 to 20 blocks. The only thing in the Lobby that hunts (outside the Red Rooms), and only someone who runs within 20 blocks of it near the way out: it howls first (1.5 s), then outruns a sprint. Killable (30 health, a good bounty). | Don't run near it. Walk away. | Own model (2026-10-10): 106 parts; stoops to 2.76 blocks under Level 0's ceiling (hitbox kept to a doorway's 1.95); every limb a bundle of twisted strands with cable wraps and ragged cut wires, frayed root strands for feet, four long two-jointed fingers per hand resting on the carpet; a faceless lump of a head with a lens-like hollow and a jaw seam that opens to howl; near-black with an olive mould tint; a mould stain that shows only as it emerges and dies. Animations: idle, lurk, walk (stiff, hands dragging), run (bent forward, clawing the carpet like front legs), attack (rears, closes both arms round you at 440 ms), hurt, die (sinks into the stain), emerge (2.5 s, out of the mould), howl. Sound: a synthesised howl (`entity/howl`). | 0 (outer bands) |
| **Wretches** | Entity 15: wanderers undone by the Wretched Cycle (hunger, thirst, sleeplessness). Reddish-brown flaking skin full of holes and pustules oozing sludge; lidless rolling eyes, no lips, teeth and nails regrowing in the wrong places; their clothes and belongings still on them; from a shamble to a sprint past a human's; they gurgle and snarl; they live in the shadows wherever people gather. | Ones and twos near camps and lobbies (Levels 1, 3, 5, 9, 11's subway), packs of up to three in Level 8's dark (in place of the vanilla drifters). Three times as likely to come for someone down to the last quarter of their satiety. Huddle and gnaw when idle; gurgle while stalking; rear and snarl (1.2 s) before the chase, then a bite. Killable (16 health); drops a bounty and one or two of what it carried as a wanderer. | Keep fed. Fight them one at a time; they are fragile. | Own model (2026-10-10): 71 parts, 1.8 blocks hunched, bent nearly double with spine and shoulder blades standing out; the remains of a wanderer (rags of a t-shirt, belted jeans torn at the knees, one sneaker, a backpack strap with a torn pouch); no lips, no nose, lidless bloodshot eyes, teeth growing from a cheek, a nail from a forearm, pustules as real bumps, sludge running from holes. Three looks chosen by depth: early (stage 2, still dressed, rash and scratches; most common near the top), common (stage 3), far gone (rags of its own skin, yellowed eyes; most common deep). Animations: idle, walk (a limping lurch), run (bent sprint, arms grabbing forward), attack (bite at 430 ms), hurt, die, huddle, gnaw, snarl. Sounds: synthesised gurgle and snarl. | 1, 3, 5, 8, 9, 11 subway |

Not planned, with reasons: Vandals (hostile humans do not fit a game about the unknown), Windows (a static trap, better done as a block later), Partygoers (Level 3's wikidot section the levels do not have), the Beast of Level 5 (one more large humanoid adds little), Jerry (no).

### 3.3 Sounds without bodies

Half the tension is sound. Each level gets a distant-sound set, played by the Sound encounter from a direction with open floor, with its frequency scaled by menace:

- Level 0: scratching behind the walls, a voice two rooms away saying a word you almost catch, the hum rising and falling.
- Level 1: a bark echoing through the car park, a crate dragged, boots in the corridors.
- Level 2: skittering in the pipes, a long metal groan, something breathing in a side tunnel.
- Level 3: a bell, a cough, machinery winding up.
- Level 4: a phone ringing once, a chair pushed back, nothing else.
- Level 5: the whispers the lore describes behind you, a tap on the shoulder (a sound at the player's position), children laughing far down a corridor, the jazz changing track.
- Level 6: the Mimicry: footsteps that match the player's and stop a half-step late; breathing; the drips of water that is not there (some of this already exists in `AtmosphereSystem.DarkEvents` and should move into this system).
- Level 7: a groan from below; a splash behind you.
- Level 8: rockfall, a drifter's moan, running feet on gravel.
- Level 9: a dog that is not a dog, a door slamming in a house, a television's static.
- Level 10: the worms under the soil, wings high up, a cowbell with no cow.
- Level 11: a car alarm blocks away, the subway's train that never comes, a crowd murmuring round a corner that is empty.

## 4. Counters and progression

The player should feel each level hand them a way to deal with the next.

| Where it is earned | Counter | What it does | Game mechanic |
|---|---|---|---|
| Level 0 | Light (candle, then torches) | Smilers will not enter light above level 7. | Vanilla light levels; Smiler AI reads the player's light. |
| Level 0 | Almond Water | Entities target low-stability players first; Dullers ignore you for 5 minutes after a drink. | Vanilla `lowStabilityAttracted` and `RequiredTemporalStability`, plus an attribute set by the Almond Water item. |
| Level 0 | Standing still and facing it | A Smiler holds while looked at and the player is not running. | Smiler AI checks the player's facing and speed. |
| Level 1 | Fire (firepit) | Hounds and Skin-Stealers will not come within 6 blocks of a lit firepit. A camp is safe. | A ward registry: lit firepits register themselves; hostile AI avoids wards. |
| Level 1 | Doors and barricades | Entities do not open doors. Vanilla doors from salvaged planks (and the Level 1 crates' planks) close off a room. Chests and crates block doorways. | Vanilla pathing. |
| Level 1 | Spear, club | Kill Hounds and rats. | Vanilla knapped spear; a club from planks. |
| Level 1 | Improvised wood armour | Halves the bites of rats and Deathmoths. | Vanilla recipe (boards + knife). |
| Level 3 | **Firesalt** (new) | A handful placed on the floor burns bright for an in-game hour. Nothing hostile comes within 8 blocks. Found in generator rooms (the lore puts Firesalt there); crafted later from salt and sulfur (Level 8). | New block with a light source and a ward entry. |
| Level 3 | Sanctums | Angel statues repel entities within 12 blocks. The Sanctum is the first guaranteed safe room outside Level 0. | Statue props register as wards. |
| Level 4 | Lantern | A closed lantern does not draw Deathmoths; a torch does. Camp lanterns in Level 1 drop one now and then. | Deathmoth AI reads the kind of light the player holds. |
| Level 5 | Leather armour | From Hound and Skin-Stealer hides, and later Level 9 and 10 animals. Cuts rat and moth bites to nothing, Hound bites by a third. | Vanilla armour. |
| Level 8 | Copper and bronze armour and weapons | The real answer to Hounds and Skin-Stealers. | Vanilla progression. |
| Level 8 | Sulfur | Firesalt can be made rather than found. | Quern salt + sulfur. |
| Level 10 | Bows | Feathers from chickens, flax for string. Kill at range. | Vanilla. |
| Everywhere | Reality Stability itself | High stability makes entities hesitant; low stability makes them bold. | Already drives the menace value. |

Damage and health, before armour (player health is 15):

| Entity | Health | Damage | Notes |
|---|---|---|---|
| Smiler | immortal | 6 | Withdraws when hurt; attacks rarely and only in the threshold band or Red Rooms |
| Hound | 12 | 2.5 | Packs of 2 to 3; retreat at half health |
| Skin-Stealer | 28 | 5 | Slow |
| Duller | 15 | 2 plus a pull | One grab, then it flees |
| Death Rat | 4 | 0.75 | Packs of 3 to 5 |
| Deathmoth (female) | 3 | 1 | Swarms of 4 to 6 |
| Clump | 20 | 4 | Grabs within 2.5 blocks |
| The Thing | not fightable | 8 | Once |

## 5. Level by level

| Level | Heartland | Approach | Threshold | Notes |
|---|---|---|---|---|
| 0 | Sounds only: the lore has no entities here. | Blackout zones: Smiler glimpses and stalks. | Near the Level 1 wall: Hounds heard, a Smiler stalk. Red Rooms: a Smiler hunt. | The player's first lesson: light keeps the eyes away. |
| 1 | Facelings at camps and in corridors, rats in the halls, a Hound barking far off. | Dark sections and Flickering events: Hound packs stalk; Smilers in the dark. Skin-Stealer at a camp, looking like a wanderer. | Hound hunts; Deathmoths round the lights near the Level 2 wall. | Flickering (whole sections going dark) becomes an event: Hounds hunt until the lights return. |
| 2 | Rats in the pipes, Smiler eyes, a Skin-Stealer's voice. | Smilers stalk every dark stretch; rats nip. | Smiler hunts in the dark, Hounds in the machine rooms. Clumps (optional). | The level where the player learns to carry two torches. |
| 3 | Facelings, Smiler glimpses in the squeezes, machinery. | Hounds, Skin-Stealers, Dullers through the room walls. | Hound packs; Smilers wherever the lights are out. | Sanctums are safe; Firesalt is found in generator rooms. |
| 4 | Facelings everywhere, going about nothing. The safest level before 10 and 11. | A Duller in the office walls, rarely a Hound. | Hounds near the elevators and stairwells. | Keep this calm: the lore makes it the hub where people rest. |
| 5 | Facelings as guests, Deathmoth males round the sconces, whispers. | Hounds in the corridors, Skin-Stealers among the guests, Deathmoth hives in some rooms. | Hound packs; Deathmoth swarms near the boiler halls. | The Beverly Room is safe. The jazz and the whispers do the work. |
| 6 | Mimicry footsteps, breathing. Nothing seen. | Smiler eyes, rarely; Dullers at the walls. | Dullers; a Smiler hunt near the stairs down. | Darkness is the entity. Keep real spawns very rare. |
| 6.1 | Facelings, friendly, at the tables. | none | none | |
| 7 | Fish; a groan from below. | The Thing circles in the midnight zone (optional). | The Thing strikes in the abyss. | Dive depth is the danger dial. |
| 8 | Wretches (drifters) glimpsed off the road; rats; rockfall. | Wretches stalk off the road; Dullers; Smilers in the pockets. | Wretch and Hound hunts near the Level 9 edge. | The 9th Road's lamps are the safe line. |
| 9 | Facelings at kitchen tables; rats in the bins; a dog barking. | Hound packs in the streets; Smilers in unlit houses; Skin-Stealers in locked houses that open. | Hound hunts; the Mangled in fog (optional); Deathmoths at the lamps. | Houses are refuges only if you close the door behind you. |
| 10 | Livestock; worms; a cowbell. Safe, as the lore says. | Clumps buried in the fields (optional); Deathmoths over the barns. | Hounds near the Level 11 barns. | Keep the fields safe: the player needs somewhere to farm. |
| 11 | Facelings in crowds, Hounds that ignore you, rats in the alleys. | Rats nip in the alleys; Dullers in the subway. | A Smiler in a sealed building's dark interior if the player breaks in (they cannot: so, in the dark of a parking garage). | The "Level 11 effect": provoke nothing and nothing provokes you. |

## 6. Wanderers (recommended, phase 4)

The lore's Backrooms are inhabited: the M.E.G., Base Omega in Level 4, settlements on the 9th Road, 130,000 people in Level 11. Vintage Story has traders built in. The two fit:

- **Wanderer traders** at Level 1 camps, Level 4 (one per few cells, as Base Omega's outposts), the 9th Road camps and Level 11 plazas: the vanilla `trader` entity with a Backrooms skin and trade lists. They buy salvage (brackets, wire, cloth, hides) and sell Almond Water, candles, bandages, Firesalt, seeds and the odd copper tool. Currency: rusty gears, which already drop.
- They are safe places in themselves (hostiles will not approach a trader's camp) and the only friendly faces, which makes Facelings feel stranger by contrast.

This is a separate phase; the core roster does not depend on it.

## 7. Implementation plan

### 7.1 Code

New folder `src/Entities/`:

- `MenaceSystem` (server): per-player menace value, bands, safe places, encounter cooldowns; exposes `MenaceAt(player)` and `BandAt(x, z)`. Replaces the level-specific spawn tables in `src/Deep/CreatureSystem.cs`; the existing wildlife, livestock and fish spawning move into its roster as "ambient" entries.
- `EncounterDirector` (server): spawn attempts, placement from the layout, caps, despawn, encounter kinds, the direction bias toward the next level.
- `DistantSounds` (server): the Sound encounter; per-level sound sets; takes over `AtmosphereSystem.DarkEvents` (keep the client-side reveal flashes there).
- `Wards` (server): registry of ward points (lit firepits, Firesalt, Sanctum statues, 9th Road lamps, trader camps, the Manila and Beverly Rooms); `IsWarded(pos, radius)`. Firepits register through a block behaviour patch; props through the layout at chunk load.
- AI tasks (registered with `AiTaskRegistry`), each a small class over the vanilla base tasks:
  - `AiTaskGlimpse`: stand and watch; flee and despawn when approached or watched.
  - `AiTaskStalk`: keep a distance band from the target, prefer dark tiles, close or retreat with the menace attribute.
  - `AiTaskAvoidLight` / `AiTaskSeekLight`: the Smiler's and the Deathmoth's relationship with light; use `TargetLightLevels` on the vanilla seek task where it suffices.
  - `AiTaskWallGrab`: the Duller.
  - `AiTaskRespectWards`: a pre-check mixed into seek and melee tasks.
- `EntityBehaviorMenace`: reads the menace attribute the director sets and scales the entity's seek range, aggression and move speed; handles "withdraw when hurt" for the Smiler.
- Items and blocks: `firesalt` (block with light and a timed burn, plus the recipe and the generator-room loot), Hound and Skin-Stealer hides (vanilla hide items work as they are).
- Debug: `/backrooms menace` (shows the player's band and value), `/backrooms encounter <kind> <entity>` (forces one), `/backrooms wards`.

### 7.2 Assets

- `assets/backrooms/entities/*.json`: one file per entity, built on the vanilla entity it derives from (copy the vanilla definition's shape, animations and behaviours; change textures, scale, tags, drops and the AI task list).
- `tools/gen_entities.py`: writes the entity JSON, the retextures (PIL, from the vanilla textures recoloured and edited) and the lang names, in the style of the other generators.
- `tools/gen_sounds.py`: barks, skitters, wingbeats, murmurs, the Mimicry footsteps, the Thing's groan; synthesised like the existing sounds.
- `assets/backrooms/lang/en.json`: names, and the handbook's new page (see 7.4).

### 7.3 Phases

1. **Foundation** (no new creatures yet): `MenaceSystem`, `EncounterDirector` with the Sound encounter and the per-level sound sets, `Wards` with firepits and statues, the debug commands. Fold the existing spawner in. Playable on its own: the levels get their soundscape.
2. **The first two**: Smiler and Hound, with Glimpse, Stalk and Hunt, light and fire counters. Tune on Levels 0 to 2 until a dark corridor feels right.
3. **The rest of the core**: Facelings (and their herd alarm), Deathmoths and the lantern rule, Skin-Stealers and their voice, Dullers, Death Rats. Firesalt. Flickering as a Hound event in Level 1.
4. **Wanderers**: trader entities, skins, trade lists, camp wards.
5. **Optional entities**: Clumps, the Thing, the Mangled.
6. **Tuning pass**: numbers in sections 2 and 4 against real play, with a world-config setting `backroomsMenace` (Off: sounds only; Low; Normal; High) so players can choose.

### 7.4 Documentation

- README: an "Entities" section and a line per level.
- Handbook: a new page, "What Lives Here", listing each entity with its counter, written in the voice of the other guide pages; and the Starter Guide's step 10 extended with "if you see eyes in the dark, raise your light and walk, don't run".
- Memory notes for the project.

### 7.5 Testing

- Headless server: spawn placement and caps can be exercised with a command that runs the director for a fake position; entity JSON and textures are validated by a load with zero errors.
- The behaviours themselves need the client. Test script per entity: approach from the dark, approach with a torch, run away, stand still, drink Almond Water, stand by a firepit, close a door.
- Performance: the director's cost is bounded by the per-player caps; sounds cost nothing; the layout-based placement avoids block scans.

## 8. Decisions to make

Recommendations in bold.

1. **Can Smilers be killed?** **No.** The lore never kills one, and an unkillable thing that light holds back is the game's thesis. Damage makes it withdraw.
2. **Wanderer traders?** **Yes, as phase 4.** They are the most Vintage-Story-native way to give the levels life and an economy for salvage, and they fit the lore.
3. **A difficulty setting?** **Yes: Off / Low / Normal / High**, with Off keeping only the sounds. Cheap to add once the menace value exists, and it lets the fear be tuned without touching the design.
4. **Facelings in Level 0?** **No.** The lore is explicit that Level 0 is empty, and an empty Level 0 is what makes the first Faceling in Level 1 land.
5. **The Thing on Level 7 and the Mangled**: build after the core, only if the deep levels feel too quiet in play.
