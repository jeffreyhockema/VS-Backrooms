using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 73, "The Redlands" (experimental): kept as level 21 (<see cref="Level73"/>) and shown as "73". One island of
/// crimson-black ground in a dark sea, under a night that never ends and a full moon that never moves; on its highest
/// point the Silver Castle, the only building and the only safe place. The design is in
/// docs/design/experimental-levels/73-plan.md (after the Wikidot page by Kitty Rika). A prototype: no thresholds in or
/// out (the cheats menu or <c>/backrooms goto</c> only), no entities, no loot.
///
/// <para><b>The region</b> is round, <see cref="L73Radius"/> cells, far out to the north-north-west (the mirror of
/// Level 188's), under the open sky. Its rim cells are a cliff of black rock round the sea. The island (centre
/// <see cref="L73IslandX"/>, <see cref="L73IslandZ"/>, radius about <see cref="L73IslandRadius"/>) is a pure function of
/// the block position (<see cref="L73Ground"/>): a low dome, a scatter of hills, red gullies, an ash beach, and the sea
/// falling to ten blocks deep beyond it. The level's floor is the sea's surface: a land tile's <see cref="Tile.Height"/>
/// is its ground above it, a sea tile's <see cref="Tile.Depth"/> how far down its bed lies.</para>
///
/// <para><b>The castle</b> (<see cref="L73CastleAt"/>, castle-local u east, v south from <see cref="L73CastleX0"/>,
/// <see cref="L73CastleZ0"/>) stands level on the summit plateau (<see cref="L73Plateau"/>): a curtain wall with four
/// corner towers, a gatehouse in the south wall, a stone path to the keep's door, and the keep: on the ground storey the
/// main hall (the stair up along its north wall) and the dining hall with its hearth; above, a landing, two bedrooms and
/// a bathroom (<see cref="L73UpperAt"/>); a flat roof with a parapet and four turrets.</para>
///
/// <para><b>Tiles:</b> <see cref="Tile.Zone"/> 1 land, 2 sea, 3 the courtyard (and its path and gate), 4 the keep's
/// inside, 5 the castle's walls, 9 the rim.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2100-0x21BF are this level's (0x21C0-0x21FF its thresholds').</summary>
    private const ulong SaltL73Shape = 0x2101, SaltL73Centre = 0x2102, SaltL73Coast = 0x2103, SaltL73Hill = 0x2104, SaltL73Rough = 0x2105,
        SaltL73Gully = 0x2106, SaltL73Outcrop = 0x2107, SaltL73Bed = 0x2108;

    /// <summary>The zones (<see cref="Tile.Zone"/>).</summary>
    public const byte L73Land = 1, L73Sea = 2, L73Court = 3, L73Keep = 4, L73Walls = 5, L73RimZone = 9;

    /// <summary>The summit plateau's ground above the sea (the castle's floor), and the highest any other ground goes.</summary>
    public const int L73Plateau = 9, L73Peak = 12;

    /// <summary>The island's average radius in blocks (its coast wanders a fifth either way).</summary>
    public const int L73IslandRadius = 230;

    /// <summary>The castle's square (u by v), and the keep in it (from its own corner, u by v).</summary>
    public const int L73CastleW = 48, L73CastleD = 40, L73KeepU0 = 10, L73KeepV0 = 5, L73KeepW = 28, L73KeepD = 20;

    /// <summary>Heights in the keep above its floor: the upper storey's floor slab, and the roof slab.</summary>
    public const int L73UpperSlab = 6, L73RoofSlab = 11;

    /// <summary>What a place in the castle is.</summary>
    public enum L73Part : byte
    {
        Outside, Court, Path, Gate, Curtain, Tower, GateTower, KeepWall, Door, Hall, Dining, Hearth, Jamb, Stair, Partition,
        // The upper storey only
        Landing, UpDoor, Hole, BedWest, Bath, BedEast,
    }

    /// <summary>The castle's furnishings.</summary>
    public enum L73Thing : byte
    {
        None, Sconce, Chandelier, Bookshelf, Clock, Candelabra, Table, Chair, BedHead, BedFoot, Nightstand, Wardrobe, TubHead, TubFoot, Toilet,
    }

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees west of north.</summary>
    private double L73Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int L73CentreX => spawnMacroX - (int)Math.Round(L73Reach * Math.Sin(Math.PI / 8));
    private int L73CentreZ => spawnMacroZ - (int)Math.Round(L73Reach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells: sixteen (512 blocks), whatever the world's size: the island and its sea.</summary>
    private int L73Radius => 16;

    private bool InL73(double mx, double mz) => InRoundRegion(mx, mz, L73CentreX, L73CentreZ, L73Radius, SaltL73Shape);

    /// <summary>The middle of the island (and of the castle), in blocks: near the region's centre, moved a little by the seed.</summary>
    public int L73IslandX => L73CentreX * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(Hashing.Hash(seed, 0, 0, SaltL73Centre)) * 33) - 16;
    public int L73IslandZ => L73CentreZ * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(Hashing.Mix(Hashing.Hash(seed, 0, 0, SaltL73Centre))) * 33) - 16;

    /// <summary>The castle's north-west corner, in blocks.</summary>
    public int L73CastleX0 => L73IslandX - L73CastleW / 2;
    public int L73CastleZ0 => L73IslandZ - L73CastleD / 2;

    /// <summary>The middle of the gate, in blocks (in the south wall).</summary>
    public (int X, int Z) L73Gate => (L73CastleX0 + 24, L73CastleZ0 + L73CastleD - 1);

    /// <summary>The hearth in the dining hall, in blocks (its first fire tile).</summary>
    public (int X, int Z) L73Hearth => (L73CastleX0 + L73KeepU0 + 26, L73CastleZ0 + L73KeepV0 + 9);

    /// <summary>
    /// A place to look for somewhere to arrive: out on the island 85 to 165 blocks from the gate, the castle on its hill
    /// in sight (the spot test keeps it on dry land).
    /// </summary>
    private (int Mx, int Mz) L73ArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, r = 85 + 80 * Hashing.Unit(Hashing.Mix(h));
        var (gx, gz) = L73Gate;
        return (MacroOf(gx + (int)Math.Round(Math.Cos(angle) * r)), MacroOf(gz + (int)Math.Round(Math.Sin(angle) * r)));
    }

    /// <summary>Arriving: on the island's dry ground, above the beach, never in a gully or the castle.</summary>
    private static bool IsL73ArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Zone == L73Land && t.Height >= 2 && t.Floor != FloorKind.L73Mud;

    /// <summary>How high above the level's floor (the sea) to put someone down: on the ground.</summary>
    private static double L73ArrivalHeight(in Tile t, double stand) => t.Height + stand;

    // ================= The island =================

    private static double L73Smooth(double t) => t * t * (3 - 2 * t);

    /// <summary>How far a block position lies beyond the coast (negative inland), and its distance from the island's middle.</summary>
    public double L73Shore(int gx, int gz, out double d)
    {
        double ux = gx - L73IslandX, uz = gz - L73IslandZ;
        d = Math.Sqrt(ux * ux + uz * uz);
        return d - L73IslandRadius * (1 + 0.2 * Fbm(ux / 120.0, uz / 120.0, SaltL73Coast));
    }

    /// <summary>The hills: low domes on a jittered lattice, the highest of those round a position (none near the castle).</summary>
    private double L73Hills(double ux, double uz)
    {
        const int pitch = 44;
        int hi = (int)Math.Floor(ux / pitch), hj = (int)Math.Floor(uz / pitch);
        double best = 0;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                ulong h = Hashing.Hash(seed, hi + di, hj + dj, SaltL73Hill);
                if (Hashing.Unit(h) < 0.25) continue; // a gap in the hills
                ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3);
                double cx = (hi + di + 0.2 + 0.6 * Hashing.Unit(h2)) * pitch, cz = (hj + dj + 0.2 + 0.6 * Hashing.Unit(h3)) * pitch;
                if (cx * cx + cz * cz < 90 * 90) continue;
                double radius = 12 + 10 * Hashing.Unit(h4), height = 2 + 2.5 * Hashing.Unit(Hashing.Mix(h4));
                double dx = ux - cx, dz = uz - cz, q = (dx * dx + dz * dz) / (radius * radius);
                if (q < 1) best = Math.Max(best, height * (1 - q));
            }
        return best;
    }

    /// <summary>
    /// The ground at a block position, in blocks above the sea (negative under it), and what it is made of: the island's
    /// dome, its hills and roughness, eased down to the beach over its last forty blocks; the summit level for the
    /// castle; gullies cut along the zero lines of a noise; and beyond the coast the seabed, falling to ten blocks deep.
    /// </summary>
    public int L73Ground(int gx, int gz, out FloorKind floor)
    {
        double beyond = L73Shore(gx, gz, out double d), ri = d - beyond;
        double ux = gx - L73IslandX, uz = gz - L73IslandZ;
        double f;
        bool gully = false;
        if (beyond < 0)
        {
            double t = 1 - d / ri;
            double dome = 8.5 * Math.Pow(Math.Max(0, t), 0.7);
            double rough = 1.2 * Fbm(ux / 22.0, uz / 22.0, SaltL73Rough);
            double coast = L73Smooth(Math.Clamp(-beyond / 40.0, 0, 1));
            f = 1 + (dome + L73Hills(ux, uz) + rough) * coast;
            // The summit, levelled for the castle
            if (d < 56)
            {
                double s = L73Smooth(Math.Clamp((d - 36) / 20.0, 0, 1));
                f = L73Plateau * (1 - s) + f * s;
            }
            // Gullies of red mud, along the zero lines of a noise, away from the summit and the beach
            else if (f > 3.5)
            {
                double n = Math.Abs(Noise(ux / 55.0, uz / 55.0, SaltL73Gully));
                if (n < 0.07)
                {
                    double cut = 3 * (1 - n / 0.07);
                    f -= cut;
                    gully = cut > 0.8;
                }
            }
        }
        else f = 0.6 - 11 * L73Smooth(Math.Clamp(beyond / 110.0, 0, 1));
        int g = Math.Clamp((int)Math.Round(f), -11, L73Peak);

        if (g < 0) floor = Noise(gx / 14.0, gz / 14.0, SaltL73Bed) > 0.2 ? FloorKind.L73Gravel : FloorKind.L73Seabed;
        else if (g <= 1) floor = FloorKind.L73Ash;
        else if (gully) floor = FloorKind.L73Mud;
        else if (g >= 11 || Noise(gx / 9.0, gz / 9.0, SaltL73Outcrop) > 0.55) floor = FloorKind.L73Rock;
        else floor = FloorKind.L73Floor;
        return g;
    }

    // ================= The castle =================

    /// <summary>What a castle-local position is on the ground storey (Outside beyond the castle's square).</summary>
    public static L73Part L73CastleAt(int u, int v)
    {
        if (u < 0 || v < 0 || u >= L73CastleW || v >= L73CastleD) return L73Part.Outside;
        bool gateway = u >= 22 && u <= 25;
        if (v >= L73CastleD - 2 && gateway) return L73Part.Gate;
        if ((u < 6 || u >= L73CastleW - 6) && (v < 6 || v >= L73CastleD - 6)) return L73Part.Tower;
        if (v >= L73CastleD - 5 && (u is >= 18 and <= 21 || u is >= 26 and <= 29)) return L73Part.GateTower;
        if (u < 2 || v < 2 || u >= L73CastleW - 2 || v >= L73CastleD - 2) return L73Part.Curtain;
        int ku = u - L73KeepU0, kv = v - L73KeepV0;
        if (ku >= 0 && kv >= 0 && ku < L73KeepW && kv < L73KeepD) return L73KeepAt(ku, kv);
        return gateway && v >= L73KeepV0 + L73KeepD ? L73Part.Path : L73Part.Court;
    }

    /// <summary>Whether a keep-local position is on the keep's outer wall.</summary>
    public static bool L73KeepRing(int ku, int kv) => ku == 0 || kv == 0 || ku == L73KeepW - 1 || kv == L73KeepD - 1;

    /// <summary>The keep's ground storey, keep-local: the main hall (west), the dining hall (east), the stair, the hearth.</summary>
    public static L73Part L73KeepAt(int ku, int kv)
    {
        if (L73KeepRing(ku, kv)) return kv == L73KeepD - 1 && ku is 13 or 14 ? L73Part.Door : L73Part.KeepWall;
        if (ku == 16) return kv is 9 or 10 ? L73Part.Hall : L73Part.Partition;
        if (kv is 1 or 2 && ku is >= 3 and <= 8) return L73Part.Stair;
        if (ku == 26 && kv is 9 or 10) return L73Part.Hearth;
        if (ku == 26 && kv is 8 or 11) return L73Part.Jamb;
        return ku < 16 ? L73Part.Hall : L73Part.Dining;
    }

    /// <summary>The keep's upper storey, keep-local: a landing along the north, two bedrooms and a bathroom off it.</summary>
    public static L73Part L73UpperAt(int ku, int kv)
    {
        if (L73KeepRing(ku, kv)) return L73Part.KeepWall;
        if (kv is 1 or 2 && ku is >= 3 and <= 8) return L73Part.Hole;
        if (kv <= 3) return L73Part.Landing;
        if (kv == 4) return ku is 5 or 13 or 21 ? L73Part.UpDoor : L73Part.Partition;
        if (ku is 10 or 16) return L73Part.Partition;
        return ku < 10 ? L73Part.BedWest : ku < 16 ? L73Part.Bath : L73Part.BedEast;
    }

    /// <summary>The step of the stair up at a keep-local position (1 to 6, climbing east), or 0.</summary>
    public static int L73StairStep(int ku, int kv) => kv is 1 or 2 && ku is >= 3 and <= 8 ? ku - 2 : 0;

    /// <summary>Whether a keep-local position on the outer wall has a (boarded) window, on the ground storey or the upper one.</summary>
    public static bool L73Window(int ku, int kv, bool upper)
    {
        if (!L73KeepRing(ku, kv)) return false;
        if (kv == 0 || kv == L73KeepD - 1) return ku % 4 == 2 && ku < L73KeepW - 2 && !(kv == L73KeepD - 1 && ku is >= 12 and <= 15);
        return kv % 4 == 2 && kv < L73KeepD - 2 && !(!upper && ku == L73KeepW - 1 && kv is >= 8 and <= 11);
    }

    /// <summary>The furnishings, keep-local (the upper storey's apart), with the way each faces.</summary>
    private static readonly Dictionary<(int, int, bool), (L73Thing Thing, ArchPier Facing)> L73Furnishings = PlanL73Furnishings();

    private static Dictionary<(int, int, bool), (L73Thing, ArchPier)> PlanL73Furnishings()
    {
        var f = new Dictionary<(int, int, bool), (L73Thing, ArchPier)>();
        void Put(int ku, int kv, bool upper, L73Thing thing, ArchPier facing) => f[(ku, kv, upper)] = (thing, facing);
        // The main hall: bookshelves on the west wall, a clock, candelabras, a chandelier, sconces
        for (int kv = 9; kv <= 12; kv++) Put(1, kv, false, L73Thing.Bookshelf, ArchPier.East);
        Put(15, 4, false, L73Thing.Clock, ArchPier.West);
        Put(3, 17, false, L73Thing.Candelabra, ArchPier.North);
        Put(12, 17, false, L73Thing.Candelabra, ArchPier.North);
        Put(7, 9, false, L73Thing.Chandelier, ArchPier.North);
        Put(7, 14, false, L73Thing.Chandelier, ArchPier.North);
        Put(1, 5, false, L73Thing.Sconce, ArchPier.East); Put(1, 15, false, L73Thing.Sconce, ArchPier.East);
        Put(15, 7, false, L73Thing.Sconce, ArchPier.West); Put(15, 14, false, L73Thing.Sconce, ArchPier.West);
        Put(5, 18, false, L73Thing.Sconce, ArchPier.North); Put(9, 18, false, L73Thing.Sconce, ArchPier.North);
        // The dining hall: the long table set with chairs, the hearth at its east end, candelabras in the corners
        for (int ku = 19; ku <= 24; ku++)
        {
            Put(ku, 9, false, L73Thing.Table, ArchPier.North);
            Put(ku, 10, false, L73Thing.Table, ArchPier.North);
            Put(ku, 8, false, L73Thing.Chair, ArchPier.South);
            Put(ku, 11, false, L73Thing.Chair, ArchPier.North);
        }
        Put(18, 2, false, L73Thing.Candelabra, ArchPier.North);
        Put(18, 17, false, L73Thing.Candelabra, ArchPier.North);
        Put(17, 5, false, L73Thing.Sconce, ArchPier.East); Put(17, 14, false, L73Thing.Sconce, ArchPier.East);
        Put(26, 4, false, L73Thing.Sconce, ArchPier.West); Put(26, 15, false, L73Thing.Sconce, ArchPier.West);
        Put(21, 1, false, L73Thing.Sconce, ArchPier.South); Put(21, 18, false, L73Thing.Sconce, ArchPier.North);
        // Upstairs: the landing, the west bedroom, the bathroom, the east bedroom (a bed's facing points head to foot)
        Put(12, 1, true, L73Thing.Sconce, ArchPier.South); Put(20, 1, true, L73Thing.Sconce, ArchPier.South);
        foreach (int bed in new[] { 5, 21 })
        {
            Put(bed, 18, true, L73Thing.BedHead, ArchPier.North);
            Put(bed, 17, true, L73Thing.BedFoot, ArchPier.North);
            Put(bed - 1, 18, true, L73Thing.Nightstand, ArchPier.North);
            Put(bed + 1, 18, true, L73Thing.Nightstand, ArchPier.North);
        }
        Put(1, 8, true, L73Thing.Wardrobe, ArchPier.East);
        Put(26, 8, true, L73Thing.Wardrobe, ArchPier.West);
        Put(1, 12, true, L73Thing.Sconce, ArchPier.East); Put(9, 12, true, L73Thing.Sconce, ArchPier.West);
        Put(17, 12, true, L73Thing.Sconce, ArchPier.East); Put(26, 12, true, L73Thing.Sconce, ArchPier.West);
        Put(13, 18, true, L73Thing.TubHead, ArchPier.North);
        Put(13, 17, true, L73Thing.TubFoot, ArchPier.North);
        Put(11, 7, true, L73Thing.Toilet, ArchPier.East);
        Put(15, 11, true, L73Thing.Sconce, ArchPier.West);
        return f;
    }

    /// <summary>What stands at a keep-local position (on the ground storey, or the upper one), and which way it faces.</summary>
    public static (L73Thing Thing, ArchPier Facing) L73FurnishingAt(int ku, int kv, bool upper) =>
        L73Furnishings.TryGetValue((ku, kv, upper), out var f) ? f : (L73Thing.None, ArchPier.North);

    /// <summary>Whether a block position is inside the keep's square (its walls included).</summary>
    public bool InL73Keep(int gx, int gz)
    {
        int ku = gx - L73CastleX0 - L73KeepU0, kv = gz - L73CastleZ0 - L73KeepV0;
        return ku >= 0 && kv >= 0 && ku < L73KeepW && kv < L73KeepD;
    }

    /// <summary>Whether a block position is in the keep's dining hall (where the hearth keeps it warm).</summary>
    public bool InL73Dining(int gx, int gz)
    {
        int ku = gx - L73CastleX0 - L73KeepU0, kv = gz - L73CastleZ0 - L73KeepV0;
        return ku is >= 17 and <= 26 && kv is >= 1 and <= 18;
    }

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the island is laid out tile by tile).</summary>
    private Edge L73Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L73Wall };

    /// <summary>Lays out one of the level's cells: the rim's cliff, or the island, its sea and the castle, tile by tile.</summary>
    private void BuildLevel73(Builder b, int mx, int mz)
    {
        // The rim: a cliff of black rock all the way round the sea
        bool rim = false;
        for (int dz = -1; dz <= 1 && !rim; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Level73) { rim = true; break; }

        int cx0 = L73CastleX0, cz0 = L73CastleZ0;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (rim)
                {
                    t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L73Rim, Floor = FloorKind.L73Rock, Zone = L73RimZone };
                    continue;
                }
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                L73Part part = L73CastleAt(gx - cx0, gz - cz0);
                t = part == L73Part.Outside ? L73Terrain(gx, gz, cx0, cz0) : L73CastleTile(part, gx - cx0, gz - cz0);
            }
    }

    private Tile L73Terrain(int gx, int gz, int cx0, int cz0)
    {
        int g = L73Ground(gx, gz, out FloorKind floor);
        var t = new Tile { Kind = TileKind.Floor, Floor = floor, Zone = g < 0 ? L73Sea : L73Land, Height = (byte)Math.Max(0, g), Depth = (byte)Math.Max(0, -g) };
        // The stone path runs on out of the gate and down the hill
        int u = gx - cx0, v = gz - cz0;
        if (g > 0 && u is >= 22 and <= 25 && v >= L73CastleD && v < L73CastleD + 26) t.Floor = FloorKind.L73Path;
        return t;
    }

    private static Tile L73CastleTile(L73Part part, int u, int v)
    {
        var t = new Tile { Height = L73Plateau };
        switch (part)
        {
            case L73Part.Court: t.Kind = TileKind.Floor; t.Floor = FloorKind.L73Court; t.Zone = L73Court; break;
            case L73Part.Path or L73Part.Gate: t.Kind = TileKind.Floor; t.Floor = FloorKind.L73Path; t.Zone = L73Court; break;
            case L73Part.Door: t.Kind = TileKind.Doorway; t.Pattern = WallPattern.L73Wall; t.Floor = FloorKind.L73Path; t.Zone = L73Keep; break;
            case L73Part.Hall or L73Part.Hearth: t.Kind = TileKind.Floor; t.Floor = FloorKind.L73Carpet; t.Zone = L73Keep; break;
            case L73Part.Dining: t.Kind = TileKind.Floor; t.Floor = FloorKind.L73Boards; t.Zone = L73Keep; break;
            case L73Part.Stair:
                t.Kind = TileKind.Floor; t.Floor = FloorKind.L73Carpet; t.Zone = L73Keep;
                t.Stair = (byte)L73StairStep(u - L73KeepU0, v - L73KeepV0); t.Pier = ArchPier.East;
                break;
            default: t.Kind = TileKind.Wall; t.Pattern = WallPattern.L73Wall; t.Floor = FloorKind.L73Court; t.Zone = L73Walls; break;
        }
        if (part == L73Part.Hearth) t.Sealed = true; // nobody is put down in the fire
        return t;
    }

    /// <summary>Which of the level's props (<see cref="Props.L73First"/>-<see cref="Props.L73Last"/>) people walk through: none (it has none).</summary>
    private static bool L73WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: near freezing out on the island; mild in the keep, warm in the dining hall by the fire.</summary>
    private float L73Temperature(int x, int y, int z, int floorY)
    {
        int rel = y - floorY;
        if (InL73Keep(x, z) && rel > L73Plateau && rel <= L73Plateau + L73RoofSlab)
            return InL73Dining(x, z) && rel <= L73Plateau + L73UpperSlab ? 22f : 15f;
        return 4f;
    }

    /// <summary>Reality stability: a slow drain out on the island and the sea; none within the castle's walls.</summary>
    private float L73Stability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        return t.Zone is L73Court or L73Keep or L73Walls ? 1f : 0.9f;
    }
}
