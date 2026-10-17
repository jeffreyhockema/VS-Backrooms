"""Wanderers' notes: every text a note can turn out to say, the order they come in, and the paper they are written on.

A note is blank until it is read. On reading, the server (src/Notes/) resolves it to the next entry due in that
player's sequence (see docs/design/notes-plan.md):

- **common** tracks: the ordered series. "main" (the way from waking to the far levels, read anywhere) and one track
  per level (read in that level). The first three notes anyone reads are main 1-3; then a note alternates between
  main and the level it is read in. A main entry with a gate waits until the reader has been to one of its levels.
- **rare** tracks: folded notes (a rarer paper, from deeper caches, dens, bodies, sealed rooms and the far edges of a
  ring) carry more valuable information, in their own fixed order: first the rare track of the level they are read
  in, then "rare-any", then, if every rare note is read, an ordinary common note.
- **scrap**: flavour, only once the common tracks run dry; after that a note is just its map mark.

Text uses the handbook's light markup (see gen_guide.py): **bold**, *italic*, [text](page) links, blank line =
paragraph. Lang keys: note-<key> (text) and notetitle-<key> (title); journal-track-<id> (chapter titles).

Writes: lang/en.json (in place, only keys this script owns), config/notes.json (tracks, gates, marks; no text),
itemtypes/wanderernote-folded.json, blocktypes/loosenote.json, shapes/block/loosenote.json, the folded note's
texture, and docs/design/notes-catalogue.md (every text, for reading). Adding a level's track (3999, 188) is data only:
add a Track below with its level id and entries, and run this script.

    python tools/gen_notes.py            generate
    python tools/gen_notes.py --check    check only (also run on every generate): keys, gates, marks, lengths, facts
"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw  # noqa: E402

from detail_kit import ground_storable  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
LANG = {}

# Level ids (src/Worldgen/WorldLayout.cs); 61 stands for Level 6.1 (a Snackrooms cell inside Level 6)
POOLROOMS, MOTION, RUN, FUN, END, HUB, L974, L3999, L188, SNACKROOMS = 12, 13, 14, 15, 16, 17, 18, 19, 20, 61
LEVEL_IDS = set(range(0, 12)) | {POOLROOMS, MOTION, RUN, FUN, END, HUB, L974, L3999, L188, SNACKROOMS}

# What an entry may mark besides its paper's own mark (src/Notes/MarkResolver.cs)
MARKS = {"door", "way", "cache", "refuge", "manila", "den", "manhole", "barnwall", "endexit", "hubdoor", "redroom", "party"}

# The recurring writers (for the catalogue only; the signatures are part of each text)
WRITERS = {
    "dez": "Dez, a scavenger: cocky in the Lobby, careful after losing Pell in Level 2, ends up with a stall in the city.",
    "al": "A. Lindqvist, a surveyor: measured, numbered, sure the doors are a system; her fair copies are the folded notes. "
          "Her arc ends with the doors honest and none of them leading out.",
    "meg": "M.E.G. Field Team 9: typed notices and restricted briefings. The team signs with how many are left: six, then fewer.",
    "tom": "Tom, who is not coping: writes every note to his wife Ruth, denies, dies, makes a home, and in the end calls the Lobby home.",
    "nell": "Nell, a grower: grows the first turnip in the Lobby and stays in the fields of Level 10. Calls everyone love.",
    "anon": "One-off hands: whoever was there.",
}


class E:
    def __init__(self, key, title, text, gate=None, mark=None, w="anon"):
        self.key, self.title, self.text, self.gate, self.mark, self.w = key, title, text.strip(), gate or [], mark, w


class Track:
    def __init__(self, id, cls, title, level=None, chapter=None, entries=()):
        self.id, self.cls, self.title, self.level, self.chapter, self.entries = id, cls, title, level, chapter or id, list(entries)


def visited(*levels):
    return list(levels)


TRACKS = []

# ============================== Common: the main series ==============================

TRACKS.append(Track("main", "common", "The Wanderer's Way", entries=[
    E("m01", "Three rules", """
Rule one: don't run. Nobody's coming, and running only brings the things that are. Rule two: break the boxes. Lid
still taped down, there's food and Almond Water in it. Torn open, it's scraps. Rule three: keep any note you find.
They turn up in order. Don't ask me how.
— Dez""", w="dez"),
    E("m02", "A blade", """
You need an edge. Knock a dead light out of the ceiling for glass. A bare shard cuts, but it snaps one time in four.
A shard, a strip of wallpaper and a carpet fibre make a shiv. A metal bracket, a strip and two fibres make a scraper,
and that lasts three times as long. Either one peels clean, two to a cut. Keep it even once you've got flint.
— Dez""", w="dez"),
    E("m03", "Wallpaper and carpet", """
Blade in hand, right-click the yellow wallpaper, then the dry carpet. Strips and fibres. Two strips twist into dry
grass. Three fibres make twine. Five fibres and a twine make a carpet bag, three slots. Make four before you go
anywhere: that's thirty-two fibres, sixteen cuts with a shiv. The floor won't mind.
— Dez""", w="dez"),
    E("m04", "Fire", """
Flint is rare in the boxes here; Level 1's crates and floors have it. With two: sneak, right-click one onto the floor, knap. Knife blade first, then an
axe head, each hafted on a stick. One rotten wood (from the ceiling voids) gives two sticks; two give a firewood. Fire
starter: one dry grass, two sticks. Firepit: dry grass on the floor, four firewood. Expect no wood here. Level 1 has
wood.
— A.L., survey""", w="al"),
    E("m05", "The gear", """
Ruth, there's a little gear by my health that turns. Forward means this place has hold of me. Backward means I'm
slipping, and when it empties it hurts. The dark rooms turn it back, and the red ones worst. A bottle of Almond Water
gives back about a seventh. Every day or so the lights go out everywhere for hours. I stop, light a torch, drink if I
must, and wait in a room I know. I think of you.
— Tom""", w="tom"),
    E("m06", "Home", """
Ruth, I died today. I woke up in the Lobby again with nothing; my things were still lying where I fell. It's always the
Lobby. So I'm making a home. A temporal gear, used on the floor anywhere in this level, moves where you wake. Anywhere
else it won't take. Fifty steps round home counts as rest. I've hung your photo by the door.
— Tom""", w="tom"),
    E("m07", "The wall", """
This level is bounded. The wall at its edge is solid, with a gap every few hundred paces. Worn carpet and missing
ceiling tiles mean you are close. A hallway runs along the inside of the wall: follow it, quietly; that is where they
wait. Chalk arrows point to a gap; chalk crosses mean keep out. The nearest gap I surveyed is marked.
— A.L., survey""", mark="door", w="al"),
    E("m08", "Eyes in the dark", """
M.E.G. FIELD NOTICE. Eyes and a grin in a dark room: a Smiler. It will not enter firelight, and a candle is not fire
enough. Carry a torch (two dry grass and a stick, lit at a fire). Hold its gaze, do not run, do not look away, and it
stops. Running, breaking things open and long stays out all draw them. A minute beside a fire counts as rest.
— Field Team 9 (six of us)""", w="meg"),
    E("m09", "The first trip out", """
First trip out is Level 1: a concrete car park in grey fog. Its wooden crates hold food, Almond Water, planks, twine and
charcoal, and flint and stones lie loose on the floor. Eight planks and a nails and strips make a chest; two metal
brackets make the nails. Bring planks home for a door. Nothing in here opens doors.
— Dez""", w="dez"),
    E("m10", "The doors are the map", """
Finding: the rings are only how it is built. Elevators, stairwells, doors and holes are the real map, and they are
honest: each always leads to the same place. Walked through, it can be walked back, by the one you come out beside or
by a thin spot, a pale seam in the air that hums. Fell or dived: no way back. Record every one.
— A.L., survey""", gate=visited(1), mark="way", w="al"),
    E("m11", "Copper", """
Copper without a mine: cable spools, about four bits each (Levels 1 and 3); machine cabinets (Level 2); stacked pipes
(Level 3), with lead. Twenty bits to an ingot; ten scrap wire to one. Melting wants a crucible and coal. Both are in
Level 3.
— A.L., survey""", gate=visited(1), w="al"),
    E("m12", "Clay", """
Clay floors the flooded tunnels under Level 3: down a manhole. The water is freezing and the gear runs back faster
there than anywhere I have measured, so dig and get out; the rungs go back up. Form a crucible, moulds, a pot and
bowls, and fire them in a pit kiln. Coal is heaped by the generators.
— A.L., survey""", gate=visited(1), w="al"),
    E("m13", "Firesalt", """
M.E.G. FIELD NOTICE. Turn over the coal by Level 3's generators and Level 5's boilers for Firesalt. Set down, it burns
for half a day and nothing hostile comes within eight paces. Salt and powdered sulfur make two. A lit firepit keeps
Hounds off while it burns. A fire, a chest and some Firesalt halfway along a route make an outpost. Build them.
— Field Team 9 (five of us)""", gate=visited(2, 3, 4, 5), w="meg"),
    E("m14", "Under the floor", """
Cast a copper pickaxe and a hammer, and keep nine ingots for an anvil. Then break through any floor: eight blocks of
concrete, and beneath it the ground of the world we came from. Rock, caves, ore, the better ores deeper. Prospect it as
you would at home. Level 8 is that ground laid open, ore lying on the cave floors.
— A.L., survey""", gate=visited(2, 3, 4, 5), w="al"),
    E("m15", "A quiet floor", """
Level 4's the calmest place I know before the city. Grey carpet, fridges with fruit and cheese, Almond Water in the
fountains and coolers. A few vending machines take you instead of serving you: you wake up in a food court and you
can't walk back. Its stairwells sometimes come out in the Lobby. Learn one and you've got a road home.
— Dez""", gate=visited(2, 3, 4, 5), w="dez"),
    E("m16", "The hotel", """
Level 5's got beds. Break the head end and it comes away whole: sleep in it at home. Linen off the foot end makes sacks,
twine and linen, five slots. Clothes in the wardrobes and suitcases, silver off the silverware, brass off the luggage
carts, coal in the boiler halls. The corridors get to you. The Beverly Room doesn't. Pell liked the hotel.
— Dez""", gate=visited(3, 4, 5), w="dez"),
    E("m17", "Growing", """
Nothing grows unless you grow it, love. Seed packets turn up in tool shelves and kitchen cupboards, four seeds a packet.
Soil comes out of the potted plants. Water within three steps: a flooded room in the dark zones, or a bucket. Plant
under a working light, not a dead one; slower than sun, but it grows. The dark zones are cold, so food keeps there. My
first turnip came up yesterday.
— Nell""", gate=visited(1), w="nell"),
    E("m18", "Lights Out", """
M.E.G. FIELD NOTICE. Level 6 is dark. Not dim: dark. Your brightest light shows a few paces and your map forgets
everything past arm's reach. Chalk the walls (right-click a wall; F chooses arrow, cross or circle): chalk stays, and
shows on the map. Keep to the long dry corridors; the wet ones end blind. Follow the sound of waves to the stairs down.
They only go down.
— Field Team 9 (four of us)""", gate=visited(5, 6), w="meg"),
    E("m19", "The sea", """
Level 7: water under a ceiling. Driftwood burns; fish bite. Depth costs light and steadiness, and something large
circles at the edge of sight: if your gear fails down there, surface. A ring of standing stones: dive in the middle and
you come up in the Suburbs. A cave mouth in the deep: the caves. Neither returns.
— A.L., survey""", gate=visited(6, 7), w="al"),
    E("m20", "The 9th Road", """
M.E.G. FIELD NOTICE. Level 8: stay on the 9th Road. Gravel, lamps, our waypoints, camps at the crossings, Almond Water
seeping from the rock beside it. Off it, drifters. All the ore is here: copper, tin, zinc, bismuth, gold, lead, coal and
three kinds of iron. Halite grinds to salt in a quern. The vents beside the road go to Level 2 and back. Dress warm.
— Field Team 9 (three of us)""", gate=visited(7, 8), w="meg"),
    E("m21", "Night and the fields", """
The Suburbs are always midnight, love. Search the houses: pantries, garages with tools and seeds, dressers of clothes.
Behind some houses a path through a field ends at a gate, and the gate is Level 10: fields standing ripe, livestock,
ponds, bee skeps, a quern in the barns. The old furrows are spent, so hoe fresh ground. Never dig below the soil there.
I'm staying.
— Nell""", gate=visited(7, 8, 9), w="nell"),
    E("m22", "The city", """
In some of Level 10's barns a stretch of the east wall between the stalls isn't quite there. Walk into it. The city on
the other side is safe, lit and stocked, with a door back to nearly everywhere: an apartment basement to the Lobby, a
parking ramp to Level 1, a diner's kitchen to the food court. I've got a stall here now. Come and trade.
— Dez""", gate=visited(9, 10), w="dez"),
    E("m23", "Off the rings", """
Not every place lies on a ring. In the hotel, now and then, a locked door is cyan and reads POOL: warm water and white
tile, where lit water heals you, but there is no food at all and the deep pits have no bottom I could find. In the
Suburbs, a doll's house, too clean and too cream, opens on green hills where everything moves a frame at a time. Be
indoors there by dusk.
— A.L., survey""", gate=visited(5, 9, 11), w="al"),
    E("m24", "Keys", """
M.E.G. FIELD NOTICE. There is a place of tunnels and carved doors: the Hub. In by a grey door with a ring of marks over
it, at the end of a maintenance hall in Level 1, chalk arrows leading to it; or one steel door in forty in Level 2, a
chalk circle beside it. Most of its doors want a key, each its own level's, and the keys turn up in their own levels. A
man in the Tower gives one away, once.
— Field Team 9 (two of us)""", gate=visited(1, 2), mark="hubdoor", w="meg"),
    E("m25", "Home", """
Ruth, I've stopped looking for the way out. Everything they wrote about the doors is true: each always goes to the same
place, and a person could learn them all. Only none of them go back to you. If anyone finds a door that does, don't
write it down. Just go. I'm going home now. Home is the Lobby.
— Tom""", gate=visited(10, 11), w="tom"),
]))

# ============================== Common: the levels ==============================

TRACKS.append(Track("l0", "common", "Level 0: the Lobby", 0, entries=[
    E("l0-1", "Corners", """
Boxes were left in twos and threes in the corners of rooms. Most have been gone through: a torn box you can see from
the doorway, and it never has food. A sealed one is worth a long walk. Marked one I didn't get to.
— Dez""", mark="cache", w="dez"),
    E("l0-2", "The dark zones", """
Where the lights are dead the carpet's soaked, the air is cold, and some rooms are flooded. The cold keeps food and the
water grows crops. But the dark pulls at the gear, and there are eyes in it. Bring a torch, not a candle."""),
    E("l0-3", "The Manila Room", """
Ruth, there's a room with a wooden floor, a door in each wall and a table under a chandelier. Nothing follows me in, and
the gear turns forward while I'm there. I sit at the table and pretend it's ours. I've marked it.
— Tom""", mark="manila", w="tom"),
    E("l0-4", "Red", """
Rooms papered red, lit red, walled off but for one narrow gap in each side. Nobody has touched the boxes in there,
because nobody stays long enough; one had a key in it that hummed. In and out. Count to a hundred, then leave whatever
you haven't got."""),
    E("l0-5", "The pits", """
A room full of square holes, two by two. Thirty steps down and you're in Level 2's tunnels, hot and dark, and there is
no climbing back. It's the quickest way out of the Lobby I know. It only goes one way."""),
    E("l0-6", "Above the tiles", """
The ceiling tiles come down, and what's on top of them sometimes doesn't: scrap wire, a bracket, rotten wood, once a
stick of chalk. The slab above that never gives. Neither do the doors, nor the top of the wall where one level meets
the next."""),
    E("l0-7", "Dens", """
M.E.G. FIELD NOTICE. Bones on the carpet, a grey papery hive, crosses chalked on the walls round about: something lives
there. At the heart of every den are two or three sealed boxes nobody dared take. In the Lobby they mostly watch.
Mostly. The nearest is marked: keep out, or don't.
— Field Team 9 (six of us)""", mark="den", w="meg"),
    E("l0-8", "Walls", """
The drywall breaks with any tool, quickest with an axe. Concrete wants a copper pickaxe and gives rubble; four rubble
make a block to build with. Close off a corner, put a door in it, a light and a fire. When the lights go out, eyes come
to the edge of the dark, even at home."""),
    E("l0-9", "TIME 4 FUN", """
A room hung with streamers, and a poster: TIME 4 FUN =). Don't touch it. If you do you won't be in the Lobby any more,
and the people where you'll be are all smiling. A lit torch burns it."""),
]))

TRACKS.append(Track("l1", "common", "Level 1: the Habitable Zone", 1, entries=[
    E("l1-1", "Crates", """
The crates are the best food this side of the city: alone or stacked in the stalls, at the foot of the columns with the
coloured cloths, in the camps. An emptied one, lid gone and straw in the corners, you can tell from across the aisle.
Don't waste the walk.
— Dez""", mark="cache", w="dez"),
    E("l1-2", "Stairs", """
The stair cores, black fire doors under lit EXIT signs, climb to another stairwell in Level 1, now and then in Level 4.
You can walk back down. Where the level ends, the gaps in the wall are under EXIT signs too. Elsewhere the signs point
at nothing.""", mark="way"),
    E("l1-3", "Wanderers", """
People camp here, in the maintenance halls and round a burning barrel. They trade for rusty gears: salvage and hides for
Almond Water, Firesalt, candles, bandages and seeds. Nothing comes near you while you're with one. They don't fight.
Don't make them.
— Dez""", mark="refuge", w="dez"),
    E("l1-4", "Flickering", """
M.E.G. FIELD NOTICE. Out towards the edge of Level 1 a whole section's lights go out at once: a Flickering. Hounds come
with it and hunt until the lights return, a minute or two. Put a fire or a door between you and the dark. Look one in
the eye and it stops and growls: a few seconds. Use them.
— Field Team 9 (six of us)""", w="meg"),
    E("l1-5", "Locked doors", """
The white halls behind the fire doors stay lit through a blackout. Workshops and toolboxes in there: a copper hammer,
chisel, saw or knife now and then, and pry bars. A pry bar, two brackets and an iron nails and strips, opens a locked
door for good in a few seconds if there's a room behind it. Everything near hears."""),
    E("l1-6", "No faces", """
People with no faces walk about here going nowhere. Wave to one (right-click it): it waves back and points the way out,
as far as it knows. Hurt one and every one of them near turns on you."""),
    E("l1-7", "Moths", """
The car park holds you; the gear turns forward. The maintenance corridors don't, quite. Moths the size of your hand
circle any open flame, and near the edges the females bite. A candle draws few, a closed lantern none, and smoke
scatters them. Leave a settled one alone."""),
    E("l1-8", "Voices", """
A voice calling from out of sight, nearly human, coughing: a Skin-Stealer. Big, yellow, slow. Keep your distance, shut a
door, keep a fire. Two red points under a shelf are rats with horns. They keep clear of a torch."""),
    E("l1-9", "Doors that shouldn't be here", """
Four doors that shouldn't be in Level 1. A red EXIT door in a solid car-park wall: it slams behind you, and then you
run. A locked hall door under a glowing EXIT sign. Stairs into the ceiling with confetti on the steps. A grey door at the
end of a maintenance hall, chalk arrows leading to it. I took the grey one.""", gate=visited(2, 3)),
]))

TRACKS.append(Track("l2", "common", "Level 2: Pipe Dreams", 2, entries=[
    E("l2-1", "The mains", """
Level 2 is hot: you will eat half again as fast. The three-wide mains run straight on for miles; the narrow ones between
them mostly end. Stay on the mains. The whole level pulls at the gear: pass through, do not stay.
— A.L., survey""", w="al"),
    E("l2-2", "Steel doors", """
Steel doors in the tunnel walls. Most are locked. Some open on a storeroom. A few that look exactly the same open on
Level 3, 4 or 1, and you can walk back.""", mark="way"),
    E("l2-3", "Cabinets", """
The machine cabinets give copper. Oil drums sometimes still slosh with Almond Water. Toolboxes, trolleys, crates. Food is
scarce: bring yours.""", mark="cache"),
    E("l2-4", "The arm", """
An arm sticking up out of the floor, a finger twitching: a Clump. Walk round it if there's room. It hunts by ear: run or
break things near it and it crawls after you. In a narrow tunnel, go back, or take the grab and be quick."""),
    E("l2-5", "The circle and the red wall", """
One steel door in forty has a chalk circle on the wall beside it: that one goes to the Hub, and you can come back. And if
a blind tunnel ends in a smooth new wall with red light at its foot, don't walk into it unless you can run for two
minutes without stopping.""", mark="hubdoor"),
    E("l2-6", "Screaming", """
Smilers like Level 2, and so do the rats, hairless in the heat. Near the edges the lights sometimes fail and something
screams close by, and a pack of rats goes past at a run after it. Stand aside till the lights come back. Pell didn't.
— Dez""", w="dez"),
]))

TRACKS.append(Track("l3", "common", "Level 3: the Electrical Station", 3, entries=[
    E("l3-1", "Hot brick", """
Level 3 is hot brick and machinery: carry food. Tangles, squeezes you stoop through, wide galleries, transformer halls.
White bars block the side ways you can see and can't reach. It pulls at the gear everywhere."""),
    E("l3-2", "Clay", """
Clay lies under the manholes. Down the rungs into the flooded tunnels: freezing water, and the worst pull on the gear I
have measured. Dig, and get out. The nearest manhole is marked.
— A.L., survey""", mark="manhole", w="al"),
    E("l3-3", "Coal", """
Coal is heaped by the generators, enough to smelt with. Turn it over: there are lumps of Firesalt in it. Copper wants a
hotter fire than wood gives."""),
    E("l3-4", "The Sanctum", """
A hushed hall of pale stone, a red carpet between the columns, candelabra, a winged statue at the end. A Sanctum.
Nothing hostile goes in. There aren't many.""", mark="refuge"),
    E("l3-5", "Freight", """
Freight elevators in the electrical rooms go to other elevators in Levels 3, 4 and 5, and back. Everyone standing in the
car rides along.""", mark="way"),
    E("l3-6", "Scraping", """
M.E.G. FIELD NOTICE. Scraping inside the walls means a Duller. It reaches through at whoever passes close: walk down the
middle of the corridor. Drink Almond Water and it will not reach for you for five minutes. Face it and it runs. What it
takes from your hands it drops wherever it went.
— Field Team 9 (five of us)""", w="meg"),
    E("l3-7", "Caches", """
Cable spools, stacked pipes (copper and lead), industrial fans: this is where copper comes from. The supply caches in the
electrical rooms are worth the squeeze.""", mark="cache"),
]))

TRACKS.append(Track("l4", "common", "Level 4: the Abandoned Office", 4, entries=[
    E("l4-1", "Quiet", """
Level 4 is quiet: cool, grey, almost empty. Desks break into planks, filing cabinets into paper. All of it holds you; the
heart of it is the calmest ground there is before the city."""),
    E("l4-2", "On tap", """
Fountains, coolers, vending machines: Almond Water, a few bottles each. Break rooms have fridges with fruit and cheese.
Some storerooms still hide a supply box.""", mark="cache"),
    E("l4-3", "Cores", """
Stairwells and elevators stand together in building cores, with a restroom. The stairs mostly go to other stairs on this
floor, now and then to the Lobby. The elevators go to 3, 4 or 5.""", mark="way"),
    E("l4-4", "Hungry machines", """
A few vending machines give nothing. Press the buttons and they take you to a food court, the same one every time:
sealed, safe and full. Getting out is one way, and every door goes somewhere different.
— Dez""", w="dez"),
    E("l4-5", "The doorframe", """
A wooden doorframe standing on its own in an empty office. Walk through it and it's gone behind you, and you're in a
library with no end. Most of its EXIT doors are locked. Bring food."""),
    E("l4-6", "Lanterns", """
Dullers here too: walk the middle of the corridor. A lantern is the light for this floor: the moths ignore it."""),
]))

TRACKS.append(Track("l5", "common", "Level 5: the Terror Hotel", 5, entries=[
    E("l5-1", "The Beverly Room", """
The hotel goes on and the corridors wear on you. The Beverly Room doesn't: a ballroom with doors on every side and a game
of Mahjong nobody finished. Nothing hostile goes in.""", mark="refuge"),
    E("l5-2", "Doors and cages", """
Copper-cage elevators under a floor dial, rare, two wide: to other elevators in 3, 4 or 5, now and then Level 1. Most
guest doors are locked for good. A few open, onto another part of the hotel, Level 3 or the Lobby, and you can walk
back.""", mark="way"),
    E("l5-3", "STAFF", """
M.E.G. FIELD NOTICE. An open door under a STAFF sign, stairs going up: the way into Level 6. Have your brightest light
lit before you reach the top.
— Field Team 9 (four of us)""", mark="way", w="meg"),
    E("l5-4", "Boilers", """
STAFF ONLY doors open on the boiler halls: coal by the furnaces, Firesalt in the coal, and heat that will have you eating
half again as fast. The worst pull on the gear in the hotel. Get the coal and go."""),
    E("l5-5", "Children", """
Ruth, there are children here with no faces. They come to look at me and run if I move too fast. When they all hurry
away at once, the dogs are coming. They're not dogs.
— Tom""", w="tom"),
    E("l5-6", "POOL", """
Now and then one of the locked doors is cyan and says POOL. It opens: warm water, white tile, and you can walk back
through the POOL door you come out beside."""),
    E("l5-7", "F-U-N", """
Wooden double doors with big letters: F-U-N. Behind them is a party that never stops. You can walk back out. They'll ask
you to stay."""),
]))

TRACKS.append(Track("l6", "common", "Level 6: Lights Out", 6, entries=[
    E("l6-1", "Trunks", """
The corridors run on a grid. Every fourth is three wide and never breaks: find one and keep to it. The two-wide ones
between are a maze with one way in. The narrow wet passages wind off a little way and stop.
— A.L., survey""", w="al"),
    E("l6-2", "Waves", """
M.E.G. FIELD NOTICE. Listen for waves: you hear them within a hundred and sixty paces of stairs down, louder as you close
in, and chalk arrows on the corridor walls point there. The stairs drop you out of a ceiling into the sea.
— Field Team 9 (four of us)""", mark="way", w="meg"),
    E("l6-3", "The wire", """
A wire strung low across a straight corridor. Trip it and you're in a food court, bright and full. You can't get back to
where you were, and nothing in there will hurt you."""),
    E("l6-4", "Packs", """
The ones who didn't make it left their packs at the dead ends: Almond Water, candles, rope, bandages, chalk, and often a
note. Every dead end is worth one look.""", mark="cache"),
    E("l6-5", "Cold", """
It's cold down here: wear something, or eat more. The scuttling and the whispering are mostly nothing. Scraping inside
the wall is a Duller."""),
    E("l6-6", "The switch", """
There's a light switch on a wall now and then. It does nothing. I've tried every one I've found."""),
]))

TRACKS.append(Track("l61", "common", "Level 6.1: the Snackrooms", SNACKROOMS, entries=[
    E("l61-1", "Eat", """
You're safe in here. The machines and fridges fill up again once a week. Eat.
— Dez""", w="dez"),
    E("l61-2", "Out", """
Every door out shuts behind you. Rusty doors go to Level 6. Glass doors to Level 4 or 5. Vents to Level 3. Kitchen doors
to another food court.""", mark="way"),
    E("l61-3", "The diner door", """
One kind of kitchen door is different: the city's diners open into food courts, and you can walk back through the kitchen
door you come out of."""),
    E("l61-4", "Held", """
Ruth, the gear turns forward faster here than anywhere. I sat a whole day. I almost stayed.
— Tom""", w="tom"),
]))

TRACKS.append(Track("l7", "common", "Level 7: Thalassophobia", 7, entries=[
    E("l7-1", "The drop", """
You come in from a room in the ceiling, over the drop. Shallows by the walls, then the twilight, then the midnight, then
the abyss. Islands of black rock, some with a camp and a supply box.""", mark="cache"),
    E("l7-2", "Standing stones", """
A ring of standing stones in the water. Dive in the middle and you come up in the Suburbs. One way."""),
    E("l7-3", "The cave mouth", """
A cave mouth in the deep. Swim in and you come out on the 9th Road, in the caves. One way. Take a breath first."""),
    E("l7-4", "White tile", """
In the twilight zone, a patch of white tile on the seabed, faintly lit. Dive to it and you come up in warm water: the
Poolrooms. One way."""),
    E("l7-5", "The Thing", """
M.E.G. FIELD NOTICE. Something vast circles out at the edge of sight. Stay below the twilight with your gear failing and
it strikes, once, hard. In the abyss it may come at anyone. It cannot be fought. Surface.
— Field Team 9 (three of us)""", w="meg"),
    E("l7-6", "Salvage", """
Driftwood is firewood. Fish bite. The seabed has wreck crates and lost packs. Mind the tar pools: they're scalding."""),
]))

TRACKS.append(Track("l8", "common", "Level 8: Cave Systems", 8, entries=[
    E("l8-1", "The road", """
M.E.G. FIELD NOTICE. Stay on the 9th Road: gravel, lamps, our waypoints, camps at the crossings. The main roads run
unbroken; the side roads mostly end in rock. Where the road meets another level it runs on through the wall.
— Field Team 9 (three of us)""", mark="door", w="meg"),
    E("l8-2", "Ore", """
Native copper and malachite. Cassiterite for tin, sphalerite for zinc, bismuth, gold in quartz, galena for lead, coal,
and limonite, hematite and magnetite for iron. No silver ore: silver comes from the hotel. Loose ore lies on the cave
floors.
— A.L., survey""", w="al"),
    E("l8-3", "Seeps", """
Almond Water seeps out of the rock beside the road. Hold a bottle to a seep and fill it; it comes back. Dullers won't
reach for you near one."""),
    E("l8-4", "Drifters", """
Drifters keep to the dark off the road; the lamps keep them off. The vents beside the road go to Level 2, and back.""",
      mark="way"),
    E("l8-5", "Salt", """
Halite grinds to salt in a quern; limestone and chalk grind to lime. There's a quern in Level 10's barns. Salt keeps meat,
and salt with powdered sulfur makes Firesalt."""),
    E("l8-6", "Off the road", """
It's cold: dress warm or eat more. The remains you find off the road were people who went to look at something."""),
]))

TRACKS.append(Track("l9", "common", "Level 9: the Suburbs", 9, entries=[
    E("l9-1", "Houses", """
Always midnight. The houses are the loot: kitchens and pantries for flour, salt and fat, garages for tools and seeds,
dressers for clothes. Some are locked; that's what pry bars are for.
— Dez""", mark="cache", w="dez"),
    E("l9-2", "The field gate", """
Behind some houses a path runs through a field to a gate. Through it is Level 10, and you can walk back.
— Nell""", mark="way", w="nell"),
    E("l9-3", "The doll's house", """
One house in a hundred and fifty is too cream and too clean: a doll's house. Its front door opens on Level 94, and you
can walk back."""),
    E("l9-4", "The teal pool", """
One backyard pool in a few dozen is still full, lit teal. Dive to the bottom: the Poolrooms. One way."""),
    E("l9-5", "Fog", """
If the air goes cold all at once, a fog rolls in and voices start calling out of it, get indoors. There's only one of it,
and it's far too big for any door. It goes in three minutes or so."""),
    E("l9-6", "Hides", """
Hares, foxes, raccoons, now and then a wolf. Hides make leather, and leather makes armour. The streets pull at the gear;
don't stand about in them."""),
]))

TRACKS.append(Track("l10", "common", "Level 10: Bumper Crop", 10, entries=[
    E("l10-1", "Ripe", """
Safe, love, and steady. Ripe spelt, rye, flax and vegetables: cut them. The old furrows are spent: hoe fresh grass and
plant there, within three steps of water. It never rains.
— Nell""", mark="cache", w="nell"),
    E("l10-2", "The farmsteads", """
Livestock in the paddocks, bee skeps by the farmhouses, cattails at the ponds for baskets, clay in the pond beds, a quern
in the barns. Everything for a farm but somewhere to wake up.
— Nell""", w="nell"),
    E("l10-3", "Worms", """
A metre under the soil is a mass of worms. Dig into it and they come up biting, and the crops die round them. Don't dig
down. And something waits half buried in the fields by the barns: watch for an arm."""),
    E("l10-4", "The barn wall", """
In some barns a stretch of the east wall between the stalls isn't quite there: the boards a little out of true, dust
hanging in front of them. Walk into it. Marked the one I found.
— Dez""", mark="barnwall", w="dez"),
    E("l10-5", "The pond", """
Dive to the bottom of a pond and you come up in the sea, Level 7. One way."""),
    E("l10-6", "Red lights", """
Out past the farmsteads, love, some of the windmills have a red light on the cap, five in a line. Follow them. At the
end there's a building that has no business being there, PARADISE in pink letters and music behind dark glass. Its
revolving door goes somewhere warm, and you can walk back. Throw the lever by a windmill's door and its light turns
green, so you know where you've been.
— Nell""", w="nell"),
]))

TRACKS.append(Track("l11", "common", "Level 11: the Endless City", 11, entries=[
    E("l11-1", "Stocked", """
Nothing attacks in the city unless you start it. Groceries, pharmacies, hardware stores: food, bandages, copper tools,
nails, rope. Almond Water in every machine and on every cart.
— Dez""", mark="cache", w="dez"),
    E("l11-2", "Home lines", """
An apartment block's basement door goes to the Lobby. A parking garage ramp to Level 1, a subway maintenance door to 2, a
substation door to 3, office tower elevators to 4, hotel elevators to 5. You can walk back through all of them.""",
      mark="way"),
    E("l11-3", "Side doors", """
A dark doorway off an alley: Level 6. A rowhouse's front door: the Suburbs. A patch of wheat in a park: the fields. A
diner's kitchen door: the food court, and back."""),
    E("l11-4", "Holes", """
An open manhole drops into Level 2, a street that has caved in into the caves, the deep middle of a park fountain into
the sea. None of them come back."""),
    E("l11-5", "Baths and screens", """
Public baths with a cyan door marked POOL: the Poolrooms. A cinema: walk up to the screen and on into the picture, and
you fall out of the sky over green hills."""),
    E("l11-6", "Books and a party", """
A closed-down bookstore's door opens on a library with no end. Gym doors painted with a tiger, a parrot and a giraffe, at
the back of a parking garage, open on a party. You can walk back out of both."""),
    E("l11-7", "Black windows", """
A third of the buildings have no doors and black mirrors for windows. Nobody gets in. The floors above the shops are
dark, and nobody has been up."""),
]))

TRACKS.append(Track("l37", "common", "Level 37: Sublimity", POOLROOMS, entries=[
    E("l37-1", "Lit water", """
Stand in lit water and it heals you, steadies you, and counts as rest. The dark corners pull at the gear. There's no food
here at all: bring it."""),
    E("l37-2", "Deep water", """
The stair pits go down further than you can see. Some passages are a swim under a wall. Know how long you can hold your
breath before you find out."""),
    E("l37-3", "Corridors", """
POOL doors go out into the hotel, and back. A dry corridor whose tile turns to office carpet goes to Level 4. One whose
tile turns to concrete and asphalt goes to the Hub. A tunnel of arches ends in a black round mouth over the sea. If a
corridor is lit red, turn round.
— A.L., survey""", mark="way", w="al"),
    E("l37-4", "Epsom salt", """
Crusts of Epsom salt dry on the rims in the dark corners. Two of them over a linen make a poultice as good as any."""),
    E("l37-5", "Red water", """
Far out the water turns thick and red, and there's chanting. Red Water heals everything. It also takes away, for good,
how steady you can ever be again."""),
    E("l37-6", "The pit", """
The pit nobody has found the bottom of comes up in a backyard pool in the Suburbs. One way."""),
]))

TRACKS.append(Track("l94", "common", "Level 94: Motion", MOTION, entries=[
    E("l94-1", "Dusk", """
Everything here moves a frame at a time. By day it's safe. When the siren tune slows and goes flat, get indoors: the
Animations come out at night, and they never come inside."""),
    E("l94-2", "Hold still", """
If they find you outside, stand still. Quite still, a few seconds, and they take you for a doll. The paper ones fall
apart in water."""),
    E("l94-3", "Iceboxes", """
Iceboxes in every house: cheese, butter, beans. Milk vans by the plazas with Almond Milk, filled again each week.
Fountains and water towers for Almond Water.
— Dez""", mark="cache", w="dez"),
    E("l94-4", "Clay", """
Dig the turf for soil, love. Under it is red modelling clay, and blue clay a little further down. All the pottery you
want.
— Nell""", w="nell"),
    E("l94-5", "The gate", """
A rusted gate with no sign on a hilltop, at dusk and dawn only: Level 10. One house in forty opens back onto the Suburbs.
Don't open the door of a house that's full of water unless you want the sea.""", mark="way"),
    E("l94-6", "The castle", """
Towards the middle the houses come apart into heaps of furniture. Follow the strangeness to a glass mountain and a castle.
Touch nothing in it: tin soldiers wind up and come for a minute and a half."""),
    E("l94-7", "The King", """
The King sits in stone at a long table. Sit in the second chair and he makes your nightmare out of clay. It's only as
strong as you think it is: drink your Almond Water first. Win, and he carries you out."""),
]))

TRACKS.append(Track("run", "common", "Level !", RUN, entries=[
    E("run-1", "Slammed", """
The door's locked behind you and there's no other way back. When the chained door bursts, run, and don't stop. Toys,
boxes and cords on the floor will trip you if you sprint over them: go round."""),
    E("run-2", "Dead end", """
Don't take the door if the hall turns beside it. The real one is at a dead end. The EXIT doors at the bends open on an
empty room. Don't stop. They're still there.""", mark="door"),
    E("run-3", "Energy bars", """
Eat the energy bars on the bedside table before the door goes: half a minute quicker. Some halls have a Safe Zone, a room
they won't come into. They wait outside. After a couple of hours they stop waiting."""),
    E("run-4", "Cracked floor", """
In the dark last stretch, cracked floor means a hole just past it. It drops you into the caves, if you'd rather that than
what's behind you."""),
    E("run-5", "Once", """
Out the far end you're in Level 1, the office or a library with no end, always the same for the same hall. Runners who
didn't make it lie along the way; one had a key that hummed. And once you're out, it won't let you in again.
— Dez""", w="dez"),
]))

TRACKS.append(Track("fun", "common", "Level Fun =)", FUN, entries=[
    E("fun-1", "Smiles", """
Everyone here is smiling, and they're not people. They bite, and a bite turns into a fever that only goes down once
you're out of here. Bandage or poultice a bite within half a minute and it doesn't take. If the fever fills, you don't
leave."""),
    E("fun-2", "Party clothes", """
Wear a party hat and hold a red balloon, and from more than three steps off they take you for one of them, as long as you
don't run or hit anything. They're slow and short-sighted: keep your distance. The hats come off the dead ones; the
balloons off the little ones."""),
    E("fun-3", "Gifts and cake", """
One gift in five is a popper, and everything near hears it. Birthday cake and cookies are fine. Don't eat the red
velvet.
— Dez""", w="dez"),
    E("fun-4", "Balloons", """
A balloon tied to nothing, in the dark corridors: it stings and holds you. Don't pop it close. The gas comes out."""),
    E("fun-5", "Out", """
The service stairs go down to Level 1, the FUN doors to the hotel, a waiting room's white door to the city, and you can
come back by each. A poster back to front in a room where the party's over goes to the office. Over the side of the deck
is the sea. The bottom of the deep ball pit is somewhere else entirely.""", mark="way"),
]))

# The note someone altered (fun-wanderernote-altered): read once, out of sequence, marking a party
TRACKS.append(Track("fun-altered", "special", "Level Fun =)", FUN, chapter="fun", entries=[
    E("fun-lie", "Come join us!", """
Level Fun is completely safe =) There is a party in the room I marked. Come join us!""", mark="party"),
]))

TRACKS.append(Track("end", "common", "The End", END, entries=[
    E("end-1", "Which doors", """
Two EXIT doors in three never open. The ones that do always go to the same place: mostly Level 1, sometimes the Hub, the
city, the office or the hotel, and you can come back. Write down which open. The cards in the catalogue drawers point at
one that does.
— A.L., survey""", mark="endexit", w="al"),
    E("end-2", "Distortions", """
Every so often the lights stutter, the floor shakes, and for a few seconds it's somewhere else: the Lobby, the office, a
street at night, warm water, green hills, snow. Walk into a wall while it lasts and you go there. Not the snow."""),
    E("end-3", "Quiet", """
Stay a couple of hours and the gear starts slipping. The central hall holds you. Shelves that lean come down at a touch,
loudly, and when the lights go out there's something grinning in the dark."""),
    E("end-4", "Screens", """
The computers buzz until you turn one on. It shows the doors that open near it, once, and dies. One in four says =)
instead. Don't."""),
    E("end-5", "Rooms that aren't", """
Some departments are somebody's office, a hotel corridor, a house, the Lobby, made of shelves. Each has one real door, to
the place it copies. Some stockrooms have a ladder up to a vent that lets you out over green hills. Service desks and
catalogues sometimes hold a key that hums."""),
]))

TRACKS.append(Track("hub", "common", "The Hub", HUB, entries=[
    E("hub-1", "Cold", """
M.E.G. FIELD NOTICE. Nothing hunts here and the gear turns forward, but it is cold and there is nothing to eat. Bring
food.
— Field Team 9 (two of us)""", w="meg"),
    E("hub-2", "Carved doors", """
Every carved door wants its own level's key, turned three times, and the key is gone after. Three open for anyone: Level
1 in tunnel 7, the city in tunnel 10, and 178, the food court, in tunnel 5. None of them let you back. Hold a key here and
listen: it chimes from the way its door is.""", mark="door"),
    E("hub-3", "Where keys are", """
The keys are found in their own levels, mostly in the worst places: the Lobby's Red Rooms, the flooded tunnels and
Sanctums of Level 3, the red water of the Poolrooms, the King's castle. Sometimes in a den, now and then a sealed box. In
the long red hall, on the runners who didn't make it."""),
    E("hub-4", "The Keymaster", """
In the Tower a man gives you one key, of a level you have been to. Right-click him to see which; sneak and right-click to
take it. He walks you to its door. He never lets you in again, and if you break anything in there he throws you out with
nothing."""),
    E("hub-5", "The doorstep", """
By the city door the M.E.G. keep a doorstep carpet: their man sells two keys a week for rusty gears, and their register
shows where the open doors are. The pink door with the ribbon opens for anyone carrying something cute. A hole in the
road drops you out of the sky over green hills. Where a wall's seams don't meet, walk through: the office.
— Dez""", mark="way", w="dez"),
]))

TRACKS.append(Track("l974", "common", "Level 974", L974, entries=[
    E("l974-1", "Manners", """
It's watching. It won't hurt you. Don't break its things and don't strike it: it puts the lights out and empties the
larder."""),
    E("l974-2", "The gift", """
It wants the cute thing you brought. Sneak and right-click with it in your hand and it comes for it. Give it over, sleep,
and you wake somewhere quiet, always the same somewhere from the same house."""),
    E("l974-3", "Don't stay", """
Ruth, after most of a day the pink starts to press, and the food turns to sugar. If you've lost what you brought, wait a
day: it'll take anything cute and send you home.
— Tom""", w="tom"),
]))

TRACKS.append(Track("l3999", "common", "Level 3999: the Neon Paradise", L3999, entries=[
    E("l3999-1", "Safe here", """
Nothing hunts where the neon is lit. It's warm, the gear turns forward, faster in the lobbies, and the violet pools mend
you while you stand in them. The faceless staff behind the counters can't be hurt and won't hurt you; ask one and it
points the way to a lobby. Right-click a mall directory and it gives the way to the nearest food court and lobby. More
wanderers camp here than anywhere."""),
    E("l3999-2", "Tickets", """
Every machine pays you once a day. Hold right-click and play it out. The little cabinets pay up to three tickets,
pinball up to four, the racers, dance pads and skee-ball one to five, and now and then one hits a jackpot of twelve. The
claw pays nothing, but one go in four it drops you a plush. Forty tickets a day is all the machines will give you, all
of them together.
— Dez""", w="dez"),
    E("l3999-3", "The prize counter", """
Tickets in your hand at a prize counter, and you get a prize from the dearest tier you can pay. 5: candy, a soda, a
candle, a glow bracelet, a plush. 15: seeds, bandages, firesalt, neon tubing, a neon lamp. 40: a lantern, a backpack, a
pry bar, six Almond Water. 200: a temporal gear. The food stalls sell a hot tray for 6.
— Dez""", w="dez"),
    E("l3999-4", "Machines that take water", """
The vending machines take a bottle of Almond Water and give you a snack or a can: chips, a candy bar, popcorn, cotton
candy, soda, cashew water, Paradise Pop. They never run empty. Popcorn's grain, love; most of the rest is sugar and fizz.
The trays from the stalls fill you best.
— Nell""", w="nell"),
    E("l3999-5", "Salvage", """
Finding: the dead machines break down. Circuit boards melt to copper in a crucible, ten to an ingot; coin mechanisms to
brass, five to an ingot. Plastic burns. Dead neon gives tubing. Two tubing, two plastic, a circuit board and a glow
bracelet make two neon lamps of the bracelet's colour; plastic and tubing make two lilac bracelets. The machines that
still work cannot be broken.
— A.L., survey""", w="al"),
    E("l3999-6", "The dark edge", """
M.E.G. FIELD NOTICE. Toward the far edge, some blocks of the mall have gone dark: Level 3999.1. The neon flickers and
fails for a stretch before it. Inside it is cold and the gear runs down fast. Smilers in the dark, Hound packs,
Partygoers. The prize cases and ticket piles in there belong to whoever carries them out. A rusted machine in a row of
cabinets is no machine: walk into it and you are in the dark.
— Field Team 9""", w="meg"),
    E("l3999-7", "Out", """
A lobby's revolving door walks you out into a car park in the wheat fields, and back. One STAFF ONLY door in six opens
on the Hub, and back; the rest are locked. Some game rooms have a little arcade at the back with an elevator down to the
Lobby, and back. Play a cabinet with another place on its marquee to the end and it takes you there, one way. A drain
at the bottom of a violet pool drops you into the Poolrooms.""", mark="way"),
]))

TRACKS.append(Track("l188", "common", "Level 188: the Courtyard of Windows", L188, entries=[
    E("l188-1", "Read the windows", """
The window you climbed in by shows where you came from, and climbing back through it takes you there. The other
ground-floor windows that show somewhere else lead there too. The rest are rooms: blinds down, lit, dark, changing
every day or so. Look before you go in anywhere."""),
    E("l188-2", "Blinds", """
Ruth, never open a blind from inside a room. A man did, in front of me, and he was gone, and the window lit up with a
hallway I'd never seen. The door shut and wouldn't open for three days. Each window always goes to the same place, so
you can tell where he went by looking. I hope it has weather.
— Tom""", w="tom"),
    E("l188-3", "Waving", """
Someone standing in a lit window, waving: count which room it is and stay out of it. Within six steps you hear
whispering. Within two, an arm comes out of the glass and pulls. Hit it twice, or get three or four steps clear, before
it has you at the glass: six seconds there and you go through, and nobody comes back from that. They move to other
windows every night. The shapes at the edge of your eye are nothing. Don't look."""),
    E("l188-4", "Rooms", """
The rooms are warm, love, and the courtyard isn't. Shut a room's door behind you and nothing comes in, unless someone
was waving in its window. Wardrobes have clothes and cloth, minibars Almond Water, juice and crackers, and beds give
cloth. Breakfast in the lobby: cereal and juice from the machines. The housekeeping carts sometimes hold a keycard; it
opens the locked rooms, never the ones held shut.
— Nell""", w="nell"),
    E("l188-5", "Other windows", """
M.E.G. FIELD NOTICE. The Hub has one window, in a tunnel wall: climb through and you come down in the courtyard beside
the window that leads back. Level Fun has one, a party room's window with confetti on the sill. The Lobby and Level 1
have windows where no window should be. All of them walk back.
— Field Team 9""", w="meg"),
    E("l188-6", "Fire exits", """
Finding: one fire door on each upper floor, EXIT over it, push bar. Second floor: Level 1. Third: the hotel. Fourth:
the office. Fifth: the pipes. Each walks back. The lifts are out of order and the front door in the lobby is locked;
the stairs are in the north-west corner.
— A.L., survey""", w="al"),
    E("l188-7", "The hatch", """
Iron ring in the middle of the deck. Lift the hatch and drop: a long way down through the black, into warm water. The
Poolrooms. No way back up.
— Dez""", w="dez"),
]))

# ============================== Rare: folded notes ==============================

RARE_CHAPTER = "rare"

TRACKS.append(Track("rare-l0", "rare", "Folded notes", 0, chapter=RARE_CHAPTER, entries=[
    E("r-l0-1", "Red keys", """
The Red Rooms keep keys. About one box in a dozen in there has a Level Key that hums when you strike it. I marked the
nearest red block. Don't stay past a hundred.""", mark="redroom"),
    E("r-l0-2", "Moving house", """
Ruth, I moved home to the Manila Room. The gear turns forward there, nothing follows me in, and four doors means four
ways out. I've marked it for whoever comes after. Use a temporal gear on the floor there.
— Tom""", mark="manila", w="tom"),
]))
TRACKS.append(Track("rare-l1", "rare", "Folded notes", 1, chapter=RARE_CHAPTER, entries=[
    E("r-l1-1", "Two doors", """
M.E.G. BRIEFING, RESTRICTED. Level 1 has two doors worth knowing. A locked hall door off the maintenance halls under a
glowing EXIT sign, about one in twenty-five: The End, and back. A grey door with a carved ring of marks at the end of a
hall, chalk arrows leading to it: the Hub, and back. Nearest marked.
— Field Team 9""", mark="hubdoor", w="meg"),
]))
TRACKS.append(Track("rare-l3", "rare", "Folded notes", 3, chapter=RARE_CHAPTER, entries=[
    E("r-l3-1", "Under the floor", """
Fair copy, Level 3. In the flooded tunnels under the floor, about one box in a dozen holds a Level Key. The Sanctums
keep them too. Clay underfoot all the way. Nearest manhole marked.
— A.L.""", mark="manhole", w="al"),
]))
TRACKS.append(Track("rare-l4", "rare", "Folded notes", 4, chapter=RARE_CHAPTER, entries=[
    E("r-l4-1", "The same machine", """
The vending machines that take you are always the same ones, and each always takes you to the same food court. If you
find one, mark it: it's the only door into that place you'll ever get to choose."""),
]))
TRACKS.append(Track("rare-l5", "rare", "Folded notes", 5, chapter=RARE_CHAPTER, entries=[
    E("r-l5-1", "Doors in the hotel", """
One locked guest door in a hundred and fifty is F-U-N. Some are cyan POOL doors. Most guest doors that open lead on into
the hotel, but some go to Level 3 or the Lobby, and the Lobby ones are the best road home there is. Nearest safe room
marked.""", mark="refuge"),
]))
TRACKS.append(Track("rare-l6", "rare", "Folded notes", 6, chapter=RARE_CHAPTER, entries=[
    E("r-l6-1", "Ways down", """
M.E.G. BRIEFING, RESTRICTED. Level 6 trip wires run low across straight corridors only. The stairs down are in chambers
deep in the level; the waves carry a hundred and sixty paces. Nearest way down marked.
— Field Team 9""", mark="way", w="meg"),
]))
TRACKS.append(Track("rare-l7", "rare", "Folded notes", 7, chapter=RARE_CHAPTER, entries=[
    E("r-l7-1", "Wrecks", """
Fair copy, Level 7. The island camps keep a supply box each, and the wreck crates on the seabed have never been opened.
The white tile lies in the twilight zone, not deeper. Nearest untouched box marked.
— A.L.""", mark="cache", w="al"),
]))
TRACKS.append(Track("rare-l8", "rare", "Folded notes", 8, chapter=RARE_CHAPTER, entries=[
    E("r-l8-1", "Ores, fair copy", """
Fair copy, Level 8: native copper and malachite (green); cassiterite, tin; sphalerite, zinc; bismuthinite; gold in quartz;
galena, lead; limonite, hematite and magnetite, iron. No silver ore at all: take silver from the hotel's silverware, or
from galena deep down. Halite and limestone for the quern.
— A.L.""", mark="refuge", w="al"),
]))
TRACKS.append(Track("rare-l9", "rare", "Folded notes", 9, chapter=RARE_CHAPTER, entries=[
    E("r-l9-1", "Too clean", """
The doll's house is one in a hundred and fifty: cream, too clean, no wear on the step. Its door goes to Motion and back.
The full pool is one backyard in a few dozen, lit teal at midnight: the Poolrooms, one way."""),
]))
TRACKS.append(Track("rare-l10", "rare", "Folded notes", 10, chapter=RARE_CHAPTER, entries=[
    E("r-l10-1", "The way through", """
Love, the barn wall: the east side, between the stalls, boards out of true, in a little under half the barns. I've marked
the nearest one I know. My lad went through to the city and came back with tinned peaches.
— Nell""", mark="barnwall", w="nell"),
]))
TRACKS.append(Track("rare-l11", "rare", "Folded notes", 11, chapter=RARE_CHAPTER, entries=[
    E("r-l11-1", "City secrets", """
City secrets: the diner kitchen doors go to the food court and walk back, the only door into the Snackrooms that does.
The cinema screen drops you over Motion. The bookstore is the way into The End that lets you back out.
— Dez""", mark="way", w="dez"),
]))
TRACKS.append(Track("rare-l37", "rare", "Folded notes", POOLROOMS, chapter=RARE_CHAPTER, entries=[
    E("r-l37-1", "Read the floor", """
Fair copy, the dry corridors: about one in five turns to asphalt (the Hub, and back); about one in seven is lit red and
ends in an EXIT door (Level !, no way back); the rest turn to office carpet (Level 4). Read the floor before you walk on.
— A.L.""", mark="way", w="al"),
]))
TRACKS.append(Track("rare-l94", "rare", "Folded notes", MOTION, chapter=RARE_CHAPTER, entries=[
    E("r-l94-1", "The throne room", """
One of the throne room's four doors opens, a different one each day. With your gear full the King's clay thing hits at a
quarter of its strength; with it empty, twice as hard. The first time you win he gives you a shard of his crown, and the
Animations take whoever carries it for one of their own."""),
]))
TRACKS.append(Track("rare-end", "rare", "Folded notes", END, chapter=RARE_CHAPTER, entries=[
    E("r-end-1", "Which doors, fair copy", """
Fair copy, The End. One EXIT door in three opens, always to the same place. Of those: four in ten to Level 1, one in four
to the Hub, three in twenty to the city's bookstore, one in ten each to the office and the hotel. The fake rooms: an
office goes to Level 4, a hotel to 5, a house to 9, the Lobby to 0; the snow goes nowhere. Nearest working door marked.
— A.L.""", mark="endexit", w="al"),
]))
TRACKS.append(Track("rare-hub", "rare", "Folded notes", HUB, chapter=RARE_CHAPTER, entries=[
    E("r-hub-1", "Resonance", """
M.E.G. BRIEFING, RESTRICTED. A Level Key held in the Hub chimes from its door's direction, and rings out within eight
paces of it. The keys for Level 1, the city and 178 are wasted: those doors open for anyone.
— Field Team 9""", w="meg"),
]))
TRACKS.append(Track("rare-run", "rare", "Folded notes", RUN, chapter=RARE_CHAPTER, entries=[
    E("r-run-1", "The third time", """
What I worked out the third time. Seventeen halls. The real exit is at a dead end with no turn either side. One hall in
three has a hole near the end, cracked floor before it, down to the caves. One in five has a Safe Zone: they wait outside
for two hours, then they come in. Real exit marked.""", mark="door"),
]))
TRACKS.append(Track("rare-fun", "rare", "Folded notes", FUN, chapter=RARE_CHAPTER, entries=[
    E("r-fun-1", "How I got out", """
A party hat on your head and a red balloon in your hand, and from more than three steps they take you for one of them, so
long as you don't run or hit. Bandage a bite inside half a minute or the fever takes. The fever only goes down outside,
slowly, and Almond Water helps. The way out I used is marked.""", mark="way"),
]))
TRACKS.append(Track("rare-l3999", "rare", "Folded notes", L3999, chapter=RARE_CHAPTER, entries=[
    E("r-l3999-1", "Ways in, fair copy", """
Fair copy, ways into 3999. Level 10: five windmills in a line, red lights on their caps, lead to a lone arcade; its
revolving door walks in, and back. The city: a stretch of alley wall flickering purple, one block in three hundred; walk
into it, and back. The far Poolrooms: glowing magenta tiles at the bottom of the deepest water; dive, one way. The End:
about one computer in twenty runs a program nobody started. The Hub: the door marked 3999.
— A.L.""", w="al"),
    E("r-l3999-2", "Ticket sense", """
Ticket sense. Hold only what you mean to spend: the counter takes the dearest tier your hand can pay, so walk up with two
hundred and you get the gear whether you wanted it or not. Forty a day means five days of machines for a gear. Or go into
the dark: the ticket piles there are a handful each, the prize cases are free, and nothing counts what you take.
— Dez""", w="dez"),
]))
TRACKS.append(Track("rare-l188", "rare", "Folded notes", L188, chapter=RARE_CHAPTER, entries=[
    E("r-l188-1", "The ground floor, fair copy", """
Fair copy, Level 188. Twelve ground-floor windows show other places and lead there, and back: the Lobby (three), Level
1 (two), the pipes, the office, the hotel, the dark, the Suburbs, the Hub, the party. A blind opened from inside any
other room goes somewhere fixed: most often the Lobby, then Level 1, the office or the hotel; one in fifty to The End. A
window lit with somewhere is a sealed room.
— A.L.""", w="al"),
    E("r-l188-2", "Ways in", """
M.E.G. BRIEFING, RESTRICTED. Ways into 188: a window where no window should be, in about one cell in three hundred of the
outer Lobby, or one car park in two hundred and fifty in Level 1; the Hub's tunnel window; Level Fun's confetti window.
All four walk back. Out without a window: the fire doors upstairs, or the hatch, one way.
— Field Team 9""", w="meg"),
]))

TRACKS.append(Track("rare-any", "rare", "Folded notes", None, chapter=RARE_CHAPTER, entries=[
    E("ra01", "Hub entrances, verified", """
M.E.G. BRIEFING, RESTRICTED. Hub entrances, verified. Level 1: in the outer half of the maintenance halls, a grey door
with a carved sigil over it in the middle of a hall block's north wall; chalk arrows along the corridor point to it.
Level 2: one locked steel door in forty, a chalk circle on the wall beside it. Level 37: a dry corridor whose tile turns
to concrete and asphalt. All three walk back.
— Field Team 9""", mark="hubdoor", w="meg"),
    E("ra02", "Into the food courts", """
Fair copy. The food courts (Level 6.1) can be entered four ways: a hungry vending machine in Level 4 (the same few always
take you); a wire strung low across a straight corridor in Level 6; a diner's kitchen door in the city, which walks back;
and the open carved door marked 178 in the Hub's fifth tunnel. I know of no other.
— A.L.""", w="al"),
    E("ra03", "Something cute", """
If you carry something cute (a plush, a flower, a seashell) through any doorway that goes somewhere, one time in twenty
you end up in a pink house that's yours, with something very tall in it. One in six if it's in your hand. It never hurts
you. Give it the thing you brought and you wake somewhere quiet. Not twice in two days."""),
    E("ra04", "Key prices", """
M.E.G. BRIEFING. Our man on the doorstep carpet by the Hub's city door sells two Level Keys a week, thirty to forty-five
rusty gears each, only for levels somebody has been to. The Keymaster in the Tower gives one free, of a level you have
been to, once: right-click to see which, sneak and right-click to take. Break nothing in the Tower.
— Field Team 9""", w="meg"),
    E("ra05", "Locks", """
Locks. A pry bar gives on a locked door in about four seconds, for good, but only if there's a room behind it. A door set
in solid wall won't give. A door that goes somewhere was never locked: just open it. Twenty-four uses. Everything near
hears it."""),
    E("ra06", "The gear trick", """
Ruth, a man showed me: a temporal gear in my left hand, a knife in my right, and hold right-click. The gear's steadiness
goes into me, at the cost of the gear and some blood. About one supply box in a hundred has a gear. Keep one for home and
one for this.
— Tom""", w="tom"),
    E("ra07", "The door that wasn't there", """
M.E.G. BRIEFING, RESTRICTED. Far from home, now and then, a grey door appears behind you where there was wall. It goes to
the Hub, one way, and it is gone in five minutes. If you want the Hub, turn round more often.
— Field Team 9 (one of us)""", w="meg"),
    E("ra08", "The Poolrooms, fair copy", """
Fair copy, ways to the Poolrooms: a cyan POOL door in the hotel, or the city's public baths (both walk back); a patch of
white tile on Level 7's seabed in the twilight zone, faintly lit; the one backyard pool in a few dozen in the Suburbs that
is still full, lit teal. The last two are one way.
— A.L.""", w="al"),
    E("ra09", "The barn wall, fair copy", """
Fair copy, Level 10 to the city. Not every barn: a little under half. The east wall, between the stalls, where the boards
look out of true and dust hangs in front of them. Walk into it. The thin spot you leave on the far side stays.
— A.L.""", mark="barnwall", w="al"),
    E("ra10", "Stash list", """
Stash list, for whoever. Sealed, untouched. I counted it twice and didn't take it, because I couldn't carry it. Marked it
for you. Food's food.
— Dez""", mark="cache", w="dez"),
    E("ra11", "Motion, by every door", """
Ways into Motion: a doll's house in the Suburbs (one in a hundred and fifty, walks back); a cinema screen in the city; a
ladder to a vent in some of The End's stockrooms; a hole in the road in the Hub's far tunnels; the deep ball pit in Level
Fun, into the castle. Be indoors by dusk."""),
    E("ra12", "The last fair copy", """
Fair copy, the last. I have walked every door I could find and written each one down. They are honest: every one leads
where it led before. None of them leads out. I am going to the Manila Room to sit at the table for a while.
— A.L.""", mark="manila", w="al"),
]))

# ============================== Scraps (flavour, when the common tracks run dry) ==============================

TRACKS.append(Track("scraps", "scrap", "Scraps", entries=[
    E("s01", "Day 40", "Day 40. Counted the ceiling tiles in one room: 117. Came back through it today. 118."),
    E("s02", "Left", "If anyone finds Marcy, tell her I went left."),
    E("s03", "B flat", "The hum is a B flat. I had perfect pitch, before."),
    E("s04", "Handwriting", "Found a room with my handwriting on the wall. I don't remember writing it. It says don't trust the room."),
    E("s05", "The light", "Three of us. Then two. Dana went to look at the light that was on in the far room. The light's still on."),
    E("s06", "Weather", "Ruth, I miss weather.\n— Tom", w="tom"),
    E("s07", "Crackers", "Ate the last crackers. They were good crackers.\n— Dez", w="dez"),
    E("s08", "Arrows", "Somebody has been moving my chalk arrows. Or I drew them wrong. Either way, I'm going right."),
    E("s09", "Things I know", "Things I know: water is real. The gear is real. The doors are honest. Nothing else is.\n— A.L.", w="al"),
    E("s10", "Keeping these", "If you're keeping these, you're keeping more than I did. Good.\n— Nell", w="nell"),
]))


# ============================== Facts the notes rely on ==============================
# Each must appear (case-insensitively) in the handbook text (gen_guide.py), README.md or docs/GUIDE.md, so that a change there makes
# this check fail until the notes are looked at again.
FACTS = [
    "5 carpet fibres + 1 flax twine", "2 wallpaper strips", "3 carpet fibres", "glass shard + wallpaper strip + carpet fibre",
    "metal bracket + wallpaper strip + 2 carpet fibres", "1 dry grass + 2 sticks", "2 dry grass + 1 stick",
    "8 planks + 1 nails and strips", "2 metal brackets", "each bottle restores 15%", "salt + powdered sulfur = 2",
    "20 metal bits = 1 ingot", "10 scrap wire = 1 copper ingot", "within 3 blocks of water", "flax twine + linen",
    "one steel tunnel door in 40", "one locked room in 150", "1 in 20", "8 blocks of concrete", "9 ingots for an anvil",
    "a temporal gear", "Almond Water", "Firesalt",
    "40 tickets a day", "200 tickets", "costs 6 tickets", "three days", "six seconds at the glass",
]


def check():
    problems = []
    keys = set()
    ids = set()
    for t in TRACKS:
        if t.id in ids:
            problems.append(f"track {t.id} twice")
        ids.add(t.id)
        if t.cls not in ("common", "rare", "scrap", "special"):
            problems.append(f"track {t.id}: class {t.cls}")
        if t.level is not None and t.level not in LEVEL_IDS:
            problems.append(f"track {t.id}: level {t.level}")
        for e in t.entries:
            if e.key in keys:
                problems.append(f"{e.key} twice")
            keys.add(e.key)
            if not e.text or not e.title:
                problems.append(f"{e.key}: no text or title")
            if len(e.text) > 560:
                problems.append(f"{e.key}: {len(e.text)} characters (keep under 560)")
            if e.mark and e.mark not in MARKS:
                problems.append(f"{e.key}: mark {e.mark}")
            for g in e.gate:
                if g not in LEVEL_IDS:
                    problems.append(f"{e.key}: gate level {g}")
    common_levels = [t.level for t in TRACKS if t.cls == "common" and t.level is not None]
    if len(common_levels) != len(set(common_levels)):
        problems.append("two common tracks for one level")
    # Facts
    try:
        import gen_guide
        guide = "\n".join(text for _, text in gen_guide.PAGES.values())
    except Exception as ex:  # (gen_guide imports the texture kit; keep the check usable without it)
        guide = ""
        print(f"gen_notes: could not read the handbook ({ex}); checking facts against the README and player guide only")
    readme = ""
    for doc in ("README.md", os.path.join("docs", "GUIDE.md")):
        with open(os.path.join(ROOT, doc), encoding="utf-8") as f:
            readme += f.read() + "\n"
    corpus = (guide + "\n" + readme).lower()
    for fact in FACTS:
        if fact.lower() not in corpus:
            problems.append(f"fact not found in the handbook or player guide: {fact!r}")
    return problems


# ============================== Output ==============================

def to_vtml(text):
    """The handbook's light markup (gen_guide.py) as rich text."""
    text = text.strip().replace("\r\n", "\n")
    text = re.sub(r"\[([^\]]+)\]\(search:([^)]+)\)", r'<a href="handbooksearch://\2">\1</a>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="handbook://\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", text)
    # A single line break inside a paragraph is only wrapping; a line starting with a dash is a signature
    paras = [p for p in re.split(r"\n\s*\n", text)]
    out = []
    for p in paras:
        lines = p.split("\n")
        body, tail = [], []
        for ln in lines:
            (tail if ln.startswith("—") or tail else body).append(ln.strip())
        s = " ".join(body)
        if tail:
            s += "<br>" + "<br>".join(tail)
        out.append(s)
    return "<br><br>".join(out)


def plain(text):
    return re.sub(r"\s*\n\s*(?!—)", " ", text.strip())


def write_config():
    data = {"version": 1, "rareChapter": RARE_CHAPTER, "tracks": []}
    for t in TRACKS:
        data["tracks"].append({
            "id": t.id, "cls": t.cls, "level": -1 if t.level is None else t.level, "chapter": t.chapter,
            "entries": [{"key": e.key, "gate": e.gate, "mark": e.mark} for e in t.entries],
        })
    path = os.path.join(ASSETS, "config", "notes.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)
        f.write("\n")


def write_lang():
    for t in TRACKS:
        LANG[f"journal-track-{t.chapter}"] = t.title
        for e in t.entries:
            LANG[f"note-{e.key}"] = to_vtml(e.text)
            LANG[f"notetitle-{e.key}"] = e.title
    LANG["journal-track-rare"] = "Folded notes"
    LANG["journal-track-dir"] = "Directions"
    LANG.update({
        "journal-title": "Wanderer's Journal",
        "journal-empty": "Nothing yet. Notes you read are kept here.",
        "journal-count": "{0} / {1}",
        "journal-read-at": "read in {0}, day {1}, {2:00}:{3:00}",
        "journal-marked": "Marked: {0}.",
        "journal-showmap": "Show on map",
        "journal-markagain": "Mark again",
        "journal-pocket": "(on the back, in pencil)",
        "journal-hotkey": "Wanderer's journal",
        "note-dialog-title": "A note",
        "note-dialog-journal": "Journal (J)",
        "note-dialog-close": "Close",
        "note-toast": "Added to your journal: {0}, {1} of {2}",
        "note-toast-dir": "Added to your journal: Directions",
        "note-chat": "{0}: \"{1}\"",
        "note-marked-again": "Marked again.",
        "note-pocket-given": "There is a folded note in your pocket. You don't remember putting it there.",
        # A note is kept when read, and remembers who read it (src/Map/WandererNote.cs)
        "note-name-read": "{0} (read)",
        "note-read-already": "You have read this one: it is in your journal.",
        "note-info-read": "You have read this one: it is in your journal. Someone else may still read it.",
        "note-info-read-other": "Read by one other wanderer; not yet by you.",
        "note-info-read-others": "Read by {0} other wanderers; not yet by you.",
        "waypoint-note-manila": "The Manila Room (a note)",
        "waypoint-note-den": "Keep out (a note)",
        "waypoint-note-manhole": "Manhole: clay below (a note)",
        "waypoint-note-barnwall": "The barn wall (a note)",
        "waypoint-note-hubdoor": "A way into the Hub (a note)",
        "waypoint-note-redroom": "The Red Rooms (a note)",
        "waypoint-note-party": "A party =) (a note)",
        "waypoint-note-runexit": "The real exit (a note)",
        "waypoint-note-hubopen": "A carved door that opens (a note)",
        "waypoint-note-staffdoor": "STAFF ONLY: one in six opens (a note)",
        "waypoint-note-fireexit": "Fire exit to {0}, storey {1} (a note)",
        "item-wanderernote-folded": "Wanderer's Note",
        "itemdesc-wanderernote-folded": "Folded small and kept dry, written in ink. Whoever wrote it meant it to last. Right-click to read it.",
        "block-loosenote-door": "Wanderer's Note (a way through)", "block-loosenote-way": "Wanderer's Note (a way out)",
        "block-loosenote-cache": "Wanderer's Note (supplies)", "block-loosenote-refuge": "Wanderer's Note (a refuge)",
        "block-loosenote-folded": "Wanderer's Note",
        "blockdesc-loosenote-door": "Someone left a note here. Right-click to pick it up.",
        "heldhelp-readnote": "Read",
        "blockhelp-takenote": "Take the note",
    })
    for k in ("way", "cache", "refuge", "folded"):
        LANG[f"blockdesc-loosenote-{k}"] = LANG["blockdesc-loosenote-door"]


def merge_lang():
    """Adds the keys to lang/en.json without disturbing its layout: existing keys updated in place, new ones appended."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    tab = "\t"
    new_lines = []
    for key, value in LANG.items():
        line = tab + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + tab + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: line + m.group(1), text, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + nl + nl + ("," + nl).join(new_lines) + nl + "}" + nl
    json.loads(text)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def write_assets():
    # The folded note: smaller, folded twice, taped, written in ink
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    paper, edge, ink, tape = (238, 232, 212, 255), (150, 140, 112, 255), (40, 52, 92, 255), (214, 200, 150, 220)
    d.polygon([(8, 9), (24, 7), (25, 23), (9, 25)], fill=paper, outline=edge)
    d.line([(8, 17), (25, 15)], fill=(205, 196, 170, 255))
    d.line([(16, 8), (17, 24)], fill=(205, 196, 170, 255))
    rng = random.Random(7240)
    for y in (11, 13, 19, 21):
        x = 10
        while x < 22:
            w = rng.randint(1, 3)
            d.line([(x, y - (x - 9) // 8), (x + w, y - (x + w - 9) // 8)], fill=ink)
            x += w + 1
    d.rectangle([14, 6, 18, 9], fill=tape)
    d.rectangle([14, 23, 18, 26], fill=tape)
    path = os.path.join(ASSETS, "textures", "item", "wanderernote-folded.png")
    import iconkit
    iconkit.finish(img, seed="item/wanderernote-folded").save(path)     # B17: lit and outlined as vanilla's icons are

    item = {
        "code": "wanderernote-folded", "class": "BackroomsWandererNote", "maxstacksize": 16,
        "texture": {"base": "item/wanderernote-folded"},
        "creativeinventory": {"general": ["*"], "items": ["*"]},
        "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
        "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
        "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
        "materialDensity": 300, "combustibleProps": {"burnTemperature": 600, "burnDuration": 3},
    }
    ground_storable(item)
    write_json(item, "itemtypes", "wanderernote-folded.json", "A rare note (gen_notes.py): read it for one of the folded notes.")

    shape = {
        "textureWidth": 16, "textureHeight": 16,
        "textures": {"paper": "backrooms:item/wanderernote"},
        "elements": [{"name": "Sheet", "from": [4, 0, 4], "to": [12, 0.12, 12], "rotationOrigin": [8, 0, 8], "rotationY": 17,
                      "faces": {"up": {"texture": "#paper", "uv": [4, 4, 12, 12]}, "down": {"texture": "#paper", "uv": [4, 4, 12, 12]}}}],
    }
    write_json(shape, "shapes", "block/loosenote.json", None)
    block = {
        "code": "loosenote", "class": "BackroomsLooseNote",
        "variantgroups": [{"code": "kind", "states": ["door", "way", "cache", "refuge", "folded"]}],
        "creativeinventory": {"general": ["*"]},
        "drawtype": "json", "shape": {"base": "block/loosenote"},
        "texturesByType": {"*-folded": {"paper": {"base": "item/wanderernote-folded"}}, "*": {"paper": {"base": "item/wanderernote"}}},
        "blockmaterial": "Cloth", "replaceable": 5000, "resistance": 0.1, "lightAbsorption": 0,
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": None,
        "selectionbox": {"x1": 0.2, "y1": 0, "z1": 0.2, "x2": 0.8, "y2": 0.06, "z2": 0.8},
        "dropsByType": {
            "*-folded": [{"type": "item", "code": "wanderernote-folded", "quantity": {"avg": 1}}],
            "*": [{"type": "item", "code": "wanderernote-{kind}", "quantity": {"avg": 1}}],
        },
        "sounds": {"place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
    }
    write_json(block, "blocktypes", "loosenote.json", "A note someone left lying here (gen_notes.py). Right-click or break to pick it up.")


def write_json(data, folder, name, comment):
    path = os.path.join(ASSETS, folder, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if comment:
            f.write("// " + comment + "\n")
        json.dump(data, f, indent="\t")
        f.write("\n")


def write_catalogue():
    lines = ["# Notes catalogue", "",
             "Generated by `tools/gen_notes.py` (edit the texts there, not here). Design: `docs/design/notes-plan.md`.", "",
             "## Writers", ""]
    for k, v in WRITERS.items():
        lines.append(f"- **{k}**: {v}")
    for t in TRACKS:
        lines += ["", f"## {t.title} (`{t.id}`, {t.cls}{'' if t.level is None else f', level {t.level}'})", ""]
        if not t.entries:
            lines.append("*(slot: entries are added when the level is built)*")
        for e in t.entries:
            meta = []
            if e.gate:
                meta.append("waits for: been to " + " or ".join(str(g) for g in e.gate))
            if e.mark:
                meta.append("marks: " + e.mark)
            meta.append("writer: " + e.w)
            lines.append(f"**{e.key}** · {e.title} · {' · '.join(meta)}")
            lines.append("")
            lines.append("> " + plain(e.text).replace("\n", "  \n> "))
            lines.append("")
    total = sum(len(t.entries) for t in TRACKS)
    lines += ["", f"{total} entries in all."]
    with open(os.path.join(ROOT, "docs", "design", "notes-catalogue.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    problems = check()
    for p in problems:
        print("gen_notes: " + p)
    if "--check" in sys.argv:
        sys.exit(1 if problems else 0)
    if problems:
        sys.exit("gen_notes: fix the problems above first")
    write_config()
    write_lang()
    merge_lang()
    write_assets()
    write_catalogue()
    counts = {}
    for t in TRACKS:
        counts[t.cls] = counts.get(t.cls, 0) + len(t.entries)
    print(f"gen_notes: {len(TRACKS)} tracks, " + ", ".join(f"{v} {k}" for k, v in counts.items()) + f"; {len(LANG)} lang keys")


if __name__ == "__main__":
    main()
