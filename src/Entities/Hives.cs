using System;
using System.Collections.Generic;
using System.Text;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Entities;

/// <summary>
/// The heart of a Deathmoth hive: resin walled round columns of larvae. The director puts two or three down the first
/// time anyone enters a hive den (MenaceSystem.Hives.cs). Breaking one is slow, and loud in the way that matters:
/// every female near answers the alarm, and more come in waves for a minute after.
/// </summary>
public class BlockMothHiveHeart : Block
{
    public override void OnBlockBroken(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1)
    {
        if (world.Side == EnumAppSide.Server) world.Api.ModLoader.GetModSystem<MenaceSystem>()?.HiveHeartBroken(pos, byPlayer?.Entity);
        base.OnBlockBroken(world, pos, byPlayer, dropQuantityMultiplier);
    }

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1f) =>
        HiveHeartDrops(world, pos, byPlayer, dropQuantityMultiplier);

    /// <summary>The level whose hive hearts also hold moth jelly, and the chance of one.</summary>
    public const int JellyLevel = 5;
    public const double JellyChance = 1.0 / 3;

    /// <summary>What a broken hive heart yields: 2 to 4 Deathmoth quills, and in Level 5 a moth jelly now and then (1 in 3).</summary>
    public static ItemStack[] HiveHeartDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier)
    {
        var drops = new List<ItemStack>();
        Item quill = world.GetItem(new AssetLocation("backrooms:mothquill"));
        if (quill != null) drops.Add(new ItemStack(quill, Math.Max(1, (int)Math.Round((2 + world.Rand.Next(3)) * Math.Max(0.5f, dropQuantityMultiplier)))));
        Item jelly = world.GetItem(new AssetLocation("backrooms:mothjelly"));
        if (jelly != null && pos != null && Backrooms.Salvage.ProtectionSystem.LevelAt(world, pos.X, pos.Z) == JellyLevel && world.Rand.NextDouble() < JellyChance)
            drops.Add(new ItemStack(jelly, 1));
        return drops.ToArray();
    }
}

/// <summary>
/// What a killed Clump leaves: a patch of flesh on the floor, which after a day grows a new, smaller Clump unless it is
/// burnt (right-click it with a lit torch or a firestarter, or keep a lit firepit or burning Firesalt within two
/// blocks) or broken.
/// </summary>
public class BlockClumpRemnant : Block
{
    /// <summary>Whether a held stack is a flame: a lit torch or a firestarter.</summary>
    public static bool IsFlame(ItemStack stack)
    {
        string path = stack?.Collectible?.Code?.Path;
        if (path == null) return false;
        return path == "firestarter" || path.StartsWith("torch") && !path.Contains("extinct");
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (!IsFlame(byPlayer?.InventoryManager?.ActiveHotbarSlot?.Itemstack)) return base.OnBlockInteractStart(world, byPlayer, blockSel);
        if (world.Side == EnumAppSide.Server && world.BlockAccessor.GetBlockEntity(blockSel.Position) is BlockEntityClumpRemnant remnant) remnant.Burn();
        return true;
    }

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1f) =>
        RemnantDrops(world, pos, byPlayer, dropQuantityMultiplier);

    /// <summary>What a broken remnant yields: 1 to 2 Clump sinew.</summary>
    public static ItemStack[] RemnantDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier)
    {
        Item sinew = world.GetItem(new AssetLocation("backrooms:clumpsinew"));
        return sinew == null ? Array.Empty<ItemStack>() : new[] { new ItemStack(sinew, 1 + world.Rand.Next(2)) };
    }

    public override string GetPlacedBlockInfo(IWorldAccessor world, BlockPos pos, IPlayer forPlayer)
    {
        var text = new StringBuilder(base.GetPlacedBlockInfo(world, pos, forPlayer));
        if (world.BlockAccessor.GetBlockEntity(pos) is BlockEntityClumpRemnant remnant)
            text.AppendLine(Lang.Get("backrooms:clumpremnant-hoursleft", Math.Max(0, remnant.HoursLeft).ToString("0")));
        return text.ToString();
    }

    /// <summary>
    /// Puts a remnant on the floor where a Clump died, if there is a standable, empty spot there. Returns whether it did.
    /// </summary>
    public static bool PlaceWhereDied(Entity clump)
    {
        IWorldAccessor world = clump.World;
        Block block = world.GetBlock(new AssetLocation("backrooms:clumpremnant"));
        if (block == null) return false;
        int x = (int)Math.Floor(clump.Pos.X), z = (int)Math.Floor(clump.Pos.Z);
        int y = Senses.FindFloor(world, x, (int)Math.Floor(clump.Pos.Y + 0.1), z, 1, 2);
        if (y == int.MinValue) return false;
        var pos = new BlockPos(x, y, z);
        if (world.BlockAccessor.GetBlock(pos).BlockId != 0) return false;
        world.BlockAccessor.SetBlock(block.BlockId, pos);
        return true;
    }
}

public class BlockEntityClumpRemnant : BlockEntity
{
    /// <summary>How long it lies before it grows a Clump, in in-game hours (a day is 24).</summary>
    public const double GrowHours = 20;

    /// <summary>It grows only with a player this near (otherwise it waits).</summary>
    public const int PlayerRange = 48;

    /// <summary>A lit firepit or burning Firesalt this near burns it when it checks.</summary>
    public const int FireRange = 2;

    private const int CheckMs = 10_000;

    /// <summary>Every remnant loaded on the server, for the debug command that hurries them.</summary>
    public static readonly HashSet<BlockPos> Live = new();

    private double placedAtHours = -1;

    public double HoursLeft => GrowHours - (Api.World.Calendar.TotalHours - placedAtHours);

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        if (api.Side != EnumAppSide.Server) return;
        if (placedAtHours < 0) placedAtHours = api.World.Calendar.TotalHours;
        Live.Add(Pos.Copy());
        RegisterGameTickListener(OnTick, CheckMs);
    }

    /// <summary>Makes it ripe at the next check (debug).</summary>
    public void Hasten()
    {
        placedAtHours = Api.World.Calendar.TotalHours - GrowHours - 0.01;
        MarkDirty();
    }

    private Vec3d Center => Pos.ToVec3d().Add(0.5, 0.1, 0.5);

    private void OnTick(float dt)
    {
        if (FireNear())
        {
            Burn();
            return;
        }
        if (HoursLeft > 0) return;
        Entity player = Api.World.GetNearestEntity(Center, PlayerRange, PlayerRange,
            e => e is EntityPlayer { Alive: true } p && p.Player?.WorldData.CurrentGameMode is not (EnumGameMode.Spectator or EnumGameMode.Creative) || e.Alive && Senses.IsTestTarget(e));
        if (player == null) return;
        if (Api.ModLoader.GetModSystem<MenaceSystem>()?.SpawnJuvenileClump(Center, player) == null) return;
        Api.World.BlockAccessor.SetBlock(0, Pos);
    }

    private bool FireNear()
    {
        IBlockAccessor ba = Api.World.BlockAccessor;
        var at = new BlockPos(0);
        for (int dy = -1; dy <= 1; dy++)
            for (int dz = -FireRange; dz <= FireRange; dz++)
                for (int dx = -FireRange; dx <= FireRange; dx++)
                {
                    Block block = ba.GetBlock(at.Set(Pos.X + dx, Pos.Y + dy, Pos.Z + dz));
                    if (block?.Code == null) continue;
                    string path = block.Code.Path;
                    if (block.Code.Domain == "game" && path == "firepit-lit" || block.Code.Domain == "backrooms" && path.StartsWith("firesalt")) return true;
                }
        return false;
    }

    /// <summary>Burns it away, with a puff of smoke.</summary>
    public void Burn()
    {
        Api.World.PlaySoundAt(new AssetLocation("game:sounds/effect/extinguish1"), Pos, 0, null, true, 16);
        Vec3d c = Center;
        Api.World.SpawnParticles(new SimpleParticleProperties(6, 10, ColorUtil.ToRgba(140, 90, 90, 90), c.AddCopy(-0.3, 0, -0.3), c.AddCopy(0.3, 0.2, 0.3),
            new Vec3f(-0.1f, 0.2f, -0.1f), new Vec3f(0.1f, 0.5f, 0.1f), 1.6f, -0.02f, 0.3f, 0.9f, EnumParticleModel.Quad));
        Api.World.BlockAccessor.SetBlock(0, Pos);
    }

    public override void OnBlockRemoved()
    {
        Live.Remove(Pos);
        base.OnBlockRemoved();
    }

    public override void OnBlockUnloaded()
    {
        Live.Remove(Pos);
        base.OnBlockUnloaded();
    }

    public override void ToTreeAttributes(ITreeAttribute tree)
    {
        base.ToTreeAttributes(tree);
        tree.SetDouble("placedAtHours", placedAtHours);
    }

    public override void FromTreeAttributes(ITreeAttribute tree, IWorldAccessor worldAccessForResolve)
    {
        base.FromTreeAttributes(tree, worldAccessForResolve);
        placedAtHours = tree.GetDouble("placedAtHours", -1);
    }
}
