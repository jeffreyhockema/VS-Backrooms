"""Level 73, "The Redlands": the words. Called from gen_73.py, which writes them into the level's block of lang/en.json.

The castle's messages (the door, the table, the baths, the light rule), CORAN's name and what he says, and the level's
handbook page (guide-level73-*, registered in src/GuideSystem.cs), in the voice of the released pages
(tools/gen_guide.py) and after the Wikidot page (https://backrooms-wiki.wikidot.com/level-73, by Kitty Rika). The
level's wanderer notes are in tools/gen_notes.py (its Level 73 block).
"""
from gen_guide import to_vtml

CORAN_SAYS = [
    "I hear you, child. Your heart is going too fast. Inside, now.",
    "Eat. There is always enough at the table.",
    "Do not look outside. Whatever you hear at the windows, do not look.",
    "The attic is mine. Leave it be.",
    "I cannot see them. I have never needed to.",
    "Bang on the door. They will let you in. They always let you in.",
    "Someday we will find the way out, all of us together, and I will come with you. Until then you are safe here.",
    "Put out your light. They come to it, and I cannot be everywhere.",
]

CORAN_GREETS = [
    "Welcome home, child.",
    "There you are. I heard you on the stones.",
    "Thirty-seven, and you. Good.",
    "Rest. I will keep the door.",
]

PAGE_TITLE = "Level 73: The Redlands"

PAGE = """
**Level 73, the Redlands**
*"We are safe here. We are loved here."*

**The island**
One island of black-red ground in a dark sea, under a night that never ends. A full moon hangs over it and never moves; now and then thick black cloud covers it and the whole level goes dark. On the island's highest point stands the **Silver Castle**, the only building there is, and the only safe place: you arrive somewhere out on the island, nearly always with the castle in sight. The sea round it has never been crossed, and something lives in it. It is cold (4 °C), and the island drains you a little.

**The one rule**
**Run straight to the castle. Do not look around. Do not stop.** The island is Survival Difficulty 5: Hounds in packs of three to five, Smilers, Death Rats, Deathmoths, Skin-Stealers, Dullers and Clumps, all of them hostile and many of them about at once, and they hunt whoever they find until they die (see [What Lives Here](backrooms-entities)). **Do not carry a light outside the walls**: they come to it from far off. Near the castle, where CORAN hunts, the hordes are thinner; beyond the hill they are not. The stone path under your feet leads up the hill to the gate, and the gate is always open; worn tracks wind in to it from every side.

**The door**
The keep's door is shut, and nothing gets through it. **Bang on it as hard and as fast as you can** ({rightmouse} it four times in a few seconds) and it is opened for you; from inside a single touch opens it. It shuts itself again behind you. Within the castle's walls nothing hostile comes.

**The castle**
Three floors and an attic, gothic, fully furnished and lit. On every floor a guest room at each end with two large curtained beds and a fire of its own; the main hall, the dining hall with its great fireplace, a bathroom and the kitchen on the ground floor; a sitting room, a library and the second bathroom above; the master bedroom and Coran's study on the third. By the main door hangs a piece of needlework: *We are safe here. We are loved here.* The walls, the doors and the windows cannot be broken.
- **The table.** At the long mahogany table in the dining hall a place is set at every seat: a plate of stew and bread and a glass of water. {rightmouse} a place to eat and drink it; it is set again some four hours later. Do not ask what the stew is (the fireplace burns Hound).
- **The baths.** The barrels in the two bathrooms are always full of warm water: {rightmouse} to wash and warm through, or with an [empty bottle](item-backrooms:emptybottle) to fill it with clean water.
- **The curtains.** Red velvet hangs over every window, and behind it the windows are boarded up. Coran says it keeps the Windows away. **Do not look outside.**
- **The paintings** show places in the Frontrooms. None of them lead anywhere.
- **The attic** is chained shut. Coran has declared it off-limits.
- What the castle keeps by is in the store-room off Coran's study.

**Coran**
The castle's keeper, and the reason anyone is alive here: a giant of a man with ram's horns, a black shell over his body and a heart beating in his chest where you can see it, his arms two great golden chains ending in spiked black gauntlets. He is blind (his eyes hang on a cord round his neck), and he hunts by ear. **He will never harm you**, and nothing you do can harm him. He walks the hill round the castle and kills whatever hostile thing he hears there: if you are being chased, run toward him. {rightmouse} him and he will speak to you. Those who live in the castle call themselves his children.

**Not here yet**
The page also names the Windows (which the curtains are for) and Camo Crawlers among the island's hordes, and unidentified things in the sea. None of these are in this version.

**Ways in**
- **The Gloom (Level 9).** Very rarely, a yard or a street of the Suburbs holds a pool of darkness that light does not reach: black ground, and a black murk over it that your torch stops at. Stand in it too long (a minute or two: it warns you, more than once) and you are on the island, somewhere in sight of the castle. One way.
- **Level 6.** Wanderers say the very deepest dark of Lights Out ends the same way, for whoever lingers in it a long time with no light. It is very rare, it takes a long while, and it warns you. One way.
- **Level 14**, says the page. Nobody here has seen that way.

**Ways out**
The page knows of none. But **Coran will lead you out**, once you have slept a night under his roof, if you ask him (sneak and {rightmouse} him). Stay close: he walks you round the walls to a chained door in the outside of the north wall, a door with no courtyard behind it, and opens it on the dark. Through it you come out in the Suburbs (Level 9). One way. He will not come with you: he will not leave his children.
"""

LANG = [
    ("item-creature-l73-coran", "Coran"),
    ("prefixandcreature-l73-coran", "Coran"),
    ("l73-coran-name", "Coran"),
    ("l73-coran-struck", "Save your strength, child. You will need it for the run."),
] + [(f"l73-coran-say-{i}", t) for i, t in enumerate(CORAN_SAYS, 1)] + [(f"l73-coran-greet-{i}", t) for i, t in enumerate(CORAN_GREETS, 1)] + [
    ("l73-light-warning", "Out in the dark, something turns toward your light. DO NOT use an artificial light source."),
    ("l73-door-knock", "Nothing yet. Bang harder: someone inside has to hear you."),
    ("l73-door-opened", "Bolts slide back. The door swings in, and warm light spills out. Quick, inside."),
    ("l73-attic-locked", "Chained and padlocked. CORAN has declared the attic off-limits."),
    ("l73-table-cleared", "Your place has been cleared. It will be set again."),
    ("l73-bath-washed", "The water is warm. The island's red dust comes off you."),
    ("blockhelp-l73-knock", "Bang on the door"),
    ("blockhelp-l73-eat", "Eat and drink"),
    ("blockhelp-l73-wash", "Wash"),
    ("blockhelp-l73-coran", "Speak to him"),
    ("blockhelp-l73-leadout", "Ask him to lead you out"),
    # The ways in and out (docs/design/experimental-levels/LINKS.md; Regions/L73System.Links.cs)
    ("l73-gloom-warn-1", "The dark here does not lift. Your light stops at its edge; it does not reach the ground under your feet."),
    ("l73-gloom-warn-2", "The Gloom is closing round you. It is warm, and very quiet, and somewhere a long way off a heart is beating. Step out of it."),
    ("l73-gloom-warn-3", "You can no longer see the street. Something in the dark has hold of you. Get out of it, now."),
    ("l73-gloom-left", "You step out of the Gloom, and the night seems almost bright."),
    ("l73-arrive-gloom", "The Gloom lets go of you. Red earth under your feet, a full moon overhead, and on the hill a castle. Run for it."),
    ("l73-dark-warn-1", "The dark here is deeper than the rest of it. It feels like a held breath."),
    ("l73-dark-warn-2", "Your eyes have given up. There is no floor in this dark, only the feeling of one. Light something, or move on."),
    ("l73-dark-warn-3", "Far under you, something is beating like a heart. The floor is gone, and wherever this dark lets you out is worse than here."),
    ("l73-dark-left", "The dark draws back a little. Only a little."),
    ("l73-arrive-dark", "You fall out of the dark onto red earth, under a full moon. On the hill stands a castle. Run for it."),
    ("l73-rested", "You slept the night through, safe, for the first time in a long while. Out in the dark chains drag on the stones: Coran keeps the night. If you would go, he is the one to ask."),
    ("l73-coran-lead-notyet", "You have only just come to us, child. Eat at my table, sleep a night under my roof. Then ask me again, if you still wish it."),
    ("l73-coran-lead-1", "You want to go back. I will not keep you. There is a door I know, the way I came back out of the dark myself. Walk with me, close, and do not look at the sea."),
    ("l73-coran-lead-again", "Close behind me, child. I can hear you."),
    ("l73-coran-lead-busy", "I am taking another out. Wait inside; I will come back for you."),
    ("l73-coran-lead-wait", "Stay close. I cannot fight for you if I cannot hear you."),
    ("l73-coran-lead-open", "Go through, and do not stop in the dark. Remember us kindly. If you ever find the way out, come back for the rest of us."),
    ("l73-coran-lead-giveup", "Coran waits a long while, listening for you on the stones, then turns back to his round."),
    ("l73-postern-locked", "A low door in the outside of the wall, black and chained. On the other side of this wall is the courtyard, and no door shows there."),
    ("l73-postern-ask", "Chained. Coran keeps this door: ask him to lead you out (sneak and speak to him)."),
    ("l73-out-arrive", "The dark lets go. Cold air, wet leaves, a dead street lamp: the Suburbs. Behind you there is nothing but a dark yard."),
    ("guide-level73-title", PAGE_TITLE),
    ("guide-level73-text", to_vtml(PAGE)),
]
