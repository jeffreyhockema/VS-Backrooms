using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Read-only questions the cheat menu's "Go to feature" finders (src/Cheats/FeatureFinder.cs) ask of plans the layout
/// otherwise keeps to itself. Queries only: nothing here is laid out, rolled or cached differently, so no world changes.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Whether a Level 3 cell is a Sanctum.</summary>
    public bool CheatIsL3Sanctum(int mx, int mz) => IsL3Sanctum(mx, mz);

    /// <summary>The Level 3 hall a cell is part of (1 a transformer hall, 2 an assembly hall, 0 none) and its north-west cell.</summary>
    public (int Kind, int X0, int Z0) CheatL3Hall(int mx, int mz) =>
        L3HallAt(mx, mz) is { } hall ? (hall.Kind == L3Kind.TransformerHall ? 1 : 2, hall.X0, hall.Z0) : (0, 0, 0);

    /// <summary>Whether a Level 1 cell is one that has a door to Level ! (if its wall allows one; see MarkRunEntrance).</summary>
    public bool CheatIsRunEntranceCellL1(int mx, int mz) =>
        RunEntrances && Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltRunEntranceL1)) < (Version >= 12 ? 1.0 / 1200 : 1.0 / 300);

    /// <summary>Whether a Level 5 cell is a dining hall.</summary>
    public bool CheatIsL5Dining(int mx, int mz) => LevelAt(mx, mz) == 5 && HotelZoneAt(mx, mz) == HotelZone.Dining;

    /// <summary>The middles of the Level 2 pump galleries (at crossings of mains) within <paramref name="reach"/> crossings of a position.</summary>
    public IEnumerable<(int X, int Z)> CheatL2Galleries(int gx, int gz, int reach)
    {
        const int span = L2Pitch * L2MainEvery;
        int mx0 = Hashing.FloorDiv(gx + span / 2, span), mz0 = Hashing.FloorDiv(gz + span / 2, span);
        for (int dj = -reach; dj <= reach; dj++)
            for (int di = -reach; di <= reach; di++)
            {
                if (!L2GalleryAt(mx0 + di, mz0 + dj)) continue;
                int cx = L2Line(0, (mx0 + di) * L2MainEvery) + 1, cz = L2Line(1, (mz0 + dj) * L2MainEvery) + 1;
                if (LevelAt(MacroOf(cx), MacroOf(cz)) == 2) yield return (cx, cz);
            }
    }

    /// <summary>Level 37's showpiece rooms of a plan block: their kind's name (as <c>PoolSpace</c> has it) and middle, in blocks.</summary>
    public IEnumerable<(string Kind, int X, int Z)> CheatPoolRooms(int bi, int bj)
    {
        foreach (PoolRoom r in PoolRooms(bi, bj))
            yield return (r.Kind.ToString(), PoolOriginX + bi * PoolBlock + (r.U0 + r.U1) / 2, PoolOriginZ + bj * PoolBlock + (r.V0 + r.V1) / 2);
    }

    /// <summary>The Level 37 plan block a position lies in.</summary>
    public (int Bi, int Bj) CheatPoolBlockOf(int gx, int gz) => PoolBlockOf(gx, gz);

    /// <summary>What stands on a Level 94 hill (as <c>HillTop</c> names it; "None" for nothing) and the hill's middle, in blocks.</summary>
    public (string Top, int X, int Z) CheatHillAt(int hi, int hj)
    {
        Hill hill = HillAt(hi, hj);
        return (hill.Radius == 0 ? "None" : hill.Top.ToString(), MotionOriginX + hill.X, MotionOriginZ + hill.Z);
    }

    /// <summary>Where Camp Amber's wanderer keeps in the Hub (by the Level 1 door), or null.</summary>
    public (int X, int Z)? CheatHubCampSite()
    {
        if (HubDoorOf(1) is not { } door) return null;
        var (fx, fz) = FacingStep(door.Facing);
        var (rx, rz) = RightOf(door.Facing);
        return StandingSpotNear(door.X + fx + rx * 8, door.Z + fz + rz * 8, 6);
    }
}
