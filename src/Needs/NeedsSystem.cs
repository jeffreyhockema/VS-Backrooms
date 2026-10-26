using System;
using System.Globalization;
using System.Linq;
using System.Text;
using Backrooms.Entities;
using HarmonyLib;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Needs;

/// <summary>
/// Thirst and fatigue (docs/design/needs/README.md): registers the two player behaviours (added to the player by
/// <c>patches/player-needs.json</c>), sums the stability offsets into vanilla's field once a second, rolls the night
/// visits, words the "died of thirst" death message, tells players of worlds made before the needs that both are on, and
/// has the commands <c>/backrooms needs</c> and <c>/backrooms needstest</c> (the meters' own cheats are in CheatSystem).
/// </summary>
public class NeedsSystem : ModSystem
{
    /// <summary>Player attribute (saved with the player): the one-time chat note about the needs in an older world was given.</summary>
    public const string NoticeKey = "backrooms:needsNotice";

    private const string HarmonyId = "backroomsss.needs";

    /// <summary>A closed door this near the bed (blocks) halves the odds of a night visit.</summary>
    public const int DoorRadius = 4;

    /// <summary>The server's instance (null on a client, or before the server started).</summary>
    public static NeedsSystem Instance { get; private set; }

    private ICoreServerAPI sapi;
    private long tickListener;
    private Harmony harmony;
    private readonly Random rand = new();

    // After BackroomsModSystem (1.0), which creates the /backrooms command
    public override double ExecuteOrder() => 1.2;

    public override void Start(ICoreAPI api)
    {
        api.RegisterEntityBehaviorClass(EntityBehaviorThirst.Code, typeof(EntityBehaviorThirst));
        api.RegisterEntityBehaviorClass(EntityBehaviorFatigue.Code, typeof(EntityBehaviorFatigue));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        Instance = this;
        harmony = new Harmony(HarmonyId);
        harmony.UnpatchAll(HarmonyId);
        // (The death message is private to the server's entity simulation; without this patch a death of thirst reads "Player died.")
        if (AccessTools.TypeByName("Vintagestory.Server.ServerSystemEntitySimulation") is { } simulation
            && AccessTools.Method(simulation, "GetDeathMessage") is { } method)
        {
            try { harmony.Patch(method, postfix: new HarmonyMethod(typeof(NeedsSystem), nameof(DeathMessagePostfix))); }
            catch (Exception e) { api.Logger.Warning("[backrooms] needs: the death message hook could not be applied ({0}); a death of thirst reads as a plain death", e.Message); }
        }
        else api.Logger.Warning("[backrooms] needs: the death message hook was not found; a death of thirst reads as a plain death");

        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            tickListener = api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] needs: {0}", e), 1000, 500);
        });
        api.Event.PlayerNowPlaying += OnPlayerNowPlaying;
        api.Event.PlayerDisconnect += OnPlayerDisconnect;

        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        command
            .BeginSubCommand("needs")
                .WithDescription("Shows a player's thirst and fatigue (yours, or a named player's): hydration, awake hours and band, caffeine, sickness, the bed under them and its quality, the stability offsets and the director's multiplier")
                .WithArgs(api.ChatCommands.Parsers.OptionalWord("player"))
                .HandleWith(OnNeedsCommand)
            .EndSubCommand()
            .BeginSubCommand("needstest")
                .WithDescription("Dev test: the needs' pure-math self-checks (drain per hour, band edges, tiredness mapping, director multiplier, visit odds), one PASS or FAIL line each")
                // (A console line ends in a carriage return the parser keeps as an argument; it is taken and ignored)
                .WithArgs(api.ChatCommands.Parsers.OptionalWord("ignored"))
                .HandleWith(_ => TextCommandResult.Success(SelfTest()))
            .EndSubCommand();
    }

    public override void Dispose()
    {
        if (sapi != null)
        {
            sapi.Event.PlayerNowPlaying -= OnPlayerNowPlaying;
            sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
            if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
            harmony?.UnpatchAll(HarmonyId);
            Needs.ForgetAllOffsets();
            if (Instance == this) Instance = null;
        }
        base.Dispose();
    }

    /// <summary>Once a second: every online player's stability offset is the sum of its named contributions.</summary>
    private void OnTick(float dt)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
            if (online.Entity is { } entity && Needs.HasOffsets(entity.EntityId)) Needs.ApplyStabilityOffset(entity);
    }

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        if (player.Entity != null) Needs.ForgetOffsets(player.Entity.EntityId);
    }

    /// <summary>A world made before the needs (no setting stored) has both on: say so once, and how to turn one off.</summary>
    private void OnPlayerNowPlaying(IServerPlayer player)
    {
        EntityPlayer entity = player.Entity;
        if (entity == null || !BackroomsWorld.IsBackroomsClimate(sapi.World.Config)) return;
        var config = sapi.World.Config;
        if (config.HasAttribute(Needs.ThirstSetting) && config.HasAttribute(Needs.FatigueSetting)) return;
        if (!Needs.ThirstOn(sapi.World) && !Needs.FatigueOn(sapi.World)) return;
        if (entity.Attributes.GetBool(NoticeKey)) return;
        entity.Attributes.SetBool(NoticeKey, true);
        // (A moment after joining, so it is not lost among the join messages)
        sapi.World.RegisterCallback(_ => Tell(player, "backrooms:needs-oldworld"), 4000);
    }

    /// <summary>A chat line for a player, in their language.</summary>
    public static void Tell(IServerPlayer player, string key, params object[] args) =>
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, key, args), EnumChatType.Notification);

    private static void DeathMessagePostfix(DamageSource src, ref string __result)
    {
        if (src is not ThirstDamageSource thirst) return;
        // Like vanilla's own messages, in the server's language
        __result = Lang.Get("backrooms:deathmsg-thirst-" + (1 + Random.Shared.Next(3)), thirst.PlayerName ?? "?");
    }

    // ================= Night visits =================

    /// <summary>
    /// One slept game hour of a player in the bed at <paramref name="bed"/>: outside the director's Safe band, the chance
    /// <c>0.06 * danger * spawns * doorFactor</c> of a night visit (a hunter put down 12 to 18 blocks off, out of sight).
    /// </summary>
    internal void RollNightVisit(IServerPlayer player, BlockPos bed)
    {
        if (player?.Entity == null || !Needs.FatigueOn(sapi.World)) return;
        MenaceSystem menace = sapi.ModLoader.GetModSystem<MenaceSystem>();
        if (menace?.Layout == null || menace.Paused || !menace.Setting.Entities) return;
        MenaceSystem.Assessment a = menace.AssessmentOf(player.Entity);
        if (a.Band == MenaceBand.Safe) return;
        bool door = ClosedDoorNear(bed, DoorRadius);
        double chance = NeedsMath.VisitChance(Danger.OfLevel(a.Level), menace.Setting.SetPieceScale, door);
        double roll = rand.NextDouble();
        if (menace.Logging) sapi.Logger.Notification("[backrooms] night visit roll for {0}: {1:0.000} against {2:0.000} (level {3}, door {4})", player.PlayerName, roll, chance, a.Level, door ? "shut" : "none");
        if (roll < chance) menace.NightVisit(player);
    }

    /// <summary>
    /// Whether a closed door stands within <paramref name="radius"/> blocks of a bed: a game door (the door behaviour,
    /// not open, as the Skin-Stealer's door search has it) or one of the mod's doors whose code says closed, locked or sealed.
    /// </summary>
    public bool ClosedDoorNear(BlockPos bed, int radius)
    {
        if (bed == null) return false;
        IBlockAccessor ba = sapi.World.BlockAccessor;
        var pos = new BlockPos(bed.dimension);
        for (int dy = -1; dy <= 2; dy++)
            for (int dz = -radius; dz <= radius; dz++)
                for (int dx = -radius; dx <= radius; dx++)
                {
                    pos.Set(bed.X + dx, bed.Y + dy, bed.Z + dz);
                    Block block = ba.GetBlock(pos);
                    if (block == null || block.Id == 0) continue;
                    if (block.GetBehavior<BlockBehaviorDoor>() != null)
                    {
                        if (BlockBehaviorDoor.getDoorAt(sapi.World, pos) is { Opened: false }) return true;
                        continue;
                    }
                    string path = block.Code?.Path;
                    if (path != null && path.Contains("door") && (path.Contains("-closed") || path.Contains("-locked") || path.Contains("-sealed"))) return true;
                }
        return false;
    }

    // ================= Commands =================

    private TextCommandResult OnNeedsCommand(TextCommandCallingArgs args)
    {
        Entity entity = args.Caller.Entity;
        string name = args.Parsers[0].IsMissing ? null : ((string)args[0]).Trim();
        if (!string.IsNullOrEmpty(name))
        {
            IPlayer named = sapi.World.AllOnlinePlayers.FirstOrDefault(p => string.Equals(p.PlayerName, name, StringComparison.OrdinalIgnoreCase));
            if (named?.Entity == null) return TextCommandResult.Error("No player online called " + name);
            entity = named.Entity;
        }
        if (entity is not EntityPlayer player) return TextCommandResult.Error("From the console, name a player: /backrooms needs <player>");
        return TextCommandResult.Success(Describe(player));
    }

    /// <summary>The /backrooms needs readout.</summary>
    public string Describe(EntityPlayer player)
    {
        IWorldAccessor world = player.World;
        double now = world.Calendar.TotalHours;
        var text = new StringBuilder();
        var inv = CultureInfo.InvariantCulture;
        bool thirstOn = Needs.ThirstOn(world), fatigueOn = Needs.FatigueOn(world);
        float hydration = Needs.Hydration(player), fraction = Needs.HydrationFraction(player), awake = Needs.AwakeHours(player);
        text.AppendFormat(inv, "Needs of {0} (thirst {1}, fatigue {2}):", player.Player?.PlayerName ?? "?", thirstOn ? "on" : "off", fatigueOn ? "on" : "off");
        text.AppendFormat(inv, "\nHydration {0:0} / {1:0} ({2:0}%, {3}); thirstrate x{4:0.00}", hydration, Needs.MaxHydration, fraction * 100, NeedsMath.ThirstBand(fraction), player.Stats.GetBlended("thirstrate"));
        text.AppendFormat(inv, "\nAwake {0:0.0} h (rest {1:0}%, {2}); vanilla tiredness {3:0.0}", awake, Needs.RestFraction(player) * 100, NeedsMath.Band(awake),
            player.GetBehavior<EntityBehaviorTiredness>()?.Tiredness ?? 0);
        var tree = player.WatchedAttributes.GetTreeAttribute(Needs.FatigueTree);
        double caffeine = tree?.GetDouble("caffeineUntil", 0) ?? 0;
        float crash = tree?.GetFloat("crashHours", 0) ?? 0;
        text.Append(Needs.Caffeinated(player) ? string.Format(inv, "\nCaffeinated for {0:0.0} more h, then {1:0} h land", caffeine - now, crash) : "\nNot caffeinated");
        double sick = player.WatchedAttributes.GetDouble(Needs.SickKey, 0);
        text.Append(Needs.IsSick(player) ? string.Format(inv, "; gut rot for {0:0.0} more h", sick - now) : "; not sick");
        text.AppendFormat(inv, "\nWalkspeed: thirst {0:+0.00;-0.00;0}, fatigue {1:+0.00;-0.00;0}", Needs.StatOf(player, "walkspeed", EntityBehaviorThirst.WalkStat), Needs.StatOf(player, "walkspeed", EntityBehaviorFatigue.WalkStat));
        text.AppendFormat(inv, "\nStability offsets: {0} (sum {1:+0.00;-0.00;0})", Needs.StabilitySources(player), Needs.StabilityOffset(player));
        if (player.MountedOn is BlockEntity bed)
            text.AppendFormat(inv, "\nAsleep in {0} at {1} {2} {3}, quality {4:0.00}{5}", bed.Block?.Code, bed.Pos.X, bed.Pos.Y, bed.Pos.Z, EntityBehaviorFatigue.Quality(player),
                ClosedDoorNear(bed.Pos, DoorRadius) ? ", a closed door near" : "");
        else text.Append("\nNot in a bed");
        text.AppendFormat(inv, "\nDirector multiplier x{0:0.00}", Needs.DirectorMult(player));
        if (player.Player is IServerPlayer sp && Needs.CanSleep(sp, null) is { } refusal) text.AppendFormat(inv, "; could not sleep now ({0})", refusal);
        return text.ToString();
    }

    private static string SelfTest()
    {
        var lines = NeedsMath.SelfTest(Danger.OfLevel);
        int failed = lines.Count(l => l.StartsWith("FAIL", StringComparison.Ordinal));
        lines.Add(string.Format(CultureInfo.InvariantCulture, "needstest: {0} checks, {1} failed", lines.Count, failed));
        return string.Join("\n", lines);
    }
}
