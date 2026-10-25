"""What breaking each piece of Backrooms furniture and clutter gives, in one place.

The philosophy is "a normal Vintage Story player wakes in the Backrooms": what you break down should feed Vintage
Story's own progression. Wooden furniture is salvaged lumber (planks, sticks, firewood and nails, so a firepit,
a chest or a barrel is possible before you own a saw); upholstery and linen give cloth; copper cable and pipe give
copper bits for the crucible; hotel silverware and brass fittings give silver and brass; wardrobes and suitcases
hold clothes; beds come away as real beds you can sleep in; coal piles burn hot enough to smelt.

apply() rewrites the drops of the generated block types (run at the end of gen_detail.py and gen_blocktypes.py).
Hand-written block types (crates, supply boxes, shelves, drums) keep their drops in their own files.
"""
import json
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..")
BLOCKTYPES = os.path.join(ROOT, "assets", "backrooms", "blocktypes")


def d(*items):
    """(code, average, variance); codes without a domain are ours. Blocks are marked with a leading 'block:'."""
    out = []
    for code, avg, var in items:
        kind = "item"
        if code.startswith("block:"):
            kind, code = "block", code[6:]
        out.append({"type": kind, "code": code, "quantity": {"avg": avg, "var": var}})
    return out


PLANK, STICK, FIREWOOD, NAILS = "game:plank-aged", "game:stick", "game:firewood", "game:metalnailsandstrips-iron"
CLOTH, LINEN, PAPER, CANDLE = "game:cloth-plain", "block:game:linen-normal-down", "game:paper-parchment", "game:candle"

SALVAGE = {
    # Level 4: the office
    "desk": d((PLANK, 2, 1), ("scrapwire", 1, 0.5), ("glassshard", 0.5, 0.5), (PAPER, 0.6, 0.6), ("wanderernote-way", 0.04, 0)),
    "conferencetable": d((PLANK, 4, 1), (NAILS, 0.5, 0.5)),
    "officechair": d(("metalbracket", 1, 0.5), (CLOTH, 0.3, 0.3), ("pleather", 1.5, 0.5)),
    "officechairtipped": d(("metalbracket", 1, 0.5), (CLOTH, 0.3, 0.3), ("pleather", 1.5, 0.5)),
    "filingcabinet": d(("metalbracket", 2, 1), (PAPER, 1, 1), ("wanderernote-door", 0.05, 0)),
    "partition": d((CLOTH, 0.6, 0.4), ("metalbracket", 0.5, 0.5)),
    "copier": d(("glassshard", 1, 0.5), ("scrapwire", 2, 1), (PAPER, 1, 1)),
    "officebookshelf": d((PLANK, 3, 1), (PAPER, 1, 1)),
    "receptiondesk": d((PLANK, 4, 1), (PAPER, 0.5, 0.5), ("game:gear-rusty", 0.15, 0)),
    "roundtable": d((PLANK, 2, 1)),
    "chairstack": d(("metalbracket", 2, 1)),
    "coatstand": d((STICK, 2, 1), (PLANK, 1, 0)),
    "wastebasket": d((PAPER, 0.6, 0.4), ("rottenwood", 0.3, 0.3), ("glassshard", 0.2, 0.2)),
    # (The pot breaks too: shards for grit, and grit and soil for a little clay)
    "ficus": d((STICK, 2, 1), ("game:drygrass", 1, 0.5), ("block:game:soil-low-none", 1, 0), ("potshard", 1, 1)),
    # Level 1 and 3: maintenance, storage, camps
    "cardboardboxes": d((PAPER, 1, 1), ("crackers", 0.15, 0.15), (CANDLE, 0.2, 0.2), ("game:drygrass", 0.5, 0.5)),
    "workbench": d((PLANK, 3, 1), (NAILS, 0.6, 0.4), ("prybar", 0.03, 0)),
    "toolbox": d((NAILS, 1, 0.5), ("scrapwire", 0.5, 0.5), ("game:rope", 0.3, 0.3), ("game:hammer-copper", 0.06, 0),
                 ("game:chisel-copper", 0.04, 0), ("game:saw-copper", 0.04, 0), ("game:knife-generic-copper", 0.08, 0),
                 ("prybar", 0.04, 0)),
    "plywood": d((PLANK, 2, 1)),
    "pallet": d((PLANK, 3, 1), (NAILS, 0.5, 0.5)),
    "tent": d((LINEN, 1, 0.5), (STICK, 3, 1), ("game:rope", 0.5, 0.5), ("wanderernote-cache", 0.3, 0), ("wanderernote-door", 0.2, 0)),
    "bedroll": d((CLOTH, 1, 0.5), ("game:drygrass", 2, 1), ("wanderernote-door", 0.12, 0)),
    # The real-sized tent and sleeping bag (two blocks by two, and two long): the first part holds it all
    "camptent": d((LINEN, 2, 0.5), (STICK, 4, 1), ("game:rope", 1, 0.5), (CLOTH, 1, 0.5), ("wanderernote-cache", 0.35, 0),
                  ("wanderernote-door", 0.2, 0)),
    "sleepingbag": d((CLOTH, 2, 0.5), ("game:drygrass", 1, 0.5), ("wanderernote-door", 0.12, 0)),
    # Improvised camps (layout version 11): beds of cardboard, blankets and mattresses; lean-tos of a tarp and chairs or a door and cabinets
    # (Their wanderer notes are half the old gear's, as the note tuning has it: NoteSystem.Spots makes the rest back in Level 0)
    "improvbed": d((PAPER, 1.5, 1), (CLOTH, 1.5, 1), ("game:drygrass", 1, 0.5), ("wanderernote-door", 0.06, 0)),
    "leanto": d((CLOTH, 1, 0.5), (STICK, 1, 1), ("metalbracket", 1, 0.5), ("game:rope", 0.5, 0.5), ("wanderernote-cache", 0.125, 0),
                ("wanderernote-door", 0.06, 0)),
    # What the lost left at Level 6's dead ends and on Level 7's seabed: their kit, and where they were trying to go
    "backpack": d(("almondwater", 0.8, 0.6), ("crackers", 0.4, 0.4), (CANDLE, 0.4, 0.4), ("game:rope", 0.3, 0.3),
                  ("game:knife-generic-copper", 0.1, 0), ("game:bandage-clean", 0.4, 0.4), ("chalk", 0.2, 0),
                  ("game:fishingbait-dough", 0.5, 0.5), ("wanderernote-door", 0.3, 0), ("wanderernote-way", 0.2, 0),
                  ("l974-plush-cat", 0.02, 0)),  # (Level 974: kept for luck, or for Kitty)
    "hospitalbed": d(("metalbracket", 2, 1), (CLOTH, 1, 0.5), ("game:bandage-clean", 0.3, 0.3)),
    "foldingtable": d(("metalbracket", 1, 0.5)),
    # (The cafeteria chair's drops come from gen_deep.py; the same here so it can be taken apart whole)
    "cafechair": d(("metalbracket", 0.6, 0.4)),
    "foldingchair": d(("metalbracket", 0.6, 0.4)),
    "medcabinet": d(("game:bandage-clean", 1, 1), ("glassshard", 0.3, 0.3)),
    "fridge": d(("crackers", 0.25, 0.25), ("cannedbeans", 0.2, 0.2), ("game:fruit-redapple", 0.35, 0.35), ("game:cheese-cheddar-1slice", 0.2, 0.2),
                ("metalbracket", 1, 0.5), ("scrapwire", 0.5, 0.5)),
    # Level 6.1's vending rooms: the dead machines of the heap, a few snacks still stuck in their spirals
    "vendingpile": d(("metalbracket", 2, 1), ("glassshard", 1, 0.5), ("scrapwire", 1, 0.5), ("chips", 0.3, 0.3), ("soda", 0.25, 0.25)),
    # The broken snack machine in a vending room's doorway: what it still held (and a coin box nobody emptied)
    "brokenvending": d(("chips", 2, 1), ("candybar", 1.5, 1), ("crackers", 1.5, 1), ("soda", 1.5, 1), ("cashewwater", 0.5, 0.5),
                       ("almondwater", 0.4, 0.4), ("metalbracket", 2, 1), ("glassshard", 1.5, 1), ("scrapwire", 1, 0.5)),
    "trashcan": d((PAPER, 0.5, 0.5), ("rottenwood", 0.4, 0.4), ("glassshard", 0.3, 0.3), ("game:gear-rusty", 0.05, 0)),
    # Copper cable on wooden drums, motor windings, old pipe: copper (and lead) for the crucible
    "cablespool": d(("game:metalbit-copper", 4, 2), (PLANK, 1, 0.5)),
    "floorfan": d(("scrapwire", 1, 0.5), ("metalbracket", 1, 0.5), ("game:metalbit-copper", 1, 0.5)),
    "pipestack": d(("game:metalbit-copper", 2, 1), ("game:metalbit-lead", 2, 1)),
    # Level 5: the hotel
    "bed-head": d(("block:game:bed-woodaged-head-north", 1, 0)),
    "bed-foot": d((LINEN, 0.6, 0.4)),
    "nightstand": d((PLANK, 1, 0.5), (CANDLE, 0.3, 0.3)),
    "wardrobe": d((PLANK, 3, 1), (CLOTH, 0.5, 0.5), ("game:clothes-upperbody-linen-tunic", 0.25, 0),
                  ("game:clothes-upperbody-woolen-shirt", 0.15, 0), ("game:clothes-lowerbody-commoner-trousers", 0.25, 0),
                  ("game:clothes-foot-commoner-boots", 0.2, 0)),
    "wingchair": d((PLANK, 1, 0.5), (CLOTH, 1, 0.5), (STICK, 1, 0.5), ("pleather", 1.5, 0.5)),
    "sofa": d((PLANK, 1, 0.5), (CLOTH, 1, 0.5), (STICK, 1, 0.5), ("pleather", 1.5, 0.5)),
    "longsofa": d((PLANK, 2, 0.5), (CLOTH, 2, 0.5), (STICK, 2, 0.5), (NAILS, 0.3, 0.3), ("pleather", 2, 0.5)),
    "pottedpalm": d((STICK, 2, 1), ("block:game:soil-low-none", 1, 0), ("potshard", 1, 1)),
    "mahjongtable": d((PLANK, 2, 1), ("game:gear-rusty", 0.2, 0)),
    "turntable": d(("scrapwire", 1, 0.5), (PLANK, 1, 0)),
    "consoletable": d((PLANK, 2, 1), (CANDLE, 0.3, 0.3)),
    "hotelbookshelf": d((PLANK, 3, 1), (PAPER, 1, 1)),
    "curiocabinet": d((PLANK, 2, 1), ("glassshard", 1, 0.5), ("game:metalbit-silver", 0.5, 0.5), ("game:gear-rusty", 0.1, 0)),
    "luggagecart": d(("game:metalbit-brass", 2, 1), ("metalbracket", 1, 0.5)),
    "servicetrolley": d(("metalbracket", 1, 0.5), ("game:metalbit-silver", 0.5, 0.5), ("crackers", 0.15, 0.15)),
    "writingdesk": d((PLANK, 2, 1), (PAPER, 1, 0.5), (CANDLE, 0.3, 0.3), ("wanderernote-refuge", 0.05, 0)),
    "hotelchair": d((PLANK, 1, 0.5), (STICK, 1, 0.5), (CLOTH, 0.3, 0.3), ("pleather", 1.5, 0.5)),
    "suitcase": d((CLOTH, 1, 0.5), ("game:clothes-upperbody-tattered-linen-shirt", 0.2, 0),
                  ("game:clothes-lowerbody-dirty-linen-trousers", 0.2, 0), (CANDLE, 0.2, 0.2), ("crackers", 0.15, 0.15),
                  ("l974-plush-bear", 0.015, 0), ("l974-plush-bunny", 0.015, 0)),  # (Level 974: a child's plush, now and then)
    "coffeetable": d((PLANK, 2, 1)),
    "ashtraystand": d(("game:metalbit-brass", 1, 0.5)),
    "diningtable": d((PLANK, 4, 1), (LINEN, 0.5, 0.5), ("game:metalbit-silver", 1, 0.5)),
    "candelabra": d((CANDLE, 2, 1), ("game:metalbit-brass", 2, 1)),
    # The coal heaped by the generators and boilers, with the Firesalt that turns up in it
    "coalpile": d(("game:ore-bituminouscoal", 6, 2), ("block:firesalt", 1, 1)),
    # Level 9: the houses
    "dresser": d((CLOTH, 0.8, 0.5), ("game:flaxtwine", 0.6, 0.5), (CANDLE, 0.2, 0.2), ("game:clothes-upperbody-commoner-shirt", 0.25, 0),
                 ("game:clothes-lowerbody-homespun-pants", 0.2, 0), ("game:clothes-foot-commoner-boots", 0.15, 0)),
    # (Level 974: a plush toy is cute, and something in the Backrooms likes cute things: about one toy box in three)
    "toybox": d((CLOTH, 0.5, 0.4), (CANDLE, 0.2, 0.2), ("game:gear-rusty", 0.1, 0), ("l974-plush-cat", 0.09, 0),
                ("l974-plush-bunny", 0.09, 0), ("l974-plush-bear", 0.09, 0), ("l974-plush-star", 0.08, 0)),
    "wheeliebin": d((PAPER, 0.5, 0.5), ("rottenwood", 0.5, 0.5), ("glassshard", 0.3, 0.3), ("game:bone", 0.3, 0.3)),
    "grill": d(("metalbracket", 1, 0.5), ("game:charcoal", 2, 1)),
    # Garden sheds and kitchen drawers: the seeds for a farm at home, and a pry bar for the houses that are locked
    "toolshelf": d(("game:hammer-copper", 0.15, 0), ("game:saw-copper", 0.1, 0), ("game:shovel-copper", 0.12, 0), (NAILS, 0.8, 0.6),
                   ("game:rope", 0.5, 0.4), ("scrapwire", 0.6, 0.5), ("prybar", 0.08, 0), ("seedpacket-turnip", 0.12, 0),
                   ("seedpacket-carrot", 0.1, 0), ("seedpacket-onion", 0.08, 0), ("seedpacket-flax", 0.06, 0)),
    "kitchencabinet": d(("game:salt", 0.5, 0.5), ("game:flour-spelt", 0.5, 0.5), ("cannedbeans", 0.6, 0.5), ("game:knife-generic-copper", 0.12, 0),
                        ("game:fat", 0.3, 0.3), ("crackers", 0.4, 0.4), (CANDLE, 0.2, 0.2), ("seedpacket-onion", 0.05, 0)),
}

# Furniture that comes away whole under a saw (src/Salvage/Dismantle.cs): the lumber, cloth and bits above are what any
# other tool gets. Wood and cloth pieces only; metal ones, the beds and anything over several blocks are left out.
DISMANTLE = ["desk", "conferencetable", "officechair", "officebookshelf", "roundtable", "partition", "hotelchair", "wingchair",
             "sofa", "nightstand", "wardrobe", "hotelbookshelf", "consoletable", "coffeetable", "diningtable", "dresser",
             "mahjongtable", "writingdesk"]

# Metal furniture comes away whole under a hammer (the bolts knocked out), by the same behaviour with tool = hammer
DISMANTLE_HAMMER = ["filingcabinet", "cafechair", "foldingtable", "foldingchair", "chairstack", "luggagecart", "servicetrolley"]

# The leading part of a block's code that the salvage system checks (bed-head and bed-foot are both "bed")
FILES = {"bed-head": "level5/bed-head.json", "bed-foot": "level5/bed-foot.json"}


def _find(code):
    if code in FILES:
        return os.path.join(BLOCKTYPES, FILES[code])
    for folder in ("detail", "level4", "level5", "level1", "level2", "level3", ""):
        p = os.path.join(BLOCKTYPES, folder, code + ".json")
        if os.path.exists(p):
            return p
    return None


def apply():
    done, skipped = 0, []
    for code in DISMANTLE + DISMANTLE_HAMMER:
        if code not in SALVAGE:
            raise SystemExit("DISMANTLE names " + code + " with no salvage entry")
    for code, drops in SALVAGE.items():
        path = _find(code)
        if path is None:
            skipped.append(code)
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        # Generated files are strict JSON after an optional leading // comment line
        m = re.match(r"((?:\s*//[^\n]*\n)*)(.*)", text, re.S)
        head, body = m.group(1), m.group(2)
        try:
            data = json.loads(body)
        except ValueError:
            skipped.append(code + " (hand-written)")
            continue
        data.pop("dropsByType", None)
        # A prop over several blocks breaks whole (BackroomsPartnered): what it gives comes from its first part only
        partnered = [b for b in data.get("behaviors", []) if b.get("name") == "BackroomsPartnered"]
        if partnered:
            data.pop("drops", None)
            data["dropsByType"] = {f"*-{partnered[0]['properties']['parts'][0]}-*": drops, "*": []}
        else:
            data["drops"] = drops
        if (code in DISMANTLE or code in DISMANTLE_HAMMER) and not any(b.get("name") == "BackroomsDismantle" for b in data.get("behaviors", [])):
            behavior = {"name": "BackroomsDismantle"}
            if code in DISMANTLE_HAMMER:
                behavior["properties"] = {"tool": "hammer"}
            data.setdefault("behaviors", []).append(behavior)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(head + json.dumps(data, indent="\t", ensure_ascii=False) + "\n")
        done += 1
    print(f"salvage: {done} block types given drops" + (f"; skipped {', '.join(skipped)}" if skipped else ""))


if __name__ == "__main__":
    apply()
