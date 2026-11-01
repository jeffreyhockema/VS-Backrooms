namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of the Basement's way in, in other levels (WorldLayout.LevelBasement.Links.cs): a cracked patch of floor five
/// by five. The host's own floor stays; over it, on each tile, lies one piece of the crack (<c>basement-floorcrack</c>, a
/// flat decal on the floor, tools/gen_basement.py): one of two drawings of it, the right way round or turned half about
/// (by a hash of the patch's middle), so no two in a row look the same. Its middle three by three is the floor broken and
/// sagging, cracks running out from it across the edge. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private const ulong SaltBasementCrackLook = 0x2282;

    /// <summary>[drawing (a, b), row (dz + 2), column (dx + 2), turn (none, half)].</summary>
    private readonly int[,,,] basementCrackIds = new int[2, 5, 5, 2];

    /// <summary>The crack's block ids (from <see cref="InitBasement"/>).</summary>
    private void InitBasementLinks()
    {
        for (int p = 0; p < 2; p++)
            for (int r = 0; r < 5; r++)
                for (int c = 0; c < 5; c++)
                    for (int turn = 0; turn < 2; turn++)
                        basementCrackIds[p, r, c, turn] = Id($"basement-floorcrack-{(p == 0 ? "a" : "b")}-p{r}{c}-{(turn == 0 ? "n" : "s")}");
    }

    /// <summary>A piece of a cracked patch: on the floor (rel 1, the air over the host's floor block); the host draws the rest.</summary>
    partial void BasementEntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        if (rel != 1 || !WorldLayout.IsBasementCrack(t)) return;
        var (dx, dz) = WorldLayout.BasementCrackOffset(t);
        ulong h = Hashing.Hash(seed, gx - dx, gz - dz, SaltBasementCrackLook);
        int drawing = (int)(h & 1), turn = (int)((h >> 1) & 1);
        // (Turned half about, the drawing's piece that lands here is the one opposite, itself turned half about)
        int sx = turn == 0 ? dx : -dx, sz = turn == 0 ? dz : -dz;
        int piece = basementCrackIds[drawing, sz + 2, sx + 2, turn];
        if (piece != 0) id = piece;
    }
}
