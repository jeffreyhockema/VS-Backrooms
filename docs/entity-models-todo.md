# Entity models and behaviour, 2026-10-06: status, checks, what is left

Eight entities were remodelled from design briefs in the afternoon (Skin-Stealer, Hound, Facelings, Death Rat,
Deathmoths, Clump, Duller, The Mangled), then given the behaviours the briefs asked for in the evening. Review sheets
are in `docs/entity-review/`. Everything below marked done compiles, and a headless server put down every changed
entity without errors; movement and anything seen on screen still need a client.

## 1. Fixed after the first play-test

- [x] **Facelings drawn as scattered squares.** The vanilla seraph shape declares `textureSizes: {"seraph": [32, 76]}`,
      which wins over `textureHeight`, so every face sampled the wrong rows of the new taller texture. The generator
      now writes the real size there. `tools/entrender.py` honours `textureSizes` too, so previews catch this now.
- [x] **"Missing attachment point Center"** warnings for every new shape: `rig.py` adds a Center point to each
      model's root part; the Faceling shapes get one on the lower torso.

## 2. Check in game (in this order)

- [ ] **Facelings** look right now (body, clothes, hair, empty glasses lenses, hair ends cut ragged).
- [ ] **A Faceling's head follows you** (client only). If it turns away from you instead, flip the sign in
      `FacelingHeadController.OnFrame`.
- [ ] **Right-click a Faceling**: it waves, then turns and points, then nods. Children only wave.
- [ ] **Hit a Faceling** in Level 4 or the city: the others near it come at you, even there.
- [ ] **Stare at a stalking Hound** from under 12 blocks: it should stop, growl and back off, then come on after a
      few seconds.
- [ ] **Death Rat horns** give a faint red light in the dark; rats in Level 2 are hairless.
- [ ] **Deathmoths settle** on floors and table tops with wings folded, and take off when you come close. Walk up to
      a settled female near an edge: she rears, wings open, and the swarm turns on you.
- [ ] **Clump**: only a forearm and hand should show above the floor until you come within 4 blocks, then the whole
      knot rises. Run or break boxes nearby: it should crawl after you. (The buried pose relies on its animation
      weight beating the idle; if the mass shows half above the floor, raise the weight of `dormant` in
      `gen_entities.py`.)
- [ ] **Duller grab**: plaster dust puffs from the wall on your side. Now and then a hotbar item vanishes; it lies on
      the floor where the Duller went.
- [ ] **The Mangled**: use `/backrooms mangled` on Level 9. Fog and a temperature drop for 45 s with voices, then it
      walks in (12 blocks tall, drawn at 1.5), the camera shaking with its steps; its tendril lifts you up to 7
      blocks. Check whether its legs clipping house fronts looks acceptable in the fog, and whether the lift's fall
      damage is too much.
- [ ] **The Screaming** (Levels 1 and 2, rare): `/backrooms scream` starts one.

## 3. Behaviour from the briefs: done

| Entity | Done |
| --- | --- |
| Hound | Stare-down (`staredDown` in the menace task, uses the `growl` animation); starved and old looks as texture alternates (25 % and 12 %), the old ones with half again the health |
| Facelings | Rarer (per-entry `Rarity`, at most 2 near a player, 3 in the city); children (`faceling-child`: drawn at 0.68 with a larger head, six play-clothes looks, curious, flee when rushed, tantrum when hurt); head-only tracking; greeting with wave, point to the nearest gate, nod; kin defence; provoked Facelings ignore a place's safety for 90 s |
| Death Rat | Hairless look in Level 2 (set by the director at spawn); glowing horn tips (`EntityDeathRat`); the Screaming (lights fail, two bursts of `ratscream`, a pack crossing ahead at a run) |
| Deathmoths | Settle and rest; males feed beside water or bodies; females threaten when approached or hurt; the alarm sets every female within 16 blocks on the cause and sends the males away |
| Clump | Buried with one arm out (`dormant`), rising (`emerge`), hunting by noise and running within 14 blocks (`crawl`), feeding after a grab, burying itself again when things go quiet, crawling away when it leaves |
| Duller | Plaster dust on a grab (instead of a shimmer, which entity shaders would not show reliably); theft, 25 % of grabs; scraping, dragging and knocking from out of sight; Almond Water fountains and seeps keep it off within 6 blocks |
| The Mangled | `MangledEvent`: rare per-player event in Level 9 (once in ~40 minutes at the edge, 8x in a Reality Shift, 80-minute cooldown); 45 s of fog, cold (-16 °C on the climate, so body temperature falls) and mimicked voices; 3 minutes hunting (longer if struck); 30 s of the fog lifting. Unkillable and unmoved by blows; the tendril lifts its target up to 7 blocks; the client shakes with its steps; the director no longer puts it down |

## 4. Not done, and why

- **Faceling evolved, shadow and memory variants**: each needs its own model or texture set and a behaviour. Worth
  doing as rare variants once the common Faceling is confirmed in game.
- **Engineer rats (Level 3)**: a larger variant that builds traps needs a trap block and new AI. Nests and hoards
  are worldgen in `WorldLayout.Dens`/`Loot`, owned by another session.
- **Deathmoth castes (larva, Praetorian, Empress) and hives**: my call was to skip them for now. Each is a new
  model, and the hive stages are worldgen. The common moths' behaviour was the higher value. Domestication is also
  left for later.
- **Clump climbing, tool use, limb damage, juveniles**: climbing needs wall-walking physics the engine does not give
  land creatures; the rest are separate systems.
- **Duller carrying objects** and **resting moths on walls and ceilings**: neither is supported by the physics the
  entities use.
- **The Mangled as several synchronised entities, and its evolution stages**: one large shape covers the encounter;
  the stages would be texture and size steps tied to how often it has been met.
- **The handbook** was updated afterwards ("What Lives Here": staring down Hounds, greeting Facelings, settled moths, Duller theft and Almond Water sources, the Screaming, buried Clumps hunting by ear, the Mangled's event).

## 5. Tooling notes

- `tools/entrender.py`: `anims=`, `frames=`, `frame=N` (one frame from every view), `views=front,side,34,back,top`,
  `scale=`, `cell=`, `cellh=`, `yoff=px`. Honours `textureSizes`. It draws everything, including what the floor
  would hide (the buried Clump).
- Headless entity tests: the scratchpad `headless.py` pattern (start the server with the scratch build, pipe console
  commands with CRLF, `/backrooms encounter <entity> <kind> 512016 512016 <distance>` next to a straw dummy). In Git
  Bash set `MSYS_NO_PATHCONV=1`, or every `/command` becomes a path. Entities think but do not move without a
  player near (the server runs no physics for them).
- Rig gotchas: every keyframe names every part the animation touches (`full(names, d)`); child limbs inherit the
  parents' rest rotations; `Model.mirror` only renames names ending in `L`/`Left`; offsets in keyframes are in the
  part's own frame; variant textures are painted by building the model again with other globals and saving only
  the PNG.
- `EntityButterfly` (the Deathmoths' base) drives `fly` and `glide` itself, and leaves animations alone only while
  `rest` or `feed` is playing.
- Head turning: only players get a head controller from the engine, and `HeadYaw` is not synced. Facelings set their
  own client-side controller.

## 6. Second lore pass (2026-10-10): the entities that had none

Every entity without a lore-and-model review got one, each by an agent that researched the wikis (briefs with
sources in `docs/entity-briefs/`) and built in a sandbox; integrated through `tools/locked.sh`. Review sheets in
`docs/entity-review/`. Codes, texture codes, animation codes and C#-referenced element names are unchanged throughout.

| Entity | Was | Now |
| --- | --- | --- |
| Smiler | stick figure, 17 parts | 92 parts: in the dark only a 33-tooth grin and slit eyes glow; in light a thin black body with backward-bent elbows and knees, black-fire tatters. Added `hurt` (registered) |
| The Thing (Level 7) | black slab, 15 parts | 135 parts: an 11-block eel-like leviathan, undershot jaw of needle teeth, mismatched milky eyes, glowing photophores and barbels. Added `rush`; its AI now plays `rush` and `attack`; selection box 7.5 x 2 so it is not culled |
| Kitty (974) | | sloped shoulders and egg head after the Wikidot photo; kneel fixed (was floating); richer idle, ask, glide, take |
| Window arm (188) | pencil, 18 parts | 26 parts: tapering, knuckled, four-joint fingers and thumb, a stump into the glass; reach unfolds the wrong way and ends closed; pull 12 / recoil 60 weights |
| Keymaster (Hub) | 89 parts | 117: real cowl with glowing eyes, robe and capelet, boots (canon: he lands and strides), 15 mixed keys; `descend`'s cloak now moves; new `dismiss` and `stride` (played by `HubTower`) |
| Attendant (3999) | egg head with a grille | a faceless shop mannequin in a tailored cabin-crew uniform (canon: Fandom Level 399), ear-grille speakers |
| Partygoer and intern (Fun) | | canon proportions, hook-lined chest doors over the centipede, which reaches out in berserk; the carved "=)" kept exactly; the intern's balloon stays upright |
| Lure balloon, Party Host (Fun) | | a glossy balloon on a swaying string; the Host as canon Level 26's single eye-and-mouth organ in a golden dome |

Check in game: the Smiler's glow at full 255; The Thing's jaw direction and its size against shallow seabeds; the
arm's semi-transparent edges and whether it blocks the view up close; the Keymaster's dark face under the Tower's
light. Suggested to the owning sessions and applied since: lure balloon hitbox 1.8 tall, Party Host invulnerable, attendant
eyeHeight 1.38. Still open: the "mannequin" wording and the arm's selection box (~1.4 x 1.2; now 0.7 x 0.6).

## 7. The Mangled again, and two new entities (2026-10-10)

Briefs: `docs/entity-briefs/mangled.md`, `bacteria.md`, `wretch.md`; sheets: `docs/entity-review/mangled.png`,
`bacteria.png`, `wretch.png`. Full rows in `docs/entity-plan.md`.

- **The Mangled, second pass**: rebuilt to the Wikidot article and its own sketch as a harvestman the size of a house
  (314 parts, 11.7 blocks drawn), with a hanging knot of fourteen modelled faces, seven tendrils and frost. Speeds cut
  to 0.01 walking and 0.024 running (the animations played 1.4x and 1.7x) so the legs do not skate; eye height 6.5.
- **Bacteria** (`backrooms:bacteria`): Level 0's dark figures, as the found footage's Howler. Rare (weight 0.6 in
  the approach band), glimpse and stalk only; hunts only someone running near the way out (`huntsInLobby`). Rises out
  of the mould when it appears (`emergeAnimation`, 2.5 s) and howls before the chase (`huntAnimation`, 1.5 s).
- **Wretches** (`backrooms:wretch`): Entity 15. Levels 1, 3, 5, 9, 11's subway, and in packs in Level 8 instead of
  the drifters; three times the weight against a starving player; look by depth (`MenaceSystem.ChooseLook`); drop
  belongings like a Skin-Stealer.
- **New in `AiTaskMenace`**: one hold (`Hold`) that stands it still and plays an animation through, used for
  `emergeAnimation` (once, on appearing) and `huntAnimation`/`huntAnimationMs` (as it turns to the hunt).
- **New sounds** (`tools/gen_entity_sounds.py`): `entity/howl`, `entity/gurgle`, `entity/snarl`.

Check in game:
- The Mangled's 2.35 MB shape (the old was 1 MB): load time, and the frame rate with it on screen.
- Its stride at the new speeds: whether the feet still skate.
- The Bacteria's head above its 1.95 hitbox clipping through door lintels; its fingertips dipping into the carpet in
  walk and run; its arms in the attack passing through the walls of narrow halls.
- How rare the Bacteria feels in practice.
- Wretch packs in Level 8: three biting at once may be too much at danger 0.74.

Open:
- A mould stain left where a Bacteria dies.
- The Wretches' rare mutated forms (misplaced eyes, extra limbs, flesh "wings") as further looks.
