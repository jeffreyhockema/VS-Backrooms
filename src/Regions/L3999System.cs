using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Map;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Regions;

/// <summary>
/// Level 3999, the Neon Paradise: its rules (docs/design/new-levels/3999-plan.md, as the user directed on 2026-10-09: an
/// ordinary level with resources of its own). Everything a block does is read from its blocktype's attributes, written by
/// tools/gen_3999.py:
/// <list type="bullet">
/// <item><b>Machines</b> (<c>l3999cabinet</c>: seconds, min, max, jackpot, jackpotChance, plushChance, plush): hold to play;
/// each pays a player once per in-game day, and every player has a cap of <see cref="DailyCap"/> tickets a day. A claw
/// machine pays a plush now and then instead.</item>
/// <item><b>Themed cabinets</b> (<c>l3999themed</c>, <c>l3999playSeconds</c>): played to the end, the game takes you to
/// the level on its marquee (threshold kind <c>l3999-cabinet</c>).</item>
/// <item><b>Prize counters</b> (<c>l3999prizes</c>: tiers of tickets, each a list of prizes): right-click with tickets in
/// hand; the most the tier you can afford allows. <b>Food stalls</b> (<c>l3999stall</c>): a tray meal for its cost.
/// <b>Vending machines</b> (<c>takes</c>, <c>stockless</c>, <c>dispenses</c> on a BackroomsDispenser): one Almond Water
/// in, a snack or a drink out, never empty (<see cref="Vend"/>).</item>
/// <item><b>Moving walkways</b> (<c>l3999walkway</c>: speed): carry whoever stands on them (on the client, which moves the
/// player).</item>
/// <item><b>Mall directories</b> mark the nearest food court and lobby; <b>Arcade Attendants</b> stand behind the prize
/// counters, the food stalls and the reception desks while anyone is near (never kept with the world), cannot be hurt,
/// and point the way: to a lobby, or from a lobby's reception desk to the food court.</item>
/// <item>The Natatorium's water soothes (half a point of health every four seconds); the first failing neon near the Neon
/// Blackout says so; a windmill's generator in Level 10 turns its beacon green, for good.</item>
/// <item>Blocks marked <c>l3999structure</c> never break (machines, counters, doors, windows: canon's indestructible
/// arcade).</item>
/// </list>
/// </summary>
public class L3999System : ModSystem
{
    /// <summary>Tickets a player can win in a day, all machines together.</summary>
    public const int DailyCap = 40;

    private const string PlayerKey = "backrooms:l3999";
    private const string TicketCode = "backrooms:l3999-ticket";
    private const int AttendantNear = 40, AttendantGone = 96;
    /// <summary>The neon sign over a prize counter, and over a lobby's reception desk (indices in <see cref="WorldLayout.L3999Signs"/>).</summary>
    private const int PrizesSign = 2, ReceptionSign = 4;

    private static ICoreServerAPI sapi;
    private ICoreServerAPI serverApi;
    private ICoreClientAPI capi;
    private long attendantTick, sootheTick, walkwayTick;
    /// <summary>Reused by the client's walkway tick (every 20 ms) for the blocks it looks at.</summary>
    private readonly BlockPos walkwayProbe = new(0);
    private WorldLayout layout;
    private WorldGeometry geometry;
    private readonly Dictionary<(int X, int Z), Entity> attendants = new();
    private readonly Dictionary<string, long> nextSoothe = new();
    /// <summary>When (server ms) each player was told the Blackout is near, until they have been out of its fringe a while.</summary>
    private readonly Dictionary<string, long> blackoutWarned = new();
    private EntityProperties[] attendantTypes = Array.Empty<EntityProperties>();

    // After Protection (1.2), whose block classes this changes for the level's indestructible blocks
    public override double ExecuteOrder() => 1.3;

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsArcadeCabinet", typeof(BlockBehaviorL3999Cabinet));
        api.RegisterBlockBehaviorClass("BackroomsPrizeCounter", typeof(BlockBehaviorL3999Prizes));
        api.RegisterBlockBehaviorClass("BackroomsFoodStall", typeof(BlockBehaviorL3999Stall));
        api.RegisterBlockBehaviorClass("BackroomsArcadeDirectory", typeof(BlockBehaviorL3999Directory));
        api.RegisterBlockBehaviorClass("BackroomsL3999Vending", typeof(BlockBehaviorL3999Vending));
        api.RegisterBlockBehaviorClass("BackroomsWindmillGenerator", typeof(BlockBehaviorL3999Generator));
        api.RegisterEntity("BackroomsAttendant", typeof(EntityL3999Attendant));
    }

    /// <summary>
    /// Gives the level's blocks their workings by their attributes (on both sides: behaviours added now are not sent to
    /// clients), makes the ones marked <c>l3999structure</c> unbreakable, and makes the attendants our own kind of entity.
    /// </summary>
    public override void AssetsFinalize(ICoreAPI api)
    {
        foreach (EntityProperties type in api.World.EntityTypes)
            if (type?.Code?.Domain == "backrooms" && type.Code.Path.StartsWith("l3999-attendant")) type.Class = "BackroomsAttendant";
        foreach (Block block in api.World.Blocks)
        {
            string path = block?.Code?.Path;
            if (block?.Code?.Domain != "backrooms" || path == null || !path.StartsWith("l3999-")) continue;
            JsonObject attributes = block.Attributes;
            if (attributes?["l3999structure"].AsBool(false) == true)
            {
                block.RequiredMiningTier = Salvage.Protection.UnbreakableTier;
                block.Resistance = 1_000_000f;
            }
            if (attributes?["l3999themed"].Exists == true) Swap(block, new BlockBehaviorL3999Cabinet(block) { Themed = true });
            else if (attributes?["l3999cabinet"].Exists == true) Add(block, new BlockBehaviorL3999Cabinet(block));
            if (attributes?["l3999prizes"].Exists == true) Add(block, new BlockBehaviorL3999Prizes(block));
            if (attributes?["l3999stall"].Exists == true) Add(block, new BlockBehaviorL3999Stall(block));
            if (path.StartsWith("l3999-directory-")) Add(block, new BlockBehaviorL3999Directory(block));
            // (The vending machines work through their own block class, BackroomsDispenser: this only says what they take)
            if (attributes?["takes"].Exists == true) Add(block, new BlockBehaviorL3999Vending(block));
            if (path.StartsWith("l3999-generator-")) Add(block, new BlockBehaviorL3999Generator(block));
        }
    }

    private static void Add(Block block, BlockBehavior behavior)
    {
        if (block.BlockBehaviors?.Any(b => b.GetType() == behavior.GetType()) == true) return;
        block.BlockBehaviors = (block.BlockBehaviors ?? Array.Empty<BlockBehavior>()).Append(behavior).ToArray();
    }

    /// <summary>A themed cabinet is played before it takes anyone: its plain threshold behaviour gives way to the cabinet's.</summary>
    private static void Swap(Block block, BlockBehavior behavior)
    {
        block.BlockBehaviors = (block.BlockBehaviors ?? Array.Empty<BlockBehavior>()).Where(b => b is not BlockBehaviorThreshold && b is not BlockBehaviorL3999Cabinet)
            .Append(behavior).ToArray();
        if (block.CollectibleBehaviors != null) block.CollectibleBehaviors = block.CollectibleBehaviors.Where(b => b is not BlockBehaviorThreshold).ToArray();
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = serverApi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            attendantTypes = api.World.EntityTypes.Where(t => t.Code?.Domain == "backrooms" && t.Code.Path.StartsWith("l3999-attendant")).ToArray();
            attendantTick = api.Event.RegisterGameTickListener(OnAttendants, 3000, 1500);
            sootheTick = api.Event.RegisterGameTickListener(OnSoothe, 1000, 500);
            api.Event.PlayerDisconnect += OnPlayerDisconnect;
        });
    }

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        nextSoothe.Remove(player.PlayerUID);
        blackoutWarned.Remove(player.PlayerUID);
        BlockBehaviorL3999Cabinet.Forget(player.PlayerUID);
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        walkwayTick = api.Event.RegisterGameTickListener(OnWalkway, 20);
    }

    public override void Dispose()
    {
        if (serverApi != null)
        {
            if (attendantTick != 0) serverApi.Event.UnregisterGameTickListener(attendantTick);
            if (sootheTick != 0) serverApi.Event.UnregisterGameTickListener(sootheTick);
            serverApi.Event.PlayerDisconnect -= OnPlayerDisconnect;
            // (Static, and shared with the client's instance in a single-player game: only the server's own may clear it)
            if (sapi == serverApi) sapi = null;
        }
        if (capi != null && walkwayTick != 0) capi.Event.UnregisterGameTickListener(walkwayTick);
    }

    // ================= Machines and tickets =================

    /// <summary>A player's day at the machines: which day it is, the tickets won, the machines that have paid them.</summary>
    private static ITreeAttribute Day(IServerPlayer player)
    {
        ITreeAttribute tree = player.Entity.Attributes.GetOrAddTreeAttribute(PlayerKey);
        int today = (int)Math.Floor(sapi.World.Calendar.TotalDays);
        if (tree.GetInt("day", int.MinValue) != today)
        {
            tree.SetInt("day", today);
            tree.SetInt("tickets", 0);
            tree.SetString("played", "");
        }
        return tree;
    }

    /// <summary>A machine's entry in the day's <c>played</c> list, which is these run together ("x,y,z;x,y,z;").</summary>
    private static string MachineKey(BlockPos pos) => $"{pos.X},{pos.Y},{pos.Z};";

    /// <summary>
    /// Whether a machine is in the day's <c>played</c> list. (Matched whole: a bare Contains would find "1,64,5;" inside
    /// "11,64,5;" or "-1,64,5;", and refuse a machine that had never paid.)
    /// </summary>
    private static bool HasPlayed(ITreeAttribute day, BlockPos pos) => (";" + day.GetString("played", "")).Contains(";" + MachineKey(pos));

    /// <summary>Whether a machine will pay a player today; if not, says why. (Themed cabinets always play.)</summary>
    public static bool MayPlay(IServerPlayer player, BlockPos pos, bool themed)
    {
        if (themed || sapi == null) return true;
        ITreeAttribute day = Day(player);
        if (HasPlayed(day, pos)) { Say(player, "backrooms:l3999-cabinet-played"); return false; }
        if (day.GetInt("tickets") >= DailyCap) { Say(player, "backrooms:l3999-cabinet-cap"); return false; }
        return true;
    }

    /// <summary>A game played to its end: a themed cabinet takes the player; any other machine pays what it pays.</summary>
    public static void Finish(IServerPlayer player, BlockPos pos, Block block, bool themed)
    {
        if (sapi == null) return;
        if (themed)
        {
            Play(pos, "backrooms:sounds/effect/3999/taken");
            sapi.ModLoader.GetModSystem<ThresholdSystem>()?.Use(player, pos, "l3999-cabinet");
            return;
        }
        if (!MayPlay(player, pos, false)) return;
        ITreeAttribute day = Day(player);
        day.SetString("played", day.GetString("played", "") + MachineKey(pos));
        JsonObject cfg = block.Attributes?["l3999cabinet"];
        Random rand = sapi.World.Rand;
        // A claw machine: now and then a plush instead of tickets
        string[] plush = cfg?["plush"].AsArray<string>();
        if (plush is { Length: > 0 } && rand.NextDouble() < (cfg?["plushChance"].AsDouble(0) ?? 0))
        {
            Give(player, Resolve(sapi.World, "block", plush[rand.Next(plush.Length)], 1), pos);
            Say(player, "backrooms:l3999-cabinet-plush");
            Play(pos, "backrooms:sounds/effect/3999/win");
            return;
        }
        int min = cfg?["min"].AsInt(0) ?? 0, max = cfg?["max"].AsInt(3) ?? 3;
        bool jackpot = rand.NextDouble() < (cfg?["jackpotChance"].AsDouble(0) ?? 0);
        int won = jackpot ? cfg["jackpot"].AsInt(12) : min + rand.Next(Math.Max(0, max - min) + 1);
        won = Math.Min(won, DailyCap - day.GetInt("tickets"));
        if (won <= 0)
        {
            Say(player, "backrooms:l3999-cabinet-lose");
            Play(pos, "backrooms:sounds/effect/3999/lose");
            return;
        }
        day.SetInt("tickets", day.GetInt("tickets") + won);
        Give(player, Resolve(sapi.World, "item", TicketCode, won), pos);
        Say(player, jackpot ? "backrooms:l3999-cabinet-jackpot" : "backrooms:l3999-cabinet-win", won);
        Play(pos, "backrooms:sounds/effect/3999/win");
    }

    /// <summary>How many tickets a player holds in their hand.</summary>
    private static int HeldTickets(IPlayer player, out ItemSlot slot)
    {
        slot = player.InventoryManager?.ActiveHotbarSlot;
        ItemStack stack = slot?.Itemstack;
        return stack?.Collectible?.Code?.ToString() == TicketCode ? stack.StackSize : 0;
    }

    private static void Take(ItemSlot slot, int count)
    {
        slot.TakeOut(count);
        slot.MarkDirty();
    }

    /// <summary>Trading tickets at a prize counter: the most the tier you can afford allows.</summary>
    public static void Prize(IServerPlayer player, BlockPos pos, Block block)
    {
        JsonObject tiers = block.Attributes?["l3999prizes"];
        if (tiers == null || !tiers.Exists) return;
        int held = HeldTickets(player, out ItemSlot slot);
        int tier = 0;
        // (The tiers are keyed by their price: the dearest that the tickets in hand afford)
        for (int cost = Math.Min(held, 10_000); cost > 0 && tier == 0; cost--)
            if (tiers[cost.ToString()].Exists) tier = cost;
        if (tier == 0)
        {
            Say(player, "backrooms:l3999-prize-need");
            Say(player, "backrooms:l3999-prize-tiers");
            return;
        }
        JsonObject[] prizes = tiers[tier.ToString()].AsArray();
        if (prizes == null || prizes.Length == 0) return;
        // A prize whose item does not exist (yet) is never handed out
        for (int attempt = 0; attempt < 8; attempt++)
        {
            JsonObject pick = prizes[sapi.World.Rand.Next(prizes.Length)];
            ItemStack stack = Resolve(sapi.World, pick["type"].AsString("item"), pick["code"].AsString(), pick["quantity"].AsInt(1));
            if (stack == null) continue;
            // (A prize may carry attributes of its own: the lantern's metal and glass)
            if (pick["attributes"].Exists && pick["attributes"].ToAttribute() is ITreeAttribute extra)
                foreach (var pair in extra) stack.Attributes[pair.Key] = pair.Value;
            Take(slot, tier);
            Give(player, stack, pos);
            Say(player, "backrooms:l3999-prize-got");
            Play(pos, "backrooms:sounds/effect/3999/win");
            return;
        }
    }

    /// <summary>Buying a tray meal at a food stall.</summary>
    public static void Stall(IServerPlayer player, BlockPos pos, Block block)
    {
        string food = block.Variant?["stall"] ?? block.Code.Path.Split('-').ElementAtOrDefault(2);
        JsonObject cfg = block.Attributes?["l3999stall"]?[food];
        if (cfg == null || !cfg.Exists) return;
        // (Never free: a stall whose cost is missing or nonsense still takes one ticket)
        int cost = Math.Max(1, cfg["cost"].AsInt(6));
        if (HeldTickets(player, out ItemSlot slot) < cost)
        {
            Say(player, "backrooms:l3999-stall-need");
            return;
        }
        ItemStack meal = Resolve(sapi.World, "item", cfg["meal"].AsString(), 1);
        if (meal == null) return;
        Take(slot, cost);
        Give(player, meal, pos);
        Say(player, "backrooms:l3999-stall-got");
        Play(pos, "game:sounds/player/clayform");
    }

    /// <summary>
    /// A vending machine that takes something (<c>takes</c>: Almond Water) for what it gives (<c>dispenses</c>): one in,
    /// one out, never empty. Called by <see cref="Props.BlockDispenser"/> for blocks with <c>takes</c>.
    /// </summary>
    public static void Vend(IServerPlayer player, BlockPos pos, Block block, string takes)
    {
        ItemSlot slot = player.InventoryManager?.ActiveHotbarSlot;
        if (slot?.Itemstack?.Collectible?.Code?.ToString() != takes)
        {
            Say(player, "backrooms:l3999-vending-need");
            return;
        }
        string[] options = block.Attributes?["dispenses"].AsArray<string>();
        if (options == null || options.Length == 0) return;
        for (int attempt = 0; attempt < 8; attempt++)
        {
            ItemStack stack = Resolve(sapi.World, "item", options[sapi.World.Rand.Next(options.Length)], 1);
            if (stack == null) continue;
            Take(slot, 1);
            Give(player, stack, pos);
            Play(pos, "game:sounds/block/vesselopen");
            return;
        }
    }

    /// <summary>An item or block stack by its code (the backrooms domain unless it names one); null if there is none.</summary>
    private static ItemStack Resolve(IWorldAccessor world, string type, string code, int quantity)
    {
        if (string.IsNullOrEmpty(code)) return null;
        var location = new AssetLocation(code.Contains(':') ? code : "backrooms:" + code);
        CollectibleObject thing = type == "block" ? world.GetBlock(location) : world.GetItem(location);
        thing ??= type == "block" ? world.GetItem(location) : world.GetBlock(location);
        if (thing == null || thing.Id == 0 && thing is Block) return null;
        return new ItemStack(thing, Math.Max(1, quantity));
    }

    private static void Give(IServerPlayer player, ItemStack stack, BlockPos at)
    {
        if (stack == null) return;
        if (!player.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true) || stack.StackSize > 0)
            sapi.World.SpawnItemEntity(stack, at.ToVec3d().Add(0.5, 1.2, 0.5));
    }

    private static void Say(IServerPlayer player, string key, params object[] args) =>
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(key, args), EnumChatType.Notification);

    private static void Play(BlockPos pos, string sound) =>
        sapi?.World.PlaySoundAt(new AssetLocation(sound), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, randomizePitch: true, range: 16);

    // ================= Finding the way =================

    private static readonly string[] DirectionNames = { "n", "ne", "e", "se", "s", "sw", "w", "nw" };

    /// <summary>The name of the direction of an offset (dx east, dz south): "north-east". Shared with The End's catalogue cards.</summary>
    internal static string Direction(double dx, double dz)
    {
        int octant = (int)Math.Round(Math.Atan2(dx, -dz) / (Math.PI / 4));
        return Lang.Get("backrooms:dir-" + DirectionNames[((octant % 8) + 8) % 8]);
    }

    /// <summary>A mall directory: marks the nearest food court and lobby on the player's map, and says which way they lie.</summary>
    public void ReadDirectory(IServerPlayer player, BlockPos pos)
    {
        if (layout == null) return;
        var food = layout.L3999UnitsNear(pos.X, pos.Z, u => u.Kind == WorldLayout.L3999Kind.FoodCourt, 900);
        var lobby = layout.L3999UnitsNear(pos.X, pos.Z, u => u.Kind == WorldLayout.L3999Kind.Lobby, 900);
        if (food.Count == 0 || lobby.Count == 0) return;
        var (fx, fz) = food[0];
        var (lx, lz) = lobby[0];
        MapMarks.Add(sapi, player, new Vec3d(fx + 0.5, pos.Y, fz + 0.5), Lang.Get("backrooms:waypoint-l3999-foodcourt"), "star1", MapMarks.NoteColor, 24, tell: false);
        MapMarks.Add(sapi, player, new Vec3d(lx + 0.5, pos.Y, lz + 0.5), Lang.Get("backrooms:waypoint-l3999-lobby"), "star1", MapMarks.NoteColor, 24, tell: false);
        int Paces(int x, int z) => (int)Math.Round(Math.Sqrt((double)(x - pos.X) * (x - pos.X) + (double)(z - pos.Z) * (z - pos.Z)) / 10) * 10;
        Say(player, "backrooms:l3999-directory", Direction(fx - pos.X, fz - pos.Z), Paces(fx, fz), Direction(lx - pos.X, lz - pos.Z), Paces(lx, lz));
    }

    // ================= Attendants =================

    /// <summary>
    /// Where the attendants stand while anyone is near: behind each prize counter (under its PRIZES sign), each food stall
    /// (under its menu board) and each reception desk (under the LOBBY sign); and the way each faces.
    /// </summary>
    private IEnumerable<(int X, int Z, ArchPier Facing)> AttendantSpots(int px, int pz)
    {
        for (int z = pz - AttendantNear; z <= pz + AttendantNear; z++)
            for (int x = px - AttendantNear; x <= px + AttendantNear; x++)
            {
                Tile t = layout.TileAt(x, z);
                if (t.Level != WorldLayout.Level3999 || t.Kind != TileKind.Floor || WorldLayout.L3999IsDark(t)) continue;
                bool spot = t.Overhead == Overheads.L3999Sign && t.Depth is PrizesSign or ReceptionSign && t.Zone is not ((byte)WorldLayout.L3999Zone.Concourse or (byte)WorldLayout.L3999Zone.Junction)
                    || t.Variant == Worldgen.Props.L3999MenuBoard;
                if (spot) yield return (x, z, t.Pier);
            }
    }

    private void OnAttendants(float dt)
    {
        if (attendantTypes.Length == 0) return;
        var players = sapi.World.AllOnlinePlayers.OfType<IServerPlayer>().Where(p => p.Entity != null && p.ConnectionState == EnumClientState.Playing).ToList();
        // Gone when nobody is near any more, or killed somehow, or unloaded with its chunk (never kept with the world, so
        // it is simply dropped, still "alive": without this its counter would go unstaffed until the server restarted)
        foreach (var key in attendants.Keys.ToList())
        {
            Entity e = attendants[key];
            bool near = false;
            foreach (IServerPlayer p in players)
            {
                double dx = p.Entity.Pos.X - (key.X + 0.5), dz = p.Entity.Pos.Z - (key.Z + 0.5);
                if (dx * dx + dz * dz < AttendantGone * AttendantGone) { near = true; break; }
            }
            if (e.Alive && near && sapi.World.GetEntityById(e.EntityId) != null) continue;
            if (e.Alive) e.Die(EnumDespawnReason.Removed);
            attendants.Remove(key);
        }
        int floor = geometry.FloorFor(WorldLayout.Level3999);
        foreach (IServerPlayer player in players)
        {
            EntityPos pos = player.Entity.Pos;
            int px = (int)Math.Floor(pos.X), pz = (int)Math.Floor(pos.Z);
            if (layout.LevelAt(WorldLayout.MacroOf(px), WorldLayout.MacroOf(pz)) != WorldLayout.Level3999) continue;
            foreach (var (x, z, facing) in AttendantSpots(px, pz))
            {
                if (attendants.ContainsKey((x, z)) || sapi.World.BlockAccessor.GetChunkAtBlockPos(x, floor + 1, z) == null) continue;
                // (in plum or navy, the same at the same counter every time)
                Entity attendant = sapi.World.ClassRegistry.CreateEntity(attendantTypes[(int)((uint)(x * 31 + z * 17) % (uint)attendantTypes.Length)]);
                attendant.Pos.SetPos(x + 0.5, floor + 1, z + 0.5);
                attendant.Pos.Yaw = facing switch { ArchPier.North => GameMath.PI, ArchPier.East => GameMath.PIHALF, ArchPier.West => -GameMath.PIHALF, _ => 0 };
                attendant.WatchedAttributes.SetInt("textureIndex", (x * 31 + z * 17) & 1);
                sapi.World.SpawnEntity(attendant);
                attendants[(x, z)] = attendant;
            }
        }
    }

    /// <summary>
    /// Asked: a chime, a polite line, and the way somewhere, marked on the map: from a lobby's reception desk (under its
    /// LOBBY sign) to the nearest food court; from anywhere else, to the nearest lobby.
    /// </summary>
    public void AttendantInteract(IServerPlayer player, Entity attendant)
    {
        Random rand = sapi.World.Rand;
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/3999/chime"), attendant, null, true, 16);
        Say(player, "backrooms:l3999-attendant-" + (1 + rand.Next(7)));
        if (layout == null) return;
        int x = (int)Math.Floor(attendant.Pos.X), z = (int)Math.Floor(attendant.Pos.Z);
        Tile at = layout.TileAt(x, z);
        bool reception = at.Overhead == Overheads.L3999Sign && at.Depth == ReceptionSign;
        var kind = reception ? WorldLayout.L3999Kind.FoodCourt : WorldLayout.L3999Kind.Lobby;
        var found = layout.L3999UnitsNear(x, z, u => u.Kind == kind, 900);
        if (found.Count == 0) return;
        var (tx, tz) = found[0];
        attendant.AnimManager?.StartAnimation("point");
        string waypoint = reception ? "backrooms:waypoint-l3999-foodcourt" : "backrooms:waypoint-l3999-lobby";
        MapMarks.Add(sapi, player, new Vec3d(tx + 0.5, attendant.Pos.Y, tz + 0.5), Lang.Get(waypoint), "star1", MapMarks.NoteColor, 24);
        Say(player, "backrooms:l3999-attendant-point", Lang.Get(reception ? "backrooms:l3999-place-foodcourt" : "backrooms:l3999-place-lobby"));
    }

    /// <summary>Struck: a chime, and "Please refrain."</summary>
    public void AttendantStruck(IServerPlayer player, Entity attendant)
    {
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/3999/chime"), attendant, null, true, 16);
        Say(player, "backrooms:l3999-attendant-8");
    }

    // ================= The Natatorium, the walkways =================

    /// <summary>
    /// Every second: Paradis Water (standing in a natatorium's water soothes, half a point of health every four seconds),
    /// and the word that the Neon Blackout is near (<see cref="BlackoutNear"/>).
    /// </summary>
    private void OnSoothe(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        foreach (IServerPlayer player in sapi.World.AllOnlinePlayers.OfType<IServerPlayer>())
        {
            EntityPlayer e = player.Entity;
            if (e == null || !e.Alive) continue;
            int x = (int)Math.Floor(e.Pos.X), z = (int)Math.Floor(e.Pos.Z);
            if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.Level3999) continue;
            Tile t = layout.TileAt(x, z);
            BlackoutNear(player, t, now);
            if (t.Kind != TileKind.Water || t.Zone != (byte)WorldLayout.L3999Zone.Natatorium || e.Pos.Y > geometry.FloorFor(WorldLayout.Level3999) + 1.2) continue;
            if (nextSoothe.TryGetValue(player.PlayerUID, out long next) && now < next) continue;
            nextSoothe[player.PlayerUID] = now + 4000;
            e.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Internal, Type = EnumDamageType.Heal }, 0.5f);
        }
    }

    /// <summary>
    /// The first failing neon (within 48 blocks of a block of the Neon Blackout, where the tiles' drift starts): told once,
    /// and again only after they have been back under neon that works, at least a minute after they were told (so that a
    /// walk along the fringe's edge is not a message every few steps).
    /// </summary>
    private void BlackoutNear(IServerPlayer player, in Tile t, long now)
    {
        if (WorldLayout.L3999IsDark(t)) return;
        if (WorldLayout.L3999Drift(t) > 0)
        {
            if (blackoutWarned.TryAdd(player.PlayerUID, now)) Say(player, "backrooms:l3999-blackout-near");
        }
        else if (blackoutWarned.TryGetValue(player.PlayerUID, out long at) && now - at > 60_000) blackoutWarned.Remove(player.PlayerUID);
    }

    /// <summary>On the client: a walkway's tread carries the player standing on it the way its chevrons point.</summary>
    private void OnWalkway(float dt)
    {
        EntityPlayer e = capi?.World?.Player?.Entity;
        if (e == null || !e.OnGround || dt > 0.25f) return;
        // (The client moves its own player: in 1.22 an entity has one position, Pos, on either side)
        EntityPos pos = e.Pos;
        Block block = capi.World.BlockAccessor.GetBlock(walkwayProbe.Set((int)Math.Floor(pos.X), (int)Math.Floor(pos.Y - 0.1), (int)Math.Floor(pos.Z)));
        JsonObject cfg = block?.Attributes?["l3999walkway"];
        if (cfg == null || !cfg.Exists) return;
        string flow = block.Code.Path.Substring(block.Code.Path.LastIndexOf('-') + 1);
        (double dx, double dz) = flow switch { "n" => (0.0, -1.0), "s" => (0.0, 1.0), "e" => (1.0, 0.0), "w" => (-1.0, 0.0), _ => (0.0, 0.0) };
        double step = cfg["speed"].AsDouble(2.5) * dt;
        double nx = pos.X + dx * step, nz = pos.Z + dz * step;
        // Never into anything solid (a rail, a wall)
        for (double up = 0.1; up < 2; up += 1)
        {
            Block ahead = capi.World.BlockAccessor.GetBlock(walkwayProbe.Set((int)Math.Floor(nx + dx * 0.3), (int)Math.Floor(pos.Y + up), (int)Math.Floor(nz + dz * 0.3)));
            if (ahead.CollisionBoxes is { Length: > 0 } && ahead.Attributes?["l3999walkway"].Exists != true) return;
        }
        pos.X = nx;
        pos.Z = nz;
    }

    // ================= Level 10's windmills =================

    /// <summary>Throwing a windmill's lever: it stays up, and the beacon on the cap turns green, for everyone.</summary>
    public static void ThrowLever(IServerPlayer player, BlockPos pos, Block block)
    {
        if (block.Variant?["state"] == "on")
        {
            Say(player, "backrooms:l3999-generator-done");
            return;
        }
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        Block on = sapi.World.GetBlock(block.CodeWithVariant("state", "on"));
        if (on != null && on.BlockId != 0) blocks.ExchangeBlock(on.BlockId, pos);
        // The beacon: on the windmill's middle, four blocks behind the generator, up on the cap
        string facing = block.Variant?["facing"] ?? "north";
        (int dx, int dz) = facing switch { "north" => (0, 1), "south" => (0, -1), "east" => (-1, 0), _ => (1, 0) };
        Block green = sapi.World.GetBlock(new AssetLocation("backrooms:l3999-beacon-green"));
        for (int up = 0; up <= 10 && green != null; up++)
        {
            var at = new BlockPos(pos.X + dx * 4, pos.Y + up, pos.Z + dz * 4);
            if (blocks.GetBlock(at).Code?.Path == "l3999-beacon-red") { blocks.ExchangeBlock(green.BlockId, at); break; }
        }
        Play(pos, "game:sounds/effect/latch");
        Say(player, "backrooms:l3999-generator-on");
    }
}

/// <summary>
/// An arcade machine (or a themed cabinet): hold to play, for <c>seconds</c> (a themed one's <c>l3999playSeconds</c>).
/// The server times the game by its own clock: how long the client says the button was held only ends it, so a client
/// that counts faster than time passes gets nothing.
/// </summary>
public class BlockBehaviorL3999Cabinet : BlockBehavior
{
    /// <summary>
    /// How much shorter than the game the server's own count may be and still pay: the start reaches it a little later
    /// than the client began, and the end a little sooner or later, by the connection's lag.
    /// </summary>
    private const long LagSlackMs = 750;

    /// <summary>
    /// Server side (only ever touched there): where each player (by uid) began a game, and when by the server's clock.
    /// (Static: a player plays one machine at a time, whatever its type.)
    /// </summary>
    private static readonly Dictionary<string, (BlockPos Pos, long StartMs)> playing = new();

    public bool Themed;
    private WorldInteraction[] help;

    /// <summary>Forgets a player's game (given up, or they left the server).</summary>
    public static void Forget(string uid) => playing.Remove(uid);

    public BlockBehaviorL3999Cabinet(Block block) : base(block)
    {
    }

    private float Seconds => Themed ? block.Attributes?["l3999playSeconds"].AsFloat(20) ?? 20 : block.Attributes?["l3999cabinet"]?["seconds"].AsFloat(4) ?? 4;

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l3999-cabinet", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
        {
            if (!L3999System.MayPlay(player, blockSel.Position, Themed)) return false;
            playing[player.PlayerUID] = (blockSel.Position.Copy(), world.ElapsedMilliseconds);
            world.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/3999/play"), blockSel.Position.X + 0.5, blockSel.Position.Y + 0.5, blockSel.Position.Z + 0.5, null, true, 12);
        }
        return true;
    }

    public override bool OnBlockInteractStep(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        return secondsUsed < Seconds;
    }

    public override void OnBlockInteractStop(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side != EnumAppSide.Server || byPlayer is not IServerPlayer player) return;
        if (!playing.Remove(player.PlayerUID, out var game)) return;
        // Played to the end: by the client's count, and (give or take the lag) by the server's own clock, at this machine
        bool held = secondsUsed >= Seconds - 0.1f;
        bool timed = world.ElapsedMilliseconds - game.StartMs >= (long)(Seconds * 1000) - LagSlackMs;
        if (held && timed && game.Pos.Equals(blockSel.Position)) L3999System.Finish(player, blockSel.Position.Copy(), block, Themed);
    }

    public override bool OnBlockInteractCancel(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        if (world.Side == EnumAppSide.Server && byPlayer != null) Forget(byPlayer.PlayerUID);
        return true;
    }
}

/// <summary>A prize counter: right-click with tickets in hand.</summary>
public class BlockBehaviorL3999Prizes : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL3999Prizes(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l3999-prize", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player) L3999System.Prize(player, blockSel.Position, block);
        return true;
    }
}

/// <summary>A food stall's counter: right-click with tickets in hand for a tray meal.</summary>
public class BlockBehaviorL3999Stall : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL3999Stall(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l3999-stall", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player) L3999System.Stall(player, blockSel.Position, block);
        return true;
    }
}

/// <summary>A mall directory: right-click to find the way.</summary>
public class BlockBehaviorL3999Directory : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL3999Directory(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l3999-directory", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player) sapi.ModLoader.GetModSystem<L3999System>()?.ReadDirectory(player, blockSel.Position);
        return true;
    }
}

/// <summary>A windmill's generator in Level 10: throw the lever.</summary>
public class BlockBehaviorL3999Generator : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL3999Generator(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l3999-generator", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player) L3999System.ThrowLever(player, blockSel.Position, block);
        return true;
    }
}

/// <summary>
/// A vending machine's interaction help (it takes Almond Water). The machine itself works through its block class,
/// BackroomsDispenser, which never asks its behaviours, so this only answers for the help.
/// </summary>
public class BlockBehaviorL3999Vending : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL3999Vending(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l3999-vending", MouseButton = EnumMouseButton.Right } };
        return help;
    }
}

/// <summary>An Arcade Attendant: faceless, polite, made of plastic. Cannot be hurt, is never kept with the world; asked, it points the way.</summary>
public class EntityL3999Attendant : EntityAgent
{
    public override bool StoreWithChunk => false;
    public override bool IsInteractable => true;

    public override bool ShouldReceiveDamage(DamageSource damageSource, float damage) => false;

    public override bool ReceiveDamage(DamageSource damageSource, float damage)
    {
        if (World.Side == EnumAppSide.Server && damageSource?.GetCauseEntity() is EntityPlayer { Player: IServerPlayer player })
            ((ICoreServerAPI)World.Api).ModLoader.GetModSystem<L3999System>()?.AttendantStruck(player, this);
        return false;
    }

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode)
    {
        if (World.Side != EnumAppSide.Server) return;
        if (byEntity is not EntityPlayer { Player: IServerPlayer player }) return;
        var rules = ((ICoreServerAPI)World.Api).ModLoader.GetModSystem<L3999System>();
        if (mode == EnumInteractMode.Interact) rules?.AttendantInteract(player, this);
        else rules?.AttendantStruck(player, this);
    }
}
