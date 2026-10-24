using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Needs.Beds;

/// <summary>
/// The mod's bed. A vanilla <see cref="BlockEntityBed"/> (so the sleeping overlay, the director's rest check and
/// Level 974's dream all keep recognising it) with three differences: the seat lies where the mod's block says (a one-block
/// bed at the block's centre, a two-block bed on the head's edge toward the foot, whichever way the foot lies), the
/// mountable is registered as <c>backroomsbed</c>, and nobody rests here the vanilla way: <c>RestPlayer</c> is switched off
/// by <see cref="BedSystem"/>'s patch, because resting belongs to the fatigue behaviour, which reads
/// <see cref="RestQuality"/> while the player is mounted on an <see cref="IRestPlace"/>.
/// </summary>
public class BlockEntityBackroomsBed : BlockEntityBed, IMountableSeat, IMountable, IRestPlace
{
    private readonly EntityPos mountPos = new();

    public float RestQuality => BlockBackroomsBed.QualityOf(Block);

    /// <summary>The seat: on the head block's edge toward the foot, or the centre of a one-block bed, at the height of the bed's top.</summary>
    public new EntityPos Position
    {
        get
        {
            var bed = Block as BlockBackroomsBed;
            BlockFacing lie = bed?.LieDir ?? BlockFacing.NORTH;
            double y = 0.5;
            Cuboidf[] boxes = Block?.GetCollisionBoxes(Api.World.BlockAccessor, Pos);
            if (boxes is { Length: > 0 }) y = boxes[0].Y2;
            mountPos.SetPos(Pos);
            mountPos.Yaw = lie.HorizontalAngleIndex * GameMath.PIHALF + GameMath.PIHALF;
            if (bed == null || !bed.IsTwoBlock) return mountPos.Add(0.5, y, 0.5);
            if (lie == BlockFacing.NORTH) return mountPos.Add(0.5, y, 0.0);
            if (lie == BlockFacing.EAST) return mountPos.Add(1.0, y, 0.5);
            if (lie == BlockFacing.SOUTH) return mountPos.Add(0.5, y, 1.0);
            return mountPos.Add(0.0, y, 0.5);
        }
    }

    public new EntityPos SeatPosition => Position;

    public new void MountableToTreeAttributes(TreeAttribute tree)
    {
        base.MountableToTreeAttributes(tree);
        tree.SetString("className", BedSystem.MountableClass);
    }
}
