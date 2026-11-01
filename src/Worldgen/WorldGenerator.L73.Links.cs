namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of Level 73's ways in and out (WorldLayout.Level73.Links.cs; this file is the level's own): the Gloom in Level 9
/// (black ground, and over its heart a black murk two or three blocks high), and the north door in the castle's curtain wall.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l73GloomGround, l73GloomAir, l73PosternBack;
    private readonly int[] l73Postern = new int[4];

    /// <summary>A salt of the level's own (0x2100-0x21BF) for how high the murk stands over each block of the Gloom's heart.</summary>
    private const ulong SaltL73GloomTop = 0x2143;

    private void InitL73Links()
    {
        l73GloomGround = Id("l73-gloom");
        l73GloomAir = Id("l73-gloomair");
        l73PosternBack = Id("l73-postern-back");
        string[] parts = { "wb", "eb", "wt", "et" };
        for (int p = 0; p < 4; p++) l73Postern[p] = Id("l73-postern-shut-" + parts[p]);
    }

    /// <summary>
    /// The Gloom, in Level 9 (ExpLinks hook): its ground black; over its heart the murk, two or three high; nothing growing or
    /// standing over its rim. Below the ground and above the murk, the street's or the yard's own (-1).
    /// </summary>
    partial void L73EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        if (t.Level != 9 || t.Under is not (Unders.L73Gloom or Unders.L73GloomRim) || rel < 0) return;
        if (rel == 0)
        {
            id = l73GloomGround;
            return;
        }
        int top = t.Under == Unders.L73Gloom ? 2 + (int)(Hashing.Hash(seed, gx, gz, SaltL73GloomTop) % 2) : 0;
        if (rel <= top) id = l73GloomAir;
        else if (rel <= 4) id = 0;
    }

    /// <summary>The north door in the curtain wall (castle-local u, v; c over the plateau's floor), shut, and the blacked course behind it; -1 elsewhere.</summary>
    private int L73PosternBlock(int u, int v, int c)
    {
        if (c < 1 || c > WorldLayout.L73PosternHeight) return -1;
        if (WorldLayout.L73PosternAt(u, v) is int leaf) return l73Postern[leaf + 2 * (c - 1)];
        return WorldLayout.L73PosternBack(u, v) ? l73PosternBack : -1;
    }
}
