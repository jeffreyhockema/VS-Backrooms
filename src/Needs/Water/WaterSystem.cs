using System;
using NeedsApi = Backrooms.Needs.Needs;
using System.Collections.Generic;
using Backrooms.Regions;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Needs.Water;

/// <summary>
/// Drinking from the world (docs/design/needs/README.md section 3): every water block (water, salt water, boiling water)
/// gets <see cref="BlockBehaviorDrinkable"/> after the assets load, on both sides (a behaviour added then is not sent
/// to clients); and the client makes liquids selectable while thirst is on and the hand is empty.
/// </summary>
public class WaterSystem : ModSystem
{
    private ICoreClientAPI capi;
    private bool forcing;

    public override void Start(ICoreAPI api)
    {
        api.RegisterItemClass("BackroomsEmptyBottle", typeof(ItemEmptyBottle));
        api.RegisterItemClass("BackroomsLucaTears", typeof(ItemLucaTears));
    }

    public override void AssetsFinalize(ICoreAPI api)
    {
        int count = 0;
        foreach (Block block in api.World.Blocks)
        {
            if (block == null || block.Code == null || !WaterClass.IsDrinkable(block)) continue;
            BehaviorInjection.Add(block, new BlockBehaviorDrinkable(block));
            count++;
        }
        // (Both sides add to the same set of blocks: the client's count is in its own log)
        api.Logger.Notification("[backrooms] {0} liquid blocks can be drunk from ({1} side)", count, api.Side);
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Event.RegisterGameTickListener(OnClientTick, 100);
    }

    /// <summary>Liquids are selectable (so a right-click can land on water) only while thirst is on and the active hotbar slot is empty.</summary>
    private void OnClientTick(float dt)
    {
        IClientPlayer player = capi.World.Player;
        bool want = player != null && NeedsApi.ThirstOn(capi.World)
            && player.WorldData.CurrentGameMode == EnumGameMode.Survival
            && player.InventoryManager.ActiveHotbarSlot?.Empty != false;
        if (want)
        {
            capi.World.ForceLiquidSelectable = true;
            forcing = true;
        }
        else if (forcing)
        {
            capi.World.ForceLiquidSelectable = false;
            forcing = false;
        }
    }

    public override void Dispose()
    {
        if (forcing && capi != null) capi.World.ForceLiquidSelectable = false;
        forcing = false;
        capi = null;
    }
}

/// <summary>
/// Right-click and hold on water with an empty hand for a second to drink a litre of it. What it does depends on
/// <see cref="WaterClass"/>. Only while thirst is on.
/// </summary>
public class BlockBehaviorDrinkable : BlockBehavior
{
    private const float Seconds = 1f, LagSlackMs = 250;

    /// <summary>Server: when each drinker began (the client's count of seconds is not taken on trust).</summary>
    private static readonly Dictionary<string, (BlockPos Pos, long StartMs)> drinking = new();

    public BlockBehaviorDrinkable(Block block) : base(block)
    {
    }

    private static bool MayDrink(IWorldAccessor world, IPlayer player) =>
        NeedsApi.ThirstOn(world) && player?.InventoryManager?.ActiveHotbarSlot?.Empty == true;

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        if (!MayDrink(world, byPlayer) || blockSel == null) return false;
        handling = EnumHandling.PreventDefault;
        EntityPlayer entity = byPlayer.Entity;
        entity.AnimManager?.StartAnimation("eat");
        PlayDrinkSound(world, entity, 4);
        if (world.Side == EnumAppSide.Server)
            lock (drinking) drinking[byPlayer.PlayerUID] = (blockSel.Position.Copy(), world.ElapsedMilliseconds);
        return true;
    }

    public override bool OnBlockInteractStep(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        // (The server keeps the interaction open until the client's stop arrives)
        return world.Side != EnumAppSide.Client || secondsUsed < Seconds;
    }

    public override void OnBlockInteractStop(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        byPlayer?.Entity?.AnimManager?.StopAnimation("eat");
        if (world.Side != EnumAppSide.Server || byPlayer is not IServerPlayer player) return;
        (BlockPos Pos, long StartMs) began;
        lock (drinking)
        {
            if (!drinking.Remove(player.PlayerUID, out began)) return;
        }
        // Held the whole second: by the client's count, and (give or take the lag) by the server's own clock
        bool held = secondsUsed >= Seconds - 0.1f;
        bool timed = world.ElapsedMilliseconds - began.StartMs >= (long)(Seconds * 1000) - LagSlackMs;
        if (!held || !timed || !MayDrink(world, byPlayer) || blockSel == null || !began.Pos.Equals(blockSel.Position)) return;
        Drink(world, player, blockSel.Position, block);
    }

    public override bool OnBlockInteractCancel(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handled)
    {
        handled = EnumHandling.PreventDefault;
        byPlayer?.Entity?.AnimManager?.StopAnimation("eat");
        if (byPlayer != null) lock (drinking) drinking.Remove(byPlayer.PlayerUID);
        return true;
    }

    public override int GetPlacedBlockInteractionHelpCount(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling) =>
        MayDrink(world, forPlayer) ? 1 : 0;

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling) =>
        MayDrink(world, forPlayer)
            ? new[] { new WorldInteraction { ActionLangCode = "backrooms:heldhelp-drink", MouseButton = EnumMouseButton.Right } }
            : System.Array.Empty<WorldInteraction>();

    private static void PlayDrinkSound(IWorldAccessor world, EntityPlayer entity, int repeats)
    {
        if (repeats <= 0 || entity.Controls.HandUse != EnumHandInteract.BlockInteract) return;
        entity.PlayEntitySound("drink", world.PlayerByUid(entity.PlayerUID));
        world.RegisterCallback(_ => PlayDrinkSound(world, entity, repeats - 1), repeats == 4 ? 500 : 300);
    }

    /// <summary>Server: the effect of one litre from the water at <paramref name="pos"/>.</summary>
    internal static void Drink(IWorldAccessor world, IServerPlayer player, BlockPos pos, Block fluid)
    {
        WorldLayout layout = null;
        try { layout = BackroomsWorld.IsBackroomsClimate(world.Config) ? BackroomsWorld.CreateLayout(world) : null; }
        catch (Exception) { /* a world with no layout: plain water */ }
        WaterKind kind = WaterClass.Of(world, layout, fluid, pos);
        EntityPlayer entity = player.Entity;
        string message;
        switch (kind)
        {
            case WaterKind.Clean:
                NeedsApi.Hydrate(entity, WaterClass.CleanHydration);
                message = "backrooms:drink-clean";
                break;
            case WaterKind.Tainted:
                NeedsApi.Hydrate(entity, WaterClass.TaintedHydration);
                Drinks.AddStability(entity, WaterClass.TaintedStability);
                bool sick = world.Rand.NextDouble() < WaterClass.SickChance;
                if (sick) NeedsApi.MakeSick(entity, WaterClass.SickHours);
                message = "backrooms:drink-tainted"; // (MakeSick says the rest)
                break;
            case WaterKind.Salt:
                NeedsApi.Hydrate(entity, WaterClass.SaltHydration);
                message = "backrooms:drink-salt";
                break;
            default:
                entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Internal, Type = EnumDamageType.Heat }, 2f);
                message = "backrooms:drink-scald";
                break;
        }
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, message), EnumChatType.Notification);
    }
}
