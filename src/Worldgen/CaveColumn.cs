using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 8's noise, worked out once for a whole column of blocks rather than once per block. The cave and ore noises
/// are smooth value noise: between two lattice layers a column's value only interpolates, so the few lattice layers
/// a column crosses are hashed once each and every block in the column is answered from them. A chunk's worth of
/// columns is kept, since a block asks about its neighbours above, below and beside it.
/// </summary>
internal sealed class CaveColumn
{
    /// <summary>One 3D value noise along a column: its lattice layers, and the column's position within the lattice cell.</summary>
    private sealed class Noise
    {
        private readonly double[] layers;
        private readonly int firstLayer;
        private readonly double scaleY;

        public Noise(ulong seed, int gx, int gz, double scaleX, double scaleY, double scaleZ, ulong salt, int yMin, int yMax)
        {
            this.scaleY = scaleY;
            double x = gx / scaleX, z = gz / scaleZ;
            int x0 = (int)Math.Floor(x), z0 = (int)Math.Floor(z);
            double fx = x - x0, fz = z - z0;
            double sx = fx * fx * (3 - 2 * fx), sz = fz * fz * (3 - 2 * fz);
            firstLayer = (int)Math.Floor(yMin / scaleY);
            int lastLayer = (int)Math.Floor(yMax / scaleY) + 1;
            layers = new double[lastLayer - firstLayer + 1];
            for (int i = 0; i < layers.Length; i++)
            {
                ulong s = salt + (ulong)((firstLayer + i) * 0x9E3779B1L);
                double c00 = Corner(seed, x0, z0, s), c10 = Corner(seed, x0 + 1, z0, s), c01 = Corner(seed, x0, z0 + 1, s), c11 = Corner(seed, x0 + 1, z0 + 1, s);
                double top = c00 + (c10 - c00) * sx, bottom = c01 + (c11 - c01) * sx;
                layers[i] = top + (bottom - top) * sz;
            }
        }

        private static double Corner(ulong seed, int x, int z, ulong salt) => Hashing.Unit(Hashing.Hash(seed, x, z, salt)) * 2 - 1;

        /// <summary>The noise at a height: smooth 3D value noise in roughly [-1, 1], as the generator always had.</summary>
        public double At(int y)
        {
            double yy = y / scaleY;
            int y0 = (int)Math.Floor(yy);
            double fy = yy - y0, sy = fy * fy * (3 - 2 * fy);
            int i = Math.Clamp(y0 - firstLayer, 0, layers.Length - 2);
            return layers[i] + (layers[i + 1] - layers[i]) * sy;
        }
    }

    private readonly int floorY;
    private readonly Noise chamber, detail, tube, ore;

    /// <summary>How far the strata are shifted here (the rock layers undulate).</summary>
    public readonly int StrataShift;
    /// <summary>Whether a flooded pocket may lie here, whether tar pools here, whether a coal seam runs up this column.</summary>
    public readonly bool Pool, Tar, CoalSeam;

    public CaveColumn(ulong seed, int gx, int gz, int floorY, int yMin, int yMax, Func<double, double, ulong, double> noise2, ulong saltCave, ulong saltTube, ulong saltStrata, ulong saltOre, ulong saltPool)
    {
        this.floorY = floorY;
        chamber = new Noise(seed, gx, gz, 26, 11, 26, saltCave, yMin - 1, yMax + 1);
        detail = new Noise(seed, gx, gz, 10, 6, 10, saltCave + 1, yMin - 1, yMax + 1);
        tube = new Noise(seed, gx, gz, 38, 14, 38, saltTube, yMin - 1, yMax + 1);
        ore = new Noise(seed, gx, gz, 6, 4, 6, saltOre, yMin - 1, yMax + 1);
        StrataShift = (int)(9 * noise2(gx / 70.0, gz / 70.0, saltStrata));
        Pool = noise2(gx / 30.0, gz / 30.0, saltPool) > 0.2;
        Tar = noise2(gx / 25.0, gz / 25.0, saltPool + 3) > 0.62;
        CoalSeam = Hashing.Mod(gx + 3 * gz, 197) == 0 && noise2(gx / 50.0, gz / 50.0, saltOre + 9) > 0.2;
    }

    /// <summary>Caves: big chambers where two noises agree, and long winding tubes along a third's zero.</summary>
    public bool IsCave(int y)
    {
        int rel = y - floorY;
        if (rel > 8 || rel < -62) return false;
        double fade = rel > 4 ? (rel - 4) * 0.08 : rel < -50 ? (-50 - rel) * 0.05 : 0;
        if (chamber.At(y) + 0.45 * detail.At(y) - fade > 0.42) return true;
        return Math.Abs(tube.At(y)) + fade < 0.055;
    }

    public double Ore(int y) => ore.At(y);
}

/// <summary>The columns of the chunk being generated and its margin, by position.</summary>
internal sealed class CaveColumns
{
    private const int Capacity = 6000;
    private readonly Dictionary<long, CaveColumn> columns = new();
    private readonly Func<int, int, CaveColumn> build;
    // The column asked about last: a block asks about its own column several times over (one reference, so a
    // generator thread never sees a key with another's column)
    private sealed record Hit(long Key, CaveColumn Column);
    private Hit last;

    public CaveColumns(Func<int, int, CaveColumn> build) => this.build = build;

    public CaveColumn Get(int gx, int gz)
    {
        long key = ((long)gx << 32) | (uint)gz;
        Hit hit = last;
        if (hit != null && hit.Key == key) return hit.Column;
        CaveColumn column;
        lock (columns)
        {
            columns.TryGetValue(key, out column);
        }
        if (column == null)
        {
            column = build(gx, gz);
            lock (columns)
            {
                if (columns.Count >= Capacity) columns.Clear();
                columns[key] = column;
            }
        }
        last = new Hit(key, column);
        return column;
    }
}
