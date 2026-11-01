namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of Level 52's ways in, in other levels (WorldLayout.Level52.Links.cs): a steel door with a push bar and wired
/// glass (<c>l52-door</c>, used to go through), two of them under a HIGH SCHOOL sign on a city high school's front
/// (<c>l52-schoolsign</c>, four blocks across) and one under a green EMERGENCY EXIT sign in a wall of Level 4
/// (<c>l52-exitsign</c>). The host draws everything else on those tiles.
/// </summary>
public sealed partial class WorldGenerator
{
    private readonly int[] l52Door = new int[2], l52ExitSign = new int[4];
    private readonly int[,] l52SchoolSign = new int[4, 4];

    /// <summary>The ways in's block ids (from <see cref="InitL52"/>).</summary>
    private void InitL52Links()
    {
        l52Door[0] = L52Block("l52-door-lower", metalDoorLowerId);
        l52Door[1] = L52Block("l52-door-upper", l52Door[0]);
        for (int f = 0; f < 4; f++)
        {
            l52ExitSign[f] = L52Block("l52-exitsign-" + Sides[f], concreteId);
            for (int p = 0; p < 4; p++) l52SchoolSign[p, f] = L52Block($"l52-schoolsign-{p}-{Sides[f]}", concreteId);
        }
    }

    partial void L52EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        int facing = Facing(t.Pier), part = t.Variant & 3;
        switch (t.Under)
        {
            case Unders.L52SchoolDoor when t.Level == 11:
                if (rel is 1 or 2) id = l52Door[rel - 1];
                else if (rel == 3) id = l52SchoolSign[part, facing];
                break;
            case Unders.L52SchoolSign when t.Level == 11:
                if (rel == 3) id = l52SchoolSign[part, facing];
                break;
            case Unders.L52ExitDoor when t.Level == 4:
                if (rel is 1 or 2) id = l52Door[rel - 1];
                else if (rel == 3) id = l52ExitSign[facing];
                break;
        }
    }
}
