"""Level 36 "Airport" (experimental, id 25): its lang keys in lang/en.json, all in one block after its level-25 lines.

Writes the level's own strings (titles, hints, the airport's messages, block names from gen_36_surfaces.py and
gen_36_props.py), then gathers the keys the shared generators write for the level (its notes from gen_notes.py, its
handbook page from gen_guide.py, the Travel Planner's lines from gen_dialogue.py), wherever they were appended, into the
same block, so the level's strings stay together. Since the links round (2026-10-31) the handbook page itself is written
here (GUIDE_TEXT), over gen_guide.py's. Run it after those generators (tools/gen_36.py does all of it).

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

# The level's handbook page (links, 2026-10-31). It is gen_guide.py's PAGES["level36"] as the links round left it: the links
# brief keeps gen_guide.py out of the level agents' hands, so the page is written here, after gen_guide.py has run, and wins
# (main() below). The lead may move it back into PAGES["level36"] at the merge.
GUIDE_TITLE = "Level 36: the Airport"
GUIDE_TEXT = """
**Level 36, the Timeless Airport**
*An endless terminal, empty and spotless, where every level is one flight away.*

**Arriving**
Most come in like luggage, on a baggage carousel in the claim hall. Behind it is the one wall anyone has found the end of; the hall runs north and south along it as far as you care to walk, a carousel every 32 blocks. Some come in by a door under an airplane sign (see below) and stand in the same hall, beside one of the doors in that wall. The bags on the belts belong to nobody now: [suitcases](block-backrooms:suitcase) give clothes and odds and ends, and the Lost and Found offices along the wall hold more, with a supply box or two.

**The terminal**
East of the claim hall: check-in, rows of desks under flight screens with queue barriers before them, then the old security checkpoint, its scanners dead. Past it the concourses: wide halls every 256 blocks each way, with moving walkways down the north-south ones (some stopped), seats, vending machines and Almond Water fountains along their sides. Between them lie the terminal's wings (a letter A to Z over each one's mouth, its gates numbered within 1 to 60), duty-free streets, food courts, first-class lounges, the Meeting Place, and doors into the back of house: dim service corridors that end nowhere, and vents with fans in them.

**Reading the screens**
A flight screen gives a flight number, a level, a gate and a count in no unit at all. {rightmouse} a screen for the flights of the gates nearest it. The screen at each gate names the level its flights go to, and it is always the same level for that gate: the city, the Suburbs, the Poolrooms, Level 3999, Level 188 or the fields of Level 10.

**Flights**
When a gate's count falls under 1000 it is boarding: {rightmouse} the jet-bridge door in the gate's window wall and you are aboard the plane parked behind it. The same door lets you off again until it leaves. Stay aboard when the count reaches nothing and you fly for about a minute, land, and step off in the level on the gate's screen, on your feet, and always in the same place for that gate. There is no flight back: to return, find your own way in again. The flight at gate C32 of a C wing has been delayed for longer than anyone has counted.

**Time**
The clocks have no hands, or have stopped. Nobody sleeps in the airport: lie down and you are up again at once. Nobody tires either: your Rest stays where it was when you arrived, for as long as you stay. Hunger and thirst go on as anywhere, so eat.

**Food and water**
The vending machines and fountains are free and safe. What was left on the food courts' tables has been there far too long.

**Signs and blackouts**
Further in, the signs contradict each other, and the EXIT signs lead nowhere. A lit sign with nothing on it means trouble ahead. Deeper in, whole stretches of concourse and whole wings are blacked out, and half the back of house is dark; only there, and rarely, does something wait: a Smiler, a Hound or two, a Deathmoth. Nothing hunts where the lights are on. Some stretches of concourse run cold (10 °C) and some warm (28 °C).

**The Absolute Limit**
Far out, every way but back toward the carousels, the walls and floors dissolve into static. Reality thins there: your stability drains while you stand in it.

**People**
The Backrooms Travel Agency keeps a booth in check-in (booth 0 on the line through the middle of the hall, others every 1024 blocks along it) and a desk at every Meeting Place. Its Travel Planner talks, gives advice, and trades: travel goods for the junk of the terminal. The Gate C32 Support Group's things are at their gate; they are never in.

**Ways in and out**
In: very rarely, in the city or in the Suburbs, a plain stretch of wall has a door in it under a lit sign with an airplane on it, where no door should be. {rightmouse} it and you are in the claim hall, beside a door under the same sign in the baggage wall; that door takes you back out where you came in. The other doors in that wall are locked. Out: the gates' flights, one way, each to its own level. And a restroom sink (there is a pair of restrooms in every wing, and showers in the lounges): turn the tap and it runs over and will not stop; hold your head under ({rightmouse}, held) and you come up in the Poolrooms, one way. Wanderers also tell of a train from somewhere called the Metro, apartment doors in a part of the city nobody here has found, luggage that falls, and a hotel's glass doors that lead elsewhere. None of those has been seen here.
"""



def owned(key):
    return (key in OWN or key.startswith(("block-l36-", "l36-", "blockhelp-l36-", "level-25", "note-l36-", "notetitle-l36-", "note-r-l36-",
                                          "notetitle-r-l36-", "journal-track-l36", "guide-level36-"))
            or re.match(r"dialogue-wanderer-.*-36$", key) is not None)


def block_names():
    names = {}
    for mod in ("gen_36_surfaces", "gen_36_props"):
        names.update(__import__(mod).NAMES)
    return names


def main():
    with open(EN, encoding="utf-8") as f:
        text = f.read()
    current = json.loads(text)
    values = dict(OWN)
    values.update(block_names())
    # (The handbook page: see GUIDE_TEXT)
    from gen_guide import to_vtml
    values["guide-level36-title"] = GUIDE_TITLE
    values["guide-level36-text"] = to_vtml(GUIDE_TEXT)
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
