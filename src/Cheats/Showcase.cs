using System;
using System.Collections.Generic;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// Showcase spots: the places in an experimental level worth a screenshot (its set pieces, rooms and creatures' haunts),
/// for the client rig's review tours (<c>/backrooms showcase &lt;level&gt;</c> lists them; the tour teleports there and looks
/// the given way). Each level fills in its own list in its own file (<c>WorldLayout.&lt;Level&gt;.Showcase.cs</c>).
/// </summary>
public static class Showcase
{
    /// <param name="Name">A short name for the shot (letters, digits and dashes).</param>
    /// <param name="X">World block coordinates of the camera's feet (a free standing spot).</param>
    /// <param name="Heading">Compass heading in degrees (0 north, 90 east), as the shotbot's <c>look</c> takes it.</param>
    /// <param name="Pitch">Degrees above the horizon (negative looks down).</param>
    /// <param name="Setup">Optional chat commands the tour runs after arriving (e.g. "/backrooms l120 misglitch"), separated by ";".</param>
    public readonly record struct Spot(string Name, double X, double Y, double Z, double Heading, double Pitch = 0, string Setup = null);

    /// <summary>The level's spots, near the world's centre first; empty for a level that has none.</summary>
    public static IEnumerable<Spot> For(int level, WorldLayout layout, WorldGeometry geometry) => level switch
    {
        WorldLayout.Level73 => layout.L73ShowcaseSpots(geometry),
        WorldLayout.Basement => layout.BasementShowcaseSpots(geometry),
        WorldLayout.Level52 => layout.L52ShowcaseSpots(geometry),
        WorldLayout.Level31 => layout.L31ShowcaseSpots(geometry),
        WorldLayout.Level120 => layout.L120ShowcaseSpots(geometry),
        WorldLayout.Level36 => layout.L36ShowcaseSpots(geometry),
        WorldLayout.Level15 => layout.L15ShowcaseSpots(geometry),
        WorldLayout.Level23 => layout.L23ShowcaseSpots(geometry),
        WorldLayout.Level14 => layout.L14ShowcaseSpots(geometry),
        WorldLayout.Level47 => layout.L47ShowcaseSpots(geometry),
        _ => Array.Empty<Spot>(),
    };
}
