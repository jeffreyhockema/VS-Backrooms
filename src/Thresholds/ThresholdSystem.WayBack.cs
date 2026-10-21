using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// The game side of the ways back built at arrivals (ThresholdNetwork.WayBack.cs): putting the door or the elevator into
/// the wall once the place is loaded, keeping them saved with the world, and the <c>/backrooms wayback</c> test command.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Where the ways back are saved, beside the links (<see cref="SaveKey"/>, whose layout is unchanged).</summary>
    private const string WayBackSaveKey = "backrooms-thresholds-wayback";

    /// <summary>How many times building a way back waits for its chunk to load, and how long each time.</summary>
    private const int WayBackTries = 6, WayBackRetryMs = 500;

    /// <summary>
    /// <see cref="TunnelPaint"/> is the generator's own rule, so a built door is painted as the level's own (Level 2's steel
    /// doors are painted by their place); <see cref="PlaqueSalt"/> is the way back's own (the generator takes a hotel
    /// plaque from the tile's variant): one of rooms 201 to 208 by place.
    /// </summary>
    private const ulong PlaqueSalt = 0x7E11;

    private void LoadWayBacks(ICoreServerAPI api)
    {
        byte[] saved = api.WorldManager.SaveGame.GetData(WayBackSaveKey);
        if (network.LoadWayBacks(saved))
        {
            api.Logger.Notification("[backrooms] {0} threshold links written down, {1} of them to doors and elevators built as ways back", network.Count, network.WayBackCount);
            return;
        }
        if (api.WorldManager.SaveGame.GetData(WayBackSaveKey + "-unreadable") == null)
            api.WorldManager.SaveGame.StoreData(WayBackSaveKey + "-unreadable", saved);
        api.Logger.Warning("[backrooms] The saved ways back could not all be read (kept as {0}-unreadable); {1} were. The doors stand and lead back; the rest are only not rebuilt",
            WayBackSaveKey, network.WayBackCount);
    }

    /// <summary>The way someone put down in front of a way back faces: out of it, into the room.</summary>
    private static (int Dx, int Dz) WayBackFacing(WayBack way) => way.Facing switch
    {
        ArchPier.North => (0, -1),
        ArchPier.South => (0, 1),
        ArchPier.East => (1, 0),
        _ => (-1, 0),
    };

    /// <summary>How many blocks high a way back is: a door's two leaves, a lift's two and its header (or the cage's dial).</summary>
    private static int WayBackHeight(WayBackStyle style) => style is WayBackStyle.OfficeLift or WayBackStyle.HotelLift or WayBackStyle.HotelCage ? 3 : 2;

    /// <summary>The code of a block of a way back: leaf <paramref name="leaf"/> (0 the first) at <paramref name="rel"/> above the floor.</summary>
    private string WayBackCode(WayBack way, int leaf, int rel)
    {
        (int x, int z) = way.Tiles[leaf];
        string part = rel == 1 ? "lower" : "upper";
        string side = way.Facing.ToString().ToLowerInvariant();
        // (As the generator has them: the leaf with the smaller coordinate is the left one seen from in front when the
        // doors face south or west)
        bool smallerIsLeft = way.Facing is ArchPier.South or ArchPier.West;
        string half = (leaf == 0) == smallerIsLeft ? "l" : "r";
        ulong seed = (ulong)sapi.World.Seed;
        switch (way.Style)
        {
            case WayBackStyle.OfficeDoor: return $"officedoor-{part}";
            case WayBackStyle.MetalDoor: return $"metaldoor-{part}";
            case WayBackStyle.PoolDoor: return $"pooldoor-{part}";
            case WayBackStyle.FreightLift: return $"elevatordoor-{part}";
            case WayBackStyle.TunnelDoor:
            {
                int paint = TunnelPaint.PaintOf(seed, x, z);
                return paint >= 0 ? $"tunneldoorpaint-{TunnelPaint.Names[paint]}-{part}" : $"tunneldoor-{part}";
            }
            case WayBackStyle.HotelDoor:
                // (Rooms 201 to 208, as the hotel's own guest doors)
                return rel == 1 ? "hoteldoor-lower" : $"hoteldoor-upper{Hashing.Hash(seed, x, z, PlaqueSalt) % 8}";
            case WayBackStyle.OfficeLift: return $"liftdoor-drywall-{(rel == 3 ? "header" : part)}-{half}-{side}";
            case WayBackStyle.HotelLift: return $"liftdoor-hotel-{(rel == 3 ? "header" : part)}-{half}-{side}";
            default: return $"cagelift-hotel-{(rel == 3 ? "dial" : part)}-{half}-{side}";
        }
    }

    /// <summary>The blocks of a way back and where they go: every leaf, from the floor up.</summary>
    private List<(BlockPos Pos, Block Block)> WayBackBlocks(WayBack way)
    {
        int level = layout.TileAt(way.X, way.Z).Level;
        int y = geometry.FloorFor(level) + 1;
        var blocks = new List<(BlockPos, Block)>();
        (int X, int Z)[] tiles = way.Tiles; // (built anew on each access)
        for (int leaf = 0; leaf < tiles.Length; leaf++)
            for (int rel = 1; rel <= WayBackHeight(way.Style); rel++)
                blocks.Add((new BlockPos(tiles[leaf].X, y + rel - 1, tiles[leaf].Z), sapi.World.GetBlock(new AssetLocation("backrooms", WayBackCode(way, leaf, rel)))));
        return blocks;
    }

    /// <summary>
    /// Whether a block of the wall may give way to a way back: what the level was built with there (the generator's own
    /// block, or one of ours of the wall's kind: solid, no block entity, not a threshold), or nothing at all (a gap
    /// someone made, which the door fills). Never anything with a block entity (a container, a sign), a threshold of
    /// any kind, or anything of anyone else's: whatever else a player has put there stays, and the thin spot does instead.
    /// </summary>
    private bool WallGivesWay(IBlockAccessor blocks, BlockPos pos, Block want)
    {
        Block there = blocks.GetBlock(pos);
        if (there.BlockId == want.BlockId) return true;
        if (blocks.GetBlockEntity(pos) != null) return false;
        if (sapi.World.Claims.Get(pos) is { Length: > 0 }) return false;
        if (there.BlockId == 0) return true;
        if (there.HasBehavior<BlockBehaviorThreshold>()) return false;
        Tile tile = layout.TileAt(pos.X, pos.Z);
        if (sapi.ModLoader.GetModSystem<BackroomsModSystem>()?.Generator is { } generator && generator.ColumnBlock(tile, pos.X, pos.Z, pos.Y, out _) == there.BlockId) return true;
        return there.Code?.Domain == "backrooms" && there.SideSolid.All && there.Replaceable < 5000;
    }

    /// <summary>
    /// Makes sure the door or elevator built as the way back of a threshold stands at its arrival (each time someone
    /// arrives that way: once built, nothing changes). Where the wall has been changed so that it cannot (a container
    /// put there, a claim), the way back becomes a thin spot on the arrival instead, for good. A chunk not yet loaded is
    /// waited for a few times, then left until the next arrival.
    /// </summary>
    private void BuildWayBack(IServerPlayer player, (int X, int Z) source, int tries = 0, Action<string> done = null)
    {
        if (network?.WayBackOf(source) is not { } way) { done?.Invoke("no way back built for it"); return; }
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        List<(BlockPos Pos, Block Block)> plan = WayBackBlocks(way);
        foreach ((BlockPos pos, _) in plan)
        {
            if (blocks.GetChunkAtBlockPos(pos) != null) continue;
            if (tries + 1 < WayBackTries) sapi.Event.RegisterCallback(_ => BuildWayBack(player, source, tries + 1, done), WayBackRetryMs);
            else done?.Invoke("its chunk is not loaded: left for the next arrival");
            return;
        }
        string why = null;
        foreach ((BlockPos pos, Block block) in plan)
        {
            if (block == null) why = "a block of it is missing";
            else if (!WallGivesWay(blocks, pos, block)) why = $"{blocks.GetBlock(pos).Code} at {pos} stays";
            if (why != null) break;
        }
        if (why != null)
        {
            // A thin spot after all, where they stand
            sapi.Logger.Notification("[backrooms] The way back at {0}, {1} cannot be built ({2}): a thin spot instead", way.X, way.Z, why);
            if (network.GiveUpWayBack(source) is { Marker: true } thin)
            {
                LeaveThinSpot(thin);
                if (player != null && player.ConnectionState == EnumClientState.Playing) inThinSpot[player.PlayerUID] = true;
            }
            done?.Invoke("cannot be built (" + why + "): a thin spot instead");
            return;
        }
        int placed = 0;
        foreach ((BlockPos pos, Block block) in plan)
        {
            if (blocks.GetBlock(pos).BlockId == block.BlockId) continue;
            blocks.SetBlock(block.BlockId, pos);
            placed++;
        }
        if (placed > 0) sapi.Logger.Notification("[backrooms] A way back built at {0}, {1} ({2}, facing {3})", way.X, way.Z, way.Style, way.Facing);
        done?.Invoke(placed > 0 ? $"built: {way.Style} at {way.X}, {way.Z} facing {way.Facing} ({placed} blocks)" : $"already standing: {way.Style} at {way.X}, {way.Z}");
    }

    // ================= The test command =================

    private void RegisterWayBackCommand(ICoreServerAPI api)
    {
        IChatCommand command = api.ChatCommands.Get("backrooms");
        if (command == null) return;
        CommandArgumentParsers parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("wayback")
                .WithDescription("(Dev test) Goes through the threshold block of a kind (door, elevator, tunneldoor, basement, ...) at x z as someone standing beside it would, the first time or again: "
                    + "then sees to the door or elevator built as its way back where it comes out (or the thin spot), tries that way back, and writes the blocks round the arrival to ModData/backrooms/wayback-<kind>-x-z.txt. "
                    + "Kind sim-door or sim-elevator with a level and a number instead of x z: a made-up door or elevator into that level (the harness's `wayback` mode), with the spawn as home; "
                    + "simblocked-door or simblocked-elevator: the same with a chest put in the wall first, so the way back cannot be built")
                .WithArgs(parsers.Word("kind"), parsers.Int("x"), parsers.Int("z"))
                .HandleWith(args =>
                {
                    string kind = (args[0] as string)?.Trim();
                    int x = (int)args[1], z = (int)args[2];
                    IServerPlayer player = args.Caller.Player as IServerPlayer;
                    int group = args.Caller.FromChatGroupId;
                    TextCommandResult result = WayBackTest(kind, x, z, text =>
                    {
                        sapi.Logger.Notification("[backrooms] wayback {0} {1} {2}: {3}", kind, x, z, text);
                        player?.SendMessage(group, text, EnumChatType.CommandSuccess);
                    });
                    return result;
                })
            .EndSubCommand();
    }

    private TextCommandResult WayBackTest(string kind, int x, int z, Action<string> report)
    {
        if (network == null || kind == null) return TextCommandResult.Error("This is not a Backrooms world");
        Passage passage;
        Link home;
        bool blocked = kind.StartsWith("simblocked-");
        if (kind.StartsWith("sim"))
        {
            // A made-up door or elevator into level x (number z), from far outside the world, as the harness's own
            int level = x, n = z;
            bool elevator = kind.EndsWith("elevator");
            passage = new Passage
            {
                // (Each its own: a made-up door and a made-up elevator of the same number are not the same threshold)
                Source = (-4_000_000 - n, -4_000_000 - level - (elevator ? 0 : 100)), Key = (ulong)n * 7919UL + 13, TwoWay = true,
                WayBack = elevator ? WayBackKind.Elevator : WayBackKind.Door,
                Find = k => layout.FindArrival(level, k) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : null,
            };
            EntityPos spawn = sapi.World.DefaultSpawnPosition;
            home = new Link(spawn.X, spawn.Y, spawn.Z, false);
        }
        else
        {
            passage = network.Used(x, z, kind, out string refusal);
            if (passage == null) return TextCommandResult.Error($"The {kind} at {x}, {z} leads nowhere ({refusal})");
            int from = geometry.FloorFor(layout.TileAt(x, z).Level);
            home = network.HomeBeside(passage.Source) ?? new Link(x + 0.5, from + StandHeight, z + 0.5, false);
        }
        bool known = network.TryGet(passage.Source, out Link before);
        // (Once written down, the way home is what was written)
        if (known && network.WayBackOf(passage.Source) is { } old && network.TryGet(old.Tiles[0], out Link written)) home = written;
        else if (known && before.Marker && network.TryGet(((int)Math.Floor(before.X), (int)Math.Floor(before.Z)), out Link spot)) home = spot;
        if (network.Take(passage, home) is not { } to) return TextCommandResult.Error($"The {kind} at {x}, {z} found nowhere to lead");
        WayBack? way = network.WayBackOf(passage.Source);
        string head = $"{kind} at {x}, {z} (source {passage.Source.X}, {passage.Source.Z}, {(known ? "written down before" : "first time")}, way back kind {passage.WayBack}) leads to "
            + $"{to.X:0.0}, {to.Y:0.0}, {to.Z:0.0} in level {layout.TileAt((int)Math.Floor(to.X), (int)Math.Floor(to.Z)).Level}: "
            + (way is { } w ? $"way back {w.Style} at {w.X}, {w.Z} facing {w.Facing}" : to.Marker ? "thin spot" : passage.TwoWay ? "beside a threshold of its kind" : "one way");
        // Load where it leads (and its neighbours: the wall may be over a chunk's edge), then build and look
        int ax = (int)Math.Floor(to.X), az = (int)Math.Floor(to.Z), pending = 0;
        int floor = geometry.FloorFor(layout.TileAt(ax, az).Level);
        void Ready()
        {
            if (--pending > 0) return;
            void Look(string built)
            {
                // (As it is now: a way back that could not be built is a thin spot's link)
                Link now = network.TryGet(passage.Source, out Link current) ? current : to;
                string back = TryWayBack(passage, now, home);
                string file = WriteWayBackDump(kind, x, z, head, built, back, now, network.WayBackOf(passage.Source));
                report($"{head}; {built}; {back}; blocks in {file}");
            }
            if (blocked && network.WayBackOf(passage.Source) is { } inWay && sapi.World.GetBlock(new AssetLocation("game:chest-east")) is { } chest)
            {
                // Something of someone's in the wall where the way back would go: it stays
                var at = new BlockPos(inWay.X, floor + 1, inWay.Z);
                sapi.World.BlockAccessor.SetBlock(chest.BlockId, at);
                if (sapi.World.BlockAccessor.GetBlockEntity(at) == null) sapi.World.BlockAccessor.SpawnBlockEntity(chest.EntityClass, at);
            }
            if (network.WayBackOf(passage.Source) != null) BuildWayBack(null, passage.Source, 0, Look);
            else
            {
                if (to.Marker) LeaveThinSpot(to);
                Look(to.Marker ? "thin spot left" : "nothing to build");
            }
        }
        var columns = new HashSet<(int, int)>();
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                columns.Add(((ax + dx * 8) / GlobalConstants.ChunkSize, (az + dz * 8) / GlobalConstants.ChunkSize));
        columns.RemoveWhere(c => sapi.World.BlockAccessor.GetChunk(c.Item1, floor / GlobalConstants.ChunkSize, c.Item2) != null);
        if (columns.Count == 0)
        {
            pending = 1;
            Ready();
            return TextCommandResult.Success(head);
        }
        pending = columns.Count;
        foreach ((int cx, int cz) in columns)
            sapi.WorldManager.LoadChunkColumnPriority(cx, cz, new ChunkLoadOptions { OnLoaded = Ready });
        return TextCommandResult.Success(head + "; loading it, see the log");
    }

    private const double StandHeight = ThresholdNetwork.StandHeight;

    /// <summary>Goes back the way it came, as someone using the way back would: by the block standing there, its own kind.</summary>
    private string TryWayBack(Passage passage, Link to, Link home)
    {
        if (network.WayBackOf(passage.Source) is { } way)
        {
            var results = new List<string>();
            int level = layout.TileAt(way.X, way.Z).Level;
            (int X, int Z)[] tiles = way.Tiles;
            for (int leaf = 0; leaf < tiles.Length; leaf++)
            {
                (int x, int z) = tiles[leaf];
                for (int rel = 1; rel <= WayBackHeight(way.Style); rel++)
                {
                    var pos = new BlockPos(x, geometry.FloorFor(level) + rel, z);
                    Block block = sapi.World.BlockAccessor.GetBlock(pos);
                    // (A lift's header, or a cage's dial, is no threshold, as on the level's own lifts)
                    if (block.GetBehavior<BlockBehaviorThreshold>() is not { } threshold) { results.Add($"leaf {leaf} rel {rel} ({block.Code.Path}, no threshold)"); continue; }
                    Passage back = network.Used(x, z, threshold.Kind, out string refusal);
                    Link? there = back == null ? null : network.Take(back, null);
                    results.Add(there == home ? $"leaf {leaf} rel {rel} ({threshold.Kind}) leads home" : $"leaf {leaf} rel {rel} ({threshold.Kind}) leads to {there?.ToString() ?? refusal}, NOT home");
                }
            }
            return "way back: " + string.Join(", ", results);
        }
        if (to.Marker)
        {
            int x = (int)Math.Floor(to.X), z = (int)Math.Floor(to.Z);
            Passage spot = network.Used(x, z, "thinspot", out _);
            return spot != null && network.Take(spot, null) == home ? "way back: the thin spot leads home" : "way back: the thin spot does NOT lead home";
        }
        return "way back: (none to try here)";
    }

    /// <summary>The blocks round an arrival, layer by layer from the floor up, as a map of letters with a key.</summary>
    private string WriteWayBackDump(string kind, int x, int z, string head, string built, string back, Link to, WayBack? way)
    {
        const int r = 5;
        int ax = (int)Math.Floor(to.X), az = (int)Math.Floor(to.Z);
        int level = layout.TileAt(ax, az).Level;
        int floor = geometry.FloorFor(level);
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        var key = new Dictionary<string, char> { ["game:air"] = '.' };
        const string symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#$%&*+=?";
        var text = new StringBuilder();
        text.AppendLine(head).AppendLine(built).AppendLine(back);
        text.AppendLine($"arrival {ax}, {az} (marked with brackets on each layer), level {level}, floor y {floor}; x runs {ax - r}..{ax + r} left to right, z {az - r}..{az + r} top to bottom (north up)");
        if (way is { } w) text.AppendLine($"way back tiles: {string.Join(" ", Array.ConvertAll(w.Tiles, t => $"{t.X},{t.Z}"))}");
        for (int rel = 0; rel <= 4; rel++)
        {
            text.AppendLine().AppendLine($"rel {rel} (y {floor + rel}):");
            for (int dz = -r; dz <= r; dz++)
            {
                var line = new StringBuilder();
                for (int dx = -r; dx <= r; dx++)
                {
                    Block b = blocks.GetBlock(new BlockPos(ax + dx, floor + rel, az + dz));
                    string code = b.Code?.ToString() ?? "?";
                    if (!key.TryGetValue(code, out char c)) key[code] = c = key.Count - 1 < symbols.Length ? symbols[key.Count - 1] : '~';
                    bool here = dx == 0 && dz == 0;
                    line.Append(here ? '[' : ' ').Append(c).Append(here ? ']' : ' ');
                }
                text.AppendLine(line.ToString());
            }
        }
        text.AppendLine().AppendLine("key:");
        foreach ((string code, char c) in key) text.AppendLine($"  {c} {code}");
        string dir = Path.Combine(GamePaths.DataPath, "ModData", "backrooms");
        Directory.CreateDirectory(dir);
        string path = Path.Combine(dir, $"wayback-{kind}-{x}-{z}.txt");
        File.WriteAllText(path, text.ToString());
        return path;
    }
}
