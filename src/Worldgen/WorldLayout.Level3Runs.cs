using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 3's wall runs, from layout version 9 (<see cref="PlanL3WallRuns"/>, <see cref="PlanL3FloorCables"/>). In 1-8
/// each wall block chose its own fitting: pipes and cables by the eight-block square it stood in, with a light, a sign
/// or a gauge now and then in the middle of a run, so a small room could hold four short lengths of pipe ending in
/// mid-air, a cable run could be a block long, the gauges sat on a length of pipe of their own and the cables on the
/// floor lay a block at a time. From 9 the runs are laid whole: a block of solid wall (with the room in it, whose walls
/// are the same blocks seen from inside) carries the pipes all the way round or not at all, its gauges sit in its
/// pipes, the cable runs go the length of a wall from a panel or a gland in the wall to another, and the cables on
/// the floor cross a corridor from a panel or a junction box to a box or a fitting on the wall opposite.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL3Runs = 0x3C0B;

    /// <summary>The share of Level 3's wall groups (a block of solid wall, and any room in it) that carry the wall pipes.</summary>
    private const double L3PipeShare = 0.42;

    /// <summary>The share of the walls left without pipes that carry a cable run, where the wall is long enough.</summary>
    private const double L3CableShare = 0.3;

    /// <summary>How often a wall's panel or junction box has cables across the floor in front of it.</summary>
    private const double L3FloorCableShare = 0.3;

    private static readonly ArchPier[] L3Dirs = { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West };

    /// <summary>The fittings a planned run may take the place of (those <see cref="DecorateLevel3"/> puts on a wall).</summary>
    private static bool L3Replaceable(ushort v) => v is Props.WallPlain or Props.WallPanel or Props.WallFan or Decor.Bulkhead
        or Decor.DangerSign or Decor.KnifeSwitch or Decor.JunctionBox or Decor.SparkOutlet or Decor.AlarmBell or Decor.Risers;

    /// <summary>
    /// The fitting of a Level 3 wall facing a walkway (layout version 9), from the wall's own roll: lights, signs and
    /// switch gear as in 1-8, panels and fans on the rest, and no pipes, gauges or cables, which
    /// <see cref="PlanL3WallRuns"/> lays afterwards as whole runs. Bulkheads are a little commoner, since the runs take
    /// the place of some.
    /// </summary>
    private static ushort L3WallFixture(double r) =>
        r < 0.05 ? Decor.Bulkhead : r < 0.075 ? Decor.DangerSign : r < 0.1 ? Decor.KnifeSwitch : r < 0.125 ? Decor.JunctionBox
        : r < 0.137 ? Decor.SparkOutlet : r < 0.145 ? Decor.AlarmBell : r < 0.16 ? Decor.Risers
        : r < 0.25 ? Props.WallPanel : r < 0.32 ? Props.WallFan : Props.WallPlain;

    /// <summary>
    /// From layout version 9, after <see cref="DecorateLevel3"/> has given the walls their fittings: the wall pipes and
    /// cable runs, laid whole. A run is a straight stretch of wall blocks facing the same way into the open, from corner
    /// to corner (or to a door, a sign or a niche). Runs that share a block (round an outer corner, or the two faces of a
    /// thin wall, such as a room's walls and the corridor outside them) go together, and so do a room's walls where they
    /// meet in its corners, so a block of solid wall and the room in it carry the pipes all the way round, or none of
    /// them do; the generator turns them round the corners and
    /// bends their ends into the wall (WorldGenerator.WallPipeCorner). A group of fewer than four faces carries none.
    /// The walls beside a switchgear cabinet carry no run (one would come out of its front); the wall behind it may (the
    /// pipes go into its sides). Pressure gauges sit in the pipes, on a block with one face open between two of the run
    /// (the generator draws them on the pipes). Of the walls left, a run three blocks or more long may carry the cables,
    /// all of it, with a panel at one end now and then (the generator draws the panel's conduit up into a junction box
    /// the cables run into, and bends the other end into the wall through a gland).
    /// </summary>
    private void PlanL3WallRuns(Builder b, int mx, int mz)
    {
        const int N = MacroSize;
        static bool In(int x, int z) => x >= 0 && z >= 0 && x < N && z < N;
        // Where a wall pipe shows beside a column (as WorldGenerator.PipeOpen)
        bool Open(int x, int z) => In(x, z) && b.At(x, z).Kind is TileKind.Floor or TileKind.Doorway or TileKind.Pit or TileKind.Bars
            or TileKind.Water or TileKind.ArchDoor;
        // What a decoration on one face may look out onto
        bool Faces(int x, int z) => In(x, z) && b.At(x, z).Kind is TileKind.Floor or TileKind.Bars;
        bool LooksOut(int x, int z, ArchPier d)
        {
            var (fx, fz) = Step(x, z, d);
            return Faces(fx, fz);
        }
        int OpenSides(int x, int z)
        {
            int k = 0;
            foreach (ArchPier d in L3Dirs)
            {
                var (nx, nz) = Step(x, z, d);
                if (Open(nx, nz)) k++;
            }
            return k;
        }

        // The walls beside a switchgear cabinet, not behind it
        var beside = new bool[N * N];
        for (int z = 0; z < N; z++)
            for (int x = 0; x < N; x++)
            {
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Floor || t.Variant != Props.Switchgear) continue;
                foreach (ArchPier side in new[] { Turn(t.Pier), Opposite(Turn(t.Pier)) })
                {
                    var (sx, sz) = Step(x, z, side);
                    if (!In(sx, sz) || b.At(sx, sz).Kind != TileKind.Wall) continue;
                    beside[TileIndex(sx, sz)] = true;
                    // (nor a panel or a fan, which are on every face of their block, so one would be in the cabinet's side)
                    if (b.At(sx, sz).Variant is Props.WallPanel or Props.WallFan) b.At(sx, sz).Variant = Props.WallPlain;
                }
            }
        // (Not the cell's own edge walls: what lies beyond them is the next cell's)
        bool Eligible(int x, int z) => x >= 1 && z >= 1 && In(x, z) && !beside[TileIndex(x, z)] && b.At(x, z).Kind == TileKind.Wall
            && b.At(x, z).Pattern != WallPattern.Stone && L3Replaceable(b.At(x, z).Variant);
        bool Face(int x, int z, ArchPier d)
        {
            var (nx, nz) = Step(x, z, d);
            return Eligible(x, z) && Open(nx, nz);
        }

        // The runs: each face's stretch along its wall, in the order the wall runs with the open side on the left
        var runs = new List<(ArchPier D, List<(int X, int Z)> Tiles)>();
        var runsAt = new Dictionary<int, List<int>>();
        foreach (ArchPier d in L3Dirs)
        {
            ArchPier along = Turn(d);
            for (int z = 1; z < N; z++)
                for (int x = 1; x < N; x++)
                {
                    if (!Face(x, z, d)) continue;
                    var (px, pz) = Step(x, z, Opposite(along));
                    if (Face(px, pz, d)) continue;
                    var tiles = new List<(int X, int Z)>();
                    for ((int cx, int cz) = (x, z); Face(cx, cz, d); (cx, cz) = Step(cx, cz, along)) tiles.Add((cx, cz));
                    int id = runs.Count;
                    runs.Add((d, tiles));
                    foreach ((int tx, int tz) in tiles)
                    {
                        int i = TileIndex(tx, tz);
                        if (!runsAt.TryGetValue(i, out var list)) runsAt[i] = list = new List<int>();
                        list.Add(id);
                    }
                }
        }
        if (runs.Count == 0) return;

        // Runs that share a block go together
        var parent = new int[runs.Count];
        for (int i = 0; i < parent.Length; i++) parent[i] = i;
        int Root(int i)
        {
            while (parent[i] != i) i = parent[i] = parent[parent[i]];
            return i;
        }
        void Union(int i, int j)
        {
            int a = Root(i), c = Root(j);
            if (a != c) parent[Math.Max(a, c)] = Math.Min(a, c);
        }
        foreach (var list in runsAt.Values)
            for (int k = 1; k < list.Count; k++) Union(list[0], list[k]);
        // and a room's walls meet in its inner corners: a room is piped all round or not at all
        for (int i = 0; i < runs.Count; i++)
        {
            var (d, tiles) = runs[i];
            ArchPier along = Turn(d);
            foreach (((int X, int Z) end, ArchPier toward) in new[] { (tiles[^1], along), (tiles[0], Opposite(along)) })
            {
                if (b.At(end.X, end.Z).Pattern != WallPattern.Cinder) continue;
                var (cx, cz) = Step(end.X, end.Z, toward);
                var (ox, oz) = Step(cx, cz, d);
                if (!Face(ox, oz, Opposite(toward)) || b.At(ox, oz).Pattern != WallPattern.Cinder) continue;
                if (runsAt.TryGetValue(TileIndex(ox, oz), out var other))
                    foreach (int j in other)
                        if (runs[j].D == Opposite(toward)) Union(i, j);
            }
        }
        var faces = new Dictionary<int, int>();
        var first = new Dictionary<int, (int X, int Z)>();
        for (int i = 0; i < runs.Count; i++)
        {
            int g = Root(i);
            faces[g] = (faces.TryGetValue(g, out int f) ? f : 0) + runs[i].Tiles.Count;
            foreach (var p in runs[i].Tiles)
                if (!first.TryGetValue(g, out var q) || p.Z < q.Z || p.Z == q.Z && p.X < q.X) first[g] = p;
        }
        bool Piped(int g) => faces[g] >= 4
            && Hashing.Unit(Hashing.Hash(seed, mx * N + first[g].X, mz * N + first[g].Z, SaltL3Runs)) < L3PipeShare;

        // The pipes, whole, and their gauges
        for (int i = 0; i < runs.Count; i++)
        {
            if (!Piped(Root(i))) continue;
            foreach ((int x, int z) in runs[i].Tiles) b.At(x, z).Variant = Props.WallPipes;
        }
        for (int i = 0; i < runs.Count; i++)
        {
            var (d, tiles) = runs[i];
            if (!Piped(Root(i))) continue;
            int last = -9;
            for (int k = 1; k < tiles.Count - 1; k++)
            {
                (int x, int z) = tiles[k];
                int gx = mx * N + x, gz = mz * N + z;
                // (Between the flanged joints and the brackets, WorldGenerator.WallPipeRun)
                if (k - last < 3 || OpenSides(x, z) != 1 || !LooksOut(x, z, d) || Hashing.Mod(gx + gz, 2) != 1) continue;
                if (Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Runs + 1)) >= 0.16) continue;
                b.At(x, z).Variant = Decor.Gauges;
                b.At(x, z).Pier = d;
                last = k;
            }
        }

        // Cable runs on walls without pipes: a whole stretch three blocks long or more, facing the open
        var taken = new bool[N * N];
        for (int i = 0; i < runs.Count; i++)
        {
            var (d, tiles) = runs[i];
            if (Piped(Root(i))) continue;
            for (int k = 0; k < tiles.Count;)
            {
                int end = k;
                while (end < tiles.Count && !taken[TileIndex(tiles[end].X, tiles[end].Z)] && LooksOut(tiles[end].X, tiles[end].Z, d))
                    end++;
                int length = end - k;
                if (length >= 3)
                {
                    (int x0, int z0) = tiles[k];
                    ulong h = Hashing.Hash(seed, mx * N + x0, mz * N + z0, SaltL3Runs + 2 + (ulong)d);
                    if (Hashing.Unit(h) < L3CableShare)
                    {
                        for (int j = k; j < end; j++)
                        {
                            ref Tile t = ref b.At(tiles[j].X, tiles[j].Z);
                            t.Variant = Decor.WallCables;
                            t.Pier = d;
                            taken[TileIndex(tiles[j].X, tiles[j].Z)] = true;
                        }
                        // Now and then the run starts from a panel, whose conduit carries it up into a junction box
                        int at = ((h >> 24) & 1) == 0 ? k : end - 1;
                        if (length >= 4 && ((h >> 25) & 1) == 0 && OpenSides(tiles[at].X, tiles[at].Z) == 1)
                            b.At(tiles[at].X, tiles[at].Z).Variant = Props.WallPanel;
                    }
                }
                k = Math.Max(end, k + 1);
            }
        }
    }

    /// <summary>
    /// From layout version 9: the cables on Level 3's floors (in 1-8 a block of them here and there along a corridor, on
    /// one tile in twenty). Now and then a panel or a junction box on a corridor wall has cables down to the floor and
    /// across it to the wall opposite, two to five blocks, where they end in a cable box on the floor or rise into a
    /// panel or junction box there: <see cref="Props.FloorCable"/> with <see cref="Tile.Stack"/> 0 the straight lengths
    /// (Pier as in 1-8: North along X, East along Z), 1 the box against the wall and 2 the rise up the wall (Pier toward
    /// that wall). At most three crossings in a cell, never two side by side.
    /// </summary>
    private void PlanL3FloorCables(Builder b, int mx, int mz)
    {
        const int N = MacroSize;
        static bool In(int x, int z) => x >= 0 && z >= 0 && x < N && z < N;
        bool Cable(int x, int z) => In(x, z) && b.At(x, z).Kind == TileKind.Floor && b.At(x, z).Variant == Props.FloorCable;
        bool Clear(int x, int z)
        {
            if (!In(x, z)) return false;
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stack != 0 || t.Sealed || t.Under != 0 || t.Stair != 0) return false;
            // (ClearDoorways clears the floor in front of a doorway)
            foreach (ArchPier d in L3Dirs)
            {
                var (nx, nz) = Step(x, z, d);
                if (In(nx, nz) && b.At(nx, nz).Kind == TileKind.Doorway) return false;
            }
            return x < N - 1 && z < N - 1;
        }
        bool Fitting(in Tile w, ArchPier facing) => w.Kind == TileKind.Wall && (w.Variant == Props.WallPanel || w.Variant == Decor.JunctionBox && w.Pier == facing);

        int placed = 0;
        var line = new List<(int X, int Z)>();
        for (int z = 1; z < N - 1; z++)
            for (int x = 1; x < N - 1; x++)
            {
                ref Tile wall = ref b.At(x, z);
                if (wall.Kind != TileKind.Wall || wall.Variant != Props.WallPanel && wall.Variant != Decor.JunctionBox) continue;
                int gx = mx * N + x, gz = mz * N + z;
                foreach (ArchPier d in L3Dirs)
                {
                    if (!Fitting(wall, d)) continue;
                    if (Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL3Runs + 6 + (ulong)d)) >= L3FloorCableShare) continue;
                    // The floor straight across from the fitting to the wall opposite
                    line.Clear();
                    var (cx, cz) = Step(x, z, d);
                    while (line.Count <= 5 && In(cx, cz) && b.At(cx, cz).Kind == TileKind.Floor)
                    {
                        line.Add((cx, cz));
                        (cx, cz) = Step(cx, cz, d);
                    }
                    if (line.Count < 2 || line.Count > 5 || !In(cx, cz) || b.At(cx, cz).Kind != TileKind.Wall) continue;
                    ArchPier side = Turn(d);
                    bool ok = true;
                    foreach ((int lx, int lz) in line)
                    {
                        var (ax, az) = Step(lx, lz, side);
                        var (bx, bz) = Step(lx, lz, Opposite(side));
                        if (!Clear(lx, lz) || Cable(ax, az) || Cable(bx, bz)) { ok = false; break; }
                    }
                    if (!ok) continue;
                    bool rises = Fitting(b.At(cx, cz), Opposite(d));
                    for (int k = 0; k < line.Count; k++)
                    {
                        ref Tile t = ref b.At(line[k].X, line[k].Z);
                        t.Variant = Props.FloorCable;
                        if (k == 0) { t.Stack = 2; t.Pier = Opposite(d); }
                        else if (k == line.Count - 1) { t.Stack = (byte)(rises ? 2 : 1); t.Pier = d; }
                        else t.Pier = d is ArchPier.East or ArchPier.West ? ArchPier.North : ArchPier.East;
                    }
                    if (++placed >= 3) return;
                    break;
                }
            }
    }
}
