using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>), all worked out from the plans:
    /// Marshall David Campus (the way in through its fence, the quad's entrance, the buildings across the lawns, the
    /// courtyard, a locker corridor, a dark classroom, a stairwell, the M.E.G.'s top floor, the canteen, the view from the
    /// roof, a pedestrian bridge), the hills between the campuses, J. Turner's basketball court and J. Barry's warehouse.
    /// </summary>
    public IEnumerable<Showcase.Spot> L52ShowcaseSpots(WorldGeometry geometry)
    {
        var spots = new List<Showcase.Spot>();
        int floor = geometry.FloorFor(Level52);
        var (mi, mj) = L52MarshallDavid;
        L52Campus md = L52CampusOf(mi, mj);
        if (md == null) return spots;
        L52Head head = md.Head;
        L52Building quad = md.Buildings[0];

        static double Heading(double dx, double dz) => (Math.Atan2(dx, -dz) * 180 / Math.PI + 360) % 360;
        void Add(L52Campus c, string name, int u, int v, int rel, double heading, double pitch)
        {
            if (c == null || !c.InGrid(u, v)) return;
            spots.Add(new Showcase.Spot(name, c.Head.X0 + u + 0.5, floor + rel + 1, c.Head.Z0 + v + 0.5, Math.Round(heading), pitch));
        }
        // A free tile (floor, nothing on it, no tree's crown round it) at or near (u, v), searched outward ring by ring
        bool Free(L52Campus c, int u, int v, Func<Tile, bool> ok)
        {
            if (!c.InGrid(u, v)) return false;
            Tile t = c.At(u, v);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stair != 0 || !ok(t)) return false;
            for (int dv = -3; dv <= 3; dv++)
                for (int du = -3; du <= 3; du++)
                    if (c.InGrid(u + du, v + dv) && c.At(u + du, v + dv).Variant == Props.Tree) return false;
            return true;
        }
        (int U, int V)? Near(L52Campus c, int u, int v, Func<Tile, bool> ok, int reach = 6)
        {
            for (int r = 0; r <= reach; r++)
                for (int dv = -r; dv <= r; dv++)
                    for (int du = -r; du <= r; du++)
                        if (Math.Max(Math.Abs(du), Math.Abs(dv)) == r && Free(c, u + du, v + dv, ok)) return (u + du, v + dv);
            return null;
        }
        static bool Outdoors(Tile t) => t.Depth == 0;

        // 1. The way in: outside the fence's wide gap on the side the quad is nearest, looking in
        bool quadNorth = quad.V0 + quad.V1 < md.D, quadEast = quad.U0 + quad.U1 > md.W;
        {
            int side = quadNorth ? 0 : 2;
            int gx = head.X0 + head.Gap[side], gz = quadNorth ? head.Z0 - 14 : head.Z1 + 14;
            Tile t = TileAt(gx, gz);
            spots.Add(new Showcase.Spot("approach", gx + 0.5, floor + t.Height + 1, gz + 0.5, quadNorth ? 180 : 0, 6));
        }

        // 2. The quad's main entrance (the canopy, the surround), from the paving in front of it
        {
            int v = quadNorth ? quad.V0 : quad.V1, dir = quadNorth ? -1 : 1;
            for (int u = quad.U0 + 1; u < quad.U1; u++)
            {
                if (md.At(u, v).Zone != (byte)L52Zone.Entrance || md.At(u + 1, v).Zone != (byte)L52Zone.Entrance || md.At(u - 1, v).Zone != (byte)L52Zone.Entrance) continue;
                // (clear of the boards and flagpoles that stand on the lawns: nothing fitted within three blocks)
                bool Open(Tile t) => Outdoors(t);
                (int U, int V)? spot = null;
                for (int r = 0; r <= 10 && spot == null; r++)
                    for (int dv = -r; dv <= r && spot == null; dv++)
                        for (int du = -r; du <= r && spot == null; du++)
                        {
                            int su = u - 5 + du, sv = v + dir * 10 + dv;
                            if (Math.Max(Math.Abs(du), Math.Abs(dv)) != r || !Free(md, su, sv, Open)) continue;
                            bool clear = true;
                            for (int k = -6; k <= 6 && clear; k++)
                                for (int m = -6; m <= 6 && clear; m++)
                                    if (md.InGrid(su + k, sv + m) && md.At(su + k, sv + m).Depth == 0 && md.HasFixture[su + k + (sv + m) * md.W]) clear = false;
                            if (clear) spot = (su, sv);
                        }
                if (spot is { } p)
                    Add(md, "entrance", p.U, p.V, 0, Heading(u - p.U, v - p.V), 14);
                break;
            }
        }

        // 3. The campus across its lawns: from the open ground furthest from every building, toward the quad
        {
            // (Distance from the nearest building, by a breadth-first walk out from every building tile)
            var dist = new int[md.W * md.D];
            Array.Fill(dist, -1);
            var queue = new Queue<int>();
            for (int i = 0; i < dist.Length; i++)
                if (md.Grid[i].Depth > 0) { dist[i] = 0; queue.Enqueue(i); }
            while (queue.Count > 0)
            {
                int i = queue.Dequeue(), u = i % md.W, v = i / md.W;
                foreach (var (du, dv) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                {
                    int nu = u + du, nv = v + dv;
                    if (!md.InGrid(nu, nv) || dist[nu + nv * md.W] >= 0) continue;
                    dist[nu + nv * md.W] = dist[i] + 1;
                    queue.Enqueue(nu + nv * md.W);
                }
            }
            int best = -1, bu = 0, bv = 0;
            for (int v = 8; v < md.D - 8; v++)
                for (int u = 8; u < md.W - 8; u++)
                    if (dist[u + v * md.W] > best && Free(md, u, v, Outdoors)) { best = dist[u + v * md.W]; bu = u; bv = v; }
            if (best > 0) Add(md, "campus", bu, bv, 0, Heading((quad.U0 + quad.U1) / 2 - bu, (quad.V0 + quad.V1) / 2 - bv), 10);
        }

        // 4. The courtyard: (round 4) from the path in one corner, along the diagonal to the far corner (over the lawns' trees, not into them)
        int cu0 = quad.U0 + 21, cv0 = quad.V0 + 21, cu1 = quad.U1 - 21, cv1 = quad.V1 - 21;
        if (Near(md, cu0 + 5, cv0 + 1, Outdoors, 4) is { } cy)
            Add(md, "courtyard", cy.U, cy.V, 0, Heading(cu1 - 3 - cy.U, cv1 - cy.V), 4);

        // 4b. The courtyard's fountain, from the paving round it
        {
            int fu = (cu0 + cu1) / 2, fv = (cv0 + cv1) / 2;
            if (md.InGrid(fu, fv + 5) && md.At(fu, fv).Kind == TileKind.Wall)
                Add(md, "fountain", fu + 3, fv + 5, 0, Heading(-3, -5), -14);
        }

        // 5. A locker corridor on the ground floor: the quad's west ring, looking along it
        if (Near(md, quad.U0 + 10, quad.V0 + 26, t => t.Zone == (byte)L52Zone.Corridor, 2) is { } cor)
            Add(md, "corridor", cor.U, cor.V, 0, 180, -4);

        // 6. A classroom on the first floor up (lights off, lit by its windows), from the back toward the board
        // 7. The M.E.G.'s offices on the quad's top floor
        bool classroom = false, meg = false;
        foreach (L52Room room in md.Rooms)
        {
            if (room.Building != quad.Index || !room.HasDoor || room.Kind != L52RoomKind.Classroom) continue;
            bool alongX = room.DoorSide is ArchPier.North or ArchPier.South;
            int la = alongX ? room.U1 - room.U0 + 1 : room.V1 - room.V0 + 1, ld = alongX ? room.V1 - room.V0 + 1 : room.U1 - room.U0 + 1;
            if (la < 8 || ld < 6) continue;
            (int U, int V) At(int a, int d) => (
                alongX ? room.U0 + a : room.DoorSide == ArchPier.West ? room.U0 + d : room.U1 - d,
                !alongX ? room.V0 + a : room.DoorSide == ArchPier.North ? room.V0 + d : room.V1 - d);
            bool Clear(int storey, int a, int d)
            {
                var (u, v) = At(a, d);
                return md.RoomOf[u + v * md.W] == room.Id && L52Furnish(md, room, storey, u, v, out _, out _, out _) == 0;
            }
            if (!classroom && L52KindOn(md, room, 1) == L52RoomKind.Classroom)
            {
                // (The board's end: the one whose first tile holds a board)
                var (bu, bv) = At(0, 2);
                bool boardLow = L52Furnish(md, room, 1, bu, bv, out _, out _, out _) == Props.L52Chalkboard;
                int back = boardLow ? la - 1 : 0;
                for (int d = 1; d < ld - 1 && !classroom; d++)
                {
                    if (!Clear(1, back, d)) continue;
                    var (su, sv) = At(back, d);
                    var (tu, tv) = At(boardLow ? 0 : la - 1, ld / 2);
                    Add(md, "classroom", su, sv, L52Storey, Heading(tu - su, tv - sv), -14);
                    classroom = true;
                }
            }
            if (!meg && quad.Storeys >= 2 && L52KindOn(md, room, quad.Storeys - 1) == L52RoomKind.Meg)
            {
                for (int a = 0; a < la && !meg; a++)
                {
                    if (!Clear(quad.Storeys - 1, a, 1)) continue;
                    var (su, sv) = At(a, 1);
                    var (tu, tv) = At(la - 1 - a, ld - 1);
                    Add(md, "meg-offices", su, sv, (quad.Storeys - 1) * L52Storey, Heading(tu - su, tv - sv), -16);
                    meg = true;
                }
            }
            if (classroom && meg) break;
        }

        // 8. A stairwell: the quad's north-west one, from the ground floor's landing up the first flight (it climbs west)
        Add(md, "stairwell", quad.U0 + 13 + 6, quad.V0 + 13 + 1, 0, 270, 28);

        // 9. The canteen, from one end along the hall (the gym is the same kind of hall)
        foreach (L52Room room in md.Rooms)
        {
            if (room.Kind != L52RoomKind.Canteen) continue;
            bool alongX = room.DoorSide is ArchPier.North or ArchPier.South;
            int su = alongX ? room.U0 + 1 : (room.U0 + room.U1) / 2 + 2, sv = alongX ? (room.V0 + room.V1) / 2 + 2 : room.V0 + 1;
            if (Near(md, su, sv, t => t.Zone == (byte)L52Zone.Hall, 3) is { } p)
                Add(md, "canteen", p.U, p.V, 0, alongX ? 90 : 180, -8);
        }

        // 11. The view from the quad's roof, over the campus and out across the hills
        // (at the quad's corner nearest the rest of the campus, looking out over it from just inside the parapet)
        {
            // (looking along the roof over a stairwell's bulkhead and the air handlers, the campus beyond)
            int u = quadEast ? quad.U0 + 4 : quad.U1 - 4, v = quadNorth ? quad.V1 - 4 : quad.V0 + 4;
            int tu = quadEast ? quad.U0 + 16 : quad.U1 - 16, tv = quadNorth ? quad.V1 - 16 : quad.V0 + 16;
            Add(md, "roof", u, v, quad.Storeys * L52Storey + 1, Heading(tu - u, tv - v), -6);
        }

        // 11b. A pedestrian bridge, from the lawn beside it (Marshall David's, or the nearest campus's that has one)
        bool bridge = false;
        for (int r = 0; r <= 1 && !bridge; r++)
            for (int dj = -r; dj <= r && !bridge; dj++)
                for (int di = -r; di <= r && !bridge; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    L52Campus c = L52CampusOf(mi + di, mj + dj);
                    if (c == null) continue;
                    var mids = new List<(int U, int V, ArchPier Runs)>();
                    for (int i = 0; i < c.Grid.Length; i++)
                        if (c.Grid[i].Overhead == Overheads.L52Bridge && c.Grid[i].Stack == 2) mids.Add((i % c.W, i / c.W, c.Grid[i].Pier));
                    if (mids.Count == 0) continue;
                    var (bu, bv, runs) = mids[mids.Count / 2];
                    foreach (int sgn in new[] { 1, -1 })
                    {
                        int su = runs == ArchPier.East ? bu : bu + sgn * 11, sv = runs == ArchPier.East ? bv + sgn * 11 : bv;
                        if (Near(c, su, sv, t => Outdoors(t) && t.Overhead == 0, 2) is not { } p) continue;
                        // (Nothing in the way: no tree within three blocks of the line of sight)
                        bool clear = true;
                        for (int k = 1; k < 12 && clear; k++)
                        {
                            int lu = p.U + (bu - p.U) * k / 12, lv = p.V + (bv - p.V) * k / 12;
                            for (int dv = -3; dv <= 3 && clear; dv++)
                                for (int du = -3; du <= 3 && clear; du++)
                                    if (c.InGrid(lu + du, lv + dv) && c.At(lu + du, lv + dv).Variant == Props.Tree) clear = false;
                        }
                        if (!clear) continue;
                        Add(c, "bridge", p.U, p.V, 0, Heading(bu - p.U, bv - p.V), 18);
                        bridge = true;
                        break;
                    }
                }

        // 12. The hills: out on the road east of the campus, looking back at it
        {
            int x = head.X1 + 70, z = head.Z0 + head.Gap[1];
            Tile t = TileAt(x, z);
            spots.Add(new Showcase.Spot("hills", x + 0.5, floor + t.Height + 1, z + 0.5, 290, 2));
        }

        // 13. J. Turner's basketball court in its quad
        var (turner, barry) = L52Named;
        L52Campus jt = L52CampusOf(turner.Ci, turner.Cj);
        if (jt != null)
        {
            L52Building q = jt.Buildings[0];
            int tu0 = q.U0 + 21, tv0 = q.V0 + 21, tu1 = q.U1 - 21, tv1 = q.V1 - 21;
            if (Near(jt, tu0 + 3, tv0 + 3, Outdoors) is { } p)
                Add(jt, "turner-court", p.U, p.V, 0, Heading((tu0 + tu1) / 2 - p.U, (tv0 + tv1) / 2 - p.V), -4);
        }

        // 14. J. Barry's warehouse, from a corner
        L52Campus jb = L52CampusOf(barry.Ci, barry.Cj);
        // (Round 3's spots follow J. Barry's)
        if (jb != null)
            foreach (L52Room room in jb.Rooms)
            {
                if (room.Kind != L52RoomKind.Warehouse) continue;
                if (Near(jb, room.U0 + 1, room.V0 + 1, t => t.Zone == (byte)L52Zone.Hall, 3) is { } p)
                    Add(jb, "barry-warehouse", p.U, p.V, 0, Heading((room.U0 + room.U1) / 2 - p.U, (room.V0 + room.V1) / 2 - p.V), -6);
                break;
            }

        // Round 3's set pieces. A room seen from just inside its door, toward its far side
        bool RoomShot(L52Campus c, string name, Func<L52Room, bool> pick, int storey)
        {
            if (c == null) return false;
            foreach (L52Room room in c.Rooms)
            {
                if (room.DoorU < 0 || !pick(room)) continue;
                var (su, sv) = L52Step(room.DoorSide);
                int u = room.DoorU - su, v = room.DoorV - sv;
                if (!c.InGrid(u, v) || c.At(u, v).Kind != TileKind.Floor) continue;
                Add(c, name, u, v, storey * L52Storey, Heading((room.U0 + room.U1) / 2.0 - u, (room.V0 + room.V1) / 2.0 - v), -14);
                return true;
            }
            return false;
        }
        RoomShot(md, "front-office", r => r.GroundKind == L52RoomKind.Reception && r.Building == 1, 0);
        RoomShot(md, "restroom", r => r.Kind == L52RoomKind.RestroomMen && r.Building == 1, 0);
        RoomShot(md, "library", r => r.GroundKind == L52RoomKind.Library, 0);
        RoomShot(md, "staff-room", r => r.GroundKind == L52RoomKind.StaffRoom, 0);
        int labs = L52LabStorey(quad);
        if (labs > 0) RoomShot(md, "lab", r => r.Building == 1 && r.HasDoor && L52KindOn(md, r, labs) == L52RoomKind.Lab, labs);

        // The corridor by the quad's first stairwell: its doors, EXIT over them, the directory, the lift
        if (md.Stairs.Count > 0)
        {
            var (st, _) = md.Stairs[0];
            var (jdu, jdv) = L52Step(st.J);
            var (idu, idv) = L52Step(st.I);
            int u = st.U - 3 * idu - 2 * jdu, v = st.V - 3 * idv - 2 * jdv;
            if (md.InGrid(u, v) && md.At(u, v).Kind == TileKind.Floor) Add(md, "stair-hall", u, v, 0, Heading(jdu, jdv), -2);
        }

        // The gym: from its door side, across the court to the bleachers and along to the changing rooms
        foreach (L52Room room in md.Rooms)
        {
            if (room.Kind != L52RoomKind.Gym) continue;
            bool alongX = room.DoorSide is ArchPier.North or ArchPier.South;
            int su = alongX ? room.U0 + (room.U1 - room.U0) / 4 : room.U0 + 1, sv = alongX ? room.V0 + 1 : room.V0 + (room.V1 - room.V0) / 4;
            if (Near(md, su, sv, t => t.Zone == (byte)L52Zone.Hall, 3) is { } p)
                Add(md, "gym", p.U, p.V, 0, Heading(room.U1 - p.U, room.V1 - p.V), -6);
            break;
        }

        // (Round 4) A hoop close: in Marshall David's gym from the court, and on J. Turner's courtyard court, each from about
        // seven tiles out and two to the side, looking up at the board and rim
        void HoopShot(L52Campus c, string kind, string name)
        {
            if (c == null) return;
            foreach (var (i, list) in c.Fixtures)
                foreach (L52Fixture f in list)
                {
                    if (!f.Code.StartsWith($"l52-hoop-board-{kind}-")) continue;
                    ArchPier fp = f.Code.EndsWith("north") ? ArchPier.North : f.Code.EndsWith("south") ? ArchPier.South : f.Code.EndsWith("east") ? ArchPier.East : ArchPier.West;
                    var (fu, fv) = L52Step(fp);
                    var (ru, rv) = L52Step(L52RightOf(fp));
                    int bu = i % c.W, bv = i / c.W, u = bu + fu * 7 + ru * 2, v = bv + fv * 7 + rv * 2;
                    if (!c.InGrid(u, v)) continue;
                    Add(c, name, u, v, 0, Heading(bu - u + 0.0, bv - v + 0.0), 14);
                    return;
                }
        }
        HoopShot(md, "gym", "gym-hoop");
        // (Round 4) a trophy case in a quad's lobby (Marshall David's, or the nearest campus's), from a few tiles in front of it
        bool trophyShot = false;
        for (int r = 0; r <= 2 && !trophyShot; r++)
            for (int dj = -r; dj <= r && !trophyShot; dj++)
                for (int di = -r; di <= r && !trophyShot; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    L52Campus tc = L52CampusOf(mi + di, mj + dj);
                    if (tc == null) continue;
                    foreach (var (i, list) in tc.Fixtures)
                    {
                        L52Fixture tf = list.Find(f => f.Code.StartsWith("l52-trophy-upper-"));
                        if (tf.Code == null) continue;
                        ArchPier tp = tf.Code.EndsWith("north") ? ArchPier.North : tf.Code.EndsWith("south") ? ArchPier.South : tf.Code.EndsWith("east") ? ArchPier.East : ArchPier.West;
                        var (tdu, tdv) = L52Step(tp);
                        var (rdu, rdv) = L52Step(L52RightOf(tp));
                        foreach (var (f, k) in new[] { (3, 1), (3, -1), (3, 0), (2, 1), (2, 0) })
                        {
                            int tu = i % tc.W + tdu * f + rdu * k, tv = i / tc.W + tdv * f + rdv * k;
                            if (!tc.InGrid(tu, tv) || tc.At(tu, tv).Kind != TileKind.Floor || tc.HasFixture[tu + tv * tc.W]) continue;
                            Add(tc, "trophy-case", tu, tv, 0, Heading(i % tc.W - tu, i / tc.W - tv), -12);
                            trophyShot = true;
                            break;
                        }
                        if (trophyShot) break;
                    }
                }
        {
            var (tn, _) = L52Named;
            HoopShot(L52CampusOf(tn.Ci, tn.Cj), "yard", "court-hoop");
        }

        // A lecture theatre (Marshall David's, or the nearest campus's): from the front, by the board, up its tiers
        for (int r = 0; r <= 2; r++)
        {
            bool found = false;
            for (int dj = -r; dj <= r && !found; dj++)
                for (int di = -r; di <= r && !found; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    L52Campus c = L52CampusOf(mi + di, mj + dj);
                    if (c == null) continue;
                    foreach (L52Room room in c.Rooms)
                    {
                        if (room.Kind != L52RoomKind.Lecture) continue;
                        bool ax = room.DoorSide is ArchPier.North or ArchPier.South;
                        int su = ax ? room.U0 + 1 : room.U0 + 1, sv = ax ? room.V0 + 1 : room.V0 + 1;
                        Add(c, "lecture", su, sv, 0, Heading(room.U1 - su, room.V1 - sv), 14);
                        found = true;
                        break;
                    }
                }
            if (found) break;
        }

        // The clock tower over its corner of the quad, from the lawn out beyond that corner
        {
            ulong th = Hashing.Hash(seed, head.X0, head.Z0, SaltL52Detail + 3);
            int corner = (int)(th >> 8 & 3), sx = (corner & 1) == 0 ? -1 : 1, sz = (corner & 2) == 0 ? -1 : 1;
            int tu = ((corner & 1) == 0 ? quad.U0 : quad.U1 - 4) + 2, tv = ((corner & 2) == 0 ? quad.V0 : quad.V1 - 4) + 2;
            if (Near(md, tu + sx * 20, tv + sz * 20, Outdoors, 8) is { } p)
            {
                double dist = Math.Sqrt((tu - p.U) * (tu - p.U) + (tv - p.V) * (tv - p.V));
                Add(md, "clock-tower", p.U, p.V, 0, Heading(tu - p.U, tv - p.V), Math.Round(Math.Atan2(quad.Storeys * L52Storey + 4, dist) * 180 / Math.PI));
            }
        }

        // The way in at the gap the quad faces, from the path inside: the campus map and the M.E.G.'s board either side
        {
            int s = quadNorth ? 0 : 2, g = head.Gap[s];
            int u = g, v = quadNorth ? 11 : md.D - 12;
            if (md.InGrid(u, v)) Add(md, "gate-boards", u, v, 0, quadNorth ? 0 : 180, -6);
        }

        // Other campuses near Marshall David: a football pitch, an abandoned base's board and camp
        bool pitchShot = false, baseShot = false;
        for (int r = 0; r <= 3 && !(pitchShot && baseShot); r++)
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    L52Campus c = L52CampusOf(mi + di, mj + dj);
                    if (c == null) continue;
                    var goals = new List<(int U, int V)>();
                    foreach (var (i, list) in c.Fixtures)
                        foreach (L52Fixture f in list)
                        {
                            if (!pitchShot && f.Code.StartsWith("l52-goal-m-lower")) goals.Add((i % c.W, i / c.W));
                            if (!baseShot && f.Code.StartsWith("l52-post-") && f.Code.Contains("-l-upper-") && !f.Code.Contains("-map-")
                                && (f.Code.Contains("sunfire") || f.Code.Contains("ember") || f.Code.Contains("blackcross")))
                            {
                                ArchPier fp = f.Code.EndsWith("north") ? ArchPier.North : f.Code.EndsWith("south") ? ArchPier.South : f.Code.EndsWith("east") ? ArchPier.East : ArchPier.West;
                                var (fu, fv) = L52Step(fp);
                                int u = i % c.W + fu * 6, v = i / c.W + fv * 6;
                                if (c.InGrid(u, v))
                                {
                                    Add(c, "abandoned-base", u, v, 0, Heading(-fu, -fv), -4);
                                    baseShot = true;
                                }
                            }
                        }
                    if (!pitchShot && goals.Count >= 2)
                    {
                        var (au, av) = goals[0];
                        var (bu, bv) = goals[1];
                        // (Round 4) eight tiles out from one goal and three to the side, looking at it
                        int du = Math.Sign(au - bu), dv = Math.Sign(av - bv);
                        int pu = bu + du * 8 + (dv != 0 ? 3 : 0), pv = bv + dv * 8 + (du != 0 ? 3 : 0);
                        Add(c, "pitch", pu, pv, 0, Heading(bu - pu, bv - pv), -4);
                        pitchShot = true;
                    }
                }

        // A car park (Marshall David's, or the nearest campus's): from one end of its aisle, along it
        for (int r = 0, found = 0; r <= 2 && found == 0; r++)
            for (int dj = -r; dj <= r && found == 0; dj++)
                for (int di = -r; di <= r && found == 0; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    L52Campus c = L52CampusOf(mi + di, mj + dj);
                    if (c == null) continue;
                    int pu0 = int.MaxValue, pv0 = int.MaxValue, pu1 = -1, pv1 = -1;
                    for (int i = 0; i < c.Grid.Length; i++)
                        if (c.Grid[i].Floor is FloorKind.L52Asphalt or FloorKind.L52AsphaltLine)
                        {
                            pu0 = Math.Min(pu0, i % c.W); pv0 = Math.Min(pv0, i / c.W); pu1 = Math.Max(pu1, i % c.W); pv1 = Math.Max(pv1, i / c.W);
                        }
                    if (pu1 < 0) continue;
                    Add(c, "car-park", pu0, (pv0 + pv1) / 2, 0, 90, -6);
                    found = 1;
                }

        // J. Barry's warehouse from outside: COOL MART CO. over its doors
        if (jb != null)
            foreach (var (i, list) in jb.Fixtures)
            {
                bool done = false;
                foreach (L52Fixture f in list)
                {
                    if (!f.Code.StartsWith("l52-sign-cool-m")) continue;
                    ArchPier fp = f.Code.EndsWith("north") ? ArchPier.North : f.Code.EndsWith("south") ? ArchPier.South : f.Code.EndsWith("east") ? ArchPier.East : ArchPier.West;
                    var (fu, fv) = L52Step(fp);
                    int back = 7;
                    while (back > 3 && (!jb.InGrid(i % jb.W + fu * back, i / jb.W + fv * back) || jb.At(i % jb.W + fu * back, i / jb.W + fv * back).Zone == (byte)L52Zone.Fence
                                         || jb.At(i % jb.W + fu * back, i / jb.W + fv * back).Kind != TileKind.Floor)) back--;
                    int x = jb.Head.X0 + i % jb.W + fu * back, z = jb.Head.Z0 + i / jb.W + fv * back;
                    spots.Add(new Showcase.Spot("barry-sign", x + 0.5, floor + TileAt(x, z).Height + 1, z + 0.5, Math.Round(Heading(-fu, -fv)), 22));
                    done = true;
                    break;
                }
                if (done) break;
            }

        // 15-18. The ways in and back (WorldLayout.Level52.Links.cs): the high school nearest spawn, from across its street;
        // the EMERGENCY EXIT door nearest spawn in Level 4, from the office floor; and on Marshall David, a quad's front doors
        // and a teaching block's end doors from just inside, looking out, as someone who came in by them sees them
        foreach (var s in L52NearestSchools(1))
        {
            var (fx, fz) = FacingStep(s.Facing);
            double cx = s.DoorX + (s.Facing == ArchPier.North ? 0.0 : 1.0), cz = s.DoorZ + 0.5 + fz * 11;
            spots.Add(new Showcase.Spot("way-in-school", cx, geometry.FloorFor(11) + 1, cz, Heading(-fx, -fz), 14));
        }
        foreach (var (name, under) in new[] { ("way-back-quad", Unders.L52QuadDoor) })
        {
            bool done = false;
            for (int v = 0; v < md.D && !done; v++)
                for (int u = 0; u < md.W && !done; u++)
                {
                    Tile d = md.At(u, v);
                    if (d.Under != under) continue;
                    // (The middle of the three: a door tile with door tiles either side)
                    var (au, av) = L52Step(L52LeftOf(d.Pier));
                    if (!md.InGrid(u + au, v + av) || !md.InGrid(u - au, v - av) || md.At(u + au, v + av).Under != under || md.At(u - au, v - av).Under != under) continue;
                    var (ou, ov) = L52Step(d.Pier);
                    int pu = u - ou * 5, pv = v - ov * 5;
                    if (!md.InGrid(pu, pv) || md.At(pu, pv).Kind != TileKind.Floor) continue;
                    Add(md, name, pu, pv, 0, Heading(ou, ov), 4);
                    done = true;
                }
        }
        return spots;
    }
}
