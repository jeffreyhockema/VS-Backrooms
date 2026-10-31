using System;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 120, "Server Room" (experimental): kept as level 26 (<see cref="Level120"/>) and shown as "120". A dark, endless
/// server floor in a round noclip region far out to the north-east, beyond Level Fun (after Wikidot's "Broken Servos"; the
/// design is docs/design/experimental-levels/120-plan.md). No thresholds in or out: the cheats menu or
/// <c>/backrooms goto 120</c> only.
///
/// <para><b>The lattice.</b> Service corridors run straight through the whole region every <see cref="L120Period"/> blocks
/// each way, four wide (x or z mod 96 in 1-4), dirty yellow walls, a duct along one side and mostly dead lights; every
/// other crossing keeps one working tube. Between four corridors lies a <b>hall</b>, 90 blocks square (mod 96 in 6-95,
/// its walls at 5 and 96), laid out once from its own hash (<see cref="L120PlanOf"/>, kept in a <see cref="PlanCache{T}"/>)
/// with two doors onto each of its four corridors and a three-wide walk round the inside of its walls.</para>
///
/// <para><b>Halls.</b> A <b>rack hall</b> (70%) is rows of server racks two blocks high, every six blocks a pair: a
/// three-wide cold aisle between the racks' fronts (a cable tray over its middle), a one-wide hot aisle between their
/// backs, the rows cut every 8-14 racks by a cross-aisle. One rack in six is wrecked (gutted, gone, or a heap of scrap);
/// about one in five of those standing has its LEDs on, and those are nearly all the light there is. A <b>control room</b>
/// (10%) is rows of terminals and chairs facing a wall of them; a <b>cold vault</b> (8%) an empty white floor under
/// lights that mostly work; a <b>great hall</b> (7%, only where the hall and the cells round it are all the level's) a rack
/// hall six high with longer rows and a second level of trays; a <b>dead store</b> (5%) racks wrecked and stripped,
/// heaps of scrap, crates.</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> is the <see cref="L120Zone"/>; a floor tile's <see cref="Tile.Height"/> is
/// its air (3, or 6 in a great hall), its <see cref="Tile.Depth"/> the floor panel (<see cref="L120PanelClean"/> ...). A
/// rack is <see cref="L120Rack"/> (Pier the way its front faces, <see cref="Tile.Detail"/> its LEDs, <see cref="L120RackOff"/>
/// ...); a terminal <see cref="L120Terminal"/> (Detail 1: lit); a cable tray is in <see cref="Tile.Overhead"/>, a duct in
/// <see cref="Tile.Pipe"/>, all with this level's own values.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2600-0x26BF are this level's (0x26C0-0x26FF its thresholds').</summary>
    private const ulong SaltL120Shape = 0x2601, SaltL120Hall = 0x2610, SaltL120Light = 0x2611, SaltL120Corridor = 0x2612;

    /// <summary>The lattice: a service corridor every 96 blocks each way; a hall's inside is 90 square, its plan 92 with its walls.</summary>
    public const int L120Period = 96, L120HallSize = 90, L120Grid = 92;

    /// <summary>What part of the level a tile is in (kept in <see cref="Tile.Zone"/>).</summary>
    public enum L120Zone : byte { None, Corridor, Cold, Hot, Control, Vault, Store, Wall }

    public enum L120HallKind : byte { Racks, Control, Vault, Great, Store }

    /// <summary>The level's props: a server rack (two blocks high), a terminal on its desk, an office chair.</summary>
    public const ushort L120Rack = Props.L120First, L120Terminal = Props.L120First + 1, L120Chair = Props.L120First + 2;

    /// <summary>A rack's LEDs (<see cref="Tile.Detail"/>): dark, bank A on (green), bank B (amber and blue), both; or gutted.</summary>
    public const byte L120RackOff = 0, L120RackLedA = 1, L120RackLedB = 2, L120RackBoth = 3, L120RackGutted = 4;

    /// <summary>The floor panel (<see cref="Tile.Depth"/>): clean, grimy, perforated (the cold aisles' vents), one lifted out.</summary>
    public const byte L120PanelClean = 0, L120PanelDirty = 1, L120PanelVent = 2, L120PanelHole = 3;

    /// <summary>A cable tray under the ceiling (<see cref="Tile.Overhead"/>): along x or z at rel 3 (in a great hall hung from the ceiling on rods), or at rel 6 (a great hall's upper level, over its cold aisles).</summary>
    public const byte L120TrayX = Overheads.L120LegacyFirst, L120TrayZ = Overheads.L120LegacyFirst + 1, L120HighTrayX = Overheads.L120LegacyFirst + 2, L120HighTrayZ = Overheads.L120LegacyFirst + 3;

    /// <summary>A duct along the top of a corridor (<see cref="Tile.Pipe"/>): along x, along z, where two meet.</summary>
    public const byte L120DuctX = Pipes.L120LegacyFirst, L120DuctZ = Pipes.L120LegacyFirst + 1, L120DuctHub = Pipes.L120LegacyFirst + 2;

    /// <summary>A dim fitting that still gives a little warm light (the level's own ceiling kind).</summary>
    public const CeilingKind L120Dim = (CeilingKind)113;

    /// <summary>
    /// The plan of one hall. Laid out in its own coordinates (P, Q), which are the hall's (A east, B south) or, in a
    /// flipped hall, the same transposed; <see cref="Tiles"/> are kept by (A, B), -1..90 each way (the walls round it included).
    /// </summary>
    public sealed class L120Plan
    {
        public int Hx, Hz;
        public L120HallKind Kind;
        public bool Flip;
        public int Racks, Lit, Wrecked, Terminals;
        public readonly Tile[] Tiles = new Tile[L120Grid * L120Grid];

        public ref Tile At(int p, int q) => ref Flip ? ref AtAB(q, p) : ref AtAB(p, q);
        public ref Tile AtAB(int a, int b) => ref Tiles[a + 1 + (b + 1) * L120Grid];
        /// <summary>A way in the plan's coordinates (North = -Q, West = -P) as a way in the world.</summary>
        public ArchPier Dir(ArchPier d) => !Flip ? d : d switch
        {
            ArchPier.North => ArchPier.West,
            ArchPier.South => ArchPier.East,
            ArchPier.West => ArchPier.North,
            _ => ArchPier.South,
        };
        /// <summary>The block position of a place in the plan.</summary>
        public (int X, int Z) World(int p, int q) => Flip ? (Hx * L120Period + 6 + q, Hz * L120Period + 6 + p) : (Hx * L120Period + 6 + p, Hz * L120Period + 6 + q);
    }

    private PlanCache<L120Plan> l120Plans;

    /// <summary>A hall's plan (shared: read it, never change it).</summary>
    public L120Plan L120PlanOf(int hx, int hz) =>
        LazyInitializer.EnsureInitialized(ref l120Plans, () => new PlanCache<L120Plan>(32, MakeL120Plan)).Get(hx, hz);

    // ================= Where it is =================

    /// <summary>
    /// How far out along the north-east diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond Level Fun, which is 1.25 times out), as Level 3999 lies beyond the Hub.
    /// </summary>
    private int L120Reach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    public int L120CentreX => spawnMacroX + L120Reach;
    public int L120CentreZ => spawnMacroZ - L120Reach;

    /// <summary>The region's radius in macro cells.</summary>
    public int L120Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL120(double mx, double mz) => InRoundRegion(mx, mz, L120CentreX, L120CentreZ, L120Radius, SaltL120Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L120ArrivalCell(ulong h) => RoundArrivalCell(h, L120CentreX, L120CentreZ, L120Radius);

    /// <summary>Arriving: in a service corridor or a cold aisle, never wedged into a hot aisle or a control room.</summary>
    private static bool IsL120ArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone is (byte)L120Zone.Corridor or (byte)L120Zone.Cold;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L120ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the corridors and halls are laid over the edges).</summary>
    private Edge L120Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L120Wall };

    /// <summary>
    /// Lays out one of the level's cells: the corridors from arithmetic, the rest copied from the plans of the halls it
    /// covers; where the region ends, a hallway runs round inside its wall (<see cref="CarveEdgeHall"/>) so nothing it cuts
    /// through is left shut off.
    /// </summary>
    private void BuildLevel120(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue; // the wall round the region
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int u = Hashing.Mod(gx, L120Period), v = Hashing.Mod(gz, L120Period);
                bool alongZ = u is >= 1 and <= 4, alongX = v is >= 1 and <= 4;
                if (alongZ || alongX)
                {
                    L120CorridorTile(ref t, gx, gz, u, v, alongZ, alongX);
                    continue;
                }
                int hx = Hashing.FloorDiv(gx, L120Period) - (u == 0 ? 1 : 0), hz = Hashing.FloorDiv(gz, L120Period) - (v == 0 ? 1 : 0);
                int a = u == 0 ? L120HallSize : u - 6, bb = v == 0 ? L120HallSize : v - 6;
                t = L120PlanOf(hx, hz).AtAB(a, bb);
            }
        if (WalledNeighbours(Level120, mx, mz) != null) CarveEdgeHall(b, mx, mz, GetEdge(mx, mz, west: true), GetEdge(mx, mz, west: false));
    }

    /// <summary>The state of a ceiling fitting, by hash: <paramref name="off"/> of them dead, a few failing, most only glowing, the odd one dim or working.</summary>
    private CeilingKind L120Lamp(int gx, int gz, double off, double on = 0.03)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL120Light));
        if (r < off) return CeilingKind.LightOff;
        if (r < off + 0.08) return CeilingKind.LightFlicker;
        if (r >= 1 - on) return CeilingKind.LightOn;
        if (r >= 1 - on - 0.12) return L120Dim;
        return CeilingKind.LightLit;
    }

    /// <summary>A tile of a service corridor (along z where x mod 96 is 1-4, along x where z mod 96 is), or of a crossing.</summary>
    private void L120CorridorTile(ref Tile t, int gx, int gz, int u, int v, bool alongZ, bool alongX)
    {
        t.Kind = TileKind.Floor;
        t.Floor = FloorKind.L120Floor;
        t.Ceiling = CeilingKind.L120Ceiling;
        t.Zone = (byte)L120Zone.Corridor;
        t.Height = 3;
        ulong h = Hashing.Hash(seed, gx, gz, SaltL120Corridor);
        t.Depth = Hashing.Unit(h) < 0.7 ? L120PanelDirty : L120PanelClean;
        if (alongZ && alongX)
        {
            // A crossing: the ducts meet in its north-west corner; every other crossing keeps one working tube
            t.Pipe = u == 1 && v == 1 ? L120DuctHub : u == 1 ? L120DuctZ : v == 1 ? L120DuctX : Pipes.None;
            if (u == 3 && v == 3)
            {
                bool kept = Hashing.Mod(Hashing.FloorDiv(gx, L120Period) + Hashing.FloorDiv(gz, L120Period), 2) == 0;
                t.Ceiling = kept ? CeilingKind.LightOn : L120Lamp(gx, gz, 0.5);
            }
            return;
        }
        // The duct along the west (or north) wall; a fitting every six blocks down the middle, nearly all of them dead
        int across = alongZ ? u : v, along = alongZ ? gz : gx;
        t.Pipe = across == 1 ? (alongZ ? L120DuctZ : L120DuctX) : Pipes.None;
        if (across == 3 && Hashing.Mod(along, 6) == 3) t.Ceiling = L120Lamp(gx, gz, 0.45);
        // Now and then a dead cabinet or a bin against a wall
        if (across is 1 or 4)
        {
            double p = Hashing.Unit(Hashing.Mix(h));
            ArchPier into = alongZ ? (across == 1 ? ArchPier.East : ArchPier.West) : (across == 1 ? ArchPier.South : ArchPier.North);
            if (p < 0.012)
            {
                t.Variant = Props.Cabinet;
                t.Pier = into;
            }
            else if (p < 0.016) t.Variant = Props.TrashCan;
        }
    }

    // ================= A hall =================

    /// <summary>Whether a hall and the cells round it are all the level's (a great hall is laid out only then).</summary>
    private bool L120HallInside(int hx, int hz)
    {
        int x0 = MacroOf(hx * L120Period + 5) - 1, x1 = MacroOf(hx * L120Period + L120Period) + 1;
        int z0 = MacroOf(hz * L120Period + 5) - 1, z1 = MacroOf(hz * L120Period + L120Period) + 1;
        for (int mz = z0; mz <= z1; mz++)
            for (int mx = x0; mx <= x1; mx++)
                if (LevelAt(mx, mz) != Level120) return false;
        return true;
    }

    private L120Plan MakeL120Plan(int hx, int hz)
    {
        var plan = new L120Plan { Hx = hx, Hz = hz };
        ulong h = Hashing.Hash(seed, hx, hz, SaltL120Hall);
        var rng = new Rng(Hashing.Mix(h));
        plan.Flip = (h & 1) != 0;
        double r = Hashing.Unit(h);
        plan.Kind = r < 0.70 ? L120HallKind.Racks : r < 0.80 ? L120HallKind.Control : r < 0.88 ? L120HallKind.Vault
            : r < 0.95 ? L120HallKind.Great : L120HallKind.Store;
        if (plan.Kind == L120HallKind.Great && !L120HallInside(hx, hz)) plan.Kind = L120HallKind.Racks;
        bool great = plan.Kind == L120HallKind.Great;
        L120Zone zone = plan.Kind switch
        {
            L120HallKind.Control => L120Zone.Control,
            L120HallKind.Vault => L120Zone.Vault,
            L120HallKind.Store => L120Zone.Store,
            _ => L120Zone.Cold,
        };

        const int n = L120HallSize;
        for (int i = 0; i < plan.Tiles.Length; i++)
            plan.Tiles[i] = new Tile
            {
                Kind = TileKind.Wall, Pattern = WallPattern.L120Wall, Zone = (byte)L120Zone.Wall, Floor = FloorKind.L120Floor,
                Ceiling = CeilingKind.L120Ceiling, Height = 3,
            };
        for (int q = 0; q < n; q++)
            for (int p = 0; p < n; p++)
            {
                ref Tile t = ref plan.At(p, q);
                t.Kind = TileKind.Floor;
                t.Zone = (byte)zone;
                t.Height = (byte)(great ? 6 : 3);
                t.Depth = plan.Kind == L120HallKind.Store || rng.Chance(0.15) ? L120PanelDirty : L120PanelClean;
            }

        // Doors onto the four corridors: one in the middle of each wall, one more somewhere along it
        foreach (var (side, wall) in new[] { (0, -1), (1, n), (2, -1), (3, n) })
        {
            int other = rng.Chance(0.5) ? rng.Range(8, 36) : rng.Range(52, 79);
            foreach (int at in new[] { 43, other })
                for (int k = 0; k < 3; k++)
                {
                    ref Tile t = ref side < 2 ? ref plan.AtAB(wall, at + k) : ref plan.AtAB(at + k, wall);
                    t.Kind = TileKind.Doorway;
                    t.Zone = (byte)L120Zone.Corridor;
                    t.Height = 3;
                }
        }

        switch (plan.Kind)
        {
            case L120HallKind.Racks or L120HallKind.Great or L120HallKind.Store: L120LayRacks(plan, ref rng); break;
            case L120HallKind.Control: L120LayControl(plan, ref rng); break;
            case L120HallKind.Vault: L120LayVault(plan, ref rng); break;
        }

        // The walk round the inside of the walls: a fitting every eight blocks down its middle, nearly all dead (a vault's mostly working)
        bool vault = plan.Kind == L120HallKind.Vault;
        for (int i = 4; i < n - 3; i += 8)
            foreach (var (p, q) in new[] { (i, 1), (i, n - 2), (1, i), (n - 2, i) })
            {
                var (x, z) = plan.World(p, q);
                plan.At(p, q).Ceiling = vault ? L120Lamp(x, z, 0.3, 0.1) : L120Lamp(x, z, 0.6, 0.02);
            }
        return plan;
    }

    /// <summary>
    /// The rack rows of a rack hall, a great hall or a dead store: across Q every six blocks a cold aisle (three wide), a
    /// row of racks facing it, a hot aisle (one wide), a row facing the next cold aisle; along P the rows cut by cross-aisles.
    /// </summary>
    private static void L120LayRacks(L120Plan plan, ref Rng rng)
    {
        bool great = plan.Kind == L120HallKind.Great, store = plan.Kind == L120HallKind.Store;
        const int lo = 3, hi = L120HallSize - 4;
        // Where the rows run and where the cross-aisles cut them: the same for every row of the hall
        var rack = new bool[L120HallSize];
        for (int p = lo; p <= hi;)
        {
            int end = Math.Min(p + rng.Range(great ? 16 : 8, great ? 24 : 14) - 1, hi);
            if (hi - end < 4) end = hi;
            for (int k = p; k <= end; k++) rack[k] = true;
            p = end + 4;
        }
        // A tray runs along P: along the world's x unless the hall is flipped
        byte tray = plan.Flip ? L120TrayZ : L120TrayX, high = plan.Flip ? L120HighTrayZ : L120HighTrayX;
        L120Zone cold = store ? L120Zone.Store : L120Zone.Cold, hot = store ? L120Zone.Store : L120Zone.Hot;

        for (int q = lo; q <= hi; q++)
        {
            int o = (q - lo) % 6;
            for (int p = lo; p <= hi; p++)
            {
                ref Tile t = ref plan.At(p, q);
                if (o <= 2)
                {
                    // The cold aisle: perforated panels down its middle, a tray over them (a great hall's high up)
                    t.Zone = (byte)cold;
                    if (o == 1)
                    {
                        if (!store) t.Depth = rng.Chance(1 / 40.0) ? L120PanelHole : L120PanelVent;
                        t.Overhead = great ? high : tray;
                    }
                    continue;
                }
                if (o == 4)
                {
                    // The hot aisle between the racks' backs (a great hall's lower trays over it)
                    t.Zone = (byte)hot;
                    t.Depth = L120PanelDirty;
                    if (great) t.Overhead = tray;
                    continue;
                }
                t.Zone = (byte)(rack[p] ? hot : cold);
                if (!rack[p]) continue; // a cross-aisle
                L120PlaceRack(plan, ref t, ref rng, o == 3 ? ArchPier.North : ArchPier.South, store);
            }
        }
    }

    /// <summary>One rack in a row, facing its cold aisle: one in six wrecked (in a dead store most), about one in five of the rest lit.</summary>
    private static void L120PlaceRack(L120Plan plan, ref Tile t, ref Rng rng, ArchPier face, bool store)
    {
        double w = rng.NextDouble();
        t.Pier = plan.Dir(face);
        if (store)
        {
            if (w < 0.30) Rack(ref t, L120RackGutted);
            else if (w < 0.50) t.Variant = Props.ScrapMetal;
            else if (w < 0.68) t.Variant = Props.MachineParts;
            else if (w < 0.78) t.Variant = Props.CardboardBoxes;
            else if (w < 0.86) t.Stack = (byte)rng.Range(1, 2); // crates
            else if (w < 0.92) t.Variant = Props.Drum;
            else Rack(ref t, rng.Chance(0.25) ? L120RackLedA : L120RackOff);
            if (t.Variant != L120Rack) plan.Wrecked++;
            return;
        }
        if (w < 1 / 6.0)
        {
            plan.Wrecked++;
            double k = rng.NextDouble();
            if (k < 0.5) Rack(ref t, L120RackGutted);
            else if (k < 0.8) t.Variant = Props.MachineParts; // pulled out: only its parts left on the floor
            else t.Variant = Props.ScrapMetal; // toppled and broken up
            return;
        }
        Rack(ref t, rng.Chance(0.22) ? (byte)rng.Range(L120RackLedA, L120RackBoth) : L120RackOff);

        void Rack(ref Tile r, byte state)
        {
            r.Variant = L120Rack;
            r.Detail = state;
            plan.Racks++;
            if (state is >= L120RackLedA and <= L120RackBoth) plan.Lit++;
        }
    }

    /// <summary>A control room: rows of terminals with their chairs, everyone looking towards a wall of terminals along the hall's low-Q wall (Pier: the way a screen faces).</summary>
    private void L120LayControl(L120Plan plan, ref Rng rng)
    {
        const int n = L120HallSize;
        var r = rng;
        void Terminal(int p, int q, ArchPier face, double lit)
        {
            ref Tile t = ref plan.At(p, q);
            t.Variant = L120Terminal;
            t.Pier = plan.Dir(face);
            t.Detail = (byte)(r.Chance(lit) ? 1 : 0);
            plan.Terminals++;
        }
        bool DoorBeside(int p) =>
            plan.At(p - 1, -1).Kind == TileKind.Doorway || plan.At(p, -1).Kind == TileKind.Doorway || plan.At(p + 1, -1).Kind == TileKind.Doorway;
        // The wall of terminals, against the wall itself (the walk past it two wide)
        for (int p = 4; p <= n - 5; p++)
            if (!DoorBeside(p)) Terminal(p, 0, ArchPier.South, 0.5);
        // The desks in rows, a gap every twelve, each with its chair behind it
        for (int q = 7; q <= n - 6; q += 5)
            for (int p = 4; p <= n - 5; p++)
            {
                if ((p - 4) % 12 == 11) continue;
                if (r.Chance(0.06)) continue; // a desk taken away
                Terminal(p, q, ArchPier.South, 0.28); // its screen to the chair behind it
                if (r.Chance(0.85))
                {
                    ref Tile c = ref plan.At(p, q + 1);
                    c.Variant = L120Chair;
                    c.Pier = plan.Dir(r.Chance(0.85) ? ArchPier.North : ArchPier.East);
                }
            }
        rng = r;
        // A few lights over the desks, most of them dead
        for (int q = 9; q < n - 3; q += 10)
            for (int p = 10; p < n - 3; p += 12)
            {
                var (x, z) = plan.World(p, q);
                plan.At(p, q).Ceiling = L120Lamp(x, z, 0.55, 0);
            }
    }

    /// <summary>A cold vault: an empty white floor under lights that mostly work, a few racks and cabinets left standing.</summary>
    private void L120LayVault(L120Plan plan, ref Rng rng)
    {
        const int n = L120HallSize;
        for (int q = 0; q < n; q++)
            for (int p = 0; p < n; p++) plan.At(p, q).Depth = L120PanelClean;
        for (int k = rng.Range(6, 14); k > 0; k--)
        {
            int p = rng.Range(6, n - 7), q = rng.Range(6, n - 7);
            ref Tile t = ref plan.At(p, q);
            if (rng.Chance(0.6))
            {
                t.Variant = L120Rack;
                t.Detail = rng.Chance(0.5) ? L120RackGutted : L120RackOff;
                plan.Racks++;
            }
            else t.Variant = Props.Cabinet;
            t.Pier = plan.Dir((ArchPier)rng.Range(0, 3));
        }
        // Lights in a grid
        for (int q = 3; q < n - 3; q += 6)
            for (int p = 3; p < n - 3; p += 6)
            {
                var (x, z) = plan.World(p, q);
                plan.At(p, q).Ceiling = L120Lamp(x, z, 0.25, 0.08);
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L120First"/>-<see cref="Props.L120Last"/>) people walk through: none.</summary>
    private static bool L120WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>
    /// The temperature: the hot aisles behind the racks are hot enough to cost food (38 °C, see HeatSystem), a dead store
    /// warm; the cold aisles and control rooms are chilled, the vaults cold, the corridors in between.
    /// </summary>
    private float L120Temperature(int x, int y, int z, int floorY)
    {
        Tile t = TileAt(x, z);
        if (t.Level != Level120) return LevelTemperatures[Level120];
        return t.Zone switch
        {
            (byte)L120Zone.Hot => 38f,
            (byte)L120Zone.Store => 33f,
            (byte)L120Zone.Cold => 22f,
            (byte)L120Zone.Control => 23f,
            (byte)L120Zone.Vault => 15f,
            (byte)L120Zone.Corridor => 27f,
            _ => LevelTemperatures[Level120],
        };
    }

    /// <summary>Reality stability: a little steadier than neutral; nothing here is going anywhere.</summary>
    private float L120Stability(double x, double y, double z, int floorY, float drift) => 1.05f;
}
