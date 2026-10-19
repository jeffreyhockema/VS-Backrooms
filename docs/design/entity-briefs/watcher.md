# Watcher (Entity 96, floating form): design brief

## Sources
- Wikidot, Entity 96 "The Neighborhood Watch" (primary): http://backrooms-wiki.wikidot.com/entity-96
  - Watchers are "gigantic eyeball-like structures with multiple optic veins" that "levitate effortlessly at walking speeds and silently glide over the suburban areas".
  - The beam "instantly turns any living matter fully absorbed in the light into fine, gray dust"; victims leave piles of gray dust beside their belongings.
  - No weapon has destroyed one; Firesalt does nothing; no hearing, no smell (sight only).
- Lore notes: `docs/design/entity-ai-overhaul/lore-2026-10.md` section 9. Design: `docs/design/entity-ai-overhaul/README.md` section 6.2, `decisions.md` item 6.

## Design decisions
- A bloodshot eyeball with its optic veins trailing behind it: not a sphere of noise. The sclera is a yellowed milky white, reddening toward the back, with red veins painted on the sphere itself (3D, from the back toward the iris), so they run on from face to face.
- A large dark iris (crimson-brown fibres, a faint collarette, a near-black limbus) and a black pupil with a dull ember at its heart. Iris and pupil glow faintly: in the Suburbs' night you see it before it sees you.
- A hot disc sits behind the pupil, shrunk to nothing until the charge brightens the iris (the warning); during the beam it is white-hot and the pupil a point.
- At the back a wet red bulb, from which eight optic veins trail: tapering strands of six segments each, hanging back and down (the further, the steeper), swaying in waves. They stiffen and tremble in the charge.
- The eye turns in its bulb: the eye bone turns on whoever it watches (client side, WatcherEyeController, synced key `backrooms:watcherOn`); the body turns to face them too.

## Proportions (16 px = 1 block)
- Eye 35.2 px across (2.2 blocks), built as the Strider's rhombicuboctahedron of ten boxes (R 17.6). Centre 20 px above the model's feet.
- Iris 19.4 px, hot disc 14 px, pupil 8.9 px (stretched by the animations). Bulb 7.6 x 10 x 10 behind the eye.
- Veins: 6 segments of 8.5 to 10.5 px, 3.4 to 4.2 px thick at the root tapering to about 1 px: about 3.5 blocks long, hanging below the model's feet.
- Hitbox 2.2 x 2.4, eyeHeight 1.25. 63 parts, texture 256 x 1024.

## Palette
Sclera (226,218,198), pink (212,170,160), veins (150,30,38) / (96,18,28). Iris (112,36,30) / (58,16,16), limbus (26,10,10), collarette (214,120,56). Pupil (8,4,6) with ember (150,20,16). Hot disc (255,236,190) to (255,150,70) to (214,50,34). Bulb (150,50,62), strands (164,58,74) to (210,130,140), channel (100,26,44).

## Parts
Body (a bone, nothing drawn; Center point), Eye + EyeX/Y/Z + EyeXZa/b, EyeXYa/b, EyeYZa/b, Iris, IrisHot, Pupil, Bulb, V0_0 to V7_5 (the veins: chains, each segment the child of the one before).

## Animations (30 fps)
float 90 (loop, default: slow bob and roll, eye drifting, veins swaying), idle 120, scan 120 (the eye sweeps +-62 degrees, holding at the ends), charge 60 (2 s, held: pupil 1 to 0.3, hot disc up, eye leans in and rises, veins straighten and tremble), beam 15 (held: iris white-hot, pupil a point, eye thrown back, veins rigid).

## Sounds
watcher-hum (4 s low beating drone, played every few seconds near it), watcher-charge (2 s rising tone with a quickening tremolo), watcher-beam (a crack, a searing hiss over a falling tone, dust crackle). All synthesised in `tools/gen_watcher.py`.
