using System;
using System.Collections.Generic;
using System.Text;
using HarmonyLib;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;
using Backrooms.Worldgen;
using Vintagestory.API.Config;

namespace Backrooms.Needs.Beds;

/// <summary>
/// Registers the mod's bed (block, block entity, mountable) and switches the vanilla bed's own resting off for it.
/// The vanilla <c>DidMount</c> starts a <c>RestPlayer</c> listener that lowers vanilla tiredness and gets the sleeper up at
/// zero; here the fatigue behaviour does the resting from awake hours, so that listener must do nothing on our entity.
/// Also the <c>/backrooms bedtest</c> debug command.
/// </summary>
public class BedSystem : ModSystem
{
    /// <summary>The class name the mountable is saved under in an entity's <c>mountedOn</c> tree.</summary>
    public const string MountableClass = "backroomsbed";

    private const string HarmonyId = "backroomsss.beds";
    private static readonly object patchLock = new();
    private static int patchUsers;
    private bool patched;

    public override double ExecuteOrder() => 1.2;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockClass("BackroomsBed", typeof(BlockBackroomsBed));
        api.RegisterBlockEntityClass("BackroomsBed", typeof(BlockEntityBackroomsBed));
        api.RegisterMountable(MountableClass, GetMountable);

        lock (patchLock)
        {
            patched = true;
            if (patchUsers++ > 0) return;
            var harmony = new Harmony(HarmonyId);
            harmony.UnpatchAll(HarmonyId);
            harmony.Patch(AccessTools.Method(typeof(BlockEntityBed), "RestPlayer"),
                prefix: new HarmonyMethod(typeof(BedSystem), nameof(RestPlayerPrefix)));
        }
    }

    public override void Dispose()
    {
        if (!patched) return;
        patched = false;
        lock (patchLock)
            if (--patchUsers == 0) new Harmony(HarmonyId).UnpatchAll(HarmonyId);
    }

    /// <summary>Vanilla resting runs for vanilla beds only.</summary>
    private static bool RestPlayerPrefix(BlockEntityBed __instance) => __instance is not BlockEntityBackroomsBed;

    /// <summary>
    /// The seat an entity's saved <c>mountedOn</c> tree points to. The tree holds the head's position. A client that has not
    /// yet been sent the block entity (the server made it a moment ago) makes its own, which the server's replaces.
    /// </summary>
    private static IMountableSeat GetMountable(IWorldAccessor world, TreeAttribute tree)
    {
        var pos = new BlockPos(tree.GetInt("posx"), tree.GetInt("posy"), tree.GetInt("posz"));
        IBlockAccessor blocks = world.BlockAccessor;
        if (blocks.GetBlock(pos) is not BlockBackroomsBed bed) return null;
        pos = bed.HeadPos(pos);
        if (blocks.GetBlockEntity(pos) is BlockEntityBackroomsBed existing) return existing;
        try
        {
            if (world.Side == EnumAppSide.Server) return BlockBackroomsBed.EnsureEntity(world, pos);
            if (blocks.GetBlock(pos) is not BlockBackroomsBed { IsHead: true }) return null;
            blocks.SpawnBlockEntity("BackroomsBed", pos);
            return blocks.GetBlockEntity(pos) as BlockEntityBackroomsBed;
        }
        catch (Exception e)
        {
            world.Logger.Warning("[backrooms] could not make a bed entity at {0}: {1}", pos, e.Message);
            return null;
        }
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        var parsers = api.ChatCommands.Parsers;
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("bedtest")
                .WithDescription("Dev test: bedtest [x y z] reports the bed at a position (or the one you look at, or stand on): which half, head and foot positions, rest quality, the seat "
                    + "(makes the bed's entity if it has none). bedtest scan [rings] finds one of each bed family the worldgen places within that many macro cells of the spawn (default 40) "
                    + "and reports it in the log once its column loads. bedtest place <headcode> [x y z] puts a bed down (default two blocks over the spawn) and reports it. "
                    + "bedtest room <headcode> x y z <none|head|sides|all> clears a box there, makes a floor and ceiling, puts a wall right behind the head with an empty room beyond it, "
                    + "places the bed and blocks beside it (none; both sides of the head; every side block; everything round it), and reports where getting up would put the sleeper, and where vanilla's rule would")
                // (Words, not numbers: the first one may be a mode. A console line ends in a carriage return the parser keeps as an argument; it is dropped)
                .WithArgs(parsers.OptionalWord("a"), parsers.OptionalWord("b"), parsers.OptionalWord("c"), parsers.OptionalWord("d"), parsers.OptionalWord("e"), parsers.OptionalWord("f"))
                .HandleWith(args => OnBedTest(api, args))
            .EndSubCommand();
    }

    private static int placed;

    private static TextCommandResult OnBedTest(ICoreServerAPI api, TextCommandCallingArgs args)
    {
        var words = new List<string>();
        for (int i = 0; i < 6; i++)
            if (args[i] is string w && w.Trim() is { Length: > 0 } t) words.Add(t);

        // bedtest scan [rings]
        if (words.Count > 0 && words[0] == "scan") return OnScan(api, words.Count > 1 && int.TryParse(words[1], out int rings) ? rings : 40);

        // bedtest room <headcode> x y z <none|head|sides|all>
        if (words.Count > 0 && words[0] == "room")
        {
            if (words.Count < 6 || !int.TryParse(words[2], out int rx) || !int.TryParse(words[3], out int ry) || !int.TryParse(words[4], out int rz))
                return TextCommandResult.Error("bedtest room <headcode> x y z <none|head|sides|all>");
            // (The room spans the chunk columns round the head: load them, then build)
            var at = new BlockPos(rx, ry, rz);
            var columns = new HashSet<(int, int)>();
            foreach (int dx in new[] { -5, 5 })
                foreach (int dz in new[] { -5, 5 })
                    columns.Add(((rx + dx) / GlobalConstants.ChunkSize, (rz + dz) / GlobalConstants.ChunkSize));
            int waiting = columns.Count;
            foreach ((int cx, int cz) in columns)
                api.WorldManager.LoadChunkColumnPriority(cx, cz, new ChunkLoadOptions
                {
                    OnLoaded = () =>
                    {
                        if (--waiting == 0) Logged(api, OnRoom(api, words[1], at, words[5]));
                    },
                });
            return TextCommandResult.Success("bedtest room: loading " + columns.Count + " chunk columns, the result is in the log");
        }

        // bedtest place <headcode> [x y z]
        if (words.Count > 0 && words[0] == "place")
        {
            if (words.Count < 2) return TextCommandResult.Error("bedtest place <headcode> [x y z]");
            BlockPos at;
            if (words.Count >= 5 && int.TryParse(words[2], out int px) && int.TryParse(words[3], out int py) && int.TryParse(words[4], out int pz)) at = new BlockPos(px, py, pz);
            else
            {
                // (Each one in a place of its own, so a test does not break the last one's bed)
                at = api.World.DefaultSpawnPosition.AsBlockPos.UpCopy(2).Add(3 * (placed % 5), 0, 3 * (placed++ / 5));
                for (int i = 0; i < 12 && api.World.BlockAccessor.GetBlock(at).Id != 0; i++) at.Up();
            }
            return Logged(api, OnPlace(api, words[1], at));
        }

        // bedtest [x y z]
        BlockPos pos;
        if (words.Count >= 3 && int.TryParse(words[0], out int x) && int.TryParse(words[1], out int y) && int.TryParse(words[2], out int z)) pos = new BlockPos(x, y, z);
        else if (args.Caller.Player is IServerPlayer { CurrentBlockSelection: { } sel }) pos = sel.Position.Copy();
        else if (args.Caller.Entity != null) pos = args.Caller.Entity.Pos.AsBlockPos.Copy();
        else return TextCommandResult.Error("Give x y z, or look at a bed");
        return Logged(api, TextCommandResult.Success(Describe(api.World, pos)));
    }

    /// <summary>(The console shows a command's reply only some of the time; the log always has it)</summary>
    private static TextCommandResult Logged(ICoreServerAPI api, TextCommandResult result)
    {
        api.Logger.Notification("[backrooms] {0}", result.StatusMessage);
        return result;
    }

    /// <summary>
    /// A test room round a bed: a stone floor and ceiling over 11 by 11, air between, a wall one block behind the headboard across
    /// the whole width (with the same room again beyond it), the bed, and stone "nightstands" as the mode says.
    /// </summary>
    private static TextCommandResult OnRoom(ICoreServerAPI api, string headCode, BlockPos head, string mode)
    {
        IBlockAccessor blocks = api.World.BlockAccessor;
        if (!headCode.Contains(':')) headCode = "backrooms:" + headCode;
        if (api.World.GetBlock(new AssetLocation(headCode)) is not BlockBackroomsBed { IsHead: true } bed) return TextCommandResult.Error(headCode + " is not a bed head");
        Block stone = api.World.GetBlock(new AssetLocation("game:rock-granite"));
        if (stone == null) return TextCommandResult.Error("no game:rock-granite");
        BlockFacing headDir = BedStand.HeadDir(bed), foot = bed.FootDir;
        var p = new BlockPos(0);
        for (int dx = -5; dx <= 5; dx++)
            for (int dz = -5; dz <= 5; dz++)
                for (int dy = -1; dy <= 3; dy++)
                {
                    p.Set(head.X + dx, head.Y + dy, head.Z + dz);
                    blocks.SetBlock(dy is -1 or 3 ? stone.Id : 0, p);
                    blocks.RemoveBlockEntity(p);
                }
        // (The wall: the plane one block behind the head, across and up)
        for (int w = -5; w <= 5; w++)
            for (int dy = 0; dy <= 2; dy++)
            {
                BlockPos q = head.AddCopy(headDir).Add(headDir.Axis == EnumAxis.X ? 0 : w, dy, headDir.Axis == EnumAxis.X ? w : 0);
                blocks.SetBlock(stone.Id, q);
            }
        OnPlace(api, headCode, head);
        BlockPos footPos = foot == null ? null : head.AddCopy(foot);
        var stoneAt = new List<BlockPos>();
        if (mode is "head" or "sides" or "all")
        {
            BlockFacing across = foot?.GetCW() ?? headDir.GetCW();
            stoneAt.Add(head.AddCopy(across)); stoneAt.Add(head.AddCopy(across.Opposite));
        }
        if (mode is "sides" or "all" && footPos != null)
        {
            BlockFacing across = foot.GetCW();
            stoneAt.Add(footPos.AddCopy(across)); stoneAt.Add(footPos.AddCopy(across.Opposite));
        }
        if (mode == "all")
        {
            if (footPos != null) stoneAt.Add(footPos.AddCopy(foot));
            else foreach (BlockFacing f in BlockFacing.HORIZONTALS) stoneAt.Add(head.AddCopy(f));
        }
        foreach (BlockPos s in stoneAt) blocks.SetBlock(stone.Id, s);
        return TextCommandResult.Success($"bedtest room ({mode}): " + Describe(api.World, head));
    }

    private static TextCommandResult OnPlace(ICoreServerAPI api, string headCode, BlockPos pos)
    {
        IBlockAccessor blocks = api.World.BlockAccessor;
        if (!headCode.Contains(':')) headCode = "backrooms:" + headCode;
        Block head = api.World.GetBlock(new AssetLocation(headCode));
        if (head is not BlockBackroomsBed bed || !bed.IsHead) return TextCommandResult.Error(headCode + " is not the head of one of the mod's beds");
        blocks.SetBlock(head.Id, pos);
        if (bed.PartnerPos(pos) is { } footPos)
        {
            Block foot = null;
            foreach (string word in new[] { "foot", "feet" })
                foot ??= api.World.GetBlock(new AssetLocation(headCode.Replace("head", word)));
            if (foot == null) return TextCommandResult.Error("No foot block for " + headCode);
            blocks.SetBlock(foot.Id, footPos);
        }
        return TextCommandResult.Success(Describe(api.World, pos));
    }

    /// <summary>The prop of each family the generator places, and how its head half is told from its foot.</summary>
    private static readonly (string Name, ushort Prop, System.Func<Tile, bool> IsHead)[] Families =
    {
        ("bed-head/foot (Level 5, 9)", Worldgen.Props.Bed, t => t.Stack == 0),
        ("hospitalbed", Worldgen.Props.HospitalBed, t => t.Stack == 0),
        ("sleepingbag", Worldgen.Props.SleepingBag, t => t.Stack == 0),
        ("improvbed", Worldgen.Props.ImprovBed, t => true),
        ("bedroll", Worldgen.Props.Bedroll, t => true),
        ("run-safecot", Worldgen.Props.RunSafeCot, t => t.Stack == 0),
        ("l974-bed", Worldgen.Props.L974Bed, t => (t.Stack & 1) == 0),
    };

    private static TextCommandResult OnScan(ICoreServerAPI api, int rings)
    {
        WorldLayout layout;
        WorldGeometry geometry;
        try { layout = BackroomsWorld.CreateLayout(api.World); geometry = BackroomsWorld.CreateGeometry(api.World); }
        catch (Exception e) { return TextCommandResult.Error("Not a Backrooms world: " + e.Message); }
        BlockPos spawn = api.World.DefaultSpawnPosition.AsBlockPos;
        int smx = WorldLayout.MacroOf(spawn.X), smz = WorldLayout.MacroOf(spawn.Z);
        var found = new (int X, int Z, int Level)?[Families.Length];
        int missing = Families.Length, cells = 0;
        for (int ring = 0; ring <= rings && missing > 0; ring++)
            for (int dx = -ring; dx <= ring && missing > 0; dx++)
                for (int dz = -ring; dz <= ring && missing > 0; dz++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != ring) continue;
                    int mx = smx + dx, mz = smz + dz, level = layout.LevelAt(mx, mz);
                    // (Only the levels that have beds in them)
                    if (level is not (WorldLayout.Level974 or WorldLayout.RunLevel or 1 or 4 or 5 or 9)) continue;
                    cells++;
                    for (int lx = 0; lx < WorldLayout.MacroSize && missing > 0; lx++)
                        for (int lz = 0; lz < WorldLayout.MacroSize && missing > 0; lz++)
                        {
                            int gx = mx * WorldLayout.MacroSize + lx, gz = mz * WorldLayout.MacroSize + lz;
                            Tile t = layout.TileAt(gx, gz);
                            if (t.Variant == 0) continue;
                            for (int i = 0; i < Families.Length; i++)
                                if (found[i] == null && t.Variant == Families[i].Prop && Families[i].IsHead(t))
                                {
                                    found[i] = (gx, gz, level);
                                    missing--;
                                }
                        }
                }
        var text = new StringBuilder($"bedtest scan: looked in {cells} cells, {Families.Length - missing} of {Families.Length} families found; each is reported below as its column loads");
        for (int i = 0; i < Families.Length; i++)
        {
            if (found[i] is not { } f) { api.Logger.Notification("[backrooms] bedtest scan: {0}: none found", Families[i].Name); continue; }
            string family = Families[i].Name;
            api.Logger.Notification("[backrooms] bedtest scan: {0}: tile at {1} {2} (Level {3})", family, f.X, f.Z, WorldLayout.DisplayNumber(f.Level));
            api.WorldManager.LoadChunkColumnPriority(f.X / GlobalConstants.ChunkSize, f.Z / GlobalConstants.ChunkSize, new ChunkLoadOptions
            {
                OnLoaded = () =>
                {
                    int floor = geometry.FloorFor(f.Level);
                    var pos = new BlockPos(f.X, 0, f.Z);
                    for (int y = floor - 2; y <= floor + 8; y++)
                    {
                        pos.Y = y;
                        if (api.World.BlockAccessor.GetBlock(pos) is BlockBackroomsBed { IsHead: true })
                        {
                            api.Logger.Notification("[backrooms] bedtest scan: {0}: {1}", family, Describe(api.World, pos));
                            return;
                        }
                    }
                    api.Logger.Notification("[backrooms] bedtest scan: {0}: NO BED BLOCK in the column at {1} {2} (floor {3})", family, f.X, f.Z, floor);
                },
            });
        }
        return TextCommandResult.Success(text.ToString());
    }

    /// <summary>The report of <c>/backrooms bedtest</c> for the bed at a position (also what the headless test reads).</summary>
    public static string Describe(IWorldAccessor world, BlockPos pos)
    {
        IBlockAccessor blocks = world.BlockAccessor;
        Block block = blocks.GetBlock(pos);
        if (block is not BlockBackroomsBed bed) return $"bedtest {pos}: {block.Code} is not one of the mod's beds ({block.GetType().Name})";
        var sb = new StringBuilder();
        BlockPos head = bed.HeadPos(pos), foot = bed.PartnerPos(head);
        sb.Append($"bedtest {block.Code} at {pos}: {(bed.IsTwoBlock ? (bed.IsHead ? "head half" : "foot half") : "one block")}");
        sb.Append($", side {bed.Side.Code}, foot direction {(bed.FootDir?.Code ?? "none")}, lying toward {bed.LieDir.Code}");
        sb.Append($"; head {head}");
        if (!ReferenceEquals(blocks.GetBlock(head), bed) && blocks.GetBlock(head) is not BlockBackroomsBed { IsHead: true })
            sb.Append($" HAS NO HEAD BLOCK (found {blocks.GetBlock(head).Code})");
        if (foot != null)
        {
            Block other = blocks.GetBlock(foot);
            bool paired = other is BlockBackroomsBed ob && !ob.IsHead && ob.Side == bed.Side;
            sb.Append($", foot {foot} = {other.Code} ({(paired ? "paired" : "NOT PAIRED")})");
        }
        sb.Append($"; quality {bed.Quality:0.##}");
        BlockEntityBackroomsBed entity = BlockBackroomsBed.EnsureEntity(world, head);
        if (entity == null) sb.Append("; no entity could be made");
        else
        {
            EntityPos seat = entity.SeatPosition;
            sb.Append($"; seat {seat.X:0.##} {seat.Y:0.##} {seat.Z:0.##} yaw {seat.Yaw:0.##}, entity quality {entity.RestQuality:0.##}, mounted by {(entity.MountedBy?.GetName() ?? "nobody")}");
            Vec3d stand = BedStand.Choose(world, bed, head, BedStand.PlayerBox, new Vec3d(seat.X, seat.Y + 0.1, seat.Z), out string how);
            sb.Append($"; STAND {stand.AsBlockPos} ({how}, {BlockDist(stand, head, foot)})");
            BlockFacing vanillaFacing = BlockFacing.FromCode(blocks.GetBlock(head).LastCodePart(0));
            Vec3d van = BedStand.Vanilla(world, head, vanillaFacing, BedStand.PlayerBox, out string vhow);
            sb.Append($"; VANILLA would stand {(van == null ? "nowhere" : van.AsBlockPos.ToString())} ({vhow}, {(van == null ? "-" : BlockDist(van, head, foot))})");
        }
        return sb.ToString();
    }

    /// <summary>How far a spot is from the nearest block of the bed, in blocks, for the report (1 = beside it).</summary>
    private static string BlockDist(Vec3d spot, BlockPos head, BlockPos foot)
    {
        BlockPos s = spot.AsBlockPos;
        int d = Math.Abs(s.X - head.X) + Math.Abs(s.Z - head.Z) + Math.Abs(s.Y - head.Y);
        if (foot != null) d = Math.Min(d, Math.Abs(s.X - foot.X) + Math.Abs(s.Z - foot.Z) + Math.Abs(s.Y - foot.Y));
        return d == 0 ? "on the bed" : $"{d} from the bed";
    }
}
