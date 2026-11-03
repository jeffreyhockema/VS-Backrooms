"""Level 36 "Airport" (experimental, id 25): its lang keys in lang/en.json, all in one block after its level-25 lines.

Writes the level's own strings (titles, hints, the airport's messages, block names from gen_36_surfaces.py and
gen_36_props.py), then gathers the keys the shared generators write for the level (its notes from gen_notes.py, its
handbook page from gen_guide.py, the Travel Planner's lines from gen_dialogue.py), wherever they were appended, into the
same block, so the level's strings stay together. (The handbook page is gen_guide.py's PAGES["level36"]: the links round
wrote it here for a while; the lead moved it back on 2026-11-01.) Run it after those generators (tools/gen_36.py does all
of it).

    python tools/gen_36_lang.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.join(os.path.dirname(__file__), "..")
EN = os.path.join(ROOT, "assets", "backrooms", "lang", "en.json")

OWN = {
    "level-25": "Level 36: Airport",
    "levelhint-25": "Every level is one flight away. Watch the screens; and leave the sinks alone.",
    "levelname-25": "Level 36",
    "level-2501": "Baggage Claim",
    "level-2502": "Check-in",
    "level-2503": "Security",
    "level-2504": "The Concourses",
    "level-2505": "The Gates",
    "level-2506": "Duty Free",
    "level-2507": "The Food Court",
    "level-2508": "The Lounge",
    "level-2509": "The Meeting Place",
    "level-2510": "Out of Bounds",
    "level-2511": "The Absolute Limit",
    "level-2512": "Flight 36.1",
    "level-2513": "Blackout",
    "level-2514": "Lost and Found",
    "blockhelp-l36-gatedoor": "Board / step off",
    "blockhelp-l36-screen": "Read the departures",
    "l36-gate-waiting": "Gate {0}: flight {1} to Level {2}. Count {3}. Not boarding yet: boarding opens under 1,000.",
    "l36-gate-c32": "Gate {0}: flight {1} to Level {2}. Count {3}. DELAYED.",
    "l36-board": "You board flight {0} to Level {1} at gate {2}. Find a seat. (Count {3}: the doors close at nothing.)",
    "l36-deplane": "You step back off the plane at gate {0}.",
    "l36-door-inflight": "The door is sealed. The plane is in the air.",
    "l36-takeoff": "The doors close. Flight {0} pushes back, and climbs.",
    "l36-cruise": "The seatbelt sign goes off. Outside the little windows: cloud tops, and nothing else.",
    "l36-descent": "The seatbelt sign comes on. Cabin crew, prepare for landing.",
    "l36-landed": "The wheels touch. The door opens, and the airport is not there any more.",
    "l36-nosleep": "You close your eyes for what feels like hours and open them in the same second. Nobody sleeps here.",
    "l36-screen-empty": "The screen shows only dashes.",
    "l36-screen-head": "DEPARTURES   flight / to / gate / count",
    "l36-screen-row": "{0}   Level {1}   {2}   {3}   {4}",
    "l36-status-boarding": "BOARDING",
    "l36-status-soon": "GO TO GATE",
    "l36-status-scheduled": "SCHEDULED",
    # (links, 2026-10-31: ThresholdNetwork.L36.cs, L36System)
    "l36-arrive-door": "The door under the airplane sign lets you into a baggage hall that goes on, north and south, further than any building could.",
    "l36-leave-door": "You push the door open and step back out where you came in.",
    "l36-sink-overflow": "The tap runs, and will not turn off. The basin fills to the brim and over it, onto the floor.",
    "l36-sink-arrive": "You hold your breath and put your face into the water. It is deeper than the basin; much deeper. You come up in warm, tiled light.",
    "blockhelp-l36-sink-tap": "Turn the tap",
    "blockhelp-l36-sink-dunk": "Put your head under (hold)",
}




def owned(key):
    return (key in OWN or key.startswith(("block-l36-", "l36-", "blockhelp-l36-", "level-25", "note-l36-", "notetitle-l36-", "note-r-l36-",
                                          "notetitle-r-l36-", "journal-track-l36", "guide-level36-"))
            or re.match(r"dialogue-wanderer-.*-36$", key) is not None)


def block_names():
    names = {}
    for mod in ("gen_36_surfaces", "gen_36_props", "gen_36_detail", "gen_36_r4"):
        names.update(__import__(mod).NAMES)
    return names


def main():
    with open(EN, encoding="utf-8") as f:
        text = f.read()
    current = json.loads(text)
    values = dict(OWN)
    values.update(block_names())
    # (Keys the shared generators own keep the value they wrote)
    for k, v in current.items():
        if owned(k) and k not in values:
            values[k] = v
    # Take every owned line out, then put the block back after the line before level-25
    lines = text.split("\n")
    m = [i for i, line in enumerate(lines) if line.startswith('\t"level-25":')]
    if not m:
        sys.exit("no level-25 line in en.json")
    anchor_key = lines[m[0] - 1]
    kept = [line for line in lines if not (re.match(r'^\t"([^"]+)":', line) and owned(re.match(r'^\t"([^"]+)":', line).group(1)))]
    at = kept.index(anchor_key) + 1
    order = ["level-25", "levelhint-25", "levelname-25"] + [k for k in values if k not in ("level-25", "levelhint-25", "levelname-25")]
    block = ["\t" + json.dumps(k) + ": " + json.dumps(values[k], ensure_ascii=False) + "," for k in order]
    kept[at:at] = block
    out = "\n".join(kept)
    # (Commas: every entry but the last ends in one)
    out = re.sub(r",(\s*\n\})", r"\1", out)
    out = re.sub(r'(")(\s*\n\t")', r'\1,\2', out)
    json.loads(out)
    with open(EN, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print(f"wrote {len(block)} Level 36 lines into lang/en.json")


if __name__ == "__main__":
    main()
