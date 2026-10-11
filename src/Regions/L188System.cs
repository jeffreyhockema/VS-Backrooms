using System;
using System.Collections.Generic;
using System.Text;
using Backrooms.Entities;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Part = Backrooms.Worldgen.WorldLayout.L188Part;
using WState = Backrooms.Worldgen.WorldLayout.L188WindowState;

namespace Backrooms.Regions;

/// <summary>What of Level 188 is the building itself, and never breaks.</summary>
public static class L188
{
    private static readonly HashSet<string> FabricParts = new()
    {
        "nothing", "sky", "shaft", "paver", "turf", "deck", "hatch", "cladding", "sill", "coping", "slab", "downlight", "wall", "window",
        "stairwindow", "outerwindow", "guestdoor", "stairdoor", "courtyarddoor", "firedoor", "frontdoor", "stair", "exitsign", "floorsign",
        "downpipe", "drain", "entrywindow", "entrysill",
    };

    /// <summary>Whether a block is the fabric of Level 188's building (canon: forcing its doors has always failed).</summary>
    public static bool IsFabric(Block block)
    {
        if (block?.Code == null || block.Code.Domain != "backrooms" || !block.Code.Path.StartsWith("l188-")) return false;
        return FabricParts.Contains(block.Code.Path.Split('-')[1]);
    }
}

/// <summary>
/// Level 188, "The Courtyard of Windows": the rules (docs/new-levels/188-plan.md, 3.4-3.8).
/// <list type="bullet">
/// <item><b>The windows.</b> Every courtyard window's state is the world's (<see cref="WorldLayout.L188StateAt"/>): blinds
/// down, glowing, up on a dark or a lit room, changing every day or so; a predatory one (Entity 2), about one room in
/// sixteen, moving every night. While anyone is in the level the system keeps the blocks (and the room's bedside lamp)
/// in step, and swaps a figure to beckoning while someone is near it.</item>
/// <item><b>Blinds.</b> Opening a closed window's blind from inside its room is being taken (the network's
/// <c>l188-blind-&lt;storey&gt;</c>): the window then shows where its opener went, and the room's door is sealed for three
/// in-game days (saved with the world).</item>
/// <item><b>The arm.</b> Within six blocks of a predatory window: whispers, and the figure beckons. Within two for a
/// second: an arm comes out of the glass, holds, drags and hurts. Hit it twice, or get three and a half blocks away; held
/// for six seconds at the glass, you are pulled through, and die.</item>
/// <item><b>Doors, the hatch, dispensers, the keycard, the guest book</b>, by their block behaviours below.</item>
/// <item><b>Peripherals.</b> Now and then, at the edge of sight in the corridors and the courtyard, a shape that is gone when
/// you look (the client draws it; the server says when, and takes a little stability for it).</item>
/// </list>
/// </summary>
public class L188System : ModSystem
{
    /// <summary>Player attribute (watched): bumped each time a Peripheral shows; its lowest bit is the side (1 right).</summary>
    public const string PeripheralKey = "backrooms:l188Peri";
    private const string SaveKey = "backrooms-l188-windows";
    private const string HeldStat = "l188Held";
    private const double SealDays = 3;
    private const double WhisperReach = 6, GrabReach = 2, BreakFreeReach = 3.5;
    private const long GrabDelayMs = 1000, HeldMaxMs = 6000;

    private static ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private ThresholdSystem thresholds;
    private bool dirty;

    // Saved: windows whose blind someone opened (window * 8 + storey) -> (the level it shows, the day it closes again)
    private readonly Dictionary<int, (int Level, double Until)> sealedWindows = new();
    private readonly Dictionary<string, int> blockIds = new();
    private readonly Dictionary<string, Grab> grabs = new();
    private readonly Dictionary<string, long> nearSinceMs = new();
    private readonly Dictionary<string, double> nextPeripheral = new();
    private readonly Dictionary<(int, int), long> lastWhisperMs = new();
    private readonly Random rand = new();
    private readonly List<IServerPlayer> here = new();
    private readonly List<string> stale = new();
    private readonly List<int> expired = new();
    private long[] tickListeners = Array.Empty<long>();
    private bool isServer;
    private ICoreClientAPI capi;
    private PeripheralRenderer peripheral;

    private sealed class Grab
    {
        public int Window, Storey;
        public long StartMs;
        public int Hits;
        public Entity Arm;
        public bool Pulling;
    }

    /// <summary>The arm's animations (its model's): one plays at a time.</summary>
    private static readonly string[] ArmAnimations = { "reach", "grab", "pull", "recoil" };

    /// <summary>Arms reaching out of the glass toward someone in the second before they are taken (by the player's uid).</summary>
    private readonly Dictionary<string, (Entity Arm, int Window, int Storey)> reaching = new();

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsL188Blind", typeof(BlockBehaviorL188Blind));
        api.RegisterBlockBehaviorClass("BackroomsL188Door", typeof(BlockBehaviorL188Door));
        api.RegisterBlockBehaviorClass("BackroomsL188Hatch", typeof(BlockBehaviorL188Hatch));
        api.RegisterBlockBehaviorClass("BackroomsL188GuestBook", typeof(BlockBehaviorL188GuestBook));
        api.RegisterBlockClass("BackroomsL188Dispenser", typeof(BlockL188Dispenser));
        api.RegisterEntity("BackroomsL188Arm", typeof(EntityL188Arm));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        isServer = true;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            thresholds = api.ModLoader.GetModSystem<ThresholdSystem>();
            Load(api.WorldManager.SaveGame.GetData(SaveKey));
            api.Event.GameWorldSave += OnGameWorldSave;
            tickListeners = new[]
            {
                api.Event.RegisterGameTickListener(OnWindowsTick, 2000, 1000),
                api.Event.RegisterGameTickListener(OnArmTick, 250),
                api.Event.RegisterGameTickListener(OnPlayersTick, 1000),
            };
            api.Event.PlayerDisconnect += OnPlayerDisconnect;
        });
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        peripheral = new PeripheralRenderer(api);
        api.Event.RegisterRenderer(peripheral, EnumRenderStage.Ortho, "backrooms-l188-peripheral");
    }

    public override void Dispose()
    {
        if (peripheral != null) capi?.Event.UnregisterRenderer(peripheral, EnumRenderStage.Ortho);
        peripheral = null;
        // (sapi is static, so in single player this system's client-side instance sees it too: only the server's own
        // instance lets go of it)
        if (!isServer || sapi == null) return;
        foreach (long id in tickListeners) sapi.Event.UnregisterGameTickListener(id);
        sapi.Event.GameWorldSave -= OnGameWorldSave;
        sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
        // (Static, for BandAt: it must not outlive this world in a process that goes on to load another)
        sapi = null;
    }

    private void OnGameWorldSave()
    {
        if (!dirty) return;
        sapi.WorldManager.SaveGame.StoreData(SaveKey, Save());
        dirty = false;
    }

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        ReleaseGrab(player, false);
        Retract(player.PlayerUID);
        nearSinceMs.Remove(player.PlayerUID);
        nextPeripheral.Remove(player.PlayerUID);
    }

    // ================= Where things are =================

    private int Floor => geometry.FloorFor(WorldLayout.Level188);
    private double Hours => sapi.World.Calendar.TotalHours;
    private long Day => (long)Math.Floor(sapi.World.Calendar.TotalDays);

    private int LevelAt(double x, double z) => layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(x)), WorldLayout.MacroOf((int)Math.Floor(z)));

    private static string Side(ArchPier p) => p switch { ArchPier.North => "north", ArchPier.East => "east", ArchPier.South => "south", _ => "west" };

    private int Id(string path)
    {
        if (blockIds.TryGetValue(path, out int id)) return id;
        id = sapi.World.GetBlock(new AssetLocation("backrooms", path))?.BlockId ?? 0;
        return blockIds[path] = id;
    }

    /// <summary>The middle of a courtyard window (block coordinates) at a storey: the centre of its 2 x 2 in the wall.</summary>
    private Vec3d WindowCentre(int wi, int storey)
    {
        var (l, r, _) = WorldLayout.L188WindowTiles(wi);
        return new Vec3d(layout.L188BuildX0 + (l.Bx + r.Bx) / 2.0 + 0.5, Floor + 4 * storey + 3, layout.L188BuildZ0 + (l.Bz + r.Bz) / 2.0 + 0.5);
    }

    /// <summary>A window's state now: the world's, but for a blind someone opened (it shows where they went).</summary>
    private WState StateNow(int wi, int storey, out int sceneLevel)
    {
        sceneLevel = -1;
        if (sealedWindows.TryGetValue(wi * 8 + storey, out var seal) && seal.Until > sapi.World.Calendar.TotalDays)
        {
            sceneLevel = seal.Level;
            return WState.Scene;
        }
        WState state = layout.L188StateAt(wi, storey, Hours, Day);
        if (state == WState.Scene) sceneLevel = layout.L188LinkLevel(wi);
        return state;
    }

    private bool IsLoaded(BlockPos pos) => sapi.World.BlockAccessor.GetChunkAtBlockPos(pos) != null;

    /// <summary>
    /// Whether a window is predatory now and shows it: the world says so and its glass has the figure in it (a figure waits
    /// while someone is in its room, <see cref="Apply"/>, and the arm never comes out of a window that gave no warning).
    /// </summary>
    private bool Predatory(int wi, int storey)
    {
        if (StateNow(wi, storey, out _) != WState.Figure) return false;
        var (l, _, _) = WorldLayout.L188WindowTiles(wi);
        string path = sapi.World.BlockAccessor.GetBlock(new BlockPos(layout.L188BuildX0 + l.Bx, Floor + 4 * storey + 2, layout.L188BuildZ0 + l.Bz)).Code?.Path;
        return path != null && (path.Contains("-figure-") || path.Contains("-beckon-"));
    }

    // ================= Keeping the windows =================

    /// <summary>Everyone playing in the level now (one list, refilled by each tick that asks: don't keep it).</summary>
    private List<IServerPlayer> PlayersHere()
    {
        here.Clear();
        foreach (IPlayer p in sapi.World.AllOnlinePlayers)
            if (p is IServerPlayer sp && sp.Entity != null && sp.ConnectionState == EnumClientState.Playing && LevelAt(sp.Entity.Pos.X, sp.Entity.Pos.Z) == WorldLayout.Level188)
                here.Add(sp);
        return here;
    }

    private void OnWindowsTick(float dt)
    {
        // Blinds come down again after their days are up
        expired.Clear();
        foreach (var (key, seal) in sealedWindows) if (seal.Until <= sapi.World.Calendar.TotalDays) expired.Add(key);
        foreach (int key in expired) { sealedWindows.Remove(key); dirty = true; }
        List<IServerPlayer> here = PlayersHere();
        if (here.Count == 0) return;
        for (int wi = 0; wi < WorldLayout.L188Windows; wi++)
        {
            if (wi == WorldLayout.L188StairWindow) continue;
            for (int s = 0; s < WorldLayout.L188Storeys; s++)
            {
                if (s == 0 && layout.L188LinkLevel(wi) >= 0) continue; // always the same
                WState state = StateNow(wi, s, out int scene);
                if (state == WState.Figure && AnyoneWithin(here, WindowCentre(wi, s), WhisperReach)) state = WState.Beckon;
                Apply(wi, s, state, scene, here);
            }
        }
    }

    private static bool AnyoneWithin(List<IServerPlayer> players, Vec3d at, double reach)
    {
        foreach (IServerPlayer p in players)
            if (p.Entity.Pos.XYZ.Add(0, 1, 0).SquareDistanceTo(at) <= reach * reach) return true;
        return false;
    }

    /// <summary>Whether a player is in a window's room (at its storey).</summary>
    private bool InRoom(List<IServerPlayer> players, int wi, int storey)
    {
        var (wing, k) = WorldLayout.L188WindowWingK(wi);
        foreach (IServerPlayer p in players)
        {
            var c = layout.L188CellAtWorld((int)Math.Floor(p.Entity.Pos.X), (int)Math.Floor(p.Entity.Pos.Z));
            int s = (int)Math.Floor((p.Entity.Pos.Y - Floor) / 4);
            if (c.Part == Part.Room && c.Wing == wing && c.K == k && s == storey) return true;
        }
        return false;
    }

    /// <summary>Makes a window (its four blocks, its room's lamp and door) show a state, where it is loaded and not already so.</summary>
    private void Apply(int wi, int storey, WState state, int scene, List<IServerPlayer> here)
    {
        var (l, r, facing) = WorldLayout.L188WindowTiles(wi);
        string side = Side(facing);
        string Code(string part) => state == WState.Scene
            ? $"l188-window-scene-{WorldLayout.L188SceneOf(scene)}-{part}-{side}"
            : $"l188-window-{state.ToString().ToLowerInvariant()}-{part}-{side}";
        var ll = new BlockPos(layout.L188BuildX0 + l.Bx, Floor + 4 * storey + 2, layout.L188BuildZ0 + l.Bz);
        if (!IsLoaded(ll)) return;
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int want = Id(Code("ll"));
        if (want == 0 || ba.GetBlock(ll).BlockId == want) return;
        // A figure never appears in a room someone is in at that moment; it waits until they leave
        Block now = ba.GetBlock(ll);
        bool wasFigure = now.Code?.Path.Contains("-figure-") == true || now.Code?.Path.Contains("-beckon-") == true;
        if (state is WState.Figure or WState.Beckon && !wasFigure && InRoom(here, wi, storey)) return;
        foreach (var (pos, part) in new[] { ((l.Bx, l.Bz), "l"), ((r.Bx, r.Bz), "r") })
        {
            Set(new BlockPos(layout.L188BuildX0 + pos.Item1, Floor + 4 * storey + 2, layout.L188BuildZ0 + pos.Item2), Code("l" + part));
            Set(new BlockPos(layout.L188BuildX0 + pos.Item1, Floor + 4 * storey + 3, layout.L188BuildZ0 + pos.Item2), Code("u" + part));
        }
        // The bedside lamp: on behind a glowing or lit window and behind a figure; off otherwise
        var (wing, k) = WorldLayout.L188WindowWingK(wi);
        var (lx, lz) = WorldLayout.L188RoomTile(wing, k, false, 0, 0);
        var lamp = new BlockPos(layout.L188BuildX0 + lx, Floor + 4 * storey + 1, layout.L188BuildZ0 + lz);
        string lampPath = ba.GetBlock(lamp).Code?.Path;
        if (lampPath != null && lampPath.StartsWith("l188-nightstand-"))
        {
            bool on = state is WState.Glow or WState.Lit or WState.Figure or WState.Beckon;
            string next = on ? lampPath.Replace("-off-", "-on-") : lampPath.Replace("-on-", "-off-");
            if (next != lampPath) Set(lamp, next);
        }
        // The room's door: sealed while its window shows another place
        var (dx, dz) = WorldLayout.L188At(wing, 17 + 5 * k + 3, 6);
        foreach (int up in new[] { 1, 2 })
        {
            var door = new BlockPos(layout.L188BuildX0 + dx, Floor + 4 * storey + up, layout.L188BuildZ0 + dz);
            string path = ba.GetBlock(door).Code?.Path;
            if (path == null || !path.StartsWith("l188-guestdoor-")) continue;
            if (state == WState.Scene && !path.Contains("-sealed-"))
                Set(door, path.Replace("-closed-", "-sealed-").Replace("-open-", "-sealed-").Replace("-locked-", "-sealed-"));
            else if (state != WState.Scene && path.Contains("-sealed-")) Set(door, path.Replace("-sealed-", "-closed-"));
        }
    }

    private void Set(BlockPos pos, string path)
    {
        int id = Id(path);
        if (id == 0) return;
        sapi.World.BlockAccessor.ExchangeBlock(id, pos);
        sapi.World.BlockAccessor.MarkBlockDirty(pos);
    }

    // ================= Sealed doors =================

    /// <summary>Whether someone using a guest door stands on its room side (its code's side is the corridor face).</summary>
    internal static bool FromInside(IPlayer player, BlockPos pos, string path)
    {
        BlockFacing corridor = BlockFacing.FromCode(path.Substring(path.LastIndexOf('-') + 1));
        if (corridor == null || player?.Entity == null) return false;
        double side = (player.Entity.Pos.X - (pos.X + 0.5)) * corridor.Normali.X + (player.Entity.Pos.Z - (pos.Z + 0.5)) * corridor.Normali.Z;
        return side < 0;
    }

    /// <summary>
    /// A sealed door opened from inside closes and seals again once nobody stands in its way, if its window still shows
    /// another place (if the seal ran out meanwhile, it simply stays open).
    /// </summary>
    internal void ResealLater(BlockPos pos, BlockPos half)
    {
        sapi.Event.RegisterCallback(dt =>
        {
            if (layout == null) return;
            var c = layout.L188CellAtWorld(pos.X, pos.Z);
            if (c.Part != Part.WallIn) return;
            int storey = (Math.Min(pos.Y, half.Y) - Floor) / 4;
            if (StateNow(WorldLayout.L188WindowIndex(c.Wing, (c.A - 17) / 5), storey, out _) != WState.Scene) return;
            foreach (IPlayer p in sapi.World.AllOnlinePlayers)
                if (p.Entity != null && p.Entity.Pos.XYZ.SquareDistanceTo(pos.X + 0.5, p.Entity.Pos.Y, pos.Z + 0.5) < 1.6 * 1.6)
                {
                    ResealLater(pos, half);
                    return;
                }
            foreach (BlockPos at in new[] { pos, half })
            {
                string path = sapi.World.BlockAccessor.GetBlock(at).Code?.Path;
                if (path != null && path.StartsWith("l188-guestdoor-open-")) Set(at, path.Replace("-open-", "-sealed-"));
            }
        }, 3000);
    }

    // ================= Blinds =================

    /// <summary>A player uses a window block (the blind behaviour): opening a blind from inside, the Hub's window, an outer window.</summary>
    public void UseWindow(IServerPlayer player, BlockPos pos, Block block)
    {
        if (layout == null || player.Entity == null) return;
        string path = block.Code.Path;
        int level = LevelAt(pos.X, pos.Z);
        if (level == WorldLayout.Hub)
        {
            thresholds?.Use(player, pos, "l188-hubwindow");
            return;
        }
        if (level != WorldLayout.Level188) return;
        if (path.StartsWith("l188-outerwindow-"))
        {
            // Only a blind onto nothing
            foreach (var at in WindowBlocks(pos, "l188-outerwindow-"))
            {
                string p = sapi.World.BlockAccessor.GetBlock(at).Code.Path;
                Set(at, path.Contains("-closed-") ? p.Replace("-closed-", "-open-") : p.Replace("-open-", "-closed-"));
            }
            Play("backrooms:sounds/effect/188/blindup", pos);
            return;
        }
        int bx = pos.X - layout.L188BuildX0, bz = pos.Z - layout.L188BuildZ0;
        int wi = WorldLayout.L188WindowAt(bx, bz);
        if (wi < 0 || wi == WorldLayout.L188StairWindow) return;
        int storey = (pos.Y - Floor) / 4;
        var (_, _, facing) = WorldLayout.L188WindowTiles(wi);
        var (fx, fz) = WorldLayout.L188Step(facing);
        // The blind is on the inside: from the courtyard there is only glass
        double side = (player.Entity.Pos.X - (pos.X + 0.5)) * fx + (player.Entity.Pos.Z - (pos.Z + 0.5)) * fz;
        WState state = StateNow(wi, storey, out _);
        if (side > 0)
        {
            if (state != WState.Scene) player.SendIngameError("backrooms-l188", Lang.Get("backrooms:l188-blind-outside"));
            return;
        }
        switch (state)
        {
            case WState.Closed or WState.Glow:
            {
                Play("backrooms:sounds/effect/188/blindup", pos);
                Vec3d from = player.Entity.Pos.XYZ;
                int target = layout.L188BlindTarget(wi, storey);
                player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:l188-taken"), EnumChatType.Notification);
                thresholds?.Use(player, pos, "l188-blind-" + storey);
                SealWhenGone(player, from, wi, storey, target, pos, 10);
                return;
            }
            case WState.Open or WState.Lit:
                player.SendIngameError("backrooms-l188", Lang.Get("backrooms:l188-blind-up"));
                return;
            case WState.Figure or WState.Beckon:
                Play("backrooms:sounds/effect/188/whisper", pos);
                return;
        }
    }

    /// <summary>
    /// Once whoever opened a blind has gone, the window lights up with where they went, and the room is sealed. (The
    /// teleport waits for the place to load, and maybe be generated first: while it is still on its way, look again.)
    /// </summary>
    private void SealWhenGone(IServerPlayer player, Vec3d from, int wi, int storey, int target, BlockPos pos, int tries)
    {
        sapi.Event.RegisterCallback(_ =>
        {
            if (sapi == null || player.Entity == null) return;
            if (player.Entity.Pos.XYZ.SquareDistanceTo(from) < 8 * 8)
            {
                if (player.Entity.Teleporting && tries > 0) SealWhenGone(player, from, wi, storey, target, pos, tries - 1);
                return;
            }
            sealedWindows[wi * 8 + storey] = (target, sapi.World.Calendar.TotalDays + SealDays);
            dirty = true;
            Apply(wi, storey, WState.Scene, target, new List<IServerPlayer>());
            Play("backrooms:sounds/effect/188/taken", pos);
        }, 600);
    }

    /// <summary>The blocks of one window (the 2 x 2 round a block of it) whose code starts so.</summary>
    private IEnumerable<BlockPos> WindowBlocks(BlockPos pos, string prefix)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++)
                for (int dz = -1; dz <= 1; dz++)
                {
                    if (dx != 0 && dz != 0) continue;
                    var at = pos.AddCopy(dx, dy, dz);
                    if (ba.GetBlock(at).Code?.Path.StartsWith(prefix) == true) yield return at;
                }
    }

    private void Play(string sound, BlockPos pos, float range = 16) =>
        sapi.World.PlaySoundAt(new AssetLocation(sound), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, range);

    // ================= The arm =================

    private void OnArmTick(float dt)
    {
        if (layout == null) return;
        List<IServerPlayer> here = PlayersHere();
        long now = sapi.World.ElapsedMilliseconds;
        // Whoever left the level while held (taken through a threshold, died and came back elsewhere) is let go
        if (grabs.Count > 0)
        {
            stale.Clear();
            foreach (string uid in grabs.Keys) if (!IsHere(here, uid)) stale.Add(uid);
            foreach (string uid in stale)
            {
                if (sapi.World.PlayerByUid(uid) is IServerPlayer gone) ReleaseGrab(gone, false);
                else grabs.Remove(uid);
            }
        }
        if (reaching.Count > 0)
        {
            stale.Clear();
            foreach (string uid in reaching.Keys) if (!IsHere(here, uid)) stale.Add(uid);
            foreach (string uid in stale) Retract(uid);
        }
        foreach (IServerPlayer player in here)
        {
            string uid = player.PlayerUID;
            if (grabs.TryGetValue(uid, out Grab grab))
            {
                Hold(player, grab, now);
                continue;
            }
            if (!player.Entity.Alive || Strike.IsCreative(player.Entity)) { nearSinceMs.Remove(uid); Retract(uid); continue; }
            // The nearest predatory window on the player's storey
            int storey = (int)Math.Floor((player.Entity.Pos.Y - Floor) / 4);
            if (storey < 0 || storey >= WorldLayout.L188Storeys) { nearSinceMs.Remove(uid); Retract(uid); continue; }
            Vec3d eye = player.Entity.Pos.XYZ.Add(0, 1, 0);
            int best = -1;
            double bestD = double.MaxValue;
            for (int wi = 0; wi < WorldLayout.L188Windows; wi++)
            {
                if (!Predatory(wi, storey)) continue;
                double d = eye.DistanceTo(WindowCentre(wi, storey));
                if (d < bestD) { bestD = d; best = wi; }
            }
            if (best < 0 || bestD > WhisperReach) { nearSinceMs.Remove(uid); Retract(uid); continue; }
            // The whispers, from the window
            var key = (best, storey);
            if (now - lastWhisperMs.GetValueOrDefault(key) > 9000)
            {
                lastWhisperMs[key] = now;
                Vec3d c = WindowCentre(best, storey);
                sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/188/whisper"), c.X, c.Y, c.Z, null, false, 10, 0.8f);
            }
            if (bestD > GrabReach) { nearSinceMs.Remove(uid); Retract(uid); continue; }
            if (!nearSinceMs.TryGetValue(uid, out long since))
            {
                // The arm comes out of the glass, reaching, in the second's grace
                nearSinceMs[uid] = now;
                Retract(uid);
                if (SpawnArm(player, best, storey) is { } arm)
                {
                    reaching[uid] = (arm, best, storey);
                    Animate(arm, "reach");
                }
                continue;
            }
            if (now - since < GrabDelayMs) continue;
            nearSinceMs.Remove(uid);
            StartGrab(player, best, storey, now);
        }
    }

    private static bool IsHere(List<IServerPlayer> players, string uid)
    {
        foreach (IServerPlayer p in players) if (p.PlayerUID == uid) return true;
        return false;
    }

    private void StartGrab(IServerPlayer player, int wi, int storey, long now)
    {
        var grab = new Grab { Window = wi, Storey = storey, StartMs = now };
        grabs[player.PlayerUID] = grab;
        Vec3d c = WindowCentre(wi, storey);
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/188/grab"), c.X, c.Y, c.Z, null, true, 16);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:l188-grabbed"), EnumChatType.Notification);
        player.Entity.Stats.Set("walkspeed", HeldStat, -0.5f, false);
        // The arm that was reaching for them (else one out of the glass now, if its model is there) takes hold
        Entity arm = null;
        if (reaching.TryGetValue(player.PlayerUID, out var reach) && reach.Window == wi && reach.Storey == storey && reach.Arm.Alive)
        {
            arm = reach.Arm;
            reaching.Remove(player.PlayerUID);
        }
        else
        {
            Retract(player.PlayerUID);
            arm = SpawnArm(player, wi, storey);
        }
        if (arm != null)
        {
            Animate(arm, "grab");
            grab.Arm = arm;
        }
    }

    /// <summary>A Window's arm out of the glass on the player's side of it, turned toward them (null if its model is missing).</summary>
    private Entity SpawnArm(IServerPlayer player, int wi, int storey)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation("backrooms", "l188-arm"));
        if (type == null) return null;
        Vec3d c = WindowCentre(wi, storey);
        Entity arm = sapi.World.ClassRegistry.CreateEntity(type);
        var (_, _, facing) = WorldLayout.L188WindowTiles(wi);
        var (fx, fz) = WorldLayout.L188Step(facing);
        // On the side of the glass the player is
        double side = (player.Entity.Pos.X - c.X) * fx + (player.Entity.Pos.Z - c.Z) * fz;
        double out_ = side >= 0 ? 0.55 : -0.55;
        arm.Pos.SetPos(c.X + fx * out_, c.Y - 0.4, c.Z + fz * out_);
        arm.Pos.Yaw = (float)Math.Atan2(player.Entity.Pos.X - arm.Pos.X, player.Entity.Pos.Z - arm.Pos.Z);
        arm.WatchedAttributes.SetString("backrooms:l188Victim", player.PlayerUID);
        sapi.World.SpawnEntity(arm);
        return arm;
    }

    /// <summary>Plays one of the arm's animations, stopping whichever it played before.</summary>
    private static void Animate(Entity arm, string animation)
    {
        if (arm?.AnimManager == null) return;
        foreach (string other in ArmAnimations)
            if (other != animation) arm.AnimManager.StopAnimation(other);
        arm.AnimManager.StartAnimation(animation);
    }

    /// <summary>An arm that reached and took nobody goes back into the glass.</summary>
    private void Retract(string uid)
    {
        if (!reaching.TryGetValue(uid, out var reach)) return;
        reaching.Remove(uid);
        Entity arm = reach.Arm;
        if (!arm.Alive) return;
        Animate(arm, "recoil");
        sapi.Event.RegisterCallback(dt => { if (arm.Alive) arm.Die(EnumDespawnReason.Removed); }, 300);
    }

    private void Hold(IServerPlayer player, Grab grab, long now)
    {
        EntityPlayer entity = player.Entity;
        if (!entity.Alive || grab.Hits >= 2) { ReleaseGrab(player, grab.Hits >= 2); return; }
        Vec3d c = WindowCentre(grab.Window, grab.Storey);
        double dx = c.X - entity.Pos.X, dz = c.Z - entity.Pos.Z, d = Math.Sqrt(dx * dx + dz * dz);
        if (d > BreakFreeReach) { ReleaseGrab(player, true); return; }
        // It hurts, and drags toward the glass
        if ((now - grab.StartMs) % 1000 < 250)
            entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Internal, Type = EnumDamageType.Injury }, 1f);
        if (d > 0.9 && (now - grab.StartMs) % 500 < 250)
        {
            double step = Math.Min(0.35, d - 0.85);
            entity.TeleportToDouble(entity.Pos.X + dx / d * step, entity.Pos.Y, entity.Pos.Z + dz / d * step);
        }
        if (grab.Arm is { Alive: true } arm)
        {
            arm.Pos.Yaw = (float)Math.Atan2(entity.Pos.X - arm.Pos.X, entity.Pos.Z - arm.Pos.Z);
            // (The grab holds for half a second, then the arm pulls while it drags)
            if (!grab.Pulling && now - grab.StartMs > 500)
            {
                grab.Pulling = true;
                Animate(arm, "pull");
            }
        }
        // Held at the glass long enough: pulled through
        if (now - grab.StartMs >= HeldMaxMs && d <= 1.4)
        {
            ReleaseGrab(player, false);
            sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/188/grab"), c.X, c.Y, c.Z, null, false, 16);
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:l188-consumed", player.PlayerName), EnumChatType.Notification);
            entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Internal, Type = EnumDamageType.Injury }, 9999f);
        }
    }

    private void ReleaseGrab(IServerPlayer player, bool brokeFree)
    {
        if (!grabs.TryGetValue(player.PlayerUID, out Grab grab)) return;
        grabs.Remove(player.PlayerUID);
        player.Entity?.Stats.Remove("walkspeed", HeldStat);
        if (grab.Arm is { Alive: true } arm)
        {
            Animate(arm, "recoil");
            Vec3d at = arm.Pos.XYZ;
            sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/188/recoil"), at.X, at.Y, at.Z, null, true, 16);
            sapi.Event.RegisterCallback(_ => { if (arm.Alive) arm.Die(EnumDespawnReason.Removed); }, 300);
        }
        if (brokeFree) player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:l188-brokefree"), EnumChatType.Notification);
    }

    /// <summary>The arm was struck (two blows and it lets go).</summary>
    internal void OnArmHit(Entity arm)
    {
        foreach (var grab in grabs.Values)
            if (grab.Arm == arm) grab.Hits++;
    }

    // ================= Peripherals, and the windows' pull on the mind =================

    private void OnPlayersTick(float dt)
    {
        if (layout == null) return;
        double now = sapi.World.ElapsedMilliseconds / 1000.0;
        foreach (IServerPlayer player in PlayersHere())
        {
            EntityPlayer entity = player.Entity;
            string uid = player.PlayerUID;
            var c = layout.L188CellAtWorld((int)Math.Floor(entity.Pos.X), (int)Math.Floor(entity.Pos.Z));
            // Near a predatory window, reality wears thin
            int storey = (int)Math.Floor((entity.Pos.Y - Floor) / 4);
            if (storey is >= 0 and < WorldLayout.L188Storeys)
            {
                Vec3d eye = entity.Pos.XYZ.Add(0, 1, 0);
                for (int wi = 0; wi < WorldLayout.L188Windows; wi++)
                    if (Predatory(wi, storey) && eye.DistanceTo(WindowCentre(wi, storey)) <= WhisperReach)
                    {
                        Drain(entity, 0.004 * dt);
                        break;
                    }
            }
            // A Peripheral, now and then, in the corridors and the courtyard
            if (c.Part is not (Part.Corridor or Part.Court)) continue;
            if (!nextPeripheral.TryGetValue(uid, out double next)) { nextPeripheral[uid] = now + 40 + rand.NextDouble() * 80; continue; }
            if (now < next) continue;
            nextPeripheral[uid] = now + 60 + rand.NextDouble() * 120;
            int count = entity.WatchedAttributes.GetInt(PeripheralKey) / 2 + 1;
            entity.WatchedAttributes.SetInt(PeripheralKey, count * 2 + rand.Next(2));
            Drain(entity, 0.02);
        }
    }

    private static void Drain(EntityPlayer entity, double amount)
    {
        double stability = entity.WatchedAttributes.GetDouble("temporalStability", 1);
        entity.WatchedAttributes.SetDouble("temporalStability", Math.Max(0, stability - amount));
    }

    // ================= Danger =================

    /// <summary>
    /// How dangerous a place in Level 188 is: safe in a room with its door shut (unless its window is a predatory one);
    /// the heart of the level in the courtyard, the lobby and the lower corridors; nearer the edge upstairs, on the roof and
    /// round the windows that lead out.
    /// </summary>
    public static MenaceBand BandAt(WorldLayout layout, WorldGeometry geometry, int gx, double y, int gz)
    {
        var c = layout.L188CellAtWorld(gx, gz);
        double rel = y - geometry.FloorFor(WorldLayout.Level188);
        int storey = (int)Math.Floor(rel / 4);
        if (rel > WorldLayout.L188RoofRel) return MenaceBand.Approach;
        if (c.Part is Part.Room or Part.OuterRoom && sapi != null && storey is >= 0 and < WorldLayout.L188Storeys)
        {
            var (dx, dz) = WorldLayout.L188At(c.Wing, (c.Part == Part.Room ? 17 : 7) + 5 * c.K + 3, c.Part == Part.Room ? 6 : 10);
            string path = sapi.World.BlockAccessor.GetBlock(new BlockPos(layout.L188BuildX0 + dx, geometry.FloorFor(WorldLayout.Level188) + 4 * storey + 1,
                layout.L188BuildZ0 + dz))?.Code?.Path;
            bool shut = path != null && path.StartsWith("l188-guestdoor-") && !path.Contains("-open-");
            bool prey = c.Part == Part.Room && layout.L188IsPrey(WorldLayout.L188WindowIndex(c.Wing, c.K), storey, (long)Math.Floor(sapi.World.Calendar.TotalDays));
            if (shut && !prey) return MenaceBand.Safe;
        }
        if (c.Part == Part.Court)
        {
            for (int wi = 0; wi < WorldLayout.L188Windows; wi++)
            {
                if (layout.L188LinkLevel(wi) < 0) continue;
                var (l, _, _) = WorldLayout.L188WindowTiles(wi);
                double ddx = layout.L188BuildX0 + l.Bx - gx, ddz = layout.L188BuildZ0 + l.Bz - gz;
                if (ddx * ddx + ddz * ddz <= 64) return MenaceBand.Approach;
            }
            return MenaceBand.Heartland;
        }
        return storey >= 2 ? MenaceBand.Approach : MenaceBand.Heartland;
    }

    // ================= Saving =================

    private byte[] Save()
    {
        var sb = new StringBuilder();
        foreach (var (key, seal) in sealedWindows) sb.Append(key).Append(' ').Append(seal.Level).Append(' ').Append(seal.Until.ToString("R", System.Globalization.CultureInfo.InvariantCulture)).Append('\n');
        return Encoding.UTF8.GetBytes(sb.ToString());
    }

    private void Load(byte[] data)
    {
        sealedWindows.Clear();
        if (data == null) return;
        foreach (string line in Encoding.UTF8.GetString(data).Split('\n'))
        {
            string[] f = line.Split(' ');
            if (f.Length != 3 || !int.TryParse(f[0], out int key) || !int.TryParse(f[1], out int level)
                || !double.TryParse(f[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double until)) continue;
            sealedWindows[key] = (level, until);
        }
    }

    // ================= The client: Peripherals =================

    /// <summary>
    /// A Peripheral: a dark, blurred, tall shape at the far left or right of the screen, fading in, gone the moment the
    /// player turns toward it, or after a few seconds anyway. It is nothing but the edge of sight.
    /// </summary>
    private sealed class PeripheralRenderer : IRenderer
    {
        private readonly ICoreClientAPI capi;
        private int last = -1, texture, frame;
        private bool showing, right;
        private double shownAt, fadingFrom = -1;
        private float yawAtShow;

        public PeripheralRenderer(ICoreClientAPI capi) { this.capi = capi; }

        public double RenderOrder => 0.9;
        public int RenderRange => 0;

        public void OnRenderFrame(float deltaTime, EnumRenderStage stage)
        {
            EntityPlayer entity = capi.World.Player?.Entity;
            if (entity == null) return;
            int value = entity.WatchedAttributes.GetInt(PeripheralKey);
            double now = capi.World.ElapsedMilliseconds / 1000.0;
            if (last < 0) last = value;
            if (value != last)
            {
                last = value;
                showing = true;
                right = (value & 1) == 1;
                shownAt = now;
                fadingFrom = -1;
                yawAtShow = entity.Pos.Yaw;
                frame = capi.World.Rand.Next(3);
                texture = capi.Render.GetOrLoadTexture(new AssetLocation("backrooms", $"textures/gui/188/peripheral-{frame + 1}.png"));
            }
            if (!showing || texture <= 0) return;
            // Turning toward it (the yaw grows turning left in Vintage Story) makes it go
            float turned = GameMath.AngleRadDistance(yawAtShow, entity.Pos.Yaw);
            bool looked = right ? turned < -0.35f : turned > 0.35f;
            if (fadingFrom < 0 && (looked || now - shownAt > 2.6)) fadingFrom = now;
            double alpha = Math.Min(1, (now - shownAt) / 0.5) * 0.55;
            if (fadingFrom >= 0)
            {
                double fade = 1 - (now - fadingFrom) / (looked ? 0.12 : 0.6);
                if (fade <= 0) { showing = false; return; }
                alpha *= fade;
            }
            float h = capi.Render.FrameHeight * 0.55f, w = h / 2;
            float x = right ? capi.Render.FrameWidth - w * 0.85f : -w * 0.15f, y = capi.Render.FrameHeight * 0.3f;
            capi.Render.Render2DTexture(texture, x, y, w, h, 50, new Vec4f(1, 1, 1, (float)alpha));
        }

        public void Dispose() { }
    }
}

/// <summary>Level 188's courtyard windows (and the Hub's window into it): using one asks <see cref="L188System.UseWindow"/>.</summary>
public class BlockBehaviorL188Blind : BlockBehavior
{
    private static WorldInteraction[] blindHelp, climbHelp;

    public BlockBehaviorL188Blind(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        // A window onto elsewhere has no blind to open (it is walked through, not used); the Hub's window (a courtyard
        // window's block, set in the Hub's tunnel) is climbed through by hand
        string path = block.Code?.Path ?? "";
        if (path.StartsWith("l188-window-scene-")) return Array.Empty<WorldInteraction>();
        if (path.StartsWith("l188-window-") && selection?.Position is { } pos && Salvage.ProtectionSystem.LevelAt(world, pos.X, pos.Z) == WorldLayout.Hub)
            return climbHelp ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l188-window", MouseButton = EnumMouseButton.Right } };
        return blindHelp ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l188-blind", MouseButton = EnumMouseButton.Right } };
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player)
            sapi.ModLoader.GetModSystem<L188System>()?.UseWindow(player, blockSel.Position, block);
        return true;
    }
}

/// <summary>
/// Level 188's doors: guest doors, stair doors, the courtyard's door. Right-click opens or shuts both halves; a locked guest
/// door opens for the housekeeping keycard (and stays open); a sealed one never opens.
/// </summary>
public class BlockBehaviorL188Door : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL188Door(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l188-door", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side != EnumAppSide.Server) return true;
        string path = block.Code.Path;
        BlockPos pos = blockSel.Position;
        string next;
        if (path.Contains("-sealed-"))
        {
            // The seal only keeps others out: from inside the room it opens, and seals again behind whoever left
            var rules = world.Api.ModLoader.GetModSystem<L188System>();
            if (rules != null && L188System.FromInside(byPlayer, pos, path))
            {
                BlockPos half = path.Contains("-lower-") ? pos.UpCopy() : pos.DownCopy();
                Swap(world, pos, path.Replace("-sealed-", "-open-"));
                string halfPath = world.BlockAccessor.GetBlock(half).Code?.Path;
                if (halfPath != null && halfPath.StartsWith("l188-guestdoor-sealed-")) Swap(world, half, halfPath.Replace("-sealed-", "-open-"));
                world.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 12);
                rules.ResealLater(pos.Copy(), half);
                return true;
            }
            // (The keycard does nothing to a door held shut)
            (byPlayer as IServerPlayer)?.SendIngameError("backrooms-l188", Lang.Get(HoldsKeycard(byPlayer) ? "backrooms:l188-keycard-sealed" : "backrooms:l188-sealed"));
            world.PlaySoundAt(new AssetLocation("game:sounds/effect/latch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 8);
            return true;
        }
        if (path.Contains("-locked-"))
        {
            if (!HoldsKeycard(byPlayer))
            {
                (byPlayer as IServerPlayer)?.SendIngameError("backrooms-l188", Lang.Get("backrooms:l188-locked"));
                world.PlaySoundAt(new AssetLocation("game:sounds/effect/latch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 8);
                return true;
            }
            (byPlayer as IServerPlayer)?.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:l188-keycard-open"), EnumChatType.Notification);
            next = path.Replace("-locked-", "-open-");
        }
        else if (path.Contains("-closed-")) next = path.Replace("-closed-", "-open-");
        else if (path.Contains("-open-")) next = path.Replace("-open-", "-closed-");
        else return true;
        BlockPos other = path.Contains("-lower-") ? pos.UpCopy() : pos.DownCopy();
        Swap(world, pos, next);
        string otherPath = world.BlockAccessor.GetBlock(other).Code?.Path;
        if (otherPath != null && otherPath.StartsWith(path.Substring(0, path.IndexOf('-', 5))))
        {
            string otherNext = otherPath.Replace("-locked-", "-open-");
            otherNext = next.Contains("-open-") ? otherNext.Replace("-closed-", "-open-") : otherNext.Replace("-open-", "-closed-");
            Swap(world, other, otherNext);
        }
        world.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 12);
        return true;
    }

    private static bool HoldsKeycard(IPlayer player) =>
        player?.InventoryManager?.ActiveHotbarSlot?.Itemstack?.Collectible?.Code?.Path == "l188-keycard";

    internal static void Swap(IWorldAccessor world, BlockPos pos, string path)
    {
        Block to = world.GetBlock(new AssetLocation("backrooms", path));
        if (to == null) return;
        world.BlockAccessor.ExchangeBlock(to.BlockId, pos);
        world.BlockAccessor.MarkBlockDirty(pos);
    }
}

/// <summary>The iron hatch in the courtyard's deck: right-click lifts all four quarters (or lets them down).</summary>
public class BlockBehaviorL188Hatch : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL188Hatch(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l188-hatch", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side != EnumAppSide.Server) return true;
        BlockPos pos = blockSel.Position;
        bool open = block.Code.Path.Contains("-closed-");
        for (int dx = -1; dx <= 1; dx++)
            for (int dz = -1; dz <= 1; dz++)
            {
                BlockPos at = pos.AddCopy(dx, 0, dz);
                string path = world.BlockAccessor.GetBlock(at).Code?.Path;
                if (path == null || !path.StartsWith("l188-hatch-")) continue;
                BlockBehaviorL188Door.Swap(world, at, open ? path.Replace("-closed-", "-open-") : path.Replace("-open-", "-closed-"));
            }
        world.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/188/hatch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 16);
        if (open) (byPlayer as IServerPlayer)?.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:l188-hatch-open"), EnumChatType.Notification);
        return true;
    }
}

/// <summary>The lobby's reception desk: the straight lengths have the guest book open on the counter, to read.</summary>
public class BlockBehaviorL188GuestBook : BlockBehavior
{
    private static WorldInteraction[] help;

    public BlockBehaviorL188GuestBook(Block block) : base(block)
    {
    }

    private bool HasBook => block.Variant["kind"] == "straight";

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        if (!HasBook) return Array.Empty<WorldInteraction>();
        return help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l188-guestbook", MouseButton = EnumMouseButton.Right } };
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        if (!HasBook) return false;
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server)
            (byPlayer as IServerPlayer)?.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:l188-guestbook"), EnumChatType.Notification);
        return true;
    }
}

/// <summary>The lobby's breakfast: a cereal or juice dispenser, three portions, then empty.</summary>
public class BlockL188Dispenser : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side != EnumAppSide.Server) return true;
        // l188-cerealdispenser-3-north: the stage is the third part
        string[] parts = Code.Path.Split('-');
        if (parts.Length < 4 || !int.TryParse(parts[2], out int stage)) return true;
        if (stage <= 0)
        {
            (byPlayer as IServerPlayer)?.SendIngameError("backrooms-l188", Lang.Get("backrooms:l188-dispenser-empty"));
            return true;
        }
        string item = parts[1] == "cerealdispenser" ? "l188-cereal" : "l188-juicebox";
        Item food = world.GetItem(new AssetLocation("backrooms", item));
        if (food != null)
        {
            var stack = new ItemStack(food);
            if (!byPlayer.InventoryManager.TryGiveItemstack(stack, true))
                world.SpawnItemEntity(stack, blockSel.Position.ToVec3d().Add(0.5, 1, 0.5));
        }
        parts[2] = (stage - 1).ToString();
        BlockBehaviorL188Door.Swap(world, blockSel.Position, string.Join("-", parts));
        world.PlaySoundAt(new AssetLocation("game:sounds/player/collect"), blockSel.Position.X + 0.5, blockSel.Position.Y + 0.5, blockSel.Position.Z + 0.5, byPlayer, true, 8);
        return true;
    }
}

/// <summary>A Window's arm (Entity 2): put where it is and turned by <see cref="L188System"/>; a blow makes it count, not die.</summary>
public class EntityL188Arm : EntityAgent
{
    public override bool StoreWithChunk => false;

    public override bool ReceiveDamage(DamageSource damageSource, float damage)
    {
        if (World.Side == EnumAppSide.Server && damageSource?.Type != EnumDamageType.Heal)
            Api.ModLoader.GetModSystem<L188System>()?.OnArmHit(this);
        return false;
    }
}
