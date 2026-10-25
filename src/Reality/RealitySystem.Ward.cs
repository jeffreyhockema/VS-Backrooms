using System;
using System.Globalization;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Server;

namespace Backrooms.Reality;

/// <summary>The <c>/backrooms ward</c> command: what tier someone holds, what the level asks, and what that costs.</summary>
public partial class RealitySystem
{
    private void RegisterWardCommand(ICoreServerAPI sapi)
    {
        sapi.ChatCommands.Get("backrooms")?
            .BeginSubCommand("ward")
                .WithDescription("Your ward tier (the best anchor worn, and half a tier for a full armour set of that tier), what tier the level you are in asks, how many tiers beyond you it is, the stability it takes off, and how long a full bar lasts here. From the console it is about the latest straw dummy. 'ward <0-3>' gives the straw dummy that ward (a test stand-in for gear), 'ward clear' takes it away")
                .WithArgs(sapi.ChatCommands.Parsers.OptionalWord("tier"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(args => OnWardCommand(sapi, args))
            .EndSubCommand();
    }

    private TextCommandResult OnWardCommand(ICoreServerAPI sapi, TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string word = args.Parsers[0].IsMissing ? "" : ((string)args[0]).Trim().ToLowerInvariant();
        Entity who = args.Caller.Entity;
        if (word != "" || who == null)
        {
            // From the console, or setting a stand-in: the latest straw dummy
            who = sapi.World.LoadedEntities.Values.Where(e => e.Alive && Entities.Senses.IsTestTarget(e)).OrderBy(e => e.EntityId).LastOrDefault();
            if (who == null) return TextCommandResult.Error("No straw dummy (put one down with /backrooms dummy place)");
        }
        if (word == "clear") who.WatchedAttributes.RemoveAttribute(WardTiers.TestKey);
        else if (word != "")
        {
            if (!double.TryParse(word, NumberStyles.Float, CultureInfo.InvariantCulture, out double set) || set < 0 || set > 3)
                return TextCommandResult.Error("A ward is a number from 0 to 3 (halves allowed), or 'clear'");
            who.WatchedAttributes.SetDouble(WardTiers.TestKey, set);
        }

        double tier = WardTiers.TierOf(who);
        (int anchor, int armour) = WardTiers.Worn(who);
        int mx = WorldLayout.MacroOf((int)Math.Floor(who.Pos.X)), mz = WorldLayout.MacroOf((int)Math.Floor(who.Pos.Z));
        int level = layout.LevelAt(mx, mz), levelTier = layout.WardTierAt(mx, mz);
        int beyond = WardTiers.Beyond(tier, levelTier);
        float deficit = WardTiers.Deficit(beyond);
        float baseline = layout.StabilityAt(who.Pos.X, who.Pos.Y, who.Pos.Z, geometry.FloorY) - 1.3f * (float)ShiftStrength;
        double area = baseline - deficit;
        string lasts = area < 1 ? (800 * (1 + 1.0 / 30) / (1 - area)).ToString("0", CultureInfo.InvariantCulture) + " s" : "for ever";
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture,
            "Ward: {0} #{1} tier {2:0.0} (anchor {3}, armour {4}{5}); Level {6} asks tier {7}; {8} beyond; deficit {9:0.00}; area stability {10:0.00} before it, {11:0.00} with it; a full bar lasts {12}",
            who is EntityPlayer ep ? ep.Player?.PlayerName : "dummy", who.EntityId, tier, anchor, armour,
            who.WatchedAttributes.HasAttribute(WardTiers.TestKey) ? ", test ward" : "", WorldLayout.DisplayNumber(level), levelTier, beyond, deficit, baseline, area, lasts));
    }
}
