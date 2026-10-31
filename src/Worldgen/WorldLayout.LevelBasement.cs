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
        SaltBasementFinds = 0x220A, SaltBasementDoor = 0x220B;

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
    private const double BasementCrackShare = 0.4, BasementEscherShare = 0.18, BasementCharnelShare = 0.14;

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

    /// <summary>What a Cellar room is: a finished room of the house (carpet, panelling, cast-offs), a utility room (bare concrete, a boiler), a store room.</summary>
    private enum BasementRoomKind : byte { Finished, Utility, Store }

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
        var rooms = new List<(int X0, int Z0, int X1, int Z1)>();
        var doorRng = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementDoor));
        BasementSplit(b, ref rng, ref doorRng, Solid, 1, 1, MacroSize - 1, MacroSize - 1, rooms);

        // A landing inside every gap in the cell's sides, so no wall of the rooms ends across one
        for (int s = 0; s < 4; s++)
        {
            if (!sides[s].Ours) continue;
            for (int i = 1; i < MacroSize; i++)
            {
                if (!InGap(sides[s].Gaps, i)) continue;
                var (x, z, dx, dz) = BasementSideTile(s, i);
                for (int k = s < 2 ? 1 : 0; k <= (s < 2 ? 2 : 1); k++) BasementClear(ref b.At(x + dx * k, z + dz * k));
            }
        }

        // The cell's one room of each special kind (by hash): the crack someone fell through, an Escherian stairwell, a
        // room of the dead. The crack and the stairwell want the room's middle, so they take big rooms; the dead keep to a small one
        var special = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementSpecial));
        bool wantCrack = special.Chance(BasementCrackShare), wantEscher = special.Chance(BasementEscherShare), wantCharnel = special.Chance(BasementCharnelShare);
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

        var furnish = new Rng(Hashing.Hash(seed, mx, mz, SaltBasementFurnish));
        bool Open(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z));
        for (int k = 0; k < rooms.Count; k++)
        {
            var (x0, z0, x1, z1) = rooms[k];
            int w = x1 - x0 + 1, h = z1 - z0 + 1;
            double roll = furnish.NextDouble();
            BasementRoomKind kind = k == charnelRoom ? BasementRoomKind.Store
                : roll < 0.45 && w * h >= 20 ? BasementRoomKind.Finished : roll < 0.8 ? BasementRoomKind.Utility : BasementRoomKind.Store;
            FloorKind floor = kind == BasementRoomKind.Finished
                ? (furnish.Chance(0.85) ? (furnish.Chance(0.55) ? FloorKind.BasementCarpet : FloorKind.BasementCarpetWorn) : FloorKind.BasementFloor)
                : furnish.Chance(kind == BasementRoomKind.Utility ? 0.35 : 0.2) ? FloorKind.BasementDamp : FloorKind.BasementFloor;
            bool joists = kind == BasementRoomKind.Finished && furnish.Chance(0.6);
            for (int z = z0; z <= z1; z++)
                for (int x = x0; x <= x1; x++)
                {
                    ref Tile t = ref b.At(x, z);
                    if (t.Kind != TileKind.Floor) continue;
                    t.Floor = floor;
                    if (joists) t.Ceiling = CeilingKind.BasementJoists;
                    else if (furnish.Chance(floor == FloorKind.BasementDamp ? 0.25 : 0.08)) t.Ceiling = CeilingKind.BasementStained;
                }
            int cx = x0 + w / 2, cz = z0 + h / 2;
            bool middleTaken = false;
            if (k == crackRoom) { BasementCrack(b, ref furnish, x0, z0, x1, z1, cx, cz); middleTaken = true; }
            else if (k == escherRoom) { BasementTowerAt(b, cx - 2, cz - 2); middleTaken = true; }
            // A squat concrete pillar holding up the middle of a big room (the bulb then hangs beside it)
            bool pillar = !middleTaken && kind != BasementRoomKind.Finished && w >= 9 && h >= 9 && furnish.Chance(0.6) && b.At(cx, cz).Kind == TileKind.Floor;
            if (pillar) SetWall(ref b.At(cx, cz), WallPattern.BasementPillar, BaseStyle.Plain);
            // A bulb in about half the rooms (beside the pillar; off to the side of a crack or a stairwell)
            if (furnish.Chance(k == crackRoom ? 0.3 : kind == BasementRoomKind.Finished ? 0.55 : 0.45))
            {
                int lx = middleTaken ? x0 + 1 : pillar ? cx + 1 : cx, lz = middleTaken ? z0 + 1 : cz;
                ref Tile lamp = ref b.At(lx, lz);
                if (lamp.Kind == TileKind.Floor && lamp.Ceiling != CeilingKind.BasementOpen)
                {
                    double r = furnish.NextDouble();
                    lamp.Ceiling = r < 0.2 ? CeilingKind.BasementBulbOff : r < 0.5 ? CeilingKind.BasementBulbFlicker : CeilingKind.BasementBulbOn;
                }
            }
            if (k == charnelRoom) BasementCharnel(b, ref furnish, mx, mz, x0, z0, x1, z1, Solid, Open);
            else BasementFurnishRoom(b, ref furnish, kind, x0, z0, x1, z1, Solid, Open);
            // Wires that serve no purpose, hanging from the ceiling here and there
            if (furnish.Chance(0.3))
            {
                int x = furnish.Range(x0, x1), z = furnish.Range(z0, z1);
                ref Tile t = ref b.At(x, z);
                if (t.Kind == TileKind.Floor && t.Ceiling is CeilingKind.BasementCeiling or CeilingKind.BasementStained or CeilingKind.BasementJoists && t.Overhead == 0)
                    t.Overhead = Overheads.BasementWire;
            }
        }
        BasementFinds(b, mx, mz, rooms, Solid, Open);
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

    /// <summary>Things against a room's walls, by its kind, never where they would cut a way off nor beside the cell's edges.</summary>
    private static void BasementFurnishRoom(Builder b, ref Rng rng, BasementRoomKind kind, int x0, int z0, int x1, int z1,
        Func<int, int, bool> solid, Func<int, int, bool> open)
    {
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        int things = rng.Range(kind == BasementRoomKind.Utility ? 0 : 1, Math.Min(kind == BasementRoomKind.Utility ? 4 : 5, Math.Max(1, w * h / 25)));
        for (int n = 0, tries = 0; n < things && tries < 24; tries++)
        {
            int x = rng.Range(x0, x1), z = rng.Range(z0, z1);
            if (x < 2 || z < 2 || x > MacroSize - 3 || z > MacroSize - 3) continue;
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0 || t.Detail != 0 || t.Ceiling == CeilingKind.BasementOpen
                || t.Ceiling is CeilingKind.BasementBulbOn or CeilingKind.BasementBulbOff or CeilingKind.BasementBulbFlicker) continue;
            ArchPier? away = solid(x - 1, z) ? ArchPier.East : solid(x + 1, z) ? ArchPier.West : solid(x, z - 1) ? ArchPier.South : solid(x, z + 1) ? ArchPier.North : null;
            if (away == null || !SafeToBlock(open, x, z)) continue;
            double roll = rng.NextDouble();
            switch (kind)
            {
                case BasementRoomKind.Utility:
                    // Old crates, gone through long ago, a boiler, an oil drum, a shelf, a cabinet
                    if (roll < 0.4) { t.Stack = (byte)rng.Range(1, 2); t.Looted = rng.Chance(0.8); }
                    else if (roll < 0.55) t.Variant = Props.BasementBoiler;
                    else if (roll < 0.7) t.Variant = Props.BasementDrum;
                    else if (roll < 0.85) t.Variant = Props.BasementShelf;
                    else t.Variant = Props.BasementCabinet;
                    break;
                case BasementRoomKind.Finished:
                    // What a family put down in the basement and never came back for
                    if (roll < 0.14) t.Variant = Props.CoffeeTable;
                    else if (roll < 0.26) t.Variant = Props.Tv;
                    else if (roll < 0.38) t.Variant = Props.ToyBox;
                    else if (roll < 0.5) { t.Variant = Props.Laundry; t.Stack = (byte)rng.Range(0, 1); }
                    else if (roll < 0.6) t.Variant = Props.Radiator;
                    else if (roll < 0.7) t.Variant = Props.Icebox;
                    else if (roll < 0.8) t.Variant = Props.RotaryPhone;
                    else if (roll < 0.9) t.Variant = Props.CardboardBoxes;
                    else t.Variant = Props.ChairStack;
                    break;
                default:
                    // Boxes, a pile of old furniture, a suitcase, stacked chairs
                    if (roll < 0.35) t.Variant = Props.CardboardBoxes;
                    else if (roll < 0.55) { t.Variant = Props.FurniturePile; t.Stack = (byte)rng.Range(0, 3); }
                    else if (roll < 0.7) t.Variant = Props.Suitcase;
                    else if (roll < 0.85) t.Variant = Props.ChairStack;
                    else { t.Stack = 1; t.Looted = true; }
                    break;
            }
            t.Pier = away.Value;
            n++;
        }
        // Out of place: a caution sign or a cone in a room with nothing wet in it, a cable run across the floor
        if (rng.Chance(0.1))
        {
            int x = rng.Range(x0, x1), z = rng.Range(z0, z1);
            ref Tile t = ref b.At(x, z);
            if (x >= 2 && z >= 2 && x <= MacroSize - 3 && z <= MacroSize - 3 && t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0
                && t.Detail == 0 && t.Ceiling != CeilingKind.BasementOpen && SafeToBlock(open, x, z))
            {
                t.Variant = rng.Chance(0.6) ? Props.WetFloorSign : Props.TrafficCone;
                t.Pier = (ArchPier)rng.Range(0, 3);
            }
        }
        if (rng.Chance(0.12))
        {
            int x = rng.Range(x0, x1), z = rng.Range(z0, z1);
            ref Tile t = ref b.At(x, z);
            if (t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && t.Detail == 0)
            {
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
        if (rooms.Count > 0 && rng.Chance(0.2))
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
        if (t.Kind is TileKind.Wall or TileKind.Doorway && t.Pattern is WallPattern.BasementCinder or WallPattern.BasementStained or WallPattern.BasementPanel)
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
    /// every room can be reached from every other through a door that opens. A wall may not end against a door.
    /// </summary>
    private static void BasementSplit(Builder b, ref Rng rng, ref Rng doors, Func<int, int, bool> solid, int x0, int z0, int x1, int z1,
        List<(int, int, int, int)> rooms)
    {
        const int minRoom = 5;
        int w = x1 - x0 + 1, h = z1 - z0 + 1, area = w * h;
        bool canX = w >= 2 * minRoom + 1, canZ = h >= 2 * minRoom + 1;
        double stop = area <= 80 ? 1 : area <= 160 ? 0.75 : area <= 300 ? 0.45 : 0;
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
                // A door: shut, or standing open; the second one in a wall now and then swollen shut in its frame
                t.Kind = TileKind.Doorway;
                t.Variant = Props.BasementDoor;
                t.Floor = FloorKind.BasementFloor;
                double state = doors.NextDouble();
                int st = k == gap2 && state < 0.3 ? 2 : state < 0.7 ? 0 : 1;
                t.Stack = (byte)(st | (doors.Chance(0.5) ? 4 : 0));
                bool flip = doors.Chance(0.5);
                t.Pier = splitX ? (flip ? ArchPier.East : ArchPier.West) : (flip ? ArchPier.South : ArchPier.North);
            }
            if (splitX)
            {
                BasementSplit(b, ref rng, ref doors, solid, x0, z0, x0 + s - 1, z1, rooms);
                BasementSplit(b, ref rng, ref doors, solid, x0 + s + 1, z0, x1, z1, rooms);
            }
            else
            {
                BasementSplit(b, ref rng, ref doors, solid, x0, z0, x1, z0 + s - 1, rooms);
                BasementSplit(b, ref rng, ref doors, solid, x0, z0 + s + 1, x1, z1, rooms);
            }
            return;
        }
        rooms.Add((x0, z0, x1, z1));
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
                if (patch && InPatch(i, j) || degree[j * n + i] != 1 || stubbed[j * n + i] || !dead.Chance(0.3)) continue;
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
    private static bool BasementWalkThrough(ushort variant) => variant is Props.BasementDebris or Props.BasementBody or Props.BasementJunk or Props.BasementEscher;

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
