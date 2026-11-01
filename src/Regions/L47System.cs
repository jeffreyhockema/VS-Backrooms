using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// Level 47, "The Adderwood"'s living things on the server (experimental, kept as level 30). The level is not the entity
/// director's (its band is Safe): this system keeps its own, as the lore has them (Wikidot):
/// <list type="bullet">
/// <item><b>Snakes</b>, a handful round anyone in the forest, by day and night: harmless, sacred. Whoever harms one (or one of
/// the Order) has the Great Adder put down out of their sight, coming for them (<see cref="Offend"/>).</item>
/// <item><b>Irish elk</b> by day, now and then, far off (the vanilla moose stands in: palmate antlers, and its bulls and its
/// cows with calves are as quick to charge as the lore's; our substitution).</item>
/// <item><b>Black Shucks</b> by night: after a while out in the forest at night a scout finds you (put down out of sight) and
/// stalks; the rest of the pack come in over the next minutes (<see cref="ShuckPackHunts"/> together, and they hunt). At dawn
/// they run. Never in the glade.</item>
/// <item><b>The Ophion Order</b>: four keepers in the glade, hostile to whoever comes in; now and then a walker on the trail,
/// indifferent, who stops and looks, and sometimes preaches (<see cref="Preach"/>).</item>
/// </list>
/// <c>/backrooms l47 snake|adder|shuck|pack|keeper|walker|elk</c> put them down for testing. This file is the level's own.
/// </summary>
public class L47System : ModSystem
{
    public const string SnakeCode = "backrooms:l47-snake", AdderCode = "backrooms:l47-greatadder", ShuckCode = "backrooms:l47-shuck", OphionCode = "backrooms:l47-ophion";

    /// <summary>Entity attribute: put down for a showcase shot, it holds still (rearing, standing, watching) and does nothing else.</summary>
    public const string ShowKey = "backrooms:l47Show";

    /// <summary>How many of a pack together turn the stalk into the hunt.</summary>
    public const int ShuckPackHunts = 3;

    private const int SnakeCap = 4, KeeperCount = 4;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private readonly Random rand = new();
    private readonly Dictionary<string, double> nightOut = new();
    private readonly Dictionary<string, long> nextPackMs = new();
    private long tick, slowTick;

    public override void Start(ICoreAPI api)
    {
        AiTaskRegistry.Register<AiTaskL47Snake>("backrooms-l47-snake");
        AiTaskRegistry.Register<AiTaskL47Adder>("backrooms-l47-greatadder");
        AiTaskRegistry.Register<AiTaskL47Shuck>("backrooms-l47-shuck");
        AiTaskRegistry.Register<AiTaskL47Ophion>("backrooms-l47-ophion");
    }

    public override bool ShouldLoad(EnumAppSide side) => true;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.3;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            tick = api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] Level 47: {0}", e), 2000, 1200);
            slowTick = api.Event.RegisterGameTickListener(OnSlowTick, e => api.Logger.Error("[backrooms] Level 47 despawn: {0}", e), 10000, 3000);
            api.Event.PlayerDisconnect += p => { nightOut.Remove(p.PlayerUID); nextPackMs.Remove(p.PlayerUID); };
        });
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l47")
                .WithDescription("Level 47 (testing): 'snake', 'adder' (comes for you), 'shuck' (a scout stalks you), 'pack' (three hunt you), 'keeper', 'walker', 'elk' puts one down near you (or at x z, from the console)")
                .WithArgs(api.ChatCommands.Parsers.Word("what"), api.ChatCommands.Parsers.OptionalInt("x"), api.ChatCommands.Parsers.OptionalInt("z"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnCommand)
            .EndSubCommand();
    }

    public override void Dispose()
    {
        if (sapi == null) return;
        if (tick != 0) sapi.Event.UnregisterGameTickListener(tick);
        if (slowTick != 0) sapi.Event.UnregisterGameTickListener(slowTick);
    }

    // ================= Where things are =================

    public bool InLevel(double x, double z) => layout != null && layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(x)), WorldLayout.MacroOf((int)Math.Floor(z))) == WorldLayout.Level47;

    /// <summary>Whether a point is in the glade (or within a margin of its edge).</summary>
    public bool InGlade(double x, double z, double margin) => InLevel(x, z) && layout.L47FromMid(x, z) < WorldLayout.L47GladeRadius + margin;

    /// <summary>Whether it is night in the Adderwood (the fog gone), by the world's clock.</summary>
    public bool IsNight() => AtmosphereSystem.L47Night(sapi.World.Calendar) > 0.5f;

    /// <summary>Whether a member of the Order stands within a distance of a point.</summary>
    public bool OphionNear(Vec3d at, double range) => sapi.World.GetEntitiesAround(at, (float)range, 6, e => e.Alive && e.Code?.Path == "l47-ophion").Length > 0;

    public double TrailPhiAt(double x, double z) => layout.L47TrailDistance(x, z, out double phi) < 8 ? phi : -1;

    public (double X, double Z) TrailPoint(double phi) => layout.L47TrailPoint(phi);

    public double TrailRadius(double phi) => layout.L47FromMid(layout.L47TrailPoint(phi).X, layout.L47TrailPoint(phi).Z);

    // ================= Words =================

    /// <summary>A member of the Order says something to whoever is near (one of the level's lines).</summary>
    public void Say(Entity speaker, Entity to, string key)
    {
        foreach (IPlayer p in sapi.World.AllOnlinePlayers)
        {
            if (p is not IServerPlayer sp || p.Entity == null || p.Entity.Pos.SquareDistanceTo(speaker.Pos) > 20 * 20) continue;
            sp.SendMessage(GlobalConstants.GeneralChatGroup, Say0(sp, "l47-ophion-name") + ": " + Say0(sp, key), EnumChatType.Notification);
        }
        speaker.World.PlaySoundAt(new AssetLocation($"backrooms:sounds/ambient/47/murmur{1 + rand.Next(3)}"), speaker.Pos.X, speaker.Pos.Y + 1.6, speaker.Pos.Z, null, true, 16, 0.6f);
    }

    /// <summary>How many lines the Order preaches (l47-ophion-preach-1...).</summary>
    public const int PreachLines = 8;

    /// <summary>A member of the Order preaches: its boasts (Wikidot: "the arcane secrets and miraculous powers their order possesses, including the ability to travel The Backrooms at will").</summary>
    public void Preach(Entity speaker, Entity to) => Say(speaker, to, "l47-ophion-preach-" + (1 + rand.Next(PreachLines)));

    private static string Say0(IServerPlayer p, string key) => Backrooms.Say.T(p, "backrooms:" + key);

    // ================= The Great Adder =================

    /// <summary>
    /// Someone has harmed a snake (or one of the Order): the Great Adder comes for them. Put down out of their sight, sixteen
    /// to twenty-four blocks off, behind them; one at a time for each offender.
    /// </summary>
    public void Offend(IServerPlayer player, Vec3d at, string why)
    {
        if (layout == null || player.Entity is not { Alive: true } pe || !InLevel(pe.Pos.X, pe.Pos.Z)) return;
        if (sapi.World.GetEntitiesAround(pe.Pos.XYZ, 160, 40, e => e.Alive && e.Code?.Path == "l47-greatadder"
            && e.WatchedAttributes.GetString(AiTaskL47Adder.QuarryKey) == player.PlayerUID).Length > 0) return;
        Entity adder = PutDownAdder(pe, player.PlayerUID);
        if (adder == null) return;
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say0(player, why == "snake" ? "l47-adder-comes" : "l47-adder-summoned"), EnumChatType.Notification);
    }

    private Entity PutDownAdder(Entity quarry, string quarryId)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(AdderCode));
        if (type == null) return null;
        Vec3d spot = Behind(quarry, 16, 24, 3) ?? Around(quarry.Pos.XYZ, 12, 20, 3);
        if (spot == null) return null;
        Entity e = sapi.World.ClassRegistry.CreateEntity(type);
        e.Pos.SetPos(spot);
        e.Pos.Yaw = (float)Math.Atan2(quarry.Pos.X - spot.X, quarry.Pos.Z - spot.Z);
        e.WatchedAttributes.SetString(AiTaskL47Adder.QuarryKey, quarryId);
        e.AlwaysActive = true;
        sapi.World.SpawnEntity(e);
        Strike.Log(e, "comes for {0}", quarryId);
        return e;
    }

    // ================= Putting things down =================

    /// <summary>A free standing spot on the ground (feet position) out of a player's sight, behind them, between two distances, or null.</summary>
    private Vec3d Behind(Entity who, double near, double far, int headroom)
    {
        var (fx, fz) = Forward(who);
        double back = Math.Atan2(-fz, -fx);
        for (int attempt = 0; attempt < 16; attempt++)
        {
            double a = back + (rand.NextDouble() - 0.5) * 2.2, r = near + rand.NextDouble() * (far - near);
            var spot = Ground(who.Pos.X + Math.Cos(a) * r, who.Pos.Y, who.Pos.Z + Math.Sin(a) * r, headroom);
            if (spot != null && (who is not EntityPlayer || !Senses.LooksAt(who, spot, 60))) return spot;
        }
        return null;
    }

    /// <summary>Which way an entity looks, along the ground (a unit vector along x then z).</summary>
    private static (double X, double Z) Forward(Entity who)
    {
        Vec3f v = who.Pos.GetViewVector();
        double len = Math.Sqrt(v.X * v.X + v.Z * v.Z);
        return len < 1e-4 ? (0, -1) : (v.X / len, v.Z / len);
    }

    /// <summary>A free standing spot on the ground in front of an entity, about a distance off (for the showcase shots).</summary>
    private Vec3d Ahead(Entity who, double distance, int headroom, double heading = double.NaN)
    {
        var (fx, fz) = double.IsNaN(heading) ? Forward(who) : (Math.Sin(heading * Math.PI / 180), -Math.Cos(heading * Math.PI / 180));
        for (int attempt = 0; attempt < 12; attempt++)
        {
            double side = (attempt % 2 == 0 ? 1 : -1) * (attempt / 2) * 0.8, d = distance + (attempt / 4);
            var spot = Ground(who.Pos.X + fx * d - fz * side, who.Pos.Y, who.Pos.Z + fz * d + fx * side, headroom);
            if (spot != null) return spot;
        }
        return null;
    }

    /// <summary>A free standing spot on the ground round a point, between two distances, or null.</summary>
    private Vec3d Around(Vec3d at, double near, double far, int headroom)
    {
        for (int attempt = 0; attempt < 16; attempt++)
        {
            double a = rand.NextDouble() * Math.PI * 2, r = near + rand.NextDouble() * (far - near);
            var spot = Ground(at.X + Math.Cos(a) * r, at.Y, at.Z + Math.Sin(a) * r, headroom);
            if (spot != null) return spot;
        }
        return null;
    }

    private Vec3d Ground(double x, double nearY, double z, int headroom)
    {
        int bx = (int)Math.Floor(x), bz = (int)Math.Floor(z);
        if (!InLevel(bx, bz) || sapi.World.BlockAccessor.GetChunkAtBlockPos(bx, (int)nearY, bz) == null) return null;
        Tile t = layout.TileAt(bx, bz);
        if (t.Kind != TileKind.Floor || t.Zone is WorldLayout.L47ManorZone or WorldLayout.L47RimZone || t.Under != 0) return null;
        int y = Senses.FindFloor(sapi.World, bx, (int)Math.Floor(nearY), bz, headroom, 6);
        if (y == int.MinValue) return null;
        // (Never in water)
        if (sapi.World.BlockAccessor.GetBlock(new BlockPos(bx, y, bz), BlockLayersAccess.Fluid)?.LiquidCode != null) return null;
        return new Vec3d(bx + 0.5, y, bz + 0.5);
    }

    private Entity Spawn(string code, Vec3d at, System.Action<Entity> setup = null)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(code));
        if (type == null || at == null) return null;
        Entity e = sapi.World.ClassRegistry.CreateEntity(type);
        e.Pos.SetPos(at);
        e.Pos.Yaw = (float)(rand.NextDouble() * Math.PI * 2);
        double danger = Danger.OfLevel(WorldLayout.Level47);
        e.Attributes.SetDouble(Danger.Key, danger);
        setup?.Invoke(e);
        sapi.World.SpawnEntity(e);
        return e;
    }

    private int Count(Vec3d at, float range, string path, System.Func<Entity, bool> also = null) =>
        sapi.World.GetEntitiesAround(at, range, 24, e => e.Alive && e.Code?.Path == path && (also == null || also(e))).Length;

    private Entity PutDownShuck(Entity quarry, string quarryId, double near, double far)
    {
        Vec3d spot = Behind(quarry, near, far, 2) ?? Around(quarry.Pos.XYZ, near, far, 2);
        return Spawn(ShuckCode, spot, e =>
        {
            e.WatchedAttributes.SetString(AiTaskL47Shuck.QuarryKey, quarryId);
            e.WatchedAttributes.SetInt("textureIndex", rand.Next(2));
        });
    }

    private Entity PutDownOphion(Vec3d at, bool walker)
    {
        return Spawn(OphionCode, at, e =>
        {
            e.WatchedAttributes.SetBool(AiTaskL47Ophion.WalkerKey, walker);
            e.WatchedAttributes.SetDouble(AiTaskL47Ophion.HomeKey + "X", at.X);
            e.WatchedAttributes.SetDouble(AiTaskL47Ophion.HomeKey + "Y", at.Y);
            e.WatchedAttributes.SetDouble(AiTaskL47Ophion.HomeKey + "Z", at.Z);
            e.WatchedAttributes.SetInt("textureIndex", walker || rand.NextDouble() < 0.6 ? 0 : 1);
        });
    }

    /// <summary>The keepers' places in the glade (glade-local): before the door, by the stones, on the walk in.</summary>
    private static readonly (int U, int V)[] KeeperPlaces = { (0, 11), (-6, 15), (7, 14), (3, 30) };

    private void OnTick(float dt)
    {
        if (layout == null) return;
        float night = AtmosphereSystem.L47Night(sapi.World.Calendar);
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity is not { Alive: true } pe) continue;
            if (player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
            if (!InLevel(pe.Pos.X, pe.Pos.Z)) { nightOut.Remove(player.PlayerUID); continue; }
            Vec3d at = pe.Pos.XYZ;
            double fromGlade = layout.L47FromMid(at.X, at.Z);

            // Snakes, a few round about, in the litter
            if (Count(at, 40, "l47-snake") < SnakeCap && rand.NextDouble() < 0.5)
                Spawn(SnakeCode, Behind(pe, 12, 28, 1) ?? Around(at, 14, 28, 1), e => e.WatchedAttributes.SetInt("textureIndex", rand.Next(4)));

            // The Order's keepers in the glade, put there before anyone comes into it
            if (fromGlade < 160 && fromGlade > 30)
            {
                var mid = new Vec3d(layout.L47MidX + 0.5, at.Y, layout.L47MidZ + 0.5);
                int keepers = Count(mid, 60, "l47-ophion", e => !e.WatchedAttributes.GetBool(AiTaskL47Ophion.WalkerKey));
                for (int k = keepers; k < KeeperCount; k++)
                {
                    var (u, v) = KeeperPlaces[k];
                    PutDownOphion(Ground(layout.L47MidX + u + 0.5, geometry.FloorFor(WorldLayout.Level47) + 2, layout.L47MidZ + v + 0.5, 2), false);
                }
            }
            // Now and then a walker on the trail
            if (fromGlade > 90 && layout.L47TrailAt((int)Math.Floor(at.X), (int)Math.Floor(at.Z)) < 14 && rand.NextDouble() < 0.006
                && Count(at, 120, "l47-ophion", e => e.WatchedAttributes.GetBool(AiTaskL47Ophion.WalkerKey)) == 0)
            {
                double phi = layout.L47TrailDistance(at.X, at.Z, out double here) < 20 ? here : -1;
                if (phi >= 0)
                {
                    double along = phi + (rand.NextDouble() < 0.5 ? 1 : -1) * 36 / Math.Max(60, fromGlade);
                    var (x, z) = layout.L47TrailPoint(Math.Max(0.3, along));
                    var spot = Ground(x, at.Y, z, 2);
                    if (spot != null && !Senses.LooksAt(pe, spot, 45)) PutDownOphion(spot, true);
                }
            }

            // By day the elk, far off now and then (a cow with her calf, or a bull)
            if (night < 0.3f && rand.NextDouble() < 0.025 && Count(at, 90, "deer-moose-adult-male") + Count(at, 90, "deer-moose-adult-female") == 0)
            {
                var spot = Around(at, 45, 70, 3);
                if (spot != null)
                {
                    bool bull = rand.NextDouble() < 0.5;
                    Spawn(bull ? "game:deer-moose-adult-male" : "game:deer-moose-adult-female", spot);
                    if (!bull && rand.NextDouble() < 0.6) Spawn("game:deer-moose-baby-female", spot.AddCopy(1.5, 0, 1));
                }
            }

            // By night the Black Shucks: after a while out in the forest a scout finds you, and the pack follows
            bool outInIt = night > 0.8f && fromGlade > WorldLayout.L47GladeRadius + 30;
            if (!outInIt) { nightOut.Remove(player.PlayerUID); continue; }
            nightOut[player.PlayerUID] = (nightOut.TryGetValue(player.PlayerUID, out double t) ? t : 0) + dt;
            int pack = Count(at, 48, "l47-shuck", e => e.WatchedAttributes.GetString(AiTaskL47Shuck.QuarryKey) == player.PlayerUID);
            long now = sapi.World.ElapsedMilliseconds;
            if (pack == 0)
            {
                // (A minute or two out, then a chance every few seconds)
                if (nightOut[player.PlayerUID] > 70 && rand.NextDouble() < 0.06)
                {
                    PutDownShuck(pe, player.PlayerUID, 20, 30);
                    nextPackMs[player.PlayerUID] = now + 30000 + rand.Next(25000);
                }
            }
            else if (pack < ShuckPackHunts + 1 && now > (nextPackMs.TryGetValue(player.PlayerUID, out long next) ? next : 0))
            {
                PutDownShuck(pe, player.PlayerUID, 26, 40);
                nextPackMs[player.PlayerUID] = now + 30000 + rand.Next(25000);
            }
        }
    }

    /// <summary>Lets go of what nobody is near any more: snakes and elk out of everyone's way, walkers far behind, keepers when nobody is near the glade.</summary>
    private void OnSlowTick(float dt)
    {
        if (layout == null) return;
        var players = sapi.World.AllOnlinePlayers.Where(p => p.Entity != null).Select(p => p.Entity.Pos.XYZ).ToList();
        foreach (Entity e in sapi.World.LoadedEntities.Values.ToList())
        {
            if (!e.Alive) continue;
            string path = e.Code?.Path;
            double far = path switch
            {
                "l47-snake" => 60,
                "deer-moose-adult-male" or "deer-moose-adult-female" or "deer-moose-baby-female" => 120,
                "l47-ophion" => e.WatchedAttributes.GetBool(AiTaskL47Ophion.WalkerKey) ? 110 : 220,
                "l47-shuck" => 90,
                _ => -1,
            };
            if (far < 0 || e.AlwaysActive || !InLevel(e.Pos.X, e.Pos.Z)) continue;
            if (players.Any(p => p.SquareDistanceTo(e.Pos.XYZ) < far * far)) continue;
            e.Die(EnumDespawnReason.OutOfRange);
        }
    }

    // ================= Testing =================

    private TextCommandResult OnCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world.");
        string what = (string)args[0];
        Entity caller = args.Caller.Entity;
        if (what == "state")
        {
            var lines = sapi.World.LoadedEntities.Values.Where(e => e.Code?.Domain == "backrooms" && e.Code.Path.StartsWith("l47-") || e.Code?.Path.StartsWith("deer-moose") == true)
                .Select(e => $"{e.Code.Path} #{e.EntityId} at {e.Pos.X:0},{e.Pos.Y:0},{e.Pos.Z:0} {(e.Alive ? "alive" : "dead")} health {e.GetBehavior<EntityBehaviorHealth>()?.Health:0.0}"
                    + $" quarry {e.WatchedAttributes.GetString(AiTaskL47Adder.QuarryKey, "-")} night {AtmosphereSystem.L47Night(sapi.World.Calendar):0.00}");
            return TextCommandResult.Success("l47 state:\n" + string.Join("\n", lines));
        }
        Vec3d at;
        if (args.Parsers[2].IsMissing) at = caller?.Pos.XYZ;
        else
        {
            int x = (int)args[1], z = (int)args[2];
            int y = Senses.FindFloor(sapi.World, x, geometry.FloorFor(WorldLayout.Level47) + layout.TileAt(x, z).Height + 1, z, 2, 8);
            at = y == int.MinValue ? null : new Vec3d(x + 0.5, y, z + 0.5);
        }
        if (at == null) return TextCommandResult.Error("Where? Give x and z from the console.");
        Entity quarry = caller ?? sapi.World.GetNearestEntity(at, 32, 8, e => e.Alive && (e is EntityPlayer || Senses.IsTestTarget(e)));
        string quarryId = quarry is EntityPlayer ep ? ep.PlayerUID : quarry?.EntityId.ToString();
        // An aurora over the caller's night whatever night it is (for the showcase: the sky is drawn on their client, Regions.L47Sky)
        if (what == "aurora" && caller != null)
        {
            bool on = !caller.WatchedAttributes.GetBool(L47Sky.AuroraKey);
            caller.WatchedAttributes.SetBool(L47Sky.AuroraKey, on);
            return TextCommandResult.Success(on ? "An aurora tonight." : "The aurora as the nights have it.");
        }
        // The showcase's: put down in front of whoever asks, held still for the shot
        if (what.StartsWith("show") && caller != null)
        {
            // (The heading the shot looks along, in degrees, as the first number: the camera turns after the setup runs)
            double heading = args.Parsers[1].IsMissing ? double.NaN : (int)args[1];
            Entity Shown(Entity e)
            {
                if (e == null) return null;
                e.WatchedAttributes.SetBool(ShowKey, true);
                e.Pos.Yaw = (float)Math.Atan2(caller.Pos.X - e.Pos.X, caller.Pos.Z - e.Pos.Z);
                return e;
            }
            Entity shown = what switch
            {
                "showsnake" => Shown(Spawn(SnakeCode, Ahead(caller, 3, 1, heading), e => e.WatchedAttributes.SetInt("textureIndex", rand.Next(4)))),
                "showadder" => Shown(Spawn(AdderCode, Ahead(caller, 11, 3, heading))),
                "showelk" => Shown(Spawn("game:deer-moose-adult-male", Ahead(caller, 9, 3, heading))),
                "showwalker" => Shown(PutDownOphion(Ahead(caller, 7, 2, heading), true)),
                "showkeepers" => new[] { -3, 0, 3 }.Select(side => Shown(PutDownOphion(Ground(caller.Pos.X + side, caller.Pos.Y, caller.Pos.Z - 9 + Math.Abs(side), 2), false))).LastOrDefault(e => e != null),
                "showpack" => Enumerable.Range(0, 3).Select(k => Shown(Spawn(ShuckCode, Ahead(caller, 6 + k * 2, 2, heading), e => e.WatchedAttributes.SetInt("textureIndex", k % 2)))).LastOrDefault(e => e != null),
                _ => null,
            };
            return shown == null ? TextCommandResult.Error($"Could not put down '{what}'.") : TextCommandResult.Success($"Put down {shown.Code.Path} for the shot.");
        }
        Entity made = what switch
        {
            "snake" => Spawn(SnakeCode, Around(at, 3, 6, 1), e => e.WatchedAttributes.SetInt("textureIndex", rand.Next(4))),
            "adder" when quarry != null => PutDownAdder(quarry, quarryId),
            "shuck" when quarry != null => PutDownShuck(quarry, quarryId, 8, 14),
            "pack" when quarry != null => Enumerable.Range(0, ShuckPackHunts).Select(_ => PutDownShuck(quarry, quarryId, 7, 12)).LastOrDefault(),
            "keeper" => PutDownOphion(Around(at, 3, 6, 2), false),
            "walker" => PutDownOphion(Around(at, 3, 6, 2), true),
            "elk" => Spawn("game:deer-moose-adult-male", Around(at, 6, 10, 3)),
            _ => null,
        };
        if (made == null) return TextCommandResult.Error($"Could not put down '{what}' (snake, adder, shuck, pack, keeper, walker, elk; adder, shuck and pack need a player or dummy near).");
        made.AlwaysActive = caller == null;
        return TextCommandResult.Success($"Put down {made.Code.Path} at {made.Pos.X:0},{made.Pos.Y:0},{made.Pos.Z:0}.");
    }
}
