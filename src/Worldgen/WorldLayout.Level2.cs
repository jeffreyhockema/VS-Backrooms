using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 2, "Pipe Dreams": long, dark concrete maintenance tunnels stretching for miles, lined with pipes along the
/// walls and the ceiling. Sparse caged lights in white or orange are wired in series, so a whole stretch of tunnel
/// is dark at once. It is hot, and food is scarce.
///
/// <para>The tunnels run on a lattice. Every <see cref="L2Pitch"/> * <see cref="L2MainEvery"/> blocks is a main
/// tunnel, three wide and unbroken, running straight on as far as anyone has followed it. Between the mains, one- and
/// two-wide service tunnels every <see cref="L2Pitch"/> blocks form a maze of their own: a tree with a few loops,
/// grown in from the mains, so many of them end blind. Where two mains cross there is sometimes a pump gallery, a
/// wider hall with machinery along its walls.</para>
///
/// <para>Now and then a steel door is set in a tunnel wall. Most are locked, or open onto a small storeroom of
/// shelves and a dead computer; a few, which look no different, open onto another level. Trolleys, toolboxes, wooden
/// boxes and the pieces of dismantled machines lie about the tunnels without much rhyme or reason.</para>
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL2Section = 0x2B01;
    private const ulong SaltL2Light = 0x2B02;
    private const ulong SaltL2Wall = 0x2B03;
    private const ulong SaltL2Door = 0x2B04;
    private const ulong SaltL2Line = 0x2B05;
    private const ulong SaltL2Tree = 0x2B06;
    private const ulong SaltL2Gallery = 0x2B07;
    /// <summary>The pump galleries' and tunnels' gauges, valves, tanks and old pumps (vanilla machinery).</summary>
    private const ulong SaltL2Fitting = 0x1E01;

    /// <summary>Distance between neighbouring tunnels of the lattice, each way.</summary>
    private const int L2Pitch = 16;
    /// <summary>Every this many tunnels is a main one.</summary>
    private const int L2MainEvery = 4;

    private int L2Line(int axis, int k) => k * L2Pitch + (int)(Hashing.Hash(seed, k, axis, SaltL2Line) % 5) - 2;

    private static bool L2Main(int k) => Hashing.Mod(k, L2MainEvery) == 0;

    private int L2Width(int axis, int k) => L2Main(k) ? 3 : Hashing.Unit(Hashing.Hash(seed, k, axis, SaltL2Line + 1)) < 0.4 ? 2 : 1;

    /// <summary>Which unit (the block between tunnels, with the tunnels on its low sides) a coordinate lies in, along an axis.</summary>
    private int L2UnitOf(int axis, int g)
    {
        int k = Hashing.FloorDiv(g, L2Pitch);
        while (g < L2Line(axis, k)) k--;
        while (g >= L2Line(axis, k + 1)) k++;
        return k;
    }

    private PlanCache<HashSet<(int, int, int)>> l2Trees;

    /// <summary>Whether a stretch of tunnel is there (see <see cref="PlanLatticeTree"/> for how stretches are named).</summary>
    private bool L2Stretch(int axis, int line, int index)
    {
        if (L2Main(line)) return true;
        int mcx = Hashing.FloorDiv(axis == 0 ? line : index, L2MainEvery), mcz = Hashing.FloorDiv(axis == 0 ? index : line, L2MainEvery);
        return (l2Trees ??= new PlanCache<HashSet<(int, int, int)>>(256, (x, z) => PlanLatticeTree(x, z, L2MainEvery, SaltL2Tree, 0.5, 0.25, 0.2)))
            .Get(mcx, mcz).Contains((axis, line, index));
    }

    /// <summary>What a block position is in the tunnels: rock, a tunnel running along an axis (with its stretch), a crossing, or a gallery.</summary>
    private enum L2Part : byte { Rock, AlongX, AlongZ, Crossing, Gallery }

    /// <summary>
    /// The tunnel plan at a block position: what it is, the stretch of tunnel it belongs to (as a hash, for the lights
    /// and leaks that go with the stretch), and where across the tunnel it lies (0 at the low side) of how wide.
    /// </summary>
    private (L2Part Part, ulong Stretch, int Across, int Width) L2At(int gx, int gz)
    {
        int kx = L2UnitOf(0, gx), kz = L2UnitOf(1, gz);
        int wx = L2Width(0, kx), wz = L2Width(1, kz);
        int ax = gx - L2Line(0, kx), az = gz - L2Line(1, kz);
        bool inX = ax < wx, inZ = az < wz; // in the band of the north-south tunnel kx, of the west-east tunnel kz
        if (L2InGallery(gx, gz)) return (L2Part.Gallery, Hashing.Hash(seed, kx, kz, SaltL2Gallery), 0, 0);
        if (inX && inZ)
        {
            bool open = L2Stretch(0, kx, kz) || L2Stretch(0, kx, kz - 1) || L2Stretch(1, kz, kx) || L2Stretch(1, kz, kx - 1);
            return open ? (L2Part.Crossing, Hashing.Hash(seed, kx, kz, SaltL2Section), 0, 0) : default;
        }
        if (inX && L2Stretch(0, kx, kz)) return (L2Part.AlongZ, Hashing.Hash(seed, kx * 2, kz, SaltL2Section), ax, wx);
        if (inZ && L2Stretch(1, kz, kx)) return (L2Part.AlongX, Hashing.Hash(seed, kz * 2 + 1, kx, SaltL2Section), az, wz);
        return default;
    }

    /// <summary>
    /// A pump gallery: at about one crossing of two mains in three, the main tunnel widens to seven blocks for
    /// sixteen either side of the crossing, along one of the two.
    /// </summary>
    private bool L2InGallery(int gx, int gz)
    {
        const int span = L2Pitch * L2MainEvery;
        int mx0 = Hashing.FloorDiv(gx + span / 2, span), mz0 = Hashing.FloorDiv(gz + span / 2, span); // nearest crossing of mains
        int kx = mx0 * L2MainEvery, kz = mz0 * L2MainEvery;
        ulong h = Hashing.Hash(seed, kx, kz, SaltL2Gallery);
        if (Hashing.Unit(h) >= 0.33) return false;
        int cx = L2Line(0, kx) + 1, cz = L2Line(1, kz) + 1; // middle of the crossing
        bool alongX = (h >> 32 & 1) == 0;
        int along = alongX ? gx - cx : gz - cz, across = alongX ? gz - cz : gx - cx;
        return Math.Abs(along) <= 16 && Math.Abs(across) <= 3;
    }

    private Edge Level2Edge(int mx, int mz, bool west)
    {
        var edge = new Edge { Pattern = WallPattern.Tunnel, Planned = true };
        bool[] walled = WalledNeighbours(2, mx, mz);
        for (int i = 1; i < MacroSize; i++)
        {
            int gx = west ? mx * MacroSize : mx * MacroSize + i, gz = west ? mz * MacroSize + i : mz * MacroSize;
            bool open = L2At(gx, gz).Part != L2Part.Rock || (west ? EdgeHall(walled, 0, i) : EdgeHall(walled, i, 0));
            edge.Tiles[i] = open ? EdgeTile.Open : EdgeTile.Wall;
        }
        return edge;
    }

    private void BuildLevel2(Builder b, int mx, int mz, Edge west, Edge north)
    {
        var open = new bool[MacroSize * MacroSize];
        var machineRoom = new bool[MacroSize * MacroSize];
        var storeroom = new bool[MacroSize * MacroSize];

        // Lay the tunnels down from the plan, with their pipes and their lights
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                tile.Floor = FloorKind.Concrete;
                if (lx == 0 && !west.Planned || lz == 0 && !north.Planned || tile.Tall) continue; // a wall between levels
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz, index = TileIndex(lx, lz);
                var at = L2At(gx, gz);
                if (at.Part == L2Part.Rock)
                {
                    if (tile.Kind == TileKind.Floor || lx == 0 || lz == 0) SetWall(ref tile, WallPattern.Tunnel, BaseStyle.Plain);
                    continue;
                }
                tile.Kind = TileKind.Floor;
                open[index] = true;
                if (at.Part == L2Part.Gallery) { machineRoom[index] = true; continue; }
                PipeAndLight(ref tile, at, gx, gz);
            }
        CarveEdgeHall(b, mx, mz, west, north);
        for (int i = 0; i < open.Length; i++) open[i] |= b.Tiles[i].Kind == TileKind.Floor;

        AddTunnelDoors(b, open, storeroom);
        DecorateTunnels(b, mx, mz, machineRoom, storeroom);
        // One locked steel door in forty is a door into the Hub (its own salt: nothing else moves)
        MarkHubDoorsInLevel2(b, mx, mz);
        // Now and then a tunnel ends in a wall that wasn't there a moment ago: Level ! (its own salt: nothing else moves)
        MarkRunFalseWall(b, mx, mz);
    }

    /// <summary>
    /// The pipes over a tunnel and its lights. Pipe bundles run the length of every tunnel, three side by side over a
    /// main, meeting at junction boxes over the crossings; some stretches leak. Caged fixtures hang down the middle,
    /// every eight blocks along a main and six along the rest; each stretch is one circuit wired in series, so it is
    /// all lit, all dead, or all failing, and all white or all orange.
    /// </summary>
    private void PipeAndLight(ref Tile tile, (L2Part Part, ulong Stretch, int Across, int Width) at, int gx, int gz)
    {
        double circuit = Hashing.Unit(at.Stretch), leaks = Hashing.Unit(at.Stretch << 20);
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL2Light));
        bool fixture;
        if (at.Part == L2Part.Crossing)
        {
            tile.Pipe = Pipes.Hub;
            fixture = false;
        }
        else
        {
            bool alongX = at.Part == L2Part.AlongX;
            bool leak = leaks < 0.15 && r < 0.3;
            tile.Pipe = alongX ? (leak ? Pipes.LeakX : Pipes.RunX) : (leak ? Pipes.LeakZ : Pipes.RunZ);
            int spacing = at.Width == 3 ? 8 : 6;
            fixture = at.Across == (at.Width - 1) / 2 && Hashing.Mod(alongX ? gx : gz, spacing) == 0;
        }
        if (!fixture) return;
        if (tile.Pipe == Pipes.LeakX) tile.Pipe = Pipes.RunX;
        if (tile.Pipe == Pipes.LeakZ) tile.Pipe = Pipes.RunZ;
        tile.Ceiling = circuit < 0.3 ? CeilingKind.LightOff
            : circuit < 0.4 ? (r < 0.7 ? CeilingKind.LightFlicker : CeilingKind.LightOff)
            : r < 0.05 ? CeilingKind.LightOff
            : ((at.Stretch >> 40) & 1) == 0 ? CeilingKind.LightWarm : CeilingKind.LightOn;
    }

    /// <summary>
    /// Steel doors in the tunnel walls. Each needs solid concrete behind it; where there is room for one, some open
    /// (a doorway) onto a storeroom three blocks square.
    /// </summary>
    private static void AddTunnelDoors(Builder b, bool[] open, bool[] storeroom)
    {
        ref Rng rng = ref b.Rng;
        bool Solid(int x, int z) => x >= 1 && z >= 1 && x < MacroSize - 1 && z < MacroSize - 1 && !open[TileIndex(x, z)] && b.At(x, z).Kind == TileKind.Wall;
        bool Tunnel(int x, int z) => x >= 1 && z >= 1 && x < MacroSize && z < MacroSize && open[TileIndex(x, z)] && b.At(x, z).Kind == TileKind.Floor;

        // Wall tiles with a tunnel on exactly one side, and what lies behind them
        var sites = new List<(int X, int Z, int Dx, int Dz, bool Room)>();
        for (int z = 3; z < MacroSize - 3; z++)
        {
            for (int x = 3; x < MacroSize - 3; x++)
            {
                if (!Solid(x, z)) continue;
                int sides = 0, dx = 0, dz = 0;
                foreach ((int sx, int sz) in Steps)
                {
                    if (!Tunnel(x + sx, z + sz)) continue;
                    sides++;
                    (dx, dz) = (-sx, -sz); // the way in, away from the tunnel
                }
                if (sides != 1 || !Solid(x + dx, z + dz) || !Solid(x - dz, z + dx) || !Solid(x + dz, z - dx)) continue;
                // Room for a storeroom: a 5x5 block of solid concrete behind the door (the room and its walls)
                bool room = true;
                for (int depth = 1; depth <= 5 && room; depth++)
                    for (int side = -2; side <= 2; side++)
                        if (!Solid(x + dx * depth + dz * side, z + dz * depth + dx * side)) { room = false; break; }
                sites.Add((x, z, dx, dz, room));
            }
        }

        var placed = new List<(int X, int Z)>();
        for (int n = rng.Range(0, 3); n > 0 && sites.Count > 0; n--)
        {
            var site = sites[rng.Range(0, sites.Count - 1)];
            bool crowded = false;
            foreach ((int px, int pz) in placed) crowded |= Math.Abs(px - site.X) + Math.Abs(pz - site.Z) < 8;
            if (crowded) continue;
            placed.Add((site.X, site.Z));

            ref Tile door = ref b.At(site.X, site.Z);
            door.Variant = 0;
            door.Pier = site.Dx > 0 ? ArchPier.West : site.Dx < 0 ? ArchPier.East : site.Dz > 0 ? ArchPier.North : ArchPier.South; // faces the tunnel
            if (site.Room && rng.Chance(0.45))
            {
                door.Kind = TileKind.Doorway;
                for (int depth = 1; depth <= 3; depth++)
                    for (int side = -1; side <= 1; side++)
                    {
                        int x = site.X + site.Dx * depth + site.Dz * side, z = site.Z + site.Dz * depth + site.Dx * side;
                        open[TileIndex(x, z)] = storeroom[TileIndex(x, z)] = true;
                        ref Tile t = ref b.At(x, z);
                        t.Kind = TileKind.Floor;
                        t.Variant = 0;
                        // One caged bulb in the middle; half of them are dead
                        if (depth == 2 && side == 0) t.Ceiling = rng.Chance(0.5) ? CeilingKind.LightWarm : CeilingKind.LightOff;
                    }
            }
            else door.Kind = TileKind.Door;
        }
    }

    private void DecorateTunnels(Builder b, int mx, int mz, bool[] machineRoom, bool[] storeroom)
    {
        bool InCell(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize;
        bool IsOpen(int x, int z) => InCell(x, z) && b.At(x, z).Kind != TileKind.Wall;
        bool IsWall(int x, int z) => InCell(x, z) && b.At(x, z).Kind == TileKind.Wall;

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL2Wall));
                double r2 = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL2Wall + 1));

                bool e = IsOpen(lx + 1, lz), w = IsOpen(lx - 1, lz), s = IsOpen(lx, lz + 1), n = IsOpen(lx, lz - 1);
                if (tile.Kind == TileKind.Wall)
                {
                    // Walls facing a tunnel: whole stretches carry continuous pipework (with the odd valve or riser
                    // on it); other stretches are machinery, brick, hazard signs or bare concrete
                    if (tile.Pattern == WallPattern.Tunnel && (e || w || s || n))
                    {
                        double stretch = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 10), Hashing.FloorDiv(gz, 10), SaltL2Wall + 2));
                        if (stretch < 0.7) tile.Variant = r < 0.08 ? Props.WallValve : r < 0.16 ? Props.WallRiser : Props.WallPipes;
                        else tile.Variant = r < 0.35 ? Props.WallMachinery : r < 0.6 ? Props.WallBrick : r < 0.7 ? Props.WallWarning : Props.WallPlain;
                    }
                    continue;
                }
                if (tile.Kind != TileKind.Floor) continue;

                if (storeroom[TileIndex(lx, lz)])
                {
                    // A storeroom: shelving along the walls, boxes and a toolbox, a desk with a computer nobody
                    // has switched on in years
                    if (!TryWallSide(IsWall, lx, lz, out ArchPier side)) continue;
                    if (r < 0.42) { tile.Variant = Props.Shelf; tile.Pier = side; }
                    else if (r < 0.54) { tile.Variant = Props.Desk; tile.Pier = OppositeSide(side); }
                    else if (r < 0.66) tile.Variant = Props.CardboardBoxes;
                    else if (r < 0.74) { tile.Variant = Props.Toolbox; tile.Pier = OppositeSide(side); }
                    else if (r < 0.8) tile.Stack = 1; // a wooden crate
                    continue;
                }

                int neighbours = (e ? 1 : 0) + (w ? 1 : 0) + (s ? 1 : 0) + (n ? 1 : 0);
                // Direction of the tunnel; in a 2-wide tunnel the other lane counts as a side, not a branch
                bool alongX = e && w && !(s && n) || (e ^ w) && !s && !n;
                bool alongZ = s && n && !(e && w) || (s ^ n) && !e && !w;
                int index = TileIndex(lx, lz);

                // Overhead pipe bundles follow every tunnel, meeting at junction boxes where tunnels turn or branch
                // (the tunnels of the plan have theirs already; this is for the galleries and the hallway round the edge)
                bool planned = tile.Pipe != 0;
                if (machineRoom[index])
                {
                    // Pipes only run along the walls of machine rooms
                    if (IsWall(lx, lz - 1) || IsWall(lx, lz + 1)) tile.Pipe = Pipes.RunX;
                    else if (IsWall(lx - 1, lz) || IsWall(lx + 1, lz)) tile.Pipe = Pipes.RunZ;
                }
                else if (planned)
                {
                }
                else if (alongX || alongZ)
                {
                    bool leak = r2 < 0.035;
                    tile.Pipe = alongX ? (leak ? Pipes.LeakX : Pipes.RunX) : (leak ? Pipes.LeakZ : Pipes.RunZ);
                }
                else
                {
                    tile.Pipe = Pipes.Hub;
                }

                // Fluorescent fixtures every 6 blocks along a tunnel, on circuits that fail by section
                bool fixture = planned ? false : alongX ? Hashing.Mod(gx, 6) == 0
                    : alongZ ? Hashing.Mod(gz, 6) == 0
                    : Hashing.Mod(gx, 6) == 0 && Hashing.Mod(gz, 6) == 0;
                if (fixture)
                {
                    if (tile.Pipe == Pipes.LeakX) tile.Pipe = Pipes.RunX;
                    if (tile.Pipe == Pipes.LeakZ) tile.Pipe = Pipes.RunZ;
                    ulong section = Hashing.Hash(seed, Hashing.FloorDiv(gx, 24), Hashing.FloorDiv(gz, 24), SaltL2Section);
                    double light = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL2Light));
                    if (Hashing.Unit(section) < 0.35) tile.Ceiling = light < 0.15 ? CeilingKind.LightFlicker : CeilingKind.LightOff;
                    else tile.Ceiling = light < 0.08 ? CeilingKind.LightOff : light < 0.13 ? CeilingKind.LightFlicker
                        : ((section >> 12) & 1) == 0 ? CeilingKind.LightWarm : CeilingKind.LightOn;
                }

                // Machine rooms are lined with cabinets; elsewhere drums in wider spots and forgotten supplies in dead ends
                if (machineRoom[index] && r > 0.35 && TryWallSide(IsWall, lx, lz, out ArchPier wall)
                    && SafeToBlock((x, z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z)), lx, lz))
                {
                    tile.Variant = Props.Cabinet;
                    tile.Pier = wall;
                }
                // (Only where it leaves the way past open, counting what already stands on the tiles round it)
                else if (neighbours >= 3 && r > 0.94 && SafeToBlock((x, z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z)), lx, lz))
                {
                    // Where a tunnel widens: an oil drum, a trolley, a toolbox, a wooden box, cardboard boxes
                    tile.Pier = (ArchPier)((int)(r2 * 4) & 3);
                    if (r > 0.975) tile.Variant = Props.Drum;
                    else if (r > 0.966) tile.Variant = Props.Trolley;
                    else if (r > 0.957) tile.Variant = Props.Toolbox;
                    else if (r > 0.949) tile.Stack = 1;
                    else tile.Variant = Props.CardboardBoxes;
                }
                // Pieces of a dismantled machine, kicked against the wall: nothing to stop anyone walking on
                else if (r2 > 0.985 && !machineRoom[index]) { tile.Variant = Props.MachineParts; tile.Pier = (ArchPier)((int)(r * 4) & 3); }
                // (Not on the cell's own edge rows, where the tunnel may run on into the next cell)
                else if (neighbours == 1 && r > 0.86 && lx > 0 && lz > 0 && lx < MacroSize - 1 && lz < MacroSize - 1) tile.SupplyBox = true;
                // Against the walls of a pump gallery, between its cabinets: gauge boards and valve manifolds on their
                // pipes, rusted pressure tanks, what is left of an old pump; and now and then a gauge board on a wall
                // of a wider tunnel (only its back third is solid, so the way past stays open)
                else if (tile.Variant == 0 && tile.Stack == 0 && !tile.SupplyBox && TryWallSide(IsWall, lx, lz, out ArchPier back))
                {
                    ulong h = Hashing.Hash(seed, gx, gz, SaltL2Fitting);
                    double fit = Hashing.Unit(h);
                    bool place = machineRoom[index] ? fit < 0.5 : neighbours >= 3 && fit < 0.02;
                    if (!place || !SafeToBlock((x, z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z)), lx, lz)) continue;
                    double kind = machineRoom[index] ? fit / 0.5 : 0;
                    tile.Pier = OppositeSide(back);
                    tile.Variant = kind < 0.55 ? Props.GaugeFrame : kind < 0.8 ? Props.PressureTank : Props.RustMachine;
                    tile.Stack = (byte)((h >> 24) % (tile.Variant == Props.GaugeFrame ? 4ul : 2ul));
                }
            }
        }
    }

    private static ArchPier OppositeSide(ArchPier side) => side switch
    {
        ArchPier.North => ArchPier.South,
        ArchPier.South => ArchPier.North,
        ArchPier.East => ArchPier.West,
        _ => ArchPier.East,
    };

    /// <summary>Finds a wall next to a tile, so props can stand against it.</summary>
    private static bool TryWallSide(Func<int, int, bool> isWall, int x, int z, out ArchPier side)
    {
        side = ArchPier.North;
        if (isWall(x, z - 1)) { side = ArchPier.North; return true; }
        if (isWall(x, z + 1)) { side = ArchPier.South; return true; }
        if (isWall(x - 1, z)) { side = ArchPier.West; return true; }
        if (isWall(x + 1, z)) { side = ArchPier.East; return true; }
        return false;
    }
}
