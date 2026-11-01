using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
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
/// Level 14's Hunter ("Patient Zero", Fandom's File 14-E) and its Infecting Agents: who gets one, where it is put down,
/// and the test command. One Hunter per player in the level, at most three in it: a random 150 to 300 seconds after
/// someone comes in (counted while they are in the level), it is put down out of their sight 36 to 60 blocks away, near a
/// torture chamber if there is one ("Torture Chambers indicate that The Hunter is drawing near"). Killed, the next comes
/// 20 to 30 minutes later; gone (nobody within 128 blocks of it for a minute: it is taken away), four to eight minutes of
/// the player's time in the level later. Hunters and Agents are never kept: one loaded from a save (a restart, a chunk
/// coming back) that this run did not put down is taken away at once, so they cannot pile up. Nothing of this is saved.
/// See <see cref="AiTaskL14Hunter"/> and <see cref="AiTaskL14Agent"/> for what they do.
/// </summary>
public class L14HunterSystem : ModSystem
{
    public const string HunterCode = "backrooms:l14-hunter", AgentCode = "backrooms:l14-agent";
    public const string HunterPath = "l14-hunter", AgentPath = "l14-agent";

    /// <summary>Entity attributes: whom it hunts (a player's uid, or a straw dummy's entity id), whose Agent it is.</summary>
    public const string PreyUidKey = "backrooms:l14PreyUid", PreyIdKey = "backrooms:l14PreyId", MotherKey = "backrooms:l14Mother";

    /// <summary>Watched attribute: true while a Hunter chases (the client's atmosphere thickens the smoky dread on it).</summary>
    public const string HuntingKey = "backrooms:l14Hunting";

    /// <summary>The danger the creatures take when the level's own is not set (the director's for a Class 4 level).</summary>
    public const double FallbackDanger = 0.7;

    private const int MaxHunters = 3;
    private const double FirstMin = 150, FirstMax = 300, AgainMin = 240, AgainMax = 480;
    private const long KilledMinMs = 20 * 60_000, KilledMaxMs = 30 * 60_000, FarMs = 60_000;
    private const double FarRange = 128;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private long tick;
    private readonly Random rand = new();

    private sealed class Track
    {
        /// <summary>Seconds in the level, and the count at which the next Hunter comes.</summary>
        public double Seconds, Due;
        /// <summary>Not before this (ElapsedMilliseconds): after a kill.</summary>
        public long NotBeforeMs;
        public long Hunter;
    }

    private readonly Dictionary<string, Track> tracks = new();
    /// <summary>Every Hunter and Agent this run put down and that is still about.</summary>
    private readonly HashSet<long> live = new();
    private readonly Dictionary<long, long> farSince = new();

    public override void Start(ICoreAPI api)
    {
        AiTaskRegistry.Register<AiTaskL14Hunter>("backrooms-l14-hunter");
        AiTaskRegistry.Register<AiTaskL14Agent>("backrooms-l14-agent");
        api.RegisterEntityBehaviorClass("backrooms-l14smoke", typeof(EntityBehaviorL14Smoke));
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
            tick = api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] Level 14 Hunter: {0}", e), 1000, 2000);
            api.Event.OnEntityLoaded += OnEntityLoaded;
            api.Event.OnEntityDeath += OnEntityDeath;
            api.Event.OnEntityDespawn += OnEntityDespawn;
        });

        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l14hunter")
                .WithDescription("Level 14 (testing): 'spawn [x z]' a Hunter near you (or at x z), hunting you; 'show' one 7 blocks in front of you, facing you, calm for 40 s (screenshots); 'agent' an Infecting Agent near you; 'state' every Hunter's state and every player's clock; 'kill' kills every Hunter; 'clear' takes them all away and restarts the clocks. From the console, the latest straw dummy stands in for you")
                .WithArgs(api.ChatCommands.Parsers.Word("what"), api.ChatCommands.Parsers.OptionalInt("x"), api.ChatCommands.Parsers.OptionalInt("z"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnCommand)
            .EndSubCommand();
    }

    public override void Dispose()
    {
        if (sapi == null || layout == null) return;
        if (tick != 0) sapi.Event.UnregisterGameTickListener(tick);
        sapi.Event.OnEntityLoaded -= OnEntityLoaded;
        sapi.Event.OnEntityDeath -= OnEntityDeath;
        sapi.Event.OnEntityDespawn -= OnEntityDespawn;
    }

    /// <summary>Whether a position is in Level 14.</summary>
    public bool InLevel(double x, double z) => layout != null && layout.L14In((int)Math.Floor(x), (int)Math.Floor(z));

    /// <summary>The danger of the level (its director's), or <see cref="FallbackDanger"/> while it is not set.</summary>
    public static double LevelDanger
    {
        get
        {
            double d = Danger.OfLevel(WorldLayout.Level14);
            return d > 0 ? d : FallbackDanger;
        }
    }

    private static bool IsOurs(Entity e) => e?.Code?.Domain == "backrooms" && e.Code.Path is HunterPath or AgentPath;

    /// <summary>Whether something may be hunted: a player in survival (or adventure), or a console test's straw dummy.</summary>
    public static bool Huntable(Entity e) => e is { Alive: true } && (e is EntityPlayer || Senses.IsTestTarget(e)) && !Strike.IsCreative(e) && !Strike.IsSpectator(e);

    /// <summary>Whom a Hunter or an Agent hunts: its player (by uid, so a relog does not lose them), or its straw dummy.</summary>
    public static Entity PreyOf(Entity e)
    {
        string uid = e.Attributes.GetString(PreyUidKey, null);
        if (!string.IsNullOrEmpty(uid)) return e.World.PlayerByUid(uid)?.Entity;
        long id = e.Attributes.GetLong(PreyIdKey, 0);
        return id != 0 ? e.World.GetEntityById(id) : null;
    }

    public static void SetPrey(Entity e, Entity prey)
    {
        e.Attributes.RemoveAttribute(PreyUidKey);
        e.Attributes.RemoveAttribute(PreyIdKey);
        if (prey is EntityPlayer p && p.PlayerUID != null) e.Attributes.SetString(PreyUidKey, p.PlayerUID);
        else if (prey != null) e.Attributes.SetLong(PreyIdKey, prey.EntityId);
    }

    private static string KeyOf(Entity e) => e is EntityPlayer p && p.PlayerUID != null ? p.PlayerUID : "dummy#" + e.EntityId;

    // ================= The clocks =================

    /// <summary>Everyone a Hunter may come for (players, and straw dummies for headless tests), and everyone who keeps one about.</summary>
    private List<Entity> People(bool huntableOnly)
    {
        var who = new List<Entity>();
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
            if (online is IServerPlayer player && player.ConnectionState == EnumClientState.Playing && player.Entity is { Alive: true } entity
                && (!huntableOnly || Huntable(entity)) && !Strike.IsSpectator(entity)) who.Add(entity);
        foreach (Entity e in sapi.World.LoadedEntities.Values)
            if (e.Alive && Senses.IsTestTarget(e)) who.Add(e);
        return who;
    }

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        List<Entity> everyone = People(false);

        // Hunters nobody is near are taken away (after a minute); and anything of ours that is gone from the world is forgotten
        foreach (long id in live.ToArray())
        {
            Entity e = sapi.World.GetEntityById(id);
            if (e == null || !e.Alive)
            {
                if (e == null) live.Remove(id);
                farSince.Remove(id);
                continue;
            }
            if (e.Code.Path != HunterPath) continue;
            bool near = everyone.Any(p => p.Pos.DistanceTo(e.Pos) <= FarRange);
            if (near) { farSince.Remove(id); continue; }
            if (!farSince.TryGetValue(id, out long since)) farSince[id] = since = now;
            if (now - since >= FarMs)
            {
                Strike.Log(e, "taken away: nobody within {0} blocks for a minute", FarRange);
                TakeAway(e);
            }
        }

        foreach (Entity who in everyone)
        {
            if (!Huntable(who)) continue;
            string key = KeyOf(who);
            if (!tracks.TryGetValue(key, out Track t)) tracks[key] = t = new Track { Due = FirstMin + rand.NextDouble() * (FirstMax - FirstMin) };
            if (!InLevel(who.Pos.X, who.Pos.Z)) continue;
            t.Seconds += dt;
            if (t.Hunter != 0)
            {
                if (live.Contains(t.Hunter) && sapi.World.GetEntityById(t.Hunter) is { Alive: true }) continue;
                // Gone without being killed (taken away, unloaded): another comes some minutes on
                t.Hunter = 0;
                t.Due = t.Seconds + AgainMin + rand.NextDouble() * (AgainMax - AgainMin);
            }
            // (One already after them: put down by the test command, or turned on them when its own was gone)
            if (HunterAfter(who) is { } already) { t.Hunter = already.EntityId; continue; }
            if (t.Seconds < t.Due || now < t.NotBeforeMs) continue;
            if (CountHunters() >= MaxHunters) continue;
            if (FindLair(who) is not { } at)
            {
                t.Due = t.Seconds + 5;
                continue;
            }
            Entity hunter = PutDownHunter(at, (float)Math.Atan2(who.Pos.X - at.X, who.Pos.Z - at.Z), who, calm: false, hunting: false, alwaysActive: Senses.IsTestTarget(who));
            if (hunter == null) { t.Due = t.Seconds + 30; continue; }
            t.Hunter = hunter.EntityId;
            Strike.Log(hunter, "comes for {0}, {1:0} blocks off, after {2:0} s in the level", who.Code.Path, hunter.Pos.DistanceTo(who.Pos), t.Seconds);
        }
        // Straw dummies come and go: their clocks with them
        foreach (string key in tracks.Keys.Where(k => k.StartsWith("dummy#", StringComparison.Ordinal)).ToArray())
            if (sapi.World.GetEntityById(long.Parse(key.Substring(6))) is not { Alive: true }) tracks.Remove(key);
    }

    private Entity HunterAfter(Entity who)
    {
        foreach (long id in live)
            if (sapi.World.GetEntityById(id) is { Alive: true } e && e.Code.Path == HunterPath && PreyOf(e) == who) return e;
        return null;
    }

    private int CountHunters() => live.Count(id => sapi.World.GetEntityById(id) is { Alive: true } e && e.Code.Path == HunterPath);

    /// <summary>
    /// Where a Hunter is put down for someone: on walkable floor in the level 36 to 60 blocks off, out of their sight, by a
    /// torture chamber if one is within reach; failing anything out of sight (an open floor), somewhere behind them.
    /// </summary>
    private Vec3d FindLair(Entity prey)
    {
        IWorldAccessor world = sapi.World;
        Vec3d eyes = Senses.Eyes(prey);
        int px = (int)Math.Floor(prey.Pos.X), pz = (int)Math.Floor(prey.Pos.Z), py = (int)Math.Floor(prey.Pos.Y + 0.05);
        (int X, int Z)? torture = layout.L14TortureNear(px, pz, 96);
        Vec3d behind = null;
        for (int tries = 0; tries < 48; tries++)
        {
            double x, z;
            if (torture is { } c && tries < 16)
            {
                x = c.X + 0.5 + (rand.NextDouble() - 0.5) * 10;
                z = c.Z + 0.5 + (rand.NextDouble() - 0.5) * 10;
            }
            else
            {
                double a = rand.NextDouble() * Math.PI * 2, d = 36 + rand.NextDouble() * 24;
                x = prey.Pos.X + Math.Sin(a) * d;
                z = prey.Pos.Z + Math.Cos(a) * d;
            }
            double dist = Math.Sqrt((x - prey.Pos.X) * (x - prey.Pos.X) + (z - prey.Pos.Z) * (z - prey.Pos.Z));
            if (dist < 36 || dist > 60) continue;
            int ix = (int)Math.Floor(x), iz = (int)Math.Floor(z);
            if (!InLevel(ix, iz) || world.BlockAccessor.GetChunkAtBlockPos(new BlockPos(ix, py, iz)) == null) continue;
            int y = Senses.FindFloor(world, ix, py, iz, 2, 8);
            if (y == int.MinValue) continue;
            var spot = new Vec3d(ix + 0.5, y, iz + 0.5);
            if (!Senses.ClearLine(world, eyes, spot.AddCopy(0, 1.4, 0))) return spot;
            if (behind == null && Senses.AngleTo(prey, spot.AddCopy(0, 1.4, 0)) > 100) behind = spot;
        }
        return behind;
    }

    // ================= Putting them down, taking them away =================

    /// <summary>A Hunter at a place hunting someone; calm: still and harmless for 40 s (screenshots); hunting: it shrieks and comes at once.</summary>
    public Entity PutDownHunter(Vec3d at, float yaw, Entity prey, bool calm, bool hunting, bool alwaysActive)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(HunterCode));
        if (type == null) return null;
        Entity e = sapi.World.ClassRegistry.CreateEntity(type);
        e.Pos.SetPos(at);
        e.Pos.Yaw = yaw;
        SetPrey(e, prey);
        double danger = LevelDanger;
        e.Attributes.SetDouble(Danger.Key, danger);
        if (calm) e.Attributes.SetLong(AiTaskL14Hunter.CalmUntilKey, sapi.World.ElapsedMilliseconds + 40_000);
        if (hunting) e.Attributes.SetBool(AiTaskL14Hunter.HuntNowKey, true);
        // (Headless tests: with no player about nothing would think)
        if (alwaysActive) e.AlwaysActive = true;
        sapi.World.SpawnEntity(e);
        live.Add(e.EntityId);
        if (e.GetBehavior<EntityBehaviorHealth>() is { } health && Danger.ExtraHealth(danger) > 0)
        {
            health.SetMaxHealthModifiers("backrooms-danger", health.BaseMaxHealth * Danger.ExtraHealth(danger));
            health.Health = health.MaxHealth;
        }
        Strike.Log(e, "put down for {0} ({1})", prey?.Code.Path ?? "nobody", calm ? "calm" : hunting ? "hunting" : "sensing");
        return e;
    }

    /// <summary>An Infecting Agent at a place, its mother's (or nobody's), hunting someone.</summary>
    public Entity PutDownAgent(Vec3d at, Entity mother, Entity prey)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(AgentCode));
        if (type == null) return null;
        Entity e = sapi.World.ClassRegistry.CreateEntity(type);
        e.Pos.SetPos(at);
        e.Pos.Yaw = prey == null ? (float)(rand.NextDouble() * Math.PI * 2) : (float)Math.Atan2(prey.Pos.X - at.X, prey.Pos.Z - at.Z);
        SetPrey(e, prey);
        if (mother != null) e.Attributes.SetLong(MotherKey, mother.EntityId);
        e.Attributes.SetDouble(Danger.Key, mother?.Attributes.GetDouble(Danger.Key, LevelDanger) ?? LevelDanger);
        if (mother?.AlwaysActive == true || Senses.IsTestTarget(prey)) e.AlwaysActive = true;
        sapi.World.SpawnEntity(e);
        live.Add(e.EntityId);
        return e;
    }

    /// <summary>The live Agents a Hunter has let go.</summary>
    public int AgentsOf(Entity mother) =>
        live.Count(id => sapi.World.GetEntityById(id) is { Alive: true } e && e.Code.Path == AgentPath && e.Attributes.GetLong(MotherKey) == mother.EntityId);

    private void TakeAway(Entity e)
    {
        live.Remove(e.EntityId);
        farSince.Remove(e.EntityId);
        sapi.World.DespawnEntity(e, new EntityDespawnData { Reason = EnumDespawnReason.Expire });
    }

    private void OnEntityLoaded(Entity e)
    {
        if (!IsOurs(e)) return;
        // (Spawned this run: the id is added just after; loaded from a save or a chunk this run lost track of: taken away)
        long id = e.EntityId;
        sapi.Event.RegisterCallback(_ =>
        {
            if (live.Contains(id) || sapi.World.GetEntityById(id) is not { } found || !found.Alive) return;
            sapi.Logger.Notification("[backrooms] Level 14: took away {0} #{1}, left from before", found.Code.Path, id);
            sapi.World.DespawnEntity(found, new EntityDespawnData { Reason = EnumDespawnReason.Removed });
        }, 500);
    }

    private void OnEntityDeath(Entity e, DamageSource source)
    {
        if (e?.Code?.Path != HunterPath || e.Code.Domain != "backrooms") return;
        long now = sapi.World.ElapsedMilliseconds;
        foreach (Track t in tracks.Values)
        {
            if (t.Hunter != e.EntityId) continue;
            t.Hunter = 0;
            t.NotBeforeMs = now + KilledMinMs + (long)(rand.NextDouble() * (KilledMaxMs - KilledMinMs));
            t.Due = t.Seconds;
        }
        e.WatchedAttributes.SetBool(HuntingKey, false);
        Strike.Log(e, "killed by {0}", source?.GetCauseEntity()?.Code?.Path ?? "something");
    }

    private void OnEntityDespawn(Entity e, EntityDespawnData data)
    {
        if (!IsOurs(e)) return;
        live.Remove(e.EntityId);
        farSince.Remove(e.EntityId);
    }

    // ================= Testing =================

    private Entity LatestDummy()
    {
        Entity latest = null;
        foreach (Entity e in sapi.World.LoadedEntities.Values)
            if (e.Alive && Senses.IsTestTarget(e) && (latest == null || e.EntityId > latest.EntityId)) latest = e;
        return latest;
    }

    /// <summary>Open floor near a point, along a heading first and then round it, `d` blocks out; null if none.</summary>
    private Vec3d FloorNear(Entity from, double yaw, double d)
    {
        int py = (int)Math.Floor(from.Pos.Y + 0.05);
        for (int i = 0; i < 12; i++)
        {
            double a = yaw + (i == 0 ? 0 : (i % 2 == 0 ? 1 : -1) * ((i + 1) / 2) * Math.PI / 6);
            double x = from.Pos.X + Math.Sin(a) * d, z = from.Pos.Z + Math.Cos(a) * d;
            int y = Senses.FindFloor(sapi.World, (int)Math.Floor(x), py, (int)Math.Floor(z), 2, 4);
            if (y != int.MinValue) return new Vec3d(Math.Floor(x) + 0.5, y, Math.Floor(z) + 0.5);
        }
        return null;
    }

    private TextCommandResult OnCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string what = (string)args[0];
        Entity caller = args.Caller.Entity;
        Entity me = caller ?? LatestDummy();
        bool hasXz = !args.Parsers[1].IsMissing && !args.Parsers[2].IsMissing;
        bool console = caller == null;
        switch (what)
        {
            case "spawn":
            {
                if (me == null && !hasXz) return TextCommandResult.Error("From the console, put a straw dummy down first (or give x z)");
                Vec3d at;
                if (hasXz)
                {
                    int x = (int)args[1], z = (int)args[2];
                    int y = Senses.FindFloor(sapi.World, x, me != null ? (int)Math.Floor(me.Pos.Y + 0.05) : sapi.World.SeaLevel, z, 2, 12);
                    if (y == int.MinValue) return TextCommandResult.Error("No floor there (or its chunk is not loaded)");
                    at = new Vec3d(x + 0.5, y, z + 0.5);
                }
                else at = FloorNear(me, me.Pos.Yaw, 10);
                if (at == null) return TextCommandResult.Error("No open floor about 10 blocks from you");
                if (!InLevel(at.X, at.Z)) return TextCommandResult.Error("Not in Level 14");
                float yaw = me == null ? 0 : (float)Math.Atan2(me.Pos.X - at.X, me.Pos.Z - at.Z);
                Entity e = PutDownHunter(at, yaw, me, calm: false, hunting: me != null, alwaysActive: console);
                if (e == null) return TextCommandResult.Error("No Hunter type");
                if (me != null && tracks.TryGetValue(KeyOf(me), out Track t)) t.Hunter = e.EntityId;
                else if (me != null && Huntable(me)) tracks[KeyOf(me)] = new Track { Hunter = e.EntityId, Due = FirstMin };
                return TextCommandResult.Success($"A Hunter at {at.X:0}, {at.Y:0}, {at.Z:0} (#{e.EntityId}), hunting {me?.Code.Path ?? "nobody"}");
            }
            case "show":
            {
                if (me == null) return TextCommandResult.Error("Needs a player, or a straw dummy put down first");
                // (Along the way they look: the view vector, whatever the yaw's convention)
                Vec3f view = (caller ?? me).Pos.GetViewVector();
                double yaw = Math.Atan2(view.X, view.Z);
                Vec3d at = FloorNear(me, yaw, 7);
                if (at == null) return TextCommandResult.Error("No open floor 7 blocks in front of you");
                Entity e = PutDownHunter(at, (float)Math.Atan2(me.Pos.X - at.X, me.Pos.Z - at.Z), me, calm: true, hunting: false, alwaysActive: console);
                return e == null ? TextCommandResult.Error("No Hunter type") : TextCommandResult.Success($"A Hunter stands at {at.X:0}, {at.Y:0}, {at.Z:0} (#{e.EntityId}), calm for 40 s");
            }
            case "agent":
            {
                if (me == null) return TextCommandResult.Error("Needs a player, or a straw dummy put down first");
                Vec3d at = FloorNear(me, me.Pos.Yaw, 4);
                if (at == null) return TextCommandResult.Error("No open floor near you");
                Entity e = PutDownAgent(at, null, me);
                return e == null ? TextCommandResult.Error("No Agent type") : TextCommandResult.Success($"An Infecting Agent at {at.X:0}, {at.Y:0}, {at.Z:0} (#{e.EntityId})");
            }
            case "state":
            {
                var lines = new List<string>();
                foreach (long id in live)
                {
                    if (sapi.World.GetEntityById(id) is not { } e) continue;
                    Entity prey = PreyOf(e);
                    string health = e.GetBehavior<EntityBehaviorHealth>() is { } h ? $"{h.Health:0.#}/{h.MaxHealth:0.#}" : "?";
                    lines.Add($"{e.Code.Path} #{id} at {e.Pos.X:0},{e.Pos.Y:0},{e.Pos.Z:0} {(e.Alive ? "" : "(dead) ")}health {health}: "
                              + $"{e.Attributes.GetString(AiTaskL14Hunter.StateKey, "?")}; hunting {(e.WatchedAttributes.GetBool(HuntingKey) ? "yes" : "no")}; "
                              + $"prey {(prey == null ? "none" : $"{prey.Code.Path} #{prey.EntityId}, {prey.Pos.DistanceTo(e.Pos):0.0} blocks")}");
                }
                long now = sapi.World.ElapsedMilliseconds;
                foreach (var (key, t) in tracks)
                    lines.Add($"clock {key}: {t.Seconds:0} s in the level, next due at {t.Due:0} s{(t.NotBeforeMs > now ? $", not for {(t.NotBeforeMs - now) / 1000} s (killed)" : "")}, hunter #{t.Hunter}");
                if (lines.Count == 0) lines.Add("No Hunters, no Agents, no clocks");
                string text = string.Join("\n", lines);
                sapi.Logger.Notification("[backrooms] l14hunter state:\n{0}", text);
                return TextCommandResult.Success(text);
            }
            case "kill":
            {
                // (Testing the death, the decay and the clock after a kill)
                int n = 0;
                foreach (Entity e in sapi.World.LoadedEntities.Values.Where(e => e.Alive && e.Code?.Path == HunterPath).ToArray())
                {
                    e.Die(EnumDespawnReason.Death, new DamageSource { Source = EnumDamageSource.Player, Type = EnumDamageType.PiercingAttack });
                    n++;
                }
                return TextCommandResult.Success($"Killed {n} Hunter(s)");
            }
            case "clear":
            {
                int n = 0;
                foreach (Entity e in sapi.World.LoadedEntities.Values.Where(IsOurs).ToArray())
                {
                    TakeAway(e);
                    n++;
                }
                foreach (Track t in tracks.Values)
                {
                    t.Hunter = 0;
                    t.NotBeforeMs = 0;
                    t.Due = t.Seconds + FirstMin + rand.NextDouble() * (FirstMax - FirstMin);
                }
                return TextCommandResult.Success($"Took away {n}; the clocks start over");
            }
        }
        return TextCommandResult.Error("spawn [x z], show, agent, state, kill or clear");
    }
}

/// <summary>
/// The Hunter ("Patient Zero"): "its main objective is to hunt down any wanderers"; "he seemingly could sense whether someone
/// was nearby". It always knows roughly where its player is: a point near them, picked again every 20 s, nearer the truth
/// the nearer it is (Roam, a slow haul along the floor, a wet breath that carries 16 blocks: the dread). Within 24 blocks
/// and unseen it Stalks, slower and quieter, homing in. Seeing them within 20 blocks, or met eye to eye ("Once you make eye
/// contact with The Hunter, there is no hope": their view within 10 degrees of it, a clear line, within 32 blocks), it
/// shrieks and Chases: for five seconds a little faster than a sprint, then about a sprint. Its tentacles lash and drag
/// (the blow pulls its prey in rather than knocking them away), and every 10 to 15 s of a chase its tentacles' mouths let go
/// one or two Infecting Agents (four alive at most). Out of sight 20 s and more than 32 blocks off, it has lost them: it goes
/// back to sensing. Struck, it turns on whoever struck it. Speeds, damage, cooldowns and health scale with the level's danger.
/// </summary>
public class AiTaskL14Hunter : AiTaskBase
{
    public const string CalmUntilKey = "backrooms:l14CalmUntil", HuntNowKey = "backrooms:l14HuntNow", StateKey = "backrooms:l14State";

    private enum State { Roam, Stalk, Shriek, Chase, Calm }

    private readonly float roamSpeed, stalkSpeed, burstSpeed, chaseSpeed, stalkRange, sightRange, eyeRange, eyeDegrees, loseRange,
        attackRange, damage, pull, senseErrorMin, senseErrorMax;
    private readonly int senseEveryMs, stalkEveryMs, burstMs, shriekMs, loseMs, damageTier, attackDurationMs, damageAtMs, attackCooldownMs,
        agentEveryMinMs, agentEveryMaxMs, agentCap;
    private readonly AssetLocation[] breathSounds, dragSounds;
    private readonly AssetLocation shriekSound, lashSound, releaseSound;

    private L14HunterSystem system;
    private State state;
    private Entity target;
    private float think, nextBreath = 3, nextDrag;
    private long stateSinceMs, attackStartMs = -1, lastAttackMs, lastPathMs, lastSeenMs, nextSenseMs, burstUntilMs, nextAgentMs, straightUntilMs;
    private bool damageDone, started, moving, running, burstPathed, eyeContact;
    private double speedMul = 1, damageMul = 1, cooldownMul = 1;
    private int tierBonus;
    private Vec3d chasing;

    public AiTaskL14Hunter(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        roamSpeed = taskConfig["roamSpeed"].AsFloat(0.014f);
        stalkSpeed = taskConfig["stalkSpeed"].AsFloat(0.011f);
        burstSpeed = taskConfig["burstSpeed"].AsFloat(0.047f);
        chaseSpeed = taskConfig["chaseSpeed"].AsFloat(0.041f);
        senseEveryMs = taskConfig["senseEveryMs"].AsInt(20000);
        stalkEveryMs = taskConfig["stalkEveryMs"].AsInt(5000);
        senseErrorMin = taskConfig["senseErrorMin"].AsFloat(3);
        senseErrorMax = taskConfig["senseErrorMax"].AsFloat(24);
        stalkRange = taskConfig["stalkRange"].AsFloat(24);
        sightRange = taskConfig["sightRange"].AsFloat(20);
        eyeRange = taskConfig["eyeContactRange"].AsFloat(32);
        eyeDegrees = taskConfig["eyeContactDegrees"].AsFloat(10);
        burstMs = taskConfig["burstMs"].AsInt(5000);
        shriekMs = taskConfig["shriekMs"].AsInt(900);
        loseMs = taskConfig["loseMs"].AsInt(20000);
        loseRange = taskConfig["loseRange"].AsFloat(32);
        attackRange = taskConfig["attackRange"].AsFloat(2.5f);
        damage = taskConfig["damage"].AsFloat(4.2f);
        damageTier = taskConfig["damageTier"].AsInt(2);
        pull = taskConfig["pull"].AsFloat(0.14f);
        attackDurationMs = taskConfig["attackDurationMs"].AsInt(1000);
        damageAtMs = taskConfig["damageAtMs"].AsInt(430);
        attackCooldownMs = taskConfig["attackCooldownMs"].AsInt(1800);
        agentEveryMinMs = taskConfig["agentEveryMinMs"].AsInt(10000);
        agentEveryMaxMs = taskConfig["agentEveryMaxMs"].AsInt(15000);
        agentCap = taskConfig["agentCap"].AsInt(4);
        breathSounds = Sounds(taskConfig["breathSounds"]);
        dragSounds = Sounds(taskConfig["dragSounds"]);
        shriekSound = Sound(taskConfig["shriekSound"].AsString(null));
        lashSound = Sound(taskConfig["lashSound"].AsString(null));
        releaseSound = Sound(taskConfig["releaseSound"].AsString(null));
    }

    internal static AssetLocation Sound(string code) => code == null ? null : AssetLocation.Create(code, "backrooms").WithPathPrefixOnce("sounds/");

    internal static AssetLocation[] Sounds(JsonObject list) => (list.AsArray<string>() ?? Array.Empty<string>()).Select(Sound).Where(s => s != null).ToArray();

    public override bool ShouldExecute() => entity.Alive;

    public override void StartExecute()
    {
        base.StartExecute();
        if (started) return;
        started = true;
        system = entity.Api.ModLoader.GetModSystem<L14HunterSystem>();
        double d = Danger.Of(entity);
        speedMul = Danger.Speed(d);
        damageMul = Danger.Damage(d);
        cooldownMul = Danger.Cooldown(d);
        tierBonus = Danger.TierBonus(d);
        long now = entity.World.ElapsedMilliseconds;
        target = L14HunterSystem.PreyOf(entity);
        if (entity.Attributes.GetLong(CalmUntilKey) > now) SetState(State.Calm);
        else if (entity.Attributes.GetBool(HuntNowKey) && target != null)
        {
            entity.Attributes.RemoveAttribute(HuntNowKey);
            Shriek("put down hunting");
        }
        else SetState(State.Roam);
        nextAgentMs = now + agentEveryMinMs;
        if (state is State.Calm or State.Roam) entity.AnimManager.StartAnimation("lurk");
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        long now = entity.World.ElapsedMilliseconds;
        Noises(dt);
        if (attackStartMs >= 0)
        {
            ContinueAttack(now);
            return true;
        }
        if (target != null && state is State.Shriek or State.Calm) TurnTowards(target.Pos.XYZ, dt, state == State.Shriek ? 6f : 1.5f);

        think -= dt;
        if (think > 0) return true;
        think = 0.25f;

        switch (state)
        {
            case State.Calm:
                if (now >= entity.Attributes.GetLong(CalmUntilKey))
                {
                    entity.Attributes.RemoveAttribute(CalmUntilKey);
                    SetState(State.Roam);
                    nextSenseMs = now;
                }
                return true;

            case State.Shriek:
                if (now - stateSinceMs >= shriekMs)
                {
                    entity.AnimManager.StopAnimation("shriek");
                    SetState(State.Chase);
                    burstUntilMs = now + burstMs;
                    burstPathed = false;
                    lastSeenMs = now;
                    chasing = null;
                }
                return true;

            case State.Chase:
                Chase(now);
                return true;

            default:
                Sense(now);
                return true;
        }
    }

    // ================= Sensing =================

    private Entity Prey()
    {
        Entity prey = L14HunterSystem.PreyOf(entity);
        if (L14HunterSystem.Huntable(prey) && (system == null || system.InLevel(prey.Pos.X, prey.Pos.Z))) return prey;
        // Its own gone (dead, away, out of the level): whoever is nearest within 48 blocks in the level
        Entity best = null;
        double bestD = 48;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, 48, 12, e => L14HunterSystem.Huntable(e)))
        {
            double d = e.Pos.DistanceTo(entity.Pos);
            if (d < bestD && (system == null || system.InLevel(e.Pos.X, e.Pos.Z))) { best = e; bestD = d; }
        }
        if (best != null) L14HunterSystem.SetPrey(entity, best);
        return best;
    }

    /// <summary>Roam and Stalk: it homes in on where it senses its prey, and turns to the chase when it sees them or they meet its eyes.</summary>
    private void Sense(long now)
    {
        target = Prey();
        if (target == null)
        {
            if (moving) Stop();
            return;
        }
        double d = entity.Pos.DistanceTo(target.Pos);
        if (d <= eyeRange)
        {
            bool line = Senses.ClearLine(entity.World, Senses.Eyes(entity), Senses.Eyes(target));
            if (line && Senses.LooksAt(target, Senses.Eyes(entity), eyeDegrees))
            {
                eyeContact = true;
                Shriek("eye contact");
                return;
            }
            if (line && d <= sightRange && (d <= 8 || Facing(target.Pos.XYZ) < 70))
            {
                eyeContact = false;
                Shriek("sees it");
                return;
            }
        }
        if (state == State.Roam && d <= stalkRange) { SetState(State.Stalk); nextSenseMs = now; }
        else if (state == State.Stalk && d > stalkRange + 8) { SetState(State.Roam); nextSenseMs = now; }

        if (now >= nextSenseMs || !pathTraverser.Active && now - lastPathMs > 4000)
        {
            bool stalk = state == State.Stalk;
            double err = stalk ? 2.5 : Math.Clamp(d * 0.3, senseErrorMin, senseErrorMax);
            Vec3d point = Near(target.Pos.XYZ, err);
            nextSenseMs = now + (stalk ? stalkEveryMs : senseEveryMs);
            Go(point, stalk ? stalkSpeed : roamSpeed, 1.5f, 6000);
        }
    }

    /// <summary>A walkable point within some blocks of a place (in the level), or the place itself.</summary>
    private Vec3d Near(Vec3d at, double err)
    {
        var rand = entity.World.Rand;
        for (int i = 0; i < 8; i++)
        {
            double a = rand.NextDouble() * Math.PI * 2, r = Math.Sqrt(rand.NextDouble()) * err;
            int x = (int)Math.Floor(at.X + Math.Sin(a) * r), z = (int)Math.Floor(at.Z + Math.Cos(a) * r);
            if (system != null && !system.InLevel(x, z)) continue;
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(at.Y + 0.05), z, 2, 4);
            if (y != int.MinValue) return new Vec3d(x + 0.5, y, z + 0.5);
        }
        return at.Clone();
    }

    /// <summary>The angle (degrees) between where it faces and a point.</summary>
    private double Facing(Vec3d point)
    {
        double want = Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);
        return Math.Abs(GameMath.AngleRadDistance(entity.Pos.Yaw, (float)want)) * 180 / Math.PI;
    }

    private void Shriek(string why)
    {
        Stop();
        SetState(State.Shriek);
        SetHunting(true);
        entity.AnimManager.StopAnimation("lurk");
        entity.AnimManager.StartAnimation("shriek");
        if (shriekSound != null) entity.World.PlaySoundAt(shriekSound, entity.Pos.X, entity.Pos.Y + 1.6, entity.Pos.Z, null, 0.92f + (float)entity.World.Rand.NextDouble() * 0.16f, 48, 1f);
        Strike.Log(entity, "shrieks: {0} ({1})", why, target?.Code.Path ?? "nobody");
    }

    private void Lose(string why)
    {
        Strike.Log(entity, "loses {0}: {1}", target?.Code.Path ?? "nobody", why);
        Stop();
        SetState(State.Roam);
        SetHunting(false);
        nextSenseMs = entity.World.ElapsedMilliseconds;
        eyeContact = false;
    }

    // ================= The chase =================

    private void Chase(long now)
    {
        Entity prey = L14HunterSystem.PreyOf(entity);
        if (L14HunterSystem.Huntable(prey) && (system == null || system.InLevel(prey.Pos.X, prey.Pos.Z))) target = prey;
        if (!L14HunterSystem.Huntable(target) || system != null && !system.InLevel(target.Pos.X, target.Pos.Z)) { Lose("gone"); return; }

        double distance = entity.Pos.DistanceTo(target.Pos);
        bool line = distance < 64 && Senses.ClearLine(entity.World, Senses.Eyes(entity), Senses.Centre(target));
        if (line) lastSeenMs = now;
        if (now - lastSeenMs > loseMs && distance > loseRange) { Lose("out of sight and far"); return; }
        if (distance > 96) { Lose("too far"); return; }

        // Its tentacles let go of Infecting Agents
        if (now >= nextAgentMs)
        {
            nextAgentMs = now + agentEveryMinMs + entity.World.Rand.Next(Math.Max(1, agentEveryMaxMs - agentEveryMinMs));
            Release();
        }

        double gap = distance - (entity.CollisionBox.XSize + target.CollisionBox.XSize) / 2;
        double dy = Math.Abs(target.Pos.Y - entity.Pos.Y);
        if (gap <= attackRange && dy < 2 && now - lastAttackMs > attackCooldownMs * cooldownMul && line)
        {
            StartAttack(now);
            return;
        }
        if (gap <= attackRange * 0.6)
        {
            Stop();
            return;
        }
        float speed = now < burstUntilMs ? burstSpeed : chaseSpeed;
        bool burstOver = now >= burstUntilMs && !burstPathed;
        if (burstOver) burstPathed = true;
        float within = attackRange * 0.6f + (entity.CollisionBox.XSize + target.CollisionBox.XSize) / 2;
        bool moved = chasing == null || chasing.SquareDistanceTo(target.Pos.X, target.Pos.Y, target.Pos.Z) >= 9;
        if (now < straightUntilMs)
        {
            if (!pathTraverser.Active || now - lastPathMs > 750 || burstOver)
            {
                lastPathMs = now;
                SetMoving(true, true);
                pathTraverser.WalkTowards(target.Pos.XYZ.Clone(), speed * (float)speedMul, within, OnArrived, OnArrived);
            }
        }
        else if (!pathTraverser.Active && now - lastPathMs > 600 || moved && now - lastPathMs > 750 || burstOver)
        {
            chasing = target.Pos.XYZ;
            Go(chasing, speed, within, 2500);
        }
        else
        {
            pathTraverser.CurrentTarget.X = target.Pos.X;
            pathTraverser.CurrentTarget.Y = target.Pos.Y;
            pathTraverser.CurrentTarget.Z = target.Pos.Z;
        }
    }

    /// <summary>One or two Infecting Agents from the tentacles' mouths, by its sides (four of its own alive at most).</summary>
    private void Release()
    {
        if (system == null || entity.Api.Side != EnumAppSide.Server) return;
        int room = agentCap - system.AgentsOf(entity);
        if (room <= 0) return;
        var rand = entity.World.Rand;
        int n = Math.Min(room, 1 + rand.Next(2)), made = 0;
        IBlockAccessor ba = entity.World.BlockAccessor;
        for (int i = 0; i < 8 && made < n; i++)
        {
            double a = rand.NextDouble() * Math.PI * 2, r = 0.9 + rand.NextDouble() * 0.8;
            double x = entity.Pos.X + Math.Sin(a) * r, z = entity.Pos.Z + Math.Cos(a) * r;
            var feet = new BlockPos((int)Math.Floor(x), (int)Math.Floor(entity.Pos.Y + 0.05), (int)Math.Floor(z));
            if (!Senses.Open(ba, feet) || Senses.Open(ba, feet.DownCopy())) continue;
            if (system.PutDownAgent(new Vec3d(x, feet.Y, z), entity, target) != null) made++;
        }
        if (made > 0)
        {
            if (releaseSound != null) entity.World.PlaySoundAt(releaseSound, entity.Pos.X, entity.Pos.Y + 0.8, entity.Pos.Z, null, 0.9f + (float)rand.NextDouble() * 0.2f, 16, 1f);
            Strike.Log(entity, "lets go of {0} Infecting Agent(s)", made);
        }
    }

    private void StartAttack(long now)
    {
        Stop();
        attackStartMs = now;
        damageDone = false;
        entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
        entity.AnimManager.StartAnimation("attack");
    }

    private void ContinueAttack(long now)
    {
        long elapsed = now - attackStartMs;
        if (target != null) TurnTowards(target.Pos.XYZ, 0.05f, 5f);
        if (!damageDone && elapsed >= damageAtMs)
        {
            damageDone = true;
            if (lashSound != null) entity.World.PlaySoundAt(lashSound, entity.Pos.X, entity.Pos.Y + 1, entity.Pos.Z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.2f, 20, 1f);
            double gap = target == null ? 99 : entity.Pos.DistanceTo(target.Pos) - (entity.CollisionBox.XSize + target.CollisionBox.XSize) / 2;
            if (target != null && target.Alive && gap <= attackRange + 0.5 && !Strike.IsCreative(target))
            {
                Strike.Hit(entity, target, damage * (float)damageMul, EnumDamageType.SlashingAttack, damageTier + tierBonus, 0);
                Drag(target);
                lastSeenMs = now;
            }
        }
        if (elapsed >= attackDurationMs)
        {
            entity.AnimManager.StopAnimation("attack");
            attackStartMs = -1;
            lastAttackMs = now;
        }
    }

    /// <summary>
    /// The tentacles grab and drag: the blow's knockback is turned round, toward the Hunter ("drag those who wander too
    /// close to his grasp"). A player's own client moves them, so the pull goes out as the knockback the game sends with
    /// every blow (kbdirX/Y/Z, applied by the client's physics once per hurt); anything else is pulled here.
    /// </summary>
    private void Drag(Entity who)
    {
        if (!who.Alive) return;
        double dx = entity.Pos.X - who.Pos.X, dz = entity.Pos.Z - who.Pos.Z;
        double len = Math.Sqrt(dx * dx + dz * dz);
        if (len < 0.2) return;
        double k = pull * GameMath.Clamp((len - 1.0) / 2.0, 0, 1);
        if (k <= 0) return;
        if (who is EntityPlayer)
        {
            who.WatchedAttributes.SetDouble("kbdirX", dx / len * k);
            who.WatchedAttributes.SetDouble("kbdirY", 0.05);
            who.WatchedAttributes.SetDouble("kbdirZ", dz / len * k);
        }
        else who.Pos.Motion.Add(dx / len * k, 0.05, dz / len * k);
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        if (!entity.Alive || state == State.Calm) return;
        Entity cause = source.GetCauseEntity();
        if (!L14HunterSystem.Huntable(cause)) return;
        // Struck, it turns on whoever struck it
        if (state is State.Roam or State.Stalk)
        {
            L14HunterSystem.SetPrey(entity, cause);
            target = cause;
            Shriek("struck");
        }
        else if (state == State.Chase) lastSeenMs = entity.World.ElapsedMilliseconds;
    }

    // ================= Noises =================

    /// <summary>The wet breath (every few seconds, carrying 16 blocks; quieter stalking, harder in a chase) and the drag of its body as it moves.</summary>
    private void Noises(float dt)
    {
        var rand = entity.World.Rand;
        nextBreath -= dt;
        if (nextBreath <= 0 && breathSounds.Length > 0)
        {
            bool chase = state is State.Chase or State.Shriek;
            nextBreath = chase ? 2.5f + (float)rand.NextDouble() * 1.5f : 4.5f + (float)rand.NextDouble() * 3f;
            float volume = state == State.Stalk ? 0.55f : chase ? 1f : 0.85f;
            entity.World.PlaySoundAt(breathSounds[rand.Next(breathSounds.Length)], entity.Pos.X, entity.Pos.Y + 1.6, entity.Pos.Z, null,
                0.9f + (float)rand.NextDouble() * 0.2f, chase ? 24 : 16, volume);
        }
        if (!moving || dragSounds.Length == 0) return;
        nextDrag -= dt;
        if (nextDrag > 0) return;
        nextDrag = running ? 0.45f : 0.95f;
        entity.World.PlaySoundAt(dragSounds[rand.Next(dragSounds.Length)], entity.Pos.X, entity.Pos.Y + 0.3, entity.Pos.Z, null,
            (running ? 1.05f : 0.9f) + (float)rand.NextDouble() * 0.15f, running ? 16 : 12, state == State.Stalk ? 0.5f : 0.85f);
    }

    // ================= Going =================

    private void Go(Vec3d to, float speed, float within, int depth)
    {
        lastPathMs = entity.World.ElapsedMilliseconds;
        SetMoving(true, speed >= chaseSpeed * 0.75f);
        pathTraverser.Stop();
        pathTraverser.NavigateTo_Async(to.Clone(), speed * (float)speedMul, within, OnArrived, OnArrived, OnNoPath, depth, 1);
    }

    private void OnArrived() => SetMoving(false, false);

    private void OnNoPath()
    {
        SetMoving(false, false);
        if (state == State.Chase) straightUntilMs = entity.World.ElapsedMilliseconds + 3000;
    }

    private void Stop()
    {
        pathTraverser.Stop();
        SetMoving(false, false);
    }

    private void SetMoving(bool on, bool run)
    {
        if (on == moving && run == running) return;
        if (moving) entity.AnimManager.StopAnimation(running ? "run" : "walk");
        moving = on;
        running = on && run;
        if (moving)
        {
            entity.AnimManager.StopAnimation("lurk");
            entity.AnimManager.StartAnimation(running ? "run" : "walk");
            nextDrag = 0.1f;
        }
        // Stopped while it senses: it holds still and feels for them
        else if (state is State.Roam or State.Stalk or State.Calm) entity.AnimManager.StartAnimation("lurk");
    }

    private void SetState(State next)
    {
        state = next;
        stateSinceMs = entity.World.ElapsedMilliseconds;
        if (next is State.Chase or State.Shriek) entity.AnimManager.StopAnimation("lurk");
        entity.Attributes.SetString(StateKey, next.ToString().ToLowerInvariant() + (next is State.Chase or State.Shriek && eyeContact ? " (eye contact)" : ""));
    }

    private void SetHunting(bool on)
    {
        if (entity.WatchedAttributes.GetBool(L14HunterSystem.HuntingKey) != on) entity.WatchedAttributes.SetBool(L14HunterSystem.HuntingKey, on);
    }

    private void TurnTowards(Vec3d point, float dt, float rate)
    {
        float desired = (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float step = rate * dt;
        entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -step, step)) % GameMath.TWOPI;
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Stop();
        entity.AnimManager.StopAnimation("attack");
        if (!entity.Alive) SetHunting(false);
    }
}

/// <summary>
/// An Infecting Agent: "small, worm-like creatures that squirm along the ground extremely swiftly ... a mouth that is filled
/// with rows of sharp, razor teeth ... the ability to spit out radioactive substances ... from corrosive acids to life-ending
/// toxins". Let go by a Hunter in a chase (or put down by the test command), it rushes its Hunter's prey (or the nearest
/// player): a bite that leaves a poison burning on (the Deathmoth venom's, <see cref="VenomSystem.Envenom"/>), and now and
/// then, from a few blocks off, a glob of something corrosive spat at where they stand (a moment in the air: step aside
/// and it misses). It dies off after about 40 seconds.
/// </summary>
public class AiTaskL14Agent : AiTaskBase
{
    private readonly float speed, biteRange, damage, spitDamage, spitMin, spitMax, globSpeed;
    private readonly int damageTier, biteCooldownMs, biteDurationMs, biteAtMs, spitEveryMs, lifeMs;
    private readonly AssetLocation[] chitterSounds;
    private readonly AssetLocation biteSound, spitSound, sizzleSound;

    private L14HunterSystem system;
    private Entity target;
    private float think, nextChitter = 0.5f;
    private long bornMs, attackStartMs = -1, lastAttackMs, lastPathMs, nextSpitMs, spitStartMs = -1;
    private bool damageDone, started, moving;
    private double speedMul = 1, damageMul = 1, cooldownMul = 1;
    private int tierBonus;

    public AiTaskL14Agent(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        speed = taskConfig["speed"].AsFloat(0.055f);
        biteRange = taskConfig["biteRange"].AsFloat(0.7f);
        damage = taskConfig["damage"].AsFloat(0.9f);
        damageTier = taskConfig["damageTier"].AsInt(1);
        biteCooldownMs = taskConfig["biteCooldownMs"].AsInt(1300);
        biteDurationMs = taskConfig["biteDurationMs"].AsInt(500);
        biteAtMs = taskConfig["biteAtMs"].AsInt(230);
        spitDamage = taskConfig["spitDamage"].AsFloat(0.6f);
        spitMin = taskConfig["spitMin"].AsFloat(3);
        spitMax = taskConfig["spitMax"].AsFloat(8);
        spitEveryMs = taskConfig["spitEveryMs"].AsInt(6000);
        globSpeed = taskConfig["globSpeed"].AsFloat(12);
        lifeMs = taskConfig["lifeMs"].AsInt(40000);
        chitterSounds = AiTaskL14Hunter.Sounds(taskConfig["chitterSounds"]);
        biteSound = AiTaskL14Hunter.Sound(taskConfig["biteSound"].AsString(null));
        spitSound = AiTaskL14Hunter.Sound(taskConfig["spitSound"].AsString(null));
        sizzleSound = AiTaskL14Hunter.Sound(taskConfig["sizzleSound"].AsString(null));
    }

    public override bool ShouldExecute() => entity.Alive;

    public override void StartExecute()
    {
        base.StartExecute();
        if (started) return;
        started = true;
        system = entity.Api.ModLoader.GetModSystem<L14HunterSystem>();
        bornMs = entity.World.ElapsedMilliseconds;
        nextSpitMs = bornMs + 2500 + entity.World.Rand.Next(3000);
        double d = Danger.Of(entity);
        speedMul = Danger.Speed(d);
        damageMul = Danger.Damage(d);
        cooldownMul = Danger.Cooldown(d);
        tierBonus = Danger.TierBonus(d);
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        long now = entity.World.ElapsedMilliseconds;
        Chitter(dt);
        if (attackStartMs >= 0) { ContinueBite(now); return true; }
        if (spitStartMs >= 0) { ContinueSpit(now); return true; }

        think -= dt;
        if (think > 0) return true;
        think = 0.2f;

        // Short-lived: it dies off
        if (now - bornMs > lifeMs)
        {
            Strike.Log(entity, "dies off");
            entity.Die(EnumDespawnReason.Death, new DamageSource { Source = EnumDamageSource.Internal, Type = EnumDamageType.Hunger });
            return false;
        }

        target = Target();
        if (target == null)
        {
            entity.Attributes.SetString(AiTaskL14Hunter.StateKey, "nobody to rush");
            Stop();
            return true;
        }
        double distance = entity.Pos.DistanceTo(target.Pos);
        double gap = distance - (entity.CollisionBox.XSize + target.CollisionBox.XSize) / 2;
        double dy = Math.Abs(target.Pos.Y - entity.Pos.Y);
        entity.Attributes.SetString(AiTaskL14Hunter.StateKey, $"rush, {gap:0.0} blocks off, {(lifeMs - (now - bornMs)) / 1000} s to live");
        if (gap <= biteRange && dy < 1.6 && now - lastAttackMs > biteCooldownMs * cooldownMul)
        {
            Stop();
            attackStartMs = now;
            damageDone = false;
            entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
            entity.AnimManager.StartAnimation("attack");
            return true;
        }
        if (now >= nextSpitMs && gap >= spitMin && gap <= spitMax && dy < 3
            && Senses.ClearLine(entity.World, entity.Pos.XYZ.Add(0, 0.3, 0), Senses.Centre(target)))
        {
            Stop();
            spitStartMs = now;
            damageDone = false;
            nextSpitMs = now + spitEveryMs + entity.World.Rand.Next(spitEveryMs / 2);
            entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
            entity.AnimManager.StartAnimation("spit");
            return true;
        }
        if (gap <= biteRange * 0.7) { Stop(); return true; }
        if (!pathTraverser.Active || now - lastPathMs > 700)
        {
            lastPathMs = now;
            if (!moving)
            {
                moving = true;
                entity.AnimManager.StartAnimation("run");
            }
            pathTraverser.NavigateTo_Async(target.Pos.XYZ.Clone(), speed * (float)speedMul, biteRange * 0.6f + 0.4f, OnArrived, OnArrived, OnNoPath, 900, 1);
        }
        else
        {
            pathTraverser.CurrentTarget.X = target.Pos.X;
            pathTraverser.CurrentTarget.Y = target.Pos.Y;
            pathTraverser.CurrentTarget.Z = target.Pos.Z;
        }
        return true;
    }

    /// <summary>Its Hunter's prey if it is near; otherwise the nearest one about.</summary>
    private Entity Target()
    {
        Entity prey = L14HunterSystem.PreyOf(entity);
        if (L14HunterSystem.Huntable(prey) && prey.Pos.DistanceTo(entity.Pos) < 40) return prey;
        Entity best = null;
        double bestD = 32;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, 32, 8, e => L14HunterSystem.Huntable(e)))
        {
            double d = e.Pos.DistanceTo(entity.Pos);
            if (d < bestD) { best = e; bestD = d; }
        }
        if (best != null) L14HunterSystem.SetPrey(entity, best);
        return best;
    }

    private void ContinueBite(long now)
    {
        long elapsed = now - attackStartMs;
        if (!damageDone && elapsed >= biteAtMs)
        {
            damageDone = true;
            if (biteSound != null) entity.World.PlaySoundAt(biteSound, entity.Pos.X, entity.Pos.Y + 0.2, entity.Pos.Z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.25f, 12, 1f);
            double gap = target == null ? 99 : entity.Pos.DistanceTo(target.Pos) - (entity.CollisionBox.XSize + target.CollisionBox.XSize) / 2;
            if (target != null && target.Alive && gap <= biteRange + 0.4 && !Strike.IsCreative(target))
            {
                Strike.Hit(entity, target, damage * (float)damageMul, EnumDamageType.PiercingAttack, damageTier + tierBonus, 0.1f);
                // The infection burns on after the bite: the venom's ticks (another bite starts it over, it does not add up)
                VenomSystem.Envenom(target);
            }
        }
        if (elapsed >= biteDurationMs)
        {
            entity.AnimManager.StopAnimation("attack");
            attackStartMs = -1;
            lastAttackMs = now;
        }
    }

    /// <summary>The glob leaves the maw (300 ms in), flies at where its target stood, and lands a moment later: whoever is still near that spot is burnt.</summary>
    private void ContinueSpit(long now)
    {
        long elapsed = now - spitStartMs;
        if (!damageDone && elapsed >= 300)
        {
            damageDone = true;
            Entity at = target;
            if (at != null)
            {
                Vec3d from = entity.Pos.XYZ.Add(Math.Sin(entity.Pos.Yaw) * 0.3, 0.3, Math.Cos(entity.Pos.Yaw) * 0.3);
                Vec3d aim = Senses.Centre(at);
                double len = from.DistanceTo(aim);
                if (spitSound != null) entity.World.PlaySoundAt(spitSound, entity.Pos.X, entity.Pos.Y + 0.3, entity.Pos.Z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.2f, 14, 1f);
                Glob(from, aim);
                int flightMs = (int)(len / Math.Max(1, globSpeed) * 1000);
                Entity self = entity;
                entity.World.RegisterCallback(_ => Land(self, at, aim), Math.Max(50, flightMs));
            }
        }
        if (elapsed >= 600)
        {
            entity.AnimManager.StopAnimation("spit");
            spitStartMs = -1;
        }
    }

    /// <summary>The glob in flight: a short stream of sickly green-yellow drops along its way.</summary>
    private void Glob(Vec3d from, Vec3d to)
    {
        int n = Math.Max(4, (int)(from.DistanceTo(to) * 2.5));
        int c = ColorUtil.ToRgba(230, 150, 210, 40), c2 = ColorUtil.ToRgba(220, 90, 170, 30);
        for (int i = 0; i <= n; i++)
        {
            double t = i / (double)n;
            double arc = Math.Sin(t * Math.PI) * 0.35;
            var at = new Vec3d(from.X + (to.X - from.X) * t, from.Y + (to.Y - from.Y) * t + arc, from.Z + (to.Z - from.Z) * t);
            var p = new SimpleParticleProperties(1, 2, i % 2 == 0 ? c : c2, at.AddCopy(-0.05, -0.05, -0.05), at.AddCopy(0.05, 0.05, 0.05), new Vec3f(-0.1f, -0.2f, -0.1f), new Vec3f(0.1f, 0f, 0.1f), 0.5f, 0.3f, 0.12f, 0.22f, EnumParticleModel.Quad)
            {
                VertexFlags = 90,
                ShouldDieInLiquid = true,
                WindAffected = false,
            };
            entity.World.SpawnParticles(p);
        }
    }

    private void Land(Entity agent, Entity target, Vec3d aim)
    {
        IWorldAccessor world = agent.World;
        if (sizzleSound != null) world.PlaySoundAt(sizzleSound, aim.X, aim.Y, aim.Z, null, 0.9f + (float)world.Rand.NextDouble() * 0.2f, 12, 0.9f);
        var splash = new SimpleParticleProperties(8, 14, ColorUtil.ToRgba(200, 120, 190, 30), aim.AddCopy(-0.3, -0.4, -0.3), aim.AddCopy(0.3, 0.1, 0.3),
            new Vec3f(-0.6f, 0.2f, -0.6f), new Vec3f(0.6f, 1.0f, 0.6f), 0.8f, 0.8f, 0.1f, 0.25f, EnumParticleModel.Quad) { VertexFlags = 70, WindAffected = false };
        world.SpawnParticles(splash);
        if (target == null || !target.Alive || Strike.IsCreative(target)) return;
        if (Senses.Centre(target).DistanceTo(aim) > 1.2) return;
        Strike.Hit(agent, target, spitDamage * (float)damageMul, EnumDamageType.Acid, 0, 0);
    }

    private void Chitter(float dt)
    {
        nextChitter -= dt;
        if (nextChitter > 0 || chitterSounds.Length == 0) return;
        var rand = entity.World.Rand;
        nextChitter = 1.6f + (float)rand.NextDouble() * 2.4f;
        entity.World.PlaySoundAt(chitterSounds[rand.Next(chitterSounds.Length)], entity.Pos.X, entity.Pos.Y + 0.2, entity.Pos.Z, null,
            0.9f + (float)rand.NextDouble() * 0.3f, 12, 0.7f);
    }

    private void OnArrived() => Stop();

    private void OnNoPath() => Stop();

    private void Stop()
    {
        pathTraverser.Stop();
        if (!moving) return;
        moving = false;
        entity.AnimManager.StopAnimation("run");
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Stop();
        entity.AnimManager.StopAnimation("attack");
        entity.AnimManager.StopAnimation("spit");
    }
}

/// <summary>
/// "Shrouded in some sort of darkness that seems to absorb all sources of light": wisps of dark smoke drift up off the
/// Hunter, thicker while it hunts (client only, a few particles a second).
/// </summary>
public class EntityBehaviorL14Smoke : EntityBehavior
{
    private float acc;

    public EntityBehaviorL14Smoke(Entity entity) : base(entity) { }

    public override string PropertyName() => "backrooms-l14smoke";

    public override void OnGameTick(float dt)
    {
        if (entity.World.Side != EnumAppSide.Client || !entity.Alive) return;
        acc += dt;
        bool hunting = entity.WatchedAttributes.GetBool(L14HunterSystem.HuntingKey);
        float every = hunting ? 0.07f : 0.16f;
        if (acc < every) return;
        acc = 0;
        double x = entity.Pos.X, y = entity.Pos.Y, z = entity.Pos.Z;
        var smoke = new SimpleParticleProperties(1, hunting ? 3 : 2, ColorUtil.ToRgba(hunting ? 120 : 90, 8, 8, 12),
            new Vec3d(x - 0.75, y + 0.1, z - 0.75), new Vec3d(x + 0.75, y + 2.0, z + 0.75), new Vec3f(-0.08f, 0.04f, -0.08f), new Vec3f(0.08f, 0.22f, 0.08f),
            hunting ? 2.6f : 2.0f, -0.004f, 0.35f, 0.8f, EnumParticleModel.Quad)
        {
            SizeEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, 1.2f),
            OpacityEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, -40f),
            WindAffected = false,
            ShouldDieInLiquid = true,
        };
        entity.World.SpawnParticles(smoke);
    }
}
