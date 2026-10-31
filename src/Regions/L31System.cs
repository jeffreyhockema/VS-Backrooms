using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Zone = Backrooms.Worldgen.WorldLayout.L31Zone;

namespace Backrooms.Regions;

/// <summary>
/// Level 31, "Roller Rink" (experimental): its people and its rules (docs/design/experimental-levels/31-plan.md, detail
/// pass). This file is the level's own.
/// <list type="bullet">
/// <item><b>The staff</b> stand where the layout marks them (<see cref="WorldLayout.L31Props.StaffSpot"/>) while anyone is
/// near, and are never kept with the world: the <b>Coach</b> behind each Skate Rental counter (he talks: the vanilla
/// dialogue in config/dialogue/l31-coach.json, which gives the skates and remembers your name), a Faceling behind each
/// food court's counter and one at each DJ station. None can be hurt; none is ever hostile.</item>
/// <item><b>Free food</b> (Wikidot): the food court's server hands a player a slice of pizza, wings or a foot-long hot dog,
/// and often a cup of Almond Water, once every <see cref="ServeHours"/> in-game hours. Food or anything else left lying
/// on a food court's floor is cleaned up, begrudgingly, and whoever dropped it is refused for a day.</item>
/// <item><b>Skates</b> (Fandom): worn on the feet in this level, the Coach's skates make their wearer quicker on its boards,
/// tiles and concrete (not on carpet).</item>
/// <item><b>Paranoia</b> (Fandom): now and then a still black figure stands at the edge of a dark room some way off, and is
/// gone when the player comes close. Nothing else: it has no AI and cannot be touched.</item>
/// <item><b>Do not stay</b> (Wikidot): after a day and a half in the level, and every half day after, the Coach finds the
/// player by name and tells them it is time to go.</item>
/// <item>The arcade's <b>green-card dispenser</b> drops a green card for anyone without one.</item>
/// </list>
/// </summary>
public class L31System : ModSystem
{
    private const int StaffNear = 40, StaffGone = 96;
    /// <summary>How often the server feeds a player (in-game hours), and how long it refuses a litterer.</summary>
    private const double ServeHours = 1.5, RefuseHours = 24;
    /// <summary>How long in the level before the Coach says it is time to go, and how often after (in-game hours).</summary>
    private const double StayHours = 36, StayAgainHours = 12;
    private const string SkatesKey = "backrooms-l31skates";
    private const float SkatesBonus = 0.3f;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private long tick, slowTick;
    private EntityProperties coachType, staffType, shadowType;
    private readonly Dictionary<(int X, int Z), Entity> staff = new();
    private readonly Dictionary<string, double> nextServe = new(), refusedUntil = new(), arrived = new(), nextStayWord = new();
    private readonly Dictionary<string, (Entity Shadow, long Gone)> shadows = new();
    private readonly Dictionary<long, long> litterSeen = new();
    private readonly HashSet<string> skating = new();
    private readonly Random rand = new();

    public override bool ShouldLoad(EnumAppSide side) => true;

    // (After BackroomsModSystem)
    public override double ExecuteOrder() => 1.3;

    public override void Start(ICoreAPI api)
    {
        api.RegisterEntity("BackroomsL31Staff", typeof(EntityL31Staff));
        api.RegisterBlockBehaviorClass("BackroomsL31Dispenser", typeof(BlockBehaviorL31Dispenser));
    }

    public override void AssetsFinalize(ICoreAPI api)
    {
        foreach (Block block in api.World.Blocks)
            if (block?.Code?.Domain == "backrooms" && block.Code.Path.StartsWith("l31-dispenser-", StringComparison.Ordinal))
                BehaviorInjection.Add(block, new BlockBehaviorL31Dispenser(block));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            coachType = api.World.GetEntityType(new AssetLocation("backrooms:l31-coach"));
            staffType = api.World.GetEntityType(new AssetLocation("backrooms:l31-staff"));
            shadowType = api.World.GetEntityType(new AssetLocation("backrooms:l31-shadow"));
            tick = api.Event.RegisterGameTickListener(OnTick, 1000, 700);
            slowTick = api.Event.RegisterGameTickListener(OnSlowTick, 3000, 1300);
            api.Event.PlayerDisconnect += OnPlayerDisconnect;
        });
    }

    public override void Dispose()
    {
        if (sapi == null) return;
        if (tick != 0) sapi.Event.UnregisterGameTickListener(tick);
        if (slowTick != 0) sapi.Event.UnregisterGameTickListener(slowTick);
        sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
    }

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        arrived.Remove(player.PlayerUID);
        skating.Remove(player.PlayerUID);
        if (shadows.Remove(player.PlayerUID, out var s) && s.Shadow.Alive) s.Shadow.Die(EnumDespawnReason.Removed);
    }

    private double Hours => sapi.World.Calendar.TotalHours;

    private List<IServerPlayer> PlayersHere() => sapi.World.AllOnlinePlayers.OfType<IServerPlayer>()
        .Where(p => p.Entity is { Alive: true } && p.ConnectionState == EnumClientState.Playing && In31(p.Entity.Pos)).ToList();

    private bool In31(EntityPos pos) => layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(pos.X)), WorldLayout.MacroOf((int)Math.Floor(pos.Z))) == WorldLayout.Level31;

    private Tile TileAt(double x, double z) => layout.TileAt((int)Math.Floor(x), (int)Math.Floor(z));

    private static void Say(IServerPlayer player, string key, params object[] args) =>
        player.SendMessage(GlobalConstants.GeneralChatGroup, Backrooms.Say.T(player, key, args), EnumChatType.Notification);

    // ================= Every second: skates, how long they have stayed =================

    private void OnTick(float dt)
    {
        foreach (IServerPlayer player in sapi.World.AllOnlinePlayers.OfType<IServerPlayer>())
        {
            EntityPlayer e = player.Entity;
            if (e == null) continue;
            bool here = e.Alive && In31(e.Pos);
            Skates(player, e, here);
            if (!here)
            {
                arrived.Remove(player.PlayerUID);
                continue;
            }
            if (!arrived.TryGetValue(player.PlayerUID, out double since)) arrived[player.PlayerUID] = since = Hours;
            if (Hours - since >= StayHours && Hours >= nextStayWord.GetValueOrDefault(player.PlayerUID))
            {
                nextStayWord[player.PlayerUID] = Hours + StayAgainHours;
                Say(player, rand.Next(2) == 0 ? "backrooms:l31-coach-stay" : "backrooms:l31-coach-stay-2", player.PlayerName);
            }
        }
    }

    /// <summary>Quicker on smooth floors, in this level only, while the Coach's skates are on the feet.</summary>
    private void Skates(IServerPlayer player, EntityPlayer e, bool here)
    {
        bool on = false;
        if (here && e.OnGround)
        {
            IInventory gear = player.InventoryManager?.GetOwnInventory(GlobalConstants.characterInvClassName);
            ItemSlot feet = gear?.Count > (int)EnumCharacterDressType.Foot ? gear[(int)EnumCharacterDressType.Foot] : null;
            if (feet?.Itemstack?.Collectible?.Attributes?["l31skates"].AsBool(false) == true)
                on = TileAt(e.Pos.X, e.Pos.Z).Zone is not ((byte)Zone.Hall or (byte)Zone.Lobby or (byte)Zone.Skirt or (byte)Zone.Lounge
                    or (byte)Zone.CarpetRoom or (byte)Zone.Cinema or 0);
        }
        else if (here && skating.Contains(player.PlayerUID)) return; // (in the air: as they were)
        if (on == skating.Contains(player.PlayerUID)) return;
        if (on)
        {
            skating.Add(player.PlayerUID);
            e.Stats.Set("walkspeed", SkatesKey, SkatesBonus, false);
        }
        else
        {
            skating.Remove(player.PlayerUID);
            e.Stats.Remove("walkspeed", SkatesKey);
        }
    }

    // ================= Every three seconds: the staff, the litter, the shadows =================

    private void OnSlowTick(float dt)
    {
        if (layout == null) return;
        var players = PlayersHere();
        KeepStaff(players);
        Litter(players);
        Shadows(players);
    }

    /// <summary>Where the staff stand near a point: the layout's marks, kept per 32-block cell (the layout never changes).</summary>
    private IEnumerable<(int X, int Z, ArchPier Facing, byte Role)> SpotsNear(int px, int pz)
    {
        int x0 = (int)Math.Floor((px - StaffNear) / 32.0), z0 = (int)Math.Floor((pz - StaffNear) / 32.0);
        for (int cz = z0; cz * 32 <= pz + StaffNear; cz++)
            for (int cx = x0; cx * 32 <= px + StaffNear; cx++)
                foreach (var spot in SpotsOfCell(cx, cz))
                    if (Math.Abs(spot.X - px) <= StaffNear && Math.Abs(spot.Z - pz) <= StaffNear) yield return spot;
    }

    private readonly Dictionary<(int, int), List<(int X, int Z, ArchPier Facing, byte Role)>> spotCells = new();

    private List<(int X, int Z, ArchPier Facing, byte Role)> SpotsOfCell(int cx, int cz)
    {
        if (spotCells.TryGetValue((cx, cz), out var spots)) return spots;
        spots = new();
        for (int z = cz * 32; z < (cz + 1) * 32; z++)
            for (int x = cx * 32; x < (cx + 1) * 32; x++)
            {
                Tile t = layout.TileAt(x, z);
                if (t.Level == WorldLayout.Level31 && t.Kind == TileKind.Floor && t.Variant == WorldLayout.L31Props.StaffSpot) spots.Add((x, z, t.Pier, t.Stack));
            }
        spotCells[(cx, cz)] = spots;
        return spots;
    }

    private void KeepStaff(List<IServerPlayer> players)
    {
        foreach (var key in staff.Keys.ToList())
        {
            Entity e = staff[key];
            bool near = players.Any(p => Sq(p.Entity.Pos.X - key.X - 0.5, p.Entity.Pos.Z - key.Z - 0.5) < StaffGone * StaffGone);
            if (e.Alive && near && sapi.World.GetEntityById(e.EntityId) != null) continue;
            if (e.Alive) e.Die(EnumDespawnReason.Removed);
            staff.Remove(key);
        }
        int floor = geometry.FloorFor(WorldLayout.Level31);
        foreach (IServerPlayer player in players)
            foreach (var (x, z, facing, role) in SpotsNear((int)Math.Floor(player.Entity.Pos.X), (int)Math.Floor(player.Entity.Pos.Z)))
            {
                if (staff.ContainsKey((x, z)) || sapi.World.BlockAccessor.GetChunkAtBlockPos(x, floor + 1, z) == null) continue;
                EntityProperties type = role == WorldLayout.L31Coach ? coachType : staffType;
                if (type == null) continue;
                Entity person = sapi.World.ClassRegistry.CreateEntity(type);
                person.Pos.SetPos(x + 0.5, floor + 1, z + 0.5);
                person.Pos.Yaw = Yaw(facing);
                if (role != WorldLayout.L31Coach) person.WatchedAttributes.SetInt("textureIndex", role == WorldLayout.L31Dj ? 1 : 0);
                person.WatchedAttributes.SetInt("l31role", role);
                sapi.World.SpawnEntity(person);
                staff[(x, z)] = person;
            }
    }

    private static float Yaw(ArchPier facing) => facing switch
    {
        ArchPier.North => GameMath.PI, ArchPier.East => GameMath.PIHALF, ArchPier.West => -GameMath.PIHALF, _ => 0,
    };

    private static double Sq(double dx, double dz) => dx * dx + dz * dz;

    /// <summary>Asked: the server feeds you (or will not), the DJ nods along; the Coach talks through his dialogue.</summary>
    public void Interact(IServerPlayer player, Entity person)
    {
        int role = person.WatchedAttributes.GetInt("l31role", -1);
        if (role == WorldLayout.L31Server) Serve(player, person);
        else if (role == WorldLayout.L31Dj)
        {
            person.AnimManager?.StartAnimation("nod");
            Say(player, "backrooms:l31-dj-" + (1 + rand.Next(3)));
        }
    }

    public void Struck(IServerPlayer player, Entity person)
    {
        int role = person.WatchedAttributes.GetInt("l31role", -1);
        Say(player, role == WorldLayout.L31Coach ? "backrooms:l31-coach-struck" : "backrooms:l31-server-struck");
    }

    private static readonly string[] Dishes = { "pizza", "pepperoni", "wings", "hotdog" };

    private void Serve(IServerPlayer player, Entity server)
    {
        string uid = player.PlayerUID;
        if (refusedUntil.TryGetValue(uid, out double until) && Hours < until)
        {
            Say(player, "backrooms:l31-server-refuse");
            return;
        }
        if (nextServe.TryGetValue(uid, out double next) && Hours < next)
        {
            Say(player, rand.Next(3) == 0 ? "backrooms:l31-server-question" : "backrooms:l31-server-wait");
            return;
        }
        nextServe[uid] = Hours + ServeHours;
        server.AnimManager?.StartAnimation("nod");
        Give(player, "backrooms:l31-food-" + Dishes[rand.Next(Dishes.Length)], server);
        Say(player, "backrooms:l31-server-serve-" + (1 + rand.Next(3)));
        if (rand.NextDouble() < 0.6)
        {
            Give(player, "backrooms:almondwater", server);
            Say(player, "backrooms:l31-server-water");
        }
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/player/clayform"), server, null, true, 12);
    }

    private void Give(IServerPlayer player, string code, Entity from)
    {
        Item item = sapi.World.GetItem(new AssetLocation(code));
        if (item == null) return;
        var stack = new ItemStack(item);
        if (!player.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true) || stack.StackSize > 0)
            sapi.World.SpawnItemEntity(stack, from.Pos.XYZ.Add(0, 1.2, 0));
    }

    /// <summary>
    /// What lies on a food court's floor for more than a few seconds is swept up by the Faceling behind the counter, and
    /// whoever dropped it (or, not knowing, whoever is nearest) gets nothing more for a day.
    /// </summary>
    private void Litter(List<IServerPlayer> players)
    {
        long now = sapi.World.ElapsedMilliseconds;
        var seen = new HashSet<long>();
        foreach (IServerPlayer player in players)
        {
            if (TileAt(player.Entity.Pos.X, player.Entity.Pos.Z).Zone != (byte)Zone.Snack) continue;
            foreach (Entity e in sapi.World.GetEntitiesAround(player.Entity.Pos.XYZ, 20, 4, e => e is EntityItem && e.Alive))
            {
                if (TileAt(e.Pos.X, e.Pos.Z).Zone != (byte)Zone.Snack) continue;
                seen.Add(e.EntityId);
                if (!litterSeen.TryGetValue(e.EntityId, out long first)) { litterSeen[e.EntityId] = now; continue; }
                if (now - first < 9000) continue;
                string by = ((EntityItem)e).ByPlayerUid;
                IServerPlayer culprit = (by != null ? sapi.World.PlayerByUid(by) as IServerPlayer : null)
                    ?? players.OrderBy(p => p.Entity.Pos.SquareDistanceTo(e.Pos.XYZ)).First();
                refusedUntil[culprit.PlayerUID] = Hours + RefuseHours;
                foreach (IServerPlayer p in players)
                    if (p.Entity.Pos.SquareDistanceTo(e.Pos.XYZ) < 24 * 24) Say(p, "backrooms:l31-server-clean", culprit.PlayerName);
                e.Die(EnumDespawnReason.Removed);
                litterSeen.Remove(e.EntityId);
            }
        }
        foreach (long id in litterSeen.Keys.Where(id => !seen.Contains(id)).ToList()) litterSeen.Remove(id);
    }

    // ================= Paranoia =================

    private static bool DarkZone(byte zone) => zone is (byte)Zone.Cinema or (byte)Zone.Empty or (byte)Zone.CarpetRoom or (byte)Zone.Hvac
        or (byte)Zone.Store or (byte)Zone.Corridor;

    private void Shadows(List<IServerPlayer> players)
    {
        long now = sapi.World.ElapsedMilliseconds;
        foreach (var uid in shadows.Keys.ToList())
        {
            var (shadow, gone) = shadows[uid];
            IServerPlayer owner = players.FirstOrDefault(p => p.PlayerUID == uid);
            bool close = owner == null || shadow.Pos.SquareDistanceTo(owner.Entity.Pos.XYZ) < 9 * 9;
            if (shadow.Alive && !close && now < gone && sapi.World.GetEntityById(shadow.EntityId) != null) continue;
            if (shadow.Alive) shadow.Die(EnumDespawnReason.Removed);
            shadows.Remove(uid);
        }
        if (shadowType == null) return;
        int floor = geometry.FloorFor(WorldLayout.Level31);
        foreach (IServerPlayer player in players)
        {
            if (shadows.ContainsKey(player.PlayerUID) || rand.NextDouble() > 0.05) continue;
            EntityPos pos = player.Entity.Pos;
            for (int attempt = 0; attempt < 12; attempt++)
            {
                double angle = rand.NextDouble() * Math.PI * 2, r = 13 + rand.NextDouble() * 10;
                int x = (int)Math.Floor(pos.X + Math.Cos(angle) * r), z = (int)Math.Floor(pos.Z + Math.Sin(angle) * r);
                Tile t = layout.TileAt(x, z);
                if (t.Level != WorldLayout.Level31 || t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || !DarkZone(t.Zone)) continue;
                var at = new BlockPos(x, floor + 1, z);
                if (sapi.World.BlockAccessor.GetChunkAtBlockPos(at) == null || sapi.World.BlockAccessor.GetLightLevel(at, EnumLightLevelType.MaxLight) > 5) continue;
                Entity shadow = sapi.World.ClassRegistry.CreateEntity(shadowType);
                shadow.Pos.SetPos(x + 0.5, floor + 1, z + 0.5);
                shadow.Pos.Yaw = (float)Math.Atan2(pos.X - (x + 0.5), pos.Z - (z + 0.5));
                sapi.World.SpawnEntity(shadow);
                shadows[player.PlayerUID] = (shadow, now + 25_000);
                break;
            }
        }
    }

    // ================= The card dispenser =================

    public static void Dispense(IServerPlayer player, BlockPos pos)
    {
        IWorldAccessor world = player.Entity.World;
        Item card = world.GetItem(new AssetLocation("backrooms:l31-greencard"));
        if (card == null) return;
        bool has = false;
        player.Entity.WalkInventory(slot =>
        {
            if (slot?.Itemstack?.Collectible == card) has = true;
            return !has;
        });
        if (has)
        {
            Say(player, "backrooms:l31-card-have");
            return;
        }
        var stack = new ItemStack(card);
        if (!player.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true) || stack.StackSize > 0)
            world.SpawnItemEntity(stack, pos.ToVec3d().Add(0.5, 1.1, 0.5));
        world.PlaySoundAt(new AssetLocation("game:sounds/effect/latch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 12);
        Say(player, "backrooms:l31-card-got");
    }
}

/// <summary>One of Level 31's people (the Coach, the staff, a shadow): cannot be hurt, never kept with the world.</summary>
public class EntityL31Staff : EntityAgent
{
    public override bool StoreWithChunk => false;
    public override bool IsInteractable => WatchedAttributes.GetInt("l31role", -1) >= 0;

    public override bool ShouldReceiveDamage(DamageSource damageSource, float damage) => false;

    public override bool ReceiveDamage(DamageSource damageSource, float damage)
    {
        if (World.Side == EnumAppSide.Server && damageSource?.GetCauseEntity() is EntityPlayer { Player: IServerPlayer player })
            ((ICoreServerAPI)World.Api).ModLoader.GetModSystem<L31System>()?.Struck(player, this);
        return false;
    }

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode)
    {
        // (The Coach's dialogue is a behaviour: let the behaviours have the click)
        base.OnInteract(byEntity, itemslot, hitPosition, mode);
        if (World.Side != EnumAppSide.Server || byEntity is not EntityPlayer { Player: IServerPlayer player }) return;
        var rules = ((ICoreServerAPI)World.Api).ModLoader.GetModSystem<L31System>();
        // (A blow comes through ReceiveDamage)
        if (mode == EnumInteractMode.Interact) rules?.Interact(player, this);
    }
}

/// <summary>The arcade's green-card dispenser: press the button for a card.</summary>
public class BlockBehaviorL31Dispenser : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL31Dispenser(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l31-dispenser", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player) L31System.Dispense(player, blockSel.Position);
        return true;
    }
}
