using System;
using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Server;
using Vintagestory.GameContent;
using Backrooms.Entities;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// Testing cheats. The server side adds more <c>/backrooms</c> subcommands (heal, kit, clear, home, find, nearest,
/// director, stat, exposure, noise, die); the client side (CheatSystem.Client.cs) is a menu (F7, or <c>.cheats</c>)
/// whose buttons send those and the other debug commands, so every action still goes through the server's privilege
/// check, plus a few view cheats that only touch the client.
/// </summary>
public partial class CheatSystem : ModSystem
{
    /// <summary>The places <c>/backrooms find</c> knows, with the level it looks in when none is given.</summary>
    public static readonly (string Code, string Name, int DefaultLevel)[] Features =
    {
        ("elevator", "Elevator", 3),
        ("stairs", "Stairs (L1/4/5)", 4),
        ("pit", "Pit", 0),
        ("descent", "Stairs down (L6)", 6),
        ("snackrooms", "Snackrooms (6.1)", 6),
        ("entryroom", "L7 entry room", 7),
    };

    /// <summary>
    /// What <c>/backrooms nearest</c> looks for round you, in your own level, and how far by default. The searches that
    /// look at every tile (ways out, caches) build each cell they pass, so they reach less far.
    /// </summary>
    public static readonly (string Code, string Name, int Radius, int MaxRadius)[] Targets =
    {
        ("gate", "Gate", 1024, 4096),
        ("threshold", "Way out", 384, 768),
        ("cache", "Unopened cache", 384, 768),
        ("refuge", "Refuge", 2048, 4096),
        ("den", "Den", 2048, 4096),
        ("redroom", "Red Room", 4096, 8192),
    };

    public static readonly string[] Stats = { "health", "food", "stability" };

    // A modest kit for getting about and testing the survival systems
    private static readonly (string Code, int Quantity)[] Kit =
    {
        ("game:torch-basic-lit-up", 8),
        ("game:candle", 4),
        ("backrooms:almondwater", 8),
        ("backrooms:cannedbeans", 4),
        ("backrooms:prybar", 1),
        ("backrooms:chalk", 1),
        ("backrooms:glassshiv", 1),
        ("backrooms:firesalt", 4),
    };

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.2;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
        });

        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        CommandArgumentParsers parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("heal")
                .WithDescription("Restores your health, food, body temperature and stability, and resets your time out (menace exposure)")
                .RequiresPlayer()
                .HandleWith(OnHealCommand)
            .EndSubCommand()
            .BeginSubCommand("kit")
                .WithDescription("Gives you a testing kit: light, food, a pry bar, chalk, a shiv and Firesalt")
                .RequiresPlayer()
                .HandleWith(OnKitCommand)
            .EndSubCommand()
            .BeginSubCommand("clear")
                .WithDescription("Removes every Backrooms creature within the radius (default 64)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalInt("radius", 64))
                .HandleWith(OnClearCommand)
            .EndSubCommand()
            .BeginSubCommand("home")
                .WithDescription("Teleports you to where you wake up")
                .RequiresPlayer()
                .HandleWith(OnHomeCommand)
            .EndSubCommand()
            .BeginSubCommand("find")
                .WithDescription("Teleports you beside a feature: " + string.Join(", ", Features.Select(f => f.Code)) + ". Give a level (a number, or !, fun, end, hub) to look in another level.")
                .RequiresPlayer()
                .WithArgs(parsers.WordRange("feature", Features.Select(f => f.Code).ToArray()), parsers.OptionalWord("level"))
                .HandleWith(OnFindCommand)
            .EndSubCommand()
            .BeginSubCommand("nearest")
                .WithDescription("Teleports you to the nearest " + string.Join(", ", Targets.Select(t => t.Code)) + " in the level you are in (within the radius, in blocks)")
                .RequiresPlayer()
                .WithArgs(parsers.WordRange("target", Targets.Select(t => t.Code).ToArray()), parsers.OptionalInt("radius", -1))
                .HandleWith(OnNearestCommand)
            .EndSubCommand()
            .BeginSubCommand("director")
                .WithDescription("Pauses (off) or resumes (on) the entity director: nothing new is put down near anyone, and no distant sounds play")
                .WithArgs(parsers.OptionalBool("on"))
                .HandleWith(OnDirectorCommand)
            .EndSubCommand()
            .BeginSubCommand("stat")
                .WithDescription("Sets your health or food (as a fraction of the most, 0-1) or your stability (0-1)")
                .RequiresPlayer()
                .WithArgs(parsers.WordRange("stat", Stats), parsers.Double("value"))
                .HandleWith(OnStatCommand)
            .EndSubCommand()
            .BeginSubCommand("exposure")
                .WithDescription("Sets how many in-game hours it is since you last rested (the time out that raises menace)")
                .RequiresPlayer()
                .WithArgs(parsers.Double("hours"))
                .HandleWith(OnExposureCommand)
            .EndSubCommand()
            .BeginSubCommand("noise")
                .WithDescription("Makes as much noise as you can: what hunts by sound comes to see")
                .RequiresPlayer()
                .HandleWith(args =>
                {
                    sapi.ModLoader.GetModSystem<MenaceSystem>()?.MakeNoise(args.Caller.Entity, 1);
                    return TextCommandResult.Success("CLANG");
                })
            .EndSubCommand()
            .BeginSubCommand("die")
                .WithDescription("Kills you, to test dying and waking up again")
                .RequiresPlayer()
                .HandleWith(args =>
                {
                    args.Caller.Entity.Die(EnumDespawnReason.Death, new DamageSource { Source = EnumDamageSource.Suicide, Type = EnumDamageType.Injury });
                    return TextCommandResult.Success();
                })
            .EndSubCommand();
    }

    private TextCommandResult OnHealCommand(TextCommandCallingArgs args)
    {
        Entity entity = args.Caller.Entity;
        if (entity.GetBehavior<EntityBehaviorHealth>() is { } health) health.Health = health.MaxHealth;
        if (entity.GetBehavior<EntityBehaviorHunger>() is { } hunger) hunger.Saturation = hunger.MaxSaturation;
        if (entity.GetBehavior<EntityBehaviorBodyTemperature>() is { } temperature) temperature.CurBodyTemperature = temperature.NormalBodyTemperature;
        entity.WatchedAttributes.SetDouble("temporalStability", 1);
        entity.Attributes.SetDouble(MenaceSystem.RestedKey, sapi.World.Calendar.TotalHours);
        return TextCommandResult.Success("Healed, fed, warmed, stable and rested");
    }

    private TextCommandResult OnKitCommand(TextCommandCallingArgs args)
    {
        IPlayer player = args.Caller.Player;
        int given = 0;
        foreach ((string code, int quantity) in Kit)
        {
            var location = new AssetLocation(code);
            CollectibleObject collectible = (CollectibleObject)sapi.World.GetItem(location) ?? sapi.World.GetBlock(location);
            if (collectible == null)
            {
                sapi.Logger.Warning("[backrooms] cheat kit: no item or block {0}", code);
                continue;
            }
            var stack = new ItemStack(collectible, quantity);
            if (!player.InventoryManager.TryGiveItemstack(stack, true)) sapi.World.SpawnItemEntity(stack, player.Entity.Pos.XYZ);
            given++;
        }
        return TextCommandResult.Success($"Gave {given} kinds of things");
    }

    private TextCommandResult OnClearCommand(TextCommandCallingArgs args)
    {
        int radius = Math.Clamp((int)args[0], 1, 512);
        Entity[] creatures = sapi.World.GetEntitiesAround(args.Caller.Entity.Pos.XYZ, radius, radius,
            e => e is not EntityPlayer && e.Alive && e.Code?.Domain == "backrooms");
        foreach (Entity creature in creatures) creature.Die(EnumDespawnReason.Removed);
        return TextCommandResult.Success($"Removed {creatures.Length} creatures within {radius} blocks");
    }

    private TextCommandResult OnHomeCommand(TextCommandCallingArgs args)
    {
        var player = (IServerPlayer)args.Caller.Player;
        FuzzyEntityPos home = player.GetSpawnPosition(false);
        if (home == null) return TextCommandResult.Error("You have nowhere to wake up");
        player.Entity.TeleportToDouble(home.X, home.Y, home.Z);
        return TextCommandResult.Success("Back where you woke up");
    }

    private TextCommandResult OnFindCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        string feature = (string)args[0];
        int level;
        if (args.Parsers[1].IsMissing || string.IsNullOrEmpty(args[1] as string)) level = Features.First(f => f.Code == feature).DefaultLevel;
        else
        {
            string number = (string)args[1];
            level = WorldLayout.FromDisplayName(number);
            if (level < 0) return TextCommandResult.Error($"There is no Level {number} here (0-11, 37, 94, !, fun, end, hub, 974, 3999 or 188)");
        }

        // The arrival search starts from a point picked by key, so a few keys find a few different places
        ulong key = (ulong)sapi.World.Rand.NextInt64();
        (int X, int Z)? arrival = null;
        if (feature == "snackrooms")
        {
            level = 6;
            for (int attempt = 0; attempt < 4 && arrival == null; attempt++, key = Hashing.Mix(key)) arrival = layout.FindSnackroomsArrival(key);
        }
        else if (feature == "entryroom")
        {
            level = 7;
            arrival = layout.FindEntryRoomArrival(key);
        }
        else
        {
            System.Func<Tile, bool> anchor = feature switch
            {
                "elevator" => t => t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator,
                "stairs" => t => t.Stair > 0 && t.Under == 0,
                "pit" => t => t.Kind == TileKind.Pit,
                _ => t => t.Under is >= Unders.Descent1 and <= Unders.Descent3,
            };
            // Without a match nearby, the search settles for any open floor: only take a spot that is beside one
            for (int attempt = 0; attempt < 4 && arrival == null; attempt++, key = Hashing.Mix(key))
            {
                if (layout.FindArrival(level, key, anchor) is { } spot && Beside(spot.X, spot.Z, anchor)) arrival = spot;
            }
        }
        if (arrival is not { } a) return TextCommandResult.Error($"Found no {feature} in Level {WorldLayout.DisplayNumber(level)} this time; try again, or another level");

        Teleport((IServerPlayer)args.Caller.Player, a.X, a.Z, level);
        string name = Features.First(f => f.Code == feature).Name;
        return TextCommandResult.Success($"{name}, Level {WorldLayout.DisplayNumber(level)} ({FromSpawn(a.X, a.Z)})");
    }

    private bool Beside(int x, int z, System.Func<Tile, bool> anchor) =>
        anchor(layout.TileAt(x - 1, z)) || anchor(layout.TileAt(x + 1, z)) || anchor(layout.TileAt(x, z - 1)) || anchor(layout.TileAt(x, z + 1));

    private TextCommandResult OnNearestCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        var target = Targets.First(t => t.Code == (string)args[0]);
        int radius = (int)args[1] < 0 ? target.Radius : Math.Clamp((int)args[1], 16, target.MaxRadius);
        Entity entity = args.Caller.Entity;
        int gx = (int)Math.Floor(entity.Pos.X), gz = (int)Math.Floor(entity.Pos.Z);
        int level = layout.LevelAt(WorldLayout.MacroOf(gx), WorldLayout.MacroOf(gz));

        string detail = "";
        (int X, int Z)? found;
        switch (target.Code)
        {
            case "gate":
                var gate = layout.NearestGate(gx, gz, level, radius);
                found = gate is { } g ? (g.X, g.Z) : null;
                if (gate != null) detail = $" to Level {WorldLayout.DisplayNumber(gate.Value.To)}";
                break;
            case "threshold": found = layout.NearestThreshold(gx, gz, level, radius); break;
            case "cache": found = layout.NearestCache(gx, gz, level, radius); break;
            case "refuge": found = layout.NearestRefuge(gx, gz, level, radius); break;
            case "den":
                found = NearestCell(gx, gz, radius, (mx, mz) => layout.LevelAt(mx, mz) == level && layout.DenAt(mx, mz) != DenKind.None);
                if (found is { } d) detail = $" ({layout.DenAt(WorldLayout.MacroOf(d.X), WorldLayout.MacroOf(d.Z))})";
                break;
            default:
                if (level != 0) return TextCommandResult.Error("Red Rooms are only in Level 0");
                found = NearestCell(gx, gz, radius, layout.IsRedRoom);
                break;
        }
        if (found is not { } f) return TextCommandResult.Error($"No {target.Name.ToLowerInvariant()} within {radius} blocks in Level {WorldLayout.DisplayNumber(level)}");
        if (StandNear(f.X, f.Z, level) is not { } stand) return TextCommandResult.Error($"Found a {target.Name.ToLowerInvariant()} at {FromSpawn(f.X, f.Z)}, but nowhere to stand near it");

        int distance = (int)Math.Sqrt((double)(f.X - gx) * (f.X - gx) + (double)(f.Z - gz) * (f.Z - gz));
        Teleport((IServerPlayer)args.Caller.Player, stand.X, stand.Z, level);
        return TextCommandResult.Success($"{target.Name}{detail}, {distance} blocks from where you were ({FromSpawn(f.X, f.Z)})");
    }

    /// <summary>The middle of the nearest cell that matches, searching outward ring by ring.</summary>
    private static (int X, int Z)? NearestCell(int gx, int gz, int radius, System.Func<int, int, bool> match)
    {
        int mx0 = WorldLayout.MacroOf(gx), mz0 = WorldLayout.MacroOf(gz), rings = radius / WorldLayout.MacroSize + 1;
        (int X, int Z)? best = null;
        long bestDistance = long.MaxValue;
        for (int r = 0; r <= rings && best == null; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || !match(mx0 + dx, mz0 + dz)) continue;
                    int x = (mx0 + dx) * WorldLayout.MacroSize + WorldLayout.MacroSize / 2, z = (mz0 + dz) * WorldLayout.MacroSize + WorldLayout.MacroSize / 2;
                    long distance = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                    if (distance < bestDistance && distance <= (long)radius * radius) (best, bestDistance) = ((x, z), distance);
                }
        return best;
    }

    /// <summary>The nearest open floor (or doorway) to a spot, within 8 blocks, in the same level.</summary>
    private (int X, int Z)? StandNear(int x, int z, int level)
    {
        for (int r = 0; r <= 8; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    Tile t = layout.TileAt(x + dx, z + dz);
                    if (t.Level == level && t.Kind is TileKind.Floor or TileKind.Doorway && !t.Sealed && t.Stack == 0 && t.Stair == 0
                        && t.Under == 0 && !t.SupplyBox && (t.Kind == TileKind.Doorway || t.Variant == 0)) return (x + dx, z + dz);
                }
        return null;
    }

    private void Teleport(IServerPlayer player, int x, int z, int level) =>
        player.Entity.TeleportToDouble(x + 0.5, geometry.FloorFor(level) + layout.ArrivalHeight(x, z), z + 0.5);

    /// <summary>A position as the HUD shows it, relative to spawn.</summary>
    private string FromSpawn(int x, int z) => $"{x - sapi.World.DefaultSpawnPosition.X:0}, {z - sapi.World.DefaultSpawnPosition.Z:0}";

    private TextCommandResult OnDirectorCommand(TextCommandCallingArgs args)
    {
        MenaceSystem menace = sapi.ModLoader.GetModSystem<MenaceSystem>();
        if (menace == null) return TextCommandResult.Error("No entity director");
        menace.Paused = args.Parsers[0].IsMissing ? !menace.Paused : !(bool)args[0];
        return TextCommandResult.Success(menace.Paused ? "Director paused: nothing new comes" : "Director running");
    }

    private TextCommandResult OnStatCommand(TextCommandCallingArgs args)
    {
        Entity entity = args.Caller.Entity;
        float value = (float)Math.Clamp((double)args[1], 0, 1);
        switch ((string)args[0])
        {
            case "health":
                if (entity.GetBehavior<EntityBehaviorHealth>() is not { } health) return TextCommandResult.Error("You have no health");
                // (Zero would kill you without going through dying: /backrooms die does that)
                health.Health = Math.Max(0.5f, value * health.MaxHealth);
                return TextCommandResult.Success($"Health {health.Health:0.#} / {health.MaxHealth:0.#}");
            case "food":
                if (entity.GetBehavior<EntityBehaviorHunger>() is not { } hunger) return TextCommandResult.Error("You have no hunger");
                hunger.Saturation = value * hunger.MaxSaturation;
                return TextCommandResult.Success($"Satiety {hunger.Saturation:0} / {hunger.MaxSaturation:0}");
            default:
                entity.WatchedAttributes.SetDouble("temporalStability", value);
                return TextCommandResult.Success($"Stability {value:0.00}");
        }
    }

    private TextCommandResult OnExposureCommand(TextCommandCallingArgs args)
    {
        double hours = Math.Max(0, (double)args[0]);
        args.Caller.Entity.Attributes.SetDouble(MenaceSystem.RestedKey, sapi.World.Calendar.TotalHours - hours);
        return TextCommandResult.Success($"Out for {hours:0.#} hours (resting by a fire, a ward or at home resets it)");
    }
}
