using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// The Basement (experimental, unnumbered): kept as level 22 (<see cref="Basement"/>) and shown as "Basement". A round
/// noclip region far out to the south-south-west: the endless house basement of the Fandom page, whose lower parts are the
/// flooded cellar of the Wikidot account. The design is in docs/design/experimental-levels/basement-plan.md (lore:
/// lore/basement-brief.md). No thresholds in or out (the cheats menu or <c>/backrooms goto basement</c> only). This file is
/// the level's own.
///
/// <para><b>Zones</b>, one per cell (<see cref="BasementCellZone"/>, a smooth noise over the cells): <b>the Cellar</b>
/// (dry, about half), rooms split from the cell as a BSP tree, each wall with a wooden door in it (now and then two, one
/// of them swollen shut), its walls cinder block or old pine panelling. Finished rooms have dusty carpet and bare joists
/// overhead and a house's cast-offs; utility rooms bare concrete with a boiler, crates, a shelf; store rooms boxes and
/// furniture. A bare bulb in about one room in two. In some cells, a room someone fell into (a crack in the ceiling
/// twenty blocks high, the yellow light of the Lobby at its top, the rubble under it: where people arrive), an
/// Escherian stairwell (a brick tower whose stairs, up or down, come round to the same floor), a room of the dead.
/// <b>The Flood</b>, a maze of passages three wide on an eight-block grid of nodes (a spanning tree over the cell's
/// sixteen nodes, a few links more for loops), its floor two blocks lower under two blocks of still black water, pipes
/// along its ceiling, a drowned body in some of its dead ends; and <b>the Dry Patch</b>, about one wet cell in five,
/// whose four middle nodes are one raised room 14 by 14 at the Cellar's height, two steps up into it from every passage
/// that reaches it, with now and then a dead cage elevator in its wall.</para>
///
/// <para><b>Joins.</b> Two Cellar cells meet through two gaps two wide; two wet cells through two of the four node lines,
/// three wide; a Cellar and a wet cell through one node line, where a stair of two steps goes down into the water on the
/// wet side (<see cref="BasementGaps"/>; both cells and the edge work it out alike).</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> the <see cref="BasementZone"/> (on walls too). The Flood's tiles are
/// <see cref="TileKind.Water"/> (walkable, never an arrival); its steps have <see cref="Tile.Height"/> 2 (the upper, a stair
/// block level with the dry floor) or 1 (the lower), climbing toward <see cref="Tile.Pier"/>. Lamps are
/// <see cref="Tile.Ceiling"/> kinds (82-86), hanging in the top block of air; pipes <see cref="Tile.Pipe"/> 100-103.
/// Doors are <see cref="TileKind.Doorway"/> tiles with <see cref="Props.BasementDoor"/>. An Escherian stairwell's tiles have
/// <see cref="Tile.Detail"/> <see cref="BasementTower"/>; its steps <see cref="Props.BasementEscher"/> with their place round
/// the core in <see cref="Tile.Stair"/> (1 the landing by the door, 2-8 the steps, each one higher). The crack: its 3 by 3
/// <see cref="CeilingKind.BasementOpen"/> (the middle one <see cref="Tile.Detail"/> <see cref="BasementCrackMiddle"/>), the
/// ring round it <see cref="Overheads.BasementCrackRim"/>, the ring round that <see cref="Overheads.BasementCrackWall"/>.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2200-0x22BF are this level's (0x22C0-0x22FF its thresholds').</summary>
    private const ulong SaltBasementShape = 0x2201;
    private const ulong SaltBasementZone = 0x2200, SaltBasementPatch = 0x2202, SaltBasementGap = 0x2203, SaltBasementMaze = 0x2205,
        SaltBasementRooms = 0x2206, SaltBasementFurnish = 0x2207, SaltBasementSpecial = 0x2208, SaltBasementDead = 0x2209,
        SaltBasementFinds = 0x220A, SaltBasementDoor = 0x220B, SaltBasementWear = 0x220C, SaltBasementOverhead = 0x2210; // (Wear: 0x220C-0x220E, Fbm's three)

    /// <summary>What part of the Basement a tile is in (kept in <see cref="Tile.Zone"/>).</summary>
    public enum BasementZone : byte { None, Cellar, Flood, Patch }

    /// <summary>The Flood's node grid: a node every eight blocks, the first four in from the cell's west (north) line.</summary>
    public const int BasementPitch = 8, BasementNode0 = 4;

    /// <summary>The Dry Patch's room: its walls on lines 8 and 23 of the cell, its floor between.</summary>
    public const int BasementPatchLo = 8, BasementPatchHi = 23;

    /// <summary><see cref="Tile.Detail"/> on a Cellar tile: part of an Escherian stairwell's tower; the middle of a crack in the ceiling.</summary>
    public const byte BasementTower = 1, BasementCrackMiddle = 2;

    /// <summary>
    /// An Escherian stairwell: one turn of its stairs climbs <see cref="BasementEscherRise"/> blocks over its eight places
    /// round the core, and it repeats from <see cref="BasementEscherLow"/> to <see cref="BasementEscherHigh"/> above the floor.
    /// Stepping onto its landing a turn above or below the door puts you back on the landing by the door
    /// (<see cref="Regions.BasementSystem"/>), so the stairs, up or down, come round to the same floor.
    /// </summary>
    public const int BasementEscherRise = 8, BasementEscherLow = -8, BasementEscherHigh = 23;

    /// <summary>The crack's top: the ceiling of the room above (the Lobby, by its yellow light), this far over the floor.</summary>
    public const int BasementCrackTop = 20;

    /// <summary>Below this zone noise a cell is wet (the Flood, or a Dry Patch in it); tuned for about 55% Cellar.</summary>
    private const double BasementWetBelow = -0.06;

    /// <summary>The share of wet cells that hold a Dry Patch.</summary>
    private const double BasementPatchShare = 0.22;

    /// <summary>The share of Cellar cells with a crack in a ceiling, an Escherian stairwell, a room of the dead.</summary>
    private const double BasementCrackShare = 0.4, BasementEscherShare = 0.18, BasementCharnelShare = 0.18;

    /// <summary>Round 3: the share of Cellar cells whose first split is a hallway two wide right across them, rooms off both sides.</summary>
    private const double BasementHallShare = 0.45;

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees west of south.</summary>
    private double BasementReach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int BasementCentreX => spawnMacroX - (int)Math.Round(BasementReach * Math.Sin(Math.PI / 8));
    private int BasementCentreZ => spawnMacroZ + (int)Math.Round(BasementReach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells.</summary>
    private int BasementRadius => Math.Max(40, spawnMacroX / 50);

    /// <summary>The region's centre and radius, in cells (for the harness).</summary>
    public (int Mx, int Mz, int Radius) BasementRegion => (BasementCentreX, BasementCentreZ, BasementRadius);

    private bool InBasement(double mx, double mz) => InRoundRegion(mx, mz, BasementCentreX, BasementCentreZ, BasementRadius, SaltBasementShape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) BasementArrivalCell(ulong h) => RoundArrivalCell(h, BasementCentreX, BasementCentreZ, BasementRadius);

    /// <summary>
    /// Arriving: as everyone does, by falling through the floor of the level above. On the floor under a crack in the
    /// ceiling (the rubble that came down with you beside you), never in the water.
    /// </summary>
    private static bool IsBasementArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone == (byte)BasementZone.Cellar && t.Ceiling == CeilingKind.BasementOpen;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double BasementArrivalHeight(in Tile t, double stand) => stand;

    // ================= Zones =================

    /// <summary>The zone of one of the level's cells: the Cellar, the Flood, or a Flood cell with a Dry Patch in its middle.</summary>
    public BasementZone BasementCellZone(int mx, int mz)
    {
        if (Fbm(mx / 6.0, mz / 6.0, SaltBasementZone) >= BasementWetBelow) return BasementZone.Cellar;
        return Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltBasementPatch)) < BasementPatchShare ? BasementZone.Patch : BasementZone.Flood;
    }

    /// <summary>The zone at a block position, by arithmetic (the Dry Patch is its room only; the passages round it are the Flood).</summary>
    public BasementZone BasementZoneAt(int x, int z)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        BasementZone zone = BasementCellZone(mx, mz);
        if (zone != BasementZone.Patch) return zone;
        int lx = x - mx * MacroSize, lz = z - mz * MacroSize;
        bool room = lx >= BasementPatchLo && lx <= BasementPatchHi && lz >= BasementPatchLo && lz <= BasementPatchHi;
        return room ? BasementZone.Patch : BasementZone.Flood;
    }

    private static bool BasementWet(BasementZone z) => z is BasementZone.Flood or BasementZone.Patch;

    /// <summary>
    /// The gaps in the wall line on the west (or north) side of cell (mx, mz), between two of the level's cells: the
    /// first index along the line of each (B is -1 when there is one), and how wide they are. Two Cellar cells: two gaps two
    /// wide, anywhere. Two wet cells: two of the four node lines, three wide (the passage's width). A Cellar and a wet cell:
    /// one node line, three wide, with the stair down on the wet side.
    /// </summary>
    private (int A, int B, int Width) BasementGaps(int mx, int mz, bool west)
    {
        int nx = west ? mx - 1 : mx, nz = west ? mz : mz - 1;
        bool dryHere = BasementCellZone(mx, mz) == BasementZone.Cellar, dryThere = BasementCellZone(nx, nz) == BasementZone.Cellar;
        ulong h = Hashing.Hash(seed, mx, mz, SaltBasementGap + (west ? 0UL : 1UL));
        if (dryHere && dryThere) return (3 + (int)(h % 11), 17 + (int)((h >> 12) % 12), 2);
        int i = (int)((h >> 24) % 4), j = (int)((h >> 36) % 3);
        if (j >= i) j++;
        int a = BasementNode0 - 1 + BasementPitch * i, b = BasementNode0 - 1 + BasementPitch * j;
        return dryHere || dryThere ? (a, -1, 3) : (a, b, 3);
    }

    private static bool InGap((int A, int B, int Width) g, int i) => i >= g.A && i < g.A + g.Width || g.B >= 0 && i >= g.B && i < g.B + g.Width;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells, with its gaps (see <see cref="BasementGaps"/>).</summary>
    private Edge BasementEdge(int mx, int mz, bool west)
    {
        var gaps = BasementGaps(mx, mz, west);
        bool wet = BasementWet(BasementCellZone(mx, mz)) && BasementWet(BasementCellZone(west ? mx - 1 : mx, west ? mz : mz - 1));
        var edge = new Edge { Pattern = wet ? WallPattern.BasementFloodWall : WallPattern.BasementCinder };
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = InGap(gaps, i) ? EdgeTile.Open : EdgeTile.Wall;
        return edge;
    }

    /// <summary>One of a cell's four sides: whether the level goes on past it, whether the cell there is dry, and its gaps.</summary>
    private readonly struct BasementSide
    {
        public readonly bool Ours, Dry;
        public readonly (int A, int B, int Width) Gaps;
        public BasementSide(bool ours, bool dry, (int, int, int) gaps) { Ours = ours; Dry = dry; Gaps = gaps; }
    }

    /// <summary>The four sides of a cell: west, north, east, south.</summary>
    private BasementSide[] BasementSides(int mx, int mz)
    {
        var sides = new BasementSide[4];
        (int Nx, int Nz, int Ex, int Ez, bool West)[] at = { (mx - 1, mz, mx, mz, true), (mx, mz - 1, mx, mz, false), (mx + 1, mz, mx + 1, mz, true), (mx, mz + 1, mx, mz + 1, false) };
        for (int s = 0; s < 4; s++)
        {
            var (nx, nz, ex, ez, west) = at[s];
            bool ours = LevelAt(nx, nz) == Basement;
            sides[s] = new BasementSide(ours, ours && BasementCellZone(nx, nz) == BasementZone.Cellar, ours ? BasementGaps(ex, ez, west) : (-1, -1, 0));
        }
        return sides;
    }

    /// <summary>A tile of a side: the tile in this cell at index i along it, and the step inward (toward the cell's middle).</summary>
    private static (int X, int Z, int Dx, int Dz) BasementSideTile(int side, int i) => side switch
    {
        0 => (0, i, 1, 0),
        1 => (i, 0, 0, 1),
        2 => (MacroSize - 1, i, -1, 0),
        _ => (i, MacroSize - 1, 0, -1),
    };

    /// <summary>The way a step inward from a side climbs back out toward it.</summary>
    private static ArchPier BasementOutward(int side) => side switch { 0 => ArchPier.West, 1 => ArchPier.North, 2 => ArchPier.East, _ => ArchPier.South };

    /// <summary>Lays out one of the level's cells: Cellar rooms, or the Flood's maze (with a Dry Patch in some).</summary>
    private void BuildLevelBasement(Builder b, int mx, int mz)
    {
        BasementZone zone = BasementCellZone(mx, mz);
        BasementSide[] sides = BasementSides(mx, mz);
        if (zone == BasementZone.Cellar) BuildBasementCellar(b, mx, mz, sides);
        else BuildBasementFlood(b, mx, mz, sides, zone == BasementZone.Patch);
    }

    // ---- The Cellar ----

    /// <summary>
    /// What a Cellar room is: a finished room of the house (carpet, panelling, cast-offs), a utility room (a boiler, tanks,
    /// gauges), a workshop (a bench, tools, lumber), a laundry (washer and dryer, a sink), a store room (boxes, furniture,
    /// suitcases, aisles of shelving) or a pantry (shelves of jars).
    /// </summary>
    private enum BasementRoomKind : byte { Finished, Utility, Store, Workshop, Laundry, Pantry, Boiler, Rec, RootCellar, Hall }

    private void BuildBasementCellar(Builder b, int mx, int mz, BasementSide[] sides)
    {
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementRooms));
        for (int i = 0; i < b.Tiles.Length; i++)
        {
            ref Tile t = ref b.Tiles[i];
            t.Zone = (byte)BasementZone.Cellar;
            t.Ceiling = CeilingKind.BasementCeiling;
            if (t.Kind != TileKind.Floor) continue;
            t.Floor = FloorKind.BasementFloor;
        }

        // Whether a tile beyond a wall's end is solid: the cell's own west and north lines are its tiles; past the east and
        // south lines, a gap there is open
        bool Solid(int x, int z)
        {
            if (x < 0 || z < 0) return true;
            if (x >= MacroSize) return !(sides[2].Ours && InGap(sides[2].Gaps, z));
            if (z >= MacroSize) return !(sides[3].Ours && InGap(sides[3].Gaps, x));
            return b.At(x, z).Kind == TileKind.Wall;
        }

        // The cell's one room of each special kind (by hash): the crack someone fell through, an Escherian stairwell, a
        // room of the dead. The split keeps a big room for each of the first two; the dead keep to a small one
        var special = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementSpecial));
        (int X0, int Z0, int X1, int Z1) hallRect = (-1, -1, -1, -1);
        bool wantCrack = special.Chance(BasementCrackShare), wantEscher = special.Chance(BasementEscherShare), wantCharnel = special.Chance(BasementCharnelShare);
        bool wantHall = special.Chance(BasementHallShare);
        int keepBig = (wantCrack ? 1 : 0) + (wantEscher ? 1 : 0);
        var rooms = new List<(int X0, int Z0, int X1, int Z1)>();
        var doorRng = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementDoor));
        // Round 3: now and then a hallway two wide right across the cell between unfinished stud walls, the rooms split off
        // both sides of it, each with a door onto it
        if (wantHall && BasementHall(b, ref special, Solid, out var hall, out bool hallNs))
        {
            if (hallNs)
            {
                BasementSplit(b, ref rng, ref doorRng, Solid, 1, 1, hall.X0 - 2, MacroSize - 1, rooms, ref keepBig);
                BasementSplit(b, ref rng, ref doorRng, Solid, hall.X1 + 2, 1, MacroSize - 1, MacroSize - 1, rooms, ref keepBig);
            }
            else
            {
                BasementSplit(b, ref rng, ref doorRng, Solid, 1, 1, MacroSize - 1, hall.Z0 - 2, rooms, ref keepBig);
                BasementSplit(b, ref rng, ref doorRng, Solid, 1, hall.Z1 + 2, MacroSize - 1, MacroSize - 1, rooms, ref keepBig);
            }
            BasementHallDoors(b, ref doorRng, rooms, hall, hallNs);
            hallRect = hall;
        }
        else BasementSplit(b, ref rng, ref doorRng, Solid, 1, 1, MacroSize - 1, MacroSize - 1, rooms, ref keepBig);

        // A landing inside every gap in the cell's sides, so no wall of the rooms ends across one; nothing stands on it
        var keepClear = new bool[MacroSize * MacroSize];
        void Mark(int x, int z)
        {
            if (x >= 0 && z >= 0 && x < MacroSize && z < MacroSize) keepClear[TileIndex(x, z)] = true;
        }
        for (int s = 0; s < 4; s++)
        {
            if (!sides[s].Ours) continue;
            for (int i = 1; i < MacroSize; i++)
            {
                if (!InGap(sides[s].Gaps, i)) continue;
                var (x, z, dx, dz) = BasementSideTile(s, i);
                for (int k = s < 2 ? 1 : 0; k <= (s < 2 ? 2 : 1); k++) BasementClear(ref b.At(x + dx * k, z + dz * k));
                for (int k = 0; k <= 3; k++) Mark(x + dx * k, z + dz * k);
            }
        }

        int crackRoom = -1, escherRoom = -1, charnelRoom = -1;
        for (int k = 0, best = 0; k < rooms.Count; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            int w = x1 - x0 + 1, h = z1 - z0 + 1;
            if (wantCrack && w >= 7 && h >= 7 && w * h > best && BasementMiddleFits(x0, z0, x1, z1, 3)) { crackRoom = k; best = w * h; }
        }
        for (int k = 0; k < rooms.Count && wantEscher; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            if (k != crackRoom && x1 - x0 + 1 >= 9 && z1 - z0 + 1 >= 9) { escherRoom = k; break; }
        }
        for (int k = 0, least = int.MaxValue; k < rooms.Count && wantCharnel; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            int area = (x1 - x0 + 1) * (z1 - z0 + 1);
            if (k != crackRoom && k != escherRoom && area >= 25 && area < least) { charnelRoom = k; least = area; }
        }

        // The hallway is a room of its own (none of the special rooms)
        int hallRoom = -1;
        if (hallRect.X0 >= 0)
        {
            hallRoom = rooms.Count;
            rooms.Add(hallRect);
        }

        // The rooms' floors and ceilings, and what takes their middles (the crack, the stairwell, a pillar)
        var furnish = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementFurnish));
        var kinds = BasementAssignKinds(ref furnish, rooms, crackRoom, escherRoom, charnelRoom, hallRoom);
        var middles = new bool[rooms.Count];
        for (int k = 0; k < rooms.Count; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            int w = x1 - x0 + 1, h = z1 - z0 + 1;
            BasementRoomKind kind = kinds[k];
            FloorKind floor = kind is BasementRoomKind.Finished or BasementRoomKind.Rec
                ? (furnish.Chance(kind == BasementRoomKind.Rec ? 1 : 0.85) ? (furnish.Chance(0.6) ? FloorKind.BasementCarpet : FloorKind.BasementCarpetWorn) : FloorKind.BasementFloor)
                : kind == BasementRoomKind.RootCellar ? FloorKind.BasementEarth : FloorKind.BasementFloor;
            // Real basements leave the joists bare over their workrooms and hallways; a finished room has them now and then
            bool joists = kind == BasementRoomKind.Hall || furnish.Chance(kind is BasementRoomKind.Finished or BasementRoomKind.Rec ? 0.35 : 0.6);
            // Damp comes up through the slab in patches (more in a laundry), and a carpet is worn to another colour in places
            double damp = kind switch
            {
                BasementRoomKind.Laundry => 0.0, BasementRoomKind.Utility or BasementRoomKind.Boiler => 0.15, BasementRoomKind.Finished or BasementRoomKind.Rec => 0.45,
                BasementRoomKind.Hall => 0.2, _ => 0.3,
            };
            for (int z = z0; z <= z1; z++)
                for (int x = x0; x <= x1; x++)
                {
                    ref Tile t = ref b.At(x, z);
                    if (t.Kind != TileKind.Floor) continue;
                    double wear = Fbm((mx * MacroSize + x) / 3.5, (mz * MacroSize + z) / 3.5, SaltBasementWear);
                    t.Floor = floor == FloorKind.BasementFloor && wear > damp ? FloorKind.BasementDamp
                        : floor == FloorKind.BasementCarpet && wear > 0.3 ? FloorKind.BasementCarpetWorn
                        : floor;
                    if (joists) t.Ceiling = CeilingKind.BasementJoists;
                    else if (furnish.Chance(t.Floor == FloorKind.BasementDamp ? 0.3 : 0.06)) t.Ceiling = CeilingKind.BasementStained;
                }
            int cx = x0 + w / 2, cz = z0 + h / 2;
            if (k == crackRoom) { BasementCrack(b, ref furnish, x0, z0, x1, z1, cx, cz); middles[k] = true; }
            else if (k == escherRoom) { BasementTowerAt(b, cx - 2, cz - 2); middles[k] = true; }
            // A squat concrete pillar holding up the middle of a big workroom
            else if (kind is BasementRoomKind.Utility or BasementRoomKind.Workshop or BasementRoomKind.Store && w >= 9 && h >= 9 && furnish.Chance(0.6)
                && b.At(cx, cz).Kind == TileKind.Floor)
            {
                SetWall(ref b.At(cx, cz), WallPattern.BasementPillar, BaseStyle.Plain);
                middles[k] = true;
            }
        }

        // Overhead: a heating duct across the cell, and more often than not a water main along another line, both running
        // on through the walls; in a workroom, pipes along a wall
        var over = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementOverhead));
        BasementOverheadRun(b, ref over, true);
        if (over.Chance(0.65)) BasementOverheadRun(b, ref over, false);
        for (int k = 0; k < rooms.Count; k++)
        {
            if (kinds[k] is not (BasementRoomKind.Utility or BasementRoomKind.Workshop or BasementRoomKind.Laundry or BasementRoomKind.Boiler) || !over.Chance(0.75)) continue;
            var (x0, z0, x1, z1) = rooms[k];
            bool alongX = x1 - x0 >= z1 - z0;
            int line = alongX ? (over.Chance(0.5) ? z0 : z1) : (over.Chance(0.5) ? x0 : x1);
            for (int i = alongX ? x0 : z0; i <= (alongX ? x1 : z1); i++)
            {
                ref Tile t = ref b.At(alongX ? i : line, alongX ? line : i);
                if (t.Kind == TileKind.Floor && t.Pipe == 0 && t.Ceiling != CeilingKind.BasementOpen && t.Detail == 0)
                    t.Pipe = over.Chance(0.06) ? (alongX ? Pipes.BasementLeakWE : Pipes.BasementLeakNS) : alongX ? Pipes.BasementPipeWE : Pipes.BasementPipeNS;
            }
        }

        // The hallway's duct runs the length of it, the bulbs hang down its other side
        if (hallRoom >= 0)
        {
            var (hx0, hz0, hx1, hz1) = rooms[hallRoom];
            bool ns = hx1 - hx0 < hz1 - hz0;
            for (int i = 1; i < MacroSize; i++)
            {
                ref Tile t = ref b.At(ns ? hx0 : i, ns ? i : hz0);
                if (t.Kind == TileKind.Floor && t.Ceiling != CeilingKind.BasementOpen) t.Pipe = ns ? Pipes.BasementDuctNS : Pipes.BasementDuctWE;
            }
        }

        bool Open(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z));
        for (int z = 0; z < MacroSize; z++)
            for (int x = 0; x < MacroSize; x++)
                if (b.At(x, z).Kind == TileKind.Doorway)
                    foreach (var (dx, dz) in Steps) Mark(x + dx, z + dz);
        for (int k = 0; k < rooms.Count; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            int w = x1 - x0 + 1, h = z1 - z0 + 1;
            BasementRoomKind kind = kinds[k];
            if (k == hallRoom)
            {
                BasementHallBulbs(b, ref furnish, x0, z0, x1, z1);
                BasementFurnishHall(b, ref furnish, x0, z0, x1, z1, keepClear, Solid, Open);
                continue;
            }
            // A bare bulb in a little over half the rooms, two in a long one (off to the side of a crack or a stairwell)
            if (furnish.Chance(k == crackRoom ? 0.35 : kind is BasementRoomKind.Finished or BasementRoomKind.Rec or BasementRoomKind.Boiler ? 0.7 : 0.55))
            {
                int cx = x0 + w / 2, cz = z0 + h / 2;
                var at = new List<(int, int)>();
                if (middles[k] && k != crackRoom && k != escherRoom) at.Add((cx + 1, cz));
                else if (middles[k]) at.Add((x0 + 1, z0 + 1));
                else if (w >= 10 && w >= h) { at.Add((x0 + w / 4, cz)); at.Add((x1 - w / 4, cz)); }
                else if (h >= 10) { at.Add((cx, z0 + h / 4)); at.Add((cx, z1 - h / 4)); }
                else at.Add((cx, cz));
                foreach (var (lx, lz) in at) BasementBulb(b, ref furnish, lx, lz);
            }
            if (k == charnelRoom) BasementCharnel(b, ref furnish, mx, mz, x0, z0, x1, z1, Solid, Open);
            else BasementFurnishRoom(b, ref furnish, kind, x0, z0, x1, z1, middles[k], keepClear, Solid, Open);
            // Wires that serve no purpose, hanging from the ceiling here and there
            if (furnish.Chance(0.35))
            {
                int x = furnish.Range(x0, x1), z = furnish.Range(z0, z1);
                ref Tile t = ref b.At(x, z);
                if (t.Kind == TileKind.Floor && t.Pipe == 0 && t.Ceiling is CeilingKind.BasementCeiling or CeilingKind.BasementStained or CeilingKind.BasementJoists && t.Overhead == 0)
                    t.Overhead = Overheads.BasementWire;
            }
        }
        BasementFinds(b, mx, mz, rooms, Solid, Open);
        BasementWallSigns(b, ref furnish, rooms, kinds, sides, Solid);
        BasementUnseal(b, sides);
    }

    /// <summary>
    /// The things round the walls are put down one at a time with only their eight neighbours in view, so now and then two
    /// of them close a corner off between them, and a small room's only door can be one swollen shut. From the gaps in the
    /// cell's sides, walk the rooms (four ways, as people do, through doors that open), and take away anything standing
    /// beside a tile that was not reached, and unstick any jammed door beside one, until every tile is reached.
    /// </summary>
    private static void BasementUnseal(Builder b, BasementSide[] sides)
    {
        // (Round 3: from the ways out of the cell only, the gaps in its west and north lines and the tiles inside the gaps of
        // its east and south sides; a tile merely on the cell's edge may be a corner closed off by furniture)
        bool Way(int x, int z) => x == 0 || z == 0
            || x == MacroSize - 1 && sides[2].Ours && InGap(sides[2].Gaps, z)
            || z == MacroSize - 1 && sides[3].Ours && InGap(sides[3].Gaps, x);
        bool Walk(in Tile t) => IsWalkable(t) && !BasementDoorJammed(t);
        for (int pass = 0; pass < 8; pass++)
        {
            var reached = new bool[MacroSize * MacroSize];
            var queue = new Queue<int>();
            for (int i = 0; i < reached.Length; i++)
            {
                int x = i % MacroSize, z = i / MacroSize;
                if (Way(x, z) && Walk(b.Tiles[i])) { reached[i] = true; queue.Enqueue(i); }
            }
            if (queue.Count == 0) return;
            while (queue.Count > 0)
            {
                int i = queue.Dequeue(), x = i % MacroSize, z = i / MacroSize;
                foreach (var (dx, dz) in Steps)
                {
                    int nx = x + dx, nz = z + dz;
                    if (nx < 0 || nz < 0 || nx >= MacroSize || nz >= MacroSize) continue;
                    int j = TileIndex(nx, nz);
                    if (reached[j] || !Walk(b.Tiles[j])) continue;
                    reached[j] = true;
                    queue.Enqueue(j);
                }
            }
            bool changed = false;
            for (int i = 0; i < reached.Length; i++)
            {
                if (reached[i] || b.Tiles[i].Kind != TileKind.Floor || !Walk(b.Tiles[i])) continue;
                int x = i % MacroSize, z = i / MacroSize;
                foreach (var (dx, dz) in Steps)
                {
                    int nx = x + dx, nz = z + dz;
                    if (nx < 0 || nz < 0 || nx >= MacroSize || nz >= MacroSize) continue;
                    ref Tile t = ref b.At(nx, nz);
                    if (BasementDoorJammed(t))
                    {
                        t.Stack = (byte)(t.Stack & ~3);
                        changed = true;
                    }
                    if (t.Kind != TileKind.Floor || Walk(t) || t.Detail != 0) continue;
                    // (a thing two tiles long goes whole)
                    if (t.Variant is Props.BasementBench or Props.BasementPoolTable or Props.LongSofa or Props.Laundry)
                        foreach (var (ex, ez) in Steps)
                        {
                            int px = nx + ex, pz = nz + ez;
                            if (px < 0 || pz < 0 || px >= MacroSize || pz >= MacroSize) continue;
                            ref Tile pair = ref b.At(px, pz);
                            if (pair.Variant == t.Variant && pair.Variant is not Props.Laundry) { pair.Variant = 0; pair.Stack = 0; if (pair.Overhead == Overheads.BasementPoolLamp) pair.Overhead = 0; }
                        }
                    if (t.Overhead == Overheads.BasementPoolLamp) t.Overhead = 0;
                    t.Variant = 0;
                    t.Stack = 0;
                    t.SupplyBox = false;
                    changed = true;
                }
            }
            if (!changed) return;
        }
    }

    /// <summary>A room's kind, by its size: small rooms are laundries, pantries and store rooms.</summary>
    private static BasementRoomKind BasementPickKind(ref Rng rng, int w, int h)
    {
        double r = rng.NextDouble();
        if (w * h < 30)
            return r < 0.32 ? BasementRoomKind.Store : r < 0.6 ? BasementRoomKind.Laundry : r < 0.85 ? BasementRoomKind.Pantry : BasementRoomKind.Utility;
        return r < 0.36 ? BasementRoomKind.Finished : r < 0.52 ? BasementRoomKind.Utility : r < 0.66 ? BasementRoomKind.Workshop
            : r < 0.84 ? BasementRoomKind.Store : r < 0.93 ? BasementRoomKind.Laundry : BasementRoomKind.Pantry;
    }

    /// <summary>A bare bulb (lit, flickering or dead), beside whatever already hangs from the ceiling there.</summary>
    private static void BasementBulb(Builder b, ref Rng rng, int x, int z)
    {
        foreach (var (dx, dz) in new[] { (0, 0), (0, 1), (0, -1), (1, 0), (-1, 0) })
        {
            int lx = x + dx, lz = z + dz;
            if (lx < 1 || lz < 1 || lx >= MacroSize || lz >= MacroSize) continue;
            ref Tile t = ref b.At(lx, lz);
            if (t.Kind != TileKind.Floor || t.Pipe != 0 || t.Detail != 0 || t.Ceiling == CeilingKind.BasementOpen) continue;
            double r = rng.NextDouble();
            t.Ceiling = r < 0.2 ? CeilingKind.BasementBulbOff : r < 0.48 ? CeilingKind.BasementBulbFlicker : CeilingKind.BasementBulbOn;
            return;
        }
    }

    /// <summary>A heating duct (or a water main) straight across the cell under the ceiling, through the walls it meets.</summary>
    private static void BasementOverheadRun(Builder b, ref Rng rng, bool duct)
    {
        bool alongX = rng.Chance(0.5);
        int line = rng.Range(3, MacroSize - 4), leakAt = rng.Chance(0.4) ? rng.Range(3, MacroSize - 4) : -1;
        for (int i = 0; i < MacroSize; i++)
        {
            ref Tile t = ref b.At(alongX ? i : line, alongX ? line : i);
            if (t.Kind != TileKind.Floor || t.Ceiling == CeilingKind.BasementOpen || t.Detail != 0 || t.Pipe != 0) continue;
            t.Pipe = duct ? (alongX ? Pipes.BasementDuctWE : Pipes.BasementDuctNS)
                : i == leakAt ? (alongX ? Pipes.BasementLeakWE : Pipes.BasementLeakNS) : alongX ? Pipes.BasementPipeWE : Pipes.BasementPipeNS;
            // (Round 3: the floor under a leak is wet, round it damp)
            if (!duct && i == leakAt)
                for (int k = -1; k <= 1; k++)
                {
                    int lx = alongX ? i + k : line, lz = alongX ? line : i + k;
                    if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
                    ref Tile u = ref b.At(lx, lz);
                    if (u.Kind == TileKind.Floor && u.Floor == FloorKind.BasementFloor) u.Floor = FloorKind.BasementDamp;
                }
        }
    }

    /// <summary>Whether a room's middle has <paramref name="reach"/> tiles of it all round, inside the cell.</summary>
    private static bool BasementMiddleFits(int x0, int z0, int x1, int z1, int reach)
    {
        int cx = x0 + (x1 - x0 + 1) / 2, cz = z0 + (z1 - z0 + 1) / 2;
        return cx - reach >= 0 && cz - reach >= 0 && cx + reach < MacroSize && cz + reach < MacroSize;
    }

    /// <summary>
    /// The crack someone fell through: the middle three by three of the room open to the top of the level (the room above
    /// lit, its torn floor round the edge), the rubble that came down under it, a rope's frayed end high up, and now and
    /// then a ladder somebody brought, far too short.
    /// </summary>
    private static void BasementCrack(Builder b, ref Rng rng, int x0, int z0, int x1, int z1, int cx, int cz)
    {
        for (int dz = -3; dz <= 3; dz++)
            for (int dx = -3; dx <= 3; dx++)
            {
                ref Tile t = ref b.At(cx + dx, cz + dz);
                int d = Math.Max(Math.Abs(dx), Math.Abs(dz));
                if (d <= 1)
                {
                    t.Ceiling = CeilingKind.BasementOpen;
                    t.Overhead = 0;
                }
                else t.Overhead = d == 2 ? Overheads.BasementCrackRim : Overheads.BasementCrackWall;
            }
        ref Tile middle = ref b.At(cx, cz);
        middle.Detail = BasementCrackMiddle;
        if (middle.Kind == TileKind.Floor)
        {
            middle.Variant = Props.BasementDebris;
            middle.Stack = (byte)rng.Range(0, 1);
            middle.Pier = (ArchPier)rng.Range(0, 3);
        }
        // A second heap where it bounced
        var (ox, oz) = Steps[rng.Range(0, 3)];
        ref Tile heap = ref b.At(cx + ox, cz + oz);
        if (heap.Kind == TileKind.Floor && rng.Chance(0.6))
        {
            heap.Variant = Props.BasementDebris;
            heap.Stack = (byte)rng.Range(0, 1);
            heap.Pier = (ArchPier)rng.Range(0, 3);
        }
        var (rx, rz) = Steps[rng.Range(0, 3)];
        b.At(cx + rx, cz + rz).Overhead = Overheads.BasementRope;
        // (Round 3) a broken joist that came down with the floor, leaning in the rubble
        var (jx, jz) = Steps[rng.Range(0, 3)];
        ref Tile joist = ref b.At(cx + jx, cz + jz);
        if (joist.Kind == TileKind.Floor && joist.Variant == 0 && joist.Stack == 0)
        {
            joist.Variant = Props.BasementFallen;
            joist.Pier = (ArchPier)rng.Range(0, 3);
        }
        // The ladder: against the room's wall, in the corner nearest the crack's north-west
        if (!rng.Chance(0.45)) return;
        foreach (var (x, z, away) in new[] { (x0, cz, ArchPier.East), (x1, cz, ArchPier.West), (cx, z0, ArchPier.South), (cx, z1, ArchPier.North) })
        {
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0) continue;
            t.Variant = Props.BasementLadder;
            t.Pier = away;
            break;
        }
    }

    /// <summary>
    /// An Escherian stairwell: a brick tower five by five at (x, z), its door in the middle of its north wall; inside, the
    /// stairs climb round a brick core, a block a step, eight to a turn (see <see cref="BasementEscherRise"/>).
    /// </summary>
    private static void BasementTowerAt(Builder b, int x, int z)
    {
        for (int dz = 0; dz < 5; dz++)
            for (int dx = 0; dx < 5; dx++)
            {
                ref Tile t = ref b.At(x + dx, z + dz);
                bool ring = dx == 0 || dz == 0 || dx == 4 || dz == 4, core = dx == 2 && dz == 2;
                t.Detail = BasementTower;
                t.Overhead = 0;
                t.Variant = 0;
                t.Stack = 0;
                t.Ceiling = CeilingKind.BasementCeiling;
                if (ring || core) SetWall(ref t, WallPattern.BasementBrick, BaseStyle.Plain);
            }
        // The door, shut, in the north wall; the steps round the core clockwise from the landing behind it
        ref Tile door = ref b.At(x + 2, z);
        door.Kind = TileKind.Doorway;
        door.Variant = Props.BasementDoor;
        door.Stack = 0;
        door.Pier = ArchPier.North;
        door.Floor = FloorKind.BasementFloor;
        (int Dx, int Dz)[] round = { (2, 1), (3, 1), (3, 2), (3, 3), (2, 3), (1, 3), (1, 2), (1, 1) };
        for (int i = 0; i < round.Length; i++)
        {
            var (px, pz) = round[(i + 7) % 8];
            var (qx, qz) = round[i];
            ref Tile t = ref b.At(x + qx, z + qz);
            t.Kind = TileKind.Floor;
            t.Floor = FloorKind.BasementFloor;
            t.Variant = Props.BasementEscher;
            t.Stair = (byte)(i + 1);
            // Climbing from the place before toward this one
            t.Pier = qx > px ? ArchPier.East : qx < px ? ArchPier.West : qz > pz ? ArchPier.South : ArchPier.North;
        }
    }

    /// <summary>A room of the dead (Fandom: "a large amount of human corpses"): bones heaped against its walls, bodies on its floor.</summary>
    private void BasementCharnel(Builder b, ref Rng rng, int mx, int mz, int x0, int z0, int x1, int z1, Func<int, int, bool> solid, Func<int, int, bool> open)
    {
        int bodies = rng.Range(2, 4), heaps = rng.Range(3, 5);
        for (int tries = 0; tries < 40 && (bodies > 0 || heaps > 0); tries++)
        {
            int x = rng.Range(x0, x1), z = rng.Range(z0, z1);
            if (x < 1 || z < 1 || x > MacroSize - 2 || z > MacroSize - 2) continue;
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0 || t.Overhead != 0) continue;
            ArchPier? away = solid(x - 1, z) ? ArchPier.East : solid(x + 1, z) ? ArchPier.West : solid(x, z - 1) ? ArchPier.South : solid(x, z + 1) ? ArchPier.North : null;
            if (heaps > 0 && away != null && SafeToBlock(open, x, z))
            {
                double r = rng.NextDouble();
                t.Variant = r < 0.5 ? Props.BonePile : r < 0.8 ? Props.Ribcage : Props.JawSkeleton;
                t.Pier = away.Value;
                heaps--;
            }
            else if (bodies > 0 && away == null)
            {
                t.Variant = Props.BasementBody;
                t.Stack = 0;
                t.Pier = (ArchPier)rng.Range(0, 3);
                bodies--;
            }
        }
    }

    /// <summary>
    /// Things round a room's walls by its kind, never where they would cut a way off, in front of a door or on a landing
    /// inside a gap in the cell's sides; and in the middle of a big room, now and then something more: a store room's aisles
    /// of shelving, a sitting room round a coffee table, a workshop's pallet of lumber.
    /// </summary>
    private static void BasementFurnishRoom(Builder b, ref Rng rng, BasementRoomKind kind, int x0, int z0, int x1, int z1, bool middleTaken,
        bool[] keepClear, Func<int, int, bool> solid, Func<int, int, bool> open)
    {
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        bool Free(int x, int z)
        {
            if (x < 1 || z < 1 || x >= MacroSize || z >= MacroSize || keepClear[TileIndex(x, z)]) return false;
            ref Tile t = ref b.At(x, z);
            return t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox && t.Detail == 0 && t.Ceiling != CeilingKind.BasementOpen
                && t.Overhead is 0 or Overheads.BasementWire;
        }
        // Round 3: what the room is for, as things of several blocks, before the odds and ends round its walls
        bool middleUsed = BasementSetPieces(b, ref rng, kind, x0, z0, x1, z1, middleTaken, keepClear, solid, open);
        middleTaken |= middleUsed;

        // Aisles of shelving down a big store room or pantry, with a way round both ends
        if (!middleTaken && kind is BasementRoomKind.Store or BasementRoomKind.Pantry && w >= 7 && h >= 7 && rng.Chance(0.6))
        {
            bool alongX = w >= h;
            int across0 = alongX ? z0 : x0, across1 = alongX ? z1 : x1, from = (alongX ? x0 : z0) + 2, to = (alongX ? x1 : z1) - 2;
            for (int row = across0 + 2; row <= across1 - 2; row += 3)
                for (int i = from; i <= to; i++)
                {
                    int x = alongX ? i : row, z = alongX ? row : i;
                    if (!Free(x, z) || !SafeToBlock(open, x, z)) continue;
                    ref Tile t = ref b.At(x, z);
                    // (Round 3: steel shelving two high, loaded, down most of a store room's aisles)
                    double r = rng.NextDouble();
                    t.Variant = kind == BasementRoomKind.Pantry ? (r < 0.6 ? Props.PantryShelf : Props.BasementShelving) : r < 0.12 ? Props.CardboardBoxes : r < 0.3 ? Props.BasementShelf : Props.BasementShelving;
                    if (t.Variant == Props.BasementShelving) t.Stack = (byte)(kind == BasementRoomKind.Pantry ? 1 : rng.Range(0, 3));
                    bool even = (row - across0) / 3 % 2 == 0;
                    t.Pier = alongX ? (even ? ArchPier.South : ArchPier.North) : (even ? ArchPier.East : ArchPier.West);
                }
        }
        // A sitting room: a coffee table in the middle, a chair or two drawn up to it
        else if (!middleTaken && kind == BasementRoomKind.Finished && w >= 6 && h >= 6 && rng.Chance(0.7))
        {
            int cx = x0 + w / 2, cz = z0 + h / 2;
            if (Free(cx, cz) && SafeToBlock(open, cx, cz))
            {
                ref Tile table = ref b.At(cx, cz);
                table.Variant = Props.CoffeeTable;
                table.Pier = ArchPier.North;
                // (Round 3: a braided rug under it, now and then)
                if (rng.Chance(0.6))
                    for (int dz = -1; dz <= 1; dz++)
                        for (int dx = -1; dx <= 1; dx++)
                            if (b.At(cx + dx, cz + dz).Kind == TileKind.Floor) b.At(cx + dx, cz + dz).Floor = FloorKind.BasementRug;
                foreach (var (dx, dz) in Steps)
                {
                    if (!rng.Chance(0.45) || !Free(cx + dx, cz + dz) || !SafeToBlock(open, cx + dx, cz + dz)) continue;
                    ref Tile chair = ref b.At(cx + dx, cz + dz);
                    chair.Variant = rng.Chance(0.6) ? Props.HotelChair : Props.FoldingChair;
                    // (facing the table)
                    chair.Pier = dx > 0 ? ArchPier.West : dx < 0 ? ArchPier.East : dz > 0 ? ArchPier.North : ArchPier.South;
                }
            }
        }
        // A workshop's pallet of lumber, or a folding table with tools on it
        else if (!middleTaken && kind == BasementRoomKind.Workshop && w >= 6 && h >= 6)
        {
            int cx = x0 + w / 2, cz = z0 + h / 2;
            if (Free(cx, cz) && SafeToBlock(open, cx, cz))
            {
                b.At(cx, cz).Variant = rng.Chance(0.5) ? Props.Pallet : Props.FoldingTable;
                b.At(cx, cz).Pier = ArchPier.North;
            }
        }

        // Round the walls: each tile along them by chance, starting anywhere on the round
        double density = kind switch
        {
            BasementRoomKind.Store or BasementRoomKind.Pantry or BasementRoomKind.RootCellar => 0.5,
            BasementRoomKind.Workshop or BasementRoomKind.Laundry => 0.4,
            BasementRoomKind.Utility => 0.36,
            BasementRoomKind.Boiler => 0.26,
            BasementRoomKind.Rec => 0.22,
            _ => 0.4,
        };
        var round = new List<(int X, int Z)>();
        for (int x = x0; x <= x1; x++) round.Add((x, z0));
        for (int z = z0 + 1; z <= z1; z++) round.Add((x1, z));
        for (int x = x1 - 1; x >= x0; x--) round.Add((x, z1));
        for (int z = z1 - 1; z > z0; z--) round.Add((x0, z));
        int start = rng.Range(0, round.Count - 1);
        ushort last = 0;
        for (int n = 0; n < round.Count; n++)
        {
            var (x, z) = round[(start + n) % round.Count];
            if (!rng.Chance(density) || !Free(x, z)) continue;
            ArchPier? away = solid(x - 1, z) ? ArchPier.East : solid(x + 1, z) ? ArchPier.West : solid(x, z - 1) ? ArchPier.South : solid(x, z + 1) ? ArchPier.North : null;
            if (away == null || !SafeToBlock(open, x, z)) continue;
            ref Tile t = ref b.At(x, z);
            double roll = rng.NextDouble();
            switch (kind)
            {
                case BasementRoomKind.Utility or BasementRoomKind.Boiler:
                    // The house's plant, long dead: a boiler, tanks and gauges, drums, crates gone through long ago
                    if (roll < 0.18) { t.Stack = (byte)rng.Range(1, 2); t.Looted = rng.Chance(0.8); }
                    else if (roll < 0.32) t.Variant = kind == BasementRoomKind.Boiler ? Props.BasementDrum : Props.BasementBoiler;
                    else if (roll < 0.44) t.Variant = Props.BasementDrum;
                    else if (roll < 0.54) { t.Variant = Props.BasementShelving; t.Stack = 3; }
                    else if (roll < 0.62) t.Variant = Props.BasementCabinet;
                    else if (roll < 0.71) { t.Variant = Props.PressureTank; t.Stack = (byte)rng.Range(0, 1); }
                    else if (roll < 0.8) { t.Variant = Props.GaugeFrame; t.Stack = (byte)rng.Range(0, 3); }
                    else if (roll < 0.87) { t.Variant = Props.RustMachine; t.Stack = (byte)rng.Range(0, 1); }
                    else if (roll < 0.93) t.Variant = Props.PipeStack;
                    else if (roll < 0.97) t.Variant = Props.CoalPile;
                    else t.Variant = Props.TrashCan;
                    break;
                case BasementRoomKind.Workshop:
                    // Somebody's workshop: a bench, tools on the wall, lumber, a barrel of nails
                    if (roll < 0.2) t.Variant = Props.Workbench;
                    else if (roll < 0.33) t.Variant = Props.ToolShelf;
                    else if (roll < 0.43) t.Variant = Props.ToolRack;
                    else if (roll < 0.51) t.Variant = Props.Toolbox;
                    else if (roll < 0.59) t.Variant = Props.NailBarrel;
                    else if (roll < 0.68) t.Variant = Props.Plywood;
                    else if (roll < 0.74) t.Variant = Props.PipeStack;
                    else if (roll < 0.8) t.Variant = Props.CableSpool;
                    else if (roll < 0.86) t.Variant = Props.MachineParts;
                    else if (roll < 0.92) { t.Variant = Props.BasementShelving; t.Stack = (byte)(rng.Chance(0.6) ? 2 : 3); }
                    else if (roll < 0.96) t.Variant = Props.FloorFan;
                    else { t.Stack = 1; t.Looted = true; }
                    break;
                case BasementRoomKind.Laundry:
                    // A washer and a dryer side by side, a utility sink, a basket, a rack with nothing on it
                    if (roll < 0.4)
                    {
                        t.Variant = Props.Laundry;
                        t.Stack = (byte)(last == Props.Laundry ? 1 : 0);
                    }
                    else if (roll < 0.52) { t.Variant = Props.KitchenCounter; t.Stack = 1; }
                    else if (roll < 0.62) t.Variant = Props.LaundryCart;
                    else if (roll < 0.72) t.Variant = Props.ClothesRack;
                    else if (roll < 0.8) t.Variant = Props.BasementShelf;
                    else if (roll < 0.88) t.Variant = Props.TrashBags;
                    else if (roll < 0.94) t.Variant = Props.Wastebasket;
                    else t.Variant = Props.CardboardBoxes;
                    break;
                case BasementRoomKind.Store:
                    // Boxes (stacked two high, labelled), a pile of old furniture, suitcases, stacked chairs, crates
                    if (roll < 0.22) { t.Variant = Props.BasementBoxes; t.Stack = (byte)rng.Range(0, 3); }
                    else if (roll < 0.36) { t.Variant = Props.FurniturePile; t.Stack = (byte)rng.Range(0, 3); }
                    else if (roll < 0.46) t.Variant = Props.Suitcase;
                    else if (roll < 0.54) t.Variant = Props.ChairStack;
                    else if (roll < 0.68) { t.Stack = (byte)rng.Range(1, 2); t.Looted = rng.Chance(0.85); }
                    else if (roll < 0.78) { t.Variant = Props.BasementShelving; t.Stack = (byte)rng.Range(0, 3); }
                    else if (roll < 0.84) t.Variant = Props.TrashBags;
                    else if (roll < 0.89) t.Variant = Props.Plywood;
                    else if (roll < 0.94) t.Variant = Props.ToyBox;
                    else t.Variant = Props.Dresser;
                    break;
                case BasementRoomKind.Pantry or BasementRoomKind.RootCellar:
                    // Shelves of jars (most gone bad), an icebox, sacks, a barrel; in a root cellar, a wine rack now and then
                    if (roll < 0.4) t.Variant = Props.PantryShelf;
                    else if (roll < 0.52) { t.Variant = Props.BasementShelving; t.Stack = 1; }
                    else if (roll < 0.6) t.Variant = kind == BasementRoomKind.RootCellar ? Props.BasementWineRack : Props.BasementShelf;
                    else if (roll < 0.68) t.Variant = Props.Icebox;
                    else if (roll < 0.8) { t.Stack = 1; t.Looted = rng.Chance(0.85); }
                    else if (roll < 0.9) t.Variant = Props.CardboardBoxes;
                    else if (roll < 0.95) t.Variant = Props.SeedSacks;
                    else t.Variant = Props.NailBarrel;
                    break;
                default:
                    // What a family put down in the basement and never came back for
                    if (roll < 0.1) t.Variant = Props.Tv;
                    else if (roll < 0.18) t.Variant = Props.ToyBox;
                    else if (roll < 0.26) t.Variant = Props.Radiator;
                    else if (roll < 0.33) t.Variant = Props.Icebox;
                    else if (roll < 0.39) t.Variant = Props.RotaryPhone;
                    else if (roll < 0.47) { t.Variant = Props.BasementBoxes; t.Stack = (byte)rng.Range(0, 3); }
                    else if (roll < 0.52) t.Variant = Props.ChairStack;
                    else if (roll < 0.59) t.Variant = Props.RadioCabinet;
                    else if (roll < 0.67) t.Variant = Props.Dresser;
                    else if (roll < 0.72) t.Variant = Props.CoatStand;
                    else if (roll < 0.78) t.Variant = Props.WritingDesk;
                    else if (roll < 0.84) t.Variant = Props.HotelBookshelf;
                    else if (roll < 0.89) t.Variant = Props.Suitcase;
                    else if (roll < 0.94) { t.Variant = Props.BasementBoxes; t.Stack = (byte)rng.Range(0, 3); }
                    else t.Variant = Props.Wastebasket;
                    break;
            }
            t.Pier = away.Value;
            last = t.Variant;
        }
        // Out of place: a caution sign or a cone in a room with nothing wet in it, a cable run across the floor
        if (rng.Chance(0.12))
        {
            int x = rng.Range(x0, x1), z = rng.Range(z0, z1);
            if (Free(x, z) && SafeToBlock(open, x, z))
            {
                ref Tile t = ref b.At(x, z);
                t.Variant = rng.Chance(0.6) ? Props.WetFloorSign : Props.TrafficCone;
                t.Pier = (ArchPier)rng.Range(0, 3);
            }
        }
        if (rng.Chance(0.15))
        {
            int x = rng.Range(x0, x1), z = rng.Range(z0, z1);
            if (Free(x, z))
            {
                ref Tile t = ref b.At(x, z);
                t.Variant = Props.FloorCable;
                t.Pier = (ArchPier)rng.Range(0, 3);
            }
        }
    }

    /// <summary>
    /// What else lies about a Cellar cell (resources are scarce here, Fandom's class 2): now and then a box or two in a corner
    /// (most of them gone through), a body left where it fell, and something someone dropped: rope, a bottle, a jar gone bad,
    /// rarely a crowbar.
    /// </summary>
    private void BasementFinds(Builder b, int mx, int mz, List<(int X0, int Z0, int X1, int Z1)> rooms, Func<int, int, bool> solid, Func<int, int, bool> open)
    {
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementFinds));
        bool Free(in Tile t) => t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox && t.Detail == 0 && t.Ceiling != CeilingKind.BasementOpen;
        // A stash: one or two boxes in an inside corner
        if (rooms.Count > 0 && rng.Chance(0.22))
        {
            var (x0, z0, x1, z1) = rooms[rng.Range(0, rooms.Count - 1)];
            foreach (var (x, z) in new[] { (x0, z0), (x1, z0), (x0, z1), (x1, z1) })
            {
                if (x < 2 || z < 2 || x > MacroSize - 3 || z > MacroSize - 3 || !Free(b.At(x, z)) || !SafeToBlock(open, x, z)) continue;
                b.At(x, z).SupplyBox = true;
                int nx = x == x0 ? x + 1 : x - 1;
                if (rng.Chance(0.5) && Free(b.At(nx, z)) && SafeToBlock(open, nx, z)) b.At(nx, z).SupplyBox = true;
                break;
            }
        }
        // Someone who sat down in a corner and stayed
        if (rooms.Count > 0 && rng.Chance(0.28))
        {
            var (x0, z0, x1, z1) = rooms[rng.Range(0, rooms.Count - 1)];
            int x = rng.Range(x0, x1), z = rng.Range(z0, z1);
            ref Tile t = ref b.At(x, z);
            if (x >= 1 && z >= 1 && x <= MacroSize - 2 && z <= MacroSize - 2 && Free(t))
            {
                t.Variant = Props.BasementBody;
                t.Stack = 0;
                t.Pier = (ArchPier)rng.Range(0, 3);
                // and what they carried
                foreach (var (dx, dz) in Steps)
                {
                    ref Tile n = ref b.At(Math.Clamp(x + dx, 1, MacroSize - 2), Math.Clamp(z + dz, 1, MacroSize - 2));
                    if (!Free(n) || !rng.Chance(0.5)) continue;
                    n.Variant = rng.Chance(0.6) ? Props.Backpack : Props.Flashlight;
                    n.Pier = (ArchPier)rng.Range(0, 3);
                    break;
                }
            }
        }
        // Things dropped: 0-2 a cell
        int things = rng.Chance(0.5) ? rng.Range(1, 2) : 0;
        for (int n = 0, tries = 0; n < things && tries < 20; tries++)
        {
            int x = rng.Range(2, MacroSize - 3), z = rng.Range(2, MacroSize - 3);
            ref Tile t = ref b.At(x, z);
            if (!Free(t)) continue;
            double r = rng.NextDouble();
            t.Variant = Props.BasementJunk;
            t.Stack = (byte)(r < 0.35 ? 0 : r < 0.7 ? 2 : r < 0.92 ? 3 : 1); // rope, bottle, jar, crowbar
            t.Pier = (ArchPier)rng.Range(0, 3);
            n++;
        }
    }

    /// <summary>Opens a tile of a Cellar cell back up to bare floor.</summary>
    private static void BasementClear(ref Tile t)
    {
        if (t.Kind is TileKind.Wall or TileKind.Doorway && t.Pattern is WallPattern.BasementCinder or WallPattern.BasementStained or WallPattern.BasementPanel or WallPattern.BasementStuds)
        {
            t.Kind = TileKind.Floor;
            t.Variant = 0;
        }
        if (t.Kind != TileKind.Floor) return;
        t.Floor = FloorKind.BasementFloor;
        t.Variant = 0;
        t.Stack = 0;
    }

    /// <summary>
    /// Splits the inclusive rectangle into cellar rooms with walls one thick (cinder block, panelling, a stained wall),
    /// each wall with a wooden door in it (two in a long one, the second now and then swollen shut), as a BSP tree, so
    /// every room can be reached from every other through a door that opens. A wall may not end against a door. Rooms
    /// come in all sizes down to four across (a closet of a laundry), but the first <paramref name="keepBig"/> pieces of
    /// nine by nine to fifteen by fifteen stay whole, for a crack or a stairwell.
    /// </summary>
    private static void BasementSplit(Builder b, ref Rng rng, ref Rng doors, Func<int, int, bool> solid, int x0, int z0, int x1, int z1,
        List<(int, int, int, int)> rooms, ref int keepBig)
    {
        const int minRoom = 4;
        int w = x1 - x0 + 1, h = z1 - z0 + 1, area = w * h;
        bool canX = w >= 2 * minRoom + 1, canZ = h >= 2 * minRoom + 1;
        if (keepBig > 0 && w >= 9 && h >= 9 && w <= 15 && h <= 15)
        {
            keepBig--;
            rooms.Add((x0, z0, x1, z1));
            return;
        }
        // (Round 3: smaller rooms, most four to eight across, as a house's basement is divided)
        double stop = area <= 24 ? 1 : area <= 48 ? 0.45 : area <= 90 ? 0.15 : area <= 160 ? 0.03 : 0;
        if (!canX && !canZ || rng.Chance(stop))
        {
            rooms.Add((x0, z0, x1, z1));
            return;
        }
        bool splitX = canX && (!canZ || rng.Chance(w >= h ? 0.75 : 0.25));
        int len = splitX ? w : h, across = splitX ? h : w;
        for (int attempt = 0; attempt < 6; attempt++)
        {
            int s = rng.Range(minRoom, len - 1 - minRoom);
            if (splitX ? !solid(x0 + s, z0 - 1) || !solid(x0 + s, z1 + 1) : !solid(x0 - 1, z0 + s) || !solid(x1 + 1, z0 + s)) continue;
            int gap = rng.Range(1, across - 3), gap2 = across >= 16 && rng.Chance(0.5) ? rng.Range(1, across - 3) : -1;
            if (gap2 >= gap - 1 && gap2 <= gap + 1) gap2 = -1;
            double look = doors.NextDouble();
            WallPattern pattern = look < 0.34 ? WallPattern.BasementPanel : look < 0.46 ? WallPattern.BasementStained : WallPattern.BasementCinder;
            for (int k = 0; k < across; k++)
            {
                ref Tile t = ref b.At(splitX ? x0 + s : x0 + k, splitX ? z0 + k : z0 + s);
                SetWall(ref t, pattern, BaseStyle.Plain);
                if (k != gap && k != gap2) continue;
                // A door: shut, or standing open (two in five); the second one in a wall now and then swollen shut in its frame
                t.Kind = TileKind.Doorway;
                t.Variant = Props.BasementDoor;
                t.Floor = FloorKind.BasementFloor;
                double state = doors.NextDouble();
                int st = k == gap2 && state < 0.3 ? 2 : state < 0.6 ? 0 : 1;
                t.Stack = (byte)(st | (doors.Chance(0.5) ? 4 : 0));
                bool flip = doors.Chance(0.5);
                t.Pier = splitX ? (flip ? ArchPier.East : ArchPier.West) : (flip ? ArchPier.South : ArchPier.North);
            }
            if (splitX)
            {
                BasementSplit(b, ref rng, ref doors, solid, x0, z0, x0 + s - 1, z1, rooms, ref keepBig);
                BasementSplit(b, ref rng, ref doors, solid, x0 + s + 1, z0, x1, z1, rooms, ref keepBig);
            }
            else
            {
                BasementSplit(b, ref rng, ref doors, solid, x0, z0, x1, z0 + s - 1, rooms, ref keepBig);
                BasementSplit(b, ref rng, ref doors, solid, x0, z0 + s + 1, x1, z1, rooms, ref keepBig);
            }
            return;
        }
        rooms.Add((x0, z0, x1, z1));
    }

    // ---- Round 3 (2026-11-01): the house's rooms by what they are for ----

    /// <summary>
    /// A hallway two wide right across the cell, between two walls of bare studs and insulation (north-south when
    /// <paramref name="ns"/>), where neither wall would end against a gap in the cell's sides. Its floor's rectangle, or false.
    /// </summary>
    private static bool BasementHall(Builder b, ref Rng rng, Func<int, int, bool> solid, out (int X0, int Z0, int X1, int Z1) hall, out bool ns)
    {
        for (int attempt = 0; attempt < 6; attempt++)
        {
            ns = rng.Chance(0.5);
            int a = rng.Range(6, MacroSize - 11);
            bool ok = true;
            foreach (int line in new[] { a, a + 3 })
                ok &= ns ? solid(line, 0) && solid(line, MacroSize) : solid(0, line) && solid(MacroSize, line);
            if (!ok) continue;
            for (int i = 1; i < MacroSize; i++)
                foreach (int line in new[] { a, a + 3 })
                    SetWall(ref b.At(ns ? line : i, ns ? i : line), WallPattern.BasementStuds, BaseStyle.Plain);
            hall = ns ? (a + 1, 1, a + 2, MacroSize - 1) : (1, a + 1, MacroSize - 1, a + 2);
            return true;
        }
        hall = (-1, -1, -1, -1);
        ns = false;
        return false;
    }

    /// <summary>Every room against a hallway's wall gets a door onto it (shut or standing open, never swollen shut), if it has none.</summary>
    private static void BasementHallDoors(Builder b, ref Rng doors, List<(int X0, int Z0, int X1, int Z1)> rooms, (int X0, int Z0, int X1, int Z1) hall, bool ns)
    {
        foreach (var (x0, z0, x1, z1) in rooms)
        {
            int line = ns ? (x1 == hall.X0 - 2 ? hall.X0 - 1 : x0 == hall.X1 + 2 ? hall.X1 + 1 : -1)
                          : (z1 == hall.Z0 - 2 ? hall.Z0 - 1 : z0 == hall.Z1 + 2 ? hall.Z1 + 1 : -1);
            if (line < 0) continue;
            int from = ns ? z0 : x0, to = ns ? z1 : x1;
            bool has = false;
            for (int i = from; i <= to && !has; i++) has = b.At(ns ? line : i, ns ? i : line).Kind == TileKind.Doorway;
            if (has) continue;
            int at = from + (to - from) / 2 + (to - from >= 4 ? doors.Range(-1, 1) : 0);
            ref Tile t = ref b.At(ns ? line : at, ns ? at : line);
            t.Kind = TileKind.Doorway;
            t.Variant = Props.BasementDoor;
            t.Floor = FloorKind.BasementFloor;
            t.Stack = (byte)((doors.Chance(0.55) ? 0 : 1) | (doors.Chance(0.5) ? 4 : 0));
            bool flip = doors.Chance(0.5);
            t.Pier = ns ? (flip ? ArchPier.East : ArchPier.West) : (flip ? ArchPier.South : ArchPier.North);
        }
    }

    /// <summary>
    /// What each room is for. A house's basement has one furnace room, one laundry (beside the furnace room where it can:
    /// the water and the flue), a rec room in its biggest finished room, and the rest workshops, store rooms, pantries and
    /// root cellars, finished rooms. The room of the dead is a store room; the hallway a hallway.
    /// </summary>
    private static BasementRoomKind[] BasementAssignKinds(ref Rng rng, List<(int X0, int Z0, int X1, int Z1)> rooms, int crack, int escher, int charnel, int hall)
    {
        int n = rooms.Count;
        var kinds = new BasementRoomKind[n];
        for (int k = 0; k < n; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            kinds[k] = BasementPickKind(ref rng, x1 - x0 + 1, z1 - z0 + 1);
            // (a root cellar instead of a pantry, half the time)
            if (kinds[k] == BasementRoomKind.Pantry && rng.Chance(0.5)) kinds[k] = BasementRoomKind.RootCellar;
        }
        if (charnel >= 0) kinds[charnel] = BasementRoomKind.Store;
        if (hall >= 0) kinds[hall] = BasementRoomKind.Hall;
        bool Plain(int k) => k != crack && k != escher && k != charnel && k != hall;
        int Area(int k) => (rooms[k].X1 - rooms[k].X0 + 1) * (rooms[k].Z1 - rooms[k].Z0 + 1);
        bool Next(int a, int c)
        {
            var (ax0, az0, ax1, az1) = rooms[a];
            var (cx0, cz0, cx1, cz1) = rooms[c];
            bool overlapZ = az0 <= cz1 && cz0 <= az1, overlapX = ax0 <= cx1 && cx0 <= ax1;
            return overlapZ && (ax1 + 2 == cx0 || cx1 + 2 == ax0) || overlapX && (az1 + 2 == cz0 || cz1 + 2 == az0);
        }
        // The rec room: the biggest room six by six or more
        int rec = -1;
        for (int k = 0; k < n; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            if (Plain(k) && x1 - x0 >= 5 && z1 - z0 >= 5 && (rec < 0 || Area(k) > Area(rec))) rec = k;
        }
        if (rec >= 0 && rng.Chance(0.75)) kinds[rec] = BasementRoomKind.Rec;
        else rec = -1;
        // The furnace room: a middling room, five across or more
        int boiler = -1;
        int start = rng.Range(0, Math.Max(0, n - 1));
        for (int j = 0; j < n && boiler < 0; j++)
        {
            int k = (start + j) % n;
            var (x0, z0, x1, z1) = rooms[k];
            if (Plain(k) && k != rec && x1 - x0 >= 4 && z1 - z0 >= 4 && Area(k) <= 110) boiler = k;
        }
        if (boiler >= 0 && rng.Chance(0.9)) kinds[boiler] = BasementRoomKind.Boiler;
        else boiler = -1;
        // The laundry: beside the furnace room where a room fits, else wherever the dice put one
        if (boiler >= 0)
            for (int k = 0; k < n; k++)
                if (Plain(k) && k != rec && k != boiler && Next(k, boiler) && Area(k) <= 70)
                {
                    for (int j = 0; j < n; j++)
                        if (kinds[j] == BasementRoomKind.Laundry) kinds[j] = BasementRoomKind.Store;
                    kinds[k] = BasementRoomKind.Laundry;
                    break;
                }
        // (a house has one laundry, one furnace room, one rec room: the dice's others become store rooms)
        bool laundry = false;
        for (int k = 0; k < n; k++)
        {
            if (kinds[k] == BasementRoomKind.Laundry) { if (laundry) kinds[k] = BasementRoomKind.Store; laundry = true; }
            if (kinds[k] == BasementRoomKind.Utility && boiler >= 0 && rng.Chance(0.5)) kinds[k] = BasementRoomKind.Workshop;
        }
        return kinds;
    }

    /// <summary>The way to the right of something facing <paramref name="facing"/> (its left part to its right part).</summary>
    private static (int Dx, int Dz) BasementRightOf(ArchPier facing) => facing switch
    {
        ArchPier.North => (1, 0),
        ArchPier.South => (-1, 0),
        ArchPier.East => (0, 1),
        _ => (0, -1),
    };

    /// <summary>
    /// Hangs something on the wall behind a tile (at head height; nothing is in the way of walking): the tile must have the
    /// wall at its back, nothing hanging there yet, and anything standing on it must face the same way.
    /// </summary>
    private static bool BasementHang(Builder b, Func<int, int, bool> solid, int x, int z, ushort what, ArchPier away)
    {
        if (x < 1 || z < 1 || x >= MacroSize - 1 || z >= MacroSize - 1) return false;
        ref Tile t = ref b.At(x, z);
        if (t.Kind != TileKind.Floor || t.Overhead != 0 || t.Detail != 0 || t.SupplyBox || t.Ceiling == CeilingKind.BasementOpen) return false;
        if (t.Variant is Props.BasementFurnace or Props.BasementHeater or Props.BasementShelving or Props.BasementBoxes or Props.BasementWineRack or Props.BasementLadder) return false;
        if (t.Variant == 0 && t.Stack > 0) return false;
        if (t.Variant != 0 && t.Pier != away) return false;
        var (dx, dz) = PierStep(away);
        if (!solid(x - dx, z - dz)) return false;
        t.Overhead = what;
        if (t.Variant == 0) t.Pier = away;
        return true;
    }

    /// <summary>A hallway's bulbs: one every four steps down its far side, in runs lit, flickering and dead.</summary>
    private static void BasementHallBulbs(Builder b, ref Rng rng, int x0, int z0, int x1, int z1)
    {
        bool ns = x1 - x0 < z1 - z0;
        // (lit half the time, flickering three in ten, dead two in ten; a run changes one bulb in two)
        int State(ref Rng r) => r.Chance(0.5) ? 0 : r.Chance(0.6) ? 1 : 2;
        int state = State(ref rng), phase = rng.Range(1, 4);
        for (int i = phase; i < MacroSize - 1; i += 4)
        {
            ref Tile t = ref b.At(ns ? x1 : i, ns ? i : z1);
            if (rng.Chance(0.5)) state = State(ref rng);
            if (t.Kind != TileKind.Floor || t.Pipe != 0 || t.Detail != 0 || t.Ceiling == CeilingKind.BasementOpen) continue;
            t.Ceiling = state == 0 ? CeilingKind.BasementBulbOn : state == 1 ? CeilingKind.BasementBulbFlicker : CeilingKind.BasementBulbOff;
        }
    }

    /// <summary>A hallway: mostly clear, now and then boxes stacked against a wall, a caution sign under the duct, a web.</summary>
    private static void BasementFurnishHall(Builder b, ref Rng rng, int x0, int z0, int x1, int z1, bool[] keepClear, Func<int, int, bool> solid, Func<int, int, bool> open)
    {
        bool ns = x1 - x0 < z1 - z0;
        for (int i = 2; i < MacroSize - 2; i++)
            foreach (int across in ns ? new[] { x0, x1 } : new[] { z0, z1 })
            {
                int x = ns ? across : i, z = ns ? i : across;
                ref Tile t = ref b.At(x, z);
                if (keepClear[TileIndex(x, z)] || t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0 || t.Detail != 0) continue;
                ArchPier away = ns ? (across == x0 ? ArchPier.East : ArchPier.West) : (across == z0 ? ArchPier.South : ArchPier.North);
                var (dx, dz) = PierStep(away);
                if (!solid(x - dx, z - dz)) continue;
                double r = rng.NextDouble();
                if (r < 0.05 && SafeToBlock(open, x, z)) { t.Variant = Props.BasementBoxes; t.Stack = (byte)rng.Range(0, 3); t.Pier = away; }
                else if (r < 0.065 && SafeToBlock(open, x, z)) { t.Variant = Props.ChairStack; t.Pier = away; }
                else if (r < 0.08) BasementHang(b, solid, x, z, Overheads.BasementWatchHead, away);
                else if (r < 0.09) { t.Variant = Props.BasementJunk; t.Stack = (byte)(rng.Chance(0.5) ? 0 : 2); t.Pier = away; }
            }
        // (Round 4) a hall that ends on the cell's wall ends on something: steel shelving and boxes against it
        foreach (int end in new[] { 1, MacroSize - 1 })
        {
            int ox = ns ? 0 : (end == 1 ? -1 : 1), oz = ns ? (end == 1 ? -1 : 1) : 0;
            ArchPier back = ns ? (end == 1 ? ArchPier.South : ArchPier.North) : (end == 1 ? ArchPier.East : ArchPier.West);
            int k = 0;
            foreach (int across in ns ? new[] { x0, x1 } : new[] { z0, z1 })
            {
                int x = ns ? across : end, z = ns ? end : across;
                ref Tile t = ref b.At(x, z);
                bool free = solid(x + ox, z + oz) && !keepClear[TileIndex(x, z)] && t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0
                            && t.Detail == 0 && !t.SupplyBox && SafeToBlock(open, x, z);
                if (k++ > 0 && !free) continue;
                if (!free) continue;
                t.Variant = k == 1 ? Props.BasementShelving : Props.BasementBoxes;
                t.Stack = (byte)rng.Range(0, 3);
                t.Pier = back;
            }
        }
    }

    /// <summary>
    /// What a room is for, built first: the furnace room's furnace and water heater (their ducts and pipes up into the
    /// joists), its coal chute over the coal, the sump in a corner, the fuse box; the laundry's washer and dryer, sink and a
    /// clothesline across the room; the workshop's long bench under a pegboard of tools; the rec room's pool table under its
    /// lamp on a rug, an old sofa facing a TV. Returns whether it took the middle of the room.
    /// </summary>
    private static bool BasementSetPieces(Builder b, ref Rng rng, BasementRoomKind kind, int x0, int z0, int x1, int z1, bool middleTaken,
        bool[] keepClear, Func<int, int, bool> solid, Func<int, int, bool> open)
    {
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        bool Free(int x, int z)
        {
            if (x < 1 || z < 1 || x >= MacroSize - 1 || z >= MacroSize - 1 || keepClear[TileIndex(x, z)]) return false;
            ref Tile t = ref b.At(x, z);
            return t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox && t.Detail == 0 && t.Ceiling != CeilingKind.BasementOpen
                && t.Overhead is 0 or Overheads.BasementWire;
        }
        bool Bare(int x, int z) => b.At(x, z).Ceiling is CeilingKind.BasementCeiling or CeilingKind.BasementStained or CeilingKind.BasementJoists;
        bool Put(int x, int z, ushort v, ArchPier p, int stack = 0)
        {
            if (!Free(x, z) || !SafeToBlock(open, x, z)) return false;
            ref Tile t = ref b.At(x, z);
            t.Variant = v;
            t.Pier = p;
            t.Stack = (byte)stack;
            return true;
        }
        // Two tiles side by side along a wall (both with the wall at their back), left then right as seen from in front
        bool Pair(int x, int z, ushort v, ArchPier away, int s0 = 0, int s1 = 1)
        {
            var (rx, rz) = BasementRightOf(away);
            var (dx, dz) = PierStep(away);
            int x2 = x + rx, z2 = z + rz;
            if (x2 < x0 || x2 > x1 || z2 < z0 || z2 > z1 || !Free(x2, z2) || !solid(x2 - dx, z2 - dz)) return false;
            if (!Put(x, z, v, away, s0)) return false;
            if (Put(x2, z2, v, away, s1)) return true;
            b.At(x, z).Variant = 0;
            b.At(x, z).Stack = 0;
            return false;
        }
        // The wall tiles round the room with the way away from their wall, from somewhere along it by chance
        var spots = new List<(int X, int Z, ArchPier Away)>();
        for (int x = x0; x <= x1; x++) { if (solid(x, z0 - 1)) spots.Add((x, z0, ArchPier.South)); }
        for (int z = z0; z <= z1; z++) { if (solid(x1 + 1, z)) spots.Add((x1, z, ArchPier.West)); }
        for (int x = x1; x >= x0; x--) { if (solid(x, z1 + 1)) spots.Add((x, z1, ArchPier.North)); }
        for (int z = z1; z >= z0; z--) { if (solid(x0 - 1, z)) spots.Add((x0, z, ArchPier.East)); }
        if (spots.Count == 0) return false;
        int first = rng.Range(0, spots.Count - 1);
        IEnumerable<(int X, int Z, ArchPier Away)> Round()
        {
            for (int n = 0; n < spots.Count; n++) yield return spots[(first + n) % spots.Count];
        }
        // (a wall's middle first: the furnace and the bench stand out from the corners)
        bool Middling(int x, int z, ArchPier away) => away is ArchPier.North or ArchPier.South ? x > x0 && x < x1 : z > z0 && z < z1;

        switch (kind)
        {
            case BasementRoomKind.Boiler:
            {
                (int X, int Z, ArchPier Away)? furnace = null;
                foreach (var (x, z, away) in Round())
                    if (Middling(x, z, away) && Bare(x, z) && b.At(x, z).Overhead == 0 && Put(x, z, Props.BasementFurnace, away)) { furnace = (x, z, away); break; }
                if (furnace is (var fx, var fz, var fa))
                {
                    // The water heater two along the same wall, either way
                    var (rx, rz) = BasementRightOf(fa);
                    var (dx, dz) = PierStep(fa);
                    foreach (int s in rng.Chance(0.5) ? new[] { 2, -2 } : new[] { -2, 2 })
                    {
                        int hx = fx + rx * s, hz = fz + rz * s;
                        if (hx < x0 || hx > x1 || hz < z0 || hz > z1 || !Bare(hx, hz) || !solid(hx - dx, hz - dz) || b.At(hx, hz).Overhead != 0) continue;
                        if (Put(hx, hz, Props.BasementHeater, fa)) break;
                    }
                }
                // The coal chute's hatch on another wall, the coal heaped under it
                foreach (var (x, z, away) in Round())
                {
                    if (furnace is (_, _, var ca) && ca == away) continue;
                    if (!Middling(x, z, away) || !Put(x, z, Props.CoalPile, away)) continue;
                    if (!BasementHang(b, solid, x, z, Overheads.BasementChute, away)) { b.At(x, z).Variant = 0; continue; }
                    break;
                }
                // The fuse box, its conduit up into the joists
                foreach (var (x, z, away) in Round())
                    if (Free(x, z) && b.At(x, z).Pipe == 0 && Bare(x, z) && BasementHang(b, solid, x, z, Overheads.BasementFuseBox, away)) break;
                // The sump in a corner
                foreach (var (x, z) in new[] { (x0, z0), (x1, z0), (x1, z1), (x0, z1) })
                    if (Free(x, z)) { b.At(x, z).Variant = Props.BasementSump; break; }
                return false;
            }
            case BasementRoomKind.Laundry:
            {
                // Washer and dryer side by side, the sink beside them
                foreach (var (x, z, away) in Round())
                {
                    if (!Pair(x, z, Props.Laundry, away)) continue;
                    var (rx, rz) = BasementRightOf(away);
                    var (dx, dz) = PierStep(away);
                    int sx = x + 2 * rx, sz = z + 2 * rz;
                    if (sx >= x0 && sx <= x1 && sz >= z0 && sz <= z1 && solid(sx - dx, sz - dz)) Put(sx, sz, Props.KitchenCounter, away, 1);
                    break;
                }
                // A line across the room's middle, along it, with the washing left on it
                bool alongX = w >= h;
                int mid = alongX ? z0 + h / 2 : x0 + w / 2;
                for (int i = alongX ? x0 : z0; i <= (alongX ? x1 : z1); i++)
                {
                    ref Tile t = ref b.At(alongX ? i : mid, alongX ? mid : i);
                    if (t.Kind == TileKind.Floor && t.Overhead == 0 && t.Pipe == 0 && Bare(alongX ? i : mid, alongX ? mid : i))
                        t.Overhead = alongX ? Overheads.BasementLineWE : Overheads.BasementLineNS;
                }
                return false;
            }
            case BasementRoomKind.Workshop:
            {
                // The bench along a wall, a pegboard of tools over it
                foreach (var (x, z, away) in Round())
                {
                    if (!Middling(x, z, away) || !Pair(x, z, Props.BasementBench, away)) continue;
                    var (rx, rz) = BasementRightOf(away);
                    BasementHang(b, solid, x, z, Overheads.BasementPegboard, away);
                    BasementHang(b, solid, x + rx, z + rz, Overheads.BasementPegboard, away);
                    break;
                }
                return false;
            }
            case BasementRoomKind.Rec:
            {
                bool took = false;
                // The pool table in the middle, along the room, a clear way all round it, its lamp over it, a rug under it
                if (!middleTaken && w >= 6 && h >= 6)
                {
                    bool alongX = w >= h;
                    int cx = x0 + (w - 1) / 2, cz = z0 + (h - 1) / 2;
                    ArchPier f = alongX ? ArchPier.North : ArchPier.East;
                    var (rx, rz) = BasementRightOf(f);
                    bool clear = true;
                    for (int dz = -1; dz <= 1 + rz && clear; dz++)
                        for (int dx = -1; dx <= 1 + rx && clear; dx++)
                            clear = Free(cx + dx, cz + dz);
                    if (clear)
                    {
                        foreach (var (px, pz, half) in new[] { (cx, cz, 0), (cx + rx, cz + rz, 1) })
                        {
                            ref Tile t = ref b.At(px, pz);
                            // (the lamp over the table, not a bare bulb)
                            if (!Bare(px, pz) && t.Ceiling != CeilingKind.BasementOpen)
                                t.Ceiling = Bare(cx - 1, cz - 1) ? b.At(cx - 1, cz - 1).Ceiling : CeilingKind.BasementCeiling;
                            t.Variant = Props.BasementPoolTable;
                            t.Pier = f;
                            t.Stack = (byte)half;
                            if (t.Pipe == 0 && Bare(px, pz)) t.Overhead = Overheads.BasementPoolLamp;
                            else t.Overhead = 0;
                        }
                        for (int dz = -1; dz <= 1 + rz; dz++)
                            for (int dx = -1; dx <= 1 + rx; dx++)
                                if (b.At(cx + dx, cz + dz).Kind == TileKind.Floor) b.At(cx + dx, cz + dz).Floor = FloorKind.BasementRug;
                        took = true;
                    }
                }
                // The old sofa against a wall, and the TV on the wall across from it
                foreach (var (x, z, away) in Round())
                {
                    if (!Middling(x, z, away) || !Pair(x, z, Props.LongSofa, away)) continue;
                    var (dx, dz) = PierStep(away);
                    for (int k = 2; k < 16; k++)
                    {
                        int tx = x + dx * k, tz = z + dz * k;
                        if (tx < x0 || tx > x1 || tz < z0 || tz > z1) break;
                        if (solid(tx + dx, tz + dz)) { Put(tx, tz, Props.Tv, Opposite(away)); break; }
                    }
                    break;
                }
                // (Round 4) the cue rack on another wall, where the pool table is
                if (took)
                    foreach (var (x, z, away) in Round())
                        if (Middling(x, z, away) && b.At(x, z).Overhead == 0 && Put(x, z, Props.BasementCueRack, away)) break;
                // (Round 4) a home bar against a wall in most, a stool or two before it (the Wikidot clipping's bar cellar,
                // as a family's rec room has one)
                if (rng.Chance(0.7))
                    foreach (var (x, z, away) in Round())
                    {
                        // (not hard by a doorway: its casing would cut into the mirror)
                        var (rx, rz) = BasementRightOf(away);
                        bool Door(int ax, int az) => ax >= 0 && az >= 0 && ax < MacroSize && az < MacroSize && b.At(ax, az).Kind == TileKind.Doorway;
                        if (!Middling(x, z, away) || Door(x - rx, z - rz) || Door(x + 2 * rx, z + 2 * rz) || !Pair(x, z, Props.BasementBar, away)) continue;
                        var (dx, dz) = PierStep(away);
                        foreach (int s in new[] { 0, 1 })
                        {
                            int sx = x + rx * s + dx, sz = z + rz * s + dz;
                            if (sx >= x0 && sx <= x1 && sz >= z0 && sz <= z1 && rng.Chance(0.75)) Put(sx, sz, Props.BasementStool, away);
                        }
                        break;
                    }
                return took;
            }
            case BasementRoomKind.RootCellar:
                // A wine rack against a wall now and then
                foreach (var (x, z, away) in Round())
                    if (rng.Chance(0.5) && Middling(x, z, away) && Put(x, z, Props.BasementWineRack, away)) break;
                return false;
        }
        return false;
    }

    /// <summary>
    /// What is written on the walls: caution signs that serve no purpose (Fandom's "caution signs"), DANGER DEEP WATER
    /// beside the stairs down into the Flood, a calendar stopped long ago, a fuse box in a cell without a furnace room;
    /// and cobwebs in the corners of the joists.
    /// </summary>
    private static void BasementWallSigns(Builder b, ref Rng rng, List<(int X0, int Z0, int X1, int Z1)> rooms, BasementRoomKind[] kinds, BasementSide[] sides, Func<int, int, bool> solid)
    {
        // Beside each way down into the water, on the wall next to it
        for (int s = 0; s < 4; s++)
        {
            if (!sides[s].Ours || sides[s].Dry) continue;
            var g = sides[s].Gaps;
            ArchPier inward = Opposite(BasementOutward(s));
            foreach (int i in new[] { g.A - 1, g.A + g.Width })
            {
                var (x, z, dx, dz) = BasementSideTile(s, i);
                if (BasementHang(b, solid, x + dx, z + dz, Overheads.BasementDeepWater, inward)) break;
            }
        }
        bool boiler = false;
        foreach (var k in kinds) boiler |= k == BasementRoomKind.Boiler;
        for (int k = 0; k < rooms.Count; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            BasementRoomKind kind = kinds[k];
            // A wall tile of the room at random, and the way away from its wall
            (int X, int Z, ArchPier Away)? Spot(ref Rng rng)
            {
                for (int tries = 0; tries < 12; tries++)
                {
                    int side = rng.Range(0, 3);
                    int x = side switch { 1 => x1, 3 => x0, _ => rng.Range(x0, x1) }, z = side switch { 0 => z0, 2 => z1, _ => rng.Range(z0, z1) };
                    ArchPier away = side switch { 0 => ArchPier.South, 1 => ArchPier.West, 2 => ArchPier.North, _ => ArchPier.East };
                    var (dx, dz) = PierStep(away);
                    if (solid(x - dx, z - dz)) return (x, z, away);
                }
                return null;
            }
            if (rng.Chance(kind is BasementRoomKind.Utility or BasementRoomKind.Boiler or BasementRoomKind.Store ? 0.22 : 0.1) && Spot(ref rng) is (var sx, var sz, var sa))
                BasementHang(b, solid, sx, sz, rng.Chance(0.7) ? Overheads.BasementCaution : Overheads.BasementWatchHead, sa);
            if (rng.Chance(kind is BasementRoomKind.Finished or BasementRoomKind.Rec or BasementRoomKind.Workshop or BasementRoomKind.Laundry ? 0.16 : 0.03) && Spot(ref rng) is (var cx, var cz, var ca))
                BasementHang(b, solid, cx, cz, Overheads.BasementCalendar, ca);
            if (!boiler && kind is BasementRoomKind.Utility or BasementRoomKind.Hall && Spot(ref rng) is (var fx, var fz, var fa) && b.At(fx, fz).Pipe == 0
                && BasementHang(b, solid, fx, fz, Overheads.BasementFuseBox, fa))
                boiler = true;
            // Cobwebs up in the corners
            double webs = kind is BasementRoomKind.Hall or BasementRoomKind.Store or BasementRoomKind.RootCellar or BasementRoomKind.Utility or BasementRoomKind.Boiler ? 0.45 : 0.2;
            (int X, int Z, int Dx, int Dz)[] corners = { (x0, z0, -1, -1), (x1, z0, 1, -1), (x1, z1, 1, 1), (x0, z1, -1, 1) };
            for (int c = 0; c < 4; c++)
            {
                var (x, z, dx, dz) = corners[c];
                if (x < 1 || z < 1 || x >= MacroSize - 1 || z >= MacroSize - 1 || !rng.Chance(webs)) continue;
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Floor || t.Overhead != 0 || t.Pipe != 0 || t.Detail != 0 || !solid(x + dx, z) || !solid(x, z + dz)) continue;
                if (t.Ceiling is not (CeilingKind.BasementCeiling or CeilingKind.BasementStained or CeilingKind.BasementJoists)) continue;
                if (t.Variant is Props.BasementFurnace or Props.BasementHeater) continue;
                t.Overhead = (ushort)(Overheads.BasementCobweb + c);
            }
        }
    }

    /// <summary>Whether a Basement door is swollen shut (it will not open).</summary>
    public static bool BasementDoorJammed(in Tile t) => t.Variant == Props.BasementDoor && (t.Stack & 3) == 2;

    // ---- The Flood ----

    private void BuildBasementFlood(Builder b, int mx, int mz, BasementSide[] sides, bool patch)
    {
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementMaze));
        const int n = MacroSize / BasementPitch; // nodes each way
        static int Node(int k) => BasementNode0 + BasementPitch * k;
        var open = new bool[MacroSize * MacroSize];
        void Rect(int xa, int za, int xb, int zb)
        {
            for (int z = Math.Max(0, Math.Min(za, zb)); z <= Math.Min(MacroSize - 1, Math.Max(za, zb)); z++)
                for (int x = Math.Max(0, Math.Min(xa, xb)); x <= Math.Min(MacroSize - 1, Math.Max(xa, xb)); x++)
                    open[TileIndex(x, z)] = true;
        }
        static bool InPatch(int i, int j) => i is 1 or 2 && j is 1 or 2;
        bool InRoom(int x, int z) => patch && x > BasementPatchLo && x < BasementPatchHi && z > BasementPatchLo && z < BasementPatchHi;

        // A spanning tree over the nodes (a hash-ordered union-find over the links), a few more links for loops; a Dry
        // Patch's four middle nodes are its one room
        var parent = new int[n * n];
        for (int i = 0; i < parent.Length; i++) parent[i] = i;
        int Find(int a) { while (parent[a] != a) a = parent[a] = parent[parent[a]]; return a; }
        if (patch)
            foreach (int k in new[] { 1 * n + 2, 2 * n + 1, 2 * n + 2 }) parent[Find(k)] = Find(1 * n + 1);
        var links = new List<(int I, int J, bool AlongX, double Order)>();
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (i + 1 < n && !(patch && InPatch(i, j) && InPatch(i + 1, j))) links.Add((i, j, true, rng.NextDouble()));
                if (j + 1 < n && !(patch && InPatch(i, j) && InPatch(i, j + 1))) links.Add((i, j, false, rng.NextDouble()));
            }
        links.Sort((p, q) => p.Order.CompareTo(q.Order));
        var kept = new List<(int I, int J, bool AlongX)>();
        foreach (var (i, j, alongX, _) in links)
        {
            int a = Find(j * n + i), c = Find(alongX ? j * n + i + 1 : (j + 1) * n + i);
            if (a != c) { parent[c] = a; kept.Add((i, j, alongX)); }
            else if (rng.Chance(0.2)) kept.Add((i, j, alongX));
        }
        // How many ways lead from each node (for the dead ends, where the drowned are)
        var degree = new int[n * n];
        foreach (var (i, j, alongX) in kept)
        {
            degree[j * n + i]++;
            degree[alongX ? j * n + i + 1 : (j + 1) * n + i]++;
        }

        // The passages: every node's square, every kept link, and a stub out to each gap in the cell's sides
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
                if (!(patch && InPatch(i, j))) Rect(Node(i) - 1, Node(j) - 1, Node(i) + 1, Node(j) + 1);
        var entries = new List<(int X, int Z, int Dx, int Dz)>(); // a Dry Patch's doorway tiles, and the way out of it
        foreach (var (i, j, alongX) in kept)
        {
            int ax = Node(i), az = Node(j), bx = alongX ? Node(i + 1) : ax, bz = alongX ? az : Node(j + 1);
            if (patch && (InPatch(i, j) || InPatch(alongX ? i + 1 : i, alongX ? j : j + 1)))
            {
                // Into the room: from the outer node up to the room's wall
                bool fromLow = !InPatch(i, j); // the outer node is the low one (west or north)
                int wx = alongX ? (fromLow ? BasementPatchLo : BasementPatchHi) : ax, wz = alongX ? az : (fromLow ? BasementPatchLo : BasementPatchHi);
                if (alongX) Rect(fromLow ? ax : wx, az - 1, fromLow ? wx : bx, az + 1);
                else Rect(ax - 1, fromLow ? az : wz, ax + 1, fromLow ? wz : bz);
                int dx = alongX ? (fromLow ? -1 : 1) : 0, dz = alongX ? 0 : (fromLow ? -1 : 1);
                for (int k = -1; k <= 1; k++) entries.Add((alongX ? wx : wx + k, alongX ? wz + k : wz, dx, dz));
                continue;
            }
            if (alongX) Rect(ax, az - 1, bx, az + 1);
            else Rect(ax - 1, az, ax + 1, bz);
            // Pipes along the north (or west) side of the passage, between the nodes; now and then a leaking one
            ushort pipe = alongX ? (rng.Chance(0.15) ? Pipes.BasementLeakWE : Pipes.BasementPipeWE) : (rng.Chance(0.15) ? Pipes.BasementLeakNS : Pipes.BasementPipeNS);
            if (rng.Chance(0.7))
                for (int k = 2; k <= BasementPitch - 2; k++)
                    b.At(alongX ? ax + k : ax - 1, alongX ? az - 1 : az + k).Pipe = pipe;
        }
        var stairs = new List<(int X, int Z, int Dx, int Dz, int Side)>();
        var stubbed = new bool[n * n];
        for (int s = 0; s < 4; s++)
        {
            if (!sides[s].Ours) continue;
            var g = sides[s].Gaps;
            foreach (int start in g.B >= 0 ? new[] { g.A, g.B } : new[] { g.A })
            {
                int line = start + 1;
                var (x, z, dx, dz) = BasementSideTile(s, line);
                // From the side to the node on that line
                int outer = Node(s < 2 ? 0 : n - 1);
                if (s is 0 or 2) Rect(x, line - 1, outer, line + 1);
                else Rect(line - 1, z, line + 1, outer);
                int along = (line - BasementNode0) / BasementPitch;
                if (along >= 0 && along < n) stubbed[s is 0 or 2 ? along * n + (s == 0 ? 0 : n - 1) : (s == 1 ? 0 : n - 1) * n + along] = true;
                if (!sides[s].Dry) continue;
                for (int k = -1; k <= 1; k++)
                {
                    var (sx, sz, _, _) = BasementSideTile(s, line + k);
                    stairs.Add((sx, sz, dx, dz, s));
                }
            }
        }

        // Lay it down: the passages flooded, everything else wall; the room dry, ringed by its walls
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                t.Ceiling = CeilingKind.BasementCeiling;
                if (InRoom(lx, lz))
                {
                    t.Kind = TileKind.Floor;
                    t.Zone = (byte)BasementZone.Patch;
                    t.Floor = FloorKind.BasementPatch;
                    t.Pipe = 0;
                    continue;
                }
                bool ring = patch && lx >= BasementPatchLo && lx <= BasementPatchHi && lz >= BasementPatchLo && lz <= BasementPatchHi;
                t.Zone = (byte)(ring ? BasementZone.Patch : BasementZone.Flood);
                if (ring)
                {
                    SetWall(ref t, WallPattern.BasementCinder, BaseStyle.Plain);
                    t.Pipe = 0;
                    continue;
                }
                // The cell's own west and north lines, where the edge laid a wall
                if ((lx == 0 || lz == 0) && t.Kind == TileKind.Wall) { t.Pipe = 0; continue; }
                if (open[TileIndex(lx, lz)])
                {
                    t.Kind = TileKind.Water;
                    t.Floor = FloorKind.BasementBed;
                }
                else
                {
                    SetWall(ref t, WallPattern.BasementFloodWall, BaseStyle.Plain);
                    t.Pipe = 0;
                }
            }

        // The doorways into the Dry Patch, and the steps up to them
        foreach (var (x, z, dx, dz) in entries)
        {
            ref Tile door = ref b.At(x, z);
            door.Kind = TileKind.Floor;
            door.Zone = (byte)BasementZone.Patch;
            door.Floor = FloorKind.BasementPatch;
            ArchPier toward = dx < 0 ? ArchPier.East : dx > 0 ? ArchPier.West : dz < 0 ? ArchPier.South : ArchPier.North;
            BasementStep(ref b.At(x + dx, z + dz), 2, toward);
            BasementStep(ref b.At(x + 2 * dx, z + 2 * dz), 1, toward);
        }
        // The stairs up out of the water to a Cellar cell
        foreach (var (x, z, dx, dz, s) in stairs)
        {
            BasementStep(ref b.At(x, z), 2, BasementOutward(s));
            BasementStep(ref b.At(x + dx, z + dz), 1, BasementOutward(s));
        }

        // A dim lamp over about one node in three (the Dry Patch has one bulb), dead now and then
        var furnish = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementFurnish));
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (patch && InPatch(i, j) || !furnish.Chance(0.32)) continue;
                ref Tile t = ref b.At(Node(i), Node(j));
                if (t.Kind == TileKind.Water && t.Height == 0) t.Ceiling = furnish.Chance(0.2) ? CeilingKind.BasementBulbOff : CeilingKind.BasementBulbDim;
            }
        // The drowned, in the dead ends: bloated, a week in the water by the look of them. One in a long while is the man the
        // newspaper said had never resurfaced
        var dead = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementDead));
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (patch && InPatch(i, j) || degree[j * n + i] != 1 || stubbed[j * n + i]) continue;
                if (!dead.Chance(0.3))
                {
                    // (Round 3) or boxes that floated down here and sank in a corner of it, their tops just out of the water
                    if (!dead.Chance(0.35)) continue;
                    ref Tile c = ref b.At(Node(i) + (dead.Chance(0.5) ? -1 : 1), Node(j) + (dead.Chance(0.5) ? -1 : 1));
                    if (c.Kind != TileKind.Water || c.Height != 0 || c.Variant != 0) continue;
                    c.Variant = Props.BasementBoxes;
                    c.Stack = (byte)dead.Range(0, 3);
                    c.Pier = (ArchPier)dead.Range(0, 3);
                    continue;
                }
                ref Tile t = ref b.At(Node(i) + dead.Range(-1, 1), Node(j) + dead.Range(-1, 1));
                if (t.Kind != TileKind.Water || t.Height != 0) continue;
                t.Variant = Props.BasementBody;
                t.Stack = (byte)(dead.Chance(0.06) ? 2 : 1);
                t.Pier = (ArchPier)dead.Range(0, 3);
            }
        if (!patch) return;
        const int mid = (BasementPatchLo + BasementPatchHi) / 2;
        b.At(mid, mid).Ceiling = CeilingKind.BasementBulbOn;
        // The Dry Patch: "a little above the rest", and nothing to it. A crate or two, a shelf, a drum round its walls, in its
        // corners and the middles of its sides, clear of the doorways (which are on the node lines)
        (int X, int Z, ArchPier Away)[] spots =
        {
            (BasementPatchLo + 1, BasementPatchLo + 1, ArchPier.South), (BasementPatchHi - 1, BasementPatchLo + 1, ArchPier.West),
            (BasementPatchLo + 1, BasementPatchHi - 1, ArchPier.East), (BasementPatchHi - 1, BasementPatchHi - 1, ArchPier.North),
            (mid, BasementPatchLo + 1, ArchPier.South), (BasementPatchLo + 1, mid, ArchPier.East),
            (mid + 1, BasementPatchHi - 1, ArchPier.North), (BasementPatchHi - 1, mid + 1, ArchPier.West),
        };
        ushort[] things = { 0, Props.BasementShelf, Props.BasementDrum, Props.BasementBody };
        int first = furnish.Range(0, spots.Length - 1);
        for (int k = 0; k < things.Length; k++)
        {
            var (x, z, away) = spots[(first + k * 3) % spots.Length];
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0) continue;
            if (things[k] == Props.BasementBody && !furnish.Chance(0.35)) continue;
            if (things[k] == 0) { t.Stack = (byte)furnish.Range(1, 2); t.Looted = true; }
            else t.Variant = things[k];
            t.Pier = away;
        }
        // Four squat pillars hold the room's ceiling up, on the node lines (the passages come in between them)
        foreach (int px in new[] { BasementNode0 + BasementPitch, BasementNode0 + 2 * BasementPitch - 1 })
            foreach (int pz in new[] { BasementNode0 + BasementPitch, BasementNode0 + 2 * BasementPitch - 1 })
                if (b.At(px, pz).Kind == TileKind.Floor && b.At(px, pz).Variant == 0 && b.At(px, pz).Stack == 0 && b.At(px, pz).Ceiling == CeilingKind.BasementCeiling)
                    SetWall(ref b.At(px, pz), WallPattern.BasementPillar, BaseStyle.Plain);
        // Where somebody lay down to rest, as the man who wrote of the Flood did: a bedroll, a pack left by it
        if (furnish.Chance(0.45))
        {
            int cx = furnish.Chance(0.5) ? BasementPatchLo + 2 : BasementPatchHi - 2, cz = furnish.Chance(0.5) ? BasementPatchLo + 3 : BasementPatchHi - 3;
            ref Tile bed = ref b.At(cx, cz);
            if (bed.Kind == TileKind.Floor && bed.Variant == 0 && bed.Stack == 0)
            {
                bed.Variant = Props.Bedroll;
                bed.Pier = cz < mid ? ArchPier.South : ArchPier.North;
                ref Tile pack = ref b.At(cx + (cx < mid ? 1 : -1), cz);
                if (pack.Kind == TileKind.Floor && pack.Variant == 0 && pack.Stack == 0)
                {
                    pack.Variant = furnish.Chance(0.6) ? Props.Backpack : Props.Flashlight;
                    pack.Pier = ArchPier.North;
                }
            }
        }
        // The elevator in the distance: in about one Dry Patch in two, a dead cage lift in the middle of a wall with no doorway
        if (!furnish.Chance(0.5)) return;
        int side = furnish.Range(0, 3);
        for (int turn = 0; turn < 4; turn++, side = (side + 1) % 4)
        {
            // The wall's two tiles either side of its middle (the doorways are on the node lines, 12 and 20)
            (int X, int Z)[] pair = side switch
            {
                0 => new[] { (BasementPatchLo, mid + 1), (BasementPatchLo, mid) },
                1 => new[] { (mid, BasementPatchLo), (mid + 1, BasementPatchLo) },
                2 => new[] { (BasementPatchHi, mid), (BasementPatchHi, mid + 1) },
                _ => new[] { (mid + 1, BasementPatchHi), (mid, BasementPatchHi) },
            };
            ArchPier faces = side switch { 0 => ArchPier.East, 1 => ArchPier.South, 2 => ArchPier.West, _ => ArchPier.North };
            var (ix, iz) = side switch { 0 => (1, 0), 1 => (0, 1), 2 => (-1, 0), _ => (0, -1) };
            bool ok = true;
            foreach (var (x, z) in pair)
                ok &= b.At(x, z).Kind == TileKind.Wall && b.At(x + ix, z + iz).Kind == TileKind.Floor;
            if (!ok) continue;
            for (int leaf = 0; leaf < 2; leaf++)
            {
                ref Tile t = ref b.At(pair[leaf].X, pair[leaf].Z);
                t.Pattern = WallPattern.BasementLift;
                t.Stack = (byte)leaf;
                t.Pier = faces;
                // (and nothing stands in front of it)
                ref Tile front = ref b.At(pair[leaf].X + ix, pair[leaf].Z + iz);
                front.Variant = 0;
                front.Stack = 0;
            }
            break;
        }
    }

    /// <summary>Makes a flooded tile one of a stair's steps: 2 the upper (level with the dry floor), 1 the lower, climbing toward <paramref name="toward"/>.</summary>
    private static void BasementStep(ref Tile t, byte height, ArchPier toward)
    {
        if (t.Kind != TileKind.Water) return;
        t.Height = height;
        t.Pier = toward;
        t.Pipe = 0;
        t.Ceiling = CeilingKind.BasementCeiling;
    }

    /// <summary>
    /// Which of the level's props (<see cref="Props.BasementFirst"/>-<see cref="Props.BasementLast"/>) people walk through:
    /// the rubble under a crack, the dead, what lies on the floor, and an Escherian stairwell's steps (they climb them).
    /// </summary>
    private static bool BasementWalkThrough(ushort variant) => variant is Props.BasementDebris or Props.BasementBody or Props.BasementJunk or Props.BasementEscher or Props.BasementSump or Props.BasementFallen;

    // ================= Air =================

    /// <summary>The temperature: cold everywhere, colder down in the water, a little less so in the Dry Patch.</summary>
    private float BasementTemperature(int x, int y, int z, int floorY)
    {
        int rel = y - (floorY - WorldGeometry.BasementDrop);
        return BasementZoneAt(x, z) switch
        {
            BasementZone.Flood => rel <= 0 ? 4f : 5f,
            BasementZone.Patch => 9f,
            _ => 8f,
        };
    }

    /// <summary>Reality stability: steady in the Cellar, a slow drain out in the Flood (Level 2's), a little gain in the Dry Patch.</summary>
    private float BasementStability(double x, double y, double z, int floorY, float drift) => BasementZoneAt((int)Math.Floor(x), (int)Math.Floor(z)) switch
    {
        BasementZone.Flood => 0.7f + 0.2f * drift,
        BasementZone.Patch => 1.15f,
        _ => 1f + 0.05f * drift,
    };

    /// <summary>
    /// The bodies of a cell (<see cref="Props.BasementBody"/>), cell-local, with their kind (0 bones, 1 a drowned body, 2 the
    /// drowned man the papers named) and the way they lie: <see cref="Regions.BasementSystem"/> lays one down the first time
    /// anyone comes near.
    /// </summary>
    public List<(int Lx, int Lz, int Kind, ArchPier Pier)> BasementBodies(int mx, int mz)
    {
        var bodies = new List<(int, int, int, ArchPier)>();
        if (LevelAt(mx, mz) != Basement) return bodies;
        Tile[] tiles = CellTiles(mx, mz);
        for (int i = 0; i < tiles.Length; i++)
            if (tiles[i].Variant == Props.BasementBody) bodies.Add((i % MacroSize, i / MacroSize, tiles[i].Stack, tiles[i].Pier));
        return bodies;
    }
}
