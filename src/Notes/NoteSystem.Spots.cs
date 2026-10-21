using System;
using System.Collections.Generic;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Notes;

/// <summary>
/// Where notes come from besides the block types' own drops (docs/design/notes-plan.md, section 6):
/// <list type="bullet">
/// <item><b>More ordinary notes in Levels 0 and 1</b> (about double), and a few more from desks, bedrolls, runners'
/// remains and The End's desks everywhere.</item>
/// <item><b>Folded notes</b> (the rare class) from what was left where few go: more the deeper the level, three times
/// as likely behind a locked door, half again at the far edge of a ring, and often in a den's cache or a Red Room.</item>
/// <item><b>Notes lying loose</b> where a story puts one (<see cref="WorldLayout.NoteSpots"/>), set down the first
/// time a player comes near the cell and never again.</item>
/// </list>
/// Rolls are hashed from the block's position, so breaking the same box twice (a creative re-place) changes nothing.
/// </summary>
public partial class NoteSystem
{
    private const string SpotsKey = "backrooms-notespots";
    private const ulong SaltExtra = 0x7080, SaltRare = 0x7081, SaltKind = 0x7082;

    /// <summary>What a broken block may give besides its own drops: (path, extra ordinary note in Levels 0-1, extra anywhere, folded note base chance).</summary>
    private static readonly (string Path, double ExtraNear, double ExtraAll, double Rare)[] Sources =
    {
        ("supplybox-torn", 0.06, 0, 0),
        ("supplybox", 0.10, 0, 0.012),
        ("crate-open", 0.02, 0, 0),
        ("crate", 0.03, 0, 0.008),
        ("backpack", 0, 0, 0.08),
        ("bedroll", 0, 0.03, 0.04),
        ("tent", 0, 0, 0.04),
        ("sleepingbag", 0, 0.03, 0.04),
        ("camptent", 0, 0, 0.04),
        ("filingcabinet", 0, 0.01, 0.01),
        ("writingdesk", 0, 0.01, 0.01),
        ("desk", 0, 0.02, 0.01),
        ("run-remains", 0, 0.25, 0.15),
        ("end-desk", 0, 0.06, 0.03),
    };

    private static readonly string[] Kinds = { "door", "way", "cache", "refuge" };
    private static readonly double[] KindWeights = { 0.3, 0.25, 0.3, 0.15 };

    private readonly HashSet<long> spotCells = new();
    private readonly Dictionary<int, int> sourceOf = new();
    private readonly Dictionary<string, int> looseNoteIds = new();

    private void StartSources(ICoreServerAPI api)
    {
        foreach (Block block in api.World.Blocks)
        {
            if (block?.Code == null || block.Code.Domain != "backrooms") continue;
            string path = block.Code.Path;
            for (int i = 0; i < Sources.Length; i++)
                if (path == Sources[i].Path || path.StartsWith(Sources[i].Path + "-", StringComparison.Ordinal))
                {
                    // (torn and emptied ones are listed first, so they never count as sealed)
                    sourceOf[block.BlockId] = i;
                    break;
                }
            if (path.StartsWith("loosenote-", StringComparison.Ordinal)) looseNoteIds[path.Substring("loosenote-".Length)] = block.BlockId;
        }
        api.Event.DidBreakBlock += OnBrokeBlock;
        api.Event.RegisterGameTickListener(OnSpotTick, 3000, 1200);
    }

    private void OnBrokeBlock(IServerPlayer byPlayer, int oldBlockId, BlockSelection blockSel)
    {
        if (layout == null || blockSel == null || !sourceOf.TryGetValue(oldBlockId, out int si)) return;
        if (byPlayer?.WorldData.CurrentGameMode != EnumGameMode.Survival) return;
        var source = Sources[si];
        BlockPos pos = blockSel.Position;
        int mx = WorldLayout.MacroOf(pos.X), mz = WorldLayout.MacroOf(pos.Z);
        int level = layout.LevelAt(mx, mz);
        ulong h = Hashing.Hash((ulong)sapi.World.Seed, pos.X * 31 + pos.Y, pos.Z, SaltExtra);
        var at = new Vec3d(pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5);

        // More ordinary notes
        double extra = source.ExtraAll + (level <= 1 ? source.ExtraNear : 0);
        if (extra > 0 && Hashing.Unit(h) < extra)
        {
            string kind = source.Path == "run-remains" ? "way" : source.Path == "end-desk" ? "door" : PickKind(Hashing.Hash((ulong)sapi.World.Seed, pos.X, pos.Z, SaltKind));
            Spawn("wanderernote-" + kind, at);
        }

        // A folded note
        double rare = source.Rare;
        bool box = source.Path == "supplybox";
        if (box && layout.DenNear(pos.X, pos.Z) is { } den && (den.X - pos.X) * (den.X - pos.X) + (den.Z - pos.Z) * (den.Z - pos.Z) <= 64) rare += 0.25;
        if (box && level == 0 && layout.IsRedRoom(mx, mz)) rare += 0.15;
        if (rare <= 0) return;
        rare *= 1 + 2 * Danger.OfLevel(level);
        if (layout.TileAt(pos.X, pos.Z).Sealed) rare *= 3;
        if (level <= 10 && layout.LevelDepth(pos.X, pos.Z, level) >= 0.85) rare *= 1.5;
        if (Hashing.Unit(Hashing.Hash((ulong)sapi.World.Seed, pos.X * 31 + pos.Y, pos.Z, SaltRare)) < Math.Min(0.6, rare)) Spawn("wanderernote-folded", at);
    }

    private static string PickKind(ulong h)
    {
        double r = Hashing.Unit(h), sum = 0;
        for (int i = 0; i < Kinds.Length; i++)
        {
            sum += KindWeights[i];
            if (r < sum) return Kinds[i];
        }
        return Kinds[0];
    }

    private void Spawn(string code, Vec3d at)
    {
        Item item = sapi.World.GetItem(new AssetLocation("backrooms", code));
        if (item != null) sapi.World.SpawnItemEntity(new ItemStack(item), at);
    }

    // ================= Notes lying loose =================

    private static long CellKey(int mx, int mz) => ((long)mx << 32) ^ (uint)mz;

    private void OnSpotTick(float dt)
    {
        if (layout == null || looseNoteIds.Count == 0) return;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online.Entity is not { Alive: true } entity) continue;
            MarkVisited(entity);
            int pmx = WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), pmz = WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z));
            for (int mz = pmz - 1; mz <= pmz + 1; mz++)
                for (int mx = pmx - 1; mx <= pmx + 1; mx++)
                {
                    long cell = CellKey(mx, mz);
                    if (spotCells.Contains(cell)) continue;
                    if (TryPlaceSpots(mx, mz)) spotCells.Add(cell);
                }
        }
    }

    /// <summary>Sets down a cell's loose notes. False (to try again later) while any of their chunks is not loaded.</summary>
    private bool TryPlaceSpots(int mx, int mz)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int x0 = mx * WorldLayout.MacroSize, z0 = mz * WorldLayout.MacroSize;
        if (ba.GetChunkAtBlockPos(new BlockPos(x0 + WorldLayout.MacroSize / 2, geometry.FloorY, z0 + WorldLayout.MacroSize / 2)) == null) return false;
        List<(int Lx, int Lz, string Kind)> spots = layout.NoteSpots(mx, mz);
        if (spots.Count == 0) return true;
        int floor = geometry.FloorFor(layout.LevelAt(mx, mz));
        // Every spot's chunk first: a cell is set down whole or not at all, so a note already taken is never put back
        // when the cell is tried again
        foreach (var (lx, lz, _) in spots)
            if (ba.GetChunkAtBlockPos(new BlockPos(x0 + lx, floor, z0 + lz)) == null) return false;
        foreach (var (lx, lz, kind) in spots)
        {
            if (!looseNoteIds.TryGetValue(kind, out int id)) continue;
            int x = x0 + lx, z = z0 + lz;
            for (int y = floor - 1; y <= floor + 3; y++)
            {
                var p = new BlockPos(x, y, z);
                Block here = ba.GetBlock(p), below = ba.GetBlock(p.DownCopy());
                if (here.Id != 0 || below.Id == 0 || !below.SideSolid[BlockFacing.UP.Index]) continue;
                ba.SetBlock(id, p);
                break;
            }
        }
        return true;
    }

    private void LoadSpots()
    {
        byte[] data = sapi.WorldManager.SaveGame.GetData(SpotsKey);
        if (data == null) return;
        for (int i = 0; i + 8 <= data.Length; i += 8) spotCells.Add(BitConverter.ToInt64(data, i));
    }

    private void SaveSpots()
    {
        var data = new byte[spotCells.Count * 8];
        int i = 0;
        foreach (long cell in spotCells) { BitConverter.GetBytes(cell).CopyTo(data, i); i += 8; }
        sapi.WorldManager.SaveGame.StoreData(SpotsKey, data);
    }
}
