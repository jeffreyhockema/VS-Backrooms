using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms;

/// <summary>
/// What each player has found, for the handbook (<see cref="Discovery"/>; the pages are DiscoveryPages.cs). Server side
/// only, per player, in a Backrooms world:
/// <list type="bullet">
/// <item><b>Levels visited:</b> the level a player stands in is marked every tick (the Hub's tower tick marks the same bits).</item>
/// <item><b>Creatures met</b> (config/guide.json's codes): a creature is met when it has been within
/// <see cref="MeetRange"/> blocks and in the player's view (<see cref="Senses.Sees"/>, <see cref="MeetHalfAngle"/>
/// degrees either side of where they look, nothing in between) for <see cref="MeetMs"/> ms together, or has hurt
/// them, or they have struck, used or killed it. Heard, glimpsed off to the side, or on the HUD does not count. Things
/// that are not entities count when they have happened to the player (a <see cref="GuideTable.Creature.PlayerAttribute"/>).</item>
/// </list>
/// <c>/backrooms discover status|all|reset|level &lt;id|all&gt;|creature &lt;code|all&gt; [player]</c> for testing.
/// </summary>
public class DiscoverySystem : ModSystem
{
    public const double MeetRange = 32, MeetHalfAngle = 45;
    public const int MeetMs = 1000, TickMs = 250;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private GuideTable table;
    /// <summary>How long (ms) each player has had each entity in view without a break: player uid to entity id to ms.</summary>
    private readonly Dictionary<string, Dictionary<long, int>> inView = new();
    /// <summary>Players whose health this system listens to (an entity is listened to once).</summary>
    private readonly ConditionalWeakTable<EntityPlayer, object> hooked = new();

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.1;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            table = GuideTable.Load(api);
            api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] discovery: {0}", e), TickMs, 1000);
            api.Event.PlayerNowPlaying += Hook;
            api.Event.PlayerRespawn += Hook;
            api.Event.PlayerDisconnect += p => inView.Remove(p.PlayerUID);
            api.Event.OnPlayerInteractEntity += OnInteractEntity;
            api.Event.OnEntityDeath += OnEntityDeath;
            foreach (IPlayer online in api.World.AllOnlinePlayers) if (online is IServerPlayer sp) Hook(sp);
        });
        RegisterCommands(api);
    }

    // ================= Levels and sight =================

    private void OnTick(float dt)
    {
        if (layout == null || table == null) return;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { Alive: true } entity } player) continue;
            int level = LevelOf(entity);
            MarkLevel(entity, level);
            Look(player, entity, level);
        }
    }

    private int LevelOf(Entity entity) =>
        layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z)));

    private static void MarkLevel(Entity entity, int level)
    {
        if (level is < 0 or > Discovery.MaxLevelBit) return;
        int bits = entity.WatchedAttributes.GetInt(Discovery.VisitedKey);
        if ((bits & (1 << level)) == 0) entity.WatchedAttributes.SetInt(Discovery.VisitedKey, bits | (1 << level));
    }

    /// <summary>What a player has had in view for a second, and the things that are not entities.</summary>
    private void Look(IServerPlayer player, EntityPlayer entity, int level)
    {
        HashSet<string> met = Discovery.Met(entity);
        foreach (GuideTable.Creature c in table.Entities)
            if (c.PlayerAttribute != null && !met.Contains(c.Code) && entity.WatchedAttributes.GetInt(c.PlayerAttribute) != 0)
                Meet(entity, new[] { c.Code });

        if (!inView.TryGetValue(player.PlayerUID, out Dictionary<long, int> seen)) inView[player.PlayerUID] = seen = new Dictionary<long, int>();
        var still = new HashSet<long>();
        Entity[] near = sapi.World.GetEntitiesAround(entity.Pos.XYZ, (float)MeetRange, (float)MeetRange,
            e => e != entity && e.Alive && e is not EntityPlayer && table.CreaturesOf(e, level).Any(code => !met.Contains(code)));
        foreach (Entity e in near)
        {
            if (!Senses.Sees(entity, e, MeetRange, MeetHalfAngle)) continue;
            still.Add(e.EntityId);
            int ms = seen.GetValueOrDefault(e.EntityId) + TickMs;
            seen[e.EntityId] = ms;
            if (ms >= MeetMs) Meet(entity, table.CreaturesOf(e, level));
        }
        foreach (long id in seen.Keys.Where(id => !still.Contains(id)).ToList()) seen.Remove(id);
    }

    // ================= Blows either way =================

    private void Hook(IServerPlayer player)
    {
        if (player?.Entity is not { } entity || hooked.TryGetValue(entity, out _)) return;
        if (entity.GetBehavior<EntityBehaviorHealth>() is not { } health) return;
        hooked.Add(entity, null);
        health.onDamaged += (damage, source) =>
        {
            if (table != null && source?.GetCauseEntity() is { } by && by is not EntityPlayer) Meet(entity, table.CreaturesOf(by, LevelOf(entity)));
            return damage;
        };
    }

    /// <summary>Struck or used (right-clicked): met.</summary>
    private void OnInteractEntity(Entity entity, IPlayer byPlayer, ItemSlot slot, Vec3d hitPosition, int mode, ref EnumHandling handling)
    {
        if (table == null || layout == null || byPlayer?.Entity is not { } player || entity is EntityPlayer) return;
        Meet(player, table.CreaturesOf(entity, LevelOf(player)));
    }

    /// <summary>Killed from afar (an arrow, a thrown spear): met.</summary>
    private void OnEntityDeath(Entity entity, DamageSource source)
    {
        if (table == null || layout == null || entity is EntityPlayer || source?.GetCauseEntity() is not EntityPlayer player) return;
        Meet(player, table.CreaturesOf(entity, LevelOf(player)));
    }

    /// <summary>Adds creatures to what a player has met (the handbook shows their pages from then on).</summary>
    public static void Meet(Entity player, IEnumerable<string> codes)
    {
        if (player == null) return;
        HashSet<string> met = Discovery.Met(player);
        int before = met.Count;
        foreach (string code in codes) met.Add(code);
        if (met.Count != before) player.WatchedAttributes.SetString(Discovery.MetKey, Discovery.Join(met));
    }

    // ================= /backrooms discover =================

    private void RegisterCommands(ICoreServerAPI api)
    {
        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        var parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("discover")
                .WithDescription("The handbook's discovery (levels visited, creatures met), for testing: status, all, reset, level <id|all>, creature <code|all>, each for you or a named player")
                .BeginSubCommand("status")
                    .WithDescription("Lists the levels a player has visited and the creatures they have met")
                    .WithArgs(parsers.OptionalWord("player"))
                    .HandleWith(args => WithPlayer(args, 0, e => TextCommandResult.Success(Status(e))))
                .EndSubCommand()
                .BeginSubCommand("all")
                    .WithDescription("Every level visited and every creature met")
                    .WithArgs(parsers.OptionalWord("player"))
                    .HandleWith(args => WithPlayer(args, 0, e =>
                    {
                        int bits = 0;
                        foreach (int l in table.Levels) if (l is >= 0 and <= Discovery.MaxLevelBit) bits |= 1 << l;
                        e.WatchedAttributes.SetInt(Discovery.VisitedKey, e.WatchedAttributes.GetInt(Discovery.VisitedKey) | bits);
                        Meet(e, table.Entities.Select(c => c.Code));
                        return TextCommandResult.Success("Everything discovered. " + Status(e));
                    }))
                .EndSubCommand()
                .BeginSubCommand("reset")
                    .WithDescription("Nothing visited (but the level you stand in, marked again at once) and nothing met. The Hub's Keymaster reads the same levels")
                    .WithArgs(parsers.OptionalWord("player"))
                    .HandleWith(args => WithPlayer(args, 0, e =>
                    {
                        e.WatchedAttributes.SetInt(Discovery.VisitedKey, 0);
                        e.WatchedAttributes.SetString(Discovery.MetKey, "");
                        inView.Clear();
                        MarkLevel(e, LevelOf(e));
                        return TextCommandResult.Success("Discovery reset. " + Status(e));
                    }))
                .EndSubCommand()
                .BeginSubCommand("level")
                    .WithDescription("Marks a level visited (a number or name as /backrooms goto takes it: 37, 94, !, fun, end, hub, 974, 3999, 188; or #<id>), or all")
                    .WithArgs(parsers.Word("level"), parsers.OptionalWord("player"))
                    .HandleWith(args => WithPlayer(args, 1, e =>
                    {
                        string which = (string)args[0];
                        int[] levels = which == "all" ? table.Levels : new[] { ParseLevel(which) };
                        if (levels.Any(l => l < 0 || l > Discovery.MaxLevelBit)) return TextCommandResult.Error("No such level (try 0-11, 37, 94, !, fun, end, hub, 974, 3999, 188, #<id> or all)");
                        foreach (int l in levels) MarkLevel(e, l);
                        return TextCommandResult.Success("Visited. " + Status(e));
                    }))
                .EndSubCommand()
                .BeginSubCommand("creature")
                    .WithDescription("Marks a creature met (a code from config/guide.json: hound, smiler, partygoer, ...), or all")
                    .WithArgs(parsers.Word("code"), parsers.OptionalWord("player"))
                    .HandleWith(args => WithPlayer(args, 1, e =>
                    {
                        string which = (string)args[0];
                        if (which != "all" && table.Find(which) == null) return TextCommandResult.Error("No such creature; the codes are: " + string.Join(", ", table.Entities.Select(c => c.Code)));
                        Meet(e, which == "all" ? table.Entities.Select(c => c.Code) : new[] { which });
                        return TextCommandResult.Success("Met. " + Status(e));
                    }))
                .EndSubCommand()
            .EndSubCommand();
    }

    private static int ParseLevel(string s) =>
        s.StartsWith("#") && int.TryParse(s.Substring(1), out int id) ? id : WorldLayout.FromDisplayName(s);

    /// <summary>Runs a discover command on the player named in argument <paramref name="playerArg"/> (or the caller).</summary>
    private TextCommandResult WithPlayer(TextCommandCallingArgs args, int playerArg, System.Func<EntityPlayer, TextCommandResult> action)
    {
        if (layout == null || table == null) return TextCommandResult.Error("Not a Backrooms world");
        EntityPlayer entity;
        if (args.Parsers[playerArg].IsMissing)
        {
            entity = args.Caller.Entity as EntityPlayer;
            if (entity == null) return TextCommandResult.Error("Name a player (from the console)");
        }
        else
        {
            string name = (string)args[playerArg];
            entity = sapi.World.AllOnlinePlayers.FirstOrDefault(p => string.Equals(p.PlayerName, name, StringComparison.OrdinalIgnoreCase))?.Entity;
            if (entity == null) return TextCommandResult.Error("No player online named " + name);
        }
        return action(entity);
    }

    private string Status(EntityPlayer e)
    {
        int bits = Discovery.Visited(e);
        var visited = table.Levels.Where(l => Discovery.HasVisited(bits, l)).Select(l => WorldLayout.DisplayNumber(l)).ToList();
        HashSet<string> met = Discovery.Met(e);
        var known = table.Entities.Where(c => met.Contains(c.Code)).Select(c => c.Code).ToList();
        string name = e.Player?.PlayerName ?? "?";
        return $"{name}: visited {visited.Count} ({(visited.Count == 0 ? "none" : string.Join(", ", visited))}); met {known.Count} of {table.Entities.Length} ({(known.Count == 0 ? "none" : string.Join(", ", known))})";
    }
}
