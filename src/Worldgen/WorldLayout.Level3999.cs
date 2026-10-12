using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 3999, "The Neon Paradise" (kept as level 19, <see cref="Level3999"/>, shown as "3999"): an endless arcade the
/// size of a mall, safe at heart, lit only by neon. It lies far out beyond the Hub to the south-east, a round region only
/// thresholds reach. The design is docs/design/new-levels/3999-plan.md as the user directed on 2026-10-09: an ordinary level to
/// visit, with its own resources (tickets from the machines, prize counters, food stalls, vending machines), a safe heart
/// and a dangerous fringe (Level 3999.1, the Neon Blackout), and ordinary thresholds.
///
/// The level is planned in blocks of <see cref="L3999Block"/> (128) blocks a side, each from its own id and cached
/// (<see cref="PlanCache{T}"/>). Along every block line runs a <b>concourse</b> twelve wide (offsets -6 to 5 about the
/// line), eighteen high, with a mezzanine gallery three wide down each side (its slab at rel 7) and two moving walkways
/// down the middle running opposite ways; where two concourses cross is a <b>junction</b> under a hanging "3999" sign,
/// with escalators up to the galleries just off it. Inside each block a cross of four-wide <b>service corridors</b> cuts
/// four quadrants of 56 by 56, each a <b>unit</b> behind a glass shopfront: a game area (rows of cabinets, a prize
/// counter, now and then the mini arcade with its elevator), a food court (stalls, tables, a gallery ring), a lobby (a
/// reception desk and, opposite, a revolving door), bowling lanes, or a shuttered unit (sealed stores, in from the
/// service corridor). Two quadrants may merge into a game hall or (past 30% of the radius) the violet-pooled Neon
/// Natatorium. Past 65% of the radius, one block in fourteen is the Neon Blackout: dead neon, rotten carpet, dark
/// machines, abandoned prize cases, and things in the dark; for 48 blocks round one the neon fails.
///
/// Heights (rel above the level's floor, <see cref="WorldGeometry.L3999Drop"/> below the others'): a floor tile's ceiling
/// is at <see cref="Tile.Height"/> (7 a hall, 18 an atrium, 4 a service corridor); walls run to 18.
///
/// Tile fields on the level's tiles: Zone the kind of place (<see cref="L3999Zone"/>); Detail bits 0-2 the neon colour
/// (<see cref="L3999Colours"/>), bit 3 the Neon Blackout, bits 4-5 how far the neon has failed nearby (1-3), bit 6 this
/// tile's lights are dead; Roof bit 0 a gallery slab at rel 7, bit 3 a balustrade on it (facing in bits 1-2), bit 4 a
/// neon tube under the slab (bit 5: running north-south), bit 6 a neon tube up the wall beside this tile, bit 7 a neon
/// strip along the foot of that wall (both facing <see cref="Tile.Pier"/>); Pipe what stands on a gallery
/// (<see cref="Pipes.L3999UpperCabinet"/>); Depth the water's depth, or (under a neon sign) the sign's words; Stack and
/// Pier the prop's kind and facing; Stair an escalator's step.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Whether Level 3999's entrances in other levels are laid out (always, but for the harness's 3999hash check).</summary>
    internal static bool L3999Entrances = true;

    /// <summary>Hash salts 0x1900-0x19BF are this level's (0x19C0-0x19FF its thresholds').</summary>
    private const ulong SaltL3999Shape = 0x1901, SaltL3999Plan = 0x1902, SaltL3999Unit = 0x1903, SaltL3999Merge = 0x1904,
        SaltL3999Blackout = 0x1905, SaltL3999Colour = 0x1906, SaltL3999Decay = 0x1907, SaltL3999Wanderer = 0x1908, SaltL3999Find = 0x1909;

    /// <summary>Salts of the level's entrances in other levels, each its own so nothing else there moves.</summary>
    private const ulong SaltL3999Arcade = 0x1910, SaltL3999Glitch = 0x1911, SaltL3999Magenta = 0x1912;

    /// <summary>The size of a plan block, and the spans of a block's quadrants (walls included).</summary>
    public const int L3999Block = 128;
    private const int L3999Lo0 = 6, L3999Lo1 = 61, L3999Hi0 = 66, L3999Hi1 = 121;

    /// <summary>Ceiling heights: a hall, an atrium, a service corridor; the galleries' slab; a doorway's opening.</summary>
    public const int L3999HallHeight = 7, L3999AtriumHeight = 18, L3999CorridorHeight = 4, L3999SlabRel = 7, L3999DoorHeight = 4;

    /// <summary>What part of the level a tile is in (<see cref="Tile.Zone"/>).</summary>
    public enum L3999Zone : byte { Concourse, Junction, Service, Game, GameHall, FoodCourt, Lobby, Lanes, Shuttered, MiniArcade, Natatorium, Rim }

    /// <summary>The kinds of unit.</summary>
    public enum L3999Kind : byte { Game, FoodCourt, Lobby, Lanes, Shuttered, GameHall, Natatorium }

    /// <summary>One unit of a plan block, its rectangle (walls included) in block-local coordinates.</summary>
    public readonly record struct L3999Unit(L3999Kind Kind, int A0, int C0, int A1, int C1, bool Mini);

    /// <summary>The six neon colours (the Fandom page's own palette), by the index in Detail bits 0-2.</summary>
    public static readonly string[] L3999Colours = { "magenta", "cyan", "blue", "pink", "orange", "lilac" };

    /// <summary>The food stalls' kinds (a stall counter's Stack bits 0-2).</summary>
    public static readonly string[] L3999Foods = { "burger", "pizza", "noodles", "taco", "icecream", "pretzel" };

    /// <summary>The neon signs' words (in Depth under <see cref="Overheads.L3999Sign"/>); 0 none.</summary>
    public static readonly string[] L3999Signs = { "", "arcade", "prizes", "foodcourt", "lobby", "open", "paradise", "exit" };

    /// <summary>The themed cabinets' marquees (a themed cabinet's Stack), each the way to one level (<see cref="L3999ThemeLevel"/>).</summary>
    public static readonly string[] L3999Themes = { "l4", "l5", "l6", "l7", "l9", "l10", "l11", "l37", "l94", "run", "fun", "kitty" };

    /// <summary>The level a themed cabinet's marquee shows, and takes whoever plays it to the end to.</summary>
    public static int L3999ThemeLevel(int theme) => theme switch
    {
        0 => 4, 1 => 5, 2 => 6, 3 => 7, 4 => 9, 5 => 10, 6 => 11, 7 => Poolrooms, 8 => Motion, 9 => RunLevel, 10 => FunLevel, _ => Level974,
    };

    // Detail and Roof bits (see the summary)
    public const byte L3999DarkBit = 8, L3999DeadBit = 64;
    public const byte L3999SlabBit = 1, L3999RailBit = 8, L3999TubeBit = 16, L3999TubeNSBit = 32, L3999ArchBit = 64, L3999BaseBit = 128;

    public static int L3999Colour(in Tile t) => t.Detail & 7;
    public static bool L3999IsDark(in Tile t) => (t.Detail & L3999DarkBit) != 0;
    public static bool L3999LightsDead(in Tile t) => (t.Detail & (L3999DarkBit | L3999DeadBit)) != 0;
    public static int L3999Drift(in Tile t) => (t.Detail >> 4) & 3;
    public static bool L3999HasSlab(in Tile t) => (t.Roof & L3999SlabBit) != 0;

    /// <summary>The way a gallery's balustrade on this tile faces (toward the drop), if it has one.</summary>
    public static ArchPier? L3999Rail(in Tile t) => (t.Roof & L3999RailBit) != 0 ? (ArchPier)((t.Roof >> 1) & 3) : null;

    // ================= Where it is =================

    /// <summary>
    /// How far out along the south-east diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond the Hub, which is 1.25 times out), so a full-size world's 3999 is about 205 km away.
    /// </summary>
    private int L3999Reach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    private int L3999CentreX => spawnMacroX + L3999Reach;
    private int L3999CentreZ => spawnMacroZ + L3999Reach;

    /// <summary>The region's radius in macro cells: endless to anyone in it.</summary>
    private int L3999Radius => Math.Max(60, spawnMacroX / 40);

    /// <summary>The block the level's plans count from.</summary>
    public int L3999OriginX => L3999CentreX * MacroSize;
    public int L3999OriginZ => L3999CentreZ * MacroSize;

    private bool InL3999(double mx, double mz) => InRoundRegion(mx, mz, L3999CentreX, L3999CentreZ, L3999Radius, SaltL3999Shape);

    /// <summary>A place in the inner 35% of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L3999ArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, r = Math.Sqrt(Hashing.Unit(Hashing.Mix(h))) * L3999Radius * 0.35;
        return (L3999CentreX + (int)Math.Round(Math.Cos(angle) * r), L3999CentreZ + (int)Math.Round(Math.Sin(angle) * r));
    }

    /// <summary>Arriving: on a lobby's floor (where wanderers arrive, canon says), on the ground storey, never in the Blackout.</summary>
    private static bool IsL3999ArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Zone == (byte)L3999Zone.Lobby && !L3999IsDark(t) && !L3999HasSlab(t);

    /// <summary>How high above the level's floor to put someone down: standing, or afloat in a pool.</summary>
    private static double L3999ArrivalHeight(in Tile t, double stand) => t.Kind == TileKind.Water ? 0.2 : stand;

    /// <summary>One of the lobbies' revolving doors (the way back for whoever arrives beside it from the Level 10 arcade).</summary>
    public static bool IsL3999Revolving(Tile t) => t.Kind == TileKind.Door && t.Pattern == WallPattern.L3999Revolving && t.Level == Level3999;

    /// <summary>A STAFF ONLY door of the level's.</summary>
    public static bool IsL3999StaffDoor(Tile t) => t.Kind == TileKind.Door && t.Pattern == WallPattern.L3999Staff && t.Level == Level3999;

    /// <summary>The lone arcade's revolving door, out in the fields of Level 10.</summary>
    public static bool IsL3999ArcadeDoor(Tile t) => t.Kind == TileKind.Door && t.Under == Unders.L3999Arcade && t.Level == 10;

    // ================= Plan blocks =================

    /// <summary>The plan block a block position lies in.</summary>
    public (int Bi, int Bj) L3999BlockOf(int gx, int gz) => (Hashing.FloorDiv(gx - L3999OriginX, L3999Block), Hashing.FloorDiv(gz - L3999OriginZ, L3999Block));

    /// <summary>How far out a plan block's middle lies, as a fraction of the region's radius.</summary>
    public double L3999BlockFraction(int bi, int bj)
    {
        double dx = (bi * L3999Block + L3999Block / 2.0) / MacroSize, dz = (bj * L3999Block + L3999Block / 2.0) / MacroSize;
        return Math.Sqrt(dx * dx + dz * dz) / L3999Radius;
    }

    /// <summary>Whether a plan block is the Neon Blackout, Level 3999.1: one in fourteen, only past 65% of the radius.</summary>
    public bool L3999BlackoutBlock(int bi, int bj) =>
        L3999BlockFraction(bi, bj) >= 0.65 && Hashing.Unit(Hashing.Hash(seed, bi, bj, SaltL3999Blackout)) < 1 / 14.0;

    /// <summary>A block's middle in block coordinates.</summary>
    public (int X, int Z) L3999BlockCentre(int bi, int bj) => (L3999OriginX + bi * L3999Block + L3999Block / 2, L3999OriginZ + bj * L3999Block + L3999Block / 2);

    private sealed class L3999Plan
    {
        public readonly Tile[] T = new Tile[L3999Block * L3999Block];
        public readonly List<L3999Unit> Units = new();
    }

    private PlanCache<L3999Plan> l3999Plans;

    private L3999Plan L3999PlanOf(int bi, int bj) => (l3999Plans ??= new PlanCache<L3999Plan>(16, PlanL3999Block)).Get(bi, bj);

    /// <summary>The units of a plan block (rectangles in block-local coordinates).</summary>
    public IReadOnlyList<L3999Unit> L3999UnitsOf(int bi, int bj) => L3999PlanOf(bi, bj).Units;

    /// <summary>The planned tile at a block position (before the cell's own passes, and with no rim).</summary>
    private Tile L3999PlannedTile(int gx, int gz)
    {
        var (bi, bj) = L3999BlockOf(gx, gz);
        int a = gx - L3999OriginX - bi * L3999Block, c = gz - L3999OriginZ - bj * L3999Block;
        return L3999PlanOf(bi, bj).T[c * L3999Block + a];
    }

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: open, the plans are laid over it.</summary>
    private Edge L3999Edge(int mx, int mz, bool west) => new() { Pattern = WallPattern.L3999Wall };

    /// <summary>Whether a cell is on the region's rim: the mall's outer wall, solid, all the way round.</summary>
    private bool L3999IsRimCell(int mx, int mz)
    {
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Level3999) return true;
        return false;
    }

    private void BuildLevel3999(Builder b, int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        if (L3999IsRimCell(mx, mz))
        {
            // Which of the cells round it are the level's own and not rim (their tiles are the ones a rim window looks onto)
            var open = new bool[9];
            for (int dz = -1; dz <= 1; dz++)
                for (int dx = -1; dx <= 1; dx++)
                    open[(dz + 1) * 3 + dx + 1] = LevelAt(mx + dx, mz + dz) == Level3999 && !L3999IsRimCell(mx + dx, mz + dz);
            for (int lz = 0; lz < MacroSize; lz++)
                for (int lx = 0; lx < MacroSize; lx++)
                    b.At(lx, lz) = L3999RimTile(x0 + lx, z0 + lz, mx, mz, open);
            return;
        }
        // The plan blocks count from a cell corner and are four cells a side, so the whole cell lies in one of them
        var (bi, bj) = L3999BlockOf(x0, z0);
        Tile[] plan = L3999PlanOf(bi, bj).T;
        int a0 = x0 - L3999OriginX - bi * L3999Block, c0 = z0 - L3999OriginZ - bj * L3999Block;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
                b.At(lx, lz) = plan[(c0 + lz) * L3999Block + a0 + lx];
    }

    private static readonly ArchPier[] L3999RimSides = { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West };

    /// <summary>
    /// The rim: the outer wall; where it closes off a concourse, unbreakable windows onto a car park at night.
    /// <paramref name="open"/> says which of the nine cells round (and including) the rim cell <paramref name="mx"/>,
    /// <paramref name="mz"/> are the level's and not rim, indexed (dz + 1) * 3 + (dx + 1).
    /// </summary>
    private Tile L3999RimTile(int gx, int gz, int mx, int mz, bool[] open)
    {
        var t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L3999Wall, Height = L3999AtriumHeight, Zone = (byte)L3999Zone.Rim, Detail = 1 };
        foreach (ArchPier d in L3999RimSides)
        {
            var (dx, dz) = Step(d);
            int nx = gx + dx, nz = gz + dz, nmx = MacroOf(nx), nmz = MacroOf(nz);
            if (!open[(nmz - mz + 1) * 3 + nmx - mx + 1]) continue;
            Tile n = L3999PlannedTile(nx, nz);
            if (n.Kind != TileKind.Floor || n.Zone is not ((byte)L3999Zone.Concourse or (byte)L3999Zone.Junction)) continue;
            t.Pattern = WallPattern.L3999Window;
            t.Pier = d;
            t.Variant = (ushort)Hashing.Mod(dx != 0 ? gz : gx, 4);
            break;
        }
        return t;
    }

    // ================= Directions =================

    public static ArchPier L3999Opp(ArchPier d) => d switch
    {
        ArchPier.North => ArchPier.South,
        ArchPier.South => ArchPier.North,
        ArchPier.East => ArchPier.West,
        _ => ArchPier.East,
    };

    /// <summary>The direction on the right hand of someone facing <paramref name="d"/>.</summary>
    public static ArchPier L3999Right(ArchPier d) => d switch
    {
        ArchPier.North => ArchPier.East,
        ArchPier.East => ArchPier.South,
        ArchPier.South => ArchPier.West,
        _ => ArchPier.North,
    };

    /// <summary>A direction's index in the north/east/south/west order of block variants.</summary>
    public static int L3999FacingIndex(ArchPier d) => d switch { ArchPier.North => 0, ArchPier.East => 1, ArchPier.South => 2, _ => 3 };

    private static ArchPier L3999FromIndex(int i) => (i & 3) switch { 0 => ArchPier.North, 1 => ArchPier.East, 2 => ArchPier.South, _ => ArchPier.West };

    private static byte L3999RailRoof(ArchPier d) => (byte)(L3999RailBit | ((int)d << 1));

    // ================= Concourses and junctions =================

    /// <summary>A concourse line's neon colour.</summary>
    private byte L3999LineColour(int axis, int line) => (byte)(Hashing.Hash(seed, axis, line, SaltL3999Colour) % 6);

    /// <summary>
    /// The concourse tile at a position (<paramref name="u"/>, <paramref name="v"/> from the plans' origin) that lies
    /// within six of a block line. A pure function of the position, so both blocks beside a concourse agree on it.
    /// </summary>
    private Tile L3999ConcourseTile(int u, int v)
    {
        int ox = Hashing.Mod(u + 6, L3999Block) - 6, oz = Hashing.Mod(v + 6, L3999Block) - 6;
        int lineX = Hashing.FloorDiv(u + 6, L3999Block), lineZ = Hashing.FloorDiv(v + 6, L3999Block);
        if (ox <= 5 && oz <= 5) return L3999JunctionTile(ox, oz, lineX, lineZ);
        return ox <= 5 ? L3999ArmTile(0, ox, oz, lineX) : L3999ArmTile(1, oz, ox, lineZ);
    }

    /// <summary>
    /// A stretch of concourse between two junctions: axis 0 runs north-south (across is x), axis 1 west-east (across is
    /// z); <paramref name="across"/> is the offset from the line (-6 to 5), <paramref name="s"/> the place along the
    /// stretch (6 to 121; the junctions are at 122-127 and 0-5).
    /// </summary>
    private Tile L3999ArmTile(int axis, int across, int s, int line)
    {
        ArchPier Along(int sign) => axis == 0 ? (sign > 0 ? ArchPier.South : ArchPier.North) : (sign > 0 ? ArchPier.East : ArchPier.West);
        ArchPier Across(int sign) => axis == 0 ? (sign > 0 ? ArchPier.East : ArchPier.West) : (sign > 0 ? ArchPier.South : ArchPier.North);
        var t = new Tile
        {
            Kind = TileKind.Floor, Floor = across is -1 or 0 ? FloorKind.L3999MarbleBlack : FloorKind.L3999Marble, Ceiling = CeilingKind.L3999Ceiling,
            Height = L3999AtriumHeight, Zone = (byte)L3999Zone.Concourse, Pattern = WallPattern.L3999Wall, Detail = L3999LineColour(axis, line),
        };
        // Escalators up to the galleries just off each junction: one on the near side of the stretch's end, one on the far
        // side of its start, each climbing toward the junction
        bool up1 = s is >= 115 and <= 121 && across is -5 or -4, up2 = s is >= 6 and <= 12 && across is 3 or 4;
        if (up1 || up2)
        {
            t.Variant = Props.L3999Escalator;
            t.Stair = (byte)(up1 ? s - 114 : 13 - s);
            t.Pier = up1 ? Along(1) : Along(-1);
            return t;
        }
        bool gallery = across <= -4 || across >= 3, bridge = s is >= 63 and <= 65;
        if (gallery || bridge) t.Roof |= L3999SlabBit;

        // The balustrades: along the galleries' inner edges, along the bridge's sides, and round the escalators' wells
        // (where a corner would need two, a planter on the gallery closes the corner)
        ArchPier? rail = null;
        if (bridge && across is >= -3 and <= 2) rail = s == 63 ? Along(-1) : s == 65 ? Along(1) : null;
        else if (across == -4 && !bridge) rail = Across(1);
        else if (across == 3 && !bridge) rail = Across(-1);
        if (across == -6 && s is >= 115 and <= 121) rail = Across(1);
        if (across == 5 && s is >= 6 and <= 12) rail = Across(-1);
        if (s == 114 && across is -5 or -4) { rail = Along(1); if (across == -4) t.Pipe = Pipes.L3999UpperPlanter; }
        if (s == 13 && across is 3 or 4) { rail = Along(-1); if (across == 3) t.Pipe = Pipes.L3999UpperPlanter; }
        if (rail is { } r) t.Roof |= L3999RailRoof(r);

        // Neon tubes under the galleries, every other block along
        if (gallery && across is -5 or 4 && s % 2 == 0) t.Roof |= (byte)(L3999TubeBit | (axis == 0 ? L3999TubeNSBit : 0));
        // An arch of neon every sixteen: up both walls, and a tube across under the ceiling
        bool wallSide = across is -6 or 5;
        ArchPier fromWall = across == -6 ? Across(1) : Across(-1);
        if (s % 16 == 8)
        {
            t.Overhead = axis == 0 ? Overheads.L3999TubeWE : Overheads.L3999TubeNS;
            if (wallSide) { t.Roof |= L3999ArchBit; t.Pier = fromWall; }
        }
        // A glowing strip along the foot of the shopfronts, but at the units' and the corridors' doors
        if (wallSide && s is not ((>= 29 and <= 38) or (>= 59 and <= 68) or (>= 89 and <= 98)))
        {
            t.Roof |= L3999BaseBit;
            t.Pier = fromWall;
        }

        // The moving walkways, two wide, opposite ways, ending in combplates four short of the junctions
        if (s is >= 10 and <= 117 && across is -3 or -2 or 1 or 2)
        {
            ArchPier dir = across < 0 ? Along(1) : Along(-1);
            bool lower = across is -3 or 1, lowerIsRight = L3999Right(dir) == Across(-1);
            t.Variant = Props.L3999Walkway;
            // (bit 3: the end it starts from, where the combplate ramps up the other way)
            bool start = across < 0 ? s == 10 : s == 117;
            t.Stack = (byte)((s is 10 or 117 ? 1 : 0) | (lower == lowerIsRight ? 4 : 2) | (start ? 8 : 0));
            t.Pier = dir;
            return t;
        }
        // Down the middle between them: pillars and planters under the arches, benches, a bin, a directory
        if (across is -1 or 0 && s is >= 14 and <= 113)
        {
            int m = s % 16;
            if (s % 64 == 32) { t.Variant = Props.L3999Directory; t.Pier = across == 0 ? Along(-1) : Along(1); }
            else if (m == 8) t.Variant = across == -1 ? Props.L3999Pillar : Props.L3999Planter;
            else if (m == 0) t.Variant = across == 0 ? Props.L3999Pillar : s % 64 == 0 ? Props.L3999TrashBin : Props.L3999Planter;
            else if (m is 4 or 12) { t.Variant = Props.L3999Bench; t.Pier = across == -1 ? Across(-1) : Across(1); }
        }
        return t;
    }

    /// <summary>A junction, where two concourses cross: the galleries cross over as bridges, round an open middle under the sign.</summary>
    private Tile L3999JunctionTile(int ox, int oz, int lineX, int lineZ)
    {
        var t = new Tile
        {
            Kind = TileKind.Floor, Floor = ((((ox + 6) >> 1) + ((oz + 6) >> 1)) & 1) == 0 ? FloorKind.L3999Marble : FloorKind.L3999MarbleBlack,
            Ceiling = CeilingKind.L3999Ceiling, Height = L3999AtriumHeight, Zone = (byte)L3999Zone.Junction, Pattern = WallPattern.L3999Wall,
            Detail = (byte)(Hashing.Hash(seed, lineX, lineZ, SaltL3999Colour + 1) % 6),
        };
        static bool Strip(int o) => o <= -4 || o >= 3;
        bool inner(int o) => o is >= -3 and <= 2;
        if (Strip(ox) || Strip(oz)) t.Roof |= L3999SlabBit;
        if (ox is -4 or 3 && inner(oz)) t.Roof |= L3999RailRoof(ox == -4 ? ArchPier.East : ArchPier.West);
        else if (oz is -4 or 3 && inner(ox)) t.Roof |= L3999RailRoof(oz == -4 ? ArchPier.South : ArchPier.North);
        // Neon round the open middle, under the ceiling; the "3999" sign hanging in it
        if (inner(ox) && oz is -3 or 2) t.Overhead = Overheads.L3999TubeWE;
        else if (inner(oz) && ox is -3 or 2) t.Overhead = Overheads.L3999TubeNS;
        if (ox == 0 && oz == 0) t.Overhead = Overheads.L3999Sign3999;
        // A mall directory at each corner of the middle, facing up the concourse beside it
        (int, int) at = (ox, oz);
        if (at == (-3, -3)) { t.Variant = Props.L3999Directory; t.Pier = ArchPier.North; }
        else if (at == (2, -3)) { t.Variant = Props.L3999Directory; t.Pier = ArchPier.East; }
        else if (at == (2, 2)) { t.Variant = Props.L3999Directory; t.Pier = ArchPier.South; }
        else if (at == (-3, 2)) { t.Variant = Props.L3999Directory; t.Pier = ArchPier.West; }
        // Pillars at the junction's corners; tubes under the galleries' corner squares
        if (ox is -6 or 5 && oz is -6 or 5) t.Variant = Props.L3999Pillar;
        if (ox is -5 or 4 && oz is -5 or 4) t.Roof |= L3999TubeBit;
        return t;
    }

    // ================= Planning a block =================

    /// <summary>Helpers over one plan block's tiles while it is planned.</summary>
    private sealed class L3999Planner
    {
        public readonly Tile[] T;
        public Rng Rng;
        public int Bi, Bj;

        public L3999Planner(Tile[] t) => T = t;

        public static bool In(int a, int c) => a >= 0 && c >= 0 && a < L3999Block && c < L3999Block;
        public ref Tile At(int a, int c) => ref T[c * L3999Block + a];
    }

    /// <summary>
    /// A unit's frame of reference: u runs along its front wall (0 to W - 1), w back from it (0 to D - 1); the front wall
    /// is at w = -1, the back wall at w = D, the side walls at u = -1 and u = W.
    /// </summary>
    private readonly struct L3999Frame
    {
        public readonly int A0, C0, A1, C1, W, D;
        public readonly ArchPier Front;

        public L3999Frame(int a0, int c0, int a1, int c1, ArchPier front)
        {
            A0 = a0; C0 = c0; A1 = a1; C1 = c1; Front = front;
            bool ns = front is ArchPier.North or ArchPier.South;
            W = ns ? a1 - a0 - 1 : c1 - c0 - 1;
            D = ns ? c1 - c0 - 1 : a1 - a0 - 1;
        }

        public (int A, int C) Map(int u, int w) => Front switch
        {
            ArchPier.North => (A0 + 1 + u, C0 + 1 + w),
            ArchPier.South => (A1 - 1 - u, C1 - 1 - w),
            ArchPier.West => (A0 + 1 + w, C1 - 1 - u),
            _ => (A1 - 1 - w, C0 + 1 + u),
        };

        /// <summary>Toward the back wall (the way someone coming in through the front faces).</summary>
        public ArchPier Back => L3999Opp(Front);
        /// <summary>The way u grows; the side wall at u = W is on that side, the one at u = -1 on the other.</summary>
        public ArchPier PlusU => Front switch { ArchPier.North => ArchPier.East, ArchPier.South => ArchPier.West, ArchPier.West => ArchPier.North, _ => ArchPier.South };
        public ArchPier MinusU => L3999Opp(PlusU);
        public bool Inside(int u, int w) => u >= 0 && w >= 0 && u < W && w < D;
    }

    private ref Tile L3999F(L3999Planner p, in L3999Frame f, int u, int w)
    {
        var (a, c) = f.Map(u, w);
        return ref p.At(a, c);
    }

    /// <summary>Puts a prop on a floor tile of a unit (only on bare floor).</summary>
    private void L3999Prop(L3999Planner p, in L3999Frame f, int u, int w, ushort prop, int stack, ArchPier pier)
    {
        if (!f.Inside(u, w)) return;
        ref Tile t = ref L3999F(p, f, u, w);
        if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stair != 0 || t.SupplyBox) return;
        t.Variant = prop;
        t.Stack = (byte)stack;
        t.Pier = pier;
    }

    private L3999Plan PlanL3999Block(int bi, int bj)
    {
        var plan = new L3999Plan();
        var p = new L3999Planner(plan.T) { Rng = new Rng(Hashing.Hash(seed, bi, bj, SaltL3999Plan)), Bi = bi, Bj = bj };
        // The concourses and junctions along the block's edges
        for (int c = 0; c < L3999Block; c++)
            for (int a = 0; a < L3999Block; a++)
                if (a < L3999Lo0 || a > L3999Hi1 || c < L3999Lo0 || c > L3999Hi1)
                    p.At(a, c) = L3999ConcourseTile(bi * L3999Block + a, bj * L3999Block + c);
        L3999Corridors(p);
        L3999Units(p, plan, bi, bj);
        L3999Decay(p, plan, bi, bj);
        return plan;
    }

    /// <summary>The cross of service corridors between the quadrants: grey concrete, acoustic tile, white fluorescent tubes; open at both ends.</summary>
    private static void L3999Corridors(L3999Planner p)
    {
        Tile Corridor(bool light) => new()
        {
            Kind = TileKind.Floor, Floor = FloorKind.L3999Concrete, Height = L3999CorridorHeight, Zone = (byte)L3999Zone.Service,
            Ceiling = light ? CeilingKind.L3999Fluoro : CeilingKind.L3999Acoustic, Pattern = WallPattern.L3999Concrete,
        };
        for (int s = L3999Lo0; s <= L3999Hi1; s++)
            for (int k = L3999Lo1 + 1; k < L3999Hi0; k++)
            {
                p.At(k, s) = Corridor(k == L3999Lo1 + 2 && s % 6 == 3);
                p.At(s, k) = Corridor(k == L3999Lo1 + 2 && s % 6 == 3);
            }
        // Each end meets a concourse in a two-wide service doorway
        foreach (int end in new[] { L3999Lo0, L3999Hi1 })
            for (int k = L3999Lo1 + 1; k < L3999Hi0; k++)
            {
                bool door = k is L3999Lo1 + 2 or L3999Lo1 + 3;
                var t = new Tile
                {
                    Kind = door ? TileKind.Doorway : TileKind.Wall, Pattern = WallPattern.L3999Concrete, Floor = FloorKind.L3999Concrete,
                    Height = door ? (byte)L3999DoorHeight : (byte)L3999AtriumHeight, Zone = (byte)L3999Zone.Service,
                };
                p.At(k, end) = t;
                p.At(end, k) = t;
            }
    }

    /// <summary>The block's units: four quadrants, or a merged pair and two quadrants.</summary>
    private void L3999Units(L3999Planner p, L3999Plan plan, int bi, int bj)
    {
        ulong mh = Hashing.Hash(seed, bi, bj, SaltL3999Merge);
        double mr = Hashing.Unit(mh);
        L3999Kind? merged = mr < 0.09 && L3999BlockFraction(bi, bj) >= 0.3 ? L3999Kind.Natatorium : mr < 0.21 ? L3999Kind.GameHall : null;
        var done = new bool[2, 2];
        if (merged is { } mk)
        {
            int pair = (int)(Hashing.Mix(mh) % 4);
            // 0 the north pair, 1 the south pair, 2 the west pair, 3 the east pair
            var (qa0, qc0, qa1, qc1) = pair switch { 0 => (0, 0, 1, 0), 1 => (0, 1, 1, 1), 2 => (0, 0, 0, 1), _ => (1, 0, 1, 1) };
            done[qa0, qc0] = done[qa1, qc1] = true;
            ArchPier front = pair switch { 0 => ArchPier.North, 1 => ArchPier.South, 2 => ArchPier.West, _ => ArchPier.East };
            PlanL3999Unit(p, plan, mk, qa0 == 0 ? L3999Lo0 : L3999Hi0, qc0 == 0 ? L3999Lo0 : L3999Hi0,
                qa1 == 0 ? L3999Lo1 : L3999Hi1, qc1 == 0 ? L3999Lo1 : L3999Hi1, front, bi * 4 + pair, bj * 4 + 3);
        }
        for (int qj = 0; qj < 2; qj++)
            for (int qi = 0; qi < 2; qi++)
            {
                if (done[qi, qj]) continue;
                ulong h = Hashing.Hash(seed, bi * 2 + qi, bj * 2 + qj, SaltL3999Unit);
                double r = Hashing.Unit(h) * 79;
                L3999Kind kind = r < 40 ? L3999Kind.Game : r < 54 ? L3999Kind.FoodCourt : r < 66 ? L3999Kind.Lobby : r < 71 ? L3999Kind.Lanes : L3999Kind.Shuttered;
                ArchPier front = (Hashing.Mix(h) & 1) == 0 ? (qj == 0 ? ArchPier.North : ArchPier.South) : (qi == 0 ? ArchPier.West : ArchPier.East);
                PlanL3999Unit(p, plan, kind, qi == 0 ? L3999Lo0 : L3999Hi0, qj == 0 ? L3999Lo0 : L3999Hi0, qi == 0 ? L3999Lo1 : L3999Hi1,
                    qj == 0 ? L3999Lo1 : L3999Hi1, front, bi * 4 + qi, bj * 4 + qj);
            }
    }

    /// <summary>Whether the side of a unit's rectangle facing <paramref name="d"/> fronts onto a concourse.</summary>
    private static bool L3999Frontage(int a0, int c0, int a1, int c1, ArchPier d) => d switch
    {
        ArchPier.North => c0 == L3999Lo0,
        ArchPier.South => c1 == L3999Hi1,
        ArchPier.West => a0 == L3999Lo0,
        _ => a1 == L3999Hi1,
    };

    private void PlanL3999Unit(L3999Planner p, L3999Plan plan, L3999Kind kind, int a0, int c0, int a1, int c1, ArchPier front, int ui, int uj)
    {
        var f = new L3999Frame(a0, c0, a1, c1, front);
        p.Rng = new Rng(Hashing.Hash(seed, ui, uj, SaltL3999Unit + 1));
        ref Rng rng = ref p.Rng;
        byte colour = (byte)rng.Range(0, 5);
        L3999Zone zone = kind switch
        {
            L3999Kind.Game => L3999Zone.Game,
            L3999Kind.GameHall => L3999Zone.GameHall,
            L3999Kind.FoodCourt => L3999Zone.FoodCourt,
            L3999Kind.Lobby => L3999Zone.Lobby,
            L3999Kind.Lanes => L3999Zone.Lanes,
            L3999Kind.Shuttered => L3999Zone.Shuttered,
            _ => L3999Zone.Natatorium,
        };
        bool hall = kind is L3999Kind.Game or L3999Kind.Lanes or L3999Kind.Shuttered;
        FloorKind floor = kind switch
        {
            L3999Kind.Game or L3999Kind.GameHall => FloorKind.L3999Floor,
            L3999Kind.Lobby or L3999Kind.Lanes => FloorKind.L3999Galaxy,
            L3999Kind.FoodCourt => FloorKind.L3999Marble,
            L3999Kind.Shuttered => FloorKind.L3999Concrete,
            _ => FloorKind.L3999PoolLilac,
        };

        // The floor
        for (int w = 0; w < f.D; w++)
            for (int u = 0; u < f.W; u++)
                L3999F(p, f, u, w) = new Tile
                {
                    Kind = TileKind.Floor, Floor = floor, Height = (byte)(hall ? L3999HallHeight : L3999AtriumHeight), Zone = (byte)zone,
                    Detail = colour, Ceiling = kind == L3999Kind.Shuttered && (u % 8 == 4 && w % 8 == 4) ? CeilingKind.L3999Fluoro : CeilingKind.L3999Ceiling,
                    Pattern = WallPattern.L3999Wall,
                };
        // The walls: glass shopfronts onto the concourses, painted plaster against the service corridors
        for (int w = -1; w <= f.D; w++)
            for (int u = -1; u <= f.W; u++)
            {
                if (f.Inside(u, w)) continue;
                bool corner = (u == -1 || u == f.W) && (w == -1 || w == f.D);
                ArchPier d = w == -1 ? f.Front : w == f.D ? f.Back : u == -1 ? f.MinusU : f.PlusU;
                L3999F(p, f, u, w) = new Tile
                {
                    Kind = TileKind.Wall, Pattern = !corner && L3999Frontage(a0, c0, a1, c1, d) ? WallPattern.L3999Shopfront : WallPattern.L3999Wall,
                    Height = L3999AtriumHeight, Detail = colour, Zone = (byte)zone, Pier = d, Floor = floor,
                };
            }

        // The way in, under a neon sign: on the front, and on a second frontage if the unit has one
        byte sign = kind switch
        {
            L3999Kind.Game or L3999Kind.GameHall => 1,
            L3999Kind.FoodCourt => 3,
            L3999Kind.Lobby => 4,
            L3999Kind.Lanes or L3999Kind.Natatorium => 5,
            _ => 0,
        };
        ArchPier? second = L3999Frontage(a0, c0, a1, c1, f.MinusU) ? f.MinusU : L3999Frontage(a0, c0, a1, c1, f.PlusU) ? f.PlusU : null;
        // (A lobby's second frontage holds its revolving door instead)
        L3999Entrance(p, f, f.Front, kind == L3999Kind.Shuttered, sign, floor);
        if (second is { } s2 && kind is not (L3999Kind.Lobby or L3999Kind.Natatorium)) L3999Entrance(p, f, s2, kind == L3999Kind.Shuttered, sign, floor);

        // A STAFF ONLY door in the back wall, onto the service corridor (the shuttered units have an open doorway there instead)
        if (kind == L3999Kind.Shuttered)
        {
            for (int u = f.W / 2 - 1; u <= f.W / 2; u++)
                L3999F(p, f, u, f.D) = new Tile { Kind = TileKind.Doorway, Pattern = WallPattern.L3999Wall, Height = L3999DoorHeight, Floor = floor, Zone = (byte)zone, Detail = colour };
        }
        else L3999F(p, f, 3, f.D) = new Tile { Kind = TileKind.Door, Pattern = WallPattern.L3999Staff, Height = L3999AtriumHeight, Pier = f.Front, Zone = (byte)zone, Detail = colour };

        bool mini = false;
        switch (kind)
        {
            case L3999Kind.Game: mini = PlanL3999Games(p, f, false); break;
            case L3999Kind.GameHall: PlanL3999Games(p, f, true); break;
            case L3999Kind.FoodCourt: PlanL3999FoodCourt(p, f, a0, c0, a1, c1); break;
            case L3999Kind.Lobby: PlanL3999Lobby(p, f, second ?? f.PlusU); break;
            case L3999Kind.Lanes: PlanL3999Lanes(p, f); break;
            case L3999Kind.Shuttered: PlanL3999Stores(p, f); break;
            case L3999Kind.Natatorium: PlanL3999Natatorium(p, f); break;
        }
        plan.Units.Add(new L3999Unit(kind, a0, c0, a1, c1, mini));
    }

    /// <summary>A six-wide way in, centred on a frontage, with the unit's neon sign over it outside (a shutter, for a closed unit).</summary>
    private void L3999Entrance(L3999Planner p, in L3999Frame f, ArchPier side, bool shutter, byte sign, FloorKind floor)
    {
        bool front = side == f.Front;
        int centre = front ? f.W / 2 : f.D / 2;
        int wallU = side == f.MinusU ? -1 : f.W;
        for (int k = centre - 3; k <= centre + 2; k++)
        {
            ref Tile t = ref front ? ref L3999F(p, f, k, -1) : ref L3999F(p, f, wallU, k);
            t.Kind = shutter ? TileKind.Wall : TileKind.Doorway;
            t.Pattern = shutter ? WallPattern.L3999Shutter : WallPattern.L3999Shopfront;
            t.Height = shutter ? (byte)2 : (byte)L3999DoorHeight;
            t.Floor = floor;
            t.Pier = side;
        }
        if (sign == 0) return;
        var (a, c) = front ? f.Map(centre, -2) : f.Map(side == f.MinusU ? -2 : f.W + 1, centre);
        if (!L3999Planner.In(a, c)) return;
        ref Tile outside = ref p.At(a, c);
        if (outside.Kind != TileKind.Floor || outside.Overhead != 0) return;
        outside.Overhead = Overheads.L3999Sign;
        outside.Depth = sign;
        outside.Pier = side;
    }

    /// <summary>A neon sign at rel 5 over a floor tile of a unit (over a counter's attendant, say).</summary>
    private void L3999SignAt(L3999Planner p, in L3999Frame f, int u, int w, byte sign, ArchPier facing)
    {
        if (!f.Inside(u, w)) return;
        ref Tile t = ref L3999F(p, f, u, w);
        if (t.Kind != TileKind.Floor) return;
        t.Overhead = Overheads.L3999Sign;
        t.Depth = sign;
        t.Pier = facing;
    }

    /// <summary>A neon tube under a unit's ceiling, running along <paramref name="axis"/> (north-south or west-east).</summary>
    private void L3999Tube(L3999Planner p, in L3999Frame f, int u, int w, ArchPier axis)
    {
        if (!f.Inside(u, w)) return;
        ref Tile t = ref L3999F(p, f, u, w);
        if (t.Kind != TileKind.Floor || t.Overhead != 0) return;
        t.Overhead = axis is ArchPier.North or ArchPier.South ? Overheads.L3999TubeNS : Overheads.L3999TubeWE;
    }

    /// <summary>A wall inside a unit (the mini arcade's).</summary>
    private void L3999InnerWall(L3999Planner p, in L3999Frame f, int u, int w, int height)
    {
        if (!f.Inside(u, w)) return;
        ref Tile t = ref L3999F(p, f, u, w);
        t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L3999Wall, Height = (byte)height, Detail = t.Detail, Zone = t.Zone, Floor = t.Floor };
    }

    // ================= Units =================

    /// <summary>
    /// A game area (or, in an atrium with a gallery ring of cabinets, a game hall): rows of machines back to back, two-wide
    /// aisles, every row one kind; a prize counter on the back wall with its attendant, the prizes on the wall behind;
    /// neon strips under the ceiling along the aisles. Now and then, in a back corner, the mini arcade. Returns whether it
    /// has one.
    /// </summary>
    private bool PlanL3999Games(L3999Planner p, in L3999Frame f, bool atrium)
    {
        ref Rng rng = ref p.Rng;
        int mid = f.W / 2;
        if (atrium)
        {
            L3999Ring(p, f);
            L3999RingEscalator(p, f);
        }
        for (int u = mid - 3; u <= mid + 3; u++) L3999Prop(p, f, u, f.D - 1, Props.L3999PrizeWall, 0, f.Front);
        for (int u = mid - 2; u <= mid + 2; u++) L3999Prop(p, f, u, f.D - 3, Props.L3999PrizeCounter, 0, f.Front);
        L3999SignAt(p, f, mid, f.D - 2, 2, f.Front);
        bool mini = !atrium && f.W >= 40 && f.D >= 40 && rng.Chance(0.14);
        if (mini) PlanL3999MiniArcade(p, f);
        bool rustOk = L3999DarkNear(p.Bi, p.Bj, 24) && !L3999BlackoutBlock(p.Bi, p.Bj);
        bool alongU = rng.Chance(0.5);
        int u0 = mini ? 23 : atrium ? 5 : 3, u1 = f.W - (atrium ? 6 : 4), w0 = atrium ? 5 : 4, w1 = f.D - 6;
        if (alongU) L3999Rows(p, f, true, w0, w1, u0, u1, rustOk, atrium);
        else L3999Rows(p, f, false, u0, u1, w0, w1, rustOk, atrium);
        if (atrium) L3999UpperCabinets(p, f);
        if (atrium) L3999Rails(p, f);
        // Neon up the walls and along their feet
        L3999WallNeon(p, f, 8);
        return mini;
    }

    /// <summary>
    /// Rows of machines: across from <paramref name="x0"/> to <paramref name="x1"/>, each row running along from
    /// <paramref name="s0"/> to <paramref name="s1"/> with a cross aisle every eleven. Along u if <paramref name="alongU"/>.
    /// </summary>
    private void L3999Rows(L3999Planner p, in L3999Frame f, bool alongU, int x0, int x1, int s0, int s1, bool rustOk, bool atrium)
    {
        ref Rng rng = ref p.Rng;
        ArchPier minus = alongU ? f.Front : f.MinusU, plus = alongU ? f.Back : f.PlusU, alongDir = alongU ? f.PlusU : f.Back;
        var frame = f;
        void Put(int x, int s, ushort prop, int stack, ArchPier pier)
        {
            if (alongU) L3999Prop(p, frame, s, x, prop, stack, pier);
            else L3999Prop(p, frame, x, s, prop, stack, pier);
        }
        int x = x0;
        while (true)
        {
            double r = rng.NextDouble();
            int kind = r < 0.5 ? 0 : r < 0.6 ? 1 : r < 0.67 ? 2 : r < 0.77 ? 3 : r < 0.86 ? 4 : r < 0.93 ? 5 : 6;
            int depth = kind switch { 1 or 2 or 5 => 4, 6 => 1, _ => 2 };
            if (x + depth - 1 > x1) break;
            int game = rng.Range(0, 5);
            for (int s = s0; s <= s1; s++)
            {
                int k = (s - s0) % 11;
                if (k >= 9) continue; // a cross aisle
                switch (kind)
                {
                    case 0:
                        for (int side = 0; side < 2; side++)
                        {
                            double roll = rng.NextDouble();
                            ArchPier face = side == 0 ? minus : plus;
                            if (rustOk && roll < 1 / 200.0) Put(x + side, s, Props.L3999Rusted, 0, face);
                            else if (roll < 1 / 30.0) Put(x + side, s, Props.L3999Themed, rng.Range(0, L3999Themes.Length - 1), face);
                            else Put(x + side, s, Props.L3999Cabinet, game, face);
                        }
                        break;
                    case 1:
                    case 2:
                    case 5:
                        // Two-part games: the seat (pad, lane) one block in front of the screen (target), both facing the aisle
                        ushort front = kind == 1 ? Props.L3999RacerSeat : kind == 2 ? Props.L3999DancePad : Props.L3999SkeeLane;
                        ushort back = kind == 1 ? Props.L3999RacerScreen : kind == 2 ? Props.L3999DanceScreen : Props.L3999SkeeTarget;
                        // (the racer's seat and the dance pad face the screen; a skee-ball lane faces the way its player stands, as its target does)
                        Put(x, s, front, 0, kind == 5 ? minus : plus);
                        Put(x + 1, s, back, 0, minus);
                        Put(x + 2, s, back, 0, plus);
                        Put(x + 3, s, front, 0, kind == 5 ? plus : minus);
                        break;
                    case 3:
                        Put(x, s, Props.L3999Pinball, 0, minus);
                        Put(x + 1, s, Props.L3999Pinball, 0, plus);
                        break;
                    case 4:
                        Put(x, s, Props.L3999Claw, 0, minus);
                        Put(x + 1, s, Props.L3999Claw, 0, plus);
                        break;
                    case 6:
                        // Air hockey: two-block tables end to end along the row, room to play at each end
                        // (half a faces along the row; half b lies against a's back edge, facing the other way)
                        if (k % 4 == 0 && k < 8) { Put(x, s + 1, Props.L3999AirHockey, 0, alongDir); Put(x, s, Props.L3999AirHockey, 1, L3999Opp(alongDir)); }
                        break;
                }
            }
            // The aisle after the row: a neon strip under the ceiling along it (in an atrium, pillars at the cross aisles)
            int aisle = x + depth;
            for (int s = s0 - 1; s <= s1 + 1; s++)
            {
                if (atrium)
                {
                    if ((s - s0) % 11 == 9 && s <= s1) Put(aisle, s, Props.L3999Pillar, 0, minus);
                    continue;
                }
                if (alongU) L3999Tube(p, frame, s, aisle, alongDir);
                else L3999Tube(p, frame, aisle, s, alongDir);
            }
            x += depth + 2;
        }
    }

    /// <summary>
    /// The mini arcade: a small room of machines in a back corner of a game area, a table heaped with red tickets, and the
    /// elevator, its keypad beside it. Its interior is u 0-18, w D-19 to D-1.
    /// </summary>
    private void PlanL3999MiniArcade(L3999Planner p, in L3999Frame f)
    {
        int D = f.D;
        for (int w = D - 20; w <= D - 1; w++) L3999InnerWall(p, f, 19, w, L3999HallHeight);
        for (int u = 0; u <= 19; u++) L3999InnerWall(p, f, u, D - 20, L3999HallHeight);
        for (int w = D - 11; w <= D - 10; w++)
        {
            ref Tile door = ref L3999F(p, f, 19, w);
            door.Kind = TileKind.Doorway;
            door.Height = L3999DoorHeight;
        }
        for (int w = D - 19; w <= D - 1; w++)
            for (int u = 0; u <= 18; u++)
            {
                ref Tile t = ref L3999F(p, f, u, w);
                t.Zone = (byte)L3999Zone.MiniArcade;
                t.Floor = FloorKind.L3999Galaxy;
            }
        // The elevator, in the unit's back wall, and its keypad
        L3999F(p, f, 9, D) = new Tile { Kind = TileKind.Door, Pattern = WallPattern.L3999Elevator, Height = L3999AtriumHeight, Pier = f.Front, Zone = (byte)L3999Zone.MiniArcade, Detail = 3 };
        L3999Prop(p, f, 10, D - 1, Props.L3999Keypad, 0, f.Front);
        L3999Prop(p, f, 3, D - 1, Props.L3999TicketPile, 0, f.Front);
        L3999Prop(p, f, 4, D - 1, Props.L3999TicketPile, 0, f.Front);
        // Two rows of machines, back to back
        for (int u = 3; u <= 15; u++)
        {
            if (u == 9) continue;
            L3999Prop(p, f, u, D - 13, Props.L3999Cabinet, u % 6, f.Front);
            L3999Prop(p, f, u, D - 12, Props.L3999Cabinet, (u + 3) % 6, f.Back);
        }
        for (int u = 1; u <= 17; u++) L3999Tube(p, f, u, D - 6, f.PlusU);
        for (int u = 1; u <= 17; u++) L3999Tube(p, f, u, D - 16, f.PlusU);
        // Its sign, over the doorway outside
        L3999SignAt(p, f, 20, D - 11, 1, f.PlusU);
    }

    /// <summary>A gallery ring three wide round an atrium's walls (its slab at rel 7), with neon tubes under it.</summary>
    private void L3999Ring(L3999Planner p, in L3999Frame f)
    {
        for (int w = 0; w < f.D; w++)
            for (int u = 0; u < f.W; u++)
            {
                int du = Math.Min(u, f.W - 1 - u), dw = Math.Min(w, f.D - 1 - w), d = Math.Min(du, dw);
                if (d > 2) continue;
                ref Tile t = ref L3999F(p, f, u, w);
                if (t.Kind != TileKind.Floor) continue;
                t.Roof |= L3999SlabBit;
                // A tube under the slab every third block, along the wall it runs beside
                bool besideFrontBack = dw <= du;
                ArchPier axis = besideFrontBack ? f.PlusU : f.Back;
                if (d is 1 or 2 && (besideFrontBack ? u : w) % 2 == d % 2)
                    t.Roof |= (byte)(L3999TubeBit | (axis is ArchPier.North or ArchPier.South ? L3999TubeNSBit : 0));
            }
    }

    /// <summary>An escalator up to a ring, on the minus side, climbing toward the back (u 1-2, w 5-11).</summary>
    private void L3999RingEscalator(L3999Planner p, in L3999Frame f)
    {
        for (int k = 0; k < 7; k++)
            for (int u = 1; u <= 2; u++)
            {
                ref Tile t = ref L3999F(p, f, u, 5 + k);
                t.Roof = 0;
                t.Variant = Props.L3999Escalator;
                t.Stair = (byte)(k + 1);
                t.Pier = f.Back;
            }
    }

    /// <summary>
    /// Balustrades on every gallery tile of a unit that borders an opening (not toward an escalator's top step, the
    /// way off it). Where a tile would need two, a planter on it closes the corner.
    /// </summary>
    private void L3999Rails(L3999Planner p, in L3999Frame f)
    {
        var dirs = new[] { f.Front, f.Back, f.MinusU, f.PlusU };
        var steps = new (int Du, int Dw)[] { (0, -1), (0, 1), (-1, 0), (1, 0) };
        for (int w = 0; w < f.D; w++)
            for (int u = 0; u < f.W; u++)
            {
                ref Tile t = ref L3999F(p, f, u, w);
                if (!L3999HasSlab(t) || t.Kind != TileKind.Floor) continue;
                int found = 0;
                ArchPier first = ArchPier.North;
                for (int i = 0; i < 4; i++)
                {
                    int nu = u + steps[i].Du, nw = w + steps[i].Dw;
                    if (!f.Inside(nu, nw)) continue;
                    Tile n = L3999F(p, f, nu, nw);
                    if (n.Kind != TileKind.Floor || L3999HasSlab(n)) continue;
                    if (n.Variant == Props.L3999Escalator && n.Stair >= 6) continue;
                    if (found++ == 0) first = dirs[i];
                }
                if (found == 0) continue;
                t.Roof |= L3999RailRoof(first);
                if (found > 1 && t.Pipe == 0) t.Pipe = Pipes.L3999UpperPlanter;
            }
    }

    /// <summary>A game hall's gallery ring: machines along its outer edge, facing in.</summary>
    private void L3999UpperCabinets(L3999Planner p, in L3999Frame f)
    {
        for (int w = 0; w < f.D; w++)
            for (int u = 0; u < f.W; u++)
            {
                bool side = u == 0 || u == f.W - 1, back = w == f.D - 1;
                if (!(side || back) || w == 0 || (side && back)) continue;
                if (u <= 2 && w is >= 3 and <= 13) continue; // round the escalator
                ref Tile t = ref L3999F(p, f, u, w);
                if (!L3999HasSlab(t) || t.Pipe != 0) continue;
                ArchPier inward = back ? f.Front : u == 0 ? f.PlusU : f.MinusU;
                t.Pipe = (byte)(Pipes.L3999UpperCabinet + L3999FacingIndex(inward));
            }
    }

    /// <summary>
    /// A food court: a single-file line of five to seven stalls along the back wall (a counter, its neon sign, a menu
    /// board, an attendant behind), rows of tables with moulded chairs round a clear way in, diner booths along a side
    /// wall, Almond Water vending machines by the door, a gallery ring with an escalator; a colonnade of neon pillars round
    /// the open middle; in one in three, windows on the gallery onto the car park outside.
    /// </summary>
    private void PlanL3999FoodCourt(L3999Planner p, in L3999Frame f, int a0, int c0, int a1, int c1)
    {
        ref Rng rng = ref p.Rng;
        int W = f.W, D = f.D, mid = W / 2;
        L3999Ring(p, f);
        L3999RingEscalator(p, f);
        // The stalls
        int n = rng.Range(5, 7), start = (W - (4 * n - 1)) / 2;
        int[] order = { 0, 1, 2, 3, 4, 5 };
        for (int i = order.Length - 1; i > 0; i--) { int j = rng.Range(0, i); (order[i], order[j]) = (order[j], order[i]); }
        for (int k = 0; k < n; k++)
        {
            int s = start + 4 * k, food = order[k % order.Length];
            for (int i = 0; i < 3; i++) L3999Prop(p, f, s + i, D - 2, Props.L3999StallCounter, food, f.Front);
            // Against the back wall over the attendant: the menu board (rel 3) and the stall's neon sign (rel 5)
            L3999Prop(p, f, s + 1, D - 1, Props.L3999MenuBoard, food, f.Front);
        }
        // Almond Water vending machines inside the front, beside the way in
        L3999Prop(p, f, mid - 5, 0, Props.L3999Vending, 0, f.Back);
        L3999Prop(p, f, mid - 6, 0, Props.L3999Vending, 1, f.Back);
        // Booths along the plus side
        for (int w = 6; w + 2 <= D - 6; w += 4)
        {
            L3999Prop(p, f, W - 1, w, Props.L3999Booth, 0, f.Back);
            L3999Prop(p, f, W - 1, w + 1, Props.L3999Table, 0, f.Back);
            L3999Prop(p, f, W - 1, w + 2, Props.L3999Booth, 0, f.Front);
        }
        // Tables and chairs in the middle, round a clear way from the door to the stalls
        int chair = rng.Range(0, 2);
        for (int w = 6; w <= D - 8; w += 5)
            for (int u = 6; u <= W - 7; u += 5)
            {
                if (Math.Abs(u - mid) <= 4) continue;
                L3999Prop(p, f, u, w, Props.L3999Table, 0, f.Front);
                L3999Prop(p, f, u - 1, w, Props.L3999Chair, chair, f.PlusU);
                L3999Prop(p, f, u + 1, w, Props.L3999Chair, chair, f.MinusU);
                L3999Prop(p, f, u, w - 1, Props.L3999Chair, chair, f.Back);
                L3999Prop(p, f, u, w + 1, Props.L3999Chair, chair, f.Front);
            }
        // Neon pillars round the open middle, just in from the gallery, and among the tables (the atrium's only light low down)
        for (int w = 3; w <= D - 6; w += 6)
        {
            L3999Prop(p, f, 3, w, Props.L3999Pillar, 0, f.Front);
            L3999Prop(p, f, W - 4, w, Props.L3999Pillar, 0, f.Front);
        }
        for (int u = 3; u <= W - 4; u += 6)
            if (Math.Abs(u - mid) > 4) L3999Prop(p, f, u, 3, Props.L3999Pillar, 0, f.Front);
        if (Version >= 5)
        {
            // Layout version 5 on: among the tables, a pillar every ten blocks rather than five (in 1-4 a forest), and
            // neon tubes under the ceiling every six blocks across the atrium, as over the concourses
            foreach (int u in new[] { 9, 19, W - 20, W - 10 })
                for (int w = 9; w <= D - 9; w += 10)
                    if (Math.Abs(u - mid) > 4) L3999Prop(p, f, u, w, Props.L3999Pillar, 0, f.Front);
            for (int w = 3; w < D; w += 6)
                for (int u = 0; u < W; u++) L3999Tube(p, f, u, w, f.PlusU);
        }
        else
            for (int w = 8; w <= D - 9; w += 5)
                for (int u = 8; u <= W - 9; u += 5)
                    if (Math.Abs(u - mid) > 4) L3999Prop(p, f, u, w, Props.L3999Pillar, 0, f.Front);
        // Windows on the gallery, onto the car park, in the side wall that is not a shopfront
        if (rng.Chance(1 / 3.0))
        {
            int wallU = !L3999Frontage(a0, c0, a1, c1, f.MinusU) ? -1 : !L3999Frontage(a0, c0, a1, c1, f.PlusU) ? W : int.MinValue;
            if (wallU != int.MinValue)
                for (int k = 0; k < 4; k++)
                {
                    ref Tile t = ref L3999F(p, f, wallU, D / 2 - 2 + k);
                    if (t.Kind != TileKind.Wall) continue;
                    t.Pattern = WallPattern.L3999Window;
                    t.Variant = (ushort)k;
                    t.Pier = wallU < 0 ? f.PlusU : f.MinusU;
                }
        }
        // Benches along the gallery, a planter in each corner
        for (int w = 0; w < D; w++)
            for (int u = 0; u < W; u++)
            {
                bool edge = u == 0 || u == W - 1 || w == 0 || w == D - 1;
                if (!edge) continue;
                ref Tile t = ref L3999F(p, f, u, w);
                if (!L3999HasSlab(t) || t.Pipe != 0) continue;
                bool corner = (u == 0 || u == W - 1) && (w == 0 || w == D - 1);
                if (corner) { t.Pipe = Pipes.L3999UpperPlanter; continue; }
                if (u <= 2 && w is >= 3 and <= 13) continue;
                int along = u == 0 || u == W - 1 ? w : u;
                if (along % 6 != 3) continue;
                ArchPier inward = w == 0 ? f.Back : w == D - 1 ? f.Front : u == 0 ? f.PlusU : f.MinusU;
                t.Pipe = (byte)(Pipes.L3999UpperBench + L3999FacingIndex(inward));
            }
        L3999Rails(p, f);
    }

    /// <summary>
    /// A lobby, where wanderers arrive: a curved reception desk with an attendant on one side wall, a revolving door
    /// opposite it (on the second frontage), couches and coffee tables in strict rows, planters, a lost-and-found bin, the
    /// LOBBY sign over the desk, neon up the walls (from layout version 5, also under the ceiling, and a row of machines
    /// against the back wall). One lobby in four has a wanderer's camp.
    /// </summary>
    private void PlanL3999Lobby(L3999Planner p, in L3999Frame f, ArchPier revolvingSide)
    {
        int W = f.W, D = f.D, wc = D / 2;
        bool minus = revolvingSide == f.MinusU;
        int doorU = minus ? -1 : W;
        ArchPier inward = minus ? f.PlusU : f.MinusU;
        for (int k = -1; k <= 1; k++)
        {
            ref Tile t = ref L3999F(p, f, doorU, wc + k);
            t.Kind = TileKind.Door;
            t.Pattern = WallPattern.L3999Revolving;
            t.Stack = (byte)(k + 1);
            t.Pier = inward;
            t.Height = 3;
        }
        // The reception desk opposite, an attendant's place behind it, the LOBBY sign over it
        int deskU = minus ? W - 2 : 1, backU = minus ? W - 1 : 0;
        // (left, middle, right as seen from in front of it)
        bool leftHigh = L3999Right(L3999Opp(inward)) == f.Back;
        for (int k = -1; k <= 1; k++) L3999Prop(p, f, deskU, wc + k, Props.L3999Reception, leftHigh ? 1 - k : k + 1, L3999Opp(inward));
        L3999Prop(p, f, deskU, wc + 3, Props.L3999LostFound, 0, L3999Opp(inward));
        L3999SignAt(p, f, backU, wc, 4, L3999Opp(inward));
        // Couches facing across coffee tables, in strict rows, round a clear aisle from the revolving door to the desk and
        // a clear way in from the front
        for (int gw = 5; gw + 1 <= D - 5; gw += 5)
        {
            if (Math.Abs(gw - wc) <= 3 || Math.Abs(gw + 1 - wc) <= 3) continue;
            for (int gu = 6; gu + 2 <= W - 7; gu += 5)
            {
                if (gw < 9 && Math.Abs(gu + 1 - W / 2) <= 5) continue;
                // (a couch's left half is on its right hand, seen from in front of it)
                int plusLeft = L3999Right(f.PlusU) == f.Back ? 1 : 0, minusLeft = 1 - plusLeft;
                L3999Prop(p, f, gu, gw, Props.L3999Couch, plusLeft == 0 ? 0 : 1, f.PlusU);
                L3999Prop(p, f, gu, gw + 1, Props.L3999Couch, plusLeft == 1 ? 0 : 1, f.PlusU);
                L3999Prop(p, f, gu + 1, gw, Props.L3999CoffeeTable, 0, f.PlusU);
                L3999Prop(p, f, gu + 1, gw + 1, Props.L3999CoffeeTable, 0, f.PlusU);
                L3999Prop(p, f, gu + 2, gw, Props.L3999Couch, minusLeft == 0 ? 0 : 1, f.MinusU);
                L3999Prop(p, f, gu + 2, gw + 1, Props.L3999Couch, minusLeft == 1 ? 0 : 1, f.MinusU);
            }
        }
        // Planters in the corners and either side of the revolving door
        foreach (var (u, w) in new[] { (0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1), (minus ? 0 : W - 1, wc - 3), (minus ? 0 : W - 1, wc + 3) })
            L3999Prop(p, f, u, w, Props.L3999Planter, 0, f.Front);
        if (Version >= 5)
        {
            // Layout version 5 on: a row of six machines against the back wall, facing the way in (canon's machines
            // stand "at random about the level"), so a lobby reads as an arcade at a glance; neon tubes under the
            // ceiling every six blocks, running back from the front, as over the concourses
            int game = p.Rng.Range(0, 5);
            for (int k = 0; k < 6; k++) L3999Prop(p, f, W / 2 - 3 + k, D - 1, Props.L3999Cabinet, (game + k) % 6, f.Front);
            for (int u = 3; u < W; u += 6)
                for (int w = 0; w < D; w++) L3999Tube(p, f, u, w, f.Back);
        }
        // Neon up the walls every six blocks, and along their feet; pillars at the inner corners
        L3999WallNeon(p, f, 4);
        // Neon pillars in strict rows among the couches (the atrium's light low down), clear of the aisle and the way in
        if (Version >= 5)
        {
            // (Layout version 5 on: every ten blocks, not five, and in pairs either side of the way in and the aisle, so
            // the two cross as naves; in 1-4 the rows of pillars every five were a forest)
            int[] at = { 4, 14, W / 2 - 3, W / 2 + 2, W - 15, W - 5 }, atW = { 4, 14, wc - 3, wc + 2, D - 15, D - 5 };
            foreach (int w in atW)
                foreach (int u in at)
                    if (!(w < 9 && Math.Abs(u - W / 2) <= 5)) L3999Prop(p, f, u, w, Props.L3999Pillar, 0, f.Front);
            return;
        }
        for (int w = 4; w <= D - 5; w += 5)
            for (int u = 4; u <= W - 5; u += 5)
                if (Math.Abs(w - wc) > 3 && !(w < 9 && Math.Abs(u - W / 2) <= 5)) L3999Prop(p, f, u, w, Props.L3999Pillar, 0, f.Front);
    }

    /// <summary>Neon tubes up a unit's walls every <paramref name="every"/> blocks, and a glowing strip along their feet (not before a door).</summary>
    private void L3999WallNeon(L3999Planner p, in L3999Frame f, int every)
    {
        for (int w = 0; w < f.D; w++)
            for (int u = 0; u < f.W; u++)
            {
                bool edge = u == 0 || u == f.W - 1 || w == 0 || w == f.D - 1;
                if (!edge) continue;
                ref Tile t = ref L3999F(p, f, u, w);
                if (t.Kind != TileKind.Floor || t.Variant != 0 || L3999HasSlab(t)) continue;
                ArchPier fromWall = w == 0 ? f.Back : w == f.D - 1 ? f.Front : u == 0 ? f.PlusU : f.MinusU;
                var (du, dw) = fromWall == f.Back ? (0, -1) : fromWall == f.Front ? (0, 1) : fromWall == f.PlusU ? (-1, 0) : (1, 0);
                if (L3999F(p, f, u + du, w + dw).Kind != TileKind.Wall) continue; // a door, not a wall
                int along = w == 0 || w == f.D - 1 ? u : w;
                t.Pier = fromWall;
                t.Roof |= along % every == every / 2 ? L3999ArchBit : L3999BaseBit;
            }
    }

    /// <summary>
    /// Bowling lanes: six lanes of maple boards running back from the approach, black gutters between them under neon,
    /// benches at the foul line; a row of skee-ball along one side; a small prize counter by the door.
    /// </summary>
    private void PlanL3999Lanes(L3999Planner p, in L3999Frame f)
    {
        int W = f.W, D = f.D;
        int u0 = (W - 19) / 2;
        for (int w = 8; w <= D - 1; w++)
            for (int k = 0; k < 19; k++)
            {
                ref Tile t = ref L3999F(p, f, u0 + k, w);
                bool gutter = k % 3 == 0;
                t.Floor = gutter || w >= D - 3 ? FloorKind.L3999MarbleBlack : FloorKind.L3999Lanewood;
                if (gutter && w <= D - 4) L3999Tube(p, f, u0 + k, w, f.Back);
            }
        for (int k = 0; k < 6; k++)
        {
            L3999Prop(p, f, u0 + 3 * k + 1, 5, Props.L3999Bench, 0, f.Back);
            L3999Prop(p, f, u0 + 3 * k + 2, 5, Props.L3999Bench, 0, f.Back);
        }
        for (int w = 8; w <= D - 6; w += 2)
        {
            L3999Prop(p, f, W - 1, w, Props.L3999SkeeTarget, 0, f.MinusU);
            L3999Prop(p, f, W - 2, w, Props.L3999SkeeLane, 0, f.MinusU);
        }
        for (int w = 1; w <= 5; w++) L3999Prop(p, f, 0, w, Props.L3999PrizeWall, 0, f.PlusU);
        for (int w = 2; w <= 4; w++) L3999Prop(p, f, 2, w, Props.L3999PrizeCounter, 0, f.PlusU);
        L3999SignAt(p, f, 1, 3, 2, f.PlusU);
        for (int u = 2; u <= W - 3; u += 4) L3999Tube(p, f, u, 3, f.PlusU);
    }

    /// <summary>
    /// A shuttered unit, CLOSED FOR REFIT: the shutters down over its front, the way in through an open doorway from the
    /// service corridor; inside, bare concrete under a few white tubes, sealed supply boxes and spare cabinets in rows.
    /// </summary>
    private void PlanL3999Stores(L3999Planner p, in L3999Frame f)
    {
        ref Rng rng = ref p.Rng;
        for (int w = 6; w <= f.D - 8; w += 6)
            for (int u = 6; u <= f.W - 7; u += 3)
            {
                double r = rng.NextDouble();
                if (r < 0.07)
                {
                    ref Tile t = ref L3999F(p, f, u, w);
                    if (t.Kind == TileKind.Floor && t.Variant == 0) t.SupplyBox = true;
                }
                else if (r < 0.35) L3999Prop(p, f, u, w, Props.L3999DeadCabinet, 0, L3999FromIndex(rng.Range(0, 3)));
            }
    }

    /// <summary>
    /// The Neon Natatorium: violet mosaic pools two to three deep (a deep end four) edged in white with violet LED strips;
    /// a hot tub; loungers in rows; vending machines; neon pillars; 34 °C. One in three has a floor drain in its deep end.
    /// </summary>
    private void PlanL3999Natatorium(L3999Planner p, in L3999Frame f)
    {
        ref Rng rng = ref p.Rng;
        int W = f.W, D = f.D, wc = D / 2;
        int pu0 = 14, pu1 = W - 15, pw0 = wc - 8, pw1 = wc + 7, length = pu1 - pu0 + 1;
        var frame = f;
        void Pool(int u, int w, int depth, FloorKind floor)
        {
            ref Tile t = ref L3999F(p, frame, u, w);
            t.Kind = TileKind.Water;
            t.Depth = (byte)depth;
            t.Floor = floor;
        }
        for (int w = pw0; w <= pw1; w++)
            for (int u = pu0; u <= pu1; u++)
                Pool(u, w, u - pu0 < length * 45 / 100 ? 2 : u > pu1 - 8 ? 4 : 3, FloorKind.L3999PoolViolet);
        for (int w = wc - 2; w <= wc + 1; w++)
            for (int u = 4; u <= 7; u++) Pool(u, w, 1, FloorKind.L3999PoolLilac);
        if (rng.Chance(1 / 3.0)) L3999F(p, f, pu1 - 4, wc).Under = Unders.L3999Drain;
        // The white edges round the water (the coping's LED strip faces the water)
        var toward = new[] { (1, 0, f.PlusU), (-1, 0, f.MinusU), (0, 1, f.Back), (0, -1, f.Front) };
        for (int w = 0; w < D; w++)
            for (int u = 0; u < W; u++)
            {
                ref Tile t = ref L3999F(p, f, u, w);
                if (t.Kind != TileKind.Floor) continue;
                foreach (var (du, dw, d) in toward)
                    if (f.Inside(u + du, w + dw) && L3999F(p, f, u + du, w + dw).Kind == TileKind.Water) { t.Floor = FloorKind.L3999PoolEdge; t.Pier = d; break; }
            }
        for (int u = pu0 + 2; u <= pu1 - 2; u += 3)
        {
            L3999Prop(p, f, u, pw0 - 3, Props.L3999Lounger, 0, f.Back);
            L3999Prop(p, f, u, pw1 + 3, Props.L3999Lounger, 0, f.Front);
        }
        for (int u = 10; u <= W - 10; u += 12)
        {
            L3999Prop(p, f, u, pw0 - 6, Props.L3999Pillar, 0, f.Front);
            L3999Prop(p, f, u, pw1 + 6, Props.L3999Pillar, 0, f.Front);
        }
        L3999Prop(p, f, W / 2 - 5, 0, Props.L3999Vending, 1, f.Back);
        L3999Prop(p, f, W / 2 - 6, 0, Props.L3999Vending, 0, f.Back);
        L3999Prop(p, f, 2, wc - 4, Props.L3999Planter, 0, f.Front);
        L3999Prop(p, f, 2, wc + 3, Props.L3999Planter, 0, f.Front);
        L3999WallNeon(p, f, 8);
    }

    // ================= The Neon Blackout =================

    /// <summary>Whether a Blackout block lies within <paramref name="reach"/> blocks of a block.</summary>
    private bool L3999DarkNear(int bi, int bj, int reach)
    {
        if (L3999BlockFraction(bi, bj) + reach * (double)L3999Block / MacroSize / L3999Radius < 0.65) return false;
        for (int dj = -reach; dj <= reach; dj++)
            for (int di = -reach; di <= reach; di++)
                if (L3999BlackoutBlock(bi + di, bj + dj)) return true;
        return false;
    }

    /// <summary>
    /// The Neon Blackout over a block that is one (everything dead and dark, rotten carpet, debris, the prize counters
    /// abandoned, sealed boxes nobody came back for), and the failing neon within 48 blocks of one: first a tube dead here
    /// and there, then half of them and the carpet going, then the machines dark too.
    /// </summary>
    private void L3999Decay(L3999Planner p, L3999Plan plan, int bi, int bj)
    {
        bool dark = L3999BlackoutBlock(bi, bj);
        var near = new List<(int Di, int Dj)>();
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
                if ((di != 0 || dj != 0) && L3999BlackoutBlock(bi + di, bj + dj)) near.Add((di, dj));
        if (!dark && near.Count == 0) return;
        bool prizeCase = false;
        for (int c = 0; c < L3999Block; c++)
            for (int a = 0; a < L3999Block; a++)
            {
                int drift = 3;
                if (!dark)
                {
                    int best = int.MaxValue;
                    foreach (var (di, dj) in near)
                    {
                        int ex = di < 0 ? a + 1 : di > 0 ? L3999Block - a : 0, ez = dj < 0 ? c + 1 : dj > 0 ? L3999Block - c : 0;
                        best = Math.Min(best, Math.Max(ex, ez));
                    }
                    if (best > 48) continue;
                    drift = best <= 16 ? 3 : best <= 32 ? 2 : 1;
                }
                ref Tile t = ref p.At(a, c);
                ulong h = Hashing.Hash(seed, bi * L3999Block + a, bj * L3999Block + c, SaltL3999Decay);
                double r = Hashing.Unit(h), r2 = Hashing.Unit(Hashing.Mix(h)), r3 = Hashing.Unit(Hashing.Mix(h + 1));
                if (dark) t.Detail |= L3999DarkBit;
                else t.Detail = (byte)((t.Detail & 0x0F) | (drift << 4));
                bool dead = dark || drift == 3 || drift == 2 && r < 0.5 || drift == 1 && r < 0.2;
                if (dead) t.Detail |= L3999DeadBit;
                if (t.Kind == TileKind.Floor && t.Floor is FloorKind.L3999Floor or FloorKind.L3999Galaxy && (dark || drift == 3 || drift == 2 && r2 < 0.5))
                    t.Floor = FloorKind.L3999Rotten;
                if (dead && t.Ceiling == CeilingKind.L3999Fluoro) t.Ceiling = CeilingKind.L3999FluoroOff;
                if (t.Kind != TileKind.Floor) continue;
                bool machine = t.Variant is Props.L3999Cabinet or Props.L3999Themed or Props.L3999Rusted or Props.L3999RacerScreen or Props.L3999DanceScreen
                    or Props.L3999Pinball or Props.L3999Claw or Props.L3999SkeeTarget;
                if (machine && (dark || drift == 3 && r3 < 0.7)) { t.Variant = Props.L3999DeadCabinet; t.Stack = 0; }
                if (dark)
                {
                    // The prize counters were abandoned in the blackout: one is a case of prizes, free to whoever dares
                    if (t.Variant == Props.L3999PrizeCounter)
                    {
                        t.Variant = prizeCase ? (ushort)0 : Props.L3999PrizeCase;
                        prizeCase = true;
                    }
                    if (t.Variant is Props.L3999Vending or Props.L3999Directory or Props.L3999Pillar or Props.L3999RacerSeat or Props.L3999DancePad
                        or Props.L3999SkeeLane) t.Variant = 0;
                    // Only the EXIT signs still glow
                    if (t.Overhead == Overheads.L3999Sign) t.Depth = 7;
                }
                if (t.Variant == 0 && t.Stair == 0 && !t.SupplyBox && (dark && r3 < 0.025 || !dark && drift == 3 && r3 < 0.006))
                {
                    t.Variant = Props.L3999Debris;
                    t.Pier = L3999FromIndex((int)(h & 3));
                }
            }
        if (!dark) return;
        // Three sealed supply boxes nobody came back for
        for (int n = 0, tries = 0; n < 3 && tries < 400; tries++)
        {
            int a = p.Rng.Range(L3999Lo0 + 1, L3999Hi1 - 1), c = p.Rng.Range(L3999Lo0 + 1, L3999Hi1 - 1);
            ref Tile t = ref p.At(a, c);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stair != 0 || t.Zone == (byte)L3999Zone.Service) continue;
            t.SupplyBox = true;
            n++;
        }
    }

    /// <summary>Whether a position is in the Neon Blackout (Level 3999.1).</summary>
    public bool L3999DarkAt(int gx, int gz) => LevelAt(MacroOf(gx), MacroOf(gz)) == Level3999 && L3999IsDark(TileAt(gx, gz));

    // ================= Searches =================

    /// <summary>A unit's middle, in block coordinates.</summary>
    public (int X, int Z) L3999UnitCentre(int bi, int bj, L3999Unit unit) =>
        (L3999OriginX + bi * L3999Block + (unit.A0 + unit.A1) / 2, L3999OriginZ + bj * L3999Block + (unit.C0 + unit.C1) / 2);

    /// <summary>
    /// The nearest units of a kind (or with a mini arcade) round a position, within <paramref name="radius"/> blocks,
    /// nearest first, never in the Blackout: their middles. Block by block.
    /// </summary>
    public List<(int X, int Z)> L3999UnitsNear(int gx, int gz, Func<L3999Unit, bool> want, int radius, int max = 1)
    {
        var found = new List<(int X, int Z, long D)>();
        var (bi0, bj0) = L3999BlockOf(gx, gz);
        int reach = radius / L3999Block + 1;
        for (int bj = bj0 - reach; bj <= bj0 + reach; bj++)
            for (int bi = bi0 - reach; bi <= bi0 + reach; bi++)
            {
                if (L3999BlackoutBlock(bi, bj)) continue;
                var (cx, cz) = L3999BlockCentre(bi, bj);
                if (LevelAt(MacroOf(cx), MacroOf(cz)) != Level3999) continue;
                foreach (L3999Unit unit in L3999UnitsOf(bi, bj))
                {
                    if (!want(unit)) continue;
                    var (x, z) = L3999UnitCentre(bi, bj, unit);
                    if (LevelAt(MacroOf(x), MacroOf(z)) != Level3999 || L3999IsRimCell(MacroOf(x), MacroOf(z))) continue;
                    long d = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                    if (d <= (long)radius * radius) found.Add((x, z, d));
                }
            }
        found.Sort((p, q) => p.D.CompareTo(q.D));
        var result = new List<(int X, int Z)>();
        foreach (var f in found)
        {
            if (result.Count >= max) break;
            result.Add((f.X, f.Z));
        }
        return result;
    }

    /// <summary>
    /// Somewhere afloat in a Neon Natatorium's pool for a key: one past 40% of the way out, picked by the key, then the
    /// nearest natatorium to it. Null if none is found nearby.
    /// </summary>
    public (int X, int Z)? L3999NatatoriumArrival(ulong key)
    {
        ulong h = Hashing.Hash(seed, (int)(key & 0xFFFFFFFF), (int)(key >> 32), SaltL3999Find);
        double angle = Hashing.Unit(h) * Math.PI * 2, r = (0.4 + 0.15 * Hashing.Unit(Hashing.Mix(h))) * L3999Radius;
        int cx = (L3999CentreX + (int)Math.Round(Math.Cos(angle) * r)) * MacroSize, cz = (L3999CentreZ + (int)Math.Round(Math.Sin(angle) * r)) * MacroSize;
        var (bi0, bj0) = L3999BlockOf(cx, cz);
        static bool Afloat(Tile t) => t.Kind == TileKind.Water && t.Depth >= 2 && t.Under == 0 && t.Zone == (byte)L3999Zone.Natatorium && !L3999IsDark(t);
        for (int rr = 0; rr <= 8; rr++)
            for (int bj = bj0 - rr; bj <= bj0 + rr; bj++)
                for (int bi = bi0 - rr; bi <= bi0 + rr; bi++)
                {
                    if (Math.Max(Math.Abs(bi - bi0), Math.Abs(bj - bj0)) != rr || L3999BlackoutBlock(bi, bj)) continue;
                    foreach (L3999Unit unit in L3999UnitsOf(bi, bj))
                    {
                        if (unit.Kind != L3999Kind.Natatorium) continue;
                        int x0 = L3999OriginX + bi * L3999Block + unit.A0, z0 = L3999OriginZ + bj * L3999Block + unit.C0;
                        int x1 = x0 + unit.A1 - unit.A0, z1 = z0 + unit.C1 - unit.C0;
                        var (ux, uz) = L3999UnitCentre(bi, bj, unit);
                        bool Cell(int mx, int mz) => mx * MacroSize + MacroSize > x0 && mx * MacroSize <= x1 && mz * MacroSize + MacroSize > z0 && mz * MacroSize <= z1;
                        if (FindArrival(Level3999, key, null, Cell, Afloat, checkEscape: false, near: (MacroOf(ux), MacroOf(uz))) is { } a) return a;
                    }
                }
        return null;
    }

    /// <summary>
    /// Somewhere in the nearest block of the Neon Blackout to a position, for a key (falling through a rusted cabinet).
    /// Null if there is none within 40 blocks.
    /// </summary>
    public (int X, int Z)? L3999BlackoutArrival(int gx, int gz, ulong key)
    {
        var (bi0, bj0) = L3999BlockOf(gx, gz);
        static bool Dark(Tile t) => IsArrivalSpot(t) && L3999IsDark(t) && !L3999HasSlab(t);
        for (int rr = 0; rr <= 40; rr++)
            for (int bj = bj0 - rr; bj <= bj0 + rr; bj++)
                for (int bi = bi0 - rr; bi <= bi0 + rr; bi++)
                {
                    if (Math.Max(Math.Abs(bi - bi0), Math.Abs(bj - bj0)) != rr || !L3999BlackoutBlock(bi, bj)) continue;
                    var (cx, cz) = L3999BlockCentre(bi, bj);
                    if (LevelAt(MacroOf(cx), MacroOf(cz)) != Level3999) continue;
                    int b0 = bi, b1 = bj;
                    bool Cell(int mx, int mz) => L3999BlockOf(mx * MacroSize + MacroSize / 2, mz * MacroSize + MacroSize / 2) == (b0, b1);
                    if (FindArrival(Level3999, key, null, Cell, Dark, near: (MacroOf(cx), MacroOf(cz))) is { } a) return a;
                }
        return null;
    }

    /// <summary>
    /// A wanderer's camp in one lobby in four (canon's Megacolony: more of them here than anywhere): in the cell holding
    /// the lobby's middle, on a free tile near it.
    /// </summary>
    private (int X, int Z)? L3999WandererSite(int mx, int mz)
    {
        int gx = mx * MacroSize + MacroSize / 2, gz = mz * MacroSize + MacroSize / 2;
        var (bi, bj) = L3999BlockOf(gx, gz);
        if (L3999BlackoutBlock(bi, bj) || L3999IsRimCell(mx, mz)) return null;
        foreach (L3999Unit unit in L3999UnitsOf(bi, bj))
        {
            if (unit.Kind != L3999Kind.Lobby) continue;
            var (ux, uz) = L3999UnitCentre(bi, bj, unit);
            if (MacroOf(ux) != mx || MacroOf(uz) != mz) continue;
            if (Hashing.Unit(Hashing.Hash(seed, ux, uz, SaltL3999Wanderer)) >= 0.25) return null;
            for (int r = 0; r <= 8; r++)
                for (int dz = -r; dz <= r; dz++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                        int x = ux + dx, z = uz + dz;
                        if (MacroOf(x) == mx && MacroOf(z) == mz && IsEntitySpot(x, z) && TileAt(x, z).Variant == 0) return (x, z);
                    }
        }
        return null;
    }

    /// <summary>Which of the level's props (<see cref="Props.L3999First"/>-<see cref="Props.L3999Last"/>) people walk through.</summary>
    private static bool L3999WalkThrough(ushort variant) => variant is Props.L3999Walkway or Props.L3999Escalator;

    // ================= Air =================

    /// <summary>24 °C, constant; the Natatorium 34 °C; the Blackout 14 °C.</summary>
    private float L3999Temperature(int x, int y, int z, int floorY)
    {
        Tile t = TileAt(x, z);
        if (L3999IsDark(t)) return 14f;
        if (t.Zone == (byte)L3999Zone.Natatorium) return 34f;
        return LevelTemperatures[Level3999];
    }

    /// <summary>Reality Stability: a heavenly respite (1.3; lobbies 1.4, the Natatorium 1.35), failing with the neon, 0.15 in the Blackout.</summary>
    private float L3999Stability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        if (L3999IsDark(t)) return 0.15f;
        int fail = L3999Drift(t);
        if (fail > 0) return 1.3f - 0.3f * fail;
        return t.Zone switch
        {
            (byte)L3999Zone.Lobby => 1.4f,
            (byte)L3999Zone.Natatorium => 1.35f,
            _ => 1.3f + 0.03f * drift,
        };
    }
}
