using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>), found in the wings nearest the middle:
    /// a lit hall down its length and a dead one; inside each kind of room, just in from its door, looking in (a reception
    /// toward its revolving door); a contaminated room's door seen from the corridor; the Hunter put down in a hall; then the
    /// links' spots (WorldLayout.Level14.Links.cs).
    /// </summary>
    public IEnumerable<Showcase.Spot> L14ShowcaseSpots(WorldGeometry geometry)
    {
        var spots = new List<Showcase.Spot>();
        double feet = geometry.FloorFor(Level14) + 1;
        int cx = L14CentreX * MacroSize + 16, cz = L14CentreZ * MacroSize + 16;
        int hcx = Hashing.FloorDiv(cx, L14Period), hcz = Hashing.FloorDiv(cz, L14Period);
        static double Heading(int dx, int dz) => (Math.Atan2(dx, -dz) * 180 / Math.PI + 360) % 360;
        static (int Dx, int Dz) StepOf(ArchPier p) => p switch
        {
            ArchPier.West => (-1, 0), ArchPier.East => (1, 0), ArchPier.North => (0, -1), _ => (0, 1),
        };

        // The halls: a lit stretch down its length from a crossing, and a stretch whose lights are dead
        // (round 4: from just short of the first stretch whose next two troffers both give light, so the shot is lit)
        double litZ = hcz * L14Period + 11.5;
        for (int gz = hcz * L14Period + 10; gz < hcz * L14Period + 50; gz++)
        {
            if (Hashing.Mod(gz, 8) != 4) continue;
            var t1 = new Tile { Kind = TileKind.Floor };
            var t2 = new Tile { Kind = TileKind.Floor };
            int gx = hcx * L14Period + 2;
            L14HallTile(ref t1, gx, gz, 2, Hashing.Mod(gz, L14Period));
            L14HallTile(ref t2, gx, gz + 8, 2, Hashing.Mod(gz + 8, L14Period));
            if (t1.Ceiling == CeilingKind.L14LightOn && t2.Ceiling == CeilingKind.L14LightOn) { litZ = gz - 2.5; break; }
        }
        spots.Add(new Showcase.Spot("hall-lit", hcx * L14Period + 3.5, feet, litZ, 180, -4));
        for (int r = 3; r < 12 && spots.Count < 2; r++)
            for (int k = -r; k <= r && spots.Count < 2; k++)
                if (L14DarkStretch(true, hcx + k, hcz + r) && L14In((hcx + k) * L14Period + 2, (hcz + r) * L14Period + 32))
                    spots.Add(new Showcase.Spot("hall-dark", (hcx + k) * L14Period + 3.5, feet, (hcz + r) * L14Period + 11.5, 180, -4));

        // The rooms, by kind (the first of each found walking out from the middle wing)
        var want = new List<L14Zone> { L14Zone.Reception, L14Zone.Ward, L14Zone.Icu, L14Zone.Maternity, L14Zone.Psych, L14Zone.Surgery,
            L14Zone.Storage, L14Zone.Office, L14Zone.Torture, L14Zone.Research };
        bool contam = false;
        for (int ring = 0; ring < 9 && (want.Count > 0 || !contam); ring++)
            for (int dz = -ring; dz <= ring; dz++)
                for (int dx = -ring; dx <= ring; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != ring) continue;
                    var plan = L14PlanOf(hcx + dx, hcz + dz);
                    var (wx, wz) = plan.World(L14WingSize / 2, L14WingSize / 2);
                    if (!L14In(wx, wz)) continue;
                    for (int b = 0; b < L14WingSize; b++)
                        for (int a = 0; a < L14WingSize; a++)
                        {
                            Tile t = plan.AtAB(a, b);
                            if (t.Kind != TileKind.Doorway) continue;
                            L14Zone z = L14ZoneOf(t);
                            var (ox, oz) = StepOf(t.Pier);
                            var (x, zz) = plan.World(a, b);
                            if (!contam && t.Detail == L14DoorContam && plan.AtAB(a + ox * 2, b + oz * 2).Kind == TileKind.Floor)
                            {
                                contam = true;
                                spots.Add(new Showcase.Spot("contaminated-door", x + ox * 2 + 0.5, feet, zz + oz * 2 + 0.5, Heading(-ox, -oz), -6));
                                continue;
                            }
                            if (!want.Contains(z) || t.Detail == L14DoorContam) continue;
                            // Just inside, looking in
                            int ia = a - ox, ib = b - oz;
                            if (!L14Plan.In(ia, ib) || plan.AtAB(ia, ib).Kind != TileKind.Floor || plan.AtAB(ia, ib).Variant != 0) continue;
                            want.Remove(z);
                            spots.Add(new Showcase.Spot(z.ToString().ToLowerInvariant(), x - ox + 0.5, feet, zz - oz + 0.5, Heading(-ox, -oz), z == L14Zone.Reception ? -8 : -14));
                        }
                }

        // Round 4: a gurney left along a hall wall (the nearest to the middle), seen from three blocks up the hall in the far lane
        bool gurney = false;
        for (int ring = 0; ring < 4 && !gurney; ring++)
            for (int k = -ring; k <= ring && !gurney; k++)
            {
                int bx = (hcx + k) * L14Period, bz = (hcz + ring) * L14Period;
                for (int gz = bz + 12; gz < bz + 54 && !gurney; gz++)
                    foreach (int u in new[] { 1, L14HallWidth })
                    {
                        int gx = bx + u;
                        if (!L14In(gx, gz) || L14WingAt(gx, gz) != null) continue;
                        var t = new Tile { Kind = TileKind.Floor };
                        L14HallTile(ref t, gx, gz, u, Hashing.Mod(gz, L14Period));
                        if (t.Variant != Props.L14Gurney || t.Stack != 0) continue;
                        double sx = bx + (u == 1 ? 3.5 : 1.5), sz = gz - 2.5;
                        spots.Add(new Showcase.Spot("gurney-hall", sx, feet, sz, Heading((int)Math.Round((gx + 0.5 - sx) * 4), (int)Math.Round((gz + 1 - sz) * 4)), -22));
                        gurney = true;
                        break;
                    }
            }
        // Round 4: a nurses' station (its counter and back unit) in an office, from three blocks in front of its counter
        bool station = false;
        for (int ring = 0; ring < 9 && !station; ring++)
            for (int dz = -ring; dz <= ring && !station; dz++)
                for (int dx = -ring; dx <= ring && !station; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != ring) continue;
                    var plan = L14PlanOf(hcx + dx, hcz + dz);
                    var (wx, wz) = plan.World(L14WingSize / 2, L14WingSize / 2);
                    if (!L14In(wx, wz)) continue;
                    for (int b = 0; b < L14WingSize && !station; b++)
                        for (int a = 0; a < L14WingSize && !station; a++)
                        {
                            Tile t = plan.AtAB(a, b);
                            if (t.Variant != Props.L14Station || t.Stack != 1) continue;
                            var (ox, oz) = StepOf(t.Pier);
                            int sa = a + ox * 3, sb = b + oz * 3;
                            if (!L14Plan.In(sa, sb) || plan.AtAB(sa, sb).Kind != TileKind.Floor || plan.AtAB(sa, sb).Variant != 0) continue;
                            var (x, zz) = plan.World(sa, sb);
                            spots.Add(new Showcase.Spot("nurses-station", x + 0.5, feet, zz + 0.5, Heading(-ox, -oz), -12));
                            station = true;
                        }
                }

        // Round 4: the surgery set (the table under its light, the monitor and drip stand at its head), seen from three blocks
        // beyond the table's foot; an ICU bed with its monitor arm, seen from three blocks out from the wall
        bool surg = false, icuBed = false;
        for (int ring = 0; ring < 9 && !(surg && icuBed); ring++)
            for (int dz = -ring; dz <= ring && !(surg && icuBed); dz++)
                for (int dx = -ring; dx <= ring && !(surg && icuBed); dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != ring) continue;
                    var plan = L14PlanOf(hcx + dx, hcz + dz);
                    var (wx, wz) = plan.World(L14WingSize / 2, L14WingSize / 2);
                    if (!L14In(wx, wz)) continue;
                    for (int b = -1; b <= L14WingSize; b++)
                        for (int a = -1; a <= L14WingSize; a++)
                        {
                            Tile t = plan.AtAB(a, b);
                            if (!surg && t.Variant == Props.L14OpTable && t.Stack == 1)
                            {
                                // the foot: the table runs from its head toward Pier; stand on past the foot
                                var (ox, oz) = StepOf(t.Pier);
                                int sa = a + ox * 2, sb = b + oz * 2;
                                if (L14Plan.In(sa, sb) && plan.AtAB(sa, sb) is { Kind: TileKind.Floor, Variant: 0 })
                                {
                                    var (x, zz) = plan.World(sa, sb);
                                    spots.Add(new Showcase.Spot("surgery-set", x + 0.5, feet, zz + 0.5, Heading(-ox, -oz), 4));
                                    surg = true;
                                }
                            }
                            if (!icuBed && t.Kind == TileKind.Wall && t.Detail == L14DMonArm)
                            {
                                var (ox, oz) = StepOf(t.Pier);
                                int sa = a + ox * 4, sb = b + oz * 4;
                                if (L14Plan.In(sa, sb) && plan.AtAB(sa, sb) is { Kind: TileKind.Floor, Variant: 0 })
                                {
                                    var (x, zz) = plan.World(sa, sb);
                                    spots.Add(new Showcase.Spot("icu-bed", x + 0.5, feet, zz + 0.5, Heading(-ox, -oz), 2));
                                    icuBed = true;
                                }
                            }
                        }
                }

        // Round 4: a lift and a directory board in hall walls, seen from the hall in front of them
        foreach (var (what, name, back, pitch) in new[] { (L14DLift, "lift", 4, 6), (L14DDirectory, "directory", 3, -2) })
        {
            bool found = false;
            for (int ring = 0; ring < 6 && !found; ring++)
                for (int dz = -ring; dz <= ring && !found; dz++)
                    for (int dx = -ring; dx <= ring && !found; dx++)
                    {
                        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != ring) continue;
                        var plan = L14PlanOf(hcx + dx, hcz + dz);
                        var (wx, wz) = plan.World(L14WingSize / 2, L14WingSize / 2);
                        if (!L14In(wx, wz)) continue;
                        for (int b = -1; b <= L14WingSize && !found; b++)
                            for (int a = -1; a <= L14WingSize && !found; a++)
                            {
                                Tile t = plan.AtAB(a, b);
                                if (t.Kind != TileKind.Wall || t.Detail != what || t.Stack != 0) continue;
                                var (ox, oz) = StepOf(t.Pier);
                                // its other half beside it along the wall
                                int ra = a + oz, rb = b + ox, la = a - oz, lb = b - ox;
                                (int A, int B)? other = L14Plan.In(ra, rb) && plan.AtAB(ra, rb).Detail == what && plan.AtAB(ra, rb).Stack == 1 ? (ra, rb)
                                    : L14Plan.In(la, lb) && plan.AtAB(la, lb).Detail == what && plan.AtAB(la, lb).Stack == 1 ? (la, lb) : null;
                                if (other is not { } o) continue;
                                var (x0, z0) = plan.World(a, b);
                                var (x1, z1) = plan.World(o.A, o.B);
                                double mx = (x0 + x1) / 2.0 + 0.5, mz = (z0 + z1) / 2.0 + 0.5;
                                spots.Add(new Showcase.Spot(name, mx + ox * back, feet, mz + oz * back, Heading(-ox, -oz), pitch));
                                found = true;
                            }
                    }
        }

        // The Hunter, put down calm in front of the camera in a lit hall
        spots.Add(new Showcase.Spot("hunter", hcx * L14Period + 2.5, feet, hcz * L14Period + 20.5, 180, -6, $"/backrooms l14hunter show {hcx * L14Period + 2} {hcz * L14Period + 27}"));
        spots.AddRange(L14LinkShowcaseSpots(geometry));
        return spots;
    }
}
