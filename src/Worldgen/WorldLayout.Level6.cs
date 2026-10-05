using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 6, "Lights Out": an endless series of tight hallways of a smooth, cold material, in total darkness. No
/// light permeates it and light brought in barely works. It is unnaturally silent. The hallways are a maze of
/// one-wide passages with the odd small chamber, dead ends everywhere, and chalk left on the walls by those who
/// came before. Deeper in, stairs lead down toward the faint sound of waves (Level 7), and a wire strung across a
/// passage here and there trips the unwary straight into Level 6.1.
///
/// <para><b>Level 6.1, the Snackrooms</b>, is hidden in rare cells of the same ring, walled off from the maze: an
/// endless 1980s mall food court, bright as day, with snack bars and convenience stores whose vending machines,
/// fridges and shelves are full. It can only be fallen into, and its exits are unreliable: a rusty steel door back
/// into the dark, glass doors and vents to other levels, and kitchen doors that open into another food court.</para>
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL6Edge = 0x6A01;
    private const ulong SaltL6Snack = 0x6A02;
    private const ulong SaltL6Detail = 0x6A03;
    private const ulong SaltL6Unit = 0x6A04;

    private const double SnackroomsChance = 0.05;

    /// <summary>The Snackrooms: rare cells of Level 6 wholly surrounded by Level 6.</summary>
    public bool IsSnackrooms(int mx, int mz)
    {
        if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL6Snack)) > SnackroomsChance) return false;
        return SurroundedByLevel6(mx, mz);
    }

    private bool SurroundedByLevel6(int mx, int mz)
    {
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != 6) return false;
        return true;
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

    private Edge Level6Edge(ref Rng rng, int mx, int mz, int nx, int nz)
    {
        var edge = new Edge { Pattern = WallPattern.L6Wall };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        if (IsSnackrooms(mx, mz) || IsSnackrooms(nx, nz)) return edge; // sealed

        // The maze crosses the edge at a few of its odd positions
        int openings = rng.Range(3, 5);
        for (int n = 0; n < openings; n++) edge.Tiles[1 + 2 * rng.Range(0, 15)] = EdgeTile.Open;
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

        ref Rng rng = ref b.Rng;
        var open = new bool[MacroSize * MacroSize];
        void Carve(int x, int z) { if (x >= 1 && z >= 1 && x < MacroSize && z < MacroSize) open[TileIndex(x, z)] = true; }

        // A perfect maze over the odd positions: one-wide passages with one-wide walls between
        const int nodes = MacroSize / 2;
        var visited = new bool[nodes * nodes];
        var stack = new Stack<int>();
        int start = rng.Range(0, nodes * nodes - 1);
        visited[start] = true;
        stack.Push(start);
        Carve(1 + 2 * (start % nodes), 1 + 2 * (start / nodes));
        var options = new List<int>(4);
        while (stack.Count > 0)
        {
            int node = stack.Peek();
            int nx = node % nodes, nz = node / nodes;
            options.Clear();
            if (nx > 0 && !visited[node - 1]) options.Add(node - 1);
            if (nx < nodes - 1 && !visited[node + 1]) options.Add(node + 1);
            if (nz > 0 && !visited[node - nodes]) options.Add(node - nodes);
            if (nz < nodes - 1 && !visited[node + nodes]) options.Add(node + nodes);
            if (options.Count == 0) { stack.Pop(); continue; }
            int next = options[rng.Range(0, options.Count - 1)];
            visited[next] = true;
            int ax = 1 + 2 * nx, az = 1 + 2 * nz, bx = 1 + 2 * (next % nodes), bz = 1 + 2 * (next / nodes);
            Carve((ax + bx) / 2, (az + bz) / 2);
            Carve(bx, bz);
            stack.Push(next);
        }
        // A few loops, so not every wrong turn is a dead end
        for (int n = rng.Range(4, 9); n > 0; n--)
        {
            int x = 1 + 2 * rng.Range(0, nodes - 2) + 1, z = 1 + 2 * rng.Range(0, nodes - 1);
            if (rng.Chance(0.5)) (x, z) = (z, x);
            Carve(x, z);
        }

        // A couple of small chambers; the deeper into the level, the likelier one holds stairs going down
        double depth = RingFraction(mx * MacroSize + 16, mz * MacroSize + 16, 6);
        var chambers = new List<(int X, int Z, int Size)>();
        for (int n = rng.Range(1, 2); n > 0; n--)
        {
            int size = rng.Chance(0.5) ? 5 : 3;
            int x0 = 1 + 2 * rng.Range(1, nodes - 1 - size / 2 - 1), z0 = 1 + 2 * rng.Range(1, nodes - 1 - size / 2 - 1);
            for (int z = z0; z < z0 + size; z++)
                for (int x = x0; x < x0 + size; x++)
                    Carve(x, z);
            chambers.Add((x0, z0, size));
        }

        // Edge openings join the maze at the node beside them
        foreach (int i in Passages(west)) { open[TileIndex(0, i)] = true; Carve(1, i); }
        foreach (int i in Passages(north)) { open[TileIndex(i, 0)] = true; Carve(i, 1); }

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind == TileKind.Floor && !open[TileIndex(lx, lz)]) SetWall(ref tile, WallPattern.L6Wall, BaseStyle.Plain);
            }
        }

        foreach (var c in chambers)
        {
            if (c.Size == 5 && rng.Chance(0.06 + 0.3 * depth))
            {
                // Stairs down along the middle of the chamber, toward the faint sound of waves
                ArchPier dir = rng.Chance(0.5) ? ArchPier.East : ArchPier.West;
                int z = c.Z + 2;
                for (int k = 0; k < 3; k++)
                {
                    int x = dir == ArchPier.East ? c.X + 1 + k : c.X + 3 - k;
                    ref Tile step = ref b.At(x, z);
                    step.Under = (byte)(Unders.Descent1 + k);
                    step.Pier = dir;
                    step.Sealed = true; // nobody is put down on a staircase
                }
            }
        }

        DecorateLevel6(b, mx, mz);
    }

    /// <summary>Chalk on the walls, and wires across the passages.</summary>
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
                    if (ways == 1 && r < 0.35)
                    {
                        ArchPier toOpen = e ? ArchPier.East : w ? ArchPier.West : s ? ArchPier.South : ArchPier.North;
                        var (fx, fz) = Step(lx, lz, Opposite(toOpen));
                        ref Tile end = ref b.At(fx, fz);
                        if (end.Kind == TileKind.Wall && end.Variant == 0) { end.Variant = Decor.MegCross; end.Pier = toOpen; }
                        // Now and then, what is left of whoever came this far: a dead flashlight, a pack, a bedroll
                        double left = Hashing.Unit(Hashing.Mix(h));
                        if (left < 0.12) { tile.Variant = Props.Flashlight; tile.Pier = (ArchPier)(h % 4); }
                        else if (left < 0.18) { tile.Variant = Props.Backpack; tile.Pier = toOpen; }
                        else if (left < 0.22) { tile.Variant = Props.Bedroll; tile.Pier = toOpen; }
                    }
                    // Water stands in places, slick and black
                    else if (Noise((mx * MacroSize + lx) / 6.0, (mz * MacroSize + lz) / 6.0, SaltL6Detail + 5) > 0.55)
                        tile.Floor = FloorKind.L6Wet;
                    // A wire strung low across a straight passage
                    else if (ways == 2 && (e && w || s && n) && r > 0.993)
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

    private enum SnackUnit { Restaurant, Store, Seating }

    private void BuildSnackrooms(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        const int hall0 = 13, hall1 = 18;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
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
                    BuildSnackUnit(b, ux0, ux1, north ? qz0 : qz1, north ? qz1 : qz0, north, kind, ref rng);
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
    private static void BuildSnackUnit(Builder b, int x0, int x1, int zBack, int zFront, bool north, SnackUnit kind, ref Rng rng)
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
                t.Pattern = kind == SnackUnit.Store ? WallPattern.SnackMall : WallPattern.SnackPanel;
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
            default:
                for (int k = 1; Math.Abs(k) < Math.Abs(zFront - zBack) - 1; k += 3)
                    for (int x = x0 + 1; x < x1; x += 3)
                        PlaceCafeTable(b, x, zBack + k * dz);
                Put(x1, zBack, Props.SnackVending, toHall);
                break;
        }
    }
}
