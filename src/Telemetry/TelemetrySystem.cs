using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Backrooms.Entities;
using Backrooms.Needs;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.PlayTelemetry;

/// <summary>
/// What the rest of the mod calls: one-line, no-op when the telemetry is off (or on a client). See
/// <see cref="TelemetrySystem"/> for the file and docs/DEVELOPING.md ("Play telemetry") for the events.
/// </summary>
public static class Telemetry
{
    internal static TelemetrySystem Sys;

    /// <summary>Whether events are being recorded right now.</summary>
    public static bool On => Sys is { Enabled: true };

    /// <summary>Records an event for someone (a player, or a straw dummy in a test; null for none): <c>kv</c> alternates field names and values.</summary>
    public static void Log(string ev, Entity who, params object[] kv) => Sys?.Record(ev, who, kv);

    /// <summary>An entity was put down for <paramref name="target"/> by the director (or a set piece).</summary>
    public static void Spawn(Entity entity, Entity target, string kind, string band, bool setPiece)
    {
        if (Sys is not { Enabled: true }) return;
        Log("spawn", target, "code", entity.Code.Path, "kind", kind, "band", band, "dist", target == null ? 0 : entity.Pos.DistanceTo(target.Pos.XYZ),
            "setpiece", setPiece, "id", entity.EntityId);
    }

    /// <summary>An owned entity changed what it is doing.</summary>
    public static void Kind(Entity entity, Entity target, string from, string to)
    {
        if (Sys is not { Enabled: true }) return;
        Log("kind", target, "code", entity.Code.Path, "id", entity.EntityId, "from", from, "to", to,
            "dist", target == null ? 0 : entity.Pos.DistanceTo(target.Pos.XYZ));
    }

    /// <summary>An owned entity saw its target for the first time.</summary>
    public static void Contact(Entity entity, Entity target, string kind)
    {
        if (Sys is not { Enabled: true }) return;
        Log("contact", target, "code", entity.Code.Path, "id", entity.EntityId, "kind", kind, "dist", entity.Pos.DistanceTo(target.Pos.XYZ));
    }

    public static void Blackout(Entity who, double seconds) => Log("blackout", who, "seconds", seconds);

    public static void Cross(Entity who, int level) => Log("cross", who, "level", WorldLayout.DisplayNumber(level), "class", WorldLayout.SurvivalClass(level));

    public static void Note(Entity who, string key) => Log("note", who, "key", key);
}

/// <summary>
/// Play telemetry: a local event log of the user's own sessions (nothing leaves the machine) and a one-key marker, so a
/// human play-test yields numbers (tools/telemetry/report.py) without note-taking. One JSON Lines file per server
/// session, <c>ModData/backroomsss/telemetry/&lt;world&gt;-&lt;yyyyMMdd-HHmm&gt;.jsonl</c> in the data folder, one object per
/// event: <c>t</c> (UTC time), <c>h</c> (in-game hours), <c>p</c> (player), <c>ev</c> and the event's fields.
///
/// It mostly watches: a half-second tick reads the state of each player (level, band, stability, needs, eating) and logs
/// only changes; the few events nobody else can tell (spawns, kind changes, contact, blackout, crossing, notes) are
/// one-line calls from the systems that make them (<see cref="Telemetry"/>). No player gets more than
/// <see cref="MaxPerSecond"/> events a second. On by default; <c>/backrooms telemetry on|off</c>. F8 (client) or
/// <c>/backrooms mark [text]</c> records a <c>mark</c> with everything about the moment.
/// </summary>
public class TelemetrySystem : ModSystem
{
    public const string HotkeyCode = "backroomsmark";
    private const int MaxPerSecond = 20;
    private const double RingSeconds = 60;
    private const int PosSeconds = 30;
    private const int AboutRange = 48;

    private ICoreServerAPI sapi;
    private ICoreClientAPI capi;
    private MenaceSystem menace;

    private readonly object gate = new();
    private StreamWriter writer;
    private string path;
    private DateTime lastFlush;
    private bool started;
    private long tickListener;

    public bool Enabled { get; private set; } = true;

    private sealed class PState
    {
        public int Level = int.MinValue;
        public MenaceBand Band = (MenaceBand)(-1);
        public int StabTier;
        public string Thirst, Rest;
        public bool Sleeping;
        public double LastX = double.NaN, LastZ = double.NaN, Walked;
        public int PosCountdown = PosSeconds;
        public int Slot = -1, Size;
        public string Code;
        public float Sat = -1, Hyd = -1;
        public readonly HashSet<string> Looted = new();
    }

    private readonly Dictionary<string, PState> states = new();
    private readonly Dictionary<string, Queue<(DateTime At, Dictionary<string, object> Ev)>> rings = new();
    private readonly Dictionary<string, (long Second, int Count)> rates = new();
    private readonly Dictionary<string, int> dropped = new();
    private readonly HashSet<long> hooked = new();
    private int tickNo;

    // After BackroomsModSystem (1.0), which creates the /backrooms command
    public override double ExecuteOrder() => 1.3;

    // ============================================================ Client: the marker key

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Input.RegisterHotKey(HotkeyCode, "Backrooms: mark this moment", GlKeys.F8, HotkeyType.GUIOrOtherControls);
        api.Input.SetHotKeyHandler(HotkeyCode, _ => SendMark(""));
        api.ChatCommands.Create("mark")
            .WithDescription("Marks this moment in the play telemetry, with a note: .mark the hound came from behind")
            .WithArgs(api.ChatCommands.Parsers.OptionalAll("text"))
            .HandleWith(args =>
            {
                SendMark(args.Parsers[0].IsMissing ? "" : (string)args[0]);
                return TextCommandResult.Success();
            });
    }

    private bool SendMark(string text)
    {
        if (!BackroomsWorld.IsBackroomsClimate(capi.World.Config)) { capi.ShowChatMessage("This is not a Backrooms world"); return true; }
        capi.SendChatMessage("/backrooms mark" + (string.IsNullOrWhiteSpace(text) ? "" : " " + text.Trim()));
        return true;
    }

    // ============================================================ Server

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            menace = api.ModLoader.GetModSystem<MenaceSystem>();
            Telemetry.Sys = this;
            OpenFile();
            tickListener = api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] telemetry: {0}", e), 500, 250);
            api.Event.PlayerNowPlaying += OnJoin;
            api.Event.PlayerDisconnect += OnLeave;
            api.Event.PlayerDeath += OnDeath;
            api.Event.PlayerRespawn += OnRespawn;
            api.Event.DidUseBlock += OnUsedBlock;
            api.Event.DidBreakBlock += OnBrokeBlock;
            api.Logger.EntryAdded += OnLogEntry;
        });
        api.Event.ServerRunPhase(EnumServerRunPhase.Shutdown, CloseFile);

        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        command
            .BeginSubCommand("mark")
                .WithDescription("Marks this moment in the play telemetry (F8 on the client): your position, level, band, menace, health, needs, the entities about and your last minute of events. From the console it marks the latest straw dummy.")
                .WithArgs(api.ChatCommands.Parsers.OptionalAll("text"))
                .HandleWith(OnMarkCommand)
            .EndSubCommand()
            .BeginSubCommand("telemetry")
                .WithDescription("Play telemetry (a local event log of your sessions, for tools/telemetry/report.py): on, off, or where the file is")
                .WithArgs(api.ChatCommands.Parsers.OptionalWord("state"))
                .HandleWith(OnTelemetryCommand)
            .EndSubCommand();
    }

    public override void Dispose()
    {
        if (sapi != null)
        {
            sapi.Event.PlayerNowPlaying -= OnJoin;
            sapi.Event.PlayerDisconnect -= OnLeave;
            sapi.Event.PlayerDeath -= OnDeath;
            sapi.Event.PlayerRespawn -= OnRespawn;
            sapi.Event.DidUseBlock -= OnUsedBlock;
            sapi.Event.DidBreakBlock -= OnBrokeBlock;
            sapi.Logger.EntryAdded -= OnLogEntry;
            if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
            CloseFile();
        }
        if (Telemetry.Sys == this) Telemetry.Sys = null;
        base.Dispose();
    }

    private TextCommandResult OnTelemetryCommand(TextCommandCallingArgs args)
    {
        if (Telemetry.Sys != this) return TextCommandResult.Error("Not a Backrooms world");
        string state = args.Parsers[0].IsMissing ? "" : ((string)args[0]).Trim().ToLowerInvariant();
        if (state == "on") Enabled = true;
        else if (state == "off") Enabled = false;
        else if (state != "") return TextCommandResult.Error("Use: /backrooms telemetry [on|off]");
        return TextCommandResult.Success($"Play telemetry is {(Enabled ? "on" : "off")}; writing {path}");
    }

    // ------------------------------------------------------------ File

    private void OpenFile()
    {
        string dir = sapi.GetOrCreateDataPath(Path.Combine("ModData", "backroomsss", "telemetry"));
        string world = WorldName();
        world = new string(world.Select(c => char.IsLetterOrDigit(c) || c is '-' or '_' ? c : '_').ToArray());
        path = Path.Combine(dir, $"{world}-{DateTime.Now:yyyyMMdd-HHmm}.jsonl");
        for (int n = 2; File.Exists(path); n++) path = Path.Combine(dir, $"{world}-{DateTime.Now:yyyyMMdd-HHmm}-{n}.jsonl");
        writer = new StreamWriter(new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.ReadWrite), new UTF8Encoding(false));
        started = true;
        lastFlush = DateTime.UtcNow;
        IWorldAccessor w = sapi.World;
        Record("session", null, "state", "start", "world", WorldName(), "seed", sapi.WorldManager.Seed,
            "mod", Mod.Info.Version, "layout", w.Config.GetInt("backroomsLayoutVersion", 1),
            "backroomsMenace", w.Config.GetString("backroomsMenace", "normal"),
            "backroomsScarcity", w.Config.GetString(Salvage.ScarcitySystem.ConfigKey, "normal"),
            "backroomsThirst", w.Config.GetString(Backrooms.Needs.Needs.ThirstSetting, "on"),
            "backroomsFatigue", w.Config.GetString(Backrooms.Needs.Needs.FatigueSetting, "on"));
        sapi.Logger.Notification("[backrooms] play telemetry is on: {0} (turn off with /backrooms telemetry off)", path);
    }

    private string WorldName() => Path.GetFileNameWithoutExtension(sapi.WorldManager.CurrentWorldFilepath ?? "") is { Length: > 0 } n ? n : "world";

    private void CloseFile()
    {
        if (!started) return;
        started = false;
        Record("session", null, "state", "end");
        lock (gate)
        {
            writer?.Dispose();
            writer = null;
        }
    }

    // ------------------------------------------------------------ Recording

    private static string NameOf(Entity who) => who switch
    {
        null => "-",
        EntityPlayer { Player: { } p } => p.PlayerName,
        _ => who.Code.Path + "#" + who.EntityId,
    };

    private static object Clean(object v) => v switch
    {
        double d => double.IsFinite(d) ? Math.Round(d, 2) : 0,
        float f => float.IsFinite(f) ? Math.Round(f, 2) : 0,
        Enum e => e.ToString(),
        null => "",
        _ => v,
    };

    /// <summary>Records an event; see <see cref="Telemetry.Log"/>.</summary>
    internal void Record(string ev, Entity who, params object[] kv)
    {
        if (!Enabled && ev != "session" || sapi == null) return;
        string name = NameOf(who);
        DateTime now = DateTime.UtcNow;
        var e = new Dictionary<string, object>
        {
            ["t"] = now.ToString("yyyy-MM-ddTHH:mm:ss.fffZ", CultureInfo.InvariantCulture),
            ["h"] = Math.Round(sapi.World.Calendar.TotalHours, 3),
            ["p"] = name,
            ["ev"] = ev,
        };
        for (int i = 0; i + 1 < kv.Length; i += 2) e[(string)kv[i]] = Clean(kv[i + 1]);
        lock (gate)
        {
            if (writer == null) return;
            // (Marks, deaths and the session itself are never dropped)
            if (ev is not ("mark" or "death" or "session" or "respawn" or "level" or "stab" or "need" or "damage"))
            {
                long second = now.Ticks / TimeSpan.TicksPerSecond;
                rates.TryGetValue(name, out var rate);
                rate = rate.Second == second ? (second, rate.Count + 1) : (second, 1);
                rates[name] = rate;
                if (rate.Count > MaxPerSecond)
                {
                    dropped[name] = dropped.GetValueOrDefault(name) + 1;
                    return;
                }
            }
            if (ev is not ("pos" or "mark" or "session"))
            {
                if (!rings.TryGetValue(name, out var ring)) rings[name] = ring = new();
                ring.Enqueue((now, e));
                while (ring.Count > 0 && (now - ring.Peek().At).TotalSeconds > RingSeconds) ring.Dequeue();
            }
            writer.WriteLine(JsonSerializer.Serialize(e));
            if ((now - lastFlush).TotalSeconds >= 2 || ev == "session")
            {
                writer.Flush();
                lastFlush = now;
            }
        }
    }

    /// <summary>The last minute of a player's events, oldest first, as small objects.</summary>
    private List<Dictionary<string, object>> RecentOf(string name)
    {
        lock (gate)
        {
            if (!rings.TryGetValue(name, out var ring)) return new();
            DateTime now = DateTime.UtcNow;
            return ring.Where(r => (now - r.At).TotalSeconds <= RingSeconds)
                .Select(r => r.Ev.Where(p => p.Key != "p" && p.Key != "h").ToDictionary(p => p.Key, p => p.Value)).ToList();
        }
    }

    // ------------------------------------------------------------ The tick

    private static bool Live(IServerPlayer p) => p.ConnectionState == EnumClientState.Playing && p.Entity is { Alive: true };

    private PState StateOf(IServerPlayer p)
    {
        if (!states.TryGetValue(p.PlayerUID, out PState s)) states[p.PlayerUID] = s = new PState();
        return s;
    }

    private void OnTick(float dt)
    {
        if (!Enabled || menace?.Layout == null) return;
        bool full = (++tickNo & 1) == 0;
        while (trades.TryDequeue(out var trade))
            Record("trade", sapi.World.AllOnlinePlayers.FirstOrDefault(p => p.PlayerName == trade.Who)?.Entity, "item", trade.What, "price", trade.Price);
        foreach (IServerPlayer player in sapi.World.AllOnlinePlayers.OfType<IServerPlayer>())
        {
            if (!Live(player)) continue;
            EntityPlayer entity = player.Entity;
            PState s = StateOf(player);
            HookDamage(player, entity);
            WatchEating(player, entity, s);
            if (full) Poll(player, entity, s);
        }
        if (full)
            lock (gate)
            {
                // (Say what the throttle dropped)
                if (dropped.Count > 0 && writer != null)
                {
                    foreach (var d in dropped)
                        writer.WriteLine(JsonSerializer.Serialize(new Dictionary<string, object>
                        {
                            ["t"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ", CultureInfo.InvariantCulture), ["h"] = 0, ["p"] = d.Key, ["ev"] = "throttled", ["dropped"] = d.Value,
                        }));
                    dropped.Clear();
                }
                if (writer != null && (DateTime.UtcNow - lastFlush).TotalSeconds >= 2) { writer.Flush(); lastFlush = DateTime.UtcNow; }
            }
    }

    /// <summary>Once a second per player: level, band, stability, the needs, the walked distance and (every 30 s) a position.</summary>
    private void Poll(IServerPlayer player, EntityPlayer entity, PState s)
    {
        MenaceSystem.Assessment a = menace.AssessmentOf(entity);
        // Walked distance (a jump, a gate or a teleport is not walking)
        double x = entity.Pos.X, z = entity.Pos.Z;
        if (!double.IsNaN(s.LastX))
        {
            double step = Math.Sqrt((x - s.LastX) * (x - s.LastX) + (z - s.LastZ) * (z - s.LastZ));
            if (step < 20) s.Walked += step;
        }
        s.LastX = x;
        s.LastZ = z;

        string display = WorldLayout.DisplayNumber(a.Level);
        if (a.Level != s.Level)
        {
            int cls = WorldLayout.SurvivalClass(a.Level);
            string from = s.Level == int.MinValue ? "" : WorldLayout.DisplayNumber(s.Level);
            Record("level", entity, "from", from, "to", display, "band", a.Band, "class", cls, "x", x, "z", z);
            s.Level = a.Level;
            s.Band = a.Band;
        }
        else if (a.Band != s.Band)
        {
            Record("band", entity, "level", display, "from", s.Band < 0 ? "" : s.Band.ToString(), "to", a.Band, "value", a.Value);
            s.Band = a.Band;
        }

        // Stability: crossings of 0.5, 0.3 and 0.1 downwards, back above 0.5, and zero
        double stab = Senses.Stability(entity);
        int tier = stab > 0.5 ? 0 : stab > 0.3 ? 1 : stab > 0.1 ? 2 : stab > 0.005 ? 3 : 4;
        if (tier != s.StabTier)
        {
            string[] names = { "above 0.5", "below 0.5", "below 0.3", "below 0.1", "zero" };
            if (tier > s.StabTier) Record("stab", entity, "crossed", names[tier], "value", stab, "level", display);
            else if (tier == 0) Record("stab", entity, "crossed", names[0], "value", stab, "level", display);
            // (A recovery that stays below 0.5 is only remembered, so the next fall logs again)
            s.StabTier = tier;
        }

        // Needs: the band crossings of thirst and rest, and sleep
        if (Backrooms.Needs.Needs.ThirstOn(sapi.World))
        {
            string band = NeedsMath.ThirstBand(Backrooms.Needs.Needs.HydrationFraction(entity));
            if (band != s.Thirst)
            {
                if (s.Thirst != null) Record("need", entity, "kind", "thirst", "band", band, "from", s.Thirst, "value", Backrooms.Needs.Needs.HydrationFraction(entity) * 100);
                s.Thirst = band;
            }
        }
        if (Backrooms.Needs.Needs.FatigueOn(sapi.World))
        {
            float awake = Backrooms.Needs.Needs.AwakeHours(entity);
            string band = NeedsMath.Band(awake);
            if (band != s.Rest)
            {
                if (s.Rest != null) Record("need", entity, "kind", "rest", "band", band, "from", s.Rest, "value", awake);
                s.Rest = band;
            }
            bool sleeping = EntityBehaviorFatigue.Sleeping(entity);
            if (sleeping != s.Sleeping)
            {
                Record("need", entity, "kind", "sleep", "band", sleeping ? "start" : "end", "value", awake);
                s.Sleeping = sleeping;
            }
        }

        if (--s.PosCountdown <= 0)
        {
            s.PosCountdown = PosSeconds;
            Record("pos", entity, "x", x, "z", z, "level", display, "band", a.Band, "d", s.Walked, "gm", player.WorldData.CurrentGameMode);
            s.Walked = 0;
        }
    }

    /// <summary>Watches the hand: a stack that shrank (or turned into its empty bottle) while the stomach or the hydration rose was eaten or drunk.</summary>
    private void WatchEating(IServerPlayer player, EntityPlayer entity, PState s)
    {
        ItemSlot slot = player.InventoryManager?.ActiveHotbarSlot;
        int index = player.InventoryManager?.ActiveHotbarSlotNumber ?? -1;
        string code = slot?.Itemstack?.Collectible?.Code?.ToString();
        int size = slot?.Itemstack?.StackSize ?? 0;
        float sat = entity.WatchedAttributes.GetTreeAttribute("hunger")?.GetFloat("currentsaturation", -1) ?? -1;
        float hyd = Backrooms.Needs.Needs.ThirstOn(sapi.World) ? Backrooms.Needs.Needs.Hydration(entity) : -1;
        if (s.Slot == index && s.Code != null && (code != s.Code || size < s.Size))
        {
            if (hyd >= 0 && s.Hyd >= 0 && hyd - s.Hyd > 1) Record("drink", entity, "item", s.Code, "hydration", hyd - s.Hyd);
            else if (sat >= 0 && s.Sat >= 0 && sat - s.Sat > 0.5f) Record("eat", entity, "item", s.Code, "satiety", sat - s.Sat);
        }
        s.Slot = index;
        s.Code = code;
        s.Size = size;
        s.Sat = sat;
        s.Hyd = hyd;
    }

    // ------------------------------------------------------------ Events from the game

    private void OnJoin(IServerPlayer player)
    {
        PState s = StateOf(player);
        s.Level = int.MinValue;
        if (player.Entity != null) hooked.Remove(player.Entity.EntityId); // (a new entity object may have a new health behaviour)
        Record("join", player.Entity, "gm", player.WorldData.CurrentGameMode);
    }

    private void OnLeave(IServerPlayer player)
    {
        Record("leave", player.Entity);
        states.Remove(player.PlayerUID);
        if (player.Entity != null) hooked.Remove(player.Entity.EntityId);
        lock (gate)
        {
            rings.Remove(NameOf(player.Entity));
            rates.Remove(NameOf(player.Entity));
        }
    }

    private void OnDeath(IServerPlayer player, DamageSource source)
    {
        MenaceSystem.Assessment a = menace?.AssessmentOf(player.Entity);
        Entity by = source?.GetCauseEntity();
        string cause = by != null ? by.Code.Path : source != null ? source.Type.ToString() : "unknown";
        if (source is ThirstDamageSource) cause = "thirst";
        Record("death", player.Entity, "cause", cause, "level", a == null ? "" : WorldLayout.DisplayNumber(a.Level), "band", a?.Band, "x", player.Entity.Pos.X, "z", player.Entity.Pos.Z);
        if (states.TryGetValue(player.PlayerUID, out PState s)) s.StabTier = 0;
    }

    private void OnRespawn(IServerPlayer player)
    {
        MenaceSystem.Assessment a = menace?.AssessmentOf(player.Entity);
        Record("respawn", player.Entity, "level", a == null ? "" : WorldLayout.DisplayNumber(a.Level), "x", player.Entity.Pos.X, "z", player.Entity.Pos.Z);
    }

    /// <summary>Gives the player's health a listener (once per entity) that logs the damage it takes, after the armour has had its say.</summary>
    private void HookDamage(IServerPlayer player, EntityPlayer entity)
    {
        if (hooked.Contains(entity.EntityId)) return;
        if (entity.GetBehavior<EntityBehaviorHealth>() is not { } health) return;
        hooked.Add(entity.EntityId);
        health.onDamaged += (damage, source) =>
        {
            if (damage > 0 && source != null && source.Type != EnumDamageType.Heal && Enabled)
            {
                Entity by = source.GetCauseEntity();
                Record("damage", entity, "src", by != null ? by.Code.Path : source.Type.ToString(), "type", source.Type, "amount", damage,
                    "hp", Math.Max(0, health.Health - damage), "armour", CrossingSystem.ArmourTier(player));
            }
            return damage;
        };
    }

    private static readonly Regex LootBlock = new(@"cache|crate|supply|stash|locker|chest|cabinet|fridge|vending|box", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private void Loot(IServerPlayer player, Block block, BlockPos pos, string how)
    {
        if (block?.Code == null || block.Code.Domain != "backrooms" || !LootBlock.IsMatch(block.Code.Path)) return;
        PState s = StateOf(player);
        // (Opening the same box again is not another box)
        if (!s.Looted.Add($"{pos.X},{pos.Y},{pos.Z}") && how == "open") return;
        if (s.Looted.Count > 4000) s.Looted.Clear();
        MenaceSystem.Assessment a = menace?.AssessmentOf(player.Entity);
        Record("loot", player.Entity, "block", block.Code.Path, "how", how, "level", a == null ? "" : WorldLayout.DisplayNumber(a.Level));
    }

    private void OnUsedBlock(IServerPlayer player, BlockSelection sel)
    {
        if (!Enabled || sel?.Position == null) return;
        Loot(player, sapi.World.BlockAccessor.GetBlock(sel.Position), sel.Position, "open");
    }

    private void OnBrokeBlock(IServerPlayer player, int oldBlockId, BlockSelection sel)
    {
        if (!Enabled || sel?.Position == null) return;
        Loot(player, sapi.World.GetBlock(oldBlockId), sel.Position, "break");
    }

    private static readonly Regex TradeLine = new(@"^(?<who>.+?) (?<what>(?:sold|bought) .*?) at trader .* and (?<verb>payed|received) (?<n>-?\d+) RG", RegexOptions.Compiled);

    /// <summary>The trader's own audit line ("Name sold 2x... and bought 1x... at trader x, y, z and payed 5 RG") is the trade event.</summary>
    private void OnLogEntry(EnumLogType type, string message, object[] args)
    {
        if (type != EnumLogType.Audit || !Enabled || message == null) return;
        // (Any thread: only parse here, and let the tick log it)
        try
        {
            string line = args is { Length: > 0 } ? string.Format(CultureInfo.InvariantCulture, message, args) : message;
            Match m = TradeLine.Match(line);
            if (!m.Success || !int.TryParse(m.Groups["n"].Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out int n)) return;
            trades.Enqueue((m.Groups["who"].Value, m.Groups["what"].Value, m.Groups["verb"].Value == "payed" ? n : -n));
        }
        catch (Exception) { }
    }

    private readonly System.Collections.Concurrent.ConcurrentQueue<(string Who, string What, int Price)> trades = new();

    // ------------------------------------------------------------ The marker

    private TextCommandResult OnMarkCommand(TextCommandCallingArgs args)
    {
        if (Telemetry.Sys != this || menace?.Layout == null) return TextCommandResult.Error("Not a Backrooms world");
        if (!Enabled) return TextCommandResult.Error("Play telemetry is off (/backrooms telemetry on)");
        Entity who = args.Caller.Entity;
        if (who == null)
        {
            // (From the console: the latest straw dummy)
            who = sapi.World.LoadedEntities.Values.Where(e => e.Alive && Senses.IsTestTarget(e)).OrderByDescending(e => e.EntityId).FirstOrDefault();
            if (who == null) return TextCommandResult.Error("A mark needs a player (or a straw dummy: /backrooms dummies on, /backrooms dummy place)");
        }
        string text = args.Parsers[0].IsMissing ? "" : ((string)args[0]).Trim();
        MenaceSystem.Assessment a = menace.AssessmentOf(who);
        var about = sapi.World.GetEntitiesAround(who.Pos.XYZ, AboutRange, AboutRange / 2, e => e != who && e.Alive && (int)EntityBehaviorMenace.KindOf(e) >= 0)
            .OrderBy(e => e.Pos.DistanceTo(who.Pos.XYZ)).Take(12)
            .Select(e => new Dictionary<string, object>
            {
                ["code"] = e.Code.Path, ["kind"] = EntityBehaviorMenace.KindOf(e).ToString(), ["dist"] = Math.Round(e.Pos.DistanceTo(who.Pos.XYZ), 1),
            }).ToList();
        var health = who.GetBehavior<EntityBehaviorHealth>();
        bool thirstOn = Backrooms.Needs.Needs.ThirstOn(sapi.World), fatigueOn = Backrooms.Needs.Needs.FatigueOn(sapi.World);
        Record("mark", who, "text", text, "x", who.Pos.X, "y", who.Pos.Y, "z", who.Pos.Z, "level", WorldLayout.DisplayNumber(a.Level), "band", a.Band,
            "menace", a.Value, "hp", health?.Health ?? 0, "maxhp", health?.MaxHealth ?? 0, "stability", Senses.Stability(who),
            "thirst", thirstOn ? Backrooms.Needs.Needs.HydrationFraction(who) * 100 : -1, "rest", fatigueOn ? Backrooms.Needs.Needs.RestFraction(who) * 100 : -1,
            "about", about, "recent", RecentOf(NameOf(who)));
        return TextCommandResult.Success("Marked.");
    }
}
