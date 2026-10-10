"""Vanilla-style particles and warmth for the props that burn: candle flames, fire licks, embers, smoke and steam.

The particle dicts follow vanilla's own (blocktypes/wax/candle.json, wood/firepit.json, clay/oven.json). A plain
block spawns each entry every 25 ms at its top middle (the middle of the top of its first collision box) plus
`posOffset`, so every helper takes the offset from that point. Offsets are in world axes: a prop that turns needs one
list per side (see `by_side`).
"""

SIDES = ["north", "east", "south", "west"]


def nf(avg, var=0):
    return {"avg": avg, "var": var}


def turn(x, z, side):
    """A point (x, z) of a north-facing model (block units, 0-1) as it lies once the block is turned to `side`.
    VS turns a model counter-clockwise seen from above: rotateY 270 brings its north face round to the east."""
    return {"north": (x, z), "east": (1 - z, x), "south": (1 - x, 1 - z), "west": (z, 1 - x)}[side]


def flame(dx, dy, dz, quantity=0.1, size=0.05):
    """One candle flame (vanilla candle's fire quads), its foot at the offset."""
    return {
        "hsvaColor": [nf(20, 20), nf(255, 50), nf(255, 50), nf(255, 0)],
        "opacityEvolve": {"transform": "quadratic", "factor": -16},
        "gravityEffect": nf(0),
        "posOffset": [nf(dx, 0.005), nf(dy, 0), nf(dz, 0.005)],
        "velocity": [nf(0, 0.0125), nf(0.03, 0.01), nf(0, 0.0125)],
        "quantity": nf(quantity),
        "size": nf(size, size / 2),
        "lifeLength": nf(0.5),
        "sizeEvolve": {"transform": "linear", "factor": 0.1},
        "particleModel": "Quad",
        "vertexFlags": 128,
        "windAffectednes": 0.05,
    }


def fire(dx, dy, dz, spread=(0.2, 0, 0.2), quantity=0.6, size=0.3, rise=0.125):
    """Licking flames over a bed of coals (vanilla firepit's fire quads), smaller and fewer."""
    return {
        "hsvaColor": [nf(20, 20), nf(255, 50), nf(255, 50), nf(255, 0)],
        "opacityEvolve": {"transform": "quadratic", "factor": -16},
        "gravityEffect": nf(0),
        "posOffset": [nf(dx, spread[0]), nf(dy, spread[1]), nf(dz, spread[2])],
        "velocity": [nf(0, 0.05), nf(rise, 0.05), nf(0, 0.05)],
        "quantity": nf(quantity),
        "size": nf(size, size / 6),
        "lifeLength": nf(0.25),
        "sizeEvolve": {"transform": "linear", "factor": 0.25},
        "particleModel": "Quad",
        "vertexFlags": 128,
        "windAffectednes": 0.2,
    }


def embers(dx, dy, dz, spread=(0.2, 0, 0.2), quantity=0.015, velocity=(0, 0.5, 0)):
    """Sparks flying up off the coals (vanilla firepit's ember cubicles)."""
    vx, vy, vz = velocity
    return {
        "hsvaColor": [nf(30, 20), nf(255, 50), nf(255, 50), nf(255, 0)],
        "gravityEffect": {"dist": "invexp", "avg": -0.1, "var": 0.4},
        "posOffset": [nf(dx, spread[0]), nf(dy, spread[1]), nf(dz, spread[2])],
        "velocity": [nf(vx, 0.15), nf(vy, 0.1), nf(vz, 0.15)],
        "quantity": nf(quantity),
        "size": nf(0.4, 0),
        "sizeEvolve": {"transform": "quadratic", "factor": -0.7},
        "lifeLength": nf(1.5),
        "vertexFlags": 128,
        "windAffectednes": 0.2,
    }


def smoke(dx, dy, dz, spread=0.2, quantity=0.04, life=5, value=70, alpha=160):
    """Grey smoke drifting up (vanilla firepit's smoke quads, thinner and shorter-lived under a ceiling)."""
    return {
        "hsvaColor": [nf(0), nf(0), nf(value, 30), nf(alpha, 40)],
        "opacityEvolve": {"transform": "linear", "factor": -255},
        "gravityEffect": nf(0),
        "posOffset": [nf(dx, spread), nf(dy, 0), nf(dz, spread)],
        "velocity": [nf(0, 0.025), nf(0.2, 0.05), nf(0, 0.025)],
        "quantity": nf(quantity),
        "size": nf(0.3, 0.05),
        "sizeEvolve": {"transform": "linear", "factor": 1.5},
        "particleModel": "Quad",
        "lifeLength": nf(life),
        "selfPropelled": True,
        "windAffectednes": 0.7,
    }


def steam(dx, dy, dz, spread=(0.08, 0, 0.08), quantity=0.06, velocity=(0, 0.35, 0), life=1.4, size=0.3):
    """A thin white wisp of steam from a joint or a valve (pale, quick, swelling as it fades)."""
    vx, vy, vz = velocity
    return {
        "hsvaColor": [nf(0), nf(0), nf(225, 20), nf(110, 30)],
        "opacityEvolve": {"transform": "quadratic", "factor": -16},
        "gravityEffect": nf(-0.01),
        "posOffset": [nf(dx, spread[0]), nf(dy, spread[1]), nf(dz, spread[2])],
        "velocity": [nf(vx, 0.06), nf(vy, 0.08), nf(vz, 0.06)],
        "quantity": nf(quantity),
        "size": nf(size, size / 3),
        "sizeEvolve": {"transform": "linear", "factor": 1.2},
        "particleModel": "Quad",
        "lifeLength": nf(life, life / 4),
        "selfPropelled": True,
    }


def by_side(make):
    """{"*-north": [...], ...}: `make(side)` builds the list for one facing."""
    return {f"*-{s}": make(s) for s in SIDES}


def heat(strength):
    """Vanilla's HeatSource behaviour: warms a player standing near (a lit firepit gives 10, a forge 7, embers 6)."""
    return {"name": "HeatSource", "properties": {"heatStrength": strength}}
