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
/// is a full-height wall, unbroken except at the few gates (see WorldLayout.Gates.cs). Within a level the edges are
/// laid by the level itself: some follow a plan larger than a cell (Level 0's districts, Level 2's tunnels, Level 6's
/// trunks), the rest leave passages of their own. Each level lays out the interior of its cells in its own partial
/// class file.
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
    /// goes on forever. Level 0 alone averages some 770 blocks from spawn to its edge, and reaching Level 10 is a
    /// journey of several kilometres. No ring is a circle: each is stretched by its own <see cref="RingShape"/>, so in
    /// one direction a level may end after a few hundred blocks and in another go on for several times that.
    /// (Smaller than they once were: with the walls between levels unbroken but for a few gates, it is finding the way
    /// through rather than the distance that takes time.)
    /// </summary>
    private static readonly double[] RingWidths = { 24, 18, 14, 16, 20, 20, 16, 22, 18, 24 };

    /// <summary>How strongly the rings are stretched: each ring's width varies by about e^±Stretch with direction.</summary>
    private const double Stretch = 1.45;

    /// <summary>Waves round the circle that shape each ring: the first few stretch it, the rest make it lumpy.</summary>
    private const int ShapeHarmonics = 7;

    /// <summary>
    /// Number of levels: Level 0 to the outermost ring, Level 11 (the city beyond it), and the other places no ring
    /// reaches, Level 37 (kept as <see cref="Poolrooms"/>), Level 94 (<see cref="Motion"/>), the five kept as 14-18,
    /// Level 3999 (19) and Level 188 (20).
    /// </summary>
    public static int LevelCount => RingWidths.Length + 11;

    /// <summary>Level 37, "Sublimity", the Poolrooms: kept as level 12, shown as 37.</summary>
    public const int Poolrooms = 12;

    /// <summary>Level 94, "Motion": kept as level 13, shown as 94.</summary>
    public const int Motion = 13;

    /// <summary>Level !, "Run For Your Life!": kept as level 14, shown as "!".</summary>
    public const int RunLevel = 14;

    /// <summary>Level Fun =): kept as level 15, shown as "Fun".</summary>
    public const int FunLevel = 15;

    /// <summary>The End: kept as level 16, shown as "End".</summary>
    public const int TheEnd = 16;

    /// <summary>The Hub: kept as level 17, shown as "Hub".</summary>
    public const int Hub = 17;

    /// <summary>Level 974: kept as level 18, shown as 974.</summary>
    public const int Level974 = 18;

    /// <summary>Level 3999, "The Neon Paradise": kept as level 19, shown as 3999.</summary>
    public const int Level3999 = 19;

    /// <summary>Level 188, "The Courtyard of Windows": kept as level 20, shown as 188.</summary>
    public const int Level188 = 20;

    /// <summary>The number (or name) a level goes by: its own for the rings and the city, 37 and 94 and the rest for those kept past them.</summary>
    public static string DisplayNumber(int level) => level switch
    {
        Poolrooms => "37",
        Motion => "94",
        RunLevel => "!",
        FunLevel => "Fun",
        TheEnd => "End",
        Hub => "Hub",
        Level974 => "974",
        Level3999 => "3999",
        Level188 => "188",
        _ => level.ToString(),
    };

    /// <summary>The level kept for a number a player would use ("37" is the Poolrooms), or -1 if there is none.</summary>
    public static int FromDisplayNumber(int number) => number switch
    {
        37 => Poolrooms,
        94 => Motion,
        974 => Level974,
        3999 => Level3999,
        188 => Level188,
        _ => number >= 0 && number <= 11 ? number : -1,
    };

    /// <summary>
    /// The level kept for what a player would type: a number ("37"), or a name ("!", "fun", "end", "hub"), with or
    /// without "level" in front; -1 if there is none.
    /// </summary>
    public static int FromDisplayName(string name)
    {
        string s = (name ?? "").Trim().ToLowerInvariant();
        if (s.StartsWith("level")) s = s.Substring(5).Trim();
        if (s.StartsWith("the ")) s = s.Substring(4).Trim();
        return s switch
        {
            "!" => RunLevel,
            "fun" or "fun=)" or "fun =)" => FunLevel,
            "end" => TheEnd,
            "hub" => Hub,
            _ => int.TryParse(s, out int number) ? FromDisplayNumber(number) : -1,
        };
    }

    /// <summary>
    /// The places no ring reaches, which you can only noclip into: the city, the Poolrooms, Motion, and the rest kept as
    /// 14-20. Their rims have no gates.
    /// </summary>
    public static bool IsNoclipRegion(int level) => level >= 11;

    /// <summary>
    /// The layout version new worlds are made with. A world keeps the version it was made with for good, since its
    /// chunks are generated as they are first reached and must go on matching the ones already made. Fixes that would
    /// move what an existing world holds go in behind a new version (test <see cref="Version"/>), never in place:
    /// <list type="bullet">
    /// <item>1: every world made before the layout was versioned (up to 0.3.5).</item>
    /// <item>2: Level 37's deep halls are rolled apart from their width (in 1 every deep hall is also a wide one), and
    /// Level 5's boiler-bay fittings by the row as well as the column (in 1 they repeat from cell to cell along z).</item>
    /// <item>3: Level 0 has more food: stashes of boxes in about one cell in six rather than nine (blackouts, one in
    /// three or four rather than four or five), and fewer of them picked over (55% rather than 65%; blackouts, 35%
    /// rather than 40%). Players starved looking for the way out.</item>
    /// <item>4: Level 0 has one wallpaper, the chevron paper with its dark baseboard, as in Kane Parsons' footage and
    /// the film (in 1-3 some areas and odd walls had the dotted paper with a brown rail). The pale walls of the arched
    /// areas have the same baseboard and outlets, each face of a wall where the two meet shows the paper of the side
    /// it faces, and the openings into an arched area are arches. A doorway wider than one block has one sign over
    /// its middle (an EXIT or STAFF ONLY sign, a store's sign, a Level 3999 unit's neon), split in halves over the
    /// middle two blocks of an even width (in 1-3 each block of a signed doorway had a sign of its own, a store's sign
    /// hung over one of its two doors and a unit's neon half a block off; see WorldGenerator.Signs.cs). Level 5's
    /// STAFF ONLY sign is a plate on the frieze. Level 1's car park is laid out district by district, its grid counted
    /// from each district's corner, so the fire walls stand on column lines and never cut through a row of stalls or
    /// along an aisle; its stair cores stand in the corners of each district, by the fire walls, with a crossing
    /// painted from their doors; it has no speed bumps across its aisles; its stairs to nowhere climb into a wall at
    /// the back of a stall; shear walls never stand across a cross aisle; and now and then a bay of stalls is a store.
    /// Its maintenance halls have stockrooms of racks and aisles, and storerooms with shelving along the walls and
    /// a clear way in (in 1-3 the grid ran on across the whole level and its things stood wherever they fell; see
    /// WorldLayout.Level1.cs). Every stairwell of Levels 1 and 4 (Level 1's stair cores and its halls' stairwell rooms,
    /// and Level 4's, which take in the corridor beside them) has a flight up through the ceiling and a flight down
    /// through the floor, each into a dark shaft and on to another stairwell's flight the other way, Level 1's from
    /// floor to painted floor, P5 to B3, and none of its halls' rooms has a corner fenced off by its furniture (in 1-3,
    /// one flight that climbed into the ceiling, and a few such corners; see WorldLayout.StampStairwellV4).</item>
    /// <item>5: arrivals in Levels 2, 3, 9, 11, 37 and 94 would rather be under a working light (2, 3), in a slit's light
    /// and never in the dark corners (37), or out in the open, clear of house walls, trees and parked cars (9, 11, 94);
    /// where none is near, the arrival is where it was (see WorldLayout.Reality.cs, ArrivalPreference). Level 4's cables
    /// hang out of about one missing ceiling tile in six (0.8% of ceiling tiles; in 1-4, 2.5%). Level 37's arrivals would
    /// rather be in a rotunda, pillar hall or natatorium with room to look round than in a corridor facing a wall. The
    /// End has partition walls (the store's painted wall, with openings) along about one department border in three,
    /// on the side of a stacks or open-floor department, and the central hall's EXIT doors stand at the back of little
    /// vestibules (in 1-4, in lone walls; see WorldLayout.LevelEnd.cs, PlanEndPartitions). Most of Level 10's crop fields
    /// have a second thing in them besides the scarecrow: a lone shed, a water trough and pump, or a fallen gate
    /// (FieldFocalOf). Some of Level 11's low brick roofs carry a billboard facing the street, and some street corners an
    /// advertising pillar (RoofDressing, CornerFurniture). Level 4 turns to hotel red toward Level 5 by the distance to
    /// it, solid within about five blocks and frayed by noise out to fourteen (in 1-4, in noisy patches all over a cell
    /// beside the hotel; WarmTowardsHotel), and its wanderers' refuges are camps (PitchL4Camp; the wanderer stands on
    /// the tile it marks). One Level 5 lobby cell in each four by four region of cells is a front hall: a back wall, the
    /// front desk on the axis with a key rack, two grand staircases up through the ceiling to Level 4, runners
    /// (BuildFrontHall). One locked hotel door in three hundred reads 666, and the Beverly Room's doors have blank plates
    /// (in 1-4, 201-208). Some of Level 2's mains carry the B.N.T.G.'s tramway down their middle lane, now and then
    /// with a dead locomotive and wagon on it (Tile.Zone, L2Rails, PlaceDeadTram), and about one length of main in eight
    /// between two crossings of mains is stepped 4-8 blocks aside (L2Jog); a Level 2 warren has candle stubs under its
    /// crosses and by its cache. Now and then something purpified lies half in a Level 3 wall (Decor.Purpified).
    /// Level 7's islands rise in steps from the water (Tile.Height 0-2), pillars of their rock stand into the ceiling
    /// from the larger islands and as sea stacks in the sea, and one camp in two has a shelter of furniture and tar
    /// (ShapeLevel7, Tile.Detail L7Pillar, L7TarUnder); its ceiling glows in patches (WorldGenerator.CeilingGlows). Level
    /// 8's road is an arch and its settlements domes (Tile.Height: RoadRoof, CampDome; a clearing is round, in 1-4 a
    /// square 17 across), its lamps face the road (Tile.Pier), glowcaps grow along its walls and in its caves
    /// (Props.GlowcapRed/Mixed, WorldGenerator.Glowcaps), and its ore lies in veins and pockets (CaveColumn.OreGrade).
    /// One Level 6.1 store in four is a vending machine room (SnackUnit.VendingRoom, Props.VendingPile). About a third
    /// of Level 9's houses have two storeys with stairs and bedrooms upstairs, more have porches, there is a lamp by
    /// every front door, windows come in three rhythms (PlanHouse, Tile.Height), and every junction has street-name
    /// signs, one in six a DOWNTOWN sign. Level Fun's elevator lobbies are dressed for the party (string lights,
    /// confetti, balloons and streamers, a poster, the ship's directory, a palm; DressFunLobbyTile), and one pair of
    /// doors in each says OUT OF ORDER =). Level !'s start rooms have the crash rail, notices and a sanitiser dispenser
    /// (in 1-4 bare walls). Level 3999's lobbies and food courts have pillars every ten blocks rather than five and
    /// neon tubes under the ceiling every six, its lobbies a row of six machines on the back wall and a storey line of
    /// black marble at rel 6-7 (drawn by the generator when Version >= 5). In Level 974 you wake on the bedroom rug
    /// before the bed (in 1-4, in the mouth of the bed's alcove), and the hall has a third downlight. Level 188's EXIT
    /// sign hangs over the courtyard door on the courtyard side (drawn by the generator when Version >= 5).</item>
    /// <item>6: camps' tents and bedrolls are as big as the real things, a camp tent two by two and a sleeping bag two
    /// long (Level 1's hall camps, Level 4's refuges, Level 6's dead ends, Level 7's islands and shelters, Level 8's
    /// settlements, lairs), left out where there is no room; one-tile velvet sofas become two-wide sofas where there is
    /// room (Levels 5, 9, 11, 94); a multi-tile prop that lost a part is removed whole (WorldLayout.Parts.cs). Level !'s
    /// hallway is packed with set pieces (barricades, supply cabinets, collapsed ceiling, lines of gurneys and
    /// wheelchairs, needles, feints), every straight kept passable at a sprint (PlanRunGauntlet, RunSprintable).</item>
    /// <item>7: the world's Backrooms scarcity reaches the fields: where it is below Normal (<see cref="FoodScale"/>
    /// under 1), Level 9's gardens and Level 10's crops, vegetable patches and berry bushes are thinned to that share
    /// (ThinFood). At Normal or Plentiful a world is laid out as in 6.</item>
    /// </list>
    /// </summary>
    public const int CurrentVersion = 7;

    /// <summary>The layout version this world was made with (see <see cref="CurrentVersion"/>).</summary>
    public readonly int Version;

    /// <summary>
    /// The world's food multiplier, from its Backrooms scarcity setting (1 at Normal; the game side passes the one
    /// recorded when the world was made, BackroomsWorld.WorldgenFoodScale). From layout version 7, below 1 it thins the
    /// crops of Levels 9 and 10 (ThinFood).
    /// </summary>
    public readonly double FoodScale;

    private readonly ulong seed;
    private readonly int spawnMacroX;
    private readonly int spawnMacroZ;

    // Each ring's shape: the amplitude and phase of its waves round the circle
    private readonly double[,] shapeAmplitude = new double[RingWidths.Length, ShapeHarmonics + 1];
    private readonly double[,] shapePhase = new double[RingWidths.Length, ShapeHarmonics + 1];

    // The level of the cells asked about lately (it is asked about constantly): bounded, so a world explored far and
    // wide does not keep one entry for every cell it ever looked at
    private readonly LatticeMemo<byte> levelCache;

    public WorldLayout(long seed, int spawnMacroX, int spawnMacroZ, int version = CurrentVersion, double foodScale = 1)
    {
        Version = Math.Clamp(version, 1, CurrentVersion);
        FoodScale = foodScale > 0 ? foodScale : 1;
        this.seed = (ulong)seed;
        this.spawnMacroX = spawnMacroX;
        this.spawnMacroZ = spawnMacroZ;
        levelCache = new LatticeMemo<byte>(1 << 16, (mx, mz) => (byte)ComputeLevel(mx, mz));
        snackCache = new LatticeMemo<bool>(1 << 12, ComputeSnackrooms);
        gateCache = new LatticeMemo<HashSet<long>>(1 << 10, PlanGates);
        featureCells = new PlanCache<Tile[]>(48, BuildMacro);

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

        // The Level 0 district the spawn point lies in (asked about for every district planned or zoned)
        int sgx = spawnMacroX * MacroSize + MacroSize / 2, sgz = spawnMacroZ * MacroSize + MacroSize / 2;
        l0SpawnRow = L0RowOf(sgz);
        l0SpawnCol = L0ColOf(sgx, l0SpawnRow);
    }

    public static int MacroOf(int blockCoord) => Hashing.FloorDiv(blockCoord, MacroSize);

    public static int TileIndex(int lx, int lz) => lz * MacroSize + lx;

    private bool IsSpawnMacro(int mx, int mz) => mx == spawnMacroX && mz == spawnMacroZ;

    // ================= Levels =================

    /// <summary>Which level a macro cell belongs to.</summary>
    public int LevelAt(int mx, int mz) => levelCache.Get(mx, mz);

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
        // Far out in the fields lie the places no ring reaches: the city to the east, the Poolrooms to the west, and
        // Motion to the north
        if (InCity(mx, mz)) return 11;
        if (InPoolrooms(mx, mz)) return Poolrooms;
        if (InMotion(mx, mz)) return Motion;
        // And further out, the five kept as 14-18, each in its own direction (see RegionReach): Level ! to the south,
        // Fun to the north-east, the End to the north-west, the Hub to the south-east and Level 974 to the south-west
        if (InRun(mx, mz)) return RunLevel;
        if (InFun(mx, mz)) return FunLevel;
        if (InEnd(mx, mz)) return TheEnd;
        if (InHub(mx, mz)) return Hub;
        if (InL974(mx, mz)) return Level974;
        // Level 3999 far out beyond the Hub to the south-east, Level 188 to the north-north-east (see their files)
        if (InL3999(mx, mz)) return Level3999;
        if (InL188(mx, mz)) return Level188;
        return RingWidths.Length;
    }

    /// <summary>
    /// How far out, in macro cells, the regions past the rings lie: the city, the Poolrooms and Motion this far from
    /// spawn; the five kept as 14-18 this far (Level !) or a quarter further (the rest). Scales with the world, so they
    /// never overlap one another, in a small world or a full-size one.
    /// </summary>
    private int RegionReach => Math.Max(800, spawnMacroX / 4);

    /// <summary>The offset along each axis of a region lying diagonally out from spawn, a quarter further than the city.</summary>
    private int DiagonalReach => (int)Math.Round(RegionReach * 1.25 / Math.Sqrt(2));

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
    /// <see cref="InnerEdge"/> and <see cref="OuterEdge"/> of a ring level (0 to the outermost ring) in one pass, for
    /// the per-block callers: the same sums in the same order, so the same values to the last bit, at half the cost.
    /// </summary>
    private (double Inner, double Outer) RingEdges(int level, double angle)
    {
        double inner = 0, edge = 0;
        for (int ring = 0; ring <= level; ring++)
        {
            if (ring == level) inner = edge;
            edge += RingWidths[ring] * RingShape(ring, angle);
        }
        return (inner, edge);
    }

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
        var (inner, outer) = RingEdges(level, angle);
        return Math.Clamp((RingDistance(mx, mz) - inner) / (outer - inner), 0, 1);
    }

    /// <summary>Levels under the open sky rather than a ceiling: the Suburbs, the fields, the city and Motion.</summary>
    public static bool IsOpenSky(int level) => level switch
    {
        9 or 10 or 11 or Motion => true,
        // The five kept as 14-18 (each level's own line)
        RunLevel => false,
        FunLevel => false,
        TheEnd => false,
        Hub => false,
        Level974 => false,
        Level3999 => false,
        Level188 => false,
        _ => false,
    };

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
        /// <summary>Level 0: the line follows the hallway plan, and the cell copies the plan's tiles onto it as they are.</summary>
        public bool Planned;
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
            0 => Level0Edge(ref rng, mx, mz, nx, nz, west),
            1 => Level1Edge(ref rng, mx, mz, nx, nz),
            2 => Level2Edge(mx, mz, west),
            3 => Level3Edge(ref rng, mx, mz, nx, nz),
            4 => Level4Edge(ref rng, mx, mz, nx, nz),
            5 => Level5Edge(ref rng, mx, mz, nx, nz, west),
            6 => Level6Edge(mx, mz, nx, nz, west),
            7 => new Edge { Pattern = WallPattern.Concrete },
            8 => Level8Edge(mx, mz, west),
            Poolrooms => new Edge { Pattern = WallPattern.PoolTile }, // the plans are laid over the edges
            RunLevel => RunEdge(mx, mz, west),
            FunLevel => FunEdge(mx, mz, west),
            TheEnd => EndEdge(mx, mz, west),
            Hub => HubEdge(mx, mz, west),
            Level974 => L974Edge(mx, mz, west),
            Level3999 => L3999Edge(mx, mz, west),
            Level188 => L188Edge(mx, mz, west),
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
            4 => WallPattern.OfficeWindow, // where the office floor ends: windows onto the rain
            5 => WallPattern.Hotel,
            6 => WallPattern.L6Wall,
            7 => WallPattern.Concrete,
            Poolrooms => WallPattern.PoolTile,
            RunLevel => WallPattern.RunWall,
            FunLevel => WallPattern.FunWall,
            TheEnd => WallPattern.EndWall,
            Hub => WallPattern.HubWall,
            Level974 => WallPattern.L974Wall,
            Level3999 => WallPattern.L3999Wall,
            Level188 => WallPattern.L188Wall,
            _ => WallPattern.Rock, // the caves; and the cliffs the open levels meet the rest at
        };
        // Where an open level meets an enclosed one, the wall is a rock cliff with cave mouths in it
        if (IsOpenSky(level) || IsOpenSky(otherLevel)) pattern = WallPattern.Rock;
        var edge = new Edge { Pattern = pattern, Base = BaseFor(pattern), Tall = true, ExitSigns = level == 1 };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;

        if (halls && IsGate(mx, mz, west))
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
        // Most of the wall is unbroken: only a gate has a way through
        if (!IsGate(mx, mz, west)) return edge;
        int doors = rng.Range(2, 3);

        // Next to an office block or a hotel wing, the doorways open where its corridors meet the wall, not into
        // the back of a room
        int nx = west ? mx - 1 : mx, nz = west ? mz : mz - 1;
        bool officeGrid = level == 4 && IsOfficeBlock(mx, mz) || otherLevel == 4 && IsOfficeBlock(nx, nz);
        bool hotelGrid = level == 5 && HotelZoneAt(mx, mz) == HotelZone.Wing || otherLevel == 5 && HotelZoneAt(nx, nz) == HotelZone.Wing;
        if (officeGrid || hotelGrid)
        {
            // Where an office block meets a hotel wing, a doorway must line up with corridors on both sides, or it
            // would open into the back of a locked room; failing that, with either
            bool OfficeAligned(int gx, int gz) => Hashing.Mod(west ? gz : gx, L4OfficeGrid) < 2;
            bool HotelAligned(int gx, int gz) => HotelCellAt(gx, gz) == HotelCell.Corridor;
            bool Aligned(int i, bool both)
            {
                int gx = west ? mx * MacroSize : mx * MacroSize + i, gz = west ? mz * MacroSize + i : mz * MacroSize;
                bool office = officeGrid && OfficeAligned(gx, gz), hotel = hotelGrid && HotelAligned(gx, gz);
                return both && officeGrid && hotelGrid ? office && hotel : office || hotel;
            }
            var runs = new List<(int Start, int Length)>();
            for (int pass = 0; pass < 2 && runs.Count == 0; pass++)
                for (int i = 2; i < MacroSize - 1; i++)
                {
                    if (!Aligned(i, pass == 0)) continue;
                    int first = i;
                    while (i + 1 < MacroSize - 1 && Aligned(i + 1, pass == 0)) i++;
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
    /// Level 5's boiler halls are scorching. Level 0's blackout zones are cold and damp, cool enough that food
    /// keeps there; the dark of Level 6 and the caves of Level 8 are cold enough to want clothes.
    /// </summary>
    public float TemperatureAt(int x, int y, int z, int floorY)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        int level = LevelAt(mx, mz);
        if (level == 3 && y < floorY) return -4f;
        if (level == 0 && Level0ZoneAt(x, z) == ZoneKind.Blackout) return 10f;
        if (level == 5 && HotelZoneAt(mx, mz) == HotelZone.Boiler) return 42f;
        if (level == 6 && IsSnackrooms(mx, mz)) return 21f;
        if (level == 7 && y <= floorY) return 6f; // the cold sea
        if (level == Poolrooms) return y <= floorY - WorldGeometry.PoolDrop ? 31f : IsReservoir(mx, mz) ? 24f : 29f; // lukewarm, everywhere
        switch (level)
        {
            // The five kept as 14-18 work theirs out in their own files
            case RunLevel: return RunTemperature(x, y, z, floorY);
            case FunLevel: return FunTemperature(x, y, z, floorY);
            case TheEnd: return EndTemperature(x, y, z, floorY);
            case Hub: return HubTemperature(x, y, z, floorY);
            case Level974: return L974Temperature(x, y, z, floorY);
            case Level3999: return L3999Temperature(x, y, z, floorY);
            case Level188: return L188Temperature(x, y, z, floorY);
        }
        return LevelTemperatures[Math.Min(level, LevelTemperatures.Length - 1)];
    }

    /// <summary>Each level's usual temperature, by the number it is kept as (14-20: Level !, Fun, the End, the Hub, 974, 3999, 188).</summary>
    private static readonly float[] LevelTemperatures = { 22f, 28f, 38f, 35f, 15f, 20f, 8f, 12f, 9f, 14f, 18f, 17f, 29f, 21f, 20f, 22f, 19f, 20f, 21f, 24f, 21f };

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
            case 0: BuildLevel0(b, mx, mz, west, north); break;
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
            case Poolrooms: BuildLevel37(b, mx, mz); break;
            case Motion: BuildLevel94(b, mx, mz); break;
            case RunLevel: BuildLevelRun(b, mx, mz); break;
            case FunLevel: BuildLevelFun(b, mx, mz); break;
            case TheEnd: BuildLevelEnd(b, mx, mz); break;
            case Hub: BuildLevelHub(b, mx, mz); break;
            case Level974: BuildLevel974(b, mx, mz); break;
            case Level3999: BuildLevel3999(b, mx, mz); break;
            case Level188: BuildLevel188(b, mx, mz); break;
            default: BuildLevel10(b, mx, mz); break;
        }

        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Level = (byte)b.Level;
        OrientDoorways(b);
        Edge east = GetEdge(mx + 1, mz, west: true), south = GetEdge(mx, mz + 1, west: false);
        // The Snackrooms are sealed on purpose, and their whole shop fronts are doorways
        if (!(b.Level == 6 && IsSnackrooms(mx, mz)))
        {
            ClearDoorways(b, east, south);
            SealPockets(b, east, south);
            OpenGates(b, mx, mz, west, north, east, south);
        }
        // (After the doorways are cleared and the pockets sealed, so the camp stays as it is laid out)
        if (b.Level == 4 && Version >= 5) PitchL4Camp(b, mx, mz);
        MarkPickedOver(b, mx, mz);
        PlaceDen(b, mx, mz);
        MarkWayToGates(b, mx, mz);
        // (Last: the tents and sleeping bags as big as the real things, and nothing left of one in part)
        if (Version >= 6) LayOutParts(b, mx, mz);
        // (In version 7 a scarce world's fields and gardens bear less)
        if (Version >= 7 && FoodScale < 1 && b.Level is 9 or 10) ThinFood(b, mx, mz);
        return b.Tiles;
    }

    private const ulong SaltThinFood = 0xF00D;

    /// <summary>
    /// A scarce world's crops, vegetables and berry bushes, thinned to <see cref="FoodScale"/> of them: each plant kept
    /// or left out by a hash of where it stands, so a field is gappy rather than cut short.
    /// </summary>
    private void ThinFood(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Variant is not (Props.Crop or Props.Vegetable or Props.BerryBush)) continue;
                if (Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltThinFood)) < FoodScale) continue;
                t.Variant = 0;
                t.Stack = 0;
            }
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

    /// <summary>Props on a floor tile that don't stop anyone walking on: low clutter, plants, wires, an open gate.</summary>
    internal static bool IsWalkThroughProp(ushort variant) => variant is 0 or Props.WheelStop or Props.SpeedBump or Props.FloorCable
        or Props.Bedroll or Props.SleepingBag or Props.Crop or Props.TallGrass or Props.Reeds or Props.Tripwire or Props.FieldGate or Props.MachineParts
        // The five kept as 14-18 say which of their own props are walked through
        || variant >= Props.RunFirst && (RunWalkThrough(variant) || FunWalkThrough(variant) || EndWalkThrough(variant)
            || HubWalkThrough(variant) || L974WalkThrough(variant) || L3999WalkThrough(variant) || L188WalkThrough(variant));

    /// <summary>Whether a person can stand on and walk across a tile.</summary>
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
        void Seed(int x, int z, bool open)
        {
            int index = TileIndex(x, z);
            if (!open || reached[index] || !IsWalkable(b.Tiles[index])) return;
            reached[index] = true;
            queue.Enqueue(index);
        }
        for (int i = 0; i < MacroSize; i++)
        {
            // The west and north edges are this cell's own tiles; past the east and south ones, the neighbours' edges must be open
            Seed(i, 0, true);
            Seed(0, i, true);
            Seed(i, MacroSize - 1, south.Tiles[i] != EdgeTile.Wall);
            Seed(MacroSize - 1, i, east.Tiles[i] != EdgeTile.Wall);
        }
        while (queue.Count > 0)
        {
            int index = queue.Dequeue();
            int x = index % MacroSize, z = index / MacroSize;
            foreach ((int dx, int dz) in Steps)
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

    /// <summary>A supply box a couple of steps from the spawn point (one more each call), so the first minutes are survivable.</summary>
    private static void PlaceSpawnBox(Builder b)
    {
        (int sx, int sz) = FindSpawnTile(b.Tiles);
        foreach ((int dx, int dz) in new[] { (2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2), (1, 0), (0, 1) })
        {
            int x = sx + dx, z = sz + dz;
            if (!InInterior(x, z)) continue;
            ref Tile tile = ref b.At(x, z);
            if (tile.Kind != TileKind.Floor || tile.SupplyBox) continue;
            tile.SupplyBox = true;
            return;
        }
    }

    // ================= Shared by the far places (ids 14-20) =================

    /// <summary>Whether a cell lies in a round region past the rings, a little lumpy at its rim, like the Poolrooms.</summary>
    private bool InRoundRegion(double mx, double mz, int centreX, int centreZ, int radius, ulong salt)
    {
        double dx = mx - centreX, dz = mz - centreZ;
        double r = Math.Sqrt(dx * dx + dz * dz);
        if (r > radius * 1.2) return false;
        return r * (1 + 0.08 * Fbm(mx / 40.0, mz / 40.0, salt)) < radius;
    }

    /// <summary>A cell near the middle of a round region, picked by hash, to look for somewhere to arrive.</summary>
    private static (int Mx, int Mz) RoundArrivalCell(ulong h, int centreX, int centreZ, int radius)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, r = Math.Sqrt(Hashing.Unit(Hashing.Mix(h))) * radius * 0.4;
        return (centreX + (int)Math.Round(Math.Cos(angle) * r), centreZ + (int)Math.Round(Math.Sin(angle) * r));
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
