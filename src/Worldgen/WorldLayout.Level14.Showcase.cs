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
        spots.Add(new Showcase.Spot("hall-lit", hcx * L14Period + 3.5, feet, hcz * L14Period + 11.5, 180, -4));
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

        // The Hunter, put down calm in front of the camera in a lit hall
        spots.Add(new Showcase.Spot("hunter", hcx * L14Period + 2.5, feet, hcz * L14Period + 20.5, 180, -6, "/backrooms l14hunter show"));
        spots.AddRange(L14LinkShowcaseSpots(geometry));
        return spots;
    }
}
