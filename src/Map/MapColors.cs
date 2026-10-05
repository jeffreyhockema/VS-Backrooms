using System;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Backrooms.Worldgen;

namespace Backrooms.Map;

/// <summary>Turns a Level 0 block column into a map pixel. Pixels are ABGR ints, as the map textures expect.</summary>
public static class MapColors
{
    private static readonly int Wall = Rgb(0x4B3D1C);
    private static readonly int Obstacle = Rgb(0x6B5A2C);
    private static readonly int SupplyBox = Rgb(0xC0392B);
    private static readonly int Pit = Rgb(0x141210);
    private static readonly int Water = Rgb(0x4A5A55);
    private static readonly int Carpet = Rgb(0xB09C5C);
    private static readonly int CarpetStained = Rgb(0x8E7C44);
    private static readonly int OtherFloor = Rgb(0x9A9890);

    public static int Classify(IBlockAccessor blockAccessor, WorldGeometry geometry, BlockPos tmpPos, int x, int z, int lightLevel)
    {
        Block eye = blockAccessor.GetBlock(tmpPos.Set(x, geometry.EyeY, z));
        if (IsSolid(eye)) return Wall;

        Block feet = blockAccessor.GetBlock(tmpPos.Set(x, geometry.FloorY + 1, z));
        if (feet.Code?.Path is "supplybox" or "crate") return SupplyBox;
        if (IsSolid(feet)) return Obstacle;

        Block floor = blockAccessor.GetBlock(tmpPos.Set(x, geometry.FloorY, z));
        if (floor.BlockId == 0)
        {
            Block fluid = blockAccessor.GetBlock(tmpPos, BlockLayersAccess.Fluid);
            return fluid.BlockId != 0 ? Water : Pit;
        }

        string path = floor.Code?.Path ?? "";
        int color = path.StartsWith("carpet") ? (path.EndsWith("stained") ? CarpetStained : Carpet) : OtherFloor;

        // A doorway: open at head height but with a lintel above
        Block lintel = blockAccessor.GetBlock(tmpPos.Set(x, geometry.CeilingY - 1, z));
        float shade = IsSolid(lintel) ? 0.82f : 1f;

        // Shade by light level so lit rooms, dim corners and dead zones read at a glance
        shade *= 0.45f + 0.55f * Math.Clamp(lightLevel / 16f, 0f, 1f);
        return Scale(color, shade);
    }

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
