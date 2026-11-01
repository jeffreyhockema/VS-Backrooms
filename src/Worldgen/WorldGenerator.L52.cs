using System;
using System.Collections.Generic;
using Zone = Backrooms.Worldgen.WorldLayout.L52Zone;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 52, "The Greenfield Campus" (experimental, kept as level 23), laid out in WorldLayout.Level52.cs, from its
/// own floor (<see cref="WorldGeometry.FloorFor"/>): the open land (grass over soil and rock, gravel and sand roads, tall
/// grass and wild flowers in patches, lone oaks, birches and maples), the campuses' fences (a concrete barrier, chain-link
/// over it), lawns, paving, artificial turf and courts, and the buildings storey by storey. A building's storey is four
/// blocks: its slab (<c>l52-slab-*</c>: the floor finish on top, the suspended ceiling of the storey below underneath; a
/// troffer, <c>l52-light-*</c>, where a light hangs: lit down the corridors, dark in the rooms), then three of air. Outside
/// walls are the campus's façade with window bays (<c>l52-window-*</c>) in every storey, doors on the ground floor, a parapet
/// with a coping over a flat roof; inside walls the campus's paint (<c>l52-wall-*</c>), banks of lockers along the corridors.
/// What stands in a room on each storey is <see cref="WorldLayout.L52Furnish"/>'s; the stairs are scissor flights.
///
/// Every block of the level's own is looked up softly (<see cref="L52Block"/>): what is missing is drawn as concrete
/// (structure) or left out, logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] L52SlabKinds = { "hall", "room", "carpetblue", "carpetred", "carpetgreen", "carpetgrey", "lino", "concrete", "wood", "worn" };
    private static readonly string[] L52LightStates = { "on", "lit", "off", "flicker" };
    private const int L52SlabConcrete = 7, L52LightOn = 0, L52LightOff = 2;

    private int l52Grass, l52Soil, l52Rock, l52Gravel, l52Sand, l52Coping, l52Barrier, l52Roof, l52Plinth, l52Canopy;
    private readonly int[] l52Trim = new int[3];
    private readonly int[,] l52Wall = new int[4, 3], l52Light = new int[10, 4], l52Window = new int[2, 2], l52Chain = new int[2, 2];
    private readonly int[,,] l52Locker = new int[4, 2, 4], l52Board = new int[2, 3, 4];
    private readonly int[,,,] l52Plaque = new int[2, 10, 10, 4];
    private readonly int[,] l52Stall = new int[2, 4], l52Hood = new int[2, 4];
    private readonly int[] l52Bleacher = new int[4], l52PitchLine = new int[2], l52Track = new int[3];
    private readonly int[] l52Slab = new int[10], l52Facade = new int[5], l52Turf = new int[2], l52Court = new int[3], l52Paving = new int[2],
        l52GymLine = new int[3], l52Desk = new int[4], l52Fountain = new int[4];
    private readonly HashSet<string> l52Missing = new();

    /// <summary>A block of the level's, or <paramref name="fallback"/> if its asset is not there (logged once).</summary>
    private int L52Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l52Missing.Add(code) && l52Missing.Count <= 20) api.Logger.Warning("[backrooms] Level 52: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>The level's block ids (called from the constructor, after the vegetation's).</summary>
    private void InitL52()
    {
        l52Grass = GameId("game:soil-medium-normal");
        l52Soil = GameId("game:soil-medium-none");
        l52Rock = GameId("game:rock-granite", "game:rock-andesite");
        l52Gravel = GameId("game:gravel-granite", "game:gravel-andesite");
        l52Sand = GameId("game:sand-granite", "game:sand-andesite");
        string[] parts = { "base", "dado", "upper" }, halves = { "lower", "upper" }, axes = { "ns", "we" }, ends = { "l", "m", "r" };
        for (int p = 0; p < 4; p++)
        {
            string paint = WorldLayout.L52Paints[p];
            for (int k = 0; k < 3; k++) l52Wall[p, k] = L52Block($"l52-wall-{paint}-{parts[k]}", concreteId);
            for (int k = 0; k < 2; k++)
                for (int f = 0; f < 4; f++) l52Locker[p, k, f] = L52Block($"l52-locker-{paint}-{halves[k]}-{Sides[f]}", l52Wall[p, k]);
        }
        for (int i = 0; i < 5; i++) l52Facade[i] = L52Block("l52-facade-" + WorldLayout.L52Facades[i], concreteId);
        l52Coping = L52Block("l52-coping", l52Facade[0]);
        l52Barrier = L52Block("l52-barrier", concreteId);
        l52Roof = L52Block("l52-roof", concreteId);
        for (int i = 0; i < 3; i++) l52Trim[i] = L52Block("l52-band-" + WorldLayout.L52Trims[i], l52Coping);
        l52Plinth = L52Block("l52-plinth", l52Trim[1]);
        l52Canopy = L52Block("l52-canopy", l52Coping);
        for (int k = 0; k < 2; k++)
            for (int a = 0; a < 2; a++)
            {
                l52Window[k, a] = L52Block($"l52-window-{halves[k]}-{axes[a]}", concreteId);
                l52Chain[k, a] = L52Block($"l52-chainlink-{halves[k]}-{axes[a]}");
            }
        for (int s = 0; s < L52SlabKinds.Length; s++)
        {
            l52Slab[s] = L52Block("l52-slab-" + L52SlabKinds[s], concreteId);
            for (int st = 0; st < 4; st++) l52Light[s, st] = L52Block($"l52-light-{L52SlabKinds[s]}-{L52LightStates[st]}", l52Slab[s]);
        }
        l52Turf[0] = L52Block("l52-turf-plain", l52Grass);
        l52Turf[1] = L52Block("l52-turf-worn", l52Turf[0]);
        string[] courts = { "plain", "linens", "linewe" };
        for (int i = 0; i < 3; i++)
        {
            l52Court[i] = L52Block("l52-court-" + courts[i], concreteId);
            l52GymLine[i] = L52Block("l52-gymfloor-" + courts[i], l52Slab[8]);
        }
        l52Paving[0] = L52Block("l52-paving-a", concreteId);
        l52Paving[1] = L52Block("l52-paving-b", l52Paving[0]);
        for (int f = 0; f < 4; f++)
        {
            l52Desk[f] = L52Block("l52-desk-" + Sides[f]);
            l52Fountain[f] = L52Block("l52-fountain-" + Sides[f], coolerIds[f]);
            for (int p = 0; p < 2; p++)
                for (int e = 0; e < 3; e++) l52Board[p, e, f] = L52Block($"l52-chalkboard-{halves[p]}-{ends[e]}-{Sides[f]}");
            for (int h = 0; h < 2; h++)
                for (int a = 0; a < 10; a++)
                    for (int b = 0; b < 10; b++) l52Plaque[h, a, b, f] = L52Block($"l52-plaque-{(h == 0 ? "lo" : "hi")}-{a}-{b}-{Sides[f]}");
        }
        for (int f = 0; f < 4; f++)
        {
            for (int k = 0; k < 2; k++)
            {
                l52Stall[k, f] = L52Block($"l52-stall-{halves[k]}-{Sides[f]}");
                l52Hood[k, f] = L52Block($"l52-fumehood-{halves[k]}-{Sides[f]}");
            }
            l52Bleacher[f] = L52Block("l52-bleacher-" + Sides[f]);
        }
        l52PitchLine[0] = L52Block("l52-turf-linens", l52Turf[0]);
        l52PitchLine[1] = L52Block("l52-turf-linewe", l52Turf[0]);
        for (int i = 0; i < 3; i++) l52Track[i] = L52Block("l52-track-" + courts[i], l52Court[i]);
        InitL52Links();
    }

    /// <summary>
    /// A campus tile's fitting at a height (WorldLayout.Level52.Detail.cs), or -1 for none: <paramref name="rel"/> above the
    /// floor (outdoors, above the ground); fittings on every storey count below <paramref name="top"/> (the building's roof).
    /// </summary>
    private int L52FixtureAt(WorldLayout.L52Campus c, int index, int rel, int top, out int fluid)
    {
        fluid = 0;
        if (!c.Fixtures.TryGetValue(index, out var list)) return -1;
        int h = rel % WorldLayout.L52Storey;
        foreach (WorldLayout.L52Fixture f in list)
        {
            if (f.EveryStorey ? rel >= top || h < f.Lo || h > f.Hi : rel < f.Lo || rel > f.Hi) continue;
            if (f.Code == "=water") { fluid = waterId; return 0; }
            if (f.Code == "=hedge") return treeLeafIds[0, 0];
            if (f.Code.StartsWith("=stair-"))
                return stairIds[f.Code.EndsWith("north") ? 0 : f.Code.EndsWith("east") ? 1 : f.Code.EndsWith("south") ? 2 : 3];
            return modBlocks.TryGetValue(f.Code, out int id) ? id : 0;
        }
        return -1;
    }

    /// <summary>The slab kind (<see cref="L52SlabKinds"/>) of a floor finish.</summary>
    private static int L52SlabOf(FloorKind floor) => floor switch
    {
        FloorKind.L52Floor => 0,
        FloorKind.L52CarpetBlue => 2,
        FloorKind.L52CarpetRed => 3,
        FloorKind.L52CarpetGreen => 4,
        FloorKind.L52CarpetGrey => 5,
        FloorKind.L52Lino => 6,
        FloorKind.L52Concrete => 7,
        FloorKind.L52Gym or FloorKind.L52GymLineNS or FloorKind.L52GymLineWE => 8,
        FloorKind.L52HallWorn => 9,
        _ => 1,
    };

    // ---- One column, worked out once (the column builder is asked for every height in turn) ----

    private struct L52Column
    {
        public WorldGenerator Owner;
        public int Gx, Gz;
        public WorldLayout.L52Campus Campus;
        public int Index;
        /// <summary>The nearest tree whose crown reaches this column: its ground, and this column's offset from its trunk; <see cref="Wood"/> -1 for none.</summary>
        public int TreeGround, TreeDx, TreeDz, Wood;
        /// <summary>What grows on the ground here (0 nothing).</summary>
        public int Plant;
    }

    [ThreadStatic] private static L52Column l52Column;

    private ref L52Column L52Col(in Tile t, int gx, int gz)
    {
        ref L52Column c = ref l52Column;
        if (c.Owner == this && c.Gx == gx && c.Gz == gz) return ref c;
        c = default;
        c.Owner = this;
        c.Gx = gx;
        c.Gz = gz;
        c.Campus = layout.L52CampusAt(gx, gz, out c.Index);
        c.Wood = -1;
        // A tree's crown from a trunk within two blocks (the nearest, if more than one)
        int best = int.MaxValue;
        Tile[] cell = null;
        int cellX = 0, cellZ = 0;
        const int size = WorldLayout.MacroSize;
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
            {
                if (Math.Abs(dx) == 2 && Math.Abs(dz) == 2) continue;
                int px = gx + dx, pz = gz + dz;
                int mx = Hashing.FloorDiv(px, size), mz = Hashing.FloorDiv(pz, size);
                if (cell == null || mx != cellX || mz != cellZ) { cell = Macro(mx, mz); cellX = mx; cellZ = mz; }
                Tile n = cell[WorldLayout.TileIndex(px - mx * size, pz - mz * size)];
                if (n.Variant != Props.Tree || n.Kind != TileKind.Floor || n.Level != WorldLayout.Level52) continue;
                int score = dx * dx + dz * dz;
                if (score >= best) continue;
                best = score;
                c.TreeGround = n.Height;
                c.TreeDx = -dx;
                c.TreeDz = -dz;
                c.Wood = (int)(Hashing.Hash(seed, px, pz, 0x2330) % 3);
            }
        // Tall grass and wild flowers in patches on the open hills ("a little flora")
        if (t.Zone == (byte)Zone.Hill && t.Variant == 0)
        {
            double patch = Noise2(gx / 13.0, gz / 13.0, 0x2331);
            ulong h = Hashing.Hash(seed, gx, gz, 0x2332);
            double r = Hashing.Unit(h);
            if (patch > 0.25 && r < 0.55) c.Plant = grassIds[Math.Min(5, (int)((patch - 0.25) * 6) + (int)((h >> 40) % 2))];
            else if (r < 0.012) c.Plant = marginFlowerIds[(int)((h >> 20) % (ulong)marginFlowerIds.Length)];
            else if (r < 0.05) c.Plant = grassIds[0];
        }
        return ref c;
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level52Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        // The rim: the hills rise into a ridge
        if (t.Kind == TileKind.Wall && t.Zone == 0) return rel < 26 ? (rel < 22 ? l52Rock : l52Soil) : rel == 26 ? l52Grass : 0;
        if (rel < -6) return concreteId;
        ref L52Column col = ref L52Col(t, gx, gz);
        if (t.Depth > 0 && col.Campus != null) return L52BuildingBlock(t, ref col, gx, gz, rel);
        if (col.Campus != null && rel > t.Height && col.Campus.HasFixture[col.Index])
        {
            int fb = L52FixtureAt(col.Campus, col.Index, rel - t.Height, 0, out fluid);
            if (fb >= 0) return fb;
        }

        int g = t.Height;
        // The fences: a concrete barrier with chain-link over it (out on the plain, the chain-link alone)
        if (t.Zone is (byte)Zone.Fence or (byte)Zone.StrayFence)
        {
            int axis = t.Pier == ArchPier.North ? 1 : 0;
            if (rel <= g) return rel == g && t.Zone == (byte)Zone.Fence ? l52Paving[0] : rel == g ? l52Grass : rel >= g - 2 ? l52Soil : l52Rock;
            int up = rel - g - (t.Zone == (byte)Zone.Fence ? 1 : 0);
            if (up == 0) return l52Barrier;
            return up is 1 or 2 ? l52Chain[up - 1, axis] : 0;
        }
        if (rel <= g)
        {
            if (rel < g - 3) return l52Rock;
            if (rel < g) return t.Zone is (byte)Zone.Path or (byte)Zone.Court ? concreteId : t.Zone == (byte)Zone.Road ? l52Gravel : l52Soil;
            return t.Floor switch
            {
                FloorKind.L52Turf => Noise2(gx / 6.0, gz / 6.0, 0x2333) > 0.5 ? l52Turf[1] : l52Turf[0],
                FloorKind.L52Paving => Hashing.Unit(Hashing.Hash(seed, gx, gz, 0x2334)) < 0.08 ? l52Paving[1] : l52Paving[0],
                FloorKind.L52Gravel => l52Gravel,
                FloorKind.L52Sand => l52Sand,
                FloorKind.L52Court => l52Court[0],
                FloorKind.L52CourtLineNS => l52Court[1],
                FloorKind.L52CourtLineWE => l52Court[2],
                FloorKind.L52PitchLineNS => l52PitchLine[0],
                FloorKind.L52PitchLineWE => l52PitchLine[1],
                FloorKind.L52Track => l52Track[0],
                FloorKind.L52TrackLineNS => l52Track[1],
                FloorKind.L52TrackLineWE => l52Track[2],
                _ => l52Grass,
            };
        }
        int up1 = rel - g;
        // A pedestrian bridge at the first floor up: its floor, glazed sides, roof (the sides in the quad's façade and trim)
        if (t.Overhead == Overheads.L52Bridge && col.Campus != null)
        {
            int b = up1 - WorldLayout.L52BridgeStorey * WorldLayout.L52Storey;
            if (b >= 0 && b <= 4)
            {
                WorldLayout.L52Building quad = col.Campus.Buildings[0];
                bool side = t.Stack == 1;
                return b switch
                {
                    0 => side ? l52Trim[quad.Trim] : l52Slab[0],
                    1 => side ? l52Facade[quad.Facade] : 0,
                    2 or 3 => side ? l52Window[b - 2, t.Pier is ArchPier.East or ArchPier.West ? 1 : 0] : 0,
                    _ => side ? l52Trim[quad.Trim] : l52Roof,
                };
            }
        }
        // An entrance's canopy, at the first floor line
        if (t.Overhead == Overheads.L52Canopy && up1 == WorldLayout.L52Storey) return l52Canopy;
        // A tree's trunk (five logs), and the crowns of the trees round about
        if (t.Variant == Props.Tree && up1 <= 5) return treeLogIds[Math.Max(0, col.Wood)];
        if (col.Wood >= 0)
        {
            int k = rel - col.TreeGround - 5, ax = Math.Abs(col.TreeDx), az = Math.Abs(col.TreeDz), m = ax + az;
            bool leaf = k switch
            {
                -2 or -1 => m >= 1 && m <= 3,
                0 or 1 => m <= 3,
                2 => m <= 2,
                3 => m <= 1,
                _ => false,
            };
            if (leaf) return treeLeafIds[col.Wood, 0];
        }
        if (up1 == 1)
        {
            if (t.SupplyBox) return BoxOf(t);
            if (t.Variant == 0) return col.Plant;
            if (t.Variant == Props.L52Fountain) return l52Fountain[Facing(t.Pier)];
            return AnyProp(t, 1);
        }
        return 0;
    }

    /// <summary>A block of a building: its storey (rel / 4) and the height in it (rel % 4, 0 the slab).</summary>
    private int L52BuildingBlock(in Tile t, ref L52Column col, int gx, int gz, int rel)
    {
        WorldLayout.L52Campus c = col.Campus;
        int n = t.Depth, top = n * WorldLayout.L52Storey;
        if (rel < 0) return concreteId;
        if (rel > 0 && c.HasFixture[col.Index])
        {
            int fb = L52FixtureAt(c, col.Index, rel, n * WorldLayout.L52Storey, out _);
            if (fb >= 0) return fb;
        }
        int paint = c.Paint;
        if (t.Zone is (byte)Zone.Ext or (byte)Zone.Entrance)
        {
            // (The building's own look: its façade, trim, bands and base course; see WorldLayout.L52AddBuilding)
            WorldLayout.L52Building bld = t.Detail > 0 && t.Detail <= c.Buildings.Count ? c.Buildings[t.Detail - 1] : null;
            int trim = l52Trim[bld?.Trim ?? 0];
            if (rel == top + 2) return l52Coping;
            if (rel > top + 2) return 0;
            int s = rel / 4, k = rel % 4;
            bool entrance = t.Zone == (byte)Zone.Entrance;
            if (entrance && s == 0 && k is 1 or 2) return 0;
            // A bridge's opening at its floor, and its lintel
            if (s == WorldLayout.L52BridgeStorey && t.Overhead == Overheads.L52BridgeDoor && k > 0) return k == 3 ? trim : 0;
            // The door's lintel and the surround either side of it
            if (s == 0 && k == 3 && entrance || s == 0 && k >= 1 && t.Overhead == Overheads.L52Frame) return trim;
            if (rel < top && k is 2 or 3 && (t.Under == Unders.L52Window || entrance && s > 0))
                return l52Window[k - 2, t.Pier is ArchPier.North or ArchPier.South ? 1 : 0];
            if (entrance && rel == 0) return l52Slab[0];
            if (bld != null)
            {
                // The cornice under the parapet, the bands at the floor lines, the base course
                if (rel == top || k == 0 && s >= 1 && (bld.Band == 1 || bld.Band == 2 && s == 1)) return trim;
                if (rel == 1 && bld.Plinth) return l52Plinth;
            }
            return l52Facade[bld?.Facade ?? c.Facade];
        }
        // Over the top storey: the roof, an air-conditioning unit on it now and then
        if (rel == top + 1) return l52Roof;
        if (rel == top + 2)
        {
            if (t.Kind != TileKind.Floor || t.Zone == (byte)Zone.Stair) return 0;
            ulong hh = Hashing.Hash(seed, gx, gz, 0x2335);
            return Hashing.Unit(hh) < 0.003 ? AnyProp(new Tile { Kind = TileKind.Floor, Variant = Props.AcUnit, Pier = (ArchPier)(int)((hh >> 30) % 4), Level = t.Level }, 1) : 0;
        }
        if (rel > top) return 0;
        if (t.Zone == (byte)Zone.Stair) return L52StairBlock(t, rel, n, paint);
        int storey = rel / 4, h = rel % 4;

        if (t.Kind == TileKind.Wall)
        {
            if (h == 0) return concreteId;
            if (t.Under == Unders.L52Locker && h <= 2) return l52Locker[paint, h - 1, Facing(t.Pier)];
            return l52Wall[paint, h - 1];
        }
        int kind = L52SlabOf(t.Floor);
        if (t.Kind == TileKind.Doorway)
        {
            if (h == 0) return l52Slab[kind];
            return h == 3 ? l52Wall[paint, 2] : 0;
        }
        // A floor tile: its slab (the floor of this storey, the ceiling of the one below), then its three of air
        bool hall = t.Zone == (byte)Zone.Hall;
        if (h == 0)
        {
            if (storey == 0)
                return t.Floor switch
                {
                    FloorKind.L52GymLineNS => l52GymLine[1],
                    FloorKind.L52GymLineWE => l52GymLine[2],
                    _ => l52Slab[kind],
                };
            if (hall && storey < n) return 0; // (a hall is two storeys high)
            return t.Ceiling switch
            {
                CeilingKind.LightOn => l52Light[kind, L52LightState(gx, gz, storey, hall)],
                CeilingKind.LightOff => l52Light[kind, L52LightOff],
                _ => l52Slab[kind],
            };
        }
        if (hall && storey == 1) return 0;
        // What stands on this storey: the plaques, the ground storey's props from the plan, the others' from the same arithmetic
        int idx = col.Index;
        if (t.Overhead is Overheads.L52PlaqueLo or Overheads.L52PlaqueHi)
        {
            if (h != 2) return 0;
            int roomId = c.RoomOf[idx];
            if (roomId < 0) return 0;
            WorldLayout.L52Room room = c.Rooms[roomId];
            bool lo = t.Overhead == Overheads.L52PlaqueLo;
            int a = lo ? room.Number / 10 % 10 : (storey + 1) % 10, b = lo ? room.Number % 10 : room.Building % 10;
            return l52Plaque[lo ? 0 : 1, a, b, Facing(t.Pier)];
        }
        ushort prop;
        ArchPier facing;
        byte stack = 0;
        bool box = false;
        if (storey == 0)
        {
            prop = t.Variant;
            facing = t.Pier;
            stack = t.Stack;
            box = t.SupplyBox;
        }
        else if (t.Zone is (byte)Zone.Corridor or (byte)Zone.Lobby)
            prop = layout.L52CorridorThing(c, idx % c.W, idx / c.W, storey, out facing);
        else
        {
            int roomId = c.RoomOf[idx];
            if (roomId < 0) return 0;
            prop = layout.L52Furnish(c, c.Rooms[roomId], storey, idx % c.W, idx / c.W, out facing, out stack, out box);
        }
        if (prop == Props.L52Chalkboard)
            return h is 2 or 3 ? l52Board[h - 2, Math.Min((int)stack, 2), Facing(facing)] : 0;
        if (prop == Props.L52Stall) return h is 1 or 2 ? l52Stall[h - 1, Facing(facing)] : 0;
        if (prop == Props.L52FumeHood) return h is 1 or 2 ? l52Hood[h - 1, Facing(facing)] : 0;
        if (prop == Props.L52Bleacher) return h == 1 + stack ? l52Bleacher[Facing(facing)] : h >= 1 && h <= stack ? l52Plinth : 0;
        if (h != 1) return 0;
        if (box)
        {
            // (Above the ground storey a box is sealed or torn by its own hash, as the layout marks the ground storey's)
            if (storey == 0) return BoxOf(t);
            return Hashing.Unit(Hashing.Hash(seed, gx * 31 + storey, gz, 0x2336)) < 0.3 ? boxTornId : boxId;
        }
        if (prop == 0) return 0;
        int f = Facing(facing);
        return prop switch
        {
            Props.L52Desk => l52Desk[f],
            Props.L52Fountain => l52Fountain[f],
            _ => AnyProp(new Tile { Kind = TileKind.Floor, Variant = prop, Pier = facing, Stack = stack, Level = t.Level }, 1),
        };
    }

    /// <summary>A light on a storey: most give light or glow, a few are dead or failing (in a hall, all work).</summary>
    private int L52LightState(int gx, int gz, int storey, bool hall)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz * 31 + storey, 0x2337));
        if (hall) return r < 0.6 ? 0 : 1;
        return r < 0.45 ? 0 : r < 0.88 ? 1 : r < 0.95 ? 2 : 3;
    }

    /// <summary>
    /// The scissor stair (<see cref="WorldLayout.L52StairWell"/>): flight A (i 0-2) climbs toward -j from even storeys, flight
    /// B (i 4-6) toward +j from odd ones, four steps a storey, round a core wall (i 3); the landings (j 0 and 5-6) at every
    /// storey, lit.
    /// </summary>
    private int L52StairBlock(in Tile t, int rel, int storeys, int paint)
    {
        int i = t.Detail / 8, j = t.Detail % 8, top = storeys * WorldLayout.L52Storey;
        if (rel == 0) return l52Slab[L52SlabConcrete];
        int lit = t.Ceiling == CeilingKind.LightOn ? l52Light[L52SlabConcrete, L52LightOn] : l52Slab[L52SlabConcrete];
        if (rel == top) return i == 3 ? lit : l52Slab[L52SlabConcrete];
        if (i == 3 && j >= 1 && j <= 4) return l52Wall[paint, rel % 4 == 0 ? 2 : rel % 4 - 1];
        if (j == 0 || j >= 5) return rel % 4 != 0 ? 0 : lit;
        int sf = (rel - 1) / 4, k = rel - 4 * sf;
        if (sf > storeys - 2) return 0;
        bool a = i <= 2;
        if (a ? sf % 2 != 0 : sf % 2 != 1) return 0;
        int step = a ? 5 - j : j;
        if (k == step) return stairIds[Facing(a ? Opposite(t.Pier) : t.Pier)];
        return k < step ? concreteId : 0;
    }
}
