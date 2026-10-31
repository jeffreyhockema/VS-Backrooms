using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using Backrooms.Map;
using Backrooms.Notes;
using Backrooms.Worldgen;
using ProtoBuf;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace Backrooms.Corpse;

/// <summary>One corpse in the save data: what the map markers and the dev commands go by (the body itself is an entity, saved with its chunk).</summary>
[ProtoContract]
public class CorpseRecord
{
    [ProtoMember(1)] public long EntityId;
    [ProtoMember(2)] public string Owner;
    [ProtoMember(3)] public string OwnerName;
    [ProtoMember(4)] public double X;
    [ProtoMember(5)] public double Y;
    [ProtoMember(6)] public double Z;
    /// <summary>The calendar's TotalDays when they died.</summary>
    [ProtoMember(7)] public double DiedDays;
    /// <summary>The map waypoint's Guid, or null if it has none (no map, or the owner was not there to be given one).</summary>
    [ProtoMember(8)] public string WaypointGuid;
    [ProtoMember(9)] public bool Bones;
}

/// <summary>
/// Death leaves a corpse (docs/design/corpse.md). When a player dies, the game drops what they carried as loose items that
/// vanish in ten minutes (and tells the dead player that other players have so many in-game minutes to revive them: the
/// "29 minutes" of the death screen is that, and nothing to do with the items). Here the dropped stacks are caught as they
/// are spawned and put into an <see cref="EntityCorpse"/> where the player fell instead: the player's own seraph, in their skin and
/// clothes, lying down, which never despawns and turns to bones after <see cref="BonesAfterDays"/> in-game days. Each corpse
/// has its own marker on its owner's map (the newest pinned), and loses it when emptied.
/// Worlds that keep the inventory on death drop nothing, so there is nothing to catch and no corpse.
/// </summary>
public class CorpseSystem : ModSystem
{
    public const string FreshCode = "backrooms:corpse";
    public const string BonesCode = "backrooms:corpse-bones";

    /// <summary>How long a body lies before it is only bones, in in-game days.</summary>
    public const double BonesAfterDays = 3;

    private const string SaveKey = "backrooms-corpses";

    /// <summary>How long after a death a drop can still be its own (ms): the game drops them within a tick or two, a lagging server later.</summary>
    private const int CatchMs = 15000;

    /// <summary>What a death took with it, from the moment of dying until the corpse is made.</summary>
    private sealed class Dying
    {
        public string Uid, Name;
        public long Ms;
        public Vec3d Pos;
        public float Yaw;
        public ITreeAttribute Skin, Gear;
        public readonly List<ItemStack> Stacks = new();
        /// <summary>Set when its first body is being made, so that nothing makes a second one (or drops the stacks twice).</summary>
        public bool Settled;
        /// <summary>The body, once made; drops that come late are put into it.</summary>
        public EntityCorpse Body;
        /// <summary>Loose items seen near the death, not yet known to be its own (decided on the next tick).</summary>
        public readonly List<EntityItem> Candidates = new();
        public bool ConfirmQueued;
        /// <summary>What was in the crafting grid at death (the game drops those without marking them as the player's): item code and quantity.</summary>
        public readonly List<(string Code, int Size)> Crafting = new();
    }

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private bool active;
    private List<CorpseRecord> records = new();
    private bool dirty;
    private readonly Dictionary<string, Dying> dying = new();
    /// <summary>Where each player last stood on firm ground, for a death in the air or the void.</summary>
    private readonly Dictionary<string, Vec3d> lastSafe = new();
    /// <summary>Players who have a corpse they have not been told of yet (told when they wake again), and when it was made.</summary>
    private readonly Dictionary<string, long> toldAt = new();
    private readonly Dictionary<string, CorpseRecord> toTell = new();
    private Entity swapFrom;

    private static readonly MethodInfo ResendWaypoints = typeof(WaypointMapLayer).GetMethod("ResendWaypoints", BindingFlags.Instance | BindingFlags.NonPublic);

    // After the world map (0.1), whose death waypoint ours takes away
    public override double ExecuteOrder() => 1.0;

    public override void Start(ICoreAPI api)
    {
        api.RegisterEntity("BackroomsCorpse", typeof(EntityCorpse));
        api.RegisterEntityBehaviorClass("backrooms-corpsecontents", typeof(EntityBehaviorCorpseContents));
    }

    /// <summary>
    /// The body is a seraph in a player's skin, so it has the player's skin parts to know what the skin config names: the
    /// player's own attributes, copied to the corpse's type (on both sides, before any is made).
    /// </summary>
    public override void AssetsFinalize(ICoreAPI api)
    {
        EntityProperties player = api.World.GetEntityType(new AssetLocation("game:player"));
        EntityProperties corpse = api.World.GetEntityType(new AssetLocation(FreshCode));
        if (corpse == null) return;
        JsonObject attributes = player?.Attributes;
        if (attributes == null || !attributes["skinnableParts"].Exists)
        {
            api.Logger.Warning("[backrooms] corpse: the player has no skinnableParts; a body will have a random skin");
            return;
        }
        corpse.Attributes = JsonObject.FromJson(attributes.ToString());
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.SaveGameLoaded += Load;
        api.Event.GameWorldSave += Save;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            active = true;
            layout = BackroomsWorld.CreateLayout(api.World);
            api.Event.OnEntityDeath += OnEntityDeath;
            api.Event.OnEntitySpawn += OnEntitySpawned;
            api.Event.PlayerDeath += OnPlayerDeath;
            api.Event.PlayerRespawn += OnPlayerRespawn;
            api.Event.PlayerNowPlaying += OnPlayerNowPlaying;
            api.Event.RegisterGameTickListener(_ => TrackSafePlaces(), 1000);
            // A server stopping inside a death's catch window: the stacks are already out of the world, so the bodies are made now
            api.Event.ServerRunPhase(EnumServerRunPhase.Shutdown, SettleAll);
        });
    }

    public override void Dispose()
    {
        layout = null;
        base.Dispose();
    }

    // ================= Save data =================

    private void Load()
    {
        try
        {
            byte[] data = sapi.WorldManager.SaveGame.GetData(SaveKey);
            records = data == null ? new() : SerializerUtil.Deserialize<List<CorpseRecord>>(data) ?? new();
        }
        catch (Exception ex)
        {
            sapi.Logger.Error("[backrooms] could not read the corpse save data; starting afresh: {0}", ex);
            records = new();
        }
    }

    private void Save()
    {
        if (!dirty) return;
        dirty = false;
        sapi.WorldManager.SaveGame.StoreData(SaveKey, SerializerUtil.Serialize(records));
    }

    // ================= Catching a death's drops =================

    private void OnEntityDeath(Entity entity, DamageSource source)
    {
        if (entity is not EntityPlayer { Player: IServerPlayer player } body) return;
        // (A world that keeps the inventory drops nothing: catching what happens to lie nearby would take a stranger's things)
        if (body.Properties?.Server?.Attributes?.GetBool("keepContents", false) == true) return;
        var d = new Dying
        {
            Uid = player.PlayerUID,
            Name = player.PlayerName,
            Ms = sapi.World.ElapsedMilliseconds,
            Pos = body.Pos.XYZ.Clone(),
            Yaw = body.Pos.Yaw,
            Skin = body.WatchedAttributes.GetTreeAttribute("skinConfig")?.Clone() as ITreeAttribute,
            Gear = CopyClothes(player),
        };
        try
        {
            if (player.InventoryManager.GetOwnInventory(GlobalConstants.craftingInvClassName) is IInventory grid)
                foreach (ItemSlot slot in grid)
                    if (!slot.Empty && slot.GetType().Name != "ItemSlotCraftingOutput") d.Crafting.Add((slot.Itemstack.Collectible.Code.ToString(), slot.StackSize));
        }
        catch (Exception) { }
        dying[d.Uid] = d;
        sapi.World.RegisterCallback(_ => Expire(d), CatchMs + 100);
    }

    /// <summary>What the player is wearing, as the tree the body's own clothes are kept in (they are not dropped: they stay on the player).</summary>
    private static ITreeAttribute CopyClothes(IServerPlayer player)
    {
        try
        {
            if (player.InventoryManager.GetOwnInventory(GlobalConstants.characterInvClassName) is not InventoryBase clothes) return null;
            var tree = new TreeAttribute();
            clothes.ToTreeAttributes(tree);
            return tree.Clone() as ITreeAttribute;
        }
        catch (Exception) { return null; }
    }

    /// <summary>
    /// A loose item has appeared near a death. The game marks the stacks it drops from a player's inventory with their
    /// uid, but only after spawning them, so nothing is decided here: it is looked at again on the next tick (<see cref="Confirm"/>).
    /// </summary>
    private void OnEntitySpawned(Entity entity)
    {
        if (dying.Count == 0 || entity is not EntityItem { Itemstack: { } } item || !item.Alive) return;
        long now = sapi.World.ElapsedMilliseconds;
        Dying best = null;
        double bestDistance = 2.0;
        foreach (Dying d in dying.Values)
        {
            if (now - d.Ms > CatchMs) continue;
            double distance = d.Pos.DistanceTo(item.Pos.XYZ);
            if (distance < bestDistance) { best = d; bestDistance = distance; }
        }
        if (best == null) return;
        best.Candidates.Add(item);
        if (best.ConfirmQueued) return;
        best.ConfirmQueued = true;
        sapi.Event.EnqueueMainThreadTask(() => Confirm(best, false), "corpse");
    }

    /// <summary>
    /// The candidates of a death, one tick on: the ones the game marked as the dead player's (or, unmarked, matching what was in
    /// their crafting grid) are taken, and the rest are left in the world untouched. The first taken make the body; later ones
    /// (a lagging server drops late) go into it.
    /// </summary>
    private void Confirm(Dying d, bool stopping)
    {
        d.ConfirmQueued = false;
        var taken = new List<ItemStack>();
        foreach (EntityItem item in d.Candidates)
        {
            if (!item.Alive || item.Itemstack == null) continue;
            string marked = item.ByPlayerUid;
            bool ours = marked == d.Uid;
            if (!ours && marked == null)
            {
                string code = item.Itemstack.Collectible.Code.ToString();
                int i = d.Crafting.FindIndex(c => c.Code == code && c.Size == item.Itemstack.StackSize);
                if (i >= 0) { d.Crafting.RemoveAt(i); ours = true; }
            }
            if (!ours) continue;
            taken.Add(item.Itemstack.Clone());
            item.Die(EnumDespawnReason.Removed);
        }
        d.Candidates.Clear();
        if (taken.Count == 0) return;
        if (d.Body != null && d.Body.Alive && !d.Body.Replaced)
        {
            sapi.Logger.Notification("[backrooms] corpse: {0} more stacks of {1}'s, dropped late, go into the body", taken.Count, d.Name);
            try { AddToBody(d, taken); }
            catch (Exception ex)
            {
                sapi.Logger.Error("[backrooms] corpse: could not add late drops to the body of {0}; dropping them where they fell: {1}", d.Name, ex);
                DropLoose(taken, d.Pos);
            }
            return;
        }
        d.Stacks.AddRange(taken);
        if (!d.Settled) Settle(d, stopping);
    }

    /// <summary>The window of a death is over.</summary>
    private void Expire(Dying d)
    {
        if (dying.TryGetValue(d.Uid, out Dying current) && current == d) dying.Remove(d.Uid);
    }

    /// <summary>The server is stopping: every death still collecting drops gets its body now (the chunks are still loaded).</summary>
    private void SettleAll()
    {
        foreach (Dying d in dying.Values.ToList()) Confirm(d, true);
    }

    /// <summary>The first drops are in: the corpse.</summary>
    private void Settle(Dying d, bool stopping = false)
    {
        if (d.Stacks.Count == 0 || d.Settled) return;
        d.Settled = true;
        int things = d.Stacks.Sum(s => s.StackSize);
        sapi.Logger.Notification("[backrooms] corpse: {0} died at {1:0.#} {2:0.#} {3:0.#} with {4} stacks ({5} things)", d.Name, d.Pos.X, d.Pos.Y, d.Pos.Z, d.Stacks.Count, things);
        Vec3d spot;
        try { spot = ResolveSpot(d.Pos, d.Uid); }
        catch (Exception ex)
        {
            sapi.Logger.Error("[backrooms] corpse: could not find the floor for {0}: {1}", d.Name, ex);
            spot = d.Pos.Clone();
        }
        MakeBody(d, spot, stopping ? LoadTries : 0, false);
    }

    private const int LoadTries = 6;

    private void DropLoose(IEnumerable<ItemStack> stacks, Vec3d at)
    {
        foreach (ItemStack stack in stacks)
        {
            Entity loose = sapi.World.SpawnItemEntity(stack, at.AddCopy(0, 0.3, 0));
            loose?.Attributes.SetInt("minsecondsToDespawn", 7 * 24 * 3600);
        }
    }

    /// <summary>
    /// Makes the body once the column it lies in is loaded: it is where someone has just died, but a last safe place may not be.
    /// The column is asked for again, up to <see cref="LoadTries"/> times; after that the body goes to the floor of the death
    /// itself (<paramref name="fallback"/>), which is loaded, and if even that is not, it waits for it. A body is never made in a
    /// column that is not loaded: it would not be saved.
    /// </summary>
    private void MakeBody(Dying d, Vec3d spot, int tries, bool fallback)
    {
        var at = new BlockPos((int)Math.Floor(spot.X), (int)Math.Floor(spot.Y), (int)Math.Floor(spot.Z), 0);
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(at) == null)
        {
            if (tries >= LoadTries && !fallback)
            {
                Vec3d near = null;
                try { near = FloorBelow(d.Pos.X, d.Pos.Y, d.Pos.Z, 48); } catch (Exception) { }
                near ??= d.Pos.Clone();
                sapi.Logger.Warning("[backrooms] corpse: the column of {0:0.#} {1:0.#} {2:0.#} would not load; {3}'s body goes to {4:0.#} {5:0.#} {6:0.#}", spot.X, spot.Y, spot.Z, d.Name, near.X, near.Y, near.Z);
                MakeBody(d, near, 0, true);
                return;
            }
            int attempt = tries;
            bool again = false;
            void Retry()
            {
                if (again) return;
                again = true;
                MakeBody(d, spot, attempt + 1, fallback);
            }
            sapi.WorldManager.LoadChunkColumnPriority(at.X / GlobalConstants.ChunkSize, at.Z / GlobalConstants.ChunkSize, new ChunkLoadOptions
            {
                OnLoaded = () => sapi.Event.EnqueueMainThreadTask(Retry, "corpse"),
            });
            // (If the load never reports, ask again)
            sapi.World.RegisterCallback(_ => Retry(), 5000);
            return;
        }
        EntityCorpse body;
        try
        {
            body = Spawn(d, spot);
            // (Spawning can be refused without an exception, e.g. in repair mode: then the body is not in the world)
            if (sapi.World.GetEntityById(body.EntityId) != body) throw new InvalidOperationException("the game did not take the body");
        }
        catch (Exception ex)
        {
            // (Whatever happens, nothing is lost: the stacks lie there as they would have)
            sapi.Logger.Error("[backrooms] corpse: could not make the body for {0}; dropping their things where they fell: {1}", d.Name, ex);
            DropLoose(d.Stacks, spot);
            return;
        }
        d.Body = body;

        // The body exists and holds the stacks; whatever goes wrong from here must not drop them a second time
        try
        {
            CorpseRecord r = Adopt(body);
            IServerPlayer owner = sapi.World.PlayerByUid(d.Uid) as IServerPlayer;
            if (owner != null) AddMarker(owner, r);
            MarkTold(d.Uid, r);
        }
        catch (Exception ex)
        {
            sapi.Logger.Error("[backrooms] corpse: the body of {0} is made, but its marker or message failed: {1}", d.Name, ex);
        }
    }

    /// <summary>
    /// Stacks dropped after the body was made: into its empty slots, else (its slots are fixed) into a new body of the right size
    /// that takes its place, with its record and marker.
    /// </summary>
    private void AddToBody(Dying d, List<ItemStack> extra)
    {
        EntityCorpse body = d.Body;
        EntityBehaviorCorpseContents contents = body.GetBehavior<EntityBehaviorCorpseContents>();
        var rest = new List<ItemStack>();
        foreach (ItemStack stack in extra)
        {
            ItemSlot free = contents.Inventory.FirstOrDefault(sl => sl.Empty);
            if (free == null) { rest.Add(stack); continue; }
            free.Itemstack = stack;
            free.MarkDirty();
        }
        contents.Store();
        if (rest.Count == 0) return;
        var all = contents.Inventory.Where(sl => !sl.Empty).Select(sl => sl.Itemstack.Clone()).ToList();
        all.AddRange(rest);
        d.Stacks.Clear();
        d.Stacks.AddRange(all);
        swapFrom = body;
        EntityCorpse bigger;
        try
        {
            bigger = Spawn(d, body.Pos.XYZ);
            if (sapi.World.GetEntityById(bigger.EntityId) != bigger) throw new InvalidOperationException("the game did not take the body");
        }
        catch (Exception)
        {
            // (The old body keeps what fits; the rest is dropped where it lies)
            DropLoose(rest, body.Pos.XYZ);
            return;
        }
        finally { swapFrom = null; }
        bigger.WatchedAttributes.SetDouble(EntityCorpse.DiedKey, body.DiedDays);
        Adopt(bigger);
        body.Replaced = true;
        body.Die(EnumDespawnReason.Removed);
        d.Body = bigger;
    }

    /// <summary>Puts a body down: the player's skin and clothes, and the stacks inside.</summary>
    private EntityCorpse Spawn(Dying d, Vec3d spot)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(FreshCode)) ?? throw new InvalidOperationException("no entity type " + FreshCode);
        Entity entity = sapi.World.ClassRegistry.CreateEntity(type);
        if (entity is not EntityCorpse body) throw new InvalidOperationException("entity " + FreshCode + " is not a corpse: " + entity?.GetType());
        body.Pos.SetPos(spot.X, spot.Y, spot.Z);
        body.Pos.Yaw = d.Yaw;
        ITreeAttribute wa = body.WatchedAttributes;
        wa.SetString(EntityCorpse.OwnerKey, d.Uid);
        wa.SetString(EntityCorpse.OwnerNameKey, d.Name);
        wa.SetDouble(EntityCorpse.DiedKey, sapi.World.Calendar.TotalDays);
        if (d.Skin != null) wa["skinConfig"] = d.Skin;
        if (d.Gear != null) wa["seraphinventory"] = d.Gear;
        wa[EntityBehaviorCorpseContents.TreeKey] = Pack(d.Stacks);
        sapi.World.SpawnEntity(body);
        sapi.Logger.Notification("[backrooms] corpse: #{0} of {1} lies at {2:0.#} {3:0.#} {4:0.#}", body.EntityId, d.Name, spot.X, spot.Y, spot.Z);
        return body;
    }

    /// <summary>The stacks as the tree a corpse's contents are kept in: a slot for each, in rows of four.</summary>
    private ITreeAttribute Pack(IReadOnlyList<ItemStack> stacks)
    {
        int slots = Math.Max(4, (stacks.Count + 3) / 4 * 4);
        var inventory = new InventoryGeneric(slots, "corpse-new", sapi, null);
        for (int i = 0; i < stacks.Count; i++) inventory[i].Itemstack = stacks[i];
        var tree = new TreeAttribute();
        inventory.ToTreeAttributes(tree);
        return tree;
    }

    // ================= Where it lies =================

    /// <summary>
    /// Where the body goes for a death at <paramref name="death"/>: on the floor under it (the nearest solid one, if they fell,
    /// were in the air or in water), else where they last stood on firm ground (a death in the void), else where they fell.
    /// </summary>
    private Vec3d ResolveSpot(Vec3d death, string uid)
    {
        Vec3d floor = FloorBelow(death.X, death.Y, death.Z, 48);
        if (floor != null) return floor;
        if (lastSafe.TryGetValue(uid, out Vec3d safe))
        {
            sapi.Logger.Notification("[backrooms] corpse: no floor under {0:0.#} {1:0.#} {2:0.#}; using the last firm ground, {3:0.#} {4:0.#} {5:0.#}", death.X, death.Y, death.Z, safe.X, safe.Y, safe.Z);
            return safe.Clone();
        }
        sapi.Logger.Warning("[backrooms] corpse: no floor and no firm ground for a death at {0:0.#} {1:0.#} {2:0.#}", death.X, death.Y, death.Z);
        return death.Clone();
    }

    /// <summary>How high the top of the block at a position is (0..1 or more), or 0 for no collision there.</summary>
    private double TopOf(IBlockAccessor ba, BlockPos pos)
    {
        Block block = ba.GetBlock(pos);
        if (block == null || block.Id == 0) return 0;
        Cuboidf[] boxes = block.GetCollisionBoxes(ba, pos);
        if (boxes == null || boxes.Length == 0) return 0;
        double top = 0;
        foreach (Cuboidf box in boxes) top = Math.Max(top, box.Y2);
        return top;
    }

    /// <summary>
    /// The top of the nearest floor at or below a point (looking up first if the point is inside something), or null where
    /// there is none within <paramref name="maxDown"/> blocks or the column is not loaded.
    /// </summary>
    public Vec3d FloorBelow(double x, double y, double z, int maxDown)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int bx = (int)Math.Floor(x), bz = (int)Math.Floor(z), by = (int)Math.Floor(y + 0.001);
        var pos = new BlockPos(bx, by, bz, 0);
        if (ba.GetChunkAtBlockPos(pos) == null) return null;
        int start = by;
        for (int up = 0; up < 6; up++)
        {
            pos.Y = start;
            double top = TopOf(ba, pos);
            if (top <= 0) break;
            // (Standing on it: the point is at or above its top)
            if (up == 0 && y - by >= top - 0.02) break;
            start++;
        }
        for (int down = 0; down <= maxDown; down++)
        {
            int yy = start - down;
            if (yy < 0) break;
            pos.Y = yy;
            double top = TopOf(ba, pos);
            if (top > 0) return new Vec3d(x, yy + top, z);
        }
        return null;
    }

    private void TrackSafePlaces()
    {
        foreach (IPlayer p in sapi.World.AllOnlinePlayers)
        {
            EntityPlayer e = p.Entity;
            if (e == null || !e.Alive || !e.OnGround || e.FeetInLiquid || e.Swimming) continue;
            lastSafe[p.PlayerUID] = e.Pos.XYZ.Clone();
        }
    }

    // ================= The bodies =================

    /// <summary>A body has come into the world (made, or loaded with its chunk): its record, made if it has none.</summary>
    public CorpseRecord Adopt(EntityCorpse body)
    {
        CorpseRecord r = records.FirstOrDefault(c => c.EntityId == body.EntityId);
        if (r == null && swapFrom != null)
        {
            // (Its bones, replacing it: the same record, and the same marker)
            r = records.FirstOrDefault(c => c.EntityId == swapFrom.EntityId);
            if (r != null) r.EntityId = body.EntityId;
        }
        if (r == null)
        {
            r = new CorpseRecord { EntityId = body.EntityId };
            records.Add(r);
            dirty = true;
        }
        string owner = body.OwnerUid, name = body.OwnerName;
        if (r.Owner != owner || r.OwnerName != name || r.Bones != body.Bones || r.DiedDays != body.DiedDays
            || Math.Abs(r.X - body.Pos.X) + Math.Abs(r.Y - body.Pos.Y) + Math.Abs(r.Z - body.Pos.Z) > 0.01)
        {
            r.Owner = owner;
            r.OwnerName = name;
            r.Bones = body.Bones;
            r.DiedDays = body.DiedDays;
            r.X = body.Pos.X;
            r.Y = body.Pos.Y;
            r.Z = body.Pos.Z;
            dirty = true;
        }
        return r;
    }

    /// <summary>A body has gone for good (emptied, or removed): its record and its marker go too.</summary>
    public void Forget(EntityCorpse body)
    {
        CorpseRecord r = records.FirstOrDefault(c => c.EntityId == body.EntityId);
        if (r == null) return;
        records.Remove(r);
        dirty = true;
        RemoveMarker(r);
        sapi.Logger.Notification("[backrooms] corpse: #{0} of {1} is gone", r.EntityId, r.OwnerName);
    }

    /// <summary>Every few seconds, for a body in a loaded chunk: crumble if empty, turn to bones when old, settle if the floor went.</summary>
    public void Look(EntityCorpse body)
    {
        if (!body.Alive || body.Replaced) return;
        EntityBehaviorCorpseContents contents = body.GetBehavior<EntityBehaviorCorpseContents>();
        if (contents != null && contents.Count().Stacks == 0)
        {
            contents.Crumble();
            return;
        }
        if (!body.Bones && sapi.World.Calendar.TotalDays - body.DiedDays >= BonesAfterDays)
        {
            TurnToBones(body);
            return;
        }
        // (If what it lay on has been dug away, it comes down to the next floor)
        IBlockAccessor ba = sapi.World.BlockAccessor;
        var below = new BlockPos((int)Math.Floor(body.Pos.X), (int)Math.Floor(body.Pos.Y - 0.05), (int)Math.Floor(body.Pos.Z), 0);
        if (ba.GetChunkAtBlockPos(below) == null || TopOf(ba, below) > 0) return;
        Vec3d floor = FloorBelow(body.Pos.X, body.Pos.Y - 0.05, body.Pos.Z, 64);
        if (floor == null || Math.Abs(floor.Y - body.Pos.Y) < 0.05) return;
        body.TeleportToDouble(floor.X, floor.Y, floor.Z);
        Adopt(body);
    }

    /// <summary>The body is bones now: a skeleton entity of the same contents, in its place.</summary>
    public bool TurnToBones(EntityCorpse body)
    {
        if (body.Bones || body.Replaced) return false;
        body.GetBehavior<EntityBehaviorCorpseContents>()?.Store();
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(BonesCode));
        if (type == null) return false;
        Entity entity = sapi.World.ClassRegistry.CreateEntity(type);
        if (entity is not EntityCorpse bones) return false;
        bones.Pos.SetPos(body.Pos.X, body.Pos.Y, body.Pos.Z);
        bones.Pos.Yaw = body.Pos.Yaw;
        ITreeAttribute wa = bones.WatchedAttributes;
        wa.SetString(EntityCorpse.OwnerKey, body.OwnerUid);
        wa.SetString(EntityCorpse.OwnerNameKey, body.OwnerName);
        wa.SetDouble(EntityCorpse.DiedKey, body.DiedDays);
        ITreeAttribute contents = body.WatchedAttributes.GetTreeAttribute(EntityBehaviorCorpseContents.TreeKey);
        if (contents != null) wa[EntityBehaviorCorpseContents.TreeKey] = contents.Clone();
        body.Replaced = true;
        swapFrom = body;
        try { sapi.World.SpawnEntity(bones); }
        catch (Exception ex)
        {
            body.Replaced = false;
            sapi.Logger.Error("[backrooms] corpse: could not turn #{0} to bones: {1}", body.EntityId, ex);
            return false;
        }
        finally { swapFrom = null; }
        body.Die(EnumDespawnReason.Removed);
        sapi.Logger.Notification("[backrooms] corpse: #{0} of {1} is bones now (#{2})", body.EntityId, body.OwnerName, bones.EntityId);
        return true;
    }

    // ================= The map =================

    private WaypointMapLayer Layer() => sapi.ModLoader.GetModSystem<WorldMapManager>()?.MapLayers.OfType<WaypointMapLayer>().FirstOrDefault();

    private static Waypoint Find(WaypointMapLayer layer, string guid) => guid == null ? null : layer.Waypoints.FirstOrDefault(w => w.Guid == guid);

    private void Resend(WaypointMapLayer layer, string uid)
    {
        if (sapi.World.PlayerByUid(uid) is not IServerPlayer player) return;
        try { ResendWaypoints?.Invoke(layer, new object[] { player }); }
        catch (Exception ex) { sapi.Logger.Warning("[backrooms] corpse: could not resend {0}'s waypoints: {1}", player.PlayerName, ex.Message); }
    }

    /// <summary>
    /// A marker for a new corpse on its owner's map, pinned, and the owner's earlier ones unpinned (kept: they stay on the map).
    /// Where the world's map setting makes no waypoints there is none (the player is told which way instead).
    /// </summary>
    private void AddMarker(IServerPlayer owner, CorpseRecord r)
    {
        if (!MapSetting.Waypoints(sapi.World.Config)) return;
        WaypointMapLayer layer = Layer();
        if (layer == null) return;
        foreach (CorpseRecord other in records)
            if (other != r && other.Owner == r.Owner && Find(layer, other.WaypointGuid) is { } older) older.Pinned = false;
        string level = MapMarks.LevelName(layout, r.X, r.Z);
        int day = (int)Math.Floor(sapi.World.Calendar.ElapsedDays) + 1;
        var waypoint = new Waypoint
        {
            Position = new Vec3d(r.X, r.Y, r.Z),
            Title = Say.T(owner, "backrooms:corpse-waypoint", level, day),
            Icon = "skull_and_crossbones",
            Color = ColorUtil.ColorFromRgba(214, 96, 84, 255),
            OwningPlayerUid = owner.PlayerUID,
            Pinned = true,
            Guid = Guid.NewGuid().ToString(),
        };
        layer.AddWaypoint(waypoint, owner);
        r.WaypointGuid = waypoint.Guid;
        dirty = true;
    }

    /// <summary>The marker of a corpse that is gone; the owner's newest remaining one is pinned in its place, if it was the pinned one.</summary>
    private void RemoveMarker(CorpseRecord r)
    {
        WaypointMapLayer layer = Layer();
        Waypoint mine = layer == null ? null : Find(layer, r.WaypointGuid);
        if (mine == null) return;
        layer.Waypoints.Remove(mine);
        if (mine.Pinned)
        {
            CorpseRecord next = records.Where(c => c.Owner == r.Owner && Find(layer, c.WaypointGuid) != null).OrderByDescending(c => c.DiedDays).FirstOrDefault();
            if (next != null) Find(layer, next.WaypointGuid).Pinned = true;
        }
        Resend(layer, r.Owner);
    }

    /// <summary>A player's map when they join: a marker for any corpse of theirs that has none (made while they were not there).</summary>
    private void OnPlayerNowPlaying(IServerPlayer player)
    {
        if (!MapSetting.Waypoints(sapi.World.Config)) return;
        foreach (CorpseRecord r in records.Where(c => c.Owner == player.PlayerUID && c.WaypointGuid == null).OrderBy(c => c.DiedDays).ToList())
            AddMarker(player, r);
    }

    private void OnPlayerDeath(IServerPlayer player, DamageSource source)
    {
        // Vanilla's "You died here" is for a death that leaves nothing; with a body there is the body's marker
        sapi.World.RegisterCallback(_ =>
        {
            if (toldAt.TryGetValue(player.PlayerUID, out long ms) && sapi.World.ElapsedMilliseconds - ms < 30000) RemoveVanillaMarker(player.PlayerUID);
        }, 2600);
    }

    private void RemoveVanillaMarker(string uid)
    {
        WaypointMapLayer layer = Layer();
        if (layer == null) return;
        string title = Lang.Get("You died here");
        if (layer.Waypoints.RemoveAll(w => w.OwningPlayerUid == uid && w.Icon == "gravestone" && w.Title == title) > 0) Resend(layer, uid);
    }

    // ================= Telling the player =================

    private void MarkTold(string uid, CorpseRecord r)
    {
        toldAt[uid] = sapi.World.ElapsedMilliseconds;
        if (sapi.World.PlayerByUid(uid) is IServerPlayer { Entity: { Alive: true } } already) Tell(already, r);
        else toTell[uid] = r;
    }

    private void OnPlayerRespawn(IServerPlayer player)
    {
        if (toTell.Remove(player.PlayerUID, out CorpseRecord r)) Tell(player, r);
    }

    private void Tell(IServerPlayer player, CorpseRecord r)
    {
        string text;
        if (r.WaypointGuid != null) text = Say.T(player, "backrooms:corpse-waits");
        else
        {
            double dx = r.X - player.Entity.Pos.X, dz = r.Z - player.Entity.Pos.Z;
            text = Say.T(player, "backrooms:corpse-waits-nomap", Say.T(player, "backrooms:dir-" + MarkResolver.Direction(dx, dz)), MarkResolver.Paces(dx, dz));
        }
        player.SendMessage(GlobalConstants.GeneralChatGroup, text, EnumChatType.Notification);
    }

    // ================= Dev commands (/backrooms corpse) =================

    /// <summary>The test stacks <c>corpse make</c> and <c>corpse simdeath</c> use: a bag with something in it among them.</summary>
    private List<ItemStack> TestStacks()
    {
        var stacks = new List<ItemStack>();
        foreach ((string code, int quantity) in new[] { ("backrooms:almondwater", 3), ("backrooms:cannedbeans", 2), ("game:torch-basic-lit-up", 5), ("backrooms:carpetbag", 1), ("backrooms:chalk", 1) })
        {
            var location = new AssetLocation(code);
            CollectibleObject collectible = (CollectibleObject)sapi.World.GetItem(location) ?? sapi.World.GetBlock(location);
            if (collectible != null) stacks.Add(new ItemStack(collectible, quantity));
        }
        return stacks;
    }

    public string Debug(Caller caller, string action, string arg)
    {
        if (!active) return "Not a Backrooms world";
        IServerPlayer player = caller.Player as IServerPlayer;
        switch ((action ?? "").Trim().ToLowerInvariant())
        {
            case "":
            case "list":
            {
                if (records.Count == 0) return "No corpses";
                var text = new StringBuilder($"{records.Count} corpses (bones after {BonesAfterDays} days):");
                double now = sapi.World.Calendar.TotalDays;
                foreach (CorpseRecord r in records.OrderBy(c => c.DiedDays))
                {
                    var body = sapi.World.GetEntityById(r.EntityId) as EntityCorpse;
                    string contents = body?.GetBehavior<EntityBehaviorCorpseContents>() is { } c ? $"{c.Count().Stacks} stacks, {c.Count().Things} things" : "not loaded";
                    text.Append($"\n#{r.EntityId} {(r.Bones ? "bones" : "body")} of {r.OwnerName} ({r.Owner}) at {r.X:0.#} {r.Y:0.#} {r.Z:0.#}, {now - r.DiedDays:0.##} days old, {(r.WaypointGuid != null ? "marked" : "no marker")}, {contents}");
                }
                return text.ToString();
            }
            case "make":
            {
                // A corpse of the caller's (or of nobody, from the console) with the test stacks, at their feet or at the spawn
                Vec3d at = player?.Entity?.Pos.XYZ.Clone() ?? DefaultSpot();
                var d = new Dying
                {
                    Uid = player?.PlayerUID ?? "test", Name = player?.PlayerName ?? "Test Pilgrim", Ms = sapi.World.ElapsedMilliseconds, Pos = at,
                    Yaw = player?.Entity?.Pos.Yaw ?? 0, Skin = player?.Entity?.WatchedAttributes.GetTreeAttribute("skinConfig")?.Clone() as ITreeAttribute,
                    Gear = player == null ? null : CopyClothes(player),
                };
                d.Stacks.AddRange(TestStacks());
                MakeBody(d, ResolveSpot(at, d.Uid), 0, false);
                return $"A corpse of {d.Name} with {d.Stacks.Count} stacks at {at.X:0.#} {at.Y:0.#} {at.Z:0.#}";
            }
            case "simdeath":
            {
                // A death with no player to die: the drops of "Test Pilgrim" are marked as the game marks them (a tick after they
                // spawn), a crafting-grid one is not, and there are strangers' items too: one unmarked beside the body, one marked
                // as another player's. One more drop comes late, after the body is made (arg "late" seconds, default 5)
                Vec3d at = player?.Entity?.Pos.XYZ.Clone() ?? DefaultSpot();
                var d = new Dying { Uid = "simdeath", Name = "Test Pilgrim", Ms = sapi.World.ElapsedMilliseconds, Pos = at, Yaw = 1f };
                dying[d.Uid] = d;
                sapi.World.RegisterCallback(_ => Expire(d), CatchMs + 100);
                List<ItemStack> stacks = TestStacks();
                ItemStack grid = stacks[^1];
                d.Crafting.Add((grid.Collectible.Code.ToString(), grid.StackSize));
                foreach (ItemStack stack in stacks)
                {
                    Entity drop = sapi.World.SpawnItemEntity(stack.Clone(), at.Clone());
                    if (stack != grid) drop.WatchedAttributes.SetString("byPlayerUid", d.Uid);
                }
                sapi.World.SpawnItemEntity(new ItemStack(sapi.World.GetItem(new AssetLocation("backrooms:chalk")), 7), at.AddCopy(0.5, 0, 0));
                Entity theirs = sapi.World.SpawnItemEntity(new ItemStack(sapi.World.GetItem(new AssetLocation("backrooms:chalk")), 9), at.AddCopy(0, 0, 0.5));
                theirs.WatchedAttributes.SetString("byPlayerUid", "someone-else");
                sapi.World.SpawnItemEntity(stacks[0].Clone(), at.AddCopy(6, 0, 0));
                int late = int.TryParse((arg ?? "").Trim(), out int seconds) ? seconds : 5;
                sapi.World.RegisterCallback(_ =>
                {
                    Entity drop = sapi.World.SpawnItemEntity(new ItemStack(sapi.World.GetItem(new AssetLocation("backrooms:chalk")), 3), at.Clone());
                    drop.WatchedAttributes.SetString("byPlayerUid", d.Uid);
                    // ...and enough more to fill the body's slots, to test it growing
                    for (int i = 0; i < 8; i++)
                    {
                        Entity more = sapi.World.SpawnItemEntity(new ItemStack(sapi.World.GetItem(new AssetLocation("game:stick")), i + 1), at.Clone());
                        more.WatchedAttributes.SetString("byPlayerUid", d.Uid);
                    }
                }, late * 1000);
                return $"Dropped {stacks.Count} stacks for a death at {at.X:0.#} {at.Y:0.#} {at.Z:0.#} (one unmarked, as from a crafting grid), two strangers' chalk beside it and one stack 6 blocks away that should stay; 9 more come in {late} s";
            }
            case "far":
            {
                // A body 4000 blocks from the death, in a column that is not loaded (the last-safe-place case): it is loaded first
                Vec3d at = DefaultSpot();
                var d = new Dying { Uid = "far", Name = "Far Pilgrim", Ms = sapi.World.ElapsedMilliseconds, Pos = at, Yaw = 2f, Settled = true };
                d.Stacks.AddRange(TestStacks());
                Vec3d spot = at.AddCopy(4000, 0, 0);
                MakeBody(d, spot, 0, false);
                return $"A body for {d.Name} asked for at {spot.X:0.#} {spot.Y:0.#} {spot.Z:0.#}; see the log";
            }
            case "age":
            {
                // Makes a body old enough to be bones (default: the newest), and looks at it now
                CorpseRecord r = records.OrderByDescending(c => c.DiedDays).FirstOrDefault(c => string.IsNullOrWhiteSpace(arg) || arg.Trim() == c.EntityId.ToString());
                if (r == null || sapi.World.GetEntityById(r.EntityId) is not EntityCorpse body) return "No such corpse in a loaded chunk";
                body.WatchedAttributes.SetDouble(EntityCorpse.DiedKey, sapi.World.Calendar.TotalDays - BonesAfterDays - 0.1);
                Adopt(body);
                bool done = TurnToBones(body);
                return done ? $"#{r.EntityId} of {r.OwnerName} is bones" : $"#{r.EntityId} could not be turned to bones";
            }
            case "clear":
            {
                int n = 0;
                foreach (CorpseRecord r in records.ToList())
                    if (sapi.World.GetEntityById(r.EntityId) is EntityCorpse body) { body.Die(EnumDespawnReason.Removed); n++; }
                    else Forget(r);
                return $"Removed {n} loaded corpses, and the records of the others";
            }
            default:
                return "Usage: /backrooms corpse [list | make | simdeath [late seconds] | far | age [id] | clear]";
        }
    }

    /// <summary>A record whose body is not loaded (or is gone): forgotten along with its marker.</summary>
    private void Forget(CorpseRecord r)
    {
        records.Remove(r);
        dirty = true;
        RemoveMarker(r);
    }

    private Vec3d DefaultSpot()
    {
        PlayerSpawnPos spawn = sapi.WorldManager.SaveGame.DefaultSpawn;
        int floor = BackroomsWorld.CreateGeometry(sapi.World).FloorY;
        return new Vec3d((spawn?.x ?? 0) + 0.5, spawn?.y ?? floor + 1, (spawn?.z ?? 0) + 0.5);
    }
}
