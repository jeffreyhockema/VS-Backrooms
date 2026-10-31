using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using HarmonyLib;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// Envenomed weapons (docs/design/entity-ai-overhaul/README.md section 7). A Deathmoth quill in the crafting grid
/// with a spear gives the same spear with the stack attribute <c>backrooms:venom = 3</c>, and with eight arrows gives
/// eight arrows with <c>backrooms:venom = 1</c> (recipes/grid/venom-*.json, written by tools/gen_materials.py). Every
/// hit that wounds a living thing adds the spider's venom through the game's own damage-over-time effects
/// (<see cref="EntityBehaviorHealth.ApplyDoTEffect(EnumDamageSource, EnumDamageType, int, float, TimeSpan, int, EnumDamageOverTimeEffectType)"/>):
/// 1 damage every 2 seconds for 6 seconds. A spear loses a charge per hit (the attribute goes at 0); an arrow is
/// spent by the hit anyway.
///
/// Harmony postfixes do it, as the game has no event for a creature being hurt and the items are vanilla ones:
/// <c>Entity.ReceiveDamage</c> (and the <c>EntityAgent</c> override of it; server: who struck, with what) and <c>CollectibleObject.GetHeldItemName</c> /
/// <c>GetHeldItemInfo</c> (the name shows "(envenomed, N)", the help says what it does). Saves: the attribute is
/// read with a default of 0 and written only by the recipes and this code.
/// </summary>
public class VenomSystem : ModSystem
{
    /// <summary>The stack attribute: how many hits of venom are left.</summary>
    public const string Key = "backrooms:venom";

    public const string ByKey = "backrooms:venomBy";
    public const string AtKey = "backrooms:venomAtMs";

    private const string HarmonyId = "backroomsss.venom";

    /// <summary>Total damage, how long it takes and in how many ticks: 1 every 2 s for 6 s.</summary>
    public const float Damage = 3f;
    public const int Ticks = 3;
    public static readonly TimeSpan Duration = TimeSpan.FromSeconds(6);

    // (One per side: in single player the client and the server share a process, so the first to start patches and
    // the last to go unpatches, as ProtectionSystem does)
    private static readonly object patchLock = new();
    private static int patchUsers;
    private bool patched;

    public override void Start(ICoreAPI api)
    {
        lock (patchLock)
        {
            patched = true;
            if (patchUsers++ > 0) return;
            var harmony = new Harmony(HarmonyId);
            harmony.UnpatchAll(HarmonyId);
            harmony.Patch(AccessTools.Method(typeof(Entity), nameof(Entity.ReceiveDamage), new[] { typeof(DamageSource), typeof(float) }),
                postfix: new HarmonyMethod(typeof(VenomSystem), nameof(ReceiveDamagePostfix)));
            // (EntityAgent overrides it only to call the base, which the JIT may inline there: patch the override too,
            // and the postfix lets only one of the two do the work)
            harmony.Patch(AccessTools.DeclaredMethod(typeof(EntityAgent), nameof(Entity.ReceiveDamage), new[] { typeof(DamageSource), typeof(float) }),
                postfix: new HarmonyMethod(typeof(VenomSystem), nameof(ReceiveDamagePostfix)));
            harmony.Patch(AccessTools.Method(typeof(CollectibleObject), nameof(CollectibleObject.GetHeldItemName), new[] { typeof(ItemStack) }),
                postfix: new HarmonyMethod(typeof(VenomSystem), nameof(HeldItemNamePostfix)));
            harmony.Patch(AccessTools.Method(typeof(CollectibleObject), nameof(CollectibleObject.GetHeldItemInfo), new[] { typeof(ItemSlot), typeof(StringBuilder), typeof(IWorldAccessor), typeof(bool) }),
                postfix: new HarmonyMethod(typeof(VenomSystem), nameof(HeldItemInfoPostfix)));
        }
    }

    // After the BackroomsModSystem that creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.2;

    public override void StartServerSide(ICoreServerAPI api)
    {
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("materialstest")
                .WithDescription("Dev test of the harvest materials (works from the console): what the harvestable creatures are set to leave, 300 broken hive hearts and remnants (in a Level 5 spot it finds, and in the spawn's level), and an envenomed arrow hitting a Death Rat (its poison, in the log)")
                .HandleWith(args => OnMaterialsTest(api))
            .EndSubCommand();
    }

    private static TextCommandResult OnMaterialsTest(ICoreServerAPI api)
    {
        IWorldAccessor world = api.World;
        void Say(string text) => api.Logger.Notification("[backrooms] materialstest: " + text);

        // What the creatures are set to leave, and the time the knife takes
        foreach (string code in new[] { "giantspider", "deathmoth-female", "deathmoth-male", "hound", "deathrat" })
        {
            EntityProperties type = world.GetEntityType(new AssetLocation("backrooms:" + code));
            if (type == null) { Say(code + ": no such entity"); continue; }
            JsonObject server = type.Server?.BehaviorsAsJsonObj?.FirstOrDefault(x => x["code"].AsString() == "harvestable");
            bool client = type.Client?.BehaviorsAsJsonObj?.Any(x => x["code"].AsString() == "harvestable") == true;
            if (server == null) { Say($"{code}: server has no harvestable; client has one: {client}"); continue; }
            BlockDropItemStack[] drops = server["drops"].AsObject<BlockDropItemStack[]>(null);
            Say($"{code}: server harvest {server["duration"].AsFloat(5):0.#} s, client has harvestable: {client}; drops: "
                + string.Join(", ", (drops ?? Array.Empty<BlockDropItemStack>()).Select(d => $"{d.Code} avg {d.Quantity.avg} var {d.Quantity.var}")));
        }

        // Broken hive hearts and remnants, where the level is 5 and where it is not
        int level5x = int.MinValue, level5z = 0;
        for (int dz = -40000; dz <= 40000 && level5x == int.MinValue; dz += 256)
            for (int dx = -40000; dx <= 40000; dx += 256)
                if (Backrooms.Salvage.ProtectionSystem.LevelAt(world, dx, dz) == BlockMothHiveHeart.JellyLevel) { level5x = dx; level5z = dz; break; }
        foreach (var (label, x, z) in new[] { ("a Level 5 spot", level5x, level5z), ("the spawn", 0, 0) })
        {
            if (x == int.MinValue) { Say(label + ": none found"); continue; }
            var pos = new BlockPos(x, 100, z);
            var quills = new List<int>();
            int jellies = 0;
            for (int i = 0; i < 300; i++)
            {
                ItemStack[] hearts = BlockMothHiveHeart.HiveHeartDrops(world, pos, null, 1f);
                quills.Add(hearts.Where(d => d.Collectible.Code.Path == "mothquill").Sum(d => d.StackSize));
                jellies += hearts.Count(d => d.Collectible.Code.Path == "mothjelly");
            }
            var sinews = Enumerable.Range(0, 300).Select(_ => BlockClumpRemnant.RemnantDrops(world, pos, null, 1f).Sum(d => d.StackSize)).ToList();
            Say($"{label} ({x},{z}, level {Backrooms.Salvage.ProtectionSystem.LevelAt(world, x, z)}): hive heart quills {quills.Min()}..{quills.Max()} (mean {quills.Average():0.00}), jelly {jellies}/300; remnant sinew {sinews.Min()}..{sinews.Max()} (mean {sinews.Average():0.00})");
        }

        // An envenomed arrow, then a plain one, into a hare
        try
        {
            Entity rat = world.ClassRegistry.CreateEntity(world.GetEntityType(new AssetLocation("game:hare-european-adult-male")));
            rat.Pos.SetPos(world.DefaultSpawnPosition.X, world.DefaultSpawnPosition.Y + 1, world.DefaultSpawnPosition.Z);
            world.SpawnEntity(rat);
            var health = rat.GetBehavior<EntityBehaviorHealth>();
            Item arrowItem = world.GetItem(new AssetLocation("game:arrow-flint"));
            var arrow = (EntityProjectile)world.ClassRegistry.CreateEntity(world.GetEntityType(new AssetLocation("game:arrow-flint")));
            var plain = new ItemStack(arrowItem, 1);
            var coated = new ItemStack(arrowItem, 1);
            coated.Attributes.SetInt(Key, 1);
            Say($"name of the coated arrow: {coated.GetName()} (plain: {plain.GetName()})");
            // (The coated one first: a second hit at once falls in the target's invulnerability frames)
            arrow.ProjectileStack = coated;
            rat.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Entity, SourceEntity = arrow, Type = EnumDamageType.PiercingAttack }, 0.1f);
            Say($"envenomed arrow: DoT effects {health.ActiveDoTEffects.Count}, health {health.Health:0.0}, arrow's charges left {Charges(coated)}");
            int n = 0;
            void Tick(float dt)
            {
                Say($"rat after {++n * 2} s: health {health.Health:0.00}, DoT effects {health.ActiveDoTEffects.Count}, alive {rat.Alive}");
                if (n < 5) world.RegisterCallback(Tick, 2000);
                else rat.Die(EnumDespawnReason.Removed);
            }
            world.RegisterCallback(Tick, 2000);
        }
        catch (Exception e)
        {
            Say("arrow test failed: " + e);
        }
        return TextCommandResult.Success("materialstest: see the log");
    }

    public override void Dispose()
    {
        if (!patched) return;
        patched = false;
        lock (patchLock)
            if (--patchUsers == 0) new Harmony(HarmonyId).UnpatchAll(HarmonyId);
    }

    /// <summary>Hits of venom left on a stack (0 for none).</summary>
    public static int Charges(ItemStack stack) => stack?.Attributes?.GetInt(Key, 0) ?? 0;

    private static bool IsArrow(ItemStack stack) => stack?.Collectible?.Code?.Path.StartsWith("arrow", System.StringComparison.Ordinal) == true;

    /// <summary>Takes a charge off a stack: the attribute is removed at 0.</summary>
    private static void Spend(ItemStack stack)
    {
        int left = Charges(stack) - 1;
        if (left <= 0) stack.Attributes.RemoveAttribute(Key);
        else stack.Attributes.SetInt(Key, left);
    }

    [ThreadStatic] private static DamageSource lastDamage;
    [ThreadStatic] private static Entity lastTarget;
    [ThreadStatic] private static long lastMoment;

    public static void ReceiveDamagePostfix(Entity __instance, DamageSource damageSource, bool __result)
    {
        // (An agent's blow can come through both patches: the same blow on the same target in the same moment is one)
        long moment = __instance?.World?.ElapsedMilliseconds ?? 0;
        if (lastDamage == damageSource && lastTarget == __instance && lastMoment == moment) return;
        lastDamage = damageSource;
        lastTarget = __instance;
        lastMoment = moment;
        // (Not a heal, not a damage-over-time tick, not our own poison or anyone else's)
        if (!__result || damageSource == null || __instance?.Api?.Side != EnumAppSide.Server) return;
        if (damageSource.Type is EnumDamageType.Poison or EnumDamageType.Heal || damageSource.TicksPerDuration > 1) return;
        try
        {
            Entity striker = damageSource.SourceEntity;
            if (striker is EntityProjectile projectile)
            {
                ItemStack shot = projectile.ProjectileStack;
                if (Charges(shot) <= 0) return;
                if (Envenom(__instance, projectile.FiredBy ?? striker)) Spend(shot);
            }
            else if (striker is EntityPlayer player && damageSource.Source == EnumDamageSource.Player)
            {
                // A blow from the hand: the weapon held (never an arrow held in the hand)
                ItemSlot slot = Senses.RightHand(player);
                ItemStack held = slot?.Itemstack;
                if (Charges(held) <= 0 || IsArrow(held)) return;
                if (Envenom(__instance, player))
                {
                    Spend(held);
                    slot.MarkDirty();
                }
            }
        }
        catch (Exception e)
        {
            __instance.Api.Logger.Warning("[backrooms] venom: {0}", e.Message);
        }
    }

    /// <summary>Who killed something: the cause of the death, or, for a death by our poison (the stamp under ten seconds old), the player who envenomed it.</summary>
    public static EntityPlayer KillerOf(Entity victim, DamageSource source)
    {
        if (source?.GetCauseEntity() is EntityPlayer direct) return direct;
        if (source != null && source.GetCauseEntity() == null && source.Source == EnumDamageSource.Internal && source.Type == EnumDamageType.Poison
            && victim?.Attributes != null && victim.Attributes.HasAttribute(ByKey)
            && victim.World.ElapsedMilliseconds - victim.Attributes.GetLong(AtKey) < 10_000)
            return victim.World.GetEntityById(victim.Attributes.GetLong(ByKey)) as EntityPlayer;
        return null;
    }

    /// <summary>Poisons a living thing: 1 damage every 2 seconds for 6 seconds, starting over if it is still burning from before. Returns whether it took.</summary>
    public static bool Envenom(Entity target, Entity striker = null)
    {
        if (target is not { Alive: true }) return false;
        var health = target.GetBehavior<EntityBehaviorHealth>();
        if (health == null) return false;
        // (Who did it, for the bounty and the shame when it kills: read by the menace and faceling death handlers)
        if (striker != null && target.Attributes != null)
        {
            target.Attributes.SetLong(ByKey, striker.EntityId);
            target.Attributes.SetLong(AtKey, target.World.ElapsedMilliseconds);
        }
        // (Still burning: it starts over rather than adding up, and without a stopped effect left to tick once more)
        DamageOverTimeEffect burning = health.ActiveDoTEffects.FirstOrDefault(e => e.EffectType == (int)EnumDamageOverTimeEffectType.Poison && e.TicksLeft > 0);
        if (burning != null)
        {
            if (burning.TicksLeft < Ticks) burning.TicksLeft = Ticks;
            return true;
        }
        health.ApplyDoTEffect(EnumDamageSource.Internal, EnumDamageType.Poison, 0, Damage, Duration, Ticks, EnumDamageOverTimeEffectType.Poison);
        return true;
    }

    public static void HeldItemNamePostfix(ItemStack itemStack, ref string __result)
    {
        int charges = Charges(itemStack);
        if (charges <= 0 || __result == null) return;
        __result = IsArrow(itemStack) ? Lang.Get("backrooms:venom-name-arrow", __result) : Lang.Get("backrooms:venom-name", __result, charges);
    }

    public static void HeldItemInfoPostfix(ItemSlot inSlot, StringBuilder dsc)
    {
        ItemStack stack = inSlot?.Itemstack;
        int charges = Charges(stack);
        if (charges <= 0 || dsc == null) return;
        dsc.AppendLine(IsArrow(stack) ? Lang.Get("backrooms:venom-info-arrow") : Lang.Get("backrooms:venom-info", charges));
    }
}

