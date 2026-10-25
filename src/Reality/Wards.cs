using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;

namespace Backrooms.Reality;

/// <summary>
/// Ward tiers (docs/design/progression/plan.md section 2). Every level asks a ward tier of whoever stays in it
/// (<see cref="WorldLayout.WardTier"/>); a wanderer's tier is the best anchor worn round the neck, plus half a tier for a
/// full set of vanilla armour of at least that tier. A level more than the wanderer's tier is "beyond" them: their stability
/// drains (<see cref="Deficit"/>), Almond Water steadies them less (<see cref="Drink"/>), and at zero the level's hunters come
/// and in the end they black out (<see cref="ZeroSystem"/>).
///
/// The drain is calibrated to vanilla's own formula (EntityBehaviorTemporalStabilityAffected.OnGameTick): each game tick the
/// behaviour sets V = (T - V) * dt, where T = area stability - 1 and dt is the tick's seconds, then moves the player's stability
/// by V / 800 while V is negative (V / 200 when positive). V settles at T * dt / (1 + dt), and since the ticks of a second add
/// up to one second of dt, a negative area T drains 1 / (800 * (1 + dt)) of a full bar per second, however many ticks there
/// are (dt = 1/30 on the server). So full to empty takes 800 * (1 + dt) / (1 - area) seconds.
/// </summary>
public static class WardTiers
{
    /// <summary>Watched attribute (a double, the whole tier) that stands in for worn gear on a straw dummy, which has no inventory.</summary>
    public const string TestKey = "backrooms:testWard";

    /// <summary>Real seconds from a full bar to zero one tier beyond, and two or more beyond.</summary>
    public const double OneBeyondSeconds = 600, TwoBeyondSeconds = 180;

    /// <summary>Vanilla's divisor for a falling bar and the server's tick (seconds), as in the class comment.</summary>
    private const double VanillaDivisor = 800, TickSeconds = 1.0 / 30;

    /// <summary>The baseline the deficits are measured from: the middle of the levels' own stabilities (0.55 to 0.95).</summary>
    private const double ReferenceBaseline = 0.75;

    /// <summary>The area stability that empties a bar in the given number of seconds.</summary>
    public static double AreaForSeconds(double seconds) => 1 - VanillaDivisor * (1 + TickSeconds) / seconds;

    /// <summary>
    /// What a level beyond a wanderer's tier takes off its area stability: enough that a level with the typical baseline
    /// empties a full bar in <see cref="OneBeyondSeconds"/> (one tier beyond) or <see cref="TwoBeyondSeconds"/> (two or more).
    /// A worse place drains faster, a kinder one slower. Nothing at or below the tier.
    /// </summary>
    public static float Deficit(int beyond)
    {
        if (beyond <= 0) return 0;
        return (float)(ReferenceBaseline - AreaForSeconds(beyond == 1 ? OneBeyondSeconds : TwoBeyondSeconds));
    }

    /// <summary>How many whole tiers a level is beyond a tier of ward (half a tier beyond counts as one).</summary>
    public static int Beyond(double tier, int levelTier) => (int)Math.Ceiling(Math.Max(0, levelTier - tier) - 1e-9);

    /// <summary>The highest stability Almond Water can bring someone to: full at or below their tier, 0.6 one beyond, 0.3 two or more.</summary>
    public static double RestoreCeiling(int beyond) => beyond <= 0 ? 1.0 : beyond == 1 ? 0.6 : 0.3;

    /// <summary>How much of a drink's stability it gives: all at or below the tier, less the further beyond, never under a fifth.</summary>
    public static double RestoreFactor(int beyond) => Math.Max(0.2, 1 - 0.4 * Math.Max(0, beyond));

    // ================= What someone wears =================

    /// <summary>The tier of an anchor (<c>backrooms:anchor-copper</c>, <c>-bronze</c>, <c>-iron</c>): 1, 2, 3; 0 for anything else.</summary>
    public static int AnchorTier(ItemStack stack)
    {
        AssetLocation code = stack?.Collectible?.Code;
        if (code == null || code.Domain != "backrooms" || !code.Path.StartsWith("anchor-", StringComparison.Ordinal)) return 0;
        return code.Path.Substring(7) switch { "copper" => 1, "bronze" => 2, "iron" => 3, _ => 0 };
    }

    /// <summary>
    /// The tier of a piece of vanilla armour (<c>armor-body-plate-iron</c>): leather and hides 1; copper and the bronzes 2; iron,
    /// meteoric iron and steel 3; anything else (pleather, linen, wood, gold) 0. Read from the material in the code.
    /// </summary>
    public static int ArmourTier(ItemStack stack)
    {
        AssetLocation code = stack?.Collectible?.Code;
        if (code == null || !code.Path.StartsWith("armor-", StringComparison.Ordinal)) return 0;
        int best = 0;
        foreach (string token in code.Path.Split('-'))
        {
            int tier = token switch
            {
                "leather" or "hide" => 1,
                "copper" or "tinbronze" or "bismuthbronze" or "blackbronze" => 2,
                "iron" or "meteoriciron" or "steel" => 3,
                _ => 0,
            };
            best = Math.Max(best, tier);
        }
        return best;
    }

    /// <summary>The worn anchor's tier and the tier of the armour set (the lowest of head, body and legs; 0 unless all three are worn).</summary>
    public static (int Anchor, int Armour) Worn(Entity entity)
    {
        if (entity is not EntityPlayer { Player: { } player }) return (0, 0);
        if (player.InventoryManager?.GetOwnInventory(GlobalConstants.characterInvClassName) is not { } worn) return (0, 0);
        int anchor = AnchorTier(worn[(int)EnumCharacterDressType.Neck]?.Itemstack);
        int head = ArmourTier(worn[(int)EnumCharacterDressType.ArmorHead]?.Itemstack);
        int body = ArmourTier(worn[(int)EnumCharacterDressType.ArmorBody]?.Itemstack);
        int legs = ArmourTier(worn[(int)EnumCharacterDressType.ArmorLegs]?.Itemstack);
        return (anchor, Math.Min(head, Math.Min(body, legs)));
    }

    /// <summary>
    /// The ward tier of a wanderer: the best anchor worn, and half a tier more for a full armour set of at least that tier
    /// (so a leather set and a copper anchor make 1.5). A straw dummy's is its <see cref="TestKey"/>, if it has one.
    /// </summary>
    public static double TierOf(Entity entity)
    {
        if (entity == null) return 0;
        if (entity.WatchedAttributes.HasAttribute(TestKey)) return entity.WatchedAttributes.GetDouble(TestKey);
        (int anchor, int armour) = Worn(entity);
        return anchor + (armour >= Math.Max(1, anchor) ? 0.5 : 0);
    }

    // ================= Where someone is =================

    /// <summary>The ward tier of the place an entity stands in, or 0 outside a Backrooms world.</summary>
    public static int LevelTierAt(WorldLayout layout, double x, double z) =>
        layout?.WardTierAt(WorldLayout.MacroOf((int)Math.Floor(x)), WorldLayout.MacroOf((int)Math.Floor(z))) ?? 0;

    /// <summary>Whether the Backrooms leave someone be here: Level 0, the Hub, Level 974 and the Snackrooms never drain or black out anyone.</summary>
    public static bool SafePlace(WorldLayout layout, double x, double z)
    {
        int mx = WorldLayout.MacroOf((int)Math.Floor(x)), mz = WorldLayout.MacroOf((int)Math.Floor(z));
        int level = layout.LevelAt(mx, mz);
        return level is 0 or WorldLayout.Hub or WorldLayout.Level974 || level == 6 && layout.IsSnackrooms(mx, mz);
    }

    /// <summary>
    /// Where someone who blacks out wakes: the level before the one they lost their grip in. Rings: one up (Level 1: Level 0).
    /// The places no ring reaches are woken in the level their way in came from (docs/design/new-levels/LINKS.md): the city from
    /// 10, the Poolrooms from the hotel (5), Motion from 9, Level ! from the Poolrooms, Fun from 1, the End from 4, 3999
    /// from the Poolrooms, 188 from 1.
    /// </summary>
    public static int WakeLevel(int level) => level switch
    {
        11 => 10,
        WorldLayout.Poolrooms => 5,
        WorldLayout.Motion => 9,
        WorldLayout.RunLevel => WorldLayout.Poolrooms,
        WorldLayout.FunLevel => 1,
        WorldLayout.TheEnd => 4,
        WorldLayout.Level3999 => WorldLayout.Poolrooms,
        WorldLayout.Level188 => 1,
        <= 0 => 0,
        > 11 => 0,
        _ => level - 1,
    };

    // ================= Almond Water =================

    /// <summary>
    /// Server: a drink steadies someone by <paramref name="amount"/>, less the further beyond their ward tier they stand, and never
    /// to more than <see cref="RestoreCeiling"/> (a bar already above the ceiling is left as it is).
    /// </summary>
    public static void Drink(Entity entity, double amount)
    {
        int beyond = 0;
        if (BackroomsWorld.IsBackroomsClimate(entity.World.Config))
        {
            WorldLayout layout = BackroomsWorld.CreateLayout(entity.World);
            beyond = Beyond(TierOf(entity), LevelTierAt(layout, entity.Pos.X, entity.Pos.Z));
        }
        double stability = entity.WatchedAttributes.GetDouble("temporalStability", 1);
        double restored = stability + amount * (amount > 0 ? RestoreFactor(beyond) : 1);
        double ceiling = Math.Max(stability, RestoreCeiling(beyond));
        entity.WatchedAttributes.SetDouble("temporalStability", Math.Min(ceiling, restored));
    }
}
