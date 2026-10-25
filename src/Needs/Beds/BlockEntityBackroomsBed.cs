using System;
using System.Reflection;
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

    // Vanilla's private bookkeeping, which its DidUnmount sets and ours must set the same way (read once)
    private static readonly FieldInfo BlockBrokenField = typeof(BlockEntityBed).GetField("blockBroken", BindingFlags.Instance | BindingFlags.NonPublic);
    private static readonly FieldInfo MountedByEntityIdField = typeof(BlockEntityBed).GetField("mountedByEntityId", BindingFlags.Instance | BindingFlags.NonPublic);
    private static readonly FieldInfo MountedByPlayerUidField = typeof(BlockEntityBed).GetField("mountedByPlayerUid", BindingFlags.Instance | BindingFlags.NonPublic);
    private static readonly FieldInfo RestingListenerField = typeof(BlockEntityBed).GetField("restingListener", BindingFlags.Instance | BindingFlags.NonPublic);

    /// <summary>
    /// Getting up. Vanilla's own would teleport the sleeper by the side code, which for most of the mod's beds points through the
    /// headboard (into the next room); this does its bookkeeping and stands the sleeper by <see cref="BedStand"/>'s rule instead.
    /// Never calls the base, which would teleport.
    /// </summary>
    public new void DidUnmount(EntityAgent entityAgent)
    {
        if (MountedBy?.GetBehavior("tiredness") is EntityBehaviorTiredness tiredness) tiredness.IsSleeping = false;
        MountedBy = null;
        if (entityAgent != null && !(BlockBrokenField?.GetValue(this) is true))
        {
            Vec3d spot = null;
            if (Block is BlockBackroomsBed bed)
            {
                EntityPos seat = Position;
                Vec3d onTop = new(seat.X, seat.Y + 0.1, seat.Z);
                spot = BedStand.Choose(Api.World, bed, bed.HeadPos(Pos), entityAgent.SelectionBox, onTop, out _);
            }
            if (spot != null)
            {
                spot.Y %= 32768.0;
                entityAgent.TeleportTo(spot);
            }
        }
        MountedByEntityIdField?.SetValue(this, 0L);
        MountedByPlayerUidField?.SetValue(this, null);
        if (RestingListenerField?.GetValue(this) is long listener) UnregisterGameTickListener(listener);
        RestingListenerField?.SetValue(this, 0L);
    }

    public new void MountableToTreeAttributes(TreeAttribute tree)
    {
        base.MountableToTreeAttributes(tree);
        tree.SetString("className", BedSystem.MountableClass);
    }
}
