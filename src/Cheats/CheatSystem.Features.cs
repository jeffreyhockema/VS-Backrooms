using System;
using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Server;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// <c>/backrooms feature &lt;code&gt; [radius]</c>: to the nearest of one of the special places of the level you are in
/// (<see cref="FeatureCatalog"/>, the cheat menu's "Go to feature (in this level)"), standing beside or in it; and
/// <c>/backrooms features</c>, which lists the codes of the level you are in.
/// </summary>
public partial class CheatSystem
{
    private void RegisterFeatures(IChatCommand command, CommandArgumentParsers parsers)
    {
        command
            .BeginSubCommand("feature")
                .WithDescription("Teleports you to the nearest of a special place of the level you are in (a set piece, room, zone or way out: /backrooms features lists this level's), within the radius if given; back undoes it")
                .RequiresPlayer()
                .WithArgs(parsers.Word("code"), parsers.OptionalInt("radius", -1))
                .HandleWith(OnFeatureCommand)
            .EndSubCommand()
            .BeginSubCommand("features")
                .WithDescription("Lists the special places of the level you are in that /backrooms feature goes to")
                .RequiresPlayer()
                .HandleWith(args =>
                {
                    if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
                    int level = LevelOf(args.Caller.Entity);
                    var entries = FeatureCatalog.ForLevel(level);
                    return entries.Length == 0
                        ? TextCommandResult.Success($"Level {WorldLayout.DisplayNumber(level)} has no features listed")
                        : TextCommandResult.Success($"Level {WorldLayout.DisplayNumber(level)}: " + string.Join(", ", entries.Select(e => $"{e.Code} ({e.Name})")));
                })
            .EndSubCommand();
    }

    private int LevelOf(Entity entity) =>
        layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z)));

    private TextCommandResult OnFeatureCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        string code = ((string)args[0]).Trim().ToLowerInvariant();
        Entity entity = args.Caller.Entity;
        int gx = (int)Math.Floor(entity.Pos.X), gz = (int)Math.Floor(entity.Pos.Z);
        int level = LevelOf(entity);
        string here = $"Level {WorldLayout.DisplayNumber(level)}";
        if (FeatureCatalog.Find(level, code) is not { } entry)
        {
            var elsewhere = FeatureCatalog.All.Where(e => e.Code == code).Select(e => WorldLayout.DisplayNumber(e.Level)).ToArray();
            return TextCommandResult.Error(elsewhere.Length > 0
                ? $"{code} is in Level {string.Join(", ", elsewhere)}, not {here} (/backrooms features lists this level's)"
                : $"No feature {code} (/backrooms features lists this level's)");
        }
        int radius = (int)args[1] < 0 ? entry.Radius : Math.Clamp((int)args[1], 16, 16384);

        FeatureFinder.Hit hit = finder.Feature(entry.Code, gx, gz, radius, level, (ulong)sapi.World.Rand.NextInt64());
        if (hit == null)
            return TextCommandResult.Error(finder.Error
                ?? (finder.Stopped
                    ? $"No {entry.Name} found in the first {Math.Min(radius, FeatureFinder.TileScanMaxRadius)} blocks searched in {here} (the search stopped after {FeatureFinder.TileScanSeconds} s)"
                    : $"No {entry.Name} within {radius} blocks in {here}"));
        if (!finder.Resolve(hit, level)) return TextCommandResult.Error($"Found a {entry.Name} at {FromSpawn(hit.X, hit.Z)}, but nowhere to stand near it");

        var player = (IServerPlayer)args.Caller.Player;
        var (sx, sz) = hit.Stand.Value;
        if (hit.FeetY is { } feet) Teleport(player, sx + 0.5, feet, sz + 0.5);
        else Teleport(player, sx, sz, level);

        string detail = hit.Detail;
        if (detail.Length == 0 && (sx, sz) != (hit.X, hit.Z)) detail = $" (heading {FeatureFinder.Heading(sx, sz, hit.X, hit.Z)} looks toward it)";
        int distance = (int)Math.Sqrt((double)(hit.X - gx) * (hit.X - gx) + (double)(hit.Z - gz) * (hit.Z - gz));
        string where = hit.Elsewhere ? $"none within {radius} blocks, so one elsewhere in {here}, {distance} blocks away" : $"{distance} blocks from where you were";
        return TextCommandResult.Success($"{entry.Name}{detail}, {where} ({FromSpawn(hit.X, hit.Z)})");
    }
}
