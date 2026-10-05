using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 2, "Pipe Dreams": narrow, dark concrete maintenance tunnels, 1-2 blocks wide, with pipes running along
/// the ceiling and walls covered in pipework and machinery. Sparse caged lights in white or orange are wired in
/// series, so whole sections are dark at once. It is hot, and food is scarce.
///
/// Each cell starts solid. Corridors are carved from every passage in the cell's edges (its own west/north
/// edges and its neighbours' east/south ones) to one or two hubs, running straight in multiples of 5 blocks
/// before turning, so all tunnels connect.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL2Section = 0x2B01;
    private const ulong SaltL2Light = 0x2B02;
    private const ulong SaltL2Wall = 0x2B03;

    private static Edge Level2Edge(ref Rng rng)
    {
        var edge = new Edge { Pattern = WallPattern.Tunnel };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        int passages = rng.Range(1, 3);
        int spacing = (MacroSize - 4) / passages;
        for (int n = 0; n < passages; n++)
        {
            int start = 2 + n * spacing + rng.Range(0, spacing - 3);
            edge.Tiles[start] = EdgeTile.Open;
            if (rng.Chance(0.6)) edge.Tiles[start + 1] = EdgeTile.Open;
        }
        return edge;
    }

    private void BuildLevel2(Builder b, int mx, int mz, Edge west, Edge north)
    {
        ref Rng rng = ref b.Rng;
        var open = new bool[MacroSize * MacroSize];
        var machineRoom = new bool[MacroSize * MacroSize];

        // Entry points just inside each passage, with the direction pointing into the cell
        var portals = new List<(int X, int Z, int Dx, int Dz)>();
        foreach (int i in Passages(west)) { open[TileIndex(0, i)] = true; portals.Add((1, i, 1, 0)); }
        foreach (int i in Passages(north)) { open[TileIndex(i, 0)] = true; portals.Add((i, 1, 0, 1)); }
        foreach (int i in Passages(GetEdge(mx + 1, mz, west: true))) portals.Add((MacroSize - 1, i, -1, 0));
        foreach (int i in Passages(GetEdge(mx, mz + 1, west: false))) portals.Add((i, MacroSize - 1, 0, -1));

        var hub = (X: rng.Range(8, 23), Z: rng.Range(8, 23));
        int wide = rng.Chance(0.5) ? 2 : 1;
        foreach (var p in portals)
        {
            int run = 5 * rng.Range(1, 3);
            int x = p.X, z = p.Z;
            for (int k = 0; k < run && InCarveArea(x + p.Dx, z + p.Dz); k++)
            {
                Carve(open, x, z, 1);
                x += p.Dx;
                z += p.Dz;
            }
            CarvePath(open, ref rng, x, z, hub.X, hub.Z, wide);
        }

        if (rng.Chance(0.4))
        {
            // A second hub, and dead-end branches for good measure
            var hub2 = (X: rng.Range(4, 27), Z: rng.Range(4, 27));
            CarvePath(open, ref rng, hub.X, hub.Z, hub2.X, hub2.Z, wide);
        }
        int branches = rng.Range(0, 2);
        for (int n = 0; n < branches; n++)
        {
            int len = 5 * rng.Range(1, 3);
            int dx = rng.Chance(0.5) ? 1 : 0, dz = 1 - dx, sign = rng.Chance(0.5) ? 1 : -1;
            int x = hub.X, z = hub.Z;
            for (int k = 0; k < len && InCarveArea(x + dx * sign, z + dz * sign); k++) { x += dx * sign; z += dz * sign; Carve(open, x, z, 1); }
        }

        if (rng.Chance(0.2))
        {
            // A cramped machine room off the hub
            int w = rng.Range(4, 6), h = rng.Range(4, 7);
            int x0 = Math.Clamp(hub.X - w / 2, 2, MacroSize - 2 - w), z0 = Math.Clamp(hub.Z - h / 2, 2, MacroSize - 2 - h);
            for (int z = z0; z < z0 + h; z++)
                for (int x = x0; x < x0 + w; x++)
                    open[TileIndex(x, z)] = machineRoom[TileIndex(x, z)] = true;
        }

        // Turn the carved plan into tiles
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                tile.Floor = FloorKind.Concrete;
                if (tile.Kind != TileKind.Floor) continue; // edge walls and doorways
                if (!open[TileIndex(lx, lz)]) SetWall(ref tile, WallPattern.Tunnel, BaseStyle.Plain);
            }
        }

        DecorateTunnels(b, mx, mz, machineRoom);
    }

    private static bool InCarveArea(int x, int z) => x >= 1 && z >= 1 && x < MacroSize && z < MacroSize;

    private static void Carve(bool[] open, int x, int z, int width)
    {
        for (int dz = 0; dz < width; dz++)
            for (int dx = 0; dx < width; dx++)
                if (InCarveArea(x + dx, z + dz)) open[TileIndex(x + dx, z + dz)] = true;
    }

    /// <summary>An L-shaped tunnel between two points, choosing at random which leg comes first.</summary>
    private static void CarvePath(bool[] open, ref Rng rng, int x0, int z0, int x1, int z1, int width)
    {
        bool xFirst = rng.Chance(0.5);
        int x = x0, z = z0;
        Carve(open, x, z, width);
        for (int leg = 0; leg < 2; leg++)
        {
            bool alongX = xFirst == (leg == 0);
            while (alongX ? x != x1 : z != z1)
            {
                if (alongX) x += Math.Sign(x1 - x); else z += Math.Sign(z1 - z);
                Carve(open, x, z, width);
            }
        }
    }

    private void DecorateTunnels(Builder b, int mx, int mz, bool[] machineRoom)
    {
        bool InCell(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize;
        bool IsOpen(int x, int z) => InCell(x, z) && b.At(x, z).Kind != TileKind.Wall;
        bool IsWall(int x, int z) => InCell(x, z) && b.At(x, z).Kind == TileKind.Wall;

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL2Wall));
                double r2 = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL2Wall + 1));

                bool e = IsOpen(lx + 1, lz), w = IsOpen(lx - 1, lz), s = IsOpen(lx, lz + 1), n = IsOpen(lx, lz - 1);
                if (tile.Kind == TileKind.Wall)
                {
                    // Walls facing a tunnel: whole stretches carry continuous pipework (with the odd valve or riser
                    // on it); other stretches are machinery, brick, hazard signs or bare concrete
                    if (tile.Pattern == WallPattern.Tunnel && (e || w || s || n))
                    {
                        double stretch = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 10), Hashing.FloorDiv(gz, 10), SaltL2Wall + 2));
                        if (stretch < 0.7) tile.Variant = r < 0.08 ? Props.WallValve : r < 0.16 ? Props.WallRiser : Props.WallPipes;
                        else tile.Variant = r < 0.35 ? Props.WallMachinery : r < 0.6 ? Props.WallBrick : r < 0.7 ? Props.WallWarning : Props.WallPlain;
                    }
                    continue;
                }
                if (tile.Kind != TileKind.Floor) continue;

                int neighbours = (e ? 1 : 0) + (w ? 1 : 0) + (s ? 1 : 0) + (n ? 1 : 0);
                // Direction of the tunnel; in a 2-wide tunnel the other lane counts as a side, not a branch
                bool alongX = e && w && !(s && n) || (e ^ w) && !s && !n;
                bool alongZ = s && n && !(e && w) || (s ^ n) && !e && !w;
                int index = TileIndex(lx, lz);

                // Overhead pipe bundles follow every tunnel, meeting at junction boxes where tunnels turn or branch
                if (machineRoom[index])
                {
                    // Pipes only run along the walls of machine rooms
                    if (IsWall(lx, lz - 1) || IsWall(lx, lz + 1)) tile.Pipe = Pipes.RunX;
                    else if (IsWall(lx - 1, lz) || IsWall(lx + 1, lz)) tile.Pipe = Pipes.RunZ;
                }
                else if (alongX || alongZ)
                {
                    bool leak = r2 < 0.035;
                    tile.Pipe = alongX ? (leak ? Pipes.LeakX : Pipes.RunX) : (leak ? Pipes.LeakZ : Pipes.RunZ);
                }
                else
                {
                    tile.Pipe = Pipes.Hub;
                }

                // Fluorescent fixtures every 6 blocks along a tunnel, on circuits that fail by section
                bool fixture = alongX ? Hashing.Mod(gx, 6) == 0
                    : alongZ ? Hashing.Mod(gz, 6) == 0
                    : Hashing.Mod(gx, 6) == 0 && Hashing.Mod(gz, 6) == 0;
                if (fixture)
                {
                    if (tile.Pipe == Pipes.LeakX) tile.Pipe = Pipes.RunX;
                    if (tile.Pipe == Pipes.LeakZ) tile.Pipe = Pipes.RunZ;
                    ulong section = Hashing.Hash(seed, Hashing.FloorDiv(gx, 24), Hashing.FloorDiv(gz, 24), SaltL2Section);
                    double light = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL2Light));
                    if (Hashing.Unit(section) < 0.35) tile.Ceiling = light < 0.15 ? CeilingKind.LightFlicker : CeilingKind.LightOff;
                    else tile.Ceiling = light < 0.08 ? CeilingKind.LightOff : light < 0.13 ? CeilingKind.LightFlicker
                        : ((section >> 12) & 1) == 0 ? CeilingKind.LightWarm : CeilingKind.LightOn;
                }

                // Machine rooms are lined with cabinets; elsewhere drums in wider spots and forgotten supplies in dead ends
                if (machineRoom[index] && r > 0.35 && TryWallSide(IsWall, lx, lz, out ArchPier wall))
                {
                    tile.Variant = Props.Cabinet;
                    tile.Pier = wall;
                }
                else if (neighbours >= 3 && r > 0.975) tile.Variant = Props.Drum;
                else if (neighbours == 1 && r > 0.86) tile.SupplyBox = true;
            }
        }
    }

    /// <summary>Finds a wall next to a tile, so props can stand against it.</summary>
    private static bool TryWallSide(Func<int, int, bool> isWall, int x, int z, out ArchPier side)
    {
        side = ArchPier.North;
        if (isWall(x, z - 1)) { side = ArchPier.North; return true; }
        if (isWall(x, z + 1)) { side = ArchPier.South; return true; }
        if (isWall(x - 1, z)) { side = ArchPier.West; return true; }
        if (isWall(x + 1, z)) { side = ArchPier.East; return true; }
        return false;
    }
}
