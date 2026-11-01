using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 52's ways in, in other levels, and the doors of its own that lead back (docs/design/experimental-levels/LINKS.md,
/// "Level 52"; the lore: Fandom's Greenfield Campus, "entering any sort of a high school building in Level 11", "emergency
/// exits or lifts in Levels 1-4"). Both are doors you walk through, so both are two-way: you come in through the doors of a
/// campus building, and those doors lead back.
///
/// <list type="bullet">
/// <item><b>The city (Level 11).</b> One lot in some hundreds, in midtown or the low-rise streets, is a high school: its lot
/// planned again over the top (its own salt, so no other lot moves) as a three- or four-storey brick building with a pair of
/// steel doors in the middle of its front and a sign over them, HIGH SCHOOL. Nothing else in the city says school. The doors
/// open into the lobby of a quad on (or near) Marshall David Campus, just inside its front doors.</item>
/// <item><b>The Abandoned Office (Level 4).</b> Now and then a steel door under a green EMERGENCY EXIT sign in an office wall
/// that has nothing behind it. It opens into the corridor at the end of a teaching block, just inside its end doors.</item>
/// <item><b>Back.</b> Those doors of the campus building (<see cref="Unders.L52QuadDoor"/>, <see cref="Unders.L52WingDoor"/>):
/// walk out through them and you are back where you came in. Every other door on the campus is only a door.</item>
/// </list>
///
/// The host tiles stay walls (nothing in the host's plan of ways and pockets changes); WorldGenerator.L52.Links.cs draws the
/// doors and the signs. Salts 0x2380-0x239F.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL52School = 0x2380, SaltL52SchoolPick = 0x2381, SaltL52SchoolStyle = 0x2382, SaltL52Exit = 0x2388, SaltL52ExitPick = 0x2389;

    /// <summary>
    /// The share of the city's blocks of lots (midtown and low-rise) that have a high school: about one lot in five hundred of
    /// those it could be, a walk of a kilometre or more from one to the next.
    /// </summary>
    public const double L52SchoolBlockChance = 1 / 80.0;

    /// <summary>
    /// The share of Level 4's cells drawn for an EMERGENCY EXIT door (about a third of them have a wall for one: the office is
    /// mostly open floor): some ten in the whole of Level 4 in a full-size world, a kilometre or more apart.
    /// </summary>
    public const double L52ExitCellChance = 1 / 500.0;

    // ================= Level 52's own doors that lead back =================

    /// <summary>
    /// Marks the campus's outside doors that can be a way back: the quad's front doors (a lobby inside) and the end doors of
    /// a standalone teaching block or hall of lodgings (its corridor inside). Never a courtyard's door, a hall's or a bridge's.
    /// </summary>
    private static void L52MarkWaysBack(L52Campus c)
    {
        for (int v = 0; v < c.D; v++)
            for (int u = 0; u < c.W; u++)
            {
                ref Tile e = ref c.At(u, v);
                if (e.Zone != (byte)L52Zone.Entrance || e.Kind != TileKind.Doorway || e.Detail == 0 || e.Detail > c.Buildings.Count) continue;
                L52Building b = c.Buildings[e.Detail - 1];
                if (b.Kind is not (L52BuildingKind.Teaching or L52BuildingKind.Lodging)) continue;
                var (ou, ov) = L52Step(e.Pier);
                if (!c.InGrid(u + ou, v + ov) || !c.InGrid(u - ou, v - ov)) continue;
                Tile front = c.At(u + ou, v + ov), back = c.At(u - ou, v - ov);
                if (front.Depth != 0 || front.Zone is (byte)L52Zone.Turf or (byte)L52Zone.Court) continue;
                bool quad = b.Index == 1;
                if (back.Zone != (byte)(quad ? L52Zone.Lobby : L52Zone.Corridor)) continue;
                e.Under = quad ? Unders.L52QuadDoor : Unders.L52WingDoor;
            }
    }

    /// <summary>A front door of a campus quad that can be a way back (to the city's high schools).</summary>
    public static bool IsL52QuadDoor(Tile t) => t.Level == Level52 && t.Under == Unders.L52QuadDoor;

    /// <summary>An end door of a campus's teaching block that can be a way back (to Level 4's emergency exits).</summary>
    public static bool IsL52WingDoor(Tile t) => t.Level == Level52 && t.Under == Unders.L52WingDoor;

    /// <summary>Somewhere to be put down just inside one of those doors: the lobby or the corridor, on the ground floor.</summary>
    public static bool IsL52InsideDoorSpot(Tile t) =>
        IsArrivalSpot(t) && t.Level == Level52 && t.Height == 0 && t.Depth > 0 && t.Zone is (byte)L52Zone.Lobby or (byte)L52Zone.Corridor;

    // ================= The ways in, in other levels =================

    /// <summary>A high school's front doors in the city.</summary>
    public static bool IsL52SchoolDoor(Tile t) => t.Level == 11 && t.Under == Unders.L52SchoolDoor;

    /// <summary>An EMERGENCY EXIT door in Level 4.</summary>
    public static bool IsL52ExitDoor(Tile t) => t.Level == 4 && t.Under == Unders.L52ExitDoor;

    /// <summary>Level 52's entrances in this cell of a host level (called once a cell, WorldLayout.ExpLinks.cs).</summary>
    partial void L52Entrances(Builder b, int mx, int mz)
    {
        if (b.Level == 11) L52MarkSchool(b, mx, mz);
        else if (b.Level == 4) L52MarkExit(b, mx, mz);
    }

    // ---- The city: a high school ----

    /// <summary>A high school's lot in a city block: its frame (block-local), which way it fronts, and the block's tiles with it planned in.</summary>
    public sealed class L52School
    {
        public int Bi, Bj, X0, X1, Z0, Z1;
        public bool FrontNorth;
        public Tile[] Tiles;
        /// <summary>The left of its two doors (world), as seen from the street, and the way they face.</summary>
        public int DoorX, DoorZ;
        public ArchPier Facing;
    }

    private PlanCache<L52School> l52Schools;

    /// <summary>Whether a city block (bi, bj) is one with a high school by its hash alone (cheap; the school may still not fit).</summary>
    private bool L52SchoolBlock(int bi, int bj) => Hashing.Unit(Hashing.Hash(seed, bi, bj, SaltL52School)) < L52SchoolBlockChance;

    /// <summary>The high school in a city block, or null.</summary>
    public L52School L52SchoolOf(int bi, int bj)
    {
        if (!ExpEntrances || !L52SchoolBlock(bi, bj)) return null;
        return System.Threading.LazyInitializer.EnsureInitialized(ref l52Schools, () => new PlanCache<L52School>(64, MakeL52School)).Get(bi, bj);
    }

    private static bool L52SchoolKind(CityKind k) =>
        k is CityKind.Apartment or CityKind.Office or CityKind.Diner or CityKind.Grocery or CityKind.Pharmacy or CityKind.Hardware
            or CityKind.Clothing or CityKind.Laundromat;

    /// <summary>Whether a cell of the city is laid out as city blocks (not the black glass rim, nor outside the city).</summary>
    private bool L52CityCell(int mx, int mz)
    {
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != 11) return false;
        return true;
    }

    private L52School MakeL52School(int bi, int bj)
    {
        District district = DistrictOf(bi, bj);
        if (district == District.Downtown || BlockKindOf(bi, bj, district) != CityBlock.Lots) return null;
        Tile[] plan = BlockPlan(bi, bj);
        int ox = CityOriginX + bi * AvePitch + AveWidth, oz = CityOriginZ + bj * StreetPitch + StreetWidth;
        // The lots along each half's street front: a run between two corners of one building, fronting the street
        var lots = new List<(int X0, int X1, int Half)>();
        for (int half = 0; half < 2; half++)
        {
            int front = half == 0 ? 0 : BlockD - 1, back = half == 0 ? AlleyZ - 1 : AlleyZ + 3;
            int x = 0;
            while (x < BlockW)
            {
                Tile a = plan[front * BlockW + x];
                if (a.Kind != TileKind.Wall || (a.Detail & CityDetail.Corner) == 0) { x++; continue; }
                int x1 = x + 1;
                while (x1 < BlockW && !(plan[front * BlockW + x1].Kind == TileKind.Wall && (plan[front * BlockW + x1].Detail & CityDetail.Corner) != 0)) x1++;
                if (x1 >= BlockW) break;
                int w = x1 - x + 1;
                bool ok = w >= 14 && w <= 30 && L52SchoolKind((CityKind)a.Zone);
                for (int z = Math.Min(front, back); z <= Math.Max(front, back) && ok; z++)
                    for (int xx = x; xx <= x1 && ok; xx++)
                    {
                        Tile t = plan[z * BlockW + xx];
                        ok = t.Under == 0 && t.Zone == a.Zone && t.Kind != TileKind.Pit;
                    }
                ok = ok && plan[back * BlockW + x].Kind == TileKind.Wall && plan[back * BlockW + x1].Kind == TileKind.Wall;
                // (Every cell it touches laid out as city, so none of it is the black glass rim)
                ok = ok && L52CityCell(MacroOf(ox + x), MacroOf(oz + Math.Min(front, back))) && L52CityCell(MacroOf(ox + x1), MacroOf(oz + Math.Max(front, back)))
                    && L52CityCell(MacroOf(ox + x1), MacroOf(oz + Math.Min(front, back))) && L52CityCell(MacroOf(ox + x), MacroOf(oz + Math.Max(front, back)));
                if (ok) lots.Add((x, x1, half));
                x = x1 + 1;
            }
        }
        if (lots.Count == 0) return null;
        ulong h = Hashing.Hash(seed, bi, bj, SaltL52SchoolPick);
        var (X0, X1, Half) = lots[(int)(h % (ulong)lots.Count)];
        bool north = Half == 0;
        int Z0 = north ? 0 : AlleyZ + 3, Z1 = north ? AlleyZ - 1 : BlockD - 1;
        var s = new L52School { Bi = bi, Bj = bj, X0 = X0, X1 = X1, Z0 = Z0, Z1 = Z1, FrontNorth = north, Tiles = (Tile[])plan.Clone() };

        // Brick (red or dark) or stone, three storeys or four
        ulong hs = Hashing.Hash(seed, bi, bj, SaltL52SchoolStyle);
        double r = Hashing.Unit(hs);
        WallPattern style = r < 0.5 ? WallPattern.CityBrick : r < 0.8 ? WallPattern.CityBrickDark : WallPattern.CityStone;
        byte height = (byte)(Hashing.Unit(Hashing.Mix(hs)) < 0.7 ? 12 : 16);
        int W = X1 - X0 + 1, D = Z1 - Z0 + 1;
        ref Tile At(int u, int v) => ref s.Tiles[(north ? Z0 + v : Z1 - v) * BlockW + (north ? X0 + u : X1 - u)];
        ArchPier facing = north ? ArchPier.North : ArchPier.South;
        for (int v = 0; v < D; v++)
            for (int u = 0; u < W; u++)
            {
                ref Tile t = ref At(u, v);
                int d = Math.Min(Math.Min(u, W - 1 - u), Math.Min(v, D - 1 - v));
                if (d == 0)
                {
                    // The outside wall as it was (its corners, and blank where it meets the next building), with no doors in it
                    t.Kind = TileKind.Wall;
                    t.Detail = (byte)(t.Detail & (CityDetail.Corner | CityDetail.Party));
                    t.Variant = 0;
                    t.Stack = 0;
                    t.Stair = 0;
                }
                else
                {
                    ushort keep = t.Overhead is Props.AcUnit or Props.WaterTank ? t.Overhead : (ushort)0;
                    t = new Tile { Kind = TileKind.Floor, Floor = t.Floor, Sealed = true, Pipe = (ushort)Math.Min(d, 3), Overhead = keep };
                }
                t.Pattern = style;
                t.Zone = (byte)CityKind.Sealed;
                t.Depth = height;
                t.Roof = 0;
                t.Under = 0;
            }
        // The doors in the middle of the front, the sign over them and the wall either side: parts 0-3 left to right from the street
        int mid = W / 2;
        for (int u = mid - 2; u <= mid + 1; u++)
        {
            ref Tile t = ref At(u, 0);
            t.Under = u == mid - 1 || u == mid ? Unders.L52SchoolDoor : Unders.L52SchoolSign;
            t.Variant = (ushort)(mid + 1 - u);
            t.Pier = facing;
            t.Detail = 0;
        }
        // (The left door as seen from the street: part 1)
        int lu = mid, lx = north ? X0 + lu : X1 - lu, lz = north ? Z0 : Z1;
        s.DoorX = ox + lx;
        s.DoorZ = oz + lz;
        s.Facing = facing;
        return s;
    }

    /// <summary>The city block (bi, bj) a world position is in, and its block-local position; false on a street or avenue.</summary>
    private bool L52CityBlockAt(int gx, int gz, out int bi, out int bj, out int x, out int z)
    {
        int ux = gx - CityOriginX, uz = gz - CityOriginZ;
        int ax = Hashing.Mod(ux, AvePitch), sz = Hashing.Mod(uz, StreetPitch);
        bi = Hashing.FloorDiv(ux, AvePitch);
        bj = Hashing.FloorDiv(uz, StreetPitch);
        x = ax - AveWidth;
        z = sz - StreetWidth;
        return ax >= AveWidth && sz >= StreetWidth;
    }

    /// <summary>The high school's tiles over this cell of the city, where a block it touches has one.</summary>
    private void L52MarkSchool(Builder b, int mx, int mz)
    {
        if (b.At(0, 0).Zone == (byte)CityKind.Rim) return;
        int gx0 = mx * MacroSize, gz0 = mz * MacroSize;
        // (A cell of 32 touches at most two blocks each way)
        var seen = new HashSet<(int, int)>();
        foreach (int dx in new[] { 0, MacroSize - 1 })
            foreach (int dz in new[] { 0, MacroSize - 1 })
            {
                int ux = gx0 + dx - CityOriginX, uz = gz0 + dz - CityOriginZ;
                seen.Add((Hashing.FloorDiv(ux, AvePitch), Hashing.FloorDiv(uz, StreetPitch)));
            }
        foreach (var (bi, bj) in seen)
        {
            L52School s = L52SchoolOf(bi, bj);
            if (s == null) continue;
            for (int lz = 0; lz < MacroSize; lz++)
                for (int lx = 0; lx < MacroSize; lx++)
                {
                    if (!L52CityBlockAt(gx0 + lx, gz0 + lz, out int i, out int j, out int x, out int z) || i != bi || j != bj) continue;
                    if (x < s.X0 || x > s.X1 || z < s.Z0 || z > s.Z1) continue;
                    ref Tile t = ref b.At(lx, lz);
                    if (t.Under >= 256) continue; // (another level's way in, laid first)
                    t = s.Tiles[z * BlockW + x];
                }
        }
    }

    // ---- The Abandoned Office: an EMERGENCY EXIT door ----

    /// <summary>Whether a cell of Level 4 is one that has an EMERGENCY EXIT door, by its hash alone (the cell may have no wall for it).</summary>
    public bool L52ExitCell(int mx, int mz)
    {
        if (!ExpEntrances) return false;
        double r = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL52Exit));
        if (r >= L52ExitCellChance) return false;
        // (Never two within a few cells of each other: the lower roll keeps it)
        for (int dz = -L52ExitApart; dz <= L52ExitApart; dz++)
            for (int dx = -L52ExitApart; dx <= L52ExitApart; dx++)
                if ((dx != 0 || dz != 0) && Hashing.Unit(Hashing.Hash(seed, mx + dx, mz + dz, SaltL52Exit)) is double o && o < L52ExitCellChance && o < r) return false;
        return true;
    }

    /// <summary>How many cells apart two cells drawn for an EMERGENCY EXIT must be (else the lower roll keeps it).</summary>
    private const int L52ExitApart = 8;

    /// <summary>
    /// A steel door in a straight office wall, the wall going on past it both ways, a clear floor in front of it, and (where
    /// the cell has one) nothing open behind it: a door that leads nowhere in the building. Nothing else in the cell changes.
    /// </summary>
    private void L52MarkExit(Builder b, int mx, int mz)
    {
        if (!L52ExitCell(mx, mz) || IsSpawnMacro(mx, mz)) return;
        bool Wall(int x, int z) => x >= 1 && z >= 1 && x < MacroSize - 1 && z < MacroSize - 1 && b.At(x, z) is { Kind: TileKind.Wall, Under: 0, Variant: 0, Tall: false }
            && b.At(x, z).Pattern is not (WallPattern.OfficeWindow or WallPattern.OfficeGlass or WallPattern.Hotel or WallPattern.Elevator);
        bool Clear(int x, int z) => x >= 1 && z >= 1 && x < MacroSize - 1 && z < MacroSize - 1
            && b.At(x, z) is { Kind: TileKind.Floor, Variant: 0, SupplyBox: false, Sealed: false, Stair: 0, Under: 0, Stack: 0 };
        bool Open(int x, int z) => x < 0 || z < 0 || x >= MacroSize || z >= MacroSize || b.At(x, z).Kind is TileKind.Floor or TileKind.Doorway or TileKind.Door;
        var blind = new List<(int X, int Z, ArchPier Facing)>();
        var any = new List<(int X, int Z, ArchPier Facing)>();
        for (int z = 2; z < MacroSize - 2; z++)
            for (int x = 2; x < MacroSize - 2; x++)
                foreach (var (ax, az) in new[] { (1, 0), (0, 1) })
                {
                    if (!Wall(x, z) || !Wall(x - ax, z - az) || !Wall(x + ax, z + az)) continue;
                    foreach (int side in new[] { 1, -1 })
                    {
                        int fx = az * side, fz = ax * side; // the room's side, across the wall
                        if (!Clear(x + fx, z + fz)) continue;
                        ArchPier facing = fx > 0 ? ArchPier.East : fx < 0 ? ArchPier.West : fz > 0 ? ArchPier.South : ArchPier.North;
                        (Open(x - fx, z - fz) ? any : blind).Add((x, z, facing));
                    }
                }
        var from = blind.Count > 0 ? blind : any;
        if (from.Count == 0) return;
        ulong h = Hashing.Hash(seed, mx, mz, SaltL52ExitPick);
        var (ex, ez, f) = from[(int)(h % (ulong)from.Count)];
        ref Tile door = ref b.At(ex, ez);
        door.Under = Unders.L52ExitDoor;
        door.Pier = f;
    }

    // ================= For the harness and the showcase =================

    /// <summary>The high schools in the city blocks within <paramref name="reach"/> blocks of a world position (nearest first).</summary>
    public List<L52School> L52SchoolsNear(int gx, int gz, int reach)
    {
        var found = new List<L52School>();
        int ci = Hashing.FloorDiv(gx - CityOriginX, AvePitch), cj = Hashing.FloorDiv(gz - CityOriginZ, StreetPitch);
        for (int j = cj - reach; j <= cj + reach; j++)
            for (int i = ci - reach; i <= ci + reach; i++)
            {
                if (!L52SchoolBlock(i, j)) continue;
                int cx = CityOriginX + i * AvePitch + AvePitch / 2, cz = CityOriginZ + j * StreetPitch + StreetPitch / 2;
                if (LevelAt(MacroOf(cx), MacroOf(cz)) != 11) continue;
                if (L52SchoolOf(i, j) is { } s) found.Add(s);
            }
        found.Sort((a, b) => (Sq(a.DoorX - gx) + Sq(a.DoorZ - gz)).CompareTo(Sq(b.DoorX - gx) + Sq(b.DoorZ - gz)));
        return found;
        static long Sq(long v) => v * v;
    }

    /// <summary>The world's spawn point (blocks), the middle of its cell.</summary>
    public (int X, int Z) L52SpawnBlock => (spawnMacroX * MacroSize + MacroSize / 2, spawnMacroZ * MacroSize + MacroSize / 2);

    /// <summary>
    /// The high schools nearest the world's spawn (the city's near edge is a long way out): those in the blocks round the
    /// point of the city nearest spawn, nearest spawn first.
    /// </summary>
    public List<L52School> L52NearestSchools(int count, int reach = 40)
    {
        var (sx, sz) = L52SpawnBlock;
        // The city's edge toward spawn: in from the circle's nearest point until the cells are city
        int mx = CityCentreX - CityRadius, mz = CityCentreZ;
        while (mx < CityCentreX && !L52CityCell(mx, mz)) mx++;
        var near = L52SchoolsNear(mx * MacroSize + 16 + 3 * AvePitch, mz * MacroSize, reach);
        near.Sort((a, b) => (Sq(a.DoorX - sx) + Sq(a.DoorZ - sz)).CompareTo(Sq(b.DoorX - sx) + Sq(b.DoorZ - sz)));
        return near.Count > count ? near.GetRange(0, count) : near;
        static long Sq(long v) => v * v;
    }

    /// <summary>The EMERGENCY EXIT doors nearest the world's spawn, out to <paramref name="maxRing"/> cells (nearest first).</summary>
    public List<(int X, int Z, ArchPier Facing)> L52NearestExits(int count, int maxRing = 8000)
    {
        var found = new List<(int X, int Z, ArchPier Facing)>();
        int cx = spawnMacroX, cz = spawnMacroZ, stopAt = int.MaxValue;
        for (int r = 1; r <= maxRing && r <= stopAt; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx += Math.Abs(dz) == r ? 1 : 2 * r)
                {
                    int mx = cx + dx, mz = cz + dz;
                    if (!L52ExitCell(mx, mz) || L52ExitIn(mx, mz) is not { } e) continue;
                    found.Add(e);
                    if (found.Count == count) stopAt = r + 40; // (a few rings on, for any nearer by straight line)
                }
        var (sx, sz) = L52SpawnBlock;
        found.Sort((a, b) => (Sq(a.X - sx) + Sq(a.Z - sz)).CompareTo(Sq(b.X - sx) + Sq(b.Z - sz)));
        return found.Count > count ? found.GetRange(0, count) : found;
        static long Sq(long v) => v * v;
    }

    /// <summary>The city's centre (cells) and radius, for the harness.</summary>
    public (int Mx, int Mz, int Radius) L52City => (CityCentreX, CityCentreZ, CityRadius);

    /// <summary>The EMERGENCY EXIT door in a cell of Level 4 (world position and the way it faces), if it has one.</summary>
    public (int X, int Z, ArchPier Facing)? L52ExitIn(int mx, int mz)
    {
        if (LevelAt(mx, mz) != 4 || !L52ExitCell(mx, mz)) return null;
        Tile[] tiles = BuildMacro(mx, mz);
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
                if (tiles[TileIndex(lx, lz)].Under == Unders.L52ExitDoor) return (mx * MacroSize + lx, mz * MacroSize + lz, tiles[TileIndex(lx, lz)].Pier);
        return null;
    }
}
