using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// The End (kept as level 16, <see cref="TheEnd"/>, shown as "End"): a library that goes on forever and looks like the
/// way out. A closed-down bookstore with no books: empty maple gondola shelving, tapered slatwall towers, sage columns
/// clad in slatwall, a curved service desk with an old computer, and over it bronze letters reading THE END, under a
/// drop ceiling full of fluorescent troffers. It lies far to the north-west, a region only thresholds reach. The design
/// is in docs/design/new-levels/end-plan.md (after Wikidot's Level 601 and Fandom's The End).
///
/// The level is planned in departments of <see cref="EndDept"/> blocks a side (two cells), each from its own id and
/// cached (<see cref="PlanCache{T}"/>). Along every department line runs the store's racetrack aisle, a band of navy
/// patterned carpet five wide that wanders a little, computed from coordinates so it is seamless; one stretch in four
/// is jammed by furniture that has grown into itself, so the long views end. Each department is one of: stacks, open
/// floor, a service desk under a lettered soffit, a reading room, a two-storey atrium round a void, a stockroom (with
/// the EXIT doors and the vents), a collapse, a fake reality (a familiar place the library blends into), or half of a
/// long aisle that repeats exactly every 32 blocks (the loop). The department round the region's centre is the central
/// hall: THE END IS NEAR over a round desk, an EXIT door in each corner.
///
/// Heights (rel above The End's floor, <see cref="WorldGeometry.EndDrop"/> below the others'): ordinary rooms have
/// their ceiling at <see cref="Tile.Height"/> 5; a long aisle's at 6; an atrium's at 10, its mezzanine deck at rel
/// <see cref="EndDeckRel"/>. Fake realities' cores have the height of the place they imitate (4).
///
/// Tile fields on The End's tiles: Zone 0 library, 1 central hall, 2 stockroom, 3 collapse, 4 a fake reality's blend,
/// 5 its core; Detail the fake reality's kind (<see cref="EndFake"/>) on zones 4 and 5; Depth 1 where the ceiling is
/// the imitated place's; Stack the prop's kind; Pier the way a prop or door faces.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Whether The End's entrances in other levels are laid out (always, but for the harness's endhash check).</summary>
    internal static bool EndEntrances = true;

    /// <summary>Hash salts 0x1600-0x16BF are this level's.</summary>
    private const ulong SaltEndShape = 0x1601, SaltEndDept = 0x1602, SaltEndRunway = 0x1603, SaltEndJam = 0x1604, SaltEndFake = 0x1605,
        SaltEndPlan = 0x1606, SaltEndLight = 0x1607, SaltEndScene = 0x1608, SaltEndPartition = 0x160A;

    /// <summary>Size of a department, the piece the level is planned in.</summary>
    public const int EndDept = 64;

    /// <summary>Where a department's own floor begins and ends, inside the margins and the runway along its edges.</summary>
    private const int EndInner0 = 6, EndInner1 = 57;

    /// <summary>Ceiling heights: ordinary rooms, the long aisles, the atriums; the atrium's deck; the pendants under its ceiling.</summary>
    public const int EndCeilingHeight = 5, EndAisleHeight = 6, EndAtriumHeight = 10, EndDeckRel = 5, EndPendantRel = 9;

    /// <summary>The period a long aisle repeats with, and the stretch of it that loops (pair-local, along the aisle).</summary>
    public const int EndLoopPeriod = 32, EndLoopStart = 8, EndLoopEnd = 120;

    /// <summary>The kinds of department.</summary>
    public enum EndKind : byte { Stacks, Open, Desk, Reading, Atrium, Stock, LongLeft, LongRight, Collapse, Fake, Central }

    /// <summary>The kinds of fake reality (in <see cref="Tile.Detail"/>).</summary>
    public enum EndFake : byte { None, Lobby, Office, Hotel, House, Snow, Home }

    /// <summary>The letters the bronze signs are spelled in (<see cref="Tile.Stack"/> on a lettered soffit or wall): 0 is a blank.</summary>
    public static readonly string EndLetters = " thendisar";

    // ================= Where it is =================

    /// <summary>The region's centre, in macro cells: far out to the north-west, a quarter further out than the city.</summary>
    private int EndCentreX => spawnMacroX - DiagonalReach;
    private int EndCentreZ => spawnMacroZ - DiagonalReach;

    /// <summary>The region's radius in macro cells: endless to anyone in it.</summary>
    private int EndRadius => Math.Max(60, spawnMacroX / 40);

    /// <summary>The block the level's departments count from: department (0, 0) is the central hall.</summary>
    public int EndOriginX => EndCentreX * MacroSize - EndDept / 2 + MacroSize / 2;
    public int EndOriginZ => EndCentreZ * MacroSize - EndDept / 2 + MacroSize / 2;

    private bool InEnd(double mx, double mz) => InRoundRegion(mx, mz, EndCentreX, EndCentreZ, EndRadius, SaltEndShape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive: within a few departments of the central hall.</summary>
    private (int Mx, int Mz) EndArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, r = Math.Sqrt(Hashing.Unit(Hashing.Mix(h))) * 7;
        return (EndCentreX + (int)Math.Round(Math.Cos(angle) * r), EndCentreZ + (int)Math.Round(Math.Sin(angle) * r));
    }

    /// <summary>Arriving: on the library's carpet or the runway, in the open, never in a fake reality, an atrium's void or a long aisle.</summary>
    private static bool IsEndArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Zone is 0 or 1 && t.Overhead == 0 && t.Height == EndCeilingHeight
        && t.Floor is FloorKind.EndCarpet or FloorKind.EndCarpetWorn or FloorKind.EndCarpetDusty or FloorKind.EndRunway;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double EndArrivalHeight(in Tile t, double stand) => stand;

    /// <summary>An EXIT door of The End's (the way back for whoever arrives beside it).</summary>
    public static bool IsEndExitDoor(Tile t) => t.Kind == TileKind.Door && t.Pattern == WallPattern.EndExit && t.Level == TheEnd;

    // ================= Departments =================

    /// <summary>The department a block position lies in.</summary>
    public (int Di, int Dj) EndDeptOf(int gx, int gz) => (Hashing.FloorDiv(gx - EndOriginX, EndDept), Hashing.FloorDiv(gz - EndOriginZ, EndDept));

    /// <summary>How far out a department lies, in departments from the central hall.</summary>
    private static double EndDeptDistance(int di, int dj) => Math.Sqrt((double)di * di + (double)dj * dj);

    private EndKind EndRoll(int di, int dj)
    {
        double u = Hashing.Unit(Hashing.Hash(seed, di, dj, SaltEndDept));
        return u switch
        {
            < 0.34 => EndKind.Stacks,
            < 0.54 => EndKind.Open,
            < 0.62 => EndKind.Desk,
            < 0.72 => EndKind.Reading,
            < 0.79 => EndKind.Atrium,
            < 0.87 => EndKind.Stock,
            < 0.91 => EndKind.LongLeft,
            < 0.95 => EndKind.Collapse,
            _ => EndKind.Stacks,
        };
    }

    /// <summary>The fake reality a department holds, if it is one: about one department in twenty, from six departments out, never two close together.</summary>
    public EndFake EndFakeAt(int di, int dj)
    {
        int sx = Hashing.FloorDiv(di, 3), sz = Hashing.FloorDiv(dj, 3);
        ulong h = Hashing.Hash(seed, sx, sz, SaltEndFake);
        if (Hashing.Unit(h) >= 0.45) return EndFake.None;
        int ci = sx * 3 + (int)(Hashing.Mix(h) % 3), cj = sz * 3 + (int)(Hashing.Mix(h + 1) % 3);
        if (ci != di || cj != dj || EndDeptDistance(di, dj) < 6) return EndFake.None;
        double u = Hashing.Unit(Hashing.Mix(h + 2));
        return u switch
        {
            < 0.30 => EndFake.Lobby,
            < 0.45 => EndFake.Office,
            < 0.60 => EndFake.Hotel,
            < 0.75 => EndFake.House,
            < 0.90 => EndFake.Snow,
            _ => EndFake.Home,
        };
    }

    /// <summary>Whether a fake reality's door opens onto somewhere real (three in five do; the Snowfield and Home have none).</summary>
    public bool EndFakeWorks(int di, int dj, EndFake kind) =>
        kind is EndFake.Lobby or EndFake.Office or EndFake.Hotel or EndFake.House && Hashing.Unit(Hashing.Hash(seed, di, dj, SaltEndFake + 7)) < 0.6;

    /// <summary>What a department is.</summary>
    public EndKind EndKindAt(int di, int dj)
    {
        if (di == 0 && dj == 0) return EndKind.Central;
        if (EndFakeAt(di, dj) != EndFake.None) return EndKind.Fake;
        bool Plain(int i, int j) => !(i == 0 && j == 0) && EndFakeAt(i, j) == EndFake.None;
        // A long aisle takes two departments side by side, the even one and the next
        if (Hashing.Mod(di, 2) == 0 && EndRoll(di, dj) == EndKind.LongLeft && Plain(di + 1, dj)) return EndKind.LongLeft;
        if (Hashing.Mod(di, 2) == 1 && EndRoll(di - 1, dj) == EndKind.LongLeft && Plain(di - 1, dj)) return EndKind.LongRight;
        EndKind kind = EndRoll(di, dj);
        if (kind == EndKind.LongLeft) return EndKind.Stacks;
        if (kind == EndKind.Collapse && EndDeptDistance(di, dj) < 5) return EndKind.Stacks;
        return kind;
    }

    /// <summary>The scene a department's distortions always show (see EndSystem): the level a wall leads to during one, or -1 (the snow).</summary>
    public int EndDistortionScene(int di, int dj)
    {
        double u = Hashing.Unit(Hashing.Hash(seed, di, dj, SaltEndScene));
        return u switch { < 0.35 => 0, < 0.50 => 4, < 0.65 => 9, < 0.75 => Poolrooms, < 0.80 => Motion, _ => -1 };
    }

    /// <summary>The middle of a department, in block coordinates.</summary>
    public (int X, int Z) EndDeptCentre(int di, int dj) => (EndOriginX + di * EndDept + EndDept / 2, EndOriginZ + dj * EndDept + EndDept / 2);

    // ================= The runway =================

    /// <summary>How far a runway line's middle lies off its line at a point along it.</summary>
    private int EndRunwayOffset(int axis, int line, int along)
    {
        ulong h = Hashing.Hash(seed, axis, line, SaltEndRunway);
        int amplitude = (int)(Hashing.Unit(h) * 4);
        double period = 30 + 20 * Hashing.Unit(Hashing.Mix(h)), phase = Hashing.Unit(Hashing.Mix(h + 1)) * Math.PI * 2;
        return (int)Math.Round(amplitude * Math.Sin(along / period + phase));
    }

    /// <summary>
    /// What the racetrack aisle does at a block position: 0 nothing, 1 runway carpet, 2 a jam of furniture across it.
    /// Axis 0 is a line of constant x (the runway running north-south), axis 1 one of constant z.
    /// </summary>
    private int EndRunwayAt(int gx, int gz, out ulong jamHash)
    {
        jamHash = 0;
        int u = gx - EndOriginX, v = gz - EndOriginZ;
        int result = 0;
        for (int axis = 0; axis < 2; axis++)
        {
            int across = axis == 0 ? u : v, along = axis == 0 ? v : u;
            int line = (int)Math.Round(across / (double)EndDept);
            int fromLine = across - line * EndDept;
            if (fromLine < -6 || fromLine > 5) continue;
            int seg = Hashing.FloorDiv(along, EndDept), local = along - seg * EndDept;
            // A long aisle crosses its own middle line: no runway there
            if (axis == 0 && local is >= EndInner0 and <= EndInner1)
            {
                int left = line - 1;
                if (Hashing.Mod(left, 2) == 0 && EndKindAt(left, seg) == EndKind.LongLeft) continue;
            }
            // A jam: furniture grown together right across the band, two deep
            if (local is 30 or 31 && local >= EndInner0)
            {
                ulong h = Hashing.Hash(seed, axis * 100003 + line, seg, SaltEndJam);
                static bool Jammable(EndKind k) => k is not (EndKind.Central or EndKind.LongLeft or EndKind.LongRight);
                if (Hashing.Unit(h) < 0.25 && Jammable(EndKindAt(axis == 0 ? line : seg, axis == 0 ? seg : line))
                    && Jammable(EndKindAt(axis == 0 ? line - 1 : seg, axis == 0 ? seg : line - 1)))
                {
                    jamHash = Hashing.Hash(seed, gx, gz, SaltEndJam + 1);
                    return 2;
                }
            }
            int off = fromLine - EndRunwayOffset(axis, line, along);
            if (off is >= -2 and <= 2) result = 1;
        }
        return result;
    }

    // ================= Cells =================

    /// <summary>The wall line on a cell's west or north side, between two cells of the level: open, the plans are laid over it.</summary>
    private Edge EndEdge(int mx, int mz, bool west) => new() { Pattern = WallPattern.EndWall };

    private void BuildLevelEnd(Builder b, int mx, int mz)
    {
        // The rim: the store's back wall, solid, all the way round
        bool rim = false;
        for (int dz = -1; dz <= 1 && !rim; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != TheEnd) { rim = true; break; }

        if (rim)
        {
            for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i] = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.EndWall, Height = EndCeilingHeight };
            return;
        }
        // A cell is half a department across, but the departments are offset half a cell from the cells, so a cell
        // takes in parts of up to four of them: each one's plan is fetched once
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        var (di0, dj0) = EndDeptOf(x0, z0);
        var plans = new Tile[4][];
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int gx = x0 + lx, gz = z0 + lz;
                var (di, dj) = EndDeptOf(gx, gz);
                int k = (dj - dj0) * 2 + di - di0;
                b.At(lx, lz) = EndTileAt(gx, gz, di, dj, plans[k] ??= EndPlan(di, dj));
            }
    }

    /// <summary>The planned tile at a block position (department plan, then the runway over it), in department di, dj, whose plan is given.</summary>
    private Tile EndTileAt(int gx, int gz, int di, int dj, Tile[] plan)
    {
        int a = gx - EndOriginX - di * EndDept, c = gz - EndOriginZ - dj * EndDept;
        Tile t = plan[c * EndDept + a];
        int runway = EndRunwayAt(gx, gz, out ulong jam);
        if (runway == 0) return t;
        if (t.Kind != TileKind.Floor || t.Zone >= 4) t = EndFloorTile(a, c, SaltEndLight, di, dj);
        if (runway == 1)
        {
            t.Floor = FloorKind.EndRunway;
            t.Variant = 0;
            t.Stack = 0;
            t.Overhead = 0;
            t.Height = EndCeilingHeight;
            return t;
        }
        // The jam: shelving, a desk, a trolley and chairs converged into one another
        double u = Hashing.Unit(jam);
        t.Floor = FloorKind.EndCarpetDusty;
        (t.Variant, t.Stack) = u switch
        {
            < 0.45 => (Props.EndShelf, (byte)(Hashing.Mix(jam) % 3 == 0 ? 4 : 0)),
            < 0.60 => (Props.EndDesk, (byte)0),
            < 0.75 => (Props.EndStock, (byte)1),
            < 0.88 => (Props.EndFurniture, (byte)2),
            _ => (Props.EndEndcap, (byte)0),
        };
        t.Pier = (ArchPier)(Hashing.Mix(jam + 3) % 4);
        return t;
    }

    /// <summary>A plain floor tile of the library: grey-green carpet under the drop ceiling, a troffer on the four-block grid.</summary>
    private Tile EndFloorTile(int a, int c, ulong salt, int di, int dj, bool dark = false)
    {
        var t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.EndCarpet, Height = EndCeilingHeight, Pattern = WallPattern.EndWall };
        if ((a & 3) == 1 && (c & 3) == 1)
        {
            double u = Hashing.Unit(Hashing.Hash(seed, di * EndDept + a, dj * EndDept + c, salt));
            t.Ceiling = dark ? CeilingKind.LightOff : u switch
            {
                < 0.06 => CeilingKind.LightOff,
                < 0.09 => CeilingKind.LightFlicker,
                < 0.60 => CeilingKind.LightOn,
                _ => CeilingKind.LightLit,
            };
        }
        return t;
    }

    // ================= Plans =================

    private PlanCache<Tile[]> endPlans;

    /// <summary>A department's tiles, 64 by 64, row by row (index z * 64 + x, local to the department).</summary>
    private Tile[] EndPlan(int di, int dj) => (endPlans ??= new PlanCache<Tile[]>(24, PlanEndDepartment)).Get(di, dj);

    /// <summary>Helpers over one department's tiles while it is planned (or two, for a long aisle).</summary>
    private sealed class EndPlanner
    {
        public readonly int W, H;
        public readonly Tile[] T;
        public Rng Rng;
        public int Di, Dj;
        public byte Zone;
        public bool Dark;
        /// <summary>Whether the layout is version 5 or later (partition walls, the EXIT vestibules).</summary>
        public bool V5;

        public EndPlanner(int w, int h)
        {
            W = w;
            H = h;
            T = new Tile[w * h];
        }

        public bool In(int a, int c) => a >= 0 && c >= 0 && a < W && c < H;
        public ref Tile At(int a, int c) => ref T[c * W + a];
        public bool IsFloor(int a, int c) => In(a, c) && At(a, c).Kind == TileKind.Floor;
        public bool IsEmptyFloor(int a, int c) => IsFloor(a, c) && At(a, c).Variant == 0;

        public void Prop(int a, int c, ushort prop, int stack = 0, ArchPier pier = ArchPier.North)
        {
            if (!In(a, c)) return;
            ref Tile t = ref At(a, c);
            if (t.Kind != TileKind.Floor) return;
            t.Variant = prop;
            t.Stack = (byte)stack;
            t.Pier = pier;
        }

        public void Wall(int a, int c, WallPattern pattern = WallPattern.EndWall)
        {
            if (!In(a, c)) return;
            ref Tile t = ref At(a, c);
            byte height = t.Height;
            t = new Tile { Kind = TileKind.Wall, Pattern = pattern, Height = height == 0 ? (byte)EndCeilingHeight : height, Zone = Zone };
        }

        public void Clear(int a, int c)
        {
            if (!In(a, c)) return;
            ref Tile t = ref At(a, c);
            if (t.Kind != TileKind.Floor) { t.Kind = TileKind.Floor; t.Pattern = WallPattern.EndWall; }
            t.Variant = 0;
            t.Stack = 0;
        }
    }

    private Tile[] PlanEndDepartment(int di, int dj)
    {
        EndKind kind = EndKindAt(di, dj);
        if (kind is EndKind.LongLeft or EndKind.LongRight)
        {
            // A long aisle is planned whole, across both departments, and each takes its half
            int left = kind == EndKind.LongLeft ? di : di - 1;
            Tile[] pair = PlanEndLongAisle(left, dj);
            var half = new Tile[EndDept * EndDept];
            int offset = kind == EndKind.LongLeft ? 0 : EndDept;
            for (int c = 0; c < EndDept; c++)
                Array.Copy(pair, c * EndDept * 2 + offset, half, c * EndDept, EndDept);
            return half;
        }

        var p = NewEndPlanner(EndDept, EndDept, di, dj, kind == EndKind.Collapse);
        switch (kind)
        {
            case EndKind.Central: PlanEndCentral(p); break;
            case EndKind.Open: PlanEndOpen(p); break;
            case EndKind.Desk: PlanEndDesk(p); break;
            case EndKind.Reading: PlanEndReading(p); break;
            case EndKind.Atrium: PlanEndAtrium(p); break;
            case EndKind.Stock: PlanEndStock(p); break;
            case EndKind.Collapse: PlanEndCollapse(p); break;
            case EndKind.Fake: PlanEndFake(p, EndFakeAt(di, dj)); break;
            default:
                PlanEndStacks(p, EndInner0, EndInner0, EndInner1, EndInner1, null, p.Rng.Chance(0.5));
                PlanEndColumns(p, 16, null);
                break;
        }
        if (p.V5 && kind is EndKind.Stacks or EndKind.Open) PlanEndPartitions(p);
        return p.T;
    }

    /// <summary>
    /// From layout version 5: the store's painted walls (base, ghost marks, yellow band, cream above) along about one
    /// department border in three, on the side of a stacks or open-floor department, as in the photographs the level is
    /// built on, so the floor reads as a store's departments and the long views end. A wall stands one block thick on the
    /// department's inner edge, out of the runway, broken by openings three wide every 8 to 12 blocks; ghost marks show
    /// where fixtures once hung, a run now and then has a poster, and a clear way runs along its inner face, so no
    /// shelving closes off a corner behind it.
    /// </summary>
    private void PlanEndPartitions(EndPlanner p)
    {
        for (int side = 0; side < 4; side++)
            if (EndPartitionAt(p.Di, p.Dj, side, out ulong h)) PlanEndPartition(p, side, new Rng(Hashing.Mix(h + 2)));
        // A poster or ghost mark only where it looks onto the floor: a wall's at a corner, or a column's that now looks
        // onto a wall, turns to the floor or goes
        for (int c = 0; c < p.H; c++)
            for (int a = 0; a < p.W; a++)
            {
                ref Tile t = ref p.At(a, c);
                if (t.Kind != TileKind.Wall || t.Variant is not (>= Decor.EndPoster and < Decor.EndPoster + 4 or Decor.EndGhost)) continue;
                var (dx, dz) = Step(t.Pier);
                if (p.IsFloor(a + dx, c + dz)) continue;
                ushort decor = t.Variant;
                t.Variant = 0;
                foreach (ArchPier side in new[] { ArchPier.North, ArchPier.South, ArchPier.West, ArchPier.East })
                {
                    (dx, dz) = Step(side);
                    if (p.IsFloor(a + dx, c + dz)) { t.Variant = decor; t.Pier = side; break; }
                }
            }
    }

    /// <summary>
    /// Whether a department has a partition wall along a side (0 west, 1 east, 2 north, 3 south), from layout version 5
    /// (see <see cref="PlanEndPartitions"/>); <paramref name="h"/> is the border's hash.
    /// </summary>
    public bool EndPartitionAt(int di, int dj, int side, out ulong h)
    {
        // The border, as the runway counts it: axis 0 a line of constant x (west 0, east 1), axis 1 one of constant z
        // (north 2, south 3); either department's plan rolls the same wall for it
        int axis = side < 2 ? 0 : 1;
        int line = side switch { 0 => di, 1 => di + 1, 2 => dj, _ => dj + 1 };
        h = Hashing.Hash(seed, axis * 100003 + line, axis == 0 ? dj : di, SaltEndPartition);
        if (Version < 5 || EndKindAt(di, dj) is not (EndKind.Stacks or EndKind.Open) || Hashing.Unit(h) >= 0.45) return false;
        // It stands on this side if the other is no stacks or open floor; if both are, the hash picks
        var (oi, oj) = side switch { 0 => (di - 1, dj), 1 => (di + 1, dj), 2 => (di, dj - 1), _ => (di, dj + 1) };
        bool other = EndKindAt(oi, oj) is EndKind.Stacks or EndKind.Open;
        return !other || ((Hashing.Mix(h) & 1) == 0) == (side is 1 or 3);
    }

    /// <summary>One partition wall along a department's side (0 west, 1 east, 2 north, 3 south); see <see cref="PlanEndPartitions"/>.</summary>
    private static void PlanEndPartition(EndPlanner p, int side, Rng rng)
    {
        int fixedAt = side is 0 or 2 ? EndInner0 : EndInner1, inward = side is 0 or 2 ? 1 : -1;
        ArchPier facing = side switch { 0 => ArchPier.East, 1 => ArchPier.West, 2 => ArchPier.South, _ => ArchPier.North };
        (int A, int C) At(int along, int off) => side < 2 ? (fixedAt + off, along) : (along, fixedAt + off);
        void ClearAt(int along, int off)
        {
            var (a, c) = At(along, off);
            if (!p.IsFloor(a, c)) return; // a column stays
            ref Tile t = ref p.At(a, c);
            t.Variant = 0;
            t.Stack = 0;
        }
        // The clear way inside it
        for (int k = EndInner0; k <= EndInner1; k++) ClearAt(k, inward);
        for (int k = EndInner0; k <= EndInner1;)
        {
            int end = Math.Min(k + rng.Range(5, 9) - 1, EndInner1);
            if (end > k)
            {
                int poster = rng.Chance(0.5) ? rng.Range(k, end) : -1;
                for (int s = k; s <= end; s++)
                {
                    var (a, c) = At(s, 0);
                    if (!p.IsFloor(a, c)) continue; // a column, or a corner already walled
                    ref Tile t = ref p.At(a, c);
                    byte height = t.Height;
                    t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.EndWall, Height = height == 0 ? (byte)EndCeilingHeight : height };
                    if (s == poster) { t.Variant = (ushort)(Decor.EndPoster + rng.Range(0, 2)); t.Pier = facing; }
                    else if (rng.Chance(0.3)) { t.Variant = Decor.EndGhost; t.Pier = facing; }
                }
            }
            // An opening three wide, clear either side
            for (int s = end + 1; s <= Math.Min(end + 3, EndInner1); s++)
            {
                ClearAt(s, 0);
                ClearAt(s, -inward);
            }
            k = end + 4;
        }
    }

    private EndPlanner NewEndPlanner(int w, int h, int di, int dj, bool dark)
    {
        var p = new EndPlanner(w, h) { Rng = new Rng(Hashing.Hash(seed, di, dj, SaltEndPlan)), Di = di, Dj = dj, Dark = dark, V5 = Version >= 5 };
        for (int c = 0; c < h; c++)
            for (int a = 0; a < w; a++)
                p.At(a, c) = EndFloorTile(a, c, SaltEndLight, di, dj, dark);
        return p;
    }

    /// <summary>Which part of a planned area a stacks or column pass may use (null: all of it).</summary>
    private delegate bool EndArea(int a, int c);

    /// <summary>
    /// Rows of double-faced gondola shelving, 2 high, one tile thick with aisles two wide between them, in runs of 4 to
    /// 10 with cross-gaps; an end panel or a slatwall tower at each end. Now and then a run converges: half way along it
    /// steps across into the next aisle. A few shelves hold books, some are dusty, a few lean and will fall.
    /// </summary>
    private static void PlanEndStacks(EndPlanner p, int a0, int c0, int a1, int c1, EndArea allowed, bool alongA, double keep = 1.0)
    {
        int across0 = alongA ? c0 : a0, across1 = alongA ? c1 : a1, along0 = alongA ? a0 : c0, along1 = alongA ? a1 : c1;
        ref Rng rng = ref p.Rng;
        for (int row = across0 + 1; row <= across1 - 1; row += 3)
        {
            if (keep < 1 && !rng.Chance(keep)) continue;
            int s = along0 + rng.Range(0, 2);
            while (s <= along1 - 3)
            {
                int length = rng.Range(4, 10), end = Math.Min(s + length - 1, along1);
                bool converge = rng.Chance(0.1);
                ArchPier face = rng.Chance(0.5) ? (alongA ? ArchPier.North : ArchPier.West) : (alongA ? ArchPier.South : ArchPier.East);
                for (int k = s; k <= end; k++)
                {
                    int r = row + (converge && k > (s + end) / 2 ? 1 : 0);
                    int a = alongA ? k : r, c = alongA ? r : k;
                    if (!p.In(a, c) || allowed != null && !allowed(a, c) || !p.IsFloor(a, c)) continue;
                    bool first = k == s, last = k == end;
                    if (first || last)
                    {
                        if (rng.Chance(0.35)) p.Prop(a, c, Props.EndEndcap, rng.Chance(0.3) ? 1 : 0);
                        else
                        {
                            ArchPier outward = alongA ? (first ? ArchPier.West : ArchPier.East) : (first ? ArchPier.North : ArchPier.South);
                            p.Prop(a, c, Props.EndShelf, 3, outward);
                        }
                        continue;
                    }
                    double u = rng.NextDouble();
                    int kind = u < 1 / 30.0 ? 1 : u < 1 / 30.0 + 1 / 8.0 ? 2 : u < 1 / 30.0 + 1 / 8.0 + 1 / 25.0 ? 4 : 0;
                    p.Prop(a, c, Props.EndShelf, kind, face);
                }
                s = end + 3;
            }
        }
    }

    /// <summary>Square columns on a grid, sage or slate over slatwall, with THE END posters on some faces.</summary>
    private static void PlanEndColumns(EndPlanner p, int spacing, EndArea allowed, double posters = 0.4)
    {
        var pattern = p.Rng.Chance(0.6) ? WallPattern.EndColumn : WallPattern.EndColumnSlate;
        for (int c = spacing / 2; c < p.H; c += spacing)
            for (int a = spacing / 2; a < p.W; a += spacing)
            {
                if (a < EndInner0 || c < EndInner0 || a > p.W - 1 - (EndDept - 1 - EndInner1) || c > EndInner1) continue;
                if (allowed != null && !allowed(a, c) || !p.IsFloor(a, c)) continue;
                p.Wall(a, c, pattern);
                if (p.Rng.Chance(posters)) EndPoster(p, a, c);
            }
    }

    private static void EndPoster(EndPlanner p, int a, int c)
    {
        ref Tile t = ref p.At(a, c);
        t.Variant = (ushort)(Decor.EndPoster + p.Rng.Range(0, 3));
        t.Pier = (ArchPier)p.Rng.Range(0, 3);
    }

    /// <summary>Open floor: the photo. Columns, slatwall towers, display tables, short runs of shelving, things in plastic, a field of blue carpet.</summary>
    private static void PlanEndOpen(EndPlanner p)
    {
        ref Rng rng = ref p.Rng;
        // The field of navy carpet in one corner
        int fa = rng.Chance(0.5) ? 10 : 36, fc = rng.Chance(0.5) ? 10 : 36;
        for (int c = fc; c < fc + 18; c++)
            for (int a = fa; a < fa + 18; a++)
                p.At(a, c).Floor = FloorKind.EndRunway;
        PlanEndColumns(p, 16, null, 0.6);
        for (int c = EndInner0 + 1; c < EndInner1; c += 6)
            for (int a = EndInner0 + 1; a < EndInner1; a += 6)
            {
                int x = a + rng.Range(0, 4), z = c + rng.Range(0, 4);
                if (!p.IsEmptyFloor(x, z)) continue;
                double u = rng.NextDouble();
                if (u < 0.30) p.Prop(x, z, Props.EndEndcap, rng.Chance(0.3) ? 1 : 0);
                else if (u < 0.40) p.Prop(x, z, Props.EndFurniture, 6, (ArchPier)rng.Range(0, 3));
                else if (u < 0.48)
                {
                    // A short run of shelving, two or three long
                    bool alongA = rng.Chance(0.5);
                    var face = alongA ? ArchPier.North : ArchPier.East;
                    for (int k = 0; k < rng.Range(2, 3); k++)
                        if (p.IsEmptyFloor(x + (alongA ? k : 0), z + (alongA ? 0 : k)))
                            p.Prop(x + (alongA ? k : 0), z + (alongA ? 0 : k), Props.EndShelf, rng.Chance(0.1) ? 1 : 0, face);
                }
                else if (u < 0.52) p.Prop(x, z, Props.EndFurniture, 3, (ArchPier)rng.Range(0, 3));
                else if (u < 0.54) p.Prop(x, z, Props.EndStock, 2, (ArchPier)rng.Range(0, 3));
                else if (u < 0.58) p.Prop(x, z, Props.EndFurniture, 2, (ArchPier)rng.Range(0, 3));
            }
    }

    /// <summary>
    /// A service desk under a soffit lettered THE END: a C-shaped desk round a staff floor with a computer on its front,
    /// columns with posters at the soffit's corners, stacks all round.
    /// </summary>
    private static void PlanEndDesk(EndPlanner p)
    {
        bool InZone(int a, int c) => a >= 18 && a <= 46 && c >= 20 && c <= 44;
        PlanEndStacks(p, EndInner0, EndInner0, EndInner1, EndInner1, (a, c) => !InZone(a, c), p.Rng.Chance(0.5));
        PlanEndColumns(p, 16, (a, c) => !InZone(a, c));
        PlanEndSoffit(p, 22, 24, 42, 40, "the end", 0);
        foreach (var (a, c) in new[] { (21, 23), (43, 23), (21, 41), (43, 41) })
        {
            p.Wall(a, c, WallPattern.EndColumn);
            p.At(a, c).Variant = Decor.EndPoster;
            p.At(a, c).Pier = c < 30 ? ArchPier.South : ArchPier.North;
        }
        PlanEndServiceDesk(p, 28, 30, 36, 35, ArchPier.South, terminals: new[] { 30, 34 }, central: false);
    }

    /// <summary>
    /// A soffit over a rectangle (a bulkhead at rel 4), with words in bronze letters along its faces: on the side
    /// facing <paramref name="sides"/> (0: south only; 1: all four).
    /// </summary>
    private static void PlanEndSoffit(EndPlanner p, int a0, int c0, int a1, int c1, string words, int sides)
    {
        for (int c = c0; c <= c1; c++)
            for (int a = a0; a <= a1; a++)
                if (p.IsFloor(a, c)) p.At(a, c).Overhead = Overheads.EndSoffit;

        void Spell(int length, Func<int, (int A, int C)> at, ArchPier facing)
        {
            int start = (length - words.Length) / 2;
            for (int i = 0; i < words.Length; i++)
            {
                var (a, c) = at(start + i);
                if (!p.IsFloor(a, c)) continue;
                ref Tile t = ref p.At(a, c);
                t.Overhead = Overheads.EndSoffitLetter;
                int letter = EndLetters.IndexOf(words[i]);
                t.Stack = (byte)Math.Max(0, letter);
                t.Pier = facing;
            }
        }
        Spell(a1 - a0 + 1, i => (a0 + i, c1), ArchPier.South);
        if (sides == 1)
        {
            Spell(a1 - a0 + 1, i => (a1 - i, c0), ArchPier.North);
            Spell(c1 - c0 + 1, i => (a0, c0 + i), ArchPier.West);
            Spell(c1 - c0 + 1, i => (a1, c1 - i), ArchPier.East);
        }
    }

    /// <summary>
    /// A service desk round a rectangle: the front (toward <paramref name="front"/>) straight, rounded at the corners, the
    /// sides straight, the back two ends and a gate; computers on the front at the given offsets.
    /// </summary>
    private static void PlanEndServiceDesk(EndPlanner p, int a0, int c0, int a1, int c1, ArchPier front, int[] terminals, bool central)
    {
        for (int c = c0; c <= c1; c++)
            for (int a = a0; a <= a1; a++)
            {
                bool edge = a == a0 || a == a1 || c == c0 || c == c1;
                p.Clear(a, c);
                if (!edge)
                {
                    p.At(a, c).Floor = FloorKind.EndCarpetWorn;
                    continue;
                }
                bool corner = (a == a0 || a == a1) && (c == c0 || c == c1);
                int piece;
                ArchPier pier;
                if (c == c1) { piece = corner ? 1 : 0; pier = ArchPier.South; }
                else if (c == c0)
                {
                    int mid = (a0 + a1) / 2;
                    if (a == mid) { p.At(a, c).Floor = FloorKind.EndCarpetWorn; continue; } // the gap at the back
                    piece = corner ? 1 : a == mid - 1 || a == mid + 1 ? 3 : 0;
                    pier = ArchPier.North;
                }
                else { piece = 0; pier = a == a0 ? ArchPier.West : ArchPier.East; }
                if (corner) pier = c == c1 ? (a == a0 ? ArchPier.West : ArchPier.South) : (a == a0 ? ArchPier.North : ArchPier.East);
                int stack = piece;
                if (c == c1 && Array.IndexOf(terminals, a) >= 0) stack |= 8 | (central ? 16 : 0);
                p.Prop(a, c, Props.EndDesk, stack, front == ArchPier.South ? pier : Opposite(pier));
            }
    }


    /// <summary>
    /// A room walled round a rectangle with a doorway three wide in the middle of some sides (<paramref name="doors"/>:
    /// bit 0 north, 1 south, 2 west, 3 east).
    /// </summary>
    private static void PlanEndRoom(EndPlanner p, int a0, int c0, int a1, int c1, WallPattern pattern, int doors = 15)
    {
        int ma = (a0 + a1) / 2, mc = (c0 + c1) / 2;
        for (int c = c0; c <= c1; c++)
            for (int a = a0; a <= a1; a++)
            {
                if (a != a0 && a != a1 && c != c0 && c != c1) continue;
                bool door = (c == c0 && (doors & 1) != 0 || c == c1 && (doors & 2) != 0) && Math.Abs(a - ma) <= 1
                    || (a == a0 && (doors & 4) != 0 || a == a1 && (doors & 8) != 0) && Math.Abs(c - mc) <= 1;
                if (door)
                {
                    p.Clear(a, c);
                    ref Tile t = ref p.At(a, c);
                    t.Kind = TileKind.Doorway;
                    t.Pattern = pattern;
                    continue;
                }
                p.Wall(a, c, pattern);
            }
    }

    /// <summary>
    /// A reading room: walls lined with shelving, rows of study tables with green banker's lamps and chairs, carrels
    /// along one wall, two card catalogues by the door, armchairs and a magazine rack in a corner.
    /// </summary>
    private static void PlanEndReading(EndPlanner p)
    {
        ref Rng rng = ref p.Rng;
        PlanEndRoom(p, 8, 8, 55, 55, WallPattern.EndWall);
        // Shelving along the inside of the walls, carrels along the west one
        for (int i = 10; i <= 53; i++)
        {
            if (Math.Abs(i - 31) <= 2) continue;
            p.Prop(i, 9, Props.EndWallShelf, rng.Chance(0.05) ? 1 : 0, ArchPier.South);
            p.Prop(i, 54, Props.EndWallShelf, rng.Chance(0.05) ? 1 : 0, ArchPier.North);
            p.Prop(54, i, Props.EndWallShelf, rng.Chance(0.05) ? 1 : 0, ArchPier.West);
            if (i % 2 == 0) p.Prop(9, i, Props.EndFurniture, 5, ArchPier.East);
        }
        // Study tables, two by one, a lamp on one end, chairs either side
        for (int c = 16; c <= 46; c += 5)
            for (int a = 16; a <= 44; a += 6)
            {
                if (Math.Abs(c - 31) <= 2 && a < 20) continue;
                bool lamp = rng.Chance(0.7);
                p.Prop(a, c, Props.EndFurniture, lamp ? 1 : 0, ArchPier.North);
                p.Prop(a + 1, c, Props.EndFurniture, 0, ArchPier.North);
                for (int k = 0; k < 2; k++)
                {
                    if (rng.Chance(0.8)) p.Prop(a + k, c - 1, Props.EndFurniture, rng.Chance(0.05) ? 3 : 2, ArchPier.South);
                    if (rng.Chance(0.8)) p.Prop(a + k, c + 1, Props.EndFurniture, 2, ArchPier.North);
                }
            }
        // The card catalogues by the north door, armchairs and the rack in the north-east corner
        p.Prop(27, 11, Props.EndCatalogue, rng.Chance(0.3) ? 1 : 0, ArchPier.South);
        p.Prop(35, 11, Props.EndCatalogue, rng.Chance(0.3) ? 1 : 0, ArchPier.South);
        p.Prop(50, 12, Props.EndFurniture, 4, ArchPier.West);
        p.Prop(50, 14, Props.EndFurniture, 4, ArchPier.West);
        p.Prop(48, 11, Props.EndFurniture, 7, ArchPier.South);
    }

    /// <summary>
    /// A two-storey atrium: walls round it, a mezzanine deck all round a void, a stopped escalator up to the deck, library
    /// stacks four high under the deck and in the void with rolling ladders, pendants hung under the high ceiling.
    /// </summary>
    private static void PlanEndAtrium(EndPlanner p)
    {
        const int w0 = 10, w1 = 53, v0 = 19, v1 = 44;
        PlanEndRoom(p, w0, w0, w1, w1, WallPattern.EndWall);
        ref Rng rng = ref p.Rng;
        for (int c = w0; c <= w1; c++)
            for (int a = w0; a <= w1; a++)
            {
                ref Tile t = ref p.At(a, c);
                t.Height = EndAtriumHeight;
                if (t.Kind != TileKind.Floor || a == w0 || a == w1 || c == w0 || c == w1) continue;
                bool voidTile = a >= v0 && a <= v1 && c >= v0 && c <= v1;
                if (!voidTile)
                {
                    // The deck, its edge railed toward the void
                    bool edge = a >= v0 - 1 && a <= v1 + 1 && c >= v0 - 1 && c <= v1 + 1;
                    t.Overhead = edge ? Overheads.EndDeckEdge : Overheads.EndDeck;
                    if (edge) t.Pier = a == v0 - 1 ? ArchPier.East : a == v1 + 1 ? ArchPier.West : c == v0 - 1 ? ArchPier.South : ArchPier.North;
                    continue;
                }
                // The void's ceiling has no troffers: the pendants light it
                t.Ceiling = CeilingKind.Tile;
                if ((a - v0) % 4 == 2 && (c - v0) % 4 == 0) t.Overhead = Overheads.EndPendant;
            }
        // Under the deck, stacks out from the walls
        for (int i = w0 + 2; i <= w1 - 2; i += 3)
        {
            if (Math.Abs(i - 31) <= 2) continue;
            for (int k = 1; k <= 5; k++)
            {
                p.Prop(i, w0 + k, Props.EndTallShelf, rng.Chance(0.05) ? 1 : 0, ArchPier.West);
                p.Prop(i, w1 - k, Props.EndTallShelf, rng.Chance(0.05) ? 1 : 0, ArchPier.East);
            }
        }
        // In the void, rows of stacks with ladders against them
        for (int c = v0 + 2; c <= v1 - 2; c += 4)
            for (int a = v0 + 3; a <= v1 - 2; a++)
            {
                if (Math.Abs(a - 31) <= 1) continue;
                p.Prop(a, c, Props.EndTallShelf, rng.Chance(0.08) ? 1 : rng.Chance(0.2) ? 2 : 0, ArchPier.South);
                if (p.At(a, c).Stack == 2 && rng.Chance(0.4)) p.Prop(a, c + 1, Props.EndLadder, 0, ArchPier.North);
            }
        // The escalator, up the west side of the void onto the deck
        for (int k = 0; k < 6; k++)
        {
            p.Clear(v0, 25 + k);
            ref Tile t = ref p.At(v0, 25 + k);
            t.Variant = Props.EndEscalator;
            // The foot piece is the landing at the first step's height, and the top piece the last step up onto the deck
            t.Stair = (byte)Math.Min(Math.Max(k, 1), EndDeckRel);
            t.Stack = (byte)(k == 0 ? 2 : k == 5 ? 1 : 0); // bottom, top, steps
            t.Pier = ArchPier.South;
            t.Overhead = 0;
        }
        p.Clear(v0, 24);
        p.Clear(v0 + 1, 24);
        // Off the top of the escalator onto the deck: no railing there
        for (int k = 3; k <= 5; k++) p.At(v0 - 1, 25 + k).Overhead = Overheads.EndDeck;
        p.Prop(v0, 31, Props.EndTallShelf, 0, ArchPier.North);
    }

    /// <summary>
    /// A stockroom: painted block walls, concrete, rows of wrapped stock, trolleys and ladders in plastic, a break nook
    /// with an Almond Water cooler, EXIT doors in the back wall (two in three of them locked), a staff door, and in some a
    /// vent up a steel ladder.
    /// </summary>
    private void PlanEndStock(EndPlanner p)
    {
        ref Rng rng = ref p.Rng;
        p.Zone = 2;
        for (int c = 8; c <= 55; c++)
            for (int a = 8; a <= 55; a++)
            {
                ref Tile t = ref p.At(a, c);
                t.Floor = a is 31 or 32 ? FloorKind.EndConcreteLine : FloorKind.EndConcrete;
                t.Zone = 2;
                if (t.Ceiling is CeilingKind.LightOn or CeilingKind.LightLit && rng.Chance(0.5)) t.Ceiling = CeilingKind.LightOff;
            }
        PlanEndRoom(p, 8, 8, 55, 55, WallPattern.EndStockWall, doors: 1 | 8);
        // Wrapped stock in rows, a cross aisle down the middle
        for (int c = 14; c <= 46; c += 4)
            for (int a = 12; a <= 51; a++)
            {
                if (a is >= 30 and <= 33) continue;
                double u = rng.NextDouble();
                if (u < 0.75) p.Prop(a, c, Props.EndStock, rng.Chance(0.75) ? 0 : 3, ArchPier.North);
                else if (u < 0.82) p.Prop(a, c + 1, Props.EndStock, 1, (ArchPier)rng.Range(0, 3));
                else if (u < 0.86) p.Prop(a, c + 2, Props.EndStock, 2, (ArchPier)rng.Range(0, 3));
            }
        // The break nook: the cooler, a table and chairs
        p.Prop(54, 50, Props.Cooler, 0, ArchPier.West);
        p.Prop(50, 51, Props.EndFurniture, 0, ArchPier.North);
        p.Prop(50, 50, Props.EndFurniture, 2, ArchPier.South);
        p.Prop(50, 52, Props.EndFurniture, 2, ArchPier.North);
        // EXIT doors in the back (south) wall, a staff door in the west one
        int doors = rng.Range(1, 2);
        for (int n = 0; n < doors; n++)
        {
            int a = n == 0 ? 20 : 43;
            ref Tile t = ref p.At(a, 55);
            t.Kind = TileKind.Door;
            t.Pattern = WallPattern.EndExit;
            t.Pier = ArchPier.North;
            p.Clear(a, 54);
            p.Clear(a, 53);
        }
        {
            ref Tile t = ref p.At(8, 40);
            t.Kind = TileKind.Door;
            t.Pattern = WallPattern.EndStaff;
            t.Pier = ArchPier.East;
            p.Clear(9, 40);
        }
        // One stockroom in three: a vent high in the back wall, a steel ladder up to it
        if (rng.Chance(0.34))
        {
            ref Tile wall = ref p.At(32, 55);
            wall.Under = Unders.EndVentWall;
            wall.Pier = ArchPier.North;
            p.Clear(32, 54);
            p.Prop(32, 54, Props.EndLadder, 1, ArchPier.South);
            p.Clear(32, 53);
            p.Clear(31, 53);
            p.Clear(33, 53);
        }
    }

    /// <summary>A collapse: stacks fallen like dominoes, ceiling tiles down, cracked columns, every light dead.</summary>
    private static void PlanEndCollapse(EndPlanner p)
    {
        ref Rng rng = ref p.Rng;
        PlanEndStacks(p, EndInner0, EndInner0, EndInner1, EndInner1, null, rng.Chance(0.5));
        PlanEndColumns(p, 16, null, 0.1);
        for (int c = 0; c < p.H; c++)
            for (int a = 0; a < p.W; a++)
            {
                ref Tile t = ref p.At(a, c);
                if (t.Kind == TileKind.Wall)
                {
                    if (rng.Chance(0.5)) { t.Variant = Decor.EndCrack; t.Pier = (ArchPier)rng.Range(0, 3); }
                    continue;
                }
                t.Zone = 3;
                t.Floor = rng.Chance(0.5) ? FloorKind.EndCarpetDusty : FloorKind.EndCarpetStained;
                if (t.Variant == Props.EndShelf && t.Stack != 3)
                {
                    double u = rng.NextDouble();
                    if (u < 0.35) { t.Variant = Props.EndRubble; t.Stack = 0; }
                    else if (u < 0.5) t.Stack = 4;
                }
                if (rng.Chance(0.2))
                {
                    t.Overhead = Overheads.EndMissingTile;
                    if (t.Variant == 0 && rng.Chance(0.3)) { t.Variant = Props.EndRubble; t.Stack = 1; }
                }
            }
    }

    /// <summary>
    /// The central hall: open carpet with the blue field, a round desk under a soffit lettered THE END IS NEAR on all
    /// four faces, four columns papered with posters, stacks round it all, and an EXIT door in each corner.
    /// </summary>
    private static void PlanEndCentral(EndPlanner p)
    {
        bool Ring(int a, int c) => a < 14 || a > 50 || c < 14 || c > 50;
        PlanEndStacks(p, EndInner0, EndInner0, EndInner1, EndInner1, (a, c) => Ring(a, c) && !(a < 18 && c < 18 || a > 46 && c < 18 || a < 18 && c > 46 || a > 46 && c > 46), true);
        for (int c = 0; c < p.H; c++)
            for (int a = 0; a < p.W; a++)
            {
                p.At(a, c).Zone = 1;
                if (a >= 22 && a <= 42 && c >= 22 && c <= 42) p.At(a, c).Floor = FloorKind.EndRunway;
            }
        PlanEndSoffit(p, 21, 21, 43, 43, "the end is near", 1);
        PlanEndServiceDesk(p, 28, 28, 36, 35, ArchPier.South, terminals: new[] { 30, 32, 34 }, central: true);
        foreach (var (a, c) in new[] { (17, 17), (47, 17), (17, 47), (47, 47) })
        {
            p.Wall(a, c, WallPattern.EndColumn);
            p.At(a, c).Zone = 1;
            p.At(a, c).Variant = Decor.EndPoster;
            p.At(a, c).Pier = a < 30 ? ArchPier.East : ArchPier.West;
        }
        // An EXIT door in a short wall in each corner, facing the middle; from layout version 5 at the back of a little
        // vestibule, walled on three sides and open toward the middle, so it reads as a way out of the store, not a kiosk
        foreach (var (a, c, face) in new[] { (12, 10, ArchPier.South), (51, 10, ArchPier.South), (12, 53, ArchPier.North), (51, 53, ArchPier.North) })
        {
            int s = face == ArchPier.South ? 1 : -1;
            for (int k = -2; k <= 2; k++)
            {
                p.Clear(a + k, c - 1);
                p.Clear(a + k, c + 1);
                if (p.V5)
                {
                    p.Clear(a + k, c + 2 * s);
                    p.Clear(a + k, c + 3 * s);
                }
                p.Wall(a + k, c);
                p.At(a + k, c).Zone = 1;
            }
            if (p.V5)
                for (int d = 1; d <= 2; d++)
                    foreach (int k in new[] { -2, 2 })
                    {
                        p.Wall(a + k, c + d * s);
                        p.At(a + k, c + d * s).Zone = 1;
                    }
            ref Tile door = ref p.At(a, c);
            door.Kind = TileKind.Door;
            door.Pattern = WallPattern.EndExit;
            door.Pier = face;
            // (In a vestibule the ghost marks are beside the door, the end of the wall being its corner)
            int ghost = p.V5 ? a - 1 : a - 2;
            p.At(ghost, c).Variant = Decor.EndGhost;
            p.At(ghost, c).Pier = face;
            if (p.V5)
            {
                // A poster inside on one side wall, ghost marks on the other
                p.At(a - 2, c + 2 * s).Variant = Decor.EndPoster;
                p.At(a - 2, c + 2 * s).Pier = ArchPier.East;
                p.At(a + 2, c + s).Variant = Decor.EndGhost;
                p.At(a + 2, c + s).Pier = ArchPier.West;
            }
        }
    }

    /// <summary>
    /// A long aisle across two departments: three wide, between library stacks four high, repeating exactly every
    /// <see cref="EndLoopPeriod"/> blocks from one end to the other (stacks, lights, gaps, ladders), so that walking on
    /// along it can loop without anyone seeing the seam. Gaps lead out to the sides, north and south in turn.
    /// </summary>
    private Tile[] PlanEndLongAisle(int left, int dj)
    {
        var p = NewEndPlanner(EndDept * 2, EndDept, left, dj, false);
        ulong h = Hashing.Hash(seed, left, dj, SaltEndPlan + 1);
        PlanEndStacks(p, EndInner0, EndInner0, EndDept + EndInner1, 24, null, true);
        PlanEndStacks(p, EndInner0, 38, EndDept + EndInner1, EndInner1, null, true);
        for (int s = 0; s < EndDept * 2; s++)
        {
            for (int c = 25; c <= 37; c++)
            {
                ref Tile t = ref p.At(s, c);
                t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.EndCarpet, Pattern = WallPattern.EndWall,
                    Height = c is >= 28 and <= 34 ? (byte)EndAisleHeight : (byte)EndCeilingHeight };
            }
            bool inside = s >= EndLoopStart && s < EndLoopEnd;
            int phase = Hashing.Mod(s, EndLoopPeriod);
            // Lights: one line down the aisle, the same every period
            if ((s & 3) == 1) p.At(s, 31).Ceiling = phase is 1 or 17 ? CeilingKind.LightOn : CeilingKind.LightLit;
            if ((s & 3) == 1) { p.At(s, 26).Ceiling = CeilingKind.LightLit; p.At(s, 36).Ceiling = CeilingKind.LightLit; }
            if (!inside) continue;
            for (int c = 30; c <= 32; c++)
            {
                p.At(s, c).Under = Unders.EndLoop;
                p.At(s, c).Pier = ArchPier.East;
                p.At(s, c).Floor = FloorKind.EndCarpetWorn;
            }
            bool northGap = phase is 8 or 9, southGap = phase is 24 or 25;
            int books = (int)((h >> phase) & 15);
            if (!northGap)
            {
                p.Prop(s, 29, Props.EndTallShelf, phase is >= 13 and <= 15 ? 2 : books == 0 ? 1 : 0, ArchPier.South);
                p.Prop(s, 28, Props.EndTallShelf, 0, ArchPier.North);
            }
            if (!southGap)
            {
                p.Prop(s, 33, Props.EndTallShelf, books == 1 ? 1 : 0, ArchPier.North);
                p.Prop(s, 34, Props.EndTallShelf, 0, ArchPier.South);
            }
            if (phase == 14) p.Prop(s, 30, Props.EndLadder, 0, ArchPier.North);
        }
        return p.T;
    }

    // ================= Fake realities =================

    /// <summary>
    /// A fake reality: a familiar place the library gives way to. Over the outer sixteen blocks the shelves thin out and
    /// the imitation's floor, walls and lights come in more and more; its 32-block core is the place itself. Its door
    /// (where it has one) is a doorway in a lone wall in the middle.
    /// </summary>
    private void PlanEndFake(EndPlanner p, EndFake kind)
    {
        ref Rng rng = ref p.Rng;
        PlanEndStacks(p, EndInner0, EndInner0, EndInner1, EndInner1, null, rng.Chance(0.5), keep: 0.6);
        PlanEndColumns(p, 16, null, 0.2);
        bool works = EndFakeWorks(p.Di, p.Dj, kind);
        FloorKind floor = kind switch
        {
            EndFake.Lobby => FloorKind.Carpet,
            EndFake.Office => FloorKind.OfficeCarpet,
            EndFake.Hotel => FloorKind.HotelCarpet,
            EndFake.House => FloorKind.HouseWood,
            EndFake.Snow => FloorKind.EndCarpetSnow,
            _ => FloorKind.HouseCarpet,
        };
        WallPattern paper = kind switch
        {
            EndFake.Lobby => WallPattern.Chevron,
            EndFake.Office => WallPattern.Drywall,
            EndFake.Hotel => WallPattern.Hotel,
            EndFake.House => WallPattern.InteriorFloral,
            EndFake.Home => WallPattern.InteriorBeige,
            _ => WallPattern.EndWall,
        };
        // The blend: the nearer the core, the more of the imitation
        for (int c = 0; c < p.H; c++)
            for (int a = 0; a < p.W; a++)
            {
                double d = Math.Max(Math.Abs(a - 31.5), Math.Abs(c - 31.5));
                ref Tile t = ref p.At(a, c);
                if (d >= 30) continue;
                double share = d < 16 ? 1 : (30 - d) / 14;
                t.Zone = (byte)(d < 16 ? 5 : 4);
                t.Detail = (byte)kind;
                if (d < 16)
                {
                    // The core is cleared and built afresh below
                    t = new Tile { Kind = TileKind.Floor, Floor = floor, Zone = 5, Detail = (byte)kind, Depth = 1,
                        Height = kind == EndFake.Snow ? (byte)EndAtriumHeight : (byte)(WorldGeometry.RoomHeight + 1), Pattern = paper };
                    continue;
                }
                if (rng.Chance(share)) t.Floor = floor;
                if (t.Kind == TileKind.Floor && t.Variant is Props.EndShelf or Props.EndEndcap && rng.Chance(share * 0.8)) { t.Variant = 0; t.Stack = 0; }
                if (t.Kind == TileKind.Wall && paper != WallPattern.EndWall && rng.Chance(share)) { t.Pattern = paper; t.Variant = 0; t.Tall = true; }
                if (kind != EndFake.Snow && rng.Chance(share * 0.8)) t.Depth = 1;
                if (kind == EndFake.Snow && t.Kind == TileKind.Floor && t.Variant == 0 && rng.Chance(share)) t.Variant = Props.EndSnow;
            }

        const int k0 = 16, k1 = 47;
        switch (kind)
        {
            case EndFake.Lobby:
                // Level 0: yellow rooms on an eight-block grid, gaps in every wall, Level 0's troffers
                for (int c = k0; c <= k1; c++)
                    for (int a = k0; a <= k1; a++)
                    {
                        ref Tile t = ref p.At(a, c);
                        if (a % 3 == 1 && c % 4 == 2) t.Ceiling = rng.Chance(0.6) ? CeilingKind.LightOn : CeilingKind.LightLit;
                        bool onA = (a - k0) % 8 == 0, onC = (c - k0) % 8 == 0;
                        if (!onA && !onC) continue;
                        int along = onA ? (c - k0) % 8 : (a - k0) % 8;
                        bool gap = along is 3 or 4 && Hashing.Unit(Hashing.Hash(seed, p.Di * 64 + a / 8 * 8, p.Dj * 64 + c / 8 * 8 + (onA ? 1 : 0), SaltEndFake + 3)) < 0.75;
                        if (onA && onC || !gap) { p.Wall(a, c, WallPattern.Chevron); p.At(a, c).Base = BaseStyle.Baseboard; }
                    }
                break;
            case EndFake.Office:
                PlanEndRoom(p, k0, k0, k1, k1, WallPattern.Drywall);
                for (int c = k0 + 1; c < k1; c++)
                    for (int a = k0 + 1; a < k1; a++)
                    {
                        if (a % 4 == 1 && c % 4 == 1) p.At(a, c).Ceiling = rng.Chance(0.5) ? CeilingKind.LightOn : CeilingKind.LightLit;
                        int ca = (a - k0 - 3) % 7, cc = (c - k0 - 3) % 6;
                        if (a < k0 + 3 || c < k0 + 3 || a > k1 - 3 || c > k1 - 3 || Math.Abs(a - 31) <= 2 && Math.Abs(c - 31) <= 2) continue;
                        if (ca == 0) p.Prop(a, c, Props.Partition, 0, ArchPier.North);
                        else if (cc == 0 && ca < 6) p.Prop(a, c, Props.Partition, 0, ArchPier.East);
                        else if (ca == 2 && cc == 2) p.Prop(a, c, Props.Desk, 0, ArchPier.South);
                        else if (ca == 2 && cc == 3 && rng.Chance(0.7)) p.Prop(a, c, Props.OfficeChair, 0, ArchPier.North);
                    }
                for (int i = k0 + 4; i < k1 - 3; i += 5) { p.At(i, k1).Pattern = WallPattern.OfficeWindow; p.At(i, k1).Variant = (ushort)(i % 3); }
                break;
            case EndFake.Hotel:
                // A stretch of the hotel's corridor, guest doors along it, the corridor's end wall with the door out
                for (int a = k0; a <= k1; a++)
                {
                    p.Wall(a, 29, WallPattern.Hotel);
                    p.Wall(a, 33, WallPattern.Hotel);
                    for (int c = 30; c <= 32; c++)
                    {
                        ref Tile t = ref p.At(a, c);
                        t.Floor = c == 31 ? FloorKind.HotelRunnerWE : FloorKind.HotelCarpet;
                        t.Ceiling = c == 31 && a % 4 == 0 ? CeilingKind.LightOn : CeilingKind.Tile;
                    }
                    if ((a - k0) % 6 == 3 && a < k1 - 2)
                    {
                        foreach (int c in new[] { 29, 33 })
                        {
                            ref Tile door = ref p.At(a, c);
                            door.Kind = TileKind.Door;
                            door.Variant = (ushort)(a % 8);
                            door.Pier = c == 29 ? ArchPier.South : ArchPier.North;
                        }
                    }
                }
                for (int c = k0; c <= k1; c++)
                    for (int a = k0; a <= k1; a++)
                        if (c is < 29 or > 33) { p.Wall(a, c, WallPattern.Hotel); p.At(a, c).Zone = 5; p.At(a, c).Detail = (byte)kind; }
                for (int c = 30; c <= 32; c++) p.Wall(k1, c, WallPattern.Hotel);
                {
                    ref Tile end = ref p.At(k1, 31);
                    end.Kind = works ? TileKind.Doorway : TileKind.Door;
                    end.Under = works ? Unders.EndFakeDoor : (byte)0;
                    end.Pier = ArchPier.West;
                }
                break;
            case EndFake.House:
            case EndFake.Home:
            {
                // A living room and a hall of a house in the Suburbs (or, for Home, a warm room from the real world)
                int a0 = 20, c0 = 22, a1 = 43, c1 = 41;
                PlanEndRoom(p, a0, c0, a1, c1, paper, doors: 1);
                for (int c = c0 + 1; c < c1; c++)
                    for (int a = a0 + 1; a < a1; a++)
                    {
                        ref Tile t = ref p.At(a, c);
                        if (kind == EndFake.House && a > a0 + 3 && a < a1 - 3 && c > c0 + 3 && c < c1 - 3) t.Floor = FloorKind.HouseRug;
                        if ((a - a0) % 6 == 3 && (c - c0) % 6 == 3) t.Ceiling = CeilingKind.LightOn;
                    }
                if (kind == EndFake.House) for (int c = c0 + 1; c < c1; c++) if (Math.Abs(c - 31) > 1) p.Wall(32, c, paper);
                p.Prop(a0 + 2, c0 + 2, Props.FloorLamp);
                p.Prop(a1 - 2, c0 + 2, Props.FloorLamp);
                p.Prop(26, c1 - 1, Props.Tv, 0, ArchPier.North);
                p.Prop(26, c1 - 5, Props.CoffeeTable);
                p.Prop(25, c1 - 7, Props.EndFurniture, 4, ArchPier.South);
                p.Prop(27, c1 - 7, Props.EndFurniture, 4, ArchPier.South);
                for (int a = a0 + 2; a <= a0 + 8; a += 2) p.Prop(a, c0 + 1, Props.HotelBookshelf, 0, ArchPier.South);
                p.Prop(a1 - 2, c1 - 2, Props.Dresser, 0, ArchPier.West);
                if (kind == EndFake.House)
                {
                    // The front door, in the south wall
                    ref Tile door = ref p.At(36, c1);
                    door.Kind = works ? TileKind.Doorway : TileKind.Door;
                    door.Under = works ? Unders.EndFakeDoor : (byte)0;
                    door.Pier = ArchPier.North;
                    p.Clear(36, c1 - 1);
                }
                break;
            }
            case EndFake.Snow:
                // Snow on the carpet, bare trees between the last shelves, the lights white and far apart
                for (int c = k0; c <= k1; c++)
                    for (int a = k0; a <= k1; a++)
                    {
                        ref Tile t = ref p.At(a, c);
                        t.Ceiling = a % 8 == 4 && c % 8 == 4 ? CeilingKind.LightOn : CeilingKind.Tile;
                        if (rng.Chance(0.04) && Math.Abs(a - 31) + Math.Abs(c - 31) > 3) { t.Variant = Props.EndTree; t.Stack = (byte)rng.Range(3, 5); }
                        else t.Variant = Props.EndSnow;
                    }
                break;
        }

        // The door out: a doorway in a lone wall in the middle (the hotel's and the house's are their own doors)
        if (kind is EndFake.Lobby or EndFake.Office)
        {
            for (int c = 28; c <= 34; c++)
                for (int a = 28; a <= 35; a++)
                    if (p.At(a, c).Kind != TileKind.Floor || p.At(a, c).Variant != 0) { p.Clear(a, c); p.At(a, c).Floor = floor; }
            for (int a = 30; a <= 32; a++) p.Wall(a, 31, paper);
            ref Tile mid = ref p.At(31, 31);
            if (works)
            {
                mid.Kind = TileKind.Doorway;
                mid.Under = Unders.EndFakeDoor;
                mid.Pier = ArchPier.North;
            }
            for (int a = 30; a <= 32; a++) { p.At(a, 31).Zone = 5; p.At(a, 31).Detail = (byte)kind; p.At(a, 31).Tall = true; if (kind == EndFake.Lobby) p.At(a, 31).Base = BaseStyle.Baseboard; }
        }
        // Whatever the core's walls are, they are the imitation's, its height, its zone
        for (int c = k0; c <= k1; c++)
            for (int a = k0; a <= k1; a++)
            {
                ref Tile t = ref p.At(a, c);
                t.Zone = 5;
                t.Detail = (byte)kind;
                if (t.Height == 0) t.Height = (byte)(WorldGeometry.RoomHeight + 1);
                if (t.IsWallLike) t.Tall = true;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.EndFirst"/> to <see cref="Props.EndLast"/>) are walked through rather than around.</summary>
    private static bool EndWalkThrough(ushort variant) => variant is Props.EndSnow or Props.EndEscalator;

    // ================= Searches =================

    /// <summary>
    /// The nearest way out of The End from a position, within a radius: an EXIT door that opens, a fake reality's working
    /// door, a vent. Department by department, nearest first. <paramref name="opens"/> says whether an EXIT door opens
    /// (the network decides); null counts every one.
    /// </summary>
    public List<(int X, int Z)> EndExitsNear(int gx, int gz, int radius, Func<int, int, bool> opens, int max = 3)
    {
        var found = new List<(int X, int Z, long D)>();
        var (di0, dj0) = EndDeptOf(gx, gz);
        int reach = radius / EndDept + 1;
        for (int dj = dj0 - reach; dj <= dj0 + reach; dj++)
            for (int di = di0 - reach; di <= di0 + reach; di++)
            {
                var (cx, cz) = EndDeptCentre(di, dj);
                if (LevelAt(MacroOf(cx), MacroOf(cz)) != TheEnd) continue;
                EndKind kind = EndKindAt(di, dj);
                if (kind is not (EndKind.Stock or EndKind.Central or EndKind.Fake)) continue;
                Tile[] plan = EndPlan(di, dj);
                for (int i = 0; i < plan.Length; i++)
                {
                    Tile t = plan[i];
                    bool exit = t.Kind == TileKind.Door && t.Pattern == WallPattern.EndExit || t.Under is Unders.EndFakeDoor or Unders.EndVentWall;
                    if (!exit) continue;
                    int x = EndOriginX + di * EndDept + i % EndDept, z = EndOriginZ + dj * EndDept + i / EndDept;
                    if (LevelAt(MacroOf(x), MacroOf(z)) != TheEnd) continue;
                    if (t.Pattern == WallPattern.EndExit && t.Kind == TileKind.Door && opens != null && !opens(x, z)) continue;
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
    /// Whether a position is in a long aisle's looping stretch, and if so its place along the aisle (pair-local x, from
    /// the west edge of the pair's left department; the stretch is <see cref="EndLoopStart"/> to <see cref="EndLoopEnd"/>).
    /// </summary>
    public bool EndLoopAt(int gx, int gz, out int along)
    {
        along = -1;
        if (TileAt(gx, gz).Under != Unders.EndLoop) return false;
        var (di, _) = EndDeptOf(gx, gz);
        int left = Hashing.Mod(di, 2) == 0 ? di : di - 1;
        along = gx - EndOriginX - left * EndDept;
        return true;
    }

    /// <summary>The Junkies' camp: where a wanderer keeps to in a Home fake reality (one to its cell, by the sofa).</summary>
    private (int X, int Z)? EndWandererSite(int mx, int mz)
    {
        int gx = mx * MacroSize + MacroSize / 2, gz = mz * MacroSize + MacroSize / 2;
        var (di, dj) = EndDeptOf(gx, gz);
        if (EndKindAt(di, dj) != EndKind.Fake || EndFakeAt(di, dj) != EndFake.Home) return null;
        var (cx, cz) = EndDeptCentre(di, dj);
        foreach (var (x, z) in new[] { (cx - 6, cz + 2), (cx + 4, cz + 4) })
            if (MacroOf(x) == mx && MacroOf(z) == mz && IsEntitySpot(x, z)) return (x, z);
        return null;
    }

    // ================= What it is like =================

    private float EndTemperature(int x, int y, int z, int floorY)
    {
        Tile t = TileAt(x, z);
        if (t.Zone is 4 or 5 && t.Detail == (byte)EndFake.Snow) return t.Zone == 5 ? -6f : 6f;
        if (t.Zone == 5 && t.Detail == (byte)EndFake.Home) return 22f;
        return LevelTemperatures[TheEnd];
    }

    /// <summary>
    /// Reality stability here: kindest in the central hall ("stay here and not explore"), falling toward the rim, low in
    /// the collapses and the fake realities, lowest in the snow.
    /// </summary>
    private float EndStability(double x, double y, double z, int floorY, float drift)
    {
        int gx = (int)Math.Floor(x), gz = (int)Math.Floor(z);
        Tile t = TileAt(gx, gz);
        switch (t.Zone)
        {
            case 1: return 1.2f;
            case 3: return 0.45f;
            case 4: return 0.6f;
            case 5: return t.Detail switch { (byte)EndFake.Snow => 0.35f, (byte)EndFake.Home => 0.9f, _ => 0.45f };
        }
        var (di, dj) = EndDeptOf(gx, gz);
        double f = Math.Clamp(EndDeptDistance(di, dj) / 30, 0, 1);
        return (float)(1.0 - 0.25 * f + 0.15 * drift);
    }
}
