"""The Backrooms pages of the in-game handbook (H): the starter guide, the progression guide, Reality Stability, and
three reference pages (salvage and recipes, the levels, the ways between them).

In a Backrooms world these replace the vanilla Starter Guide, Progression Guide and Temporal Stability pages and add
the rest (src/GuideSystem.cs); other worlds keep the vanilla handbook. The text lives here in a light markup and is
written into lang/en.json as the handbook's rich text:

    blank line           paragraph break
    **bold**  *italic*
    [text](page)         link to a handbook page: a guide's page code, or item-<code> / block-<code>
    [text](search:word)  link that searches the handbook
    {shift}              a key

Run on its own (python tools/gen_guide.py) or as part of gen_detail.py. Keep the pages short: they may be the only
reference a player has. Every number here comes from the block types, recipes and code; check them when those change.
"""
import json
import os
import re

from detail_kit import ASSETS, LANG

PAGES = {}

PAGES["starter"] = ("Starter Guide", """
**Waking in the Backrooms**
*You have nothing, and nobody is coming.*

This guide covers your first hours in Level 0. Then read [Progression](craftinginfo-progressionguide), and keep [Salvage and Recipes](backrooms-salvage), [The Levels](backrooms-levels), [Ways Between Levels](backrooms-thresholds) and [Reality Stability](gamemechanicinfo-temporalstability) to hand. The other guides describe ordinary worlds: their crafting is right, but where they say to find things is not.

**What is different here**
- The building cannot be broken: walls, floors, ceilings and doors are permanent. Loose things can: boxes, furniture, ceiling tiles, dead lights.
- Nothing grows and nothing can be dug until the deep levels. Everything you need was left by someone else.
- No rain, no seasons, no winter, no thirst. Hunger and health work as usual.
- Dying puts you back where you woke up.

**1. Open supply boxes**
Cardboard supply boxes stand about Level 0, and one is always a few steps from where you wake. Break them (hold {leftmouse}). They show red on the map. Each gives a few of: Almond Water, crackers, canned beans, carpet fibres, wallpaper strips, a glass shard, [flint](item-flint), sticks, dry grass; sometimes a candle or a metal bracket.

**2. Get a blade**
Break a dead (dark) light panel in the ceiling for [glass shards](item-backrooms:glassshard). Lit panels cannot be removed. A bare shard cuts, but snaps about one use in four. Make it a tool:
- [Glass shiv](item-backrooms:glassshiv) = glass shard + wallpaper strip + carpet fibre. A knife, 60 uses.
- [Improvised scraper](item-backrooms:scraper) = metal bracket + wallpaper strip + 2 carpet fibres. A knife, 180 uses.

**3. Cut wallpaper and carpet**
Hold a blade and {rightmouse} Level 0's yellow wallpaper or its dry carpet. Each block gives one [wallpaper strip](item-backrooms:wallpaperstrip) or [carpet fibres](item-backrooms:carpetfibre) and is left bare.
- 2 wallpaper strips = 1 [dry grass](item-drygrass)
- 3 carpet fibres = 1 flax twine

**4. Knap flint**
With two flints (supply boxes; loose on the floor in Level 1, with stones that work as well), {shift} + {rightmouse} one onto the floor to start [knapping](craftinginfo-knapping). Make a knife blade and an axe head first; each needs a stick for a handle.

**5. Sticks, firewood, fire**
- 1 [rotten wood](item-backrooms:rottenwood) = 2 sticks. 2 rotten wood = 1 firewood. Rotten wood sometimes falls out of broken ceiling tiles.
- 1 plank + a knife = 2 sticks. 3 planks + an axe = 1 firewood. Planks come from furniture and crates, from Level 1 on.
- [Fire starter](item-firestarter) = 1 dry grass + 2 sticks.
- Firepit: {shift} + {rightmouse} dry grass onto the floor, add 4 firewood, light it with the fire starter.
Level 0 has almost no wood. Expect your first fire in Level 1.

**6. Light**
A candle in your hand is enough for the dark zones. [Torch](block-torch-basic-extinct-up) = 2 dry grass + 1 stick; light it at a firepit.

**7. Eat and drink**
Crackers and canned beans fill you. [Almond Water](item-backrooms:almondwater) fills you a little, heals 1 and restores stability. Level 0 has no food but what is in the boxes, so do not settle here.

**8. Carry more**
You have 10 slots and room for 4 bags. Make bags before you do anything else in Level 0:
- [Carpet bag](item-backrooms:carpetbag) (3 slots) = 5 carpet fibres + 1 flax twine. Four of them cost 32 cuts of carpet.
- Linen sack (5 slots) = flax twine + linen (hotel beds and tents).
- Chest = 8 planks + 1 nails and strips. 2 metal brackets = 1 nails and strips.
Hand baskets need cattails, which only grow in Level 10.

**9. Find the way on**
The map (M) shows only what you have seen, and remembers it. Right-click it to add waypoints. Walk in one direction: Level 0 ends between 650 and 4,000 blocks from where you woke, depending on the way you pick. Worn carpet with concrete showing through and missing ceiling tiles mean Level 1 is near.

**10. Watch the gear**
The gear between your health and hunger is your [Reality Stability](gamemechanicinfo-temporalstability). If it turns backwards, move on.
""")

PAGES["progression"] = ("Progression Guide", """
**Progression Guide**
*The way from a shard of glass to steel is the usual one. Only the places are strange.*

**Scavenger: Level 0**
Supply boxes, a glass blade, wallpaper strips and carpet fibres, four carpet bags, two flints. See the [Starter Guide](craftinginfo-starterguide).

**Stone age: Levels 0 and 1**
[Knap](craftinginfo-knapping) a knife, an axe, a spear and a shovel from flint, or from the chert, andesite and granite lying loose on Level 1's concrete. Level 1's crates, pallets, plywood and workbenches are your first planks: split them for firewood, build a firepit and cook. Build a chest.

**Pottery: Level 3, then 8 and 10**
Clay floors the flooded tunnel under Level 3: climb down a manhole. The water is freezing and stability drains there faster than anywhere, so dig and get out. Later sources: pockets in Level 8's rock, and the beds of Level 10's ponds. [Form](craftinginfo-clayforming) a crucible, tool moulds, a cooking pot, bowls and storage vessels, and fire them in a pit kiln.

**Copper: Levels 1 to 3**
No mining needed. Break these for copper bits (20 bits = 1 ingot):
- cable spools (Levels 1 and 3), about 4 each
- machine cabinets (Level 2)
- stacked pipes (Level 3), which give lead as well
- industrial fans (Level 3)
[Scrap wire](item-backrooms:scrapwire) melts to copper too: 10 wire = 1 ingot. Copper needs a hotter fire than wood gives: use the coal heaped by Level 3's generators and Level 5's boilers, charcoal from crates, or burn your own [charcoal](craftinginfo-charcoalburning). [Smelt](craftinginfo-smelting) in the crucible and cast a pickaxe and a hammer, then save 9 ingots for an anvil. Toolboxes (Level 1, later garages and hardware stores) sometimes hold a copper hammer, chisel, saw or knife.

**Comfort: Levels 4 and 5**
Level 4 is the calmest place before the city: rest there. Its fridges hold fruit and cheese, and its fountains, coolers and vending machines give Almond Water. Level 5's beds come away as real beds (break the head end), its wardrobes and suitcases hold clothes, its bedding is linen for sacks, and its boiler halls have coal. Hotel silverware gives silver bits; luggage carts, ashtray stands and candelabras give brass.

**Bronze and iron: Level 8**
Level 8 is real rock, and it can be mined: native copper, malachite, tin (cassiterite), zinc (sphalerite), bismuth, gold in quartz, lead, coal, and the iron ores limonite, hematite and magnetite. There is no silver ore: silver comes from the hotel. Loose ore and stones lie on the cave floors. Bring a pickaxe, light and food; drifters hunt in the dark, and the lamps of the 9th Road are the safe line through. From here bronze, iron and steel are made exactly as the other guides say.

**Salt, lime, leather**
Level 8's limestone and chalk grind to lime in a quern, and its halite to salt. There is a quern in the barns of Level 10. Hides come from the wildlife of Level 9 and the livestock of Level 10.

**Wood: Levels 7, 9 and 10**
Driftwood on Level 7's sea is firewood. Levels 9 and 10 have real trees to fell.

**Farming: Levels 9 and 10**
Level 10's fields stand ripe: spelt, rye, flax and vegetables. Seed sacks are in barns, sheds and garages. The old fields are exhausted, so replant in fresh soil: hoe grass in Level 10 or a lawn in Level 9. It never rains, so [farm](gamemechanicinfo-farming) within 3 blocks of a pond. Level 10 also has livestock in its paddocks ([husbandry](gamemechanicinfo-animalhusbandry)), bee skeps by the farmhouses, berry bushes, and cattails at the ponds for hand baskets. Do not dig below the soil in Level 10.

**The city: Level 11**
Reached only through a barn wall in Level 10. Stores full of food, tools and clothes, safe streets, and elevators and doors back to almost every level: see [Ways Between Levels](backrooms-thresholds).
""")

PAGES["stability"] = ("Reality Stability", """
**Reality Stability**
*Some places hold you. Most do not.*

The gear between your health and hunger shows how firmly you are anchored. Where it turns clockwise you recover; where it turns backwards you drain. As it empties the world distorts, and at zero you take damage until you recover.

**Places that restore you**
- Level 0: the Manila Room
- Level 1: the car park
- Level 4: all of it
- Level 5: the Beverly Room
- Level 6.1, the Snackrooms
- Level 8: on the 9th Road
- Level 10 and Level 11

**Places that drain you**
- Level 0: blackout zones, and worst of all the Red Rooms (red wallpaper, red lamps: take what is there and leave)
- Level 1: the maintenance corridors, a little
- Level 2: everywhere
- Level 3: everywhere, and worst of all in its flooded tunnels
- Level 5: the corridors, and above all the boiler halls
- Level 6: the dark
- Level 7: the deeper you dive
- Level 8: off the road
- Level 9: everywhere

**Ways to recover**
- Stand somewhere the gear turns clockwise.
- Drink [Almond Water](item-backrooms:almondwater): each bottle restores 15%. Cashew water restores 8%.
- A [temporal gear](item-gear-temporal) in your left hand, a knife in your right, hold {rightmouse}: the gear's stability passes to you, at the cost of the gear and some health.

**Reality Shifts**
About once every 30 in-game hours (an hour of play), the lights fail for 2 to 4 in-game hours. Everything beyond a few steps is lost in black, and stability drains everywhere while it lasts. None comes in your first 30 hours. When the lights go: stop, light a candle or a torch, drink Almond Water if the gear runs low, and wait in a room you know.

There are no temporal storms here.
""")

PAGES["salvage"] = ("Salvage and Recipes", """
**Salvage and Recipes**
*What to break, and what to make of it.*

**Backrooms recipes**
- [Glass shiv](item-backrooms:glassshiv) (knife, 60 uses) = glass shard + wallpaper strip + carpet fibre
- [Improvised scraper](item-backrooms:scraper) (knife, 180 uses) = metal bracket + wallpaper strip + 2 carpet fibres
- 1 dry grass = 2 wallpaper strips
- 1 flax twine = 3 carpet fibres
- [Carpet bag](item-backrooms:carpetbag) (3 slots) = 5 carpet fibres + 1 flax twine
- 2 sticks = 1 rotten wood, or 1 plank + a knife
- 1 firewood = 2 rotten wood, or 3 planks + an axe
- 1 nails and strips = 2 metal brackets
- [Surveyor's chalk](item-backrooms:chalk) = 1 chalk stone
- Crucible: 20 metal bits = 1 ingot. 10 scrap wire = 1 copper ingot.
Knives and axes are not used up by these, only worn.

**Recipes you will want early**
- Fire starter = 1 dry grass + 2 sticks
- Torch = 2 dry grass + 1 stick
- Firepit = dry grass placed on the floor + 4 firewood
- Linen sack (5 slots) = flax twine + linen
- Chest = 8 planks + 1 nails and strips
- Hay bed = 3 hay
- Knife, axe, spear, shovel, hoe = a [knapped](craftinginfo-knapping) head + 1 stick

**Cutting (hold a blade, {rightmouse})**
- Level 0's yellow wallpaper: wallpaper strip
- Level 0's dry carpet: carpet fibres
A bare glass shard works but may snap. Other levels' walls and floors cannot be cut.

**What gives what when broken**
- **Glass shards:** dead light fixtures (1 or 2); desks, photocopiers, televisions, curio cabinets, phone booths.
- **Metal brackets:** dead lights, metal shelving, office chairs, filing cabinets, stacked chairs, folding furniture, hospital beds, shopping carts, crates.
- **Scrap wire:** machine cabinets, machine parts, photocopiers, desks, televisions, industrial fans, washing machines, toolboxes, crates. Rarely above ceiling tiles.
- **Copper bits:** cable spools (about 4), machine cabinets, stacked pipes (with lead), industrial fans, parking meters, phone booths.
- **Silver bits:** curio cabinets, room service trolleys, hotel dining tables. **Brass bits:** luggage carts, ashtray stands, candelabras.
- **Planks:** desks (2), bookshelves (3), workbenches (3), pallets (3), wardrobes (3), pews (3), conference and dining tables and reception desks (4), plywood (2), crates, most hotel furniture.
- **Nails and strips:** barrels of nails (2), workbenches, pallets, toolboxes, crates.
- **Rotten wood:** trash cans, wastebaskets, wheelie bins, dumpsters, televisions. Rarely above ceiling tiles.
- **Sticks and dry grass:** supply boxes, supply crates. Sticks also from potted plants and coat stands; dry grass from cardboard boxes and bedrolls.
- **Cloth:** sofas, wing chairs, office chairs, partitions, bedrolls, suitcases, laundry carts. **Linen:** hotel beds (the foot end), tents, hotel dining tables.
- **Clothes:** wardrobes, suitcases, dressers, clothes racks.
- **Paper:** desks, filing cabinets, photocopiers, bookshelves, mailboxes, newspaper boxes.
- **Candles:** supply boxes, crates, nightstands, candelabras (2).
- **Rope and twine:** crates, toolboxes, tents, tool shelves, lost backpacks.
- **Bandages:** medical cabinets, hospital beds, lost backpacks.
- **Coal:** coal piles (about 6). **Charcoal:** crates, barbecue grills.
- **Seeds:** seed sacks. **Soil:** potted plants.
- **A real bed:** a hotel bed's head end.
- **Tools, now and then:** toolboxes (copper hammer, chisel, saw, knife); tool shelves (hammer, saw, shovel); tool racks (hoe, scythe, shovel); kitchen cupboards and lost backpacks (knife); waterlogged crates (raft, fishing pole).
- **Chalk:** rarely above ceiling tiles; lost backpacks.
- **Rusty gears:** reception desks, mahjong tables, curio cabinets, toy boxes, trash cans. Supply boxes hold one now and then, and very rarely a temporal gear.

**Food and drink**
- **Almond Water:** supply boxes, supply crates, drums; fountains, coolers and vending machines (Level 4, the city); seeps in the rock beside Level 8's road; vendors' carts (the city). Each has a few bottles; the Snackrooms' machines and the carts restock weekly.
- **Crackers, canned beans:** supply boxes, crates, cardboard boxes, fridges, pantries.
- **Fruit and cheese:** fridges (Levels 4, 9, the city).
- **Flour, salt, fat:** kitchen cupboards and pantries (Level 9, city groceries).
- **Chips, chocolate, soda:** the Snackrooms; city stores.
- **Fish:** Level 7. **Game:** Level 9. **Crops, livestock, honey, berries:** Level 10.
""")

PAGES["levels"] = ("The Levels", """
**The Levels**
*Each lies around the one before, like rings. Walk outward and you pass through them all, but it is a walk of many kilometres.*

**Level 0, the Lobby.** Yellow wallpaper, damp carpet, humming lights. Supply boxes, glass, strips and fibres. Blackout zones drain you; the Manila Room restores you. Pits drop into Level 2. Rooms papered in red hold untouched boxes, and drain you faster than anywhere: be quick.

**Level 1, the Habitable Zone.** A concrete car park and white maintenance halls. Supply crates (food, planks, twine, charcoal), pallets, workbenches, toolboxes, cable spools, loose stones and flint, wanderers' camps. Stable in the car park. Stairwells lead to other stairwells.

**Level 2, Pipe Dreams.** Hot, narrow, dark tunnels. Machine cabinets (copper), drums, trolleys, toolboxes, machine parts. Steel doors in the walls: most locked, some storerooms, a few lead to another level. Drains you everywhere: pass through.

**Level 3, the Electrical Station.** Brick, tile and machinery. Cable spools, stacked pipes, coal by the generators, clay in the flooded tunnels below the manholes. Drains you. Elevators.

**Level 4, the Abandoned Office.** Quiet and safe. Furniture for planks and paper, fridges, Almond Water on tap. A few vending machines take you instead of serving you. Elevators and stairwells.

**Level 5, the Terror Hotel.** Beds, clothes, linen, silver and brass, coal in the boiler halls. The corridors wear on you; the Beverly Room is safe. Elevators; a few locked doors open; staff stairs lead to Level 6.

**Level 6, Lights Out.** Total darkness. Hold the brightest light you have and mark your way with [chalk](item-backrooms:chalk): chalk marks show white on the map. Lost backpacks. Stairs down, found by the sound of waves, drop you into Level 7.

**Level 6.1, the Snackrooms.** Sealed food courts, bright and safe, their machines and shelves full. You cannot walk in, and every door out shuts behind you.

**Level 7, Thalassophobia.** A cold sea under a concrete ceiling. Driftwood, fish, islands of basalt (some with an abandoned camp), wrecks on the bottom. Deeper is darker and less stable.

**Level 8, Cave Systems.** Real rock, ore and clay, in the dark, with drifters. Keep to the lamps of the 9th Road and its camps. Almond Water seeps from the rock beside the road: use a seep to fill a bottle.

**Level 9, the Suburbs.** Endless night. Houses to search: kitchens, pantries, garages with tools and seeds, dressers of clothes. Trees, berry bushes, game. The streets drain you.

**Level 10, Bumper Crop.** Farmland under a grey sky, safe and stable. Crops, livestock, ponds with cattails and clay, bee skeps, barns with a quern. A metre under the soil is a mass of worms: do not dig down.

**Level 11, the Endless City.** Not a ring: far out past the fields, reached through a barn wall. Safe. Stores, diners, a subway, Almond Water everywhere, and ways back to every level.

**Getting on.** Where two levels meet there is a wall with doorways through it; follow it to find one. Level 8 is solid rock, entered and left only where its road runs through. Signs of the next level creep in before you reach it: concrete under worn carpet, pipes along a ceiling, hotel red in an office.
""")

PAGES["thresholds"] = ("Ways Between Levels", """
**Ways Between Levels**
*The rings are only how the place is built. The doors are the real map.*

**The two rules**
- Every threshold always leads to the same place. Mark both ends on your map.
- If you walked through it, you can walk back. If you fell, dived or were taken, you cannot.

**Coming back**
An elevator arrives beside another elevator, a stairwell beside a stairwell, a door beside a locked door: that one is now your way back. Where there is nothing of the kind, a **thin spot** is left where you arrived: a pale, wavering seam in the air that hums. {rightmouse} it to step back through. It stays for good.

**Two-way**
- Elevators (Levels 3, 4, 5): to another elevator in Levels 3 to 5; from the hotel, sometimes Level 1. Everyone in the car rides along.
- Level 1 stairwells, climbed: another stairwell in Level 1, sometimes Level 4.
- Level 4 stairwells, climbed: another on the same floor, sometimes Level 0.
- Level 5 doors: most are locked for good. A few open, onto the hotel, Level 3 or Level 0.
- Level 5 staff stairs (an open door under a STAFF sign): Level 6.
- Level 2 steel doors in the tunnel walls: most are locked. Some open, onto Level 3, Level 4 or Level 1.
- Level 8 vents beside the 9th Road: Level 2.
- Level 9, the gate at the end of a field behind the houses: Level 10.
- Level 10, a stretch of barn wall that is not quite there (east wall, between the stalls, in some barns): Level 11.

**Two-way, from the city (Level 11)**
- Office tower elevators: Level 4. Hotel elevators: Level 5.
- Apartment basement door: Level 0.
- Parking garage ramp down: Level 1.
- Subway maintenance door: Level 2.
- Substation door: Level 3.
- A dark doorway off an alley: Level 6.
- A rowhouse's front door: Level 9.
- A diner's kitchen door: the Snackrooms. The kitchen door you come out of leads back.
- A patch of wheat in a park: Level 10.

**One-way**
- Level 0 pits: Level 2.
- Level 4, a vending machine that takes you (the same few always do): the Snackrooms.
- Level 6, a wire across a passage: the Snackrooms.
- Level 6, stairs down toward the sound of waves: Level 7, from the ceiling.
- The Snackrooms: rusty doors to Level 6, glass doors to Level 4 or 5, vents to Level 3, kitchen doors to another food court.
- Level 7, diving into the ring of standing stones: Level 9. Swimming into a cave mouth in the deep: Level 8.
- Level 10, diving to the bottom of a pond: Level 7.
- The city: an open manhole to Level 2, a caved-in street to Level 8, the deep middle of a park fountain to Level 7.

**Good to know**
- A threshold that has become a way back no longer leads where it once would have.
- Using a temporal gear sets where you return to when you die. Set it beside a thin spot or an elevator you know.
""")


def to_vtml(text):
    """Turns the light markup above into the handbook's rich text."""
    text = text.strip().replace("\r\n", "\n")
    text = re.sub(r"\[([^\]]+)\]\(search:([^)]+)\)", r'<a href="handbooksearch://\2">\1</a>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="handbook://\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"\{(\w+)\}", r"<hk>\1</hk>", text)
    return text.replace("\n", "<br>")


def fill():
    for code, (title, text) in PAGES.items():
        LANG[f"guide-{code}-title"] = title
        LANG[f"guide-{code}-text"] = to_vtml(text)


def check():
    """Every link to one of our own items or blocks must name something that exists."""
    items = {os.path.splitext(f)[0] for root, _, files in os.walk(os.path.join(ASSETS, "itemtypes")) for f in files}
    bad = []
    for code, (_, text) in PAGES.items():
        for target in re.findall(r"\]\(((?:item|block)-backrooms:[^)]+)\)", text):
            if target.split(":", 1)[1] not in items:
                bad.append((code, target))
    return bad


if __name__ == "__main__":
    from gen_detail import merge_lang
    LANG.clear()
    fill()
    merge_lang()
    for code, (title, text) in PAGES.items():
        print(f"{code:12} {len(to_vtml(text)):5} characters  {title}")
    problems = check()
    print("links ok" if not problems else f"BROKEN LINKS: {problems}")
