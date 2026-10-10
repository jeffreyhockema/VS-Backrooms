using System;

namespace Backrooms.Worldgen;

/// <summary>What makes its home in a den.</summary>
public enum DenKind : byte
{
    None,
    /// <summary>A pack of Hounds, over the bones of what they caught.</summary>
    Pack,
    /// <summary>A Deathmoth hive: papery cocoons heaped in a room with few ways in.</summary>
    Hive,
    /// <summary>Somewhere a Smiler keeps to, in a place already dark.</summary>
    Dark,
    /// <summary>A Death Rat warren, gnawed bones everywhere.</summary>
    Warren,
    /// <summary>A Skin-Stealer's lair: someone's bedroll, and the remains of whoever it was.</summary>
    Lair,
}

/// <summary>
/// Dens: places where something lives, which change how a level is crossed. Each is a bubble about
/// <see cref="DenRadius"/> blocks across its middle, as dangerous as the edge of the level wherever the level it is
/// in, with a cache at its heart that nobody has dared take: two or three sealed boxes. It can be seen coming. Bones
/// on the floor, a hive in a corner, and on the walls round it the crosses in chalk that others left to say keep
/// out. Whether the cache is worth it is the player's call.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>How far from its heart a den's danger reaches.</summary>
    public const int DenRadius = 18;

    private const ulong SaltDen = 0xDE40;

    /// <summary>The den whose heart lies in a cell, if there is one.</summary>
    public DenKind DenAt(int mx, int mz)
    {
        int level = LevelAt(mx, mz);
        DenKind[] kinds = level switch
        {
            // The Lobby is empty but for the eyes in its blackouts
            0 => ZoneAt(mx, mz) == ZoneKind.Blackout && !IsRedRoom(mx, mz) ? new[] { DenKind.Dark } : null,
            1 => new[] { DenKind.Pack, DenKind.Warren, DenKind.Hive, DenKind.Lair },
            2 => new[] { DenKind.Warren, DenKind.Dark },
            3 => new[] { DenKind.Pack, DenKind.Lair },
            5 => HotelZoneAt(mx, mz) == HotelZone.Beverly ? null : new[] { DenKind.Hive, DenKind.Pack, DenKind.Lair },
            8 => new[] { DenKind.Warren, DenKind.Dark },
            9 => new[] { DenKind.Pack, DenKind.Warren, DenKind.Lair, DenKind.Hive },
            // The five kept as 14-18 (each level's own line): none yet
            RunLevel => null,
            FunLevel => null,
            TheEnd => null,
            Hub => null,
            Level974 => null,
            Level3999 => null,
            Level188 => null,
            _ => null,
        };
        if (kinds == null) return DenKind.None;
        if (level == 0 && (Math.Abs(mx - spawnMacroX) < 6 && Math.Abs(mz - spawnMacroZ) < 6 || IsManilaMacro(mx, mz))) return DenKind.None;
        if (level == 3 && IsSanctum(mx, mz)) return DenKind.None;

        ulong h = Hashing.Hash(seed, mx, mz, SaltDen);
        // Commoner further out, where the level gives way to the next; and Level 0's blackouts are where the eyes are
        double depth = LevelDepth(mx * MacroSize + MacroSize / 2, mz * MacroSize + MacroSize / 2, level);
        double chance = level == 0 ? 0.25 : depth < 0.6 ? 0.04 : 0.08;
        if (Hashing.Unit(h) >= chance) return DenKind.None;
        return kinds[(int)(Hashing.Mix(h) % (ulong)kinds.Length)];
    }

    /// <summary>The den (its kind and heart) a position lies within, if any.</summary>
    public (DenKind Kind, int X, int Z)? DenNear(int gx, int gz)
    {
        int mx0 = MacroOf(gx), mz0 = MacroOf(gz);
        for (int mz = mz0 - 1; mz <= mz0 + 1; mz++)
            for (int mx = mx0 - 1; mx <= mx0 + 1; mx++)
            {
                DenKind kind = DenAt(mx, mz);
                if (kind == DenKind.None) continue;
                int cx = mx * MacroSize + MacroSize / 2, cz = mz * MacroSize + MacroSize / 2;
                if ((cx - gx) * (cx - gx) + (cz - gz) * (cz - gz) <= DenRadius * DenRadius) return (kind, cx, cz);
            }
        return null;
    }

    /// <summary>Lays out a den in its cell: the cache at its heart, the bones or the hive, and the warnings on the walls.</summary>
    private void PlaceDen(Builder b, int mx, int mz)
    {
        DenKind kind = DenAt(mx, mz);
        if (kind == DenKind.None) return;
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltDen + 1));
        const int c = MacroSize / 2;
        bool Open(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z));
        // Clear floor, and never in front of a door, a doorway or a lift
        bool Opening(int x, int z) => b.At(x, z).Kind is TileKind.Door or TileKind.Doorway or TileKind.ArchDoor || b.At(x, z).Stair != 0;
        bool Free(int x, int z) => x >= 1 && z >= 1 && x < MacroSize - 1 && z < MacroSize - 1
            && b.At(x, z) is { Kind: TileKind.Floor, Variant: 0, Stack: 0, SupplyBox: false, Stair: 0, Sealed: false, Under: 0 }
            && !Opening(x + 1, z) && !Opening(x - 1, z) && !Opening(x, z + 1) && !Opening(x, z - 1);

        // The cache: what others left and never came back for, as near the heart as there is floor to put it
        int boxes = rng.Range(2, 3);
        for (int r = 0; r < 10 && boxes > 0; r++)
            for (int dz = -r; dz <= r && boxes > 0; dz++)
                for (int dx = -r; dx <= r && boxes > 0; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || !Free(c + dx, c + dz) || !SafeToBlock(Open, c + dx, c + dz)) continue;
                    ref Tile t = ref b.At(c + dx, c + dz);
                    t.SupplyBox = true;
                    t.Looted = false;
                    boxes--;
                }

        // What lives here leaves its mark on the floor
        int litter = kind switch { DenKind.Pack or DenKind.Warren => rng.Range(4, 7), DenKind.Lair or DenKind.Hive => rng.Range(2, 4), _ => rng.Range(1, 2) };
        for (int attempt = 0; attempt < 80 && litter > 0; attempt++)
        {
            int x = c + rng.Range(-10, 10), z = c + rng.Range(-10, 10);
            if (!Free(x, z) || !SafeToBlock(Open, x, z)) continue;
            ref Tile t = ref b.At(x, z);
            t.Variant = kind switch
            {
                DenKind.Hive => Props.MothHive,
                DenKind.Lair => litter == 1 ? Props.Bedroll : Props.Ribcage,
                DenKind.Pack => rng.Chance(0.25) ? Props.Ribcage : Props.BonePile,
                _ => Props.BonePile,
            };
            t.Pier = (ArchPier)rng.Range(0, 3);
            litter--;
        }

        // And on the walls round it, the crosses others drew to say keep out
        int crosses = rng.Range(2, 4);
        for (int attempt = 0; attempt < 200 && crosses > 0; attempt++)
        {
            int x = rng.Range(1, MacroSize - 2), z = rng.Range(1, MacroSize - 2);
            int d2 = (x - c) * (x - c) + (z - c) * (z - c);
            if (d2 < 8 * 8 || d2 > 15 * 15) continue;
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Sealed || t.Chalk != 0) continue;
            foreach ((int dx, int dz, ArchPier side) in new[] { (0, -1, ArchPier.North), (1, 0, ArchPier.East), (0, 1, ArchPier.South), (-1, 0, ArchPier.West) })
            {
                ref Tile n = ref b.At(x + dx, z + dz);
                if (n.Kind != TileKind.Wall || n.Variant != 0) continue;
                t.Chalk = ChalkBits.Make(side, 2);
                crosses--;
                break;
            }
        }
    }
}
