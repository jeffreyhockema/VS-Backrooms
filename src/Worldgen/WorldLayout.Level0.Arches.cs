using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 0's arched areas from layout version 10: plain cream stucco and an arcade of bays, not a labyrinth with the
/// paper bleached. The unit is a bay: one pier and two arched openings, three blocks along a wall, with a pier every
/// third block on one lattice that starts at the district's west (or north) wall. An area is one of
///
/// <list type="bullet">
/// <item>an arcade street: a hall five wide along the district's longer side with a full arcade down both of its
/// sides (every opening a walkable arch), and behind each arcade rows of rooms, six to nine deep and two to four bays
/// wide, every room opening onto the row before it through its own bays: at least two walkable arches, and in about
/// half the rooms one outer bay is a half-height window, the only place half walls occur. A third of the walls
/// between neighbouring rooms have a two-wide arch (an enfilade), so rooms make loops;</item>
/// <item>a cloister (one in four): the whole district one hall, two or three arcade rows running across it from wall
/// to wall, all openings walkable, the piers in line, so you walk through repeated arches either way.</item>
/// </list>
///
/// <para>Every plan is checked before it is kept (<see cref="ArchesSound"/>): one piece of floor, floor behind every
/// arch in the district's own walls and on both faces of every arch, every arch standing between two piers. A plan that
/// fails is drawn again from the same stream; if none passes, the district is one open hall.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>A tile of the arcade street or cloister hall (see <see cref="L0Plan.Hall"/>), not a room.</summary>
    private const byte HallStreet = 4;

    /// <summary>A room of an arched area: its floor, and the wall row its bays are in (for supply boxes, and the harness).</summary>
    private readonly struct ArchRoom
    {
        public readonly int A0, A1, C0, C1, Back;
        public ArchRoom(int a0, int a1, int c0, int c1, int back) { A0 = a0; A1 = a1; C0 = c0; C1 = c1; Back = back; }
    }

    private void PlanArches(L0Plan p, List<(int U, int V, int DU, int DV)> openings)
    {
        bool swap = p.H > p.W; // a runs along the longer side
        int A = (swap ? p.H : p.W) - 1, C = (swap ? p.W : p.H) - 1;
        // The gaps in the walls, in the plan's own terms: end walls (a = 0 and a = A + 1), sides (c = 0 and c = C + 1)
        var endGaps = new[] { new List<int>(), new List<int>() };
        var sideGaps = new[] { new List<int>(), new List<int>() };
        foreach (var o in openings)
        {
            int a = swap ? o.V : o.U, c = swap ? o.U : o.V, da = swap ? o.DV : o.DU, dc = swap ? o.DU : o.DV;
            if (da != 0) endGaps[da > 0 ? 0 : 1].Add(c); else sideGaps[dc > 0 ? 0 : 1].Add(a);
        }
        // An arcade or a dividing wall may not stand across the way in from an end gap
        var barred = new bool[C + 3];
        foreach (var list in endGaps) foreach (int g in list) { barred[g] = true; barred[g + 1] = true; }
        var noBox = new bool[p.W * p.H];
        foreach (var o in openings)
            for (int k = 0; k < 2; k++)
            {
                int u = o.U + (o.DU == 0 ? k : 0), v = o.V + (o.DV == 0 ? k : 0);
                foreach ((int du, int dv) in new[] { (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1) })
                    if (p.In(u + du, v + dv)) noBox[(v + dv) * p.W + u + du] = true;
            }

        ref Tile T(int a, int c) => ref p.At(swap ? c : a, swap ? a : c);
        ArchPier Along(bool first) => swap ? (first ? ArchPier.North : ArchPier.South) : (first ? ArchPier.West : ArchPier.East);
        ArchPier Across(bool first) => swap ? (first ? ArchPier.West : ArchPier.East) : (first ? ArchPier.North : ArchPier.South);
        void Wall(int a, int c) => SetWall(ref T(a, c), WallPattern.Stucco, BaseStyle.Baseboard);
        void Arch(int a, int c, bool window, ArchPier pier)
        {
            ref Tile t = ref T(a, c);
            t.Kind = window ? TileKind.ArchWindow : TileKind.ArchDoor;
            t.Pattern = WallPattern.Stucco;
            t.Base = BaseStyle.Baseboard;
            t.Pier = pier;
            t.SupplyBox = false;
        }
        int bays = (A + 1) / 3; // whole bays along the long side; what is left over is solid
        var rooms = new List<ArchRoom>();
        int lampPhase = 0;
        int deadEnd = -1, deadEndC = 0;

        void Reset()
        {
            for (int v = 1; v < p.H; v++)
                for (int u = 1; u < p.W; u++)
                {
                    p.At(u, v) = default;
                    p.Hall[v * p.W + u] = HallNone;
                }
            rooms.Clear();
            deadEnd = -1;
        }

        // The wall row of bays for the part of a row from column a0 + 1 to a1, with the bays opening from d0 on the lattice
        void Bays(int front, int d0, int last, int window)
        {
            for (int a = d0; a <= last; a++)
            {
                if (a < 1) continue;
                if (a % 3 == 0 || a > bays * 3) { Wall(a, front); continue; }
                int bay = (a - d0 - 1) / 3;
                Arch(a, front, window == bay, Along((a - d0) % 3 == 1));
            }
        }

        // ---- the arcade street ----
        bool Street()
        {
            int span = C - 7;
            if (span < 12) return false;
            int north = Math.Clamp(span / 2 + p.Rng.Range(-6, 6), 6, span - 6), south = span - north;
            int cs = north + 2; // the street's first row
            // Rows of rooms to each side, outward from the street: (first row, last row, the wall row they open through)
            List<(int C0, int C1, int Front)> Side(int space, bool northSide)
            {
                int n = Math.Max(1, (int)Math.Round((space + 1) / 8.0)), total = space - (n - 1);
                var depth = new int[n];
                for (int k = 0; k < n; k++) depth[k] = total / n;
                for (int k = 0; k < total % n; k++) depth[p.Rng.Range(0, n - 1)]++;
                var rows = new List<(int, int, int)>();
                int front = northSide ? cs - 1 : cs + 5;
                for (int k = 0; k < n; k++)
                {
                    if (northSide) { rows.Add((front - depth[k], front - 1, front)); front -= depth[k] + 1; }
                    else { rows.Add((front + 1, front + depth[k], front)); front += depth[k] + 1; }
                }
                return rows;
            }
            var sides = new[] { Side(north, true), Side(south, false) };
            foreach (var side in sides) foreach (var row in side) if (barred[row.Front]) return false;

            for (int s = 0; s < 2; s++)
            {
                bool northSide = s == 0;
                for (int k = 0; k < sides[s].Count; k++)
                {
                    var (c0, c1, front) = sides[s][k];
                    bool outermost = k == sides[s].Count - 1;
                    if (!Row(c0, c1, front, northSide ? c0 : c1, outermost ? sideGaps[s] : null)) return false;
                }
            }
            for (int c = cs; c < cs + 5; c++) for (int a = 1; a <= A; a++) p.Hall[(swap ? a : c) * p.W + (swap ? c : a)] = HallStreet;
            lampPhase = Hashing.Mod(cs + 2, 3);
            // Where the street ends against a wall with no gap in it: a dead end, with a supply box
            bool Gapped(int end) { foreach (int g in endGaps[end]) if (g + 1 >= cs - 1 && g <= cs + 5) return true; return false; }
            for (int end = 0; end < 2 && deadEnd < 0; end++)
                if (!Gapped(end)) { deadEnd = end; deadEndC = cs + 2; }
            return true;
        }

        // One row of rooms between the wall rows 'front' and its own far wall, cut into rooms of two to four bays
        bool Row(int c0, int c1, int front, int back, List<int> gaps)
        {
            // Dividers sit on piers (every third column), and not on a gap's way in
            bool Allowed(int b)
            {
                if (gaps == null) return true;
                foreach (int g in gaps) if (g == b * 3 || g + 1 == b * 3) return false;
                return true;
            }
            var ok = new bool[bays + 1];
            ok[bays] = true;
            for (int b = bays - 1; b >= 0; b--)
            {
                if (b > 0 && !Allowed(b)) continue;
                for (int size = 2; size <= 4 && !ok[b]; size++) if (b + size <= bays && ok[b + size]) ok[b] = true;
            }
            if (!ok[0]) return false;
            var sizes = new List<int>();
            for (int b = 0; b < bays;)
            {
                int pick = 0;
                double r = p.Rng.NextDouble();
                int[] order = r < 0.6 ? new[] { 3, 2, 4 } : r < 0.9 ? new[] { 2, 3, 4 } : new[] { 4, 3, 2 };
                foreach (int size in order) if (b + size <= bays && ok[b + size]) { pick = size; break; }
                if (pick == 0) return false;
                sizes.Add(pick);
                b += pick;
            }
            int at = 0;
            var dividers = new List<int>();
            for (int i = 0; i < sizes.Count; i++)
            {
                int d0 = at * 3;
                bool last = i == sizes.Count - 1;
                at += sizes[i];
                int a1 = last ? A : at * 3 - 1;
                int window = sizes[i] >= 3 && p.Rng.Chance(0.5) ? (p.Rng.Chance(0.5) ? 0 : sizes[i] - 1) : -1;
                if (d0 > 0)
                {
                    for (int c = c0; c <= c1; c++) Wall(d0, c);
                    dividers.Add(d0);
                }
                Bays(front, d0, last ? A : at * 3, window);
                rooms.Add(new ArchRoom(d0 + 1, a1, c0, c1, back));
            }
            // An enfilade: a two-wide arch in about a third of the walls between neighbouring rooms
            foreach (int d in dividers)
            {
                if (!p.Rng.Chance(0.3) || c1 - c0 < 4) continue;
                int c = p.Rng.Range(c0 + 1, c1 - 2);
                Arch(d, c, false, Across(true));
                Arch(d, c + 1, false, Across(false));
            }
            return true;
        }

        // ---- the cloister ----
        bool Cloister()
        {
            var rows = new List<int>();
            int row = 5 + p.Rng.Range(0, 2);
            while (row <= C - 4)
            {
                if (!barred[row]) rows.Add(row);
                else { row++; continue; }
                if (rows.Count == 3) break;
                row += p.Rng.Range(5, 6);
            }
            if (rows.Count < 2) return false;
            foreach (int c in rows)
                for (int a = 1; a <= A; a++)
                {
                    if (a % 3 == 0 || a > bays * 3) Wall(a, c);
                    else Arch(a, c, false, Along(a % 3 == 1));
                }
            lampPhase = Hashing.Mod((1 + rows[0] - 1) / 2, 3);
            return true;
        }

        bool built = false;
        bool cloister = p.W >= 30 && p.H >= 30 && p.Rng.Chance(0.25);
        for (int attempt = 0; attempt < 240 && !built; attempt++)
        {
            Reset();
            bool style = attempt < 120 ? cloister : !cloister;
            built = (style ? Cloister() : Street()) && ArchesSound(p, openings);
        }
        if (!built)
        {
            Reset();
            lampPhase = 0;
            deadEnd = -1;
        }

        // Lights: a lattice three apart that puts a fixture over the second opening of every bay and over the middle of
        // the street, so the pale areas are lit as evenly as any lit area (and no darker)
        p.Lamp = new byte[p.W * p.H];
        for (int v = 1; v < p.H; v++)
            for (int u = 1; u < p.W; u++)
            {
                int a = swap ? v : u, c = swap ? u : v;
                if (p.At(u, v).Kind != TileKind.Floor || a % 3 != 2 || Hashing.Mod(c - lampPhase, 3) != 0) continue;
                bool emit = (a / 3) % 2 == 0 && Hashing.Mod(Hashing.FloorDiv(c - lampPhase, 3), 2) == 0;
                p.Lamp[v * p.W + u] = (byte)(emit ? 2 : 1);
            }

        // Supply boxes: in the far corner of about one room in two, and at a street's dead end; never beside an arch,
        // and never where an arch in the district's wall looks onto
        bool Free(int a, int c)
        {
            int u = swap ? c : a, v = swap ? a : c;
            if (!p.Inner(u, v) || p.At(u, v).Kind != TileKind.Floor || noBox[v * p.W + u]) return false;
            foreach ((int du, int dv) in Steps4)
                if (p.In(u + du, v + dv) && p.At(u + du, v + dv).Kind is TileKind.ArchDoor or TileKind.ArchWindow) return false;
            return true;
        }
        foreach (var room in rooms)
        {
            if (!p.Rng.Chance(0.5)) continue;
            bool left = p.Rng.Chance(0.5);
            foreach (int a in left ? new[] { room.A0, room.A1 } : new[] { room.A1, room.A0 })
                if (Free(a, room.Back)) { T(a, room.Back).SupplyBox = true; break; }
        }
        if (deadEnd >= 0)
        {
            int a = deadEnd == 0 ? 1 : A;
            if (Free(a, deadEndC)) T(a, deadEndC).SupplyBox = true;
        }
        if (built && rooms.Count == 0)
        {
            // A cloister: a box or two in the corners of the hall
            var corners = new List<(int, int)> { (1, 1), (A, 1), (1, C), (A, C) };
            for (int n = p.Rng.Range(1, 2); n > 0 && corners.Count > 0; n--)
            {
                int k = p.Rng.Range(0, corners.Count - 1);
                (int a, int c) = corners[k];
                corners.RemoveAt(k);
                if (Free(a, c)) T(a, c).SupplyBox = true;
            }
        }
    }

    /// <summary>
    /// Whether a plan of an arched area is sound: all of its floor one piece, floor (not a wall, a box or another arch)
    /// behind every opening of the district's own walls and on both faces of every arch, and every arch standing
    /// between a pier and its partner (so <see cref="MendArches"/> would change nothing).
    /// </summary>
    private static bool ArchesSound(L0Plan p, List<(int U, int V, int DU, int DV)> openings)
    {
        int[] comp = LabComponents(p, out int count, out _);
        if (count != 1) return false;
        foreach (var o in openings)
            for (int k = 0; k < 2; k++)
            {
                int u = o.U + (o.DU == 0 ? k : 0), v = o.V + (o.DV == 0 ? k : 0);
                if (!p.Inner(u, v) || p.At(u, v).Kind != TileKind.Floor) return false;
            }
        for (int v = 1; v < p.H; v++)
            for (int u = 1; u < p.W; u++)
            {
                ref Tile t = ref p.At(u, v);
                if (t.Kind is not (TileKind.ArchDoor or TileKind.ArchWindow)) continue;
                (int du, int dv) = t.Pier switch { ArchPier.West => (-1, 0), ArchPier.East => (1, 0), ArchPier.North => (0, -1), _ => (0, 1) };
                bool pier = !p.In(u + du, v + dv) || p.At(u + du, v + dv).Kind == TileKind.Wall;
                bool partner = !p.In(u - du, v - dv) || p.At(u - du, v - dv).Kind is TileKind.ArchDoor or TileKind.ArchWindow;
                if (!pier || !partner) return false;
                // The faces: the two tiles across the wall
                foreach (int s in new[] { 1, -1 })
                {
                    int fu = u + (dv != 0 ? s : 0), fv = v + (du != 0 ? s : 0);
                    if (p.In(fu, fv) && (p.At(fu, fv).Kind != TileKind.Floor || p.At(fu, fv).SupplyBox)) return false;
                }
            }
        return true;
    }
}
