using Atp = Backrooms.Worldgen.WorldLayout.L73AtticPart;
using Layer = Backrooms.Worldgen.WorldLayout.L73Layer;
using Part = Backrooms.Worldgen.WorldLayout.L73Part;
using Room = Backrooms.Worldgen.WorldLayout.L73Room;
using Thing = Backrooms.Worldgen.WorldLayout.L73Thing;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 73, "The Redlands" (experimental, kept as level 21), laid out in WorldLayout.Level73.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>), which is the sea's surface. The island is crimson earth over basalt, black rock on
/// its outcrops and hilltops, ash sand on the beach and blood-red mud in the gullies, old bones strewn over it; the seabed is
/// basalt sand and gravel under still water. The Silver Castle is pale silver ashlar: curtain walls seven high with
/// battlements, towers ten, banners of a silver heart with ram's horns on black hung inside and out; the keep three storeys
/// under a flat roof with turrets and a chimney stack, and on the roof the attic under slate with its balcony. Inside,
/// carpet, damask, tiles and boards, the Level 5 hotel's furniture, iron sconces, a hearth of embers, the mahogany table
/// with a place set at every seat, the bathrooms' barrels of warm water, paintings of the Frontrooms, and red velvet
/// curtains over boarded windows. The keep's door is a pair of studded leaves that open only to banging
/// (Regions.L73System). The rim of the region is a cliff of basalt. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l73Earth, l73Rock, l73Ash, l73Mud, l73Silver, l73Basalt, l73Sand, l73Gravel, l73Ashlar, l73Carpet, l73Damask, l73TileFloor,
        l73Boards, l73Ember, l73Slate, l73Bath, l73WindowBoards, l73Note, l73Burnt, l73Crust, l73Bone;
    private readonly int[] l73Grass = new int[4];
    /// <summary>The keep's lined walls: [0 panelling (floor height), 1 damask above], by the face lined (north, east, south, west, 4 all round).</summary>
    private readonly int[,] l73Lined = new int[2, 5];
    private readonly int[] l73Sconce = new int[4], l73Banner = new int[4], l73Door = new int[6], l73AtticDoor = new int[4];
    private readonly int[,] l73Curtain = new int[3, 4], l73Table = new int[2, 4], l73Painting = new int[WorldLayout.L73Paintings, 4];

    /// <summary>How high the cliff round the sea rises above it.</summary>
    private const int L73RimTop = 16;

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL73()
    {
        l73Basalt = GameId("game:rock-basalt", "game:rock-granite");
        l73Earth = Id("l73-redearth");
        l73Rock = Id("l73-blackrock");
        l73Ash = Id("l73-ash-sand");
        l73Mud = Id("l73-bloodmud");
        l73Burnt = Id("l73-burnt");
        l73Crust = Id("l73-crust");
        l73Bone = Id("l73-bone");
        string[] lined = { "north", "east", "south", "west", "all" };
        for (int f = 0; f < 5; f++)
        {
            l73Lined[0, f] = Id("l73-wainscot-" + lined[f]);
            l73Lined[1, f] = Id("l73-damask-" + lined[f]);
        }
        l73Grass[1] = Id("l73-deadgrass-short");
        l73Grass[2] = Id("l73-deadgrass-mid");
        l73Grass[3] = Id("l73-deadgrass-tall");
        l73Silver = Id("l73-silverwall");
        l73Slate = Id("l73-slate");
        l73Bath = Id("l73-bath");
        l73WindowBoards = Id("l73-boards");
        l73Note = Id("loosenote-refuge");
        string[] curtainParts = { "top", "mid", "low" }, doorParts = { "lb", "rb", "lm", "rm", "lt", "rt" };
        for (int f = 0; f < 4; f++)
        {
            l73Sconce[f] = Id("l73-sconce-" + Sides[f]);
            l73Banner[f] = Id("l73-banner-" + Sides[f]);
            for (int p = 0; p < 3; p++) l73Curtain[p, f] = Id($"l73-curtain-{curtainParts[p]}-{Sides[f]}");
            l73Table[0, f] = Id("l73-table-set-" + Sides[f]);
            l73Table[1, f] = Id("l73-table-bare-" + Sides[f]);
            for (int k = 0; k < WorldLayout.L73Paintings; k++) l73Painting[k, f] = Id($"l73-painting-{k + 1}-{Sides[f]}");
        }
        for (int p = 0; p < 6; p++) l73Door[p] = Id("l73-door-shut-" + doorParts[p]);
        string[] atticParts = { "lb", "rb", "lt", "rt" };
        for (int p = 0; p < 4; p++) l73AtticDoor[p] = Id("l73-atticdoor-" + atticParts[p]);
        l73Sand = GameId("game:sand-basalt", "game:sand-granite");
        l73Gravel = GameId("game:gravel-basalt", "game:gravel-granite");
        l73Ashlar = Id("hub-ashlar-worn");
        l73Carpet = BlockId("backrooms:hotelcarpet-maroon");
        l73Damask = BlockId("backrooms:hotelcarpet-damask");
        l73TileFloor = Id("l188-tile-bath");
        l73Boards = BlockId("game:planks-aged-ud");
        l73Ember = GameId("game:ember");
        floorIds[(int)FloorKind.L73Floor] = l73Earth;
        floorIds[(int)FloorKind.L73Rock] = l73Rock;
        floorIds[(int)FloorKind.L73Ash] = l73Ash;
        floorIds[(int)FloorKind.L73Mud] = l73Mud;
        floorIds[(int)FloorKind.L73Tor] = l73Rock;
        floorIds[(int)FloorKind.L73Burnt] = l73Burnt;
        floorIds[(int)FloorKind.L73Crust] = l73Crust;
        floorIds[(int)FloorKind.L73Seabed] = l73Sand;
        floorIds[(int)FloorKind.L73Gravel] = l73Gravel;
        floorIds[(int)FloorKind.L73Court] = l73Rock;
        floorIds[(int)FloorKind.L73Path] = l73Ashlar;
        floorIds[(int)FloorKind.L73Carpet] = l73Carpet;
        floorIds[(int)FloorKind.L73Boards] = l73Boards;
        floorIds[(int)FloorKind.L73Tile] = l73TileFloor;
        floorIds[(int)FloorKind.L73Damask] = l73Damask;
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above the sea's surface.</summary>
    private int Level73Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        // The rim: a cliff of basalt round the sea
        if (t.Zone == WorldLayout.L73RimZone) return rel < -12 ? concreteId : rel <= L73RimTop ? l73Basalt : 0;
        if (t.Zone is WorldLayout.L73Court or WorldLayout.L73Keep or WorldLayout.L73Walls) return L73CastleBlock(gx, gz, rel);

        // The island and the sea
        int g = t.Depth > 0 ? -t.Depth : t.Height;
        // The Great Hound's bones (sunk into the ground where it rises)
        if (t.Sealed && t.Zone == WorldLayout.L73Land && rel > 0 && layout.L73HoundBoneAt(gx, gz, rel)) return l73Bone;
        if (rel > g)
        {
            if (rel <= 0) fluid = waterId;
            if (rel == g + 1 && t.Variant != 0) return PropBlock(t);
            if (rel == g + 1 && t.Detail == 1) return l73Note;
            // Dead grass on the fields
            if (rel == g + 1 && g > 0 && !t.Sealed && layout.L73GrassAt(gx, gz, t.Floor) is int grass and > 0) return l73Grass[grass];
            // The banners on the castle's outer walls hang over the ground just outside them
            if (g == WorldLayout.L73Plateau && WorldLayout.L73BannerAt(gx - layout.L73CastleX0, gz - layout.L73CastleZ0) is { } banner
                && rel == WorldLayout.L73Plateau + banner.Top)
                return l73Banner[Facing(banner.Facing)];
            return 0;
        }
        if (rel < System.Math.Min(g - 4, -8)) return concreteId; // (the ground below, as vanilla laid it)
        if (rel == g) return floorIds[(int)t.Floor] is int top and not 0 ? top : l73Earth;
        // A tor is black rock right down into the ground
        if (t.Floor == FloorKind.L73Tor && rel > g - 10) return l73Rock;
        if (rel >= g - 2)
            return t.Floor switch
            {
                FloorKind.L73Ash => l73Ash,
                FloorKind.L73Seabed => l73Sand,
                FloorKind.L73Gravel => l73Gravel,
                FloorKind.L73Rock => l73Rock,
                _ => rel == g - 1 ? l73Earth : l73Basalt,
            };
        return l73Basalt;
    }

    /// <summary>The Silver Castle, from its castle-local position and the height above its floor (the summit plateau).</summary>
    private int L73CastleBlock(int gx, int gz, int rel)
    {
        int u = gx - layout.L73CastleX0, v = gz - layout.L73CastleZ0;
        Part part = WorldLayout.L73CastleAt(u, v);
        int c = rel - WorldLayout.L73Plateau;
        if (c < 0) return rel < -8 ? concreteId : l73Basalt;
        const int w = WorldLayout.L73CastleW, d = WorldLayout.L73CastleD;
        bool Merlon(int a, int b) => ((a + b) & 1) == 0;
        switch (part)
        {
            case Part.Court:
            case Part.Path:
                if (c == 0) return part == Part.Court ? l73Rock : l73Ashlar;
                // Buttresses against the keep's walls, between its windows, capped in slate
                if (L73Buttress(u, v) && c <= 12) return c <= 11 ? l73Silver : l73Slate;
                // A little slate canopy over the keep's door, pointed
                if (v == WorldLayout.L73KeepV0 + WorldLayout.L73KeepD && u - WorldLayout.L73KeepU0 is >= 16 and <= 19
                    && (c == 4 || c == 5 && u - WorldLayout.L73KeepU0 is 17 or 18))
                    return l73Slate;
                return WorldLayout.L73BannerAt(u, v) is { } banner && c == banner.Top ? l73Banner[Facing(banner.Facing)] : 0;
            case Part.Gate:
                // The gateway, four wide and four high, under the wall-walk
                if (c == 0) return l73Ashlar;
                if (c <= 4) return 0;
                if (c <= 7) return l73Silver;
                return c == 8 && v == d - 1 && Merlon(u, v) ? l73Silver : 0;
            case Part.Curtain:
                if (c <= 7) return l73Silver;
                return c == 8 && (u == 0 || v == 0 || u == w - 1 || v == d - 1) && Merlon(u, v) ? l73Silver : 0;
            case Part.Tower:
            {
                if (c <= 10) return l73Silver;
                int tu = u < 6 ? u : w - 1 - u, tv = v < 6 ? v : d - 1 - v;
                // A steep pointed slate roof from the eaves, tapering to a spire (the castle's gothic outline from afar)
                if (c == 11) return l73Slate;
                if (c <= 13 && tu is >= 1 and <= 4 && tv is >= 1 and <= 4) return l73Slate;
                return c <= 17 && tu is 2 or 3 && tv is 2 or 3 ? l73Slate : 0;
            }
            case Part.GateTower:
                if (c <= 10) return l73Silver;
                if (c == 11 && (u is 22 or 25 or 30 or 33 || v is d - 5 or d - 1)) return Merlon(u, v) ? l73Silver : 0;
                // A slate cap and a spire on each gate tower
                if (c == 11) return l73Slate;
                return c <= 15 && u is 23 or 24 or 31 or 32 && v == d - 3 ? l73Slate : 0;
        }
        return L73KeepBlock(u - WorldLayout.L73KeepU0, v - WorldLayout.L73KeepV0, c);
    }

    /// <summary>
    /// Whether a castle-local courtyard position holds a buttress against the keep's outer wall: on the long faces at keep
    /// columns 4, 8, 15, 20, 27 and 31 (15 and 20 flank the door's path), on the ends at rows 4, 8, 15 and 19, so never
    /// in front of a window (every fourth, from 2) or a banner.
    /// </summary>
    private static bool L73Buttress(int u, int v)
    {
        int ku = u - WorldLayout.L73KeepU0, kv = v - WorldLayout.L73KeepV0;
        bool longFace = (kv == -1 || kv == WorldLayout.L73KeepD) && ku is 4 or 8 or 15 or 20 or 27 or 31;
        bool endFace = (ku == -1 || ku == WorldLayout.L73KeepW) && kv is 4 or 8 or 15 or 19;
        return longFace || endFace;
    }

    /// <summary>The keep, keep-local, <paramref name="c"/> above its floor: three storeys, the slabs between, the roof above.</summary>
    private int L73KeepBlock(int ku, int kv, int c)
    {
        if (c > WorldLayout.L73Terrace) return L73KeepTop(ku, kv, c);
        bool ring = WorldLayout.L73KeepRing(ku, kv);
        const int storey = WorldLayout.L73Storey;
        if (c == 0)
        {
            if (WorldLayout.L73MainDoor(ku, kv)) return l73Ashlar;
            if (ring || WorldLayout.L73HearthAt(ku, kv) > 0) return l73Silver;
            return WorldLayout.L73RoomAt(ku, kv, 0) switch
            {
                Room.Wall => l73Silver,
                Room.Hall => l73Carpet,
                Room.Bath => l73TileFloor,
                Room.Guest => l73Damask,
                _ => l73Boards,
            };
        }
        if (c % storey == 0)
        {
            // A slab: the ceiling of the storey below, the floor of the one above (open over the flight below it)
            int below = c / storey - 1, above = below + 1;
            if (ring) return l73Ashlar; // (a string course of smooth stone round the outside at every floor)
            int step = WorldLayout.L73StairStep(ku, kv, below);
            if (step == 5) return hotelStairIds[0, Facing(WorldLayout.L73StairRise(below))];
            if (step > 0) return 0;
            if (above <= 2)
                return WorldLayout.L73RoomAt(ku, kv, above) switch { Room.Wall => l73Silver, Room.Bath => l73TileFloor, _ => l73Boards };
            // The roof terrace: the attic's boards in it, stone paving round it
            return WorldLayout.L73AtticAt(ku, kv) switch
            {
                Atp.Inside or Atp.LockedDoor or Atp.BalconyDoor => l73Boards,
                Atp.Wall or Atp.StairWall => l73Silver,
                _ => l73Ashlar,
            };
        }

        int s = c / storey, h = c - s * storey; // h 1 to 4 over the storey's floor
        if (ring)
        {
            if (s == 0 && WorldLayout.L73MainDoor(ku, kv)) return h <= 3 ? l73Door[ku - 17 + 2 * (h - 1)] : l73Silver;
            // Windows, boarded up (the curtains hang inside)
            if (h is 2 or 3 && WorldLayout.L73Window(ku, kv, s)) return l73WindowBoards;
            // Silver ashlar outside; inside, panelling to the chair rail and red damask over it ("lavishly decorated")
            int lined = kv == 0 && ku is > 0 and < WorldLayout.L73KeepW - 1 ? 2 : kv == WorldLayout.L73KeepD - 1 && ku is > 0 and < WorldLayout.L73KeepW - 1 ? 0
                : ku == 0 && kv is > 0 and < WorldLayout.L73KeepD - 1 ? 1 : ku == WorldLayout.L73KeepW - 1 && kv is > 0 and < WorldLayout.L73KeepD - 1 ? 3 : -1;
            return lined < 0 ? l73Silver : l73Lined[h == 1 ? 0 : 1, lined];
        }
        if (s == 0 && WorldLayout.L73HearthAt(ku, kv) is int hearth and > 0)
            return hearth == 1 || h == 4 ? l73Silver : h == 1 ? l73Ember : 0; // the jambs, the breast over the fire, the embers

        if (WorldLayout.L73RoomAt(ku, kv, s) == Room.Wall)
        {
            if (WorldLayout.L73Doorway(ku, kv, s) && h <= 2) return 0;
            // (the chimney rising through the upper storeys stays stone; the partitions are panelled and papered both sides)
            bool chimney = s > 0 && kv == 1 && ku is >= 16 and <= 19;
            return chimney ? l73Silver : l73Lined[h == 1 ? 0 : 1, 4];
        }
        int st = WorldLayout.L73StairStep(ku, kv, s);
        if (st > 0) return h < st ? l73Silver : h == st ? hotelStairIds[0, Facing(WorldLayout.L73StairRise(s))] : 0;
        if (WorldLayout.L73CurtainAt(ku, kv, s) is ArchPier curtain) return l73Curtain[h == 4 ? 0 : h == 1 ? 2 : 1, Facing(curtain)];
        return L73Furnishing(ku, kv, s, h, 3);
    }

    /// <summary>
    /// Over the roof terrace: the parapet, the corner turrets, the chimney stack, the attic (its walls three high, its
    /// locked door and its balcony door, what is kept in it) under a stepped slate roof, and the balcony's rail.
    /// </summary>
    private int L73KeepTop(int ku, int kv, int c)
    {
        const int kw = WorldLayout.L73KeepW, kd = WorldLayout.L73KeepD;
        bool merlon = ((ku + kv) & 1) == 0;
        if ((ku < 3 || ku >= kw - 3) && (kv < 3 || kv >= kd - 3))
        {
            if (c <= 19) return l73Silver;
            // A slate cap and a needle spire on each turret, its top one under the band's (as the attic's ridge)
            if (c == 20) return l73Slate;
            return c <= WorldLayout.L73AtticTop && ku is 1 or kw - 2 && kv is 1 or kd - 2 ? l73Slate : 0;
        }
        if (ku is >= 16 and <= 19 && kv <= 1) return c <= 18 ? l73Silver : 0; // the chimney stack
        if (WorldLayout.L73KeepRing(ku, kv)) return c == 16 && merlon ? l73Silver : 0;
        // The attic's roof, stepping up from its eaves to the ridge (with an overhang at the gable ends)
        if (ku is >= 8 and <= 27 && kv is >= 4 and <= 15 && c >= 19)
        {
            int r = System.Math.Min(4, System.Math.Min(kv - 4, 15 - kv));
            int low = r == 0 ? 19 : 18 + r, high = 19 + r;
            if (c >= low && c <= high) return l73Slate;
            return c < low && ku is 9 or 26 ? l73Silver : 0;
        }
        int h = c - WorldLayout.L73Terrace;
        switch (WorldLayout.L73AtticAt(ku, kv))
        {
            case Atp.Wall:
            case Atp.StairWall:
                return l73Silver;
            case Atp.LockedDoor:
                return h <= 2 ? l73AtticDoor[ku - 23 + 2 * (h - 1)] : l73Silver;
            case Atp.BalconyDoor:
                return h <= 2 ? l73AtticDoor[ku - 17 + 2 * (h - 1)] : l73Silver;
            case Atp.Rail:
                return h == 1 ? l73Silver : 0;
            case Atp.Inside:
                return L73Furnishing(ku, kv, 3, h, 3);
        }
        return 0;
    }

    /// <summary>
    /// What stands at a keep-local position on a storey at <paramref name="h"/> above its floor: furniture on the floor (1),
    /// sconces and paintings on the walls at <paramref name="wallAt"/> (banners hang from the row above, down over it),
    /// chandeliers under the ceiling (4); air elsewhere.
    /// </summary>
    private int L73Furnishing(int ku, int kv, int storey, int h, int wallAt)
    {
        if (h == 1 && WorldLayout.L73FurnishingAt(ku, kv, storey, Layer.Floor) is { Thing: not Thing.None } floor) return L73FloorThing(floor.Thing, floor.Facing);
        var wall = WorldLayout.L73FurnishingAt(ku, kv, storey, Layer.Wall);
        if (wall.Thing == Thing.Banner && h == wallAt + 1) return l73Banner[Facing(wall.Facing)];
        if (wall.Thing is not (Thing.None or Thing.Banner) && h == wallAt)
            return wall.Thing == Thing.Sconce ? l73Sconce[Facing(wall.Facing)] : l73Painting[wall.Kind, Facing(wall.Facing)];
        if (h == 4 && WorldLayout.L73FurnishingAt(ku, kv, storey, Layer.Ceiling).Thing == Thing.Chandelier) return chandelierId;
        return 0;
    }

    private int L73FloorThing(Thing thing, ArchPier facing)
    {
        int Prop(ushort variant, byte stack = 0) => PropBlock(new Tile { Variant = variant, Pier = facing, Stack = stack });
        return thing switch
        {
            Thing.Bookshelf => Prop(Props.HotelBookshelf),
            Thing.Clock => Prop(Props.GrandfatherClock),
            Thing.Candelabra => Prop(Props.Candelabra),
            Thing.Chair => Prop(Props.HotelChair),
            Thing.Toilet => Prop(Props.Toilet),
            Thing.Dresser => Prop(Props.Dresser),
            Thing.Desk => Prop(Props.WritingDesk),
            Thing.RoundTable => Prop(Props.DiningTable),
            Thing.SofaLeft => Prop(Props.LongSofa, 0),
            Thing.SofaRight => Prop(Props.LongSofa, 1),
            Thing.Crate => Prop(Props.WreckCrate),
            Thing.Bones => Prop(Props.BonePile),
            Thing.Ribcage => Prop(Props.Ribcage),
            Thing.Skull => Prop(Props.JawSkeleton),
            Thing.Pack => Prop(Props.Backpack),
            Thing.Box => boxId,
            Thing.Note => l73Note,
            Thing.Table => l73Table[0, Facing(facing)],
            Thing.Bath => l73Bath,
            // Beds are modelled head to the north; the facing points from the head toward the foot
            Thing.BedHead => bedHeadIds[Facing(Opposite(facing))],
            Thing.BedFoot => bedFootIds[Facing(Opposite(facing))],
            Thing.Nightstand => nightstandIds[Facing(facing)],
            Thing.Wardrobe => wardrobeIds[Facing(facing)],
            _ => 0,
        };
    }
}
