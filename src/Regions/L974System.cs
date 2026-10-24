using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Map;
using Backrooms.Salvage;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// What counts as cute, for Kitty (and for the Hub's pink ribbon door, which calls <see cref="CarriesCute"/>).
/// </summary>
public static class L974
{
    /// <summary>On an item or block type (its attributes) or on one stack: this is cute.</summary>
    public const string CuteKey = "backroomsCute";
    /// <summary>On a stack: brought into Kitty's House on this visit (its id): the gift Kitty will take.</summary>
    public const string BroughtKey = "l974Brought";
    /// <summary>On a stack: got inside Kitty's House (the dresser's clothes): Kitty's own, never a gift.</summary>
    public const string KittysKey = "l974Kitty";

    /// <summary>Whether a stack is something Kitty finds cute.</summary>
    public static bool IsCute(ItemStack stack) =>
        stack?.Collectible != null && (stack.Collectible.Attributes?[CuteKey].AsBool(false) == true || stack.Attributes?.GetBool(CuteKey) == true);

    private static readonly string[] CarriedInventories = { GlobalConstants.hotBarInvClassName, GlobalConstants.backpackInvClassName };

    /// <summary>The slots a player carries things in: the hotbar and the backpack.</summary>
    public static IEnumerable<ItemSlot> Carried(IPlayer player)
    {
        foreach (string name in CarriedInventories)
        {
            IInventory inv = player?.InventoryManager?.GetOwnInventory(name);
            if (inv == null) continue;
            foreach (ItemSlot slot in inv) if (slot?.Itemstack != null) yield return slot;
        }
    }

    /// <summary>Whether a player has anything cute on them.</summary>
    public static bool CarriesCute(IPlayer player) => Carried(player).Any(s => IsCute(s.Itemstack));

    /// <summary>Whether a player holds something cute in their hand.</summary>
    public static bool HoldsCute(IPlayer player) => IsCute(player?.InventoryManager?.ActiveHotbarSlot?.Itemstack);

    private static readonly HashSet<string> FabricParts = new() { "wall", "floor", "ceiling", "slope", "lintel", "casing", "jamb", "window", "downlight", "fairylights", "nightlight" };

    /// <summary>
    /// Whether a block in Kitty's House is part of the house itself (never broken): its walls, floors, ceilings,
    /// windows, lights and door frames, and the solid nothing round it. Its furniture breaks (and breaking it offends
    /// Kitty); so does anything a wanderer set down there themselves.
    /// </summary>
    public static bool IsHouseFabric(Block block)
    {
        if (block?.Code == null || block.Code.Domain != "backrooms") return false;
        string path = block.Code.Path;
        if (path.StartsWith("l974-")) return FabricParts.Contains(path.Split('-')[1]);
        if (path.StartsWith("rubblemasonry")) return false;
        return Salvage.Breakdown.KindOf(block) != Salvage.BreakKind.None;
    }
}

/// <summary>
/// Level 974, Kitty's House: the rules (docs/design/new-levels/974-plan.md, sections 2.3, 3 and 4).
/// <list type="bullet">
/// <item><b>Taken.</b> Cross any threshold with something cute on you and, now and then, Kitty takes you to your own
/// house instead (<see cref="Detour"/>); the Hub's pink door lands there too. Each wanderer is given one house for
/// good (saved with the world).</item>
/// <item><b>The house.</b> Food that comes back and slowly turns to sugar, running water, a bed, an old computer,
/// cute clothes. The pink is kind for a while, then it wears you down (<see cref="CalmHours"/>).</item>
/// <item><b>Kitty.</b> One to a house that anyone is in; it watches, never seen to walk; it sneaks up behind you;
/// it watches you sleep; called with something cute in hand it comes and holds out its arm.</item>
/// <item><b>The gift.</b> Give it the cute thing you brought and you fall asleep, and wake in the safe place fixed
/// for your house (<see cref="ThresholdNetwork.KittyWake"/>), watched over for a few minutes.</item>
/// <item><b>Offence.</b> Break its things or strike it: the lights go out, the food is gone, your mind takes a blow,
/// and Kitty will not come for a day.</item>
/// </list>
/// </summary>
public class L974System : ModSystem
{
    // Player attributes (watched, so the client's air and sound can read them)
    public const string VisitKey = "backrooms:l974Visit", ArrivedKey = "backrooms:l974Arrived", LeftKey = "backrooms:l974Left";
    private const string HouseXKey = "backrooms:l974HouseX", HouseZKey = "backrooms:l974HouseZ", StageKey = "backrooms:l974Stage",
        DresserKey = "backrooms:l974Dresser", InternetKey = "backrooms:l974Internet", DreamKey = "backrooms:l974Dream", DreamtKey = "backrooms:l974Dreamt";
    private const string SaveKey = "backrooms-l974-houses";

    /// <summary>How long the pink is kind; when the lullaby goes out of tune; when the food turns half, then all, to sugar.</summary>
    public const double CalmHours = 18, WarpHours = 36, HalfSugarHours = 24, AllSugarHours = 48;
    /// <summary>The detour's odds (something cute carried, or held), and how long after a visit before Kitty takes anyone again.</summary>
    public const double DetourCarried = 1 / 20.0, DetourHeld = 1 / 6.0, CooldownHours = 48;
    private const double OffenceHours = 24, OffenceBlow = 0.4, MealEveryHours = 24, ValveHours = 24;
    private const int StockMax = 6;
    private const double RefillHours = 2;
    private const long WatchMs = 180_000;

    private static readonly string[] RealFridge = { "game:cheese-cheddar-1slice", "game:vegetable-carrot", "game:redmeat-cooked", "backrooms:l974-strawberrymilk", "game:butter-salted" };
    private static readonly string[] RealPantry = { "game:bread-spelt-perfect", "game:fruit-redapple", "backrooms:l974-marshmallow", "backrooms:l974-strawberrymilk" };
    private static readonly string[] Sugar = { "backrooms:l974-marshmallow", "backrooms:l974-candy" };
    private static readonly string[] Meals = { "pancakes", "soup", "macaroni" };
    private static readonly string[] CuteClothes =
    {
        "game:clothes-upperbody-kirtlepink", "game:clothes-upperbody-chemiseshort", "game:clothes-lowerbody-skirt",
        "game:clothes-lowerbody-hosebluepink", "game:clothes-head-liripipepink", "game:clothes-head-wreathflower",
    };

    private static ICoreServerAPI sapi;
    private static readonly Dictionary<string, long> watchedUntilMs = new();

    private WorldLayout layout;
    private WorldGeometry geometry;
    private ThresholdSystem thresholds;

    // Saved: each wanderer's house, and each house's larder and mood
    private Dictionary<string, (int Mx, int Mz)> houses = new();
    private Dictionary<(int, int), HouseState> state = new();
    private bool dirty;

    private sealed class HouseState
    {
        public double Fridge = StockMax, Pantry = StockMax, RefilledAt = -1, OffendedUntil, LastMeal = -1000;
        public bool LightsOut;
    }

    // Not saved: Kitty in each house someone is in, the last detour (for who is taken along), clocks per player
    private readonly Dictionary<(int, int), KittyState> kitties = new();
    private (int X, int Z) lastDetourSource;
    private long lastDetourMs = -100_000;
    private Vec3d lastDetourFrom;
    private (int, int) lastDetourHouse;
    private readonly HashSet<string> detoured = new();
    private readonly Dictionary<string, double> nextSmell = new(), nextMemory = new();
    private readonly Dictionary<string, long> lastCallMs = new();
    private readonly HashSet<string> sleeping = new();

    // Reused by the Kitty tick (ten times a second): who is in which house
    private readonly Dictionary<(int, int), List<IServerPlayer>> occupied = new();
    private readonly List<(int, int)> emptied = new();
    private long[] tickListeners = Array.Empty<long>();
    private ICoreServerAPI serverApi;

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockClass("BackroomsL974Food", typeof(BlockL974Food));
        api.RegisterBlockClass("BackroomsL974Tap", typeof(BlockL974Tap));
        api.RegisterBlockClass("BackroomsL974Computer", typeof(BlockL974Computer));
        api.RegisterBlockClass("BackroomsL974Dresser", typeof(BlockL974Dresser));
        api.RegisterEntity("EntityKitty", typeof(EntityKitty));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = serverApi = api;
        // (Static, so it would outlive the last world loaded in this process, whose clock ran on further)
        watchedUntilMs.Clear();
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            thresholds = api.ModLoader.GetModSystem<ThresholdSystem>();
            Load(api.WorldManager.SaveGame.GetData(SaveKey));
            api.Event.GameWorldSave += OnGameWorldSave;
            tickListeners = new[]
            {
                api.Event.RegisterGameTickListener(OnPlayerTick, 1000),
                api.Event.RegisterGameTickListener(OnKittyTick, 100),
            };
            api.Event.DidBreakBlock += OnBrokeBlock;
            api.Event.PlayerDisconnect += OnPlayerDisconnect;
        });
    }

    public override void Dispose()
    {
        // (sapi is static, so in single player this system's client-side instance sees it too: only the server's own
        // instance lets go of it, and only while it is still the one that holds it)
        if (serverApi == null) return;
        foreach (long id in tickListeners) serverApi.Event.UnregisterGameTickListener(id);
        serverApi.Event.GameWorldSave -= OnGameWorldSave;
        serverApi.Event.DidBreakBlock -= OnBrokeBlock;
        serverApi.Event.PlayerDisconnect -= OnPlayerDisconnect;
        // (Static, for Watched: it must not outlive this world in a process that goes on to load another)
        if (sapi == serverApi) sapi = null;
        serverApi = null;
    }

    private void OnGameWorldSave()
    {
        if (!dirty) return;
        sapi.WorldManager.SaveGame.StoreData(SaveKey, Save());
        dirty = false;
    }

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        sleeping.Remove(player.PlayerUID);
        detoured.Remove(player.PlayerUID);
        nextSmell.Remove(player.PlayerUID);
        nextMemory.Remove(player.PlayerUID);
        lastCallMs.Remove(player.PlayerUID);
        watchedUntilMs.Remove(player.PlayerUID);
    }

    /// <summary>Whether a player is still watched over after waking from Kitty's House (nothing hostile comes).</summary>
    public static bool Watched(EntityPlayer player) =>
        sapi != null && player?.PlayerUID != null && watchedUntilMs.TryGetValue(player.PlayerUID, out long until) && sapi.World.ElapsedMilliseconds < until;

    private double Now => sapi.World.Calendar.TotalHours;

    private int LevelAt(double x, double z) => layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(x)), WorldLayout.MacroOf((int)Math.Floor(z)));

    private HouseState StateOf((int, int) house)
    {
        if (!state.TryGetValue(house, out HouseState s)) { state[house] = s = new HouseState { RefilledAt = Now }; dirty = true; }
        return s;
    }

    // ================= Houses =================

    /// <summary>A wanderer's house: given the first time they are taken, and theirs for good.</summary>
    public (int Mx, int Mz)? HouseOf(IServerPlayer player)
    {
        if (layout == null) return null;
        if (houses.TryGetValue(player.PlayerUID, out var house)) return house;
        var taken = new HashSet<(int, int)>(houses.Values);
        ulong h = Hashing.Mix(StableHash(player.PlayerUID) * 0x9E3779B97F4A7C15UL ^ (ulong)sapi.World.Seed);
        for (int attempt = 0; attempt < 400; attempt++, h = Hashing.Mix(h + 1))
        {
            if (layout.L974HouseCellFor(h) is not { } cell || taken.Contains(cell)) continue;
            houses[player.PlayerUID] = cell;
            dirty = true;
            return cell;
        }
        return null;
    }

    /// <summary>
    /// FNV-1a over a player's uid: the same in every run of the server (string.GetHashCode is randomised per process, so a
    /// house given but not yet saved when the server stopped would have been a different one next time).
    /// </summary>
    private static ulong StableHash(string text)
    {
        ulong h = 14695981039346656037UL;
        foreach (char c in text) { h ^= c; h *= 1099511628211UL; }
        return h;
    }

    private Link ArrivalLink((int Mx, int Mz) house)
    {
        var (x, z) = layout.L974Arrival(house.Mx, house.Mz);
        return new Link(x + 0.5, geometry.FloorFor(WorldLayout.Level974) + 1.05, z + 0.5, false);
    }

    private static (int, int) CellOf(double x, double z) => (WorldLayout.MacroOf((int)Math.Floor(x)), WorldLayout.MacroOf((int)Math.Floor(z)));

    // ================= Taken =================

    /// <summary>
    /// Just before someone going through a threshold arrives: whether Kitty takes them to their house instead. Anyone
    /// arriving in the level at all (the Hub's pink door) is put in their own house.
    /// </summary>
    public Link? Detour(IServerPlayer player, Passage passage, Link destination)
    {
        if (layout == null || player.Entity == null) return null;
        if (LevelAt(destination.X, destination.Z) == WorldLayout.Level974)
        {
            if (HouseOf(player) is not { } own) return null;
            Link home = ArrivalLink(own);
            return Math.Abs(home.X - destination.X) < 1 && Math.Abs(home.Z - destination.Z) < 1 ? null : home;
        }
        // Not when stepping back the way you came, carried out by the King, or waking from Kitty's House
        if (passage.Find == null || passage.Message is "backrooms:trial-carried" or ThresholdNetwork.L974WakeMessage) return null;
        if (!L974.CarriesCute(player)) return null;
        long nowMs = sapi.World.ElapsedMilliseconds;

        // Whoever goes through with the one Kitty took, carrying something cute too, goes along with them
        if (nowMs - lastDetourMs < 5000 && passage.Source == lastDetourSource && lastDetourFrom != null
            && player.Entity.Pos.XYZ.SquareDistanceTo(lastDetourFrom) <= 4 * 4)
        {
            detoured.Add(player.PlayerUID);
            return ArrivalLink(lastDetourHouse);
        }

        double left = player.Entity.WatchedAttributes.GetDouble(LeftKey, -1000);
        if (Now - left < CooldownHours) return null;
        double odds = L974.HoldsCute(player) ? DetourHeld : DetourCarried;
        if (sapi.World.Rand.NextDouble() >= odds) return null;
        if (HouseOf(player) is not { } house) return null;
        lastDetourMs = nowMs;
        lastDetourSource = passage.Source;
        lastDetourFrom = player.Entity.Pos.XYZ;
        lastDetourHouse = house;
        detoured.Add(player.PlayerUID);
        return ArrivalLink(house);
    }

    /// <summary>Someone is about to arrive in the level (by detour, the Hub's door, or the goto command): the visit begins.</summary>
    public void Arriving(IServerPlayer player, Link link)
    {
        if (layout == null || player.Entity == null) return;
        var house = CellOf(link.X, link.Z);
        EntityPlayer entity = player.Entity;
        int visit = entity.WatchedAttributes.GetInt(VisitKey);
        bool sameHouse = visit != 0 && entity.WatchedAttributes.GetInt(HouseXKey) == house.Item1 && entity.WatchedAttributes.GetInt(HouseZKey) == house.Item2;
        if (!sameHouse) BeginVisit(player, house);
        if (detoured.Remove(player.PlayerUID))
            player.SendMessage(GlobalConstants.GeneralChatGroup, Backrooms.Say.T(player, "backrooms:l974-detour"), EnumChatType.Notification);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Backrooms.Say.T(player, "backrooms:l974-arrive"), EnumChatType.Notification);
    }

    private void BeginVisit(IServerPlayer player, (int, int) house)
    {
        EntityPlayer entity = player.Entity;
        int visit = 1 + sapi.World.Rand.Next(int.MaxValue - 1);
        entity.WatchedAttributes.SetInt(VisitKey, visit);
        entity.WatchedAttributes.SetDouble(ArrivedKey, Now);
        entity.WatchedAttributes.SetInt(HouseXKey, house.Item1);
        entity.WatchedAttributes.SetInt(HouseZKey, house.Item2);
        entity.WatchedAttributes.SetInt(StageKey, 0);
        // What they brought that is cute: one of these is Kitty's gift
        foreach (ItemSlot slot in L974.Carried(player))
        {
            if (!L974.IsCute(slot.Itemstack) || slot.Itemstack.Attributes.HasAttribute(L974.KittysKey)) continue;
            slot.Itemstack.Attributes.SetInt(L974.BroughtKey, visit);
            slot.MarkDirty();
        }
        nextSmell[player.PlayerUID] = Now + 1 + sapi.World.Rand.NextDouble() * 3;
        nextMemory[player.PlayerUID] = Now + 0.5 + sapi.World.Rand.NextDouble() * 2;
        HouseState s = StateOf(house);
        if (s.RefilledAt < 0) s.RefilledAt = Now;
    }

    private void EndVisit(EntityPlayer entity)
    {
        entity.WatchedAttributes.SetInt(VisitKey, 0);
        entity.WatchedAttributes.SetDouble(LeftKey, Now);
        if (entity.GetBehavior<EntityBehaviorTemporalStabilityAffected>() is { } tsa) tsa.stabilityOffset = 0;
    }

    // ================= Every second, for everyone =================

    private void OnPlayerTick(float dt)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { Alive: true } entity } player) continue;
            bool here = LevelAt(entity.Pos.X, entity.Pos.Z) == WorldLayout.Level974;
            int visit = entity.WatchedAttributes.GetInt(VisitKey);
            if (!here)
            {
                if (visit != 0) EndVisit(entity);
                sleeping.Remove(player.PlayerUID);
                continue;
            }
            var house = CellOf(entity.Pos.X, entity.Pos.Z);
            if (visit == 0 || entity.WatchedAttributes.GetInt(HouseXKey) != house.Item1 || entity.WatchedAttributes.GetInt(HouseZKey) != house.Item2)
            {
                BeginVisit(player, house);
                visit = entity.WatchedAttributes.GetInt(VisitKey);
            }
            HouseState s = StateOf(house);
            double hours = Now - entity.WatchedAttributes.GetDouble(ArrivedKey, Now);
            bool offended = s.OffendedUntil > Now;

            // The pink: kind at first (the level's own 1.3), then less and less so the longer you stay
            double effective = offended ? 0.4 : hours < CalmHours ? 1.3 : hours < WarpHours ? 0.9 : hours < 60 ? 0.6 : 0.3;
            if (entity.GetBehavior<EntityBehaviorTemporalStabilityAffected>() is { } tsa) tsa.stabilityOffset = effective - 1.3;
            int stage = hours < CalmHours ? 0 : hours < WarpHours ? 1 : hours < 60 ? 2 : 3;
            int sugarStage = hours >= AllSugarHours ? 1 : 0;
            int was = entity.WatchedAttributes.GetInt(StageKey);
            int now = stage | (sugarStage << 4);
            if (now != was)
            {
                entity.WatchedAttributes.SetInt(StageKey, now);
                if ((was & 15) != stage && stage > 0) Say(player, "backrooms:l974-pink-" + stage);
                if ((was >> 4) != sugarStage && sugarStage > 0) Say(player, "backrooms:l974-sugar");
            }

            // Memories, soft at the edges; and near the kitchen, a meal you remember. (The clocks are not saved: a visit
            // carried on after a restart starts them again here.)
            if (!nextMemory.ContainsKey(player.PlayerUID)) nextMemory[player.PlayerUID] = Now + 0.5 + sapi.World.Rand.NextDouble() * 2;
            if (!nextSmell.ContainsKey(player.PlayerUID)) nextSmell[player.PlayerUID] = Now + 1 + sapi.World.Rand.NextDouble() * 3;
            if (Now >= nextMemory[player.PlayerUID])
            {
                nextMemory[player.PlayerUID] = Now + 3 + sapi.World.Rand.NextDouble() * 4;
                Say(player, "backrooms:l974-memory-" + (1 + sapi.World.Rand.Next(4)));
            }
            var spots = SpotsOf(house);
            var kitchen = spots.First(p => p.Kind == WorldLayout.L974SpotKind.Kitchen);
            double toKitchen = Math.Sqrt(Sq(entity.Pos.X - kitchen.X - 0.5) + Sq(entity.Pos.Z - kitchen.Z - 0.5));
            if (toKitchen <= 8 && Now >= nextSmell[player.PlayerUID])
            {
                nextSmell[player.PlayerUID] = Now + 2.5 + sapi.World.Rand.NextDouble() * 1.5;
                int smell = sapi.World.Rand.Next(5);
                Say(player, "backrooms:l974-smell-" + (smell + 1));
                // Mostly the smell is all there is; now and then the meal is really on the table
                if (smell < 3 && !offended && Now - s.LastMeal >= MealEveryHours && sapi.World.Rand.NextDouble() < 0.2 * ScarcitySystem.FoodScale(sapi.World)
                    && sapi.World.GetItem(new AssetLocation("backrooms:l974-meal-" + Meals[smell])) is { } meal)
                {
                    s.LastMeal = Now;
                    dirty = true;
                    var table = spots.First(p => p.Kind == WorldLayout.L974SpotKind.Table);
                    sapi.World.SpawnItemEntity(new ItemStack(meal), new Vec3d(table.X + 0.5, geometry.FloorFor(WorldLayout.Level974) + 2.1, table.Z + 0.5), new Vec3d());
                    Say(player, "backrooms:l974-meal");
                }
            }

            // DreamSleep: after the computer's dream is ready, a sleep in the bed steadies you (once a visit)
            bool asleep = entity.MountedOn is BlockEntityBed;
            if (asleep && entity.WatchedAttributes.GetInt(DreamKey) == visit && entity.WatchedAttributes.GetInt(DreamtKey) != visit)
            {
                entity.WatchedAttributes.SetInt(DreamtKey, visit);
                entity.WatchedAttributes.SetDouble("temporalStability", Math.Min(1, entity.WatchedAttributes.GetDouble("temporalStability", 1) + 0.3));
                Say(player, "backrooms:l974-dream");
            }
            if (asleep) sleeping.Add(player.PlayerUID); else sleeping.Remove(player.PlayerUID);

            // Forgiven, after a day
            if (!offended && s.LightsOut)
            {
                s.LightsOut = false;
                dirty = true;
                SwapLights(house, on: true);
                foreach (IServerPlayer guest in GuestsOf(house)) Say(guest, "backrooms:l974-forgiven");
            }
        }
    }

    private static double Sq(double v) => v * v;

    private readonly Dictionary<(int, int), List<(int X, int Z, WorldLayout.L974SpotKind Kind)>> spotsOfHouse = new();

    /// <summary>A house's spots (the layout's, which are a pure function of the house and asked for by every player each second and by Kitty ten times a second, so kept).</summary>
    private List<(int X, int Z, WorldLayout.L974SpotKind Kind)> SpotsOf((int, int) house)
    {
        if (!spotsOfHouse.TryGetValue(house, out var spots)) spotsOfHouse[house] = spots = layout.L974Spots(house.Item1, house.Item2);
        return spots;
    }

    private static void Say(IServerPlayer player, string key, params object[] args) =>
        player.SendMessage(GlobalConstants.GeneralChatGroup, Backrooms.Say.T(player, key, args), EnumChatType.Notification);

    private IEnumerable<IServerPlayer> GuestsOf((int, int) house)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
            if (online is IServerPlayer { Entity: { Alive: true } e } p && LevelAt(e.Pos.X, e.Pos.Z) == WorldLayout.Level974 && CellOf(e.Pos.X, e.Pos.Z) == house)
                yield return p;
    }

    // ================= Kitty =================

    private enum KittyMode { Hidden, Watching, Coming, Asking, Gliding }

    private sealed class KittyState
    {
        public long EntityId = -1;
        public KittyMode Mode = KittyMode.Hidden;
        public long NextMs, SeenMs, LeaveAfterMs, NextSneakMs, ModeUntilMs;
        public bool Relocate;
        public string For;
        public Vec3d GlideTo;
        public string Anim;
    }

    private void OnKittyTick(float dt)
    {
        if (layout == null) return;
        long nowMs = sapi.World.ElapsedMilliseconds;
        if (occupied.Count > 0) occupied.Clear();
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { Alive: true } e } p || LevelAt(e.Pos.X, e.Pos.Z) != WorldLayout.Level974) continue;
            var house = CellOf(e.Pos.X, e.Pos.Z);
            if (!occupied.TryGetValue(house, out var list)) occupied[house] = list = new List<IServerPlayer>();
            list.Add(p);
            // "Here Kitty, Kitty, Kitty!": sneak and use, with something cute in hand
            if (e.Controls.Sneak && e.Controls.RightMouseDown && L974.HoldsCute(p) && nowMs - lastCallMs.GetValueOrDefault(p.PlayerUID, -10_000) > 4000)
            {
                lastCallMs[p.PlayerUID] = nowMs;
                Call(p, house);
            }
        }
        if (kitties.Count > 0)
        {
            emptied.Clear();
            foreach (var house in kitties.Keys) if (!occupied.ContainsKey(house)) emptied.Add(house);
            foreach (var house in emptied) { Vanish(kitties[house], quiet: true); kitties.Remove(house); }
        }
        foreach (var (house, guests) in occupied)
        {
            if (!kitties.TryGetValue(house, out KittyState k))
            {
                kitties[house] = k = new KittyState { NextMs = nowMs + 30_000 + sapi.World.Rand.Next(60_000), NextSneakMs = nowMs + 240_000 + sapi.World.Rand.Next(240_000) };
            }
            ThinkKitty(house, k, guests, nowMs);
        }
    }

    private Entity KittyEntity(KittyState k) => k.EntityId < 0 ? null : sapi.World.GetEntityById(k.EntityId);

    private double FloorY => geometry.FloorFor(WorldLayout.Level974) + 1;

    /// <summary>Whether a player can see a point: in front of them, not too far, nothing in the way.</summary>
    private bool Sees(EntityPlayer player, Vec3d point, double range = 32) =>
        player.Pos.XYZ.SquareDistanceTo(point) <= range * range && Senses.AngleTo(player, point) <= 60
        && Senses.ClearLine(sapi.World, Senses.Eyes(player), point);

    private bool SeenByAny(List<IServerPlayer> guests, Vec3d point)
    {
        foreach (IServerPlayer g in guests) if (Sees(g.Entity, point)) return true;
        return false;
    }

    // (Loops rather than LINQ: these run ten times a second for each house someone is in)
    private static IServerPlayer GuestByUid(List<IServerPlayer> guests, string uid)
    {
        foreach (IServerPlayer g in guests) if (g.PlayerUID == uid) return g;
        return null;
    }

    private static IServerPlayer NearestGuest(List<IServerPlayer> guests, Vec3d to)
    {
        IServerPlayer best = null;
        double bestSq = double.MaxValue;
        foreach (IServerPlayer g in guests)
        {
            double sq = g.Entity.Pos.SquareDistanceTo(to);
            if (sq < bestSq) { bestSq = sq; best = g; }
        }
        return best;
    }

    private void ThinkKitty((int, int) house, KittyState k, List<IServerPlayer> guests, long nowMs)
    {
        HouseState s = StateOf(house);
        Entity kitty = KittyEntity(k);
        if (kitty == null && k.Mode != KittyMode.Hidden) { k.Mode = KittyMode.Hidden; k.EntityId = -1; k.NextMs = nowMs + 20_000; }
        if (s.OffendedUntil > Now)
        {
            // Offended: gone, but now and then glimpsed far off in the dark, to see you out
            if (kitty != null && k.Mode == KittyMode.Watching && nowMs > k.ModeUntilMs) { Vanish(k); k.NextMs = nowMs + 90_000 + sapi.World.Rand.Next(120_000); }
            else if (kitty == null && nowMs >= k.NextMs)
            {
                IServerPlayer target = guests[sapi.World.Rand.Next(guests.Count)];
                var far = SpotsOf(house).Where(p => p.Kind == WorldLayout.L974SpotKind.Watch)
                    .OrderByDescending(p => Sq(p.X - target.Entity.Pos.X) + Sq(p.Z - target.Entity.Pos.Z)).First();
                if (Appear(k, new Vec3d(far.X + 0.5, FloorY, far.Z + 0.5), target.Entity, "idle")) { k.Mode = KittyMode.Watching; k.ModeUntilMs = nowMs + 2500; }
                else k.NextMs = nowMs + 10_000;
            }
            return;
        }

        IServerPlayer asleep = null;
        foreach (IServerPlayer g in guests) if (sleeping.Contains(g.PlayerUID)) { asleep = g; break; }
        switch (k.Mode)
        {
            case KittyMode.Hidden:
            {
                if (asleep != null && nowMs >= k.NextMs)
                {
                    // Watching you sleep
                    var bed = SpotsOf(house).First(p => p.Kind == WorldLayout.L974SpotKind.SleepWatch);
                    if (Appear(k, new Vec3d(bed.X + 0.5, FloorY, bed.Z + 0.5), asleep.Entity, "sleepwatch")) { k.Mode = KittyMode.Watching; k.SeenMs = 0; k.LeaveAfterMs = 4000; }
                    return;
                }
                if (nowMs >= k.NextSneakMs && TrySneakUp(k, guests, nowMs)) return;
                if (nowMs < k.NextMs) return;
                IServerPlayer target = guests[sapi.World.Rand.Next(guests.Count)];
                if (TryWatch(house, k, guests, target)) { k.SeenMs = 0; k.Relocate = false; k.LeaveAfterMs = 2000 + sapi.World.Rand.Next(4000); }
                else k.NextMs = nowMs + 3000;
                return;
            }
            case KittyMode.Watching:
            {
                Vec3d at = kitty.Pos.XYZ.Add(0, 1.6, 0);
                bool seen = SeenByAny(guests, at);
                if (seen) k.SeenMs += 100;
                Vec3d kittyAt = kitty.Pos.XYZ;
                IServerPlayer near = NearestGuest(guests, kittyAt);
                double dist = near.Entity.Pos.DistanceTo(kittyAt);
                // (Close by only counts once it has been seen: it is put down close behind someone, or by their bed, on purpose)
                if (k.SeenMs >= k.LeaveAfterMs || dist < 3 && k.SeenMs > 0) k.Relocate = true;
                // Walked straight at: it glides back out of the way, the one time it is seen to move
                if (dist < 2 && k.SeenMs > 0 && near.Entity.Controls.TriesToMove)
                {
                    Vec3d away = kitty.Pos.XYZ.SubCopy(near.Entity.Pos.XYZ);
                    away.Y = 0;
                    if (away.Length() > 0.01) away.Normalize();
                    Vec3d to = kitty.Pos.XYZ.AddCopy(away.X * 3, 0, away.Z * 3);
                    if (Walkable(to)) { k.Mode = KittyMode.Gliding; k.GlideTo = to; Animate(kitty, k, "glide"); return; }
                }
                if (k.Relocate && !seen)
                {
                    Vanish(k);
                    k.NextMs = nowMs + 20_000 + sapi.World.Rand.Next(100_000);
                }
                else Face(kitty, near.Entity.Pos.XYZ);
                return;
            }
            case KittyMode.Gliding:
            {
                if (Glide(kitty, k.GlideTo, 0.6)) { k.Mode = KittyMode.Watching; k.Relocate = true; Animate(kitty, k, "idle"); }
                return;
            }
            case KittyMode.Coming:
            {
                IServerPlayer caller = GuestByUid(guests, k.For);
                if (caller == null || nowMs > k.ModeUntilMs) { Vanish(k); k.NextMs = nowMs + 30_000; return; }
                Vec3d target = caller.Entity.Pos.XYZ;
                Vec3d from = kitty.Pos.XYZ;
                Vec3d dir = target.SubCopy(from);
                dir.Y = 0;
                double d = dir.Length();
                if (d <= 1.6)
                {
                    k.Mode = KittyMode.Asking;
                    k.ModeUntilMs = nowMs + 30_000;
                    Animate(kitty, k, "ask");
                    Face(kitty, target);
                    Say(caller, "backrooms:l974-ask");
                    return;
                }
                dir.Normalize();
                Vec3d step = from.AddCopy(dir.X * Math.Min(0.6, d - 1.5), 0, dir.Z * Math.Min(0.6, d - 1.5));
                if (!Walkable(step)) step = from.AddCopy(dir.X * 0.3, 0, dir.Z * 0.3);
                Glide(kitty, step, 0.6);
                Face(kitty, target);
                return;
            }
            case KittyMode.Asking:
            {
                IServerPlayer caller = GuestByUid(guests, k.For);
                if (caller == null || nowMs > k.ModeUntilMs) { Vanish(k); k.NextMs = nowMs + 20_000; return; }
                Face(kitty, caller.Entity.Pos.XYZ);
                return;
            }
        }
    }

    /// <summary>Puts Kitty down at a watch spot out of the target's sight, 4 to 10 blocks off (or anywhere out of sight).</summary>
    private bool TryWatch((int, int) house, KittyState k, List<IServerPlayer> guests, IServerPlayer target)
    {
        var spots = SpotsOf(house);
        var options = new List<Vec3d>();
        var fallback = new List<Vec3d>();
        foreach (var (x, z, kind) in spots)
        {
            if (kind is not (WorldLayout.L974SpotKind.Watch or WorldLayout.L974SpotKind.Kneel)) continue;
            var at = new Vec3d(x + 0.5, FloorY, z + 0.5);
            if (SeenByAny(guests, at.AddCopy(0, 1.6, 0)) || guests.Any(g => g.Entity.Pos.XYZ.SquareDistanceTo(at) < 9)) continue;
            double d = target.Entity.Pos.XYZ.DistanceTo(at);
            (d >= 4 && d <= 10 ? options : fallback).Add(at);
        }
        var pick = options.Count > 0 ? options : fallback;
        if (pick.Count == 0) return false;
        Vec3d spot = pick[sapi.World.Rand.Next(pick.Count)];
        // By the cat bed it kneels; in a doorway it stoops (its head would touch the lintel)
        var tile = layout.TileAt((int)Math.Floor(spot.X), (int)Math.Floor(spot.Z));
        bool catBed = spots.Any(p => p.Kind == WorldLayout.L974SpotKind.Kneel && p.X == (int)Math.Floor(spot.X) && p.Z == (int)Math.Floor(spot.Z));
        string anim = catBed ? "kneel" : tile.Kind == TileKind.Doorway ? (sapi.World.Rand.NextDouble() < 0.5 ? "peek" : "stoop")
            : sapi.World.Rand.NextDouble() < 0.3 ? "headtilt" : "idle";
        if (!Appear(k, spot, target.Entity, anim)) return false;
        k.Mode = KittyMode.Watching;
        return true;
    }

    /// <summary>Every few minutes, Kitty is suddenly right behind someone.</summary>
    private bool TrySneakUp(KittyState k, List<IServerPlayer> guests, long nowMs)
    {
        k.NextSneakMs = nowMs + 240_000 + sapi.World.Rand.Next(240_000);
        IServerPlayer target = guests[sapi.World.Rand.Next(guests.Count)];
        EntityPlayer e = target.Entity;
        double yaw = e.Pos.Yaw;
        // (A player looks along (-sin yaw, cos yaw)... behind them is the other way)
        Vec3d look = new Vec3d(-Math.Sin(yaw), 0, -Math.Cos(yaw));
        Vec3d behind = e.Pos.XYZ.AddCopy(-look.X * 1.75, 0, -look.Z * 1.75);
        behind.Y = FloorY;
        if (!Walkable(behind) || SeenByAny(guests, behind.AddCopy(0, 1.6, 0))) return false;
        if (!Appear(k, behind, e, "idle")) return false;
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/creature/974/rustle*"), behind.X, behind.Y + 1, behind.Z, null, true, 8, 0.3f);
        k.Mode = KittyMode.Watching;
        k.SeenMs = 0;
        k.LeaveAfterMs = 2000;
        k.Relocate = false;
        return true;
    }

    /// <summary>Whether Kitty can stand at a point: floor, walked over, in the level.</summary>
    private bool Walkable(Vec3d at)
    {
        int x = (int)Math.Floor(at.X), z = (int)Math.Floor(at.Z);
        Tile t = layout.TileAt(x, z);
        return t.Level == WorldLayout.Level974 && (t.Kind == TileKind.Doorway || t.Kind == TileKind.Floor && (t.Variant == 0 || t.Variant == Worldgen.Props.L974Rug) && t.Depth >> 2 != WorldLayout.L974HighSlope);
    }

    private bool Appear(KittyState k, Vec3d at, Entity facing, string anim)
    {
        Entity kitty = KittyEntity(k);
        if (kitty == null)
        {
            EntityProperties type = sapi.World.GetEntityType(new AssetLocation("backrooms:l974-kitty"));
            if (type == null) return false;
            kitty = sapi.World.ClassRegistry.CreateEntity(type);
            kitty.Pos.SetPos(at.X, at.Y, at.Z);
            kitty.AlwaysActive = true;
            sapi.World.SpawnEntity(kitty);
            k.EntityId = kitty.EntityId;
            k.Anim = null;
        }
        else kitty.TeleportToDouble(at.X, at.Y, at.Z);
        Face(kitty, facing.Pos.XYZ);
        Animate(kitty, k, anim);
        return true;
    }

    private void Vanish(KittyState k, bool quiet = false)
    {
        Entity kitty = KittyEntity(k);
        if (kitty != null)
        {
            if (!quiet) sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/creature/974/rustle*"), kitty.Pos.X, kitty.Pos.Y + 1, kitty.Pos.Z, null, true, 10, 0.4f);
            kitty.Die(EnumDespawnReason.Removed);
        }
        k.EntityId = -1;
        k.Mode = KittyMode.Hidden;
        k.For = null;
    }

    private static void Animate(Entity kitty, KittyState k, string anim)
    {
        if (k.Anim == anim) return;
        if (k.Anim != null) kitty.AnimManager?.StopAnimation(k.Anim);
        k.Anim = anim;
        if (anim != "idle") kitty.AnimManager?.StartAnimation(anim);
    }

    private static void Face(Entity kitty, Vec3d target)
    {
        float yaw = (float)Math.Atan2(target.X - kitty.Pos.X, target.Z - kitty.Pos.Z);
        kitty.Pos.Yaw = yaw;
    }

    /// <summary>Slides Kitty toward a point, smoothly and swiftly; true once it is there.</summary>
    private static bool Glide(Entity kitty, Vec3d to, double step)
    {
        Vec3d from = kitty.Pos.XYZ;
        double dx = to.X - from.X, dz = to.Z - from.Z, d = Math.Sqrt(dx * dx + dz * dz);
        if (d <= step) { kitty.Pos.SetPos(to.X, from.Y, to.Z); return true; }
        kitty.Pos.SetPos(from.X + dx / d * step, from.Y, from.Z + dz / d * step);
        return false;
    }

    // ================= The call and the gift =================

    private void Call(IServerPlayer player, (int, int) house)
    {
        foreach (IServerPlayer guest in GuestsOf(house))
            guest.SendMessage(GlobalConstants.GeneralChatGroup, player.PlayerName + ": " + Backrooms.Say.T(guest, "backrooms:l974-call"), EnumChatType.OthersMessage);
        if (StateOf(house).OffendedUntil > Now) { Say(player, "backrooms:l974-gift-refused"); return; }
        if (!kitties.TryGetValue(house, out KittyState k)) return;
        if (k.Mode is KittyMode.Coming or KittyMode.Asking && k.For == player.PlayerUID) return;
        long nowMs = sapi.World.ElapsedMilliseconds;
        // It comes, from the nearest of its places that the caller cannot see, in a few seconds
        sapi.Event.RegisterCallback(_ =>
        {
            if (player.Entity == null || !kitties.TryGetValue(house, out KittyState kk)) return;
            var guests = GuestsOf(house).ToList();
            var spot = SpotsOf(house).Where(p => p.Kind == WorldLayout.L974SpotKind.Watch)
                .Select(p => new Vec3d(p.X + 0.5, FloorY, p.Z + 0.5))
                .OrderBy(p => (SeenByAny(guests, p.AddCopy(0, 1.6, 0)) ? 1000 : 0) + p.DistanceTo(player.Entity.Pos.XYZ)).FirstOrDefault();
            if (spot == null) return;
            if (KittyEntity(kk) == null && !Appear(kk, spot, player.Entity, "glide")) return;
            Animate(KittyEntity(kk), kk, "glide");
            kk.Mode = KittyMode.Coming;
            kk.For = player.PlayerUID;
            kk.ModeUntilMs = sapi.World.ElapsedMilliseconds + 20_000;
        }, 2000 + sapi.World.Rand.Next(4000));
    }

    /// <summary>Someone right-clicks Kitty: with something cute in hand, it is a call, or (while it holds out its arm) the gift.</summary>
    public void OnKittyInteract(EntityKitty kitty, IServerPlayer player, ItemSlot slot)
    {
        if (layout == null || player.Entity == null) return;
        var house = CellOf(kitty.Pos.X, kitty.Pos.Z);
        if (!kitties.TryGetValue(house, out KittyState k) || k.EntityId != kitty.EntityId) return;
        if (k.Mode != KittyMode.Asking || k.For != player.PlayerUID)
        {
            if (L974.IsCute(slot?.Itemstack)) Call(player, house);
            return;
        }
        Give(player, house, k, slot);
    }

    private void Give(IServerPlayer player, (int, int) house, KittyState k, ItemSlot slot)
    {
        EntityPlayer entity = player.Entity;
        int visit = entity.WatchedAttributes.GetInt(VisitKey);
        ItemStack stack = slot?.Itemstack;
        bool brought = L974.IsCute(stack) && stack.Attributes.GetInt(L974.BroughtKey) == visit && visit != 0;
        // The safety valve: a day without what you brought, and Kitty will take anything cute, but sends you home
        bool lost = !L974.Carried(player).Any(s => L974.IsCute(s.Itemstack) && s.Itemstack.Attributes.GetInt(L974.BroughtKey) == visit);
        bool valve = !brought && lost && L974.IsCute(stack) && Now - entity.WatchedAttributes.GetDouble(ArrivedKey, Now) >= ValveHours;
        Entity kitty = KittyEntity(k);
        if (!brought && !valve)
        {
            Say(player, L974.IsCute(stack) ? "backrooms:l974-gift-wrong" : "backrooms:l974-gift-none");
            Vanish(k);
            k.NextMs = sapi.World.ElapsedMilliseconds + 20_000;
            return;
        }
        string name = stack.GetName();
        slot.TakeOut(1);
        slot.MarkDirty();
        if (kitty != null)
        {
            Animate(kitty, k, "take");
            sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/creature/974/purr"), kitty.Pos.X, kitty.Pos.Y + 2, kitty.Pos.Z, null, false, 12, 0.8f);
        }
        k.Mode = KittyMode.Watching;
        k.Relocate = true;
        k.LeaveAfterMs = 0;
        Say(player, "backrooms:l974-gift-taken", name);
        // Overwhelmingly sleepy: slow, then asleep, then elsewhere
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/974/drowsy"), entity, null, false, 8, 0.8f);
        entity.Stats.Set("walkspeed", "backrooms-l974-drowsy", -0.7f, false);
        sapi.Event.RegisterCallback(_ =>
        {
            entity.Stats.Remove("walkspeed", "backrooms-l974-drowsy");
            // (Not if they died meanwhile, or logged out: their entity is gone, or a new one)
            if (sapi == null || !entity.Alive || player.Entity != entity || player.ConnectionState != EnumClientState.Playing) return;
            Wake(player, house, home: valve);
        }, 4000);
    }

    private void Wake(IServerPlayer player, (int Mx, int Mz) house, bool home)
    {
        EntityPlayer entity = player.Entity;
        bool woke;
        if (home)
        {
            FuzzyEntityPos spawn = player.GetSpawnPosition(false);
            woke = spawn != null;
            if (woke) entity.TeleportToDouble(spawn.X, spawn.Y, spawn.Z);
            if (woke) Say(player, "backrooms:l974-wake-home");
        }
        else woke = thresholds?.L974Wake(player, layout.L974At(house.Mx, house.Mz, 9, 8)) == true;
        if (!woke) return;
        watchedUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + WatchMs;
        entity.Attributes.SetDouble(MenaceSystem.RestedKey, Now);
        EndVisit(entity);
    }

    // ================= Offence =================

    private void OnBrokeBlock(IServerPlayer player, int oldBlockId, BlockSelection sel)
    {
        if (layout == null || sel?.Position == null || LevelAt(sel.Position.X, sel.Position.Z) != WorldLayout.Level974) return;
        Block old = sapi.World.GetBlock(oldBlockId);
        if (old?.Code == null || old.Code.Domain != "backrooms" || !old.Code.Path.StartsWith("l974-")) return;
        Offend(CellOf(sel.Position.X, sel.Position.Z), player);
    }

    /// <summary>Someone has struck Kitty.</summary>
    public void OnKittyHurt(EntityKitty kitty, DamageSource source)
    {
        if (layout == null) return;
        Entity by = source?.GetCauseEntity() ?? source?.SourceEntity;
        if (by is not EntityPlayer { Player: IServerPlayer player }) return;
        Offend(CellOf(kitty.Pos.X, kitty.Pos.Z), player);
    }

    private void Offend((int, int) house, IServerPlayer by)
    {
        HouseState s = StateOf(house);
        bool already = s.OffendedUntil > Now;
        s.OffendedUntil = Now + OffenceHours;
        s.Fridge = s.Pantry = 0;
        s.RefilledAt = Now;
        dirty = true;
        if (kitties.TryGetValue(house, out KittyState k))
        {
            Entity kitty = KittyEntity(k);
            if (kitty != null) sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/creature/974/exhale"), kitty.Pos.X, kitty.Pos.Y + 2, kitty.Pos.Z, null, false, 24, 1f);
            Vanish(k, quiet: true);
            k.NextMs = sapi.World.ElapsedMilliseconds + 60_000;
        }
        double stability = by.Entity.WatchedAttributes.GetDouble("temporalStability", 1);
        by.Entity.WatchedAttributes.SetDouble("temporalStability", Math.Max(0, stability - OffenceBlow));
        if (already) return;
        s.LightsOut = true;
        SwapLights(house, on: false);
        var (x0, z0) = WorldLayout.L974HouseCorner(house.Item1, house.Item2);
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/974/lightsout"), x0 + 9.5, FloorY + 3, z0 + 8.5, null, false, 32, 1f);
        foreach (IServerPlayer guest in GuestsOf(house)) Say(guest, "backrooms:l974-offended");
    }

    /// <summary>Puts the house's lights out (or on again): its ceiling lights and the fairy lights.</summary>
    private void SwapLights((int, int) house, bool on)
    {
        var (x0, z0) = WorldLayout.L974HouseCorner(house.Item1, house.Item2);
        int floor = geometry.FloorFor(WorldLayout.Level974);
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        var pos = new BlockPos(0, 0, 0);
        string from = on ? "-off" : "-on", to = on ? "-on" : "-off";
        for (int x = x0; x < x0 + layout.L974Width; x++)
            for (int z = z0; z < z0 + WorldLayout.L974HouseDeep; z++)
                for (int y = floor + 4; y <= floor + 5; y++)
                {
                    pos.Set(x, y, z);
                    Block b = blocks.GetBlock(pos);
                    if (b?.Code == null || b.Code.Domain != "backrooms") continue;
                    string path = b.Code.Path;
                    if (!(path.StartsWith("l974-downlight") || path.StartsWith("l974-fairylights")) || !path.Contains(from)) continue;
                    Block swapped = sapi.World.GetBlock(new AssetLocation("backrooms", path.Replace(from, to)));
                    if (swapped != null && swapped.BlockId != 0) blocks.SetBlock(swapped.BlockId, pos);
                }
    }

    // ================= The house's things =================

    /// <summary>The fridge or the pantry gives one thing: real food at first, then less and less but sugar.</summary>
    public void Dispense(IServerPlayer player, BlockPos pos, string kind)
    {
        if (layout == null || player.Entity == null) return;
        var house = CellOf(pos.X, pos.Z);
        HouseState s = StateOf(house);
        if (s.RefilledAt < 0) s.RefilledAt = Now;
        // The world's Backrooms scarcity sets how much each holds and how soon it refills (Scarce: two, every six hours)
        float food = ScarcitySystem.FoodScale(sapi.World);
        int max = Math.Max(1, (int)Math.Round(StockMax * food));
        double every = RefillHours / food;
        int refills = (int)Math.Floor((Now - s.RefilledAt) / every);
        if (refills > 0 && s.OffendedUntil <= Now)
        {
            s.Fridge = Math.Min(max, s.Fridge + refills);
            s.Pantry = Math.Min(max, s.Pantry + refills);
            s.RefilledAt += refills * every;
        }
        s.Fridge = Math.Min(max, s.Fridge);
        s.Pantry = Math.Min(max, s.Pantry);
        bool fridge = kind != "pantry";
        double stock = fridge ? s.Fridge : s.Pantry;
        if (stock < 1)
        {
            player.SendIngameError("dispenserempty", Backrooms.Say.T(player, "backrooms:dispenser-empty"));
            return;
        }
        double hours = Now - player.Entity.WatchedAttributes.GetDouble(ArrivedKey, Now);
        double sugar = hours >= AllSugarHours ? 1 : hours >= HalfSugarHours ? 0.5 : 0;
        string[] pool = sapi.World.Rand.NextDouble() < sugar ? Sugar : fridge ? RealFridge : RealPantry;
        Item item = null;
        for (int tries = 0; tries < 4 && item == null; tries++) item = sapi.World.GetItem(new AssetLocation(pool[sapi.World.Rand.Next(pool.Length)]));
        if (item == null) return;
        if (fridge) s.Fridge--; else s.Pantry--;
        dirty = true;
        var given = new ItemStack(item);
        if (!player.InventoryManager.TryGiveItemstack(given, true)) sapi.World.SpawnItemEntity(given, pos.ToVec3d().Add(0.5, 1.1, 0.5));
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 8, 0.4f);
    }

    /// <summary>Kitty's dresser: something cute to wear, in your size, once a visit. Kitty's, so never a gift.</summary>
    public void OpenDresser(IServerPlayer player, BlockPos pos)
    {
        EntityPlayer entity = player.Entity;
        int visit = entity.WatchedAttributes.GetInt(VisitKey);
        if (visit == 0 || entity.WatchedAttributes.GetInt(DresserKey) == visit)
        {
            player.SendIngameError("dispenserempty", Backrooms.Say.T(player, "backrooms:dispenser-empty"));
            return;
        }
        Item item = null;
        for (int tries = 0; tries < 6 && item == null; tries++) item = sapi.World.GetItem(new AssetLocation(CuteClothes[sapi.World.Rand.Next(CuteClothes.Length)]));
        if (item == null) return;
        entity.WatchedAttributes.SetInt(DresserKey, visit);
        var stack = new ItemStack(item);
        stack.Attributes.SetBool(L974.CuteKey, true);
        stack.Attributes.SetBool(L974.KittysKey, true);
        if (!player.InventoryManager.TryGiveItemstack(stack, true)) sapi.World.SpawnItemEntity(stack, pos.ToVec3d().Add(0.5, 1.1, 0.5));
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 8, 0.5f);
    }

    /// <summary>
    /// The old computer, server side: DreamSleep's dream is made ready, and the Internet, once a visit, marks on your map
    /// where your house will let you wake.
    /// </summary>
    public void UseComputer(IServerPlayer player, BlockPos pos)
    {
        EntityPlayer entity = player.Entity;
        int visit = entity.WatchedAttributes.GetInt(VisitKey);
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/974/chime"), pos.X + 0.5, pos.Y + 1, pos.Z + 0.5, null, false, 12, 0.6f);
        if (visit == 0) return;
        entity.WatchedAttributes.SetInt(DreamKey, visit);
        if (entity.WatchedAttributes.GetInt(InternetKey) == visit) return;
        entity.WatchedAttributes.SetInt(InternetKey, visit);
        var house = CellOf(pos.X, pos.Z);
        Link? wake = thresholds?.L974WakeLink(layout.L974At(house.Item1, house.Item2, 9, 8));
        if (wake is { } w && sapi.World.Rand.NextDouble() < 0.75)
        {
            // (The search result first: where the map setting makes no waypoints, the mark is told after it)
            Say(player, "backrooms:l974-internet-1");
            MapMarks.Add(sapi, player, new Vec3d(w.X, w.Y, w.Z), Backrooms.Say.T(player, "backrooms:l974-waypoint"), "star1", MapMarks.WayColor, 8);
        }
        else Say(player, "backrooms:l974-internet-" + (2 + sapi.World.Rand.Next(3)));
    }

    // ================= Saving =================

    private byte[] Save()
    {
        using var ms = new System.IO.MemoryStream();
        using var w = new System.IO.BinaryWriter(ms);
        w.Write(1);
        w.Write(houses.Count);
        foreach (var (uid, (mx, mz)) in houses) { w.Write(uid); w.Write(mx); w.Write(mz); }
        w.Write(state.Count);
        foreach (var ((mx, mz), s) in state)
        {
            w.Write(mx); w.Write(mz);
            w.Write(s.Fridge); w.Write(s.Pantry); w.Write(s.RefilledAt); w.Write(s.OffendedUntil); w.Write(s.LastMeal); w.Write(s.LightsOut);
        }
        w.Flush();
        return ms.ToArray();
    }

    private void Load(byte[] data)
    {
        if (data == null) return;
        try
        {
            using var r = new System.IO.BinaryReader(new System.IO.MemoryStream(data));
            if (r.ReadInt32() != 1) return;
            for (int n = r.ReadInt32(); n > 0; n--) houses[r.ReadString()] = (r.ReadInt32(), r.ReadInt32());
            for (int n = r.ReadInt32(); n > 0; n--)
            {
                var key = (r.ReadInt32(), r.ReadInt32());
                state[key] = new HouseState { Fridge = r.ReadDouble(), Pantry = r.ReadDouble(), RefilledAt = r.ReadDouble(), OffendedUntil = r.ReadDouble(), LastMeal = r.ReadDouble(), LightsOut = r.ReadBoolean() };
            }
        }
        catch (Exception e)
        {
            sapi.Logger.Error("[backrooms] Level 974: the houses could not be read back ({0}); everyone gets a new one", e.Message);
            houses.Clear();
            state.Clear();
        }
    }
}

/// <summary>Kitty's fridge and pantry: one thing at a time, and they fill again by themselves.</summary>
public class BlockL974Food : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
            world.Api.ModLoader.GetModSystem<L974System>()?.Dispense(player, blockSel.Position, Attributes?["l974food"].AsString("fridge") ?? "fridge");
        return true;
    }
}

/// <summary>A tap in Kitty's House: the plumbing works. Use it with a bucket, jug or bowl to fill it with water.</summary>
public class BlockL974Tap : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        ItemSlot slot = byPlayer.InventoryManager.ActiveHotbarSlot;
        if (slot?.Itemstack?.Collectible is not ILiquidSink sink) return base.OnBlockInteractStart(world, byPlayer, blockSel);
        if (world.Side != EnumAppSide.Server) return true;
        if (slot.Itemstack.StackSize != 1) return true;
        Item water = world.GetItem(new AssetLocation("game:waterportion"));
        if (water == null) return true;
        var liquid = new ItemStack(water);
        float perLitre = BlockLiquidContainerBase.GetContainableProps(liquid)?.ItemsPerLitre ?? 100;
        liquid.StackSize = (int)(perLitre * sink.CapacityLitres);
        if (sink.TryPutLiquid(slot.Itemstack, liquid, sink.CapacityLitres) > 0)
        {
            slot.MarkDirty();
            world.PlaySoundAt(new AssetLocation("game:sounds/effect/water-fill"), blockSel.Position.X + 0.5, blockSel.Position.Y + 0.5, blockSel.Position.Z + 0.5, null, true, 8, 0.6f);
        }
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer) =>
        new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l974-tap", MouseButton = EnumMouseButton.Right } };
}

/// <summary>The old computer on the desk: the Guest desktop (the e-mail, the Internet, DreamSleep).</summary>
public class BlockL974Computer : Block
{
    private L974ComputerDialog dialog;

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
            world.Api.ModLoader.GetModSystem<L974System>()?.UseComputer(player, blockSel.Position);
        else if (world.Api is ICoreClientAPI capi)
        {
            dialog ??= new L974ComputerDialog(capi);
            if (!dialog.IsOpened()) dialog.TryOpen();
        }
        return true;
    }
}

/// <summary>The dresser in the open closet: cute clothes, in your size.</summary>
public class BlockL974Dresser : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
            world.Api.ModLoader.GetModSystem<L974System>()?.OpenDresser(player, blockSel.Position);
        return true;
    }
}

/// <summary>
/// Kitty: 3.2 m tall, faceless, matt black, its limbs ending in points. It cannot be hurt (striking it offends it), and
/// it is never stored with the world. What it does is <see cref="L974System"/>'s.
/// </summary>
public class EntityKitty : EntityAgent
{
    private static WorldInteraction[] help;

    public override bool StoreWithChunk => false;

    /// <summary>Right-click, with something cute in hand: a call, or (while it holds out its arm) the gift.</summary>
    public override WorldInteraction[] GetInteractionHelp(IClientWorldAccessor world, EntitySelection es, IClientPlayer player) =>
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l974-call", MouseButton = EnumMouseButton.Right } };

    public override bool ReceiveDamage(DamageSource damageSource, float damage)
    {
        if (World.Side == EnumAppSide.Server && damageSource?.Type != EnumDamageType.Heal)
            Api.ModLoader.GetModSystem<L974System>()?.OnKittyHurt(this, damageSource);
        return false;
    }

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode)
    {
        // (A melee hit is dealt in EntityAgent.OnInteract, and comes through ReceiveDamage from there)
        if (mode == EnumInteractMode.Attack)
        {
            base.OnInteract(byEntity, itemslot, hitPosition, mode);
            return;
        }
        if (World.Side != EnumAppSide.Server) return;
        if (mode == EnumInteractMode.Interact && byEntity is EntityPlayer { Player: IServerPlayer player })
            Api.ModLoader.GetModSystem<L974System>()?.OnKittyInteract(this, player, itemslot);
    }
}
