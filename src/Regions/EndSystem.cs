using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Map;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// What The End does to you (kept as level 16; docs/new-levels/end-plan.md):
/// <list type="bullet">
/// <item>its computers: one use each, a buzz, THE END in white, static, dead for good; before it dies it shows you the
/// nearest ways out (marked on your map). One in four says "=)" instead, and you are taken to Level Fun;</item>
/// <item>the loop and the Turnaround: walking on along a long aisle loops you back 64 blocks to a stretch that looks the
/// same, and a bookcase is set across the aisle behind you (behind a flag, <c>/endloop on</c>: untested in a client);</item>
/// <item>distortions: once you have been here a while, now and then the floor shakes and for twelve seconds you are
/// somewhere else (the department's scene, shown by the client's fog and sound); walk into a wall then, and you are;</item>
/// <item>lights out round you now and then; the longer you stay, the more your stability drains (isolation);</item>
/// <item>shelves that come down at a touch; found books and the Hub's key in what you break; catalogue cards; Memory
/// Juice; the Junkies, who trade only with someone carrying Memory Juice.</item>
/// </list>
/// The client reads the distortion and lights-out state from the player's watched attributes (AtmosphereSystem.End.cs).
/// </summary>
public class EndSystem : ModSystem
{
    /// <summary>Watched attributes: when (calendar hours) a distortion ends and its scene (a level, or -1 the snow); when the lights come back.</summary>
    public const string DistortUntilKey = "backrooms:endDistortUntil", SceneKey = "backrooms:endScene", LightsOutKey = "backrooms:endLightsOutUntil";

    private const string SaveKey = "backrooms-end", LoopFlagKey = "backrooms-endloop";

    /// <summary>
    /// Whether walking on along a long aisle loops you back (the teleport) and sets the Turnaround's bookcase behind you.
    /// Off by default until it has been tried in a client: <c>/endloop on</c>.
    /// </summary>
    public static bool LoopEnabled;

    private ICoreServerAPI sapi;
    private WorldLayout layout;

    /// <summary>
    /// The level's layout, warm with its plans (server side, in a Backrooms world): the computers and catalogue cards look
    /// far round them, which a fresh layout would have to plan from nothing, on the main thread, every time.
    /// </summary>
    internal static WorldLayout SharedLayout(ICoreServerAPI sapi) =>
        sapi.ModLoader.GetModSystem<EndSystem>()?.layout ?? BackroomsWorld.CreateLayout(sapi.World);
    private WorldGeometry geometry;

    private sealed class Wanderer
    {
        public double EnteredHours = -1, NextDistortHours = -1, NextLightsOutHours = -1;
        public double LastX, LastZ;
        public int Pressing;
        public long LoopedAtMs;
    }

    private readonly Dictionary<string, Wanderer> wanderers = new();

    /// <summary>
    /// The blocks of the Turnaround's bookcases standing now. Saved, so that ones still standing when the server stopped
    /// are taken down after a restart too (once nobody is near them, like any other).
    /// </summary>
    private List<(int X, int Y, int Z)> turnarounds = new();

    private ICoreAPI api;
    private long tickId;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsEndTerminal", typeof(BlockBehaviorEndTerminal));
        api.RegisterBlockClass("BackroomsFragileShelf", typeof(BlockFragileShelf));
        api.RegisterItemClass("BackroomsCatalogueCard", typeof(ItemCatalogueCard));
        api.RegisterItemClass("BackroomsMemoryJuice", typeof(ItemMemoryJuice));
        this.api = api;
        api.Event.OnEntityLoaded += AttachJunkie;
        api.Event.OnEntitySpawn += AttachJunkie;
    }

    private void AttachJunkie(Entity entity) => Junkies.Attach(api, entity);

    public override void Dispose()
    {
        if (api != null)
        {
            api.Event.OnEntityLoaded -= AttachJunkie;
            api.Event.OnEntitySpawn -= AttachJunkie;
        }
        if (sapi != null)
        {
            if (tickId != 0) sapi.Event.UnregisterGameTickListener(tickId);
            sapi.Event.DidBreakBlock -= OnBrokenBlock;
            sapi.Event.GameWorldSave -= OnSave;
        }
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = new WorldGeometry(api.WorldManager.MapSizeY);
            LoopEnabled = api.WorldManager.SaveGame.GetData(LoopFlagKey) is { Length: > 0 } flag && flag[0] == 1;
            byte[] data = api.WorldManager.SaveGame.GetData(SaveKey);
            if (data != null && data.Length > 0)
            {
                try { turnarounds = SerializerUtil.Deserialize<List<int>>(data).Chunk(3).Select(c => (c[0], c[1], c[2])).ToList(); }
                catch (Exception e) { api.Logger.Warning("[backrooms] could not read The End's state: {0}", e.Message); }
            }
            tickId = api.Event.RegisterGameTickListener(OnTick, 250);
            api.Event.DidBreakBlock += OnBrokenBlock;
        });
        api.Event.GameWorldSave += OnSave;
        api.ChatCommands.Create("endloop")
            .WithDescription("The End: turn the looping long aisles (and the Turnaround) on or off. Untested in a client.")
            .RequiresPrivilege(Privilege.controlserver)
            .WithArgs(api.ChatCommands.Parsers.OptionalWord("onoff"))
            .HandleWith(args =>
            {
                string word = args[0] as string;
                if (word == "on") LoopEnabled = true;
                else if (word == "off") LoopEnabled = false;
                return TextCommandResult.Success($"The End's loop is {(LoopEnabled ? "on" : "off")}.");
            });
    }

    private void OnSave()
    {
        if (layout == null) return;
        var flat = new List<int>();
        foreach (var (x, y, z) in turnarounds) { flat.Add(x); flat.Add(y); flat.Add(z); }
        sapi.WorldManager.SaveGame.StoreData(SaveKey, SerializerUtil.Serialize(flat));
        sapi.WorldManager.SaveGame.StoreData(LoopFlagKey, new[] { (byte)(LoopEnabled ? 1 : 0) });
    }

    // ================= The tick =================

    private double HoursFor(double seconds) => seconds * sapi.World.Calendar.SpeedOfTime * sapi.World.Calendar.CalendarSpeedMul / 3600.0;

    private void OnTick(float dt)
    {
        if (layout == null) return;
        double now = sapi.World.Calendar.TotalHours;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity == null || !player.Entity.Alive) continue;
            if (player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
            EntityPos pos = player.Entity.Pos;
            int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
            bool here = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) == WorldLayout.TheEnd;
            if (!wanderers.TryGetValue(player.PlayerUID, out Wanderer w)) wanderers[player.PlayerUID] = w = new Wanderer { LastX = pos.X, LastZ = pos.Z };
            if (!here)
            {
                w.EnteredHours = -1;
                EndEffects(player);
                continue;
            }
            if (w.EnteredHours < 0)
            {
                w.EnteredHours = now;
                w.NextDistortHours = now + HoursFor(sapi.World.Rand.Next(20 * 60, 26 * 60));
                // The first lights-out waits a while, so that a first look round the store is in the light
                w.NextLightsOutHours = now + 3 + sapi.World.Rand.NextDouble();
            }
            double dx = pos.X - w.LastX, dz = pos.Z - w.LastZ;
            w.LastX = pos.X;
            w.LastZ = pos.Z;

            // (A player's walking into something is never seen as a collision on the server, whose physics only replays the
            // positions the client sends: pushing on without moving is how it shows)
            bool pushing = player.Entity.Controls.TriesToMove && Math.Abs(dx) + Math.Abs(dz) < 0.05;
            if (pushing) PushShelf(player);
            Isolation(player, now - w.EnteredHours, dt);
            Distortions(player, w, now, x, z, pushing);
            LightsOut(player, w, now);
            if (LoopEnabled) Loop(player, w, x, z, dx, dz);
        }
        ClearTurnarounds();
    }

    /// <summary>Someone pushing into a leaning shelf in front of them brings it down.</summary>
    private void PushShelf(IServerPlayer player)
    {
        EntityPos pos = player.Entity.Pos;
        double yaw = pos.Yaw;
        int fx = (int)Math.Floor(pos.X - Math.Sin(yaw) * 0.8), fz = (int)Math.Floor(pos.Z - Math.Cos(yaw) * 0.8), fy = (int)Math.Floor(pos.Y + 0.05);
        for (int dy = 0; dy <= 1; dy++)
        {
            var at = new BlockPos(fx, fy + dy, fz);
            if (sapi.World.BlockAccessor.GetBlock(at) is BlockFragileShelf)
            {
                BlockFragileShelf.Collapse(sapi.World, at, player.Entity);
                return;
            }
        }
    }

    private void EndEffects(IServerPlayer player)
    {
        var attrs = player.Entity.WatchedAttributes;
        if (attrs.GetDouble(DistortUntilKey, -1) > 0) attrs.SetDouble(DistortUntilKey, -1);
        if (attrs.GetDouble(LightsOutKey, -1) > 0) attrs.SetDouble(LightsOutKey, -1);
    }

    /// <summary>After two hours (in-game) in The End without leaving, stability drains a hundredth a minute, down to a quarter.</summary>
    private void Isolation(IServerPlayer player, double hoursIn, float dt)
    {
        if (hoursIn < 2) return;
        var attrs = player.Entity.WatchedAttributes;
        double stability = attrs.GetDouble("temporalStability", 1);
        if (stability <= 0.25) return;
        attrs.SetDouble("temporalStability", Math.Max(0.25, stability - 0.01 * dt / 60.0));
    }

    /// <summary>
    /// A distortion: the floor shakes and for twelve seconds you are somewhere else (the client shows it). Walk into a
    /// wall while it lasts (pressing against it for half a second) and you go through, into the place it showed.
    /// </summary>
    private void Distortions(IServerPlayer player, Wanderer w, double now, int x, int z, bool pushing)
    {
        var attrs = player.Entity.WatchedAttributes;
        double until = attrs.GetDouble(DistortUntilKey, -1);
        if (until < now && now >= w.NextDistortHours)
        {
            var (di, dj) = layout.EndDeptOf(x, z);
            attrs.SetInt(SceneKey, layout.EndDistortionScene(di, dj));
            attrs.SetDouble(DistortUntilKey, now + HoursFor(12));
            w.NextDistortHours = now + HoursFor(sapi.World.Rand.Next(8 * 60, 15 * 60));
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:enddistortion"), EnumChatType.Notification);
            sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/end/distortion"), player.Entity, null, randomizePitch: false, range: 16);
            return;
        }
        if (until < now)
        {
            w.Pressing = 0;
            return;
        }
        // Pressing into a wall or a shelf
        EntityPos pos = player.Entity.Pos;
        bool pressing = pushing;
        if (pressing)
        {
            double yaw = pos.Yaw;
            int fx = (int)Math.Floor(pos.X - Math.Sin(yaw) * 0.8), fz = (int)Math.Floor(pos.Z - Math.Cos(yaw) * 0.8);
            Tile ahead = layout.TileAt(fx, fz);
            pressing = ahead.IsWallLike || ahead.Kind == TileKind.Floor && ahead.Variant != 0 && !WorldLayout.IsWalkThroughProp(ahead.Variant);
        }
        w.Pressing = pressing ? w.Pressing + 1 : 0;
        if (w.Pressing < 2) return;
        w.Pressing = 0;
        var (ddi, ddj) = layout.EndDeptOf(x, z);
        var threshold = sapi.ModLoader.GetModSystem<ThresholdSystem>();
        Passage passage = threshold?.EndDistortion(ddi, ddj);
        if (passage == null) return;
        if (threshold.EndCarry(player, passage)) attrs.SetDouble(DistortUntilKey, -1);
    }

    /// <summary>Now and then the lights go out round you for a minute or two (an hour or two apart).</summary>
    private void LightsOut(IServerPlayer player, Wanderer w, double now)
    {
        if (now < w.NextLightsOutHours) return;
        var attrs = player.Entity.WatchedAttributes;
        attrs.SetDouble(LightsOutKey, now + HoursFor(sapi.World.Rand.Next(60, 120)));
        w.NextLightsOutHours = now + 1 + sapi.World.Rand.NextDouble();
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/end/breaker"), player.Entity, null, randomizePitch: false, range: 24);
    }

    // ================= The loop and the Turnaround =================

    /// <summary>
    /// Walking on along a long aisle's looping stretch, past three periods from its start, moves you back two periods
    /// (64 blocks) to a stretch that looks exactly the same; the Turnaround's bookcase goes up across the aisle five
    /// blocks behind you, out of sight. Only while nobody else is within 48 blocks.
    /// </summary>
    private void Loop(IServerPlayer player, Wanderer w, int x, int z, double dx, double dz)
    {
        if (sapi.World.ElapsedMilliseconds - w.LoopedAtMs < 3000) return;
        if (Math.Abs(dx) < 0.45 || Math.Abs(dz) > Math.Abs(dx) * 0.5) return; // walking (or running) along x
        if (!layout.EndLoopAt(x, z, out int along)) return;
        int shift;
        if (dx > 0 && along >= WorldLayout.EndLoopStart + 3 * WorldLayout.EndLoopPeriod - 8) shift = -2 * WorldLayout.EndLoopPeriod;
        else if (dx < 0 && along < WorldLayout.EndLoopStart + WorldLayout.EndLoopPeriod - 8) shift = 2 * WorldLayout.EndLoopPeriod;
        else return;
        EntityPos pos = player.Entity.Pos;
        foreach (IPlayer other in sapi.World.AllOnlinePlayers)
            if (other != player && other.Entity != null && other.Entity.Pos.SquareDistanceTo(pos.XYZ) < 48 * 48) return;
        if (!layout.EndLoopAt(x + shift, z, out _)) return;
        // (Never into a chunk that is not there: 64 blocks back along the way they came, it almost always is)
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x + shift, (int)Math.Floor(pos.Y), z) == null) return;
        w.LoopedAtMs = sapi.World.ElapsedMilliseconds;
        w.LastX = pos.X + shift;
        player.Entity.TeleportToDouble(pos.X + shift, pos.Y, pos.Z);
        PlaceTurnaround(x + shift - Math.Sign(dx) * 5, z, (int)Math.Floor(pos.Y), dx > 0 ? ArchPier.East : ArchPier.West);
    }

    /// <summary>A full-height bookcase across the aisle at x (on every aisle row round z), facing the way the player is walking.</summary>
    private void PlaceTurnaround(int x, int z, int y, ArchPier facing)
    {
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        int floor = geometry.FloorFor(WorldLayout.TheEnd);
        string side = facing == ArchPier.East ? "east" : "west";
        string[] parts = { "base", "mid1", "mid2", "crown" };
        for (int dz = -3; dz <= 3; dz++)
        {
            if (layout.TileAt(x, z + dz).Under != Unders.EndLoop) continue;
            for (int rel = 1; rel <= WorldLayout.EndAisleHeight - 1; rel++)
            {
                var pos = new BlockPos(x, floor + rel, z + dz);
                if (blocks.GetBlock(pos).BlockId != 0) continue;
                string code = rel <= 4 ? $"backrooms:end-tallshelf-empty-{parts[rel - 1]}-{side}" : "backrooms:end-wall-upper";
                Block block = sapi.World.GetBlock(new AssetLocation(code));
                if (block == null || block.BlockId == 0) continue;
                blocks.SetBlock(block.BlockId, pos);
                turnarounds.Add((pos.X, pos.Y, pos.Z));
            }
        }
    }

    /// <summary>Takes a Turnaround's bookcase down again once nobody is within 40 blocks of it.</summary>
    private void ClearTurnarounds()
    {
        if (turnarounds.Count == 0) return;
        for (int i = turnarounds.Count - 1; i >= 0; i--)
        {
            var (x, y, z) = turnarounds[i];
            bool near = false;
            foreach (IPlayer p in sapi.World.AllOnlinePlayers)
                if (p.Entity != null && p.Entity.Pos.SquareDistanceTo(x + 0.5, y, z + 0.5) < 40 * 40) { near = true; break; }
            if (near) continue;
            var pos = new BlockPos(x, y, z);
            if (sapi.World.BlockAccessor.GetChunkAtBlockPos(pos) == null) continue;
            Block there = sapi.World.BlockAccessor.GetBlock(pos);
            if (there.Code?.Domain == "backrooms" && there.Code.Path.StartsWith("end-")) sapi.World.BlockAccessor.SetBlock(0, pos);
            turnarounds.RemoveAt(i);
        }
    }

    // ================= What breaks =================

    private static readonly string[] BookColours = { "brickred", "cherryred", "darkbeige", "darkgray", "darkgreen", "darkolive", "gray", "olive", "orange", "orangebrown", "purple", "teal" };

    /// <summary>
    /// What The End's furniture gives besides its own drops: now and then a written book from a shelf that held books, a
    /// desk or a card catalogue; and from a desk or a catalogue, rarely, the Hub's key to The End.
    /// </summary>
    private void OnBrokenBlock(IServerPlayer byPlayer, int oldBlockId, BlockSelection blockSel)
    {
        if (layout == null || blockSel == null) return;
        BlockPos pos = blockSel.Position;
        if (layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z)) != WorldLayout.TheEnd) return;
        Block block = sapi.World.GetBlock(oldBlockId);
        string path = block?.Code?.Domain == "backrooms" ? block.Code.Path : null;
        if (path == null) return;
        bool shelfBooks = path.StartsWith("end-shelf-books") || path.StartsWith("end-tallshelf-books") || path.StartsWith("end-wallshelf-books");
        bool desk = path.StartsWith("end-desk"), catalogue = path.StartsWith("end-catalogue");
        if (!shelfBooks && !desk && !catalogue) return;
        // (Rolled by position, so the same place always gives the same. That cannot be farmed: none of these blocks drops
        // itself, so one cannot be put back where it stood and broken again outside creative mode)
        ulong h = Hashing.Hash((ulong)sapi.World.Seed, pos.X * 31 + pos.Y, pos.Z, 0x16F0);
        var at = new Vec3d(pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5);
        if (Hashing.Unit(h) < (shelfBooks ? 0.3 : 0.1)) sapi.World.SpawnItemEntity(FoundBook(Hashing.Mix(h)), at);
        // A service desk's own loot (end-plan.md): paper, ink and quill, Memory Juice (the Junkies' currency), a catalogue card
        if (desk)
        {
            void Find(string code, double chance, int salt)
            {
                if (Hashing.Unit(Hashing.Mix(h + (ulong)salt)) < chance && sapi.World.GetItem(new AssetLocation(code)) is { } item)
                    sapi.World.SpawnItemEntity(new ItemStack(item), at);
            }
            Find("game:paper-parchment", 0.30, 11);
            Find("game:inkandquill", 0.08, 12);
            Find("backrooms:end-memoryjuice", 0.15, 13);
            Find("backrooms:end-cataloguecard", 0.20, 14);
        }
        if ((desk || catalogue) && Hashing.Unit(Hashing.Mix(h + 1)) < 0.08)
        {
            Item key = sapi.World.GetItem(new AssetLocation("backrooms:hub-key-end"));
            if (key != null) HubSystem.KeyTurnedUp(sapi.World, byPlayer, new ItemStack(key), pos);
        }
    }

    /// <summary>A book someone left in The End, written in (one of twelve texts).</summary>
    private ItemStack FoundBook(ulong h)
    {
        var (title, text) = FoundBooks[(int)(h % (ulong)FoundBooks.Length)];
        Item item = sapi.World.GetItem(new AssetLocation("game:book-normal-" + BookColours[(int)((h >> 8) % (ulong)BookColours.Length)]));
        if (item == null) return null;
        var stack = new ItemStack(item);
        stack.Attributes.SetString("title", title);
        stack.Attributes.SetString("text", text);
        stack.Attributes.SetString("signedby", "?");
        return stack;
    }

    private static readonly (string Title, string Text)[] FoundBooks =
    {
        ("Distortions", "On the fifth, the lights flickered in a pattern I could not follow and the floor shook. For a few seconds there was no library. There was snow, and bare trees, and a silence even deeper than this one. Then the shelves came back.\n\nIt has happened four times since. Once it was the yellow rooms. Once it was water. I think if I had walked forward instead of standing still, I would have gone."),
        ("The Long Aisle", "There is an aisle here that does not end. I walked it for an hour. The same ladder, the same gap on the left, the same flickering tube, over and over.\n\nWhen I turned round there was a bookcase where I had just been. Solid. Full height.\n\nThe gaps at the side are the way out. Take them. Do not keep walking."),
        ("Visitor's Log", "Day 1. Found the exit. Big letters, THE END. I laughed.\nDay 2. Every desk has the same letters over it.\nDay 4. No food. The water coolers in the back rooms still work.\nDay 6. Most of the EXIT doors are locked. One opened. I came back for the others, like an idiot.\nDay 9. If you are reading this, the door by the cooler in the third stockroom from the middle opens."),
        ("THE END IS NEAR", "THE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS NEAR\nTHE END IS"),
        ("Catalogue: Section E", "EXIT (see also: EXIT). Filed under E. Cross-referenced to: Doors, Locked; Doors, Not Locked; Lobby, The; Office, The; Snow.\n\nThe cards are real. The drawers hold almost nothing else, but the cards point the right way. Somebody kept them up to date for a long time."),
        ("Which Doors Opened", "Locked, locked, locked, locked, opened (back hall, by the pallets: came out in a car park with EXIT signs), locked, locked, opened (corner of the big desk hall: concrete tunnels, a grey door behind me), locked.\n\nThe ones that open always open. The ones that don't never do. Write them down."),
        ("Juice", "They are in the room that looks like a living room. Six of them, then four. They will not talk to you unless you have juice. The little amber bottles, no label. You find them in the desk drawers.\n\nThey say it tastes like home. I tried one. It does. That is the problem."),
        ("Home", "There is a room out here that is my mother's front room. The lamp, the carpet, the television with nothing on it. I sat in it for a day.\n\nIt is not her room. It is The End wearing it. When I walked out of the far side, the shelves came back, and they were empty, like always."),
        ("Don't Turn It On", "The computers buzz until you turn them on. Then they show the name of this place, and die, and never come back.\n\nBut before it died, mine showed me a plan of the floor. I remembered where the doors were.\n\nThe one by the reading room did not say THE END. It said =)\nThe man who turned it on is not here any more."),
        ("=)", "Why would you want to leave? Everything is quiet here. Nothing hurts. Nobody needs anything from you.\n\nThere is a party, though, if you get bored. You only have to turn on the right screen.\n\nWe will be so happy to see you. =)"),
        ("Shelf 4,812", "I have been counting shelves. 4,812 so far. Books on 127 of them. Most of the books are blank. I write in the blank ones, so there will be something to read for the next one.\n\nHello, next one."),
        ("Isolation", "You stop hearing your own footsteps after a while. Then you start hearing them again, a little after you stop walking.\n\nDo not turn round when that happens. Keep to the middle, under the big letters. It is easier to think there."),
    };
}

/// <summary>
/// One of The End's computers: right-click to turn it on. It buzzes, shows THE END in white, turns to static, and is
/// dead for good. Before it dies it marks on your map the nearest ways out of The End that open (up to three). One in
/// four (never the central hall's) says "=)" instead, and whoever turned it on is taken to Level Fun.
/// </summary>
public class BlockBehaviorEndTerminal : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorEndTerminal(Block block) : base(block) { }

    // (Asked every frame the block is looked at: the help is made once)
    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling) =>
        block.Variant["state"] != "off" ? Array.Empty<WorldInteraction>() :
            (help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-endterminal", MouseButton = EnumMouseButton.Right } });

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Api is not ICoreServerAPI sapi || byPlayer is not IServerPlayer player) return true;
        BlockPos pos = blockSel.Position.Copy();
        if (block.Variant["state"] != "off")
        {
            if (block.Variant["state"] == "dead") player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:endterminal-dead"), EnumChatType.Notification);
            return true;
        }
        var layout = EndSystem.SharedLayout(sapi);
        Tile under = layout.TileAt(pos.X, pos.Z);
        bool central = under.Variant == Worldgen.Props.EndDesk && (under.Stack & 16) != 0;
        var threshold = sapi.ModLoader.GetModSystem<ThresholdSystem>();
        Passage party = threshold?.EndTerminal(pos.X, pos.Z, central);
        // (Level 3999's TRUEEND.EXE has a screen of its own, and says so, instead of "=)")
        bool trueEnd = party?.Message == "backrooms:l3999-arrive-lobby";
        if (trueEnd) SwapTo(sapi, pos, "l3999-trueendterminal-" + block.Variant["side"]);
        else Swap(sapi, pos, party != null ? "party" : "on");
        world.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/end/crton"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, false, 16);
        string said = party == null ? "backrooms:endterminal-on" : trueEnd ? "backrooms:l3999-trueend" : "backrooms:endterminal-party";
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(said), EnumChatType.Notification);
        sapi.ModLoader.GetModSystem<MenaceSystem>()?.MakeNoise(player.Entity, 0.2);
        if (party != null)
        {
            sapi.Event.RegisterCallback(_ =>
            {
                threshold.EndCarry(player, party);
                if (trueEnd) SwapTo(sapi, pos, block.CodeWithVariant("state", "dead").Path);
                else Swap(sapi, pos, "dead");
            }, 3000);
            return true;
        }
        // Before it dies, it shows the floor plan: the nearest ways out that open
        var exits = layout.EndExitsNear(pos.X, pos.Z, 400, (x, z) => threshold?.EndExitOpens(x, z) ?? true, 3);
        foreach (var (x, z) in exits)
            MapMarks.Add(sapi, player, new Vec3d(x + 0.5, pos.Y, z + 0.5), Lang.Get("backrooms:waypoint-endterminal"), "star1", MapMarks.NoteColor, 4);
        if (exits.Count > 0) player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:endterminal-marked"), EnumChatType.Notification);
        sapi.Event.RegisterCallback(_ =>
        {
            Swap(sapi, pos, "static");
            world.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/end/crtstatic"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, false, 16);
            sapi.Event.RegisterCallback(_ => Swap(sapi, pos, "dead"), 2500);
        }, 3000);
        return true;
    }

    /// <summary>Puts the computer at a position (The End's, or Level 3999's TRUEEND.EXE screen) into the block of the given code.</summary>
    private static void SwapTo(ICoreServerAPI sapi, BlockPos pos, string path)
    {
        string here = sapi.World.BlockAccessor.GetBlock(pos).Code?.Path;
        if (here == null || !(here.StartsWith("end-terminal-") || here.StartsWith("l3999-trueendterminal-"))) return;
        Block next = sapi.World.GetBlock(new AssetLocation("backrooms", path));
        if (next != null && next.BlockId != 0) sapi.World.BlockAccessor.ExchangeBlock(next.BlockId, pos);
    }

    /// <summary>Puts The End's computer at a position into another state (on, static, party, dead), keeping its facing.</summary>
    private static void Swap(ICoreServerAPI sapi, BlockPos pos, string state)
    {
        Block here = sapi.World.BlockAccessor.GetBlock(pos);
        if (here.Code?.Path.StartsWith("end-terminal-") != true) return;
        Block next = sapi.World.GetBlock(here.CodeWithVariant("state", state));
        if (next != null && next.BlockId != 0) sapi.World.BlockAccessor.ExchangeBlock(next.BlockId, pos);
    }
}

/// <summary>Shelving that leans (a block class): it comes down the moment anyone walks into it or strikes it, with a crash that carries.</summary>
public class BlockFragileShelf : Block
{
    public override void OnEntityCollide(IWorldAccessor world, Entity entity, BlockPos pos, BlockFacing facing, Vec3d collideSpeed, bool isImpact)
    {
        base.OnEntityCollide(world, entity, pos, facing, collideSpeed, isImpact);
        if (world.Side != EnumAppSide.Server || entity is not EntityPlayer) return;
        Collapse(world, pos, entity);
    }

    public override void OnBlockBroken(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1)
    {
        base.OnBlockBroken(world, pos, byPlayer, dropQuantityMultiplier);
        if (world.Side == EnumAppSide.Server) Collapse(world, pos, byPlayer?.Entity);
    }

    internal static void Collapse(IWorldAccessor world, BlockPos pos, Entity by)
    {
        // Both halves of the shelf come down
        bool fell = false;
        for (int dy = -1; dy <= 1; dy++)
        {
            BlockPos p = pos.AddCopy(0, dy, 0);
            Block b = world.BlockAccessor.GetBlock(p);
            if (b.Code?.Path.StartsWith("end-shelf-leaning") == true) { world.BlockAccessor.BreakBlock(p, null); fell = true; }
        }
        if (!fell && by is EntityPlayer) return;
        world.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/end/shelfcrash"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 32);
        if (by != null) world.Api.ModLoader.GetModSystem<MenaceSystem>()?.MakeNoise(by, 0.3);
    }
}

/// <summary>A card from The End's card catalogue: read it, and the nearest way out of The End is marked on your map.</summary>
public class ItemCatalogueCard : Item
{
    public override void OnHeldInteractStart(ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel, bool firstEvent, ref EnumHandHandling handling)
    {
        if (!firstEvent) return;
        handling = EnumHandHandling.PreventDefault;
        if (api.Side != EnumAppSide.Server || (byEntity as EntityPlayer)?.Player is not IServerPlayer player || api is not ICoreServerAPI sapi) return;
        var layout = EndSystem.SharedLayout(sapi);
        EntityPos pos = byEntity.Pos;
        int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
        var threshold = sapi.ModLoader.GetModSystem<ThresholdSystem>();
        var exits = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) == WorldLayout.TheEnd
            ? layout.EndExitsNear(x, z, 600, (ex, ez) => threshold?.EndExitOpens(ex, ez) ?? true, 1) : new List<(int X, int Z)>();
        if (exits.Count == 0)
        {
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:note-nothing"), EnumChatType.Notification);
            return;
        }
        var (ax, az) = exits[0];
        double dx = ax + 0.5 - pos.X, dz = az + 0.5 - pos.Z;
        string direction = L3999System.Direction(dx, dz);
        double d = Math.Sqrt(dx * dx + dz * dz);
        int step = d < 60 ? 10 : d < 300 ? 25 : 50, paces = Math.Max(step, (int)Math.Round(d / step) * step);
        int variant = (int)(Hashing.Hash((ulong)api.World.Seed, ax, az, 0x16F1) % 3) + 1;
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get($"backrooms:note-endexit-{variant}", direction, paces), EnumChatType.Notification);
        MapMarks.Add(sapi, player, new Vec3d(ax + 0.5, pos.Y, az + 0.5), Lang.Get("backrooms:waypoint-note-endexit"), "star1", MapMarks.NoteColor, 4);
        byEntity.World.PlaySoundAt(new AssetLocation("game:sounds/effect/writing"), byEntity, null, randomizePitch: true, range: 8);
        slot.TakeOut(1);
        slot.MarkDirty();
    }
}

/// <summary>Memory Juice: an unlabelled amber bottle from The End's desks. It steadies you a little (+0.2 stability), and tastes like home.</summary>
public class ItemMemoryJuice : Item
{
    protected override void tryEatStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity)
    {
        int before = slot.StackSize;
        base.tryEatStop(secondsUsed, slot, byEntity);
        if (byEntity.World.Side != EnumAppSide.Server || slot.StackSize >= before) return;
        double stability = byEntity.WatchedAttributes.GetDouble("temporalStability", 1);
        byEntity.WatchedAttributes.SetDouble("temporalStability", Math.Min(1, stability + 0.2));
        byEntity.WatchedAttributes.SetDouble("backrooms:memoryUntil", byEntity.World.Calendar.TotalHours + 0.25);
    }
}

/// <summary>
/// The Junkies of The End (Wikidot's Level 601): the wanderers who keep to its Home fake realities. They trade only with
/// someone who carries Memory Juice; anyone else gets a word and nothing more.
/// </summary>
public static class Junkies
{
    public const string JuiceCode = "end-memoryjuice";

    /// <summary>Gives a wanderer standing in The End the Junkies' rule (on both sides, so the trade dialog never opens without juice).</summary>
    public static void Attach(ICoreAPI api, Entity entity)
    {
        if (entity?.Code?.Domain != "backrooms" || !entity.Code.Path.StartsWith("wanderer")) return;
        if (api.World is not IWorldAccessor world || world.Config == null) return;
        WorldLayout layout;
        try { layout = BackroomsWorld.CreateLayout(world); }
        catch { return; }
        if (layout == null) return;
        int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
        if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.TheEnd) return;
        if (entity.GetBehavior<EntityBehaviorJunkie>() != null) return;
        entity.SidedProperties?.Behaviors.Insert(0, new EntityBehaviorJunkie(entity));
    }

    public static bool CarriesJuice(IPlayer player)
    {
        if (player?.InventoryManager == null) return false;
        foreach (IInventory inv in player.InventoryManager.Inventories.Values)
        {
            if (inv == null || inv.ClassName == "creative") continue;
            foreach (ItemSlot slot in inv)
                if (slot?.Itemstack?.Collectible?.Code is { } code && code.Domain == "backrooms" && code.Path == JuiceCode) return true;
        }
        return false;
    }
}

/// <summary>A Junkie's rule: no juice, no trade.</summary>
public class EntityBehaviorJunkie : EntityBehavior
{
    public EntityBehaviorJunkie(Entity entity) : base(entity) { }

    public override string PropertyName() => "backrooms-junkie";

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode, ref EnumHandling handled)
    {
        if (mode != EnumInteractMode.Interact || byEntity is not EntityPlayer ep) return;
        bool juice = Junkies.CarriesJuice(ep.Player);
        if (entity.World.Side == EnumAppSide.Server && ep.Player is IServerPlayer sp)
            sp.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(juice ? "backrooms:endjunkie-greet" : "backrooms:endjunkie-nojuice"), EnumChatType.Notification);
        if (!juice) handled = EnumHandling.PreventSubsequent;
    }
}
