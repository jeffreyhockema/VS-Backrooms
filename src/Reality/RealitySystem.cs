using System;
using System.Text;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Reality;

/// <summary>
/// Reality Stability: Vintage Story's temporal stability, recast as how firmly a wanderer is anchored to the level
/// they are in. The game's own system does the work (the gear on the HUD, the distortion and whispers at low
/// stability, the damage at zero); this replaces where stability is high or low with the Backrooms' own geography,
/// and drains it everywhere during a Reality Shift.
/// </summary>
public partial class RealitySystem : ModSystem
{
    /// <summary>How much a full Reality Shift lowers stability everywhere.</summary>
    private const float ShiftDrain = 1.3f;

    private ICoreAPI api;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private SystemTemporalStability stabilitySystem;

    /// <summary>Server: the calendar's elapsed hours until which a forced shift lasts (not saved: a restart ends it).</summary>
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
            RegisterWardCommand(sapi); // (the "backrooms" command exists by now)
            Hook(sapi);
            sapi.Event.PlayerNowPlaying += player => player.Entity?.WatchedAttributes.SetDouble(RealityShift.ForcedUntilAttribute, forcedUntilHours);
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
        stabilitySystem = api.ModLoader.GetModSystem<SystemTemporalStability>();
        stabilitySystem.OnGetTemporalStability += OnGetStability;
    }

    public override void Dispose()
    {
        if (stabilitySystem != null) stabilitySystem.OnGetTemporalStability -= OnGetStability;
        stabilitySystem = null;
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
            player.Entity?.WatchedAttributes.SetDouble(RealityShift.ForcedUntilAttribute, forcedUntilHours);
        }
        cachedAtMs = -1000;
    }

    private float OnGetStability(float vanillaStability, double x, double y, double z)
    {
        // (A shift's own drain is floored where it always was; only the depth deficit goes far below)
        float stability = Math.Max(-0.5f, layout.StabilityAt(x, y, z, geometry.FloorY) - ShiftDrain * (float)ShiftStrength) - DepthDeficit(x, y, z);
        // (Far below zero on purpose: vanilla drains a bar by how far under 1 the area is, see WardTiers)
        return Math.Clamp(stability, -5f, 1.5f);
    }

    /// <summary>
    /// What a level beyond the ward tier of whoever stands at this spot takes off its stability (<see cref="WardTiers.Deficit"/>).
    /// The stability query carries only a position, so the wanderer is the player standing exactly there (the game's own queries
    /// for a player's stability pass its position); any other query, for a spot or a mob, has no deficit.
    /// </summary>
    private float DepthDeficit(double x, double y, double z)
    {
        int levelTier = WardTiers.LevelTierAt(layout, x, z);
        if (levelTier == 0) return 0;
        try
        {
            Entity who = PlayerAt(x, y, z);
            return who == null ? 0 : WardTiers.Deficit(WardTiers.Beyond(WardTiers.TierOf(who), levelTier));
        }
        catch (Exception)
        {
            return 0; // (asked from another thread while a player joins or leaves)
        }
    }

    /// <summary>The player whose feet are exactly at a spot, if any (on a client, only its own player).</summary>
    private Entity PlayerAt(double x, double y, double z)
    {
        static bool At(Entity e, double x, double y, double z) =>
            e != null && Math.Abs(e.Pos.X - x) < 1e-6 && Math.Abs(e.Pos.Y - y) < 1e-6 && Math.Abs(e.Pos.Z - z) < 1e-6;
        if (api is ICoreClientAPI capi) return At(capi.World.Player?.Entity, x, y, z) ? capi.World.Player.Entity : null;
        foreach (IPlayer player in api.World.AllOnlinePlayers)
            if (At(player.Entity, x, y, z)) return player.Entity;
        return null;
    }
}

/// <summary>
/// Almond Water steadies the mind: drinking it restores some of the drinker's stability. It is also the mod's general drink class
/// (docs/design/needs/README.md section 3), driven by the item's attributes: <c>stabilityRestored</c> (0.15 if absent), and with
/// thirst on <c>hydration</c>, <c>satietyWhenThirst</c> (the satiety it gives instead of its food value), <c>sleepAid</c> (drowsy at
/// once), <c>caffeineHours</c>, <c>taintChance</c> (gut rot), <c>leavesBottle</c> and <c>wardsDullers</c> (true if absent).
/// </summary>
public class ItemAlmondWater : Item
{
    /// <summary>The nutrition this drink has while thirst is on (a copy of its own with <c>satietyWhenThirst</c>), made once.</summary>
    private FoodNutritionProperties thirstProps;

    private double Stability => Backrooms.Needs.Water.Drinks.StabilityOf(this);

    /// <summary>With thirst on a drink is no meal: its satiety is <c>satietyWhenThirst</c> (an item without the attribute keeps its own).</summary>
    public override FoodNutritionProperties GetNutritionProperties(IWorldAccessor world, ItemStack itemstack, Entity forEntity)
    {
        FoodNutritionProperties props = base.GetNutritionProperties(world, itemstack, forEntity);
        if (props == null || Attributes?["satietyWhenThirst"].Exists != true || !Backrooms.Needs.Needs.ThirstOn(world)) return props;
        if (thirstProps == null)
        {
            thirstProps = props.Clone();
            thirstProps.Satiety = Attributes["satietyWhenThirst"].AsFloat(0);
            thirstProps.SaturationLossDelay = props.SaturationLossDelay;
        }
        return thirstProps;
    }

    /// <summary>The tooltip gains the hydration, and the stability, a drink gives.</summary>
    public override void GetHeldItemInfo(ItemSlot inSlot, StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
        Backrooms.Needs.Water.Drinks.AppendHydrationInfo(this, world, dsc);
        double stability = Stability;
        if (Math.Abs(stability) > 0.0005)
            dsc.AppendLine(Lang.Get("backrooms:iteminfo-stability", (stability >= 0 ? "+" : "") + Math.Round(stability * 100)));
    }

    /// <summary>Drunk, not eaten: the game's own drinking sound (four swallows), as a held cup of water makes. The arm
    /// raises the bottle to the mouth with the same "eat" pose every drink in the game uses, and it still counts as food.</summary>
    protected override void tryEatBegin(ItemSlot slot, EntityAgent byEntity, ref EnumHandHandling handling, string eatSound = "eat", int eatSoundRepeats = 1)
    {
        base.tryEatBegin(slot, byEntity, ref handling, "drink", 4);
    }

    /// <summary>The hold-to-use hint reads "Drink", not "Eat".</summary>
    public override WorldInteraction[] GetHeldInteractionHelp(ItemSlot inSlot)
    {
        WorldInteraction[] help = base.GetHeldInteractionHelp(inSlot);
        foreach (WorldInteraction interaction in help)
        {
            if (interaction.ActionLangCode == "heldhelp-eat") interaction.ActionLangCode = "backrooms:heldhelp-drink";
        }
        return help;
    }

    protected override void tryEatStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity)
    {
        int before = slot.StackSize;
        base.tryEatStop(secondsUsed, slot, byEntity);
        if (byEntity.World.Side != EnumAppSide.Server || slot.StackSize >= before) return;

        // (The effects are shared with drinking straight from a water cooler or a fountain: Drinks.ApplyDrink)
        Backrooms.Needs.Water.Drinks.ApplyDrink(new ItemStack(this), byEntity, leavesBottle: true);
    }
}
