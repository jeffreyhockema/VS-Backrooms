using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 120's ways in and out (docs/design/experimental-levels/LINKS.md, "Level 120"; Wikidot's Level 120 names a door
/// labelled "Server Room" in Level 4.3, which this mod stands in with Level 4, and doors in the server rooms and black
/// hallways back to 4.3). Every value here is on the level's own salts, so nothing else in Level 4 moves.
///
/// <list type="bullet">
/// <item><b>In: the door marked SERVER ROOM.</b> Level 4's office blocks have server rooms of their own (one room in twenty,
/// open doorways, a few racks). Very rarely (<see cref="L120ServerDoorChance"/> of the office cells, and only where the cell
/// has a server room) one of them has a grey steel door instead of its doorway, marked SERVER ROOM, a cold green light
/// under it; the room behind is shut (sealed, as a locked office is). Used, it opens on a server room of Level 120,
/// beside one of that level's doors back, which is then its way back: two-way. From layout 12, an M.E.G. placard on the
/// corridor wall beside it, as the offices' elevators down to Level 3 have (Level 120 is class 2, the offices 1).</item>
/// <item><b>Out: doors back to the offices.</b> One cluster of server rooms in <see cref="L120ExitClusterChance"/> has a
/// steel door in a room's wall, a line of office light under it; every Pitch-Black Hallway has one, in its first or last
/// lane. Used, each opens on Level 4 beside a locked office door, one-way (the door it came out of is only an office
/// door, and locked), unless it is the way back of a SERVER ROOM door, in which case it leads back there.</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Salts of the level's ways in and out (from the level's own 0x2600-0x26BF).</summary>
    private const ulong SaltL120LinkCell = 0x2680, SaltL120LinkRoom = 0x2681, SaltL120ExitCluster = 0x2682, SaltL120ExitHallway = 0x2683;

    /// <summary>
    /// The share of Level 4's office cells that roll for a SERVER ROOM door (it is there only if the cell has a server room
    /// of its own, a little under half of them do): a few to the square kilometre of offices, kilometres apart (LINKS.md:
    /// a way into a more dangerous level, a quarter as common as layout 11's ways or rarer).
    /// </summary>
    public const double L120ServerDoorChance = 1 / 150.0;

    /// <summary>The share of Level 120's clusters of server rooms that have a door back to the offices.</summary>
    public const double L120ExitClusterChance = 0.3;

    /// <summary>Whether a cell of Level 4 is an office block (for the harness's count of the offices' area).</summary>
    public bool L120IsOfficeCell(int mx, int mz) => IsOfficeBlock(mx, mz);

    /// <summary>A tile of a SERVER ROOM door into Level 120, in Level 4.</summary>
    public static bool IsL120ServerDoor(in Tile t) => t.Under == Unders.L120ServerDoor && t.Kind == TileKind.Door && t.Level == 4;

    /// <summary>A tile of one of Level 120's doors back to the offices.</summary>
    public static bool IsL120ExitDoor(in Tile t) => t.Under == Unders.L120ExitDoor && t.Kind == TileKind.Door && t.Level == Level120;

    // ================= In: the door marked SERVER ROOM, in Level 4 =================

    /// <summary>
    /// Where a cell of Level 4 has its SERVER ROOM door, worked out from the hashes alone (the cell's roll, its office
    /// grid's rooms, the building core): the door's tile and the corridor tile in front of it, or null. The cell is built
    /// only by <see cref="L120Entrances"/>, which checks the tiles are as expected; the harness and the showcase use this
    /// to find the doors without building every cell.
    /// </summary>
    public (int X, int Z, int OutX, int OutZ)? L120ServerDoorOf(int mx, int mz)
    {
        if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL120LinkCell)) >= L120ServerDoorChance) return null;
        if (LevelAt(mx, mz) != 4 || IsSpawnMacro(mx, mz) || !IsOfficeBlock(mx, mz)) return null;
        var core = L4Core(mx, mz);
        var rooms = new List<(int X, int Z, int OutX, int OutZ)>();
        const int per = MacroSize / L4OfficeGrid;
        for (int j = 0; j < per; j++)
            for (int i = 0; i < per; i++)
            {
                int roomX = mx * per + i, roomZ = mz * per + j;
                // (A concourse takes the whole of a room's square; the core's four rooms are elevators, stairs and a restroom)
                if (Hashing.Mod(roomX, L4ConcourseEvery) == 3 || Hashing.Mod(roomZ, L4ConcourseEvery) == 3) continue;
                if (core is { } c && roomX - c.RoomX is 0 or 1 && roomZ - c.RoomZ is 0 or 1) continue;
                ulong h = Hashing.Hash(seed, roomX, roomZ, SaltL4Room);
                double kind = Hashing.Unit(h);
                if (kind < 0.74 || kind >= 0.79) continue; // (BuildOfficeBlock's server rooms)
                bool doorNorth = (int)((h >> 8) % 2) == 0;
                int x = roomX * L4OfficeGrid + (doorNorth ? 4 : 2), z = roomZ * L4OfficeGrid + (doorNorth ? 2 : 5);
                rooms.Add(doorNorth ? (x, z, x, z - 1) : (x, z, x - 1, z));
            }
        if (rooms.Count == 0) return null;
        return rooms[(int)(Hashing.Hash(seed, mx, mz, SaltL120LinkRoom) % (ulong)rooms.Count)];
    }

    /// <summary>
    /// The scaffold's hook (WorldLayout.ExpLinks.cs), for every cell of Levels 0-20: in a Level 4 cell that has one, the
    /// SERVER ROOM door on its server room's doorway, the room behind it shut, and (layout 12 on) the placard beside it.
    /// Nothing is done unless every tile is as the office grid laid it (a doorway, corridor in front, nobody else's).
    /// </summary>
    partial void L120Entrances(Builder b, int mx, int mz)
    {
        if (b.Level != 4 || b.IsSpawn || L120ServerDoorOf(mx, mz) is not { } d) return;
        int ox = mx * MacroSize, oz = mz * MacroSize;
        int lx = d.X - ox, lz = d.Z - oz, fx = d.OutX - ox, fz = d.OutZ - oz;
        if (lx < 1 || lz < 1 || fx < 0 || fz < 0 || lx >= MacroSize - 1 || lz >= MacroSize - 1) return;
        int dx = fx - lx, dz = fz - lz;
        ref Tile door = ref b.At(lx, lz);
        Tile front = b.At(fx, fz), inside = b.At(lx - dx, lz - dz);
        if (door.Kind != TileKind.Doorway || door.Under != 0 || door.Tall) return;
        if (front.Kind != TileKind.Floor || front.Under != 0 || front.Sealed || front.Stair != 0) return;
        if (inside.Kind != TileKind.Floor || inside.Under != 0) return;
        door.Kind = TileKind.Door;
        door.Under = Unders.L120ServerDoor;
        door.Pier = Toward(dx, dz);
        door.ExitSign = false;
        // The room behind it is no longer anyone's to walk into: shut, as a locked office is
        int rx = Hashing.FloorDiv(d.X, L4OfficeGrid) * L4OfficeGrid - ox, rz = Hashing.FloorDiv(d.Z, L4OfficeGrid) * L4OfficeGrid - oz;
        for (int iz = 3; iz <= 6; iz++)
            for (int ix = 3; ix <= 6; ix++)
                if (rx + ix is >= 0 and < MacroSize && rz + iz is >= 0 and < MacroSize && b.At(rx + ix, rz + iz).Kind == TileKind.Floor)
                {
                    ref Tile t = ref b.At(rx + ix, rz + iz);
                    t.Sealed = true;
                    t.SupplyBox = false;
                }
        L120PlacardBeside(b, lx, lz, dx, dz);
    }

    /// <summary>
    /// The M.E.G. placard beside the door: on the corridor floor against the wall one or two along from it, facing the
    /// approach, as the host's own placards stand (PlaceShortcutPlacards), on a tile still free.
    /// </summary>
    private static void L120PlacardBeside(Builder b, int x, int z, int dx, int dz)
    {
        (int px, int pz) = (-dz, dx);
        foreach (int off in new[] { 1, -1, 2, -2 })
        {
            int wx = x + px * off, wz = z + pz * off, fx = wx + dx, fz = wz + dz;
            if (wx < 0 || wz < 0 || fx < 0 || fz < 0 || wx >= MacroSize || wz >= MacroSize || fx >= MacroSize || fz >= MacroSize) continue;
            if (b.At(wx, wz).Kind != TileKind.Wall || !FreeForPlacard(b.At(fx, fz)) || b.At(fx, fz).Sealed) continue;
            ref Tile t = ref b.At(fx, fz);
            t.Under = Unders.L120Placard;
            t.Pier = Toward(dx, dz);
            return;
        }
    }

    /// <summary>
    /// The SERVER ROOM doors in the Level 4 cells within <paramref name="reach"/> cells (a square) of a cell, nearest
    /// first, from the hashes (<see cref="L120ServerDoorOf"/>) and checked on the built cell. For the harness and the showcase.
    /// </summary>
    public List<(int X, int Z, int OutX, int OutZ)> L120ServerDoorsNear(int cmx, int cmz, int reach, int max = 8)
    {
        var found = new List<(int X, int Z, int OutX, int OutZ)>();
        for (int r = 0; r <= reach && found.Count < max; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int mx = cmx + dx, mz = cmz + dz;
                    if (L120ServerDoorOf(mx, mz) is not { } d) continue;
                    if (IsL120ServerDoor(TileAt(d.X, d.Z))) found.Add(d);
                }
        return found;
    }

    // ================= Out: the doors back to the offices, in Level 120 =================

    /// <summary>
    /// After a hall is laid out: a door back to the offices in one cluster in <see cref="L120ExitClusterChance"/> (in the
    /// wall of a server room, cable room or rack aisle room, with clear floor in front, the wall going on either side, and
    /// solid behind where it can be), and in every Pitch-Black Hallway, in the wall of its first or last lane. On its own
    /// salt, after everything else in the hall.
    /// </summary>
    private void L120PlaceExitDoors(L120Plan plan)
    {
        const int n = L120HallSize;
        if (plan.Kind == L120HallKind.Void) return;
        var rng = new Rng(Hashing.Hash(seed, plan.Hx, plan.Hz, plan.Kind == L120HallKind.Hallway ? SaltL120ExitHallway : SaltL120ExitCluster));
        static bool Clear(in Tile t, L120Zone zone) => t.Kind == TileKind.Floor && t.Zone == (byte)zone && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Under == 0;
        Tile At(int p, int q) => p < -1 || q < -1 || p > n || q > n ? default : plan.At(p, q);

        if (plan.Kind == L120HallKind.Hallway)
        {
            // The first lane's north wall or the last lane's south wall: black fill behind it, the lane in front
            int lanes = plan.Rooms;
            bool first = rng.Chance(0.5);
            int q = first ? 2 : 3 + 3 * (lanes - 1) + 2, fq = first ? 3 : q - 1;
            for (int tries = 0; tries < 40; tries++)
            {
                int p = rng.Range(12, 78);
                if (plan.At(p, q).Kind != TileKind.Wall || !Clear(plan.At(p, fq), L120Zone.Hallway)) continue;
                L120MarkExitDoor(ref plan.At(p, q), first ? ArchPier.South : ArchPier.North);
                plan.Exits++;
                return;
            }
            return;
        }

        if (!rng.Chance(L120ExitClusterChance)) return;
        var best = new List<(int P, int Q, ArchPier Face)>();
        int bestScore = 0;
        for (int q = 0; q < n; q++)
            for (int p = 0; p < n; p++)
            {
                Tile w = plan.At(p, q);
                if (w.Kind != TileKind.Wall || w.Zone != (byte)L120Zone.Wall || w.Under != 0) continue;
                foreach (var (dx, dz) in Steps)
                {
                    // In front: clear floor of a room; the wall goes on either side of the door, with floor before it
                    if (!Clear(At(p + dx, q + dz), L120Zone.Room)) continue;
                    int ax = dz, az = dx;
                    if (At(p + ax, q + az).Kind != TileKind.Wall || At(p - ax, q - az).Kind != TileKind.Wall) continue;
                    if (At(p + dx + ax, q + dz + az).Kind != TileKind.Floor || At(p + dx - ax, q + dz - az).Kind != TileKind.Floor) continue;
                    // Behind: a wall or something standing (the door shows on one side only) is better than another room's floor
                    Tile behind = At(p - dx, q - dz);
                    int score = behind.Kind == TileKind.Wall || behind.Kind == TileKind.Floor && !IsWalkable(behind) ? 2 : 1;
                    if (score < bestScore) continue;
                    if (score > bestScore) { best.Clear(); bestScore = score; }
                    best.Add((p, q, Toward(dx, dz)));
                }
            }
        if (best.Count == 0) return;
        var (bp, bq, face) = best[rng.Range(0, best.Count - 1)];
        L120MarkExitDoor(ref plan.At(bp, bq), face);
        plan.Exits++;
    }

    private static void L120MarkExitDoor(ref Tile t, ArchPier face)
    {
        t.Kind = TileKind.Door;
        t.Under = Unders.L120ExitDoor;
        t.Pier = face;
    }

    /// <summary>The doors back to the offices in a hall (world blocks: the door, and the floor in front of it).</summary>
    public List<(int X, int Z, int FrontX, int FrontZ)> L120ExitDoorsOf(int hx, int hz)
    {
        var doors = new List<(int, int, int, int)>();
        L120Plan plan = L120PlanOf(hx, hz);
        if (plan.Exits == 0) return doors;
        for (int q = -1; q <= L120HallSize; q++)
            for (int p = -1; p <= L120HallSize; p++)
            {
                Tile t = plan.At(p, q);
                if (t.Under != Unders.L120ExitDoor || t.Kind != TileKind.Door) continue;
                var (x, z) = plan.World(p, q);
                var (sx, sz) = FacingStep(t.Pier);
                doors.Add((x, z, x + sx, z + sz));
            }
        return doors;
    }
}
