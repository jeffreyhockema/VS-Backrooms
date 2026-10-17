using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Backrooms.Map;
using Backrooms.Worldgen;
using ProtoBuf;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;

namespace Backrooms.Notes;

[ProtoContract]
public class NoteLogPacket
{
    [ProtoMember(1)] public string Json;
}

[ProtoContract]
public class ShowNotePacket
{
    /// <summary>Which read to show: its <see cref="NoteRead.Id"/>.</summary>
    [ProtoMember(1)] public int Id;
}

[ProtoContract]
public class MarkAgainPacket
{
    /// <summary>The read (its <see cref="NoteRead.Id"/>) and which of its marks.</summary>
    [ProtoMember(1)] public int Id;
    [ProtoMember(2)] public int Mark;
}

/// <summary>
/// Wanderers' notes and the journal (docs/design/notes-plan.md). A note is blank until read; reading it on the server resolves
/// it to the next entry in that player's sequence (<see cref="NoteSequencer"/>, from config/notes.json written by
/// tools/gen_notes.py), marks what its paper and its entry point at (<see cref="MarkResolver"/>), and keeps it in the
/// player's journal: a log per player in the save game, sent to them on joining and after every read, and shown on J.
/// The note itself is kept and remembers who has read it (<see cref="ItemWandererNote"/>), so it can be handed on:
/// one paper gives each player one read. Also: the note in a new player's pocket, extra and folded notes from what is
/// broken (by level, dens, locked rooms and the far edges), and notes left lying where a story puts one.
/// </summary>
public partial class NoteSystem : ModSystem
{
    public const string Channel = "backrooms-notes", SaveKey = "backrooms-notes", VisitedKey = "backrooms:visitedLevels";

    /// <summary>A folded note's marks: a warmer gold than the ordinary notes' paper yellow.</summary>
    public static readonly int RareColor = ColorUtil.ColorFromRgba(240, 186, 90, 255);

    private ICoreAPI api;
    private ICoreServerAPI sapi;
    private IServerNetworkChannel serverChannel;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private MarkResolver marks;
    // The slow part of finding a note's marks runs on a worker, on a layout of its own (one search at a time)
    private MarkResolver workerMarks;
    private readonly object workerLock = new();
    private Dictionary<string, NoteLog> logs = new();
    private bool dirty;

    /// <summary>The tracks and entries (both sides; null outside a Backrooms world or if the file is missing).</summary>
    public NoteCatalog Catalog { get; private set; }

    public override void Start(ICoreAPI api)
    {
        this.api = api;
        api.RegisterBlockClass("BackroomsLooseNote", typeof(BlockLooseNote));
        api.Network.RegisterChannel(Channel).RegisterMessageType<NoteLogPacket>().RegisterMessageType<ShowNotePacket>().RegisterMessageType<MarkAgainPacket>();
    }

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.25;

    private void LoadCatalog()
    {
        try
        {
            IAsset asset = api.Assets.TryGet(new AssetLocation("backrooms", "config/notes.json"));
            if (asset != null) Catalog = NoteCatalog.Parse(asset.ToText());
        }
        catch (Exception ex)
        {
            api.Logger.Error("[backrooms] could not read config/notes.json: {0}", ex);
        }
    }

    // ================= Server =================

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        serverChannel = api.Network.GetChannel(Channel);
        serverChannel.SetMessageHandler<MarkAgainPacket>(OnMarkAgain);
        LoadCatalog();
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode || Catalog == null) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            marks = new MarkResolver(api, layout, geometry);
            workerMarks = new MarkResolver(api, BackroomsWorld.CreateLayout(api.World), geometry);
            Load();
            api.Event.GameWorldSave += Save;
            api.Event.PlayerNowPlaying += OnPlayerNowPlaying;
            StartSources(api);
            api.Logger.Notification("[backrooms] notes: {0} entries in {1} tracks, journals for {2} players", Catalog.ByKey.Count, Catalog.Tracks.Count, logs.Count);
        });
        RegisterCommands(api);
    }

    public override void Dispose()
    {
        // (A search still on the worker finds layout gone and gives up: see ApplyMarks)
        layout = null;
        marks = null;
        DisposeClient();
    }

    private void Load()
    {
        try
        {
            byte[] data = sapi.WorldManager.SaveGame.GetData(SaveKey);
            logs = data == null ? new() : NoteLog.LoadAll(Encoding.UTF8.GetString(data));
            // (A hand-edited or damaged save may hold an empty entry: it would be handed out as a null log)
            foreach (string uid in logs.Where(p => p.Value == null).Select(p => p.Key).ToList()) logs.Remove(uid);
        }
        catch (Exception ex)
        {
            sapi.Logger.Error("[backrooms] could not read the notes save data; starting afresh: {0}", ex);
            logs = new();
        }
        LoadSpots();
    }

    private void Save()
    {
        if (dirty)
        {
            sapi.WorldManager.SaveGame.StoreData(SaveKey, Encoding.UTF8.GetBytes(NoteLog.SaveAll(logs)));
            dirty = false;
        }
        SaveSpots();
    }

    /// <summary>A player's log (created empty the first time).</summary>
    public NoteLog LogOf(string uid)
    {
        if (!logs.TryGetValue(uid, out NoteLog log)) logs[uid] = log = new NoteLog();
        return log;
    }

    private void SendLog(IServerPlayer player)
    {
        if (logs.TryGetValue(player.PlayerUID, out NoteLog log)) serverChannel.SendPacket(new NoteLogPacket { Json = log.ToJson() }, player);
    }

    private void OnPlayerNowPlaying(IServerPlayer player)
    {
        NoteLog log = LogOf(player.PlayerUID);
        MarkVisited(player.Entity);
        // A new player finds a note in their pocket (not someone who has been about before the notes were sequenced)
        int bits = player.Entity.WatchedAttributes.GetInt(VisitedKey);
        if (!log.PocketGiven && log.Read.Count == 0 && (bits & ~1) == 0 && sapi.World.GetItem(new AssetLocation("backrooms", "wanderernote-cache")) is Item note)
        {
            // (With no room in their pockets, it is at their feet)
            if (GiveOrDrop(player, new ItemStack(note)))
                player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:note-pocket-given"), EnumChatType.Notification);
        }
        if (!log.PocketGiven) { log.PocketGiven = true; dirty = true; }
        // Directions notes that told of nothing, read just before they left: theirs to read again (see ApplyMarks)
        if (log.Owed is { Count: > 0 } owed)
        {
            log.Owed = null;
            dirty = true;
            foreach (string kind in owed) HandBack(player, kind);
        }
        SendLog(player);
    }

    /// <summary>Puts a stack in a player's inventory, or at their feet if there is no room; true if it went in.</summary>
    private bool GiveOrDrop(IServerPlayer player, ItemStack stack)
    {
        if (player.InventoryManager.TryGiveItemstack(stack, true)) return true;
        sapi.World.SpawnItemEntity(stack, player.Entity.Pos.XYZ);
        return false;
    }

    /// <summary>The item a note of a kind is (door, way, cache, refuge; folded; altered, Level Fun's).</summary>
    public static string NoteItemCode(string kind) => kind switch
    {
        "folded" => "wanderernote-folded",
        "altered" => "fun-wanderernote-altered",
        _ => "wanderernote-" + kind,
    };

    // ================= Where a player has been =================

    /// <summary>The level a note read here counts as: its id, but 61 for a Snackrooms cell (Level 6.1).</summary>
    public int LevelKey(double x, double z, out int level)
    {
        int mx = WorldLayout.MacroOf((int)Math.Floor(x)), mz = WorldLayout.MacroOf((int)Math.Floor(z));
        level = layout.LevelAt(mx, mz);
        return level == 6 && layout.IsSnackrooms(mx, mz) ? NoteCatalog.SnackroomsKey : level;
    }

    /// <summary>Records the level a player is in (the same bits the Hub's Keymaster reads).</summary>
    private void MarkVisited(EntityPlayer entity)
    {
        if (entity == null || layout == null) return;
        LevelKey(entity.Pos.X, entity.Pos.Z, out int level);
        if (level >= 31) return;
        int bits = entity.WatchedAttributes.GetInt(VisitedKey);
        if ((bits & (1 << level)) == 0) entity.WatchedAttributes.SetInt(VisitedKey, bits | (1 << level));
    }

    /// <summary>Whether a player has been to a level (a gate's level: the 6.1 key counts as Level 6, which holds it).</summary>
    private static bool HasVisited(EntityPlayer entity, int level)
    {
        if (level == NoteCatalog.SnackroomsKey) level = 6;
        return level is >= 0 and < 31 && (entity.WatchedAttributes.GetInt(VisitedKey) & (1 << level)) != 0;
    }

    // ================= Reading =================

    /// <summary>
    /// A note read from the hand (<see cref="ItemWandererNote"/>). The note is kept, marked as read by this player, so
    /// one paper gives each player one read and can be handed on; read again by them, it only says so. From a bundle,
    /// the one read is split off (the rest stay fresh and stacked) and goes back in their pockets.
    /// </summary>
    public void ReadHeld(IServerPlayer player, ItemSlot slot)
    {
        if (slot?.Itemstack?.Collectible is not ItemWandererNote note) return;
        string uid = player.PlayerUID;
        if (ItemWandererNote.ReadBy(slot.Itemstack, uid))
        {
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:note-read-already"), EnumChatType.Notification);
            return;
        }
        if (!Read(player, note.Kind)) return;
        ItemStack one = slot.StackSize > 1 ? slot.TakeOut(1) : slot.Itemstack;
        ItemWandererNote.MarkRead(one, uid);
        slot.MarkDirty();
        if (one != slot.Itemstack) GiveOrDrop(player, one);
    }

    /// <summary>
    /// A directions note that told its reader nothing is theirs to read elsewhere: the note they read, or any note of
    /// the kind they have read (the papers being alike), forgets them; failing that (dropped, put away, lost with them),
    /// a fresh one is given.
    /// </summary>
    private void HandBack(IServerPlayer player, string kind)
    {
        string uid = player.PlayerUID;
        foreach (IInventory inventory in player.InventoryManager.Inventories.Values)
        {
            if (inventory == null || inventory.ClassName is "creative" or "ground") continue;
            foreach (ItemSlot slot in inventory)
            {
                if (slot?.Itemstack?.Collectible is not ItemWandererNote note || note.Kind != kind || !ItemWandererNote.ReadBy(slot.Itemstack, uid)) continue;
                ItemStack one = slot.StackSize > 1 ? slot.TakeOut(1) : slot.Itemstack;
                ItemWandererNote.Unread(one, uid);
                slot.MarkDirty();
                if (one != slot.Itemstack) GiveOrDrop(player, one);
                return;
            }
        }
        if (sapi.World.GetItem(new AssetLocation("backrooms", NoteItemCode(kind))) is Item item) GiveOrDrop(player, new ItemStack(item));
    }

    /// <summary>
    /// Reads a note of a kind (door, way, cache, refuge; folded for a rare note; altered for Level Fun's) where the player
    /// stands. What it says is known at once (it goes in the journal and is shown); what it marks is searched for on a
    /// worker and added a moment later (<see cref="FindMarks"/>). A note that only gives directions waits for its marks,
    /// and is handed back if it told nothing. Returns false only where notes are not running.
    /// </summary>
    public bool Read(IServerPlayer player, string kind)
    {
        if (layout == null || Catalog == null || player?.Entity == null) return false;
        EntityPos pos = player.Entity.Pos;
        MarkVisited(player.Entity);
        NoteResolution res = ResolveAt(player.PlayerUID, pos.X, pos.Z, kind, l => HasVisited(player.Entity, l), out NoteLog log, out int key, out int level);
        var request = new MarkRequest
        {
            Uid = player.PlayerUID, Kind = kind, X = pos.X, Y = geometry.FloorFor(level) + 1, Z = pos.Z, Level = level, Key = key,
            EntryMark = res?.Entry.Mark, Hours = sapi.World.Calendar.TotalHours, Taken = TakenOf(log),
        };
        if (res != null)
        {
            var read = new NoteRead
            {
                Key = res.Entry.Key, Track = res.Track.Id, Level = key, X = (int)Math.Floor(pos.X), Z = (int)Math.Floor(pos.Z),
                Hours = request.Hours, Kind = kind,
            };
            log.Add(read, res.Pick);
            dirty = true;
            request.ReadId = read.Id;
            SendLog(player);
            serverChannel.SendPacket(new ShowNotePacket { Id = read.Id }, player);
            sapi.SendIngameDiscovery(player, "backrooms-note", Banner(log, res));
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/writing"), player.Entity, null, true, 8);
        }
        FindMarks(request);
        return true;
    }

    /// <summary>A note read whose marks are still being searched for.</summary>
    private sealed class MarkRequest
    {
        public string Uid, Kind, EntryMark;
        public double X, Y, Z, Hours;
        public int Level, Key;
        /// <summary>The read in the player's log the marks belong to; 0 for a directions note (recorded once its marks are found).</summary>
        public int ReadId;
        /// <summary>Everything the reader's notes have marked before (a snapshot, so the worker reads nothing shared).</summary>
        public List<(int X, int Z)> Taken;
    }

    /// <summary>Two places this close are the same place: another doorway of the same gate, another box of the same stash.</summary>
    private const int SamePlace = 12;

    /// <summary>Everything a log's notes have marked so far.</summary>
    private static List<(int X, int Z)> TakenOf(NoteLog log)
    {
        var taken = new List<(int X, int Z)>();
        foreach (NoteRead r in log.Read) foreach (NoteMark m in r.Marks) taken.Add((m.X, m.Z));
        foreach (NoteRead r in log.Directions) foreach (NoteMark m in r.Marks) taken.Add((m.X, m.Z));
        return taken;
    }

    /// <summary>
    /// A search's skip: places already marked for this reader (null when there are none). A note never points at a place
    /// the reader's earlier notes marked while there is another to point at; failing that, the nearest is named again.
    /// </summary>
    private static System.Func<int, int, bool> SkipOf(List<(int X, int Z)> taken)
    {
        if (taken == null || taken.Count == 0) return null;
        return (x, z) =>
        {
            foreach (var (tx, tz) in taken)
                if ((tx - x) * (tx - x) + (tz - z) * (tz - z) <= SamePlace * SamePlace) return true;
            return false;
        };
    }

    /// <summary>One search of a note: its kind of mark, and how far.</summary>
    private sealed class MarkSlot
    {
        public string Kind;
        public bool Far;
        public NoteMark Found;
        public MarkDefer Defer;
    }

    /// <summary>The searches a note makes, in order: the paper's own mark, then the entry's (a folded note with none marks an unopened cache, from twice as far).</summary>
    private static List<MarkSlot> SlotsFor(string kind, string entryMark)
    {
        bool rare = kind == "folded";
        var slots = new List<MarkSlot>();
        if (kind is "door" or "way" or "cache" or "refuge") slots.Add(new MarkSlot { Kind = kind });
        if (entryMark != null) slots.Add(new MarkSlot { Kind = entryMark, Far = rare });
        else if (rare) slots.Add(new MarkSlot { Kind = "cache", Far = true });
        return slots;
    }

    /// <summary>At most two marks, never two of the same place.</summary>
    private static List<NoteMark> Gather(List<MarkSlot> slots)
    {
        var found = new List<NoteMark>();
        foreach (MarkSlot slot in slots)
        {
            NoteMark m = slot.Found;
            if (m == null || found.Count >= 2) continue;
            if (found.Any(f => (f.X - m.X) * (f.X - m.X) + (f.Z - m.Z) * (f.Z - m.Z) <= SamePlace * SamePlace)) continue;
            found.Add(m);
        }
        return found;
    }

    /// <summary>
    /// Searches the layout for a note's marks on a worker thread (a second at worst, in Level 94), then finishes on the main
    /// thread: whatever needs the loaded world, and handing the marks to the player and their journal.
    /// </summary>
    private void FindMarks(MarkRequest request)
    {
        List<MarkSlot> slots = SlotsFor(request.Kind, request.EntryMark);
        if (slots.Count == 0)
        {
            ApplyMarks(request, slots);
            return;
        }
        MarkResolver resolver = workerMarks;
        ICoreServerAPI api = sapi;
        System.Func<int, int, bool> skip = SkipOf(request.Taken);
        Task.Run(() =>
        {
            try
            {
                lock (workerLock)
                    foreach (MarkSlot slot in slots)
                        slot.Found = resolver.Resolve(slot.Kind, request.X, request.Y, request.Z, request.Level, slot.Far, MarkSearch.Layout, out slot.Defer, skip);
            }
            catch (Exception ex)
            {
                api.Logger.Error("[backrooms] a note's marks could not be searched for: {0}", ex);
                foreach (MarkSlot slot in slots) { slot.Found = null; slot.Defer = MarkDefer.Full; }
            }
            api.Event.EnqueueMainThreadTask(() => ApplyMarks(request, slots), "backrooms-notemarks");
        });
    }

    /// <summary>On the main thread: the world's part of the search, then the marks go on the map, in the journal and in chat.</summary>
    private void ApplyMarks(MarkRequest request, List<MarkSlot> slots)
    {
        if (layout == null || marks == null) return; // (the world is closing)
        System.Func<int, int, bool> skip = SkipOf(request.Taken);
        foreach (MarkSlot slot in slots)
            if (slot.Found == null && slot.Defer != MarkDefer.None)
                slot.Found = marks.Resolve(slot.Kind, request.X, request.Y, request.Z, request.Level, slot.Far,
                    slot.Defer == MarkDefer.World ? MarkSearch.World : MarkSearch.Full, out _, skip);
        // Nowhere new to point at: the nearest place is named again rather than nothing
        if (skip != null)
            foreach (MarkSlot slot in slots)
                if (slot.Found == null) slot.Found = marks.Resolve(slot.Kind, request.X, request.Y, request.Z, request.Level, slot.Far);
        List<NoteMark> found = Gather(slots);
        NoteLog log = LogOf(request.Uid);
        var player = sapi.World.PlayerByUid(request.Uid) as IServerPlayer;
        bool online = player?.Entity != null && player.ConnectionState == EnumClientState.Playing;
        bool rare = request.Kind == "folded";
        NoteRead read;
        if (request.ReadId > 0)
        {
            // (Gone if the journal was reset meanwhile)
            read = log.Find(request.ReadId);
            if (read == null || found.Count == 0) return;
            read.Marks.AddRange(found);
            dirty = true;
        }
        else
        {
            if (found.Count == 0)
            {
                // A directions note that tells of nothing here: theirs to read again somewhere else (gone meanwhile,
                // they are owed it: handed back when they next join, see OnPlayerNowPlaying)
                if (!online)
                {
                    (log.Owed ??= new()).Add(request.Kind);
                    dirty = true;
                    return;
                }
                player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:note-nothing"), EnumChatType.Notification);
                HandBack(player, request.Kind);
                return;
            }
            read = new NoteRead
            {
                Track = "dir", Level = request.Key, X = (int)Math.Floor(request.X), Z = (int)Math.Floor(request.Z), Hours = request.Hours,
                Kind = request.Kind, Marks = found,
            };
            log.Add(read, null);
            dirty = true;
        }
        if (!online) return; // (the marks are in their journal, to mark again)
        // (The note's own words give the way, so a world without waypoints needs no more telling)
        foreach (NoteMark m in found)
            MapMarks.Add(sapi, player, new Vec3d(m.X + 0.5, player.Entity.Pos.Y, m.Z + 0.5), m.Title, m.Icon, rare ? RareColor : MapMarks.NoteColor, 4, tell: false);
        SendLog(player);
        foreach (NoteMark m in found)
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(m.Ps, Lang.Get("backrooms:dir-" + m.Dir), m.Paces), EnumChatType.Notification);
        // ("Marked: ...", now that the marks are on the map, a moment after the note itself)
        if (request.ReadId > 0)
        {
            if (MapSetting.Waypoints(sapi.World.Config))
                foreach (NoteMark m in found) player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:journal-marked", m.Title), EnumChatType.Notification);
        }
        else
        {
            serverChannel.SendPacket(new ShowNotePacket { Id = read.Id }, player);
            sapi.SendIngameDiscovery(player, "backrooms-note", Banner(log, null));
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/writing"), player.Entity, null, true, 8);
        }
    }

    /// <summary>What a note of this kind read at (x, z) says for this log (null: nothing due, directions only).</summary>
    private NoteResolution ResolveAt(string uid, double x, double z, string kind, System.Func<int, bool> visited, out NoteLog log, out int key, out int level)
    {
        key = LevelKey(x, z, out level);
        log = LogOf(uid);
        bool rare = kind == "folded";
        // (Level Fun's altered paper says its lie only once main 1 is read: the very first note is always main 1)
        bool firstRead = Catalog.Main?.Entries.Count > 0 && !log.Has(Catalog.Main.Entries[0].Key);
        NoteResolution res = kind == "altered" && level == WorldLayout.FunLevel && !firstRead ? NoteSequencer.ResolveSpecial(Catalog, log, "fun-altered") : null;
        return res ?? NoteSequencer.Resolve(Catalog, log, key, rare, visited);
    }

    /// <summary>
    /// The heart of reading, with no player needed (the console's <c>note probe</c> uses it too): resolves what a note
    /// of this kind read at (x, z) says for this log, finds its marks, and records it. Null if it told nothing.
    /// </summary>
    private NoteRead ReadAt(string uid, double x, double z, string kind, System.Func<int, bool> visited, out NoteLog log, out NoteResolution res)
    {
        res = ResolveAt(uid, x, z, kind, visited, out log, out int key, out int level);
        // (All on this thread: the console can wait)
        double y = geometry.FloorFor(level) + 1;
        List<MarkSlot> slots = SlotsFor(kind, res?.Entry.Mark);
        System.Func<int, int, bool> skip = SkipOf(TakenOf(log));
        foreach (MarkSlot slot in slots)
            slot.Found = marks.Resolve(slot.Kind, x, y, z, level, slot.Far, skip) ?? (skip != null ? marks.Resolve(slot.Kind, x, y, z, level, slot.Far) : null);
        List<NoteMark> found = Gather(slots);
        if (res == null && found.Count == 0) return null;

        var read = new NoteRead
        {
            Key = res?.Entry.Key, Track = res?.Track.Id ?? "dir", Level = key,
            X = (int)Math.Floor(x), Z = (int)Math.Floor(z), Hours = sapi.World.Calendar.TotalHours, Kind = kind, Marks = found,
        };
        log.Add(read, res?.Pick);
        dirty = true;
        return read;
    }

    private string Banner(NoteLog log, NoteResolution res)
    {
        if (res == null) return Lang.Get("backrooms:note-toast-dir");
        string chapter = res.Track.Chapter;
        int total = Catalog.ChapterTotal(chapter), n = Catalog.InChapter(chapter).Where(t => t.Cls != "special").Sum(log.CountIn);
        return Lang.Get("backrooms:note-toast", Lang.Get("backrooms:journal-track-" + chapter), Math.Max(1, n), Math.Max(total, n));
    }

    /// <summary>
    /// A journal's "mark again" link. The client only names one of its own reads and a mark of it: the place comes from
    /// the server's copy of that player's log, so nothing else can be marked this way.
    /// </summary>
    private void OnMarkAgain(IServerPlayer player, MarkAgainPacket packet)
    {
        if (player?.Entity == null || packet == null || !MapSetting.Waypoints(sapi.World.Config)) return;
        if (!logs.TryGetValue(player.PlayerUID, out NoteLog log) || log.Find(packet.Id) is not { } read) return;
        List<NoteMark> ms = read.Marks;
        if (packet.Mark < 0 || packet.Mark >= ms.Count) return;
        NoteMark m = ms[packet.Mark];
        bool rare = read.Kind == "folded";
        MapMarks.Add(sapi, player, new Vec3d(m.X + 0.5, player.Entity.Pos.Y, m.Z + 0.5), m.Title, m.Icon, rare ? RareColor : MapMarks.NoteColor, 4);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:note-marked-again"), EnumChatType.Notification);
    }

    // ================= Commands =================

    private void RegisterCommands(ICoreServerAPI api)
    {
        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        CommandArgumentParsers parsers = api.ChatCommands.Parsers;
        string[] kinds = { "door", "way", "cache", "refuge", "folded", "altered" };
        command.BeginSubCommand("note")
            .WithDescription("Wanderers' notes: read, give, status, reset")
            .BeginSubCommand("read")
                .WithDescription("Reads a note of a kind where you stand, as if you held one (door, way, cache, refuge; folded for a rare one; altered for Level Fun's)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWordRange("kind", kinds))
                .HandleWith(args =>
                {
                    string kind = args[0] as string ?? "door";
                    bool told = Read(args.Caller.Player as IServerPlayer, kind);
                    return TextCommandResult.Success(told ? "Read a " + kind + " note." : "The note told you nothing here.");
                })
            .EndSubCommand()
            .BeginSubCommand("give")
                .WithDescription("Gives you wanderers' notes (default: 4 door notes)")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWordRange("kind", kinds.Take(5).ToArray()), parsers.OptionalInt("count", 4))
                .HandleWith(args =>
                {
                    string kind = args[0] as string ?? "door";
                    Item item = api.World.GetItem(new AssetLocation("backrooms", NoteItemCode(kind)));
                    if (item == null) return TextCommandResult.Error("No such note.");
                    args.Caller.Player.InventoryManager.TryGiveItemstack(new ItemStack(item, (int)args[1]), true);
                    return TextCommandResult.Success($"Gave {(int)args[1]} {kind} notes.");
                })
            .EndSubCommand()
            .BeginSubCommand("probe")
                .WithDescription("Reads a note for a test reader (any name) at x z without a player (for the console): prints what it said and marked. Levels in 'been' (comma-separated ids) count as visited")
                .WithArgs(parsers.Word("reader"), parsers.Int("x"), parsers.Int("z"), parsers.OptionalWordRange("kind", kinds), parsers.OptionalWord("been"))
                .HandleWith(args =>
                {
                    if (layout == null || Catalog == null) return TextCommandResult.Error("Notes are not running.");
                    string kind = args[3] as string ?? "door";
                    var been = new HashSet<int>((args[4] as string ?? "0").Split(',').Select(v => int.TryParse(v, out int l) ? l : 0));
                    NoteRead read = ReadAt("probe:" + (string)args[0], (int)args[1], (int)args[2], kind, l => been.Contains(l == NoteCatalog.SnackroomsKey ? 6 : l), out NoteLog log, out NoteResolution res);
                    if (read == null) return TextCommandResult.Success("told nothing (no entry due and nothing to mark)");
                    string marksText = string.Join("; ", read.Marks.Select(m => $"{m.Title} at {m.X},{m.Z} ({m.Paces} paces {m.Dir})"));
                    return TextCommandResult.Success($"{(string)args[0]} read a {kind} note in level {read.Level}: {read.Key ?? "directions"} ({res?.Track.Cls ?? "-"}, track {read.Track}); marks: {(marksText.Length > 0 ? marksText : "none")}; banner: {Banner(log, res)}");
                })
            .EndSubCommand()
            .BeginSubCommand("log")
                .WithDescription("Prints a test reader's (or a player's) log: every note read, in order")
                .WithArgs(parsers.Word("reader"))
                .HandleWith(args =>
                {
                    string name = (string)args[0];
                    string uid = logs.ContainsKey("probe:" + name) ? "probe:" + name : sapi.World.AllPlayers.FirstOrDefault(p => p.PlayerName == name)?.PlayerUID;
                    if (uid == null || !logs.TryGetValue(uid, out NoteLog log)) return TextCommandResult.Error("No notes for " + name);
                    return TextCommandResult.Success($"{name}: " + string.Join(", ", log.Read.Select(r => r.Key)) + $" (+{log.Directions.Count} directions)");
                })
            .EndSubCommand()
            .BeginSubCommand("status")
                .WithDescription("Shows where a player is in each sequence of notes")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWord("player"))
                .HandleWith(args => TextCommandResult.Success(Status(args.Caller.Player as IServerPlayer, args[0] as string)))
            .EndSubCommand()
            .BeginSubCommand("reset")
                .WithDescription("Forgets every note a player has read (their journal), so the sequence starts again")
                .RequiresPlayer()
                .WithArgs(parsers.OptionalWord("player"))
                .HandleWith(args =>
                {
                    IServerPlayer who = Find(args.Caller.Player as IServerPlayer, args[0] as string);
                    if (who == null) return TextCommandResult.Error("No such player online.");
                    // (Ids go on from where the old log's stopped: a search still running for an old read must not find a new one)
                    logs[who.PlayerUID] = new NoteLog { PocketGiven = true, NextId = LogOf(who.PlayerUID).NextId };
                    dirty = true;
                    SendLog(who);
                    return TextCommandResult.Success($"{who.PlayerName}'s notes are forgotten.");
                })
            .EndSubCommand()
        .EndSubCommand();
    }

    private IServerPlayer Find(IServerPlayer caller, string name) =>
        string.IsNullOrEmpty(name) ? caller : sapi.World.AllOnlinePlayers.OfType<IServerPlayer>().FirstOrDefault(p => p.PlayerName.Equals(name, StringComparison.OrdinalIgnoreCase));

    private string Status(IServerPlayer caller, string name)
    {
        IServerPlayer who = Find(caller, name);
        if (who == null) return "No such player online.";
        if (Catalog == null || layout == null) return "Notes are not running (not a Backrooms world, or config/notes.json is missing).";
        NoteLog log = LogOf(who.PlayerUID);
        int key = LevelKey(who.Entity.Pos.X, who.Entity.Pos.Z, out _);
        System.Func<int, bool> visited = l => HasVisited(who.Entity, l);
        var sb = new StringBuilder();
        sb.AppendLine($"{who.PlayerName}: {log.Read.Count} notes read, {log.Directions.Count} directions; last common pick {log.LastPick ?? "-"}; here counts as level {key}");
        foreach (NoteTrack t in Catalog.Tracks)
        {
            int n = log.CountIn(t);
            if (n == 0 && t != Catalog.Main && t != Catalog.CommonFor(key) && t != Catalog.RareFor(key) && t != Catalog.RareAny) continue;
            NoteEntry next = t.Entries.FirstOrDefault(e => !log.Has(e.Key));
            string state = next == null ? "done" : NoteSequencer.GateMet(next, visited) ? "next " + next.Key : "waiting (" + next.Key + " wants a visit to " + string.Join("/", next.Gate) + ")";
            sb.AppendLine($"  {t.Id} ({t.Cls}): {n}/{t.Entries.Count}, {state}");
        }
        var nextOrdinary = NoteSequencer.Resolve(Catalog, log, key, false, visited);
        var nextFolded = NoteSequencer.Resolve(Catalog, log, key, true, visited);
        sb.Append($"  a note read here now would be {nextOrdinary?.Entry.Key ?? "directions only"}; a folded one {nextFolded?.Entry.Key ?? "directions only"}");
        return sb.ToString();
    }
}
