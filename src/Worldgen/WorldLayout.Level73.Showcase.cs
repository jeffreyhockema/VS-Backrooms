using System;
using System.Collections.Generic;
using System.Globalization;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>), all from the castle's place: the
    /// run up to the castle from the fields (the moon over it), the path and the gatehouse, Coran on the hill, the
    /// courtyard and the keep's front, the keep's rooms (the main hall, the dining hall with its table and hearth, a guest
    /// room, a bathroom, the gallery, the master bedroom), the roof terrace with the shut attic, the fields with their tors
    /// and dead grass, and the shore under the moon.
    /// </summary>
    public IEnumerable<Showcase.Spot> L73ShowcaseSpots(WorldGeometry geometry)
    {
        int floor = geometry.FloorFor(Level73);
        int x0 = L73CastleX0, z0 = L73CastleZ0;
        double mid = x0 + 28.0; // the middle of the gate and the path (between u 27 and 28)
        double gateZ = z0 + L73CastleD;
        // Feet on the ground of the island at a column, stepped along (dx, dz) until it is open land (not a tor, no prop)
        (double X, double Y, double Z) Ground(double x, double z, int dx = 0, int dz = 0)
        {
            for (int i = 0; i < 40; i++)
            {
                Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
                if (t.Zone == L73Land && t.Floor != FloorKind.L73Tor && t.Variant == 0 || dx == 0 && dz == 0)
                    return (x, floor + t.Height + 1, z);
                x += dx;
                z += dz;
            }
            return (x, floor + TileAt((int)Math.Floor(x), (int)Math.Floor(z)).Height + 1, z);
        }
        // Keep-local, on a storey (3 the roof terrace): feet on its floor
        (double X, double Y, double Z) Keep(double ku, double kv, int storey) =>
            (x0 + L73KeepU0 + ku, floor + L73Plateau + storey * L73Storey + 1, z0 + L73KeepV0 + kv);
        Showcase.Spot At((double X, double Y, double Z) p, string name, double heading, double pitch, string setup = null) =>
            new(name, p.X, p.Y, p.Z, heading, pitch, setup);

        // The run: out on the fields south of the gate, the castle on its hill ahead and the moon over it
        yield return At(Ground(mid + 0.5, gateZ + 72, 1, 0), "the-run", 0, 7);
        // The foot of the stone path ("follow the hard sensation on the bottom of your feet")
        yield return At(Ground(mid, gateZ + 25), "path-foot", 0, 9);
        // Coran on the hill below the gate, beside the path, facing whoever comes up it
        string coran = string.Format(CultureInfo.InvariantCulture, "/backrooms l73coran {0:0.#} {1:0.#} 165", mid + 3.5, gateZ + 25.5);
        yield return At(Ground(mid + 5, gateZ + 31), "coran", 345, 7, coran);
        // Coran close to (round 3: his idle look up close), on the path below the gate, facing whoever comes up it
        string coranClose = string.Format(CultureInfo.InvariantCulture, "/backrooms l73coran {0:0.#} {1:0.#} 180", mid + 0.5, gateZ + 12.5);
        yield return At(Ground(mid + 0.5, gateZ + 17.5), "coran-close", 0, 14, coranClose);
        // The gatehouse, close, its banners either side, the M.E.G.'s plate beside the gate
        yield return At(Ground(mid, gateZ + 7), "gatehouse", 350, 12);
        // The courtyard: the keep's front, its door, banners, the balcony over the door and the attic on the roof
        yield return At((mid, floor + L73Plateau + 1, z0 + L73CastleD - 4.5), "keep-front", 0, 22);
        // The keep's door close: its slate canopy, the M.E.G.'s plate beside it
        yield return At((mid, floor + L73Plateau + 1, z0 + L73KeepV0 + L73KeepD + 4.5), "keep-door", 0, 12);
        // Inside: the main hall from inside the door (the runner, the stair and its balustrade along the cross wall, the
        // lectern, tapestries, sofas, chandeliers under the beams)
        yield return At(Keep(18.0, 21.5, 0), "main-hall", 0, 4);
        // The grand stair from the hall, rising east under the landing's rail
        yield return At(Keep(16.5, 17.5, 0), "stair", 60, 8);
        // The dining hall: the table of plenty along its length, the hearth on the north wall
        yield return At(Keep(25.5, 7.5, 0), "dining-hall", 282, -14);
        // The kitchen off the dining hall: its hearth (a cauldron, a spit), the worktables under the pot rack
        yield return At(Keep(28.5, 3.5, 0), "kitchen", 90, -10);
        // The cellar under it, down the pantry's stair: barrels, the heaps of the dead kept for the fires
        yield return At(Keep(29.5, 7.5, -1), "cellar", 45, -10);
        // A guest room on the first floor: the two large canopied beds, a chest at the foot of each
        yield return At(Keep(6.5, 21.5, 1), "guest-room", 330, -16);
        // The same room's fireplace with the wing chairs before it
        yield return At(Keep(6.5, 18.5, 1), "guest-fire", 270, -8);
        // The ground floor's bathroom: the barrels of warm water, the washstand
        yield return At(Keep(5.5, 5.5, 0), "bathroom", 330, -18);
        // The library on the first floor, its fireplace and shelves
        yield return At(Keep(29.5, 8.5, 1), "library", 70, -8);
        // Coran's solar on the third floor, round the chimney breast's fireplace
        yield return At(Keep(17.5, 8.5, 2), "solar", 0, -8);
        // The master bedroom (Coran's): the bed hung in black, the fireplace on the end wall
        yield return At(Keep(28.5, 8.5, 2), "master-bedroom", 30, -12);
        // The roof terrace: the attic, shut, under its slate roof, the chimney stack, the turrets
        yield return At(Keep(4.5, 19.5, 3), "roof-attic", 55, 12);
        // The Great Hound's bones on the fields, side on from the south (the skull, the arched spine over the ribs, the tail)
        var (hx, hz, _) = L73Hound;
        yield return At(Ground(hx + 19.5, hz + 16.5), "great-hound", 0, -4);
        // A track worn toward the castle, from out on the fields, looking along it to the castle on its hill
        if (L73TrackSpot() is { } track)
            yield return At(Ground(track.X, track.Z), "track", track.Heading, 4);
        // A dead tree on the fields, from a little south of it (its branches against the sky)
        if (L73TreeSpot() is { } tree)
            yield return At(Ground(tree.X + 0.5, tree.Z + 7.5), "dead-tree", 0, 14);
        // The fields east of the castle: tors, dead grass, bones, the sea far off
        yield return At(Ground(L73IslandX + 70.5, L73IslandZ + 10.5, 1, 0), "fields", 100, -2);
        // The north shore under the moon
        var (sx, sz) = L73Shoreline(10);
        yield return At((sx, floor + TileAt((int)Math.Floor(sx), (int)Math.Floor(sz)).Height + 1, sz), "shore-moon", 10, 12);
        // The way out (WorldLayout.Level73.Links.cs): the north door in the outside of the curtain wall, chained shut, and opened
        // on the dark as Coran opens it
        yield return At(Ground(mid, z0 - 10.5), "north-door", 180, 6);
        yield return At(Ground(mid, z0 - 5.5), "north-door-open", 180, 2, "/backrooms l73postern open");
        // The ways in, in their host levels: the nearest Gloom in Level 9, the nearest of Level 6's deepest dark
        foreach (Showcase.Spot spot in L73LinkSpots(geometry)) yield return spot;
    }

    /// <summary>A place on a track about 110 out from the island's middle, and the heading from it toward the castle.</summary>
    private (double X, double Z, double Heading)? L73TrackSpot()
    {
        for (int a = 0; a < 360; a += 2)
        {
            double b = a * Math.PI / 180;
            int x = L73IslandX + (int)Math.Round(Math.Sin(b) * 110), z = L73IslandZ - (int)Math.Round(Math.Cos(b) * 110);
            Tile t = TileAt(x, z);
            if (t.Zone == L73Land && t.Floor == FloorKind.L73Track)
                return (x + 0.5, z + 0.5, (a + 180) % 360);
        }
        return null;
    }

    /// <summary>The trunk of the first dead tree found going round the island about 100 out.</summary>
    private (int X, int Z)? L73TreeSpot()
    {
        for (int r = 90; r <= 150; r += 6)
            for (int a = 0; a < 360; a += 3)
            {
                double b = a * Math.PI / 180;
                int x = L73IslandX + (int)Math.Round(Math.Sin(b) * r), z = L73IslandZ - (int)Math.Round(Math.Cos(b) * r);
                if (L73TreeNear(x, z) is { } tree && TileAt(tree.X, tree.Z + 7).Zone == L73Land) return (tree.X, tree.Z);
            }
        return null;
    }

    /// <summary>A spot on the island's last dry ground on a bearing (degrees clockwise from north) from its middle.</summary>
    private (double X, double Z) L73Shoreline(double bearing)
    {
        double b = bearing * Math.PI / 180, sx = Math.Sin(b), sz = -Math.Cos(b);
        int lastLand = 120;
        for (int r = 120; r < 420; r++)
        {
            Tile t = TileAt(L73IslandX + (int)Math.Round(sx * r), L73IslandZ + (int)Math.Round(sz * r));
            if (t.Zone == L73Land) lastLand = r;
            else if (t.Zone == L73Sea) break;
        }
        int back = Math.Max(120, lastLand - 4);
        return (L73IslandX + (int)Math.Round(sx * back) + 0.5, L73IslandZ + (int)Math.Round(sz * back) + 0.5);
    }
}
