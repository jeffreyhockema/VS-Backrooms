using System.Reflection;
using System.Text;
using Backrooms.Worldgen;

/// <summary>
/// l11rooms [blocks] [per-kind]: Level 11's ground floors in plan. Finds every enterable building in a square of
/// city blocks round the city's centre (its inside: tiles of a building in from its outside wall), and writes
/// <c>l11rooms.txt</c>: per kind of building a few of them in plan, turned so the street front is at the top, each
/// tile as a two-letter code and the way its front faces (^ toward the street, v to the back, &lt; and &gt; across),
/// then the ceiling (lights) and the floor finishes. Prints, per kind, what the ground floors hold: props per hundred
/// tiles of floor, props standing against the plate glass of the front, props in front of a doorway or door, chairs
/// and benches facing a wall a block in front of them, how far the farthest floor tile is from a light, and how many
/// different floor finishes a room has.
/// </summary>
static class L11Rooms
{
    static readonly Dictionary<int, string> PropNames = typeof(Props).GetFields(BindingFlags.Public | BindingFlags.Static)
        .Where(f => f.IsLiteral && f.FieldType == typeof(byte)).GroupBy(f => (int)(byte)f.GetRawConstantValue()).ToDictionary(g => g.Key, g => g.First().Name);
    static readonly Dictionary<int, string> DecorNames = typeof(Decor).GetFields(BindingFlags.Public | BindingFlags.Static)
        .Where(f => f.IsLiteral && f.FieldType == typeof(byte) && f.Name is not ("First" or "Limit")).GroupBy(f => (int)(byte)f.GetRawConstantValue()).ToDictionary(g => g.Key, g => g.First().Name);

    public record Lot(CityKind Kind, int X0, int X1, int Z0, int Z1, bool North);

    public static void Run(WorldLayout layout, int blocks, int perKind)
    {
        var tiles = new Dictionary<(int, int), Tile>();
        Tile At(int x, int z) { if (!tiles.TryGetValue((x, z), out var t)) tiles[(x, z)] = t = layout.TileAt(x, z); return t; }
        var lots = FindLots(layout, blocks, At);
        Report(layout, lots, perKind, At);
    }

    /// <summary>Every enterable building's lot in a square of blocks round the city's centre, its front the side its way in is on.</summary>
    public static List<Lot> FindLots(WorldLayout layout, int blocks, Func<int, int, Tile> At)
    {
        int ox = layout.CityOriginX, oz = layout.CityOriginZ;
        var lots = new List<Lot>();
        var seen = new HashSet<(int, int)>();
        for (int bj = -blocks; bj <= blocks; bj++)
            for (int bi = -blocks; bi <= blocks; bi++)
            {
                int bx = ox + bi * WorldLayout.AvePitch + WorldLayout.AveWidth, bz = oz + bj * WorldLayout.StreetPitch + WorldLayout.StreetWidth;
                for (int z = bz; z < bz + WorldLayout.StreetPitch - WorldLayout.StreetWidth; z++)
                    for (int x = bx; x < bx + WorldLayout.AvePitch - WorldLayout.AveWidth; x++)
                    {
                        Tile t = At(x, z);
                        if (seen.Contains((x, z)) || t.Level != 11 || t.Depth == 0 || t.Pipe == 0 || t.Sealed || !WorldLayout.CityEnterable((CityKind)t.Zone)) continue;
                        // The inside of one building: joined tiles in from its walls (a garage's columns, the partitions, included)
                        int x0 = x, x1 = x, z0 = z, z1 = z;
                        var q = new Queue<(int, int)>(); q.Enqueue((x, z)); seen.Add((x, z));
                        while (q.Count > 0)
                        {
                            var (cx, cz) = q.Dequeue();
                            x0 = Math.Min(x0, cx); x1 = Math.Max(x1, cx); z0 = Math.Min(z0, cz); z1 = Math.Max(z1, cz);
                            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                            {
                                int nx = cx + dx, nz = cz + dz;
                                if (seen.Contains((nx, nz))) continue;
                                Tile n = At(nx, nz);
                                if (n.Depth == 0 || n.Pipe == 0 || n.Zone != t.Zone) continue;
                                seen.Add((nx, nz)); q.Enqueue((nx, nz));
                            }
                        }
                        x0--; x1++; z0--; z1++;
                        // The front is the side with the way in on it
                        int north = 0, south = 0;
                        for (int u = x0; u <= x1; u++)
                        {
                            if (At(u, z0).Kind is TileKind.Doorway or TileKind.Door) north++;
                            if (At(u, z1).Kind is TileKind.Doorway or TileKind.Door) south++;
                        }
                        bool front = north > 0 || south == 0 ? (north >= south) : false;
                        if (north == 0 && south == 0) front = layout.CityLotFront(x0, z0) == ArchPier.North;
                        lots.Add(new Lot((CityKind)t.Zone, x0, x1, z0, z1, front));
                    }
            }
        return lots;
    }

    static void Report(WorldLayout layout, List<Lot> lots, int perKind, Func<int, int, Tile> At)
    {

        var codes = new Dictionary<string, string>();
        string Code(string name)
        {
            if (codes.TryGetValue(name, out var c)) return c;
            string up = new string(name.Where(char.IsUpper).ToArray());
            var tries = new List<string>();
            if (up.Length >= 2) tries.Add(up.Substring(0, 2));
            tries.Add(name.Substring(0, Math.Min(2, name.Length)));
            for (int i = 1; i < name.Length; i++) tries.Add($"{name[0]}{char.ToLower(name[i])}");
            foreach (var t in tries) if (!codes.ContainsValue(t)) { codes[name] = t; return t; }
            codes[name] = "??"; return "??";
        }

        static (int X, int Z) W(Lot l, int u, int v) => l.North ? (l.X0 + u, l.Z0 + v) : (l.X1 - u, l.Z1 - v);
        static char Arrow(Lot l, ArchPier p)
        {
            if (!l.North) p = p switch { ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East };
            return p switch { ArchPier.North => '^', ArchPier.South => 'v', ArchPier.West => '<', _ => '>' };
        }
        static (int, int) Ahead(Lot l, ArchPier p) => p switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.West => (-1, 0), _ => (1, 0) };

        var sb = new StringBuilder();
        var stats = new SortedDictionary<string, double[]>();
        // per kind: lots, floor tiles, props, props against the glass, props blocking a way in, seats facing a wall, worst light distance (sum), worst (max), floors per lot (sum)
        foreach (var group in lots.GroupBy(l => l.Kind).OrderBy(g => g.Key.ToString()))
        {
            var s = stats[group.Key.ToString()] = new double[10];
            // Show the narrowest, the widest and ones between (each kind's plans in order of width)
            var ordered = group.OrderBy(l => (l.X1 - l.X0) * 100000L + l.Z0 * 7 + l.X0).ToList();
            var show = new HashSet<Lot>();
            for (int i = 0; i < perKind && ordered.Count > 0; i++) show.Add(ordered[perKind == 1 ? 0 : (int)Math.Round(i * (ordered.Count - 1) / (double)(perKind - 1))]);
            foreach (var l in ordered)
            {
                int W_ = l.X1 - l.X0 + 1, D = l.Z1 - l.Z0 + 1;
                s[0]++;
                var floors = new HashSet<FloorKind>();
                var lights = new List<(int, int)>();
                var floorTiles = new List<(int, int)>();
                for (int v = 1; v < D - 1; v++)
                    for (int u = 1; u < W_ - 1; u++)
                    {
                        var (x, z) = W(l, u, v); Tile t = At(x, z);
                        if (t.Ceiling is CeilingKind.LightOn or CeilingKind.LightLit or CeilingKind.LightFlicker or CeilingKind.LightWarm or CeilingKind.Chandelier) lights.Add((u, v));
                        if (t.Kind != TileKind.Floor) continue;
                        // only the rooms you can get into: tiles reachable from the front without crossing walls are counted below
                        floorTiles.Add((u, v));
                    }
                // What you can walk to from the way in
                var reach = new HashSet<(int, int)>();
                var rq = new Queue<(int, int)>();
                for (int u = 1; u < W_ - 1; u++) { var (x, z) = W(l, u, 0); if (At(x, z).Kind == TileKind.Doorway) { reach.Add((u, 1)); rq.Enqueue((u, 1)); } }
                while (rq.Count > 0)
                {
                    var (u, v) = rq.Dequeue();
                    foreach (var (du, dv) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        int nu = u + du, nv = v + dv;
                        if (nu < 1 || nv < 1 || nu > W_ - 2 || nv > D - 2 || reach.Contains((nu, nv))) continue;
                        var (x, z) = W(l, nu, nv); Tile n = At(x, z);
                        if (n.Kind is TileKind.Wall or TileKind.Bars or TileKind.Door) continue;
                        reach.Add((nu, nv)); rq.Enqueue((nu, nv));
                    }
                }
                // Floor fenced off by furniture: open floor in the rooms that cannot be walked to from the way in
                var walk = new HashSet<(int, int)>();
                var wq = new Queue<(int, int)>();
                bool Open(Tile t) => t.Kind == TileKind.Doorway || t.Kind == TileKind.Floor && (t.Variant == 0 || t.Variant is Props.Crop or Props.TallGrass);
                foreach (var st in reach) if (st.Item2 == 1) { var (x, z) = W(l, st.Item1, 1); if (Open(At(x, z))) { walk.Add(st); wq.Enqueue(st); } }
                while (wq.Count > 0)
                {
                    var (u, v) = wq.Dequeue();
                    foreach (var (du, dv) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        var n = (u + du, v + dv);
                        if (!reach.Contains(n) || walk.Contains(n)) continue;
                        var (x, z) = W(l, n.Item1, n.Item2);
                        Tile nt = At(x, z);
                        if (!Open(nt) && !(nt.Kind == TileKind.Floor && nt.Stair > 0 && nt.Variant == 0)) continue;
                        walk.Add(n); wq.Enqueue(n);
                    }
                }
                int fenced = reach.Count(p => { var (x, z) = W(l, p.Item1, p.Item2); Tile t = At(x, z); return t.Kind == TileKind.Floor && t.Variant == 0 && t.Stair == 0 && !walk.Contains(p); });
                int props = 0, glass = 0, block = 0, seatWall = 0, worst = 0;
                foreach (var (u, v) in reach)
                {
                    var (x, z) = W(l, u, v); Tile t = At(x, z);
                    floors.Add(t.Floor);
                    int best = 999;
                    foreach (var (lu, lv) in lights) best = Math.Min(best, Math.Max(Math.Abs(lu - u), Math.Abs(lv - v)));
                    worst = Math.Max(worst, best);
                    if (t.Variant == 0 || t.Kind != TileKind.Floor) continue;
                    if (t.Variant is Props.CarPart) continue;
                    props++;
                    // against the plate glass of the front
                    if (v == 1) { var (fx, fz) = W(l, u, 0); if ((At(fx, fz).Detail & CityDetail.Storefront) != 0) glass++; }
                    // in front of a way in (the front doorways, a side doorway, an inside door)
                    foreach (var (du, dv) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        int nu = u + du, nv = v + dv;
                        var (nx, nz) = W(l, nu, nv); Tile n = At(nx, nz);
                        bool outerDoorway = (nu == 0 || nv == 0 || nu == W_ - 1 || nv == D - 1) && n.Kind == TileKind.Doorway;
                        bool innerDoor = n.Kind == TileKind.Door && n.Pattern != WallPattern.Elevator || n.Kind == TileKind.Doorway && nu > 0 && nv > 0 && nu < W_ - 1 && nv < D - 1;
                        bool lift = n.Kind == TileKind.Door && n.Pattern == WallPattern.Elevator;
                        if (outerDoorway || innerDoor || lift) { block++; break; }
                    }
                    // a seat looking straight at a wall a block away
                    if (t.Variant is Props.Bench or Props.CafeChair or Props.HotelChair or Props.Sofa or Props.WingChair or Props.FoldingChair or Props.OfficeChair or Props.Pew)
                    {
                        var (ax, az) = Ahead(l, t.Pier);
                        Tile n = At(x + ax, z + az);
                        if (n.Kind == TileKind.Wall && (n.Detail & CityDetail.Storefront) == 0) seatWall++;
                    }
                }
                s[1] += reach.Count; s[2] += props; s[3] += glass; s[4] += block; s[5] += seatWall; s[6] += worst; s[7] = Math.Max(s[7], worst); s[8] += floors.Count; s[9] += fenced;

                if (!show.Contains(l)) continue;
                sb.AppendLine($"=== {l.Kind} at {l.X0},{l.Z0} .. {l.X1},{l.Z1}  {W_} wide, {D} deep, front {(l.North ? "north" : "south")}; " +
                              $"{props} props on {reach.Count} tiles you can reach, {fenced} fenced off by furniture, farthest from a light {worst}, floors {string.Join("/", floors)}");
                var plan = new StringBuilder(); var ceil = new StringBuilder(); var flo = new StringBuilder();
                for (int v = 0; v < D; v++)
                {
                    for (int u = 0; u < W_; u++)
                    {
                        var (x, z) = W(l, u, v); Tile t = At(x, z);
                        bool edge = u == 0 || v == 0 || u == W_ - 1 || v == D - 1;
                        string cell;
                        switch (t.Kind)
                        {
                            case TileKind.Wall:
                                if (t.Variant >= Decor.First && DecorNames.TryGetValue(t.Variant, out var dn)) cell = Code("d" + dn).ToLower() + Arrow(l, t.Pier);
                                else if ((t.Detail & CityDetail.Storefront) != 0 && edge) cell = "===";
                                else if (t.Under == Unders.CinemaScreen) cell = "[S]";
                                else cell = edge ? "###" : "%%%";
                                break;
                            case TileKind.Doorway: cell = " : "; break;
                            case TileKind.Door: cell = t.Pattern == WallPattern.Elevator ? "EL" + Arrow(l, t.Pier) : "DR" + Arrow(l, t.Pier); break;
                            case TileKind.Bars: cell = "|||"; break;
                            default:
                                if (t.Stair > 0) cell = "s" + t.Stair + Arrow(l, t.Pier);
                                else if (t.Variant != 0 && PropNames.TryGetValue(t.Variant, out var pn)) cell = Code(pn) + Arrow(l, t.Pier);
                                else if (t.Under == Unders.CinemaScreen) cell = " S ";
                                else cell = reach.Contains((u, v)) || edge ? " . " : " ~ ";
                                break;
                        }
                        plan.Append(cell);
                        ceil.Append(edge || t.Kind == TileKind.Wall ? '#' : t.Ceiling switch
                        {
                            CeilingKind.LightOn or CeilingKind.LightLit or CeilingKind.LightWarm => 'o',
                            CeilingKind.LightFlicker => 'f', CeilingKind.LightOff => 'x', CeilingKind.Chandelier => 'C', _ => '.',
                        });
                        flo.Append(edge || t.Kind == TileKind.Wall ? '#' : FloorChar(t.Floor));
                    }
                    plan.AppendLine(); ceil.AppendLine(); flo.AppendLine();
                }
                sb.Append(plan);
                var c1 = ceil.ToString().Split('\n'); var f1 = flo.ToString().Split('\n');
                sb.AppendLine("ceiling".PadRight(W_ + 4) + "floor");
                for (int i = 0; i < c1.Length; i++) sb.AppendLine(c1[i].TrimEnd('\r').PadRight(W_ + 4) + f1[i].TrimEnd('\r'));
            }
        }
        sb.AppendLine("legend: ### outside wall, === plate glass, %%% inside wall, ' : ' doorway, DR door, EL elevator, sN stair step N, ||| railing, ' ~ ' floor you cannot reach");
        sb.AppendLine("        props and (lower case) wall decorations: " + string.Join(", ", codes.OrderBy(p => p.Value).Select(p => $"{p.Value}={p.Key}")));
        sb.AppendLine("        floors: " + string.Join(", ", floorChars.Select(p => $"{p.Value}={p.Key}")));
        File.WriteAllText("l11rooms.txt", sb.ToString());
        Console.WriteLine($"{lots.Count} enterable ground floors (plans in l11rooms.txt)");
        Console.WriteLine($"{"kind",-11} {"lots",5} {"props/100",9} {"by glass",8} {"at doors",8} {"seat>wall",9} {"light far",9} {"max",4} {"floors",6} {"fenced",6}");
        double[] all = new double[10];
        foreach (var (k, s) in stats)
        {
            Console.WriteLine($"{k,-11} {s[0],5} {100 * s[2] / Math.Max(1, s[1]),9:0.0} {s[3],8} {s[4],8} {s[5],9} {s[6] / Math.Max(1, s[0]),9:0.0} {s[7],4} {s[8] / Math.Max(1, s[0]),6:0.0} {s[9],6}");
            for (int i = 0; i < 10; i++) all[i] = i == 7 ? Math.Max(all[i], s[i]) : all[i] + s[i];
        }
        Console.WriteLine($"{"all",-11} {all[0],5} {100 * all[2] / Math.Max(1, all[1]),9:0.0} {all[3],8} {all[4],8} {all[5],9} {all[6] / Math.Max(1, all[0]),9:0.0} {all[7],4} {all[8] / Math.Max(1, all[0]),6:0.0} {all[9],6}");
    }

    static readonly Dictionary<FloorKind, char> floorChars = new();
    static char FloorChar(FloorKind f)
    {
        if (floorChars.TryGetValue(f, out char c)) return c;
        const string pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
        c = pool[floorChars.Count % pool.Length];
        floorChars[f] = c;
        return c;
    }
}
