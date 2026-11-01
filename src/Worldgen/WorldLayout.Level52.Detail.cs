using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 52's round-3 detail (2026-11-01; docs/design/experimental-levels/52-plan.md, "Round 3"): rooms by what they are
/// for (restrooms by the stairs, the front office, the staff room and the library by the lobbies, a floor of labs), the
/// fittings on the walls (EXIT signs, floor numbers and directories, restroom signs, notice boards, posters, fire hose
/// cabinets, the doors standing open, lifts, the M.E.G.'s sign, COOL MART CO., building numbers on the canopies), and the
/// things outdoors and on the roofs built of several blocks (stair bulkheads with their doors, air handlers, vents, a clock
/// tower, a fountain, flagpoles, the boards at the gaps in the fences, a football pitch inside a running track).
///
/// <para>A fitting is a block code at a height on a campus tile (<see cref="L52Fixture"/>, kept in
/// <see cref="L52Campus.Fixtures"/>): on a building's tile its height is <c>rel</c> above the level's floor, or (when
/// <see cref="L52Fixture.EveryStorey"/>) the height in each storey; outdoors, the height above the ground (a campus lies
/// level at the floor, so the same numbers). The generator looks a tile's fittings up before anything else.</para>
///
/// <para>Signs keep to what the lore allows (a door's sign "no subject and no campus name"): numbers, the words every
/// building has, and the people's own signs (the M.E.G.'s, Cool Mart Co.'s, the abandoned bases').</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>A block (by code) fixed at a height on a campus tile: <see cref="Lo"/>-<see cref="Hi"/> as <c>rel</c>, or as the height within every storey.</summary>
    public readonly record struct L52Fixture(string Code, short Lo, short Hi, bool EveryStorey);

    private const ulong SaltL52Detail = 0x2320;

    /// <summary>The way a fitting faces, as the code's last part.</summary>
    private static string L52Side(ArchPier p) => p switch { ArchPier.North => "north", ArchPier.East => "east", ArchPier.South => "south", _ => "west" };

    private static void L52Fix(L52Campus c, int u, int v, string code, int lo, int hi, bool every = false)
    {
        if (!c.InGrid(u, v)) return;
        int i = u + v * c.W;
        if (!c.Fixtures.TryGetValue(i, out var list)) c.Fixtures[i] = list = new List<L52Fixture>(2);
        list.Add(new L52Fixture(code, (short)lo, (short)hi, every));
        c.HasFixture[i] = true;
    }

    private static void L52Sign(L52Campus c, int u, int v, string kind, ArchPier facing, int lo, int hi, bool every = false) =>
        L52Fix(c, u, v, $"l52-sign-{kind}-{L52Side(facing)}", lo, hi, every);

    /// <summary>Whether a tile is free of fittings at a height (as rel, or as every storey's height).</summary>
    private static bool L52FixFree(L52Campus c, int u, int v, int lo, int hi)
    {
        if (!c.InGrid(u, v)) return false;
        if (!c.Fixtures.TryGetValue(u + v * c.W, out var list)) return true;
        foreach (var f in list)
            if (f.EveryStorey || f.Lo <= hi && f.Hi >= lo) return false;
        return true;
    }

    /// <summary>The tile k steps to the right of someone looking at a fitting that faces <paramref name="facing"/> (part k of a sign several blocks wide).</summary>
    private static (int U, int V) L52Right(int u, int v, ArchPier facing, int k)
    {
        var (du, dv) = L52Step(L52LeftOf(facing));
        return (u + du * k, v + dv * k);
    }

    // ================= Rooms by what they are for =================

    /// <summary>
    /// What some rooms of a building are for, on every storey or the ground one: a pair of restrooms by each stairwell, the
    /// front office, the principal's office, the staff room and the library nearest the lobbies (the quad) or the doors
    /// (a block standing apart); a dormitory's front desk.
    /// </summary>
    private void L52AssignRoles(L52Campus c, L52Building b, List<L52Room> mine)
    {
        bool Usable(L52Room r) => r.HasDoor && r.DoorU >= 0 && r.Kind is L52RoomKind.Classroom or L52RoomKind.Lodging && r.GroundKind == null;
        // Restrooms by the stairs (men's by the first landing's door, women's by the second)
        foreach (var (s, bi) in c.Stairs)
        {
            if (bi != b.Index) continue;
            var (jdu, jdv) = L52Step(s.J);
            var (idu, idv) = L52Step(s.I);
            for (int k = 0; k < 2; k++)
            {
                int j = k == 0 ? 0 : 5;
                int du = s.U + j * jdu - idu, dv = s.V + j * jdv - idv;
                L52Room best = null;
                int bestD = 9;
                foreach (L52Room r in mine)
                {
                    if (!Usable(r) || r.Area < 24 || r.Area > 110) continue;
                    int d = Math.Abs(r.DoorU - du) + Math.Abs(r.DoorV - dv);
                    if (d < bestD) { bestD = d; best = r; }
                }
                if (best != null) best.Kind = k == 0 ? L52RoomKind.RestroomMen : L52RoomKind.RestroomWomen;
            }
        }
        // The rooms nearest the ways in: the front office, the principal's office, the staff room, the library
        var ways = new List<(int U, int V)>();
        for (int v = b.V0; v <= b.V1; v++)
            for (int u = b.U0; u <= b.U1; u++)
                if (c.At(u, v).Zone is (byte)L52Zone.Lobby or (byte)L52Zone.Entrance) ways.Add((u, v));
        if (ways.Count == 0) return;
        var near = new List<(int D, L52Room R)>();
        foreach (L52Room r in mine)
        {
            if (!Usable(r)) continue;
            int d = int.MaxValue;
            foreach (var (u, v) in ways) d = Math.Min(d, Math.Abs(r.DoorU - u) + Math.Abs(r.DoorV - v));
            near.Add((d, r));
        }
        near.Sort((x, y) => x.D != y.D ? x.D.CompareTo(y.D) : x.R.Id.CompareTo(y.R.Id));
        L52RoomKind[] order = b.Kind == L52BuildingKind.Lodging
            ? new[] { L52RoomKind.Reception, L52RoomKind.StaffRoom }
            : b.Index == 1 ? new[] { L52RoomKind.Reception, L52RoomKind.Office, L52RoomKind.StaffRoom, L52RoomKind.Library }
            : new[] { L52RoomKind.Office, L52RoomKind.StaffRoom, L52RoomKind.Library };
        int at = 0;
        foreach (var (_, r) in near)
        {
            if (at >= order.Length) break;
            L52RoomKind want = order[at];
            if (want == L52RoomKind.Library && r.Area < 50) continue;
            if (want == L52RoomKind.StaffRoom && r.Area < 40) continue;
            r.GroundKind = want;
            at++;
        }
    }

    /// <summary>The storey a building's labs are on (none in a building of two).</summary>
    private static int L52LabStorey(L52Building b) => b.Storeys >= 3 ? 1 + b.Index % 2 : -1;

    // ================= The fittings =================

    /// <summary>Everything this round adds to a campus, once its plan is laid (before the grounds are furnished).</summary>
    private void L52LayDetails(L52Campus c)
    {
        // Marshall David is worn now, as the lore has it: dirt prints and cracks down its corridors, in patches
        if (c.Head.Kind == L52CampusKind.MarshallDavid)
            for (int v = 0; v < c.D; v++)
                for (int u = 0; u < c.W; u++)
                {
                    ref Tile t = ref c.At(u, v);
                    if (t.Floor == FloorKind.L52Floor && t.Zone is (byte)L52Zone.Corridor or (byte)L52Zone.Lobby
                        && Noise((c.Head.X0 + u) / 9.0, (c.Head.Z0 + v) / 9.0, SaltL52Detail + 5) > 0.42)
                        t.Floor = FloorKind.L52HallWorn;
                }
        L52LayRoomFittings(c);
        L52LayCorridorFittings(c);
        L52LayStairFittings(c);
        L52LayDoorFittings(c);
        L52LayRoofs(c);
        L52LayTower(c);
        L52LayFountain(c);
        L52LayFlags(c);
        L52LayBoards(c);
        L52LayHedges(c);
        L52LayTrophies(c);
        L52LaySkylight(c);
        L52LayTerrace(c);
    }

    /// <summary>Outside a canteen's door on a long side, a few café tables with their chairs on the lawn: where people would eat in the sun.</summary>
    private static void L52LayTerrace(L52Campus c)
    {
        foreach (L52Building b in c.Buildings)
        {
            if (b.Kind != L52BuildingKind.Canteen) continue;
            bool done = false;
            for (int v = b.V0; v <= b.V1 && !done; v++)
                for (int u = b.U0; u <= b.U1 && !done; u++)
                {
                    Tile e = c.At(u, v);
                    if (e.Zone != (byte)L52Zone.Entrance || e.Detail != b.Index) continue;
                    var (ou, ov) = L52Step(e.Pier);
                    var (au, av) = L52Step(L52LeftOf(e.Pier));
                    // (a long side's pair: the door beside it is a door too)
                    if (!c.InGrid(u + au, v + av) || c.At(u + au, v + av).Zone != (byte)L52Zone.Entrance) continue;
                    foreach (int side in new[] { 1, -1 })
                    {
                        int placed = 0;
                        for (int k = 0; k < 3; k++)
                        {
                            int tu = u + ou * 6 + au * side * (5 + k * 4), tv = v + ov * 6 + av * side * (5 + k * 4);
                            bool free = true;
                            for (int dv = -1; dv <= 1 && free; dv++)
                                for (int du = -1; du <= 1 && free; du++)
                                {
                                    int nu = tu + du, nv = tv + dv;
                                    if (!c.InGrid(nu, nv) || c.At(nu, nv).Zone != (byte)L52Zone.Lawn || c.At(nu, nv).Variant != 0 || c.At(nu, nv).Overhead != 0
                                        || c.HasFixture[nu + nv * c.W]) free = false;
                                }
                            if (!free) continue;
                            L52Put(c, tu, tv, Props.CafeTable, e.Pier);
                            foreach (ArchPier w in L52Ways)
                            {
                                var (wu, wv) = L52Step(w);
                                L52Put(c, tu + wu, tv + wv, Props.CafeChair, L52Opposite(w));
                            }
                            placed++;
                        }
                        if (placed > 0) done = true;
                    }
                }
        }
    }

    /// <summary>
    /// On about one ordinary quad in three (not where the courtyard is a court), the courtyard roofed over in glass at the
    /// level of the quad's roof: the lore's courtyards have "a translucent or missing ceiling".
    /// </summary>
    private void L52LaySkylight(L52Campus c)
    {
        if (c.Buildings.Count == 0 || c.Head.Kind != L52CampusKind.Ordinary) return;
        if (Hashing.Unit(Hashing.Hash(seed, c.Head.X0, c.Head.Z0, SaltL52Detail + 6)) > 0.35) return;
        L52Building q = c.Buildings[0];
        int rel = q.Storeys * L52Storey + 1;
        for (int v = q.V0 + 21; v <= q.V1 - 21; v++)
            for (int u = q.U0 + 21; u <= q.U1 - 21; u++)
                if (c.At(u, v).Zone == (byte)L52Zone.Court) return;
        for (int v = q.V0 + 21; v <= q.V1 - 21; v++)
            for (int u = q.U0 + 21; u <= q.U1 - 21; u++)
                if (c.At(u, v).Depth == 0) L52Fix(c, u, v, "l52-skylight", rel, rel);
    }

    /// <summary>Across the corridor from each of the quad's front doors (where the lobby does not run on to the courtyard): two trophy cases against the wall, either side of the lobby's line.</summary>
    private static void L52LayTrophies(L52Campus c)
    {
        if (c.Buildings.Count == 0) return;
        L52Building q = c.Buildings[0];
        for (int v = q.V0; v <= q.V1; v++)
            for (int u = q.U0; u <= q.U1; u++)
            {
                Tile e = c.At(u, v);
                if (e.Zone != (byte)L52Zone.Entrance || u != q.U0 && u != q.U1 && v != q.V0 && v != q.V1) continue;
                var (au, av) = L52Step(L52LeftOf(e.Pier));
                if (!c.InGrid(u + au, v + av) || !c.InGrid(u - au, v - av) || c.At(u + au, v + av).Zone != (byte)L52Zone.Entrance || c.At(u - au, v - av).Zone != (byte)L52Zone.Entrance) continue;
                var (ou, ov) = L52Step(e.Pier);
                int fu = u - ou * 11, fv = v - ov * 11, wu = u - ou * 12, wv = v - ov * 12;
                if (!c.InGrid(wu, wv) || c.At(wu, wv).Kind != TileKind.Wall) continue;
                foreach (int k in new[] { -1, 1 })
                {
                    int tu = fu + au * k, tv = fv + av * k;
                    if (c.At(tu, tv).Zone is (byte)L52Zone.Corridor or (byte)L52Zone.Lobby && c.At(tu - ou, tv - ov).Kind == TileKind.Wall && !c.HasFixture[tu + tv * c.W])
                    {
                        L52Put(c, tu, tv, Props.CurioCabinet, e.Pier);
                        L52Fix(c, tu, tv, "l52-sign-exit-none", 99, 99); // (marks the tile taken: the corridor's things keep off it)
                    }
                }
            }
    }

    /// <summary>A clipped hedge along the quad's outside, a step beyond its paving, broken wherever a path leads off.</summary>
    private static void L52LayHedges(L52Campus c)
    {
        if (c.Buildings.Count == 0) return;
        L52Building q = c.Buildings[0];
        for (int v = q.V0 - 3; v <= q.V1 + 3; v++)
            for (int u = q.U0 - 3; u <= q.U1 + 3; u++)
            {
                if (u != q.U0 - 3 && u != q.U1 + 3 && v != q.V0 - 3 && v != q.V1 + 3 || !c.InGrid(u, v)) continue;
                ref Tile t = ref c.At(u, v);
                if (t.Zone != (byte)L52Zone.Lawn || t.Depth != 0 || t.Variant != 0 || t.Overhead != 0 || c.HasFixture[u + v * c.W]) continue;
                bool nearPath = false;
                for (int dv = -2; dv <= 2 && !nearPath; dv++)
                    for (int du = -2; du <= 2 && !nearPath; du++)
                    {
                        int nu = u + du, nv = v + dv;
                        if (!c.InGrid(nu, nv)) continue;
                        Tile n = c.At(nu, nv);
                        // (a path that does not belong to the apron: one further out than the hedge line)
                        bool apron = nu >= q.U0 - 2 && nu <= q.U1 + 2 && nv >= q.V0 - 2 && nv <= q.V1 + 2;
                        if (n.Zone == (byte)L52Zone.Path && !apron || n.Zone != (byte)L52Zone.Lawn && n.Zone != (byte)L52Zone.Path && n.Depth == 0) nearPath = true;
                    }
                if (nearPath) continue;
                t.Kind = TileKind.Wall; // (not walked through)
                L52Fix(c, u, v, "=hedge", 1, 1);
            }
    }

    /// <summary>The restrooms' signs, mirrors and posters; the doors of rooms standing open against the wall inside.</summary>
    private void L52LayRoomFittings(L52Campus c)
    {
        foreach (L52Room r in c.Rooms)
        {
            if (!r.HasDoor || r.DoorU < 0) continue;
            ArchPier side = r.DoorSide;
            var (su, sv) = L52Step(side);
            bool restroom = r.Kind is L52RoomKind.RestroomMen or L52RoomKind.RestroomWomen;
            if (restroom)
            {
                // The pictogram on the corridor wall to the left of the door, as seen from the corridor
                var (lu, lv) = L52Step(L52LeftOf(L52Opposite(side)));
                int pu = r.DoorU + su + lu, pv = r.DoorV + sv + lv;
                if (c.InGrid(pu, pv) && c.At(pu, pv).Zone is (byte)L52Zone.Corridor or (byte)L52Zone.Lobby && c.At(pu, pv).Overhead == 0
                    && c.At(r.DoorU + lu, r.DoorV + lv).Kind == TileKind.Wall && L52FixFree(c, pu, pv, 2, 2))
                    L52Sign(c, pu, pv, r.Kind == L52RoomKind.RestroomMen ? "men" : "women", side, 2, 2, true);
                // Mirrors over the basins along one end wall, the poster by the door
                bool alongX = side is ArchPier.North or ArchPier.South;
                ArchPier toHighA = alongX ? ArchPier.East : ArchPier.South;
                int la = alongX ? r.U1 - r.U0 + 1 : r.V1 - r.V0 + 1, ld = alongX ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1;
                for (int d = 1; d <= ld - 3; d++)
                {
                    var (mu, mv) = L52RoomTile(r, side, 0, d);
                    L52Sign(c, mu, mv, "mirror", toHighA, 2, 2, true);
                }
                var (qu, qv) = L52RoomTile(r, side, la - 1, 1);
                L52Sign(c, qu, qv, "poster-hands", L52Opposite(toHighA), 2, 2, true);
                continue;
            }
            // A door standing open against the wall beside it, inside (not every room's: about two in three)
            if (r.Kind is L52RoomKind.Empty or L52RoomKind.Gym or L52RoomKind.Canteen or L52RoomKind.Warehouse) continue;
            // A clock over the door, inside, as every classroom has (stopped, like the tower's)
            int cu = r.DoorU - su, cv = r.DoorV - sv;
            if (c.InGrid(cu, cv) && c.RoomOf[cu + cv * c.W] == r.Id && L52FixFree(c, cu, cv, 3, 3))
                L52Sign(c, cu, cv, "wallclock", L52Opposite(side), 3, 3, true);
            ulong h = Hashing.Hash(seed, c.Head.X0 + r.DoorU, c.Head.Z0 + r.DoorV, SaltL52Detail);
            if (Hashing.Unit(h) < 0.33) continue;
            var (au, av) = L52Step(L52LeftOf(side));
            int k = (h >> 20 & 1) == 0 ? 1 : -1;
            int iu = r.DoorU - su + au * k, iv = r.DoorV - sv + av * k;
            if (!c.InGrid(iu, iv) || c.RoomOf[iu + iv * c.W] != r.Id || c.At(iu, iv).Zone != (byte)L52Zone.Room) continue;
            if (c.At(r.DoorU + au * k, r.DoorV + av * k).Kind != TileKind.Wall) continue;
            L52Sign(c, iu, iv, "leaf-lo", L52Opposite(side), 1, 1, true);
            L52Sign(c, iu, iv, "leaf-hi", L52Opposite(side), 2, 2, true);
        }
    }

    /// <summary>A room's tile at <paramref name="a"/> along its door's wall (from its low end) and <paramref name="d"/> in from it.</summary>
    private static (int U, int V) L52RoomTile(L52Room r, ArchPier doorSide, int a, int d)
    {
        bool alongX = doorSide is ArchPier.North or ArchPier.South;
        int u = alongX ? r.U0 + a : doorSide == ArchPier.West ? r.U0 + d : r.U1 - d;
        int v = !alongX ? r.V0 + a : doorSide == ArchPier.North ? r.V0 + d : r.V1 - d;
        return (u, v);
    }

    /// <summary>
    /// Along the corridors' walls, the runs of lockers broken now and then: a fire hose cabinet with an extinguisher under
    /// it, a notice board, a poster; at J. Barry, the alarm bells.
    /// </summary>
    private void L52LayCorridorFittings(L52Campus c)
    {
        for (int v = 1; v < c.D - 1; v++)
            for (int u = 1; u < c.W - 1; u++)
            {
                ref Tile w = ref c.At(u, v);
                if (w.Zone != (byte)L52Zone.Wall || w.Depth == 0) continue;
                foreach (ArchPier side in L52Ways)
                {
                    var (du, dv) = L52Step(side);
                    int cu = u + du, cv = v + dv;
                    if (!c.InGrid(cu, cv) || c.At(cu, cv).Zone != (byte)L52Zone.Corridor || c.At(cu, cv).Overhead != 0) continue;
                    // Not beside a doorway, nor at a corner of the wall
                    var (au, av) = L52Step(L52LeftOf(side));
                    bool ok = true;
                    for (int k = -2; k <= 2 && ok; k++)
                        if (c.InGrid(u + au * k, v + av * k) && c.At(u + au * k, v + av * k).Kind == TileKind.Doorway) ok = false;
                    if (!ok || c.At(u + au, v + av).Kind != TileKind.Wall || c.At(u - au, v - av).Kind != TileKind.Wall) continue;
                    int along = side is ArchPier.North or ArchPier.South ? u : v;
                    int phase = (int)(Hashing.Hash(seed, c.Head.X0 + (side is ArchPier.North or ArchPier.South ? 0 : u), c.Head.Z0 + (side is ArchPier.North or ArchPier.South ? v : 0), SaltL52Detail + 1) % 19);
                    int k19 = Hashing.Mod(along + phase, 19);
                    if (!L52FixFree(c, cu, cv, 1, 3)) continue;
                    if (k19 == 0)
                    {
                        L52Sign(c, cu, cv, "hose", side, 2, 2, true);
                        L52Sign(c, cu, cv, "ext", side, 1, 1, true);
                        w.Under = 0;
                    }
                    else if (k19 == 7)
                    {
                        // A notice board two blocks wide: this tile is its left as seen from the corridor
                        var (ru, rv) = L52Right(cu, cv, side, 1);
                        var (rwu, rwv) = L52Right(u, v, side, 1);
                        if (!c.InGrid(ru, rv) || c.At(ru, rv).Zone != (byte)L52Zone.Corridor || c.At(ru, rv).Overhead != 0 || !L52FixFree(c, ru, rv, 1, 3)
                            || c.At(rwu, rwv).Zone != (byte)L52Zone.Wall) continue;
                        L52Sign(c, cu, cv, "notice-l", side, 2, 2, true);
                        L52Sign(c, ru, rv, "notice-r", side, 2, 2, true);
                        w.Under = 0;
                        c.At(rwu, rwv).Under = 0;
                    }
                    else if (k19 == 13 && w.Under == 0)
                        L52Sign(c, cu, cv, (along / 19 & 1) == 0 ? "poster-run" : "poster-fire", side, 2, 2, true);
                    else if (k19 == 4 && c.Head.Kind == L52CampusKind.JBarry)
                        L52Sign(c, cu, cv, "alarm", side, 3, 3, true);
                    break;
                }
            }
    }

    /// <summary>
    /// The stairwells: an EXIT sign over each door on every storey, a directory beside the first door, the floor's number
    /// on the first landing's wall, a lift beside the quad's first stairwell, the M.E.G.'s sign on Marshall David's top floor.
    /// </summary>
    private void L52LayStairFittings(L52Campus c)
    {
        int index = 0;
        foreach (var (s, bi) in c.Stairs)
        {
            L52Building b = c.Buildings[bi - 1];
            var (jdu, jdv) = L52Step(s.J);
            var (idu, idv) = L52Step(s.I);
            (int U, int V) At(int i, int j) => (s.U + j * jdu + i * idu, s.V + j * jdv + i * idv);
            ArchPier outward = L52Opposite(s.I);
            bool Hall(int i, int j)
            {
                var (u, v) = At(i, j);
                return c.InGrid(u, v) && c.At(u, v).Zone is (byte)L52Zone.Corridor or (byte)L52Zone.Lobby;
            }
            foreach (int j in new[] { 0, 5 })
                if (Hall(-2, j))
                {
                    var (u, v) = At(-2, j);
                    L52Sign(c, u, v, "exit", outward, 3, 3, true);
                }
            if (Hall(-2, 1))
            {
                var (u, v) = At(-2, 1);
                for (int st = 0; st < b.Storeys; st++) L52Sign(c, u, v, $"dir{Math.Min(8, st + 1)}", outward, st * L52Storey + 2, st * L52Storey + 2);
            }
            // The floor's number on the wall at the end of the first landing
            var (fu, fv) = At(1, 0);
            for (int st = 0; st < b.Storeys; st++) L52Sign(c, fu, fv, $"floor{Math.Min(8, st + 1)}", s.J, st * L52Storey + 2, st * L52Storey + 2);
            // Two tiles on the hall side of the stairwell's wall, between its doors: this one the left as seen from the hall
            bool Pair(int j0, out (int U, int V) left, out (int U, int V) right)
            {
                var a = At(-2, j0);
                var bb = At(-2, j0 + 1);
                var r1 = L52Right(a.U, a.V, outward, 1);
                (left, right) = r1 == bb ? (a, bb) : (bb, a);
                return Hall(-2, j0) && Hall(-2, j0 + 1);
            }
            if (bi == 1 && index == 0 && Pair(2, out var l0, out var r0))
            {
                L52Sign(c, l0.U, l0.V, "liftlo-l", outward, 1, 1, true);
                L52Sign(c, r0.U, r0.V, "liftlo-r", outward, 1, 1, true);
                L52Sign(c, l0.U, l0.V, "lifthi-l", outward, 2, 2, true);
                L52Sign(c, r0.U, r0.V, "lifthi-r", outward, 2, 2, true);
            }
            else if (c.Head.Kind == L52CampusKind.MarshallDavid && bi == 1 && Pair(3, out var l1, out var r1))
            {
                int rel = (b.Storeys - 1) * L52Storey + 2;
                L52Sign(c, l1.U, l1.V, "meg-l", outward, rel, rel);
                L52Sign(c, r1.U, r1.V, "meg-r", outward, rel, rel);
            }
            if (bi == 1) index++;
        }
    }

    /// <summary>EXIT over the outside doors (inside), the building's number on the canopy, COOL MART CO. over J. Barry's warehouse doors.</summary>
    private void L52LayDoorFittings(L52Campus c)
    {
        for (int v = 1; v < c.D - 1; v++)
            for (int u = 1; u < c.W - 1; u++)
            {
                Tile e = c.At(u, v);
                if (e.Zone != (byte)L52Zone.Entrance || e.Depth == 0) continue;
                var (ou, ov) = L52Step(e.Pier);
                var (au, av) = L52Step(L52LeftOf(e.Pier));
                bool l = c.InGrid(u + au, v + av) && c.At(u + au, v + av).Zone == (byte)L52Zone.Entrance;
                bool r = c.InGrid(u - au, v - av) && c.At(u - au, v - av).Zone == (byte)L52Zone.Entrance;
                bool middle = l == r || r && !l;
                if (!middle) continue;
                int iu = u - ou, iv = v - ov;
                if (c.InGrid(iu, iv) && c.At(iu, iv).Kind == TileKind.Floor && c.At(iu, iv).Zone != (byte)L52Zone.Stair && L52FixFree(c, iu, iv, 3, 3))
                    L52Sign(c, iu, iv, "exit", L52Opposite(e.Pier), 3, 3);
                if (!c.InGrid(u + ou, v + ov) || c.At(u + ou, v + ov).Depth != 0) continue;
                L52Building b = e.Detail > 0 && e.Detail <= c.Buildings.Count ? c.Buildings[e.Detail - 1] : null;
                if (b == null) continue;
                // Bike racks along the wall beside the door, on the paving (round a teaching block or the quad)
                if (b.Kind is L52BuildingKind.Teaching or L52BuildingKind.Lodging)
                    for (int k = 3; k <= 5; k++)
                    {
                        var (ru, rv) = L52Right(u + ou, v + ov, e.Pier, -k);
                        if (c.InGrid(ru, rv) && c.At(ru, rv).Zone == (byte)L52Zone.Path && c.At(ru, rv).Depth == 0 && c.At(ru, rv).Variant == 0
                            && c.At(ru, rv).Overhead == 0 && !c.HasFixture[ru + rv * c.W] && c.At(ru - ou, rv - ov).Zone == (byte)L52Zone.Ext)
                            L52Fix(c, ru, rv, "l52-bikerack-" + L52Side(e.Pier), 1, 1);
                    }
                // The number at the front of the canopy (its front edge is three out)
                int n = b.Index % 10, fu = u + ou * 4, fv = v + ov * 4;
                if (n > 0 && c.InGrid(fu, fv) && c.At(u + ou * 3, v + ov * 3).Overhead == Overheads.L52Canopy && c.At(fu, fv).Depth == 0)
                    L52Sign(c, fu, fv, $"bnum{n}", e.Pier, L52Storey, L52Storey);
                if (b.Kind == L52BuildingKind.Warehouse && c.Head.Kind == L52CampusKind.JBarry)
                {
                    string[] parts = { "cool-l", "cool-m", "cool-r" };
                    var (lu, lv) = L52Right(u + ou, v + ov, e.Pier, -1);
                    for (int k = 0; k < 3; k++)
                    {
                        var (pu, pv) = L52Right(lu, lv, e.Pier, k);
                        if (c.InGrid(pu, pv) && c.At(pu, pv).Depth == 0) L52Sign(c, pu, pv, parts[k], e.Pier, L52Storey + 1, L52Storey + 1);
                    }
                }
            }
    }

    // ================= The roofs =================

    /// <summary>
    /// On every building's roof: a bulkhead over each stairwell (walls of the building's façade a storey high, a roof, a steel
    /// door on the side its doors are), one to three air handlers (two blocks high, louvred, fan grilles on top), vents.
    /// </summary>
    private void L52LayRoofs(L52Campus c)
    {
        var taken = new HashSet<int>();
        foreach (var (s, bi) in c.Stairs)
        {
            L52Building b = c.Buildings[bi - 1];
            int top = b.Storeys * L52Storey;
            if (top + 5 > 36) continue;
            string facade = "l52-facade-" + L52Facades[b.Facade];
            var (jdu, jdv) = L52Step(s.J);
            var (idu, idv) = L52Step(s.I);
            for (int i = -1; i <= 7; i++)
                for (int j = -1; j <= 7; j++)
                {
                    int u = s.U + j * jdu + i * idu, v = s.V + j * jdv + i * idv;
                    if (!c.InGrid(u, v) || c.At(u, v).Depth == 0) continue;
                    taken.Add(u + v * c.W);
                    bool rim = i == -1 || i == 7 || j == -1 || j == 7;
                    if (rim) L52Fix(c, u, v, facade, top + 2, top + 4);
                    L52Fix(c, u, v, rim ? "l52-coping" : "l52-roof", top + 5, top + 5);
                }
            // The door: in the wall on the stairwell's door side, at the first landing, facing out over the roof
            int du = s.U - 2 * idu, dv = s.V - 2 * idv;
            ArchPier outward = L52Opposite(s.I);
            if (c.InGrid(du, dv) && c.At(du, dv).Depth > 0 && c.At(du, dv).Zone != (byte)L52Zone.Ext)
            {
                L52Sign(c, du, dv, "door-lo", outward, top + 2, top + 2);
                L52Sign(c, du, dv, "door-hi", outward, top + 3, top + 3);
                taken.Add(du + dv * c.W);
            }
        }
        foreach (L52Building b in c.Buildings)
        {
            int top = b.Storeys * L52Storey;
            if (top + 4 > 36) continue;
            ulong h = Hashing.Hash(seed, c.Head.X0 + b.Index * 13, c.Head.Z0 + b.U0, SaltL52Detail + 2);
            int units = 1 + (int)(h % 3), tries = 0;
            var rng = new Rng(Hashing.Mix(h));
            while (units > 0 && tries++ < 30)
            {
                bool alongU = rng.Chance(0.5);
                int w = alongU ? rng.Range(3, 5) : 2, d = alongU ? 2 : rng.Range(3, 5);
                int u0 = rng.Range(b.U0 + 3, Math.Max(b.U0 + 4, b.U1 - 2 - w)), v0 = rng.Range(b.V0 + 3, Math.Max(b.V0 + 4, b.V1 - 2 - d));
                bool ok = u0 + w <= b.U1 - 2 && v0 + d <= b.V1 - 2;
                // (clear of the quad's corners, where a clock tower may stand)
                if (b.Index == 1 && (u0 < b.U0 + 7 || u0 + w > b.U1 - 6) && (v0 < b.V0 + 7 || v0 + d > b.V1 - 6)) ok = false;
                for (int v = v0 - 1; v <= v0 + d && ok; v++)
                    for (int u = u0 - 1; u <= u0 + w && ok; u++)
                    {
                        Tile t = c.At(u, v);
                        if (t.Depth != b.Storeys || t.Zone is (byte)L52Zone.Ext or (byte)L52Zone.Stair or (byte)L52Zone.Turf or (byte)L52Zone.Path
                            || taken.Contains(u + v * c.W)) ok = false;
                    }
                if (!ok) continue;
                for (int v = v0; v < v0 + d; v++)
                    for (int u = u0; u < u0 + w; u++)
                    {
                        L52Fix(c, u, v, "l52-hvac-body", top + 2, top + 2);
                        L52Fix(c, u, v, "l52-hvac-top", top + 3, top + 3);
                        taken.Add(u + v * c.W);
                    }
                for (int v = v0 - 1; v <= v0 + d; v++)
                    for (int u = u0 - 1; u <= u0 + w; u++) taken.Add(u + v * c.W);
                units--;
            }
            // Vents, here and there
            for (int k = 0; k < 2 + (b.U1 - b.U0) * (b.V1 - b.V0) / 600; k++)
            {
                int u = rng.Range(b.U0 + 2, b.U1 - 2), v = rng.Range(b.V0 + 2, b.V1 - 2);
                Tile t = c.At(u, v);
                if (t.Depth != b.Storeys || t.Zone is (byte)L52Zone.Ext or (byte)L52Zone.Stair or (byte)L52Zone.Turf || taken.Contains(u + v * c.W)) continue;
                if (b.Index == 1 && (u < b.U0 + 6 || u > b.U1 - 6) && (v < b.V0 + 6 || v > b.V1 - 6)) continue;
                L52Fix(c, u, v, "l52-vent", top + 2, top + 2);
                taken.Add(u + v * c.W);
            }
        }
    }

    /// <summary>
    /// The clock tower over a corner of the quad (Marshall David's always, about one other quad in three; none on a quad too
    /// tall for it under the sky's lid): a shaft of the quad's façade, a clock on each side, a belfry of four piers, a cap
    /// and a finial.
    /// </summary>
    private void L52LayTower(L52Campus c)
    {
        if (c.Buildings.Count == 0) return;
        L52Building q = c.Buildings[0];
        int top = q.Storeys * L52Storey;
        ulong h = Hashing.Hash(seed, c.Head.X0, c.Head.Z0, SaltL52Detail + 3);
        if (top + 12 > 36 || c.Head.Kind != L52CampusKind.MarshallDavid && Hashing.Unit(h) > 0.35) return;
        int corner = (int)(h >> 8 & 3);
        int tu0 = (corner & 1) == 0 ? q.U0 : q.U1 - 4, tv0 = (corner & 2) == 0 ? q.V0 : q.V1 - 4;
        string facade = "l52-facade-" + L52Facades[q.Facade], trim = "l52-band-" + L52Trims[q.Trim];
        int shaft0 = top + 1, clock0 = top + 3, belfry0 = top + 7, cap = top + 9;
        for (int v = tv0; v < tv0 + 5; v++)
            for (int u = tu0; u < tu0 + 5; u++)
            {
                bool rim = u == tu0 || u == tu0 + 4 || v == tv0 || v == tv0 + 4;
                bool pier = (u == tu0 || u == tu0 + 4) && (v == tv0 || v == tv0 + 4);
                if (rim)
                {
                    L52Fix(c, u, v, facade, shaft0, belfry0 - 2);
                    L52Fix(c, u, v, trim, belfry0 - 1, belfry0 - 1);
                    if (pier) L52Fix(c, u, v, facade, belfry0, belfry0 + 1);
                }
                L52Fix(c, u, v, rim ? "l52-coping" : "l52-roof", cap, cap);
                if (!rim) L52Fix(c, u, v, "l52-roof", top + 1, top + 1);
            }
        // The finial: a short mast with a ball
        L52Fix(c, tu0 + 2, tv0 + 2, "l52-flagpole-pole-north", cap + 1, cap + 1);
        // The clocks: three by three, centred on each face, hung on the tile in front of it
        foreach (ArchPier face in L52Ways)
        {
            var (fu, fv) = L52Step(face);
            int cu = tu0 + 2 + fu * 3, cv = tv0 + 2 + fv * 3;
            var (lu, lv) = L52Right(cu, cv, face, -1);
            for (int k = 0; k < 3; k++)
                for (int row = 0; row < 3; row++)
                {
                    var (pu, pv) = L52Right(lu, lv, face, k);
                    if (!c.InGrid(pu, pv)) continue;
                    L52Fix(c, pu, pv, $"l52-sign-clock{row * 3 + k}-{L52Side(face)}", clock0 + 2 - row, clock0 + 2 - row);
                }
        }
    }

    // ================= Outdoors =================

    /// <summary>A fountain in the middle of a courtyard laid out as lawns (not a court): a stone rim round water, a bowl and jet in the middle, paving round it.</summary>
    private void L52LayFountain(L52Campus c)
    {
        if (c.Buildings.Count == 0) return;
        L52Building q = c.Buildings[0];
        int u0 = int.MaxValue, v0 = int.MaxValue, u1 = int.MinValue, v1 = int.MinValue;
        for (int v = q.V0; v <= q.V1; v++)
            for (int u = q.U0; u <= q.U1; u++)
            {
                byte z = c.At(u, v).Zone;
                if (c.At(u, v).Depth != 0 || z is not ((byte)L52Zone.Turf or (byte)L52Zone.Court)) continue;
                if (z == (byte)L52Zone.Court) return; // a court instead
                u0 = Math.Min(u0, u); v0 = Math.Min(v0, v); u1 = Math.Max(u1, u); v1 = Math.Max(v1, v);
            }
        if (u1 - u0 < 20 || v1 - v0 < 20) return;
        int mu = (u0 + u1) / 2, mv = (v0 + v1) / 2;
        for (int dv = -5; dv <= 5; dv++)
            for (int du = -5; du <= 5; du++)
            {
                ref Tile t = ref c.At(mu + du, mv + dv);
                int r = Math.Max(Math.Abs(du), Math.Abs(dv));
                t.Variant = 0;
                t.Zone = (byte)L52Zone.Path;
                t.Floor = FloorKind.L52Paving;
                if (r >= 4) continue;
                t.Kind = TileKind.Wall; // (the rim, the water and the jet: not walked on)
                if (r == 3) L52Fix(c, mu + du, mv + dv, "l52-coping", 1, 1);
                else if (r == 0) L52Fix(c, mu + du, mv + dv, "l52-jet", 1, 1);
                else L52Fix(c, mu + du, mv + dv, "=water", 1, 1);
            }
        // Benches facing it across the paving
        foreach (ArchPier side in L52Ways)
        {
            var (du, dv) = L52Step(side);
            var (au, av) = L52Step(L52LeftOf(side));
            foreach (int k in new[] { -2, 2 })
            {
                int u = mu + du * 6 + au * k, v = mv + dv * 6 + av * k;
                if (c.InGrid(u, v) && c.At(u, v).Zone is (byte)L52Zone.Turf or (byte)L52Zone.Path && !c.HasFixture[u + v * c.W])
                    L52Put(c, u, v, Props.Bench, L52Opposite(side));
            }
        }
    }

    /// <summary>Three flagpoles on the lawn beside the path to the quad's first outside door.</summary>
    private void L52LayFlags(L52Campus c)
    {
        if (c.Buildings.Count == 0) return;
        L52Building q = c.Buildings[0];
        for (int v = q.V0; v <= q.V1; v++)
            for (int u = q.U0; u <= q.U1; u++)
            {
                Tile e = c.At(u, v);
                if (e.Zone != (byte)L52Zone.Entrance || e.Detail != 1) continue;
                var (ou, ov) = L52Step(e.Pier);
                if (!c.InGrid(u + ou, v + ov) || c.At(u + ou, v + ov).Depth != 0
                    || u + ou >= q.U0 && u + ou <= q.U1 && v + ov >= q.V0 && v + ov <= q.V1) continue; // (not into the courtyard)
                // (the run's left end as seen from outside: three doors wide, so the poles go four and more to the side)
                var (au, av) = L52Step(L52LeftOf(L52Opposite(e.Pier)));
                if (c.InGrid(u + au, v + av) && c.At(u + au, v + av).Zone == (byte)L52Zone.Entrance) continue;
                bool any = false;
                for (int k = 0; k < 3; k++)
                {
                    int pu = u + ou * 7 + au * (4 + k * 3), pv = v + ov * 7 + av * (4 + k * 3);
                    if (!c.InGrid(pu, pv)) continue;
                    Tile t = c.At(pu, pv);
                    if (t.Depth != 0 || t.Kind != TileKind.Floor || t.Zone != (byte)L52Zone.Lawn || t.Overhead != 0 || c.HasFixture[pu + pv * c.W]) continue;
                    string side = L52Side(e.Pier);
                    L52Fix(c, pu, pv, "l52-flagpole-base-" + side, 1, 1);
                    L52Fix(c, pu, pv, "l52-flagpole-pole-" + side, 2, 7);
                    L52Fix(c, pu, pv, "l52-flagpole-top-" + side, 8, 8);
                    any = true;
                }
                if (any) return;
            }
    }

    /// <summary>
    /// At each wide gap in the fence: the campus map on its board beside the path in; at the named campuses the M.E.G.'s
    /// board with the campus's name on the other side; on about one ordinary campus in six, an abandoned base's board.
    /// </summary>
    private void L52LayBoards(L52Campus c)
    {
        ulong h = Hashing.Hash(seed, c.Head.X0, c.Head.Z0, SaltL52Detail + 4);
        string name = c.Head.Kind switch
        {
            L52CampusKind.MarshallDavid => "md", L52CampusKind.JBarry => "barry", L52CampusKind.JTurner => "turner",
            _ => Hashing.Unit(h) < 0.17 ? new[] { "sunfire", "ember", "blackcross" }[(int)((h >> 16) % 3)] : null,
        };
        for (int s = 0; s < 4; s++)
        {
            ArchPier inward = L52Opposite(L52Ways[s]);
            var (iu, iv) = L52Step(inward);
            var (au, av) = L52Step(L52LeftOf(inward));
            int g = c.Head.Gap[s];
            int gu = s switch { 0 or 2 => g, 1 => c.W - 1, _ => 0 }, gv = s switch { 1 or 3 => g, 0 => 0, _ => c.D - 1 };
            // Beside the path (three wide round the gap's middle), five in from the fence: the map on the left of someone
            // walking in, facing the path; the name on the right
            for (int which = 0; which < 2; which++)
            {
                string kind = which == 0 ? "map" : name;
                if (kind == null || which == 1 && s != 0 && name is "sunfire" or "ember" or "blackcross") continue;
                int k = which == 0 ? -3 : 3;
                ArchPier facing = which == 0 ? L52LeftOf(inward) : L52LeftOf(L52Opposite(inward)); // toward the path
                // its two parts run along the path: the left one (as seen from the path) first
                int bu = gu + iu * 5 + au * k, bv = gv + iv * 5 + av * k;
                var (ru, rv) = L52Right(bu, bv, facing, 1);
                bool ok = true;
                foreach (var (pu, pv) in new[] { (bu, bv), (ru, rv) })
                    if (!c.InGrid(pu, pv) || c.At(pu, pv).Zone != (byte)L52Zone.Lawn || c.At(pu, pv).Depth != 0 || c.At(pu, pv).Overhead != 0 || c.HasFixture[pu + pv * c.W])
                        ok = false;
                if (!ok) continue;
                string side = L52Side(facing);
                L52Fix(c, bu, bv, $"l52-post-{kind}-l-lower-{side}", 1, 1);
                L52Fix(c, bu, bv, $"l52-post-{kind}-l-upper-{side}", 2, 2);
                L52Fix(c, ru, rv, $"l52-post-{kind}-r-lower-{side}", 1, 1);
                L52Fix(c, ru, rv, $"l52-post-{kind}-r-upper-{side}", 2, 2);
                c.At(bu, bv).Variant = 0;
                c.At(ru, rv).Variant = 0;
                // An abandoned base left a camp behind its board: a tent, crates, a burn barrel
                if (which == 1 && kind is "sunfire" or "ember" or "blackcross")
                    L52LayCamp(c, bu + iu * 4, bv + iv * 4, inward);
            }
        }
    }

    private static void L52LayCamp(L52Campus c, int u, int v, ArchPier facing)
    {
        bool Free(int pu, int pv) => c.InGrid(pu, pv) && c.At(pu, pv).Zone == (byte)L52Zone.Lawn && c.At(pu, pv).Depth == 0 && c.At(pu, pv).Overhead == 0
                                     && c.At(pu, pv).Variant == 0 && !c.HasFixture[pu + pv * c.W];
        for (int dv = 0; dv < 2; dv++)
            for (int du = 0; du < 2; du++)
                if (!Free(u + du, v + dv)) return;
        string[] parts = { "nw", "ne", "sw", "se" };
        for (int dv = 0; dv < 2; dv++)
            for (int du = 0; du < 2; du++) L52Put(c, u + du, v + dv, Props.CampTent, ArchPier.North, (byte)(dv * 2 + du));
        if (Free(u + 3, v)) L52Put(c, u + 3, v, Props.WreckCrate, facing);
        if (Free(u + 3, v + 1)) L52Put(c, u + 3, v + 1, Props.Pallet, facing);
        if (Free(u - 2, v + 2)) L52Put(c, u - 2, v + 2, Props.BurnBarrel, facing);
        if (Free(u + 1, v + 3)) L52Put(c, u + 1, v + 3, Props.Lantern, facing);
    }

    // ================= The gym's changing rooms; the pitch =================

    /// <summary>
    /// The changing rooms across the gym's far end: a cross wall nine in from the end wall, a passage from the end door
    /// through to the gym, a changing room either side of it with its own door into the gym (lockers on its walls, benches
    /// down the middle, the pictogram beside its door).
    /// </summary>
    private static void L52LayChanging(L52Campus c, L52Building b, int u0, int v0, int u1, int v1, bool alongX)
    {
        int x0 = alongX ? v0 + 1 : u0 + 1, x1 = alongX ? v1 - 1 : u1 - 1, mid = alongX ? (v0 + v1) / 2 : (u0 + u1) / 2;
        int wallA = (alongX ? u1 : v1) - 9, endA = (alongX ? u1 : v1) - 1;
        (int U, int V) P(int a, int x) => alongX ? (a, x) : (x, a);
        int doorL = (x0 + mid - 2) / 2, doorR = (mid + 2 + x1) / 2;
        ArchPier toGym = alongX ? ArchPier.West : ArchPier.North;
        var rooms = new L52Room[2];
        for (int k = 0; k < 2; k++)
        {
            int xa = k == 0 ? x0 : mid + 3, xb = k == 0 ? mid - 3 : x1;
            var (ru0, rv0) = P(wallA + 1, xa);
            var (ru1, rv1) = P(endA, xb);
            var (du, dv) = P(wallA, k == 0 ? doorL : doorR);
            rooms[k] = new L52Room
            {
                Id = c.Rooms.Count, Building = b.Index, U0 = Math.Min(ru0, ru1), V0 = Math.Min(rv0, rv1), U1 = Math.Max(ru0, ru1), V1 = Math.Max(rv0, rv1),
                Number = 2 + k, HasDoor = true, Kind = L52RoomKind.Changing, Floor = FloorKind.L52Lino, DoorSide = toGym, DoorU = du, DoorV = dv,
            };
            rooms[k].Area = (rooms[k].U1 - rooms[k].U0 + 1) * (rooms[k].V1 - rooms[k].V0 + 1);
            c.Rooms.Add(rooms[k]);
        }
        for (int a = wallA; a <= endA; a++)
            for (int x = x0; x <= x1; x++)
            {
                var (u, v) = P(a, x);
                ref Tile t = ref c.At(u, v);
                t.Ceiling = 0;
                bool passage = Math.Abs(x - mid) <= 1;
                if (a == wallA)
                {
                    if (passage || x == doorL || x == doorR)
                    {
                        t.Kind = TileKind.Doorway;
                        t.Zone = (byte)L52Zone.Door;
                        t.Floor = FloorKind.L52Gym;
                    }
                    else
                    {
                        t.Kind = TileKind.Wall;
                        t.Zone = (byte)L52Zone.Wall;
                    }
                    continue;
                }
                if (Math.Abs(x - mid) == 2)
                {
                    t.Kind = TileKind.Wall;
                    t.Zone = (byte)L52Zone.Wall;
                    // Lockers on the changing room's side
                    t.Under = Unders.L52Locker;
                    t.Pier = x < mid ? (alongX ? ArchPier.North : ArchPier.West) : (alongX ? ArchPier.South : ArchPier.East);
                    continue;
                }
                t.Kind = TileKind.Floor;
                if (passage)
                {
                    t.Zone = (byte)L52Zone.Corridor;
                    t.Floor = FloorKind.L52Floor;
                    c.RoomOf[u + v * c.W] = -1;
                    if (a == (wallA + endA) / 2 && x == mid) t.Ceiling = CeilingKind.LightOn;
                    continue;
                }
                L52Room r = rooms[x < mid ? 0 : 1];
                t.Zone = (byte)L52Zone.Room;
                t.Floor = FloorKind.L52Lino;
                c.RoomOf[u + v * c.W] = (short)r.Id;
            }
        // The pictograms beside the doors, on the gym's side of the cross wall
        for (int k = 0; k < 2; k++)
        {
            var (su, sv) = P(wallA - 1, (k == 0 ? doorL : doorR) + 1);
            if (c.InGrid(su, sv)) L52Sign(c, su, sv, k == 0 ? "men" : "women", toGym, 2, 2);
        }
    }

    /// <summary>
    /// A football pitch inside a running track: the track three lanes wide round the edge (red rubber, a white line down
    /// its middle), the pitch's artificial turf inside with its touch lines, halfway line and goal areas, a goal at each
    /// end; three rows of bleachers along one long side, outside the track.
    /// </summary>
    private void L52LayPitch(L52Campus c, int u0, int v0, int u1, int v1, bool alongX)
    {
        // (a along the pitch's length, x across it)
        int a0 = alongX ? u0 : v0, a1 = alongX ? u1 : v1, x0 = alongX ? v0 : u0, x1 = alongX ? v1 : u1;
        (int U, int V) P(int a, int x) => alongX ? (a, x) : (x, a);
        // Leave room for the stand on the far long side: three rows outside the track
        int xs = x1;
        x1 -= 4;
        FloorKind lineAlong = alongX ? FloorKind.L52PitchLineWE : FloorKind.L52PitchLineNS, lineAcross = alongX ? FloorKind.L52PitchLineNS : FloorKind.L52PitchLineWE;
        FloorKind laneAlong = alongX ? FloorKind.L52TrackLineWE : FloorKind.L52TrackLineNS, laneAcross = alongX ? FloorKind.L52TrackLineNS : FloorKind.L52TrackLineWE;
        int am = (a0 + a1) / 2, xm = (x0 + x1) / 2;
        for (int a = a0; a <= a1; a++)
            for (int x = x0; x <= x1; x++)
            {
                var (u, v) = P(a, x);
                if (!c.InGrid(u, v)) continue;
                ref Tile t = ref c.At(u, v);
                if (t.Depth != 0 || t.Kind != TileKind.Floor || t.Zone != (byte)L52Zone.Lawn) continue;
                t.Variant = 0;
                t.Zone = (byte)L52Zone.Court;
                int ra = Math.Min(a - a0, a1 - a), rx = Math.Min(x - x0, x1 - x), ring = Math.Min(ra, rx);
                if (ring <= 2)
                {
                    // The track: its middle lane line runs along whichever side this is
                    t.Floor = ring != 1 ? FloorKind.L52Track : rx <= ra ? laneAlong : laneAcross;
                    continue;
                }
                bool touch = rx == 4 && ra >= 4 || ra == 4 && rx >= 4, half = a == am && rx >= 4;
                bool box = ra >= 4 && ra <= 9 && Math.Abs(x - xm) <= 8 && (ra == 9 || Math.Abs(x - xm) == 8);
                t.Floor = touch ? (rx == 4 ? lineAlong : lineAcross) : half ? lineAcross : box ? (ra == 9 ? lineAcross : lineAlong) : FloorKind.L52Turf;
            }
        // The goals, on the goal lines, facing up the pitch
        foreach (bool far in new[] { false, true })
        {
            int a = far ? a1 - 4 : a0 + 4;
            ArchPier facing = alongX ? (far ? ArchPier.West : ArchPier.East) : (far ? ArchPier.North : ArchPier.South);
            var (lu, lv) = L52Right(P(a, xm).U, P(a, xm).V, facing, -1);
            string[] parts = { "l", "m", "r" };
            for (int k = 0; k < 3; k++)
            {
                var (gu, gv) = L52Right(lu, lv, facing, k);
                L52Fix(c, gu, gv, $"l52-goal-{parts[k]}-lower-{L52Side(facing)}", 1, 1);
                L52Fix(c, gu, gv, $"l52-goal-{parts[k]}-upper-{L52Side(facing)}", 2, 2);
            }
        }
        // The stand: three rows stepping up away from the track, along the middle half of the long side
        ArchPier toPitch = alongX ? ArchPier.North : ArchPier.West;
        for (int a = a0 + (a1 - a0) / 4; a <= a1 - (a1 - a0) / 4; a++)
            for (int row = 0; row < 3; row++)
            {
                var (u, v) = P(a, x1 + 2 + row);
                if (!c.InGrid(u, v) || x1 + 2 + row > xs) continue;
                ref Tile t = ref c.At(u, v);
                if (t.Depth != 0 || t.Kind != TileKind.Floor || t.Zone != (byte)L52Zone.Lawn) continue;
                t.Variant = 0;
                t.Kind = TileKind.Wall; // (not walked through: climbed)
                t.Zone = (byte)L52Zone.Court;
                t.Floor = FloorKind.L52Paving;
                if (row > 0) L52Fix(c, u, v, "l52-plinth", 1, row);
                L52Fix(c, u, v, "l52-bleacher-" + L52Side(toPitch), row + 1, row + 1);
            }
    }

    /// <summary>
    /// A lecture theatre: a long board on the front wall with the lecturer's desk before it, and behind, rows of desks on
    /// tiers rising a block every three rows deep (to five up), stairs up both side aisles. Built of fittings over the hall's
    /// floor (the tiers are slabs of its carpet), so the plan's tiles stay a plain hall underneath.
    /// </summary>
    private static void L52LayLecture(L52Campus c, L52Room room, bool alongX)
    {
        int la = alongX ? room.U1 - room.U0 + 1 : room.V1 - room.V0 + 1, ld = alongX ? room.V1 - room.V0 + 1 : room.U1 - room.U0 + 1;
        (int U, int V) P(int a, int d) => alongX ? (room.U0 + a, room.V0 + d) : (room.U0 + d, room.V0 + a);
        ArchPier back = alongX ? ArchPier.East : ArchPier.South, front = L52Opposite(back);
        string sb = L52Side(back), sf = L52Side(front);
        for (int a = 6; a < la; a++)
        {
            int h = Math.Min(5, (a - 6) / 3);
            for (int d = 0; d < ld; d++)
            {
                var (u, v) = P(a, d);
                bool aisle = d == 1 || d == ld - 2;
                if (h > 0)
                {
                    bool rise = (a - 6) % 3 == 0 && (a - 6) / 3 <= 5;
                    if (aisle && rise)
                    {
                        if (h > 1) L52Fix(c, u, v, "l52-slab-carpetgrey", 1, h - 1);
                        L52Fix(c, u, v, "=stair-" + sb, h, h);
                    }
                    else L52Fix(c, u, v, "l52-slab-carpetgrey", 1, h);
                }
                if (!aisle && d >= 3 && d <= ld - 4 && (a - 6) % 3 == 1) L52Fix(c, u, v, "l52-desk-" + sf, h + 1, h + 1);
                c.At(u, v).Variant = 0;
                c.At(u, v).Ceiling = h >= 4 ? 0 : c.At(u, v).Ceiling;
            }
        }
        // The board along the front wall, two high, and the lecturer's desk before it
        int d0 = 3, d1 = ld - 4;
        for (int d = d0; d <= d1; d++)
        {
            var (u, v) = P(0, d);
            // (its ends: left and right as seen from the seats, looking at the front)
            var (ru, rv) = L52Right(u, v, back, 1);
            var (nu, nv) = P(0, d + 1);
            bool rightIsUp = ru == nu && rv == nv;
            int k = rightIsUp ? d - d0 : d1 - d;
            string end = k == 0 ? "l" : k == d1 - d0 ? "r" : "m";
            L52Fix(c, u, v, $"l52-chalkboard-lower-{end}-{sb}", 2, 2);
            L52Fix(c, u, v, $"l52-chalkboard-upper-{end}-{sb}", 3, 3);
        }
        var (lu, lv) = P(2, ld / 2);
        L52Put(c, lu, lv, Props.Desk, back);
    }
}
