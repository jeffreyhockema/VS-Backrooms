using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>), found by walking the cells out
    /// from the region's middle and taking the first of each: the crack someone fell through (from the room and from under
    /// it), the kinds of room (finished, utility, store), a door in old panelling, a long look through the rooms, an
    /// Escherian stairwell (its door, and its stairs from the landing), a room of the dead (its bodies laid down first), the
    /// stairs down into the Flood, the Flood from a Dry Patch's doorway (once more with the far figure put in it), the Dry
    /// Patch and its dead elevator. Each looks from a free floor tile along the way it sees furthest, or back at its subject.
    /// </summary>
    public IEnumerable<Showcase.Spot> BasementShowcaseSpots(WorldGeometry geometry)
    {
        var spots = new List<Showcase.Spot>();
        var (cmx, cmz, radius) = BasementRegion;
        double feet = geometry.FloorFor(Basement) + 1;
        var taken = new HashSet<string>();

        void Add(string name, int mx, int mz, int lx, int lz, double heading, double pitch, string setup)
        {
            if (!taken.Add(name)) return;
            spots.Add(new Showcase.Spot(name, mx * MacroSize + lx + 0.5, feet, mz * MacroSize + lz + 0.5, heading, pitch, setup));
        }

        for (int ring = 0; ring <= Math.Min(radius - 2, 14) && taken.Count < ShowcaseOrder.Length; ring++)
            for (int dz = -ring; dz <= ring; dz++)
                for (int dx = -ring; dx <= ring; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != ring) continue;
                    int mx = cmx + dx, mz = cmz + dz;
                    if (LevelAt(mx, mz) != Basement) continue;
                    Tile[] tiles = CellTiles(mx, mz);
                    BasementZone zone = BasementCellZone(mx, mz);
                    if (zone == BasementZone.Cellar) ShowcaseCellar(tiles, mx, mz, Add);
                    else ShowcaseFlood(tiles, mx, mz, zone == BasementZone.Patch, Add);
                }

        spots.Sort((a, b) => Array.IndexOf(ShowcaseOrder, a.Name).CompareTo(Array.IndexOf(ShowcaseOrder, b.Name)));
        // (The way in, in other levels, and out at the top of a crack: WorldLayout.LevelBasement.Links.cs)
        spots.AddRange(BasementLinkShowcaseSpots(geometry));
        return spots;
    }

    /// <summary>The spots, in the order a review reads best.</summary>
    private static readonly string[] ShowcaseOrder =
    {
        "crack-room", "crack-up", "furnace", "fusebox", "laundry", "workshop", "rec-room", "hall", "root-cellar", "store-shelves",
        "finished", "utility", "store", "panel-door", "long-view", "stairwell-door", "stairwell-stairs",
        "dead", "lone-body", "flood-stairs", "flood-passage", "flood-figure", "dry-patch", "lift",
    };

    private static readonly (int Dx, int Dz)[] ShowcaseDirs = { (0, -1), (1, 0), (0, 1), (-1, 0) };

    private static double ShowcaseHeading(int dx, int dz) => dx == 0 ? (dz < 0 ? 0 : 180) : (dx > 0 ? 90 : 270);

    private static (int Dx, int Dz) PierStep(ArchPier p) => p switch
    {
        ArchPier.West => (-1, 0),
        ArchPier.East => (1, 0),
        ArchPier.North => (0, -1),
        _ => (0, 1),
    };

    /// <summary>Whether a tile can be seen through (open floor, a doorway with its door standing open, water).</summary>
    private static bool ShowcaseClear(Tile[] tiles, int x, int z)
    {
        if (x < 0 || z < 0 || x >= MacroSize || z >= MacroSize) return false;
        Tile t = tiles[TileIndex(x, z)];
        if (t.Kind == TileKind.Doorway) return t.Variant != Props.BasementDoor || (t.Stack & 3) == 1;
        if (t.Kind == TileKind.Water) return true;
        return t.Kind == TileKind.Floor && t.Detail != BasementTower && (t.Variant == 0 && t.Stack == 0 && !t.SupplyBox || BasementWalkThrough(t.Variant));
    }

    /// <summary>Whether someone can stand on a tile: free dry floor, under the ceiling.</summary>
    private static bool ShowcaseStand(Tile[] tiles, int x, int z)
    {
        if (x < 1 || z < 1 || x >= MacroSize - 1 || z >= MacroSize - 1) return false;
        Tile t = tiles[TileIndex(x, z)];
        return t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox && t.Detail == 0 && t.Ceiling != CeilingKind.BasementOpen;
    }

    private static int ShowcaseRun(Tile[] tiles, int x, int z, int dx, int dz, int max)
    {
        int n = 0;
        while (n < max && ShowcaseClear(tiles, x + dx * (n + 1), z + dz * (n + 1))) n++;
        return n;
    }

    /// <summary>From a free tile with a wall at its back, the way it sees furthest over clear tiles; null if none sees five or more.</summary>
    private static (int X, int Z, int Dx, int Dz)? ShowcaseBestView(Tile[] tiles, Func<Tile, bool> where, int max = 30)
    {
        (int, int, int, int)? best = null;
        int bestRun = 4;
        for (int z = 1; z < MacroSize - 1; z++)
            for (int x = 1; x < MacroSize - 1; x++)
            {
                if (!ShowcaseStand(tiles, x, z) || !where(tiles[TileIndex(x, z)])) continue;
                foreach (var (dx, dz) in ShowcaseDirs)
                {
                    if (ShowcaseClear(tiles, x - dx, z - dz)) continue; // (a wall at its back)
                    int run = ShowcaseRun(tiles, x, z, dx, dz, max);
                    if (run > bestRun) { bestRun = run; best = (x, z, dx, dz); }
                }
            }
        return best;
    }

    /// <summary>A free tile a few steps out from a thing along the way it faces (nothing in between), looking back at it.</summary>
    private static (int X, int Z, double Heading)? ShowcaseFacing(Tile[] tiles, int x, int z, int dx, int dz, int far, int near)
    {
        for (int k = far; k >= near; k--)
        {
            int sx = x + dx * k, sz = z + dz * k;
            if (!ShowcaseStand(tiles, sx, sz)) continue;
            bool seen = true;
            for (int j = 1; j < k && seen; j++) seen = ShowcaseClear(tiles, x + dx * j, z + dz * j);
            if (seen) return (sx, sz, ShowcaseHeading(-dx, -dz));
        }
        return null;
    }

    private void ShowcaseCellar(Tile[] tiles, int mx, int mz, Action<string, int, int, int, int, double, double, string> add)
    {
        int bones = 0, bx = -1, bz = -1, towerX = int.MaxValue, towerZ = int.MaxValue;
        for (int z = 0; z < MacroSize; z++)
            for (int x = 0; x < MacroSize; x++)
            {
                Tile t = tiles[TileIndex(x, z)];
                if (t.Detail == BasementTower) { towerX = Math.Min(towerX, x); towerZ = Math.Min(towerZ, z); }
                if (t.Variant is Props.BonePile or Props.Ribcage or Props.JawSkeleton) { bones++; bx = x; bz = z; }
            }

        // The crack: from the room's edge on a line through its middle, looking at the rubble and up into it; and from under it
        for (int z = 1; z < MacroSize - 1; z++)
            for (int x = 1; x < MacroSize - 1; x++)
            {
                if (tiles[TileIndex(x, z)].Detail != BasementCrackMiddle) continue;
                int bestD = 0, bdx = 0, bdz = 0;
                foreach (var (dx, dz) in ShowcaseDirs)
                {
                    int d = ShowcaseRun(tiles, x, z, dx, dz, 6);
                    while (d > 3 && !ShowcaseStand(tiles, x + dx * d, z + dz * d)) d--;
                    if (d > bestD && ShowcaseStand(tiles, x + dx * d, z + dz * d)) { bestD = d; bdx = dx; bdz = dz; }
                }
                if (bestD >= 4) add("crack-room", mx, mz, x + bdx * bestD, z + bdz * bestD, ShowcaseHeading(-bdx, -bdz), 24, null);
                // (Standing in the opening beside the heap, looking up it)
                foreach (var (dx, dz) in ShowcaseDirs)
                {
                    Tile t = tiles[TileIndex(x + dx, z + dz)];
                    if (t.Kind != TileKind.Floor || t.Variant != 0 && !BasementWalkThrough(t.Variant)) continue;
                    add("crack-up", mx, mz, x + dx, z + dz, ShowcaseHeading(-dx, -dz), 72, null);
                    break;
                }
            }

        // An Escherian stairwell: its door from across the room, and its stairs from the landing inside
        if (towerX != int.MaxValue)
        {
            int doorX = towerX + 2, doorZ = towerZ;
            if (ShowcaseFacing(tiles, doorX, doorZ, 0, -1, 6, 3) is (var sx, var sz, var h)) add("stairwell-door", mx, mz, sx, sz, h, 16, null);
            add("stairwell-stairs", mx, mz, towerX + 2, towerZ + 1, 270, -35, null);
        }

        // A room of the dead, its bodies laid down first; or someone who sat down in a corner and stayed
        if (bones >= 2)
        {
            var (dx, dz) = PierStep(tiles[TileIndex(bx, bz)].Pier);
            if (ShowcaseFacing(tiles, bx, bz, dx, dz, 6, 3) is (var sx, var sz, var h))
                add("dead", mx, mz, sx, sz, h, -14, $"/basementbodies {mx * MacroSize + bx} {mz * MacroSize + bz}");
        }
        for (int z = 1; z < MacroSize - 1; z++)
            for (int x = 1; x < MacroSize - 1; x++)
            {
                if (tiles[TileIndex(x, z)].Variant != Props.BasementBody || bones >= 2) continue;
                foreach (var (dx, dz) in ShowcaseDirs)
                    if (ShowcaseFacing(tiles, x, z, dx, dz, 4, 2) is (var sx, var sz, var h))
                    {
                        add("lone-body", mx, mz, sx, sz, h, -28, $"/basementbodies {mx * MacroSize + x} {mz * MacroSize + z}");
                        break;
                    }
            }

        // The kinds of room, by what stands in them
        void Prop(string name, Func<Tile, bool> what, double pitch)
        {
            for (int z = 1; z < MacroSize - 1; z++)
                for (int x = 1; x < MacroSize - 1; x++)
                {
                    Tile t = tiles[TileIndex(x, z)];
                    if (!what(t)) continue;
                    var (dx, dz) = PierStep(t.Pier);
                    if (ShowcaseFacing(tiles, x, z, dx, dz, 6, 4) is (var sx, var sz, var h)) { add(name, mx, mz, sx, sz, h, pitch, null); return; }
                }
        }
        Prop("utility", t => t.Variant == Props.BasementBoiler, -4);
        // Round 3: the rooms by what they are for
        Prop("furnace", t => t.Variant == Props.BasementFurnace, 12);
        Prop("fusebox", t => t.Overhead == Overheads.BasementFuseBox && t.Variant == 0, 6);
        Prop("laundry", t => t.Variant == Props.Laundry && t.Stack == 0, 6);
        Prop("workshop", t => t.Variant == Props.BasementBench && t.Stack == 0, 0);
        Prop("store-shelves", t => t.Variant is Props.BasementShelving or Props.BasementBoxes, 2);
        for (int z = 1; z < MacroSize - 1; z++)
            for (int x = 1; x < MacroSize - 1; x++)
            {
                Tile t = tiles[TileIndex(x, z)];
                if (t.Variant != Props.BasementPoolTable || t.Stack != 0) continue;
                // (from beside the table's long side, back across it to the room)
                var (rx, rz) = BasementRightOf(t.Pier);
                foreach (var (dx, dz) in new[] { (rz, rx), (-rz, -rx) })
                    if (ShowcaseFacing(tiles, x, z, dx, dz, 5, 2) is (var sx, var sz, var h)) { add("rec-room", mx, mz, sx, sz, h, -14, null); break; }
            }
        // A hallway between its stud walls, from one end
        int hallRun = 0, hx = 0, hz = 0;
        double hh = 0;
        for (int z = 1; z < MacroSize - 1; z++)
            for (int x = 1; x < MacroSize - 1; x++)
            {
                if (!ShowcaseStand(tiles, x, z)) continue;
                foreach (var (dx, dz) in ShowcaseDirs)
                {
                    Tile side = tiles[TileIndex(x + dz, z + dx)];
                    if (side.Kind != TileKind.Wall || side.Pattern != WallPattern.BasementStuds) continue;
                    int run = ShowcaseRun(tiles, x, z, dx, dz, 28);
                    if (run > hallRun && run >= 10) { hallRun = run; hx = x; hz = z; hh = ShowcaseHeading(dx, dz); }
                }
            }
        if (hallRun > 0) add("hall", mx, mz, hx, hz, hh, -2, null);
        if (ShowcaseBestView(tiles, t => t.Floor == FloorKind.BasementEarth, 8) is (var ex, var ez, var edx, var edz))
            add("root-cellar", mx, mz, ex, ez, ShowcaseHeading(edx, edz), -10, null);
        Prop("store", t => t.Variant is Props.FurniturePile or Props.Suitcase, -10);
        if (ShowcaseBestView(tiles, t => t.Floor is FloorKind.BasementCarpet or FloorKind.BasementCarpetWorn, 12) is (var fx, var fz, var fdx, var fdz))
            add("finished", mx, mz, fx, fz, ShowcaseHeading(fdx, fdz), -8, null);

        // A door in old panelling, from a few steps off
        bool door = false;
        for (int z = 2; z < MacroSize - 2 && !door; z++)
            for (int x = 2; x < MacroSize - 2 && !door; x++)
            {
                Tile t = tiles[TileIndex(x, z)];
                if (t.Kind != TileKind.Doorway || t.Variant != Props.BasementDoor || t.Pattern != WallPattern.BasementPanel || t.Detail != 0) continue;
                bool wallAlongX = tiles[TileIndex(x - 1, z)].Kind is TileKind.Wall or TileKind.Doorway;
                foreach (int s in new[] { -1, 1 })
                {
                    int dx = wallAlongX ? 0 : s, dz = wallAlongX ? s : 0;
                    if (ShowcaseFacing(tiles, x, z, dx, dz, 4, 3) is (var sx, var sz, var h)) { add("panel-door", mx, mz, sx, sz, h, 4, null); door = true; break; }
                }
            }

        // The furthest look through the rooms (open doors let it through)
        if (ShowcaseBestView(tiles, _ => true) is (var lx, var lz, var ldx, var ldz) && ShowcaseRun(tiles, lx, lz, ldx, ldz, 30) >= 13)
            add("long-view", mx, mz, lx, lz, ShowcaseHeading(ldx, ldz), -3, null);
    }

    private void ShowcaseFlood(Tile[] tiles, int mx, int mz, bool patch, Action<string, int, int, int, int, double, double, string> add)
    {
        // The stairs down into the water from the Cellar: from the dry floor at their top, looking down the passage
        bool Step(int ax, int az) => ax >= 0 && az >= 0 && ax < MacroSize && az < MacroSize && tiles[TileIndex(ax, az)].Kind == TileKind.Water && tiles[TileIndex(ax, az)].Height == 2;
        for (int z = 0; z < MacroSize; z++)
            for (int x = 0; x < MacroSize; x++)
            {
                if (!Step(x, z) || x != 0 && z != 0 && x != MacroSize - 1 && z != MacroSize - 1) continue;
                var (ox, oz) = PierStep(tiles[TileIndex(x, z)].Pier);
                int ax = oz != 0 ? 1 : 0, az = ox != 0 ? 1 : 0; // (along the stair)
                if (!Step(x + ax, z + az) || !Step(x - ax, z - az) || ShowcaseRun(tiles, x, z, -ox, -oz, 20) < 6) continue;
                // (The dry tile past the top step lies in the next cell; the spot is given from this one)
                add("flood-stairs", mx, mz, x + ox * 2, z + oz * 2, ShowcaseHeading(-ox, -oz), -14, null);
            }

        if (!patch) return;
        const int lo = BasementPatchLo, hi = BasementPatchHi;
        // The Flood from a doorway of the Dry Patch, along the passage out of it (once more with the figure put in it, far off)
        foreach (var (dx, dz) in ShowcaseDirs)
            foreach (int along in new[] { BasementNode0 + BasementPitch, BasementNode0 + 2 * BasementPitch })
            {
                int x = dx != 0 ? (dx < 0 ? lo : hi) : along, z = dz != 0 ? (dz < 0 ? lo : hi) : along;
                Tile door = tiles[TileIndex(x, z)];
                if (door.Kind != TileKind.Floor || door.Zone != (byte)BasementZone.Patch || ShowcaseRun(tiles, x, z, dx, dz, 20) < 6) continue;
                add("flood-passage", mx, mz, x - dx, z - dz, ShowcaseHeading(dx, dz), -12, null);
                add("flood-figure", mx, mz, x - dx, z - dz, ShowcaseHeading(dx, dz), -6, "/backrooms encounter bacteria glimpse");
            }
        // The Dry Patch from the middle of a side, between two of its pillars, across to the far one
        add("dry-patch", mx, mz, (lo + hi) / 2 - 1, lo + 1, 180, -8, null);
        // Its elevator, dead, from across the room
        for (int z = lo; z <= hi; z++)
            for (int x = lo; x <= hi; x++)
            {
                Tile t = tiles[TileIndex(x, z)];
                if (t.Kind != TileKind.Wall || t.Pattern != WallPattern.BasementLift || (t.Stack & 1) != 0) continue;
                var (dx, dz) = PierStep(t.Pier);
                if (ShowcaseFacing(tiles, x, z, dx, dz, 7, 4) is (var sx, var sz, var h)) add("lift", mx, mz, sx, sz, h, 6, null);
            }
    }
}
