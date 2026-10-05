using System;
using System.Collections.Generic;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// The Backrooms' topology lies. The levels are laid out as rings, but some thresholds put you down somewhere else
/// entirely:
/// <list type="bullet">
/// <item>Elevators (Levels 3, 4 and 5) each lead to one fixed place, usually beside another elevator on another
/// level. The trip back is rarely the same.</item>
/// <item>A few of the hotel's locked doors open after all, onto somewhere far away.</item>
/// <item>Falling into one of Level 0's pits drops you into Level 2.</item>
/// <item>Climbing a Level 4 stairwell brings you out of another stairwell on the same floor, or now and then
/// back in Level 0.</item>
/// </list>
/// Every destination is a pure function of the world seed and the threshold's position, so each one can be learnt
/// and marked on the map.
/// </summary>
public class ThresholdSystem : ModSystem
{
    private const ulong SaltElevator = 0x7E01;
    private const ulong SaltDoor = 0x7E02;
    private const ulong SaltPit = 0x7E03;
    private const ulong SaltStairs = 0x7E04;

    private const int CooldownMs = 4000;
    private const int ElevatorRideMs = 1500;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private readonly Dictionary<string, long> busyUntilMs = new();

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
            api.Event.RegisterGameTickListener(OnTick, 200);
            api.Event.PlayerDisconnect += player =>
            {
                busyUntilMs.Remove(player.PlayerUID);
                cellCache.Remove(player.PlayerUID);
            };
        });
    }

    // ================= Thresholds you use =================

    /// <summary>Called when a player uses an elevator or a locked door.</summary>
    public void Use(IServerPlayer player, BlockPos pos, string kind)
    {
        if (layout == null || IsBusy(player)) return;
        ulong seed = (ulong)sapi.World.Seed;

        if (kind == "elevator")
        {
            // Both leaves of a pair of doors belong to the same elevator
            int ex = Hashing.FloorDiv(pos.X, 4), ez = Hashing.FloorDiv(pos.Z, 4);
            ulong h = Hashing.Hash(seed, ex, ez, SaltElevator);
            int here = layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z));
            int target = ElevatorTarget(here, Hashing.Unit(h));

            Play(pos, "game:sounds/block/metaldoor");
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + ElevatorRideMs + CooldownMs;
            sapi.Event.RegisterCallback(_ => Send(player, target, h, IsElevator), ElevatorRideMs);
            return;
        }

        // A locked hotel door. Both halves of the door give the same answer.
        ulong door = Hashing.Hash(seed, pos.X, pos.Z, SaltDoor);
        double r = Hashing.Unit(door);
        if (r >= 0.06)
        {
            Play(pos, "game:sounds/effect/latch");
            player.SendIngameError("backrooms-locked", Lang.Get("backrooms:door-locked"));
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 500;
            return;
        }

        // It opens, onto somewhere else: another corridor of the hotel, the Electrical Station, or the Lobby
        double where = Hashing.Unit(Hashing.Mix(door));
        int level = where < 0.5 ? 5 : where < 0.85 ? 3 : 0;
        Play(pos, "game:sounds/block/door");
        Send(player, level, door, null);
    }

    private static int ElevatorTarget(int level, double r) => level switch
    {
        3 => r < 0.6 ? 4 : r < 0.9 ? 5 : 3,
        4 => r < 0.5 ? 5 : r < 0.75 ? 3 : 4,
        _ => r < 0.45 ? 5 : r < 0.75 ? 3 : r < 0.9 ? 4 : 1,
    };

    private static bool IsElevator(Tile t) => t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator;

    // ================= Thresholds you stumble through =================

    private void OnTick(float dt)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity == null || IsBusy(player)) continue;
            if (player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;

            EntityPos pos = player.Entity.Pos;
            int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            int level = layout.LevelAt(mx, mz);
            if (level != 0 && level != 4) continue;

            Tile tile = CellOf(player, mx, mz)[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
            ulong seed = (ulong)sapi.World.Seed;

            if (level == 0 && tile.Kind == TileKind.Pit && pos.Y < geometry.FloorY - 4)
            {
                // Falling out of Level 0: you land in the pipe tunnels of Level 2
                Send(player, 2, Hashing.Hash(seed, mx, mz, SaltPit), null);
            }
            else if (level == 4 && tile.Stair >= 1 && pos.Y >= geometry.FloorY + 1.4)
            {
                // Office stairwells loop back to the same floor... usually
                ulong h = Hashing.Hash(seed, x, z, SaltStairs);
                if (Hashing.Unit(h) < 0.8) Send(player, 4, h, t => t.Stair > 0);
                else Send(player, 0, h, null);
            }
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

    /// <summary>Teleports a player to an arrival point in the given level.</summary>
    public bool Send(IServerPlayer player, int level, ulong key, System.Func<Tile, bool> anchor)
    {
        if (layout == null || player.Entity == null) return false;
        (int X, int Z)? arrival = layout.FindArrival(level, key, anchor);
        if (arrival == null) return false;

        busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + CooldownMs;
        player.Entity.TeleportToDouble(arrival.Value.X + 0.5, geometry.FloorY + 1.05, arrival.Value.Z + 0.5);
        return true;
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

    public BlockBehaviorThreshold(Block block) : base(block)
    {
    }

    public override void Initialize(Vintagestory.API.Datastructures.JsonObject properties)
    {
        base.Initialize(properties);
        kind = properties?["kind"].AsString("door") ?? "door";
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
