using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 6, "Lights Out": an endless series of tight hallways of a smooth, cold material, in total darkness. No
/// light permeates it and light brought in barely works. It is unnaturally silent.
///
/// <para>The hallways are laid out so they can be walked by touch. Long, straight trunk corridors run on a lattice
/// about <see cref="L6Pitch"/> blocks apart; every fourth is a main trunk, three wide and never broken, and between
/// the mains the minor trunks (two wide) form a maze of their own: a tree grown in from one side, so most wrong turns
/// end, a hundred blocks and more on, against a blank wall. Off the trunks, narrow side passages, wet underfoot, wind a
/// little way into the rock and stop. At some crossings the trunks open into a chamber; deeper into the level, the
/// likelier a chamber is to hold stairs going down toward the faint sound of waves (Level 7): from layout version 9 a
/// stairwell two wide, cut down through the rock to a landing eight blocks below, and only in a few chambers, most of
/// them deep in the level (<see cref="L6DescentChance"/>). Chalk on the walls,
/// left by those who came before, marks the dead ends and points along the trunks toward the stairs, and a wire
/// strung across a side passage here and there trips the unwary straight into Level 6.1.</para>
///
/// <para><b>Level 6.1, the Snackrooms</b>, is hidden in rare cells of the same ring, walled off from the maze: an
/// endless 1980s mall food court, bright as day, with snack bars and convenience stores whose vending machines,
/// fridges and shelves are full. It can only be fallen into, and its exits are unreliable: a rusty steel door back
/// into the dark, glass doors and vents to other levels, and kitchen doors that open into another food court.</para>
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL6Snack = 0x6A02;
    private const ulong SaltL6Detail = 0x6A03;
    private const ulong SaltL6Unit = 0x6A04;
    private const ulong SaltL6Line = 0x6A10;
    private const ulong SaltL6Tree = 0x6A11;
    private const ulong SaltL6Plan = 0x6A13;
    private const ulong SaltL6Chamber = 0x6A14;

    /// <summary>Average distance between neighbouring trunk corridors, each way.</summary>
    private const int L6Pitch = 64;
    private const int L6Jitter = 7;
    /// <summary>Every this many trunks is a main one: three wide and never broken.</summary>
    private const int L6MainEvery = 4;

    private const double SnackroomsChance = 0.35;

    // Bounded memo of IsSnackrooms (each answer looks at the 49 cells round one)
    private readonly LatticeMemo<bool> snackCache;

    /// <summary>
    /// The Snackrooms: rare cells of Level 6 with the 3 by 3 cells round them all Level 6, kept clear of any likelier site
    /// within three cells (so two food courts are never close together), and clear of the trunks (a food court set down
    /// across a trunk would cut it).
    /// </summary>
    public bool IsSnackrooms(int mx, int mz) => snackCache.Get(mx, mz);

    private bool ComputeSnackrooms(int mx, int mz)
    {
        double h = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL6Snack));
        if (!SnackroomsSite(mx, mz, h)) return false;
        // Of two sites close together, only the likelier is a food court
        for (int dz = -3; dz <= 3; dz++)
            for (int dx = -3; dx <= 3; dx++)
            {
                if (dx == 0 && dz == 0) continue;
                double other = Hashing.Unit(Hashing.Hash(seed, mx + dx, mz + dz, SaltL6Snack));
                if (other < h && SnackroomsSite(mx + dx, mz + dz, other)) return false;
            }
        return true;
    }

    /// <summary>Whether a cell could hold the Snackrooms: picked by its hash, clear of the trunks, inside Level 6.</summary>
    private bool SnackroomsSite(int mx, int mz, double hash) =>
        hash <= SnackroomsChance && !L6LineNear(0, mx * MacroSize) && !L6LineNear(1, mz * MacroSize) && SurroundedByLevel6(mx, mz);

    private bool SurroundedByLevel6(int mx, int mz)
    {
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != 6) return false;
        return true;
    }

    /// <summary>Whether a trunk of an axis runs within a few blocks of the cell starting at <paramref name="start"/>.</summary>
    private bool L6LineNear(int axis, int start)
    {
        int k = L6UnitOf(axis, start - 4);
        for (int n = 0; n <= 2; n++)
        {
            int line = L6Line(axis, k + n);
            if (line >= start - 4 && line <= start + MacroSize + 3) return true;
        }
        return false;
    }

    /// <summary>
    /// Picks a Snackrooms cell for a key: the same key always leads to the same food court. The search starts at a
    /// point of the Level 6 ring picked from the key and spirals out to the nearest food court.
    /// </summary>
    public (int Mx, int Mz)? SnackroomCellFor(ulong key)
    {
        ulong h = Hashing.Mix(key ^ SaltL6Snack);
        double angle = Hashing.Unit(h) * Math.PI * 2;
        double inner = InnerEdge(6, angle), outer = OuterEdge(6, angle);
        double radius = inner + (0.2 + 0.6 * Hashing.Unit(Hashing.Mix(h))) * (outer - inner);
        int cx = spawnMacroX + (int)Math.Round(Math.Cos(angle) * radius), cz = spawnMacroZ + (int)Math.Round(Math.Sin(angle) * radius);
        for (int r = 0; r <= 40; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) == r && IsSnackrooms(cx + dx, cz + dz)) return (cx + dx, cz + dz);
        return null;
    }

    // ================= The trunks =================

    /// <summary>Where trunk <paramref name="k"/> of an axis runs: the x of a north-south trunk (axis 0), the z of a west-east one.</summary>
    private int L6Line(int axis, int k) => k * L6Pitch + (int)(Hashing.Hash(seed, k, axis, SaltL6Line) % (2 * L6Jitter + 1)) - L6Jitter;

    private static bool L6Main(int k) => Hashing.Mod(k, L6MainEvery) == 0;

    private static int L6Width(int k) => L6Main(k) ? 3 : 2;

    /// <summary>Which unit (the rock between trunks, with the trunks on its west and north sides) a coordinate lies in.</summary>
    private int L6UnitOf(int axis, int g)
    {
        int k = Hashing.FloorDiv(g, L6Pitch);
        while (g < L6Line(axis, k)) k--;
        while (g >= L6Line(axis, k + 1)) k++;
        return k;
    }

    /// <summary>
    /// Whether a stretch of trunk is there: the part of trunk <paramref name="line"/> of an axis between two crossings,
    /// beside unit <paramref name="index"/>. Main trunks always are; the minor ones are the maze between them.
    /// </summary>
    private bool L6Stretch(int axis, int line, int index)
    {
        if (L6Main(line)) return true;
        int mcx = Hashing.FloorDiv(axis == 0 ? line : index, L6MainEvery), mcz = Hashing.FloorDiv(axis == 0 ? index : line, L6MainEvery);
        return L6Tree(mcx, mcz).Contains((axis, line, index));
    }

    private readonly PlanCache<HashSet<(int, int, int)>> l6Trees;

    private HashSet<(int, int, int)> L6Tree(int mcx, int mcz) => l6Trees.Get(mcx, mcz);

    /// <summary>The minor trunks between four main ones: a maze with one way in (see <see cref="PlanLatticeTree"/>).</summary>
    private HashSet<(int, int, int)> PlanL6Tree(int mcx, int mcz) => PlanLatticeTree(mcx, mcz, L6MainEvery, SaltL6Tree, 0.6, 0.08, 0.1);

    /// <summary>
    /// The chamber some crossings open into, in the corner of the unit beside them, and whether it holds stairs down:
    /// the deeper into the level, the likelier.
    /// </summary>
    private (bool Chamber, int Size, bool Stairs, bool East) L6Chamber(int bx, int bz)
    {
        ulong h = Hashing.Hash(seed, bx, bz, SaltL6Chamber);
        if (Hashing.Unit(h) >= 0.5) return default;
        int x0 = L6Line(0, bx), z0 = L6Line(1, bz);
        int size = Hashing.Unit(h << 8) < 0.5 ? 7 : 9;
        double depth = RingFraction(x0 + size, z0 + size, 6);
        bool east = Hashing.Unit(h << 24) < 0.5;
        bool stairs = Version >= 9
            ? Hashing.Unit(h << 16) < L6DescentChance(depth) && L6StairwellFits(bx, bz, size, east)
            : Hashing.Unit(h << 16) < 0.2 + 0.6 * depth && LevelAt(MacroOf(x0 + size), MacroOf(z0 + size)) == 6;
        return (true, size, stairs, east);
    }

    // ================= The stairwell down to Level 7 (layout version 9) =================

    /// <summary>
    /// From layout version 9 a Level 6 descent is a stairwell two wide and this many steps deep: step n's tread is a
    /// stair block n - 1 below the floor, the first four open under the chamber, the rest cut on into the rock with three
    /// blocks of headroom under its floor; then a landing of <see cref="L6LandingRows"/> rows whose floor block lies
    /// <see cref="L6DescentSteps"/> below the chamber's. The first row of the landing is only a landing (whoever comes
    /// back up from Level 7 is put down there); walking on onto the last two takes you down into Level 7.
    /// </summary>
    public const int L6DescentSteps = 8, L6LandingRows = 3;

    /// <summary>How far below the floor (at the feet) someone on the far rows of a stairwell's landing is taken to Level 7.</summary>
    public const double L6DescentTripRel = -6.5;

    /// <summary>The height over the floor at which someone is put down on a stairwell's landing (its floor's top is 7 below the floor's).</summary>
    public const double L6LandingHeight = 1.05 - L6DescentSteps;

    /// <summary>
    /// The chance that a chamber holds the stairs down, by how far into the ring it lies (0 at the inner edge, 1 at the
    /// outer): from layout version 9 the lore's "deep enough", one chamber in a hundred near Level 5, one in sixteen
    /// halfway and one in five at the far edge (in 1-8, 0.2 + 0.6 times the depth: half of all chambers on average).
    /// </summary>
    private static double L6DescentChance(double depth) => 0.01 + 0.2 * depth * depth;

    /// <summary>
    /// Where a chamber's stairwell runs (layout version 9): the corners of its two lanes, in global coordinates, from the
    /// first step to the far end of the landing. It runs east (or south) from the chamber's last four rows, away from the
    /// trunks on the unit's west and north sides, on into the rock.
    /// </summary>
    private (int X0, int Z0, int X1, int Z1) L6StairwellSpan(int bx, int bz, int size, bool east)
    {
        int gx = L6Line(0, bx) + L6Width(bx), gz = L6Line(1, bz) + L6Width(bz);
        int along = (east ? gx : gz) + size - 4, across = (east ? gz : gx) + size / 2 - 1;
        int run = L6DescentSteps + L6LandingRows - 1;
        return east ? (along, across, along + run, across + 1) : (across, along, across + 1, along + run);
    }

    /// <summary>
    /// Whether a chamber's stairwell (layout version 9) fits: it stays inside the unit, short of the next trunk, and every
    /// cell it touches is Level 6 all round and no food court (nor beside one), so nothing else is laid over it.
    /// </summary>
    private bool L6StairwellFits(int bx, int bz, int size, bool east)
    {
        var (x0, z0, x1, z1) = L6StairwellSpan(bx, bz, size, east);
        if (east ? x1 >= L6Line(0, bx + 1) - 1 : z1 >= L6Line(1, bz + 1) - 1) return false;
        foreach ((int x, int z) in new[] { (x0, z0), (x1, z0), (x0, z1), (x1, z1) })
        {
            int mx = MacroOf(x), mz = MacroOf(z);
            if (!SurroundedByLevel6(mx, mz) || IsSnackrooms(mx, mz) || IsSnackrooms(mx - 1, mz) || IsSnackrooms(mx, mz - 1)) return false;
        }
        return true;
    }

    /// <summary>
    /// Cuts a chamber's stairwell (layout version 9) into a unit's plan: <see cref="Unders.Descent1"/> on the steps
    /// (<see cref="Tile.Stair"/> their number), <see cref="Unders.Descent2"/> on the landing's first row and
    /// <see cref="Unders.Descent3"/> on the two beyond, <see cref="Tile.Pier"/> the way it goes down. The tiles keep what
    /// they are above the floor: the chamber's floor over the first steps, the rock or a side passage over the rest.
    /// </summary>
    private static void CutL6Stairwell(L6Unit u, int hw, int hh, int size, bool east)
    {
        int along0 = (east ? hw : hh) + size - 4, across0 = (east ? hh : hw) + size / 2 - 1;
        for (int k = 0; k < L6DescentSteps + L6LandingRows; k++)
            for (int lane = 0; lane < 2; lane++)
            {
                int a = along0 + k, c = across0 + lane;
                ref Tile t = ref east ? ref u.At(a, c) : ref u.At(c, a);
                t.Variant = 0;
                t.Stack = 0;
                t.SupplyBox = false;
                t.Chalk = 0;
                t.Under = k < L6DescentSteps ? Unders.Descent1 : k == L6DescentSteps ? Unders.Descent2 : Unders.Descent3;
                t.Stair = (byte)(k < L6DescentSteps ? k + 1 : 0);
                t.Pier = east ? ArchPier.East : ArchPier.South;
                t.Sealed = true; // nobody is put down on a staircase
                // (The faint sound of waves, from under the far end of the landing)
                t.Detail = k == L6DescentSteps + L6LandingRows - 1 && lane == 0 ? L6WaveEcho : (byte)0;
            }
    }

    /// <summary>Level 6's <see cref="Tile.Detail"/> (layout version 9): the sound of waves comes from under this tile of a stairwell's landing.</summary>
    public const byte L6WaveEcho = 1;

    /// <summary>
    /// The first row of the landing of the stairwell down that a tile of it belongs to (layout version 9), in the tile's
    /// own lane: where whoever comes back up from Level 7 is put down. Null for anything else.
    /// </summary>
    public (int X, int Z)? L6LandingOf(int x, int z)
    {
        if (Version < 9) return null;
        Tile t = TileAt(x, z);
        if (t.Level != 6 || t.Under is not (Unders.Descent1 or Unders.Descent2 or Unders.Descent3)) return null;
        (int dx, int dz) = t.Pier == ArchPier.East ? (1, 0) : (0, 1);
        // How far along the stairwell the tile is (0 the first step); the two far rows of the landing tell themselves apart
        // by what lies two back
        int k = t.Under == Unders.Descent1 ? t.Stair - 1 : t.Under == Unders.Descent2 ? L6DescentSteps
            : TileAt(x - dx, z - dz).Under == Unders.Descent2 ? L6DescentSteps + 1 : L6DescentSteps + 2;
        int off = L6DescentSteps - k;
        return (x + dx * off, z + dz * off);
    }

    /// <summary>
    /// The landing of a stairwell down to Level 7 (layout version 9) for a key: the same key always finds the same one.
    /// The search starts at a point picked from the key in the deeper half of the Level 6 ring and looks outward for the
    /// nearest stairwell. Null if there is none (or before version 9).
    /// </summary>
    public (int X, int Z)? FindDescentLanding(ulong key)
    {
        if (Version < 9) return null;
        ulong h = Hashing.Mix(key ^ SaltL6Chamber);
        double angle = Hashing.Unit(h) * Math.PI * 2;
        double inner = InnerEdge(6, angle), outer = OuterEdge(6, angle);
        double radius = inner + (0.55 + 0.4 * Hashing.Unit(Hashing.Mix(h))) * (outer - inner);
        int gx = (spawnMacroX + (int)Math.Round(Math.Cos(angle) * radius)) * MacroSize + MacroSize / 2;
        int gz = (spawnMacroZ + (int)Math.Round(Math.Sin(angle) * radius)) * MacroSize + MacroSize / 2;
        for (int reach = 400; reach <= 3200; reach *= 2)
            if (NearestDescentLanding(gx, gz, reach) is { } landing) return landing;
        return null;
    }

    /// <summary>The first row of the landing (in its first lane) of the nearest stairwell down within a radius (layout version 9).</summary>
    private (int X, int Z)? NearestDescentLanding(int gx, int gz, int radius)
    {
        (int, int)? best = null;
        long bestD = long.MaxValue;
        for (int bz = L6UnitOf(1, gz - radius); bz <= L6UnitOf(1, gz + radius); bz++)
            for (int bx = L6UnitOf(0, gx - radius); bx <= L6UnitOf(0, gx + radius); bx++)
            {
                if (L6StairwellAt(bx, bz) is not { } s) continue;
                bool east = s.X1 - s.X0 > s.Z1 - s.Z0;
                int x = east ? s.X0 + L6DescentSteps : s.X0, z = east ? s.Z0 : s.Z0 + L6DescentSteps;
                long d = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                if (d < bestD && d <= (long)radius * radius) { bestD = d; best = (x, z); }
            }
        return best;
    }

    /// <summary>The span of the stairwell a unit's chamber holds (layout version 9), or null if it holds none.</summary>
    private (int X0, int Z0, int X1, int Z1)? L6StairwellAt(int bx, int bz)
    {
        var c = L6Chamber(bx, bz);
        if (!c.Chamber || !c.Stairs || !(L6Stretch(0, bx, bz) || L6Stretch(1, bz, bx)) || !L6CrossingOpen(bx, bz)) return null;
        return L6StairwellSpan(bx, bz, c.Size, c.East);
    }

    /// <summary>The middle of the nearest stairs down to Level 7 within a radius, if any (for the sound of the waves).</summary>
    public (int X, int Z)? NearestDescent(int gx, int gz, int radius)
    {
        (int, int)? best = null;
        long bestD = long.MaxValue;
        for (int bz = L6UnitOf(1, gz - radius); bz <= L6UnitOf(1, gz + radius); bz++)
            for (int bx = L6UnitOf(0, gx - radius); bx <= L6UnitOf(0, gx + radius); bx++)
            {
                int x, z;
                if (Version >= 9)
                {
                    // (The middle of the landing, down in the rock, where the sound comes from)
                    if (L6StairwellAt(bx, bz) is not { } s) continue;
                    x = (s.X0 + s.X1 + 1) / 2;
                    z = (s.Z0 + s.Z1 + 1) / 2;
                }
                else
                {
                    var c = L6Chamber(bx, bz);
                    if (!c.Stairs || !L6CrossingOpen(bx, bz)) continue;
                    x = L6Line(0, bx) + L6Width(bx) + c.Size / 2;
                    z = L6Line(1, bz) + L6Width(bz) + c.Size / 2;
                    if (IsSnackrooms(MacroOf(x), MacroOf(z))) continue;
                }
                long d = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                if (d < bestD && d <= (long)radius * radius) { bestD = d; best = (x, z); }
            }
        return best;
    }

    private bool L6CrossingOpen(int bx, int bz) =>
        L6Stretch(0, bx, bz) || L6Stretch(1, bz, bx) || L6Stretch(0, bx, bz - 1) || L6Stretch(1, bz, bx - 1);

    // ================= Units: the rock between the trunks =================

    private sealed class L6Unit
    {
        public int X0, Z0, W, H;
        public Tile[] Tiles;
        public ref Tile At(int u, int v) => ref Tiles[v * W + u];
    }

    private readonly PlanCache<L6Unit> l6Units;

    private L6Unit L6UnitAt(int bx, int bz) => l6Units.Get(bx, bz);

    private Tile L6TileAt(int gx, int gz)
    {
        L6Unit u = L6UnitAt(L6UnitOf(0, gx), L6UnitOf(1, gz));
        return u.At(gx - u.X0, gz - u.Z0);
    }

    private L6Unit PlanL6Unit(int bx, int bz)
    {
        int x0 = L6Line(0, bx), z0 = L6Line(1, bz);
        var u = new L6Unit { X0 = x0, Z0 = z0, W = L6Line(0, bx + 1) - x0, H = L6Line(1, bz + 1) - z0 };
        u.Tiles = new Tile[u.W * u.H];
        for (int i = 0; i < u.Tiles.Length; i++)
        {
            ref Tile t = ref u.Tiles[i];
            SetWall(ref t, WallPattern.L6Wall, BaseStyle.Plain);
            t.Floor = FloorKind.L6Floor;
        }
        var rng = new Rng(Hashing.Hash(seed, bx, bz, SaltL6Plan));
        int hw = L6Width(bx), hh = L6Width(bz);

        // No passage is cut into a food court, nor into the wall round one
        var snack = new Dictionary<(int, int), bool>();
        bool SnackCell(int cx, int cz)
        {
            if (!snack.TryGetValue((cx, cz), out bool s)) snack[(cx, cz)] = s = IsSnackrooms(cx, cz);
            return s;
        }
        // (The tile's own cell, and the cells west and north of it for the wall round a food court)
        bool Snack(int gx, int gz) => SnackCell(MacroOf(gx), MacroOf(gz)) || SnackCell(MacroOf(gx - 1), MacroOf(gz)) || SnackCell(MacroOf(gx), MacroOf(gz - 1));
        bool Carve(int x, int v, bool wet)
        {
            if (x < 0 || v < 0 || x >= u.W || v >= u.H || Snack(x0 + x, z0 + v)) return false;
            ref Tile t = ref u.At(x, v);
            if (t.Kind != TileKind.Floor) t = new Tile { Floor = wet ? FloorKind.L6Wet : FloorKind.L6Floor };
            return true;
        }

        // The trunks along the west and north sides, and the crossing between them
        bool west = L6Stretch(0, bx, bz), north = L6Stretch(1, bz, bx);
        bool crossing = L6CrossingOpen(bx, bz);
        for (int v = 0; v < u.H; v++)
            for (int x = 0; x < u.W; x++)
            {
                bool inW = x < hw, inN = v < hh;
                if (inW && inN ? crossing : inW ? west : inN && north) Carve(x, v, false);
            }

        // A chamber in the corner by the crossing, opening onto the trunks there; perhaps with stairs going down
        var chamber = L6Chamber(bx, bz);
        if (chamber.Chamber && crossing && (west || north))
        {
            for (int v = hh; v < hh + chamber.Size; v++)
                for (int x = hw; x < hw + chamber.Size; x++)
                    Carve(x, v, false);
            if (Version < 9 && chamber.Stairs && !Snack(x0 + hw + chamber.Size / 2, z0 + hh + chamber.Size / 2))
            {
                ArchPier dir = chamber.East ? ArchPier.East : ArchPier.West;
                int sv = hh + chamber.Size / 2, sx = hw + chamber.Size / 2 - 1;
                for (int k = 0; k < 3; k++)
                {
                    ref Tile step = ref u.At(dir == ArchPier.East ? sx + k : sx + 2 - k, sv);
                    step.Under = (byte)(Unders.Descent1 + k);
                    step.Pier = dir;
                    step.Sealed = true; // nobody is put down on a staircase
                }
            }
        }

        // Side passages off every trunk round the unit, a little way into the rock, wet underfoot
        bool east = L6Stretch(0, bx + 1, bz), south = L6Stretch(1, bz + 1, bx);
        var sides = new (bool Open, int U0, int V0, (int X, int Z) Along, (int X, int Z) In, int Len)[]
        {
            (west, hw, hh, (0, 1), (1, 0), u.H - hh),
            (north, hw, hh, (1, 0), (0, 1), u.W - hw),
            (east, u.W - 1, hh, (0, 1), (-1, 0), u.H - hh),
            (south, hw, u.H - 1, (1, 0), (0, -1), u.W - hw),
        };
        foreach (var s in sides)
        {
            if (!s.Open) continue;
            for (int a = 12 + rng.Range(0, 8); a < s.Len - 14; a += 20 + rng.Range(0, 10))
                if (rng.Chance(0.75)) SidePassage(s.U0 + s.Along.X * a, s.V0 + s.Along.Z * a, s.Along, s.In, ref rng, Carve);
        }

        // From layout version 9, the stairwell down to Level 7, cut through the rock under the chamber and on beyond it
        // (after the side passages, which would otherwise carve over it)
        if (Version >= 9 && chamber.Chamber && chamber.Stairs && crossing && (west || north)) CutL6Stairwell(u, hw, hh, chamber.Size, chamber.East);

        // Chalk on the trunk walls, pointing the way toward the nearest stairs down (from layout version 9, which are
        // rarer, from further off)
        if (NearestDescent(x0 + u.W / 2, z0 + u.H / 2, Version >= 9 ? 400 : 220) is { } target)
        {
            void Arrow(int x, int v, ArchPier wall)
            {
                if (rng.Chance(0.4) || x < 0 || v < 0 || x >= u.W || v >= u.H) return;
                (int wx, int wz) = wall switch { ArchPier.North => (0, -1), ArchPier.East => (1, 0), ArchPier.South => (0, 1), _ => (-1, 0) };
                if (x + wx < 0 || v + wz < 0 || x + wx >= u.W || v + wz >= u.H || u.At(x + wx, v + wz).Kind != TileKind.Wall) return;
                ref Tile t = ref u.At(x, v);
                if (t.Kind != TileKind.Floor || t.Under != 0) return;
                // Facing the wall, which way are the stairs? (Facing north, left is west; facing east, left is north)
                double toX = target.X - (x0 + x), toZ = target.Z - (z0 + v);
                if (toX * toX + toZ * toZ < 100) return;
                t.Chalk = ChalkBits.Make(wall, toX * wz - toZ * wx > 0 ? 0 : 1);
            }
            if (west) Arrow(hw - 1, hh + (u.H - hh) / 2, ArchPier.East);
            if (north) Arrow(hw + (u.W - hw) / 2, hh - 1, ArchPier.South);
        }
        return u;
    }

    /// <summary>Carves one tile of a unit's plan (wet underfoot or not); false where it may not be carved.</summary>
    private delegate bool Carver(int x, int v, bool wet);

    /// <summary>
    /// A narrow passage from a trunk into the rock, branching a few times on a six-block lattice and ending blind: a
    /// tree of three to eight stretches at most four deep, all within thirty blocks of the trunk.
    /// </summary>
    private static void SidePassage(int u0, int v0, (int X, int Z) along, (int X, int Z) inward, ref Rng rng, Carver carve)
    {
        (int, int) At(int p, int d) => (u0 + along.X * p + inward.X * d, v0 + along.Z * p + inward.Z * d);
        bool Line(int p0, int d0, int p1, int d1)
        {
            int steps = Math.Abs(p1 - p0) + Math.Abs(d1 - d0);
            for (int k = 0; k <= steps; k++)
            {
                int p = p0 + Math.Sign(p1 - p0) * Math.Min(k, Math.Abs(p1 - p0)), d = d0 + Math.Sign(d1 - d0) * Math.Min(k, Math.Abs(d1 - d0));
                (int x, int v) = At(p, d);
                if (!carve(x, v, true)) return false;
            }
            return true;
        }
        // Into the rock from the trunk to the first turning
        if (!Line(0, 0, 0, 5)) return;
        // Turnings at p in -12..12 and d in 5..29, six apart; grown as a tree that tends to run straight on
        const int span = 2, rows = 5;
        var visited = new bool[2 * span + 1, rows];
        visited[span, 0] = true;
        int budget = rng.Range(3, 8);
        var stack = new Stack<(int I, int J, int Dir, int Depth)>();
        stack.Push((span, 0, 2, 0));
        (int, int)[] steps = { (1, 0), (-1, 0), (0, 1), (0, -1) };
        var options = new List<int>(4);
        while (stack.Count > 0 && budget > 0)
        {
            var (i, j, dir, depth) = stack.Peek();
            options.Clear();
            if (depth < 4)
                for (int d = 0; d < 4; d++)
                {
                    int ni = i + steps[d].Item1, nj = j + steps[d].Item2;
                    if (ni >= 0 && nj >= 0 && ni <= 2 * span && nj < rows && !visited[ni, nj]) options.Add(d);
                }
            if (options.Count == 0 || rng.Chance(0.25)) { stack.Pop(); continue; }
            int pick = options.Contains(dir) && rng.Chance(0.6) ? dir : options[rng.Range(0, options.Count - 1)];
            int ti = i + steps[pick].Item1, tj = j + steps[pick].Item2;
            visited[ti, tj] = true;
            if (!Line((i - span) * 6, 5 + j * 6, (ti - span) * 6, 5 + tj * 6)) continue;
            budget--;
            stack.Push((ti, tj, pick, depth + 1));
        }
    }

    // ================= Cells =================

    private Edge Level6Edge(int mx, int mz, int nx, int nz, bool west)
    {
        var edge = new Edge { Pattern = WallPattern.L6Wall };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        if (IsSnackrooms(mx, mz) || IsSnackrooms(nx, nz)) return edge; // sealed
        edge.Planned = true;
        bool[] walled = WalledNeighbours(6, mx, mz);
        var wide = walled == null ? default : LiningWidens(6, mx, mz);
        for (int i = 1; i < MacroSize; i++)
        {
            Tile t = west ? L6TileAt(mx * MacroSize, mz * MacroSize + i) : L6TileAt(mx * MacroSize + i, mz * MacroSize);
            bool edgeHall = west ? EdgeHall(walled, 0, i, wide) : EdgeHall(walled, i, 0, wide);
            if (IsWalkable(t) || edgeHall) edge.Tiles[i] = EdgeTile.Open;
        }
        return edge;
    }

    private void BuildLevel6(Builder b, int mx, int mz, Edge west, Edge north)
    {
        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Floor = FloorKind.L6Floor;
        if (IsSnackrooms(mx, mz))
        {
            BuildSnackrooms(b, mx, mz);
            return;
        }
        CopyPlan(b, mx, mz, west, north, (gx, gz, index) => b.Tiles[index] = L6TileAt(gx, gz));
        CarveEdgeHall(b, mx, mz, west, north);
        DecorateLevel6(b, mx, mz);
    }

    /// <summary>Marks on the walls at the dead ends, what was left there, and wires across the side passages.</summary>
    private void DecorateLevel6(Builder b, int mx, int mz)
    {
        bool Open(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && b.At(x, z).Kind == TileKind.Floor;
        for (int lz = 1; lz < MacroSize - 1; lz++)
        {
            for (int lx = 1; lx < MacroSize - 1; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                ulong h = Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltL6Detail);
                double r = Hashing.Unit(h);
                bool e = Open(lx + 1, lz), w = Open(lx - 1, lz), s = Open(lx, lz + 1), n = Open(lx, lz - 1);
                int ways = (e ? 1 : 0) + (w ? 1 : 0) + (s ? 1 : 0) + (n ? 1 : 0);

                if (tile.Kind == TileKind.Floor)
                {
                    if (tile.Under != 0) continue;
                    // A dead end: someone has chalked an X on the wall facing you
                    if (ways == 1 && r < 0.6)
                    {
                        ArchPier toOpen = e ? ArchPier.East : w ? ArchPier.West : s ? ArchPier.South : ArchPier.North;
                        var (fx, fz) = Step(lx, lz, Opposite(toOpen));
                        ref Tile end = ref b.At(fx, fz);
                        if (end.Kind == TileKind.Wall && end.Variant == 0) { end.Variant = Decor.MegCross; end.Pier = toOpen; }
                        // Now and then, what is left of whoever came this far: a dead flashlight, a pack, a bedroll
                        double left = Hashing.Unit(Hashing.Mix(h));
                        if (left < 0.12) { tile.Variant = Props.Flashlight; tile.Pier = (ArchPier)(h % 4); }
                        else if (left < 0.18) { tile.Variant = Props.Backpack; tile.Pier = toOpen; }
                        else if (left < 0.22) { tile.Variant = Version >= 11 ? Props.ImprovBed : Props.Bedroll; tile.Pier = toOpen; if (Version >= 11) tile.Stack = 1; }
                    }
                    // A wire strung low across a straight, narrow passage
                    else if (ways == 2 && (e && w || s && n) && r > 0.985)
                    {
                        tile.Variant = Props.Tripwire;
                        tile.Pier = e && w ? ArchPier.East : ArchPier.North;
                    }
                    continue;
                }
                if (tile.Kind != TileKind.Wall || tile.Variant != 0 || ways == 0) continue;
                ArchPier face = n ? ArchPier.North : s ? ArchPier.South : e ? ArchPier.East : ArchPier.West;
                byte decor = r < 0.012 ? Decor.MegExit : r < 0.014 ? Decor.MegLogo : r < 0.02 ? Decor.Handprints : r < 0.025 ? Decor.Scratches
                    : r < 0.028 ? Decor.DeadSwitch : (byte)0;
                if (decor == 0) continue;
                tile.Variant = decor;
                tile.Pier = face;
            }
        }
    }

    // ================= Level 6.1: the Snackrooms =================

    private enum SnackUnit { Restaurant, Store, Seating, VendingRoom }

    /// <summary>
    /// Level 6.1's <see cref="Tile.Detail"/> (from layout version 5): another machine lies across the top of the one on
    /// this tile (<see cref="SnackPiledOn"/>); the shop front of a vending machine room (<see cref="SnackVendingFront"/>).
    /// </summary>
    public const byte SnackPiledOn = 1, SnackVendingFront = 2;

    private void BuildSnackrooms(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        const int hall0 = 13, hall1 = 18;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                // From layout version 9 the cell's own edges stay Level 6's wall on the outside: the mall's own wall stands
                // inside them (in 1-8 the edges were the mall's, so the maze saw the Snackrooms' wall on two sides)
                if (Version >= 9 && (lx == 0 || lz == 0) && t.Kind != TileKind.Floor) continue;
                t.Zone = 1;
                t.Floor = FloorKind.SnackTerrazzo;
                if (t.Kind != TileKind.Floor) { t.Pattern = WallPattern.SnackMall; continue; }
                bool hall = lz >= hall0 && lz <= hall1 && lx >= 2 && lx <= 30 || lx >= hall0 && lx <= hall1 && lz >= 2 && lz <= 30;
                if (!hall) { SetWall(ref t, WallPattern.SnackMall, BaseStyle.Plain); continue; }
                // Skylights over the halls: they show only darkness, yet light the place like day
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (Hashing.Mod(gx, 3) == 1 && Hashing.Mod(gz, 3) == 1) t.Ceiling = CeilingKind.LightOn;
            }
        }

        // Eight units round the crossing, two to each quadrant, opening onto the halls
        foreach ((int qx0, int qx1) in new[] { (2, 11), (20, 30) })
        {
            foreach ((int qz0, int qz1, bool north) in new[] { (2, 12, true), (19, 30, false) })
            {
                int split = (qx0 + qx1) / 2 + rng.Range(-1, 1);
                foreach ((int ux0, int ux1) in new[] { (qx0, split - 1), (split + 1, qx1) })
                {
                    double r = Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + ux0, mz * MacroSize + qz0, SaltL6Unit));
                    SnackUnit kind = r < 0.55 ? SnackUnit.Restaurant : r < 0.85 ? SnackUnit.Store : SnackUnit.Seating;
                    // From layout version 5, one store in four is a room "unenterable due to the sheer amount of vending
                    // machines piled on top of each other" (about one food court in two has one)
                    if (Version >= 5 && kind == SnackUnit.Store
                        && Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + ux0, mz * MacroSize + qz0, SaltL6Unit + 1)) < 0.25) kind = SnackUnit.VendingRoom;
                    BuildSnackUnit(b, ux0, ux1, north ? qz0 : qz1, north ? qz1 : qz0, north, kind, ref rng, Version >= 9);
                }
            }
        }

        // Tables and chairs down the halls, bins and plants, vending machines against the walls
        for (int k = 3; k <= 28; k += 5)
        {
            if (k >= hall0 - 1 && k <= hall1 + 1) continue;
            PlaceCafeTable(b, k, 15);
            PlaceCafeTable(b, 15, k);
        }
        foreach ((int x, int z) in new[] { (hall0, 3), (hall1, 28), (3, hall0), (28, hall1) }) b.At(x, z).Variant = Props.Ficus;
        foreach ((int x, int z) in new[] { (hall0, 8), (hall1, 23), (8, hall1), (23, hall0) }) b.At(x, z).Variant = Props.TrashCan;
        foreach ((int x, int z, ArchPier f) in new[] { (hall0, 24, ArchPier.East), (hall1, 6, ArchPier.West) })
        {
            b.At(x, z).Variant = Props.SnackVending;
            b.At(x, z).Pier = f;
        }
        ref Tile map = ref b.At(hall0 - 1, 10);
        if (map.Kind == TileKind.Wall) { map.Variant = Decor.MallMap; map.Pier = ArchPier.East; }

        // Ways out, none of them reliable: a rusty steel door back into the dark, glass doors, a vent
        void Exit(int x, int z, byte kind, ArchPier facing)
        {
            ref Tile t = ref b.At(x, z);
            t.Kind = TileKind.Door;
            t.Pattern = WallPattern.SnackMall;
            t.Variant = kind;
            t.Pier = facing;
            // Nothing stands in front of a way out
            var (fx, fz) = Step(x, z, facing);
            ref Tile front = ref b.At(fx, fz);
            if (front.Kind == TileKind.Floor) { front.Variant = 0; front.SupplyBox = false; front.Stack = 0; }
        }
        Exit(1, 15, 1, ArchPier.East);
        if (rng.Chance(0.5)) Exit(15, 1, 4, ArchPier.South);
        if (rng.Chance(0.5)) { Exit(MacroSize - 1, 15, 2, ArchPier.West); Exit(MacroSize - 1, 16, 2, ArchPier.West); }
        if (rng.Chance(0.4)) Exit(16, MacroSize - 1, 1, ArchPier.North);
    }

    private static void PlaceCafeTable(Builder b, int x, int z)
    {
        b.At(x, z).Variant = Props.CafeTable;
        foreach (ArchPier side in new[] { ArchPier.North, ArchPier.South, ArchPier.East, ArchPier.West })
        {
            var (cx, cz) = Step(x, z, side);
            ref Tile chair = ref b.At(cx, cz);
            if (chair.Kind != TileKind.Floor || chair.Variant != 0) continue;
            chair.Variant = Props.CafeChair;
            chair.Pier = Opposite(side);
        }
    }

    /// <summary>
    /// One unit between x0 and x1, from its back wall (row zBack) to its front (row zFront) on the hall. Its side
    /// walls stand at x0 - 1 and x1 + 1 and its back wall at zBack - 1 (or + 1); the front row is open under a
    /// lintel, where the neon sign hangs.
    /// </summary>
    private static void BuildSnackUnit(Builder b, int x0, int x1, int zBack, int zFront, bool north, SnackUnit kind, ref Rng rng, bool broken = false)
    {
        int dz = north ? 1 : -1; // from the back toward the front
        ArchPier toHall = north ? ArchPier.South : ArchPier.North;
        ArchPier toBack = Opposite(toHall);
        int width = x1 - x0 + 1;
        for (int z = zBack; z != zFront + dz; z += dz)
        {
            for (int x = x0; x <= x1; x++)
            {
                ref Tile t = ref b.At(x, z);
                t.Kind = z == zFront ? TileKind.Doorway : TileKind.Floor;
                t.Pattern = kind is SnackUnit.Store or SnackUnit.VendingRoom ? WallPattern.SnackMall : WallPattern.SnackPanel;
                t.Variant = 0;
                t.Floor = kind == SnackUnit.Restaurant ? FloorKind.SnackQuarry : FloorKind.SnackChecker;
                if ((x - x0) % 2 == 1 && (z - zBack) % 3 == 1) t.Ceiling = CeilingKind.LightOn;
            }
        }
        ref Tile At(int x, int z) => ref b.At(x, z);
        void Put(int x, int z, byte prop, ArchPier facing, byte stack = 0)
        {
            ref Tile t = ref b.At(x, z);
            t.Variant = prop;
            t.Pier = facing;
            t.Stack = stack;
        }

        int mid = (x0 + x1) / 2;
        switch (kind)
        {
            case SnackUnit.Restaurant:
            {
                // A neon sign over the front, the counter just inside, the kitchen behind
                ref Tile sign = ref At(mid, zFront);
                sign.Variant = (byte)(Decor.SignBurger + rng.Range(0, 3));
                sign.Pier = toHall;
                int counter = zFront - dz;
                for (int x = x0; x < x1; x++)
                {
                    Put(x, counter, Props.SnackCounter, toHall, (byte)(x == x0 + 1 ? 1 : x == x0 + 2 ? 2 : 0));
                    At(x, counter).Floor = FloorKind.SnackChecker;
                }
                At(x1, counter).Floor = FloorKind.SnackChecker; // the staff gap
                At(x1, zFront).Floor = FloorKind.SnackChecker;
                for (int x = x0; x <= x1; x++) At(x, zFront).Floor = FloorKind.SnackChecker;
                // Along the back wall: griddle, fryer, fridges
                byte[] line = { Props.Stove, Props.Fryer, Props.DrinkFridge, Props.Stove, Props.SnackShelf, Props.DrinkFridge };
                for (int x = x0; x <= x1; x++) Put(x, zBack, line[(x - x0) % line.Length], toHall);
                // A menu board over the griddle, a swinging door into somewhere else
                ref Tile back = ref At(x0 + 1, zBack - dz);
                if (back.Kind == TileKind.Wall) { back.Variant = Decor.MenuBoard; back.Pier = toHall; }
                ref Tile door = ref At(x1, zBack - dz);
                if (door.Kind == TileKind.Wall)
                {
                    door.Kind = TileKind.Door;
                    door.Variant = 3;
                    door.Pier = toHall;
                }
                At(x1, zBack).Variant = 0; // keep the kitchen door clear
                break;
            }
            case SnackUnit.Store:
            {
                // A shop front of glowing windows with a doorway in the middle; shelves in rows, fridges at the back
                for (int x = x0; x <= x1; x++)
                {
                    ref Tile front = ref At(x, zFront);
                    if (Math.Abs(x - mid) <= 0) continue;
                    front.Kind = TileKind.Wall;
                    front.Pattern = WallPattern.SnackWindow;
                }
                for (int x = x0; x <= x1; x++) Put(x, zBack, Props.DrinkFridge, toHall);
                for (int z = zBack + 2 * dz; z != zFront - dz && z != zFront; z += dz)
                    for (int x = x0; x <= x1; x += 2)
                        if (x != mid) Put(x, z, Props.SnackShelf, x < mid ? ArchPier.East : ArchPier.West);
                Put(x0, zFront - dz, Props.SnackCounter, toBack, 1);
                if (width >= 4) Put(x1, zFront - dz, Props.SnackVending, toBack);
                break;
            }
            case SnackUnit.VendingRoom:
            {
                // A shop front like a store's, and behind it machines wall to wall, standing, toppled and piled on
                // each other, dead but for the one in the doorway (which still works; from layout version 9 a broken one,
                // which can be broken up to get in)
                for (int x = x0; x <= x1; x++)
                {
                    ref Tile front = ref At(x, zFront);
                    front.Detail = SnackVendingFront;
                    if (x == mid) continue;
                    front.Kind = TileKind.Wall;
                    front.Pattern = WallPattern.SnackWindow;
                }
                for (int z = zBack; z != zFront; z += dz)
                    for (int x = x0; x <= x1; x++)
                    {
                        ArchPier any = (ArchPier)rng.Range(0, 3);
                        bool first = z == zFront - dz;
                        At(x, z).Sealed = true; // nobody is put down in the gaps of the heap
                        if (first && x == mid) Put(x, z, broken ? Props.BrokenVending : Props.SnackVending, toHall);
                        else if (!first && rng.Chance(0.12)) continue; // a gap in the heap
                        else if (!first && rng.Chance(0.3)) Put(x, z, Props.VendingPile, any, 1); // toppled
                        else Put(x, z, Props.VendingPile, first ? toHall : any);
                        if (At(x, z).Stack == 0 && rng.Chance(first ? 0.75 : 0.5)) At(x, z).Detail = SnackPiledOn;
                    }
                break;
            }
            default:
                for (int k = 1; Math.Abs(k) < Math.Abs(zFront - zBack) - 1; k += 3)
                    for (int x = x0 + 1; x < x1; x += 3)
                        PlaceCafeTable(b, x, zBack + k * dz);
                Put(x1, zBack, Props.SnackVending, toHall);
                break;
        }
    }
}
