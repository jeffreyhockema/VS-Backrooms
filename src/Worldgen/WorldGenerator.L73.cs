using Part = Backrooms.Worldgen.WorldLayout.L73Part;
using Thing = Backrooms.Worldgen.WorldLayout.L73Thing;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 73, "The Redlands" (experimental, kept as level 21), laid out in WorldLayout.Level73.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>), which is the sea's surface. The island is crimson earth over basalt, black rock on
/// its outcrops and hilltops, ash sand on the beach and blood-red mud in the gullies; the seabed is basalt sand and gravel
/// under still water. The Silver Castle is pale silver ashlar: curtain walls seven high with battlements, towers ten, the
/// keep two storeys under a flat roof with turrets; inside, carpet and boards, the Level 5 hotel's furniture, iron sconces
/// and a hearth of embers. The rim of the region is a cliff of basalt. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l73Earth, l73Rock, l73Ash, l73Mud, l73Silver, l73Basalt, l73Sand, l73Gravel, l73Ashlar, l73Carpet, l73Boards, l73Ember;
    private readonly int[] l73Sconce = new int[4];

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
        l73Silver = Id("l73-silverwall");
        for (int f = 0; f < 4; f++) l73Sconce[f] = Id("l73-sconce-" + Sides[f]);
        l73Sand = GameId("game:sand-basalt", "game:sand-granite");
        l73Gravel = GameId("game:gravel-basalt", "game:gravel-granite");
        l73Ashlar = Id("hub-ashlar-worn");
        l73Carpet = BlockId("backrooms:hotelcarpet-maroon");
        l73Boards = BlockId("game:planks-aged-ud");
        l73Ember = GameId("game:ember");
        floorIds[(int)FloorKind.L73Floor] = l73Earth;
        floorIds[(int)FloorKind.L73Rock] = l73Rock;
        floorIds[(int)FloorKind.L73Ash] = l73Ash;
        floorIds[(int)FloorKind.L73Mud] = l73Mud;
        floorIds[(int)FloorKind.L73Seabed] = l73Sand;
        floorIds[(int)FloorKind.L73Gravel] = l73Gravel;
        floorIds[(int)FloorKind.L73Court] = l73Rock;
        floorIds[(int)FloorKind.L73Path] = l73Ashlar;
        floorIds[(int)FloorKind.L73Carpet] = l73Carpet;
        floorIds[(int)FloorKind.L73Boards] = l73Boards;
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
        if (rel > g)
        {
            if (rel <= 0) fluid = waterId;
            return 0;
        }
        if (rel < System.Math.Min(g - 4, -8)) return concreteId; // (the ground below, as vanilla laid it)
        if (rel == g) return floorIds[(int)t.Floor] is int top and not 0 ? top : l73Earth;
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
        if (c == 0)
            return part switch
            {
                Part.Court => l73Rock,
                Part.Path or Part.Gate or Part.Door => l73Ashlar,
                Part.Hall or Part.Stair => l73Carpet,
                Part.Dining => l73Boards,
                _ => l73Silver,
            };
        const int w = WorldLayout.L73CastleW, d = WorldLayout.L73CastleD;
        bool Merlon(int a, int b) => ((a + b) & 1) == 0;
        switch (part)
        {
            case Part.Court:
            case Part.Path:
                return 0;
            case Part.Gate:
                // The gateway, four wide and four high, under the wall-walk
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
                return c == 11 && (tu is 0 or 5 || tv is 0 or 5) && Merlon(u, v) ? l73Silver : 0;
            }
            case Part.GateTower:
                if (c <= 10) return l73Silver;
                return c == 11 && (u is 18 or 21 or 26 or 29 || v is d - 5 or d - 1) && Merlon(u, v) ? l73Silver : 0;
        }
        return L73KeepBlock(u - WorldLayout.L73KeepU0, v - WorldLayout.L73KeepV0, c, part);
    }

    /// <summary>The keep, keep-local, <paramref name="c"/> above its floor.</summary>
    private int L73KeepBlock(int ku, int kv, int c, Part part)
    {
        const int kw = WorldLayout.L73KeepW, kd = WorldLayout.L73KeepD;
        bool ring = WorldLayout.L73KeepRing(ku, kv);
        bool turret = (ku < 3 || ku >= kw - 3) && (kv < 3 || kv >= kd - 3);
        bool merlon = ((ku + kv) & 1) == 0;
        // The roof: a parapet round it, a turret on each corner
        if (c > WorldLayout.L73RoofSlab)
        {
            if (turret)
            {
                if (c <= 14) return l73Silver;
                bool edge = ku is 0 or 2 or kw - 3 or kw - 1 || kv is 0 or 2 or kd - 3 or kd - 1;
                return c == 15 && edge && merlon ? l73Silver : 0;
            }
            return c == 12 && ring && merlon ? l73Silver : 0;
        }
        if (c == WorldLayout.L73RoofSlab) return l73Silver;
        bool upper = c > WorldLayout.L73UpperSlab;
        if (ring)
        {
            if (part == Part.Door && c <= 3) return 0;
            // Windows, boarded up from outside
            if (WorldLayout.L73Window(ku, kv, upper) && (upper ? c is 8 or 9 : c is 2 or 3)) return l73Boards;
            return l73Silver;
        }

        // The stair up along the main hall's north wall, through a hole in the floor above
        if (part == Part.Stair && c <= WorldLayout.L73UpperSlab)
        {
            int step = WorldLayout.L73StairStep(ku, kv);
            return c < step ? l73Silver : c == step ? hotelStairIds[0, Facing(ArchPier.East)] : 0;
        }
        if (c == WorldLayout.L73UpperSlab) return l73Boards;

        if (!upper)
        {
            switch (part)
            {
                case Part.Partition:
                case Part.Jamb:
                    return l73Silver;
                case Part.Hearth:
                    // Embers on the hearthstone, the chimney breast over them
                    return c == 1 ? l73Ember : c <= 3 ? 0 : l73Silver;
            }
            return L73Furnishing(ku, kv, false, c, 1, 3, 5);
        }

        int cu = c - WorldLayout.L73UpperSlab; // 1 just above the upper floor
        switch (WorldLayout.L73UpperAt(ku, kv))
        {
            case Part.Hole: return 0;
            case Part.Partition: return l73Silver;
            case Part.UpDoor: return cu <= 2 ? 0 : l73Silver;
        }
        return L73Furnishing(ku, kv, true, cu, 1, 3, 4);
    }

    /// <summary>
    /// What stands at a keep-local position at <paramref name="c"/> above its storey's floor: furniture on the floor
    /// (<paramref name="floorAt"/>), sconces on the walls (<paramref name="sconceAt"/>), chandeliers under the ceiling
    /// (<paramref name="ceilingAt"/>); air elsewhere.
    /// </summary>
    private int L73Furnishing(int ku, int kv, bool upper, int c, int floorAt, int sconceAt, int ceilingAt)
    {
        var (thing, facing) = WorldLayout.L73FurnishingAt(ku, kv, upper);
        if (thing == Thing.None) return 0;
        if (thing == Thing.Sconce) return c == sconceAt ? l73Sconce[Facing(facing)] : 0;
        if (thing == Thing.Chandelier) return c == ceilingAt ? chandelierId : 0;
        if (c != floorAt) return 0;
        return thing switch
        {
            Thing.Bookshelf => PropBlock(new Tile { Variant = Props.HotelBookshelf, Pier = facing }),
            Thing.Clock => PropBlock(new Tile { Variant = Props.GrandfatherClock, Pier = facing }),
            Thing.Candelabra => PropBlock(new Tile { Variant = Props.Candelabra, Pier = facing }),
            Thing.Table => PropBlock(new Tile { Variant = Props.DiningTable, Pier = facing }),
            Thing.Chair => PropBlock(new Tile { Variant = Props.HotelChair, Pier = facing }),
            Thing.Toilet => PropBlock(new Tile { Variant = Props.Toilet, Pier = facing }),
            Thing.TubHead => PropBlock(new Tile { Variant = Props.Bathtub, Pier = facing, Stack = 0 }),
            Thing.TubFoot => PropBlock(new Tile { Variant = Props.Bathtub, Pier = facing, Stack = 1 }),
            // Beds are modelled head to the north; the facing points from the head toward the foot
            Thing.BedHead => bedHeadIds[Facing(Opposite(facing))],
            Thing.BedFoot => bedFootIds[Facing(Opposite(facing))],
            Thing.Nightstand => nightstandIds[Facing(facing)],
            Thing.Wardrobe => wardrobeIds[Facing(facing)],
            _ => 0,
        };
    }
}
