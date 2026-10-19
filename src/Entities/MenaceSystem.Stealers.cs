using System;
using System.Globalization;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// Test commands for the Skin-Stealer's hunger and the hard-to-hurt (AI overhaul, batch P2): <c>/backrooms feed</c> sets the
/// nearest Skin-Stealer fed or hungry; <c>/backrooms strike</c> hurts the nearest Backrooms creature as the caller (or, from
/// the console, the latest straw dummy) would, to see a stun, a Duller's window or the clear blood.
/// </summary>
public partial class MenaceSystem
{
    private void RegisterStealerCommands(ICoreServerAPI api, IChatCommand command)
    {
        var parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("feed")
                .WithDescription("Sets the nearest Skin-Stealer within 64 blocks (of you, or of the latest straw dummy) fed (docile, wearing the disguise, Ambient), hungry (it stalks, in its waxy skin) or says which it is: fed | hungry | status")
                .WithArgs(parsers.OptionalWord("what"))
                .HandleWith(OnFeedCommand)
            .EndSubCommand()
            .BeginSubCommand("strike")
                .WithDescription("Hurts the nearest living Backrooms creature within 16 blocks of you (or of the latest straw dummy) as you (or the dummy) would, by this much damage (default 6), and says what became of its health: a Skin-Stealer stuns at 5, a Duller outside its grab takes none")
                .WithArgs(parsers.OptionalFloat("damage"))
                .HandleWith(OnStrikeCommand)
            .EndSubCommand();
    }

    private TextCommandResult OnFeedCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        Entity who = args.Caller.Entity ?? LatestDummy(args);
        if (who == null) return TextCommandResult.Error("From the console, put a straw dummy down first (/backrooms dummy place <level>)");
        Entity stealer = sapi.World.GetNearestEntity(who.Pos.XYZ, 64, 32, e => e.Alive && e.Code.Path == "skinstealer");
        if (stealer?.GetBehavior<EntityBehaviorMenace>() is not { } menace) return TextCommandResult.Error("No Skin-Stealer within 64 blocks");
        string what = args.Parsers[0].IsMissing ? "status" : ((string)args[0]).Trim().ToLowerInvariant();
        switch (what)
        {
            case "fed":
                menace.Feed(SkinStealerFedHours);
                menace.Kind = Encounter.Ambient;
                SetLook(stealer, 1);
                break;
            case "hungry":
                menace.Starve();
                if (menace.Kind == Encounter.Ambient) menace.Kind = Encounter.Stalk;
                SetLook(stealer, 0);
                break;
            case "status":
                break;
            default:
                return TextCommandResult.Error("fed, hungry or status");
        }
        double until = stealer.Attributes.GetDouble(EntityBehaviorMenace.FedKey, 0), now = sapi.World.Calendar.TotalHours;
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "Skin-Stealer #{0}: {1}{2}, {3}",
            stealer.EntityId, menace.Fed ? "fed" : "hungry", menace.Fed ? $" for another {until - now:0.0} hours" : "", menace.Kind));
    }

    private static void SetLook(Entity entity, int look)
    {
        entity.WatchedAttributes.SetInt("textureIndex", look);
        entity.WatchedAttributes.MarkPathDirty("textureIndex");
    }

    private TextCommandResult OnStrikeCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        Entity who = args.Caller.Entity ?? LatestDummy(args);
        if (who == null) return TextCommandResult.Error("From the console, put a straw dummy down first (/backrooms dummy place <level>)");
        Entity victim = sapi.World.GetNearestEntity(who.Pos.XYZ, 16, 8, e => e.Alive && e != who && e.Code.Domain == "backrooms" && e.GetBehavior<EntityBehaviorMenace>() != null);
        if (victim == null) return TextCommandResult.Error("No living Backrooms creature within 16 blocks");
        float damage = args.Parsers[0].IsMissing ? 6 : (float)args[0];
        var health = victim.GetBehavior<EntityBehaviorHealth>();
        float before = health?.Health ?? 0;
        victim.ReceiveDamage(new DamageSource
        {
            Source = EnumDamageSource.Entity,
            SourceEntity = who,
            Type = EnumDamageType.BluntAttack,
            DamageTier = 1,
            KnockbackStrength = 0.1f,
        }, damage);
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "Struck {0} #{1} for {2:0.0}: health {3:0.0} -> {4:0.0}{5}",
            victim.Code.Path, victim.EntityId, damage, before, health?.Health ?? 0, victim.Alive ? "" : " (dead)"));
    }
}
