"""Level 3999, "The Neon Paradise" (level 19): every asset, from docs/new-levels/3999-plan.md section 6 as the user's
direction of 2026-10-09 trims it (no List, no glass-door ending, no Frontrooms car park; the arcade-mall, 3999.1 and
the theme-based resources stay). Run from the repo root, through the asset lock:

    bash tools/locked.sh run python tools/gen_3999.py [tex] [blocks] [entity] [sounds] [lang]

(no arguments: everything). Writes textures (block/3999/, item/3999/, entity/3999/), shapes (block/3999/,
entity/3999/), block types (blocktypes/3999/), item types (itemtypes/3999/), the Arcade Attendant
(entities/3999/attendant.json), grid recipes (recipes/grid/l3999-*.json), sounds (sounds/ambient/3999/,
sounds/effect/3999/) and the level's lang keys (merged into lang/en.json in place after levelname-19; nothing else
in that file is touched). Ends with a check that every texture, shape and sound named resolves and every drop,
prize and ingredient is a real block or item; it exits non-zero if anything is missing.

Modules: gen_3999_kit (helpers, lang, check), gen_3999_tex and gen_3999_tex_arcade (textures), gen_3999_blocks (the
building), gen_3999_arcade (the machines and prizes), gen_3999_items (items, the neon lamp, recipes),
gen_3999_attendant (the entity), gen_3999_sounds.

Block classes the code has not registered yet are left out of the block types (gen_3999_kit.with_class); run this
again once L3999System's classes exist and they are written in.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gen_3999_kit as K  # noqa: E402


def lang():
    K.LANG.update({
        "level-19": "Level 3999: The Neon Paradise",
        "levelhint-19": "Here, you are protected.",
        "levelname-19": "Level 3999",
        "level-1901": "Level 3999.1: The Neon Blackout",
        "levelhint-1901": "The lights went out here long ago. Walk toward the colour.",
        "level-1902": "Level 3999: The Neon Natatorium",
        "levelhint-1902": "Warm violet water. It smells of the sea.",
        "levelname-3999.1": "Level 3999.1",
        "l3999-arrive-lobby": "You come in through a revolving door, into music.",
        "l3999-arrive-natatorium": "You come up into warm violet water. It smells of the sea.",
        "l3999-arrive-staff": "The STAFF ONLY door swings shut behind you. Somewhere ahead, music.",
        "l3999-glitchwall": "The wall gives like static, and the city is gone.",
        "l3999-revolving-out": "The revolving door turns, and you step out into fog, wheat and the smell of rain.",
        "l3999-trueend": "The screen flickers on. A program nobody started is running: TRUEEND.EXE. The room fills with neon and music.",
        "l3999-cabinet-taken": "The screen fills your eyes, and the game lets you in.",
        "l3999-rusted": "You lean on the machine, and fall through it into the dark.",
        "l3999-drain": "The drain pulls you down, and down, into white tile.",
        "l3999-elevator-ride": "A screen in the corner plays a public notice about noclipping, too quiet to hear.",
        "l3999-staff-locked": "STAFF ONLY. It is locked.",
        "l3999-cabinet-played": "You've played this one today.",
        "l3999-cabinet-cap": "The machines seem to think you've had enough for today.",
        "l3999-cabinet-win": "{0} tickets.",
        "l3999-cabinet-jackpot": "JACKPOT! {0} tickets.",
        "l3999-cabinet-lose": "GAME OVER.",
        "l3999-cabinet-plush": "The claw closes on something soft, and holds on.",
        "l3999-prize-need": "You need at least 5 tickets.",
        "l3999-prize-got": "The attendant hands you your prize.",
        "l3999-prize-tiers": "Prizes: 5, 15, 40 and 200 tickets.",
        "l3999-stall-need": "A meal costs 6 tickets.",
        "l3999-stall-got": "The attendant slides a tray across the counter.",
        "l3999-vending-need": "The machine only takes Almond Water.",
        "l3999-directory": "Food court: {0}, about {1} paces. Lobby: {2}, about {3}.",
        "l3999-attendant-1": "\"Welcome to Paradise.\"",
        "l3999-attendant-2": "\"Please take your time.\"",
        "l3999-attendant-3": "\"Please enjoy the games.\"",
        "l3999-attendant-4": "\"We hope your stay is restful.\"",
        "l3999-attendant-5": "\"The food court is open.\"",
        "l3999-attendant-6": "\"There is nowhere you need to be.\"",
        "l3999-attendant-7": "\"Many guests choose to stay.\"",
        "l3999-attendant-8": "\"Please refrain.\"",
        "l3999-attendant-point": "The attendant points, palm up. \"The {0} is that way.\"",
        "l3999-place-foodcourt": "food court", "l3999-place-lobby": "lobby",
        "l3999-generator-on": "You throw the lever. Far off, the beacon on the cap turns green.",
        "l3999-generator-done": "The lever is already up. Someone has been this way.",
        "l3999-blackout-near": "The neon flickers here, as if it is tired.",
        "waypoint-l3999-foodcourt": "A food court (from a mall directory)",
        "waypoint-l3999-lobby": "A lobby (from a mall directory)",
    })


def main():
    only = set(sys.argv[1:])
    everything = not only
    os.chdir(K.ROOT)
    if everything or "tex" in only:
        import gen_3999_tex
        import gen_3999_tex_arcade
        gen_3999_tex.generate()
        gen_3999_tex_arcade.generate()
    if everything or "blocks" in only:
        import gen_3999_blocks
        import gen_3999_arcade
        import gen_3999_items
        gen_3999_blocks.generate()
        gen_3999_arcade.generate()
        gen_3999_items.items()
        gen_3999_items.trueend_terminal()
    entity = os.path.join(K.ASSETS, "entities", "3999", "attendant.json")
    if everything or "entity" in only:
        import gen_3999_attendant
        entity = gen_3999_attendant.generate()
        K.SHAPES.append("entity/3999/attendant")
    if everything or "sounds" in only:
        import gen_3999_sounds
        gen_3999_sounds.generate()
    lang()
    if everything or "lang" in only or "blocks" in only:
        K.merge_lang()
    print(f"3999: {len(K.CODES)} block types, {K.COUNT['variants']} variants, {len(K.SHAPES)} shapes, {len(K.ITEMS)} item types")
    ok = K.check([entity] if os.path.exists(entity) else [])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
