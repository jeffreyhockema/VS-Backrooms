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
        // A free tile (floor, nothing on it) at or near (u, v), searched outward ring by ring
        bool Free(L52Campus c, int u, int v, Func<Tile, bool> ok)
        {
            if (!c.InGrid(u, v)) return false;
            Tile t = c.At(u, v);
            return t.Kind == TileKind.Floor && t.Variant == 0 && !t.SupplyBox && t.Stair == 0 && ok(t);
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
        bool quadNorth = quad.V0 < md.D / 2;
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
                if (Near(md, u - 5, v + dir * 10, Outdoors, 3) is { } p)
                    Add(md, "entrance", p.U, p.V, 0, Heading(u - p.U, v - p.V), 14);
                break;
            }
        }

        // 3. The campus across its lawns: from the corner furthest from the quad, toward it
        {
            bool quadEast = quad.U0 > md.W / 2;
            int u = quadEast ? 12 : md.W - 13, v = quadNorth ? md.D - 13 : 12;
            if (Near(md, u, v, Outdoors) is { } p)
                Add(md, "campus", p.U, p.V, 0, Heading((quad.U0 + quad.U1) / 2 - p.U, (quad.V0 + quad.V1) / 2 - p.V), 8);
        }

        // 4. The courtyard: from one corner across to the other
        int cu0 = quad.U0 + 21, cv0 = quad.V0 + 21, cu1 = quad.U1 - 21, cv1 = quad.V1 - 21;
        if (Near(md, cu0 + 4, cv0 + 3, Outdoors) is { } cy)
            Add(md, "courtyard", cy.U, cy.V, 0, Heading(cu1 - cy.U, cv1 - cy.V), 6);

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
        Add(md, "roof", quad.U0 + 10, quadNorth ? quad.V1 - 10 : quad.V0 + 10, quad.Storeys * L52Storey + 1, quadNorth ? 150 : 30, -10);

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
        if (jb != null)
            foreach (L52Room room in jb.Rooms)
            {
                if (room.Kind != L52RoomKind.Warehouse) continue;
                if (Near(jb, room.U0 + 1, room.V0 + 1, t => t.Zone == (byte)L52Zone.Hall, 3) is { } p)
                    Add(jb, "barry-warehouse", p.U, p.V, 0, Heading((room.U0 + room.U1) / 2 - p.U, (room.V0 + room.V1) / 2 - p.V), -6);
                break;
            }
        return spots;
    }
}
