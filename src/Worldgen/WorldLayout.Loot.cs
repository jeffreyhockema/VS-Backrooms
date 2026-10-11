using System;

namespace Backrooms.Worldgen;

/// <summary>
/// What is left to scavenge. Others came this way before the player: most of the supply boxes and crates they left
/// have been torn or prised open since, and only the food is gone from those. What is still sealed is worth the
/// search, and the tell is honest from a distance.
///
/// The deeper the level, the fewer wanderers have been through it, so less is picked over. Places nobody goes
/// (Red Rooms, Level 0's blackout zones, rooms behind locked doors) are picked over least or not at all.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltPickedOver = 0x7A11;
    private const ulong SaltStash = 0x7A12;

    /// <summary>The share of boxes and crates in a cell that have already been gone through.</summary>
    private double PickedOverShare(int level, int mx, int mz) => level switch
    {
        // (Layout version 3 gave Level 0 more food: see CurrentVersion)
        0 => ZoneAt(mx, mz) == ZoneKind.Blackout ? (Version >= 3 ? 0.35 : 0.4) : (Version >= 3 ? 0.55 : 0.65),
        1 => 0.8, // the Habitable Zone has the most crates, and the most people going through them
        <= 5 => 0.6,
        // The five kept as 14-18 (each level's own line)
        RunLevel => 0.4,
        FunLevel => 0.4,
        TheEnd => 0, // "these objects appear untouched"
        Hub => 0.4,
        Level974 => 0.4,
        Level3999 => 0.15, // this deep, hardly anyone has been through the stores
        Level188 => 0.3, // few come here, fewer leave

        _ => 0.4,
    };

    /// <summary>Whether a tile holds a crate (the stacked kind, in the levels that have them).</summary>
    private static bool IsCrate(in Tile t, int level) =>
        t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack > 0 && !t.SupplyBox && level is 1 or 2 or 3 or 8;

    /// <summary>Marks the boxes and crates of a cell that were picked over long ago. Runs after the cell's pockets are sealed.</summary>
    private void MarkPickedOver(Builder b, int mx, int mz)
    {
        // The first boxes a newcomer finds, and the places nobody dares go, are untouched
        if (b.IsSpawn || b.Level == 0 && (IsRedRoom(mx, mz) || IsManilaMacro(mx, mz))) return;
        if (b.Level == 6 && IsSnackrooms(mx, mz)) return;
        double share = PickedOverShare(b.Level, mx, mz);
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (!t.SupplyBox && !IsCrate(t, b.Level)) continue;
                if (BehindLockedDoor(b, lx, lz)) continue;
                if (Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltPickedOver)) < share) t.Looted = true;
            }
    }

    /// <summary>
    /// Whether a box stands in a space nobody can walk into (a locked room): it has open floor beside it, and all of
    /// that floor is sealed off. A box in the middle of a pile of crates, with no floor beside it, does not count.
    /// </summary>
    private static bool BehindLockedDoor(Builder b, int lx, int lz)
    {
        bool anyFloor = false;
        foreach ((int dx, int dz) in Steps)
        {
            int x = lx + dx, z = lz + dz;
            if (x < 0 || z < 0 || x >= MacroSize || z >= MacroSize) continue;
            ref Tile n = ref b.At(x, z);
            if (!IsWalkable(n)) continue;
            if (!n.Sealed) return false;
            anyFloor = true;
        }
        return anyFloor;
    }

    /// <summary>
    /// Level 0: what wanderers left, they left together. About one cell in six has a stash of two or three boxes in
    /// the corner of a room (one in nine before layout version 3); the blackout zones, where few go, have more. (Dens
    /// add their own caches on top.)
    /// </summary>
    private void PlaceStash(Builder b, int mx, int mz)
    {
        if (b.IsSpawn) return;
        ulong h = Hashing.Hash(seed, mx, mz, SaltStash);
        double chance = Version >= 3 ? (b.Zone == ZoneKind.Blackout ? 0.28 : 0.16) : (b.Zone == ZoneKind.Blackout ? 0.22 : 0.11);
        if (Hashing.Unit(h) >= chance) return;
        var rng = new Rng(Hashing.Mix(h));
        bool Open(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z));
        bool Solid(int x, int z) => x < 0 || z < 0 || x >= MacroSize || z >= MacroSize || b.At(x, z).IsWallLike;

        for (int attempt = 0; attempt < 120; attempt++)
        {
            int x = rng.Range(2, MacroSize - 3), z = rng.Range(2, MacroSize - 3);
            ref Tile corner = ref b.At(x, z);
            if (corner.Kind != TileKind.Floor || corner.Variant != 0 || corner.SupplyBox) continue;
            // An inside corner: wall on two sides at right angles
            int wx = Solid(x - 1, z) ? -1 : Solid(x + 1, z) ? 1 : 0, wz = Solid(x, z - 1) ? -1 : Solid(x, z + 1) ? 1 : 0;
            if (wx == 0 || wz == 0 || !SafeToBlock(Open, x, z)) continue;
            corner.SupplyBox = true;
            // One or two more along whichever wall runs on
            int more = rng.Range(1, 2);
            foreach ((int dx, int dz) in new[] { (-wx, 0), (0, -wz), (-2 * wx, 0), (0, -2 * wz) })
            {
                if (more == 0) break;
                int bx = x + dx, bz = z + dz;
                if (!Open(bx, bz) || b.At(bx, bz).Kind != TileKind.Floor || b.At(bx, bz).Variant != 0) continue;
                // Against the wall, and not cutting anything off
                bool againstWall = dx != 0 ? Solid(bx, z + wz) : Solid(x + wx, bz);
                if (!againstWall || !SafeToBlock(Open, bx, bz)) continue;
                b.At(bx, bz).SupplyBox = true;
                more--;
            }
            return;
        }
    }
}
