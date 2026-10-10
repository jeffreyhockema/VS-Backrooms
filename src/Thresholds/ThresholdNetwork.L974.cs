using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 974's thresholds (kept as level 18). Kitty's House has none of its own: you are taken into it (Kitty's detour,
/// and the Hub's pink ribbon door, both landing in your own house: see ThresholdSystem.L974.cs), and you leave it asleep,
/// once Kitty has its gift, by <see cref="KittyWake"/>. This file is the level's own; see docs/new-levels/CONTRACT.md.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here.</summary>
    private const ulong SaltL974Threshold = 0x18C0;

    /// <summary>The message shown on waking from Kitty's House (and how the detour knows not to take anyone off it).</summary>
    public const string L974WakeMessage = "backrooms:l974-wake";

    private Passage L974Walked(int x, int z, in Tile tile, double rel) => null;

    private Passage L974Used(int x, int z, int level, string kind, ref string refusal) => null;

    /// <summary>Somewhere to arrive in the level for a key (beside a tile matching <paramref name="beside"/>, where one can be found).</summary>
    private System.Func<ulong, (int X, int Z, double Height)?> IntoL974(System.Func<Tile, bool> beside = null) => In(WorldLayout.Level974, beside);

    /// <summary>
    /// Waking up after giving Kitty its gift, from the house standing for <paramref name="house"/> (any one position in
    /// it): one-way ("taken"), to a safe place fixed for that house the first time anyone sleeps there, as the King's
    /// table is: the quiet heart of Level 4 (half the houses), a lit deck in the Poolrooms, or a food court of the
    /// Snackrooms (a quarter each).
    /// </summary>
    public Passage KittyWake((int X, int Z) house)
    {
        ulong key = KeyOf(house, SaltL974Threshold + 1);
        double r = Hashing.Unit(key);
        System.Func<ulong, (int X, int Z, double Height)?> find =
            r < 0.5 ? k => layout.FindArrival(4, k, cellFilter: (mx, mz) => layout.BlocksToNextLevel(mx * WorldLayout.MacroSize + 16, mz * WorldLayout.MacroSize + 16, 4) > 160)
                is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : null
            : r < 0.75 ? In(WorldLayout.Poolrooms)
            : InSnackrooms();
        return new Passage { Source = house, Key = key, Find = find, Message = L974WakeMessage };
    }
}
