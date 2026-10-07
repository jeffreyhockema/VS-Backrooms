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

This guide covers your first hours in Level 0. Then read [Making a Home](backrooms-home) and [Finding the Way](backrooms-finding), and keep [Salvage and Recipes](backrooms-salvage), [The Levels](backrooms-levels), [Ways Between Levels](backrooms-thresholds) and [Reality Stability](gamemechanicinfo-temporalstability) to hand. The other guides describe ordinary worlds: their crafting is right, but where they say to find things is not.

**What is different here**
- Loose things come away whole, with whatever is in them: boxes, furniture, ceiling tiles, lights. The building breaks too, with the right tool, but only *down*: drywall to dust and the odd stick, concrete to rubble. Each level's roof, its doors and its elevators never break. See [Salvage and Recipes](backrooms-salvage).
- Nothing grows. Under every floor lie a few metres of concrete, and under that the ground of any world: rock, caves and ore. Bring a copper pickaxe. Everything else you need was left by someone else.
- No rain, no seasons, no winter, no thirst. Hunger runs a little faster than usual, and faster still in the hot levels.
- **You only ever wake up in Level 0.** Die anywhere and you wake in the Lobby; what you carried stays where you fell. Leaving Level 0 is an expedition: plan to come back.

**1. Open supply boxes**
Two supply boxes stand a few steps from where you wake. Break them (hold {leftmouse}). Others are rare, and were mostly left in twos and threes in the corners of rooms. They show red on the map.
- A **sealed** box (lid on, taped shut) gives a few of: Almond Water, crackers, canned beans, carpet fibres, wallpaper strips, a glass shard, [flint](item-flint), sticks, dry grass; sometimes a candle, a metal bracket or a [wanderer's note](item-backrooms:wanderernote-door).
- A **torn** box (lid hanging open) was gone through long ago: scraps, never food. You can tell from across the room.
Food is scarce. Every sealed box counts.

**2. Get a blade**
Break a light panel in the ceiling for [glass shards](item-backrooms:glassshard): a dead (dark) one costs you nothing, a lit one costs you its light. A bare shard cuts, but snaps about one use in four. Make it a tool:
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
Crackers and canned beans fill you. [Almond Water](item-backrooms:almondwater) fills you a little, heals 1 and restores stability. Level 0 has no food but what is in the boxes. You burn food walking, faster running, and hardly at all standing still. Level 1's sealed crates are the nearest real food: the first trip out is for those.

**8. Carry more**
You have 10 slots and room for 4 bags. Make bags before you do anything else in Level 0:
- [Carpet bag](item-backrooms:carpetbag) (3 slots) = 5 carpet fibres + 1 flax twine. Four of them cost 32 cuts of carpet.
- Linen sack (5 slots) = flax twine + linen (hotel beds and tents).
- Chest = 8 planks + 1 nails and strips. 2 metal brackets = 1 nails and strips.
Hand baskets need cattails, which only grow in Level 10.

**9. Find the way on**
The map (M) shows only what you have seen, and remembers it. Level 0 ends somewhere between 450 and 3,000 blocks from where you woke, but the wall where it ends is solid, with a gap only every few hundred blocks. Worn carpet and missing ceiling tiles mean Level 1 is near; chalk arrows on the walls point to a gap; a [wanderer's note](item-backrooms:wanderernote-door) may tell you where one is. See [Finding the Way](backrooms-finding).

**10. Watch the gear**
The gear between your health and hunger is your [Reality Stability](gamemechanicinfo-temporalstability). If it turns backwards, move on.

**11. Things in the dark**
You will hear things before you see them, and see them far off before they come near. If you see eyes in the dark, raise your light and walk, don't run. Running, breaking things and staying out long all draw them. Read [What Lives Here](backrooms-entities).

**12. Make a home**
Before you go far, read [Making a Home](backrooms-home).
""")

PAGES["progression"] = ("Progression Guide", """
**Progression Guide**
*The way from a shard of glass to steel is the usual one. Only the places are strange.*

**Scavenger: Level 0**
Supply boxes, a glass blade, wallpaper strips and carpet fibres, four carpet bags, two flints. See the [Starter Guide](craftinginfo-starterguide). Then the first expedition: find a gate into Level 1, bring back planks and food, and [make a home](backrooms-home).

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

**Bronze and iron: the ground, and Level 8**
With a copper pickaxe, break through any floor: under 8 blocks of concrete is the ground of any world, with its rock strata, caves and ore, and you [prospect](item-prospectingpick-copper) and mine it exactly as the other guides say. The ores lie where they would anywhere, deeper ones deeper. Level 8 is the same ground laid open: native copper, malachite, tin (cassiterite), zinc (sphalerite), bismuth, gold in quartz, lead, coal, and the iron ores limonite, hematite and magnetite, with loose ore and stones on the cave floors and no digging to get at them. There is no silver ore there: silver comes from the hotel, or from deep galena. Bring light and food; drifters hunt Level 8's dark, and the lamps of the 9th Road are the safe line through. From here bronze, iron and steel are made exactly as the other guides say.

**Salt, lime, leather**
Level 8's limestone and chalk grind to lime in a quern, and its halite to salt. There is a quern in the barns of Level 10. Hides come from the wildlife of Level 9 and the livestock of Level 10.

**Wood: Levels 7, 9 and 10**
Driftwood on Level 7's sea is firewood. Levels 9 and 10 have real trees to fell.

**Farming: at home, then Levels 9 and 10**
You can farm in Level 0: see [Making a Home](backrooms-home). Seed packets turn up in garden sheds and kitchens (Level 9) and now and then in a supply box; seed sacks are in Level 10's barns; wanderers sell seeds. Level 10's fields stand ripe: spelt, rye, flax and vegetables. The old fields are exhausted, so replant in fresh soil: hoe grass in Level 10 or a lawn in Level 9. It never rains, so [farm](gamemechanicinfo-farming) within 3 blocks of water. Level 10 also has livestock in its paddocks ([husbandry](gamemechanicinfo-animalhusbandry)), bee skeps by the farmhouses, berry bushes, and cattails at the ponds for hand baskets. Do not dig below the soil in Level 10.

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

PAGES["home"] = ("Making a Home", """
**Making a Home**
*You only ever wake up in Level 0. Make it somewhere worth waking up.*

**Why**
Die anywhere and you wake in the Lobby, with nothing; what you carried lies where you fell, in a level you cannot wake up in. Every trip out is an expedition, and the Lobby is where it starts and ends.

**Where**
- Where you woke is home until you move it. A [temporal gear](item-gear-temporal), held and used ({rightmouse} on the floor) anywhere in Level 0, moves it there. Elsewhere it will not take hold.
- Good places: the Manila Room (nothing hostile goes in); beside a way out you know; beside a flooded room (water for a farm).
- Within about 50 blocks of home counts as resting.

**What a home needs, and where it comes from**
- **Walls where you want them.** Break out drywall with any tool (an axe is quickest) to join rooms or close off a corner; concrete takes a copper pickaxe. Wall up the rest with [rubble masonry](block-backrooms:rubblemasonry), 4 rubble each. Only the roof over a level, and the top of the walls between levels, never give.
- **A door.** Nothing in the Backrooms opens doors. Planks from Level 1's crates and Level 4's furniture.
- **Storage.** A chest (8 planks + nails and strips); baskets from Level 10's cattails.
- **Light and fire.** Torches, a firepit, Firesalt from Level 3. When a Reality Shift puts the lights out, eyes come to the edge of the dark, even here.
- **Cold storage.** Level 0's blackout zones are cold and damp (10 °C): food in a chest there spoils at less than half the rate.
- **A farm.** Soil from potted plants (Levels 4 and 5), seeds (seed packets, Level 10's barns, wanderers), a hoe, and water within 3 blocks: a flooded room, or a bucket. Crops grow under the ceiling lights, a little slower than in daylight, and hardly at all in the cold of the blackouts. Plant under a working light, not a dead one.
- **A bed.** A hotel bed's head end (Level 5) comes away as a real bed.

**Food that comes back**
Nothing in Levels 0 to 5 restocks but the Snackrooms. What does: fish (Level 7), game and berries (Level 9), crops, livestock and honey (Level 10), and a farm of your own. Preserve with salt (Level 8's halite, ground in a quern), honey, or a sealed crock.
""")

PAGES["finding"] = ("Finding the Way", """
**Finding the Way**
*Reaching the wall is not reaching the next level.*

**Gates**
Where two levels meet, the wall is solid but for a gate every few hundred blocks: a doorway, two or three wide (in Level 1, under an EXIT sign). Walking along the wall to find one is walking the most dangerous ground in the level. In Levels 0, 2 and 6 a hallway runs along the inside of that wall: follow it. The first time you walk through a gate it is marked on your map.

**Signs of a gate**
- **Chalk arrows** on the walls, left by those who came before, point the way to the nearest gate. Chalk shows white on the map, so an arrow you have seen is a lead.
- **Crosses in chalk** mean keep out: a den is near.
- **Wanderers' notes** ({rightmouse} to read) mark a place on your map: a note of a door, the nearest gate; of a way, the nearest elevator, stairwell or pit; of something left, the nearest sealed box or crate; of a refuge, the nearest safe place or trader. A note that tells of nothing near is kept, to read somewhere else.

**Ways through**
Elevators, stairwells, doors and pits are the other ways between levels, often far shorter. Each is marked on your map the first time you take it, with the way back where there is one. See [Ways Between Levels](backrooms-thresholds).

**Locked doors**
Every level has rooms behind locked doors that nobody has been into since. A [pry bar](item-backrooms:prybar) forces one in a few seconds, for good, if there is a room behind it: and everything near hears. A door set in solid wall will not give, and a door that goes somewhere is not locked at all.

**Expeditions**
- The longer you are out without resting, the more the Backrooms notice you. Rest by a fire, beside a wanderer or in a safe place, then go on.
- An outpost (a firepit, a chest, some Firesalt) halfway along a route you use makes it safe to stop.
- The hot levels (2, 3, the boiler halls) burn food faster. The cold ones (6, 8) want warm clothes.
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
- [Pry bar](item-backrooms:prybar) (24 uses) = 2 metal brackets + 1 iron nails and strips
- 4 seeds = 1 [seed packet](item-backrooms:seedpacket-turnip), opened in the grid
- [Surveyor's chalk](item-backrooms:chalk) = 1 chalk stone
- Salt poultice (as good as the best poultice there is) = 2 [Epsom salt](item-backrooms:epsomsalt) above 1 linen
- Crucible: 20 metal bits = 1 ingot. 10 scrap wire = 1 copper ingot.
- [Rubble masonry](block-backrooms:rubblemasonry) = 4 [rubble](item-backrooms:rubble) (2 by 2): a rough block to build with
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

**Breaking the building**
Walls, floors and fixtures break like anything else, with the tool their material calls for, but they break *down*: bash out a wall and you get rubble and scraps, never the wall back. Breaking anything is loud.
- **Drywall, plaster, wallpaper** (Levels 0, 4 and 5, the houses): any tool, an axe best; bare hands take a very long time. Dust, now and then a stick or a wallpaper strip.
- **Boards, panelling, floorboards, roofs:** the same. Sticks, a little firewood, rarely a plank.
- **Concrete, brick, tile, marble, every floor slab:** a copper pickaxe, as for rock. [Rubble](item-backrooms:rubble); carpeted floors some carpet fibres. Under every floor is 8 blocks of concrete, then the ground: rock, caves and ore, as in any world.
- **Pipes, railings, poles, machinery:** a copper pickaxe. Metal brackets; wired things a little scrap wire; pipes now and then a copper or lead bit.
- **Glass:** anything. Glass shards.
- **Rock** (Level 8, the cliffs): a copper pickaxe, and it gives stones and ore as anywhere.
- **Wrecks:** an abandoned car comes apart with a copper pickaxe, all of it at once: brackets, wire, glass, a little copper.
- **Lights**, lit or dead: anything. Glass shards, a bracket, some wire; a lit one's light goes with it.
- **Never:** each level's roof, the solid top of it with nothing open above (in Level 0, the slab over the crawlspace: the ceiling tiles and the crawlspace come down); the wall between two levels from that height up (below it, the wall breaks like any other); doors, elevators, vents, vending machines, fountains and anything else that leads elsewhere or gives. The block info says so when you look at one.

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
- **Seeds:** seed sacks (Level 10); seed packets (tool shelves, kitchen cupboards, now and then a supply box). **Soil:** potted plants.
- **Pry bars:** tool shelves, toolboxes, workbenches; or make one.
- **Wanderers' notes:** supply boxes, torn boxes, desks, filing cabinets, writing desks, tents, bedrolls, and above all lost backpacks.
- **A real bed:** a hotel bed's head end.
- **Tools, now and then:** toolboxes (copper hammer, chisel, saw, knife); tool shelves (hammer, saw, shovel); tool racks (hoe, scythe, shovel); kitchen cupboards and lost backpacks (knife); waterlogged crates (raft, fishing pole).
- **Chalk:** rarely above ceiling tiles; lost backpacks.
- **Rusty gears:** reception desks, mahjong tables, curio cabinets, toy boxes, trash cans. Supply boxes hold one now and then, and very rarely a temporal gear.

**Food and drink**
Only sealed boxes and crates hold food; most are found torn or prised open. Rooms behind locked doors were never picked over (see the pry bar), and neither were dens.
- **Almond Water:** supply boxes, supply crates, drums; fountains, coolers and vending machines (Level 4, the city); seeps in the rock beside Level 8's road; vendors' carts (the city). Each has a few bottles; the Snackrooms' machines and the carts restock weekly.
- **Crackers, canned beans:** supply boxes, crates, cardboard boxes, fridges, pantries.
- **Fruit and cheese:** fridges (Levels 4, 9, the city).
- **Flour, salt, fat:** kitchen cupboards and pantries (Level 9, city groceries).
- **Chips, chocolate, soda:** the Snackrooms; city stores.
- **Fish:** Level 7. **Game:** Level 9. **Crops, livestock, honey, berries:** Level 10.
- **Level 37 has no food at all.** Take enough with you.
- **Level 94 has plenty:** iceboxes in every house (cheese, butter, beans), [Almond Milk](item-backrooms:almondmilk) in the milk vans by the towns' plazas (they restock weekly), Almond Water from the towns' fountains and the hilltop water towers (they fill a bottle and come back).
- **[Epsom salt](item-backrooms:epsomsalt):** crusts of it dried on the rims in Level 37's dark corners.
- **[Red Water](item-backrooms:redwater):** red sprouts at the bottom of the Sanguine Reservoir (Level 37.1). It heals every wound, and lowers for good how steady you can ever be again.
""")

PAGES["levels"] = ("The Levels", """
**The Levels**
*Each lies around the one before, like rings. But the walls between them are solid, but for a few gates.*

**Level 0, the Lobby.** Yellow wallpaper, damp carpet, humming lights. A labyrinth of rooms and winding hallways that turn every few dozen steps, open into rooms and end blind; there is always more than one way. Supply boxes, glass, strips and fibres. Blackout zones drain you; the Manila Room restores you. Pits drop into Level 2. Rooms papered in red hold untouched boxes, and drain you faster than anywhere: be quick.

**Level 1, the Habitable Zone.** A concrete car park, walled into districts with gaps where the aisles run through, and white maintenance halls. Supply crates (food, planks, twine, charcoal), pallets, workbenches, toolboxes, cable spools, loose stones and flint, wanderers' camps. Stable in the car park. Stairwells lead to other stairwells.

**Level 2, Pipe Dreams.** Hot (you go hungry faster), dark tunnels: the three-wide mains run straight on for miles; the narrow ones between them often end. Machine cabinets (copper), drums, trolleys, toolboxes, machine parts. Steel doors in the walls: most locked, some storerooms, a few lead to another level. Drains you everywhere: pass through.

**Level 3, the Electrical Station.** Hot brick, tile and machinery: carry food. Cramped tangles and stooping squeezes, wide galleries, vast transformer halls. Cable spools, stacked pipes, coal by the generators, clay in the flooded tunnels below the manholes. Drains you. Elevators.

**Level 4, the Abandoned Office.** Quiet and safe. Furniture for planks and paper, fridges, Almond Water on tap. A few vending machines take you instead of serving you. Elevators and stairwells stand together in building cores, with restrooms.

**Level 5, the Terror Hotel.** Beds, clothes, linen, silver and brass, coal in the boiler halls. The corridors wear on you; the Beverly Room is safe. Elevators; a few locked doors open; staff stairs lead to Level 6.

**Level 6, Lights Out.** Cold, total darkness. Hold the brightest light you have and mark your way with [chalk](item-backrooms:chalk): chalk marks show white on the map. Keep to the long dry corridors; passages wet underfoot end blind. Lost backpacks. Stairs down drop you into Level 7: listen for the waves, which grow louder the nearer you come, and look for arrows chalked along the corridors.

**Level 6.1, the Snackrooms.** Sealed food courts, bright and safe, their machines and shelves full. You cannot walk in, and every door out shuts behind you.

**Level 7, Thalassophobia.** A cold sea under a concrete ceiling. Driftwood, fish, islands of basalt (some with an abandoned camp), wrecks on the bottom. Deeper is darker and less stable.

**Level 8, Cave Systems.** Cold real rock, ore and clay, in the dark, with drifters. Dress warmly. Keep to the lamps of the 9th Road and its camps; its side roads often end in rock, its main roads run through. Almond Water seeps from the rock beside the road: use a seep to fill a bottle.

**Level 9, the Suburbs.** Endless night. Houses to search: kitchens, pantries, garages with tools and seeds, dressers of clothes. Trees, berry bushes, game. The streets drain you.

**Level 10, Bumper Crop.** Farmland under a grey sky, safe and stable. Crops, livestock, ponds with cattails and clay, bee skeps, barns with a quern. A metre under the soil is a mass of worms: do not dig down.

**Level 11, the Endless City.** Not a ring: far out past the fields, reached through a barn wall. Safe. Stores, diners, a subway, Almond Water everywhere, and ways back to every level.

**Level 37, Sublimity (the Poolrooms).** Not a ring either. White tile and warm, still water, rooms and pools that make no sense, light falling through slits from somewhere you never see, and corners left in the dark. Nothing lives here; no one has ever met anyone. Standing in lit water heals you, steadies you and counts as rest, so it is the place to recover between expeditions. But there is no food at all, the dark corners drain you, and the deep water is where people drown: stair pits go down further than you can see, and some passages are a swim under a wall. Crusts of [Epsom salt](item-backrooms:epsomsalt) dry on the rims in the dark.

**Level 37.1, the Sanguine Reservoir.** Far out in the Poolrooms, the light thins, the water turns thick and slow and red, and red sprouts on the pool floors are all the light there is. A distant chanting draws people in, louder the nearer you come. Stability drains fast. What the drowned left lies on the bottom, untouched; and the red water heals everything, at a price.

**Level 94, Motion.** Not a ring: you fall into it out of the sky, and land softly. A stop-motion picture of the 1950s: round green hills, a two-storey cream house on each, winding roads behind white picket fences, small towns round fountains of Almond Water, siren poles playing the same tune all day. Food in plenty, and the ground is clay: dig the turf for soil, and the red modelling clay under it for clay. **By night the Animations come out**, and hunt anything that does not look animated: be indoors by dusk (when the tune slows and goes flat, it is nearly time), or stand quite still and be taken for a doll. Towards the middle the houses come apart, room by room, into heaps of furniture; follow the strangeness and you reach the glass mountain and the King's castle.

**Getting on.** Where two levels meet there is a solid wall, with a gate (a doorway through) only every few hundred blocks: see [Finding the Way](backrooms-finding). Level 8 is solid rock, entered and left only where its road runs through. Signs of the next level creep in before you reach it: concrete under worn carpet, pipes along a ceiling, hotel red in an office.
""")

PAGES["thresholds"] = ("Ways Between Levels", """
**Ways Between Levels**
*The rings are only how the place is built. The doors are the real map.*

**The two rules**
- Every threshold always leads to the same place. Both ends are marked on your map the first time you go through.
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
- Public baths, a cyan door marked POOL: Level 37.
- A cinema: walk up to the screen and on into the picture: Level 94.

**Two-way, to and from Levels 37 and 94**
- Level 5, now and then a locked door is a cyan door marked POOL: Level 37, out of one of its own POOL doors. Level 37's POOL doors lead out into the hotel.
- Level 37, a long dry corridor whose tile gives way to office carpet: walk on into Level 4.
- Level 37, the black round mouth at the end of a tunnel of arches: Level 7, over the sea.
- Level 9, a doll's house (too clean, too cream): its front door opens onto a house on the hills of Level 94. One house in forty there opens back onto the Suburbs.
- Level 94, a rusted gate with no sign on a hilltop, at twilight only (dusk and dawn): Level 10.

**One-way**
- Level 0 pits: Level 2.
- Level 4, a vending machine that takes you (the same few always do): the Snackrooms.
- Level 6, a wire across a passage: the Snackrooms.
- Level 6, stairs down toward the sound of waves: Level 7, from the ceiling.
- The Snackrooms: rusty doors to Level 6, glass doors to Level 4 or 5, vents to Level 3, kitchen doors to another food court.
- Level 7, diving into the ring of standing stones: Level 9. Swimming into a cave mouth in the deep: Level 8.
- Level 10, diving to the bottom of a pond: Level 7.
- The city: an open manhole to Level 2, a caved-in street to Level 8, the deep middle of a park fountain to Level 7.
- Level 7, a patch of white tile on the seabed in the twilight zone, faintly lit: dive to it and surface in Level 37.
- Level 9, the rare backyard pool that is still full, lit teal at midnight: dive to its bottom, Level 37.
- Level 37, the bottom of a pit nobody has found the bottom of: you come up in a backyard pool in Level 9.
- Level 94, the door of a house full of water: Level 7.
- Level 94, winning the King's trial: you are carried to Level 1, Level 4, or back to a town in Level 94.

**Good to know**
- A threshold that has become a way back no longer leads where it once would have.
- You only ever wake up in Level 0. A temporal gear still moves where you wake, but only within Level 0: elsewhere it will not take hold (and is not used up). Two-way ways that come out in Level 0 (a Level 4 stairwell, a hotel door, a city basement) make good places for a home.
""")


PAGES["entities"] = ("What Lives Here", """
**What lives in the Backrooms**
*Most of what you hear will never touch you. Learn what keeps each thing back.*

**How danger works**
- The heart of each level is quietest: sounds down the hall, something seen far off that goes when you come near.
- Further out, things follow you at a distance and wait for you to falter.
- Near the edge into the next level, and near elevators, stairs, pits and other ways through, they hunt.
- Things come bolder when you stand in the dark, when your [Reality Stability](gamemechanicinfo-temporalstability) is low, when you run, when you make noise (breaking things open, forcing doors), the longer you have been out without resting, and during a Reality Shift. After a close call they leave you be for a while.
- **Resting:** a minute by a lit firepit or burning Firesalt, beside a wanderer, somewhere nothing hostile goes, asleep in a bed, or at home in Level 0. A firepit and a chest halfway along a long route make an outpost.
- **Dens:** some places are where something lives. Bones on the floor, a grey papery hive, crosses chalked on the walls round about: inside, it is as dangerous as the edge of the level. At the heart of every den are two or three sealed boxes nobody has dared take.
- Running for a gate runs into whatever waits there: near the edge, they wait on the way you are going.
- **Every level is worse than the last.** Deeper down, everything is quicker (from Level 3 a Hound outruns you; a Smiler always does, in the dark), hits harder (from Level 6 through one more grade of armour), takes more killing, follows further, comes more often and in bigger packs, and the quiet after a close call is shorter. Running stops being an answer: fire, light, doors, a stare and keeping still are.
- **And pays better.** A deep level's boxes, crates and cupboards are fuller, and often hold something extra: medicine and rusty gears, then copper, then bronze and iron, very rarely a temporal gear. What you kill there carries a bounty of rusty gears, the wanderers' coin; a Skin-Stealer drops the belongings of whoever it wore.
- **Dodge.** Every blow is wound up first: step back out of reach as it comes and it misses.
- Level 0 is empty, but when the lights fail in a Reality Shift, eyes watch even its heart from the dark. A door and a light at home keep them out.
- Nothing hostile enters the Manila Room, a Sanctum (Level 3), the Beverly Room (Level 5), the Snackrooms, the lamplit 9th Road and its camps (Level 8), or the Poolrooms (Level 37) outside the Reservoir. Level 94 is safe by day and indoors. Level 4's heart and Level 10's fields are calm. In the city (Level 11) nothing attacks unless you start it.
- Things do not open doors. A closed door behind you is a wall to them.
- Nothing hostile closes in on you while you keep company with a wanderer. Wanderers are few: one every kilometre or two, at camps in Level 1, outposts in Level 4, on the 9th Road and in the city. They are friendly and never fight back. Talk to one ({rightmouse}) and ask to trade, for rusty gears: they buy salvage and hides and sell Almond Water, Firesalt, candles, bandages and seeds. The faceless people wandering about are Facelings, not traders.

**Smilers** (dark places of most levels; Level 0's blackouts and Red Rooms; Level 2)
Eyes and a grin in the dark. They cannot be killed; struck, they withdraw.
- They never step into light: a torch, a lantern, a fire, a working lamp. A candle is not enough.
- Held in your gaze, while you neither run nor look away, a Smiler freezes, and in the end goes.
- They come for people alone in the dark. Carry a torch, and do not run.

**Hounds** (Level 1's dark sections, Levels 2 to 5, 8 and 9; harmless in the city)
Pale, hairless, on all fours, in packs of two or three. You hear them first.
- Out towards the edge of Level 1, the lights of a section sometimes fail all at once: a Flickering. Hounds hunt you until the lights come back, a minute or two later. Keep a fire, or a door, between you and the dark.
- They will not come within a few steps of a lit [firepit](search:firepit) or burning [Firesalt](block-backrooms:firesalt). A fire makes a camp safe.
- Light slows them. A spear, a club and armour see them off; hurt, they run. Their hides make leather.
- Stare one down: look straight at a Hound that is following you and it stops, lowers its head and growls, and backs off. It holds only a few seconds; then it comes at you. Use the seconds.
- Some are starved, thin and pale; now and then an old one, grey-haired and harder to put down.

**Facelings** (Levels 1, 3, 4, 5, 9, the city, the Snackrooms; their children in 5, 9, the city and the Snackrooms)
People with no faces, going about nothing; seldom met, except in the city. Their blank faces turn to follow you.
- Greet one ({rightmouse}): it waves, then points the way to the nearest way out of the level, as far as it knows.
- Harmless unless you hurt one, and then every Faceling near turns on you together.
- The children come to look at you and run if you rush them. When they hurry away, Hounds are near.

**Deathmoths** (Levels 1, 5, 9)
Moths the size of a hand span, drawn to open flame. They circle a torch; near the edges of a level the females bite whoever carries it.
- A candle draws few, a closed [lantern](search:lantern) none. Smoke from a fire scatters them. Any armour turns their bite.
- They settle on floors and tables to rest, the males by puddles and bodies to drink. Leave a settled female be: come at her, or hurt one, and she rears up and calls every female near onto you, flame or no flame.

**Skin-Stealers** (Levels 1, 2, 3, 5, 9)
Large, pale yellow and slow. They cough and call out from out of sight in a voice that is nearly human. Strong but slow: keep your distance, close a door, keep a fire.

**Dullers** (Levels 3, 4, 6, 8, the city's subway)
Tall and grey. They reach through walls at people passing close on the other side, then run. Plaster puffs out of the wall where the hand comes through.
- Scraping or dragging inside the walls means one is near: walk down the middle of corridors.
- Sometimes the hand takes something from your hotbar instead. It lies on the floor wherever the Duller went: in the room on the other side, if you can find it.
- [Almond Water](item-backrooms:almondwater) keeps them off for five minutes after a drink, and they will not reach for anyone near a fountain or seep of it.
- Faced, they flee.

**Death Rats** (Levels 1, 2, 8, 9, the city's alleys)
Rats, in packs, with short horns whose tips glow faintly red: two red points under a shelf in the dark. Hairless in Level 2's heat. They nip at your legs but keep clear of a carried torch and of fire. Food, if you can catch one.
- Rarely, near the edges of Levels 1 and 2, the Screaming: the lights fail, something screams close by, and a pack of them goes past at a run after whatever it is. Keep out of their way until the lights come back.

**Clumps** (Levels 2 and 3, the fields by Level 10's barns)
A bundle of limbs that buries itself where it waits: all you see is an arm sticking up out of the floor, a finger twitching now and then. Come within a few steps and the floor gives it up; it grabs and drags at whoever is in reach, then crawls away after a grab or two.
- It hunts by ear: run, or break things open, near one and it crawls after you. Go quietly and it buries itself again.
- Where there is room, walk round. In a narrow tunnel there is none: go back, or take the grab and be quick.

**The Thing** (deep in Level 7)
Something vast circles divers out at the edge of sight. Stay below the twilight zone too long with your stability failing and it strikes, once, hard. In the abyss it may come at anyone. It cannot be fought: surface.

**The Mangled** (the Suburbs, rarely; far likelier during a Reality Shift)
There is only one. It comes with its own weather: the air turns cold all at once, a grey fog rolls in, and voices start calling out of it, someone saying hello, someone hurt. Then a black pillar walks out of the fog: a mass of human faces held high above the roofs on legs like trees.
- It cannot be killed. Striking it only keeps it longer.
- Its tendrils take whoever they reach up into the dark and let go. Get indoors: it is far too big for any door.
- It leaves after three minutes or so, and the fog lifts.

**Animations** (Level 94, by night)
Puppets, clay and wooden figures and paper cut-outs that move a frame at a time, and hunt anything that does not look animated. Very strong, not clever. Clay ones smother, wooden ones club (a good hit can knock a head off), paper ones come in a crowd and fall apart in water. They never come indoors, and at dawn they are gone the moment nobody is looking. Stand quite still for a few seconds and they take you for a doll. Whoever carries a shard of the King's crown is one of their own.

**Robo-Men** (the castle in Level 94)
Tin wind-up toys that stand guard. Touch, use or break anything in the castle and you will hear a key turning: they come, for a minute and a half. They lose people in the blinding halls.

**The King** (the throne room of the castle in Level 94)
A stone statue at the head of a long table. Only one of the throne room's four doors opens, a different one each day. Sit in the second chair and he raises your nightmare in clay: the thing that has killed you most often. **It can only do what you think it can:** with your [Reality Stability](gamemechanicinfo-temporalstability) full it hits at a quarter of its strength; with it gone, twice as hard. Drink Almond Water before you sit down. Destroy it and the King bursts into light, gives you a shard of his crown (the first time), and carries you out of Level 94.

**Level 37** is empty, as far as anyone knows: nothing hostile goes there, but in the dark of the Sanguine Reservoir.

**Level 8's drifters** keep to the dark off the road. Stay in the lamplight.

**What keeps you safe, as you go deeper**
- Level 0: light, and a steady mind (Almond Water).
- Level 1: fire, doors, a spear or a club, improvised armour.
- Level 3: [Firesalt](block-backrooms:firesalt), found in the coal by generators and boilers. Set it down: for half a day nothing hostile comes near. From Level 8 you can make it: salt + powdered sulfur = 2 Firesalt.
- Level 4: a lantern, which draws no moths.
- Level 5 on: leather armour from Hound and Skin-Stealer hides; then copper and bronze from Level 8.
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
    items = {os.path.splitext(f)[0] for kind in ("itemtypes", "blocktypes") for root, _, files in os.walk(os.path.join(ASSETS, kind)) for f in files}
    bad = []
    for code, (_, text) in PAGES.items():
        for target in re.findall(r"\]\(((?:item|block)-backrooms:[^)]+)\)", text):
            name = target.split(":", 1)[1]
            # (A variant, like wanderernote-door, is named after its file plus its states)
            if name not in items and not any(name.startswith(item + "-") for item in items):
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
