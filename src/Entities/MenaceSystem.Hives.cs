using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// The Deathmoths' hive hearts and the Clumps' juveniles: what the director does at runtime (no worldgen, no layout
/// version). The first time anyone enters a hive den it puts down two or three hearts (<c>backrooms:mothhiveheart</c>)
/// round the den's heart and remembers the den in the world's <c>backrooms-dens</c> save data; breaking a heart raises
/// the alarm and sends waves of females. A Clump remnant that has lain long enough grows a juvenile through
/// <see cref="SpawnJuvenileClump"/>.
/// </summary>
public partial class MenaceSystem
{
    private const string DensSaveKey = "backrooms-dens";
    public const string HiveHeartCode = "backrooms:mothhiveheart";

    /// <summary>Hearts put down in a hive den: two or three.</summary>
    public const int HeartsMin = 2, HeartsMax = 3;

    /// <summary>How far from the den's heart (blocks) a heart may be put, and how near each other.</summary>
    public const int HeartSpread = 9, HeartSpacing = 3;

    /// <summary>The waves after a heart is broken: how many, and how long between.</summary>
    public const int WaveCount = 3, WaveIntervalMs = 20_000;

    /// <summary>A juvenile Clump's health.</summary>
    public const float JuvenileHealth = 8;

    /// <summary>The dens that have had their hearts put down (keys from <see cref="DenKey"/>), saved with the world.</summary>
    private HashSet<long> densDone = new();
    private readonly Dictionary<long, int> denTries = new();
    private readonly List<Entity> lastPack = new();

    /// <summary>While set, a pack put down is not clipped to the band's cap (a hive's waves, which answer a deliberate act).</summary>
    private bool packUncapped;

    /// <summary>A hive's waves stop adding females once this many are about the one who broke the heart.</summary>
    public const int WaveFemalesMax = 14;

    private static long DenKey(int x, int z) => ((long)x << 32) ^ (uint)z;

    private void StartHives(ICoreServerAPI api)
    {
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            byte[] data = api.WorldManager.SaveGame.GetData(DensSaveKey);
            if (data == null || data.Length == 0) return;
            try { densDone = new HashSet<long>(SerializerUtil.Deserialize<long[]>(data)); }
            catch (Exception e) { api.Logger.Warning("[backrooms] could not read the dens that have hearts: {0}", e.Message); }
        });
        api.Event.GameWorldSave += SaveDens;
    }

    private void SaveDens()
    {
        if (layout != null) sapi.WorldManager.SaveGame.StoreData(DensSaveKey, SerializerUtil.Serialize(densDone.ToArray()));
    }

    private void StopHives(ICoreServerAPI api) => api.Event.GameWorldSave -= SaveDens;

    // ================= Hive hearts =================

    /// <summary>Called for everyone the director watches: the first entry to a hive den puts its hearts down.</summary>
    private void NoteDen(Entity who, Assessment a)
    {
        if (a.Den != DenKind.Hive || layout.DenNear((int)Math.Floor(who.Pos.X), (int)Math.Floor(who.Pos.Z)) is not { Kind: DenKind.Hive } den) return;
        long key = DenKey(den.X, den.Z);
        if (densDone.Contains(key)) return;
        int placed = PlaceHearts(den.X, den.Z, (int)Math.Floor(who.Pos.Y));
        // (If the floor round it is not loaded yet, try again a few times before giving up on this den)
        if (placed > 0 || denTries.GetValueOrDefault(key) >= 5) densDone.Add(key);
        else denTries[key] = denTries.GetValueOrDefault(key) + 1;
        if (Logging) sapi.Logger.Notification("[backrooms] hive den at {0},{1}: {2} hearts put down", den.X, den.Z, placed);
    }

    /// <summary>Puts two or three hive hearts on standable floor round a den's heart, on walls where there are some and out of doorways. Returns how many.</summary>
    private int PlaceHearts(int cx, int cz, int refY)
    {
        Block heart = sapi.World.GetBlock(new AssetLocation(HiveHeartCode));
        if (heart == null) return 0;
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int want = HeartsMin + rand.Next(HeartsMax - HeartsMin + 1);
        var cells = new List<(int Dx, int Dz, double Order)>();
        for (int dz = -HeartSpread; dz <= HeartSpread; dz++)
            for (int dx = -HeartSpread; dx <= HeartSpread; dx++)
                if (dx * dx + dz * dz <= HeartSpread * HeartSpread) cells.Add((dx, dz, Math.Sqrt(dx * dx + dz * dz) + rand.NextDouble() * 3));
        cells.Sort((a, b) => a.Order.CompareTo(b.Order));

        var placed = new List<BlockPos>();
        for (int pass = 0; pass < 2 && placed.Count < want; pass++)
        {
            foreach (var (dx, dz, _) in cells)
            {
                if (placed.Count >= want) break;
                int x = cx + dx, z = cz + dz;
                if (ba.GetChunkAtBlockPos(x, refY, z) == null) continue;
                int y = Senses.FindFloor(sapi.World, x, refY, z, 2, 3);
                if (y == int.MinValue) continue;
                var pos = new BlockPos(x, y, z);
                if (ba.GetBlock(pos).BlockId != 0 || placed.Any(p => Math.Abs(p.X - x) < HeartSpacing && Math.Abs(p.Z - z) < HeartSpacing)) continue;
                if (!HeartSpotOk(ba, pos, needWall: pass == 0)) continue;
                ba.SetBlock(heart.BlockId, pos);
                placed.Add(pos);
            }
        }
        return placed.Count;
    }

    private static bool Solid(IBlockAccessor ba, int x, int y, int z) => !Senses.Open(ba, new BlockPos(x, y, z)) || !Senses.Open(ba, new BlockPos(x, y + 1, z));

    /// <summary>Whether a doorway or a corridor: walled on two opposite sides and open on the other two.</summary>
    private static bool Chokes(IBlockAccessor ba, int x, int y, int z)
    {
        bool n = Solid(ba, x, y, z - 1), s = Solid(ba, x, y, z + 1), e = Solid(ba, x + 1, y, z), w = Solid(ba, x - 1, y, z);
        return n && s && !e && !w || e && w && !n && !s;
    }

    /// <summary>A spot fit for a heart: not a doorway or corridor (nor beside one), with room round it, and against a wall if wanted.</summary>
    private static bool HeartSpotOk(IBlockAccessor ba, BlockPos pos, bool needWall)
    {
        int x = pos.X, y = pos.Y, z = pos.Z;
        if (Chokes(ba, x, y, z) || Chokes(ba, x + 1, y, z) || Chokes(ba, x - 1, y, z) || Chokes(ba, x, y, z + 1) || Chokes(ba, x, y, z - 1)) return false;
        int open = 0;
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if ((dx != 0 || dz != 0) && !Solid(ba, x + dx, y, z + dz)) open++;
        if (open < 5) return false;
        bool wall = Solid(ba, x + 1, y, z) || Solid(ba, x - 1, y, z) || Solid(ba, x, y, z + 1) || Solid(ba, x, y, z - 1);
        return wall || !needWall;
    }

    /// <summary>
    /// A hive heart has been broken: every female within sixteen blocks answers the alarm, and waves of three to five
    /// more come for whoever did it, every twenty seconds for a minute.
    /// </summary>
    public void HiveHeartBroken(BlockPos pos, Entity cause)
    {
        if (layout == null || cause == null || !Setting.Entities || Paused) return;
        AiTaskMoth.AlarmAt(sapi.World, pos.ToVec3d().Add(0.5, 0.5, 0.5), cause);
        if (Logging) sapi.Logger.Notification("[backrooms] a hive heart is broken at {0},{1},{2} by {3}: the alarm, and {4} waves", pos.X, pos.Y, pos.Z, cause.Code.Path, WaveCount);
        SendWave(cause, WaveCount);
    }

    private void SendWave(Entity cause, int remaining)
    {
        if (cause == null || !cause.Alive || remaining <= 0 || layout == null || !Setting.Entities || Paused) return;
        RosterEntry entry = Roster.DenEntry(DenKind.Hive);
        int about = sapi.World.GetEntitiesAround(cause.Pos.XYZ, 48, 24, e => e.Alive && e.Code.Path == "deathmoth-female").Length;
        if (types.ContainsKey(entry.Code) && about < WaveFemalesMax)
        {
            packUncapped = true;
            try
            {
                // (The wave's size follows the world's spawn setting, at least one)
                int wave = Math.Max(1, (int)Math.Round(Setting.Spawns));
                for (int i = 0; i < wave && about + i < WaveFemalesMax; i++)
                    if (TrySpawn(cause, AssessmentOf(cause), entry, Encounter.Hunt))
                        foreach (Entity moth in lastPack.ToList()) AiTaskMoth.Rally(moth, cause);
            }
            finally { packUncapped = false; }
        }
        if (remaining > 1) sapi.Event.RegisterCallback(_ => SendWave(cause, remaining - 1), WaveIntervalMs);
    }

    // ================= Clump juveniles =================

    /// <summary>
    /// Puts down a juvenile Clump (a remnant has grown one) as an ambusher the director owns, hunting the nearest
    /// player. The engine scales a model per type, not per entity, so it is full size, with only
    /// <see cref="JuvenileHealth"/> health. Null if it could not.
    /// </summary>
    public Entity SpawnJuvenileClump(Vec3d at, Entity target)
    {
        if (layout == null || target == null || !Setting.Entities || Paused || !types.TryGetValue(Roster.Clump, out EntityProperties type)) return null;
        // (Only for a player in danger: otherwise it waits)
        if (!target.Alive || (target is EntityPlayer player ? player.Player?.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator : !Senses.IsTestTarget(target))
            || AssessmentOf(target).Band == MenaceBand.Safe) return null;
        Entity clump = Spawn(type, at, target, Encounter.Stalk, passive: false);
        if (clump?.GetBehavior<EntityBehaviorHealth>() is { } health)
        {
            health.SetMaxHealthModifiers("backrooms-danger", JuvenileHealth - health.BaseMaxHealth);
            health.Health = health.MaxHealth;
        }
        if (Logging) sapi.Logger.Notification("[backrooms] a juvenile Clump grows at {0:0},{1:0},{2:0}", at.X, at.Y, at.Z);
        return clump;
    }

    // ================= Commands =================

    private void RegisterHiveCommands(ICoreServerAPI api, IChatCommand command)
    {
        var parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("hiveheart")
                .WithDescription("Puts down hive hearts at the nearest Deathmoth hive den (within about 100 blocks of you, or of the latest straw dummy from the console), as if it had just been entered, and says where it is. 'hiveheart break' breaks the nearest heart within 24 blocks as you (or the dummy) would: the alarm and the waves")
                .WithArgs(parsers.OptionalWord("what"))
                .HandleWith(OnHiveHeartCommand)
            .EndSubCommand()
            .BeginSubCommand("remnant")
                .WithDescription("Clump remnants: 'place' puts one in front of you (or the latest straw dummy), 'grow' makes every loaded one ripe (a player within 48 blocks then lets it grow at its next check, within 10 seconds), 'burn' burns every loaded one away as a torch would")
                .WithArgs(parsers.Word("what"))
                .HandleWith(OnRemnantCommand)
            .EndSubCommand();
    }

    private TextCommandResult OnHiveHeartCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        Entity who = args.Caller.Entity ?? LatestDummy(args);
        if (who == null) return TextCommandResult.Error("From the console, put a straw dummy down first (/backrooms dummy place <level>)");
        int px = (int)Math.Floor(who.Pos.X), pz = (int)Math.Floor(who.Pos.Z);
        if (!args.Parsers[0].IsMissing && ((string)args[0]).Trim().Equals("break", StringComparison.OrdinalIgnoreCase)) return BreakNearestHeart(who);
        (DenKind Kind, int X, int Z)? best = null;
        double bestDistance = double.MaxValue;
        for (int dz = -4; dz <= 4; dz++)
            for (int dx = -4; dx <= 4; dx++)
            {
                if (layout.DenNear(px + dx * WorldLayout.MacroSize, pz + dz * WorldLayout.MacroSize) is not { Kind: DenKind.Hive } den) continue;
                double d = Math.Sqrt((den.X - px) * (double)(den.X - px) + (den.Z - pz) * (double)(den.Z - pz));
                if (d < bestDistance) { bestDistance = d; best = den; }
            }
        if (best is not { } found) return TextCommandResult.Error("No Deathmoth hive den within about 100 blocks");
        if (bestDistance > 40) return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "The nearest hive den is at {0} {1}, {2:0} blocks away: go within 40 blocks to put its hearts down", found.X, found.Z, bestDistance));
        int placed = PlaceHearts(found.X, found.Z, (int)Math.Floor(who.Pos.Y));
        densDone.Add(DenKey(found.X, found.Z));
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "Hive den at {0} {1} ({2:0} blocks away): {3} hearts put down", found.X, found.Z, bestDistance, placed));
    }

    private TextCommandResult BreakNearestHeart(Entity who)
    {
        Block heart = sapi.World.GetBlock(new AssetLocation(HiveHeartCode));
        if (heart == null) return TextCommandResult.Error("The hive heart block is missing");
        IBlockAccessor ba = sapi.World.BlockAccessor;
        BlockPos best = null;
        double bestDistance = double.MaxValue;
        var at = new BlockPos(0);
        int x0 = (int)Math.Floor(who.Pos.X), y0 = (int)Math.Floor(who.Pos.Y), z0 = (int)Math.Floor(who.Pos.Z);
        for (int dy = -6; dy <= 6; dy++)
            for (int dz = -24; dz <= 24; dz++)
                for (int dx = -24; dx <= 24; dx++)
                {
                    if (ba.GetBlock(at.Set(x0 + dx, y0 + dy, z0 + dz)).BlockId != heart.BlockId) continue;
                    double d = dx * dx + dy * dy + dz * dz;
                    if (d < bestDistance) { bestDistance = d; best = at.Copy(); }
                }
        if (best == null) return TextCommandResult.Error("No hive heart within 24 blocks");
        HiveHeartBroken(best, who);
        ba.SetBlock(0, best);
        return TextCommandResult.Success($"Broke the hive heart at {best.X} {best.Y} {best.Z}: the alarm, and {WaveCount} waves");
    }

    private TextCommandResult OnRemnantCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string what = ((string)args[0]).Trim().ToLowerInvariant();
        switch (what)
        {
            case "grow":
                int n = 0;
                foreach (BlockPos pos in BlockEntityClumpRemnant.Live.ToList())
                {
                    if (sapi.World.BlockAccessor.GetBlockEntity(pos) is not BlockEntityClumpRemnant remnant) continue;
                    remnant.Hasten();
                    n++;
                }
                return TextCommandResult.Success($"{n} remnants are ripe: they grow at their next check if a player is within {BlockEntityClumpRemnant.PlayerRange} blocks");
            case "burn":
                int burnt = 0;
                foreach (BlockPos pos in BlockEntityClumpRemnant.Live.ToList())
                {
                    if (sapi.World.BlockAccessor.GetBlockEntity(pos) is not BlockEntityClumpRemnant remnant) continue;
                    remnant.Burn();
                    burnt++;
                }
                return TextCommandResult.Success($"{burnt} remnants burnt");
            case "place":
                Entity who = args.Caller.Entity ?? LatestDummy(args);
                if (who == null) return TextCommandResult.Error("From the console, put a straw dummy down first (/backrooms dummy place <level>)");
                Vec3f view = who.Pos.GetViewVector();
                double length = Math.Max(1e-3, Math.Sqrt(view.X * view.X + view.Z * view.Z));
                Block block = sapi.World.GetBlock(new AssetLocation("backrooms:clumpremnant"));
                if (block == null) return TextCommandResult.Error("The remnant block is missing");
                // (Two blocks ahead if there is room, else the nearest empty floor round about)
                for (int ring = 0; ring < 5; ring++)
                {
                    double ox = ring == 0 ? view.X / length * 2 : ring == 1 ? 0 : ring == 2 ? 2 : ring == 3 ? 0 : -2;
                    double oz = ring == 0 ? view.Z / length * 2 : ring == 1 ? 2 : ring == 2 ? 0 : ring == 3 ? -2 : 0;
                    int x = (int)Math.Floor(who.Pos.X + ox), z = (int)Math.Floor(who.Pos.Z + oz);
                    int y = Senses.FindFloor(sapi.World, x, (int)Math.Floor(who.Pos.Y), z, 1, 3);
                    if (y == int.MinValue || sapi.World.BlockAccessor.GetBlock(new BlockPos(x, y, z)).BlockId != 0) continue;
                    sapi.World.BlockAccessor.SetBlock(block.BlockId, new BlockPos(x, y, z));
                    return TextCommandResult.Success($"A remnant at {x} {y} {z}");
                }
                return TextCommandResult.Error("No empty floor near");
            default:
                return TextCommandResult.Error("place, grow or burn");
        }
    }
}
