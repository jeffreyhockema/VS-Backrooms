"""Assets for the ward anchors (docs/design/progression/plan.md 3.2). Run on its own: python tools/gen_wards.py

Three worn items in the neck slot, `backrooms:anchor-copper`, `-bronze` and `-iron`: a small metal ring with a gear on it. They are
vanilla clothing (the Wearable behaviour, no durability) on vanilla's rusty gear amulet model, with the gear and chain textures
replaced. The tier logic is src/Reality/Wards.cs; the recipes chain (each anchor is made from the one before):

- copper anchor = 2 copper ingots + 1 temporal gear + 1 candle
- bronze anchor = copper anchor + 2 bronze ingots (any bronze) + 1 temporal gear
- iron anchor   = bronze anchor + 2 iron ingots + 1 temporal gear

Writes the item type, the textures, the three recipes and the words (en, es-419, es-es).
"""
import json
import os
import random
import re

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
NL = "\n"
TAB = "\t"

# metal: (name, base colour, lit, dark)
METALS = {
    "copper": ((0xB8, 0x73, 0x33), (0xE0, 0x9A, 0x58), (0x7A, 0x45, 0x1C)),
    "bronze": ((0x9C, 0x7A, 0x3C), (0xC8, 0xA2, 0x5C), (0x5E, 0x46, 0x20)),
    "iron": ((0x7C, 0x82, 0x8A), (0xB0, 0xB6, 0xBE), (0x44, 0x48, 0x4E)),
}

NAMES = {
    "en": {"copper": "Copper Anchor", "bronze": "Bronze Anchor", "iron": "Iron Anchor"},
    "es-419": {"copper": "Ancla de cobre", "bronze": "Ancla de bronce", "iron": "Ancla de hierro"},
    "es-es": {"copper": "Ancla de cobre", "bronze": "Ancla de bronce", "iron": "Ancla de hierro"},
}

DESCRIPTIONS = {
    "en": {
        "copper": "A copper ring with a little temporal gear, worn at the neck. It keeps a thread back to you: stability holds in Levels 3, 4 and 5.",
        "bronze": "A bronze ring with a temporal gear, worn at the neck. The thread is thicker: stability holds as deep as Levels 6, 7, 8, 37 and 94.",
        "iron": "An iron ring with a temporal gear, worn at the neck. The thread is strong enough for everything beyond: Levels 9 and deeper.",
    },
    "es-419": {
        "copper": "Un aro de cobre con un pequeño engranaje temporal, que se lleva al cuello. Guarda un hilo de vuelta hacia ti: la estabilidad aguanta en los Niveles 3, 4 y 5.",
        "bronze": "Un aro de bronce con un engranaje temporal, que se lleva al cuello. El hilo es más grueso: la estabilidad aguanta hasta los Niveles 6, 7, 8, 37 y 94.",
        "iron": "Un aro de hierro con un engranaje temporal, que se lleva al cuello. El hilo aguanta todo lo que hay más allá: del Nivel 9 en adelante.",
    },
    "es-es": {
        "copper": "Un aro de cobre con un pequeño engranaje temporal, que se lleva al cuello. Guarda un hilo de vuelta hacia ti: la estabilidad aguanta en los Niveles 3, 4 y 5.",
        "bronze": "Un aro de bronce con un engranaje temporal, que se lleva al cuello. El hilo es más grueso: la estabilidad aguanta hasta los Niveles 6, 7, 8, 37 y 94.",
        "iron": "Un aro de hierro con un engranaje temporal, que se lleva al cuello. El hilo aguanta todo lo que hay más allá: del Nivel 9 en adelante.",
    },
}

ZERO_LINE = {
    "en": "You lose your grip on the place. When you come to, the walls are the wrong colour.",
    "es-419": "Pierdes el control del lugar. Cuando vuelves en ti, las paredes son del color equivocado.",
    "es-es": "Pierdes el control del lugar. Cuando vuelves en ti, las paredes son del color equivocado.",
}


def write_json(data, *rel, comment=None):
    path = os.path.join(ASSETS, *rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False) + NL
    if comment:
        text = "// " + comment + NL + text
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


def gear_texture(metal, base, lit, dark):
    """The amulet's gear, 16 x 16. The model samples its top-left corner, so that is solid metal; the rest shows the thing itself:
    a ring with a gear on it."""
    img = Image.new("RGBA", (16, 16), base + (255,))
    d = ImageDraw.Draw(img)
    rng = random.Random(sum(map(ord, metal)))
    for y in range(16):
        for x in range(16):
            if x >= 4 or y >= 4:
                img.putpixel((x, y), shade(base, rng.uniform(0.9, 1.08)))
    # The ring (right half) and its gear
    cx, cy = 10, 8
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], outline=shade(dark, 1.0), width=1)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], outline=shade(lit, 1.0), width=1)
    for tx, ty in ((cx, cy - 3), (cx, cy + 3), (cx - 3, cy), (cx + 3, cy), (cx - 2, cy - 2), (cx + 2, cy - 2), (cx - 2, cy + 2), (cx + 2, cy + 2)):
        img.putpixel((tx, ty), shade(lit, 1.1))
    d.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=shade(dark, 0.8))
    return img


def chain_texture(base, lit, dark):
    """The chain, 8 x 4: links of two tones."""
    img = Image.new("RGBA", (8, 4), base + (255,))
    for x in range(8):
        img.putpixel((x, 0), shade(lit, 1.0))
        img.putpixel((x, 3), shade(dark, 1.0))
        if x % 2 == 0:
            img.putpixel((x, 1), shade(dark, 1.2))
            img.putpixel((x, 2), shade(lit, 0.9))
    return img


def textures():
    for metal, (base, lit, dark) in METALS.items():
        folder = os.path.join(ASSETS, "textures", "item", "anchor")
        os.makedirs(folder, exist_ok=True)
        gear_texture(metal, base, lit, dark).save(os.path.join(folder, f"gear-{metal}.png"))
        chain_texture(base, lit, dark).save(os.path.join(folder, f"chain-{metal}.png"))


def item():
    neck = {"translation": {"x": -0.6, "y": -2.1, "z": -0.7}, "rotation": {"x": -21, "y": -180, "z": 25},
            "origin": {"x": 0.5, "y": 1.4, "z": 0.5}, "scale": 0.71}
    data = {
        "code": "anchor",
        "variantgroups": [{"code": "metal", "states": list(METALS)}],
        "maxstacksize": 1,
        "storageFlags": 128,
        "behaviors": [{"name": "Wearable"}],
        "shape": {"base": "survival:entity/humanoid/seraph/clothing/neck/gear-amulet-rusty"},
        "texturesByType": {
            f"*-{metal}": {
                "seraph": {"base": "survival:block/transparent"},
                "rusty-iron": {"base": f"backrooms:item/anchor/gear-{metal}"},
                "irontarnished": {"base": f"backrooms:item/anchor/chain-{metal}"},
            } for metal in METALS
        },
        "attributes": {"clothescategory": "neck", "wearableAttachment": True, "warmth": 0, "displaycaseable": True},
        "creativeinventory": {"general": ["*"], "items": ["*"], "clothing": ["*"]},
        "renderAlphaTest": 0.25,
        "tpHandTransform": neck,
        "guiTransform": {"rotation": {"x": 174, "y": -128, "z": 6}, "origin": {"x": 0.45, "y": 1.43, "z": 0.54}, "scale": 3.5},
        "groundTransform": {"translation": {"x": 0, "y": -0.05, "z": 0}, "rotation": {"x": 0, "y": 0, "z": -90},
                            "origin": {"x": 0.5, "y": 1.5, "z": 0.5}, "scale": 3.06},
    }
    write_json(data, "itemtypes", "ward", "anchor.json",
               comment="Generated by tools/gen_wards.py. The ward anchors: worn in the neck slot, no durability. Tier logic in src/Reality/Wards.cs.")


def recipes():
    gear = {"type": "item", "code": "game:gear-temporal"}
    write_json([{
        "ingredientPattern": "CG,CL",
        "ingredients": {"C": {"type": "item", "code": "game:ingot-copper"}, "G": gear, "L": {"type": "item", "code": "game:candle"}},
        "width": 2, "height": 2,
        "output": {"type": "item", "code": "backrooms:anchor-copper"},
    }], "recipes", "grid", "anchor-copper.json")
    write_json([{
        "ingredientPattern": "BA,BG",
        "ingredients": {"B": {"type": "item", "code": "game:ingot-{metal}", "name": "metal"},
                        "A": {"type": "item", "code": "backrooms:anchor-copper"}, "G": gear},
        "allowedVariants": {"metal": ["tinbronze", "bismuthbronze", "blackbronze"]},
        "width": 2, "height": 2,
        "output": {"type": "item", "code": "backrooms:anchor-bronze"},
    }], "recipes", "grid", "anchor-bronze.json")
    write_json([{
        "ingredientPattern": "IA,IG",
        "ingredients": {"I": {"type": "item", "code": "game:ingot-iron"},
                        "A": {"type": "item", "code": "backrooms:anchor-bronze"}, "G": gear},
        "width": 2, "height": 2,
        "output": {"type": "item", "code": "backrooms:anchor-iron"},
    }], "recipes", "grid", "anchor-iron.json")


def merge_lang(lang):
    """Adds the words to lang/<lang>.json without disturbing its layout: existing keys updated in place, new ones appended."""
    words = {"zero-blackout": ZERO_LINE[lang]}
    for metal in METALS:
        words[f"item-anchor-{metal}"] = NAMES[lang][metal]
        words[f"itemdesc-anchor-{metal}"] = DESCRIPTIONS[lang][metal]
    path = os.path.join(ASSETS, "lang", lang + ".json")
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    bom = text.startswith("﻿")
    text = text.lstrip("﻿")
    crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")
    new_lines = []
    for key, value in words.items():
        line = TAB + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + TAB + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: line + m.group(1), text, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + NL + NL + ("," + NL).join(new_lines) + NL + "}" + NL
    json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.M))
    if crlf:
        text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(("﻿" if bom else "") + text)


def main():
    textures()
    item()
    recipes()
    for lang in ("en", "es-419", "es-es"):
        merge_lang(lang)
    print("gen_wards: 3 anchors, 3 recipes, 3 languages")


if __name__ == "__main__":
    main()
