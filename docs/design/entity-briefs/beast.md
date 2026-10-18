# The Beast of Level 5 (Entity 18): design brief

## Sources
- Fandom, "Entity 18: The Beast of Level 5" (rewrite by The Bishop in the Blue Dimension, original by Homie Robot; read
  through the MediaWiki API, the page itself answers 402): https://backrooms.fandom.com/wiki/Entity_18 . The fullest and
  best-known account, so the one followed here.
  - "an eldritch sapient creature lurking deep within Level 5"; "the supposed cause or even the embodiment of the
    constant unease and insanity permeating the Terror Hotel".
  - Body: "a chimaeric conglomeration of human, octopus and deathmoth dressed in a furred black suit"; about 6'2"; "a
    head resembling a dark blue octopus, his eyes an otherworldly violet"; two pairs of arms, "the upper set resembling
    mottled blue tentacles", the lower human "albeit having clawed hands with sharpened ungues of what appears to be
    steel"; "pointed, buckled black leather shoes resembling footwear common in the eighteenth century"; "the furred
    outer jacket of his suit appears to actually be a massive pair of moth-wings", unfurled "to extinguish flames or
    blow objects and wanderers away".
  - Camouflage "allowing him to blend in so well with his surroundings that he is practically invisible".
  - Behaviour: "stalking the shadows of his hotel and, on occasion, selecting a victim"; the chosen grow terrified and
    paranoid; then he "will manifest before them in a usually flamboyant and zesty manner (... emerging from a column
    of flame ... or materialising in a violent flash of purple light)" and offers a deal: their soul for what they
    crave (safety, among others). Gentlemanly, keeps his word; the deal is sealed with a handshake; after the allotted
    time he hunts his thrall through the levels, even "safe" ones.
  - Refused, he attacks: transformed "to over 4 metres", "his claws sharpen and elongate into shining blades; the
    tentacles on the bottom of his head undulate furiously; and his purple eyes split into compound orbs like those of
    a moth"; victims "engulfed in flames", tentacles from the ground, the ceiling coming down. "Attacks are mainly fatal".
  - The one known escape: a scribe who stopped running and confronted him "face-to-face in his own home": "surprising
    the eldritch entity so much that he allegedly stood, shocked and unmoving, for several seconds, allowing his
    escaped thrall time to flee"; she regained her soul.
  - "It is believed that the Beast is currently in possession of Level 5's level key." Even brain death would not kill
    him for good.
- Wikidot, "Entity 18 - The Beast of Level 5" (ratscrapz): https://backrooms-wiki.wikidot.com/entity-18 . A short story in
  two voices: the Beast as the hotel's gracious host who would rather be called "the Gentleman" and offers a deal ("a
  few simple favors" to be free of fear, "a man of my word", "Why are you doubting me?"), and a former visitor's warning
  (he watches "until he can see you break", "can smell your fear", "don't listen to his voice", the portraits are
  lies, if you see him out of the corner of your eye it is too late: "Just get out of there"). No physical description.
- Wikidot, Level 5: https://backrooms-wiki.wikidot.com/level-5 . Jazz from turntables and speakers "throughout the halls",
  the Beverly Room, the Boiler Room "very claustrophobic", "faint whispering ... from large smoking furnaces"; Entity 18
  only hinted at ("Why don't you come to my office?").
- Fandom, Level 5 (API wikitext): https://backrooms.fandom.com/wiki/Level_5 . "Whispering incoherently behind them ... a
  little too quiet ... as if the level is holding its breath"; the Addendum: octopus-like gods in the portraits, then "a
  sudden sound ... deep and inhuman, like a bass drum, though it sounded far away", "scraping and clanging ... getting
  louder by the second, as if something were approaching us at extreme speed". The boiler rooms: "the maintenance
  halls"; whispers from the "face-like boilers".
- Where they differ: Wikidot gives no body and no rules, Fandom gives both and agrees with Wikidot's voice (the deal,
  "Why are you doubting me?", the Gentleman). Fandom is followed; Wikidot supplies the corner-of-the-eye sighting.

## Decisions
- An event, like the Mangled's (`src/Entities/BeastSystem.cs`), never put down by the director. Rolled once a second
  in Level 5 outside the safe band: 1/1200 at the edge of the hotel, 1/2000 further out, 1/4000 in the heart when in a
  boiler hall ("deep within": the maintenance halls); a quarter of that elsewhere in the hotel; up to x3 with the
  player's stability gone (he smells fear); x the director's spawn setting; at most once in 36 in-game hours each.
- The warning signs, 50 seconds: Level 5's music stops for that player (client side: `BeastSystem.Hushed` makes
  `AtmosphereSystem.L5` treat the hotel as silent; also while one of his forms is within 40 blocks), a far bass drum
  every 7-12 s, whispers, scraping and clanging closing in, and once a corner-of-the-eye glimpse of the gentleman that
  vanishes when looked at. Leaving Level 5 or reaching a safe place before he comes ends it.
- He comes 4.5-7 blocks in front of the player: flame column and violet flash (particles, a short dynamic violet light
  from `EntityBeast.LightHsv`), a greeting in chat, and the offer (`AiTaskBeast`), walking slowly up with his hand out.
  - Handshake (right-click; only the chosen player, only when not collecting, only with no debt): full health,
    satiety and stability; a debt due in 72 in-game hours (player attribute `backrooms:beastDueHours`). When due, he
    comes with the same dread wherever the debtor is (not the Hub), with no offer. Killed by him: paid. Escaped: due
    again a day later.
  - Held gaze (within 14 degrees, clear line, not sprinting, 5 s in all): "shocked", frozen 8 s, then gone; it frees a
    debtor.
  - Refusal (struck, more than 13 blocks off, out of sight 4 s, or 24 s gone by): "Why are you doubting me?", flame,
    and `beast-unveiled` hunts.
- Unveiled: same shape at 1.4x (2.8 blocks: the hotel's halls are 3 high, not 4 m), compound-eye texture, its own
  animations with the claws stretched into blades and the wings half open. The common hunter task: run 0.047 (a
  sprint is 0.05), 7 damage tier 3 slashing, 1.7 reach, 120 health, own numbers (not the level's danger), so a hunt
  that draws no blood for 20 s is given up and safe places turn him away. Brought down by a player he dissolves after
  3 s and leaves Level 5's Level Key (`backrooms:hub-key-l5`) and 6-10 rusty gears.
- Not built: setting victims alight (cut for balance: two hits already nearly kill), Roth Syndrome over days, the
  reality warping (looping corridors, crushing walls), tentacles from the floor, the camouflage as a visual effect
  (rendered as never being seen until he chooses), moth jelly.

## Model (tools/gen_beast.py, 96 parts, 13 animations)
Pelvis, waist (violet waistcoat), chest (fur lapels, waistcoat, jabot), fur collar; legs with trousers and pointed
buckled shoes; octopus head (face, mantle swept back, cap, tip), violet slit-pupilled eyes (glow), brows; a beard of
eight 4-segment tentacles; two 5-segment tentacle arms from behind the shoulders; human arms with lace cuffs, three
fingers and a thumb each with steel claws; coat tails that are wings (forewing, folded hindwing, ragged tips), fur
outside, moth scales with a violet eye spot inside. Animations: idle, walk, run, attack, hurt, die, offer, shocked,
unveil; fury, stalk, charge, rend for the unveiled form.
