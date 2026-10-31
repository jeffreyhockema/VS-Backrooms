using System;

namespace Backrooms.Worldgen;

public sealed partial class WorldLayout
{
    /// <summary>How a run of Level 1's ceiling conduit ends at one side.</summary>
    public const int ConduitGoesOn = 0, ConduitCap = 1, ConduitBox = 2;

    /// <summary>
    /// How the conduit in a column ends at each end of its run, used from layout version 9 (before that the bare tubes
    /// were left as they stood): along the run's axis (X for <c>ConduitX</c>) the end toward lower coordinates, then the
    /// end toward higher ones, each <see cref="ConduitGoesOn"/> where the next column's conduit carries on,
    /// <see cref="ConduitBox"/> where the run meets a wall, a doorway or a beam (it goes into a junction box mounted on
    /// it) and <see cref="ConduitCap"/> where there is open space or a light beyond (a capped end with a collar).
    /// </summary>
    public static (int Low, int High) ConduitEnds(Func<int, int, Tile> at, int gx, int gz, out string why)
    {
        Tile t = at(gx, gz);
        bool x = t.Pipe == Pipes.ConduitX;
        int a = ConduitEnd(at, t, x ? gx - 1 : gx, x ? gz : gz - 1, x, out string wa);
        int b = ConduitEnd(at, t, x ? gx + 1 : gx, x ? gz : gz + 1, x, out string wb);
        why = (a == 0 ? "" : wa) + (a != 0 && b != 0 ? " + " : "") + (b == 0 ? "" : wb);
        if (why.Length == 0) why = "run";
        return (a, b);
    }

    private static int ConduitEnd(Func<int, int, Tile> at, in Tile t, int nx, int nz, bool x, out string why)
    {
        Tile n = at(nx, nz);
        why = "";
        if (n.Pipe == (x ? Pipes.ConduitX : Pipes.ConduitZ) && n.Kind == TileKind.Floor && n.Level == t.Level && !n.Beam) return ConduitGoesOn;
        if (n.IsWallLike) { why = n.Kind == TileKind.Wall ? "wall" : "doorway"; return ConduitBox; }
        if (n.Beam) { why = "beam"; return ConduitBox; }
        why = n.Ceiling != CeilingKind.Tile ? "light" : n.Pipe != Pipes.None ? "other pipe" : "open";
        return ConduitCap;
    }
}
