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
                if (IsRedRoom(mx, mz)) return 0.1f; // and the ones that are anything but
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
            case 6:
                if (IsSnackrooms(mx, mz)) return 1.45f; // the jackpot, as long as you can stay
                return 0.35f + 0.1f * drift; // total darkness eats at you
            case 7:
                // Steady at the surface; the deeper you dive, the less anything holds
                if (y >= floorY) return 0.95f + 0.1f * drift;
                double below = floorY - y;
                return (float)Math.Max(0.05, 0.9 - below / 60.0);
            case 8:
                // The 9th Road runs through islands of stability
                return IsNinthRoad((int)Math.Floor(x), (int)Math.Floor(z)) ? 1.25f : 0.7f + 0.15f * drift;
            case 9:
                return 0.65f + 0.15f * drift; // the streets are the most dangerous place
            case 10:
                return 1.15f + 0.05f * drift;
            case 11:
                // The safest place in the Backrooms; only the subway, and the dark alleys, are less kind
                // (floorY is the other levels' floor; the city's streets lie lower)
                return y < floorY - WorldGeometry.CityDrop ? 0.9f + 0.1f * drift : 1.3f + 0.05f * drift;
            case 5:
                return HotelZoneAt(mx, mz) switch
                {
                    HotelZone.Boiler => 0.4f + 0.15f * drift,
                    HotelZone.Lobby => 0.95f + 0.1f * drift,
                    HotelZone.Beverly => 1.2f,
                    _ => 0.75f + 0.2f * drift, // the corridors wear on you
                };
            default:
                return 1f;
        }
    }

    /// <summary>Distance from spawn, in macro cells, of the middle of a level's ring along a direction.</summary>
    private double LevelMidRadius(int level, double angle)
    {
        if (level <= 0) return OuterEdge(0, angle) * 0.4;
        if (level >= RingWidths.Length) return OuterEdge(RingWidths.Length - 1, angle) + 12;
        return (InnerEdge(level, angle) + OuterEdge(level, angle)) / 2;
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
            || t.Kind == TileKind.Floor && IsWalkThroughProp(t.Variant) && (t.Stack == 0 || t.Variant != 0) && !t.SupplyBox && t.Stair == 0;

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

    /// <summary>A place to arrive in one of the Snackrooms, chosen by key from every food court in the world.</summary>
    public (int X, int Z)? FindSnackroomsArrival(ulong key, Func<Tile, bool> beside = null)
    {
        (int Mx, int Mz)? cell = SnackroomCellFor(key);
        if (cell == null) return null;
        var target = cell.Value;
        return FindArrival(6, key, beside, (mx, mz) => (mx, mz) == target, null, checkEscape: false, near: target);
    }

    /// <summary>
    /// A place to arrive in one of Level 7's entry rooms. They are built only where the sea is shallow, at the
    /// inner edge of the ring, so the search starts there.
    /// </summary>
    public (int X, int Z)? FindEntryRoomArrival(ulong key)
    {
        ulong h = Hashing.Hash(seed, (int)(key & 0xFFFFFFFF), (int)(key >> 32), SaltArrival);
        // Just inside the shore, where the sea is still shallow
        double angle = Hashing.Unit(h) * Math.PI * 2, radius = InnerEdge(7, angle) + 0.08 * (OuterEdge(7, angle) - InnerEdge(7, angle));
        var start = (spawnMacroX + (int)Math.Round(Math.Cos(angle) * radius), spawnMacroZ + (int)Math.Round(Math.Sin(angle) * radius));
        bool EntryRoom(Tile t) => t.Zone == 1 && t.Stack == 0;
        return FindArrival(7, key, null, (mx, mz) => true, EntryRoom, checkEscape: false, near: start)
            ?? FindArrival(7, key, null, (mx, mz) => true, EntryRoom, checkEscape: false);
    }

    /// <summary>
    /// Finds a place to arrive in the given level. The same key always leads to the same place. If
    /// <paramref name="anchor"/> is given, the arrival is next to a tile matching it (e.g. beside another elevator)
    /// where one can be found; otherwise it is any open floor. <paramref name="cellFilter"/> restricts which cells
    /// may be chosen (the Snackrooms, sealed from the rest, are never chosen otherwise); <paramref name="spot"/>
    /// replaces the usual test for a tile to stand on; and without <paramref name="checkEscape"/>, the arrival need
    /// not be walkable away from (the Snackrooms are sealed; Level 7's entry rooms drop you into the sea).
    /// <paramref name="near"/> searches outward from a given cell instead of a point picked from the key.
    /// </summary>
    public (int X, int Z)? FindArrival(int level, ulong key, Func<Tile, bool> anchor = null, Func<int, int, bool> cellFilter = null,
                                       Func<Tile, bool> spot = null, bool checkEscape = true, (int Mx, int Mz)? near = null)
    {
        ulong h = Hashing.Hash(seed, (int)(key & 0xFFFFFFFF), (int)(key >> 32), SaltArrival);
        double angle = Hashing.Unit(h) * Math.PI * 2;
        double radius = LevelMidRadius(level, angle);
        int cx = spawnMacroX + (int)Math.Round(Math.Cos(angle) * radius);
        int cz = spawnMacroZ + (int)Math.Round(Math.Sin(angle) * radius);
        if (level == 11)
        {
            // The city is not a ring: somewhere towards its middle, out on a sidewalk
            (cx, cz) = CityArrivalCell(h);
            spot ??= IsCityArrivalSpot;
        }
        int reach = cellFilter != null ? 16 : 6;
        if (near != null) (cx, cz, reach) = (near.Value.Mx, near.Value.Mz, Math.Min(reach, 5));

        (int, int)? fallback = null;
        for (int r = 0; r <= reach; r++)
        {
            for (int dz = -r; dz <= r; dz++)
            {
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int mx = cx + dx, mz = cz + dz;
                    if (LevelAt(mx, mz) != level || IsSpawnMacro(mx, mz)) continue;
                    if (cellFilter != null ? !cellFilter(mx, mz) : level == 6 && IsSnackrooms(mx, mz)) continue;

                    Tile[] tiles = BuildMacro(mx, mz);
                    var anchored = new List<int>();
                    var open = new List<int>();
                    for (int lz = 1; lz < MacroSize - 1; lz++)
                    {
                        for (int lx = 1; lx < MacroSize - 1; lx++)
                        {
                            int index = TileIndex(lx, lz);
                            if (!(spot != null ? spot(tiles[index]) : IsArrivalSpot(tiles[index]))) continue;
                            open.Add(index);
                            if (anchor != null && (anchor(tiles[index - 1]) || anchor(tiles[index + 1])
                                || anchor(tiles[index - MacroSize]) || anchor(tiles[index + MacroSize]))) anchored.Add(index);
                        }
                    }

                    (int, int)? found = checkEscape ? PickEscapable(anchored, mx, mz, h) : PickAny(anchored, mx, mz, h);
                    if (found != null) return found;
                    fallback ??= checkEscape ? PickEscapable(open, mx, mz, h) : PickAny(open, mx, mz, h);
                    // Without an anchor any open floor will do; with one, keep looking for an anchored spot
                    if (anchor == null && fallback != null) return fallback;
                }
            }
        }
        return fallback;
    }

    private static (int, int)? PickAny(List<int> candidates, int mx, int mz, ulong h)
    {
        if (candidates.Count == 0) return null;
        int index = candidates[(int)(Hashing.Mix(h) % (ulong)candidates.Count)];
        return (mx * MacroSize + index % MacroSize, mz * MacroSize + index / MacroSize);
    }

    // ================= Thresholds as features =================

    // Cells looked at lately on behalf of thresholds (a flight of stairs or a lake bottom is asked about many times)
    private readonly Dictionary<(int, int), Tile[]> featureCells = new();

    /// <summary>The layout tile at a block position.</summary>
    public Tile TileAt(int x, int z)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        Tile[] tiles;
        lock (featureCells)
        {
            if (!featureCells.TryGetValue((mx, mz), out tiles))
            {
                if (featureCells.Count >= 48) featureCells.Clear();
                featureCells[(mx, mz)] = tiles = BuildMacro(mx, mz);
            }
        }
        return tiles[TileIndex(x - mx * MacroSize, z - mz * MacroSize)];
    }

    /// <summary>
    /// One position that stands for a whole threshold: a flight of stairs, both leaves of an elevator, every tile of
    /// a lake's bottom. It is the least (by x, then z) of the tiles joined to the given one that are also
    /// <paramref name="part"/> of it, so whichever tile of the threshold is asked about, the answer is the same.
    /// </summary>
    public (int X, int Z) FeatureOrigin(int x, int z, Func<Tile, bool> part)
    {
        if (!part(TileAt(x, z))) return (x, z);
        (int X, int Z) best = (x, z);
        var seen = new HashSet<(int, int)> { best };
        var queue = new Queue<(int, int)>();
        queue.Enqueue(best);
        while (queue.Count > 0 && seen.Count < 4000)
        {
            (int cx, int cz) = queue.Dequeue();
            foreach ((int dx, int dz) in Steps)
            {
                (int X, int Z) next = (cx + dx, cz + dz);
                if (seen.Contains(next) || !part(TileAt(next.X, next.Z))) continue;
                seen.Add(next);
                queue.Enqueue(next);
                if (next.X < best.X || next.X == best.X && next.Z < best.Z) best = next;
            }
        }
        return best;
    }

    /// <summary>The threshold (see <see cref="FeatureOrigin"/>) that a position stands right beside, if any.</summary>
    public (int X, int Z)? FeatureBeside(int x, int z, Func<Tile, bool> part)
    {
        foreach ((int dx, int dz) in Steps)
            if (part(TileAt(x + dx, z + dz))) return FeatureOrigin(x + dx, z + dz, part);
        return null;
    }

    private static readonly (int, int)[] Steps = { (1, 0), (-1, 0), (0, 1), (0, -1) };

    /// <summary>
    /// The nearest clear floor to a threshold that a person can be put down on without at once going through it
    /// again: reached by walking from the threshold, with nothing standing on it, no step, no drop, and nothing under
    /// it that leads elsewhere.
    /// </summary>
    public (int X, int Z)? StandingSpotNear(int x, int z, int reach = 7)
    {
        static bool Open(in Tile t) => t.Kind is TileKind.Floor or TileKind.Doorway or TileKind.ArchDoor;
        static bool Standable(in Tile t) =>
            t.Kind == TileKind.Floor && !t.Sealed && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Stair == 0
            && t.Under is 0 or Unders.LakeRim or Unders.Subway or Unders.Station && t.Floor != FloorKind.PoolDeep;

        var seen = new HashSet<(int, int)> { (x, z) };
        var queue = new Queue<(int X, int Z, int Distance)>();
        queue.Enqueue((x, z, 0));
        while (queue.Count > 0)
        {
            (int cx, int cz, int distance) = queue.Dequeue();
            Tile here = TileAt(cx, cz);
            if (distance > 0 && Standable(here)) return (cx, cz);
            if (distance >= reach) continue;
            foreach ((int dx, int dz) in Steps)
            {
                (int, int) next = (cx + dx, cz + dz);
                if (seen.Contains(next) || !Open(TileAt(next.Item1, next.Item2))) continue;
                seen.Add(next);
                queue.Enqueue((next.Item1, next.Item2, distance + 1));
            }
        }
        return null;
    }
}
