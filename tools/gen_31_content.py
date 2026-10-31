"""Level 31, "Roller Rink" (experimental): its people, its things and its words (the detail pass of 2026-10-30).

    entities/31/l31-coach.json    the Coach (Wikidot): a friendly Faceling in a striped coach's shirt with a name tag,
                                  behind the Skate Rental counter; talks (config/dialogue/l31-coach.json), gives skates,
                                  remembers your name; never hostile, cannot be hurt
    entities/31/l31-staff.json    the rink's Faceling staff: the food court's server (red uniform, blank name tag) and
                                  the DJ (black tee), by texture index (Regions.L31System puts them down)
    entities/31/l31-shadow.json   "Paranoia" (Fandom): a still black figure at the edge of a dark room, gone when you come
                                  close; cosmetic, no AI, no collision with anything that matters
    itemtypes/31/                 the food court's free food (pizza, pepperoni pizza, wings, a foot-long hot dog), a green
                                  arcade card, and the Coach's roller skates (feet; fast on smooth floors in the level)
    sounds/ambient/31/            skates rolling on boards somewhere overhead, a CCTV camera's servo and chirp
    lang/en.json                  the level's whole block of lines (titles, blocks, items, staff, the Coach's talk),
                                  kept together right after levelname-24

Textures of the people are painted by gen_entities.py's Faceling painter (its looks are not changed: this script adds
its own looks and paints them into textures/entity/31/). Run from the repo root:

    bash tools/locked.sh run python tools/gen_31_content.py
"""
import json
import math
import os
import random
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("VINTAGE_STORY", r"G:\Games\Vintagestory")

import gen_entities as E  # noqa: E402
from oggutil import write_ogg  # noqa: E402
from gen_entity_sounds import RATE  # noqa: E402

ROOT = os.path.join(HERE, "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
EN = os.path.join(ASSETS, "lang", "en.json")
TAB, NL = "\t", "\n"
LANG = {}


def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent=TAB, ensure_ascii=False)
    if comment:
        text = "// " + comment + NL + text
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text + NL)
    print("wrote", os.path.relpath(path, ROOT))


# ======================================================================== The people

# Looks for gen_entities' painter, plus this script's extras: "stripes" (referee stripes on the top), "tag" (a name tag)
LOOKS = {
    "coach": dict(skin="light", hair=("short", "brown"), top=("tshirt", (236, 236, 232), None), bottom=("slacks", (34, 34, 38)),
                  shoes=("sneakers", (238, 236, 232)), extras=(), stripes=(22, 22, 24), tag=True),
    "employee": dict(skin="tan", hair=("short", "black"), top=("tshirt", (186, 40, 44), None), bottom=("slacks", (38, 36, 40)),
                     shoes=("sneakers", (36, 34, 36)), extras=("cap",), tag=True, collar=(236, 196, 60)),
    "dj": dict(skin="brown", hair=("buzz", "black"), top=("tshirt", (30, 30, 34), None), bottom=("jeans", (52, 62, 84)),
               shoes=("sneakers", (232, 230, 226)), extras=(), collar=(220, 60, 170)),
}

_paint_top = E.paint_top
_current = {}


def paint_top(ctx, look, name, side):
    """gen_entities' top, then the stripes, the collar and the name tag of this level's looks."""
    _paint_top(ctx, look, name, side)
    if side in ("up", "down"):
        return
    stripes = look.get("stripes")
    if stripes and name in ("UpperTorso", "LowerTorso", "UpperArmL", "UpperArmR"):
        n = 4 if name.endswith("Torso") else 2
        for k in range(n):
            u = (k + 0.25) / n
            E.rect(ctx, u, 0.0, u + 0.5 / n, 0.5 if name.startswith("UpperArm") else 1.0, stripes)
    if look.get("collar") and name == "UpperTorso" and side == "west":
        E.rect(ctx, 0.25, 0.0, 0.75, 0.1, look["collar"])
    if look.get("tag") and name == "UpperTorso" and side == "west":
        # A white name tag over the heart (blank on the staff; the Coach's has a line of writing)
        E.rect(ctx, 0.58, 0.32, 0.86, 0.5, (240, 240, 236))
        if look.get("stripes"):
            E.rect(ctx, 0.62, 0.39, 0.82, 0.43, (40, 60, 150))


E.paint_top = paint_top


def save_entity_texture(img, name):
    code = name[len("faceling-"):] if name.startswith("faceling-") else name
    path = os.path.join(ASSETS, "textures", "entity", "31", code + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if _current.get("shadow"):
        img = shadow_of(img)
    img.save(path)
    print("wrote", os.path.relpath(path, ROOT))


def shadow_of(img):
    """A figure all of black, a little ragged at the edges: what a dark room's corner makes of a coat on a stand."""
    rng = random.Random(3131)
    px = img.load()
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    po = out.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            v = 6 + rng.randint(0, 8) + (r + g + b) // 120
            po[x, y] = (v, v, v + 2, a)
    return out


def textures():
    E.save_texture = save_entity_texture
    for code, look in LOOKS.items():
        E.paint_look(code, look)
    _current["shadow"] = True
    E.paint_look("shadow", dict(skin="dark", hair=("short", "black"), top=("coat", (20, 20, 22), (16, 16, 18)), bottom=("slacks", (18, 18, 20)),
                                shoes=("boots", (14, 14, 16)), extras=()))
    _current["shadow"] = False


def people_client(texture, extra_behaviours=()):
    client = E.common_client("backrooms:entity/faceling", texture, E.FACELING_ANIMS, step=1.01, movable=False)
    client["behaviors"] = [b for b in client["behaviors"] if b["code"] not in ("harvestable", "floatupwhenstuck")] + list(extra_behaviours)
    return client


def staff_tasks(nod="nod", wave="wave"):
    return [
        {"code": "lookatentity", "priority": 1.5, "maxTurnAngleDeg": 140, "entityCodes": ["player"], "minduration": 2000, "maxduration": 6000,
         "mincooldown": 1000, "maxcooldown": 3000},
        E.idle(nod, 1.3, 3000, 4000, 15000, 45000),
        E.idle(wave, 1.25, 3000, 3500, 40000, 120000),
        E.idle("lookaround", 1.2, 3000, 5000, 8000, 25000),
    ]


def people():
    conversable = {"code": "conversable", "dialogue": "backrooms:config/dialogue/l31-coach", "approachPlayer": False}
    base = {
        "class": "BackroomsL31Staff",
        "tags": ["backrooms-entity", "humanoid"],
        "weight": 70,
        "hitboxSize": {"x": 0.6, "y": 1.85},
        "eyeHeight": 1.7,
    }
    coach = dict(base, code="l31-coach", attributes={"invulnerable": True, "l31staff": "coach"},
                 client=people_client({"base": "backrooms:entity/31/coach"}, [{"code": "nametag", "showtagonlywhentargeted": True}, conversable]),
                 server={"behaviors": [
                     {"code": "repulseagents", "movable": False}, {"code": "controlledphysics", "stepHeight": 1.01},
                     {"code": "nametag", "showtagonlywhentargeted": True, "selectFromRandomName": ["Coach"]},
                     {"code": "taskai", "aiCreatureType": "LandCreature", "aitasks": staff_tasks()}, conversable,
                     {"code": "entitystatetags"}]})
    write_json(os.path.join(ASSETS, "entities", "31", "l31-coach.json"), coach,
               "Level 31's Coach (Wikidot): a friendly, talking Faceling in a striped coach's shirt with a name tag, behind the Skate Rental "
               "counter. Cannot be hurt, is never kept with the world; Regions.L31System puts him down and speaks for him")
    staff = dict(base, code="l31-staff", attributes={"invulnerable": True, "l31staff": "staff"},
                 client=people_client({"base": "backrooms:entity/31/employee", "alternates": [{"base": "backrooms:entity/31/dj"}]}),
                 server={"behaviors": [
                     {"code": "repulseagents", "movable": False}, {"code": "controlledphysics", "stepHeight": 1.01},
                     {"code": "taskai", "aiCreatureType": "LandCreature", "aitasks": staff_tasks()}, {"code": "entitystatetags"}]})
    write_json(os.path.join(ASSETS, "entities", "31", "l31-staff.json"), staff,
               "Level 31's Faceling staff (Wikidot): the food court's server in a red uniform with a blank name tag (texture 0) and the DJ "
               "(texture 1). Docile, cannot be hurt, never kept with the world (Regions.L31System)")
    shadow = dict(base, code="l31-shadow", attributes={"invulnerable": True, "l31staff": "shadow"},
                  client=people_client({"base": "backrooms:entity/31/shadow"}),
                  server={"behaviors": [{"code": "controlledphysics", "stepHeight": 1.01}, {"code": "entitystatetags"}]})
    shadow["client"]["behaviors"] = [b for b in shadow["client"]["behaviors"] if b["code"] != "repulseagents"]
    write_json(os.path.join(ASSETS, "entities", "31", "l31-shadow.json"), shadow,
               "Level 31's 'Paranoia' (Fandom): a still black figure at the edge of a dark room that is gone when you come close. Cosmetic: "
               "no AI, cannot be hurt, never kept with the world (Regions.L31System)")
    LANG.update({
        "item-creature-l31-coach": "The Coach",
        "item-creature-l31-staff": "Faceling (rink staff)",
        "item-creature-l31-shadow": "Shadow figure",
        "prefixandcreature-l31-coach": "the Coach",
        "prefixandcreature-l31-staff": "a Faceling",
        "prefixandcreature-l31-shadow": "a shadow",
    })


# ======================================================================== The Coach's talk

D = "l31-coach-"


def say(key, text):
    LANG[D + key] = text
    return "backrooms:" + D + key


def dialogue():
    met = {"variable": "player.l31coachmet", "isValue": "true"}
    skates = {"variable": "player.l31skates", "isValue": "true"}
    no_skates = {"variable": "player.l31skates", "isNotValue": "true"}
    comps = [
        {"code": "start", "owner": "trader", "type": "condition", "variable": "player.l31coachmet", "isNotValue": "true",
         "thenJumpTo": "firstmeet", "elseJumpTo": "welcomeback"},
        {"code": "firstmeet", "owner": "trader", "type": "talk", "setVariables": {"player.l31coachmet": "true"}, "jumpTo": "offer", "text": [
            {"value": say("first", "Oh! Sorry, didn't mean to make you jump. I saw you come in a while back and couldn't decide when to say "
                                   "hello. It's on the tag: Coach. And you're {{playername}}? Good. I'll remember that.")}]},
        {"code": "welcomeback", "owner": "trader", "type": "talk", "jumpTo": "main", "text": [
            {"value": say("back-1", "{{playername}}! There's my skater. How are you doing?")},
            {"value": say("back-2", "Welcome back, {{playername}}. Have you eaten today? Be honest.")},
            {"value": say("back-3", "{{playername}}. Good to see you up and about. Beaten your high score yet?")},
        ]},
        {"code": "offer", "owner": "trader", "type": "talk", "jumpTo": "offer-answer", "text": [
            {"value": say("offer", "I give lessons, free. Skating, I mean. Want one?")}]},
        {"code": "offer-answer", "owner": "player", "type": "talk", "text": [
            {"value": say("p-yes", "Sure. Teach me."), "jumpTo": "lesson"},
            {"value": say("p-no", "Maybe another time."), "jumpTo": "sigh"},
        ]},
        {"code": "sigh", "owner": "trader", "type": "talk", "jumpTo": "main", "text": [
            {"value": say("sigh", "*sighs* That's all right. The offer stands. Come by the counter whenever you want one.")}]},
        {"code": "main", "owner": "player", "type": "talk", "text": [
            {"value": say("p-lesson", "Can I have that lesson?"), "jumpTo": "lesson", "conditions": [no_skates]},
            {"value": say("p-technique", "Got a new technique for me?"), "jumpTo": "technique", "conditions": [skates]},
            {"value": say("p-live", "How do I get by here?"), "jumpTo": "live"},
            {"value": say("p-shadows", "What are the shapes in the dark rooms?"), "jumpTo": "shadows"},
            {"value": say("p-out", "Can you lead me out?"), "jumpTo": "out"},
            {"value": say("p-why", "Why do you keep telling people to leave?"), "jumpTo": "why", "conditions": [met]},
            {"value": say("p-bye", "See you, Coach."), "jumpTo": "bye"},
        ]},
        {"code": "lesson", "owner": "trader", "type": "talk", "jumpTo": "lesson2", "trigger": "giveitemstack",
         "triggerdata": {"type": "item", "code": "backrooms:l31-skates", "stacksize": 1}, "setVariables": {"player.l31skates": "true"},
         "text": [{"value": say("lesson", "Here, these are your size. Laces tight, knees soft, eyes up: look where you want to go, not "
                                           "at your feet. Push, glide. Push, glide. There you go!")}]},
        {"code": "lesson2", "owner": "trader", "type": "talk", "jumpTo": "lesson3", "text": [
            {"value": say("lesson2", "You fell. You got up. That's the whole trick, on the rink and off it. I'm proud of you, "
                                     "{{playername}}. You learn fast.")}]},
        {"code": "lesson3", "owner": "trader", "type": "talk", "jumpTo": "main", "text": [
            {"value": say("lesson3", "Keep them. They're quick on the boards and the concrete; they won't do a thing on carpet. And "
                                     "they're on loan, mind. Folk say skates walked out of here end up somewhere grey, without their feet.")}]},
        {"code": "technique", "owner": "trader", "type": "talk", "jumpTo": "main", "text": [
            {"value": say("tech-1", "Spins today. Arms in, pick one spot and look at it every time you come round. Out of it the way you went in.")},
            {"value": say("tech-2", "Crossovers. Lean into the turn, step the outside skate over the inside one. Don't think about it. Feel it.")},
            {"value": say("tech-3", "Stopping. Everybody forgets stopping. Toe stop down, gently, weight back. Knowing how to stop is half of going.")},
        ]},
        {"code": "live", "owner": "trader", "type": "talk", "jumpTo": "main", "text": [
            {"value": say("live", "Nothing here will hurt you. The food court feeds you for free: ask the fellow behind the counter, and "
                                  "the soda fountain pours Almond Water. Tidy up after yourself, though; leave your rubbish about and he "
                                  "won't serve you for a day. The cinema is the darkest, quietest place to sleep. The arcade cards are "
                                  "free at the machine by the door. And the HVAC rooms are cold, so don't nap in there.")}]},
        {"code": "shadows", "owner": "trader", "type": "talk", "jumpTo": "main", "text": [
            {"value": say("shadows", "In the dark rooms, standing still, and gone when you get close? I've seen them. Never once seen one "
                                     "move. I think they're what the dark makes when you've been alone too long. Don't go looking for them.")}]},
        {"code": "out", "owner": "trader", "type": "talk", "jumpTo": "out2", "text": [
            {"value": say("out", "I can. Behind the arcades, where the machines are switched off, there's a white door with a 70 on it. "
                                 "The food court has a door marked Employees Only. Folk talk about others, a revolving door, the arcade "
                                 "going on and on till it isn't ours any more.")}]},
        {"code": "out2", "owner": "trader", "type": "talk", "jumpTo": "main", "text": [
            {"value": say("out2", "They aren't there today. They come and go. When one's back, I'll walk you to it myself. And "
                                  "{{playername}}? You're always welcome back.")}]},
        {"code": "why", "owner": "trader", "type": "talk", "jumpTo": "main", "text": [
            {"value": say("why", "Because it feels like home here, and that's the trouble. It's the safest place I know, so people stop. "
                                 "Stop eating, stop talking, stop trying. I've watched it. I'd rather miss you than watch it again. "
                                 "Connections are what keep you going down here. Go and make some.")}]},
        {"code": "bye", "owner": "trader", "type": "talk", "trigger": "closedialogue", "text": [
            {"value": say("bye", "Take care of yourself, {{playername}}. The counter's here.")}]},
    ]
    write_json(os.path.join(ASSETS, "config", "dialogue", "l31-coach.json"), {"components": comps})


# ======================================================================== Things

ITEMS = os.path.join(ASSETS, "itemtypes", "31")
ITEX = os.path.join(ASSETS, "textures", "item", "31")
INV = {"general": ["*"], "items": ["*"], "backrooms": ["*"]}
SPRITE = {
    "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
    "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
    "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
}


def save_item_tex(img, name):
    os.makedirs(ITEX, exist_ok=True)
    img.save(os.path.join(ITEX, name + ".png"))


def sprite(draw_fn, name, size=32):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_fn(d, random.Random(name))
    save_item_tex(img, name)


def pizza(pepperoni):
    def draw(d, rng):
        d.polygon([(4, 6), (28, 6), (16, 29)], fill=(222, 170, 82))          # the slice
        d.polygon([(6, 8), (26, 8), (16, 26)], fill=(246, 210, 96))           # the cheese
        d.rectangle([3, 3, 29, 7], fill=(196, 132, 62))                       # the crust
        d.line([(3, 7), (29, 7)], fill=(160, 100, 48))
        for _ in range(14):
            x, y = rng.randint(9, 23), rng.randint(9, 20)
            d.point((x, y), fill=(250, 232, 150))
        if pepperoni:
            for x, y in ((11, 11), (20, 11), (16, 17), (14, 23) if False else (16, 21)):
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(176, 42, 36))
                d.point((x - 1, y - 1), fill=(210, 80, 64))
    return draw


def wings(d, rng):
    d.rounded_rectangle([3, 14, 29, 28], 3, fill=(204, 46, 44))               # a red paper boat
    d.line([(3, 18), (29, 18)], fill=(236, 236, 230))
    for x, y in ((9, 12), (16, 10), (23, 12), (12, 15), (20, 15)):
        d.ellipse([x - 4, y - 3, x + 4, y + 3], fill=(176, 84, 34))
        d.ellipse([x - 2, y - 2, x + 1, y], fill=(214, 120, 52))


def hotdog(d, rng):
    d.rounded_rectangle([1, 12, 30, 22], 5, fill=(222, 170, 96))              # the long bun
    d.rounded_rectangle([0, 14, 31, 19], 3, fill=(176, 72, 48))               # the foot-long sausage
    for x in range(4, 29, 4):
        d.line([(x, 14), (x + 2, 16)], fill=(236, 200, 40))                   # mustard
    d.line([(2, 21), (29, 21)], fill=(196, 140, 72))


def greencard(d, rng):
    d.rounded_rectangle([3, 8, 28, 24], 2, fill=(64, 178, 92))
    d.rectangle([3, 11, 28, 13], fill=(30, 40, 34))                          # the magnetic strip
    d.rectangle([5, 16, 14, 18], fill=(214, 240, 210))
    d.text((17, 15), "31", fill=(230, 250, 230))
    d.rounded_rectangle([3, 8, 28, 24], 2, outline=(36, 120, 58))


def skates_textures():
    def flat(name, colour, var=10, size=16, seed=0):
        rng = random.Random(seed)
        img = Image.new("RGBA", (size, size))
        px = img.load()
        for y in range(size):
            for x in range(size):
                n = rng.randint(-var, var)
                px[x, y] = tuple(max(0, min(255, c + n)) for c in colour) + (255,)
        return img
    boot = flat("boot", (236, 232, 222), 6, seed=1)
    d = ImageDraw.Draw(boot)
    for y in (4, 7, 10):
        d.line([(5, y), (10, y)], fill=(200, 60, 160))                        # magenta laces
    d.rectangle([0, 14, 15, 15], fill=(40, 38, 40))                          # the sole
    save_item_tex(boot, "skate-boot")
    save_item_tex(flat("wheel", (230, 70, 180), 8, seed=2), "skate-wheel")
    save_item_tex(flat("plate", (150, 154, 160), 6, seed=3), "skate-plate")
    save_item_tex(flat("stop", (200, 40, 40), 6, seed=4), "skate-stop")


def bx(name, frm, to, tex, parent=None):
    (x1, y1, z1), (x2, y2, z2) = frm, to
    w, h, d = x2 - x1, y2 - y1, z2 - z1
    sizes = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}
    faces = {f: {"texture": "#" + tex, "uv": [0, 0, round(min(16, max(a * 2, 1)), 3), round(min(16, max(b * 2, 1)), 3)]} for f, (a, b) in sizes.items()}
    el = {"name": name, "from": list(frm), "to": list(to), "faces": faces}
    if parent:
        el["stepParentName"] = parent
    return el


def skates_shape():
    """A roller skate on each foot: the boot over the seraph's lower foot (its sole at y 0, its toe toward -x, as vanilla's
    shoes), a plate under it, four wheels and a toe stop."""
    els = []
    for side, parent in (("L", "LowerFootL"), ("R", "LowerFootR")):
        boot = bx(f"skate{side}", (-0.2, -0.2, -0.2), (4.2, 5.2, 3.2), "boot", parent)
        boot["children"] = [
            bx(f"plate{side}", (-0.6, -0.8, 0.4), (4.6, -0.2, 2.6), "plate"),
            bx(f"stop{side}", (-1.4, -1.4, 0.9), (-0.4, -0.4, 2.1), "stop"),
        ]
        for i, (x, z) in enumerate(((-0.3, -0.5), (-0.3, 2.9), (3.1, -0.5), (3.1, 2.9))):
            boot["children"].append(bx(f"wheel{side}{i}", (x, -2.0, z), (x + 1.4, -0.6, z + 0.6), "wheel"))
        els.append(boot)
    shape = {"textureWidth": 16, "textureHeight": 16,
             "textures": {"boot": "backrooms:item/31/skate-boot", "wheel": "backrooms:item/31/skate-wheel",
                          "plate": "backrooms:item/31/skate-plate", "stop": "backrooms:item/31/skate-stop"},
             "elements": els}
    write_json(os.path.join(ASSETS, "shapes", "item", "31", "skates.json"), shape)


def items():
    sprite(pizza(False), "pizza")
    sprite(pizza(True), "pepperoni")
    sprite(wings, "wings")
    sprite(hotdog, "hotdog")
    sprite(greencard, "greencard")
    foods = {"pizza": ("Slice of Cheese Pizza", 300, "Grain"), "pepperoni": ("Slice of Pepperoni Pizza", 320, "Protein"),
             "wings": ("Chicken Wings", 340, "Protein"), "hotdog": ("Foot-Long Hot Dog", 380, "Protein")}
    data = {"code": "l31-food", "variantgroups": [{"code": "dish", "states": list(foods)}], "maxstacksize": 8, "creativeinventory": INV,
            "materialDensity": 600,
            "textureByType": {f"l31-food-{k}": {"base": f"item/31/{k}"} for k in foods},
            "nutritionPropsByType": {f"l31-food-{k}": {"satiety": sat, "foodcategory": cat, "health": 1} for k, (_, sat, cat) in foods.items()},
            "transitionablePropsByType": {"*": [{"type": "Perish", "freshHours": {"avg": 48}, "transitionHours": {"avg": 24},
                                                  "transitionedStack": {"type": "item", "code": "game:rot"}, "transitionRatio": 1}]},
            "attributes": {"handbook": {"groupBy": ["l31-food-*"]}}}
    data.update(SPRITE)
    write_json(os.path.join(ITEMS, "l31-food.json"), data,
               "Level 31's food court: what the Faceling behind the counter serves, free (Wikidot): pizza, pepperoni pizza, wings, a foot-long hot dog")
    for k, (n, _, _) in foods.items():
        LANG[f"item-l31-food-{k}"] = n
    LANG["itemdesc-l31-food-*"] = ("Free, from the Faceling behind the food court's counter in Level 31. Not the best you ever had, "
                                   "but familiar in a strangely welcoming way.")
    card = {"code": "l31-greencard", "maxstacksize": 1, "creativeinventory": INV, "materialDensity": 400, "texture": {"base": "item/31/greencard"}}
    card.update(SPRITE)
    write_json(os.path.join(ITEMS, "l31-greencard.json"), card, "Level 31's green arcade card, from the dispenser at the arcade's door")
    LANG["item-l31-greencard"] = "Green Arcade Card"
    LANG["itemdesc-l31-greencard"] = ("From the machine at the door of Level 31's arcade: \"Please press the button to get a card.\" "
                                      "The games are free with it, or so the machine says. A keepsake.")
    skates_textures()
    skates_shape()
    skates = {
        "code": "l31-skates", "maxstacksize": 1, "storageFlags": 128, "creativeinventory": {"general": ["*"], "clothing": ["*"], "backrooms": ["*"]},
        "behaviors": [{"name": "Wearable"}],
        "shape": {"base": "backrooms:item/31/skates"},
        "attributes": {"clothescategory": "foot", "wearableAttachment": True, "l31skates": True},
        "guiTransform": {"translation": {"x": 3, "y": 6, "z": 0}, "rotation": {"x": -20, "y": 40, "z": 0}, "origin": {"x": 2, "y": 2, "z": 1.5}, "scale": 3.2},
        "tpHandTransform": {"translation": {"x": -0.8, "y": -0.3, "z": -0.6}, "rotation": {"x": 0, "y": 0, "z": 0}, "scale": 0.8},
        "groundTransform": {"translation": {"x": 0, "y": 0.15, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 3},
    }
    write_json(os.path.join(ITEMS, "l31-skates.json"), skates,
               "Level 31's roller skates, from the Coach's lesson (Fandom: anomalous, hard to fall in): worn on the feet, quick on smooth floors in the level")
    LANG["item-l31-skates"] = "Rink Skates"
    LANG["itemdesc-l31-skates"] = ("The Coach's loan from the Skate Rental of Level 31. Worn, they make you quicker on the rink's boards "
                                   "and its smooth concrete, though not on carpet; and somehow you never fall in them.")


# ======================================================================== Sounds

def skates_overhead():
    """Skates crossing the boards somewhere overhead: a rolling rumble, the click of the joints under the wheels, swelling
    and fading as they pass, muffled through a ceiling."""
    rng = np.random.default_rng(3170)
    n = int(4.5 * RATE)
    t = np.arange(n) / RATE
    noise = rng.normal(size=n)
    spec = np.fft.rfft(noise)
    f = np.fft.rfftfreq(n, 1 / RATE)
    spec *= np.exp(-((f - 140) / 160) ** 2) + 0.3 * np.exp(-((f - 420) / 200) ** 2)
    rumble = np.fft.irfft(spec, n=n)
    rumble /= np.max(np.abs(rumble)) + 1e-9
    clicks = np.zeros(n)
    k = 0.0
    while k < 4.4:
        i = int(k * RATE)
        m = min(n - i, int(0.02 * RATE))
        clicks[i:i + m] += np.exp(-np.arange(m) / (0.003 * RATE)) * rng.uniform(0.5, 1)
        k += rng.uniform(0.16, 0.24)
    env = np.exp(-((t - 2.2) / 1.3) ** 2)
    sig = (rumble * 0.8 + np.convolve(clicks, np.ones(40) / 40, mode="same") * 0.5) * env
    spec = np.fft.rfft(sig)
    spec *= 1 / (1 + (f / 700) ** 4)
    sig = np.fft.irfft(spec, n=n)
    sig = 0.5 * sig / (np.max(np.abs(sig)) + 1e-9)
    path = os.path.join(ASSETS, "sounds", "ambient", "31", "skates.ogg")
    if write_ogg(path, sig, RATE):
        print("wrote", os.path.relpath(path, ROOT))


def cctv():
    """A CCTV camera turning on its mount: a servo's whine, a stop, a chirp."""
    n = int(1.4 * RATE)
    t = np.arange(n) / RATE
    whine = np.sin(2 * np.pi * np.cumsum(900 + 300 * np.minimum(t, 0.8)) / RATE) * (t < 0.8) * 0.2
    whine *= np.minimum(1, t / 0.05) * np.minimum(1, np.maximum(0, 0.8 - t) / 0.05)
    chirp = np.sin(2 * np.pi * 2800 * t) * ((t > 1.0) & (t < 1.08)) * 0.25
    sig = whine + chirp
    path = os.path.join(ASSETS, "sounds", "ambient", "31", "cctv.ogg")
    if write_ogg(path, sig, RATE):
        print("wrote", os.path.relpath(path, ROOT))


# ======================================================================== Words

def words():
    LANG.update({
        "level-2401": "The Rink",
        "level-2402": "The Arcade",
        "level-2403": "The Food Court",
        "level-2404": "Skate Rental",
        "level-2405": "The Cinema",
        "level-2406": "Employees Lounge",
        "block-l31-carpet-rink": "Rink Carpet",
        "block-l31-carpet-black": "Black Carpet",
        "block-l31-carpet-grey": "Grey Carpet",
        "block-l31-floor-polished": "Polished Concrete",
        "block-l31-floor-tile": "Vinyl Tile",
        "block-l31-floor-quarry": "Quarry Tile",
        "block-l31-brick-*": "Exposed Brick",
        "block-l31-sign-trash-*": "Taped Sign",
        "block-l31-sign-outoforder-*": "OUT OF ORDER Sign",
        "block-l31-sign-menu-*": "Menu Board",
        "block-l31-sign-ad1-*": "Faded Advert",
        "block-l31-sign-ad2-*": "Faded Advert",
        "block-l31-sign-ad3-*": "Faded Advert",
        "block-l31-sign-staffdoorlow-*": "Employees Only Door",
        "block-l31-sign-staffdoorhigh-*": "Employees Only Door",
        "block-l31-sign-door70low-*": "White Door",
        "block-l31-sign-door70high-*": "White Door (70)",
        "block-l31-chair-*": "Plastic Chair",
        "block-l31-table-*": "Square Table",
        "block-l31-bench-*": "Park Bench",
        "block-l31-condiments-*": "Condiment Stand",
        "block-l31-fountain-*": "Soda Fountain",
        "block-l31-djdesk-*": "DJ Desk",
        "block-l31-speaker-*": "PA Speaker",
        "block-l31-gate-*": "Rink Gate",
        "block-l31-star-*": "Star Light",
        "block-l31-dispenser-*": "Card Dispenser",
        "block-l31-retrocab-*": "Old Arcade Cabinet",
        "block-l31-skateshelf-*": "Skate Cubbies",
        "block-l31-cinemabench-*": "Metal Bench",
        "block-l31-tv-*": "Big TV",
        "block-l31-cctv-*": "CCTV Camera",
        "block-l31-monitors-*": "CCTV Monitors",
        "block-l31-cladding-m*": "Rink Mural",
        "block-l31-cladding-f*": "Wall Mirror",
        "block-l31-cladding-lacq*": "Black Lacquer Panel",
        "block-l31-cladding-dj*": "DJ Sign",
        "block-l31-cladding-exit-*": "EXIT Sign",
        "blockhelp-l31-dispenser": "Get a card",
        # The staff (Regions.L31System)
        "l31-server-serve-1": "The Faceling behind the counter slides a tray across to you without a word.",
        "l31-server-serve-2": "The Faceling behind the counter hands you something hot, and a napkin.",
        "l31-server-serve-3": "The Faceling behind the counter serves you, and goes back to wiping the counter.",
        "l31-server-water": "It fills a cup at the soda fountain for you as well.",
        "l31-server-wait": "The Faceling behind the counter points at the clock. Not yet.",
        "l31-server-refuse": "The Faceling behind the counter folds its arms. Not after the mess you left.",
        "l31-server-question": "It does not answer questions. It only serves.",
        "l31-server-clean": "The Faceling comes out from behind the counter and, very slowly, picks up what was left lying about. It does not look at {0}.",
        "l31-server-struck": "The Faceling behind the counter flinches, and keeps wiping the counter.",
        "l31-dj-1": "The DJ doesn't look up from the decks. The song changes anyway.",
        "l31-dj-2": "The DJ nods along to something only it can hear.",
        "l31-dj-3": "The DJ turns a knob. The music gets no louder.",
        "l31-coach-struck": "The Coach catches your wrist, gently. \"Hey. Whatever it is, we can talk about it.\"",
        "l31-coach-stay": "The Coach finds you. \"{0}, you've been here a long while now. It's time you moved on. Not because you're not wanted: because you are. You're always welcome back.\"",
        "l31-coach-stay-2": "The Coach sits down beside you. \"{0}. When did you last eat? When did you last talk to anyone who wasn't me? Go on, now. Find the door.\"",
        "l31-card-got": "The machine whirs and a green card drops into the tray.",
        "l31-card-have": "You already have a card. The machine's button does not press.",
        "l31-skates-on": "The skates hum on the smooth floor.",
    })


# ======================================================================== Writing the lang block

def merge_lang():
    """Puts LANG into en.json's Level 31 block (from level-24 on, while the keys are the level's): a key there is updated
    in place; a new one goes at the end of the block."""
    with open(EN, encoding="utf-8") as f:
        lines = f.read().split(NL)
    start = next(i for i, l in enumerate(lines) if l.startswith(TAB + '"level-24"'))
    ours = re.compile(r'^\t"(level-24\d\d|levelhint-24|levelname-24|[^"]*l31-[^"]*)"\s*:')
    end = start
    while end + 1 < len(lines) and ours.match(lines[end + 1]):
        end += 1
    block = lines[start:end + 1]
    keys = {}
    for i, l in enumerate(block):
        m = re.match(r'^\t"([^"]+)"\s*:', l)
        if m:
            keys[m.group(1)] = i
    for k, v in LANG.items():
        entry = TAB + json.dumps(k) + ": " + json.dumps(v, ensure_ascii=False) + ","
        if k in keys:
            block[keys[k]] = entry
        else:
            keys[k] = len(block)
            block.append(entry)
    # (Every line of the block ends in a comma: it is never the file's last)
    block = [l if l.rstrip().endswith(",") else l.rstrip() + "," for l in block]
    lines[start:end + 1] = block
    text = NL.join(lines)
    json.loads(text)
    with open(EN, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)
    print("wrote", os.path.relpath(EN, ROOT), f"({len(LANG)} Level 31 lines)")


def main():
    textures()
    people()
    dialogue()
    items()
    skates_overhead()
    cctv()
    words()
    merge_lang()


if __name__ == "__main__":
    main()
