"""The Backrooms' handbook (H) and quick start: the text of every page the mod rewrites or adds, the "In the
Backrooms" prefaces for the vanilla guides, and the steps of the Backrooms: First Steps tutorial.

In a Backrooms world these replace the vanilla Starter Guide, Progression Guide and Temporal Stability pages, add the
Backrooms' own pages, and preface every other vanilla guide (src/GuideSystem.cs); the tutorial is
src/Tutorial/BackroomsTutorial.cs. Other worlds keep the vanilla handbook and tutorial. The text lives here in a light
markup and is written into lang/en.json as the handbook's rich text:

    blank line           paragraph break
    **bold**  *italic*
    [text](page)         link to a handbook page: a guide's page code, or item-<code> / block-<code>
    [text](search:word)  link that searches the handbook
    {shift}              a key (a hotkey code: shift, rightmouse, leftmouse, handbook, worldmaphud, journal...)

Written in the voice of the vanilla guides (assets/game/lang/en.json, craftinginfo-* and gamemechanicinfo-*): a bold
title, an italic line under it, short sections with a bold heading, plain friendly prose, and links to the items and
blocks named. The vanilla pages are right about how things are made; these pages say where things are, and what is
different here.

Run on its own (python tools/gen_guide.py) or as part of gen_detail.py; python tools/gen_guide.py --check only looks
for broken links and writes nothing. Every number here comes from the block types,
recipes and code; check them when those change (tools/gen_notes.py --check also looks for the recipes the notes quote).
"""
import json
import os
import re
import sys

from detail_kit import ASSETS, LANG

PAGES = {}
BRIDGES = {}
TUTORIAL = []

# ====================================================================================================================
# Pages that replace vanilla ones (same page codes, so links keep working)
# ====================================================================================================================

PAGES["starter"] = ("Starter Guide", """
**Starter Survival Guide**
*The Backrooms: the art of not dying*

Note: This guide is purposely kept short. The other guides in the Guides tab are the game's own: their crafting is right, but where they say to find things is not, so each begins with a note on how it goes here. The Backrooms' own pages follow the [Progression Guide](craftinginfo-progressionguide) in the list. A step-by-step start is in the Tutorials tab, under *Backrooms: First Steps*.

**Where you are**
You have woken in Level 0, the Lobby: yellow wallpaper, damp carpet and humming lights, going on in every direction. Nothing grows here, it never rains, there are no seasons and no winter, and there is no one to be found. What you need was left behind by those who came before, in supply boxes, in the furniture, and in the building itself. A [wanderer's note](item-backrooms:wanderernote-door) is in your pocket: {rightmouse} with it in hand to read it. It will tell you the first three rules, and mark the nearest unopened supply box on your map (or, in a world made with less map, tell you which way it lies: see [Finding the Way](backrooms-finding)).

**What is different here**
- **You wake where you last slept.** Die anywhere and you wake in the last bed you slept in, or in the Lobby if you have never slept in one, and what you carried waits in your body where you fell, for as long as it takes. A [temporal gear](item-gear-temporal) moves where you wake, from any level. See [Home and Expeditions](backrooms-home).
- **The levels get harder by degree.** Each level has a class, shown on the M.E.G. placards beside the gates into a higher one. From Level 3 on, what lives there outruns a sprint, so what you wear decides how many blows you take. See [What Lives Here](backrooms-entities).
- **Nothing grows in Levels 0 to 5.** Trees, grass and animals exist only on the open-sky levels far out (9, 10, 11 and 94). Your first tools, fire and bags all come from salvage.
- **The levels nest like rings.** Walk far enough from where you woke and the Lobby gives way to Level 1, then 2, and so on. The walls between them break only below their roof line, and have a doorway through every few hundred blocks. See [Finding the Way](backrooms-finding).
- **Hunger and thirst both run down.** Hunger runs a quarter faster than usual, and water runs out faster in the heat. Sleep runs out too: lie down in a bed when the Rest bar runs low. See [Food and Water](backrooms-food) and [Rest and Sleep](backrooms-rest).
- **The gear by your health** is your [Reality Stability](gamemechanicinfo-temporalstability). Where it turns backwards, the place is draining you.

**First tools**
There are no stones lying about in the Lobby, but there is glass: break a dead (dark) [light fixture](block-backrooms:fluorescentlight-off) out of the ceiling with your bare hands for a [glass shard](item-backrooms:glassshard) or two. A lit one breaks too, but takes its light with it. A bare shard cuts wallpaper and carpet, but snaps about one time in four. Make a proper blade as soon as you have the parts: a [glass shiv](item-backrooms:glassshiv) is a shard, a wallpaper strip and a carpet fibre (a knife, 60 uses); an [improvised scraper](item-backrooms:scraper) is a metal bracket, a wallpaper strip and 2 carpet fibres (a knife, 180 uses). Brackets come from dead lights, ceiling tiles and supply boxes, now and then. The shiv and the scraper are the Lobby's own blades, made for its walls and floors: they peel wallpaper and carpet cleanly, two strips or fibres a cut, where any other knife, a flint one too, tears off one.

For real stone tools you need [flint](item-flint), and flint is a Level 1 find: a sealed supply box holds one only about one time in twenty, but Level 1's crates hold it and its broken concrete has flint and hard stones lying loose. With 2 flints, {shift} + {rightmouse} one onto the floor to begin [knapping](craftinginfo-knapping). A knife blade and an axe head first; each needs a [stick](item-stick) for a handle.

**Supply boxes**
Two [supply boxes](block-backrooms:supplybox) stand beside where you woke. Break them (hold {leftmouse}): a sealed box, its lid still taped down, holds a few of Almond Water, crackers, canned beans, carpet fibres, wallpaper strips, a glass shard, sticks and dry grass, and now and then a candle, a metal bracket, a wanderer's note, a seed packet, a rusty gear, a ready-made shiv or, rarely, a flint. A torn box, lid hanging open, was gone through long ago: scraps and paper, never food, and you can tell from across the room. Sealed boxes and crates show red on your map. Boxes were left in twos and threes at the inside corners of rooms, about one room in six, and over half of them were torn open before you came. Rooms papered in red and the hearts of dens hold boxes nobody dared to touch (see [What Lives Here](backrooms-entities)).

**Expanding inventory**
Your starting inventory has 10 slots, and you can carry up to 4 bags. There are no cattails here for a hand basket; the Lobby's bag is the [carpet bag](item-backrooms:carpetbag) (3 slots): 5 carpet fibres + 1 flax twine, and 3 carpet fibres make the twine. Hold a blade and {rightmouse} the dry carpet for a [carpet fibre](item-backrooms:carpetfibre) per block, two with a shiv or a scraper (the block is left bare). Four bags cost 32 carpet fibres, 16 cuts with a shiv: make them before you go anywhere. Later, a [linen sack](search:linen sack) (5 slots) is flax twine + linen from hotel beds and tents, and a [chest](search:chest) is 8 planks + 1 nails and strips, with planks from Level 1's crates.

**Finding food**
Food in the Lobby is what is in the sealed boxes, and nothing else. [Almond Water](item-backrooms:almondwater) quenches your thirst, heals 1 and steadies you, but gives no food (see [Reality Stability](gamemechanicinfo-temporalstability)); [crackers](item-backrooms:crackers) and [canned beans](item-backrooms:cannedbeans) fill you properly. You burn food and water walking, more running, and hardly at all standing still, so do not wander for the sake of it. The nearest plentiful food is Level 1's sealed crates: the first expedition out is for those. The dark, cold blackout zones of Level 0 keep food fresh (10 °C), so store it there. See [Food and Water](backrooms-food).

**Fire / Light**
A candle in your hand is enough light for the blackout zones; a [torch](block-torch-basic-extinct-up) (2 dry grass + 1 stick, lit at a firepit) is what keeps things away. Tinder is 2 [wallpaper strips](item-backrooms:wallpaperstrip) = 1 [dry grass](item-drygrass): hold a blade and {rightmouse} the yellow wallpaper. Sticks come from supply boxes (about one a box), from [rotten wood](item-backrooms:rottenwood) that falls out of broken ceiling tiles (1 rotten wood = 2 sticks, 2 rotten wood = 1 firewood), and now and then from a broken wall. The Lobby has almost no firewood: expect to light your first fire with rotten wood, or with planks from Level 1 (3 planks + an axe = 1 firewood). Then it is as usual: {shift} + {rightmouse} dry grass onto the floor, add 4 [firewood](item-firewood), and light it with a [fire starter](item-firestarter) (1 dry grass + 2 sticks).

**Combat**
The Lobby's heart is empty, but its Red Rooms are not; far out near its edge a tall figure of black wires watches from the mould and hunts whoever runs; and when the lights fail in a Reality Shift things watch even the heart from the dark. The rule is simple: **walk, carry a torch, and don't look away**. Running, breaking things and staying out a long time all draw attention. For Level 1 and beyond, craft a [spear](item-spear-generic-flint) or [wooden club](item-club-generic-wood) and some [improvised armor](item-armor-body-improvised-wood), and keep a fire between you and the dark. Everything that lives here, and what keeps each thing back, is in [What Lives Here](backrooms-entities).

**Shelter**
You already have one: the Lobby is where you will wake up, until you sleep in a bed somewhere else. Where you woke is your home until you move it. Close off a corner (drywall breaks with any tool, an axe quickest), put a torch up, and bring back a door and a chest from Level 1. The map marks "Where I woke up" so you can find it again. See [Home and Expeditions](backrooms-home).

**Finding the way**
The map ({worldmaphud}) shows only what you have seen, and remembers it. Level 0 ends somewhere between about 460 and 3,300 blocks from where you woke, depending on the direction; worn carpet and missing ceiling tiles mean Level 1 is near. Chalk arrows on the walls point to a doorway through; crosses mean a dead end, or a den. Every note you read is kept in your journal ({journal}). See [Finding the Way](backrooms-finding).

**Preparing for an expedition**
Instead of a winter, you prepare for trips. Before leaving the Lobby: four bags, a blade, a torch or a candle, all the Almond Water and food you can spare, and a note or two to read where you are going. Rest before you set out (a minute at home counts), because the longer you have been out, the bolder what lives here becomes. Reality Shifts come about once every 30 in-game hours (none in the first 30): when the lights go, stop, light up, and wait where you are.

For further progression, see the [Progression Guide](craftinginfo-progressionguide).
""")

PAGES["progression"] = ("Progression Guide", """
**Progression Guide**
*The way from a shard of glass to iron is the usual one. Only the places are strange, and they hold you back.*

**The ladder of classes**
Each level has a class, from 1 to 5, and the M.E.G.'s placards beside the gates say what lies past them. Levels 0, 1, 4 and 10 are Class 1, and Levels 5 and 11 Class 2. Level 2 is Class 3, and so is Level 94; Level 3 is Class 4, where the creatures first outrun a sprint. Levels 7 and 8 are Class 4 and Level 9 Class 5. Level 6 is not classed yet.

The materials climb the same way. The first copper is in Levels 1 and 2; copper, clay and coal in Level 3 and its tunnels; pottery shards in Levels 4 and 5; the tin is a dash off the 9th Road in Level 8, whose lamps keep your stability up. Level 94 has the fire clay that iron needs, and Level 7's sea the sand. The intended first expeditions are a raid into Level 3 for clay and coal (in, dig, and out before your stability runs out) and the tin dash off the 9th Road. A raid is not a stay: the classes are the reason for the trips.

**Scavenger Age**
Supply boxes, a glass shiv and a scraper, wallpaper strips and carpet fibres, four carpet bags, a torch: see the [Starter Survival Guide](craftinginfo-starterguide). Then the first expedition, to Level 1: bring back flint, planks and food, and [make a home](backrooms-home) of the Lobby.

**Stone Age**
[Knap](craftinginfo-knapping) a knife, an axe, a spear and a shovel from flint (Level 1's crates and floors), or from the chert, andesite and granite lying loose on Level 1's concrete. Keep the shiv or the scraper for the wallpaper and carpet: they cut twice what a flint knife does. Level 1's crates, pallets, plywood and workbenches are your first planks: split them for firewood, build a firepit and cook. Build a chest. Wood is the shortage of the early levels: there are no trees until the open-sky levels, and firewood comes from rotten wood (Level 0's ceiling voids), planks (furniture, from Level 1 on) and driftwood (Level 7).

**Pottery Age**
Clay is the first thing you have to travel for. The nearest is the flooded tunnel under Level 3: climb down a manhole; the water is freezing and the tunnel drains your stability about as badly as anywhere, so dig and get out before your stability runs out. Later sources: the beds of Level 10's ponds (iron tier), rare pockets in Level 8's rock (bronze), and best of all Level 94 (bronze), whose whole ground is modelling clay under a skin of turf. If you cannot face the tunnel yet, there is a slow way: the potted plants of Levels 4 and 5 break for soil and [pottery shards](item-backrooms:potshard) (about one a pot); 2 shards pounded with a stone make [ceramic grit](item-backrooms:ceramicgrit), and 2 grit + 1 soil make 1 blue clay, so some four plants to a clay. [Form](craftinginfo-clayforming) a crucible, tool moulds, a cooking pot, bowls, a watering can and storage vessels, and fire them in a pit kiln. Fire clay, for fire bricks, lies only in Level 94: see the Iron Age below. This is also the time to start [farming](gamemechanicinfo-farming) at home.

**Early Copper Age**
No mining needed: Levels 1 and 2 hold the first copper. Break these for copper bits (20 metal bits = 1 ingot in the crucible):
- cable spools (Levels 1, 3 and the city), about 4 each
- machine cabinets and machine parts (Level 2)
- stacked pipes (Level 3), which give lead as well
- industrial fans (Level 3), parking meters and phone booths (the city), wrecked cars (Level 1)
[Scrap wire](item-backrooms:scrapwire) melts to copper too: 10 scrap wire = 1 copper ingot; so do Level 3999's circuit boards. Copper needs a hotter fire than wood gives: use the coal heaped by Level 3's generators and in Level 5's boiler halls, charcoal from crates, or burn your own [charcoal](craftinginfo-charcoalburning). [Smelt](craftinginfo-smelting) in the crucible and cast a pickaxe and a hammer first. Toolboxes (Level 1, later garages and hardware stores) sometimes hold a copper hammer, chisel, saw or knife, and wanderers sell bronze knives and spears for rusty gears.

**Late Copper Age**
Save 9 ingots for an anvil (900 units), and cast it. With it come the saw, boards, barrels, shields and [leather](craftinginfo-leathermaking) from the hides of Hounds, Skin-Stealers, rats and the wildlife of Level 9. The copper pickaxe also opens the building: concrete, floors and pipes break for rubble, brackets and the odd copper bit. Under every floor, 8 blocks of concrete down, is the rock of the world, but its ore is only in Level 8 now (see the Bronze Age). See [Salvage](backrooms-salvage).

**Comfort**
Level 4 is the calmest place before the city: rest there. Its fridges hold fruit and cheese, and its fountains, coolers and vending machines give Almond Water. Level 5's beds come away as real beds (break the head end), its wardrobes and suitcases hold clothes, its bedding is linen for sacks, and its boiler halls have coal. Hotel dining tables, curio cabinets and service trolleys give silver bits; luggage carts, ashtray stands and chandeliers give brass. Level 3's Sanctums have candelabras, brass too.

**Bronze Age**
Level 8, Cave Systems, is where the ores are, and the way in is the 9th Road. Its lamps keep your stability up, and the tin is a short dash off the road (the dark drains you about ten minutes from full to zero, so take what you can and go back to the lamps). Its rock carries native copper, malachite, tin (cassiterite), zinc (sphalerite), bismuth, gold in quartz, lead (galena), sulfur, coal, and the iron ores limonite, hematite and magnetite, with loose ore and stones lying on the cave floors and no digging needed to get at them. There is no silver in Level 8: silver comes from the hotel, the city's parking meters, or deep galena in the ground. Bring light, warm clothes and food; Wretches hunt Level 8's dark caves in packs, Giant Spiders lie in wait in them, and the lamps of the 9th Road are the safe line through. Deep caches in the dangerous levels hold bronze and iron bits as well. Acquire one of the 3 types of bronze as the vanilla guides say, and work it as usual: [smithing](craftinginfo-smithing) is unchanged.

The ground under the floors is rock: the strata and caves the game's own generator lays down, with the Backrooms' floor at its sea level. **It carries no ore, outside Level 8.** The ore deposits are not laid there, so the [prospecting](gamemechanicinfo-prospecting) pick finds nothing to read under the other levels' floors, and the ores the other guides name are in Level 8's rock alone. With a copper pickaxe you can still dig through any floor (except Level 10's, where the worms are, and Level 94's, which is clay) for stone and what the strata hold.

**Iron Age**
Iron ore is plentiful in Level 8, but a [bloomery](search:bloomery) is built of fire bricks, and the ground under the levels holds no fire clay. **The only fire clay in the Backrooms is in Level 94:** dig down through the hills, and three to seven blocks under the turf, over much of the ground, run pale seams of it, five blocks thick. Bring a shovel and bags, dig by day, and carry it home: a bloomery base and chimney want a few dozen bricks. From there iron is made exactly as the other guides say, with Level 8's limonite, hematite and magnetite and its coal, and the bloomery also makes glass from Level 8's quartz. Until then, iron comes only as finds: the odd tool in a toolbox or a deep cache, and the wanderers' trade.

**Steel Age**
Steel is the same long road as anywhere: a cementation furnace of refractory bricks (some 65 of them, so a great deal of Level 94's fire clay), coke from a coke oven of the same bricks, and an iron anvil. Nothing about the process is different here; only the clay has to be fetched from a world of stop-motion hills, and carried past the Animations by night, and the sand for the bricks' mortar dived for on the floor of Level 7's sea.

**Salt, lime, leather**
Level 8's limestone and chalk grind to lime in a quern, and its halite to salt; the seashells on Level 7's islands grind to lime too. There is a quern in the barns of Level 10, or make one from Level 8's hard rock. Hides come from the wildlife of Level 9, the livestock of Level 10, and what hunts you.

**Wood**
Driftwood on Level 7's sea is firewood. Levels 9, 10, 11 and 94 have real oak, birch and maple to fell, with sticks lying under them; oak is what tanning wants. Level 7's jetties stand on oak logs.

**Farming**
You can farm in Level 0: see [Home and Expeditions](backrooms-home). Seed packets turn up on the tool shelves of Level 9's garages and sheds, and now and then in a supply box; seed sacks are in Level 9's sheds and Level 10's barns; wanderers sell flax and cabbage seeds. Level 10's fields stand ripe: spelt, rye, flax and vegetables. The old fields are exhausted, so replant in fresh soil: hoe a lawn in Level 9, 10 or 11, or Level 94's turf. It never rains, so [farm](gamemechanicinfo-farming) within 3 blocks of water, or carry a watering can. Level 10 also has livestock in its paddocks ([husbandry](gamemechanicinfo-animalhusbandry)), bee skeps by the farmhouses, berry bushes, and cattails at the ponds for hand baskets. Do not dig below the soil in Level 10.

**The city**
Level 11 is reached through a barn wall in Level 10 (or by the Hub's Tunnel 10 door). Stores full of food, tools and clothes, safe streets, and elevators and doors back to almost every level: see [Ways Between Levels](backrooms-thresholds). Beyond it lie the places no ring reaches: see [The Levels: Beyond the Rings](backrooms-farlevels).
""")

PAGES["stability"] = ("Game Mechanic: Reality Stability", """
**Reality Stability**
*Some places hold you. Most do not.*

The cyan gear between your health and hunger bar is your reality stability meter: how firmly this place has hold of you. Where the place is steadier than you, the gear turns clockwise and you recover; where it is not, it turns counter-clockwise and you drain. As your stability falls the world distorts, and at zero you take constant damage until you recover. Things that live here come bolder the lower your stability is. There are no temporal storms and no rifts in the Backrooms: the geography does the work instead, and each place has its own steadiness.

**Places that restore you**
- Level 0: the Manila Room, strongly. The ordinary Lobby is neutral, drifting a little either way.
- Level 1: the car park, barely (the maintenance corridors drain).
- Level 4: all of it.
- Level 5: the Beverly Room.
- Level 6.1, the Snackrooms, strongly.
- Level 8: on the 9th Road.
- Level 10, and Level 11's streets (not its subway).
- Level 37 in the light, and more still standing in lit water. Level 94's hills, a little.
- Level !: the Safe Zone. The End: under THE END IS NEAR, in the central hall. The Hub, everywhere but the Far Tunnels, which neither give nor take.
- Level 974, Kitty's House, for the first 18 hours of a visit.
- Level 3999, the Neon Paradise, wherever the neon is lit (the lobbies most).
- Level 188: inside a guest room with the door shut, a little.

**Places that drain you**
A minute at zero ends in a blackout, from any cause (a dark pocket, a Reality Shift, hunger, thirst or no sleep), and you wake a level back with what you carried.
- Level 0: the blackout zones, and worst of all the Red Rooms (red wallpaper, red lamps): take what is there and leave.
- Level 1: the maintenance corridors, a little.
- Level 2: everywhere. Level 3: everywhere, and its flooded tunnels nearly as badly as a Red Room.
- Level 5: the corridors, and above all the boiler halls. Level 6: everywhere in the dark.
- Level 7: the surface is neutral; below it, the deeper you dive the worse, until past 50 blocks down nothing drains you faster.
- Level 8 off the road. Level 9 everywhere. Level 11's subway, a little.
- Level 37's dark corners, and the Sanguine Reservoir badly. Level 94's castle.
- Level !: everywhere but the Safe Zone.
- Level Fun: everywhere, the party rooms and service corridors most. Party Fever lowers how steady you can be.
- The End: more the further from its middle; after two hours there, more again; worst in the collapses and the fake realities.
- Level 974: after 18 hours, more and more the longer you stay.
- Level 3999: where the neon flickers and fails, and fast in the dark of Level 3999.1 beyond it.
- Level 188: the corridors a little, the courtyard and the roof more, and most near a window with someone waving in it.

**Ways to recover**
- Enter a steadier place, which is indicated by your gear turning clockwise.
- Drink [Almond Water](item-backrooms:almondwater): each bottle restores 15%. [Cashew Water](item-backrooms:cashewwater) restores 8%, [Almond Milk](item-backrooms:almondmilk) 10%, [Memory Juice](item-backrooms:end-memoryjuice) 20%.
- Stand in the lit water of Level 37: it steadies and heals you, and counts as rest.
- Sleep in Kitty's bed after the computer's dream: a large restore, once a visit.
- Putting a [temporal gear](item-gear-temporal) in your left hand, a knife in your main hand and holding {rightmouse} will transfer stability from the gear to you, but consumes the gear and some of your health. Gears are very rare here.

**Reality Shifts**
About once every 30 in-game hours (an hour of play) the lights fail everywhere for 2 to 4 in-game hours. Everything beyond a few steps is lost in black, every place drains you while it lasts (even the safe ones), and what lives in the dark comes out, even into the heart of the Lobby. None comes in your first 30 hours. When the lights go: stop, light a torch or a candle, drink Almond Water if the gear runs low, and wait it out somewhere with a door. It ramps up and down over a few minutes, so you have a moment's warning.

**Going without**
Go without sleep long enough, or let your water run dry, and the place drains you wherever you stand, more the longer it goes on. [Rest and Sleep](backrooms-rest) and [Food and Water](backrooms-food) say what each costs.

**Things that lower your ceiling**
Party Fever (Level Fun's bite) caps your stability while it lasts; [Red Water](item-backrooms:redwater) from the Sanguine Reservoir heals every wound but lowers for good how steady you can ever be, a little each drink.
""")

# ====================================================================================================================
# Pages of our own
# ====================================================================================================================

PAGES["home"] = ("Game Mechanic: Home and Expeditions", """
**Home and Expeditions**
*You wake where you last slept. Make it somewhere worth waking up in.*

The Backrooms are survived from a home, in expeditions. Everything that follows is built on one fact: however deep you go, when you die you wake with nothing, in the last bed you slept in (or in the Lobby, if you have never slept in one), and what you carried lies in your body where you fell, wherever that was.

**Your body**
Where you fell, your body lies, in your own skin and clothes, with everything you carried inside it. It does not go away, and nothing eats it: it waits as long as it takes, and after a few in-game days it is only bones, still holding all of it. The map marks each body of yours with a skull and pins the newest one, so it shows at the edge of the minimap when it is far away. {rightmouse} it to search it like a chest, or {shift} and {rightmouse} to take everything that fits. When it is empty it crumbles, and its mark goes with it. What you were wearing stays on you.

**Where you wake**
Sleep in a bed and that bed becomes the place you wake next time, wherever it stands, so a bed near the way you mean to go is worth a night. Until you have slept in one, you wake where you first woke, in Level 0, which the map marks as "Where I woke up". A [temporal gear](item-gear-temporal) held and right-clicked on the floor sets your waking place there instead, in any level, and is used up. Gears are rare: early caches in Levels 1 to 5 give one in about 2 to 4 breaks in a hundred, more often than the deep caches (under 1 in a hundred); the Level ! prize gives two, the prize counter of Level 3999 sells one for 200 tickets, and the wanderers at five of their sites (the crate-pickers, the Level 4 outpost, the 9th Road, the city and the Hub's doorstep) sell one for 6 rusty gears (about eight bounties from mid-level Hounds). Good places to call home: the Manila Room (nothing hostile goes in, and it steadies you), beside a way out you know, and beside a flooded room, for water.

**Resting**
The longer you are out without a rest, the bolder what lives here becomes (see [What Lives Here](backrooms-entities)); after ten in-game hours out, about twenty minutes of play, it is as bad as it gets. A rest is a full minute, without moving on, in any of these: within about 48 blocks of home; beside a lit [firepit](block-firepit-lit) or burning Firesalt (within 6 blocks); asleep in a bed; beside a wanderer; or in one of the safe places. A firepit and a chest halfway along a route you use make an outpost, and make it safe to stop. (Sitting by a fire is not sleep: see [Rest and Sleep](backrooms-rest).)

**What a home needs, and where it comes from**
- **Walls where you want them.** Drywall and wallpaper break with any tool (an axe is quickest; bare hands take seven times as long) to join rooms or close off a corner. Concrete and floors take a copper pickaxe. To build, [rubble masonry](block-backrooms:rubblemasonry) is 4 [rubble](item-backrooms:rubble) in a 2 by 2, and rubble comes from breaking concrete and floor slabs with a copper pickaxe (about one rubble from two blocks), never from drywall. Beyond that, the usual vanilla blocks: cobblestone from Level 8's rock, bricks from clay. Only the roof of a level, and the top of the walls between levels, never give.
- **A door.** Nothing in the Backrooms opens doors, so a door is a wall to them. Planks come from Level 1's crates and pallets and Level 4's furniture.
- **Storage.** A [chest](search:chest) (8 planks + 1 nails and strips, the nails from 2 metal brackets). Baskets need Level 10's cattails. Before that, most tools and many items can be [stored on the ground](gamemechanicinfo-groundstorage).
- **Light and fire.** Torches on the walls, a firepit, [Firesalt](block-backrooms:firesalt) from Level 3 for when the lights fail. When a Reality Shift puts the lights out, eyes come to the edge of the dark even here; a door and a light keep them out.
- **Cold storage.** Level 0's blackout zones are cold and damp (10 °C): food in a chest there keeps more than twice as long as in the Lobby proper. See [Food and Water](backrooms-food) and the vanilla [food preservation](gamemechanicinfo-foodpreservation) page.
- **A farm.** Soil comes from potted plants (Levels 4 and 5), the lawns of Levels 9, 10 and 11, or Level 94's turf; seeds from seed packets, Level 10's barns and wanderers; and water from a flooded room, a bucket, or a watering can, within 3 blocks of the farmland. Crops grow under a working ceiling light at a little over half the daylight pace, and hardly at all in the cold of the blackouts; plant under a lit troffer, not a dead one. See [farming](gamemechanicinfo-farming).
- **A bed.** The head end of a hotel bed (Level 5) comes away as a real bed you can sleep in; a hay bed is 3 hay from Level 10. A bed at home is where you rest properly: nothing visits a sleeper in Level 0. See [Rest and Sleep](backrooms-rest).

**Food that comes back**
Nothing in Levels 0 to 5 restocks except the Snackrooms' food machines and, in a world with Thirst off, the drink dispensers listed in [Food and Water](backrooms-food); with Thirst on, drink dispensers are one-time stock. What does come back: fish (Level 7), game and berries (Level 9), crops, livestock and honey (Level 10), the iceboxes and milk vans of Level 94, and a farm of your own. Preserve with salt (Level 8's halite, ground in a quern) or a sealed crock.

**Planning an expedition**
- Rest first. Take four bags, a blade, a torch and a candle, Almond Water, food for the way back, a bandage, chalk if you have it, and any note you have not read yet (a note read in a new level tells of that level).
- Know the way back before you need it: every doorway between levels and every elevator, stairwell, door or pit you take is marked on your map the first time, with the way back where there is one ([Ways Between Levels](backrooms-thresholds)).
- The hot levels (2, 3, the boiler halls) burn food faster; the cold ones (6, 7's sea, 8, the Hub) want warm clothes.
- Leave an outpost on any route you mean to use twice.
""")

PAGES["finding"] = ("Game Mechanic: Finding the Way", """
**Finding the Way**
*Reaching the wall is not reaching the next level.*

**The map**
Open it with {worldmaphud}. It shows only what you have actually seen: it fills in along your line of sight out to about 24 blocks, 4 in the dark (2 in Level 6), and remembers between sessions, so what you have mapped stays mapped. Walls block it. It marks "Where I woke up"; every doorway between levels you walk through and every elevator, stairwell, door or pit you take (with the way back where there is one); the places wanderers' notes tell of; chalk marks, in white; and sealed supply boxes and crates, in red. {rightmouse} the map to add waypoints of your own.
How much the map helps is chosen when a world is created (*Backrooms map*, under Survival challenges). With *No waypoints* it fills in just the same but marks nothing for you. With *None* there is no map or minimap at all: you find your way or you don't. Without waypoints, what would have been marked is told to you instead, as a direction and a number of paces, and your journal keeps what the notes said; [chalk](item-backrooms:chalk) is how you find your way back, and with no map there is a little more of it in ceiling tiles and lost backpacks.

**Gates**
Where two levels meet the wall is solid, but every few hundred blocks along it there is a gate: two or three doorways side by side, each two blocks wide (in Level 1, under an EXIT sign). The first time you walk through one it is marked on your map. In Levels 0, 2 and 6 a hallway runs along the inside of the boundary wall: follow it and you will come to a gate, quietly, because the edge of a level is the most dangerous ground in it. The wall itself is not sacred below its roof line: a Level 0 boundary is papered drywall and breaks with any tool, a concrete one with a copper pickaxe, so with the right tool a wall is a slow way through rather than a dead end. Level 8 is solid rock, entered and left only where the 9th Road runs through it, and the open-sky levels (9, 10) have no wall between them at all.

**Signs of a gate**
- **The doorway itself.** Each level looks like itself right up to its wall; only the short passage through a gate shows the next level, with its doorway at the far end: Level 0's carpet worn to the concrete in the doorway to Level 1, the hotel's red carpet in Level 4's doorway to Level 5. (In worlds made before 0.514.0 the next level showed itself sooner: worn carpet and missing ceiling tiles near Level 1, pipes along Level 1's ceiling near Level 2, hotel red in Level 4's carpet near Level 5.)
- **Chalk arrows** on the walls, left by those who came before, point the way to the nearest gate from about a hundred blocks out (Levels 0 to 6). Chalk shows white on the map, so an arrow you have seen is a lead.
- **Chalk crosses** mean a dead end (most of the Lobby's blind hallways carry one), or, in a ring of them round a place with bones on the floor, a den: keep out.
- **Facelings** (the faceless people of Levels 1, 4, 5, 9 and the city; Level 3's are the hostile Evolved, and do not wave): greet one with {rightmouse} and it waves, then turns and points toward the nearest gate it knows of within a few hundred blocks, and you are told which way it pointed and roughly how far.
- **Wanderers' notes** ({rightmouse} to read) mark a place on your map, by the paper: a note *of a door* marks the nearest gate (where there are no gates, the nearest way out); *of a way*, the nearest elevator, stairwell or pit; *of something left*, the nearest sealed box or crate; *of a refuge*, the nearest safe place or trader. The text tells you the direction and about how many paces. A note with nothing of its kind in range is handed back, to read somewhere else.

**Notes and the journal**
- What a note says is what the wanderers before you learned, and it comes **in order**. Whatever note you find first, it is the same first page anyone reads, and the next carries on from it. After the first three (the rules of the Lobby), notes take turns between the wanderers' way through the levels and what is known of the level you read them in. Some pages wait until you have been somewhere.
- **[Folded notes](item-backrooms:wanderernote-folded)**, taped small and written in ink, are rarer (deep caches, the hearts of dens, Red Rooms, rooms behind locked doors, lost backpacks, bedrolls, tents, makeshift beds, lean-tos, the far edges of a level) and say something more exact: a route, the odds of a door, a rule that keeps you alive. What they mark, they find from twice as far, and show in gold.
- **Every note marks somewhere new.** A note never points at a place one of your earlier notes already marked while there is another to point at: the first supplies note marks the nearest unopened box, the next one the box after that, and so on outward; the same for gates, ways and refuges. Only when nothing else is in range does a note name a place again.
- **A note is kept when read**, and remembers who has read it: to you it is now "(read)", and reading it again only says so, but anyone else can read it for the next page in *their* sequence. One paper gives each player one read, so pass your notes on, or leave them where the next wanderer will find them.
- **Notes stack** by what they are about, 16 to a stack (a way through, a way out, supplies, a refuge; the folded notes together), so you can carry a bundle and read them where they will help, one at a time. Read notes stack apart from fresh ones.
- Some notes lie loose on the floor: at chalk-crossed dead ends, in the Manila Room and the Red Rooms, in Level 3's Sanctums and the Beverly Room, in the food courts, beside each arrival in Level !.
- Every note you read goes into your **journal** ({journal}, or .journal): the wanderers' way, a chapter for each level, the folded notes, and the directions you have been given, each with where you read it and, where the world has waypoints, **Show on map** and **Mark again** for what it marked. It is kept for you, not carried: dying loses nothing.
- You wake with a note already in your pocket: the first page, marking the nearest sealed box.
- Once you have read everything, a note is only its directions. Anything signed =) is a lie.

**Ways through**
Elevators, stairwells, doors, pits, vents and stranger things are the other ways between levels, often far shorter than walking. Two rules hold for all of them: a threshold always leads to the same place, and if you walked through it you can walk back (by the twin you come out beside, or by a thin spot left where you arrived), while if you fell, dived or were taken you cannot. Each is marked on your map the first time. The full list is [Ways Between Levels](backrooms-thresholds).

**Locked doors**
Levels 1, 2, 4, 5 and 9 have rooms behind locked doors that nobody has been into since. A [pry bar](item-backrooms:prybar) (2 metal brackets + 1 iron nails and strips; also found on tool shelves, in toolboxes and on workbenches; 24 uses) forces one in 4 seconds, for good, if there is a room behind it, and leaves you the door's bracket; everything near hears it. A door set in solid wall will not give, and a door that goes somewhere is not locked at all. The Lobby has no doors to force. Level 188's rooms open with its own keycards.

**Expeditions**
The longer you are out without resting, the more the Backrooms notice you (see [Home and Expeditions](backrooms-home) for what counts as rest). Rest by a fire, beside a wanderer or in a safe place, then go on. Mark your way with [chalk](item-backrooms:chalk) in the dark levels: choose arrow, cross or circle with the tool mode key ({toolmodeselect}), and {rightmouse} a wall; a mark can be changed by clicking it again (48 marks a stick). Chalk is made from a chalk stone, and falls out of ceiling tiles and lost backpacks now and then.
""")

PAGES["salvage"] = ("Crafting Mechanic: Salvage", """
**Salvage**
*What to break, and what to make of it.*

The Backrooms are a scavenger's world: nothing is mined or grown in the first six levels, and almost everything you make starts as something somebody left. There are three kinds of salvage: loose things that come away whole, walls and floors that can be cut, and the building itself, which breaks down into scraps.

**Loose things**
Supply boxes, crates, furniture, machines, ceiling tiles and light fixtures break like any block (hold {leftmouse}) and drop what is in them. Boxes and crates hold food; furniture holds planks, cloth, paper and metal; machines hold wire and copper. A sealed box or crate (lid on) is untouched; a torn or opened one was picked over long ago and never holds food. The list of what gives what is below.

**Cutting (hold a blade, {rightmouse})**
With any knife in hand (a [glass shiv](item-backrooms:glassshiv), an [improvised scraper](item-backrooms:scraper) or a flint knife), {rightmouse} a block to cut it, and it is left bare. The shiv, the scraper and any knife of copper or better (a blade that holds an edge) cut cleanly and give two of the item; a flint or bone knife tears off one. A bare [glass shard](item-backrooms:glassshard) works too (one item), but snaps one time in four.
- Level 0's wallpaper (yellow, pale, dotted, manila or red): a [wallpaper strip](item-backrooms:wallpaperstrip).
- Level 0's dry carpet (normal or stained; not the soaked carpet of the blackouts, nor threadbare carpet): [carpet fibres](item-backrooms:carpetfibre).
- The End's carpet: carpet fibres.
Other levels' walls and floors cannot be cut; they break instead.

**Breaking the building**
Walls, floors and fixtures break with the tool their material calls for, but they break *down*: bash out a wall and you get dust and scraps, never the wall back. Breaking anything is loud.
- **Drywall, plaster, wallpaper** (Levels 0, 4 and 5, the houses): any tool, an axe best; bare hands at a seventh of the pace. Mostly dust; now and then a stick or a wallpaper strip.
- **Boards, panelling, floorboards, roofs:** the same. Sticks, a little firewood, rarely a plank.
- **Concrete, brick, tile, marble, every floor slab:** a copper pickaxe, as for rock. [Rubble](item-backrooms:rubble), about one from two blocks; carpeted floors a few carpet fibres as well. Under every floor lie 8 blocks of concrete, then the rock of the world: strata and caves, but no ore outside Level 8.
- **Pipes, railings, poles, machinery:** a copper pickaxe. Metal brackets; wired things a little scrap wire; pipes now and then a copper or lead bit. A bronze pickaxe cuts pipes, cable and machinery into cleaner, longer pieces and gets a quarter more out of them than a copper one; an iron pickaxe, half more.
- **Glass:** anything. Glass shards.
- **Light fixtures:** a dead one worked loose with a knife, scraper or chisel in hand, instead of smashed, gives half as many shards again (and brackets and wire).
- **Rock and ore** (Level 8's rock): a pickaxe, as anywhere, and it gives stones and ore as anywhere. The rock under the other levels' floors gives stones and no ore: the ore deposits are Level 8's alone.
- **Wrecks:** an abandoned car comes apart with a copper pickaxe, all of it at once: brackets, wire, glass, a little copper.
- **Lights,** lit or dead: anything. One or two glass shards, sometimes a bracket or wire; a lit one's light goes with it.
- **Never:** each level's roof (the solid top of it with nothing open above; in Level 0, the slab over the crawlspace, while the ceiling tiles and the crawlspace come down); the wall between two levels from that height up (below it, the wall breaks like any other); doors, elevators, vents, vending machines, fountains and anything else that leads elsewhere or gives something; Level 188's building; Level 3999's working machines, counters, doors and windows. The block info says so when you look at one.

**Building with the Backrooms**
Walls break down, but a room can be built again from what they leave. All of it but the asphalt is made in the crafting grid, with plaster ([quicklime](item-quicklime) over sand), [mortar](item-mortar) (slaked lime and sand, from the barrel), sticks, planks, cloth and parchment from the usual recipes.
- **Drywall:** 2 plaster in the top row and 2 sticks in the bottom (2 by 2) = 4 bare drywall; plaster in the left column and sticks in the right = 4 Level 4 drywall.
- **Wallpaper:** bare drywall + 2 [wallpaper strips](item-backrooms:wallpaperstrip) = yellow wallpaper; + 1 parchment = manila; + 1 plaster = 2 cream stucco. Drywall + 2 strips + 1 charcoal = dotted yellow wallpaper (the pattern printed on), and + 1 quicklime = pale wallpaper (whitewashed). Any of those + a stick = the same with its baseboard.
- **Carpet:** 4 [carpet fibres](item-backrooms:carpetfibre) + 2 flax twine = 2 Level 0 carpet. Fibres and cloth make Level 4's office carpet and the hotel's maroon and damask; the maroon carpet + 2 fibres = the lobby's carpet.
- **Ceilings:** a strip, plaster and a strip in a row = 4 ceiling tiles; the same standing = 4 Level 4 tiles.
- **Hotel:** 4 planks + 2 sticks = 4 panels; a panel + a stick = wainscot, + a plank = frieze. 5 planks + nails (the nails in the bottom row) = 4 walnut floor; with the nails in the top row, 4 floorboards.
- **Concrete:** 3 [rubble](item-backrooms:rubble) + 1 mortar = 2 [concrete](block-backrooms:built-concrete). 2 concrete side by side = 2 floor slabs, one above the other = 2 ceiling slabs, 1 on its own = a concrete wall; concrete + rubble = 2 pavement.
- **Brick, tile, cinder block:** Level 3's walls are 2 of the game's bricks, tiles or rubble and 2 mortar, set crosswise, for 2 blocks; bathroom tiles are 3 clay tiles + mortar for 4.
- **Houses and farms:** 3 planks + 1 quicklime (in the 2 by 2, the lime bottom right) = 4 white house siding, 4 siding + 1 blue clay = 4 blue; 2 bricks over 2 mortar = 2 brick siding. 3 fired shingles + mortar = 4 flat roof; 2 shingles over 2 sticks = 2 lower slope, and the sticks over the shingles = 2 upper slope (grey, brown or red shingles for the same colour). 3 planks + 1 stick = 4 weathered barn boards; 4 boards + 1 red clay = 4 red; 3 planks over 3 sticks = 4 porch deck, and a deck + a plank = 2 steps.
- **Tile and the city:** 3 clay tiles + 1 quicklime = 4 pool tiles, and 2 pool tiles side by side = 2 coping; 2 tiles over 2 mortar = 2 subway tiles. Concrete + plaster = 2 city concrete wall; concrete + 3 glass shards = 2 curtain wall; a Level 3 brick wall + plaster = 2 brick; concrete + quicklime = 2 limestone; 2 plaster + rubble = 2 plaster wall. Lit windows, signs and everything powered are left out.
- **Asphalt:** take tar from a pool in Level 7's sea or Level 8's rock with a bucket (right-click the pool; it scalds anyone standing in it), then put 1 litre of it and 4 [rubble](item-backrooms:rubble) in a barrel: 4 asphalt.
- **Whole furniture:** break an office or hotel desk, table, chair, sofa, wardrobe, bookshelf, dresser or cubicle partition with a saw in hand and it comes away whole, to set down again facing you. Metal pieces (a filing cabinet, a cafeteria, folding or stacked chair, a folding table, a luggage cart or a service trolley) come away whole under a hammer, unbolted. Any other tool breaks it for lumber and cloth as before.
- **Only salvaged, never made:** light fixtures, machines, pipes, wiring, doors, vending machines, anything that holds a level up or leads elsewhere. They give up their glass, brackets and wire, never themselves.
What you make comes back whole: break a block you crafted (an axe or bare hands for drywall, wallpaper, carpet and tiles; a pickaxe for concrete and masonry) and you get that block, to use again. Only the Backrooms' own walls break down, and a block taken from the world is still salvage. Furniture is different: even set down again, it comes away whole only under a saw.

**Backrooms recipes**
- [Glass shiv](item-backrooms:glassshiv) (knife, 60 uses, cuts two a block) = glass shard + wallpaper strip + carpet fibre
- [Glass spear](item-backrooms:glassspear) (spear, 12 uses, thrown or in the hand) = glass shard + carpet fibre + stick, one above the other
- [Improvised scraper](item-backrooms:scraper) (knife, 180 uses, cuts two a block) = metal bracket + wallpaper strip + 2 carpet fibres
- 1 dry grass = 2 wallpaper strips
- 1 flax twine = 3 carpet fibres
- [Carpet bag](item-backrooms:carpetbag) (3 slots) = 5 carpet fibres + 1 flax twine
- 2 sticks = 1 rotten wood, or 1 plank + a knife
- 1 firewood = 2 rotten wood, or 3 planks + an axe
- 1 iron nails and strips = 2 metal brackets
- [Pry bar](item-backrooms:prybar) (24 uses) = 2 metal brackets + 1 iron nails and strips
- 4 seeds = 1 [seed packet](item-backrooms:seedpacket-turnip), opened in the grid
- [Surveyor's chalk](item-backrooms:chalk) (48 marks) = 1 chalk stone
- 3 salt poultices (as good as the best there is) = 2 [Epsom salt](item-backrooms:epsomsalt) above 1 linen
- 2 [Firesalt](block-backrooms:firesalt) = salt + powdered sulfur
- Crucible: 20 metal bits = 1 ingot. 10 scrap wire = 1 copper ingot. 10 [circuit boards](item-backrooms:l3999-circuitboard) = 1 copper ingot. 5 [coin mechanisms](item-backrooms:l3999-coinmech) = 1 brass ingot.
- 2 [neon lamps](block-backrooms:l3999-neonlamp-magenta-north) (the glow bracelet's colour) = 2 neon tubing + 1 glow bracelet + 2 plastic scrap + 1 circuit board
- 2 [glow bracelets](item-backrooms:l3999-glowband-lilac) (lilac) = 1 plastic scrap + 1 neon tubing
- [Rubble masonry](block-backrooms:rubblemasonry) = 4 [rubble](item-backrooms:rubble) (2 by 2): a rough block to build with
- [Ceramic grit](item-backrooms:ceramicgrit) = 2 [pottery shards](item-backrooms:potshard) + any stone (the stone is kept)
- 1 blue clay = 2 ceramic grit + 1 soil: about four potted plants' worth, so a slow clay for those not yet ready for Level 3's tunnel
Knives and axes are not used up by these, only worn.

**Vanilla recipes you will want early**
- Fire starter = 1 dry grass + 2 sticks
- Torch = 2 dry grass + 1 stick, lit at a firepit
- Firepit = dry grass placed on the floor + 4 firewood
- Linen sack (5 slots) = flax twine + linen
- Chest = 8 planks + 1 nails and strips
- Hay bed = 3 hay
- Knife, axe, spear, shovel, hoe = a [knapped](craftinginfo-knapping) head + 1 stick

**What gives what when broken**
- **Glass shards:** dead and lit light fixtures (1 or 2); desks, photocopiers, televisions, curio cabinets, phone booths.
- **Metal brackets:** light fixtures, metal shelving, office chairs, filing cabinets, stacked chairs, folding furniture, hospital beds, shopping carts, crates, a door you pry open.
- **Scrap wire:** machine cabinets, machine parts, photocopiers, desks, televisions, industrial fans, washing machines, toolboxes, crates. Rarely above ceiling tiles.
- **Copper bits:** cable spools (about 4), machine cabinets, stacked pipes (with lead), industrial fans, parking meters, phone booths, wrecked cars.
- **Silver bits:** curio cabinets, room service trolleys, hotel dining tables, parking meters. **Brass bits:** luggage carts, ashtray stands, chandeliers, candelabras.
- **Planks:** desks (2), bookshelves (3), workbenches (3), pallets (3), wardrobes (3), pews (3), conference and dining tables and reception desks (4), plywood (2), crates, most hotel furniture.
- **Nails and strips:** barrels of nails (2), workbenches, pallets, toolboxes, opened crates; sealed Level 1 crates hold copper nails.
- **Rotten wood:** trash cans, wastebaskets, wheelie bins, dumpsters, televisions. Rarely above ceiling tiles.
- **Sticks and dry grass:** supply boxes, supply crates. Sticks also from potted plants, coat stands, broken drywall and under the trees of the open-sky levels; dry grass from cardboard boxes, bedrolls, sleeping bags, makeshift beds and (with a knife) the tall grass of those levels.
- **Pleather:** the seats of Level 1's wrecked cars, Level 4's office chairs and Level 5's hotel chairs and sofas, one or two a piece. It is thin and fragile, and it is armour of its own (see [What lives here](backrooms-entities)), but it is never leather: no recipe takes it for leather, so tanned rat hides and Level 9's hides are still the road to leather.
- **Cloth:** sofas, wing chairs, office chairs, partitions, bedrolls, sleeping bags, tents, makeshift beds, lean-tos, suitcases, laundry carts. **Linen:** hotel beds (the foot end), tents, hotel dining tables.
- **Clothes:** wardrobes, suitcases, dressers, clothes racks.
- **Paper:** desks, filing cabinets, photocopiers, bookshelves, mailboxes, newspaper boxes.
- **Candles:** supply boxes, crates, nightstands, candelabras (2).
- **Rope and twine:** crates, toolboxes, tents, lean-tos, tool shelves, lost backpacks.
- **Bandages:** medical cabinets, hospital beds, lost backpacks.
- **Coal:** coal piles (about 6), by Level 3's generators and in Level 5's boiler halls; they also hold Firesalt. **Charcoal:** crates, barbecue grills.
- **Seeds:** seed sacks (Level 9's sheds, Level 10's barns); seed packets (tool shelves, kitchen cupboards, now and then a supply box). **Soil:** potted plants, which also give pottery shards.
- **Pry bars:** tool shelves, toolboxes, workbenches; or make one.
- **Wanderers' notes:** supply boxes, torn boxes, desks, filing cabinets, writing desks, tents, bedrolls, makeshift beds, lean-tos, and above all lost backpacks. Folded notes from the places named in [Finding the Way](backrooms-finding).
- **A real bed:** a hotel bed's head end.
- **Tools, now and then:** toolboxes (copper hammer, chisel, saw, knife); tool shelves (hammer, saw, shovel); tool racks (hoe, scythe, shovel); kitchen cupboards and lost backpacks (knife); waterlogged crates (raft, fishing pole).
- **Chalk:** rarely above ceiling tiles; lost backpacks.
- **Rusty gears:** reception desks, mahjong tables, curio cabinets, toy boxes, trash cans, grandfather clocks; supply boxes now and then. They are the wanderers' coin, and what you kill carries a bounty of them.
- **Temporal gears:** early caches in Levels 1 to 5 give one in about 2 to 4 breaks in a hundred, deep caches under 1; the Level ! prize gives two; Level 3999's prize counter for 200 tickets; wanderers at five sites (not Camp Amber, The End or Level 3999) for 6 rusty gears.
- **[Plush toys](item-backrooms:l974-plush-cat):** toy boxes (Level 9, about one in three); now and then a suitcase (Level 5) or a lost backpack. A plush is *cute* (see [Kitty's House](backrooms-farlevels)), and so are flowers and seashells.
- **Furniture for a home (The End):** chairs, tables, ladders and shelves come away whole; reading-room shelves, desks and card catalogues sometimes hold a book (a few are written in). Card catalogues give [catalogue cards](item-backrooms:end-cataloguecard): read one ({rightmouse}) and the nearest way out of The End is marked on your map.
- **Party hats and red balloons:** Partygoers (Level Fun) drop hats; the ones holding a red balloon drop it. Together they are a disguise (see [What Lives Here](backrooms-entities)).
- **Level 3999:** the machines that work cannot be broken, but dead cabinets give scrap wire, glass, brackets, a [circuit board](item-backrooms:l3999-circuitboard), [coin mechanisms](item-backrooms:l3999-coinmech), [plastic scrap](item-backrooms:l3999-plastic) and a ticket or two; air hockey tables plastic, brackets, wire and coin mechanisms; bins plastic, paper and tickets; dead neon [neon tubing](item-backrooms:l3999-neontubing) and glass. Plastic scrap burns as fuel. Lost-and-found bins hold clothes, cloth, now and then a backpack. In 3999.1 the prize cases (bandages, Firesalt, seeds, rusty gears, neon lamps, tubing, Almond Water, now and then a pry bar, a backpack or a plush) and ticket piles (3 to 6 tickets) are free for the taking.
- **Level 188:** wardrobes (cloth, now and then a shirt, trousers or boots), minibars (Almond Water, juice, crackers), housekeeping carts (cloth, a candle, sometimes the [housekeeping keycard](item-backrooms:l188-keycard), which opens guest rooms that are only locked, never one held shut), linen shelves (cloth), beds (cloth, sometimes linen).
- **The caves and the sea:** Level 8's cave-in boulders give stones, its bracket fungi are tinder (and some are food), and its crystals break for gems; Level 7's seashells grind to lime, and its seaweed is food.

**Tickets and prizes (Level 3999)**
[Arcade tickets](item-backrooms:l3999-ticket) come from the machines (each pays you once a day; 40 tickets a day at most, all machines together), the bins, and 3999.1's ticket piles. At a prize counter ({rightmouse}), the tickets in your hand buy one prize from the dearest tier they can pay, so hold only what you mean to spend:
- **5 tickets:** Almond Water, 2 candles, a [glow bracelet](item-backrooms:l3999-glowband-magenta), a [plush](block-backrooms:l3999-plush-bear-north) (cute), [popcorn](item-backrooms:l3999-popcorn), [cotton candy](item-backrooms:l3999-cottoncandy) or a [Paradise Pop](item-backrooms:l3999-soda-cherry)
- **15 tickets:** a bandage, Firesalt, a seed packet, 2 rusty gears, 3 neon tubing, 2 burger trays or a [neon lamp](block-backrooms:l3999-neonlamp-cyan-north)
- **40 tickets:** a copper lantern, a pry bar, a backpack, 6 Almond Water, 4 bandages or 5 neon lamps
- **200 tickets:** a temporal gear
A food stall's [tray meal](item-backrooms:l3999-traymeal-burger) costs 6 tickets. A neon lamp gives light 9 on any wall; a glow bracelet glows a little in the hand.

**Dispensers**
Fountains, coolers, vending machines, seeps and carts give with {rightmouse}. Most hold one to three servings and never refill (Level 4's vending machines and water coolers among them). The ones that do refill hold four to eight and fill again a week after they run dry: the spouts of the Almond Water fountains, the seeps beside Level 8's road, the hand pumps of Level 10's farmyards, the Snackrooms' drinks fridges and snack machines, the city's vendor carts, and Level 94's milk vans and water towers. Level 3999's vending machines take an Almond Water and give a snack, as often as you like.

**Level Keys**
A [Level Key](item-backrooms:hub-key-l5) opens its level's door in the Hub once, and is used up. Nowhere else does it open anything. The carved symbol on its bow is the one over its door. Each is found only in its own level: in sealed boxes and crates broken open there (likeliest at the heart of a den, behind a forced door, and in the level's worst places: Level 0's Red Rooms, Level 3's Sanctums and tunnels, the Sanguine Reservoir, the King's castle), on the remains of runners in Level !, in The End's desks and card catalogues. The M.E.G.'s wanderer in the Hub sells two at a time (30 to 45 rusty gears, only for levels someone has been to), and the Keymaster gives one. Levels 1 and 11 and the Snackrooms need none; Kitty's House has a pink door instead, and Level 188 a window.
""")

PAGES["food"] = ("Game Mechanic: Food and Water", """
**Food and Water**
*Nothing grows here. Everything you eat and drink was left behind by someone else.*

**Hunger**
You go hungry a quarter faster than in an ordinary world. Moving burns food; sprinting burns more; standing still burns almost nothing. Almond Water is a drink, not food (see Drinks below).

**Water**
Water is the bar above your food bar. It runs down about as hunger does: a full one lasts about 25 minutes of walking, or about 100 minutes standing still, and sprinting empties it faster. Heat makes you thirsty. From 30 °C up the water runs down faster, about 6% more for every degree, up to half again as fast. Level 2 (38 °C) and the boiler halls of Levels 3 and 5 (42 °C) are the worst; Level 3 (35 °C) and Level 3999's natatoria (34 °C) are hot too. Level 1 (28 °C) is warm but costs nothing extra.

**Supplies by level**
From Class 3 down, the levels hold less food and Almond Water. Caches, crates, supply boxes and the dispensers' stock come to seven tenths of their usual share in Class 3, half in Class 4 and a third in Class 5, on top of what the world setting gives. Level 94, the Snackrooms, the Hub and Kitty's House keep theirs.

**Drinks**
Drinks fill the water bar, and most of them feed you a little besides.
- [Almond Water](item-backrooms:almondwater) fills two-fifths of the bar and gives no food at all. It restores 15% stability, heals 1, and leaves an [empty bottle](item-backrooms:emptybottle) when you have drunk it.
- Cashew Water and a plain water bottle fill two-fifths of the bar, and give no food. [Cashew Water](item-backrooms:cashewwater) restores 8% stability.
- [Almond Milk](item-backrooms:almondmilk) fills about a third of the bar, and feeds you too. It restores 10% stability.
- [Soda](item-backrooms:soda) fills about a fifth of the bar. Juice boxes ([juice box](item-backrooms:l188-juicebox)) and strawberry milk ([strawberry milk](item-backrooms:l974-strawberrymilk)) fill about a quarter.
- [Red Water](item-backrooms:redwater) fills about an eighth of the bar, and [Memory Juice](item-backrooms:end-memoryjuice) less than a tenth.

**Drinking from the world**
Crouch, and with empty hands hold {rightmouse} on the water for a second and you drink your fill of a litre. Where you find the water tells you what it is.
- **Clean water** is the still water of the deep places: the pools of Level 8's caves, the ponds of Level 10, the pools of Level 37, the basin of Level 94's town fountain, and Level 974. It fills the bar as well as a bottle of Almond Water does, and it does you no harm.
- **Puddles and tainted water** is what most of the levels hold: the sumps and puddles of Levels 1 to 5, the flooded tunnels, the pools of the houses in Levels 9 and 94, the city's water and fountains, the natatorium of Level 3999 and the water of Level 188. It fills the bar only half as well, costs a little stability, and one time in four sickens you. Your stomach turns, and for about twenty minutes you burn both food and water faster.
- **The sea is salt.** Level 7's sea and the sea of Level Fun are brine. Drinking it makes you thirstier, not less.
- **Boiling water scalds.** The hot pools of Level 5's sumps are boiling, and they burn you a little when you drink.

**Bottles**
Drinking a bottled drink leaves an [empty bottle](item-backrooms:emptybottle), and empty bottles stack 16. Right-click a liquid with one in hand to fill it: [clean](item-backrooms:bottledwater-clean), [murky](item-backrooms:bottledwater-murky) or [salt](item-backrooms:bottledwater-salt), according to the water it is in. Boiling water fills a clean bottle.
Water coolers, drinking fountains, pumps, taps and seeps pour: hold {rightmouse} with empty hands to drink straight from one, or right-click with an empty bottle to fill it. Each costs one of its few portions. Vending machines and fridges hand out sealed bottles.
Murky water is the one to carry. Put a bottle of it in a lit [firepit](block-firepit-lit) and it boils clean. Salt water never does. That is how water gets from the wet levels into the dry ones.

**Running low**
Below two-fifths of the water bar you slow down, more the drier you get: a quarter slower at empty. Below a fifth the bar flashes. At empty you waste away. You lose a little health every few seconds, your Reality Stability drains, and the Wretches come for the parched as they do for the starving. Hunger works the same way at empty.

**What there is to eat and drink**
Only sealed boxes and crates hold food, and most were found torn or prised open long ago. Rooms behind locked doors were never picked over (see the pry bar in [Finding the Way](backrooms-finding)), and neither were the hearts of dens.
- **[Almond Water](item-backrooms:almondwater):** a drink (see above). Supply boxes, supply crates, drums; fountains, coolers and vending machines (Level 4, the city); seeps in the rock beside Level 8's road; the hand pumps on Level 10's farms; vendors' carts (the city); the towns' fountains and the hilltop water towers of Level 94.
- **[Crackers](item-backrooms:crackers), [canned beans](item-backrooms:cannedbeans):** supply boxes, crates, cardboard boxes, fridges, pantries.
- **Fruit and cheese:** fridges (Levels 4, 9, the city). **Flour, salt, fat:** kitchen cupboards and pantries (Level 9, city groceries).
- **[Chips](item-backrooms:chips), [chocolate](item-backrooms:candybar), [soda](item-backrooms:soda), [Cashew Water](item-backrooms:cashewwater) (8% stability):** the Snackrooms; city stores.
- **Fish:** Level 7, and seaweed in its shallows. **Game and berries:** Level 9. **Crops, livestock, honey, berries:** Level 10, where the fields stand ripe. **Mushrooms:** the bracket fungi of Level 8's caves, some of them.
- **Level 94:** iceboxes in every house (cheese, butter, beans), [Almond Milk](item-backrooms:almondmilk) (10% stability) in the milk vans by the towns' plazas, Almond Water from the fountains and water towers.
- **Level 37 has no food at all.** Take enough with you. Its dark corners hold [Epsom salt](item-backrooms:epsomsalt) for poultices, and the Sanguine Reservoir's red sprouts give [Red Water](item-backrooms:redwater), which heals every wound and lowers for good how steady you can ever be.
- **[Energy Bars](item-backrooms:run-energybar):** only in Level !: the bedside table, trays beside doors, the Safe Zone's shelves. Eating one gives you a second wind: a little more speed for half a minute.
- **Level Fun:** [birthday cake](item-backrooms:fun-cakeslice-birthday) ({rightmouse} a cake for a slice), [cookies](item-backrooms:fun-cookie) from the plates, Almond Water on some tables, pumpkins in the Halloween rooms, onions from popped balloons. **[Red Velvet =)](item-backrooms:fun-cakeslice-velvet): do not eat.** It fills you well, but costs you stability and the party gets into you (Party Fever). Gifts hold what wanderers left; one in five is a popper, and the bang carries.
- **The End has no food:** Almond Water from the coolers in the stockrooms, nothing else. [Memory Juice](item-backrooms:end-memoryjuice) restores 20% stability, and for a while everything feels like home. The Junkies want it.
- **Kitty's House (Level 974):** the fridge and the pantry give one thing per {rightmouse}, six at most, one more every 2 hours: bread, cheese, fruit, [strawberry milk](item-backrooms:l974-strawberrymilk). After a day half of it is sweets ([marshmallows](item-backrooms:l974-marshmallow), [candy](item-backrooms:l974-candy)), after two days all of it. Now and then a [remembered meal](item-backrooms:l974-meal-pancakes) lies on the table, the best food in the house. Every tap fills a bucket, jug or bowl with water.
- **The Hub has nothing to eat.** Bring food, water and clothes.
- **Level 3999:** [tray meals](item-backrooms:l3999-traymeal-burger) at the food stalls, 6 tickets each (burgers, pizza, noodles, tacos, ice cream, pretzels: filling, and they heal a little). The vending machines take one Almond Water for chips, a candy bar, popcorn, cotton candy, soda, cashew water or Paradise Pop, and never run out. See the tickets in [Salvage](backrooms-salvage).
- **Level 188:** the lobby's breakfast dispensers ({rightmouse}): [cereal](item-backrooms:l188-cereal) and [juice boxes](item-backrooms:l188-juicebox), three of each, then empty; the minibars in the rooms.

**Food and water that come back**
See [Home and Expeditions](backrooms-home): fish, game, crops, livestock, the refilling dispensers, and a farm of your own. Everything else is finite: a level is a larder that empties. Drink dispensers that hand out water are one-time stock now; only the Level 8 seeps fill again, slowly (the Level 10 ponds are water, which you can drink from as it is).

**Cold**
Nothing here is cold enough to kill you quickly, but the cold levels are cold enough to hurt without clothes: Level 6 (8 °C), Level 8 (9 °C), Level 7 (12 °C, 6 °C under the sea), the Hub's tunnels (6 °C, and 2 °C in the Far Tunnels), Level 188's courtyard (8 °C), Level 3999's Blackout (14 °C) and the open decks of Level Fun (11 °C). Clothes come from Level 5's wardrobes and suitcases, Level 9's dressers and Level 188's rooms; Level 5's furnaces and boilers and Level 1's burn barrels give off warmth. Level 0's blackout zones (10 °C) are the useful cold: food in a chest there keeps more than twice as long as in the Lobby proper, and any fully enclosed room counts as a cellar for the vanilla [preservation](gamemechanicinfo-foodpreservation) rules.

**World settings**
When a world is created, *Backrooms scarcity* (under Survival challenges) sets how much food and drink the Backrooms leave you: Plentiful doubles it, Sparse leaves six parts in ten, Scarce about a third. It scales everything you can eat or drink, Almond Water among it, in every box, crate, cupboard and fridge; how much the vending machines, water coolers, fountains and Kitty's fridge and pantry hold, and how soon they refill (on Scarce, what refills does so after three weeks rather than one, and about one in three of Level 4's vending machines and water coolers is empty from the start); and how much livestock grazes in Level 10. In new worlds on Sparse or Scarce, Level 9's gardens and Level 10's crops, vegetable patches and berry bushes bear less too (by the scarcity the world was created with, even if it is changed later). Seeds, notes and tools are not affected. *Backrooms map* sets how much the map helps (see [Finding the Way](backrooms-finding)).
*Thirst*, also under Survival challenges, turns the water bar on or off. With it off, drinks are food again as they used to be, nothing runs dry, and heat drains your hunger instead of your water. *Fatigue* does the same for the Rest bar: with it off you never tire (see [Rest and Sleep](backrooms-rest)).
""")

PAGES["rest"] = ("Game Mechanic: Rest and Sleep", """
**Rest and Sleep**
*You can get about for an hour or two on your feet. The Backrooms count every minute of it.*

**The Rest bar**
The bar above your health is your rest. It starts full, at 48 minutes of play, and it empties as you stay awake. A game hour here is two minutes, and a day is 48. There are four stages:
- **Rested** (the first 48 minutes awake): nothing. A bed will not take you yet; the game says you are not tired enough.
- **Drowsy** (48 to 90 minutes): you can lie down and sleep, and the game tells you so once: "You could sleep now". From about an hour awake your Reality Stability starts to drain, a little at first.
- **Exhausted** (90 to 120 minutes): you walk a tenth slower, your Reality Stability drains faster the longer you go without sleep, and the things that live here come to find you more often.
- **Dead on your feet** (from two hours): you walk a fifth slower, the bar flashes, the screen dims and blinks now and then, your Reality Stability drains harder and harder, and the things that live here come in greater numbers. The Wretches come for you as they do for the starving. Nothing here kills you outright, but the Backrooms do: lie down before it comes to that.

**Sleeping**
Right-click a bed to lie down in it once you are drowsy. The foot of a two-part bed works as well as its head. While you sleep the Rest bar fills, and the clock runs fast, as in any Vintage Story world: when everyone is in bed a night passes in a moment. On a server the clock hurries only when everyone is asleep.

**Beds**
Any bed will do, and some do better.
- **Hotel beds** (the rooms of Level 5, the houses of Levels 9, 11 and 94, Kitty's bedroom, the rooms of Level 188) are the best. A night in one takes you from dead on your feet to rested.
- **Hospital beds** (Level 1's camp rooms, Level !), **cots** (the Safe Zone, the Hub) and **sleeping bags** (Level 4's outposts, the camps) are a step behind. Hospital beds are nearly as good; cots and sleeping bags give you a little less.
- **Makeshift beds and bedrolls** of the camps (Levels 1, 4, 7 and 8) are the least. A poor bed refills you more slowly: from dead on your feet it takes more than half a game day to make you fully rested.

**The carpet bedroll**
The one bed you can make yourself is the [carpet bedroll](block-backrooms:carpetbedroll-north), from 16 carpet fibres + 2 flax twine + 4 wallpaper strips, in a grid two wide and three tall: a stack of 8 fibres in each top slot, a twine in each middle slot, 2 strips in each bottom slot (3 carpet fibres make a twine). It is enough to sleep on, not enough to sleep well. Put it down anywhere, and when you pick it up again it comes back whole.

**What wakes you**
You wake rested ("You wake rested"), or sooner for one of these, and the game says which:
- **Pain:** you take damage. "Pain wakes you."
- **Something close:** a creature that hunts or stalks you comes within six blocks. "Something is in the room."
- **Thirst or hunger:** the water or food bar falls below a tenth. "Thirst wakes you" or "Hunger wakes you", and you cannot go back to sleep until you have eaten or drunk.
- **Sneaking:** crouch, and you get up.

**Night visits**
Sleeping outside a safe place invites a visit. A night's sleep in an ordinary level may draw something to your bed: a hunting creature, placed out of sight a dozen or more blocks away, coming for you. The odds rise with the level's danger: about one night in sixteen in Level 1, one in four or five in Level 5, and more than one in three in the deepest levels. Level 0, the safe places and anywhere beside a wanderer never get a visit. A closed door within four blocks of the bed halves the odds, which is what the wanderers' notes mean by "barricade your door". The sleeper wakes as the creature closes in.

**Almond Water for rest**
[Almond Water](item-backrooms:almondwater) is the drink for it: [Blue Almond Water](item-backrooms:almondwaterblue) makes you drowsy at once, so you can lie down straight away, and steadies you (a quarter restored). [Green Almond Water](item-backrooms:almondwatergreen) keeps the tiredness off for about twenty minutes, and the exhaustion lifts while it does. When it wears off, the sleep it held back lands all at once, about sixteen minutes' worth of tiredness. Drink two and it lands twice.

**Sitting by a fire is not sleep**
Resting by a fire, or beside a wanderer, keeps the things that live here back (see [Home and Expeditions](backrooms-home)), but only sleep refills this bar. Eat and drink before you lie down: a sleeper who is hungry or thirsty is woken at once.

For the things that come, see [What Lives Here](backrooms-entities). For the drain on your stability, see [Reality Stability](gamemechanicinfo-temporalstability).
""")

PAGES["levels"] = ("The Levels: 0 to 11", """
**The Levels, from the Lobby to the City**
*Each lies around the one before, like rings. The walls between them are solid, but for a few gates.*

The levels nest around the place you woke: Level 0 at the centre, Level 1 around it, Level 2 around that, and so on out to Level 10, which goes on forever. No ring is round: a level may end after a few hundred blocks in one direction and go on for several times that in another. Where two levels meet there is a wall with a gate every few hundred blocks (see [Finding the Way](backrooms-finding)), and each level keeps its own look right up to it: the next level only shows in the short passage through a gate. The deeper the level, the more dangerous and the better stocked (see [What Lives Here](backrooms-entities)). Levels 11, 37, 94 and the far places are not rings at all: see [The Levels: Beyond the Rings](backrooms-farlevels).

The distances on this page are for the usual *Backrooms level size*. That world setting (under World generation, when a world is created) makes every ring from half as wide (50%) to twice as wide (200%): only how far you go through each level changes, not its rooms, halls or buildings, and the far places lie where they always do. It is fixed when the world is made.

**Level 0, the Lobby.** Yellow wallpaper, damp carpet, humming lights. Districts of rooms laid like bricks, split into rooms and winding hallways that turn every few dozen steps and open through doorless gaps; there is always more than one way. Supply boxes in the corners of rooms, glass in the ceiling, strips and fibres in the walls and floor. The **blackout zones** are dark, cold (10 °C) and drain you; the **Manila Room** (manila wallpaper, a table and a chandelier) restores you and nothing hostile goes in; the **Red Rooms** (red wallpaper, red lamps) hold untouched boxes and drain you faster than nearly anywhere: be quick. Pits in the floor drop into Level 2. The Lobby is empty but for the dark figures of its outer reaches, which rise out of the mould far out towards the edge (460 to 3,300 blocks out, depending on the direction). Smilers come only into the Red Rooms, and when the lights fail in a Reality Shift.

**Level 1, the Habitable Zone.** A concrete car park in grey fog (28 °C), walled into districts with gaps where the aisles run through, and white maintenance halls. Supply crates (food, planks, twine, charcoal), pallets, workbenches, toolboxes, cable spools, loose stones and flint, wrecked cars, wanderers' makeshift camps. The car park is nearly neutral; the corridors drain a little. Stairwells lead to other stairwells. Rats and the odd Faceling in the halls, Hounds, Smilers and Dullers (in the walls) in the dark sections, Clumps and Wretches towards the edge, now and then a Skin-Stealer, and out there the lights of a whole section sometimes fail for a minute or two: a Flickering.

**Level 2, Pipe Dreams.** *The first copper is here.* Hot (38 °C: you go hungry half again as fast), dark tunnels: the three-wide mains run on for miles, now and then jogging aside at a crossing; the narrow ones between them often end. Some carry the rusting rails of a dead tramway. Machine cabinets (copper), drums, trolleys, toolboxes, machine parts. Steel doors in the walls: most locked, some storerooms, a few lead to another level. Drains you everywhere: pass through. Smilers, hairless rats, Clumps buried in the floor, and towards the edges Hounds, Deathmoths and the odd Wretch.

**Level 3, the Electrical Station.** Hot (35 °C) brick, tile and machinery: carry food. Cramped tangles and stooping squeezes, wide galleries, vast transformer halls, and Sanctums of ashlar stone where nothing hostile goes. Cable spools, stacked pipes, industrial fans, coal heaped by the generators (with Firesalt in it), clay in the flooded tunnels below the manholes (which drain you nearly as fast as a Red Room: dig and get out). Drains you. Elevators. Smilers, Hounds, Dullers in the walls, Clumps, Skin-Stealers, Wretches, and Facelings, which here are the Evolved: half-formed faces, and hostile. It is a busy level, far more so than Levels 0, 1 and 4: something turns up on most walks through its galleries.

**Level 4, the Abandoned Office.** Quiet and safe, and it restores you. Furniture for planks and paper, fridges, Almond Water on tap from the fountains and coolers, toolboxes with the odd copper tool, potted plants for soil and pottery shards (a slow clay: see [Salvage](backrooms-salvage)). A few vending machines take you instead of serving you. Elevators and stairwells stand together in building cores, with restrooms. Wanderers' outposts. It is mostly devoid of entities: now and then a Duller reaches through its walls, and the odd Hound wanders by, both seldom.

**Level 5, the Terror Hotel.** Beds (the head end comes away as a real bed), clothes, linen, silver and brass, coal in the boiler halls (42 °C, with scalding sumps underfoot). The lobby is neutral, the corridors wear on you, the boiler halls badly; the Beverly Room is safe and restores you. Elevators; a few of its locked doors open; the staff stairs behind an open STAFF door lead to Level 6, and the grand staircases by a lobby's front desk back up to Level 4. Hounds, Skin-Stealers, Death Rats in the boiler halls, Wretches, moths, and once in a long while, deep in the boiler halls above all, the Beast of Level 5.

**Level 6, Lights Out.** Cold (8 °C), total darkness. Hold the brightest light you have and mark your way with [chalk](item-backrooms:chalk): chalk marks show white on the map. Keep to the long dry corridors; passages wet underfoot end blind. Lost backpacks. Stairs down lead to Level 7: they are few, and the deeper into the level the likelier. Listen for the waves, which grow louder the nearer you come, and look for arrows chalked along the corridors. The stairwell is two wide and goes down through the rock to a landing; walk on and you come out at the foot of the stairs into a room hung over the sea, and those stairs bring you back. (In worlds made before 0.514.0 the stairs are three steps, they are common, and they drop you out of a room in the ceiling into the sea, one way.) Nothing is ever met here, only seen: Smilers, far off in the dark.

**Level 6.1, the Snackrooms.** Sealed food courts, bright and safe, their machines and shelves full and refilling. Some shops are heaped to the ceiling with dead vending machines; only the one in the doorway still works. You cannot walk in, and nearly every door out shuts behind you.

**Level 7, Thalassophobia.** A cold sea (12 °C, 6 °C under water) under a high concrete ceiling, in a dim light that comes from nowhere and is the same at every hour; it fades as you dive, and the midnight zone is dark. Driftwood, fish, seagrass and seaweed in the shallows, a dead reef, islands of dark rock with seashells on their rims, rising in steps from the water (some with an abandoned camp, now and then a shelter of broken furniture stuck together with tar), pillars of the same rock standing up into the ceiling from the islands and out of the sea, jetties, wrecks on the bottom, and a floor of sand (the Backrooms' only sand to speak of, and so the mortar for fire bricks). The surface is neutral; the deeper you dive the darker and the less stable, and something circles divers who stay down too long. Tar can be taken from its pools with a bucket: right-click a pool with an empty one (it scalds anyone standing in it), and rubble and a litre of it, in a barrel, make asphalt.

**The entry rooms** hang from the ceiling in piers of concrete: a study with a bookcase, a coffee table and a chair, its carpet soaked, the stairs from Level 6 coming down into it, and across from them a doorway onto the sea five blocks above the water. A rope ladder hangs from the doorway into the water: the way back up.

**Air under the sea.** Out over deep water a buoy floats with a rope ladder hanging from it all the way to the bottom. Under it lies a room on the seabed with air still trapped under its roof and its light still on, showing through its windows. Climb down the line, swim in under the room through the low tunnel beside it and come up through the hatch in its floor: you can breathe there before you go back up. Each room has a chest, and the deeper the room the better what is in it: a sea chest in the twilight zone (rope, bandages, candles, copper bits, the odd copper tool), a strongbox in the midnight zone (copper and bronze ingots, silver and gold bits, bronze tools, now and then a temporal gear). The midnight zone is where the Thing circles. (In worlds made from 0.514.0.)

**Level 8, Cave Systems.** Cold (9 °C) real rock, ore, coal and clay, in the dark, with packs of Wretches where the light fails and Giant Spiders waiting in it, and here and there stretches of cave strung with their webs. Stalactites and stalagmites, hanging lichen, bracket fungi on the walls (tinder, and some to eat), glowing mushrooms in some stretches (mostly blood-red; they give nothing but rot), boulders from cave-ins, crystals deep down, and rare colonies of glowworms. Ore runs through the rock in veins and pockets. Dress warmly. Off the road it is a busy level, far more so than Levels 0, 1 and 4: the Wretches and spiders come often, with rats, the odd Duller and Smiler, and Hounds towards the edges. Keep to the lamps of the 9th Road and its camps: the road restores you and the dark off it drains you. The road winds through the rock, forking and joining again, but it does not always run on: now and then a rockfall ends it in a wall of rubble, with a long stretch of solid rock beyond and its lamps stopped short, and the way on lies down through the caves, away from the light. Look for a cave mouth in the road's wall just before the rubble: the passage winds off into the dark and down, past side passages that lead nowhere, and comes up on the far side. Camps are few and far between. Where the road meets another level it runs through the wall. Almond Water seeps from the rock beside the road: use a seep to fill a bottle. The pools of tar scald, but a bucket right-clicked on one takes tar from it (rubble and a litre of it, in a barrel, make asphalt).

**Level 9, the Suburbs.** Endless night. Houses to search (in some, the bedrooms are upstairs; in new worlds the front and back doors open and shut with {rightmouse}, and a locked one gives only to a pry bar): kitchens, pantries, garages with tools and seeds, dressers of clothes, toy boxes. Real trees, tall grass, flowers, berry bushes gone wild, and wildlife by night: hares, foxes and raccoons. The streets drain you. Hounds, rats, Smilers, Wretches and Skin-Stealers, Deathmoths near the edges, the Striders of the Neighborhood Watch walking the streets (they see a light from far off) with the Watcher's floating eye above them, and once in a long while the Mangled. The Suburbs are a busy level, far more so than Levels 0, 1 and 4: something turns up on most walks through the streets.

**Level 10, Bumper Crop.** Farmland under a grey sky, now and then lost in fog for a few minutes, safe and stable. Crops standing ripe, livestock in the paddocks, ponds with cattails, reeds and clay (and a little sand on the bed of a few), bee skeps, barns with a quern and seed sacks, and iron hand pumps in the farmyards that still give a little Almond Water ({rightmouse}; it comes back after a week). The old fields are exhausted: replant in fresh soil. A metre under the soil is a mass of worms: do not dig down. Nothing hostile lives here: the worms underfoot are its only danger.

**Level 11, the Endless City.** Not a ring: far out past the fields, reached through a barn wall. Safe on the streets (bar a rat or two in the alleys), and they restore you; the subway drains, and Dullers and Wretches live in it. Stores full of food, tools and clothes, diners, a subway, Almond Water everywhere, wanderers, and ways to almost every level: see [Ways Between Levels](backrooms-thresholds). On the streets nothing attacks unless you start it.
""")

PAGES["farlevels"] = ("The Levels: Beyond the Rings", """
**The Levels Beyond the Rings**
*No wall leads here. You get in by the ways in [Ways Between Levels](backrooms-thresholds), and by no other.*

**Level 37, Sublimity (the Poolrooms).** White tile and warm, still water, rooms and pools that make no sense, light falling through slits from somewhere you never see, and corners left in the dark. Nothing lives here; no one has ever met anyone. Standing in lit water heals you, steadies you and counts as rest, so it is the place to recover between expeditions. But there is no food at all, the dark corners drain you, and the deep water is where people drown: stair pits go down further than you can see, and some passages are a swim under a wall. Crusts of [Epsom salt](item-backrooms:epsomsalt) dry on the rims in the dark.

**Level 37.1, the Sanguine Reservoir.** Far out in the Poolrooms, the light thins, the water turns thick and slow and red, and red sprouts on the pool floors are all the light there is. A distant chanting draws people in, louder the nearer you come. Stability drains fast. What the drowned left lies on the bottom, untouched; and the red water heals everything, at a price.

**Level 94, Motion.** You fall into it out of the sky, and land softly. A stop-motion picture of the 1950s: round green hills, a two-storey cream house on each, winding roads behind white picket fences, small towns round fountains of Almond Water, siren poles playing the same tune all day. Food in plenty, and the ground is clay: dig the turf for soil, the red modelling clay under it for clay (blue clay a little way down), and three to seven blocks down, over much of the hills, pale seams of **fire clay**, the only fire clay in the Backrooms and the key to iron and steel. **By night the Animations come out** (with the odd Hound, Skin-Stealer and Smiler), and hunt anything that does not look animated: be indoors by dusk (when the tune slows and goes flat, from half past five, it is nearly time; they are out from eight until half past five in the morning), or stand quite still and be taken for a doll. Towards the middle the houses come apart, room by room, into heaps of furniture; follow the strangeness (or the white castle on the horizon, which glows a little after dusk) and you reach the glass mountain and the King's castle, which drains you.

**Level !, Run For Your Life!** You are taken there, and the door slams behind you. A hospital room in red light, an alarm, something hammering at a chained door (it holds for twelve seconds, or four once you are in the hall). Take what is in the bedside table and the cabinet (Almond Water, [Energy Bars](item-backrooms:run-energybar), a bandage) and go: the way out is **the door under the lit EXIT sign**, and it sticks (pull it three times). Then **run, and don't stop**: about a minute and a quarter at a sprint, some 480 blocks of hall lit only by EXIT signs (600 in worlds made before 0.514.0). Swerve round beds and chairs, jump fallen shelving, mind the doors that fly open and the signs that burst into flame, and jump the junk on the floor (toys, boxes, tangled cords, fallen ceiling): sprint over it on the ground and you trip. The horde behind you runs at four fifths of your sprint, a little slower just after it bursts out: it falls back while you run and catches you the moment you stop, and **being caught is death**. **Telling the exits apart:** a false exit has a turn in the hall beside it, its EXIT sign is darker with the X burnt out, and the gap under its door is dark. The real exit is at a dead end with no turn either side, under a bright EXIT sign, with a faint light in the gap under the door; it leads to Level 1, Level 4 or The End. Escape once and the Backrooms never send you there again; a present waits by the door you come out of, once, ever: 25 rusty gears and 2 temporal gears. A blue stretch of hall is the Safe Zone: nothing comes in, not into the hall nor its side rooms, so rest and eat, but go when the walls shudder (after about two hours; at three the horde comes in).

**Level Fun =).** Endless party rooms on a ship that cannot be this big: balloons, streamers, cake on every table, a tinny "Happy Birthday" somewhere through the walls. A room with a **balloon arch** over its door and **music** playing has guests: tall yellow **Partygoers** with a smile carved into the face (see [What Lives Here](backrooms-entities)). Their tables are the best larder in the Backrooms. Dark service corridors hold balloons tied to nothing: don't touch them. **Anything marked =) is a lie**, wanderers' notes included. It drains you everywhere, and the open decks are cold (11 °C). You arrive in an elevator lobby; the ways home are rare: stairs into the ceiling (Level 1), wooden doors marked FUN (the hotel), a waiting room's door (the city).

**The End.** A library that goes on forever, and the cruellest trap in the Backrooms: it looks like the way out. Empty maple shelving under fluorescent lights, and in the middle a curved desk under bronze letters: THE END.
- **Doors marked EXIT** stand in the stockrooms and at the corners of the central hall. Two in three never open. The rest always lead to the same place: Level 1, the Hub, the city, the Office or the Hotel, and back again.
- **Fake realities:** out in the library, places you know (the Lobby, an office, a hotel corridor, a house, a snowfield) that the shelves blend into. Some have a real door in their middle.
- **A vent** at the top of a ladder in some stockrooms drops you into Level 94.
- **The computers** buzz until you turn one on. It shows the name of the place and dies for good, but marks on your map the nearest ways out that open. If a screen says =), you are not staying; now and then one runs TRUEEND.EXE instead, and takes you to Level 3999.
- **The longer you stay, the less sure of yourself you are:** after two in-game hours inside, stability drains a little more each minute. It is kindest in the middle; outward it drains, and the collapses and fake realities drain badly.
- **Distortions:** now and then the floor shakes and for a few seconds you are somewhere else. Walk into a wall or a shelf then, and you will be (the snowfield leads nowhere). And the lights go out for a minute or two: carry a light.
- No food (see [Food and Water](backrooms-food)), but furniture, ladders and books for a home. In the Home fake realities live the Junkies, who trade only with someone carrying Memory Juice.

**The Hub.** A hidden crossroads of road tunnels under orange lamps, silent and cold (14 °C at the centre, 6 °C in the tunnels, 2 °C far out). Ten numbered tunnels run out from a tower at its centre, and both walls are lined with great concrete doors, a crop circle carved over each. Every door leads to a level, and almost all are locked.
- **Safe:** nothing hostile follows you in, it restores you, and resting here counts. But there is nothing to eat: bring food and clothes.
- **Open doors:** three are always open, each one way: Level 1 in Tunnel 7, Level 11 in Tunnel 10, the Snackrooms ("178") in Tunnel 5. The M.E.G. marked them, and their outpost by the Level 11 door has a register ({rightmouse}) that marks them on your map, and a wanderer who sells Level Keys. A second camp keeps the Level 1 door.
- **Level Keys:** any other door needs its level's key (see [Salvage](backrooms-salvage)). Hold a key in your hand in the Hub and listen: it rings from the way its door lies, and close by the door goes on your map. Use the door with the key: three turns, the key is gone, and there is no way back through.
- **The pink door** with a ribbon bow needs no key, only something cute on you: it leads to Kitty's House.
- **A lit window** in a tunnel wall, a room behind it: climb through (walk into it, or {rightmouse}) to Level 188's courtyard, and back.
- **The way back** is the plain grey door you came in by.
- **The Far Tunnels:** past the third ring road the lamps die out and the place stops restoring you. Out there are a wall that isn't there (Level 4), holes in the road (Level 94), and tunnels where the concrete turns to white tile (Level 37).
- **The Tower:** ten ornate doors at the inner ends of the tunnels. You are let in once. Its keeper wants you gone, and will give you one key to make sure of it. Break nothing inside, and mind the balcony: fall from it and you are thrown out into the tunnels.

**Level 974, Kitty's House.** Not a place you can walk to. Cross into any level with something cute on you (a plush, a flower, a seashell) and, once in a while, you are taken here instead, more often if you hold it in your hand. A small pink house with no door to the outside: its windows are paintings. To leave, hold out the cute thing you brought and call, "Here Kitty, Kitty, Kitty!" (right-click the tall shape with it in hand): Kitty takes it, you grow sleepy, and you wake somewhere safe. Nothing hostile comes: lights, water from every tap, a bed you can sleep in, a fridge and a pantry that fill again, and an old computer whose e-mail explains the rest. **Kitty** lives here: very tall, faceless, black as cloth, and it will never hurt you. It watches.
- **Be a good guest.** Break anything in the house, or strike Kitty, and the lights go out, the food is gone, your stability takes a blow, and Kitty will not see you for a day.
- **Don't stay long.** After 18 hours the pink starts to wear on you (and more so at 36 and 60); after a day half the food is sweets, after two days all of it.
- **To leave**, hold the cute thing you brought (not what you found here), sneak and {rightmouse} to call ("Here Kitty, Kitty, Kitty!"), then {rightmouse} Kitty when it holds out its arm. You fall asleep and wake somewhere safe (Level 4, 37 or the Snackrooms), the same place every time for your house, and for three minutes nothing comes near. Lost what you brought? After a day Kitty takes anything cute, but you wake where you last slept.
- The house is yours: what you leave in it is there next time.

**Level 3999, the Neon Paradise.** An arcade the size of a city: carpet that glows under black light, neon on every wall, music from nowhere. Concourses eighteen blocks high with galleries along both sides and **moving walkways** that carry you; game rooms and halls, food courts, bowling lanes, lobbies with a revolving door, pools of warm violet water. Warm (24 °C; the pools 34 °C) and **safe**: nothing hostile comes where the neon is lit, and the gear turns forward, most in the lobbies. Standing in a pool heals you slowly. Faceless **Arcade Attendants** keep the counters; a **mall directory** ({rightmouse}) marks the nearest food court and lobby on your map. More wanderers camp here than anywhere (one lobby in four).
- **Machines:** hold {rightmouse} on one to play it out. Each pays you tickets once a day (little cabinets 0 to 3, pinball 0 to 4, racers, dance pads and skee-ball 1 to 5, now and then a jackpot of 12; the claw drops a plush one go in four, nothing otherwise), and no more than **40 tickets a day** from all of them together.
- **Prize counters** take the dearest tier the tickets in your hand can pay (5, 15, 40 or 200: see [Salvage](backrooms-salvage)); **food stalls** sell a tray meal for 6; **vending machines** take one Almond Water for a snack or a drink.
- **The machines, counters, doors and windows cannot be broken.** Dead machines, bins and dead neon can (see [Salvage](backrooms-salvage)).
- **Ways in and out:** a lone arcade at the end of a line of five red-lit windmills in Level 10, a purple-flickering alley wall in the city, a computer in The End, magenta tiles under the far Poolrooms' deep water, and the Hub's door marked 3999 lead in; STAFF ONLY doors (one in six opens, onto the Hub), the mini arcade's elevator (Level 0), the themed cabinets (played to the end, one way to the level on the marquee) and the pools' drains (Level 37) lead out.
- **Level 3999.1, the Neon Blackout:** far out, whole blocks of the mall have gone dark behind a stretch of failing neon. Cold (14 °C), it drains you fast, and Smilers, Hound packs and Partygoers hunt there. Its prize cases and ticket piles are free for the taking. A rusted cabinet in a row of machines is not solid: walk into it and you are in the dark.

**Level 188, the Courtyard of Windows.** A dark courtyard of mossy lawns and a round wooden deck, walled in by a five-storey hotel with 160 small square windows, under a black sky. You come in through a window and climb down into the courtyard. **The window you came in by still shows where you came from, and leads back.** Other windows on the ground floor show other places, and lead there. Inside, grey corridors run round the courtyard past unnumbered rooms; the stairs are in the north-west corner, the lifts are dead and the lobby's front door is locked. The building cannot be broken.
- **Never open a blind from inside a room:** whoever does is taken, one way, always to the same place for that window; the window then shows it, and the room's door stays shut for three days.
- **If someone is standing in a lit window, waving, count which room it is and stay out.** Within two blocks an arm comes out of the glass, and six seconds at the glass is death (see [What Lives Here](backrooms-entities)). They move to other windows every night.
- The rooms are warm (21 °C) and steady you a little: shut a room's door behind you and nothing comes in, unless someone was waving in its window. The courtyard is cold (8 °C) and drains you, the roof more.
- Clothes, cloth, beds and a little food (see [Salvage](backrooms-salvage)). A fire exit on each upper floor leads out, each somewhere different, and the iron ring in the deck opens onto a long fall into the water of Level 37.
""")

PAGES["thresholds"] = ("Ways Between Levels", """
**Ways Between Levels**
*The rings are only how the place is built. The doors are the real map.*

**The two rules**
- Every threshold always leads to the same place. Both ends are marked on your map the first time you go through.
- If you walked through it, you can walk back. If you fell, dived or were taken, you cannot.

**Coming back**
An elevator arrives beside another elevator, a stairwell beside a stairwell, a door beside a locked door, a vent beside a vent grille: that one is now your way back, and where the level has none to spare, one is built into a wall beside you. Only when there is no room for that, a **thin spot** is left where you arrived: a pale, wavering seam in the air that hums. {rightmouse} it to step back through. It stays for good.

**Two-way**
- Elevators (Levels 3, 4, 5): to another elevator in Levels 3 to 5; from the hotel, sometimes Level 1. Everyone in the car rides along.
- Level 1 stairwells, up or down a flight: another stairwell in Level 1. From the top floors about one flight in twenty-five climbs into Level 4, and one flight in sixteen down from the bottom floor comes out in Level 2's pipe tunnels.
- Level 4 stairwells: another Level 4 stairwell; one flight down in five comes out in Level 0.
- Level 5 doors: most are locked for good. A few open (about one in sixteen), onto the hotel, Level 3 or Level 0.
- Level 5 staff stairs (an open door under a STAFF sign): Level 6.
- Level 5 grand staircases, either side of the front desk at the end of a lobby: up through the ceiling to Level 4, at the top of a stairwell's flight down, which leads back.
- Level 2 steel doors in the tunnel walls: most are locked. Some open, onto Level 3, Level 4 or Level 1.
- Level 8 vents beside the 9th Road: Level 2, out through a vent grille in a tunnel wall; crawl back into it to return.
- Level 9, the gate at the end of a field behind the houses: Level 10.
- Level 10, a stretch of barn wall that is not quite there (east wall, between the stalls, in some barns): Level 11.
- Level 6, a stairwell down toward the sound of waves, walked to its landing: the foot of the stairs into one of Level 7's entry rooms, which lead back up to the landing.

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

**Two-way, to and from Level Fun, The End and the Hub**
- Level 1, stairs into the ceiling with confetti on the steps and a red balloon on the rail: Level Fun's service stairs.
- Level 5, wooden double doors with big letters F-U-N (now and then a locked door): Level Fun's FUN doors.
- Level 11, gym doors painted with a tiger, a parrot and a giraffe, at the back of a parking garage: a Level Fun waiting room.
- Level 1, a locked hall door under a glowing EXIT sign: The End, beside an EXIT door.
- Level 11, the door of a closed-down bookstore (THE END IS NEAR in its windows): The End.
- The End, an EXIT door: two in three never open; the rest lead to Level 1, the Hub (beside a grey service door), the city, Level 4 or Level 5.
- The End, the real door in the middle of a fake reality: the Lobby to Level 0, the office to Level 4, the hotel to Level 5, the house to Level 9.
- The End, a vent up a ladder in a stockroom: Level 94, out of the sky.
- The End, walking into a wall or a shelf during a distortion: the place it showed you, most often the Lobby, else an office, a house, the Poolrooms or the hills; one time in five, nowhere (and the snow leads nowhere).
- Level 1, a grey door with a carved crop circle over it, partway along a winding maintenance hall (chalk arrows lead to it): the Hub, beside a grey service door.
- Level 2, now and then a steel tunnel door with a chalk circle: the Hub.
- Level 37, a dry corridor whose tile gives way to concrete and asphalt: the Hub, where a tunnel's concrete turns to white tile.
- The Hub, walking into a stretch of wall whose seams don't meet (Far Tunnels): Level 4.
- The Hub, walking on where a tunnel's concrete turns to white tile (Far Tunnels): Level 37.

**Two-way, to and from Levels 3999 and 188**
- Level 10, a lone arcade (PARADISE in neon over dark glass) at the end of a line of five windmills with red lights on their caps: its revolving door, into a lobby of Level 3999, whose revolving door leads back. The lever by a windmill's door turns its light green, for good.
- Level 11, a stretch of alley wall flickering purple: walk into it, Level 3999.
- Level 3999, a STAFF ONLY door: one in six opens, onto the Hub beside a grey service door; the rest are locked.
- Level 3999, the elevator at the back of a little arcade inside some game rooms: Level 0.
- Level 0 (far from where you woke) and Level 1 (in a car park), a window where no window should be: climb in, Level 188's courtyard, beside the window that shows where you came from.
- The Hub, the lit window in a tunnel wall; Level Fun, a party room's window with confetti on the sill: Level 188.
- Level 188, a ground-floor window that shows another place: climb in at the sill (the Lobby, Level 1, 2, 4, 5, 6 or 9, the Hub, Level Fun).
- Level 188, the fire door on each upper floor: Level 1 from the second, Level 5 from the third, Level 4 from the fourth, Level 2 from the fifth.

**One-way**
- Level 0 pits: Level 2.
- Level 4, a vending machine that takes you (the same few always do): the Snackrooms.
- Level 6, a wire across a passage: the Snackrooms.
- Level 6, stairs down toward the sound of waves (worlds made before 0.514.0): Level 7, from the ceiling.
- The Snackrooms: rusty doors to Level 6, glass doors to Level 4 or 5, vents to Level 3, kitchen doors to another food court (except the one you arrived beside from a diner, which leads back).
- Level 7, diving into the ring of standing stones: Level 9. Swimming into a cave mouth in the deep: Level 8.
- Level 10, diving to the bottom of a pond: Level 7.
- The city: an open manhole to Level 2, a caved-in street to Level 8, the deep middle of a park fountain to Level 7.
- Level 7, a patch of white tile on the seabed in the twilight zone, faintly lit: dive to it and surface in Level 37.
- Level 9, the rare backyard pool that is still full, lit teal at midnight: dive to its bottom, Level 37.
- Level 37, the bottom of a pit nobody has found the bottom of: you come up in a backyard pool in Level 9.
- Level 94, the door of a house full of water: Level 7.
- Level 94, winning the King's trial: you are carried to Level 1, Level 4, or back to a town in Level 94.

**One-way, the places no ring reaches**
- Level 1, a red steel EXIT door where no door should be, in a solid wall of the car park: Level !. It slams behind you.
- Level 2, a tunnel closed by a smooth new concrete wall with a thread of red light at its foot: walk into it, Level !.
- Level 37, a dry corridor lit red, ending in a red EXIT door: Level !.
- Level !, the real exit, at a dead end with no turn either side: Level 1, Level 4 or The End, fixed for each hall. You come out of a locked red fire door marked NO RE-ENTRY, set into the level you arrive in; it leads nowhere.
- Level !, falling into a hole in the floor of the dark last stretch: Level 8.
- Level 0, touching a TIME 4 FUN =) poster in a room dressed for a party: Level Fun. Hold a lit torch to it instead and it burns away for good.
- Level Fun, touching a reversed, blurred poster: Level 4.
- Level Fun, going overboard from an open deck: Level 7's sea.
- Level Fun, diving to the bottom of a deep ball pit: the ball pit in Level 94's castle.
- Level 4, walking through a lone wooden doorframe standing on the carpet: The End. It is gone behind you.
- The End, a computer whose screen says =): Level Fun.
- The Hub, the open doors: Tunnel 7 to Level 1, Tunnel 10 to Level 11, Tunnel 5 ("178") to the Snackrooms.
- The Hub, any other carved door, with its level's key (used up): that level. The door marked 3999 puts you down beside a STAFF ONLY door. The pink door, carrying something cute: Kitty's House.
- The Hub, falling into a rectangular hole in the road (Far Tunnels): Level 94, out of the sky.
- The Hub, falling from the Tower's balcony: thrown out into the tunnels.
- The Hub, the Keymaster's escort: the door of the key he gave you.
- Level 37, glowing magenta tiles at the bottom of the deepest water, far out: dive to them, Level 3999's violet pools.
- The End, a computer that runs TRUEEND.EXE: Level 3999.
- Level 3999, a cabinet with another place on its marquee, played to the end: that place (Level 4, 5, 6, 7, 9, 10, 11, 37, 94, Level !, Level Fun or Kitty's House).
- Level 3999, a rusted cabinet in a row of machines: walk into it, Level 3999.1.
- Level 3999, the drain at the bottom of a violet pool: Level 37.
- Level 188, opening a blind from inside a room: taken, always to the same place for that window (most often Level 0, 1, 4 or 5; any other level less often, Level 37, 94, The End and Level Fun least).
- Level 188, dropping through the hatch in the wooden deck: Level 37.
- Any level, rarely and far from home: a grey door with a carved circle over it, where there was none a moment ago (it is gone after five minutes): the Hub.

**Taken by Kitty**
- Any threshold (not a thin spot or a way back), crossed with something cute on you: one time in 20 (one in 6 if it is in your hand), Kitty's House instead. Never within two days of last leaving the house.
- Kitty's House, giving Kitty the cute thing you brought: you wake in Level 4, Level 37 or the Snackrooms, the same place every time for your house.

**Good to know**
- A threshold that has become a way back no longer leads where it once would have.
- Three kinds of door are one-way although you walk through them: Level !'s doors slam and lock, the Hub's carved doors and The End's lone doorframe are gone behind you.
- You wake in the last bed you slept in, wherever it is, or at your Level 0 home if you have slept in none. A temporal gear moves where you wake, from any level. Two-way ways that come out in Level 0 (a Level 4 stairwell, a hotel door, a city basement, Level 3999's mini arcade elevator) make good places for a home.
""")

PAGES["entities"] = ("What Lives Here", """
**What lives in the Backrooms**
*Most of what you hear will never touch you. Learn what keeps each thing back.*

**How danger works**
- Every level has a heart and an edge. In the heart you hear things down the hall and glimpse things far off that go when you come near; further out, things follow you at a distance and wait for you to falter; near the edge into the next level, near elevators, stairs, pits and other ways through, and in dens, they hunt. In the deep levels even the heart is not quiet.
- Things come bolder when you stand in the dark, when your [Reality Stability](gamemechanicinfo-temporalstability) is low, when you run, when you make noise (breaking anything open, and above all forcing a door), the longer you have been out without resting (worst after ten in-game hours), the more tired you are and when your water has run dry (see [Rest and Sleep](backrooms-rest)), and during a Reality Shift. After something has hit you, the pressure eases for a minute or so.
- **The setting.** *Backrooms entities* (a world setting under Survival challenges) sets how often things come for you and how hard they hit. **Off** leaves only their sounds. On **Normal**, in the heart of Level 1 a creature turns up about every seven minutes, more often toward the edge. **Very low** is about every twenty minutes and hits half as hard; **Low** about every eleven and hits three quarters as hard; **High** about every four and a half, with more hunters, one more creature about at once and blows 1.3 times as hard; **Very high** about every three, with more again and blows 1.6 times as hard. Each setting is one step busier than in the previous build, so a world saved on Normal sees about 1.6 times the old number of visits. The big moments (a night visit to a sleeping player, a hive wave, the Mangled's fog, the Beast) scale more gently, by the square root of the setting. Deeper levels are busier on every setting.
- **Resting:** a full minute by a lit firepit or burning Firesalt, beside a wanderer, somewhere nothing hostile goes, asleep in a bed, or at home (within 48 blocks of where you wake). See [Home and Expeditions](backrooms-home).
- **Dens:** some places are where something lives. Bones on the floor, a grey papery hive, crosses chalked on the walls round about: inside, it is as dangerous as the edge of the level, and what lives there is what comes. At the heart of every den are two or three sealed boxes nobody has dared take, and often a folded note. A spider nest in Level 8's caves is the exception: cobwebs strung thick through the rock instead of chalk, and nothing at its heart but what the spiders caught.
- Running for a gate runs into whatever waits there: near the edge, hunters are put down on the way you are going.
- **Every level is worse than the last.** Deeper down, everything is quicker (a Hound always outruns you; a Smiler always does, in the dark), hits harder (from Level 6 through one more grade of armour), takes more killing, follows further, comes more often and in bigger packs, and the quiet after a close call is shorter. Running stops being an answer: fire, light, doors, a stare and keeping still are.
- **Classes and placards.** Every level has a class, from 1 to 5, and a gate into a higher class has an M.E.G. placard beside it naming the level and the class. Its second line is a warning: Class 3, THINGS HERE OUTRUN YOU; Class 4, ARMOUR OR DON'T; Class 5, NO UNARMOURED TRAVEL. Crossing into a higher class is said in chat, once a level. Food and Almond Water thin out from Class 3 down.
- **And pays better.** A deep level's boxes, crates and cupboards are fuller, and often hold something extra: medicine and rusty gears, then copper, then bronze and iron, very rarely a temporal gear. What you kill there carries a bounty of rusty gears, the wanderers' coin; a Skin-Stealer drops the belongings of whoever it wore.
- **Nothing chases for ever.** A hunter that has not drawn blood for twenty seconds or so (longer, deeper down) gives up, falls back to following at a distance, and does not come for you again for a while. Keep out of reach, behind doors and fire, and it tires first.
- **Dodge.** Every blow is wound up first: step back out of reach as it comes and it misses.
- **Armour.** Unarmoured, a catch takes you in about two blows at Level 3 (a Hound hits for 9, a Smiler 8, a Skin-Stealer 13), one or two by Level 8, and a Hound kills in one at Level 9. Sewn leather about halves the blow. Copper or bronze lamellar stands three blows at Level 8, and iron plate stands many (seven to eleven) at Level 9. Armour wears fast against deep hitters: pleather lasts a hit or two against a Level 9 Smiler, sewn leather about six. Pleather, salvaged from car seats and chairs, is armour too, but it turns a blow only a little under half as well as leather. Most hunters outrun a sprint from Level 3 on, so from there armour and fire are the answer, not running. Wretches, Clumps and Dullers are the exceptions: they ambush or reach for you rather than chase, so a sprint is not what they are answered with. The Animations keep their own paces (the wooden ones a little faster than a walk).
- **Fire wards.** A lit firepit, burning [Firesalt](block-backrooms:firesalt) or an angel statue keeps Hounds, Skin-Stealers, rats, moths, Giant Spiders, Partygoers and the wooden and paper Animations out to 8 blocks; a hunter will not close on anyone within 9 blocks of one. Smilers mind light, not fire; Wretches, Dullers, Clumps, clay Animations and Robo-Men mind neither.
- Level 0 is empty but for the Bacteria of its outer reaches, and when the lights fail in a Reality Shift eyes watch even its heart from the dark (in the Lobby they only follow; in the Red Rooms they hunt). A door and a light at home keep them out.
- Nothing hostile enters the Manila Room, a Sanctum (Level 3), the Beverly Room (Level 5), the Snackrooms, Level 3999 where its neon is lit, the lamplit 9th Road and its camps (Level 8), the Poolrooms (Level 37) outside the Reservoir, the Hub, or Kitty's House. Level 94 is safe by day and indoors. Level 4's heart is calm, and nothing hostile lives in Level 10. On the streets of the city (Level 11) nothing attacks unless you start it (a rat in an alley aside). In Level 188, a room with its door shut.
- A closed door behind you stops whatever cannot find a way round it, with one exception: out towards the edge of a level, a Skin-Stealer that cannot reach you knocks, waits, and opens the door. It has hands. A door barred from the inside holds it, and it will not come near a fire.
- Nothing hostile closes in on you while you keep company with a wanderer, and a minute beside one is a rest. Wanderers are few: camps in Level 1, outposts in Level 4, on the 9th Road, in the city, two camps in the Hub, one lobby in four in Level 3999, and the Junkies of The End. They are friendly and never fight back. Talk to one ({rightmouse}): they will tell you what lives where they keep, where the water is, how to sleep safely and where the ways out are, and they trade, for rusty gears. Each deals in what its place has and buys what it lacks. Level 1's crate-pickers sell Almond Water, crackers and beans, candles, Firesalt, bandages, twine and flax and cabbage seeds, for salvage (brackets, wire, glass, cloth, copper bits) and raw hides; they, the outposts, the road, the city and the Hub's doorstep also sell a temporal gear for 6 rusty gears. The M.E.G.'s outposts in Level 4 sell water (the Blue and Green kinds too) and empty bottles, bandages and poultices, Firesalt and seeds, and buy salvage, paper, silver and specimens (Deathmoth quills, moth jelly, Clump sinew). The camps of the 9th Road sell food, rope, torches, a lantern, bronze tools and weapons and sewn linen armour, and buy hides, cloth and spider silk. The B.N.T.G.'s vendors in the city sell candy, the coloured Almond Waters, Firesalt, bronze and chalk, and buy rare things from other levels. The Hub's two camps sell field supplies (Camp Amber, by the Level 1 door, cheap basics for the Lobby's scraps) and buy salvage (the M.E.G.'s also has two Level Keys a week); Level 3999's campers sell the mall's food and prizes and buy tickets; the Junkies sell catalogue cards and keepsakes for Memory Juice and food. Water is never plentiful: a few bottles a week at most. The faceless people wandering about are Facelings, not traders.

**Smilers** (dark places: Level 0's Red Rooms and Reality Shifts only, Levels 1 to 3, 6 (seen, never close), 8, 9, 94 by night, the Reservoir, The End's collapses, Level 188, Level 3999's Blackout)
Eyes and a grin in the dark. They cannot be killed; struck, they withdraw.
- They never step into light of a torch's strength: a torch, a lantern, a fire, a working lamp. A candle is not enough.
- Held in your gaze, while you neither run nor look away, a Smiler freezes, and after a few seconds goes.
- They come for people alone in the dark, and turn to the hunt when you run, or your stability is low. Carry a torch, and do not run.

**Bacteria** (the outer reaches of Level 0)
The Lobby's dark figures: a tall figure of black wires that rises out of black mould, seen far off down a hallway, and sometimes following. It hunts only someone who runs near the way out of the level: run within about twenty blocks of one there and it howls, stands a moment, and gives chase, a little short of a sprint. Keep running and you pull away; stop and walk, or turn back towards the middle of the level, and it gives up and sinks back into the mould, as it does once it has struck you or after half a minute. It can be killed, and carries a good bounty in rusty gears; struck, it fights back. Its patience has an end: corner it, or keep chasing it for ten seconds or so, and it turns on you.

**Hounds** (Level 1's dark sections, Levels 2 to 5 (only the edges of 2, and the odd one in 4), 8 (the edges), 9, 94 by night, Level 3999.1; harmless in the city)
Pale, hairless, on all fours, in packs of two or three. You hear them first. Some are starved, thin and pale; now and then an old one, grey-haired, harder to put down and worth a double bounty.
- Out towards the edge of Level 1, the lights of a section sometimes fail all at once: a Flickering. Hounds hunt you until the lights come back, a minute or two later. It never starts while something else is already about you. Keep a fire, or a door, between you and the dark.
- They will not come within 8 blocks of a lit [firepit](search:firepit) or burning [Firesalt](block-backrooms:firesalt). A fire makes a camp safe.
- They hunt by sight and hearing, and have no nose. Stay out of sight: break the line of sight, stop, and go dark and quiet. It searches where it lost you, then gives up.
- Stare one down: look straight at a Hound that is following you for a few seconds, and it lowers its head, growls and backs off. Then back away at a walk, facing it. Running, or turning your back, brings it on at once, and a Hound always outruns you. Its nerve does not last long: use the seconds.
- A shut door stops a Hound: it has no hands, and it cannot come through. It fits a gap one block wide, but squeezing through anything narrower than two blocks (a service tunnel, a cluttered aisle) slows it to about three fifths of its pace.
- A carried light no longer slows them; it only lets them see you from farther off. A spear, a club and armour see them off; hurt, they run. Each drops meat and a medium hide for leather.

**Facelings** (Levels 1, 3 (the Evolved), 4, 5, 9, the city, the Snackrooms; their children in 5, 9, the city and the Snackrooms)
People with no faces, going about nothing; seldom met, except in the city. Their blank faces turn to follow you.
- Greet one ({rightmouse}): it waves, then turns and points the way to the nearest gate out of the level, as far as it knows, and nods. You are told which way it pointed and roughly how far. One that knows of no gate shrugs; a child only waves.
- Harmless unless you hurt one, and then every grown Faceling near turns on you together for a minute and a half, even where the level is safe. The exception is Level 3, where every one is an Evolved, with a half-formed face: hostile, and it does not greet.
- The children come to look at you and run if you rush them. When they hurry away, Hounds are near.

**Deathmoths** (the females in Levels 1, 2, 5 and 9, mostly towards the edges and in hives; the males in Levels 5 and 94)
Moths the size of a hand span, drawn to open flame. They circle a torch; near the edges of a level the females bite whoever carries it.
- A candle never gets you bitten, a closed [lantern](search:lantern) draws none; a torch draws them most. Smoke from a fire scatters them. A hive is a den with resin hearts: breaking one answers with every female near, and waves for a minute after. Leave it be.
- They settle on floors and tables to rest, the males (Levels 5 and 94) by puddles and bodies to drink. Leave a settled female be: come at her, or hurt one, and she rears up and calls every female near onto you, flame or no flame.

**Skin-Stealers** (Levels 1, 3, 5, 9, 94 by night, 188; lairs)
Large, pale yellow and slow. They cough and call out from out of sight in a voice that is nearly human. Strong, and from Level 3 they outrun a sprint like the other hunters.
- A fed one (it has just killed) keeps to itself, ambling and muttering, but turns on anyone who comes within five blocks until they are well clear. A hungry one stalks you, and out towards the edge soon comes for you.
- A shut door only delays it: it knocks, waits and opens it, though a door barred from the inside holds. A fire keeps it off. Keep your distance and keep a fire. One drops the hide and belongings of whoever it wore.

**Wretches** (the outer parts of Levels 1, 2, 3, 5 and 9; packs of up to three in the dark of Level 8; the city's subway)
Wanderers worn down to nothing by hunger, thirst and sleeplessness, still dressed near the top and all but gone deep down. They gurgle while they follow you and snarl before they charge; the bite is quick but they are frail, and they drop one or two things they carried when they were still wanderers. They come three times as readily for anyone down to the last quarter of their hunger bar: keep fed, and fight them one at a time. In Level 8 they share the dark with the spiders; the lamps of the 9th Road keep them off.

**Giant Spiders** (Level 8's dark off the 9th Road, and its spider nests)
As long as you are and low on its legs, waiting in the dark where its eyes catch your light; you hear its mouthparts clicking before you see it. Come within a few steps of it (fewer if you creep), run or make a racket within earshot, or strike it, and it rears with a hiss, then runs you down faster than a sprint. Its bite is venomous and burns on for a few seconds.
- It is territorial: run the moment it rears, away from where it waited, and it lets you go once you are well clear of its ground. It will not follow into water (spiders can't swim), up to a fire, or onto the road.
- Cobwebs slow you to a crawl and not it: keep out of them, or burn them. In worlds made from now on, whole stretches of cave well off the road are strung with them round a nest, where the spiders are what comes.
- Noise carries to the whole nest: a bang, a block broken, a fight or a forced door within two dozen blocks of its heart wakes every spider of it and sends them after you, and the dark puts down one or two more if there are few. Be quiet in a nest, or do not go.
- It climbs the walls. It mends while it waits; badly hurt, it flees. It carries a good bounty in rusty gears, and a little raw meat ("extra protein", and only worth eating cooked).

**Dullers** (Levels 1, 3, 4, 8, the city's subway)
Tall and grey, and quick. They reach through walls at people passing close on the other side, then run. Plaster puffs out of the wall where the hand comes through.
- Scraping or dragging inside the walls means one is near: walk down the middle of corridors.
- One grab in four takes something from your hotbar instead. It lies on the floor wherever the Duller went: in the room on the other side, if you can find it.
- [Almond Water](item-backrooms:almondwater) keeps them off for five minutes after a drink, and they will not reach for anyone near a fountain or seep of it.
- Faced, they flee.

**Death Rats** (Levels 1, 2, 5, 8, 9, the city's alleys; harmless by day in Level 94)
Rats, in packs, with short horns whose tips glow faintly red: two red points under a shelf in the dark. Hairless in Level 2's heat. They nip at your legs but keep clear of a carried torch or lantern (a candle will not do) and of fire. Food, if you can catch one.
- Rarely, near the edges of Level 2, the Screaming: the lights fail, something screams close by, and a pack of Death Rats goes past at a run after whatever it is. Keep out of their way until the lights come back.

**Clumps** (Levels 1, 2 and 3)
A bundle of limbs that buries itself where it waits: all you see is an arm sticking up out of the floor, a finger twitching now and then. Come within a few steps and the floor gives it up; it grabs and drags at whoever is in reach, then crawls away after a grab or two.
- It hunts by ear: run near one, or make a real noise (forcing a door, breaking several things), and it crawls after you. Go quietly and it buries itself again. Struck, it leaves.
- Where there is room, walk round. In a narrow tunnel there is none: go back, or take the grab and be quick.

**The Thing** (deep in Level 7)
Something vast circles divers out at the edge of sight. Stay more than twenty blocks down for long with your stability failing, or go below fifty-five, and it strikes, once, hard, and leaves. It cannot be fought: surface, or come up for air under the roof of a sunken room, where it only waits. A lit lantern or oil lamp held under water within a dozen blocks of it as it rushes shows it what it is rushing at: it breaks off and circles for twenty seconds. A torch goes out in the water.

**The Mangled** (the Suburbs, rarely; far likelier during a Reality Shift)
There is only one. It comes with its own weather: over most of a minute the air turns cold, a grey fog rolls in, and voices start calling out of it, someone saying hello, someone hurt. Then a black pillar walks out of the fog, slower than a walking man: a mass of human faces held high above the roofs on legs like trees. Its reach is the danger, not its pace.
- It cannot be killed. Striking it only keeps it longer.
- Its tendrils take whoever they reach up into the dark and let go. Get indoors: it needs a clear line to you, and walls stop it.
- It leaves after three minutes or so, and the fog lifts.

**The Beast of Level 5** (the Terror Hotel, rarely; above all in its boiler halls; and anywhere, for whoever owes him)
There is only one, and he chooses you. The hotel's music stops round you, a drum beats somewhere far off, something whispers, metal scrapes closer through the pipes; once, a gentleman watches you from the edge of your sight and is gone when you turn. Leave the hotel, or reach the Beverly Room, and he lets you be. Otherwise, after most of a minute, he steps out of a column of flame in a flash of violet light: an octopus's head, two tentacles for a second pair of arms, steel claws, a black fur suit. He offers a deal.
- **Shake his hand** ({rightmouse} him): you are healed, fed and steady again, and in three days he comes to collect, wherever you are (the Hub excepted). Die to him then and the debt is paid; get away and he comes again a day later.
- **Hold his gaze:** stand your ground and look him in the eye for five seconds, not running. He is startled as nobody startles him, stands frozen, and is gone. It frees you from a debt too.
- **Refuse him** (strike him, walk away, or let the offer lapse) and his suit opens into moth wings: half as tall again, blades for claws, a little short of a sprint, and two of his blows will nearly kill you. A hunt that draws no blood for twenty seconds is given up, and safe places turn him away. Brought down, he dissolves and leaves Level 5's [Level Key](item-backrooms:hub-key-l5); not for long.

**The Striders of the Neighborhood Watch** (the Suburbs' streets, out from the middle of the level, never near the wall into Level 10)
A bloodshot eyeball the size of a man, carried three blocks up on six long legs, walking the streets and yards. It has no ears and no nose: it finds you by sight, and by touch close up.
- The other things of the dark fear it: Hounds, Smilers, Skin-Stealers and Deathmoths within two dozen blocks of one turn tail. That is no help to you, only to them.
- In the dark it sees you only within a dozen blocks; carrying a torch or lantern, standing under a working street lamp, in a lit room or by a fire, it sees you from forty. Crouching shrinks both. Put the light away on the streets.
- Its eye glows faintly: you see it before it sees you. When the eye turns toward you, it is making you out. Get out of its sight, and do not meet its eye: that makes it sure of you faster.
- Once sure, it stares, and comes, faster than you run. It chases only what it sees: break its line of sight (round a house, behind a hedge, through a door) and it goes to where it last saw you and searches. It may walk off and wait a little way away, watching: give it time.
- It is too tall for any door. Indoors you are safe from it, but it looks in through the windows and taps on the glass, and being watched wears on your stability: keep away from the windows until it goes.
- It can be killed, and it is worth a good bounty, but it hits hard and knocks you flat. Arrows and thrown spears hurt it twice as much as blows do.

**The Watcher** (the Suburbs, above the streets and houses, rarely)
The Strider's floating form: a gigantic eye that levitates, silent, a few blocks up. Seen in the open within twelve blocks you have two seconds' warning, the eye turning on you and a tone rising, and then the beam turns you to dust, whatever you wear.
- Break its line of sight in those two seconds: round a house, behind a wall, through a door. The beam needs open air, so from indoors it can only look in at the windows; it is too large to follow you in.
- Nothing hurts or moves it. Lose it and it searches where you were for ten seconds.

**Animations** (Level 94, by night)
Puppets, clay and wooden figures and paper cut-outs that move a frame at a time, and hunt anything that does not look animated. Very strong, not clever: the clay ones are slower than a walk and smother, the wooden ones club and knock you about, the paper ones come in a crowd and are frail. The wooden and paper ones fear fire. They never come indoors (a porch is not indoors), and at dawn they are gone. Stand quite still for a few seconds and they take you for a doll. Whoever carries a shard of the King's crown is one of their own. Worst in the towns, on the roads, and near the glass mountain.

**Robo-Men** (the castle in Level 94)
Tin wind-up toys. Touch, use or break anything in the castle above the mountain's foot and you will hear a key turning: they come, for a minute and a half, slow but hard-hitting.

**The King** (the throne room of the castle in Level 94)
A stone statue at the head of a long table. Only one of the throne room's four doors opens, a different one each day. Sit in the second chair and he raises your nightmare: the thing that has killed you most often (a Hound if nothing has yet), tougher than its kind, and **it can only do what you think it can:** with your [Reality Stability](gamemechanicinfo-temporalstability) full it hits at a quarter of its strength; with it gone, twice as hard. Drink Almond Water before you sit down. Destroy it and the King bursts into light, gives you a shard of his crown (the first time), and carries you out of Level 94.

**The horde** (Level !)
Hounds, Skin-Stealers, Smilers, rats and moths, all running at four fifths of your sprint (a little slower just after they burst out). It can't be fought off (kill one and another takes its place) and it can't be outrun for long by anyone who stops: within a block and a half it pins you and tears you apart. It falls back out of sight while you keep running, and it waits at the Safe Zone's door for three hours before it comes in. Now and then a vent drops a Hound behind you, nearly as fast as you for a few seconds, or a dented door bursts and something slower comes out; neither follows you into the Safe Zone.

**Partygoers** (Level Fun; a few in Level 3999.1)
Tall, yellow, a smile carved into the face; always in packs, round the head table of a party with music. They are slow and nearsighted (about 12 blocks in light, 7 in dim light, 4 in the dark; less if you sneak) and hear little but running, fighting and pops. One that sees you stares for a second, then its pack joins in. Run: they are slower than a sprint, never open doors, and keep away from fire ([Firesalt](block-backrooms:firesalt), a firepit).
- If one **latches on**, you have **30 seconds** to use a poultice or a bandage, or the bite becomes **Party Fever**: hungrier, less steady, and it fades only once you are out of Level Fun (Almond Water helps). Three bites' worth and you join the party: you die, and a new Partygoer with a red balloon stands guard over what you dropped.
- Below half health its chest opens: it stops biting and claws instead, and fire burns it badly.
- **Disguise:** a party hat on your head and a red balloon in your hand, and a Partygoer more than three blocks off takes you for one of its own, as long as you don't run or strike.
- One that has seen you may speak in a voice you know. Don't answer.
- A killed guest stays dead for a day; then the party has a new one.

**Carnivorous Balloons** (Level Fun's dark corridors)
A balloon floating at chest height, tied to nothing, on a curly ribbon. Walk into one and it stings and holds you nearly still for 3 seconds. Pop it and it lets out a gas that burns anyone close; what is left is onions, and the bang brings the guests. Poke it from out of reach, or walk round.

**The Junkies** (The End)
Wanderers who stayed, in the Home fake realities. Harmless, and nothing hostile comes near them, but they trade only with someone carrying Memory Juice.

**Kitty** (Level 974)
A figure three metres tall, faceless, matt black, its arms and legs ending in points. You will rarely see it move: it is simply somewhere else when you look again, in a doorway, at the end of the hall, by your bed while you sleep, behind you. It cannot be hurt and never harms anyone, but striking it, or breaking its things, offends it for a day. Hold out what you brought and call it, and it comes for its gift.

**The Keymaster** (the Hub's Tower)
A tall cloaked figure with a ring of keys. He cannot be harmed and does not harm. He comes to anyone in the Tower carrying a Level Key, or who reaches the meeting hall at the top. {rightmouse} him to see the keys of levels you have been to; {shift} + {rightmouse} takes the one shown, once. Then he shows you to its door, and the Tower will not let you in again. Break anything of his and he throws you out with nothing.

**Arcade Attendants** (Level 3999)
Faceless, polite, made of plastic, in plum or navy uniforms: behind the prize counters, the food stalls and the lobby desks. They cannot be hurt and will not hurt you. {rightmouse} one and it points the way to a lobby.

**The Windows** (Level 188)
Someone standing in a lit window, beckoning. Within six blocks you hear whispering; stay within two for a second and a long black arm comes out of the glass, holds you, hurts you and drags you toward it. **Hit the arm twice, or get three and a half blocks away**, before it has held you six seconds at the glass: then you are pulled through, and that is death. About one room in sixteen has one, and they move to other windows every night.

**Peripherals** (Level 188)
Shapes at the very edge of your sight in the corridors and the courtyard, gone when you turn toward them. They do nothing but unsettle you (a little stability each time).

**The wild and the tame.** Level 7's sea has fish. Level 9's night has hares, foxes and raccoons, as in any world. Level 10's paddocks hold livestock to keep (see [animal husbandry](gamemechanicinfo-animalhusbandry)). Nothing of the rust world lives here: Level 8's dark belongs to the Wretches and the spiders.

**Level 37** is empty, as far as anyone knows: nothing hostile goes there, but in the dark of the Sanguine Reservoir. **The Hub and Kitty's House** are safe: nothing hostile goes there. **Level 3999** is safe where the neon is lit; its Blackout is not. **The End** is empty but for Smilers glimpsed in the dark of its collapsed departments.

**What keeps you safe, as you go deeper**
- Level 0: light, and a steady mind (Almond Water).
- Level 1: fire, doors, a spear or a club, improvised armour.
- Level 3: [Firesalt](block-backrooms:firesalt), found in the coal by generators and boilers. Set it down and light it: for half a day nothing hostile comes near. Later you can make it: salt + powdered sulfur = 2 Firesalt.
- Level 4: a lantern, which draws no moths.
- Level 5 on: leather armour from Hound and Skin-Stealer hides; then copper and bronze from Level 8.
""")


# ====================================================================================================================
# Prefaces for the vanilla guides: one short paragraph at the top of each, saying how it goes in the Backrooms.
# The vanilla text follows unchanged. Keyed by the suffix GuideSystem.Bridged maps each page code to.
# ====================================================================================================================

BRIDGES["knapping"] = """
**In the Backrooms:** there are no stones lying about in the Lobby, and [flint](item-flint) is a Level 1 find: Level 1's crates hold it and its broken concrete has flint, chert, andesite and granite lying loose (a Lobby supply box holds one only about one time in twenty); Level 8's cave floors have stones too, and the ground under every floor holds flint as any world does. Knapping itself is unchanged. Until you have two flints, a [glass shiv](item-backrooms:glassshiv) or an [improvised scraper](item-backrooms:scraper) is your knife, and for wallpaper and carpet it stays the better one: see [Salvage](backrooms-salvage).
"""

BRIDGES["clayforming"] = """
**In the Backrooms:** clay is the first thing you have to travel for. The nearest is the flooded tunnel under Level 3 (down a manhole; cold, and it drains your stability badly), then the beds of Level 10's ponds, rare pockets in Level 8's rock, and above all Level 94, whose hills are modelling clay under a skin of turf (about 3 clay a block, blue clay a little way down). The potted plants of Levels 4 and 5 give a slow trickle without the trip: their pottery shards, pounded to grit with a stone and worked into soil, make about one clay for every four plants (see [Salvage](backrooms-salvage)). Clay forming itself is unchanged. Fire clay, for fire bricks, the bloomery and the kilns, lies only in Level 94, in pale seams three to seven blocks under the turf: see the [Progression Guide](craftinginfo-progressionguide).
"""

BRIDGES["mealcooking"] = """
**In the Backrooms:** the pot and the bowls want clay (see above), and the firepit wants firewood, which is scarce in the first levels (rotten wood, planks, Level 7's driftwood, then the real trees of Levels 9 to 11 and 94). Water for a bucket is in the flooded rooms of Level 0, the tunnel under Level 3, the Poolrooms, Level 7's sea, Level 10's ponds and the city's fountains. Ingredients: fridges, pantries and crates give vegetables, fruit, cheese and flour; Level 7 fish; Level 9 game and berries; Level 10 crops, eggs, milk and honey. Cooking itself is unchanged.
"""

BRIDGES["charcoalburning"] = """
**In the Backrooms:** charcoal is also found ready-made in Level 1's crates and Level 9's barbecue grills, and coal lies heaped by Level 3's generators and in Level 5's boiler halls, so you may not need a pit at all. If you do, nothing the Backrooms are built of burns, so any wall or floor of the building will seal a pit; but digging one into a floor takes a copper pickaxe (concrete and floor slabs are as hard as rock), unless you dig into the soil of Levels 9 or 10 or the clay of Level 94, or wall a corner with rubble masonry. The firewood is the hard part: see the [Progression Guide](craftinginfo-progressionguide).
"""

BRIDGES["farming"] = """
**In the Backrooms:** it never rains, so moisture comes only from water within 3 blocks of the farmland or a watering can. Crops grow without sunlight under a *working* ceiling light, at about six tenths of the daylight pace (nothing grows under a dead one, and little in the cold of a blackout zone), so you can farm at home in the Lobby. Soil comes from potted plants (Levels 4 and 5), the lawns of Levels 9, 10 and 11, and Level 94's turf; the ground under the floors has none. Level 10's old fields are exhausted and never regrow: harvest them, then plant in fresh soil. Seeds: seed packets (tool shelves in Level 9's garages and sheds, now and then a supply box), seed sacks (Level 9's sheds, Level 10's barns), wanderers (flax, cabbage), and the harvest itself. See [Home and Expeditions](backrooms-home).
"""

BRIDGES["foodpreservation"] = """
**In the Backrooms:** there are no seasons, so spoilage runs at the pace of the room you are in, all year. Any fully enclosed room counts as a cellar (concrete walls cool it; drywall does not), and Level 0's blackout zones are cold and damp (10 °C), so a chest there keeps food more than twice as long as the Lobby proper. Salt for pickling comes from kitchen cupboards or Level 8's halite ground in a quern; crocks and vessels from clay; wax from Level 10's skeps. See [Food and Water](backrooms-food).
"""

BRIDGES["animalhusbandry"] = """
**In the Backrooms:** livestock lives only in Level 10's paddocks: hens and a rooster, pigs, mouflon sheep and goats, a few at a time, with populated bee skeps by the farmhouses. Hares are in Level 9's gardens. Fences, troughs and henboxes are built from planks and sticks as usual; milk comes from the ewes and nannies. Nothing hostile closes in on the fields of Level 10, so a farm there is possible, but you still only wake up in Level 0.
"""

BRIDGES["panning"] = """
**In the Backrooms:** there is almost nothing to pan. No sand or gravel lies under the floors; the only gravel is the surface of Level 8's road and the park paths of the city, and the muddy gravel of the pond beds will not pan. The one place with sand to pan is the floor of Level 7's sea (worlds made from 0.514.0), and a few of Level 10's ponds have a little. Copper comes far more easily from salvage: see the [Progression Guide](craftinginfo-progressionguide).
"""

BRIDGES["smelting"] = """
**In the Backrooms:** the crucible and moulds need clay (Level 3's tunnel, Level 10's ponds, Level 94), and the heat needs coal (heaped by Level 3's generators and in Level 5's boiler halls) or charcoal (crates, grills, or your own pit). Copper comes as bits from cable spools, machine cabinets, stacked pipes, fans and wrecked cars rather than from ore: 20 metal bits = 1 ingot, and 10 scrap wire or 10 circuit boards melt to a copper ingot too. Ore proper is in Level 8, and nowhere else: the ground under the other floors has none. Tongs are made as usual. Iron ore needs a bloomery, and the bloomery needs fire bricks: the fire clay for them is in Level 94, and nowhere else, and the mortar to lay them wants sand: it lies on the floor of Level 7's sea, with a little in some of Level 10's ponds (worlds made from 0.514.0).
"""

BRIDGES["smithing"] = """
**In the Backrooms:** a copper hammer sometimes turns up in a toolbox (Level 1, garages, hardware stores), or cast one; the anvil takes 9 ingots of copper or bronze; the forge is built as usual. Smithing itself is unchanged. Bronze comes from Level 8's tin, zinc, bismuth and gold with copper from salvage; iron needs a bloomery, whose fire clay comes only from Level 94.
"""

BRIDGES["prospecting"] = """
**In the Backrooms:** there is no ore to prospect for under the floors. The ground there is rock, the strata of an ordinary world with the Backrooms' floor at its sea level, but its ore deposits are laid only in Level 8's rock, so the pick, which reads deposits in density mode as usual (node search is off), finds nothing under the other levels. Level 8's ore is laid open on the cave walls and floors and needs no prospecting. Do not dig under Level 10 (the worms), and mind that Level 94's ground is clay, then rock.
"""

BRIDGES["armor"] = """
**In the Backrooms:** improvised armour is sticks and twine as usual; leather comes from the hides of Hounds, Skin-Stealers, rats and Level 9's wildlife; wanderers sell sewn linen armour; iron and steel wait on a bloomery, whose fire clay is in Level 94 and nowhere else. From Level 6 down, what hunts you hits through one more grade of armour than it would nearer the Lobby, and in Level ! armour's weight slows you with a horde at your back. A party hat and a red balloon are the only armour that works in Level Fun.
"""

BRIDGES["mechanicalpower"] = """
**In the Backrooms:** windmills turn only under an open sky, so only on Levels 9, 10, 11 and 94. There is no flowing water anywhere for a water wheel. Level 10's barns have a quern already, and Level 8's hard rock makes another. The helve hammer, pulverizer and grinding wheel work as usual once you have a windmill up on the open-sky levels.
"""

BRIDGES["steelmaking"] = """
**In the Backrooms:** refractory bricks need fire clay, and the only fire clay in the Backrooms is in the seams under Level 94's hills, three to seven blocks down. A cementation furnace wants some 65 bricks, so plan several trips with bags; the iron and the coal come from Level 8. The bricks are laid in mortar (slaked lime and sand): sand lies thick on the floor of Level 7's sea, so plan a dive, and a few of Level 10's ponds have a little on the bed (worlds made from 0.514.0). Everything else is as usual.
"""

BRIDGES["cokeoven"] = """
**In the Backrooms:** the coke oven is built of refractory bricks, whose fire clay comes only from the seams under Level 94's hills and whose mortar wants sand, from the floor of Level 7's sea (or, a little, some of Level 10's ponds; worlds made from 0.514.0). Coal itself is plentiful: Level 3's generators, Level 5's boilers and Level 8's seams.
"""

BRIDGES["weather"] = """
**In the Backrooms:** there is no weather. It never rains or snows anywhere, there are no seasons, and each level keeps its own temperature all year (see [Food and Water](backrooms-food)). The open-sky levels have wind for windmills. The weather here is the Reality Shift: see [Reality Stability](gamemechanicinfo-temporalstability).
"""

BRIDGES["stonelayers"] = """
**In the Backrooms:** these rules hold for the ground under the floors (8 blocks of concrete down), whose strata are an ordinary world's, though it carries no ore outside Level 8 (see prospecting). Level 8's caves are the Backrooms' own rock, with limestone, chalk and halite among its strata and its ore laid open on the walls, and the ground proper begins far below it.
"""

BRIDGES["cheese"] = """
**In the Backrooms:** milk comes from the ewes and nannies of Level 10's paddocks, pickled vegetables from Level 10's crops, salt from Level 8's halite or a kitchen cupboard, linen from hotel beds, and wax from Level 10's skeps. Cheese itself is made as usual. Ready-made cheese sits in the fridges of Levels 4 and 9, the city and Level 94.
"""

BRIDGES["quenching"] = """
**In the Backrooms:** quenching works as usual wherever there is water (the flooded rooms of Level 0, the tunnel under Level 3, the Poolrooms, the ponds of Level 10). Copper and bronze take no quench, so this page matters once you have a bloomery (its fire clay is in Level 94) and iron from Level 8.
"""

BRIDGES["fruittrees"] = """
**In the Backrooms:** there are no fruit trees. Fruit comes from fridges (Levels 4 and 9, the city, Level 94's iceboxes) and from the berry bushes gone wild in Level 9's gardens and along Level 10's fields. The trees of Levels 9, 10, 11 and 94 are oak, birch and maple, for wood.
"""

BRIDGES["alcohol"] = """
**In the Backrooms:** barrels want boards (a saw, so copper); fruit comes from fridges and Level 9's berries, honey from Level 10's skeps, and flour from Level 10's grain ground in the barns' quern. The rest is as usual.
"""

BRIDGES["dyemaking"] = """
**In the Backrooms:** flowers grow on the open-sky levels (9, 10, 11 and 94), and a pulverizer needs a windmill, which turns only there. Cloth itself is plentiful: sofas, chairs, suitcases and bedrolls give it, and so do Level 188's wardrobes. Clothes ready-made are in Level 5's wardrobes, Level 9's dressers and the city's stores.
"""

BRIDGES["groundstorage"] = """
**In the Backrooms:** ground storage works as usual, and matters more, because a chest needs 8 planks from Level 1 and a basket needs Level 10's cattails. Lean your tools on the wall of your home in the Lobby until then.
"""

BRIDGES["leathermaking"] = """
**In the Backrooms:** hides come from Death Rats (small), Hounds (medium), Skin-Stealers (large), Level 9's hares, foxes and raccoons, and Level 10's livestock. Limewater needs lime: Level 8's limestone and chalk, or the seashells of Level 7's islands, ground in a quern. Tannin needs oak, and about half the trees of Levels 9, 10, 11 and 94 are oak. Barrels need a saw. The steps are as usual.
"""

BRIDGES["greenhouse"] = """
**In the Backrooms:** a greenhouse needs sky, so only the open-sky levels (9, 10, 11, 94) could hold one, and the glass is the work: glass shards from the Backrooms' lights are not glass blocks, so glass is made in a bloomery (fire clay from Level 94) from Level 8's quartz. Under a ceiling, a working light grows crops without any greenhouse: see [farming](gamemechanicinfo-farming).
"""

BRIDGES["beehivekiln"] = """
**In the Backrooms:** the beehive kiln is built of refractory or fire bricks, whose fire clay comes only from the seams under Level 94's hills. The pit kiln fires everything you need until then.
"""

BRIDGES["shipbuilding"] = """
**In the Backrooms:** the only sea is Level 7's, under a concrete ceiling (in worlds made from 0.514.0 a high one, thirty-six blocks over the water; before, only a few blocks above it), and nobody has yet found whether a sailboat fits under it. The raft from a waterlogged crate is the Backrooms' boat. Logs and boards exist (the trees of Levels 9 to 11 and 94, a saw), and rope comes from crates and toolboxes.
"""

BRIDGES["mountableanimals"] = """
**In the Backrooms:** there are no elk and no mounts. Nobody rides here; the moving walkways of Level 3999 are the nearest thing.
"""

BRIDGES["fishing"] = """
**In the Backrooms:** the fish are in Level 7's sea, and they are the sea's own kinds. Fishing poles turn up in the waterlogged crates on its bottom and in lost backpacks, or are made as usual. Worms for bait come from a worm grunter in the soil of Levels 9 or 10 (or Level 94's turf); meat and small fish work as bait too.
"""


# ====================================================================================================================
# The tutorial: Backrooms: First Steps (src/Tutorial/BackroomsTutorial.cs). One entry per step, in order.
# {0}.. are filled by the game: for a key step the keys named, for a collect or craft step the number still to get.
# <itemstack type="item">code</itemstack> shows the item, as the vanilla tutorial does.
# ====================================================================================================================

TUTORIAL = [
    # 1 move
    "Use {0} {1} {2} {3} to move around and your mouse to look around. {4} jumps and {5} sneaks. Hold {6} and {0} to sprint, but not here: in the Backrooms, running is heard.",
    # 2 journal
    "There is a wanderer's note in your pocket. With it in your hand, <icon>rightmousebutton</icon> to read it: it marks the nearest unopened supply box on your map. Every note you read is kept in your journal; press {0} to open it.",
    # 3 boxes
    "Two <itemstack type=\"block\">backrooms:supplybox</itemstack> supply boxes stand beside you. Break one (hold <icon>leftmousebutton</icon>) and pick up what falls out: {0} more thing(s) to collect. A box with its lid taped down holds food; a torn one holds scraps.",
    # 4 shard
    "Break a dead <itemstack type=\"block\">backrooms:fluorescentlight-off</itemstack> light fixture out of the ceiling for {0} <itemstack type=\"item\">backrooms:glassshard</itemstack> <a href=\"handbook://item-backrooms:glassshard\">glass shard</a>. Bare hands will do.",
    # 5 strip
    "With the shard in your hand, <icon>rightmousebutton</icon> the yellow wallpaper to cut {0} <itemstack type=\"item\">backrooms:wallpaperstrip</itemstack> <a href=\"handbook://item-backrooms:wallpaperstrip\">wallpaper strip</a>. A bare shard snaps one time in four, so cut carefully.",
    # 6 fibre
    "Now <icon>rightmousebutton</icon> the carpet for {0} <itemstack type=\"item\">backrooms:carpetfibre</itemstack> <a href=\"handbook://item-backrooms:carpetfibre\">carpet fibre</a>. Dry carpet cuts; the soaked carpet of the dark zones does not.",
    # 7 shiv
    "Craft a <itemstack type=\"item\">backrooms:glassshiv</itemstack> <a href=\"handbook://item-backrooms:glassshiv\">glass shiv</a> in your crafting grid (open your inventory with <hk>inventorydialog</hk>): a glass shard, a wallpaper strip and a carpet fibre. It is a knife, and it does not snap.",
    # 8 fibres
    "Bags next. With the shiv, cut {0} more <itemstack type=\"item\">backrooms:carpetfibre</itemstack> carpet fibres from the carpet. It cuts cleanly: two fibres a block.",
    # 9 twine
    "Craft <itemstack type=\"item\">flaxtwine</itemstack> <a href=\"handbook://item-flaxtwine\">twine</a> from 3 carpet fibres.",
    # 10 bag
    "Craft a <itemstack type=\"item\">backrooms:carpetbag</itemstack> <a href=\"handbook://item-backrooms:carpetbag\">carpet bag</a>: 5 carpet fibres and the twine. Put it in one of the 4 bag slots on the right of your inventory. You will want four of them, which is 32 carpet fibres.",
    # 11 scraper
    "Craft an <itemstack type=\"item\">backrooms:scraper</itemstack> <a href=\"handbook://item-backrooms:scraper\">improvised scraper</a>: a <itemstack type=\"item\">backrooms:metalbracket</itemstack> metal bracket, a wallpaper strip and 2 carpet fibres. Brackets fall now and then from dead lights, ceiling tiles and supply boxes. Like the shiv it cuts two strips or fibres a block, and it lasts three times as long.",
    # 12 tinder
    "Tinder: craft {0} <itemstack type=\"item\">drygrass</itemstack> <a href=\"handbook://item-drygrass\">dry grass</a> from 2 wallpaper strips. The Lobby has almost no firewood, and no flint either: dry grass and sticks are what fire starts with here.",
    # 13 torch
    "Craft a <itemstack type=\"block\">torch-basic-extinct-up</itemstack> torch: 2 dry grass above a stick. Sticks come from supply boxes, from rotten wood out of broken ceiling tiles, and now and then from a broken wall. Light it at a fire; a lit torch keeps things back where a candle only lights the dark.",
    # 14 map
    "Open the map with {0}. It shows only what you have seen, and remembers it. 'Where I woke up' is your home: you will wake there whenever you die, until you sleep in a bed somewhere else.",
    # 15 handbook
    "That is the Lobby's whole toolkit. Stone tools wait for Level 1: <a href=\"handbook://item-flint\">flint</a> is rare in the Lobby's boxes, but Level 1's crates hold it and its concrete floors have flint and stones lying loose; then <a href=\"handbook://craftinginfo-knapping\">knap</a> a knife and an axe. Fire, food, the way to Level 1, the gear by your health, the water and Rest bars (you will need to drink and sleep) and what lives in the dark are all in the handbook: press {0} and read the <a href=\"handbook://craftinginfo-starterguide\">Starter Guide</a>. Good luck, and don't run.",
]

# Steps 2 and 14 where the world's Backrooms map setting is not the default (BackroomsTutorial.JournalStep, MapStep):
# keyed by the lang suffix. Step 2's stands for both No waypoints and None
TUTORIAL_MAP = {
    "2-nowaypoints": "There is a wanderer's note in your pocket. With it in your hand, <icon>rightmousebutton</icon> to read it: it tells you which way the nearest unopened supply box lies, and how many paces. Every note you read is kept in your journal, directions and all; press {0} to open it.",
    "14-nowaypoints": "Open the map with {0}. It shows only what you have seen, and remembers it, but in this world it marks nothing for you: <icon>rightmousebutton</icon> on it to add waypoints of your own. Where you woke up is your home: you will wake there whenever you die, until you sleep in a bed somewhere else.",
    "14-nomap": "There is no map in this world: you find your way or you don't. Where you woke up is your home: you will wake there whenever you die, until you sleep in a bed somewhere else, so learn the way back to it. A note gives a direction and a number of paces, and your journal ({0}) keeps them. Chalk arrows on the walls point to the ways through; leave your own with <itemstack type=\"item\">backrooms:chalk</itemstack> <a href=\"handbook://item-backrooms:chalk\">surveyor's chalk</a>, from crumbled ceiling tiles.",
}

TUTORIAL_STARTED = "Backrooms: First Steps is on screen. Hide it with .tutorial hud; find it again under Tutorials in the handbook (H)."


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
    for code, text in BRIDGES.items():
        LANG[f"guide-bridge-{code}"] = to_vtml(text)
    for n, text in enumerate(TUTORIAL, 1):
        LANG[f"tutorial-backrooms-{n}"] = text
    for n, text in TUTORIAL_MAP.items():
        LANG[f"tutorial-backrooms-{n}"] = text
    LANG["tutorial-backrooms-started"] = TUTORIAL_STARTED


def check():
    """Every link to one of our own items or blocks must name something that exists, and every page link a page."""
    items = set()
    for kind in ("itemtypes", "blocktypes"):
        for root, _, files in os.walk(os.path.join(ASSETS, kind)):
            for f in files:
                items.add(os.path.splitext(f)[0])
                # (and the type's own code, where its file is named otherwise: hub/key.json is hub-key)
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    m = re.search(r'"code"\s*:\s*"([^"]+)"', fh.read())
                if m:
                    items.add(m.group(1))
    pages = {"backrooms-" + code for code in PAGES} | {
        "craftinginfo-starterguide", "craftinginfo-progressionguide", "gamemechanicinfo-temporalstability",
        "craftinginfo-knapping", "craftinginfo-clayforming", "craftinginfo-mealcooking", "craftinginfo-charcoalburning",
        "gamemechanicinfo-farming", "gamemechanicinfo-foodpreservation", "gamemechanicinfo-animalhusbandry",
        "gamemechanicinfo-panning", "craftinginfo-smelting", "craftinginfo-smithing", "gamemechanicinfo-prospecting",
        "craftinginfo-armor", "gamemechanicinfo-mechanicalpower", "gamemechanicinfo-steelmaking", "craftinginfo-cokeoven",
        "gamemechanicinfo-weather", "gamemechanicinfo-stonelayers", "craftinginfo-cheese", "craftinginfo-quenching",
        "gamemechanicinfo-fruittrees", "craftinginfo-alcohol", "craftinginfo-dyemaking", "gamemechanicinfo-groundstorage",
        "craftinginfo-leathermaking", "gamemechanicinfo-greenhouse", "gamemechanicinfo-beehivekiln",
        "gamemechanicinfo-shipbuilding", "gamemechanicinfo-mountableanimals", "gamemechanicinfo-fishing",
    }
    bad = []
    texts = [(code, text) for code, (_, text) in PAGES.items()] + list(BRIDGES.items())
    texts += [(f"tutorial-{n}", text) for n, text in enumerate(TUTORIAL, 1)]
    texts += [(f"tutorial-{n}", text) for n, text in TUTORIAL_MAP.items()]
    for code, text in texts:
        targets = re.findall(r"\]\(((?:item|block)-backrooms:[^)]+)\)", text)
        targets += re.findall(r'handbook://((?:item|block)-backrooms:[^"]+)', text)
        targets += [f"x-backrooms:{t}" for t in re.findall(r'<itemstack[^>]*>backrooms:([^<]+)</itemstack>', text)]
        for target in targets:
            name = target.split(":", 1)[1]
            # (A variant, like wanderernote-door, is named after its file plus its states)
            if name not in items and not any(name.startswith(item + "-") for item in items):
                bad.append((code, target))
        for target in re.findall(r"\]\(([a-z]+-[a-z]+)\)", text):
            if target not in pages and not target.startswith(("item-", "block-")):
                bad.append((code, target))
    return bad


if __name__ == "__main__":
    LANG.clear()
    fill()
    if "--check" in sys.argv:
        problems = check()
        print("links ok" if not problems else f"BROKEN LINKS: {problems}")
        sys.exit(1 if problems else 0)
    from gen_detail import merge_lang
    merge_lang()
    for code, (title, text) in PAGES.items():
        print(f"{code:12} {len(to_vtml(text)):5} characters  {title}")
    print(f"{len(BRIDGES)} prefaces, {len(TUTORIAL)} tutorial steps")
    problems = check()
    print("links ok" if not problems else f"BROKEN LINKS: {problems}")
