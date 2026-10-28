using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Backrooms.Reality;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Entities;

/// <summary>
/// The entities' director. Every two seconds it weighs how much danger each player is in (the menace: how deep into
/// their level they are, how close to the edge into the next or to a threshold, their Reality Stability, whether they
/// stand in the dark, whether a Reality Shift has put the lights out) and, now and then, does something about it: a
/// sound down the hall, something seen far off, something that follows, something that hunts. Spawn rolls are made
/// once per place (people within 24 blocks of each other share one, for whoever is in most danger), and a pack is
/// clipped to the cap of the current band. Wanderers that mean no
/// harm (Facelings, the city's Hounds) are kept around separately.
///
/// Entities are put down out of the player's reach, from the layout (so never inside a wall or a sealed room), and
/// despawn once they have done their job (see <see cref="EntityBehaviorMenace"/>).
/// </summary>
public partial class MenaceSystem : ModSystem
{
    /// <summary>The director's tick; the rates (<see cref="EncounterRoll"/>) are worked out for exactly this, so it is derived from them.</summary>
    private const int IntervalMs = (int)(EncounterRoll.TickSeconds * 1000);
    /// <summary>Nothing is put down closer than this to anyone.</summary>
    private const int NoSpawnRadius = 12;
    /// <summary>After a close call, the Backrooms let the player breathe for a while.</summary>
    private const int CalmMs = 90_000;

    public sealed class Assessment
    {
        public int Level;
        public MenaceBand Band;
        public double Value;
        public double Depth;
        public int ToNextLevel;
        public bool Dark;
        /// <summary>Level 11: everything there leaves you alone unless provoked.</summary>
        public bool Passive;
        public bool Snackrooms;
        public bool Subway;
        /// <summary>A Level 1 Flickering has the lights out round the player.</summary>
        public bool Flickering;
        /// <summary>The worst kind of place in a level (a Red Room, the far dark of Level 8): the hunts come even where they otherwise would not.</summary>
        public bool Worst;
        /// <summary>Safe only because a wanderer is near (the harmless things still come and go).</summary>
        public bool NearWanderer;
        /// <summary>A Reality Shift is on.</summary>
        public bool Shift;
        /// <summary>The den the player is in, if any: what lives there is what comes.</summary>
        public DenKind Den;
        /// <summary>How long (in-game hours) since the player last rested by a fire, a ward, a wanderer or at home.</summary>
        public double OutHours;
        /// <summary>How much noise the player has made lately, from 0 to 1.</summary>
        public double Noise;
        /// <summary>Level 94: inside the castle on the mountain, where only its Robo-Men stand guard.</summary>
        public bool Castle;
        /// <summary>Level 94: facing the King's trial. What he raised hunts the player, and nothing else comes.</summary>
        public bool Trial;
    }

    private sealed class Watch
    {
        public Assessment Now = new();
        public long CalmUntilMs;
        /// <summary>In-game hours: when the player's Flickering ends, and when the next may come.</summary>
        public double FlickerUntilHours = -1, NextFlickerHours;
        /// <summary>Noise made lately (decays), and how many seconds in a row the player has been somewhere restful.</summary>
        public double Noise, RestingFor;
        /// <summary>In-game hours: when the next Screaming may come.</summary>
        public double NextScreamHours;
        /// <summary>World milliseconds before which this one hears no more distant sounds (see <see cref="Roster.SoundGapSeconds"/>).</summary>
        public long NextSoundMs;
        /// <summary>World milliseconds when the last body (a glimpse, stalker or hunter, the Flickering, the Screaming) and the last distant sound were put down for this place (EncounterRoll's hard gaps).</summary>
        public long LastBodyMs = NeverMs, LastSoundMs = NeverMs;
        /// <summary>Where this one has been looking lately: (world ms, flat view direction), the last <see cref="RecentViewMs"/> or so.</summary>
        public readonly List<(long Ms, double X, double Z)> Views = new();
    }

    /// <summary>"Never": far enough back that every hard gap has passed.</summary>
    private const long NeverMs = long.MinValue / 4;

    /// <summary>How long the rats' Screaming keeps the lights failing, and how long before another can come (in-game hours).</summary>
    private const double ScreamHours = 0.5, ScreamCooldownHours = 24;

    /// <summary>Player attribute (kept with the player) holding the in-game hour they last rested.</summary>
    public const string RestedKey = "backrooms:restedAt";

    /// <summary>How much the time out since resting adds to the menace per in-game hour (an hour is two real minutes), and the most it adds.</summary>
    private const double ExposurePerHour = 0.03, ExposureMax = 0.3;

    /// <summary>How long someone must stay somewhere restful before it counts, and how near home in Level 0 counts as home.</summary>
    private const double RestSeconds = 60, HomeRadius = 48;

    /// <summary>How fast noise dies away (per second), and how much breaking something or running makes.</summary>
    private const double NoiseDecay = 0.05, BreakNoise = 0.3, RunNoisePerSecond = 0.08;

    /// <summary>
    /// How loud things are for whatever listens (the noise bus; 1 carries as far as an entity's full hearing). See
    /// docs/design/entity-ai-overhaul/README.md, section 4.2.
    /// </summary>
    public const double RunLoudness = 0.4, JumpLoudness = 0.3, BreakLoudness = 0.5, FightLoudness = 0.6, DoorLoudness = 0.3,
        QuietDoorLoudness = 0.05, FireLoudness = 0.4, ImpactLoudness = 0.5, CryLoudness = 0.6;

    /// <summary>The noises of the last two seconds, for entities that listen.</summary>
    public NoiseBus Noises { get; } = new();

    /// <summary>Player attribute (synced to the client, which darkens the world) holding when a Flickering ends.</summary>
    public const string FlickerKey = "backrooms:flickerUntil";

    /// <summary>How long a Flickering lasts and how long until another can come, in in-game hours (an hour is two real minutes).</summary>
    private const double FlickerHours = 0.75, FlickerCooldownHours = 20;

    /// <summary>How the world's "backroomsMenace" setting scales things.</summary>
    /// <param name="MixDanger">Added to the level's danger in the glimpse/stalk/hunt mix (more of the bodies stalk and hunt).</param>
    /// <param name="CapBonus">Added to the menacing cap of the approach and threshold bands, and of the heartland when <paramref name="HeartCapBonus"/> is.</param>
    public readonly record struct Difficulty(string Code, double Spawns, double Damage, bool Entities, double MixDanger = 0, int CapBonus = 0, int HeartCapBonus = 0)
    {
        /// <summary>How much the set pieces (night visits, hive waves, nest refills, the rare events) scale with the setting: the square root of <see cref="Spawns"/>, so they thicken more slowly than the ordinary spawns (1 at off, 2.35 at Normal).</summary>
        public double SetPieceScale => Math.Sqrt(Spawns);
    }

    /// <summary>The six settings (dialin.md 3.1; shifted up one step in the progression round, plan.md 3.7: the dial-in's high rate, 5.5, is the new normal, and the dial-in's normal, 3.5, is now low). Spawns divides the mean intervals; "normal" is the fourth.</summary>
    private static readonly Difficulty[] Difficulties =
    {
        new("off", 1, 0, false),
        new("verylow", 2, 0.5, true),
        new("low", 3.5, 0.75, true),
        new("normal", 5.5, 1, true),
        new("high", 8.5, 1.3, true, 0.3, 1),
        new("veryhigh", 13, 1.6, true, 0.6, 1, 1),
    };

    private static readonly Difficulty NormalSetting = Difficulties[3];

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private RealitySystem reality;
    private readonly Dictionary<long, Watch> watches = new();
    private readonly Dictionary<string, EntityProperties> types = new();
    private Random rand;

    public Difficulty Setting { get; private set; } = NormalSetting;

    /// <summary>The world's layout (null outside a Backrooms world), for entities that need to know where they are.</summary>
    public WorldLayout Layout => layout;

    /// <summary>Log what the entities decide (/backrooms entitylog).</summary>
    public bool Logging;

    /// <summary>Stops the director putting anything down or playing distant sounds (/backrooms director, for testing).</summary>
    public bool Paused;

    /// <summary>When any Faceling last shoved someone (the shove's own noise must not set the neighbours off).</summary>
    public long LastShoveMs = -1_000_000;

    /// <summary>
    /// Headless tests (/backrooms dummies): the director also directs the straw dummies put down by /backrooms
    /// encounter, as if they were players, so what gathers round one or two of them can be watched without a client.
    /// </summary>
    public bool DirectsDummies;
    private readonly List<Entity> dummies = new();
    private int dummyTicks;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.1;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        rand = new Random();
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            reality = api.ModLoader.GetModSystem<RealitySystem>();
            EntityBehaviorMenace.NewSession();
            string code = api.World.Config.GetString("backroomsMenace", "normal");
            Setting = Difficulties.FirstOrDefault(d => d.Code == code, NormalSetting);
            if (Setting.Code != code) api.Logger.Notification("[backrooms] unknown backroomsMenace '{0}': using normal", code);
            Roster.ApplySetting(Setting.MixDanger, Setting.CapBonus, Setting.HeartCapBonus);
            foreach (string entity in Roster.AllCodes.Append("backrooms:wanderer-male").Append("backrooms:partygoer").Append("backrooms:partygoer-intern"))
            {
                EntityProperties type = api.World.GetEntityType(new AssetLocation(entity));
                if (type == null) api.Logger.Warning("[backrooms] entity type {0} is missing", entity);
                else types[entity] = type;
            }
            api.Event.RegisterGameTickListener(_ => SampleViews(), e => api.Logger.Error("[backrooms] view sampling: {0}", e), ViewSampleMs, 1000);
            tickListener = api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] entity director: {0}", e), IntervalMs, 1000);
            // Breaking things open is loud
            api.Event.DidBreakBlock += OnBrokeBlock;
            StartListening(api);
        });
        api.Event.PlayerDisconnect += OnPlayerDisconnect;
        StartHives(api);

        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        command
            .BeginSubCommand("menace")
                .WithDescription("Shows how much danger you are in, and the entities around you")
                .RequiresPlayer()
                .HandleWith(OnMenaceCommand)
            .EndSubCommand()
            .BeginSubCommand("feltrate")
                .WithDescription("Dry-runs the director's placement for glimpses, stalkers and hunters at the straw dummy (latest) or you: success per kind, why spots were refused, and the felt bodies an hour (the rate check's, times the success). Args: level (its id, 94 is 13, or here), band (heartland, approach, threshold; default your own), tries (60)")
                .WithArgs(api.ChatCommands.Parsers.Word("level"), api.ChatCommands.Parsers.OptionalWord("band"), api.ChatCommands.Parsers.OptionalInt("tries"))
                .HandleWith(OnFeltRateCommand)
            .EndSubCommand()
            .BeginSubCommand("creativehunts")
                .WithDescription("Whether a creative-mode player is hunted like anyone else (on/off; toggles without), for testing")
                .WithArgs(api.ChatCommands.Parsers.OptionalBool("on"))
                .HandleWith(args =>
                {
                    CreativeHunted = args.Parsers[0].IsMissing ? !CreativeHunted : (bool)args[0];
                    return TextCommandResult.Success("Creative is hunted " + (CreativeHunted ? "on" : "off"));
                })
            .EndSubCommand()
            .BeginSubCommand("ratecheck")
                .WithDescription("Simulates the director's rolls for hours (default 50) in a level (its id, 94 is 13) and band (heartland, approach, threshold, den) and prints bodies and sounds per hour (the rolls only: real rates are lower, since a body also waits for fewer kinds of menacing thing about than the level allows (one in Classes 0 to 2, two in 3 to 5) and for a spot to put it; the optional menacing=<n> says how many kinds are about; awake=<hours> applies the thirst-and-fatigue multiplier for that many awake hours); \"ratecheck here\" uses your own level and band (and your own multiplier)")
                .WithArgs(api.ChatCommands.Parsers.Word("level"), api.ChatCommands.Parsers.OptionalWord("band"), api.ChatCommands.Parsers.OptionalWord("hours"), api.ChatCommands.Parsers.OptionalWord("menacing"), api.ChatCommands.Parsers.OptionalWord("awake"))
                .HandleWith(OnRateCheckCommand)
            .EndSubCommand()
            .BeginSubCommand("partycheck")
                .WithDescription("Simulates the rolls for hours of players standing in a line <spacing> blocks apart in one level and band, with the party rule (new) or as it was before 0.610.2 (old: places of 24 blocks, one roll each, no bonus), and prints the bodies and sounds an hour in all and for each player (the rolls only, as ratecheck): /backrooms partycheck <level> <band> <players> <spacing> [hours] [old|new]")
                .WithArgs(api.ChatCommands.Parsers.Word("level"), api.ChatCommands.Parsers.Word("band"), api.ChatCommands.Parsers.Int("players"), api.ChatCommands.Parsers.Int("spacing"), api.ChatCommands.Parsers.OptionalWord("hours"), api.ChatCommands.Parsers.OptionalWord("mode"))
                .HandleWith(OnPartyCheckCommand)
            .EndSubCommand()
            .BeginSubCommand("encounter")
                .WithDescription("Puts down an entity (any Backrooms entity code: smiler, hound, faceling, deathmoth-male, deathrat, wretch, ...) for an encounter (ambient, glimpse, stalk, hunt; default hunt), optionally at a distance. From the console, give x and z: it targets a straw dummy put down there.")
                .WithArgs(api.ChatCommands.Parsers.Word("entity"), api.ChatCommands.Parsers.OptionalWord("kind"), api.ChatCommands.Parsers.OptionalInt("x"), api.ChatCommands.Parsers.OptionalInt("z"), api.ChatCommands.Parsers.OptionalInt("distance"))
                .HandleWith(OnEncounterCommand)
            .EndSubCommand()
            .BeginSubCommand("flicker")
                .WithDescription("Starts a Level 1 Flickering round you: the lights go out and Hounds hunt until they return")
                .HandleWith(args =>
                {
                    if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
                    // (From the console: the latest straw dummy)
                    Entity entity = args.Caller.Entity ?? LatestDummy(args);
                    if (entity == null) return TextCommandResult.Error("Needs a player, or a straw dummy put down first");
                    if (!watches.TryGetValue(entity.EntityId, out Watch watch)) watches[entity.EntityId] = watch = new Watch();
                    Assess(entity, watch);
                    StartFlicker(entity, watch, Roster.For(1));
                    return TextCommandResult.Success(watch.Now.Level == 1 ? "The lights fail" : "Hounds are coming (the lights only fail in Level 1)");
                })
            .EndSubCommand()
            .BeginSubCommand("scream")
                .WithDescription("Starts the rats' Screaming round you: the lights fail and a pack runs past")
                .RequiresPlayer()
                .HandleWith(args =>
                {
                    if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
                    Entity entity = args.Caller.Entity;
                    if (!watches.TryGetValue(entity.EntityId, out Watch watch)) watches[entity.EntityId] = watch = new Watch();
                    Assess(entity, watch);
                    StartScreaming(entity, watch);
                    return TextCommandResult.Success(watch.Now.Level is 1 or 2 ? "Something is screaming" : "The rats are coming (the Screaming is Level 2's; the lights only fail in Levels 1 and 2 here)");
                })
            .EndSubCommand()
            .BeginSubCommand("entitylog")
                .WithDescription("Logs what the entities decide to the server log (on/off)")
                .WithArgs(api.ChatCommands.Parsers.OptionalBool("on"))
                .HandleWith(args =>
                {
                    Logging = args.Parsers[0].IsMissing ? !Logging : (bool)args[0];
                    return TextCommandResult.Success("Entity log " + (Logging ? "on" : "off"));
                })
            .EndSubCommand()
            .BeginSubCommand("dummies")
                .WithDescription("Headless tests: the director also directs the straw dummies put down by /backrooms encounter (on/off), and reports where each stands")
                .WithArgs(api.ChatCommands.Parsers.OptionalBool("on"))
                .HandleWith(OnDummiesCommand)
            .EndSubCommand()
            .BeginSubCommand("facelingtest")
                .WithDescription("Has the nearest Faceling greet you as if right-clicked, and says which gate it knows of and which way it will point. From the console, give x and z: the Faceling nearest there greets the straw dummy there")
                .WithArgs(api.ChatCommands.Parsers.OptionalInt("x"), api.ChatCommands.Parsers.OptionalInt("z"))
                .HandleWith(OnFacelingTestCommand)
            .EndSubCommand();
        RegisterProbeCommands(api, command);
        RegisterHiveCommands(api, command);
        RegisterStealerCommands(api, command);
        RegisterPathTestCommands(api, command);
        RegisterWalkerCommands(api, command);
    }

    private long tickListener;

    private void OnBrokeBlock(IServerPlayer player, int oldBlockId, BlockSelection sel) =>
        MakeNoise(player?.Entity, BreakNoise, sel == null ? null : sel.Position.ToVec3d().Add(0.5, 0.5, 0.5), BreakLoudness, "break");

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        long id = player.Entity?.EntityId ?? -1;
        watches.Remove(id);
        shames.Remove(id);
        jumping.Remove(id);
        ambientNextMs.Remove(id);
    }

    public override void Dispose()
    {
        if (sapi != null)
        {
            // (The hooks are lambda-free so a world reopened in this process does not leave handlers on a dead server)
            sapi.Event.DidBreakBlock -= OnBrokeBlock;
            sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
            if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
            StopListening(sapi);
            StopHives(sapi);
        }
        // (Static, so it would outlast this world into the next one opened in the same process)
        Senses.LightsOut = false;
        CreativeHunted = false;
        Perception.Reset();
        BlockEntityClumpRemnant.Live.Clear();
        base.Dispose();
    }

    // ================= Menace =================

    /// <summary>The latest assessment for a player (or a test target), worked out now if there is none yet.</summary>
    public Assessment AssessmentOf(Entity target)
    {
        if (target == null || layout == null) return new Assessment { Band = MenaceBand.Safe };
        if (!watches.TryGetValue(target.EntityId, out Watch watch))
        {
            watches[target.EntityId] = watch = new Watch();
            Assess(target, watch);
        }
        return watch.Now;
    }

    /// <summary>Called when something has just hurt a player, or a hunt has ended: a while of calm follows.</summary>
    public void NoteCloseCall(Entity target)
    {
        if (target != null && watches.TryGetValue(target.EntityId, out Watch watch))
            watch.CalmUntilMs = sapi.World.ElapsedMilliseconds + (long)(CalmMs * (1 - 0.5 * Danger.OfLevel(watch.Now.Level)));
    }

    /// <summary>
    /// Something the player did was loud (breaking a box open, prying a door, lighting a fire): it carries, and what
    /// hunts by sound comes to see. Amounts add up to at most 1, and die away over half a minute or so. The noise is
    /// also put on the noise bus, where it was made (the player's feet unless <paramref name="at"/> says), as loud as
    /// <paramref name="loudness"/> (by default the amount).
    /// </summary>
    public void MakeNoise(Entity target, double amount, Vec3d at = null, double? loudness = null, string source = "noise")
    {
        if (target == null || layout == null) return;
        if (!watches.TryGetValue(target.EntityId, out Watch watch)) watches[target.EntityId] = watch = new Watch();
        watch.Noise = Math.Min(1, watch.Noise + amount);
        RaiseNoise(at ?? target.Pos.XYZ, loudness ?? amount, source, target);
    }

    /// <summary>
    /// Puts a noise on the noise bus only (it does not raise anyone's menace): a fight, a cry, a door, a stone landing.
    /// <paramref name="who"/> is whom it gives away (a player, for a noise they made or a fight they are in).
    /// </summary>
    public void RaiseNoise(Vec3d at, double loudness, string source, Entity who)
    {
        if (layout == null || at == null) return;
        Noises.Raise(at, loudness, source, who, sapi.World.ElapsedMilliseconds);
        NestHeard(at, loudness, who);
        if (Logging && source != "run") sapi.Logger.Notification("[backrooms] noise {0} {1:0.00} at {2:0},{3:0},{4:0}{5}", source, loudness, at.X, at.Y, at.Z, who == null ? "" : " by " + who.Code.Path + " #" + who.EntityId);
    }

    /// <summary>Marks a Faceling put down as Evolved (for its health).</summary>
    private const string EvolvedKey = "backrooms:evolvedFaceling";

    private readonly Dictionary<long, List<(double Amount, long Start, long End)>> shames = new();

    /// <summary>
    /// Raises a player's menace by <paramref name="amount"/> for <paramref name="minutes"/> real minutes, fading away
    /// evenly over them (killing something docile: a Faceling). Kept in memory only, per player; they add up.
    /// </summary>
    public void Shame(Entity player, double amount, double minutes)
    {
        if (player == null || amount <= 0 || minutes <= 0) return;
        long now = sapi.World.ElapsedMilliseconds;
        if (!shames.TryGetValue(player.EntityId, out var list)) shames[player.EntityId] = list = new();
        list.Add((amount, now, now + (long)(minutes * 60_000)));
        if (Logging) sapi.Logger.Notification("[backrooms] shame {0:0.00} for {1} minutes on {2} (now {3:0.00})", amount, minutes, player.Code.Path, ShameOf(player));
    }

    /// <summary>What shame is on someone now, from 0 up.</summary>
    public double ShameOf(Entity target)
    {
        if (!shames.TryGetValue(target.EntityId, out var list)) return 0;
        long now = sapi.World.ElapsedMilliseconds;
        list.RemoveAll(s => s.End <= now);
        double sum = 0;
        foreach (var s in list) sum += s.Amount * (s.End - now) / (double)(s.End - s.Start);
        return sum;
    }

    private void Assess(Entity target, Watch watch)
    {
        Assessment a = watch.Now;
        Rate(a, (int)Math.Floor(target.Pos.X), target.Pos.Y, (int)Math.Floor(target.Pos.Z));
        // Level 94 by night: whoever stands quite still is taken for a doll, and nothing comes for them; in the castle,
        // the Robo-Men only stir once someone has touched something there
        a.Trial = false;
        if (a.Level == WorldLayout.Motion && target is EntityPlayer motionPlayer)
        {
            if (Regions.MotionSystem.InTrial(motionPlayer))
            {
                a.Trial = true;
                a.Band = MenaceBand.Threshold;
            }
            else if (a.Castle) a.Band = Regions.MotionSystem.CastleAlarmed(motionPlayer) ? MenaceBand.Threshold : MenaceBand.Safe;
            else if (a.Band != MenaceBand.Safe && Regions.MotionSystem.PlayingDoll(motionPlayer)) a.Band = MenaceBand.Safe;
        }
        // Level 974: for a few minutes after waking from Kitty's House, nothing comes ("somewhere just as safe")
        if (target is EntityPlayer kittyGuest && Regions.L974System.Watched(kittyGuest)) a.Band = MenaceBand.Safe;
        // Nothing hostile closes in on someone keeping company with a wanderer
        a.NearWanderer = false;
        if (a.Band != MenaceBand.Safe && sapi.World.GetNearestEntity(target.Pos.XYZ, 12, 4, e => e.Alive && e.Code.Path.StartsWith("wanderer", StringComparison.Ordinal)) != null)
        {
            a.Band = MenaceBand.Safe;
            a.NearWanderer = true;
        }
        a.Flickering = watch.FlickerUntilHours > sapi.World.Calendar.TotalHours;
        a.Shift = (reality?.ShiftStrength ?? 0) > 0;
        a.Dark = a.Flickering || Senses.InDark(target);
        a.OutHours = TimeOut(target, watch, a);
        a.Noise = watch.Noise;
        if (a.Band == MenaceBand.Safe)
        {
            a.Value = 0;
            return;
        }
        double value = a.Band switch { MenaceBand.Heartland => 0.15, MenaceBand.Approach => 0.5, _ => 0.85 };
        value += 0.25 * (1 - Math.Clamp(Senses.Stability(target), 0, 1));
        if (a.Dark) value += 0.15;
        if (a.Flickering) value += 0.3;
        value += 0.4 * (reality?.ShiftStrength ?? 0);
        // The longer you are out, the more the Backrooms notice you; and what hears you comes
        value += Math.Min(ExposureMax, ExposurePerHour * a.OutHours);
        value += 0.3 * a.Noise;
        value += ShameOf(target);
        if (sapi.World.ElapsedMilliseconds < watch.CalmUntilMs) value -= 0.3;
        a.Value = Math.Clamp(value, 0, 1);
    }

    /// <summary>
    /// Keeps the player's noise and time-out up to date (called every assessment) and returns how many in-game hours it
    /// is since they last rested: a minute by a lit fire or burning Firesalt, beside a wanderer, somewhere nothing
    /// hostile goes, asleep, or at home (in Level 0, near where they wake up).
    /// </summary>
    private double TimeOut(Entity target, Watch watch, Assessment a)
    {
        double seconds = EncounterRoll.TickSeconds;
        if (target is EntityAgent agent && Senses.Running(agent))
        {
            watch.Noise = Math.Min(1, watch.Noise + RunNoisePerSecond * seconds);
            RaiseNoise(target.Pos.XYZ, RunLoudness, "run", target);
        }
        watch.Noise = Math.Max(0, watch.Noise - NoiseDecay * seconds);

        double now = sapi.World.Calendar.TotalHours;
        if (!target.Attributes.HasAttribute(RestedKey)) target.Attributes.SetDouble(RestedKey, now);
        bool restful = a.Band == MenaceBand.Safe || Wards.Warded(sapi.World, target.Pos.XYZ, 6) || AtHome(target)
            || target is EntityAgent { MountedOn: Vintagestory.GameContent.BlockEntityBed };
        watch.RestingFor = restful ? watch.RestingFor + seconds : 0;
        if (watch.RestingFor >= RestSeconds) target.Attributes.SetDouble(RestedKey, now);
        return Math.Max(0, now - target.Attributes.GetDouble(RestedKey, now));
    }

    /// <summary>Whether a player is at home: near their spawn point (the last bed they slept in or a temporal gear), in whatever level that is.</summary>
    private bool AtHome(Entity target)
    {
        if (target is not EntityPlayer { Player: IServerPlayer player }) return false;
        FuzzyEntityPos home = player.GetSpawnPosition(false);
        if (home == null) return false;
        double dx = home.X - target.Pos.X, dz = home.Z - target.Pos.Z;
        return dx * dx + dz * dz <= HomeRadius * HomeRadius;
    }

    private void Rate(Assessment a, int gx, double y, int gz)
    {
        int mx = WorldLayout.MacroOf(gx), mz = WorldLayout.MacroOf(gz);
        int level = layout.LevelAt(mx, mz);
        a.Level = level;
        // (A watch's assessment is used again every time: what only some levels set must not linger from the last level)
        a.Den = DenKind.None;
        a.Worst = false;
        a.Snackrooms = level == 6 && layout.IsSnackrooms(mx, mz);
        a.Subway = level == 11 && y < geometry.CityFloorY - 1;
        // The city's effect: nothing there attacks unless provoked. It does not reach down into the subway
        a.Passive = level == 11 && !a.Subway;
        a.Depth = layout.LevelDepth(gx, gz, level);
        a.ToNextLevel = layout.BlocksToNextLevel(gx, gz, level);
        a.Castle = level == WorldLayout.Motion && layout.InCastle(gx, gz);
        if (level == WorldLayout.Motion && !a.Castle)
        {
            // Motion is safe by day, and indoors; at night the Animations come out, worst in the towns and near the
            // mountain, where the King keeps them
            Tile here = layout.TileAt(gx, gz);
            bool night = Regions.MotionSystem.IsNight(sapi.World.Calendar);
            double fromMountain = layout.MotionDistance(gx, gz);
            bool indoors = RoofBits.IsSloped(here.Roof) && !RoofBits.IsLowered(here.Roof) && here.Kind is TileKind.Floor or TileKind.Doorway; // (not a porch)
            a.Band = !night || indoors ? MenaceBand.Safe
                : here.Floor is FloorKind.MotionConcrete || fromMountain < 400 || layout.InMotionTown(gx, gz) ? MenaceBand.Threshold : MenaceBand.Approach;
            return;
        }
        // The five kept as 14-18 (each level's own case): calm until their plans say otherwise
        switch (level)
        {
            case WorldLayout.RunLevel: a.Band = MenaceBand.Safe; return;
            case WorldLayout.FunLevel: a.Band = Regions.FunSystem.BandAt(layout, gx, gz); return;
            case WorldLayout.TheEnd:
                // Devoid of all life, but in the dark of a collapse something grins now and then
                a.Band = layout.TileAt(gx, gz).Zone == 3 ? MenaceBand.Heartland : MenaceBand.Safe;
                return;
            case WorldLayout.Hub: a.Band = MenaceBand.Safe; return;
            case WorldLayout.Level974: a.Band = MenaceBand.Safe; return;
            // Level 3999: safe, but in the dark of its Neon Blackout (3999.1), where things hunt
            case WorldLayout.Level3999: a.Band = layout.L3999DarkAt(gx, gz) ? MenaceBand.Threshold : MenaceBand.Safe; return;
            // Level 188: safe in a room with its door shut, the heart in the courtyard and below, the edge upstairs and by the windows out
            case WorldLayout.Level188: a.Band = Regions.L188System.BandAt(layout, geometry, gx, y, gz); return;
        }
        if (a.Snackrooms || layout.IsSanctuary(gx, gz, level))
        {
            a.Band = MenaceBand.Safe;
            return;
        }

        WorldLayout.DarkPlace dark = layout.DarkPlaceAt(gx, gz, level);
        a.Worst = dark == WorldLayout.DarkPlace.Worst;
        MenaceBand band = MenaceBand.Heartland;
        if (a.Depth >= 0.5 || dark == WorldLayout.DarkPlace.Bad || a.Subway) band = MenaceBand.Approach;
        if (a.Depth >= 0.8 || a.ToNextLevel <= 40 || dark == WorldLayout.DarkPlace.Worst || layout.NearThreshold(gx, gz)) band = MenaceBand.Threshold;
        // In a den, it is as dangerous as the edge of the level, wherever the den is
        a.Den = layout.DenNear(gx, gz) is { } den && Roster.DenActive(level, den.Kind) ? den.Kind : DenKind.None;
        if (a.Den != DenKind.None) band = MenaceBand.Threshold;
        // When the lights fail, even the heart of the Lobby is watched from the dark
        if (level == 0 && band == MenaceBand.Heartland && (reality?.ShiftStrength ?? 0) > 0) band = MenaceBand.Approach;
        // Level 7: what matters is how deep you dive (the twilight zone, then the midnight zone and the abyss)
        if (level == 7) band = y < geometry.FloorY - WorldLayout.AbyssDepth ? MenaceBand.Threshold : y < geometry.FloorY - WorldLayout.MidnightDepth ? MenaceBand.Approach : MenaceBand.Heartland;
        // The calm levels: the office is where people rest, the fields are where they farm, the city leaves you be
        if (level is 4 or 10 && band == MenaceBand.Heartland) band = MenaceBand.Safe;
        if (level == 11 && !a.Subway) band = MenaceBand.Heartland;
        a.Band = band;
    }

    // ================= The director =================

    private void OnTick(float dt)
    {
        long started = System.Diagnostics.Stopwatch.GetTimestamp();
        try { Tick(); }
        finally { NoteTickCost(System.Diagnostics.Stopwatch.GetTimestamp() - started); }
    }

    /// <summary>
    /// Drops what is kept for entities that are gone (a player who left whose entity was already unloaded at disconnect,
    /// so <see cref="OnPlayerDisconnect"/> could not name it). Looks only now and then.
    /// </summary>
    private void PruneGone()
    {
        long now = sapi.World.ElapsedMilliseconds;
        if (now < nextPruneMs) return;
        nextPruneMs = now + 60_000;
        var live = new HashSet<long>();
        foreach (IPlayer online in sapi.World.AllOnlinePlayers) if (online.Entity != null) live.Add(online.Entity.EntityId);
        foreach (Entity dummy in dummies) live.Add(dummy.EntityId);
        foreach (long id in watches.Keys.Where(id => !live.Contains(id)).ToList()) watches.Remove(id);
        foreach (long id in shames.Keys.Where(id => !live.Contains(id)).ToList()) shames.Remove(id);
        foreach (long id in jumping.Keys.Where(id => !live.Contains(id)).ToList()) jumping.Remove(id);
        foreach (long id in ambientNextMs.Keys.Where(id => !live.Contains(id)).ToList()) ambientNextMs.Remove(id);
    }

    private long nextPruneMs;

    private void Tick()
    {
        Senses.LightsOut = (reality?.ShiftStrength ?? 0) > 0.5;
        PruneGone();
        if (Paused) return;
        // Assess everyone first (players, and the dummies if they are directed), then direct them by place
        var directed = new List<(Entity Entity, Watch Watch, bool Creative)>();
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity == null || !player.Entity.Alive) continue;
            if (player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
            EntityPlayer entity = player.Entity;
            if (!watches.TryGetValue(entity.EntityId, out Watch watch)) watches[entity.EntityId] = watch = new Watch();
            Assess(entity, watch);
            NoteDen(entity, watch.Now);
            directed.Add((entity, watch, player.WorldData.CurrentGameMode == EnumGameMode.Creative));
        }
        if (DirectsDummies)
        {
            dummies.RemoveAll(d => !d.Alive);
            foreach (Entity dummy in dummies)
            {
                if (!watches.TryGetValue(dummy.EntityId, out Watch watch)) watches[dummy.EntityId] = watch = new Watch();
                Assess(dummy, watch);
                NoteDen(dummy, watch.Now);
                directed.Add((dummy, watch, false));
            }
        }
        DirectByPlace(directed);
        if (DirectsDummies) ReportDummies();
    }

    /// <summary>Players (and dummies) in the same level this close share one spawn roll, a party's (README section 5; MenaceSystem.Party.cs).</summary>
    private const double PlaceRadius = PartyRadius, PlaceHeight = PartyHeight;

    /// <summary>
    /// Directs everyone, rolling for a spawn once per party: those within <see cref="PlaceRadius"/> blocks of each other
    /// in the same level (greedily, each joining the first group that has a member that near) share one roll, made for
    /// the member in the most danger (the highest menace), at PartyFactor times the rate; the Flickering and the Screaming are rolled with it and the arrival is for a member drawn at random. Wanderers stay per person.
    /// Someone alone in their place is directed exactly as before.
    /// </summary>
    private void DirectByPlace(List<(Entity Entity, Watch Watch, bool Creative)> directed)
    {
        List<List<int>> groups = PartyGroups(directed.Count, (i, j) =>
        {
            Entity e = directed[i].Entity, o = directed[j].Entity;
            Assessment ai = directed[i].Watch.Now, aj = directed[j].Watch.Now;
            return ai.Level == aj.Level && ai.Snackrooms == aj.Snackrooms && ai.Castle == aj.Castle
                && Math.Abs(e.Pos.Y - o.Pos.Y) <= PlaceHeight && Within(e.Pos.X - o.Pos.X, e.Pos.Z - o.Pos.Z);
        });
        foreach (List<int> group in groups)
        {
            // Only someone who can be hunted rolls (not a creative player, the King's trial, or the Safe band); a real
            // player's place is not rolled for the dummies in it
            bool anyPlayer = group.Any(i => directed[i].Entity is EntityPlayer);
            int rolls = -1;
            var mates = new List<(Entity Entity, Watch Watch)>();
            foreach (int i in group)
            {
                (Entity entity, Watch watch, bool creative) = directed[i];
                if (creative && !CreativeHunted || watch.Now.Trial || watch.Now.Band == MenaceBand.Safe || anyPlayer && entity is not EntityPlayer) continue;
                mates.Add((entity, watch));
                if (rolls < 0 || watch.Now.Value > directed[rolls].Watch.Now.Value) rolls = i;
            }
            // The place shares its body and sound clocks: the roller sees the latest of the group's, and all are stamped with the result
            if (rolls >= 0)
                foreach (int i in group)
                {
                    directed[rolls].Watch.LastBodyMs = Math.Max(directed[rolls].Watch.LastBodyMs, directed[i].Watch.LastBodyMs);
                    directed[rolls].Watch.LastSoundMs = Math.Max(directed[rolls].Watch.LastSoundMs, directed[i].Watch.LastSoundMs);
                }
            foreach (int i in group) Direct(directed[i].Entity, directed[i].Watch, directed[i].Creative, i == rolls, mates);
            if (rolls >= 0)
            {
                // (The arrival may have been for another member than the roller: the latest of the group's clocks is the group's)
                long body = group.Max(i => directed[i].Watch.LastBodyMs), sound = group.Max(i => directed[i].Watch.LastSoundMs);
                foreach (int i in group)
                {
                    directed[i].Watch.LastBodyMs = body;
                    directed[i].Watch.LastSoundMs = sound;
                }
            }
        }
    }

    /// <summary>Logs what is about the straw dummies (see <see cref="DirectsDummies"/>) every half minute.</summary>
    private void ReportDummies()
    {
        if (!Logging || ++dummyTicks % 15 != 0) return;
        foreach (Entity dummy in dummies)
        {
            Watch watch = watches[dummy.EntityId];
            int own = sapi.World.GetEntitiesAround(dummy.Pos.XYZ, 64, 24, e => e.Alive && EntityBehaviorMenace.OwnerOf(e) == dummy.EntityId && EntityBehaviorMenace.KindOf(e) != Encounter.Ambient).Length;
            sapi.Logger.Notification("[backrooms] about {0} #{1}: {2} menacing within 64 blocks ({3} its own), band {4}, menace {5:0.00}, cap {6}",
                dummy.Code.Path, dummy.EntityId, CountMenacing(dummy), own, watch.Now.Band, watch.Now.Value, Roster.Cap(watch.Now.Band, watch.Now.Level));
        }
    }

    private TextCommandResult OnDummiesCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        DirectsDummies = args.Parsers[0].IsMissing ? !DirectsDummies : (bool)args[0];
        dummies.RemoveAll(d => !d.Alive);
        var text = new StringBuilder();
        text.Append(DirectsDummies ? "The director directs the dummies" : "The director leaves the dummies alone");
        foreach (Entity dummy in dummies)
        {
            Assessment a = AssessmentOf(dummy);
            text.AppendFormat("\n#{0} at {1:0} {2:0} {3:0}: Level {4}, band {5}, menace {6:0.00}, {7:0}% through it, {8} blocks to the next, {9} menacing about it",
                dummy.EntityId, dummy.Pos.X, dummy.Pos.Y, dummy.Pos.Z, a.Level, a.Band, a.Value, a.Depth * 100, a.ToNextLevel == int.MaxValue ? "no" : a.ToNextLevel.ToString(), CountMenacing(dummy));
        }
        return TextCommandResult.Success(text.ToString());
    }

    private TextCommandResult OnFacelingTestCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        Entity greeter = args.Caller.Entity;
        Vec3d at;
        if (greeter != null) at = greeter.Pos.XYZ;
        else
        {
            if (args.Parsers[0].IsMissing || args.Parsers[1].IsMissing) return TextCommandResult.Error("From the console, give x and z");
            int x = (int)args[0], z = (int)args[1];
            at = new Vec3d(x + 0.5, geometry.FloorFor(layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z))) + 1, z + 0.5);
            greeter = sapi.World.GetNearestEntity(at, 16, 64, e => e.Alive && e.WatchedAttributes.GetBool("backrooms:testTarget"));
        }
        Entity faceling = sapi.World.GetNearestEntity(at, 48, 32, e => e.Alive && e.Code.Domain == "backrooms" && e.Code.Path.StartsWith("faceling", StringComparison.Ordinal));
        if (faceling == null) return TextCommandResult.Error("No Faceling within 48 blocks (put one down with /backrooms encounter faceling ambient)");
        return TextCommandResult.Success(EntityBehaviorFaceling.TestGreeting(faceling, greeter));
    }

    /// <summary>
    /// <paramref name="rolls"/>: whether this one makes the place's spawn roll (see <see cref="DirectByPlace"/>); the
    /// wanderers, the Flickering and the Screaming are rolled for everyone.
    /// </summary>
    private void Direct(Entity target, Watch watch, bool creative, bool rolls = true, List<(Entity Entity, Watch Watch)> mates = null)
    {
        creative &= !CreativeHunted; // (/backrooms creativehunts: a creative player is directed like anyone else)
        Assessment a = watch.Now;
        if (a.Trial) return; // the King's trial is his own affair
        RosterEntry[] roster = a.Snackrooms ? Roster.Snackrooms : a.Castle ? Roster.Castle : Roster.For(a.Level);

        // Wanderers that mean no harm come and go on their own
        if (Setting.Entities) SpawnAmbient(target, a, roster);
        if (a.Band == MenaceBand.Safe) return;

        // A party (the people within PartyRadius of each other in a level) is rolled for once, for the member in most danger, at
        // PartyFactor times the rate (see MenaceSystem.Party.cs); who the arrival is for is drawn from the party. Alone, nothing changes.
        int party = rolls && mates != null ? Math.Max(1, mates.Count) : 1;
        double factor = PartyFactor(party);
        Entity actor = target;
        Watch actorWatch = watch;
        if (party > 1) (actor, actorWatch) = mates[rand.Next(party)];
        Assessment aa = actorWatch.Now;
        RosterEntry[] actorRoster = aa.Snackrooms ? Roster.Snackrooms : aa.Castle ? Roster.Castle : Roster.For(aa.Level);

        // Level 1's Flickering: out towards the edge, now and then the lights of a section fail, and the Hounds come
        double hours = sapi.World.Calendar.TotalHours;
        if (rolls && aa.Level == 1 && aa.Band >= MenaceBand.Approach && Setting.Entities && !creative && !aa.Flickering && hours >= actorWatch.NextFlickerHours
            && rand.NextDouble() < (0.004 + 0.01 * aa.Value) * factor && types.ContainsKey(Roster.Hound) && BodyAllowed(actor, actorWatch, aa))
        {
            // (A set piece, but not on top of another encounter: it waits for the hard gap and the one-kind rule; once started the Hounds always come, capped as a pack is)
            StartFlicker(actor, actorWatch, actorRoster);
            return;
        }

        // The Screaming: somewhere near, the rats are after something, and the lights fail while they are
        if (rolls && aa.Level == 2 && aa.Band >= MenaceBand.Approach && Setting.Entities && !creative && !aa.Flickering && hours >= actorWatch.NextScreamHours
            && rand.NextDouble() < (0.0015 + 0.004 * aa.Value) * factor && BodyAllowed(actor, actorWatch, aa))
        {
            StartScreaming(actor, actorWatch);
            return;
        }

        if (!rolls) return;
        // Bodies and sounds are rolled apart, as rates with hard gaps (EncounterRoll); no fallback sounds: a failed spawn is silence
        long nowMs = sapi.World.ElapsedMilliseconds;
        // (Thirst and fatigue scale the odds for this player: Needs.DirectorMult, 1 when rested and watered)
        RollKind roll = EncounterRoll.Roll(a.Band, a.Level, a.Value, Setting.Spawns * Backrooms.Needs.Needs.DirectorMult(target) * factor, nowMs - watch.LastBodyMs, nowMs - watch.LastSoundMs, a.Den != DenKind.None, CountMenacingKinds(target), a.Worst, rand);
        if (roll == RollKind.Nothing) return;
        if (roll == RollKind.Sound)
        {
            watch.LastSoundMs = nowMs;
            PlayDistantSound(actor, aa.Level);
            return;
        }
        Encounter kind = EncounterRoll.ToEncounter(roll);
        // Creative players only ever glimpse things; with the entities off there are no bodies
        if (!Setting.Entities || creative && kind != Encounter.Glimpse) return;
        Encounters flag = kind switch { Encounter.Glimpse => Encounters.Glimpse, Encounter.Stalk => Encounters.Stalk, _ => Encounters.Hunt };
        RosterEntry[] options = actorRoster.Where(e => (e.Kinds & flag) != 0 && e.MinBand <= aa.Band && (!e.SubwayOnly || aa.Subway) && (!e.ShiftOnly || aa.Shift)
            && (!e.LightsOutOnly || aa.Worst || aa.Shift) && types.ContainsKey(e.Code)).ToArray();
        // Someone starving, parched or dead on their feet draws the Wretches, three times over: they know what is coming for them
        if (Wretched(actor)) options = options.Select(e => e.Code == Roster.Wretch ? e with { Weight = e.Weight * 3 } : e).ToArray();
        // In a den, mostly what lives there comes
        if (Roster.DenEntry(aa.Den) is { } dweller && (dweller.Kinds & flag) != 0 && types.ContainsKey(dweller.Code) && rand.NextDouble() < DwellerChance && DwellerFits(actorRoster, dweller, aa)) options = new[] { dweller };
        RosterEntry entry = Pick(options);
        if (entry != null && TrySpawn(actor, aa, entry, kind)) watch.LastBodyMs = nowMs;
    }

    /// <summary>Whether a den's dweller may come here: a Smiler the level's roster keeps to the lights-out places (Level 0) still is.</summary>
    private static bool DwellerFits(RosterEntry[] roster, RosterEntry dweller, Assessment a) =>
        a.Worst || a.Shift || !roster.Any(e => e.Code == dweller.Code && e.LightsOutOnly);

    /// <summary>How likely a body put down in a den is what lives there.</summary>
    private const double DwellerChance = 0.75;

    /// <summary>Whether a set-piece body (the Flickering, the Screaming) may come: the hard gap since the last body has passed and the level's one-kind rule (<see cref="Roster.MaxKinds"/>) allows another kind.</summary>
    private bool BodyAllowed(Entity target, Watch watch, Assessment a) =>
        EncounterRoll.BodyMayCome(CountMenacingKinds(target), Roster.MaxKinds(a.Level), sapi.World.ElapsedMilliseconds - watch.LastBodyMs, EncounterRoll.BodyGapMs(a.Band, a.Level, a.Value, Setting.Spawns * Backrooms.Needs.Needs.DirectorMult(target), a.Den != DenKind.None));

    /// <summary>The Wretch's prey (Entity 15, "starved, parched, sleepless"): starving, parched, or dead on their feet (and not held up by caffeine).</summary>
    private static bool Wretched(Entity target) =>
        Starving(target) || Backrooms.Needs.Needs.Parched(target) || Backrooms.Needs.Needs.DeadOnFeet(target) && !Backrooms.Needs.Needs.Caffeinated(target);

    /// <summary>Whether someone is down to the last quarter of their satiety.</summary>
    private static bool Starving(Entity target)
    {
        var hunger = target.WatchedAttributes.GetTreeAttribute("hunger");
        if (hunger == null) return false;
        float max = hunger.GetFloat("maxsaturation", 1500);
        return max > 0 && hunger.GetFloat("currentsaturation", max) < 0.25f * max;
    }

    /// <summary>Puts a player's section of Level 1 into a Flickering; after a dark, dreadful wait a pack of Hounds comes to hunt them until it ends.</summary>
    private void StartFlicker(Entity target, Watch watch, RosterEntry[] roster)
    {
        double hours = sapi.World.Calendar.TotalHours;
        watch.FlickerUntilHours = hours + FlickerHours;
        watch.NextFlickerHours = hours + FlickerCooldownHours;
        watch.LastBodyMs = sapi.World.ElapsedMilliseconds;
        target.WatchedAttributes.SetDouble(FlickerKey, watch.FlickerUntilHours);
        watch.Now.Flickering = watch.Now.Dark = true;
        if (Logging) sapi.Logger.Notification("[backrooms] a Flickering for {0}", (target as EntityPlayer)?.Player?.PlayerName ?? target.Code.ToString());
        RosterEntry hounds = roster.FirstOrDefault(e => e.Code == Roster.Hound);
        if (hounds == null) return;
        BringDarkHunters(target, watch, hounds, FlickerDelayMinMs, FlickerDelayMaxMs, Roster.HoundCues);
    }

    /// <summary>How long (ms) the lights are out before the Hounds are put down, at least and at most.</summary>
    private const int FlickerDelayMinMs = 5000, FlickerDelayMaxMs = 10000;

    /// <summary>When (ms after the lights fail) the first far-off cue is heard, at least and at most: the player hears the Hounds within a few seconds.</summary>
    private const int FirstCueMinMs = 2000, FirstCueMaxMs = 4000;

    /// <summary>How long (ms) between looks for an unseen place for the dark's hunters (they are looked for until the lights return).</summary>
    private const int FlickerRetryMs = 3000;

    /// <summary>The dark's hunters are put down at least this far off (and up to this much further), so they have to come; later tries widen the band and drop the recent-view rule.</summary>
    private const double FlickerMinDistance = 22, FlickerSpread = 16;

    /// <summary>The failed tries after which the recent-view rule is dropped for the dark's hunters.</summary>
    private const int RecentViewDroppedAfter = 2;

    /// <summary>
    /// The dark of a Flickering or Screaming: at once only far-off cries of the hunters (three, the first within a few
    /// seconds), then after a dreadful wait they are put down unseen and hunt until the lights return. Placement is tried
    /// again every few seconds for the whole dark, with a wider band and without the recent-view rule after two failures.
    /// </summary>
    private void BringDarkHunters(Entity target, Watch watch, RosterEntry hunters, int minMs, int maxMs, DistantSound[] cues)
    {
        int delay = minMs + rand.Next(maxMs - minMs + 1);
        int first = Math.Min(FirstCueMinMs + rand.Next(FirstCueMaxMs - FirstCueMinMs + 1), delay - 1000);
        if (Logging) sapi.Logger.Notification("[backrooms] flicker: the Hounds come in {0:0.0} s (first cry in {1:0.0} s)", delay / 1000.0, first / 1000.0);
        foreach (double share in new[] { 0, 0.5, 0.85 })
            sapi.World.RegisterCallback(_ => { if (target.Alive && sapi.World.Calendar.TotalHours < watch.FlickerUntilHours) PlayDistantSound(target, 1, force: true, minDistance: 26, maxDistance: 44, only: cues); }, (int)(first + (delay - first) * share));
        sapi.World.RegisterCallback(_ => SendDarkHunters(target, watch, hunters, 0), delay);
    }

    private void SendDarkHunters(Entity target, Watch watch, RosterEntry hunters, int failed)
    {
        if (!target.Alive || sapi.World.Calendar.TotalHours >= watch.FlickerUntilHours) return;
        // (Not gated on what else is about: the pack is clipped to the cap, to one at least)
        if (TrySpawn(target, watch.Now, hunters, Encounter.Hunt, watch.FlickerUntilHours, setPiece: true, minDistance: FlickerMinDistance, failedTries: failed))
        {
            watch.LastBodyMs = sapi.World.ElapsedMilliseconds;
            return;
        }
        if (Logging) sapi.Logger.Notification("[backrooms] flicker: no place for the Hounds yet (try {0}), again in {1} s", failed + 1, FlickerRetryMs / 1000);
        sapi.World.RegisterCallback(_ => SendDarkHunters(target, watch, hunters, failed + 1), FlickerRetryMs);
    }

    // ================= Where people have been looking =================

    /// <summary>How often (ms) everyone's view direction is noted, how long (ms) it is kept, and the half-angle (degrees) and range (blocks) round a recent view that nothing is put down in (<c>minDistance</c> placements).</summary>
    private const int ViewSampleMs = 400;
    private const long RecentViewMs = 10_000;
    private const double RecentViewHalfAngle = 60, RecentViewRange = 40;

    private void SampleViews()
    {
        long now = sapi.World.ElapsedMilliseconds;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
            if (online.Entity is { Alive: true } e) NoteView(e, now);
        foreach (Entity dummy in dummies) if (dummy.Alive) NoteView(dummy, now);
    }

    private void NoteView(Entity who, long now)
    {
        if (!watches.TryGetValue(who.EntityId, out Watch watch)) watches[who.EntityId] = watch = new Watch();
        Vec3f view = who.Pos.GetViewVector();
        watch.Views.Add((now, view.X, view.Z));
        watch.Views.RemoveAll(v => now - v.Ms > RecentViewMs);
    }

    /// <summary>Whether someone looked towards a spot (within <see cref="RecentViewHalfAngle"/> degrees, <see cref="RecentViewRange"/> blocks) in the last few seconds: in the dark, it would be the same pop-in.</summary>
    private bool InRecentView(Entity target, Vec3d spot)
    {
        long now = sapi.World.ElapsedMilliseconds;
        double cosLimit = Math.Cos(RecentViewHalfAngle * Math.PI / 180);
        bool Looked(Entity who)
        {
            if (!watches.TryGetValue(who.EntityId, out Watch watch)) return false;
            double dx = spot.X - who.Pos.X, dz = spot.Z - who.Pos.Z, flat = Math.Sqrt(dx * dx + dz * dz);
            if (flat > RecentViewRange) return false;
            if (flat < 0.5) return true;
            foreach ((long ms, double vx, double vz) in watch.Views)
            {
                double len = Math.Sqrt(vx * vx + vz * vz);
                if (now - ms <= RecentViewMs && len > 0.01 && (dx * vx + dz * vz) / (flat * len) >= cosLimit) return true;
            }
            return false;
        }
        if (Looked(target)) return true;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
            if (online.Entity is { Alive: true } other && other != target && other.Pos.Dimension == target.Pos.Dimension && Looked(other)) return true;
        return false;
    }

    /// <summary>
    /// The Screaming (the lore's rare events of Death Rats in full cry after something, the lights flickering until it
    /// ends): the lights fail round the player for a few minutes; the screaming is heard close by, twice; and a pack of
    /// rats goes across the way ahead at a run, after whatever it is.
    /// </summary>
    private void StartScreaming(Entity target, Watch watch)
    {
        double hours = sapi.World.Calendar.TotalHours;
        watch.NextScreamHours = hours + ScreamCooldownHours;
        watch.LastBodyMs = sapi.World.ElapsedMilliseconds;
        watch.FlickerUntilHours = Math.Max(watch.FlickerUntilHours, hours + ScreamHours);
        target.WatchedAttributes.SetDouble(FlickerKey, watch.FlickerUntilHours);
        watch.Now.Flickering = watch.Now.Dark = true;
        if (Logging) sapi.Logger.Notification("[backrooms] the Screaming for {0}", (target as EntityPlayer)?.Player?.PlayerName ?? target.Code.ToString());
        double angle = rand.NextDouble() * Math.PI * 2;
        for (int i = 0; i < 2; i++)
        {
            double a = angle + (rand.NextDouble() - 0.5) * 0.8, d = 16 + rand.NextDouble() * 10;
            double x = target.Pos.X + Math.Cos(a) * d, z = target.Pos.Z + Math.Sin(a) * d;
            sapi.World.RegisterCallback(_ => sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/ratscream"), x, target.Pos.Y + 1, z, null, 0.9f + (float)rand.NextDouble() * 0.2f, 56, 1f), 400 + i * 4500);
        }
        if (!types.ContainsKey(Roster.DeathRat)) return;
        var pack = new RosterEntry(Roster.DeathRat, MenaceBand.Heartland, Encounters.Glimpse, 1, 4, 6) { Frenzy = true };
        sapi.World.RegisterCallback(_ =>
        {
            if (target.Alive) TrySpawn(target, watch.Now, pack, Encounter.Glimpse, setPiece: true);
        }, 2500);
        // What the rats are after is you, or what comes for you: the Hounds in Level 1, the rats themselves in Level 2
        RosterEntry hunters = watch.Now.Level == 1 ? Roster.For(1).FirstOrDefault(e => e.Code == Roster.Hound) : new RosterEntry(Roster.DeathRat, MenaceBand.Heartland, Encounters.Hunt, 1, 2, 3);
        if (hunters != null && types.ContainsKey(hunters.Code))
            BringDarkHunters(target, watch, hunters, 6000, 10000, watch.Now.Level == 1 ? Roster.HoundCues : Roster.RatCues);
    }

    private RosterEntry Pick(RosterEntry[] options)
    {
        if (options.Length == 0) return null;
        double total = options.Sum(e => e.Weight), r = rand.NextDouble() * total;
        foreach (RosterEntry e in options)
        {
            r -= e.Weight;
            if (r <= 0) return e;
        }
        return options[^1];
    }

    /// <summary>
    /// How many menacing (not Ambient) entities are about a player already, whoever they were put down for: the cap
    /// is on the place (and a pack is clipped to the current band's cap), so two people together are not hunted by twice as much, and what turns on a second player
    /// (see <see cref="AiTaskMenace.OnEntityHurt"/>) still counts for the first.
    /// </summary>
    private int CountMenacing(Entity target) =>
        sapi.World.GetEntitiesAround(target.Pos.XYZ, 64, 24, e => e.Alive && EntityBehaviorMenace.KindOf(e) is Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Leave or Encounter.Investigate or Encounter.Search).Length;

    /// <summary>The menacing entities (as <see cref="CountMenacing"/>) within 64 blocks counted by kind (entity code): the one-kind rule counts these, the caps count bodies.</summary>
    private int CountMenacingKinds(Entity target) =>
        sapi.World.GetEntitiesAround(target.Pos.XYZ, 64, 24, e => e.Alive && EntityBehaviorMenace.KindOf(e) is Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Leave or Encounter.Investigate or Encounter.Search)
            .Select(e => e.Code.ToString()).Distinct().Count();

    /// <summary>How much longer than the level's sound gap one person's next distant sound may be put off (a fraction of the gap, at random).</summary>
    private const double SoundGapJitter = 0.5;

    /// <summary>Plays one of the level's distant sounds from somewhere off down a corridor.</summary>
    public void PlayDistantSound(Entity target, int level, bool force = false, double minDistance = 14, double maxDistance = 36, DistantSound[] only = null)
    {
        DistantSound[] sounds = only ?? Roster.SoundsFor(level);
        if (sounds.Length == 0) return;
        // (A minimum gap between one person's distant sounds, longer in Level 0, where they were too frequent)
        long now = sapi.World.ElapsedMilliseconds;
        double gap = Roster.SoundGapSeconds(level);
        if (!force && gap > 0 && watches.TryGetValue(target.EntityId, out Watch heard))
        {
            if (now < heard.NextSoundMs) return;
            heard.NextSoundMs = now + (long)(gap * 1000 * (1 + SoundGapJitter * rand.NextDouble()));
        }
        DistantSound sound = sounds[rand.Next(sounds.Length)];
        double angle = rand.NextDouble() * Math.PI * 2, distance = minDistance + rand.NextDouble() * (maxDistance - minDistance);
        double x = target.Pos.X + Math.Cos(angle) * distance, z = target.Pos.Z + Math.Sin(angle) * distance;
        float pitch = sound.PitchMin + (float)rand.NextDouble() * (sound.PitchMax - sound.PitchMin);
        IPlayer player = (target as EntityPlayer)?.Player;
        sapi.World.PlaySoundAt(new AssetLocation(sound.Location), x, target.Pos.Y + 1, z, null, pitch, 48, sound.Volume);
        if (Logging) sapi.Logger.Notification("[backrooms] sound {0} for {1} at {2:0} blocks", sound.Location, player?.PlayerName ?? target.Code.ToString(), distance);
    }

    // ================= Putting entities down =================

    /// <summary>Puts down an entity (and the rest of its pack) for an encounter with a target. Returns whether it did.</summary>
    /// <param name="setPiece">The Flickering's hounds, the Screaming's rats, a test: the pack is clipped to the Threshold cap rather than the current band's.</param>
    public bool TrySpawn(Entity target, Assessment a, RosterEntry entry, Encounter kind, double untilHours = -1, bool setPiece = false, double minDistance = 0, int failedTries = 0, bool dryRun = false, double maxDistance = 0)
    {
        LastTry = default;
        if (!types.TryGetValue(entry.Code, out EntityProperties type)) return false;
        // A capped scavenger pack is silence, like any failed spawn: say so before the search for a spot, not after it
        if (Scavengers(entry, a, kind, setPiece) && RatPacksNear(target) >= MaxRatPacks) { LastTry.RatCap = 1; if (!dryRun && minDistance <= 0 && !setPiece && kind != Encounter.Ambient) NoteFailedBody(a.Level, entry.Code, LastTry, 0, 0); return false; }
        (double min, double max) = kind switch
        {
            Encounter.Glimpse => (22.0, 40.0),
            Encounter.Stalk => (18.0, 30.0),
            Encounter.Hunt => (14.0, 24.0),
            _ => (18.0, 40.0),
        };
        (double ox, double oz) = layout.Outward((int)target.Pos.X, (int)target.Pos.Z);
        Vec3f view = target.Pos.GetViewVector();
        // At the edge of a level, the danger comes from the way the player is going: between them and the gate they are
        // making for, or else simply from further out
        double? ahead = a.Band == MenaceBand.Threshold && a.Level < 10 ? Math.Atan2(oz, ox) : null;
        if (a.Band == MenaceBand.Threshold && kind is Encounter.Hunt or Encounter.Stalk && !entry.Ambush && !entry.Aquatic
            && GateAhead(target, a.Level, view) is double toGate)
        {
            ahead = toGate;
            if (kind == Encounter.Hunt) (min, max) = (10.0, 16.0);
        }
        // Things that lie in wait are put ahead of the player, the way they are looking
        if (entry.Ambush) (min, max) = (8.0, 16.0);
        // A set piece's pack is put well away, and not where anyone has just been looking
        // (Each failed try before this one brings the band nearer at its inner edge and out at its far edge)
        if (minDistance > 0) (min, max) = (Math.Max(14, minDistance - 3 * Math.Min(failedTries, 3)), minDistance + FlickerSpread + 6 * Math.Min(failedTries, 4));
        // (A band given outright, a night visit's 12 to 18 blocks: taken as it is)
        if (minDistance > 0 && maxDistance > minDistance) (min, max) = (minDistance, maxDistance);
        int refusedSeen = 0, refusedView = 0, refusedSpot = 0;

        bool widened = false;
        for (int attempt = 0; attempt < 2 * Looks; attempt++)
        {
            // Under the open sky a stalker or hunter often has no unseen spot within the usual band (every spot is in a clear line):
            // after the usual looks all failed, look again 30 to 48 blocks out, where a hill crest or a house may stand between
            if (attempt == Looks)
            {
                if (kind is not (Encounter.Stalk or Encounter.Hunt) || entry.Ambush || entry.Aquatic || minDistance > 0 || setPiece || !UnderOpenSky(target.Pos.X, target.Pos.Y, target.Pos.Z)) break;
                (min, max) = (OpenMinDistance, OpenMaxDistance);
                widened = true;
            }
            double angle = rand.NextDouble() * Math.PI * 2;
            if (ahead is double heading && attempt % 3 != 2) angle = heading + (rand.NextDouble() - 0.5) * 1.6;
            if (entry.Ambush) angle = Math.Atan2(view.Z, view.X) + (rand.NextDouble() - 0.5) * 1.2;
            double distance = min + rand.NextDouble() * (max - min);
            int x = (int)Math.Floor(target.Pos.X + Math.Cos(angle) * distance), z = (int)Math.Floor(target.Pos.Z + Math.Sin(angle) * distance);
            Vec3d spot = entry.Aquatic ? FindWaterSpot(target, a, x, z) : FindSpot(target, a, entry, kind, x, z);
            if (spot == null || widened && !UnderOpenSky(spot.X, spot.Y, spot.Z)) { refusedSpot++; continue; }

            // A glimpse is meant to be seen; stalkers, hunters, what lies in wait and wanderers arrive unseen.
            // Nothing is put down where someone could see any part of it: no spawn is better than a visible one. (What moves
            // in the deep can be put down anywhere.)
            bool wanted = true;
            if (!entry.Aquatic)
            {
                bool seen = SeenBySomeone(target, spot, type);
                wanted = kind == Encounter.Glimpse && !entry.Ambush ? seen : !seen;
            }
            if (!wanted) { refusedSeen++; continue; }
            if (minDistance > 0 && failedTries < RecentViewDroppedAfter && InRecentView(target, spot))
            {
                refusedView++;
                continue;
            }
            LastTry = new SpawnTry { NoFloor = refusedSpot, InSight = refusedSeen, JustSeen = refusedView };
            if (!dryRun) SpawnPack(target, entry, kind, type, spot, a, untilHours, setPiece);
            return true;
        }
        LastTry = new SpawnTry { NoFloor = refusedSpot, InSight = refusedSeen, JustSeen = refusedView };
        if (!dryRun && minDistance <= 0 && !setPiece && kind != Encounter.Ambient) NoteFailedBody(a.Level, entry.Code, LastTry, min, max);
        if (Logging && minDistance > 0) sapi.Logger.Notification("[backrooms] {0}: no spot after 18 looks ({1} no floor/room, {2} in sight, {3} where they were just looking{4}); band {5:0}-{6:0} blocks", entry.Code, refusedSpot, refusedSeen, refusedView, failedTries >= RecentViewDroppedAfter ? "; recent view ignored" : "", min, max);
        return false;
    }

    /// <summary>The looks for a spot a try makes (and as many more at <see cref="OpenMinDistance"/> to <see cref="OpenMaxDistance"/> blocks under the open sky).</summary>
    private const int Looks = 18;
    private const double OpenMinDistance = 30, OpenMaxDistance = 48;

    /// <summary>Whether nothing roofs the column above a standing place (no block that stops rain over the head).</summary>
    private bool UnderOpenSky(double x, double y, double z) =>
        sapi.World.BlockAccessor.GetRainMapHeightAt((int)Math.Floor(x), (int)Math.Floor(z)) <= (int)Math.Floor(y) + 1;

    /// <summary>The heights (fractions of the hitbox) and sides rays are cast to when asking whether something could be seen.</summary>
    private static readonly (double Up, double Side)[] SightPoints = { (0.05, 0), (0.5, 0), (0.5, -0.5), (0.5, 0.5), (0.95, 0), (0.95, -0.5), (0.95, 0.5) };

    /// <summary>How far (blocks) someone can see something put down.</summary>
    private const double SightRange = 64;

    /// <summary>
    /// The client's view cone (degrees wide, with margin) and how far it counts. Only the sight test's log line uses
    /// them, to say whether a refused spot was in view; the decision ignores the cone (any clear ray counts as seen).
    /// </summary>
    private const double ViewConeDegrees = 110, ViewConeRange = 48;

    /// <summary>
    /// Whether the player (or dummy) <paramref name="target"/>, or any other player about, could see any part of an entity
    /// of this type standing at <paramref name="spot"/>: a ray from their eyes to its feet, middle or head (and the sides of
    /// its body) is not stopped by a solid block (glass does not stop it). A spot in someone's view cone within
    /// <see cref="ViewConeRange"/> blocks counts as seen unless every ray is blocked; outside the cone it counts as seen all
    /// the same when a ray is clear, since they only have to turn round.
    /// </summary>
    private bool SeenBySomeone(Entity target, Vec3d spot, EntityProperties type)
    {
        return SeenBySomeone(target, spot, type.CollisionBoxSize?.Y ?? 1.85f, type.CollisionBoxSize?.X ?? 0.6f);
    }

    /// <summary>The same for a thing of a known size (the wanderers, put down by their own system).</summary>
    internal bool SeenBySomeone(Entity target, Vec3d spot, float height, float width)
    {
        if (SeenBy(target, spot, height, width)) return true;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            EntityPlayer other = online.Entity;
            if (other == null || other == target || !other.Alive || other.Pos.Dimension != target.Pos.Dimension) continue;
            if (online.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
            if (other.Pos.DistanceTo(spot) > SightRange) continue;
            if (SeenBy(other, spot, height, width)) return true;
        }
        return false;
    }

    private bool SeenBy(Entity viewer, Vec3d spot, float height, float width)
    {
        Vec3d eyes = Senses.Eyes(viewer);
        double dx = spot.X - eyes.X, dz = spot.Z - eyes.Z, flat = Math.Sqrt(dx * dx + dz * dz);
        if (eyes.DistanceTo(spot) > SightRange) return false;
        // (The sideways rays run across the line of sight)
        double sx = flat > 0.01 ? -dz / flat : 1, sz = flat > 0.01 ? dx / flat : 0;
        bool clear = false;
        foreach ((double up, double side) in SightPoints)
        {
            var to = new Vec3d(spot.X + sx * side * width, spot.Y + up * height, spot.Z + sz * side * width);
            if (Senses.ClearLine(sapi.World, eyes, to, throughGlass: true)) { clear = true; break; }
        }
        if (Logging)
        {
            Vec3f view = viewer.Pos.GetViewVector();
            double cos = flat > 0.01 ? (dx * view.X + dz * view.Z) / flat : 1;
            bool inCone = flat <= ViewConeRange && cos >= Math.Cos(ViewConeDegrees / 2 * Math.PI / 180);
            sapi.Logger.Notification("[backrooms] sight test {0:0} blocks off, {1}: {2}", flat, inCone ? "in view cone" : "out of cone", clear ? "REFUSED (clear line)" : "hidden, ok");
        }
        return clear;
    }

    /// <summary>
    /// The bearing (radians, as from Math.Atan2(dz, dx)) to the nearest gate out of the player's level within a few
    /// hundred blocks, if they are close to it or facing roughly its way; otherwise null.
    /// </summary>
    private double? GateAhead(Entity target, int level, Vec3f view)
    {
        int x = (int)Math.Floor(target.Pos.X), z = (int)Math.Floor(target.Pos.Z);
        if (layout.NearestGate(x, z, level, 192) is not { } gate) return null;
        double dx = gate.X + 0.5 - target.Pos.X, dz = gate.Z + 0.5 - target.Pos.Z, length = Math.Sqrt(dx * dx + dz * dz);
        if (length < 8) return null; // already there
        bool facing = (dx * view.X + dz * view.Z) / length > 0.3;
        return length < 48 || facing ? Math.Atan2(dz, dx) : null;
    }

    /// <summary>Whether a body of this kind becomes a pack of scavenging rats: a Death Rat in the heart of a level, apart from the Screaming's frenzy and set pieces.</summary>
    private static bool Scavengers(RosterEntry entry, Assessment a, Encounter kind, bool setPiece) =>
        entry.Code == Roster.DeathRat && a.Band == MenaceBand.Heartland && !entry.Frenzy && kind != Encounter.Ambient && !setPiece;

    /// <summary>Whether the spawns being made now are a set piece (for the play telemetry).</summary>
    private bool telemetrySetPiece;

    private void SpawnPack(Entity target, RosterEntry entry, Encounter kind, EntityProperties type, Vec3d spot, Assessment a, double untilHours, bool setPiece)
    {
        telemetrySetPiece = setPiece;
        int packMax = entry.PackMax + (entry.PackMax > 1 && Danger.OfLevel(a.Level) >= 0.5 ? 1 : 0);
        // In the heart of a level, rats are scavengers (README 6.1): a pack that goes about its own business, to food on the
        // floor, and runs from you (AiTaskScavenge). At the edge and in dens they are put down hunting, as before. Not
        // too many of them about one person at a time.
        bool unseen = kind != Encounter.Glimpse && !entry.Aquatic; // (every member of a pack is put down out of sight too)
        bool scavengers = Scavengers(entry, a, kind, setPiece);
        if (scavengers) kind = Encounter.Ambient; // (TrySpawn has already refused when too many packs are about)
        // The Skin-Stealer's day: now and then one put down is fed already, so docile (the heartland, where they only wander, and a fifth further out)
        double fedChance = entry.Code == Roster.SkinStealer && kind != Encounter.Ambient ? (a.Band == MenaceBand.Heartland ? SkinStealerFedHeartland : SkinStealerFedOut) : 0;
        // A glimpse is one thing seen and gone, except the Screaming's frenzied pack, which crosses ahead all together
        bool single = !scavengers && (kind == Encounter.Ambient || (kind == Encounter.Glimpse && !entry.Frenzy));
        int count = single ? 1 : entry.PackMin + rand.Next(packMax - entry.PackMin + 1);
        if (kind != Encounter.Ambient && !packUncapped) count = Math.Max(1, Math.Min(count, Roster.Cap(setPiece ? MenaceBand.Threshold : a.Band, a.Level) - CountMenacing(target)));
        lastPack.Clear();
        if (Spawn(type, spot, target, kind, a.Passive, untilHours, entry.ShiftOnly, entry.Frenzy, fedChance: fedChance) is { } first) lastPack.Add(first);
        for (int i = 1; i < count; i++)
        {
            for (int attempt = 0; attempt < 6; attempt++)
            {
                int x = (int)Math.Floor(spot.X) + rand.Next(-3, 4), z = (int)Math.Floor(spot.Z) + rand.Next(-3, 4);
                Vec3d near = entry.Aquatic ? FindWaterSpot(target, a, x, z) : FindSpot(target, a, entry, kind, x, z, (int)Math.Floor(spot.Y));
                if (near == null || unseen && SeenBySomeone(target, near, type)) continue;
                if (Spawn(type, near, target, kind, a.Passive, untilHours, entry.ShiftOnly, entry.Frenzy, fedChance: fedChance) is { } another) lastPack.Add(another);
                break;
            }
        }
        if (Logging)
            foreach (Entity member in lastPack)
            {
                // (Checked on the entity as it stands, as a second opinion on SeenBySomeone: any ray from the eyes to feet, middle, head)
                Vec3d eyesNow = Senses.Eyes(target);
                float h = member.Properties.CollisionBoxSize?.Y ?? 1.85f;
                bool anyClear = new[] { 0.05, 0.5, 0.95 }.Any(f => Senses.ClearLine(sapi.World, eyesNow, member.Pos.XYZ.Add(0, f * h, 0), throughGlass: true));
                sapi.Logger.Notification("[backrooms] placed {0} ({1}) {2:0} blocks off: {3}", member.Code.Path, kind, member.Pos.DistanceTo(target.Pos.XYZ), anyClear ? "CLEAR LINE to the eyes" : "no line to the eyes");
            }
        telemetrySetPiece = false;
        if (Logging) sapi.Logger.Notification("[backrooms] {0} x{1} ({2}) for {3}, {4:0} blocks off, band {5}", entry.Code, count, kind, (target as EntityPlayer)?.Player?.PlayerName ?? target.Code.ToString(), spot.DistanceTo(target.Pos.XYZ), a.Band);
    }

    /// <summary>
    /// Puts down one entity of a kind at a spot, hunting a target, outside the director's own rules: what the King
    /// raises for his trial. Null if there is no such entity. With <paramref name="ownNumbers"/> it keeps the speed,
    /// damage and health its type gives it instead of taking the level's danger (the Mangled, whose walk and stride
    /// were matched by hand).
    /// </summary>
    public Entity SpawnHunter(string code, Vec3d at, Entity target, bool ownNumbers = false)
    {
        if (!types.TryGetValue(code, out EntityProperties type)) return null;
        return Spawn(type, at, target, Encounter.Hunt, passive: false, dangerOverride: ownNumbers ? 0 : null);
    }

    /// <summary>The chance a Skin-Stealer the director puts down is fed (docile): in the heartland, and further out. The calendar hours a meal lasts.</summary>
    private const double SkinStealerFedHeartland = 0.5, SkinStealerFedOut = 0.2, SkinStealerFedHours = 24;

    private Entity Spawn(EntityProperties type, Vec3d at, Entity target, Encounter kind, bool passive, double untilHours = -1, bool duringShift = false, bool frenzy = false, double? dangerOverride = null, double fedChance = 0)
    {
        Entity entity = sapi.World.ClassRegistry.CreateEntity(type);
        if (frenzy) entity.Attributes.SetBool(AiTaskMenace.FrenzyKey, true);
        // A fed Skin-Stealer is docile, whatever it was put down to do: it wanders (and wears the disguise look, see ChooseLook).
        // One put down as a wanderer (Ambient) is always fed
        if (type.Code.Path == "skinstealer" && (kind == Encounter.Ambient || rand.NextDouble() < fedChance))
        {
            kind = Encounter.Ambient;
            entity.Attributes.SetDouble(EntityBehaviorMenace.FedKey, sapi.World.Calendar.TotalHours + SkinStealerFedHours);
        }
        entity.Pos.SetPos(at.X, at.Y + 0.02, at.Z);
        entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - at.X, target.Pos.Z - at.Z);
        EntityBehaviorMenace.Prepare(entity, target, kind, passive, sapi.World.ElapsedMilliseconds, untilHours, duringShift);
        // (Headless tests: with no player about nothing would think)
        if (target.WatchedAttributes.GetBool("backrooms:testTarget")) entity.AlwaysActive = true;
        bool elder = ChooseLook(entity, at);
        double danger = dangerOverride ?? Danger.OfLevel(layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(at.X)), WorldLayout.MacroOf((int)Math.Floor(at.Z))));
        entity.Attributes.SetDouble(Danger.Key, danger);
        sapi.World.SpawnEntity(entity);
        if (PlayTelemetry.Telemetry.On) PlayTelemetry.Telemetry.Spawn(entity, target, EntityBehaviorMenace.KindOf(entity).ToString(), AssessmentOf(target).Band.ToString(), telemetrySetPiece);
        if (entity.GetBehavior<Vintagestory.GameContent.EntityBehaviorHealth>() is { } health)
        {
            // Deeper down, harder to put down; an old Hound half as hard again
            // (Evolved Facelings are weak: 12 against the ordinary 10)
            float extra = Danger.ExtraHealth(danger) + (elder ? 0.5f : 0f) + (entity.Attributes.GetBool(EvolvedKey) ? 0.2f : 0f);
            if (extra > 0)
            {
                health.SetMaxHealthModifiers("backrooms-danger", health.BaseMaxHealth * extra);
                health.Health = health.MaxHealth;
            }
        }
        return entity;
    }

    /// <summary>
    /// Picks which of its looks a new entity wears (its texture alternate), where that depends on more than chance: the
    /// Death Rats of Level 2's heat have lost their fur; a Hound may be one of the starved ones, or rarely an old one.
    /// Returns whether it is an old Hound.
    /// </summary>
    private bool ChooseLook(Entity entity, Vec3d at)
    {
        switch (entity.Code.Path)
        {
            case "deathrat":
                int level = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(at.X)), WorldLayout.MacroOf((int)Math.Floor(at.Z)));
                entity.WatchedAttributes.SetInt("textureIndex", level == 2 ? 1 : 0);
                return false;
            case "hound":
                double r = rand.NextDouble();
                int look = r < 0.12 ? 2 : r < 0.37 ? 1 : 0;
                entity.WatchedAttributes.SetInt("textureIndex", look);
                return look == 2;
            case "faceling":
                // Level 3's are all Evolved (hostile, half-formed faces); elsewhere any of the ordinary looks (the Evolved
                // one is only ever given by index, never left to the client's chance)
                int here = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(at.X)), WorldLayout.MacroOf((int)Math.Floor(at.Z)));
                bool evolved = here == 3;
                entity.WatchedAttributes.SetInt("textureIndex", evolved ? EntityBehaviorFaceling.EvolvedLook : rand.Next(EntityBehaviorFaceling.AdultLooks));
                if (evolved) entity.Attributes.SetBool(EvolvedKey, true);
                if (Logging) sapi.Logger.Notification("[backrooms] faceling look {0} (level {1}{2})", entity.WatchedAttributes.GetInt("textureIndex"), here, evolved ? ", Evolved" : "");
                return false;
            case "skinstealer":
                // Fed, it wears clothes over a fresher skin (index 1); hungry, the waxy one
                entity.WatchedAttributes.SetInt("textureIndex", entity.Attributes.GetDouble(EntityBehaviorMenace.FedKey, 0) > sapi.World.Calendar.TotalHours ? 1 : 0);
                return false;
            case "wretch":
                // The further down, the longer they have been down here: still dressed near the top, all but gone deep
                double d = Danger.OfLevel(layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(at.X)), WorldLayout.MacroOf((int)Math.Floor(at.Z))));
                double w = rand.NextDouble();
                entity.WatchedAttributes.SetInt("textureIndex", w < 0.5 * (1 - d) ? 1 : w > 0.9 - 0.4 * d ? 2 : 0);
                return false;
        }
        return false;
    }

    /// <summary>How far (blocks) from Level 10's wall the Neighborhood Watch is never put down.</summary>
    private const int WatchClearOfLevel10 = 200;

    /// <summary>
    /// A place an entity could stand at a column: in the target's level, not in a sanctuary or a sealed room, a solid
    /// floor with room above it near the target's height, and dark if the entity needs the dark.
    /// </summary>

    private Vec3d FindSpot(Entity target, Assessment a, RosterEntry entry, Encounter kind, int x, int z, int? nearY = null)
    {
        if (target.Pos.XYZ.HorizontalSquareDistanceTo(x + 0.5, z + 0.5) < NoSpawnRadius * NoSpawnRadius) return null;
        // (Nor on top of anyone else: a hunter put down 14 blocks from one player must not land beside another)
        if (sapi.World.GetNearestEntity(new Vec3d(x + 0.5, target.Pos.Y, z + 0.5), NoSpawnRadius, NoSpawnRadius, e => e != target && e is EntityPlayer p && p.Alive) != null) return null;
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, (int)target.Pos.Y, z) == null) return null;
        int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
        if (level != a.Level) return null;
        if (a.Snackrooms != (level == 6 && layout.IsSnackrooms(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)))) return null;
        // The Watch is not found "in areas that go to Level 10" (Wikidot): never within 200 blocks of the wall into it
        if (entry.Code == Roster.NeighborhoodWatch && layout.BlocksToNextLevel(x, z, level) < WatchClearOfLevel10) return null;
        bool ambient = kind == Encounter.Ambient;
        if (!ambient && layout.IsSanctuary(x, z, level)) return null;
        // The layout knows where the rooms, walls and sealed places are on every level but the sea and the caves
        if (level is not (7 or 8) && !layout.IsEntitySpot(x, z)) return null;

        // (Motion's ground rises and falls with its hills: look for the floor at the ground's own height)
        int startY = nearY ?? (level == WorldLayout.Motion && !layout.InCastle(x, z) ? geometry.FloorFor(level) + layout.TileAt(x, z).Height + 1 : (int)Math.Floor(target.Pos.Y));
        int y = Senses.FindFloor(sapi.World, x, startY, z, entry.Code == Roster.DeathmothMale || entry.Code == Roster.DeathmothFemale ? 3 : 2);
        if (y == int.MinValue) return null;
        var spot = new Vec3d(x + 0.5, y, z + 0.5);
        if (entry.SubwayOnly && y >= geometry.CityFloorY - 1) return null;
        if (entry.NeedsDark && Senses.LightAt(sapi.World, spot.AddCopy(0, 1, 0), target) >= Senses.LitLevel) return null;
        // (Under the open sky, with room for something three blocks tall)
        if (entry.Outdoors && (sapi.World.BlockAccessor.GetRainMapHeightAt(x, z) > y || Senses.FindFloor(sapi.World, x, y, z, 3, 0) != y)) return null;
        // (The Watcher: never two within 48 blocks, never within 200 of Level 10's wall)
        if (entry.Code == Roster.Watcher && !WatcherSpotOk(spot)) return null;
        if (!ambient && Wards.Warded(sapi.World, spot)) return null;
        return spot;
    }

    /// <summary>Whether a Watcher may be put down at a spot: no other within 48 blocks, no Level 10 within 200 (the lore's "never near Level 10").</summary>
    private bool WatcherSpotOk(Vec3d spot)
    {
        if (sapi.World.GetNearestEntity(spot, 48, 48, e => e.Alive && e.Code.Path == "watcher") != null) return false;
        int mx = WorldLayout.MacroOf((int)Math.Floor(spot.X)), mz = WorldLayout.MacroOf((int)Math.Floor(spot.Z));
        int reach = 200 / WorldLayout.MacroSize + 2;
        for (int dz = -reach; dz <= reach; dz++)
            for (int dx = -reach; dx <= reach; dx++)
            {
                if (layout.LevelAt(mx + dx, mz + dz) != 10) continue;
                // (The distance to the nearest point of that cell)
                double nx = Math.Clamp(spot.X, (mx + dx) * WorldLayout.MacroSize, (mx + dx + 1) * WorldLayout.MacroSize);
                double nz = Math.Clamp(spot.Z, (mz + dz) * WorldLayout.MacroSize, (mz + dz + 1) * WorldLayout.MacroSize);
                if ((nx - spot.X) * (nx - spot.X) + (nz - spot.Z) * (nz - spot.Z) < 200.0 * 200.0) return false;
            }
        return true;
    }

    /// <summary>Somewhere in open, deep water around a column, near the target's depth (for The Thing).</summary>
    private Vec3d FindWaterSpot(Entity target, Assessment a, int x, int z)
    {
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, (int)target.Pos.Y, z) == null) return null;
        if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != a.Level) return null;
        IBlockAccessor ba = sapi.World.BlockAccessor;
        var pos = new BlockPos(0);
        int y0 = (int)Math.Floor(target.Pos.Y) - rand.Next(0, 8);
        // Room for something vast: open water two blocks every way
        for (int dy = -1; dy <= 1; dy++)
            for (int dz = -2; dz <= 2; dz++)
                for (int dx = -2; dx <= 2; dx++)
                {
                    pos.Set(x + dx, y0 + dy, z + dz);
                    Block solid = ba.GetBlock(pos);
                    if (solid.CollisionBoxes != null && solid.CollisionBoxes.Length > 0) return null;
                    if (!ba.GetBlock(pos, BlockLayersAccess.Fluid).IsLiquid()) return null;
                }
        return new Vec3d(x + 0.5, y0, z + 0.5);
    }

    // ================= Commands =================

    private TextCommandResult OnMenaceCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        Entity entity = args.Caller.Entity;
        if (!watches.TryGetValue(entity.EntityId, out Watch watch)) watches[entity.EntityId] = watch = new Watch();
        Assess(entity, watch);
        Assessment a = watch.Now;
        var text = new StringBuilder();
        text.AppendFormat("Level {0}, {1:0}% through it, {2} blocks to the next. Band {3}, menace {4:0.00}{5}{6}{7}. Setting: {8}.",
            a.Level, a.Depth * 100, a.ToNextLevel == int.MaxValue ? "no" : a.ToNextLevel.ToString(), a.Band, a.Value,
            a.Dark ? ", in the dark" : "", a.Passive ? ", passive" : "", sapi.World.ElapsedMilliseconds < watch.CalmUntilMs ? ", calm" : "", Setting.Code);
        double dl = Danger.OfLevel(a.Level);
        text.AppendFormat("\nLevel danger {0:0.00}: entities x{1:0.00} speed, x{2:0.00} damage, x{3:0.00} health{4}.", dl, Danger.Speed(dl), Danger.Damage(dl), 1 + Danger.ExtraHealth(dl),
            Danger.TierBonus(dl) > 0 ? ", one armour tier harder" : "");
        text.AppendFormat("\nOut {0:0.0} h since resting (resting {1:0} s), noise {2:0.00}{3}.", a.OutHours, watch.RestingFor, a.Noise,
            a.Den != DenKind.None ? ", in a den: " + a.Den : "");
        if (layout.NearestGate((int)entity.Pos.X, (int)entity.Pos.Z, a.Level, 400) is { } gate)
            text.AppendFormat(" Nearest gate: {0}, {1} (to Level {2}).", gate.X, gate.Z, gate.To);
        foreach (Entity e in sapi.World.GetEntitiesAround(entity.Pos.XYZ, 64, 24, e => e.Alive && e.GetBehavior<EntityBehaviorMenace>() != null))
        {
            text.AppendFormat("\n{0}: {1}, {2:0} blocks", e.Code.Path, e.GetBehavior<EntityBehaviorMenace>().Kind, e.Pos.DistanceTo(entity.Pos.XYZ));
        }
        text.Append('\n').Append(FailedBodiesLine(a.Level));
        text.Append('\n').Append(CostLine());
        return TextCommandResult.Success(text.ToString());
    }

    private TextCommandResult OnEncounterCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string code = (string)args[0];
        if (!code.Contains(':')) code = "backrooms:" + code;
        if (!types.TryGetValue(code, out EntityProperties type)) return TextCommandResult.Error("No such entity: " + code);
        string kindWord = args.Parsers[1].IsMissing ? "hunt" : (string)args[1];
        if (!Enum.TryParse(kindWord, true, out Encounter kind)) return TextCommandResult.Error("No such encounter: " + kindWord);

        Entity target = args.Caller.Entity;
        if (target == null)
        {
            if (args.Parsers[2].IsMissing || args.Parsers[3].IsMissing) return TextCommandResult.Error("From the console, give x and z");
            int x = (int)args[2], z = (int)args[3];
            int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
            int floorY = geometry.FloorFor(level) + 1;
            target = sapi.World.GetNearestEntity(new Vec3d(x + 0.5, floorY, z + 0.5), 16, 64, e => e.Alive && e.WatchedAttributes.GetBool("backrooms:testTarget"));
            if (target == null)
            {
                target = SpawnDummy(x, floorY, z, out string why);
                if (target == null) return TextCommandResult.Error(why);
            }
            if (!dummies.Contains(target)) dummies.Add(target);
            // Dummies are never players: assess them here
            if (!watches.TryGetValue(target.EntityId, out Watch dummyWatch)) watches[target.EntityId] = dummyWatch = new Watch();
            Assess(target, dummyWatch);
        }

        var a = new Assessment();
        Rate(a, (int)Math.Floor(target.Pos.X), target.Pos.Y, (int)Math.Floor(target.Pos.Z));
        var entry = new RosterEntry(code, MenaceBand.Heartland, Encounters.Menacing | Encounters.Ambient, 1, 1, kind is Encounter.Stalk or Encounter.Hunt ? 2 : 1)
        {
            NeedsDark = code == Roster.Smiler,
            Aquatic = code == Roster.TheThing,
            Ambush = code is Roster.Clump, // (the Giant Spider is not put in ambush by the roster either)
            Outdoors = code is Roster.NeighborhoodWatch or Roster.Watcher,
        };
        // Put it down at the right distance (or the one asked for); failing that, anywhere 14 blocks off
        int distance = args.Parsers[4].IsMissing ? 14 : (int)args[4];
        if (args.Parsers[4].IsMissing && TrySpawn(target, a, entry, kind, setPiece: true)) return TextCommandResult.Success($"{code} ({kind}) put down for {target.Code}");
        for (int attempt = 0; attempt < 60; attempt++)
        {
            // (In a maze of narrow tunnels most points at a set distance are rock: try nearer ones too)
            double angle = rand.NextDouble() * Math.PI * 2, d = attempt < 20 ? distance : 3 + rand.NextDouble() * distance;
            int x = (int)Math.Floor(target.Pos.X + Math.Cos(angle) * d), z = (int)Math.Floor(target.Pos.Z + Math.Sin(angle) * d);
            Vec3d at;
            if (entry.Aquatic) at = FindWaterSpot(target, a, x, z);
            else
            {
                int y = Senses.FindFloor(sapi.World, x, (int)Math.Floor(target.Pos.Y), z);
                at = y == int.MinValue ? null : new Vec3d(x + 0.5, y, z + 0.5);
            }
            if (at == null) continue;
            Spawn(type, at, target, kind, a.Passive);
            return TextCommandResult.Success($"{code} ({kind}) put down {distance} blocks from {target.Code}");
        }
        return TextCommandResult.Error("Found nowhere to put it");
    }

    /// <summary>A straw dummy to stand in for a player in headless tests.</summary>
    private Entity SpawnDummy(int x, int y, int z, out string why)
    {
        why = null;
        // Keep the area loaded: with nobody online the server would otherwise unload it, entities and all
        int cx = x / GlobalConstants.ChunkSize, cz = z / GlobalConstants.ChunkSize;
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
                sapi.WorldManager.LoadChunkColumn(cx + dx, cz + dz, true);
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, y, z) == null) { why = "The chunk is not loaded yet; it is loading now, try again in a moment"; return null; }
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation("game:strawdummy"));
        if (type == null) { why = "No straw dummy entity type"; return null; }
        // (At sea, the nearest bit of solid ground will do)
        int floor = int.MinValue;
        for (int r = 0; r <= 24 && floor == int.MinValue; r += 2)
        {
            for (int i = 0; i < Math.Max(1, r * 4) && floor == int.MinValue; i++)
            {
                double angle = i * Math.PI * 2 / Math.Max(1, r * 4);
                int fx = x + (int)Math.Round(Math.Cos(angle) * r), fz = z + (int)Math.Round(Math.Sin(angle) * r);
                floor = Senses.FindFloor(sapi.World, fx, y, fz);
                if (floor != int.MinValue) (x, z) = (fx, fz);
            }
        }
        if (floor == int.MinValue) { why = "No floor within 24 blocks of there (open sea?)"; return null; }
        Entity dummy = sapi.World.ClassRegistry.CreateEntity(type);
        dummy.Pos.SetPos(x + 0.5, floor, z + 0.5);
        dummy.WatchedAttributes.SetBool("backrooms:testTarget", true);
        dummy.AlwaysActive = true;
        sapi.World.SpawnEntity(dummy);
        return dummy;
    }
}
