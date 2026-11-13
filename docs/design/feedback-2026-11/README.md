# Player-feedback round, 2026-11 (0.700.0-pre.10)

The mod page's comments of 3 to 10 November 2026, reviewed on 13 November. Everything here ships in the 0.700 branch
(`experimental-levels`) only. The new-world parts take **layout version 16** on this branch (15 is its food round, main's 14 is
the 0.611 review), so main's next layout bump is **17**. Built in four packages (`exp/fb-late`, `exp/fb-small`, `exp/fb-armour`,
`exp/fb-props`) and merged together for pre.10.

## What players said, and what the code showed

- **"The late game is punishing" (Hounds in Levels 8 and 9).** At Normal, spawns 5.5 (the dial-in's old High), a Hound pack
  reached a player in Levels 8 and 9 about every 45 s to 2 min, against 3 to 25 min in Levels 1 to 5. A full cap still let one
  Hound through (`max(1, cap - present)`).
- **"I can't find the way to the city".** Level 10's noclip wall was in about one barn in nine (layout 12 on), a typical search of
  5.6 km, and the notes still said "a little under half".
- **"No way back from the Suburbs".** The Suburbs door you arrive beside from a city rowhouse was a plain locked door with no
  threshold (every world since layout 9); the pry bar just deleted it.
- **"Carpet armour and bags are useless".** Gambeson, sewn from Level 0's carpet fibre, beat sewn leather and bronze lamellar, and
  three wanderer lists sold it. Pleather turned only about a fifth of a blow.
- **Smaller:** butter was only edible in meals; no borax anywhere; vanilla drinks gave no water; Facelings shoved for no visible
  reason; nothing dropped rot for a farm; the props were decoration only.

## Decisions (the user's, 2026-11-13)

1. **Hounds in Levels 8 and 9:** their share of what comes is halved (Level 9 1.0 to 0.5, Level 8 0.5 to 0.25); one pack at a time
   per player or party, then a quiet spell of 3 to 5 minutes at Normal (scaled by the spawn setting and party size); a second pack
   only rarely (5 %), in Level 8's worst off-road ground and Level 9's threshold band and dens. A full cap now sends nothing.
2. **Barns:** one in five has the wall in new worlds; the wall shows (orange seams, a faint glow at night, the city's hum within
   about 30 blocks); the notes search farther; the stale wording is fixed.
3. **City rowhouses:** a door that leads to Level 9 is the Suburbs' red door with a lamp behind its glass (every world); from layout
   16 one in four leads there and the rest are the city's own locked front door. The way back is fixed in every world, and the pry
   bar refuses a door that leads somewhere.
4. **Armour is a trade-off, not a must.** Metal is loud: chain, lamellar, brigandine and scale are heard 40 % farther as you run,
   plate twice as far, and both clank as you walk (sneaking halves it); cloth, carpet and leather are silent.
5. **The carpet ladder:** twine costs 18 carpet fibre; crouching with a blade cuts a whole carpet square and leaves bare floor;
   carpet armour (squares, fibre, twine) stops what a leather jerkin does (0.4 / 0.25, tier 1); bedrolls take squares; the carpet
   bag holds 4 and (the user, later the same day) is 4 squares + 2 fibres, no twine, so four bags cost about 20 cuts, not
   about 46; gambeson (linen) comes next. Wanderers no longer sell gambeson.
6. **Pleather is retired.** Its codes stay registered and hidden; every pleather stack in an old world is remapped once at load
   (`config/remaps.json`, the game's own remapper): pleather to carpet squares, each pleather piece to the same carpet piece.
   Chairs, sofas and car seats give cloth instead.
7. **Food and needs:** butter is out of iceboxes and Kitty's fridge (more cheese, Almond Milk); flour and salt stay with a handbook
   line. Vanilla drinks fill the water bar per litre (water and juice 600 of 1500, milk 500, cider/wine/mead 300, spirits 50,
   vinegar -200). Torn supply boxes and emptied crates drop rot about 1 in 6.
8. **Borax:** washing machines drop it about 15 % of the time (every world); Level 8 holds more borax ore in new worlds (layout 16).
9. **Facelings** keep the noise shove but stare at you for a second first; the handbook explains it, and that Level 3's half-faced
   Evolved attack.
10. **Working props** (every world, no worldgen): fire alarms ring 25 s and set off the sprinklers within 12 blocks (fires and torches
    go out, Deathmoths react); steam valves scald a corridor for 5 s (about 10 damage); breakers really put a section's lights out
    until a new `fuse` (or a day) restores them; car alarms, radios, record players and a new wind-up alarm clock are lures.
11. **Not now:** loneliness hallucinations.

## Changelog, 0.700.0-pre.10

- Hounds in Levels 8 and 9 come about half as often, one pack at a time, with a quiet spell after each.
- The way back from the Suburbs to the city works again, in every world; the pry bar no longer destroys a working door.
- City rowhouse doors that lead to the Suburbs are marked by a red door and a lamp; in new worlds only a quarter lead there.
- One Level 10 barn in five has the way to the city in new worlds, and you can see, and at night hear, which.
- Carpet: twine costs 18 fibre; crouch to cut whole carpet squares; new carpet armour; bedrolls from squares; a 4-slot carpet bag.
- Pleather is gone; any you have becomes carpet squares and carpet armour. Seats give cloth.
- Metal armour is loud. Wanderers no longer sell gambeson.
- Vanilla drinks fill the water bar. Butter is replaced by cheese and Almond Milk. Borax from washers and in Level 8. Rot from
  torn boxes.
- Facelings stare before they shove.
- Fire alarms and sprinklers, steam valves, breakers and fuses, car alarms, radios and alarm clocks all work.

## After pre.10

- The carpet bag is 4 carpet squares + 2 carpet fibres (it was 5 fibres + a twine, 23 fibres a bag). The tutorial's bag
  steps follow: cut 4 squares, cut 2 fibres, craft the bag (its twine step is gone).

## Known gaps

- Spanish strings for the new text are not written.
- Restart resets the props' cooldowns (in memory); tripped breakers persist.
- A converted pleather piece keeps its remaining uses, not its share (full pleather shows as 175/250 carpet armour).
