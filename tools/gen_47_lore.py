"""Level 47, "The Adderwood": the level's texts besides its blocks' names (read by tools/gen_47.py, which writes the level's
whole block of en.json): its creatures' names, what the Ophion Order says, the Great Adder's coming, the ways in and out.

The Order's boasts follow the lore (Wikidot): "the arcane secrets and miraculous powers their order possesses, including the
ability to travel The Backrooms at will"; "they claim that it's possible to steer or summon [the trail] towards specific
no-clip points. One member even claimed it was possible to reach The Frontrooms using this method, but he was immediately
silenced"; they revere the Great Adder as "a scion or avatar or emanation of a Divine World Snake". Wanderers are told to
"regard any promises of aid or salvation as duplicitous": the lines are tempting on purpose.
"""

LANG = [
    # The creatures (the creature models: tools/gen_47_creatures.py)
    ("item-creature-l47-snake", "Adderwood Snake"),
    ("prefixandcreature-l47-snake", "an Adderwood snake"),
    ("deadcreature-l47-snake", "Killed by an Adderwood snake"),
    ("item-creature-l47-greatadder", "The Great Old Adder"),
    ("prefixandcreature-l47-greatadder", "the Great Old Adder"),
    ("deadcreature-l47-greatadder", "Devoured by the Great Old Adder"),
    ("item-creature-l47-shuck", "Black Shuck"),
    ("prefixandcreature-l47-shuck", "a Black Shuck"),
    ("deadcreature-l47-shuck", "Run down by the Black Shucks"),
    ("item-creature-l47-ophion", "Ophion Acolyte"),
    ("prefixandcreature-l47-ophion", "an acolyte of the Ophion Occult Order"),
    ("deadcreature-l47-ophion", "Killed by the Ophion Occult Order"),
    # The Great Adder
    ("l47-adder-comes", "The birds stop. The whole forest goes quiet, as if it were holding its breath. Somewhere behind you, something enormous is moving through the trees."),
    ("l47-adder-summoned", "The acolyte's mask turns to you, and it says one word you do not know. Somewhere behind you, something enormous is moving through the trees."),
    # The Ophion Order
    ("l47-ophion-name", "Masked acolyte"),
    ("l47-ophion-warn", "This glade is not for you, wanderer. Turn round. Go back to your trail."),
    ("l47-ophion-drive", "You were told."),
    ("l47-ophion-struck", "You lift your hand against the Order, in the Adder's own wood?"),
    ("l47-ophion-preach-1", "You walk the trail as if it were a road. It is a gift, and you do not even know whose."),
    ("l47-ophion-preach-2", "We go where we please, wanderer. Any level. Any door. The World Snake shows us the way through."),
    ("l47-ophion-preach-3", "The trail can be turned. Summoned. Steered to any place where the world is thin. We could show you how."),
    ("l47-ophion-preach-4", "The Great Adder is not an animal. It is a scale of something far larger, that coils under all of this."),
    ("l47-ophion-preach-5", "The black dogs? They will not come near us. They know what we serve."),
    ("l47-ophion-preach-6", "Kneel to the Adder and you will never be lost again. That is a promise. We keep our promises."),
    ("l47-ophion-preach-7", "There is a way home from here, you know. To the real world, the one you came from. One of us has walked it. He-"),
    ("l47-ophion-preach-8", "Come to the glade some day, when you are tired of running. Not today. When we call you."),
    # The ways in and out (src/Thresholds/ThresholdNetwork.L47.cs)
    ("l47-in", "You step into the dark inside the old tree, and the dark is deeper than the tree. You come out of another hollow trunk, into fog, among trees older than any you have seen."),
    ("l47-out10", "Inside the hollow the forest goes quiet, then very far away. You step out of a dead tree into flat grey daylight and the smell of ripe grain."),
    ("l47-out23", "You climb into the green giant's hollow and up, and up, through wood that turns to stone round you. You come out of a trunk in a forest of stone under a roof of leaves."),
]
