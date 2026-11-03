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
                // (A run of 20 to 32 open blocks: trees at its end, not a blank of fog over a stream)
                for (int d = 0; d < 8; d++)
                {
                    int run = L47OpenRun(x, z, d * 45, 48);
                    if (run >= 20 && run <= 32 && (best.Run < 0 || Math.Abs(run - 26) < Math.Abs(best.Run - 26))) best = (x, z, d * 45, run);
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
            // The Great Adder come up the trail; at night, the Black Shucks on it
            spots.Add(new Showcase.Spot("great-adder", ix + 0.5, Feet(ix, iz), iz + 0.5, HeadingTo(x, z, nx, nz), 6, Day + $";/backrooms l47 showadder {(int)HeadingTo(x, z, nx, nz)}"));
            spots.Add(new Showcase.Spot("night-shucks", ix + 0.5, Feet(ix, iz), iz + 0.5, HeadingTo(x, z, nx, nz), -6, Night + $";/backrooms l47 showpack {(int)HeadingTo(x, z, nx, nz)}"));
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
            var feet = new byte[3];
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
                            if (t.Kind != TileKind.Floor || t.Zone != L47Forest || L47InWater(bx, bz)) continue;
                            // (Nothing standing at the feet, nor under them: the camera stood on a log's end, then on a root)
                            L47Wood(bx, bz, L47Ground(bx, bz), feet);
                            if (feet[0] != 0 || feet[1] != 0 || feet[2] != 0) continue;
                            found = (bx, bz, wx, wz); any = true; break;
                        }
                }
            if (any)
            {
                // (Round 4: look along the brook, turned a little toward it, so it runs away into the fog between its banks)
                double gx = L47Stream(found.Wx + 1, found.Wz) - L47Stream(found.Wx - 1, found.Wz), gz = L47Stream(found.Wx, found.Wz + 1) - L47Stream(found.Wx, found.Wz - 1);
                double tx = -gz, tz = gx, tl = Math.Sqrt(tx * tx + tz * tz);
                double h = tl > 1e-9 ? HeadingTo(0, 0, tx, tz) : HeadingTo(found.X, found.Z, found.Wx, found.Wz);
                double toWater = HeadingTo(found.X, found.Z, found.Wx, found.Wz);
                double diff = ((toWater - h + 540) % 360) - 180;
                if (Math.Abs(diff) > 90) { h = (h + 180) % 360; diff = ((toWater - h + 540) % 360) - 180; }
                spots.Add(new Showcase.Spot("stream", found.X + 0.5, Feet(found.X, found.Z), found.Z + 0.5, (h + Math.Sign(diff) * 20 + 360) % 360, -10, Day));
            }
        }
        // The glade from the walk in: the manor, and the stones round it and through it
        spots.Add(new Showcase.Spot("glade", mx + 0.5, fy + 2, mz + 38.5, 0, 6, Day));
        // The trilithons standing through the roof, from the meadow to the south-east
        spots.Add(new Showcase.Spot("stones-through-roof", mx + 16.5, fy + 2, mz + 13.5, HeadingTo(mx + 16.5, mz + 13.5, mx, mz), 14, Day));
        // Inside: the great hall (its trestle table and benches, the hearth, tapestries, banners, a trilithon through it), the east room (the library), the entrance hall (the Altar Stone)
        // (Round 4: the great hall down its length to the hearth wall; the hearth and its fire close to; a tapestry over the
        // table; the door from the walk, open, in its frame; the library)
        spots.Add(new Showcase.Spot("great-hall", mx - 4.5, fy + 2, mz + 0.5, 270, -5, Day));
        spots.Add(new Showcase.Spot("hearth", mx - 6.5, fy + 2, mz - 2.5, HeadingTo(mx - 6.5, mz - 2.5, mx - 10.5, mz - 0.0), -4, Day));
        // (the south wall's: the north wall's is behind a trilithon from anywhere in the hall)
        spots.Add(new Showcase.Spot("tapestry", mx - 5.0, fy + 2, mz + 2.5, HeadingTo(mx - 5.0, mz + 2.5, mx - 7.0, mz + 6.5), 8, Day));
        spots.Add(new Showcase.Spot("manor-door", mx + 0.5, fy + 2, mz + 11.5, 0, 6, Day));
        spots.Add(new Showcase.Spot("east-room", mx + 5.5, fy + 2, mz + 2.5, 95, -6, Day));
        spots.Add(new Showcase.Spot("entrance-hall", mx + 0.5, fy + 2, mz + 6.5, 0, -10, Day));
        // The Great Adder in the open, on the glade's meadow (the Order keeps it, the lore says, "to some extent")
        spots.Add(new Showcase.Spot("great-adder-glade", mx - 32.5, fy + 2, mz + 22.5, 90, 4, Day + ";/backrooms l47 showadder 90"));
        // The Order's keepers before the door
        spots.Add(new Showcase.Spot("keepers", mx + 0.5, fy + 2, mz + 24.5, 0, -4, Day + ";/backrooms l47 showkeepers"));
        // Out in the forest by day: a snake in the litter; the Great Adder rearing; an elk
        if (L47OpenNear(mx + 120, mz - 60, 12, out int sx, out int sz))
        {
            spots.Add(new Showcase.Spot("snake", sx + 0.5, Feet(sx, sz), sz + 0.5, 90, -30, Day + ";/backrooms l47 showsnake 90"));
            spots.Add(new Showcase.Spot("elk", sx + 0.5, Feet(sx, sz), sz + 0.5, 90, 0, Day + ";/backrooms l47 showelk 90"));
        }
        // The night: the fog gone, the moon's far side over the glade; the Black Shucks in the forest
        spots.Add(new Showcase.Spot("night-moon", mx + 0.5, fy + 2, mz + 30.5, 173, 45, Night));
        spots.Add(new Showcase.Spot("night-glade", mx + 0.5, fy + 2, mz + 40.5, 0, 8, Night));
        spots.Add(new Showcase.Spot("night-aurora", mx + 0.5, fy + 2, mz - 30.5, 0, 22, Night + ";/backrooms l47 aurora"));
        // (Round 4) A fallen giant's root plate, from out in front of it; an old oak with moss on its north side, brackets
        // and mushrooms at its foot
        {
            (double D, double X, double Z, double Ax, double Az) best = (1e9, 0, 0, 0, 0);
            int li = Hashing.FloorDiv(mx + 140, 23), lj = Hashing.FloorDiv(mz, 23);
            for (int j = lj - 8; j <= lj + 8; j++)
                for (int i = li - 8; i <= li + 8; i++)
                {
                    L47Log l = L47LogCached(i, j);
                    if (!l.Exists || l.Plate <= 0) continue;
                    double len = Math.Sqrt((l.Bx - l.Ax) * (l.Bx - l.Ax) + (l.Bz - l.Az) * (l.Bz - l.Az));
                    double ux = (l.Bx - l.Ax) / len, uz = (l.Bz - l.Az) / len;
                    // (Out in front of the plate, on the side away from the trunk, a little to one side to see both, with
                    // nothing standing between: round 4's first shot looked at a dead tree)
                    foreach (var (back, side) in new[] { (7.0, 3.0), (7.0, -3.0), (6.0, 5.0), (6.0, -5.0), (9.0, 0.0) })
                    {
                        double fx = l.Ax - ux * back - uz * side, fz = l.Az - uz * back + ux * side;
                        int ix = (int)Math.Floor(fx), iz = (int)Math.Floor(fz);
                        Tile t = TileAt(ix, iz);
                        if (t.Kind != TileKind.Floor || t.Zone != L47Forest) continue;
                        double len2 = Math.Sqrt((l.Ax - fx) * (l.Ax - fx) + (l.Az - fz) * (l.Az - fz));
                        bool clear = true;
                        for (double k = 1; k < len2 - 2.5 && clear; k += 0.5)
                            clear = TileAt((int)Math.Floor(fx + (l.Ax - fx) * k / len2), (int)Math.Floor(fz + (l.Az - fz) * k / len2)).Kind == TileKind.Floor;
                        if (!clear) continue;
                        double d = Math.Abs(l.Ax - (mx + 140)) + Math.Abs(l.Az - mz);
                        if (d < best.D) best = (d, ix, iz, l.Ax, l.Az);
                        break;
                    }
                }
            if (best.D < 1e9)
                spots.Add(new Showcase.Spot("root-plate", best.X + 0.5, Feet((int)best.X, (int)best.Z), best.Z + 0.5, HeadingTo(best.X + 0.5, best.Z + 0.5, best.Ax, best.Az), 8, Day));
        }
        {
            (double D, int X, int Z, double Tx, double Tz) best = (1e9, 0, 0, 0, 0);
            int ti = Hashing.FloorDiv(mx - 120, L47Pitch), tj = Hashing.FloorDiv(mz + 60, L47Pitch);
            for (int j = tj - 6; j <= tj + 6; j++)
                for (int i = ti - 6; i <= ti + 6; i++)
                {
                    L47Tree t = L47TreeAt(i, j);
                    if (!t.Exists || t.Dead || t.Conifer || t.R < 2.2) continue;
                    // (From the north, five or six blocks out past the buttresses: the moss is on the north side)
                    int fx = (int)Math.Floor(t.X), fz = (int)Math.Floor(t.Z - t.R - 5.5);
                    Tile tile = TileAt(fx, fz);
                    if (tile.Kind != TileKind.Floor || tile.Zone != L47Forest) continue;
                    double d = Math.Abs(t.X - (mx - 120)) + Math.Abs(t.Z - (mz + 60));
                    if (d < best.D) best = (d, fx, fz, t.X, t.Z);
                }
            if (best.D < 1e9)
                spots.Add(new Showcase.Spot("mossy-oak", best.X + 0.5, Feet(best.X, best.Z), best.Z + 0.5, HeadingTo(best.X + 0.5, best.Z + 0.5, best.Tx, best.Tz), 12, Day));
        }
        // (Round 4) A wanderer's camp, left with its fire alight: the nearest to a place out east of the glade, from the south
        {
            int cx = MacroOf(mx + 200), cz = MacroOf(mz);
            bool done = false;
            for (int r = 0; r <= 8 && !done; r++)
                for (int dz = -r; dz <= r && !done; dz++)
                    for (int dx = -r; dx <= r && !done; dx++)
                    {
                        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || !L47CampAt(cx + dx, cz + dz, out int ax, out int az) || !L47CampFits(ax, az)) continue;
                        // (From along its row, east of it: the log, the fire and the bedroll in a line, nothing between)
                        spots.Add(new Showcase.Spot("camp", ax + 4.5, Feet(ax + 4, az), az + 0.5, 270, -24, Day));
                        done = true;
                    }
        }
        // A dead tree's hollow (the nearest that leads out), from in front of its mouth
        foreach (var h in L47HollowTrees())
        {
            if (!h.Leads) continue;
            if (L47HollowFront(h.X, h.Z, 5) is { } f) { spots.Add(new Showcase.Spot("dead-hollow", f.X + 0.5, Feet(f.X, f.Z), f.Z + 0.5, HeadingTo(f.X, f.Z, h.X, h.Z), 2, Day)); break; }
        }
        // A green giant, the way to Level 23, from in front of its mouth
        var giants = L47GreenGiants();
        if (giants.Count > 0 && L47HollowFront(giants[0].X, giants[0].Z, 17) is { } g)
            spots.Add(new Showcase.Spot("green-giant", g.X + 0.5, Feet(g.X, g.Z), g.Z + 0.5, HeadingTo(g.X, g.Z, giants[0].X, giants[0].Z), 18, Day));
        // Level 10's ancient dead tree, the way in, nearest the spawn
        var trees10 = L47NearestTrees10();
        if (trees10.Count > 0)
        {
            var (tx, tz) = trees10[0];
            L47Tree10 t = L47Tree10Near(tx, tz);
            int fx = tx + (int)Math.Round(Math.Cos(t.MouthA) * 9), fz = tz + (int)Math.Round(Math.Sin(t.MouthA) * 9);
            spots.Add(new Showcase.Spot("way-in-level10", fx + 0.5, geometry.FloorFor(10) + 1, fz + 0.5, HeadingTo(fx, fz, tx, tz), 10, Day));
        }
        // A last day view: the clock jumps from midnight back to noon here, and the light takes a moment to follow (the
        // shot may be dark); the random arrivals after it are by day
        if (spots.Count > 0 && spots[0].Name == "forest-long") spots.Add(spots[0] with { Name = "forest-again", Setup = Day });
        // The tour in an order that changes the clock as seldom as possible: Level 10's tree (noon), the day's spots, the
        // night's, the last; each setting the clock only where it changes (a jump of the clock darkens the next few seconds)
        var ordered = new List<Showcase.Spot>();
        ordered.AddRange(spots.FindAll(s => s.Name == "way-in-level10"));
        ordered.AddRange(spots.FindAll(s => s.Name != "way-in-level10" && s.Name != "forest-again" && s.Setup?.StartsWith(Night) != true));
        ordered.AddRange(spots.FindAll(s => s.Setup?.StartsWith(Night) == true));
        ordered.AddRange(spots.FindAll(s => s.Name == "forest-again"));
        string clock = null;
        for (int k = 0; k < ordered.Count; k++)
        {
            string setup = ordered[k].Setup ?? "", want = setup.StartsWith(Night) ? Night : setup.StartsWith(Day) ? Day : null;
            if (want == null) continue;
            if (want == clock && ordered[k].Name != "forest-again")
            {
                string rest = setup.Substring(want.Length).TrimStart(';');
                ordered[k] = ordered[k] with { Setup = rest.Length == 0 ? null : rest };
            }
            clock = want;
        }
        return ordered;
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
