using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 52's round-4 courts (2026-11-02; docs/design/experimental-levels/52-plan.md, "Round 4"): the basketball hoops as
/// set pieces of several blocks (outdoors a post a block behind the board with two arms out to it; in a gym a braced truss
/// off the end wall), the board a block up from the rim, the rim and net hanging into the air in front of the board at 3
/// blocks; the courts' painted markings (the key, the free-throw circle, the three-point arc, the centre circle) as flat
/// decals over the floor; the gym's scoreboard and wall mats; a chain-link fence round a courtyard's court.
/// The blocks are tools/gen_52_r4.py's (<c>l52-hoop-*</c>, <c>l52-mark-*</c>, <c>l52-score-*</c>, <c>l52-wallmat-*</c>).
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The cells of a hoop's markings that carry paint (tools/gen_52_r4.py's <c>MARK_CELLS</c>: k(i+7)_j about the hoop, c(i+2)_(j+2) about the centre).</summary>
    private static readonly HashSet<string> L52MarkCells = new(
        ("c0_1 c0_2 c0_3 c1_0 c1_1 c1_3 c1_4 c2_0 c2_4 c3_0 c3_1 c3_3 c3_4 c4_1 c4_2 c4_3 k0_0 k0_1 k0_2 k0_3 k10_7 k11_6 k11_7 k12_5 " +
         "k12_6 k13_3 k13_4 k13_5 k14_0 k14_1 k14_2 k14_3 k1_3 k1_4 k1_5 k2_5 k2_6 k3_6 k3_7 k4_7 k5_0 k5_1 k5_2 k5_3 k5_4 k5_5 k5_6 k5_7 " +
         "k6_0 k6_1 k6_2 k6_3 k6_4 k6_5 k6_6 k6_7 k6_8 k7_0 k7_1 k7_2 k7_3 k7_4 k7_5 k7_6 k7_8 k8_0 k8_1 k8_2 k8_3 k8_4 k8_5 k8_6 k8_7 " +
         "k8_8 k9_0 k9_1 k9_2 k9_3 k9_4 k9_5 k9_6 k9_7").Split(' '));

    /// <summary>The right hand of someone looking the given way.</summary>
    private static ArchPier L52RightOf(ArchPier looking) => L52Opposite(L52LeftOf(looking));

    /// <summary>
    /// A hoop whose board stands on tile (<paramref name="bu"/>, <paramref name="bv"/>) (the court's baseline), facing
    /// <paramref name="facing"/> into the court: the board at rel 4, the rim and net in front at rel 3; behind it a post
    /// (yard) or, in a gym, the truss back to the end wall two tiles behind.
    /// </summary>
    private static void L52LayHoop(L52Campus c, int bu, int bv, ArchPier facing, bool gym)
    {
        var (fu, fv) = L52Step(facing);
        string s = L52Side(facing), kind = gym ? "gym" : "yard";
        L52Fix(c, bu, bv, $"l52-hoop-board-{kind}-{s}", 4, 4);
        L52Fix(c, bu + fu, bv + fv, $"l52-hoop-rim-{kind}-{s}", 3, 3);
        if (gym)
        {
            L52Fix(c, bu - fu, bv - fv, $"l52-hoop-truss-mid-{s}", 4, 4);
            L52Fix(c, bu - 2 * fu, bv - 2 * fv, $"l52-hoop-truss-wall-{s}", 4, 4);
            L52Fix(c, bu - 2 * fu, bv - 2 * fv, $"l52-hoop-brace-{s}", 3, 3);
            return;
        }
        int pu = bu - fu, pv = bv - fv;
        L52Fix(c, pu, pv, $"l52-hoop-pole-base-{s}", 1, 1);
        L52Fix(c, pu, pv, $"l52-hoop-pole-mid-{s}", 2, 2);
        L52Fix(c, pu, pv, $"l52-hoop-pole-neck-{s}", 3, 3);
        L52Fix(c, pu, pv, $"l52-hoop-pole-top-{s}", 4, 4);
    }

    /// <summary>
    /// The markings about the hoop whose baseline tile is (<paramref name="bu"/>, <paramref name="bv"/>): cells up to
    /// <paramref name="halfW"/> to either side and <paramref name="len"/> into the court (so they stop short of the side
    /// lines and the half line, which are the floor's own).
    /// </summary>
    private static void L52LayMarks(L52Campus c, int bu, int bv, ArchPier facing, string surf, int halfW, int len)
    {
        var (fu, fv) = L52Step(facing);
        var (ru, rv) = L52Step(L52RightOf(facing));
        string s = L52Side(facing);
        for (int j = 0; j <= Math.Min(8, len); j++)
            for (int i = -Math.Min(7, halfW); i <= Math.Min(7, halfW); i++)
            {
                string cell = $"k{i + 7}_{j}";
                if (!L52MarkCells.Contains(cell)) continue;
                int u = bu + fu * j + ru * i, v = bv + fv * j + rv * i;
                if (L52FixFree(c, u, v, 1, 1)) L52Fix(c, u, v, $"l52-mark-{surf}-{cell}-{s}", 1, 1);
            }
    }

    /// <summary>The centre circle about tile (<paramref name="mu"/>, <paramref name="mv"/>).</summary>
    private static void L52LayCentreCircle(L52Campus c, int mu, int mv, ArchPier facing, string surf)
    {
        var (fu, fv) = L52Step(facing);
        var (ru, rv) = L52Step(L52RightOf(facing));
        string s = L52Side(facing);
        for (int j = -2; j <= 2; j++)
            for (int i = -2; i <= 2; i++)
            {
                string cell = $"c{i + 2}_{j + 2}";
                if (!L52MarkCells.Contains(cell)) continue;
                int u = mu + fu * j + ru * i, v = mv + fv * j + rv * i;
                if (L52FixFree(c, u, v, 1, 1)) L52Fix(c, u, v, $"l52-mark-{surf}-{cell}-{s}", 1, 1);
            }
    }

    /// <summary>
    /// A courtyard's basketball court (its floor and lines laid by L52LayCourtyard: the court from cu0 to cu1 along u, cv0
    /// to cv1 across): a hoop at each end on its post, the markings, the centre circle, and a chain-link fence two tiles
    /// out with a gap in the middle of each long side and wherever a path meets it.
    /// </summary>
    private static void L52LayYardCourt(L52Campus c, int cu0, int cu1, int cv0, int cv1, int mu, int mv)
    {
        int hw = mu - cu0, hd = mv - cv0;
        L52LayHoop(c, cu0, mv, ArchPier.East, false);
        L52LayHoop(c, cu1, mv, ArchPier.West, false);
        L52LayMarks(c, cu0, mv, ArchPier.East, "yard", hd - 1, hw - 1);
        L52LayMarks(c, cu1, mv, ArchPier.West, "yard", hd - 1, hw - 1);
        L52LayCentreCircle(c, mu, mv, ArchPier.East, "yard");
        int fu0 = cu0 - 2, fu1 = cu1 + 2, fv0 = cv0 - 2, fv1 = cv1 + 2;
        for (int v = fv0; v <= fv1; v++)
            for (int u = fu0; u <= fu1; u++)
            {
                bool sideU = u == fu0 || u == fu1, sideV = v == fv0 || v == fv1;
                if (!sideU && !sideV || !c.InGrid(u, v)) continue;
                ref Tile t = ref c.At(u, v);
                if (t.Kind != TileKind.Floor || t.Zone is not ((byte)L52Zone.Turf or (byte)L52Zone.Court)) continue;
                if (sideV && !sideU && Math.Abs(u - mu) <= 1) continue;
                t.Zone = (byte)L52Zone.Court;
                t.Variant = 0;
                string axis = sideU ? "ns" : "we", kind = (sideU ? v : u) % 3 == 0 || sideU && sideV ? "chainpost" : "chainlink";
                L52Fix(c, u, v, $"l52-{kind}-lower-{axis}", 1, 1);
                L52Fix(c, u, v, $"l52-{kind}-upper-{axis}", 2, 2);
            }
    }

    /// <summary>
    /// A gym (one hall two storeys high; its court lines two in from the walls): a hoop off each end wall on its truss, the
    /// markings, the centre circle, wall mats either side of the hoops, the scoreboard high on a long wall where no window is.
    /// </summary>
    private static void L52LayGym(L52Campus c, L52Room r)
    {
        ArchPier side = r.DoorSide;
        bool alongX = side is ArchPier.North or ArchPier.South;
        int la = alongX ? r.U1 - r.U0 + 1 : r.V1 - r.V0 + 1, ld = alongX ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1;
        if (la < 16 || ld < 10) return;
        ArchPier toHighA = alongX ? ArchPier.East : ArchPier.South, toLowA = L52Opposite(toHighA), intoRoom = L52Opposite(side);
        int dm = ld / 2, halfW = dm - 3, len = (la - 5) / 2 - 1;
        foreach (var (a, facing, behind) in new[] { (2, toHighA, -1), (la - 3, toLowA, la) })
        {
            var (bu, bv) = L52RoomTile(r, side, a, dm);
            L52LayHoop(c, bu, bv, facing, true);
            L52LayMarks(c, bu, bv, facing, "gym", halfW, len);
            // Wall mats along the end wall either side of the hoop, where the wall behind is wall
            int wa = facing == toHighA ? 0 : la - 1;
            for (int d = dm - 4; d <= dm + 4; d++)
            {
                var (wu, wv) = L52RoomTile(r, side, wa, d);
                var (xu, xv) = L52RoomTile(r, side, behind, d);
                if (!c.InGrid(xu, xv) || c.At(xu, xv).Kind != TileKind.Wall || !L52FixFree(c, wu, wv, 1, 2)) continue;
                L52Fix(c, wu, wv, $"l52-wallmat-lower-{L52Side(facing)}", 1, 1);
                L52Fix(c, wu, wv, $"l52-wallmat-upper-{L52Side(facing)}", 2, 2);
            }
        }
        var (cu, cv) = L52RoomTile(r, side, (2 + la - 3) / 2, dm);
        L52LayCentreCircle(c, cu, cv, toHighA, "gym");
        // The scoreboard: three blocks wide, two high (rel 5 and 6), hung where no window is behind it: a long wall nearest the
        // middle, else an end wall beside the hoop (the changing rooms' cross wall has none), else a long wall over its windows
        bool TryBoard((int U, int V)[] tiles, (int U, int V)[] walls, ArchPier faces, bool overWindows)
        {
            for (int m = 0; m < 3; m++)
            {
                var (xu, xv) = walls[m];
                if (!c.InGrid(xu, xv) || c.At(xu, xv).Kind == TileKind.Floor || !overWindows && c.At(xu, xv).Under == Unders.L52Window
                    || !L52FixFree(c, tiles[m].U, tiles[m].V, 5, 6)) return false;
            }
            // (l, m, r as seen from in front: order the three from the viewer's left)
            var (rdu, rdv) = L52Step(L52RightOf(faces));
            bool forward = (tiles[2].U - tiles[0].U) * rdu + (tiles[2].V - tiles[0].V) * rdv > 0;
            for (int m = 0; m < 3; m++)
            {
                var (tu, tv) = tiles[forward ? m : 2 - m];
                string part = m == 0 ? "l" : m == 1 ? "m" : "r";
                L52Fix(c, tu, tv, $"l52-score-{part}-lo-{L52Side(faces)}", 5, 5);
                L52Fix(c, tu, tv, $"l52-score-{part}-hi-{L52Side(faces)}", 6, 6);
            }
            return true;
        }
        foreach (bool overWindows in new[] { false, true })
        {
            foreach (var (d, faces, wallD) in new[] { (0, intoRoom, -1), (ld - 1, side, ld) })
                for (int k = 0; k <= la / 2 - 3; k++)
                    foreach (int a0 in new[] { la / 2 - 1 - k, la / 2 - 1 + k })
                    {
                        if (a0 < 3 || a0 + 2 > la - 4) continue;
                        var tiles = new (int, int)[3];
                        var walls = new (int, int)[3];
                        for (int m = 0; m < 3; m++) { tiles[m] = L52RoomTile(r, side, a0 + m, d); walls[m] = L52RoomTile(r, side, a0 + m, wallD); }
                        if (TryBoard(tiles, walls, faces, overWindows)) return;
                    }
            if (overWindows) break;
            foreach (var (a, faces, wallA) in new[] { (la - 1, toLowA, la), (0, toHighA, -1) })
                foreach (int d0 in new[] { dm + 3, dm - 5 })
                {
                    if (d0 < 1 || d0 + 2 > ld - 2) continue;
                    var tiles = new (int, int)[3];
                    var walls = new (int, int)[3];
                    for (int m = 0; m < 3; m++) { tiles[m] = L52RoomTile(r, side, a, d0 + m); walls[m] = L52RoomTile(r, side, wallA, d0 + m); }
                    if (TryBoard(tiles, walls, faces, false)) return;
                }
        }
    }

    /// <summary>
    /// A projector hung from the ceiling in the middle of every classroom, storey by storey (a room is a classroom on some
    /// storeys only), its lens toward the board: the board's end as L52Furnish picks it.
    /// </summary>
    private void L52LayProjectors(L52Campus c, L52Room r)
    {
        if (r.Kind is not (L52RoomKind.Classroom or L52RoomKind.Lodging) || r.Building < 1 || r.Building > c.Buildings.Count) return;
        ArchPier side = r.DoorSide;
        bool alongX = side is ArchPier.North or ArchPier.South;
        int la = alongX ? r.U1 - r.U0 + 1 : r.V1 - r.V0 + 1, ld = alongX ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1;
        if (la < 6 || ld < 4) return;
        ArchPier toLowA = alongX ? ArchPier.West : ArchPier.North, toHighA = L52Opposite(toLowA);
        int storeys = c.Buildings[r.Building - 1].Storeys;
        for (int storey = 0; storey < storeys; storey++)
        {
            if (L52KindOn(c, r, storey) != L52RoomKind.Classroom) continue;
            ulong h = Hashing.Hash(seed, c.Head.X0 + r.U0 + storey * 131, c.Head.Z0 + r.V0, SaltL52Room);
            bool boardLow = (h & 1) == 0;
            int dEnd = Math.Min(ld - 2, 6), a = boardLow ? la / 2 - 1 : la - la / 2, d = (1 + dEnd + 1) / 2;
            var (u, v) = L52RoomTile(r, side, a, d);
            int rel = storey * L52Storey + 3;
            if (L52FixFree(c, u, v, rel, rel)) L52Fix(c, u, v, $"l52-projector-{L52Side(boardLow ? toLowA : toHighA)}", rel, rel);
            // A poster on the back wall, facing the board, in about half the classrooms
            if ((h >> 40 & 1) == 0) continue;
            int pa = boardLow ? la - 1 : 0, pd = ld / 2;
            var (pu, pv) = L52RoomTile(r, side, pa, pd);
            var (wu, wv) = L52RoomTile(r, side, boardLow ? la : -1, pd);
            string poster = (h >> 41 & 3) switch { 0 => "run", 1 => "quiet", 2 => "fire", _ => "hands" };
            if (c.InGrid(wu, wv) && c.At(wu, wv).Kind == TileKind.Wall && L52FixFree(c, pu, pv, storey * L52Storey + 2, storey * L52Storey + 2))
                L52Fix(c, pu, pv, $"l52-sign-poster-{poster}-{L52Side(boardLow ? toLowA : toHighA)}", storey * L52Storey + 2, storey * L52Storey + 2);
        }
    }

    /// <summary>
    /// Columns under the outer corners of every entrance canopy (L52LayEntrances lays the canopy three tiles out, a tile
    /// wider than the door each side): base, shaft and cap up to the canopy's soffit.
    /// </summary>
    private static void L52LayCanopyColumns(L52Campus c)
    {
        for (int v = 0; v < c.D; v++)
            for (int u = 0; u < c.W; u++)
            {
                Tile e = c.At(u, v);
                if (e.Zone != (byte)L52Zone.Entrance || e.Depth == 0) continue;
                var (ou, ov) = L52Step(e.Pier);
                if (!c.InGrid(u + ou, v + ov) || c.At(u + ou, v + ov).Depth != 0) continue;
                var (au, av) = L52Step(L52LeftOf(e.Pier));
                foreach (int l in new[] { -1, 1 })
                {
                    int pu = u + ou * 3 + au * l, pv = v + ov * 3 + av * l;
                    if (!c.InGrid(pu, pv) || !c.InGrid(pu + au * l, pv + av * l) || !c.InGrid(pu + ou, pv + ov)) continue;
                    Tile p = c.At(pu, pv);
                    if (p.Overhead != Overheads.L52Canopy || c.At(pu + au * l, pv + av * l).Overhead == Overheads.L52Canopy
                        || c.At(pu + ou, pv + ov).Overhead == Overheads.L52Canopy || !L52FixFree(c, pu, pv, 1, 3)) continue;
                    L52Fix(c, pu, pv, "l52-column-base", 1, 1);
                    L52Fix(c, pu, pv, "l52-column-shaft", 2, 2);
                    L52Fix(c, pu, pv, "l52-column-cap", 3, 3);
                    // A planter against the wall just beyond the canopy's side
                    int qu = u + ou + au * l * 2, qv = v + ov + av * l * 2;
                    if (c.InGrid(qu, qv) && c.At(qu, qv).Depth == 0 && c.At(qu, qv).Kind == TileKind.Floor && c.At(qu, qv).Overhead != Overheads.L52Canopy
                        && c.At(qu, qv).Variant == 0 && L52FixFree(c, qu, qv, 1, 1) && c.At(qu - ou, qv - ov).Depth > 0)
                        L52Fix(c, qu, qv, "l52-planter", 1, 1);
                }
            }
    }
}
