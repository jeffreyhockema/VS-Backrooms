"""The wanderers' dialogue: config/dialogue/wanderer.json and its lines in lang/en.json.

One tree for every wanderer, the size of vanilla's trader's, with the talk a wanderer would actually give: what lives
here, water and food, sleep, the ways out, what is next, and whether there is a way home. Each wanderer has a site
(WandererSites, given by WandererSystem): camp (Level 1), outpost (Level 4), road (Level 8's 9th Road), city (Level
11), end (The End's Junkies), hub (the M.E.G.'s doorstep in the Hub), amber (Camp Amber in the Hub) or 3999. The
dialogue reads it as entity.backroomsSite, and most of what a wanderer says is the line of its own site: vanilla's
dialogue picks, from a trader's lines, one of those whose conditions hold. The Junkies trade only with someone carrying
Memory Juice (the player.inventory condition, checked on both sides).

The voices follow docs/design/traders/lore.md: survivors dry and weary (the camp, the road's camp-keeper), the M.E.G.
breezy and official (the outpost, the Hub), the B.N.T.G. a polite brochure (the city), the Junkies melancholy, Camp
Amber a teacher, Level 3999's campers unhurried. What they say of the mod's mechanics is what docs/GUIDE.md and the
handbook say (tools/gen_guide.py); nothing here is a mechanic of its own.

Run from the repo root:  python tools/gen_dialogue.py          (writes both)
                         python tools/gen_dialogue.py --check  (checks the tree and that en.json has every line)
"""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
DIALOGUE = os.path.join(ASSETS, "config", "dialogue", "wanderer.json")
EN = os.path.join(ASSETS, "lang", "en.json")
TAB, NL = "\t", "\n"
PREFIX = "dialogue-wanderer-"

SITES = ["camp", "outpost", "road", "city", "end", "hub", "amber", "3999"]
SITE_VAR = "entity.backroomsSite"            # set by WandererSites.SetSite (code), never by the dialogue
JUICE = "{type: 'item', code: 'backrooms:end-memoryjuice', stacksize: 1}"
# Variables the game or the code provide, not the dialogue
PROVIDED = {SITE_VAR, "player.inventory"}


def site(s):
    return {"variable": SITE_VAR, "isValue": s}


def not_site(s):
    return {"variable": SITE_VAR, "isNotValue": s}


HAS_JUICE = {"variable": "player.inventory", "isValue": JUICE}
NO_JUICE = {"variable": "player.inventory", "isNotValue": JUICE}

LANG = {}
COMPONENTS = []


def say(key, text):
    """A line: its lang key (backrooms:dialogue-wanderer-<key>), kept in LANG."""
    full = PREFIX + key
    if full in LANG and LANG[full] != text:
        raise ValueError("two texts for " + full)
    LANG[full] = text
    return "backrooms:" + full


def line(key, text, *conds, jump=None):
    el = {"value": say(key, text)}
    if jump:
        el["jumpTo"] = jump
    if conds:
        el["conditions"] = list(conds)
    return el


def trader(code, lines, jump, **extra):
    COMPONENTS.append(dict({"code": code, "owner": "trader", "type": "talk", "text": lines, "jumpTo": jump}, **extra))


def player(code, lines, **extra):
    COMPONENTS.append(dict({"code": code, "owner": "player", "type": "talk", "text": lines}, **extra))


def per_site(key, texts, jump, **extra):
    """A trader's line for each site (texts: site -> text, or for "end" a (with juice, without) pair)."""
    lines = []
    for s in SITES:
        t = texts[s]
        if isinstance(t, tuple):
            lines.append(line(key + "-" + s + "-juice", t[0], site(s), HAS_JUICE))
            lines.append(line(key + "-" + s, t[1], site(s), NO_JUICE))
        else:
            lines.append(line(key + "-" + s, t, site(s)))
    trader(key, lines, jump, **extra)


def trade_options():
    """The way to the trade screen: anyone's, but a Junkie's only with Memory Juice on you."""
    text = "What have you got?"
    return [line("p-trade", text, not_site("end"), jump="opentrade"),
            line("p-trade", text, site("end"), HAS_JUICE, jump="opentrade"),
            line("p-trade", text, site("end"), NO_JUICE, jump="nojuice")]


def build():
    LANG.clear()
    COMPONENTS.clear()

    # ---- Meeting: a new wanderer gives its site's greeting; a new arrival is asked if they just noclipped in
    COMPONENTS.append({"code": "start", "owner": "trader", "type": "condition", "variable": "entity.hasmet", "isNotValue": "true",
                       "thenJumpTo": "greet", "elseJumpTo": "welcomeback"})
    per_site("greet", {
        "camp": "Easy. You're among people. Come and sit by the barrel.",
        "outpost": "Congratulations, wanderer! You've found an M.E.G. outpost. Water, bandages and a friendly face!",
        "road": "Off the dark and into the light. Good. Stay on the Road and you live.",
        "city": "Welcome, welcome! The B.N.T.G. is open for business. Peace through Prosperity!",
        "end": ("Oh, you have some. Sit down. Stay a while. This is home.",
                "Got any juice? No? Then you're only passing through. Everyone is."),
        "hub": "M.E.G. outpost, Doorstep Carpet. Wipe your feet. Nothing follows anyone in here.",
        "amber": "Camp Amber. We teach people where the doors go, before they go through them.",
        "3999": "Sit. Nothing hunts where the neon's lit. You can breathe here.",
    }, "testnew", setVariables={"entity.hasmet": "true"})
    COMPONENTS.append({"code": "testnew", "owner": "trader", "type": "condition", "variable": "player.backroomsmet", "isNotValue": "true",
                       "thenJumpTo": "noclip", "elseJumpTo": "main"})
    trader("noclip", [line("noclip", "You just noclip in? You've got the look.", not_site("end")),
                      line("noclip-end", "You're new. You still look for the door. We all did, once.", site("end"))], "noclipreply")
    player("noclipreply", [line("p-noclip", "Noclip?", jump="noclipwhat"),
                           line("p-wall", "There was a wall, and then there wasn't.", jump="wall"),
                           line("p-real", "Is any of this real?", jump="real"),
                           line("p-person", "It's good to see a person.", jump="person")] + trade_options(),
           setVariables={"player.backroomsmet": "true"})
    trader("noclipwhat", [line("noclipwhat", "You fell out of the world you knew, through a wall or a floor. Everyone here did. This is the Backrooms.")], "main")
    trader("wall", [line("wall", "That's it. That's noclipping. It only ever goes one way.")], "main")
    trader("real", [line("real", "Real enough to starve in. Drink, eat, sleep. Wonder about the rest later.")], "main")
    trader("person", [line("person", "Likewise. Remember: people don't cough at you from round a corner. Things do.")], "main")
    trader("welcomeback", [line("welcomeback-1", "Back again, {{playername}}. Still breathing. Good.", not_site("end")),
                           line("welcomeback-2", "{{playername}}. Sit a minute. Nothing comes near while you're with one of us.", not_site("end")),
                           line("welcomeback-end-juice", "You came back. With juice. You're starting to like it here.", site("end"), HAS_JUICE),
                           line("welcomeback-end", "No juice again. You can sit. Don't expect much.", site("end"), NO_JUICE)], "main")

    # ---- The topics
    player("main", trade_options() + [
        line("p-name", "Who are you?", jump="name"),
        line("p-gears", "Why rusty gears?", jump="gears"),
        line("p-creatures", "What lives around here?", jump="creatures"),
        line("p-water", "Where do I find water? Food?", jump="water"),
        line("p-sleep", "Is it safe to sleep?", jump="sleep"),
        line("p-exits", "How do I get out of here?", jump="exits"),
        line("p-rumours", "Heard anything about what's next?", jump="rumours"),
        line("p-home", "Is there a way home?", jump="home"),
    ])
    COMPONENTS.append({"code": "opentrade", "owner": "trader", "trigger": "opentrade"})
    trader("nojuice", [line("nojuice", "No juice, no trade. It's the only rule we kept.")], "main")

    per_site("name", {
        "camp": "{{npcname}}. Nobody's, these days. A few of us keep this camp: a barrel, some tents, what the crates give up.",
        "outpost": "{{npcname}}, Major Explorer Group! I keep this outpost stocked for everyone heading down to Level 5.",
        "road": "{{npcname}}. The M.E.G. marks the Road, the B.N.T.G. runs the caravans, and I keep the camp between.",
        "city": "{{npcname}}, Backrooms Nonaligned Trade Group. We sell to everyone and side with no one.",
        "end": "{{npcname}}. I think. There were six of us. We made a home in the rooms that look like home.",
        "hub": "Callsign {{npcname}}, M.E.G. Two Level Keys a week, the door register, and advice for free.",
        "amber": "{{npcname}}, Camp Amber. We never keep still for long, but today I'm here.",
        "3999": "{{npcname}}. I came here to rest for a week. That was a while ago.",
    }, "main", trigger="revealname")

    trader("gears", [line("gears", "Rusty gears. Every level has a few, and nobody makes them or fakes them. So they count.", not_site("city"), not_site("end")),
                     line("gears-city", "Our own coin is presses: plastic, like game pieces. Outsiders pay in rusty gears. Nobody can fake those.", site("city")),
                     line("gears-end", "Gears? Gears are fine. They don't make you feel anything, though.", site("end"))], "gearsreply")
    player("gearsreply", [line("p-gearswater", "Why not Almond Water?", jump="gearswater"),
                          line("p-gearsmore", "Where do I find more?", jump="gearsmore"),
                          line("p-isee", "I see.", jump="main")])
    trader("gearswater", [line("gearswater", "Out here everything's worth so many bottles of it. But water you drink. Gears you can only spend.")], "gearsreply")
    trader("gearsmore", [line("gearsmore", "Desks, clocks, curio cabinets, toy boxes. And most things you kill carry a few: the deeper the level, the more.")], "gearsreply")

    trader("creatures", [line("creatures", "Most of what's out there is heard before it's seen. Listen, and don't run: running carries.")], "creaturessite")
    per_site("creaturessite", {
        "camp": "Here: Hounds and rats in the dark sections, Wretches out toward the edge. When a section's lights go, Hounds come with the dark.",
        "outpost": "Level 4's quiet! Now and then a Duller in the walls: drink your Almond Water, face it, keep off the walls.",
        "road": "Off the Road: Wretches in the dark, and spiders that wait. If one rears up, run that moment, out of the webs.",
        "city": "On the streets nothing starts anything. Don't hurt a Faceling, or they all turn. The subway's another matter.",
        "end": "Nothing much. Smiles in the dark where the floor's fallen in. The quiet is what gets you. Stay too long and you come apart.",
        "hub": "Nothing hostile comes into the Hub. The Keymaster hurts nobody, but break nothing in his Tower.",
        "amber": "Here, nothing. Behind the doors, everything. That's why we teach before you go through.",
        "3999": "Nothing, where the neon's lit. Where it fails, out at the fringe: Smilers, Hounds, Partygoers. Keep to the bright.",
    }, "creaturesreply")
    player("creaturesreply", [line("p-smiler", "And Smilers?", jump="smiler"),
                              line("p-hound", "Hounds?", jump="hound"),
                              line("p-skinstealer", "Skin-Stealers?", jump="skinstealer"),
                              line("p-faceling", "Those people with no faces?", jump="faceling"),
                              line("p-thanks", "Thanks.", jump="main")])
    trader("smiler", [line("smiler", "Light. A torch, not a candle. If it's watching you, hold its gaze and walk away. Never run.")], "creaturesreply")
    trader("hound", [line("hound", "Fire keeps them off. Stare one down and it stops and growls for a few seconds. Use them.")], "creaturesreply")
    trader("skinstealer", [line("skinstealer", "They cough and call from out of sight, and they open doors. Bar yours from the inside. Keep a fire, keep your distance.")], "creaturesreply")
    trader("faceling", [line("faceling", "Facelings. Harmless. Touch one and it points to the nearest way out it knows. Hurt one and they all come. If one hurries off, Hounds are near.")], "creaturesreply")

    trader("water", [line("water", "Almond Water first: it's water, and it steadies your head. At a cooler or a fountain, drink with empty hands or fill a bottle.")], "watersite")
    per_site("watersite", {
        "camp": "In Level 1 the crates hold the water. The puddles don't: one drink in four turns your gut.",
        "outpost": "Level 4 has more Almond Water than anywhere: fountains, coolers, machines. Fill every bottle before you go down to 5!",
        "road": "Almond Water seeps from the rock by the Road: fill a bottle and it comes back. The clear cave pools are clean, too.",
        "city": "Almond Water's in every vending machine and grocery fridge. The fountains and the taps are not clean. Don't.",
        "end": "There's no food here. The juice wets your mouth, a little. We don't need much.",
        "hub": "The Hub has nothing to eat or drink, and it's cold. Come in full, leave full.",
        "amber": "Nothing to eat or drink in the Hub. We share what we have. It isn't much.",
        "3999": "The machines take a bottle of Almond Water and give you food. The stalls take tickets. Don't drink the violet pools.",
    }, "waterreply")
    player("waterreply", [line("p-boil", "What if the water's murky?", jump="boil"),
                          line("p-colours", "Blue and green bottles?", jump="colours"),
                          line("p-thanks", "Thanks.", jump="main")])
    trader("boil", [line("boil", "Bottle it and set it in a lit fire. Murky boils clean. Salt never does.")], "waterreply")
    trader("colours", [line("colours", "Blue puts you to sleep, near enough at once. Green holds sleep off a while, then drops it on you all at once.")], "waterreply")

    trader("sleep", [line("sleep", "Sleep when you're drowsy, not before. Eat and drink first: thirst and hunger wake you. Nothing visits a sleeper beside one of us.")], "sleepsite")
    per_site("sleepsite", {
        "camp": "Out in Level 1, find a room with a door and shut it. It halves the odds of company.",
        "outpost": "Level 4's gentle, and the bedrolls here are for anyone. Still: a shut door, always!",
        "road": "Sleep in the camps on the Road. Off it, nothing is safe to sleep beside.",
        "city": "Every house and hotel here has a real bed. Best sleep in the Backrooms. Shut the door anyway.",
        "end": "We sleep a lot. It's the waking that's hard.",
        "hub": "Take a cot. Nothing visits a sleeper in the Hub. Bring something warm, though.",
        "amber": "Use our cots. Nothing comes for a sleeper in the Hub. Sleep while you can.",
        "3999": "Nothing comes for you here. That's the danger: people sleep, and wake, and stay.",
    }, "sleepreply")
    player("sleepreply", [line("p-bedroll", "And without a bed?", jump="bedroll"),
                          line("p-thanks", "Thanks.", jump="main")])
    trader("bedroll", [line("bedroll", "Make a bedroll: carpet fibres, twine and wallpaper strips. Poor sleep, but it's sleep.")], "sleepreply")

    # (The gates are the rings' own: the city, The End, the Hub and Level 3999 have none)
    trader("exits", [line("exits", "Every level ends in a wall, and the wall has gates. Chalk arrows point the way.",
                          not_site("city"), not_site("end"), not_site("hub"), not_site("amber"), not_site("3999"))], "exitssite")
    per_site("exitssite", {
        "camp": "The stair cores climb to other floors, now and then to Level 4. Stay away from a red EXIT door in a solid wall.",
        "outpost": "The stairwells here loop, mostly. Some flights down come out in the Lobby. Never step through a doorframe standing on its own!",
        "road": "Follow the Road. Ways run off it into Levels 7 and 9. Where rubble stops it, the way on is the cave mouth, down and round.",
        "city": "The city has a door to nearly everywhere: office lifts to Level 4, hotel lifts to Level 5, front doors to the suburbs. Mind the manholes.",
        "end": "Most of the EXIT doors never open. The computers mark the ones that do. If a screen smiles at you, it's lying.",
        "hub": "Three doors stand open: Tunnel 7 to Level 1, Tunnel 10 to the city, Tunnel 5 to the Snackrooms. The rest want a key. Our register marks them.",
        "amber": "Every carved door goes one way. The grey service doors are the ways back. Learn that first.",
        "3999": "One staff door in six opens, onto the Hub. Play a themed cabinet to the end and it takes you where its marquee says.",
    }, "exitsreply")
    player("exitsreply", [line("p-notes", "What about the notes people leave?", jump="notes"),
                          line("p-thanks", "Thanks.", jump="main")])
    trader("notes", [line("notes", "Read every one. Somebody learned what's in them the hard way. Then pass it on: a paper reads once for each of us.")], "exitsreply")

    per_site("rumours", {
        "camp": "Past the gates is Level 2: pipes, heat, dark. Carry water. You'll sweat it out faster than you think.",
        "outpost": "The next ring down's a hotel. Good beds! If the music stops, leave.",
        "road": "Level 9 is houses. At night something tall looks for lights. Put yours away and keep from the windows.",
        "city": "They say there's a cinema in midtown. Walk into the screen and you fall out of the sky over green hills.",
        "end": "One computer in a great many runs TRUEEND. It doesn't go home. It goes somewhere bright.",
        "hub": "There's a pink door with a ribbon on it. It opens for anyone carrying something cute. I don't ask.",
        "amber": "The lit window in one tunnel climbs into a courtyard. Whatever you do in there, don't open the blinds.",
        "3999": "Don't walk into a rusted cabinet. It takes you to where the neon's dead.",
    }, "main")

    per_site("home", {
        "camp": "If there was, we'd all have used it by now.",
        "outpost": "Not that the M.E.G. has found. Yet! We keep looking. Meanwhile, live.",
        "road": "I asked that once. Then I stopped asking and started walking.",
        "city": "This city is as close as it gets. Plenty stopped looking here.",
        "end": "This is home. Look: the couch, the lamp. Have some juice and you'll see it too.",
        "hub": "Fifteen thousand doors, and not one goes home. We've checked a lot of them.",
        "amber": "Nobody's found it. So make one: a door, a fire, a chest. That's home now.",
        "3999": "The old campers say walk north till you find a glass door. I walked. It's more mall.",
    }, "homereply")
    player("homereply", [line("p-keepgoing", "Then why keep going?", jump="keepgoing"),
                         line("p-isee", "I see.", jump="main")])
    trader("keepgoing", [line("keepgoing", "Because there are people out here who want you to live. Be one of them.", not_site("end")),
                         line("keepgoing-end", "Going where? Sit. Stay a while.", site("end"))], "main")
    return {"components": COMPONENTS}


# ---------------------------------------------------------------- Checks

def holds(cond, ctx):
    """Whether a condition holds for a context {variable: value} (player.inventory: True if the player has juice)."""
    var = cond["variable"]
    if var == "player.inventory":
        val = ctx["juice"]
        want = True
    else:
        val = ctx.get(var)
        want = cond.get("isValue", cond.get("isNotValue"))
    return (val == want) if "isValue" in cond else (val != want)


def check(tree, lang):
    errors = []
    comps = tree["components"]
    codes = [c["code"] for c in comps]
    for c in set(codes):
        if codes.count(c) > 1:
            errors.append("component code used twice: " + c)
    known = set(codes)
    set_vars = {k for c in comps for k in (c.get("setVariables") or {})}

    def check_cond(where, cond):
        if cond["variable"] not in PROVIDED and cond["variable"] not in set_vars:
            errors.append(f"{where}: tests {cond['variable']}, which nothing sets")
        if cond["variable"] == SITE_VAR and cond.get("isValue", cond.get("isNotValue")) not in SITES:
            errors.append(f"{where}: no such site {cond}")

    for c in comps:
        for key in ("jumpTo", "thenJumpTo", "elseJumpTo"):
            if key in c and c[key] not in known:
                errors.append(f"{c['code']}: {key} {c[key]} is no component")
        if c.get("type") == "condition":
            check_cond(c["code"], c)
        for el in c.get("text", []):
            if el.get("jumpTo") and el["jumpTo"] not in known:
                errors.append(f"{c['code']}: a line jumps to {el['jumpTo']}, no component")
            for cond in el.get("conditions", []):
                check_cond(c["code"], cond)
            value = el["value"]
            if not value.startswith("backrooms:" + PREFIX):
                errors.append(f"{c['code']}: {value} is not one of our lang keys")
            elif value.split(":", 1)[1] not in lang:
                errors.append(f"{c['code']}: {value} is missing from en.json")
            elif re.search(r"(?<!\{)\{(?!\{)|(?<!\})\}(?!\})", lang[value.split(':', 1)[1]]):
                errors.append(f"{c['code']}: a single brace in {value} (the game formats the line: only {{{{playername}}}} and {{{{npcname}}}})")
        if c["owner"] == "player" and any("jumpTo" not in el for el in c.get("text", [])):
            errors.append(f"{c['code']}: an answer that leads nowhere")
        if c["owner"] == "trader" and c.get("type") == "talk" and "jumpTo" not in c:
            errors.append(f"{c['code']}: a trader's line with nowhere to go next")

    # Every site, with and without juice, gets a line wherever a line is due, and always one way to trade (or be refused)
    for s in SITES:
        for juice in (True, False):
            ctx = {SITE_VAR: s, "juice": juice}
            for c in comps:
                if c.get("type") != "talk":
                    continue
                n = sum(all(holds(cond, ctx) for cond in el.get("conditions", [])) for el in c["text"])
                if c["owner"] == "trader" and n == 0 and c["code"] != "exits":
                    errors.append(f"{c['code']}: nothing to say at the {s} site (juice {juice})")
                if c["owner"] == "player":
                    trades = [el for el in c["text"] if el["value"].endswith("p-trade") and all(holds(cond, ctx) for cond in el.get("conditions", []))]
                    if any(el["value"].endswith("p-trade") for el in c["text"]) and len(trades) != 1:
                        errors.append(f"{c['code']}: {len(trades)} ways to trade at the {s} site (juice {juice})")
                    if s == "end" and not juice and any(el.get("jumpTo") == "opentrade" for el in trades):
                        errors.append(f"{c['code']}: a Junkie trades without juice")
    return errors


# ---------------------------------------------------------------- Writing

def merge_lang(lang):
    """Adds the lines to lang/en.json without disturbing its layout: existing keys updated in place, new ones appended,
    and our own keys no longer used removed."""
    with open(EN, encoding="utf-8") as f:
        text = f.read()
    # (Lines of ours that are gone)
    for m in list(re.finditer("^" + TAB + r'"(' + re.escape(PREFIX) + r'[^"]*)":.*\n', text, re.M)):
        if m.group(1) not in lang:
            text = text.replace(m.group(0), "", 1)
    new_lines = []
    for key, value in lang.items():
        entry = TAB + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + TAB + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: entry + m.group(1), text, count=1)
        else:
            new_lines.append(entry)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + NL + NL + ("," + NL).join(new_lines) + NL + "}" + NL
    # (A trailing comma left by a removed last line)
    text = re.sub(r",(\s*\n\})", r"\1", text)
    json.loads(text)
    with open(EN, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)


def main():
    tree = build()
    if "--check" in sys.argv:
        with open(EN, encoding="utf-8") as f:
            lang = json.load(f)
        errors = check(tree, lang)
        with open(DIALOGUE, encoding="utf-8") as f:
            if json.load(f) != tree:
                errors.append("config/dialogue/wanderer.json is not what gen_dialogue.py writes: run it")
        stale = [k for k, v in LANG.items() if lang.get(k) != v]
        if stale:
            errors.append(f"{len(stale)} line(s) in en.json differ from gen_dialogue.py (e.g. {stale[0]}): run it")
        for e in errors:
            print("ERROR:", e)
        n = sum(len(c.get("text", [])) for c in tree["components"])
        print(f"{len(tree['components'])} components, {n} lines ({len(LANG)} lang keys): {'FAILED' if errors else 'ok'}")
        sys.exit(1 if errors else 0)
    errors = check(tree, dict(LANG))
    if errors:
        for e in errors:
            print("ERROR:", e)
        sys.exit(1)
    os.makedirs(os.path.dirname(DIALOGUE), exist_ok=True)
    with open(DIALOGUE, "w", encoding="utf-8", newline=NL) as f:
        f.write(json.dumps(tree, indent=TAB, ensure_ascii=False) + NL)
    print("wrote", os.path.relpath(DIALOGUE, ROOT))
    merge_lang(LANG)
    print("wrote", os.path.relpath(EN, ROOT), f"({len(LANG)} lines)")


if __name__ == "__main__":
    main()
