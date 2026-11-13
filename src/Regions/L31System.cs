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
/// <item><b>Stealing skates</b> (Fandom; the links round): a pair can be lifted out of Skate Rental's cubbies, but whoever
/// walks out of the rental with it noclips into Level 0 without it (Thresholds.ThresholdSystem.L31Steal); and whoever leaves
/// the level by any way with the rink's skates about them likewise (ThresholdSystem.L31Redirect, <see cref="TakeSkates"/>).</item>
/// <item>The Coach's "lead me out" (<c>l31-leadout</c>, his dialogue's trigger) marks the nearest revolving door on the
/// player's map (Wikidot: he "leads you out if asked").</item>
/// </list>
/// </summary>
public class L31System : ModSystem
{
    private const int StaffNear = 40, StaffGone = 96;
    /// <summary>How often the server feeds a player (in-game hours), and how long it refuses a litterer.</summary>
    private const double ServeHours = 12, RefuseHours = 24;
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
    private bool forceShadow;

    public override bool ShouldLoad(EnumAppSide side) => true;

    // (After BackroomsModSystem)
    public override double ExecuteOrder() => 1.3;

    public override void Start(ICoreAPI api)
    {
        api.RegisterEntity("BackroomsL31Staff", typeof(EntityL31Staff));
        api.RegisterBlockBehaviorClass("BackroomsL31Dispenser", typeof(BlockBehaviorL31Dispenser));
        api.RegisterBlockBehaviorClass("BackroomsL31SkateShelf", typeof(BlockBehaviorL31SkateShelf));
    }

    public override void AssetsFinalize(ICoreAPI api)
    {
        foreach (Block block in api.World.Blocks)
            if (block?.Code?.Domain == "backrooms" && block.Code.Path.StartsWith("l31-dispenser-", StringComparison.Ordinal))
                BehaviorInjection.Add(block, new BlockBehaviorL31Dispenser(block));
            else if (block?.Code?.Domain == "backrooms" && block.Code.Path.StartsWith("l31-skateshelf-", StringComparison.Ordinal))
                BehaviorInjection.Add(block, new BlockBehaviorL31SkateShelf(block));
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

        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l31")
                .WithDescription("Level 31 (testing): 'staff' puts the staff (the Coach, the food court's server, the DJ) at their spots near you now; 'shadow' tries to put a shadow figure down in a dark spot near you; "
                    + "the ways in and out, as a player: 'door2', 'door3', 'door6' take you to the wooden door nearest spawn in that level and through it; 'door' through the wooden door beside you; "
                    + "'revolving' to the nearest revolving door and through it; 'skates' gives you the Coach's skates, 'steal' a pair from the cubbies; 'where' logs where you are and your skates")
                .WithArgs(api.ChatCommands.Parsers.Word("what"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnCommand)
            .EndSubCommand();
    }

    private TextCommandResult OnCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        if (args.Caller.Player is IServerPlayer caller && LinkTest(caller, (string)args[0]) is { } tested) return tested;
        var players = PlayersHere();
        if (players.Count == 0) return TextCommandResult.Error("Nobody is in Level 31");
        switch ((string)args[0])
        {
            case "staff":
                int before = staff.Count;
                KeepStaff(players);
                return TextCommandResult.Success($"{staff.Count} of the staff about ({staff.Count - before} new)");
            case "shadow":
                forceShadow = true;
                Shadows(players);
                forceShadow = false;
                return TextCommandResult.Success($"{shadows.Count} shadow figures about");
            default:
                return TextCommandResult.Error("staff or shadow");
        }
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
            // Out of Skate Rental with a pair from the cubbies: noclipped into Level 0, without them
            if (here && TileAt(e.Pos.X, e.Pos.Z).Zone != (byte)Zone.Rental && HasStolen(player))
                sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>()?.L31Steal(player);
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
                if (role == WorldLayout.L31Coach) HearLeadOut(person);
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
        if (rand.NextDouble() < 0.3)
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
            if (shadows.ContainsKey(player.PlayerUID) || !forceShadow && rand.NextDouble() > 0.05) continue;
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

    // ================= Testing the ways in and out as a player =================

    private TextCommandResult LinkTest(IServerPlayer player, string what)
    {
        var thresholds = sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>();
        EntityPos pos = player.Entity.Pos;
        int px = (int)Math.Floor(pos.X), pz = (int)Math.Floor(pos.Z);
        void Report(string label) => sapi.Event.RegisterCallback(_ => LogWhere(player, label), 6000);
        switch (what)
        {
            case "door2" or "door3" or "door6":
            {
                int host = what[4] - '0';
                var (sx, sz) = layout.FindSpawn();
                if (layout.L31NearestHostDoor(host, WorldLayout.MacroOf(sx), WorldLayout.MacroOf(sz)) is not { } door)
                    return TextCommandResult.Error($"No wooden door found in Level {host}");
                var (fx, fz) = Step(door.Facing);
                int floor = geometry.FloorFor(host);
                var at = new BlockPos(door.X, floor + 1, door.Z);
                sapi.Logger.Notification("[backrooms] l31 test {0}: the wooden door at {1}, {2} facing {3}; standing at {4}, {5}", what, door.X, door.Z, door.Facing, door.X + fx, door.Z + fz);
                player.Entity.TeleportToDouble(door.X + fx + 0.5, floor + 1.05, door.Z + fz + 0.5, () =>
                    sapi.Event.RegisterCallback(_ =>
                    {
                        LogWhere(player, what + " before");
                        thresholds?.Use(player, at, "l31-door");
                        Report(what + " after");
                    }, 1500));
                return TextCommandResult.Success($"To the wooden door at {door.X}, {door.Z} in Level {host}, and through it");
            }
            case "door":
            {
                for (int r = 1; r <= 4; r++)
                    for (int dz = -r; dz <= r; dz++)
                        for (int dx = -r; dx <= r; dx++)
                        {
                            Tile t = layout.TileAt(px + dx, pz + dz);
                            if (!WorldLayout.IsL31LobbyDoor(t) && !WorldLayout.IsL31HostDoor(t)) continue;
                            LogWhere(player, "door before");
                            thresholds?.Use(player, new BlockPos(px + dx, geometry.FloorFor(t.Level) + 1, pz + dz), "l31-door");
                            Report("door after");
                            return TextCommandResult.Success($"Through the wooden door at {px + dx}, {pz + dz}");
                        }
                return TextCommandResult.Error("No wooden door beside you");
            }
            case "revolving":
            {
                (int X, int Z) from = In31(pos) ? (px, pz) : (layout.L31CentreX * WorldLayout.MacroSize, layout.L31CentreZ * WorldLayout.MacroSize);
                if (layout.L31NearestRevolving(from.X, from.Z) is not { } door) return TextCommandResult.Error("No revolving door near");
                // (In the lobby, a couple of steps in front of the drum: its middle tile faces into the lobby)
                var (fx, fz) = Step(layout.TileAt(door.X, door.Z).Pier);
                int floor = geometry.FloorFor(WorldLayout.Level31);
                var at = new BlockPos(door.X, floor + 1, door.Z);
                player.Entity.TeleportToDouble(door.X + 2 * fx + 0.5, floor + 1.05, door.Z + 2 * fz + 0.5, () =>
                    sapi.Event.RegisterCallback(_ =>
                    {
                        LogWhere(player, "revolving before");
                        thresholds?.Use(player, at, "l31-revolving");
                        Report("revolving after");
                    }, 1500));
                return TextCommandResult.Success($"To the revolving door at {door.X}, {door.Z} (to Level {layout.L31RevolvingTarget(door.X, door.Z)}), and through it");
            }
            case "skates" or "steal":
            {
                Item skates = sapi.World.GetItem(new AssetLocation("backrooms:l31-skates"));
                if (skates == null) return TextCommandResult.Error("No skates item");
                var stack = new ItemStack(skates);
                if (what == "steal") stack.Attributes.SetBool(StolenKey, true);
                player.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true);
                Report(what);
                return TextCommandResult.Success(what == "steal" ? "A pair from the cubbies" : "The Coach's skates");
            }
            case "where":
                LogWhere(player, "where");
                return TextCommandResult.Success("Logged");
        }
        return null;
    }

    private static (int Dx, int Dz) Step(ArchPier facing) => facing switch
    {
        ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0),
    };

    private void LogWhere(IServerPlayer player, string label)
    {
        if (player.Entity == null) return;
        EntityPos p = player.Entity.Pos;
        int x = (int)Math.Floor(p.X), z = (int)Math.Floor(p.Z);
        int skates = 0, stolen = 0;
        player.Entity.WalkInventory(slot =>
        {
            if (IsSkates(slot?.Itemstack))
            {
                skates++;
                if (slot.Itemstack.Attributes.GetBool(StolenKey)) stolen++;
            }
            return true;
        });
        Tile t = layout.TileAt(x, z);
        sapi.Logger.Notification("[backrooms] l31 test {0}: {1} in level {2} at {3:0.0}, {4:0.0}, {5:0.0} (zone {6}); skates {7} ({8} from the cubbies); beside: {9}",
            label, player.PlayerName, t.Level, p.X, p.Y, p.Z, t.Zone, skates, stolen, Beside(x, z));
    }

    /// <summary>What wooden or revolving door stands beside a tile, for the test log.</summary>
    private string Beside(int x, int z)
    {
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
            {
                Tile t = layout.TileAt(x + dx, z + dz);
                if (WorldLayout.IsL31LobbyDoor(t)) return $"a lobby's wooden door at {x + dx}, {z + dz}";
                if (WorldLayout.IsL31HostDoor(t)) return $"a wooden door into the rink at {x + dx}, {z + dz}";
                if (WorldLayout.IsL31Revolving(t)) return $"a revolving door at {x + dx}, {z + dz}";
            }
        return "nothing of the rink's";
    }

    // ================= The ways out =================

    private const string StolenKey = "l31stolen";

    private static bool IsSkates(ItemStack stack) => stack?.Collectible?.Attributes?["l31skates"].AsBool(false) == true;

    /// <summary>Whether a player has a pair of skates from the cubbies about them (not the Coach's).</summary>
    public static bool HasStolen(IServerPlayer player)
    {
        bool has = false;
        player.Entity?.WalkInventory(slot =>
        {
            if (IsSkates(slot?.Itemstack) && slot.Itemstack.Attributes.GetBool(StolenKey)) has = true;
            return !has;
        });
        return has;
    }

    /// <summary>Takes every pair of the rink's skates off a player (worn or carried); whether there were any.</summary>
    public static bool TakeSkates(IServerPlayer player)
    {
        bool any = false;
        player.Entity?.WalkInventory(slot =>
        {
            if (!IsSkates(slot?.Itemstack)) return true;
            slot.Itemstack = null;
            slot.MarkDirty();
            any = true;
            return true;
        });
        return any;
    }

    /// <summary>A pair lifted out of Skate Rental's cubbies (one at a time), marked as nobody's loan.</summary>
    public static void LiftSkates(IServerPlayer player, BlockPos pos)
    {
        if (HasStolen(player))
        {
            Say(player, "backrooms:l31-skates-have");
            return;
        }
        IWorldAccessor world = player.Entity.World;
        Item skates = world.GetItem(new AssetLocation("backrooms:l31-skates"));
        if (skates == null) return;
        var stack = new ItemStack(skates);
        stack.Attributes.SetBool(StolenKey, true);
        if (!player.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true) || stack.StackSize > 0)
            world.SpawnItemEntity(stack, pos.ToVec3d().Add(0.5, 1.1, 0.5));
        world.PlaySoundAt(new AssetLocation("game:sounds/player/build"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 8);
        Say(player, "backrooms:l31-skates-take");
    }

    /// <summary>The Coach hears "lead me out" (his dialogue's <c>l31-leadout</c> trigger) and marks the nearest revolving door.</summary>
    private void HearLeadOut(Entity coach)
    {
        if (coach.GetBehavior<Vintagestory.GameContent.EntityBehaviorConversable>() is not { } talk) return;
        talk.OnControllerCreated += controller => controller.DialogTriggers += (who, value, data) =>
        {
            if (value != "l31-leadout") return -1;
            if (who is EntityPlayer { Player: IServerPlayer player }) LeadOut(player);
            return 0;
        };
    }

    private void LeadOut(IServerPlayer player)
    {
        if (layout == null || player.Entity == null) return;
        EntityPos pos = player.Entity.Pos;
        if (layout.L31NearestRevolving((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)) is not { } door)
        {
            Say(player, "backrooms:l31-coach-leadout-none");
            return;
        }
        var at = new Vec3d(door.X + 0.5, geometry.FloorFor(WorldLayout.Level31) + 1, door.Z + 0.5);
        Map.MapMarks.Add(sapi, player, at, Lang.Get("backrooms:l31-waypoint-revolving"), "spiral", Map.MapMarks.WayColorTo(layout.L31RevolvingTarget(door.X, door.Z)), 6, tell: false);
        Say(player, "backrooms:l31-coach-leadout");
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

/// <summary>Skate Rental's cubbies: lift out a pair (Fandom's thief: noclipped to Level 0 on leaving the rental with it).</summary>
public class BlockBehaviorL31SkateShelf : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL31SkateShelf(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l31-skateshelf", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player) L31System.LiftSkates(player, blockSel.Position);
        return true;
    }
}
