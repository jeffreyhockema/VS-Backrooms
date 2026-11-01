using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>): a server room's aisle between
    /// its banks, a wrecked bank, a rack still lit, a rack aisle room under its trays, a terminal room, the one whole
    /// terminal's BOOT screen, cables over the floor, a passage to its working tube and one in the dark, the nearest White
    /// Void (its black doors, a broken window, a Smiler lost in the light) and Pitch-Black Hallway (along a lane, its
    /// window), and a Misglitch in a server room. All found from the halls round the region's centre, nearest first. And the
    /// ways in and out: the door marked SERVER ROOM nearest spawn (in Level 4), a door back in a server room and in a hallway.
    /// </summary>
    public IEnumerable<Showcase.Spot> L120ShowcaseSpots(WorldGeometry geometry)
    {
        double y = geometry.FloorFor(Level120) + 1;
        var (chx, chz) = L120HallOf(L120CentreX * MacroSize + MacroSize / 2, L120CentreZ * MacroSize + MacroSize / 2);
        // The cluster halls round the centre, ring by ring
        var rings = new List<List<(int Hx, int Hz)>>();
        for (int r = 0; r <= 3; r++)
        {
            var ring = new List<(int, int)>();
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) == r && L120KindOf(chx + dx, chz + dz) == L120HallKind.Cluster && L120HallInside(chx + dx, chz + dz))
                        ring.Add((chx + dx, chz + dz));
            rings.Add(ring);
        }

        static bool Stand(Tile t) => t.Kind == TileKind.Floor && t.Variant == 0 && !t.SupplyBox && t.Stack == 0;
        static bool Rack(Tile t) => t.Variant == L120Rack && t.Detail != L120RackGutted;
        static bool Lit(Tile t) => t.Variant == L120Rack && t.Detail is >= L120RackLedA and <= L120RackBoth;
        static bool Wreck(Tile t) => t.Variant is L120Wreck or Props.MachineParts or Props.ScrapMetal || t.Variant == L120Rack && t.Detail == L120RackGutted;
        static bool Terminal(Tile t) => t.Variant is L120Terminal or L120Chair;
        static bool Spill(Tile t) => t.Variant == L120Spill;
        static bool InVoid(Tile t) => t.Kind == TileKind.Floor && t.Variant == 0 && t.Zone == (byte)L120Zone.Void;

        Showcase.Spot? Spot(string name, (int X, int Z, int Dx, int Dz)? at, double pitch, string setup = null) =>
            at is { } a ? new Showcase.Spot(name, a.X + 0.5, y, a.Z + 0.5, L120Heading(a.Dx, a.Dz), pitch, setup) : null;

        var spots = new List<Showcase.Spot?>();
        // A server room: down the aisle between two banks of racks
        var servers = L120Best(rings, Stand, (t, k, s) => Math.Abs(s) == 1 && Rack(t) ? 1 : 0, 8, 6, zone: L120Zone.Room, line: 6);
        spots.Add(Spot("server-aisle", servers, -4));
        // A wrecked bank: racks gutted, toppled, torn open, parts and scrap over the floor
        spots.Add(Spot("wrecked-bank", L120Best(rings, Stand, (t, k, s) => Wreck(t) ? 1 : Spill(t) ? 0.5 : 0, 6, 8), -14));
        // A rack still lit in the dark
        spots.Add(Spot("lit-rack", L120Best(rings, Stand, (t, k, s) => Lit(t) ? (k <= 3 ? 3 : 1) : 0, 5, 1), -4));
        // A rack aisle room: along a cold aisle under its tray
        spots.Add(Spot("cold-aisle", L120Best(rings, t => Stand(t) && t.Overhead is L120TrayX or L120TrayZ,
            (t, k, s) => Math.Abs(s) == 2 && Rack(t) ? 1 : 0, 9, 8, line: 8), -2));
        // A terminal room: rows of dead and smashed screens with their chairs
        spots.Add(Spot("terminal-room", L120Best(rings, Stand, (t, k, s) => Terminal(t) ? 1 : 0, 7, 10, zone: L120Zone.Terminals), -10));
        // The cluster's one whole terminal, its green BOOT prompt
        spots.Add(Spot("boot-screen", L120BootView(rings), -20));
        // Cables pulled out over the floor
        spots.Add(Spot("spilled-cables", L120Best(rings, Stand, (t, k, s) => Spill(t) ? 1 : 0, 5, 5), -28));
        // A passage, to the crossing that keeps a working tube; and one in the dark
        spots.Add(Spot("passage-tube", L120PassageView(chx, chz, 10), 0));
        spots.Add(Spot("passage-dark", L120PassageView(chx + 1, chz, 3), 0));

        // The nearest White Void: across a room to its black doors, a broken window, a Smiler lost in the light
        if (L120NearestPocket(chx, chz, L120HallKind.Void, 12) is { } v)
        {
            var hall = new List<List<(int, int)>> { new() { v } };
            var doors = L120Best(hall, InVoid, (t, k, s) => t.Variant == L120VoidDoor ? 3 - 0.2 * Math.Abs(s) : 0, 13, 13, line: 4);
            spots.Add(Spot("void-doors", doors, 0));
            spots.Add(Spot("void-window", L120Best(hall, InVoid, (t, k, s) => t.Variant == L120Window && s == 0 && k >= 4 ? 3 : 0, 7, 1, line: 3), -4));
            if (doors is { } d)
                spots.Add(Spot("void-smiler", doors, 0, $"/backrooms l120 smiler {d.X + d.Dx * 5} {d.Z + d.Dz * 5}"));
        }
        // The nearest Pitch-Black Hallway: along a lane from the arrival, and to the window at its end
        if (L120NearestPocket(chx, chz, L120HallKind.Hallway, 12) is { } hw)
        {
            var (ax, az) = L120PocketArrival(hw.Hx, hw.Hz);
            spots.Add(Spot("hallway-lane", (ax, az, 1, 0), 0));
            var hall = new List<List<(int, int)>> { new() { hw } };
            spots.Add(Spot("hallway-window", L120Best(hall, t => t.Kind == TileKind.Floor && t.Variant != L120Window && t.Zone == (byte)L120Zone.Hallway,
                (t, k, s) => t.Variant == L120Window && k == 5 ? 3 : 0, 5, 1, line: 4), -4));
        }
        // A Misglitch standing in a server room's aisle, five blocks off
        if (servers is { } m)
            spots.Add(Spot("misglitch", servers, -2, $"/backrooms l120 misglitch {m.X + m.Dx * 5} {m.Z + m.Dz * 5}"));

        // The ways in and out (WorldLayout.Level120.Links.cs): the door marked SERVER ROOM nearest spawn, in Level 4's offices
        // (across the corridor from it, its placard beside it); the nearest door back in a server room, and in a hallway
        foreach (var d in L120ServerDoorsNear(spawnMacroX, spawnMacroZ, 1200, 1))
        {
            // (From the far side of the corridor, a few blocks along it, so the door and its placard are both in view)
            int sx = d.OutX - d.X, sz = d.OutZ - d.Z;
            Tile two = TileAt(d.X + 2 * sx, d.Z + 2 * sz);
            int back = two.Kind == TileKind.Floor && IsWalkable(two) ? 2 : 1;
            int bx = d.X + back * sx, bz = d.Z + back * sz;
            foreach (int along in new[] { 4, -4, 3, -3, 2, -2, 0 })
            {
                int cx = bx + sz * along, cz = bz + sx * along;
                if (along != 0 && !(TileAt(cx, cz).Kind == TileKind.Floor && IsWalkable(TileAt(cx, cz)))) continue;
                double heading = (Math.Atan2(d.X + 0.5 - (cx + 0.5), -(d.Z + 0.5 - (cz + 0.5))) * 180 / Math.PI + 360) % 360;
                spots.Add(new Showcase.Spot("serverroom-door", cx + 0.5, geometry.FloorFor(4) + 1, cz + 0.5, heading, -10));
                break;
            }
        }
        foreach (var ring in rings)
        {
            var exit = ring.SelectMany(h => L120ExitDoorsOf(h.Hx, h.Hz)).Cast<(int X, int Z, int FrontX, int FrontZ)?>().FirstOrDefault();
            if (exit is not { } e) continue;
            spots.Add(Spot("door-back", L120StandBack(e), -8));
            break;
        }
        if (L120NearestPocket(chx, chz, L120HallKind.Hallway, 12) is { } hd && L120ExitDoorsOf(hd.Hx, hd.Hz) is { Count: > 0 } hdoors)
            spots.Add(Spot("hallway-door", L120StandBack(hdoors[0]), -8));

        foreach (Showcase.Spot? s in spots)
            if (s is { } spot) yield return spot;
    }

    /// <summary>A few blocks back from a door (as far as the floor goes, up to three), looking at it.</summary>
    private (int X, int Z, int Dx, int Dz) L120StandBack((int X, int Z, int FrontX, int FrontZ) door)
    {
        int sx = door.FrontX - door.X, sz = door.FrontZ - door.Z, back = 1;
        while (back < 3 && IsWalkable(TileAt(door.X + (back + 1) * sx, door.Z + (back + 1) * sz)) && TileAt(door.X + (back + 1) * sx, door.Z + (back + 1) * sz).Kind == TileKind.Floor) back++;
        return (door.X + back * sx, door.Z + back * sz, -sx, -sz);
    }

    /// <summary>A compass heading (0 north, 90 east) looking along a step.</summary>
    private static double L120Heading(int dx, int dz) => (Math.Atan2(dx, -dz) * 180 / Math.PI + 360) % 360;

    /// <summary>
    /// The best place in the halls of the first ring that has a good one (nearest the centre) to stand and look one of the
    /// four ways: <paramref name="stand"/> holds where you stand, the <paramref name="line"/> tiles straight ahead can be
    /// walked (no wall in your face), and <paramref name="score"/> is summed over a cone <paramref name="reach"/> deep
    /// (k ahead, s to the side); a ring is good once its best scores <paramref name="min"/>.
    /// </summary>
    private (int X, int Z, int Dx, int Dz)? L120Best(List<List<(int Hx, int Hz)>> rings, Func<Tile, bool> stand, Func<Tile, int, int, double> score,
        int reach, double min, L120Zone? zone = null, int line = 2)
    {
        (int, int, int, int)? best = null;
        double bestScore = 0;
        foreach (var ring in rings)
        {
            foreach (var (hx, hz) in ring)
            {
                L120Plan plan = L120PlanOf(hx, hz);
                Tile At(int p, int q) => p < -1 || q < -1 || p > L120HallSize || q > L120HallSize ? default : plan.At(p, q);
                for (int q = 0; q < L120HallSize; q++)
                    for (int p = 0; p < L120HallSize; p++)
                    {
                        Tile here = plan.At(p, q);
                        if (!stand(here) || zone is { } zn && here.Zone != (byte)zn) continue;
                        foreach (var (dx, dz) in Steps)
                        {
                            bool open = true;
                            for (int k = 1; k <= line && open; k++) open = IsWalkable(At(p + dx * k, q + dz * k));
                            if (!open) continue;
                            double sum = 0;
                            for (int k = 1; k <= reach; k++)
                                for (int s = -(k + 1) / 2; s <= (k + 1) / 2; s++)
                                {
                                    Tile t = At(p + dx * k - dz * s, q + dz * k + dx * s);
                                    if (t.Kind != TileKind.Wall) sum += score(t, k, s);
                                }
                            if (sum > bestScore)
                            {
                                var (x, z) = plan.World(p, q);
                                bestScore = sum;
                                best = (x, z, dx, dz);
                            }
                        }
                    }
            }
            if (best != null && bestScore >= min) return best;
        }
        return best;
    }

    /// <summary>Two blocks back from the nearest whole terminal, looking at its screen.</summary>
    private (int X, int Z, int Dx, int Dz)? L120BootView(List<List<(int Hx, int Hz)>> rings)
    {
        foreach (var ring in rings)
            foreach (var (hx, hz) in ring)
                foreach (var b in L120PlanOf(hx, hz).Boots)
                {
                    int dx = b.FrontX - b.X, dz = b.FrontZ - b.Z;
                    Tile two = TileAt(b.X + 2 * dx, b.Z + 2 * dz);
                    return IsWalkable(two) && two.Kind == TileKind.Floor ? (b.X + 2 * dx, b.Z + 2 * dz, -dx, -dz) : (b.FrontX, b.FrontZ, -dx, -dz);
                }
        return null;
    }

    /// <summary>
    /// Down a passage along x towards a crossing: the first crossing at or east of hall <paramref name="hx"/> that keeps its
    /// working tube (for <paramref name="back"/> 10 or more, standing that far west of it), or any crossing (looking on from it).
    /// </summary>
    private (int X, int Z, int Dx, int Dz)? L120PassageView(int hx, int hz, int back)
    {
        for (int i = 0; i < 12; i++)
        {
            int cx = (hx + i / 2) * L120Period + 3, cz = (hz + i % 2) * L120Period + 3;
            bool kept = Hashing.Mod(hx + i / 2, 2) == 0 && Hashing.Mod(hz + i % 2, 2) == 0;
            if (back >= 10 && !kept) continue;
            if (LevelAt(MacroOf(cx - back), MacroOf(cz)) != Level120 || LevelAt(MacroOf(cx), MacroOf(cz)) != Level120) continue;
            return back >= 10 ? (cx - back, cz, 1, 0) : (cx, cz, 1, 0);
        }
        return null;
    }
}
