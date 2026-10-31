using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>), all worked out from the layout:
    /// the Heart of Water and its Green Giants, a long view through the forest, a light shaft under a hole in the lid, a
    /// buried sentry's face, a glow room of each colour (the nearest to the middle; a Hound brought into the amber one),
    /// Base Seedling (one of its tunnels first, from inside, so the quartermaster is put down out of sight before the camp
    /// shot), the four ruins of the Architects from their plazas, and the tangle at the forest's edge.
    /// </summary>
    public IEnumerable<Showcase.Spot> L23ShowcaseSpots(WorldGeometry geometry)
    {
        int fy = geometry.FloorFor(Level23);
        var spots = new List<Showcase.Spot>();
        int mx = L23MidX, mz = L23MidZ;
        double bearing = L23Bearing;

        // The Heart of Water: from the slope down to the shore between two Green Giants, across the pool to the far ones
        {
            double a = bearing + 0.5 * Math.PI * 2 / 7;
            int x = mx + (int)Math.Round(Math.Cos(a) * 38), z = mz + (int)Math.Round(Math.Sin(a) * 38);
            spots.Add(L23Spot("heart-of-water", x, z, L23Ground(x, z) + 1, fy, mx, mz, 6));
        }
        // A long view through the forest: the clearest run of open ground among a few places round the middle
        {
            (int X, int Z, double H, int Run) best = (0, 0, 0, -1);
            for (int k = 0; k < 12; k++)
            {
                double a = bearing + k * Math.PI / 6;
                if (!L23ClearNear(mx + (int)Math.Round(Math.Cos(a) * 110), mz + (int)Math.Round(Math.Sin(a) * 110), 8, out int x, out int z)) continue;
                for (int d = 0; d < 8; d++)
                {
                    double h = d * 45;
                    int run = L23OpenRun(x, z, h, 64);
                    if (run > best.Run) best = (x, z, h, run);
                }
            }
            if (best.Run >= 0) spots.Add(new Showcase.Spot("forest-long", best.X + 0.5, fy + L23Ground(best.X, best.Z) + 1, best.Z + 0.5, best.H, 4));
        }
        // A light shaft: the nearest good-sized hole in the lid to the middle, from a few steps off, looking up into it
        {
            (double X, double Z, double D) hole = (0, 0, double.MaxValue);
            int hi0 = Hashing.FloorDiv(mx, L23HolePitch), hj0 = Hashing.FloorDiv(mz, L23HolePitch);
            for (int j = hj0 - 4; j <= hj0 + 4; j++)
                for (int i = hi0 - 4; i <= hi0 + 4; i++)
                {
                    if (!L23HoleAt(i, j, out double cx, out double cz, out double r) || r < 3.4) continue;
                    double d = L23FromMid((int)cx, (int)cz);
                    if (d < L23CoreRadius + 30 || d > L23Reach - 40 || d >= hole.D) continue;
                    hole = (cx, cz, d);
                }
            if (hole.D < double.MaxValue)
                for (int k = 0; k < 6; k++)
                {
                    double a = bearing + k * Math.PI / 3;
                    if (!L23ClearNear((int)(hole.X + Math.Cos(a) * 9), (int)(hole.Z + Math.Sin(a) * 9), 3, out int x, out int z)) continue;
                    spots.Add(L23Spot("light-shaft", x, z, L23Ground(x, z) + 1, fy, hole.X, hole.Z, 30));
                    break;
                }
        }
        // A buried sentry's face: the nearest to the middle with open ground in front of it
        {
            int ti0 = Hashing.FloorDiv(mx, L23Pitch), tj0 = Hashing.FloorDiv(mz, L23Pitch);
            bool done = false;
            for (int ring = 4; ring < 20 && !done; ring++)
                for (int j = tj0 - ring; j <= tj0 + ring && !done; j++)
                    for (int i = ti0 - ring; i <= ti0 + ring && !done; i++)
                    {
                        if (Math.Max(Math.Abs(i - ti0), Math.Abs(j - tj0)) != ring) continue;
                        L23Trunk t = L23TrunkAt(i, j);
                        if (!t.Exists || !t.Sentry) continue;
                        var (fx, fz) = t.SentryFacing switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
                        int x = t.SentryX + fx * 4, z = t.SentryZ + fz * 4;
                        if (!L23ClearSurface(x, z) || !L23ClearSurface(t.SentryX + fx * 2, t.SentryZ + fz * 2)) continue;
                        spots.Add(L23Spot("sentry", x, z, L23Ground(x, z) + 1, fy, t.SentryX + 0.5, t.SentryZ + 0.5, 0, eyeAt: t.Base + 2.5));
                        done = true;
                    }
        }
        // A glow room of each colour: the nearest of each to the middle, from part way out across its floor to its middle
        string[] colours = { null, "teal", "violet", "amber" };
        for (byte colour = 1; colour <= 3; colour++)
        {
            int ci0 = Hashing.FloorDiv(mx, L23CavePitch), cj0 = Hashing.FloorDiv(mz, L23CavePitch);
            L23Cavern best = default;
            double bestD = double.MaxValue;
            for (int j = cj0 - 5; j <= cj0 + 5; j++)
                for (int i = ci0 - 5; i <= ci0 + 5; i++)
                {
                    L23Cavern c = L23GlowAt(i, j);
                    if (!c.Exists || c.Colour != colour) continue;
                    double d = L23FromMid(c.X, c.Z);
                    if (d < bestD) { bestD = d; best = c; }
                }
            if (!best.Exists) continue;
            for (int k = 0; k < 8; k++)
            {
                double a = bearing + k * Math.PI / 4;
                int x = best.X + (int)Math.Round(Math.Cos(a) * best.R * 0.6), z = best.Z + (int)Math.Round(Math.Sin(a) * best.R * 0.6);
                if (!L23ClearCave(x, z, best, out int floor)) continue;
                spots.Add(L23Spot($"glow-{colours[colour]}", x, z, floor + 1, fy, best.X + 0.5, best.Z + 0.5, 12,
                    setup: colour == 3 ? "/backrooms encounter hound ambient" : null));
                break;
            }
        }
        // Base Seedling: first from inside, at one of its tunnels' feet, looking up the tunnel (twenty-odd blocks from the
        // quartermaster's spot, facing away from it: he is put down then); then the camp, the hollow tree and the tents
        {
            L23Cavern s = L23Specials[0];
            L23Passage p = s.T0;
            for (int m = 1; m < s.Tunnels; m++)
            {
                L23Passage q = s.Tunnel(m);
                if (Math.Pow(q.Ax - s.X, 2) + Math.Pow(q.Az - s.Z - 6, 2) > Math.Pow(p.Ax - s.X, 2) + Math.Pow(p.Az - s.Z - 6, 2)) p = q;
            }
            // (Where the tunnel leaves the camp's floor, a little in from its foot, where the cavern is still tall)
            double ta = Math.Atan2(p.Az - s.Z, p.Ax - s.X);
            int x = (int)Math.Floor(s.X + Math.Cos(ta) * s.R * 0.6), z = (int)Math.Floor(s.Z + Math.Sin(ta) * s.R * 0.6);
            if (L23Cave(x, z, out int f, out _, out L23Cavern there) && there.Kind == L23CaveKind.Seedling)
                spots.Add(L23Spot("seedling-tunnel", x, z, f + 1, fy, p.Bx, p.Bz, 8));
            int cx = s.X + 1, cz = s.Z + 17;
            if (L23Cave(cx, cz, out int cf, out _, out _))
                spots.Add(L23Spot("seedling-camp", cx, cz, cf + 1, fy, s.X + 0.5, s.Z + 2.5, 4));
        }
        // The ruins of the Architects, each from the south edge of its plaza (their doors face south)
        string[] ruins = { "lighthouse", "sphere", "colosseum", "parthenon" };
        int[] back = { 16, 10, 17, 15 };
        for (int k = 0; k < 4; k++)
        {
            L23Cavern r = L23Specials[k + 1];
            int u = k == 1 ? 2 : k == 2 ? 5 : 0, x = r.X + u, z = r.Z + back[k];
            if (!L23Cave(x, z, out int f, out _, out _)) continue;
            spots.Add(L23Spot($"ruin-{ruins[k]}", x, z, f + 1, fy, r.X + 0.5, r.Z + 0.5, k == 1 ? 2 : 10));
        }
        // The tangle at the forest's edge: out from the middle until it starts, then back a dozen blocks, looking at it
        {
            double a = bearing + Math.PI * 1.25;
            for (int d = L23Reach - 60; d < L23Reach + 40; d++)
            {
                int ex = mx + (int)Math.Round(Math.Cos(a) * d), ez = mz + (int)Math.Round(Math.Sin(a) * d);
                if (!L23InTangle(ex, ez)) continue;
                if (L23ClearNear(mx + (int)Math.Round(Math.Cos(a) * (d - 12)), mz + (int)Math.Round(Math.Sin(a) * (d - 12)), 6, out int x, out int z))
                    spots.Add(L23Spot("edge-tangle", x, z, L23Ground(x, z) + 1, fy, ex + 0.5, ez + 0.5, 8));
                break;
            }
        }
        return spots;
    }

    /// <summary>A spot standing on <paramref name="rel"/> (feet) at a column, looking toward a point (at a pitch, or toward a height when <paramref name="eyeAt"/> is given).</summary>
    private static Showcase.Spot L23Spot(string name, int x, int z, int rel, int fy, double tx, double tz, double pitch, string setup = null, double? eyeAt = null)
    {
        double dx = tx - (x + 0.5), dz = tz - (z + 0.5);
        double heading = (Math.Atan2(dx, -dz) * 180 / Math.PI + 360) % 360;
        if (eyeAt is { } y) pitch = Math.Atan2(y - (rel + 1.6), Math.Sqrt(dx * dx + dz * dz)) * 180 / Math.PI;
        return new Showcase.Spot(name, x + 0.5, fy + rel, z + 0.5, Math.Round(heading, 1), Math.Round(pitch, 1), setup);
    }

    /// <summary>Whether someone could stand on the forest floor at a column: no wood, no tunnel, three blocks of air over the ground.</summary>
    private bool L23ClearSurface(int gx, int gz)
    {
        if (L23InTangle(gx, gz) || L23FromMid(gx, gz) < L23CoreRadius) return false;
        if (L23Tunnel(gx, gz, out _, out _, out double off) && off < 1.5) return false;
        var kinds = new byte[3];
        L23Wood(gx, gz, L23Ground(gx, gz) + 1, kinds);
        return kinds[0] == 0 && kinds[1] == 0 && kinds[2] == 0;
    }

    /// <summary>The nearest column to a point (within a reach) where someone could stand on the forest floor.</summary>
    private bool L23ClearNear(int gx, int gz, int reach, out int x, out int z)
    {
        for (int r = 0; r <= reach; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || !L23ClearSurface(gx + dx, gz + dz)) continue;
                    x = gx + dx;
                    z = gz + dz;
                    return true;
                }
        x = z = 0;
        return false;
    }

    /// <summary>How many blocks the forest stays open at eye height along a heading from a column (up to a limit).</summary>
    private int L23OpenRun(int gx, int gz, double heading, int limit)
    {
        double rad = heading * Math.PI / 180, sx = Math.Sin(rad), sz = -Math.Cos(rad);
        int eye = L23Ground(gx, gz) + 2;
        var kinds = new byte[2];
        for (int d = 1; d <= limit; d++)
        {
            int x = (int)Math.Floor(gx + 0.5 + sx * d), z = (int)Math.Floor(gz + 0.5 + sz * d);
            if (L23InTangle(x, z)) return d;
            L23Wood(x, z, eye, kinds);
            if (kinds[0] != 0 || kinds[1] != 0 || L23Ground(x, z) >= eye) return d;
        }
        return limit;
    }

    /// <summary>Whether someone could stand in a glow room at a column: in that room, no pillar, no little tree; its floor.</summary>
    private bool L23ClearCave(int gx, int gz, in L23Cavern cave, out int floor)
    {
        if (!L23Cave(gx, gz, out floor, out int ceiling, out L23Cavern c) || c.X != cave.X || c.Z != cave.Z || ceiling - floor < 4) return false;
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (L23PillarAt(gx + dx, gz + dz) != 0) return false;
        int ti = Hashing.FloorDiv(gx, L23TreePitch), tj = Hashing.FloorDiv(gz, L23TreePitch);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
                if (L23LittleTreeAt(ti + di, tj + dj, out int x, out int z, out _) && Math.Abs(x - gx) <= 1 && Math.Abs(z - gz) <= 1) return false;
        return true;
    }
}
