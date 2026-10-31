using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Cheats;

/// <summary>
/// <c>/backrooms stairscan</c> (dev test, works from the console): finds every flight of stairs round some spots of a
/// level and walks the player's box (0.6 x 1.85, stepping up 0.6, as the game's player does) up each one, along the
/// centre of each lane of steps, on the blocks' real collision boxes. A flight fails when the box cannot be put at the
/// height of the step it would stand on: something solid (a ceiling, a beam, a header, a lamp) lies in the 1.85 above
/// the step, or a step is too high to climb. One line per failing flight, a summary per block kind.
/// <list type="bullet">
/// <item><c>stairscan &lt;level&gt; [sites] [radius]</c>: sites arrival spots (every other one picked beside a Level 1/4/5
/// stair tile where there is one), a square of radius blocks round each (default 6 sites, 40 blocks);</item>
/// <item><c>stairscan at x z [radius]</c> and <c>stairscan here [radius]</c> (a player): one spot, default radius 40 and 24.</item>
/// </list>
/// The first call only starts loading the chunks; run it again until it stops saying so. The full report is also in
/// the server log (lines starting <c>[backrooms] stairscan</c>).
/// </summary>
public partial class CheatSystem
{
    private const double ScanBoxWidth = 0.6, ScanBoxHeight = 1.85, ScanStepHeight = 0.6, ScanEps = 1e-4;

    private void RegisterStairScan(IChatCommand command, CommandArgumentParsers parsers)
    {
        command
            .BeginSubCommand("stairscan")
                .WithDescription("Dev test: walks the player's box (0.6 x 1.85, step 0.6) up every flight of stairs round some spots of a level on the real collision boxes and reports the flights it cannot climb (no headroom). Args: <level> [sites] [radius], or: at x z [radius], or: here [radius]. The first try only loads the chunks; run it again")
                .WithArgs(parsers.Word("level|at|here"), parsers.OptionalInt("a", -1), parsers.OptionalInt("b", -1), parsers.OptionalInt("c", -1))
                .HandleWith(OnStairScan)
            .EndSubCommand();
    }

    private readonly record struct StairKind(int Dx, int Dz);

    private readonly Dictionary<int, StairKind?> stairKinds = new();

    /// <summary>Whether a block is a step (a directional block of two levels of collision box), and the way it climbs.</summary>
    private StairKind? StairOf(Block block)
    {
        if (block == null || block.Id == 0) return null;
        lock (stairKinds)
        {
            if (stairKinds.TryGetValue(block.Id, out StairKind? known)) return known;
            StairKind? kind = null;
            string path = block.Code?.Path ?? "";
            if ((path.Contains("stair") || path.Contains("escalator")) && !path.Contains("sign") && !path.Contains("door")
                && !path.Contains("window") && block.CollisionBoxes is { Length: > 0 } allBoxes)
            {
                // (A balustrade standing taller than the block is not the step: house stairs carry one on their open side)
                Cuboidf[] boxes = allBoxes.Where(b => b.Y2 <= 1.001f).ToArray();
                if (boxes.Length == 0) boxes = allBoxes;
                float top = boxes.Max(b => b.Y2), low = boxes.Min(b => b.Y2);
                if (top - low > 0.2f)
                {
                    var high = boxes.Where(b => b.Y2 > top - 0.01f).ToArray();
                    double hx = high.Average(b => (b.X1 + b.X2) / 2) - 0.5, hz = high.Average(b => (b.Z1 + b.Z2) / 2) - 0.5;
                    if (Math.Abs(hx) >= Math.Abs(hz) && Math.Abs(hx) > 0.1) kind = new StairKind(Math.Sign(hx), 0);
                    else if (Math.Abs(hz) > 0.1) kind = new StairKind(0, Math.Sign(hz));
                }
            }
            stairKinds[block.Id] = kind;
            return kind;
        }
    }

    private sealed class ScanFlight
    {
        public readonly List<List<BlockPos>> Lanes = new();
        public int Dx, Dz;
        public string Code;
    }

    private (int X, int Z)[] StairScanSites(int level, int sites, int radius)
    {
        var picked = new List<(int X, int Z)>();
        for (int i = 0; i < sites; i++)
        {
            ulong key = Hashing.Mix(0x57A1D5 + (ulong)i * 7919);
            if (layout.FindArrival(level, key) is not { } spot) continue;
            // Every other site is the nearest step of the level to that arrival that is clear of the sites already picked
            if (i % 2 == 0)
            {
                tileScanStopped = false;
                var near = NearestTileAt(spot.X, spot.Z, 1024, level, (t, x, z) => t.Stair > 0 && !picked.Any(p => Math.Abs(p.X - x) <= 2 * radius && Math.Abs(p.Z - z) <= 2 * radius), out _);
                if (near is { } stairs) spot = stairs;
            }
            if (picked.Any(p => Math.Abs(p.X - spot.X) < radius && Math.Abs(p.Z - spot.Z) < radius)) continue;
            picked.Add(spot);
        }
        return picked.ToArray();
    }

    private TextCommandResult OnStairScan(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        string what = ((string)args[0]).ToLowerInvariant();
        int a = (int)args[1], b = (int)args[2], c = (int)args[3];
        int level, radius;
        (int X, int Z)[] sites;
        if (what == "here")
        {
            var pos = args.Caller.Entity?.Pos;
            if (pos == null) return TextCommandResult.Error("From the console, use: stairscan at x z [radius]");
            radius = a > 0 ? a : 24;
            sites = new[] { ((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)) };
            level = layout.LevelAt(WorldLayout.MacroOf(sites[0].X), WorldLayout.MacroOf(sites[0].Z));
        }
        else if (what == "at")
        {
            if (a == -1 && b == -1) return TextCommandResult.Error("Use: stairscan at x z [radius]");
            radius = c > 0 ? c : 40;
            sites = new[] { (a, b) };
            level = layout.LevelAt(WorldLayout.MacroOf(a), WorldLayout.MacroOf(b));
        }
        else
        {
            level = WorldLayout.FromDisplayName(what);
            if (level < 0) return TextCommandResult.Error($"There is no Level {what} here ({BackroomsModSystem.LevelList})");
            radius = b > 0 ? b : 40;
            sites = StairScanSites(level, a > 0 ? a : 6, radius);
            if (sites.Length == 0) return TextCommandResult.Error($"Found nowhere to look in Level {WorldLayout.DisplayNumber(level)}");
        }

        // Load every column of every site (the first tries only start that)
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int bottom = geometry.BandBottomFor(level), top = geometry.BandTopFor(level);
        int probeY = geometry.FloorFor(level) + 1;
        var columns = new HashSet<(int, int)>();
        foreach (var (sx, sz) in sites)
            for (int cz = (sz - radius - 1) >> 5; cz <= (sz + radius + 1) >> 5; cz++)
                for (int cx = (sx - radius - 1) >> 5; cx <= (sx + radius + 1) >> 5; cx++) columns.Add((cx, cz));
        int notReady = 0;
        foreach (var (cx, cz) in columns)
        {
            if (ba.GetChunkAtBlockPos(cx * 32 + 1, probeY, cz * 32 + 1) != null) continue;
            sapi.WorldManager.LoadChunkColumn(cx, cz, true);
            notReady++;
        }
        if (notReady > 0) return TextCommandResult.Success($"stairscan: {notReady} of {columns.Count} chunk columns are loading; run it again in a moment");

        string levelName = "L" + WorldLayout.DisplayNumber(level);
        var seenFirst = new HashSet<long>();
        var report = new StringBuilder();
        var perKind = new SortedDictionary<string, (int Flights, int Fail, int Partial)>();
        var failLines = new List<string>();
        int trips = 0, deadEnds = 0, flightsTotal = 0, failTotal = 0, partialTotal = 0, lanesTotal = 0;
        var tmp = new BlockPos(0);
        foreach (var (sx, sz) in sites)
        {
            // Every step in the square
            var steps = new Dictionary<long, (BlockPos Pos, StairKind Kind, string Code)>();
            for (int x = sx - radius; x <= sx + radius; x++)
                for (int z = sz - radius; z <= sz + radius; z++)
                    for (int y = bottom; y <= top; y++)
                    {
                        tmp.Set(x, y, z);
                        Block block = ba.GetBlock(tmp);
                        if (block.Id == 0) continue;
                        if (StairOf(block) is not { } kind) continue;
                        steps[PosKey(x, y, z)] = (new BlockPos(x, y, z), kind, block.Code.ToShortString());
                    }

            // Lanes: chains of steps one up and one along
            var lanes = new List<(List<BlockPos> Cells, StairKind Kind, string Code)>();
            foreach (var (key, s) in steps)
            {
                if (steps.TryGetValue(PosKey(s.Pos.X - s.Kind.Dx, s.Pos.Y - 1, s.Pos.Z - s.Kind.Dz), out var before) && before.Kind == s.Kind) continue;
                var cells = new List<BlockPos> { s.Pos };
                var at = s;
                while (steps.TryGetValue(PosKey(at.Pos.X + at.Kind.Dx, at.Pos.Y + 1, at.Pos.Z + at.Kind.Dz), out var next) && next.Kind == s.Kind) { cells.Add(next.Pos); at = next; }
                lanes.Add((cells, s.Kind, s.Code));
            }

            // Flights: lanes side by side that start level with one another
            var flights = new List<ScanFlight>();
            foreach (var lane in lanes.OrderBy(l => l.Cells[0].Y).ThenBy(l => l.Cells[0].X).ThenBy(l => l.Cells[0].Z))
            {
                BlockPos s0 = lane.Cells[0];
                ScanFlight home = flights.FirstOrDefault(f => f.Dx == lane.Kind.Dx && f.Dz == lane.Kind.Dz && f.Lanes.Any(o =>
                    o[0].Y == s0.Y && (lane.Kind.Dx != 0 ? o[0].X == s0.X && Math.Abs(o[0].Z - s0.Z) == 1 : o[0].Z == s0.Z && Math.Abs(o[0].X - s0.X) == 1)));
                if (home == null) flights.Add(home = new ScanFlight { Dx = lane.Kind.Dx, Dz = lane.Kind.Dz, Code = lane.Code });
                home.Lanes.Add(lane.Cells);
            }

            foreach (ScanFlight flight in flights)
            {
                if (!seenFirst.Add(PosKey(flight.Lanes[0][0].X, flight.Lanes[0][0].Y, flight.Lanes[0][0].Z))) continue;
                // A single step is a kerb, not a flight
                if (flight.Lanes.Max(l => l.Count) < 2) continue;
                string kindName = flight.Code;
                perKind.TryGetValue(kindName, out var tally);
                int failedLanes = 0;
                string firstFail = null;
                BlockPos firstPos = flight.Lanes[0][0];
                foreach (var lane in flight.Lanes)
                {
                    lanesTotal++;
                    string fail = WalkLane(ba, lane, flight.Dx, flight.Dz, levelName, level, out string detail, out bool dead, out bool trip);
                    if (dead) deadEnds++;
                    if (trip) trips++;
                    if (fail == null) continue;
                    failedLanes++;
                    if (firstFail == null) { firstFail = detail; firstPos = lane[0]; }
                }
                flightsTotal++;
                bool all = failedLanes == flight.Lanes.Count;
                if (failedLanes == 0) perKind[kindName] = (tally.Flights + 1, tally.Fail, tally.Partial);
                else
                {
                    if (all) failTotal++; else partialTotal++;
                    perKind[kindName] = (tally.Flights + 1, tally.Fail + (all ? 1 : 0), tally.Partial + (all ? 0 : 1));
                    failLines.Add(string.Format(CultureInfo.InvariantCulture, "{0} {1} flight {2} of {3} steps, {4}, lanes {5}/{6} fail: {7}",
                        levelName, all ? "FAIL" : "PARTIAL", firstPos.X + "," + firstPos.Y + "," + firstPos.Z, flight.Lanes.Max(l => l.Count), Heading(flight.Dx, flight.Dz),
                        failedLanes, flight.Lanes.Count, firstFail));
                }
            }
        }

        foreach (string line in failLines) report.Append(line).Append('\n');
        foreach (var (kind, (n, fail, partial)) in perKind)
            report.Append(string.Format("{0} kind {1}: {2} flights, {3} fail, {4} partial\n", levelName, kind, n, fail, partial));
        report.Append(string.Format("{0} stairscan: {1} sites, radius {2}, {3} flights checked ({4} lanes), {5} failing, {6} partly failing, {7} lanes end against a wall at the top, {8} lanes take a threshold before the top",
            levelName, sites.Length, radius, flightsTotal, lanesTotal, failTotal, partialTotal, deadEnds, trips));
        string text = report.ToString().TrimEnd();
        foreach (string line in text.Split('\n')) sapi.Logger.Notification("[backrooms] stairscan " + line);
        // (A reply to a player has to fit in chat)
        if (args.Caller.Player != null && failLines.Count > 12)
            text = string.Join("\n", failLines.Take(12)) + $"\n... {failLines.Count - 12} more failing flights in the server log\n" + text.Substring(text.LastIndexOf('\n') + 1);
        return TextCommandResult.Success(text);
    }

    private static long PosKey(int x, int y, int z) => ((long)(x + 4_000_000) << 40) ^ ((long)(z + 4_000_000) << 16) ^ (uint)(y + 1000);

    private static string Heading(int dx, int dz) => dx > 0 ? "east" : dx < 0 ? "west" : dz > 0 ? "south" : "north";

    /// <summary>
    /// Walks the player's box up a lane of steps along its centre from a block before the first to the far edge of the
    /// last, then two stops on the landing. Null when it gets through; otherwise a short text of where and why.
    /// </summary>
    private string WalkLane(IBlockAccessor ba, List<BlockPos> lane, int dx, int dz, string levelName, int level, out string detail, out bool deadEnd, out bool tripped)
    {
        detail = null;
        deadEnd = false;
        tripped = false;
        var thresholds = sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>();
        BlockPos first = lane[0];
        double cx0 = first.X + 0.5, cz0 = first.Z + 0.5;
        double feet = first.Y;
        double half = ScanBoxWidth / 2;
        int n = lane.Count;
        var cuboids = new List<(Cuboidd Box, BlockPos Pos, string Code)>();
        // t is in blocks along the lane from the middle of the first step, from where the box is wholly on the first step
        for (double t = -0.2; t <= n - 0.5 + 0.35 + 1e-9; t += 0.05)
        {
            double cx = cx0 + dx * t, cz = cz0 + dz * t;
            Gather(ba, cx - half, cx + half, cz - half, cz + half, feet - 1.0, feet + ScanBoxHeight + 1.0, cuboids);
            // Where the feet come to rest: the highest top the box can step up to (0.6) or the highest below
            // (Several risers under the box in a row are stepped up one after the other, as the game does tick by tick)
            double best = double.NegativeInfinity, reach = feet;
            for (int settle = 0; settle < 6; settle++)
            {
                double next = double.NegativeInfinity;
                foreach (var (box, _, _) in cuboids)
                    if (box.Y2 <= reach + ScanStepHeight + ScanEps && box.Y2 > next) next = box.Y2;
                if (double.IsNegativeInfinity(next)) break;
                best = next;
                if (next <= reach + ScanEps) break;
                reach = next;
            }
            bool landing = t > n - 0.5 + 1e-9;
            if (double.IsNegativeInfinity(best))
            {
                if (landing) break;
                continue;
            }
            // (Walking down into the dark of a flight below: the box drops on to the next surface)
            double rest = best;
            double headroom = double.PositiveInfinity, lowest = double.PositiveInfinity;
            string blocker = null;
            foreach (var (box, pos, code) in cuboids)
            {
                if (box.Y2 <= rest + ScanEps || box.Y1 >= rest + ScanBoxHeight - ScanEps) continue;
                double room = Math.Max(0, box.Y1 - rest);
                lowest = Math.Min(lowest, box.Y1);
                if (room < headroom) { headroom = room; blocker = $"{code} at {pos.X},{pos.Y},{pos.Z}"; }
            }
            if (blocker != null)
            {
                if (landing)
                {
                    // Beyond the top step the landing may simply end at a wall (the top of a stair to nowhere): that is a
                    // dead end, not a lack of headroom. A ceiling that starts above the feet but under the head is
                    if (lowest > rest + 0.05) { detail = Detail(t, n, rest, first, headroom, blocker, true); return "landing"; }
                    deadEnd = true;
                    break;
                }
                // A wall that stands on the tread, in front of the box on the last step, is where the flight ends
                if (lowest <= rest + 0.05 && t > n - 1.5) { deadEnd = true; break; }
                detail = Detail(t, n, rest, first, headroom, blocker, false);
                return "blocked";
            }
            // Where the climb takes someone somewhere else (a stairwell's trip, a staff stair), it ends: nothing above matters
            if (thresholds != null && !landing && thresholds.WalkTrips((int)Math.Floor(cx0 + dx * t), (int)Math.Floor(cz0 + dz * t), rest))
            {
                tripped = true;
                break;
            }
            feet = rest;
        }
        return null;
    }

    private static string Detail(double t, int n, double rest, BlockPos first, double headroom, string blocker, bool landing) =>
        string.Format(CultureInfo.InvariantCulture, "{0} step {1:0.0} of {2} (feet y {3:0.##}, {4:0.##} above the first tread): {5} {6:0.00} above the feet of a needed {7}, by {8}",
            landing ? "on the landing past" : "at", Math.Min(t + 1, n), n, rest, rest - first.Y, "headroom", headroom, ScanBoxHeight, blocker);

    private static void Gather(IBlockAccessor ba, double x1, double x2, double z1, double z2, double y1, double y2, List<(Cuboidd, BlockPos, string)> into)
    {
        into.Clear();
        var pos = new BlockPos(0);
        for (int x = (int)Math.Floor(x1); x <= (int)Math.Floor(x2 - 1e-9); x++)
            for (int z = (int)Math.Floor(z1); z <= (int)Math.Floor(z2 - 1e-9); z++)
                for (int y = (int)Math.Floor(y1); y <= (int)Math.Floor(y2); y++)
                {
                    pos.Set(x, y, z);
                    Block block = ba.GetBlock(pos);
                    if (block.Id == 0) continue;
                    Cuboidf[] boxes = block.GetCollisionBoxes(ba, pos);
                    if (boxes == null) continue;
                    foreach (Cuboidf b in boxes)
                    {
                        var abs = new Cuboidd(x + b.X1, y + b.Y1, z + b.Z1, x + b.X2, y + b.Y2, z + b.Z2);
                        // (Only what the box overlaps in plan)
                        if (abs.X2 <= x1 + ScanEps || abs.X1 >= x2 - ScanEps || abs.Z2 <= z1 + ScanEps || abs.Z1 >= z2 - ScanEps) continue;
                        into.Add((abs, new BlockPos(x, y, z), block.Code.ToShortString()));
                    }
                }
    }
}
