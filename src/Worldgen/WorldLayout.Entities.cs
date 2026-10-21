using System;

namespace Backrooms.Worldgen;

/// <summary>
/// What the entities need to know about the layout: how deep into its level a place lies, how near the edge into the
/// next level it is, whether a threshold is close by, and which places nothing hostile ever comes.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>
    /// How far through its level a block lies, from 0 where the level begins to 1 at the edge into the next. Level 0
    /// is measured out from spawn. Level 10's fields go on for ever and the city stands apart, so both are 0.5.
    /// </summary>
    public double LevelDepth(int gx, int gz, int level)
    {
        if (level >= RingWidths.Length) return 0.5;
        // (Measured where the level itself is measured, the cell's corner, so the two always agree)
        int mx = MacroOf(gx), mz = MacroOf(gz);
        double angle = Math.Atan2(mz - spawnMacroZ, mx - spawnMacroX);
        var (inner, outer) = RingEdges(level, angle);
        return Math.Clamp((RingDistance(mx, mz) - inner) / (outer - inner), 0, 1);
    }

    /// <summary>The direction (a unit vector) leading away from spawn, which is the way to the next level.</summary>
    public (double X, double Z) Outward(int gx, int gz)
    {
        double dx = gx / (double)MacroSize - spawnMacroX - 0.5, dz = gz / (double)MacroSize - spawnMacroZ - 0.5;
        double length = Math.Sqrt(dx * dx + dz * dz);
        return length < 1e-6 ? (1, 0) : (dx / length, dz / length);
    }

    /// <summary>Roughly how many blocks it is from here to the edge into the next level (int.MaxValue where there is none).</summary>
    public int BlocksToNextLevel(int gx, int gz, int level)
    {
        if (level >= RingWidths.Length) return int.MaxValue;
        int mx = MacroOf(gx), mz = MacroOf(gz);
        double angle = Math.Atan2(mz - spawnMacroZ, mx - spawnMacroX);
        return (int)Math.Max(0, (OuterEdge(level, angle) - RingDistance(mx, mz)) * MacroSize);
    }

    /// <summary>
    /// The places that nothing hostile enters: the Manila Room, Level 3's Sanctums (the angel watches over them),
    /// Level 5's Beverly Room, the Snackrooms, and the lamplit 9th Road with its camps.
    /// </summary>
    public bool IsSanctuary(int gx, int gz, int level)
    {
        int mx = MacroOf(gx), mz = MacroOf(gz);
        return level switch
        {
            0 => IsManilaMacro(mx, mz),
            3 => IsSanctum(mx, mz),
            5 => HotelZoneAt(mx, mz) == HotelZone.Beverly,
            6 => IsSnackrooms(mx, mz),
            8 => NinthRoadDistance(gx, gz) <= 6 || IsCampClearing(gx, gz),
            // The Poolrooms: nothing has ever been met there, but in the dark of the Reservoir
            Poolrooms => !IsReservoirAt(gx, gz),
            // The far places kept as 14-20 (each level's own line)
            RunLevel => false,
            FunLevel => false,
            TheEnd => TileAt(gx, gz) is { Zone: 1 } or { Zone: 5, Detail: (byte)EndFake.Home }, // the central hall; the Junkies' Home
            Hub => true, // the Hub knows the intent of all who enter: nothing hostile is ever found in it
            Level974 => true, // Kitty's House: nothing that harms anyone ever comes
            Level3999 => !L3999DarkAt(gx, gz), // the Neon Paradise is safe; its Blackout (3999.1) is not
            Level188 => false,
            _ => false,
        };
    }

    /// <summary>Whether a Level 3 cell is a Sanctum.</summary>
    public bool IsSanctum(int mx, int mz) => IsL3Sanctum(mx, mz);

    /// <summary>Roughly how many blocks it is from a Level 8 position to the nearest stretch of the 9th Road.</summary>
    public int NinthRoadDistance(int gx, int gz)
    {
        // (from layout version 9, from the cell's road plan: the road and its settlements, up to 255)
        if (Version >= 9) return L8PlanAt(gx, gz).Dist[L8Index(gx, gz)];
        if (IsNinthRoad(gx, gz)) return 0;
        int ox = RoadOffsetX(gx, gz), oz = RoadOffsetZ(gx, gz);
        var (kz, kx) = RoadLines(gx, gz);
        // The road band is offsets 0 to 2 of each grid line: the nearer of the roads either side, where it is there
        int far = RoadGrid;
        int best = far;
        if (L8Stretch(1, kz, kx)) best = Math.Min(best, ox - 2);
        if (L8Stretch(1, kz + 1, kx)) best = Math.Min(best, RoadGrid - ox);
        if (L8Stretch(0, kx, kz)) best = Math.Min(best, oz - 2);
        if (L8Stretch(0, kx + 1, kz)) best = Math.Min(best, RoadGrid - oz);
        return Math.Max(0, best);
    }

    /// <summary>The kinds of place in a level that are worse than the level around them.</summary>
    public enum DarkPlace { None, Bad, Worst }

    /// <summary>
    /// The places entities are drawn to whatever the depth: Level 0's blackout zones (and, worst of all, its Red
    /// Rooms), Level 1's corridor sectors, Level 5's boiler halls, and Level 8 away from the road.
    /// </summary>
    public DarkPlace DarkPlaceAt(int gx, int gz, int level)
    {
        int mx = MacroOf(gx), mz = MacroOf(gz);
        switch (level)
        {
            case 0:
                if (IsRedRoom(mx, mz)) return DarkPlace.Worst;
                return ZoneAt(mx, mz) == ZoneKind.Blackout ? DarkPlace.Bad : DarkPlace.None;
            case 1:
                return IsLevel1Corridors(mx, mz) ? DarkPlace.Bad : DarkPlace.None;
            case 5:
                return HotelZoneAt(mx, mz) == HotelZone.Boiler ? DarkPlace.Bad : DarkPlace.None;
            case 8:
                // (Roads run on a 48-block grid, so where the roads either side are there nowhere is more than 23 from one,
                // and the far stretch between them is the worst; where the lattice has a gap it counts as the full 48. From
                // layout version 9 the roads lie hundreds of blocks apart, and most of the caves are the worst)
                int road = NinthRoadDistance(gx, gz);
                return road > 18 ? DarkPlace.Worst : road > 12 ? DarkPlace.Bad : DarkPlace.None;
            default:
                return DarkPlace.None;
        }
    }

    /// <summary>
    /// Whether a way into another level lies near a position: a pit, a noclip wall or Level 6's stairs down within
    /// <paramref name="rareRadius"/>, or an elevator or a flight of stairs that goes somewhere else within
    /// <paramref name="commonRadius"/> (Levels 3 to 5 have so many of those that a wider reach would cover half the
    /// level). Every tile is looked at: an elevator door or a stair is often one tile deep.
    /// </summary>
    public bool NearThreshold(int gx, int gz, int rareRadius = 24, int commonRadius = 10)
    {
        int radius = Math.Max(rareRadius, commonRadius);
        // Cell by cell, straight from the cell's tiles, which is far cheaper than a lookup per tile
        for (int mz = MacroOf(gz - radius); mz <= MacroOf(gz + radius); mz++)
        {
            for (int mx = MacroOf(gx - radius); mx <= MacroOf(gx + radius); mx++)
            {
                Tile[] tiles = CellTiles(mx, mz);
                for (int lz = 0; lz < MacroSize; lz++)
                {
                    int dz = mz * MacroSize + lz - gz;
                    if (Math.Abs(dz) > radius) continue;
                    for (int lx = 0; lx < MacroSize; lx++)
                    {
                        int dx = mx * MacroSize + lx - gx, d2 = dx * dx + dz * dz;
                        if (d2 > radius * radius) continue;
                        ref Tile t = ref tiles[TileIndex(lx, lz)];
                        bool rare = t.Kind == TileKind.Pit || t.Under == Unders.Noclip || t.Under is >= Unders.Descent1 and <= Unders.Descent3;
                        bool common = t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator || t.Stair > 0 && t.Under == 0 && t.Level is 1 or 4 or 5;
                        if (rare && d2 <= rareRadius * rareRadius || common && d2 <= commonRadius * commonRadius) return true;
                    }
                }
            }
        }
        return false;
    }

    private const ulong SaltWanderer = 0xEA7E;

    /// <summary>Wanderers are spread out by district: at most one in each square of this many cells a side.</summary>
    private const int WandererDistrict = 8;

    /// <summary>
    /// Where a wanderer who trades keeps to in a cell, if one does: now and then in Level 1 (the Habitable Zone's
    /// camps), Level 4 (the outposts of those who rest there), on Level 8's 9th Road, and in the city. Each district
    /// of 8 by 8 cells (256 blocks a side) has one candidate cell, kept off its edges so no two wanderers are near
    /// neighbours, and only some districts have a wanderer at all: about one every kilometre or two of travel.
    /// Never in a sealed room or a sanctuary.
    /// </summary>
    public (int X, int Z)? WandererSite(int mx, int mz)
    {
        // The End: the Junkies, in its Home fake realities (WorldLayout.LevelEnd.cs)
        if (LevelAt(mx, mz) == TheEnd) return EndWandererSite(mx, mz);
        // The Hub's outposts: the M.E.G.'s by the Level 11 door, Camp Amber's by the Level 1 door
        if (LevelAt(mx, mz) == Hub) return HubWandererSite(mx, mz);
        // Level 3999: a camp in one lobby in four, the Megacolony (WorldLayout.Level3999.cs)
        if (LevelAt(mx, mz) == Level3999) return L3999WandererSite(mx, mz);
        int level = LevelAt(mx, mz);
        if (!HasWandererSite(mx, mz, level)) return null;
        int cx = mx * MacroSize + MacroSize / 2, cz = mz * MacroSize + MacroSize / 2;
        // From layout version 5 a Level 4 wanderer keeps to the middle of the camp laid out round them (PitchL4Camp)
        if (level == 4 && Version >= 5)
        {
            Tile[] tiles = CellTiles(mx, mz);
            for (int i = 0; i < tiles.Length; i++)
                if (tiles[i].Detail == L4CampSite) return (mx * MacroSize + i % MacroSize, mz * MacroSize + i / MacroSize);
        }
        // (From layout version 9 Level 8's road is rare, so its wanderers look further for it: to the cell's edges and a
        // little beyond)
        int reach = level == 8 && Version >= 9 ? 40 : 12;
        for (int r = 0; r <= reach; r++)
        {
            for (int dz = -r; dz <= r; dz++)
            {
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int x = cx + dx, z = cz + dz;
                    bool ok = level == 8 ? IsNinthRoad(x, z) : IsEntitySpot(x, z) && TileAt(x, z).Variant == 0;
                    if (ok && (level == 8 || !IsSanctuary(x, z, level))) return (x, z);
                }
            }
        }
        return null;
    }

    /// <summary>
    /// Whether a cell of Levels 1, 4, 8 or 11 is its district's one candidate for a wanderer's site, and has one (from
    /// hashes alone, so a cell can ask it of itself while it is being laid out).
    /// </summary>
    private bool HasWandererSite(int mx, int mz, int level)
    {
        int dx0 = Hashing.FloorDiv(mx, WandererDistrict), dz0 = Hashing.FloorDiv(mz, WandererDistrict);
        ulong h = Hashing.Hash(seed, dx0, dz0, SaltWanderer);
        // The district's one candidate, 1 to 6 cells in from its corner
        int cmx = dx0 * WandererDistrict + 1 + (int)(Hashing.Mix(h) % 6), cmz = dz0 * WandererDistrict + 1 + (int)(Hashing.Mix(h + 1) % 6);
        if (mx != cmx || mz != cmz) return false;
        double chance = level switch { 1 => 0.3, 4 => 0.45, 8 => 0.5, 11 => 0.25, _ => 0 };
        return chance > 0 && Hashing.Unit(Hashing.Mix(h + 2)) < chance;
    }

    /// <summary>Whether a tile is somewhere an entity could be put down to stand (open floor, nothing on it, no drop).</summary>
    public bool IsEntitySpot(int gx, int gz) => IsEntitySpot(TileAt(gx, gz));

    private static bool IsEntitySpot(in Tile t)
    {
        if (t.Sealed || t.SupplyBox || t.Stair != 0) return false;
        if (t.Kind == TileKind.Doorway || t.Kind == TileKind.ArchDoor) return true;
        return t.Kind == TileKind.Floor && IsWalkThroughProp(t.Variant) && t.Stack == 0
            && (t.Under is 0 or Unders.LakeRim or Unders.Subway or Unders.Station || t.Level == 3 && t.Under == 1);
    }
}
