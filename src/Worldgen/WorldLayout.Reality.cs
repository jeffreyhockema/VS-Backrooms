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
        int mx = MacroOf((int)Math.Floor(x)), mz = MacroOf((int)Math.Floor(z));
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
            case Poolrooms:
            {
                // Calm in the light, dread in the dark corners, and in the Reservoir nothing holds at all
                if (IsReservoir(mx, mz)) return 0.15f;
                return TileAt((int)Math.Floor(x), (int)Math.Floor(z)).Detail == PoolDark ? 0.6f + 0.1f * drift : 1.35f;
            }
            case Motion:
                // The hills are kind enough by day; the castle is not ("bring some Almond Water")
                return InCastle((int)Math.Floor(x), (int)Math.Floor(z)) ? 0.7f + 0.1f * drift : 1.05f + 0.05f * drift;
            // The five kept as 14-18 work theirs out in their own files
            case RunLevel: return RunStability(x, y, z, floorY, drift);
            case FunLevel: return FunStability(x, y, z, floorY, drift);
            case TheEnd: return EndStability(x, y, z, floorY, drift);
            case Hub: return HubStability(x, y, z, floorY, drift);
            case Level974: return L974Stability(x, y, z, floorY, drift);
            case Level3999: return L3999Stability(x, y, z, floorY, drift);
            case Level188: return L188Stability(x, y, z, floorY, drift);
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
            foreach ((int dx, int dz) in Steps)
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
    /// From layout version 5, where the level's own test for a spot is used, the search would rather put someone
    /// down where they can see the level (see <see cref="ArrivalPreference"/>): it takes the best such spot within
    /// <see cref="PreferredReach"/> rings of where it would have settled, and where there is none, the spot it would
    /// have settled on, so no level has fewer places to arrive than before.
    /// </summary>
    public (int X, int Z)? FindArrival(int level, ulong key, Func<Tile, bool> anchor = null, Func<int, int, bool> cellFilter = null,
                                       Func<Tile, bool> spot = null, bool checkEscape = true, (int Mx, int Mz)? near = null)
    {
        bool preferring = Version >= 5 && spot == null && RanksArrivals(level);
        ulong h = Hashing.Hash(seed, (int)(key & 0xFFFFFFFF), (int)(key >> 32), SaltArrival);
        double angle = Hashing.Unit(h) * Math.PI * 2;
        double radius = LevelMidRadius(level, angle);
        int cx = spawnMacroX + (int)Math.Round(Math.Cos(angle) * radius);
        int cz = spawnMacroZ + (int)Math.Round(Math.Sin(angle) * radius);
        // From layout version 9 Level 8's roads lie hundreds of blocks apart: start from one of them in that direction
        if (level == 8 && Version >= 9) (cx, cz) = L8ArrivalCell(angle, h);
        if (level == 11)
        {
            // The city is not a ring: somewhere towards its middle, out on a sidewalk
            (cx, cz) = CityArrivalCell(h);
            spot ??= IsCityArrivalSpot;
        }
        else if (level == Poolrooms)
        {
            // Nor are the Poolrooms: somewhere toward the middle, on a deck or in the shallows, in the light
            (cx, cz) = PoolArrivalCell(h);
            spot ??= IsPoolArrivalSpot;
        }
        else if (level == Motion)
        {
            // Nor is Motion: out on the grass of the hills, near enough that the houses come apart
            (cx, cz) = MotionArrivalCell(h);
            spot ??= IsMotionArrivalSpot;
        }
        // Nor are the five kept as 14-18: each picks its own cell and its own kind of spot
        else if (level == RunLevel)
        {
            (cx, cz) = RunArrivalCell(h);
            spot ??= IsRunArrivalSpot;
        }
        else if (level == FunLevel)
        {
            (cx, cz) = FunArrivalCell(h);
            spot ??= IsFunArrivalSpot;
        }
        else if (level == TheEnd)
        {
            (cx, cz) = EndArrivalCell(h);
            spot ??= IsEndArrivalSpot;
        }
        else if (level == Hub)
        {
            (cx, cz) = HubArrivalCell(h);
            spot ??= IsHubArrivalSpot;
        }
        else if (level == Level974)
        {
            (cx, cz) = L974ArrivalCell(h);
            spot ??= IsL974ArrivalSpot;
            checkEscape = false; // a house with no way out is the point
        }
        else if (level == Level3999)
        {
            (cx, cz) = L3999ArrivalCell(h);
            spot ??= IsL3999ArrivalSpot;
        }
        else if (level == Level188)
        {
            (cx, cz) = L188ArrivalCell(h);
            spot ??= IsL188ArrivalSpot;
        }
        int reach = cellFilter != null ? 16 : 6;
        if (near != null) (cx, cz, reach) = (near.Value.Mx, near.Value.Mz, Math.Min(reach, 5));

        (int, int)? fallback = null, settled = null;
        var preferred = new (int, int)?[ArrivalRanks];
        int settledRing = 0;
        for (int r = 0; r <= reach; r++)
        {
            if (settled != null && r > settledRing + PreferredReach) break;
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
                    Func<int, int> rank = preferring ? ArrivalPreference(level, tiles, mx, mz) : null;
                    List<int>[] liked = null;
                    if (rank != null) { liked = new List<int>[ArrivalRanks]; for (int k = 0; k < ArrivalRanks; k++) liked[k] = new List<int>(); }
                    for (int lz = 1; lz < MacroSize - 1; lz++)
                    {
                        for (int lx = 1; lx < MacroSize - 1; lx++)
                        {
                            int index = TileIndex(lx, lz);
                            if (!(spot != null ? spot(tiles[index]) : IsArrivalSpot(tiles[index]))) continue;
                            open.Add(index);
                            bool beside = anchor != null && (anchor(tiles[index - 1]) || anchor(tiles[index + 1])
                                || anchor(tiles[index - MacroSize]) || anchor(tiles[index + MacroSize]));
                            if (beside) anchored.Add(index);
                            // (With an anchor, only an anchored spot is ever preferred)
                            if (rank != null && (anchor == null || beside) && rank(index) is int rk and >= 0) liked[rk].Add(index);
                        }
                    }

                    // The best ranked spot is taken as soon as it is found; the others only if nothing better turns up
                    if (rank != null)
                        for (int k = 0; k < ArrivalRanks; k++)
                        {
                            if (preferred[k] != null) continue;
                            preferred[k] = checkEscape ? PickEscapable(liked[k], mx, mz, h) : PickAny(liked[k], mx, mz, h);
                            if (k == 0 && preferred[0] != null) return preferred[0];
                        }

                    if (settled != null) continue;
                    (int, int)? found = checkEscape ? PickEscapable(anchored, mx, mz, h) : PickAny(anchored, mx, mz, h);
                    if (found != null) settled = found;
                    else
                    {
                        fallback ??= checkEscape ? PickEscapable(open, mx, mz, h) : PickAny(open, mx, mz, h);
                        // Without an anchor any open floor will do; with one, keep looking for an anchored spot
                        if (anchor == null && fallback != null) settled = fallback;
                    }
                    if (settled == null) continue;
                    if (!preferring) return settled;
                    settledRing = r;
                }
            }
        }
        foreach (var best in preferred) if (best != null) return best;
        return settled ?? fallback;
    }

    /// <summary>How many rings past the spot it would have settled on the search goes on looking for a preferred one.</summary>
    private const int PreferredReach = 2;

    /// <summary>How many ranks <see cref="ArrivalPreference"/> gives its spots.</summary>
    private const int ArrivalRanks = 4;

    /// <summary>The levels whose arrivals <see cref="ArrivalPreference"/> ranks (from layout version 5).</summary>
    private static bool RanksArrivals(int level) => level is 2 or 3 or 9 or 11 or Poolrooms or Motion;

    /// <summary>
    /// From layout version 5, which of a cell's arrival spots a level would rather put someone down on, so that the
    /// first thing they see is the level rather than the dark or the inside of a tree: for each tile (by index) its
    /// rank, 0 the best, or -1 for none better than any other spot. Levels 2 and 3: within a few steps of a working
    /// light, so you arrive under a live circuit (a stretch of Level 2 wired in series, a section of Level 3) and walk
    /// into the dead ones rather than waking in them. Level 9: out in the open, with nothing but open ground for two
    /// blocks round (not on the path down the side of a house, nor under a tree) and nothing standing next to you.
    /// The city: with nothing standing next to you on the sidewalk, and no street tree or parked car within two
    /// blocks. The Poolrooms: in one of the rooms that show the level off (a domed rotunda, a pillar hall, a natatorium)
    /// rather than a narrow corridor facing a wall; in the light falling from a slit (in a rotunda, anywhere its arches
    /// light), or failing that anywhere but the dark corners. Motion: clear of any tree's crown, even one down in a
    /// valley below a hillside. The cell is (mx, mz).
    /// </summary>
    private Func<int, int> ArrivalPreference(int level, Tile[] tiles, int mx, int mz)
    {
        switch (level)
        {
            case 2:
            case 3:
                bool[] lit = NearWorkingLight(tiles, 4);
                return i => lit[i] ? 0 : -1;
            case 9:
                return i => ClearAround(tiles, i, 2, t => t.Kind == TileKind.Floor && t.Roof == 0 && t.Variant != Props.Tree)
                    && ClearAround(tiles, i, 1, t => IsWalkThroughProp(t.Variant)) ? 0 : -1;
            case 11:
                return i => ClearAround(tiles, i, 1, t => t.Variant == 0)
                    && ClearAround(tiles, i, 2, t => t.Variant is not (Props.Tree or Props.Car or Props.CarPart)) ? 0 : -1;
            case Poolrooms:
            {
                var show = PoolShowRooms(mx, mz);
                return i =>
                {
                    if (tiles[i].Detail == PoolDark) return -1;
                    bool lit = tiles[i].Floor == FloorKind.PoolSunlit || show[i].Rotunda;
                    // Room to look round: no more than a pillar hall's few pillars in the 7 x 7 square about the spot
                    bool roomy = OpenAround(tiles, i, 3) >= 40;
                    if (show[i].Any && lit && roomy) return 0;
                    if (lit && roomy) return 1;
                    return lit ? 2 : 3;
                };
            }
            case Motion:
                return i => ClearAround(tiles, i, 4, t => t.Variant != Props.Tree) ? 0 : -1;
            default:
                return null;
        }
    }

    /// <summary>
    /// How many tiles of a cell within <paramref name="radius"/> of one (a square) are open (not wall); 0 for a tile too
    /// near the cell's edge for the square to fit in it.
    /// </summary>
    private static int OpenAround(Tile[] tiles, int index, int radius)
    {
        int lx = index % MacroSize, lz = index / MacroSize, open = 0;
        if (lx < radius || lz < radius || lx >= MacroSize - radius || lz >= MacroSize - radius) return 0;
        for (int z = lz - radius; z <= lz + radius; z++)
            for (int x = lx - radius; x <= lx + radius; x++)
                if (tiles[TileIndex(x, z)].Kind is not (TileKind.Wall or TileKind.Door)) open++;
        return open;
    }

    /// <summary>
    /// Whether every tile of a cell within <paramref name="radius"/> of one (a square) passes <paramref name="ok"/>.
    /// A tile too near the cell's edge for the square to fit in it does not.
    /// </summary>
    private static bool ClearAround(Tile[] tiles, int index, int radius, Func<Tile, bool> ok)
    {
        int lx = index % MacroSize, lz = index / MacroSize;
        if (lx < radius || lz < radius || lx >= MacroSize - radius || lz >= MacroSize - radius) return false;
        for (int z = lz - radius; z <= lz + radius; z++)
            for (int x = lx - radius; x <= lx + radius; x++)
                if (!ok(tiles[TileIndex(x, z)])) return false;
        return true;
    }

    /// <summary>The tiles of a cell no more than <paramref name="steps"/> steps (within the cell) from a working light overhead.</summary>
    private static bool[] NearWorkingLight(Tile[] tiles, int steps)
    {
        var near = new bool[tiles.Length];
        var queue = new Queue<(int Index, int Steps)>();
        for (int i = 0; i < tiles.Length; i++)
            if (tiles[i].Ceiling is CeilingKind.LightOn or CeilingKind.LightLit or CeilingKind.LightWarm or CeilingKind.Chandelier)
            {
                near[i] = true;
                queue.Enqueue((i, 0));
            }
        while (queue.Count > 0)
        {
            var (i, d) = queue.Dequeue();
            if (d == steps) continue;
            int x = i % MacroSize, z = i / MacroSize;
            foreach ((int dx, int dz) in Steps)
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= MacroSize || nz >= MacroSize) continue;
                int n = TileIndex(nx, nz);
                if (near[n] || tiles[n].Kind is not (TileKind.Floor or TileKind.Doorway or TileKind.ArchDoor)) continue;
                near[n] = true;
                queue.Enqueue((n, d + 1));
            }
        }
        return near;
    }

    /// <summary>
    /// How high above its level's floor to put someone down on a tile found by <see cref="FindArrival"/>: standing,
    /// on most levels; in the Poolrooms, wading in the shallows or afloat in the deep; in Motion, on the ground of the
    /// hills, which is <see cref="Tile.Height"/> above the valleys.
    /// </summary>
    public double ArrivalHeight(int x, int z)
    {
        Tile t = TileAt(x, z);
        const double stand = 1.05;
        return t.Level switch
        {
            Poolrooms => t.Depth == 0 ? stand : t.Depth == 1 ? stand - 1 : 0.2,
            Motion => t.Height + stand,
            7 => t.Height + stand, // (an island's rise, from layout version 5)
            RunLevel => RunArrivalHeight(t, stand),
            FunLevel => FunArrivalHeight(t, stand),
            TheEnd => EndArrivalHeight(t, stand),
            Hub => HubArrivalHeight(t, stand),
            Level974 => L974ArrivalHeight(t, stand),
            Level3999 => L3999ArrivalHeight(t, stand),
            Level188 => L188ArrivalHeight(t, stand),
            _ => stand,
        };
    }

    private static (int, int)? PickAny(List<int> candidates, int mx, int mz, ulong h)
    {
        if (candidates.Count == 0) return null;
        int index = candidates[(int)(Hashing.Mix(h) % (ulong)candidates.Count)];
        return (mx * MacroSize + index % MacroSize, mz * MacroSize + index / MacroSize);
    }

    // ================= Thresholds as features =================

    // Cells looked at lately on behalf of thresholds and entities (a flight of stairs or a lake bottom is asked about
    // many times): the 48 built last, built outside any lock and looked up without one. The arrays are never written to.
    private readonly PlanCache<Tile[]> featureCells;

    /// <summary>The layout tile at a block position.</summary>
    public Tile TileAt(int x, int z)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        return CellTiles(mx, mz)[TileIndex(x - mx * MacroSize, z - mz * MacroSize)];
    }

    /// <summary>A cell's tiles, from the small cache <see cref="TileAt"/> uses.</summary>
    private Tile[] CellTiles(int mx, int mz) => featureCells.Get(mx, mz);

    /// <summary>
    /// One position that stands for a whole threshold: a flight of stairs, both leaves of an elevator, every tile of
    /// a lake's bottom. It is the least (by x, then z) of the tiles joined to the given one that are also
    /// <paramref name="part"/> of it, so whichever tile of the threshold is asked about, the answer is the same.
    /// The search stops at <see cref="MaxFeatureTiles"/> as a guard against a part that matches a whole level; past
    /// that the answer would depend on the tile asked about, so the bound sits far above any real threshold (the
    /// largest the links harness finds, Level Fun's water overboard and Level 37's bottomless pits, are under 400 tiles).
    /// </summary>
    public (int X, int Z) FeatureOrigin(int x, int z, Func<Tile, bool> part)
    {
        if (!part(TileAt(x, z))) return (x, z);
        (int X, int Z) best = (x, z);
        var seen = new HashSet<(int, int)> { best };
        var queue = new Queue<(int, int)>();
        queue.Enqueue(best);
        while (queue.Count > 0 && seen.Count < MaxFeatureTiles)
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

    /// <summary>How many tiles <see cref="FeatureOrigin"/> will search (it was 4000; every real threshold is far smaller).</summary>
    private const int MaxFeatureTiles = 16384;

    /// <summary>How many tiles <see cref="StandingSpotNear"/> will look through before it gives up.</summary>
    private const int MaxStandingSearch = 20000;

    /// <summary>
    /// The nearest clear floor to a threshold that a person can be put down on without at once going through it
    /// again: reached by walking from the threshold, with nothing standing on it, no step, no drop, and nothing under
    /// it that leads elsewhere. The search goes outwards a step at a time, so the nearest such floor is found
    /// whatever the reach; the reach only decides how far it keeps looking. It is long by default because some
    /// thresholds are long (the asphalt at the end of a Level 37 dry corridor runs some seventy blocks, every tile of
    /// it a way into the Hub), and with nothing found a two-way threshold would silently become one-way.
    /// </summary>
    public (int X, int Z)? StandingSpotNear(int x, int z, int reach = 96)
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
            if (distance >= reach || seen.Count > MaxStandingSearch) continue;
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
