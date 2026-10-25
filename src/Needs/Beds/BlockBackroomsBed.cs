using System;
using System.Text;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Needs.Beds;

/// <summary>
/// Every bed-like block of the mod that can be slept on (docs/design/needs/README.md section 8): the hotel and Level 974
/// and 188 beds, hospital beds, cots, sleeping bags, makeshift beds and bedrolls, and the carpet bedroll you craft.
/// Not a vanilla <c>BlockBed</c>: the vanilla block takes its two halves from a <c>head</c>/<c>feet</c> variant and its
/// foot direction from the side code, which the mod's blocks do not all share. This one reads block attributes:
/// <list type="bullet">
/// <item><c>bedFoot</c>: <c>"side"</c> (the foot lies in the direction of the side code) or <c>"opposite"</c> (the other
/// way); absent for a one-block bed. The same on both halves.</item>
/// <item><c>restQuality</c>: 1 a proper bed, 0.6 a bedroll (falls back to <c>sleepEfficiency</c>, then 0.6).</item>
/// <item><c>bedDropHead</c>: the bed is picked and (with no drops of its own) dropped as its head half facing north.</item>
/// <item><c>bedBreakPartner</c>: breaking one half breaks the other (the vanilla bed's behaviour).</item>
/// </list>
/// The half that holds the block entity (the <c>entityClass</c>) is the head; a one-block bed is its own head. The block
/// entity is created lazily on first use, because worldgen places no block entities and old chunks hold none (or a vanilla
/// <c>Bed</c>).
/// </summary>
public class BlockBackroomsBed : Block
{
    public const float DefaultQuality = 0.6f;

    /// <summary>The side code of the block, the way it faces.</summary>
    public BlockFacing Side => BlockFacing.FromCode(LastCodePart(0)) ?? BlockFacing.NORTH;

    /// <summary>The head half (or the one block of a one-block bed): the one with the block entity.</summary>
    public bool IsHead => EntityClass != null;

    /// <summary>Whether the bed is two blocks.</summary>
    public bool IsTwoBlock => FootDir != null;

    /// <summary>The direction from the head to the foot; null for a one-block bed.</summary>
    public BlockFacing FootDir => Attributes?["bedFoot"].AsString() switch
    {
        "side" => Side,
        "opposite" => Side.Opposite,
        _ => null,
    };

    /// <summary>The way the sleeper's feet point: toward the foot half, and for a one-block bed (modelled head to the north) away from the side.</summary>
    public BlockFacing LieDir => FootDir ?? Side.Opposite;

    public float Quality => QualityOf(this);

    public static float QualityOf(Block block)
    {
        var a = block?.Attributes;
        if (a == null) return DefaultQuality;
        if (a["restQuality"].Exists) return a["restQuality"].AsFloat(DefaultQuality);
        if (a["sleepEfficiency"].Exists) return a["sleepEfficiency"].AsFloat(DefaultQuality);
        return DefaultQuality;
    }

    /// <summary>The position of the head half, from the position of either half.</summary>
    public BlockPos HeadPos(BlockPos pos)
    {
        if (IsHead || FootDir == null) return pos;
        return pos.AddCopy(FootDir.Opposite);
    }

    /// <summary>The position of the other half, or null for a one-block bed.</summary>
    public BlockPos PartnerPos(BlockPos pos)
    {
        BlockFacing foot = FootDir;
        if (foot == null) return null;
        return IsHead ? pos.AddCopy(foot) : pos.AddCopy(foot.Opposite);
    }

    /// <summary>
    /// Server side. The mod's block entity at a head position: made when there is none, and replacing any other kind (a
    /// vanilla <c>Bed</c> an old save holds). Null when the position is not a head of one of these beds.
    /// </summary>
    public static BlockEntityBackroomsBed EnsureEntity(IWorldAccessor world, BlockPos head)
    {
        IBlockAccessor blocks = world.BlockAccessor;
        if (blocks.GetBlock(head) is not BlockBackroomsBed { IsHead: true }) return null;
        BlockEntity existing = blocks.GetBlockEntity(head);
        if (existing is BlockEntityBackroomsBed mine) return mine;
        if (existing is BlockEntityBed { MountedBy: { } rider }) rider.TryUnmount();
        if (existing != null) blocks.RemoveBlockEntity(head);
        blocks.SpawnBlockEntity("BackroomsBed", head);
        return blocks.GetBlockEntity(head) as BlockEntityBackroomsBed;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (!world.Claims.TryAccess(byPlayer, blockSel.Position, EnumBlockAccessFlags.Use)) return false;
        BlockPos head = HeadPos(blockSel.Position);
        // (A half whose other half is gone cannot be slept on)
        if (world.BlockAccessor.GetBlock(head) is not BlockBackroomsBed { IsHead: true } headBlock
            || (!head.Equals(blockSel.Position) && !IsPartOfSameBed(headBlock))) return false;

        // The one rule both sides share: vanilla tiredness above 8 (the fatigue behaviour drives it from awake hours)
        if (byPlayer.Entity.GetBehavior("tiredness") is EntityBehaviorTiredness { Tiredness: <= 8f })
        {
            Refuse(world, byPlayer, "nottiredenough", "not-tired-enough");
            return false;
        }

        if (world.Side == EnumAppSide.Client)
        {
            // The server decides and makes the block entity if need be; the mount comes back with the player's state
            return (world.BlockAccessor.GetBlockEntity(head) as BlockEntityBed)?.MountedBy == null;
        }

        if (world.Config.GetString("temporalStormSleeping", "0") == "0"
            && api.ModLoader.GetModSystem<SystemTemporalStability>(true).StormStrength > 0f)
        {
            Refuse(world, byPlayer, "cantsleep-tempstorm", "cantsleep-tempstorm");
            return false;
        }
        if (byPlayer is IServerPlayer sp && Needs.CanSleep(sp, head) is { } reason)
        {
            Refuse(world, byPlayer, reason, reason);
            return false;
        }
        BlockEntityBackroomsBed bed = EnsureEntity(world, head);
        if (bed == null || bed.MountedBy != null) return false;
        Vec3d beside = byPlayer.Entity.Pos.XYZ;
        if (!byPlayer.Entity.TryMount(bed)) return false;
        // Progression 3.8: the last bed slept in is where they wake after a death (else their Level 0 home)
        (byPlayer as IServerPlayer)?.SetSpawnPosition(new PlayerSpawnPos((int)Math.Floor(beside.X), (int)Math.Floor(beside.Y), (int)Math.Floor(beside.Z)));
        return true;
    }

    private void Refuse(IWorldAccessor world, IPlayer player, string code, string langKey)
    {
        if (world.Side == EnumAppSide.Client) (api as ICoreClientAPI)?.TriggerIngameError(this, code, Lang.Get(langKey));
        else if (player is IServerPlayer sp) sp.SendIngameError(code, Say.T(sp, langKey));
    }

    /// <summary>
    /// A two-block bed that picks up as its head (<c>bedDropHead</c>) is placed the way the vanilla bed is: the head half
    /// goes on the far side of the clicked block, the foot on it, both facing so that the foot lies in the direction
    /// <c>bedFoot</c> says. Other blocks place as one block.
    /// </summary>
    public override bool TryPlaceBlock(IWorldAccessor world, IPlayer byPlayer, ItemStack itemstack, BlockSelection blockSel, ref string failureCode)
    {
        if (Attributes?["bedDropHead"].AsBool() != true || !IsTwoBlock || !Variant.ContainsKey("part"))
            return base.TryPlaceBlock(world, byPlayer, itemstack, blockSel, ref failureCode);
        if (!world.Claims.TryAccess(byPlayer, blockSel.Position, EnumBlockAccessFlags.BuildOrBreak))
        {
            byPlayer.InventoryManager.ActiveHotbarSlot.MarkDirty();
            return false;
        }
        if (!CanPlaceBlock(world, byPlayer, blockSel, ref failureCode)) return false;
        BlockFacing f = SuggestedHVOrientation(byPlayer, blockSel)[0];
        var headSel = new BlockSelection { Position = blockSel.Position.AddCopy(f), Face = BlockFacing.UP };
        if (!CanPlaceBlock(world, byPlayer, headSel, ref failureCode)) return false;
        // (The foot lies from the head toward the clicked block, which is f.Opposite from the head)
        string side = Attributes["bedFoot"].AsString() == "side" ? f.Opposite.Code : f.Code;
        Block head = Half("head", side, world), foot = Half("feet", side, world);
        if (head == null || foot == null) return false;
        head.DoPlaceBlock(world, byPlayer, headSel, itemstack);
        foot.DoPlaceBlock(world, byPlayer, blockSel, itemstack);
        return true;
    }

    /// <summary>The block of this bed's family for a part and a side, or null.</summary>
    private Block Half(string part, string side, IWorldAccessor world) =>
        world.GetBlock(BlockCodes.WithVariant(this, "part", part)) is { } p ? world.GetBlock(BlockCodes.WithVariant(p, "side", side)) : null;

    public override void OnBlockRemoved(IWorldAccessor world, BlockPos pos)
    {
        if (IsHead && world.BlockAccessor.GetBlockEntity(pos) is BlockEntityBed { MountedBy: { } rider }) rider.TryUnmount();
        if (Attributes?["bedBreakPartner"].AsBool() == true && PartnerPos(pos) is { } other
            && world.BlockAccessor.GetBlock(other) is BlockBackroomsBed partner && partner.IsHead != IsHead && IsPartOfSameBed(partner))
            world.BlockAccessor.SetBlock(0, other);
        base.OnBlockRemoved(world, pos);
    }

    /// <summary>Whether another half is the other half of this one's bed: the same code but for the part.</summary>
    private bool IsPartOfSameBed(BlockBackroomsBed other) =>
        other.Variant.TryGetValue("part", out string part) && BlockCodes.WithVariant(this, "part", part).Equals(other.Code);

    /// <summary>This bed's head half facing north: what the creative inventory holds, and what picking gives.</summary>
    private ItemStack HeadStack(IWorldAccessor world)
    {
        Block head = this;
        if (Variant.ContainsKey("part") && world.GetBlock(BlockCodes.WithVariant(this, "part", "head")) is { } h) head = h;
        Block north = world.GetBlock(BlockCodes.WithVariant(head, "side", "north"));
        return north == null ? null : new ItemStack(north);
    }

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1f)
    {
        if (Attributes?["bedDropHead"].AsBool() == true && HeadStack(world) is { } stack)
            return new[] { stack };
        return base.GetDrops(world, pos, byPlayer, dropQuantityMultiplier);
    }

    public override ItemStack OnPickBlock(IWorldAccessor world, BlockPos pos)
    {
        if (Attributes?["bedDropHead"].AsBool() == true && HeadStack(world) is { } stack) return stack;
        return base.OnPickBlock(world, pos);
    }

    public override AssetLocation GetRotatedBlockCode(int angle)
    {
        int index = GameMath.Mod(Side.HorizontalAngleIndex - angle / 90, 4);
        return BlockCodes.WithVariant(this, "side", BlockFacing.HORIZONTALS_ANGLEORDER[index].Code);
    }

    public override AssetLocation GetHorizontallyFlippedBlockCode(EnumAxis axis) =>
        Side.Axis == axis ? BlockCodes.WithVariant(this, "side", Side.Opposite.Code) : Code;

    public override void GetHeldItemInfo(ItemSlot inSlot, StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
        dsc.AppendLine().AppendLine(Lang.Get("backrooms:bedinfo", Math.Round(Quality * 100)));
    }

    public override string GetPlacedBlockInfo(IWorldAccessor world, BlockPos pos, IPlayer forPlayer) =>
        base.GetPlacedBlockInfo(world, pos, forPlayer) + Lang.Get("backrooms:bedinfo", Math.Round(Quality * 100));

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer)
    {
        WorldInteraction[] others = base.GetPlacedBlockInteractionHelp(world, selection, forPlayer) ?? Array.Empty<WorldInteraction>();
        var help = new WorldInteraction[others.Length + 1];
        help[0] = new WorldInteraction { ActionLangCode = "backrooms:blockhelp-bed", MouseButton = EnumMouseButton.Right };
        Array.Copy(others, 0, help, 1, others.Length);
        return help;
    }
}
