using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Gates: the few places where the wall between two levels has a way through. Reaching the wall is not reaching the
/// next level; the player walks along it, in the dangerous band at a level's edge, until they find a gate, and then
/// remembers where it was.
///
/// The world is divided into blocks of <see cref="GateBlock"/> x <see cref="GateBlock"/> cells. Within each block,
/// the boundary edges between the same two levels that touch end to end form a stretch, and each stretch gets exactly
/// one gate: its edge with the lowest hash. So a boundary has a gate every few hundred blocks, and every island of one
/// level inside another (which is its own closed stretch) still has a way in. Everything is a pure function of the
/// seed and the block, so neighbouring chunks always agree.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Size, in cells, of the blocks within which each stretch of boundary gets one gate (10 cells = 320 blocks).</summary>
    public const int GateBlock = 10;

    private const ulong SaltGate = 0x6A7E;

    // Bounded memo of GatesIn, one entry per block (the sets in it are only ever read)
    private readonly LatticeMemo<HashSet<long>> gateCache;

    private static long EdgeKey(int mx, int mz, bool west) => ((long)mx << 33) ^ ((long)(uint)mz << 1) ^ (west ? 1L : 0L);

    /// <summary>
    /// Whether the wall between two levels follows the gate rule. Where the open-sky levels meet there is no wall at
    /// all, the caves of Level 8 open only where the 9th Road runs through, and the places you can only noclip into
    /// (the city, the Poolrooms, Motion) have no way through their rims at all.
    /// </summary>
    private static bool IsGated(int level, int otherLevel) =>
        level != otherLevel && !(IsOpenSky(level) && IsOpenSky(otherLevel)) && level != 8 && otherLevel != 8
        && !IsNoclipRegion(level) && !IsNoclipRegion(otherLevel);

    /// <summary>Whether the boundary edge on the west or north side of a cell is one of the few with a way through.</summary>
    private bool IsGate(int mx, int mz, bool west) =>
        GatesIn(Hashing.FloorDiv(mx, GateBlock), Hashing.FloorDiv(mz, GateBlock)).Contains(EdgeKey(mx, mz, west));

    private HashSet<long> GatesIn(int bx, int bz) => gateCache.Get(bx, bz);

    /// <summary>The gates of one block, as <see cref="EdgeKey"/>s (see <see cref="GatesIn"/>).</summary>
    private HashSet<long> PlanGates(int bx, int bz)
    {
        // Every gated boundary edge owned by a cell of this block
        var edges = new List<(int Mx, int Mz, bool West, int Pair, ulong Hash)>();
        for (int mz = bz * GateBlock; mz < (bz + 1) * GateBlock; mz++)
            for (int mx = bx * GateBlock; mx < (bx + 1) * GateBlock; mx++)
            {
                int level = LevelAt(mx, mz);
                for (int side = 0; side < 2; side++)
                {
                    bool west = side == 0;
                    int other = west ? LevelAt(mx - 1, mz) : LevelAt(mx, mz - 1);
                    if (!IsGated(level, other)) continue;
                    int pair = Math.Min(level, other) * 16 + Math.Max(level, other);
                    edges.Add((mx, mz, west, pair, Hashing.Hash(seed, mx, mz, SaltGate + (ulong)side)));
                }
            }

        // Edges dividing the same two levels that meet at a corner belong to one stretch
        int[] parent = new int[edges.Count];
        for (int i = 0; i < parent.Length; i++) parent[i] = i;
        int Find(int i)
        {
            while (parent[i] != i) i = parent[i] = parent[parent[i]];
            return i;
        }
        var byCorner = new Dictionary<(int Pair, int X, int Z), int>();
        for (int i = 0; i < edges.Count; i++)
        {
            var e = edges[i];
            // A west edge runs from the cell's corner to the corner below it; a north edge to the corner beside it
            foreach ((int x, int z) in new[] { (e.Mx, e.Mz), e.West ? (e.Mx, e.Mz + 1) : (e.Mx + 1, e.Mz) })
            {
                if (byCorner.TryGetValue((e.Pair, x, z), out int j)) parent[Find(i)] = Find(j);
                else byCorner[(e.Pair, x, z)] = i;
            }
        }

        // In each stretch, the edge with the lowest hash is the gate
        var best = new Dictionary<int, int>();
        for (int i = 0; i < edges.Count; i++)
        {
            int root = Find(i);
            if (!best.TryGetValue(root, out int b) || edges[i].Hash < edges[b].Hash) best[root] = i;
        }
        var gates = new HashSet<long>();
        foreach (int i in best.Values) gates.Add(EdgeKey(edges[i].Mx, edges[i].Mz, edges[i].West));
        return gates;
    }

    /// <summary>
    /// The gates within <paramref name="radius"/> blocks of a position that lead out of <paramref name="level"/>: where
    /// each one's doorway is (a block position in the wall), and which level lies on the far side.
    /// </summary>
    public List<(int X, int Z, int To)> GatesNear(int gx, int gz, int level, int radius)
    {
        var found = new List<(int X, int Z, int To)>();
        int mx0 = MacroOf(gx - radius), mx1 = MacroOf(gx + radius), mz0 = MacroOf(gz - radius), mz1 = MacroOf(gz + radius);
        for (int bz = Hashing.FloorDiv(mz0, GateBlock); bz <= Hashing.FloorDiv(mz1 + 1, GateBlock); bz++)
            for (int bx = Hashing.FloorDiv(mx0, GateBlock); bx <= Hashing.FloorDiv(mx1 + 1, GateBlock); bx++)
                foreach (long key in GatesIn(bx, bz))
                {
                    bool west = (key & 1) != 0;
                    int mx = (int)(key >> 33), mz = (int)(uint)((key >> 1) & 0xFFFFFFFF);
                    int here = LevelAt(mx, mz), other = west ? LevelAt(mx - 1, mz) : LevelAt(mx, mz - 1);
                    if (here != level && other != level) continue;
                    (int x, int z) = GateDoorway(mx, mz, west);
                    if (Math.Abs(x - gx) > radius || Math.Abs(z - gz) > radius) continue;
                    found.Add((x, z, here == level ? other : here));
                }
        return found;
    }

    /// <summary>
    /// The nearest gate out of a level toward a given level (or any level when <paramref name="to"/> is -1), or null.
    /// <paramref name="skip"/> names gates not to count (a note never points at a place its reader's notes already marked).
    /// </summary>
    public (int X, int Z, int To)? NearestGate(int gx, int gz, int level, int radius, int to = -1, Func<int, int, bool> skip = null)
    {
        (int X, int Z, int To)? nearest = null;
        long bestDistance = long.MaxValue;
        foreach (var gate in GatesNear(gx, gz, level, radius))
        {
            if (to >= 0 && gate.To != to) continue;
            if (skip != null && skip(gate.X, gate.Z)) continue;
            long d = (long)(gate.X - gx) * (gate.X - gx) + (long)(gate.Z - gz) * (gate.Z - gz);
            if (d < bestDistance) { bestDistance = d; nearest = gate; }
        }
        return nearest;
    }

    /// <summary>
    /// A gate must lead somewhere. Where none of its doorways opens onto floor that can be walked to from the rest of
    /// this cell (it meets the back wall of a room, or a locked room), a short way is broken through, straight in
    /// from the middle doorway, until it reaches open floor. Runs after the cell's pockets are sealed, so it knows
    /// which floor counts; the cells on either side of a gate each see to their own side.
    /// </summary>
    private void OpenGates(Builder b, int mx, int mz, Edge west, Edge north, Edge east, Edge south)
    {
        int level = b.Level;
        if (IsGated(level, LevelAt(mx - 1, mz))) OpenGate(b, west, (0, 1), (1, 0), (1, 0));
        if (IsGated(level, LevelAt(mx, mz - 1))) OpenGate(b, north, (1, 0), (0, 1), (0, 1));
        if (IsGated(level, LevelAt(mx + 1, mz))) OpenGate(b, east, (0, 1), (MacroSize - 1, 0), (-1, 0));
        if (IsGated(level, LevelAt(mx, mz + 1))) OpenGate(b, south, (1, 0), (0, MacroSize - 1), (0, -1));
    }

    /// <param name="along">Step along the wall.</param>
    /// <param name="first">This cell's tile just inside the wall, at index 0 along it.</param>
    /// <param name="inward">Step away from the wall into this cell.</param>
    private static void OpenGate(Builder b, Edge edge, (int X, int Z) along, (int X, int Z) first, (int X, int Z) inward)
    {
        // Both cells must open the same doorway, or each might open a different one onto its own side and leave no way
        // through: the middle of the first run, which is also where the gate is said to be
        int mid = MainDoorway(edge);
        if (mid < 0) return;
        int x = first.X + along.X * mid, z = first.Z + along.Z * mid;
        for (int step = 0; step < 12; step++, x += inward.X, z += inward.Z)
        {
            if (x < 0 || z < 0 || x >= MacroSize || z >= MacroSize) return;
            ref Tile t = ref b.At(x, z);
            if (IsWalkable(t) && !t.Sealed) return;
            // Never through another level's wall, a lift, a stair, bars or a shaft
            if (t.Tall || t.Stair != 0 || t.Kind is TileKind.Bars or TileKind.Pit || t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator) return;
            if (t.Kind is TileKind.Wall or TileKind.Door or TileKind.ArchWindow)
            {
                t.Kind = TileKind.Floor;
                t.Variant = 0;
                t.Outlet = false;
            }
            else if (t.Kind == TileKind.Floor && !IsWalkable(t))
            {
                t.Variant = 0;
                t.Stack = 0;
                t.SupplyBox = false;
            }
            t.Sealed = false;
        }
    }

    private const ulong SaltGateChalk = 0x6A7F;

    /// <summary>The four tiles beside one, and which wall of it each is, in the order the chalk marks look for a wall.</summary>
    private static readonly (int Dx, int Dz, ArchPier Side)[] WallSides =
        { (0, -1, ArchPier.North), (1, 0, ArchPier.East), (0, 1, ArchPier.South), (-1, 0, ArchPier.West) };

    /// <summary>
    /// Others found the gates before you, and marked the way: in most cells within a hundred blocks or so of a gate,
    /// an arrow in chalk on a wall or two points toward it, the way the M.E.G. mark the ways out.
    /// </summary>
    private void MarkWayToGates(Builder b, int mx, int mz)
    {
        int level = b.Level;
        if (level > 6 || level == 6 && IsSnackrooms(mx, mz)) return;
        ulong h = Hashing.Hash(seed, mx, mz, SaltGateChalk);
        if (Hashing.Unit(h) >= 0.6) return;
        int cx = mx * MacroSize + MacroSize / 2, cz = mz * MacroSize + MacroSize / 2;
        if (NearestGate(cx, cz, level, 112) is not { } gate) return;

        var rng = new Rng(Hashing.Mix(h));
        int marks = 0, lastX = -99, lastZ = -99;
        for (int attempt = 0; attempt < 200 && marks < 2; attempt++)
        {
            int lx = rng.Range(1, MacroSize - 2), lz = rng.Range(1, MacroSize - 2);
            ref Tile t = ref b.At(lx, lz);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0 || t.SupplyBox || t.Stair != 0 || t.Sealed || t.Under != 0 || t.Chalk != 0) continue;
            if (Math.Abs(lx - lastX) + Math.Abs(lz - lastZ) < 10) continue;
            // A plain stretch of wall beside it (not a doorway or a decorated panel)
            ArchPier? wall = null;
            foreach ((int dx, int dz, ArchPier side) in WallSides)
            {
                ref Tile n = ref b.At(lx + dx, lz + dz);
                if (n.Kind == TileKind.Wall && n.Variant == 0) { wall = side; break; }
            }
            if (wall is not ArchPier w) continue;
            int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
            double toX = gate.X - gx, toZ = gate.Z - gz;
            if (toX * toX + toZ * toZ < 36) continue; // right beside it: no need
            // Facing the wall, which way is the gate? (Facing north, left is west; facing east, left is north)
            (int fx, int fz) = w switch { ArchPier.North => (0, -1), ArchPier.East => (1, 0), ArchPier.South => (0, 1), _ => (-1, 0) };
            double leftward = toX * fz - toZ * fx;
            t.Chalk = ChalkBits.Make(w, leftward > 0 ? 0 : 1);
            marks++;
            lastX = lx;
            lastZ = lz;
        }
    }

    /// <summary>The middle of a gate's doorways, as a block position in the wall.</summary>
    private (int X, int Z) GateDoorway(int mx, int mz, bool west)
    {
        int at = MainDoorway(GetEdge(mx, mz, west));
        if (at < 0) at = MacroSize / 2;
        return west ? (mx * MacroSize, mz * MacroSize + at) : (mx * MacroSize + at, mz * MacroSize);
    }

    /// <summary>The index along an edge of the middle of its first run of doorways, or -1 if it has none.</summary>
    private static int MainDoorway(Edge edge)
    {
        int first = -1, last = -1;
        for (int i = 1; i < MacroSize; i++)
        {
            if (edge.Tiles[i] != EdgeTile.Doorway) continue;
            if (first < 0) first = i;
            last = i;
            if (i + 1 < MacroSize && edge.Tiles[i + 1] != EdgeTile.Doorway) break;
        }
        return first < 0 ? -1 : (first + last) / 2;
    }
}
