using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Reality;

/// <summary>
/// Reality Stability: Vintage Story's temporal stability, recast as how firmly a wanderer is anchored to the level
/// they are in. The game's own system does the work (the gear on the HUD, the distortion and whispers at low
/// stability, the damage at zero); this replaces where stability is high or low with the Backrooms' own geography,
/// and drains it everywhere during a Reality Shift.
/// </summary>
public class RealitySystem : ModSystem
{
    /// <summary>How much a full Reality Shift lowers stability everywhere.</summary>
    private const float ShiftDrain = 1.3f;

    private ICoreAPI api;
    private WorldLayout layout;
    private WorldGeometry geometry;

    /// <summary>Server: total hours until which a forced shift lasts.</summary>
    private double forcedUntilHours;

    // Shift strength is the same everywhere, so work it out once per tick rather than for every stability query
    private double cachedStrength;
    private long cachedAtMs = -1000;

    public override void Start(ICoreAPI api)
    {
        this.api = api;
        api.RegisterItemClass("BackroomsAlmondWater", typeof(ItemAlmondWater));
    }

    public override void StartServerSide(ICoreServerAPI sapi)
    {
        sapi.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (sapi.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            Hook(sapi);
            sapi.Event.PlayerNowPlaying += player => player.Entity.WatchedAttributes.SetDouble(RealityShift.ForcedUntilAttribute, forcedUntilHours);
        });
    }

    public override void StartClientSide(ICoreClientAPI capi)
    {
        capi.Event.LevelFinalize += () =>
        {
            if (BackroomsWorld.IsBackroomsClimate(capi.World.Config)) Hook(capi);
        };
    }

    private void Hook(ICoreAPI api)
    {
        layout = BackroomsWorld.CreateLayout(api.World);
        geometry = BackroomsWorld.CreateGeometry(api.World);
        api.ModLoader.GetModSystem<SystemTemporalStability>().OnGetTemporalStability += OnGetStability;
    }

    /// <summary>Whether this world is a Backrooms world with Reality Stability running.</summary>
    public bool Active => layout != null;

    /// <summary>Strength of the Reality Shift right now, from 0 (none) to 1.</summary>
    public double ShiftStrength
    {
        get
        {
            if (layout == null) return 0;
            long now = api.World.ElapsedMilliseconds;
            if (now - cachedAtMs < 100) return cachedStrength;

            double forced = forcedUntilHours;
            if (api is ICoreClientAPI capi)
            {
                forced = capi.World.Player?.Entity?.WatchedAttributes.GetDouble(RealityShift.ForcedUntilAttribute) ?? 0;
            }
            cachedStrength = RealityShift.CurrentStrength(api, forced);
            cachedAtMs = now;
            return cachedStrength;
        }
    }

    /// <summary>Server: starts a shift now that lasts the given number of in-game hours (0 ends it).</summary>
    public void ForceShift(double hours)
    {
        if (api is not ICoreServerAPI sapi) return;
        forcedUntilHours = hours <= 0 ? 0 : sapi.World.Calendar.ElapsedHours + hours;
        foreach (IPlayer player in sapi.World.AllOnlinePlayers)
        {
            player.Entity.WatchedAttributes.SetDouble(RealityShift.ForcedUntilAttribute, forcedUntilHours);
        }
        cachedAtMs = -1000;
    }

    private float OnGetStability(float vanillaStability, double x, double y, double z)
    {
        float stability = layout.StabilityAt(x, y, z, geometry.FloorY) - ShiftDrain * (float)ShiftStrength;
        return Math.Clamp(stability, -0.5f, 1.5f);
    }
}

/// <summary>Almond Water steadies the mind: drinking it restores some of the drinker's stability.</summary>
public class ItemAlmondWater : Item
{
    /// <summary>How much stability a drink restores, unless its <c>stabilityRestored</c> attribute says otherwise.</summary>
    private const double StabilityRestored = 0.15;

    protected override void tryEatStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity)
    {
        int before = slot.StackSize;
        base.tryEatStop(secondsUsed, slot, byEntity);
        if (byEntity.World.Side != EnumAppSide.Server || slot.StackSize >= before) return;

        double stability = byEntity.WatchedAttributes.GetDouble("temporalStability", 1);
        double restored = Attributes?["stabilityRestored"].AsDouble(StabilityRestored) ?? StabilityRestored;
        byEntity.WatchedAttributes.SetDouble("temporalStability", Math.Min(1, stability + restored));
    }
}
