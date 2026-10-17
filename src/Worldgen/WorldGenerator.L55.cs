using Part = Backrooms.Worldgen.WorldLayout.L55Part;
using Thing = Backrooms.Worldgen.WorldLayout.L55Thing;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 55, "Land of Ice" (experimental, kept as level 25), laid out in WorldLayout.Level55.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>), the ice sheet's datum. The snowfield is vanilla snow (a few snow layers softening
/// its steps) or wind crust over packed glacier ice; steep faces, crevasse walls and the cave's dome are deep blue ice, the
/// cave's walls and ceiling glowing faintly; crevasse floors are soft snow, and some crevasses are bridged by a single
/// block of it. The frozen sea is vanilla lake ice over glacier ice over rock, with pressure ridges of glacier ice. The rim
/// is a cliff of rime-coated rock. The research hut is frosted planks under a snow-covered roof, with a stove of embers in
/// a stone box, two bunks, a table and chairs and four iron lamps. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l55Snow, l55Packed, l55Glacier, l55LakeIce, l55Rock, l55Crust, l55Blue, l55Glow, l55Rime, l55Plank, l55Boards, l55Glass,
        l55Stone, l55Ember;
    private readonly int[] l55Layer = new int[4];
    private readonly int[] l55Lamp = new int[4];

    /// <summary>How deep the ice goes below the datum (below this, the ground as vanilla laid it), and how high the rim's cliff rises.</summary>
    private const int L55Bottom = -14, L55RimTop = 18;

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL55()
    {
        l55Snow = GameId("game:snowblock");
        for (int i = 1; i <= 3; i++) l55Layer[i] = GameId($"game:snowlayer-{i}");
        l55Packed = GameId("game:packedglacierice", "game:glacierice");
        l55Glacier = GameId("game:glacierice");
        l55LakeIce = GameId("game:lakeice");
        l55Rock = GameId("game:rock-granite");
        l55Stone = GameId("game:cobblestone-granite", "game:rock-granite");
        l55Ember = GameId("game:ember");
        l55Glass = GameId("game:glass-plain");
        l55Boards = BlockId("game:planks-aged-ud");
        l55Crust = Id("l55-windcrust");
        l55Blue = Id("l55-blueice");
        l55Glow = Id("l55-glowice");
        l55Rime = Id("l55-rimecliff");
        l55Plank = Id("l55-frostplank");
        for (int f = 0; f < 4; f++) l55Lamp[f] = Id("l55-lamp-" + Sides[f]);
        floorIds[(int)FloorKind.L55Floor] = l55Snow;
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above the ice sheet's datum.</summary>
    private int Level55Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < L55Bottom) return concreteId; // (the ground below, as vanilla laid it)
        byte flags = t.Detail;
        switch (t.Zone)
        {
            case WorldLayout.L55RimZone:
                return rel <= L55RimTop ? l55Rime : rel == L55RimTop + 1 ? l55Snow : 0;
            case WorldLayout.L55Hut:
                return L55HutBlock(gx, gz, rel);
            case WorldLayout.L55Sea:
            {
                bool ridge = (flags & WorldLayout.L55FlagRidge) != 0;
                int top = ridge ? 0 : -t.Depth;
                if (rel > top) return 0;
                if (rel == top) return ridge ? l55Glacier : l55LakeIce;
                return rel >= top - 2 ? l55Glacier : l55Rock;
            }
            case WorldLayout.L55Crevasse:
            {
                int lip = t.Height, floor = lip - t.Depth;
                if (rel > lip) return 0;
                if (rel == lip && (flags & WorldLayout.L55FlagBridge) != 0) return l55Snow;
                if (rel > floor) return 0;
                return rel == floor ? l55Snow : l55Blue;
            }
            case WorldLayout.L55Cave:
            {
                int top = t.Height;
                if (rel > top) return 0;
                if (rel <= WorldLayout.L55CaveFloor) return l55Blue;
                if (t.Depth == 0) return 0; // (the open cut: nothing over its floor)
                if (rel < t.Depth) return 0;
                if (rel == t.Depth) return l55Glow;
                if (rel == top) return (flags & WorldLayout.L55FlagCrust) != 0 ? l55Crust : l55Snow;
                return rel == top - 1 ? l55Crust : l55Blue;
            }
        }

        // The snowfield and the glacier
        int g = t.Height;
        if (rel > g) return rel == g + 1 && t.Depth is > 0 and <= 3 ? l55Layer[t.Depth] : 0;
        if ((flags & WorldLayout.L55FlagCaveWall) != 0 && rel > WorldLayout.L55CaveFloor && rel <= WorldLayout.L55CaveFloor + 8 && rel < g - 1) return l55Glow;
        bool deepBlue = (flags & (WorldLayout.L55FlagMound | WorldLayout.L55FlagCrevWall)) != 0;
        if ((flags & WorldLayout.L55FlagSteep) != 0) return rel >= g - 2 || deepBlue ? l55Blue : l55Packed;
        if (rel == g) return (flags & WorldLayout.L55FlagCrust) != 0 ? l55Crust : l55Snow;
        if (rel >= g - 2) return l55Crust;
        return deepBlue ? l55Blue : l55Packed;
    }

    /// <summary>The research hut, from its hut-local position and the height above its floor.</summary>
    private int L55HutBlock(int gx, int gz, int rel)
    {
        int u = gx - layout.L55HutX0, v = gz - layout.L55HutZ0;
        Part part = WorldLayout.L55HutAt(u, v);
        int c = rel - WorldLayout.L55HutFloor;
        if (c < 0) return rel >= L55Bottom ? l55Packed : concreteId;
        bool stove = part == Part.Stove;
        if (c == 0) return part is Part.Room or Part.Stove ? l55Boards : l55Plank;
        const int roof = WorldLayout.L55HutRoof;
        if (c > roof)
        {
            // Snow on the roof, the stove's chimney through it
            if (stove) return c <= roof + 2 ? l55Stone : 0;
            return c == roof + 1 ? l55Snow : 0;
        }
        if (c == roof) return stove ? l55Stone : l55Plank;
        switch (part)
        {
            case Part.Wall: return l55Plank;
            case Part.Window: return c is 2 or 3 ? l55Glass : l55Plank;
            case Part.Door: return c <= 3 ? 0 : l55Plank;
            case Part.Stove: return c == 2 ? l55Ember : l55Stone; // embers in a stone box, the hood over them
        }
        var (thing, facing) = WorldLayout.L55FurnishingAt(u, v);
        if (thing == Thing.Lamp) return c == 3 ? l55Lamp[Facing(facing)] : 0;
        if (c != 1) return 0;
        return thing switch
        {
            Thing.Table => PropBlock(new Tile { Variant = Props.RoundTable, Pier = facing }),
            Thing.Chair => PropBlock(new Tile { Variant = Props.HotelChair, Pier = facing }),
            // Beds are modelled head to the north; the facing points from the head toward the foot
            Thing.BedHead => bedHeadIds[Facing(Opposite(facing))],
            Thing.BedFoot => bedFootIds[Facing(Opposite(facing))],
            _ => 0,
        };
    }
}
