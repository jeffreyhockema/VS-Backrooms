using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>): landside round the centre line
    /// (a carousel, the claim hall, check-in, the Travel Agency's booth 0 with its Planner, security, a Lost and Found office),
    /// then airside a concourse and its travelators, the nearest lit superblock of each kind (a pier's corridor, a holdroom,
    /// the runway window, a gate's sign from the corridor, the cabin; duty free, the food court, the lounge, the Meeting Place,
    /// a service maze), a blackout with something in it and the Absolute Limit at the rim. All from the layout, so any seed.
    /// </summary>
    public IEnumerable<Showcase.Spot> L36ShowcaseSpots(WorldGeometry geometry)
    {
        var spots = new List<Showcase.Spot>();
        double y = geometry.FloorFor(Level36) + 1;
        int wx = L36WallX, lz = L36LineZ;
        void Add(string name, double x, double z, double heading, double pitch = 0, string setup = null) =>
            spots.Add(new Showcase.Spot(name, x, y, z, (heading % 360 + 360) % 360, pitch, setup));

        // Landside (wx + u: blocks east of the baggage wall; lz + line: south of the centre line). The first spot is out of
        // sight of booth 0 and within 72 blocks of it, and waits there, so the Travel Planner is put down (the wanderers'
        // tick is ten seconds) before the booth's shot
        const string dwell = "/backrooms where;/backrooms where;/backrooms where;/backrooms where;/backrooms where";
        Add("carousel", wx + 20.5, lz + 76.5, 270, -18, dwell);
        Add("claim-hall", wx + 21.5, lz + 52.5, 0);
        // A blackout: the nearest dark north-south concourse stretch, something in it, looking north to its failing end
        // (the encounter is put down where the player faces on arriving: the claim hall's heading, north, as the shot's)
        bool dark = false;
        for (int r = 2; r <= 6 && !dark; r++)
            for (int sz = -r; sz <= r && !dark; sz++)
            {
                if (!L36DarkStretch(r, L36Stretch(r, sz, true, SaltL36Hall))) continue;
                int x = L36AirX + r * L36Period, z = lz + sz * L36Period + L36Hall;
                if (LevelAt(MacroOf(x), MacroOf(z + 120)) != Level36) continue;
                Add("blackout", x + 7.5, z + 60.5, 0, 0, "/backrooms encounter smiler glimpse");
                dark = true;
            }

        Add("checkin", wx + 35.5, lz + 35.5, 180, 4);
        Add("travel-agency", wx + 27.5, lz + 16, 90, 12);
        Add("security", wx + 49.5, lz + 8.5, 90, -4);
        Add("lost-and-found", wx + 9.5, lz + 6 * 32 + 16, 270, -6);
        // A concourse: the long view east along the first west-east one, the travelators down the first north-south one
        Add("concourse", L36AirX + 20.5, lz + 7.5, 90);
        Add("travelators", L36AirX + 7.5, lz + 18.5, 180, -4);

        // The nearest lit superblock of each kind
        L36Plan Nearest(L36Kind kind)
        {
            for (int r = 0; r <= 5; r++)
                for (int sx = 0; sx <= r; sx++)
                    for (int sz = -r; sz <= r; sz++)
                    {
                        if (Math.Max(sx, Math.Abs(sz)) != r || L36KindOf(sx, sz) != kind) continue;
                        L36Plan p = L36PlanOf(sx, sz);
                        if (p.Dark || LevelAt(MacroOf(p.X0 + 120), MacroOf(p.Z0 + 120)) != Level36) continue;
                        return p;
                    }
            return null;
        }
        // A spot in a plan's own coordinates, looking along a plan direction (dp along P, dq along Q)
        void AddIn(L36Plan plan, string name, double p, double q, double dp, double dq, double pitch = 0, string setup = null)
        {
            var (x0, z0) = plan.World(0, 0);
            var (xp, zp) = plan.World(1, 0);
            var (xq, zq) = plan.World(0, 1);
            double x = x0 + (xp - x0) * p + (xq - x0) * q, z = z0 + (zp - z0) * p + (zq - z0) * q;
            double vx = (xp - x0) * dp + (xq - x0) * dq, vz = (zp - z0) * dp + (zq - z0) * dq;
            Add(name, x + 0.5, z + 0.5, Math.Atan2(vx, -vz) * 180 / Math.PI, pitch, setup);
        }

        if (Nearest(L36Kind.Pier) is { } pier)
        {
            AddIn(pier, "pier", 2, 117, 1, 0.03, 2);
            // A gate on the north side: its holdroom from the back, the runway window, its sign from the corridor, its cabin
            L36Gate gate = pier.Gates.Count > 4 ? pier.Gates[4] : pier.Gates[0];
            int fx = gate.Facing switch { ArchPier.East => 1, ArchPier.West => -1, _ => 0 }, fz = gate.Facing switch { ArchPier.South => 1, ArchPier.North => -1, _ => 0 };
            double back = Math.Atan2(-fx, fz) * 180 / Math.PI;
            Add("holdroom", gate.DoorX + fx * 24 + 0.5, gate.DoorZ + fz * 24 + 0.5, back, 2);
            Add("runway", gate.DoorX + fx * 3 + 0.5, gate.DoorZ + fz * 3 + 0.5, back, 4);
            Add("gate-sign", gate.DoorX + fx * 35 + 0.5, gate.DoorZ + fz * 35 + 0.5, back, 24);
            // The cabin: from the back of the aisle toward the nose (plan west)
            var (x0, z0) = pier.World(0, 0);
            var (xp, zp) = pier.World(1, 0);
            Add("cabin", gate.AisleX + (xp - x0) * 8 + 0.5, gate.AisleZ + (zp - z0) * 8 + 0.5, Math.Atan2(-(xp - x0), zp - z0) * 180 / Math.PI, -6);
        }
        if (Nearest(L36Kind.DutyFree) is { } duty) AddIn(duty, "duty-free", 4, 112, 1, 0.12, 2);
        if (Nearest(L36Kind.FoodCourt) is { } food) AddIn(food, "food-court", 70, 70, 1, 1, -4);
        if (Nearest(L36Kind.Lounge) is { } lounge) AddIn(lounge, "lounge", 78, 119, 1, -0.2, -6);
        if (Nearest(L36Kind.Meeting) is { } meeting)
        {
            // First from behind the Travel Agency's kiosk (out of its sight, so its Planner is put down while the tour waits)
            AddIn(meeting, "meeting-kiosk", 120, 160, -0.15, -1, 6, dwell);
            AddIn(meeting, "meeting-place", 119.5, 102, 0, 1, 6);
        }
        if (Nearest(L36Kind.Service) is { } service) AddIn(service, "service", 2, 66, 1, 0);

        // The Absolute Limit: east along the centre line's concourse to the rim, a cell and a half short of it
        for (int x = L36AirX; x < L36AirX + 2 * L36Radius * MacroSize; x += 8)
            if (LevelAt(MacroOf(x), MacroOf(lz + 8)) != Level36)
            {
                Add("limit", x - 1.5 * MacroSize + 0.5, lz + 7.5, 90);
                break;
            }
        return spots;
    }
}
