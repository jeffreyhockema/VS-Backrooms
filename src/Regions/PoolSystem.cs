using System;
using System.Collections.Generic;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// Level 37, the Poolrooms: what the water does to you.
/// <list type="bullet">
/// <item>In the light, the lukewarm water eases every ache. Standing in it heals, steadies, and counts as rest.</item>
/// <item>In the Sanguine Reservoir the water turns viscous, as if not letting go, and you wade through it at half
/// pace.</item>
/// <item>The red water of the Reservoir closes every wound, and changes whoever drinks it for good: their stability
/// never again comes back quite as far (<see cref="CapKey"/>).</item>
/// </list>
/// </summary>
public class PoolSystem : ModSystem
{
    /// <summary>Player attribute: the most Reality Stability the player can ever have again, lowered by each drink of red water.</summary>
    public const string CapKey = "backrooms:stabilityCap";

    private const string ViscousStat = "backroomsViscous";
    private const float ReliefLight = 6, HealEverySeconds = 4, HealAmount = 0.5f, SteadyPerSecond = 0.02f;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private readonly Dictionary<string, float> healClock = new();
    private long tickListener;

    public override void Start(ICoreAPI api)
    {
        api.RegisterItemClass("BackroomsRedWater", typeof(ItemRedWater));
    }

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            tickListener = api.Event.RegisterGameTickListener(OnTick, 1000);
            api.Event.PlayerDisconnect += OnPlayerDisconnect;
        });
    }

    public override void Dispose()
    {
        if (sapi == null) return;
        if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
        sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
    }

    private void OnPlayerDisconnect(IServerPlayer player) => healClock.Remove(player.PlayerUID);

    private void OnTick(float dt)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { Alive: true } entity }) continue;

            // Red water's mark, wherever the player is
            double cap = entity.WatchedAttributes.GetDouble(CapKey, 1);
            double stability = entity.WatchedAttributes.GetDouble("temporalStability", 1);
            if (stability > cap) entity.WatchedAttributes.SetDouble("temporalStability", cap);

            int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
            bool here = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) == WorldLayout.Poolrooms;
            bool inWater = here && (entity.Swimming || entity.FeetInLiquid);
            bool reservoir = here && layout.IsReservoirAt(x, z);

            // The Reservoir's water holds on to whoever wades in it. (The stat itself says whether they are slowed: it is
            // not persistent, so it is gone after a rejoin or a restart, and a set kept here would go stale.)
            bool slow = inWater && reservoir;
            if (slow != entity.Stats["walkspeed"].ValuesByKey.ContainsKey(ViscousStat))
            {
                if (slow) entity.Stats.Set("walkspeed", ViscousStat, -0.5f, false);
                else entity.Stats.Remove("walkspeed", ViscousStat);
            }
            if (!inWater || reservoir) continue;

            // In the light, the water is a warm embrace
            BlockPos pos = entity.Pos.AsBlockPos.Up();
            if (sapi.World.BlockAccessor.GetLightLevel(pos, EnumLightLevelType.MaxLight) < ReliefLight) continue;
            entity.WatchedAttributes.SetDouble("temporalStability", Math.Min(cap, Math.Min(1, stability + SteadyPerSecond * dt)));
            entity.Attributes.SetDouble(MenaceSystem.RestedKey, sapi.World.Calendar.TotalHours);
            float clock = healClock.GetValueOrDefault(online.PlayerUID) + dt;
            if (clock >= HealEverySeconds)
            {
                clock = 0;
                if (entity.GetBehavior<EntityBehaviorHealth>() is { } health && health.Health < health.MaxHealth)
                    health.Health = Math.Min(health.MaxHealth, health.Health + HealAmount);
            }
            healClock[online.PlayerUID] = clock;
        }
    }
}

/// <summary>
/// Red water from the Sanguine Reservoir: drink it and every wound closes; and the drinker is changed for good, their
/// Reality Stability never again coming back past what it was, less a twentieth.
/// </summary>
public class ItemRedWater : Item
{
    private const double CapLoss = 0.05, CapFloor = 0.5;

    public override void GetHeldItemInfo(ItemSlot inSlot, System.Text.StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
        Backrooms.Needs.Water.Drinks.AppendHydrationInfo(this, world, dsc);
    }

    protected override void tryEatStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity)
    {
        int before = slot.StackSize;
        base.tryEatStop(secondsUsed, slot, byEntity);
        if (byEntity.World.Side != EnumAppSide.Server || slot.StackSize >= before) return;

        if (byEntity.GetBehavior<EntityBehaviorHealth>() is { } health) health.Health = health.MaxHealth;
        Backrooms.Needs.Water.Drinks.Hydrate(this, byEntity);
        double cap = Math.Max(CapFloor, byEntity.WatchedAttributes.GetDouble(PoolSystem.CapKey, 1) - CapLoss);
        byEntity.WatchedAttributes.SetDouble(PoolSystem.CapKey, cap);
        if (byEntity is EntityPlayer { Player: IServerPlayer player })
            player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:redwater-drunk", (int)Math.Round(cap * 100)), EnumChatType.Notification);
    }
}
