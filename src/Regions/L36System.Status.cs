using System;
using System.Collections.Generic;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Regions;

/// <summary>
/// Level 36's flight status, server side (the 2026-11-13 flight status pass; the states, the packet and the HUD are L36Flight.cs).
/// Once a second, every player at a gate or aboard is told the state of the flight (a packet for the HUD line) and, when it
/// changes, hears a chime and reads a plain line in chat; the cabin follows the flight (windows by phase, the seatbelt sign,
/// the lights, the plane's door) through blocks swapped by name, each swap skipped silently when the block does not exist.
/// The timer is real time: the countdown's units converted by the calendar's actual speed.
/// </summary>
public partial class L36System
{
    /// <summary>One player's flight, from the doors closing (by uid in <c>flying</c>).</summary>
    private sealed class FlightRun
    {
        public long StartMs;
        public string Gate, Number;
        public int DoorX, DoorZ, Destination;
    }

    /// <summary>A gate whose plane is in flight: when it left, the state its cabin is showing and the cabin's swappable blocks.</summary>
    private sealed class GateRun
    {
        public WorldLayout.L36Gate Gate;
        public long StartMs;
        public L36State? Applied;
        public Cabin Cabin;
    }

    /// <summary>The blocks of a cabin that follow the flight: windows, the PSU strip, the ceiling, the plane's door.</summary>
    private sealed class Cabin
    {
        public readonly List<(BlockPos Pos, string Side)> Windows = new(), Psu = new(), Doors = new();
        public readonly List<BlockPos> Ceiling = new();
        public bool Any => Windows.Count + Psu.Count + Doors.Count + Ceiling.Count > 0;
    }

    /// <summary>Dev: a gate's countdown moved on (units), by gate code: /backrooms l36 count.</summary>
    private readonly Dictionary<string, long> devShift = new();
    /// <summary>The state each player was last told, and for which gate (by uid).</summary>
    private readonly Dictionary<string, (string Gate, L36State State)> seen = new();
    private readonly HashSet<string> hudOn = new();
    private readonly Dictionary<string, GateRun> gateRuns = new();
    /// <summary>Gates whose cabin has been put back to rest once since the server started (one left mid-flight by a stop).</summary>
    private readonly HashSet<string> cabinsRested = new();
    private readonly Dictionary<string, Block> blockCache = new();
    private bool? swapBlocksExist;

    // ================= Real time =================

    /// <summary>Real seconds to a countdown unit at the calendar's speed (a tenth at the default).</summary>
    private double SecPerUnit()
    {
        double rate = sapi.World.Calendar.SpeedOfTime * sapi.World.Calendar.CalendarSpeedMul;
        return 3600.0 / UnitsPerHour / Math.Max(0.01, rate);
    }

    private long Seconds(long units) => (long)Math.Ceiling(Math.Max(0, units) * SecPerUnit());

    /// <summary>Gate C32's boarding, in years of real time (its count runs at a fiftieth of the clock).</summary>
    private string DelayedYears(Flight f) => Math.Max(1, (int)Math.Round(L36Timeline.Years(DelayedSeconds(f)))).ToString();

    private long DelayedSeconds(Flight f) => (long)(f.Count * 50.0 * SecPerUnit());

    // ================= Telling the player =================

    private void ClearStatus(IServerPlayer player, string uid)
    {
        seen.Remove(uid);
        if (hudOn.Remove(uid))
            sapi.Network.GetChannel(L36ClientSystem.Channel).SendPacket(new L36StatusPacket { State = -1 }, player);
    }

    private void ForgetStatus(string uid)
    {
        seen.Remove(uid);
        hudOn.Remove(uid);
    }

    /// <summary>What the player at a gate or aboard should know now: the HUD packet every second, and the line and chime when the state changes.</summary>
    private void Report(IServerPlayer player, string uid, int x, int z, long now)
    {
        L36State state;
        string number, gateCode;
        int dest;
        long secs;
        WorldLayout.L36Gate gate = layout.L36GateAt(x, z);
        string nextNumber = null;
        long departedAgo = 0;
        if (flying.TryGetValue(uid, out FlightRun run))
        {
            long elapsed = now - run.StartMs;
            state = L36Timeline.At(elapsed);
            number = run.Number; dest = run.Destination; gateCode = run.Gate;
            secs = Math.Max(0, (L36Timeline.FlightMs - elapsed + 999) / 1000);
        }
        else
        {
            if (gate == null)
            {
                ClearStatus(player, uid);
                return;
            }
            Flight f = FlightOf(gate);
            gateCode = gate.Code; number = f.Number; dest = f.Destination;
            if (layout.TileAt(x, z).Zone is (byte)WorldLayout.L36Zone.Cabin or (byte)WorldLayout.L36Zone.Bridge) RestCabinOnce(gate);
            double sinceLeft = f.Period > 0 ? (f.Period - f.Count) * SecPerUnit() : double.MaxValue;
            if (gate.SupportGroup) { state = L36State.Delayed; secs = DelayedSeconds(f); }
            else if (sinceLeft < L36Timeline.DepartedSeconds && f.Cycle > 0)
            {
                state = L36State.Departed;
                secs = Seconds(f.Count - Boarding);
                nextNumber = f.Number;
                number = NumberOf(gate, f.Cycle - 1);
                departedAgo = (long)sinceLeft;
            }
            else if (f.Boarding) { secs = Seconds(f.Count); state = secs <= L36Timeline.FinalCallSeconds ? L36State.FinalCall : L36State.Boarding; }
            else { state = L36State.Scheduled; secs = Seconds(f.Count - Boarding); }
        }
        if (state == L36State.Departed)
        {
            // The HUD names the next flight; the chat line names the one that left
            sapi.Network.GetChannel(L36ClientSystem.Channel).SendPacket(new L36StatusPacket { State = (int)state, Number = nextNumber, Destination = dest, Gate = gateCode, Seconds = secs }, player);
        }
        else
            sapi.Network.GetChannel(L36ClientSystem.Channel).SendPacket(new L36StatusPacket { State = (int)state, Number = number, Destination = dest, Gate = gateCode, Seconds = secs }, player);
        hudOn.Add(uid);
        bool known = seen.TryGetValue(uid, out var prev);
        if (known && prev.Gate == gateCode && prev.State == state) return;
        seen[uid] = (gateCode, state);
        // (First seen at this gate: the HUD line says it; chat and chimes are for changes)
        if (!known || prev.Gate != gateCode) return;
        Announce(player, state, number, nextNumber, dest, gateCode, secs);
    }

    private void Chime(IServerPlayer player, string sound, float volume = 0.6f) =>
        Play(sound, player.Entity.Pos.X, player.Entity.Pos.Y + 1.5, player.Entity.Pos.Z, player, volume);

    private void Announce(IServerPlayer player, L36State state, string number, string nextNumber, int dest, string gate, long secs)
    {
        string clock = L36Timeline.Clock(secs);
        switch (state)
        {
            case L36State.Boarding:
                Chime(player, "chime1");
                PaBabble(player);
                Tell(player, "backrooms:l36-line-boarding", number, dest, gate, clock);
                break;
            case L36State.FinalCall:
                Chime(player, "chime2");
                PaBabble(player);
                Tell(player, "backrooms:l36-line-finalcall", number, dest, gate, secs);
                break;
            case L36State.DoorsClosed:
                Chime(player, "ding");
                Tell(player, "backrooms:l36-line-doorsclosed", number, dest, gate, clock);
                break;
            case L36State.Pushback:
                Chime(player, "pushback", 0.7f);
                Tell(player, "backrooms:l36-line-pushback", number, dest, gate, clock);
                break;
            case L36State.Takeoff:
                Chime(player, "takeoff", 0.8f);
                Tell(player, "backrooms:l36-line-takeoff", number, dest, gate, clock);
                break;
            case L36State.Climb:
                Chime(player, "chime1", 0.35f);
                Tell(player, "backrooms:l36-line-climb", number, dest, gate, clock);
                break;
            case L36State.Cruise:
                Chime(player, "ding");
                Tell(player, "backrooms:l36-line-cruise", number, dest, gate, clock);
                break;
            case L36State.Descent:
                Chime(player, "chime2");
                sapi.Event.RegisterCallback(_ => { if (player.Entity != null) Chime(player, "ding"); }, 1600);
                Tell(player, "backrooms:l36-line-descent", number, dest, gate, clock);
                break;
            case L36State.Landed:
                Chime(player, "touchdown", 0.9f);
                Tell(player, "backrooms:l36-line-landed", number, dest, gate, clock);
                break;
            case L36State.Departed:
                Tell(player, "backrooms:l36-line-departed", number, gate, nextNumber, dest, clock);
                break;
        }
    }

    /// <summary>The PA at the gate: a few words nobody can make out, after the chime.</summary>
    private void PaBabble(IServerPlayer player)
    {
        string pa = "pa" + (1 + Random.Shared.Next(3));
        sapi.Event.RegisterCallback(_ => { if (player.Entity != null) Chime(player, pa, 0.7f); }, 1800);
    }

    // ================= The cabin follows the flight =================

    /// <summary>The gate's plane has left: starts following it with its cabin (its blocks looked for when the first aboard takes off).</summary>
    private GateRun GateRunFor(WorldLayout.L36Gate gate, long now)
    {
        if (gateRuns.TryGetValue(gate.Code, out GateRun run)) return run;
        run = new GateRun { Gate = gate, StartMs = now, Cabin = ScanCabin(gate) };
        gateRuns[gate.Code] = run;
        return run;
    }

    /// <summary>Every second: each plane in flight shows its state in its cabin; one with nobody aboard goes back to rest.</summary>
    private void UpdateCabins(long now)
    {
        if (gateRuns.Count == 0) return;
        List<string> done = null;
        foreach (var (code, run) in gateRuns)
        {
            bool occupied = false;
            foreach (FlightRun f in flying.Values)
                if (f.Gate == code) { occupied = true; break; }
            if (!occupied)
            {
                ApplyCabin(run.Cabin, null);
                (done ??= new List<string>()).Add(code);
                continue;
            }
            L36State state = L36Timeline.At(now - run.StartMs);
            if (run.Applied == state) continue;
            run.Applied = state;
            ApplyCabin(run.Cabin, state);
        }
        if (done == null) return;
        foreach (string code in done) gateRuns.Remove(code);
    }

    /// <summary>A cabin a player is in that no flight is following, looked at once per server run: any left mid-flight goes back to rest.</summary>
    private void RestCabinOnce(WorldLayout.L36Gate gate)
    {
        if (gateRuns.ContainsKey(gate.Code) || !cabinsRested.Add(gate.Code)) return;
        ApplyCabin(ScanCabin(gate), null);
    }

    private bool SwapBlocksExist() => swapBlocksExist ??=
        Swap("l36-cabinwindow-roll-north") != null || Swap("l36-psu-on-north") != null || Swap("l36-ceiling-cabin-dim") != null || Swap("l36-planedoor-closed-north") != null;

    private Block Swap(string code)
    {
        if (blockCache.TryGetValue(code, out Block cached)) return cached;
        Block b = sapi.World.GetBlock(new AssetLocation("backrooms", code));
        if (b == null || b.BlockId == 0) b = null;
        blockCache[code] = b;
        return b;
    }

    /// <summary>Finds a gate's cabin and bridge blocks that follow the flight (columns of the cabin and bridge and one block round them).</summary>
    private Cabin ScanCabin(WorldLayout.L36Gate gate)
    {
        var cabin = new Cabin();
        if (!SwapBlocksExist()) return cabin;
        int w = gate.X1 - gate.X0 + 3, d = gate.Z1 - gate.Z0 + 3;
        var inside = new bool[w * d];
        for (int i = 0; i < w; i++)
            for (int j = 0; j < d; j++)
                inside[i + j * w] = layout.TileAt(gate.X0 - 1 + i, gate.Z0 - 1 + j).Zone is (byte)WorldLayout.L36Zone.Cabin or (byte)WorldLayout.L36Zone.Bridge;
        BlockPos pos = new(0, 0, 0);
        int floor = geometry.FloorFor(WorldLayout.Level36);
        IBlockAccessor ba = sapi.World.BlockAccessor;
        for (int i = 1; i < w - 1; i++)
            for (int j = 1; j < d - 1; j++)
            {
                bool near = false;
                for (int di = -1; di <= 1 && !near; di++)
                    for (int dj = -1; dj <= 1; dj++)
                        if (inside[i + di + (j + dj) * w]) { near = true; break; }
                if (!near) continue;
                for (int y = floor - 1; y <= floor + 12; y++)
                {
                    pos.Set(gate.X0 - 1 + i, y, gate.Z0 - 1 + j);
                    string path = ba.GetBlock(pos).Code?.Path;
                    if (path == null || !path.StartsWith("l36-")) continue;
                    string side = path.Substring(path.LastIndexOf('-') + 1);
                    if (path.StartsWith("l36-cabinwindow-") || path.StartsWith("l36-cabinwall-window-")) cabin.Windows.Add((pos.Copy(), side));
                    else if (path.StartsWith("l36-psu-")) cabin.Psu.Add((pos.Copy(), side));
                    else if (path.StartsWith("l36-planedoor-")) cabin.Doors.Add((pos.Copy(), side));
                    else if (path == "l36-ceiling-cabin" || path == "l36-ceiling-cabin-dim") cabin.Ceiling.Add(pos.Copy());
                }
            }
        return cabin;
    }

    /// <summary>Shows a flight state in a cabin (null: at rest, the plane at the gate).</summary>
    private void ApplyCabin(Cabin cabin, L36State? state)
    {
        if (cabin == null || !cabin.Any) return;
        bool flight = state is { } s && L36Timeline.InFlight(s);
        string windows = state switch
        {
            L36State.Takeoff => "roll", L36State.Climb => "climb", L36State.Cruise => "cruise", L36State.Descent => "descent", L36State.Landed => "ground", _ => "apron",
        };
        bool belt = flight && state != L36State.Cruise;
        bool dim = state is L36State.DoorsClosed or L36State.Pushback or L36State.Takeoff or L36State.Descent or L36State.Landed;
        foreach (var (pos, side) in cabin.Windows) Put(pos, "l36-cabinwindow-" + windows + "-" + side);
        foreach (var (pos, side) in cabin.Psu) Put(pos, "l36-psu-" + (belt ? "on" : "off") + "-" + side);
        foreach (var (pos, side) in cabin.Doors) Put(pos, "l36-planedoor-" + (flight ? "closed" : "open") + "-" + side);
        foreach (BlockPos pos in cabin.Ceiling) Put(pos, dim ? "l36-ceiling-cabin-dim" : "l36-ceiling-cabin");
    }

    private void Put(BlockPos pos, string code)
    {
        Block b = Swap(code);
        if (b == null) return;
        if (sapi.World.BlockAccessor.GetBlock(pos).BlockId != b.BlockId) sapi.World.BlockAccessor.ExchangeBlock(b.BlockId, pos);
    }

    // ================= Dev command =================

    /// <summary>/backrooms l36 board|count|fly|phase: for testing (and the client rig); works on the gate you stand in, or the nearest.</summary>
    private void RegisterDevCommand(ICoreServerAPI api)
    {
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l36")
                .WithDescription("Level 36 flights (testing), at the gate you stand in or the nearest: 'board' puts you on the bridge as the door does; 'count <seconds>' sets the gate's countdown to that many real seconds to departure (boarding opens at about 100); 'fly [seconds]' boards you into the cabin and leaves in that many seconds (default 2); 'front' puts you at the gate's door; 'phase <doorsclosed|pushback|takeoff|climb|cruise|descent|landed>' jumps your flight to that part")
                .WithArgs(api.ChatCommands.Parsers.Word("what"), api.ChatCommands.Parsers.OptionalWord("arg"))
                .RequiresPrivilege(Privilege.controlserver)
                .RequiresPlayer()
                .HandleWith(OnDevCommand)
            .EndSubCommand();
    }

    private TextCommandResult OnDevCommand(TextCommandCallingArgs args)
    {
        if (layout == null || args.Caller.Player is not IServerPlayer player || player.Entity == null) return TextCommandResult.Error("Not in a Backrooms world");
        string what = (string)args[0], arg = (args[1] as string)?.Trim();
        int px = (int)Math.Floor(player.Entity.Pos.X), pz = (int)Math.Floor(player.Entity.Pos.Z);
        long now = sapi.World.ElapsedMilliseconds;
        if (what == "phase")
        {
            if (!flying.TryGetValue(player.PlayerUID, out FlightRun run)) return TextCommandResult.Error("You are not in flight");
            if (!Enum.TryParse(arg, true, out L36State st) || !L36Timeline.InFlight(st)) return TextCommandResult.Error("A phase: doorsclosed, pushback, takeoff, climb, cruise, descent or landed");
            long start = now - L36Timeline.Start(st) - 200;
            foreach (FlightRun f in flying.Values) if (f.Gate == run.Gate) f.StartMs = start;
            if (gateRuns.TryGetValue(run.Gate, out GateRun gr)) gr.StartMs = start;
            return TextCommandResult.Success("Flight " + run.Number + " jumped to " + st);
        }
        WorldLayout.L36Gate gate = layout.L36GateAt(px, pz);
        if (gate == null)
        {
            double best = double.MaxValue;
            foreach (WorldLayout.L36Gate g in layout.L36GatesNear(px, pz, 4))
            {
                double dist = (g.DoorX - px) * (double)(g.DoorX - px) + (g.DoorZ - pz) * (double)(g.DoorZ - pz);
                if (dist < best) { best = dist; gate = g; }
            }
        }
        if (gate == null || gate.SupportGroup) return TextCommandResult.Error("No gate that boards near you");
        Flight flight = FlightOf(gate);
        switch (what)
        {
            case "board":
                Board(player, gate, flight);
                return TextCommandResult.Success("On the bridge of gate " + gate.Code);
            case "count":
                if (!double.TryParse(arg, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double secs)) return TextCommandResult.Error("Seconds to departure");
                SetCount(gate, secs);
                return TextCommandResult.Success("Gate " + gate.Code + " departs in " + secs + " s: " + FlightOf(gate).Number);
            case "fly":
                aboard[player.PlayerUID] = (gate.Code, flight.Cycle);
                Move(player, gate.AisleX, gate.AisleZ);
                double leaves = double.TryParse(arg, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double ls) ? ls : 2;
                SetCount(gate, leaves);
                return TextCommandResult.Success("Aboard gate " + gate.Code + "; it leaves in " + leaves + " s");
            case "front":
                aboard.Remove(player.PlayerUID);
                Move(player, gate.FrontX, gate.FrontZ);
                return TextCommandResult.Success("At the door of gate " + gate.Code);
        }
        return TextCommandResult.Error("board, front, count <seconds>, fly [seconds] or phase <name>");
    }

    /// <summary>Moves a gate's countdown forward (only forward, in whole cycles of the flight if need be) so it reads this many real seconds.</summary>
    private void SetCount(WorldLayout.L36Gate gate, double seconds)
    {
        Flight f = FlightOf(gate);
        long want = Math.Max(1, (long)(seconds / SecPerUnit()));
        long delta = ((f.Count - want) % f.Period + f.Period) % f.Period;
        devShift[gate.Code] = (devShift.TryGetValue(gate.Code, out long old) ? old : 0) + delta;
    }
}
