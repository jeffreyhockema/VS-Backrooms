using System;
using Cave = Backrooms.Worldgen.WorldLayout.L23Cavern;
using CaveKind = Backrooms.Worldgen.WorldLayout.L23CaveKind;
using Ruin = Backrooms.Worldgen.WorldLayout.L23RuinKind;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 23, "The Petrified Garden" (experimental, kept as level 28), laid out in WorldLayout.Level23.cs, from its
/// own floor (<see cref="WorldGeometry.FloorFor"/>, ten below the shared one), up to the top of the world. Each column is
/// worked out whole, once (<see cref="L23ColumnOf"/>), from the layout's functions:
/// <list type="bullet">
/// <item>the forest floor: humus, moss and leaf litter over dark earth, the ground under it a mass of earth and petrified
/// roots; under the holes in the lid, grass and flowers;</item>
/// <item>the trees: petrified bark of four kinds (grey, redwood red, pale oak, dark cypress), roots and arches of root wood,
/// the Green Giants' green bark; ferns, mushrooms and fallen sticks at their feet, now and then a buried sentry's face;</item>
/// <item>the lid: loose leaves hanging down from 33-41, dense leaves from 41 to the top of the world (they take the sun's
/// light to about six on the forest floor), lichen hanging from it; open where the star shines through;</item>
/// <item>the glow rooms: moss floors with puddles, little petrified trees, glowcaps, mushrooms and ferns, Gardener's
/// Sorries and lichen hanging from the ceiling, pillars where a trunk comes down through; root tunnels up to the forest;</item>
/// <item>the four ruins, Base Seedling's camp (its hollow tree, tents, lanterns, a spring), the Heart of Water's pool;</item>
/// <item>the tangle round the forest: fused roots and bark to the lid.</item>
/// </list>
/// This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private const ulong SaltL23Deco = 0x2840, SaltL23Mat = 0x2841, SaltL23Pot = 0x2843;

    /// <summary>The lowest height of a column that is worked out (the band's bottom), and how many heights there are up to the top of the world.</summary>
    private const int L23Low = -20, L23Height = WorldLayout.L23Top - L23Low + 1;

    private int l23Humus, l23Moss, l23Litter, l23Earth, l23RootEarth, l23Tangle, l23Root, l23Leaves, l23LeavesDense, l23RuinStone, l23RuinMoss,
        l23Plaque, l23Sand, l23Gravel, l23Lantern, l23Table, l23Stick, l23TallGrass, l23ShortGrass, l23Flower;
    /// <summary>The block of each kind of wood (<see cref="WorldLayout.L23Wood"/>'s kinds: the barks, root, aspen, boulder, stone mushroom, fallen logs).</summary>
    private readonly int[] l23Bark = new int[WorldLayout.L23KindLimit];
    // Round 3: the forest floor's undergrowth of stone, the bracket fungi, the glowing bushes, the ruins' frescoes and rags, the
    // sentries' bodies, the M.E.G.'s signs and Base Seedling's things
    private readonly int[] l23StonePlant = new int[4];
    private readonly int[] l23Bracket = new int[4];
    private readonly int[] l23Glowbush = new int[4];
    private readonly int[] l23Fresco = new int[4];
    private readonly int[] l23SentryBody = new int[4];
    private readonly int[] l23Bedroll = new int[4];
    private readonly System.Collections.Generic.Dictionary<string, int[]> l23Signs = new();
    private int l23SignPost, l23Barrel, l23Crate, l23FireRing, l23Ledger, l23Cloth, l23Flagstone, l23MossBark, l23Bones;
    private readonly int[] l23SquirtRack = new int[4];
    private int[] l23Flowers;
    private readonly int[] l23Sentry = new int[4];
    private readonly int[] l23Latin = new int[4];
    private readonly int[] l23Pottery = new int[2];
    /// <summary>Glowcaps and Sorries by colour (1 teal, 2 violet, 3 amber; 0 green, the Sorries only).</summary>
    private readonly int[] l23Glowcap = new int[4], l23Sorry = new int[4];
    private int[] l23Ferns, l23Mushrooms, l23Toadstools;
    private readonly int[] l23Lichen = new int[3];

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL23()
    {
        string[] barks = { null, "grey", "red", "pale", "dark", "green" };
        for (int k = 1; k <= 5; k++) l23Bark[k] = Id("l23-bark-" + barks[k]);
        l23Root = Id("l23-root");
        l23Bark[WorldLayout.L23RootWood] = l23Root;
        l23Bark[WorldLayout.L23BarkAspen] = Id("l23-bark-aspen");
        l23Bark[WorldLayout.L23Boulder] = Id("l23-boulder");
        l23Bark[WorldLayout.L23MushStem] = Id("l23-mushstem");
        l23Bark[WorldLayout.L23MushCap] = Id("l23-mushcap");
        foreach (byte bark in new[] { WorldLayout.L23BarkGrey, WorldLayout.L23BarkRed, WorldLayout.L23BarkPale, WorldLayout.L23BarkDark, WorldLayout.L23BarkAspen })
        {
            string name = bark == WorldLayout.L23BarkAspen ? "aspen" : barks[bark];
            l23Bark[WorldLayout.L23LogKind(bark, false)] = Id($"l23-log-{name}-x");
            l23Bark[WorldLayout.L23LogKind(bark, true)] = Id($"l23-log-{name}-z");
        }
        string[] plants = { "shrub", "sapling", "fern", "stump" };
        for (int k = 0; k < 4; k++) l23StonePlant[k] = Id("l23-stoneplant-" + plants[k]);
        for (int f = 0; f < 4; f++)
        {
            l23Bracket[f] = Id("l23-bracket-" + Sides[f]);
            l23Fresco[f] = Id("l23-fresco-" + Sides[f]);
            l23SentryBody[f] = Id("l23-sentrybody-" + Sides[f]);
            l23Bedroll[f] = Id("l23-campbed-" + Sides[f]); // (round 4: the bedroll rebuilt; l23-bedroll stays registered)
        }
        foreach (string text in new[] { "camp-a", "camp-b", "camp-c", "rules-a", "rules-b", "trail", "giants-a", "giants-b", "dontsay" })
        {
            var ids = new int[4];
            for (int f = 0; f < 4; f++) ids[f] = Id($"l23-sign-{text}-{Sides[f]}");
            l23Signs[text] = ids;
        }
        l23SignPost = Id("l23-signpost");
        // (Round 4: Base Seedling's things rebuilt to the asset bar, tools/gen_23_r4_camp.py; round 3's blocks stay registered)
        l23Barrel = Id("l23-campbarrel");
        l23Crate = Id("l23-campcrate");
        l23FireRing = Id("l23-campfire");
        l23Ledger = Id("l23-ledger");
        l23Cloth = Id("l23-cloth");
        l23Flagstone = Id("l23-flagstone");
        l23MossBark = Id("l23-mossbark");
        l23Bones = OptionalId("bonepile");
        for (int f = 0; f < 4; f++) l23SquirtRack[f] = Id("l23-squirtrack-" + Sides[f]);
        l23Humus = Id("l23-humus");
        l23Moss = Id("l23-moss");
        l23Litter = Id("l23-litter");
        l23Earth = Id("l23-earth");
        l23RootEarth = Id("l23-rootearth");
        l23Tangle = Id("l23-tangle");
        l23Leaves = Id("l23-leaves");
        l23LeavesDense = Id("l23-leaves-dense");
        l23RuinStone = Id("l23-ruinstone");
        l23RuinMoss = Id("l23-ruinmoss");
        l23Plaque = Id("l23-plaque");
        // (Round 4: the faces sculpted, l23-sentryface; round 1's l23-sentry stays registered, and L23Sentries finds both by their code's start)
        for (int f = 0; f < 4; f++) l23Sentry[f] = Id("l23-sentryface-grey-" + Sides[f]);
        string[] latin = { "a", "b", "c", "d" };
        for (int k = 0; k < 4; k++) l23Latin[k] = Id("l23-latin-" + latin[k]);
        l23Pottery[0] = Id("l23-pottery-amphora");
        l23Pottery[1] = Id("l23-pottery-shards");
        string[] colours = { "green", "teal", "violet", "amber" };
        for (int c = 0; c < 4; c++)
        {
            l23Sorry[c] = Id("l23-sorry-" + colours[c]);
            l23Glowcap[c] = c == 0 ? 0 : Id("l23-glowcap-" + colours[c]);
            l23Glowbush[c] = c == 0 ? 0 : Id("l23-glowbush-" + colours[c]);
        }
        l23Sand = GameId("game:sand-granite", "game:sand-basalt");
        l23Gravel = GameId("game:gravel-granite", "game:gravel-basalt");
        // (Round 3, the balance review: the level's own lantern, not the vanilla one a player could pick up for free light;
        // it gives the same light and breaks to nothing)
        l23Lantern = Id("l23-camplamp");
        l23Table = OptionalId("game:table-normal");
        l23Stick = OptionalId("game:loosestick-free");
        l23TallGrass = GameId("game:tallgrass-medium-free", "game:tallgrass-short-free");
        l23ShortGrass = GameId("game:tallgrass-veryshort-free", "game:tallgrass-short-free");
        l23Flower = OptionalId("game:flower-wilddaisy-free");
        l23Flowers = VegIds("game:flower-wilddaisy-free", "game:flower-cornflower-free", "game:flower-forgetmenot-free", "game:flower-goldenpoppy-free",
            "game:flower-lilyofthevalley-free");
        l23Ferns = VegIds("game:fern-eaglefern", "game:fern-hartstongue", "game:fern-cinnamonfern", "game:tallfern");
        l23Mushrooms = VegIds("game:mushroom-fieldmushroom-normal", "game:mushroom-bolete-normal", "game:mushroom-chanterelle-normal",
            "game:mushroom-orangeoakbolete-normal");
        l23Toadstools = VegIds("game:mushroom-flyagaric-normal", "game:mushroom-earthball-normal");
        string[] lichenParts = { "top", "segment", "bottom" };
        for (int p = 0; p < 3; p++) l23Lichen[p] = OptionalId("game:hanginglichen-oldmans-" + lichenParts[p]);
        floorIds[(int)FloorKind.L23Floor] = l23Humus;
        floorIds[(int)FloorKind.L23Moss] = l23Moss;
        floorIds[(int)FloorKind.L23Earth] = l23Earth;
        floorIds[(int)FloorKind.L23Bark] = l23Bark[WorldLayout.L23BarkGrey];
        floorIds[(int)FloorKind.L23Water] = l23Gravel;
        InitL23Skin();
    }

    /// <summary>One column of the level, worked out whole: its block and fluid at every height from <see cref="L23Low"/> up.</summary>
    private sealed class L23Column
    {
        public WorldGenerator Owner;
        public int Gx, Gz;
        public Tile Tile;
        public readonly int[] Blocks = new int[L23Height];
        public readonly bool[] Water = new bool[L23Height];
        public readonly byte[] Wood = new byte[L23Height];
    }

    [ThreadStatic] private static L23Column l23Column;

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level23Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < L23Low) return concreteId; // (the ground below, as vanilla laid it)
        if (rel > WorldLayout.L23Top) return 0;
        L23Column c = L23ColumnOf(t, gx, gz);
        int i = rel - L23Low;
        if (c.Water[i]) fluid = waterId;
        return c.Blocks[i];
    }

    private L23Column L23ColumnOf(in Tile t, int gx, int gz)
    {
        var c = l23Column ??= new L23Column();
        if (c.Owner == this && c.Gx == gx && c.Gz == gz && c.Tile.Variant == t.Variant && c.Tile.SupplyBox == t.SupplyBox && c.Tile.Looted == t.Looted
            && c.Tile.Zone == t.Zone) return c;
        c.Owner = null;
        c.Gx = gx;
        c.Gz = gz;
        c.Tile = t;
        Array.Clear(c.Water);
        if (t.Zone == WorldLayout.L23RimZone) L23Tangle(c, gx, gz);
        else L23Forest(c, t, gx, gz);
        c.Owner = this;
        return c;
    }

    private ulong L23Hash(int gx, int gz, int k) => Hashing.Hash(seed, gx, gz, SaltL23Deco + (ulong)k * 0x100);

    private double L23Unit(int gx, int gz, int k) => Hashing.Unit(L23Hash(gx, gz, k));

    /// <summary>The tangle round the forest: fused roots and dark bark up to the lid, the lid's dense leaves over it.</summary>
    private void L23Tangle(L23Column c, int gx, int gz)
    {
        for (int rel = L23Low; rel <= WorldLayout.L23Top; rel++)
        {
            int i = rel - L23Low;
            if (rel >= WorldLayout.L23LidDense) c.Blocks[i] = l23LeavesDense;
            else
            {
                double u = Hashing.Unit(Hashing.Hash(seed, gx * 64 + rel, gz, SaltL23Mat));
                c.Blocks[i] = u < 0.25 ? l23Bark[WorldLayout.L23BarkDark] : u < 0.4 ? l23Root : l23Tangle;
            }
        }
    }

    /// <summary>The forest's column: ground, wood, lid, caverns and tunnels, then what grows and stands in them.</summary>
    private void L23Forest(L23Column c, in Tile t, int gx, int gz)
    {
        int[] b = c.Blocks;
        int ground = layout.L23Ground(gx, gz);
        double fromMid = layout.L23FromMid(gx, gz);
        bool core = fromMid < WorldLayout.L23CoreRadius;
        bool hole = layout.L23Hole(gx, gz);

        // ---- The ground: its top, dark earth under it, then earth and roots all the way down ----
        int top = L23GroundTop(gx, gz, ground, hole, core, fromMid);
        for (int rel = L23Low; rel <= WorldLayout.L23Top; rel++)
        {
            int i = rel - L23Low;
            if (rel > ground) b[i] = 0;
            else if (rel == ground) b[i] = top;
            else if (rel >= ground - 3) b[i] = l23Earth;
            else b[i] = L23Deep(gx, gz, rel);
        }
        // The Heart of Water's pool
        if (core && ground < WorldLayout.L23PoolSurface)
        {
            for (int rel = ground + 1; rel <= WorldLayout.L23PoolSurface; rel++) c.Water[rel - L23Low] = true;
            // (Round 4: lily pads on the shallows, over the water)
            if (ground >= WorldLayout.L23PoolSurface - 4 && L23Unit(gx, gz, 41) < 0.2 && Noise2(gx / 5.0, gz / 5.0, SaltL23Mat + 17) > 0.1)
                b[WorldLayout.L23PoolSurface + 1 - L23Low] = l23LilyPad;
            // (Round 3: mossy stones in the shallows round the edge, a few standing out of the water)
            if (ground >= WorldLayout.L23PoolSurface - 3 && Noise2(gx / 3.0, gz / 3.0, SaltL23Mat + 16) > 0.55)
                for (int rel = ground + 1; rel <= WorldLayout.L23PoolSurface + 1; rel++)
                {
                    b[rel - L23Low] = l23Bark[WorldLayout.L23Boulder];
                    c.Water[rel - L23Low] = false;
                }
        }

        // ---- The wood: trunks, buttresses, roots, arches, limbs ----
        layout.L23Wood(gx, gz, L23Low, c.Wood);
        for (int i = 0; i < L23Height; i++)
        {
            byte w = c.Wood[i];
            if (w == 0) continue;
            int rel = i + L23Low;
            // (Below the ground a root only shows as root where it is near the top: deeper, the ground's own mass of roots)
            if (rel < ground - 2 && w == WorldLayout.L23RootWood) continue;
            b[i] = l23Bark[w];
            c.Water[i] = false;
        }
        // Round 3: moss grown up over the trunks' feet (a block or two over the ground, in patches) and over the tops of
        // the roots crawling out from them
        if (!core && ground >= 0)
        {
            int band = ground + (Noise2(gx / 7.0, gz / 7.0, SaltL23Mat + 15) > 0 ? 2 : 1);
            for (int rel = ground + 1; rel <= band && rel - L23Low < L23Height; rel++)
            {
                byte w = c.Wood[rel - L23Low];
                if (w is >= WorldLayout.L23BarkGrey and <= WorldLayout.L23BarkDark or WorldLayout.L23BarkAspen) b[rel - L23Low] = l23MossBark;
            }
            for (int rel = ground + 1; rel <= ground + 3 && rel + 1 - L23Low < L23Height; rel++)
                if (c.Wood[rel - L23Low] == WorldLayout.L23RootWood && c.Wood[rel + 1 - L23Low] == 0 && L23Unit(gx, gz, 27) < 0.6) b[rel - L23Low] = l23MossBark;
        }
        // A hollow trunk's floor (inside it and in its mouth): leaf litter and humus blown in, not the cut end of its bark
        if (t.Under == Unders.L23HollowTrunk && ground >= L23Low) b[ground - L23Low] = L23Unit(gx, gz, 21) < 0.55 ? l23Litter : l23Humus;
        // A buried sentry's face, between two buttresses at head height
        for (int rel = ground; rel <= ground + 5; rel++)
        {
            if (layout.L23SentryAt(gx, gz, rel, out ArchPier facing) && b[rel - L23Low] != 0) b[rel - L23Low] = l23Sentry[Facing(facing)];
            // (Round 3: under the face, its body pushed out of the bark, so it reads as someone trapped there)
            if (rel > ground && layout.L23SentryBodyAt(gx, gz, rel, out ArchPier bodyFacing) && b[rel - L23Low] != 0) b[rel - L23Low] = l23SentryBody[Facing(bodyFacing)];
        }
        // Round 3: bracket fungi up the trunks' sides
        if (!core && layout.L23BracketAt(gx, gz, out int brRel, out ArchPier brFacing) && brRel > ground && brRel - L23Low < L23Height && b[brRel - L23Low] == 0)
            b[brRel - L23Low] = l23Bracket[Facing(brFacing)];
        // Round 4: the trunks' outer bark in relief, the logs', caps' and boulders' rounded pieces (WorldGenerator.L23.Skin.cs)
        L23DressWood(c, gx, gz, ground);

        // ---- The lid ----
        int lidBottom = layout.L23LidBottom(gx, gz), denseFrom = layout.L23DenseFrom(gx, gz);
        if (!hole)
            for (int rel = lidBottom; rel <= WorldLayout.L23Top; rel++)
            {
                int i = rel - L23Low;
                if (b[i] == 0) b[i] = rel >= denseFrom ? l23LeavesDense : l23Leaves;
            }
        // Round 4: shafts of light under the holes in the lid, a slice a block from high up down to a few over the ground, in
        // a scatter of the hole's columns (the lore's star never moves: they stand still)
        if (hole && (L23Mod(gx * 7 + gz * 13, 6) == 0) && l23Sunbeam != 0)
            for (int rel = Math.Max(ground, WorldLayout.L23PoolSurface) + 4; rel <= WorldLayout.L23Top - 4; rel++)
                if (b[rel - L23Low] == 0 && !c.Water[rel - L23Low]) b[rel - L23Low] = l23Sunbeam;
        // Lichen hanging from the lid, now and then; long roots from the vault over the pool
        if (!hole && b[lidBottom - 1 - L23Low] == 0)
        {
            double u = L23Unit(gx, gz, 1);
            if (core && u < 0.012) L23Hang(b, lidBottom - 1, 6 + (int)(L23Hash(gx, gz, 2) % 10), ground, root: true);
            else if (u < 0.03) L23Hang(b, lidBottom - 1, 1 + (int)(L23Hash(gx, gz, 2) % 5), ground, root: false);
        }

        // ---- What grows on the forest floor (before the caverns cut into it) ----
        if (!core && ground >= 0) L23Undergrowth(b, gx, gz, ground, hole);
        else if (core && ground >= WorldLayout.L23PoolSurface + 1 && b[ground + 1 - L23Low] == 0 && !layout.L23NearWarning(gx, gz))
        {
            double u = L23Unit(gx, gz, 3);
            if (u < 0.06) b[ground + 1 - L23Low] = l23Ferns[L23Hash(gx, gz, 4) % (ulong)l23Ferns.Length];
            else if (u < 0.2 && hole) b[ground + 1 - L23Low] = l23TallGrass;
        }

        // ---- The M.E.G.'s signs on the forest floor (round 3): a board on a post ----
        if (layout.L23Signs.TryGetValue((gx, gz), out WorldLayout.L23SignPart sign) && sign.Board - L23Low < L23Height)
        {
            for (int rel = ground + 1; rel < sign.Board; rel++) b[rel - L23Low] = l23SignPost;
            b[sign.Board - L23Low] = l23Signs[sign.Text][Facing(sign.Side)];
            c.Water[sign.Board - L23Low] = false;
        }

        // ---- A lost explorer's last camp (round 3, my invention): a bedroll, a crate at its foot, bones beside it ----
        if (!core && t.Zone == WorldLayout.L23Surface && ground >= 0 && b[ground + 1 - L23Low] == 0
            && layout.L23LostCampIn(Hashing.FloorDiv(gx, WorldLayout.MacroSize), Hashing.FloorDiv(gz, WorldLayout.MacroSize)) is { } lost)
        {
            var (lx, lz, head) = lost;
            var (hx, hz) = WorldLayout.L23Step(head);
            var (sx, sz) = WorldLayout.L23LeftOf(head);
            int at = ground + 1 - L23Low;
            if (gx == lx && gz == lz) b[at] = l23Bedroll[Facing(head)];
            else if (gx == lx - hx && gz == lz - hz) b[at] = l23Crate;
            else if (gx == lx + sx && gz == lz + sz && l23Bones != 0) b[at] = l23Bones;
        }

        // ---- The caverns ----
        int caveFloor = int.MinValue;
        Cave cave = default;
        if (layout.L23Cave(gx, gz, out int f, out int ceil, out cave))
        {
            caveFloor = f;
            L23Carve(c, gx, gz, f, ceil, cave);
        }
        // ---- The tunnels ----
        bool inTunnel = false;
        if (layout.L23Tunnel(gx, gz, out int tf, out int tc, out double off, out CaveKind tunnelTo))
        {
            if (off < 1)
            {
                inTunnel = true;
                for (int rel = tf + 1; rel < tc; rel++)
                {
                    int i = rel - L23Low;
                    if (rel <= ground || c.Wood[i] != 0 || b[i] == l23Sentry[0] || b[i] == l23Sentry[1] || b[i] == l23Sentry[2] || b[i] == l23Sentry[3]) b[i] = 0;
                    c.Water[i] = false;
                }
                // Its floor: trodden earth, a root across it now and then (a step)
                if (tf <= ground && caveFloor == int.MinValue) b[tf - L23Low] = L23Unit(gx, gz, 5) < 0.12 ? l23Root : l23Earth;
                // The M.E.G. light the ways down to Base Seedling: a lantern by the wall now and then (my invention)
                if (tunnelTo == CaveKind.Seedling && off > 0.7 && tf < ground && caveFloor == int.MinValue && L23Unit(gx, gz, 20) < 0.16 && b[tf - L23Low] != 0)
                    b[tf + 1 - L23Low] = l23Lantern;
                if (caveFloor == int.MinValue || tf < caveFloor) caveFloor = tf;
            }
            else
            {
                // Its walls and roof: roots laced through the earth
                for (int rel = tf; rel <= tc; rel++)
                {
                    int i = rel - L23Low;
                    if (rel <= ground - 1 && b[i] != 0 && L23Unit(gx, gz * 7 + rel, 6) < 0.55) b[i] = l23Root;
                }
                // (Round 3: on the ways down to the ruins, a stone set in the wall now and then with the Architects' hasty
                // Latin cut into it, at eye height: the lore's "hasty messages in Latin")
                if (tunnelTo == CaveKind.Ruin && off < 1.5 && tf + 2 <= ground - 1 && b[tf + 2 - L23Low] != 0 && L23Unit(gx, gz, 24) < 0.05)
                    b[tf + 2 - L23Low] = l23Latin[(int)(L23Hash(gx, gz, 25) % 4)];
            }
        }

        // Round 4: root flares at the trunks' feet, limbs out of their sides (WorldGenerator.L23.Skin.cs)
        if (!core || ground > WorldLayout.L23PoolSurface) L23DressAir(c, gx, gz, ground, inTunnel);

        // ---- What stands on the floor: Base Seedling's tents and stores, the supply boxes ----
        if (t.Variant != 0 || t.SupplyBox)
        {
            int at = (caveFloor != int.MinValue ? caveFloor : ground) + 1;
            if (at > L23Low && at <= WorldLayout.L23Top)
            {
                int thing = t.SupplyBox ? BoxOf(t) : PropBlock(t);
                // (Round 4: Base Seedling's tents are the M.E.G.'s wall tents of the level's own, on the same four tiles)
                if (!t.SupplyBox && t.Variant == Props.CampTent) thing = l23Tent[Math.Min((int)t.Stack, 3), Facing(propHeadFirst[t.Variant] ? Opposite(t.Pier) : t.Pier)];
                if (thing != 0)
                {
                    b[at - L23Low] = thing;
                    c.Water[at - L23Low] = false;
                }
            }
        }
    }

    /// <summary>The top of the ground: humus, moss in patches and under the holes, leaf litter in drifts; round the pool, gravel and sand.</summary>
    private int L23GroundTop(int gx, int gz, int ground, bool hole, bool core, double fromMid)
    {
        if (core)
        {
            // (The well at the bottom of the pool, where the reservoir goes on down: dark roots, no gravel)
            if (ground == WorldLayout.L23WellFloor) return l23Tangle;
            if (fromMid < WorldLayout.L23PoolRadius) return Noise2(gx / 6.0, gz / 6.0, SaltL23Mat + 1) > 0.1 ? l23Gravel : l23Sand;
            if (fromMid < WorldLayout.L23PoolRadius + 3) return l23Gravel;
            return Noise2(gx / 9.0, gz / 9.0, SaltL23Mat + 2) > -0.2 ? l23Moss : l23Humus;
        }
        // (Round 3: the M.E.G.'s trails out from Base Seedling's tunnels, trodden bare)
        if (layout.L23OnTrail(gx, gz)) return L23Unit(gx, gz, 26) < 0.25 ? l23Litter : l23Earth;
        if (hole) return l23Moss;
        double n = Noise2(gx / 13.0, gz / 13.0, SaltL23Mat + 3);
        if (n > 0.35) return l23Moss;
        if (n < -0.4) return l23Litter;
        return l23Humus;
    }

    /// <summary>The ground deep under the forest: dark earth laced with petrified roots, and the tangle's own mass of them in places.</summary>
    private int L23Deep(int gx, int gz, int rel)
    {
        double n = Noise2(gx / 9.0 + rel * 0.37, gz / 9.0 - rel * 0.21, SaltL23Mat + 4);
        return n > 0.45 ? l23Tangle : n > 0.05 ? l23RootEarth : l23Earth;
    }

    /// <summary>Hangs a strand of lichen (or of root) down from a height, as far as it can go with room under it.</summary>
    private void L23Hang(int[] b, int from, int length, int floor, bool root)
    {
        int lowest = Math.Max(floor + 3, from - length + 1);
        if (lowest > from) return;
        for (int rel = from; rel >= lowest; rel--)
        {
            int i = rel - L23Low;
            if (b[i] != 0) return;
            if (root) b[i] = l23Root;
            else b[i] = rel == from ? l23Lichen[0] : rel == lowest ? l23Lichen[2] : l23Lichen[1];
        }
    }

    /// <summary>Ferns and mushrooms at the trees' feet, fallen sticks; under the holes, grass and a few flowers.</summary>
    private void L23Undergrowth(int[] b, int gx, int gz, int ground, bool hole)
    {
        int i = ground + 1 - L23Low;
        if (b[i] != 0 || b[i - 1] == 0) return;
        double u = L23Unit(gx, gz, 7);
        ulong h = L23Hash(gx, gz, 8);
        if (hole)
        {
            // (A glade under one of the wide holes: flowers of several kinds, and the odd young tree of stone)
            bool glade = layout.L23InGlade(gx + 0.5, gz + 0.5, -1);
            if (u < 0.45) b[i] = l23TallGrass;
            else if (u < 0.6) b[i] = l23ShortGrass;
            else if (u < (glade ? 0.72 : 0.64) && l23Flowers.Length > 0) b[i] = glade ? l23Flowers[h % (ulong)l23Flowers.Length] : l23Flower != 0 ? l23Flower : l23ShortGrass;
            else if (u < (glade ? 0.76 : 0.72)) b[i] = l23Ferns[h % (ulong)l23Ferns.Length];
            else if (glade && u < 0.78) b[i] = l23StonePlant[1];
            return;
        }
        double patch = Noise2(gx / 10.0, gz / 10.0, SaltL23Mat + 5);
        // Round 3: the petrified undergrowth (shrubs, saplings, fern fronds, stumps) in patches of its own
        double stony = Noise2(gx / 12.0, gz / 12.0, SaltL23Mat + 14);
        double us = L23Unit(gx, gz, 22);
        if (stony > 0.1 && us < 0.07 + 0.12 * stony)
        {
            double pick = L23Unit(gx, gz, 23);
            b[i] = l23StonePlant[pick < 0.4 ? 0 : pick < 0.62 ? 2 : pick < 0.85 ? 1 : 3];
            return;
        }
        if (u < 0.035 + 0.06 * Math.Max(0, patch)) b[i] = l23Ferns[h % (ulong)l23Ferns.Length];
        else if (u < 0.05 + 0.06 * Math.Max(0, patch)) b[i] = l23Mushrooms[h % (ulong)l23Mushrooms.Length];
        else if (u < 0.053 + 0.06 * Math.Max(0, patch)) b[i] = l23Toadstools[h % (ulong)l23Toadstools.Length];
        else if (u < 0.068 + 0.06 * Math.Max(0, patch) && l23Stick != 0) b[i] = l23Stick;
    }

    /// <summary>
    /// A cavern's column: air from its floor to its ceiling (a trunk coming down through it left standing as a pillar),
    /// moss and earth underfoot with puddles, roots in the roof; then what is in it (<see cref="L23CaveThings"/>).
    /// </summary>
    private void L23Carve(L23Column c, int gx, int gz, int floor, int ceiling, in Cave cave)
    {
        int[] b = c.Blocks;
        byte pillar = layout.L23PillarAt(gx, gz);
        bool flat = cave.Kind != CaveKind.Glow;
        for (int rel = floor + 1; rel < ceiling; rel++)
        {
            int i = rel - L23Low;
            b[i] = pillar != 0 && cave.Kind == CaveKind.Glow ? l23Bark[pillar] : 0;
            c.Water[i] = false;
        }
        // The floor: moss over earth; a puddle in the hollows of the glow rooms; the ruins' plaza paved
        int fi = floor - L23Low;
        double dx = gx + 0.5 - cave.X, dz = gz + 0.5 - cave.Z, d = Math.Sqrt(dx * dx + dz * dz);
        if (cave.Kind == CaveKind.Ruin && d < WorldLayout.L23FlatRadius(cave.Kind) + 1)
            b[fi] = Noise2(gx / 4.0, gz / 4.0, SaltL23Mat + 6) > 0.15 ? l23RuinMoss : l23RuinStone;
        else if (!flat && pillar == 0 && Noise2(gx / 6.0, gz / 6.0, SaltL23Mat + 7) < -0.55)
        {
            b[fi] = 0;
            c.Water[fi] = true;
            b[fi - 1] = l23Earth;
        }
        else b[fi] = Noise2(gx / 8.0, gz / 8.0, SaltL23Mat + 8) > -0.25 ? l23Moss : l23Earth;
        // The roof: roots through the earth
        if (ceiling - L23Low < L23Height) b[ceiling - L23Low] = L23Unit(gx, gz, 9) < 0.5 ? l23RootEarth : l23Root;
        L23CaveThings(c, gx, gz, floor, ceiling, cave, pillar != 0 && cave.Kind == CaveKind.Glow);
    }

    /// <summary>
    /// What is in a cavern: in a glow room, its little forest of petrified trees, glowcaps of its colour, mushrooms and
    /// ferns, Gardener's Sorries and lichen hanging from the roof; the ruins and their pottery; Base Seedling's camp.
    /// </summary>
    private void L23CaveThings(L23Column c, int gx, int gz, int floor, int ceiling, in Cave cave, bool pillar)
    {
        int[] b = c.Blocks;
        int u = gx - cave.X, v = gz - cave.Z;
        int gap = ceiling - floor - 1;
        if (cave.Kind == CaveKind.Ruin) L23RuinColumn(c, gx, gz, u, v, floor, ceiling, cave);
        if (cave.Kind == CaveKind.Seedling) L23SeedlingColumn(c, gx, gz, u, v, floor, ceiling);
        if (pillar) return;

        // (Round 3: now and then in a glow room a long root comes down from the roof to the floor, wet, a pool at its foot:
        // the lore's trees above that pipe water down to the glow rooms)
        if (cave.Kind == CaveKind.Glow && gap >= 4 && L23Unit(gx, gz, 28) < 0.004 && b[floor + 1 - L23Low] == 0 && !c.Water[floor - L23Low])
        {
            for (int rel = ceiling - 1; rel > floor + 1; rel--) if (b[rel - L23Low] == 0) b[rel - L23Low] = l23Root;
            b[floor - L23Low] = 0;
            c.Water[floor - L23Low] = true;
            b[floor - 1 - L23Low] = l23Earth;
            return;
        }
        // Hanging from the roof: Sorries (light), lichen, a root
        int under = ceiling - 1 - L23Low;
        if (gap >= 4 && b[under] == 0)
        {
            double h = L23Unit(gx, gz, 10);
            // (More over the ruins, which lie deepest in their glow rooms: round 2's shots showed them nearly black)
            double sorries = cave.Kind == CaveKind.Seedling ? 0.012 : cave.Kind == CaveKind.Ruin ? 0.045 : 0.024;
            if (h < sorries) b[under] = l23Sorry[cave.Colour == 0 || L23Unit(gx, gz, 11) < 0.15 ? 0 : cave.Colour];
            else if (h < sorries + 0.03) L23Hang(b, ceiling - 1, 1 + (int)(L23Hash(gx, gz, 12) % 3), floor, root: false);
            else if (h < sorries + 0.06) L23Hang(b, ceiling - 1, 1 + (int)(L23Hash(gx, gz, 12) % 2), floor, root: true);
        }
        // (Round the ruins' plazas the glow room's own floor goes on: glowcaps, mushrooms and ferns, but no little trees)
        bool ruinEdge = cave.Kind == CaveKind.Ruin && u * u + v * v > (WorldLayout.L23FlatRadius(CaveKind.Ruin) + 2) * (WorldLayout.L23FlatRadius(CaveKind.Ruin) + 2);
        if (cave.Kind != CaveKind.Glow && !ruinEdge) return;

        // The little forest: petrified trees two to four high with a crown of leaves, on their own lattice
        if (!ruinEdge && L23LittleTree(b, gx, gz, floor, ceiling)) return;
        int on = floor + 1 - L23Low;
        if (b[on] != 0 || c.Water[on] || c.Water[on - 1] || b[on - 1] == 0) return;
        double r = L23Unit(gx, gz, 13);
        double patch = Math.Max(0, Noise2(gx / 9.0, gz / 9.0, SaltL23Mat + 9));
        ulong k = L23Hash(gx, gz, 14);
        if (r < 0.05 * patch + 0.01) b[on] = l23Glowcap[L23Unit(gx, gz, 15) < 0.2 ? 1 + (int)(k % 3) : cave.Colour];
        // (Round 3: the lore's glowing bushes, here and there among them)
        else if (r < 0.05 * patch + 0.022 && !ruinEdge) b[on] = l23Glowbush[cave.Colour == 0 ? 1 : cave.Colour];
        else if (r < 0.06 + 0.02 * patch) b[on] = l23Mushrooms[k % (ulong)l23Mushrooms.Length];
        else if (r < 0.065 + 0.02 * patch) b[on] = l23Toadstools[k % (ulong)l23Toadstools.Length];
        else if (r < 0.10 + 0.04 * patch) b[on] = l23Ferns[k % (ulong)l23Ferns.Length];
    }

    /// <summary>The glow rooms' little trees: a trunk of petrified wood on a lattice point of their own, a crown of leaves over it and round it.</summary>
    private bool L23LittleTree(int[] b, int gx, int gz, int floor, int ceiling)
    {
        int ti = Hashing.FloorDiv(gx, WorldLayout.L23TreePitch), tj = Hashing.FloorDiv(gz, WorldLayout.L23TreePitch);
        bool any = false;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (!layout.L23LittleTreeAt(ti + di, tj + dj, out int tx, out int tz, out ulong h)) continue;
                int ax = Math.Abs(gx - tx), az = Math.Abs(gz - tz);
                if (ax > 1 || az > 1) continue;
                // (Its own floor, from its own column, so its crown sits level)
                if (!layout.L23Cave(tx, tz, out int tf, out int tc, out Cave tcave) || tcave.Kind != CaveKind.Glow) continue;
                int height = 2 + (int)(Hashing.Mix(h + 2) % 3);
                if (tc - tf - 1 < height + 3) continue;
                int crown = tf + height + 1;
                // (Round 3: one in four is a stone mushroom instead, its cap a flat disc three across)
                bool mush = Hashing.Unit(Hashing.Mix(h + 11)) < 0.25;
                int stem = mush ? l23Bark[WorldLayout.L23MushStem] : l23Bark[1 + (int)(Hashing.Mix(h + 3) % 4)];
                int crownBlock = mush ? l23Bark[WorldLayout.L23MushCap] : l23Leaves;
                if (ax == 0 && az == 0)
                {
                    for (int rel = floor + 1; rel <= tf + height; rel++) if (b[rel - L23Low] == 0) b[rel - L23Low] = stem;
                    if (b[crown - L23Low] == 0) b[crown - L23Low] = crownBlock;
                    if (!mush && b[crown + 1 - L23Low] == 0 && crown + 1 < tc) b[crown + 1 - L23Low] = l23Leaves;
                    any = true;
                }
                else if (mush)
                {
                    if (b[crown - L23Low] == 0) b[crown - L23Low] = crownBlock;
                }
                else if (ax + az == 1 || Hashing.Unit(Hashing.Mix(h + (ulong)(ax * 3 + az * 5 + gx + gz))) < 0.7)
                {
                    // (Round 3: a rounder crown: the side's middles a block higher too, now and then hanging a block lower)
                    if (b[crown - L23Low] == 0) b[crown - L23Low] = l23Leaves;
                    ulong hs = Hashing.Mix(h + (ulong)(gx * 31 + gz * 17));
                    if (ax + az == 1 && crown + 1 < tc && b[crown + 1 - L23Low] == 0 && Hashing.Unit(hs) < 0.6) b[crown + 1 - L23Low] = l23Leaves;
                    if (ax + az == 1 && b[crown - 1 - L23Low] == 0 && Hashing.Unit(hs << 16) < 0.4) b[crown - 1 - L23Low] = l23Leaves;
                }
            }
        return any;
    }

    // ---- The ruins of the Architects ----

    /// <summary>A ruin's column: its building, the moss and the gaps of its age, Latin cut into its walls, pottery about it.</summary>
    private void L23RuinColumn(L23Column c, int gx, int gz, int u, int v, int floor, int ceiling, in Cave cave)
    {
        int[] b = c.Blocks;
        for (int rel = floor + 1; rel < ceiling; rel++)
        {
            int h = rel - cave.Floor;
            int block = cave.Ruin switch
            {
                Ruin.Lighthouse => L23Lighthouse(u, v, h),
                Ruin.Sphere => L23Sphere(u, v, h),
                Ruin.Colosseum => L23Colosseum(u, v, h),
                _ => L23Parthenon(u, v, h),
            };
            if (block < 0) continue;
            if (block == l23RuinStone)
            {
                // Age: stones fallen out, moss over the rest
                if (L23Unit(gx * 3 + rel, gz, 16) < 0.035) block = 0;
                else if (Noise2(gx / 3.0 + rel * 0.5, gz / 3.0, SaltL23Mat + 10) > 0.1 - 0.02 * h) block = l23RuinMoss;
            }
            b[rel - L23Low] = block;
        }
        // Round 4: two statues of Architects flanking the way in from the south, on their plinths, facing out
        if ((u == -6 || u == 6) && v == 15 && floor + 3 < ceiling)
        {
            for (int k = 0; k < 3; k++) b[floor + 1 + k - L23Low] = l23Statue[k, Facing(ArchPier.South)];
            return;
        }
        // Pottery: on the plaza and in the rooms, on the first floor up; and the fungi the lore says overgrow the ruins,
        // glowcaps of the room's colour come up through the moss on the paving (round 2: the plazas were black without them)
        double d = Math.Sqrt(u * u + v * v);
        if (d < WorldLayout.L23FlatRadius(CaveKind.Ruin) + 6)
            for (int rel = floor + 1; rel < ceiling - 1; rel++)
            {
                int i = rel - L23Low;
                if (b[i] != 0) continue;
                if (b[i - 1] != 0 && L23Unit(gx, gz, 17) < 0.035) b[i] = l23Pottery[L23Unit(gx, gz, 18) < 0.4 ? 0 : 1];
                // (Round 3: rags of the Architects' cloth, the lore's finds besides the pottery)
                else if (b[i - 1] != 0 && L23Unit(gx, gz, 17) < 0.05) b[i] = l23Cloth;
                else if (b[i - 1] == l23RuinMoss && L23Unit(gx, gz, 19) < 0.09) b[i] = l23Glowcap[cave.Colour];
                break;
            }
    }

    private static int L23Mod(int a, int m) => ((a % m) + m) % m;

    /// <summary>The Lighthouse of Alexandria, built as a stepped pyramid nine high, its fire on top; a passage from the south into a chamber at its heart.</summary>
    private int L23Lighthouse(int u, int v, int h)
    {
        int au = Math.Abs(u), av = Math.Abs(v), m = Math.Max(au, av);
        if (h >= 1 && h <= 9 && m <= 10 - h)
        {
            bool chamber = au <= 2 && av <= 2 && h <= 4;
            bool passage = au <= 1 && v >= 2 && h <= 3;
            if (chamber || passage) return 0;
            // Latin on the chamber's walls
            if (h == 2 && m == 3 && (u == 0 || v == 0) && v <= 0) return l23Latin[u == 0 ? 0 : u > 0 ? 1 : 2];
            // (Round 3: damaged paintings on them above, facing in: the lore's paintings)
            if (h == 3 && m == 3 && (au <= 1 && av == 3 || av <= 1 && au == 3) && !(v > 0 && au <= 1))
                return l23Fresco[Facing(au > av ? (u > 0 ? ArchPier.West : ArchPier.East) : (v > 0 ? ArchPier.North : ArchPier.South))];
            return l23RuinStone;
        }
        // (Its fire on top: a lamp still burning, as the lore's lighthouse would have; an ember gave no light to see it by)
        if (h == 10 && m == 0) return l23Lantern;
        if (h is 10 or 11 && au == 1 && av == 1) return l23RuinStone;
        return -1;
    }

    /// <summary>The Great Pyramid of Giza, built as a sphere thirteen across, its door on the south and the Architects' plaque beside it.</summary>
    private int L23Sphere(int u, int v, int h)
    {
        double dy = h - 6.0, d = Math.Sqrt(u * u + v * v + dy * dy);
        if (h < 1 || d > 6.6) return -1;
        if (h == 1) return l23RuinStone;
        if (d < 5.5) return 0;
        if (v > 0 && Math.Abs(u) <= 1 && h <= 4) return 0;
        if (v > 0 && h == 3 && u == 2) return l23Plaque;
        if (v > 0 && h == 3 && u == -2) return l23Latin[3];
        // (Round 3: inside, damaged paintings round the wall at eye height, facing in)
        if (h is 3 or 4 && d < 6.4 && (Math.Abs(u) >= 4 || Math.Abs(v) >= 4) && (u + v * 3 & 3) != 0)
        {
            ArchPier inward = Math.Abs(u) > Math.Abs(v) ? (u > 0 ? ArchPier.West : ArchPier.East) : (v > 0 ? ArchPier.North : ArchPier.South);
            var (sx, sz) = WorldLayout.L23Step(inward);
            double di = Math.Sqrt((u + sx) * (u + sx) + (v + sz) * (v + sz) + dy * dy);
            if (di < 5.5) return l23Fresco[Facing(inward)];
        }
        return l23RuinStone;
    }

    /// <summary>The Colosseum, built square: two arcaded walls round a corridor, two tiers high, round a sanded arena; part of it fallen in.</summary>
    private int L23Colosseum(int u, int v, int h)
    {
        int au = Math.Abs(u), av = Math.Abs(v), m = Math.Max(au, av);
        if (m > 12 || h < 1) return -1;
        if (m < 8) return -1;
        bool collapsed = Noise2(u / 6.0, v / 6.0, SaltL23Mat + 11) > 0.35;
        bool wall = m == 12 || m == 8;
        int along = au > av ? v : u;
        bool pier = L23Mod(along, 3) == 0 || au == av;
        if (h <= 4)
        {
            if (!wall) return 0;
            if (h <= 3 && !pier) return 0;
            if (h == 2 && m == 8 && along == 0) return l23Latin[au > av ? (u > 0 ? 0 : 1) : (v > 0 ? 2 : 3)];
            return l23RuinStone;
        }
        if (collapsed) return 0;
        if (h == 5) return Noise2(u / 3.0, v / 3.0, SaltL23Mat + 12) > 0.5 ? 0 : l23RuinStone;
        if (h <= 9)
        {
            if (!wall) return 0;
            if (h <= 8 && !pier) return 0;
            return l23RuinStone;
        }
        if (h == 10 && m == 12) return (along & 1) == 0 ? l23RuinStone : 0;
        return -1;
    }

    /// <summary>The Parthenon, built on a triangle: a stepped platform, a colonnade round its three sides, a walled cella with its door to the south, a roof partly fallen.</summary>
    private int L23Parthenon(int u, int v, int h)
    {
        // The triangle points north; its sides' outward normals, and the inradius (circumradius 13)
        const double inr = 6.5;
        double px = u, pz = v;
        double dmin = double.MaxValue, along = 0;
        for (int k = 0; k < 3; k++)
        {
            double a = Math.PI / 2 + k * 2 * Math.PI / 3; // south, then north-west, then north-east
            double nx = Math.Cos(a), nz = Math.Sin(a);
            double e = inr - (px * nx + pz * nz);
            if (e < dmin)
            {
                dmin = e;
                along = -px * nz + pz * nx;
            }
        }
        if (dmin < 0 || h < 1) return -1;
        bool south = v > 0 && dmin == inr - pz;
        if (h == 1) return l23RuinStone;
        if (h == 2) return dmin >= 1 ? l23RuinStone : -1;
        if (h <= 8)
        {
            // (Round 4: the colonnade's columns as columns, a base, a fluted shaft and a capital; mossy at their feet)
            if (dmin >= 1.5 && dmin < 2.5)
                return L23Mod((int)Math.Round(along), 3) != 0 ? 0 : h == 2 ? l23RuinStone : l23Column[h == 3 ? 0 : h == 8 ? 2 : 1, h <= 4 ? 1 : 0, 0];
            if (dmin >= 5 && dmin < 6)
            {
                if (south && Math.Abs(u) <= 1 && h <= 5) return 0;
                if (south && h == 4 && Math.Abs(u) == 3) return l23Latin[Math.Sign(u) > 0 ? 1 : 2];
                return l23RuinStone;
            }
            return 0;
        }
        if (h == 9) return dmin >= 1.2 && dmin < 3.5 || dmin >= 5 && dmin < 6 ? l23RuinStone : 0;
        if (h == 10) return dmin >= 1 && Noise2(u / 5.0, v / 5.0, SaltL23Mat + 13) < 0.3 ? l23RuinStone : -1;
        if (h == 11) return dmin >= 4.5 && Noise2(u / 5.0, v / 5.0, SaltL23Mat + 13) < 0.3 ? l23RuinStone : -1;
        return -1;
    }

    // ---- Base Seedling ----

    /// <summary>Base Seedling's lanterns, cavern-local.</summary>
    private static readonly (int U, int V)[] L23Lanterns = { (5, 3), (-5, 3), (0, -6), (-8, -8), (11, 3), (-9, 8), (4, 13), (-14, -3) };

    /// <summary>
    /// Base Seedling's things (round 3), cavern-local: a path of flagstones from the south up to the hollow tree's door; the
    /// quartermaster's counter (three tables, his ledger on the middle one, crates stacked behind) beside where he stands;
    /// water barrels by the spring; a fire ring with log seats; bedrolls by the tents; the camp's sign and the M.E.G.'s
    /// notice board on their posts, facing south (the way the camp is seen from), the first half on the reader's left.
    /// </summary>
    private static readonly (int U, int V, string Text)[] L23CampBoards =
        { (-9, 13, "camp-a"), (-8, 13, "camp-b"), (-7, 13, "camp-c"), (5, 13, "rules-a"), (6, 13, "rules-b") };

    private static readonly (int U, int V, ArchPier Head)[] L23Bedrolls =
        { (-8, -6, ArchPier.West), (-8, -2, ArchPier.West), (6, -8, ArchPier.North), (10, -8, ArchPier.North), (4, 5, ArchPier.South), (9, 5, ArchPier.South) };

    private void L23CampThings(int[] b, int u, int v, int floor)
    {
        int on = floor + 1 - L23Low;
        if (Math.Abs(u) <= 1 && v >= 4 && v <= 21 && b[floor - L23Low] != 0) b[floor - L23Low] = l23Flagstone;
        if (b[on] != 0) return;
        foreach (var (bu, bv, text) in L23CampBoards)
        {
            if (bu != u || bv != v) continue;
            if (text != "camp-b") b[on] = l23SignPost;
            b[on + 1] = l23Signs[text][Facing(ArchPier.South)];
            return;
        }
        foreach (var (bu, bv, head) in L23Bedrolls)
            if (bu == u && bv == v) { b[on] = l23Bedroll[Facing(head)]; return; }
        // The quartermaster's counter (round 4: one piece of three blocks, its front south to the camp), his ledger, the stores behind it
        if (v == 6 && u >= -4 && u <= -2)
        {
            b[on] = l23Counter[-2 - u, Facing(ArchPier.South)];
            if (u == -3) b[on + 1] = l23Ledger;
            return;
        }
        if (v == 4 && u >= -4 && u <= -2)
        {
            b[on] = l23Crate;
            if (u == -4) b[on + 1] = l23Crate;
            // (On the last crate, the camp's squirt guns, facing the counter)
            if (u == -2) b[on + 1] = l23SquirtRack[Facing(ArchPier.South)];
            return;
        }
        // Water barrels by the spring
        if ((u, v) is (-9, 4) or (-9, 5) or (-8, 3)) { b[on] = l23Barrel; return; }
        // The fire ring and its seats
        if ((u, v) == (-5, 10)) { b[on] = l23FireRing; return; }
        // (Its seats: stumps of stone; round 3's first shots had whole log blocks, which read as plain cubes)
        if ((u, v) is (-7, 10) or (-5, 8) or (-3, 10)) { b[on] = l23StonePlant[3]; return; }
    }

    /// <summary>Base Seedling's column: the hollow tree (the way home, they say), lanterns round the camp, a table, a spring.</summary>
    private void L23SeedlingColumn(L23Column c, int gx, int gz, int u, int v, int floor, int ceiling)
    {
        int[] b = c.Blocks;
        double d = Math.Sqrt(u * u + v * v);
        int on = floor + 1 - L23Low;
        if (d < 3.9)
        {
            if (d < 2.4)
            {
                // The hollow: dark, going up into the ground further than a light shows
                for (int rel = floor + 1; rel <= -2; rel++) b[rel - L23Low] = 0;
                b[floor - L23Low] = l23Earth;
            }
            else
                for (int rel = floor + 1; rel <= Math.Max(ceiling, -1); rel++)
                {
                    int h = rel - floor;
                    b[rel - L23Low] = WorldLayout.L23HollowDoor(u, v) && h <= 3 ? 0 : l23Bark[WorldLayout.L23BarkGreen];
                }
            return;
        }
        foreach (var (lu, lv) in L23Lanterns)
            if (lu == u && lv == v && b[on] == 0) b[on] = l23Lantern;
        if (u == 3 && v == -4 && b[on] == 0 && l23Table != 0) b[on] = l23Table;
        L23CampThings(b, u, v, floor);
        // The spring
        double sx = u + 7, sz = v - 5;
        if (sx * sx + sz * sz < 2.6)
        {
            b[floor - L23Low] = 0;
            c.Water[floor - L23Low] = true;
            b[floor - 1 - L23Low] = l23Gravel;
        }
    }
}
