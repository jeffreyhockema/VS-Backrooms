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
    /// <summary>From layout version 9, in Level 8's caves: a Giant Spider's nest, webs strung through the rock (WorldLayout.Level8.Nests.cs).</summary>
    Nest,
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

    // What may den in each level, in the order the hash picks from (asked about for every cell built)
    private static readonly DenKind[] DensDark = { DenKind.Dark };
    private static readonly DenKind[] DensL1 = { DenKind.Pack, DenKind.Warren, DenKind.Hive, DenKind.Lair };
    private static readonly DenKind[] DensWarrenDark = { DenKind.Warren, DenKind.Dark };
    private static readonly DenKind[] DensL3 = { DenKind.Pack, DenKind.Lair };
    private static readonly DenKind[] DensL5 = { DenKind.Hive, DenKind.Pack, DenKind.Lair };
    private static readonly DenKind[] DensL9 = { DenKind.Pack, DenKind.Warren, DenKind.Lair, DenKind.Hive };

    /// <summary>The den whose heart lies in a cell, if there is one.</summary>
    public DenKind DenAt(int mx, int mz)
    {
        int level = LevelAt(mx, mz);
        DenKind[] kinds = level switch
        {
            // The Lobby is empty but for the eyes in its blackouts
            0 => ZoneAt(mx, mz) == ZoneKind.Blackout && !IsRedRoom(mx, mz) ? DensDark : null,
            1 => DensL1,
            2 => DensWarrenDark,
            3 => DensL3,
            5 => HotelZoneAt(mx, mz) == HotelZone.Beverly ? null : DensL5,
            8 => DensWarrenDark,
            9 => DensL9,
            // (The far places kept as 14-20 have no dens yet)
            _ => null,
        };
        if (kinds == null) return DenKind.None;
        if (level == 0 && (Math.Abs(mx - spawnMacroX) < 6 && Math.Abs(mz - spawnMacroZ) < 6 || IsManilaMacro(mx, mz))) return DenKind.None;
        if (level == 3 && IsSanctum(mx, mz)) return DenKind.None;

        ulong h = Hashing.Hash(seed, mx, mz, SaltDen);
        // Commoner further out, where the level gives way to the next; and Level 0's blackouts are where the eyes are
        double depth = LevelDepth(mx * MacroSize + MacroSize / 2, mz * MacroSize + MacroSize / 2, level);
        double chance = level == 0 ? 0.25 : depth < 0.6 ? 0.04 : 0.08;
        // (From layout version 9, a Level 8 cell with no den may be a spider nest)
        if (Hashing.Unit(h) >= chance) return level == 8 ? L8NestAt(mx, mz, depth) : DenKind.None;
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
        // (A spider nest lies in Level 8's rock caves, and lays nothing out on its tiles: the generator draws its webs)
        if (kind is DenKind.None or DenKind.Nest) return;
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
                    // (Layout version 10: never beside an arch of Level 0's arched areas, as the stash's boxes are not)
                    if (Version >= 10 && b.Level == 0 && NextToArch(b, c + dx, c + dz)) continue;
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
            foreach ((int dx, int dz, ArchPier side) in WallSides)
            {
                ref Tile n = ref b.At(x + dx, z + dz);
                if (n.Kind != TileKind.Wall || n.Variant != 0) continue;
                t.Chalk = ChalkBits.Make(side, 2);
                crosses--;
                break;
            }
        }

        // From layout version 5: a Warren in Level 2's tunnels, where a whole stretch may be dead, has candle stubs left
        // burning under its crosses and by its cache by whoever came before, so its warnings can be seen (a Smiler's
        // dark is left dark). Last, so nothing above moves
        if (Version >= 5 && kind == DenKind.Warren && LevelAt(mx, mz) == 2)
        {
            // (Never beside a box or crate: in a one-wide dead end it would shut the box in)
            bool Boxed(int x, int z) => b.At(x, z).SupplyBox || b.At(x, z).Stack > 0 && b.At(x, z).Variant == 0;
            bool Candle(int x, int z)
            {
                if (!Free(x, z) || !SafeToBlock(Open, x, z) || Boxed(x + 1, z) || Boxed(x - 1, z) || Boxed(x, z + 1) || Boxed(x, z - 1)) return false;
                b.At(x, z).Variant = Props.CandleStubs;
                return true;
            }
            for (int z = 1; z < MacroSize - 1; z++)
                for (int x = 1; x < MacroSize - 1; x++)
                    if (b.At(x, z).Chalk != 0 && ChalkBits.Symbol(b.At(x, z).Chalk) == 2) Candle(x, z);
            bool lit = false;
            for (int r = 1; r < 6 && !lit; r++)
                for (int dz = -r; dz <= r && !lit; dz++)
                    for (int dx = -r; dx <= r && !lit; dx++)
                        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) == r && Hashing.Mod(dx + dz * 3, 2) == 0) lit = Candle(c + dx, c + dz);
        }
    }
}
