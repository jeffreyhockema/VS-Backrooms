using System;
using W = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 47, "The Adderwood" (experimental, kept as level 30), laid out in WorldLayout.Level47.cs, from its own
/// floor (<see cref="WorldGeometry.FloorFor"/>, ten below the shared one), up to the top of the world. Each column is worked
/// out whole, once (<see cref="L47ColumnOf"/>), from the layout's functions:
/// <list type="bullet">
/// <item>the forest floor: moss, leaf litter and humus over dark earth; ferns, mushrooms (most good to eat, some not),
/// fallen sticks, now and then grass and a flower; the trail trodden bare; the streams' beds of pebbles under clean water,
/// stepping stones where the trail fords one;</item>
/// <item>the trees: oak, beech, fir and spruce bark, mossed over at the foot and in patches up the trunk; their crowns of
/// leaves and needles; old man's beard hanging from them; the dead trees grey and bare; the green giants;</item>
/// <item>fallen logs and mossy boulders, the Order's way-stones beside the trail;</item>
/// <item>the glade: a meadow, the manor and the stones (WorldLayout.Level47.Glade.cs);</item>
/// <item>the thicket where the region ends: trunk against trunk, too close to pass.</item>
/// </list>
/// This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private const ulong SaltL47Deco = 0x3040, SaltL47Mat = 0x3041;

    /// <summary>The lowest height of a column that is worked out (the band's bottom), and how many heights there are up to the top of the world.</summary>
    private const int L47Low = -WorldGeometry.L47BandDepth, L47Height = W.L47Top - L47Low + 1;

    private int l47Humus, l47Moss, l47Litter, l47Earth, l47Trail, l47Pebbles, l47Boulder, l47BoulderMoss, l47GrassSoil,
        l47ManorStone, l47ManorMoss, l47Plinth, l47Timber, l47Slate, l47Boards, l47Window, l47Megalith, l47MegalithMoss, l47Flag, l47Lantern,
        l47Brazier, l47Hearth, l47Candles, l47Table, l47Ladder, l47Stick, l47TallGrass, l47ShortGrass;
    /// <summary>The block of each kind of the forest (<see cref="WorldLayout.L47Wood"/>'s kinds), and the mossy bark of each bark.</summary>
    private readonly int[] l47Kind = new int[W.L47KindLimit], l47MossBark = new int[W.L47KindLimit];
    private readonly int[] l47Shelf = new int[4];
    private readonly int[,] l47Banner = new int[2, 4];
    private int[] l47Ferns, l47Mushrooms, l47Toadstools, l47Flowers;
    private readonly int[] l47Lichen = new int[3];

    // ---- Round 4 (the asset-quality pass): the models (tools/gen_47_props4.py) ----
    /// <summary>The fillets by bark (<see cref="L47FilletBarks"/>) and corner (ne, se, sw, nw).</summary>
    private readonly int[,] l47Fillet = new int[14, 4];
    private static readonly string[] L47FilletBarks = { "oak", "beech", "fir", "spruce", "dead", "green", "mossoak", "mossbeech", "mossfir", "mossspruce", "mossdead", "mossgreen", "granite", "granitemoss" };
    private readonly int[,] l47Drape = new int[2, 4], l47Bracket = new int[2, 4], l47Waystone = new int[2, 4], l47Leaded = new int[3, 2], l47Door = new int[2, 6],
        l47Jamb = new int[2, 2], l47Roof = new int[4, 2], l47Mantel = new int[3, 4], l47Tapestry = new int[4, 4];
    private readonly int[,,] l47Bookcase = new int[2, 2, 4];
    private readonly int[] l47Mush = new int[3], l47Fire = new int[4], l47Trestle = new int[3], l47Bench = new int[2], l47Sconce = new int[4];
    private readonly int[,] l47Spray = new int[3, 2];
    private int l47SarsenTop, l47FireRing23, l47FireCold;
    private readonly int[] l47Bedroll23 = new int[4];
    private readonly int[] l47Offering = new int[3], l47PorchPost = new int[3];
    private readonly int[,] l47LampPost = new int[2, 4];
    private int l47RootEarth, l47Pot, l47Barrel23, l47Crate23, l47StepStone, l47RiverRock;
    private readonly int[] l47Chest73 = new int[4], l47Sacks73 = new int[4];

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL47()
    {
        string[] barks = { null, "oak", "beech", "fir", "spruce", "dead", "green" };
        for (int k = W.L47BarkOak; k <= W.L47BarkGreen; k++)
        {
            l47Kind[k] = Id("l47-bark-" + barks[k]);
            l47MossBark[k] = Id("l47-mossbark-" + barks[k]);
        }
        l47Kind[W.L47LeafOak] = Id("l47-leaves-oak");
        l47Kind[W.L47LeafBeech] = Id("l47-leaves-beech");
        l47Kind[W.L47LeafNeedle] = Id("l47-leaves-needle");
        l47Kind[W.L47Stone] = l47Boulder = Id("l47-boulder");
        l47BoulderMoss = Id("l47-boulder-moss");
        l47Kind[W.L47LogOakX] = Id("l47-log-oak-x");
        l47Kind[W.L47LogOakZ] = Id("l47-log-oak-z");
        l47Kind[W.L47LogDeadX] = Id("l47-log-dead-x");
        l47Kind[W.L47LogDeadZ] = Id("l47-log-dead-z");
        l47Kind[W.L47TrailStone] = Id("l47-waystone");
        l47Humus = Id("l47-humus");
        l47Moss = Id("l47-moss");
        l47Litter = Id("l47-litter");
        l47Earth = Id("l47-earth");
        l47Trail = Id("l47-trail");
        l47Pebbles = Id("l47-pebbles");
        l47ManorStone = Id("l47-manorstone");
        l47ManorMoss = Id("l47-manorstone-moss");
        l47Plinth = Id("l47-plinth");
        l47Timber = Id("l47-timber");
        l47Slate = Id("l47-slate");
        l47Boards = Id("l47-boards");
        l47Window = Id("l47-window");
        l47Megalith = Id("l47-megalith");
        l47MegalithMoss = Id("l47-megalith-moss");
        l47Flag = Id("l47-flagstone");
        l47Lantern = Id("l47-lantern");
        l47Brazier = Id("l47-brazier");
        l47Hearth = Id("l47-hearth");
        l47Candles = Id("l47-candles");
        for (int f = 0; f < 4; f++)
        {
            l47Shelf[f] = Id("l47-shelf-" + Sides[f]);
            l47Banner[0, f] = Id("l47-banner-top-" + Sides[f]);
            l47Banner[1, f] = Id("l47-banner-foot-" + Sides[f]);
        }
        l47GrassSoil = GameId("game:soil-medium-normal", "game:soil-low-normal");
        l47Table = OptionalId("game:table-normal");
        l47Ladder = GameId("game:ladder-wood-oak-north", "game:ladder-wood-aged-north");
        l47Stick = OptionalId("game:loosestick-free");
        l47TallGrass = GameId("game:tallgrass-medium-free", "game:tallgrass-short-free");
        l47ShortGrass = GameId("game:tallgrass-veryshort-free", "game:tallgrass-short-free");
        l47Flowers = VegIds("game:flower-wilddaisy-free", "game:flower-forgetmenot-free", "game:flower-lilyofthevalley-free", "game:flower-cornflower-free");
        l47Ferns = VegIds("game:fern-eaglefern", "game:fern-deerfern", "game:fern-hartstongue", "game:fern-cinnamonfern", "game:tallfern");
        // Most of the mushrooms are good to eat; some are not (Wikidot: "some species are poisonous or hallucinogenic")
        l47Mushrooms = VegIds("game:mushroom-fieldmushroom-normal", "game:mushroom-kingbolete-normal", "game:mushroom-chanterelle-normal",
            "game:mushroom-blacktrumpet-normal", "game:mushroom-puffball-normal", "game:mushroom-orangeoakbolete-normal");
        l47Toadstools = VegIds("game:mushroom-flyagaric-normal", "game:mushroom-deathcap-normal", "game:mushroom-earthball-normal", "game:mushroom-devilbolete-normal");
        // Round 4
        string[] corners = { "ne", "se", "sw", "nw" };
        for (int k = 0; k < L47FilletBarks.Length; k++)
            for (int c = 0; c < 4; c++) l47Fillet[k, c] = OptionalId($"backrooms:l47-fillet-{L47FilletBarks[k]}-{corners[c]}");
        string[] ab = { "a", "b" }, brackets = { "zoned", "sulphur" }, parts2 = { "lower", "upper" };
        for (int f = 0; f < 4; f++)
        {
            for (int k = 0; k < 2; k++)
            {
                l47Drape[k, f] = OptionalId($"backrooms:l47-mossdrape-{ab[k]}-{Sides[f]}");
                l47Bracket[k, f] = OptionalId($"backrooms:l47-bracket-{brackets[k]}-{Sides[f]}");
                l47Waystone[k, f] = OptionalId($"backrooms:l47-waystone2-{parts2[k]}-{Sides[f]}");
                for (int d = 0; d < 2; d++) l47Bookcase[k, d, f] = OptionalId($"backrooms:l47-bookcase-{parts2[k]}-{ab[d]}-{Sides[f]}");
            }
            l47Fire[f] = OptionalId("backrooms:l47-fire-" + Sides[f]);
            l47Sconce[f] = OptionalId("backrooms:l47-sconce-" + Sides[f]);
            string[] mantel = { "l", "m", "r" }, cells = { "tl", "tr", "bl", "br" };
            for (int k = 0; k < 3; k++) l47Mantel[k, f] = OptionalId($"backrooms:l47-mantel-{mantel[k]}-{Sides[f]}");
            for (int k = 0; k < 4; k++) l47Tapestry[k, f] = OptionalId($"backrooms:l47-tapestry-{cells[k]}-{Sides[f]}");
        }
        string[] mush = { "agaric", "honey", "inkcap" }, wins = { "lower", "upper", "single" }, axes = { "ns", "ew" }, leaves = { "west", "east" },
            pieces = { "near-lower", "near-mid", "near-upper", "far-lower", "far-mid", "far-upper" }, roofs = { "slope", "eave", "ridge", "gable" }, ns = { "north", "south" },
            trestles = { "end", "mid", "centre" }, benches = { "end", "mid" };
        for (int k = 0; k < 3; k++) l47Mush[k] = OptionalId("backrooms:l47-mushclump-" + mush[k]);
        for (int k = 0; k < 3; k++) for (int a = 0; a < 2; a++) l47Leaded[k, a] = OptionalId($"backrooms:l47-leaded-{wins[k]}-{axes[a]}");
        for (int k = 0; k < 2; k++)
        {
            for (int p = 0; p < 6; p++) l47Door[k, p] = OptionalId($"backrooms:l47-door-{leaves[k]}-{pieces[p]}");
            for (int p = 0; p < 2; p++) l47Jamb[k, p] = OptionalId($"backrooms:l47-doorjamb-{leaves[k]}-{parts2[p]}");
        }
        for (int k = 0; k < 4; k++) for (int f = 0; f < 2; f++) l47Roof[k, f] = OptionalId($"backrooms:l47-roof-{roofs[k]}-{ns[f]}");
        for (int k = 0; k < 3; k++) l47Trestle[k] = OptionalId("backrooms:l47-table-" + trestles[k]);
        for (int k = 0; k < 2; k++) l47Bench[k] = OptionalId("backrooms:l47-bench-" + benches[k]);
        l47RootEarth = OptionalId("backrooms:l47-rootearth");
        l47Pot = OptionalId("backrooms:l47-chimneypot");
        l47SarsenTop = OptionalId("backrooms:l47-sarsentop");
        // (A wanderer's camp: the Petrified Garden's fire ring and bedroll)
        l47FireRing23 = OptionalId("backrooms:l23-firering");
        l47FireCold = OptionalId("backrooms:l47-firecold");
        for (int f = 0; f < 4; f++) l47Bedroll23[f] = OptionalId("backrooms:l23-bedroll-" + Sides[f]);
        string[] porch = { "base", "shaft", "head" };
        for (int k = 0; k < 3; k++) l47PorchPost[k] = OptionalId("backrooms:l47-porchpost-" + porch[k]);
        string[] offerings = { "bowl", "skull", "book" };
        for (int k = 0; k < 3; k++) l47Offering[k] = OptionalId("backrooms:l47-offering-" + offerings[k]);
        for (int f = 0; f < 4; f++) { l47LampPost[0, f] = OptionalId("backrooms:l47-lamppost-lower-" + Sides[f]); l47LampPost[1, f] = OptionalId("backrooms:l47-lamppost-upper-" + Sides[f]); }
        string[] sprayLeaves = { "oak", "beech", "needle" };
        for (int k = 0; k < 3; k++) { l47Spray[k, 0] = OptionalId($"backrooms:l47-leafspray-{sprayLeaves[k]}-hang"); l47Spray[k, 1] = OptionalId($"backrooms:l47-leafspray-{sprayLeaves[k]}-tuft"); }
        l47StepStone = OptionalId("backrooms:l47-streamstone-step");
        l47RiverRock = OptionalId("backrooms:l47-streamstone-rock");
        // (Shared with the other levels: the Redlands' chests and sacks, the Petrified Garden's barrels and crates)
        for (int f = 0; f < 4; f++) { l47Chest73[f] = OptionalId("backrooms:l73-chest-" + Sides[f]); l47Sacks73[f] = OptionalId("backrooms:l73-sacks-" + Sides[f]); }
        l47Barrel23 = OptionalId("backrooms:l23-barrel");
        l47Crate23 = OptionalId("backrooms:l23-crate");
        l47Kind[W.L47RootEarth] = l47RootEarth != 0 ? l47RootEarth : l47Earth;
        string[] lichenParts = { "top", "segment", "bottom" };
        for (int p = 0; p < 3; p++) l47Lichen[p] = OptionalId("game:hanginglichen-oldmans-" + lichenParts[p]);
        floorIds[(int)FloorKind.L47Floor] = l47Moss;
        floorIds[(int)FloorKind.L47Trail] = l47Trail;
        floorIds[(int)FloorKind.L47Stream] = l47Pebbles;
        floorIds[(int)FloorKind.L47Grass] = l47GrassSoil;
        floorIds[(int)FloorKind.L47Bark] = l47Kind[W.L47BarkOak];
    }

    /// <summary>One column of the level, worked out whole: its block and fluid at every height from <see cref="L47Low"/> up.</summary>
    private sealed class L47Column
    {
        public WorldGenerator Owner;
        public int Gx, Gz;
        public Tile Tile;
        public readonly int[] Blocks = new int[L47Height];
        public readonly bool[] Water = new bool[L47Height];
        public readonly byte[] Wood = new byte[L47Height];
    }

    [ThreadStatic] private static L47Column l47Column;

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level47Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < L47Low) return concreteId; // (the ground below, as vanilla laid it)
        if (rel > W.L47Top) return 0;
        L47Column c = L47ColumnOf(t, gx, gz);
        int i = rel - L47Low;
        if (c.Water[i]) fluid = waterId;
        return c.Blocks[i];
    }

    private L47Column L47ColumnOf(in Tile t, int gx, int gz)
    {
        var c = l47Column ??= new L47Column();
        if (c.Owner == this && c.Gx == gx && c.Gz == gz && c.Tile.SupplyBox == t.SupplyBox && c.Tile.Looted == t.Looted && c.Tile.Zone == t.Zone) return c;
        c.Owner = null;
        c.Gx = gx;
        c.Gz = gz;
        c.Tile = t;
        Array.Clear(c.Water);
        if (t.Zone == W.L47RimZone) L47Thicket(c, gx, gz);
        else L47Forest(c, t, gx, gz);
        c.Owner = this;
        return c;
    }

    private double L47Unit(int gx, int gz, int k) => Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL47Deco + (ulong)k * 0x100));

    /// <summary>The thicket where the region ends: trunk against trunk (fir and dead wood), needles over them, too close to pass.</summary>
    private void L47Thicket(L47Column c, int gx, int gz)
    {
        for (int rel = L47Low; rel <= W.L47Top; rel++)
        {
            int i = rel - L47Low;
            if (rel <= 1) c.Blocks[i] = rel == 1 ? l47Moss : l47Earth;
            else if (rel <= 30)
            {
                double u = Hashing.Unit(Hashing.Hash(seed, gx * 64 + rel / 6, gz, SaltL47Mat));
                c.Blocks[i] = u < 0.45 ? l47Kind[W.L47BarkFir] : u < 0.7 ? l47Kind[W.L47BarkDead] : u < 0.85 ? l47MossBark[W.L47BarkSpruce] : l47Kind[W.L47LeafNeedle];
            }
            else c.Blocks[i] = rel <= 40 ? l47Kind[W.L47LeafNeedle] : 0;
        }
    }

    /// <summary>The forest's column: ground, water, wood, the glade's things, then what grows on the floor and hangs from the trees.</summary>
    private void L47Forest(L47Column c, in Tile t, int gx, int gz)
    {
        int[] b = c.Blocks;
        int ground = layout.L47Ground(gx, gz);
        double fromMid = layout.L47FromMid(gx + 0.5, gz + 0.5);
        bool glade = fromMid < W.L47GladeRadius;
        bool trail = t.Zone == W.L47TrailZone || !glade && layout.L47TrailAt(gx, gz) < W.L47TrailHalf;
        bool water = ground < 1;

        // ---- The ground: its top, earth under it, then the dark ground all the way down ----
        int top = glade ? l47GrassSoil : water ? l47Pebbles : trail ? (L47Unit(gx, gz, 1) < 0.18 ? l47Litter : l47Trail) : L47GroundTop(gx, gz);
        for (int rel = L47Low; rel <= W.L47Top; rel++)
        {
            int i = rel - L47Low;
            if (rel > ground) b[i] = 0;
            else if (rel == ground) b[i] = top;
            else if (rel >= ground - 3) b[i] = l47Earth;
            else b[i] = Noise2(gx / 7.0 + rel * 0.3, gz / 7.0, SaltL47Mat + 1) > 0.5 ? l47Boulder : l47Earth;
        }
        // The streams' water, to the brim of their beds; stepping stones where the trail fords one
        if (water)
        {
            for (int rel = ground + 1; rel <= 0; rel++) c.Water[rel - L47Low] = true;
            if (trail && ((gx + gz) & 1) == 0)
            {
                for (int rel = ground + 1; rel <= 0; rel++) { b[rel - L47Low] = l47BoulderMoss; c.Water[rel - L47Low] = false; }
                // (Round 4: the top one a worn stepping stone standing in the water)
                if (l47StepStone != 0) { b[-L47Low] = l47StepStone; c.Water[-L47Low] = true; }
            }
            else if (!trail && L47Unit(gx, gz, 2) < 0.06)
            {
                // (Round 4: a mossy river boulder standing out of the water)
                b[-L47Low] = l47RiverRock != 0 ? l47RiverRock : l47BoulderMoss;
                c.Water[-L47Low] = l47RiverRock != 0;
            }
        }

        // ---- The glade: the manor and the stones ----
        if (glade)
        {
            for (int rel = 0; rel <= W.L47Top; rel++)
            {
                int code = layout.L47GladeBlock(gx, gz, rel);
                if (code == W.L47GKeep) continue;
                b[rel - L47Low] = L47GladeId(code, gx, gz, rel);
            }
            // The meadow: grass, flowers here and there (not in the manor, not on the walk)
            if (!layout.L47InManor(gx, gz) && b[ground + 1 - L47Low] == 0 && b[ground - L47Low] == l47GrassSoil)
            {
                double u = L47Unit(gx, gz, 3);
                b[ground + 1 - L47Low] = u < 0.35 ? l47TallGrass : u < 0.6 ? l47ShortGrass : u < 0.64 && l47Flowers.Length > 0 ? l47Flowers[(int)(L47Unit(gx, gz, 4) * l47Flowers.Length)] : 0;
            }
            if (t.SupplyBox) b[ground + 1 - L47Low] = BoxOf(t);
            if (fromMid < W.L47GladeRadius - 16) return;
        }

        // ---- The wood: trunks, roots, limbs, crowns, logs, boulders, way-stones ----
        Array.Copy(L47WoodAt(gx, gz).Wood, c.Wood, L47Height);
        // Moss climbs a block or three up every trunk, and in patches higher on it
        for (int i = 0; i < L47Height; i++)
        {
            byte w = c.Wood[i];
            if (w == 0) continue;
            int rel = i + L47Low;
            if (glade && rel <= ground + 2) continue;
            if (rel <= ground && !W.L47IsBark(w)) continue;
            int id = l47Kind[w];
            if (W.L47IsBark(w) && L47Mossy(w, gx, gz, rel, ground)) id = l47MossBark[w];
            // (Round 4: the Order's way-stone, two blocks, turned to face the trail)
            else if (w == W.L47TrailStone && l47Waystone[0, 0] != 0) id = l47Waystone[rel > ground + 1 ? 1 : 0, L47FaceTrail(gx, gz)];
            b[i] = id;
            c.Water[i] = false;
        }
        // The tops of the boulders mossed over
        for (int i = 0; i < L47Height - 1; i++)
            if (b[i] == l47Boulder && b[i + 1] == 0 && i + L47Low > ground - 1) b[i] = l47BoulderMoss;
        // A hollow tree's floor: leaf litter blown in, not the cut end of its bark
        if (t.Under is Unders.L47DeadHollow or Unders.L47StillHollow or Unders.L47GreenHollow && ground >= L47Low) b[ground - L47Low] = l47Litter;

        // ---- Round 4: bark fillets round the trunks, moss drapes and brackets on them, mushroom clumps by them ----
        if (!glade && t.Under is not (Unders.L47DeadHollow or Unders.L47StillHollow or Unders.L47GreenHollow)) L47Dress(c, gx, gz, ground, trail || water);

        // ---- What grows on the forest floor ----
        if (!glade && !water && !trail && ground + 1 <= W.L47Top && b[ground + 1 - L47Low] == 0) L47Undergrowth(b, gx, gz, ground);

        // ---- Old man's beard hanging from the boughs and crowns ----
        for (int rel = W.L47Top; rel > ground + 4; rel--)
        {
            int i = rel - L47Low;
            if (b[i] == 0 || b[i - 1] != 0 || c.Water[i - 1]) continue;
            byte w = c.Wood[i];
            if (w == 0 || W.L47IsLeaf(w) && L47Unit(gx, gz * 7 + rel, 6) > 0.035 || !W.L47IsLeaf(w) && L47Unit(gx, gz * 7 + rel, 6) > 0.06) continue;
            L47Hang(b, rel - 1, 1 + (int)(L47Unit(gx, gz, 7) * 4), ground);
            break;
        }

        // ---- Round 4: sprays of leaves hanging under the crowns' lumps and standing over them ----
        if (l47Spray[0, 0] != 0)
            for (int rel = ground + 5; rel < W.L47Top; rel++)
            {
                int i = rel - L47Low;
                if (b[i] != 0 || c.Water[i]) continue;
                byte above = c.Wood[i + 1], below = c.Wood[i - 1];
                if (W.L47IsLeaf(above) && b[i + 1] == l47Kind[above] && L47Unit(gx, gz * 7 + rel, 30) < 0.4) b[i] = l47Spray[above - W.L47LeafOak, 0];
                else if (W.L47IsLeaf(below) && b[i - 1] == l47Kind[below] && L47Unit(gx, gz * 7 + rel, 31) < 0.3) b[i] = l47Spray[below - W.L47LeafOak, 1];
            }

        // ---- Round 4: a wanderer's camp, left (one cell in sixteen): the fire still alight, a bedroll by it, a log to sit on ----
        if (!glade && !water && !trail && l47FireRing23 != 0) L47Camp(b, gx, gz, ground);

        // ---- A supply box ----
        if (t.SupplyBox && !glade && ground + 1 <= W.L47Top) b[ground + 1 - L47Low] = BoxOf(t);
    }

    /// <summary>
    /// A wanderer's camp in a cell, if it has one (round 4; Wikidot: "campfires or improvised tools and weapons will often
    /// (though not always) vanish or revert" -- this one has not, yet): the fire ring with nobody at it (alight in one camp in four from layout 16, else cold), a bedroll
    /// two blocks east of it with its head to the fire, a stub of log to sit on two blocks west; only on open forest floor
    /// away from the arrival spots.
    /// </summary>
    private void L47Camp(int[] b, int gx, int gz, int ground)
    {
        if (!layout.L47CampAt(Hashing.FloorDiv(gx, W.MacroSize), Hashing.FloorDiv(gz, W.MacroSize), out int ax, out int az)) return;
        int dx = gx - ax, dz = gz - az;
        if (Math.Abs(dz) > 1 || Math.Abs(dx) > 4 || !layout.L47CampFits(ax, az)) return;
        // (The site trodden bare and cleared of ferns round the fire, so it reads as a camp)
        int at = ground + 1 - L47Low;
        if (b[ground - L47Low] is var top && (top == l47Moss || top == l47Litter || top == l47Humus)) b[ground - L47Low] = l47Trail;
        if (Array.IndexOf(l47Ferns, b[at]) >= 0 || b[at] == l47ShortGrass || b[at] == l47TallGrass || Array.IndexOf(l47Flowers, b[at]) >= 0
            || Array.IndexOf(l47Mushrooms, b[at]) >= 0 || Array.IndexOf(l47Toadstools, b[at]) >= 0 || b[at] == l47Stick) b[at] = 0;
        if (dz != 0 || dx is not (0 or 2 or -2)) return;
        int ring = l47FireCold != 0 && !layout.L47CampLit(Hashing.FloorDiv(ax, W.MacroSize), Hashing.FloorDiv(az, W.MacroSize)) ? l47FireCold : l47FireRing23;
        b[at] = dx == 0 ? ring : dx == 2 ? l47Bedroll23[3] : l47Kind[W.L47LogOakZ];
    }

    /// <summary>Whether a bark block of a column is its mossy one: a block or three up from the foot, in patches higher (dead wood only at the foot).</summary>
    private bool L47Mossy(byte w, int gx, int gz, int rel, int ground) =>
        w != W.L47BarkDead
            ? rel <= ground + 1 + (int)(3 * L47Unit(gx, gz, 5)) || Noise2(gx / 4.0 + rel / 9.0, gz / 4.0 - rel / 11.0, SaltL47Mat + 2) > 0.42
            : rel <= ground + 1;

    // ================= Round 4: the forest's models =================

    /// <summary>A column's wood (<see cref="WorldLayout.L47Wood"/>) and ground, worked out once a thread for the column and its neighbours.</summary>
    private sealed class L47WoodCache
    {
        public WorldGenerator Owner;
        public readonly System.Collections.Generic.Dictionary<(int, int), (byte[] Wood, int Ground)> Map = new();
    }

    [ThreadStatic] private static L47WoodCache l47WoodCache;

    private (byte[] Wood, int Ground) L47WoodAt(int gx, int gz)
    {
        var cache = l47WoodCache ??= new L47WoodCache();
        if (cache.Owner != this || cache.Map.Count > 24000)
        {
            cache.Map.Clear();
            cache.Owner = this;
        }
        if (cache.Map.TryGetValue((gx, gz), out var hit)) return hit;
        var wood = new byte[L47Height];
        layout.L47Wood(gx, gz, L47Low, wood);
        var e = (wood, layout.L47Ground(gx, gz));
        cache.Map[(gx, gz)] = e;
        return e;
    }

    /// <summary>The way a way-stone at a column faces: toward the trail beside it (its side index).</summary>
    private int L47FaceTrail(int gx, int gz)
    {
        layout.L47TrailDistance(gx + 0.5, gz + 0.5, out double phi);
        var (tx, tz) = layout.L47TrailPoint(phi);
        double dx = tx - (gx + 0.5), dz = tz - (gz + 0.5);
        return Math.Abs(dx) > Math.Abs(dz) ? (dx > 0 ? 1 : 3) : (dz > 0 ? 2 : 0);
    }

    private static bool L47Solid(byte k) => W.L47IsBark(k) || k == W.L47Stone;

    /// <summary>The fillet's bark (<see cref="L47FilletBarks"/>) matching a neighbour's block at a height.</summary>
    private int L47FilletBark(byte w, int nx, int nz, int rel, (byte[] Wood, int Ground) n)
    {
        if (w == W.L47Stone)
        {
            int above = rel + 1 - L47Low;
            return above < L47Height && n.Wood[above] == 0 ? 13 : 12;
        }
        int k = w - W.L47BarkOak;
        return L47Mossy(w, nx, nz, rel, n.Ground) ? k + 6 : k;
    }

    /// <summary>
    /// Dresses a forest column (round 4): in every notch of a trunk's, root's, limb's or boulder's stepped outline (wood on two
    /// sides and the corner between) a chamfer of the same bark, so the outlines run round; moss drapes on the bark faces
    /// beside it (mostly the north faces: the damp side), bracket fungi, and clumps of mushrooms by the wood and on the logs.
    /// </summary>
    private void L47Dress(L47Column c, int gx, int gz, int ground, bool path)
    {
        if (l47Fillet[0, 0] == 0) return;
        int[] b = c.Blocks;
        var n = L47WoodAt(gx, gz - 1);
        var e = L47WoodAt(gx + 1, gz);
        var s = L47WoodAt(gx, gz + 1);
        var w = L47WoodAt(gx - 1, gz);
        (byte[] Wood, int Ground) ne = default, se = default, sw = default, nw = default;
        bool diag = false;
        int topWood = Math.Min(W.L47Top, ground + 44);
        for (int rel = ground + 1; rel <= topWood; rel++)
        {
            int i = rel - L47Low;
            if (b[i] != 0 || c.Water[i]) continue;
            byte kn = n.Wood[i], ke = e.Wood[i], ks = s.Wood[i], kw = w.Wood[i];
            bool sn = L47Solid(kn), sE = L47Solid(ke), sS = L47Solid(ks), sW = L47Solid(kw);
            if (sn || sE || sS || sW)
            {
                if ((sn && sE || sE && sS || sS && sW || sW && sn) && !diag)
                {
                    ne = L47WoodAt(gx + 1, gz - 1);
                    se = L47WoodAt(gx + 1, gz + 1);
                    sw = L47WoodAt(gx - 1, gz + 1);
                    nw = L47WoodAt(gx - 1, gz - 1);
                    diag = true;
                }
                int corner = -1, bark = 0;
                if (sn && sE && L47Solid(ne.Wood[i])) { corner = 0; bark = L47FilletBark(kn, gx, gz - 1, rel, n); }
                else if (sE && sS && L47Solid(se.Wood[i])) { corner = 1; bark = L47FilletBark(ke, gx + 1, gz, rel, e); }
                else if (sS && sW && L47Solid(sw.Wood[i])) { corner = 2; bark = L47FilletBark(ks, gx, gz + 1, rel, s); }
                else if (sW && sn && L47Solid(nw.Wood[i])) { corner = 3; bark = L47FilletBark(kw, gx - 1, gz, rel, w); }
                if (corner >= 0)
                {
                    b[i] = l47Fillet[bark, corner];
                    continue;
                }
                if (rel <= ground + 16)
                {
                    // A drape or a bracket on a bark face beside this block: the faces tried north side first (the bark to
                    // the south: the drape faces north), then east, south, west
                    for (int f = 0; f < 4 && b[i] == 0; f++)
                    {
                        byte k = f switch { 0 => ks, 1 => kw, 2 => kn, _ => ke };
                        if (!W.L47IsBark(k)) continue;
                        var (nx, nz, nb) = f switch { 0 => (gx, gz + 1, s), 1 => (gx - 1, gz, w), 2 => (gx, gz - 1, n), _ => (gx + 1, gz, e) };
                        bool mossy = L47Mossy(k, nx, nz, rel, nb.Ground);
                        double u = L47Unit(gx, gz * 7 + rel, 20 + f);
                        double drape = mossy ? (f == 0 ? 0.5 : 0.14) : (f == 0 ? 0.05 : 0.015);
                        if (u < drape) b[i] = l47Drape[rel <= ground + 2 ? 0 : 1, f];
                        else if (rel >= ground + 2 && rel <= ground + 10 && u > 1 - (k == W.L47BarkDead ? 0.12 : 0.025))
                            b[i] = l47Bracket[(k is W.L47BarkOak or W.L47BarkDead) && L47Unit(gx, gz * 7 + rel, 25) < 0.35 ? 1 : 0, f];
                    }
                    if (b[i] != 0) continue;
                }
            }
            // Mushrooms: a clump on the floor by the wood, or on top of a fallen log
            if (path) continue;
            byte under = c.Wood[i - 1];
            bool onLog = under is >= W.L47LogOakX and <= W.L47LogDeadZ && b[i - 1] != 0;
            bool byWood = rel == ground + 1 && (sn || sE || sS || sW || kn >= W.L47LogOakX && kn <= W.L47LogDeadZ || ke >= W.L47LogOakX && ke <= W.L47LogDeadZ
                || ks >= W.L47LogOakX && ks <= W.L47LogDeadZ || kw >= W.L47LogOakX && kw <= W.L47LogDeadZ);
            if (!onLog && !byWood) continue;
            double m = L47Unit(gx, gz * 7 + rel, 26);
            if (m < (onLog ? 0.07 : 0.035))
            {
                double kind = L47Unit(gx, gz * 7 + rel, 27);
                bool deadWood = onLog || kn == W.L47BarkDead || ke == W.L47BarkDead || ks == W.L47BarkDead || kw == W.L47BarkDead;
                b[i] = l47Mush[deadWood ? (kind < 0.6 ? 1 : 2) : (kind < 0.55 ? 0 : kind < 0.8 ? 1 : 2)];
            }
        }
    }

    /// <summary>The top of the forest floor: moss in broad carpets, leaf litter in drifts, bare humus between.</summary>
    private int L47GroundTop(int gx, int gz)
    {
        double n = Noise2(gx / 11.0, gz / 11.0, SaltL47Mat + 3);
        if (n > -0.15) return l47Moss;
        if (n < -0.45) return l47Humus;
        return l47Litter;
    }

    /// <summary>What grows on a column of open forest floor: ferns in drifts, mushrooms by the wood (most good to eat), fallen sticks, a little grass, a rare flower.</summary>
    private void L47Undergrowth(int[] b, int gx, int gz, int ground)
    {
        int at = ground + 1 - L47Low;
        double u = L47Unit(gx, gz, 8);
        double drift = Noise2(gx / 9.0, gz / 9.0, SaltL47Mat + 4);
        if (u < (drift > 0.25 ? 0.32 : 0.05) && l47Ferns.Length > 0) { b[at] = l47Ferns[(int)(L47Unit(gx, gz, 9) * l47Ferns.Length)]; return; }
        if (u < 0.5 && L47Unit(gx, gz, 10) < 0.09 && L47NextToWood(gx, gz))
        {
            int[] set = L47Unit(gx, gz, 11) < 0.3 ? l47Toadstools : l47Mushrooms;
            if (set.Length > 0) b[at] = set[(int)(L47Unit(gx, gz, 12) * set.Length)];
            return;
        }
        if (u > 0.985 && l47Stick != 0) { b[at] = l47Stick; return; }
        if (u > 0.955) { b[at] = l47ShortGrass; return; }
        if (u > 0.951 && l47Flowers.Length > 0) b[at] = l47Flowers[(int)(L47Unit(gx, gz, 13) * l47Flowers.Length)];
    }

    /// <summary>Whether a column of floor has wood standing beside it at the height one walks (a trunk, root or log).</summary>
    private bool L47NextToWood(int gx, int gz)
    {
        foreach (var (dx, dz) in Neighbours4)
            if (layout.TileAt(gx + dx, gz + dz).Kind == TileKind.Wall) return true;
        return false;
    }

    /// <summary>Hangs a strand of old man's beard down from a height, as far as it can go with room under it.</summary>
    private void L47Hang(int[] b, int from, int length, int floor)
    {
        if (l47Lichen[0] == 0) return;
        int lowest = Math.Max(floor + 3, from - length + 1);
        if (lowest > from) return;
        for (int rel = from; rel >= lowest; rel--)
        {
            int i = rel - L47Low;
            if (b[i] != 0) return;
            b[i] = rel == from ? l47Lichen[0] : rel == lowest ? l47Lichen[2] : l47Lichen[1];
        }
    }

    /// <summary>The block of a glade kind (WorldLayout.L47GladeBlock's codes) at a place.</summary>
    private int L47GladeId(int code, int gx, int gz, int rel)
    {
        int f = Facing(W.L47GladeFacing(code));
        return (code & 0xFF) switch
        {
            W.L47GStone => rel <= 3 && L47Unit(gx, gz * 31 + rel, 14) < 0.45 ? l47ManorMoss : l47ManorStone,
            W.L47GPlinth => l47Plinth,
            W.L47GTimber => l47Timber,
            W.L47GSlate => l47Slate,
            W.L47GBoards => l47Boards,
            W.L47GWindow => l47Window,
            W.L47GMegalith => rel <= 2 || Noise2(gx / 3.0 + rel / 5.0, gz / 3.0, SaltL47Mat + 5) > 0.35 ? l47MegalithMoss : l47Megalith,
            W.L47GAltar => l47Megalith,
            W.L47GFlag => l47Flag,
            W.L47GLadder => l47Ladder,
            W.L47GTable => l47Table,
            W.L47GShelf => l47Shelf[f],
            W.L47GBannerTop => l47Banner[0, f],
            W.L47GBannerFoot => l47Banner[1, f],
            W.L47GLantern => l47Lantern,
            W.L47GBrazier => l47Brazier,
            W.L47GHearth => l47Hearth,
            W.L47GCandles => l47Candles,
            W.L47GGrass => l47GrassSoil,
            // (Round 4)
            W.L47GRoofSlope or W.L47GRoofEave or W.L47GRoofRidge or W.L47GRoofGable => l47Roof[(code & 0xFF) - W.L47GRoofSlope, f == 2 ? 1 : 0],
            W.L47GLeaded => l47Leaded[Math.Min(2, W.L47GladePart(code) & 3), W.L47GladePart(code) >> 2 & 1],
            W.L47GDoor => l47Door[W.L47GladePart(code) & 1, (W.L47GladePart(code) >> 1 & 1) * 3 + Math.Min(2, W.L47GladePart(code) >> 2)],
            W.L47GJamb => l47Jamb[W.L47GladePart(code) & 1, W.L47GladePart(code) >> 1 & 1],
            W.L47GBookcase => l47Bookcase[W.L47GladePart(code) & 1, W.L47GladePart(code) >> 1 & 1, f],
            W.L47GFire => l47Fire[f],
            W.L47GMantel => l47Mantel[Math.Min(2, W.L47GladePart(code)), f],
            W.L47GTrestle => l47Trestle[Math.Min(2, W.L47GladePart(code))],
            W.L47GBench => l47Bench[Math.Min(1, W.L47GladePart(code))],
            W.L47GTapestry => l47Tapestry[W.L47GladePart(code) & 3, f],
            W.L47GSconce => l47Sconce[f],
            W.L47GPot => l47Pot,
            W.L47GPorchPost => l47PorchPost[Math.Min(2, W.L47GladePart(code))],
            W.L47GOffering => l47Offering[Math.Min(2, W.L47GladePart(code))],
            W.L47GLampPost => l47LampPost[Math.Min(1, W.L47GladePart(code)), f],
            W.L47GSarsenTop => l47SarsenTop != 0 ? l47SarsenTop : l47Megalith,
            W.L47GStore => W.L47GladePart(code) switch { 0 => l47Chest73[f], 1 => l47Sacks73[f], 2 => l47Barrel23, _ => l47Crate23 },
            _ => 0,
        };
    }
}
