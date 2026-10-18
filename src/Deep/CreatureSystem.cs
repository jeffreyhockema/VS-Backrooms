using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Salvage;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Deep;

/// <summary>
/// Living things, only where they belong: fish in Level 7's sea, raccoons, foxes and hares in the Suburbs, and
/// livestock in Level 10's pastures and farmyards. The other levels have no animals (Level 8's caves had drifters once; the code
/// for finding a dark cave floor is kept for a level that wants it). Spawning is kept to a small number around each
/// player, and the vanilla creatures despawn by their own rules. Livestock is food, so the world's Backrooms scarcity
/// (<see cref="ScarcitySystem"/>) scales how many stand about and how often more come. The Backrooms' own entities
/// (Smilers, Hounds and the rest) are put down by <see cref="Backrooms.Entities.MenaceSystem"/>.
/// </summary>
public class CreatureSystem : ModSystem
{
    private const float IntervalSeconds = 6;
    private const int CountRadius = 48;
    private const int MinDistance = 16, MaxDistance = 40;
    /// <summary>A cave floor counts as dark (see <see cref="InDarkCave"/>) where the light is below this.</summary>
    private const int DarkLight = 7;

    private sealed class Spawns
    {
        public int Cap;
        /// <summary>Kept as food: the cap and the odds of more coming follow the world's Backrooms scarcity.</summary>
        public bool Food;
        public (string Prefix, double Weight)[] Kinds;
        /// <summary>The most that come together as a herd or a flock, by kind (a missing entry is one at a time).</summary>
        public int[] Herd;
        public EntityProperties[][] Resolved;
        public HashSet<string> Codes;
    }

    private static readonly Dictionary<int, Spawns> ByLevel = new()
    {
        [7] = new Spawns { Cap = 7, Kinds = new[] { ("fish-saltwater-", 1.0) } },
        // (Level 8's drifters are gone: its feral dark is the Wretches' now, put down by the entity director)
        [9] = new Spawns
        {
            Cap = 4,
            // (No wolves: the Suburbs' Hounds are the Backrooms' own, see src/Entities)
            Kinds = new[] { ("raccoon-common-adult-", 0.4), ("fox-red-adult-", 0.25), ("hare-european-adult-", 0.3) },
        },
        [10] = new Spawns
        {
            // A farm's stock (vanilla has no cattle): a flock of hens, a few sheep, pigs, goats, with the odd young among them.
            // On Normal nine stand about a player, three on Scarce (a third as many), eighteen on Plentiful
            Cap = 9,
            Food = true,
            Kinds = new[] { ("chicken-hen", 0.3), ("chicken-rooster", 0.04), ("pig-eurasian-adult-", 0.2), ("sheep-mouflon-adult-", 0.3), ("goat-nubian-adult-", 0.16) },
            Herd = new[] { 4, 1, 3, 4, 3 },
        },
        // (The five kept as 14-18, and Levels 3999 and 188, have no animals. A level that should gives itself an entry here, keyed by its
        // WorldLayout constant, and a case in TrySpawn saying where they stand)
    };

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private float foodScale = 1;
    private Dictionary<string, EntityProperties> byPath;
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
            foodScale = ScarcitySystem.FoodScale(api.World);
            Resolve();
            api.Event.RegisterGameTickListener(OnTick, (int)(IntervalSeconds * 1000));
        });
    }

    /// <summary>Finds the entity types behind each prefix (every variant of a creature), skipping any that are missing.</summary>
    private void Resolve()
    {
        var all = sapi.World.EntityTypes.Where(t => t.Code.Domain == "game").ToList();
        byPath = all.GroupBy(t => t.Code.Path).ToDictionary(g => g.Key, g => g.First(), StringComparer.Ordinal);
        foreach (var (level, spawns) in ByLevel)
        {
            spawns.Resolved = spawns.Kinds.Select(k => all.Where(t => t.Code.Path.StartsWith(k.Prefix) && !t.Code.Path.Contains("baby") && !t.Code.Path.Contains("poult")).ToArray()).ToArray();
            spawns.Codes = spawns.Resolved.SelectMany(r => r).Select(t => t.Code.ToString()).ToHashSet();
            // (The young count towards the cap as well)
            foreach (EntityProperties adult in spawns.Resolved.SelectMany(r => r).ToList())
                if (YoungOf(adult) is { } young) spawns.Codes.Add(young.Code.ToString());
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
            if (!ByLevel.TryGetValue(level, out Spawns spawns)) continue;
            // Livestock: on Scarce three at most round a player, coming a third as often (on Plentiful, twice as many)
            float food = spawns.Food ? foodScale : 1;
            if (sapi.World.Rand.NextDouble() >= 0.6 * Math.Min(1, food)) continue;
            int cap = spawns.Food ? Math.Max(1, (int)Math.Round(spawns.Cap * food)) : spawns.Cap;

            int count = sapi.World.GetEntitiesAround(pos.XYZ, CountRadius, 64, e => e.Alive && spawns.Codes.Contains(e.Code.ToString())).Length;
            if (count >= cap) continue;
            TrySpawn(level, spawns, pos, cap - count);
        }
    }

    private void TrySpawn(int level, Spawns spawns, EntityPos near, int room)
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
                // Paddocks and farmyards; strays also graze the fallow meadows, but less often
                _ => layout.IsPasture(x, z) || layout.IsFarmyard(x, z) || rand.NextDouble() < 0.4 && layout.IsMeadow(x, z) ? Outdoors(x, z) : null,
            };
            if (y == null) continue;

            int kind = PickKind(spawns, rand);
            if (kind < 0) return;
            // Livestock come as a herd or a flock, one of them a young one now and then, as many as the cap leaves room for
            int size = 1 + (spawns.Herd != null && spawns.Herd[kind] > 1 ? rand.Next(spawns.Herd[kind]) : 0);
            size = Math.Min(size, Math.Max(1, room));
            for (int i = 0; i < size; i++)
            {
                int ex = x, ez = z, ey = y.Value;
                if (i > 0)
                {
                    ex += rand.Next(-3, 4); ez += rand.Next(-3, 4);
                    if (!SameGround(level, ex, ez) || Outdoors(ex, ez) is not int oy) continue;
                    ey = oy;
                }
                EntityProperties type = spawns.Resolved[kind][rand.Next(spawns.Resolved[kind].Length)];
                if (spawns.Food && rand.NextDouble() < 0.25 && YoungOf(type) is { } young) type = young;
                Entity entity = sapi.World.ClassRegistry.CreateEntity(type);
                entity.Pos.SetPos(ex + 0.5, ey + 0.05, ez + 0.5);
                entity.Pos.Yaw = (float)(rand.NextDouble() * Math.PI * 2);
                sapi.World.SpawnEntity(entity);
            }
            return;
        }
    }

    /// <summary>Whether a herd member's spot is still in the pasture, the farmyard or the meadow (on the level it began in).</summary>
    private bool SameGround(int level, int x, int z) =>
        level != 10 || layout.IsPasture(x, z) || layout.IsFarmyard(x, z) || layout.IsMeadow(x, z);

    /// <summary>The young of a farm animal (piglets, lambs, kids, chicks), or null for any other creature.</summary>
    private EntityProperties YoungOf(EntityProperties adult)
    {
        string path = adult.Code.Path;
        string young = path.Contains("-adult-") ? path.Replace("-adult-", "-baby-")
            : path.StartsWith("chicken-hen") ? "chicken-henpoult" : path.StartsWith("chicken-rooster") ? "chicken-roosterpoult" : null;
        return young != null && byPath.TryGetValue(young, out EntityProperties type) ? type : null;
    }

    /// <summary>Which kind of the level's creatures comes next (by weight), or -1 if none of them exist.</summary>
    private static int PickKind(Spawns spawns, Random rand)
    {
        double total = 0;
        for (int i = 0; i < spawns.Kinds.Length; i++) if (spawns.Resolved[i].Length > 0) total += spawns.Kinds[i].Weight;
        double r = rand.NextDouble() * total;
        for (int i = 0; i < spawns.Kinds.Length; i++)
        {
            if (spawns.Resolved[i].Length == 0) continue;
            r -= spawns.Kinds[i].Weight;
            if (r <= 0) return i;
        }
        return -1;
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
