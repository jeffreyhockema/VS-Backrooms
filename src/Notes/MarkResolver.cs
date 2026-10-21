using System;
using System.Collections.Generic;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Notes;

/// <summary>
/// Which part of a mark's search to run: all of it (the main thread), only what reads the layout (a worker thread: the
/// slow part, on a layout of its own), or only what reads the loaded world (the main thread, after the worker found nothing).
/// </summary>
public enum MarkSearch { Full, Layout, World }

/// <summary>What a layout-only search left for the main thread: nothing, the world's part, or the whole search.</summary>
public enum MarkDefer { None, World, Full }

/// <summary>
/// What a note marks on the map, from where it is read (docs/design/notes-plan.md, section 4). The paper's own kinds keep
/// their old searches (door: the nearest gate out of the level; way: the nearest elevator, stairwell or pit; cache:
/// the nearest unopened box; refuge: the nearest safe place); entries add marks of their own (the Manila Room, a
/// manhole, the barn wall, a den, the Hub's doors). Where a level has no ring gates (Level 11 and every noclip region)
/// a door resolves through that level's own exits, else through the nearest threshold block in the loaded world.
/// Every search takes a <c>skip</c>: places not to name (what the reader's earlier notes already marked), so each note
/// points somewhere new while there is somewhere new to point at.
/// </summary>
public sealed class MarkResolver
{
    private readonly ICoreServerAPI sapi;
    private readonly WorldLayout layout;
    private readonly WorldGeometry geometry;
    private readonly HashSet<int> thresholdBlocks = new();

    public MarkResolver(ICoreServerAPI sapi, WorldLayout layout, WorldGeometry geometry)
    {
        this.sapi = sapi;
        this.layout = layout;
        this.geometry = geometry;
        foreach (Block block in sapi.World.Blocks)
            if (block != null && block.Id != 0 && block.HasBehavior<BlockBehaviorThreshold>()) thresholdBlocks.Add(block.Id);
    }

    /// <summary>
    /// The place a mark of this kind points at, from (x, z) in the given level (its id, not the 6.1 key), or null.
    /// <paramref name="far"/> doubles the search (a folded note's careful directions); <paramref name="skip"/> names
    /// places not to point at.
    /// </summary>
    public NoteMark Resolve(string kind, double px, double py, double pz, int level, bool far, System.Func<int, int, bool> skip = null)
        => Resolve(kind, px, py, pz, level, far, MarkSearch.Full, out _, skip);

    /// <summary>
    /// As above, but only the given part of the search (see <see cref="MarkSearch"/>). A layout-only search never touches the
    /// world (block accessor, the threshold system) and says in <paramref name="defer"/> what is left for the main thread.
    /// The layout part and then the world part together give exactly what the full search gives.
    /// </summary>
    public NoteMark Resolve(string kind, double px, double py, double pz, int level, bool far, MarkSearch search, out MarkDefer defer, System.Func<int, int, bool> skip = null)
    {
        defer = MarkDefer.None;
        // (Only these kinds have a part that reads the world)
        if (search == MarkSearch.World && kind is not ("door" or "way")) return null;
        bool slow = search != MarkSearch.World, world = search != MarkSearch.Layout;
        int x = (int)Math.Floor(px), z = (int)Math.Floor(pz);
        int k = far ? 2 : 1;
        (int X, int Z)? at = null;
        string title = null, icon = "x", ps = null;
        switch (kind)
        {
            case "door":
            {
                bool searchedWays = false;
                if (level <= 10 && !WorldLayout.IsNoclipRegion(level))
                {
                    var gate = !slow ? null : layout.NearestGate(x, z, level, 1200 * k, level + 1, skip) ?? layout.NearestGate(x, z, level, 1200 * k, -1, skip);
                    if (gate is { } g)
                    {
                        at = (g.X, g.Z);
                        title = Lang.Get("backrooms:waypoint-note-door", Lang.Get("backrooms:levelname", g.To));
                    }
                }
                else at = RegionExit(x, py, z, level, out title, out searchedWays, search, ref defer, skip);
                ps = "door";
                if (at == null)
                {
                    // (Not again where the region's exit already was the search for a way: in Level 94 that search alone is a second)
                    if (defer == MarkDefer.Full || searchedWays) return null;
                    NoteMark way = Resolve("way", px, py, pz, level, far, search, out MarkDefer wayDefer, skip);
                    if (wayDefer != MarkDefer.None) defer = wayDefer;
                    return way != null ? Postscript(way, "door") : null;
                }
                break;
            }
            case "way":
                at = (slow ? layout.NearestThreshold(x, z, level, 320 * k, skip) : null) ?? (world ? NearestThresholdBlock(x, z, level, 96 * k, skip) : Defer(ref defer, MarkDefer.World));
                title = Lang.Get("backrooms:waypoint-note-way");
                icon = "spiral";
                ps = "way";
                break;
            case "cache":
                at = layout.NearestCache(x, z, level, 256 * k, skip);
                title = Lang.Get("backrooms:waypoint-note-cache");
                icon = "vessel";
                ps = "cache";
                break;
            case "refuge":
                at = layout.NearestRefuge(x, z, level, 1600, skip);
                title = Lang.Get("backrooms:waypoint-note-refuge");
                icon = "star1";
                ps = "refuge";
                break;
            case "manila":
                at = level == 0 ? layout.NearestRefuge(x, z, 0, 2400, skip) : null;
                title = Lang.Get("backrooms:waypoint-note-manila");
                icon = "star1";
                ps = "refuge";
                break;
            case "den":
                at = layout.NearestDen(x, z, level, 400 * k, skip);
                title = Lang.Get("backrooms:waypoint-note-den");
                icon = "x";
                ps = "cache";
                break;
            case "manhole":
                at = level == 3 ? layout.NearestManhole(x, z, 320 * k, skip) : null;
                title = Lang.Get("backrooms:waypoint-note-manhole");
                icon = "spiral";
                ps = "way";
                break;
            case "barnwall":
                at = level == 10 ? layout.NearestBarnWall(x, z, 480 * k, skip) : null;
                title = Lang.Get("backrooms:waypoint-note-barnwall");
                icon = "spiral";
                ps = "way";
                break;
            case "hubdoor":
                at = layout.NearestHubEntrance(x, z, level, level == 1 ? 1200 * k : 320 * k, skip);
                title = Lang.Get("backrooms:waypoint-note-hubdoor");
                icon = "spiral";
                ps = "way";
                break;
            case "redroom":
                at = level == 0 ? layout.NearestRedRoom(x, z, 1600 * k, skip) : null;
                title = Lang.Get("backrooms:waypoint-note-redroom");
                icon = "vessel";
                ps = "cache";
                break;
            case "endexit":
                at = level != WorldLayout.TheEnd ? null : world ? EndExit(x, z, 600 * k, skip) : Defer(ref defer, MarkDefer.Full);
                title = Lang.Get("backrooms:waypoint-note-endexit");
                icon = "star1";
                ps = "door";
                break;
            case "sunken":
                // (Level 7 from layout version 9: the buoy over a room on the seabed with air under its roof)
                at = level == 7 ? layout.NearestSunkenRoom(x, z, 640 * k, skip) : null;
                title = Lang.Get("backrooms:waypoint-note-sunken");
                icon = "vessel";
                ps = "cache";
                break;
            case "party":
                at = level == WorldLayout.FunLevel ? layout.NearestParty(x, z, 320, skip) : null;
                title = Lang.Get("backrooms:waypoint-note-party");
                icon = "star1";
                ps = "refuge";
                break;
        }
        if (at is not { } p) return null;
        double dx = p.X + 0.5 - px, dz = p.Z + 0.5 - pz;
        return new NoteMark
        {
            X = p.X, Z = p.Z, Level = level, Title = title, Icon = icon,
            Ps = $"backrooms:note-{ps}-{(int)(Hashing.Hash((ulong)sapi.World.Seed, p.X, p.Z, 0x707E) % 3) + 1}",
            Dir = Direction(dx, dz), Paces = Paces(dx, dz),
        };
    }

    private static NoteMark Postscript(NoteMark mark, string ps)
    {
        mark.Ps = mark.Ps.Replace("note-way-", "note-" + ps + "-");
        return mark;
    }

    /// <summary>Notes what a layout-only search had to leave for the main thread; no place yet.</summary>
    private static (int X, int Z)? Defer(ref MarkDefer defer, MarkDefer what)
    {
        if (what > defer) defer = what;
        return null;
    }

    private static bool Skipped(System.Func<int, int, bool> skip, int x, int z) => skip != null && skip(x, z);

    /// <summary>A way out of a level with no ring gates: its own exits where the level knows them, else the nearest threshold block.</summary>
    private (int X, int Z)? RegionExit(int x, double py, int z, int level, out string title, out bool searchedWays, MarkSearch search, ref MarkDefer defer, System.Func<int, int, bool> skip)
    {
        title = Lang.Get("backrooms:waypoint-note-way");
        searchedWays = false;
        switch (level)
        {
            case WorldLayout.TheEnd:
                title = Lang.Get("backrooms:waypoint-note-endexit");
                return search != MarkSearch.Layout ? EndExit(x, z, 600, skip) : Defer(ref defer, MarkDefer.Full);
            case WorldLayout.RunLevel:
            {
                // (One exit per lane: it is named again if it must be)
                int lane = layout.RunLaneAt(x, z);
                if (lane < 0 || lane >= WorldLayout.RunLanes) break;
                var plan = layout.RunPlan(lane);
                title = Lang.Get("backrooms:waypoint-note-runexit");
                return layout.RunWorld(lane, plan.ExitDoor.X, plan.ExitDoor.Z);
            }
            case WorldLayout.Hub:
            {
                (int X, int Z)? best = null;
                long bestD = long.MaxValue;
                foreach (int open in new[] { 1, 11, WorldLayout.HubSnackroomsDoor })
                {
                    if (layout.HubDoorOf(open) is not { } d || Skipped(skip, d.X, d.Z)) continue;
                    long dd = (long)(d.X - x) * (d.X - x) + (long)(d.Z - z) * (d.Z - z);
                    if (dd < bestD) { bestD = dd; best = (d.X, d.Z); }
                }
                title = Lang.Get("backrooms:waypoint-note-hubopen");
                return best;
            }
            case WorldLayout.Level3999:
            {
                // A lobby's revolving door (always out, to the Level 10 arcade), else a STAFF ONLY door (most are locked).
                // Layout only: the world's part (the threshold blocks) is left for the main thread, as for any other level
                if (search == MarkSearch.World) break;
                if (L3999DoorNear(x, z, u => u.Kind == WorldLayout.L3999Kind.Lobby, WorldLayout.IsL3999Revolving, skip) is { } revolving)
                {
                    title = Lang.Get("backrooms:waypoint-note-door", Lang.Get("backrooms:levelname", 10));
                    return revolving;
                }
                if (L3999DoorNear(x, z, u => u.Kind != WorldLayout.L3999Kind.Shuttered, WorldLayout.IsL3999StaffDoor, skip) is { } staff)
                {
                    title = Lang.Get("backrooms:waypoint-note-staffdoor");
                    return staff;
                }
                break;
            }
            case WorldLayout.Level188:
            {
                // The nearest fire exit (one per upper storey, at the corridor's bends), counting the storeys between
                if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.Level188) break;
                int floor = geometry.FloorFor(WorldLayout.Level188);
                double bestD = double.MaxValue;
                (int X, int Z, int Storey)? best = null;
                foreach (var (bx, bz, storey) in WorldLayout.L188FireDoors)
                {
                    int fx = layout.L188BuildX0 + bx, fz = layout.L188BuildZ0 + bz;
                    if (Skipped(skip, fx, fz)) continue;
                    double dy = floor + 4 * storey + 1 - py;
                    double d = (double)(fx - x) * (fx - x) + (double)(fz - z) * (fz - z) + 16 * dy * dy;
                    if (d < bestD) { bestD = d; best = (fx, fz, storey); }
                }
                if (best is not { } fire) break;
                int to = fire.Storey switch { 1 => 1, 2 => 5, 3 => 4, _ => 2 };
                title = Lang.Get("backrooms:waypoint-note-fireexit", Lang.Get("backrooms:levelname", to), fire.Storey);
                return (fire.X, fire.Z);
            }
        }
        searchedWays = true;
        return (search != MarkSearch.World ? layout.NearestThreshold(x, z, level, 320, skip) : null)
            ?? (search != MarkSearch.Layout ? NearestThresholdBlock(x, z, level, 128, skip) : Defer(ref defer, MarkDefer.World));
    }

    /// <summary>
    /// The nearest door of a kind in Level 3999 to (x, z), among the three nearest units that might have one (never in the
    /// Blackout), within 320 blocks of the reader. Layout only (worker-thread safe).
    /// </summary>
    private (int X, int Z)? L3999DoorNear(int x, int z, System.Func<WorldLayout.L3999Unit, bool> unit, System.Func<Tile, bool> door, System.Func<int, int, bool> skip)
    {
        const int Radius = 320, Reach = 48;
        (int X, int Z)? best = null;
        long bestD = long.MaxValue;
        foreach (var (cx, cz) in layout.L3999UnitsNear(x, z, unit, Radius, 3))
            for (int gz = cz - Reach; gz <= cz + Reach; gz++)
                for (int gx = cx - Reach; gx <= cx + Reach; gx++)
                {
                    long d = (long)(gx - x) * (gx - x) + (long)(gz - z) * (gz - z);
                    if (d >= bestD || !door(layout.TileAt(gx, gz)) || Skipped(skip, gx, gz)) continue;
                    bestD = d;
                    best = (gx, gz);
                }
        return best;
    }

    private (int X, int Z)? EndExit(int x, int z, int radius, System.Func<int, int, bool> skip)
    {
        var threshold = sapi.ModLoader.GetModSystem<ThresholdSystem>();
        var exits = layout.EndExitsNear(x, z, radius, (ex, ez) => threshold?.EndExitOpens(ex, ez) ?? true, skip == null ? 1 : 8);
        foreach (var exit in exits)
            if (!Skipped(skip, exit.X, exit.Z)) return exit;
        return null;
    }

    /// <summary>
    /// The nearest block that leads somewhere (any block with a threshold behaviour) within the radius, in the band of the
    /// level's floor, among the chunks that are loaded. Up to about 2.4 million block lookups at a radius of 256 (a folded note's doubled search), once per note.
    /// </summary>
    public (int X, int Z)? NearestThresholdBlock(int x, int z, int level, int radius, System.Func<int, int, bool> skip = null)
    {
        if (thresholdBlocks.Count == 0) return null;
        int floor = geometry.FloorFor(level);
        (int X, int Z)? best = null;
        long bestD = long.MaxValue;
        var min = new BlockPos(x - radius, Math.Max(1, floor - 2), z - radius);
        var max = new BlockPos(x + radius, floor + 6, z + radius);
        sapi.World.BlockAccessor.WalkBlocks(min, max, (block, bx, by, bz) =>
        {
            if (!thresholdBlocks.Contains(block.Id)) return;
            long d = (long)(bx - x) * (bx - x) + (long)(bz - z) * (bz - z);
            if (d < bestD && d <= (long)radius * radius && !Skipped(skip, bx, bz)) { bestD = d; best = (bx, bz); }
        });
        return best;
    }

    /// <summary>The compass direction of an offset, as a code (n, ne, …; north is -Z).</summary>
    public static string Direction(double dx, double dz)
    {
        int octant = (int)Math.Round(Math.Atan2(dz, dx) / (Math.PI / 4));
        return DirectionNames[((octant % 8) + 8) % 8];
    }

    private static readonly string[] DirectionNames = { "e", "se", "s", "sw", "w", "nw", "n", "ne" };

    /// <summary>The distance, rounded the way someone pacing it out would give it.</summary>
    public static int Paces(double dx, double dz)
    {
        double d = Math.Sqrt(dx * dx + dz * dz);
        int step = d < 60 ? 10 : d < 300 ? 25 : 50;
        return Math.Max(step, (int)Math.Round(d / step) * step);
    }
}
