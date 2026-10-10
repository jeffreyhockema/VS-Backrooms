using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 10, "Bumper Crop": endless farmland under a flat grey sky that never clears. Wheat (spelt here), rye and
/// flax stand ripe in fields too big to see across, the furrows and the tractor tramlines running off to the
/// horizon; harvested fields lie in stubble with the hay rolled up and left; meadows of long grass and wildflowers
/// lie fallow. Hedgerows with the odd oak, or a strip of rough grass, divide one field from the next. Rutted dirt
/// roads, lined with telegraph poles that carry no wires anywhere, wander between them for kilometres.
///
/// Now and then a farmstead stands by itself: a farmhouse like the ones in the Suburbs, a red barn with hay and
/// stalls, a grain silo, a tool shed, an old tractor and plough in the yard. Fenced paddocks hold livestock; ponds
/// lie in hollows ringed with reeds, and the deepest point of every pond leads somewhere else. The soil is one
/// block deep, and under it the worms.
///
/// Fields are the cells of a jittered grid of sites (<see cref="FieldSpacing"/> apart): each block belongs to the
/// field of the nearest site, so fields are irregular (some two hundred blocks across), and every block can work out its field on its own.
/// </summary>
public sealed partial class WorldLayout
{
    private const int FieldSpacing = 190;
    private const int FarmRoadGrid = 420;
    private const ulong SaltL10Site = 0xA001;
    private const ulong SaltL10Detail = 0xA002;
    private const ulong SaltL10Kind = 0xA003;
    private const ulong SaltL10Road = 0xA004;
    private const ulong SaltL10Edge = 0xA005;

    private enum FarmField { Wheat, Rye, Flax, Stubble, Meadow, Pasture, Farmstead, Lake }

    /// <summary>The site of the field in a grid square: somewhere well inside it, so neighbouring sites are never too close.</summary>
    private (int X, int Z) FieldSite(int i, int j)
    {
        ulong h = Hashing.Hash(seed, i, j, SaltL10Site);
        return (i * FieldSpacing + 25 + (int)(Hashing.Unit(h) * (FieldSpacing - 50)),
                j * FieldSpacing + 25 + (int)(Hashing.Unit(Hashing.Mix(h)) * (FieldSpacing - 50)));
    }

    /// <summary>The field a block belongs to (its site's grid square), and how near it lies to the edge with the next.</summary>
    private (int I, int J, int OtherI, int OtherJ, double EdgeGap) FieldAt(int gx, int gz)
    {
        int ci = Hashing.FloorDiv(gx, FieldSpacing), cj = Hashing.FloorDiv(gz, FieldSpacing);
        double d1 = double.MaxValue, d2 = double.MaxValue;
        int bi = 0, bj = 0, oi = 0, oj = 0;
        for (int j = cj - 1; j <= cj + 1; j++)
            for (int i = ci - 1; i <= ci + 1; i++)
            {
                var (sx, sz) = FieldSite(i, j);
                double d = Math.Sqrt((double)(gx - sx) * (gx - sx) + (double)(gz - sz) * (gz - sz));
                if (d < d1) { d2 = d1; oi = bi; oj = bj; d1 = d; bi = i; bj = j; }
                else if (d < d2) { d2 = d; oi = i; oj = j; }
            }
        return (bi, bj, oi, oj, d2 - d1);
    }

    /// <summary>What a field is. Farmsteads, paddocks and ponds that would not fit wholly inside Level 10 are left as meadow.</summary>
    private FarmField FieldKind(int i, int j)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, i, j, SaltL10Kind));
        FarmField kind = r < 0.30 ? FarmField.Wheat : r < 0.47 ? FarmField.Rye : r < 0.54 ? FarmField.Flax : r < 0.64 ? FarmField.Stubble
            : r < 0.76 ? FarmField.Meadow : r < 0.84 ? FarmField.Pasture : r < 0.93 ? FarmField.Farmstead : FarmField.Lake;
        if (kind is FarmField.Pasture or FarmField.Farmstead or FarmField.Lake)
        {
            var (sx, sz) = FieldSite(i, j);
            if (!AllLevel(10, sx - 34, sz - 34, 69)) return FarmField.Meadow;
        }
        return kind;
    }

    // ---- Roads ----

    private int FarmRoadOffsetX(int gx, int gz) => Hashing.Mod(gz - (int)Math.Round(40 * Noise(gx / 150.0, 0.5, SaltL10Road)), FarmRoadGrid);
    private int FarmRoadOffsetZ(int gx, int gz) => Hashing.Mod(gx - (int)Math.Round(40 * Noise(gz / 150.0, 0.5, SaltL10Road + 1)), FarmRoadGrid);

    /// <summary>How far across a farm road a block lies (0 to 3), or -1 off the roads.</summary>
    private int FarmRoadAt(int gx, int gz)
    {
        int ox = FarmRoadOffsetX(gx, gz), oz = FarmRoadOffsetZ(gx, gz);
        return ox < 4 ? ox : oz < 4 ? oz : -1;
    }

    // ---- Trees, as a pure function of position so crowns agree across cells ----

    /// <summary>Whether a hedgerow runs along this field edge (otherwise it is a strip of rough grass).</summary>
    private bool IsHedgeEdge(int i, int j, int oi, int oj)
    {
        // The same answer from either side of the edge
        (int a, int b, int c, int d) = i < oi || i == oi && j < oj ? (i, j, oi, oj) : (oi, oj, i, j);
        return Hashing.Unit(Hashing.Hash(seed, a * 7919 + b, c * 7919 + d, SaltL10Edge)) < 0.55;
    }

    private bool IsFarmTree(int gx, int gz)
    {
        if (FarmRoadAt(gx, gz) >= 0) return false;
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL10Detail + 9));
        var f = FieldAt(gx, gz);
        if (f.EdgeGap < 2.2) return r < 0.035 && IsHedgeEdge(f.I, f.J, f.OtherI, f.OtherJ);
        FarmField kind = FieldKind(f.I, f.J);
        // The odd oak standing alone out in a meadow or a paddock
        return kind is FarmField.Meadow or FarmField.Pasture && r < 0.0012;
    }

    // ---- Paddocks, ponds and farmsteads, in their site's frame ----

    private (int HalfX, int HalfZ) PaddockSize(int i, int j)
    {
        ulong h = Hashing.Hash(seed, i, j, SaltL10Kind + 1);
        return (16 + (int)(h % 11), 11 + (int)((h >> 8) % 9));
    }

    private (double Rx, double Rz) PondSize(int i, int j)
    {
        ulong h = Hashing.Hash(seed, i, j, SaltL10Kind + 2);
        return (12 + Hashing.Unit(h) * 18, 9 + Hashing.Unit(Hashing.Mix(h)) * 14);
    }

    /// <summary>Whether a column is inside the fence of one of Level 10's paddocks, where the livestock are kept.</summary>
    public bool IsPasture(int gx, int gz)
    {
        if (LevelAt(MacroOf(gx), MacroOf(gz)) != 10) return false;
        var f = FieldAt(gx, gz);
        if (FieldKind(f.I, f.J) != FarmField.Pasture) return false;
        var (sx, sz) = FieldSite(f.I, f.J);
        var (hx, hz) = PaddockSize(f.I, f.J);
        return Math.Abs(gx - sx) < hx && Math.Abs(gz - sz) < hz;
    }

    private void BuildLevel10(Builder b, int mx, int mz)
    {
        var houses = new Dictionary<(int, int), Tile[]>();
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL10Detail));
                t.Floor = FloorKind.Grass;

                // Farm roads, four wide: two strips of tire tracks with grass between, telegraph poles along one side
                int road = FarmRoadAt(gx, gz);
                if (road >= 0)
                {
                    t.Floor = road is 1 or 2 ? FloorKind.Grass : FloorKind.DirtTracks;
                    continue;
                }
                if (FarmRoadOffsetX(gx, gz) == 5 && Hashing.Mod(gx, 32) == 0 || FarmRoadOffsetZ(gx, gz) == 5 && Hashing.Mod(gz, 32) == 0)
                {
                    t.Variant = Props.PowerPole;
                    t.Pier = FarmRoadOffsetX(gx, gz) == 5 ? ArchPier.North : ArchPier.West;
                    continue;
                }

                var f = FieldAt(gx, gz);
                if (IsFarmTree(gx, gz))
                {
                    t.Variant = Props.Tree;
                    continue;
                }
                // The edge between two fields: a hedgerow (with gaps to walk through) or a strip of rough grass
                if (f.EdgeGap < 2.2)
                {
                    // Gaps to walk through here and there along every hedge, whichever way it runs
                    bool gap = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 4), Hashing.FloorDiv(gz, 4), SaltL10Detail + 5)) < 0.12;
                    if (IsHedgeEdge(f.I, f.J, f.OtherI, f.OtherJ) && !gap) SetWall(ref t, WallPattern.Hedge, BaseStyle.Plain);
                    else if (r < 0.5) t.Variant = Props.TallGrass;
                    continue;
                }

                var (sx, sz) = FieldSite(f.I, f.J);
                FieldTile(ref t, FieldKind(f.I, f.J), f.I, f.J, gx - sx, gz - sz, gx, gz, r, houses);
            }
        }

        // Tree crowns spread over the tiles round each trunk, across cell edges too
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                bool inside = lx > 0 && lz > 0 && lx < MacroSize - 1 && lz < MacroSize - 1;
                for (int dz = -1; dz <= 1; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        if ((dx != 0 || dz != 0) && IsFarmTree(gx + dx, gz + dz)
                            && (inside || LevelAt(MacroOf(gx + dx), MacroOf(gz + dz)) == 10))
                            b.At(lx, lz).Overhead = Overheads.Leaves;
                    }
            }

        // Level 3999's way in: now and then a lone arcade at the end of a chain of red-lit windmills (its own salt; WorldLayout.Level3999.Ways.cs)
        if (L3999Entrances) L3999ArcadeOverlay(b, mx, mz);
    }

    /// <summary>One tile of a field, at (du, dv) from its site.</summary>
    private void FieldTile(ref Tile t, FarmField kind, int i, int j, int du, int dv, int gx, int gz, double r,
                           Dictionary<(int, int), Tile[]> houses)
    {
        ulong fh = Hashing.Hash(seed, i, j, SaltL10Kind + 3);
        bool alongX = (fh & 1) == 0; // which way the furrows run
        int across = alongX ? gz : gx;
        switch (kind)
        {
            case FarmField.Wheat:
            case FarmField.Rye:
            case FarmField.Flax:
            {
                t.Floor = FloorKind.Field;
                // A scarecrow near the middle, keeping watch over nothing
                if (du == 3 && dv == -2 && (fh >> 8) % 3 != 0) { t.Variant = Props.Scarecrow; t.Pier = (ArchPier)((fh >> 12) % 4); break; }
                // Furrows every few rows, and the tramlines a tractor once left
                int row = Hashing.Mod(across, 24);
                if (row is 11 or 13 || Hashing.Mod(across, 7) == 3) break;
                t.Variant = Props.Crop;
                t.Stack = (byte)(kind == FarmField.Wheat ? 0 : kind == FarmField.Rye ? 1 : 2);
                break;
            }
            case FarmField.Stubble:
                t.Floor = FloorKind.Stubble;
                // The hay rolled up and left in rows
                if (Hashing.Mod(across, 14) == 6 && Hashing.Mod(alongX ? gx : gz, 9) == 4 && r < 0.75) { t.Variant = Props.HayRoll; t.Pier = alongX ? ArchPier.East : ArchPier.North; }
                break;
            case FarmField.Meadow:
                if (r < 0.006) { t.Variant = Props.BerryBush; t.Stack = (byte)(r * 1000 % 5); }
                else if (r < 0.45) t.Variant = Props.TallGrass;
                else if (r < 0.5) { t.Variant = Props.Flowers; t.Stack = (byte)((r * 1000) % 8); }
                break;
            case FarmField.Pasture:
                PaddockTile(ref t, i, j, du, dv, r);
                break;
            case FarmField.Lake:
                PondTile(ref t, i, j, du, dv, r);
                break;
            case FarmField.Farmstead:
                FarmsteadTile(ref t, i, j, du, dv, gx, gz, r, houses);
                break;
        }
    }

    /// <summary>A fenced paddock round the site (connections N1 E2 S4 W8), a trough and a pump in it, a gap to the south.</summary>
    private void PaddockTile(ref Tile t, int i, int j, int du, int dv, double r)
    {
        var (hx, hz) = PaddockSize(i, j);
        bool inside = Math.Abs(du) <= hx && Math.Abs(dv) <= hz;
        if (!inside) { if (r < 0.3) t.Variant = Props.TallGrass; return; }
        bool edgeX = Math.Abs(du) == hx, edgeZ = Math.Abs(dv) == hz;
        if (edgeX || edgeZ)
        {
            if (dv == hz && Math.Abs(du) <= 1) return; // the way in
            byte mask = 0;
            if (edgeX) mask |= (byte)((dv > -hz ? 1 : 0) | (dv < hz ? 4 : 0));
            if (edgeZ) mask |= (byte)((du > -hx ? 8 : 0) | (du < hx ? 2 : 0));
            if (dv == hz && du == -2) mask &= unchecked((byte)~2); // no rail across the gap
            if (dv == hz && du == 2) mask &= unchecked((byte)~8);
            t.Kind = TileKind.Bars;
            t.Pattern = WallPattern.Fence;
            t.Stack = mask;
            return;
        }
        if (du == 0 && dv == 0) { t.Variant = Props.FeedTrough; t.Pier = ArchPier.North; }
        else if (du == 3 && dv == 0) t.Variant = Props.WaterPump;
        else if (r < 0.06) t.Variant = Props.TallGrass;
    }

    /// <summary>A pond in a hollow, its middle deepest (and leading elsewhere), ringed with reeds; the bank has no worms under it.</summary>
    private void PondTile(ref Tile t, int i, int j, int du, int dv, double r)
    {
        var (rx, rz) = PondSize(i, j);
        double d = (du / rx) * (du / rx) + (dv / rz) * (dv / rz);
        if (d < 1)
        {
            t.Kind = TileKind.Water;
            t.Depth = (byte)(d < 0.12 ? 5 : d < 0.45 ? 3 : 2);
            t.Floor = FloorKind.Field;
            if (d < 0.04) t.Under = Unders.LakeBottom;
        }
        else if (d < 1.6)
        {
            t.Under = Unders.LakeRim;
            if (d < 1.3 && r < 0.4) t.Variant = Props.Reeds;
        }
        else if (r < 0.35) t.Variant = Props.TallGrass;
    }

    /// <summary>
    /// A farmstead round its site: the farmhouse to the north-east, the barn to the west, a silo, a tool shed, a yard
    /// of packed earth with a tractor and a plough, hay stacked by the barn.
    /// </summary>
    private void FarmsteadTile(ref Tile t, int i, int j, int du, int dv, int gx, int gz, double r, Dictionary<(int, int), Tile[]> houses)
    {
        bool yard = du >= -24 && du <= 22 && dv >= -22 && dv <= 16;
        if (!yard)
        {
            t.Floor = FloorKind.Field;
            int row = Hashing.Mod(gz, 24);
            if (row is not (11 or 13) && Hashing.Mod(gz, 7) != 3) { t.Variant = Props.Crop; t.Stack = 0; }
            return;
        }
        // Packed earth worn into the grass where the yard is used most, in patches rather than speckles
        t.Floor = Noise(gx / 6.0, gz / 6.0, SaltL10Detail + 4) - 0.012 * (Math.Abs(du) + Math.Abs(dv)) > -0.35 ? FloorKind.DirtRoad : FloorKind.Grass;

        // The farmhouse: one of the Suburbs' houses, facing south onto the yard
        if (du >= 2 && du < 2 + Lot && dv >= -21 && dv < -21 + Lot)
        {
            if (!houses.TryGetValue((i, j), out Tile[] plan))
            {
                plan = new Tile[Lot * Lot];
                for (int k = 0; k < plan.Length; k++) plan[k].Floor = FloorKind.Grass;
                var rng = new Rng(Hashing.Hash(seed, i, j, SaltL10Kind + 4));
                PlanHouse(plan, Lot, ref rng, farmhouse: true);
                houses[(i, j)] = plan;
            }
            int u = du - 2, v = Lot - 1 - (dv + 21); // mirrored: the front (v = 0) faces south
            Tile src = plan[v * Lot + u];
            if (src.Roof > 0)
            {
                t = src;
                // A car is drawn from its front-left corner, which moves when the plan is mirrored
                if (t.Variant == Props.Car) t.Variant = Props.CarPart;
                else if (t.Variant == Props.CarPart && u > 0 && plan[v * Lot + u - 1].Variant == Props.Car) t.Variant = Props.Car;
                t.Pier = MirrorNS(t.Pier);
                t.Roof = RoofBits.Turned(t.Roof, MirrorNS);
                if (t.Kind == TileKind.Bars) t.Stack = MirrorMask(t.Stack);
                t.Zone = 9; // drawn as a house
                return;
            }
            if (src.Floor == FloorKind.Sidewalk) t.Floor = FloorKind.DirtRoad;
            if (src.Variant is Props.Tree or Props.Shrub or Props.Flowers) { t.Variant = src.Variant; t.Stack = src.Stack; }
        }

        // The barn (its frame: walls at u 4-21, v 6-19, doors to the south)
        int bu = du + 26, bv = dv + 19;
        if (bu >= 4 && bu <= 21 && bv >= 6 && bv <= 19)
        {
            PlanBarnTile(ref t, bu, bv, r, big: true);
            // In some barns, a stretch of the east wall between the stalls isn't quite there. Lean on it and you noclip
            // through, into the Endless City
            if (bu == 21 && bv == 14 && Hashing.Unit(Hashing.Hash(seed, i, j, SaltL10Kind + 5)) < 0.45) t.Under = Unders.Noclip;
            return;
        }
        // A tool shed (walls at u 6-12, v 7-12 of its frame)
        int su = du + 2, sv = dv - 1;
        if (su >= 6 && su <= 12 && sv >= 7 && sv <= 12) { PlanBarnTile(ref t, su, sv, r, big: false); return; }
        // The silo, a round tower
        int cu = du + 12, cv = dv - 8;
        if (cu * cu + cv * cv <= 6) { SetWall(ref t, WallPattern.Silo, BaseStyle.Plain); return; }

        // In the yard: a tractor and a plough, hay stacked by the barn, a pump by the house
        if (du >= 4 && du <= 5 && dv >= 2 && dv <= 4)
        {
            bool anchor = du == 4 && dv == 2;
            t.Variant = anchor ? Props.Tractor : Props.CarPart;
            t.Pier = ArchPier.North;
            t.Stack = 0;
            return;
        }
        if (du == 4 && dv == 7) { t.Variant = Props.Plough; t.Pier = ArchPier.North; return; }
        if (du == 0 && dv == -1) { t.Variant = Props.WaterPump; return; }
        // Bee skeps by the garden, and a vegetable patch beside them
        if (dv == 12 && du is 14 or 16 or 18) { t.Variant = Props.Skep; return; }
        if (dv is >= 7 and <= 10 && du >= 13 && du <= 19)
        {
            t.Floor = FloorKind.Field;
            if (dv % 2 == 1) { t.Variant = Props.Vegetable; t.Stack = (byte)((du + dv) % 6); }
            return;
        }
        if (du >= -6 && du <= -4 && dv >= 2 && dv <= 4) { t.Variant = Props.HayBale; t.Stack = (byte)(1 + (Hashing.Mod(du + dv, 3))); return; }
        if (r < 0.01) t.Variant = Props.HayRoll;
    }

    /// <summary>
    /// A barn (big: walls at u 4-21, v 6-19) or a shed (walls at u 6-12, v 7-12 in its own frame): red or grey
    /// boards, a wide doorway on the south side, hay, stalls and tools inside.
    /// </summary>
    private static void PlanBarnTile(ref Tile t, int u, int v, double r, bool big)
    {
        int u0 = big ? 4 : 6, u1 = big ? 21 : 12, v0 = big ? 6 : 7, v1 = big ? 19 : 12;
        if (u < u0 || u > u1 || v < v0 || v > v1)
        {
            if (big && r < 0.03) t.Variant = Props.HayBale;
            return;
        }
        // A pitched roof, its ridge running north to south
        byte roof = RoofBits.Make(Math.Min(u - u0, u1 - u), u - u0 <= u1 - u ? ArchPier.West : ArchPier.East);
        t.Roof = roof;
        t.Floor = FloorKind.DirtRoad;
        bool wall = u == u0 || u == u1 || v == v0 || v == v1;
        int mid = (u0 + u1) / 2;
        if (wall)
        {
            SetWall(ref t, big ? WallPattern.BarnRed : WallPattern.BarnGrey, BaseStyle.Plain);
            t.Roof = roof;
            if (v == v1 && Math.Abs(u - mid) <= (big ? 1 : 0)) t.Kind = TileKind.Doorway;
            return;
        }
        if (big)
        {
            // Hay stacked along the back, stalls down one side, tools by the door
            if (v == v0 + 1 && u > u0 + 1 && u < u1 - 1) { t.Variant = Props.HayBale; t.Stack = (byte)(r < 0.5 ? 2 : 3); }
            else if (u == u0 + 3 && v > v0 + 2 && v < v1 - 2 && v % 3 != 0)
            {
                // Stall partitions, joined only to each other
                t.Kind = TileKind.Bars;
                t.Pattern = WallPattern.Fence;
                t.Stack = (byte)(((v - 1) % 3 != 0 ? 1 : 0) | ((v + 1) % 3 != 0 ? 4 : 0));
            }
            else if (u == u0 + 1 && v % 3 == 1 && v > v0 + 2) { t.Variant = Props.FeedTrough; t.Pier = ArchPier.East; }
            else if (u == u1 - 1 && v == v1 - 2) { t.Variant = Props.ToolRack; t.Pier = ArchPier.West; }
            else if (u == u1 - 1 && v == v1 - 4) { t.Variant = Props.NailBarrel; }
            else if (u == u1 - 1 && v == v1 - 6 && r < 0.6) { t.Variant = Props.Pallet; }
            else if (u == u1 - 2 && v == v0 + 3) { t.Variant = Props.SeedSacks; }
            else if (u == u1 - 2 && v == v0 + 7) { t.Variant = Props.Quern; } // an old quern, for flour, salt and lime
        }
        else
        {
            if (u == u0 + 1 && v == v0 + 1) { t.Variant = Props.ToolRack; t.Pier = ArchPier.South; }
            else if (u == u1 - 1 && v == v0 + 1) t.Variant = Props.NailBarrel;
            else if (u == u0 + 1 && v == v1 - 1) t.Variant = Props.SeedSacks;
            else if (u == u1 - 1 && v == v1 - 1 && r < 0.5) { t.Variant = Props.HayBale; t.Stack = 1; }
        }
    }
}
