using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// How firmly reality holds in each part of the Backrooms, and where the level's impossible shortcuts (elevators,
/// pits, doors that open somewhere else) put people down.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltStability = 0x57AB;
    private const ulong SaltArrival = 0xA771;

    /// <summary>
    /// Reality stability at a position. 1 is neutral, higher slowly restores a wanderer's own stability, lower drains
    /// it. Each level has its own baseline that drifts gently from place to place; a few kinds of area are much
    /// better or worse than their surroundings.
    /// </summary>
    public float StabilityAt(double x, double y, double z, int floorY)
    {
        int mx = MacroOf((int)x), mz = MacroOf((int)z);
        int level = LevelAt(mx, mz);
        float drift = (float)Fbm(x / 60.0, z / 60.0, SaltStability);

        switch (level)
        {
            case 0:
                if (IsManilaMacro(mx, mz)) return 1.5f; // the one room that feels safe
                if (ZoneAt(mx, mz) == ZoneKind.Blackout) return 0.4f + 0.15f * drift;
                return 1.0f + 0.25f * drift;
            case 1:
                // The Habitable Zone, though the corridor sectors are less kind
                return IsLevel1Corridors(mx, mz) ? 0.85f + 0.15f * drift : 1.08f + 0.1f * drift;
            case 2:
                return 0.7f + 0.2f * drift;
            case 3:
                if (y < floorY) return 0.15f; // the flooded tunnels
                return 0.55f + 0.25f * drift;
            case 4:
                return 1.25f; // quiet, safe, and still
            default:
                return HotelZoneAt(mx, mz) switch
                {
                    HotelZone.Boiler => 0.4f + 0.15f * drift,
                    HotelZone.Lobby => 0.95f + 0.1f * drift,
                    HotelZone.Beverly => 1.2f,
                    _ => 0.75f + 0.2f * drift, // the corridors wear on you
                };
        }
    }

    /// <summary>Distance from spawn, in macro cells, of the middle of a level's ring.</summary>
    private static double LevelMidRadius(int level)
    {
        if (level <= 0) return 1.5;
        if (level >= LevelRadii.Length) return LevelRadii[^1] + 3;
        return (LevelRadii[level - 1] + LevelRadii[level]) / 2;
    }

    /// <summary>Picks one of the candidate tiles of a cell, by hash, that a person can actually walk away from.</summary>
    private (int, int)? PickEscapable(List<int> candidates, int mx, int mz, ulong h)
    {
        if (candidates.Count == 0) return null;
        int first = (int)(Hashing.Mix(h) % (ulong)candidates.Count);
        var cells = new Dictionary<(int, int), Tile[]>();
        for (int attempt = 0; attempt < Math.Min(candidates.Count, 12); attempt++)
        {
            int index = candidates[(first + attempt * 7) % candidates.Count];
            int x = mx * MacroSize + index % MacroSize, z = mz * MacroSize + index / MacroSize;
            if (CanWalkAway(x, z, cells)) return (x, z);
        }
        return null;
    }

    /// <summary>
    /// Whether you can walk at least 48 blocks away from a tile without breaking, climbing or squeezing past
    /// anything. This is what guarantees nobody is ever put down in a sealed pocket.
    /// </summary>
    private bool CanWalkAway(int startX, int startZ, Dictionary<(int, int), Tile[]> cells)
    {
        Tile TileAt(int x, int z)
        {
            int mx = MacroOf(x), mz = MacroOf(z);
            if (!cells.TryGetValue((mx, mz), out Tile[] tiles)) cells[(mx, mz)] = tiles = BuildMacro(mx, mz);
            return tiles[TileIndex(x - mx * MacroSize, z - mz * MacroSize)];
        }

        static bool Passable(in Tile t) =>
            t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water
            || t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox && t.Stair == 0;

        var seen = new HashSet<(int, int)> { (startX, startZ) };
        var queue = new Queue<(int, int)>();
        queue.Enqueue((startX, startZ));
        while (queue.Count > 0)
        {
            (int x, int z) = queue.Dequeue();
            if (Math.Abs(x - startX) + Math.Abs(z - startZ) >= 48) return true;
            foreach ((int dx, int dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                (int, int) next = (x + dx, z + dz);
                if (seen.Contains(next) || !Passable(TileAt(next.Item1, next.Item2))) continue;
                seen.Add(next);
                queue.Enqueue(next);
            }
        }
        return false;
    }

    /// <summary>Whether someone can be put down on this tile and walk away from it.</summary>
    private static bool IsArrivalSpot(in Tile t) =>
        t.Kind == TileKind.Floor && !t.Sealed && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Stair == 0 && t.Under == 0;

    /// <summary>
    /// Finds a place to arrive in the given level. The same key always leads to the same place. If
    /// <paramref name="anchor"/> is given, the arrival is next to a tile matching it (e.g. beside another elevator)
    /// where one can be found; otherwise it is any open floor.
    /// </summary>
    public (int X, int Z)? FindArrival(int level, ulong key, Func<Tile, bool> anchor = null)
    {
        ulong h = Hashing.Hash(seed, (int)(key & 0xFFFFFFFF), (int)(key >> 32), SaltArrival);
        double angle = Hashing.Unit(h) * Math.PI * 2;
        double radius = LevelMidRadius(level);
        int cx = spawnMacroX + (int)Math.Round(Math.Cos(angle) * radius);
        int cz = spawnMacroZ + (int)Math.Round(Math.Sin(angle) * radius);

        (int, int)? fallback = null;
        for (int r = 0; r <= 6; r++)
        {
            for (int dz = -r; dz <= r; dz++)
            {
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int mx = cx + dx, mz = cz + dz;
                    if (LevelAt(mx, mz) != level || IsSpawnMacro(mx, mz)) continue;

                    Tile[] tiles = BuildMacro(mx, mz);
                    var anchored = new List<int>();
                    var open = new List<int>();
                    for (int lz = 1; lz < MacroSize - 1; lz++)
                    {
                        for (int lx = 1; lx < MacroSize - 1; lx++)
                        {
                            int index = TileIndex(lx, lz);
                            if (!IsArrivalSpot(tiles[index])) continue;
                            open.Add(index);
                            if (anchor != null && (anchor(tiles[index - 1]) || anchor(tiles[index + 1])
                                || anchor(tiles[index - MacroSize]) || anchor(tiles[index + MacroSize]))) anchored.Add(index);
                        }
                    }

                    (int, int)? spot = PickEscapable(anchored, mx, mz, h);
                    if (spot != null) return spot;
                    fallback ??= PickEscapable(open, mx, mz, h);
                    // Without an anchor any open floor will do; with one, keep looking for an anchored spot
                    if (anchor == null && fallback != null) return fallback;
                }
            }
        }
        return fallback;
    }
}
