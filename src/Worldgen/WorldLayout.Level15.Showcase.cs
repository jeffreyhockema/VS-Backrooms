using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>), found from the layout round the
    /// region's middle: a main hall's long view and a crossing with its signs, a side corridor, a service passage, a machine
    /// room from its gate and from inside, a control room, a lecture hall, a laboratory, an abandoned camp with its dead, a
    /// crematorium, a dark square (and a Robo-Man in it, put down by <c>/backrooms l15 roboman x z</c>), and the star door
    /// (the nearest wing that holds it, far out). Every spot is a free standing place with the way to look.
    /// </summary>
    public IEnumerable<Showcase.Spot> L15ShowcaseSpots(WorldGeometry geometry)
    {
        double y = geometry.FloorFor(Level15) + 1;
        var spots = new List<Showcase.Spot>();
        int cx = L15CentreX * MacroSize + 16, cz = L15CentreZ * MacroSize + 16;
        int hcx = Hashing.FloorDiv(cx, L15Period), hcz = Hashing.FloorDiv(cz, L15Period);
        void Add(string name, int x, int z, double heading, double pitch = 0, string setup = null) =>
            spots.Add(new Showcase.Spot(name, x + 0.5, y, z + 0.5, heading, pitch, setup));

        // A main hall, down its length to the next crossing; a crossing, its square of lights and the halls' signs
        int hallX = hcx * L15Period + 3, hallZ = hcz * L15Period + 3;
        Add("hall", hallX, hcz * L15Period + 118, 0, 2);
        Add("crossing", hcx * L15Period + 20, hallZ - 1, 270, 4);

        if (L15FindAlong(hcx, hcz, L15Zone.Corridor, 3) is { } corridor) Add("corridor", corridor.X, corridor.Z, corridor.Heading, 0);
        if (L15FindAlong(hcx, hcz, L15Zone.Service, 2) is { } service) Add("service", service.X, service.Z, service.Heading, 0);

        // A machine room from the corridor in front of its gate (the shutter, the scanner, the code, the glass), then inside
        if (L15FindDoor(hcx, hcz, L15Zone.Machine, glass: true, machines: 24) is { } machine)
        {
            Add("machine-gate", machine.OutX, machine.OutZ, machine.Heading, 6);
            Add("machine-room", machine.InX, machine.InZ, machine.Heading, 10);
        }
        if (L15FindDoor(hcx, hcz, L15Zone.Control) is { } control) Add("control-room", control.InX, control.InZ, control.Heading, 0);
        if (L15FindDoor(hcx, hcz, L15Zone.Lecture) is { } lecture) Add("lecture-hall", lecture.InX, lecture.InZ, lecture.Heading, 4);
        if (L15FindDoor(hcx, hcz, L15Zone.Lab) is { } lab) Add("lab", lab.InX, lab.InZ, lab.Heading, -6);
        if (L15FindCamp(hcx, hcz) is { } camp) Add("camp", camp.X, camp.Z, camp.Heading, -28);
        if (L15FindDoor(hcx, hcz, L15Zone.Crematorium, rings: 8) is { } crem) Add("crematorium", crem.InX, crem.InZ, crem.Heading, -10);

        // Round 3's set pieces: the hall's floor line and its hanging sign before a crossing; a robot dock; a lift; a lab's glass
        // wall and its plates from the corridor; a dormitory's bunks; a canteen's serving line and menu; a medical bay; a
        // hydroponics bay from its glass wall and from inside
        Add("hall-sign", hallX + 1, hcz * L15Period + 19, 0, 8);
        if (L15FindLectureTop(hcx, hcz) is { } top)
            spots.Add(new Showcase.Spot("lecture-stage", top.X + 0.5, y + top.Rise, top.Z + 0.5, top.Heading, -14, null));
        if (L15FindDock(hcx, hcz) is { } dock) Add("dock", dock.X, dock.Z, dock.Heading, -4);
        if (L15FindLift(hcx, hcz) is { } lift) Add("lift", lift.X, lift.Z, lift.Heading, 4);
        if (L15FindLift(hcx, hcz, L15WallMap) is { } map) Add("sector-map", map.X, map.Z, map.Heading, 6);
        if (L15FindDoor(hcx, hcz, L15Zone.Lab, glass: true) is { } labGlass) Add("lab-glass", labGlass.OutX, labGlass.OutZ, labGlass.Heading, 0);
        if (L15FindDoor(hcx, hcz, L15Zone.Dorm) is { } dorm) Add("dorm", dorm.InX, dorm.InZ, dorm.Heading, -8);
        if (L15FindDoor(hcx, hcz, L15Zone.Canteen) is { } canteen) Add("canteen", canteen.InX, canteen.InZ, canteen.Heading, 4);
        if (L15FindServe(hcx, hcz) is { } serve) Add("serving-line", serve.X, serve.Z, serve.Heading, 8);
        if (L15FindDoor(hcx, hcz, L15Zone.Medical) is { } medical) Add("medical-bay", medical.InX, medical.InZ, medical.Heading, -8);
        if (L15FindDoor(hcx, hcz, L15Zone.Hydro, glass: true) is { } hydro)
        {
            Add("hydro-glass", hydro.OutX, hydro.OutZ, hydro.Heading, 0);
            Add("hydroponics", hydro.InX, hydro.InZ, hydro.Heading, 0);
        }

        // The dark: a main hall where the power is out, looking up it from near its end; a Robo-Man in it
        if (L15FindDarkHall(cx, cz) is { } dark)
        {
            Add("dark-hall", dark.X, dark.Z, 0, 0);
            Add("roboman", dark.X, dark.Z - 10, 0, 0, $"/backrooms l15 roboman {dark.X} {dark.Z - 18}");
            // Round 4: the edge of the dark from the lit side: the battery lamps still burning amber, the tripped breaker
            Add("dark-edge", dark.X, dark.Z + 12, 0, 2);
        }
        // Round 4: a bulkhead across the main hall (its jambs, code plate, knee braces, the header's light bar, the tread plate)
        Add("bulkhead", hcx * L15Period + 2, hcz * L15Period + 23, 22, 10);
        if (L15FindStarDoor() is { } star) Add("star-door", star.X, star.Z, star.Heading, 6);
        // The links: the ways in, in Levels 10 and 3, the door that does not open, and the ways out (WorldLayout.Level15.Links.cs)
        spots.AddRange(L15LinkSpots(geometry));
        return spots;
    }

    /// <summary>
    /// The top of the nearest lit lecture hall's middle aisle: the highest step with another step in front of it, how high it
    /// stands (blocks) and the way down to the stage.
    /// </summary>
    private (int X, int Z, double Rise, double Heading)? L15FindLectureTop(int hcx, int hcz)
    {
        foreach (var (hx, hz) in L15WingsRound(hcx, hcz, 4))
        {
            L15Plan plan = L15PlanOf(hx, hz);
            (int A, int B, int Step)? best = null;
            for (int b = 0; b < L15WingSize; b++)
                for (int a = 0; a < L15WingSize; a++)
                {
                    Tile t = plan.AtAB(a, b);
                    if (t.Variant != Props.L15Riser || L15ZoneOf(t) != L15Zone.Lecture || L15IsDark(t)) continue;
                    var (dx, dz) = L15StepOf(t.Pier);
                    var (sx, sz) = (dz, -dx); // either side across the aisle: steps too (the middle aisle, not a side one)
                    if (!L15Plan.In(a + sx, b + sz) || !L15Plan.In(a - sx, b - sz)) continue;
                    if (plan.AtAB(a + sx, b + sz).Variant != Props.L15Riser || plan.AtAB(a - sx, b - sz).Variant != Props.L15Riser) continue;
                    if (best is not { } bb || t.Stack > bb.Step) best = (a, b, t.Stack);
                }
            if (best is { } top)
            {
                Tile t = plan.AtAB(top.A, top.B);
                var (dx, dz) = L15StepOf(t.Pier);
                var (x, z) = plan.World(top.A, top.B);
                return (x, z, top.Step * 0.5, L15Heading(dx, dz));
            }
        }
        return null;
    }

    /// <summary>The nearest lit canteen's serving line: a free place a few blocks out on the customers' side of its middle, looking at it.</summary>
    private (int X, int Z, double Heading)? L15FindServe(int hcx, int hcz)
    {
        foreach (var (hx, hz) in L15WingsRound(hcx, hcz, 4))
        {
            L15Plan plan = L15PlanOf(hx, hz);
            for (int b = 0; b < L15WingSize; b++)
                for (int a = 0; a < L15WingSize; a++)
                {
                    Tile t = plan.AtAB(a, b);
                    if (t.Variant != Props.L15Serve || t.Stack != 0 || L15IsDark(t)) continue;
                    var (dx, dz) = L15StepOf(t.Pier);
                    var (x, z) = plan.World(a, b);
                    for (int k = 2; k <= 4; k++)
                        if (L15Standable(x + dx * k, z + dz * k) && L15Standable(x + dx * (k - 1), z + dz * (k - 1)))
                            return (x + dx * k, z + dz * k, L15Heading(-dx, -dz));
                }
        }
        return null;
    }

    /// <summary>The nearest lit robot dock on the main halls round the middle: a place across the hall from it, a little along, looking at it.</summary>
    private (int X, int Z, double Heading)? L15FindDock(int hcx, int hcz)
    {
        for (int ring = 0; ring <= 3; ring++)
            for (int line = -ring; line <= ring; line++)
                foreach (bool alongZ in new[] { true, false })
                    for (int along = (alongZ ? hcz : hcx) * L15Period - ring * L15Period; along < (alongZ ? hcz : hcx) * L15Period + (ring + 1) * L15Period; along++)
                    {
                        int l0 = ((alongZ ? hcx : hcz) + line) * L15Period;
                        foreach (int across in new[] { 1, L15HallWidth })
                        {
                            int x = alongZ ? l0 + across : along, z = alongZ ? along : l0 + across;
                            if (!L15HallDockAt(x, z, alongZ, across) || L15DarkQuad(x, z) || TileAt(x, z).Level != Level15) continue;
                            int other = across == 1 ? 4 : 2;
                            int sx = alongZ ? l0 + other : along + 3, sz = alongZ ? along + 3 : l0 + other;
                            return (sx, sz, L15Heading(x - sx, z - sz));
                        }
                    }
        return null;
    }

    /// <summary>The nearest lift (or other dress: a sector map) on a wing's wall onto a main hall: a place in the hall in front of it, looking at it.</summary>
    private (int X, int Z, double Heading)? L15FindLift(int hcx, int hcz, byte detail = L15WallLiftL)
    {
        foreach (var (hx, hz) in L15WingsRound(hcx, hcz, 3))
        {
            L15Plan plan = L15PlanOf(hx, hz);
            for (int k = 0; k < L15WingSize; k++)
                foreach (var (a, b) in new[] { (-1, k), (L15WingSize, k), (k, -1), (k, L15WingSize) })
                {
                    Tile t = plan.AtAB(a, b);
                    if (t.Kind != TileKind.Wall || t.Detail != detail || detail == L15WallMap && t.Stack != 0) continue;
                    var (x, z) = plan.World(a, b);
                    var (dx, dz) = L15StepOf(t.Pier);
                    if (L15DarkQuad(x, z) || TileAt(x, z).Level != Level15) continue;
                    // Four blocks out into the hall, half a door to the right, looking back at the wall
                    int sx = x + dx * 4, sz = z + dz * 4;
                    return (sx, sz, L15Heading(-dx, -dz));
                }
        }
        return null;
    }

    /// <summary>A compass heading (0 north, 90 east) for a way along x and z.</summary>
    private static double L15Heading(double dx, double dz) => (Math.Atan2(dx, -dz) * 180 / Math.PI + 360) % 360;

    private static (int Dx, int Dz) L15StepOf(ArchPier p) => p switch
    {
        ArchPier.West => (-1, 0), ArchPier.East => (1, 0), ArchPier.North => (0, -1), _ => (0, 1),
    };

    /// <summary>Whether someone can stand at a block position of the level (open floor with nothing on it, or a doorway).</summary>
    private bool L15Standable(int x, int z)
    {
        Tile t = TileAt(x, z);
        if (t.Level != Level15) return false;
        return t.Kind == TileKind.Doorway || t.Kind == TileKind.Floor && t.Variant == 0 && !t.SupplyBox && t.Stack == 0;
    }

    /// <summary>The wings round (hcx, hcz), the nearest first, out to <paramref name="rings"/> wings away.</summary>
    private static IEnumerable<(int Hx, int Hz)> L15WingsRound(int hcx, int hcz, int rings)
    {
        for (int ring = 0; ring <= rings; ring++)
            for (int j = -ring; j <= ring; j++)
                for (int i = -ring; i <= ring; i++)
                    if (Math.Max(Math.Abs(i), Math.Abs(j)) == ring) yield return (hcx + i, hcz + j);
    }

    /// <summary>
    /// The nearest lit door into a room of a kind: where to stand outside it (two blocks back across the corridor), where
    /// to stand just inside, and the heading into the room. With <paramref name="glass"/>, only a door with thick glass beside it.
    /// </summary>
    private (int OutX, int OutZ, int InX, int InZ, double Heading)? L15FindDoor(int hcx, int hcz, L15Zone kind, bool glass = false, int rings = 4,
        int machines = 0)
    {
        foreach (var (hx, hz) in L15WingsRound(hcx, hcz, rings))
        {
            L15Plan plan = L15PlanOf(hx, hz);
            for (int b = 0; b < L15WingSize; b++)
                for (int a = 0; a < L15WingSize; a++)
                {
                    Tile d = plan.AtAB(a, b);
                    if (d.Kind != TileKind.Doorway || L15ZoneOf(d) != kind || L15IsDark(d)) continue;
                    var (ox, oz) = L15StepOf(d.Pier);
                    Tile inner = plan.AtAB(a - ox, b - oz);
                    if (inner.Kind != TileKind.Floor || L15ZoneOf(inner) != kind) continue;
                    var (x, z) = plan.World(a, b);
                    if (TileAt(x, z).Level != Level15) continue;
                    if (glass && !L15GlassBeside(x, z, ox, oz)) continue;
                    if (machines > 0 && !L15MachinesAhead(plan, a - ox, b - oz, -ox, -oz, machines)) continue;
                    // Out through the doorway to the corridor, then back across it
                    int sx = x, sz = z;
                    while (TileAt(sx, sz).Kind == TileKind.Doorway) { sx += ox; sz += oz; }
                    if (!L15Standable(sx, sz)) continue;
                    for (int k = 0; k < 2 && L15Standable(sx + ox, sz + oz); k++) { sx += ox; sz += oz; }
                    // In: two blocks past the doorway if free, else one
                    int ix = x - ox, iz = z - oz;
                    if (!L15Standable(ix, iz)) continue;
                    if (L15Standable(ix - ox, iz - oz)) { ix -= ox; iz -= oz; }
                    return (sx, sz, ix, iz, L15Heading(-ox, -oz));
                }
        }
        return null;
    }

    /// <summary>
    /// Whether a machine room seen from (a, b) looking along (dx, dz) has at least <paramref name="least"/> blocks of machine
    /// in the fourteen blocks ahead (seven either side), some of them running.
    /// </summary>
    private static bool L15MachinesAhead(L15Plan plan, int a, int b, int dx, int dz, int least)
    {
        int n = 0, running = 0;
        for (int k = 1; k <= 14; k++)
            for (int j = -7; j <= 7; j++)
            {
                int pa = a + dx * k + dz * j, pb = b + dz * k + dx * j;
                if (!L15Plan.In(pa, pb)) continue;
                Tile t = plan.AtAB(pa, pb);
                if (t.Variant != Props.L15Machine || L15ZoneOf(t) != L15Zone.Machine) continue;
                n++;
                if (t.Detail == L15MachineRunning) running++;
            }
        return n >= least && running >= 3;
    }

    /// <summary>Whether there is thick glass in the wall within five blocks either side of a door (at x, z, facing out along ox, oz).</summary>
    private bool L15GlassBeside(int x, int z, int ox, int oz)
    {
        for (int k = -5; k <= 5; k++)
        {
            Tile t = TileAt(x + k * Math.Abs(oz), z + k * Math.Abs(ox));
            if (t.Kind == TileKind.Wall && t.Detail is L15WallGlass or L15WallGlassCracked) return true;
        }
        return false;
    }

    /// <summary>The nearest lit place in a corridor (in its middle) or a service passage with a long way clear ahead, and that way.</summary>
    private (int X, int Z, double Heading)? L15FindAlong(int hcx, int hcz, L15Zone zone, int width)
    {
        foreach (var (hx, hz) in L15WingsRound(hcx, hcz, 3))
        {
            L15Plan plan = L15PlanOf(hx, hz);
            for (int b = 4; b < L15WingSize - 4; b += 3)
                for (int a = 4; a < L15WingSize - 4; a++)
                {
                    Tile t = plan.AtAB(a, b);
                    if (t.Kind != TileKind.Floor || L15ZoneOf(t) != zone || L15IsDark(t)) continue;
                    var (x, z) = plan.World(a, b);
                    bool alongZ = t.Pier == ArchPier.North;
                    int sx = alongZ ? 1 : 0, sz = alongZ ? 0 : 1;
                    if (!L15Standable(x, z)) continue;
                    if (width == 3 && !(L15Standable(x - sx, z - sz) && L15Standable(x + sx, z + sz))) continue;
                    foreach (int dir in new[] { -1, 1 })
                    {
                        int dx = alongZ ? 0 : dir, dz = alongZ ? dir : 0, run = 0;
                        while (run < 30)
                        {
                            Tile ahead = TileAt(x + dx * (run + 1), z + dz * (run + 1));
                            if (ahead.Kind != TileKind.Floor || L15ZoneOf(ahead) != zone) break;
                            run++;
                        }
                        if (run >= 22) return (x, z, L15Heading(dx, dz));
                    }
                }
        }
        return null;
    }

    /// <summary>The nearest lit camp with a body by it (failing that, any): a place to stand a few blocks off, and the way to look at it.</summary>
    private (int X, int Z, double Heading)? L15FindCamp(int hcx, int hcz)
    {
        (int X, int Z, double Heading)? fallback = null;
        foreach (var (hx, hz) in L15WingsRound(hcx, hcz, 6))
        {
            L15Plan plan = L15PlanOf(hx, hz);
            foreach (var (campX, campZ) in plan.CampSpots)
            {
                Tile here = TileAt(campX, campZ);
                if (here.Level != Level15 || L15IsDark(here)) continue;
                L15Zone zone = L15ZoneOf(here);
                // What the camp is: its tent or bedroll, its bags, chairs, boxes and barrel, and its dead
                double sx = 0, sz = 0;
                int n = 0;
                bool body = false, tent = false;
                for (int dz = -6; dz <= 6; dz++)
                    for (int dx = -6; dx <= 6; dx++)
                    {
                        Tile t = TileAt(campX + dx, campZ + dz);
                        if (t.Kind != TileKind.Floor || L15ZoneOf(t) != zone) continue;
                        bool dead = t.Variant == Props.L15Corpse;
                        bool part = dead || t.SupplyBox || t.Variant is Props.CampTent or Props.SleepingBag or Props.Backpack or Props.BurnBarrel
                            or Props.FoldingChair or Props.CardboardBoxes;
                        bool near = dead || Math.Abs(dx) <= 4 && Math.Abs(dz) <= 4;
                        if (!part || !near) continue;
                        body |= dead;
                        tent |= t.Variant == Props.CampTent;
                        sx += campX + dx;
                        sz += campZ + dz;
                        n++;
                    }
                if (n == 0) continue;
                double tx = sx / n, tz = sz / n;
                (int X, int Z, double Heading)? best = null;
                double bestD = 0;
                for (int dz = -7; dz <= 7; dz++)
                    for (int dx = -7; dx <= 7; dx++)
                    {
                        int x = (int)Math.Round(tx) + dx, z = (int)Math.Round(tz) + dz;
                        double d = Math.Sqrt((x - tx) * (x - tx) + (z - tz) * (z - tz));
                        if (d < 3.5 || d > 6.5 || d <= bestD || !L15Standable(x, z) || L15ZoneOf(TileAt(x, z)) != zone) continue;
                        bestD = d;
                        best = (x, z, L15Heading(tx - x, tz - z));
                    }
                if (best == null) continue;
                if (body && tent) return best;
                if (body) fallback ??= best;
            }
        }
        return fallback;
    }

    /// <summary>
    /// The nearest stretch of main hall (running north and south) in a square where the power is out: a place near its
    /// south end, so the hall goes on dark ahead to the north.
    /// </summary>
    private (int X, int Z)? L15FindDarkHall(int cx, int cz)
    {
        int qcx = Hashing.FloorDiv(cx, 64), qcz = Hashing.FloorDiv(cz, 64);
        for (int ring = 1; ring <= 40; ring++)
            for (int j = -ring; j <= ring; j++)
                for (int i = -ring; i <= ring; i++)
                {
                    if (Math.Max(Math.Abs(i), Math.Abs(j)) != ring) continue;
                    int qx = qcx + i, qz = qcz + j;
                    if (Hashing.Mod(qx, 2) != 0) continue; // only the squares a north-south hall runs through
                    // (The square runs from 32 blocks before its line to 31 after: stand 26 in from its south edge)
                    int x = qx * 64 + 3, z = qz * 64 + 26;
                    if (!L15DarkQuad(x, z) || !L15DarkQuad(x, z - 50) || TileAt(x, z).Level != Level15 || TileAt(x, z - 50).Level != Level15) continue;
                    if (!L15Standable(x, z) || !L15Standable(x, z - 10)) continue;
                    return (x, z);
                }
        return null;
    }

    /// <summary>The nearest star door: a place to stand in front of it, and the way to look at it.</summary>
    private (int X, int Z, double Heading)? L15FindStarDoor()
    {
        int r = L15Radius * MacroSize, cx = L15CentreX * MacroSize + 16, cz = L15CentreZ * MacroSize + 16;
        var wings = new List<(double D, int Hx, int Hz)>();
        for (int hz = Hashing.FloorDiv(cz - r, L15Period); hz <= Hashing.FloorDiv(cz + r, L15Period); hz++)
            for (int hx = Hashing.FloorDiv(cx - r, L15Period); hx <= Hashing.FloorDiv(cx + r, L15Period); hx++)
                if (L15StarWing(hx, hz))
                    wings.Add((Math.Sqrt(Math.Pow(hx * L15Period + 64 - cx, 2) + Math.Pow(hz * L15Period + 64 - cz, 2)), hx, hz));
        wings.Sort((p, q) => p.D.CompareTo(q.D));
        foreach (var (_, hx, hz) in wings)
        {
            L15Plan plan = L15PlanOf(hx, hz);
            if (!plan.Star) continue;
            for (int b = 0; b < L15WingSize; b++)
                for (int a = 0; a < L15WingSize; a++)
                {
                    Tile t = plan.AtAB(a, b);
                    if (t.Variant != Props.L15StarDoor) continue;
                    var (x, z) = plan.World(a, b);
                    if (TileAt(x, z).Level != Level15 || TileAt(x, z).Variant != Props.L15StarDoor) continue;
                    var (dx, dz) = L15StepOf(t.Pier);
                    for (int k = 5; k >= 3; k--)
                        if (L15Standable(x + dx * k, z + dz * k)) return (x + dx * k, z + dz * k, L15Heading(-dx, -dz));
                }
        }
        return null;
    }
}
