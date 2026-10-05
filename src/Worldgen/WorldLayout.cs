using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Deterministic layout of the Backrooms. Everything is derived from the world seed and coordinates alone, so
/// chunks can be generated independently, in any order, and still line up.
///
/// The levels nest like blobs within blobs around the spawn point: Level 0 in the middle, Level 1 around it,
/// Level 2 beyond. Boundaries follow a noise-warped distance, so they are irregular and can leave islands.
///
/// The world is divided into 32x32 "macro cells", exactly one per chunk column, each belonging to one level.
/// Each macro cell owns the wall line on its west and north edge; whether those edges are walls, and where
/// their gaps are, is a pure function of the edge, so both neighbours agree. Where two levels meet, the edge
/// is a full-height wall with a few doorways through it. Every edge has at least one passage, so everything is
/// connected. Each level lays out the interior of its cells in its own partial class file.
/// </summary>
public sealed partial class WorldLayout
{
    public const int MacroSize = 32;

    private const ulong SaltEdgeWest = 0xED6E;
    private const ulong SaltEdgeNorth = 0xED6F;
    private const ulong SaltMacro = 0x3AC0;
    private const ulong SaltLevelWarp = 0x1E71;
    private const ulong SaltLevelDetail = 0x1E72;

    /// <summary>
    /// Noise-warped distance from spawn (in 32-block macro cells) at which each level ends; the last level goes on
    /// forever. Kept tight for testing (about 100 blocks per ring); multiply these to space the levels out.
    /// </summary>
    private static readonly double[] LevelRadii = { 4, 7, 10, 13, 16 };

    /// <summary>Number of levels, from Level 0 to the outermost one.</summary>
    public static int LevelCount => LevelRadii.Length + 1;

    private readonly ulong seed;
    private readonly int spawnMacroX;
    private readonly int spawnMacroZ;

    public WorldLayout(long seed, int spawnMacroX, int spawnMacroZ)
    {
        this.seed = (ulong)seed;
        this.spawnMacroX = spawnMacroX;
        this.spawnMacroZ = spawnMacroZ;
    }

    public static int MacroOf(int blockCoord) => Hashing.FloorDiv(blockCoord, MacroSize);

    public static int TileIndex(int lx, int lz) => lz * MacroSize + lx;

    private bool IsSpawnMacro(int mx, int mz) => mx == spawnMacroX && mz == spawnMacroZ;

    // ================= Levels =================

    /// <summary>Which level a macro cell belongs to.</summary>
    public int LevelAt(int mx, int mz)
    {
        double dx = mx - spawnMacroX, dz = mz - spawnMacroZ;
        double r = Math.Sqrt(dx * dx + dz * dz);
        if (r < 3) return 0;

        // Large-scale warp stretches the rings into blobs; small-scale detail roughens the edges and, now and
        // then, leaves an island of one level inside another
        double d = r * (1 + 0.3 * Fbm(mx / 9.0, mz / 9.0, SaltLevelWarp)) + 1.2 * Fbm(mx / 3.0, mz / 3.0, SaltLevelDetail);
        for (int level = 0; level < LevelRadii.Length; level++)
        {
            if (d < LevelRadii[level]) return level;
        }
        return LevelRadii.Length;
    }

    /// <summary>Smooth value noise in roughly [-1, 1].</summary>
    private double Noise(double x, double z, ulong salt)
    {
        int x0 = (int)Math.Floor(x), z0 = (int)Math.Floor(z);
        double fx = x - x0, fz = z - z0;
        double sx = fx * fx * (3 - 2 * fx), sz = fz * fz * (3 - 2 * fz);
        double c00 = Corner(x0, z0, salt), c10 = Corner(x0 + 1, z0, salt);
        double c01 = Corner(x0, z0 + 1, salt), c11 = Corner(x0 + 1, z0 + 1, salt);
        double top = c00 + (c10 - c00) * sx;
        double bottom = c01 + (c11 - c01) * sx;
        return top + (bottom - top) * sz;
    }

    private double Corner(int x, int z, ulong salt) => Hashing.Unit(Hashing.Hash(seed, x, z, salt)) * 2 - 1;

    private double Fbm(double x, double z, ulong salt) =>
        (Noise(x, z, salt) + 0.5 * Noise(x * 2.1, z * 2.1, salt + 1) + 0.25 * Noise(x * 4.3, z * 4.3, salt + 2)) / 1.75;

    // ================= Edges =================

    private enum EdgeTile : byte { Open, Wall, Doorway }

    private sealed class Edge
    {
        public readonly EdgeTile[] Tiles = new EdgeTile[MacroSize];
        public WallPattern Pattern;
        public BaseStyle Base;
        /// <summary>Walls between two levels run the full height of the taller one.</summary>
        public bool Tall;
        /// <summary>Doorways get a glowing EXIT sign above them.</summary>
        public bool ExitSigns;
    }

    /// <summary>
    /// The wall line on the west (x = mx*32) or north (z = mz*32) side of a macro cell. Index i is the offset
    /// along the line; index 0 is the shared corner post, which is decided separately.
    /// </summary>
    private Edge GetEdge(int mx, int mz, bool west)
    {
        int nx = west ? mx - 1 : mx;
        int nz = west ? mz : mz - 1;
        int level = LevelAt(mx, mz), otherLevel = LevelAt(nx, nz);
        var rng = new Rng(Hashing.Hash(seed, mx, mz, west ? SaltEdgeWest : SaltEdgeNorth));

        if (level != otherLevel) return LevelBoundaryEdge(ref rng, mx, mz, level);
        return level switch
        {
            0 => Level0Edge(ref rng, mx, mz, nx, nz),
            1 => Level1Edge(ref rng, mx, mz, nx, nz),
            2 => Level2Edge(ref rng),
            3 => Level3Edge(ref rng, mx, mz),
            4 => Level4Edge(ref rng, mx, mz, nx, nz),
            _ => Level5Edge(ref rng, mx, mz, nx, nz, west),
        };
    }

    /// <summary>A solid wall between two levels, pierced by a few doorways.</summary>
    private Edge LevelBoundaryEdge(ref Rng rng, int mx, int mz, int level)
    {
        WallPattern pattern = level == 0 ? RegionAt(mx, mz).PrimaryPattern : WallPattern.Chevron;
        pattern = level switch
        {
            0 => pattern,
            1 => WallPattern.Concrete,
            2 => WallPattern.Tunnel,
            3 => Level3Material(mx, mz),
            4 => WallPattern.Drywall,
            _ => WallPattern.Hotel,
        };
        var edge = new Edge { Pattern = pattern, Base = BaseFor(pattern), Tall = true, ExitSigns = level == 1 };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;

        int doors = rng.Range(2, 3);
        int spacing = (MacroSize - 4) / doors;
        for (int n = 0; n < doors; n++)
        {
            int start = 2 + n * spacing + rng.Range(0, spacing - 3);
            edge.Tiles[start] = edge.Tiles[start + 1] = EdgeTile.Doorway;
        }
        return edge;
    }

    /// <summary>
    /// Ambient temperature at a position: each level has its own, Level 3's flooded tunnels are freezing and
    /// Level 5's boiler halls are scorching.
    /// </summary>
    public float TemperatureAt(int x, int y, int z, int floorY)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        int level = LevelAt(mx, mz);
        if (level == 3 && y < floorY) return -4f;
        if (level == 5 && HotelZoneAt(mx, mz) == HotelZone.Boiler) return 42f;
        return LevelTemperatures[Math.Min(level, LevelTemperatures.Length - 1)];
    }

    private static readonly float[] LevelTemperatures = { 22f, 28f, 38f, 35f, 15f, 20f };

    /// <summary>Indices along an edge that can be walked through.</summary>
    private static List<int> Passages(Edge edge)
    {
        var list = new List<int>();
        for (int i = 1; i < MacroSize; i++)
        {
            if (edge.Tiles[i] != EdgeTile.Wall) list.Add(i);
        }
        return list;
    }

    // ================= Macro cells =================

    private sealed class Builder
    {
        public readonly Tile[] Tiles = new Tile[MacroSize * MacroSize];
        public readonly LightMood[] Mood = new LightMood[MacroSize * MacroSize];
        public Rng Rng;
        public int Level;
        public ZoneKind Zone;
        public WallPattern Primary;
        public bool IsSpawn;

        public ref Tile At(int lx, int lz) => ref Tiles[TileIndex(lx, lz)];
    }

    /// <summary>Lays out one macro cell. Tiles are indexed by <see cref="TileIndex"/>.</summary>
    public Tile[] BuildMacro(int mx, int mz)
    {
        var b = new Builder
        {
            Rng = new Rng(Hashing.Hash(seed, mx, mz, SaltMacro)),
            Level = LevelAt(mx, mz),
            IsSpawn = IsSpawnMacro(mx, mz),
        };

        Edge west = GetEdge(mx, mz, west: true);
        Edge north = GetEdge(mx, mz, west: false);
        BuildEdges(b, mx, mz, west, north);

        switch (b.Level)
        {
            case 0: BuildLevel0(b, mx, mz); break;
            case 1: BuildLevel1(b, mx, mz); break;
            case 2: BuildLevel2(b, mx, mz, west, north); break;
            case 3: BuildLevel3(b, mx, mz, west, north); break;
            case 4: BuildLevel4(b, mx, mz); break;
            default: BuildLevel5(b, mx, mz, west, north); break;
        }

        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Level = (byte)b.Level;
        return b.Tiles;
    }

    private void BuildEdges(Builder b, int mx, int mz, Edge west, Edge north)
    {
        for (int i = 1; i < MacroSize; i++)
        {
            ApplyEdgeTile(ref b.At(0, i), west, west.Tiles[i]);
            ApplyEdgeTile(ref b.At(i, 0), north, north.Tiles[i]);
        }

        // The corner post stands whenever any of the four edge segments meeting there is solid
        Edge westOfCorner = GetEdge(mx - 1, mz, west: false);
        Edge northOfCorner = GetEdge(mx, mz - 1, west: true);
        bool post = west.Tiles[1] != EdgeTile.Open || north.Tiles[1] != EdgeTile.Open
            || westOfCorner.Tiles[MacroSize - 1] != EdgeTile.Open || northOfCorner.Tiles[MacroSize - 1] != EdgeTile.Open;
        if (!post) return;

        ref Tile corner = ref b.At(0, 0);
        SetWall(ref corner, west.Pattern, west.Base);
        int level = LevelAt(mx, mz);
        corner.Tall = LevelAt(mx - 1, mz) != level || LevelAt(mx, mz - 1) != level || LevelAt(mx - 1, mz - 1) != level;
    }

    private static void ApplyEdgeTile(ref Tile tile, Edge edge, EdgeTile kind)
    {
        if (kind == EdgeTile.Open) return;
        SetWall(ref tile, edge.Pattern, edge.Base);
        if (kind == EdgeTile.Doorway)
        {
            tile.Kind = TileKind.Doorway;
            tile.ExitSign = edge.ExitSigns;
        }
        tile.Tall = edge.Tall;
    }

    // ================= Spawn =================

    /// <summary>The spawn point: the open floor tile closest to the centre of the spawn macro cell.</summary>
    public (int X, int Z) FindSpawn()
    {
        Tile[] tiles = BuildMacro(spawnMacroX, spawnMacroZ);
        (int lx, int lz) = FindSpawnTile(tiles);
        return (spawnMacroX * MacroSize + lx, spawnMacroZ * MacroSize + lz);
    }

    private static (int, int) FindSpawnTile(Tile[] tiles)
    {
        const int c = MacroSize / 2;
        for (int r = 0; r < c; r++)
        {
            for (int dz = -r; dz <= r; dz++)
            {
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    Tile t = tiles[TileIndex(c + dx, c + dz)];
                    if (t.Kind == TileKind.Floor && !t.SupplyBox) return (c + dx, c + dz);
                }
            }
        }
        return (c, c);
    }

    /// <summary>One supply box a couple of steps from the spawn point, so the first minutes are survivable.</summary>
    private static void PlaceSpawnBox(Builder b)
    {
        (int sx, int sz) = FindSpawnTile(b.Tiles);
        foreach ((int dx, int dz) in new[] { (2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2), (1, 0), (0, 1) })
        {
            int x = sx + dx, z = sz + dz;
            if (!InInterior(x, z)) continue;
            ref Tile tile = ref b.At(x, z);
            if (tile.Kind != TileKind.Floor) continue;
            tile.SupplyBox = true;
            return;
        }
    }

    // ================= Helpers =================

    private static bool InInterior(int x, int z) => x >= 1 && x < MacroSize && z >= 1 && z < MacroSize;

    private static void SetWall(ref Tile tile, WallPattern pattern, BaseStyle baseStyle)
    {
        tile.Kind = TileKind.Wall;
        tile.Pattern = pattern;
        tile.Base = baseStyle;
        tile.SupplyBox = false;
    }

    /// <summary>Mostly the area's own wallpaper, with the occasional odd wall, like the original photo.</summary>
    private static WallPattern RollPattern(ref Rng rng, WallPattern primary)
    {
        if (rng.Chance(0.9)) return primary;
        return primary == WallPattern.Chevron ? WallPattern.Dotted : WallPattern.Chevron;
    }

    /// <summary>
    /// Each wallpaper always has the same trim, matching the 2002 photos: the chevron paper meets the floor with a
    /// thin dark baseboard, the dotted paper has a low brown chair rail.
    /// </summary>
    private static BaseStyle BaseFor(WallPattern pattern) => pattern switch
    {
        WallPattern.Chevron => BaseStyle.Baseboard,
        WallPattern.Dotted => BaseStyle.Rail,
        WallPattern.Manila => BaseStyle.Baseboard,
        _ => BaseStyle.Plain,
    };
}
