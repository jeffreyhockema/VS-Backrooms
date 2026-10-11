using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Signs over doorways wider than one block. A block can only hold a sign centred on itself, so over a two-wide
/// doorway the sign is made of two blocks, one over each half of the doorway, each holding half of the sign out to
/// the seam between them: together they draw one sign centred over the doorway (the models are cut in
/// tools/detail_kit.py, <c>seam_halves</c>). Over a wider doorway the sign goes over its middle: on the middle block
/// of an odd run, in halves over the middle two of an even one, the rest of the doorway's head left plain.
///
/// <para>This is how worlds made from layout version 4 on are built. Before, every block over a signed doorway held a
/// whole sign of its own (two EXIT signs side by side over a pair of fire doors), and a store's sign hung over one of
/// its two doors; those worlds keep that, so their chunks generated later still match.</para>
/// </summary>
public sealed partial class WorldGenerator
{
    /// <summary>What a block over a signed doorway holds: no sign, a whole one, or one half of a sign over two blocks.</summary>
    private enum SignPart : byte { None, Single, Lo, Hi }

    /// <summary>How far along a wall to look for the ends of a run of doorways (the widest signed one is 6).</summary>
    private const int MaxSignRun = 8;

    /// <summary>Halves of the EXIT lintel: [material (concrete, white block, drywall), half (lo, hi), axis (we, ns)].</summary>
    private readonly int[,,] exitPairIds = new int[3, 2, 2];
    /// <summary>Level 5's STAFF ONLY plates: [wall (frieze, plaster), part (single, lo, hi), axis (we, ns)].</summary>
    private readonly int[,,] staffPlaqueIds = new int[2, 3, 2];
    /// <summary>A store's sign over a two-wide door: [decoration, half (left, right as seen from the street), facing].</summary>
    private readonly int[,,] storeSignPairIds = new int[Decor.Limit, 2, 4];

    private void InitSigns()
    {
        string[] materials = { "concrete", "whiteblock", "drywall" }, halves = { "lo", "hi" }, axes = { "we", "ns" };
        for (int m = 0; m < 3; m++)
            for (int h = 0; h < 2; h++)
                for (int a = 0; a < 2; a++)
                    exitPairIds[m, h, a] = Id($"exitlintelpair-{materials[m]}-{halves[h]}-{axes[a]}");
        string[] walls = { "frieze", "plaster" }, parts = { "single", "lo", "hi" };
        for (int w = 0; w < 2; w++)
            for (int p = 0; p < 3; p++)
                for (int a = 0; a < 2; a++)
                    staffPlaqueIds[w, p, a] = Id($"staffplaque-{walls[w]}-{parts[p]}-{axes[a]}");
        foreach (var (family, decor, rel, state) in DetailBlocks.Decorations)
        {
            if (family != "storefrontdeco" || rel != 3) continue;
            byte d = DecorFor(family, decor);
            if (d == 0) continue;
            for (int f = 0; f < 4; f++)
            {
                storeSignPairIds[d, 0, f] = Id($"storefrontsign-{state}-l-{Sides[f]}");
                storeSignPairIds[d, 1, f] = Id($"storefrontsign-{state}-r-{Sides[f]}");
            }
        }
    }

    /// <summary>What counts as one opening along a wall, for finding its middle.</summary>
    private enum RunOf : byte
    {
        /// <summary>Doorways carrying a sign (<see cref="Tile.ExitSign"/>) across the same wall.</summary>
        SignedDoorways,
        /// <summary>Any doorways.</summary>
        Doorways,
        /// <summary>A Level 3999 unit's way in: an opening in its shopfront, or the shutter closing it.</summary>
        Frontage,
    }

    /// <summary>
    /// How many blocks of the same opening lie before (toward the smaller coordinate) and after a block of it, along a
    /// wall running west-east (<paramref name="alongX"/>) or north-south.
    /// </summary>
    private void RunExtent(int gx, int gz, bool alongX, RunOf of, out int before, out int after)
    {
        int dx = alongX ? 1 : 0, dz = 1 - dx;
        before = after = 0;
        while (before < MaxSignRun && InRun(TileAt(gx - (before + 1) * dx, gz - (before + 1) * dz), alongX, of)) before++;
        while (after < MaxSignRun && InRun(TileAt(gx + (after + 1) * dx, gz + (after + 1) * dz), alongX, of)) after++;
    }

    private static bool InRun(in Tile n, bool alongX, RunOf of) => of switch
    {
        RunOf.SignedDoorways => n.Kind == TileKind.Doorway && n.ExitSign && SignAlongX(n) == alongX,
        RunOf.Doorways => n.Kind == TileKind.Doorway,
        _ => n.Kind == TileKind.Doorway && n.Pattern == WallPattern.L3999Shopfront || n.Pattern == WallPattern.L3999Shutter,
    };

    /// <summary>
    /// What part of its opening's one sign a block over the opening holds: a whole sign on the middle block of an odd
    /// run, a half on each of the middle two of an even one (Lo the one with the smaller coordinate), none elsewhere.
    /// </summary>
    private SignPart RunSignPart(int gx, int gz, bool alongX, RunOf of)
    {
        RunExtent(gx, gz, alongX, of, out int before, out int after);
        int n = before + after + 1;
        if (n % 2 == 1) return before == n / 2 ? SignPart.Single : SignPart.None;
        return before == n / 2 - 1 ? SignPart.Lo : before == n / 2 ? SignPart.Hi : SignPart.None;
    }

    /// <summary>Seen from in front of a sign facing this way, whether its left is toward the larger coordinate along the wall.</summary>
    private static bool LeftIsHigher(ArchPier facing) => facing is ArchPier.North or ArchPier.East;

    /// <summary>Whether a doorway's sign runs along a wall running west-east: its Pier says so (north or south: see OrientDoorways).</summary>
    private static bool SignAlongX(in Tile t) => t.Pier is ArchPier.North or ArchPier.South;

    /// <summary>
    /// The EXIT sign over a doorway (its faces look along the doorway), or 0 where the doorway's head is left plain:
    /// the sides of a doorway three or more wide, whose sign hangs over its middle.
    /// </summary>
    private int ExitLintel(in Tile t, int gx, int gz)
    {
        int material = t.Pattern switch
        {
            WallPattern.WhiteBlock => 1,
            WallPattern.Drywall or WallPattern.OfficeGlass => 2,
            _ => 0,
        };
        int axis = SignAlongX(t) ? 0 : 1;
        if (layout.Version < 4) return exitLintelIds[material, axis];
        return RunSignPart(gx, gz, axis == 0, RunOf.SignedDoorways) switch
        {
            SignPart.Single => exitLintelIds[material, axis],
            SignPart.Lo => exitPairIds[material, 0, axis],
            SignPart.Hi => exitPairIds[material, 1, axis],
            _ => 0,
        };
    }

    /// <summary>The STAFF ONLY sign over a doorway into Level 5's boiler halls, or 0 where the doorway's head is left plain.</summary>
    private int StaffSign(in Tile t, int gx, int gz)
    {
        if (layout.Version < 4) return staffSignId;
        int wall = t.Pattern == WallPattern.Plaster ? 1 : 0, axis = SignAlongX(t) ? 0 : 1;
        return RunSignPart(gx, gz, axis == 0, RunOf.SignedDoorways) switch
        {
            SignPart.Single => staffPlaqueIds[wall, 0, axis],
            SignPart.Lo => staffPlaqueIds[wall, 1, axis],
            SignPart.Hi => staffPlaqueIds[wall, 2, axis],
            _ => 0,
        };
    }

    /// <summary>
    /// A store's sign in the fascia over its doors (Level 11), facing the street, or 0. The layout puts the sign on
    /// one door of the middle pair when the doors are an even number; from layout version 4 on, both blocks of that
    /// pair hold half of a sign twice as wide, centred over the doors. Seen from the street, the left half is in the
    /// block with the larger coordinate when the sign faces north or east, the smaller when it faces south or west.
    /// </summary>
    private int StoreSign(in Tile t, int gx, int gz, ArchPier facing, int side)
    {
        if (layout.Version < 4 || t.Kind != TileKind.Doorway) return Sign(t, side);
        bool alongX = facing is ArchPier.North or ArchPier.South;
        SignPart part = RunSignPart(gx, gz, alongX, RunOf.Doorways);
        if (part is not (SignPart.Lo or SignPart.Hi)) return Sign(t, side);
        int dx = alongX ? 1 : 0, dz = 1 - dx, step = part == SignPart.Lo ? 1 : -1;
        int decor = t.Variant >= Decor.First ? t.Variant : TileAt(gx + step * dx, gz + step * dz) is { Variant: >= Decor.First } partner ? partner.Variant : 0;
        if (decor == 0 || decor >= Decor.Limit || storeSignPairIds[decor, 0, side] == 0) return Sign(t, side);
        return storeSignPairIds[decor, (part == SignPart.Hi) == LeftIsHigher(facing) ? 0 : 1, side];
    }

    /// <summary>
    /// A Level 3999 neon sign (its words in <see cref="Tile.Depth"/>) against the wall behind its tile, facing the way
    /// its Pier says. A unit's sign stands in front of the middle of its six-wide way in, which has no middle block:
    /// from layout version 4 on it is drawn half a block toward the true middle (signs anywhere else stay put).
    /// </summary>
    private int NeonSign(in Tile t, int gx, int gz, int facing)
    {
        int single = l3SignIds[t.Depth, facing];
        if (layout.Version < 4) return single;
        bool alongX = t.Pier is ArchPier.North or ArchPier.South;
        // The block of wall behind the sign
        int wx = gx + (t.Pier == ArchPier.East ? -1 : t.Pier == ArchPier.West ? 1 : 0), wz = gz + (t.Pier == ArchPier.South ? -1 : t.Pier == ArchPier.North ? 1 : 0);
        if (!InRun(TileAt(wx, wz), alongX, RunOf.Frontage)) return single;
        RunExtent(wx, wz, alongX, RunOf.Frontage, out int before, out int after);
        if ((before + after) % 2 == 0 || Math.Abs(after - before) != 1) return single;
        // The middle is half a block toward the larger coordinate when more of the way in lies after this block
        return l3SignShiftIds[t.Depth, (after > before) == LeftIsHigher(t.Pier) ? 0 : 1, facing];
    }
}
