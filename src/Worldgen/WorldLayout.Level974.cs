using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 974, "Kitty's House": kept as level 18 (<see cref="Level974"/>) and shown as "974". A small pink house with no
/// door to the outside, its windows paintings of a sky; one to every cell of a region far out to the south-west, each
/// sealed in solid nothing. Every wanderer who is taken there is given one of them for good (see
/// <c>Regions.L974System</c>), so a house's small differences (which way round it is, its bedding, its posters, the
/// paintings in its windows) are that wanderer's.
///
/// The plan is fixed, as the canon has it ("nearly identical homes"): 19 by 17 with its outer walls, one storey with
/// four blocks of air under the ceiling (Kitty is 3.2 m tall). A living room and a kitchen-diner on one side of a hall
/// two wide, a bedroom (the bed in an alcove under a sloping ceiling), two bathrooms and the master bedroom (empty but
/// for the cat bed) on the other. See docs/design/new-levels/974-plan.md, section 3.2.
///
/// Tiles of a house: <see cref="Tile.Zone"/> is the room (<see cref="L974Room"/>); a floor tile's
/// <see cref="Tile.Variant"/> is the prop on it (<see cref="Props.L974Bed"/> ...) facing <see cref="Tile.Pier"/>;
/// <see cref="Tile.Detail"/> is a thing hung on the wall beside it ((kind &lt;&lt; 2) | (int)facing, kinds
/// <see cref="L974Hung"/>); <see cref="Tile.Depth"/> what is up under the ceiling ((1 &lt;&lt; 2) | facing: fairy lights;
/// (2 &lt;&lt; 2) | facing: the alcove's slope, which <see cref="Tile.Height"/> says how low, 3 or 2 blocks of air).
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x1800-0x18BF are this level's.</summary>
    private const ulong SaltL974Shape = 0x1801, SaltL974House = 0x1810;

    /// <summary>A house, with its outer walls: its size, and where it stands in its cell.</summary>
    public const int L974HouseW = 19, L974HouseD = 17, L974HouseX0 = 6, L974HouseZ0 = 7;

    /// <summary>The rooms of a house, kept in <see cref="Tile.Zone"/>.</summary>
    public enum L974Room : byte { None, Living, Hall, Bedroom, Bath, HalfBath, Kitchen, Master }

    /// <summary>Things hung on a house's walls, kept in <see cref="Tile.Detail"/> of the floor tile in front of them.</summary>
    public static class L974Hung
    {
        public const int PosterFirst = 1; // 1-6: cat, bunny, rainbow, star, toast, frog
        public const int FrameWhite = 7, FrameGold = 8, ShelfPlush = 9, ShelfFigures = 10, Mirror = 11, TowelRail = 12, CatClock = 13, NightLight = 14;
        public static readonly string[] Posters = { "cat", "bunny", "rainbow", "star", "toast", "frog" };
    }

    /// <summary>What a house holds up under its ceiling, kept in <see cref="Tile.Depth"/> >> 2.</summary>
    public const int L974HighFairy = 1, L974HighSlope = 2;

    // ================= Where it is =================

    /// <summary>The region's centre, in macro cells: far out to the south-west, a quarter further out than the city.</summary>
    private int L974CentreX => spawnMacroX - DiagonalReach;
    private int L974CentreZ => spawnMacroZ + DiagonalReach;

    /// <summary>The region's radius in macro cells (one house to a cell, so thousands of houses).</summary>
    private int L974Radius => Math.Max(60, spawnMacroX / 40);

    private bool InL974(double mx, double mz) => InRoundRegion(mx, mz, L974CentreX, L974CentreZ, L974Radius, SaltL974Shape);

    /// <summary>A cell to look for a house in, picked by hash (somewhere toward the middle of the region).</summary>
    private (int Mx, int Mz) L974ArrivalCell(ulong h) => RoundArrivalCell(h, L974CentreX, L974CentreZ, L974Radius);

    /// <summary>The house cell a hash picks, if it lies in the region (for handing out houses: see <c>L974System</c>).</summary>
    public (int Mx, int Mz)? L974HouseCellFor(ulong h)
    {
        var (mx, mz) = L974ArrivalCell(h);
        return LevelAt(mx, mz) == Level974 ? (mx, mz) : null;
    }

    /// <summary>Arriving: in the bedroom, beside the bed, and nowhere else.</summary>
    private static bool IsL974ArrivalSpot(Tile t) => t.Kind == TileKind.Floor && t.Under == Unders.L974Arrival;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L974ArrivalHeight(in Tile t, double stand) => stand;

    // ================= A house, for the systems =================

    /// <summary>The north-west corner (block coordinates) of the house in a cell; the house is <see cref="L974HouseW"/> by <see cref="L974HouseD"/>.</summary>
    public static (int X, int Z) L974HouseCorner(int mx, int mz) => (mx * MacroSize + L974HouseX0, mz * MacroSize + L974HouseZ0);

    /// <summary>Whether the house in a cell is drawn the other way round (east to west).</summary>
    public bool L974Mirrored(int mx, int mz) => (Hashing.Hash(seed, mx, mz, SaltL974House) & 1) != 0;

    /// <summary>A place in a house (from its plan, drawn the right way round) as block coordinates.</summary>
    public (int X, int Z) L974At(int mx, int mz, int u, int v)
    {
        var (x0, z0) = L974HouseCorner(mx, mz);
        return (x0 + (L974Mirrored(mx, mz) ? L974HouseW - 1 - u : u), z0 + v);
    }

    /// <summary>
    /// Where someone taken to the house in a cell wakes: in the bedroom, on the rug before the bed (layout version 5 on;
    /// in 1-4 in the mouth of the bed's alcove, a stub wall at arm's length).
    /// </summary>
    public (int X, int Z) L974Arrival(int mx, int mz) => Version >= 5 ? L974At(mx, mz, 13, 4) : L974At(mx, mz, 14, 5);

    /// <summary>The kinds of place in a house Kitty keeps to (see <c>L974System</c>).</summary>
    public enum L974SpotKind : byte { Watch, SleepWatch, Kneel, Table, Kitchen }

    /// <summary>Where Kitty may stand: in doorways, at the ends of the hall, in far corners, by the bed and the cat bed.</summary>
    private static readonly (int U, int V, L974SpotKind Kind)[] L974PlanSpots =
    {
        // Doorways and the archway's ends
        (8, 4, L974SpotKind.Watch), (8, 12, L974SpotKind.Watch), (11, 5, L974SpotKind.Watch), (11, 9, L974SpotKind.Watch),
        (11, 13, L974SpotKind.Watch), (16, 11, L974SpotKind.Watch), (3, 8, L974SpotKind.Watch), (5, 8, L974SpotKind.Watch),
        // The hall's two ends, the living room's far corners, the foot of the bed, the master bedroom
        (9, 1, L974SpotKind.Watch), (10, 15, L974SpotKind.Watch), (1, 1, L974SpotKind.Watch), (7, 7, L974SpotKind.Watch),
        (1, 7, L974SpotKind.Watch), (15, 3, L974SpotKind.Watch), (12, 14, L974SpotKind.Watch), (2, 9, L974SpotKind.Watch),
        (15, 5, L974SpotKind.Watch),
        (15, 4, L974SpotKind.SleepWatch), (16, 14, L974SpotKind.Kneel), (6, 14, L974SpotKind.Table), (4, 12, L974SpotKind.Kitchen),
    };

    /// <summary>The places in a house Kitty keeps to, as block coordinates.</summary>
    public List<(int X, int Z, L974SpotKind Kind)> L974Spots(int mx, int mz)
    {
        var list = new List<(int, int, L974SpotKind)>(L974PlanSpots.Length);
        foreach (var (u, v, kind) in L974PlanSpots)
        {
            var (x, z) = L974At(mx, mz, u, v);
            list.Add((x, z, kind));
        }
        return list;
    }

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: solid, like everything between the houses.</summary>
    private Edge L974Edge(int mx, int mz, bool west)
    {
        var edge = new Edge { Pattern = WallPattern.L974Wall, Base = BaseStyle.Plain, Tall = true };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        return edge;
    }

    private PlanCache<Tile[]> l974Plans;

    private void BuildLevel974(Builder b, int mx, int mz)
    {
        Tile[] house = (l974Plans ??= new PlanCache<Tile[]>(64, PlanKittyHouse)).Get(mx, mz);
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int u = lx - L974HouseX0, v = lz - L974HouseZ0;
                b.At(lx, lz) = u >= 0 && v >= 0 && u < L974HouseW && v < L974HouseD ? house[v * L974HouseW + u]
                    : new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L974Wall, Tall = true };
            }
    }

    /// <summary>The house's plan: walls (#), stub walls of the bed alcove (x), windows (W), doorways (D), the archway (A), floor (.).</summary>
    private static readonly string[] L974Plan =
    {
        "###WW#########WW###",
        "#.......#..#......#",
        "#.......#..#....xx#",
        "#.......#..#......#",
        "#.......D..#......#",
        "#.......#..D....xx#",
        "#.......#..#..x...#",
        "#.......#..########",
        "###AAA###..#...#..#",
        "#.......#..D...#..#",
        "#.......#..#...#..#",
        "#.......#..#####D##",
        "W.......D..#......#",
        "W.......#..D......W",
        "#.......#..#......W",
        "#.......#..#......#",
        "###################",
    };

    private static L974Room L974RoomAt(int u, int v) =>
        u >= 1 && u <= 7 && v >= 1 && v <= 7 ? L974Room.Living
        : u >= 1 && u <= 7 && v >= 9 && v <= 15 ? L974Room.Kitchen
        : u >= 9 && u <= 10 && v >= 1 && v <= 15 ? L974Room.Hall
        : u >= 12 && u <= 17 && v >= 1 && v <= 6 ? L974Room.Bedroom
        : u >= 12 && u <= 14 && v >= 8 && v <= 10 ? L974Room.Bath
        : u >= 16 && u <= 17 && v >= 8 && v <= 10 ? L974Room.HalfBath
        : u >= 12 && u <= 17 && v >= 12 && v <= 15 ? L974Room.Master
        : L974Room.None;

    /// <summary>
    /// One house, drawn from the plan the right way round for its cell (mirrored east to west in half of them), with its
    /// own bedding, posters, frames, shelves and window paintings.
    /// </summary>
    private Tile[] PlanKittyHouse(int mx, int mz)
    {
        const int W = L974HouseW, D = L974HouseD;
        var tiles = new Tile[W * D];
        bool mirror = L974Mirrored(mx, mz);
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltL974House + 1));
        int U(int u) => mirror ? W - 1 - u : u;
        ArchPier F(ArchPier p) => mirror ? p switch { ArchPier.East => ArchPier.West, ArchPier.West => ArchPier.East, _ => p } : p;
        ref Tile At(int u, int v) => ref tiles[v * W + U(u)];

        // Walls, floors, doorways and windows
        for (int v = 0; v < D; v++)
            for (int u = 0; u < W; u++)
            {
                char c = L974Plan[v][u];
                ref Tile t = ref At(u, v);
                L974Room room = L974RoomAt(u, v);
                switch (c)
                {
                    case '.':
                        t = new Tile
                        {
                            Kind = TileKind.Floor, Zone = (byte)room,
                            Floor = room == L974Room.Kitchen ? FloorKind.L974Checker
                                : room is L974Room.Bath or L974Room.HalfBath ? FloorKind.L974BathHex : FloorKind.L974Floor,
                        };
                        break;
                    case 'D':
                    case 'A':
                    {
                        // A doorway's passage runs across the wall it is in
                        bool wallRunsWE = L974Plan[v][u - 1] != '.' && L974Plan[v][u + 1] != '.';
                        t = new Tile { Kind = TileKind.Doorway, Floor = FloorKind.L974Floor, Pier = wallRunsWE ? ArchPier.North : ArchPier.East, Stack = (byte)(c == 'A' ? 1 : 0) };
                        break;
                    }
                    case 'W':
                    {
                        // Which way the window looks into the room
                        ArchPier into = v == 0 ? ArchPier.South : v == D - 1 ? ArchPier.North : u == 0 ? ArchPier.East : ArchPier.West;
                        t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L974Window, Pier = F(into), Tall = true };
                        break;
                    }
                    default:
                        t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L974Paint, Tall = true };
                        break;
                }
            }

        // Things on the floor, in the plan's own directions (F turns them for a mirrored house)
        void Put(int u, int v, ushort prop, ArchPier facing, int stack = 0)
        {
            ref Tile t = ref At(u, v);
            t.Variant = prop;
            t.Pier = F(facing);
            t.Stack = (byte)stack;
        }
        // A corner piece's facing, from the two sides its backs are on: the back opposite its front, the other on its right
        void PutCorner(int u, int v, ushort prop, ArchPier backA, ArchPier backB, int stack)
        {
            ArchPier a = F(backA), bk = F(backB);
            foreach (ArchPier f in new[] { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West })
            {
                ArchPier opposite = f switch { ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East };
                ArchPier right = f switch { ArchPier.North => ArchPier.East, ArchPier.East => ArchPier.South, ArchPier.South => ArchPier.West, _ => ArchPier.North };
                if ((opposite == a && right == bk) || (opposite == bk && right == a))
                {
                    ref Tile t = ref At(u, v);
                    t.Variant = prop;
                    t.Pier = f;
                    t.Stack = (byte)stack;
                    return;
                }
            }
        }
        void Hang(int u, int v, int kind, ArchPier facing) => At(u, v).Detail = (byte)((kind << 2) | (int)F(facing));
        void Light(int u, int v) => At(u, v).Ceiling = CeilingKind.LightOn;

        // The bedroom: the bed in its alcove (head to the east wall), the desk with the old computer, the open closet
        int bedding = rng.Range(0, 2);
        Put(17, 3, Props.L974Bed, ArchPier.West, 0 | (bedding << 1));
        Put(16, 3, Props.L974Bed, ArchPier.West, 1 | (bedding << 1));
        Put(17, 4, Props.L974Nightstand, ArchPier.West);
        Put(16, 4, Props.L974PlushHeap, ArchPier.West, rng.Range(0, 1));
        Put(12, 1, Props.L974Desk, ArchPier.East, 0);
        Put(12, 2, Props.L974Desk, ArchPier.East, 1);
        Put(13, 2, Props.L974Chair, ArchPier.West, 0);
        Put(12, 6, Props.L974Dresser, ArchPier.North);
        At(13, 6).Overhead = Overheads.L974ClosetRod;
        At(13, 6).Pier = F(ArchPier.North);
        Put(13, 3, Props.L974Rug, ArchPier.North, mirror ? 1 : 0);
        Put(14, 3, Props.L974Rug, ArchPier.North, mirror ? 0 : 1);
        Put(13, 4, Props.L974Rug, ArchPier.North, mirror ? 3 : 2);
        Put(14, 4, Props.L974Rug, ArchPier.North, mirror ? 2 : 3);
        // Three posters of the six, the shelves over the desk, fairy lights along the north wall
        var posters = new List<int> { 0, 1, 2, 3, 4, 5 };
        int Poster() { int i = rng.Range(0, posters.Count - 1); int p = posters[i]; posters.RemoveAt(i); return L974Hung.PosterFirst + p; }
        Hang(13, 1, Poster(), ArchPier.South);
        Hang(17, 1, Poster(), ArchPier.South);
        Hang(15, 6, Poster(), ArchPier.East);
        Hang(12, 1, L974Hung.ShelfPlush, ArchPier.East);
        Hang(12, 2, L974Hung.ShelfFigures, ArchPier.East);
        for (int u = 12; u <= 17; u++) At(u, 1).Depth = (byte)((L974HighFairy << 2) | (int)F(ArchPier.South));
        // The alcove's ceiling slopes down to the east wall over the bed
        foreach (var (u, h) in new[] { (16, 3), (17, 2) })
            foreach (int v in new[] { 3, 4 })
            {
                At(u, v).Height = (byte)h;
                At(u, v).Depth = (byte)((L974HighSlope << 2) | (int)F(ArchPier.East));
            }
        if (Version >= 5) At(13, 4).Under = Unders.L974Arrival;
        else At(14, 5).Under = Unders.L974Arrival;
        Light(14, 3);

        // The kitchen: fridge, pantry and counters down the west wall, the stove on the south; the dining corner's
        // banquette wrapping two sides of the table
        Put(1, 10, Props.L974Fridge, ArchPier.East);
        Put(1, 11, Props.L974Pantry, ArchPier.East);
        Put(1, 12, Props.L974Counter, ArchPier.East, 3);
        Put(1, 13, Props.L974Counter, ArchPier.East, 2);
        Put(1, 14, Props.L974Counter, ArchPier.East, 0);
        PutCorner(1, 15, Props.L974Counter, ArchPier.West, ArchPier.South, 1);
        Put(2, 15, Props.L974Stove, ArchPier.North);
        Put(3, 15, Props.L974Counter, ArchPier.North, 4);
        Put(5, 15, Props.L974Banquette, ArchPier.North, 0);
        Put(6, 15, Props.L974Banquette, ArchPier.North, 0);
        PutCorner(7, 15, Props.L974Banquette, ArchPier.South, ArchPier.East, 1);
        Put(7, 14, Props.L974Banquette, ArchPier.West, 0);
        Put(7, 13, Props.L974Banquette, ArchPier.West, 0);
        Put(6, 14, Props.L974Table, ArchPier.North);
        Put(5, 14, Props.L974Chair, ArchPier.East, 1);
        Put(6, 13, Props.L974Chair, ArchPier.South, 1);
        Hang(6, 9, L974Hung.CatClock, ArchPier.South);
        Light(4, 12);

        // The living room: nothing at all, as the canon has it, but its light
        Light(4, 4);

        // The hall: empty photo frames, a night light
        int frame = rng.Chance(0.5) ? L974Hung.FrameWhite : L974Hung.FrameGold;
        Hang(9, 6, frame, ArchPier.East);
        Hang(10, 2, frame, ArchPier.West);
        Hang(9, 14, frame, ArchPier.East);
        Hang(10, 11, frame, ArchPier.West);
        Hang(10, 8, L974Hung.NightLight, ArchPier.West);
        Light(9, 3);
        Light(10, 13);
        // (Layout version 5 on, a third downlight halfway down: with two, the hall was the darkest place in the house)
        if (Version >= 5) Light(9, 8);

        // The bathrooms
        Put(12, 8, Props.L974Basin, ArchPier.South);
        Put(14, 8, Props.L974Toilet, ArchPier.South);
        Put(14, 10, Props.L974Bathtub, ArchPier.West, 0);
        Put(13, 10, Props.L974Bathtub, ArchPier.West, 1);
        Hang(12, 8, L974Hung.Mirror, ArchPier.South);
        Hang(13, 8, L974Hung.TowelRail, ArchPier.South);
        Light(13, 9);
        Put(16, 8, Props.L974Basin, ArchPier.South);
        Put(17, 8, Props.L974Toilet, ArchPier.South);
        Hang(16, 8, L974Hung.Mirror, ArchPier.South);
        Light(16, 9);

        // The master bedroom: empty, but for a pink and white cat bed at the back wall
        Put(17, 14, Props.L974CatBed, ArchPier.West);
        Light(14, 13);

        // The walls take their finish from the rooms they face: tile round the bathrooms, subway tile behind the counters
        for (int v = 0; v < D; v++)
            for (int u = 0; u < W; u++)
            {
                ref Tile t = ref tiles[v * W + u];
                if (t.Kind != TileKind.Wall || t.Pattern != WallPattern.L974Paint) continue;
                bool bath = false, other = false, counter = false;
                foreach (var (du, dv) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                {
                    int nu = u + du, nv = v + dv;
                    if (nu < 0 || nv < 0 || nu >= W || nv >= D) continue;
                    Tile n = tiles[nv * W + nu];
                    if (n.Kind != TileKind.Floor) continue;
                    if (n.Zone is (byte)L974Room.Bath or (byte)L974Room.HalfBath) bath = true; else other = true;
                    if (n.Variant is Props.L974Counter or Props.L974Stove) counter = true;
                }
                if (bath && !other) t.Pattern = WallPattern.L974BathTile;
                else if (counter) t.Pattern = WallPattern.L974Backsplash;
            }

        // The windows: which half of each is on the left as seen from the room, and what each is a painting of
        for (int v = 0; v < D; v++)
            for (int u = 0; u < W; u++)
            {
                ref Tile t = ref tiles[v * W + u];
                if (t.Pattern != WallPattern.L974Window) continue;
                // Facing the window from inside, looking the opposite way to its facing: which neighbour is the other half
                bool otherIsGreater = t.Pier is ArchPier.North or ArchPier.South
                    ? u + 1 < W && tiles[v * W + u + 1].Pattern == WallPattern.L974Window
                    : v + 1 < D && tiles[(v + 1) * W + u].Pattern == WallPattern.L974Window;
                // Looking north (window faces south) the left is west; looking south, east; looking west (faces east), south; looking east, north
                bool leftIsLesser = t.Pier is ArchPier.South or ArchPier.West;
                t.Stack = (byte)(otherIsGreater == leftIsLesser ? 0 : 1);
            }
        int[] paintings = { rng.Range(0, 3), rng.Range(0, 3), rng.Range(0, 3), rng.Range(0, 3) };
        int window = 0;
        for (int v = 0; v < D; v++)
            for (int u = 0; u < W; u++)
            {
                ref Tile t = ref tiles[v * W + u];
                if (t.Pattern != WallPattern.L974Window) continue;
                // Both halves of a window share a painting: the pair are numbered by the half with the lesser coordinates
                bool first = t.Pier is ArchPier.North or ArchPier.South
                    ? u == 0 || tiles[v * W + u - 1].Pattern != WallPattern.L974Window
                    : v == 0 || tiles[(v - 1) * W + u].Pattern != WallPattern.L974Window;
                if (first) window++;
                t.Detail = (byte)paintings[Math.Min(window - 1, 3)];
            }
        return tiles;
    }

    /// <summary>Which of the level's props (<see cref="Props.L974First"/> to <see cref="Props.L974Last"/>) are walked through rather than around.</summary>
    private static bool L974WalkThrough(ushort variant) => variant == Props.L974Rug;

    // ================= What it is like =================

    private float L974Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level974];

    /// <summary>
    /// Reality stability here: the pink is kind (Baker-Miller pink calms). How it stops being kind for whoever stays too
    /// long is <c>L974System</c>'s, which knows how long each wanderer has been in.
    /// </summary>
    private float L974Stability(double x, double y, double z, int floorY, float drift) => 1.3f;
}
