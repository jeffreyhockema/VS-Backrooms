using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 0's arched areas from layout version 10 (second redesign): the Lobby's own rooms, halls and doorways in plain
/// cream stucco, with some of the walls between two spaces made walls of archways, as in the wiki's photo ("a yellowish
/// beige room with a wall of archways"): a row of bays along most of the wall, each a pier and two half-height wall
/// blocks under a round arch, seen through and not walked through. People use the ordinary doorways the planner cut, or
/// now and then a full-height arch door in one bay.
///
/// <para>Which walls: a wall is a candidate where a run of its tiles has floor on both faces, never another wall (so a
/// window always looks onto a room or a hall). Every room gets one arch wall if it has a candidate, a transition room
/// (one an opening of the district leads into) or a dead end gets a second one half the time, and no room gets more
/// than two (a hall three), so every room keeps plain stucco walls. The floor is not touched, so the district is as
/// connected as the Lobby plan it came from.</para>
/// </summary>
public sealed partial class WorldLayout
{
    private void ArchWalls(L0Plan p, int[] comp, int count, List<(int U, int V, int DU, int DV)> openings)
    {
        if (count == 0) return;
        int W = p.W, H = p.H;
        bool Floor(int u, int v) => p.Inner(u, v) && p.At(u, v).Kind == TileKind.Floor;
        // The rooms either side of a doorway: how many other rooms each opens onto (a dead end opens onto one)
        var links = new HashSet<(int, int)>();
        for (int v = 1; v < H; v++)
            for (int u = 1; u < W; u++)
            {
                if (comp[v * W + u] >= 0 || p.At(u, v).Kind != TileKind.Floor) continue;
                foreach ((int du, int dv) in new[] { (1, 0), (0, 1) })
                {
                    if (!p.Inner(u - du, v - dv) || !p.Inner(u + du, v + dv)) continue;
                    int a = comp[(v - dv) * W + u - du], b = comp[(v + dv) * W + u + du];
                    if (a >= 0 && b >= 0 && a != b) { links.Add((a, b)); links.Add((b, a)); }
                }
            }
        var degree = new int[count];
        foreach (var (a, _) in links) degree[a]++;
        var transition = new bool[count];
        foreach (var o in openings) if (p.Inner(o.U, o.V) && comp[o.V * W + o.U] >= 0) transition[comp[o.V * W + o.U]] = true;

        // Candidate walls: maximal runs of tiles with floor on both faces, along x (axis 0) and along z (axis 1)
        var runs = new List<(int Axis, int Line, int S, int E, int A, int B)>();
        for (int axis = 0; axis < 2; axis++)
        {
            int lines = axis == 0 ? H : W, len = axis == 0 ? W : H;
            for (int line = 1; line < lines - 1; line++)
            {
                int s = -1;
                for (int k = 1; k <= len; k++)
                {
                    int u = axis == 0 ? k : line, v = axis == 0 ? line : k;
                    bool ok = k < len && p.At(u, v).Kind == TileKind.Wall && p.At(u, v).Pattern == WallPattern.Stucco && p.At(u, v).Variant == 0
                        && (axis == 0 ? Floor(u, v - 1) && Floor(u, v + 1) : Floor(u - 1, v) && Floor(u + 1, v));
                    if (ok) { if (s < 0) s = k; continue; }
                    if (s >= 0) { AddRun(axis, line, s, k - 1); s = -1; }
                }
            }
        }
        void AddRun(int axis, int line, int s, int e)
        {
            // A wall on the far side of an end (a wall crossing, say) is where the last bay's pier is
            bool Solid(int k) { int u = axis == 0 ? k : line, v = axis == 0 ? line : k; return p.In(u, v) && p.At(u, v).Kind == TileKind.Wall; }
            if (Solid(s - 1)) s--;
            if (Solid(e + 1)) e++;
            if (e - s + 1 < 7) return;
            int mid = (s + e) / 2, mu = axis == 0 ? mid : line, mv = axis == 0 ? line : mid;
            int a = axis == 0 ? comp[(mv - 1) * W + mu] : comp[mv * W + mu - 1], b = axis == 0 ? comp[(mv + 1) * W + mu] : comp[mv * W + mu + 1];
            runs.Add((axis, line, s, e, a, b));
        }
        if (runs.Count == 0) return;

        var done = new int[count];
        var wanted = new bool[runs.Count];
        var hallOf = new bool[count];
        for (int n = 0; n < comp.Length; n++) if (comp[n] >= 0 && p.Hall[n] != HallNone) hallOf[comp[n]] = true;
        bool Cap(int c) => c < 0 || done[c] < (hallOf[c] ? 3 : 2);

        // Longest candidates first within a random shuffle bias; each room in turn is given one
        var order = new List<int>();
        for (int i = 0; i < runs.Count; i++) order.Add(i);
        for (int i = order.Count - 1; i > 0; i--) { int j = p.Rng.Range(0, i); (order[i], order[j]) = (order[j], order[i]); }
        order.Sort((x, y) => Math.Min(3, (runs[y].E - runs[y].S) / 6).CompareTo(Math.Min(3, (runs[x].E - runs[x].S) / 6)));
        void Take(int i) { wanted[i] = true; if (runs[i].A >= 0) done[runs[i].A]++; if (runs[i].B >= 0) done[runs[i].B]++; }
        var rooms = new List<int>();
        for (int c = 0; c < count; c++) rooms.Add(c);
        for (int i = rooms.Count - 1; i > 0; i--) { int j = p.Rng.Range(0, i); (rooms[i], rooms[j]) = (rooms[j], rooms[i]); }
        foreach (int c in rooms)
        {
            int want = 1 + ((transition[c] || degree[c] <= 1) && p.Rng.Chance(0.5) ? 1 : 0);
            foreach (int i in order)
            {
                if (done[c] >= want) break;
                if (wanted[i] || (runs[i].A != c && runs[i].B != c) || !Cap(runs[i].A) || !Cap(runs[i].B)) continue;
                Take(i);
            }
        }

        for (int i = 0; i < runs.Count; i++)
            if (wanted[i]) Archify(p, runs[i].Axis, runs[i].Line, runs[i].S, runs[i].E);
    }

    /// <summary>A wall run from s to e (inclusive) along a line: a pier at each bay's ends, two half-wall tiles between, the leftover plain wall.</summary>
    private static void Archify(L0Plan p, int axis, int line, int s, int e)
    {
        int len = e - s + 1, bays = (len - 1) / 3, left = (len - 1) % 3;
        int start = s + p.Rng.Range(0, left);
        // A full-height arch door in one bay now and then (never the only way through: the doorways are elsewhere)
        int door = bays >= 3 && p.Rng.Chance(0.25) ? p.Rng.Range(0, bays - 1) : -1;
        for (int bay = 0; bay < bays; bay++)
            for (int k = 1; k <= 2; k++)
            {
                int pos = start + bay * 3 + k;
                ref Tile t = ref p.At(axis == 0 ? pos : line, axis == 0 ? line : pos);
                if (t.Kind != TileKind.Wall) continue;
                t.Kind = bay == door ? TileKind.ArchDoor : TileKind.ArchWindow;
                t.Pattern = WallPattern.Stucco;
                t.Base = BaseStyle.Baseboard;
                t.SupplyBox = false;
                t.Pier = axis == 0 ? (k == 1 ? ArchPier.West : ArchPier.East) : (k == 1 ? ArchPier.North : ArchPier.South);
            }
    }
}
