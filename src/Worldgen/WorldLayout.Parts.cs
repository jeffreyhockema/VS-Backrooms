using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Props as big as the real things, over several tiles (layout version 6): the camp tent, two tiles by two, the
/// sleeping bag, two long, and the long sofa, two across, in place of the one-tile tent, bedroll and sofa, which looked
/// like toys beside a person. Each
/// tile holds one part (<see cref="Tile.Stack"/>, row by row from the front-left corner) and the whole prop's
/// <see cref="Tile.Pier"/>; the generator draws a part per tile, and breaking any part breaks the whole thing.
/// </summary>
public sealed partial class WorldLayout
{
    private delegate ref Tile TileRef(int x, int z);

    /// <summary>How many tiles across and from front to back a prop takes: (1, 1) for all but the multi-tile ones.</summary>
    internal static (int W, int D) PartsOf(ushort variant) => variant switch
    {
        Props.CampTent => (2, 2),
        Props.SleepingBag => (1, 2),
        Props.LongSofa => (2, 1),
        _ => (1, 1),
    };

    /// <summary>The way a multi-tile prop's front faces: its Pier, but the sleeping bag's Pier points from its head (its front) to its foot.</summary>
    private static ArchPier PartsFacing(ushort variant, ArchPier pier) => variant == Props.SleepingBag ? Opposite(pier) : pier;

    /// <summary>
    /// The tile of part (<paramref name="i"/> across, from the left as you look out of its front; <paramref name="j"/>
    /// back from the front) of a prop whose front-left part is on (<paramref name="x"/>, <paramref name="z"/>) and whose
    /// front faces <paramref name="facing"/>. (The generator's models turn the same way: BlockBehaviorPartnered.)
    /// </summary>
    internal static (int X, int Z) PartTile(int x, int z, ArchPier facing, int i, int j) => facing switch
    {
        ArchPier.North => (x + i, z + j),
        ArchPier.East => (x - j, z + i),
        ArchPier.South => (x - i, z - j),
        _ => (x + j, z - i),
    };

    /// <summary>
    /// The tiles of the multi-tile prop a tile is part of (by its part and Pier), front-left first, or null if it is
    /// not part of one or any of it is missing (out of the grid, or not its part).
    /// </summary>
    private static List<(int X, int Z)> PartsAround(TileRef at, int size, int x, int z)
    {
        Tile t = at(x, z);
        var (w, d) = PartsOf(t.Variant);
        if (w * d == 1 || t.Stack >= w * d) return null;
        ArchPier facing = PartsFacing(t.Variant, t.Pier);
        var (sx, sz) = PartTile(0, 0, facing, t.Stack % w, t.Stack / w);
        var parts = new List<(int X, int Z)>();
        for (int n = 0; n < w * d; n++)
        {
            var (px, pz) = PartTile(x - sx, z - sz, facing, n % w, n / w);
            if (px < 0 || pz < 0 || px >= size || pz >= size) return null;
            Tile p = at(px, pz);
            if (p.Kind != TileKind.Floor || p.Variant != t.Variant || p.Stack != n || p.Pier != t.Pier) return null;
            parts.Add((px, pz));
        }
        return parts;
    }

    /// <summary>
    /// Puts a multi-tile prop down with its front-left part on (<paramref name="x"/>, <paramref name="z"/>) if every tile it
    /// takes is <paramref name="free"/> (asked first of all of them) and, unless it is walked over, taking them cuts
    /// none of the walkable floor of the grid in two. Returns whether it did.
    /// </summary>
    private static bool PutParts(TileRef at, int size, Func<int, int, bool> free, ushort prop, int x, int z, ArchPier pier)
    {
        int[] before = null;
        return PutParts(at, size, free, prop, x, z, pier, ref before);
    }

    /// <summary>
    /// <see cref="PutParts(TileRef, int, Func{int, int, bool}, ushort, int, int, ArchPier)"/> for a caller that tries several places on a grid that does not change between failed
    /// attempts: <paramref name="before"/> holds the floor's pieces, worked out on the first attempt that needs them and reused.
    /// </summary>
    private static bool PutParts(TileRef at, int size, Func<int, int, bool> free, ushort prop, int x, int z, ArchPier pier, ref int[] before)
    {
        var (w, d) = PartsOf(prop);
        ArchPier facing = PartsFacing(prop, pier);
        var tiles = new List<(int X, int Z)>();
        for (int n = 0; n < w * d; n++)
        {
            var (px, pz) = PartTile(x, z, facing, n % w, n / w);
            if (px < 0 || pz < 0 || px >= size || pz >= size || !free(px, pz)) return false;
            tiles.Add((px, pz));
        }
        if (!IsWalkThroughProp(prop) && CutsFloor(at, size, tiles, ref before)) return false;
        for (int n = 0; n < tiles.Count; n++)
        {
            ref Tile t = ref at(tiles[n].X, tiles[n].Z);
            t.Variant = prop;
            t.Stack = (byte)n;
            t.Pier = pier;
            // (As the cell's pockets are sealed: floor taken up by something you cannot walk through counts as sealed)
            if (!IsWalkThroughProp(prop)) t.Sealed = true;
        }
        return true;
    }

    /// <summary>Whether making these tiles unwalkable would leave any two pieces of walkable floor that are joined now (in this grid) apart.</summary>
    private static bool CutsFloor(TileRef at, int size, List<(int X, int Z)> blocked, ref int[] before)
    {
        var shut = new HashSet<int>();
        foreach (var (x, z) in blocked) shut.Add(z * size + x);
        before ??= FloorPieces(at, size, null);
        int[] after = FloorPieces(at, size, shut);
        // Every piece before must still be one piece (less the tiles taken)
        var seen = new Dictionary<int, int>();
        for (int i = 0; i < before.Length; i++)
        {
            if (before[i] < 0 || after[i] < 0) continue;
            if (seen.TryGetValue(before[i], out int was) ? was != after[i] : !seen.TryAdd(before[i], after[i])) return true;
        }
        return false;
    }

    /// <summary>The connected pieces of walkable floor in the grid, numbered per tile (-1 where it is not walkable, or <paramref name="shut"/>).</summary>
    private static int[] FloorPieces(TileRef at, int size, HashSet<int> shut)
    {
        var piece = new int[size * size];
        Array.Fill(piece, -1);
        var queue = new Queue<int>();
        int count = 0;
        for (int start = 0; start < piece.Length; start++)
        {
            if (piece[start] >= 0 || shut != null && shut.Contains(start) || !IsWalkable(at(start % size, start / size))) continue;
            piece[start] = count;
            queue.Enqueue(start);
            while (queue.Count > 0)
            {
                int i = queue.Dequeue();
                foreach (var (dx, dz) in Steps)
                {
                    int x = i % size + dx, z = i / size + dz, j = z * size + x;
                    if (x < 0 || z < 0 || x >= size || z >= size || piece[j] >= 0 || shut != null && shut.Contains(j) || !IsWalkable(at(x, z))) continue;
                    piece[j] = count;
                    queue.Enqueue(j);
                }
            }
            count++;
        }
        return piece;
    }

    /// <summary>
    /// From layout version 6 the one-tile tent, bedroll or sofa on (<paramref name="x"/>, <paramref name="z"/>) becomes the
    /// camp tent (its door the same way, standing forward from where the old one stood, or round it, or in the open a step
    /// or two off), the sleeping bag
    /// (its head where the bedroll lay, its foot toward the old one's Pier, or any other way) or the long sofa (along
    /// the same wall, to one side or the other), where the tiles it needs pass <paramref name="free"/> (asked with the new
    /// prop) and what cannot be walked over cuts no floor off. Where there is no room, a tent or a bedroll is left out (a
    /// toy-sized one is what this is for); a sofa stays as it was. <paramref name="forwardOnly"/>: only the first way (a
    /// tent against a wall, its back to it; a bedroll's foot out into the room).
    /// </summary>
    private static void Enlarge(TileRef at, int size, Func<ushort, int, int, bool> free, int x, int z, ulong h, bool forwardOnly)
    {
        ref Tile old = ref at(x, z);
        ushort prop = old.Variant switch { Props.Tent => Props.CampTent, Props.Bedroll => Props.SleepingBag, Props.Sofa => Props.LongSofa, _ => (ushort)0 };
        if (prop == 0) return;
        ArchPier pier = old.Pier;
        ushort was = old.Variant;
        bool wasSealed = old.Sealed;
        old.Variant = 0;
        old.Stack = 0;
        // (A tent's tile was sealed off with the cell's pockets, as all floor taken up is: open again if it is beside open floor)
        if (old.Sealed && !IsWalkThroughProp(prop))
            foreach (var (dx, dz) in Steps)
                if (x + dx >= 0 && z + dz >= 0 && x + dx < size && z + dz < size && at(x + dx, z + dz) is { Sealed: false } n && IsWalkable(n))
                    old.Sealed = false;
        bool Free(int fx, int fz) => free(prop, fx, fz);
        // (The grid is the same for every attempt below, up to the one that succeeds: its pieces are worked out once)
        int[] pieces = null;
        if (prop == Props.SleepingBag)
        {
            // The head where the bedroll lay, the foot toward its Pier, else (in the open) any other way
            var ways = new[] { pier, Turn(pier), Opposite(pier), Turn(Opposite(pier)) };
            for (int k = 0; k < (forwardOnly ? 1 : 4); k++)
                if (PutParts(at, size, Free, prop, x, z, ways[k == 0 ? 0 : 1 + (k - 1 + (int)(h % 3)) % 3], ref pieces)) return;
            return;
        }
        if (prop == Props.LongSofa)
        {
            // Where the sofa stood and the tile to its left or right, against the same wall
            for (int k = 0; k < 2; k++)
            {
                var (ox, oz) = PartTile(0, 0, pier, (k + (int)(h % 2)) % 2, 0);
                if (PutParts(at, size, Free, prop, x - ox, z - oz, pier, ref pieces)) return;
            }
            // (No room: the old one-tile sofa stays, rather than the room losing its sofa)
            old.Variant = was;
            old.Sealed = wasSealed;
            return;
        }
        // The tent: the old one's tile at the back of it (left or right), so it stands forward from where that one stood,
        // its door the same way; else (in the open) at the front, or failing that a step or so off, wherever it fits
        int[] order = (h >> 8) % 2 == 0 ? new[] { 2, 3, 0, 1 } : new[] { 3, 2, 1, 0 };
        for (int k = 0; k < (forwardOnly ? 2 : 4); k++)
        {
            var (ox, oz) = PartTile(0, 0, pier, order[k] % 2, order[k] / 2);
            if (PutParts(at, size, Free, prop, x - ox, z - oz, pier, ref pieces)) return;
        }
        if (forwardOnly) return;
        for (int k = 0; k < 16; k++)
        {
            // (Layout <= 10: the (int) cast comes before the modulo, so the start is negative for about half the hashes
            // and the walk then covers an off-pattern window; kept as it is for the saved worlds. The intended form is
            // (int)((h >> 12) % 16): a candidate for layout version 11)
            int n = (k + (int)(h >> 12) % 16) % 16;
            if (PutParts(at, size, Free, prop, x - 2 + n % 4, z - 2 + n / 4, pier, ref pieces)) return;
        }
    }

    /// <summary>
    /// From layout version 6, after everything else in a cell: the old one-tile tents, bedrolls and sofas laid out by the
    /// levels (Level 6's dead ends, Level 7's islands and shelters, Level 8's settlements, a lair; the hotel's corridors,
    /// lobbies and front halls, the Suburbs' living rooms, the city's and Level 94's) are made as big as the real things (<see cref="Enlarge"/>), on clear floor, never beside a door, a doorway or a lift, nor
    /// where it would cut the floor off; then any multi-tile prop that has lost a part (to a doorway kept clear, a fenced
    /// corner opened up, or the edge of the cell) is taken away whole.
    /// </summary>
    private void LayOutParts(Builder b, int mx, int mz)
    {
        int level = b.Level;
        bool Opening(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize
            && (b.At(x, z).Kind is TileKind.Door or TileKind.Doorway or TileKind.ArchDoor || b.At(x, z).Stair != 0);
        Tile origin = default;
        // (What was taken up before, so that what is freed can be opened again)
        var blocked = new bool[b.Tiles.Length];
        for (int i = 0; i < b.Tiles.Length; i++) blocked[i] = b.Tiles[i].Kind == TileKind.Floor && !IsWalkable(b.Tiles[i]);
        bool Free(ushort prop, int x, int z)
        {
            if (x < 0 || z < 0 || x >= MacroSize || z >= MacroSize) return false;
            Tile t = b.At(x, z);
            // (On Level 7's islands a boulder of their rock is cleared to make room: the islands are small and strewn with them)
            bool boulder = level == 7 && prop == Props.CampTent && t.Stack == 1;
            if (t is not { Kind: TileKind.Floor, Variant: 0, SupplyBox: false, Stair: 0, Under: 0, Detail: 0, Chalk: 0 }
                || t.Stack != 0 && !boulder || t.Sealed && !boulder || t.Zone != origin.Zone) return false;
            // Level 7's islands rise in steps (all of it on one), Level 8's tents stand clear of the foot of the dome's wall
            if (level == 7 && t.Height != origin.Height || level == 8 && t.Height <= 6) return false;
            return !Opening(x + 1, z) && !Opening(x - 1, z) && !Opening(x, z + 1) && !Opening(x, z - 1);
        }
        for (int z = 0; z < MacroSize; z++)
            for (int x = 0; x < MacroSize; x++)
            {
                if (b.At(x, z).Variant is not (Props.Tent or Props.Bedroll or Props.Sofa) || b.At(x, z).Kind != TileKind.Floor) continue;
                origin = b.At(x, z);
                Enlarge(b.At, MacroSize, Free, x, z, Hashing.Hash(seed, mx * MacroSize + x, mz * MacroSize + z, SaltParts), forwardOnly: false);
            }
        KeepPartsWhole(b.At, MacroSize);
        // Floor freed of a tent that had no room, or of one in part, is open again where it joins open floor (only that:
        // anything sealed off before stays as it was)
        for (bool more = true; more;)
        {
            more = false;
            for (int i = 0; i < b.Tiles.Length; i++)
            {
                ref Tile t = ref b.Tiles[i];
                if (!blocked[i] || !t.Sealed || t.Kind != TileKind.Floor || !IsWalkable(t)) continue;
                int x = i % MacroSize, z = i / MacroSize;
                foreach (var (dx, dz) in Steps)
                    if (x + dx >= 0 && z + dz >= 0 && x + dx < MacroSize && z + dz < MacroSize && b.At(x + dx, z + dz) is { Sealed: false } n && IsWalkable(n))
                    {
                        t.Sealed = false;
                        more = true;
                        break;
                    }
            }
        }
    }

    /// <summary>Takes away whole any multi-tile prop in the grid that has lost a part, so no half a tent is left standing.</summary>
    private static void KeepPartsWhole(TileRef at, int size)
    {
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
            {
                ref Tile t = ref at(x, z);
                var (w, d) = PartsOf(t.Variant);
                // (Only on the floor: a wall's Variant is its decoration, numbered on its own)
                if (w * d == 1 || t.Kind != TileKind.Floor || PartsAround(at, size, x, z) != null) continue;
                // (Its other parts are found the same way and go in their turn: none of them is whole either)
                t.Variant = 0;
                t.Stack = 0;
            }
    }

    private const ulong SaltParts = 0xB16A;
}
