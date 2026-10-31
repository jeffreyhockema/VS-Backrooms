using System;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Deep;

/// <summary>Registers the blocks and items of Levels 6 to 10 that do something.</summary>
public class DeepBlocksSystem : ModSystem
{
    public override void Start(ICoreAPI api)
    {
        api.RegisterItemClass("BackroomsChalk", typeof(ItemChalk));
        api.RegisterBlockClass("BackroomsWorms", typeof(BlockWorms));
        api.RegisterBlockClass("BackroomsTar", typeof(BlockTar));
        api.RegisterBlockBehaviorClass("BackroomsSuburbDoor", typeof(BlockBehaviorSuburbDoor));
    }
}

/// <summary>
/// Surveyor's chalk. Right-click a wall to leave a mark on it facing you: an arrow pointing left or right, a cross
/// for a dead end or a circle for "been here", picked with the tool mode menu. In Level 6, where maps fail and no
/// light reaches, these are the one thing that stays where you left it. Marks show on the map.
/// </summary>
public class ItemChalk : Item
{
    private static readonly string[] Symbols = { "left", "right", "cross", "circle" };
    private SkillItem[] modes;

    public override void OnLoaded(ICoreAPI api)
    {
        base.OnLoaded(api);
        if (api is not ICoreClientAPI capi) return;
        string[] letters = { "<", ">", "X", "O" };
        modes = new SkillItem[Symbols.Length];
        for (int i = 0; i < Symbols.Length; i++)
        {
            modes[i] = new SkillItem { Code = new AssetLocation(Symbols[i]), Name = Lang.Get("backrooms:chalkmode-" + Symbols[i]) }
                .WithLetterIcon(capi, letters[i]);
        }
    }

    public override void OnUnloaded(ICoreAPI api)
    {
        if (modes != null) foreach (SkillItem mode in modes) mode?.Dispose();
        base.OnUnloaded(api);
    }

    public override SkillItem[] GetToolModes(ItemSlot slot, IClientPlayer forPlayer, BlockSelection blockSel) => modes;

    private static bool IsMark(Block block) => block.Code?.Domain == "backrooms" && block.Code.Path.StartsWith("chalkmark-");

    public override int GetToolMode(ItemSlot slot, IPlayer byPlayer, BlockSelection blockSelection) =>
        slot.Itemstack?.Attributes.GetInt("chalkmode") ?? 0;

    public override void SetToolMode(ItemSlot slot, IPlayer byPlayer, BlockSelection blockSelection, int toolMode)
    {
        slot.Itemstack?.Attributes.SetInt("chalkmode", toolMode);
    }

    public override void OnHeldInteractStart(ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel, bool firstEvent, ref EnumHandHandling handling)
    {
        if (blockSel == null || !firstEvent)
        {
            base.OnHeldInteractStart(slot, byEntity, blockSel, entitySel, firstEvent, ref handling);
            return;
        }
        IWorldAccessor world = byEntity.World;
        Block clicked = world.BlockAccessor.GetBlock(blockSel.Position);
        BlockPos at;
        string side;
        if (IsMark(clicked))
        {
            // Clicking an existing mark changes it in place
            at = blockSel.Position.Copy();
            side = clicked.Variant["side"];
        }
        else
        {
            // Marks go on the solid side faces of walls, never on floors, ceilings, bars or furniture
            if (!blockSel.Face.IsHorizontal || !clicked.SideSolid[blockSel.Face.Index])
            {
                base.OnHeldInteractStart(slot, byEntity, blockSel, entitySel, firstEvent, ref handling);
                return;
            }
            at = blockSel.Position.AddCopy(blockSel.Face);
            side = blockSel.Face.Code;
            Block there = world.BlockAccessor.GetBlock(at);
            if (there.BlockId != 0 && there.Replaceable < 6000 && !IsMark(there)) return;
        }
        handling = EnumHandHandling.PreventDefault;
        if (world.Side != EnumAppSide.Server) return;
        IPlayer player = (byEntity as EntityPlayer)?.Player;
        if (player != null && !world.Claims.TryAccess(player, at, EnumBlockAccessFlags.BuildOrBreak)) return;

        string symbol = Symbols[Math.Clamp(GetToolMode(slot, player, blockSel), 0, Symbols.Length - 1)];
        Block mark = world.GetBlock(new AssetLocation("backrooms", $"chalkmark-{symbol}-{side}"));
        if (mark == null || mark.BlockId == world.BlockAccessor.GetBlock(at).BlockId) return;
        world.BlockAccessor.SetBlock(mark.BlockId, at);
        world.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/chalk"), at.X + 0.5, at.Y + 0.5, at.Z + 0.5, null, randomizePitch: true, range: 8);
        DamageItem(world, byEntity, slot);
    }
}

/// <summary>
/// The mass of worms a metre under Level 10. Break into it and they erupt: whoever is close is bitten, worms spill
/// out, and the infestation swells up into the soil around, killing the crops it reaches.
/// </summary>
public class BlockWorms : Block
{
    public override void OnBlockBroken(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1)
    {
        base.OnBlockBroken(world, pos, byPlayer, dropQuantityMultiplier);
        if (world.Side != EnumAppSide.Server) return;

        world.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/squelch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, randomizePitch: true, range: 24);
        // Whoever is close gets bitten
        foreach (Entity entity in world.GetEntitiesAround(pos.ToVec3d().Add(0.5, 0.5, 0.5), 5, 4, e => e.Alive && e is EntityAgent))
        {
            entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Block, SourceBlock = this, Type = EnumDamageType.PiercingAttack, SourcePos = pos.ToVec3d() }, 3f);
        }
        // Worms spill out
        EntityProperties worm = world.GetEntityType(new AssetLocation("game", "earthworm"));
        int worms = 3 + world.Rand.Next(3);
        for (int i = 0; worm != null && i < worms; i++)
        {
            Entity e = world.ClassRegistry.CreateEntity(worm);
            e.Pos.SetPos(pos.X + world.Rand.NextDouble(), pos.Y + 1, pos.Z + world.Rand.NextDouble());
            world.SpawnEntity(e);
        }
        // The infestation swells up into the soil and crops around
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
            {
                if (dx * dx + dz * dz > 5 || world.Rand.NextDouble() < 0.35) continue;
                for (int dy = 0; dy <= 2; dy++)
                {
                    BlockPos p = pos.AddCopy(dx, dy, dz);
                    Block b = world.BlockAccessor.GetBlock(p);
                    if (b.Code?.Path.StartsWith("crop-") == true || b.Code?.Path.StartsWith("tallgrass") == true) world.BlockAccessor.SetBlock(0, p);
                    else if (b.Code?.Path.StartsWith("soil-") == true || b.Code?.Path.StartsWith("farmland") == true) world.BlockAccessor.SetBlock(BlockId, p);
                }
            }
        world.SpawnCubeParticles(pos.ToVec3d().Add(0.5, 0.8, 0.5), new ItemStack(this), 1.5f, 40, 0.8f);
    }
}

/// <summary>
/// Scalding tar: anything that touches it is burnt. A bucket (or any open vanilla liquid container) right-clicked on it
/// is filled with the game's own tar (<c>game:tarportion</c>, 100 portions a litre), as it would be from a liquid block;
/// the pool is not used up. The tar goes into a barrel recipe for asphalt (<c>recipes/barrel/build-asphalt.json</c>).
/// </summary>
public class BlockTar : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        ItemSlot hand = byPlayer?.InventoryManager?.ActiveHotbarSlot;
        if (hand?.Itemstack?.Collectible is BlockLiquidContainerBase container && container.AllowHeldLiquidTransfer)
        {
            Item tar = world.GetItem(new AssetLocation("game:tarportion"));
            if (tar != null && container.GetCurrentLitres(hand.Itemstack) < container.CapacityLitres)
            {
                if (world.Side == EnumAppSide.Server)
                {
                    ItemStack portion = new ItemStack(tar, 1);
                    float litres = container.CapacityLitres;
                    int moved = container.SplitStackAndPerformAction(byPlayer.Entity, hand, stack => container.TryPutLiquid(stack, portion, litres));
                    if (moved > 0)
                    {
                        container.DoLiquidMovedEffects(byPlayer, portion, moved, BlockLiquidContainerBase.EnumLiquidDirection.Fill);
                        hand.MarkDirty();
                    }
                }
                return true;
            }
        }
        return base.OnBlockInteractStart(world, byPlayer, blockSel);
    }

    public override void OnEntityCollide(IWorldAccessor world, Entity entity, BlockPos pos, BlockFacing facing, Vec3d collideSpeed, bool isImpact)
    {
        base.OnEntityCollide(world, entity, pos, facing, collideSpeed, isImpact);
        if (world.Side != EnumAppSide.Server || entity is not EntityAgent) return;
        long now = world.ElapsedMilliseconds;
        if (now - entity.Attributes.GetLong("backroomsTarBurn") < 1000) return;
        entity.Attributes.SetLong("backroomsTarBurn", now);
        entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Block, SourceBlock = this, Type = EnumDamageType.Fire, SourcePos = pos.ToVec3d() }, 1.5f);
    }
}
