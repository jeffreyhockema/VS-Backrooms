using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 120's dressing (round 3, the detailed visual pass; see docs/design/experimental-levels/120-plan.md): a cluster as
/// a real data hall is laid out where the lore is silent. Its operators' room (the terminal room, with its wall of screens)
/// by a door onto a passage; a UPS / battery room; cooling units at the ends of the server rooms' aisles; a cable tray over
/// every standing bank and an end panel with the row's letter at each end; storage with shelving. Signs where a real place
/// has them: a plate beside the doors naming the room behind (SERVER ROOM and the hall's letter, TERMINAL ROOM, UPS /
/// BATTERY, CABLE ROOM, STORAGE), the hall's DATA HALL plate and AUTHORIZED PERSONNEL ONLY outside, EXIT signs over the
/// doors out (one in five still faintly lit on its battery), fire points, evacuation plans, the hall's letter stencilled
/// by the crossings, now and then a note taped up. And in the White Voids, one small thing wrong in a room now and then.
///
/// <para>Wall decorations sit on a wall tile (<see cref="Tile.Variant"/> one of <c>L120Deco*</c>, facing <see cref="Tile.Pier"/>,
/// its text or look in <see cref="Tile.Detail"/>); the generator draws the wall block with the thing on that face.</para>
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL120Dress = 0x2615;

    /// <summary>Round 3's props: a UPS cabinet, a battery cabinet, a cooling unit (all two high; the unit's duct a third), a KVM cart, a mop bucket, a fallen ceiling tile, a sheet of paper, a bank's end panel, steel shelving.</summary>
    public const ushort L120Ups = Props.L120First + 7, L120Battery = Props.L120First + 8, L120Crac = Props.L120First + 9,
        L120Kvm = Props.L120First + 10, L120Mop = Props.L120First + 11, L120Debris = Props.L120First + 12,
        L120Paper = Props.L120First + 13, L120RowEnd = Props.L120First + 14, L120Shelf = Props.L120First + 15;

    /// <summary>(Round 4) The fire suppression bank against a wall (two high, its pipe a third), a tape library (two high).</summary>
    public const ushort L120FireSup = Props.L120First + 16, L120TapeLib = Props.L120First + 17;

    /// <summary>Wall decorations (<see cref="Tile.Variant"/> of a wall, facing <see cref="Tile.Pier"/>).</summary>
    public const ushort L120DecoPlate = Decor.L120First, L120DecoAuth = Decor.L120First + 1, L120DecoNote = Decor.L120First + 2,
        L120DecoFire = Decor.L120First + 3, L120DecoCables = Decor.L120First + 4, L120DecoScreens = Decor.L120First + 5,
        L120DecoEvac = Decor.L120First + 6, L120DecoStencil = Decor.L120First + 7, L120DecoExit = Decor.L120First + 8,
        L120DecoPanel = Decor.L120First + 9, L120DecoCrack = Decor.L120First + 10, L120DecoSmudge = Decor.L120First + 11;

    /// <summary>A plate's text (<see cref="Tile.Detail"/>): SERVER ROOM and a letter (0-7), the other rooms, DATA HALL and a letter (12-19).</summary>
    public const byte L120PlateServer = 0, L120PlateTerminal = 8, L120PlateUps = 9, L120PlateCables = 10, L120PlateStorage = 11, L120PlateHall = 12;

    /// <summary>More of the floor (<see cref="Tile.Depth"/>): a cable port, a wet patch under a leak; in a White Void, a glitched tile.</summary>
    public const byte L120PanelPort = 4, L120PanelWet = 5, L120VoidGlitch = 6;

    /// <summary>A UPS (<see cref="Tile.Detail"/>): whole, or torn open.</summary>
    public const byte L120UpsWhole = 0, L120UpsOpen = 1;

    /// <summary>
    /// The hall's letter, A-H (0-7): on its DATA HALL plates, its stencils and its SERVER ROOM plates. Laid out as x + 3z
    /// (mod 8), so no hall shares its letter with any of the eight round it (across a passage the letters always differ).
    /// </summary>
    public static int L120HallLetter(int hx, int hz) => Hashing.Mod(hx + 3 * hz, 8);

    /// <summary>The way out of a wall tile's face toward a step.</summary>
    private static ArchPier L120Toward(int dp, int dq) => dp > 0 ? ArchPier.East : dp < 0 ? ArchPier.West : dq > 0 ? ArchPier.South : ArchPier.North;

    /// <summary>
    /// Picks the cluster's operators' room and its UPS room among the rooms already given kinds: a big room on the hall's
    /// edge by the middle of a side (where the first door onto that passage opens) becomes the terminal room, and the
    /// smallest other room the UPS / battery room.
    /// </summary>
    private static void L120PickFront(List<L120Room> rooms, ref Rng rng)
    {
        const int mid = L120HallSize / 2;
        int side = rng.Range(0, 3);
        (int P, int Q) at = side switch { 0 => (0, mid), 1 => (L120HallSize - 1, mid), 2 => (mid, 0), _ => (mid, L120HallSize - 1) };
        int noc = -1;
        for (int i = 0; i < rooms.Count; i++)
        {
            L120Room r = rooms[i];
            if (at.P >= r.P0 && at.P <= r.P1 && at.Q >= r.Q0 && at.Q <= r.Q1 && r.W * r.H >= 99) noc = i;
        }
        if (noc >= 0)
        {
            L120Room r = rooms[noc];
            r.Kind = L120RoomKind.Terminals;
            rooms[noc] = r;
        }
        int ups = -1, area = int.MaxValue;
        for (int i = 0; i < rooms.Count; i++)
        {
            L120Room r = rooms[i];
            if (i == noc || r.W < 9 || r.H < 9 || r.W * r.H >= area) continue;
            ups = i;
            area = r.W * r.H;
        }
        if (ups >= 0)
        {
            L120Room r = rooms[ups];
            r.Kind = L120RoomKind.Ups;
            rooms[ups] = r;
        }
    }

    /// <summary>
    /// The UPS / battery room: a row of UPS cabinets (now and then one torn open) along one side, rows of battery cabinets
    /// behind it with two-wide aisles, the main electrical panel on a wall, a fire point.
    /// </summary>
    private static void L120LayUps(L120Plan plan, L120Room r, ref Rng rng)
    {
        var (p0, q0, p1, q1) = L120Inner(r);
        bool alongP = p1 - p0 >= q1 - q0;
        int l0 = alongP ? p0 : q0, l1 = alongP ? p1 : q1, s0 = alongP ? q0 : p0, s1 = alongP ? q1 : p1;
        ArchPier high = alongP ? ArchPier.South : ArchPier.East;
        for (int s = s0, row = 0; s <= s1 - 2; s += 3, row++)
            for (int l = l0 + 1; l <= l1 - 1; l++)
            {
                ref Tile t = ref L120Along(plan, alongP, l, s);
                t.Pier = high;
                if (row == 0)
                {
                    t.Variant = L120Ups;
                    t.Detail = rng.Chance(0.25) ? L120UpsOpen : L120UpsWhole;
                }
                else t.Variant = L120Battery;
            }
        // The panel and a fire point on the long wall behind the UPS row's far end... or wherever the wall is whole
        L120WallThing(plan, r, L120DecoPanel, 0, ref rng);
        L120WallThing(plan, r, L120DecoFire, 0, ref rng);
        // (Round 4) The room's fire suppression bank, against a short wall on the walk round the room
        L120AgainstWall(plan, r, L120FireSup, alongP, ref rng);
    }

    /// <summary>
    /// (Round 4) Stands a two-high cabinet on the walk round a room against one of its short walls, facing in (not before a
    /// doorway, and with the tiles either side of it and the one in front of it free, so the walk goes round it).
    /// </summary>
    private static bool L120AgainstWall(L120Plan plan, L120Room r, ushort variant, bool alongP, ref Rng rng)
    {
        for (int tries = 0; tries < 10; tries++)
        {
            bool low = rng.Chance(0.5);
            int l = alongP ? (low ? r.P0 : r.P1) : (low ? r.Q0 : r.Q1);
            int sMin = alongP ? r.Q0 + 1 : r.P0 + 1, sMax = alongP ? r.Q1 - 1 : r.P1 - 1;
            if (sMax < sMin) return false;
            int sv = rng.Range(sMin, sMax);
            int p = alongP ? l : sv, q = alongP ? sv : l;
            int dp = alongP ? (low ? 1 : -1) : 0, dq = alongP ? 0 : (low ? 1 : -1);
            ref Tile t = ref plan.At(p, q);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stack != 0) continue;
            if (plan.At(p - dp, q - dq).Kind != TileKind.Wall) continue;
            Tile a = alongP ? plan.At(p, q - 1) : plan.At(p - 1, q), c = alongP ? plan.At(p, q + 1) : plan.At(p + 1, q), front = plan.At(p + dp, q + dq);
            if (a.Kind != TileKind.Floor || c.Kind != TileKind.Floor || a.Variant != 0 || c.Variant != 0 || front.Kind != TileKind.Floor || front.Variant != 0) continue;
            Tile wa = alongP ? plan.At(p - dp, q - 1) : plan.At(p - 1, q - dq), wc = alongP ? plan.At(p - dp, q + 1) : plan.At(p + 1, q - dq);
            if (wa.Kind == TileKind.Doorway || wc.Kind == TileKind.Doorway) continue;
            t.Variant = variant;
            t.Pier = L120Toward(dp, dq);
            return true;
        }
        return false;
    }

    /// <summary>Hangs a decoration on some whole stretch of a room's wall (not beside a door), facing into the room.</summary>
    private static bool L120WallThing(L120Plan plan, L120Room r, ushort deco, byte detail, ref Rng rng)
    {
        for (int tries = 0; tries < 12; tries++)
        {
            int side = rng.Range(0, 3);
            int p, q, dp = 0, dq = 0;
            switch (side)
            {
                case 0: p = r.P0 - 1; q = rng.Range(r.Q0 + 1, r.Q1 - 1); dp = 1; break;
                case 1: p = r.P1 + 1; q = rng.Range(r.Q0 + 1, r.Q1 - 1); dp = -1; break;
                case 2: q = r.Q0 - 1; p = rng.Range(r.P0 + 1, r.P1 - 1); dq = 1; break;
                default: q = r.Q1 + 1; p = rng.Range(r.P0 + 1, r.P1 - 1); dq = -1; break;
            }
            ref Tile w = ref plan.At(p, q);
            if (w.Kind != TileKind.Wall || w.Variant != 0) continue;
            // (Not beside a doorway, and with the floor in front of it clear of anything tall)
            Tile a = dp != 0 ? plan.At(p, q - 1) : plan.At(p - 1, q), b = dp != 0 ? plan.At(p, q + 1) : plan.At(p + 1, q);
            if (a.Kind == TileKind.Doorway || b.Kind == TileKind.Doorway) continue;
            Tile front = plan.At(p + dp, q + dq);
            if (front.Variant is L120Rack or L120Ups or L120Battery or L120Crac or L120Shelf or L120RowEnd or L120FireSup or L120TapeLib) continue;
            w.Variant = deco;
            w.Detail = detail;
            w.Pier = L120Toward(dp, dq);
            return true;
        }
        return false;
    }

    /// <summary>The plate that names a room of a kind, in a hall with a letter.</summary>
    private static byte L120PlateOf(L120RoomKind kind, int letter) => kind switch
    {
        L120RoomKind.Terminals => L120PlateTerminal,
        L120RoomKind.Ups => L120PlateUps,
        L120RoomKind.Cables => L120PlateCables,
        L120RoomKind.Wreck => L120PlateStorage,
        _ => (byte)(L120PlateServer + letter),
    };

    /// <summary>
    /// Dresses a laid-out cluster: the server rooms' cooling units, trays and row ends were laid with them; here the walls.
    /// Plates beside the doors between rooms naming the room behind; at the doors onto the passages EXIT inside, DATA HALL
    /// and AUTHORIZED PERSONNEL ONLY outside, fire points and plans; along the passages the hall's stencilled letter by the
    /// crossings and cables run down the walls; a note taped up now and then; fallen ceiling tiles and leaks.
    /// </summary>
    private void L120DressCluster(L120Plan plan, List<L120Room> rooms, List<(int A, int C, bool Vertical, int At, int Start, int Width)> doors, ref Rng rng)
    {
        const int n = L120HallSize;
        int letter = L120HallLetter(plan.Hx, plan.Hz);

        // Between rooms: the plate of the room behind, beside the door, on each side (not every door has them)
        bool noted = !rng.Chance(0.6);
        foreach (var (a, c, vertical, at, start, width) in doors)
        {
            if (plan.At(vertical ? at : start, vertical ? start : at).Kind != TileKind.Doorway) continue; // (walled up since)
            foreach (var (from, to, k) in new[] { (a, c, start + width), (c, a, start - 1) })
            {
                ref Tile w = ref vertical ? ref plan.At(at, k) : ref plan.At(k, at);
                if (w.Kind != TileKind.Wall || w.Variant != 0) continue;
                L120Room rf = rooms[from], rt = rooms[to];
                // (Both sides of the wall there must be room floor: not a corner)
                bool inside = vertical ? k >= Math.Max(rf.Q0, rt.Q0) && k <= Math.Min(rf.Q1, rt.Q1) : k >= Math.Max(rf.P0, rt.P0) && k <= Math.Min(rf.P1, rt.P1);
                if (!inside) continue;
                int dp = vertical ? (rf.P1 < at ? -1 : 1) : 0, dq = vertical ? 0 : (rf.Q1 < at ? -1 : 1);
                if (!noted && rng.Chance(0.4))
                {
                    w.Variant = L120DecoNote;
                    w.Detail = (byte)rng.Range(0, 3);
                    noted = true;
                }
                else if (rng.Chance(rt.Kind == L120RoomKind.Servers ? 0.55 : 0.85))
                {
                    w.Variant = L120DecoPlate;
                    w.Detail = L120PlateOf(rt.Kind, letter);
                }
                else continue;
                w.Pier = L120Toward(dp, dq);
            }
        }

        // The doors onto the passages: EXIT over them inside; outside the hall's plate on one side and the warning on the other
        for (int side = 0; side < 4; side++)
        {
            int dp = side == 0 ? -1 : side == 1 ? 1 : 0, dq = side == 2 ? -1 : side == 3 ? 1 : 0; // (out, toward the passage)
            ArchPier outward = L120Toward(dp, dq), inward = L120Toward(-dp, -dq);
            for (int k = 0; k < n; k++)
            {
                if (L120Ring(plan, side, k).Kind != TileKind.Doorway || k > 0 && L120Ring(plan, side, k - 1).Kind == TileKind.Doorway) continue;
                int len = 1;
                while (k + len < n && L120Ring(plan, side, k + len).Kind == TileKind.Doorway) len++;
                ref Tile mid = ref L120Ring(plan, side, k + len / 2);
                mid.Variant = L120DecoExit;
                mid.Pier = inward;
                mid.Detail = (byte)(rng.Chance(0.2) ? 1 : 0);
                Hang(side, k + len, L120DecoPlate, (byte)(L120PlateHall + letter), outward);
                Hang(side, k - 1, L120DecoAuth, 0, outward);
                if (rng.Chance(0.55)) Hang(side, k + len + 2, L120DecoFire, 0, outward);
                if (rng.Chance(0.3)) Hang(side, k - 3, L120DecoEvac, 0, outward);
                // Inside, a fire point by the door now and then
                if (rng.Chance(0.3)) Hang(side, k - 2, L120DecoFire, 0, inward);
                k += len;
            }
            // The hall's letter by each crossing, and cables down the walls here and there
            Hang(side, 2, L120DecoStencil, (byte)letter, outward);
            Hang(side, n - 3, L120DecoStencil, (byte)letter, outward);
            for (int k = 4; k < n - 4; k++)
                if (rng.Chance(0.012)) Hang(side, k, L120DecoCables, 0, outward);
        }

        // Leaks and fallen tiles over the rooms' floors
        for (int q = 0; q < n; q++)
            for (int p = 0; p < n; p++)
            {
                ref Tile t = ref plan.At(p, q);
                if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stack != 0) continue;
                double v = rng.NextDouble();
                if (v < 0.006) t.Variant = L120Debris;
                else if (v < 0.011 && t.Depth is L120PanelClean or L120PanelDirty) t.Depth = L120PanelWet;
            }

        // A tile of the wall round the hall is dressed only if it is wall, and nothing is on it yet
        void Hang(int side, int k, ushort deco, byte detail, ArchPier face)
        {
            if (k < 0 || k >= n) return;
            ref Tile w = ref L120Ring(plan, side, k);
            if (w.Kind != TileKind.Wall || w.Variant != 0) return;
            w.Variant = deco;
            w.Detail = detail;
            w.Pier = face;
        }
    }

    /// <summary>A tile of the wall round a hall: west (side 0), east, north, south, <paramref name="k"/> along it (-1 to the hall's size).</summary>
    private static ref Tile L120Ring(L120Plan plan, int side, int k)
    {
        if (side == 0) return ref plan.At(-1, k);
        if (side == 1) return ref plan.At(L120HallSize, k);
        if (side == 2) return ref plan.At(k, -1);
        return ref plan.At(k, L120HallSize);
    }

    /// <summary>
    /// Cooling units at the ends of a server room's aisles (against the walk round the room, one of the aisle's two
    /// columns left open), as a real hall's perimeter cooling.
    /// </summary>
    private static void L120PlaceCooling(L120Plan plan, bool alongP, int l0, int l1, int s0, int s1, ref Rng rng)
    {
        for (int s = s0 + 2; s + 1 <= s1; s += 4)
            foreach (int l in new[] { l0, l1 })
            {
                if (!rng.Chance(0.5)) continue;
                ref Tile t = ref L120Along(plan, alongP, l, s);
                Tile other = L120Along(plan, alongP, l, s + 1);
                if (t.Kind != TileKind.Floor || t.Variant != 0 || other.Variant != 0 || t.SupplyBox) continue;
                t.Variant = L120Crac;
                t.Detail = (byte)(rng.Chance(0.3) ? 1 : 0); // (now and then its panel pulled off)
                t.Pier = alongP ? (l == l0 ? ArchPier.East : ArchPier.West) : (l == l0 ? ArchPier.South : ArchPier.North);
            }
    }

    /// <summary>The terminal room's wall of screens: the wall the desks face, two rows of big dead monitors, some smashed, now and then one showing a corrupted frame of a corridor.</summary>
    private static void L120HangScreens(L120Plan plan, L120Room r, ref Rng rng)
    {
        for (int p = r.P0; p <= r.P1; p++)
        {
            ref Tile w = ref plan.At(p, r.Q0 - 1);
            if (w.Kind != TileKind.Wall || w.Variant != 0) continue;
            w.Variant = L120DecoScreens;
            w.Pier = ArchPier.South;
            int lower = rng.Chance(0.12) ? 1 : rng.Chance(0.15) ? 4 : 0, upper = rng.Chance(0.08) ? 2 : rng.Chance(0.15) ? 8 : 0;
            w.Detail = (byte)(lower | upper);
        }
    }

    /// <summary>Storage: steel shelving along the long walls, a KVM cart or two, a mop bucket left in a corner.</summary>
    private static void L120DressStore(L120Plan plan, L120Room r, ref Rng rng)
    {
        var (p0, q0, p1, q1) = L120Inner(r);
        bool alongP = p1 - p0 >= q1 - q0;
        int l0 = alongP ? p0 : q0, l1 = alongP ? p1 : q1, s0 = alongP ? q0 : p0, s1 = alongP ? q1 : p1;
        foreach (var (s, face) in new[] { (s0, alongP ? ArchPier.South : ArchPier.East), (s1, alongP ? ArchPier.North : ArchPier.West) })
            for (int l = l0 + 1; l <= l1 - 1; l++)
            {
                if (rng.Chance(0.15)) continue;
                ref Tile t = ref L120Along(plan, alongP, l, s);
                if (t.SupplyBox) continue;
                t.Variant = L120Shelf;
                t.Pier = face;
                t.Stack = 0;
            }
        // (Clear the row in front of the shelves so they can be reached)
        foreach (int s in new[] { s0 + 1, s1 - 1 })
            for (int l = l0; l <= l1; l++)
            {
                ref Tile t = ref L120Along(plan, alongP, l, s);
                if (t.Variant != L120Shelf) t.Variant = 0;
                t.Stack = 0;
            }
        for (int i = rng.Range(1, 2); i > 0; i--)
        {
            ref Tile t = ref L120Along(plan, alongP, rng.Range(l0 + 1, l1 - 1), s0 + 1);
            t.Variant = L120Kvm;
            t.Pier = (ArchPier)rng.Range(0, 3);
        }
        if (rng.Chance(0.6))
        {
            ref Tile t = ref L120Along(plan, alongP, l0, s1 - 1);
            t.Variant = L120Mop;
            t.Pier = (ArchPier)rng.Range(0, 3);
        }        // (Round 4) A tape library, two to four cabinets, in place of shelving along the first wall
        int run = rng.Range(2, 4), start = rng.Range(l0 + 1, Math.Max(l0 + 1, l1 - 1 - run));
        for (int l = start; l < start + run && l <= l1 - 1; l++)
        {
            ref Tile t = ref L120Along(plan, alongP, l, s0);
            if (t.SupplyBox) continue;
            t.Variant = L120TapeLib;
            t.Pier = alongP ? ArchPier.South : ArchPier.East;
            t.Stack = 0;
        }
    }

    /// <summary>
    /// The White Voids' rooms are "pure white", and nearly all alike: now and then one has one small thing wrong in it (a
    /// crack in a wall, a smudge, a glitched floor tile, a chair or a desk where nothing should be, one panel gone dark, a
    /// sheet of paper, a rack on its own). Never on the way between its doors and windows, nor where you arrive.
    /// </summary>
    private static void L120VoidOddities(L120Plan plan, List<(int I, int J)> list, ref Rng rng)
    {
        const int pitch = 12, off = 3;
        foreach (var (i, j) in list)
        {
            int lp = off + pitch * i, lq = off + pitch * j;
            switch (rng.Range(0, 10))
            {
                case 0:
                    Wall(lp + (rng.Chance(0.5) ? rng.Range(2, 4) : rng.Range(8, 10)), lq, ArchPier.South, L120DecoCrack);
                    break;
                case 1:
                    Wall(lp, lq + rng.Range(8, 9), ArchPier.East, L120DecoSmudge);
                    break;
                case 2:
                    plan.At(lp + 3, lq + 8).Depth = L120VoidGlitch;
                    break;
                case 3:
                    Put(lp + 8, lq + 3, L120Chair, (ArchPier)rng.Range(0, 3));
                    break;
                case 4:
                    Put(lp + 9, lq + 9, L120Terminal, (ArchPier)rng.Range(0, 3));
                    break;
                case 5:
                    plan.At(lp + 3, lq + 3).Ceiling = CeilingKind.L120VoidPanelDead;
                    break;
                case 6:
                    Put(lp + 4, lq + 9, L120Paper, (ArchPier)rng.Range(0, 3));
                    break;
                case 7:
                    Put(lp + 2, lq + 2, L120Rack, (ArchPier)rng.Range(0, 3));
                    break;
                    // (8-10: nothing)
            }
        }

        void Wall(int p, int q, ArchPier face, ushort deco)
        {
            ref Tile w = ref plan.At(p, q);
            if (w.Kind != TileKind.Wall) return;
            w.Variant = deco;
            w.Pier = face;
        }

        void Put(int p, int q, ushort variant, ArchPier face)
        {
            ref Tile t = ref plan.At(p, q);
            if (t.Kind != TileKind.Floor || t.Variant != 0) return;
            t.Variant = variant;
            t.Detail = 0;
            t.Pier = face;
        }
    }
}
