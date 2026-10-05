using System;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Map;

/// <summary>Turns a block column into a map pixel. Pixels are ABGR ints, as the map textures expect.</summary>
public static class MapColors
{
    private static readonly int Wall = Rgb(0x4B3D1C);
    private static readonly int Obstacle = Rgb(0x6B5A2C);
    private static readonly int SupplyBox = Rgb(0xC0392B);
    private static readonly int Pit = Rgb(0x141210);
    private static readonly int Water = Rgb(0x3D6E92);
    private static readonly int Carpet = Rgb(0xB09C5C);
    private static readonly int CarpetStained = Rgb(0x8E7C44);
    private static readonly int OtherFloor = Rgb(0x9A9890);
    private static readonly int Chalk = Rgb(0xF6F6F0);
    private static readonly int Vegetation = Rgb(0x2F5A2A);
    private static readonly int Grass = Rgb(0x5E8040);
    private static readonly int Field = Rgb(0x7A5C38);
    private static readonly int Road = Rgb(0x7C746A);
    private static readonly int Asphalt = Rgb(0x48494C);
    private static readonly int Pavement = Rgb(0xA9A69E);
    private static readonly int Sand = Rgb(0xB8A77A);
    private static readonly int HouseFloor = Rgb(0xA88A64);
    private static readonly int CaveFloor = Rgb(0x6E6A66);
    private static readonly int Tar = Rgb(0x1E1A16);

    /// <summary>
    /// Classifies the column at x, z, standing on the floor block at <paramref name="floorY"/>. A doorway (open at
    /// head height with a lintel at <paramref name="lintelY"/>) is shaded a little darker.
    /// </summary>
    public static int Classify(IBlockAccessor blockAccessor, int floorY, int lintelY, BlockPos tmpPos, int x, int z, int lightLevel)
    {
        Block eye = blockAccessor.GetBlock(tmpPos.Set(x, floorY + 2, z));
        Block feet = blockAccessor.GetBlock(tmpPos.Set(x, floorY + 1, z));
        // Surveyor's chalk shows up bright white: in the dark of Level 6 it is the trail you can trust
        if (IsChalk(eye) || IsChalk(feet) || IsChalk(blockAccessor.GetBlock(tmpPos.Set(x, floorY + 3, z)))) return Chalk;
        if (IsSolid(eye)) return IsPlant(eye) ? Vegetation : Wall;

        if (feet.Code?.Path is "supplybox" or "crate") return SupplyBox;
        if (IsSolid(feet)) return IsPlant(feet) ? Vegetation : Obstacle;

        Block floor = blockAccessor.GetBlock(tmpPos.Set(x, floorY, z));
        if (blockAccessor.GetBlock(tmpPos, BlockLayersAccess.Fluid).BlockId != 0
            || blockAccessor.GetBlock(tmpPos.Set(x, floorY + 1, z), BlockLayersAccess.Fluid).BlockId != 0) return Water;
        if (floor.BlockId == 0) return Pit;

        int color = FloorColor(floor);

        // A doorway: open at head height but with a lintel above
        Block lintel = blockAccessor.GetBlock(tmpPos.Set(x, lintelY, z));
        float shade = IsSolid(lintel) && !IsPlant(lintel) ? 0.82f : 1f;

        // Shade by light level so lit rooms, dim corners and dead zones read at a glance
        shade *= 0.45f + 0.55f * Math.Clamp(lightLevel / 16f, 0f, 1f);
        return Scale(color, shade);
    }

    private static int FloorColor(Block floor)
    {
        string path = floor.Code?.Path ?? "";
        if (path.StartsWith("carpet")) return path.EndsWith("stained") ? CarpetStained : Carpet;
        if (path.StartsWith("soil-")) return Grass;
        if (path.StartsWith("farmland")) return Field;
        if (path.StartsWith("gravel") || path.StartsWith("dirtroad") || path.StartsWith("muddygravel")) return Road;
        if (path.StartsWith("asphalt")) return Asphalt;
        if (path.StartsWith("sidewalk") || path.StartsWith("cityfloor-plaza") || path.StartsWith("subwayfloor-platform")) return Pavement;
        if (path.StartsWith("seabed") || path.StartsWith("islandrock")) return Sand;
        if (path.StartsWith("housefloor")) return HouseFloor;
        if (path.StartsWith("rock-") || path.StartsWith("ore-")) return CaveFloor;
        if (path.StartsWith("tar")) return Tar;
        return OtherFloor;
    }

    private static bool IsPlant(Block block)
    {
        string path = block.Code?.Path ?? "";
        return path.StartsWith("leaves") || path.StartsWith("log-");
    }

    private static bool IsChalk(Block block) => block.Code?.Domain == "backrooms" && block.Code.Path.StartsWith("chalkmark");

    private static bool IsSolid(Block block) => block.BlockId != 0 && block.CollisionBoxes != null && block.CollisionBoxes.Length > 0;

    /// <summary>0xRRGGBB to an opaque ABGR int.</summary>
    private static int Rgb(int rgb) => unchecked((int)0xFF000000) | ((rgb & 0xFF) << 16) | (rgb & 0xFF00) | ((rgb >> 16) & 0xFF);

    private static int Scale(int abgr, float factor)
    {
        int r = Math.Min(255, (int)((abgr & 0xFF) * factor));
        int g = Math.Min(255, (int)(((abgr >> 8) & 0xFF) * factor));
        int b = Math.Min(255, (int)(((abgr >> 16) & 0xFF) * factor));
        return unchecked((int)0xFF000000) | (b << 16) | (g << 8) | r;
    }
}
