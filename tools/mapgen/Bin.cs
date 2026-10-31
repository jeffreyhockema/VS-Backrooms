/// <summary>
/// The harness's <c>.bin</c> files keep one byte per tile field. WallPattern, FloorKind, CeilingKind, Under, Overhead and
/// Pipe are ushorts since 0.700.0-pre.1 (the experimental levels' values run past 255): they are written clamped to 255
/// (as Variant always was), so the readers (render*.py, shotbot's pick.py) keep their formats.
/// </summary>
static class Bin
{
    public static byte B(int value) => (byte)System.Math.Clamp(value, 0, 255);
}
