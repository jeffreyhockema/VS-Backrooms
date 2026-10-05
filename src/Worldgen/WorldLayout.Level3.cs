using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 3, "Electrical Station": a hot, cramped maze of derelict brick and glazed-tile maintenance halls fitted
/// with electrical machinery: groups of transformers, conductor coils, switchgear and industrial fans line the
/// corridors in niches, long cables sprawl along the walls and droop from the trays, outlets spark, and sparse
/// amber fixtures leave long stretches dark.
///
/// Corridors follow a lattice: 2-wide lanes every 8 blocks, joined by a random spanning tree (so the whole cell
/// is connected) plus a few extra loops. Some links are 1-wide squeezes; many loops are blocked by indestructible
/// white bars, so the way on is visible but out of reach. The solid blocks between lanes hold electrical rooms,
/// each with a small sign beside its door bearing a number and jumbled text: machine rooms, generator rooms,
/// control rooms, assembly lines, caged transformers behind bars, barred window rooms glowing with daylight,
/// supply caches and freight elevators. Rarely a whole cell is a vast transformer hall, and more rarely still a
/// Sanctum: a hushed gothic hall of pale masonry with a statue of an angel at its heart. Manholes drop into
/// flooded utility tunnels below the corridors, where it is freezing.
/// </summary>
public sealed partial class WorldLayout
{
    private const int L3Grid = 8;
    private const int L3Lane = 3; // lanes occupy offsets 3 and 4 of each lattice period

    private const ulong SaltL3Material = 0x3C01;
    private const ulong SaltL3Wall = 0x3C02;
    private const ulong SaltL3Light = 0x3C03;
    private const ulong SaltL3Section = 0x3C04;
    private const ulong SaltL3Niche = 0x3C05;
    private const ulong SaltL3Cell = 0x3C06;

    private enum L3Room { Machine, Window, Cache, Elevator, Generator, Control, Assembly, Cage, Boiler }

    private Edge Level3Edge(ref Rng rng, int mx, int mz)
    {
        var edge = new Edge { Pattern = Level3Material(mx, mz) };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;

        // Lanes cross the edge at lattice positions; at least one always does
        int forced = rng.Range(0, 3);
        for (int k = 0; k < 4; k++)
        {
            if (k != forced && !rng.Chance(0.55)) continue;
            edge.Tiles[k * L3Grid + L3Lane] = edge.Tiles[k * L3Grid + L3Lane + 1] = EdgeTile.Open;
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

        static int Lane(int i) => i * L3Grid + L3Lane;

        double cellKind = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL3Cell));
        bool sanctum = cellKind < 0.025;
        bool transformerHall = !sanctum && cellKind < 0.065;
        if (sanctum)
        {
            BuildSanctum(b, mx, mz);
            return;
        }
        if (transformerHall)
        {
            // A vast transformer hall: rows of transformers and coils on striped floors
            Carve(2, 2, MacroSize - 2, MacroSize - 2);
            for (int z = 5; z < MacroSize - 4; z += 5)
                for (int x = 5; x < MacroSize - 4; x += 3)
                {
                    if (!rng.Chance(0.75)) continue;
                    b.At(x, z).Variant = rng.Chance(0.3) ? Props.Coil : Props.Transformer;
                    for (int dz = -1; dz <= 1; dz++)
                        for (int dx = -1; dx <= 1; dx++)
                            b.At(x + dx, z + dz).Floor = FloorKind.L3Hazard;
                }
        }
        else
        {
            // Spanning tree over the 4x4 lattice nodes, by randomised depth-first search
            var visited = new bool[16];
            var stack = new Stack<int>();
            var tree = new HashSet<(int, int)>();
            int start = rng.Range(0, 15);
            visited[start] = true;
            stack.Push(start);
            while (stack.Count > 0)
            {
                int node = stack.Peek();
                int nx = node % 4, nz = node / 4;
                var options = new List<int>();
                if (nx > 0 && !visited[node - 1]) options.Add(node - 1);
                if (nx < 3 && !visited[node + 1]) options.Add(node + 1);
                if (nz > 0 && !visited[node - 4]) options.Add(node - 4);
                if (nz < 3 && !visited[node + 4]) options.Add(node + 4);
                if (options.Count == 0) { stack.Pop(); continue; }
                int next = options[rng.Range(0, options.Count - 1)];
                visited[next] = true;
                tree.Add((Math.Min(node, next), Math.Max(node, next)));
                stack.Push(next);
            }

            for (int node = 0; node < 16; node++)
            {
                int ix = node % 4, iz = node / 4;
                Carve(Lane(ix), Lane(iz), Lane(ix) + 1, Lane(iz) + 1);
                foreach (int other in new[] { ix < 3 ? node + 1 : -1, iz < 3 ? node + 4 : -1 })
                {
                    if (other < 0) continue;
                    bool inTree = tree.Contains((node, other));
                    if (!inTree && !rng.Chance(0.25)) continue;
                    int ox = other % 4, oz = other / 4;
                    // Tree links are sometimes 1-wide squeezes; extra loops are often barred off
                    bool squeeze = inTree && rng.Chance(0.15);
                    int width = squeeze ? 0 : 1;
                    Carve(Lane(ix), Lane(iz), Lane(ox) + width, Lane(oz) + width);
                    if (!inTree && rng.Chance(0.5))
                    {
                        int midX = (Lane(ix) + Lane(ox)) / 2 + 1, midZ = (Lane(iz) + Lane(oz)) / 2 + 1;
                        // Bars stand across the corridor: a north-south plane across a west-east corridor and vice versa
                        if (ox != ix) { bars.Add((midX, Lane(iz), ArchPier.North)); bars.Add((midX, Lane(iz) + 1, ArchPier.North)); }
                        else { bars.Add((Lane(ix), midZ, ArchPier.West)); bars.Add((Lane(ix) + 1, midZ, ArchPier.West)); }
                    }
                }
            }

            // Electrical rooms in the solid cells between lanes
            for (int cz = 0; cz < 3; cz++)
            {
                for (int cx = 0; cx < 3; cx++)
                {
                    if (!rng.Chance(0.42)) continue;
                    int x0 = Lane(cx) + 3, z0 = Lane(cz) + 3; // 4x4 interior inside a 6x6 solid cell
                    double kind = rng.NextDouble();
                    L3Room roomKind = kind < 0.3 ? L3Room.Machine : kind < 0.39 ? L3Room.Window : kind < 0.5 ? L3Room.Cache
                        : kind < 0.58 ? L3Room.Elevator : kind < 0.67 ? L3Room.Generator : kind < 0.76 ? L3Room.Control
                        : kind < 0.85 ? L3Room.Assembly : kind < 0.92 ? L3Room.Boiler : L3Room.Cage;
                    // The door faces whichever neighbouring lane exists
                    (int dx, int dz) door = open[TileIndex(x0 + 1, z0 - 2)] ? (x0 + 1, z0 - 1)
                        : open[TileIndex(x0 + 2, z0 + 5)] ? (x0 + 2, z0 + 4)
                        : open[TileIndex(x0 - 2, z0 + 1)] ? (x0 - 1, z0 + 1)
                        : open[TileIndex(x0 + 5, z0 + 2)] ? (x0 + 4, z0 + 2) : (-1, -1);
                    if (door.dx < 0) continue;
                    if (roomKind != L3Room.Elevator) Carve(x0, z0, x0 + 3, z0 + 3);
                    rooms.Add((x0, z0, roomKind, door.dx, door.dz));
                }
            }
        }

        // Every passage in the edges connects inward to the nearest lattice node
        void ConnectPassage(int x, int z, int dx, int dz)
        {
            int nodeX = Math.Clamp((int)Math.Round((x - L3Lane) / (double)L3Grid), 0, 3);
            int nodeZ = Math.Clamp((int)Math.Round((z - L3Lane) / (double)L3Grid), 0, 3);
            int tx = Lane(nodeX), tz = Lane(nodeZ);
            if (dx != 0) { Carve(x, z, tx, z); Carve(tx, z, tx, tz); }
            else { Carve(x, z, x, tz); Carve(x, tz, tx, tz); }
        }
        foreach (int i in Passages(west)) { open[TileIndex(0, i)] = true; ConnectPassage(1, i, 1, 0); }
        foreach (int i in Passages(north)) { open[TileIndex(i, 0)] = true; ConnectPassage(i, 1, 0, 1); }
        foreach (int i in Passages(GetEdge(mx + 1, mz, west: true))) ConnectPassage(MacroSize - 1, i, -1, 0);
        foreach (int i in Passages(GetEdge(mx, mz + 1, west: false))) ConnectPassage(i, MacroSize - 1, 0, -1);

        // Solidify; some stretches of corridor are floored with steel grating
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
            }
        }
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
        if (rng.Chance(0.3)) AddFloodedTunnel(b);
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
        if (kind is L3Room.Window or L3Room.Cage)
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
        // Near Level 2 the overhead runs are still pipes; deeper in they are cable bundles
        bool pipes = TouchesLevel(mx, mz, 2);

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
                    continue;
                }
                if (tile.Kind != TileKind.Floor || tile.Sealed) continue;

                bool alongX = e && w && !(s && n) || (e ^ w) && !s && !n;
                bool alongZ = s && n && !(e && w) || (s ^ n) && !e && !w;
                if (tile.Pipe == 0)
                {
                    bool droop = Hashing.Unit(h << 16) < 0.07;
                    tile.Pipe = pipes
                        ? (alongX ? Pipes.RunX : alongZ ? Pipes.RunZ : Pipes.Hub)
                        : (alongX ? (droop ? Pipes.CableDroopX : Pipes.CableX) : alongZ ? (droop ? Pipes.CableDroopZ : Pipes.CableZ) : Pipes.CableHub);
                }

                // Sparse amber fixtures on straight runs; about half are dead, whole sections out at once
                bool fixture = alongX ? Hashing.Mod(gx, 7) == 0 : alongZ && Hashing.Mod(gz, 7) == 0;
                if (fixture && tile.Pipe is not (Pipes.CableDroopX or Pipes.CableDroopZ))
                {
                    double section = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 20), Hashing.FloorDiv(gz, 20), SaltL3Section));
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
