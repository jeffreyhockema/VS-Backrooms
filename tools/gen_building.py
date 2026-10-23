"""Recipes for building with the Backrooms: the blocks a player can make from the building's scraps and the game's
own materials (docs/DEVELOPING.md, "Building with the Backrooms"). Run on its own: python tools/gen_building.py

The rule: only what a Vintage Story hand could plausibly make. Drywall is plaster on sticks; wallpaper is paper or
the strips cut from other walls pasted to it; carpet is felted fibre; ceiling tile is plaster and paper pulp; concrete
is rubble in lime mortar; brick, tile and cinder block are the game's own bricks, tiles and rubble in mortar; panelling
and floorboards are planks. Nothing powered, nothing that gives light, nothing that holds a level together is here
(fluorescent fixtures, vending machines, thresholds, doors). Prices are set so a room takes real salvage: a wallpaper
strip comes from stripping a wall (one a cut, two with a shiv or scraper), a lump of rubble from half a wall.

One file per family under assets/backrooms/recipes/grid/build-*.json. Two recipes of one output must not share a
shape and ingredients with another's: shapeless ones are told apart by their ingredients, shaped ones by their grid.
"""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "recipes", "grid")

PLASTER = {"type": "block", "code": "game:plaster-plain"}
STICK = {"type": "item", "code": "game:stick"}
PLANK = {"type": "item", "code": "game:plank-*"}
NAILS = {"type": "item", "code": "game:metalnailsandstrips-iron"}
MORTAR = {"type": "item", "code": "game:mortar"}
CLOTH = {"type": "item", "code": "game:cloth-plain"}
PARCHMENT = {"type": "item", "code": "game:paper-parchment"}
TWINE = {"type": "item", "code": "game:flaxtwine"}
FIBRE = {"type": "item", "code": "carpetfibre"}
STRIP = {"type": "item", "code": "wallpaperstrip"}
RUBBLE = {"type": "item", "code": "rubble"}
BRICK = {"type": "item", "code": "game:burnedbrick-*", "skipVariants": ["fire", "clinker"]}
TILE = {"type": "item", "code": "game:claytile-fired-plain-*"}


def block(code):
    return {"type": "block", "code": code}


def shaped(pattern, ingredients, out, qty=1):
    rows = pattern.split(",")
    return {
        "ingredientPattern": pattern,
        "ingredients": ingredients,
        "width": len(rows[0]),
        "height": len(rows),
        "output": {"type": "block", "code": out, "quantity": qty},
    }


def shapeless(ingredients, out, qty=1):
    """ingredients: a list of (ingredient, count)."""
    letters = "ABCDEFG"
    ing, pattern = {}, []
    for i, (item, count) in enumerate(ingredients):
        spec = dict(item)
        if count > 1:
            spec["quantity"] = count
        ing[letters[i]] = spec
        pattern.append(letters[i])
    return {
        "ingredientPattern": ",".join(pattern),
        "ingredients": ing,
        "width": 1,
        "height": len(pattern),
        "shapeless": True,
        "output": {"type": "block", "code": out, "quantity": qty},
    }


DRYWALL = block("wallpaper-stripped-upper")

FILES = {
    # Level 0 and 4: the drywall under it all (2 plaster and 2 sticks make 4), and the paper on it
    "build-drywall": [
        shaped("PP,SS", {"P": PLASTER, "S": STICK}, "wallpaper-stripped-upper", 4),
        shaped("PS,PS", {"P": PLASTER, "S": STICK}, "officewall", 4),
    ],
    # Level 0's yellow chevron: bare drywall and two cut strips; the baseboard is the wall block and a stick
    "build-wallpaper-chevron": [
        shapeless([(DRYWALL, 1), (STRIP, 2)], "wallpaper-chevron-upper"),
        shapeless([(block("wallpaper-chevron-upper"), 1), (STICK, 1)], "wallpaper-chevron-baseboard"),
    ],
    # Manila: a sheet of parchment on drywall
    "build-wallpaper-manila": [
        shapeless([(DRYWALL, 1), (PARCHMENT, 1)], "wallpaper-manila-upper"),
        shapeless([(block("wallpaper-manila-upper"), 1), (STICK, 1)], "wallpaper-manila-baseboard"),
    ],
    # The arched areas' cream stucco: plaster on drywall, no paper
    "build-wallpaper-stucco": [
        shapeless([(DRYWALL, 1), (PLASTER, 1)], "wallpaper-stucco-upper", 2),
        shapeless([(block("wallpaper-stucco-upper"), 1), (STICK, 1)], "wallpaper-stucco-baseboard"),
    ],
    # Carpets: felted fibre, or fibre and cloth (a block of carpet is five or six fibres)
    "build-carpet": [
        shaped("FTF,FTF", {"F": FIBRE, "T": TWINE}, "carpet-normal", 2),
        shaped("FCF,FCF", {"F": FIBRE, "C": CLOTH}, "officecarpet-plain", 2),
        shaped("FFF,CCC", {"F": FIBRE, "C": CLOTH}, "hotelcarpet-maroon", 2),
        shaped("FCF,CFC", {"F": FIBRE, "C": CLOTH}, "hotelcarpet-damask", 2),
    ],
    # Ceiling tile: plaster and paper pulp (here, two cut strips) pressed into a board
    "build-ceiling": [
        shaped("SPS", {"S": STRIP, "P": PLASTER}, "ceilingtile", 4),
        shaped("S,P,S", {"S": STRIP, "P": PLASTER}, "officeceiling", 4),
    ],
    # The hotel's panelling and floor: planks and sticks
    "build-hotel": [
        shaped("PSP,PSP", {"P": PLANK, "S": STICK}, "hotelwall-panel", 4),
        shapeless([(block("hotelwall-panel"), 1), (STICK, 1)], "hotelwall-wainscot"),
        shapeless([(block("hotelwall-panel"), 1), (PLANK, 1)], "hotelwall-frieze"),
        shaped("PPP,PNP", {"P": PLANK, "N": NAILS}, "hotelwood", 4),
    ],
    # Concrete is lime concrete: rubble bound with mortar (a poor cousin of the real thing, and it sets); the slab,
    # wall and ceiling forms are cast from it
    "build-concrete": [
        shaped("RR,RM", {"R": RUBBLE, "M": MORTAR}, "concrete", 2),
        shaped("CC", {"C": block("concrete")}, "concretefloor-plain", 2),
        shaped("C,C", {"C": block("concrete")}, "concreteceiling", 2),
        shaped("C", {"C": block("concrete")}, "concretewall-plain", 1),
        shapeless([(block("concrete"), 1), (RUBBLE, 1)], "sidewalk-plain", 2),
    ],
    # Level 3's walls: the game's own brick and tile, and rubble for cinder block, in mortar; the house's floors
    "build-masonry": [
        shaped("BM,MB", {"B": BRICK, "M": MORTAR}, "l3wall-brick", 2),
        shaped("TM,MT", {"T": TILE, "M": MORTAR}, "l3wall-glazed", 2),
        shaped("RM,MR", {"R": RUBBLE, "M": MORTAR}, "l3wall-cinder", 2),
        shaped("TT,TM", {"T": TILE, "M": MORTAR}, "housefloor-tile", 4),
        shaped("PNP,PPP", {"P": PLANK, "N": NAILS}, "housefloor-wood", 4),
    ],
}


def main():
    count = 0
    for name, recipes in FILES.items():
        with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(recipes, indent="\t", ensure_ascii=False) + "\n")
        count += len(recipes)
    print(f"gen_building: {count} recipes in {len(FILES)} files")


if __name__ == "__main__":
    main()
