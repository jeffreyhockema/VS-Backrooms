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
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// Testing cheats. The server side adds more <c>/backrooms</c> subcommands (heal, kit, allitems, clear, home, back,
/// find, nearest, director, stat, exposure, noise, die, light, fogspell, harvesttest); the client side (CheatSystem.Client.cs) is a
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
        // (For photographs: Level !'s hallway, the radius blocks down your lane's course from the start room's hall door;
        // a Level Fun party room with guests, from its north-west corner)
        ("runhall", "Level ! hallway", 36, 600),
        ("funparty", "Fun party room", 256, 1024),
        // (The End's partition walls, layout version 5: in front of the nearest, looking at it; and the central hall's
        // north-west EXIT vestibule, looking into it)
        ("endwall", "End partition wall", 512, 2048),
        ("endexit", "End central EXIT", 16384, 16384),
        // (A Level 3999 food court, from its middle; Level 188's courtyard door, from the courtyard looking at it)
        ("foodcourt", "3999 food court", 512, 2048),
        ("courtdoor", "188 courtyard door", 4096, 4096),
        // (Layout version 5: Level 2's dead tram, from the rails three blocks ahead of it, looking back at its front; a
        // purpified thing in a Level 3 wall, from two blocks in front of it, looking at it)
        ("tram", "Level 2 dead tram", 384, 1024),
        ("purpified", "Level 3 purpified", 384, 1024),
        // (Down a Level 3 manhole: in the flooded tunnel at the foot of the rungs, looking at them, to test the ladder)
        ("manhole", "Level 3 manhole ladder", 384, 1024),
        // (Layout version 5: a Level 10 field's shed, trough or fallen gate, from four blocks south of it; a Level 11
        // billboard, from the street in front of its building; an advertising pillar, from three blocks south-east of
        // it; Level 94's castle, from the radius blocks south of it, looking north at it on the horizon)
        ("fieldthing", "Level 10 field shed, trough or gate", 512, 2048),
        ("billboard", "Level 11 billboard", 384, 1024),
        ("adpillar", "Level 11 advertising pillar", 384, 1024),
        ("castle", "Level 94 castle on the horizon", 450, 2000),
        // (Layout version 5: a Level 5 lobby's front hall, from its axis looking at the desk and the grand staircases; a
        // guest-room door with 666 on its plaque, from across the corridor)
        ("fronthall", "Level 5 front hall", 2048, 4096),
        ("door666", "Level 5 door 666", 768, 1536),
        // (Level 4 where its carpet starts turning to hotel red, looking on toward the hotel)
        ("hotelturn", "Level 4 turning to hotel", 512, 2048),
        // (Layout version 5: a rock pillar on a Level 7 island, a camp's shelter of furniture and tar, a Level 6.1 vending
        // machine room from the hall in front of it, and blood-red glowcaps beside Level 8's road; from the nearest spot
        // to stand, with the heading that looks at it)
        ("seapillar", "Level 7 rock pillar", 512, 2048),
        ("shelter", "Level 7 shelter", 768, 2048),
        ("vendingroom", "Level 6.1 vending room", 96, 256),
        ("glowcaps", "Level 8 glowcaps", 384, 1024),
        // (Layout version 5's Suburbs: a two-storey house, from the street in front of it looking at its porch and
        // windows; the foot of its stairs, looking up them; a street-name sign and a DOWNTOWN sign, from across the corner)
        ("l9house", "Level 9 two-storey house", 384, 1024),
        ("l9stairs", "Level 9 house stairs", 384, 1024),
        ("streetname", "Level 9 street sign", 256, 1024),
        ("citysign", "Level 9 DOWNTOWN sign", 768, 2048),
        // (Runs that turn corners and end, from a few blocks off with the heading that looks at it: Levels 2 and 3's wall
        // pipes in an inner corner and round an outer one, an overhead bundle ending with open space beyond, a Level 3999
        // unit's neon base strip in a corner, and the hopper head on Level 188's downpipe)
        ("pipecorner", "Level 2/3 wall pipes, inner corner", 256, 1024),
        ("pipewrap", "Level 2/3 wall pipes, outer corner", 256, 1024),
        ("pipeend", "Level 1/2/3 overhead pipes ending", 256, 1024),
        ("neoncorner", "3999 neon strip corner", 512, 2048),
        ("downpipe", "188 downpipe head", 4096, 4096),
        // (Layout version 6: a camp tent two blocks by two, from three blocks out in front of its door, looking back at it;
        // a sleeping bag two blocks long, from the nearest place to stand; in any level)
        ("tent", "Camp tent", 1024, 4096),
        ("sleepingbag", "Sleeping bag", 1024, 4096),
    };

    /// <summary>The targets that are part of play; the rest are camera spots for the screenshots, and the manhole test.</summary>
    public static readonly string[] GameplayTargets = { "gate", "threshold", "cache", "refuge", "den", "redroom" };

    public static readonly string[] Stats = { "health", "food", "stability" };

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
            .BeginSubCommand("fogspell")
                .WithDescription("Moves the calendar on to the middle of the next spell of fog over Level 10's fields")
                .HandleWith(OnFogSpellCommand)
            .EndSubCommand()
            .BeginSubCommand("heal")
                .WithDescription("Restores your health, food, body temperature and stability, and resets your time out (menace exposure)")
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
            .BeginSubCommand("harvesttest")
                .WithDescription("Dev test: spawns a creature in front of you, kills it in your name and harvests it as a knife would, reporting what the body gives (default deathrat)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWord("entity"))
                .HandleWith(OnHarvestTestCommand)
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
            e => e is not EntityPlayer && e.Alive && e.Code?.Domain == "backrooms");
        foreach (Entity creature in creatures) creature.Die(EnumDespawnReason.Removed);
        return TextCommandResult.Success($"Removed {creatures.Length} creatures within {radius} blocks");
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
            case "runhall":
                int lane = level == WorldLayout.RunLevel ? layout.RunLaneAt(gx, gz) : -1;
                if (lane < 0) return TextCommandResult.Error("The hallway is in Level ! (/backrooms goto !)");
                WorldLayout.RunLane plan = layout.RunPlan(lane);
                var (hx, hz) = plan.LineAt(radius);
                var (ax, az) = plan.LineAt(radius + 4);
                found = layout.RunWorld(lane, hx, hz);
                // The way on down the hall, as a compass heading (0 north, 90 east)
                detail = $" ({radius} blocks down; looking on down it is heading {(Math.Atan2(ax - hx, hz - az) * 180 / Math.PI + 360) % 360:0})";
                break;
            case "funparty":
                if (level != WorldLayout.FunLevel) return TextCommandResult.Error("Party rooms are in Level Fun");
                FunRoom party = null;
                long partyDistance = long.MaxValue;
                foreach (FunRoom room in layout.FunRoomsNear(gx, gz, radius))
                {
                    if (room.Kind != FunZone.Party || room.Guests == 0) continue;
                    long dx = (room.X0 + room.X1) / 2 - gx, dz = (room.Z0 + room.Z1) / 2 - gz;
                    if (dx * dx + dz * dz < partyDistance) (party, partyDistance) = (room, dx * dx + dz * dz);
                }
                found = party != null ? (party.X0, party.Z0) : null;
                if (party != null) detail = $" ({party.Guests} guests; from its north-west corner, heading 135 looks across it)";
                break;
            case "foodcourt":
                if (level != WorldLayout.Level3999) return TextCommandResult.Error("Food courts are in Level 3999");
                var courts = layout.L3999UnitsNear(gx, gz, u => u.Kind == WorldLayout.L3999Kind.FoodCourt, radius);
                found = courts.Count > 0 ? courts[0] : null;
                break;
            case "courtdoor":
                if (level != WorldLayout.Level188) return TextCommandResult.Error("The courtyard door is in Level 188");
                // Eight blocks out into the courtyard from the door, facing it (the door is in the west façade)
                found = (layout.L188BuildX0 + 24, layout.L188BuildZ0 + 19);
                detail = " (heading 270 looks at the door and its EXIT sign)";
                break;
            case "tram":
                if (level != 2) return TextCommandResult.Error("The tramway is in Level 2");
                found = NearestTile(gx, gz, radius, level, t => t.Variant == Worldgen.Props.Tram && t.Stack == 0, out var tram);
                if (found is { } tf)
                {
                    var (fdx, fdz) = PierStep(tram.Pier);
                    found = (tf.X + 3 * fdx, tf.Z + 3 * fdz);
                    detail = $" (heading {PierHeading(tram.Pier, true)} looks back at it)";
                }
                break;
            case "tent":
                found = NearestTile(gx, gz, radius, level, t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.CampTent && t.Stack == 0, out var tent);
                if (found is { } tentAt)
                {
                    // (The front-left part: the door is half a block to its right, out toward Pier)
                    var (tdx, tdz) = PierStep(tent.Pier);
                    found = (tentAt.X + 3 * tdx, tentAt.Z + 3 * tdz);
                    detail = $" (heading {PierHeading(tent.Pier, true)} looks back at its door)";
                }
                break;
            case "sleepingbag":
                found = NearestTile(gx, gz, radius, level, t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.SleepingBag && t.Stack == 0, out _);
                if (found is { } bagAt && StandNear(bagAt.X, bagAt.Z, level) is { } bs)
                {
                    found = bs;
                    detail = $" (heading {(Math.Atan2(bagAt.X - bs.X, bs.Z - bagAt.Z) * 180 / Math.PI + 360) % 360:0} looks at its head, {bagAt.X - bs.X}, {bagAt.Z - bs.Z} away)";
                }
                break;
            case "purpified":
                if (level != 3) return TextCommandResult.Error("Purpified things are in Level 3");
                found = NearestTile(gx, gz, radius, level, t => t.Kind == TileKind.Wall && t.Variant == Decor.Purpified, out var wall);
                if (found is { } pf)
                {
                    var (pdx, pdz) = PierStep(wall.Pier);
                    found = (pf.X + 2 * pdx, pf.Z + 2 * pdz);
                    detail = $" (heading {PierHeading(wall.Pier, true)} looks at it)";
                }
                break;
            case "manhole":
            {
                if (level != 3) return TextCommandResult.Error("Manholes are in Level 3");
                if (layout.NearestManhole(gx, gz, radius) is not { } m) { found = null; break; }
                // Down in the shaft itself, on the tunnel's clay floor (rel -5) in its knee-deep water, the rungs on the
                // shaft's north side in front of you (WorldGenerator.BelowFloor): walk forward to climb
                int md = (int)Math.Sqrt((double)(m.X - gx) * (m.X - gx) + (double)(m.Z - gz) * (m.Z - gz));
                Teleport((IServerPlayer)args.Caller.Player, m.X + 0.5, geometry.FloorFor(level) - 4 + 0.05, m.Z + 0.5);
                return TextCommandResult.Success($"{target.Name} (heading 0 looks at the rungs), {md} blocks from where you were ({FromSpawn(m.X, m.Z)})");
            }
            case "fieldthing":
                if (level != 10) return TextCommandResult.Error("That is in Level 10");
                found = NearestTile(gx, gz, radius, level, t => t.Variant is Worldgen.Props.WaterTrough or Worldgen.Props.FallenGate
                    || t.Kind == TileKind.Wall && t.Pattern == WallPattern.BarnGrey, out _);
                if (found is { } ff) found = (ff.X, ff.Z + 4);
                detail = " (heading 0 looks at it)";
                break;
            case "billboard":
                if (level != 11) return TextCommandResult.Error("That is in Level 11");
                found = NearestTile(gx, gz, radius, level, t => t.Overhead == Worldgen.Props.Billboard, out _);
                if (found is { } bf)
                {
                    bool north = layout.CityLotFront(bf.X, bf.Z) == ArchPier.North;
                    found = (bf.X, bf.Z + (north ? -14 : 14));
                    detail = $" (on the roof; heading {(north ? 180 : 0)} looks back up at it)";
                }
                break;
            case "adpillar":
                if (level != 11) return TextCommandResult.Error("That is in Level 11");
                found = NearestTile(gx, gz, radius, level, t => t.Variant == Worldgen.Props.AdPillar, out _);
                if (found is { } af) found = (af.X + 3, af.Z + 3);
                detail = " (heading 315 looks at it)";
                break;
            case "l9house":
            case "l9stairs":
                if (level != 9) return TextCommandResult.Error("That is in Level 9");
                found = NearestTile(gx, gz, radius, level, t => t.Stair == 4 && t.Height != 0, out var top);
                if (found is { } stairTop)
                {
                    // The stairs climb away from the street: their foot is four back from the top, the street fifteen
                    var (cdx, cdz) = PierStep(top.Pier);
                    int back = target.Code == "l9house" ? 16 : 4;
                    found = (stairTop.X - back * cdx, stairTop.Z - back * cdz);
                    detail = $" (heading {PierHeading(top.Pier, false)} looks {(back == 4 ? "up the stairs" : "at the house")})";
                }
                break;
            case "streetname":
            case "citysign":
                if (level != 9) return TextCommandResult.Error("That is in Level 9");
                bool guide = target.Code == "citysign";
                found = NearestTile(gx, gz, radius, level, t => t.Variant == (guide ? Worldgen.Props.CitySign : Worldgen.Props.SuburbSign), out var sign);
                if (found is { } nf)
                {
                    // Out in the junction, three blocks off: the guide sign's face is side-on to its arrow
                    bool sideways = guide && sign.Pier is ArchPier.East or ArchPier.West;
                    found = sideways ? (nf.X, nf.Z - 3) : guide ? (nf.X + 3, nf.Z) : (nf.X - 3, nf.Z + 3);
                    detail = $" (heading {(sideways ? 180 : guide ? 270 : 45)} looks at it)";
                }
                break;
            case "castle":
                if (level != WorldLayout.Motion) return TextCommandResult.Error("The castle is in Level 94");
                found = (layout.MotionOriginX, layout.MotionOriginZ + radius);
                detail = " (heading 0 looks at it)";
                break;
            case "endwall":
            case "endexit":
                if (level != WorldLayout.TheEnd) return TextCommandResult.Error("That is in The End (/backrooms goto end)");
                found = target.Code == "endexit" ? NearestEndExitVestibule(out detail) : NearestEndPartition(gx, gz, radius, out detail);
                break;
            case "hotelturn":
            {
                if (level != 4) return TextCommandResult.Error("That is in Level 4");
                found = NearestTile(gx, gz, radius, level, t => t.Kind == TileKind.Floor && t.Floor == FloorKind.HotelCarpet, out _);
                if (found is { } turn)
                {
                    var (ox, oz) = layout.Outward(turn.X, turn.Z);
                    detail = $" (heading {(Math.Atan2(ox, -oz) * 180 / Math.PI + 360) % 360:0} looks on toward the hotel)";
                }
                break;
            }
            case "fronthall":
            case "door666":
            {
                if (level != 5) return TextCommandResult.Error("That is in Level 5");
                var view = target.Code == "fronthall"
                    ? NearestSpot(gx, gz, radius, layout.FrontHallView)
                    : NearestSpot(gx, gz, radius, layout.Door666View);
                found = view is { } v ? (v.X, v.Z) : null;
                if (view is { } w) detail = $" (heading {PierHeading(w.Facing, false)} looks at it)";
                break;
            }
            case "pipecorner":
            case "pipewrap":
            case "pipeend":
            case "neoncorner":
            {
                if (target.Code == "neoncorner" ? level != WorldLayout.Level3999 : target.Code == "pipeend" ? level is not (1 or 2 or 3) : level is not (2 or 3))
                    return TextCommandResult.Error(target.Code == "neoncorner" ? "That is in Level 3999" : target.Code == "pipeend" ? "That is in Levels 1, 2 and 3" : "That is in Levels 2 and 3");
                (int Dx, int Dz) toward = default;
                System.Func<Tile, int, int, bool> match = target.Code switch
                {
                    "pipecorner" => (t, x, z) => t.Kind == TileKind.Floor && RunCorner(x, z, inner: true, out toward),
                    "pipewrap" => (t, x, z) => CarriesWallPipes(t) && RunCorner(x, z, inner: false, out toward),
                    "pipeend" => (t, x, z) => OverheadEnd(t, x, z, out toward),
                    _ => (t, x, z) => NeonCorner(t, x, z, out toward),
                };
                if (NearestTileAt(gx, gz, radius, level, match, out _) is not { } it) { found = null; break; }
                // Back from it the way it looks (three blocks, or as near as there is floor), looking at it
                (int X, int Z)? spot = null;
                for (int back = 3; back >= 1 && spot == null; back--)
                {
                    int sx = it.X - back * toward.Dx, sz = it.Z - back * toward.Dz;
                    if (layout.TileAt(sx, sz) is { Kind: TileKind.Floor or TileKind.Doorway } st && st.Level == level) spot = (sx, sz);
                }
                found = spot ?? StandNear(it.X, it.Z, level) ?? it;
                if (found is { } rf) detail = $" (heading {(Math.Atan2(it.X - rf.X, rf.Z - it.Z) * 180 / Math.PI + 360) % 360:0} looks at it, {it.X - rf.X}, {it.Z - rf.Z} away)";
                break;
            }
            case "downpipe":
                if (level != WorldLayout.Level188) return TextCommandResult.Error("The downpipe is in Level 188");
                // On the courtyard's north façade (courtyard block 55, 17): from five blocks out, looking north and up
                found = (layout.L188BuildX0 + WorldLayout.L188PipeBx, layout.L188BuildZ0 + WorldLayout.L188PipeBz + 5);
                detail = " (heading 0 looks at it; its head is under the parapet, 21 blocks up)";
                break;
            case "seapillar":
            case "shelter":
            case "vendingroom":
            case "glowcaps":
            {
                int want = target.Code switch { "vendingroom" => 6, "glowcaps" => 8, _ => 7 };
                if (level != want) return TextCommandResult.Error($"That is in Level {(want == 6 ? "6.1 (/backrooms find snackrooms)" : want.ToString())}");
                System.Func<Tile, bool> match = target.Code switch
                {
                    "seapillar" => t => t.Detail == WorldLayout.L7Pillar && t.Depth == 0,
                    "shelter" => t => t.Kind == TileKind.Floor && t.Detail == WorldLayout.L7TarUnder,
                    "vendingroom" => t => t.Zone == 1 && t.Kind == TileKind.Doorway && t.Detail == WorldLayout.SnackVendingFront,
                    _ => t => t.Variant is Worldgen.Props.GlowcapRed or Worldgen.Props.GlowcapMixed,
                };
                if (NearestTile(gx, gz, radius, level, match, out _) is not { } it) { found = null; break; }
                found = StandNear(it.X, it.Z, level) ?? it;
                if (found is { } sf) detail = $" (heading {(Math.Atan2(it.X - sf.X, sf.Z - it.Z) * 180 / Math.PI + 360) % 360:0} looks at it, {it.X - sf.X}, {it.Z - sf.Z} away)";
                break;
            }
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

    /// <summary>
    /// A spot four blocks in front of the middle of the nearest partition wall of The End's (layout version 5), and the
    /// compass heading that looks at it.
    /// </summary>
    private (int X, int Z)? NearestEndPartition(int gx, int gz, int radius, out string detail)
    {
        detail = "";
        var (di0, dj0) = layout.EndDeptOf(gx, gz);
        for (int r = 0; r <= radius / WorldLayout.EndDept + 1; r++)
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    for (int side = 0; side < 4; side++)
                    {
                        if (!layout.EndPartitionAt(di0 + di, dj0 + dj, side, out _)) continue;
                        var (cx, cz) = layout.EndDeptCentre(di0 + di, dj0 + dj);
                        // The wall stands on the department's inner edge, 25 or 26 blocks out from its middle
                        var (x, z, heading) = side switch { 0 => (cx - 22, cz, 270), 1 => (cx + 21, cz, 90), 2 => (cx, cz - 22, 0), _ => (cx, cz + 21, 180) };
                        detail = $" (heading {heading} looks at it)";
                        return (x, z);
                    }
                }
        return null;
    }

    /// <summary>A spot in front of the central hall's north-west EXIT vestibule of The End's, and the heading that looks into it.</summary>
    private (int X, int Z)? NearestEndExitVestibule(out string detail)
    {
        var (cx, cz) = layout.EndDeptCentre(0, 0);
        detail = " (heading 0 looks into the vestibule at the door)";
        // The door is at department-local (12, 10), facing south; stand five blocks in front of it
        return (cx - 32 + 12, cz - 32 + 15);
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

    /// <summary>The nearest tile of a level that matches, searching cell by cell outward, and the tile itself.</summary>
    private (int X, int Z)? NearestTile(int gx, int gz, int radius, int level, System.Func<Tile, bool> match, out Tile tile) =>
        NearestTileAt(gx, gz, radius, level, (t, x, z) => match(t), out tile);

    /// <summary>As <see cref="NearestTile"/>, the match also given the tile's position.</summary>
    private (int X, int Z)? NearestTileAt(int gx, int gz, int radius, int level, System.Func<Tile, int, int, bool> match, out Tile tile)
    {
        tile = default;
        int mx0 = WorldLayout.MacroOf(gx), mz0 = WorldLayout.MacroOf(gz), rings = radius / WorldLayout.MacroSize + 1;
        (int X, int Z)? best = null;
        long bestDistance = long.MaxValue;
        for (int r = 0; r <= rings && best == null; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || layout.LevelAt(mx0 + dx, mz0 + dz) != level) continue;
                    for (int i = 0; i < WorldLayout.MacroSize * WorldLayout.MacroSize; i++)
                    {
                        int x = (mx0 + dx) * WorldLayout.MacroSize + i % WorldLayout.MacroSize, z = (mz0 + dz) * WorldLayout.MacroSize + i / WorldLayout.MacroSize;
                        Tile t = layout.TileAt(x, z);
                        if (t.Level != level || !match(t, x, z)) continue;
                        long distance = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                        if (distance < bestDistance && distance <= (long)radius * radius) (best, bestDistance, tile) = ((x, z), distance, t);
                    }
                }
        return best;
    }

    private static readonly (int Dx, int Dz)[] Sides4 = { (0, -1), (1, 0), (0, 1), (-1, 0) };

    /// <summary>Whether a wall carries Levels 2 and 3's wall pipes (as WorldGenerator draws them).</summary>
    private static bool CarriesWallPipes(in Tile t) => t.Kind == TileKind.Wall && (t.Level == 2 && t.Pattern == WallPattern.Tunnel
        && t.Variant is Worldgen.Props.WallPipes or Worldgen.Props.WallRiser or Worldgen.Props.WallValve
        || t.Level == 3 && t.Variant == Worldgen.Props.WallPipes && t.Pattern != WallPattern.Stone);

    private static bool OpenAtPipes(in Tile t) => t.Kind is TileKind.Floor or TileKind.Doorway or TileKind.Pit or TileKind.Bars or TileKind.Water or TileKind.ArchDoor;

    /// <summary>
    /// An inner corner of piped walls (a floor with piped walls on two sides that meet, <paramref name="toward"/> the way
    /// into the corner), or an outer one (a piped wall open on two sides that meet, <paramref name="toward"/> the way from
    /// the open toward it).
    /// </summary>
    private bool RunCorner(int x, int z, bool inner, out (int Dx, int Dz) toward)
    {
        toward = default;
        for (int c = 0; c < 4; c++)
        {
            var (ax, az) = Sides4[c];
            var (bx, bz) = Sides4[(c + 1) & 3];
            Tile a = layout.TileAt(x + ax, z + az), b = layout.TileAt(x + bx, z + bz);
            bool hit = inner ? CarriesWallPipes(a) && CarriesWallPipes(b) && !OpenAtPipes(layout.TileAt(x + ax + bx, z + az + bz))
                : OpenAtPipes(a) && OpenAtPipes(b) && OpenAtPipes(layout.TileAt(x + ax + bx, z + az + bz));
            if (!hit) continue;
            toward = inner ? (ax + bx, az + bz) : (-(ax + bx), -(az + bz));
            return true;
        }
        return false;
    }

    /// <summary>An overhead bundle (Levels 1-3) whose next tile on is open with nothing overhead, <paramref name="toward"/> that way.</summary>
    private bool OverheadEnd(in Tile t, int x, int z, out (int Dx, int Dz) toward)
    {
        toward = default;
        bool alongX = t.Pipe is Worldgen.Pipes.RunX or Worldgen.Pipes.LeakX, alongZ = t.Pipe is Worldgen.Pipes.RunZ or Worldgen.Pipes.LeakZ;
        if (t.Kind != TileKind.Floor || !(alongX || alongZ) || t.Ceiling != CeilingKind.Tile) return false;
        for (int dir = -1; dir <= 1; dir += 2)
        {
            var (dx, dz) = alongX ? (dir, 0) : (0, dir);
            Tile n = layout.TileAt(x + dx, z + dz);
            if (n.Kind != TileKind.Floor || n.Pipe != Worldgen.Pipes.None || n.Beam || n.Grand != t.Grand || n.Low != t.Low) continue;
            toward = (dx, dz);
            return true;
        }
        return false;
    }

    /// <summary>A Level 3999 unit's corner where the neon base strip turns along the side wall (as WorldGenerator draws it).</summary>
    private bool NeonCorner(in Tile t, int x, int z, out (int Dx, int Dz) toward)
    {
        toward = default;
        if ((t.Roof & WorldLayout.L3999BaseBit) == 0 || t.Variant != 0) return false;
        var (fx, fz) = PierStep(t.Pier);
        Tile next = layout.TileAt(x + fx, z + fz);
        if ((next.Roof & WorldLayout.L3999BaseBit) == 0 || next.Variant != 0) return false;
        var (nx, nz) = PierStep(next.Pier);
        // The next one along faces away from a side wall beside this one
        if (layout.TileAt(x - nx, z - nz).Kind != TileKind.Wall || nx * fx + nz * fz != 0) return false;
        toward = (-fx - nx, -fz - nz);
        return true;
    }

    /// <summary>One block the way a tile faces.</summary>
    private static (int Dx, int Dz) PierStep(ArchPier pier) => pier switch
    {
        ArchPier.North => (0, -1),
        ArchPier.South => (0, 1),
        ArchPier.East => (1, 0),
        _ => (-1, 0),
    };

    /// <summary>The compass heading (0 north, 90 east) of the way a tile faces, or of the way back.</summary>
    private static int PierHeading(ArchPier pier, bool back)
    {
        int heading = pier switch { ArchPier.North => 0, ArchPier.East => 90, ArchPier.South => 180, _ => 270 };
        return back ? (heading + 180) % 360 : heading;
    }

    /// <summary>
    /// The nearest open floor (or doorway) to a spot, within 8 blocks, in the same level; failing that within 16, and
    /// failing that the nearest within 16 even behind a locked door (a Level 5 den's heart can lie among locked rooms;
    /// this is a cheat, and whoever is put there can pry their way out).
    /// </summary>
    private (int X, int Z)? StandNear(int x, int z, int level) =>
        StandNear(x, z, level, 8, false) ?? StandNear(x, z, level, 16, false) ?? StandNear(x, z, level, 16, true);

    private (int X, int Z)? StandNear(int x, int z, int level, int radius, bool locked)
    {
        for (int r = 0; r <= radius; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    Tile t = layout.TileAt(x + dx, z + dz);
                    if (t.Level == level && t.Kind is TileKind.Floor or TileKind.Doorway && (locked || !t.Sealed) && t.Stack == 0 && t.Stair == 0
                        && t.Under == 0 && !t.SupplyBox && (t.Kind == TileKind.Doorway || t.Variant == 0)) return (x + dx, z + dz);
                }
        return null;
    }

    /// <summary>The nearest of the views that cells give (looking from the nearest cell outward, ring by ring), within the radius.</summary>
    private static (int X, int Z, ArchPier Facing)? NearestSpot(int gx, int gz, int radius, System.Func<int, int, (int X, int Z, ArchPier Facing)?> spot)
    {
        int mx0 = WorldLayout.MacroOf(gx), mz0 = WorldLayout.MacroOf(gz), rings = radius / WorldLayout.MacroSize + 1;
        (int X, int Z, ArchPier Facing)? best = null;
        long bestDistance = long.MaxValue;
        for (int r = 0; r <= rings && best == null; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || spot(mx0 + dx, mz0 + dz) is not { } s) continue;
                    long distance = (long)(s.X - gx) * (s.X - gx) + (long)(s.Z - gz) * (s.Z - gz);
                    if (distance < bestDistance && distance <= (long)radius * radius) (best, bestDistance) = (s, distance);
                }
        return best;
    }

    private void Teleport(IServerPlayer player, int x, int z, int level) =>
        Teleport(player, x + 0.5, geometry.FloorFor(level) + layout.ArrivalHeight(x, z), z + 0.5);

    /// <summary>Every cheat teleport goes through here, so <c>/backrooms back</c> can undo it.</summary>
    private void Teleport(IServerPlayer player, double x, double y, double z)
    {
        RememberBack(player, player.Entity.Pos.XYZ);
        player.Entity.TeleportToDouble(x, y, z);
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
