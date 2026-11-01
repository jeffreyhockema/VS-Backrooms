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
            }
            else if (!trail && L47Unit(gx, gz, 2) < 0.04)
            {
                b[-L47Low] = l47BoulderMoss;
                c.Water[-L47Low] = false;
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
        layout.L47Wood(gx, gz, L47Low, c.Wood);
        // Moss climbs a block or three up every trunk, and in patches higher on it
        int mossBand = ground + 1 + (int)(3 * L47Unit(gx, gz, 5));
        for (int i = 0; i < L47Height; i++)
        {
            byte w = c.Wood[i];
            if (w == 0) continue;
            int rel = i + L47Low;
            if (glade && rel <= ground + 2) continue;
            if (rel <= ground && !W.L47IsBark(w)) continue;
            int id = l47Kind[w];
            if (W.L47IsBark(w) && w != W.L47BarkDead && (rel <= mossBand || Noise2(gx / 4.0 + rel / 9.0, gz / 4.0 - rel / 11.0, SaltL47Mat + 2) > 0.42))
                id = l47MossBark[w];
            else if (w == W.L47BarkDead && rel <= ground + 1) id = l47MossBark[w];
            b[i] = id;
            c.Water[i] = false;
        }
        // The tops of the boulders mossed over
        for (int i = 0; i < L47Height - 1; i++)
            if (b[i] == l47Boulder && b[i + 1] == 0 && i + L47Low > ground - 1) b[i] = l47BoulderMoss;
        // A hollow tree's floor: leaf litter blown in, not the cut end of its bark
        if (t.Under is Unders.L47DeadHollow or Unders.L47StillHollow or Unders.L47GreenHollow && ground >= L47Low) b[ground - L47Low] = l47Litter;

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

        // ---- A supply box ----
        if (t.SupplyBox && !glade && ground + 1 <= W.L47Top) b[ground + 1 - L47Low] = BoxOf(t);
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
            _ => 0,
        };
    }
}
