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
    private const ulong SaltRingShape = 0x1E73;
    private const ulong SaltLevelBlob = 0x1E74;

    /// <summary>
    /// The average width of each level's ring, in 32-block macro cells (Level 0's is its radius); the last level
    /// goes on forever. Level 0 alone averages over a kilometre from spawn to its edge, and reaching Level 10 is a
    /// journey of many kilometres. No ring is a circle: each is stretched by its own <see cref="RingShape"/>, so in
    /// one direction a level may end after a few hundred blocks and in another go on for several times that.
    /// </summary>
    private static readonly double[] RingWidths = { 36, 28, 20, 24, 30, 30, 24, 30, 24, 30 };

    /// <summary>How strongly the rings are stretched: each ring's width varies by about e^±Stretch with direction.</summary>
    private const double Stretch = 1.45;

    /// <summary>Waves round the circle that shape each ring: the first few stretch it, the rest make it lumpy.</summary>
    private const int ShapeHarmonics = 7;

    /// <summary>Number of levels, from Level 0 to the outermost ring and Level 11, the city beyond it.</summary>
    public static int LevelCount => RingWidths.Length + 2;

    private readonly ulong seed;
    private readonly int spawnMacroX;
    private readonly int spawnMacroZ;

    // Each ring's shape: the amplitude and phase of its waves round the circle
    private readonly double[,] shapeAmplitude = new double[RingWidths.Length, ShapeHarmonics + 1];
    private readonly double[,] shapePhase = new double[RingWidths.Length, ShapeHarmonics + 1];

    // The level of every cell asked about so far (it is asked about constantly)
    private readonly System.Collections.Concurrent.ConcurrentDictionary<long, byte> levelCache = new();

    public WorldLayout(long seed, int spawnMacroX, int spawnMacroZ)
    {
        this.seed = (ulong)seed;
        this.spawnMacroX = spawnMacroX;
        this.spawnMacroZ = spawnMacroZ;

        for (int ring = 0; ring < RingWidths.Length; ring++)
        {
            double total = 0;
            for (int h = 1; h <= ShapeHarmonics; h++)
            {
                ulong hash = Hashing.Hash(this.seed, ring, h, SaltRingShape);
                // Low waves stretch the ring into an oval or a lopsided egg; higher ones only roughen it
                double weight = h <= 3 ? 1.0 / h : 0.18 / h;
                shapeAmplitude[ring, h] = weight * (0.35 + 0.65 * Hashing.Unit(hash));
                shapePhase[ring, h] = Hashing.Unit(Hashing.Mix(hash)) * Math.PI * 2;
                total += shapeAmplitude[ring, h];
            }
            for (int h = 1; h <= ShapeHarmonics; h++) shapeAmplitude[ring, h] /= total;
        }
    }

    public static int MacroOf(int blockCoord) => Hashing.FloorDiv(blockCoord, MacroSize);

    public static int TileIndex(int lx, int lz) => lz * MacroSize + lx;

    private bool IsSpawnMacro(int mx, int mz) => mx == spawnMacroX && mz == spawnMacroZ;

    // ================= Levels =================

    /// <summary>Which level a macro cell belongs to.</summary>
    public int LevelAt(int mx, int mz)
    {
        long key = ((long)mx << 32) | (uint)mz;
        if (levelCache.TryGetValue(key, out byte cached)) return cached;
        int level = ComputeLevel(mx, mz);
        levelCache.TryAdd(key, (byte)level);
        return level;
    }

    private int ComputeLevel(double mx, double mz)
    {
        double dx = mx - spawnMacroX, dz = mz - spawnMacroZ;
        if (dx * dx + dz * dz < 9) return 0;
        double d = RingDistance(mx, mz), angle = Math.Atan2(dz, dx), edge = 0;
        for (int ring = 0; ring < RingWidths.Length; ring++)
        {
            edge += RingWidths[ring] * RingShape(ring, angle);
            if (d < edge) return ring;
        }
        // Far out in the fields lies the city, which no ring reaches
        return InCity(mx, mz) ? 11 : RingWidths.Length;
    }

    /// <summary>
    /// How much wider or narrower than its average a ring is in a direction from spawn (an angle in radians):
    /// e to the power of a few random waves round the circle, so it is always positive and the rings always nest.
    /// </summary>
    private double RingShape(int ring, double angle)
    {
        double wave = 0;
        for (int h = 1; h <= ShapeHarmonics; h++) wave += shapeAmplitude[ring, h] * Math.Cos(h * angle + shapePhase[ring, h]);
        // However the rings are stretched, Level 0 is always vast, and no ring ever thins to nothing
        return Math.Max(ring == 0 ? 0.6 : 0.3, Math.Exp(Stretch * wave));
    }

    /// <summary>Distance from spawn, along a direction, at which a level ends.</summary>
    private double OuterEdge(int level, double angle)
    {
        double edge = 0;
        for (int ring = 0; ring <= Math.Min(level, RingWidths.Length - 1); ring++) edge += RingWidths[ring] * RingShape(ring, angle);
        return edge;
    }

    /// <summary>Distance from spawn, along a direction, at which a level begins.</summary>
    private double InnerEdge(int level, double angle) => level <= 0 ? 0 : OuterEdge(level - 1, angle);

    /// <summary>
    /// The warped distance from spawn (in macro cells) that is compared with the ring edges. Blobs and smaller
    /// lumps make the edges wander, and now and then leave an island of one level inside another.
    /// </summary>
    private double RingDistance(double mx, double mz)
    {
        double dx = mx - spawnMacroX, dz = mz - spawnMacroZ;
        double r = Math.Sqrt(dx * dx + dz * dz);
        return r * (1 + 0.08 * Fbm(mx / 30.0, mz / 30.0, SaltLevelBlob)) + 3.0 * Fbm(mx / 8.0, mz / 8.0, SaltLevelWarp)
            + 0.9 * Fbm(mx / 2.5, mz / 2.5, SaltLevelDetail);
    }

    /// <summary>How far through its ring a block lies, from 0 at the inner edge to 1 at the outer.</summary>
    private double RingFraction(int gx, int gz, int level)
    {
        if (level <= 0 || level >= RingWidths.Length) return 0.5;
        double mx = gx / (double)MacroSize, mz = gz / (double)MacroSize;
        double angle = Math.Atan2(mz - spawnMacroZ, mx - spawnMacroX);
        double inner = InnerEdge(level, angle), outer = OuterEdge(level, angle);
        return Math.Clamp((RingDistance(mx, mz) - inner) / (outer - inner), 0, 1);
    }

    /// <summary>Levels under the open sky rather than a ceiling.</summary>
    public static bool IsOpenSky(int level) => level >= 9;

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

        if (level != otherLevel)
        {
            bool halls = level == 1 && IsLevel1Corridors(mx, mz) || otherLevel == 1 && IsLevel1Corridors(nx, nz);
            return LevelBoundaryEdge(ref rng, mx, mz, level, otherLevel, halls, west);
        }
        return level switch
        {
            0 => Level0Edge(ref rng, mx, mz, nx, nz),
            1 => Level1Edge(ref rng, mx, mz, nx, nz),
            2 => Level2Edge(ref rng),
            3 => Level3Edge(ref rng, mx, mz),
            4 => Level4Edge(ref rng, mx, mz, nx, nz),
            5 => Level5Edge(ref rng, mx, mz, nx, nz, west),
            6 => Level6Edge(ref rng, mx, mz, nx, nz),
            7 => new Edge { Pattern = WallPattern.Concrete },
            8 => Level8Edge(mx, mz, west),
            _ => new Edge { Pattern = WallPattern.Rock }, // the suburbs and the fields run straight on
        };
    }

    /// <summary>A solid wall between two levels, pierced by a few doorways.</summary>
    private Edge LevelBoundaryEdge(ref Rng rng, int mx, int mz, int level, int otherLevel, bool halls, bool west)
    {
        // The suburbs give way to the fields with no wall at all
        if (IsOpenSky(level) && IsOpenSky(otherLevel)) return new Edge { Pattern = WallPattern.Rock };
        WallPattern pattern = level == 0 ? RegionAt(mx, mz).PrimaryPattern : WallPattern.Chevron;
        pattern = level switch
        {
            0 => pattern,
            1 => halls ? WallPattern.WhiteBlock : WallPattern.Concrete,
            2 => WallPattern.Tunnel,
            3 => Level3Material(mx, mz),
            4 => WallPattern.Drywall,
            5 => WallPattern.Hotel,
            6 => WallPattern.L6Wall,
            7 => WallPattern.Concrete,
            _ => WallPattern.Rock, // the caves; and the cliffs the open levels meet the rest at
        };
        // Where an open level meets an enclosed one, the wall is a rock cliff with cave mouths in it
        if (IsOpenSky(level) || IsOpenSky(otherLevel)) pattern = WallPattern.Rock;
        var edge = new Edge { Pattern = pattern, Base = BaseFor(pattern), Tall = true, ExitSigns = level == 1 };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;

        if (halls)
        {
            // Into Level 1's maintenance halls: doorways where its corridors meet the wall
            foreach (int start in HallCrossings) edge.Tiles[start] = edge.Tiles[start + 1] = EdgeTile.Doorway;
            return edge;
        }
        if (level == 8 || otherLevel == 8)
        {
            // The caves are solid rock but for the 9th Road, so the way in or out is where the road runs on
            // through the wall; elsewhere the rock is unbroken
            for (int i = 2; i < MacroSize - 1; i++)
            {
                int gx = west ? mx * MacroSize : mx * MacroSize + i, gz = west ? mz * MacroSize + i : mz * MacroSize;
                if (IsNinthRoad(gx, gz)) edge.Tiles[i] = EdgeTile.Doorway;
            }
            return edge;
        }
        int doors = rng.Range(2, 3);

        // Next to an office block or a hotel wing, the doorways open where its corridors meet the wall, not into
        // the back of a room
        int nx = west ? mx - 1 : mx, nz = west ? mz : mz - 1;
        bool officeGrid = level == 4 && IsOfficeBlock(mx, mz) || otherLevel == 4 && IsOfficeBlock(nx, nz);
        bool hotelGrid = level == 5 && HotelZoneAt(mx, mz) == HotelZone.Wing || otherLevel == 5 && HotelZoneAt(nx, nz) == HotelZone.Wing;
        if (officeGrid || hotelGrid)
        {
            bool Aligned(int i)
            {
                int gx = west ? mx * MacroSize : mx * MacroSize + i, gz = west ? mz * MacroSize + i : mz * MacroSize;
                return officeGrid && Hashing.Mod(west ? gz : gx, L4OfficeGrid) < 2 || hotelGrid && HotelCellAt(gx, gz) == HotelCell.Corridor;
            }
            var runs = new List<(int Start, int Length)>();
            for (int i = 2; i < MacroSize - 1; i++)
            {
                if (!Aligned(i)) continue;
                int first = i;
                while (i + 1 < MacroSize - 1 && Aligned(i + 1)) i++;
                runs.Add((first, Math.Min(i - first + 1, 3)));
            }
            if (runs.Count > 0)
            {
                for (int n = Math.Min(doors, runs.Count); n > 0; n--)
                {
                    int k = rng.Range(0, runs.Count - 1);
                    for (int j = 0; j < runs[k].Length; j++) edge.Tiles[runs[k].Start + j] = EdgeTile.Doorway;
                    runs.RemoveAt(k);
                }
                return edge;
            }
        }

        int width = pattern == WallPattern.Rock ? 3 : 2;
        int spacing = (MacroSize - 4) / doors;
        for (int n = 0; n < doors; n++)
        {
            int start = 2 + n * spacing + rng.Range(0, spacing - 1 - width);
            for (int k = 0; k < width; k++) edge.Tiles[start + k] = EdgeTile.Doorway;
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
        if (level == 6 && IsSnackrooms(mx, mz)) return 21f;
        if (level == 7 && y <= floorY) return 6f; // the cold sea
        return LevelTemperatures[Math.Min(level, LevelTemperatures.Length - 1)];
    }

    private static readonly float[] LevelTemperatures = { 22f, 28f, 38f, 35f, 15f, 20f, 16f, 12f, 12f, 14f, 18f, 17f };

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
            case 5: BuildLevel5(b, mx, mz, west, north); break;
            case 6: BuildLevel6(b, mx, mz, west, north); break;
            case 7: BuildLevel7(b, mx, mz); break;
            case 8: BuildLevel8(b, mx, mz); break;
            case 9: BuildLevel9(b, mx, mz); break;
            case 11: BuildLevel11(b, mx, mz); break;
            default: BuildLevel10(b, mx, mz); break;
        }

        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Level = (byte)b.Level;
        OrientDoorways(b);
        Edge east = GetEdge(mx + 1, mz, west: true), south = GetEdge(mx, mz + 1, west: false);
        // The Snackrooms are sealed on purpose, and their whole shop fronts are doorways
        if (!(b.Level == 6 && IsSnackrooms(mx, mz)))
        {
            if (b.Level == 6)
            {
                // The maze is carved from the west and north; it must meet the passages east and south too
                foreach (int i in Passages(east)) OpenMazeTile(ref b.At(MacroSize - 1, i));
                foreach (int i in Passages(south)) OpenMazeTile(ref b.At(i, MacroSize - 1));
            }
            ClearDoorways(b, east, south);
            SealPockets(b, east, south);
        }
        return b.Tiles;
    }

    private static void OpenMazeTile(ref Tile t)
    {
        if (t.Kind != TileKind.Wall) return;
        t.Kind = TileKind.Floor;
        t.Variant = 0;
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

    /// <summary>
    /// Keeps every doorway usable: single-block props and crates directly in front of or behind one are removed.
    /// Doorways in the edges are checked from both cells, since the tiles either side belong to different cells.
    /// </summary>
    private static void ClearDoorways(Builder b, Edge east, Edge south)
    {
        static bool Movable(in Tile t) => t.Kind == TileKind.Floor && t.Variant is not (Props.Car or Props.CarPart or Props.Bed
            or Props.HospitalBed or Props.WheelStop or Props.WindowGlow) && t.Stair == 0;
        void Clear(int x, int z)
        {
            if (x < 0 || z < 0 || x >= MacroSize || z >= MacroSize) return;
            ref Tile t = ref b.At(x, z);
            if (t.Kind == TileKind.Floor && t.Variant is Props.Car or Props.CarPart) { TowCar(x, z); return; }
            if (!Movable(t)) return;
            t.Variant = 0;
            t.Stack = 0;
        }
        // A car parked across a doorway is taken away whole, unless part of it stands in the next cell
        void TowCar(int x, int z)
        {
            var car = new List<(int X, int Z)> { (x, z) };
            for (int i = 0; i < car.Count; i++)
                foreach ((int dx, int dz) in Steps)
                {
                    (int X, int Z) next = (car[i].X + dx, car[i].Z + dz);
                    if (next.X < 0 || next.Z < 0 || next.X >= MacroSize || next.Z >= MacroSize) return;
                    Tile n = b.At(next.X, next.Z);
                    if (n.Kind == TileKind.Floor && n.Variant is Props.Car or Props.CarPart && !car.Contains(next)) car.Add(next);
                }
            if (car.Count > 8) return; // two cars bumper to bumper: leave them be
            foreach ((int cx, int cz) in car)
            {
                b.At(cx, cz).Variant = 0;
                b.At(cx, cz).Stack = 0;
            }
        }
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                if (b.At(lx, lz).Kind != TileKind.Doorway) continue;
                Clear(lx + 1, lz);
                Clear(lx - 1, lz);
                Clear(lx, lz + 1);
                Clear(lx, lz - 1);
            }
        // Doorways in the neighbours' edges, next to this cell's last row and column
        for (int i = 1; i < MacroSize; i++)
        {
            if (east.Tiles[i] == EdgeTile.Doorway) Clear(MacroSize - 1, i);
            if (south.Tiles[i] == EdgeTile.Doorway) Clear(i, MacroSize - 1);
        }
    }

    /// <summary>Whether a person can stand on and walk across a tile.</summary>
    /// <summary>Props on a floor tile that don't stop anyone walking on: low clutter, plants, wires, an open gate.</summary>
    internal static bool IsWalkThroughProp(byte variant) => variant is 0 or Props.WheelStop or Props.SpeedBump or Props.FloorCable
        or Props.Bedroll or Props.Crop or Props.TallGrass or Props.Reeds or Props.Tripwire or Props.FieldGate or Props.MachineParts;

    private static bool IsWalkable(in Tile t)
    {
        if (t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water) return true;
        if (t.Kind != TileKind.Floor) return false;
        if (t.Stack > 0 && t.Variant == 0 || t.SupplyBox) return false; // crates and boxes
        return IsWalkThroughProp(t.Variant);
    }

    /// <summary>
    /// Any pocket of floor that can't be walked to from the cell's edges (a room whose door fell on a wall, a
    /// corner fenced in by furniture) is marked sealed, so nobody is ever put down there.
    /// </summary>
    private static void SealPockets(Builder b, Edge east, Edge south)
    {
        var reached = new bool[MacroSize * MacroSize];
        var queue = new Queue<int>();
        for (int i = 0; i < MacroSize; i++)
        {
            // The west and north edges are this cell's own tiles; past the east and south ones, the neighbours' edges must be open
            foreach ((int x, int z, bool open) in new[] { (i, 0, true), (0, i, true),
                     (i, MacroSize - 1, south.Tiles[i] != EdgeTile.Wall), (MacroSize - 1, i, east.Tiles[i] != EdgeTile.Wall) })
            {
                int index = TileIndex(x, z);
                if (!open || reached[index] || !IsWalkable(b.Tiles[index])) continue;
                reached[index] = true;
                queue.Enqueue(index);
            }
        }
        while (queue.Count > 0)
        {
            int index = queue.Dequeue();
            int x = index % MacroSize, z = index / MacroSize;
            foreach ((int dx, int dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= MacroSize || nz >= MacroSize) continue;
                int next = TileIndex(nx, nz);
                if (reached[next] || !IsWalkable(b.Tiles[next])) continue;
                reached[next] = true;
                queue.Enqueue(next);
            }
        }
        for (int i = 0; i < b.Tiles.Length; i++)
            if (!reached[i] && b.Tiles[i].Kind == TileKind.Floor) b.Tiles[i].Sealed = true;
    }

    /// <summary>
    /// Doorways with a sign over them need to know which way their wall runs: Pier north (or south) for a wall
    /// running west-east, east (or west) for one running north-south. Fire doors set their own.
    /// </summary>
    private static void OrientDoorways(Builder b)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Doorway || !t.ExitSign || t.Variant == Props.FireDoor) continue;
                bool westEast;
                if (lz == 0 && lx > 0) westEast = true;
                else if (lx == 0 && lz > 0) westEast = false;
                else
                {
                    bool Solid(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && b.At(x, z).IsWallLike;
                    westEast = Solid(lx - 1, lz) || Solid(lx + 1, lz);
                }
                t.Pier = westEast ? ArchPier.North : ArchPier.East;
            }
        }
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

    private static readonly (int X, int Z)[] Ring = { (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1) };

    /// <summary>
    /// Whether blocking this tile leaves everything around it still connected: the open tiles in the ring of
    /// eight around it form one unbroken run.
    /// </summary>
    private static bool SafeToBlock(Func<int, int, bool> open, int x, int z)
    {
        int runs = 0, count = 0;
        for (int i = 0; i < 8; i++)
        {
            bool here = open(x + Ring[i].X, z + Ring[i].Z), prev = open(x + Ring[(i + 7) % 8].X, z + Ring[(i + 7) % 8].Z);
            if (here) count++;
            if (here && !prev) runs++;
        }
        return count > 0 && (runs <= 1 || count == 8);
    }

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
        WallPattern.RedRoom => BaseStyle.Baseboard,
        _ => BaseStyle.Plain,
    };
}
