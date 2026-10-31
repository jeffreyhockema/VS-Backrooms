using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>): the rink (a long view, the star,
    /// the DJ station with its DJ), the lobby from the hall, the food court with its server, Skate Rental with the Coach, an
    /// arcade, a cinema, the Employees Lounge, an HVAC room, a bathroom, a glowing-carpet room, an emptiness and a neon hall
    /// with a Faceling in it. Each is the nearest of its kind to the region's centre, found by walking the complexes outwards
    /// ring by ring; every spot is worked out from the plans, so it holds for any seed.
    /// </summary>
    public IEnumerable<Showcase.Spot> L31ShowcaseSpots(WorldGeometry geometry)
    {
        double feet = geometry.FloorFor(Level31) + 1.05;
        const string Staff = "/backrooms l31 staff";
        var found = new Dictionary<string, Showcase.Spot>();
        int cx = Hashing.FloorDiv(L31CentreX * MacroSize + MacroSize / 2, L31Period), cz = Hashing.FloorDiv(L31CentreZ * MacroSize + MacroSize / 2, L31Period);

        // A spot at a place in a plan (moved to the nearest clear tile within the box given), looking at another place in the
        // plan (lookUp blocks above the floor); lift raises the feet (the cinema's top step)
        Showcase.Spot? Spot(L31Plan plan, int p, int q, double lp, double lq, double lookUp, int lift = 0, string setup = null,
            int p0 = -16, int q0 = -16, int p1 = L31Size + 16, int q1 = L31Size + 16)
        {
            for (int r = 0; r <= 4; r++)
                for (int dq = -r; dq <= r; dq++)
                    for (int dp = -r; dp <= r; dp++)
                    {
                        if (Math.Max(Math.Abs(dp), Math.Abs(dq)) != r) continue;
                        int sp = p + dp, sq = q + dq;
                        if (sp < p0 || sq < q0 || sp > p1 || sq > q1) continue;
                        var (x, z) = plan.World(sp, sq);
                        if (!IsArrivalSpot(TileAt(x, z)) || TileAt(x, z).Level != Level31) continue;
                        // (the place looked at, through the plan's mirroring)
                        double tx = plan.Wx * L31Period + 7 + lp + 0.5, tz = plan.Wz * L31Period + 7 + (plan.Mirror ? L31Size - 1 - lq : lq) + 0.5;
                        double ex = x + 0.5, ez = z + 0.5, dx = tx - ex, dz = tz - ez;
                        double heading = (Math.Atan2(dx, -dz) * 180 / Math.PI + 360) % 360;
                        double pitch = Math.Atan2(lookUp - (lift + 1.6), Math.Sqrt(dx * dx + dz * dz)) * 180 / Math.PI;
                        return new Showcase.Spot("x", ex, feet + lift, ez, Math.Round(heading, 1), Math.Round(pitch, 1), setup);
                    }
            return null;
        }
        void Add(string name, Showcase.Spot? spot)
        {
            if (spot is { } s && !found.ContainsKey(name)) found[name] = s with { Name = name };
        }

        for (int ring = 0; ring <= 5 && found.Count < 14; ring++)
            for (int wz = cz - ring; wz <= cz + ring; wz++)
                for (int wx = cx - ring; wx <= cx + ring; wx++)
                {
                    if (Math.Max(Math.Abs(wx - cx), Math.Abs(wz - cz)) != ring || !L31ComplexInside(wx, wz)) continue;
                    L31Plan plan = L31PlanOf(wx, wz);
                    if (plan.Kind == L31Kind.Empty)
                    {
                        // An emptiness: from near one door, across the pillars (a carpeted one is the glowing-carpet shot)
                        Add(plan.Rooms[0].Kind == L31Zone.CarpetRoom ? "glowroom" : "emptiness", Spot(plan, 60, 2, 20, 70, 1.2));
                        continue;
                    }
                    if (!plan.Tiny)
                    {
                        // The rink: along it from the west skirt; across it from a corner to the star; the DJ station from the boards
                        Add("rink", Spot(plan, 19, 60, 102, 60, 1.8));
                        Add("rink-star", Spot(plan, 19, 27, 60, 60, 6.5));
                        int south = plan.Mirror ? 26 : 94, inward = plan.Mirror ? 1 : -1, desk = south + 3 * inward;
                        Add("dj", Spot(plan, 60, desk + 12 * inward, 60, desk, 1.6, setup: Staff));
                        // The lobby through its front doors, from the hall
                        Add("lobby", Spot(plan, 60, -4, 54, 14, 1.0));
                        // A neon hall: down the hall west of the complex towards a crossing, a Faceling about
                        Add("hall", Spot(plan, -4, 34, -4, -4, 1.6, setup: "/backrooms encounter faceling ambient 0 0 10"));
                    }
                    foreach (L31Room room in plan.Rooms)
                    {
                        string name = room.Kind switch
                        {
                            L31Zone.Snack => "foodcourt", L31Zone.Rental => "rental", L31Zone.Arcade => "arcade", L31Zone.Cinema => "cinema",
                            L31Zone.Lounge => "lounge", L31Zone.Hvac => "hvac", L31Zone.Bath => "bath", L31Zone.CarpetRoom => "glowroom",
                            _ => null,
                        };
                        if (name == null || found.ContainsKey(name)) continue;
                        // From the corner beside the door, across to the far corner. The door is on the front band's +Q side,
                        // the back rooms' -Q side and the side rooms' inner side
                        bool front = room.Q1 <= 19, back = room.Q0 >= 101, west = room.P1 <= 11;
                        int mp = (room.P0 + room.P1) / 2;
                        string setup = room.Kind is L31Zone.Rental or L31Zone.Snack ? Staff : null;
                        var (a0, b0, a1, b1) = (room.P0, room.Q0, room.P1, room.Q1);
                        Showcase.Spot? spot = room.Kind == L31Zone.Cinema
                            // (from the end of the top row, 11 from the TV's wall and three steps up, to the TV)
                            ? Spot(plan, a0, b1 - 11, mp, b1, 2.5, lift: 3, p0: a0, q0: b1 - 11, p1: a0 + 1, q1: b1 - 11)
                            : front ? Spot(plan, a0 + 1, b1, a1, b0, 1.2, setup: setup, p0: a0, q0: b0, p1: a1, q1: b1)
                            : back ? Spot(plan, a0 + 1, b0, a1, b1, 1.2, setup: setup, p0: a0, q0: b0, p1: a1, q1: b1)
                            : west ? Spot(plan, a1, b0 + 1, a0, b1, 1.2, setup: setup, p0: a0, q0: b0, p1: a1, q1: b1)
                            : Spot(plan, a0, b0 + 1, a1, b1, 1.2, setup: setup, p0: a0, q0: b0, p1: a1, q1: b1);
                        Add(name, spot);
                    }
                }

        foreach (string name in new[] { "rink", "rink-star", "dj", "lobby", "foodcourt", "rental", "arcade", "cinema", "lounge", "hvac", "bath", "glowroom", "emptiness", "hall" })
            if (found.TryGetValue(name, out var s)) yield return s;
    }
}
