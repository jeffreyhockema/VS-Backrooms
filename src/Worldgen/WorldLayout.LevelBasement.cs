using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// The Basement (experimental, unnumbered): kept as level 22 (<see cref="Basement"/>) and shown as "Basement". A round
/// noclip region far out to the south-south-west: a cold, dark cellar that floods the further in you go. The design is in
/// docs/design/experimental-levels/basement-plan.md (after the Wikidot page "Unnumbered Level: The Basement"). No
/// thresholds in or out (the cheats menu or <c>/backrooms goto basement</c> only). This file is the level's own.
///
/// <para><b>Zones</b>, one per cell (<see cref="BasementCellZone"/>, a smooth noise over the cells): <b>the Cellar</b>
/// (dry, about half), damp concrete rooms split from the cell as a BSP tree, each wall with a gap two wide, a crate
/// stack, a boiler or a shelf here and there and a bare bulb in about one room in two (one in five of them dead); <b>the Flood</b>, a maze of
/// passages three wide on an eight-block grid of nodes (a spanning tree over the cell's sixteen nodes, a few links more
/// for loops), its floor two blocks lower under two blocks of still black water, pipes along its ceiling; and <b>the Dry
/// Patch</b>, about one wet cell in five, whose four middle nodes are one raised room 14 by 14 at the Cellar's height
/// with a pump, a boiler and one bright bulb, two steps up into it from every passage that reaches it.</para>
///
/// <para><b>Joins.</b> Two Cellar cells meet through two gaps two wide; two wet cells through two of the four node lines,
/// three wide; a Cellar and a wet cell through one node line, where a stair of two steps goes down into the water on the
/// wet side (<see cref="BasementGaps"/>; both cells and the edge work it out alike).</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> the <see cref="BasementZone"/> (on walls too). The Flood's tiles are
/// <see cref="TileKind.Water"/> (walkable, never an arrival); its steps have <see cref="Tile.Height"/> 2 (the upper, a stair
/// block level with the dry floor) or 1 (the lower), climbing toward <see cref="Tile.Pier"/>. Lamps are
/// <see cref="Tile.Ceiling"/> kinds (82-86), hanging in the top block of air; pipes <see cref="Tile.Pipe"/> 100-103.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2200-0x22BF are this level's (0x22C0-0x22FF its thresholds').</summary>
    private const ulong SaltBasementShape = 0x2201;
    private const ulong SaltBasementZone = 0x2200, SaltBasementPatch = 0x2202, SaltBasementGap = 0x2203, SaltBasementMaze = 0x2205,
        SaltBasementRooms = 0x2206, SaltBasementFurnish = 0x2207;

    /// <summary>What part of the Basement a tile is in (kept in <see cref="Tile.Zone"/>).</summary>
    public enum BasementZone : byte { None, Cellar, Flood, Patch }

    /// <summary>The Flood's node grid: a node every eight blocks, the first four in from the cell's west (north) line.</summary>
    public const int BasementPitch = 8, BasementNode0 = 4;

    /// <summary>The Dry Patch's room: its walls on lines 8 and 23 of the cell, its floor between.</summary>
    public const int BasementPatchLo = 8, BasementPatchHi = 23;

    /// <summary>Below this zone noise a cell is wet (the Flood, or a Dry Patch in it); tuned for about 55% Cellar.</summary>
    private const double BasementWetBelow = -0.06;

    /// <summary>The share of wet cells that hold a Dry Patch.</summary>
    private const double BasementPatchShare = 0.22;

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees west of south.</summary>
    private double BasementReach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int BasementCentreX => spawnMacroX - (int)Math.Round(BasementReach * Math.Sin(Math.PI / 8));
    private int BasementCentreZ => spawnMacroZ + (int)Math.Round(BasementReach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells.</summary>
    private int BasementRadius => Math.Max(40, spawnMacroX / 50);

    /// <summary>The region's centre and radius, in cells (for the harness).</summary>
    public (int Mx, int Mz, int Radius) BasementRegion => (BasementCentreX, BasementCentreZ, BasementRadius);

    private bool InBasement(double mx, double mz) => InRoundRegion(mx, mz, BasementCentreX, BasementCentreZ, BasementRadius, SaltBasementShape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) BasementArrivalCell(ulong h) => RoundArrivalCell(h, BasementCentreX, BasementCentreZ, BasementRadius);

    /// <summary>Arriving: on the dry floor of a Cellar room, never in the water.</summary>
    private static bool IsBasementArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone == (byte)BasementZone.Cellar;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double BasementArrivalHeight(in Tile t, double stand) => stand;

    // ================= Zones =================

    /// <summary>The zone of one of the level's cells: the Cellar, the Flood, or a Flood cell with a Dry Patch in its middle.</summary>
    public BasementZone BasementCellZone(int mx, int mz)
    {
        if (Fbm(mx / 6.0, mz / 6.0, SaltBasementZone) >= BasementWetBelow) return BasementZone.Cellar;
        return Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltBasementPatch)) < BasementPatchShare ? BasementZone.Patch : BasementZone.Flood;
    }

    /// <summary>The zone at a block position, by arithmetic (the Dry Patch is its room only; the passages round it are the Flood).</summary>
    public BasementZone BasementZoneAt(int x, int z)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        BasementZone zone = BasementCellZone(mx, mz);
        if (zone != BasementZone.Patch) return zone;
        int lx = x - mx * MacroSize, lz = z - mz * MacroSize;
        bool room = lx >= BasementPatchLo && lx <= BasementPatchHi && lz >= BasementPatchLo && lz <= BasementPatchHi;
        return room ? BasementZone.Patch : BasementZone.Flood;
    }

    private static bool BasementWet(BasementZone z) => z is BasementZone.Flood or BasementZone.Patch;

    /// <summary>
    /// The gaps in the wall line on the west (or north) side of cell (mx, mz), between two of the level's cells: the
    /// first index along the line of each (B is -1 when there is one), and how wide they are. Two Cellar cells: two gaps two
    /// wide, anywhere. Two wet cells: two of the four node lines, three wide (the passage's width). A Cellar and a wet cell:
    /// one node line, three wide, with the stair down on the wet side.
    /// </summary>
    private (int A, int B, int Width) BasementGaps(int mx, int mz, bool west)
    {
        int nx = west ? mx - 1 : mx, nz = west ? mz : mz - 1;
        bool dryHere = BasementCellZone(mx, mz) == BasementZone.Cellar, dryThere = BasementCellZone(nx, nz) == BasementZone.Cellar;
        ulong h = Hashing.Hash(seed, mx, mz, SaltBasementGap + (west ? 0UL : 1UL));
        if (dryHere && dryThere) return (3 + (int)(h % 11), 17 + (int)((h >> 12) % 12), 2);
        int i = (int)((h >> 24) % 4), j = (int)((h >> 36) % 3);
        if (j >= i) j++;
        int a = BasementNode0 - 1 + BasementPitch * i, b = BasementNode0 - 1 + BasementPitch * j;
        return dryHere || dryThere ? (a, -1, 3) : (a, b, 3);
    }

    private static bool InGap((int A, int B, int Width) g, int i) => i >= g.A && i < g.A + g.Width || g.B >= 0 && i >= g.B && i < g.B + g.Width;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells, with its gaps (see <see cref="BasementGaps"/>).</summary>
    private Edge BasementEdge(int mx, int mz, bool west)
    {
        var gaps = BasementGaps(mx, mz, west);
        bool wet = BasementWet(BasementCellZone(mx, mz)) && BasementWet(BasementCellZone(west ? mx - 1 : mx, west ? mz : mz - 1));
        var edge = new Edge { Pattern = wet ? WallPattern.BasementFloodWall : WallPattern.BasementCinder };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = InGap(gaps, i) ? EdgeTile.Open : EdgeTile.Wall;
        return edge;
    }

    /// <summary>One of a cell's four sides: whether the level goes on past it, whether the cell there is dry, and its gaps.</summary>
    private readonly struct BasementSide
    {
        public readonly bool Ours, Dry;
        public readonly (int A, int B, int Width) Gaps;
        public BasementSide(bool ours, bool dry, (int, int, int) gaps) { Ours = ours; Dry = dry; Gaps = gaps; }
    }

    /// <summary>The four sides of a cell: west, north, east, south.</summary>
    private BasementSide[] BasementSides(int mx, int mz)
    {
        var sides = new BasementSide[4];
        (int Nx, int Nz, int Ex, int Ez, bool West)[] at = { (mx - 1, mz, mx, mz, true), (mx, mz - 1, mx, mz, false), (mx + 1, mz, mx + 1, mz, true), (mx, mz + 1, mx, mz + 1, false) };
        for (int s = 0; s < 4; s++)
        {
            var (nx, nz, ex, ez, west) = at[s];
            bool ours = LevelAt(nx, nz) == Basement;
            sides[s] = new BasementSide(ours, ours && BasementCellZone(nx, nz) == BasementZone.Cellar, ours ? BasementGaps(ex, ez, west) : (-1, -1, 0));
        }
        return sides;
    }

    /// <summary>A tile of a side: the tile in this cell at index i along it, and the step inward (toward the cell's middle).</summary>
    private static (int X, int Z, int Dx, int Dz) BasementSideTile(int side, int i) => side switch
    {
        0 => (0, i, 1, 0),
        1 => (i, 0, 0, 1),
        2 => (MacroSize - 1, i, -1, 0),
        _ => (i, MacroSize - 1, 0, -1),
    };

    /// <summary>The way a step inward from a side climbs back out toward it.</summary>
    private static ArchPier BasementOutward(int side) => side switch { 0 => ArchPier.West, 1 => ArchPier.North, 2 => ArchPier.East, _ => ArchPier.South };

    /// <summary>Lays out one of the level's cells: Cellar rooms, or the Flood's maze (with a Dry Patch in some).</summary>
    private void BuildLevelBasement(Builder b, int mx, int mz)
    {
        BasementZone zone = BasementCellZone(mx, mz);
        BasementSide[] sides = BasementSides(mx, mz);
        if (zone == BasementZone.Cellar) BuildBasementCellar(b, mx, mz, sides);
        else BuildBasementFlood(b, mx, mz, sides, zone == BasementZone.Patch);
    }

    // ---- The Cellar ----

    private void BuildBasementCellar(Builder b, int mx, int mz, BasementSide[] sides)
    {
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementRooms));
        for (int i = 0; i < b.Tiles.Length; i++)
        {
            ref Tile t = ref b.Tiles[i];
            t.Zone = (byte)BasementZone.Cellar;
            t.Ceiling = CeilingKind.BasementCeiling;
            if (t.Kind != TileKind.Floor) continue;
            t.Floor = FloorKind.BasementFloor;
        }

        // Whether a tile beyond a wall's end is solid: the cell's own west and north lines are its tiles; past the east and
        // south lines, a gap there is open
        bool Solid(int x, int z)
        {
            if (x < 0 || z < 0) return true;
            if (x >= MacroSize) return !(sides[2].Ours && InGap(sides[2].Gaps, z));
            if (z >= MacroSize) return !(sides[3].Ours && InGap(sides[3].Gaps, x));
            return b.At(x, z).Kind == TileKind.Wall;
        }
        var rooms = new List<(int X0, int Z0, int X1, int Z1)>();
        BasementSplit(b, ref rng, Solid, 1, 1, MacroSize - 1, MacroSize - 1, rooms);

        // A landing inside every gap in the cell's sides, so no wall of the rooms ends across one
        for (int s = 0; s < 4; s++)
        {
            if (!sides[s].Ours) continue;
            for (int i = 1; i < MacroSize; i++)
            {
                if (!InGap(sides[s].Gaps, i)) continue;
                var (x, z, dx, dz) = BasementSideTile(s, i);
                for (int k = s < 2 ? 1 : 0; k <= (s < 2 ? 2 : 1); k++) BasementClear(ref b.At(x + dx * k, z + dz * k));
            }
        }

        // Furnish the rooms: a bulb in about one in two, a damp floor in some, crates, a boiler, a drum, a shelf
        var furnish = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementFurnish));
        bool Open(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z));
        foreach (var (x0, z0, x1, z1) in rooms)
        {
            int w = x1 - x0 + 1, h = z1 - z0 + 1;
            bool damp = furnish.Chance(0.3);
            for (int z = z0; z <= z1; z++)
                for (int x = x0; x <= x1; x++)
                {
                    ref Tile t = ref b.At(x, z);
                    if (t.Kind != TileKind.Floor) continue;
                    if (damp) t.Floor = FloorKind.BasementDamp;
                    if (furnish.Chance(damp ? 0.25 : 0.08)) t.Ceiling = CeilingKind.BasementStained;
                }
            int cx = x0 + w / 2, cz = z0 + h / 2;
            // A squat concrete pillar holding up the middle of a big room (the bulb then hangs beside it)
            bool pillar = w >= 9 && h >= 9 && furnish.Chance(0.6) && b.At(cx, cz).Kind == TileKind.Floor;
            if (pillar) SetWall(ref b.At(cx, cz), WallPattern.BasementPillar, BaseStyle.Plain);
            if (furnish.Chance(0.45))
            {
                ref Tile lamp = ref b.At(pillar ? cx + 1 : cx, cz);
                if (lamp.Kind == TileKind.Floor)
                {
                    double roll = furnish.NextDouble();
                    lamp.Ceiling = roll < 0.2 ? CeilingKind.BasementBulbOff : roll < 0.5 ? CeilingKind.BasementBulbFlicker : CeilingKind.BasementBulbOn;
                }
            }
            // Things against the walls, never where they would cut a way off, nor beside the cell's edges
            int things = furnish.Range(0, Math.Min(4, w * h / 30));
            for (int n = 0, tries = 0; n < things && tries < 24; tries++)
            {
                int x = furnish.Range(x0, x1), z = furnish.Range(z0, z1);
                if (x < 2 || z < 2 || x > MacroSize - 3 || z > MacroSize - 3) continue;
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0 || t.Ceiling is not (CeilingKind.BasementCeiling or CeilingKind.BasementStained)) continue;
                ArchPier? away = Solid(x - 1, z) ? ArchPier.East : Solid(x + 1, z) ? ArchPier.West : Solid(x, z - 1) ? ArchPier.South : Solid(x, z + 1) ? ArchPier.North : null;
                if (away == null || !SafeToBlock(Open, x, z)) continue;
                double roll = furnish.NextDouble();
                if (roll < 0.45) t.Stack = (byte)furnish.Range(1, 2);
                else if (roll < 0.6) t.Variant = Props.BasementBoiler;
                else if (roll < 0.75) t.Variant = Props.BasementDrum;
                else if (roll < 0.9) t.Variant = Props.BasementShelf;
                else t.Variant = Props.BasementCabinet;
                t.Pier = away.Value;
                n++;
            }
        }
    }

    /// <summary>Opens a tile of a Cellar cell back up to bare floor.</summary>
    private static void BasementClear(ref Tile t)
    {
        if (t.Kind == TileKind.Wall && t.Pattern is WallPattern.BasementCinder or WallPattern.BasementStained) t.Kind = TileKind.Floor;
        if (t.Kind != TileKind.Floor) return;
        t.Floor = FloorKind.BasementFloor;
        t.Variant = 0;
        t.Stack = 0;
    }

    /// <summary>
    /// Splits the inclusive rectangle into cellar rooms with walls one thick, each wall with a gap two wide (two in a
    /// long one), as a BSP tree, so every room can be reached from every other. A wall may not end against a gap.
    /// </summary>
    private static void BasementSplit(Builder b, ref Rng rng, Func<int, int, bool> solid, int x0, int z0, int x1, int z1,
        List<(int, int, int, int)> rooms)
    {
        const int minRoom = 5;
        int w = x1 - x0 + 1, h = z1 - z0 + 1, area = w * h;
        bool canX = w >= 2 * minRoom + 1, canZ = h >= 2 * minRoom + 1;
        double stop = area <= 80 ? 1 : area <= 160 ? 0.75 : area <= 300 ? 0.45 : 0;
        if (!canX && !canZ || rng.Chance(stop))
        {
            rooms.Add((x0, z0, x1, z1));
            return;
        }
        bool splitX = canX && (!canZ || rng.Chance(w >= h ? 0.75 : 0.25));
        int len = splitX ? w : h, across = splitX ? h : w;
        for (int attempt = 0; attempt < 6; attempt++)
        {
            int s = rng.Range(minRoom, len - 1 - minRoom);
            if (splitX ? !solid(x0 + s, z0 - 1) || !solid(x0 + s, z1 + 1) : !solid(x0 - 1, z0 + s) || !solid(x1 + 1, z0 + s)) continue;
            int gap = rng.Range(1, across - 3), gap2 = across >= 16 && rng.Chance(0.5) ? rng.Range(1, across - 3) : -1;
            for (int k = 0; k < across; k++)
            {
                if (k >= gap && k < gap + 2 || gap2 >= 0 && k >= gap2 && k < gap2 + 2) continue;
                SetWall(ref b.At(splitX ? x0 + s : x0 + k, splitX ? z0 + k : z0 + s), rng.Chance(0.12) ? WallPattern.BasementStained : WallPattern.BasementCinder, BaseStyle.Plain);
            }
            if (splitX)
            {
                BasementSplit(b, ref rng, solid, x0, z0, x0 + s - 1, z1, rooms);
                BasementSplit(b, ref rng, solid, x0 + s + 1, z0, x1, z1, rooms);
            }
            else
            {
                BasementSplit(b, ref rng, solid, x0, z0, x1, z0 + s - 1, rooms);
                BasementSplit(b, ref rng, solid, x0, z0 + s + 1, x1, z1, rooms);
            }
            return;
        }
        rooms.Add((x0, z0, x1, z1));
    }

    // ---- The Flood ----

    private void BuildBasementFlood(Builder b, int mx, int mz, BasementSide[] sides, bool patch)
    {
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementMaze));
        const int n = MacroSize / BasementPitch; // nodes each way
        static int Node(int k) => BasementNode0 + BasementPitch * k;
        var open = new bool[MacroSize * MacroSize];
        void Rect(int xa, int za, int xb, int zb)
        {
            for (int z = Math.Max(0, Math.Min(za, zb)); z <= Math.Min(MacroSize - 1, Math.Max(za, zb)); z++)
                for (int x = Math.Max(0, Math.Min(xa, xb)); x <= Math.Min(MacroSize - 1, Math.Max(xa, xb)); x++)
                    open[TileIndex(x, z)] = true;
        }
        static bool InPatch(int i, int j) => i is 1 or 2 && j is 1 or 2;
        bool InRoom(int x, int z) => patch && x > BasementPatchLo && x < BasementPatchHi && z > BasementPatchLo && z < BasementPatchHi;

        // A spanning tree over the nodes (a hash-ordered union-find over the links), a few more links for loops; a Dry
        // Patch's four middle nodes are its one room
        var parent = new int[n * n];
        for (int i = 0; i < parent.Length; i++) parent[i] = i;
        int Find(int a) { while (parent[a] != a) a = parent[a] = parent[parent[a]]; return a; }
        if (patch)
            foreach (int k in new[] { 1 * n + 2, 2 * n + 1, 2 * n + 2 }) parent[Find(k)] = Find(1 * n + 1);
        var links = new List<(int I, int J, bool AlongX, double Order)>();
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (i + 1 < n && !(patch && InPatch(i, j) && InPatch(i + 1, j))) links.Add((i, j, true, rng.NextDouble()));
                if (j + 1 < n && !(patch && InPatch(i, j) && InPatch(i, j + 1))) links.Add((i, j, false, rng.NextDouble()));
            }
        links.Sort((p, q) => p.Order.CompareTo(q.Order));
        var kept = new List<(int I, int J, bool AlongX)>();
        foreach (var (i, j, alongX, _) in links)
        {
            int a = Find(j * n + i), c = Find(alongX ? j * n + i + 1 : (j + 1) * n + i);
            if (a != c) { parent[c] = a; kept.Add((i, j, alongX)); }
            else if (rng.Chance(0.2)) kept.Add((i, j, alongX));
        }

        // The passages: every node's square, every kept link, and a stub out to each gap in the cell's sides
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
                if (!(patch && InPatch(i, j))) Rect(Node(i) - 1, Node(j) - 1, Node(i) + 1, Node(j) + 1);
        var entries = new List<(int X, int Z, int Dx, int Dz)>(); // a Dry Patch's doorway tiles, and the way out of it
        foreach (var (i, j, alongX) in kept)
        {
            int ax = Node(i), az = Node(j), bx = alongX ? Node(i + 1) : ax, bz = alongX ? az : Node(j + 1);
            if (patch && (InPatch(i, j) || InPatch(alongX ? i + 1 : i, alongX ? j : j + 1)))
            {
                // Into the room: from the outer node up to the room's wall
                bool fromLow = !InPatch(i, j); // the outer node is the low one (west or north)
                int wx = alongX ? (fromLow ? BasementPatchLo : BasementPatchHi) : ax, wz = alongX ? az : (fromLow ? BasementPatchLo : BasementPatchHi);
                if (alongX) Rect(fromLow ? ax : wx, az - 1, fromLow ? wx : bx, az + 1);
                else Rect(ax - 1, fromLow ? az : wz, ax + 1, fromLow ? wz : bz);
                int dx = alongX ? (fromLow ? -1 : 1) : 0, dz = alongX ? 0 : (fromLow ? -1 : 1);
                for (int k = -1; k <= 1; k++) entries.Add((alongX ? wx : wx + k, alongX ? wz + k : wz, dx, dz));
                continue;
            }
            if (alongX) Rect(ax, az - 1, bx, az + 1);
            else Rect(ax - 1, az, ax + 1, bz);
            // Pipes along the north (or west) side of the passage, between the nodes; now and then a leaking one
            ushort pipe = alongX ? (rng.Chance(0.15) ? Pipes.BasementLeakWE : Pipes.BasementPipeWE) : (rng.Chance(0.15) ? Pipes.BasementLeakNS : Pipes.BasementPipeNS);
            if (rng.Chance(0.7))
                for (int k = 2; k <= BasementPitch - 2; k++)
                    b.At(alongX ? ax + k : ax - 1, alongX ? az - 1 : az + k).Pipe = pipe;
        }
        var stairs = new List<(int X, int Z, int Dx, int Dz, int Side)>();
        for (int s = 0; s < 4; s++)
        {
            if (!sides[s].Ours) continue;
            var g = sides[s].Gaps;
            foreach (int start in g.B >= 0 ? new[] { g.A, g.B } : new[] { g.A })
            {
                int line = start + 1;
                var (x, z, dx, dz) = BasementSideTile(s, line);
                // From the side to the node on that line
                int outer = Node(s < 2 ? 0 : n - 1);
                if (s is 0 or 2) Rect(x, line - 1, outer, line + 1);
                else Rect(line - 1, z, line + 1, outer);
                if (!sides[s].Dry) continue;
                for (int k = -1; k <= 1; k++)
                {
                    var (sx, sz, _, _) = BasementSideTile(s, line + k);
                    stairs.Add((sx, sz, dx, dz, s));
                }
            }
        }

        // Lay it down: the passages flooded, everything else wall; the room dry, ringed by its walls
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                t.Ceiling = CeilingKind.BasementCeiling;
                if (InRoom(lx, lz))
                {
                    t.Kind = TileKind.Floor;
                    t.Zone = (byte)BasementZone.Patch;
                    t.Floor = FloorKind.BasementPatch;
                    t.Pipe = 0;
                    continue;
                }
                bool ring = patch && lx >= BasementPatchLo && lx <= BasementPatchHi && lz >= BasementPatchLo && lz <= BasementPatchHi;
                t.Zone = (byte)(ring ? BasementZone.Patch : BasementZone.Flood);
                if (ring)
                {
                    SetWall(ref t, WallPattern.BasementCinder, BaseStyle.Plain);
                    t.Pipe = 0;
                    continue;
                }
                // The cell's own west and north lines, where the edge laid a wall
                if ((lx == 0 || lz == 0) && t.Kind == TileKind.Wall) { t.Pipe = 0; continue; }
                if (open[TileIndex(lx, lz)])
                {
                    t.Kind = TileKind.Water;
                    t.Floor = FloorKind.BasementBed;
                }
                else
                {
                    SetWall(ref t, WallPattern.BasementFloodWall, BaseStyle.Plain);
                    t.Pipe = 0;
                }
            }

        // The doorways into the Dry Patch, and the steps up to them
        foreach (var (x, z, dx, dz) in entries)
        {
            ref Tile door = ref b.At(x, z);
            door.Kind = TileKind.Floor;
            door.Zone = (byte)BasementZone.Patch;
            door.Floor = FloorKind.BasementPatch;
            ArchPier toward = dx < 0 ? ArchPier.East : dx > 0 ? ArchPier.West : dz < 0 ? ArchPier.South : ArchPier.North;
            BasementStep(ref b.At(x + dx, z + dz), 2, toward);
            BasementStep(ref b.At(x + 2 * dx, z + 2 * dz), 1, toward);
        }
        // The stairs up out of the water to a Cellar cell
        foreach (var (x, z, dx, dz, s) in stairs)
        {
            BasementStep(ref b.At(x, z), 2, BasementOutward(s));
            BasementStep(ref b.At(x + dx, z + dz), 1, BasementOutward(s));
        }

        // A dim lamp over about one node in three (the Dry Patch has one bright bulb), dead now and then
        var furnish = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementFurnish));
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (patch && InPatch(i, j) || !furnish.Chance(0.32)) continue;
                ref Tile t = ref b.At(Node(i), Node(j));
                if (t.Kind == TileKind.Water && t.Height == 0) t.Ceiling = furnish.Chance(0.2) ? CeilingKind.BasementBulbOff : CeilingKind.BasementBulbDim;
            }
        if (!patch) return;
        const int mid = (BasementPatchLo + BasementPatchHi) / 2;
        b.At(mid, mid).Ceiling = CeilingKind.BasementBulbBright;
        // A pump, a boiler, a crate or two, a shelf and a drum round the room's walls: in its corners and the middles of its
        // sides, clear of the doorways (which are on the node lines)
        (int X, int Z, ArchPier Away)[] spots =
        {
            (BasementPatchLo + 1, BasementPatchLo + 1, ArchPier.South), (BasementPatchHi - 1, BasementPatchLo + 1, ArchPier.West),
            (BasementPatchLo + 1, BasementPatchHi - 1, ArchPier.East), (BasementPatchHi - 1, BasementPatchHi - 1, ArchPier.North),
            (mid, BasementPatchLo + 1, ArchPier.South), (BasementPatchLo + 1, mid, ArchPier.East),
            (mid + 1, BasementPatchHi - 1, ArchPier.North), (BasementPatchHi - 1, mid + 1, ArchPier.West),
        };
        ushort[] things = { Props.BasementPump, Props.BasementBoiler, 0, Props.BasementShelf, Props.BasementDrum };
        int first = furnish.Range(0, spots.Length - 1);
        for (int k = 0; k < things.Length; k++)
        {
            var (x, z, away) = spots[(first + k * 3) % spots.Length];
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0) continue;
            if (things[k] == 0) t.Stack = (byte)furnish.Range(1, 2);
            else t.Variant = things[k];
            t.Pier = away;
        }
    }

    /// <summary>Makes a flooded tile one of a stair's steps: 2 the upper (level with the dry floor), 1 the lower, climbing toward <paramref name="toward"/>.</summary>
    private static void BasementStep(ref Tile t, byte height, ArchPier toward)
    {
        if (t.Kind != TileKind.Water) return;
        t.Height = height;
        t.Pier = toward;
        t.Pipe = 0;
        t.Ceiling = CeilingKind.BasementCeiling;
    }

    /// <summary>Which of the level's props (<see cref="Props.BasementFirst"/>-<see cref="Props.BasementLast"/>) people walk through: none.</summary>
    private static bool BasementWalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: cold everywhere, colder down in the water, a little less so in the Dry Patch.</summary>
    private float BasementTemperature(int x, int y, int z, int floorY)
    {
        int rel = y - (floorY - WorldGeometry.BasementDrop);
        return BasementZoneAt(x, z) switch
        {
            BasementZone.Flood => rel <= 0 ? 4f : 5f,
            BasementZone.Patch => 9f,
            _ => 8f,
        };
    }

    /// <summary>Reality stability: steady in the Cellar, a slow drain out in the Flood (Level 2's), a little gain in the Dry Patch.</summary>
    private float BasementStability(double x, double y, double z, int floorY, float drift) => BasementZoneAt((int)Math.Floor(x), (int)Math.Floor(z)) switch
    {
        BasementZone.Flood => 0.7f + 0.2f * drift,
        BasementZone.Patch => 1.15f,
        _ => 1f + 0.05f * drift,
    };
}
