using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// Wanderers who trade: other people lost in the Backrooms, keeping to a camp in Level 1, an outpost in Level 4, the
/// 9th Road, a corner of the city, the Junkies' places in The End, the Hub's outposts or Level 3999's camps (see
/// <see cref="WorldLayout.WandererSite"/>, which must cover every place a wanderer may stand: <see cref="OnEntityLoaded"/>
/// removes any wanderer loaded outside every site). Each site is given its wanderer the
/// first time a player comes near, and the world remembers it (saved as "backrooms-wanderers"); from then on the
/// wanderer is an ordinary trader kept with the world. A site is only ever given one: a wanderer killed is not put
/// down again. They take rusty gears.
/// <para>
/// Each wanderer has a site key (<see cref="WandererSites"/>, from <see cref="SiteKeyAt"/>: camp, outpost, road, city,
/// end, hub for the M.E.G.'s doorstep, amber for Camp Amber, 3999) that picks its trade list, its name and its lines
/// (docs/design/traders/README.md). A new one is given its key before it is spawned and stocked from its site's list as
/// it is; every time one loads, its site's list is put back over the type's (which vanilla reads at load). One saved
/// before sites existed is given its key the first time it loads, and restocked once from the site's list then (its
/// gears and name kept). One spawned any other way (the cheat menu) takes the key of the level it stands in.
/// </para>
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

    /// <summary>Set while the dev command spawns a wanderer without a site on purpose (one as saved before sites existed).</summary>
    private bool spawningSiteless;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // (After BackroomsModSystem, whose /backrooms command this adds to)
    public override double ExecuteOrder() => 1.2;

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
            CheckWares();
            tickListener = api.Event.RegisterGameTickListener(OnTick, 10_000, 5000);
            // (Chunks round spawn are loaded before this point: look at what they hold too)
            foreach (Entity entity in new List<Entity>(api.World.LoadedEntities.Values)) OnEntityLoaded(entity);
        });
        api.Event.OnEntityLoaded += OnEntityLoaded;
        api.Event.OnEntitySpawn += OnEntitySpawn;
        api.Event.GameWorldSave += SaveWanderers;

        var parsers = api.ChatCommands.Parsers;
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("wanderers")
                .WithDescription("Dev test: wanderers [list] lists the sites given a wanderer and each one's site key; wanderers load loads the chunk columns of those sites, "
                    + "so their wanderers load (and, saved before sites existed, are given theirs: see the log); wanderers spawn puts down one wanderer of every site key "
                    + "at the spawn and logs its name and wares, then removes them; wanderers adopt <site> puts down one with no site, as saved before sites existed, "
                    + "gives it that site as a load would, and logs its wares before and after")
                // (Words: a console line ends in a carriage return the parser keeps as an argument; it is trimmed away)
                .WithArgs(parsers.OptionalWord("mode"), parsers.OptionalWord("site"))
                .HandleWith(OnWanderersCommand)
            .EndSubCommand();
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
            sapi.Event.OnEntitySpawn -= OnEntitySpawn;
            sapi.Event.GameWorldSave -= SaveWanderers;
            if (tickListener != 0) sapi.Event.UnregisterGameTickListener(tickListener);
        }
        base.Dispose();
    }

    private static bool IsWanderer(Entity entity) =>
        entity?.Code?.Domain == "backrooms" && entity.Code.Path.StartsWith("wanderer", StringComparison.Ordinal);

    /// <summary>
    /// The site key of a wanderer standing here, by the level: camp (Level 1, and anywhere that is not a site's level),
    /// outpost (Level 4), road (Level 8), city (Level 11), end (The End), 3999 (Level 3999); in the Hub, hub at the M.E.G.'s
    /// doorstep by the city door and amber at Camp Amber's by the Level 1 door.
    /// </summary>
    private string SiteKeyAt(double x, double z)
    {
        int gx = (int)Math.Floor(x), gz = (int)Math.Floor(z);
        switch (layout.LevelAt(WorldLayout.MacroOf(gx), WorldLayout.MacroOf(gz)))
        {
            case 4: return "outpost";
            case 8: return "road";
            case 11: return "city";
            case WorldLayout.TheEnd: return "end";
            case WorldLayout.Level3999: return "3999";
            case WorldLayout.Hub:
                return layout.HubMegSite() is { } meg && (meg.X - gx) * (meg.X - gx) + (meg.Z - gz) * (meg.Z - gz) < 24 * 24 ? "hub" : "amber";
            default: return "camp";
        }
    }

    /// <summary>
    /// A wanderer loaded with the world whose cell is no longer a wanderer site (left from an earlier version that put
    /// far too many down) quietly goes. Removed a moment later, not while the chunk is still loading. One at its site
    /// with no site key yet (saved before there were any) is given its key, and restocked from its site's list.
    /// </summary>
    private void OnEntityLoaded(Entity entity)
    {
        if (layout == null || !IsWanderer(entity)) return;
        int mx = WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), mz = WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z));
        // (A wanderer may have walked a little way off its own cell)
        bool atSite = false;
        for (int dz = -1; dz <= 1 && !atSite; dz++)
            for (int dx = -1; dx <= 1 && !atSite; dx++)
                atSite = SiteOf(mx + dx, mz + dz) != null;
        if (atSite)
        {
            if (entity is not EntityTradingHumanoid wanderer) return;
            // (Vanilla has just read the type's own list: put the site's back. One saved before sites gets its own, and is restocked from it)
            if (WandererSites.Site(wanderer) is { } site) WandererSites.Apply(wanderer, site, restock: false);
            else sapi.Event.RegisterCallback(_ => Adopt(wanderer, null), 100);
            return;
        }
        sapi.Event.RegisterCallback(_ =>
        {
            if (!entity.Alive) return;
            entity.Die(EnumDespawnReason.Removed);
            sapi.Logger.Notification("[backrooms] removed a wanderer at {0:0},{1:0},{2:0}: no longer a wanderer's site", entity.Pos.X, entity.Pos.Y, entity.Pos.Z);
        }, 100);
    }

    /// <summary>Gives a wanderer that has none the site key of where it stands (or the one given), and stocks it afresh from that site's list.</summary>
    private void Adopt(EntityTradingHumanoid wanderer, string site)
    {
        if (wanderer == null || !wanderer.Alive || WandererSites.Site(wanderer) != null) return;
        site ??= SiteKeyAt(wanderer.Pos.X, wanderer.Pos.Z);
        WandererSites.Apply(wanderer, site, restock: true);
        // (Saved with its chunk even if nothing else there changes, or the next load would find it without a site again)
        sapi.World.BlockAccessor.GetChunkAtBlockPos(wanderer.Pos.AsBlockPos)?.MarkModified();
        var (selling, buying) = WandererSites.WareCount(wanderer);
        sapi.Logger.Notification("[backrooms] the wanderer {0} at {1:0},{2:0},{3:0} now keeps to its site: {4} ({5} wares for sale, {6} wanted)",
            wanderer.GetName(), wanderer.Pos.X, wanderer.Pos.Y, wanderer.Pos.Z, site, selling, buying);
    }

    /// <summary>
    /// A wanderer just spawned is stocked from its site's list: the key it was given before it was spawned, or (spawned
    /// from the cheat menu or a command) the key of the level it stands in.
    /// </summary>
    private void OnEntitySpawn(Entity entity)
    {
        if (layout == null || spawningSiteless || !IsWanderer(entity) || entity is not EntityTradingHumanoid wanderer) return;
        if (WandererSites.Site(wanderer) is { } site) WandererSites.Apply(wanderer, site, restock: true);
        else Adopt(wanderer, null);
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

        string siteKey = SiteKeyAt(site.X, site.Z);
        Entity wanderer = Spawn(spot, siteKey);
        placed.Add(key);
        sapi.Logger.Notification("[backrooms] a wanderer, {0}, now keeps to {1},{2},{3} (level {4}, site {5})", wanderer.GetName(), site.X, y, site.Z, level, siteKey);
    }

    /// <summary>Puts a wanderer down: given its site key (null: none, as saved before sites existed), stocked from that site's list as it is spawned (<see cref="OnEntitySpawn"/>), and named for it.</summary>
    private Entity Spawn(Vec3d spot, string siteKey)
    {
        Entity wanderer = sapi.World.ClassRegistry.CreateEntity(type);
        wanderer.Pos.SetPos(spot);
        wanderer.Pos.Yaw = (float)(sapi.World.Rand.NextDouble() * Math.PI * 2);
        if (siteKey != null) WandererSites.SetSite(wanderer, siteKey);
        spawningSiteless = siteKey == null;
        try { sapi.World.SpawnEntity(wanderer); }
        finally { spawningSiteless = false; }
        if (siteKey != null) WandererSites.NameForSite(wanderer, siteKey);
        return wanderer;
    }

    /// <summary>Reads every site's trade list and resolves its wares, and reads the wanderers' dialogue, once a world starts: a list or line that would fail later says so in the log now.</summary>
    private void CheckWares()
    {
        int wares = 0, failed = 0;
        foreach (string site in WandererSites.Sites)
        {
            TradeProperties props = WandererSites.LoadTradeProps(sapi, site);
            if (props?.Selling?.List == null || props.Buying?.List == null)
            {
                failed++;
                continue;
            }
            foreach (TradeItem item in props.Selling.List.Concat(props.Buying.List))
            {
                wares++;
                if (!item.Resolve(sapi.World, "the wanderers' trade list for " + site)) failed++;
            }
        }
        string dialogue;
        try
        {
            DialogueConfig config = JsonUtil.FromString<DialogueConfig>(sapi.Assets.Get(new AssetLocation("backrooms", "config/dialogue/wanderer.json")).ToText());
            config.Init();
            dialogue = config.components.Length + " parts";
        }
        catch (Exception e)
        {
            failed++;
            dialogue = "unreadable (" + e.Message + ")";
        }
        if (failed > 0) sapi.Logger.Warning("[backrooms] wanderers: {0} trade lists, {1} wares, {2} failed to read or resolve; dialogue {3}", WandererSites.Sites.Length, wares, failed, dialogue);
        else sapi.Logger.Notification("[backrooms] wanderers: {0} trade lists, {1} wares, all resolved; dialogue {2}", WandererSites.Sites.Length, wares, dialogue);
    }

    // ================= The dev command =================

    private TextCommandResult OnWanderersCommand(TextCommandCallingArgs args)
    {
        if (layout == null || type == null) return TextCommandResult.Error("Not a Backrooms world, or the wanderer's entity type is missing");
        string mode = (args[0] as string)?.Trim() is { Length: > 0 } m ? m : "list";
        string site = (args[1] as string)?.Trim() is { Length: > 0 } s ? s : null;
        switch (mode)
        {
            case "list":
            {
                var lines = new List<string> { $"{placed.Count} wanderer site(s) given a wanderer:" };
                foreach (long key in placed)
                {
                    int mx = (int)(key >> 32), mz = (int)(uint)key;
                    if (SiteOf(mx, mz) is not { } at)
                    {
                        lines.Add($"  cell {mx},{mz}: no longer a site");
                        continue;
                    }
                    lines.Add($"  {at.X},{at.Z}: {SiteKeyAt(at.X, at.Z)}");
                    lines.AddRange(WanderersNear(at));
                }
                foreach (string line in lines) sapi.Logger.Notification("[backrooms] {0}", line);
                return TextCommandResult.Success(string.Join("\n", lines));
            }
            case "load":
            {
                int n = 0;
                foreach (long key in placed)
                {
                    if (SiteOf((int)(key >> 32), (int)(uint)key) is not { } at) continue;
                    sapi.WorldManager.LoadChunkColumnPriority(at.X / GlobalConstants.ChunkSize, at.Z / GlobalConstants.ChunkSize, new ChunkLoadOptions
                    {
                        OnLoaded = () => sapi.Event.EnqueueMainThreadTask(() =>
                        {
                            foreach (string line in WanderersNear(at)) sapi.Logger.Notification("[backrooms] wanderers load: site {0},{1}:{2}", at.X, at.Z, line);
                        }, "backrooms-wandererload"),
                    });
                    n++;
                }
                return TextCommandResult.Success($"Loading {n} site(s); their wanderers report in the log as they load");
            }
            case "spawn":
            case "adopt":
            {
                if (mode == "adopt" && (site == null || !WandererSites.Sites.Contains(site)))
                    return TextCommandResult.Error("wanderers adopt <site>: one of " + string.Join(", ", WandererSites.Sites));
                EntityPos at = sapi.World.DefaultSpawnPosition;
                sapi.WorldManager.LoadChunkColumnPriority((int)at.X / GlobalConstants.ChunkSize, (int)at.Z / GlobalConstants.ChunkSize, new ChunkLoadOptions
                {
                    OnLoaded = () => sapi.Event.EnqueueMainThreadTask(() => SpawnTest(mode, site, at.XYZ), "backrooms-wandererstest"),
                });
                return TextCommandResult.Success("Putting wanderers down at the spawn; see the log");
            }
            default:
                return TextCommandResult.Error("wanderers [list|load|spawn|adopt <site>]");
        }
    }

    /// <summary>The wanderers loaded within 48 blocks of a site: name, class, site key and wares (for the dev command).</summary>
    private List<string> WanderersNear((int X, int Z) site)
    {
        var lines = new List<string>();
        foreach (Entity e in sapi.World.LoadedEntities.Values)
        {
            if (!IsWanderer(e) || e.Pos.HorDistanceTo(new Vec3d(site.X + 0.5, e.Pos.Y, site.Z + 0.5)) > 48) continue;
            lines.Add($"    {e.GetName()} ({e.GetType().Name}, {(e.Alive ? "alive" : "dead")}) at {e.Pos.X:0},{e.Pos.Y:0},{e.Pos.Z:0}, site {WandererSites.Site(e) ?? "(none)"}: "
                + (e is EntityTradingHumanoid w ? $"trade list of {w.TradeProps?.Selling?.List?.Length} and {w.TradeProps?.Buying?.List?.Length}; " + Wares(w) : ""));
        }
        if (lines.Count == 0) lines.Add("    (no wanderer loaded near it)");
        return lines;
    }

    private void SpawnTest(string mode, string site, Vec3d at)
    {
        var spawned = new List<Entity>();
        string[] keys = mode == "spawn" ? WandererSites.Sites : new[] { site };
        for (int i = 0; i < keys.Length; i++)
        {
            var spot = new Vec3d(at.X + 2 * i - keys.Length, at.Y, at.Z + 3);
            if (mode == "spawn")
            {
                Entity e = Spawn(spot, keys[i]);
                spawned.Add(e);
                if (e is not EntityTradingHumanoid w) continue;
                var (selling, buying) = WandererSites.WareCount(w);
                sapi.Logger.Notification("[backrooms] wanderers spawn: {0} ({1}), site {2}: {3} wares for sale, {4} wanted, of lists of {5} and {6}: {7}",
                    e.GetName(), e.GetType().Name, WandererSites.Site(w), selling, buying, w.TradeProps?.Selling?.List?.Length, w.TradeProps?.Buying?.List?.Length, Wares(w));
            }
            else
            {
                Entity e = Spawn(spot, null);
                spawned.Add(e);
                if (e is not EntityTradingHumanoid w) continue;
                var (selling, buying) = WandererSites.WareCount(w);
                sapi.Logger.Notification("[backrooms] wanderers adopt: before, {0} has site {1}: {2} wares for sale, {3} wanted ({4})",
                    w.GetName(), WandererSites.Site(w) ?? "(none)", selling, buying, Wares(w));
                Adopt(w, site);
                sapi.Logger.Notification("[backrooms] wanderers adopt: after, site {0}: {1}", WandererSites.Site(w), Wares(w));
            }
        }
        sapi.Event.RegisterCallback(_ =>
        {
            foreach (Entity e in spawned) if (e.Alive) e.Die(EnumDespawnReason.Removed);
        }, 2000);
    }

    private static string Wares(EntityTradingHumanoid w)
    {
        if (w.Inventory == null) return "";
        IEnumerable<string> Names(ItemSlotTrade[] slots) => slots.Where(s => s?.Itemstack != null && s.TradeItem != null)
            .Select(s => s.Itemstack.Collectible.Code.ToShortString() + " x" + s.TradeItem.Stock + " @" + s.TradeItem.Price);
        return "sells " + string.Join(", ", Names(w.Inventory.SellingSlots)) + "; buys " + string.Join(", ", Names(w.Inventory.BuyingSlots));
    }
}
