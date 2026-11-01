"""Level 36 "Airport" (experimental, id 25): every asset of the level, and its lang block.

    gen_36_surfaces.py   floors, walls, the painted runway windows, ceilings and lights, the carousels' belts, the cabin's
                         walls, clocks, gate and wayfinding signs, shop fascias, flight screens, the Absolute Limit's static
    gen_36_detail.py     (round 3) departures boards, posters, menus, the plane at the gate, the meeting-point sign,
                         coffers, skylights, travertine; charging posts, payphones, ATMs, fountains, shoe-shine chairs, cubicles
    gen_36_props.py      check-in desks, gate seats and podiums, jet-bridge doors, queue barriers, the security lane, the
                         Travel Agency's booth, perfume counters, food-court tables, the meeting point, cabin seats, Lost and Found
    gen_36_sounds.py     the terminal's bed, the carousels, static, the cabin, the back of house; PA chimes and announcements,
                         distant jets, the flight's ding and touchdown
    gen_36_lang.py       the level's strings in lang/en.json, in one block (run last: after gen_notes.py, gen_guide.py and
                         gen_dialogue.py, which write the level's notes, handbook page and Travel Planner's lines)

Run from the repo root, through the asset lock:  bash tools/locked.sh run python tools/gen_36.py [--no-sounds]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import gen_36_detail  # noqa: E402
import gen_36_lang  # noqa: E402
import gen_36_props  # noqa: E402
import gen_36_surfaces  # noqa: E402


def main():
    gen_36_surfaces.main()
    gen_36_props.main()
    gen_36_detail.main()   # (round 3: the wall pictures, the plane at the gate, the meeting-point sign, finishes, new props)
    if "--no-sounds" not in sys.argv:
        import gen_36_sounds
        gen_36_sounds.main()
    gen_36_lang.main()


if __name__ == "__main__":
    main()
