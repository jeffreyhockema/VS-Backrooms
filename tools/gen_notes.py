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
MARKS = {"door", "way", "cache", "refuge", "manila", "den", "manhole", "barnwall", "endexit", "hubdoor", "redroom", "party", "sunken"}

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
grass. Eighteen fibres make twine, so don't burn them. Crouch and cut the carpet and you lift a whole square instead,
and that's what armour is sewn from. Five fibres and a twine make a carpet bag, four slots. The floor won't mind.
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
concrete, and beneath it the ground of the world we came from. Rock and caves. Level 8 is that ground laid open, ore lying on the cave floors.
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
They are few, and deep in.
— Field Team 9 (four of us)""", gate=visited(5, 6), w="meg"),
    E("m19", "The sea", """
Level 7: water under a ceiling. Driftwood burns; fish bite. Depth costs light and steadiness, and something large
circles at the edge of sight: if your gear fails down there, surface. A ring of standing stones: dive in the middle and
you come up in the Suburbs. A cave mouth in the deep: the caves. Neither returns.
— A.L., survey""", gate=visited(6, 7), w="al"),
    E("m20", "The 9th Road", """
M.E.G. FIELD NOTICE. Level 8: stay on the 9th Road. Gravel, lamps, our waypoints, camps along it, Almond Water
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
    E("gate-class", "Down in flint", """
I went down into Level 2 in flint and pleather, the way the wanderers said. A flint knife, a spear on a stick, the seat
cover off a car for a jerkin. Two hundred steps along the mains something came after me, faster than I could run, and
it did not stop to see whether I had a light. I got the spear up. It came through the pleather at the shoulder as if the
seat cover were a bedsheet. I walked the rest of the way out with one hand on the wall.

Come back with metal on you.
— Pell""", w="anon"),
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
in, and chalk arrows on the corridor walls point there. The stairs come out in a room hung over the sea.
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
    E("l7-7", "Air down there", """
A buoy out over deep water, a rope ladder hanging from it all the way down: under it a room on the seabed, its light still
on, air trapped under its roof. Climb down, swim in under it, come up through the hatch and breathe. There's a chest in
each, and the deeper the room the better what's in it. The deep ones are where the big thing circles.
— Dez""", mark="sunken", w="dez"),
]))

TRACKS.append(Track("l8", "common", "Level 8: Cave Systems", 8, entries=[
    E("l8-1", "The road", """
M.E.G. FIELD NOTICE. Stay on the 9th Road: gravel, lamps, our waypoints, camps along it. It forks and joins
again, but follow the lamps and it runs on. Where the road meets another level it runs on through the wall.
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
boxes, cords and fallen ceiling on the floor will trip you if you sprint over them: jump them."""),
    E("run-2", "Dead end", """
Don't take the door if the hall turns beside it. The real one is at a dead end, light under it. The EXIT doors at the
bends have a dead letter in the sign and open on an empty room. Don't stop. They're still there.""", mark="door"),
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

# ---------- The Basement (experimental level, id 22; detail pass 2026-10-30): its own track, read there ----------
# After both wikis (docs/design/experimental-levels/lore/basement-brief.md): the Fandom page's endless basement (dusty
# carpet, wooden doors with noises behind them, brick stairwells that come back to the same floor, the dead and their
# smell, water that is not safe to drink, no way back up the hole without a ladder, and its Recovered Document) and the
# Wikidot account's flood (the dry patch, the drowned body that followed him, the elevator in the distance, the cutting
# about the flooded bar in Cincinnati and Gary Moors, who never resurfaced).
BASEMENT = 22
LEVEL_IDS.add(BASEMENT)

TRACKS.append(Track("lbasement", "common", "The Basement", BASEMENT, entries=[
    E("lbasement-1", "Bring a ladder", """
I broke through the floor of the Lobby with a crowbar, to see what was under the carpet. It was a long way down. The
hole's still up there, with the yellow light in it. I can see it from every room I come back to. I can't reach it. If
you're thinking of jumping into a hole in the floor anywhere: bring a rope, or better, a ladder. I didn't."""),
    E("lbasement-2", "Almonds", """
Ruth, the water down here smells almost like Almond Water. It isn't. I drank it the first day and I've been thirstier
every day since, and sick with it. The boxes were gone through long before me. If you ever find this, don't come down.
There's no water and nothing to eat, and the smell of the dead gets into everything.
— Tom""", w="tom"),
    E("lbasement-3", "Behind the doors", """
Survey, the cellar rooms. I counted the doors on one floor twice and got two different numbers. Behind some of them a
baby is crying, or someone walks up and down. Open the door and it stops, and the room is empty. Every time. I have
stopped opening them, and I have stopped counting. This is the first place I've been where the doors are not a system.
— A.L., survey""", w="al"),
    E("lbasement-4", "The stairwells", """
M.E.G. FIELD NOTICE. Brick stairwells stand in some of the dry rooms, a door in each. Climb one turn of the stairs and
you are back on the landing by the door you came in. Going down is the same. We tried both for an hour. Don't waste
your light on them. Rooms full of the dead: don't stay. The smell will choke you.
— Field Team 9""", w="meg"),
    E("lbasement-5", "The flood", """
Further in, it's all flooded, the water up to my neck and colder than anything. There's a dry patch somewhere in the
middle, a little above the rest. I lay there and something stood at the far end of the corridor the whole time. A body
in the water, bloated, a week in a lake by the look of it. It came after me. I saw an elevator in the distance. I never
reached it."""),
    E("lbasement-6", "A cutting", """
A newspaper cutting, soft with damp. CINCINNATI. FLOODED BAR CELLAR CLAIMS SIX. Six workers drowned when water filled
the basement of a bar on the night of January 6th. Five bodies have been recovered. The sixth victim, Gary Moors, has
yet to resurface. Patches of the cellar still suffer from large pools of water."""),
]))

# ---------------------------------------------------------------------------------------------------------------------
# Level 120, "Broken Servos" (experimental level, id 26; Wikidot's Level 120). Its own common track and one folded
# note, self-contained: nothing above or below depends on it.
L120 = 26
LEVEL_IDS.add(L120)

TRACKS.append(Track("l120", "common", "Level 120: Broken Servos", L120, entries=[
    E("l120-1", "Do not die here", """
M.E.G. FIELD NOTICE. Whoever dies in this level gets up again. A black shape where they fell, pixels coming off it like
dust, red where the wound was. It stands by its own things and crackles like a dead channel: in the dark, that static
is all the warning you get. It reaches further than you think. It lasts about a day, then it comes apart.
— Field Team 9 (four of us)""", w="meg"),
    E("l120-2", "One screen", """
Every computer in here is gutted or smashed. Every one but one in a cluster, maybe, and that one glows green: BOOT,
and a cursor. I pressed a key. The drive spun up and then everything was white, and the doors were black. Same screen
takes you to the same place every time. I've checked.
— Dez""", w="dez"),
    E("l120-3", "Walk one way", """
Finding: the white rooms are eleven paces square, black doors between them, a light in the ceiling that has no lamp.
Pick a direction and keep it. At the edge of the cluster there is a window, always already broken, black beyond. Step
through and you are standing at the terminal you booted. It has never failed.
— A.L., survey""", w="al"),
    E("l120-4", "The hallway", """
Ruth, the screen took me to a hallway, two wide and black as the inside of a coat. It folds back on itself, on and on.
I fell twice running. Walk it. Feel along the wall. There's a broken window at each end and it brings you back to the
screen. I counted nine hundred steps. I counted them to you.
— Tom""", w="tom"),
    E("l120-5", "Smilers in the white", """
Smilers stand about in the white rooms, love, staring at nothing, grinning at the light. They don't turn. I held my
breath and walked right past one, close enough to touch it. Don't touch it. Leave them to their light.
— Nell""", w="nell"),
    E("l120-6", "Torches", """
Dark as it is, think before you light a torch here. The things that stand where people died come for light, and for
running. Racks still blinking give enough to see a wall by. One crossing in four in the passages has a working tube.
The racks are worth breaking: copper wire, brackets, now and then a circuit board."""),
    E("l120-7", "A line of light", """
In the dark, look low. Now and then there is a line of light under a door in a server room's wall, warm, like an
office's. It is a way out: grey carpet, the lights buzzing, and the door behind you is only an office door, locked. The
hallways have one each, in the first lane or the last. You won't get back in the way you came out.
— Dez""", w="dez"),
]))

TRACKS.append(Track("rare-l120", "rare", "Folded notes", L120, chapter="rare", entries=[
    E("r-l120-1", "Ways in and out", """
M.E.G. BRIEFING, RESTRICTED. Confirmed: a door marked SERVER ROOM in the offices (the old reports say 4.3), grey steel,
green light under it, one in thousands. It lets you in beside a steel door that takes you back to it. Confirmed: the
other steel doors here, and the one in every black hallway, let you out into the offices, and not back. Unconfirmed:
an arcade machine's smashed screen in Level 25; noclipping the server room walls into Level 70; a drop of blood here
raising smaller ones, worse than the rest.""", w="meg"),
]))

# ---- Level 31, "Roller Rink" (experimental, id 24; docs/design/experimental-levels/31-plan.md). Its own block: the
# level's id and its track. Wikidot's lonely diarist (J.) and Fandom's details, in the notes' voices.
L31 = 24
LEVEL_IDS.add(L31)
TRACKS.append(Track("l31", "common", "Level 31: the Roller Rink", L31, entries=[
    E("l31-1", "The wooden door", """
A wooden door in a brick wall, Level 3, and music behind it. Pop music, the kind from home. I pushed it open and I was
in the roller rink from my old town: the lights, the wood, the smell. I'm so tired. I'm going to find somewhere the
lights aren't so bright and the arcade isn't so loud, and sleep.
— J."""),
    E("l31-2", "Free hot dog", """
The food court gives you food for nothing. Ask the faceless one behind the counter: pizza, wings, a foot-long. The soda
fountain pours Almond Water. Don't leave a crumb lying about: it cleans up after you, slowly, looking at you, and won't
serve you again for a day.
— Dez""", w="dez"),
    E("l31-3", "High score", """
There's a machine at the arcade door: press the blue button, get a green card. The games don't care if you have one.
Found an old box cabinet, girders and barrels, the kind I played as a kid. Beat my old high score twice. It didn't
feel like anything the second time.
— J."""),
    E("l31-4", "The Coach", """
A faceless man in a striped shirt behind the skate rental counter. Says his name's Coach. He knew mine by the second
time and still does. He gave me skates, quick on the boards and the concrete and useless on carpet, and taught me to
spin. He says don't stay too long. I don't know why he says it so often.
— J."""),
    E("l31-5", "Shadows", """
M.E.G. FIELD NOTICE. Level 31: Class 1, safe. No Hounds confirmed. Black figures reported standing still in the dark
rooms, the cinema and the cold HVAC rooms; all vanish on approach and none has ever moved. Treat as paranoia. The
staff Facelings are docile and cannot be harmed. Do not take the rental skates out of the level.
— Field Team 9""", w="meg"),
    E("l31-6", "Nothing feels good anymore", """
Arcade, skating, food court, cinema, repeat. Nothing feels good anymore. Coach found me in the cinema again and said
it's time to go, there's a white door with a 70 on it behind the arcades, a door marked Employees Only in the food
court. I said I'm not ready. I just want to feel at home again. If you're reading this, listen to the Coach.
— J."""),
]))

# (The links round, 2026-10-31: wanderers in Levels 2, 3 and 6 talk of the wooden door into the rink, with music behind it.
# One note each, appended to those levels' own tracks under the level's own keys.)
for _host, _entry in (
    ("l2", E("l31-in2", "Music in the pipes", """
Down a blind tunnel, a wooden door in the concrete. Wood, down here. Pop music behind it, the bright sugary kind with
handclaps, so faint I took it for the pipes. I didn't open it. Pell would have, and Pell would have said what's the worst
that could happen, and look.
— Dez""", w="dez")),
    ("l3", E("l31-in3", "A door in the brick", """
M.E.G. FIELD NOTICE. A plain wooden door has been reported in the brick walls of Level 3, pop music audible through it.
It opens on Level 31, a roller rink: Class 1, safe, food served free. The door leads back. Sightings are rare. Mark it if
you find one. Out of 31: the revolving doors, one way, to the Suburbs, the fields or the city.
— Field Team 9""", w="meg")),
    ("l6", E("l31-in6", "Something to dance to", """
In the dark, music. Something bright and silly, a girl singing over handclaps, coming through a wall. I felt my way
along it to wood, a handle, warm. I stood there an hour listening before I opened it. There was light on the other
side, and a roller rink. Go toward the music.""")),
):
    next(t for t in TRACKS if t.id == _host).entries.append(_entry)

# ============================== Level 52, the Greenfield Campus (experimental, id 23) ==============================
# (One self-contained block: the level's id, its track. Experimental levels are reached only by the cheats menu for now.)

L52 = 23
LEVEL_IDS.add(L52)

TRACKS.append(Track("l52", "common", "Level 52: the Greenfield Campus", L52, entries=[
    E("l52-1", "Four digits", """
Every door here has a plaque, four digits, nothing else. I've walked enough of them to read it: the first two count the
rooms along that building, the third is the floor, the last is the building. No subject on any door. No campus name
anywhere, on anything. Somebody went to a lot of trouble to say nothing at all."""),
    E("l52-2", "Lights off", """
Ruth, the corridors here are lit and humming, every one of them, all the time. The classrooms never are. I tried every
switch I found and nothing comes on, not the lights, not the old televisions. The windows light them well enough.
There's a sky outside, love. Blue, all the time. I sat in the grass for an hour.
— Tom""", w="tom"),
    E("l52-3", "The fence", """
Finding: each campus is fenced on its own, a concrete barrier with chain-link on it, too high to climb. No gate. There
is a wide gap in the middle of every side, and a narrow one where a section was set down out of line. A gravel road runs
from each gap on to the next campus. Nothing on the roads, nothing in the grass. Out on the empty plains a fence runs
straight for a hundred paces and fences nothing.
— A.L., survey""", w="al"),
    E("l52-4", "False alarms", """
Barry campus, the blue one they called the Asylum. Traders kept it once: you can tell by the warehouse, shelving and
pallets and the medical cabinets, and now and then a case nobody opened. The alarms still go off, for nothing, every few
minutes. Don't run. The fountains on the corridor walls still give water, and the canteen's machines still give
Almond Water. Nothing in the food stands, though.
— Dez""", w="dez"),
    E("l52-5", "Fresh paint", """
They tell you it's a paradise. Look behind the fresh paint in the corridors at Barry and you'll find the holes. The
Partygoers came through here twice, three thousand people, then seven hundred more when the M.E.G. tried to take it
back. They say it's over. Maybe. Turner campus has beds in its classrooms now, two floors of them, and most are made."""),
    E("l52-6", "Top floor", """
M.E.G. NOTICE, MARSHALL DAVID CAMPUS. Newcomers land in or near this building. The top floor was our outpost; the offices
are abandoned and the files are gone. Take nothing you cannot carry down. The stairs are in the corners of the quad.
Reported ways out: a door that opens on somewhere else, most often Level 53. Unconfirmed: noclipping in this building.
— Field Team 9""", w="meg"),
]))

# Level 52's ways in and back (the links round, 2026-10-31): the doors you came in by, told in the level; and one note at the
# end of each host's own track, told where the way in is (the city's high schools, Level 4's emergency exits)
next(t for t in TRACKS if t.id == "l52").entries.append(E("l52-7", "The doors you came in by", """
Came in off the street through a school's doors, into a lobby full of lockers, and the doors behind me showed grass. An
hour later I walked back out through them, and I was on the sidewalk again with HIGH SCHOOL over my head. Any other door
here is only a door. The ones you came in by remember where you came from. Mark them.
— Dez""", w="dez"))
next(t for t in TRACKS if t.id == "l11").entries.append(E("l52-in-11", "High school", """
Finding: now and then, among the shops and apartment blocks, a brick school three or four storeys high, HIGH SCHOOL in
brass over a pair of steel doors. Not one of them is a school inside. Through the doors is a lobby with lockers, and
through the lobby's glass, green hills under a blue sky. The same doors bring you back. I found two in a week's walking.
— A.L., survey""", w="al"))
next(t for t in TRACKS if t.id == "l4").entries.append(E("l52-in-4", "Emergency exit", """
Ruth, there's a steel door here under a green EMERGENCY EXIT sign, in a wall with nothing behind it. I pushed the bar.
A school corridor, lights on, lockers, and at the end of it doors onto grass and a sky so blue I had to sit down. I went
back out the same doors and I was under the sign again. I'm going back tomorrow. You'd like it there.
— Tom""", w="tom"))

# ---------- Level 23, the Petrified Garden (experimental level 28; its own block: tools/gen_23.py writes these keys into
# the level's block of en.json, this script keeps them up to date in place) ----------
L23 = 28
LEVEL_IDS |= {L23}

TRACKS.append(Track("l23", "common", "Level 23: the Petrified Garden", L23, entries=[
    E("l23-1", "Under the leaves", """
No day here and no night. There's a star up there that never moves, somewhere over the leaves, and under them it might as
well not be. Where the light gets through a hole in the canopy the ground's softer and there's grass. Walk from one of
those to the next and you'll always see what's coming."""),
    E("l23-2", "Sorry", """
Ruth, the caves under the trees glow. Little lights hanging from the roof, every colour, and every one of them whispers
sorry. Sorry, sorry, sorry. I told them it was all right. I said it out loud. They didn't stop.
— Tom""", w="tom"),
    E("l23-3", "Don't say it", """
Faces in the bark, head high, eyes shut. They're asleep or they're dead or they're waiting. Whatever you do, don't say
"it's only a matter of time" near one. Some clown did, for a laugh. The whole tree screamed like a chainsaw going through
it and he can't hear on that side any more.
— Dez""", w="dez"),
    E("l23-4", "Four ruins", """
Survey, Level 23. Four ruins in the deep caverns, each a wonder of the world built the wrong shape: the Lighthouse a
stepped pyramid, the Pyramid a sphere, the Colosseum square, the Parthenon a triangle. Latin on the walls, cut in a hurry.
The plaque on the sphere asks the Great Gardener's forgiveness. Nothing in them looks newer than a thousand years.
— A.L., survey""", w="al"),
    E("l23-5", "Base Seedling", """
M.E.G. FIELD NOTICE. Base Seedling is in a glow room off the roots: take the tunnels down until the light goes warm. We
trade. Water we have; food we do not, so bring your own. Our way home is the hollow tree in the middle of camp: climb
it, and you come out of a green tree in the Poolrooms that brings you back. Do not touch the Green Giants.
— Field Team 9""", w="meg"),
    E("l23-6", "The Heart", """
There's a pool in the middle, love, where the big green trees stand round it, and the light comes straight down on the
water. Cleanest I've had since the fields. They say if you swim down far enough it takes you to the sea. I only drank.
— Nell""", w="nell"),
    E("l23-7", "The tree in the water", """
Found a tree in the Poolrooms. Green bark, wider than a room, growing up through the tile like it was there first. I
climbed into the hollow to sit somewhere dry and kept climbing, up in the dark, and came out of another trunk in this
place. The trunk I came out of is just a trunk. Don't climb in unless you mean it.
— Dez""", w="dez"),
]))
# (And one in Level 37's own track, where the trees are: a key of this level's, at the end of that track)
next(t for t in TRACKS if t.id == "l37").entries.append(E("l23-p1", "Green bark", """
Out past where anyone goes, a tree is growing up through the floor: green bark, roots through the tile, straight up
through the ceiling, hollow at the foot. Nothing grows here. Whoever climbs into it doesn't come back out of it.
— A.L., survey""", w="al"))

# ---------- Level 47, the Adderwood (experimental level 30; its own block: tools/gen_47.py writes these keys into the level's
# block of en.json, this script keeps them up to date in place) ----------
L47 = 30
LEVEL_IDS |= {L47}

TRACKS.append(Track("l47", "common", "Level 47: the Adderwood", L47, entries=[
    E("l47-1", "Fog by day", """
The fog comes down every morning and lifts every night, regular as a clock. All day you can't see thirty steps and the
sun never once shows through it. Then it goes, all at once, and there's the moon. Too big. Wrong face. Not our stars
either. I sat under it till the fog came back and didn't sleep."""),
    E("l47-2", "Not one snake", """
Snakes everywhere here, in the leaves, on the logs, across the trail. Leave them be. Not one. Not by accident, not
because it went for your boot. A kid in our group stepped on one and it bit him and he stamped on it. Then the birds
stopped. Then it came: red, the size of a train, and faster than any of us. We didn't see him again.
— Dez""", w="dez"),
    E("l47-3", "The black dogs", """
Ruth, there are dogs here at night. Big as ponies and black as the dark between the trees. One finds you and just
watches you, close, for hours, and howls, and you hear the others answer from miles off. Don't run. Climb the tallest
tree you can and sit there till it's light. They're gone with the fog. They always are.
— Tom""", w="tom"),
    E("l47-4", "The trail", """
Survey, Level 47. Nothing here can be mapped: what I don't keep my eye on isn't where I left it. The one exception is a
trail, trodden bare, that winds and winds and does not move. A stone post with a snake cut into it stands beside it
every few hundred steps. Followed inward it ends at a glade. In the glade is a manor house, or a ring of standing stones.
I looked a long time. I think it is both.
— A.L., survey""", w="al"),
    E("l47-5", "Red robes", """
Met three of them on the trail, love. Red hoods, white masks, polite as anything. Said they could go anywhere, any level
they liked, steer the trail to any door. One started on about a way home, the real home, and the others turned on him
like I wasn't there. I said no thank you and walked the other way. You do the same.
— Nell""", w="nell"),
    E("l47-6", "Water, food, ways", """
M.E.G. FIELD NOTICE. Level 47: the streams are safe to drink. Mushrooms are the food here; learn them (the red one with
white spots and the pale green one are poison). The elk will kill you; don't try them without a weapon that drops one in
a blow. No-clipping out is easier here than anywhere: the hollows of dead trees, mostly. A huge green-barked tree, if you
find one, goes somewhere of stone.
— Field Team 9""", w="meg"),
    E("l47-7", "It puts things back", """
I made a fire last night. This morning: no ashes, no stones, no fire, just the moss as if nobody had ever sat on it.
The tree I cut a mark on doesn't have a mark. Keep what matters on you. Whatever you leave, and look away from, is the
forest's again."""),
]))
# (And one in Level 10's own track, where its ancient dead trees stand: a key of this level's, at the end of that track)
next(t for t in TRACKS if t.id == "l10").entries.append(E("l47-p1", "The old tree", """
Out past the last farm, on a field's edge, a dead tree, grey as bone, older than anything else in the fields and bigger
than any of the oaks. Hollow at the foot. It smells of rain in there, and moss, and the air is cold. I didn't go in. The
man I was with did, and he didn't come out of it, and the hollow was empty when I looked.
— A.L., survey""", w="al"))

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
for three hours, then they come in. Real exit marked.""", mark="door"),
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

# ---------------- Level 15, "Futuristic Halls" (experimental, id 27; detail pass 2026-10-30): its own block ----------------
# Both wikis' Level 15 (docs/design/experimental-levels/15-plan.md): the white wall at the edge of Level 10's field and its
# door that goes, the hum and the ticking in the dark, the codes on the vents, the dead in lab coats, the machine rooms,
# the Robo-Men in the dark (ours), the star door. No living base: isolation and what the dead left.
L15 = 27
LEVEL_IDS.add(L15)
TRACKS.append(Track("l15", "common", "Level 15: the Futuristic Halls", L15, entries=[
    E("l15-1", "The white wall", """
Out in Level 10's fields there is a white wall too high to climb, running out of sight both ways, and a small steel door
in it. I went in and marked it on my chart. The door I came out beside is in a hall wall here, and it does not open from
this side. There is one like it in nearly every block of these halls, and none of them open. Write it down: the ways
into this place close behind you.
— A.L., survey""", w="al"),
    E("l15-2", "The hum", """
Ruth, it hums. Day and night, everywhere, like the whole place is one machine and we're inside it. Where the lights
are dead it stops humming and starts ticking, slow, like a heart. It gets slower the longer you stay. I didn't stay to
hear it stop. Neither should you.
— Tom""", w="tom"),
    E("l15-3", "Letters on the vents", """
Letters and numbers on the walls by the vents, in marker, and on the doors in black paint. H15. e03. eco3x10c. Someone
had a system: H is a lab, e is a store, I think. I followed the e's for two days and found lockers already open and a
box somebody had torn before me. Nothing here grows and nothing comes back. Carry water in.
— Dez""", w="dez"),
    E("l15-4", "Lab coats", """
M.E.G. FIELD NOTICE. Bodies in lab coats throughout Level 15, months dead. Makeshift spears of pipe and glass beside
some of them. Several have gunshot wounds; no firearm has been recovered anywhere in the level. Do not assume you are
alone. Do not assume you are not.
— Field Team 9""", w="meg"),
    E("l15-5", "The machine rooms", """
The gates to the machine rooms are rolled up and the hand scanners are dead, so walk in. Most of the machines are
shells. A few still run, lit and humming, and one somewhere makes steel rods all day for nobody. Break the dead ones
for wire and a little copper. The burnt ones give you next to nothing."""),
    E("l15-6", "The dark squares", """
Love, the power's out in patches a few hundred paces across. Black as anything in there, and the air goes thick: you'll
feel it in your head before long. Something walks in the dark, metal and slow, like a man built out of a stove. I heard
it before I saw it. Go round.
— Nell""", w="nell"),
    E("l15-8", "ESCAPE", """
M.E.G. FIELD NOTICE, UNCONFIRMED. In a few control rooms one panel on the display wall has its button lit, red, under
the word ESCAPE, a green lamp beside it. Pressed, a locked security gateway in the same room rolls up onto dark. Two
personnel who went through were later met in Level 3. One way. Every other ESCAPE panel is dead.
— Field Team 9""", w="meg"),
    E("l15-9", "An office", """
Found an office in here. Carpet, filing cabinets, a desk, like somebody cut a piece out of Level 4 and set it down in
the white. In the middle of it a staircase goes down through the floor. I went down it. I'm writing this in Level 4.
Don't ask me to find it again; I tried.
— Dez""", w="dez"),
    E("l15-10", "Orange glass", """
Ruth, one of the machine rooms has a pane in its glass wall that's orange, like there's a street lamp behind it and a
city past that. There isn't, I walked round. I broke it anyway. If you find this, I'm in the city, I think. It's dark
there, and nobody's in the windows.
— Tom""", w="tom"),
    E("l15-11", "What they say at the camps", """
Talk at the camps, none of it seen by anyone I've met: a blue door; a hospital door; a
door marked THE ARCHIVES; a puddle of Almond Water you slip on in a narrow hall. All of them lead somewhere better. So
does everything, at the camps."""),
    E("l15-7", "Two hours out", """
Two hours out from where I camped, past the dark squares: an empty machine room, and in the middle of it a doorframe
with no door and no wall, and in it a night sky and one small blue star. Cold came off it. I didn't go through and I
didn't stay. Nobody I've met has come back from that side.
— Dez""", w="dez"),
]))
TRACKS.append(Track("rare-l15", "rare", "Folded notes", L15, chapter=RARE_CHAPTER, entries=[
    E("r-l15-1", "The halls, fair copy", """
Fair copy, Level 15. Main halls every hundred and twenty-eight paces both ways, lit, a steel rib every eight. Between
them the wings: corridors cut across and across, rooms in between, a door each onto a corridor. Service passages grey
and low and loud with air. One square in six without power. Bodies, camps, no one living in forty days. Ways out: none
I found. The M.E.G. claim three: a lit ESCAPE button, an office stair, an orange pane.
— A.L.""", w="al"),
]))
# Level 15's ways in, talked of in the levels they lie in (our own keys, added to those levels' tracks)
next(t for t in TRACKS if t.id == "l10").entries.append(E("l15-h10", "The white wall", """
Love, past the last farm I came on a wall across the fields, white as a fridge and three times my height, running both
ways till the haze took it. Lights set in it like a hallway's, and one small steel door with a lit frame. I didn't open
it. Anything that clean out here isn't for us. Leave it be.
— Nell""", w="nell"))
next(t for t in TRACKS if t.id == "l3").entries.append(E("l15-h3", "A clean light", """
Some of the doors in here have nothing behind them, and one I found had white light under it, cold and clean, nothing
like the bulbs here. The handle bit me, a real jolt, and I let go. The fellow with me didn't. The door's still there.
He isn't."""))
# ---------------- (end of Level 15's block) ----------------

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

# ============================== Level 36 "Airport" (experimental, id 25; detail pass 2026-10-30) ==============================
# Its own track and one folded note; the spots are WorldLayout.L36NoteSpots (the Travel Agency's booths and desks, the Lost and
# Found offices, Gate C32). What they say of the level's rules is src/Regions/L36System.cs and its handbook page.
L36 = 25
LEVEL_IDS.add(L36)

TRACKS.append(Track("l36", "common", "Level 36: the Airport", L36, entries=[
    E("l36-1", "Brought in by the belt", """
You come in on a baggage carousel, like luggage. Everyone does. Behind it is the only wall anybody has found the end of,
carousels coming out of it all along, north and south as far as you care to walk. The bags on the belts are nobody's
now. Ten rounds and they go to Lost and Found; the offices along the wall are full of them.
— Dez""", w="dez"),
    E("l36-2", "The numbers", """
The screens over check-in and at every gate give no times. A flight, a level, a gate, and a number counting down that is
not seconds or anything else. Under a thousand the gate is boarding. At nothing the plane goes. I stood at a G gate
from a hundred thousand down to nothing. My watch stopped the moment I came in. Right-click a screen for the gates near it.
— A.L., survey""", w="al"),
    E("l36-3", "Flights", """
M.E.G. FIELD NOTICE. Boarding is real. Use the jet-bridge door by the window while its gate is boarding and you are in the
cabin of the plane parked behind it. You can step off by the same door until it goes. Stay aboard when the count runs
out and you fly for a minute and land where the gate's own screen says: every gate flies to one level, the same place
every time. Logged so far: the city, the Suburbs, the Poolrooms, the fields of 10, 3999 and 188. Nothing flies back.
— Field Team 9""", w="meg"),
    E("l36-4", "Gate C32", """
Ruth, a woman at C32 gave me soup. There are about a hundred and fifty of them, bedrolls between the seats, waiting on
flight 1784XBA8JLP to Level 186. The number on their screen has nine digits. She says she'll see the valley. When I went
back the holdroom was empty, their bedding still laid out. I didn't have the heart to do the sums.
— Tom""", w="tom"),
    E("l36-5", "Signs", """
Never follow an EXIT sign here. I followed one for a day and it hung over a doorway into check-in, same as the last.
Further in the signs argue with each other. A lit sign with nothing on it means no good: the lights die past it. Go back
to the last sign that made sense. Things stand in the dark out there, and only there.
— Dez""", w="dez"),
    E("l36-6", "No sleep", """
Ruth, you can't sleep here. I lay down on a bench and shut my eyes for what felt like hours and opened them in the same
second. I'm not tired, though. Nobody is. You still have to eat and drink: the machines and the fountains in the halls
are free. Don't touch what's left on the food court tables.
— Tom""", w="tom"),
    E("l36-7", "The edge", """
The floor is so clean it hurts, love. Far out, every way but back toward the carousels, the walls go to static, like a
television nobody switched off, and you feel yourself thinning while you stand in it. They call it the Absolute Limit.
Don't go and look.
— Nell""", w="nell"),
]))

TRACKS.append(Track("rare-l36", "rare", "Folded notes", L36, chapter=RARE_CHAPTER, entries=[
    E("r-l36-1", "Ways in, as told", """
Ways into 36, as they were told to me: a door under a sign with an airplane on it, in the city or out in the Suburbs,
where no door should be. That one I walked: it comes out by the carousels, and back the same way. The rest I have not: a
door in one of the city's apartment blocks; luggage that falls; a train from somewhere called the Metro. Ways out: the
gates, each to its own place; a restroom sink, if you can bear to put your head under it, to the Poolrooms; the glass
doors of a hotel, they say.
— A.L.""", w="al"),
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


# ============================== Level 73, the Redlands (experimental, exp/73) ==============================
# Self-contained: the level's id, its common track and one folded note. Nothing above changes for it. (Notes lie in the
# castle and by the packs dropped on the fields; WorldLayout.Level73 puts them down as loose notes.)

L73 = 21
LEVEL_IDS.add(L73)

TRACKS.append(Track("l73", "common", "Level 73: the Redlands", L73, entries=[
    E("l73-1", "Don't look around", """
I did not look around. I think that is why I am writing this. The castle is on the hill, and there is stone under your
feet if you find the path: follow it up. Don't stop, not for anything you hear. At the door, bang with both fists until
it opens. It will open."""),
    E("l73-2", "Wet ground", """
The ground here is wet and it isn't water. I struck a match to see what I'd stepped in and half the island turned
round. Don't light anything out there, not a match, not a torch. Not ever.
— Dez""", w="dez"),
    E("l73-3", "The moon", """
Ruth, the moon went out for what felt like an hour. Something breathed against my sleeve the whole time and never
touched me. When the moon came back there was a man on the hill with chains for arms, and the something was in pieces
round him. He said "inside, child", and I went. They gave me soup.
— Tom""", w="tom"),
    E("l73-4", "Survey, Level 73", """
One island; sea all round, nothing on the horizon. One building: the Silver Castle, three floors and an attic, a guest
room at each end of every floor with two beds. The table sets itself about every four hours, a place for each of us.
The barrels in the bathrooms are always warm. He cannot see. He has never once raised a hand to one of us. No exits.
— A.L., survey""", w="al"),
    E("l73-5", "Thirty-seven", """
Thirty-seven, they say, whenever anyone asks how many of us there are. There is nobody here but us. I have counted the
beds: twelve in the guest rooms. They never say thirty-eight, even when someone new comes in at the door."""),
    E("l73-6", "The fuel", """
Hound is the fuel, love. Don't ask about the stew. Eat it anyway; there's always enough. And keep off the last stair at
the top: the attic is his, and the chain on that door is there for us, not for him.
— Nell""", w="nell"),
]))

TRACKS.append(Track("rare-l73", "rare", "Folded notes", L73, chapter=RARE_CHAPTER, entries=[
    E("r-l73-1", "Do not come", """
M.E.G. NOTICE, RESTRICTED. Do not mount expeditions to Level 73. It is entered by lingering near the Gloom in Level 9.1,
and reportedly from Levels 14 and 6. No exit is known. Its keeper has asked us, through the last team to reach the
castle, to call off the search: "They won't be able to get out. They'll just be trapped with the rest of us."
— Field Team 9""", w="meg"),
]))

# Level 73's ways in, as wanderers talk of them in the levels they lie in (exp/73 links): one note at the end of Level 9's
# track (the Gloom) and one at the end of Level 6's (its deepest dark), with this level's own keys. Nothing else in either moves.
next(t for t in TRACKS if t.id == "l9").entries.append(E("l73-l9", "The Gloom", """
There's a yard a few streets over where the dark just sits. Not shadow: dark, like ink poured on the grass, and my torch
stopped at the edge of it. The boy I was walking with stood in it for a bet. After a minute he said he could hear a
heart beating, and then he wasn't there. M.E.G. calls it the Gloom. They say it lets you out on an island with a castle on it. Walk round it.
— Nell""", w="nell"))
next(t for t in TRACKS if t.id == "l6").entries.append(E("l73-l6", "Deeper", """
Some of the dark down here is deeper than the rest. You can feel it, like a held breath. I sat down in it once to rest,
light out, and after a long while I heard a heart beating under the floor. I lit up and ran. They say the ones who
don't light up wake on an island under a full moon. Keep a light going."""))


# ---------- The Basement's way in (links round, 2026-10-31): one folded note in the Lobby, self-contained ----------
# "Breaking through the floor of most levels" (Fandom); the Wikidot account starts with a man breaking through the floor of
# Level 0. Appended to the Lobby's folded notes (its own key), after the two there: a cracked patch of floor that gives way.
next(t for t in TRACKS if t.id == "rare-l0").entries.append(E("r-l0-basement", "Soft floor", """
Some of the floor out here is cracked, a patch a few steps across, sunk in the middle as if there's nothing under it.
Don't stand on it. Kel did. It went from under him and he was gone, and I heard him land a long way down. He called up
for a while about rooms and doors and a smell. I had no rope. The cracks are still there. The hole isn't."""))


# ============================== Level 14, the Hospital (experimental, id 29; exp/14) ==============================
# Self-contained: the level's id, its common track, its folded notes (the T.14.R.G.'s two transcripts, then a fair copy), and
# one note each in the hosts' tracks (Level 0's EMERGENCY EXIT door, Level 15's MEDICAL CENTER door), with this level's own
# keys. After Fandom's Level 14 only (docs/design/experimental-levels/14-plan.md, sections 1-2): what the page says is told
# as seen, the rumours as rumours. The folded notes lie in the research group's rooms (WorldLayout.L14Plan.NoteSpots).
L14 = 29
LEVEL_IDS.add(L14)

TRACKS.append(Track("l14", "common", "Level 14: the Hospital", L14, entries=[
    E("l14-1", "Reception", """
I came through an EMERGENCY EXIT door in the Lobby and it turned me out into a waiting room: an oval desk, a lamp, a few
chairs, magazines about nothing I recognise. Behind me a revolving door of stained glass, and through every pane nothing
at all. Not dark: nothing. The room's door let me out into a hall and has not opened from the hall side since. These
rooms are one way. Take what is on the desk before you leave.
— A.L., survey""", w="al"),
    E("l14-2", "Footsteps", """
Ruth, there are footsteps here all the time. Far off, down some other hall, never closer and never further. And
whispering, just under hearing, like the next room is full of people talking about me. I keep turning round. There's
never anyone. It smells of antiseptic and of something gone off underneath it. I've started answering the whispers. I know.
— Tom""", w="tom"),
    E("l14-3", "The windows", """
Love, the wards have windows, the only ones I've found, and every one is broken and there's nothing past it. Not night:
black, flat as paint. The beds are made and the drips still hang, a cup on every table, as if everyone stepped out a
minute ago and never came back. In the maternity rooms there are teddy bears in the cots. Folk say to hug one. I didn't.
— Nell""", w="nell"),
    E("l14-4", "Surgery", """
Surgery rooms are behind shut doors, and harder to find than the wards. Mostly a bed tipped head-down and a big lamp
over it. Some have gone green, mould up the walls and vines over the floor, and on one shelf a rack of test tubes with
moss growing up out of whatever's in them. Don't drink it. And keep off the trolleys: one threw a scalpel at me. Threw
it. The old equipment wakes up sometimes, all on its own.
— Dez""", w="dez"),
    E("l14-5", "Look first", """
M.E.G. FIELD NOTICE. Some rooms in Level 14 are contaminated. Their steel doors carry a trefoil and a square window, a
green light through the glass, and they do not open; some of those rooms have a second, ordinary door on another
corridor. Do not go in. The air makes you sick and confused, and it stays with you. Look through a window before you
enter any room. Reports that some windows are entities in disguise are unconfirmed.
— Field Team 9""", w="meg"),
    E("l14-6", "Cracks", """
Watch the floor. Before it goes, it cracks: the tiles split in lines and the patch sags like wet card. When it creaks
under you, don't stop to look. Run. Mara stopped to look. The floor went and she went with it, and I heard her land a
long way down, and nothing after. A man at the last camp swore the ones who fall through wake on a red island under a
full moon, a castle on a hill. I'd sooner believe that than the other thing."""),
    E("l14-7", "Patient Zero", """
M.E.G. FIELD NOTICE, RESTRICTED. Rooms of rusted stretchers stacked on each other, shattered marble, blood down the
walls, cabinets of knives: the torture chambers. They mean the Hunter is near. You will feel it first: dread, the air
cold and thick with smoke. Leave the room and run, and do not look at it: once it meets your eyes, it does not stop.
It lets worms go from its arms, fast, all teeth; their bites burn. Antibiotics from the reception desks stop it.
— Field Team 9 (three of us)""", w="meg"),
]))

TRACKS.append(Track("rare-l14", "rare", "Folded notes", L14, chapter=RARE_CHAPTER, entries=[
    E("r-l14-1", "Transcript #1", """
T.14.R.G., THE LEVEL 14 RESEARCH GROUP. TRANSCRIPT #1: MEMBERS. Objective: to gather as much information as possible
about Level 14. Dwight M. Williams, project leader. Researchers. Security guards. Containment Chamber Contractors.
Chemical Sample Collectors and Containers. Twenty members in all; a stockpile of supplies for the duration. (The rest
of the list is water-stained past reading. One name in the researchers' column survives: Lawrence R. Afton.)""", w="meg"),
    E("r-l14-2", "Transcript #2", """
T.14.R.G. TRANSCRIPT #2. EXPERIMENT #1: GONE WRONG. Subject: Lawrence R. Afton, 25, injected with Compound 14. Within
30 minutes, distress; then aggression. His skin had turned pitch black, and octopus-like tentacles started to stretch
out of his body. His eyes became bloodshot, a vacant, almost lifeless gaze. He seemingly could sense whether someone was
nearby. Only 4 out of the 20 team members escaped the level alive. The survival difficulty of Level 14 has been
increased by three.
— Dwight M. Williams""", w="meg"),
    E("r-l14-3", "The hospital, fair copy", """
Fair copy, Level 14. Halls four wide, every sixty-four paces both ways; between them the wings, a department each:
wards, intensive care, psychiatry, maternity, surgery, stores. You arrive in a reception room and cannot go back into
it. Ways out, one way and rare: a futuristic door of steel and lit seams, to Level 15; a red EXIT door, to Level !; a
floor that gives way, to I do not know where. Unconfirmed: arrows on the floor to a main exit; a glowing window; a
teddy bear held tight; walking too far in.
— A.L.""", w="al"),
]))

# Level 14's ways in, talked of in the levels they lie in (our own keys, at the end of those levels' tracks)
next(t for t in TRACKS if t.id == "l0").entries.append(E("l14-h0", "EMERGENCY EXIT", """
There's a door in one of the yellow walls out here that has no business being there: grey steel, a push bar, a green
running man over it, EMERGENCY EXIT. You smell it before you see it, antiseptic, like a hospital corridor at night. My
brother pushed the bar. It let him through and swung shut, and he didn't come back out. I didn't follow. The smell is
still on my coat."""))
next(t for t in TRACKS if t.id == "l15").entries.append(E("l14-h15", "MEDICAL CENTER", """
M.E.G. FIELD NOTICE. Beside some of Level 15's medical bays: a futuristic door marked MEDICAL CENTER. It smells of
antiseptic and decay, which nothing else in these halls does. Personnel who walked through it came out in a hospital
waiting room in Level 14, a Class 4 level, and could not return the way they came. Do not use it.
— Field Team 9""", w="meg"))
# ---------------- (end of Level 14's block) ----------------


# ============================== Facts the notes rely on ==============================
# Each must appear (case-insensitively) in the handbook text (gen_guide.py), README.md or docs/GUIDE.md, so that a change there makes
# this check fail until the notes are looked at again.
FACTS = [
    "5 carpet fibres + 1 flax twine", "2 wallpaper strips", "18 carpet fibres", "glass shard + wallpaper strip + carpet fibre", "glass shard + carpet fibre + stick",
    "metal bracket + wallpaper strip + 2 carpet fibres", "1 dry grass + 2 sticks", "2 dry grass + 1 stick",
    "8 planks + 1 nails and strips", "2 metal brackets", "each bottle restores 15%", "salt + powdered sulfur = 2",
    "20 metal bits = 1 ingot", "10 scrap wire = 1 copper ingot", "within 3 blocks of water", "flax twine + linen",
    "one steel tunnel door in 40", "one locked room in 150", "1 in 20", "8 blocks of concrete", "9 ingots for an anvil",
    "a temporal gear", "Almond Water", "Firesalt", "6 carpet squares + 2 flax twine + 4 wallpaper strips",
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
        guide = "\n".join(gen_guide.all_texts())
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
        "waypoint-note-sunken": "Air under the sea (a note)",
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
