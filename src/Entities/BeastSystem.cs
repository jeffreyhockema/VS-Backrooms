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
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// The Beast of Level 5 (Entity 18): not something the director puts down, but an event, rare, and only in the
/// Terror Hotel (or wherever someone who owes him is, when he comes to collect). He chooses a victim:
/// <list type="number">
/// <item>The dread, most of a minute: the hotel's music stops round them (their client fades it out), a deep drum beats
/// somewhere far off, something whispers, and scraping and clanging come closer through the pipes. Once, at the edge
/// of their sight, a gentleman stands watching, and is gone when they turn to him. Leaving Level 5, or reaching a
/// safe place, ends it before he comes.</item>
/// <item>He comes: a burst of flame and a violent flash of violet light a few steps in front of them, and a gentleman
/// in a black fur suit with an octopus's head holds out a clawed hand (<see cref="AiTaskBeast"/>). He offers a deal.
/// Shake his hand and you are made whole (health, food, stability), and in three days he comes to collect, wherever
/// you are. Hold his gaze, standing your ground, and he is startled as no one startles him: he stands frozen, and
/// then he is gone. Refuse him (strike him, walk away, or let the offer lapse) and he unveils.</item>
/// <item>Unveiled: half as big again, wings spread, blades for claws, a hunter a little short of a sprint whose blows
/// are the worst in the hotel. A hunt that draws no blood for twenty seconds is given up; the
/// Beverly Room and the other safe places turn him away. Brought down, he dissolves and leaves Level 5's key (he is
/// believed to hold it), but not for long.</item>
/// </list>
/// A debt comes due three days after the handshake: he comes again with the dread, but makes no offer. Hold his gaze
/// and your soul is your own again; die to him and the debt is paid; get away and he will come again a day later.
/// The debt is kept with the player (<see cref="DueKey"/>); nothing else is saved.
/// </summary>
public class BeastSystem : ModSystem
{
    public const string Gentleman = "backrooms:beast", Unveiled = "backrooms:beast-unveiled";

    /// <summary>Player attribute (synced): how deep the dread round them is, 0 to 1; above nothing, Level 5's music stops.</summary>
    public const string DreadKey = "backrooms:beastDread";

    /// <summary>Player attribute (saved with the player): the calendar hour the debt from a handshake falls due; absent, none.</summary>
    public const string DueKey = "backrooms:beastDueHours";

    /// <summary>Entity attribute: put down to collect a debt (no deal is offered).</summary>
    public const string CollectKey = "backrooms:beastCollect";

    /// <summary>Entity attribute (synced): the violet flash he comes and goes in; its light while set.</summary>
    public const string FlashKey = "backrooms:beastFlash";

    /// <summary>Entity attribute (synced): the uid of the player the offer stands for, while it stands.</summary>
    public const string OfferKey = "backrooms:beastOffer";

    private const double DreadSeconds = 50, EndSeconds = 8, CooldownHours = 36, DueHours = 72, ReprieveHours = 24;

    private enum Phase { Dread, Manifest, Await, Ending }

    private sealed class Event
    {
        public Entity Target;
        public Phase Phase;
        public double Seconds, NextDrum = 2, NextWhisper = 9, NextClang = 30, GlimpseAt;
        public bool Glimpsed, Collect, Forced, Came;
        public float Dread;
        public double LastSeenBeast;
    }

    private static ICoreServerAPI sapi;
    private MenaceSystem director;
    private readonly Dictionary<long, Event> events = new();
    private readonly Dictionary<long, double> nextAllowedHours = new();
    private Random rand;

    // (After the mod system that makes the /backrooms command; the entity class and AI task are still registered in
    // Start, before any entity type is loaded)
    public override double ExecuteOrder() => 1.2;

    public override void Start(ICoreAPI api)
    {
        api.RegisterEntity("BackroomsBeast", typeof(EntityBeast));
        AiTaskRegistry.Register<AiTaskBeast>("backrooms-beast");
    }

    private long tickListener;

    private static void OnNowPlaying(IServerPlayer player) => player.Entity?.WatchedAttributes.SetFloat(DreadKey, 0);

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        long id = player.Entity?.EntityId ?? -1;
        if (events.TryGetValue(id, out Event e))
        {
            SendAway(e.Target);
            nextAllowedHours[id] = sapi.World.Calendar.TotalHours + CooldownHours;
            events.Remove(id);
        }
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        rand = new Random();
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            director = api.ModLoader.GetModSystem<MenaceSystem>();
            tickListener = api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] the Beast of Level 5: {0}", e), 1000, 1700);
            api.Event.OnEntityDeath += OnEntityDeath;
        });
        // (Nothing of an event outlives a restart: the dread starts at nothing)
        api.Event.PlayerNowPlaying += OnNowPlaying;
        api.Event.PlayerDisconnect += OnPlayerDisconnect;

        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("beast")
                .WithDescription("The Beast of Level 5 chooses you: the dread, then he comes (anywhere). 'due' makes a handshake's debt fall due now, 'clear' forgives it. From the console, give x and z: he chooses the straw dummy nearest there (put one down with /backrooms encounter)")
                .WithArgs(api.ChatCommands.Parsers.OptionalWord("what"), api.ChatCommands.Parsers.OptionalInt("x"), api.ChatCommands.Parsers.OptionalInt("z"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnBeastCommand)
            .EndSubCommand();
    }

    private TextCommandResult OnBeastCommand(TextCommandCallingArgs args)
    {
        if (director?.Layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string what = args.Parsers[0].IsMissing ? "come" : (string)args[0];
        Entity target = args.Caller.Entity;
        if (target == null)
        {
            if (args.Parsers[1].IsMissing || args.Parsers[2].IsMissing) return TextCommandResult.Error("From the console, give a word (come) and x and z");
            int x = (int)args[1], z = (int)args[2];
            target = sapi.World.GetNearestEntity(new Vec3d(x + 0.5, sapi.World.SeaLevel, z + 0.5), 32, 256, e => e.Alive && e.WatchedAttributes.GetBool("backrooms:testTarget"));
            if (target == null) return TextCommandResult.Error("No straw dummy near there: put one down with /backrooms encounter <entity> stalk x z first");
        }
        switch (what)
        {
            case "due":
                target.WatchedAttributes.SetDouble(DueKey, sapi.World.Calendar.TotalHours);
                nextAllowedHours.Remove(target.EntityId);
                return TextCommandResult.Success("Your debt to him falls due");
            case "clear":
                target.WatchedAttributes.RemoveAttribute(DueKey);
                return TextCommandResult.Success("You owe him nothing");
            default:
                if (events.ContainsKey(target.EntityId)) return TextCommandResult.Error("He has already chosen you");
                events[target.EntityId] = new Event { Target = target, Forced = true, GlimpseAt = 20 + rand.NextDouble() * 15, Collect = Owes(target) };
                return TextCommandResult.Success("The music stops");
        }
    }

    private static bool Owes(Entity player) => player.WatchedAttributes.HasAttribute(DueKey);

    // ================= The event =================

    private void OnTick(float dt)
    {
        double hours = sapi.World.Calendar.TotalHours;
        foreach (Event e in events.Values.ToList()) Advance(e, hours);

        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity is not { } entity || events.ContainsKey(entity.EntityId)) continue;
            if (!entity.Alive || player.WorldData.CurrentGameMode is EnumGameMode.Spectator or EnumGameMode.Creative || !director.Setting.Entities) continue;
            MenaceSystem.Assessment a = director.AssessmentOf(entity);

            // A debt that has fallen due is collected wherever its debtor is (only the Hub, of all places, is closed to him),
            // and the cooldown after an event does not hold it back, or the reprieve would really be the longer cooldown
            double due = entity.WatchedAttributes.GetDouble(DueKey, double.MaxValue);
            bool dueNow = hours >= due && a.Level != WorldLayout.Hub;
            if (!dueNow && hours < nextAllowedHours.GetValueOrDefault(entity.EntityId)) continue;
            if (dueNow)
            {
                events[entity.EntityId] = new Event { Target = entity, Collect = true, GlimpseAt = 20 + rand.NextDouble() * 15 };
                Log("he comes to collect from {0}", player.PlayerName);
                continue;
            }

            if (a.Level != 5 || a.Band == MenaceBand.Safe) continue;
            // Rare, rolled once a second: at set-piece scale 1 (Normal is 2.35 times as often), deep in the boiler halls about once
            // in twenty minutes at the edge of the hotel (1/1200), once in an hour further in; out in the guest wings and lobbies a quarter as often. Fear draws him:
            // up to three times as likely with your stability gone.
            bool boiler = director.Layout.IsHotelBoilerHall((int)Math.Floor(entity.Pos.X), (int)Math.Floor(entity.Pos.Z));
            double chance = a.Band switch { MenaceBand.Heartland => 1 / 4000.0, MenaceBand.Approach => 1 / 2000.0, _ => 1 / 1200.0 };
            if (!boiler) chance /= 4;
            chance *= (1 + 2 * (1 - Math.Clamp(Senses.Stability(entity), 0, 1))) * director.Setting.SetPieceScale * director.PartyShare(entity);
            if (rand.NextDouble() < chance)
            {
                events[entity.EntityId] = new Event { Target = entity, GlimpseAt = 20 + rand.NextDouble() * 15 };
                Log("he chooses {0} ({1})", player.PlayerName, boiler ? "in the boiler halls" : "in the hotel");
            }
        }
    }

    private void Advance(Event e, double hours)
    {
        Entity target = e.Target;
        e.Seconds += 1;
        if (target == null || !target.Alive || target.World == null)
        {
            if (e.Phase != Phase.Ending) Begin(e, Phase.Ending);
        }
        else if (e.Phase is Phase.Dread or Phase.Manifest)
        {
            // Out of the hotel, or somewhere safe, before he has come: he lets you be (unless he is owed)
            MenaceSystem.Assessment a = director.AssessmentOf(target);
            if (!e.Forced && !e.Collect && (a.Level != 5 || a.Band == MenaceBand.Safe)) Begin(e, Phase.Ending);
        }

        switch (e.Phase)
        {
            case Phase.Dread:
                e.Dread = (float)Math.Min(1, e.Seconds / 6);
                // A drum, far off; something whispering close by; then the scraping and clanging, coming closer
                if ((e.NextDrum -= 1) <= 0)
                {
                    e.NextDrum = 7 + rand.NextDouble() * 5;
                    Around(target, 40, 56, "backrooms:sounds/entity/beast/drum", 0.95f, 128, 0.9f);
                }
                if ((e.NextWhisper -= 1) <= 0)
                {
                    e.NextWhisper = 10 + rand.NextDouble() * 8;
                    Around(target, 5, 10, "backrooms:sounds/effect/whisper", 0.8f, 16, 0.5f);
                }
                if (e.Seconds >= e.NextClang)
                {
                    e.NextClang = e.Seconds + 5 + rand.NextDouble() * 3;
                    double near = 40 - 25 * (e.Seconds / DreadSeconds);
                    Around(target, near, near + 6, "backrooms:sounds/entity/beast/clang", 1f, 64, 0.8f);
                }
                if (!e.Glimpsed && e.Seconds >= e.GlimpseAt)
                {
                    e.Glimpsed = true;
                    Glimpse(target);
                }
                if (e.Seconds >= DreadSeconds) Begin(e, Phase.Manifest);
                break;

            case Phase.Manifest:
                e.Dread = 1;
                if (Come(target, e.Collect, ahead: e.Seconds < 12))
                {
                    e.Came = true;
                    e.LastSeenBeast = e.Seconds;
                    Begin(e, Phase.Await);
                }
                else if (e.Seconds > 20) Begin(e, Phase.Ending);
                break;

            case Phase.Await:
                e.Dread = 1;
                if (BeastsFor(target).Any()) e.LastSeenBeast = e.Seconds;
                else if (e.Seconds - e.LastSeenBeast > 3) Begin(e, Phase.Ending);
                break;

            case Phase.Ending:
                e.Dread = (float)Math.Max(0, 1 - e.Seconds / EndSeconds);
                if (e.Seconds >= EndSeconds)
                {
                    e.Dread = 0;
                    events.Remove(target?.EntityId ?? -1);
                    foreach (var pair in events.Where(p => p.Value == e).ToList()) events.Remove(pair.Key);
                    if (target != null) nextAllowedHours[target.EntityId] = hours + CooldownHours;
                    // Got away from a collection: he will come again. One that never got going (no place to stand him in) puts the
                    // debt off the same way, silently, or the next tick would start it again at once.
                    if (target is { Alive: true } && e.Collect && Owes(target) && hours >= target.WatchedAttributes.GetDouble(DueKey))
                    {
                        target.WatchedAttributes.SetDouble(DueKey, hours + ReprieveHours);
                        if (e.Came) Tell(target, "backrooms:beast-reprieve");
                    }
                    Log("the music comes back");
                }
                break;
        }

        if (target != null && Math.Abs(target.WatchedAttributes.GetFloat(DreadKey) - e.Dread) > 0.01f || e.Dread == 0)
            target?.WatchedAttributes.SetFloat(DreadKey, e.Dread);
    }

    private void Begin(Event e, Phase phase)
    {
        e.Phase = phase;
        e.Seconds = 0;
        Log("now {0}", phase);
    }

    /// <summary>The Beast's entities about a target, alive.</summary>
    private IEnumerable<Entity> BeastsFor(Entity target) =>
        sapi.World.GetEntitiesAround(target.Pos.XYZ, 96, 48, x => x.Alive && IsBeast(x) && EntityBehaviorMenace.OwnerOf(x) == target.EntityId);

    public static bool IsBeast(Entity entity) => entity.Code?.Domain == "backrooms" && entity.Code.Path is "beast" or "beast-unveiled";

    private void SendAway(Entity target)
    {
        if (target == null) return;
        foreach (Entity beast in BeastsFor(target).ToList()) Vanish(beast, flash: false);
    }

    /// <summary>At the edge of the target's sight, ten-odd blocks off: a gentleman, watching. Gone when looked at.</summary>
    private void Glimpse(Entity target)
    {
        Vec3f view = target.Pos.GetViewVector();
        double heading = Math.Atan2(view.Z, view.X);
        Vec3d eyes = Senses.Eyes(target);
        for (int attempt = 0; attempt < 16; attempt++)
        {
            double angle = heading + (rand.Next(2) == 0 ? 1 : -1) * (1.0 + rand.NextDouble() * 0.45), d = 9 + rand.NextDouble() * 6;
            Vec3d spot = Floor(target, angle, d);
            if (spot == null || !Senses.ClearLine(sapi.World, eyes, spot.AddCopy(0, 1.6, 0))) continue;
            Put(Gentleman, spot, target, Encounter.Glimpse, false);
            Log("a glimpse, {0:0} blocks off", d);
            return;
        }
    }

    /// <summary>Puts the gentleman down a few steps from the target, in front of them if it can. Returns whether it did.</summary>
    private bool Come(Entity target, bool collect, bool ahead)
    {
        Vec3f view = target.Pos.GetViewVector();
        double heading = Math.Atan2(view.Z, view.X);
        Vec3d eyes = Senses.Eyes(target);
        for (int attempt = 0; attempt < 20; attempt++)
        {
            double angle = ahead ? heading + (rand.NextDouble() - 0.5) * 1.6 : rand.NextDouble() * Math.PI * 2;
            double d = 4.5 + rand.NextDouble() * 2.5;
            Vec3d spot = Floor(target, angle, d);
            if (spot == null || !Senses.ClearLine(sapi.World, eyes, spot.AddCopy(0, 1.6, 0))) continue;
            if (Wards.Warded(sapi.World, spot) && !collect) continue;
            Entity beast = Put(Gentleman, spot, target, Encounter.Stalk, collect);
            if (beast == null) return false;
            Log("he comes, {0:0.0} blocks off{1}", d, collect ? ", to collect" : "");
            return true;
        }
        return false;
    }

    private Vec3d Floor(Entity target, double angle, double d)
    {
        int x = (int)Math.Floor(target.Pos.X + Math.Cos(angle) * d), z = (int)Math.Floor(target.Pos.Z + Math.Sin(angle) * d);
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, (int)target.Pos.Y, z) == null) return null;
        int y = Senses.FindFloor(sapi.World, x, (int)Math.Floor(target.Pos.Y), z, 2, 3);
        return y == int.MinValue ? null : new Vec3d(x + 0.5, y, z + 0.5);
    }

    /// <summary>Puts down one of the Beast's forms for a target: with his own numbers, not the level's danger.</summary>
    public static Entity Put(string code, Vec3d at, Entity target, Encounter kind, bool collect)
    {
        EntityProperties type = sapi?.World.GetEntityType(new AssetLocation(code));
        if (type == null) return null;
        Entity entity = sapi.World.ClassRegistry.CreateEntity(type);
        entity.Pos.SetPos(at.X, at.Y + 0.02, at.Z);
        entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - at.X, target.Pos.Z - at.Z);
        EntityBehaviorMenace.Prepare(entity, target, kind, false, sapi.World.ElapsedMilliseconds);
        if (target.WatchedAttributes.GetBool("backrooms:testTarget")) entity.AlwaysActive = true;
        entity.Attributes.SetDouble(Danger.Key, 0);
        entity.Attributes.SetBool(CollectKey, collect);
        sapi.World.SpawnEntity(entity);
        return entity;
    }

    // ================= What he does (called by AiTaskBeast and EntityBeast) =================

    /// <summary>His entrance: a column of flame, a violet flash, a roar of fire.</summary>
    public static void Manifest(Entity beast)
    {
        IWorldAccessor world = beast.World;
        Vec3d at = beast.Pos.XYZ;
        world.SpawnParticles(70, ColorUtil.ToRgba(255, 255, 150, 40), at.AddCopy(-0.4, 0, -0.4), at.AddCopy(0.4, 2.6, 0.4),
            new Vec3f(-0.3f, 1.5f, -0.3f), new Vec3f(0.3f, 4f, 0.3f), 0.8f, -0.05f, 0.9f, EnumParticleModel.Quad);
        Flash(beast);
        world.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/beast/flame"), at.X, at.Y + 1, at.Z, null, false, 32, 1f);
    }

    /// <summary>A violent flash of violet light, and the light of it for a moment.</summary>
    public static void Flash(Entity beast)
    {
        IWorldAccessor world = beast.World;
        Vec3d at = beast.Pos.XYZ;
        world.SpawnParticles(50, ColorUtil.ToRgba(255, 190, 90, 255), at.AddCopy(-0.6, 0.2, -0.6), at.AddCopy(0.6, 2.2, 0.6),
            new Vec3f(-2, -0.5f, -2), new Vec3f(2, 2, 2), 0.5f, 0f, 0.6f, EnumParticleModel.Quad);
        world.PlaySoundAt(new AssetLocation("game:sounds/effect/translocate-breakdimension"), at.X, at.Y + 1, at.Z, null, false, 32, 0.7f);
        beast.WatchedAttributes.SetBool(FlashKey, true);
        long id = beast.EntityId;
        world.RegisterCallback(_ =>
        {
            if (world.GetEntityById(id) is { } e) e.WatchedAttributes.SetBool(FlashKey, false);
        }, 1400);
    }

    /// <summary>Gone, in a flash or quietly (a glimpse that was looked at).</summary>
    public static void Vanish(Entity beast, bool flash)
    {
        if (!beast.Alive) return;
        if (flash)
        {
            Vec3d at = beast.Pos.XYZ;
            beast.World.SpawnParticles(40, ColorUtil.ToRgba(200, 60, 30, 80), at.AddCopy(-0.5, 0, -0.5), at.AddCopy(0.5, 2, 0.5),
                new Vec3f(-0.4f, 0.2f, -0.4f), new Vec3f(0.4f, 1.2f, 0.4f), 1.6f, -0.02f, 1.2f, EnumParticleModel.Quad);
            beast.World.PlaySoundAt(new AssetLocation("game:sounds/effect/translocate-breakdimension"), at.X, at.Y + 1, at.Z, null, false, 32, 0.6f);
        }
        beast.GetBehavior<EntityBehaviorMenace>()?.Despawn();
        if (beast.Alive) beast.Die(EnumDespawnReason.Expire);
    }

    /// <summary>Refused: "Why are you doubting me?" The suit opens like wings, and the thing inside comes out.</summary>
    public static void Unveil(Entity gentleman, Entity target)
    {
        if (!gentleman.Alive) return;
        Tell(target, "backrooms:beast-doubt");
        Vec3d at = gentleman.Pos.XYZ;
        bool collect = gentleman.Attributes.GetBool(CollectKey);
        Manifest(gentleman);
        gentleman.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/beast/roar"), at.X, at.Y + 2, at.Z, null, false, 48, 1f);
        gentleman.GetBehavior<EntityBehaviorMenace>()?.Despawn();
        if (gentleman.Alive) gentleman.Die(EnumDespawnReason.Expire);
        Entity beast = Put(Unveiled, at, target, Encounter.Hunt, collect);
        if (beast != null) Flash(beast);
        Strike.Log(gentleman, "refused: unveils");
    }

    /// <summary>The handshake: made whole now, and owed in three days.</summary>
    public static void Deal(Entity gentleman, EntityPlayer player)
    {
        if (!gentleman.Alive || gentleman.Attributes.GetBool(CollectKey) || Owes(player)) return;
        if (player.GetBehavior<EntityBehaviorHealth>() is { } health) health.Health = health.MaxHealth;
        if (player.GetBehavior<EntityBehaviorHunger>() is { } hunger) hunger.Saturation = hunger.MaxSaturation;
        player.WatchedAttributes.SetDouble("temporalStability", 1);
        player.WatchedAttributes.SetDouble(DueKey, gentleman.World.Calendar.TotalHours + DueHours);
        Tell(player, "backrooms:beast-deal");
        gentleman.WatchedAttributes.RemoveAttribute(OfferKey);
        Strike.Log(gentleman, "a deal with {0}", player.Player?.PlayerName);
        // He bows, and is gone
        long id = gentleman.EntityId;
        IWorldAccessor world = gentleman.World;
        gentleman.GetBehavior<EntityBehaviorMenace>().Kind = Encounter.Leave;
        world.RegisterCallback(_ =>
        {
            if (world.GetEntityById(id) is { Alive: true } e) Vanish(e, flash: true);
        }, 1200);
    }

    /// <summary>Looked in the eye, and not backing away: he is startled. A debt is forgiven by it.</summary>
    public static void Confronted(Entity gentleman, Entity target)
    {
        Tell(target, "backrooms:beast-shocked");
        if (gentleman.Attributes.GetBool(CollectKey) && Owes(target))
        {
            target.WatchedAttributes.RemoveAttribute(DueKey);
            Tell(target, "backrooms:beast-free");
        }
        Strike.Log(gentleman, "confronted by {0}", target.Code.Path);
    }

    public static void Greet(Entity gentleman, Entity target)
    {
        if (gentleman.Attributes.GetBool(CollectKey)) Tell(target, "backrooms:beast-collect");
        else Tell(target, "backrooms:beast-greet-" + (1 + gentleman.World.Rand.Next(3)));
        gentleman.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/beast/voice"), gentleman, null, false, 16, 0.8f);
    }

    private static void Tell(Entity target, string key)
    {
        if (target is EntityPlayer { Player: IServerPlayer player })
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.GetL(player.LanguageCode, key), EnumChatType.Notification);
        else if (sapi?.ModLoader.GetModSystem<MenaceSystem>()?.Logging == true)
            sapi.Logger.Notification("[backrooms] the Beast says to {0}: {1}", target?.Code, Lang.Get(key));
    }

    private void Around(Entity target, double near, double far, string sound, float volume, float range, float pitch)
    {
        double angle = rand.NextDouble() * Math.PI * 2, d = near + rand.NextDouble() * (far - near);
        sapi.World.PlaySoundAt(new AssetLocation(sound), target.Pos.X + Math.Cos(angle) * d, target.Pos.Y + 1.5, target.Pos.Z + Math.Sin(angle) * d,
            null, pitch + (float)rand.NextDouble() * 0.1f, range, volume);
    }

    private void OnEntityDeath(Entity entity, DamageSource source)
    {
        Entity cause = source?.GetCauseEntity();
        // A debtor he kills has paid
        if (entity is EntityPlayer && cause != null && IsBeast(cause) && Owes(entity)
            && sapi.World.Calendar.TotalHours >= entity.WatchedAttributes.GetDouble(DueKey))
        {
            entity.WatchedAttributes.RemoveAttribute(DueKey);
            Tell(entity, "backrooms:beast-taken");
            return;
        }
        if (entity.Code?.Path != "beast-unveiled" || entity.Code.Domain != "backrooms") return;
        // Brought down: he leaves what he held, Level 5's key, and a bounty; then he dissolves, as if he had never been
        Vec3d at = entity.Pos.XYZ.Add(0, 0.5, 0);
        if (cause is EntityPlayer)
        {
            if (sapi.World.GetItem(new AssetLocation("backrooms:hub-key-l5")) is { } key) sapi.World.SpawnItemEntity(new ItemStack(key), at);
            if (sapi.World.GetItem(new AssetLocation("game:gear-rusty")) is { } gear) sapi.World.SpawnItemEntity(new ItemStack(gear, 6 + rand.Next(5)), at);
        }
        long id = entity.EntityId;
        sapi.World.RegisterCallback(_ =>
        {
            if (sapi.World.GetEntityById(id) is not { } body) return;
            Vec3d p = body.Pos.XYZ;
            sapi.World.SpawnParticles(40, ColorUtil.ToRgba(200, 60, 30, 80), p.AddCopy(-0.8, 0, -0.8), p.AddCopy(0.8, 1, 0.8),
                new Vec3f(-0.3f, 0.2f, -0.3f), new Vec3f(0.3f, 1f, 0.3f), 1.8f, -0.02f, 1.2f, EnumParticleModel.Quad);
            sapi.World.DespawnEntity(body, new EntityDespawnData { Reason = EnumDespawnReason.Expire });
        }, 3000);
        Log("brought down");
    }

    private void Log(string format, params object[] args)
    {
        if (director?.Logging == true) sapi.Logger.Notification("[backrooms] the Beast of Level 5: " + string.Format(format, args));
    }

    // ================= Client: the music stops =================

    /// <summary>Whether the Beast is about (the dread round this player, or one of his forms in sight): Level 5's music stops.</summary>
    public static bool Hushed { get; private set; }

    private ICoreClientAPI capi;
    private float lookIn;
    private bool beastNear;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        Hushed = false;
        api.Event.RegisterGameTickListener(OnClientTick, 250);
    }

    public override void Dispose()
    {
        Hushed = false;
        if (sapi != null)
        {
            sapi.Event.PlayerNowPlaying -= OnNowPlaying;
            sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
            sapi.Event.OnEntityDeath -= OnEntityDeath;
            if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
        }
        base.Dispose();
    }

    private void OnClientTick(float dt)
    {
        Entity me = capi.World.Player?.Entity;
        if (me == null)
        {
            Hushed = false;
            return;
        }
        lookIn -= dt;
        if (lookIn <= 0)
        {
            lookIn = 1;
            beastNear = capi.World.GetNearestEntity(me.Pos.XYZ, 40, 16, e => e.Alive && IsBeast(e)) != null;
        }
        Hushed = beastNear || me.WatchedAttributes.GetFloat(DreadKey) > 0.02f;
    }
}

/// <summary>
/// Either of the Beast's forms: the violet flash he comes and goes in (and a faint violet from the unveiled form's
/// eyes); the handshake, for the one his offer stands for.
/// </summary>
public class EntityBeast : EntityAgent
{
    private static readonly byte[] FlashLight = { 48, 6, 18 }, EyeLight = { 48, 7, 3 };
    private WorldInteraction[] help;

    public override byte[] LightHsv
    {
        get => !Alive ? null : WatchedAttributes.GetBool(BeastSystem.FlashKey) ? FlashLight : Code?.Path == "beast-unveiled" ? EyeLight : null;
        set { }
    }

    public override WorldInteraction[] GetInteractionHelp(IClientWorldAccessor world, EntitySelection es, IClientPlayer player)
    {
        if (WatchedAttributes.GetString(BeastSystem.OfferKey) != player?.PlayerUID) return Array.Empty<WorldInteraction>();
        return help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:beast-help-shake", MouseButton = EnumMouseButton.Right } };
    }

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode)
    {
        // (A blow is dealt in EntityAgent.OnInteract, and comes through ReceiveDamage from there: a refusal)
        if (mode == EnumInteractMode.Attack)
        {
            base.OnInteract(byEntity, itemslot, hitPosition, mode);
            return;
        }
        if (World.Side != EnumAppSide.Server || byEntity is not EntityPlayer player) return;
        if (WatchedAttributes.GetString(BeastSystem.OfferKey) != player.PlayerUID) return;
        BeastSystem.Deal(this, player);
    }
}
