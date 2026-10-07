using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Deep;

/// <summary>
/// Living things, only where they belong: fish in Level 7's sea, drifters in the dark of Level 8's caves (never on
/// the lit road), raccoons, foxes and hares in the Suburbs' night, and livestock in Level 10's pastures. Levels 0 to 6
/// have no animals. Spawning is kept to a small number around each player. The Backrooms' own entities (Smilers,
/// Hounds and the rest) are put down by <see cref="Backrooms.Entities.MenaceSystem"/>.
/// </summary>
public class CreatureSystem : ModSystem
{
    private const float IntervalSeconds = 6;
    private const int CountRadius = 48;
    private const int MinDistance = 16, MaxDistance = 40;
    /// <summary>Drifters only spawn where the light is below this.</summary>
    private const int DarkLight = 7;

    private sealed class Spawns
    {
        public int Cap;
        public (string Prefix, double Weight)[] Kinds;
        public EntityProperties[][] Resolved;
        public HashSet<string> Codes;
    }

    private static readonly Dictionary<int, Spawns> ByLevel = new()
    {
        [7] = new Spawns { Cap = 7, Kinds = new[] { ("fish-saltwater-", 1.0) } },
        [8] = new Spawns { Cap = 3, Kinds = new[] { ("drifter-normal", 0.75), ("drifter-deep", 0.25) } },
        [9] = new Spawns
        {
            Cap = 4,
            // (No wolves: the Suburbs' Hounds are the Backrooms' own, see src/Entities)
            Kinds = new[] { ("raccoon-common-adult-", 0.4), ("fox-red-adult-", 0.25), ("hare-european-adult-", 0.3) },
        },
        [10] = new Spawns
        {
            Cap = 6,
            Kinds = new[] { ("chicken-hen", 0.3), ("chicken-rooster", 0.05), ("pig-eurasian-adult-", 0.2), ("sheep-mouflon-adult-", 0.25), ("goat-nubian-adult-", 0.2) },
        },
    };

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private readonly BlockPos tmp = new(0);

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            Resolve();
            api.Event.RegisterGameTickListener(OnTick, (int)(IntervalSeconds * 1000));
        });
    }

    /// <summary>Finds the entity types behind each prefix (every variant of a creature), skipping any that are missing.</summary>
    private void Resolve()
    {
        var all = sapi.World.EntityTypes.Where(t => t.Code.Domain == "game").ToList();
        foreach (var (level, spawns) in ByLevel)
        {
            spawns.Resolved = spawns.Kinds.Select(k => all.Where(t => t.Code.Path.StartsWith(k.Prefix) && !t.Code.Path.Contains("baby") && !t.Code.Path.Contains("poult")).ToArray()).ToArray();
            spawns.Codes = spawns.Resolved.SelectMany(r => r).Select(t => t.Code.ToString()).ToHashSet();
            int found = spawns.Resolved.Count(r => r.Length > 0);
            if (found < spawns.Kinds.Length)
                sapi.Logger.Warning("[backrooms] Level {0}: only {1} of {2} creature kinds were found", level, found, spawns.Kinds.Length);
        }
    }

    private void OnTick(float dt)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity == null) continue;
            if (player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
            EntityPos pos = player.Entity.Pos;
            int level = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(pos.X)), WorldLayout.MacroOf((int)Math.Floor(pos.Z)));
            if (!ByLevel.TryGetValue(level, out Spawns spawns) || sapi.World.Rand.NextDouble() < 0.4) continue;

            int count = sapi.World.GetEntitiesAround(pos.XYZ, CountRadius, 64, e => e.Alive && spawns.Codes.Contains(e.Code.ToString())).Length;
            if (count >= spawns.Cap) continue;
            TrySpawn(level, spawns, pos);
        }
    }

    private void TrySpawn(int level, Spawns spawns, EntityPos near)
    {
        Random rand = sapi.World.Rand;
        for (int attempt = 0; attempt < 6; attempt++)
        {
            double angle = rand.NextDouble() * Math.PI * 2, dist = MinDistance + rand.NextDouble() * (MaxDistance - MinDistance);
            int x = (int)Math.Floor(near.X + Math.Cos(angle) * dist), z = (int)Math.Floor(near.Z + Math.Sin(angle) * dist);
            if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != level) continue;
            if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, geometry.FloorY, z) == null) continue;

            int? y = level switch
            {
                7 => InWater(x, z, rand),
                8 => InDarkCave(x, (int)near.Y, z),
                9 => Outdoors(x, z),
                _ => layout.IsPasture(x, z) ? Outdoors(x, z) : null,
            };
            if (y == null) continue;

            EntityProperties type = Pick(spawns, rand);
            if (type == null) return;
            Entity entity = sapi.World.ClassRegistry.CreateEntity(type);
            entity.Pos.SetPos(x + 0.5, y.Value + 0.05, z + 0.5);
            entity.Pos.Yaw = (float)(rand.NextDouble() * Math.PI * 2);
            sapi.World.SpawnEntity(entity);
            return;
        }
    }

    private static EntityProperties Pick(Spawns spawns, Random rand)
    {
        double total = 0;
        for (int i = 0; i < spawns.Kinds.Length; i++) if (spawns.Resolved[i].Length > 0) total += spawns.Kinds[i].Weight;
        double r = rand.NextDouble() * total;
        for (int i = 0; i < spawns.Kinds.Length; i++)
        {
            EntityProperties[] options = spawns.Resolved[i];
            if (options.Length == 0) continue;
            r -= spawns.Kinds[i].Weight;
            if (r <= 0) return options[rand.Next(options.Length)];
        }
        return null;
    }

    /// <summary>Somewhere in open water under Level 7's floor line.</summary>
    private int? InWater(int x, int z, Random rand)
    {
        int y = geometry.FloorY - 2 - rand.Next(40);
        IBlockAccessor ba = sapi.World.BlockAccessor;
        if (ba.GetBlock(tmp.Set(x, y, z)).BlockId != 0) return null;
        return ba.GetBlock(tmp, BlockLayersAccess.Fluid).IsLiquid() ? y : null;
    }

    /// <summary>A dark cave floor with headroom, within a few blocks of the player's height.</summary>
    private int? InDarkCave(int x, int nearY, int z)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        for (int y = nearY + 8; y >= nearY - 12; y--)
        {
            if (ba.GetBlock(tmp.Set(x, y - 1, z)).SideSolid[BlockFacing.UP.Index] == false) continue;
            if (ba.GetBlock(tmp.Set(x, y, z)).BlockId != 0 || ba.GetBlock(tmp, BlockLayersAccess.Fluid).BlockId != 0) continue;
            if (ba.GetBlock(tmp.Set(x, y + 1, z)).BlockId != 0) continue;
            if (ba.GetLightLevel(tmp.Set(x, y, z), EnumLightLevelType.MaxLight) >= DarkLight) return null;
            return y;
        }
        return null;
    }

    /// <summary>Open ground under the sky: nothing standing on the floor, nothing overhead, no water.</summary>
    private int? Outdoors(int x, int z)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int y = geometry.FloorY + 1;
        if (!ba.GetBlock(tmp.Set(x, y - 1, z)).SideSolid[BlockFacing.UP.Index]) return null;
        if (ba.GetBlock(tmp.Set(x, y, z)).BlockId != 0 || ba.GetBlock(tmp, BlockLayersAccess.Fluid).BlockId != 0) return null;
        if (ba.GetBlock(tmp.Set(x, y + 1, z)).BlockId != 0) return null;
        return ba.GetRainMapHeightAt(x, z) <= y ? y : null;
    }
}
