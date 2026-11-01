"""Level 14, "The Hospital" (experimental): the blocks of its links (docs/design/experimental-levels/LINKS.md, "Level 14,
the Hospital") and the M.E.G. placard, with their textures and shapes. The level's other blocks are tools/gen_14.py's; this
uses its helpers and palette and writes only its own files (textures named link-*).

    l14-exitdoor    a grey steel hospital EMERGENCY EXIT door with a push bar and a green running man lit over it, standing
                    in a wall of Level 0 (lower, upper; the same on every face): threshold "l14-exit", into Level 14
    l14-meddoor     a white sliding door in a steel frame, MEDICAL CENTER and a red cross over it, a lit panel by it, in
                    Level 15's halls: threshold "l14-medical", into Level 14
    l14-futuredoor  the same white door in the old hospital's walls, a cool white light strip round it: threshold
                    "l14-future", to Level 15
    l14-reddoor     a red steel door, EXIT in white on red glowing over it: threshold "l14-red", to Level !
    l14-placard     the M.E.G. placard: LEVEL 14, CLASS 4, SOMETHING HUNTS HERE., DO NOT MEET ITS EYES (four sides)

The doors are two high and alike on all four faces (the faces in the wall are hidden), full collision, never broken
(resistance 99999), dropping nothing. Run from the repo root after gen_14.py:  python tools/gen_14_links.py
(under tools/locked.sh run)
"""
import os

from PIL import Image, ImageDraw

import matlib as M
import gen_14 as G
from gen_14 import B, S, SIDES, ROTATE, METAL, STONE, rect, blend, art, save, shape, write_json, draw_text, cuboid, up2
from modelkit import box, turn, push_bar, kick_plate, lever, DIRS, without

BLOCKS = G.BLOCKS
FULL = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}
WHITE15 = (222, 225, 224)   # Level 15's cool white panels (gen_15.WHITE)
STEEL15 = (206, 211, 216)


# ======================================================================== Textures

def frame_sides(img, colour, w=3, top=False):
    """A door's frame down both edges of a face (and across its top for an upper half), lit on its inner lip."""
    W, H = img.size
    rect(img, 0, 0, w - 1, H - 1, colour)
    rect(img, W - w, 0, W - 1, H - 1, colour)
    if top:
        rect(img, 0, 0, W - 1, w - 1, colour)
    M.emboss_lines(img, xs=(w, W - w - 1), raised=True, strength=0.22)
    if top:
        M.emboss_lines(img, ys=(w,), raised=True, strength=0.22)


def exitdoor_textures():
    """The emergency exit: grey-painted steel, scuffed, a pressed-steel frame a darker grey; the upper half lettered
    EMERGENCY EXIT in red, ALARM WILL SOUND under it; the lower half its hinges and kick plate."""
    paint = (148, 152, 150)
    for part in ("lower", "upper"):
        img = up2(M.painted_metal(seed=14800 + (part == "upper"), base=paint, panel=False, chips=4, under=(96, 92, 88)))
        frame_sides(img, (96, 100, 100), w=5, top=part == "upper")
        if part == "lower":
            rect(img, 8, 50, 55, 61, (176, 180, 178))
            M.bevel(img, (8, 50, 56, 62), strength=0.25)
            for sx, sy in ((10, 52), (53, 52), (10, 59), (53, 59)):
                blend(img, sx, sy, (80, 82, 82), 0.8)
            for y0 in (6, 40):
                rect(img, 5, y0, 7, y0 + 7, (120, 124, 124))
            M.grime(img, 0.14, seed=14802, bias="bottom", color=(70, 66, 58))
            G.scuffs(img, 14803, 6, colour=(90, 92, 90), ys=(44, 48, 52), length=(4, 12), strength=0.4)
        else:
            rect(img, 9, 22, 54, 45, (232, 230, 222))
            M.bevel(img, (9, 22, 55, 46), strength=0.2)
            draw_text(img, (10, 23, 54, 39), "EMERGENCY\nEXIT", (196, 28, 24), 8)
            draw_text(img, (10, 39, 54, 45), "ALARM WILL SOUND", (196, 28, 24), 3, condensed=True)
            rect(img, 5, 5, 7, 12, (120, 124, 124))
        save(img, "link-exit" + part)
    # The running man sign's face and its housing
    img = Image.new("RGBA", (B, 24), (30, 170, 84, 255))
    rect(img, 0, 0, B - 1, 0, (226, 232, 226))
    rect(img, 0, 23, B - 1, 23, (226, 232, 226))

    def man(d, k, W, H):
        g = (238, 255, 242, 255)
        d.rectangle([W * 0.05, H * 0.12, W * 0.24, H * 0.88], outline=g, width=2 * k)
        d.ellipse([W * 0.36, H * 0.05, W * 0.44, H * 0.28], fill=g)
        d.line([(W * 0.39, H * 0.32), (W * 0.35, H * 0.62)], fill=g, width=3 * k)
        d.line([(W * 0.38, H * 0.38), (W * 0.47, H * 0.52)], fill=g, width=2 * k)
        d.line([(W * 0.38, H * 0.38), (W * 0.3, H * 0.44)], fill=g, width=2 * k)
        d.line([(W * 0.35, H * 0.62), (W * 0.44, H * 0.92)], fill=g, width=2 * k)
        d.line([(W * 0.35, H * 0.62), (W * 0.28, H * 0.76), (W * 0.22, H * 0.72)], fill=g, width=2 * k)
        d.polygon([(W * 0.56, H * 0.4), (W * 0.76, H * 0.4), (W * 0.76, H * 0.22), (W * 0.94, H * 0.5), (W * 0.76, H * 0.78),
                   (W * 0.76, H * 0.6), (W * 0.56, H * 0.6)], fill=g)
    art(img, (2, 2, B - 2, 22), man)
    save(img, "link-runningman")
    save(M.brushed_metal(seed=14805, base=(214, 218, 214), direction="h", streak=4, sheen=6), "link-housing")
    save(M.brushed_metal(seed=14806, base=(180, 184, 182), direction="h", streak=5, sheen=8), "link-steel")
    save(M.noise_hv((86, 90, 90), 2, 14807, S, 3, (8, 4)), "link-edge")


def white_door(part, seed, label=None, slit=False):
    """Level 15's kind of door: two white leaves meeting at a seam down the middle in a brushed steel frame, a dark
    reveal round them; the upper half with a slit of dark glass (slit), or a label plate over it (label)."""
    img = up2(M.concrete(seed=seed, base=WHITE15, grain=2, mottle=3, aggregate=0.0, pores=0.003, hue=1.0))
    steel = up2(M.brushed_metal(seed=seed + 1, base=STEEL15, direction="v", streak=6, sheen=8))
    px, sp = img.load(), steel.load()
    top = part == "upper"
    for y in range(B):
        for x in range(B):
            if x < 7 or x > 56 or (top and y < 7):
                px[x, y] = sp[x, y]
    # the reveal between frame and leaves
    for y in range(7 if top else 0, B):
        for x in (7, 8, 55, 56):
            px[x, y] = (40, 44, 50, 255)
    if top:
        rect(img, 7, 7, 56, 8, (40, 44, 50))
    # the seam between the leaves, and their bevelled edges
    rect(img, 31, 9 if top else 0, 32, B - 1, (70, 76, 84))
    M.emboss_lines(img, xs=(30, 33), strength=0.18)
    M.emboss_lines(img, xs=(9, 54), raised=True, strength=0.15)
    if not top:
        # recessed pull grooves either side of the seam, a scuffed foot
        for gx in (25, 36):
            rect(img, gx, 10, gx + 2, 26, (150, 156, 160))
            M.inset(img, (gx, 10, gx + 3, 27), 1, 0.25)
        M.grime(img, 0.1, seed=seed + 2, bias="bottom", color=(140, 140, 132))
    if slit:
        rect(img, 14, 28, 49, 33, (14, 18, 22))
        M.inset(img, (14, 28, 50, 34), 1, 0.3)
        for k in range(6):
            blend(img, 18 + k, 29 + k // 3, (70, 84, 96), 0.5)
    if label:
        rect(img, 10, 11, 53, 33, (40, 44, 50))
        rect(img, 11, 12, 52, 32, (238, 240, 240))
        rect(img, 13, 19, 20, 22, (200, 34, 30))
        rect(img, 15, 17, 18, 24, (200, 34, 30))
        draw_text(img, (21, 13, 52, 31), label, (28, 30, 34), 9, condensed=True)
    return img


def white_door_textures():
    save(white_door("lower", 14810), "link-medlower")
    save(white_door("upper", 14811, label="MEDICAL\nCENTER"), "link-medupper")
    save(white_door("lower", 14812), "link-futurelower")
    save(white_door("upper", 14813, slit=True), "link-futureupper")
    # the lit panel by the medical door: a small screen, a green cross, a row of lamps
    img = Image.new("RGBA", (S, S), (24, 30, 36, 255))
    rect(img, 2, 2, 29, 29, (10, 40, 44))
    rect(img, 12, 6, 19, 21, (80, 230, 160))
    rect(img, 8, 10, 23, 17, (80, 230, 160))
    for x in (6, 12, 18, 24):
        rect(img, x, 24, x + 2, 26, (120, 220, 255) if x != 18 else (255, 90, 80))
    save(img, "link-medpanel")
    # the light strip: a frosted cool white lens
    img = M.noise_hv((236, 246, 255), 1, 14814, S, 2, (8, 4))
    for y in range(S):
        for x in range(S):
            if (x + y) % 4 == 0:
                blend(img, x, y, (210, 226, 240), 0.5)
    save(img, "link-strip")
    save(M.brushed_metal(seed=14815, base=STEEL15, direction="h", streak=6, sheen=8), "link-steel15")


def reddoor_textures():
    """A red steel door, scuffed and chipped to the grey under it; EXIT over it in white on red."""
    red = (164, 30, 26)
    for part in ("lower", "upper"):
        img = up2(M.painted_metal(seed=14820 + (part == "upper"), base=red, panel=False, chips=6, under=(110, 104, 100)))
        frame_sides(img, (112, 22, 20), w=4, top=part == "upper")
        if part == "lower":
            rect(img, 8, 50, 55, 61, (150, 152, 150))
            M.bevel(img, (8, 50, 56, 62), strength=0.25)
            M.grime(img, 0.18, seed=14822, bias="bottom", color=(60, 30, 24))
            G.scuffs(img, 14823, 5, colour=(90, 20, 16), ys=(46, 50), length=(4, 10), strength=0.5)
        else:
            # a small sticker with nothing printed on it, peeling
            rect(img, 24, 30, 39, 38, (226, 222, 210))
            rect(img, 36, 30, 39, 32, (200, 196, 186))
        save(img, "link-red" + part)
    img = Image.new("RGBA", (B, 24), (200, 24, 20, 255))
    rect(img, 0, 0, B - 1, 0, (90, 12, 10))
    rect(img, 0, 23, B - 1, 23, (90, 12, 10))
    draw_text(img, (6, 3, B - 6, 21), "EXIT", (255, 244, 236), 14)
    save(img, "link-redsign")


def placard_texture():
    """The M.E.G. placard (128 x 96, mapped whole onto the plate), as the other levels' (gen_120's)."""
    plate = Image.new("RGBA", (128, 96), (0x2A, 0x30, 0x30, 255))
    d = ImageDraw.Draw(plate)
    d.rectangle([0, 0, 127, 95], outline=(0x8C, 0x94, 0x90))
    d.rectangle([3, 3, 124, 92], outline=(0x58, 0x5F, 0x5C))
    d.rectangle([6, 6, 121, 30], fill=(0xD0, 0x70, 0x1C))
    draw_text(plate, (8, 9, 120, 28), "M.E.G. - LEVEL 14 - CLASS 4", (0x14, 0x10, 0x0C), 9)
    draw_text(plate, (6, 38, 122, 60), "SOMETHING HUNTS HERE.", (0xE8, 0xE4, 0xD4), 10)
    draw_text(plate, (6, 63, 122, 85), "DO NOT MEET ITS EYES", (0xE8, 0xE4, 0xD4), 10)
    for sx, sy in ((10, 88), (117, 88)):
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(0x7A, 0x80, 0x7C))
    save(plate, "link-placard")
    save(M.brushed_metal(seed=14830, base=(70, 76, 76), direction="h", streak=4, sheen=5), "link-placardback")


# ======================================================================== Shapes

def all_faces(els):
    """Elements made for the north face, repeated on the other three (the block has no facing)."""
    out = []
    for k in range(4):
        for e in turn(els, k):
            e = dict(e)
            e["name"] = e["name"] + "NESW"[k]
            out.append(e)
    return out


def leaf(face, edge="link-edge"):
    return box("Leaf", (0, 0, 0), (16, 16, 16), {"side": face, "top": edge, "bottom": edge})


def sign_box(name, tex, housing, y1, y2, glow):
    """A lit sign over a door, proud of its face (the north one, repeated round by all_faces): a housing and the face."""
    els = [box(name + "Housing", (2.5, y1, -1.2), (13.5, y2, 0), housing, faces=("east", "west", "up", "down")),
           box(name + "Face", (2.5, y1, -1.2), (13.5, y2, -1.0), tex, faces=("north",), uv=(0, 0, 16, 16), glow=glow)]
    return els


def exitdoor_shape(part):
    els = [leaf("link-exit" + part)]
    if part == "lower":
        els += all_faces(push_bar("Push", 2.5, 13.5, 14.0, 0, "link-steel", depth=2.0))
    else:
        els += all_faces(sign_box("Sign", "link-runningman", "link-housing", 12.0, 15.6, 230))
    return shape("l14-exitdoor-" + part, els)


def whitedoor_shape(kind, part):
    els = [leaf(f"link-{kind}{part}", "link-steel15")]
    if kind == "med" and part == "lower":
        els += all_faces([box("Panel", (12.6, 11.0, -0.5), (14.6, 14.0, 0), {"north": "link-medpanel", "all": "link-steel15"},
                              faces=("north", "east", "west", "up", "down"), uv=(0, 0, 16, 16))])
        for e in els[1:]:
            if "north" in e["faces"] and e["faces"]["north"]["texture"] == "#link-medpanel":
                e["faces"]["north"]["glow"] = 200
        # turned copies carry the panel's face round under other names: glow them too
        for e in els[1:]:
            for f in e["faces"].values():
                if f["texture"] == "#link-medpanel":
                    f["glow"] = 200
    if kind == "future":
        strips = [box("StripL", (1.0, 0, -0.3), (2.0, 16 if part == "lower" else 15.0, 0), "link-strip", faces=("north", "east", "west"), glow=255),
                  box("StripR", (14.0, 0, -0.3), (15.0, 16 if part == "lower" else 15.0, 0), "link-strip", faces=("north", "east", "west"), glow=255)]
        if part == "upper":
            strips.append(box("StripT", (1.0, 14.0, -0.3), (15.0, 15.0, 0), "link-strip", faces=("north", "up", "down"), glow=255))
            strips[0]["to"][1] = strips[1]["to"][1] = 14.0
            for e in strips[:2]:
                for f in e["faces"].values():
                    f["uv"] = [0, 0, 1, 14]
        els += all_faces(strips)
    return shape(f"l14-{kind}door-{part}", els)


def reddoor_shape(part):
    els = [leaf("link-red" + part)]
    if part == "lower":
        els += all_faces(lever("Lever", 11.5, 15.0, 0, 3.0, "link-steel", side=-1))
    else:
        els += all_faces(sign_box("Sign", "link-redsign", "link-edge", 12.2, 15.6, 140))
    return shape("l14-reddoor-" + part, els)


def placard_shape():
    """A steel plate flush on the wall to the south, its face to the north (as l120-megplacard)."""
    return shape("l14-placard", [
        box("Plate", (0, 4, 15), (16, 16, 16), {"north": "link-placard", "all": "link-placardback"}, faces=("north",), uv=(0, 0, 16, 16)),
        box("Back", (0, 4, 15.01), (16, 16, 16), "link-placardback", faces=("south", "east", "west", "up", "down")),
    ])


# ======================================================================== Block types

def door_block(code, kind, comment, light=None, glow=None):
    shapes = {f"*-{part}": {"base": shp} for part, shp in SHAPES[code].items()}
    data = {"code": code, "variantgroups": [{"code": "part", "states": ["lower", "upper"]}], "shapeByType": shapes,
            "creativeinventory": {"general": ["*-lower"], "backrooms": ["*-lower"]},
            "blockmaterial": "Metal", "drawtype": "json", "collisionbox": FULL, "selectionbox": FULL,
            "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 0,
            "behaviors": [{"name": "BackroomsThreshold", "properties": {"kind": kind}}],
            "resistance": 99999, "drops": [], "sounds": METAL}
    if light:
        data["lightHsvByType"] = light
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


SHAPES = {}


def blocktypes():
    door_block("l14-exitdoor", "l14-exit",
               "Level 14's link: a grey steel hospital EMERGENCY EXIT door with a push bar and a green running man lit over it, standing "
               "in a wall of Level 0 (lower, upper; alike on every face). Used: into Level 14", light={"*-upper": [22, 6, 6]})
    door_block("l14-meddoor", "l14-medical",
               "Level 14's link: a white sliding door in a steel frame, MEDICAL CENTER and a red cross over it, a lit panel by it, in "
               "Level 15's halls (lower, upper; alike on every face). Used: into Level 14", light={"*-lower": [24, 4, 3]})
    door_block("l14-futuredoor", "l14-future",
               "Level 14's link: a rare futuristic white door in the old hospital's walls, a cool white light strip round it (lower, "
               "upper; alike on every face). Used: to Level 15", light={"*-lower": [34, 1, 6], "*-upper": [34, 1, 6]})
    door_block("l14-reddoor", "l14-red",
               "Level 14's link: a rare red steel exit door, EXIT in white on red glowing faintly over it (lower, upper; alike on every "
               "face). Used: to Level !", light={"*-upper": [0, 7, 4]})
    sb = {"x1": 0, "y1": 0.25, "z1": 0.94, "x2": 1, "y2": 1, "z2": 1}
    base = placard_shape()
    write_json(os.path.join(BLOCKS, "l14-placard.json"), {
        "code": "l14-placard", "variantgroups": [{"code": "side", "states": SIDES}],
        "shapeByType": {f"*-{s}": {"base": base, "rotateY": ROTATE[s]} for s in SIDES},
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "collisionbox": None, "selectionboxByType": {f"*-{s}": dict(sb, **({"rotateY": ROTATE[s]} if ROTATE[s] else {})) for s in SIDES},
        "resistance": 1.5, "drops": [], "sounds": METAL},
        "Level 14's M.E.G. placard: LEVEL 14, CLASS 4, SOMETHING HUNTS HERE., DO NOT MEET ITS EYES (flush on the wall behind it, "
        "its face toward its side)")


def main():
    exitdoor_textures()
    white_door_textures()
    reddoor_textures()
    placard_texture()
    SHAPES["l14-exitdoor"] = {p: exitdoor_shape(p) for p in ("lower", "upper")}
    SHAPES["l14-meddoor"] = {p: whitedoor_shape("med", p) for p in ("lower", "upper")}
    SHAPES["l14-futuredoor"] = {p: whitedoor_shape("future", p) for p in ("lower", "upper")}
    SHAPES["l14-reddoor"] = {p: reddoor_shape(p) for p in ("lower", "upper")}
    blocktypes()
    print("Level 14 links: textures in", os.path.relpath(G.TEX, G.ROOT), "; blocktypes in", os.path.relpath(BLOCKS, G.ROOT))


if __name__ == "__main__":
    main()
