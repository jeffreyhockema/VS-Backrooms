"""Level 73, "The Redlands": round 4's (2026-11-02) asset-quality pass, the props part; called from gen_73.py (run that, under
the asset lock). Same interface as gen_73_interior.py: textures(save) -> count, blocktypes() -> [(comment, block)],
shapes(write_json, shape_dir) -> count.
"""


# Block names for the HUD: [("block-l73-...", "Name")]
LANG = []


def textures(save):
    return 0


def blocktypes():
    return []


def shapes(write_json, shape_dir):
    return 0
