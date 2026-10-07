using Backrooms.Worldgen;

/// <summary>
/// Level 6 densities over the whole ring (sampled every few cells): the share of cells that are the Snackrooms, and
/// stairs down per hundred cells. Usage: mapgen seed 1 l6density
/// </summary>
static class Density
{
    public static void Run(WorldLayout layout, int smx, int smz)
    {
        int cells = 0, snack = 0;
        var stairs = new HashSet<(int, int)>();
        for (int mz = smz - 260; mz <= smz + 260; mz += 1)
            for (int mx = smx - 260; mx <= smx + 260; mx += 1)
            {
                if (layout.LevelAt(mx, mz) != 6) continue;
                cells++;
                if (layout.IsSnackrooms(mx, mz)) snack++;
                if ((mx + mz) % 5 == 0 && layout.NearestDescent(mx * 32 + 16, mz * 32 + 16, 40) is { } d) stairs.Add(d);
            }
        Console.WriteLine($"level 6: {cells} cells, Snackrooms {snack} ({100.0 * snack / cells:0.00}%), stairs down {stairs.Count} found ({100.0 * stairs.Count / cells:0.00} per 100 cells, lower bound)");
    }
}
