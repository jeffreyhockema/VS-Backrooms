using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Regions;

/// <summary>
/// Level 73's ways in and out, in the game (docs/design/experimental-levels/LINKS.md; the plan's "Links"). This file is the
/// level's own.
/// <list type="bullet">
/// <item><b>The Gloom</b> (Level 9): whoever stands in it is warned (<see cref="GloomStages"/>, seconds), and at the last is
/// on the island. Stepping out for a while (<see cref="LingerGraceMs"/>) lets it go. One way.</item>
/// <item><b>Level 6's deepest dark</b>: whoever lingers in one of its cells (WorldLayout.IsL73DarkCell) with no light in
/// hand and none about is warned (<see cref="DarkStages"/>), and at the last is on the island. One way.</item>
/// <item><b>A night under his roof</b>: whoever has slept <see cref="RestHours"/> game hours in the keep's beds since they
/// came (<see cref="RestedKey"/>) may ask Coran to lead them out (sneak and speak to him).</item>
/// <item><b>Coran leads you out</b>: he walks round the walls to the north door with whoever asked (waiting for them when
/// they fall behind, fighting whatever comes), tears the chain off it and opens it: beyond is only the dark, and through it
/// the Suburbs (ThresholdNetwork.L73.cs). It shuts itself again a little later. One way.</item>
/// </list>
/// Straw dummies (/backrooms dummy) stand in for players in the Gloom and the dark, for headless tests: they are carried to
/// where the way leads (written down as a player's trip would be).
/// </summary>
public partial class L73System
{
    /// <summary>The player's watched attributes: game hours slept in the keep since they came, and whether that makes a night.</summary>
    public const string SleptKey = "backrooms:l73Slept", RestedKey = "backrooms:l73Rested";

    /// <summary>How many hours asleep in the keep make "a night under his roof".</summary>
    public const double RestHours = 4;

    /// <summary>The Gloom's warnings and its taking, in seconds stood in it ("a minute or two, warned"); Level 6's deepest dark's.</summary>
    public static readonly int[] GloomStages = { 12, 40, 70, 90 }, DarkStages = { 60, 120, 160, 180 };

    /// <summary>How long out of the Gloom (or the dark) before it lets go and the count starts again.</summary>
    public const long LingerGraceMs = 20_000;

    /// <summary>How long the north door stands open; how long Coran keeps trying to lead someone who does not follow.</summary>
    public const long PosternOpenMs = 20_000, LeadGiveUpMs = 300_000;

    /// <summary>How far behind him a wanderer may fall before Coran stops and waits for them; past this, for long, he gives up.</summary>
    public const double LeadWaitBlocks = 10, LeadLostBlocks = 64;

    /// <summary>The radius of the round he leads by, outside the walls and the corner towers.</summary>
    private const double LeadRing = 44;

    private sealed class Linger
    {
        public double Seconds;
        public int Stage;
        public long LastInMs;
        public bool Out;
        public int X, Z;
    }

    private readonly Dictionary<string, Linger> gloomFor = new(), darkFor = new();
    private readonly Dictionary<string, double> sleptAt = new();
    private long nextDummyLinkMs;

    private string leadUid;
    private long leadStartMs, leadLostSinceMs = -1, openAtMs = -1;
    private bool posternChecked;
    private long posternCloseAtMs = -1;

    /// <summary>Whether the north door stands open (ThresholdSystem lets nobody through it otherwise).</summary>
    public bool PosternOpen { get; private set; }

    /// <summary>Whether Coran is at the north door, tearing its chain off (he stands there).</summary>
    public bool LeadOpening => openAtMs >= 0;

    private ThresholdSystem Thresholds => sapi.ModLoader.GetModSystem<ThresholdSystem>();

    private void LinksTick(long now)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity is not { Alive: true } entity) continue;
            if (player.ConnectionState != EnumClientState.Playing) continue;
            Rest(player, entity);
            if (player.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator) continue;
            Lingering(player.PlayerUID, entity, player, 1);
        }
        if (now >= nextDummyLinkMs)
        {
            nextDummyLinkMs = now + 2000;
            foreach (Entity dummy in sapi.World.LoadedEntities.Values.Where(e => e.Alive && Senses.IsTestTarget(e)).ToList())
                Lingering("dummy#" + dummy.EntityId, dummy, null, 2);
        }
        LeadTick(now);
        PosternTick(now);
    }

    // ================= The Gloom and the dark =================

    /// <summary>One second (or more) of someone (a player, or a dummy standing in for one) standing where they are.</summary>
    private void Lingering(string id, Entity entity, IServerPlayer player, double seconds)
    {
        long now = sapi.World.ElapsedMilliseconds;
        int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
        int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
        int level = layout.LevelAt(mx, mz);
        bool gloom = false, dark = false;
        if (level == 9)
        {
            double rel = entity.Pos.Y - geometry.FloorFor(9);
            gloom = rel > 0.5 && rel < 3.5 && WorldLayout.IsL73Gloom(layout.TileAt(x, z));
        }
        else if (level == 6 && layout.IsL73DarkCell(mx, mz))
        {
            // No light in hand, and none about: the deepest dark
            var eyes = new BlockPos(x, (int)Math.Floor(entity.Pos.Y + 1.5), z);
            dark = Senses.HeldLight(entity) < Senses.LitLevel && sapi.World.BlockAccessor.GetLightLevel(eyes, EnumLightLevelType.OnlyBlockLight) <= 3;
        }
        if (Step(gloomFor, id, gloom, seconds, now, x, z, GloomStages) is int g && g != 0) Reached(player, entity, "gloom", g, gloomFor, id, GloomStages.Length);
        if (Step(darkFor, id, dark, seconds, now, mx, mz, DarkStages) is int d && d != 0) Reached(player, entity, "dark", d, darkFor, id, DarkStages.Length);
    }

    /// <summary>
    /// Counts someone's time in a way in. Returns the stage just reached (1 the first warning ... the last, taken), minus the
    /// stage they had reached when they step out of it after a warning, or 0.
    /// </summary>
    private static int Step(Dictionary<string, Linger> table, string id, bool inside, double seconds, long now, int x, int z, int[] stages)
    {
        table.TryGetValue(id, out Linger l);
        if (!inside)
        {
            if (l == null) return 0;
            if (now - l.LastInMs > LingerGraceMs)
            {
                table.Remove(id);
                return 0;
            }
            if (l.Out) return 0;
            l.Out = true;
            return l.Stage > 0 ? -l.Stage : 0;
        }
        if (l == null) table[id] = l = new Linger();
        // (Back in it before it let go: the count goes on; out of it long enough, it started again above)
        l.LastInMs = now;
        l.Out = false;
        l.Seconds += seconds;
        l.X = x;
        l.Z = z;
        int reached = 0;
        while (l.Stage < stages.Length && l.Seconds >= stages[l.Stage]) reached = ++l.Stage;
        return reached;
    }

    /// <summary>A warning, the letting go, or the taking.</summary>
    private void Reached(IServerPlayer player, Entity entity, string way, int stage, Dictionary<string, Linger> table, string id, int last)
    {
        if (stage < 0)
        {
            if (player != null) Tell(player, $"backrooms:l73-{way}-left");
            return;
        }
        if (stage < last)
        {
            if (player != null) Tell(player, $"backrooms:l73-{way}-warn-{stage}");
            return;
        }
        Linger l = table[id];
        if (player != null)
        {
            if (Thresholds?.L73Take(player, way, l.X, l.Z) == true) table.Remove(id);
            else l.Stage--; // (busy just now: again next second)
            return;
        }
        // A dummy: carried where the way leads, as a player would be
        table.Remove(id);
        if (Thresholds?.L73WayLink(way, l.X, l.Z) is not { } to) return;
        // (Its ground kept loaded, as the dummy's own is: with nobody online it would be unloaded, dummy and all)
        int cx = (int)to.X / GlobalConstants.ChunkSize, cz = (int)to.Z / GlobalConstants.ChunkSize;
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                sapi.WorldManager.LoadChunkColumn(cx + dx, cz + dz, true);
        entity.TeleportToDouble(to.X, to.Y, to.Z);
        sapi.Logger.Notification("[backrooms] Level 73: dummy #{0} taken by the {1} at {2},{3} to {4:0.#},{5:0.#},{6:0.#}", entity.EntityId, way, l.X, l.Z, to.X, to.Y, to.Z);
    }

    private static void Tell(IServerPlayer player, string key) =>
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, key), EnumChatType.Notification);

    // ================= A night under his roof =================

    /// <summary>Asleep in the keep: the hours add up, and a night's worth makes them one he will lead out if they ask.</summary>
    private void Rest(IServerPlayer player, EntityPlayer entity)
    {
        string uid = player.PlayerUID;
        int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
        bool asleep = InLevel(entity.Pos.X, entity.Pos.Z) && layout.TileAt(x, z).Zone == WorldLayout.L73Keep && Needs.EntityBehaviorFatigue.Sleeping(entity);
        double hours = sapi.World.Calendar.TotalHours;
        if (!asleep)
        {
            sleptAt.Remove(uid);
            return;
        }
        if (sleptAt.TryGetValue(uid, out double was))
        {
            // (A jump of the clock counts for at most two hours)
            double slept = entity.WatchedAttributes.GetDouble(SleptKey) + Math.Clamp(hours - was, 0, 2);
            entity.WatchedAttributes.SetDouble(SleptKey, slept);
            if (slept >= RestHours && !entity.WatchedAttributes.GetBool(RestedKey))
            {
                entity.WatchedAttributes.SetBool(RestedKey, true);
                Tell(player, "backrooms:l73-rested");
            }
        }
        sleptAt[uid] = hours;
    }

    /// <summary>Whether a player has slept a night under Coran's roof since they came.</summary>
    public static bool Rested(IServerPlayer player) => player.Entity?.WatchedAttributes.GetBool(RestedKey) == true;

    /// <summary>Someone has come to the island (again): no night under his roof yet.</summary>
    public void ForgetRest(IServerPlayer player)
    {
        if (player.Entity == null) return;
        player.Entity.WatchedAttributes.SetDouble(SleptKey, 0);
        player.Entity.WatchedAttributes.SetBool(RestedKey, false);
    }

    // ================= Coran leads you out =================

    /// <summary>The one he is leading, if any (a player in the level).</summary>
    public EntityPlayer LedPlayer => leadUid != null && sapi.World.PlayerByUid(leadUid) is IServerPlayer { Entity: { Alive: true } e } && InLevel(e.Pos.X, e.Pos.Z) ? e : null;

    /// <summary>Someone, sneaking, has spoken to Coran: asked him to lead them out.</summary>
    public void AskToLeave(Entity coran, IServerPlayer player)
    {
        if (!Rested(player))
        {
            CoranSays(coran, player, "backrooms:l73-coran-lead-notyet");
            return;
        }
        if (leadUid == player.PlayerUID)
        {
            CoranSays(coran, player, "backrooms:l73-coran-lead-again");
            return;
        }
        if (leadUid != null && LedPlayer != null)
        {
            CoranSays(coran, player, "backrooms:l73-coran-lead-busy");
            return;
        }
        StartLead(coran, player);
    }

    private void StartLead(Entity coran, IServerPlayer player)
    {
        leadUid = player.PlayerUID;
        leadStartMs = sapi.World.ElapsedMilliseconds;
        leadLostSinceMs = -1;
        openAtMs = -1;
        CoranSays(coran, player, "backrooms:l73-coran-lead-1");
        sapi.Logger.Notification("[backrooms] Level 73: Coran leads {0} out to the north door at {1},{2}", player.PlayerName, layout.L73Postern.X, layout.L73Postern.Z);
    }

    /// <summary>Where Coran stands to open the north door, on the ground.</summary>
    public Vec3d PosternFront
    {
        get
        {
            var (fx, fz) = layout.L73PosternFront;
            return new Vec3d(fx, geometry.FloorFor(WorldLayout.Level73) + WorldLayout.L73Plateau + 1, fz);
        }
    }

    /// <summary>
    /// The next place to walk to on the way to the north door from a position: round the castle on a ring outside its walls
    /// and towers, a step of the ring at a time, the short way round; once on the north side, straight to the door.
    /// </summary>
    public Vec3d LeadWaypoint(Vec3d at)
    {
        Vec3d c = CastleMiddle, front = PosternFront;
        double a = Math.Atan2(at.Z - c.Z, at.X - c.X), toDoor = Math.Atan2(front.Z - c.Z, front.X - c.X);
        double diff = Math.IEEERemainder(toDoor - a, Math.PI * 2);
        if (Math.Abs(diff) < 0.3) return front;
        double next = a + Math.Sign(diff) * Math.Min(Math.Abs(diff), 0.55);
        int gx = (int)Math.Floor(c.X + Math.Cos(next) * LeadRing), gz = (int)Math.Floor(c.Z + Math.Sin(next) * LeadRing);
        double y = GroundAt(gx, gz) ?? geometry.FloorFor(WorldLayout.Level73) + WorldLayout.L73Plateau + 1;
        return new Vec3d(gx + 0.5, y, gz + 0.5);
    }

    /// <summary>Coran has fallen too far ahead of the one he leads: he says so, now and then.</summary>
    public void LeadWait(Entity coran)
    {
        if (sapi.World.PlayerByUid(leadUid ?? "") is IServerPlayer player) CoranSays(coran, player, "backrooms:l73-coran-lead-wait");
    }

    /// <summary>Coran stands at the north door: he tears the chain off it, and a moment later it opens.</summary>
    public void CoranAtDoor(Entity coran, long now)
    {
        if (openAtMs >= 0 || PosternOpen) return;
        openAtMs = now + 900;
        coran.AnimManager.StartAnimation("attack");
        BlockPos at = PosternPos(1, 1);
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/73/coran/chain1"), at.X, at.Y, at.Z, null, true, 32, 1f);
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/73/coran/strike1"), at.X, at.Y, at.Z, null, true, 32, 0.8f);
    }

    private void LeadTick(long now)
    {
        if (leadUid == null) return;
        var player = sapi.World.PlayerByUid(leadUid) as IServerPlayer;
        Entity coran = Coran;
        EntityPlayer led = LedPlayer;
        if (openAtMs >= 0 && now >= openAtMs)
        {
            // The chain falls away, the leaves swing out on the dark
            openAtMs = -1;
            OpenPostern(now);
            if (player != null && coran != null) CoranSays(coran, player, "backrooms:l73-coran-lead-open");
            leadUid = null;
            return;
        }
        if (openAtMs >= 0) return;
        bool lost = led == null || coran == null || now - leadStartMs > LeadGiveUpMs;
        if (!lost && led.Pos.HorDistanceTo(coran.Pos.XYZ) > LeadLostBlocks)
        {
            if (leadLostSinceMs < 0) leadLostSinceMs = now;
            lost = now - leadLostSinceMs > 30_000;
        }
        else if (!lost) leadLostSinceMs = -1;
        if (!lost) return;
        leadUid = null;
        if (player != null && led != null) Tell(player, "backrooms:l73-coran-lead-giveup");
    }

    // ================= The north door =================

    private BlockPos PosternPos(int leaf, int up) =>
        new(layout.L73Postern.X + leaf, geometry.FloorFor(WorldLayout.Level73) + WorldLayout.L73Plateau + 1 + up, layout.L73Postern.Z);

    /// <summary>A right-click on the north door: chained, and nothing on the other side of the wall shows a door.</summary>
    private void KnockPostern(IServerPlayer player, BlockPos pos)
    {
        if (PosternOpen) return;
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/chestclose"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 12, 0.5f);
        player.SendIngameError("l73postern", Say.T(player, Rested(player) ? "backrooms:l73-postern-ask" : "backrooms:l73-postern-locked"));
    }

    private void SetPostern(bool open)
    {
        string[] parts = { "wb", "eb", "wt", "et" };
        for (int up = 0; up < WorldLayout.L73PosternHeight; up++)
            for (int leaf = 0; leaf < 2; leaf++)
            {
                Block block = sapi.World.GetBlock(new AssetLocation($"backrooms:l73-postern-{(open ? "open" : "shut")}-{parts[leaf + 2 * up]}"));
                BlockPos pos = PosternPos(leaf, up);
                if (block == null || sapi.World.BlockAccessor.GetBlock(pos).Code?.Path.StartsWith("l73-postern-") != true) continue;
                sapi.World.BlockAccessor.ExchangeBlock(block.BlockId, pos);
                sapi.World.BlockAccessor.MarkBlockDirty(pos);
            }
        PosternOpen = open;
    }

    private void OpenPostern(long now)
    {
        SetPostern(true);
        posternCloseAtMs = now + PosternOpenMs;
        BlockPos at = PosternPos(1, 0);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/largedoor-open"), at.X, at.Y + 0.5, at.Z + 0.5, null, true, 32, 1f);
        sapi.Logger.Notification("[backrooms] Level 73: the north door opens at {0},{1},{2}", at.X - 1, at.Y, at.Z);
    }

    private void PosternTick(long now)
    {
        BlockPos at = PosternPos(0, 0);
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(at) == null)
        {
            posternChecked = false;
            return;
        }
        if (!posternChecked)
        {
            // (Left open when the world last stopped: shut again a little after its ground is loaded)
            posternChecked = true;
            PosternOpen = sapi.World.BlockAccessor.GetBlock(at).Code?.Path.StartsWith("l73-postern-open") == true;
            if (PosternOpen) posternCloseAtMs = now + 6000;
        }
        if (!PosternOpen || now < posternCloseAtMs) return;
        // Not on anyone standing in the doorway
        var box = new Cuboidd(at.X, at.Y, at.Z - 1, at.X + 2, at.Y + 2, at.Z + 1);
        bool blocked = sapi.World.GetEntitiesAround(new Vec3d(at.X + 1, at.Y + 1, at.Z), 4, 4, e => e.Alive && e.CollisionBox != null)
            .Any(e => box.IntersectsOrTouches(e.CollisionBox.ToDouble().Translate(e.Pos.X, e.Pos.Y, e.Pos.Z)));
        if (blocked)
        {
            posternCloseAtMs = now + 1000;
            return;
        }
        SetPostern(false);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/largedoor-close"), at.X + 1, at.Y + 1, at.Z + 0.5, null, true, 32, 1f);
    }

    // ================= Dev commands =================

    private void RegisterLinkCommands(ICoreServerAPI api)
    {
        var parsers = api.ChatCommands.Parsers;
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l73way")
                .WithDescription("Level 73 (dev test): where one of its ways leads, written down as a first trip would: gloom x z (a block of a Gloom in Level 9), dark mx mz (a cell of Level 6), out (the north door)")
                .WithArgs(parsers.Word("way"), parsers.OptionalInt("x"), parsers.OptionalInt("z"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnWayCommand)
            .EndSubCommand()
            .BeginSubCommand("l73rest")
                .WithDescription("Level 73 (dev test): counts a player as having slept a night under Coran's roof (default: you)")
                .WithArgs(parsers.OptionalWord("player"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(args => WithPlayer(args, p =>
                {
                    p.Entity.WatchedAttributes.SetDouble(SleptKey, RestHours);
                    p.Entity.WatchedAttributes.SetBool(RestedKey, true);
                    return TextCommandResult.Success($"{p.PlayerName} has slept a night under Coran's roof");
                }))
            .EndSubCommand()
            .BeginSubCommand("l73lead")
                .WithDescription("Level 73 (dev test): Coran leads a player in the level out to the north door, as if they had asked him (default: you)")
                .WithArgs(parsers.OptionalWord("player"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(args => WithPlayer(args, p =>
                {
                    if (!InLevel(p.Entity.Pos.X, p.Entity.Pos.Z)) return TextCommandResult.Error($"{p.PlayerName} is not in Level 73");
                    lastPlayerMs = sapi.World.ElapsedMilliseconds;
                    KeepCoran(true, lastPlayerMs);
                    if (Coran is not { } coran) return TextCommandResult.Error("Coran is not about (is the gate's ground loaded?)");
                    StartLead(coran, p);
                    return TextCommandResult.Success($"Coran leads {p.PlayerName} from {coran.Pos.X:0},{coran.Pos.Z:0} to the north door at {layout.L73Postern.X},{layout.L73Postern.Z}");
                }))
            .EndSubCommand()
            .BeginSubCommand("l73dummy")
                .WithDescription("Level 73 (dev test): puts a straw dummy down in the nearest Gloom (Level 9) or cell of Level 6's deepest dark to spawn, to be taken (the first try may only load the chunks: try again)")
                .WithArgs(parsers.Word("gloomOrDark"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnDummyCommand)
            .EndSubCommand()
            .BeginSubCommand("l73postern")
                .WithDescription("Level 73 (review shots): opens the north door (for its usual time) or shuts it")
                .WithArgs(parsers.Word("openOrShut"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(args =>
                {
                    if (sapi.World.BlockAccessor.GetChunkAtBlockPos(PosternPos(0, 0)) == null) return TextCommandResult.Error("The north door's ground is not loaded");
                    if ((string)args[0] == "open") OpenPostern(sapi.World.ElapsedMilliseconds);
                    else SetPostern(false);
                    return TextCommandResult.Success($"The north door is {(PosternOpen ? "open" : "shut")}");
                })
            .EndSubCommand();
    }

    private TextCommandResult OnDummyCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        string way = (string)args[0];
        int level = way == "gloom" ? 9 : 6;
        (double X, double Z)? at = null;
        if (way == "gloom" && layout.L73NearestGlooms(1) is { Count: > 0 } g) at = (g[0].X, g[0].Z);
        else if (way == "dark" && layout.L73LinkSpots(geometry).FirstOrDefault(s => s.Name == "deepest-dark") is { Name: not null } d) at = (d.X, d.Z);
        if (at is not { } p) return TextCommandResult.Error($"No {way} found");
        int x = (int)Math.Floor(p.X), z = (int)Math.Floor(p.Z), y = geometry.FloorFor(level) + 1;
        int cx = x / GlobalConstants.ChunkSize, cz = z / GlobalConstants.ChunkSize;
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
                sapi.WorldManager.LoadChunkColumn(cx + dx, cz + dz, true);
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, y, z) == null) return TextCommandResult.Error("The chunk is loading; try again in a moment");
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation("game:strawdummy"));
        if (type == null) return TextCommandResult.Error("No straw dummy entity type");
        Entity dummy = sapi.World.ClassRegistry.CreateEntity(type);
        dummy.Pos.SetPos(x + 0.5, y, z + 0.5);
        dummy.WatchedAttributes.SetBool(Senses.TestTargetKey, true);
        dummy.AlwaysActive = true;
        sapi.World.SpawnEntity(dummy);
        string line = $"l73dummy #{dummy.EntityId} in the {way} at {x},{y},{z} (level {level}; block there {sapi.World.BlockAccessor.GetBlock(new BlockPos(x, y, z)).Code}, under it {sapi.World.BlockAccessor.GetBlock(new BlockPos(x, y - 1, z)).Code})";
        sapi.Logger.Notification("[backrooms] " + line);
        return TextCommandResult.Success(line);
    }

    private TextCommandResult WithPlayer(TextCommandCallingArgs args, System.Func<IServerPlayer, TextCommandResult> act)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        string name = args.Parsers[0].IsMissing ? null : (string)args[0];
        IServerPlayer p = name == null ? args.Caller.Player as IServerPlayer
            : sapi.World.AllOnlinePlayers.OfType<IServerPlayer>().FirstOrDefault(o => string.Equals(o.PlayerName, name, StringComparison.OrdinalIgnoreCase));
        if (p?.Entity == null) return TextCommandResult.Error(name == null ? "Give a player's name" : $"No player {name} online");
        return act(p);
    }

    private TextCommandResult OnWayCommand(TextCommandCallingArgs args)
    {
        if (layout == null || Thresholds is not { } thresholds) return TextCommandResult.Error("This is not a Backrooms world");
        string way = (string)args[0];
        int x = args.Parsers[1].IsMissing ? 0 : (int)args[1], z = args.Parsers[2].IsMissing ? 0 : (int)args[2];
        Link? to = way == "out" ? thresholds.L73OutLink() : thresholds.L73WayLink(way, x, z);
        if (to is not { } l) return TextCommandResult.Error($"l73way {way} {x} {z}: leads nowhere (not a Gloom, not a dark cell, or no arrival found)");
        int lx = (int)Math.Floor(l.X), lz = (int)Math.Floor(l.Z);
        Tile t = layout.TileAt(lx, lz);
        string where = way == "gloom" ? $" (the Gloom's first tile {layout.L73GloomOrigin(x, z)})" : "";
        string line = $"l73way {way} {x} {z}{where} leads to {l.X:0.#},{l.Y:0.#},{l.Z:0.#}: level {t.Level}, zone {t.Zone}, floor {t.Floor}";
        sapi.Logger.Notification("[backrooms] " + line);
        return TextCommandResult.Success(line);
    }
}

/// <summary>Coran leading a wanderer out (L73System.Links.cs).</summary>
public partial class AiTaskL73Coran
{
    private bool leading;
    private long leadPathMs, leadWordMs;

    /// <summary>
    /// Leading someone to the north door: round the walls a step of the ring at a time (L73System.LeadWaypoint), stopping to
    /// wait when they fall behind; at the door he stands while he tears its chain off. False when he is leading no one.
    /// </summary>
    private bool Lead(L73System l73, long now)
    {
        EntityPlayer led = l73.LedPlayer;
        if (led == null && !l73.LeadOpening)
        {
            if (!leading) return false;
            // Done (or given up): he stands a while where he is, listening, then goes back to his round
            leading = false;
            pathTraverser.Stop();
            Move(null);
            goal = null;
            entity.AnimManager.StartAnimation("listen");
            idleUntilMs = now + 6000;
            return true;
        }
        if (!leading)
        {
            leading = true;
            pathTraverser.Stop();
            goal = null;
            idleUntilMs = 0;
            entity.AnimManager.StopAnimation("listen");
        }
        Vec3d front = l73.PosternFront;
        if (l73.LeadOpening || entity.Pos.HorDistanceTo(front) < 1.8)
        {
            pathTraverser.Stop();
            Move(null);
            entity.Pos.Yaw = entity.ServerPos.Yaw = GameMath.PI; // facing north, the door
            if (!l73.LeadOpening && led != null && led.Pos.HorDistanceTo(front) < LeadOpenBlocks) l73.CoranAtDoor(entity, now);
            else if (!l73.LeadOpening && led != null && now >= leadWordMs)
            {
                leadWordMs = now + 12_000;
                l73.LeadWait(entity);
            }
            return true;
        }
        if (entity.Pos.HorDistanceTo(led.Pos.XYZ) > L73System.LeadWaitBlocks && led.Pos.HorDistanceTo(front) > entity.Pos.HorDistanceTo(front))
        {
            // Fallen behind (not run on ahead to the door): he stops, turns to listen for them, and calls now and then
            pathTraverser.Stop();
            Move(null);
            TurnTo(led);
            if (now >= leadWordMs)
            {
                leadWordMs = now + 12_000;
                l73.LeadWait(entity);
            }
            return true;
        }
        // (At his running pace: whoever he leads can keep up with him at a jog, and the island is no place to stroll)
        Move("run");
        if (!pathTraverser.Active || now - leadPathMs > 1500)
        {
            leadPathMs = now;
            pathTraverser.WalkTowards(l73.LeadWaypoint(entity.Pos.XYZ), runSpeed, 1.2f, () => { }, () => { });
        }
        return true;
    }

    /// <summary>How close to the door the one he leads must be before he opens it.</summary>
    private const double LeadOpenBlocks = 8;
}
