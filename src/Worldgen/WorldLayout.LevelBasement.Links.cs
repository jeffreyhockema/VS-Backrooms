using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

/// <summary>
/// The Basement's way in, in other levels (docs/design/experimental-levels/LINKS.md): "breaking through the floor of most
/// levels" (Fandom). Very rarely a cell of Level 0, 1, 2, 4 or 5 has a patch of cracked floor in it, five by five: hairline
/// cracks round the edge, and in its middle three by three the floor broken and sagging, that gives way under whoever steps
/// on it (one-way: a long fall into the Basement, under a crack in its ceiling; ThresholdNetwork.Basement.cs). Each tile
/// of the patch has its own <see cref="Unders"/> value (<see cref="Unders.BasementCrack"/> + 5 dz + dx from the patch's
/// north-west corner), so the generator knows which piece of the crack to draw there (WorldGenerator.Basement.Links.cs).
/// Only tiles of plain, free floor are taken, on this level's own salts: nothing else in the host moves. This file is the
/// level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Layout salts of the cracks: which cells hold one, and where in the cell it lies.</summary>
    private const ulong SaltBasementCrackCell = 0x2280, SaltBasementCrackSpot = 0x2281;

    /// <summary>
    /// The share of a host level's cells with a cracked patch in them: one in fifteen hundred in Levels 0 and 2 (Level 2's
    /// narrow tunnels leave fewer cells room for one), one in two thousand in Level 1, one in three thousand in the larger
    /// offices and hotel. That is one to eight in each level of an ordinary world, two or three on average, a walk of a
    /// kilometre or more from one to the next (the progression rule: a quarter as common as the ways of layout
    /// 11, which were a few hundred blocks apart).
    /// </summary>
    public static double BasementCrackChance(int level) => level switch
    {
        0 or 2 => 1 / 1500.0,
        1 => 1 / 2000.0,
        4 or 5 => 1 / 3000.0,
        _ => 0,
    };

    /// <summary>The levels whose floors give way into the Basement: "the floor of most levels" (Fandom), the ones with a floor of their own over a room.</summary>
    public static bool IsBasementCrackHost(int level) => level is 0 or 1 or 2 or 4 or 5;

    /// <summary>Whether a tile is a piece of a cracked patch in another level (the edge's hairline cracks too).</summary>
    public static bool IsBasementCrack(in Tile t) => t.Under is >= Unders.BasementCrack and <= Unders.BasementCrackEnd && IsBasementCrackHost(t.Level);

    /// <summary>Where a piece of a cracked patch lies from the patch's middle (each of -2 to 2).</summary>
    public static (int Dx, int Dz) BasementCrackOffset(in Tile t)
    {
        int k = t.Under - Unders.BasementCrack;
        return (k % 5 - 2, k / 5 - 2);
    }

    /// <summary>Whether a tile is in the middle three by three of a cracked patch: the floor that gives way.</summary>
    public static bool BasementCrackGives(in Tile t)
    {
        if (!IsBasementCrack(t)) return false;
        var (dx, dz) = BasementCrackOffset(t);
        return Math.Abs(dx) <= 1 && Math.Abs(dz) <= 1;
    }

    /// <summary>
    /// Whether a cell of a host level was picked to hold a cracked patch (it holds one if the patch fits). Never the spawn
    /// cell, nor in Level 0 a Red Room, the Manila Room or a party nobody came to.
    /// </summary>
    public bool IsBasementCrackCell(int mx, int mz)
    {
        double roll = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltBasementCrackCell));
        if (roll >= 1 / 1500.0) return false;
        int level = LevelAt(mx, mz);
        if (roll >= BasementCrackChance(level) || IsSpawnMacro(mx, mz)) return false;
        return level != 0 || !IsRedRoom(mx, mz) && !IsManilaMacro(mx, mz) && !IsFunPartyCell(mx, mz);
    }

    /// <summary>Whether a tile of a host level is plain free floor a crack can be laid in.</summary>
    private static bool BasementCrackFree(in Tile t, int level) =>
        t.Kind == TileKind.Floor && t.Variant == 0 && t.Under == 0 && !t.SupplyBox && !t.Sealed && t.Stair == 0 && t.Stack == 0 && t.Depth == 0
        // (Level 1's Height labels its floor; in Levels 1 and 4 a Zone marks a stairwell's flight or a stairs to nowhere's parts)
        && (level == 1 || t.Height == 0) && (level is not (1 or 4) || t.Zone == 0);

    /// <summary>
    /// A cracked patch in a cell of a host level, if the cell was picked for one, clear of the cell's edge: best where its
    /// whole five by five is free floor (in a room), else where its middle three by three is (across a wide hall), else where
    /// its middle tile and two more of the three by three round it are (across one of Level 2's narrow tunnels). Only the
    /// free floor of it is taken.
    /// </summary>
    partial void BasementEntrances(Builder b, int mx, int mz)
    {
        if (!IsBasementCrackHost(b.Level) || !IsBasementCrackCell(mx, mz)) return;
        int level = b.Level;
        bool Free(int x, int z) => BasementCrackFree(b.At(x, z), level);
        var whole = new List<(int, int)>();
        var middle = new List<(int, int)>();
        var across = new List<(int, int)>();
        for (int cz = 3; cz <= MacroSize - 4; cz++)
            for (int cx = 3; cx <= MacroSize - 4; cx++)
            {
                if (!Free(cx, cz)) continue;
                int free = 0, core = 0;
                for (int dz = -2; dz <= 2; dz++)
                    for (int dx = -2; dx <= 2; dx++)
                        if (Free(cx + dx, cz + dz))
                        {
                            free++;
                            if (Math.Abs(dx) <= 1 && Math.Abs(dz) <= 1) core++;
                        }
                if (free == 25) whole.Add((cx, cz));
                else if (core == 9) middle.Add((cx, cz));
                else if (core >= 3) across.Add((cx, cz));
            }
        List<(int, int)> from = whole.Count > 0 ? whole : middle.Count > 0 ? middle : across;
        if (from.Count == 0) return;
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementCrackSpot));
        var (mxc, mzc) = from[rng.Range(0, from.Count - 1)];
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
                if (Free(mxc + dx, mzc + dz)) b.At(mxc + dx, mzc + dz).Under = (ushort)(Unders.BasementCrack + 5 * (dz + 2) + dx + 2);
    }

    /// <summary>
    /// The middle of the cracked patch in a cell of a host level, or null if it has none (for the harness and the
    /// showcase: builds the cell).
    /// </summary>
    public (int X, int Z)? BasementCrackIn(int mx, int mz)
    {
        if (!IsBasementCrackCell(mx, mz)) return null;
        Tile[] tiles = CellTiles(mx, mz);
        for (int i = 0; i < tiles.Length; i++)
        {
            if (!IsBasementCrack(tiles[i]) || tiles[i].Under != Unders.BasementCrack + 12) continue;
            return (mx * MacroSize + i % MacroSize, mz * MacroSize + i / MacroSize);
        }
        return null;
    }

    /// <summary>
    /// The cracked patches nearest spawn in a host level, nearest first: the cells are walked out from spawn ring by ring
    /// (a hash a cell, so this is cheap) until <paramref name="count"/> are found or <paramref name="maxRing"/> is passed.
    /// </summary>
    public List<(int X, int Z)> BasementCracksNearSpawn(int level, int count, int maxRing = 400)
    {
        var found = new List<(int X, int Z)>();
        for (int ring = 0; ring <= maxRing && found.Count < count; ring++)
        {
            var thisRing = new List<(int X, int Z)>();
            for (int dz = -ring; dz <= ring; dz++)
                for (int dx = -ring; dx <= ring; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != ring) continue;
                    int mx = spawnMacroX + dx, mz = spawnMacroZ + dz;
                    if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltBasementCrackCell)) >= BasementCrackChance(level) || LevelAt(mx, mz) != level) continue;
                    if (BasementCrackIn(mx, mz) is { } c) thisRing.Add(c);
                }
            int sx = spawnMacroX * MacroSize + MacroSize / 2, sz = spawnMacroZ * MacroSize + MacroSize / 2;
            thisRing.Sort((a, c) => ((long)(a.X - sx) * (a.X - sx) + (long)(a.Z - sz) * (a.Z - sz)).CompareTo((long)(c.X - sx) * (c.X - sx) + (long)(c.Z - sz) * (c.Z - sz)));
            found.AddRange(thisRing);
        }
        if (found.Count > count) found.RemoveRange(count, found.Count - count);
        return found;
    }

    /// <summary>
    /// The showcase's spots for the way in (after the level's own, whose "crack-up" looks up the way out): the cracked patch
    /// nearest spawn in each host level, from a free tile three (to five) steps off its middle, looking down at it. (None stands at
    /// the top of a crack: standing there is climbing out.)
    /// </summary>
    public IEnumerable<Showcase.Spot> BasementLinkShowcaseSpots(WorldGeometry geometry)
    {
        foreach (int level in new[] { 0, 1, 2, 4, 5 })
        {
            if (BasementCracksNearSpawn(level, 1) is not { Count: > 0 } near) continue;
            var (cx, cz) = near[0];
            double feet = geometry.FloorFor(level) + 1;
            // (Three steps off, just clear of the patch, else four or five)
            Showcase.Spot? spot = null;
            for (int k = 3; k <= 5 && spot == null; k++)
                foreach (var (dx, dz) in ShowcaseDirs)
                {
                    int x = cx + k * dx, z = cz + k * dz;
                    Tile t = TileAt(x, z);
                    if (t.Level != level || t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stair != 0 || t.Under != 0) continue;
                    spot = new Showcase.Spot($"link-l{level}", x + 0.5, feet, z + 0.5, ShowcaseHeading(-dx, -dz), k == 3 ? -24 : -18);
                    break;
                }
            if (spot is { } found) yield return found;
        }
    }
}
