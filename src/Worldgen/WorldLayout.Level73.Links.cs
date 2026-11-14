using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 73, "The Redlands": its ways in and out (docs/design/experimental-levels/LINKS.md, the Level 73 section; the level's
/// plan, "Links"). This file is the level's own.
/// <list type="bullet">
/// <item><b>The Gloom</b> (Level 9; Wikidot: "stay near the Gloom for too long on Level 9.1"): about one Suburbs cell in
/// <see cref="L73GloomCells"/> holds, in a yard or a street, a pool of darkness that light does not reach: black ground, and over
/// its heart a black murk two blocks high (<see cref="Unders.L73Gloom"/>, its rim <see cref="Unders.L73GloomRim"/>).
/// Whoever stays in it too long is on the island (Regions/L73System.Links.cs; one way).</item>
/// <item><b>Level 6's deepest dark</b> (the page names Level 6 and nothing more): about one cell of Lights Out in
/// <see cref="L73DarkOneIn"/> is darker than the rest. Nothing marks it in the layout; whoever lingers there a long time with no
/// light is taken (one way).</item>
/// <item><b>Coran leads you out</b> (our invention: the page knows no way out): a door in the outside of the castle's north
/// curtain wall, chained shut, behind which there is no courtyard, only the dark. Coran opens it for whoever has slept a
/// night under his roof and asks him; through it is Level 9 (one way).</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The links' layout salts (in the level's 0x2100-0x21BF).</summary>
    private const ulong SaltL73GloomCell = 0x2140, SaltL73GloomShape = 0x2141, SaltL73DarkCell = 0x2142;

    /// <summary>One Suburbs cell in this many may hold the Gloom (where a yard or a street has room for it).</summary>
    public const int L73GloomCells = 2000;

    /// <summary>One cell of Level 6 in this many is its deepest dark (the pre-releases' rate, before layout 16's balance, which every world now reads: ExpVersion).</summary>
    public const int L73DarkCells = 2500;

    /// <summary>
    /// One cell of Level 6 in this many is its deepest dark in this world: from layout 16's balance (every world: ExpVersion) one in 10,000, a quarter as
    /// many (the progression rule, decision 20: from Level 6 onto the Class 5 island, and so by Coran to Level 9, is a
    /// shortcut, a quarter as common; the kept cells are the same, the lowest rolls). The Gloom in Level 9 is not a way deeper
    /// and stays.
    /// </summary>
    public int L73DarkOneIn => ExpVersion >= 16 ? L73DarkCells * 4 : L73DarkCells;

    /// <summary>How far from its middle the Gloom reaches at most (blocks), and the room round that a cell must have clear.</summary>
    private const int L73GloomReach = 4;

    // ================= The Gloom, in Level 9 =================

    /// <summary>Whether a tile is part of the Gloom (its heart or its rim).</summary>
    public static bool IsL73Gloom(in Tile t) => t.Level == 9 && t.Under is Unders.L73Gloom or Unders.L73GloomRim;

    /// <summary>Whether a Suburbs cell is one that may hold the Gloom (by its own hash; whether it found room is the cell's).</summary>
    public bool IsL73GloomCell(int mx, int mz) =>
        ExpEntrances && !IsSpawnMacro(mx, mz) && Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL73GloomCell)) < 1.0 / L73GloomCells;

    /// <summary>The ground the Gloom may lie on: lawn, asphalt and pavement (a yard or a street), with nothing on it.</summary>
    private static bool L73GloomGround(in Tile t) =>
        t.Kind == TileKind.Floor && t.Floor is FloorKind.Lawn or FloorKind.Asphalt or FloorKind.AsphaltWet or FloorKind.AsphaltLeaves or FloorKind.Sidewalk
        && t.Variant == 0 && t.Under == 0 && t.Overhead == 0 && t.Pipe == 0 && !t.Sealed && !t.SupplyBox && t.Stair == 0 && t.Stack == 0
        && t.Height == 0 && t.Depth == 0 && t.Roof == 0 && t.Detail == 0;

    /// <summary>
    /// The experimental levels' hook (WorldLayout.ExpLinks.cs), last in precedence: in Level 9, the Gloom, where this cell is
    /// one that may hold it and a yard or a street has a clear round of <see cref="L73GloomReach"/> blocks for it. A lumpy pool
    /// some five to seven across, its heart under the murk, a ring of black ground round that.
    /// </summary>
    partial void L73Entrances(Builder b, int mx, int mz)
    {
        if (b.Level != 9 || !IsL73GloomCell(mx, mz)) return;
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltL73GloomShape));
        const int r = L73GloomReach;
        var room = new List<(int X, int Z)>();
        for (int lz = r + 1; lz < MacroSize - r - 1; lz++)
            for (int lx = r + 1; lx < MacroSize - r - 1; lx++)
            {
                bool clear = true;
                for (int dz = -r; dz <= r && clear; dz++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        if (dx * dx + dz * dz > r * r + 1) continue;
                        if (!L73GloomGround(b.At(lx + dx, lz + dz))) { clear = false; break; }
                    }
                if (clear) room.Add((lx, lz));
            }
        if (room.Count == 0) return;
        var (cx, cz) = room[rng.Range(0, room.Count - 1)];
        // Its edge wanders: a base reach, and two slow waves round it
        double reach = 2.4 + 0.7 * rng.NextDouble(), a1 = rng.NextDouble() * Math.PI * 2, a2 = rng.NextDouble() * Math.PI * 2;
        for (int dz = -r; dz <= r; dz++)
            for (int dx = -r; dx <= r; dx++)
            {
                double d = Math.Sqrt(dx * dx + dz * dz), angle = Math.Atan2(dz, dx);
                double edge = Math.Min(r, reach + 0.55 * Math.Sin(2 * angle + a1) + 0.35 * Math.Sin(3 * angle + a2));
                if (d > edge) continue;
                ref Tile t = ref b.At(cx + dx, cz + dz);
                t.Under = d <= edge - 1.1 ? Unders.L73Gloom : Unders.L73GloomRim;
            }
    }

    /// <summary>The Gloom a tile is part of, as the one position that stands for it (its first tile by x, then z).</summary>
    public (int X, int Z) L73GloomOrigin(int x, int z) => FeatureOrigin(x, z, t => IsL73Gloom(t));

    // ================= Level 6's deepest dark =================

    /// <summary>
    /// Whether a cell of Level 6 is its deepest dark: one in <see cref="L73DarkOneIn"/> by the cell's own hash, never in the
    /// Snackrooms, and only where the cell's north-west corner is wall (that corner stands for it in the thresholds: a pillar
    /// where two of the cell's walls meet, which none of Level 6's own thresholds starts from).
    /// </summary>
    public bool IsL73DarkCell(int mx, int mz)
    {
        if (!ExpEntrances || !L73DarkRolls(mx, mz)) return false;
        if (LevelAt(mx, mz) != 6 || IsSnackrooms(mx, mz)) return false;
        return TileAt(mx * MacroSize, mz * MacroSize).Kind == TileKind.Wall;
    }

    /// <summary>
    /// Whether a cell rolls Level 6's deepest dark (by its own hash alone; IsL73DarkCell says whether it is one). From layout
    /// 16's balance (every world: ExpVersion), where the quarter would leave the whole of Level 6 none (a small world, an unlucky seed), the cell with the
    /// lowest roll of those the old rate gave stays (decision 20's "keep at least one"): <see cref="L73DarkFloorScan"/>.
    /// </summary>
    public bool L73DarkRolls(int mx, int mz)
    {
        double u = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL73DarkCell));
        if (u < 1.0 / L73DarkOneIn) return true;
        // (Until the floor is known, no extra cell: it comes in a second or so on a worker thread, not on the caller's)
        return ExpVersion >= 16 && u < 1.0 / L73DarkCells && L73DarkFloorNow is double floor && u <= floor;
    }

    private Task<double> l73DarkFloor;

    private double? L73DarkFloorNow
    {
        get
        {
            var task = LazyInitializer.EnsureInitialized(ref l73DarkFloor, () => Task.Run(L73DarkFloorScan));
            return task.IsCompletedSuccessfully ? task.Result : null;
        }
    }

    /// <summary>Waits for <see cref="L73DarkFloorScan"/> to be known (for the harness, which wants the final answer).</summary>
    public void L73DarkFloorWait() => LazyInitializer.EnsureInitialized(ref l73DarkFloor, () => Task.Run(L73DarkFloorScan)).Wait();

    /// <summary>
    /// The lowest roll among the cells that are Level 6's deepest dark at the old rate (one in <see cref="L73DarkCells"/>), or
    /// 0 if there is none: worked out once, over a square round spawn that holds the whole of Level 6.
    /// </summary>
    private double L73DarkFloorScan()
    {
        double outer = 0;
        for (int a = 0; a < 360; a++) outer = Math.Max(outer, RingEdges(6, a * Math.PI / 180).Outer);
        int reach = (int)Math.Ceiling(outer * 1.1) + 8;
        double best = 1.0 / L73DarkCells;
        bool found = false;
        for (int dz = -reach; dz <= reach; dz++)
            for (int dx = -reach; dx <= reach; dx++)
            {
                int mx = spawnMacroX + dx, mz = spawnMacroZ + dz;
                double u = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL73DarkCell));
                if (u >= best) continue;
                if (LevelAt(mx, mz) != 6 || IsSnackrooms(mx, mz) || TileAt(mx * MacroSize, mz * MacroSize).Kind != TileKind.Wall) continue;
                best = u;
                found = true;
            }
        return found ? best : 0;
    }

    // ================= The north door, in the castle =================

    /// <summary>
    /// The door Coran opens, castle-local: two leaves (u 27 and 28) two high in the outer course of the north curtain wall
    /// (v 0), facing north; behind it the wall's inner course is blacked on its north face (the dark), so from the courtyard
    /// the wall is only wall. Null if (u, v) is not one of its two leaves; else 0 for the west leaf, 1 for the east.
    /// </summary>
    public static int? L73PosternAt(int u, int v) => v == 0 && u is 27 or 28 ? u - 27 : null;

    /// <summary>Whether a castle-local position is the inner course behind the north door (the dark you see through it).</summary>
    public static bool L73PosternBack(int u, int v) => v == 1 && u is 27 or 28;

    /// <summary>How high the north door is (blocks over the plateau's floor, from 1).</summary>
    public const int L73PosternHeight = 2;

    /// <summary>The ground before the north door, castle-local, kept clear of bones and packs.</summary>
    private static bool L73PosternApron(int u, int v) => u is >= 24 and <= 31 && v is >= -5 and <= -1;

    /// <summary>The north door, in blocks: its west leaf (the east leaf is one east of it).</summary>
    public (int X, int Z) L73Postern => (L73CastleX0 + 27, L73CastleZ0);

    /// <summary>Where Coran stands to open the north door, in blocks (three before it, between its leaves).</summary>
    public (double X, double Z) L73PosternFront => (L73CastleX0 + 28.0, L73CastleZ0 - 2.5);

    // ================= Finding them (the harness's 73links, the showcase) =================

    /// <summary>
    /// The nearest few Glooms to spawn (each as the middle of its tiles, in blocks, and its distance from spawn's middle),
    /// nearest first, searched ring by ring out to <paramref name="maxCells"/> cells.
    /// </summary>
    public List<(double X, double Z, double Distance)> L73NearestGlooms(int n, int maxCells = 4000) =>
        L73Nearest(n, maxCells, (mx, mz) =>
        {
            if (!IsL73GloomCell(mx, mz) || LevelAt(mx, mz) != 9) return null;
            double sx = 0, sz = 0;
            int count = 0;
            for (int lz = 0; lz < MacroSize; lz++)
                for (int lx = 0; lx < MacroSize; lx++)
                {
                    int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                    if (!IsL73Gloom(TileAt(gx, gz))) continue;
                    sx += gx + 0.5;
                    sz += gz + 0.5;
                    count++;
                }
            return count == 0 ? null : (sx / count, sz / count);
        });

    /// <summary>The nearest few cells of Level 6's deepest dark to spawn (each as its middle, in blocks), nearest first.</summary>
    public List<(double X, double Z, double Distance)> L73NearestDark(int n, int maxCells = 4000) =>
        L73Nearest(n, maxCells, (mx, mz) => IsL73DarkCell(mx, mz) ? (mx * MacroSize + MacroSize / 2.0, mz * MacroSize + MacroSize / 2.0) : null);

    /// <summary>
    /// The showcase's spots at the level's ways in, in their host levels: the nearest Gloom to spawn (from a few blocks off, and
    /// from inside it), and the nearest cell of Level 6's deepest dark (a lit torch shows only an ordinary corridor of it).
    /// </summary>
    public IEnumerable<Showcase.Spot> L73LinkSpots(WorldGeometry geometry)
    {
        if (L73NearestGlooms(1) is { Count: > 0 } glooms)
        {
            var (gx, gz, _) = glooms[0];
            double feet = geometry.FloorFor(9) + 1;
            // From the open ground beside it, eight blocks off, looking at it (the first of eight bearings that is clear)
            for (int k = 0; k < 8; k++)
            {
                double a = k * Math.PI / 4, vx = gx + Math.Sin(a) * 8, vz = gz - Math.Cos(a) * 8;
                Tile t = TileAt((int)Math.Floor(vx), (int)Math.Floor(vz));
                if (t.Kind != TileKind.Floor || t.Variant != 0 || IsL73Gloom(t) || t.Height != 0) continue;
                // (Heading: clockwise from north, toward the Gloom)
                double heading = (k * 45 + 180) % 360;
                yield return new Showcase.Spot("gloom", vx, feet, vz, heading, -14);
                break;
            }
            yield return new Showcase.Spot("gloom-inside", gx, feet, gz, 90, -8);
        }
        if (L73NearestDark(1) is { Count: > 0 } dark)
        {
            var (dx, dz, _) = dark[0];
            // A floor tile near the cell's middle
            for (int r = 0; r < 14; r++)
                for (int i = 0; i < 8 * Math.Max(1, r); i++)
                {
                    double a = i * Math.PI * 2 / (8 * Math.Max(1, r));
                    int x = (int)Math.Floor(dx + Math.Cos(a) * r), z = (int)Math.Floor(dz + Math.Sin(a) * r);
                    if (TileAt(x, z) is not { Kind: TileKind.Floor, Variant: 0, Stair: 0 }) continue;
                    yield return new Showcase.Spot("deepest-dark", x + 0.5, geometry.FloorFor(6) + 1, z + 0.5, 0, -5);
                    yield break;
                }
        }
    }

    private List<(double X, double Z, double Distance)> L73Nearest(int n, int maxCells, Func<int, int, (double X, double Z)?> at)
    {
        double ox = spawnMacroX * MacroSize + MacroSize / 2.0, oz = spawnMacroZ * MacroSize + MacroSize / 2.0;
        var found = new List<(double X, double Z, double Distance)>();
        void Try(int dx, int dz)
        {
            if (at(spawnMacroX + dx, spawnMacroZ + dz) is not { } a) return;
            found.Add((a.X, a.Z, Math.Sqrt((a.X - ox) * (a.X - ox) + (a.Z - oz) * (a.Z - oz))));
        }
        for (int r = 0; r <= maxCells; r++)
        {
            // Every cell r cells from spawn's (square rings: each side once, corners once)
            if (r == 0) Try(0, 0);
            for (int i = -r; i < r; i++)
            {
                Try(i, -r);
                Try(r, i);
                Try(-i, r);
                Try(-r, -i);
            }
            if (found.Count >= n)
            {
                found.Sort((a, b) => a.Distance.CompareTo(b.Distance));
                // (Every cell nearer than the n-th found has been looked at once the rings have passed it)
                if (r * MacroSize >= found[n - 1].Distance + MacroSize) return found.GetRange(0, n);
            }
        }
        found.Sort((a, b) => a.Distance.CompareTo(b.Distance));
        return found.Count > n ? found.GetRange(0, n) : found;
    }
}
