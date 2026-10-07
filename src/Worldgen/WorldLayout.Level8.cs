using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 8, "Cave Systems": a sprawling network of natural caves, and the one level where the rock is real. Its
/// geology is Vintage Story's own (granite, limestone, basalt and the rest, with copper, tin, iron, coal, sulfur,
/// saltpeter, quartz and clay) only arranged wrongly: strata out of order, a seam of office carpet between two
/// layers of granite, a coal seam running straight up. Speleothems jut at all angles; almond water pools in the
/// low places, and pools of scalding tar wait in others. It is cold, and light barely carries.
///
/// The caves themselves are carved in 3D by <see cref="WorldGenerator"/>. The layout only holds what is fixed in
/// the plane: the 9th Road, a marked way through islands of stability with M.E.G. markers and lamps along it, the
/// settlements where it crosses itself, and vents in its walls. Everything else is rock to be hollowed out.
///
/// <para>The road runs on a meandering lattice <see cref="RoadGrid"/> blocks apart, but most of the lattice is not
/// there. Every <see cref="L8MainEvery"/>th road runs on unbroken, the long marked ways through; between them the
/// side roads are a tree with a few loops (see <see cref="PlanLatticeTree"/>), so most turnings off the main road
/// end in a blind cave wall. Only where a road reaches the edge of the level is there a way out.</para>
/// </summary>
public sealed partial class WorldLayout
{
    private const int RoadGrid = 48;
    /// <summary>Every this many roads of the lattice is a main road, never broken.</summary>
    private const int L8MainEvery = 4;
    private const ulong SaltL8Road = 0x8C01;
    private const ulong SaltL8Tree = 0x8C04;
    private const ulong SaltL8Camp = 0x8C02;
    private const ulong SaltL8Detail = 0x8C03;

    /// <summary>Distance across the road band, or -1 off the road. Roads meander along a 48-block grid.</summary>
    private int RoadOffsetX(int gx, int gz) => Hashing.Mod(gz - (int)Math.Round(6 * Noise(gx / 40.0, 0.5, SaltL8Road)), RoadGrid);
    private int RoadOffsetZ(int gx, int gz) => Hashing.Mod(gx - (int)Math.Round(6 * Noise(gz / 40.0, 0.5, SaltL8Road + 1)), RoadGrid);

    /// <summary>Which road of the lattice a block's offsets put it beside: the west-east road and the north-south one.</summary>
    private (int Kz, int Kx) RoadLines(int gx, int gz) =>
        (Hashing.FloorDiv(gz - (int)Math.Round(6 * Noise(gx / 40.0, 0.5, SaltL8Road)), RoadGrid),
         Hashing.FloorDiv(gx - (int)Math.Round(6 * Noise(gz / 40.0, 0.5, SaltL8Road + 1)), RoadGrid));

    private PlanCache<System.Collections.Generic.HashSet<(int, int, int)>> l8Trees;

    /// <summary>Whether a stretch of the road lattice is there (see <see cref="PlanLatticeTree"/> for how stretches are named).</summary>
    private bool L8Stretch(int axis, int line, int index)
    {
        if (Hashing.Mod(line, L8MainEvery) == 0) return true;
        int mcx = Hashing.FloorDiv(axis == 0 ? line : index, L8MainEvery), mcz = Hashing.FloorDiv(axis == 0 ? index : line, L8MainEvery);
        // (Near the edge of the level, where the way into the side roads might lie beyond it, every road is there)
        var tree = (l8Trees ??= new PlanCache<System.Collections.Generic.HashSet<(int, int, int)>>(128, PlanL8Tree)).Get(mcx, mcz);
        return tree.Count == 0 || tree.Contains((axis, line, index));
    }

    /// <summary>The side roads between four main ones; empty (meaning all of them) where the block is not wholly Level 8.</summary>
    private System.Collections.Generic.HashSet<(int, int, int)> PlanL8Tree(int mcx, int mcz)
    {
        int span = RoadGrid * L8MainEvery, x0 = mcx * span - RoadGrid, z0 = mcz * span - RoadGrid;
        for (int z = MacroOf(z0); z <= MacroOf(z0 + span + 2 * RoadGrid); z++)
            for (int x = MacroOf(x0); x <= MacroOf(x0 + span + 2 * RoadGrid); x++)
                if (LevelAt(x, z) != 8) return new System.Collections.Generic.HashSet<(int, int, int)>();
        return PlanLatticeTree(mcx, mcz, L8MainEvery, SaltL8Tree, 0.6, 0.15, 0.15);
    }

    private bool L8Crossing(int kx, int kz) => L8Stretch(0, kx, kz) || L8Stretch(0, kx, kz - 1) || L8Stretch(1, kz, kx) || L8Stretch(1, kz, kx - 1);

    /// <summary>Whether a block lies on the 9th Road (in Level 8).</summary>
    public bool IsNinthRoad(int gx, int gz)
    {
        bool alongX = RoadOffsetX(gx, gz) < 3, alongZ = RoadOffsetZ(gx, gz) < 3;
        if (!alongX && !alongZ) return false;
        var (kz, kx) = RoadLines(gx, gz);
        if (alongX && alongZ) return L8Crossing(kx, kz);
        return alongX ? L8Stretch(1, kz, kx) : L8Stretch(0, kx, kz);
    }

    private Edge Level8Edge(int mx, int mz, bool west)
    {
        var edge = new Edge { Pattern = WallPattern.Rock };
        int gx0 = mx * MacroSize, gz0 = mz * MacroSize;
        for (int i = 1; i < MacroSize; i++)
        {
            int gx = west ? gx0 : gx0 + i, gz = west ? gz0 + i : gz0;
            edge.Tiles[i] = IsNinthRoad(gx, gz) || IsCampClearing(gx, gz) ? EdgeTile.Open : EdgeTile.Wall;
        }
        return edge;
    }

    private void BuildLevel8(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (t.Kind != TileKind.Floor) continue;
                int ox = RoadOffsetX(gx, gz), oz = RoadOffsetZ(gx, gz);
                bool road = IsNinthRoad(gx, gz);
                // Settlements where roads cross: a clearing round the crossing
                bool camp = IsCampClearing(gx, gz);
                if (!road && !camp)
                {
                    SetWall(ref t, WallPattern.Rock, BaseStyle.Plain);
                    continue;
                }
                t.Floor = FloorKind.Gravel;
                if (!road) continue;
                // M.E.G. markers every so often on one side of the road, lamps on the other
                bool alongX = ox < 3;
                int along = alongX ? gx : gz, across = alongX ? ox : oz;
                if (across == 0 && Hashing.Mod(along, 24) == 0) { t.Variant = Props.MegMarker; t.Pier = alongX ? ArchPier.South : ArchPier.East; }
                else if (across == 2 && Hashing.Mod(along, 12) == 6) t.Variant = Props.RoadLamp;
            }
        }

        // Settlement furnishings, vents in the walls beside the road, the odd strange formation
        ref Rng rng = ref b.Rng;
        for (int lz = 1; lz < MacroSize - 1; lz++)
        {
            for (int lx = 1; lx < MacroSize - 1; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL8Detail));
                if (t.Kind == TileKind.Wall)
                {
                    bool besideRoad = b.At(lx + 1, lz).Kind == TileKind.Floor || b.At(lx - 1, lz).Kind == TileKind.Floor
                                      || b.At(lx, lz + 1).Kind == TileKind.Floor || b.At(lx, lz - 1).Kind == TileKind.Floor;
                    if (besideRoad && r < 0.018)
                    {
                        // A vent grate, or (more often) Almond Water seeping out of the rock
                        t.Variant = r < 0.006 ? Props.CaveVent : Props.AlmondSeep;
                        t.Pier = b.At(lx, lz - 1).Kind == TileKind.Floor ? ArchPier.North : b.At(lx, lz + 1).Kind == TileKind.Floor ? ArchPier.South
                            : b.At(lx + 1, lz).Kind == TileKind.Floor ? ArchPier.East : ArchPier.West;
                    }
                    continue;
                }
                if (t.Variant != 0 || IsNinthRoad(gx, gz)) continue;
                // In a settlement clearing (off the road itself)
                t.Pier = (ArchPier)rng.Range(0, 3);
                t.Variant = r < 0.05 ? Props.Tent : r < 0.08 ? Props.Bedroll : r < 0.1 ? Props.BurnBarrel : r < 0.12 ? Props.FoldingTable
                    : r < 0.14 ? Props.CardboardBoxes : r < 0.15 ? Props.Lantern : (byte)0;
                if (r > 0.96) t.SupplyBox = true;
                else if (r > 0.94) t.Stack = 2;
            }
        }
    }

    /// <summary>
    /// Whether a block lies in the clearing round a road crossing that has a settlement. Offsets are taken signed,
    /// so the clearing surrounds the crossing, and every block of it agrees on which crossing it belongs to.
    /// </summary>
    private bool IsCampClearing(int gx, int gz)
    {
        int ox = Hashing.Mod(RoadOffsetX(gx, gz) + RoadGrid / 2, RoadGrid) - RoadGrid / 2;
        int oz = Hashing.Mod(RoadOffsetZ(gx, gz) + RoadGrid / 2, RoadGrid) - RoadGrid / 2;
        if (Math.Abs(ox - 1) > 8 || Math.Abs(oz - 1) > 8) return false;
        // The crossing's road lines, numbered along the grid; a settlement only where roads still meet
        int lineX = Hashing.FloorDiv(gx - oz + RoadGrid / 2, RoadGrid), lineZ = Hashing.FloorDiv(gz - ox + RoadGrid / 2, RoadGrid);
        return Hashing.Unit(Hashing.Hash(seed, lineX, lineZ, SaltL8Camp)) < 0.35 && L8Crossing(lineX, lineZ);
    }
}
