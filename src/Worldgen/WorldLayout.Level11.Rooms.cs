using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 11's ground floors from layout version 9. The lore's open buildings have "interiors which resemble layouts
/// typical of their building type", "always" sparsely furnished, with the lighting, heating and taps working: so each
/// kind keeps its own few things, but they are set out as people would, in rooms of their own. Up to version 8 a
/// ground floor was one room at the front, closed off by a wall a dozen rows in, its furniture placed by rule of thumb
/// (some of it against the plate glass, some on a grid of its own); now
/// <list type="bullet">
/// <item>an office tower's lobby (reception desk facing the way in, benches along the walls, the elevators centred
/// behind it) opens at one end onto an open-plan office: desks in pairs facing the lobby with their chairs behind them,
/// filing cabinets, a copier and a cooler against the walls, and in a wide tower a conference room;</item>
/// <item>a hotel's lobby has its front desk and key rack on the middle of the way in, a sitting area on a rug either
/// side (or a grand piano on one) and a chandelier over the middle, and opens onto a dining room behind;</item>
/// <item>an apartment block's lobby (mailboxes, the directory, the stairs, the dead elevator and the basement door)
/// leads into a corridor with flats off it, a few of them furnished (a bed against the window wall, a kitchenette,
/// a table for two, a radiator), the rest empty; a narrow block has one flat behind the lobby;</item>
/// <item>the stores keep their counters, shelves and machines, clear of the glass and the doors, and have a stockroom
/// behind with metal shelving and a desk (a diner's kitchen door still opens somewhere else);</item>
/// <item>a church's aisle, pews, altar and lights are laid out on the middle of its door, and its stained glass too
/// (<see cref="CityStainedGlass"/>).</item>
/// </list>
/// Every room's lights are spread evenly over it (<see cref="Fit.Lights"/>), its floor is one finish, nothing stands in
/// front of a doorway, a door or an elevator, nor against the plate glass, and seats face their tables.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltCityFitOut = 0xB1F9;

    /// <summary>Whether layout version 9 plans this ground floor anew (big enough for its rooms).</summary>
    private static bool FitsOutV9(CityKind kind, Frame f) => f.D >= 24 && kind switch
    {
        CityKind.Office or CityKind.Hotel => f.W >= 12,
        CityKind.Apartment => f.W >= 9,
        CityKind.Diner or CityKind.Grocery or CityKind.Pharmacy or CityKind.Hardware or CityKind.Clothing or CityKind.Laundromat => f.W >= 7,
        CityKind.Church => f.W >= 9,
        _ => false,
    };

    private static Tile[] SaveLot(Frame f)
    {
        var saved = new Tile[f.W * f.D];
        for (int v = 0; v < f.D; v++)
            for (int u = 0; u < f.W; u++) saved[v * f.W + u] = f.At(u, v);
        return saved;
    }

    private static void RestoreLot(Frame f, Tile[] saved)
    {
        for (int v = 0; v < f.D; v++)
            for (int u = 0; u < f.W; u++) f.At(u, v) = saved[v * f.W + u];
    }

    private void FitOutV9(Frame frame, Spec spec, ref Rng rng)
    {
        var f = new Fit(frame);
        switch (spec.Kind)
        {
            case CityKind.Office: OfficeV9(f, ref rng); break;
            case CityKind.Hotel: HotelV9(f, ref rng); break;
            case CityKind.Apartment: ApartmentV9(f, ref rng); break;
            case CityKind.Church: ChurchV9(f, ref rng); break;
            default: StoreV9(f, spec.Kind, ref rng); break;
        }
    }

    /// <summary>A room inside a ground floor, in the lot's frame (inclusive).</summary>
    private readonly struct Room
    {
        public readonly int U0, U1, V0, V1;
        public Room(int u0, int u1, int v0, int v1) { U0 = u0; U1 = u1; V0 = v0; V1 = v1; }
        public int W => U1 - U0 + 1;
        public int D => V1 - V0 + 1;
        public bool Ok => U1 >= U0 && V1 >= V0;
        public bool Has(int u, int v) => u >= U0 && u <= U1 && v >= V0 && v <= V1;
    }

    /// <summary>
    /// What a version 9 ground floor is planned with: its frame, the middle of its way in, a side doorway if it has one,
    /// and the tiles kept clear in front of every doorway, door and elevator.
    /// </summary>
    private sealed class Fit
    {
        public readonly Frame F;
        public readonly int W, D;
        /// <summary>The middle of the way in from the street (the left of the middle two of an even number).</summary>
        public readonly int C;
        /// <summary>Which side wall has a doorway onto the avenue: -1 the left (u = 0), 1 the right, 0 neither.</summary>
        public readonly int Side;
        private readonly bool[] keep;

        public Fit(Frame f)
        {
            F = f; W = f.W; D = f.D;
            keep = new bool[W * D];
            int lo = -1, hi = -1;
            for (int u = 1; u < W - 1; u++)
                if (f.At(u, 0).Kind is TileKind.Doorway or TileKind.Door) { if (lo < 0) lo = u; hi = u; }
            C = lo < 0 ? (W - 1) / 2 : (lo + hi) / 2;
            for (int v = 1; v < D - 1; v++)
            {
                if (f.At(0, v).Kind == TileKind.Doorway) Side = -1;
                if (f.At(W - 1, v).Kind == TileKind.Doorway) Side = 1;
            }
        }

        public ref Tile At(int u, int v) => ref F.At(u, v);

        public bool Inside(int u, int v) => F.Inside(u, v);

        public bool Free(int u, int v) => Inside(u, v) && !keep[v * W + u] && At(u, v) is { Kind: TileKind.Floor, Variant: 0, Stair: 0, Under: 0 };

        /// <summary>Puts a prop on a free tile (kept-clear tiles are not free). Returns whether it did.</summary>
        public bool Put(int u, int v, ushort prop, ArchPier facing, int stack = 0)
        {
            if (!Free(u, v)) return false;
            F.Prop(u, v, (byte)prop, facing, stack);
            return true;
        }

        /// <summary>A bed (head against the wall, foot toward <paramref name="facing"/>), or nothing if either tile is taken.</summary>
        public bool Bed(int u, int v, ArchPier facing, ushort prop = Props.Bed)
        {
            var (du, dv) = FacingStep(facing);
            if (!Free(u, v) || !Free(u + du, v + dv)) return false;
            Put(u, v, prop, facing, 0);
            Put(u + du, v + dv, prop, facing, 1);
            return true;
        }

        /// <summary>
        /// The long sofa (two across, WorldLayout.Parts.cs), its front toward <paramref name="facing"/>, its left part (as
        /// you look out of its front) on (<paramref name="u"/>, <paramref name="v"/>). Placed whole, so the version 6
        /// pass that widens one-tile sofas leaves it where it is.
        /// </summary>
        public bool LongSofa(int u, int v, ArchPier facing)
        {
            var (du, dv) = facing switch { ArchPier.North => (1, 0), ArchPier.South => (-1, 0), ArchPier.East => (0, 1), _ => (0, -1) };
            if (!Free(u, v) || !Free(u + du, v + dv)) return false;
            Put(u, v, Props.LongSofa, facing, 0);
            Put(u + du, v + dv, Props.LongSofa, facing, 1);
            return true;
        }

        public void Keep(int u, int v)
        {
            if (u >= 0 && v >= 0 && u < W && v < D) keep[v * W + u] = true;
        }

        public void Keep(Room r)
        {
            for (int v = r.V0; v <= r.V1; v++)
                for (int u = r.U0; u <= r.U1; u++) Keep(u, v);
        }

        /// <summary>Keeps the two tiles in front of every doorway, door and elevator in the lot clear, on both sides of it.</summary>
        public void KeepClearOfWays()
        {
            for (int v = 0; v < D; v++)
                for (int u = 0; u < W; u++)
                {
                    if (At(u, v).Kind is not (TileKind.Doorway or TileKind.Door)) continue;
                    foreach (var (du, dv) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        int nu = u + du, nv = v + dv;
                        if (!Inside(nu, nv) || At(nu, nv).Kind != TileKind.Floor) continue;
                        Keep(nu, nv);
                        Keep(nu + du, nv + dv);
                    }
                }
        }

        /// <summary>A wall inside the ground floor; a doorway, door or elevator already there stays.</summary>
        public void Wall(int u, int v, WallPattern pattern)
        {
            if (!Inside(u, v) || At(u, v).Kind is TileKind.Door or TileKind.Doorway) return;
            F.Partition(u, v, pattern, ArchPier.North);
        }

        public void WallAcross(int v, int u0, int u1, WallPattern pattern)
        {
            for (int u = u0; u <= u1; u++) Wall(u, v, pattern);
        }

        public void WallAlong(int u, int v0, int v1, WallPattern pattern)
        {
            for (int v = v0; v <= v1; v++) Wall(u, v, pattern);
        }

        /// <summary>An opening in an inside wall, the wall's material over it.</summary>
        public void Opening(int u, int v)
        {
            if (!Inside(u, v)) return;
            ref Tile t = ref At(u, v);
            if (t.Kind != TileKind.Wall) return;
            t.Kind = TileKind.Doorway;
            t.Variant = 0;
        }

        /// <summary>Hangs a decoration on an inside wall, facing a floor tile.</summary>
        public bool Hang(int u, int v, byte decor, ArchPier facing)
        {
            if (!Inside(u, v)) return false;
            ref Tile t = ref At(u, v);
            if (t.Kind != TileKind.Wall || t.Variant != 0) return false;
            var (du, dv) = FacingStep(facing);
            if (!Inside(u + du, v + dv) || At(u + du, v + dv).Kind != TileKind.Floor) return false;
            t.Variant = decor;
            t.Pier = F.P(facing);
            return true;
        }

        public void Floor(Room r, FloorKind floor)
        {
            for (int v = r.V0; v <= r.V1; v++)
                for (int u = r.U0; u <= r.U1; u++)
                    if (Inside(u, v) && At(u, v).Kind == TileKind.Floor) At(u, v).Floor = floor;
        }

        /// <summary>
        /// Ceiling lights spread evenly over a room, about <paramref name="spacing"/> apart and as far from each wall as
        /// from each other (centred in the room, so a row of them is symmetric in it), the rest plain ceiling.
        /// </summary>
        public void Lights(Room r, int spacing, CeilingKind on, double flicker, ref Rng rng, Room? leave = null)
        {
            for (int v = r.V0; v <= r.V1; v++)
                for (int u = r.U0; u <= r.U1; u++)
                    if (Inside(u, v) && leave?.Has(u, v) != true) At(u, v).Ceiling = CeilingKind.Tile;
            // (Never over a wall or a doorway, nor in a room left to its own lights)
            foreach (int v in Spread(r.V0, r.V1, spacing))
                foreach (int u in Spread(r.U0, r.U1, spacing))
                    if (Inside(u, v) && At(u, v).Kind == TileKind.Floor && leave?.Has(u, v) != true)
                        At(u, v).Ceiling = rng.Chance(flicker) ? CeilingKind.LightFlicker : on;
        }

        /// <summary>Hangs a decoration on the plain wall tile nearest <paramref name="u"/> along a wall across at <paramref name="v"/>.</summary>
        public bool HangNear(int u, int v, byte decor, ArchPier facing, int reach = 4)
        {
            for (int d = 0; d <= reach; d++)
                foreach (int at in new[] { u - d, u + d })
                    if (Hang(at, v, decor, facing)) return true;
            return false;
        }
    }

    /// <summary>
    /// Evenly spaced places along a run of tiles from <paramref name="a0"/> to <paramref name="a1"/>: as many as fit at
    /// about <paramref name="spacing"/> apart, the first and last as far from the ends as half the gap between them,
    /// and the second half the mirror of the first.
    /// </summary>
    internal static List<int> Spread(int a0, int a1, int spacing)
    {
        var at = new List<int>();
        int len = a1 - a0 + 1;
        if (len <= 0) return at;
        int n = Math.Max(1, (len + spacing / 2) / spacing);
        for (int k = 0; k < n; k++)
        {
            int first = k < (n + 1) / 2 ? k : n - 1 - k;
            int off = (int)Math.Floor((2 * first + 1) * len / (2.0 * n));
            at.Add(k < (n + 1) / 2 ? a0 + off : a1 - off);
        }
        return at;
    }

    /// <summary>Evenly spread starts of groups <paramref name="size"/> wide with <paramref name="gap"/> between them, across a run.</summary>
    private static List<int> Groups(int a0, int a1, int size, int gap)
    {
        var at = new List<int>();
        int len = a1 - a0 + 1, n = (len + gap) / (size + gap);
        if (n <= 0) return at;
        int used = n * size + (n - 1) * gap, start = a0 + (len - used) / 2;
        for (int k = 0; k < n; k++) at.Add(start + k * (size + gap));
        return at;
    }

    private static ArchPier Across(int dir) => dir > 0 ? ArchPier.East : ArchPier.West;

    // ================= Offices =================

    /// <summary>
    /// An office tower's ground floor: a marble lobby with the reception desk on the middle of the way in, benches and
    /// plants along the walls, the elevators centred behind the desk and the stairs into the ceiling in a back corner;
    /// through a wide opening at the other end, an open-plan office with a conference room in a wide tower.
    /// </summary>
    private void OfficeV9(Fit f, ref Rng rng)
    {
        int W = f.W, D = f.D, c = f.C, back = 13;
        f.WallAcross(back, 1, W - 2, WallPattern.Drywall);
        var lobby = new Room(1, W - 2, 1, back - 1);
        var suite = new Room(1, W - 2, back + 1, D - 2);
        f.Floor(suite, FloorKind.OfficeCarpet);
        // The elevators, centred behind the desk (two pairs either side of the call button in a wide lobby)
        int callU;
        if (W >= 14)
        {
            Elevators(f.F, back, c - 3);
            Elevators(f.F, back, c + 2);
            callU = c;
        }
        else
        {
            Elevators(f.F, back, c - 1);
            callU = c + 1;
        }
        // The stairs into the ceiling against the back wall, at the end away from a side door; the way through to the
        // offices at the other end
        bool stairsLeft = f.Side != -1;
        int su = stairsLeft ? 1 : W - 3, ou = stairsLeft ? W - 3 : 1;
        while (ou > 1 && ou < W - 3 && (f.At(ou, back).Kind != TileKind.Wall || f.At(ou + 1, back).Kind != TileKind.Wall)) ou += stairsLeft ? -1 : 1;
        f.Opening(ou, back);
        f.Opening(ou + 1, back);
        Stairs(f.F, su, back - 3, PublicStairWidth);
        WallDecor(f.F, callU, back, Decor.CallButton);
        f.HangNear(stairsLeft ? 3 : W - 4, back, Decor.EvacMap, ArchPier.North);
        f.HangNear(stairsLeft ? ou - 1 : ou + 2, back, Decor.Clock, ArchPier.North);
        f.KeepClearOfWays();

        // Reception, facing the way in
        f.Put(c, 7, Props.ReceptionDesk, ArchPier.North);
        f.Put(c, 8, Props.OfficeChair, ArchPier.North);
        // Benches along both walls between plants, facing into the lobby
        foreach (int u in new[] { 1, W - 2 })
        {
            ArchPier inward = u == 1 ? ArchPier.East : ArchPier.West;
            f.Put(u, 3, Props.Ficus, ArchPier.North);
            f.Put(u, 4, Props.Bench, inward);
            f.Put(u, 5, Props.Bench, inward);
            f.Put(u, 6, Props.Ficus, ArchPier.North);
        }
        // An Almond Water machine and a cooler against the wall on the stairs' side (which never has a side door)
        int vu = stairsLeft ? 1 : W - 2;
        f.Put(vu, 7, Props.Vending, Across(stairsLeft ? 1 : -1));
        f.Put(vu, 8, Props.Cooler, Across(stairsLeft ? 1 : -1));
        f.Put(c + 3, 2, Props.TrashCan, ArchPier.North);
        f.Lights(lobby, 4, CeilingKind.LightOn, 0.06, ref rng);

        OfficeFloor(f, suite, ou, ref rng);
    }

    /// <summary>The open-plan office behind the lobby, entered at <paramref name="ou"/>.</summary>
    private void OfficeFloor(Fit f, Room suite, int ou, ref Rng rng)
    {
        int W = f.W, back = suite.V0 - 1;
        bool openingLeft = ou < W / 2;
        // A conference room in the back corner away from the way in, in a wide tower
        Room? conf = null;
        if (W >= 22 && suite.D >= 12)
        {
            int cw = 7, u0 = openingLeft ? W - 1 - cw : 1, u1 = u0 + cw - 1, v0 = suite.V1 - 6;
            int wallU = openingLeft ? u0 - 1 : u1 + 1;
            f.WallAcross(v0 - 1, Math.Min(u0, wallU), Math.Max(u1, wallU), WallPattern.Drywall);
            f.WallAlong(wallU, v0, suite.V1, WallPattern.Drywall);
            f.Opening(wallU, v0 + 2);
            var cr = new Room(u0, u1, v0, suite.V1);
            conf = cr;
            // A long table, chairs down both sides facing it, a whiteboard on the wall at its end
            int t0 = cr.U0 + 2, t1 = cr.U1 - 2, tv = cr.V0 + 3;
            for (int u = t0; u <= t1; u++)
            {
                f.Put(u, tv, Props.ConferenceTable, ArchPier.North);
                f.Put(u, tv - 1, Props.OfficeChair, ArchPier.South);
                f.Put(u, tv + 1, Props.OfficeChair, ArchPier.North);
            }
            int bu = (cr.U0 + cr.U1) / 2;
            // (Facing south, the left half is the one at the smaller u: L4BoardLeft)
            if (f.Hang(bu, cr.V0 - 1, Decor.WhiteboardLeft, ArchPier.South) && !f.Hang(bu + 1, cr.V0 - 1, Decor.WhiteboardRight, ArchPier.South))
                f.At(bu, cr.V0 - 1).Variant = 0;
            f.Put(openingLeft ? cr.U1 : cr.U0, cr.V1, Props.Ficus, ArchPier.North);
        }
        bool InConf(int u, int v) => conf?.Has(u, v) == true;
        f.KeepClearOfWays();
        // Along the walls: filing cabinets by the way in, a copier and a cooler across from them, bookshelves at the back
        int nearU = openingLeft ? 1 : W - 2, farU = openingLeft ? W - 2 : 1;
        ArchPier fromNear = Across(openingLeft ? 1 : -1), fromFar = Across(openingLeft ? -1 : 1);
        for (int v = back + 3; v <= back + 5; v++) f.Put(nearU, v, Props.FilingCabinet, fromNear);
        f.Put(farU, back + 2, Props.Copier, fromFar);
        f.Put(farU, back + 4, Props.Cooler, fromFar);
        f.Put(nearU, suite.V1, Props.Ficus, ArchPier.North);
        // Desks in pairs, side by side, facing the lobby, a chair behind each; aisles between the pairs and the rows
        // (A row is laid whole or not at all: the floor is not full, but what is there is in order)
        int a0 = 3, a1 = W - 4;
        int rowsLaid = 0;
        foreach (int v in new[] { back + 3, back + 7, back + 11 })
        {
            if (v + 1 >= suite.V1) break;
            if (rowsLaid > 0 && !rng.Chance(0.75)) continue;
            rowsLaid++;
            foreach (int u in Groups(a0, a1, 2, 2))
            {
                if (InConf(u, v + 1) || InConf(u + 1, v + 1) || InConf(u, v - 1) || InConf(u + 1, v - 1) || InConf(u - 1, v) || InConf(u + 2, v)) continue;
                for (int k = 0; k < 2; k++)
                {
                    if (!f.Free(u + k, v) || !f.Free(u + k, v + 1)) continue;
                    f.Put(u + k, v, Props.Desk, ArchPier.North);
                    f.Put(u + k, v + 1, Props.OfficeChair, ArchPier.North);
                }
            }
        }
        for (int u = 3; u <= W - 4; u += 3)
        {
            if (InConf(u, suite.V1) || InConf(u, suite.V1 - 1)) continue;
            f.Put(u, suite.V1, Props.OfficeBookshelf, ArchPier.North);
        }
        // A corkboard on the lobby wall, over the first row
        f.HangNear(openingLeft ? ou + 3 : ou - 2, back, Decor.Corkboard, ArchPier.South);
        // The open office's lights, and the conference room's own
        f.Lights(suite, 4, CeilingKind.LightOn, 0.08, ref rng, conf);
        if (conf is Room room) f.Lights(room, 3, CeilingKind.LightOn, 0, ref rng);
    }

    // ================= Hotels =================

    /// <summary>
    /// A hotel's ground floor: the front desk on the middle of the way in, the key rack behind it, a sitting area on a
    /// rug either side (one a grand piano now and then), palms by the door, a chandelier over the middle; the elevators
    /// to one side of the desk and, through a wide opening at the other end, a dining room of tables laid for nobody.
    /// </summary>
    private void HotelV9(Fit f, ref Rng rng)
    {
        int W = f.W, D = f.D, c = f.C, back = 13;
        f.WallAcross(back, 1, W - 2, WallPattern.Hotel);
        var lobby = new Room(1, W - 2, 1, back - 1);
        var dining = new Room(1, W - 2, back + 1, D - 2);
        f.Floor(dining, FloorKind.HotelCarpet);
        int eu = c + 5 <= W - 2 ? c + 3 : W - 4;
        Elevators(f.F, back, eu);
        int ou = 1;
        f.Opening(ou, back);
        f.Opening(ou + 1, back);
        f.Hang(c, back, Decor.KeyRack, ArchPier.North);
        f.Hang(Math.Max(3, c - 4), back, Decor.Landscape, ArchPier.North);
        f.Hang(eu + 2, back, Decor.CallPlate, ArchPier.North);
        f.KeepClearOfWays();

        for (int u = c - 1; u <= c + 1; u++) f.Put(u, 10, Props.FrontDesk, ArchPier.North);
        if (!f.Put(c - 3, back - 1, Props.GrandfatherClock, ArchPier.North)) f.Put(c - 2, back - 1, Props.GrandfatherClock, ArchPier.North);
        f.Put(c + 2, 11, Props.LuggageCart, ArchPier.North);
        f.Put(Math.Min(W - 2, eu + 2), back - 1, Props.AshtrayStand, ArchPier.North);
        // Palms either side of the way in, a row back from the glass
        f.Put(c - 2, 2, Props.Palm, ArchPier.North);
        f.Put(c + 2, 2, Props.Palm, ArchPier.North);
        // Sitting areas, four wide and mirrored about the middle: a long sofa facing two coffee tables, a wing chair at
        // either end of them, a lamp at the outer end of the sofa, on a rug (in a wide lobby one is a grand piano now and then)
        int a = Math.Max(1, c - 5 - (W - 2) / 8), a2 = 2 * c - a - 3;
        bool two = a + 3 <= c - 2 && a2 + 3 <= W - 2;
        bool piano = two && W >= 16 && rng.Chance(0.45);
        foreach (int g in two ? new[] { a, a2 } : new[] { 1 })
        {
            bool right = g > c;
            if (piano && right)
            {
                // The piano's model brings its own bench, standing in the tile in front of the keyboard (west of it): keep that clear
                f.Put(g + 1, 5, Props.GrandPiano, ArchPier.West);
                continue;
            }
            f.Floor(new Room(g, g + 3, 4, 6), FloorKind.HotelRug);
            f.Put(g + 1, 5, Props.CoffeeTable, ArchPier.North);
            f.Put(g + 2, 5, Props.CoffeeTable, ArchPier.North);
            f.LongSofa(g + 1, 6, ArchPier.North);
            f.Put(g, 5, Props.WingChair, ArchPier.East);
            f.Put(g + 3, 5, Props.WingChair, ArchPier.West);
            f.Put(right ? g + 3 : g, 6, Props.FloorLamp, ArchPier.North);
        }
        f.Lights(lobby, 4, CeilingKind.LightLit, 0.04, ref rng);
        if (f.Inside(c, 6)) f.At(c, 6).Ceiling = CeilingKind.Chandelier;

        // The dining room: tables laid for nobody, four chairs to a table, a sideboard against the back wall
        int[] rows = dining.D >= 12 ? new[] { back + 4, back + 9 } : new[] { back + 4 };
        var tables = new List<(int, int)>();
        foreach (int v in rows)
            foreach (int u in Groups(2, W - 3, 3, 1))
            {
                int tu = u + 1;
                if (!f.Free(tu, v) || !rng.Chance(0.85)) continue;
                f.Put(tu, v, Props.DiningTable, ArchPier.North);
                f.Put(tu - 1, v, Props.HotelChair, ArchPier.East);
                f.Put(tu + 1, v, Props.HotelChair, ArchPier.West);
                f.Put(tu, v - 1, Props.HotelChair, ArchPier.South);
                f.Put(tu, v + 1, Props.HotelChair, ArchPier.North);
                tables.Add((tu, v));
            }
        for (int u = 3; u <= W - 4; u += 4) f.Put(u, dining.V1, Props.ConsoleTable, ArchPier.North);
        f.Put(1, dining.V1, Props.Candelabra, ArchPier.North);
        f.Put(W - 2, dining.V1, Props.Candelabra, ArchPier.North);
        f.Put(W - 2, back + 1, Props.CurioCabinet, ArchPier.West);
        f.HangNear(c + 2, back, Decor.Mirror, ArchPier.South);
        f.Lights(dining, 4, CeilingKind.LightLit, 0.04, ref rng);
        // A chandelier over the table nearest the middle of the room
        if (tables.Count > 0)
        {
            int cu = (dining.U0 + dining.U1) / 2, cv = (dining.V0 + dining.V1) / 2;
            var (bu, bv) = tables[0];
            foreach (var (tu, tv) in tables)
                if (Math.Abs(tu - cu) + Math.Abs(tv - cv) < Math.Abs(bu - cu) + Math.Abs(bv - cv)) (bu, bv) = (tu, tv);
            f.At(bu, bv).Ceiling = CeilingKind.Chandelier;
        }
    }

    // ================= Apartment blocks =================

    /// <summary>
    /// An apartment block's ground floor: the lobby as before (mailboxes, the directory, stairs into the ceiling, the
    /// elevator that is out of order and the basement door that is not locked), and behind it a corridor with flats
    /// either side (one side in a narrower block), a few furnished and the rest empty; a block too narrow for a
    /// corridor has one flat behind its lobby.
    /// </summary>
    private void ApartmentV9(Fit f, ref Rng rng)
    {
        int W = f.W, D = f.D, c = f.C, back = 8, mid = W / 2;
        f.WallAcross(back, 1, W - 2, WallPattern.CityPlaster);
        var lobby = new Room(1, W - 2, 1, back - 1);
        int stairWidth = PublicStairWidth;
        Stairs(f.F, 1, back - 3, stairWidth);
        int du = stairWidth > 1 && mid - 2 <= stairWidth ? stairWidth + 1 : mid - 2;
        Door(f.F, du, back);
        if (W >= 9) Elevators(f.F, back, W - 4);
        // The way through to the flats: two wide, as near the middle as the door, the stairs and the elevator allow
        bool Clear(int u) => u > stairWidth && u <= W - 2 && u != du && f.At(u, back).Kind == TileKind.Wall;
        int ou = -1;
        for (int d = 0; d < W && ou < 0; d++)
            foreach (int u in new[] { c - d, c + d })
                if (ou < 0 && Clear(u) && Clear(u + 1)) ou = u;
        if (ou < 0)
        {
            // No room for two: one wide
            for (int d = 0; d < W && ou < 0; d++)
                foreach (int u in new[] { c - d, c + d })
                    if (ou < 0 && Clear(u)) ou = u;
        }
        if (ou < 0) { f.KeepClearOfWays(); f.Lights(lobby, 3, CeilingKind.LightOn, 0.05, ref rng); return; }
        bool wide = Clear(ou + 1);
        f.Opening(ou, back);
        if (wide) f.Opening(ou + 1, back);
        // Mailboxes, the directory and now and then a poster, on what is left of the lobby's back wall
        var slots = new List<int>();
        for (int u = stairWidth + 1; u <= W - 2; u++)
            if (f.At(u, back).Kind == TileKind.Wall && f.At(u, back).Variant == 0) slots.Add(u);
        slots.Sort((a, b) => Math.Abs(a - c).CompareTo(Math.Abs(b - c)));
        byte[] hang = { Decor.Mailboxes, Decor.Mailboxes, Decor.Directory, Decor.MissingPoster };
        int h = 0;
        foreach (int u in slots)
        {
            if (h >= hang.Length || hang[h] == Decor.MissingPoster && !rng.Chance(0.5)) break;
            if (WallDecorAt(f, u, back, hang[h])) h++;
        }
        f.KeepClearOfWays();
        // Heating: a radiator under each front window; a bench against the wall
        f.Put(W - 2, 2, Props.Radiator, ArchPier.West);
        if (f.Free(1, 2)) f.Put(1, 2, Props.Radiator, ArchPier.East);
        f.Put(W - 2, 4, Props.Bench, ArchPier.West);
        f.Lights(lobby, 3, CeilingKind.LightOn, 0.05, ref rng);

        int cw = wide ? 2 : 1;
        var rest = new Room(1, W - 2, back + 1, D - 2);
        int leftW = ou - 2, rightW = W - 2 - (ou + cw);  // the flats' widths either side of a corridor (and its walls)
        if (leftW >= 4 && rightW >= 4)
        {
            var corridor = new Room(ou, ou + cw - 1, rest.V0, rest.V1);
            f.WallAlong(ou - 1, rest.V0, rest.V1, WallPattern.CityPlaster);
            f.WallAlong(ou + cw, rest.V0, rest.V1, WallPattern.CityPlaster);
            f.Lights(corridor, 4, CeilingKind.LightOn, 0.08, ref rng);
            Flats(f, new Room(1, ou - 2, rest.V0, rest.V1), ou - 1, 1, ref rng);
            Flats(f, new Room(ou + cw + 1, W - 2, rest.V0, rest.V1), ou + cw, -1, ref rng);
        }
        else if (Math.Max(leftW, rightW) >= 4)
        {
            // One side only: the corridor runs on the narrow side, the flats on the other
            bool flatsRight = rightW >= leftW;
            var corridor = flatsRight ? new Room(1, ou + cw - 1, rest.V0, rest.V1) : new Room(ou, W - 2, rest.V0, rest.V1);
            int wallU = flatsRight ? ou + cw : ou - 1;
            f.WallAlong(wallU, rest.V0, rest.V1, WallPattern.CityPlaster);
            f.Floor(corridor, FloorKind.HouseLino);
            f.Lights(corridor, 4, CeilingKind.LightOn, 0.08, ref rng);
            if (flatsRight) Flats(f, new Room(wallU + 1, W - 2, rest.V0, rest.V1), wallU, -1, ref rng);
            else Flats(f, new Room(1, wallU - 1, rest.V0, rest.V1), wallU, 1, ref rng);
        }
        else Flat(f, rest, ou, ref rng);
    }

    private static bool WallDecorAt(Fit f, int u, int v, byte decor) => f.Hang(u, v, decor, ArchPier.North);

    /// <summary>
    /// Flats in a row along a corridor wall at <paramref name="wallU"/> (the corridor toward <paramref name="toCorridor"/>
    /// of them): two long ones in a wide row, three shorter ones in a narrow one, each with a doorway near its front.
    /// </summary>
    private void Flats(Fit f, Room side, int wallU, int toCorridor, ref Rng rng)
    {
        int n = side.W >= 6 ? 2 : 3;
        int len = (side.D - (n - 1)) / n;
        int v = side.V0;
        for (int k = 0; k < n; k++)
        {
            int v1 = k == n - 1 ? side.V1 : v + len - 1;
            var unit = new Room(side.U0, side.U1, v, v1);
            if (k < n - 1) f.WallAcross(v1 + 1, side.U0, side.U1, WallPattern.InteriorBeige);
            f.Opening(wallU, v + 1);
            f.KeepClearOfWays();
            Studio(f, unit, toCorridor, rng.Chance(0.6), ref rng);
            v = v1 + 2;
        }
    }

    /// <summary>
    /// One flat, its window wall on the far side from its door: a bed against the window wall at the back, a nightstand
    /// and a wardrobe; a kitchenette along the front wall; a table for two; a radiator under the window. An empty flat
    /// has only its floor and lights.
    /// </summary>
    private void Studio(Fit f, Room r, int toCorridor, bool furnished, ref Rng rng)
    {
        f.Floor(r, rng.Chance(0.5) ? FloorKind.HouseWood : FloorKind.HouseCarpet);
        f.Lights(r, 4, CeilingKind.LightOn, 0.05, ref rng);
        int wu = toCorridor > 0 ? r.U0 : r.U1, du = toCorridor;
        ArchPier inward = Across(du);
        int U(int k) => wu + du * k;
        // Heating, working, under the window
        f.Put(wu, (r.V0 + r.V1) / 2, Props.Radiator, inward);
        if (!furnished) return;
        // The bed: its head against the window wall, by the back wall, a nightstand beside it
        f.Bed(wu, r.V1, inward);
        f.Put(wu, r.V1 - 1, Props.Nightstand, inward);
        f.Put(wu, r.V0, Props.Wardrobe, inward);
        // A kitchenette along the front wall, from the window wall in
        ushort[] kitchen = { Props.Fridge, Props.KitchenCounter, Props.Stove };
        for (int k = 1, i = 0; k < r.W - 1 && i < kitchen.Length; k++)
            if (f.Put(U(k), r.V0, kitchen[i], ArchPier.South, kitchen[i] == Props.KitchenCounter ? 1 : 0)) i++;
        // A table for two in the middle of the room
        if (r.W >= 4 && r.D >= 6)
        {
            int tu = U(r.W >= 5 ? 2 : 1), tv = r.V0 + 2;
            if (f.Put(tu, tv, Props.RoundTable, ArchPier.North))
            {
                f.Put(tu, tv + 1, Props.HotelChair, ArchPier.North);
                if (!f.Put(tu - du, tv, Props.HotelChair, Across(du))) f.Put(tu + du, tv, Props.HotelChair, Across(-du));
            }
        }
        // A sofa across from a television in a flat wide enough: the set against the corridor wall, a coffee table between
        if (r.W >= 7 && r.D >= 7)
        {
            int mv = (r.V0 + r.V1) / 2 + 1;
            if (f.Put(U(r.W - 1), mv, Props.Tv, Across(-du)))
            {
                f.Put(U(r.W - 3), mv, Props.CoffeeTable, ArchPier.North);
                f.LongSofa(U(r.W - 5), mv, Across(du));
            }
        }
        // Something on the wall
        if (rng.Chance(0.5)) f.Hang(U(1), r.V1 + 1, Decor.HousePainting, ArchPier.North);
    }

    /// <summary>
    /// The flat behind a narrow block's lobby: a living room (sofa, coffee table on a rug, television, a kitchenette and
    /// a table) and, through the wall behind it, a bedroom and a bathroom.
    /// </summary>
    private void Flat(Fit f, Room r, int ou, ref Rng rng)
    {
        int W = f.W, split = r.V0 + r.D / 2;
        f.WallAcross(split, r.U0, r.U1, WallPattern.InteriorBeige);
        var living = new Room(r.U0, r.U1, r.V0, split - 1);
        int s = r.U0 + Math.Max(3, r.W / 2);
        f.WallAlong(s, split + 1, r.V1, WallPattern.InteriorBeige);
        var bed = new Room(r.U0, s - 1, split + 1, r.V1);
        var bath = new Room(s + 1, r.U1, split + 1, r.V1);
        f.Opening(Math.Min(s - 1, Math.Max(r.U0 + 1, ou)), split);
        f.Opening(s, split + 2);
        f.KeepClearOfWays();
        f.Floor(living, FloorKind.HouseWood);
        f.Floor(bed, FloorKind.HouseCarpet);
        f.Floor(bath, FloorKind.HouseTile);
        // Living room: the television against one wall, the sofa facing it across a coffee table on a rug
        int lv = (living.V0 + living.V1) / 2;
        f.Put(r.U0, lv, Props.Tv, ArchPier.East);
        f.Floor(new Room(r.U0 + 1, r.U0 + 3, lv - 1, lv + 1), FloorKind.HouseRug);
        f.Put(r.U0 + 2, lv, Props.CoffeeTable, ArchPier.North);
        f.LongSofa(r.U0 + 4, lv + 1, ArchPier.West);
        f.Put(r.U0, lv - 2, Props.FloorLamp, ArchPier.North);
        f.Put(r.U1, living.V0 + 1, Props.Radiator, ArchPier.West);
        // The kitchenette along the far wall, a table for two beside it
        int ku = r.U1;
        f.Put(ku, living.V1, Props.Stove, ArchPier.West);
        f.Put(ku, living.V1 - 1, Props.KitchenCounter, ArchPier.West, 1);
        f.Put(ku, living.V1 - 2, Props.Fridge, ArchPier.West);
        if (f.Put(ku - 2, living.V1 - 1, Props.RoundTable, ArchPier.North))
        {
            f.Put(ku - 3, living.V1 - 1, Props.HotelChair, ArchPier.East);
            f.Put(ku - 2, living.V1 - 2, Props.HotelChair, ArchPier.South);
        }
        f.Hang(r.U0 + 2, split, Decor.FamilyPhoto, ArchPier.North);
        // Bedroom: the bed's head against the back wall, a nightstand either side, a wardrobe
        int bu = bed.U0 + 1;
        f.Bed(bu, bed.V1, ArchPier.North);
        f.Put(bu - 1, bed.V1, Props.Nightstand, ArchPier.North);
        f.Put(bu + 1, bed.V1, Props.Nightstand, ArchPier.North);
        f.Put(bed.U0, bed.V0, Props.Wardrobe, ArchPier.East);
        f.Put(bed.U0, (bed.V0 + bed.V1) / 2, Props.Radiator, ArchPier.East);
        // Bathroom: a bath along the back wall, a toilet, the cabinet
        f.Put(bath.U0, bath.V1, Props.Bathtub, ArchPier.East, 0);
        f.Put(bath.U0 + 1, bath.V1, Props.Bathtub, ArchPier.East, 1);
        f.Put(bath.U1, bath.V0 + 2, Props.Toilet, ArchPier.West);
        f.Put(bath.U1, bath.V0 + 4, Props.MedCabinet, ArchPier.West);
        foreach (var room in new[] { living, bed, bath }) f.Lights(room, 4, CeilingKind.LightOn, 0.04, ref rng);
    }

    // ================= Stores =================

    /// <summary>
    /// A store's ground floor: the sales floor at the front, as deep as before, its counters, shelves and machines set
    /// out clear of the plate glass and the doors; behind it a stockroom through a door at one end (a diner's kitchen
    /// door still opens into another restaurant altogether, and its back stays shut).
    /// </summary>
    private void StoreV9(Fit f, CityKind kind, ref Rng rng)
    {
        int W = f.W, D = f.D, c = f.C, mid = W / 2;
        int depth = kind switch { CityKind.Diner => 11, CityKind.Grocery => 16, CityKind.Hardware => 14, _ => 12 };
        int back = depth + 1, last = back - 1;
        WallPattern wall = kind switch { CityKind.Diner => WallPattern.SnackMall, CityKind.Clothing => WallPattern.InteriorBeige, _ => WallPattern.CityPlaster };
        f.WallAcross(back, 1, W - 2, wall);
        var floor = new Room(1, W - 2, 1, last);
        var stock = new Room(1, W - 2, back + 1, D - 2);
        // The way through to the back: a diner's kitchen door, or a doorway into the stockroom
        int su = W - 3;
        if (kind == CityKind.Diner) Door(f.F, su, back);
        else f.Opening(su, back);
        // Nothing against the glass: keep the row inside it clear
        for (int u = 1; u < W - 1; u++)
            if ((f.At(u, 0).Detail & CityDetail.Storefront) != 0) f.Keep(u, 1);
        f.KeepClearOfWays();
        switch (kind)
        {
            case CityKind.Diner:
            {
                // The counter down the right with stools at it, the kitchen behind; booths and tables on the left
                int counter = W - 4;
                for (int v = 3; v < last; v++)
                {
                    f.Put(counter, v, Props.SnackCounter, ArchPier.West, v == 3 ? 1 : v == 5 ? 2 : 0);
                    if (v % 2 == 1) f.Put(counter - 1, v, Props.CafeChair, ArchPier.East);
                }
                f.Put(W - 2, 3, Props.Stove, ArchPier.West);
                f.Put(W - 2, 5, Props.Fryer, ArchPier.West);
                f.Put(W - 2, 7, Props.DrinkFridge, ArchPier.West);
                f.Put(W - 2, 9, Props.KitchenCounter, ArchPier.West, 1);
                foreach (int u in Groups(2, counter - 3, 3, 1))
                    foreach (int v in new[] { 3, 7 })
                    {
                        if (v + 1 >= last) continue;
                        int tu = u + 1;
                        if (!f.Put(tu, v, Props.CafeTable, ArchPier.North)) continue;
                        f.Put(tu - 1, v, Props.CafeChair, ArchPier.East);
                        f.Put(tu + 1, v, Props.CafeChair, ArchPier.West);
                    }
                f.Hang(mid, back, Decor.MenuBoard, ArchPier.North);
                f.Put(1, last, Props.TrashCan, ArchPier.North);
                f.Lights(floor, 3, CeilingKind.LightOn, 0.06, ref rng);
                return;
            }
            case CityKind.Grocery:
            {
                // Checkouts by the way in, carts along the wall; aisles of shelves back to back; fridges along the back
                foreach (int u in Groups(2, W - 3, 1, 2)) if (Math.Abs(u - c) > 1) f.Put(u, 3, Props.SnackCounter, ArchPier.West, 1);
                for (int v = 2; v <= 4; v++) f.Put(1, v, Props.ShoppingCart, ArchPier.East);
                f.Put(W - 2, 3, Props.Vending, ArchPier.West);
                int gap = (6 + last) / 2;
                foreach (int u in Groups(2, W - 3, 2, 2))
                    for (int v = 6; v < last - 1; v++)
                    {
                        if (v == gap) continue;
                        ushort shelf = (u / 4) % 2 == 0 ? Props.PantryShelf : Props.SnackShelf;
                        f.Put(u, v, shelf, ArchPier.West);
                        f.Put(u + 1, v, shelf, ArchPier.East);
                    }
                for (int u = 1; u < W - 1; u++) f.Put(u, last, u % 3 == 0 ? Props.Fridge : Props.DrinkFridge, ArchPier.North);
                break;
            }
            case CityKind.Pharmacy:
            {
                // Cabinets along both walls, two shelves back to back down the middle, the dispensing counter across the back
                for (int v = 2; v < last - 1; v++)
                {
                    f.Put(1, v, Props.MedCabinet, ArchPier.East);
                    f.Put(W - 2, v, Props.MedCabinet, ArchPier.West);
                }
                for (int v = 4; v < last - 2; v++)
                {
                    f.Put(c, v, Props.SnackShelf, ArchPier.West);
                    f.Put(c + 1, v, Props.PantryShelf, ArchPier.East);
                }
                for (int u = c - 2; u <= c + 2; u++) f.Put(u, last, Props.SnackCounter, ArchPier.North, u == c ? 1 : 0);
                f.Put(W - 3, 2, Props.Vending, ArchPier.West);
                if (rng.Chance(0.5)) f.Hang(c - 3, back, Decor.MissingPoster, ArchPier.North);
                break;
            }
            case CityKind.Hardware:
            {
                // Tool racks and barrels down one wall, shelving in back-to-back runs, the counter by the way in
                for (int v = 2; v < last; v++) f.Put(1, v, v % 3 != 1 ? Props.ToolRack : Props.NailBarrel, v % 3 != 1 ? ArchPier.East : ArchPier.North);
                foreach (int u in Groups(3, W - 4, 2, 2))
                    for (int v = 4; v < last - 1; v++)
                    {
                        f.Put(u, v, Props.ToolShelf, ArchPier.West);
                        f.Put(u + 1, v, Props.ToolShelf, ArchPier.East);
                    }
                f.Put(W - 2, 3, Props.SnackCounter, ArchPier.West, 1);
                f.Put(W - 2, last, Props.Workbench, ArchPier.West);
                f.Put(W - 2, last - 1, Props.CableSpool, ArchPier.North);
                f.Put(W - 2, last - 3, Props.Pallet, ArchPier.North);
                if (rng.Chance(0.5)) f.Put(W - 2, last - 2, Props.Toolbox, ArchPier.West);
                break;
            }
            case CityKind.Clothing:
            {
                // Racks in rows across the floor, wardrobes and dressers along the walls, a mirror and the counter at the back
                foreach (int v in new[] { 3, 6, 9 })
                {
                    if (v >= last - 1) continue;
                    foreach (int u in Groups(3, W - 4, 1, 1)) f.Put(u, v, Props.ClothesRack, ArchPier.North);
                }
                for (int v = 2; v < last; v += 2)
                {
                    f.Put(1, v, Props.Wardrobe, ArchPier.East);
                    f.Put(W - 2, v, Props.Dresser, ArchPier.West);
                }
                f.Put(c + 2, last, Props.SnackCounter, ArchPier.North, 1);
                f.Hang(c - 1, back, Decor.HouseMirror, ArchPier.North);
                f.Put(c - 2, last, Props.CoatStand, ArchPier.North);
                if (rng.Chance(0.5)) f.Put(c, last, Props.Suitcase, ArchPier.North);
                break;
            }
            case CityKind.Laundromat:
            {
                // Washers and dryers down both walls facing in, folding tables down the middle, chairs along the back
                for (int v = 3; v <= last; v++)
                {
                    f.Put(1, v, Props.Laundry, ArchPier.East, 0);
                    f.Put(W - 2, v, Props.Laundry, ArchPier.West, 1);
                }
                for (int v = 4; v < last - 1; v += 3) f.Put(c, v, Props.FoldingTable, ArchPier.North);
                foreach (int u in Groups(3, W - 4, 1, 1)) if (Math.Abs(u - c) > 1) f.Put(u, last, Props.FoldingChair, ArchPier.North);
                f.Put(c, last, Props.LaundryCart, ArchPier.North);
                f.Put(W - 2, 2, Props.Vending, ArchPier.West);
                f.Put(1, 2, Props.Wastebasket, ArchPier.North);
                if (rng.Chance(0.4)) f.Hang(c, back, Decor.MissingPoster, ArchPier.North);
                break;
            }
        }
        f.Lights(floor, 3, CeilingKind.LightOn, 0.06, ref rng);
        Stockroom(f, stock, su, kind, ref rng);
    }

    /// <summary>A store's stockroom: bare concrete, metal shelving along the walls, boxes, a pallet, a desk by the door.</summary>
    private void Stockroom(Fit f, Room r, int doorU, CityKind kind, ref Rng rng)
    {
        f.Floor(r, FloorKind.CityGarage);
        f.KeepClearOfWays();
        for (int u = r.U0; u <= r.U1; u++) if (u % 2 == 1) f.Put(u, r.V1, Props.Shelf, ArchPier.North);
        for (int v = r.V0 + 1; v < r.V1 - 1; v += 2) f.Put(r.U0, v, Props.Shelf, ArchPier.East);
        ushort stock = kind switch
        {
            CityKind.Hardware => Props.ToolShelf,
            CityKind.Grocery or CityKind.Pharmacy => Props.PantryShelf,
            CityKind.Clothing => Props.ClothesRack,
            _ => Props.Shelf,
        };
        int mu = (r.U0 + r.U1) / 2;
        for (int v = r.V0 + 3; v < r.V1 - 2; v++) f.Put(mu, v, stock, ArchPier.West);
        f.Put(r.U0 + 2, r.V1 - 2, Props.CardboardBoxes, ArchPier.North);
        f.Put(r.U0 + 3, r.V1 - 2, Props.Pallet, ArchPier.North);
        if (rng.Chance(0.6)) f.Put(r.U0 + 2, r.V1 - 3, Props.CardboardBoxes, ArchPier.North);
        // The manager's desk by the door, facing it
        f.Put(doorU, r.V0 + 3, Props.Desk, ArchPier.North);
        f.Put(doorU, r.V0 + 4, Props.OfficeChair, ArchPier.North);
        f.Put(r.U1, r.V0 + 3, Props.FilingCabinet, ArchPier.West);
        f.Lights(r, 4, CeilingKind.LightOn, 0.15, ref rng);
    }

    // ================= The church =================

    /// <summary>
    /// A church laid out on the middle of its door: the red aisle from the door to the altar, pews either side as far
    /// out as there is room on both, the altar with its candles and the two statues, the lights in rows that mirror
    /// about the aisle, and its stained glass (marked in <see cref="Tile.Stack"/> for <see cref="CityStainedGlass"/>):
    /// in the front and back walls every third block out from the middle, and over the door; in a side wall on the
    /// avenue every third block out from its middle.
    /// </summary>
    private void ChurchV9(Fit f, ref Rng rng)
    {
        int W = f.W, D = f.D, c = f.C, e = Math.Min(c - 1, W - 2 - c);
        f.KeepClearOfWays();
        for (int v = 1; v < D - 1; v++)
            for (int u = c - 1; u <= c + 1; u++)
                if (f.Inside(u, v)) f.At(u, v).Floor = FloorKind.SanctumCarpet;
        for (int v = 3; v < D - 5; v += 2)
            for (int k = 2; k <= e; k++)
            {
                f.Put(c - k, v, Props.Pew, ArchPier.North);
                f.Put(c + k, v, Props.Pew, ArchPier.North);
            }
        int altar = D - 3;
        f.Put(c, altar, Props.ConsoleTable, ArchPier.North);
        f.Put(c - 2, altar, Props.Candelabra, ArchPier.North);
        f.Put(c + 2, altar, Props.Candelabra, ArchPier.North);
        f.Put(c - e, altar, Props.AngelStatue, ArchPier.East);
        f.Put(c + e, altar, Props.AngelStatue, ArchPier.West);
        f.Lights(new Room(c - e, c + e, 1, D - 2), 4, CeilingKind.LightLit, 0, ref rng);
        // The lights outside the mirrored part are plain ceiling (Lights only touches the room it is given)
        // The stained glass, on the middle of the door
        foreach (int v in new[] { 0, D - 1 })
        {
            Mark(c, v);
            for (int k = 3; k <= e; k += 3) { Mark(c - k, v); Mark(c + k, v); }
        }
        int vc = (D - 1) / 2;
        foreach (int u in new[] { 0, W - 1 })
        {
            Mark(u, vc);
            for (int k = 3; vc - k >= 1; k += 3) { Mark(u, vc - k); Mark(u, vc + k); }
        }

        void Mark(int u, int v)
        {
            ref Tile t = ref f.At(u, v);
            if (t.Kind is TileKind.Wall or TileKind.Doorway && (t.Detail & (CityDetail.Corner | CityDetail.Party)) == 0) t.Stack = 1;
        }
    }

    /// <summary>
    /// Whether a block of a church's outside wall is stained glass. Up to layout version 8 every third block along the
    /// street (by world position, so the windows fell unevenly about the door); from version 9 where the plan marked
    /// it (<see cref="ChurchV9"/>, Tile.Stack 1), symmetric about the door. Rel 2 to 7 of a wall, 4 to 7 over the door.
    /// </summary>
    public bool CityStainedGlass(in Tile t, int gx, int gz, int rel, ArchPier facing)
    {
        if (Version >= 9) return t.Stack == 1 && rel >= (t.Kind == TileKind.Doorway ? 4 : 2) && rel <= 7;
        int at = facing is ArchPier.North or ArchPier.South ? gx : gz;
        return rel >= 2 && rel <= 7 && Hashing.Mod(at, 3) == 1;
    }

    // ================= The subway's stairs and platforms =================

    /// <summary>
    /// The height (above the street's floor block, rel) of the step block on a station stair tile: from layout version 9
    /// six steps, the first in the sidewalk itself (rel 0, its tread level with the street) down to rel -5, a half step
    /// over the platform (rel -6 is its floor); in 1-8 five, rel -1 to -5, so the top tread was a block under the
    /// sidewalk and you had to jump out.
    /// </summary>
    public int CityStationStepRel(in Tile t) => Version >= 9 ? 1 - t.Stair : -t.Stair;

    /// <summary>
    /// What stands on a station platform at a tile (<paramref name="ax"/> across the avenue, <paramref name="uz"/> along
    /// it from the city's origin): benches facing the tracks, an Almond Water machine, a bin, or nothing. From layout
    /// version 9 no machine stands at the foot of a flight of stairs, where it took half the way off them.
    /// </summary>
    public byte CityPlatformProp(int ax, int uz)
    {
        int k = Hashing.Mod(uz, 9);
        if ((ax == 2 || ax == 14) && k == 0) return Props.Bench;
        if ((ax == 1 || ax == 15) && Hashing.Mod(uz, 17) == 8)
        {
            int sl = Hashing.Mod(uz + StationReach, StreetPitch * StationEvery);
            bool foot = sl is >= 6 and <= 9 || sl >= StationLength - 10 && sl <= StationLength - 7;
            return Version >= 9 && foot ? (byte)0 : Props.Vending;
        }
        if ((ax == 3 || ax == 13) && k == 4) return Props.TrashCan;
        return 0;
    }
}
