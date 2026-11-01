namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of the experimental levels' ways in, in the other levels (docs/design/experimental-levels/LINKS.md). A tile
/// of a level 0 to 20 whose Under is in an experimental level's block (256 + 32k) is that level's to draw: this file hands
/// it to the level's own partial (<c>partial void L31EntranceBlock</c> and so on, in its WorldGenerator file).
/// </summary>
public sealed partial class WorldGenerator
{
    // Each level's own: set id to the block at this height of one of its entrance tiles (and fluid, if any), or leave
    // id at -1 for the host level to draw its own. Unimplemented ones compile away.
    partial void L73EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void BasementEntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void L52EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void L31EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void L120EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void L36EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void L15EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void L23EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void L14EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);
    partial void L47EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid);

    /// <summary>
    /// The block of an experimental level's entrance at this height (rel from the host level's floor), or -1 for the host
    /// level's own. The owner is the README's block the Under falls in: 256-287 Level 73, then the Basement, 52, 31, 120,
    /// 36, 15, 23, 14 (512-543) and 47 (544-575).
    /// </summary>
    internal int ExpEntranceBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        int id = -1;
        switch ((t.Under - 256) / 32)
        {
            case 0: L73EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 1: BasementEntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 2: L52EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 3: L31EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 4: L120EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 5: L36EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 6: L15EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 7: L23EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 8: L14EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
            case 9: L47EntranceBlock(t, gx, gz, rel, ref id, ref fluid); break;
        }
        return id;
    }
}
