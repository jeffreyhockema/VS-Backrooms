using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 37, "Sublimity": the Poolrooms. An expansive complex of rooms and corridors of white ceramic tile, flooded
/// with lukewarm water, every tile identical and undamaged. The rooms are strict in design and senseless in purpose:
/// far too many pillars, pools far too large to be pools, open water with no ledge to climb out onto, staircases that
/// go straight down into deep dark water. There are no lamps. Light comes through tall slits from somewhere you can
/// never see, and leaves the far corners in complete darkness. Nothing lives here, and no one has ever met anyone.
///
/// Kept as level 12 (<see cref="Poolrooms"/>) and shown as 37. Like the city it is not a ring: it lies far out to the
/// west, a region you can only noclip into. Its water lies <see cref="WorldGeometry.PoolDrop"/> blocks below the other
/// levels' floor, so its domes have room to rise and its pits to fall.
///
/// The level is planned in blocks of <see cref="PoolBlock"/> square (three cells). Wandering flooded galleries run
/// along the lines between blocks, so they go on for kilometres; inside each block a few rooms (rotundas, natatoriums,
/// pillar halls, arch-ring tunnels, stair pits, slit halls, the odd dry corridor) open off the galleries by short
/// corridors, and now and then by a swim through a hole under the water.
///
/// Heights: a floor tile's <see cref="Tile.Depth"/> is how deep the water stands over it (0 is a dry deck level with
/// the water); its <see cref="Tile.Height"/> is how high above the water its ceiling is. A wall's Height is the top of
/// the slit of light in it, if it has one.
///
/// About one block in twenty, far out, is the Sanguine Reservoir (Level 37.1): the slits stop, the water is red, and
/// red sprouts on the pool floors are all the light there is.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltPoolShape = 0x3701, SaltPoolBlock = 0x3702, SaltPoolGallery = 0x3703, SaltPoolLight = 0x3704,
        SaltPoolReservoir = 0x3705, SaltPoolDeep = 0x3706;

    /// <summary>On a Level 37 floor tile's <see cref="Tile.Detail"/>: out of reach of any slit's light.</summary>
    public const byte PoolDark = 1;

    /// <summary>Size of the blocks Level 37 is planned in, between the lines of its galleries.</summary>
    public const int PoolBlock = 96;

    /// <summary>How far a gallery wanders either side of its line, and how high its ceiling is.</summary>
    private const int GalleryWander = 5, GalleryHeight = 7;

    // ================= Where the Poolrooms are =================

    /// <summary>The Poolrooms' centre, in macro cells: as far out to the west as the city is to the east.</summary>
    private int PoolCentreX => spawnMacroX - Math.Max(800, spawnMacroX / 4);
    private int PoolCentreZ => spawnMacroZ;

    /// <summary>The Poolrooms' radius in macro cells: a third of the city's, still endless to anyone in it.</summary>
    private int PoolRadius => Math.Max(80, spawnMacroX / 20);

    /// <summary>The block the plans count from.</summary>
    public int PoolOriginX => PoolCentreX * MacroSize;
    public int PoolOriginZ => PoolCentreZ * MacroSize;

    private bool InPoolrooms(double mx, double mz)
    {
        double dx = mx - PoolCentreX, dz = mz - PoolCentreZ;
        double r = Math.Sqrt(dx * dx + dz * dz);
        if (r > PoolRadius * 1.2) return false;
        return r * (1 + 0.08 * Fbm(mx / 40.0, mz / 40.0, SaltPoolShape)) < PoolRadius;
    }

    /// <summary>Whether a square of the world (block coordinates) might reach into the Poolrooms.</summary>
    public bool MayReachPoolrooms(int x0, int z0, int size)
    {
        double cx = (x0 + size / 2.0) / MacroSize - PoolCentreX, cz = (z0 + size / 2.0) / MacroSize - PoolCentreZ;
        return Math.Sqrt(cx * cx + cz * cz) < PoolRadius * 1.2 + size / (double)MacroSize;
    }

    /// <summary>A place near the middle of the Poolrooms to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) PoolArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, radius = Math.Sqrt(Hashing.Unit(Hashing.Mix(h))) * PoolRadius * 0.4;
        return (PoolCentreX + (int)Math.Round(Math.Cos(angle) * radius), PoolCentreZ + (int)Math.Round(Math.Sin(angle) * radius));
    }

    /// <summary>Arriving in the Poolrooms: on a deck or in the shallows, in the light, never in the Reservoir.</summary>
    private static bool IsPoolArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Depth <= 1 && t.Zone == 0 && t.Floor != FloorKind.OfficeCarpet;

    /// <summary>Which plan block a block position lies in.</summary>
    private (int Bi, int Bj) PoolBlockOf(int gx, int gz) =>
        (Hashing.FloorDiv(gx - PoolOriginX, PoolBlock), Hashing.FloorDiv(gz - PoolOriginZ, PoolBlock));

    /// <summary>
    /// Whether a plan block is part of the Sanguine Reservoir, Level 37.1: one block in twenty, and only past the
    /// first three fifths of the way out.
    /// </summary>
    private bool IsReservoirBlock(int bi, int bj)
    {
        double cx = (PoolOriginX + bi * PoolBlock + PoolBlock / 2.0) / MacroSize - PoolCentreX;
        double cz = (PoolOriginZ + bj * PoolBlock + PoolBlock / 2.0) / MacroSize - PoolCentreZ;
        if (cx * cx + cz * cz < 0.36 * PoolRadius * PoolRadius) return false;
        return Hashing.Unit(Hashing.Hash(seed, bi, bj, SaltPoolReservoir)) < 0.05;
    }

    /// <summary>Whether a Level 37 cell lies in the Sanguine Reservoir.</summary>
    public bool IsReservoir(int mx, int mz)
    {
        if (LevelAt(mx, mz) != Poolrooms) return false;
        var (bi, bj) = PoolBlockOf(mx * MacroSize + MacroSize / 2, mz * MacroSize + MacroSize / 2);
        return IsReservoirBlock(bi, bj);
    }

    /// <summary>Whether a block position lies in the Sanguine Reservoir.</summary>
    public bool IsReservoirAt(int gx, int gz)
    {
        var (bi, bj) = PoolBlockOf(gx, gz);
        return IsReservoirBlock(bi, bj);
    }

    /// <summary>
    /// The middle of the nearest block of the Sanguine Reservoir within a radius of a position, if any: where its
    /// chanting is heard from.
    /// </summary>
    public (int X, int Z)? NearestReservoir(int gx, int gz, int radius)
    {
        var (bi, bj) = PoolBlockOf(gx, gz);
        int reach = radius / PoolBlock + 1;
        (int X, int Z)? best = null;
        long bestD = (long)radius * radius;
        for (int dj = -reach; dj <= reach; dj++)
            for (int di = -reach; di <= reach; di++)
            {
                if (!IsReservoirBlock(bi + di, bj + dj)) continue;
                int x = PoolOriginX + (bi + di) * PoolBlock + PoolBlock / 2, z = PoolOriginZ + (bj + dj) * PoolBlock + PoolBlock / 2;
                long d = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                if (d <= bestD) { bestD = d; best = (x, z); }
            }
        return best;
    }

    // ================= Cells =================

    private void BuildLevel37(Builder b, int mx, int mz)
    {
        // The Poolrooms' edge: tile, solid, all the way round, like any other wall
        bool rim = false;
        for (int dz = -1; dz <= 1 && !rim; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Poolrooms) { rim = true; break; }

        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (rim)
                {
                    t = PoolWall();
                    continue;
                }
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                var (bi, bj) = PoolBlockOf(gx, gz);
                t = PoolPlan(bi, bj)[(gz - PoolOriginZ - bj * PoolBlock) * PoolBlock + gx - PoolOriginX - bi * PoolBlock];
            }
    }

    private static Tile PoolWall() => new() { Kind = TileKind.Wall, Pattern = WallPattern.PoolTile };

    // ================= Galleries =================

    /// <summary>
    /// How far a gallery's middle lies off its line at a point along it: it wanders, so the long halls curve. Each
    /// line wanders in its own way.
    /// </summary>
    private int GalleryOffset(int axis, int line, int along)
    {
        ulong h = Hashing.Hash(seed, axis, line, SaltPoolGallery);
        double phase = Hashing.Unit(h) * Math.PI * 2, amplitude = 0.4 + 0.6 * Hashing.Unit(Hashing.Mix(h));
        double period = 15 + 10 * Hashing.Unit(Hashing.Mix(Hashing.Mix(h)));
        return (int)Math.Round(GalleryWander * amplitude * Math.Sin(along / period + phase));
    }

    /// <summary>
    /// Whether a block position lies in a gallery, and if so which way it runs (0: west-east, 1: north-south, 2: where
    /// two cross). A gallery is six wide round its wandering middle, and always takes in the two rows either side of
    /// its line, so the corridors that run up to the line from both sides always reach it.
    /// </summary>
    private int GalleryAt(int gx, int gz)
    {
        int ux = gx - PoolOriginX, uz = gz - PoolOriginZ;
        bool InBand(int across, int along, int axis)
        {
            int line = (int)Math.Round(across / (double)PoolBlock);
            int off = across - line * PoolBlock;
            int mid = GalleryOffset(axis, line, along);
            return off >= Math.Min(mid - 3, -1) && off <= Math.Max(mid + 2, 0);
        }
        bool we = InBand(uz, ux, 0), ns = InBand(ux, uz, 1);
        return we && ns ? 2 : we ? 0 : ns ? 1 : -1;
    }

    /// <summary>The offset of a gallery tile from the middle of its band (for the pillars down the middle).</summary>
    private int GalleryAcross(int gx, int gz, int axis)
    {
        int across = axis == 0 ? gz - PoolOriginZ : gx - PoolOriginX, along = axis == 0 ? gx - PoolOriginX : gz - PoolOriginZ;
        int line = (int)Math.Round(across / (double)PoolBlock);
        return across - line * PoolBlock - GalleryOffset(axis, line, along);
    }

    /// <summary>A stretch of gallery (48 blocks of it) is lit or dark as a whole, and now and then deep enough to swim.</summary>
    private (bool Lit, bool Deep) GalleryStretch(int gx, int gz, int axis)
    {
        int along = axis == 0 ? gx - PoolOriginX : gz - PoolOriginZ, across = axis == 0 ? gz - PoolOriginZ : gx - PoolOriginX;
        int line = (int)Math.Round(across / (double)PoolBlock);
        ulong h = Hashing.Hash(seed, line * 2 + axis, Hashing.FloorDiv(along, 48), SaltPoolLight);
        var (bi, bj) = PoolBlockOf(gx, gz);
        double lit = IsReservoirBlock(bi, bj) ? 0 : NearReservoir(bi, bj) ? 0.35 : 0.72;
        return (Hashing.Unit(h) < lit, Hashing.Unit(Hashing.Mix(h)) < 0.1);
    }

    private bool NearReservoir(int bi, int bj)
    {
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
                if ((di != 0 || dj != 0) && IsReservoirBlock(bi + di, bj + dj)) return true;
        return false;
    }

    // ================= Block plans =================

    private PlanCache<Tile[]> poolPlans;

    private Tile[] PoolPlan(int bi, int bj) => (poolPlans ??= new PlanCache<Tile[]>(32, PlanPoolBlock)).Get(bi, bj);

    private enum PoolSpace { Rotunda, Natatorium, PillarHall, ArchTunnel, StairPit, SlitHall, DryCorridor, PoolRoom, Basin, FloodedHall, Solid, Serpentine }

    /// <summary>One room of a block plan: what it is, the box it fills, and the way it faces (toward the galleries it opens on).</summary>
    private sealed record PoolRoom(PoolSpace Kind, int U0, int V0, int U1, int V1);

    /// <summary>Helpers over one block's tiles while it is planned.</summary>
    private sealed class PoolPlanner
    {
        public readonly Tile[] Tiles = new Tile[PoolBlock * PoolBlock];
        public readonly bool[] Reserved = new bool[PoolBlock * PoolBlock];
        /// <summary>Which room carved each floor tile (1-based), so corridors know when they have left their own.</summary>
        public readonly byte[] Owner = new byte[PoolBlock * PoolBlock];
        public Rng Rng;
        public bool Reservoir, Dim;

        public static bool In(int u, int v) => u >= 0 && v >= 0 && u < PoolBlock && v < PoolBlock;
        public ref Tile At(int u, int v) => ref Tiles[v * PoolBlock + u];
        public bool IsFloor(int u, int v) => In(u, v) && At(u, v).Kind == TileKind.Floor;

        public void Floor(int u, int v, int depth, int height, byte owner, FloorKind kind = FloorKind.PoolTile)
        {
            if (!In(u, v)) return;
            ref Tile t = ref At(u, v);
            t = new Tile { Kind = TileKind.Floor, Floor = kind, Depth = (byte)Math.Clamp(depth, 0, WorldGeometry.PoolPitDepth), Height = (byte)Math.Clamp(height, 3, 15), Pattern = WallPattern.PoolTile };
            Owner[v * PoolBlock + u] = owner;
        }

        public void Wall(int u, int v)
        {
            if (!In(u, v)) return;
            At(u, v) = PoolWall();
            Owner[v * PoolBlock + u] = 0;
        }

        /// <summary>A slit of light (or a glowing arch) in a wall tile, facing the floor at <paramref name="pier"/>.</summary>
        public void Slit(int u, int v, ArchPier pier, int top, byte kind = PoolWalls.Slit)
        {
            if (!In(u, v) || Reservoir) return;
            ref Tile t = ref At(u, v);
            if (t.Kind != TileKind.Wall) return;
            t.Variant = kind;
            t.Pier = pier;
            t.Height = (byte)Math.Clamp(top, 2, 12);
        }
    }

    private static readonly (int Du, int Dv, ArchPier Toward)[] PoolSteps =
        { (0, -1, ArchPier.North), (1, 0, ArchPier.East), (0, 1, ArchPier.South), (-1, 0, ArchPier.West) };

    private static (int Du, int Dv) StepOf(ArchPier p) => p switch
    {
        ArchPier.North => (0, -1),
        ArchPier.South => (0, 1),
        ArchPier.East => (1, 0),
        _ => (-1, 0),
    };

    private static ArchPier Opposite37(ArchPier p) => p switch
    {
        ArchPier.North => ArchPier.South,
        ArchPier.South => ArchPier.North,
        ArchPier.East => ArchPier.West,
        _ => ArchPier.East,
    };

    private Tile[] PlanPoolBlock(int bi, int bj)
    {
        var p = new PoolPlanner
        {
            Rng = new Rng(Hashing.Hash(seed, bi, bj, SaltPoolBlock)),
            Reservoir = IsReservoirBlock(bi, bj),
            Dim = NearReservoir(bi, bj),
        };
        for (int i = 0; i < p.Tiles.Length; i++) p.Tiles[i] = PoolWall();
        int x0 = PoolOriginX + bi * PoolBlock, z0 = PoolOriginZ + bj * PoolBlock;

        PlanGalleries(p, x0, z0);

        // Three by three squares, each a room filling it (a natatorium or a long tunnel takes two); halls on the
        // lattice between them; and every room opens onto whatever lies beyond each of its sides
        List<PoolRoom> rooms = PlanPoolSquares(p);
        PlanPoolHalls(p, x0, z0);
        for (int r = 0; r < rooms.Count; r++) OpenPoolRoom(p, rooms[r], (byte)(r + 1));

        LightGalleries(p, x0, z0);
        PlaceCoping(p);
        PlacePoolDoors(p);
        PlacePoolLeftovers(p);
        if (p.Reservoir) MakeReservoir(p);
        return p.Tiles;
    }

    private static PoolSpace PickPoolSpace(ref Rng rng)
    {
        double r = rng.NextDouble();
        return r < 0.15 ? PoolSpace.Rotunda : r < 0.26 ? PoolSpace.Natatorium : r < 0.36 ? PoolSpace.PillarHall
            : r < 0.45 ? PoolSpace.ArchTunnel : r < 0.54 ? PoolSpace.StairPit : r < 0.60 ? PoolSpace.SlitHall
            : r < 0.72 ? PoolSpace.Serpentine : r < 0.82 ? PoolSpace.PoolRoom : r < 0.88 ? PoolSpace.Basin : r < 0.96 ? PoolSpace.FloodedHall : PoolSpace.Solid;
    }

    /// <summary>The three squares across a block between its galleries and inner halls: where each starts and ends.</summary>
    private static readonly int[] SquareLo = { 9, 35, 67 }, SquareHi = { 29, 61, 86 };

    /// <summary>
    /// Puts a room in every square of the block. A natatorium or an arch-ring tunnel takes in the next square too (and
    /// the hall between), if it is free; a dry corridor to the offices takes the first square, in a block in four.
    /// </summary>
    private List<PoolRoom> PlanPoolSquares(PoolPlanner p)
    {
        var rooms = new List<PoolRoom>();
        var used = new bool[3, 3];
        bool dry = p.Rng.Chance(0.25);
        for (int j = 0; j < 3; j++)
            for (int i = 0; i < 3; i++)
            {
                if (used[i, j]) continue;
                used[i, j] = true;
                int u0 = SquareLo[i] + 1, v0 = SquareLo[j] + 1, u1 = SquareHi[i] - 1, v1 = SquareHi[j] - 1;
                PoolSpace kind = dry ? PoolSpace.DryCorridor : PickPoolSpace(ref p.Rng);
                dry = false;
                if (kind == PoolSpace.Solid) continue;
                bool alongZ = v1 - v0 > u1 - u0;
                if (kind is PoolSpace.Natatorium or PoolSpace.ArchTunnel or PoolSpace.DryCorridor)
                {
                    // Take in the square to the east or the south as well, if it is free
                    bool east = i < 2 && !used[i + 1, j], south = j < 2 && !used[i, j + 1];
                    if (east && (!south || p.Rng.Chance(0.5))) { used[i + 1, j] = true; u1 = SquareHi[i + 1] - 1; alongZ = false; }
                    else if (south) { used[i, j + 1] = true; v1 = SquareHi[j + 1] - 1; alongZ = true; }
                    else if (kind == PoolSpace.Natatorium) kind = PoolSpace.PoolRoom;
                }
                int cu = (u0 + u1) / 2, cv = (v0 + v1) / 2;
                switch (kind)
                {
                    case PoolSpace.Rotunda:
                    {
                        // A square box round the circle, as big as the square allows
                        int half = (Math.Min(u1 - u0, v1 - v0) + 1) / 2;
                        (u0, u1, v0, v1) = (cu - half, cu + half, cv - half, cv + half);
                        break;
                    }
                    case PoolSpace.ArchTunnel:
                        if (alongZ) (u0, u1) = (cu - 3, cu + 2); else (v0, v1) = (cv - 3, cv + 2);
                        break;
                    case PoolSpace.DryCorridor:
                        if (alongZ) (u0, u1) = (cu - 2, cu + 2); else (v0, v1) = (cv - 2, cv + 2);
                        break;
                    case PoolSpace.SlitHall:
                        if (alongZ) (u0, u1) = (cu - 3, cu + 3); else (v0, v1) = (cv - 3, cv + 3);
                        break;
                    case PoolSpace.StairPit:
                    {
                        // Steps down along the square's length, the pit filling most of it
                        int half = Math.Min(5, (Math.Min(u1 - u0, v1 - v0) + 1) / 2);
                        if (alongZ) (u0, u1) = (cu - half, cu + half); else (v0, v1) = (cv - half, cv + half);
                        break;
                    }
                }
                var room = new PoolRoom(kind, u0, v0, u1, v1);
                byte o = (byte)(rooms.Count + 1);
                switch (kind)
                {
                    case PoolSpace.Rotunda: CarveRotunda(p, room, o); break;
                    case PoolSpace.Natatorium: CarveNatatorium(p, room, o); break;
                    case PoolSpace.PillarHall: CarvePillarHall(p, room, o); break;
                    case PoolSpace.ArchTunnel: CarveArchTunnel(p, room, o); break;
                    case PoolSpace.StairPit: CarveStairPit(p, room, o); break;
                    case PoolSpace.SlitHall: CarveSlitHall(p, room, o); break;
                    case PoolSpace.DryCorridor: CarveDryCorridor(p, room, o); break;
                    case PoolSpace.Serpentine: CarveSerpentine(p, room, o); break;
                    default: CarveFiller(p, room, o); break;
                }
                rooms.Add(room);
            }
        return rooms;
    }

    /// <summary>The galleries crossing this block: wading water under a seven-high ceiling, pillars down the middle, rails and slits on their walls.</summary>
    private void PlanGalleries(PoolPlanner p, int x0, int z0)
    {
        for (int v = 0; v < PoolBlock; v++)
            for (int u = 0; u < PoolBlock; u++)
            {
                int gx = x0 + u, gz = z0 + v;
                int g = GalleryAt(gx, gz);
                if (g < 0) continue;
                int axis = g == 1 ? 1 : 0;
                var (_, deep) = GalleryStretch(gx, gz, axis);
                p.Floor(u, v, deep && g != 2 ? 2 : 1, GalleryHeight, 0);
                p.Reserved[v * PoolBlock + u] = true;
                // Two-by-two pillars down the middle every nine blocks, far more of them than any hall would need
                if (g == 2) continue;
                int across = GalleryAcross(gx, gz, axis), along = axis == 0 ? gx - PoolOriginX : gz - PoolOriginZ;
                if (across is -1 or 0 && Hashing.Mod(along, 9) is 0 or 1) p.Wall(u, v);
            }
        // The ring round the galleries is kept clear of rooms
        for (int v = 0; v < PoolBlock; v++)
            for (int u = 0; u < PoolBlock; u++)
                if (u < 10 || v < 10 || u >= PoolBlock - 10 || v >= PoolBlock - 10) p.Reserved[v * PoolBlock + u] = true;
    }

    /// <summary>
    /// Halls inside the block, three or four wide, on the lines a third and two thirds of the way across it, stretch
    /// by stretch (most stretches are there). They run on through whatever rooms they meet, joining them to each other
    /// and to the galleries, which is what makes the Poolrooms one complex rather than rooms off corridors. A hall
    /// never cuts through a black tunnel mouth or the offices' drywall.
    /// </summary>
    private void PlanPoolHalls(PoolPlanner p, int x0, int z0)
    {
        for (int axis = 0; axis < 2; axis++)
            for (int line = 1; line <= 2; line++)
                for (int seg = 0; seg < 3; seg++)
                {
                    ulong h = Hashing.Hash(seed, x0 * 2 + axis, z0 * 3 + line * 7 + seg, SaltPoolDeep);
                    if (Hashing.Unit(h) > 0.65) continue;
                    int width = Hashing.Unit(Hashing.Mix(h)) < 0.3 ? 4 : 3;
                    int depth = Hashing.Unit(Hashing.Mix(h) >> 1 << 1) < 0.12 ? 2 : 1;
                    bool lit = Hashing.Unit(Hashing.Mix(Hashing.Mix(h))) < (p.Dim ? 0.3 : 0.6);
                    int across = line * PoolBlock / 3, from = seg * PoolBlock / 3, to = (seg + 1) * PoolBlock / 3 + (seg == 2 ? 0 : 1);
                    for (int a = from; a < to; a++)
                        for (int w = 0; w < width; w++)
                        {
                            int u = axis == 0 ? a : across - width / 2 + w, v = axis == 0 ? across - width / 2 + w : a;
                            if (!PoolPlanner.In(u, v)) continue;
                            ref Tile t = ref p.At(u, v);
                            if (t.Kind != TileKind.Wall || t.Pattern != WallPattern.PoolTile || t.Variant != 0) continue;
                            p.Floor(u, v, depth, 5, 0);
                        }
                    if (!lit) continue;
                    // Slits every five blocks along one side
                    int side = axis == 0 ? across - width / 2 - 1 : across - width / 2 - 1;
                    for (int a = from + 2; a < to - 1; a += 5)
                    {
                        int u = axis == 0 ? a : side, v = axis == 0 ? side : a;
                        if (PoolPlanner.In(u, v) && p.IsFloor(axis == 0 ? u : u + 1, axis == 0 ? v + 1 : v))
                            p.Slit(u, v, axis == 0 ? ArchPier.South : ArchPier.East, 4);
                    }
                }
    }

    /// <summary>
    /// The plainer rooms: a pool with a deck round it and a ladder at each end, a basin stepping down on all sides to
    /// a deep middle, or a hall of water too deep to wade, with a pillar here and there. Slits on one or two walls.
    /// </summary>
    private static void CarveFiller(PoolPlanner p, PoolRoom r, byte owner)
    {
        int u0 = r.U0, v0 = r.V0, u1 = r.U1, v1 = r.V1;
        int height = r.Kind == PoolSpace.FloodedHall ? p.Rng.Range(5, 7) : p.Rng.Range(6, 9);
        int deep = p.Rng.Range(3, 6), cu = (u0 + u1) / 2, cv = (v0 + v1) / 2;
        for (int v = v0; v <= v1; v++)
            for (int u = u0; u <= u1; u++)
            {
                int edge = Math.Min(Math.Min(u - u0, u1 - u), Math.Min(v - v0, v1 - v));
                int depth = r.Kind switch
                {
                    PoolSpace.PoolRoom => edge < 2 ? 0 : deep,
                    PoolSpace.Basin => Math.Min(edge, deep + 2),
                    _ => 2,
                };
                p.Floor(u, v, depth, height, owner);
                if (r.Kind == PoolSpace.FloodedHall && edge >= 2 && (u - u0) % 6 == 3 && (v - v0) % 6 == 3) p.Wall(u, v);
            }
        RoundCorners(p, r, owner, r.Kind == PoolSpace.Basin ? 5 : 4);
        if (r.Kind == PoolSpace.PoolRoom)
        {
            PlaceLadder(p, cu, v0 + 2, ArchPier.North);
            PlaceLadder(p, cu, v1 - 2, ArchPier.South);
        }
        int lit = p.Dim ? 0 : p.Rng.Range(1, 2);
        for (int side = 0; side < 4 && lit > 0; side++)
        {
            if (!p.Rng.Chance(0.55)) continue;
            lit--;
            SlitWall(p, r, (ArchPier)side, height - 2, 4);
        }
    }

    /// <summary>
    /// Rounds off the corners of a rectangular room, as the Poolrooms' rooms are: curved where the walls meet, a
    /// quarter circle of the given radius, so the room reads as one smooth tiled shape.
    /// </summary>
    private static void RoundCorners(PoolPlanner p, PoolRoom r, byte owner, int radius)
    {
        radius = Math.Min(radius, Math.Min(r.U1 - r.U0, r.V1 - r.V0) / 3);
        for (int a = 0; a < radius; a++)
            for (int b = 0; b < radius; b++)
            {
                double dx = radius - a - 0.5, dz = radius - b - 0.5;
                if (dx * dx + dz * dz <= radius * radius) continue;
                foreach (var (u, v) in new[] { (r.U0 + a, r.V0 + b), (r.U1 - a, r.V0 + b), (r.U0 + a, r.V1 - b), (r.U1 - a, r.V1 - b) })
                    if (p.IsFloor(u, v) && p.Owner[v * PoolBlock + u] == owner) p.Wall(u, v);
            }
    }

    /// <summary>
    /// A serpentine hall: a channel of water five wide winding through the square in long curves, its walls following
    /// it, tall slits of light down the outside of each bend.
    /// </summary>
    private static void CarveSerpentine(PoolPlanner p, PoolRoom r, byte o)
    {
        bool alongZ = r.V1 - r.V0 >= r.U1 - r.U0;
        int length = alongZ ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1, across = alongZ ? r.U1 - r.U0 + 1 : r.V1 - r.V0 + 1;
        double amplitude = Math.Max(2, across / 2.0 - 4), period = length / (p.Rng.Chance(0.5) ? 1.0 : 1.5);
        double phase = p.Rng.Chance(0.5) ? 0 : Math.PI;
        int height = p.Rng.Range(6, 8);
        for (int a = 0; a < length; a++)
        {
            double mid = (across - 1) / 2.0 + amplitude * Math.Sin(2 * Math.PI * a / period + phase);
            double slope = Math.Cos(2 * Math.PI * a / period + phase);
            for (int c = 0; c < across; c++)
            {
                if (Math.Abs(c - mid) > 2.6) continue;
                int u = alongZ ? r.U0 + c : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + c;
                p.Floor(u, v, 1, height, o);
            }
            // Slits on the outer side of each bend, every third row
            if (a % 3 != 1 || Math.Abs(slope) > 0.5) continue;
            bool outerHigh = Math.Sin(2 * Math.PI * a / period + phase) > 0;
            int cWall = (int)Math.Round(outerHigh ? mid + 3.1 : mid - 3.1);
            if (cWall < 0 || cWall >= across) continue;
            int wu = alongZ ? r.U0 + cWall : r.U0 + a, wv = alongZ ? r.V0 + a : r.V0 + cWall;
            ArchPier toward = alongZ ? (outerHigh ? ArchPier.West : ArchPier.East) : (outerHigh ? ArchPier.North : ArchPier.South);
            var (du, dv) = StepOf(toward);
            if (p.IsFloor(wu + du, wv + dv) && !p.IsFloor(wu, wv)) p.Slit(wu, wv, toward, height - 2);
        }
    }

    /// <summary>Where a dry deck drops into deep water, its edge is laid with coping tile.</summary>
    private static void PlaceCoping(PoolPlanner p)
    {
        for (int v = 0; v < PoolBlock; v++)
            for (int u = 0; u < PoolBlock; u++)
            {
                ref Tile t = ref p.At(u, v);
                if (t.Kind != TileKind.Floor || t.Depth != 0 || t.Floor != FloorKind.PoolTile || t.Under != 0) continue;
                foreach (var (du, dv, _) in PoolSteps)
                    if (p.IsFloor(u + du, v + dv) && p.At(u + du, v + dv).Depth >= 2) { t.Floor = FloorKind.PoolCoping; break; }
            }
    }

    /// <summary>Slits along one wall of each lit stretch of gallery, handrails along the other.</summary>
    private void LightGalleries(PoolPlanner p, int x0, int z0)
    {
        for (int v = 0; v < PoolBlock; v++)
            for (int u = 0; u < PoolBlock; u++)
            {
                ref Tile t = ref p.At(u, v);
                if (t.Kind != TileKind.Wall || t.Variant != 0) continue;
                int gx = x0 + u, gz = z0 + v;
                foreach (var (du, dv, toward) in PoolSteps)
                {
                    int g = GalleryAt(gx + du, gz + dv);
                    if (g is < 0 or 2 || GalleryAt(gx, gz) >= 0) continue; // a pillar is not a wall
                    int axis = g;
                    // The wall must run along the gallery: the gallery lies across it, not along it
                    if (axis == 0 && du != 0 || axis == 1 && dv != 0) continue;
                    var (lit, _) = GalleryStretch(gx + du, gz + dv, axis);
                    int along = axis == 0 ? gx - PoolOriginX : gz - PoolOriginZ;
                    bool lowSide = toward is ArchPier.South or ArchPier.East; // the wall on the north or west side of the gallery
                    if (lowSide && lit && Hashing.Mod(along, p.Dim ? 8 : 4) == 0) p.Slit(u, v, toward, 6);
                    else if (!lowSide) { t.Variant = PoolWalls.Rail; t.Pier = toward; }
                    break;
                }
            }
    }

    /// <summary>
    /// A domed rotunda round a circular pool, with a dry rim and a pool ladder, ringed by arched openings that glow
    /// white with light from somewhere beyond.
    /// </summary>
    private static void CarveRotunda(PoolPlanner p, PoolRoom r, byte o)
    {
        int cu = (r.U0 + r.U1) / 2, cv = (r.V0 + r.V1) / 2, radius = (r.U1 - r.U0) / 2 - 1;
        int pool = p.Rng.Range(3, 5);
        for (int v = r.V0; v <= r.V1; v++)
            for (int u = r.U0; u <= r.U1; u++)
            {
                double d = Math.Sqrt((u - cu) * (u - cu) + (v - cv) * (v - cv));
                if (d > radius + 0.5) continue;
                // A stepped dome over the pool, rising toward the middle
                double rise = Math.Sqrt(Math.Max(0, 1 - d * d / ((radius + 2.0) * (radius + 2.0))));
                int height = 5 + (int)Math.Round((radius + 3) * rise * 0.9);
                p.Floor(u, v, d <= radius - 2 ? pool : 0, height, o);
            }
        // Arched openings round the wall between the four ways in, glowing with light from beyond
        int arches = radius >= 9 ? 8 : 4;
        for (int k = 0; k < arches; k++)
        {
            double a = (k + 0.5) * Math.PI * 2 / arches;
            int u = cu + (int)Math.Round(Math.Cos(a) * (radius + 1)), v = cv + (int)Math.Round(Math.Sin(a) * (radius + 1));
            ArchPier toward = Math.Abs(Math.Cos(a)) > Math.Abs(Math.Sin(a)) ? (Math.Cos(a) > 0 ? ArchPier.West : ArchPier.East)
                : (Math.Sin(a) > 0 ? ArchPier.North : ArchPier.South);
            p.Slit(u, v, toward, 4, PoolWalls.Arch);
        }
        // A pool ladder on the near side of the pool
        PlaceLadder(p, cu, cv + radius - 2, ArchPier.South);
        PlaceLadder(p, cu, cv - radius + 2, ArchPier.North);
    }

    /// <summary>A pool ladder in the water at the pool's edge, climbing toward the rim at <paramref name="toward"/>.</summary>
    private static void PlaceLadder(PoolPlanner p, int u, int v, ArchPier toward)
    {
        var (du, dv) = StepOf(toward);
        if (!p.IsFloor(u, v) || !p.IsFloor(u + du, v + dv)) return;
        ref Tile t = ref p.At(u, v);
        if (t.Depth < 2 || p.At(u + du, v + dv).Depth != 0) return;
        t.Variant = Props.PoolLadder;
        t.Pier = toward;
    }

    /// <summary>
    /// A pool hall far too big to be one: a shallow end, steps down, a deep end with no ledge along its sides, dry
    /// decks with a colonnade, and high slits down one long wall that never reach the deep end.
    /// </summary>
    private static void CarveNatatorium(PoolPlanner p, PoolRoom r, byte o)
    {
        bool alongZ = r.V1 - r.V0 >= r.U1 - r.U0;
        int length = alongZ ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1, width = alongZ ? r.U1 - r.U0 + 1 : r.V1 - r.V0 + 1;
        bool flip = p.Rng.Chance(0.5); // which end is deep
        int deep = p.Rng.Range(4, 7), height = p.Rng.Range(9, 12), deck = 2;
        int shallowEnd = length / 3, rampEnd = shallowEnd + deep;
        for (int a = 0; a < length; a++)
            for (int c = 0; c < width; c++)
            {
                int t = flip ? length - 1 - a : a; // 0 at the shallow end
                int u = alongZ ? r.U0 + c : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + c;
                bool side = c < deck || c >= width - deck;
                int depth = t < 3 ? 0 : t < shallowEnd ? 1 : t < rampEnd ? 1 + (t - shallowEnd) * (deep - 1) / Math.Max(1, rampEnd - shallowEnd) : deep;
                // The decks run along the sides of the shallow end and the steps, but not the deep end: there is no
                // ledge there to climb out onto
                if (side && t < rampEnd) depth = 0;
                p.Floor(u, v, depth, height, o);
                // A colonnade along the inner edge of each deck
                if ((c == deck - 1 || c == width - deck) && t >= 3 && t < rampEnd && t % 4 == 1) p.Wall(u, v);
            }
        RoundCorners(p, r, o, 4);
        // Slits high in one long wall, down the shallow end and the steps only: the deep end is dark
        bool leftWall = p.Rng.Chance(0.5);
        for (int a = 0; a < length; a++)
        {
            int t = flip ? length - 1 - a : a;
            if (t >= rampEnd || a % 3 != 1) continue;
            int u = alongZ ? (leftWall ? r.U0 - 1 : r.U1 + 1) : r.U0 + a, v = alongZ ? r.V0 + a : (leftWall ? r.V0 - 1 : r.V1 + 1);
            ArchPier toward = alongZ ? (leftWall ? ArchPier.East : ArchPier.West) : (leftWall ? ArchPier.South : ArchPier.North);
            var (su, sv) = StepOf(toward);
            if (!p.IsFloor(u + su, v + sv)) continue; // a rounded corner
            p.Slit(u, v, toward, height - 2);
            SunlitStripe(p, u, v, toward, width - 1);
        }
        // Ladders out of the water where the steps meet the decks
        for (int k = 0; k < 2; k++)
        {
            int a = flip ? length - 1 - (rampEnd - 1) : rampEnd - 1;
            int c = k == 0 ? deck : width - deck - 1;
            int u = alongZ ? r.U0 + c : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + c;
            ArchPier toward = alongZ ? (k == 0 ? ArchPier.West : ArchPier.East) : (k == 0 ? ArchPier.North : ArchPier.South);
            PlaceLadder(p, u, v, toward);
        }
    }

    /// <summary>Light falling through a slit lies in a long bright stripe across the floor in front of it.</summary>
    private static void SunlitStripe(PoolPlanner p, int u, int v, ArchPier toward, int length)
    {
        var (du, dv) = StepOf(toward);
        for (int k = 1; k <= length; k++)
        {
            int x = u + du * k, z = v + dv * k;
            if (!p.IsFloor(x, z)) return;
            p.At(x, z).Floor = FloorKind.PoolSunlit;
        }
    }

    /// <summary>A wading hall with a forest of pillars, far more than it could ever need.</summary>
    private static void CarvePillarHall(PoolPlanner p, PoolRoom r, byte o)
    {
        int height = p.Rng.Range(6, 8), pitch = p.Rng.Chance(0.5) ? 4 : 3, depth = p.Rng.Chance(0.2) ? 0 : 1;
        bool big = pitch == 4 && p.Rng.Chance(0.4);
        for (int v = r.V0; v <= r.V1; v++)
            for (int u = r.U0; u <= r.U1; u++)
            {
                p.Floor(u, v, depth, height, o);
                int a = u - r.U0, c = v - r.V0;
                bool inside = a >= 2 && c >= 2 && u <= r.U1 - 2 && v <= r.V1 - 2;
                if (inside && (big ? a % 6 is 2 or 3 && c % 6 is 2 or 3 : a % pitch == 2 && c % pitch == 2)) p.Wall(u, v);
            }
        RoundCorners(p, r, o, 3);
        // Slits along one or two of its walls
        int lit = p.Rng.Range(1, 2);
        for (int side = 0; side < 4 && lit > 0; side++)
        {
            if (!p.Rng.Chance(0.6)) continue;
            lit--;
            SlitWall(p, r, (ArchPier)side, height - 2, 3);
        }
    }

    /// <summary>Slits every <paramref name="every"/> blocks along one wall of a rectangular room.</summary>
    private static void SlitWall(PoolPlanner p, PoolRoom r, ArchPier wall, int top, int every)
    {
        // The wall on that side of the room, and the way into the room from it
        int count = wall is ArchPier.North or ArchPier.South ? r.U1 - r.U0 + 1 : r.V1 - r.V0 + 1;
        for (int k = 1; k < count - 1; k += every)
        {
            (int u, int v) = wall switch
            {
                ArchPier.North => (r.U0 + k, r.V0 - 1),
                ArchPier.South => (r.U0 + k, r.V1 + 1),
                ArchPier.West => (r.U0 - 1, r.V0 + k),
                _ => (r.U1 + 1, r.V0 + k),
            };
            ArchPier toward = Opposite37(wall);
            var (du, dv) = StepOf(toward);
            if (!p.IsFloor(u + du, v + dv)) continue; // a rounded corner
            p.Slit(u, v, toward, top);
            SunlitStripe(p, u, v, toward, 6);
        }
    }

    /// <summary>
    /// A tunnel of tiled arch rings over shallow water, a step running out of the water along one side. It ends in a
    /// round black mouth (the way out to the sea) or in deep water going nowhere.
    /// </summary>
    private static void CarveArchTunnel(PoolPlanner p, PoolRoom r, byte o)
    {
        bool alongZ = r.V1 - r.V0 > r.U1 - r.U0;
        int length = alongZ ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1;
        bool startHigh = p.Rng.Chance(0.5); // which end opens onto the corridor; the other is the end
        bool mouth = p.Rng.Chance(0.4);
        int ledge = p.Rng.Chance(0.5) ? 1 : 5; // the side with the step (columns 1 to 5; 0 and 6... are walls)
        for (int a = 0; a < length; a++)
        {
            int t = startHigh ? length - 1 - a : a; // 0 at the open end
            for (int c = 1; c <= 5; c++)
            {
                int u = alongZ ? r.U0 + c : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + c;
                if (c != 3 && Math.Abs(c - 3) > 1 && c != ledge) continue; // three wide, and the step
                // The vault: highest down the middle; every third block a ring stands out of it
                int height = (c == 3 ? 5 : 4) - (t % 3 == 0 ? 1 : 0);
                int depth = c == ledge ? 0 : 1;
                bool end = t >= length - 4;
                if (end && !mouth) { depth = c == ledge ? 0 : 6; }
                p.Floor(u, v, depth, height, o);
                if (end && mouth)
                {
                    ref Tile e = ref p.At(u, v);
                    e.Height = 3;
                    e.Under = Unders.TunnelMouth;
                    if (c == ledge) p.Wall(u, v); // the step stops at the mouth
                }
            }
        }
        // The mouth: black all round its last blocks
        if (mouth)
            for (int a = 0; a < length; a++)
            {
                int t = startHigh ? length - 1 - a : a;
                if (t < length - 4) continue;
                for (int c = 0; c <= 6; c++)
                {
                    int u = alongZ ? r.U0 + c : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + c;
                    if (PoolPlanner.In(u, v) && p.At(u, v).Kind == TileKind.Wall) p.At(u, v).Pattern = WallPattern.PoolVoid;
                }
                if (t == length - 1)
                    for (int c = 0; c <= 6; c++)
                    {
                        int u = alongZ ? r.U0 + c : r.U0 + a + (startHigh ? -1 : 1), v = alongZ ? r.V0 + a + (startHigh ? -1 : 1) : r.V0 + c;
                        if (PoolPlanner.In(u, v) && p.At(u, v).Kind == TileKind.Wall) p.At(u, v).Pattern = WallPattern.PoolVoid;
                    }
            }
        // A slit or two by the open end only; the tunnel goes on into the dark
        int sideWall = ledge == 1 ? 5 : 1; // the wall across from the step
        for (int t = 1; t <= 4; t += 3)
        {
            int a = startHigh ? length - 1 - t : t;
            int u = alongZ ? r.U0 + sideWall : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + sideWall;
            ArchPier toward = alongZ ? (sideWall == 1 ? ArchPier.East : ArchPier.West) : (sideWall == 1 ? ArchPier.South : ArchPier.North);
            p.Slit(u, v, toward, 3);
        }
    }

    /// <summary>
    /// Broad steps going straight down into water too deep and dark to see the bottom of. One pit in four has no
    /// bottom at all that anyone has found; in the others lies what someone lost.
    /// </summary>
    private void CarveStairPit(PoolPlanner p, PoolRoom r, byte o)
    {
        bool alongZ = r.V1 - r.V0 >= r.U1 - r.U0;
        int length = alongZ ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1, width = alongZ ? r.U1 - r.U0 + 1 : r.V1 - r.V0 + 1;
        bool flip = p.Rng.Chance(0.5);
        int pit = p.Rng.Range(10, WorldGeometry.PoolPitDepth);
        bool bottomless = p.Rng.Chance(0.25);
        int steps = p.Rng.Range(4, 6);
        for (int a = 0; a < length; a++)
            for (int c = 0; c < width; c++)
            {
                int t = flip ? length - 1 - a : a; // 0 at the top of the steps
                int u = alongZ ? r.U0 + c : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + c;
                int depth = t < 2 ? 0 : t < 2 + steps ? t - 1 : pit;
                p.Floor(u, v, depth, 6, o);
                if (depth == pit && bottomless) p.At(u, v).Under = Unders.PitBottom;
            }
        if (!bottomless)
        {
            // What the drowned left on the bottom
            for (int k = 0; k < 2; k++)
            {
                int a = flip ? p.Rng.Range(0, length - 3 - steps) : p.Rng.Range(2 + steps, length - 1);
                int c = p.Rng.Range(0, width - 1);
                int u = alongZ ? r.U0 + c : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + c;
                ref Tile t = ref p.At(u, v);
                if (t.Depth != pit) continue;
                t.Variant = k == 0 ? Props.Backpack : Props.BonePile;
            }
        }
    }

    /// <summary>A long wading hall with a whole wall of slits, the brightest place there is.</summary>
    private static void CarveSlitHall(PoolPlanner p, PoolRoom r, byte o)
    {
        bool alongZ = r.V1 - r.V0 > r.U1 - r.U0;
        for (int v = r.V0; v <= r.V1; v++)
            for (int u = r.U0; u <= r.U1; u++) p.Floor(u, v, 1, 7, o);
        ArchPier wall = alongZ ? (p.Rng.Chance(0.5) ? ArchPier.West : ArchPier.East) : (p.Rng.Chance(0.5) ? ArchPier.North : ArchPier.South);
        SlitWall(p, r, wall, 5, 2);
        // A handrail along the other
        ArchPier other = Opposite37(wall);
        int count = alongZ ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1;
        for (int k = 0; k < count; k++)
        {
            (int u, int v) = other switch
            {
                ArchPier.North => (r.U0 + k, r.V0 - 1),
                ArchPier.South => (r.U0 + k, r.V1 + 1),
                ArchPier.West => (r.U0 - 1, r.V0 + k),
                _ => (r.U1 + 1, r.V0 + k),
            };
            if (PoolPlanner.In(u, v) && p.At(u, v).Kind == TileKind.Wall && p.At(u, v).Variant == 0)
            {
                p.At(u, v).Variant = PoolWalls.Rail;
                p.At(u, v).Pier = wall;
            }
        }
    }

    /// <summary>
    /// A long dry corridor, low and plain, with nothing in it. At its far end the tile gives way to grey office
    /// carpet and drywall: walk on and you are in Level 4.
    /// </summary>
    private static void CarveDryCorridor(PoolPlanner p, PoolRoom r, byte o)
    {
        bool alongZ = r.V1 - r.V0 > r.U1 - r.U0;
        int length = alongZ ? r.V1 - r.V0 + 1 : r.U1 - r.U0 + 1;
        bool farHigh = p.Rng.Chance(0.5);
        for (int a = 0; a < length; a++)
        {
            int t = farHigh ? a : length - 1 - a; // 0 at the far end
            for (int c = 1; c <= 3; c++)
            {
                int u = alongZ ? r.U0 + c : r.U0 + a, v = alongZ ? r.V0 + a : r.V0 + c;
                bool carpet = t < 4;
                p.Floor(u, v, 0, 4, o, carpet ? FloorKind.OfficeCarpet : FloorKind.PoolTile);
                if (t == 0) p.At(u, v).Under = Unders.PoolCarpet;
                if (carpet)
                {
                    // Drywall either side of the carpet
                    int wu = alongZ ? r.U0 + (c == 1 ? 0 : 4) : u, wv = alongZ ? v : r.V0 + (c == 1 ? 0 : 4);
                    if (c != 2 && p.At(wu, wv).Kind == TileKind.Wall) p.At(wu, wv).Pattern = WallPattern.Drywall;
                }
            }
        }
        // The far wall, drywall too
        int endA = farHigh ? 0 : length - 1;
        for (int c = 0; c <= 4; c++)
        {
            int u = alongZ ? r.U0 + c : r.U0 + endA + (farHigh ? -1 : 1), v = alongZ ? r.V0 + endA + (farHigh ? -1 : 1) : r.V0 + c;
            if (PoolPlanner.In(u, v) && p.At(u, v).Kind == TileKind.Wall) p.At(u, v).Pattern = WallPattern.Drywall;
        }
        // One slit at the tile end, and then the corridor goes on without light
        int a0 = farHigh ? length - 2 : 1;
        int su = alongZ ? r.U0 : r.U0 + a0, sv = alongZ ? r.V0 + a0 : r.V0;
        p.Slit(su, sv, alongZ ? ArchPier.East : ArchPier.South, 3);
    }

    /// <summary>
    /// Opens a room onto whatever lies beyond each of its sides (a hall, a gallery, the next room), within ten blocks:
    /// an opening three wide in the middle of the side. A tunnel, a corridor or a stair pit opens at its one open end
    /// only. A natatorium's deep end, now and then, has a hole in its wall under the water instead.
    /// </summary>
    private void OpenPoolRoom(PoolPlanner p, PoolRoom r, byte owner)
    {
        int cu = (r.U0 + r.U1) / 2, cv = (r.V0 + r.V1) / 2;
        bool thin = r.Kind is PoolSpace.ArchTunnel or PoolSpace.DryCorridor or PoolSpace.StairPit;
        foreach (ArchPier side in new[] { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West })
        {
            if (thin && !OpenEndOf(p, r, side, owner)) continue;
            int depth = r.Kind == PoolSpace.DryCorridor ? 0 : r.Kind == PoolSpace.FloodedHall ? 2 : 1;
            CarveCorridor(p, r, side, cu, cv, owner, depth);
        }
        if (r.Kind == PoolSpace.Natatorium && p.Rng.Chance(0.35)) CarveUnderwaterHole(p, r, owner);
    }

    /// <summary>Whether the tile just inside a side of a long room is its open end (where it should be entered).</summary>
    private static bool OpenEndOf(PoolPlanner p, PoolRoom r, ArchPier side, byte owner)
    {
        int cu = (r.U0 + r.U1) / 2, cv = (r.V0 + r.V1) / 2;
        (int u, int v) = side switch
        {
            ArchPier.North => (cu, r.V0),
            ArchPier.South => (cu, r.V1),
            ArchPier.West => (r.U0, cv),
            _ => (r.U1, cv),
        };
        if (!p.IsFloor(u, v)) return false;
        Tile t = p.At(u, v);
        // Not the black mouth, the carpet, nor the bottom of a pit
        return t.Under == 0 && t.Floor != FloorKind.OfficeCarpet && t.Depth <= 1;
    }

    private static bool CarveCorridor(PoolPlanner p, PoolRoom r, ArchPier side, int cu, int cv, byte owner, int depth)
    {
        var (du, dv) = StepOf(side);
        // Start just outside the room's box, in the middle of that side
        int u = side switch { ArchPier.West => r.U0 - 1, ArchPier.East => r.U1 + 1, _ => cu };
        int v = side switch { ArchPier.North => r.V0 - 1, ArchPier.South => r.V1 + 1, _ => cv };
        // Step back into the room until floor of its own is found (a rotunda's circle sits inside its box)
        int back = 0;
        while (back < 4 && !(p.IsFloor(u - du, v - dv) && p.Owner[(v - dv) * PoolBlock + u - du] == owner)) { u -= du; v -= dv; back++; }
        var path = new List<(int, int)>();
        bool reached = false;
        for (int k = 0; k < 11; k++, u += du, v += dv)
        {
            if (!PoolPlanner.In(u, v)) { reached = true; break; } // out to the block's edge: the gallery's line is there
            bool open = p.IsFloor(u, v) && p.Owner[v * PoolBlock + u] != owner;
            if (open && k > 0) { reached = true; break; }
            path.Add((u, v));
        }
        if (path.Count == 0 || !reached) return false;
        foreach (var (x, z) in path)
            for (int w = -1; w <= 1; w++)
            {
                int a = x + (du == 0 ? w : 0), b = z + (dv == 0 ? w : 0);
                if (!PoolPlanner.In(a, b)) continue;
                ref Tile t = ref p.At(a, b);
                if (t.Kind == TileKind.Floor) continue;
                p.Floor(a, b, depth, 5, 0);
            }
        return true;
    }

    /// <summary>A swim: a passage under the water from a natatorium's deep end out to a gallery, surfacing through a sump in its floor.</summary>
    private void CarveUnderwaterHole(PoolPlanner p, PoolRoom r, byte owner)
    {
        // The deep end is the end of the long axis that is deep; head for the nearest edge of the block from there
        bool alongZ = r.V1 - r.V0 >= r.U1 - r.U0;
        foreach (bool high in new[] { false, true })
        {
            int u = alongZ ? (r.U0 + r.U1) / 2 : high ? r.U1 : r.U0, v = alongZ ? (high ? r.V1 : r.V0) : (r.V0 + r.V1) / 2;
            if (!p.IsFloor(u, v) || p.At(u, v).Depth < 4) continue;
            int deep = p.At(u, v).Depth;
            ArchPier side = alongZ ? (high ? ArchPier.South : ArchPier.North) : (high ? ArchPier.East : ArchPier.West);
            var (du, dv) = StepOf(side);
            int x = u + du, z = v + dv;
            var path = new List<(int, int)>();
            while (PoolPlanner.In(x, z) && !p.IsFloor(x, z)) { path.Add((x, z)); x += du; z += dv; }
            if (path.Count < 3 || !PoolPlanner.In(x, z)) return; // nowhere to surface in this block
            for (int k = 0; k < path.Count; k++)
            {
                var (a, b) = path[k];
                bool last = k == path.Count - 1;
                for (int w = 0; w <= 1; w++)
                {
                    int a2 = a + (du == 0 ? w : 0), b2 = b + (dv == 0 ? w : 0);
                    if (!PoolPlanner.In(a2, b2) || p.IsFloor(a2, b2)) continue;
                    // Under the water all the way, then a sump in the gallery's floor to come up through
                    p.Floor(a2, b2, last ? 3 : deep, 5, 0);
                    if (!last) p.At(a2, b2).Under = Unders.PoolHole;
                }
            }
            return;
        }
    }

    /// <summary>
    /// The cyan doors marked POOL: one or two to a block, in a wall beside the water. Most lead to a corridor of the
    /// Terror Hotel.
    /// </summary>
    private static void PlacePoolDoors(PoolPlanner p)
    {
        int doors = p.Reservoir ? 0 : p.Rng.Range(1, 2);
        for (int attempt = 0; attempt < 300 && doors > 0; attempt++)
        {
            int u = p.Rng.Range(2, PoolBlock - 3), v = p.Rng.Range(2, PoolBlock - 3);
            ref Tile t = ref p.At(u, v);
            if (t.Kind != TileKind.Wall || t.Variant != 0 || t.Pattern != WallPattern.PoolTile) continue;
            // Floor on exactly one side, wall on the other three, and the floor shallow
            int floors = 0;
            ArchPier toward = ArchPier.North;
            foreach (var (du, dv, side) in PoolSteps)
            {
                if (!p.IsFloor(u + du, v + dv)) continue;
                floors++;
                toward = side;
            }
            if (floors != 1) continue;
            var (fu, fv) = StepOf(toward);
            Tile front = p.At(u + fu, v + fv);
            if (front.Depth > 1 || front.Under != 0 || front.Variant != 0) continue;
            // Its neighbours along the wall must be wall too, so the door stands in a wall and not at a corner
            var (au, av) = toward is ArchPier.North or ArchPier.South ? (1, 0) : (0, 1);
            if (p.IsFloor(u + au, v + av) || p.IsFloor(u - au, v - av) || p.IsFloor(u - fu, v - fv)) continue;
            t.Kind = TileKind.Door;
            t.Pattern = WallPattern.PoolDoor;
            t.Pier = toward;
            doors--;
        }
    }

    /// <summary>
    /// What is left lying about: a towel, a flip-flop, a pool noodle on a deck now and then; and crusts of Epsom salt
    /// dried on the rims in the dark, where no slit's light reaches.
    /// </summary>
    private static void PlacePoolLeftovers(PoolPlanner p)
    {
        bool[] lit = PoolLightReach(p);
        for (int v = 1; v < PoolBlock - 1; v++)
            for (int u = 1; u < PoolBlock - 1; u++)
            {
                ref Tile t = ref p.At(u, v);
                // The dark corners are marked, for the stability that drains there
                if (t.Kind == TileKind.Floor && !lit[v * PoolBlock + u]) t.Detail = PoolDark;
                if (t.Kind != TileKind.Floor || t.Depth != 0 || t.Variant != 0 || t.Under != 0 || t.Floor == FloorKind.OfficeCarpet) continue;
                if (!lit[v * PoolBlock + u] && p.Rng.Chance(0.05)) t.Variant = Props.EpsomCrust;
                else if (lit[v * PoolBlock + u] && p.Rng.Chance(0.004))
                {
                    t.Variant = Props.LostThing;
                    t.Stack = (byte)p.Rng.Range(0, 2);
                    t.Pier = (ArchPier)p.Rng.Range(0, 3);
                }
            }
    }

    /// <summary>
    /// Roughly which floor the slits light: within fourteen blocks of one, walking (the light fades a level a block,
    /// and a slit is bright 18). Worked out on the plan alone, for placing things in the dark.
    /// </summary>
    private static bool[] PoolLightReach(PoolPlanner p)
    {
        var dist = new int[PoolBlock * PoolBlock];
        Array.Fill(dist, int.MaxValue);
        var queue = new Queue<int>();
        for (int v = 0; v < PoolBlock; v++)
            for (int u = 0; u < PoolBlock; u++)
            {
                Tile t = p.At(u, v);
                if (t.Kind != TileKind.Wall || t.Variant is not (PoolWalls.Slit or PoolWalls.Arch)) continue;
                var (du, dv) = StepOf(t.Pier);
                if (!p.IsFloor(u + du, v + dv)) continue;
                int i = (v + dv) * PoolBlock + u + du;
                if (dist[i] == 0) continue;
                dist[i] = 0;
                queue.Enqueue(i);
            }
        while (queue.Count > 0)
        {
            int i = queue.Dequeue();
            if (dist[i] >= 14) continue;
            int u = i % PoolBlock, v = i / PoolBlock;
            foreach (var (du, dv, _) in PoolSteps)
            {
                if (!p.IsFloor(u + du, v + dv)) continue;
                int n = (v + dv) * PoolBlock + u + du;
                if (dist[n] <= dist[i] + 1) continue;
                dist[n] = dist[i] + 1;
                queue.Enqueue(n);
            }
        }
        var lit = new bool[dist.Length];
        for (int i = 0; i < dist.Length; i++) lit[i] = dist[i] != int.MaxValue;
        return lit;
    }

    /// <summary>
    /// The Sanguine Reservoir: the same rooms, but no light gets in, the water stands deeper and red, red sprouts glow
    /// on the floors of the pools, and at the bottom lie those who stayed.
    /// </summary>
    private static void MakeReservoir(PoolPlanner p)
    {
        for (int i = 0; i < p.Tiles.Length; i++)
        {
            ref Tile t = ref p.Tiles[i];
            t.Zone = 1;
            if (t.Kind == TileKind.Wall)
            {
                if (t.Variant is PoolWalls.Slit or PoolWalls.Arch) { t.Variant = 0; t.Height = 0; }
                continue;
            }
            if (t.Kind != TileKind.Floor) continue;
            if (t.Floor is FloorKind.PoolTile or FloorKind.PoolSunlit or FloorKind.PoolCoping) t.Floor = FloorKind.PoolRed;
            if (t.Under == Unders.PitBottom) t.Under = 0; // the Reservoir keeps what falls in
            if (t.Floor == FloorKind.OfficeCarpet || t.Under is Unders.TunnelMouth or Unders.PoolCarpet) continue;
            if (t.Depth >= 1 && t.Depth < 3) t.Depth++;
            if (t.Variant != 0 || t.Depth < 2) continue;
            double r = p.Rng.NextDouble();
            if (r < 0.06) t.Variant = Props.RedSprout;
            else if (r < 0.075) t.Variant = Props.BonePile;
            else if (r < 0.085) t.Variant = Props.Backpack;
        }
    }
}
