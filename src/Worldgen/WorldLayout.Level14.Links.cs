using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 14, "The Hospital"'s ways in and out (docs/design/experimental-levels/LINKS.md, "Level 14, the Hospital"; the level's
/// own file). Every value here is on the level's own salts (0x2980-0x29BF), so nothing else in a host level moves.
///
/// <list type="bullet">
/// <item><b>In, from Level 0</b> (Fandom: "a rare emergency exit door found in Level 0"): very rarely
/// (<see cref="L14ExitCellChance"/> of the Lobby's cells, in its outer two fifths, never two within
/// <see cref="L14ExitApart"/> cells) a grey steel hospital EMERGENCY EXIT door stands in a straight Lobby wall, a push bar
/// across it and a green running man lit over it, with clear carpet before it; the M.E.G. placard beside it from layout 12
/// (Level 0 is class 1, the Hospital class 4). Used: a reception room, one way.</item>
/// <item><b>In, from Level 15</b> (Fandom 15: "walking into a futuristic door labeled 'Medical Center' will send you to Level
/// 14"): one wing of Level 15 in <see cref="L14MedDoorShare"/> (never near its middle, where people are put down) has a
/// white door marked MEDICAL CENTER in the wall of one of its medical bays, best on the corridor beside the bay's own door.
/// Used: a reception room, one way. Laid by Level 15's own WorldLayout.Level15.Links.cs, which calls
/// <see cref="L14PlaceMedDoor"/> last of its links.</item>
/// <item><b>Out</b> (one wing in about thirty, never within 200 blocks of the region's middle, where everyone arrives): a
/// futuristic white door in a hall's or corridor's wall, a cool light strip round it (Fandom 14: "a rare futuristic-looking
/// door will lead one to Level 15"), used: a main hall of Level 15 beside a reinforced door that does not open; a red steel
/// exit door (Fandom 14: "a rare red exit door ... will lead to Level !"), used: a start room of Level !, the door slamming;
/// and (our invention, LINKS.md: Wikidot 73 names Level 14 as a way in with no detail, and Fandom 14 has "certain floor tiles
/// ... may collapse and give way unexpectedly") a patch of a corridor's floor sagging in its middle lane, cracked tiles round
/// it as the warning ("if there are any signs of instability, the best thing to do would be to run"): stood on, it gives way
/// and you fall out of the sky onto the Redlands, Level 73 (from layout version 16 a quarter as often: <see cref="L14CollapseShare"/>).
/// All one way.</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Layout salts of the level's links (from the level's own 0x2980-0x29BF).</summary>
    private const ulong SaltL14ExitCell = 0x2980, SaltL14ExitPick = 0x2981, SaltL14MedWing = 0x2982, SaltL14MedPick = 0x2983,
        SaltL14WayOut = 0x2984, SaltL14WayPick = 0x2985;

    /// <summary>
    /// The share of Level 0's cells drawn for an EMERGENCY EXIT door (in the Lobby's outer two fifths, and of any two
    /// drawn within <see cref="L14ExitApart"/> cells only the lower roll keeps it): a handful in the whole Lobby, kilometres
    /// apart (the progression rule: a way into a far more dangerous level, rarer than a quarter of layout 11's ways).
    /// </summary>
    public const double L14ExitCellChance = 1 / 1000.0;

    /// <summary>How many cells apart two Lobby cells drawn for an EMERGENCY EXIT must be (else the lower roll keeps it).</summary>
    public const int L14ExitApart = 16;

    /// <summary>The share of Level 15's wings with a MEDICAL CENTER door (if one of its medical bays has a wall for it), in worlds made before layout version 16.</summary>
    public const double L14MedDoorChance = 1 / 64.0;

    /// <summary>The shares of the Hospital's wings with a futuristic door, a red exit door, a floor that gives way (one in about thirty in all; the floor in worlds made before layout version 16).</summary>
    public const double L14FutureChance = 1 / 80.0, L14RedChance = 1 / 80.0, L14CollapseChance = 1 / 112.0;

    /// <summary>
    /// The share of Level 15's wings with a MEDICAL CENTER door in this world, and of the Hospital's wings with a floor that
    /// gives way: from layout version 16 a quarter of each, one in 256 and one in 448 (the progression rule, decision 20: a
    /// way from Level 3's side of the world into the Class 4 hospital, and from it onto the Class 5 island and so to Level 9,
    /// are shortcuts, a quarter as common; the kept ones are the same, the lowest rolls). The futuristic door back to Level 15
    /// and the red door to Level ! are not ways deeper and stay.
    /// </summary>
    public double L14MedDoorShare => Version >= 16 ? L14MedDoorChance / 4 : L14MedDoorChance;
    public double L14CollapseShare => Version >= 16 ? L14CollapseChance / 4 : L14CollapseChance;

    /// <summary>How far from the region's middle (blocks) the nearest way out may be: the reception rooms there are where everyone arrives.</summary>
    public const int L14WayOutClear = 200;

    /// <summary>A wing's way out (<see cref="L14Plan.WayOut"/>).</summary>
    public const byte L14WayNone = 0, L14WayFuture = 1, L14WayRed = 2, L14WayCollapse = 3;

    public sealed partial class L14Plan
    {
        /// <summary>The wing's way out (<see cref="L14WayFuture"/> ...): the door's wall tile, or the first tile of the sagging floor.</summary>
        public byte WayOut;
        public int WayA, WayB;
    }

    /// <summary>An EMERGENCY EXIT door into Level 14, in Level 0.</summary>
    public static bool IsL14ExitDoor(in Tile t) => t.Under == Unders.L14ExitDoor && t.Level == 0;

    /// <summary>A door marked MEDICAL CENTER, in Level 15.</summary>
    public static bool IsL14MedDoor(in Tile t) => t.Under == Unders.L14MedDoor && t.Level == Level15 && t.Kind == TileKind.Wall;

    /// <summary>A futuristic door to Level 15, in Level 14.</summary>
    public static bool IsL14FutureDoor(in Tile t) => t.Under == Unders.L14FutureDoor && t.Level == Level14 && t.Kind == TileKind.Wall;

    /// <summary>A red exit door to Level !, in Level 14.</summary>
    public static bool IsL14RedDoor(in Tile t) => t.Under == Unders.L14RedDoor && t.Level == Level14 && t.Kind == TileKind.Wall;

    /// <summary>A tile of sagging floor in Level 14 that gives way (to Level 73).</summary>
    public static bool IsL14Collapse(in Tile t) => t.Under == Unders.L14Collapse && t.Level == Level14 && t.Kind == TileKind.Floor;

    /// <summary>A tile of the cracked floor round one that gives way (the warning; it holds).</summary>
    public static bool IsL14Cracks(in Tile t) => t.Under == Unders.L14Cracks && t.Level == Level14 && t.Kind == TileKind.Floor;

    // ================= In: the EMERGENCY EXIT door, in Level 0 =================

    /// <summary>
    /// Whether a cell is drawn for an EMERGENCY EXIT door, by its hashes alone (the cell may have no wall for it): a Lobby cell
    /// in the outer two fifths of the level, at least 1500 blocks from spawn, never the spawn cell, a party nobody came to, a Red Room or the Manila Room.
    /// </summary>
    /// <summary>How near the world's spawn (in blocks) no EMERGENCY EXIT door into Level 14 may stand.</summary>
    public const int L14ExitMinFromSpawn = 1500;

    public bool L14ExitCell(int mx, int mz)
    {
        if (!ExpEntrances) return false;
        double r = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL14ExitCell));
        if (r >= L14ExitCellChance || LevelAt(mx, mz) != 0 || IsSpawnMacro(mx, mz)) return false;
        double angle = Math.Atan2(mz - spawnMacroZ, mx - spawnMacroX);
        if (RingDistance(mx, mz) < 0.6 * OuterEdge(0, angle)) return false;
        // Never within L14ExitMinFromSpawn blocks of the world's spawn (the cell's nearest block to the spawn cell's middle): a new
        // player must not walk into a Class 4 level a few hundred blocks from where they start
        int sx = spawnMacroX * MacroSize + MacroSize / 2, sz = spawnMacroZ * MacroSize + MacroSize / 2;
        double nx = Math.Clamp(sx, mx * MacroSize, mx * MacroSize + MacroSize - 1) - sx, nz = Math.Clamp(sz, mz * MacroSize, mz * MacroSize + MacroSize - 1) - sz;
        if (nx * nx + nz * nz < (double)L14ExitMinFromSpawn * L14ExitMinFromSpawn) return false;
        if (IsFunPartyCell(mx, mz) || IsRedRoom(mx, mz) || IsManilaMacro(mx, mz)) return false;
        // (Never two within a few cells of each other: the lower roll keeps it)
        for (int dz = -L14ExitApart; dz <= L14ExitApart; dz++)
            for (int dx = -L14ExitApart; dx <= L14ExitApart; dx++)
                if ((dx != 0 || dz != 0) && Hashing.Unit(Hashing.Hash(seed, mx + dx, mz + dz, SaltL14ExitCell)) is double o && o < L14ExitCellChance && o < r)
                    return false;
        return true;
    }

    /// <summary>
    /// The scaffold's hook (WorldLayout.ExpLinks.cs), for every cell of Levels 0-20, last of all (after the Basement's cracks
    /// and Level 73's): in a Lobby cell drawn for one, the EMERGENCY EXIT door in a straight wall, the wall going on past it
    /// both ways, clear carpet before it, and best with nothing open behind it (a door that leads nowhere in the Lobby); and
    /// from layout 12 the M.E.G. placard beside it. Nothing else in the cell changes.
    /// </summary>
    partial void L14Entrances(Builder b, int mx, int mz)
    {
        if (b.Level != 0 || b.IsSpawn || !L14ExitCell(mx, mz)) return;
        bool Wall(int x, int z) => x >= 1 && z >= 1 && x < MacroSize - 1 && z < MacroSize - 1
            && b.At(x, z) is { Kind: TileKind.Wall, Under: 0, Variant: 0, Tall: false };
        bool Clear(int x, int z) => x >= 1 && z >= 1 && x < MacroSize - 1 && z < MacroSize - 1
            && b.At(x, z) is { Kind: TileKind.Floor, Variant: 0, SupplyBox: false, Sealed: false, Stair: 0, Under: 0, Stack: 0 };
        bool Open(int x, int z) => x < 0 || z < 0 || x >= MacroSize || z >= MacroSize || b.At(x, z).Kind is not TileKind.Wall;
        var blind = new List<(int X, int Z, ArchPier Facing)>();
        var any = new List<(int X, int Z, ArchPier Facing)>();
        for (int z = 3; z < MacroSize - 3; z++)
            for (int x = 3; x < MacroSize - 3; x++)
                foreach (var (ax, az) in new[] { (1, 0), (0, 1) })
                {
                    if (!Wall(x, z) || !Wall(x - ax, z - az) || !Wall(x + ax, z + az)) continue;
                    foreach (int side in new[] { 1, -1 })
                    {
                        int fx = az * side, fz = ax * side; // the room's side, across the wall
                        // Clear carpet before it, and before the wall either side (where the placard goes)
                        if (!Clear(x + fx, z + fz) || !Clear(x + fx + ax, z + fz + az) && !Clear(x + fx - ax, z + fz - az)) continue;
                        (Open(x - fx, z - fz) ? any : blind).Add((x, z, Toward(fx, fz)));
                    }
                }
        var from = blind.Count > 0 ? blind : any;
        if (from.Count == 0) return;
        var (ex, ez, f) = from[(int)(Hashing.Hash(seed, mx, mz, SaltL14ExitPick) % (ulong)from.Count)];
        ref Tile door = ref b.At(ex, ez);
        door.Under = Unders.L14ExitDoor;
        door.Pier = f;
        if (Version >= 12)
        {
            var (dx, dz) = FacingStep(f);
            L14PlacardBeside(b, ex, ez, dx, dz);
        }
    }

    /// <summary>
    /// The M.E.G. placard beside the door: on the floor against the wall one or two along from it, facing the approach, as the
    /// host's own placards stand (PlaceShortcutPlacards), on a tile still free.
    /// </summary>
    private static void L14PlacardBeside(Builder b, int x, int z, int dx, int dz)
    {
        (int px, int pz) = (-dz, dx);
        foreach (int off in new[] { 1, -1, 2, -2 })
        {
            int wx = x + px * off, wz = z + pz * off, fx = wx + dx, fz = wz + dz;
            if (wx < 0 || wz < 0 || fx < 0 || fz < 0 || wx >= MacroSize || wz >= MacroSize || fx >= MacroSize || fz >= MacroSize) continue;
            if (b.At(wx, wz).Kind != TileKind.Wall || !FreeForPlacard(b.At(fx, fz)) || b.At(fx, fz).Sealed) continue;
            ref Tile t = ref b.At(fx, fz);
            t.Under = Unders.L14Placard;
            t.Pier = Toward(dx, dz);
            return;
        }
    }

    /// <summary>The EMERGENCY EXIT door in a cell of Level 0 (world position and the way it faces), if it has one (builds the cell).</summary>
    public (int X, int Z, ArchPier Facing)? L14ExitIn(int mx, int mz)
    {
        if (!L14ExitCell(mx, mz)) return null;
        Tile[] tiles = BuildMacro(mx, mz);
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
                if (IsL14ExitDoor(tiles[TileIndex(lx, lz)])) return (mx * MacroSize + lx, mz * MacroSize + lz, tiles[TileIndex(lx, lz)].Pier);
        return null;
    }

    /// <summary>The EMERGENCY EXIT doors nearest the world's spawn, out to <paramref name="maxRing"/> cells (nearest first).</summary>
    public List<(int X, int Z, ArchPier Facing)> L14NearestExits(int count, int maxRing = 3000)
    {
        var found = new List<(int X, int Z, ArchPier Facing)>();
        int cx = spawnMacroX, cz = spawnMacroZ, stopAt = int.MaxValue;
        for (int r = 1; r <= maxRing && r <= stopAt; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx += Math.Abs(dz) == r ? 1 : 2 * r)
                {
                    int mx = cx + dx, mz = cz + dz;
                    if (L14ExitIn(mx, mz) is not { } e) continue;
                    found.Add(e);
                    if (found.Count == count) stopAt = r + 40; // (a few rings on, for any nearer by straight line)
                }
        int sx = cx * MacroSize + MacroSize / 2, sz = cz * MacroSize + MacroSize / 2;
        found.Sort((a, b) => (Sq(a.X - sx) + Sq(a.Z - sz)).CompareTo(Sq(b.X - sx) + Sq(b.Z - sz)));
        return found.Count > count ? found.GetRange(0, count) : found;
        static long Sq(long v) => v * v;
    }

    // ================= In: the MEDICAL CENTER door, in Level 15 =================

    /// <summary>
    /// Called by Level 15's links (WorldLayout.Level15.Links.cs) last of all, for every wing of Level 15: in one wing in
    /// <see cref="L14MedDoorShare"/>, clear of the region's middle, a door marked MEDICAL CENTER in a medical bay's wall:
    /// best where it faces a corridor beside the bay's own door, else on the corridor anywhere along the bay, else inside the
    /// bay with the wall going on behind it. A plain wall tile with wall on with it either way, clear floor before it.
    /// </summary>
    private void L14PlaceMedDoor(L15Plan plan)
    {
        if (!ExpEntrances || !L14MedWingDrawn(plan.Hx, plan.Hz)) return;
        var (cx, cz) = plan.World(60, 60);
        if (Math.Abs(cx - L15CentreX * MacroSize) < 200 && Math.Abs(cz - L15CentreZ * MacroSize) < 200) return;
        const int n = L15WingSize;
        Tile At(int a, int b) => L15Plan.In(a, b) ? plan.AtAB(a, b) : default;
        static bool Clear(in Tile t) => t.Kind == TileKind.Floor && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Under == 0 && !t.Sealed;
        bool Medical(in Tile t) => t.Kind == TileKind.Floor && L15ZoneOf(t) == L15Zone.Medical;
        var found = new List<(int A, int B, ArchPier Face, int Score)>();
        int best = 0;
        for (int b = 0; b < n; b++)
            for (int a = 0; a < n; a++)
            {
                Tile w = At(a, b);
                if (w.Kind != TileKind.Wall || w.Under != 0 || w.Detail != L15WallPlain) continue;
                foreach (var (dx, dz) in FourSteps)
                {
                    // (dx, dz) toward the bay; the wall goes on along it both ways
                    if (!Medical(At(a + dx, b + dz))) continue;
                    int ax = dz, az = dx;
                    if (At(a + ax, b + az).Kind != TileKind.Wall || At(a - ax, b - az).Kind != TileKind.Wall) continue;
                    Tile outside = At(a - dx, b - dz);
                    int score;
                    ArchPier face;
                    if (Clear(outside) && L15ZoneOf(outside) is L15Zone.Corridor or L15Zone.Hall)
                    {
                        // On the corridor: beside the bay's own door (a doorway two or three along the same wall) is best
                        bool beside = false;
                        for (int k = 2; k <= 3; k++)
                            beside |= At(a + ax * k, b + az * k).Kind == TileKind.Doorway || At(a - ax * k, b - az * k).Kind == TileKind.Doorway;
                        score = beside ? 3 : 2;
                        face = Toward(-dx, -dz);
                    }
                    else if (Clear(At(a + dx, b + dz)) && outside.Kind == TileKind.Wall)
                    {
                        score = 1;
                        face = Toward(dx, dz);
                    }
                    else continue;
                    if (score < best || !L15PlanInLevel(plan, a - 1, b - 1, a + 1, b + 1)) continue;
                    if (score > best) { found.Clear(); best = score; }
                    found.Add((a, b, face, score));
                }
            }
        if (found.Count == 0) return;
        var pick = found[(int)(Hashing.Hash(seed, plan.Hx, plan.Hz, SaltL14MedPick) % (ulong)found.Count)];
        ref Tile door = ref plan.AtAB(pick.A, pick.B);
        door.Under = Unders.L14MedDoor;
        door.Pier = pick.Face;
    }

    /// <summary>Whether a wing of Level 15 is drawn for a MEDICAL CENTER door, by its hash alone (it may have no medical bay for it).</summary>
    public bool L14MedWingDrawn(int hx, int hz) => Hashing.Unit(Hashing.Hash(seed, hx, hz, SaltL14MedWing)) < L14MedDoorShare;

    /// <summary>The MEDICAL CENTER door in a wing of Level 15 (world position and the way it faces), if it has one.</summary>
    public (int X, int Z, ArchPier Facing)? L14MedDoorIn(int hx, int hz)
    {
        if (!L14MedWingDrawn(hx, hz)) return null;
        L15Plan plan = L15PlanOf(hx, hz);
        for (int b = 0; b < L15WingSize; b++)
            for (int a = 0; a < L15WingSize; a++)
                if (plan.AtAB(a, b).Under == Unders.L14MedDoor)
                {
                    var (x, z) = plan.World(a, b);
                    return (x, z, plan.AtAB(a, b).Pier);
                }
        return null;
    }

    /// <summary>The MEDICAL CENTER doors nearest a block position of Level 15 (by wings outward, up to <paramref name="reach"/> wings), nearest first.</summary>
    public List<(int X, int Z, ArchPier Facing)> L14MedDoorsNear(int gx, int gz, int count, int reach = 40)
    {
        var found = new List<(int X, int Z, ArchPier Facing)>();
        int hx0 = Hashing.FloorDiv(gx, L15Period), hz0 = Hashing.FloorDiv(gz, L15Period), stopAt = int.MaxValue;
        for (int r = 0; r <= reach && r <= stopAt; r++)
            for (int j = -r; j <= r; j++)
                for (int i = -r; i <= r; i++)
                {
                    if (Math.Max(Math.Abs(i), Math.Abs(j)) != r || L14MedDoorIn(hx0 + i, hz0 + j) is not { } d) continue;
                    if (LevelAt(MacroOf(d.X), MacroOf(d.Z)) != Level15 || !IsL14MedDoor(TileAt(d.X, d.Z))) continue;
                    found.Add(d);
                    if (found.Count == count) stopAt = r + 2;
                }
        found.Sort((a, b) => (Sq(a.X - gx) + Sq(a.Z - gz)).CompareTo(Sq(b.X - gx) + Sq(b.Z - gz)));
        return found.Count > count ? found.GetRange(0, count) : found;
        static long Sq(long v) => v * v;
    }

    // ================= Out: in Level 14 =================

    /// <summary>
    /// After a wing is planned (WorldLayout.Level14.cs): in one wing in about thirty, wholly inside the region and clear of
    /// its middle, a way out: a futuristic door, a red exit door, or a floor that gives way. On the level's own salts, after
    /// everything else in the wing.
    /// </summary>
    partial void L14LinkPlan(L14Plan plan)
    {
        double r = L14WayOutRoll(plan.Hx, plan.Hz);
        byte kind = r < L14FutureChance ? L14WayFuture : r < L14FutureChance + L14RedChance ? L14WayRed
            : r < L14FutureChance + L14RedChance + L14CollapseShare ? L14WayCollapse : L14WayNone;
        if (kind == L14WayNone || !L14WingInside(plan)) return;
        var rng = new Rng(Hashing.Hash(seed, plan.Hx, plan.Hz, SaltL14WayPick));
        if (kind == L14WayCollapse) L14PlaceCollapse(plan, ref rng);
        else L14PlaceDoorOut(plan, kind == L14WayFuture ? Unders.L14FutureDoor : Unders.L14RedDoor, kind, ref rng);
    }

    /// <summary>A wing's roll for a way out (below <see cref="L14FutureChance"/> a futuristic door, and so on; most wings have none).</summary>
    public double L14WayOutRoll(int hx, int hz) => Hashing.Unit(Hashing.Hash(seed, hx, hz, SaltL14WayOut));

    /// <summary>Whether a wing and the cells round it lie wholly in the level (a wing at the rim is cut by the edge's hallway).</summary>
    private bool L14WingInside(L14Plan plan)
    {
        var (x0, z0) = plan.World(-1, -1);
        var (x1, z1) = plan.World(L14WingSize, L14WingSize);
        for (int mz = MacroOf(z0) - 1; mz <= MacroOf(z1) + 1; mz++)
            for (int mx = MacroOf(x0) - 1; mx <= MacroOf(x1) + 1; mx++)
                if (LevelAt(mx, mz) != Level14) return false;
        return true;
    }

    /// <summary>
    /// A door out in a wall along a corridor, or in the wing's wall along a main hall: a wall tile with only the handrail on it,
    /// the wall going on either side, clear floor in front, at least <see cref="L14WayOutClear"/> blocks from the middle; best
    /// with solid wall behind it (the door shows on one side only), then something standing, then any room.
    /// </summary>
    private void L14PlaceDoorOut(L14Plan plan, ushort under, byte kind, ref Rng rng)
    {
        const int n = L14WingSize;
        Tile At(int a, int b) => L14Plan.In(a, b) ? plan.AtAB(a, b) : default;
        static bool Clear(in Tile t) => t.Kind == TileKind.Floor && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Under == 0;
        var found = new List<(int A, int B, ArchPier Face)>();
        int best = 0;
        for (int b = -1; b <= n; b++)
            for (int a = -1; a <= n; a++)
            {
                Tile w = At(a, b);
                if (w.Kind != TileKind.Wall || w.Under != 0 || w.Detail is not (L14DRail or L14DNone)) continue;
                bool rim = a is -1 or n || b is -1 or n;
                foreach (var (dx, dz) in FourSteps)
                {
                    // (dx, dz) the way it faces; the wall goes on along it both ways
                    int ax = dz, az = dx;
                    if (At(a + ax, b + az).Kind != TileKind.Wall || At(a - ax, b - az).Kind != TileKind.Wall) continue;
                    var (x, z) = plan.World(a, b);
                    if (L14FromMiddle(x, z) < L14WayOutClear) continue;
                    Tile behind;
                    if (rim)
                    {
                        // The wing's own wall, onto the main hall: only outward, and never where the hall has a thing against its wall
                        if (L14Plan.In(a + dx, b + dz)) continue;
                        if (Hashing.Unit(Hashing.Hash(seed, x + dx, z + dz, SaltL14HallProp)) < 0.03) continue;
                        behind = At(a - dx, b - dz);
                    }
                    else
                    {
                        Tile front = At(a + dx, b + dz);
                        if (!Clear(front) || L14ZoneOf(front) != L14Zone.Corridor) continue;
                        behind = At(a - dx, b - dz);
                        if (behind.Kind == TileKind.Floor && L14ZoneOf(behind) == L14Zone.Corridor) continue;
                    }
                    if (behind.Kind == TileKind.Doorway) continue;
                    int score = behind.Kind == TileKind.Wall ? 3 : behind.Kind == TileKind.Floor && (behind.Variant != 0 || behind.SupplyBox) ? 2 : 1;
                    if (score < best) continue;
                    if (score > best) { found.Clear(); best = score; }
                    found.Add((a, b, Toward(dx, dz)));
                }
            }
        if (found.Count == 0) return;
        var (pa, pb, face) = found[rng.Range(0, found.Count - 1)];
        ref Tile door = ref plan.AtAB(pa, pb);
        door.Under = under;
        door.Pier = face;
        door.Detail = L14DNone;
        plan.WayOut = kind;
        (plan.WayA, plan.WayB) = (pa, pb);
    }

    /// <summary>
    /// A patch of a corridor's floor that gives way: three wide (the corridor's width) and four long, on a straight stretch
    /// with wall either side; its middle lane sags for two tiles (<see cref="Unders.L14Collapse"/>), the tiles round it are
    /// cracked (<see cref="Unders.L14Cracks"/>), so there is a way past along either side, on the cracks.
    /// </summary>
    private void L14PlaceCollapse(L14Plan plan, ref Rng rng)
    {
        const int n = L14WingSize;
        Tile At(int a, int b) => L14Plan.In(a, b) ? plan.AtAB(a, b) : default;
        static bool Clear(in Tile t) => t.Kind == TileKind.Floor && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Under == 0
            && L14ZoneOf(t) == L14Zone.Corridor;
        var found = new List<(int A, int B, bool AlongZ)>();
        for (int b = 1; b < n - 1; b++)
            for (int a = 1; a < n - 1; a++)
                foreach (bool alongZ in new[] { true, false })
                {
                    // (a, b) the first sagging tile, in the middle lane; the patch runs one back and two on along the corridor
                    int ux = alongZ ? 0 : 1, uz = alongZ ? 1 : 0, sx = uz, sz = ux;
                    bool ok = true;
                    for (int k = -1; k <= 2 && ok; k++)
                    {
                        for (int s = -1; s <= 1 && ok; s++) ok = Clear(At(a + ux * k + sx * s, b + uz * k + sz * s));
                        // Wall either side: a straight stretch, not a crossing nor the mouth of another corridor
                        ok = ok && At(a + ux * k + sx * 2, b + uz * k + sz * 2).Kind == TileKind.Wall && At(a + ux * k - sx * 2, b + uz * k - sz * 2).Kind == TileKind.Wall;
                    }
                    if (!ok) continue;
                    var (x, z) = plan.World(a, b);
                    if (L14FromMiddle(x, z) < L14WayOutClear) continue;
                    found.Add((a, b, alongZ));
                }
        if (found.Count == 0) return;
        var (pa, pb, along) = found[rng.Range(0, found.Count - 1)];
        int vx = along ? 0 : 1, vz = along ? 1 : 0, wx = vz, wz = vx;
        for (int k = -1; k <= 2; k++)
            for (int s = -1; s <= 1; s++)
            {
                ref Tile t = ref plan.AtAB(pa + vx * k + wx * s, pb + vz * k + wz * s);
                t.Under = s == 0 && k is 0 or 1 ? Unders.L14Collapse : Unders.L14Cracks;
            }
        plan.WayOut = L14WayCollapse;
        (plan.WayA, plan.WayB) = (pa, pb);
    }

    /// <summary>
    /// The Hospital's ways out of a kind nearest a block position (by wings outward, up to <paramref name="reach"/> wings), nearest
    /// first: the door's wall tile (and the way it faces), or the first sagging tile (and the way the corridor runs).
    /// </summary>
    public List<(int X, int Z, ArchPier Facing)> L14WaysOutNear(byte kind, int gx, int gz, int count, int reach = 60)
    {
        var found = new List<(int X, int Z, ArchPier Facing)>();
        int hx0 = Hashing.FloorDiv(gx, L14Period), hz0 = Hashing.FloorDiv(gz, L14Period), stopAt = int.MaxValue;
        for (int r = 0; r <= reach && r <= stopAt; r++)
            for (int j = -r; j <= r; j++)
                for (int i = -r; i <= r; i++)
                {
                    if (Math.Max(Math.Abs(i), Math.Abs(j)) != r) continue;
                    // (The roll first: most wings have none, and their plans need not be made)
                    if (L14WayOutRoll(hx0 + i, hz0 + j) >= L14FutureChance + L14RedChance + L14CollapseChance) continue;
                    var (wx, wz) = (hx0 + i, hz0 + j);
                    if (LevelAt(MacroOf(wx * L14Period + 34), MacroOf(wz * L14Period + 34)) != Level14) continue;
                    L14Plan plan = L14PlanOf(wx, wz);
                    if (plan.WayOut != kind) continue;
                    var (x, z) = plan.World(plan.WayA, plan.WayB);
                    Tile t = plan.AtAB(plan.WayA, plan.WayB);
                    ArchPier face = t.Pier;
                    if (kind == L14WayCollapse) face = plan.AtAB(plan.WayA, plan.WayB + 1).Under == Unders.L14Collapse ? ArchPier.South : ArchPier.East;
                    found.Add((x, z, face));
                    if (found.Count == count) stopAt = r + 2;
                }
        found.Sort((a, b) => (Sq(a.X - gx) + Sq(a.Z - gz)).CompareTo(Sq(b.X - gx) + Sq(b.Z - gz)));
        return found.Count > count ? found.GetRange(0, count) : found;
        static long Sq(long v) => v * v;
    }

    /// <summary>The region's middle (blocks), where everyone arrives.</summary>
    public (int X, int Z) L14Middle => (L14CentreX * MacroSize + MacroSize / 2, L14CentreZ * MacroSize + MacroSize / 2);

    // ================= Showcase =================

    /// <summary>
    /// The showcase's spots for the links (computed from the layout): the EMERGENCY EXIT door nearest spawn in Level 0 and the
    /// MEDICAL CENTER door nearest Level 15's middle, each from a few steps in front; in Level 14 the futuristic door, the red
    /// exit door and the floor that gives way nearest the region's middle (the floor from along the corridor, looking down at it).
    /// </summary>
    public IEnumerable<Showcase.Spot> L14LinkShowcaseSpots(WorldGeometry geometry)
    {
        var spots = new List<Showcase.Spot>();
        void Before(string name, int level, int x, int z, ArchPier face, double pitch)
        {
            var (dx, dz) = FacingStep(face);
            // (Three steps back, else two: the first standing spot)
            for (int k = 3; k >= 2; k--)
            {
                Tile t = TileAt(x + dx * k, z + dz * k);
                if (t.Level != level || t.Kind != TileKind.Floor || t.Variant != 0 && !IsWalkThroughProp(t.Variant) || t.SupplyBox) continue;
                spots.Add(new Showcase.Spot(name, x + dx * k + 0.5, geometry.FloorFor(level) + 1, z + dz * k + 0.5, ShowcaseHeading(-dx, -dz), pitch));
                return;
            }
        }
        if (L14NearestExits(1) is { Count: > 0 } exits) Before("link-l0-exit", 0, exits[0].X, exits[0].Z, exits[0].Facing, 6);
        int c15x = L15CentreX * MacroSize + MacroSize / 2, c15z = L15CentreZ * MacroSize + MacroSize / 2;
        if (L14MedDoorsNear(c15x, c15z, 1) is { Count: > 0 } med) Before("link-l15-medical", Level15, med[0].X, med[0].Z, med[0].Facing, 6);
        var (mx, mz) = L14Middle;
        if (L14WaysOutNear(L14WayFuture, mx, mz, 1) is { Count: > 0 } future) Before("link-future", Level14, future[0].X, future[0].Z, future[0].Facing, 6);
        if (L14WaysOutNear(L14WayRed, mx, mz, 1) is { Count: > 0 } red) Before("link-red", Level14, red[0].X, red[0].Z, red[0].Facing, 6);
        if (L14WaysOutNear(L14WayCollapse, mx, mz, 1) is { Count: > 0 } collapse)
        {
            // From four tiles back along the corridor, in its middle lane, looking down at the patch
            var (cx, cz, run) = collapse[0];
            var (dx, dz) = FacingStep(run);
            spots.Add(new Showcase.Spot("link-collapse", cx - dx * 4 + 0.5, geometry.FloorFor(Level14) + 1, cz - dz * 4 + 0.5, ShowcaseHeading(dx, dz), -24));
        }
        return spots;
    }
}
