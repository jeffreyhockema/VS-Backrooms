using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// Level Fun =): its parties and what they do to you.
/// <list type="bullet">
/// <item><b>Guests.</b> A party room with guests has its Partygoers standing round the head table, put down when anyone
/// comes within <see cref="GuestRange"/> blocks and gone again when nobody is near. A guest killed stays dead for a
/// day; then the party has a new one ("we can easily create another hundred").</item>
/// <item><b>Party Fever.</b> A Partygoer that latches on bites: for <see cref="PendingSeconds"/> seconds the bite can
/// be treated with a poultice or a bandage; after that it is fever (a third, <see cref="FeverKey"/>). Fever makes you
/// hungry, lowers how steady you can be, and falls only once you are out of Level Fun (Almond Water helps). At full
/// fever you join the party: you die, and where you fell a new Partygoer with a red balloon stands guard over what
/// you dropped.</item>
/// <item><b>The disguise.</b> A party hat on your head and a red balloon in your hand: a Partygoer more than three
/// blocks off takes you for one of its own, as long as you don't run or strike (you are told so when you put it on there).</item>
/// <item><b>Voices.</b> One that has seen you speaks in a familiar voice (chat, now and then).</item>
/// </list>
/// The level's blocks with their own ways (cakes and cookies, gifts, Carnivorous Balloons, the poster trap) and its
/// Partygoers' AI are registered here too.
/// </summary>
public class FunSystem : ModSystem
{
    /// <summary>Player attribute: Party Fever, 0 to 1.</summary>
    public const string FeverKey = "backrooms:funFever";
    /// <summary>
    /// Entity attributes on a guest: its room's key (<see cref="KeyOf"/>, never negative; a guard's is -1 - its index in
    /// the guards), and where it stands.
    /// </summary>
    public const string RoomKey = "backrooms:funRoom", HomeKey = "backrooms:funHome";

    public const int GuestRange = 32;
    public const double FeverPerBite = 0.34, PendingSeconds = 30, DecayPerHour = 0.1, AlmondCure = 0.1;
    private const string SaveKey = "backrooms-fun";
    private const string LatchStat = "backrooms:funLatch", FeverStat = "backrooms:funFever";

    private static FunSystem server;
    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;

    /// <summary>The guests standing now, by room key (and by guard index for the guards).</summary>
    private readonly Dictionary<long, List<long>> standing = new();
    /// <summary>Guests killed, by room key: how many, and when the party has filled up again (calendar hours). Saved.</summary>
    private Dictionary<long, (int Killed, double RefillAt)> killed = new();
    /// <summary>The guards over the things of those who joined the party: where, and whether they still stand. Saved.</summary>
    private List<(double X, double Y, double Z, bool Alive)> guards = new();
    /// <summary>The supply shelves already stocked (the first time anyone opened them). Saved.</summary>
    private readonly HashSet<(int X, int Y, int Z)> stocked = new();

    private long tickId;

    private readonly Dictionary<long, (double Amount, long DueMs)> pending = new();
    private readonly Dictionary<long, long> latchedUntilMs = new(), lastVoiceMs = new(), struckMs = new(), noiseMs = new();
    private readonly Dictionary<long, (float Health, bool Treating)> lastHealth = new();
    private readonly Dictionary<long, double> lastHours = new(), lastDrank = new();
    /// <summary>Players wearing the disguise in the level now (told so when they put it on).</summary>
    private readonly HashSet<long> disguised = new();

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockClass("BackroomsFunCake", typeof(BlockFunCake));
        api.RegisterBlockClass("BackroomsFunCookies", typeof(BlockFunCake));
        api.RegisterBlockClass("BackroomsFunGift", typeof(BlockFunGift));
        api.RegisterBlockClass("BackroomsCarnivorousBalloon", typeof(BlockCarnivorousBalloon));
        api.RegisterBlockClass("BackroomsFunPoster", typeof(BlockFunPoster));
        api.RegisterBlockClass("BackroomsFunSupplyShelf", typeof(BlockFunSupplyShelf));
        api.RegisterItemClass("BackroomsVelvetCake", typeof(ItemVelvetCake));
        api.RegisterEntityBehaviorClass("backrooms-partygoer", typeof(EntityBehaviorPartygoer));
        api.RegisterEntity("BackroomsPartyHost", typeof(EntityPartyHost));
        AiTaskRegistry.Register<AiTaskPartygoer>("backrooms-partygoer");
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        AiTaskPartygoer.Forget();
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            server = this;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            Load();
            tickId = api.Event.RegisterGameTickListener(OnTick, 500);
            api.Event.PlayerDeath += OnPlayerDeath;
            api.Event.GameWorldSave += Save;
            api.Event.CanUseBlock += StockShelf;
            // A Partygoer's body (its fireproof hide and the carapace that opens) is attached here, whoever put it down
            api.Event.OnEntitySpawn += GiveBody;
            api.Event.OnEntityLoaded += GiveBody;
        });
    }

    private static void GiveBody(Entity entity)
    {
        if (AiTaskPartygoer.IsPartygoer(entity) && entity.GetBehavior<EntityBehaviorPartygoer>() == null)
            entity.AddBehavior(new EntityBehaviorPartygoer(entity));
    }

    public override void Dispose()
    {
        if (server == this) server = null;
        if (sapi == null || layout == null) return;
        if (tickId != 0) sapi.Event.UnregisterGameTickListener(tickId);
        sapi.Event.PlayerDeath -= OnPlayerDeath;
        sapi.Event.GameWorldSave -= Save;
        sapi.Event.CanUseBlock -= StockShelf;
        sapi.Event.OnEntitySpawn -= GiveBody;
        sapi.Event.OnEntityLoaded -= GiveBody;
    }

    // ================= Saved =================

    private void Load()
    {
        byte[] data = sapi.WorldManager.SaveGame.GetData(SaveKey);
        if (data == null) return;
        try
        {
            string[] lines = Encoding.UTF8.GetString(data).Split('\n');
            foreach (string line in lines)
            {
                string[] f = line.Split(' ');
                if (f.Length == 4 && f[0] == "k") killed[long.Parse(f[1])] = (int.Parse(f[2]), double.Parse(f[3], System.Globalization.CultureInfo.InvariantCulture));
                if (f.Length == 4 && f[0] == "s") stocked.Add((int.Parse(f[1]), int.Parse(f[2]), int.Parse(f[3])));
                if (f.Length == 4 && f[0] == "g")
                    guards.Add((double.Parse(f[1], System.Globalization.CultureInfo.InvariantCulture), double.Parse(f[2], System.Globalization.CultureInfo.InvariantCulture),
                        double.Parse(f[3], System.Globalization.CultureInfo.InvariantCulture), true));
            }
        }
        catch (Exception e)
        {
            sapi.Logger.Warning("[backrooms] Level Fun: could not read its saved parties: {0}", e.Message);
        }
    }

    private void Save()
    {
        var sb = new StringBuilder();
        var inv = System.Globalization.CultureInfo.InvariantCulture;
        double now = sapi.World.Calendar.TotalHours;
        foreach (var (key, (n, at)) in killed) if (at > now) sb.Append($"k {key} {n} {at.ToString(inv)}\n");
        foreach (var (x, y, z) in stocked) sb.Append($"s {x} {y} {z}\n");
        foreach (var g in guards) if (g.Alive) sb.Append($"g {g.X.ToString(inv)} {g.Y.ToString(inv)} {g.Z.ToString(inv)}\n");
        sapi.WorldManager.SaveGame.StoreData(SaveKey, Encoding.UTF8.GetBytes(sb.ToString()));
    }

    // ================= Party supplies =================

    /// <summary>
    /// A supply shelf in the service corridors is stocked the first time anyone opens it (fun-plan.md 3.7): candles,
    /// balloon string, party hats, red balloons, confetti, and now and then the crew's Firesalt. Never refuses the use.
    /// </summary>
    private bool StockShelf(IServerPlayer player, BlockSelection sel)
    {
        BlockPos pos = sel?.Position;
        if (pos == null || layout == null) return true;
        Block block = sapi.World.BlockAccessor.GetBlock(pos);
        if (block?.Code?.Domain != "backrooms" || !block.Code.Path.StartsWith("fun-supplyshelf")) return true;
        if (layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z)) != WorldLayout.FunLevel) return true;
        if (sapi.World.BlockAccessor.GetBlockEntity(pos) is not BlockEntityContainer shelf || !stocked.Add((pos.X, pos.Y, pos.Z))) return true;
        var rand = new Random((int)Hashing.Hash((ulong)sapi.World.Seed, pos.X, pos.Z ^ pos.Y * 31, 0x15F4));
        int slot = 0;
        void Put(string code, bool isBlock, double chance, int min, int max)
        {
            if (slot >= shelf.Inventory.Count || rand.NextDouble() >= chance) return;
            var at = new AssetLocation(code);
            CollectibleObject what = isBlock ? sapi.World.GetBlock(at) : sapi.World.GetItem(at);
            if (what == null) return;
            shelf.Inventory[slot].Itemstack = new ItemStack(what, min + rand.Next(max - min + 1));
            shelf.Inventory[slot++].MarkDirty();
        }
        Put("game:candle", false, 0.7, 1, 4);
        Put("game:flaxtwine", false, 0.6, 1, 3);
        Put(rand.NextDouble() < 0.5 ? "backrooms:fun-partyhat-stripes" : "backrooms:fun-partyhat-dots", false, 0.5, 1, 1);
        Put("backrooms:fun-balloon-red", false, 0.5, 1, 2);
        Put("backrooms:fun-confetti", true, 0.6, 2, 8);
        Put("backrooms:firesalt", true, 0.1, 1, 1);
        shelf.MarkDirty(true);
        return true;
    }

    // ================= Every half second =================

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { Alive: true } entity } player) continue;
            int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
            bool here = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) == WorldLayout.FunLevel;
            if (here) PutDownGuests(player, x, z);
            // Dressed for the party: told so once each time they put the disguise together here
            if (here && Disguised(entity))
            {
                if (disguised.Add(entity.EntityId)) Tell(player, "backrooms:fun-disguised");
            }
            else disguised.Remove(entity.EntityId);
            Fever(player, entity, here, now);
            // Let go: the arm that held you lets go
            if (latchedUntilMs.TryGetValue(entity.EntityId, out long until) && now >= until)
            {
                latchedUntilMs.Remove(entity.EntityId);
                entity.Stats.Remove("walkspeed", LatchStat);
            }
        }
    }

    // ================= Guests =================

    /// <summary>Puts down the guests of every party near a player that has none standing, out of the player's sight.</summary>
    private void PutDownGuests(IServerPlayer player, int x, int z)
    {
        double hours = sapi.World.Calendar.TotalHours;
        foreach (FunRoom room in layout.FunRoomsNear(x, z, GuestRange))
        {
            if (room.Guests == 0 || room.Spots.Count == 0) continue;
            long key = KeyOf(room);
            if (Standing(key)) continue;
            int count = room.Spots.Count;
            if (killed.TryGetValue(key, out var k))
            {
                if (k.RefillAt <= hours) killed.Remove(key);
                else count -= k.Killed;
            }
            if (count <= 0) continue;
            int y = geometry.FloorFor(WorldLayout.FunLevel) + 1;
            // Never in front of the player's eyes
            Vec3d eyes = Senses.Eyes(player.Entity);
            bool seen = room.Spots.Take(count).Any(s => eyes.DistanceTo(new Vec3d(s.X + 0.5, y + 1, s.Z + 0.5)) < GuestRange
                && Senses.ClearLine(sapi.World, eyes, new Vec3d(s.X + 0.5, y + 1, s.Z + 0.5)));
            if (seen) continue;
            var ids = new List<long>();
            for (int i = 0; i < count; i++)
            {
                var (sx, sz) = room.Spots[i];
                // (A plan block's rooms run on into the level's solid rim, and past it)
                Tile at = layout.TileAt(sx, sz);
                if (at.Level != WorldLayout.FunLevel || at.Kind != TileKind.Floor) continue;
                bool intern = Hashing.Unit(Hashing.Mix(room.Key + (ulong)i)) < 0.5;
                float yaw = (float)(Hashing.Unit(Hashing.Mix(room.Key ^ (ulong)(i * 7919))) * Math.PI * 2);
                Entity guest = PutDown(intern ? Roster.PartygoerIntern : Roster.Partygoer, new Vec3d(sx + 0.5, y, sz + 0.5), yaw, player.Entity, key);
                if (guest != null) ids.Add(guest.EntityId);
            }
            standing[key] = ids;
        }
        // The guards over the belongings of those who joined the party
        for (int g = 0; g < guards.Count; g++)
        {
            var guard = guards[g];
            if (!guard.Alive || Standing(-1 - g)) continue;
            double dx = guard.X - player.Entity.Pos.X, dz = guard.Z - player.Entity.Pos.Z;
            if (dx * dx + dz * dz > GuestRange * GuestRange) continue;
            Entity e = PutDown(Roster.PartygoerIntern, new Vec3d(guard.X, guard.Y, guard.Z), 0, player.Entity, -1 - g);
            if (e != null) standing[-1 - g] = new List<long> { e.EntityId };
        }
    }

    /// <summary>
    /// A party room's key in <see cref="standing"/>, <see cref="killed"/> and its guests' <see cref="RoomKey"/>: its hash
    /// with the sign bit cleared, since negative keys are the guards'. (Taken whole, half the rooms' keys were negative,
    /// and a guest killed in one of those was taken for a guard, so its party was never one short.)
    /// </summary>
    private static long KeyOf(FunRoom room) => (long)(room.Key & long.MaxValue);

    private bool Standing(long key)
    {
        if (!standing.TryGetValue(key, out var ids)) return false;
        foreach (long id in ids)
            if (sapi.World.GetEntityById(id) is { Alive: true }) return true;
        return false;
    }

    private Entity PutDown(string code, Vec3d at, float yaw, Entity near, long key)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(code));
        if (type == null) return null;
        Entity entity = sapi.World.ClassRegistry.CreateEntity(type);
        entity.Pos.SetPos(at.X, at.Y + 0.02, at.Z);
        entity.Pos.Yaw = yaw;
        EntityBehaviorMenace.Prepare(entity, near, Encounter.Ambient, false, sapi.World.ElapsedMilliseconds);
        entity.Attributes.SetLong(RoomKey, key);
        entity.Attributes.SetDouble(HomeKey + "X", at.X);
        entity.Attributes.SetDouble(HomeKey + "Y", at.Y);
        entity.Attributes.SetDouble(HomeKey + "Z", at.Z);
        double danger = Danger.OfLevel(WorldLayout.FunLevel);
        entity.Attributes.SetDouble(Danger.Key, danger);
        if (near.WatchedAttributes.GetBool("backrooms:testTarget")) entity.AlwaysActive = true;
        sapi.World.SpawnEntity(entity);
        if (entity.GetBehavior<EntityBehaviorHealth>() is { } health)
        {
            health.SetMaxHealthModifiers("backrooms-danger", health.BaseMaxHealth * Danger.ExtraHealth(danger));
            health.Health = health.MaxHealth;
        }
        return entity;
    }

    /// <summary>A guest (or a guard) was killed: its party is one short until tomorrow.</summary>
    public static void GuestKilled(Entity entity)
    {
        if (server == null || !entity.Attributes.HasAttribute(RoomKey)) return;
        long key = entity.Attributes.GetLong(RoomKey);
        if (key < 0)
        {
            int g = (int)(-1 - key);
            if (g < server.guards.Count) server.guards[g] = server.guards[g] with { Alive = false };
            return;
        }
        double refill = server.sapi.World.Calendar.TotalHours + 24;
        server.killed[key] = (server.killed.TryGetValue(key, out var k) ? k.Killed + 1 : 1, refill);
    }

    /// <summary>The menace band at a place in the level: the parties with guests are its edge; the deck and the waiting rooms quieter.</summary>
    public static MenaceBand BandAt(WorldLayout layout, int gx, int gz)
    {
        var zone = (FunZone)layout.TileAt(gx, gz).Zone;
        if (zone is FunZone.Waiting or FunZone.Deck or FunZone.Sea or FunZone.Lobby) return MenaceBand.Heartland;
        return layout.FunRoomAt(gx, gz) is { Guests: > 0 } ? MenaceBand.Threshold : MenaceBand.Approach;
    }

    // ================= Party Fever =================

    /// <summary>A Partygoer has latched on: held a moment, and bitten. The bite is fever unless treated in time.</summary>
    public static void Latched(Entity who)
    {
        if (server == null || who is not EntityPlayer { Player: IServerPlayer player } entity) return;
        long now = server.sapi.World.ElapsedMilliseconds;
        entity.Stats.Set("walkspeed", LatchStat, -0.7f, false);
        server.latchedUntilMs[entity.EntityId] = now + 1500;
        double amount = server.pending.TryGetValue(entity.EntityId, out var p) ? p.Amount + FeverPerBite : FeverPerBite;
        server.pending[entity.EntityId] = (amount, now + (long)(PendingSeconds * 1000));
        Tell(player, "backrooms:fun-latched");
        Tell(player, "backrooms:fun-fever-pending");
    }

    /// <summary>Adds Party Fever at once (the Red Velvet).</summary>
    public static void AddFever(Entity who, double amount)
    {
        double fever = who.WatchedAttributes.GetDouble(FeverKey, 0);
        who.WatchedAttributes.SetDouble(FeverKey, Math.Clamp(fever + amount, 0, 1));
    }

    private void Fever(IServerPlayer player, EntityPlayer entity, bool here, long now)
    {
        long id = entity.EntityId;
        double fever = entity.WatchedAttributes.GetDouble(FeverKey, 0);

        // A bite not yet fever: a poultice or a bandage now, and it never takes
        if (pending.TryGetValue(id, out var bite))
        {
            float health = entity.GetBehavior<EntityBehaviorHealth>()?.Health ?? 0;
            bool treating = Treating(entity);
            if (lastHealth.TryGetValue(id, out var before) && health - before.Health >= 0.75f && (treating || before.Treating))
            {
                pending.Remove(id);
                Tell(player, "backrooms:fun-fever-cleared");
            }
            else if (now >= bite.DueMs)
            {
                pending.Remove(id);
                fever = Math.Min(1, fever + bite.Amount);
                entity.WatchedAttributes.SetDouble(FeverKey, fever);
                Tell(player, "backrooms:fun-fever");
            }
            lastHealth[id] = (health, treating);
        }
        else lastHealth.Remove(id);

        // Falling, slowly, once out of the level; Almond Water helps
        double hours = sapi.World.Calendar.TotalHours;
        double drank = entity.Attributes.GetDouble(AlmondWater.DrankKey, -1);
        if (fever > 0 && !here)
        {
            if (lastHours.TryGetValue(id, out double then) && hours > then) fever -= DecayPerHour * (hours - then);
            if (lastDrank.TryGetValue(id, out double was) && drank > was) fever -= AlmondCure;
            fever = Math.Max(0, fever);
            entity.WatchedAttributes.SetDouble(FeverKey, fever);
        }
        lastHours[id] = hours;
        lastDrank[id] = drank;

        // What it does: hunger, and a ceiling on how steady you can be. (Only on a change: every Set or Remove rewrites
        // and resends the player's whole stats tree, and this runs for every player twice a second)
        bool hungry = HasStat(entity, "hungerrate", FeverStat);
        if (fever > 0 && !hungry) entity.Stats.Set("hungerrate", FeverStat, 0.25f, false);
        else if (fever <= 0 && hungry) entity.Stats.Remove("hungerrate", FeverStat);
        if (fever > 0)
        {
            double cap = 1 - 0.5 * fever, stability = entity.WatchedAttributes.GetDouble("temporalStability", 1);
            if (stability > cap) entity.WatchedAttributes.SetDouble("temporalStability", cap);
            if (here && sapi.World.Rand.NextDouble() < 0.004) Voice(player, null);
        }

        // At full fever, you join the party
        if (fever >= 1)
        {
            entity.WatchedAttributes.SetDouble(FeverKey, 0);
            sapi.BroadcastMessageToAllGroups(Lang.Get("backrooms:fun-joined", player.PlayerName), EnumChatType.Notification);
            entity.Die(EnumDespawnReason.Death, JoinedTheParty);
        }
    }

    /// <summary>Whether an entity has a stat modifier (the watched "stats" tree mirrors every one, saved or not).</summary>
    private static bool HasStat(Entity entity, string category, string code) =>
        entity.WatchedAttributes.GetTreeAttribute("stats")?.GetTreeAttribute(category)?.HasAttribute(code) == true;

    /// <summary>Whether someone has a poultice or a bandage in hand.</summary>
    private static bool Treating(EntityAgent entity) => IsTreatment(Senses.RightHand(entity)) || IsTreatment(Senses.LeftHand(entity));

    private static bool IsTreatment(ItemSlot slot)
    {
        string path = slot?.Itemstack?.Collectible?.Code?.Path;
        return path != null && (path.Contains("poultice") || path.Contains("bandage"));
    }

    /// <summary>
    /// What full fever kills you with. The server reports a player's death a tick later, with this same object, which is
    /// how <see cref="OnPlayerDeath"/> knows it from any other death "from inside" (starving reports Internal too).
    /// </summary>
    private static readonly DamageSource JoinedTheParty = new() { Source = EnumDamageSource.Internal, Type = EnumDamageType.Injury };

    private void OnPlayerDeath(IServerPlayer player, DamageSource source)
    {
        EntityPlayer entity = player.Entity;
        if (entity == null) return;
        pending.Remove(entity.EntityId);
        entity.WatchedAttributes.SetDouble(FeverKey, 0);
        int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
        if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.FunLevel) return;
        // Killed in Level Fun by its own (a Partygoer, or the fever): a new one, with a red balloon, will stand where you
        // fell. Not for starving, drowning or anything else that happens to kill you here
        Entity killer = source?.GetCauseEntity() ?? source?.SourceEntity;
        bool theirs = killer?.Code?.Path?.StartsWith("partygoer") == true || ReferenceEquals(source, JoinedTheParty);
        if (theirs) guards.Add((entity.Pos.X, geometry.FloorFor(WorldLayout.FunLevel) + 1, entity.Pos.Z, true));
    }

    // ================= The disguise, and what they notice =================

    /// <summary>Whether someone wears a party hat and holds a red balloon. (Asked by every Partygoer that looks at them.)</summary>
    public static bool Disguised(EntityAgent entity)
    {
        // (A player entity without its player, still joining or just gone, has no hands to look at: this threw every
        // tick and kept a save from loading while someone stood in Level Fun)
        bool balloon = Senses.RightHand(entity)?.Itemstack?.Collectible?.Code?.Path == "fun-balloon-red"
            || Senses.LeftHand(entity)?.Itemstack?.Collectible?.Code?.Path == "fun-balloon-red";
        if (!balloon || entity is not EntityPlayer { Player: { } player }) return false;
        IInventory clothes = player.InventoryManager?.GetOwnInventory(GlobalConstants.characterInvClassName);
        if (clothes == null) return false;
        foreach (ItemSlot slot in clothes)
            if (slot?.Itemstack?.Collectible?.Code?.Path?.StartsWith("fun-partyhat") == true) return true;
        return false;
    }

    /// <summary>Someone struck a Partygoer: for a while they look like nothing but what they are.</summary>
    public static void Struck(Entity who)
    {
        if (server != null && who != null) server.struckMs[who.EntityId] = server.sapi.World.ElapsedMilliseconds;
    }

    public static bool StruckLately(Entity who) =>
        server != null && server.struckMs.TryGetValue(who.EntityId, out long at) && server.sapi.World.ElapsedMilliseconds - at < 15000;

    /// <summary>A loud noise (a popper, a balloon popping): every Partygoer within <paramref name="range"/> blocks comes to see.</summary>
    public static void Noise(IWorldAccessor world, Vec3d at, Entity who, double range)
    {
        if (server != null && who != null) server.noiseMs[who.EntityId] = world.ElapsedMilliseconds;
        AiTaskPartygoer.Hear(world, at, who, range);
        if (who != null) world.Api.ModLoader.GetModSystem<MenaceSystem>()?.MakeNoise(who, 0.5);
    }

    /// <summary>A line in a familiar voice, now and then, from one that has seen you (or from the fever).</summary>
    public static void Voice(IServerPlayer player, Entity from)
    {
        if (server == null || player?.Entity == null) return;
        long now = server.sapi.World.ElapsedMilliseconds;
        if (server.lastVoiceMs.TryGetValue(player.Entity.EntityId, out long last) && now - last < 20000) return;
        server.lastVoiceMs[player.Entity.EntityId] = now;
        Random rand = server.sapi.World.Rand;
        // Whose voice: someone else in the world, else somebody you knew
        IPlayer[] others = server.sapi.World.AllOnlinePlayers.Where(p => p.PlayerUID != player.PlayerUID).ToArray();
        string who = others.Length > 0 ? others[rand.Next(others.Length)].PlayerName : Lang.GetL(player.LanguageCode, $"backrooms:fun-voice-familiar-{rand.Next(4) + 1}");
        string line = Lang.GetL(player.LanguageCode, $"backrooms:fun-voice-{rand.Next(7) + 1}");
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.GetL(player.LanguageCode, "backrooms:fun-voice-from", who, line), EnumChatType.Notification);
    }

    private static void Tell(IServerPlayer player, string key) =>
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.GetL(player.LanguageCode, key), EnumChatType.Notification);
}

// ================= The level's blocks and items =================

/// <summary>The Party Host: a golden fried egg in the ceiling. It never moves and cannot be hurt or killed (like the Keymaster).</summary>
public class EntityPartyHost : EntityAgent
{
    public override bool ShouldReceiveDamage(DamageSource damageSource, float damage) => false;

    public override bool ReceiveDamage(DamageSource damageSource, float damage) => false;
}

/// <summary>
/// A cake (or a plate of cookies) on a party table: right-click to take a slice (a cookie), and the block steps down to
/// what is left (its code ends in how many are left; at 0 only crumbs, or an empty plate).
/// </summary>
public class BlockFunCake : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        string path = Code.Path;
        int dash = path.LastIndexOf('-');
        if (dash < 0 || !int.TryParse(path[(dash + 1)..], out int left) || left <= 0) return base.OnBlockInteractStart(world, byPlayer, blockSel);
        if (world.Side != EnumAppSide.Server) return true;
        // fun-cake-birthday-4 gives fun-cakeslice-birthday; fun-cookieplate-3 gives fun-cookie
        string piece = path.StartsWith("fun-cookieplate") ? "fun-cookie" : "fun-cakeslice-" + path.Split('-')[2];
        Item item = world.GetItem(new AssetLocation("backrooms", piece));
        if (item != null)
        {
            var stack = new ItemStack(item);
            if (!byPlayer.InventoryManager.TryGiveItemstack(stack, true)) world.SpawnItemEntity(stack, blockSel.Position.ToVec3d().Add(0.5, 0.5, 0.5));
        }
        Block next = world.GetBlock(new AssetLocation("backrooms", path[..(dash + 1)] + (left - 1)));
        if (next != null) world.BlockAccessor.ExchangeBlock(next.BlockId, blockSel.Position);
        world.PlaySoundAt(new AssetLocation("game:sounds/player/eat"), blockSel.Position.X + 0.5, blockSel.Position.Y + 0.5, blockSel.Position.Z + 0.5, byPlayer, true, 8, 0.5f);
        return true;
    }
}

/// <summary>A wrapped gift: break it open for what is inside, unless it is one of the one in five that is a party popper.</summary>
public class BlockFunGift : Block
{
    public static bool IsPopper(BlockPos pos) => Hashing.Unit(Hashing.Hash(0x15F0, pos.X, pos.Z ^ pos.Y * 31, 0x15F1)) < 0.2;

    public override void OnBlockBroken(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1)
    {
        if (world.Side == EnumAppSide.Server && IsPopper(pos) && byPlayer?.WorldData.CurrentGameMode != EnumGameMode.Creative)
        {
            // Bang: confetti everywhere, and nothing inside; and it carries
            world.BlockAccessor.SetBlock(0, pos);
            Vec3d at = pos.ToVec3d().Add(0.5, 0.5, 0.5);
            world.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/fun/popper"), at.X, at.Y, at.Z, null, true, 32, 1f);
            foreach (int colour in new[] { ColorUtil.ToRgba(255, 220, 60, 60), ColorUtil.ToRgba(255, 60, 120, 220), ColorUtil.ToRgba(255, 240, 210, 60), ColorUtil.ToRgba(255, 80, 200, 90) })
                world.SpawnParticles(25, colour, at.AddCopy(-0.3, 0, -0.3), at.AddCopy(0.3, 0.6, 0.3), new Vec3f(-2, 1, -2), new Vec3f(2, 4, 2), 2.5f, 0.3f, 0.5f, EnumParticleModel.Quad);
            FunSystem.Noise(world, at, byPlayer?.Entity, 16);
            return;
        }
        base.OnBlockBroken(world, pos, byPlayer, dropQuantityMultiplier);
        // Now and then, among a wanderer's belongings, the Hub's key to Level Fun (its only source, as The End's desks are its).
        // (Rolled by position; a gift drops only what is inside, never itself, so the roll cannot be had twice)
        if (world.Side == EnumAppSide.Server && byPlayer?.WorldData.CurrentGameMode == EnumGameMode.Survival
            && Hashing.Unit(Hashing.Hash(0x15F2, pos.X, pos.Z ^ pos.Y * 31, 0x15F3)) < 0.04
            && world.GetItem(new AssetLocation("backrooms:hub-key-fun")) is { } key)
            HubSystem.KeyTurnedUp(world, byPlayer, new ItemStack(key), pos);
    }
}

/// <summary>
/// A Carnivorous Balloon (Entity 110): a balloon floating at chest height, tied to nothing, its ribbon curled. Walk
/// into it and the ribbon stings: it hurts and holds you nearly still a moment. Pop it and it lets out its gas.
/// </summary>
public class BlockCarnivorousBalloon : Block
{
    private const string StungKey = "backrooms:stungMs", StungStat = "backrooms:stung";

    public override void OnEntityInside(IWorldAccessor world, Entity entity, BlockPos pos)
    {
        base.OnEntityInside(world, entity, pos);
        if (world.Side != EnumAppSide.Server || entity is not EntityPlayer { Alive: true } player) return;
        if (player.Player?.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator) return;
        long now = world.ElapsedMilliseconds;
        // (Entity attributes are saved, but the clock starts again with the server: a sting "later than now" is from before)
        long since = now - entity.Attributes.GetLong(StungKey, -100000);
        if (since >= 0 && since < 3000) return;
        entity.Attributes.SetLong(StungKey, now);
        entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Block, SourceBlock = this, SourcePos = pos.ToVec3d(), Type = EnumDamageType.Poison }, 3);
        player.Stats.Set("walkspeed", StungStat, -0.8f, false);
        world.RegisterCallback(_ => player.Stats.Remove("walkspeed", StungStat), 3000);
        world.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/fun/cballoon-sting"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 16, 1f);
    }

    public override void OnBlockBroken(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1)
    {
        base.OnBlockBroken(world, pos, byPlayer, dropQuantityMultiplier);
        if (world.Side != EnumAppSide.Server) return;
        // Ammonia: it burns the eyes and the throat of anyone close, for a few seconds
        Vec3d at = pos.ToVec3d().Add(0.5, 0.5, 0.5);
        world.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/fun/cballoon-gas"), at.X, at.Y, at.Z, null, true, 16, 1f);
        world.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/fun/balloonpop"), at.X, at.Y, at.Z, null, true, 24, 1f);
        world.SpawnParticles(30, ColorUtil.ToRgba(120, 220, 230, 170), at.AddCopy(-0.5, -0.5, -0.5), at.AddCopy(0.5, 0.5, 0.5), new Vec3f(-0.5f, 0, -0.5f), new Vec3f(0.5f, 0.4f, 0.5f), 3f, -0.02f, 1f, EnumParticleModel.Quad);
        for (int i = 1; i <= 4; i++)
        {
            world.RegisterCallback(_ =>
            {
                foreach (Entity e in world.GetEntitiesAround(at, 2.5f, 2, e => e is EntityPlayer { Alive: true }))
                    e.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Block, SourceBlock = this, SourcePos = at, Type = EnumDamageType.Poison }, 1);
            }, 1000 * i);
        }
        FunSystem.Noise(world, at, byPlayer?.Entity, 10);
    }
}

/// <summary>
/// The TIME 4 FUN =) poster in a Level 0 party cell. Touch it and you are taken (its threshold behaviour); hold a lit
/// torch to it instead and it curls, blackens and is gone, and with it the red smileys of the room.
/// </summary>
public class BlockFunPoster : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        string held = byPlayer?.InventoryManager?.ActiveHotbarSlot?.Itemstack?.Collectible?.Code?.Path;
        if (held != null && held.StartsWith("torch") && held.Contains("-lit"))
        {
            if (world.Side == EnumAppSide.Server)
            {
                BlockPos pos = blockSel.Position;
                Vec3d at = pos.ToVec3d().Add(0.5, 0.5, 0.5);
                world.BlockAccessor.SetBlock(0, pos);
                world.SpawnParticles(20, ColorUtil.ToRgba(200, 40, 40, 40), at.AddCopy(-0.4, -0.4, -0.4), at.AddCopy(0.4, 0.4, 0.4), new Vec3f(-0.2f, 0.2f, -0.2f), new Vec3f(0.2f, 0.8f, 0.2f), 2f, -0.03f, 0.8f, EnumParticleModel.Quad);
                world.PlaySoundAt(new AssetLocation("game:sounds/effect/extinguish"), at.X, at.Y, at.Z, byPlayer, true, 16, 1f);
                // The red smileys of the same room go with it
                var probe = new BlockPos(0);
                for (int dx = -14; dx <= 14; dx++)
                    for (int dz = -14; dz <= 14; dz++)
                    {
                        probe.Set(pos.X + dx, pos.Y, pos.Z + dz);
                        if (world.BlockAccessor.GetBlock(probe)?.Code?.Path?.StartsWith("fun-smiley") == true) world.BlockAccessor.SetBlock(0, probe);
                    }
                if (byPlayer is IServerPlayer player)
                    player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.GetL(player.LanguageCode, "backrooms:funposter-burnt"), EnumChatType.Notification);
            }
            return true;
        }
        return base.OnBlockInteractStart(world, byPlayer, blockSel);
    }
}

/// <summary>A slice of Red Velvet =): sweeter than it should be, and filling. It costs you some steadiness, and the party gets into you.</summary>
public class ItemVelvetCake : Item
{
    protected override void tryEatStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity)
    {
        int before = slot.StackSize;
        base.tryEatStop(secondsUsed, slot, byEntity);
        if (byEntity.World.Side != EnumAppSide.Server || slot.StackSize >= before) return;
        double stability = byEntity.WatchedAttributes.GetDouble("temporalStability", 1);
        byEntity.WatchedAttributes.SetDouble("temporalStability", Math.Max(0, stability - 0.2));
        FunSystem.AddFever(byEntity, 0.2);
    }
}
