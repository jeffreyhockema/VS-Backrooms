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
/// then touchdown, and they come off on a baggage carousel somewhere along the claim hall ("The flight lands. It's already
/// the airport again."). From inside, the door lets anyone off again until the plane leaves. The flight screens, used, list
/// the flights of the nearest gates. Gate C32's flight, 1784XBA8JLP to Level 186, is always tens of millions away.
/// </para>
/// <para>
/// <b>Time.</b> Nobody sleeps here and nobody tires: a player's awake hours are held where they were on arriving for as
/// long as they stay (hunger and thirst go on), and anyone who lies down is up again at once. The world's clock is not
/// touched; the level's clocks are blocks with no hands.
/// </para>
/// <para>Blocks marked <c>l36structure</c> (the terminal's floors, walls, windows, ceilings, doors and static) are unbreakable.</para>
/// </summary>
public class L36System : ModSystem
{
    /// <summary>How many countdown units to a game hour (ten to a real second at the default 30 game seconds a second).</summary>
    public const double UnitsPerHour = 1200;
    public const int Boarding = 1000;
    private const ulong SaltFlight = 0x2520;
    private const long FlightMs = 55_000;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private long tick;

    /// <summary>A player's awake hours, held from when they arrived (by uid).</summary>
    private readonly Dictionary<string, float> heldAwake = new();
    /// <summary>The gate and flight cycle a player boarded (by uid).</summary>
    private readonly Dictionary<string, (string Gate, long Cycle)> aboard = new();
    /// <summary>When a player in flight lands (by uid), and what has been said so far.</summary>
    private readonly Dictionary<string, (long LandMs, int Said)> flying = new();
    private readonly Dictionary<string, long> lastRefusal = new();

    private static readonly int[] Destinations = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 37, 94, 188, 974, 3999, 6, 4, 2, 11 };

    public override double ExecuteOrder() => 1.3;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsL36GateDoor", typeof(BlockBehaviorL36GateDoor));
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
        });
    }

    /// <summary>The level's handbook page (tools/gen_guide.py's "level36"), after The Levels: Beyond the Rings, in a Backrooms world.</summary>
    public override void StartClientSide(ICoreClientAPI api)
    {
        api.ModLoader.GetModSystem<ModSystemSurvivalHandbook>().OnInitCustomPages += pages =>
        {
            if (api.World?.Config == null || !BackroomsWorld.IsBackroomsClimate(api.World.Config)) return;
            if (pages.Exists(p => p.PageCode == "backrooms-level36")) return;
            int after = pages.FindIndex(p => p.PageCode == "backrooms-farlevels");
            var page = new GuiHandbookTextPage { pageCode = "backrooms-level36", Title = "backrooms:guide-level36-title", Text = "backrooms:guide-level36-text" };
            page.Init(api);
            if (after < 0) pages.Add(page);
            else pages.Insert(after + 1, page);
        };
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
        lastRefusal.Remove(player.PlayerUID);
    }

    // ================= The flights =================

    /// <summary>A gate's flight now: its countdown, which flight of the gate's it is, its number and where it says it goes.</summary>
    public readonly record struct Flight(long Count, long Cycle, string Number, int Destination, bool Boarding);

    public Flight FlightOf(WorldLayout.L36Gate gate)
    {
        long units = (long)(sapi.World.Calendar.TotalHours * UnitsPerHour);
        if (gate.SupportGroup) return new Flight(Math.Max(1, 94_612_753 - units / 50), 0, "1784XBA8JLP", 186, false);
        ulong h = Hashing.Hash((ulong)sapi.World.Seed, gate.DoorX, gate.DoorZ, SaltFlight);
        long period = 6000 + (long)(h % 30000), phase = (long)(h >> 20) % period;
        long cycle = (units + phase) / period, count = period - (units + phase) % period;
        ulong c = Hashing.Hash((ulong)sapi.World.Seed, (int)cycle, gate.DoorX ^ gate.DoorZ, SaltFlight + 1);
        string number = (1000 + (int)(c % 9000)).ToString() + (char)('A' + (int)(c / 9000 % 26)) + (char)('A' + (int)(c / 234000 % 26));
        return new Flight(count, cycle, number, Destinations[(int)(c / 6084000 % (ulong)Destinations.Length)], count <= Boarding);
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
            Tell(player, gate.SupportGroup ? "backrooms:l36-gate-c32" : "backrooms:l36-gate-waiting", gate.Code, flight.Number, flight.Destination, flight.Count.ToString("N0"));
            return;
        }
        aboard[player.PlayerUID] = (gate.Code, flight.Cycle);
        Play("boarding", player.Entity.Pos.X, player.Entity.Pos.Y + 1, player.Entity.Pos.Z, null, 0.8f);
        Move(player, gate.AisleX, gate.AisleZ);
        Tell(player, "backrooms:l36-board", flight.Number, flight.Destination, gate.Code, flight.Count.ToString("N0"));
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
            string status = Say.T(player, f.Boarding ? "backrooms:l36-status-boarding" : f.Count < 5000 ? "backrooms:l36-status-soon" : "backrooms:l36-status-scheduled");
            sb.Append('\n').Append(Say.T(player, "backrooms:l36-screen-row", f.Number, f.Destination, g.Code, f.Count.ToString("N0"), status));
        }
        player.SendMessage(GlobalConstants.GeneralChatGroup, sb.ToString(), EnumChatType.Notification);
    }

    // ================= Every second =================

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
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
                continue;
            }
            HoldTime(player, uid, now);
            Fly(player, uid, x, z, now);
        }
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

    /// <summary>Aboard a plane when its count runs out: the flight, and then the carousel.</summary>
    private void Fly(IServerPlayer player, string uid, int x, int z, long now)
    {
        if (flying.TryGetValue(uid, out var flight))
        {
            int said = flight.Said;
            long left = flight.LandMs - now;
            if (said == 0 && left < FlightMs - 15_000) { Tell(player, "backrooms:l36-cruise"); said = 1; }
            if (said == 1 && left < 12_000) { Tell(player, "backrooms:l36-descent"); Play("ding", player.Entity.Pos.X, player.Entity.Pos.Y + 1.5, player.Entity.Pos.Z, player); said = 2; }
            if (said == 2 && left < 4_000) { Play("touchdown", player.Entity.Pos.X, player.Entity.Pos.Y + 1, player.Entity.Pos.Z, player); said = 3; }
            flying[uid] = (flight.LandMs, said);
            if (left > 0) return;
            flying.Remove(uid);
            aboard.Remove(uid);
            ulong key = Hashing.Hash((ulong)sapi.World.Seed, (int)(now / 1000), uid.GetHashCode(), SaltFlight + 2);
            if (layout.FindArrival(WorldLayout.Level36, key) is { } landing) Move(player, landing.X, landing.Z);
            Play("clunk", player.Entity.Pos.X, player.Entity.Pos.Y + 1, player.Entity.Pos.Z);
            Tell(player, "backrooms:l36-landed");
            return;
        }
        if (!Aboard(x, z))
        {
            aboard.Remove(uid);
            return;
        }
        WorldLayout.L36Gate gate = layout.L36GateAt(x, z);
        if (gate == null) return;
        Flight f = FlightOf(gate);
        // (Aboard with no boarding remembered, after a restart: counted as boarded on this flight)
        if (!aboard.TryGetValue(uid, out var boarded) || boarded.Gate != gate.Code) aboard[uid] = boarded = (gate.Code, f.Cycle);
        if (f.Cycle <= boarded.Cycle || gate.SupportGroup) return;
        flying[uid] = (now + FlightMs, 0);
        Play("ding", player.Entity.Pos.X, player.Entity.Pos.Y + 1.5, player.Entity.Pos.Z, player);
        Tell(player, "backrooms:l36-takeoff", f.Number);
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
