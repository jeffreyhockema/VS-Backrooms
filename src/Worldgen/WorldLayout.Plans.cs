using System;
using System.Collections.Concurrent;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

public sealed partial class WorldLayout
{
    /// <summary>
    /// For the levels whose ways run on a lattice with main lines every <paramref name="n"/> lines (Level 2's tunnels,
    /// Level 6's trunks, Level 8's roads): which stretches of the minor lines between four main ones are there. The crossings inside (n - 1 by
    /// n - 1 of them) are joined by a tree grown from one crossing on the mains, tending to run straight on, so there
    /// is one way in and most turnings end blind; a few extra stretches join two branches, or a branch back to the
    /// mains. A stretch is (axis, line, index): axis 0 the stretch of north-south line `line` beside unit row
    /// `index`, axis 1 the stretch of west-east line `line` beside unit column `index`.
    /// </summary>
    private HashSet<(int, int, int)> PlanLatticeTree(int mcx, int mcz, int n, ulong salt, double straight, double extraInside, double extraToMains)
    {
        var kept = new HashSet<(int, int, int)>();
        var rng = new Rng(Hashing.Hash(seed, mcx, mcz, salt));
        (int, int, int) Stretch(int ai, int aj, int bi, int bj) => aj == bj
            ? (1, mcz * n + aj, mcx * n + Math.Min(ai, bi))
            : (0, mcx * n + ai, mcz * n + Math.Min(aj, bj));
        bool Inside(int i, int j) => i >= 1 && j >= 1 && i < n && j < n;
        (int, int)[] steps = { (1, 0), (-1, 0), (0, 1), (0, -1) };

        // The one way in, from a crossing on the mains
        int side = rng.Range(0, 3), at = rng.Range(1, n - 1);
        (int i, int j) root = side switch { 0 => (1, at), 1 => (n - 1, at), 2 => (at, 1), _ => (at, n - 1) };
        (int i, int j) gate = side switch { 0 => (0, at), 1 => (n, at), 2 => (at, 0), _ => (at, n) };
        kept.Add(Stretch(root.i, root.j, gate.i, gate.j));

        var visited = new bool[n + 1, n + 1];
        visited[root.i, root.j] = true;
        var stack = new Stack<(int I, int J, int Dir)>();
        stack.Push((root.i, root.j, side));
        var options = new List<int>(4);
        while (stack.Count > 0)
        {
            var (ci, cj, dir) = stack.Peek();
            options.Clear();
            for (int d = 0; d < 4; d++)
                if (Inside(ci + steps[d].Item1, cj + steps[d].Item2) && !visited[ci + steps[d].Item1, cj + steps[d].Item2]) options.Add(d);
            if (options.Count == 0) { stack.Pop(); continue; }
            int pick = options.Contains(dir) && rng.Chance(straight) ? dir : options[rng.Range(0, options.Count - 1)];
            int ni = ci + steps[pick].Item1, nj = cj + steps[pick].Item2;
            visited[ni, nj] = true;
            kept.Add(Stretch(ci, cj, ni, nj));
            stack.Push((ni, nj, pick));
        }

        for (int j = 0; j <= n; j++)
            for (int i = 0; i <= n; i++)
                for (int d = 0; d < 2; d++)
                {
                    int ni = i + (d == 0 ? 1 : 0), nj = j + (d == 1 ? 1 : 0);
                    if (ni > n || nj > n || !Inside(i, j) && !Inside(ni, nj)) continue; // along the mains: always there
                    var s = Stretch(i, j, ni, nj);
                    if (!kept.Contains(s) && rng.Chance(Inside(i, j) && Inside(ni, nj) ? extraInside : extraToMains)) kept.Add(s);
                }
        return kept;
    }

    /// <summary>
    /// For the levels laid out from plans larger than a cell (Level 0, Level 2, Level 6): which of the eight cells round a cell
    /// are walled off from it: another level, or (in Level 0) a Red Room on one side and not the other. Indexed
    /// (dz + 1) * 3 + (dx + 1); null when there are none.
    /// </summary>
    private bool[] WalledNeighbours(int level, int mx, int mz)
    {
        bool red = level == 0 && IsRedRoom(mx, mz);
        bool[] other = null;
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
            {
                int nx = mx + dx, nz = mz + dz;
                if (LevelAt(nx, nz) == level && (level != 0 || IsRedRoom(nx, nz) == red)) continue;
                (other ??= new bool[9])[(dz + 1) * 3 + dx + 1] = true;
            }
        return other;
    }

    /// <summary>
    /// Whether a tile of a cell lies in the hallway that runs round the inside of the walls that cut the plan off: two
    /// wide, just inside the wall to the next level (or round a Red Room), turning with it at every corner. Whatever
    /// the wall cuts through opens onto this hallway, so nothing is ever left cut off; and it is the way to walk along
    /// the wall looking for a gate.
    /// </summary>
    /// <param name="other">The cell's <see cref="WalledNeighbours"/>.</param>
    /// <param name="wide">
    /// Whether the cell lines the next level's wall on its east and on its south side (from layout version 9, see
    /// <see cref="LiningWidens"/>): the lining takes the tile by the wall, so the hallway takes one more further in.
    /// </param>
    private static bool EdgeHall(bool[] other, int lx, int lz, (bool East, bool South) wide = default)
    {
        if (other == null) return false;
        bool Other(int dx, int dz) => other[(dz + 1) * 3 + dx + 1];
        bool west = lx is >= 1 and <= 2, east = lx >= MacroSize - (wide.East ? 3 : 2), north = lz is >= 1 and <= 2,
            south = lz >= MacroSize - (wide.South ? 3 : 2);
        if (west && Other(-1, 0) || east && Other(1, 0) || north && Other(0, -1) || south && Other(0, 1)) return true;
        // Where the wall turns a corner round another cell, the hallway turns with it
        bool w = lx <= 2, n = lz <= 2;
        return w && n && Other(-1, -1) || east && n && Other(1, -1) || w && south && Other(-1, 1) || east && south && Other(1, 1);
    }

    /// <summary>
    /// Clears the hallway round the inside of the walls that cut the plan off (see <see cref="EdgeHall"/>) through
    /// whatever the plan put there; never through those walls themselves.
    /// </summary>
    private void CarveEdgeHall(Builder b, int mx, int mz, Edge west, Edge north)
    {
        bool[] other = WalledNeighbours(b.Level, mx, mz);
        if (other == null) return;
        var wide = LiningWidens(b.Level, mx, mz);
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                if (lx == 0 && (lz == 0 || !west.Planned) || lz == 0 && !north.Planned) continue;
                ref Tile t = ref b.At(lx, lz);
                // (From layout version 9, where the hallway moves in a tile for the lining, an arch or a doorway left
                // standing in it by the tile the lining takes goes too, so the lining runs on unbroken)
                bool orphan = t.Kind is TileKind.ArchDoor or TileKind.Doorway && (wide.East && lx >= MacroSize - 2 || wide.South && lz >= MacroSize - 2);
                if (t.Tall || IsWalkable(t) && !orphan || !EdgeHall(other, lx, lz, wide)) continue;
                t.Kind = TileKind.Floor;
                t.Variant = 0;
                t.Outlet = false;
            }
    }

    /// <summary>
    /// Copies a cell's part of a level's plan into it. The cell's own edges are copied too where they follow the plan;
    /// a wall between levels (or round a Red Room, or the Snackrooms) stays as the edge laid it.
    /// </summary>
    /// <param name="copy">Copies the planned tile at a block position into the cell's tile at a local index.</param>
    private void CopyPlan(Builder b, int mx, int mz, Edge west, Edge north, Action<int, int, int> copy)
    {
        bool cornerPlanned = west.Planned && north.Planned && GetEdge(mx - 1, mz, west: false).Planned && GetEdge(mx, mz - 1, west: true).Planned;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                if (lx == 0 && lz == 0 ? !cornerPlanned : lx == 0 ? !west.Planned : lz == 0 && !north.Planned) continue;
                copy(mx * MacroSize + lx, mz * MacroSize + lz, TileIndex(lx, lz));
            }
    }
}

/// <summary>
/// Plans for pieces of a level larger than a macro cell (a city block, a Level 0 district, the rock between Level 6's
/// trunks, a lattice tree). A plan is worked out once from its own id and kept for a while: a cell covers parts of
/// several, and neighbouring cells share them. Plans are pure functions of the seed and the id, so dropping one
/// only costs the time to work it out again.
/// </summary>
/// <remarks>
/// Thread-safe: worldgen threads share it. Looking a plan up takes no lock (some callers ask once per tile); a plan is
/// worked out outside any lock, and two threads that both miss may each work it out, keeping whichever was stored
/// first. Plans handed out are shared, so callers only ever read them. Once more than the capacity are kept, the
/// oldest stored is dropped.
/// </remarks>
internal sealed class PlanCache<T> where T : class
{
    private readonly ConcurrentDictionary<(int, int), T> plans = new();
    /// <summary>The order plans were stored in, for dropping the oldest; only touched under its own lock.</summary>
    private readonly Queue<(int, int)> order = new();
    private readonly int capacity;
    private readonly Func<int, int, T> make;

    public PlanCache(int capacity, Func<int, int, T> make)
    {
        this.capacity = capacity;
        this.make = make;
    }

    public T Get(int i, int j)
    {
        if (plans.TryGetValue((i, j), out T cached)) return cached;
        T plan = make(i, j);
        lock (order)
        {
            if (plans.TryGetValue((i, j), out T raced)) return raced;
            plans[(i, j)] = plan;
            order.Enqueue((i, j));
            if (order.Count > capacity) plans.TryRemove(order.Dequeue(), out _);
        }
        return plan;
    }
}
