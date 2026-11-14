using System;
using System.Collections.Generic;
using System.Threading;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 15, "Futuristic Halls"'s links (docs/design/experimental-levels/LINKS.md, "Level 15"; the level's own file). The level
/// is "extremely hard to get into and out of": every way is one-way, and every one is rare.
///
/// <list type="bullet">
/// <item><b>In, from Level 10</b> (Wikidot, Enric; Fandom): now and then an immense white wall of Level 15's own panels rises
/// across the fields, ten blocks high and nearly four hundred long, between two of the farm roads, so that from its door it
/// runs out of sight both ways into the haze; one small reinforced door in one face, lit jambs and a lit lintel round it, a
/// tread plate before it. At most one to a square of the fields 2048 blocks a side (<see cref="L15WallLattice"/>), and only
/// where all of it lies on crops, stubble or meadow clear of the trees. Its own salt; nothing else in the fields moves.</item>
/// <item><b>In, from Level 3</b> (Fandom: "opening numerous doors in Level 3 has, in rare instances, led to Level 15"; the
/// shock from a door handle is its first entrance): about one cell in fifteen hundred has a steel door set in a straight wall
/// where no door should be, cold white light under it.</item>
/// <item><b>Where those come out</b>: in a lit main hall, beside one of the reinforced doors in the halls' walls that do not
/// open (one in most wings: <see cref="L15Plan.HasSealed"/>).</item>
/// <item><b>Out</b> (Fandom; all one-way, and rare: one wing in about sixty-four has each, and from layout 16's balance (every world: ExpVersion) one in
/// 256 the pane and the stairs, the ways deeper): a control room whose ESCAPE panel works (pressed, the locked gateway in the
/// room's side wall rolls up onto the dark, and through it is Level 3); a machine room's pane of thick glass with a street's
/// orange light behind it (broken, or climbed through once broken: Level 11); an office out of place, Level 4's carpet and
/// filing cabinets, with a staircase going down through its floor (Level 4).</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL15Wall10 = 0x2780, SaltL15Door3 = 0x2781, SaltL15SealedDoor = 0x2782, SaltL15Exit = 0x2783, SaltL15ExitPick = 0x2784,
        SaltL15Arrive = 0x2785;

    /// <summary>The side of a square of Level 10 that holds at most one white wall.</summary>
    public const int L15WallLattice = 2048;

    /// <summary>The white wall's top (rel; Level 10's band ends there) and how far clear of a farm road its ends stop.</summary>
    public const int L15WallTop = 10, L15WallEndClear = 16;

    /// <summary>
    /// How often: a square of the fields has a wall (if one fits: about half do); a cell of Level 3 has a door to Level 15;
    /// a wing of Level 15 has a way out (each of the three a third of it; from layout 16's balance (every world: ExpVersion) the pane and the stairs a
    /// quarter of their third: <see cref="L15PlaceExit"/>).
    /// </summary>
    private const double L15WallChance = 0.5, L15Door3Chance = 1 / 1500.0, L15ExitChance = 3 / 64.0;

    /// <summary>A white wall's dress (<see cref="Tile.Detail"/> of a <see cref="Unders.L15Wall10"/> tile): a steel pilaster, a door's lit jamb.</summary>
    public const byte L15WallPilasterBit = 1, L15WallJambBit = 2;

    /// <summary>A wing's way out (<see cref="L15Plan.Exit"/>).</summary>
    public const byte L15ExitNone = 0, L15ExitEscape = 1, L15ExitWindow = 2, L15ExitStairs = 3;

    /// <summary>The office staircase: six steps down, then a landing (<see cref="Tile.Stack"/> 1-7 of a <see cref="Unders.L15Stairs"/> tile).</summary>
    public const int L15StairSteps = 6;

    // ================= Level 10: the white wall =================

    /// <summary>A white wall in the fields of Level 10 (Valid false where its square has none).</summary>
    public sealed class L15WallSite
    {
        public bool Valid;
        /// <summary>Whether it runs along x (its faces north and south) or along z (west and east).</summary>
        public bool AlongX;
        /// <summary>Its first row (z when it runs along x, else x); the second is Line + 1.</summary>
        public int Line;
        /// <summary>Its ends and its door, along the way it runs.</summary>
        public int From, To, Door;
        /// <summary>Whether the door is in the second row's face (south or east) rather than the first's (north or west).</summary>
        public bool DoorFar;

        /// <summary>The door's block position, and the way it faces.</summary>
        public (int X, int Z) DoorAt => AlongX ? (Door, DoorFar ? Line + 1 : Line) : (DoorFar ? Line + 1 : Line, Door);
        public ArchPier DoorFace => AlongX ? (DoorFar ? ArchPier.South : ArchPier.North) : (DoorFar ? ArchPier.East : ArchPier.West);
    }

    private PlanCache<L15WallSite> l15Walls;

    /// <summary>The white wall of a square of the fields (Valid false if it has none).</summary>
    public L15WallSite L15WallAt(int i, int j) =>
        LazyInitializer.EnsureInitialized(ref l15Walls, () => new PlanCache<L15WallSite>(64, PlanL15Wall)).Get(i, j);

    /// <summary>The square of the fields a block position lies in.</summary>
    public static (int I, int J) L15WallSquare(int gx, int gz) => (Hashing.FloorDiv(gx, L15WallLattice), Hashing.FloorDiv(gz, L15WallLattice));

    private L15WallSite PlanL15Wall(int i, int j)
    {
        var site = new L15WallSite();
        if (!ExpEntrances) return site;
        ulong h = Hashing.Hash(seed, i, j, SaltL15Wall10);
        if (Hashing.Unit(h) >= L15WallChance) return site;
        const int S = L15WallLattice, G = FarmRoadGrid;
        // (Most squares are no part of Level 10: ask that first)
        if (LevelAt(MacroOf(i * S + S / 2), MacroOf(j * S + S / 2)) != 10 && LevelAt(MacroOf(i * S + 300), MacroOf(j * S + 300)) != 10
            && LevelAt(MacroOf(i * S + S - 300), MacroOf(j * S + S - 300)) != 10) return site;
        for (int attempt = 0; attempt < 8; attempt++)
        {
            ulong k = Hashing.Mix(h + (ulong)attempt * 0x9E3779B97F4A7C15UL);
            bool alongX = (k & 1) == 0;
            int pa = (alongX ? i : j) * S + 300 + (int)(Hashing.Unit(Hashing.Mix(k + 1)) * (S - 600)); // along the way it runs
            int pc = (alongX ? j : i) * S + 300 + (int)(Hashing.Unit(Hashing.Mix(k + 2)) * (S - 600)); // across it
            // Its rows in the middle of a block of the roads that run its way (well clear of them, however they wander)...
            int wander = (int)Math.Round(40 * Noise(pa / 150.0, 0.5, alongX ? SaltL10Road : SaltL10Road + 1));
            int line = Hashing.FloorDiv(pc - wander, G) * G + wander + G / 2 + (int)(Hashing.Mix(k + 3) % 61) - 30;
            // ...and its ends just short of the roads that cross its way, which at its row lie at fixed places
            int cross = (int)Math.Round(40 * Noise(line / 150.0, 0.5, alongX ? SaltL10Road + 1 : SaltL10Road));
            int road = Hashing.FloorDiv(pa - cross, G) * G + cross;
            int from = road + 4 + L15WallEndClear, to = road + G - 1 - L15WallEndClear;
            int door = (from + to) / 2 + (int)(Hashing.Mix(k + 4) % 121) - 60;
            // The door between two pilasters, its jambs clear of them
            while (Hashing.Mod(door, 8) is 0 or 1 or 7) door++;
            var candidate = new L15WallSite { AlongX = alongX, Line = line, From = from, To = to, Door = door, DoorFar = (Hashing.Mix(k + 5) & 1) == 1 };
            if (!L15WallFits(candidate)) continue;
            candidate.Valid = true;
            return candidate;
        }
        return site;
    }

    /// <summary>
    /// Whether a wall can stand where it is planned: all of it, a row either side and well beyond its ends in Level 10, never
    /// on a road, a tree or a crown, a paddock, a farmstead or a pond, nor near a scarecrow, a field's shed or trough, or
    /// Level 3999's arcade and windmills.
    /// </summary>
    private bool L15WallFits(L15WallSite w)
    {
        (int X, int Z) At(int along, int across) => w.AlongX ? (along, across) : (across, along);
        // Far from the edge of the fields (and so from every gate out of them)
        for (int along = w.From - 64; along <= w.To + 64; along += 32)
            foreach (int across in new[] { w.Line - 64, w.Line, w.Line + 65 })
            {
                var (x, z) = At(along, across);
                if (LevelAt(MacroOf(x), MacroOf(z)) != 10) return false;
            }
        var fields = new HashSet<(int, int)>();
        for (int along = w.From - 1; along <= w.To + 1; along++)
            for (int across = w.Line - 2; across <= w.Line + 3; across++)
            {
                var (x, z) = At(along, across);
                if (FarmRoadAt(x, z) >= 0) return false;
                var f = FieldAt(x, z);
                if (IsFarmTreeIn(x, z, f)) return false;
                if (fields.Add((f.I, f.J)) && FieldKind(f.I, f.J) is FarmField.Pasture or FarmField.Farmstead or FarmField.Lake) return false;
            }
        int minX = w.AlongX ? w.From : w.Line, maxX = w.AlongX ? w.To : w.Line + 1;
        int minZ = w.AlongX ? w.Line : w.From, maxZ = w.AlongX ? w.Line + 1 : w.To;
        bool Near(int x, int z, int reach) => x >= minX - reach && x <= maxX + reach && z >= minZ - reach && z <= maxZ + reach;
        foreach (var (fi, fj) in fields)
        {
            FarmField kind = FieldKind(fi, fj);
            if (kind is not (FarmField.Wheat or FarmField.Rye or FarmField.Flax)) continue;
            var (sx, sz) = FieldSite(fi, fj);
            if (Near(sx + 3, sz - 2, 3)) return false; // the scarecrow
            var focal = FieldFocalOf(fi, fj);
            if (focal.Kind != FieldFocal.None && Near(sx + focal.Du, sz + focal.Dv, 9)) return false;
        }
        // Level 3999's arcade and its windmills (squares of the same size)
        var (si, sj) = L15WallSquare((minX + maxX) / 2, (minZ + maxZ) / 2);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L3999ArcadeSite a = L3999ArcadeAt(si + di, sj + dj);
                if (a.Valid && maxX >= a.MinX - 12 && minX <= a.MaxX + 12 && maxZ >= a.MinZ - 12 && minZ <= a.MaxZ + 12) return false;
            }
        return true;
    }

    /// <summary>Lays the white walls over a cell of Level 10 (where one crosses it).</summary>
    private void L15MarkWall10(Builder b, int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize, x1 = x0 + MacroSize - 1, z1 = z0 + MacroSize - 1;
        var (i0, j0) = L15WallSquare(x0, z0);
        for (int j = j0 - 1; j <= j0 + 1; j++)
            for (int i = i0 - 1; i <= i0 + 1; i++)
            {
                // (A wall lies well inside its square: test the bounds before planning it)
                int si = i * L15WallLattice, sj = j * L15WallLattice;
                if (x1 < si || x0 >= si + L15WallLattice || z1 < sj || z0 >= sj + L15WallLattice) continue;
                L15WallSite w = L15WallAt(i, j);
                if (!w.Valid) continue;
                int minX = w.AlongX ? w.From : w.Line - 1, maxX = w.AlongX ? w.To : w.Line + 2;
                int minZ = w.AlongX ? w.Line - 1 : w.From, maxZ = w.AlongX ? w.Line + 2 : w.To;
                if (x1 < minX || x0 > maxX || z1 < minZ || z0 > maxZ) continue;
                for (int lz = 0; lz < MacroSize; lz++)
                    for (int lx = 0; lx < MacroSize; lx++)
                        L15Wall10Tile(ref b.At(lx, lz), w, x0 + lx, z0 + lz);
            }
    }

    /// <summary>One tile of a white wall, or of the tread plate before its door, if the position is in it.</summary>
    private static void L15Wall10Tile(ref Tile t, L15WallSite w, int gx, int gz)
    {
        if (t.Under != 0) return; // (someone else's: never taken)
        int along = w.AlongX ? gx : gz, across = (w.AlongX ? gz : gx) - w.Line;
        if (along < w.From || along > w.To || across is < -1 or > 2) return;
        bool far = across >= 1;
        ArchPier face = w.AlongX ? (far ? ArchPier.South : ArchPier.North) : (far ? ArchPier.East : ArchPier.West);
        bool doorRow = far == w.DoorFar;
        if (across is -1 or 2)
        {
            // Before the door: the crop cleared, a steel tread plate on the ground
            if (!doorRow || Math.Abs(along - w.Door) > 1) return;
            t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Grass, Under = Unders.L15Apron10, Pier = face };
            return;
        }
        t = new Tile { Kind = TileKind.Wall, Floor = FloorKind.Grass, Under = Unders.L15Wall10, Pier = face };
        if (Hashing.Mod(along, 8) == 0) t.Detail |= L15WallPilasterBit;
        if (doorRow && along == w.Door) t.Under = Unders.L15WallDoor10;
        else if (doorRow && Math.Abs(along - w.Door) == 1) t.Detail |= L15WallJambBit;
    }

    // ================= Level 3: the door =================

    /// <summary>
    /// Now and then a cell of Level 3 has a steel door in a straight stretch of wall, solid wall behind it and either side of it
    /// and clear floor before it, where nothing else is fixed to the wall.
    /// </summary>
    private void L15MarkDoor3(Builder b, int mx, int mz)
    {
        if (IsSpawnMacro(mx, mz)) return;
        ulong h = Hashing.Hash(seed, mx, mz, SaltL15Door3);
        if (Hashing.Unit(h) >= L15Door3Chance) return;
        bool Wall(int x, int z) => b.At(x, z).Kind == TileKind.Wall && !b.At(x, z).Tall && b.At(x, z).Under == 0 && b.At(x, z).Variant == 0;
        bool Open(int x, int z)
        {
            Tile t = b.At(x, z);
            return t.Kind == TileKind.Floor && t.Under == 0 && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Stair == 0 && !t.Sealed;
        }
        var found = new List<(int X, int Z, ArchPier Face)>();
        for (int z = 2; z < MacroSize - 2; z++)
            for (int x = 2; x < MacroSize - 2; x++)
            {
                if (!Wall(x, z)) continue;
                foreach (ArchPier face in new[] { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West })
                {
                    var (dx, dz) = FacingStep(face);
                    // Clear floor before it (and before its neighbours), wall behind it, and wall along both sides of it
                    if (!Open(x + dx, z + dz) || !Open(x + dx - dz, z + dz + dx) || !Open(x + dx + dz, z + dz - dx)) continue;
                    if (b.At(x - dx, z - dz).Kind != TileKind.Wall || !Wall(x - dz, z + dx) || !Wall(x + dz, z - dx)) continue;
                    found.Add((x, z, face));
                }
            }
        if (found.Count == 0) return;
        var rng = new Rng(Hashing.Mix(h));
        var (wx, wz, f) = found[rng.Range(0, found.Count - 1)];
        ref Tile door = ref b.At(wx, wz);
        door.Under = Unders.L15Door3;
        door.Pier = f;
    }

    /// <summary>Level 15's ways in, in a cell of one of the levels 0-20 (WorldLayout.ExpLinks.cs calls it first of all).</summary>
    partial void L15Entrances(Builder b, int mx, int mz)
    {
        if (b.Level == 10) L15MarkWall10(b, mx, mz);
        else if (b.Level == 3) L15MarkDoor3(b, mx, mz);
    }

    /// <summary>Whether a cell of Level 3 has the door to Level 15 by its hash (the harness's count; the door itself needs a wall to stand in).</summary>
    public bool L15Door3Cell(int mx, int mz) =>
        ExpEntrances && !IsSpawnMacro(mx, mz) && LevelAt(mx, mz) == 3 && Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL15Door3)) < L15Door3Chance;

    // ================= Level 15: the doors that do not open, and the ways out =================

    /// <summary>A wing's links (laid over its plan by <see cref="L15LinkPlan"/>).</summary>
    public sealed partial class L15Plan
    {
        /// <summary>The wing's hall door that does not open: its wall tile, and the way it faces (onto the main hall).</summary>
        public bool HasSealed;
        public int SealedA, SealedB;
        public ArchPier SealedFace;
        /// <summary>The wing's way out (<see cref="L15ExitEscape"/> ...), and a tile of it: the ESCAPE panel, the pane, the first step.</summary>
        public byte Exit;
        public int ExitA, ExitB;
        /// <summary>The ESCAPE panel's gateway (its first tile) and the way it faces (into the control room).</summary>
        public int GateA, GateB;
        public ArchPier GateFace;
        /// <summary>The office: its floor, inside its walls.</summary>
        public int OfficeX0, OfficeZ0, OfficeX1, OfficeZ1;
    }

    /// <summary>Lays a wing's links over its plan: the door that does not open, and now and then a way out.</summary>
    private void L15LinkPlan(L15Plan plan)
    {
        L15PlaceSealed(plan);
        L15PlaceExit(plan);
        // Last, Level 14's MEDICAL CENTER door in a medical bay's wall, on Level 14's salts (WorldLayout.Level14.Links.cs)
        L14PlaceMedDoor(plan);
    }

    /// <summary>Now and then a way out of the wing.</summary>
    private void L15PlaceExit(L15Plan plan)
    {
        ulong h = Hashing.Hash(seed, plan.Hx, plan.Hz, SaltL15Exit);
        double r = Hashing.Unit(h);
        if (r >= L15ExitChance) return;
        var rng = new Rng(Hashing.Hash(seed, plan.Hx, plan.Hz, SaltL15ExitPick));
        // The middle of the region stays as it was (where people are put down): no way out within a wing or so of it
        var (cx, cz) = plan.World(60, 60);
        if (Math.Abs(cx - L15CentreX * MacroSize) < 200 && Math.Abs(cz - L15CentreZ * MacroSize) < 200) return;
        int kind = (int)(r / L15ExitChance * 3);
        // From layout 16's balance (every world: ExpVersion) the two ways deeper (the pane to Level 11, the office stairs to Level 4) are a quarter as
        // common, the ESCAPE gateway back to Level 3 as it was (the progression rule, decision 20): of the wings that roll a
        // pane or stairs, only the lowest quarter of the roll keeps it, so the kept ones are the same wings
        if (ExpVersion >= 16 && kind >= 1 && r / L15ExitChance * 3 - kind >= 0.25) return;
        switch (kind)
        {
            case 0: L15PlaceEscape(plan, ref rng); break;
            case 1: L15PlaceWindow(plan, ref rng); break;
            default: L15PlaceOffice(plan, ref rng); break;
        }
    }

    /// <summary>The wall tile on a side of a wing (0 west, 1 east, 2 north, 3 south) at k along it, and the way it faces.</summary>
    private static (int A, int B, ArchPier Face) L15WingWall(int side, int k) => side switch
    {
        0 => (-1, k, ArchPier.West),
        1 => (L15WingSize, k, ArchPier.East),
        2 => (k, -1, ArchPier.North),
        _ => (k, L15WingSize, ArchPier.South),
    };

    /// <summary>
    /// A reinforced door in one of the wing's walls onto a main hall, between two pilasters and clear of the wall lights and
    /// the hall signs, with lit jambs: it does not open (people put down in the level from outside arrive beside one).
    /// </summary>
    private void L15PlaceSealed(L15Plan plan)
    {
        var rng = new Rng(Hashing.Hash(seed, plan.Hx, plan.Hz, SaltL15SealedDoor));
        bool Plain(Tile t) => t.Kind == TileKind.Wall && t.Detail == L15WallPlain && t.Depth == L15WallWhite && t.Under == 0;
        for (int attempt = 0; attempt < 24; attempt++)
        {
            int side = rng.Range(0, 3), k = rng.Range(10, L15WingSize - 11);
            var (a, b, face) = L15WingWall(side, k);
            var (x, z) = plan.World(a, b);
            int along = side < 2 ? z : x;
            if (Hashing.Mod(along, 8) is not (2 or 6) || Hashing.Mod(along, L15Period) is >= 9 and <= 13 or >= 121 and <= 125) continue;
            var (pa, pb, _) = L15WingWall(side, k - 1);
            var (na, nb, _) = L15WingWall(side, k + 1);
            if (!Plain(plan.AtAB(a, b)) || !Plain(plan.AtAB(pa, pb)) || !Plain(plan.AtAB(na, nb))) continue;
            ref Tile door = ref plan.AtAB(a, b);
            door.Under = Unders.L15Sealed;
            door.Pier = face;
            foreach (var (ja, jb) in new[] { (pa, pb), (na, nb) })
            {
                ref Tile jamb = ref plan.AtAB(ja, jb);
                jamb.Detail = L15WallJamb;
                jamb.Pier = face;
            }
            plan.HasSealed = true;
            plan.SealedA = a;
            plan.SealedB = b;
            plan.SealedFace = face;
            return;
        }
    }

    /// <summary>A plan's room round a floor tile: the rectangle of floor of its zone along the tile's row and column.</summary>
    private static (int X0, int Z0, int X1, int Z1) L15RoomRound(L15Plan plan, int a, int b)
    {
        byte zone = plan.AtAB(a, b).Zone;
        bool Same(int x, int z) => L15Plan.In(x, z) && plan.AtAB(x, z).Kind == TileKind.Floor && plan.AtAB(x, z).Zone == zone;
        int x0 = a, x1 = a, z0 = b, z1 = b;
        while (Same(x0 - 1, b)) x0--;
        while (Same(x1 + 1, b)) x1++;
        while (Same(a, z0 - 1)) z0--;
        while (Same(a, z1 + 1)) z1++;
        return (x0, z0, x1, z1);
    }

    /// <summary>Whether the whole of a piece of a plan lies in the level (a wing at the rim is only partly in it).</summary>
    private bool L15PlanInLevel(L15Plan plan, int a0, int b0, int a1, int b1)
    {
        foreach (var (a, b) in new[] { (a0, b0), (a1, b0), (a0, b1), (a1, b1) })
        {
            var (x, z) = plan.World(a, b);
            if (LevelAt(MacroOf(x), MacroOf(z)) != Level15) return false;
        }
        return true;
    }

    /// <summary>
    /// A lit control room's ESCAPE panel that works, and the locked gateway it opens: two tiles of a side wall (or the back
    /// wall), where it can be with more wall behind them (a service passage's), so the gateway is a deep doorway.
    /// </summary>
    private void L15PlaceEscape(L15Plan plan, ref Rng rng)
    {
        var panels = new List<(int A, int B)>();
        for (int b = 0; b < L15WingSize; b++)
            for (int a = 0; a < L15WingSize; a++)
            {
                Tile t = plan.AtAB(a, b);
                if (t.Kind != TileKind.Wall || t.Detail != L15WallEscape || t.Under != 0) continue;
                var (dx, dz) = FacingStep(t.Pier);
                Tile inside = plan.AtAB(a + dx, b + dz);
                if (inside.Kind == TileKind.Floor && L15ZoneOf(inside) == L15Zone.Control && !L15IsDark(inside)) panels.Add((a, b));
            }
        // (Each in turn from one picked by hash, until one has room for its gateway)
        int start = panels.Count == 0 ? 0 : rng.Range(0, panels.Count - 1);
        for (int n = 0; n < panels.Count; n++)
        {
            var (pa, pb) = panels[(start + n) % panels.Count];
            Tile panel = plan.AtAB(pa, pb);
            var (dx, dz) = FacingStep(panel.Pier);
            var room = L15RoomRound(plan, pa + dx, pb + dz);
            if (!L15PlanInLevel(plan, room.X0 - 1, room.Z0 - 1, room.X1 + 1, room.Z1 + 1)) continue;
            if (L15FindGateway(plan, room, panel.Pier) is not { } gate) continue;
            plan.AtAB(pa, pb).Under = Unders.L15Escape;
            var (sx, sz) = L15Along(gate.Face);
            for (int i = 0; i < 2; i++)
            {
                ref Tile g = ref plan.AtAB(gate.A + sx * i, gate.B + sz * i);
                g.Under = Unders.L15Gateway;
                g.Pier = gate.Face;
                g.Detail = L15WallPlain;
                g.Stack = (byte)i;
            }
            plan.Exit = L15ExitEscape;
            (plan.ExitA, plan.ExitB) = (pa, pb);
            (plan.GateA, plan.GateB, plan.GateFace) = (gate.A, gate.B, gate.Face);
            return;
        }
    }

    /// <summary>The way along a wall that faces a direction (a quarter turn from it).</summary>
    private static (int Dx, int Dz) L15Along(ArchPier face) => face is ArchPier.North or ArchPier.South ? (1, 0) : (0, 1);

    /// <summary>
    /// Two tiles of a room's wall for its gateway: in a side wall, from its middle outward, else the wall across from the
    /// panel; plain wall with wall either side, and behind both more wall where it can be.
    /// </summary>
    private static (int A, int B, ArchPier Face)? L15FindGateway(L15Plan plan, (int X0, int Z0, int X1, int Z1) r, ArchPier intoRoom)
    {
        // The room's four walls, each as (its line, the way it faces into the room); the panel's own wall last of all (never)
        var walls = intoRoom is ArchPier.East or ArchPier.West
            ? new[] { (r.Z0 - 1, ArchPier.South), (r.Z1 + 1, ArchPier.North), intoRoom == ArchPier.East ? (r.X1 + 1, ArchPier.West) : (r.X0 - 1, ArchPier.East) }
            : new[] { (r.X0 - 1, ArchPier.East), (r.X1 + 1, ArchPier.West), intoRoom == ArchPier.South ? (r.Z1 + 1, ArchPier.North) : (r.Z0 - 1, ArchPier.South) };
        bool Wall(int a, int b) => L15Plan.In(a, b) && plan.AtAB(a, b).Kind == TileKind.Wall;
        bool Plain(int a, int b) => Wall(a, b) && plan.AtAB(a, b).Under == 0 && plan.AtAB(a, b).Detail is L15WallPlain or L15WallPilaster;
        // First where there is more wall behind (a service passage's: the gateway a deep doorway onto nothing but the way out),
        // else where a corridor or a main hall lies behind (stepping into it from either side takes you)
        bool Behind(int a, int b, bool deep) => deep ? Wall(a, b) : L15Plan.In(a, b) && plan.AtAB(a, b).Kind is TileKind.Wall or TileKind.Floor;
        foreach (bool deep in new[] { true, false })
        foreach (var (line, face) in walls)
        {
            bool alongX = face is ArchPier.North or ArchPier.South;
            int lo = alongX ? r.X0 : r.Z0, hi = alongX ? r.X1 : r.Z1, mid = (lo + hi) / 2;
            var (bx, bz) = FacingStep(face);
            for (int d = 0; d <= (hi - lo) / 2; d++)
                foreach (int k in new[] { mid - d, mid + d })
                {
                    if (k < lo + 1 || k + 1 > hi - 1) continue;
                    (int A, int B) T(int at) => alongX ? (at, line) : (line, at);
                    bool ok = true;
                    for (int i = -1; i <= 2 && ok; i++)
                    {
                        var (a, b) = T(k + i);
                        ok = i is 0 or 1 ? Plain(a, b) && Behind(a - bx, b - bz, deep) : Wall(a, b);
                    }
                    if (!ok) continue;
                    var (ga, gb) = T(k);
                    return (ga, gb, face);
                }
        }
        return null;
    }

    /// <summary>A pane of a lit machine room's thick glass with a street's orange light behind it.</summary>
    private void L15PlaceWindow(L15Plan plan, ref Rng rng)
    {
        var panes = new List<(int A, int B)>();
        for (int b = 0; b < L15WingSize; b++)
            for (int a = 0; a < L15WingSize; a++)
            {
                Tile t = plan.AtAB(a, b);
                if (t.Kind != TileKind.Wall || t.Detail != L15WallGlass || t.Under != 0) continue;
                var (dx, dz) = FacingStep(t.Pier);
                Tile inside = plan.AtAB(a - dx, b - dz), outside = plan.AtAB(a + dx, b + dz);
                if (inside.Kind != TileKind.Floor || L15ZoneOf(inside) != L15Zone.Machine || L15IsDark(inside) || outside.Kind != TileKind.Floor) continue;
                if (!L15PlanInLevel(plan, a - 1, b - 1, a + 1, b + 1)) continue;
                panes.Add((a, b));
            }
        if (panes.Count == 0) return;
        var (pa, pb) = panes[rng.Range(0, panes.Count - 1)];
        plan.AtAB(pa, pb).Under = Unders.L15Window;
        plan.Exit = L15ExitWindow;
        (plan.ExitA, plan.ExitB) = (pa, pb);
    }

    /// <summary>
    /// An office out of place: a lit bare room, store, dormitory or lab cleared and laid with Level 4's carpet, filing cabinets
    /// along its walls and a desk or two, and down the middle of it a staircase going down through the floor.
    /// </summary>
    private void L15PlaceOffice(L15Plan plan, ref Rng rng)
    {
        var rooms = new List<(int X0, int Z0, int X1, int Z1)>();
        var seen = new HashSet<(int, int)>();
        for (int b = 0; b < L15WingSize; b++)
            for (int a = 0; a < L15WingSize; a++)
            {
                Tile d = plan.AtAB(a, b);
                if (d.Kind != TileKind.Doorway) continue;
                var (dx, dz) = FacingStep(d.Pier);
                int ia = a - dx, ib = b - dz;
                if (!L15Plan.In(ia, ib)) continue;
                Tile inside = plan.AtAB(ia, ib);
                if (inside.Kind != TileKind.Floor || L15IsDark(inside) || L15ZoneOf(inside) is not (L15Zone.Blank or L15Zone.Storage or L15Zone.Dorm or L15Zone.Lab))
                    continue;
                var room = L15RoomRound(plan, ia, ib);
                if (!seen.Add((room.X0, room.Z0))) continue;
                int w = room.X1 - room.X0 + 1, dd = room.Z1 - room.Z0 + 1;
                if (Math.Min(w, dd) < 7 || Math.Max(w, dd) < 12 || Math.Max(w, dd) > 28) continue;
                if (!L15PlanInLevel(plan, room.X0 - 1, room.Z0 - 1, room.X1 + 1, room.Z1 + 1)) continue;
                rooms.Add(room);
            }
        if (rooms.Count == 0) return;
        var r = rooms[rng.Range(0, rooms.Count - 1)];
        // Cleared and carpeted
        for (int b = r.Z0; b <= r.Z1; b++)
            for (int a = r.X0; a <= r.X1; a++)
            {
                ref Tile t = ref plan.AtAB(a, b);
                t.Variant = 0;
                t.Stack = 0;
                t.SupplyBox = false;
                t.Looted = false;
                t.Detail = 0;
                t.Overhead = 0;
                t.Pipe = 0;
                t.Depth = L15FloorCarpet;
                t.Under = Unders.L15Office;
                t.Pier = ArchPier.North;
            }
        plan.CampSpots.RemoveAll(s =>
        {
            int a = s.X - plan.Hx * L15Period - 7, b = s.Z - plan.Hz * L15Period - 7;
            return a >= r.X0 && a <= r.X1 && b >= r.Z0 && b <= r.Z1;
        });
        // The staircase down the long way, two wide, from two tiles in at one end: six steps, then the landing
        bool alongX = r.X1 - r.X0 >= r.Z1 - r.Z0;
        bool forward = rng.Chance(0.5);
        int lo = alongX ? r.X0 : r.Z0, hi = alongX ? r.X1 : r.Z1, across = alongX ? (r.Z0 + r.Z1) / 2 : (r.X0 + r.X1) / 2;
        ArchPier climb = alongX ? (forward ? ArchPier.West : ArchPier.East) : (forward ? ArchPier.North : ArchPier.South);
        for (int n = 1; n <= L15StairSteps + 1; n++)
        {
            int at = forward ? lo + 1 + n : hi - 1 - n;
            for (int c = 0; c < 2; c++)
            {
                int a = alongX ? at : across + c, b = alongX ? across + c : at;
                ref Tile t = ref plan.AtAB(a, b);
                t.Under = Unders.L15Stairs;
                t.Stack = (byte)n;
                t.Pier = climb;
                if (n == 1 && c == 0) (plan.ExitA, plan.ExitB) = (a, b);
            }
        }
        // Filing cabinets along the long walls (clear of the doors and the stairs), a desk and a chair or two at the far end
        bool NearDoor(int a, int b)
        {
            for (int db = -2; db <= 2; db++)
                for (int da = -2; da <= 2; da++)
                    if (L15Plan.In(a + da, b + db) && plan.AtAB(a + da, b + db).Kind == TileKind.Doorway) return true;
            return false;
        }
        bool Free(int a, int b) => plan.AtAB(a, b).Under == Unders.L15Office && plan.AtAB(a, b).Variant == 0 && !NearDoor(a, b);
        foreach (int side in new[] { 0, 1 })
        {
            int line = alongX ? (side == 0 ? r.Z0 : r.Z1) : (side == 0 ? r.X0 : r.X1);
            ArchPier faceIn = alongX ? (side == 0 ? ArchPier.South : ArchPier.North) : (side == 0 ? ArchPier.East : ArchPier.West);
            for (int k = lo + 1; k <= hi - 1; k += 2)
            {
                int a = alongX ? k : line, b = alongX ? line : k;
                if (!Free(a, b) || rng.Chance(0.35)) continue;
                ref Tile t = ref plan.AtAB(a, b);
                t.Variant = Props.FilingCabinet;
                t.Pier = faceIn;
            }
        }
        int deskAt = forward ? hi - 1 : lo + 1;
        ArchPier toStairs = alongX ? (forward ? ArchPier.West : ArchPier.East) : (forward ? ArchPier.North : ArchPier.South);
        var (sx, sz) = FacingStep(toStairs);
        for (int c = -1; c <= 2; c += 3)
        {
            int a = alongX ? deskAt : across + c, b = alongX ? across + c : deskAt;
            if (!L15Plan.In(a, b) || !Free(a, b) || !Free(a + sx, b + sz)) continue;
            plan.AtAB(a, b).Variant = Props.Desk;
            plan.AtAB(a, b).Pier = toStairs;
            if (rng.Chance(0.8))
            {
                plan.AtAB(a + sx, b + sz).Variant = Props.OfficeChair;
                plan.AtAB(a + sx, b + sz).Pier = Opposite(toStairs);
            }
        }
        plan.Exit = L15ExitStairs;
        (plan.OfficeX0, plan.OfficeZ0, plan.OfficeX1, plan.OfficeZ1) = r;
    }

    // ================= Arrivals =================

    /// <summary>
    /// Where someone comes in from outside (the white wall's door, Level 3's): in a lit main hall in front of one of the doors
    /// that do not open, the nearest to a place near the middle picked by the key. Null if none is found.
    /// </summary>
    public (int X, int Z)? L15SealedArrival(ulong key)
    {
        ulong h = Hashing.Hash(seed, (int)(key & 0xFFFFFFFF), (int)(key >> 32), SaltL15Arrive);
        var (cmx, cmz) = L15ArrivalCell(h);
        int hcx = Hashing.FloorDiv(cmx * MacroSize + 16, L15Period), hcz = Hashing.FloorDiv(cmz * MacroSize + 16, L15Period);
        for (int ring = 0; ring <= 4; ring++)
            for (int j = -ring; j <= ring; j++)
                for (int i = -ring; i <= ring; i++)
                {
                    if (Math.Max(Math.Abs(i), Math.Abs(j)) != ring) continue;
                    L15Plan plan = L15PlanOf(hcx + i, hcz + j);
                    if (!plan.HasSealed) continue;
                    var (x, z) = plan.World(plan.SealedA, plan.SealedB);
                    var (dx, dz) = FacingStep(plan.SealedFace);
                    int fx = x + dx, fz = z + dz;
                    Tile t = TileAt(fx, fz);
                    if (t.Level != Level15 || L15IsDark(t) || t.Kind != TileKind.Floor || t.Variant != 0 || TileAt(x, z).Under != Unders.L15Sealed) continue;
                    return (fx, fz);
                }
        return null;
    }

    /// <summary>The ESCAPE panel's gateway tiles near a block position of the level (within a room's reach), for opening it.</summary>
    public List<(int X, int Z)> L15GatewayNear(int gx, int gz, int reach = 24)
    {
        var found = new List<(int X, int Z)>();
        for (int dz = -reach; dz <= reach; dz++)
            for (int dx = -reach; dx <= reach; dx++)
            {
                Tile t = TileAt(gx + dx, gz + dz);
                if (t.Level == Level15 && t.Under == Unders.L15Gateway) found.Add((gx + dx, gz + dz));
            }
        return found;
    }

    // ================= Showcase =================

    /// <summary>
    /// The showcase's spots for the links: the nearest white wall to spawn (its door from the field, and the wall running off
    /// along its face), the nearest door in Level 3, a door that does not open in a hall near the middle, and the nearest way out
    /// of each kind to the middle (the ESCAPE panel, its gateway shut and then rolled up, the pane, the office's stairs).
    /// </summary>
    private IEnumerable<Showcase.Spot> L15LinkSpots(WorldGeometry geometry)
    {
        var spots = new List<Showcase.Spot>();
        int sx = spawnMacroX * MacroSize + 16, sz = spawnMacroZ * MacroSize + 16;
        double y10 = geometry.FloorFor(10) + 1, y3 = geometry.FloorFor(3) + 1, y15 = geometry.FloorFor(Level15) + 1;
        void Add(string name, double y, int x, int z, int dx, int dz, double pitch = 0, string setup = null) =>
            spots.Add(new Showcase.Spot(name, x + 0.5, y, z + 0.5, L15Heading(dx, dz), pitch, setup));

        // Level 10: the nearest wall, by squares outward from spawn
        var (si, sj) = L15WallSquare(sx, sz);
        L15WallSite wall = null;
        double best = double.MaxValue;
        for (int ring = 0; ring <= 10 && wall == null; ring++)
            for (int j = sj - ring; j <= sj + ring; j++)
                for (int i = si - ring; i <= si + ring; i++)
                {
                    if (Math.Max(Math.Abs(i - si), Math.Abs(j - sj)) != ring) continue;
                    L15WallSite w = L15WallAt(i, j);
                    if (!w.Valid) continue;
                    var (dx, dz) = w.DoorAt;
                    double d = Math.Sqrt((double)(dx - sx) * (dx - sx) + (double)(dz - sz) * (dz - sz));
                    if (d < best) { best = d; wall = w; }
                }
        if (wall != null)
        {
            var (x, z) = wall.DoorAt;
            var (fx, fz) = FacingStep(wall.DoorFace);
            Add("wall10", y10, x + fx * 14, z + fz * 14, -fx, -fz, 12);
            int ax = wall.AlongX ? 1 : 0, az = 1 - ax;
            Add("wall10-along", y10, x + fx * 5 - ax * 40, z + fz * 5 - az * 40, ax, az, 4);
            // And through it: where it puts you down (beside a door that does not open)
            Add("trip-wall10", y10, x + fx, z + fz, -fx, -fz, 0, $"/backrooms l15 l15-walldoor {x} {z}");
        }

        // Level 3: the nearest door, by cells outward from spawn
        for (int ring = 0, found = 0; ring <= 160 && found == 0; ring++)
            for (int mz = spawnMacroZ - ring; mz <= spawnMacroZ + ring && found == 0; mz++)
                for (int mx = spawnMacroX - ring; mx <= spawnMacroX + ring && found == 0; mx++)
                {
                    if (Math.Max(Math.Abs(mx - spawnMacroX), Math.Abs(mz - spawnMacroZ)) != ring || !L15Door3Cell(mx, mz)) continue;
                    Tile[] tiles = BuildMacro(mx, mz);
                    for (int k = 0; k < tiles.Length; k++)
                    {
                        if (tiles[k].Under != Unders.L15Door3) continue;
                        int x = mx * MacroSize + k % MacroSize, z = mz * MacroSize + k / MacroSize;
                        var (fx, fz) = FacingStep(tiles[k].Pier);
                        Add("l3-door", y3, x + fx * 3, z + fz * 3, -fx, -fz, 8);
                        Add("trip-l3door", y3, x + fx, z + fz, -fx, -fz, 0, $"/backrooms l15 l15-l3door {x} {z}");
                        found = 1;
                        break;
                    }
                }

        // Level 15: a door that does not open, from across the hall
        if (L15SealedArrival(1) is { } arrive)
        {
            var (x, z) = (arrive.X, arrive.Z);
            foreach (ArchPier p in new[] { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West })
            {
                var (dx, dz) = FacingStep(p);
                if (TileAt(x + dx, z + dz).Under != Unders.L15Sealed) continue;
                Add("sealed-door", y15, x - dx * 3, z - dz * 3, dx, dz, 8);
                break;
            }
        }

        // The nearest way out of each kind to the middle
        int cx = L15CentreX * MacroSize + 16, cz = L15CentreZ * MacroSize + 16;
        int hcx = Hashing.FloorDiv(cx, L15Period), hcz = Hashing.FloorDiv(cz, L15Period);
        var done = new HashSet<byte>();
        for (int ring = 0; ring <= 16 && done.Count < 3; ring++)
            for (int j = -ring; j <= ring; j++)
                for (int i = -ring; i <= ring; i++)
                {
                    if (Math.Max(Math.Abs(i), Math.Abs(j)) != ring) continue;
                    L15Plan plan = L15PlanOf(hcx + i, hcz + j);
                    if (plan.Exit == 0 || !done.Add(plan.Exit)) continue;
                    var (ex, ez) = plan.World(plan.ExitA, plan.ExitB);
                    Tile t = TileAt(ex, ez);
                    var (fx, fz) = FacingStep(t.Pier);
                    switch (plan.Exit)
                    {
                        case L15ExitEscape:
                        {
                            // (From the first clear floor three or more steps back into the room: control rooms are full of consoles)
                            int back = 3;
                            while (back < 7 && !L15Standable(ex + fx * back, ez + fz * back)) back++;
                            Add("escape-panel", y15, ex + fx * back, ez + fz * back, -fx, -fz, 6 + 2 * (7 - back) / 2);
                            var (gx, gz) = plan.World(plan.GateA, plan.GateB);
                            var (gfx, gfz) = FacingStep(plan.GateFace);
                            Add("gateway-shut", y15, gx + gfx * 4, gz + gfz * 4, -gfx, -gfz, 4);
                            Add("gateway-open", y15, gx + gfx * 4, gz + gfz * 4, -gfx, -gfz, 4, $"/backrooms l15 escape {ex} {ez}");
                            // Standing in it once it is open: Level 3
                            Add("trip-gateway", y15, gx, gz, gfx, gfz, 0);
                            break;
                        }
                        case L15ExitWindow:
                            Add("street-pane", y15, ex + fx * 2, ez + fz * 2, -fx, -fz, 10);
                            Add("trip-pane", y15, ex + fx, ez + fz, -fx, -fz, 0, $"/backrooms l15 break {ex} {ez}");
                            break;
                        case L15ExitStairs:
                            // From the top of the stairs (Pier the way they climb), looking down them
                            Add("office-stairs", y15, ex + fx * 2, ez + fz * 2, -fx, -fz, -30);
                            // Three steps down (feet two blocks under the floor): out of sight of the room, into Level 4
                            var (dx, dz) = (-fx, -fz);
                            spots.Add(new Showcase.Spot("trip-stairs", ex + dx * 3 + 0.5, y15 - 3, ez + dz * 3 + 0.5, L15Heading(dx, dz), 0));
                            break;
                    }
                }
        return spots;
    }
}
