"""Level 3999, the Neon Paradise: the arcade (docs/new-levels/3999-plan.md 6.3). Called from gen_3999.py.

Cabinets share one body, modelled in boxes facing north: a lower body with a coin door, a control panel with a
joystick and four buttons, a screen in a bezel leaning back 15 degrees, a lit marquee box projecting a pixel, side
panels carrying the side art, and neon T-moulding along the panels' front edges. Then the themed, rusted and dead
cabinets, the racer, the dance machine, pinball, the claw machine, skee-ball, air hockey, the prize counters and
wall, the abandoned prize case of 3999.1 and the prize plushes.

The machines are part of the building (never broken), except the dead ones, the air hockey table and the prize case
(salvage) and the plushes (prizes you carry away).
"""
from gen_3999_kit import (CLOTH, COLOURS, FIXED, GLASS, LANG, METAL, NEON, SIDES, WOOD, bx, cuboid, cyl, drops, faces_box, glass,
                          hang, hsv, mirror_x, move, picture, rot, scale_els, threshold, turn, variants_block, with_class)

GAME_COLOURS = {"a": ("magenta", "cyan"), "b": ("orange", "pink"), "c": ("lilac", "orange"), "d": ("blue", "orange"),
                "e": ("cyan", "orange"), "f": ("pink", "blue")}
GAME_NAMES = {"a": "Galaxia 3999", "b": "Neon Rally", "c": "Dungeon Byte", "d": "Robo Brawl", "e": "Sky Jouster", "f": "Maze Muncher"}
THEMED = {"l4": ("4", "blue", "Cubicle Chaos"), "l5": ("5", "pink", "Check Out"), "l6": ("6", "lilac", "Lights Out"),
          "l7": ("7", "blue", "Deep Blue"), "l9": ("9", "orange", "Cul-de-Sac"), "l10": ("10", "orange", "Harvest"),
          "l11": ("11", "cyan", "Metropolis"), "l37": ("37", "cyan", "Pool Party"), "l94": ("94", "lilac", "Claymation"),
          "run": ("!", "pink", "Run!"), "fun": ("Fun", "magenta", "=)"), "kitty": ("974", "lilac", "Kitty")}


def side_uv(z1, z2, y1, y2, face):
    """The slice of the side art (24 x 56, the panel's z 3..15 by y 0..28) under one side box. Seen from outside, the
    west face's left edge is the front, the east face's left edge the back, so the art reads the right way on both."""
    v1, v2 = (28 - y2) / 28 * 16, (28 - y1) / 28 * 16
    if face == "west":
        u1, u2 = (z1 - 3) / 12 * 16, (z2 - 3) / 12 * 16
    else:
        u1, u2 = (15 - z2) / 12 * 16, (15 - z1) / 12 * 16
    clampu = lambda u: round(max(0, min(16, u)), 3)
    return [clampu(u1), round(v1, 3), clampu(u2), round(v2, 3)]


def side_panels(side_tex, trim, glow=255):
    els = []
    profile = [("Low", 0, 14, 3, 15), ("Up", 14, 23, 5, 15), ("Top", 23, 28, 2, 15)]
    for sx, (x1, x2), face in (("W", (1.5, 2.5), "west"), ("E", (13.5, 14.5), "east")):
        for nm, y1, y2, z1, z2 in profile:
            el = bx(f"Side{sx}{nm}", (x1, y1, z1), (x2, y2, z2), "black", faces=("north", "east", "west", "up", "down", "south"))
            el["faces"][face] = {"texture": "#" + side_tex, "uv": side_uv(z1, z2, y1, y2, face)}
            inner = "east" if face == "west" else "west"
            el["faces"][inner]["texture"] = "#black"
            els.append(el)
        tx1, tx2 = x1 - 0.2, x2 + 0.2
        for nm, (a, b) in (("TLow", ((tx1, 0, 2.7), (tx2, 14, 3.1))), ("TUp", ((tx1, 14, 4.7), (tx2, 23, 5.1))),
                           ("TTop", ((tx1, 23, 1.7), (tx2, 28.2, 2.1))), ("TCrest", ((tx1, 27.9, 2.1), (tx2, 28.3, 15))),
                           ("TStep", ((tx1, 22.8, 2.1), (tx2, 23.2, 5))), ("TBack", ((tx1, 0, 14.9), (tx2, 28, 15.3)))):
            els.append(bx(f"{nm}{sx}", a, b, trim, glow=glow))
    return els


def cabinet(screen, marquee, side, body, cpanel, trim, buttons=("magenta", "cyan"), lit=True, missing_button=False, dusty=False):
    g = 255 if lit else 0
    els = [faces_box("Lower", (2, 0, 3), (14, 14, 15), {"north": body, "south": body, "down": body}),
           picture(bx("CoinDoor", (5, 3.5, 2.6), (11, 9.5, 3), body, faces=("north", "east", "west", "up", "down")), "coindoor"),
           bx("Kick", (2, 0, 2.6), (14, 1.5, 3), "black"),
           faces_box("Panel", (1.4, 14, 0.5), (14.6, 16, 6), {"up": cpanel, "north": "black", "east": "black", "west": "black", "down": "black"}),
           bx("Back", (2.5, 14, 9), (13.5, 28, 15), body, faces=("south", "up")),
           faces_box("UnderMarquee", (2.5, 22, 2), (13.5, 23, 6), {"down": "black", "north": "black"})]
    els[-3]["faces"]["up"]["uv"] = [0, 0, 16, 16]
    # Screen: a bezel leaning back 15 degrees, the picture set into it
    bezel = bx("Bezel", (2.5, 15, 6), (13.5, 22.5, 9), "black")
    scr = picture(bx("Screen", (3.6, 16, 5.9), (12.4, 21.6, 6), "black", faces=("north",)), screen, glow=g)
    els += [rot(bezel, rx=15, origin=(8, 15, 7.5)), rot(scr, rx=15, origin=(8, 15, 7.5))]
    # Marquee box, projecting a pixel past the body
    mq = picture(bx("Marquee", (2.5, 23.2, 2), (13.5, 27.8, 5), body, faces=("north", "down")), marquee, glow=200 if lit else 0)
    els += [mq, bx("Crest", (2.5, 27.8, 2), (13.5, 28, 15), "black", faces=("up",))]
    # Joystick (player one, on the left as seen from the front: +X) and four buttons
    els += [bx("StickBase", (9.9, 16, 1.9), (12.1, 16.3, 4.1), "darksteel"), bx("Stick", (10.6, 16.3, 2.6), (11.4, 19, 3.4), "stick"),
            bx("Ball", (10, 19, 2), (12, 21, 4), "joyball")]
    spots = [(7, 2), (5, 2.6), (3, 3.2), (6, 4.4)]
    for i, (x, z) in enumerate(spots):
        if missing_button and i == 1:
            els.append(bx(f"Hole{i}", (x, 15.95, z), (x + 1.2, 16.05, z + 1.2), "black", faces=("up",)))
            continue
        c = buttons[i % 2]
        els.append(bx(f"Button{i}", (x, 16, z), (x + 1.2, 16.8, z + 1.2), f"neon-{c}" if lit else f"neondim-{c}", glow=140 if lit else 0))
    els += side_panels(side, trim, glow=g)
    if dusty:
        els.append(bx("Dust", (1.6, 16.02, 0.6), (14.4, 16.1, 5.9), "dust", faces=("up",)))
    return els


CAB_BOX = (0.09, 0, 0.03, 0.91, 1.75, 0.94)


def cabinets():
    def build(v):
        g = v["game"]
        c1, c2 = GAME_COLOURS[g]
        return cabinet(f"cab-{g}-screen", f"cab-{g}-marquee", f"cab-{g}-side", f"cab-{g}-body", f"cpanel-{g}", f"neon-{c1}", (c1, c2))

    variants_block("l3999-cabinet", "Arcade Cabinet", [("game", list(GAME_COLOURS)), ("facing", SIDES)], build, rot="facing",
                   box=CAB_BOX, material="Wood",
                   data=with_class({"lightHsvByType": {f"*-{g}-*": hsv(c1, 6) for g, (c1, _) in GAME_COLOURS.items()}, "drops": [],
                                    "attributes": dict(FIXED, l3999cabinet={"seconds": 4, "min": 0, "max": 3, "jackpot": 12, "jackpotChance": 0.03})},
                                   cls="BackroomsArcadeCabinet", entity="BackroomsArcadeCabinet"),
                   comment="Level 3999: an upright arcade cabinet facing the way named, six invented games (a GALAXIA 3999, b NEON RALLY, "
                           "c DUNGEON BYTE, d ROBO BRAWL, e SKY JOUSTER, f MAZE MUNCHER), each with its marquee, screen, side art and neon "
                           "T-moulding. Hold to play (4 s); pays 0-3 tickets once a day (attributes.l3999cabinet; screen light 6)",
                   names={f"l3999-cabinet-{g}-*": f"Arcade Cabinet ({n})" for g, n in GAME_NAMES.items()})

    def themed(v):
        t = v["level"]
        c = THEMED[t][1]
        return cabinet(f"cab-{t}-screen", f"cab-{t}-marquee", f"cab-{t}-side", "cab-themed-body", "cpanel-themed", f"neon-{c}", (c, "lilac"))

    variants_block("l3999-themed", "Themed Arcade Cabinet", [("level", list(THEMED)), ("facing", SIDES)], themed, rot="facing",
                   box=CAB_BOX, material="Wood",
                   data={"behaviors": threshold("l3999-cabinet"), "lightHsvByType": {f"*-{t}-*": hsv(c, 7) for t, (_, c, _) in THEMED.items()},
                         "drops": [], "attributes": dict(FIXED, l3999themed={t: lvl for t, (lvl, _, _) in THEMED.items()}, l3999playSeconds=20)},
                   comment="Level 3999: a themed cabinet whose marquee names another level and whose screen shows it (CUBICLE CHAOS 4, CHECK "
                           "OUT 5, LIGHTS OUT 6, DEEP BLUE 7, CUL-DE-SAC 9, HARVEST 10, METROPOLIS 11, POOL PARTY 37, CLAYMATION 94, RUN! !, "
                           "=) Fun, KITTY 974). Played to the end (20 s), the game takes you there (threshold kind l3999-cabinet; light 7)",
                   names={f"l3999-themed-{t}-*": f"Arcade Cabinet ({n})" for t, (_, _, n) in THEMED.items()})

    variants_block("l3999-cabinet-rusted", "Rusted Arcade Cabinet", [("facing", SIDES)],
                   lambda v: cabinet("screen-rust", "cab-rust-marquee", "cab-rust-side", "cab-rust-body", "cpanel-dead", "darksteel",
                                     ("orange", "pink"), lit=False, missing_button=True, dusty=True),
                   rot="facing", box=CAB_BOX, collide=False, material="Wood",
                   data={"drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a rusted cabinet, the screen dark but for dead pixels, the marquee peeling. It looks solid but is "
                           "not: walk into it and you fall through into Level 3999.1")

    variants_block("l3999-cabinet-dead", "Dead Arcade Cabinet", [("facing", SIDES)],
                   lambda v: cabinet("screen-cracked", "cab-dead-marquee", "cab-dead-side", "cab-dead-body", "cpanel-dead", "neon-dead",
                                     ("blue", "orange"), lit=False, missing_button=True, dusty=True),
                   rot="facing", box=CAB_BOX, material="Wood",
                   data={"resistance": 3, "drops": drops(("scrapwire", 2, 0.5), ("glassshard", 1, 0.5), ("metalbracket", 1, 0.5),
                                                         ("l3999-circuitboard", 1, 0.3), ("l3999-coinmech", 0.6, 0.2), ("l3999-plastic", 1, 0.5),
                                                         ("l3999-ticket", 0.5, 0.5))},
                   comment="Level 3999.1: a dead cabinet, cracked screen, dust on the panel, a button missing, no light. Salvage: wire, glass, "
                           "brackets, a circuit board, the coin mechanism, plastic, a few tickets left in the hopper")


def games():
    # ---- The racer: a seat, and the hooded screen in front of it
    def racer(v):
        if v["part"] == "seat":
            els = [bx("Frame", (1, 0, 1), (15, 2, 15), "black"), bx("Base", (3, 2, 5), (13, 6, 14), "racer-body"),
                   bx("Seat", (3.5, 6, 5), (12.5, 8, 13), "vinyl-black"),
                   rot(bx("Back", (3.5, 7, 12), (12.5, 20, 14.5), "vinyl-black"), rx=12, origin=(8, 7, 13)),
                   rot(bx("BolsterL", (11.5, 7, 6), (13.5, 10, 13), "vinyl-black"), rz=-8, origin=(12.5, 7, 9)),
                   rot(bx("BolsterR", (2.5, 7, 6), (4.5, 10, 13), "vinyl-black"), rz=8, origin=(3.5, 7, 9)),
                   bx("PedalBox", (4, 2, 1), (12, 5, 3.5), "racer-body"),
                   rot(bx("Gas", (5, 4, 1.5), (7.5, 4.6, 3.5), "darksteel"), rx=-30, origin=(6, 4, 3)),
                   rot(bx("Brake", (8.5, 4, 1.5), (11, 4.6, 3.5), "darksteel"), rx=-30, origin=(10, 4, 3)),
                   bx("NeonL", (14.9, 0.5, 1), (15.2, 1.5, 15), "neon-pink", glow=255), bx("NeonR", (0.8, 0.5, 1), (1.1, 1.5, 15), "neon-pink", glow=255)]
            return els
        els = [bx("Body", (0, 0, 5), (16, 26, 16), "racer-body"), bx("Hood", (-0.5, 26, 0.5), (16.5, 31, 16), "racer-body"),
               picture(bx("Marquee", (0.5, 26.4, 0.4), (15.5, 30.6, 0.5), "black", faces=("north",)), "racer-marquee", glow=200),
               bx("Recess", (1, 11, 4.9), (15, 26, 5), "black", faces=("north",)),
               picture(bx("Screen", (1.5, 12, 4.8), (14.5, 25, 4.9), "black", faces=("north",)), "racer-screen", glow=255),
               bx("CheekL", (14.5, 11, 0.5), (16, 26, 5), "racer-body"), bx("CheekR", (0, 11, 0.5), (1.5, 26, 5), "racer-body"),
               bx("Dash", (0.5, 6, 0), (15.5, 11, 5), "black"), bx("DashTop", (0.5, 11, 0), (15.5, 11.5, 5), "racer-body"),
               rot(bx("Column", (7.3, 9, -2), (8.7, 10.4, 1), "darksteel"), rx=-25, origin=(8, 9.7, 0))]
        # The steering wheel: a 10 px ring of four bars and two spokes, tilted back
        ring = [bx("WheelT", (3, 14, -2.6), (13, 15.2, -1.6), "rubber"), bx("WheelB", (3, 4.8, -2.6), (13, 6, -1.6), "rubber"),
                bx("WheelL", (11.8, 6, -2.6), (13, 14, -1.6), "rubber"), bx("WheelR", (3, 6, -2.6), (4.2, 14, -1.6), "rubber"),
                bx("Spoke1", (4.2, 9.4, -2.4), (11.8, 10.6, -1.8), "darksteel"), bx("Spoke2", (7.4, 6, -2.4), (8.6, 9.4, -1.8), "darksteel"),
                bx("Hub", (6.8, 8.8, -2.8), (9.2, 11.2, -1.6), "neon-orange")]
        els += [rot(e, rx=-25, origin=(8, 10, -2)) for e in ring]
        els += [bx("GearBase", (13, 6, -1), (15, 6.6, 1), "darksteel"), rot(bx("Gear", (13.6, 6.6, -0.4), (14.4, 10, 0.4), "stick"), rx=-10, origin=(14, 6.6, 0)),
                bx("GearKnob", (13.3, 9.8, -0.9), (14.7, 11.2, 0.5), "joyball"),
                bx("NeonL", (16, 0, 5), (16.3, 26, 5.6), "neon-cyan", glow=255), bx("NeonR", (-0.3, 0, 5), (0, 26, 5.6), "neon-cyan", glow=255)]
        return els

    variants_block("l3999-racer", "Racing Cabinet", [("part", ["seat", "screen"]), ("facing", SIDES)], racer, rot="facing",
                   boxes=lambda v: (0.06, 0, 0.06, 0.94, 0.9, 0.94) if v["part"] == "seat" else (0, 0, 0, 1, 1.9, 1), material="Wood",
                   data=with_class({"lightHsvByType": {"*-screen-*": [3, 7, 7]}, "drops": [],
                                    "attributesByType": {
                                        "*-screen-*": dict(FIXED, l3999cabinet={"seconds": 10, "min": 1, "max": 5, "jackpot": 12, "jackpotChance": 0.03}),
                                        "*": dict(FIXED)}}, cls="BackroomsArcadeCabinet", entity="BackroomsArcadeCabinet"),
                   comment="Level 3999: NEON RALLY, a sit-down racer. seat: a bucket seat with pedals, the player looking the way named; "
                           "screen: a hooded screen with a steering wheel and a gear lever, its front facing the way named (put it in front of "
                           "the seat, facing it). Hold the screen to play (10 s, pays 1-5)")

    def dance(v):
        if v["part"] == "pad":
            els = [faces_box("Pad", (0, 0, 0), (16, 2, 16), {"up": "arrowpad", "north": "darksteel", "east": "darksteel", "south": "darksteel",
                                                             "west": "darksteel", "down": "darksteel"}, glow_by_face={"up": 120})]
            els[0]["faces"]["up"]["uv"] = [0, 0, 16, 16]
            els += [bx("PostL", (14.5, 2, 14), (15.5, 16, 15), "chrome"), bx("PostR", (0.5, 2, 14), (1.5, 16, 15), "chrome"),
                    bx("Bar", (0.5, 15, 13.8), (15.5, 16.2, 15.2), "rubber")]
            return els
        els = [bx("Tower", (2, 0, 6), (14, 32, 16), "dance-body"),
               picture(bx("Screen", (3, 12, 5.8), (13, 26, 6), "black", faces=("north",)), "dance-screen", glow=255),
               picture(bx("Marquee", (2, 27, 4.5), (14, 32, 6), "dance-body", faces=("north", "down", "up", "east", "west")), "dance-marquee", glow=200)]
        for sx, (x1, x2) in (("L", (14, 16.5)), ("R", (-0.5, 2))):
            els += [picture(bx(f"Speaker{sx}", (x1, 0, 6.5), (x2, 14, 13), "darksteel"), "speaker"),
                    bx(f"Neon{sx}", (x1, 14, 6.5), (x2, 14.6, 13), "neon-magenta", glow=255)]
        return els

    variants_block("l3999-dance", "Dance Machine", [("part", ["pad", "screen"]), ("facing", SIDES)], dance, rot="facing",
                   boxes=lambda v: (0, 0, 0, 1, 0.125, 1) if v["part"] == "pad" else (0, 0, 0.3, 1, 1.9, 1), material="Metal", sounds=METAL,
                   data=with_class({"lightHsvByType": {"*-pad-*": [51, 6, 4], "*-screen-*": [62, 7, 7]}, "drops": [],
                                    "attributesByType": {
                                        "*-screen-*": dict(FIXED, l3999cabinet={"seconds": 10, "min": 1, "max": 5, "jackpot": 12, "jackpotChance": 0.03}),
                                        "*": dict(FIXED)}}, cls="BackroomsArcadeCabinet", entity="BackroomsArcadeCabinet"),
                   comment="Level 3999: NEON STEP, a dance machine. pad: a platform with four glowing arrow panels and a safety bar behind "
                           "(the dancer looks the way named); screen: a tall tower with speakers, its front facing the way named. Hold the "
                           "screen to play (10 s, pays 1-5)")

    def pinball(v):
        els = []
        for x in (2.5, 12.5):
            for z in (1, 14):
                els.append(bx(f"Leg{x}{z}", (x, 0, z), (x + 1, 8, z + 1), "chrome"))
        table = [faces_box("Table", (2, 8, 0), (14, 12, 16), {"up": "playfield", "north": "pinball-body", "east": "pinball-body",
                                                            "west": "pinball-body", "south": "pinball-body", "down": "pinball-body"}),
                 glass(bx("Glass", (2.5, 12.6, 0.5), (13.5, 12.7, 15.5), "glasspane", faces=("up",))),
                 bx("RailL", (13.4, 12, 0), (14, 13, 16), "chrome"), bx("RailR", (2, 12, 0), (2.6, 13, 16), "chrome"),
                 bx("RailF", (2, 12, 0), (14, 13, 0.6), "chrome")]
        table[0]["faces"]["up"]["uv"] = [0, 0, 16, 16]
        els += [rot(e, rx=-4, origin=(8, 8, 16)) for e in table]
        els += [faces_box("Backbox", (2, 13, 13), (14, 25, 16), {"north": "backbox", "east": "pinball-body", "west": "pinball-body",
                                                                "south": "pinball-body", "up": "pinball-body"}, glow_by_face={"north": 200}),
                bx("Plunger", (11.5, 9, -1.2), (12.5, 10, 0), "chrome"), bx("FlipL", (14, 9.5, 1.5), (14.4, 10.5, 2.5), "neon-pink", glow=150),
                bx("FlipR", (1.6, 9.5, 1.5), (2, 10.5, 2.5), "neon-pink", glow=150)]
        els[-4]["faces"]["north"]["uv"] = [0, 0, 16, 16]
        return els

    variants_block("l3999-pinball", "Pinball Table", [("facing", SIDES)], pinball, rot="facing", box=(0.12, 0, 0, 0.88, 0.85, 1), material="Wood",
                   data=with_class({"lightHsv": [33, 6, 5], "drops": [],
                                    "attributes": dict(FIXED, l3999cabinet={"seconds": 6, "min": 0, "max": 4, "jackpot": 12, "jackpotChance": 0.03})},
                                   cls="BackroomsArcadeCabinet", entity="BackroomsArcadeCabinet"),
                   comment="Level 3999: COMET, a pinball table on four legs, a glass top over the playfield, the backbox at the rear (the "
                           "player stands on the side named). Hold to play (6 s, pays 0-4; light 5)")

    def claw(v):
        els = [bx("Base", (1, 0, 1), (15, 10, 15), "claw-body"),
               picture(bx("Chute", (10, 2, 0.6), (14, 7, 1), "black", faces=("north",)), "chute"),
               bx("PanelBox", (3, 8, -1), (13, 10.5, 1), "claw-body"), bx("Stick", (9.6, 10.5, -0.4), (10.4, 13, 0.4), "stick"),
               bx("Ball", (9.2, 13, -0.8), (10.8, 14.6, 0.8), "joyball"), bx("Button", (5, 10.5, -0.5), (6.5, 11.2, 0.5), "neon-cyan", glow=150)]
        for i, (x, z) in enumerate(((1, 1), (14, 1), (1, 14), (14, 14))):
            els.append(bx(f"Post{i}", (x, 10, z), (x + 1, 28, z + 1), "chrome"))
        for nm, a, b in (("PaneN", (2, 10, 1.4), (14, 28, 1.6)), ("PaneS", (2, 10, 14.4), (14, 28, 14.6)),
                         ("PaneE", (14.4, 10, 2), (14.6, 28, 14)), ("PaneW", (1.4, 10, 2), (1.6, 28, 14))):
            els.append(glass(bx(nm, a, b, "glasspane", faces=("north", "south", "east", "west"))))
        els += [bx("Top", (0.6, 28, 0.6), (15.4, 31, 15.4), "claw-body"),
                picture(bx("Marquee", (1, 28.3, 0.4), (15, 30.7, 0.6), "black", faces=("north",)), "claw-marquee", glow=200),
                bx("Floor", (2, 10, 2), (14, 10.5, 14), "black", faces=("up",))]
        # A heap of plush inside
        heap = [("pink", 2, 2, 6, 4), ("blue", 7, 3, 5, 3.5), ("smiley", 3, 7, 5, 3), ("alien", 9, 8, 5, 4), ("cat", 5, 10, 5, 3.2),
                ("purple", 10, 2.5, 3.5, 2.5), ("bear", 2, 10.5, 3.5, 3), ("white", 8, 6, 3, 5)]
        for i, (col, x, z, w, h) in enumerate(heap):
            els.append(bx(f"Plush{i}", (x, 10.5, z), (x + w, 10.5 + h, z + w * 0.9), f"fur-{col}"))
        # The gantry, the cable and a three-pronged claw
        els += [bx("RailA", (2, 26.5, 3), (14, 27.2, 3.8), "chrome"), bx("RailB", (2, 26.5, 12.2), (14, 27.2, 13), "chrome"),
                bx("Carriage", (6, 26.3, 3), (9, 27.4, 13), "darksteel"), bx("Trolley", (6.5, 25.6, 7), (8.5, 26.3, 9), "darksteel"),
                bx("Cable", (7.4, 21, 7.9), (7.6, 25.6, 8.1), "darksteel"), bx("ClawHub", (6.7, 20, 7.2), (8.3, 21.2, 8.8), "chrome")]
        for k in range(3):
            prong = bx(f"Prong{k}", (7.3, 16.5, 8.6), (7.7, 20.2, 9), "chrome")
            els.append(rot(prong, rx=-18, ry=k * 120, origin=(7.5, 20.2, 8)))
        return els

    variants_block("l3999-claw", "Claw Machine", [("facing", SIDES)], claw, rot="facing", box=(0.06, 0, 0.06, 0.94, 1.94, 0.94), material="Glass",
                   sounds=GLASS,
                   data=with_class({"lightHsv": [53, 3, 6], "drops": [],
                                    "attributes": dict(FIXED, l3999cabinet={"seconds": 6, "min": 0, "max": 0, "plushChance": 0.25,
                                                                            "plush": ["l3999-plush-bear-north", "l3999-plush-cat-north",
                                                                                      "l3999-plush-alien-north", "l3999-plush-smiley-north"]})},
                                   cls="BackroomsArcadeCabinet", entity="BackroomsArcadeCabinet"),
                   comment="Level 3999: GRAB-A-PRIZE, a claw machine: a glass box heaped with plush, a gantry and a three-pronged claw, a "
                           "control panel on the side named. 1 play in 4 wins a plush instead of tickets (light 6)")

    def skee(v):
        if v["part"] == "lane":
            import math
            a = math.degrees(math.atan2(6, 16))
            lane = faces_box("Lane", (2, 1, 0), (14, 2.5, 17), {"up": "lanewood", "north": "skee-body", "south": "skee-body"})
            els = [bx("Body", (1, 0, 0), (15, 1, 16), "skee-body"), rot(lane, rx=-a, origin=(8, 2, 0)),
                   bx("SideL", (14, 0, 3), (16, 10, 16), "slat"), bx("SideR", (0, 0, 3), (2, 10, 16), "slat"),
                   bx("NeonL", (14, 10, 3), (16, 10.6, 16), "neon-lilac", glow=255), bx("NeonR", (0, 10, 3), (2, 10.6, 16), "neon-lilac", glow=255),
                   bx("Trough", (1, 0, 0), (15, 4, 3), "skee-body"), bx("TroughIn", (2, 3.5, 0.5), (14, 4.01, 2.5), "black", faces=("up",))]
            for i, x in enumerate((3, 5.5, 8, 10.5)):
                els.append(bx(f"Ball{i}", (x, 4, 0.8), (x + 2, 6, 2.8), "skeeball-ball"))
            return els
        tgt = faces_box("Target", (0, 0, 2), (16, 22, 16), {"north": "skee-target", "east": "skee-body", "west": "skee-body",
                                                            "south": "skee-body", "up": "skee-body"}, glow_by_face={"north": 90})
        tgt["faces"]["north"]["uv"] = [0, 0, 16, 16]
        score = picture(bx("Score", (1, 22, 2), (15, 27, 5), "skee-body", faces=("north", "up", "east", "west")), "skee-score", glow=255)
        return [rot(tgt, rx=12, origin=(8, 0, 2)), score,
                bx("ScoreBack", (1, 22, 5), (15, 27, 16), "skee-body"),
                bx("NeonT", (0.6, 26.6, 1.6), (15.4, 27.2, 2.2), "neon-pink", glow=255)]

    variants_block("l3999-skeeball", "Skee-Ball", [("part", ["lane", "target"]), ("facing", SIDES)], skee, rot="facing",
                   boxes=lambda v: (0, 0, 0, 1, 0.65, 1) if v["part"] == "lane" else (0, 0, 0.12, 1, 1.7, 1), material="Wood",
                   data=with_class({"lightHsvByType": {"*-target-*": [62, 7, 5], "*-lane-*": [53, 3, 3]}, "drops": [],
                                    "attributesByType": {
                                        "*-target-*": dict(FIXED, l3999cabinet={"seconds": 10, "min": 1, "max": 5, "jackpot": 12, "jackpotChance": 0.03}),
                                        "*": dict(FIXED)}}, cls="BackroomsArcadeCabinet", entity="BackroomsArcadeCabinet"),
                   comment="Level 3999: skee-ball. lane: a wooden ramp rising toward the back, a ball trough at the front (the player stands "
                           "on the side named); target: rings and holes worth 10 to 100 under a score display, its face toward the way named "
                           "(put it at the far end of the lane, facing it). Hold the target to play (10 s, pays 1-5)")

    def airhockey(v):
        els = [faces_box("Top", (0, 10, 0), (16, 11, 16), {"up": "airtable", "north": "airrim", "east": "airrim", "west": "airrim", "south": "airrim"}),
               bx("Body", (0.5, 4, 0.5), (15.5, 10, 16), "airrim"), bx("Foot", (2, 0, 2), (14, 4, 15), "darksteel"),
               bx("RimL", (15, 11, 0), (16, 12.5, 16), "airrim"), bx("RimR", (0, 11, 0), (1, 12.5, 16), "airrim"),
               bx("RimF", (1, 11, 0), (16, 12.5, 1), "airrim"), bx("Goal", (5, 10.9, 0.2), (11, 11.6, 1.1), "black"),
               bx("Mallet", (6.5, 11, 4), (9.5, 11.8, 7), "neon-pink" if v["half"] == "a" else "neon-blue", glow=80),
               bx("Grip", (7.4, 11.8, 4.9), (8.6, 13.4, 6.1), "rubber")]
        els[0]["faces"]["up"]["uv"] = [0, 0, 16, 16]
        if v["half"] == "a":
            els.append(bx("Puck", (9, 11, 10), (11, 11.4, 12), "puck"))
        return els

    variants_block("l3999-airhockey", "Air Hockey Table", [("half", ["a", "b"]), ("facing", SIDES)], airhockey, rot="facing",
                   boxes=lambda v: (0, 0, 0, 1, 0.78, 1), material="Wood",
                   data={"drops": drops(("l3999-plastic", 2, 1), ("metalbracket", 1, 0.5), ("scrapwire", 0.5, 0.5), ("l3999-coinmech", 0.4, 0))},
                   rot_offset=0,
                   comment="Level 3999: an air hockey table two blocks long, a white top and a rim, a mallet on each half and the puck on "
                           "a. Each half's goal is on the side it faces: put b beside a's back edge, facing the opposite way. Salvage: "
                           "plastic, brackets, wire, the coin mechanism")

    # ---- Prizes
    def prizes_inside(seed=0, few=False):
        els = []
        spots = [(2.5, 3, "fur-pink", 2.6), (5.8, 4, "fur-blue", 2.2), (9, 2.8, "fur-smiley", 2.4), (12, 4.2, "fur-alien", 2),
                 (3.5, 8, "toybox-0", 2.8), (7.5, 8.5, "fur-cat", 2.4), (11, 8, "toybox-1", 2.8), (5, 12, "fur-bear", 2.6), (10.5, 12, "toybox-2", 2.6)]
        for i, (x, z, t, s) in enumerate(spots):
            if few and i % 2:
                continue
            els.append(bx(f"Prize{i}", (x, 9, z), (x + s, 9 + s * 0.9, z + s), t))
        return els

    def counter(v):
        els = [faces_box("Base", (0, 0, 1), (16, 9, 16), {"north": "laminate", "east": "laminate", "west": "laminate", "south": "laminate", "down": "laminate"}),
               bx("Kick", (0, 0, 0.6), (16, 1, 1), "black"), bx("EdgeT", (0, 8.6, 0.6), (16, 9.2, 16), "chrome", faces=("north", "up", "east", "west")),
               tube_strip("Strip", (0, 7.5, 0.7), (16, 8.1, 1), "lilac")]
        els += prizes_inside()
        els += [glass(bx("GlassF", (0.2, 9.2, 0.8), (15.8, 13.8, 1), "glasspane", faces=("north", "south"))),
                glass(bx("GlassT", (0.2, 13.8, 0.8), (15.8, 14, 15.8), "glasspane", faces=("up", "down"))),
                bx("PostL", (15.2, 9.2, 0.6), (16, 14.2, 1.4), "chrome"), bx("PostR", (0, 9.2, 0.6), (0.8, 14.2, 1.4), "chrome"),
                bx("TopRail", (0, 13.8, 0.6), (16, 14.4, 1.4), "chrome"), bx("BackT", (0, 13.8, 15.2), (16, 14.4, 16), "chrome")]
        return els

    prize_data = prize_tiers()
    variants_block("l3999-prizecounter", "Prize Counter", [("facing", SIDES)], counter, rot="facing", box=(0, 0, 0.03, 1, 0.9, 1), material="Glass",
                   sounds=GLASS,
                   data=with_class({"lightHsv": [53, 3, 6], "drops": [], "attributes": dict(FIXED, l3999prizes=prize_data)},
                                   cls="BackroomsPrizeCounter", entity="BackroomsPrizeCounter"),
                   comment="Level 3999: a prize counter: purple laminate, a chrome edge, a glass case of plush and boxed toys (its customer "
                           "side faces the way named; an attendant stands behind it). Tickets buy prizes by tier (attributes.l3999prizes: "
                           "5, 15, 40, 200 tickets; light 6)")

    def prizewall(v):
        els = [bx("Board", (0, 0, -1), (16, 32, 0), "pegboard"),
               bx("Shelf1", (0, 14, -5), (16, 15, -1), "laminate"), bx("Shelf2", (0, 25, -5), (16, 26, -1), "laminate"),
               bx("Edge1", (0, 14, -5.4), (16, 15, -5), "neon-cyan", glow=180), bx("Edge2", (0, 25, -5.4), (16, 26, -5), "neon-cyan", glow=180)]
        # A giant bear sitting on the floor, plush hanging on pegs, boxed toys on the shelves
        els += [move([e], dz=-6)[0] for e in scale_els(plush_els("bear"), 1.5, at=(8, 0, 0))]
        for i, (x, col) in enumerate(((2, "pink"), (6, "blue"), (10.5, "purple"))):
            els += [bx(f"Peg{i}", (x + 1.2, 21.5, -2), (x + 1.8, 22, -1), "chrome"),
                    bx(f"Hang{i}", (x, 17.5, -3.6), (x + 3, 21.5, -1.6), f"fur-{col}"),
                    bx(f"HangHead{i}", (x + 0.4, 21, -3.4), (x + 2.6, 23, -1.8), f"fur-{col}")]
        for i, (x, t) in enumerate(((1, "toybox-0"), (6, "toybox-1"), (11, "toybox-2"))):
            els.append(picture(bx(f"Box{i}", (x, 26, -4.5), (x + 4, 31, -1.5), t), t))
        return hang(els)

    variants_block("l3999-prizewall", "Prize Wall", [("facing", SIDES)], prizewall, rot="facing", box=(0, 0, 0.62, 1, 1, 1), material="Wood",
                   data={"drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a two-high wall of prizes behind a prize counter, against the wall behind it: plush hanging on pegs, "
                           "a giant bear on the floor, boxed toys on lit shelves (drawn two blocks high from its block)")

    def prizecase(v):
        els = [faces_box("Base", (0, 0, 1), (16, 9, 16), {"north": "laminate-dusty", "east": "laminate-dusty", "west": "laminate-dusty",
                                                          "south": "laminate-dusty", "down": "laminate-dusty"}),
               bx("Kick", (0, 0, 0.6), (16, 1, 1), "black"), bx("EdgeT", (0, 8.6, 0.6), (16, 9.2, 16), "darksteel", faces=("north", "up", "east", "west"))]
        els += prizes_inside(few=True)
        els += [glass(bx("GlassF", (0.2, 9.2, 0.8), (15.8, 13.8, 1), "glass-cracked", faces=("north", "south"))),
                glass(bx("GlassT", (4, 13.8, 0.8), (15.8, 14, 15.8), "glass-cracked", faces=("up", "down"))),
                bx("PostL", (15.2, 9.2, 0.6), (16, 14.2, 1.4), "darksteel"), bx("PostR", (0, 9.2, 0.6), (0.8, 14.2, 1.4), "darksteel"),
                bx("TopRail", (0, 13.8, 0.6), (16, 14.4, 1.4), "darksteel"), bx("Dust", (0.3, 9.05, 1.2), (15.7, 9.15, 15.7), "dust", faces=("up",)),
                rot(bx("Shard", (1.5, 9.1, 6), (4.5, 9.3, 9), "glass-cracked"), ry=25)]
        return els

    t = prize_data
    variants_block("l3999-prizecase", "Abandoned Prize Case", [("facing", SIDES)], prizecase, rot="facing", box=(0, 0, 0.03, 1, 0.9, 1),
                   material="Glass", sounds=GLASS,
                   data={"resistance": 2, "drops": drops(("game:bandage-clean", 0.4, 0), ("block:firesalt", 0.25, 0), ("seedpacket-turnip", 0.2, 0),
                                                         ("seedpacket-carrot", 0.2, 0), ("game:gear-rusty", 0.5, 0.5), ("block:l3999-neonlamp-pink-north", 0.3, 0),
                                                         ("block:l3999-neonlamp-cyan-north", 0.3, 0), ("l3999-neontubing", 0.5, 0.5), ("prybar", 0.12, 0),
                                                         ("game:backpack-normal", 0.1, 0), ("almondwater", 1, 1), ("block:l3999-plush-bear-north", 0.15, 0),
                                                         ("block:l3999-plush-alien-north", 0.15, 0), ("glassshard", 1, 0.5))},
                   comment="Level 3999.1: a prize counter abandoned in the blackout, its glass cracked, dust on everything. Salvage: 2-4 "
                           "prizes of the 15 and 40 ticket tiers, free for whoever dares the dark")

    def plush_block(v):
        return scale_els(plush_els(v["kind"]), 1.0, at=(8, 0, 8))

    variants_block("l3999-plush", "Plush", [("kind", ["bear", "cat", "alien", "smiley"]), ("facing", SIDES)], plush_block, rot="facing",
                   box=(0.25, 0, 0.25, 0.75, 0.56, 0.75), material="Cloth", sounds=CLOTH,
                   data={"behaviors": [{"name": "HorizontalOrientable", "properties": {"dropBlockFace": "north"}}], "resistance": 0.5,
                         "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]}, "attributes": {"backroomsCute": True},
                         "heldTpIdleAnimation": "holdbothhandslarge"},
                   comment="Level 3999's prizes: a plush toy 8 px tall (a brown bear, an orange cat, a green alien, a yellow smiley ball), "
                           "won from a claw machine or a prize counter; set it down anywhere. Cute (backroomsCute)",
                   names={"l3999-plush-bear-*": "Plush Bear", "l3999-plush-cat-*": "Plush Cat", "l3999-plush-alien-*": "Plush Alien",
                          "l3999-plush-smiley-*": "Plush Smiley"})


def tube_strip(name, frm, to, colour):
    return bx(name, frm, to, f"neon-{colour}", glow=255)


def plush_els(kind):
    """A plush toy round (0, 0, 0), about 8 px tall, facing north."""
    fur, face = f"fur-{kind}", f"face-{kind}"
    if kind == "bear":
        head = picture(bx("Head", (-3, 4, -2.5), (3, 9, 2.5), fur), face)
        return [bx("Body", (-2.6, 0, -2.2), (2.6, 4.4, 2.4), fur), head,
                bx("EarL", (1.6, 8.4, -0.6), (3.2, 10, 0.6), fur), bx("EarR", (-3.2, 8.4, -0.6), (-1.6, 10, 0.6), fur),
                bx("ArmL", (2.4, 1.2, -1.2), (3.6, 3.8, 0.6), fur), bx("ArmR", (-3.6, 1.2, -1.2), (-2.4, 3.8, 0.6), fur),
                bx("LegL", (0.8, 0, -3.2), (2.6, 1.6, -1.8), fur), bx("LegR", (-2.6, 0, -3.2), (-0.8, 1.6, -1.8), fur),
                bx("Tummy", (-1.5, 0.8, -2.4), (1.5, 3.2, -2.2), "fur-white", faces=("north",)),
                bx("Bow", (-1.2, 3.8, -2.7), (1.2, 4.6, -2.3), "neon-pink")]
    if kind == "cat":
        head = picture(bx("Head", (-3, 3.6, -2.5), (3, 8.6, 2.5), fur), face)
        return [bx("Body", (-2.4, 0, -1.9), (2.4, 4, 2.4), fur), head,
                bx("EarL", (1.2, 8.6, -0.6), (2.8, 10.2, 0.6), fur), bx("EarR", (-2.8, 8.6, -0.6), (-1.2, 10.2, 0.6), fur),
                bx("PawL", (0.6, 0, -2.6), (2, 1.2, -1.6), "fur-white"), bx("PawR", (-2, 0, -2.6), (-0.6, 1.2, -1.6), "fur-white"),
                bx("Tail", (-3.4, 0.4, 1.0), (-2.4, 3.6, 2.0), fur), bx("TailTip", (-3.8, 3.6, 1.1), (-2.8, 4.8, 1.9), "fur-white")]
    if kind == "alien":
        head = picture(bx("Head", (-3.4, 3.4, -2.6), (3.4, 9, 2.6), fur), face)
        return [bx("Body", (-2, 0, -1.6), (2, 3.6, 1.8), fur), head,
                bx("Antenna1", (1.4, 9, -0.3), (1.9, 11.4, 0.2), fur), bx("Antenna2", (-1.9, 9, -0.3), (-1.4, 11.4, 0.2), fur),
                bx("Bobble1", (1.1, 11.4, -0.6), (2.2, 12.5, 0.5), "neon-magenta"), bx("Bobble2", (-2.2, 11.4, -0.6), (-1.1, 12.5, 0.5), "neon-magenta"),
                bx("ArmL", (2, 1.2, -0.6), (3.6, 2.2, 0.6), fur), bx("ArmR", (-3.6, 1.2, -0.6), (-2, 2.2, 0.6), fur),
                bx("FootL", (0.4, 0, -2.4), (1.8, 0.9, -1.2), fur), bx("FootR", (-1.8, 0, -2.4), (-0.4, 0.9, -1.2), fur)]
    # A smiley ball: a rounded cluster of boxes, the face on its front
    front = picture(bx("BallZ", (-2.4, 1.6, -4), (2.4, 6.4, 4), fur), face)
    els = [bx("Core", (-3.1, 0.7, -3.1), (3.1, 7.3, 3.1), fur), front,
           bx("BallX", (-4, 1.6, -2.4), (4, 6.4, 2.4), fur), bx("BallY", (-2.4, 0, -2.4), (2.4, 8, 2.4), fur)]
    return els


def prize_tiers():
    """What the prize counters give, by the most tickets you can spend (the code picks one entry of the tier at random)."""
    def it(code, q=1, typ="item", **kw):
        d = {"type": typ, "code": code, "quantity": q}
        d.update(kw)
        return d
    colours = COLOURS
    return {
        "5": [it("almondwater"), it("game:candle", 2), it("l3999-glowband-magenta"), it("l3999-glowband-cyan"), it("l3999-glowband-lilac"),
              it("l3999-plush-bear-north", typ="block"), it("l3999-plush-cat-north", typ="block"), it("l3999-plush-alien-north", typ="block"),
              it("l3999-plush-smiley-north", typ="block"), it("l3999-popcorn"), it("l3999-cottoncandy"), it("l3999-soda-cherry"), it("l3999-soda-grape")],
        "15": [it("game:bandage-clean"), it("firesalt", typ="block"), it("seedpacket-turnip"), it("seedpacket-carrot"), it("seedpacket-onion"),
               it("game:gear-rusty", 2), it("l3999-neontubing", 3), it("l3999-traymeal-burger", 2)]
              + [it(f"l3999-neonlamp-{c}-north", typ="block") for c in colours],
        "40": [it("game:lantern-small-up", typ="block", attributes={"material": "copper", "lining": "plain", "glass": "quartz"}),
               it("prybar"), it("game:backpack-normal"), it("almondwater", 6), it("game:bandage-clean", 4)]
              + [it(f"l3999-neonlamp-{c}-north", 5, typ="block") for c in ("magenta", "cyan", "pink")],
        "200": [it("game:gear-temporal")],
    }


def generate():
    cabinets()
    games()
    LANG.update({"blockhelp-l3999-cabinet": "Play (hold)", "blockhelp-l3999-prize": "Trade tickets"})
