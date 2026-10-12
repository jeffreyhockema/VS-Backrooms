"""The Hub (level 17): every asset in docs/design/new-levels/hub-plan.md section 4 (and its "Manifest changes (phase 2)").

Road-tunnel blocks (seamed concrete slabs, asphalt with yellow road studs, caged amber lamps, jet fans, lane signals,
M.E.G. stencils), the carved concrete level doors with their crop-circle sigils, the service doors, the ornate Tower
doors, the pink ribbon door to Level 974, the false wall, the Tower's stone and marble, the outposts' furniture, the
Level Keys for every level, the sounds, the Keymaster and the English names.

Run from the repo root, through the asset lock:   bash tools/locked.sh run python tools/gen_hub.py
Options: --no-sounds, --no-keymaster (skip the slow parts while iterating).

Modules: gen_hub_kit.py (writers, boxes, textures, tunnel blocks), gen_hub_sigils.py (the sigil table),
gen_hub_doors.py, gen_hub_tower.py (Tower and outposts), gen_hub_items.py (Level Keys), gen_hub_sounds.py,
gen_hub_keymaster.py (the Keymaster's model and entity).

Everything is written to hub/ folders: textures/block/hub, shapes/block/hub, blocktypes/hub, textures/item/hub,
shapes/item/hub, itemtypes/hub, sounds/{ambient,effect}/hub, plus the Keymaster's shape, texture and entity type
(shapes/entity/hub-keymaster.json, textures/entity/hub-keymaster.png, entities/hub-keymaster.json). Names are merged
into lang/en.json: only keys this script owns are touched (block-hub-*, item-hub-*, hub-*, level 17's title keys).

Orientation, for every block with a `side` variant group: the `-north` variant shows its face to the north (-Z).
- Blocks set INTO a wall (doors, sigils, sigil sides, service doors, ornate doors, pink door): the block is the wall
  cell, its carved face is its north face, and the player stands north of it.
- Blocks hung ON a wall (lamps, stencils, plaques, amber arrows, banner, key cabinet, pilasters, cornice): the block
  is the air cell in front of the wall; its back is against the wall to its south.
- Free-standing props face north. The arch blocks are the top row of an opening, face north.
- "l" and "r" parts are the viewer's left and right, looking at the face: in the -north variant "l" is the east (+X)
  block and "r" the west (-X) one.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

import gen_hub_kit as K  # noqa: E402

TAB, NL = "\t", "\n"


def merge_lang():
    """Adds the names to lang/en.json without disturbing its layout: existing keys are updated in place, new ones are
    appended after the last hub key (or at the end)."""
    path = os.path.join(K.ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new_lines = []
    for key, value in K.LANG.items():
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
    json.loads(text)  # still valid
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)
    return len(new_lines)


def main():
    args = set(sys.argv[1:])
    # Start clean: these folders hold only what this script writes, so nothing stale is left behind
    import shutil
    for sub in (("textures", "block"), ("textures", "item"), ("shapes", "block"), ("shapes", "item"), ("blocktypes",), ("itemtypes",)):
        shutil.rmtree(os.path.join(K.ASSETS, *sub, "hub"), ignore_errors=True)
    K.wall_textures()
    K.road_textures()
    K.fixture_textures()
    K.stencil_textures()
    K.door_textures()
    K.tower_textures()
    K.outpost_textures()
    K.tunnel_blocks()
    import gen_hub_doors
    gen_hub_doors.generate()
    import gen_hub_tower
    gen_hub_tower.generate()
    import gen_hub_items
    gen_hub_items.generate()
    if "--no-sounds" not in args:
        import gen_hub_sounds
        gen_hub_sounds.generate()
    if "--no-keymaster" not in args:
        import gen_hub_keymaster
        gen_hub_keymaster.generate()
    import gen_hub_lang
    gen_hub_lang.generate()
    added = merge_lang()
    c = K.COUNTS
    print(f"hub: {c['blocktypes']} block types ({c['variants']} variants), {c['shapes']} shapes, {c['textures']} textures,"
          f" {len(K.LANG)} lang keys ({added} new)")


if __name__ == "__main__":
    main()
