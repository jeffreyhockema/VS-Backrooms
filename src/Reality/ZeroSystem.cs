using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Server;

namespace Backrooms.Reality;

/// <summary>
/// What happens when a wanderer's Reality Stability reaches zero (docs/design/progression/plan.md 3.4, decisions 3 and 12).
///
/// At zero, where the Backrooms are not at rest (not the Safe band, and not Level 0, the Hub, Level 974 or the Snackrooms), the level's worst hunter comes at once (<see cref="MenaceSystem.SendWorstHunter"/>).
/// After <see cref="ZeroSeconds"/> at zero, from any cause and in any level but 0, the Hub, Level 974 and the Snackrooms, the lights
/// go for a few seconds and the wanderer wakes at a random place in the previous level (<see cref="WakeLevel"/>): their
/// belongings with them, their stability half full, and no thin spot and no way back where they wake.
///
/// Players and the straw dummies of the headless tests (which stand in for them) are treated alike.
/// </summary>
public class ZeroSystem : ModSystem
{
    /// <summary>How long (real seconds) someone must stay at zero before they black out, and how long the dark lasts before they are moved.</summary>
    public const double ZeroSeconds = 60, BlackoutSeconds = 3;

    /// <summary>The stability they wake with.</summary>
    public const double WakeStability = 0.5;

    /// <summary>Player attribute (synced to the client, which darkens the world as for a Flickering) holding when the blackout ends, in calendar hours.</summary>
    public const string BlackoutKey = "backrooms:blackoutUntil";

    /// <summary>At or under this a bar counts as empty (vanilla clamps it to exactly 0).</summary>
    private const double Zero = 0.005;

    private sealed class State
    {
        public double Seconds;
        public bool Hunted, Dark;
    }

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private readonly Dictionary<long, State> states = new();
    private long lastMs;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            lastMs = api.World.ElapsedMilliseconds;
            api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] zero stability: {0}", e), 1000, 300);
        });
    }

    public override void Dispose()
    {
        states.Clear();
        base.Dispose();
    }

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        double seconds = Math.Clamp((now - lastMs) / 1000.0, 0, 5);
        lastMs = now;
        var seen = new HashSet<long>();
        foreach (IServerPlayer player in sapi.World.AllOnlinePlayers.OfType<IServerPlayer>())
        {
            if (player.ConnectionState != EnumClientState.Playing || player.Entity is not { Alive: true } entity) continue;
            if (player.WorldData.CurrentGameMode != EnumGameMode.Survival) continue;
            seen.Add(entity.EntityId);
            Step(entity, seconds);
        }
        foreach (Entity dummy in sapi.World.LoadedEntities.Values.Where(e => e.Alive && Senses.IsTestTarget(e)).ToList())
        {
            seen.Add(dummy.EntityId);
            Step(dummy, seconds);
        }
        foreach (long gone in states.Keys.Where(id => !seen.Contains(id)).ToList()) states.Remove(gone);
    }

    private void Step(Entity entity, double seconds)
    {
        if (!states.TryGetValue(entity.EntityId, out State state)) states[entity.EntityId] = state = new State();
        if (state.Dark) return; // (the lights are out; the move is on its way)
        double stability = Senses.Stability(entity);
        if (stability > Zero || SafePlace(layout, entity.Pos.X, entity.Pos.Z))
        {
            state.Seconds = 0;
            if (stability > 0.1) state.Hunted = false;
            return;
        }
        state.Seconds += seconds;

        // The level's worst hunter at once, once for each time the bar runs out (SendWorstHunter sends nothing in the Safe band)
        if (!state.Hunted)
            state.Hunted = sapi.ModLoader.GetModSystem<MenaceSystem>()?.SendWorstHunter(entity) == true;

        if (state.Seconds >= ZeroSeconds) Blackout(entity, state);
    }

    private void Blackout(Entity entity, State state)
    {
        state.Dark = true;
        if (entity is EntityPlayer)
        {
            // The same darkening a Flickering gives (the client sees the key whatever level it is in), with its power-down sound
            double hours = BlackoutSeconds * sapi.World.Calendar.SpeedOfTime * sapi.World.Calendar.CalendarSpeedMul / 3600;
            entity.WatchedAttributes.SetDouble(BlackoutKey, sapi.World.Calendar.TotalHours + hours);
        }
        sapi.Logger.Notification("[backrooms] zero: {0} has been at zero stability for {1:0} s in Level {2}: the lights go",
            NameOf(entity), state.Seconds, WorldLayout.DisplayNumber(LevelOf(entity)));
        sapi.World.RegisterCallback(_ =>
        {
            // (A player who left or died in the meantime is not moved)
            if (entity is EntityPlayer { Player: IServerPlayer p } && (p.ConnectionState != EnumClientState.Playing || !entity.Alive)) { state.Dark = false; state.Seconds = 0; return; }
            WakeElsewhere(entity, state);
        }, (int)(BlackoutSeconds * 1000));
    }

    /// <summary>Whether the Backrooms leave someone be here: Level 0, the Hub, Level 974 and the Snackrooms never black out anyone.</summary>
    private static bool SafePlace(WorldLayout layout, double x, double z)
    {
        int mx = WorldLayout.MacroOf((int)Math.Floor(x)), mz = WorldLayout.MacroOf((int)Math.Floor(z));
        int level = layout.LevelAt(mx, mz);
        return level is 0 or WorldLayout.Hub or WorldLayout.Level974 || level == 6 && layout.IsSnackrooms(mx, mz);
    }

    /// <summary>
    /// Where someone who blacks out wakes: the level before the one they lost their grip in. Rings: one up (Level 1: Level 0).
    /// The places no ring reaches are woken in the level their way in came from (docs/design/new-levels/LINKS.md): the city from
    /// 10, the Poolrooms from the hotel (5), Motion from 9, Level ! from the Poolrooms, Fun from 1, the End from 4, 3999
    /// from the Poolrooms, 188 from 1.
    /// </summary>
    public static int WakeLevel(int level) => level switch
    {
        11 => 10,
        WorldLayout.Poolrooms => 5,
        WorldLayout.Motion => 9,
        WorldLayout.RunLevel => WorldLayout.Poolrooms,
        WorldLayout.FunLevel => 1,
        WorldLayout.TheEnd => 4,
        WorldLayout.Level3999 => WorldLayout.Poolrooms,
        WorldLayout.Level188 => 1,
        <= 0 => 0,
        > 11 => 0,
        _ => level - 1,
    };

    private int LevelOf(Entity entity) => layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z)));

    private static string NameOf(Entity entity) => (entity as EntityPlayer)?.Player?.PlayerName ?? "dummy #" + entity.EntityId;

    /// <summary>Moves them to a random walkable spot in the previous level, with their stability at half. No thin spot, no way back.</summary>
    private void WakeElsewhere(Entity entity, State state)
    {
        state.Dark = false;
        state.Seconds = 0;
        entity.WatchedAttributes.RemoveAttribute(BlackoutKey);
        entity.WatchedAttributes.MarkPathDirty(BlackoutKey);
        if (!entity.Alive) return;
        int from = LevelOf(entity), to = WakeLevel(from);
        ulong key = (ulong)sapi.World.Rand.NextInt64();
        bool moved;
        if (entity is EntityPlayer { Player: IServerPlayer player })
        {
            // (The thresholds' own way of putting someone down, as /backrooms goto: it loads the place first and fades the screen)
            moved = sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>()?.Send(player, to, key, null) == true;
        }
        else
        {
            (int X, int Z)? spot = null;
            for (int attempt = 0; attempt < 4 && spot == null; attempt++, key = Hashing.Mix(key)) spot = layout.FindArrival(to, key);
            moved = spot is { } a;
            if (spot is { } at)
            {
                // (A stand-in is put down once the place is loaded, as the thresholds do for a player)
                double y = geometry.FloorFor(to) + layout.ArrivalHeight(at.X, at.Z);
                sapi.WorldManager.LoadChunkColumnPriority(at.X / GlobalConstants.ChunkSize, at.Z / GlobalConstants.ChunkSize, new ChunkLoadOptions
                {
                    OnLoaded = () => entity.TeleportToDouble(at.X + 0.5, y, at.Z + 0.5),
                });
            }
        }
        if (!moved)
        {
            sapi.Logger.Warning("[backrooms] zero: found nowhere to wake {0} in Level {1}", NameOf(entity), WorldLayout.DisplayNumber(to));
            state.Seconds = ZeroSeconds - 10; // (try again in a few seconds)
            return;
        }
        entity.WatchedAttributes.SetDouble("temporalStability", WakeStability);
        state.Hunted = false;
        sapi.Logger.Notification("[backrooms] zero: {0} lost their grip in Level {1} and came to in Level {2}",
            NameOf(entity), WorldLayout.DisplayNumber(from), WorldLayout.DisplayNumber(to));
        if (entity is EntityPlayer { Player: IServerPlayer woken })
            woken.SendMessage(Vintagestory.API.Config.GlobalConstants.GeneralChatGroup, Say.T(woken, "zero-blackout"), EnumChatType.Notification);
    }
}
