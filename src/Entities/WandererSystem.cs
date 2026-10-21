using System;
using System.Collections.Generic;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;

namespace Backrooms.Entities;

/// <summary>
/// Wanderers who trade: other people lost in the Backrooms, keeping to a camp in Level 1, an outpost in Level 4, the
/// 9th Road, a corner of the city, the Junkies' places in The End, the Hub's outposts or Level 3999's camps (see
/// <see cref="WorldLayout.WandererSite"/>, which must cover every place a wanderer may stand: <see cref="OnEntityLoaded"/>
/// removes any wanderer loaded outside every site). Each site is given its wanderer the
/// first time a player comes near, and the world remembers it (saved as "backrooms-wanderers"); from then on the
/// wanderer is an ordinary trader kept with the world. A site is only ever given one: a wanderer killed is not put
/// down again. They take rusty gears, buy salvage and sell Almond Water, Firesalt, candles, bandages and seeds.
/// </summary>
public class WandererSystem : ModSystem
{
    private const string SaveKey = "backrooms-wanderers";
    private const string Code = "backrooms:wanderer-male";

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private EntityProperties type;
    private HashSet<long> placed = new();

    /// <summary>What the layout says of each cell (it never changes for a world), so a site not yet given its wanderer is not searched for again every tick.</summary>
    private readonly Dictionary<long, (int X, int Z)?> sites = new();

    private (int X, int Z)? SiteOf(int mx, int mz)
    {
        long key = ((long)mx << 32) | (uint)mz;
        if (!sites.TryGetValue(key, out (int X, int Z)? site)) sites[key] = site = layout.WandererSite(mx, mz);
        return site;
    }

    private long tickListener;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            type = api.World.GetEntityType(new AssetLocation(Code));
            if (type == null)
            {
                api.Logger.Warning("[backrooms] entity type {0} is missing; no wanderers", Code);
                return;
            }
            byte[] data = api.WorldManager.SaveGame.GetData(SaveKey);
            if (data != null && data.Length > 0)
            {
                try { placed = new HashSet<long>(SerializerUtil.Deserialize<long[]>(data)); }
                catch (Exception e) { api.Logger.Warning("[backrooms] could not read the wanderers' sites: {0}", e.Message); }
            }
            tickListener = api.Event.RegisterGameTickListener(OnTick, 10_000, 5000);
            // (Chunks round spawn are loaded before this point: look at what they hold too)
            foreach (Entity entity in new List<Entity>(api.World.LoadedEntities.Values)) OnEntityLoaded(entity);
        });
        api.Event.OnEntityLoaded += OnEntityLoaded;
        api.Event.GameWorldSave += SaveWanderers;
    }

    private void SaveWanderers()
    {
        if (layout != null) sapi.WorldManager.SaveGame.StoreData(SaveKey, SerializerUtil.Serialize(new List<long>(placed).ToArray()));
    }

    public override void Dispose()
    {
        if (sapi != null)
        {
            sapi.Event.OnEntityLoaded -= OnEntityLoaded;
            sapi.Event.GameWorldSave -= SaveWanderers;
            if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
        }
        base.Dispose();
    }

    /// <summary>
    /// A wanderer loaded with the world whose cell is no longer a wanderer site (left from an earlier version that put
    /// far too many down) quietly goes. Removed a moment later, not while the chunk is still loading.
    /// </summary>
    private void OnEntityLoaded(Entity entity)
    {
        if (layout == null || entity.Code?.Domain != "backrooms" || !entity.Code.Path.StartsWith("wanderer", StringComparison.Ordinal)) return;
        int mx = WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), mz = WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z));
        // (A wanderer may have walked a little way off its own cell)
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (SiteOf(mx + dx, mz + dz) != null) return;
        sapi.Event.RegisterCallback(_ =>
        {
            if (!entity.Alive) return;
            entity.Die(EnumDespawnReason.Removed);
            sapi.Logger.Notification("[backrooms] removed a wanderer at {0:0},{1:0},{2:0}: no longer a wanderer's site", entity.Pos.X, entity.Pos.Y, entity.Pos.Z);
        }, 100);
    }

    private void OnTick(float dt)
    {
        foreach (IPlayer player in sapi.World.AllOnlinePlayers)
        {
            if (player.Entity == null || player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
            int pmx = WorldLayout.MacroOf((int)Math.Floor(player.Entity.Pos.X)), pmz = WorldLayout.MacroOf((int)Math.Floor(player.Entity.Pos.Z));
            for (int mz = pmz - 2; mz <= pmz + 2; mz++)
            {
                for (int mx = pmx - 2; mx <= pmx + 2; mx++)
                {
                    long key = ((long)mx << 32) | (uint)mz;
                    if (placed.Contains(key)) continue;
                    (int X, int Z)? site = SiteOf(mx, mz);
                    if (site == null) continue;
                    TryPlace(key, site.Value, player.Entity);
                }
            }
        }
    }

    private void TryPlace(long key, (int X, int Z) site, Entity near)
    {
        // Put down while out of sight, not on top of anyone
        double distance = Math.Sqrt(near.Pos.XYZ.HorizontalSquareDistanceTo(site.X + 0.5, site.Z + 0.5));
        if (distance < 20 || distance > 72) return;
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(site.X, (int)near.Pos.Y, site.Z) == null) return;
        int level = layout.LevelAt(WorldLayout.MacroOf(site.X), WorldLayout.MacroOf(site.Z));
        int y = Senses.FindFloor(sapi.World, site.X, (int)Math.Floor(near.Pos.Y), site.Z, 2, level == 8 ? 16 : 6);
        if (y == int.MinValue) return;
        var spot = new Vec3d(site.X + 0.5, y, site.Z + 0.5);
        // (Nor within 20 blocks of, nor in view of, any other player either: the director's own sight test, which looks at everyone)
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            EntityPlayer other = online.Entity;
            if (other == null || other == near || !other.Alive || other.Pos.Dimension != near.Pos.Dimension || online.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
            if (other.Pos.XYZ.HorizontalSquareDistanceTo(spot.X, spot.Z) < 20 * 20) return;
        }
        float height = type.CollisionBoxSize?.Y ?? 1.85f, width = type.CollisionBoxSize?.X ?? 0.6f;
        MenaceSystem director = sapi.ModLoader.GetModSystem<MenaceSystem>();
        if (director != null ? director.SeenBySomeone(near, spot, height, width) : Senses.ClearLine(sapi.World, Senses.Eyes(near), spot.AddCopy(0, 1.5, 0))) return;

        Entity wanderer = sapi.World.ClassRegistry.CreateEntity(type);
        wanderer.Pos.SetPos(spot);
        wanderer.Pos.Yaw = (float)(sapi.World.Rand.NextDouble() * Math.PI * 2);
        sapi.World.SpawnEntity(wanderer);
        placed.Add(key);
        sapi.Logger.Notification("[backrooms] a wanderer now keeps to {0},{1},{2} (level {3})", site.X, y, site.Z, level);
    }
}
