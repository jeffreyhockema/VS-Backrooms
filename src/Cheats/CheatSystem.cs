using System;
using System.Collections.Generic;
using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;
using Backrooms.Entities;
using Backrooms.Regions;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// Testing cheats. The server side adds more <c>/backrooms</c> subcommands (heal, kit, allitems, clear, home, back,
/// find, nearest, feature, features, director, stat, exposure, noise, die, light, fogspell, harvesttest, blocksweep, transitiontest,
/// transitionbench; the registrations in <c>StartServerSide</c> are the full list); the client side (CheatSystem.Client.cs) is a
/// menu (F7, or <c>.cheats</c>) whose buttons send those and the other debug commands, so every action still goes
/// through the server's privilege check, plus a few view cheats that only touch the client.
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

    /// <summary>What <c>/backrooms nearest</c> looks for round you (<see cref="FeatureFinder.Targets"/>).</summary>
    public static (string Code, string Name, int Radius, int MaxRadius)[] Targets => FeatureFinder.Targets;

    /// <summary>The targets that are part of play; the rest are camera spots for the screenshots, and the manhole test.</summary>
    public static string[] GameplayTargets => FeatureFinder.GameplayTargets;

    public static readonly string[] Stats = { "health", "food", "stability", "thirst", "rest" };

    /// <summary>What <c>/backrooms kit</c> gives, by kind (testing when none is given).</summary>
    public static readonly (string Code, string Name, (string Code, int Quantity)[] Things)[] Kits =
    {
        // A modest kit for getting about and testing the survival systems
        ("testing", "Testing kit", new[]
        {
            ("game:torch-basic-lit-up", 8), ("game:candle", 4), ("backrooms:almondwater", 8), ("backrooms:cannedbeans", 4),
            ("backrooms:prybar", 1), ("backrooms:chalk", 1), ("backrooms:glassshiv", 1), ("backrooms:scraper", 1), ("backrooms:firesalt", 4),
        }),
        // For a long walk: a bag, and light, water and food for a few days
        ("explorer", "Explorer kit", new[]
        {
            ("backrooms:carpetbag", 1), ("game:torch-basic-lit-up", 16), ("backrooms:almondwater", 12), ("backrooms:cannedbeans", 6),
            ("backrooms:crackers", 6), ("backrooms:prybar", 1), ("backrooms:chalk", 2), ("backrooms:glassshiv", 1), ("backrooms:scraper", 1),
            ("backrooms:firesalt", 6), ("game:firestarter", 1),
        }),
        // Scrap metal in a crucible: the scrap, a fired crucible and ingot mould, and firewood and charcoal for a firepit
        ("crucible", "Crucible test kit", new[]
        {
            ("backrooms:scrapwire", 10), ("backrooms:l3999-circuitboard", 2), ("backrooms:l3999-coinmech", 5), ("game:crucible-blue-fired", 1),
            ("game:ingotmold-blue-fired", 1), ("game:firewood", 4), ("game:charcoal", 16), ("game:firestarter", 1),
        }),
        // Pottery shards to clay: shards, grit, soil and a stone, and two ficus to break for more shards
        ("pottery", "Pottery test kit", new[]
        {
            ("backrooms:potshard", 8), ("backrooms:ceramicgrit", 2), ("game:soil-low-none", 2), ("game:stone-granite", 1), ("backrooms:ficus", 2),
        }),
    };

    /// <summary>
    /// Where each player was before their last cheat teleport (goto, find, nearest, home, back), for
    /// <c>/backrooms back</c>. Kept for the session only.
    /// </summary>
    private readonly Dictionary<string, Vec3d> backs = new();

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private FeatureFinder finder;

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
            finder = new FeatureFinder(layout, geometry);
        });

        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        CommandArgumentParsers parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("fogspell")
                .WithDescription("Moves the calendar on to the middle of the next spell of fog over Level 10's fields")
                .HandleWith(OnFogSpellCommand)
            .EndSubCommand()
            .BeginSubCommand("heal")
                .WithDescription("Restores your health, food, water, body temperature and stability, rests you (no awake hours, no caffeine crash, no gut rot), and resets your time awake (menace exposure)")
                .RequiresPlayer()
                .HandleWith(OnHealCommand)
            .EndSubCommand()
            .BeginSubCommand("kit")
                .WithDescription("Gives you a kit: testing (the default: light, food, a pry bar, chalk, a shiv, a scraper and Firesalt), explorer (a bag and supplies for a long walk), crucible (scrap metal, a fired crucible and what heats it) or pottery (shards, grit, soil, a stone, ficus)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWordRange("kind", Kits.Select(k => k.Code).ToArray()))
                .HandleWith(OnKitCommand)
            .EndSubCommand()
            .BeginSubCommand("allitems")
                .WithDescription("Puts one of every Backrooms item into chests beside you (or beside the floor at x z), for checking how they look set down on the ground")
                .WithArgs(parsers.OptionalInt("x"), parsers.OptionalInt("z"))
                .HandleWith(OnAllItemsCommand)
            .EndSubCommand()
            .BeginSubCommand("back")
                .WithDescription("Takes you back to where you were before your last cheat teleport (goto, find, nearest, home or back)")
                .RequiresPlayer()
                .HandleWith(OnBackCommand)
            .EndSubCommand()
            .BeginSubCommand("light")
                .WithDescription("Puts a lit light in your hand (the active hotbar slot; what was there goes to your bags): candle, torch or lantern (default)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWordRange("kind", "lantern", "torch", "candle"))
                .HandleWith(OnLightCommand)
            .EndSubCommand()
            .BeginSubCommand("clear")
                .WithDescription("Removes every Backrooms creature within the radius (default 64)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalInt("radius", 64))
                .HandleWith(OnClearCommand)
            .EndSubCommand()
            .BeginSubCommand("runescape")
                .WithDescription("Dev test: comes out of Level !'s true exit into Level 1 (default), 4 or end, as the escape does (the red door replaces a door, the present by it): add reset to forget that you ever had the present. From the console it only does the world's part, and logs")
                .WithArgs(parsers.OptionalWord("level"), parsers.OptionalWord("reset"))
                .HandleWith(OnRunEscapeCommand)
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
                .WithDescription("Sets your health, food or thirst (hydration, as a fraction of the most, 0-1), your stability (0-1) or your rest (1 rested, 0 dead on your feet: awake hours = (1 - value) x 60)")
                .RequiresPlayer()
                .WithArgs(parsers.WordRange("stat", Stats), parsers.Double("value"))
                .HandleWith(OnStatCommand)
            .EndSubCommand()
            .BeginSubCommand("exposure")
                .WithDescription("Sets your time awake: how many in-game hours it is since you last rested (which raises menace)")
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
            .BeginSubCommand("harvesttest")
                .WithDescription("Dev test: spawns a creature in front of you, kills it in your name and harvests it as a knife would, reporting what the body gives (default deathrat)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWord("entity"))
                .HandleWith(OnHarvestTestCommand)
            .EndSubCommand()
            .BeginSubCommand("blocksweep")
                .WithDescription("Dev test: puts one of every Backrooms block down in turn (where you stand, or at the spawn from the console) and asks it what the block-info HUD asks a looked-at block; reports any that throw")
                // (A console line ends in a carriage return the parser keeps as an argument; it is taken and ignored)
                .WithArgs(sapi.ChatCommands.Parsers.OptionalWord("ignored"))
                .HandleWith(OnBlockSweepCommand)
            .EndSubCommand()
            .BeginSubCommand("transitiontest")
                .WithDescription("Plays the screen effect of passing through a threshold on your screen alone, without taking you anywhere: a style (door, walk, fall, elevator or plain, default walk) and how long to hold it in seconds (default 2)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWordRange("style", "door", "walk", "fall", "elevator", "plain"), parsers.OptionalDouble("seconds", 2))
                .HandleWith(args =>
                {
                    string style = args[0] as string ?? "walk";
                    double seconds = Math.Clamp((double)args[1], 0.2, 15);
                    sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>()?.TransitionTest((IServerPlayer)args.Caller.Player, style, (int)(seconds * 1000));
                    return TextCommandResult.Success($"Transition ({style}) for {seconds:0.0} s");
                })
            .EndSubCommand()
            .BeginSubCommand("transitionbench")
                .WithDescription("Times how long the server takes to load (and if need be generate) the chunk column around x z, which is what a threshold waits for before it moves anyone; the answer is in the log")
                .WithArgs(parsers.Int("x"), parsers.Int("z"))
                .HandleWith(args =>
                {
                    sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>()?.BenchLoad((int)args[0], (int)args[1], _ => { });
                    return TextCommandResult.Success("Loading; see the log");
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
            .EndSubCommand()
            .BeginSubCommand("corpse")
                .WithDescription("Dev test of the corpse a death leaves: list (the default), make (a corpse of yours with test stacks at your feet, or at the spawn from the console), simdeath (items dropped for a made-up death, to be caught), age [id] (turns the newest or that body to bones), clear (removes them all)")
                // (A console line ends in a carriage return the parser keeps as an argument; it is trimmed)
                .WithArgs(parsers.OptionalWord("action"), parsers.OptionalWord("id"))
                .HandleWith(args => TextCommandResult.Success(sapi.ModLoader.GetModSystem<Corpse.CorpseSystem>()?.Debug(args.Caller, args[0] as string, args[1] as string) ?? "Not a Backrooms world"))
            .EndSubCommand();
        RegisterStairScan(command, parsers);
        RegisterFeatures(command, parsers);
    }

    private TextCommandResult OnHealCommand(TextCommandCallingArgs args)
    {
        Entity entity = args.Caller.Entity;
        if (entity.GetBehavior<EntityBehaviorHealth>() is { } health) health.Health = health.MaxHealth;
        if (entity.GetBehavior<EntityBehaviorHunger>() is { } hunger) hunger.Saturation = hunger.MaxSaturation;
        if (entity.GetBehavior<EntityBehaviorBodyTemperature>() is { } temperature) temperature.CurBodyTemperature = temperature.NormalBodyTemperature;
        entity.WatchedAttributes.SetDouble("temporalStability", 1);
        entity.Attributes.SetDouble(MenaceSystem.RestedKey, sapi.World.Calendar.TotalHours);
        // The needs: full of water, no awake hours, no caffeine (nor its crash), no gut rot
        Needs.Needs.SetHydration(entity, Needs.Needs.MaxHydration);
        Needs.Needs.SetAwakeHours(entity, 0);
        if (entity.WatchedAttributes.GetTreeAttribute(Needs.Needs.FatigueTree) is { } fatigue)
        {
            fatigue.SetDouble("caffeineUntil", 0);
            fatigue.SetFloat("crashHours", 0);
            entity.WatchedAttributes.MarkPathDirty(Needs.Needs.FatigueTree);
        }
        entity.WatchedAttributes.SetDouble(Needs.Needs.SickKey, 0);
        return TextCommandResult.Success("Healed, fed, watered, warmed, stable and rested");
    }

    private TextCommandResult OnKitCommand(TextCommandCallingArgs args)
    {
        IPlayer player = args.Caller.Player;
        var kit = Kits.First(k => k.Code == (args.Parsers[0].IsMissing ? "testing" : (string)args[0]));
        int given = 0;
        foreach ((string code, int quantity) in kit.Things)
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
        return TextCommandResult.Success($"{kit.Name}: gave {given} kinds of things");
    }

    /// <summary>
    /// One of every item in the backrooms domain (every variant), in chests put down round a spot on the floor, for
    /// looking at them set down on the ground. What finds no room in a chest is dropped there.
    /// </summary>
    private TextCommandResult OnAllItemsCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        Entity caller = args.Caller.Entity;
        BlockPos at;
        if (!args.Parsers[0].IsMissing && !args.Parsers[1].IsMissing)
        {
            int x = (int)args[0], z = (int)args[1];
            int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
            at = new BlockPos(x, geometry.FloorFor(level) + (int)Math.Floor(layout.ArrivalHeight(x, z)), z);
        }
        else if (caller != null) at = caller.Pos.AsBlockPos;
        else return TextCommandResult.Error("From the console, give x and z");

        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(at) != null) return PutAllItems(at);
        // Not loaded (from the console): load it, and put them down once it is
        IServerPlayer player = args.Caller.Player as IServerPlayer;
        int group = args.Caller.FromChatGroupId;
        sapi.WorldManager.LoadChunkColumnPriority(at.X / GlobalConstants.ChunkSize, at.Z / GlobalConstants.ChunkSize, new ChunkLoadOptions
        {
            OnLoaded = () =>
            {
                TextCommandResult result = PutAllItems(at);
                if (player != null) player.SendMessage(group, result.StatusMessage, EnumChatType.CommandSuccess);
                else sapi.Logger.Notification("[backrooms] allitems: {0}", result.StatusMessage);
            },
        });
        return TextCommandResult.Success("That column is not loaded yet. Loading it; the chests follow once it is.");
    }

    private TextCommandResult PutAllItems(BlockPos at)
    {
        Block chest = sapi.World.GetBlock(new AssetLocation("game:chest-east"));
        if (chest == null) return TextCommandResult.Error("No game:chest-east in this game");
        IBlockAccessor ba = sapi.World.BlockAccessor;
        var stacks = new Queue<ItemStack>(sapi.World.Items.Where(i => i?.Code?.Domain == "backrooms").OrderBy(i => i.Code.Path).Select(i => new ItemStack(i)));
        int items = stacks.Count, chests = 0;
        // Round the spot, ring by ring: any open block with a solid floor under it, never the spot itself
        for (int r = 1; r <= 4 && stacks.Count > 0; r++)
            for (int dz = -r; dz <= r && stacks.Count > 0; dz++)
                for (int dx = -r; dx <= r && stacks.Count > 0; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    BlockPos pos = at.AddCopy(dx, 0, dz);
                    if (ba.GetBlock(pos).Id != 0 || ba.GetBlock(pos, BlockLayersAccess.Fluid).Id != 0 || !ba.GetBlock(pos.DownCopy()).SideSolid[BlockFacing.UP.Index]) continue;
                    ba.SetBlock(chest.Id, pos);
                    if (ba.GetBlockEntity(pos) == null) ba.SpawnBlockEntity(chest.EntityClass, pos);
                    if (ba.GetBlockEntity(pos) is not BlockEntityContainer container) continue;
                    chests++;
                    for (int slot = 0; slot < container.Inventory.Count && stacks.Count > 0; slot++)
                    {
                        container.Inventory[slot].Itemstack = stacks.Dequeue();
                        container.Inventory[slot].MarkDirty();
                    }
                    container.MarkDirty(true);
                }
        int dropped = stacks.Count;
        foreach (ItemStack stack in stacks) sapi.World.SpawnItemEntity(stack, at.ToVec3d().Add(0.5, 0.5, 0.5));
        return TextCommandResult.Success($"{items} items in {chests} chests round {FromSpawn(at.X, at.Z)}" + (dropped > 0 ? $"; {dropped} found no room and were dropped" : ""));
    }

    /// <summary>Notes where a player is, for <c>/backrooms back</c>, before a cheat teleport takes them away.</summary>
    public void RememberBack(IServerPlayer player, Vec3d from)
    {
        if (player?.PlayerUID != null && from != null) backs[player.PlayerUID] = from.Clone();
    }

    private TextCommandResult OnBackCommand(TextCommandCallingArgs args)
    {
        var player = (IServerPlayer)args.Caller.Player;
        if (!backs.TryGetValue(player.PlayerUID, out Vec3d to)) return TextCommandResult.Error("No cheat teleport to go back from this session");
        Teleport(player, to.X, to.Y, to.Z);
        return TextCommandResult.Success($"Back at {FromSpawn((int)Math.Floor(to.X), (int)Math.Floor(to.Z))} (back again returns you)");
    }

    /// <summary>
    /// A lit light straight into the hand, for seeing (and photographing) Level 6: the kit's torches go into whatever
    /// slots are free, and only what is in the active slot lights anything.
    /// </summary>
    private TextCommandResult OnLightCommand(TextCommandCallingArgs args)
    {
        IPlayer player = args.Caller.Player;
        string kind = args.Parsers[0].IsMissing ? "lantern" : (string)args[0];
        string[] codes = kind switch
        {
            "torch" => new[] { "game:torch-basic-lit-up" },
            "candle" => new[] { "game:candle" },
            _ => new[] { "game:lantern-large-up", "game:lantern-small-up", "game:lantern-up" },
        };
        Block block = codes.Select(c => sapi.World.GetBlock(new AssetLocation(c))).FirstOrDefault(b => b != null);
        if (block == null) return TextCommandResult.Error($"No {codes[0]} in this game");
        var stack = new ItemStack(block);
        if (kind == "lantern")
        {
            stack.Attributes.SetString("material", "copper");
            stack.Attributes.SetString("lining", "plain");
            stack.Attributes.SetString("glass", "quartz");
        }
        ItemSlot slot = player.InventoryManager.ActiveHotbarSlot;
        if (slot == null) return TextCommandResult.Error("You have no hand to hold it in");
        if (!slot.Empty)
        {
            ItemStack held = slot.TakeOutWhole();
            if (!player.InventoryManager.TryGiveItemstack(held, true)) sapi.World.SpawnItemEntity(held, player.Entity.Pos.XYZ);
        }
        slot.Itemstack = stack;
        slot.MarkDirty();
        byte[] hsv = block.GetLightHsv(sapi.World.BlockAccessor, null, stack);
        return TextCommandResult.Success($"Holding a lit {kind} (light {hsv?[2] ?? 0})");
    }

    private TextCommandResult OnClearCommand(TextCommandCallingArgs args)
    {
        int radius = Math.Clamp((int)args[0], 1, 512);
        Entity[] creatures = sapi.World.GetEntitiesAround(args.Caller.Entity.Pos.XYZ, radius, radius,
            e => e is not EntityPlayer and not Corpse.EntityCorpse && e.Alive && e.Code?.Domain == "backrooms");
        foreach (Entity creature in creatures) creature.Die(EnumDespawnReason.Removed);
        return TextCommandResult.Success($"Removed {creatures.Length} creatures within {radius} blocks");
    }

    private TextCommandResult OnRunEscapeCommand(TextCommandCallingArgs args)
    {
        var run = sapi.ModLoader.GetModSystem<RunSystem>();
        if (layout == null || run == null) return TextCommandResult.Error("This is not a Backrooms world");
        string word = args.Parsers[0].IsMissing ? "1" : (string)args[0];
        int level = word == "end" ? WorldLayout.TheEnd : word == "4" ? 4 : 1;
        bool reset = !args.Parsers[1].IsMissing && (string)args[1] == "reset" || word == "reset";
        return TextCommandResult.Success(run.DebugEscape(args.Caller.Player as IServerPlayer, level, reset));
    }

    private TextCommandResult OnHomeCommand(TextCommandCallingArgs args)
    {
        var player = (IServerPlayer)args.Caller.Player;
        FuzzyEntityPos home = player.GetSpawnPosition(false);
        if (home == null) return TextCommandResult.Error("You have nowhere to wake up");
        Teleport(player, home.X, home.Y, home.Z);
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
            if (level < 0) return TextCommandResult.Error($"There is no Level {number} here ({BackroomsModSystem.LevelList})");
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

    private TextCommandResult OnFogSpellCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        double now = sapi.World.Calendar.TotalHours, middle = AtmosphereSystem.NextL10FogSpell(sapi.World.Seed, now);
        sapi.World.Calendar.Add((float)(middle - now));
        return TextCommandResult.Success($"{middle - now:0.0} hours on: Level 10 is in the thick of a spell of fog");
    }

    private TextCommandResult OnNearestCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        var target = Targets.First(t => t.Code == (string)args[0]);
        int radius = (int)args[1] < 0 ? target.Radius : Math.Clamp((int)args[1], 16, target.MaxRadius);
        Entity entity = args.Caller.Entity;
        int gx = (int)Math.Floor(entity.Pos.X), gz = (int)Math.Floor(entity.Pos.Z);
        int level = layout.LevelAt(WorldLayout.MacroOf(gx), WorldLayout.MacroOf(gz));

        FeatureFinder.Hit hit = finder.Target(target.Code, gx, gz, radius, level, target.Name);
        if (hit == null && finder.Error != null) return TextCommandResult.Error(finder.Error);
        if (hit == null)
            return TextCommandResult.Error(finder.Stopped
                ? $"No {target.Name.ToLowerInvariant()} found in the first {Math.Min(radius, FeatureFinder.TileScanMaxRadius)} blocks searched in Level {WorldLayout.DisplayNumber(level)} (the search stopped after {FeatureFinder.TileScanSeconds} s)"
                : $"No {target.Name.ToLowerInvariant()} within {radius} blocks in Level {WorldLayout.DisplayNumber(level)}");
        if (hit.Message != null)
        {
            string message = FaceText(hit.Message, hit.Stand.Value.X, hit.Stand.Value.Z, hit, out float? shaftYaw, false);
            Teleport((IServerPlayer)args.Caller.Player, hit.Stand.Value.X + 0.5, hit.FeetY.Value, hit.Stand.Value.Z + 0.5, shaftYaw);
            return TextCommandResult.Success($"{message} ({FromSpawn(hit.X, hit.Z)})");
        }
        if (finder.StandNear(hit.X, hit.Z, level) is not { } stand) return TextCommandResult.Error($"Found a {target.Name.ToLowerInvariant()} at {FromSpawn(hit.X, hit.Z)}, but nowhere to stand near it");

        int distance = (int)Math.Sqrt((double)(hit.X - gx) * (hit.X - gx) + (double)(hit.Z - gz) * (hit.Z - gz));
        string detail = FaceText(hit.Detail, stand.X, stand.Z, hit, out float? yaw);
        Teleport((IServerPlayer)args.Caller.Player, stand.X + 0.5, geometry.FloorFor(level) + layout.ArrivalHeight(stand.X, stand.Z), stand.Z + 0.5, yaw);
        return TextCommandResult.Success($"{target.Name}{detail}, {distance} blocks from where you were ({FromSpawn(hit.X, hit.Z)})");
    }

    /// <summary>As <see cref="FeatureFinder.NearestTileAt"/> (for the stair scan).</summary>
    private (int X, int Z)? NearestTileAt(int gx, int gz, int radius, int level, System.Func<Tile, int, int, bool> match, out Tile tile) =>
        finder.NearestTileAt(gx, gz, radius, level, match, out tile);

    private void Teleport(IServerPlayer player, int x, int z, int level) =>
        Teleport(player, x + 0.5, geometry.FloorFor(level) + layout.ArrivalHeight(x, z), z + 0.5);

    /// <summary>Every cheat teleport goes through here, so <c>/backrooms back</c> can undo it.</summary>
    private void Teleport(IServerPlayer player, double x, double y, double z, float? yaw = null)
    {
        RememberBack(player, player.Entity.Pos.XYZ);
        if (yaw is { } turn) player.Entity.TeleportToDouble(x, y, z, () =>
        {
            // (Turned again a moment on: a far teleport's position update can reach the client after the first turn and undo it)
            var thresholds = sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>();
            thresholds?.Face(player, turn);
            sapi.Event.RegisterCallback(_ => thresholds?.Face(player, turn), 600);
            sapi.Event.RegisterCallback(_ => thresholds?.Face(player, turn), 1800);
        });
        else player.Entity.TeleportToDouble(x, y, z);
    }

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
            case "thirst":
                Needs.Needs.SetHydration(entity, value * Needs.Needs.MaxHydration);
                return TextCommandResult.Success($"Hydration {Needs.Needs.Hydration(entity):0} / {Needs.Needs.MaxHydration:0} ({Needs.NeedsMath.ThirstBand(value)}{(Needs.Needs.ThirstOn(sapi.World) ? "" : "; thirst is off in this world")})");
            case "rest":
                Needs.Needs.SetAwakeHours(entity, (1 - value) * Needs.Needs.DeadHours);
                return TextCommandResult.Success($"Awake {Needs.Needs.AwakeHours(entity):0.#} h ({Needs.NeedsMath.Band(Needs.Needs.AwakeHours(entity))}{(Needs.Needs.FatigueOn(sapi.World) ? "" : "; fatigue is off in this world")})");
            default:
                entity.WatchedAttributes.SetDouble("temporalStability", value);
                return TextCommandResult.Success($"Stability {value:0.00}");
        }
    }

    private TextCommandResult OnExposureCommand(TextCommandCallingArgs args)
    {
        double hours = Math.Max(0, (double)args[0]);
        args.Caller.Entity.Attributes.SetDouble(MenaceSystem.RestedKey, sapi.World.Calendar.TotalHours - hours);
        return TextCommandResult.Success($"Awake for {hours:0.#} hours (resting by a fire, a ward or at home resets it)");
    }

    /// <summary>
    /// Dev test: puts one of every Backrooms block down in turn and asks it what the block-info HUD asks a looked-at
    /// block (its placed name, its pick stack and its drops). A block that throws is reported: the Level Fun supply shelf
    /// crashed clients that way, by a code rebuilt from the wrong part.
    /// </summary>
    private TextCommandResult OnBlockSweepCommand(TextCommandCallingArgs args)
    {
        IWorldAccessor world = sapi.World;
        IBlockAccessor blocks = world.BlockAccessor;
        BlockPos at = (args.Caller.Entity?.Pos.AsBlockPos ?? world.DefaultSpawnPosition.AsBlockPos).UpCopy(2);
        for (int i = 0; i < 12 && blocks.GetBlock(at).Id != 0; i++) at = at.UpCopy();
        if (blocks.GetBlock(at).Id != 0) return TextCommandResult.Error("No air to put the blocks in here");
        int tried = 0;
        var failed = new List<string>();
        foreach (Block block in world.Blocks)
        {
            if (block?.Code == null || block.Code.Domain != "backrooms" || block.Id == 0) continue;
            tried++;
            try
            {
                blocks.SetBlock(block.Id, at);
                block.GetPlacedBlockName(world, at);
                block.OnPickBlock(world, at);
                block.GetDrops(world, at, null, 1f);
            }
            catch (Exception e)
            {
                failed.Add($"{block.Code}: {e.GetType().Name}: {e.Message}");
            }
            finally
            {
                try { blocks.SetBlock(0, at); } catch (Exception) { }
            }
        }
        foreach (string f in failed) sapi.Logger.Warning("[backrooms] blocksweep: {0}", f);
        string summary = $"blocksweep: {tried} blocks tried, {failed.Count} threw" + (failed.Count > 0 ? ": " + string.Join(" | ", failed.Take(20)) : "");
        sapi.Logger.Notification("[backrooms] " + summary);
        return failed.Count == 0 ? TextCommandResult.Success(summary) : TextCommandResult.Error(summary);
    }

    /// <summary>
    /// Dev test for the empty-harvest report: spawns the creature three blocks ahead, kills it a second later in the
    /// player's name, and a second after that harvests it the way the knife does on the server (stopping when the
    /// client's copy would), then reports the harvest attributes and the body's inventory in chat.
    /// </summary>
    private TextCommandResult OnHarvestTestCommand(TextCommandCallingArgs args)
    {
        IServerPlayer player = (IServerPlayer)args.Caller.Player;
        string code = args[0] as string ?? "deathrat";
        if (!code.Contains(':')) code = "backrooms:" + code;
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(code));
        if (type == null) return TextCommandResult.Error("No entity type " + code);
        EntityPlayer me = player.Entity;
        void Say(string text) => player.SendMessage(GlobalConstants.GeneralChatGroup, "harvesttest " + code + ": " + text, EnumChatType.CommandSuccess);

        Entity entity = sapi.World.ClassRegistry.CreateEntity(type);
        Vec3d at = me.Pos.XYZ.Add(Math.Sin(me.Pos.Yaw) * 3, 0, Math.Cos(me.Pos.Yaw) * 3);
        entity.Pos.SetPos(at.X, at.Y, at.Z);
        entity.Pos.Yaw = me.Pos.Yaw + MathF.PI;
        // (Our creatures despawn at once unless the director prepared them)
        EntityBehaviorMenace.Prepare(entity, me, Encounter.Ambient, passive: true, sapi.World.ElapsedMilliseconds);
        sapi.World.SpawnEntity(entity);
        Say($"spawned #{entity.EntityId} at {at.X:0.#} {at.Y:0.#} {at.Z:0.#}");

        sapi.World.RegisterCallback(_ =>
        {
            try
            {
                var source = new DamageSource { Source = EnumDamageSource.Player, SourceEntity = me, CauseEntity = me, Type = EnumDamageType.Injury, DamageTier = 9 };
                bool took = entity.ReceiveDamage(source, 1000f);
                if (entity.Alive) entity.Die(EnumDespawnReason.Death, source);
                Say($"killed (ReceiveDamage={took}): alive={entity.Alive}");
                sapi.World.RegisterCallback(_ =>
                {
                    try { HarvestTestReport(player, entity, Say); }
                    catch (Exception e) { Say("exception: " + e); }
                }, 1000);
            }
            catch (Exception e) { Say("exception: " + e); }
        }, 1000);
        return TextCommandResult.Success("harvesttest " + code + " started");
    }

    private void HarvestTestReport(IServerPlayer player, Entity entity, Action<string> say)
    {
        EntityPlayer me = player.Entity;
        var wa = entity.WatchedAttributes;
        string Attrs() => $"harvested={wa.GetBool("harvested")} dropsgenerated={wa.GetBool("dropsgenerated")} animalWeight={wa.GetFloat("animalWeight", -1):0.##}"
            + $" deathByEntity={wa.GetString("deathByEntity") ?? "(none)"} deathByPlayer={wa.GetString("deathByPlayer") ?? "(none)"}";
        say($"alive={entity.Alive} {Attrs()} animalLootDropRate={me.Stats.GetBlended("animalLootDropRate"):0.##}");

        var h = entity.GetBehavior<EntityBehaviorHarvestable>();
        if (h == null) { say("the server's copy has no harvestable behaviour"); return; }
        string Inv()
        {
            var items = h.Inventory.Select(s => s.Itemstack == null ? "-" : s.Itemstack.StackSize + "x " + s.Itemstack.Collectible?.Code).ToList();
            return items.Count == 0 ? "(no slots)" : string.Join(", ", items);
        }

        // What each side thinks the harvest takes: the knife stops when the client's copy is done, the server only
        // harvests if that is long enough for its own copy
        float clientDuration = 5, serverDuration = h.GetHarvestDuration(null, me);
        foreach (JsonObject b in entity.Properties.Client?.BehaviorsAsJsonObj ?? Array.Empty<JsonObject>())
        {
            if (b["code"].AsString() == "harvestable") clientDuration = b["duration"].AsFloat(5) * me.Stats.GetBlended("animalHarvestingTime");
        }
        ItemKnife knife = sapi.World.GetItem(new AssetLocation("game:knife-generic-flint")) as ItemKnife
            ?? sapi.World.Items.OfType<ItemKnife>().FirstOrDefault(k => k.Code != null);
        if (knife == null) { say("no knife item found; " + Attrs()); return; }
        var slot = new DummySlot(new ItemStack(knife));
        float speed = knife.GetKnifeHarvestingSpeed(slot);
        float clientStopsAt = speed * clientDuration + 0.15f, serverNeeds = speed * serverDuration - 0.1f;
        say($"harvest duration: client copy {clientDuration:0.##}s, server copy {serverDuration:0.##}s; with {knife.Code} the client stops at {clientStopsAt:0.00}s, the server harvests from {serverNeeds:0.00}s");

        var selection = new EntitySelection { Entity = entity, Position = entity.Pos.XYZ, HitPosition = new Vec3d(0, 0.1, 0), SelectionBoxIndex = 0 };
        knife.OnHeldInteractStop(clientStopsAt, slot, me, null, selection);
        say($"knife stop at {clientStopsAt:0.00}s: {Attrs()} inventory: {Inv()}");
        if (!wa.GetBool("harvested"))
        {
            h.SetHarvested(player, 1f);
            say($"SetHarvested directly: {Attrs()} inventory: {Inv()}");
        }
        say("harvestableInv attribute: " + ((wa["harvestableInv"] as ITreeAttribute)?.ToJsonToken() ?? "(none)"));
    }
}
