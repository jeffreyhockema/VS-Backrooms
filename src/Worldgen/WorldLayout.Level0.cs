using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 0, "the Lobby": back rooms of an office or a shop that go on for miles, a labyrinth of rooms and hallways.
/// Hallways two or three wide run a few blocks, turn hard, run on, turn again, open into a room, end against a blank
/// wall; rooms open into rooms, into narrow gaps, into other hallways. Nothing runs straight for long, and no view goes
/// far, as in the 2002 photos, Kane Pixels' footage and the film: "one long corridor that turns into a never-ending
/// labyrinth", "endless corners".
///
/// <para>The level is laid out in districts, about <see cref="L0Pitch"/> blocks each way, laid like bricks (each row
/// of districts is shifted, and every wall between two of them is jittered) so no wall lines up with the next. The
/// wall between two districts is gapped every dozen blocks or so, and nothing tells it apart from any other wall.
/// Each district is planned once from its own id (it is larger than a macro cell, so the plan is cached and the cells
/// copy their part of it): it is split into rooms, then hallways wind in from the gaps in its walls, and finally every
/// room and hallway is joined to the rest by doorless openings, with plenty of extra ones, so there are always more
/// ways than you need.</para>
///
/// <para>What a district holds depends on its area (a jittered Voronoi diagram over coarse regions): the labyrinth;
/// open offices of big rooms with partitions standing free in them, like the photo; pillar halls, which run on through
/// the walls into the next pillar hall; arched rooms; blackout areas in the dark on soaked carpet. Inside the labyrinth
/// some rooms are set pieces: a big room, rows of identical rooms off a corridor, a room of pits. The Manila Room and
/// the Red Rooms are rare whole cells laid over the plan.</para>
/// </summary>
public sealed partial class WorldLayout
{
    private const int RegionSize = 4;
    private const int MinRoom = 5;

    /// <summary>Average size of a district, each way.</summary>
    private const int L0Pitch = 44;
    private const int L0Jitter = 7;
    /// <summary>About how far apart the gaps in the wall between two districts are.</summary>
    private const int L0GapEvery = 11;

    private const ulong SaltRegionSeed = 0x2E61;
    private const ulong SaltRegionKind = 0x2E62;
    private const ulong SaltManila = 0x3A71;
    private const ulong SaltLight = 0x1167;
    private const ulong SaltPillar = 0x9111;
    private const ulong SaltOutlet = 0x0717;
    private const ulong SaltL0Line = 0x2E80;
    private const ulong SaltL0Gap = 0x2E81;
    private const ulong SaltL0Block = 0x2E82;

    // ================= Zones =================

    private enum LightStyle : byte { Grid, Rows }

    private readonly struct Region
    {
        public readonly int X, Z;
        public readonly ZoneKind Zone;
        public readonly LightStyle Lights;
        public readonly int LightSpacing;
        public readonly bool LightRowsAlongX;
        public readonly int LightPhaseX, LightPhaseZ;
        public readonly int PillarSpacing, PillarSize, PillarPhaseX, PillarPhaseZ;
        public readonly bool PlusPillars;
        /// <summary>Most walls in an area share one wallpaper, so trim stays consistent.</summary>
        public readonly WallPattern PrimaryPattern;

        public Region(ulong seed, int rx, int rz)
        {
            X = rx;
            Z = rz;
            var rng = new Rng(Hashing.Hash(seed, rx, rz, SaltRegionKind));
            double r = rng.NextDouble();
            Zone = r < 0.58 ? ZoneKind.Lobby
                : r < 0.72 ? ZoneKind.OpenOffice
                : r < 0.82 ? ZoneKind.PillarHall
                : r < 0.91 ? ZoneKind.Arches
                : ZoneKind.Blackout;

            Lights = rng.Chance(0.3) ? LightStyle.Rows : LightStyle.Grid;
            LightSpacing = rng.Chance(0.65) ? 3 : 4;
            LightRowsAlongX = rng.Chance(0.5);
            LightPhaseX = rng.Range(0, 11);
            LightPhaseZ = rng.Range(0, 11);

            PillarSpacing = rng.Range(5, 8);
            PillarSize = rng.Chance(0.35) ? 1 : rng.Chance(0.6) ? 2 : 3;
            PlusPillars = PillarSize == 3 && rng.Chance(0.5);
            PillarPhaseX = rng.Range(0, 15);
            PillarPhaseZ = rng.Range(0, 15);
            PrimaryPattern = rng.Chance(0.8) ? WallPattern.Chevron : WallPattern.Dotted;
        }
    }

    private Region RegionAt(int mx, int mz)
    {
        int rx = Hashing.FloorDiv(mx, RegionSize);
        int rz = Hashing.FloorDiv(mz, RegionSize);
        double best = double.MaxValue;
        int bestX = rx, bestZ = rz;
        for (int dz = -1; dz <= 1; dz++)
        {
            for (int dx = -1; dx <= 1; dx++)
            {
                int cx = rx + dx, cz = rz + dz;
                ulong h = Hashing.Hash(seed, cx, cz, SaltRegionSeed);
                double sx = cx * RegionSize + Hashing.Unit(h) * RegionSize;
                double sz = cz * RegionSize + Hashing.Unit(Hashing.Mix(h)) * RegionSize;
                double d = (mx + 0.5 - sx) * (mx + 0.5 - sx) + (mz + 0.5 - sz) * (mz + 0.5 - sz);
                if (d < best) { best = d; bestX = cx; bestZ = cz; }
            }
        }
        return new Region(seed, bestX, bestZ);
    }

    /// <summary>The zone of a cell: that of the district its middle lies in.</summary>
    public ZoneKind ZoneAt(int mx, int mz)
    {
        if (IsSpawnMacro(mx, mz)) return ZoneKind.Lobby;
        return Level0ZoneAt(mx * MacroSize + MacroSize / 2, mz * MacroSize + MacroSize / 2);
    }

    /// <summary>The zone of the district a block position lies in.</summary>
    public ZoneKind Level0ZoneAt(int gx, int gz)
    {
        int j = L0RowOf(gz);
        return L0Info(L0ColOf(gx, j), j).Zone;
    }

    /// <summary>The Manila Room: a very rare, quiet 8x8 room with wooden floors, and a table under a chandelier.</summary>
    public bool IsManilaMacro(int mx, int mz)
    {
        if (Math.Abs(mx - spawnMacroX) < 3 && Math.Abs(mz - spawnMacroZ) < 3) return false;
        if (LevelAt(mx, mz) != 0) return false;
        ZoneKind zone = RegionAt(mx, mz).Zone;
        if (zone != ZoneKind.Lobby && zone != ZoneKind.OpenOffice) return false;
        return Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltManila)) < 0.0015;
    }

    private const ulong SaltRedRoom = 0x3A72;

    /// <summary>
    /// A Red Room: a rare cell of Level 0 papered in red and lit by a few dim red lamps, walled off from the rooms
    /// round it but for one gap in each side. Nothing holds here; whatever was left inside is still there.
    /// </summary>
    public bool IsRedRoom(int mx, int mz)
    {
        if (Math.Abs(mx - spawnMacroX) < 6 && Math.Abs(mz - spawnMacroZ) < 6) return false;
        if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltRedRoom)) >= 0.004) return false;
        return LevelAt(mx, mz) == 0 && RegionAt(mx, mz).Zone == ZoneKind.Lobby && !IsManilaMacro(mx, mz);
    }

    // ================= Districts =================

    /// <summary>What a stretch of a district is: not a hallway, the middle lane of one running west-east or north-south, or the rest of one.</summary>
    private const byte HallNone = 0, HallAlongX = 1, HallAlongZ = 2, HallSide = 3;

    /// <summary>A room in the labyrinth that is laid out on its own: anything but plain rooms.</summary>
    private enum L0Piece : byte { Big, Pits, CellRows, Spawn }

    private static int L0Jit(ulong h) => (int)(h % (2 * L0Jitter + 1)) - L0Jitter;

    /// <summary>The z of the wall along the north side of row <paramref name="j"/> of districts.</summary>
    private int L0Row(int j) => j * L0Pitch + L0Jit(Hashing.Hash(seed, j, 0, SaltL0Line));

    /// <summary>How far a row of districts is shifted west-east, so the walls of one row never line up with the next.</summary>
    private int L0RowShift(int j) => (int)(Hashing.Hash(seed, j, 1, SaltL0Line) % L0Pitch);

    /// <summary>The x of the wall along the west side of district <paramref name="i"/> in row <paramref name="j"/>.</summary>
    private int L0Col(int i, int j) => i * L0Pitch + L0RowShift(j) + L0Jit(Hashing.Hash(seed, i, j, SaltL0Line + 2));

    private int L0RowOf(int gz)
    {
        int j = Hashing.FloorDiv(gz, L0Pitch);
        while (gz < L0Row(j)) j--;
        while (gz >= L0Row(j + 1)) j++;
        return j;
    }

    private int L0ColOf(int gx, int j)
    {
        int i = Hashing.FloorDiv(gx - L0RowShift(j), L0Pitch);
        while (gx < L0Col(i, j)) i--;
        while (gx >= L0Col(i + 1, j)) i++;
        return i;
    }

    private bool L0SpawnDistrict(int i, int j)
    {
        int gx = spawnMacroX * MacroSize + MacroSize / 2, gz = spawnMacroZ * MacroSize + MacroSize / 2;
        int sj = L0RowOf(gz);
        return sj == j && L0ColOf(gx, sj) == i;
    }

    /// <summary>The area (zone, wallpaper, lights, pillars) a district belongs to, decided by its middle.</summary>
    private (ZoneKind Zone, Region Region, bool Pillars, bool Spawn) L0Info(int i, int j)
    {
        int cx = (L0Col(i, j) + L0Col(i + 1, j)) / 2, cz = (L0Row(j) + L0Row(j + 1)) / 2;
        Region region = RegionAt(MacroOf(cx), MacroOf(cz));
        // You wake in a big empty room with one partition standing in it, like the photo
        if (L0SpawnDistrict(i, j)) return (ZoneKind.Lobby, region, false, true);
        return (region.Zone, region, region.Zone == ZoneKind.PillarHall, false);
    }

    /// <summary>
    /// Where the gaps in a district's west wall (axis 0) or north wall (axis 1) start, as block coordinates along the
    /// wall; each is two wide. One every dozen blocks or so, never at a corner, and always at least one, so every
    /// district opens onto every neighbour along its west side and onto the row north of it.
    /// </summary>
    private List<int> L0Gaps(int i, int j, int axis)
    {
        int a0 = axis == 0 ? L0Row(j) + 1 : L0Col(i, j) + 1;
        int a1 = axis == 0 ? L0Row(j + 1) - 1 : L0Col(i + 1, j) - 1;
        // A gap in a north wall keeps clear of the walls of the row beyond that meet it
        var meet = new List<int>();
        if (axis == 1)
            for (int k = L0ColOf(a0 - 1, j - 1); L0Col(k, j - 1) <= a1 + 1; k++) meet.Add(L0Col(k, j - 1));
        bool Valid(int s)
        {
            if (s < a0 + 1 || s + 1 > a1 - 1) return false;
            foreach (int x in meet) if (x >= s - 1 && x <= s + 2) return false;
            return true;
        }

        var rng = new Rng(Hashing.Hash(seed, i * 2 + axis, j, SaltL0Gap));
        var gaps = new List<int>();
        int len = a1 - a0 + 1, segments = Math.Max(1, len / L0GapEvery);
        for (int n = 0; n < segments; n++)
        {
            int lo = a0 + n * len / segments, hi = a0 + (n + 1) * len / segments - 2;
            bool want = rng.Chance(0.55);
            int s = rng.Range(lo, Math.Max(lo, hi));
            if (want && Valid(s)) gaps.Add(s);
        }
        if (gaps.Count == 0)
        {
            int start = rng.Range(a0, a1);
            for (int n = 0; n < len; n++)
            {
                int s = a0 + Hashing.Mod(start - a0 + n, len);
                if (Valid(s)) { gaps.Add(s); break; }
            }
        }
        return gaps;
    }

    private sealed class L0Plan
    {
        /// <summary>The district's corner and size, counting its own west and north walls (the east and south ones belong to its neighbours).</summary>
        public int X0, Z0, W, H;
        public ZoneKind Zone;
        public Region Region;
        public bool Pillars, Spawn, PitsAllowed;
        public WallPattern Primary;
        public Tile[] Tiles;
        public LightMood[] Mood;
        /// <summary>Which tiles are hallway (see <see cref="HallNone"/>), for the lights down the middle.</summary>
        public byte[] Hall;
        public Rng Rng;

        public ref Tile At(int u, int v) => ref Tiles[v * W + u];
        public bool In(int u, int v) => u >= 0 && v >= 0 && u < W && v < H;
        /// <summary>Inside the district's own walls.</summary>
        public bool Inner(int u, int v) => u >= 1 && v >= 1 && u < W && v < H;
    }

    private PlanCache<L0Plan> l0Plans;

    private L0Plan L0PlanAt(int i, int j) => (l0Plans ??= new PlanCache<L0Plan>(256, PlanL0)).Get(i, j);

    /// <summary>The planned tile at a block position (before any cell lays the Manila Room or a Red Room over it).</summary>
    private Tile L0TileAt(int gx, int gz)
    {
        int j = L0RowOf(gz);
        L0Plan p = L0PlanAt(L0ColOf(gx, j), j);
        return p.At(gx - p.X0, gz - p.Z0);
    }

    private L0Plan PlanL0(int i, int j)
    {
        var info = L0Info(i, j);
        int x0 = L0Col(i, j), z0 = L0Row(j);
        var p = new L0Plan
        {
            X0 = x0, Z0 = z0, W = L0Col(i + 1, j) - x0, H = L0Row(j + 1) - z0,
            Zone = info.Zone, Region = info.Region, Pillars = info.Pillars, Spawn = info.Spawn,
            Primary = info.Zone == ZoneKind.Arches ? WallPattern.Cream : info.Region.PrimaryPattern,
            Rng = new Rng(Hashing.Hash(seed, i, j, SaltL0Block)),
        };
        int cmx = MacroOf(x0 + p.W / 2), cmz = MacroOf(z0 + p.H / 2);
        p.PitsAllowed = p.Zone == ZoneKind.Lobby && (Math.Abs(cmx - spawnMacroX) >= 3 || Math.Abs(cmz - spawnMacroZ) >= 3);
        p.Tiles = new Tile[p.W * p.H];
        p.Mood = new LightMood[p.W * p.H];
        p.Hall = new byte[p.W * p.H];
        if (p.Zone == ZoneKind.Blackout)
            for (int n = 0; n < p.Tiles.Length; n++) { p.Tiles[n].Floor = FloorKind.Soaked; p.Mood[n] = LightMood.Blackout; }

        // The walls this district shares with its neighbours to the west and north, and their gaps. Between two
        // pillar halls there is no wall: the pillars run on.
        BaseStyle baseStyle = BaseFor(p.Primary);
        bool UpperPillars(int gx) => L0Info(L0ColOf(gx, j - 1), j - 1).Pillars;
        bool westMerged = p.Pillars && L0Info(i - 1, j).Pillars;
        for (int v = 0; v < p.H; v++) if (!(westMerged && v > 0)) SetWall(ref p.At(0, v), p.Primary, baseStyle);
        for (int u = 1; u < p.W; u++) if (!(p.Pillars && UpperPillars(x0 + u))) SetWall(ref p.At(u, 0), p.Primary, baseStyle);
        if (westMerged && UpperPillars(x0) && UpperPillars(x0 - 1)) p.At(0, 0).Kind = TileKind.Floor;

        // Every gap, from inside: its first tile, and the step from it into the district
        var openings = new List<(int U, int V, int DU, int DV)>();
        var gapTiles = new List<(int, int)>();
        if (!westMerged)
            foreach (int s in L0Gaps(i, j, 0))
            {
                gapTiles.Add((0, s - z0));
                gapTiles.Add((0, s - z0 + 1));
                openings.Add((1, s - z0, 1, 0));
            }
        foreach (int s in L0Gaps(i, j, 1))
        {
            gapTiles.Add((s - x0, 0));
            gapTiles.Add((s - x0 + 1, 0));
            openings.Add((s - x0, 1, 0, 1));
        }
        foreach ((int u, int v) in gapTiles) p.At(u, v).Kind = TileKind.Floor;
        if (!(p.Pillars && L0Info(i + 1, j).Pillars))
            foreach (int s in L0Gaps(i + 1, j, 0)) openings.Add((p.W - 1, s - z0, -1, 0));
        for (int k = L0ColOf(x0, j + 1); L0Col(k, j + 1) < x0 + p.W; k++)
        {
            if (p.Pillars && L0Info(k, j + 1).Pillars) continue;
            foreach (int s in L0Gaps(k, j + 1, 1))
                if (s >= x0 + 1 && s + 1 <= x0 + p.W - 1) openings.Add((s - x0, p.H - 1, 0, -1));
        }

        if (p.Pillars)
        {
            PlanPillars(p);
            foreach ((int u, int v) in gapTiles) p.At(u, v).Kind = TileKind.Floor;
            foreach (var o in openings) ClearGap(p, o);
            MoodPatch(p, 1, 1, p.W - 1, p.H - 1);
            for (int n = 0; n < 3; n++) Stain(p, p.Rng.Range(1, p.W - 1), p.Rng.Range(1, p.H - 1), p.Rng.Range(1, 3));
            return p;
        }
        PlanLabyrinth(p, openings);
        return p;
    }

    /// <summary>Clears the two tiles just inside a gap.</summary>
    private static void ClearGap(L0Plan p, (int U, int V, int DU, int DV) o)
    {
        p.At(o.U, o.V).Kind = TileKind.Floor;
        int u2 = o.U + (o.DU == 0 ? 1 : 0), v2 = o.V + (o.DV == 0 ? 1 : 0);
        if (p.Inner(u2, v2)) p.At(u2, v2).Kind = TileKind.Floor;
    }

    // ================= The labyrinth =================

    private void PlanLabyrinth(L0Plan p, List<(int U, int V, int DU, int DV)> openings)
    {
        int W = p.W, H = p.H;
        // Rooms first: the district split up by straight walls, a few rooms kept whole for set pieces
        var pieces = new List<(L0Piece Kind, int X0, int Z0, int X1, int Z1)>();
        LabSplit(p, 1, 1, W - 1, H - 1, pieces);
        if (p.Spawn)
        {
            int cu = spawnMacroX * MacroSize + MacroSize / 2 - p.X0, cv = spawnMacroZ * MacroSize + MacroSize / 2 - p.Z0;
            var room = (L0Piece.Spawn, Math.Max(2, cu - 8), Math.Max(2, cv - 7), Math.Min(W - 2, cu + 8), Math.Min(H - 2, cv + 7));
            pieces.RemoveAll(q => q.X0 <= room.Item4 + 1 && q.X1 >= room.Item2 - 1 && q.Z0 <= room.Item5 + 1 && q.Z1 >= room.Item3 - 1);
            pieces.Add(room);
            for (int v = room.Item3 - 1; v <= room.Item5 + 1; v++)
                for (int u = room.Item2 - 1; u <= room.Item4 + 1; u++)
                {
                    bool ring = u < room.Item2 || u > room.Item4 || v < room.Item3 || v > room.Item5;
                    if (ring) SetWall(ref p.At(u, v), p.Primary, BaseFor(p.Primary));
                    else p.At(u, v) = new Tile { Floor = p.At(u, v).Floor };
                }
        }
        // 1 inside a set piece, 2 its wall
        var piece = new byte[W * H];
        foreach (var q in pieces)
            for (int v = q.Z0 - 1; v <= q.Z1 + 1; v++)
                for (int u = q.X0 - 1; u <= q.X1 + 1; u++)
                    if (p.In(u, v)) piece[v * W + u] = (byte)(u < q.X0 || u > q.X1 || v < q.Z0 || v > q.Z1 ? Math.Max(piece[v * W + u], (byte)2) : 1);

        // Then the hallways, winding in from the gaps
        var force = new List<(int, int)>();
        var deadEnds = new List<(int U, int V, int DU, int DV)>();
        var worm = new short[W * H];
        var step = new int[W * H];
        double wormChance = p.Zone switch { ZoneKind.OpenOffice => 0.4, ZoneKind.Arches => 0.5, _ => 0.75 };
        short id = 0;
        foreach (var o in openings)
            if (p.Rng.Chance(wormChance)) Worm(p, o, ++id, worm, step, piece, force, deadEnds);
        // Hallways close in on both sides
        for (int v = 1; v < H; v++)
            for (int u = 1; u < W; u++)
            {
                if (worm[v * W + u] != 0 || piece[v * W + u] == 1) continue;
                bool beside = false;
                for (int dv = -1; dv <= 1 && !beside; dv++)
                    for (int du = -1; du <= 1; du++)
                        if (p.In(u + du, v + dv) && worm[(v + dv) * W + u + du] != 0) { beside = true; break; }
                if (beside && p.At(u, v).Kind != TileKind.Wall) SetWall(ref p.At(u, v), p.Primary, BaseFor(p.Primary));
            }

        // The set pieces
        var noDoor = new bool[W * H];
        foreach (var q in pieces)
        {
            switch (q.Kind)
            {
                case L0Piece.Big: case L0Piece.Spawn: PlanBigRoom(p, q.X0, q.Z0, q.X1, q.Z1); break;
                case L0Piece.Pits: PlanPitRoom(p, q.X0, q.Z0, q.X1, q.Z1); break;
                case L0Piece.CellRows:
                    PlanCellRows(p, q.X0, q.Z0, q.X1, q.Z1);
                    for (int v = q.Z0; v <= q.Z1; v++)
                        for (int u = q.X0; u <= q.X1; u++) noDoor[v * W + u] = true;
                    break;
            }
        }

        foreach (var o in openings) ClearGap(p, o);
        foreach ((int u, int v) in force) p.At(u, v).Kind = TileKind.Floor;
        if (p.Zone == ZoneKind.Arches) MendArches(p);

        // Scraps too small or too thin to be rooms are filled in
        int[] comp = LabComponents(p, out int count, out int[] size);
        var keep = new bool[count];
        foreach (var o in openings) if (comp[o.V * W + o.U] >= 0) keep[comp[o.V * W + o.U]] = true;
        foreach ((int u, int v) in force) if (comp[v * W + u] >= 0) keep[comp[v * W + u]] = true;
        var box = new (int U0, int V0, int U1, int V1)[count];
        for (int c = 0; c < count; c++) box[c] = (int.MaxValue, int.MaxValue, int.MinValue, int.MinValue);
        for (int n = 0; n < comp.Length; n++)
        {
            int c = comp[n];
            if (c < 0) continue;
            int u = n % W, v = n / W;
            box[c] = (Math.Min(box[c].U0, u), Math.Min(box[c].V0, v), Math.Max(box[c].U1, u), Math.Max(box[c].V1, v));
        }
        for (int n = 0; n < comp.Length; n++)
        {
            int c = comp[n];
            if (c < 0 || keep[c]) continue;
            if (size[c] < 6 || box[c].U0 == box[c].U1 || box[c].V0 == box[c].V1) SetWall(ref p.Tiles[n], p.Primary, BaseFor(p.Primary));
        }
        comp = LabComponents(p, out count, out size);

        // What each piece of floor is, for doorways and lights
        var hasHall = new bool[count];
        var inPiece = new bool[count];
        for (int n = 0; n < comp.Length; n++)
        {
            if (comp[n] < 0) continue;
            if (worm[n] != 0) hasHall[comp[n]] = true;
            if (piece[n] == 1) inPiece[comp[n]] = true;
        }
        LabConnect(p, comp, count, hasHall, inPiece, noDoor);

        // Rooms each get their own light, the odd one dark; blackout rooms flood
        var roomRng = new Rng(Hashing.Hash(seed, p.X0, p.Z0, SaltL0Block + 1));
        var moods = new LightMood[count];
        var water = new bool[count];
        for (int c = 0; c < count; c++)
        {
            moods[c] = RollMood(ref roomRng);
            water[c] = p.Zone == ZoneKind.Blackout && !hasHall[c] && !inPiece[c] && size[c] is >= 9 and <= 90 && roomRng.Chance(0.15);
        }
        for (int n = 0; n < comp.Length; n++)
        {
            int c = comp[n];
            if (c < 0 || hasHall[c] || inPiece[c]) continue;
            if (p.Zone == ZoneKind.Blackout)
            {
                if (water[c]) p.Tiles[n].Kind = TileKind.Water;
            }
            else p.Mood[n] = moods[c];
        }

        // A dead end: someone has chalked a cross on the wall facing back down the hallway
        foreach (var d in deadEnds)
        {
            if (!p.In(d.U + d.DU, d.V + d.DV) || p.At(d.U + d.DU, d.V + d.DV).Kind != TileKind.Wall || !p.Rng.Chance(0.4)) continue;
            ArchPier wall = d.DU > 0 ? ArchPier.East : d.DU < 0 ? ArchPier.West : d.DV > 0 ? ArchPier.South : ArchPier.North;
            if (p.At(d.U, d.V).Kind == TileKind.Floor) p.At(d.U, d.V).Chalk = ChalkBits.Make(wall, 2);
        }
        for (int n = W * H / 300; n >= 0; n--) Stain(p, p.Rng.Range(1, W - 1), p.Rng.Range(1, H - 1), p.Rng.Range(1, 3));
    }

    /// <summary>
    /// Splits the inclusive rectangle into rooms with straight walls, unbroken for now (the doorways come last). Some
    /// rooms are kept whole as set pieces.
    /// </summary>
    private static void LabSplit(L0Plan p, int x0, int z0, int x1, int z1, List<(L0Piece, int, int, int, int)> pieces)
    {
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        ref Rng rng = ref p.Rng;
        bool canSplitX = w >= 2 * MinRoom + 1 && h >= 3;
        bool canSplitZ = h >= 2 * MinRoom + 1 && w >= 3;
        int area = w * h;
        bool office = p.Zone == ZoneKind.OpenOffice;
        double stop = area <= 60 ? 0.85 : area <= 140 ? 0.5 : area <= 260 ? (office ? 0.6 : 0.25) : area <= 420 && office ? 0.4 : 0;
        if (!canSplitX && !canSplitZ || rng.Chance(stop))
        {
            LabLeaf(p, x0, z0, x1, z1, pieces);
            return;
        }

        bool splitX = canSplitX && (!canSplitZ || rng.Chance(w >= h ? 0.8 : 0.2));
        int len = splitX ? w : h;
        // A new wall may not end against a gap in the wall it meets, or it would half block it
        bool Solid(int x, int z) => !p.In(x, z) || p.At(x, z).Kind is TileKind.Wall or TileKind.ArchWindow;
        for (int attempt = 0; attempt < 4; attempt++)
        {
            int s = rng.Range(MinRoom, len - 1 - MinRoom);
            if (splitX ? !Solid(x0 + s, z0 - 1) || !Solid(x0 + s, z1 + 1) : !Solid(x0 - 1, z0 + s) || !Solid(x1 + 1, z0 + s)) continue;
            if (splitX)
            {
                LabWall(p, x0 + s, z0, alongZ: true, h);
                LabSplit(p, x0, z0, x0 + s - 1, z1, pieces);
                LabSplit(p, x0 + s + 1, z0, x1, z1, pieces);
            }
            else
            {
                LabWall(p, x0, z0 + s, alongZ: false, w);
                LabSplit(p, x0, z0, x1, z0 + s - 1, pieces);
                LabSplit(p, x0, z0 + s + 1, x1, z1, pieces);
            }
            return;
        }
        LabLeaf(p, x0, z0, x1, z1, pieces);
    }

    private static void LabLeaf(L0Plan p, int x0, int z0, int x1, int z1, List<(L0Piece, int, int, int, int)> pieces)
    {
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        ref Rng rng = ref p.Rng;
        double big = p.Zone switch { ZoneKind.OpenOffice => 0.8, ZoneKind.Lobby => 0.3, ZoneKind.Blackout => 0.15, _ => 0 };
        if (w * h >= 140 && Math.Min(w, h) >= 10 && rng.Chance(big))
        {
            // Pits are lethal, so they only appear in lit areas where they can be seen
            pieces.Add((p.PitsAllowed && rng.Chance(0.1) ? L0Piece.Pits : L0Piece.Big, x0, z0, x1, z1));
            return;
        }
        if (p.Zone is ZoneKind.Lobby or ZoneKind.OpenOffice && Math.Max(w, h) >= 14 && Math.Min(w, h) is >= 9 and <= 15 && rng.Chance(0.2))
            pieces.Add((L0Piece.CellRows, x0, z0, x1, z1));
    }

    /// <summary>A straight wall of length <paramref name="len"/> from (x, z). In arched areas, a row of arches with a pair or two open.</summary>
    private static void LabWall(L0Plan p, int x, int z, bool alongZ, int len)
    {
        ref Rng rng = ref p.Rng;
        if (p.Zone == ZoneKind.Arches)
        {
            var open = new bool[len];
            int gaps = len >= 16 && rng.Chance(0.5) ? 2 : 1;
            for (int n = 0; n < gaps; n++)
            {
                int start = rng.Range(0, Math.Max(0, len - 2));
                for (int k = start; k < Math.Min(len, start + 2); k++) open[k] = true;
            }
            ArchWall(p, x, z, !alongZ, open);
            return;
        }
        WallPattern pattern = RollPattern(ref rng, p.Primary);
        BaseStyle baseStyle = BaseFor(pattern);
        // Now and then a wall stops short, or is broken by a wide gap, so rooms run into each other round corners
        int gap0 = -1, gap1 = -1;
        if (len >= 8 && rng.Chance(0.22))
        {
            int width = rng.Range(3, Math.Min(7, len - 4));
            gap0 = rng.Chance(0.4) ? (rng.Chance(0.5) ? 0 : len - width) : rng.Range(2, len - width - 2);
            gap1 = gap0 + width - 1;
        }
        for (int k = 0; k < len; k++)
            if (k < gap0 || k > gap1) SetWall(ref p.At(alongZ ? x : x + k, alongZ ? z + k : z), pattern, baseStyle);
    }

    /// <summary>
    /// A hallway winding in from a gap: two wide (now and then three), running a few blocks, turning hard left or
    /// right, running on. It stops where it runs into another hallway, opens into a set piece, or just ends.
    /// </summary>
    private static void Worm(L0Plan p, (int U, int V, int DU, int DV) from, short id, short[] worm, int[] stepAt, byte[] piece,
        List<(int, int)> force, List<(int U, int V, int DU, int DV)> deadEnds)
    {
        ref Rng rng = ref p.Rng;
        int W = p.W, H = p.H;
        int w = rng.Chance(0.15) ? 3 : 2;
        int du = from.DU, dv = from.DV;
        // The head: a w by w block, by its north-west corner
        int hx = du < 0 ? from.U - w + 1 : from.U, hz = dv < 0 ? from.V - w + 1 : from.V;
        if (hx < 1 || hz < 1 || hx + w - 1 > W - 1 || hz + w - 1 > H - 1) return;
        LightMood mood = HallMood(ref rng);
        int steps = 0;

        void Carve()
        {
            for (int b = 0; b < w; b++)
                for (int a = 0; a < w; a++)
                {
                    int u = hx + a, v = hz + b, n = v * W + u;
                    if (worm[n] == 0) { worm[n] = id; stepAt[n] = steps; }
                    p.Tiles[n].Kind = TileKind.Floor;
                    p.Tiles[n].Variant = 0;
                    if (p.Zone != ZoneKind.Blackout) p.Mood[n] = mood;
                    byte lane = du != 0 ? (b == (w - 1) / 2 ? HallAlongX : HallSide) : (a == (w - 1) / 2 ? HallAlongZ : HallSide);
                    if (p.Hall[n] == HallNone || p.Hall[n] == HallSide && lane != HallSide) p.Hall[n] = lane;
                }
        }

        // What lies one step on: 0 clear, 1 the district's walls, 2 a set piece, 3 another hallway
        int Probe(int ddu, int ddv)
        {
            int result = 0;
            for (int k = 0; k < w; k++)
            {
                int u = ddu > 0 ? hx + w : ddu < 0 ? hx - 1 : hx + k;
                int v = ddv > 0 ? hz + w : ddv < 0 ? hz - 1 : hz + k;
                if (u < 1 || v < 1 || u > W - 1 || v > H - 1) return 1;
                int n = v * W + u;
                if (piece[n] != 0) result = Math.Max(result, 2);
                else if (worm[n] != 0 && (worm[n] != id || stepAt[n] < steps - 3 * w)) result = Math.Max(result, 3);
            }
            return result;
        }

        Carve();
        bool? lastLeft = null;
        int runs = rng.Range(2, 5);
        int len = rng.Range(3, 10); // in from the gap before the first turn
        for (int r = 0; ; r++)
        {
            for (int k = 0; k < len; k++)
            {
                int ahead = Probe(du, dv);
                if (ahead == 1) break;
                if (ahead == 2)
                {
                    // A hallway that opens into a big room
                    if (!rng.Chance(0.6)) break;
                    for (int m = 0; m < w; m++)
                    {
                        int u = du > 0 ? hx + w : du < 0 ? hx - 1 : hx + m;
                        int v = dv > 0 ? hz + w : dv < 0 ? hz - 1 : hz + m;
                        if (piece[v * W + u] == 2) force.Add((u, v));
                    }
                    return;
                }
                hx += du;
                hz += dv;
                steps++;
                Carve();
                if (ahead == 3) return; // joined another hallway
            }
            if (r >= runs) break;
            // Turn hard left or right, whichever way there is room; mostly the other way from last time, so the
            // hallway zigzags on rather than coiling round on itself
            bool left = lastLeft == null ? rng.Chance(0.5) : rng.Chance(0.75) ? !lastLeft.Value : lastLeft.Value, turned = false;
            for (int t = 0; t < 2 && !turned; t++)
            {
                bool l = left ^ (t == 1);
                int ndu = l ? dv : -dv, ndv = l ? -du : du;
                if (Probe(ndu, ndv) == 1) continue;
                du = ndu;
                dv = ndv;
                turned = true;
                lastLeft = l;
            }
            if (!turned) break;
            len = rng.Chance(0.15) ? rng.Range(17, 26) : rng.Range(6, 16);
        }
        int cu = du > 0 ? hx + w - 1 : du < 0 ? hx : hx + (w - 1) / 2;
        int cv = dv > 0 ? hz + w - 1 : dv < 0 ? hz : hz + (w - 1) / 2;
        deadEnds.Add((cu, cv, du, dv));
    }

    /// <summary>Most hallways are evenly lit; whole stretches have dim or failing lights, now and then one is dark.</summary>
    private static LightMood HallMood(ref Rng rng)
    {
        double r = rng.NextDouble();
        return r < 0.04 ? LightMood.Dark : r < 0.10 ? LightMood.Dim : r < 0.18 ? LightMood.Failing : LightMood.Normal;
    }

    /// <summary>
    /// Pieces of floor inside a district's walls that can be walked between without passing a wall: -1 for tiles
    /// that cannot be walked on.
    /// </summary>
    private static int[] LabComponents(L0Plan p, out int count, out int[] size)
    {
        int W = p.W, H = p.H;
        var comp = new int[W * H];
        Array.Fill(comp, -1);
        var sizes = new List<int>();
        var queue = new Queue<int>();
        for (int v0 = 1; v0 < H; v0++)
            for (int u0 = 1; u0 < W; u0++)
            {
                int start = v0 * W + u0;
                if (comp[start] >= 0 || !IsWalkable(p.Tiles[start])) continue;
                int c = sizes.Count, n = 0;
                comp[start] = c;
                queue.Enqueue(start);
                while (queue.Count > 0)
                {
                    int at = queue.Dequeue();
                    n++;
                    int u = at % W, v = at / W;
                    foreach ((int du, int dv) in Steps4)
                    {
                        int nu = u + du, nv = v + dv;
                        if (!p.Inner(nu, nv)) continue;
                        int next = nv * W + nu;
                        if (comp[next] >= 0 || !IsWalkable(p.Tiles[next])) continue;
                        comp[next] = c;
                        queue.Enqueue(next);
                    }
                }
                sizes.Add(n);
            }
        count = sizes.Count;
        size = sizes.ToArray();
        return comp;
    }

    private static readonly (int, int)[] Steps4 = { (1, 0), (-1, 0), (0, 1), (0, -1) };

    /// <summary>
    /// Joins every piece of floor in the district to the rest through doorless openings in the walls between them: one
    /// for each pair a spanning tree needs, and many more besides, most of all onto hallways and into big rooms, so
    /// that rooms open into rooms and there are always more ways than you need.
    /// </summary>
    private static void LabConnect(L0Plan p, int[] comp, int count, bool[] hasHall, bool[] inPiece, bool[] noDoor)
    {
        if (count == 0) return;
        int W = p.W, H = p.H;
        ref Rng rng = ref p.Rng;
        bool Arch(int u, int v) => p.In(u, v) && p.At(u, v).Kind is TileKind.ArchDoor or TileKind.ArchWindow;
        int Comp(int u, int v) => p.Inner(u, v) ? comp[v * W + u] : -1;

        // Each wall tile with different pieces of floor on opposite sides could be a doorway between them
        var pairs = new List<(int A, int B)>();
        var index = new Dictionary<(int, int), int>();
        var spots = new List<List<int>>();
        var candX = new int[W * H];
        var candZ = new int[W * H];
        for (int v = 1; v < H; v++)
            for (int u = 1; u < W; u++)
            {
                int n = v * W + u;
                if (p.Tiles[n].Kind != TileKind.Wall || noDoor[n] || Arch(u - 1, v) || Arch(u + 1, v) || Arch(u, v - 1) || Arch(u, v + 1)) continue;
                for (int axis = 0; axis < 2; axis++)
                {
                    int a = axis == 0 ? Comp(u - 1, v) : Comp(u, v - 1), b = axis == 0 ? Comp(u + 1, v) : Comp(u, v + 1);
                    if (a < 0 || b < 0 || a == b) continue;
                    var key = (Math.Min(a, b), Math.Max(a, b));
                    if (!index.TryGetValue(key, out int k))
                    {
                        k = pairs.Count;
                        index.Add(key, k);
                        pairs.Add(key);
                        spots.Add(new List<int>());
                    }
                    spots[k].Add(n * 2 + axis);
                    (axis == 0 ? candX : candZ)[n] = k + 1;
                }
            }

        var parent = new int[count];
        for (int c = 0; c < count; c++) parent[c] = c;
        int Find(int c) { while (parent[c] != c) c = parent[c] = parent[parent[c]]; return c; }

        void Door(int k)
        {
            int spot = spots[k][p.Rng.Range(0, spots[k].Count - 1)];
            int n = spot / 2, axis = spot % 2, u = n % W, v = n / W;
            p.Tiles[n].Kind = TileKind.Floor;
            // Two wide where the wall allows: the next tile along the wall, between the same two pieces
            if (p.Rng.Chance(0.15)) return;
            foreach (int s in new[] { 1, -1 })
            {
                int nu = axis == 0 ? u : u + s, nv = axis == 0 ? v + s : v;
                if (!p.Inner(nu, nv)) continue;
                int m = nv * W + nu;
                if ((axis == 0 ? candX : candZ)[m] == k + 1 && p.Tiles[m].Kind == TileKind.Wall) { p.Tiles[m].Kind = TileKind.Floor; return; }
            }
        }

        var order = new int[pairs.Count];
        for (int k = 0; k < order.Length; k++) order[k] = k;
        for (int k = order.Length - 1; k > 0; k--)
        {
            int m = rng.Range(0, k);
            (order[k], order[m]) = (order[m], order[k]);
        }
        foreach (int k in order)
        {
            var (a, b) = pairs[k];
            bool hall = hasHall[a] || hasHall[b], big = inPiece[a] || inPiece[b];
            if (Find(a) != Find(b))
            {
                parent[Find(a)] = Find(b);
                Door(k);
            }
            else if (rng.Chance(hall ? 0.5 : big ? 0.6 : p.Zone == ZoneKind.Arches ? 0.4 : 0.25)) Door(k);
            // A long wall onto a hallway or a big room gets a second way through, well along from the first
            if (spots[k].Count >= 16 && (hall || big) && rng.Chance(0.4)) Door(k);
        }

        // Anything still cut off (walls more than one thick between it and the rest) is broken through to the rest
        // along the way with the least wall in it
        for (int c = 0; c < count; c++)
        {
            if (Find(c) == Find(0)) continue;
            int start = Array.IndexOf(comp, c);
            var cost = new int[W * H];
            Array.Fill(cost, int.MaxValue);
            var from = new int[W * H];
            var deque = new LinkedList<int>();
            cost[start] = 0;
            from[start] = -1;
            deque.AddFirst(start);
            int reached = -1;
            while (deque.Count > 0)
            {
                int at = deque.First.Value;
                deque.RemoveFirst();
                if (comp[at] >= 0 && Find(comp[at]) == Find(0)) { reached = at; break; }
                int u = at % W, v = at / W;
                foreach ((int du, int dv) in Steps4)
                {
                    int nu = u + du, nv = v + dv;
                    if (!p.Inner(nu, nv)) continue;
                    int next = nv * W + nu, step = comp[next] >= 0 ? 0 : 1;
                    if (cost[at] + step >= cost[next]) continue;
                    cost[next] = cost[at] + step;
                    from[next] = at;
                    if (step == 0) deque.AddFirst(next); else deque.AddLast(next);
                }
            }
            if (reached < 0) continue;
            for (int at = reached; at >= 0; at = from[at])
            {
                if (comp[at] >= 0) { parent[Find(comp[at])] = Find(c); continue; }
                p.Tiles[at] = new Tile { Floor = p.Tiles[at].Floor };
            }
        }
    }

    /// <summary>Where a hallway cut through a row of arches, the half arches left hanging become plain wall.</summary>
    private static void MendArches(L0Plan p)
    {
        for (int pass = 0; pass < 2; pass++)
            for (int v = 0; v < p.H; v++)
                for (int u = 0; u < p.W; u++)
                {
                    ref Tile t = ref p.At(u, v);
                    if (t.Kind is not (TileKind.ArchDoor or TileKind.ArchWindow)) continue;
                    (int du, int dv) = t.Pier switch { ArchPier.West => (-1, 0), ArchPier.East => (1, 0), ArchPier.North => (0, -1), _ => (0, 1) };
                    bool pier = !p.In(u + du, v + dv) || p.At(u + du, v + dv).Kind == TileKind.Wall;
                    bool partner = !p.In(u - du, v - dv) || p.At(u - du, v - dv).Kind is TileKind.ArchDoor or TileKind.ArchWindow;
                    if (!pier || !partner) SetWall(ref t, WallPattern.Cream, BaseFor(WallPattern.Cream));
                }
    }

    /// <summary>Piers every third block with pairs of arched openings over half-height walls between them.</summary>
    private static void ArchWall(L0Plan u, int x, int z, bool alongX, bool[] open)
    {
        BaseStyle baseStyle = BaseFor(WallPattern.Cream);
        bool anyDoor = false;
        int len = open.Length;

        for (int pass = 0; pass < 2; pass++)
        {
            for (int k = 0; k < len; k++)
            {
                int phase = k % 3;
                ref Tile tile = ref u.At(alongX ? x + k : x, alongX ? z : z + k);
                // A lone opening at the very end would have no pier to rest on
                if (phase == 0 || (phase == 1 && k == len - 1))
                {
                    SetWall(ref tile, WallPattern.Cream, baseStyle);
                    continue;
                }

                // Second pass only runs when the first produced no walkable opening: force the first pair open
                bool door = open[k] || (pass == 1 && k <= 2);
                tile.Kind = door ? TileKind.ArchDoor : TileKind.ArchWindow;
                tile.Pattern = WallPattern.Cream;
                tile.Base = baseStyle;
                bool towardStart = phase == 1;
                tile.Pier = alongX ? (towardStart ? ArchPier.West : ArchPier.East) : (towardStart ? ArchPier.North : ArchPier.South);
                anyDoor |= door;
            }
            if (anyDoor || len < 3) break;
        }
    }

    /// <summary>A grid of 2x2 shafts with thin strips of carpet between them and a walkway around the edge.</summary>
    private static void PlanPitRoom(L0Plan u, int x0, int z0, int x1, int z1)
    {
        for (int z = z0 + 1; z < z1; z++)
            for (int x = x0 + 1; x < x1; x++)
                if ((x - x0 - 1) % 3 != 2 && (z - z0 - 1) % 3 != 2) u.At(x, z).Kind = TileKind.Pit;
        FillMood(u, x0, z0, x1, z1, LightMood.Half);
    }

    // ---- Big rooms: open carpet with partitions standing in it ----

    /// <summary>
    /// The photo: a big empty room, a partition wall or two standing free in it, now and then bent into an L, and the
    /// odd lone column. Nothing touches anything else, so nothing is ever closed off.
    /// </summary>
    private static void PlanBigRoom(L0Plan u, int x0, int z0, int x1, int z1)
    {
        ref Rng rng = ref u.Rng;
        bool Clear(int x, int z)
        {
            for (int dz = -1; dz <= 1; dz++)
                for (int dx = -1; dx <= 1; dx++)
                {
                    int nx = x + dx, nz = z + dz;
                    if (nx < x0 || nz < z0 || nx > x1 || nz > z1 || u.At(nx, nz).Kind != TileKind.Floor) return false;
                }
            return true;
        }
        bool Place(List<(int X, int Z)> tiles)
        {
            foreach ((int x, int z) in tiles) if (!Clear(x, z)) return false;
            WallPattern pattern = RollPattern(ref u.Rng, u.Primary);
            foreach ((int x, int z) in tiles) SetWall(ref u.At(x, z), pattern, BaseFor(pattern));
            return true;
        }

        int partitions = u.Spawn ? 1 : rng.Range(1, 3), placed = 0;
        for (int attempt = 0; attempt < 30 && placed < partitions; attempt++)
        {
            bool alongZ = rng.Chance(0.5);
            int span = alongZ ? z1 - z0 + 1 : x1 - x0 + 1;
            int len = rng.Range(5, Math.Max(5, Math.Min(12, span - 6)));
            int x = rng.Range(x0 + 2, x1 - 2), z = rng.Range(z0 + 2, z1 - 2);
            var tiles = new List<(int, int)>();
            for (int k = 0; k < len; k++) tiles.Add(alongZ ? (x, z + k) : (x + k, z));
            if (!u.Spawn && rng.Chance(0.2))
            {
                // An L: a short leg off the far end
                int leg = rng.Range(3, 6), dir = rng.Chance(0.5) ? 1 : -1;
                (int ex, int ez) = tiles[^1];
                for (int k = 1; k <= leg; k++) tiles.Add(alongZ ? (ex + k * dir, ez) : (ex, ez + k * dir));
            }
            if (Place(tiles)) placed++;
        }
        if (!u.Spawn && rng.Chance(0.3))
            for (int n = rng.Range(1, 2); n > 0; n--)
            {
                int x = rng.Range(x0 + 2, x1 - 2), z = rng.Range(z0 + 2, z1 - 2);
                Place(new List<(int, int)> { (x, z) });
            }

        if (!u.Spawn && u.Zone != ZoneKind.Blackout) MoodPatch(u, x0, z0, x1, z1);
        for (int n = 0; n < 2; n++) Stain(u, rng.Range(x0, x1), rng.Range(z0, z1), rng.Range(1, 3));
    }

    // ---- Rows of identical rooms ----

    /// <summary>
    /// A corridor down the length of the room with identical small rooms off it, every doorway in the same place.
    /// A deep one has rooms on both sides.
    /// </summary>
    private static void PlanCellRows(L0Plan u, int x0, int z0, int x1, int z1)
    {
        ref Rng rng = ref u.Rng;
        bool alongX = x1 - x0 >= z1 - z0; // the corridor runs along the longer side
        int a0 = alongX ? x0 : z0, a1 = alongX ? x1 : z1, c0 = alongX ? z0 : x0, c1 = alongX ? z1 : x1;
        ref Tile At(int a, int c) => ref u.At(alongX ? a : c, alongX ? c : a);
        int depth = c1 - c0 + 1;
        bool both = depth >= 12;
        int corridor = both ? c0 + (depth - 2) / 2 : rng.Chance(0.5) ? c0 : c1 - 1; // first of its two rows
        WallPattern pattern = u.Primary;
        BaseStyle baseStyle = BaseFor(pattern);
        int doorAt = rng.Range(1, 2); // where in each room's front its doorway is, the same for all
        int roomWidth = rng.Range(4, 5);

        void Rooms(int front, int back, int step)
        {
            // The wall between the corridor and the rooms, then partitions every roomWidth + 1 along it
            for (int a = a0; a <= a1; a++) SetWall(ref At(a, front), pattern, baseStyle);
            for (int a = a0 + roomWidth; a <= a1 - 2; a += roomWidth + 1)
                for (int c = front; c != back + step; c += step)
                    SetWall(ref At(a, c), pattern, baseStyle);
            for (int start = a0; start <= a1; start += roomWidth + 1)
            {
                int door = Math.Min(start + doorAt, a1);
                At(door, front).Kind = TileKind.Floor;
                int end = Math.Min(start + roomWidth - 1, a1);
                LightMood mood = u.Zone == ZoneKind.Blackout ? LightMood.Blackout : RollMood(ref u.Rng);
                for (int a = start; a <= end; a++)
                    for (int c = front + step; c != back + step; c += step)
                        if (At(a, c).Kind == TileKind.Floor) u.Mood[(alongX ? c : a) * u.W + (alongX ? a : c)] = mood;
            }
        }
        if (both || corridor == c0) Rooms(corridor + 2, c1, 1);
        if (both || corridor != c0) Rooms(corridor - 1, c0, -1);
    }

    // ---- Pillar halls ----

    /// <summary>
    /// A lattice of pillars over the whole hall, aligned across every district of the same area and carried on through
    /// into the next pillar hall, with some pillars missing.
    /// </summary>
    private void PlanPillars(L0Plan u)
    {
        Region region = u.Region;
        int spacing = region.PillarSpacing, size = region.PillarSize;
        for (int v = 0; v < u.H; v++)
        {
            for (int x = 0; x < u.W; x++)
            {
                ref Tile tile = ref u.At(x, v);
                if (tile.Kind != TileKind.Floor) continue;

                int gx = u.X0 + x - region.PillarPhaseX;
                int gz = u.Z0 + v - region.PillarPhaseZ;
                int pillarX = Hashing.FloorDiv(gx, spacing), pillarZ = Hashing.FloorDiv(gz, spacing);
                double r = Hashing.Unit(Hashing.Hash(seed, pillarX, pillarZ, SaltPillar));
                if (r < 0.06) continue; // missing pillar

                // A few pillars stand one block out of line
                int shiftX = r > 0.96 ? 1 : 0;
                int shiftZ = r > 0.93 && r <= 0.96 ? 1 : 0;
                int ix = Hashing.Mod(gx, spacing) - shiftX;
                int iz = Hashing.Mod(gz, spacing) - shiftZ;
                if (ix < 0 || iz < 0 || ix >= size || iz >= size) continue;
                if (region.PlusPillars && ix != 1 && iz != 1) continue;

                SetWall(ref tile, region.PrimaryPattern, BaseFor(region.PrimaryPattern));
            }
        }
    }

    /// <summary>For the layout harness: which district a block position lies in, and what it is.</summary>
    internal string DescribeLevel0(int gx, int gz)
    {
        int j = L0RowOf(gz), i = L0ColOf(gx, j);
        L0Plan p = L0PlanAt(i, j);
        int u = gx - p.X0, v = gz - p.Z0;
        return $"district {i},{j} {p.Zone}{(p.Pillars ? " pillars" : "")}{(p.Spawn ? " spawn" : "")} at {p.X0},{p.Z0} size {p.W}x{p.H} "
            + $"tile {u},{v} {p.At(u, v).Kind} hall {p.Hall[v * p.W + u]}";
    }

    /// <summary>For the layout harness: whether a block position is hallway (see <see cref="HallNone"/>), as planned.</summary>
    internal byte Level0HallAt(int gx, int gz)
    {
        int j = L0RowOf(gz);
        L0Plan p = L0PlanAt(L0ColOf(gx, j), j);
        return p.Hall[(gz - p.Z0) * p.W + gx - p.X0];
    }

    // ================= Cells =================

    /// <summary>An edge between two Level 0 cells: the plan as it runs along the line (or a Red Room's wall).</summary>
    private Edge Level0Edge(ref Rng rng, int mx, int mz, int nx, int nz, bool west)
    {
        if (IsRedRoom(mx, mz) || IsRedRoom(nx, nz))
        {
            // Cut off from the rest: one narrow way through each side
            var red = new Edge { Pattern = WallPattern.RedRoom, Base = BaseStyle.Baseboard };
            for (int i = 1; i < MacroSize; i++) red.Tiles[i] = EdgeTile.Wall;
            int gap = rng.Range(4, MacroSize - 6);
            red.Tiles[gap] = red.Tiles[gap + 1] = EdgeTile.Open;
            return red;
        }
        WallPattern pattern = RegionAt(mx, mz).PrimaryPattern;
        var edge = new Edge { Pattern = pattern, Base = BaseFor(pattern), Planned = true };
        bool[] walled = WalledNeighbours(0, mx, mz);
        for (int i = 1; i < MacroSize; i++)
        {
            Tile t = west ? L0TileAt(mx * MacroSize, mz * MacroSize + i) : L0TileAt(mx * MacroSize + i, mz * MacroSize);
            bool edgeHall = west ? EdgeHall(walled, 0, i) : EdgeHall(walled, i, 0);
            edge.Tiles[i] = IsWalkable(t) || edgeHall ? EdgeTile.Open : EdgeTile.Wall;
        }
        return edge;
    }

    private void BuildLevel0(Builder b, int mx, int mz, Edge west, Edge north)
    {
        b.Zone = ZoneAt(mx, mz);
        b.Primary = RegionAt(mx, mz).PrimaryPattern;

        var owner = new L0Plan[MacroSize * MacroSize];
        var rowOf = new int[MacroSize];
        for (int i = 0; i < MacroSize; i++) rowOf[i] = L0RowOf(mz * MacroSize + i);
        // A cell spans at most two rows of districts; the district each column of tiles falls in, for each
        var colOf = new Dictionary<int, int[]>();
        foreach (int j in rowOf)
        {
            if (colOf.ContainsKey(j)) continue;
            var cols = new int[MacroSize];
            for (int i = 0; i < MacroSize; i++) cols[i] = L0ColOf(mx * MacroSize + i, j);
            colOf.Add(j, cols);
        }
        CopyPlan(b, mx, mz, west, north, (gx, gz, index) =>
        {
            int j = rowOf[gz - mz * MacroSize];
            L0Plan u = L0PlanAt(colOf[j][gx - mx * MacroSize], j);
            int iu = gx - u.X0, iv = gz - u.Z0;
            b.Tiles[index] = u.At(iu, iv);
            b.Mood[index] = u.Mood[iv * u.W + iu];
            owner[index] = u;
        });

        CarveEdgeHall(b, mx, mz, west, north);
        bool red = IsRedRoom(mx, mz);
        if (IsManilaMacro(mx, mz)) BuildManila(b);
        if (red)
        {
            // Every wall red, the carpet stained dark, no light but the red lamps; and what others left behind
            for (int i = 0; i < b.Tiles.Length; i++)
            {
                ref Tile t = ref b.Tiles[i];
                b.Mood[i] = LightMood.Red;
                if (t.IsWallLike && t.Pattern <= WallPattern.Manila) { t.Pattern = WallPattern.RedRoom; t.Base = BaseStyle.Baseboard; }
                if (t.Kind == TileKind.Pit) t.Kind = TileKind.Floor;
                if (t.Kind == TileKind.Floor) { t.Floor = FloorKind.Stained; t.Chalk = 0; }
            }
            PlaceBoxNearWall(b);
            PlaceBoxNearWall(b);
        }
        else if (!IsManilaMacro(mx, mz)) PlaceStash(b, mx, mz);
        OpenRedRoomGaps(b, mx, mz, west, north);
        PlaceLights(b, mx, mz, owner);
        PlaceOutlets(b, mx, mz);
        if (b.IsSpawn)
        {
            PlaceSpawnBox(b);
            PlaceSpawnBox(b);
        }
        if (TouchesLevel(mx, mz, 1)) WearAway(b, mx, mz);
    }

    /// <summary>
    /// The one gap in each side of a Red Room must lead somewhere on both sides: from each, a way is broken through
    /// whatever of the plan stands behind it, until it reaches open floor.
    /// </summary>
    private void OpenRedRoomGaps(Builder b, int mx, int mz, Edge west, Edge north)
    {
        void Gaps(Edge edge, int x, int z, (int X, int Z) along, (int X, int Z) inward)
        {
            if (edge.Pattern != WallPattern.RedRoom || edge.Tall) return;
            for (int i = 1; i < MacroSize; i++)
                if (edge.Tiles[i] == EdgeTile.Open) BreakThrough(b, x + along.X * i, z + along.Z * i, inward);
        }
        Gaps(west, 1, 0, (0, 1), (1, 0));
        Gaps(north, 0, 1, (1, 0), (0, 1));
        if (IsRedRoom(mx, mz) || IsRedRoom(mx + 1, mz)) Gaps(GetEdge(mx + 1, mz, west: true), MacroSize - 1, 0, (0, 1), (-1, 0));
        if (IsRedRoom(mx, mz) || IsRedRoom(mx, mz + 1)) Gaps(GetEdge(mx, mz + 1, west: false), 0, MacroSize - 1, (1, 0), (0, -1));
    }

    /// <summary>Clears a straight way from (x, z) in a direction until it reaches floor that can be walked on.</summary>
    private static void BreakThrough(Builder b, int x, int z, (int X, int Z) step)
    {
        for (int n = 0; n < 12; n++, x += step.X, z += step.Z)
        {
            if (x < 0 || z < 0 || x >= MacroSize || z >= MacroSize) return;
            ref Tile t = ref b.At(x, z);
            if (IsWalkable(t)) return;
            if (t.Tall) return; // never through the wall of another level
            t.Kind = TileKind.Floor;
            t.Variant = 0;
            t.Outlet = false;
            t.SupplyBox = false;
        }
    }

    /// <summary>
    /// Next to Level 1 the Lobby starts to give way: carpet worn through to concrete and ceiling tiles missing,
    /// so walking out of Level 0 feels gradual.
    /// </summary>
    private void WearAway(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                double patch = Noise((mx * MacroSize + lx) / 5.0, (mz * MacroSize + lz) / 5.0, SaltOutlet + 9);
                if (tile.Kind == TileKind.Floor && patch > 0.15) tile.Floor = FloorKind.Concrete;
                if (!tile.IsWallLike && tile.Ceiling == CeilingKind.Tile && patch > 0.3) tile.Worn = true;
            }
        }
    }

    // ---- The Manila Room ----

    private static void BuildManila(Builder b)
    {
        const int outer0 = 11, outer1 = 22; // two-block-thick walls around an 8x8 room (13..20)
        // A walkway two wide all round it: whatever the room was set down across opens onto it, so nothing is cut off
        for (int z = outer0 - 2; z <= outer1 + 2; z++)
            for (int x = outer0 - 2; x <= outer1 + 2; x++)
            {
                ref Tile around = ref b.At(x, z);
                if (IsWalkable(around)) continue;
                around.Kind = TileKind.Floor;
                around.Variant = 0;
                around.Outlet = false;
            }
        for (int z = outer0; z <= outer1; z++)
        {
            for (int x = outer0; x <= outer1; x++)
            {
                bool wall = x <= outer0 + 1 || x >= outer1 - 1 || z <= outer0 + 1 || z >= outer1 - 1;
                ref Tile tile = ref b.At(x, z);
                tile = new Tile { Floor = FloorKind.Wood };
                if (wall) SetWall(ref tile, WallPattern.Manila, BaseStyle.Baseboard);
                b.Mood[TileIndex(x, z)] = LightMood.None;
            }
        }

        // A door in each wall, each leading out to the rooms round it
        const int mid = 16;
        foreach ((int x, int z) in new[] { (outer0, mid), (outer0 + 1, mid), (outer1, mid), (outer1 - 1, mid), (mid, outer0), (mid, outer0 + 1), (mid, outer1), (mid, outer1 - 1) })
        {
            b.At(x, z).Kind = TileKind.Doorway;
        }
        BreakThrough(b, outer0 - 1, mid, (-1, 0));
        BreakThrough(b, outer1 + 1, mid, (1, 0));
        BreakThrough(b, mid, outer0 - 1, (0, -1));
        BreakThrough(b, mid, outer1 + 1, (0, 1));

        // A table in the middle of the room, under a chandelier
        b.At(mid, mid).Ceiling = CeilingKind.Chandelier;
        b.At(mid, mid).Variant = Props.RoundTable;
        b.At(outer0 + 2, outer0 + 2).SupplyBox = true;
    }

    // ================= Details =================

    /// <summary>
    /// Ceiling lights. In the rooms, a lattice per area, so the spacing and the way the rows run shift when you cross
    /// into another; down the hallways, a row of panels along the middle, every other one lit.
    /// </summary>
    private void PlaceLights(Builder b, int mx, int mz, L0Plan[] owner)
    {
        Region cellRegion = RegionAt(mx, mz);
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int index = TileIndex(lx, lz);
                ref Tile tile = ref b.Tiles[index];
                LightMood mood = b.Mood[index];
                if (tile.IsWallLike || tile.Ceiling != CeilingKind.Tile || mood == LightMood.None) continue;

                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                L0Plan u = owner[index];
                Region region = u?.Region ?? cellRegion;
                byte hall = u == null ? HallNone : u.Hall[(gz - u.Z0) * u.W + gx - u.X0];
                bool fixture, emitter;
                if (hall == HallSide) continue;
                if (hall != HallNone)
                {
                    int along = hall == HallAlongX ? gx : gz;
                    fixture = Hashing.Mod(along, 4) == 0;
                    emitter = Hashing.Mod(along, 8) == 0;
                }
                else if (region.Lights == LightStyle.Grid)
                {
                    int x = gx - region.LightPhaseX, z = gz - region.LightPhaseZ, spacing = region.LightSpacing;
                    fixture = Hashing.Mod(x, spacing) == 0 && Hashing.Mod(z, spacing) == 0;
                    emitter = Hashing.Mod(Hashing.FloorDiv(x, spacing), 2) == 0 && Hashing.Mod(Hashing.FloorDiv(z, spacing), 2) == 0;
                }
                else
                {
                    // Strips of two panels, three blocks apart along the row, rows four blocks apart
                    int x = gx - region.LightPhaseX, z = gz - region.LightPhaseZ;
                    int along = region.LightRowsAlongX ? x : z;
                    int across = region.LightRowsAlongX ? z : x;
                    fixture = Hashing.Mod(along, 3) < 2 && Hashing.Mod(across, 4) == 0;
                    emitter = Hashing.Mod(along, 6) == 0 && Hashing.Mod(Hashing.FloorDiv(across, 4), 2) == 0;
                }
                if (!fixture) continue;
                CeilingKind working = emitter ? CeilingKind.LightOn : CeilingKind.LightLit;

                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltLight));
                tile.Ceiling = mood switch
                {
                    // Mostly working, some dead, a few never installed, the odd one failing
                    LightMood.Normal => r < 0.03 ? CeilingKind.Tile : r < 0.09 ? CeilingKind.LightOff : r < 0.11 ? CeilingKind.LightFlicker : working,
                    LightMood.Half => r < 0.5 ? working : CeilingKind.LightOff,
                    LightMood.Dim => r < 0.6 ? CeilingKind.LightOff : r < 0.85 ? CeilingKind.LightFlicker : working,
                    LightMood.Failing => r < 0.25 ? CeilingKind.LightOff : CeilingKind.LightFlicker,
                    LightMood.Dark => CeilingKind.LightOff,
                    LightMood.Red => r < 0.3 ? CeilingKind.LampRed : CeilingKind.Tile,
                    // Blackout zones: dead fixtures, and now and then one that still sputters
                    _ => r < 0.05 ? CeilingKind.LightOff : r < 0.08 ? CeilingKind.LightFlicker : CeilingKind.Tile,
                };
            }
        }
    }

    private void PlaceOutlets(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Wall || tile.Pattern is WallPattern.Cream or WallPattern.Manila) continue;
                if (Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltOutlet)) < 0.04) tile.Outlet = true;
            }
        }
    }

    private static void Stain(L0Plan u, int cx, int cz, int radius)
    {
        for (int z = cz - radius; z <= cz + radius; z++)
        {
            for (int x = cx - radius; x <= cx + radius; x++)
            {
                if (!u.In(x, z)) continue;
                int dx = x - cx, dz = z - cz;
                // Ragged edge
                if (dx * dx + dz * dz > radius * radius + u.Rng.Range(-1, 1)) continue;
                ref Tile tile = ref u.At(x, z);
                if (tile.Floor == FloorKind.Carpet) tile.Floor = FloorKind.Stained;
            }
        }
    }

    private static void PlaceBoxNearWall(Builder b)
    {
        for (int attempt = 0; attempt < 40; attempt++)
        {
            int x = b.Rng.Range(1, MacroSize - 2), z = b.Rng.Range(1, MacroSize - 2);
            ref Tile tile = ref b.At(x, z);
            if (tile.Kind != TileKind.Floor) continue;
            if (b.At(x + 1, z).Kind == TileKind.Wall || b.At(x - 1, z).Kind == TileKind.Wall
                || b.At(x, z + 1).Kind == TileKind.Wall || b.At(x, z - 1).Kind == TileKind.Wall)
            {
                tile.SupplyBox = true;
                return;
            }
        }
    }

    private static void FillMood(L0Plan u, int x0, int z0, int x1, int z1, LightMood mood)
    {
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
                u.Mood[z * u.W + x] = mood;
    }

    /// <summary>Most rooms are evenly lit; some are dim, some have failing lights, a few have gone dark.</summary>
    private static LightMood RollMood(ref Rng rng)
    {
        double r = rng.NextDouble();
        return r < 0.03 ? LightMood.Dark : r < 0.10 ? LightMood.Dim : r < 0.17 ? LightMood.Failing : LightMood.Normal;
    }

    /// <summary>Open areas have no rooms, so moods come in roughly round patches instead.</summary>
    private static void MoodPatch(L0Plan u, int x0, int z0, int x1, int z1)
    {
        LightMood mood = RollMood(ref u.Rng);
        if (mood == LightMood.Normal || u.Zone == ZoneKind.Blackout) return;
        int cx = u.Rng.Range(x0, x1), cz = u.Rng.Range(z0, z1), radius = u.Rng.Range(5, 10);
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
                if ((x - cx) * (x - cx) + (z - cz) * (z - cz) <= radius * radius) u.Mood[z * u.W + x] = mood;
    }
}
