"""Level 73, "The Redlands": the words. Called from gen_73.py, which writes them into the level's block of lang/en.json.

The castle's messages (the door, the table, the baths, the light rule), CORAN's name and what he says, in the voice
of the released pages (tools/gen_guide.py) and after the Wikidot page (https://backrooms-wiki.wikidot.com/level-73,
by Kitty Rika). The level's handbook page is tools/gen_guide.py's (LEVELS row 21, Coran's ENTITIES row), its wanderer
notes tools/gen_notes.py's (its Level 73 block).
"""

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
]
