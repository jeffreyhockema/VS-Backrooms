"""Level 0's arched areas: the arch header model and the blocks where the pale walls meet the yellow paper; and the
troffer's shape.

- shapes/block/archheader.json: half of a two-block arched opening, its soffit a quarter ellipse stepped one pixel at
  a time from the pier (west, low) to the crown (east, high).
- blocktypes/paperjoin.json: a wall whose four sides each show the yellow chevron paper or the pale paper, so a wall
  between an arched area and a papered one is papered on one side and pale on the other (WorldGenerator picks it from
  Tile.Detail, see WorldLayout.L0FlipBits).
- troffer() (graphics pass B3, not written): the troffer as a housing whose frame stands one pixel proud of the lens.
  Tried and withdrawn: as a json block the lit panels lost the cube's glow and the rooms went dark in the review
  world. Kept for a later try with the light emission checked first.

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
    # The soffit and the risers (B3): plain painted plaster, not the printed paper, so the steps read as one curve
    for el in elements:
        for f in ("down", "east", "up"):
            if f in el["faces"]:
                el["faces"][f]["texture"] = "#soffit"
    return {"textureWidth": 16, "textureHeight": 16,
            "textures": {"wall": "backrooms:block/wallpaper/cream-plain", "soffit": "backrooms:block/wallpaper/cream-soffit"},
            "elements": elements}


def troffer(glow=0):
    """A lay-in troffer seen from below: the housing (its underside the lens) with a frame 1.5 units wide (the T-bar
    rail and the housing's bevelled frame of the texture) standing 0.5 units below it, so the lens is recessed and its
    four inner walls show as a dark step. Faces on the block's boundary are culled against the ceiling round it.
    A shape's faces do not take the blocktype's vertexFlags glow (a cube's do), so the lit states get a copy of the
    shape with `glow` on every face (the blocktype picks it with shapeByType)."""
    k, d = 1.5, 0.5  # frame width (3 texture px: rail and frame), recess depth (1 px)
    def f(uv):
        face = {"texture": "#troffer", "uv": uv}
        if glow:
            face["glow"] = glow
        return face
    inner_n = [k, k - d, 16 - k, k]  # the inner walls show the dark gap painted round the lens (gen_textures.troffer)
    els = [{"name": "Housing", "from": [0, d, 0], "to": [16, 16, 16],
            "faces": {"down": f([0, 0, 16, 16]), "up": f([0, 0, 16, 16]), "north": f([0, 0, 16, 16 - d]),
                      "south": f([0, 0, 16, 16 - d]), "east": f([0, 0, 16, 16 - d]), "west": f([0, 0, 16, 16 - d])}},
           {"name": "FrameN", "from": [0, 0, 0], "to": [16, d, k],
            "faces": {"down": f([0, 0, 16, k]), "north": f([0, 16 - d, 16, 16]), "south": f(inner_n),
                      "east": f([0, 16 - d, k, 16]), "west": f([0, 16 - d, k, 16])}},
           {"name": "FrameS", "from": [0, 0, 16 - k], "to": [16, d, 16],
            "faces": {"down": f([0, 16 - k, 16, 16]), "south": f([0, 16 - d, 16, 16]), "north": f(inner_n),
                      "east": f([16 - k, 16 - d, 16, 16]), "west": f([16 - k, 16 - d, 16, 16])}},
           {"name": "FrameW", "from": [0, 0, k], "to": [k, d, 16 - k],
            "faces": {"down": f([0, k, k, 16 - k]), "west": f([k, 16 - d, 16 - k, 16]), "east": f(inner_n)}},
           {"name": "FrameE", "from": [16 - k, 0, k], "to": [16, d, 16 - k],
            "faces": {"down": f([16 - k, k, 16, 16 - k]), "east": f([k, 16 - d, 16 - k, 16]), "west": f(inner_n)}}]
    return {"textureWidth": 16, "textureHeight": 16, "textures": {"troffer": "backrooms:block/fluorescentlight-on"},
            "elements": els}


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
                {"base": f"block/wallpaper/{{{s}}}-{{part}}-2"}, {"base": f"block/wallpaper/{{{s}}}-{{part}}-damp"}]} for s in sides},
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
    # troffer() is not written (B3): as a shape, the lit panels lost the cube's glow and, in the review world, the
    # rooms round them went dark; the troffer stays a cube with its frame and recess painted (gen_textures.troffer).
    write("blocktypes/paperjoin.json", paper_join())
