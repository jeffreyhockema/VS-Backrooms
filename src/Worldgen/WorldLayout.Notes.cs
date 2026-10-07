using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// What a wanderer's note can tell you: where the nearest gate out of a level is, the nearest other way out (an
/// elevator, a stairwell, a pit), the nearest place where something was left untouched, or the nearest refuge.
/// Each search goes outward cell by cell and stops at the first ring that finds something.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The cells around one, nearest first: ring 0 is the cell itself, ring r the square r cells out.</summary>
    private static IEnumerable<(int Mx, int Mz, int Ring)> CellsOutward(int mx0, int mz0, int rings)
    {
        for (int r = 0; r <= rings; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) == r) yield return (mx0 + dx, mz0 + dz, r);
    }

    /// <summary>
    /// Searches outward for the nearest tile (in the same level) that matches, within <paramref name="radius"/> blocks.
    /// Once something is found, only one more ring is searched (a nearer match may lie in the next ring's corner).
    /// </summary>
    private (int X, int Z)? NearestTile(int gx, int gz, int level, int radius, Func<Tile, bool> match, int min = 0)
    {
        (int X, int Z)? best = null;
        long bestD = long.MaxValue;
        int stopAfter = int.MaxValue;
        foreach ((int mx, int mz, int ring) in CellsOutward(MacroOf(gx), MacroOf(gz), radius / MacroSize + 1))
        {
            if (ring > stopAfter) break;
            if (LevelAt(mx, mz) != level) continue;
            // (Built afresh rather than through the small cell cache, which a wide search would only flush)
            Tile[] tiles = BuildMacro(mx, mz);
            for (int i = 0; i < tiles.Length; i++)
            {
                if (!match(tiles[i])) continue;
                int x = mx * MacroSize + i % MacroSize, z = mz * MacroSize + i / MacroSize;
                long d = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                if (d > (long)radius * radius || d < (long)min * min || d >= bestD) continue;
                bestD = d;
                best = (x, z);
                stopAfter = Math.Min(stopAfter, ring + 1);
            }
        }
        return best;
    }

    /// <summary>The nearest way into another level that is not a gate: an elevator, a stairwell that goes somewhere, a pit, a noclip wall, stairs down.</summary>
    public (int X, int Z)? NearestThreshold(int gx, int gz, int level, int radius) =>
        NearestTile(gx, gz, level, radius, t => t.Kind == TileKind.Pit || t.Under == Unders.Noclip || t.Under is >= Unders.Descent1 and <= Unders.Descent3
            || t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator || t.Stair > 0 && t.Under == 0 && t.Level is 1 or 4 or 5);

    /// <summary>The nearest supply box or crate that nobody has opened yet (not counting any right beside you).</summary>
    public (int X, int Z)? NearestCache(int gx, int gz, int level, int radius) =>
        NearestTile(gx, gz, level, radius, t => !t.Looted && (t.SupplyBox || IsCrate(t, t.Level)), min: 12);

    /// <summary>
    /// The nearest refuge: the Manila Room, a Sanctum, the Beverly Room, the Snackrooms, a wanderer who trades, the
    /// 9th Road. Decided cell by cell, so it is cheap to search far.
    /// </summary>
    public (int X, int Z)? NearestRefuge(int gx, int gz, int level, int radius)
    {
        foreach ((int mx, int mz, int ring) in CellsOutward(MacroOf(gx), MacroOf(gz), radius / MacroSize + 1))
        {
            if (LevelAt(mx, mz) != level) continue;
            int cx = mx * MacroSize + MacroSize / 2, cz = mz * MacroSize + MacroSize / 2;
            bool refuge = level switch
            {
                0 => IsManilaMacro(mx, mz),
                3 => IsSanctum(mx, mz),
                5 => HotelZoneAt(mx, mz) == HotelZone.Beverly,
                6 => IsSnackrooms(mx, mz),
                _ => false,
            };
            if (refuge) return (cx, cz);
            if (level is 1 or 4 or 8 or 11 && WandererSite(mx, mz) is { } site) return site;
        }
        return null;
    }
}
