namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of Level 47's way in, in Level 10 (WorldLayout.Level47.Links.cs): an ancient dead tree in the fields, grey and
/// mossed at the foot, broken off at the top, its bare limbs out over the hedges and its roots over the ground round it, a
/// hollow inside it with a mouth three high, its floor leaf litter. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    partial void L47EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        if (t.Level != 10 || t.Under is not (Unders.L47Tree10Bark or Unders.L47Tree10Hollow or Unders.L47Tree10Foot)) return;
        switch (layout.L47Tree10Block(gx, gz, rel))
        {
            case 1: id = l47Kind[WorldLayout.L47BarkDead]; return;
            case 2: id = l47MossBark[WorldLayout.L47BarkDead]; return;
            case 3: id = l47Litter; return;
            case 4: id = 0; return;
        }
        // (Inside the hollow over its mouth, the dark goes on up the trunk: nothing of the host's grows there)
        if (t.Under == Unders.L47Tree10Hollow && rel >= 1) id = 0;
    }
}
