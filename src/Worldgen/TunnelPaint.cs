namespace Backrooms.Worldgen;

/// <summary>
/// Which coat of paint Level 2's steel tunnel doors wear. The generator places the door blocks and the way-back
/// threshold system names the same doors, so both must reach the same answer for a place: the rule lives here once.
/// </summary>
public static class TunnelPaint
{
    /// <summary>The hash salt of the paint rule; part of the world's look, never change it.</summary>
    public const ulong Salt = 0x2B0D;

    /// <summary>The shades the doors come in; a door's paint index points into this list.</summary>
    public static readonly string[] Names = { "white", "grey", "cream" };

    /// <summary>
    /// The paint of the door at a place: an index into <see cref="Names"/>, or -1 for the plain, unpainted door
    /// (one place in four).
    /// </summary>
    public static int PaintOf(ulong seed, int x, int z)
    {
        int paint = (int)(Hashing.Hash(seed, x, z, Salt) % 4);
        return paint < Names.Length ? paint : -1;
    }
}
