"""Level 0's arched areas: the arch header model and the blocks where the pale walls meet the yellow paper.

- shapes/block/archheader.json: half of a two-block arched opening, its soffit a quarter ellipse stepped one pixel at
  a time from the pier (west, low) to the crown (east, high).
- blocktypes/paperjoin.json: a wall whose four sides each show the yellow chevron paper or the pale paper, so a wall
  between an arched area and a papered one is papered on one side and pale on the other (WorldGenerator picks it from
  Tile.Detail, see WorldLayout.L0FlipBits).

Run from the repo root:  python tools/gen_l0_walls.py
"""
import json
import math
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")

# The opening rises this many pixels into the header block, leaving a band of wall above the crown
RISE = 11


def soffit():
    """(x0, x1, y) runs: from x0 to x1 the header is solid from y up, a quarter ellipse from the pier to the crown."""
    heights = [round(RISE * math.sqrt(max(0.0, 1 - ((16 - (d + 0.5)) / 16) ** 2))) for d in range(16)]
    runs = []
    for d, y in enumerate(heights):
        if runs and runs[-1][2] == y:
            runs[-1][1] = d + 1
        else:
            runs.append([d, d + 1, y])
    return runs


def arch_header():
    elements = []
    runs = soffit()
    for k, (x0, x1, y) in enumerate(runs):
        faces = {
            # The wall runs along x: north and south are its two faces (north is seen mirrored)
            "north": {"texture": "#wall", "uv": [16 - x1, 0, 16 - x0, 16 - y]},
            "south": {"texture": "#wall", "uv": [x0, 0, x1, 16 - y]},
            "down": {"texture": "#wall", "uv": [x0, 0, x1, 16]},
            "up": {"texture": "#wall", "uv": [x0, 0, x1, 16]},
        }
        # The riser up to the next step; the crown meets the other half and the foot meets the pier
        if k < len(runs) - 1:
            faces["east"] = {"texture": "#wall", "uv": [0, 0, 16, 16 - y]}
        elements.append({"name": f"Step{k}", "from": [x0, y, 0], "to": [x1, 16, 16], "faces": faces})
    return {"textureWidth": 16, "textureHeight": 16,
            "textures": {"wall": "backrooms:block/wallpaper/cream-plain"}, "elements": elements}


def paper_join():
    sides = ["north", "east", "south", "west"]
    return {
        "code": "paperjoin",
        "variantgroups": [
            {"code": s, "states": ["chevron", "cream"]} for s in sides
        ] + [{"code": "part", "states": ["upper", "baseboard"]}],
        # A blade strips the paper off every side alike, leaving the wall bare
        "behaviors": [{"name": "BackroomsStrippable", "properties": {"result": "wallpaper-stripped-{part}", "item": "wallpaperstrip"}}],
        "blockmaterial": "Stone",
        "drawtype": "cube",
        "textures": dict(
            {s: {"base": f"block/wallpaper/{{{s}}}-{{part}}", "alternates": [
                {"base": f"block/wallpaper/{{{s}}}-{{part}}"}, {"base": f"block/wallpaper/{{{s}}}-{{part}}-damp"}]} for s in sides},
            up={"base": "block/wallpaper/{north}-upper"}, down={"base": "block/wallpaper/{north}-upper"}),
        "resistance": 2.5,
        "lightAbsorption": 99,
        "sounds": {"walk": "game:walk/stone", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
    }


def write(rel, data):
    path = os.path.join(ASSETS, rel)
    text = json.dumps(data, indent="\t")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    print("wrote", rel)


if __name__ == "__main__":
    write("shapes/block/archheader.json", arch_header())
    write("blocktypes/paperjoin.json", paper_join())
