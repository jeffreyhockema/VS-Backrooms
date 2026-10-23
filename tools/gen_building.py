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
import fnmatch
import itertools
import json
import os
import re

import json5

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "recipes", "grid")

BUILT = "built-"
BOM = "﻿"

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


OUTPUTS = []


def out(code):
    """The code a recipe outputs for a block of the world's code: its player-made twin. Every output is noted, and
    the twins are made from the notes (twin_states), so a new recipe needs nothing more."""
    OUTPUTS.append(code)
    return BUILT + code


def block(code):
    """One of the player's own blocks (see the built-* twins below), never the world's."""
    return {"type": "block", "code": BUILT + code}


def shaped(pattern, ingredients, result, qty=1):
    rows = pattern.split(",")
    return {
        "ingredientPattern": pattern,
        "ingredients": ingredients,
        "width": len(rows[0]),
        "height": len(rows),
        "output": {"type": "block", "code": out(result), "quantity": qty},
    }


def shapeless(ingredients, result, qty=1):
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
        "output": {"type": "block", "code": out(result), "quantity": qty},
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


# ---- The twins ----
#
# The recipes output "built-<code>", a twin of the block the world generator uses: the same look, sounds, light and
# boxes, but it gives itself back when broken (no breakdown: Breakdown.KindOf leaves a block with the backroomsBuilt
# attribute as it is). A twin is made for each variant a recipe outputs, and for the ones a cut leaves behind.

BLOCKTYPES = os.path.join(ROOT, "assets", "backrooms", "blocktypes")
LANG = os.path.join(ROOT, "assets", "backrooms", "lang")

# the original block type of each family (relative to blocktypes/), by its code
FAMILIES = {
    "wallpaper": "wallpaper", "officewall": "level4/officewall", "carpet": "carpet", "officecarpet": "level4/officecarpet",
    "hotelcarpet": "level5/hotelcarpet", "ceilingtile": "ceilingtile", "officeceiling": "level4/officeceiling",
    "hotelwall": "level5/hotelwall", "hotelwood": "level5/hotelwood", "concrete": "concrete",
    "concretefloor": "level1/concretefloor", "concreteceiling": "level1/concreteceiling", "concretewall": "level1/concretewall",
    "sidewalk": "detail/sidewalk", "l3wall": "level3/l3wall", "housefloor": "detail/housefloor",
}
# what a blade leaves behind (BackroomsStrippable), which the player can cut too
CUT_RESULTS = ["wallpaper-stripped-baseboard", "carpet-threadbare"]
# (material, tool tier, resistance) the twin breaks as, where the original's own is not it (Breakdown sets the original's
# at load): drywall under an axe or a hand, rock-hard things a copper pick; the rest keep their material and resistance
BREAKS = {
    "wallpaper": ("Wood", 0, 2.5), "officewall": ("Wood", 0, 2.5), "ceilingtile": ("Wood", 0, 1), "officeceiling": ("Wood", 0, 1),
    "concrete": ("Stone", 2, None), "concretefloor": ("Stone", 2, None), "concreteceiling": ("Stone", 2, None),
    "concretewall": ("Stone", 2, None), "sidewalk": ("Stone", 2, None), "l3wall": ("Stone", 2, None),
}


def family_of(code):
    best = max((f for f in FAMILIES if code == f or code.startswith(f + "-")), key=len)
    return best, [p for p in code[len(best):].split("-") if p]


def twin_states():
    """{family: [the states of each variant group]} for every output of the recipes, and what a cut leaves."""
    codes = set(OUTPUTS)
    codes.update(CUT_RESULTS)
    states = {}
    for code in sorted(codes):
        fam, parts = family_of(code)
        groups = states.setdefault(fam, [])
        while len(groups) < len(parts):
            groups.append([])
        for i, part in enumerate(parts):
            if part not in groups[i]:
                groups[i].append(part)
    return states


def twin(fam, groups):
    with open(os.path.join(BLOCKTYPES, FAMILIES[fam] + ".json"), encoding="utf-8") as f:
        src = json5.load(f)
    turned = [g["code"] for g in src.get("variantgroups", []) if g["code"] in ("side", "facing")]
    assert not any(g["code"] == "axis" for g in src.get("variantgroups", [])), fam + " has an axis; not supported yet"
    out ={"code": BUILT + fam}
    variants = []
    for g, keep in zip(src.get("variantgroups", []), groups):
        assert all(k in g["states"] for k in keep), (fam, keep)
        if g["code"] in turned:
            keep = g["states"]  # all four ways, for the behaviour to choose from
        variants.append({"code": g["code"], "states": [s for s in g["states"] if s in keep]})
    if variants:
        out["variantgroups"] = variants
    for key, value in src.items():
        if key not in ("drops", "creativeinventory", "code", "variantgroups"):
            out[key] = value
    material, tier, resistance = BREAKS.get(fam, (None, 0, None))
    if material:
        out["blockmaterial"] = material
    if resistance is not None:
        out["resistance"] = resistance
    out.pop("requiredMiningTier", None)
    if tier:
        out["requiredMiningTier"] = tier
    # A cut leaves the twin of the bare block
    for b in out.get("behaviors", []):
        props = b.get("properties", {})
        if "result" in props:
            props["result"] = BUILT + props["result"]
    drop = BUILT + fam + "".join("-{" + g["code"] + "}" for g in variants)
    out["drops"] = [{"type": "block", "code": drop, "quantity": {"avg": 1, "var": 0}}]
    out["creativeinventory"] = {"construction": ["*-north" if turned else "*"]}
    if turned:
        # Set down facing the player, and carried as the north one (our behaviour, not the game's: see BlockCodes.cs)
        assert not any(b["name"] == "BackroomsHorizontalOrientable" for b in out.get("behaviors", [])), fam
        out["behaviors"] = [*out.get("behaviors", []), {"name": "BackroomsHorizontalOrientable", "properties": {"dropBlockFace": "north"}}]
    out["attributes"] = {**out.get("attributes", {}), "backroomsBuilt": True}
    return out


def lookup(lang, key):
    """The game's lookup in a lang file: the exact key, else the most specific wildcard."""
    if key in lang:
        return lang[key]
    hits = [k for k in lang if "*" in k and fnmatch.fnmatchcase(key, k)]
    return lang[max(hits, key=lambda k: len(k.replace("*", "")))] if hits else None


def merge_lang(names):
    """Adds {key: value} to each lang file without disturbing its layout: existing keys updated, new ones appended."""
    for code, entries in names.items():
        path = os.path.join(LANG, code + ".json")
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        bom = text.startswith(BOM)
        text = text.lstrip(BOM)
        new_lines = []
        for key, value in entries.items():
            line = "\t" + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
            pattern = re.compile("^\t" + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
            if pattern.search(text):
                text = pattern.sub(lambda m: line + m.group(1), text, count=1)
            else:
                new_lines.append(line)
        if new_lines:
            body = text.rstrip().rpartition("}")[0].rstrip()
            if not body.endswith(",") and not body.endswith("{"):
                body += ","
            text = body + "\n\n" + ",\n".join(new_lines) + "\n}\n"
        json5.loads(text)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write((BOM if bom else "") + text)


def twins():
    outdir = os.path.join(BLOCKTYPES, "built")
    os.makedirs(outdir, exist_ok=True)
    langs = {}
    for code in ("en", "es-419", "es-es"):
        with open(os.path.join(LANG, code + ".json"), encoding="utf-8-sig") as f:
            langs[code] = json5.load(f)
    adds = {code: {} for code in langs}
    count = 0
    for fam, groups in twin_states().items():
        data = twin(fam, groups)
        with open(os.path.join(outdir, BUILT + fam + ".json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, indent="\t", ensure_ascii=False) + "\n")
        for combo in itertools.product(*[g["states"] for g in data.get("variantgroups", [])]):
            original = "-".join([fam, *combo])
            for code, lang in langs.items():
                value = lookup(lang, "block-" + original)
                if value is not None:
                    adds[code]["block-" + BUILT + original] = value
            count += 1
    merge_lang(adds)
    return count


def main():
    count = 0
    for name, recipes in FILES.items():
        with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(recipes, indent="\t", ensure_ascii=False) + "\n")
        count += len(recipes)
    print(f"gen_building: {count} recipes in {len(FILES)} files, {twins()} built twins")


if __name__ == "__main__":
    main()
