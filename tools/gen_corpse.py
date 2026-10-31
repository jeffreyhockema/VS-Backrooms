"""The corpse a death leaves (src/Corpse, docs/design/corpse.md): its two entity types, and the shape of its bones.

  corpse        the dead player's own seraph shape, skin and clothes (copied from the player at death, see
                CorpseSystem.AssetsFinalize for the skin parts), lying down with the seraph's own death animation
  corpse-bones  the same thing after a few days: the game's lying human skeleton (block/bone/carcass/humanoid2), moved
                so that it lies about the entity's position (the block shape is laid out inside a block's cube)

Run from the repo root:  python tools/gen_corpse.py
Needs the game's assets (VINTAGE_STORY, else %APPDATA%/Vintagestory).
"""
import json
import math
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
GAME = os.environ.get("VINTAGE_STORY", os.path.join(os.environ.get("APPDATA", ""), "Vintagestory"))
VANILLA = os.path.join(GAME, "assets")

SKELETON = "survival/shapes/block/bone/carcass/humanoid2.json"


def write_json(data, *parts):
    path = os.path.join(ASSETS, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent="\t", ensure_ascii=False) + "\n")
    print("wrote", os.path.relpath(path, ROOT))


# ---------------------------------------------------------------- Shape

def rotate(point, element):
    """A point (in the element's parent's space) turned by the element's own rotations: Z, then Y, then X, about its origin."""
    ox, oy, oz = element.get("rotationOrigin", [0.0, 0.0, 0.0])
    x, y, z = point[0] - ox, point[1] - oy, point[2] - oz
    a = math.radians(element.get("rotationZ", 0.0))
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    a = math.radians(element.get("rotationY", 0.0))
    x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    a = math.radians(element.get("rotationX", 0.0))
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return [x + ox, y + oy, z + oz]


def bounds(elements, root):
    """The box round every element with faces, with only the shape's one turned root applied (the small bones' own turns are left out)."""
    low, high = [1e9] * 3, [-1e9] * 3
    for e in elements:
        if e.get("faces"):
            f, t = e["from"], e["to"]
            for cx in (f[0], t[0]):
                for cy in (f[1], t[1]):
                    for cz in (f[2], t[2]):
                        p = rotate([cx, cy, cz], root)
                        for i in range(3):
                            low[i], high[i] = min(low[i], p[i]), max(high[i], p[i])
        if e.get("children"):
            lo, hi = bounds(e["children"], root)
            for i in range(3):
                low[i], high[i] = min(low[i], lo[i]), max(high[i], hi[i])
    return low, high


def shift(elements, d):
    """Every element moved by d (its box and the point it turns about), so that the whole shape moves."""
    for e in elements:
        for key in ("from", "to", "rotationOrigin"):
            if key in e:
                e[key] = [round(e[key][i] + d[i], 4) for i in range(3)]
        shift(e.get("children", []), d)


def bones_shape():
    with open(os.path.join(VANILLA, *SKELETON.split("/")), encoding="utf-8-sig") as f:
        shape = json.load(f)
    shape.pop("editor", None)
    low, high = bounds(shape["elements"], shape["elements"][0])
    # About the entity's position (the middle of a 16-wide cell, on the floor), whichever way it was laid in its block
    d = [8 - (low[0] + high[0]) / 2, -low[1], 8 - (low[2] + high[2]) / 2]
    shift(shape["elements"], d)
    shape["textures"] = {k: v if ":" in v else "game:" + v for k, v in shape["textures"].items()}
    print("bones: was x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f, moved by %s" % (low[0], high[0], low[1], high[1], low[2], high[2], [round(x, 2) for x in d]))
    write_json(shape, "shapes", "entity", "corpse-bones.json")


# ---------------------------------------------------------------- Entities

def seraph_entity():
    # Modelled on the game's playerbot: a seraph that is not a player (extraskinnable for the skin, seraphinventory for the
    # clothes). The skin parts it names are the player's own, copied at load; the skin and clothes come from the dead player.
    behaviors = [{"code": "extraskinnable"}, {"code": "seraphinventory"}, {"code": "backrooms-corpsecontents"}]
    return {
        "code": "corpse",
        "class": "BackroomsCorpse",
        "tags": ["backrooms-corpse"],
        "hitboxSize": {"x": 1.3, "y": 0.5},
        "eyeHeight": 0.3,
        "client": {
            "renderer": "Shape",
            "pitchStep": False,
            "shape": {"base": "game:entity/humanoid/seraph-faceless"},
            "texture": {"base": "game:entity/humanoid/seraph-naked-hairless"},
            "behaviors": behaviors,
            "animations": [
                {"code": "die", "animation": "die", "blendMode": "Average", "animationSpeed": 1.5},
            ],
        },
        "server": {"behaviors": behaviors},
    }


def bones_entity():
    behaviors = [{"code": "backrooms-corpsecontents"}]
    return {
        "code": "corpse-bones",
        "class": "BackroomsCorpse",
        "tags": ["backrooms-corpse"],
        "hitboxSize": {"x": 1.3, "y": 0.4},
        "eyeHeight": 0.3,
        "client": {
            "renderer": "Shape",
            "pitchStep": False,
            "shape": {"base": "backrooms:entity/corpse-bones"},
            "behaviors": behaviors,
        },
        "server": {"behaviors": behaviors},
    }


def main():
    bones_shape()
    write_json(seraph_entity(), "entities", "corpse.json")
    write_json(bones_entity(), "entities", "corpse-bones.json")


if __name__ == "__main__":
    main()
