using System;
using System.Collections.Generic;
using System.Text;
using Backrooms.Needs;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// Level 36, "Airport"'s rules on the server (experimental; the layout is WorldLayout.Level36.cs, the design
/// docs/design/experimental-levels/36-plan.md).
/// <para>
/// <b>Flights.</b> Every gate has a flight, its countdown a unitless number (ten to a second of game time at the usual day
/// length), from a period and a phase of its own: when it reaches 1000 the gate is boarding, at 0 the flight leaves and the
/// next one is counted down. Using the jet-bridge door while a flight boards takes the player aboard the plane parked behind
/// it (the cabin, a sealed pocket in the apron); anyone still aboard when the count runs out flies: a minute of cabin roar,
/// then touchdown, and they come off the plane in the level the gate's flights always go to (one of six, named on the gate's
/// screen: WorldLayout.L36FlightTo), one-way, through the threshold network (kind "l36-flight", ThresholdNetwork.L36.cs), so
/// each gate's flight always comes down in the same place. From inside, the door lets anyone off again until the plane
/// leaves. The flight screens, used, list the flights of the nearest gates. Gate C32's flight, 1784XBA8JLP to Level 186, is
/// always tens of millions away.
/// </para>
/// <para>
/// <b>The restroom sinks</b> (Fandom: "Overflowing a sink ... and submerging one's head in it for a moment will transition the
/// level to Level 37"): used, a sink's tap runs and will not turn off, and it overflows for a while; held while it overflows
/// (your head under), it takes you to the Poolrooms, one-way (kind "l36-sink").
/// </para>
/// <para>
/// <b>Time.</b> Nobody sleeps here and nobody tires: a player's awake hours are held where they were on arriving for as
/// long as they stay (hunger and thirst go on), and anyone who lies down is up again at once. The world's clock is not
/// touched; the level's clocks are blocks with no hands.
/// </para>
/// <para>Blocks marked <c>l36structure</c> (the terminal's floors, walls, windows, ceilings, doors and static) are unbreakable.</para>
/// </summary>
public partial class L36System : ModSystem
{
    /// <summary>How many countdown units to a game hour (ten to a real second at the default 30 game seconds a second).</summary>
    public const double UnitsPerHour = 1200;
    public const int Boarding = 1000;
    private const ulong SaltFlight = 0x2520;
    /// <summary>How long a sink runs over once its tap is turned, and how long a head must be held under.</summary>
    private const long OverflowMs = 45_000;
    public const float DunkSeconds = 2.5f;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private long tick;

    /// <summary>A player's awake hours, held from when they arrived (by uid).</summary>
    private readonly Dictionary<string, float> heldAwake = new();
    /// <summary>The gate and flight cycle a player boarded (by uid).</summary>
    private readonly Dictionary<string, (string Gate, long Cycle)> aboard = new();
    /// <summary>The flight each player aboard has taken off on (by uid): see L36System.Status.cs.</summary>
    private readonly Dictionary<string, FlightRun> flying = new();
    /// <summary>The sinks running over (by position), and when each stops.</summary>
    private readonly Dictionary<BlockPos, long> overflowing = new();
    private readonly Dictionary<string, long> lastRefusal = new();

    public override double ExecuteOrder() => 1.3;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsL36GateDoor", typeof(BlockBehaviorL36GateDoor));
        api.RegisterBlockBehaviorClass("BackroomsL36Sink", typeof(BlockBehaviorL36Sink));
    }

    /// <summary>The terminal's structure is unbreakable; the flight screens list flights when used (both sides: behaviours added now are not sent to clients).</summary>
    public override void AssetsFinalize(ICoreAPI api)
    {
        foreach (Block block in api.World.Blocks)
        {
            string path = block?.Code?.Path;
            if (block?.Code?.Domain != "backrooms" || path == null || !path.StartsWith("l36-")) continue;
            if (block.Attributes?["l36structure"].AsBool(false) == true)
            {
                block.RequiredMiningTier = Salvage.Protection.UnbreakableTier;
                block.Resistance = 1_000_000f;
            }
            if (path.StartsWith("l36-fids-")) BehaviorInjection.Add(block, new BlockBehaviorL36Screen(block));
        }
    }

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            tick = api.Event.RegisterGameTickListener(OnTick, 1000, 500);
            api.Event.PlayerDisconnect += Forget;
            RegisterDevCommand(api);
        });
    }

    public override void Dispose()
    {
        if (sapi != null)
        {
            if (tick != 0) sapi.Event.UnregisterGameTickListener(tick);
            sapi.Event.PlayerDisconnect -= Forget;
        }
    }

    private void Forget(IServerPlayer player)
    {
        heldAwake.Remove(player.PlayerUID);
        aboard.Remove(player.PlayerUID);
        flying.Remove(player.PlayerUID);
        ForgetStatus(player.PlayerUID);
        lastRefusal.Remove(player.PlayerUID);
        BlockBehaviorL36Sink.Forget(player.PlayerUID);
    }

    // ================= The flights =================

    /// <summary>A gate's flight now: its countdown, which flight of the gate's it is, its number and where it goes (always the same level for the gate).</summary>
    public readonly record struct Flight(long Count, long Cycle, string Number, int Destination, bool Boarding, long Period = 0);

    public Flight FlightOf(WorldLayout.L36Gate gate)
    {
        long units = (long)(sapi.World.Calendar.TotalHours * UnitsPerHour);
        if (gate.SupportGroup) return new Flight(Math.Max(1, 94_612_753 - units / 50), 0, "1784XBA8JLP", 186, false);
        if (devShift.TryGetValue(gate.Code, out long shift)) units += shift;
        ulong h = Hashing.Hash((ulong)sapi.World.Seed, gate.DoorX, gate.DoorZ, SaltFlight);
        long period = 6000 + (long)(h % 30000), phase = (long)(h >> 20) % period;
        long cycle = (units + phase) / period, count = period - (units + phase) % period;
        return new Flight(count, cycle, NumberOf(gate, cycle), layout.L36FlightTo(gate), count <= Boarding, period);
    }

    /// <summary>The number of a gate's flight of a given cycle.</summary>
    private string NumberOf(WorldLayout.L36Gate gate, long cycle)
    {
        ulong c = Hashing.Hash((ulong)sapi.World.Seed, (int)cycle, gate.DoorX ^ gate.DoorZ, SaltFlight + 1);
        return (1000 + (int)(c % 9000)).ToString() + (char)('A' + (int)(c / 9000 % 26)) + (char)('A' + (int)(c / 234000 % 26));
    }

    private static void Tell(IServerPlayer player, string key, params object[] args) =>
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, key, args), EnumChatType.Notification);

    private void Play(string sound, double x, double y, double z, IServerPlayer only = null, float volume = 1f) =>
        sapi.World.PlaySoundAt(new AssetLocation("backrooms", "sounds/effect/36/" + sound), x, y, z, only, true, 24, volume);

    private void Move(IServerPlayer player, int x, int z) =>
        player.Entity.TeleportToDouble(x + 0.5, geometry.FloorFor(WorldLayout.Level36) + layout.ArrivalHeight(x, z), z + 0.5);

    private bool Aboard(int x, int z) => layout.TileAt(x, z).Zone is (byte)WorldLayout.L36Zone.Cabin or (byte)WorldLayout.L36Zone.Bridge;

    /// <summary>A jet-bridge door used: board while the flight boards, step back off the plane from inside, else the gate's count.</summary>
    public void UseDoor(IServerPlayer player, BlockPos pos)
    {
        if (layout == null || player.Entity == null) return;
        WorldLayout.L36Gate gate = layout.L36GateAt(pos.X, pos.Z);
        if (gate == null) return;
        Flight flight = FlightOf(gate);
        int px = (int)Math.Floor(player.Entity.Pos.X), pz = (int)Math.Floor(player.Entity.Pos.Z);
        if (Aboard(px, pz))
        {
            if (flying.ContainsKey(player.PlayerUID))
            {
                player.SendIngameError("backrooms-l36", Say.T(player, "backrooms:l36-door-inflight"));
                return;
            }
            aboard.Remove(player.PlayerUID);
            Move(player, gate.FrontX, gate.FrontZ);
            Play("clunk", gate.FrontX + 0.5, player.Entity.Pos.Y + 1, gate.FrontZ + 0.5);
            Tell(player, "backrooms:l36-deplane", gate.Code);
            return;
        }
        if (!flight.Boarding)
        {
            if (gate.SupportGroup) Tell(player, "backrooms:l36-gate-c32", gate.Code, flight.Number, flight.Destination, DelayedYears(flight));
            else Tell(player, "backrooms:l36-gate-waiting", gate.Code, flight.Number, flight.Destination, L36Timeline.Clock(Seconds(flight.Count - Boarding)));
            return;
        }
        Board(player, gate, flight);
    }

    /// <summary>Aboard a boarding flight: the jet bridge's start, just inside the door; the walk to the cabin is theirs.</summary>
    private void Board(IServerPlayer player, WorldLayout.L36Gate gate, Flight flight)
    {
        aboard[player.PlayerUID] = (gate.Code, flight.Cycle);
        Play("boarding", player.Entity.Pos.X, player.Entity.Pos.Y + 1, player.Entity.Pos.Z, null, 0.8f);
        Move(player, gate.BridgeX, gate.BridgeZ);
        Tell(player, "backrooms:l36-board", flight.Number, flight.Destination, gate.Code, L36Timeline.Clock(Seconds(flight.Count)));
    }

    /// <summary>A flight screen used: the flights of the nearest gates.</summary>
    public void UseScreen(IServerPlayer player, BlockPos pos)
    {
        if (layout == null) return;
        List<WorldLayout.L36Gate> gates = layout.L36GatesNear(pos.X, pos.Z, 12);
        if (gates.Count == 0)
        {
            Tell(player, "backrooms:l36-screen-empty");
            return;
        }
        var rows = new List<(Flight F, WorldLayout.L36Gate G)>();
        foreach (WorldLayout.L36Gate g in gates) rows.Add((FlightOf(g), g));
        rows.Sort((a, b) => a.F.Count.CompareTo(b.F.Count));
        var sb = new StringBuilder(Say.T(player, "backrooms:l36-screen-head"));
        for (int i = 0; i < Math.Min(6, rows.Count); i++)
        {
            var (f, g) = rows[i];
            string status = Say.T(player, g.SupportGroup ? "backrooms:l36-status-delayed" : f.Boarding && Seconds(f.Count) <= L36Timeline.FinalCallSeconds ? "backrooms:l36-status-finalcall"
                : f.Boarding ? "backrooms:l36-status-boarding" : f.Count < 5000 ? "backrooms:l36-status-soon" : "backrooms:l36-status-scheduled");
            string time = g.SupportGroup ? DelayedYears(f) : L36Timeline.Clock(Seconds(f.Count));
            sb.Append((char)10).Append(Say.T(player, "backrooms:l36-screen-row", f.Number, f.Destination, g.Code, time, status));
        }
        player.SendMessage(GlobalConstants.GeneralChatGroup, sb.ToString(), EnumChatType.Notification);
    }

    // ================= Every second =================

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        DrainSinks(now);
        foreach (IPlayer p in sapi.World.AllOnlinePlayers)
        {
            if (p is not IServerPlayer player || player.Entity == null || !player.Entity.Alive) continue;
            int x = (int)Math.Floor(player.Entity.Pos.X), z = (int)Math.Floor(player.Entity.Pos.Z);
            bool here = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) == WorldLayout.Level36
                && Math.Abs(player.Entity.Pos.Y - geometry.FloorFor(WorldLayout.Level36)) < 30;
            string uid = player.PlayerUID;
            if (!here)
            {
                heldAwake.Remove(uid);
                aboard.Remove(uid);
                flying.Remove(uid);
                ClearStatus(player, uid);
                continue;
            }
            HoldTime(player, uid, now);
            if (Fly(player, uid, x, z, now)) continue;
            Report(player, uid, x, z, now);
        }
        UpdateCabins(now);
    }

    /// <summary>No tiring here, and no sleep: the awake hours held as they were; anyone lying down is up again at once.</summary>
    private void HoldTime(IServerPlayer player, string uid, long now)
    {
        if (Needs.Needs.FatigueOn(sapi.World))
        {
            if (!heldAwake.TryGetValue(uid, out float held)) heldAwake[uid] = held = Needs.Needs.AwakeHours(player.Entity);
            if (Math.Abs(Needs.Needs.AwakeHours(player.Entity) - held) > 0.01f) Needs.Needs.SetAwakeHours(player.Entity, held);
        }
        if (player.Entity.MountedOn is IRestPlace)
        {
            player.Entity.TryUnmount();
            if (!lastRefusal.TryGetValue(uid, out long at) || now - at > 10_000)
            {
                lastRefusal[uid] = now;
                Tell(player, "backrooms:l36-nosleep");
            }
        }
    }

    /// <summary>Aboard a plane when its count runs out: the flight, and then the carousel. (What is said and shown is Report's.) True when the player left this tick.</summary>
    private bool Fly(IServerPlayer player, string uid, int x, int z, long now)
    {
        if (flying.TryGetValue(uid, out FlightRun run))
        {
            if (now - run.StartMs < L36Timeline.FlightMs) return false;
            // Not now if the player cannot travel this tick (loading, mid-teleport, in another passage): the flight waits for the next
            if (sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>() is not { } thresholds || !thresholds.CanTravelNow(player)) return false;
            flying.Remove(uid);
            aboard.Remove(uid);
            // Off the plane, wherever the gate's flights go: one-way, through the threshold network, so every flight from
            // this gate comes down in the same place (ThresholdNetwork.L36.cs)
            Play("clunk", player.Entity.Pos.X, player.Entity.Pos.Y + 1, player.Entity.Pos.Z, player);
            var door = new BlockPos(run.DoorX, geometry.FloorFor(WorldLayout.Level36) + 1, run.DoorZ);
            sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>()?.Use(player, door, "l36-flight");
            return true;
        }
        if (!Aboard(x, z))
        {
            aboard.Remove(uid);
            return false;
        }
        WorldLayout.L36Gate gate = layout.L36GateAt(x, z);
        if (gate == null) return false;
        Flight f = FlightOf(gate);
        // (Aboard with no boarding remembered, after a restart: counted as boarded on this flight)
        if (!aboard.TryGetValue(uid, out var boarded) || boarded.Gate != gate.Code) aboard[uid] = boarded = (gate.Code, f.Cycle);
        if (f.Cycle <= boarded.Cycle || gate.SupportGroup) return false;
        if (layout.TileAt(x, z).Zone != (byte)WorldLayout.L36Zone.Cabin)
        {
            // Still on the bridge when the plane leaves: the bridge pulls back, and they are put off at the door
            aboard.Remove(uid);
            Move(player, gate.FrontX, gate.FrontZ);
            Play("clunk", gate.FrontX + 0.5, player.Entity.Pos.Y + 1, gate.FrontZ + 0.5, player);
            Tell(player, "backrooms:l36-bridge-back", NumberOf(gate, boarded.Cycle), gate.Code);
            seen[uid] = (gate.Code, L36State.Departed);
            return false;
        }
        flying[uid] = new FlightRun { StartMs = now, Gate = gate.Code, DoorX = gate.DoorX, DoorZ = gate.DoorZ, Number = NumberOf(gate, boarded.Cycle), Destination = f.Destination };
        GateRunFor(gate, now);
        return false;
    }

    // ================= The restroom sinks =================

    /// <summary>A sink's tap turned: it runs and will not turn off, and the basin runs over, for a while.</summary>
    public void Overflow(IServerPlayer player, BlockPos pos, Block block)
    {
        if (block.Variant["state"] != "dry") return;
        if (sapi.World.GetBlock(BlockCodes.WithVariant(block, "state", "overflow")) is not { BlockId: not 0 } over) return;
        sapi.World.BlockAccessor.ExchangeBlock(over.BlockId, pos);
        overflowing[pos.Copy()] = sapi.World.ElapsedMilliseconds + OverflowMs;
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/water-pour"), pos.X + 0.5, pos.Y + 1, pos.Z + 0.5, null, true, 16);
        Tell(player, "backrooms:l36-sink-overflow");
    }

    /// <summary>
    /// A sink that shows as overflowing though no timer runs for it (the server restarted, or the timer was lost): it is dry again,
    /// and true is returned so the use is the tap's, not a dunk.
    /// </summary>
    public bool DrainIfStale(BlockPos pos, Block block)
    {
        if (overflowing.ContainsKey(pos)) return false;
        if (sapi.World.GetBlock(BlockCodes.WithVariant(block, "state", "dry")) is { BlockId: not 0 } dry) sapi.World.BlockAccessor.ExchangeBlock(dry.BlockId, pos);
        return true;
    }

    /// <summary>A head held under an overflowing sink: the Poolrooms, one-way, through the threshold network.</summary>
    public void Dunk(IServerPlayer player, BlockPos pos)
    {
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/environment/underwater"), pos.X + 0.5, pos.Y + 1, pos.Z + 0.5, player, true, 8);
        sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>()?.Use(player, pos, "l36-sink");
    }

    /// <summary>The sinks whose time is up stop running over (those still loaded; one left running in an unloaded chunk stays so).</summary>
    private void DrainSinks(long now)
    {
        if (overflowing.Count == 0) return;
        List<BlockPos> done = null;
        foreach (var (pos, until) in overflowing)
            if (now >= until) (done ??= new List<BlockPos>()).Add(pos);
        if (done == null) return;
        foreach (BlockPos pos in done)
        {
            overflowing.Remove(pos);
            Block block = sapi.World.BlockAccessor.GetBlock(pos);
            if (block?.Code?.Path?.StartsWith("l36-sink-overflow-") != true) continue;
            if (sapi.World.GetBlock(BlockCodes.WithVariant(block, "state", "dry")) is { BlockId: not 0 } dry) sapi.World.BlockAccessor.ExchangeBlock(dry.BlockId, pos);
        }
    }
}

/// <summary>A jet-bridge door: using it asks <see cref="L36System.UseDoor"/>.</summary>
public class BlockBehaviorL36GateDoor : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL36GateDoor(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l36-gatedoor", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
            world.Api.ModLoader.GetModSystem<L36System>()?.UseDoor(player, blockSel.Position);
        return true;
    }
}

/// <summary>A flight screen: using it asks <see cref="L36System.UseScreen"/>.</summary>
public class BlockBehaviorL36Screen : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL36Screen(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l36-screen", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
            world.Api.ModLoader.GetModSystem<L36System>()?.UseScreen(player, blockSel.Position);
        return true;
    }
}

/// <summary>
/// A restroom sink: used dry, its tap runs and the basin runs over (<see cref="L36System.Overflow"/>); held while it runs over,
/// for <see cref="L36System.DunkSeconds"/>, the head goes under (<see cref="L36System.Dunk"/>).
/// </summary>
public class BlockBehaviorL36Sink : BlockBehavior
{
    /// <summary>A little slack for lag between the client's count of the hold and the server's clock.</summary>
    private const long LagSlackMs = 750;

    /// <summary>Server side: where each player (by uid) put their head under, and when by the server's clock.</summary>
    private static readonly Dictionary<string, (BlockPos Pos, long StartMs)> under = new();

    private WorldInteraction[] dryHelp, overHelp;

    public BlockBehaviorL36Sink(Block block) : base(block)
    {
    }

    public static void Forget(string uid) => under.Remove(uid);

    private bool Over => block.Variant["state"] == "overflow";

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        dryHelp ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l36-sink-tap", MouseButton = EnumMouseButton.Right } };
        overHelp ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l36-sink-dunk", MouseButton = EnumMouseButton.Right } };
        return Over ? overHelp : dryHelp;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        bool server = world.Side == EnumAppSide.Server && byPlayer is IServerPlayer;
        if (!Over)
        {
            if (server) world.Api.ModLoader.GetModSystem<L36System>()?.Overflow((IServerPlayer)byPlayer, blockSel.Position, block);
            return false;
        }
        if (server && world.Api.ModLoader.GetModSystem<L36System>()?.DrainIfStale(blockSel.Position, block) == true) return false;
        if (server)
        {
            under[byPlayer.PlayerUID] = (blockSel.Position.Copy(), world.ElapsedMilliseconds);
            world.PlaySoundAt(new AssetLocation("game:sounds/environment/smallsplash"), blockSel.Position.X + 0.5, blockSel.Position.Y + 1, blockSel.Position.Z + 0.5, null, true, 12);
        }
        return true;
    }

    public override bool OnBlockInteractStep(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        // (The server keeps the interaction open until the client's stop arrives)
        return world.Side != EnumAppSide.Client || secondsUsed < L36System.DunkSeconds;
    }

    public override void OnBlockInteractStop(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side != EnumAppSide.Server || byPlayer is not IServerPlayer player) return;
        if (!under.Remove(player.PlayerUID, out var began)) return;
        // Held long enough: by the client's count, and (give or take the lag) by the server's own clock, at this sink
        bool held = secondsUsed >= L36System.DunkSeconds - 0.1f;
        bool timed = world.ElapsedMilliseconds - began.StartMs >= (long)(L36System.DunkSeconds * 1000) - LagSlackMs;
        if (held && timed && blockSel != null && began.Pos.Equals(blockSel.Position) && Over)
            world.Api.ModLoader.GetModSystem<L36System>()?.Dunk(player, blockSel.Position.Copy());
    }

    public override bool OnBlockInteractCancel(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        if (world.Side == EnumAppSide.Server && byPlayer != null) Forget(byPlayer.PlayerUID);
        return true;
    }
}
