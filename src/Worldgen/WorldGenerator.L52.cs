using System.Collections.Generic;
using Zone = Backrooms.Worldgen.WorldLayout.L52Zone;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 52, "School Halls" (experimental, kept as level 23), laid out in WorldLayout.Level52.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>). Halls, classrooms and the canteen's store rooms are four blocks high under a drop
/// ceiling of Level 4's tiles with fluorescent panels (the ones that work hum), the canteen five, the gym eight under bare
/// concrete; walls are the school's two-tone paint (<c>l52-wall</c>: a mint base and dado with a dark rail, off-white above),
/// banks of lockers (<c>l52-locker</c>) along the halls. Everything above the rooms is solid to the top of the band.
///
/// Every block of the level's own is looked up softly (<see cref="L52Block"/>): until its asset exists, what is missing is
/// drawn as Level 4's nearest (walls, floors) or left out (the desks, the boards), logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private readonly int[] l52Wall = new int[3], l52Tile = new int[2], l52Gym = new int[3], l52Desk = new int[4];
    private readonly int[,] l52Locker = new int[2, 4];
    private readonly int[,,] l52Board = new int[2, 3, 4];
    private readonly HashSet<string> l52Missing = new();

    /// <summary>A block of the level's, or <paramref name="fallback"/> if its asset is not there (logged once).</summary>
    private int L52Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l52Missing.Add(code) && l52Missing.Count <= 20) api.Logger.Warning("[backrooms] Level 52: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>The level's block ids (called from the constructor, after Level 4's).</summary>
    private void InitL52()
    {
        string[] wallParts = { "base", "dado", "upper" };
        int officeWall = BlockId("backrooms:officewall");
        for (int i = 0; i < 3; i++) l52Wall[i] = L52Block("l52-wall-" + wallParts[i], officeWall);
        l52Tile[0] = L52Block("l52-tile-hall", BlockId("backrooms:officecarpet-plain"));
        l52Tile[1] = L52Block("l52-tile-room", l52Tile[0]);
        string[] gymKinds = { "plain", "linens", "linewe" };
        int hotelWood = BlockId("backrooms:hotelwood");
        for (int i = 0; i < 3; i++) l52Gym[i] = L52Block("l52-gymfloor-" + gymKinds[i], hotelWood);
        string[] parts = { "lower", "upper" }, ends = { "l", "m", "r" };
        for (int f = 0; f < 4; f++)
        {
            l52Desk[f] = L52Block("l52-desk-" + Sides[f]);
            for (int p = 0; p < 2; p++)
            {
                l52Locker[p, f] = L52Block($"l52-locker-{parts[p]}-{Sides[f]}", l52Wall[p]);
                for (int e = 0; e < 3; e++) l52Board[p, e, f] = L52Block($"l52-chalkboard-{parts[p]}-{ends[e]}-{Sides[f]}");
            }
        }
    }

    /// <summary>How many blocks of air a floor tile of the level has over it.</summary>
    private static int L52Air(in Tile t) => t.Zone switch
    {
        (byte)Zone.Gym => 8,
        (byte)Zone.Canteen => 5,
        _ => 4,
    };

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level52Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < 0) return concreteId;
        if (t.IsWallLike || t.Kind != TileKind.Floor)
        {
            int high = t.Height > 0 ? t.Height : 4;
            if (rel > high) return concreteId;
            if (rel == 0) return t.Kind == TileKind.Doorway ? L52Floor(t) : concreteId;
            if (t.Kind == TileKind.Doorway && rel <= 2) return 0;
            if (t.Kind == TileKind.Wall && t.Detail == 1 && rel <= 2) return l52Locker[rel - 1, Facing(t.Pier)];
            return l52Wall[rel >= 3 ? 2 : rel - 1];
        }
        int air = L52Air(t);
        if (rel == 0) return L52Floor(t);
        if (rel == air + 1)
        {
            int ceiling = t.Zone == (byte)Zone.Gym ? concreteCeilingId : officeCeilingId;
            return t.Ceiling switch
            {
                CeilingKind.LightOn => lightOnId,
                CeilingKind.LightLit => lightLitId,
                CeilingKind.LightOff => lightOffId,
                CeilingKind.LightFlicker => lightFlickerId,
                _ => ceiling,
            };
        }
        if (rel > air) return concreteId;
        // A chalkboard hangs at rel 2 and 3, over nothing
        if (t.Variant == Props.L52Chalkboard)
            return rel is 2 or 3 ? l52Board[rel - 2, System.Math.Min((int)t.Stack, 2), Facing(t.Pier)] : 0;
        if (rel != 1) return 0;
        int facing = Facing(t.Pier);
        return t.Variant switch
        {
            0 => 0,
            Props.L52Desk => l52Desk[facing],
            Props.Desk => deskIds[facing],
            Props.Vending => vendingIds[facing],
            Props.Cooler => coolerIds[facing],
            Props.Shelf => shelfIds[Facing(Opposite(t.Pier))],
            >= 40 and < Props.Limit => PropBlock(t),
            _ => 0,
        };
    }

    private int L52Floor(in Tile t) => t.Floor switch
    {
        FloorKind.L52Room => l52Tile[1],
        FloorKind.L52Gym => l52Gym[0],
        FloorKind.L52GymLineNS => l52Gym[1],
        FloorKind.L52GymLineWE => l52Gym[2],
        _ => l52Tile[0],
    };
}
