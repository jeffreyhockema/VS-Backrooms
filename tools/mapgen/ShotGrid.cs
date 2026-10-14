using Backrooms.Worldgen;

/// <summary>
/// Camera planning for the graphics pass's spot lists (tools/shotbot/mkspots.py).
///
///   mapgen &lt;seed&gt; &lt;cells&gt; shotgrid &lt;level&gt; [x z]
///       Writes shotgrid.bin: the tiles of a square of cells centred on the level's first arrival (the one AT=L&lt;level&gt;
///       uses; "6.1" is the Snackrooms' arrival), or on block x, z, with each tile's feet height. Prints the arrival,
///       spawn and the shared floor. Levels by the names players type: 0-11, 6.1, 37, 94, !, fun, end, hub, 974, 3999, 188.
///   mapgen &lt;seed&gt; 1 feet x z [x z ...]
///       Prints "x z level feetY" for each column: where /tp puts your feet to stand there, as /backrooms nearest does.
///
/// shotgrid.bin: int32 x0, z0, size, floorY, then size*size tiles (rows of z, each x from x0), 18 bytes each:
/// kind, floor, ceiling, flags, level, pattern, variant (uint16), zone, height, overhead, roof, depth, stair, pier,
/// pipe, then feet y (uint16, hundredths of a block). flags: 1 supply box, 2 stack/prop part, 4 pipe, 8 EXIT sign,
/// 16 worn, 32 under, 64 grand, 128 sealed.
/// </summary>
static class ShotGrid
{
    // Heights for a world 256 high, the default (WorldGeometry's FloorY is mapSizeY - 40)
    static readonly WorldGeometry Geometry = new WorldGeometry(256);

    public static bool Run(WorldLayout layout, string[] args)
    {
        if (args.Length > 3 && args[2] == "feet")
        {
            for (int i = 3; i + 1 < args.Length; i += 2)
            {
                int x = int.Parse(args[i]), z = int.Parse(args[i + 1]);
                Tile t = layout.TileAt(x, z);
                Console.WriteLine(FormattableString.Invariant($"{x} {z} {WorldLayout.DisplayNumber(t.Level)} {Feet(layout, x, z, t):0.00}"));
            }
            return true;
        }
        if (args.Length > 3 && args[2] == "shotgrid")
        {
            int n = int.Parse(args[1]);
            string name = args[3];
            (int X, int Z)? centre;
            if (args.Length > 5) centre = (int.Parse(args[4]), int.Parse(args[5]));
            else if (name == "6.1") centre = layout.FindSnackroomsArrival(99991UL);
            else
            {
                int level = WorldLayout.FromDisplayName(name);
                if (level < 0) { Console.WriteLine("unknown level " + name); return true; }
                centre = layout.FindArrival(level, 99991UL);
            }
            if (centre is not { } c) { Console.WriteLine("no arrival"); return true; }
            Tile at = layout.TileAt(c.X, c.Z);
            var (sx, sz) = layout.FindSpawn();
            Console.WriteLine(FormattableString.Invariant($"arrival {c.X} {c.Z} {Feet(layout, c.X, c.Z, at):0.00} level {WorldLayout.DisplayNumber(at.Level)} zone {at.Zone}"));
            Console.WriteLine($"spawn {sx} {sz}");
            Console.WriteLine($"floor {Geometry.FloorY}");
            int m0x = WorldLayout.MacroOf(c.X) - n / 2, m0z = WorldLayout.MacroOf(c.Z) - n / 2;
            int size = n * WorldLayout.MacroSize, x0 = m0x * WorldLayout.MacroSize, z0 = m0z * WorldLayout.MacroSize;
            var buf = new byte[16 + size * size * 18];
            BitConverter.TryWriteBytes(buf.AsSpan(0), x0);
            BitConverter.TryWriteBytes(buf.AsSpan(4), z0);
            BitConverter.TryWriteBytes(buf.AsSpan(8), size);
            BitConverter.TryWriteBytes(buf.AsSpan(12), Geometry.FloorY);
            for (int mz = 0; mz < n; mz++)
                for (int mx = 0; mx < n; mx++)
                {
                    Tile[] tiles = layout.BuildMacro(m0x + mx, m0z + mz);
                    for (int i = 0; i < tiles.Length; i++)
                    {
                        Tile t = tiles[i];
                        int lx = mx * WorldLayout.MacroSize + i % WorldLayout.MacroSize, lz = mz * WorldLayout.MacroSize + i / WorldLayout.MacroSize;
                        int o = 16 + (lz * size + lx) * 18;
                        buf[o] = (byte)t.Kind; buf[o + 1] = (byte)t.Floor; buf[o + 2] = (byte)t.Ceiling;
                        buf[o + 3] = (byte)((t.SupplyBox ? 1 : 0) | (t.Stack > 0 ? 2 : 0) | (t.Pipe > 0 ? 4 : 0) | (t.ExitSign ? 8 : 0)
                            | (t.Worn ? 16 : 0) | (t.Under > 0 ? 32 : 0) | (t.Grand ? 64 : 0) | (t.Sealed ? 128 : 0));
                        buf[o + 4] = t.Level; buf[o + 5] = (byte)t.Pattern;
                        BitConverter.TryWriteBytes(buf.AsSpan(o + 6), t.Variant);
                        buf[o + 8] = t.Zone; buf[o + 9] = t.Height; buf[o + 10] = t.Overhead; buf[o + 11] = t.Roof;
                        buf[o + 12] = t.Depth; buf[o + 13] = t.Stair; buf[o + 14] = (byte)t.Pier; buf[o + 15] = t.Pipe;
                        double feet = Feet(layout, x0 + lx, z0 + lz, t);
                        BitConverter.TryWriteBytes(buf.AsSpan(o + 16), (ushort)Math.Clamp(Math.Round(feet * 100), 0, 65535));
                    }
                }
            File.WriteAllBytes("shotgrid.bin", buf);
            Console.WriteLine($"wrote shotgrid.bin: {size}x{size} from {x0},{z0}");
            return true;
        }
        return false;
    }

    // As CheatSystem.Teleport: the level's floor plus how high above it one stands on that tile
    static double Feet(WorldLayout layout, int x, int z, Tile t) => Geometry.FloorFor(t.Level) + layout.ArrivalHeight(x, z);
}
