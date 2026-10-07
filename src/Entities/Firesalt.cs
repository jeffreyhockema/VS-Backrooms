using System;
using System.Text;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;

namespace Backrooms.Entities;

/// <summary>
/// Firesalt: a handful of the strange salt found by Level 3's generators, which burns with a hot red light once set
/// down. While it burns nothing hostile comes near (see <see cref="Wards"/>); after half a day it is spent.
/// </summary>
public class BlockFiresalt : Block
{
    public override string GetPlacedBlockInfo(IWorldAccessor world, Vintagestory.API.MathTools.BlockPos pos, IPlayer forPlayer)
    {
        var text = new StringBuilder(base.GetPlacedBlockInfo(world, pos, forPlayer));
        if (world.BlockAccessor.GetBlockEntity(pos) is BlockEntityFiresalt firesalt)
        {
            double left = Math.Max(0, firesalt.HoursLeft);
            text.AppendLine(Lang.Get("backrooms:firesalt-hoursleft", left.ToString("0")));
        }
        return text.ToString();
    }
}

public class BlockEntityFiresalt : BlockEntity
{
    /// <summary>How long a handful burns, in in-game hours.</summary>
    public const double BurnHours = 12;

    private double litAtHours = -1;

    public double HoursLeft => BurnHours - (Api.World.Calendar.TotalHours - litAtHours);

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        if (api.Side != EnumAppSide.Server) return;
        if (litAtHours < 0) litAtHours = api.World.Calendar.TotalHours;
        Wards.Invalidate();
        RegisterGameTickListener(OnTick, 5000);
    }

    private void OnTick(float dt)
    {
        if (HoursLeft > 0) return;
        Api.World.PlaySoundAt(new AssetLocation("game:sounds/effect/extinguish1"), Pos, 0, null, true, 16);
        Api.World.BlockAccessor.SetBlock(0, Pos);
        Wards.Invalidate();
    }

    public override void OnBlockRemoved()
    {
        base.OnBlockRemoved();
        Wards.Invalidate();
    }

    public override void ToTreeAttributes(ITreeAttribute tree)
    {
        base.ToTreeAttributes(tree);
        tree.SetDouble("litAtHours", litAtHours);
    }

    public override void FromTreeAttributes(ITreeAttribute tree, IWorldAccessor worldAccessForResolve)
    {
        base.FromTreeAttributes(tree, worldAccessForResolve);
        litAtHours = tree.GetDouble("litAtHours", -1);
    }
}
