namespace Backrooms.Worldgen;

/// <summary>
/// Level 36 (cabin pass, 2026-11-13): the plane's cabin behind a gate, as a narrow-body's economy cabin. Its blocks are
/// WorldGenerator.L36.cs's (tools/gen_36_cabin.py).
///
/// <para>The cabin stays in the gate's bounds (p pa0-1..pa0+21: the flight's rules find a player's gate by them) and the bridge
/// meets it at p pa0+10, so the boarding door is the plane's front left door (L1): the nose is put toward plan west or east
/// so that every plane has the same hand (a plane boards on its left). From the nose: the forward bulkhead with the flight
/// deck's door (a = -4); three rows with the forward galley on the right, the lavatory and the crew's jump seat on the left
/// (a = -3..-1); the L1 / R1 doors (a = 0); eight rows of seats, two and two (a = 1..8, the fifth the overwing exits); the L2 /
/// R2 doors (a = 9); the aft galley between two lavatories (a = 10); the aft bulkhead (a = 11). Five wide (the left window
/// seats, the left aisle seats, the aisle, the right aisle seats, the right window seats), three high; in the top block over
/// the seats, the passenger service units (window side) and the bins (aisle side).</para>
/// </summary>
public static class L36Cab
{
    /// <summary>A cabin wall's kind (<see cref="Tile.Roof"/> on a <c>CabinWall</c> tile; 0 the old dressed wall).</summary>
    public const byte WallWindow = 1, WallPlain = 2, WallDoorFwd = 3, WallDoorAft = 4, WallDoorPort = 5, WallDoorStbd = 6, WallExit = 7,
        WallBulkhead = 8, WallBulkheadExt = 9, WallFlightDeck = 10, WallHidden = 11;

    /// <summary>A cabin floor's kind (<see cref="Tile.Roof"/> on a Cabin floor tile; <see cref="Tile.Pier"/> toward the nose).</summary>
    public const byte FloorTrack = 1, FloorAisle = 2, FloorVinyl = 3, FloorCarpet = 4;

    /// <summary>A fitting's kind (<see cref="Tile.Stack"/> under <see cref="Props.L36CabinFit"/>).</summary>
    public const byte FitGalleyOven = 0, FitGalleyCoffee = 1, FitGalleyCounter = 2, FitLavOccupied = 3, FitLavVacant = 4, FitLavBody = 5,
        FitJumpSeat = 6, FitCurtain = 7, FitPlaneDoor = 8;

    /// <summary>A seat's kind (<see cref="Tile.Stack"/> under <see cref="Props.L36CabinSeat"/>): 0 as it was left by nobody.</summary>
    public const byte SeatPlain = 0, SeatBlanket = 1, SeatPillow = 2, SeatBag = 3, SeatMagazine = 4, SeatExitRow = 5;

    /// <summary>The bins' open states (<see cref="Tile.Depth"/> bits 4-5 under <see cref="Overheads.L36CabinBin"/>).</summary>
    public const byte BinShut = 0, BinBag = 1, BinCoat = 2;
}

public sealed partial class WorldLayout
{
    /// <summary>(cabin pass) Lays out a gate's cabin (the bridge, laid out before, ends at its door: p pa0+10, q 71).</summary>
    private void L36LayCabin(L36Plan plan, int pa0, int side)
    {
        int Q(int q) => L36Q(side, q);
        // The nose toward plan east or west, so the boarding door is on the plane's left whichever way the plan lies
        bool east = (side == 1) ^ plan.Mirror ^ plan.Flip;
        int f = east ? 1 : -1, door = pa0 + 10;
        int P(int a) => door - f * a;
        ArchPier nose = east ? ArchPier.East : ArchPier.West, aft = east ? ArchPier.West : ArchPier.East;
        ArchPier leftward = side == 0 ? ArchPier.South : ArchPier.North, rightward = side == 0 ? ArchPier.North : ArchPier.South;
        int wl = Q(70), sl = Q(69), aisle = Q(68), sr = Q(67), wr = Q(66), leftWall = Q(71), rightWall = Q(65);
        int[] cols = { wl, sl, aisle, sr, wr };

        Tile Floor(byte kind)
        {
            Tile c = L36Air(L36Zone.Cabin, 3, L36Mat.CarpetBlue);
            c.Roof = kind;
            c.Pier = plan.Dir(nose);
            return c;
        }
        void Wall(int a, int q, byte kind, ArchPier facing)
        {
            ref Tile w = ref plan.At(P(a), q);
            w = L36Solid(L36Mat.CabinWall);
            w.Roof = kind;
            w.Pier = plan.Dir(facing);
        }
        void Fit(int a, int q, byte kind, ArchPier facing) => L36Put(plan, P(a), q, Props.L36CabinFit, facing, kind);
        double Roll(int a, int q, ulong salt)
        {
            var (x, z) = plan.World(P(a), q);
            return Hashing.Unit(Hashing.Hash(seed, x, z, SaltL36Prop + salt));
        }

        // The floor: carpet with the seats' tracks under the seats, the aisle's carpet with its floor-path lights, plain carpet in
        // the door rows, vinyl in the galleys
        for (int a = -3; a <= 10; a++)
            foreach (int q in cols)
            {
                bool seats = a is >= 1 and <= 8, galley = a < 0 || a == 10;
                plan.At(P(a), q) = Floor(galley ? L36Cab.FloorVinyl : q == aisle ? L36Cab.FloorAisle : seats ? L36Cab.FloorTrack : L36Cab.FloorCarpet);
            }
        // The seats, the service units and the bins over them (rows 10-18, no 13), the EXIT signs over the aisle at the doors and
        // the overwing exits
        for (int a = 1; a <= 8; a++)
            foreach (int q in new[] { wl, sl, sr, wr })
            {
                ref Tile t = ref plan.At(P(a), q);
                bool window = q == wl || q == wr, left = q == wl || q == sl;
                double r = Roll(a, q, 12);
                byte kind = r < 0.05 ? L36Cab.SeatBlanket : r < 0.09 ? L36Cab.SeatPillow : r < 0.14 ? L36Cab.SeatBag : r < 0.17 ? L36Cab.SeatMagazine
                    : a == 5 ? L36Cab.SeatExitRow : L36Cab.SeatPlain;
                t.Variant = Props.L36CabinSeat;
                t.Stack = kind;
                t.Overhead = window ? Overheads.L36Psu : Overheads.L36CabinBin;
                t.Pier = plan.Dir(nose);
                if (!window)
                {
                    double o = Roll(a, q, 13);
                    t.Depth = (byte)(a - 1 | (o < 0.07 ? L36Cab.BinBag : o < 0.12 ? L36Cab.BinCoat : L36Cab.BinShut) << 4);
                }
                // (bit 3: a right-hand seat; the overhead faces the aisle, to the seat's right on the left, its left on the right)
                t.Stack |= (byte)(left ? 0 : 8);
            }
        foreach (int a in new[] { 0, 5, 9 })
        {
            ref Tile t = ref plan.At(P(a), aisle);
            t.Overhead = Overheads.L36CabinSign;
        }
        // The nose: the forward galley on the right, the lavatory and the jump seat on the left, a curtain across the galley's end
        Fit(-3, wr, L36Cab.FitGalleyOven, leftward);
        Fit(-2, wr, L36Cab.FitGalleyCoffee, leftward);
        Fit(-1, wr, L36Cab.FitGalleyCounter, leftward);
        Fit(-3, wl, L36Cab.FitLavOccupied, rightward);
        Fit(-2, wl, L36Cab.FitLavBody, rightward);
        Fit(-1, wl, L36Cab.FitJumpSeat, aft);
        Fit(-1, sr, L36Cab.FitCurtain, aft);
        // The rear: the aft galley across the back, a lavatory either side
        Fit(10, sl, L36Cab.FitGalleyCoffee, nose);
        Fit(10, aisle, L36Cab.FitGalleyCounter, nose);
        Fit(10, sr, L36Cab.FitGalleyOven, nose);
        Fit(10, wl, L36Cab.FitLavVacant, nose);
        Fit(10, wr, Roll(10, wr, 14) < 0.5 ? L36Cab.FitLavOccupied : L36Cab.FitLavVacant, nose);
        // The walls: the boarding door (the bridge's last tile) between its surrounds, R1 opposite, the overwing exits, L2 / R2,
        // windows down the rows, the forward bulkhead with the flight deck's door, the aft bulkhead
        for (int a = -3; a <= 10; a++)
        {
            if (a != 0)
                Wall(a, leftWall, a == -1 ? L36Cab.WallDoorFwd : a == 1 ? L36Cab.WallDoorAft : a == 5 ? L36Cab.WallExit : a == 9 ? L36Cab.WallDoorPort
                    : a is -3 or -2 or 10 ? L36Cab.WallHidden : L36Cab.WallWindow, rightward);
            Wall(a, rightWall, a is 0 or 9 ? L36Cab.WallDoorStbd : a == 5 ? L36Cab.WallExit : a < 0 || a == 10 ? L36Cab.WallHidden : L36Cab.WallWindow, leftward);
        }
        L36Put(plan, door, leftWall, Props.L36CabinFit, rightward, L36Cab.FitPlaneDoor);
        foreach (int q in cols)
        {
            Wall(-4, q, q == aisle ? L36Cab.WallFlightDeck : q == sl ? L36Cab.WallBulkhead : q == sr ? L36Cab.WallBulkheadExt : L36Cab.WallHidden, aft);
            Wall(11, q, L36Cab.WallHidden, nose);
        }
    }
}
