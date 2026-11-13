using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using ProtoBuf;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Props;

/// <summary>
/// The props that work: fire alarms and the sprinklers over them, steam valves, breakers and the fuses that undo them, and
/// the alarms that make good lures (car alarms, wind-up alarm clocks, radios). The old ones are block types already in
/// every world, so they are given their workings at load time (<see cref="AssetsFinalize"/> appends a behaviour to each,
/// on both sides), and whatever has to last is kept in the world's save data (the tripped breakers) or by a block entity
/// of a new block (the alarm clock). Each makes a noise where it is, on the director's noise bus, and whatever hunts by
/// ear comes to see what it was (<see cref="MenaceSystem.RaiseNoise"/>).
/// </summary>
public partial class PropSystem : ModSystem
{
    public const string ChannelName = "backrooms-props";

    /// <summary>The server's instance (behaviours and the alarm clock call it); null on a client.</summary>
    public static PropSystem Server { get; private set; }

    private ICoreServerAPI sapi;
    private ICoreClientAPI capi;
    private MenaceSystem director;
    private IServerNetworkChannel serverChannel;
    private long tickListener, slowListener;

    // After BackroomsModSystem (1.0, which makes /backrooms) and MenaceSystem (1.1); before ProtectionSystem (1.2), whose
    // Breakdown reads the drops in AssetsFinalize: an alarm clock given by a nightstand is then something carried off and
    // set down again (it comes back whole), not part of the building
    public override double ExecuteOrder() => 1.15;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsFireAlarm", typeof(BlockBehaviorFireAlarm));
        api.RegisterBlockBehaviorClass("BackroomsSteamValve", typeof(BlockBehaviorSteamValve));
        api.RegisterBlockBehaviorClass("BackroomsBreaker", typeof(BlockBehaviorBreaker));
        api.RegisterBlockBehaviorClass("BackroomsCarAlarm", typeof(BlockBehaviorCarAlarm));
        api.RegisterBlockBehaviorClass("BackroomsRadio", typeof(BlockBehaviorRadio));
        api.RegisterBlockClass("BackroomsAlarmClock", typeof(BlockAlarmClock));
        api.RegisterBlockEntityClass("BackroomsAlarmClock", typeof(BlockEntityAlarmClock));
        api.Network.RegisterChannel(ChannelName).RegisterMessageType<PropFxPacket>();
    }

    // ================= Behaviours on the old blocks =================

    /// <summary>Which behaviour each prop block gets, by its code (path, our domain).</summary>
    private static BlockBehavior BehaviorFor(Block block)
    {
        if (block?.Code == null || block.Code.Domain != "backrooms") return null;
        string path = block.Code.Path;
        string first = block.FirstCodePart();
        string decor = block.Variant?["decor"];
        // Fire alarms: the pull stations of Levels 1 and 4, Level 3's alarm bells, and the hotel's fire-hose cabinets (their
        // pull handle beside the hose)
        if (first is "l1deco" or "concretedeco" or "officedeco" && decor == "alarm"
            || first is "l3decoglazed" or "l3decobrick" or "l3decocinder" && decor == "alarmbell"
            || first == "hoteldeco" && decor == "firehose")
            return new BlockBehaviorFireAlarm(block);
        // Steam valves: Level 2's valve wheels and gate valves, the valve manifolds and valved tanks of Levels 2, 3 and 5,
        // the valves of Level 5's boiler halls
        if (path == "tunnelwall-valve" || path is "tunnelfitting-pipesvalve" or "tunnelfitting-riservalve"
            || first == "gaugeframe" && block.Variant?["kind"] == "valve" || first == "pressuretank" && block.Variant?["kind"] == "valved"
            || first == "plasterdeco" && decor == "valve")
            return new BlockBehaviorSteamValve(block);
        // Breakers: Level 1's breaker panels and power boxes, Level 3's knife switches and electrical panels
        if (first is "l1deco" or "concretedeco" && (decor == "breaker" || decor?.StartsWith("powerbox", StringComparison.Ordinal) == true)
            || first is "l3decoglazed" or "l3decobrick" or "l3decocinder" && decor == "knifeswitch"
            || first == "l3wallfixture" && path.EndsWith("-panel", StringComparison.Ordinal))
            return new BlockBehaviorBreaker(block);
        // Car alarms: the cars of Level 1 and the city (the corner block that draws one, and the colliders filling it out)
        if (first == "car" || path == "carcollider") return new BlockBehaviorCarAlarm(block);
        // Radios: Level 94's radio cabinets, Level 5's turntables, the T.14.R.G.'s field desk radio in Level 14
        if (first == "radiocabinet" || path == "turntable" || path.StartsWith("l14-trgdesk-radio", StringComparison.Ordinal))
            return new BlockBehaviorRadio(block);
        return null;
    }

    public override void AssetsFinalize(ICoreAPI api)
    {
        int given = 0;
        foreach (Block block in api.World.Blocks)
        {
            if (BehaviorFor(block) is not { } behavior) continue;
            Regions.BehaviorInjection.Add(block, behavior);
            given++;
        }
        int drops = AddLoot(api);
        if (api.Side == EnumAppSide.Server)
            api.Logger.Notification("[backrooms] props: {0} block types work (fire alarms, valves, breakers, cars, radios); {1} give fuses or alarm clocks", given, drops);
    }

    /// <summary>
    /// What gives a fuse or an alarm clock when broken, as a chance (an average below one): fuses where tools and spares are
    /// kept, alarm clocks by beds and on desks.
    /// </summary>
    private static readonly (string First, string Item, bool Block, float Chance)[] Loot =
    {
        ("toolbox", "fuse", false, 0.12f), ("toolshelf", "fuse", false, 0.10f), ("metalshelf", "fuse", false, 0.05f),
        ("machinecabinet", "fuse", false, 0.08f), ("machinecabinetfeed", "fuse", false, 0.08f), ("workbench", "fuse", false, 0.05f),
        ("cablespool", "fuse", false, 0.04f),
        ("nightstand", "alarmclock-north", true, 0.12f), ("dresser", "alarmclock-north", true, 0.10f),
        ("writingdesk", "alarmclock-north", true, 0.06f), ("desk", "alarmclock-north", true, 0.03f),
    };

    private static int AddLoot(ICoreAPI api)
    {
        int n = 0;
        foreach (Block block in api.World.Blocks)
        {
            if (block?.Code == null || block.Code.Domain != "backrooms" || block.Drops == null) continue;
            string first = block.FirstCodePart();
            foreach (var (code, item, isBlock, chance) in Loot)
            {
                if (code != first) continue;
                var drop = new BlockDropItemStack
                {
                    Type = isBlock ? EnumItemClass.Block : EnumItemClass.Item,
                    Code = new AssetLocation("backrooms", item),
                    Quantity = NatFloat.createUniform(chance, 0),
                };
                if (!drop.Resolve(api.World, "props loot", block.Code)) continue;
                block.Drops = block.Drops.Append(drop).ToArray();
                n++;
            }
        }
        return n;
    }

    // ================= Server =================

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        Server = this;
        serverChannel = api.Network.GetChannel(ChannelName);
        director = api.ModLoader.GetModSystem<MenaceSystem>();
        api.Event.SaveGameLoaded += LoadBreakers;
        api.Event.GameWorldSave += SaveBreakers;
        tickListener = api.Event.RegisterGameTickListener(OnTick, 200);
        slowListener = api.Event.RegisterGameTickListener(_ => CheckBreakers(), 5000);
        StartSteamPathing(api);
        RegisterCommands(api);
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Network.GetChannel(ChannelName).SetMessageHandler<PropFxPacket>(OnFx);
    }

    public override void Dispose()
    {
        if (sapi != null)
        {
            sapi.Event.SaveGameLoaded -= LoadBreakers;
            sapi.Event.GameWorldSave -= SaveBreakers;
            if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
            if (slowListener != 0) sapi.Event.UnregisterGameTickListener(slowListener);
            StopSteamPathing();
        }
        if (Server == this) Server = null;
        // (Static, so they would outlast this world into the next one opened in the same process)
        Waters = Array.Empty<(Vec3d, long)>();
        JetCells = EmptyCells;
        base.Dispose();
    }

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        TickRings(now);
        TickSprays(now);
        TickJets(now);
    }

    /// <summary>A block position as one number, for the dictionaries of cooldowns.</summary>
    internal static long Key(BlockPos pos) => ((long)(pos.X & 0x3FFFFF) << 42) | ((long)(pos.Y & 0xFFFFF) << 22) | (long)(pos.Z & 0x3FFFFF);

    private Vec3d Centre(BlockPos pos) => new(pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5);

    /// <summary>Tells a player something went wrong (or a note about the prop) in their own language; nothing for the console.</summary>
    internal static void Tell(IPlayer player, string key, params object[] args)
    {
        if (player is IServerPlayer sp) sp.SendIngameError("backrooms-props", Say.T(sp, "backrooms:" + key, args));
    }

    /// <summary>The same, as a chat line (for news rather than a refusal).</summary>
    internal static void Note(IPlayer player, string key, params object[] args)
    {
        if (player is IServerPlayer sp) sp.SendMessage(Vintagestory.API.Config.GlobalConstants.GeneralChatGroup, Say.T(sp, "backrooms:" + key, args), EnumChatType.Notification);
    }

    /// <summary>Sends an effect to every client near enough to see it.</summary>
    private void SendFx(PropFxPacket fx, Vec3d at, double range = 96)
    {
        if (serverChannel == null) return;
        foreach (IPlayer p in sapi.World.AllOnlinePlayers)
            if (p is IServerPlayer sp && sp.ConnectionState == EnumClientState.Playing && sp.Entity != null && sp.Entity.Pos.DistanceTo(at) < range)
                serverChannel.SendPacket(fx, sp);
    }

    /// <summary>Plays a sound at a block, heard for range blocks.</summary>
    private void Play(string sound, BlockPos pos, float range, float volume = 1f, bool randomPitch = false) =>
        sapi.World.PlaySoundAt(new AssetLocation(sound), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, randomPitch, range, volume);

    /// <summary>Whether a block holds nothing that stops a jet of steam or a body: air, a plant, a liquid, anything without a box.</summary>
    internal static bool Passable(IBlockAccessor ba, BlockPos pos)
    {
        Block block = ba.GetBlock(pos);
        if (block == null || block.Id == 0) return true;
        Cuboidf[] boxes = block.GetCollisionBoxes(ba, pos);
        return boxes == null || boxes.Length == 0;
    }
}

/// <summary>An effect for the clients to draw: a spray of sprinkler heads, a jet of steam, a shower of sparks.</summary>
[ProtoContract]
public class PropFxPacket
{
    public const int Spray = 0, Steam = 1, Sparks = 2;

    [ProtoMember(1)] public int Kind;
    /// <summary>Positions, three numbers each (block coordinates).</summary>
    [ProtoMember(2)] public int[] Xyz;
    [ProtoMember(3)] public int DurationMs;
    /// <summary>Steam: the way the jet goes (a BlockFacing index) and how far (blocks).</summary>
    [ProtoMember(4)] public int Dir;
    [ProtoMember(5)] public int Length;
}
