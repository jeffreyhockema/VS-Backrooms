using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 8's spider nests, from layout version 9. The lore gives the level "a bit of a spider problem": whole stretches
/// of cave taken over by colonies of them, some bred to "extreme gigantism", aggressively territorial, highly venomous,
/// and coming to loud noise (Wikidot's Level 8, its Tip #7 "Creepy Crawlies", and the old Fandom page's nests of
/// "massive king and queen spiders"). A nest is a den (<see cref="DenKind.Nest"/>): a bubble <see cref="DenRadius"/>
/// blocks across its middle, as dangerous as the level's edge, whose dweller is the Giant Spider. It lies in the caves,
/// never on the 9th Road: its heart is at least <see cref="NestClearOfRoad"/> blocks from the road and outside the rich
/// deposits (whose hearts are solid). Unlike the other dens it lays nothing out on the tiles (it has no cache, bones or
/// chalk crosses: the tiles round it are rock); the generator strings its webs through the caves round its heart
/// (<see cref="L8NestNear"/>, WorldGenerator.Nests.cs).
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltNest = 0x5E57;

    /// <summary>How far from the 9th Road (in blocks, at its heart) a nest must be.</summary>
    private const int NestClearOfRoad = 22;

    /// <summary>
    /// From layout version 9, whether a cell of Level 8 that the den roll left empty is a spider nest: one cell in
    /// fourteen in the level's inner part, one in seven further out, where its heart is in the caves well off the road.
    /// </summary>
    private DenKind L8NestAt(int mx, int mz, double depth)
    {
        if (Version < 9) return DenKind.None;
        double chance = depth < 0.6 ? 0.07 : 0.14;
        if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltNest)) >= chance) return DenKind.None;
        int cx = mx * MacroSize + MacroSize / 2, cz = mz * MacroSize + MacroSize / 2;
        L8Plan plan = L8PlanAt(cx, cz);
        int i = L8Index(cx, cz);
        if (plan.Dist[i] < NestClearOfRoad || plan.Deposit[i] != 0 || plan.Flags[i] != 0) return DenKind.None;
        return DenKind.Nest;
    }

    /// <summary>
    /// How deep into a spider nest a column of Level 8 lies, from 1 at its heart to 0 at its rim and beyond (0 in every
    /// world before layout version 9, and outside Level 8).
    /// </summary>
    public double L8NestNear(int gx, int gz)
    {
        if (Version < 9 || LevelAt(MacroOf(gx), MacroOf(gz)) != 8) return 0;
        if (DenNear(gx, gz) is not { Kind: DenKind.Nest } nest) return 0;
        double d = Math.Sqrt((nest.X - gx) * (nest.X - gx) + (nest.Z - gz) * (nest.Z - gz));
        return Math.Clamp(1 - d / DenRadius, 0, 1);
    }
}
