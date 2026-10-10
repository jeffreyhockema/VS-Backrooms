using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Vanilla plants for the levels under the open sky (9, 10, 11 and 94), decided here from hashes and noise rather than
/// from the layout, so no plan changes: tall grass of six heights in patches, weeds along the fences, ferns and fallen
/// sticks in the shade of the trees, flowers along the field margins, reeds and lilies on Level 10's ponds, and Level
/// 94's hills grown over in the stripes they are mown in. Trees are drawn here too, from their trunk tiles: oak, birch
/// or maple, a trunk of four to six logs and a rounded crown two blocks out (one, over pavement), worked out column by
/// column from the trunks round each column, so a crown carries on across cell edges.
/// </summary>
public sealed partial class WorldGenerator
{
    private const ulong SaltVegCover = 0x5E61, SaltVegHeight = 0x5E62, SaltVegJitter = 0x5E63, SaltVegPick = 0x5E64,
        SaltVegPatch = 0x5E65, SaltVegTree = 0x5E66, SaltVegCrown = 0x5E67, SaltVegPond = 0x5E68, SaltVegKind = 0x5E69;

    /// <summary>The trunk of every tree on these levels is drawn from this (the column builders all pass 4).</summary>
    private const int TreeTrunk = 4;

    /// <summary>Tall grass, veryshort to verytall.</summary>
    private readonly int[] grassIds = new int[6];
    private int[] weedIds, fernIds, marginFlowerIds, brightFlowerIds;
    private int looseStickId, waterReedId, waterLilyId, sedgeId, tuleId;
    private readonly int[] treeLogIds = new int[3];
    private readonly int[,] treeLeafIds = new int[3, 8];

    private void InitVegetation()
    {
        string[] heights = { "veryshort", "short", "mediumshort", "medium", "tall", "verytall" };
        for (int i = 0; i < heights.Length; i++) grassIds[i] = GameId($"game:tallgrass-{heights[i]}-free", "game:tallgrass-medium-free");
        weedIds = VegIds("game:flower-wilddaisy-free", "game:flower-cowparsley-free", "game:flower-catmint-free", "game:flower-redtopgrass-free",
            "game:flower-mugwort-free");
        fernIds = VegIds("game:fern-eaglefern", "game:fern-hartstongue", "game:fern-cinnamonfern", "game:tallfern");
        marginFlowerIds = VegIds("game:flower-goldenpoppy-free", "game:flower-cornflower-free", "game:flower-lupine-blue-free",
            "game:flower-lupine-purple-free", "game:flower-lupine-red-free", "game:flower-wilddaisy-free");
        brightFlowerIds = VegIds("game:flower-goldenpoppy-free", "game:flower-cornflower-free", "game:flower-lupine-red-free",
            "game:flower-lupine-blue-free", "game:flower-lupine-orange-free");
        looseStickId = OptionalId("game:loosestick-free");
        waterReedId = OptionalId("game:tallplant-coopersreed-water-normal-free");
        waterLilyId = OptionalId("game:waterlily");
        sedgeId = OptionalId("game:tallplant-brownsedge-land-normal-free");
        tuleId = OptionalId("game:tallplant-tule-land-normal-free");
        string[] woods = { "oak", "birch", "maple" };
        for (int w = 0; w < woods.Length; w++)
        {
            treeLogIds[w] = GameId($"game:log-grown-{woods[w]}-ud", "game:log-grown-oak-ud", "game:log-placed-oak-ud");
            for (int k = 0; k < 8; k++)
                treeLeafIds[w, k] = GameId($"game:leaves-grown{(k == 0 ? "" : k.ToString())}-{woods[w]}", "game:leaves-grown-oak", "game:leaves-placed-oak");
        }
    }

    /// <summary>The ones of several vanilla blocks that exist (a warning for any that don't; tall grass if none do).</summary>
    private int[] VegIds(params string[] codes)
    {
        var ids = new List<int>();
        foreach (string code in codes)
        {
            int id = OptionalId(code);
            if (id != 0) ids.Add(id);
            else api.Logger.Warning("[backrooms] Vegetation: no block {0}", code);
        }
        if (ids.Count == 0) ids.Add(grassIds[3]);
        return ids.ToArray();
    }

    private static bool IsVegetationLevel(int level) => level is 9 or 10 or 11 or WorldLayout.Motion;

    // ---- One column's plants, worked out once (the column builders ask for every height in turn) ----

    private struct VegColumn
    {
        public WorldGenerator Owner;
        public int Gx, Gz;
        public TileKind Kind;
        public ushort Variant;
        /// <summary>A trunk on this column: logs from 1 up to here (0: no trunk).</summary>
        public int LogTop;
        /// <summary>The crown over this column: bit r set, leaves r above the trunk's own ground.</summary>
        public uint LeafMask;
        /// <summary>Added to a height above this column's ground to give the height above the trunk's (Level 94's hills).</summary>
        public int Shift;
        public int LogId, LeafId;
        /// <summary>What grows on the ground (height 1): a block, 0 for nothing, -1 to leave it to the tile's prop.</summary>
        public int Ground;
        /// <summary>Level 10's ponds: shallows with reeds standing in them, and lilies on the open water.</summary>
        public bool Shallows, Lily;
    }

    [ThreadStatic] private static VegColumn vegColumn;

    private ref VegColumn Veg(in Tile t, int gx, int gz)
    {
        ref VegColumn c = ref vegColumn;
        if (c.Owner == this && c.Gx == gx && c.Gz == gz && c.Kind == t.Kind && c.Variant == t.Variant) return ref c;
        c = default;
        c.Owner = this;
        c.Gx = gx;
        c.Gz = gz;
        c.Kind = t.Kind;
        c.Variant = t.Variant;
        c.Ground = -1;
        ComputeVeg(ref c, t, gx, gz);
        return ref c;
    }

    /// <summary>The layout tile at a position, from the cell cache.</summary>
    private Tile VegTile(int gx, int gz)
    {
        const int size = WorldLayout.MacroSize;
        return Macro(Hashing.FloorDiv(gx, size), Hashing.FloorDiv(gz, size))[WorldLayout.TileIndex(Hashing.Mod(gx, size), Hashing.Mod(gz, size))];
    }

    /// <summary>A tree whose crown spreads two blocks: over grass. Over pavement and plazas, one.</summary>
    private static bool BigCrown(in Tile trunk) => trunk.Floor is FloorKind.Lawn or FloorKind.Grass or FloorKind.TurfLight or FloorKind.TurfDark;

    private static bool CrownAllowed(in Tile t)
    {
        if (t.Roof != 0) return false;
        if (t.Kind == TileKind.Bars) return true;
        if (t.Kind == TileKind.Wall) return t.Pattern == WallPattern.Hedge;
        if (t.Kind != TileKind.Floor || t.Overhead is not (0 or Overheads.Leaves) || t.SupplyBox) return false;
        return t.Variant is 0 or Props.Tree or Props.TallGrass or Props.Flowers or Props.Shrub or Props.Reeds or Props.BerryBush
            or Props.Crop or Props.Vegetable;
    }

    private void ComputeVeg(ref VegColumn c, in Tile t, int gx, int gz)
    {
        // What is round this column, two blocks out: the nearest trunk, and the things grass grows long beside
        int best = int.MaxValue, tdx = 0, tdz = 0;
        Tile trunk = default;
        bool fence = false, door = false, road = false, field = false, backdrop = false, tower = false, hedge = false, tracks = false, shore = false;
        for (int dz = -2; dz <= 2; dz++)
        {
            for (int dx = -2; dx <= 2; dx++)
            {
                Tile n = dx == 0 && dz == 0 ? t : VegTile(gx + dx, gz + dz);
                int d = Math.Max(Math.Abs(dx), Math.Abs(dz));
                if (n.Variant == Props.Tree && n.Kind == TileKind.Floor && n.Level == t.Level && (d <= 1 || BigCrown(n)))
                {
                    int score = d * 16 + dx * dx + dz * dz;
                    if (score < best) { best = score; trunk = n; tdx = dx; tdz = dz; }
                }
                if (d <= 1)
                {
                    if (n.Kind is TileKind.Door or TileKind.Doorway) door = true;
                    if (n.Kind == TileKind.Bars) fence = true;
                    if (n.Kind == TileKind.Wall && n.Pattern == WallPattern.Hedge) hedge = true;
                    if (n.Variant == Props.WaterTower) tower = true;
                    if (n.Floor == FloorKind.DirtTracks) tracks = true;
                    if (dx * dz == 0 && d == 1 && n.Kind != TileKind.Water) shore = true;
                }
                if (n.Floor is FloorKind.MotionKerb or FloorKind.MotionAsphalt) road = true;
                if (n.Floor == FloorKind.Field && n.Kind == TileKind.Floor) field = true;
                if (n.Kind == TileKind.Wall && n.Pattern == WallPattern.Backdrop) backdrop = true;
            }
        }

        // The tree, if this column is under one
        bool shade = false;
        if (best != int.MaxValue && CrownAllowed(t))
        {
            int tx = gx + tdx, tz = gz + tdz;
            bool big = BigCrown(trunk);
            ulong th = Hashing.Hash(seed, tx, tz, SaltVegTree);
            int top = TreeTrunk + (big ? (int)(th % 3) : 0);
            double species = Hashing.Unit(Hashing.Mix(th));
            int wood = species < 0.55 ? 0 : species < 0.8 ? 1 : 2;
            c.LogId = treeLogIds[wood];
            c.LeafId = treeLeafIds[wood, (int)((th >> 40) % 8)];
            c.Shift = t.Level == WorldLayout.Motion ? t.Height - trunk.Height : 0;
            if (tdx == 0 && tdz == 0) c.LogTop = top;
            c.LeafMask = CrownMask(-tdx, -tdz, top, big, tx, tz);
            shade = big && (tdx != 0 || tdz != 0);
        }

        // Level 10's ponds
        if (t.Kind == TileKind.Water)
        {
            if (t.Level != 10 || t.Under != 0) return;
            double roll = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltVegPond));
            c.Shallows = shore && t.Depth == 2 && roll < 0.6 && waterReedId != 0;
            c.Lily = !shore && t.Depth >= 2 && waterLilyId != 0 && Noise2(gx / 5.0, gz / 5.0, SaltVegPond + 1) > 0.2 && roll < 0.3;
            return;
        }

        if (t.Kind != TileKind.Floor || t.Variant == Props.Tree || door) return;
        c.Ground = GroundCover(t, gx, gz, shade, fence, road, field, backdrop, tower, hedge, tracks);
    }

    /// <summary>
    /// Which blocks of a crown lie over a column (dx, dz) from its trunk, as a mask of heights above the trunk's ground.
    /// A big crown is five across with its corners cut, two layers deep round the top of the trunk, a skirt under it
    /// on the taller trees, three across and then a cross over it, each edge block trimmed now and then; a small one
    /// (over pavement) is three across.
    /// </summary>
    private uint CrownMask(int dx, int dz, int top, bool big, int tx, int tz)
    {
        int ax = Math.Abs(dx), az = Math.Abs(dz), d = Math.Max(ax, az), m = ax + az;
        uint mask = 0;
        void Set(int r) { if (r >= 1 && r < 32) mask |= 1u << r; }
        double U(int layer) => Hashing.Unit(Hashing.Hash(seed, tx * 5 + dx, tz * 5 + dz, SaltVegCrown + (ulong)layer));
        if (!big)
        {
            if (d > 1) return 0;
            if (d == 0) { Set(top + 1); Set(top + 2); return mask; }
            Set(top);
            Set(top + 1);
            if (m == 1) Set(top + 2);
            return mask;
        }
        if (d == 0)
        {
            for (int r = top + 1; r <= top + 3; r++) Set(r);
            return mask;
        }
        if (d == 1 && top >= 5 && (m == 1 || U(0) < 0.5)) Set(top - 1);
        for (int layer = 0; layer <= 1; layer++)
            if (!(ax == 2 && az == 2) && !(m == 3 && U(1 + layer) < 0.3)) Set(top + layer);
        if (d == 1 && (m == 1 || U(3) < 0.6) || d == 2 && m == 2 && U(3) < 0.25) Set(top + 2);
        if (m == 1 && U(4) < 0.6) Set(top + 3);
        return mask;
    }

    /// <summary>A trunk, a crown, or what grows on the ground, for a column of an open-sky level; -1 to leave the column to its tile.</summary>
    private int Vegetation(in Tile t, int gx, int gz, int rel)
    {
        ref VegColumn c = ref Veg(t, gx, gz);
        int r = rel + c.Shift;
        bool leaves = r >= 1 && r < 32 && (c.LeafMask >> r & 1) != 0;
        if (c.LogTop > 0) return r >= 1 && r <= c.LogTop ? c.LogId : leaves ? c.LeafId : 0;
        if (leaves) return c.LeafId;
        if (rel == 1 && c.Ground >= 0) return c.Ground;
        // (The layout's own three-by-three crowns are drawn above instead)
        if (t.Overhead == Overheads.Leaves && rel >= 2 && t.Variant != Props.HayBale) return 0;
        return -1;
    }

    /// <summary>Leaves of a crown over a fence or a hedge (which draw their own lowest blocks), or air.</summary>
    private int CrownOver(in Tile t, int gx, int gz, int rel)
    {
        if (!IsVegetationLevel(t.Level) || rel < 2) return 0;
        ref VegColumn c = ref Veg(t, gx, gz);
        int r = rel + c.Shift;
        return r >= 1 && r < 32 && (c.LeafMask >> r & 1) != 0 ? c.LeafId : 0;
    }

    /// <summary>Grass (or nothing) under a Level 94 water tower, between its legs.</summary>
    private int UnderTowerGrass(in Tile t, int gx, int gz)
    {
        int du = t.Stack % 5 - 2, dv = t.Stack / 5 - 2;
        if (Math.Abs(du) == 2 && Math.Abs(dv) == 2 || du == 0 && dv == 0) return 0;
        return GrassAt(gx, gz, 0.6, 1, 3);
    }

    /// <summary>
    /// Level 10's ponds: reeds standing in the shallows round the edge (a block of water over the mud), lilies out on
    /// the open water. -1 to leave the block to the pond.
    /// </summary>
    private int PondVegetation(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (t.Level != 10 || t.Under != 0 || rel < -1 || rel > 1) return -1;
        ref VegColumn c = ref Veg(t, gx, gz);
        if (c.Shallows && rel <= 0)
        {
            if (rel == -1) return lakeBedId;
            fluid = waterId;
            return waterReedId;
        }
        return rel == 1 && c.Lily ? waterLilyId : -1;
    }

    // ---- Ground cover, level by level ----

    private int GroundCover(in Tile t, int gx, int gz, bool shade, bool fence, bool road, bool field, bool backdrop, bool tower, bool hedge, bool tracks)
    {
        if (t.SupplyBox || t.Stair != 0 || t.Roof != 0 || t.Overhead is not (0 or Overheads.Leaves)) return -1;
        bool plain = t.Variant == 0;
        double roll = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltVegKind));
        switch (t.Level)
        {
            case 9:
            {
                if (t.Under != 0 || t.Floor != FloorKind.Lawn) return -1;
                if (t.Variant == Props.TallGrass) return grassIds[GrassHeight(gx, gz, fence ? 4 : 3, 5)];
                if (!plain) return -1;
                // The Suburbs have not been mown in a long time: short at the front, long behind, longest along the fences
                var (v, house) = layout.SuburbLotDepth(gx, gz);
                if (shade) return roll < 0.2 ? Pick(fernIds, gx, gz) : roll < 0.23 && looseStickId != 0 ? looseStickId : GrassAt(gx, gz, 0.25, 0, 2);
                if (fence) return roll < 0.08 ? Pick(weedIds, gx, gz) : GrassAt(gx, gz, 0.7, 4, 5);
                if (!house) return roll < 0.05 ? Pick(weedIds, gx, gz) : GrassAt(gx, gz, 0.5, 3, 4);
                if (v <= 0) return GrassAt(gx, gz, 0.35, 1, 3);
                if (v < 6) return GrassAt(gx, gz, 0.15, 0, 1);
                if (v < 18) return GrassAt(gx, gz, 0.25, 1, 2);
                return roll < 0.04 ? Pick(weedIds, gx, gz) : GrassAt(gx, gz, 0.45, 2, 4);
            }
            case 10:
            {
                if (t.Zone != 0 || t.Floor != FloorKind.Grass) return -1;
                // The bank round a pond: sedge and tule among the long grass (the reeds there are the layout's)
                if (t.Under == Unders.LakeRim)
                {
                    if (!plain) return -1;
                    return roll < 0.12 && sedgeId != 0 ? sedgeId : roll < 0.2 && tuleId != 0 ? tuleId : GrassAt(gx, gz, 0.4, 2, 4);
                }
                if (t.Under != 0) return -1;
                bool margin = field || hedge;
                if (t.Variant == Props.TallGrass)
                    return grassIds[margin ? GrassHeight(gx, gz, 4, 5) : layout.IsPasture(gx, gz) ? GrassHeight(gx, gz, 1, 2) : GrassHeight(gx, gz, 2, 5)];
                if (!plain) return -1;
                if (shade) return roll < 0.08 ? Pick(fernIds, gx, gz) : GrassAt(gx, gz, 0.35, 2, 4);
                if (tracks) return GrassAt(gx, gz, 0.4, 0, 1);
                // Poppies, cornflowers and lupins along the edges of the fields
                if (margin) return roll < 0.14 ? Pick(marginFlowerIds, gx, gz) : GrassAt(gx, gz, 0.5, 3, 5);
                if (layout.IsPasture(gx, gz)) return GrassAt(gx, gz, 0.45, 0, 1);
                return GrassAt(gx, gz, 0.3, 1, 3);
            }
            case 11:
            {
                if (t.Under != 0 || t.Floor != FloorKind.Lawn || !plain) return -1;
                if (shade) return roll < 0.18 ? Pick(fernIds, gx, gz) : roll < 0.2 && looseStickId != 0 ? looseStickId : GrassAt(gx, gz, 0.25, 0, 2);
                if (fence) return GrassAt(gx, gz, 0.5, 2, 3);
                return GrassAt(gx, gz, 0.3, 0, 2);
            }
            case WorldLayout.Motion:
            {
                if (t.Under != 0 || t.Zone != 0) return -1;
                // The front yards' beds, in the saturated colours of an old picture
                if (t.Variant == Props.Flowers) return Pick(brightFlowerIds, gx, gz, t.Stack);
                if (!plain || t.Floor is not (FloorKind.TurfLight or FloorKind.TurfDark)) return -1;
                // Long grass and flowers where the mower doesn't reach: the verges, the fences, the foot of the backdrop,
                // round the water towers
                if (road && t.Height == 0 || fence || backdrop || tower)
                    return roll < 0.12 ? Pick(brightFlowerIds, gx, gz) : GrassAt(gx, gz, 0.75, 2, 4);
                if (shade) return GrassAt(gx, gz, 0.5, 1, 2);
                // Otherwise the stripes it is mown in: longer on the dark ones
                return t.Floor == FloorKind.TurfDark ? GrassAt(gx, gz, 0.65, 0, 2) : GrassAt(gx, gz, 0.35, 0, 1);
            }
        }
        return -1;
    }

    /// <summary>Tall grass on a share of the tiles (in patches), its height between two of the six, varying smoothly.</summary>
    private int GrassAt(int gx, int gz, double cover, int lo, int hi)
    {
        double patch = Noise2(gx / 9.0, gz / 9.0, SaltVegPatch) * 0.5 + 0.5;
        if (Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltVegCover)) >= cover * (0.5 + patch)) return 0;
        return grassIds[GrassHeight(gx, gz, lo, hi)];
    }

    private int GrassHeight(int gx, int gz, int lo, int hi)
    {
        double n = Noise2(gx / 6.0, gz / 6.0, SaltVegHeight) * 0.5 + 0.5;
        double jitter = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltVegJitter)) - 0.5;
        return Math.Clamp(lo + (int)Math.Floor((n + 0.4 * jitter) * (hi - lo + 1)), lo, hi);
    }

    private int Pick(int[] ids, int gx, int gz, int extra = 0) =>
        ids[(int)((Hashing.Hash(seed, gx, gz, SaltVegPick) + (ulong)extra) % (ulong)ids.Length)];
}
