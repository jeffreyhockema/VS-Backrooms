using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Needs.Beds;

/// <summary>
/// Where a sleeper stands when they get up from one of the mod's beds. Vanilla's rule (<c>BlockEntityBed.DidUnmount</c>) walks
/// one and two blocks from the head along the block's side code, which is the way head-to-foot only for a vanilla bed; the mod's
/// "opposite" beds have it pointing through the headboard, so the sleeper was put on the far side of the wall. This rule only
/// tries the blocks next to the bed's own blocks (beside each half, then past the foot, and for a one-block bed every side but
/// the head's), each at the bed's floor, and else puts the sleeper on the bed.
/// Pure: reads the world and the collision tester, changes nothing, so the headless test and the entity share it.
/// </summary>
public static class BedStand
{
    /// <summary>A player's selection box, for the tests that have no player.</summary>
    public static readonly Cuboidf PlayerBox = new(-0.3f, 0f, -0.3f, 0.3f, 1.85f, 0.3f);

    /// <summary>The way the headboard faces: away from the foot, or for a one-block bed the side code.</summary>
    public static BlockFacing HeadDir(BlockBackroomsBed bed) => bed.FootDir?.Opposite ?? bed.Side;

    /// <summary>The blocks to try, in order. Never on the head side of a two-block bed.</summary>
    public static List<BlockPos> Candidates(BlockBackroomsBed bed, BlockPos head)
    {
        var list = new List<BlockPos>();
        BlockFacing foot = bed.FootDir;
        if (foot != null)
        {
            BlockPos footPos = head.AddCopy(foot);
            foreach (BlockFacing side in new[] { foot.GetCW(), foot.GetCCW() })
            {
                list.Add(footPos.AddCopy(side));
                list.Add(head.AddCopy(side));
            }
            list.Add(footPos.AddCopy(foot));
            return list;
        }
        // (A one-block bed: the foot end first, then the long sides; the head side is the wall)
        BlockFacing lie = bed.LieDir, headDir = HeadDir(bed);
        list.Add(head.AddCopy(lie));
        foreach (BlockFacing f in BlockFacing.HORIZONTALS)
            if (f != lie && f != headDir) list.Add(head.AddCopy(f));
        return list;
    }

    /// <summary>The first candidate a sleeper's box fits in with something under it, or <paramref name="onTop"/> when none does.</summary>
    public static Vec3d Choose(IWorldAccessor world, BlockBackroomsBed bed, BlockPos head, Cuboidf box, Vec3d onTop, out string how)
    {
        foreach (BlockPos c in Candidates(bed, head))
        {
            Vec3d at = new Vec3d(c.X + 0.5, c.Y + 0.001, c.Z + 0.5);
            if (!Standable(world, box, at)) continue;
            how = $"next to the bed at {c}";
            return at;
        }
        how = "on top of the bed (nothing free beside it)";
        return onTop;
    }

    /// <summary>Free for the box, and the floor right under it (the box moved down a little is in something).</summary>
    public static bool Standable(IWorldAccessor world, Cuboidf box, Vec3d at)
    {
        IBlockAccessor blocks = world.BlockAccessor;
        if (world.CollisionTester.IsColliding(blocks, box, at, false)) return false;
        return world.CollisionTester.IsColliding(blocks, box, new Vec3d(at.X, at.Y - 0.1, at.Z), false);
    }

    /// <summary>What vanilla's <c>DidUnmount</c> would pick (the same loop), for the test's comparison; null when it finds nothing.</summary>
    public static Vec3d Vanilla(IWorldAccessor world, BlockPos head, BlockFacing facing, Cuboidf box, out string how)
    {
        IBlockAccessor blocks = world.BlockAccessor;
        BlockPos val = head.AddCopy(facing);
        foreach (BlockFacing f in BlockFacing.HORIZONTALS)
        {
            Vec3d a = head.ToVec3d().AddCopy(f).Add(0.5, 0.001, 0.5);
            Vec3d b = val.ToVec3d().AddCopy(f).Add(0.5, 0.001, 0.5);
            if (!world.CollisionTester.IsColliding(blocks, box, a, false)) { how = $"{f.Code} of the head, {a.AsBlockPos}"; return a; }
            if (!world.CollisionTester.IsColliding(blocks, box, b, false)) { how = $"{f.Code} of the block behind the head, {b.AsBlockPos}"; return b; }
        }
        how = "nowhere";
        return null;
    }
}
