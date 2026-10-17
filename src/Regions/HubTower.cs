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
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// The Hub's people (docs/design/new-levels/hub-plan.md 2.6, 2.7):
/// <list type="bullet">
/// <item><b>The Tower</b> lets each person in once (canon: "Upon exiting The Tower, it will be impossible to re-enter
/// afterwards"). Whoever has been inside and is outside again, however they left, is never let in again.</item>
/// <item><b>The Keymaster</b> appears to each visitor once: at once if they carry a Level Key, otherwise when they reach
/// the meeting hall. Right-click him and he holds out the key to one of the levels you have been to, another each time;
/// sneak and right-click to take it. He then shows you to its door, and the Tower is closed to you. Break anything of the
/// Tower's own and he throws you out with nothing (what you put down yourself, a torch to see by, is yours to break).
/// <c>/backrooms hub reset [player]</c> lets someone in again.</item>
/// <item><b>The M.E.G.'s "Doorstep Carpet"</b> by the Level 11 door: its wanderer sells two Level Keys at a time, chosen
/// afresh each week from the levels anyone in the world has entered, for 30-45 rusty gears.</item>
/// <item><b>The door register</b> there marks on your map the three open doors, the Tower's ten doors and the outpost.</item>
/// </list>
/// </summary>
public partial class HubSystem
{
    private const string VisitedKey = "backrooms:visitedLevels", InTowerKey = "backrooms:hubInTower", TowerVisitedKey = "backrooms:hubTowerVisited",
        GiftKey = "backrooms:hubKeymasterGift", ChoiceKey = "backrooms:hubKeymasterChoice", EnteredSaveKey = "backrooms-hub-entered", MegKey = "backrooms:megKeys";

    /// <summary>The levels whose keys the Keymaster and the M.E.G. deal in (those whose doors need a key), in order.</summary>
    private static readonly int[] KeyedLevels =
        { 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, WorldLayout.Poolrooms, WorldLayout.Motion, WorldLayout.RunLevel, WorldLayout.FunLevel, WorldLayout.TheEnd, WorldLayout.Level3999 };

    /// <summary>Every level anyone in the world has entered (bits by level id).</summary>
    private int entered;
    private readonly Dictionary<string, Entity> keymasters = new();
    /// <summary>Players the Keymaster is in the middle of showing out (his gesture plays before they are put out).</summary>
    private readonly HashSet<string> escorting = new();
    /// <summary>Where players have put blocks down in the Tower this session (a torch to see by): theirs to break again.</summary>
    private readonly HashSet<BlockPos> placedInTower = new();

    private void StartTower(ICoreServerAPI api)
    {
        byte[] data = api.WorldManager.SaveGame.GetData(EnteredSaveKey);
        if (data != null && data.Length == 4) entered = BitConverter.ToInt32(data, 0);
        api.Event.GameWorldSave += SaveEntered;
        ticks.Add(api.Event.RegisterGameTickListener(OnTowerTick, 1000, 1500));
        ticks.Add(api.Event.RegisterGameTickListener(OnMegTick, 30_000, 7000));
        api.Event.PlayerDisconnect += OnTowerDisconnect;
        api.Event.DidPlaceBlock += OnTowerPlace;
    }

    /// <summary>Takes the Tower's handlers off again (its tick listeners are among <see cref="HubSystem"/>'s own).</summary>
    private void StopTower(ICoreServerAPI api)
    {
        api.Event.GameWorldSave -= SaveEntered;
        api.Event.PlayerDisconnect -= OnTowerDisconnect;
        api.Event.DidPlaceBlock -= OnTowerPlace;
    }

    /// <summary><c>/backrooms hub reset [player]</c>: another visit to the Tower. (Registered once the game runs: the command itself is made at start-up.)</summary>
    private static void RegisterTowerCommand(ICoreServerAPI api)
    {
        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        command
            .BeginSubCommand("hub")
                .WithDescription("The Hub's Tower")
                .BeginSubCommand("reset")
                    .WithDescription("Lets a player (you, if no name is given) into the Tower again as if they had never been: forgets their visit, and the Keymaster's key or his throwing them out")
                    .WithArgs(api.ChatCommands.Parsers.OptionalWord("player"))
                    .HandleWith(args => api.ModLoader.GetModSystem<HubSystem>().OnHubResetCommand(args))
                .EndSubCommand()
            .EndSubCommand();
    }

    private TextCommandResult OnHubResetCommand(TextCommandCallingArgs args)
    {
        string name = (args[0] as string)?.Trim(); // (the console's line ending arrives as an argument)
        IServerPlayer who = string.IsNullOrEmpty(name) ? args.Caller.Player as IServerPlayer
            : sapi.World.AllOnlinePlayers.OfType<IServerPlayer>().FirstOrDefault(p => p.PlayerName.Equals(name, StringComparison.OrdinalIgnoreCase));
        if (who?.Entity == null) return TextCommandResult.Error(string.IsNullOrEmpty(name) ? "Give a player's name." : "No such player online: " + name);
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world.");
        ResetTower(who);
        return TextCommandResult.Success($"The Tower will let {who.PlayerName} in again, and the Keymaster will come down to them once more.");
    }

    /// <summary>
    /// Forgets a player's visit to the Tower: its doors open for them again and the Keymaster offers a key once more. (The
    /// same flags the Tower keeps, set back to what a new player has, so nothing new is saved.)
    /// </summary>
    private void ResetTower(IServerPlayer player)
    {
        Dismiss(player.PlayerUID);
        SyncedTreeAttribute attributes = player.Entity.WatchedAttributes;
        attributes.SetBool(TowerVisitedKey, false);
        attributes.SetBool(GiftKey, false);
        attributes.SetInt(ChoiceKey, -1);
        sapi.Logger.Notification("[backrooms] the Tower forgets {0}'s visit (hub reset)", player.PlayerName);
    }

    private void SaveEntered() => sapi.WorldManager.SaveGame.StoreData(EnteredSaveKey, BitConverter.GetBytes(entered));

    private void OnTowerDisconnect(IServerPlayer player)
    {
        Dismiss(player.PlayerUID);
        nextChime.Remove(player.PlayerUID);
        keyNear.Remove(player.PlayerUID);
    }

    // ================= Who has been where =================

    /// <summary>Whether a player has been inside the Tower and come out again (it will not let them in twice).</summary>
    public static bool TowerVisited(IPlayer player) => player.Entity?.WatchedAttributes.GetBool(TowerVisitedKey) == true;

    private static bool HasVisited(IPlayer player, int level) => (player.Entity.WatchedAttributes.GetInt(VisitedKey) & (1 << level)) != 0;

    private void OnTowerTick(float dt)
    {
        if (layout == null) return;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { Alive: true } entity } player) continue;
            EntityPos pos = entity.Pos;
            int level = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(pos.X)), WorldLayout.MacroOf((int)Math.Floor(pos.Z)));
            // The levels this player has been to (for the Keymaster), and that anyone has (for the M.E.G.)
            if (level is >= 0 and < 31)
            {
                int bits = entity.WatchedAttributes.GetInt(VisitedKey);
                if ((bits & (1 << level)) == 0) entity.WatchedAttributes.SetInt(VisitedKey, bits | (1 << level));
                entered |= 1 << level;
            }

            bool inTower = level == WorldLayout.Hub && layout.InHubTower(pos.X, pos.Z);
            bool wasIn = entity.WatchedAttributes.GetBool(InTowerKey);
            if (inTower != wasIn) entity.WatchedAttributes.SetBool(InTowerKey, inTower);
            if (!inTower)
            {
                // Out again, by a door, the Keymaster, the void or death: the Tower will not have them back
                if (wasIn) entity.WatchedAttributes.SetBool(TowerVisitedKey, true);
                Dismiss(player.PlayerUID);
                continue;
            }
            if (entity.WatchedAttributes.GetBool(GiftKey) || keymasters.ContainsKey(player.PlayerUID)) continue;
            bool carriesKey = FindKey(player, -1) != null;
            bool inHall = pos.Y >= geometry.FloorFor(WorldLayout.Hub) + WorldLayout.HubTowerHall;
            if (carriesKey || inHall) Summon(player);
        }
    }

    // ================= The Keymaster =================

    private void Summon(IServerPlayer player)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation("backrooms:hub-keymaster"));
        if (type == null) return;
        Entity keymaster = sapi.World.ClassRegistry.CreateEntity(type);
        EntityPos pos = player.Entity.Pos;
        // A few steps from them, toward the middle, and on their own floor: he comes down from above
        double dx = layout.HubOriginX + 0.5 - pos.X, dz = layout.HubOriginZ + 0.5 - pos.Z, d = Math.Max(0.001, Math.Sqrt(dx * dx + dz * dz));
        double step = Math.Min(3, d - 1.5);
        double x = pos.X + dx / d * step, z = pos.Z + dz / d * step, y = Math.Floor(pos.Y + 0.01);
        keymaster.Pos.SetPos(x, y, z);
        keymaster.Pos.Yaw = (float)Math.Atan2(-dx, -dz);
        // (Whose he is: each visitor has their own, and the client shows his help only to them)
        keymaster.WatchedAttributes.SetString(EntityKeymaster.ForKey, player.PlayerUID);
        sapi.World.SpawnEntity(keymaster);
        keymaster.StartAnimation("descend");
        keymasters[player.PlayerUID] = keymaster;
        player.Entity.WatchedAttributes.SetInt(ChoiceKey, -1);
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/hub/keyjingle"), x, y + 1.5, z, null, true, 16, 1f);
        Say(player, "backrooms:hub-keymaster-1");
        sapi.Logger.Notification("[backrooms] the Keymaster comes down to {0} in the Tower", player.PlayerName);
    }

    /// <summary>Ends an audience: a curt backhand flick ("dismiss"), and he is gone a moment later.</summary>
    private void Dismiss(string uid)
    {
        if (!keymasters.TryGetValue(uid, out Entity keymaster)) return;
        keymasters.Remove(uid);
        if (!keymaster.Alive) return;
        keymaster.StopAnimation("stride");
        keymaster.StartAnimation("dismiss");
        sapi.Event.RegisterCallback(_ => { if (keymaster.Alive) keymaster.Die(EnumDespawnReason.Removed); }, 800);
    }

    private void Say(IServerPlayer player, string key, params object[] args)
    {
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(key, args), EnumChatType.Notification);
        if (keymasters.TryGetValue(player.PlayerUID, out Entity keymaster))
            sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/hub/keymaster"), keymaster, null, true, 16, 0.8f);
    }

    /// <summary>
    /// Someone right-clicks the Keymaster. He holds out the key to a level they have been to, another each time; sneaking,
    /// they take the one he holds, and he shows them to its door. He answers only the visitor he came down to: anyone
    /// else's is deaf to them (otherwise a second player could take a key from someone else's audience).
    /// </summary>
    public void KeymasterInteract(IServerPlayer player, Entity keymaster)
    {
        if (!keymasters.TryGetValue(player.PlayerUID, out Entity mine) || mine != keymaster) return;
        if (player.Entity.WatchedAttributes.GetBool(GiftKey))
        {
            // Already given his key: he waves them off
            keymaster.StartAnimation("dismiss");
            Say(player, "backrooms:hub-keymaster-3");
            return;
        }
        int[] choices = KeyedLevels.Where(l => HasVisited(player, l) && sapi.World.GetItem(new AssetLocation("backrooms:" + KeyPrefix + KeyTag(l))) != null).ToArray();
        if (choices.Length == 0) choices = new[] { 0 };
        int choice = player.Entity.WatchedAttributes.GetInt(ChoiceKey, -1);
        bool sneaking = player.Entity.Controls.Sneak;
        if (!sneaking || choice < 0 || choice >= choices.Length)
        {
            // (The first time asked, he says so; then the first key)
            if (choice < 0) Say(player, "backrooms:hub-keymaster-2");
            choice = (choice + 1) % choices.Length;
            player.Entity.WatchedAttributes.SetInt(ChoiceKey, choice);
            keymaster.StartAnimation("jingle");
            Say(player, "backrooms:hub-keymaster-offer", LevelName(choices[choice]));
            return;
        }

        // The key, and the way to its door
        int level = choices[choice];
        Item key = sapi.World.GetItem(new AssetLocation("backrooms:" + KeyPrefix + KeyTag(level)));
        if (key != null && !player.InventoryManager.TryGiveItemstack(new ItemStack(key), true))
            sapi.World.SpawnItemEntity(new ItemStack(key), player.Entity.Pos.XYZ);
        player.Entity.WatchedAttributes.SetBool(GiftKey, true);
        keymaster.StartAnimation("point");
        Say(player, "backrooms:hub-keymaster-3");
        sapi.Logger.Notification("[backrooms] the Keymaster gives {0} the key to level {1}", player.PlayerName, level);
        // He points, then strides up to them, and shows them to its door
        EscortAfter(player, level, 1200, 1000);
    }

    /// <summary>
    /// Shows someone out after a beat, so his gesture is seen: waits <paramref name="waitMs"/>, then (if
    /// <paramref name="strideMs"/> &gt; 0) strides toward them that long, then <see cref="Escort"/>s them.
    /// </summary>
    private void EscortAfter(IServerPlayer player, int level, int waitMs, int strideMs)
    {
        string uid = player.PlayerUID;
        if (!escorting.Add(uid)) return;
        sapi.Event.RegisterCallback(_ =>
        {
            long walk = 0;
            if (strideMs > 0 && keymasters.TryGetValue(uid, out Entity keymaster) && keymaster.Alive)
            {
                keymaster.StopAnimation("point");
                keymaster.StartAnimation("stride");
                walk = sapi.Event.RegisterGameTickListener(_ => StrideToward(keymaster, player), 50);
            }
            sapi.Event.RegisterCallback(_ =>
            {
                if (walk != 0) sapi.Event.UnregisterGameTickListener(walk);
                escorting.Remove(uid);
                if (player.ConnectionState != EnumClientState.Playing || player.Entity is not { Alive: true }) Dismiss(uid);
                else Escort(player, level);
            }, Math.Max(1, strideMs));
        }, waitMs);
    }

    /// <summary>One step of his stride toward someone (he floats, so he is moved by hand), stopping at arm's length.</summary>
    private static void StrideToward(Entity keymaster, IServerPlayer player)
    {
        if (!keymaster.Alive || player.Entity == null) return;
        EntityPos to = player.Entity.Pos, at = keymaster.Pos;
        double dx = to.X - at.X, dz = to.Z - at.Z, d = Math.Sqrt(dx * dx + dz * dz);
        if (d < 0.001) return;
        at.Yaw = (float)Math.Atan2(dx, dz);
        if (d > 1.6)
        {
            double step = Math.Min(0.16, d - 1.6);
            at.X += dx / d * step;
            at.Z += dz / d * step;
        }
    }

    /// <summary>Puts someone out of the Tower: in front of a level's door if one is given, else on the approach nearest them.</summary>
    private void Escort(IServerPlayer player, int level = -1)
    {
        double floor = geometry.FloorFor(WorldLayout.Hub);
        if (level >= 0 && layout.HubDoorOf(level) is { } door)
        {
            var (fx, fz) = door.Facing switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
            player.Entity.TeleportToDouble(door.X + fx + 0.5, floor + 1.55, door.Z + fz + 0.5);
        }
        else
        {
            double angle = Math.Atan2(player.Entity.Pos.Z - layout.HubOriginZ, player.Entity.Pos.X - layout.HubOriginX);
            int k = Enumerable.Range(0, 10).OrderBy(i =>
            {
                var (ux, uz) = layout.HubSpokeDirection(i);
                return Math.Abs(Math.IEEERemainder(angle - Math.Atan2(uz, ux), 2 * Math.PI));
            }).First();
            var (dx, dz) = layout.HubSpokeDirection(k);
            player.Entity.TeleportToDouble(layout.HubOriginX + 0.5 + dx * 28.5, floor + 1.05, layout.HubOriginZ + 0.5 + dz * 28.5);
        }
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/door"), player.Entity, null, true, 16, 1f);
        player.Entity.WatchedAttributes.SetBool(TowerVisitedKey, true);
        Dismiss(player.PlayerUID);
    }

    /// <summary>Whether a position is in the Tower (the Hub's; the same ring of blocks in some other level is not).</summary>
    private bool InTower(BlockPos pos) =>
        layout != null && layout.InHubTower(pos.X + 0.5, pos.Z + 0.5) && layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z)) == WorldLayout.Hub;

    /// <summary>Whether a block is of the Tower's own fabric (its marble, ashlar, doors, statue, lights, and the concrete behind them).</summary>
    private static bool IsTowerFabric(Block block) =>
        block?.Code != null && block.Code.Domain == "backrooms" && (block.Code.Path.StartsWith("hub-") || block.Code.Path == "concrete");

    /// <summary>Something put down in the Tower (a torch to see by) is remembered as the player's own: taking it up again is no offence.</summary>
    private void OnTowerPlace(IServerPlayer byPlayer, int oldblockId, BlockSelection blockSel, ItemStack withItemStack)
    {
        if (byPlayer != null && blockSel != null && InTower(blockSel.Position)) placedInTower.Add(blockSel.Position.Copy());
    }

    /// <summary>
    /// Something of the Tower's own broken: the Keymaster throws whoever broke it out, with nothing. What a player put down
    /// themselves is theirs to take up again: remembered by position this session, and by kind (nothing of the Tower's
    /// fabric) after a restart.
    /// </summary>
    private void OnTowerBreak(IServerPlayer byPlayer, int oldblockId, BlockPos pos)
    {
        if (byPlayer?.Entity == null || !InTower(pos)) return;
        if (placedInTower.Remove(pos) || !IsTowerFabric(sapi.World.GetBlock(oldblockId))) return;
        if (!keymasters.ContainsKey(byPlayer.PlayerUID) && !byPlayer.Entity.WatchedAttributes.GetBool(GiftKey)) Summon(byPlayer);
        Say(byPlayer, "backrooms:hub-keymaster-angry");
        byPlayer.Entity.WatchedAttributes.SetBool(GiftKey, true);
        // A shove (its blow lands about half a second in), and out they go
        if (!escorting.Contains(byPlayer.PlayerUID) && keymasters.TryGetValue(byPlayer.PlayerUID, out Entity keymaster)) keymaster.StartAnimation("shove");
        EscortAfter(byPlayer, -1, 450, 0);
    }

    // ================= The M.E.G.'s Level Keys =================

    /// <summary>
    /// The wanderer at the M.E.G.'s outpost keeps two Level Keys among its wares: chosen each week from the levels anyone
    /// in the world has entered, one of each, for 30-45 rusty gears. Put back if the trader's own restocking pushes them
    /// out, until they are sold.
    /// </summary>
    private void OnMegTick(float dt)
    {
        if (layout == null || layout.HubMegSite() is not { } site) return;
        int week = (int)Math.Floor(sapi.World.Calendar.TotalDays / 7);
        var near = sapi.World.GetEntitiesAround(new Vec3d(site.X + 0.5, geometry.FloorFor(WorldLayout.Hub) + 1.5, site.Z + 0.5), 14, 6,
            e => e is EntityTradingHumanoid && e.Code?.Domain == "backrooms" && e.Code.Path.StartsWith("wanderer"));
        foreach (Entity e in near) StockKeys((EntityTradingHumanoid)e, week);
    }

    private void StockKeys(EntityTradingHumanoid trader, int week)
    {
        if (trader.Inventory == null) return;
        ITreeAttribute tree = trader.WatchedAttributes.GetOrAddTreeAttribute(MegKey);
        if (tree.GetInt("week", -1) != week)
        {
            int[] candidates = KeyedLevels.Where(l => (entered & (1 << l)) != 0 && sapi.World.GetItem(new AssetLocation("backrooms:" + KeyPrefix + KeyTag(l))) != null).ToArray();
            var picks = new List<int>();
            for (int n = 0; n < 8 && picks.Count < Math.Min(2, candidates.Length); n++)
            {
                int l = candidates[(int)(Hashing.Hash((ulong)sapi.World.Seed, week, n, 0x17F0) % (ulong)candidates.Length)];
                if (!picks.Contains(l)) picks.Add(l);
            }
            tree.SetInt("week", week);
            tree.SetString("tags", string.Join(",", picks.Select(KeyTag)));
            tree.SetString("stock", string.Join(",", picks.Select(_ => "1")));
            tree.SetString("price", string.Join(",", picks.Select((_, i) => (30 + (int)(Hashing.Hash((ulong)sapi.World.Seed, week, i, 0x17F1) % 16)).ToString())));
        }
        string[] tags = tree.GetString("tags", "").Split(',', StringSplitOptions.RemoveEmptyEntries);
        int[] stock = tree.GetString("stock", "").Split(',', StringSplitOptions.RemoveEmptyEntries).Select(int.Parse).ToArray();
        int[] price = tree.GetString("price", "").Split(',', StringSplitOptions.RemoveEmptyEntries).Select(int.Parse).ToArray();
        ItemSlotTrade[] slots = trader.Inventory.SellingSlots;
        bool changed = false;
        for (int i = 0; i < tags.Length && i < stock.Length && i < price.Length; i++)
        {
            Item key = sapi.World.GetItem(new AssetLocation("backrooms:" + KeyPrefix + tags[i]));
            if (key == null) continue;
            ItemSlotTrade held = slots.FirstOrDefault(s => s?.Itemstack?.Collectible == key && s.TradeItem != null);
            if (held != null)
            {
                stock[i] = held.TradeItem.Stock;
                continue;
            }
            if (stock[i] <= 0) continue;
            // Back among the wares: the last free slot, or the last slot
            ItemSlotTrade slot = slots.LastOrDefault(s => s != null && s.Itemstack == null) ?? slots[slots.Length - 1 - i];
            slot.SetTradeItem(new ResolvedTradeItem
            {
                Stack = new ItemStack(key), Price = price[i], Stock = stock[i],
                Restock = new RestockOpts { HourDelay = 0, Quantity = 0 },
                SupplyDemand = new SupplyDemandOpts { PriceChangePerDay = 0, PriceChangePerPurchase = 0 },
            });
            changed = true;
        }
        tree.SetString("stock", string.Join(",", stock));
        if (!changed) return;
        if (trader.WatchedAttributes["traderInventory"] is ITreeAttribute store) trader.Inventory.ToTreeAttributes(store);
        trader.WatchedAttributes.MarkAllDirty();
    }

    // ================= The door register =================

    /// <summary>Reading the M.E.G.'s door register: the three open doors, the Tower's ten doors and the outpost go on your map.</summary>
    public void ReadRegister(IServerPlayer player)
    {
        if (layout == null) return;
        double y = geometry.FloorFor(WorldLayout.Hub) + 1.5;
        // (Where the map setting makes no waypoints, each place is told instead: the Tower once, by its nearest door)
        bool waypoints = MapSetting.Waypoints(sapi.World.Config);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(waypoints ? "backrooms:hub-register-read" : "backrooms:hub-register-read-nomap"), EnumChatType.Notification);
        foreach (int level in new[] { 1, 11, WorldLayout.HubSnackroomsDoor })
            if (layout.HubDoorOf(level) is { } door)
                MapMarks.Add(sapi, player, new Vec3d(door.X + 0.5, y, door.Z + 0.5), Lang.Get("backrooms:waypoint-hubdoor", LevelName(level)), "spiral", MapMarks.WayColor, 6);
        int nearest = 0;
        double nearestD = double.MaxValue;
        for (int k = 0; k < 10; k++)
        {
            var (dx, dz) = layout.HubSpokeDirection(k);
            double ex = layout.HubOriginX + 0.5 + dx * 26 - player.Entity.Pos.X, ez = layout.HubOriginZ + 0.5 + dz * 26 - player.Entity.Pos.Z;
            if (ex * ex + ez * ez < nearestD) { nearestD = ex * ex + ez * ez; nearest = k; }
        }
        for (int k = 0; k < 10; k++)
        {
            var (dx, dz) = layout.HubSpokeDirection(k);
            MapMarks.Add(sapi, player, new Vec3d(layout.HubOriginX + 0.5 + dx * 26, y, layout.HubOriginZ + 0.5 + dz * 26),
                Lang.Get("backrooms:waypoint-hubtower"), "star1", MapMarks.WayColor, 4, tell: k == nearest);
        }
        if (layout.HubMegSite() is { } site)
            MapMarks.Add(sapi, player, new Vec3d(site.X + 0.5, y, site.Z + 0.5), Lang.Get("backrooms:waypoint-hubmeg"), "home", MapMarks.NoteColor, 6);
    }
}

/// <summary>The Keymaster: he cannot be hurt, is never kept with the world, and right-clicking him asks for a key.</summary>
public class EntityKeymaster : EntityAgent
{
    /// <summary>Watched attribute: the uid of the visitor he came down to.</summary>
    public const string ForKey = "backrooms:keymasterFor";

    private static WorldInteraction[] help;

    public override bool StoreWithChunk => false;
    public override bool IsInteractable => true;

    /// <summary>Right-click for another key, sneak and right-click to take it: shown only to the visitor he came down to.</summary>
    public override WorldInteraction[] GetInteractionHelp(IClientWorldAccessor world, EntitySelection es, IClientPlayer player)
    {
        if (WatchedAttributes.GetString(ForKey) != player?.PlayerUID) return Array.Empty<WorldInteraction>();
        return help ??= new[]
        {
            new WorldInteraction { ActionLangCode = "backrooms:hub-keymaster-choose", MouseButton = EnumMouseButton.Right },
            new WorldInteraction { ActionLangCode = "backrooms:hub-keymaster-take", MouseButton = EnumMouseButton.Right, HotKeyCode = "sneak" },
        };
    }

    public override bool ShouldReceiveDamage(DamageSource damageSource, float damage) => false;

    public override bool ReceiveDamage(DamageSource damageSource, float damage) => false;

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode)
    {
        if (mode != EnumInteractMode.Interact || World.Side != EnumAppSide.Server) return;
        if (byEntity is EntityPlayer { Player: IServerPlayer player })
            ((ICoreServerAPI)World.Api).ModLoader.GetModSystem<HubSystem>().KeymasterInteract(player, this);
    }
}

/// <summary>The M.E.G.'s door register: right-click to read it.</summary>
public class BlockBehaviorHubRegister : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorHubRegister(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-register", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player) sapi.ModLoader.GetModSystem<HubSystem>().ReadRegister(player);
        return true;
    }
}
