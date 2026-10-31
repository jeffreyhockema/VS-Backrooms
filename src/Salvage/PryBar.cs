using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Salvage;

/// <summary>
/// The pry bar. Every level has rooms behind locked doors that nobody has been into since they were locked: Level 1's
/// steel doors, Level 2's storerooms, Level 4's offices, Level 5's guest rooms, Level 9's houses. Lean on a pry bar
/// for a few seconds and the door gives, for good. It is loud: whatever is near hears it. A door with nothing behind it
/// (and there are many) does not give, and costs nothing to try; a door that goes somewhere is not locked at all.
/// </summary>
public class PrySystem : ModSystem
{
    /// <summary>The locked doors a pry bar works on (the first part of their block codes).</summary>
    public static readonly HashSet<string> Doors = new() { "metaldoor", "officedoor", "hoteldoor", "tunneldoor", "tunneldoorpaint", "housedoor", "suburbdoor" };

    /// <summary>Whether a block of one of the <see cref="Doors"/> is locked (a Suburbs door from layout version 9 only when it says so; the others always).</summary>
    public static bool Locked(Block block) => block.FirstCodePart() != "suburbdoor" || block.Variant["state"] == "locked";

    /// <summary>How long it takes to force a door, in seconds.</summary>
    public const float PrySeconds = 4f;

    private ICoreServerAPI sapi;
    private WorldLayout layout;

    public override void Start(ICoreAPI api)
    {
        api.RegisterItemClass("BackroomsPryBar", typeof(ItemPryBar));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType == BackroomsWorld.WorldTypeCode) layout = BackroomsWorld.CreateLayout(api.World);
        });
    }

    public override void AssetsFinalize(ICoreAPI api)
    {
        // Ahead of the doors' own behaviours, so that with a pry bar in hand you force the door rather than try it
        foreach (Block block in api.World.Blocks)
        {
            if (block?.Code?.Domain != "backrooms" || !Doors.Contains(block.FirstCodePart()) || !Locked(block)) continue;
            block.BlockBehaviors = new BlockBehavior[] { new BlockBehaviorPryable(block) }.Concat(block.BlockBehaviors ?? Array.Empty<BlockBehavior>()).ToArray();
        }
    }

    /// <summary>Forces the door at a position, if it will give. Returns whether it did.</summary>
    public bool Pry(IServerPlayer player, BlockPos pos, ItemSlot slot)
    {
        if (layout == null) return false;
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        Block door = blocks.GetBlock(pos);
        if (door.Code?.Domain != "backrooms" || !Doors.Contains(door.FirstCodePart()) || !Locked(door)) return false;
        string family = door.FirstCodePart();
        // Not in somebody else's claim (TryAccess tells the player why)
        if (!sapi.World.Claims.TryAccess(player, pos, EnumBlockAccessFlags.BuildOrBreak)) return false;

        // A door that goes somewhere is not locked
        if (door.GetBehavior<BlockBehaviorThreshold>() is { } threshold
            && sapi.ModLoader.GetModSystem<ThresholdSystem>().LeadsSomewhere(pos, threshold.Kind))
        {
            player.SendIngameError("backrooms-pry", Lang.Get("backrooms:pry-notlocked"));
            return false;
        }
        // Only a door with a room behind it gives; most are set in solid wall
        if (!RoomBehind(pos.X, pos.Z))
        {
            player.SendIngameError("backrooms-pry", Lang.Get("backrooms:pry-solid"));
            return false;
        }

        // Both halves of the door come away
        for (int dy = -2; dy <= 2; dy++)
        {
            BlockPos at = pos.AddCopy(0, dy, 0);
            Block there = blocks.GetBlock(at);
            if (there.Code?.Domain == "backrooms" && there.FirstCodePart() == family) blocks.SetBlock(0, at);
        }
        if (sapi.World.GetItem(new AssetLocation("backrooms:metalbracket")) is Item bracket)
            sapi.World.SpawnItemEntity(new ItemStack(bracket), pos.ToVec3d().Add(0.5, 0.5, 0.5));
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/metaldoor"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, false, 48, 1f);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/anvilhit"), pos.X + 0.5, pos.Y + 1, pos.Z + 0.5, null, true, 48, 0.8f);
        // Everything near hears it
        sapi.ModLoader.GetModSystem<MenaceSystem>()?.MakeNoise(player.Entity, 1.0);
        slot.Itemstack?.Collectible.DamageItem(sapi.World, player.Entity, slot);
        slot.MarkDirty();
        return true;
    }

    private static readonly (int Dx, int Dz)[] Sides = { (1, 0), (-1, 0), (0, 1), (0, -1) };

    /// <summary>Whether a door tile has a locked room behind it: floor beside it that nobody can walk into.</summary>
    private bool RoomBehind(int x, int z)
    {
        Tile tile = layout.TileAt(x, z);
        if (tile.Kind != TileKind.Door) return false;
        foreach ((int dx, int dz) in Sides)
        {
            Tile n = layout.TileAt(x + dx, z + dz);
            if (n.Kind == TileKind.Floor && n.Sealed) return true;
        }
        return false;
    }
}

/// <summary>The pry bar: hold right-click on a locked door to force it.</summary>
public class ItemPryBar : Item
{
}

/// <summary>
/// Lets a pry bar force a locked door: hold right-click with one in hand for <see cref="PrySystem.PrySeconds"/>. Letting
/// go, looking away or putting the bar away before then ends it with nothing done; the door is only forced in
/// <see cref="OnBlockInteractStop"/> on the server, on the server's own count of how long it was held.
/// </summary>
public class BlockBehaviorPryable : BlockBehavior
{
    public BlockBehaviorPryable(Block block) : base(block)
    {
    }

    private static bool Holding(IPlayer player) => player?.InventoryManager?.ActiveHotbarSlot?.Itemstack?.Collectible is ItemPryBar;

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        if (!Holding(byPlayer)) return false;
        handling = EnumHandling.PreventSubsequent;
        world.PlaySoundAt(new AssetLocation("game:sounds/block/metaldoor"), blockSel.Position.X + 0.5, blockSel.Position.Y + 0.5, blockSel.Position.Z + 0.5, byPlayer, true, 16, 0.4f);
        return true;
    }

    public override bool OnBlockInteractStep(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        if (!Holding(byPlayer)) return false;
        handling = EnumHandling.PreventSubsequent;
        return secondsUsed < PrySystem.PrySeconds;
    }

    public override void OnBlockInteractStop(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        if (!Holding(byPlayer)) return;
        handling = EnumHandling.PreventSubsequent;
        // (Stop also follows a release: only a full hold forces the door. The tenth of a second allows for the server
        // counting from when the start reached it, a little after the client did)
        if (secondsUsed < PrySystem.PrySeconds - 0.1f || world.Api is not ICoreServerAPI sapi || byPlayer is not IServerPlayer player) return;
        sapi.ModLoader.GetModSystem<PrySystem>()?.Pry(player, blockSel.Position, player.InventoryManager.ActiveHotbarSlot);
    }

    public override bool OnBlockInteractCancel(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        if (!Holding(byPlayer)) return false;
        // Letting go or looking away always ends it (the door's own behaviours never get to hold the bar on the door)
        handling = EnumHandling.PreventSubsequent;
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        // (Never null: the HUD counts what comes back)
        return Array.Empty<WorldInteraction>();
    }
}
