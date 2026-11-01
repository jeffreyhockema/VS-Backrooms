using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>), all worked out from the layout:
    /// a long view through the forest by day, the trail and one of the Order's way-stones, a stream, the glade from the walk
    /// in (the manor and the stones in the same place), the trilithons through the roof, the great hall and the east room
    /// inside, the Order's keepers, a snake, the Great Adder, the elk, the night sky over the glade (the moon's far side),
    /// the Black Shucks at night, a walker on the trail, a dead tree's hollow, a green giant (the way to Level 23), and Level
    /// 10's ancient dead tree (the way in).
    /// </summary>
    public IEnumerable<Showcase.Spot> L47ShowcaseSpots(WorldGeometry geometry)
    {
        int fy = geometry.FloorFor(Level47);
        var spots = new List<Showcase.Spot>();
        int mx = L47MidX, mz = L47MidZ;
        const string Day = "/time set lunch", Night = "/time set midnight";
        double Feet(int x, int z) => fy + Math.Max(0, L47Ground(x, z)) + 1;
        double HeadingTo(double fx, double fz, double tx, double tz) => (Math.Atan2(tx - fx, -(tz - fz)) * 180 / Math.PI + 360) % 360;

        // A long view through the forest: the longest clear run of ground from a few places 150 blocks out
        {
            (int X, int Z, double H, int Run) best = (0, 0, 0, -1);
            for (int k = 0; k < 10; k++)
            {
                double a = k * Math.PI / 5 + 0.3;
                if (!L47OpenNear(mx + (int)Math.Round(Math.Cos(a) * 150), mz + (int)Math.Round(Math.Sin(a) * 150), 10, out int x, out int z)) continue;
                for (int d = 0; d < 8; d++)
                {
                    int run = L47OpenRun(x, z, d * 45, 48);
                    if (run > best.Run) best = (x, z, d * 45, run);
                }
            }
            if (best.Run >= 0) spots.Add(new Showcase.Spot("forest-long", best.X + 0.5, Feet(best.X, best.Z), best.Z + 0.5, best.H, 3, Day));
        }
        // The trail: standing on it a turn and a half out, looking along it
        {
            double phi = 7.5;
            var (x, z) = L47TrailPoint(phi);
            var (nx, nz) = L47TrailPoint(phi + 0.12);
            int ix = (int)Math.Floor(x), iz = (int)Math.Floor(z);
            spots.Add(new Showcase.Spot("trail", ix + 0.5, Feet(ix, iz), iz + 0.5, HeadingTo(x, z, nx, nz), -4, Day));
            // A walker of the Order on it, come round the bend
            spots.Add(new Showcase.Spot("trail-walker", ix + 0.5, Feet(ix, iz), iz + 0.5, HeadingTo(x, z, nx, nz), -4, Day + $";/backrooms l47 showwalker {(int)HeadingTo(x, z, nx, nz)}"));
        }
        // One of the Order's way-stones, from the trail beside it
        {
            var (wx, wz) = L47MarkerAt(6);
            L47TrailDistance(wx + 0.5, wz + 0.5, out double phi);
            var (tx, tz) = L47TrailPoint(phi - 0.03);
            int ix = (int)Math.Floor(tx), iz = (int)Math.Floor(tz);
            spots.Add(new Showcase.Spot("waystone", ix + 0.5, Feet(ix, iz), iz + 0.5, HeadingTo(tx, tz, wx + 0.5, wz + 0.5), -18, Day));
        }
        // A stream: the nearest stretch of water to a place out in the forest, from its bank
        {
            (int X, int Z, int Wx, int Wz) found = (0, 0, 0, 0);
            bool any = false;
            for (int r = 80; r < 400 && !any; r += 6)
                for (int k = 0; k < 24 && !any; k++)
                {
                    double a = k * Math.PI / 12;
                    int wx = mx + (int)Math.Round(Math.Cos(a) * r), wz = mz + (int)Math.Round(Math.Sin(a) * r);
                    if (!L47InWater(wx, wz) || L47Stream(wx, wz) > 0.006) continue;
                    // (A bank three to six blocks off, open)
                    for (int d = 3; d <= 6 && !any; d++)
                        foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                        {
                            int bx = wx + dx * d, bz = wz + dz * d;
                            Tile t = TileAt(bx, bz);
                            if (t.Kind == TileKind.Floor && t.Zone == L47Forest && !L47InWater(bx, bz)) { found = (bx, bz, wx, wz); any = true; break; }
                        }
                }
            if (any) spots.Add(new Showcase.Spot("stream", found.X + 0.5, Feet(found.X, found.Z), found.Z + 0.5, HeadingTo(found.X, found.Z, found.Wx, found.Wz), -12, Day));
        }
        // The glade from the walk in: the manor, and the stones round it and through it
        spots.Add(new Showcase.Spot("glade", mx + 0.5, fy + 2, mz + 38.5, 0, 6, Day));
        // The trilithons standing through the roof, from the meadow to the south-east
        spots.Add(new Showcase.Spot("stones-through-roof", mx + 16.5, fy + 2, mz + 13.5, HeadingTo(mx + 16.5, mz + 13.5, mx, mz), 14, Day));
        // Inside: the great hall (its long table, lanterns, banners, a trilithon through it), the east room (the shelves), the entrance hall (the Altar Stone)
        spots.Add(new Showcase.Spot("great-hall", mx - 4.5, fy + 2, mz + 5.5, 290, -6, Day));
        spots.Add(new Showcase.Spot("east-room", mx + 5.5, fy + 2, mz + 2.5, 95, -6, Day));
        spots.Add(new Showcase.Spot("entrance-hall", mx + 0.5, fy + 2, mz + 6.5, 0, -10, Day));
        // The Order's keepers before the door
        spots.Add(new Showcase.Spot("keepers", mx + 0.5, fy + 2, mz + 24.5, 0, -4, Day + ";/backrooms l47 showkeepers"));
        // Out in the forest by day: a snake in the litter; the Great Adder rearing; an elk
        if (L47OpenNear(mx + 120, mz - 60, 12, out int sx, out int sz))
        {
            spots.Add(new Showcase.Spot("snake", sx + 0.5, Feet(sx, sz), sz + 0.5, 90, -30, Day + ";/backrooms l47 showsnake 90"));
            spots.Add(new Showcase.Spot("great-adder", sx + 0.5, Feet(sx, sz), sz + 0.5, 90, 4, Day + ";/backrooms l47 showadder 90"));
            spots.Add(new Showcase.Spot("elk", sx + 0.5, Feet(sx, sz), sz + 0.5, 90, 0, Day + ";/backrooms l47 showelk 90"));
        }
        // The night: the fog gone, the moon's far side over the glade; the Black Shucks in the forest
        spots.Add(new Showcase.Spot("night-moon", mx + 0.5, fy + 2, mz + 30.5, 173, 45, Night));
        spots.Add(new Showcase.Spot("night-glade", mx + 0.5, fy + 2, mz + 40.5, 0, 8, Night));
        spots.Add(new Showcase.Spot("night-aurora", mx + 0.5, fy + 2, mz - 30.5, 0, 22, Night + ";/backrooms l47 aurora"));
        if (L47OpenNear(mx - 130, mz + 70, 12, out int nx2, out int nz2))
            spots.Add(new Showcase.Spot("night-shucks", nx2 + 0.5, Feet(nx2, nz2), nz2 + 0.5, 0, -2, Night + ";/backrooms l47 showpack 0"));
        // A dead tree's hollow (the nearest that leads out), from in front of its mouth
        foreach (var h in L47HollowTrees())
        {
            if (!h.Leads) continue;
            if (L47HollowFront(h.X, h.Z, 5) is { } f) { spots.Add(new Showcase.Spot("dead-hollow", f.X + 0.5, Feet(f.X, f.Z), f.Z + 0.5, HeadingTo(f.X, f.Z, h.X, h.Z), 2, Day)); break; }
        }
        // A green giant, the way to Level 23, from in front of its mouth
        var giants = L47GreenGiants();
        if (giants.Count > 0 && L47HollowFront(giants[0].X, giants[0].Z, 12) is { } g)
            spots.Add(new Showcase.Spot("green-giant", g.X + 0.5, Feet(g.X, g.Z), g.Z + 0.5, HeadingTo(g.X, g.Z, giants[0].X, giants[0].Z), 12, Day));
        // Level 10's ancient dead tree, the way in, nearest the spawn
        var trees10 = L47NearestTrees10();
        if (trees10.Count > 0)
        {
            var (tx, tz) = trees10[0];
            L47Tree10 t = L47Tree10Near(tx, tz);
            int fx = tx + (int)Math.Round(Math.Cos(t.MouthA) * 9), fz = tz + (int)Math.Round(Math.Sin(t.MouthA) * 9);
            spots.Add(new Showcase.Spot("way-in-level10", fx + 0.5, geometry.FloorFor(10) + 1, fz + 0.5, HeadingTo(fx, fz, tx, tz), 10, Day));
        }
        return spots;
    }

    /// <summary>The nearest tile to a point with open forest floor all round it (within a reach), if any.</summary>
    private bool L47OpenNear(int x, int z, int reach, out int ox, out int oz)
    {
        for (int r = 0; r <= reach; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    Tile t = TileAt(x + dx, z + dz);
                    if (t.Level == Level47 && (t.Detail & L47OpenGround) != 0) { ox = x + dx; oz = z + dz; return true; }
                }
        ox = oz = 0;
        return false;
    }

    /// <summary>How far the ground runs open along a heading (degrees, 0 north) from a tile, up to a limit.</summary>
    private int L47OpenRun(int x, int z, double heading, int limit)
    {
        double a = heading * Math.PI / 180, dx = Math.Sin(a), dz = -Math.Cos(a);
        for (int d = 1; d <= limit; d++)
        {
            Tile t = TileAt((int)Math.Floor(x + 0.5 + dx * d), (int)Math.Floor(z + 0.5 + dz * d));
            if (t.Kind != TileKind.Floor) return d - 1;
        }
        return limit;
    }

    /// <summary>A tile of open floor out in front of a hollow tree's mouth (at about a distance), if any.</summary>
    private (int X, int Z)? L47HollowFront(int tx, int tz, int distance)
    {
        // (Look round the tree for the side its hollow opens on: a run of open floor straight out from the middle)
        for (int k = 0; k < 16; k++)
        {
            double a = k * Math.PI / 8;
            bool through = false;
            for (int d = 1; d <= 7 && !through; d++)
            {
                Tile t = TileAt(tx + (int)Math.Round(Math.Cos(a) * d), tz + (int)Math.Round(Math.Sin(a) * d));
                if (t.Kind == TileKind.Wall) break;
                if (t.Under == 0 && d >= 3) through = true;
            }
            if (!through) continue;
            for (int d = distance; d <= distance + 4; d++)
            {
                int x = tx + (int)Math.Round(Math.Cos(a) * d), z = tz + (int)Math.Round(Math.Sin(a) * d);
                Tile t = TileAt(x, z);
                if (t.Kind == TileKind.Floor && t.Under == 0 && t.Zone is L47Forest or L47TrailZone) return (x, z);
            }
        }
        return null;
    }
}
