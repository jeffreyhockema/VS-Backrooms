using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Entities;

/// <summary>
/// The Mangled (Entity 63): not something the director puts down, but an event, rare, and only in the Suburbs. There
/// is one Mangled at a time (no second event is begun for anyone while one is under way), and it comes with its own weather:
/// <list type="number">
/// <item>The onset, most of a minute: the air goes cold (the temperature where the player stands drops some
/// sixteen degrees), a grey fog rolls in and closes round them, and voices start up out in it: someone saying hello,
/// a cough, a whisper, somebody hurt. Far off, something like thunder, which is its steps.</item>
/// <item>It comes: a black pillar out in the fog, which walks. Close by, its faces all talk at once. Its tendrils take
/// whoever they reach up into the dark and let go. It cannot be killed; striking it only makes it louder and keeps
/// it longer. Indoors is safer: it is too big for doors.</item>
/// <item>After three minutes or so (or once the player leaves the Suburbs), it goes back into the fog and the fog
/// lifts.</item>
/// </list>
/// On the client: the ground shakes a little with each of its steps.
/// </summary>
public class MangledEvent : ModSystem
{
    /// <summary>Player attribute (synced) holding how thick the Mangled's fog is round them, 0 to 1.</summary>
    public const string FogKey = "backrooms:mangledFog";

    /// <summary>How many degrees the air drops at the heart of its cold.</summary>
    public const float ColdDegrees = 16;

    private const double OnsetSeconds = 45, ManifestSeconds = 180, EndSeconds = 30, CooldownHours = 40;

    private enum Phase { Onset, Manifest, Ending }

    private sealed class Event
    {
        public Phase Phase;
        public double Seconds, NextVoice = 5, NextRumble = 3, Extra;
        public float Fog;
        public Entity Mangled;
        public Vec3d LastMangledPos;
        public long LastStruckMs;
        /// <summary>Brought down by the cheat, which may be used anywhere: holds the Onset's fog outside the Suburbs (the Mangled itself only comes in Level 9).</summary>
        public bool Forced;
    }

    private static readonly string[] Voices =
    {
        "backrooms:sounds/entity/hello", "backrooms:sounds/entity/cough", "backrooms:sounds/effect/whisper",
        "game:sounds/player/hurt*", "backrooms:sounds/entity/murmur", "backrooms:sounds/entity/hello",
    };

    private static readonly Dictionary<long, (Vec3d At, float Strength)> Cold = new();

    private ICoreServerAPI sapi;
    private MenaceSystem director;
    private readonly Dictionary<long, Event> events = new();
    private readonly Dictionary<long, double> nextAllowedHours = new();
    private Random rand;

    /// <summary>How cold its weather makes a place, 0 to 1 (for the climate: the server's body temperature).</summary>
    public static float ColdAt(BlockPos pos)
    {
        lock (Cold)
        {
            float best = 0;
            foreach (var (at, strength) in Cold.Values)
            {
                double dx = at.X - pos.X, dz = at.Z - pos.Z, d = Math.Sqrt(dx * dx + dz * dz);
                if (d < 64) best = Math.Max(best, strength * (float)(1 - 0.5 * d / 64));
            }
            return best;
        }
    }

    public override double ExecuteOrder() => 1.2;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        rand = new Random();
        lock (Cold) Cold.Clear();
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            director = api.ModLoader.GetModSystem<MenaceSystem>();
            tickListener = api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] the Mangled: {0}", e), 1000, 1500);
        });
        api.Event.PlayerDisconnect += OnPlayerDisconnect;

        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("mangled")
                .WithDescription("Brings the Mangled's weather down on you (in the Suburbs, it then comes)")
                .RequiresPlayer()
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(args =>
                {
                    if (director?.Layout == null) return TextCommandResult.Error("Not a Backrooms world");
                    Entity entity = args.Caller.Entity;
                    if (events.ContainsKey(entity.EntityId)) return TextCommandResult.Error("It is already coming");
                    events[entity.EntityId] = new Event { Forced = true };
                    return TextCommandResult.Success("The air goes cold");
                })
            .EndSubCommand();
    }

    private long tickListener;

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        long id = player.Entity?.EntityId ?? -1;
        if (events.TryGetValue(id, out Event e))
        {
            if (e.Mangled?.Alive == true) e.Mangled.GetBehavior<EntityBehaviorMenace>().Kind = Encounter.Leave;
            // (Cut short, it still counts: logging out and back in does not bring the next one sooner)
            nextAllowedHours[id] = sapi.World.Calendar.TotalHours + CooldownHours;
        }
        events.Remove(id);
        lock (Cold) Cold.Remove(id);
    }

    public override void Dispose()
    {
        if (sapi != null)
        {
            sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
            if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
        }
        base.Dispose();
    }

    private void OnTick(float dt)
    {
        double hours = sapi.World.Calendar.TotalHours;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity == null) continue;
            EntityPlayer entity = player.Entity;
            if (events.TryGetValue(entity.EntityId, out Event e))
            {
                Advance(entity, e, hours);
                continue;
            }
            if (!entity.Alive || player.WorldData.CurrentGameMode is EnumGameMode.Spectator or EnumGameMode.Creative || !director.Setting.Entities) continue;
            if (hours < nextAllowedHours.GetValueOrDefault(entity.EntityId)) continue;
            MenaceSystem.Assessment a = director.AssessmentOf(entity);
            if (a.Level != 9 || a.Band == MenaceBand.Safe) continue;
            // Rare: rolled once a second, so at set-piece scale 1 about once in forty minutes at the edge of the Suburbs (1/2400),
            // once in an hour and a half further in, once in four hours in the heart (Normal, scale 2.35, makes it 2.35 times as
            // often); far likelier (x8) when a Reality Shift has the lights out
            double chance = a.Band switch { MenaceBand.Heartland => 0.00007, MenaceBand.Approach => 0.0002, _ => 0.0004 };
            if (a.Shift) chance *= 8;
            // Scaled by the spawn setting (its square root), and only one event at a time, whoever it is for
            chance *= director.Setting.SetPieceScale;
            if (rand.NextDouble() < chance && !events.Values.Any(ev => ev.Phase != Phase.Ending || ev.Mangled?.Alive == true))
            {
                events[entity.EntityId] = new Event();
                Log("the air goes cold round {0}", player.PlayerName);
            }
        }
    }

    private void Advance(EntityPlayer player, Event e, double hours)
    {
        e.Seconds += 1;
        bool gone = !player.Alive;
        // Out of the Suburbs, by a threshold or on foot, its weather lifts (its fog is drawn round the player wherever
        // they are, so left to run on it would follow them into the next level)
        bool left = director.AssessmentOf(player).Level != 9;
        switch (e.Phase)
        {
            case Phase.Onset:
                e.Fog = (float)Math.Min(1, e.Seconds / OnsetSeconds);
                Voice(player, e, 20, 36, 6, 11);
                Rumble(player, e, null, 10, 16);
                if (gone || left && !e.Forced) Begin(e, Phase.Ending);
                else if (e.Seconds >= OnsetSeconds)
                {
                    if (TrySpawn(player, e)) Begin(e, Phase.Manifest);
                    else if (e.Seconds > OnsetSeconds + 20) Begin(e, Phase.Ending);
                }
                break;

            case Phase.Manifest:
                e.Fog = 1;
                if (e.Mangled == null || !e.Mangled.Alive)
                {
                    Begin(e, Phase.Ending);
                    break;
                }
                double distance = e.Mangled.Pos.DistanceTo(player.Pos);
                // Close by, its faces all talk at once; further off, single voices out in the fog
                if (distance < 30) Voice(player, e, 0, 0, 5, 9, e.Mangled.Pos.XYZ.Add(0, 6, 0), "backrooms:sounds/entity/chorus");
                else Voice(player, e, 18, 30, 6, 11);
                bool moving = e.LastMangledPos != null && e.LastMangledPos.SquareDistanceTo(e.Mangled.Pos.XYZ) > 0.09;
                e.LastMangledPos = e.Mangled.Pos.XYZ;
                if (moving) Rumble(player, e, e.Mangled.Pos.XYZ, 2.5, 3.5);

                // Struck: louder, and it stays longer
                long struck = e.Mangled.Attributes.GetLong(EntityBehaviorMenace.StruckKey, 0);
                if (struck > e.LastStruckMs)
                {
                    e.LastStruckMs = struck;
                    e.Extra = Math.Min(90, e.Extra + 30);
                    Play("backrooms:sounds/entity/chorus", e.Mangled.Pos.XYZ.Add(0, 6, 0), 1.0f, 0.8f, 64);
                }
                if (gone || left || e.Seconds > ManifestSeconds + e.Extra) Begin(e, Phase.Ending);
                break;

            case Phase.Ending:
                e.Fog = (float)Math.Max(0, 1 - e.Seconds / EndSeconds);
                if (e.Seconds >= EndSeconds)
                {
                    events.Remove(player.EntityId);
                    nextAllowedHours[player.EntityId] = hours + CooldownHours;
                    e.Fog = 0;
                    Log("the fog lifts");
                }
                break;
        }

        // The weather round the player: the fog (drawn on their client) and the cold (for their body temperature)
        if (Math.Abs(player.WatchedAttributes.GetFloat(FogKey) - e.Fog) > 0.005f || e.Fog == 0) player.WatchedAttributes.SetFloat(FogKey, e.Fog);
        lock (Cold)
        {
            if (e.Fog > 0) Cold[player.EntityId] = (player.Pos.XYZ, e.Fog);
            else Cold.Remove(player.EntityId);
        }
    }

    private void Begin(Event e, Phase phase)
    {
        if (phase == Phase.Ending && e.Mangled?.Alive == true)
        {
            // Back into the fog
            e.Mangled.GetBehavior<EntityBehaviorMenace>().Kind = Encounter.Leave;
        }
        e.Phase = phase;
        e.Seconds = 0;
        Log("now {0}", phase);
    }

    /// <summary>Puts the Mangled down out in the fog, twenty-odd blocks off, somewhere tall enough for it to stand.</summary>
    private bool TrySpawn(EntityPlayer player, Event e)
    {
        WorldLayout layout = director.Layout;
        if (layout == null) return false;
        for (int attempt = 0; attempt < 24; attempt++)
        {
            double angle = rand.NextDouble() * Math.PI * 2, d = 22 + rand.NextDouble() * 10;
            int x = (int)Math.Floor(player.Pos.X + Math.Cos(angle) * d), z = (int)Math.Floor(player.Pos.Z + Math.Sin(angle) * d);
            if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, (int)player.Pos.Y, z) == null) continue;
            if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != 9) continue;
            int y = Senses.FindFloor(sapi.World, x, (int)Math.Floor(player.Pos.Y), z, 4, 4);
            if (y == int.MinValue) continue;
            e.Mangled = director.SpawnHunter(Roster.Mangled, new Vec3d(x + 0.5, y, z + 0.5), player, ownNumbers: true);
            if (e.Mangled == null) return false;
            Log("it comes, {0:0} blocks off", d);
            return true;
        }
        return false;
    }

    private void Voice(EntityPlayer player, Event e, double near, double far, double every, double everyMax, Vec3d at = null, string sound = null)
    {
        e.NextVoice -= 1;
        if (e.NextVoice > 0) return;
        e.NextVoice = every + rand.NextDouble() * (everyMax - every);
        if (at == null)
        {
            double angle = rand.NextDouble() * Math.PI * 2, d = near + rand.NextDouble() * (far - near);
            at = new Vec3d(player.Pos.X + Math.Cos(angle) * d, player.Pos.Y + 1.5, player.Pos.Z + Math.Sin(angle) * d);
        }
        Play(sound ?? Voices[rand.Next(Voices.Length)], at, 0.85f + (float)rand.NextDouble() * 0.25f, 0.7f, 48);
    }

    private void Rumble(EntityPlayer player, Event e, Vec3d at, double every, double everyMax)
    {
        e.NextRumble -= 1;
        if (e.NextRumble > 0) return;
        e.NextRumble = every + rand.NextDouble() * (everyMax - every);
        if (at == null)
        {
            double angle = rand.NextDouble() * Math.PI * 2;
            at = new Vec3d(player.Pos.X + Math.Cos(angle) * 44, player.Pos.Y, player.Pos.Z + Math.Sin(angle) * 44);
        }
        Play("backrooms:sounds/entity/rumble", at, 0.8f + (float)rand.NextDouble() * 0.15f, 1f, 96);
    }

    private void Play(string sound, Vec3d at, float pitch, float volume, float range)
    {
        sapi.World.PlaySoundAt(new AssetLocation(sound), at.X, at.Y, at.Z, null, pitch, range, volume);
    }

    private void Log(string format, params object[] args)
    {
        if (director?.Logging == true) sapi.Logger.Notification("[backrooms] the Mangled: " + string.Format(format, args));
    }

    // ================= Client: the ground shakes =================

    private ICoreClientAPI capi;
    private float stepIn, lookIn;
    private Entity mangled;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Event.RegisterGameTickListener(OnClientTick, 100);
    }

    private void OnClientTick(float dt)
    {
        Entity me = capi.World.Player?.Entity;
        if (me == null) return;
        // (Looked for once a second; the one found is followed until it is gone)
        if (mangled == null || !mangled.Alive || capi.World.GetEntityById(mangled.EntityId) == null)
        {
            mangled = null;
            lookIn -= dt;
            if (lookIn > 0) return;
            lookIn = 1;
            mangled = capi.World.GetNearestEntity(me.Pos.XYZ, 80, 80, e => e.Alive && e.Code.Path == "mangled");
            if (mangled == null) return;
        }
        var active = mangled.AnimManager?.ActiveAnimationsByAnimCode;
        bool walking = active != null && (active.ContainsKey("walk") || active.ContainsKey("run"));
        if (!walking) return;
        stepIn -= dt;
        if (stepIn > 0) return;
        // A heavy step every second and a half of its walk, every 0.8 seconds when it runs
        stepIn = active.ContainsKey("run") ? 0.8f : 1.5f;
        double d = mangled.Pos.DistanceTo(me.Pos);
        float strength = (float)Math.Max(0, 1 - d / 80);
        if (strength > 0.05f) capi.World.AddCameraShake(0.12f * strength);
    }
}
