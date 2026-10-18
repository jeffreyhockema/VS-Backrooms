using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 3, "Electrical Station": a hot, cramped maze of derelict brick and glazed-tile maintenance halls fitted
/// with electrical machinery: groups of transformers, conductor coils, switchgear and industrial fans line the
/// corridors in niches, long cables sprawl along the walls and droop from the trays, outlets spark, and sparse
/// amber fixtures leave long stretches dark.
///
/// The hallways are "extremely inconsistent in their dimensions". Corridors follow a lattice, joined by a random
/// spanning tree that tends to run straight on (so the whole cell is connected) plus a few extra loops. In the tight
/// districts lanes are 2 wide every 8 blocks; in the wide districts, patches of cells a few across, they are galleries
/// 4 wide and 4 high every 16. Some links are 1-wide squeezes, half of them so low (two blocks) the ceiling all but
/// touches your head; many loops are blocked by indestructible white bars, so the way on is visible but out of reach.
/// The solid blocks between lanes hold electrical rooms, each with a small sign beside its door bearing a number and
/// jumbled text: machine rooms, generator rooms, control rooms, assembly lines, boiler rooms, supply caches and
/// freight elevators; behind bars, caged transformers, windows glowing with daylight, a worn statue among candles, a
/// pool of black sludge. In each region of five cells by five, two by two of them may be one vast hall, four high: a
/// transformer hall or an assembly line. Rarer still (one per eight by eight) is a Sanctum: a hushed gothic hall of
/// pale masonry with a statue of an angel at its heart. Manholes drop into flooded utility tunnels below the
/// corridors, where it is freezing.
/// </summary>
public sealed partial class WorldLayout
{
    private const int L3Lane = 3; // lanes occupy offsets 3 and 4 of each lattice period

    private const ulong SaltL3Material = 0x3C01;
    private const ulong SaltL3Wall = 0x3C02;
    private const ulong SaltL3Light = 0x3C03;
    private const ulong SaltL3Section = 0x3C04;
    private const ulong SaltL3Niche = 0x3C05;

    private const ulong SaltL3District = 0x3C07;
    private const ulong SaltL3Hall = 0x3C08;
    private const ulong SaltL3Sanctum = 0x3C09;
    /// <summary>Where something has been purpified into a wall (from layout version 5).</summary>
    private const ulong SaltL3Purpified = 0x3C0A;
    /// <summary>Vanilla machinery in the corridor niches (pressure tanks, old pumps) instead of the electrical gear.</summary>
    private const ulong SaltL3Fitting = 0x1E02;

    /// <summary>Halls: one site per this many cells each way.</summary>
    private const int L3HallRegion = 5;
    /// <summary>Sanctums: one per this many cells each way.</summary>
    private const int L3SanctumRegion = 8;

    private enum L3Room { Machine, Window, Cache, Elevator, Generator, Control, Assembly, Cage, Boiler, Shrine, Sludge }

    /// <summary>What a Level 3 cell is: a cramped tangle, a district of wide galleries, part of a hall, or a Sanctum.</summary>
    private enum L3Kind { Tight, Wide, TransformerHall, AssemblyHall, Sanctum }

    /// <summary>
    /// The lattice a cell's corridors follow: lanes every <paramref name="Pitch"/> blocks starting at offset 3, so
    /// lanes of tight and wide districts meet where they share a position.
    /// </summary>
    private static (int Nodes, int Pitch, int Width) L3Lattice(L3Kind kind) => kind == L3Kind.Wide ? (2, 16, 4) : (4, 8, 2);

    private L3Kind L3KindAt(int mx, int mz)
    {
        if (L3HallAt(mx, mz) is { } hall) return hall.Kind;
        if (IsL3Sanctum(mx, mz)) return L3Kind.Sanctum;
        // Districts come in patches a few cells across
        return Noise(mx / 5.0, mz / 5.0, SaltL3District) > 0.12 ? L3Kind.Wide : L3Kind.Tight;
    }

    /// <summary>
    /// The hall a cell is part of, if any: in each region of <see cref="L3HallRegion"/> cells each way, two cells by two
    /// at a place picked from the region, a vast room four blocks high (when all four cells are Level 3).
    /// </summary>
    private (L3Kind Kind, int X0, int Z0)? L3HallAt(int mx, int mz)
    {
        int rx = Hashing.FloorDiv(mx, L3HallRegion), rz = Hashing.FloorDiv(mz, L3HallRegion);
        ulong h = Hashing.Hash(seed, rx, rz, SaltL3Hall);
        if (Hashing.Unit(h) >= 0.75) return null;
        int x0 = rx * L3HallRegion + (int)((h >> 8) % (L3HallRegion - 1)), z0 = rz * L3HallRegion + (int)((h >> 16) % (L3HallRegion - 1));
        if (mx < x0 || mz < z0 || mx > x0 + 1 || mz > z0 + 1) return null;
        for (int dz = 0; dz <= 1; dz++)
            for (int dx = 0; dx <= 1; dx++)
                if (LevelAt(x0 + dx, z0 + dz) != 3) return null;
        return (Hashing.Unit(h << 24) < 0.6 ? L3Kind.TransformerHall : L3Kind.AssemblyHall, x0, z0);
    }

    /// <summary>A Sanctum: at most one cell in each region of <see cref="L3SanctumRegion"/> cells each way.</summary>
    private bool IsL3Sanctum(int mx, int mz)
    {
        int rx = Hashing.FloorDiv(mx, L3SanctumRegion), rz = Hashing.FloorDiv(mz, L3SanctumRegion);
        ulong h = Hashing.Hash(seed, rx, rz, SaltL3Sanctum);
        if (Hashing.Unit(h) >= 0.7) return false;
        if (mx != rx * L3SanctumRegion + (int)((h >> 8) % L3SanctumRegion) || mz != rz * L3SanctumRegion + (int)((h >> 16) % L3SanctumRegion)) return false;
        return LevelAt(mx, mz) == 3 && L3HallAt(mx, mz) == null;
    }

    private Edge Level3Edge(ref Rng rng, int mx, int mz, int nx, int nz)
    {
        var edge = new Edge { Pattern = Level3Material(mx, mz) };
        L3Kind a = L3KindAt(mx, mz), b = L3KindAt(nx, nz);
        // Within a hall there is no wall at all
        if (L3HallAt(mx, mz) is { } ha && L3HallAt(nx, nz) is { } hb && ha.X0 == hb.X0 && ha.Z0 == hb.Z0) return edge;
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;

        // Lanes cross the edge where both sides have one: every 8 blocks between tight districts, every 16 where a
        // wide one is involved, and the full width of a gallery between two wide ones. Halls and Sanctums are open
        // inside, so they take whatever the other side has. At least one always crosses.
        bool OpenInside(L3Kind k) => k is L3Kind.TransformerHall or L3Kind.AssemblyHall or L3Kind.Sanctum;
        L3Kind lattice = OpenInside(a) ? (OpenInside(b) ? L3Kind.Tight : b) : OpenInside(b) || a == b ? a : L3Kind.Wide;
        var (nodes, pitch, _) = L3Lattice(lattice);
        int width = a == L3Kind.Wide && b == L3Kind.Wide ? 4 : 2;
        int forced = rng.Range(0, nodes - 1);
        for (int k = 0; k < nodes; k++)
        {
            if (k != forced && !rng.Chance(0.55)) continue;
            for (int j = 0; j < width; j++) edge.Tiles[k * pitch + L3Lane + j] = EdgeTile.Open;
        }
        return edge;
    }

    private WallPattern Level3Material(int mx, int mz)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(mx, 3), Hashing.FloorDiv(mz, 3), SaltL3Material));
        return r < 0.6 ? WallPattern.GlazedTile : WallPattern.RedBrick;
    }

    private void BuildLevel3(Builder b, int mx, int mz, Edge west, Edge north)
    {
        ref Rng rng = ref b.Rng;
        var open = new bool[MacroSize * MacroSize];
        var bars = new List<(int X, int Z, ArchPier Plane)>();
        var rooms = new List<(int X0, int Z0, L3Room Kind, int DoorX, int DoorZ)>();
        WallPattern material = Level3Material(mx, mz);

        void Carve(int x0, int z0, int x1, int z1)
        {
            for (int z = Math.Min(z0, z1); z <= Math.Max(z0, z1); z++)
                for (int x = Math.Min(x0, x1); x <= Math.Max(x0, x1); x++)
                    if (x >= 1 && z >= 1 && x < MacroSize && z < MacroSize) open[TileIndex(x, z)] = true;
        }

        L3Kind kind = L3KindAt(mx, mz);
        if (kind == L3Kind.Sanctum)
        {
            BuildSanctum(b, mx, mz);
            return;
        }
        var (nodes, pitch, laneWidth) = L3Lattice(kind);
        int Lane(int i) => i * pitch + L3Lane;
        var low = new List<(int X0, int Z0, int X1, int Z1)>();

        if (kind is L3Kind.TransformerHall or L3Kind.AssemblyHall)
        {
            BuildL3Hall(b, mx, mz, kind, Carve);
        }
        else
        {
            // Spanning tree over the lattice nodes, by randomised depth-first search that tends to run straight on
            var visited = new bool[nodes * nodes];
            var stack = new Stack<(int Node, int Dir)>();
            var tree = new HashSet<(int, int)>();
            int start = rng.Range(0, nodes * nodes - 1);
            visited[start] = true;
            stack.Push((start, -1));
            var options = new List<(int Next, int Dir)>(4);
            while (stack.Count > 0)
            {
                var (node, dir) = stack.Peek();
                int nx = node % nodes, nz = node / nodes;
                options.Clear();
                if (nx > 0 && !visited[node - 1]) options.Add((node - 1, 0));
                if (nx < nodes - 1 && !visited[node + 1]) options.Add((node + 1, 1));
                if (nz > 0 && !visited[node - nodes]) options.Add((node - nodes, 2));
                if (nz < nodes - 1 && !visited[node + nodes]) options.Add((node + nodes, 3));
                if (options.Count == 0) { stack.Pop(); continue; }
                int straight = options.FindIndex(o => o.Dir == dir);
                var pick = straight >= 0 && rng.Chance(0.7) ? options[straight] : options[rng.Range(0, options.Count - 1)];
                visited[pick.Next] = true;
                tree.Add((Math.Min(node, pick.Next), Math.Max(node, pick.Next)));
                stack.Push((pick.Next, pick.Dir));
            }

            for (int node = 0; node < nodes * nodes; node++)
            {
                int ix = node % nodes, iz = node / nodes;
                Carve(Lane(ix), Lane(iz), Lane(ix) + laneWidth - 1, Lane(iz) + laneWidth - 1);
                foreach (int other in new[] { ix < nodes - 1 ? node + 1 : -1, iz < nodes - 1 ? node + nodes : -1 })
                {
                    if (other < 0) continue;
                    bool inTree = tree.Contains((node, other));
                    if (!inTree && !rng.Chance(0.25)) continue;
                    int ox = other % nodes, oz = other / nodes;
                    // Tree links are sometimes one-wide squeezes, and half of those so low you must stoop through;
                    // extra loops are often barred off
                    bool squeeze = inTree && rng.Chance(0.15);
                    int width = squeeze ? 0 : laneWidth - 1;
                    Carve(Lane(ix), Lane(iz), Lane(ox) + width, Lane(oz) + width);
                    if (squeeze && rng.Chance(0.5))
                        low.Add(ox != ix ? (Lane(ix) + laneWidth, Lane(iz), Lane(ox) - 1, Lane(iz)) : (Lane(ix), Lane(iz) + laneWidth, Lane(ix), Lane(oz) - 1));
                    if (!inTree && rng.Chance(0.5))
                    {
                        int midX = (Lane(ix) + Lane(ox)) / 2 + 1, midZ = (Lane(iz) + Lane(oz)) / 2 + 1;
                        // Bars stand across the corridor: a north-south plane across a west-east corridor and vice versa
                        for (int j = 0; j < laneWidth; j++)
                        {
                            if (ox != ix) bars.Add((midX, Lane(iz) + j, ArchPier.North));
                            else bars.Add((Lane(ix) + j, midZ, ArchPier.West));
                        }
                    }
                }
            }

            // Electrical rooms in the solid blocks between lanes: one between each pair of tight lanes, four in each
            // wide block
            var sites = new List<(int, int)>();
            if (kind == L3Kind.Wide)
            {
                foreach (int z0 in new[] { 8, 14 })
                    foreach (int x0 in new[] { 8, 14 })
                        sites.Add((x0, z0));
            }
            else
            {
                for (int cz = 0; cz < nodes - 1; cz++)
                    for (int cx = 0; cx < nodes - 1; cx++)
                        sites.Add((Lane(cx) + 3, Lane(cz) + 3)); // 4x4 interior inside a 6x6 solid block
            }
            foreach ((int x0, int z0) in sites)
            {
                if (!rng.Chance(kind == L3Kind.Wide ? 0.55 : 0.42)) continue;
                double r = rng.NextDouble();
                L3Room roomKind = r < 0.27 ? L3Room.Machine : r < 0.35 ? L3Room.Window : r < 0.45 ? L3Room.Cache
                    : r < 0.52 ? L3Room.Elevator : r < 0.60 ? L3Room.Generator : r < 0.68 ? L3Room.Control
                    : r < 0.76 ? L3Room.Assembly : r < 0.83 ? L3Room.Boiler : r < 0.88 ? L3Room.Cage
                    : r < 0.94 ? L3Room.Shrine : L3Room.Sludge;
                // The door faces whichever neighbouring lane exists
                bool Lit(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && open[TileIndex(x, z)];
                (int dx, int dz) door = Lit(x0 + 1, z0 - 2) ? (x0 + 1, z0 - 1)
                    : Lit(x0 + 2, z0 + 5) ? (x0 + 2, z0 + 4)
                    : Lit(x0 - 2, z0 + 1) ? (x0 - 1, z0 + 1)
                    : Lit(x0 + 5, z0 + 2) ? (x0 + 4, z0 + 2) : (-1, -1);
                if (door.dx < 0) continue;
                if (roomKind != L3Room.Elevator) Carve(x0, z0, x0 + 3, z0 + 3);
                rooms.Add((x0, z0, roomKind, door.dx, door.dz));
            }
        }

        // Every passage in the edges connects inward to the nearest lattice node
        void ConnectPassage(int x, int z, int dx, int dz)
        {
            int nodeX = Math.Clamp((int)Math.Round((x - L3Lane) / (double)pitch), 0, nodes - 1);
            int nodeZ = Math.Clamp((int)Math.Round((z - L3Lane) / (double)pitch), 0, nodes - 1);
            int tx = Lane(nodeX), tz = Lane(nodeZ);
            if (dx != 0) { Carve(x, z, tx, z); Carve(tx, z, tx, tz); }
            else { Carve(x, z, x, tz); Carve(x, tz, tx, tz); }
        }
        foreach (int i in Passages(west)) { open[TileIndex(0, i)] = true; ConnectPassage(1, i, 1, 0); }
        foreach (int i in Passages(north)) { open[TileIndex(i, 0)] = true; ConnectPassage(i, 1, 0, 1); }
        foreach (int i in Passages(GetEdge(mx + 1, mz, west: true))) ConnectPassage(MacroSize - 1, i, -1, 0);
        foreach (int i in Passages(GetEdge(mx, mz + 1, west: false))) ConnectPassage(i, MacroSize - 1, 0, -1);

        // Solidify; some stretches of corridor are floored with steel grating. Galleries and halls are four high.
        bool tall = kind != L3Kind.Tight;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (tile.Floor != FloorKind.L3Hazard)
                {
                    bool grated = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 8), Hashing.FloorDiv(gz, 8), SaltL3Section + 7)) < 0.18;
                    tile.Floor = grated ? FloorKind.Grate : FloorKind.Dusty;
                }
                if (tile.Kind != TileKind.Floor) continue;
                if (!open[TileIndex(lx, lz)]) SetWall(ref tile, material, BaseStyle.Plain);
                else if (tall) tile.Grand = true;
            }
        }
        foreach ((int x0, int z0, int x1, int z1) in low)
            for (int z = z0; z <= z1; z++)
                for (int x = x0; x <= x1; x++)
                    if (InInterior(x, z) && b.At(x, z).Kind == TileKind.Floor) { b.At(x, z).Low = true; b.At(x, z).Grand = false; }
        foreach ((int x, int z, ArchPier plane) in bars)
        {
            if (!InInterior(x, z) || b.At(x, z).Kind != TileKind.Floor) continue;
            if (rooms.Exists(r => Math.Abs(r.DoorX - x) + Math.Abs(r.DoorZ - z) <= 1)) continue;
            b.At(x, z).Kind = TileKind.Bars;
            b.At(x, z).Pier = plane;
            // A plaque on the wall beside some of them: OUT OF BOUNDS, DO NOT ENTER
            foreach ((int dx, int dz, ArchPier toward) in new[] { (1, 0, ArchPier.West), (-1, 0, ArchPier.East), (0, 1, ArchPier.North), (0, -1, ArchPier.South) })
            {
                if (!InInterior(x + dx, z + dz)) continue;
                ref Tile wall = ref b.At(x + dx, z + dz);
                if (wall.Kind != TileKind.Wall || wall.Variant != 0 || wall.Pattern is not (WallPattern.GlazedTile or WallPattern.RedBrick or WallPattern.Cinder)) continue;
                if (Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + x, mz * MacroSize + z, SaltL3Section + 11)) < 0.5)
                {
                    wall.Variant = Decor.Plaque;
                    wall.Pier = toward;
                }
                break;
            }
        }
        foreach (var room in rooms) FurnishLevel3Room(b, room.X0, room.Z0, room.Kind, room.DoorX, room.DoorZ);

        CarveMachineNiches(b, mx, mz);
        DecorateLevel3(b, mx, mz);
        if (kind is L3Kind.Tight or L3Kind.Wide && rng.Chance(0.3)) AddFloodedTunnel(b);
    }

    /// <summary>
    /// A quarter of a hall, two cells by two and four blocks high: a transformer hall, rows of transformers and coils
    /// on striped floors; or an assembly line, long conveyors running the length of the hall with parcels on them.
    /// The rows are laid out from block positions, so they run on unbroken from one cell of the hall to the next.
    /// </summary>
    private void BuildL3Hall(Builder b, int mx, int mz, L3Kind kind, Action<int, int, int, int> carve)
    {
        ref Rng rng = ref b.Rng;
        carve(1, 1, MacroSize - 1, MacroSize - 1);
        // Within the hall the cell lines are open; keep a walkway clear along the hall's own outer walls
        var (_, hx0, hz0) = L3HallAt(mx, mz).Value;
        int ox = hx0 * MacroSize, oz = hz0 * MacroSize;
        bool Margin(int gx, int gz) => gx - ox < 3 || gz - oz < 3 || ox + 2 * MacroSize - 1 - gx < 3 || oz + 2 * MacroSize - 1 - gz < 3;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz, ux = gx - ox, uz = gz - oz;
                if (Margin(gx, gz)) continue;
                ref Tile t = ref b.At(lx, lz);
                if (kind == L3Kind.TransformerHall)
                {
                    // Machines on a 6 x 5 grid, each on its own patch of hazard stripes
                    if (Hashing.Mod(ux, 6) == 4 && Hashing.Mod(uz, 5) == 3)
                    {
                        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Hall + 1));
                        if (r >= 0.8) continue;
                        t.Variant = r < 0.25 ? Props.Coil : Props.Transformer;
                        for (int dz = -1; dz <= 1; dz++)
                            for (int dx = -1; dx <= 1; dx++)
                                if (InCell(lx + dx, lz + dz)) b.At(lx + dx, lz + dz).Floor = FloorKind.L3Hazard;
                    }
                }
                else
                {
                    // Conveyor lines along the hall, a gap every twelve blocks to cross them; switchgear at the ends
                    int row = Hashing.Mod(uz, 7);
                    if (row is 3 or 4 && Hashing.Mod(ux, 12) is not (0 or 1))
                    {
                        t.Variant = Props.Conveyor;
                        t.Pier = ArchPier.East;
                        t.Stack = (byte)(Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Hall + 2)) < 0.35 ? 1 : 0);
                    }
                    else if (row == 6 && Hashing.Mod(ux, 12) == 6 && Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Hall + 3)) < 0.5)
                    {
                        t.Variant = Props.CardboardBoxes;
                        t.Pier = ArchPier.North;
                    }
                }
            }
        static bool InCell(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize;
    }

    private static void FurnishLevel3Room(Builder b, int x0, int z0, L3Room kind, int doorX, int doorZ)
    {
        ref Rng rng = ref b.Rng;
        // Which way the door looks out into the corridor, and the room's back wall
        ArchPier outward = doorZ < z0 ? ArchPier.North : doorZ > z0 + 3 ? ArchPier.South : doorX < x0 ? ArchPier.West : ArchPier.East;
        ArchPier inward = Opposite(outward);

        if (kind == L3Room.Elevator)
        {
            // A freight elevator set into the corridor wall
            ref Tile elevator = ref b.At(doorX, doorZ);
            elevator.Kind = TileKind.Door;
            elevator.Pattern = WallPattern.Elevator;
            return;
        }
        // Cinder-block walls round the room
        for (int z = z0 - 1; z <= z0 + 4; z++)
            for (int x = x0 - 1; x <= x0 + 4; x++)
            {
                ref Tile wall = ref b.At(x, z);
                if (wall.Kind == TileKind.Wall) wall.Pattern = WallPattern.Cinder;
            }

        // The tiles of the room, by depth from the door (0 = just inside, 3 = back wall) and position across it
        (int X, int Z) Spot(int depth, int across)
        {
            return outward switch
            {
                ArchPier.North => (x0 + across, z0 + depth),
                ArchPier.South => (x0 + across, z0 + 3 - depth),
                ArchPier.West => (x0 + depth, z0 + across),
                _ => (x0 + 3 - depth, z0 + across),
            };
        }
        ref Tile At((int X, int Z) p) => ref b.At(p.X, p.Z);

        ref Tile door = ref b.At(doorX, doorZ);
        if (kind is L3Room.Window or L3Room.Cage or L3Room.Shrine or L3Room.Sludge)
        {
            // Barred off: daylight from a far window, or a transformer kept in a cage
            door.Kind = TileKind.Bars;
            door.Pier = outward is ArchPier.North or ArchPier.South ? ArchPier.West : ArchPier.North;
            for (int z = z0; z <= z0 + 3; z++)
                for (int x = x0; x <= x0 + 3; x++)
                    b.At(x, z).Sealed = true;
            if (kind == L3Room.Window)
            {
                for (int k = 0; k < 4; k++) At(Spot(3, k)).Variant = Props.WindowGlow;
            }
            else if (kind == L3Room.Shrine)
            {
                // A worn statue, out of reach, with candles still burning either side of it
                At(Spot(2, 1)).Variant = Props.AngelStatue;
                At(Spot(2, 1)).Pier = outward;
                At(Spot(3, 0)).Variant = Props.Candelabra;
                At(Spot(3, 3)).Variant = Props.Candelabra;
                for (int d = 0; d <= 3; d++)
                    for (int k = 0; k < 4; k++)
                        At(Spot(d, k)).Floor = FloorKind.L3Stone;
            }
            else if (kind == L3Room.Sludge)
            {
                // A pool of the black sludge, fed from a pipe, filling the room
                for (int d = 1; d <= 3; d++)
                    for (int k = 0; k < 4; k++)
                        At(Spot(d, k)).Floor = FloorKind.Tar;
                At(Spot(3, 0)).Variant = Props.PipeStack;
                At(Spot(3, 0)).Pier = outward;
                PlaceNumberSign(b, doorX, doorZ, outward, ref rng);
            }
            else
            {
                At(Spot(2, 1)).Variant = Props.Transformer;
                At(Spot(2, 2)).Variant = Props.Coil;
                for (int d = 1; d <= 3; d++)
                    for (int k = 0; k < 4; k++)
                        At(Spot(d, k)).Floor = FloorKind.L3Hazard;
                PlaceNumberSign(b, doorX, doorZ, outward, ref rng);
            }
            return;
        }

        SetWall(ref door, WallPattern.Cinder, BaseStyle.Plain);
        door.Kind = TileKind.Doorway;
        PlaceNumberSign(b, doorX, doorZ, outward, ref rng);
        At(Spot(1, 1)).Ceiling = rng.Chance(0.35) ? CeilingKind.LightOff : CeilingKind.LightWarm;
        At(Spot(1, 1)).Pipe = outward is ArchPier.North or ArchPier.South ? Pipes.CableZ : Pipes.CableX;

        void Face(int depth, int across, byte prop, ArchPier facing)
        {
            ref Tile t = ref At(Spot(depth, across));
            t.Variant = prop;
            t.Pier = facing;
        }

        switch (kind)
        {
            case L3Room.Machine:
                // Switchgear along the back wall, transformers either side, cables over the floor
                Face(3, 0, Props.Transformer, outward);
                Face(3, 1, Props.Switchgear, outward);
                Face(3, 2, Props.Switchgear, outward);
                Face(3, 3, Props.Transformer, outward);
                if (rng.Chance(0.5)) Face(1, 3, Props.Coil, outward);
                if (rng.Chance(0.4)) At(Spot(1, 0)).SupplyBox = true;
                break;
            case L3Room.Cache:
                // Level 3 is said to be rich in loot
                At(Spot(3, 0)).SupplyBox = true;
                At(Spot(3, 3)).SupplyBox = true;
                At(Spot(2, 3)).Stack = 2;
                Face(3, 1, Props.Shelf, inward);
                Face(3, 2, Props.Shelf, inward);
                if (rng.Chance(0.5)) Face(1, 0, Props.CableSpool, outward);
                break;
            case L3Room.Boiler:
                // Boilers against the back wall, and the black sludge they make, scalding, pooled along one side
                Face(3, 1, Props.Boiler, outward);
                Face(3, 2, Props.Boiler, outward);
                for (int d = 1; d <= 3; d++) At(Spot(d, 3)).Floor = FloorKind.Tar;
                Face(1, 0, Props.PipeStack, outward);
                if (rng.Chance(0.5)) Face(3, 0, Props.Drum, outward);
                // Their gauges and valves on the side wall, and a pressure tank in the corner the drum left empty
                // (chosen from the room's position, not the shared random sequence, so nothing else moves)
                Face(2, 0, Props.GaugeFrame, Toward(Spot(2, 0), Spot(2, 1)));
                At(Spot(2, 0)).Stack = (byte)Hashing.Mod(x0 * 7 + z0 * 13, 4);
                if (At(Spot(3, 0)).Variant == 0)
                {
                    Face(3, 0, Props.PressureTank, outward);
                    At(Spot(3, 0)).Stack = (byte)Hashing.Mod(x0 + z0, 2);
                }
                break;
            case L3Room.Generator:
                Face(2, 1, Props.Generator, outward);
                Face(1, 2, Props.CoalPile, outward); // the generator's coal, enough to smelt with
                Face(3, 3, Props.Drum, outward);
                Face(2, 3, Props.Drum, outward);
                Face(3, 0, Props.FloorFan, outward);
                for (int d = 1; d <= 3; d++)
                    for (int k = 0; k <= 2; k++)
                        if (At(Spot(d, k)).Variant == 0) At(Spot(d, k)).Floor = FloorKind.L3Hazard;
                break;
            case L3Room.Control:
                // An operator's desk facing the meters on the back wall
                Face(3, 1, Props.ControlDesk, outward);
                Face(3, 2, Props.ControlDesk, outward);
                Face(2, 1, Props.OfficeChair, inward);
                Face(3, 0, Props.Switchgear, outward);
                Face(3, 3, Props.Switchgear, outward);
                // The levers that worked whatever the meters measured, and gauges on the side wall (both in corners
                // nothing passes through)
                Face(2, 3, Props.FloorLever, outward);
                At(Spot(2, 3)).Stack = (byte)Hashing.Mod(x0 + z0, 2);
                Face(2, 0, Props.GaugeFrame, Toward(Spot(2, 0), Spot(2, 1)));
                At(Spot(2, 0)).Stack = (byte)Hashing.Mod(x0 * 5 + z0 * 3, 4);
                break;
            case L3Room.Assembly:
                // Two conveyor lines crossing the room, still carrying parcels to nowhere
                for (int k = 0; k < 4; k++)
                {
                    ArchPier along = outward is ArchPier.North or ArchPier.South ? ArchPier.North : ArchPier.East;
                    Face(2, k, Props.Conveyor, along);
                    At(Spot(2, k)).Stack = (byte)(rng.Chance(0.5) ? 1 : 0);
                    if (k is 0 or 3) continue;
                    Face(3, k, Props.Conveyor, along);
                    At(Spot(3, k)).Stack = (byte)(rng.Chance(0.4) ? 1 : 0);
                }
                Face(3, 0, Props.CardboardBoxes, outward);
                Face(3, 3, Props.Switchgear, outward);
                break;
        }
    }

    /// <summary>The direction from one tile to its neighbour.</summary>
    private static ArchPier Toward((int X, int Z) from, (int X, int Z) to) =>
        to.X > from.X ? ArchPier.East : to.X < from.X ? ArchPier.West : to.Z > from.Z ? ArchPier.South : ArchPier.North;

    /// <summary>The small sign beside an electrical room's door: a number and a line of jumbled text.</summary>
    private static void PlaceNumberSign(Builder b, int doorX, int doorZ, ArchPier outward, ref Rng rng)
    {
        byte sign = (byte)(Decor.RoomSign + rng.Range(0, 7));
        bool alongX = outward is ArchPier.North or ArchPier.South;
        foreach (int side in new[] { 1, -1 })
        {
            int x = alongX ? doorX + side : doorX, z = alongX ? doorZ : doorZ + side;
            if (!InInterior(x, z)) continue;
            ref Tile wall = ref b.At(x, z);
            if (wall.Kind != TileKind.Wall) continue;
            wall.Variant = sign;
            wall.Pier = outward;
            return;
        }
    }

    /// <summary>
    /// Machinery lines the corridors: niches one block deep cut into the solid walls hold transformers, conductor
    /// coils, switchgear, fans, generators and cable spools, on striped floors.
    /// </summary>
    private void CarveMachineNiches(Builder b, int mx, int mz)
    {
        bool Floor(int x, int z) => b.At(x, z).Kind == TileKind.Floor && b.At(x, z).Variant == 0 && !b.At(x, z).Sealed;
        bool Solid(int x, int z) => b.At(x, z).Kind == TileKind.Wall;

        for (int lz = 2; lz < MacroSize - 2; lz++)
        {
            for (int lx = 2; lx < MacroSize - 2; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Wall || tile.Pattern == WallPattern.Cinder || tile.Variant != 0) continue;
                double r = Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltL3Niche));
                if (r > 0.12) continue;
                foreach (ArchPier dir in new[] { ArchPier.North, ArchPier.South, ArchPier.East, ArchPier.West })
                {
                    var (ox, oz) = Step(lx, lz, dir);
                    var (bx, bz) = Step(lx, lz, Opposite(dir));
                    var (bx2, bz2) = Step(bx, bz, Opposite(dir));
                    var (sx, sz) = Step(lx, lz, Turn(dir));
                    var (tx, tz) = Step(lx, lz, Opposite(Turn(dir)));
                    if (!Floor(ox, oz) || !Solid(bx, bz) || !Solid(sx, sz) || !Solid(tx, tz)) continue;
                    if (bx2 >= 0 && bz2 >= 0 && bx2 < MacroSize && bz2 < MacroSize && !Solid(bx2, bz2)) continue;
                    if (b.At(bx, bz).Pattern == WallPattern.Cinder) continue;
                    tile.Kind = TileKind.Floor;
                    tile.Floor = FloorKind.L3Hazard;
                    tile.Pier = dir;
                    double m = r / 0.12;
                    tile.Variant = m < 0.3 ? Props.Coil : m < 0.55 ? Props.Switchgear : m < 0.72 ? Props.Transformer
                        : m < 0.82 ? Props.FloorFan : m < 0.92 ? Props.Generator : Props.CableSpool;
                    // One niche in four holds older plant: a rusted pressure tank or the remains of a pump
                    ulong fit = Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltL3Fitting);
                    if (Hashing.Unit(fit) < 0.25)
                    {
                        tile.Variant = ((fit >> 20) & 1) == 0 ? Props.PressureTank : Props.RustMachine;
                        tile.Stack = (byte)((fit >> 28) & 1);
                    }
                    tile.Sealed = true;
                    break;
                }
            }
        }
    }

    private void DecorateLevel3(Builder b, int mx, int mz)
    {
        bool InCell(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize;
        bool IsOpen(int x, int z) => InCell(x, z) && b.At(x, z).Kind is TileKind.Floor or TileKind.Bars;
        bool IsWalkway(int x, int z) => InCell(x, z) && b.At(x, z).Kind == TileKind.Floor && b.At(x, z).Variant == 0;
        // Near Level 2 the overhead runs are still pipes; deeper in they are cable bundles (up to layout version 8; from 9
        // they are cable bundles right up to Level 2's wall)
        bool pipes = Version < 9 && TouchesLevel(mx, mz, 2);

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                ulong h = Hashing.Hash(seed, gx, gz, SaltL3Wall);
                double r = Hashing.Unit(h);
                bool e = IsOpen(lx + 1, lz), w = IsOpen(lx - 1, lz), s = IsOpen(lx, lz + 1), n = IsOpen(lx, lz - 1);

                if (tile.Kind == TileKind.Wall)
                {
                    if (tile.Variant != 0 || !(e || w || s || n)) continue;
                    // Facing a walkway: oriented equipment. Long stretches carry pipe runs and cable bundles.
                    ArchPier? face = IsWalkway(lx, lz - 1) ? ArchPier.North : IsWalkway(lx, lz + 1) ? ArchPier.South
                        : IsWalkway(lx + 1, lz) ? ArchPier.East : IsWalkway(lx - 1, lz) ? ArchPier.West : null;
                    double stretch = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 8), Hashing.FloorDiv(gz, 8), SaltL3Wall + 1));
                    if (face == null)
                    {
                        // Only open to bars or machinery: fittings that work from any side
                        tile.Variant = stretch < 0.45 ? Props.WallPipes : r < 0.32 ? Props.WallPanel : Props.WallPlain;
                        continue;
                    }
                    tile.Pier = face.Value;
                    tile.Variant = r < 0.035 ? Decor.Bulkhead : r < 0.06 ? Decor.DangerSign : r < 0.085 ? Decor.Gauges
                        : r < 0.1 ? Decor.KnifeSwitch : r < 0.125 ? Decor.JunctionBox : r < 0.137 ? Decor.SparkOutlet
                        : r < 0.145 ? Decor.AlarmBell : r < 0.16 ? Decor.Risers
                        : stretch < 0.45 ? Props.WallPipes : stretch < 0.62 ? Decor.WallCables
                        : r < 0.32 ? Props.WallPanel : r < 0.42 ? Props.WallFan : Props.WallPlain;
                    // From layout version 5, very rarely: something dead half noclipped into the wall, it and the wall
                    // round it gone purple ("Only 17 instances of Purpification have been encountered", Wikidot)
                    if (Version >= 5 && Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Purpified)) < 0.00025) tile.Variant = Decor.Purpified;
                    continue;
                }
                if (tile.Kind != TileKind.Floor || tile.Sealed) continue;

                bool alongX = e && w && !(s && n) || (e ^ w) && !s && !n;
                bool alongZ = s && n && !(e && w) || (s ^ n) && !e && !w;
                bool fixture;
                if (tile.Grand)
                {
                    // Galleries and halls: cable runs along the walls, lights down the middle
                    bool wallX = !n || !s, wallZ = !e || !w;
                    alongX = wallX && !wallZ;
                    alongZ = wallZ && !wallX;
                    if (tile.Pipe == 0 && (alongX || alongZ))
                        tile.Pipe = pipes ? (alongX ? Pipes.RunX : Pipes.RunZ) : alongX ? Pipes.CableX : Pipes.CableZ;
                    fixture = !wallX && !wallZ && Hashing.Mod(gx, 6) == 0 && Hashing.Mod(gz, 6) == 0;
                }
                else
                {
                    if (tile.Pipe == 0 && !tile.Low)
                    {
                        bool droop = Hashing.Unit(h << 16) < 0.07;
                        tile.Pipe = pipes
                            ? (alongX ? Pipes.RunX : alongZ ? Pipes.RunZ : Pipes.Hub)
                            : (alongX ? (droop ? Pipes.CableDroopX : Pipes.CableX) : alongZ ? (droop ? Pipes.CableDroopZ : Pipes.CableZ) : Pipes.CableHub);
                    }
                    fixture = !tile.Low && (alongX ? Hashing.Mod(gx, 7) == 0 : alongZ && Hashing.Mod(gz, 7) == 0);
                }

                // Sparse amber fixtures; about half are dead, and a whole stretch of corridor goes out at once
                if (fixture && tile.Pipe is not (Pipes.CableDroopX or Pipes.CableDroopZ))
                {
                    double section = tile.Grand
                        ? Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 24), Hashing.FloorDiv(gz, 24), SaltL3Section))
                        : alongX ? Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gz, 8), Hashing.FloorDiv(gx, 24), SaltL3Section + 1))
                        : Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 8), Hashing.FloorDiv(gz, 24), SaltL3Section + 2));
                    double light = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Light));
                    tile.Ceiling = section < 0.35 ? CeilingKind.LightOff
                        : light < 0.3 ? CeilingKind.LightOff : light < 0.42 ? CeilingKind.LightFlicker : CeilingKind.LightWarm;
                }

                if (tile.Variant != 0) continue;
                int neighbours = (e ? 1 : 0) + (w ? 1 : 0) + (s ? 1 : 0) + (n ? 1 : 0);
                if (neighbours == 1 && r > 0.8) tile.SupplyBox = true;
                // Cables trail across the floor from the machinery, and things are left lying about
                else if ((alongX || alongZ) && r < 0.05)
                {
                    tile.Variant = Props.FloorCable;
                    tile.Pier = alongX ? ArchPier.North : ArchPier.East;
                }
                else if ((alongX || alongZ) && r > 0.993 && SafeToBlock(IsWalkway, lx, lz))
                {
                    tile.Variant = r > 0.997 ? Props.PipeStack : Props.Drum;
                    tile.Pier = alongX ? ArchPier.North : ArchPier.East;
                }
            }
        }
    }

    /// <summary>
    /// A Sanctum: a gothic hall of pale ashlar out of all keeping with the rest of the level, with a red carpet
    /// leading between rows of columns and candelabra to a winged statue on a pedestal. Nothing else: no pews, no
    /// organ, no altar.
    /// </summary>
    private void BuildSanctum(Builder b, int mx, int mz)
    {
        const int c = MacroSize / 2;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                tile.Floor = Math.Abs(lx - c) <= 1 ? FloorKind.SanctumCarpet : FloorKind.L3Stone;
                if (tile.Kind != TileKind.Floor || lx == 0 || lz == 0) continue;
                // Columns down both sides of the nave and round the edge
                bool colonnade = (lx == c - 6 || lx == c + 6) && lz % 4 == 2 && lz > 2 && lz < MacroSize - 3;
                bool aisle = (lx == 4 || lx == MacroSize - 4) && lz % 4 == 0 && lz > 2;
                if (colonnade || aisle)
                {
                    SetWall(ref tile, WallPattern.Stone, BaseStyle.Plain);
                    if (colonnade && lz % 8 == 2)
                    {
                        tile.Variant = Decor.Bulkhead;
                        tile.Pier = lx < c ? ArchPier.East : ArchPier.West;
                    }
                    continue;
                }
                // Candelabra line the carpet
                if ((lx == c - 2 || lx == c + 2) && lz % 4 == 0 && lz > 4 && lz < MacroSize - 4) tile.Variant = Props.Candelabra;
            }
        }
        // The statue at the head of the nave, facing down it
        ref Tile statue = ref b.At(c, 6);
        statue.Variant = Props.AngelStatue;
        statue.Pier = ArchPier.South;
        b.At(c - 1, 6).Variant = Props.Candelabra;
        b.At(c + 1, 6).Variant = Props.Candelabra;
        // The cell's own two edge walls are masonry too
        for (int i = 0; i < MacroSize; i++)
        {
            if (b.At(0, i).Kind == TileKind.Wall) b.At(0, i).Pattern = WallPattern.Stone;
            if (b.At(i, 0).Kind == TileKind.Wall) b.At(i, 0).Pattern = WallPattern.Stone;
        }
    }

    /// <summary>A manhole in a corridor dropping into a freezing, flooded tunnel running beneath it.</summary>
    private static void AddFloodedTunnel(Builder b)
    {
        // Find a straight west-east corridor run of at least 6 blocks
        for (int z = 1; z < MacroSize - 1; z++)
        {
            int runStart = -1;
            for (int x = 1; x <= MacroSize - 1; x++)
            {
                bool ok = x < MacroSize - 1 && b.At(x, z).Kind == TileKind.Floor && b.At(x, z).Variant == 0 && !b.At(x, z).SupplyBox && !b.At(x, z).Sealed;
                if (ok && runStart < 0) runStart = x;
                if (!ok && runStart >= 0)
                {
                    if (x - runStart >= 6)
                    {
                        for (int k = runStart; k < x; k++) b.At(k, z).Under = 1;
                        b.At(runStart + 1, z).Under = 2;
                        return;
                    }
                    runStart = -1;
                }
            }
        }
    }
}
