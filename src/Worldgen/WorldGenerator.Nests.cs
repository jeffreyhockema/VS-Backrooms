using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 8's spider nests (from layout version 9; WorldLayout.Level8.Nests.cs): the caves round a nest's heart strung
/// with the game's own cobwebs, thick under the ceilings and across the walls, thinner over the floor, the thicker the
/// nearer the heart, with now and then what is left of something it caught lying in them. Cobwebs slow whoever walks
/// through them to a quarter of their pace (the Giant Spider is not slowed in its own webs) and burn.
/// </summary>
public sealed partial class WorldGenerator
{
    private const ulong SaltNestWeb = 0x5E58;

    /// <summary>A nest's web (or a dry carcass at its heart) in an open cave block, or -1.</summary>
    private int NestWeb(int gx, int y, int gz)
    {
        double nest = caveColumns.Get(gx, gz).Nest;
        if (nest <= 0 || webId == 0) return -1;
        bool ceiling = !IsCave(gx, y + 1, gz), floor = !IsCave(gx, y - 1, gz);
        bool wall = false;
        foreach ((int dx, int dz) in Neighbours4)
        {
            if (IsCave(gx + dx, y, gz + dz)) continue;
            wall = true;
            break;
        }
        // Anchored where a spider would string it; a sheet across open air only near the heart
        double chance = ceiling ? 0.55 : wall ? 0.3 : floor ? 0.1 : nest > 0.5 ? 0.04 : 0;
        chance *= Math.Min(1, 0.2 + 1.1 * nest);
        double roll = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltNestWeb + (ulong)(y & 255)));
        if (roll < chance) return webId;
        // What it caught, wrapped and left, on the floor near the heart
        if (floor && nest > 0.55 && roll > 0.993 && remainsId != 0) return remainsId;
        return -1;
    }
}
