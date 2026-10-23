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


# ---------------------------------------------------------------------------------------------------------------------
# Wave two: the finishes and shells (wallpapers, siding, roofs, tile, the city's walls), the barrel's asphalt, and the
# tar. Every output of this section goes through out(): it names the block a recipe makes, and it is the one place to
# redirect them all (to the "built" twins of the blocks, so that what you build is not salvage again).
# ---------------------------------------------------------------------------------------------------------------------
def out(code):
    return code


QUICKLIME = {"type": "item", "code": "game:quicklime"}  # whitewash, grout
CHARCOAL = {"type": "item", "code": "game:charcoal"}  # a printed pattern
GLASS = {"type": "item", "code": "glassshard"}
CLAY_RED = {"type": "item", "code": "game:clay-red"}  # ochre
CLAY_BLUE = {"type": "item", "code": "game:clay-blue"}
SHINGLE = {color: {"type": "item", "code": "game:shingle-burned-" + color} for color in ("gray", "brown", "red")}
TAR = {"type": "item", "code": "game:tarportion", "litres": 1, "consumeLitres": 1}

# Roof covers: the block's name for the colour, and the shingle colour
COVERS = [("grey", "gray"), ("brown", "brown"), ("red", "red")]


def _housing():
    return [
        shaped("PP,PQ", {"P": PLANK, "Q": QUICKLIME}, out("housewall-white-north"), 4),
        shapeless([(block("housewall-white-north"), 4), (CLAY_BLUE, 1)], out("housewall-blue-north"), 4),
        shaped("BB,MM", {"B": BRICK, "M": MORTAR}, out("housewall-brick-north"), 2),
    ]


def _roofs():
    recipes = []
    for cover, color in COVERS:
        recipes.append(shaped("SS,SM", {"S": SHINGLE[color], "M": MORTAR}, out("houseroof-" + cover), 4))
    for cover, color in COVERS:
        recipes.append(shaped("SS,TT", {"S": SHINGLE[color], "T": STICK}, out("pitchroof-%s-none-lower-north" % cover), 2))
        recipes.append(shaped("TT,SS", {"S": SHINGLE[color], "T": STICK}, out("pitchroof-%s-none-upper-north" % cover), 2))
    return recipes


FILES_TWO = {
    # The dotted paper is printed (charcoal rubbed in), the cream paper whitewashed (quicklime); the baseboards as before
    "build-wallpaper-dotted": [
        shapeless([(DRYWALL, 1), (STRIP, 2), (CHARCOAL, 1)], out("wallpaper-dotted-upper")),
        shapeless([(block("wallpaper-dotted-upper"), 1), (STICK, 1)], out("wallpaper-dotted-baseboard")),
    ],
    "build-wallpaper-cream": [
        shapeless([(DRYWALL, 1), (STRIP, 2), (QUICKLIME, 1)], out("wallpaper-cream-upper")),
        shapeless([(block("wallpaper-cream-upper"), 1), (STICK, 1)], out("wallpaper-cream-baseboard")),
    ],
    # The lobby's carpet is the maroon with fibre worked into it (no dye is made here)
    "build-carpet-lobby": [
        shapeless([(block("hotelcarpet-maroon"), 1), (FIBRE, 2)], out("hotelcarpet-lobby")),
    ],
    # The houses: boards limewashed white (a blue wash from blue clay), or brick in mortar; the roof is the game's
    # fired shingles (a flat cap, or the two courses of a slope); blocks with a side are made facing north
    "build-house": _housing() + _roofs(),
    # The farm: weathered boards, red from red clay (4 boards and a lump); the porch's boards and step
    "build-farm": [
        shaped("PP,PS", {"P": PLANK, "S": STICK}, out("barnwall-grey"), 4),
        shapeless([(block("barnwall-grey"), 4), (CLAY_RED, 1)], out("barnwall-red"), 4),
        shaped("PPP,SSS", {"P": PLANK, "S": STICK}, out("porchdeck-deck"), 4),
        shapeless([(block("porchdeck-deck"), 1), (PLANK, 1)], out("porchdeck-step"), 2),
    ],
    # Pool and subway tile: fired clay tile with quicklime for grout (mortar for the subway's)
    "build-tile": [
        shaped("TT,TQ", {"T": TILE, "Q": QUICKLIME}, out("pooltile-plain"), 4),
        shaped("PP", {"P": block("pooltile-plain")}, out("pooltile-coping"), 2),
        shaped("TT,MM", {"T": TILE, "M": MORTAR}, out("subwaywall-tile"), 2),
    ],
    # The Endless City: concrete faced with plaster, glass, brick or limestone (lime); not the lit or powered ones
    "build-city": [
        shapeless([(block("concrete"), 1), (PLASTER, 1)], out("cityfacade-concrete-wall-north"), 2),
        shapeless([(block("concrete"), 1), (GLASS, 3)], out("cityfacade-glass-wall-north"), 2),
        shapeless([(block("l3wall-brick"), 1), (PLASTER, 1)], out("cityfacade-brick-wall-north"), 2),
        shapeless([(block("concrete"), 1), (QUICKLIME, 1)], out("cityfacade-stone-wall-north"), 2),
        shapeless([(PLASTER, 2), (RUBBLE, 1)], out("cityplaster-plain"), 2),
    ],
}

# Barrel recipes (recipes/barrel/): a litre of the tar from Levels 7 and 8 (taken in a bucket) and rubble make asphalt
BARREL_FILES = {
    "build-asphalt": [
        {
            "code": "asphalt",
            "sealHours": 2,
            "ingredients": [dict(TAR), {"type": "item", "code": "rubble", "quantity": 4}],
            "output": {"type": "block", "code": out("asphalt-plain"), "stackSize": 4},
        },
    ],
}


def main():
    count = 0
    for name, recipes in {**FILES, **FILES_TWO}.items():
        with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(recipes, indent="\t", ensure_ascii=False) + "\n")
        count += len(recipes)
    barrel_dir = os.path.join(ROOT, "assets", "backrooms", "recipes", "barrel")
    os.makedirs(barrel_dir, exist_ok=True)
    for name, recipes in BARREL_FILES.items():
        with open(os.path.join(barrel_dir, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(recipes, indent="\t", ensure_ascii=False) + "\n")
    print(f"gen_building: {count} grid recipes in {len(FILES) + len(FILES_TWO)} files, "
          f"{sum(len(r) for r in BARREL_FILES.values())} barrel")


if __name__ == "__main__":
    main()
