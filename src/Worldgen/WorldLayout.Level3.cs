using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 3, "Electrical Station": a hot, cramped maze of brick and glazed-tile maintenance corridors, crowded
/// with pipes, cable bundles, electrical panels, fans and transformers, lit by sparse amber fixtures with long
/// dark stretches between.
///
/// Corridors follow a lattice: 2-wide lanes every 8 blocks, joined by a random spanning tree (so the whole cell
/// is connected) plus a few extra loops. Some links are 1-wide squeezes; many loops are blocked by indestructible
/// white bars, so the way on is visible but out of reach. The solid blocks between lanes hold numbered machine
/// rooms, barred window rooms glowing with daylight, and supply caches. Rarely a whole cell is a vast transformer
/// hall. Manholes drop into flooded utility tunnels below the corridors, where it is freezing.
/// </summary>
public sealed partial class WorldLayout
{
    private const int L3Grid = 8;
    private const int L3Lane = 3; // lanes occupy offsets 3 and 4 of each lattice period

    private const ulong SaltL3Material = 0x3C01;
    private const ulong SaltL3Wall = 0x3C02;
    private const ulong SaltL3Light = 0x3C03;
    private const ulong SaltL3Section = 0x3C04;

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
        var rooms = new List<(int X0, int Z0, int Kind, int DoorX, int DoorZ)>();
        WallPattern material = Level3Material(mx, mz);

        void Carve(int x0, int z0, int x1, int z1)
        {
            for (int z = Math.Min(z0, z1); z <= Math.Max(z0, z1); z++)
                for (int x = Math.Min(x0, x1); x <= Math.Max(x0, x1); x++)
                    if (x >= 1 && z >= 1 && x < MacroSize && z < MacroSize) open[TileIndex(x, z)] = true;
        }

        static int Lane(int i) => i * L3Grid + L3Lane;

        if (rng.Chance(0.04))
        {
            // A vast transformer hall: one open space lined with machinery
            Carve(2, 2, MacroSize - 2, MacroSize - 2);
            for (int z = 5; z < MacroSize - 4; z += 5)
                for (int x = 5; x < MacroSize - 4; x += 3)
                    if (rng.Chance(0.75)) b.At(x, z).Variant = Props.Transformer;
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

            // Machine rooms, window rooms and caches in the solid cells between lanes
            for (int cz = 0; cz < 3; cz++)
            {
                for (int cx = 0; cx < 3; cx++)
                {
                    if (!rng.Chance(0.35)) continue;
                    int x0 = Lane(cx) + 3, z0 = Lane(cz) + 3; // 4x4 interior inside a 6x6 solid cell
                    double kind = rng.NextDouble();
                    // 0 machine room, 1 barred window room, 2 cache, 3 elevator
                    int roomKind = kind < 0.55 ? 0 : kind < 0.72 ? 1 : kind < 0.88 ? 2 : 3;
                    // The door faces whichever neighbouring lane exists
                    (int dx, int dz) door = open[TileIndex(x0 + 1, z0 - 2)] ? (x0 + 1, z0 - 1)
                        : open[TileIndex(x0 + 2, z0 + 5)] ? (x0 + 2, z0 + 4)
                        : open[TileIndex(x0 - 2, z0 + 1)] ? (x0 - 1, z0 + 1)
                        : open[TileIndex(x0 + 5, z0 + 2)] ? (x0 + 4, z0 + 2) : (-1, -1);
                    if (door.dx < 0) continue;
                    if (roomKind != 3) Carve(x0, z0, x0 + 3, z0 + 3);
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

        // Solidify
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                tile.Floor = FloorKind.Dusty;
                if (tile.Kind != TileKind.Floor) continue;
                if (!open[TileIndex(lx, lz)]) SetWall(ref tile, material, BaseStyle.Plain);
            }
        }
        foreach ((int x, int z, ArchPier plane) in bars)
        {
            if (!InInterior(x, z) || b.At(x, z).Kind != TileKind.Floor) continue;
            b.At(x, z).Kind = TileKind.Bars;
            b.At(x, z).Pier = plane;
        }
        foreach (var room in rooms) FurnishLevel3Room(b, room.X0, room.Z0, room.Kind, room.DoorX, room.DoorZ);

        DecorateLevel3(b, mx, mz);
        if (rng.Chance(0.3)) AddFloodedTunnel(b);
    }

    private static void FurnishLevel3Room(Builder b, int x0, int z0, int kind, int doorX, int doorZ)
    {
        ref Rng rng = ref b.Rng;
        if (kind == 3)
        {
            // Just a pair of elevator doors set into the corridor wall
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

        ref Tile door = ref b.At(doorX, doorZ);
        if (kind == 1)
        {
            // Window room: barred off, with daylight glowing from the far wall
            door.Kind = TileKind.Bars;
            door.Pier = doorZ < z0 || doorZ > z0 + 3 ? ArchPier.West : ArchPier.North;
            for (int x = x0; x <= x0 + 3; x++) b.At(x, z0 + 3).Variant = Props.WindowGlow;
            for (int z = z0; z <= z0 + 3; z++)
                for (int x = x0; x <= x0 + 3; x++)
                    b.At(x, z).Sealed = true;
            return;
        }

        SetWall(ref door, WallPattern.Cinder, BaseStyle.Plain);
        door.Kind = TileKind.Doorway;
        if (kind == 0)
        {
            // Machine room with a numbered sign over the door, transformers along the back
            door.Variant = Props.WallSign;
            door.Stack = (byte)rng.Range(0, 7); // which numbered sign hangs over the door
            for (int x = x0; x <= x0 + 3; x += 2) b.At(x, doorZ < z0 ? z0 + 3 : z0).Variant = Props.Transformer;
            if (rng.Chance(0.4)) b.At(x0 + 1, z0 + 1).SupplyBox = true;
        }
        else
        {
            // Supply cache: Level 3 is said to be rich in loot
            b.At(x0, z0).SupplyBox = true;
            b.At(x0 + 3, z0 + 3).SupplyBox = true;
            b.At(x0 + 3, z0).Stack = 2;
        }
    }

    private void DecorateLevel3(Builder b, int mx, int mz)
    {
        bool InCell(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize;
        bool IsOpen(int x, int z) => InCell(x, z) && b.At(x, z).Kind is TileKind.Floor or TileKind.Bars;
        // Near Level 2 the overhead runs are still pipes; deeper in they are cable bundles
        bool pipes = TouchesLevel(mx, mz, 2);

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Wall));
                bool e = IsOpen(lx + 1, lz), w = IsOpen(lx - 1, lz), s = IsOpen(lx, lz + 1), n = IsOpen(lx, lz - 1);

                if (tile.Kind == TileKind.Wall)
                {
                    // Long stretches of wall carry pipe runs; elsewhere electrical panels and industrial fans
                    if ((e || w || s || n) && tile.Variant == 0)
                    {
                        double stretch = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 8), Hashing.FloorDiv(gz, 8), SaltL3Wall + 1));
                        if (stretch < 0.55) tile.Variant = Props.WallPipes;
                        else tile.Variant = r < 0.2 ? Props.WallPanel : r < 0.32 ? Props.WallFan : Props.WallPlain;
                    }
                    continue;
                }
                if (tile.Kind != TileKind.Floor) continue;

                bool alongX = e && w && !(s && n) || (e ^ w) && !s && !n;
                bool alongZ = s && n && !(e && w) || (s ^ n) && !e && !w;
                tile.Pipe = pipes
                    ? (alongX ? Pipes.RunX : alongZ ? Pipes.RunZ : Pipes.Hub)
                    : (alongX ? Pipes.CableX : alongZ ? Pipes.CableZ : Pipes.CableHub);

                // Sparse amber fixtures on straight runs; about half are dead, whole sections out at once
                bool fixture = alongX ? Hashing.Mod(gx, 7) == 0 : alongZ && Hashing.Mod(gz, 7) == 0;
                if (fixture)
                {
                    double section = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 20), Hashing.FloorDiv(gz, 20), SaltL3Section));
                    double light = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Light));
                    tile.Ceiling = section < 0.35 ? CeilingKind.LightOff
                        : light < 0.3 ? CeilingKind.LightOff : light < 0.42 ? CeilingKind.LightFlicker : CeilingKind.LightWarm;
                }

                int neighbours = (e ? 1 : 0) + (w ? 1 : 0) + (s ? 1 : 0) + (n ? 1 : 0);
                if (neighbours == 1 && r > 0.8 && tile.Variant == 0) tile.SupplyBox = true;
            }
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
                bool ok = x < MacroSize - 1 && b.At(x, z).Kind == TileKind.Floor && b.At(x, z).Variant == 0 && !b.At(x, z).SupplyBox;
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
