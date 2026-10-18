using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// From layout version 9 each level keeps its own look right up to the wall between it and the next.
///
/// The wall between two levels is one tile thick and belongs to the cell on its east or south side (each cell owns its
/// west and north edges), so up to version 8 the level on the other side saw the next level's wall: Level 1's concrete
/// along the edge of Level 0, Level 0's wallpaper along the edge of Level 1, and so on round every ring. In version 9
/// the cell on the west or north side lines that wall with one of its own (<see cref="LineLevelWalls"/>): the wall
/// between the levels is two thick, each side shows its own face, and the way through a gate is a short passage
/// through both, the next level's doorway at its far end. Where the walls are laid from a plan larger than a cell
/// (Levels 0, 2 and 6), the hallway that runs along the wall moves in a tile with it, so it stays two wide
/// (<see cref="LiningWidens"/>). The Snackrooms keep Level 6's wall on the outside of theirs.
///
/// The only mixing left is at a gate: the tile of each side's floor in the way through, and the one before it, are
/// worn the way the next level begins (<see cref="WearThresholds"/>): Level 0's carpet worn through to the concrete
/// before Level 1, Level 4's grey carpet turned to the hotel's red before Level 5.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>
    /// Whether a cell lines the wall its neighbour (to the east or south) owns between them: where they are different
    /// levels, the wall is there (not two open levels), and the neighbour's face of it is not what this level's would be.
    /// A noclip region's rim is its own, whatever the edge says, so the fields line it; a region never lines its rim.
    /// </summary>
    private bool LinesWallTo(int level, int mx, int mz, int nx, int nz)
    {
        if (Version < 9) return false;
        int other = LevelAt(nx, nz);
        if (other == level || IsOpenSky(level) && IsOpenSky(other) || IsNoclipRegion(level)) return false;
        if (IsNoclipRegion(other)) return true;
        bool hallsHere = level == 1 && IsLevel1Corridors(mx, mz), hallsThere = other == 1 && IsLevel1Corridors(nx, nz);
        return BoundaryPattern(level, other, mx, mz, hallsHere) != BoundaryPattern(other, level, nx, nz, hallsThere);
    }

    /// <summary>
    /// For the levels whose walls follow a plan (0, 2 and 6): whether the hallway along the wall to the next level runs
    /// a tile further in on the cell's east side and on its south side, because the cell lines the wall there (or the
    /// cell beyond the corner does, and the hallway turns the corner with it). Always false before layout version 9.
    /// </summary>
    private (bool East, bool South) LiningWidens(int level, int mx, int mz)
    {
        if (Version < 9) return (false, false);
        bool Lines(int dx, int dz) => LevelAt(mx + dx, mz + dz) != level && LinesWallTo(level, mx, mz, mx + dx, mz + dz);
        bool corner = Lines(1, 1);
        return (Lines(1, 0) || Lines(1, -1) || corner, Lines(0, 1) || Lines(-1, 1) || corner);
    }

    /// <summary>
    /// Lines the walls this cell's east and south neighbours own between their level and this one, with this level's
    /// own wall, a tile in from theirs (see the class summary). The gaps of a gate are left open, so the way through is
    /// a passage two deep; a tile is only lined if the floor round it stays joined up without it, and never where a
    /// stair, a lift, a way into somewhere else or part of something bigger than a tile stands.
    /// </summary>
    private void LineLevelWalls(Builder b, int mx, int mz, Edge west, Edge north, Edge east, Edge south)
    {
        if (Version < 9) return;
        int level = b.Level;
        bool lineEast = LinesWallTo(level, mx, mz, mx + 1, mz), lineSouth = LinesWallTo(level, mx, mz, mx, mz + 1);
        if (!lineEast && !lineSouth) return;
        // Where this cell's own west or north edge is open at the corner, the tile there leads into the next cell: it is
        // only lined when that cell lines its own tile beside it too
        bool northLinesEast = LevelAt(mx, mz - 1) == level && LinesWallTo(level, mx, mz - 1, mx + 1, mz - 1);
        bool westLinesSouth = LevelAt(mx - 1, mz) == level && LinesWallTo(level, mx - 1, mz, mx - 1, mz + 1);
        bool southLinesEast = LevelAt(mx, mz + 1) == level && LinesWallTo(level, mx, mz + 1, mx + 1, mz + 1);
        bool eastLinesSouth = LevelAt(mx + 1, mz) == level && LinesWallTo(level, mx + 1, mz, mx + 1, mz + 1);
        bool halls = level == 1 && IsLevel1Corridors(mx, mz);

        void Line(int x, int z, int nx, int nz, bool alongX)
        {
            ref Tile t = ref b.At(x, z);
            if (!CanLine(b, x, z, alongX)) return;
            // Into the next cell over this cell's own edge, or out of it past the neighbours'
            // (or the way on into it stays open a tile along, beside the lining)
            if (IsWalkable(t))
            {
                const int last = MacroSize - 1;
                if (z == 0 && !(x == last && northLinesEast) && north.Tiles[x - 1] == EdgeTile.Wall) return;
                if (x == 0 && !(z == last && westLinesSouth) && west.Tiles[z - 1] == EdgeTile.Wall) return;
                if (z == last && x > 0 && south.Tiles[x] != EdgeTile.Wall && !(x == last && southLinesEast && lineEast) && south.Tiles[x - 1] == EdgeTile.Wall) return;
                if (x == last && z > 0 && east.Tiles[z] != EdgeTile.Wall && !(z == last && eastLinesSouth && lineSouth) && east.Tiles[z - 1] == EdgeTile.Wall) return;
                if (!StaysJoined(b, x, z)) return;
            }
            WallPattern pattern = BoundaryPattern(level, LevelAt(nx, nz), mx, mz, halls);
            t = new Tile
            {
                Kind = TileKind.Wall, Pattern = pattern, Base = BaseFor(pattern), Tall = true, Floor = t.Floor,
                Grand = t.Grand, Low = t.Low, Level = (byte)level,
                Variant = LiningVariant(level, pattern, mx * MacroSize + x, mz * MacroSize + z),
            };
            // What hung on the walls either side of it, along the lining, facing this tile, would face the lining now
            foreach (int k in new[] { -1, 1 })
            {
                int ax = alongX ? x + k : x, az = alongX ? z : z + k;
                if (ax < 0 || az < 0 || ax >= MacroSize || az >= MacroSize) continue;
                ref Tile n = ref b.At(ax, az);
                if (n.Kind == TileKind.Wall && n.Variant >= Decor.First && FacingStep(n.Pier) == (x - ax, z - az)) n.Variant = 0;
            }
        }

        // Down the east side, from the corner post to the last tile, wherever the neighbour's wall is solid; then the
        // same along the south
        if (lineEast)
            for (int i = 0; i < MacroSize; i++)
                if (i == 0 || east.Tiles[i] == EdgeTile.Wall) Line(MacroSize - 1, i, mx + 1, mz, alongX: false);
        if (lineSouth)
            for (int i = 0; i < MacroSize; i++)
                if (i == 0 || south.Tiles[i] == EdgeTile.Wall) Line(i, MacroSize - 1, mx, mz + 1, alongX: true);

        // The tile inside each gap of a gate is kept clear, as the doorway's own neighbours are
        void ClearInside(int x, int z)
        {
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Stair != 0 || t.Variant is Props.Car or Props.CarPart or Props.Bed or Props.HospitalBed
                or Props.WheelStop or Props.WindowGlow) return;
            if (PartsOf(t.Variant) != (1, 1)) return;
            t.Variant = 0;
            t.Stack = 0;
        }
        for (int i = 1; i < MacroSize; i++)
        {
            if (lineEast && east.Tiles[i] == EdgeTile.Doorway && IsWalkable(b.At(MacroSize - 1, i))) ClearInside(MacroSize - 2, i);
            if (lineSouth && south.Tiles[i] == EdgeTile.Doorway && IsWalkable(b.At(i, MacroSize - 1))) ClearInside(i, MacroSize - 2);
        }
    }

    /// <summary>
    /// Whether a tile may become a wall lining the next level's: floor, and what stands on it (this level's own walls,
    /// doors and bars are left as they are, their faces being its own already), but never a stair, a lift, a pit, water,
    /// a way into somewhere else, or part of something bigger than a tile (a car, a tent; a prop beside another of its
    /// kind might be one).
    /// </summary>
    private static bool CanLine(Builder b, int x, int z, bool alongX)
    {
        Tile t = b.At(x, z);
        if (t.Tall || t.Kind != TileKind.Floor || t.Stair != 0 || t.Under != 0) return false;
        if (t.Variant is Props.Car or Props.CarPart || PartsOf(t.Variant) != (1, 1)) return false;
        foreach ((int dx, int dz) in Steps)
        {
            int nx = x + dx, nz = z + dz;
            if (nx < 0 || nz < 0 || nx >= MacroSize || nz >= MacroSize) continue;
            Tile n = b.At(nx, nz);
            if (t.Variant != 0 && n.Kind == TileKind.Floor && (n.Variant == t.Variant || n.Variant == Props.CarPart)) return false;
            // The way in front of a door, a lift or an opening, or of whatever hangs on a wall facing it, stays clear
            if (n.Kind is TileKind.Door or TileKind.Doorway or TileKind.ArchDoor or TileKind.ArchWindow) return false;
            // (a fitting on a wall along the lining, beside it, comes down, unless it is a sign or a button someone needs)
            if (n.Kind == TileKind.Wall && n.Variant >= Decor.First && FacingStep(n.Pier) == (-dx, -dz)
                && ((alongX ? dz != 0 : dx != 0) || IsNeededFitting(n.Variant))) return false;
        }
        return true;
    }

    /// <summary>
    /// Whether the open tiles beside a tile stay joined up within the cell when it is walled: at once if the ring of
    /// eight round it has one run of open tiles (or none), else by a search round it.
    /// </summary>
    private static bool StaysJoined(Builder b, int x, int z)
    {
        bool Open(int ox, int oz) => ox >= 0 && oz >= 0 && ox < MacroSize && oz < MacroSize && (ox != x || oz != z) && IsWalkable(b.At(ox, oz));
        var beside = new List<int>();
        foreach ((int dx, int dz) in Steps)
            if (Open(x + dx, z + dz)) beside.Add(TileIndex(x + dx, z + dz));
        if (beside.Count <= 1) return true;
        if (SafeToBlock(Open, x, z)) return true;
        var reached = new bool[MacroSize * MacroSize];
        var queue = new Queue<int>();
        reached[beside[0]] = true;
        queue.Enqueue(beside[0]);
        while (queue.Count > 0)
        {
            int index = queue.Dequeue();
            int cx = index % MacroSize, cz = index / MacroSize;
            foreach ((int dx, int dz) in Steps)
            {
                if (!Open(cx + dx, cz + dz)) continue;
                int next = TileIndex(cx + dx, cz + dz);
                if (reached[next]) continue;
                reached[next] = true;
                queue.Enqueue(next);
            }
        }
        foreach (int index in beside)
            if (!reached[index]) return false;
        return true;
    }

    /// <summary>Wall fittings that tell or do something (signs, lift buttons, the hotel's key rack), never taken down.</summary>
    private static bool IsNeededFitting(ushort decor) => decor is Decor.LevelSign or Decor.StairSign or Decor.RoomSign or Decor.CallButton
        or Decor.OfficeStairSign or Decor.CallPlate or Decor.KeyRack or Decor.MegExit or Decor.MegCross or Decor.EvacMap || decor >= Decor.SignBurger;

    private static (int Dx, int Dz) FacingStep(ArchPier pier) => pier switch
    {
        ArchPier.North => (0, -1),
        ArchPier.South => (0, 1),
        ArchPier.East => (1, 0),
        _ => (-1, 0),
    };

    /// <summary>What a lining wall carries: Level 4's windows are papered over, behind blinds or clear, as its own are.</summary>
    private ushort LiningVariant(int level, WallPattern pattern, int gx, int gz)
    {
        if (level != 4 || pattern != WallPattern.OfficeWindow) return 0;
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL4Detail));
        return WindowVariant(r);
    }

    /// <summary>
    /// The way through a gate wears a little of the next level in, from layout version 9: on this side, the doorway (if
    /// this cell owns it) or the gap in the lining, and the tile before it. Level 0's carpet is worn through to the
    /// concrete before Level 1, and Level 4's carpet is the hotel's red before Level 5. Everywhere else a level is its
    /// own to the wall.
    /// </summary>
    private void WearThresholds(Builder b, int mx, int mz, Edge west, Edge north, Edge east, Edge south)
    {
        if (Version < 9) return;
        int level = b.Level, toward;
        FloorKind floor;
        if (level == 0) { toward = 1; floor = FloorKind.Concrete; }
        else if (level == 4) { toward = 5; floor = FloorKind.HotelCarpet; }
        else return;

        void Wear(int x, int z)
        {
            ref Tile t = ref b.At(x, z);
            if (t.Kind is TileKind.Floor or TileKind.Doorway && IsWalkable(t) && t.Under == 0 && t.Stair == 0) t.Floor = floor;
        }
        void Way(Edge edge, int nx, int nz, (int X, int Z) first, (int X, int Z) along, (int X, int Z) inward)
        {
            if (LevelAt(nx, nz) != toward || !IsGated(level, toward)) return;
            for (int i = 1; i < MacroSize; i++)
            {
                if (edge.Tiles[i] != EdgeTile.Doorway) continue;
                int x = first.X + along.X * i, z = first.Z + along.Z * i;
                if (!IsWalkable(b.At(x, z))) continue;
                Wear(x, z);
                Wear(x + inward.X, z + inward.Z);
            }
        }
        // This cell's own edges: the doorway is its tile; the neighbours' edges: the gap in the lining is
        Way(west, mx - 1, mz, (0, 0), (0, 1), (1, 0));
        Way(north, mx, mz - 1, (0, 0), (1, 0), (0, 1));
        Way(east, mx + 1, mz, (MacroSize - 1, 0), (0, 1), (-1, 0));
        Way(south, mx, mz + 1, (0, MacroSize - 1), (1, 0), (0, -1));
    }
}
