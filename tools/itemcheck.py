"""Lists the itemtypes (variants expanded as langcheck does) that have no shape: the game draws those as its flat extruded sprite.

    python tools/itemcheck.py [--list]

Fails (exit 1) if a flat itemtype is not named in tools/itemcheck-flat.txt, or a listed one is no longer flat or no longer exists
(remove its line). Run by the gate's lang stage. Item pass 0.700: every flat item gets a model; the list only ever shrinks.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import langcheck  # noqa: E402

ITEMS = os.path.join(REPO, "assets", "backrooms", "itemtypes")
LIST = os.path.join(HERE, "itemcheck-flat.txt")


def has_shape(doc, path):
    sh = doc.get("shape")
    if isinstance(sh, dict) and sh.get("base"):
        return True
    by = doc.get("shapeByType")
    if isinstance(by, dict):
        for pat, v in by.items():
            if langcheck.wild(pat, path) and isinstance(v, dict) and v.get("base"):
                return True
    return False


def flat_items():
    out = []
    for f in sorted(glob.glob(os.path.join(ITEMS, "**", "*.json"), recursive=True)):
        try:
            doc = langcheck.read_json(f)
        except (ValueError, IndexError):
            continue
        if not isinstance(doc, dict) or doc.get("enabled") is False:
            continue
        for p in langcheck.expand(doc, [], f):
            if not has_shape(doc, p):
                out.append(p)
    return sorted(set(out))


def allowed():
    if not os.path.exists(LIST):
        return set()
    return {l.split("#")[0].strip() for l in open(LIST, encoding="utf-8") if l.split("#")[0].strip()}


def main(argv):
    flat, ok = flat_items(), allowed()
    if "--list" in argv:
        print("\n".join(flat))
    new = [c for c in flat if c not in ok]
    stale = sorted(ok - set(flat))
    for c in new:
        print("[flat] %s has no shape (drawn flat) and is not in tools/itemcheck-flat.txt: give it a model" % c)
    for c in stale:
        print("[stale] %s is in tools/itemcheck-flat.txt but now has a shape (or is gone): remove the line" % c)
    print("itemcheck: %d flat itemtypes, %d allowed, %d new, %d stale" % (len(flat), len(ok), len(new), len(stale)))
    return 1 if new or stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
