"""Generates the 3D block models (shapes) for pipes, light fixtures and props.

Models are built from boxes in block space (0-16 per axis); helpers mirror and rotate boxes so that, for
example, wall pipes can stick out of all four faces of a wall block. Run from the repo root:

    python tools/gen_shapes.py
"""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "shapes", "block")

DIRS = ("north", "east", "south", "west", "up", "down")


def box(name, frm, to, tex, glow=0, faces=DIRS):
    """A box with UVs taken from its own size, so textures keep a consistent scale."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    w, h, d = abs(x2 - x1), abs(y2 - y1), abs(z2 - z1)

    def uv(a, b):
        a, b = max(a, 0.5), max(b, 0.5)
        return [0, 0, min(16, a), min(16, b)]

    sizes = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}
    out = {}
    for f in faces:
        face = {"texture": "#" + tex, "uv": uv(*sizes[f])}
        if glow:
            face["glow"] = glow
        out[f] = face
    return {"name": name, "from": [x1, y1, z1], "to": [x2, y2, z2], "faces": out}


def rot(b, times):
    """Rotates a box 90 degrees clockwise (seen from above) around the block centre, `times` times."""
    b = json.loads(json.dumps(b))
    for _ in range(times % 4):
        (x1, y1, z1), (x2, y2, z2) = b["from"], b["to"]
        nx1, nz1 = 16 - z2, x1
        nx2, nz2 = 16 - z1, x2
        b["from"], b["to"] = [nx1, y1, nz1], [nx2, y2, nz2]
        f = b["faces"]
        b["faces"] = {k: v for k, v in {
            "east": f.get("north"), "south": f.get("east"), "west": f.get("south"), "north": f.get("west"),
            "up": f.get("up"), "down": f.get("down"),
        }.items() if v is not None}
    return b


def all_sides(boxes):
    """Copies boxes that stick out of the north face onto all four faces."""
    out = []
    for i in range(4):
        out += [dict(rot(b, i), name=f"{b['name']}{i}") for b in boxes]
    return out


def save(name, textures, elements):
    os.makedirs(OUT, exist_ok=True)
    shape = {"textureWidth": 16, "textureHeight": 16, "textures": textures, "elements": elements}
    with open(os.path.join(OUT, name + ".json"), "w") as f:
        json.dump(shape, f, indent=1)


CUBE = lambda tex: box("Cube", (0, 0, 0), (16, 16, 16), tex)

PIPE_TEX = {
    "rust": "backrooms:block/level2/pipe-rust",
    "lagging": "backrooms:block/level2/pipe-lagging",
    "red": "backrooms:block/level2/pipe-red",
    "metal": "backrooms:block/props/metal",
    "dark": "backrooms:block/props/metal-dark",
}


# ---------------- Level 2 pipe bundles (in the top block of a tunnel, along X) ----------------

def bundle_x():
    return [
        box("Lagged", (0, 10, 1), (16, 15, 6), "lagging", faces=("north", "south", "up", "down")),
        box("Rusty", (0, 11, 10), (16, 14, 13), "rust", faces=("north", "south", "up", "down")),
        box("FireLine", (0, 13.5, 13.5), (16, 15.5, 15.5), "red", faces=("north", "south", "up", "down")),
        box("Strap", (7.5, 15, 0.5), (8.5, 16, 15.5), "metal"),
        box("Hanger1", (7.5, 9.5, 0.5), (8.5, 15, 1), "metal"),
        box("Hanger2", (7.5, 10.5, 13), (8.5, 14, 13.5), "metal"),
    ]


def bundle_z():
    return [dict(rot(b, 1), name=b["name"] + "Z") for b in bundle_x()]


def fixture_x(tube_tex):
    return [
        box("Housing", (1, 14, 6.5), (15, 16, 9.5), "metal"),
        box("Tube", (1, 13.3, 7), (15, 14, 9), tube_tex, glow=0 if tube_tex == "tubeoff" else 255, faces=("north", "south", "down", "east", "west")),
    ]


# Horizontal pipes bolted to a wall, sticking out a few pixels into the tunnel
WALL_PIPES = [
    box("PipeA", (0, 9, -3), (16, 13, 0), "rust", faces=("north", "up", "down")),
    box("PipeB", (0, 3, -2.5), (16, 6.5, 0), "lagging", faces=("north", "up", "down")),
    box("Bracket", (7, 2, -3.5), (9, 14, 0), "metal", faces=("north", "east", "west", "up", "down")),
]


def hub_pipes():
    """Both bundles crossing at the same height, with a junction box where they meet."""
    return bundle_x() + bundle_z() + [
        box("JunctionBox", (4, 8, 4), (12, 16, 12), "dark"),
        box("Lid", (4.5, 7.5, 4.5), (11.5, 8, 11.5), "metal"),
    ]


def fixture_hub(tube_tex):
    """A fixture hanging from the junction box."""
    return [
        box("Housing", (2, 6, 6.5), (14, 7.5, 9.5), "metal"),
        box("Tube", (2, 5.3, 7), (14, 6, 9), tube_tex, glow=255 if tube_tex != "tubeoff" else 0, faces=("north", "south", "down", "east", "west")),
    ]


def level2():
    save("pipes-run", PIPE_TEX, bundle_x())
    save("pipes-hub", PIPE_TEX, hub_pipes())

    for state, tex in (("lit", "tube"), ("off", "tubeoff")):
        textures = dict(PIPE_TEX, tube="backrooms:block/props/tube-white", tubeoff="backrooms:block/props/tube-off")
        save(f"tunnellight-bundle-{state}", textures, bundle_x() + fixture_x(tex))
        save(f"tunnellight-plain-{state}", textures, fixture_x(tex))
        save(f"tunnellight-hub-{state}", textures, hub_pipes() + fixture_hub(tex))
    textures = dict(PIPE_TEX, tube="backrooms:block/props/tube-warm")
    save("tunnellight-bundle-warm", textures, bundle_x() + fixture_x("tube"))
    save("tunnellight-plain-warm", textures, fixture_x("tube"))
    save("tunnellight-hub-warm", textures, hub_pipes() + fixture_hub("tube"))

    wall = {"wall": "backrooms:block/level2/tunnelwall-plain", **PIPE_TEX,
            "valve": "backrooms:block/props/valve", "panel": "backrooms:block/props/cabinet-front"}
    # Horizontal pipes bolted to the wall, sticking out a few pixels into the tunnel
    save("tunnelwall-pipes", wall, [CUBE("wall")] + all_sides(WALL_PIPES))
    # A vertical riser from floor to ceiling, and where it crosses the horizontal wall pipes
    riser = [
        box("Riser", (6, 0, -4), (10, 16, 0), "rust", faces=("north", "east", "west")),
        box("Clamp", (5.5, 7, -4.5), (10.5, 8.5, 0), "metal", faces=("north", "east", "west", "up", "down")),
    ]
    save("tunnelwall-riser", wall, [CUBE("wall")] + all_sides(riser))
    save("tunnelwall-riserjoint", wall, [CUBE("wall")] + all_sides(riser + WALL_PIPES))
    # A valve wheel on a short stem
    save("tunnelwall-valve", wall, [CUBE("wall")] + all_sides([
        box("Stem", (7.5, 7.5, -3), (8.5, 8.5, 0), "metal", faces=("north", "east", "west", "up", "down")),
        box("RimTop", (5, 10.5, -4), (11, 11.5, -3), "valve"),
        box("RimBottom", (5, 4.5, -4), (11, 5.5, -3), "valve"),
        box("RimLeft", (4.5, 5, -4), (5.5, 11, -3), "valve"),
        box("RimRight", (10.5, 5, -4), (11.5, 11, -3), "valve"),
        box("Spoke", (7.5, 5, -3.8), (8.5, 11, -3.2), "valve"),
        box("SpokeH", (5, 7.5, -3.8), (11, 8.5, -3.2), "valve"),
    ]))

    # Machine cabinet, front panel facing north, back against the wall to the south
    save("machinecabinet", {"body": "backrooms:block/props/metal-dark", "front": "backrooms:block/props/cabinet-front",
                            "metal": "backrooms:block/props/metal", "rust": PIPE_TEX["rust"]}, [
        box("Body", (1, 0, 4), (15, 15, 16), "body"),
        box("Front", (1.5, 1, 3.5), (14.5, 14, 4), "front", faces=("north",)),
        box("Gauge1", (3, 10, 2.8), (6, 13, 3.5), "metal"),
        box("Gauge2", (10, 10, 2.8), (13, 13, 3.5), "metal"),
        box("Handle", (11, 5, 2.8), (12, 8, 3.5), "metal"),
        box("Pipe", (11, 15, 11), (14, 16, 14), "rust"),
    ])


# ---------------- Level 1 fixtures and props ----------------

def level1():
    tubes = {"metal": "backrooms:block/props/metal", "chain": "backrooms:block/props/metal-dark",
             "tube": "backrooms:block/props/tube-white", "tubeoff": "backrooms:block/props/tube-off"}
    for state, tex in (("lit", "tube"), ("off", "tubeoff")):
        save(f"hanginglight-{state}", tubes, [
            box("Chain1", (3, 10, 7.75), (3.5, 16, 8.25), "chain"),
            box("Chain2", (12.5, 10, 7.75), (13, 16, 8.25), "chain"),
            box("Housing", (0.5, 8.5, 5.5), (15.5, 10, 10.5), "metal"),
            box("Tube1", (1, 7.7, 6.2), (15, 8.5, 7.6), tex, glow=255 if state == "lit" else 0),
            box("Tube2", (1, 7.7, 8.4), (15, 8.5, 9.8), tex, glow=255 if state == "lit" else 0),
        ])
    bulbs = {"chain": "backrooms:block/props/metal-dark", "socket": "backrooms:block/props/metal",
             "bulb": "backrooms:block/props/tube-warm", "bulboff": "backrooms:block/props/tube-off"}
    for state, tex in (("lit", "bulb"), ("off", "bulboff")):
        save(f"hangingbulb-{state}", bulbs, [
            box("Cord", (7.75, 8, 7.75), (8.25, 16, 8.25), "chain"),
            box("Socket", (7, 6.5, 7), (9, 8, 9), "socket"),
            box("Bulb", (6.5, 3.5, 6.5), (9.5, 6.5, 9.5), tex, glow=255 if state == "lit" else 0),
        ])

    pillar = {"pillar": "backrooms:block/level1/concretepillar-plain", "metal": "backrooms:block/props/metal",
              "tube": "backrooms:block/props/tube-white"}
    save("pillarlight", pillar, [CUBE("pillar")] + all_sides([
        box("Housing", (6, 0.5, -1.5), (10, 15.5, 0), "metal", faces=("north", "east", "west", "up", "down")),
        box("Tube", (7, 1, -2.2), (9, 15, -1.5), "tube", glow=255, faces=("north", "east", "west", "up", "down")),
    ]))

    save("concretewall-damaged", {"wall": "backrooms:block/level1/concretewall-damaged", "rust": PIPE_TEX["rust"]},
         [CUBE("wall")] + all_sides([
             box("Rebar1", (4, 6, -4), (5, 7, 0), "rust"),
             box("Rebar2", (10, 9, -3), (11, 10, 0), "rust"),
             box("Rebar3", (12, 3, -2), (13, 4, 0), "rust"),
         ]))

    save("conduit", {"conduit": "backrooms:block/props/conduit", "metal": "backrooms:block/props/metal"}, [
        box("Conduit1", (0, 14.5, 4), (16, 15.5, 5), "conduit", faces=("north", "south", "down")),
        box("Conduit2", (0, 14.5, 6), (16, 15.5, 7), "conduit", faces=("north", "south", "down")),
        box("Clip", (7.5, 14, 3.5), (8.5, 16, 7.5), "metal"),
    ])

    # Metal shelving with boxes, open side facing north
    shelf = [
        box("Post1", (0.5, 0, 0.5), (1.5, 16, 1.5), "metal"),
        box("Post2", (14.5, 0, 0.5), (15.5, 16, 1.5), "metal"),
        box("Post3", (0.5, 0, 14.5), (1.5, 16, 15.5), "metal"),
        box("Post4", (14.5, 0, 14.5), (15.5, 16, 15.5), "metal"),
    ]
    for i, y in enumerate((1, 8, 15)):
        shelf.append(box(f"Shelf{i}", (0.5, y, 0.5), (15.5, y + 0.6, 15.5), "metal"))
    shelf += [
        box("BoxA", (2, 1.6, 3), (8, 6.6, 13), "cardboard"),
        box("BoxB", (9, 1.6, 5), (14, 5.6, 13), "cardboard"),
        box("BoxC", (3, 8.6, 4), (10, 12.6, 14), "cardboard"),
    ]
    save("metalshelf", {"metal": "backrooms:block/props/metal", "cardboard": "backrooms:block/supplybox-side"}, shelf)

    # Stair climbing toward the north
    save("concretestairs", {"concrete": "backrooms:block/level1/concretefloor-plain"}, [
        box("Lower", (0, 0, 0), (16, 8, 16), "concrete"),
        box("Upper", (0, 8, 0), (16, 16, 8), "concrete"),
    ])


def parking():
    save("wheelstop", {"stop": "backrooms:block/level1/wheelstop"}, [
        box("Stop", (0, 0, 6), (16, 2.5, 10), "stop"),
    ])

    # A boxy abandoned car, 2 blocks wide and 4 long, nose to the north, drawn from its corner block
    for colour in ("red", "blue", "white", "black"):
        textures = {"body": f"backrooms:block/level1/car-{colour}", "glass": "backrooms:block/level1/car-glass",
                    "tyre": "backrooms:block/props/metal-dark", "metal": "backrooms:block/props/metal",
                    "lamp": "backrooms:block/props/tube-white", "tail": "backrooms:block/props/valve"}
        save(f"car-{colour}", textures, [
            box("Body", (1, 2.5, 1), (31, 11, 63), "body"),
            box("Cabin", (3, 11, 17), (29, 20, 45), "body", faces=("up",)),
            box("CabinPillars", (3, 11, 17), (29, 20, 45), "glass", faces=("north", "south", "east", "west")),
            box("Roof", (3.5, 19.5, 17.5), (28.5, 20.5, 44.5), "body"),
            box("BumperFront", (1, 3, 0), (31, 7, 1), "metal"),
            box("BumperRear", (1, 3, 63), (31, 7, 64), "metal"),
            box("LampLeft", (3, 7.5, 0.6), (8, 9.5, 1), "lamp", glow=60),
            box("LampRight", (24, 7.5, 0.6), (29, 9.5, 1), "lamp", glow=60),
            box("TailLeft", (3, 7.5, 63), (8, 9.5, 63.4), "tail"),
            box("TailRight", (24, 7.5, 63), (29, 9.5, 63.4), "tail"),
            box("WheelFL", (0, 0, 8), (3, 7, 16), "tyre"),
            box("WheelFR", (29, 0, 8), (32, 7, 16), "tyre"),
            box("WheelRL", (0, 0, 48), (3, 7, 56), "tyre"),
            box("WheelRR", (29, 0, 48), (32, 7, 56), "tyre"),
        ])


def oriented(name, textures, elements):
    """Props that face a direction are modelled facing north; block variants rotate them."""
    save(name, textures, elements)


def level3():
    cables = {"cable": "backrooms:block/level3/cable", "metal": "backrooms:block/props/metal",
              "tube": "backrooms:block/props/tube-warm", "tubeoff": "backrooms:block/props/tube-off"}

    def cable_x():
        out = []
        for i, (y, z, r) in enumerate(((12.5, 2, 1.5), (13, 5, 1), (12, 8, 2), (13.5, 11.5, 1), (12.5, 13.5, 1.5))):
            out.append(box(f"Cable{i}", (0, y, z), (16, y + r, z + r), "cable", faces=("north", "south", "up", "down")))
        out.append(box("Tray", (0, 11.5, 1), (16, 12, 15.5), "metal", faces=("north", "south", "up", "down")))
        out.append(box("Hanger", (7.5, 12, 0.5), (8.5, 16, 1), "metal"))
        out.append(box("Hanger2", (7.5, 12, 15.5), (8.5, 16, 16), "metal"))
        return out

    save("cables-run", cables, cable_x())
    save("cables-hub", cables, cable_x() + [dict(rot(b, 1), name=b["name"] + "Z") for b in cable_x()] + [
        box("Box", (5, 9, 5), (11, 16, 11), "metal")])
    for state, tex in (("lit", "tube"), ("off", "tubeoff")):
        save(f"cablelight-{state}", cables, cable_x() + [
            box("Housing", (2, 9.5, 6.5), (14, 11, 9.5), "metal"),
            box("Tube", (2, 8.8, 7), (14, 9.5, 9), tex, glow=255 if state == "lit" else 0),
            box("Chain1", (4, 11, 7.75), (4.5, 11.5, 8.25), "metal"),
            box("Chain2", (11.5, 11, 7.75), (12, 11.5, 8.25), "metal"),
        ])

    save("transformer", {"body": "backrooms:block/level3/transformer", "metal": "backrooms:block/props/metal-dark",
                         "insulator": "backrooms:block/level3/insulator"}, [
        box("Tank", (2, 0, 3), (14, 12, 13), "body"),
        box("FinsWest", (0.5, 1, 4), (2, 11, 12), "metal"),
        box("FinsEast", (14, 1, 4), (15.5, 11, 12), "metal"),
        box("Lid", (1.5, 12, 2.5), (14.5, 13, 13.5), "metal"),
        box("Insulator1", (4, 13, 7), (6, 16, 9), "insulator"),
        box("Insulator2", (7, 13, 7), (9, 16, 9), "insulator"),
        box("Insulator3", (10, 13, 7), (12, 16, 9), "insulator"),
    ])

    for material in ("glazed", "brick", "cinder"):
        tex = {"wall": f"backrooms:block/level3/l3wall-{material}", **PIPE_TEX,
               "panel": "backrooms:block/level3/panel", "fan": "backrooms:block/level3/fan"}
        save(f"l3wall-{material}-pipes", tex, [CUBE("wall")] + all_sides(WALL_PIPES))
        save(f"l3wall-{material}-panel", tex, [CUBE("wall")] + all_sides([
            box("Panel", (3, 2, -2.5), (13, 14, 0), "panel", faces=("north", "east", "west", "up", "down")),
            box("Conduit", (7, 14, -1.5), (9, 16, 0), "metal", faces=("north", "east", "west")),
        ]))
        save(f"l3wall-{material}-fan", tex, [CUBE("wall")] + all_sides([
            box("Housing", (2, 2, -3), (14, 14, -0.5), "metal", faces=("east", "west", "up", "down")),
            box("Grille", (2.5, 2.5, -3), (13.5, 13.5, -2.5), "fan", faces=("north",)),
            box("Back", (2, 2, -0.5), (14, 14, 0), "metal", faces=("north",)),
            box("Hub", (7, 7, -2.5), (9, 9, -1), "metal"),
            box("BladeV", (7.5, 3.5, -2), (8.5, 12.5, -1.5), "metal"),
            box("BladeH", (3.5, 7.5, -2), (12.5, 8.5, -1.5), "metal"),
        ]))

    # Bars standing in a west-east plane across the middle of the block
    bars = [box(f"Bar{i}", (x, 0, 7.25), (x + 1.5, 16, 8.75), "bars", faces=("north", "south", "east", "west"))
            for i, x in enumerate((0.5, 3.5, 6.5, 9.5, 12.5))]
    bars += [box("RailTop", (0, 14, 7), (16, 15.5, 9), "bars"), box("RailBottom", (0, 1, 7), (16, 2.5, 9), "bars")]
    save("ironbars", {"bars": "backrooms:block/level3/bars"}, bars)

    save("manhole", {"iron": "backrooms:block/level3/manhole", "floor": "backrooms:block/level3/dustyfloor"}, [
        box("North", (0, 0, 0), (16, 16, 3), "floor"),
        box("South", (0, 0, 13), (16, 16, 16), "floor"),
        box("West", (0, 0, 3), (3, 16, 13), "floor"),
        box("East", (13, 0, 3), (16, 16, 13), "floor"),
        box("Rim", (2.5, 15.5, 2.5), (13.5, 16.2, 13.5), "iron", faces=("up",)),
    ])
    save("rungs", {"metal": PIPE_TEX["rust"]}, [
        box(f"Rung{i}", (4, y, 1), (12, y + 1, 2), "metal") for i, y in enumerate((2, 6, 10, 14))
    ] + [box("RailL", (3, 0, 0.5), (4, 16, 1.5), "metal"), box("RailR", (12, 0, 0.5), (13, 16, 1.5), "metal")])


def level4():
    t = {"wood": "backrooms:block/level4/laminate", "metal": "backrooms:block/props/metal",
         "plastic": "backrooms:block/level4/crt", "screen": "backrooms:block/level4/crt-screen",
         "fabric": "backrooms:block/level4/chairfabric", "dark": "backrooms:block/props/metal-dark",
         "partition": "backrooms:block/level4/partition", "filing": "backrooms:block/level4/filing",
         "vending": "backrooms:block/level4/vending", "cooler": "backrooms:block/level4/cooler",
         "water": "backrooms:block/level4/coolerbottle"}
    # Cubicle partition running west-east, about 1.5 m tall
    save("partition", t, [box("Panel", (0, 0, 6.5), (16, 24, 9.5), "partition"),
                          box("Cap", (0, 24, 6), (16, 24.5, 10), "metal")])
    oriented("desk", t, [
        box("Top", (0, 11.5, 2), (16, 12.5, 14), "wood"),
        box("LegL", (1, 0, 3), (2, 11.5, 13), "wood"),
        box("LegR", (14, 0, 3), (15, 11.5, 13), "wood"),
        box("Modesty", (2, 4, 12), (14, 11.5, 13), "wood"),
        box("Crt", (4, 12.5, 6), (12, 19.5, 13), "plastic"),
        box("Screen", (5, 13.5, 5.6), (11, 18.5, 6), "screen", glow=30, faces=("north",)),
        box("Keyboard", (4, 12.5, 2.5), (12, 13, 5), "plastic"),
    ])
    oriented("officechair", t, [
        box("Seat", (3, 6, 3), (13, 8, 13), "fabric"),
        box("Back", (3.5, 8, 11), (12.5, 17, 13), "fabric"),
        box("Post", (7, 2, 7), (9, 6, 9), "dark"),
        box("BaseX", (2, 0.5, 7.5), (14, 1.5, 8.5), "dark"),
        box("BaseZ", (7.5, 0.5, 2), (8.5, 1.5, 14), "dark"),
    ])
    oriented("filingcabinet", t, [
        box("Body", (2, 0, 2), (14, 16, 14), "filing"),
        box("Handle1", (6, 12, 1.5), (10, 12.8, 2), "metal"),
        box("Handle2", (6, 7, 1.5), (10, 7.8, 2), "metal"),
        box("Handle3", (6, 2, 1.5), (10, 2.8, 2), "metal"),
    ])
    oriented("vendingmachine", t, [
        box("Body", (0.5, 0, 2), (15.5, 28, 15), "vending"),
        box("Glow", (2, 9, 1.8), (11, 26, 2), "water", glow=90, faces=("north",)),
    ])
    oriented("watercooler", t, [
        box("Body", (4, 0, 4), (12, 14, 12), "cooler"),
        box("Bottle", (5, 14, 5), (11, 22, 11), "water"),
        box("Tap", (7, 9, 3), (9, 10.5, 4), "dark"),
    ])
    save("conferencetable", t, [
        box("Top", (0, 11, 0), (16, 12.5, 16), "wood"),
        box("Leg", (6, 0, 6), (10, 11, 10), "dark"),
    ])


def level5():
    t = {"panel": "backrooms:block/level5/hotelwall-panel", "brass": "backrooms:block/level5/brass",
         "candle": "backrooms:block/props/tube-warm", "gilt": "backrooms:block/level5/gilt",
         "portrait": "backrooms:block/level5/portrait", "placard": "backrooms:block/level5/beverly",
         "cream": "backrooms:block/level5/hotelceiling-cream", "glass": "backrooms:block/level5/domeglass",
         "crystal": "backrooms:block/level5/crystal", "wood": "backrooms:block/level5/mahogany",
         "linen": "backrooms:block/level5/linen", "blanket": "backrooms:block/level5/blanket",
         "velvet": "backrooms:block/level5/velvet", "leaf": "backrooms:block/level5/palmleaf",
         "pot": "backrooms:block/level5/pot", "felt": "backrooms:block/level5/felt", "tile": "backrooms:block/level5/mahjong",
         "record": "backrooms:block/props/metal-dark", "boiler": "backrooms:block/level5/boiler",
         "iron": "backrooms:block/props/metal-dark", "fire": "backrooms:block/level5/fire", "rust": PIPE_TEX["rust"],
         "lampshade": "backrooms:block/level5/lampshade"}

    save("hotelfixture-sconce", t, [CUBE("panel")] + all_sides([
        box("Plate", (6.5, 4, -0.5), (9.5, 10, 0), "brass", faces=("north", "east", "west", "up", "down")),
        box("Arm", (7.5, 7, -3), (8.5, 8, -0.5), "brass"),
        box("Cup", (6.5, 8, -4), (9.5, 9, -2), "brass"),
        box("Candle", (7.25, 9, -3.25), (8.75, 12, -2.75), "candle", glow=180),
    ]))
    save("hotelfixture-portrait", t, [CUBE("panel")] + all_sides([
        box("Frame", (2, 2, -1), (14, 15, 0), "gilt", faces=("east", "west", "up", "down")),
        box("Canvas", (3, 3, -1), (13, 14, -0.8), "portrait", faces=("north",)),
        box("FrameFront", (2, 2, -1.1), (14, 15, -1), "gilt", faces=("north",)),
    ]))
    # Portrait canvas sits behind the frame front: draw the frame as four strips instead
    portrait = [CUBE("panel")] + all_sides([
        box("Canvas", (3, 3, -0.8), (13, 14, -0.5), "portrait", faces=("north",)),
        box("FrameTop", (2, 14, -1.2), (14, 15, 0), "gilt"),
        box("FrameBottom", (2, 2, -1.2), (14, 3, 0), "gilt"),
        box("FrameLeft", (2, 3, -1.2), (3, 14, 0), "gilt"),
        box("FrameRight", (13, 3, -1.2), (14, 14, 0), "gilt"),
    ])
    save("hotelfixture-portrait", t, portrait)
    save("hotelfixture-beverly", t, [CUBE("panel")] + all_sides([
        box("Placard", (2, 5, -0.6), (14, 11, 0), "placard", faces=("north", "east", "west", "up", "down")),
    ]))

    for state, glow in (("lit", 200), ("off", 0)):
        save(f"domelight-{state}", t, [CUBE("cream"),
            box("Base", (5, -0.5, 5), (11, 0, 11), "brass"),
            box("Dome", (5.5, -3, 5.5), (10.5, -0.5, 10.5), "glass", glow=glow)])

    # A great chandelier hanging from the grand ceilings (drawn larger than its block)
    chandelier = [box("Chain", (7.5, 8, 7.5), (8.5, 16, 8.5), "brass"),
                  box("Hub", (6, 4, 6), (10, 8, 10), "brass"),
                  box("Ring", (-4, 5, -4), (20, 6, 20), "brass", faces=("up", "down", "north", "south", "east", "west"))]
    for i, (x, z) in enumerate(((-3, -3), (8, -4), (19, -3), (-4, 8), (20, 8), (-3, 19), (8, 20), (19, 19))):
        chandelier.append(box(f"Candle{i}", (x - 0.75, 6, z - 0.75), (x + 0.75, 8.5, z + 0.75), "candle", glow=220))
    for i, (x, z) in enumerate(((2, 2), (14, 2), (2, 14), (14, 14))):
        chandelier.append(box(f"Crystal{i}", (x - 1, 0, z - 1), (x + 1, 4, z + 1), "crystal", glow=120))
    save("chandelier", t, chandelier)

    oriented("bed-head", t, [
        box("Frame", (1, 2, 0), (15, 6, 16), "wood"),
        box("Mattress", (1.5, 6, 0.5), (14.5, 9, 16), "linen"),
        box("Pillow", (3, 9, 1.5), (13, 10.5, 5), "linen"),
        box("Headboard", (0.5, 0, -0.5), (15.5, 16, 1), "wood"),
        box("Blanket", (1.3, 6.5, 6), (14.7, 9.3, 16), "blanket"),
    ])
    oriented("bed-foot", t, [
        box("Frame", (1, 2, 0), (15, 6, 15), "wood"),
        box("Mattress", (1.5, 6, 0), (14.5, 9, 14.5), "linen"),
        box("Blanket", (1.3, 6.5, 0), (14.7, 9.3, 14.7), "blanket"),
        box("Footboard", (0.5, 0, 14.5), (15.5, 11, 16), "wood"),
    ])
    oriented("nightstand", t, [
        box("Body", (2, 0, 4), (14, 10, 14), "wood"),
        box("LampBase", (6.5, 10, 7.5), (9.5, 11, 10.5), "brass"),
        box("LampStem", (7.5, 11, 8.5), (8.5, 15, 9.5), "brass"),
        box("Shade", (5, 14, 6.5), (11, 19, 12.5), "lampshade", glow=90),
    ])
    oriented("wardrobe", t, [
        box("Body", (1, 0, 5), (15, 30, 16), "wood"),
        box("Seam", (7.8, 2, 4.8), (8.2, 28, 5), "brass"),
        box("Handle1", (6.5, 14, 4.5), (7.5, 17, 5), "brass"),
        box("Handle2", (8.5, 14, 4.5), (9.5, 17, 5), "brass"),
    ])
    oriented("wingchair", t, [
        box("Seat", (2, 4, 2), (14, 8, 14), "velvet"),
        box("Back", (2, 8, 12), (14, 22, 15), "velvet"),
        box("WingL", (1, 8, 6), (3, 18, 15), "velvet"),
        box("WingR", (13, 8, 6), (15, 18, 15), "velvet"),
        box("Legs", (3, 0, 3), (13, 4, 13), "wood"),
    ])
    oriented("sofa", t, [
        box("Seat", (0, 4, 3), (16, 8, 14), "velvet"),
        box("Back", (0, 8, 12), (16, 17, 15), "velvet"),
        box("Base", (0.5, 0, 3.5), (15.5, 4, 14.5), "wood"),
    ])
    palm = [box("Pot", (4, 0, 4), (12, 8, 12), "pot"), box("Trunk", (7, 8, 7), (9, 20, 9), "wood")]
    for i, (dx, dz) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        palm.append(box(f"Frond{i}", (8 + min(0, dx * 9) if dx else 6, 18, 8 + min(0, dz * 9) if dz else 6),
                        (8 + max(0, dx * 9) if dx else 10, 19, 8 + max(0, dz * 9) if dz else 10), "leaf"))
    save("pottedpalm", t, palm)
    save("mahjongtable", t, [
        box("Top", (0, 11, 0), (16, 12.5, 16), "felt"),
        box("Rim", (-0.5, 11, -0.5), (16.5, 12, 16.5), "wood", faces=("north", "south", "east", "west", "down")),
        box("Leg", (6, 0, 6), (10, 11, 10), "wood"),
    ] + [box(f"Tiles{i}", (x, 12.5, z), (x + w, 13.5, z + d), "tile") for i, (x, z, w, d) in
         enumerate(((2, 2, 12, 1.5), (2, 12.5, 12, 1.5), (2, 4, 1.5, 8), (12.5, 4, 1.5, 8), (6, 7, 4, 2)))])
    save("turntable", t, [
        box("Base", (2, 0, 2), (14, 10, 14), "wood"),
        box("Platter", (3.5, 10, 3.5), (12.5, 10.6, 12.5), "record"),
        box("Arm", (11, 10.5, 4), (12, 11.5, 11), "brass"),
        box("Horn", (10, 10.5, 10), (15, 17, 15), "brass"),
    ])
    oriented("boiler", t, [
        box("Body", (1, 0, 2), (15, 26, 15), "boiler"),
        box("Hatch", (5, 6, 1.5), (11, 12, 2), "iron"),
        box("Gauge", (6.5, 17, 1.5), (9.5, 20, 2), "iron"),
        box("Flue", (6, 26, 7), (10, 32, 11), "rust"),
    ])
    oriented("furnace", t, [
        box("Body", (1, 0, 2), (15, 14, 15), "iron"),
        box("Door", (4, 2, 1.6), (12, 9, 2), "fire", glow=200, faces=("north",)),
        box("Hood", (0, 14, 1), (16, 16, 16), "iron"),
    ])


if __name__ == "__main__":
    parking()
    level3()
    level4()
    level5()
    level2()
    level1()
    print("shapes written")
