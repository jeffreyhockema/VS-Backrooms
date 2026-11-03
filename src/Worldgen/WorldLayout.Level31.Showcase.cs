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

        for (int ring = 0; ring <= 5 && found.Count < 28; ring++)
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
                        // The rink: along the boards from their west end; up at the star from a corner of the oval; the DJ
                        // station from the boards
                        Add("rink", Spot(plan, 27, 60, 100, 60, 1.2));
                        Add("rink-star", Spot(plan, 40, 44, 60, 60, 7.0));
                        int south = plan.Mirror ? 26 : 94, inward = plan.Mirror ? 1 : -1, desk = south + 3 * inward;
                        Add("dj", Spot(plan, 60, desk + 9 * inward, 60, desk, 2.2, setup: Staff));
                        // (round 4) The booth close up from the boards' edge (decks, mixer, the speaker stacks); a gate in the
                        // barrier from the boards (the north straight's west gap)
                        Add("djbooth", Spot(plan, 63, desk + 3 * inward, 60, desk, 0.9, setup: Staff, p0: 62, q0: Math.Min(desk + 2 * inward, desk + 3 * inward),
                            p1: 65, q1: Math.Max(desk + 2 * inward, desk + 3 * inward)));
                        int edgeN = plan.Mirror ? 88 : 32;
                        Add("gate", Spot(plan, 44, edgeN - 4 * inward, 41, edgeN, 0.6, p0: 43, q0: Math.Min(edgeN - 3 * inward, edgeN - 5 * inward),
                            p1: 46, q1: Math.Max(edgeN - 3 * inward, edgeN - 5 * inward)));
                        // The lobby through its front doors, from the hall
                        Add("lobby", Spot(plan, 60, -4, 54, 14, 1.0));
                        // A neon hall: down the hall west of the complex towards a crossing, a Faceling about
                        Add("hall", Spot(plan, -4, 34, -4, -4, 1.6, setup: "/backrooms encounter faceling ambient 0 0 10"));
                        // (round 3) The rink's name over the lobby's front doors, from along the hall; the snack window on the
                        // rink's north skirt; the service corridor's door signs; the lobby's trophy cases and jukebox
                        Add("lobby-front", Spot(plan, 50, -4, 60, -1, 4.6, p0: 40, q0: -6, p1: 80, q1: -2));
                        int north = plan.Mirror ? 94 : 26, toRink = plan.Mirror ? -1 : 1;
                        Add("snackwindow", Spot(plan, 66, north + 5 * toRink, 71.5, north, 2.6));
                        Add("corridor", Spot(plan, 18, 22, 90, 22, 2.4, p0: 13, q0: 21, p1: 30, q1: 24));
                        Add("trophies", Spot(plan, 53, 7, 46, 4, 1.4, p0: 47, q0: 1, p1: 73, q1: 18));
                    }
                    foreach (L31Room room in plan.Rooms)
                    {
                        // (round 3) The Coach close up behind his counter, his whiteboard and the cubbies; the arcade's prize corner
                        if (room.Kind == L31Zone.Rental && room.Q1 <= 19)
                            Add("coach", Spot(plan, (room.P0 + room.P1) / 2 - 2, 9, (room.P0 + room.P1) / 2, 2, 1.9, setup: Staff,
                                p0: room.P0, q0: 6, p1: room.P1, q1: 10));
                        if (room.Kind == L31Zone.Rental && room.Q1 <= 19)
                            Add("skates", Spot(plan, (room.P0 + room.P1) / 2 + 5, 5, (room.P0 + room.P1) / 2 + 5, 3, 0.8,
                                p0: room.P0, q0: 4, p1: room.P1, q1: 5));
                        if (room.Kind == L31Zone.Store && !found.ContainsKey("backarcade"))
                        {
                            // (round 4) The back arcade's covered machines, from the aisle beside the first of them
                            for (int q = room.Q0; q <= room.Q1 && !found.ContainsKey("backarcade"); q++)
                                for (int p = room.P0; p <= room.P1; p++)
                                {
                                    var (cx2, cz2) = plan.World(p, q);
                                    if (TileAt(cx2, cz2).Variant != L31Props.Covered) continue;
                                    Add("backarcade", Spot(plan, p, q + 1, p + 2, q, 1.4, p0: room.P0, q0: room.Q0, p1: room.P1, q1: room.Q1));
                                    break;
                                }
                        }
                        if (room.Kind == L31Zone.Arcade && room.Q1 <= 19)
                            Add("pinball", Spot(plan, room.P0 + 6, room.Q0 + 2, room.P0 + 9, room.Q0, 1.3,
                                p0: room.P0, q0: room.Q0 + 1, p1: room.P1, q1: room.Q0 + 2));
                        if (room.Kind == L31Zone.Arcade && room.Q1 <= 19)
                            Add("prizes", Spot(plan, room.P1 - 7, room.Q0 + 8, room.P1, room.Q0 + 3, 2.0, p0: room.P0, q0: room.Q0, p1: room.P1, q1: room.Q1));
                        if (room.Kind == L31Zone.Bath && room.DoorP > -9)
                        {
                            // (from just inside its door, to one side, across to its far wall's stalls: the restroom is walled in
                            // round its door)
                            int ox = room.DoorSide == ArchPier.West ? -1 : room.DoorSide == ArchPier.East ? 1 : 0;
                            int oz = room.DoorSide == ArchPier.North ? -1 : room.DoorSide == ArchPier.South ? 1 : 0;
                            int ip = room.DoorP - ox + (oz != 0 ? 3 : 0), iq = room.DoorQ - oz + (ox != 0 ? 3 : 0);
                            Add(room.Q0 >= 101 ? "restroom" : "bath", Spot(plan, ip, iq, room.DoorP - 9 * ox - (oz != 0 ? 2 : 0), room.DoorQ - 9 * oz - (ox != 0 ? 2 : 0), 1.3,
                                p0: room.P0, q0: room.Q0, p1: room.P1, q1: room.Q1));
                        }
                        if (room.Kind == L31Zone.Hvac)
                        {
                            // (from its door across to the air handlers on its far wall)
                            int ox = room.DoorSide == ArchPier.West ? -1 : room.DoorSide == ArchPier.East ? 1 : 0;
                            int oz = room.DoorSide == ArchPier.North ? -1 : room.DoorSide == ArchPier.South ? 1 : 0;
                            int ip = room.DoorP - ox + (oz != 0 ? 4 : 0), iq = room.DoorQ - oz + (ox != 0 ? 4 : 0);
                            Add("hvac", Spot(plan, ip, iq, (room.P0 + room.P1) / 2.0, (room.Q0 + room.Q1) / 2.0 - 0 * oz + (oz == 0 ? 0 : 0), 2.0,
                                p0: room.P0, q0: room.Q0, p1: room.P1, q1: room.Q1));
                        }
                        if ((room.Kind == L31Zone.Rental || room.Kind == L31Zone.Snack) && room.Q1 <= 19)
                            Add(room.Kind == L31Zone.Rental ? "doorsign-rental" : "doorsign-snack",
                                Spot(plan, room.DoorP + 5, 23, room.DoorP + 1, 20, 3.6, p0: 13, q0: 21, p1: 107, q1: 24));
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
                            // (from the end of the top row, 11 from the TV's wall and three steps up, to the TV; the room is walled
                            // in round its middle, so the end of the row is the first clear tile along it)
                            ? L31RowEnd(plan, a0, a1, b1 - 11) is int e ? Spot(plan, e, b1 - 11, mp, b1, 2.5, lift: 3, p0: e, q0: b1 - 11, p1: e, q1: b1 - 11) : null
                            : front ? Spot(plan, a0 + 1, b1, a1, b0, 1.2, setup: setup, p0: a0, q0: b0, p1: a1, q1: b1)
                            : back ? Spot(plan, a0 + 1, b0, a1, b1, 1.2, setup: setup, p0: a0, q0: b0, p1: a1, q1: b1)
                            : west ? Spot(plan, a1, b0 + 1, a0, b1, 1.2, setup: setup, p0: a0, q0: b0, p1: a1, q1: b1)
                            : Spot(plan, a0, b0 + 1, a1, b1, 1.2, setup: setup, p0: a0, q0: b0, p1: a1, q1: b1);
                        Add(name, spot);
                    }
                }

        int? L31RowEnd(L31Plan plan, int a0, int a1, int q)
        {
            for (int p = a0; p <= a1; p++)
            {
                var (x, z) = plan.World(p, q);
                if (IsArrivalSpot(TileAt(x, z))) return p;
            }
            return null;
        }

        // The ways in and out (WorldLayout.Level31.Links.cs): a lobby's wooden door and a revolving door, from inside the lobby
        for (int ring = 0; ring <= 8 && !(found.ContainsKey("lobbydoor") && found.ContainsKey("revolving")); ring++)
            for (int wz = cz - ring; wz <= cz + ring; wz++)
                for (int wx = cx - ring; wx <= cx + ring; wx++)
                {
                    if (Math.Max(Math.Abs(wx - cx), Math.Abs(wz - cz)) != ring || !L31ComplexInside(wx, wz)) continue;
                    L31Plan plan = L31PlanOf(wx, wz);
                    if (plan.Kind != L31Kind.Rinks) continue;
                    Add("lobbydoor", Spot(plan, L31LobbyDoorP - 2, L31LobbyDoorQ - 6, L31LobbyDoorP, L31LobbyDoorQ, 1.4, p0: 46, q0: 0, p1: 74, q1: 19));
                    if (L31HasRevolving(wx, wz))
                        Add("revolving", Spot(plan, L31RevolvingP + 1, L31RevolvingQ + 8, L31RevolvingP, L31RevolvingQ, 2.8, p0: 46, q0: 0, p1: 74, q1: 19));
                }

        foreach (string name in new[] { "rink", "rink-star", "dj", "djbooth", "gate", "skates", "pinball", "backarcade", "lobby", "lobby-front", "foodcourt", "rental", "coach", "arcade", "prizes", "cinema",
            "lounge", "hvac", "bath", "restroom", "doorsign-rental", "doorsign-snack", "snackwindow", "corridor", "trophies", "glowroom", "emptiness", "hall", "lobbydoor", "revolving" })
            if (found.TryGetValue(name, out var s)) yield return s;

        // The wooden doors into the rink in its hosts, the nearest to spawn in each: from four steps in front of it
        var (sx, sz) = FindSpawn();
        foreach (int host in new[] { 2, 3, 6 })
        {
            if (L31NearestHostDoor(host, MacroOf(sx), MacroOf(sz)) is not { } door) continue;
            var (fx, fz) = FacingStep(door.Facing);
            Showcase.Spot? shot = null;
            for (int back = 4; back >= 1 && shot == null; back--)
            {
                int ex = door.X + fx * back, ez = door.Z + fz * back;
                // (all the way from the door: a tunnel may turn a step or two in front of it)
                bool clear = true;
                for (int k = 1; k <= back; k++) clear &= TileAt(door.X + fx * k, door.Z + fz * k).Kind == TileKind.Floor;
                if (!clear) continue;
                double heading = (Math.Atan2(-fx, fz) * 180 / Math.PI + 360) % 360;
                double pitch = Math.Atan2(1.2 - 1.6, back) * 180 / Math.PI;
                shot = new Showcase.Spot($"door-l{host}", ex + 0.5, geometry.FloorFor(host) + 1.05, ez + 0.5, Math.Round(heading, 1), Math.Round(pitch, 1));
            }
            if (shot is { } sh) yield return sh;
        }
    }
}
