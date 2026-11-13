using System;
using System.Text;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Props;

/// <summary>
/// A wind-up alarm clock: set down and wound ({rightmouse}), it rings <see cref="DelaySeconds"/> later for
/// <see cref="PropSystem.AlarmClockMs"/> (each {rightmouse} while it ticks adds as long again, up to <see cref="MaxSeconds"/>),
/// a lure that can be left behind. Its old spring holds <see cref="Winds"/> windings; when they are used up it is only a
/// clock. Picked up (broken), it keeps what it has left. {rightmouse} while it rings stops it.
/// </summary>
public class BlockAlarmClock : Block
{
    public const int Winds = 6, DelaySeconds = 20, MaxSeconds = 120;
    public const string WindsKey = "winds";

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (byPlayer?.Entity?.Controls.ShiftKey == true) return base.OnBlockInteractStart(world, byPlayer, blockSel);
        if (world.Side == EnumAppSide.Server && world.BlockAccessor.GetBlockEntity(blockSel.Position) is BlockEntityAlarmClock clock) clock.Wind(byPlayer);
        return true;
    }

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1)
    {
        Block north = world.GetBlock(CodeWithVariant("side", "north")) ?? this;
        var stack = new ItemStack(north);
        int winds = world.BlockAccessor.GetBlockEntity(pos) is BlockEntityAlarmClock clock ? clock.WindsLeft : Winds;
        stack.Attributes.SetInt(WindsKey, winds);
        return new[] { stack };
    }

    public override ItemStack OnPickBlock(IWorldAccessor world, BlockPos pos) =>
        new(world.GetBlock(CodeWithVariant("side", "north")) ?? this);

    public override void GetHeldItemInfo(ItemSlot inSlot, StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
        int winds = inSlot.Itemstack?.Attributes?.GetInt(WindsKey, Winds) ?? Winds;
        dsc.AppendLine(winds > 0 ? Lang.Get("backrooms:props-info-clockwinds", winds) : Lang.Get("backrooms:props-info-clockspent"));
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer) =>
        new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-windclock", MouseButton = EnumMouseButton.Right } };
}

public class BlockEntityAlarmClock : BlockEntity
{
    /// <summary>Windings the spring has left.</summary>
    public int WindsLeft = BlockAlarmClock.Winds;
    /// <summary>When it rings (world ms), or -1 if it is not set.</summary>
    private long ringAtMs = -1;
    /// <summary>Kept from a save until the world's clock is there to count from: ms still to go.</summary>
    private long pendingMs = -1;
    private long nextTickSoundMs;

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        if (pendingMs >= 0) ringAtMs = api.World.ElapsedMilliseconds + pendingMs;
        pendingMs = -1;
        if (api.Side == EnumAppSide.Server) RegisterGameTickListener(OnTick, 500);
    }

    public override void OnBlockPlaced(ItemStack byItemStack = null)
    {
        base.OnBlockPlaced(byItemStack);
        if (byItemStack?.Attributes != null) WindsLeft = byItemStack.Attributes.GetInt(BlockAlarmClock.WindsKey, BlockAlarmClock.Winds);
    }

    public void Wind(IPlayer byPlayer)
    {
        PropSystem props = PropSystem.Server;
        long now = Api.World.ElapsedMilliseconds;
        if (props?.RingingAt(Pos) != null)
        {
            props.StopRing(Pos);
            Api.World.PlaySoundAt(new AssetLocation("game:sounds/effect/latch"), Pos, 0, null, false, 12, 0.7f);
            return;
        }
        if (ringAtMs < 0)
        {
            if (WindsLeft <= 0)
            {
                PropSystem.Tell(byPlayer, "props-clock-spent");
                return;
            }
            WindsLeft--;
            ringAtMs = now + BlockAlarmClock.DelaySeconds * 1000L;
        }
        else ringAtMs = Math.Min(now + BlockAlarmClock.MaxSeconds * 1000L, ringAtMs + BlockAlarmClock.DelaySeconds * 1000L);
        Api.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/props/windup"), Pos, 0, null, true, 12, 0.8f);
        PropSystem.Note(byPlayer, "props-clock-set", (int)Math.Ceiling((ringAtMs - now) / 1000.0));
        setter = byPlayer?.Entity?.EntityId ?? -1;
        MarkDirty(true);
    }

    private long setter = -1;

    private void OnTick(float dt)
    {
        if (ringAtMs < 0) return;
        long now = Api.World.ElapsedMilliseconds;
        if (now < ringAtMs)
        {
            if (now >= nextTickSoundMs)
            {
                nextTickSoundMs = now + 2000;
                Api.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/clock"), Pos, 0, null, false, 6, 0.35f);
            }
            return;
        }
        ringAtMs = -1;
        MarkDirty(true);
        PropSystem.Server?.StartRing("alarmclock", Pos, setter < 0 ? null : Api.World.GetEntityById(setter));
    }

    public override void OnBlockRemoved()
    {
        PropSystem.Server?.StopRing(Pos);
        base.OnBlockRemoved();
    }

    public override void ToTreeAttributes(ITreeAttribute tree)
    {
        base.ToTreeAttributes(tree);
        tree.SetInt("winds", WindsLeft);
        long left = ringAtMs >= 0 && Api != null ? Math.Max(0, ringAtMs - Api.World.ElapsedMilliseconds) : pendingMs;
        tree.SetLong("ringInMs", left);
    }

    public override void FromTreeAttributes(ITreeAttribute tree, IWorldAccessor worldAccessForResolve)
    {
        base.FromTreeAttributes(tree, worldAccessForResolve);
        WindsLeft = tree.GetInt("winds", BlockAlarmClock.Winds);
        long left = tree.GetLong("ringInMs", -1);
        if (Api == null)
        {
            pendingMs = left;
            ringAtMs = -1;
        }
        else ringAtMs = left >= 0 ? Api.World.ElapsedMilliseconds + left : -1;
    }

    public override void GetBlockInfo(IPlayer forPlayer, StringBuilder dsc)
    {
        base.GetBlockInfo(forPlayer, dsc);
        if (ringAtMs >= 0 && Api != null)
            dsc.AppendLine(Lang.Get("backrooms:props-info-clockset", Math.Max(0, (int)Math.Ceiling((ringAtMs - Api.World.ElapsedMilliseconds) / 1000.0))));
        dsc.AppendLine(WindsLeft > 0 ? Lang.Get("backrooms:props-info-clockwinds", WindsLeft) : Lang.Get("backrooms:props-info-clockspent"));
    }
}
