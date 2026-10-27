using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.Essentials;

namespace Backrooms.Entities;

/// <summary>
/// Pathfinding tests (dev): <c>/backrooms pathtest</c> and <c>/backrooms pathgrid</c> run the game's own A* with an
/// entity type's hitbox, step height and fall height and the search settings the Menace task uses, and say whether a
/// way was found, how many nodes it took and where the search got nearest. Works headless: the pathfinder needs no
/// entity, only loaded chunks (the first try only loads them).
/// </summary>
public partial class MenaceSystem
{
    private void RegisterPathTestCommands(ICoreServerAPI api, IChatCommand command)
    {
        var parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("pathtest")
                .WithDescription("Dev test: runs the pathfinder as an entity type would (its hitbox, step height and fall height; the Menace task's search depth 2500 unless given, 1 block of tolerance) from x z to tx tz on the floor of the level there, and reports found or not, nodes searched, path length and how near the search got. The first try may only load the chunks")
                .WithArgs(parsers.Word("entity"), parsers.Int("x"), parsers.Int("z"), parsers.Int("tx"), parsers.Int("tz"), parsers.OptionalInt("depth", 2500))
                .HandleWith(args => RunPathTests(args, false))
            .EndSubCommand()
            .BeginSubCommand("pathgrid")
                .WithDescription("Dev test: pathtest between n pairs of random floor points in the size x size square from x z (the corner), seeded, and the tally of paths found; the first failures are listed. Args: entity x z size n [depth]")
                .WithArgs(parsers.Word("entity"), parsers.Int("x"), parsers.Int("z"), parsers.Int("size"), parsers.Int("n"), parsers.OptionalInt("depth", 2500))
                .HandleWith(args => RunPathTests(args, true))
            .EndSubCommand()
            .BeginSubCommand("partypath")
                .WithDescription("Dev test: for every Level Fun party room with guests within radius of x z, runs the pathfinder as an entity type would from each guest's stand to the corridor outside each of the room's doorways (tried 3 to 6 blocks out of the door) and tallies the paths found. Args: entity x z [radius]. The first try may only load the chunks")
                .WithArgs(parsers.Word("entity"), parsers.Int("x"), parsers.Int("z"), parsers.OptionalInt("radius", 40))
                .HandleWith(RunPartyPaths)
            .EndSubCommand()
            .BeginSubCommand("blocksnear")
                .WithDescription("Dev test: the blocks standing on the floor round x z (radius, default 3) with their collision height and whether the pathfinder counts them tall (impassable), one line per cell. Args: x z [radius]")
                .WithArgs(parsers.Int("x"), parsers.Int("z"), parsers.OptionalInt("radius", 3))
                .HandleWith(args =>
                {
                    int x = (int)args[0], z = (int)args[1], r = (int)args[2];
                    var text = new System.Text.StringBuilder();
                    IBlockAccessor ba = sapi.World.BlockAccessor;
                    for (int dz = -r; dz <= r; dz++)
                        for (int dx = -r; dx <= r; dx++)
                        {
                            int fy = PathFloor(x + dx, z + dz);
                            if (fy == int.MinValue) { text.Append(string.Format("{0},{1}: no floor\n", x + dx, z + dz)); continue; }
                            var parts = new List<string>();
                            for (int h = 0; h < 2; h++)
                            {
                                Block b = ba.GetBlock(new BlockPos(x + dx, fy + h, z + dz));
                                if (b.Id == 0) continue;
                                float top = 0;
                                foreach (Cuboidf c in b.CollisionBoxes ?? System.Array.Empty<Cuboidf>()) top = Math.Max(top, c.Y2);
                                parts.Add(string.Format(CultureInfo.InvariantCulture, "y+{0} {1} top {2:0.##}{3}", h, b.Code, top, TallBlockPathing.IsTall(b) ? " TALL" : ""));
                            }
                            text.Append(string.Format("{0},{1} (floor y {2}): {3}\n", x + dx, z + dz, fy, parts.Count == 0 ? "clear" : string.Join("; ", parts)));
                        }
                    foreach (Entity e in sapi.World.GetEntitiesAround(new Vec3d(x + 0.5, PathFloor(x, z) + 1, z + 0.5), r + 12, 6, _ => true))
                        text.Append(string.Format(CultureInfo.InvariantCulture, "entity {0} at {1:0.0},{2:0.0},{3:0.0}\n", e.Code, e.Pos.X, e.Pos.Y, e.Pos.Z));
                    string result = text.ToString().TrimEnd();
                    sapi.Logger.Notification("[backrooms] blocksnear: " + result);
                    return TextCommandResult.Success(result);
                })
            .EndSubCommand()
            .BeginSubCommand("squeeze")
                .WithDescription("Dev test: the free width a Hound's squeeze rule measures at x y z (y is the floor, where the feet stand), across a walk along each axis and the speed factor that gives (AiTaskMenace.Squeeze: under 2 blocks, 60 %). Args: x y z [radius]. With a radius it surveys the square instead: for every open floor tile the tighter of the two ways, tallied by width, with a first example of each. The first try may only load the chunks")
                .WithArgs(parsers.Int("x"), parsers.Int("y"), parsers.Int("z"), parsers.OptionalInt("radius", 0))
                .HandleWith(args =>
                {
                    int x = (int)args[0], y = (int)args[1], z = (int)args[2], radius = (int)args[3];
                    if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, y, z) == null)
                    {
                        sapi.WorldManager.LoadChunkColumn(x / 32, z / 32, true);
                        return TextCommandResult.Error("The chunk is loading; try again in a moment");
                    }
                    var text = new System.Text.StringBuilder();
                    if (radius > 0)
                    {
                        // The tighter of the two ways across a tile that can be stood in (open at the feet and the head), by width
                        var tally = new SortedDictionary<double, (int Count, string First)>();
                        IBlockAccessor ba = sapi.World.BlockAccessor;
                        for (int dz = -radius; dz <= radius; dz++)
                            for (int dx = -radius; dx <= radius; dx++)
                            {
                                if (!Senses.Open(ba, new BlockPos(x + dx, y, z + dz)) || !Senses.Open(ba, new BlockPos(x + dx, y + 1, z + dz))) continue;
                                double w = Math.Min(Senses.FreeWidth(ba, x + dx + 0.5, y, z + dz + 0.5, 0), Senses.FreeWidth(ba, x + dx + 0.5, y, z + dz + 0.5, Math.PI / 2));
                                double key = Math.Round(w * 2) / 2;
                                tally.TryGetValue(key, out var seen);
                                tally[key] = (seen.Count + 1, seen.First ?? (x + dx) + " " + y + " " + (z + dz));
                            }
                        foreach (var (key, (count, first)) in tally)
                            text.Append(string.Format(CultureInfo.InvariantCulture, "tighter way about {0:0.0} wide: {1} tiles, e.g. {2}\n", key, count, first));
                        string survey = text.ToString().TrimEnd();
                        sapi.Logger.Notification("[backrooms] squeeze survey at " + x + " " + y + " " + z + ": " + survey);
                        return TextCommandResult.Success(survey);
                    }
                    // (Yaw 0 walks along +z, yaw pi/2 along +x)
                    foreach (var (name, yaw) in new[] { ("walking along z (across x)", 0.0), ("walking along x (across z)", Math.PI / 2) })
                    {
                        double w = Senses.FreeWidth(sapi.World.BlockAccessor, x + 0.5, y, z + 0.5, yaw);
                        bool narrow = w < AiTaskMenace.SqueezeWidth - 0.05;
                        text.Append(string.Format(CultureInfo.InvariantCulture, "{0}: free width {1:0.00}, speed x{2:0.00}{3}\n", name, w, narrow ? AiTaskMenace.SqueezeFactor : 1f, narrow ? " (squeezed)" : ""));
                    }
                    string result = text.ToString().TrimEnd();
                    sapi.Logger.Notification("[backrooms] squeeze at " + x + " " + y + " " + z + ": " + result);
                    return TextCommandResult.Success(result);
                })
            .EndSubCommand();
    }

    private TextCommandResult RunPartyPaths(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string code = (string)args[0];
        if (!code.Contains(':')) code = "backrooms:" + code;
        if (!types.TryGetValue(code, out EntityProperties type)) return TextCommandResult.Error("No such entity: " + code);
        PathfindSystem psys = sapi.ModLoader.GetModSystem<PathfindSystem>();
        if (psys?.astar == null) return TextCommandResult.Error("No pathfinder");
        int x = (int)args[1], z = (int)args[2], radius = (int)args[3];
        int probeY = geometry.FloorFor(layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z))) + 1;
        bool ready = true;
        for (int cz = (z - radius) / 32 - 1; cz <= (z + radius) / 32 + 1; cz++)
            for (int cx = (x - radius) / 32 - 1; cx <= (x + radius) / 32 + 1; cx++)
            {
                sapi.WorldManager.LoadChunkColumn(cx, cz, true);
                if (sapi.World.BlockAccessor.GetChunkAtBlockPos(cx * 32 + 1, probeY, cz * 32 + 1) == null) ready = false;
            }
        if (!ready) return TextCommandResult.Error("The chunks are loading; try again in a moment");

        Cuboidf box = type.SpawnCollisionBox;
        float step = 0.6f;
        if (type.Server?.BehaviorsAsJsonObj?.FirstOrDefault(b => b["code"].AsString() == "controlledphysics") is { } cp) step = cp["stepHeight"].AsFloat(0.6f);
        var report = new System.Text.StringBuilder();
        report.Append(string.Format(CultureInfo.InvariantCulture, "{0}: box {1:0.##}x{2:0.##}x{3:0.##}, step {4:0.####}\n", code, box.XSize, box.YSize, box.ZSize, step));
        int rooms = 0, doors = 0, tried = 0, found = 0, guests = 0, guestsOut = 0;
        // (A guest can leave when any doorway of its room is reachable: the pairs are the detail, the guests the verdict)
        var outOf = new Dictionary<(int, int), bool>();
        var (dxs, dzs) = (new[] { 1, -1, 0, 0 }, new[] { 0, 0, 1, -1 });
        foreach (FunRoom room in layout.FunRoomsNear(x, z, radius))
        {
            if (room.Guests == 0 || room.Spots.Count == 0) continue;
            rooms++;
            foreach (var (doorX, doorZ) in room.Doors)
            {
                doors++;
                foreach (var (sx, sz) in room.Spots)
                {
                    int sy = PathFloor(sx, sz);
                    if (sy == int.MinValue) continue;
                    string verdict = null;
                    // (Out of the room's bounds on any side: a doorway on a corner could lead out either way)
                    for (int d = 0; d < 4 && (verdict == null || verdict[0] == 'N'); d++)
                    {
                        int ox = doorX + dxs[d], oz = doorZ + dzs[d];
                        if (ox >= room.X0 && ox <= room.X1 && oz >= room.Z0 && oz <= room.Z1) continue;
                        for (int k = 3; k <= 6; k++)
                        {
                            int tx = doorX + dxs[d] * k, tz = doorZ + dzs[d] * k;
                            int ty = PathFloor(tx, tz);
                            if (ty == int.MinValue) continue;
                            List<PathNode> path = psys.astar.FindPath(new BlockPos(sx, sy, sz), new BlockPos(tx, ty, tz), 8, step, box, 10000, 1, EnumAICreatureType.LandCreature);
                            if (path != null) { verdict = "FOUND " + path.Count + " steps to " + tx + "," + tz; break; }
                            verdict = "NO PATH to " + tx + "," + tz;
                        }
                    }
                    if (verdict != null) { tried++; if (verdict[0] == 'F') found++; outOf[(sx, sz)] = outOf.TryGetValue((sx, sz), out bool was) && was || verdict[0] == 'F'; }
                    if (verdict != null) report.Append(string.Format(CultureInfo.InvariantCulture, "  room {0:x} spot {1},{2} -> door {3},{4}: {5}" + "\n", room.Key, sx, sz, doorX, doorZ, verdict));
                }
            }
        }
        guests = outOf.Count; guestsOut = outOf.Values.Count(v => v);
        report.Append(string.Format(CultureInfo.InvariantCulture, "partypath: {0} rooms, {1} doors, {2} guest-door pairs, {3} found; guests {4}, out {5}", rooms, doors, tried, found, guests, guestsOut));
        string text = report.ToString().TrimEnd();
        sapi.Logger.Notification("[backrooms] " + text);
        return TextCommandResult.Success(text);
    }

    private int PathFloor(int x, int z)
    {
        int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
        int near = geometry.FloorFor(level) + 1;
        return Senses.FindFloor(sapi.World, x, near, z, 3, 3);
    }

    private TextCommandResult RunPathTests(TextCommandCallingArgs args, bool grid)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string code = (string)args[0];
        if (!code.Contains(':')) code = "backrooms:" + code;
        if (!types.TryGetValue(code, out EntityProperties type)) return TextCommandResult.Error("No such entity: " + code);
        PathfindSystem psys = sapi.ModLoader.GetModSystem<PathfindSystem>();
        if (psys?.astar == null) return TextCommandResult.Error("No pathfinder");
        int x = (int)args[1], z = (int)args[2];
        int size = grid ? (int)args[3] : 0;
        int x2 = grid ? x + size : (int)args[3], z2 = grid ? z + size : (int)args[4];

        // Load the chunks over the area (the first try only starts that)
        int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
        int probeY = geometry.FloorFor(level) + 1;
        bool ready = true;
        for (int cz = Math.Min(z, z2) / 32 - 1; cz <= Math.Max(z, z2) / 32 + 1; cz++)
            for (int cx = Math.Min(x, x2) / 32 - 1; cx <= Math.Max(x, x2) / 32 + 1; cx++)
            {
                sapi.WorldManager.LoadChunkColumn(cx, cz, true);
                if (sapi.World.BlockAccessor.GetChunkAtBlockPos(cx * 32 + 1, probeY, cz * 32 + 1) == null) ready = false;
            }
        if (!ready) return TextCommandResult.Error("The chunks are loading; try again in a moment");

        Cuboidf box = type.SpawnCollisionBox;
        float step = 0.6f;
        const float speed = 0.054f;
        if (type.Server?.BehaviorsAsJsonObj?.FirstOrDefault(b => b["code"].AsString() == "controlledphysics") is { } cp) step = cp["stepHeight"].AsFloat(0.6f);
        int maxFall = type.FallDamage ? Math.Min(8, (int)Math.Round(3.51 / Math.Max(0.01, type.FallDamageMultiplier))) - (int)(speed * 30f) : 8;
        int depth = args.Parsers[5].IsMissing ? 2500 : (int)args[5];

        var pairs = new List<(int X, int Z, int TX, int TZ)>();
        if (grid)
        {
            var rng = new Random(12345 + x * 31 + z);
            int n = (int)args[4];
            for (int tries = 0; pairs.Count < n && tries < n * 200; tries++)
            {
                int ax = x + rng.Next(size), az = z + rng.Next(size), bx = x + rng.Next(size), bz = z + rng.Next(size);
                if (Math.Abs(ax - bx) + Math.Abs(az - bz) < 6) continue;
                if (PathFloor(ax, az) == int.MinValue || PathFloor(bx, bz) == int.MinValue) continue;
                pairs.Add((ax, az, bx, bz));
            }
        }
        else pairs.Add((x, z, x2, z2));

        var report = new System.Text.StringBuilder();
        report.Append(string.Format(CultureInfo.InvariantCulture, "{0}: box {1:0.##}x{2:0.##}x{3:0.##} (y {4:0.##}..{5:0.##}), step {6:0.####}, fall {7}, depth {8}\n", code, box.XSize, box.YSize, box.ZSize, box.Y1, box.Y2, step, maxFall, depth));
        int found = 0, listed = 0;
        long nodesFound = 0;
        foreach (var (ax, az, bx, bz) in pairs)
        {
            int ay = PathFloor(ax, az), by = PathFloor(bx, bz);
            if (ay == int.MinValue || by == int.MinValue)
            {
                report.Append(string.Format(CultureInfo.InvariantCulture, "  {0},{1} -> {2},{3}: no floor at {4}\n", ax, az, bx, bz, ay == int.MinValue ? "the start" : "the end"));
                continue;
            }
            var start = new BlockPos(ax, ay, az);
            var end = new BlockPos(bx, by, bz);
            List<PathNode> path = psys.astar.FindPath(start, end, maxFall, step, box, depth, 1, EnumAICreatureType.LandCreature);
            int checkedNodes = psys.astar.NodesChecked;
            if (path != null)
            {
                found++;
                nodesFound += checkedNodes;
                if (!grid) report.Append(string.Format(CultureInfo.InvariantCulture, "  {0},{1} -> {2},{3}: FOUND, {4} nodes searched, {5} steps for {6:0.0} blocks as the crow flies\n", ax, az, bx, bz, checkedNodes, path.Count, Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz))));
                continue;
            }
            // How near the search got
            PathNode nearest = null;
            double best = double.MaxValue;
            foreach (PathNode node in psys.astar.closedSet)
            {
                double d = Math.Abs(node.X - bx) + Math.Abs(node.Z - bz);
                if (d < best) { best = d; nearest = node; }
            }
            if (!grid || listed++ < 12)
                report.Append(string.Format(CultureInfo.InvariantCulture, "  {0},{1} -> {2},{3}: NO PATH ({4}), {5} nodes searched, nearest {6},{7} ({8} blocks off)\n", ax, az, bx, bz, checkedNodes > depth ? "gave up at the depth" : "the search ran out", checkedNodes, nearest?.X, nearest?.Z, best));
        }
        if (grid)
            report.Append(string.Format(CultureInfo.InvariantCulture, "found {0} of {1} ({2:0}%), mean nodes of the found {3:0}\n", found, pairs.Count, pairs.Count == 0 ? 0 : 100.0 * found / pairs.Count, found == 0 ? 0 : (double)nodesFound / found));
        string text = report.ToString().TrimEnd();
        sapi.Logger.Notification("[backrooms] pathtest: " + text);
        return TextCommandResult.Success(text);
    }
}
