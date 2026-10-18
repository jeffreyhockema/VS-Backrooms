using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// What a wanderer's note can tell you: where the nearest gate out of a level is, the nearest other way out (an
/// elevator, a stairwell, a pit), the nearest place where something was left untouched, or the nearest refuge.
/// Each search goes outward cell by cell and stops at the first ring that finds something. Every search takes an
/// optional <c>skip</c>: places (block x, z) not to name, so a reader's second note can point at the next place rather
/// than the one their first note already marked.
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
    private (int X, int Z)? NearestTile(int gx, int gz, int level, int radius, Func<Tile, bool> match, int min = 0, Func<int, int, bool> skip = null)
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
                if (skip != null && skip(x, z)) continue;
                bestD = d;
                best = (x, z);
                stopAfter = Math.Min(stopAfter, ring + 1);
            }
        }
        return best;
    }

    /// <summary>The nearest way into another level that is not a gate: an elevator, a stairwell that goes somewhere, a pit, a noclip wall, stairs down.</summary>
    public (int X, int Z)? NearestThreshold(int gx, int gz, int level, int radius, Func<int, int, bool> skip = null) =>
        NearestTile(gx, gz, level, radius, t => t.Kind == TileKind.Pit || t.Under == Unders.Noclip || t.Under is >= Unders.Descent1 and <= Unders.Descent3
            || t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator || t.Stair > 0 && t.Under == 0 && t.Level is 1 or 4 or 5, skip: skip);

    /// <summary>The nearest supply box or crate that nobody has opened yet (not counting any right beside you).</summary>
    public (int X, int Z)? NearestCache(int gx, int gz, int level, int radius, Func<int, int, bool> skip = null) =>
        NearestTile(gx, gz, level, radius, t => !t.Looted && (t.SupplyBox || IsCrate(t, t.Level)), min: 12, skip: skip);

    /// <summary>
    /// The nearest refuge: the Manila Room, a Sanctum, the Beverly Room, the Snackrooms, a wanderer who trades, the
    /// 9th Road. Decided cell by cell, so it is cheap to search far.
    /// </summary>
    public (int X, int Z)? NearestRefuge(int gx, int gz, int level, int radius, Func<int, int, bool> skip = null)
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
            if (refuge && !(skip != null && skip(cx, cz))) return (cx, cz);
            if (level is 1 or 4 or 8 or 11 && WandererSite(mx, mz) is { } site && !(skip != null && skip(site.X, site.Z))) return site;
        }
        return null;
    }

    // ================= What the notes' own marks point at (src/Notes/MarkResolver.cs) =================

    /// <summary>The nearest manhole down into Level 3's flooded tunnels (where the clay is).</summary>
    public (int X, int Z)? NearestManhole(int gx, int gz, int radius, Func<int, int, bool> skip = null) =>
        NearestTile(gx, gz, 3, radius, t => t.Under == 2 && t.Kind != TileKind.Wall, skip: skip);

    /// <summary>The buoy over the nearest sunken room in Level 7 (layout version 9), where its line goes down.</summary>
    public (int X, int Z)? NearestSunkenRoom(int gx, int gz, int radius, Func<int, int, bool> skip = null) =>
        Version < 9 ? null : NearestTile(gx, gz, 7, radius, t => t.Zone == L7ZoneLine, skip: skip);

    /// <summary>The nearest stretch of barn wall in Level 10 that isn't quite there (the way into the city).</summary>
    public (int X, int Z)? NearestBarnWall(int gx, int gz, int radius, Func<int, int, bool> skip = null) =>
        NearestTile(gx, gz, 10, radius, t => t.Under == Unders.Noclip, skip: skip);

    /// <summary>The heart of the nearest den in the same level. Decided cell by cell, so cheap to search far.</summary>
    public (int X, int Z)? NearestDen(int gx, int gz, int level, int radius, Func<int, int, bool> skip = null)
    {
        foreach ((int mx, int mz, int ring) in CellsOutward(MacroOf(gx), MacroOf(gz), radius / MacroSize + 1))
        {
            if (LevelAt(mx, mz) != level || DenAt(mx, mz) == DenKind.None) continue;
            int cx = mx * MacroSize + MacroSize / 2, cz = mz * MacroSize + MacroSize / 2;
            if (skip != null && skip(cx, cz)) continue;
            return (cx, cz);
        }
        return null;
    }

    /// <summary>The middle of the nearest block of Red Rooms in Level 0. Decided cell by cell.</summary>
    public (int X, int Z)? NearestRedRoom(int gx, int gz, int radius, Func<int, int, bool> skip = null)
    {
        foreach ((int mx, int mz, int ring) in CellsOutward(MacroOf(gx), MacroOf(gz), radius / MacroSize + 1))
        {
            if (LevelAt(mx, mz) != 0 || !IsRedRoom(mx, mz)) continue;
            int cx = mx * MacroSize + MacroSize / 2, cz = mz * MacroSize + MacroSize / 2;
            if (skip != null && skip(cx, cz)) continue;
            return (cx, cz);
        }
        return null;
    }

    /// <summary>
    /// The nearest way into the Hub from Level 1 (the grey door at a maintenance hall's end: the corridor in front of it)
    /// or Level 2 (a steel door with a chalk circle). Level 1's are found by the same hash as
    /// <see cref="MarkHubDoorInLevel1"/>, hall block by hall block, without building any cell.
    /// </summary>
    public (int X, int Z)? NearestHubEntrance(int gx, int gz, int level, int radius, Func<int, int, bool> skip = null)
    {
        if (level == 2) return NearestTile(gx, gz, 2, radius, t => t.Kind == TileKind.Door && t.Under == Unders.HubEntrance, skip: skip);
        if (level != 1) return null;
        (int X, int Z)? best = null;
        long bestD = (long)radius * radius;
        int bx0 = Hashing.FloorDiv(gx - radius - HallOffset - 2, HallGrid), bx1 = Hashing.FloorDiv(gx + radius - HallOffset - 2, HallGrid);
        int bz0 = Hashing.FloorDiv(gz - radius - HallOffset - 2, HallGrid), bz1 = Hashing.FloorDiv(gz + radius - HallOffset - 2, HallGrid);
        for (int bz = bz0; bz <= bz1; bz++)
            for (int bx = bx0; bx <= bx1; bx++)
            {
                if (Hashing.Unit(Hashing.Hash(seed, bx, bz, SaltHubLevel1)) >= 1 / 250.0) continue;
                int dx = bx * HallGrid + HallOffset + 2 + 6, dz = bz * HallGrid + HallOffset + 2;
                int dmx = MacroOf(dx), dmz = MacroOf(dz);
                if (LevelAt(dmx, dmz) != 1 || !IsLevel1Corridors(dmx, dmz) || RingFraction(dx, dz, 1) < 0.5) continue;
                if (skip != null && skip(dx, dz - 1)) continue;
                long d = (long)(dx - gx) * (dx - gx) + (long)(dz - 1 - gz) * (dz - 1 - gz);
                if (d < bestD) { bestD = d; best = (dx, dz - 1); }
            }
        return best;
    }

    /// <summary>The middle of the nearest room in Level Fun where a party is going on (the altered note's "party").</summary>
    public (int X, int Z)? NearestParty(int gx, int gz, int radius, Func<int, int, bool> skip = null)
    {
        (int X, int Z)? best = null;
        long bestD = long.MaxValue;
        foreach (FunRoom room in FunRoomsNear(gx, gz, radius))
        {
            if (room.Guests <= 0) continue;
            int cx = (room.X0 + room.X1) / 2, cz = (room.Z0 + room.Z1) / 2;
            if (skip != null && skip(cx, cz)) continue;
            long d = (long)(cx - gx) * (cx - gx) + (long)(cz - gz) * (cz - gz);
            if (d < bestD) { bestD = d; best = (cx, cz); }
        }
        return best;
    }

    // ================= Notes left lying where a story puts one (src/Notes/NoteSystem.Spots.cs) =================

    private const ulong SaltNoteSpot = 0x707F;

    /// <summary>Whether a cell of Level 5 is the Beverly Room.</summary>
    public bool IsBeverlyMacro(int mx, int mz) => LevelAt(mx, mz) == 5 && HotelZoneAt(mx, mz) == HotelZone.Beverly;

    /// <summary>
    /// The notes lying loose in a cell (cell-local tile, and the paper: door, way, cache, refuge or folded): beside the cache
    /// of half the dens (folded), on the floor of the Manila Room and of a Red Room block (folded), at one chalk-crossed dead
    /// end in eight in Level 0, in a Sanctum, the Beverly Room and a food court, beside where a runner arrives in
    /// Level !, by Kitty's kitchen table, and at the Hub's outposts and Level 3999's camps. Their own salt, so nothing else
    /// in the layout moves.
    /// </summary>
    public List<(int Lx, int Lz, string Kind)> NoteSpots(int mx, int mz)
    {
        var spots = new List<(int, int, string)>();
        int level = LevelAt(mx, mz);
        Tile[] tiles = null;
        Tile[] Tiles() => tiles ??= BuildMacro(mx, mz);
        void Near(int cx, int cz, string kind, int reach = 10)
        {
            if (FreeNear(Tiles(), cx, cz, reach) is { } at) spots.Add((at.X, at.Z, kind));
        }

        const int c = MacroSize / 2;
        // (Half the dens: the rest still have their caches, and a folded note may be in a box)
        if (DenAt(mx, mz) != DenKind.None && Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltNoteSpot + 1)) < 0.5) Near(c, c, "folded", 6);
        switch (level)
        {
            case 0:
                if (IsManilaMacro(mx, mz)) Near(c + 1, c + 1, "way", 4);
                if (IsRedRoom(mx, mz)) Near(c, c, "folded", 14);
                Tile[] t0 = Tiles();
                for (int i = 0; i < t0.Length; i++)
                {
                    if (t0[i].Chalk == 0 || ChalkBits.Symbol(t0[i].Chalk) != 2 || !FreeFloor(t0[i])) continue;
                    int lx = i % MacroSize, lz = i / MacroSize;
                    if (Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltNoteSpot)) < 1 / 8.0) spots.Add((lx, lz, "door"));
                }
                break;
            case 3 when IsSanctum(mx, mz): Near(c, c, "way", 12); break;
            case 5 when IsBeverlyMacro(mx, mz): Near(c + 2, c, "door", 8); break;
            case 6 when IsSnackrooms(mx, mz): Near(c, c, "way", 12); break;
            // Level 974: on the floor by the kitchen table (the house's first visit)
            case Level974:
            {
                var (tx, tz) = L974At(mx, mz, 6, 13);
                Near(tx - mx * MacroSize, tz - mz * MacroSize, "refuge", 3);
                break;
            }
            // The Hub's outposts and Level 3999's camps (the Megacolony): beside the camp
            case Hub or Level3999 when WandererSite(mx, mz) is { } camp:
                Near(camp.X - mx * MacroSize, camp.Z - mz * MacroSize, "way", 4);
                break;
            case RunLevel:
            {
                int lane = RunLaneAt(mx * MacroSize + c, mz * MacroSize + c);
                if (lane < 0) break;
                var (ax, az) = RunWorld(lane, RunPlan(lane).Arrival.X, RunPlan(lane).Arrival.Z);
                int alx = ax - mx * MacroSize, alz = az - mz * MacroSize;
                if (alx >= 0 && alz >= 0 && alx < MacroSize && alz < MacroSize) Near(alx, alz, "door", 3);
                break;
            }
        }
        return spots;
    }

    private static bool FreeFloor(in Tile t) =>
        t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox && t.Stair == 0 && t.Under == 0;

    /// <summary>The free floor tile nearest a cell-local spot (not right in a doorway), within the reach, or null.</summary>
    private static (int X, int Z)? FreeNear(Tile[] tiles, int cx, int cz, int reach)
    {
        for (int r = 0; r <= reach; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int x = cx + dx, z = cz + dz;
                    if (x < 1 || z < 1 || x >= MacroSize - 1 || z >= MacroSize - 1) continue;
                    if (!FreeFloor(tiles[TileIndex(x, z)])) continue;
                    bool doorway = false;
                    foreach ((int ox, int oz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                        if (tiles[TileIndex(x + ox, z + oz)].Kind is TileKind.Door or TileKind.Doorway or TileKind.ArchDoor) doorway = true;
                    if (!doorway) return (x, z);
                }
        return null;
    }
}
