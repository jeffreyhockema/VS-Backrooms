using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// <c>/backrooms armourtest</c> (progression round, plan.md 3.5): what one blow of an entity does to a player in a vanilla
/// armour set, level by level. A straw dummy has no character inventory (vanilla's armour belongs to
/// <c>ModSystemWearableStats</c>, which only hooks players), so the vanilla pipeline is re-run here on the real items'
/// <c>ProtectionModifiers</c>: a blow lands on the head 20 %, the body 50 % or the legs 30 % of the time, only that piece
/// protects (flat reduction, then the relative share, each worn down per tier of the blow beyond the piece's), and a
/// slot with nothing in it protects nothing. The blow itself is what <see cref="AiTaskMenace"/> deals: the entity's base
/// damage x <see cref="Danger.Damage"/> x the world's damage setting, at its damage tier plus the depth bonus.
/// </summary>
public partial class MenaceSystem
{
    /// <summary>A player's health, and how the game picks the piece a blow lands on (head, body, legs).</summary>
    private const float PlayerHealth = 15;
    private static readonly double[] HitZones = { 0.2, 0.5, 0.3 };
    private static readonly string[] ZoneParts = { "head", "body", "legs" };

    /// <summary>The sets worth comparing: construction-material (game:armor-{head|body|legs}-...), as the plan's ladder goes.</summary>
    private static readonly string[] ArmourSets =
    {
        "none", "jerkin-leather", "sewn-leather", "lamellar-copper", "lamellar-tinbronze", "chain-copper", "chain-tinbronze",
        "plate-copper", "plate-tinbronze", "chain-iron", "plate-iron",
    };

    private void RegisterArmourCommands(ICoreServerAPI api, IChatCommand command)
    {
        var parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("armourtest")
                .WithDescription("What one blow of an entity does to a player (15 health) in vanilla armour at a level, and how many blows it takes, by the game's own armour rules (a dummy cannot wear any). Args: entity, level, set (e.g. sewn-leather, lamellar-tinbronze, plate-iron, none; default all of a ladder)")
                .WithArgs(parsers.Word("entity"), parsers.Word("level"), parsers.OptionalWord("set"))
                .HandleWith(OnArmourTestCommand)
            .EndSubCommand();
    }

    /// <summary>The base damage and damage tier the entity's task deals (the first of its tasks that has a damage).</summary>
    private static bool BaseHit(EntityProperties type, out float damage, out int tier)
    {
        damage = 0;
        tier = 0;
        foreach (JsonObject behaviour in type.Server?.BehaviorsAsJsonObj ?? Array.Empty<JsonObject>())
        {
            if (behaviour["code"].AsString() != "taskai") continue;
            foreach (JsonObject task in behaviour["aitasks"].AsArray() ?? Array.Empty<JsonObject>())
            {
                if (task["damage"].AsFloat(0) <= 0) continue;
                damage = task["damage"].AsFloat(0);
                tier = task["damageTier"].AsInt(0);
                return true;
            }
        }
        return false;
    }

    /// <summary>The damage a blow of this strength and tier leaves after one piece of armour (vanilla's ModSystemWearableStats.handleDamaged).</summary>
    private static float AfterPiece(float damage, int damageTier, ProtectionModifiers p)
    {
        if (p == null) return damage;
        float flat = p.FlatDamageReduction, relative = p.RelativeProtection;
        for (int i = 1; i <= damageTier; i++)
        {
            bool beyond = i > p.ProtectionTier;
            float flatLoss = p.PerTierFlatDamageReductionLoss?[beyond ? 1 : 0] ?? 0, relativeLoss = p.PerTierRelativeProtectionLoss?[beyond ? 1 : 0] ?? 0;
            if (beyond && p.HighDamageTierResistant)
            {
                flatLoss /= 2;
                relativeLoss /= 2;
            }
            flat -= flatLoss;
            relative *= 1 - relativeLoss;
        }
        damage = Math.Max(0, damage - flat);
        return damage * (1 - Math.Max(0, relative));
    }

    private TextCommandResult OnArmourTestCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string code = ((string)args[0]).Trim();
        if (!code.Contains(':')) code = "backrooms:" + code;
        EntityProperties type = types.GetValueOrDefault(code) ?? sapi.World.GetEntityType(new AssetLocation(code));
        if (type == null) return TextCommandResult.Error("No such entity: " + code);
        if (!BaseHit(type, out float baseDamage, out int baseTier)) return TextCommandResult.Error(code + " has no damaging task");
        string levelWord = ((string)args[1]).Trim();
        int level = WorldLayout.FromDisplayName(levelWord);
        if (level < 0) return TextCommandResult.Error("There is no Level " + levelWord);
        double danger = Danger.OfLevel(level);
        float hit = baseDamage * Danger.Damage(danger) * (float)Setting.Damage * GlobalConstants.CreatureDamageModifier;
        int tier = baseTier + Danger.TierBonus(danger);
        string[] sets = args.Parsers[2].IsMissing ? ArmourSets : new[] { ((string)args[2]).Trim().ToLowerInvariant() };

        var text = new StringBuilder();
        text.AppendFormat(CultureInfo.InvariantCulture, "armourtest {0} Level {1}: danger {2:0.00}, hit {3:0.0} at tier {4} against {5:0} health", code.Replace("backrooms:", ""), levelWord, danger, hit, tier, PlayerHealth);
        sapi.Logger.Notification("[backrooms] " + text);
        foreach (string set in sets)
        {
            string line = ArmourLine(code, levelWord, set, hit, tier);
            sapi.Logger.Notification("[backrooms] " + line);
            text.Append('\n').Append(line);
        }
        return TextCommandResult.Success(text.ToString());
    }

    private string ArmourLine(string entity, string level, string set, float hit, int tier)
    {
        float[] after = new float[3];
        var missing = new List<string>();
        for (int zone = 0; zone < 3; zone++)
        {
            ProtectionModifiers p = null;
            if (set != "none")
            {
                Item item = sapi.World.GetItem(new AssetLocation("game:armor-" + ZoneParts[zone] + "-" + set));
                if (item == null) missing.Add(ZoneParts[zone]);
                else p = item.GetCollectibleInterface<IWearableStatsSupplier>()?.GetProtectionModifiers(new DummySlot(new ItemStack(item)));
            }
            after[zone] = AfterPiece(hit, tier, p);
        }
        double mean = 0;
        for (int zone = 0; zone < 3; zone++) mean += HitZones[zone] * after[zone];
        // Blows to kill: on average (health over the mean blow), and the fewest (all on the worst piece) to the most (all on the best)
        string blows = mean <= 0.001 ? "never" : (PlayerHealth / mean).ToString("0.0", CultureInfo.InvariantCulture);
        int fewest = (int)Math.Ceiling(PlayerHealth / Math.Max(0.001f, after.Max())), most = after.Min() <= 0.001f ? 999 : (int)Math.Ceiling(PlayerHealth / after.Min());
        return string.Format(CultureInfo.InvariantCulture, "armourtest {0} L{1} {2}: head {3:0.0} body {4:0.0} legs {5:0.0}; mean {6:0.00}; blows to kill {7} ({8} to {9}){10}",
            entity.Replace("backrooms:", ""), level, set, after[0], after[1], after[2], mean, blows, fewest, most >= 999 ? "never" : most.ToString(CultureInfo.InvariantCulture),
            missing.Count > 0 ? " (no " + string.Join("/", missing) + " piece: bare there)" : "");
    }
}
