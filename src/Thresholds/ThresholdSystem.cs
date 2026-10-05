using System;
using System.Collections.Generic;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// The Backrooms' topology lies. The levels are laid out as rings, and you can walk outward through them all; but
/// the rings are only how the world is built. The game is the network of ways between them:
/// <list type="bullet">
/// <item>Elevators (Levels 3, 4 and 5) each lead to one fixed place, beside another elevator on another level, and
/// that elevator brings you back.</item>
/// <item>A few of the hotel's locked doors open after all, onto somewhere far away.</item>
/// <item>Falling into one of Level 0's pits drops you into Level 2.</item>
/// <item>Stairwells: Level 1's come out of other stairwells, or now and then in the Abandoned Office; Level 4's
/// come out of other stairwells on the same floor, or now and then back in Level 0; the hotel's staff stairs come
/// out in the dark of Level 6.</item>
/// <item>A few of Level 4's vending machines and the wires strung across Level 6's passages drop you into
/// Level 6.1, the Snackrooms. Its rusty doors lead back into Level 6, its glass doors to the offices or the hotel,
/// its vents to the Electrical Station, and its kitchen doors into another food court.</item>
/// <item>Level 6's stairs down, found by the sound of waves, come out in an entry room in the ceiling of Level 7,
/// and you fall through into the sea.</item>
/// <item>In Level 7, swim down into the circle of stones to reach Level 9, or into a cave mouth in the midnight
/// zone to reach the 9th Road in Level 8. Level 8's vents lead up into Level 2.</item>
/// <item>A gate at the end of a field behind the houses of Level 9 opens onto Level 10, and diving to the bottom
/// of one of Level 10's lakes brings you up in Level 7.</item>
/// <item>Level 11, the Endless City, is no ring: you noclip into it, through a stretch of barn wall in Level 10
/// that isn't quite there. It is the hub of the Backrooms. An office tower's elevators go to Level 4 and a hotel's
/// to Level 5; an apartment block's basement door to Level 0, a garage's ramp to Level 1, an open manhole or a
/// subway maintenance door to Level 2, a substation's door to Level 3; a dark doorway off an alley to Level 6, the
/// deep middle of a park fountain to Level 7, a fallen-in street to Level 8, a rowhouse's front door to Level 9, a
/// patch of wheat in a park to Level 10, and a diner's kitchen door to the Snackrooms.</item>
/// </list>
/// Where each one leads, which are two-way and how the way back is made is all in <see cref="ThresholdNetwork"/>;
/// this system notices players going through thresholds, moves them, and keeps the network saved with the world.
/// </summary>
public class ThresholdSystem : ModSystem
{
    private const string SaveKey = "backrooms-thresholds";
    private const int CooldownMs = 4000;
    private const int ElevatorRideMs = 1500;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private ThresholdNetwork network;
    private int thinSpotId;
    private readonly Dictionary<string, long> busyUntilMs = new();
    private readonly Dictionary<string, (int, int)> preloadedPit = new();
    // Whether each player stood in a thin spot at the last tick: stepping into one takes you back, standing in the
    // one you arrived in does not
    private readonly Dictionary<string, bool> inThinSpot = new();

    // Per-player cache of the cell they are standing in, so the tick does not rebuild it every time
    private readonly Dictionary<string, (int Mx, int Mz, Tile[] Tiles)> cellCache = new();

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsThreshold", typeof(BlockBehaviorThreshold));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            network = new ThresholdNetwork(layout, geometry, api.WorldManager.Seed);
            byte[] saved = api.WorldManager.SaveGame.GetData(SaveKey);
            if (!network.Load(saved))
            {
                // Keep what could not be read rather than overwrite it with whatever is found from now on
                api.WorldManager.SaveGame.StoreData(SaveKey + "-unreadable", saved);
                api.Logger.Error("[backrooms] The saved threshold links could not be read (kept as {0}-unreadable); thresholds will find their places again", SaveKey);
            }
            thinSpotId = api.World.GetBlock(new AssetLocation("backrooms:thinspot"))?.BlockId ?? 0;
            api.Event.GameWorldSave += () =>
            {
                if (network.Dirty) api.WorldManager.SaveGame.StoreData(SaveKey, network.Save());
            };
            api.Event.RegisterGameTickListener(OnTick, 200);
            api.Event.PlayerDisconnect += player =>
            {
                busyUntilMs.Remove(player.PlayerUID);
                cellCache.Remove(player.PlayerUID);
                preloadedPit.Remove(player.PlayerUID);
                inThinSpot.Remove(player.PlayerUID);
            };
        });
    }

    /// <summary>The level at a block position.</summary>
    public int LevelAt(BlockPos pos) => layout?.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z)) ?? -1;

    /// <summary>How many thresholds have had their destination (or their way back) written down so far.</summary>
    public int LinkCount => network?.Count ?? 0;

    // ================= Thresholds you use =================

    /// <summary>Called when a player uses a threshold block (an elevator, a door, a vent, a thin spot).</summary>
    public void Use(IServerPlayer player, BlockPos pos, string kind)
    {
        if (network == null || IsBusy(player) || !CanTravel(player)) return;
        Passage passage = network.Used(pos.X, pos.Z, kind, out string refusal);
        if (passage == null)
        {
            Play(pos, "game:sounds/effect/latch");
            string message = refusal switch
            {
                "outoforder" => "backrooms:elevator-outoforder",
                "nowhere" => "backrooms:thinspot-nowhere",
                _ => "backrooms:door-locked",
            };
            player.SendIngameError("backrooms-" + refusal, Lang.Get(message));
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 500;
            return;
        }

        // Whoever comes back this way is put down where this player is standing now
        EntityPos from = player.Entity.Pos;
        Link? destination = network.Take(passage, new Link(from.X, from.Y + 0.05, from.Z, false));
        if (destination == null)
        {
            Play(pos, "game:sounds/effect/latch");
            player.SendIngameError("backrooms-nowhere", Lang.Get("backrooms:thinspot-nowhere"));
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 2000;
            return;
        }
        if (passage.Sound != null) Play(pos, passage.Sound);
        if (kind != "elevator")
        {
            Go(player, passage, destination);
            return;
        }

        // Start loading where it goes while the car rides, and take everyone standing in it along
        Link arrival = destination.Value;
        Preload(arrival);
        List<IServerPlayer> riders = PlayersNear(player, 2.5);
        var boarded = new Dictionary<string, Vec3d>();
        foreach (IServerPlayer rider in riders)
        {
            busyUntilMs[rider.PlayerUID] = sapi.World.ElapsedMilliseconds + ElevatorRideMs + CooldownMs;
            boarded[rider.PlayerUID] = rider.Entity.Pos.XYZ;
        }
        sapi.Event.RegisterCallback(_ =>
        {
            foreach (IServerPlayer rider in riders)
            {
                // Anyone who stepped out of the car before the doors closed stays behind
                if (!CanTravel(rider) || rider.Entity.Pos.SquareDistanceTo(boarded[rider.PlayerUID]) > 2.5 * 2.5)
                {
                    busyUntilMs.Remove(rider.PlayerUID);
                    continue;
                }
                Arrive(rider, arrival);
            }
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/metaldoor"), arrival.X, arrival.Y, arrival.Z, null, randomizePitch: true, range: 16);
        }, ElevatorRideMs);
    }

    /// <summary>
    /// Called when a player presses the buttons of a vending machine. A few of Level 4's machines take whoever does
    /// to the Snackrooms, every time; returns whether this is one of them (it never serves anyone, either way).
    /// </summary>
    public bool UseVendingMachine(IServerPlayer player, BlockPos pos)
    {
        if (network == null) return false;
        Passage passage = network.Vending(pos.X, pos.Z);
        if (passage == null) return false;
        if (IsBusy(player) || !CanTravel(player)) return true;
        Link? destination = network.Take(passage, null);
        if (destination == null) return true;
        Play(pos, passage.Sound);
        Go(player, passage, destination);
        return true;
    }

    // ================= Thresholds you stumble through =================

    private void OnTick(float dt)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || !CanTravel(player) || player.Entity.Teleporting) continue;
            if (player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;

            EntityPos pos = player.Entity.Pos;
            int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);

            // Stepping into a thin spot takes you back the way it came (standing in the one you arrived in does not)
            bool thin = thinSpotId != 0 && (sapi.World.BlockAccessor.GetBlock(new BlockPos(x, (int)Math.Floor(pos.Y), z)).BlockId == thinSpotId
                || sapi.World.BlockAccessor.GetBlock(new BlockPos(x, (int)Math.Floor(pos.Y + 1), z)).BlockId == thinSpotId);
            bool wasThin = inThinSpot.GetValueOrDefault(player.PlayerUID);
            inThinSpot[player.PlayerUID] = thin;
            if (IsBusy(player)) continue;
            if (thin && !wasThin)
            {
                Use(player, new BlockPos(x, (int)Math.Floor(pos.Y), z), "thinspot");
                continue;
            }

            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            int level = layout.LevelAt(mx, mz);
            if (level is 2 or 3 or 8) continue;

            Tile tile = CellOf(player, mx, mz)[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
            double rel = pos.Y - geometry.FloorFor(level);

            if (level is 0 or 11) PreloadNearbyDrop(player, x, z, rel);

            Passage passage = network.Walked(x, z, tile, rel);
            if (passage == null) continue;
            Go(player, passage, network.Take(passage, passage.TwoWay ? network.HomeBeside(passage.Source) : null));
        }
    }

    /// <summary>
    /// Near the edge of a pit, an open manhole or a fallen-in street, start loading the place it drops into, so the
    /// fall never outlasts the trip.
    /// </summary>
    private void PreloadNearbyDrop(IServerPlayer player, int x, int z, double rel)
    {
        if (rel < -1) return;
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
            {
                Tile near = layout.TileAt(x + dx, z + dz);
                if (near.Kind != TileKind.Pit) continue;
                Passage drop = network.Walked(x + dx, z + dz, near, -100);
                if (drop == null || preloadedPit.GetValueOrDefault(player.PlayerUID, (int.MinValue, 0)) == drop.Source) return;
                preloadedPit[player.PlayerUID] = drop.Source;
                if (network.Take(drop, null) is { } below) Preload(below);
                return;
            }
    }

    private Tile[] CellOf(IServerPlayer player, int mx, int mz)
    {
        if (cellCache.TryGetValue(player.PlayerUID, out var cached) && cached.Mx == mx && cached.Mz == mz) return cached.Tiles;
        Tile[] tiles = layout.BuildMacro(mx, mz);
        cellCache[player.PlayerUID] = (mx, mz, tiles);
        return tiles;
    }

    // ================= Shared =================

    private bool Go(IServerPlayer player, Passage passage, Link? destination)
    {
        if (!Arrive(player, destination)) return false;
        if (passage.Message != null) player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(passage.Message), EnumChatType.Notification);
        return true;
    }

    /// <summary>
    /// Teleports a player to somewhere in the given level, picked by key (the <c>/backrooms goto</c> command). This
    /// is not a threshold: nothing is written down, and there is no way back.
    /// </summary>
    public bool Send(IServerPlayer player, int level, ulong key, System.Func<Tile, bool> anchor)
    {
        if (layout == null || player.Entity == null) return false;
        // Now and then the search finds nowhere to stand; try somewhere else nearby instead
        (int X, int Z)? arrival = null;
        for (int attempt = 0; attempt < 4 && arrival == null; attempt++, key = Hashing.Mix(key)) arrival = layout.FindArrival(level, key, anchor);
        if (arrival is not { } a) return Arrive(player, null);
        return Arrive(player, new Link(a.X + 0.5, geometry.FloorFor(level) + ThresholdNetwork.StandHeight, a.Z + 0.5, false));
    }

    private bool Arrive(IServerPlayer player, Link? destination)
    {
        if (destination is not { } link)
        {
            // Nowhere to go after all: don't look again for a while
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 6000;
            return false;
        }
        if (link.Marker) inThinSpot[player.PlayerUID] = true; // they arrive standing in it
        busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + CooldownMs;
        // The place is loaded (and if need be generated) before the player is moved; a thin spot, the way back
        // from a place with no threshold of its own, is left there once it is
        player.Entity.TeleportToDouble(link.X, link.Y, link.Z, link.Marker ? () => LeaveThinSpot(link) : null);
        return true;
    }

    /// <summary>Makes sure the thin spot that leads back from an arrival is there.</summary>
    private void LeaveThinSpot(Link link)
    {
        if (thinSpotId == 0) return;
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        var pos = new BlockPos((int)Math.Floor(link.X), (int)Math.Floor(link.Y), (int)Math.Floor(link.Z));
        // The arrival is clear floor; a tuft of grass or a loose stone may have been put there since
        for (int up = 0; up < 2; up++, pos.Up())
        {
            Block there = blocks.GetBlock(pos);
            if (there.BlockId == thinSpotId) return;
            if (there.BlockId != 0 && there.Replaceable < 5000) continue;
            blocks.SetBlock(thinSpotId, pos);
            return;
        }
        sapi.Logger.Warning("[backrooms] No room for the thin spot back from {0:0}, {1:0}, {2:0}", link.X, link.Y, link.Z);
    }

    /// <summary>Starts loading (and if need be generating) the chunk column around a place someone is about to arrive.</summary>
    private void Preload(Link at)
    {
        sapi.WorldManager.LoadChunkColumnPriority((int)at.X / GlobalConstants.ChunkSize, (int)at.Z / GlobalConstants.ChunkSize);
    }

    private static bool CanTravel(IServerPlayer player) =>
        player.ConnectionState == EnumClientState.Playing && player.Entity != null && player.Entity.Alive;

    /// <summary>The player and everyone else standing within the given distance of them.</summary>
    private List<IServerPlayer> PlayersNear(IServerPlayer player, double range)
    {
        var near = new List<IServerPlayer> { player };
        foreach (IPlayer other in sapi.World.AllOnlinePlayers)
        {
            if (other == player || other is not IServerPlayer sp || !CanTravel(sp) || IsBusy(sp)) continue;
            if (sp.Entity.Pos.SquareDistanceTo(player.Entity.Pos.XYZ) <= range * range) near.Add(sp);
        }
        return near;
    }

    private bool IsBusy(IServerPlayer player) =>
        busyUntilMs.TryGetValue(player.PlayerUID, out long until) && sapi.World.ElapsedMilliseconds < until;

    private void Play(BlockPos pos, string sound)
    {
        sapi.World.PlaySoundAt(new AssetLocation(sound), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, randomizePitch: true, range: 16);
    }
}

/// <summary>Makes a block a threshold: using it asks <see cref="ThresholdSystem"/> where it leads.</summary>
public class BlockBehaviorThreshold : BlockBehavior
{
    private string kind = "door";
    private WorldInteraction[] help;

    public BlockBehaviorThreshold(Block block) : base(block)
    {
    }

    public override void Initialize(Vintagestory.API.Datastructures.JsonObject properties)
    {
        base.Initialize(properties);
        kind = properties?["kind"].AsString("door") ?? "door";
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[]
        {
            new WorldInteraction
            {
                ActionLangCode = kind switch
                {
                    "elevator" => "backrooms:blockhelp-elevator",
                    "door" or "locked" => "backrooms:blockhelp-door",
                    "thinspot" => "backrooms:blockhelp-thinspot",
                    _ => "backrooms:blockhelp-exit",
                },
                MouseButton = EnumMouseButton.Right,
            },
        };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player)
        {
            sapi.ModLoader.GetModSystem<ThresholdSystem>().Use(player, blockSel.Position, kind);
        }
        return true;
    }
}
