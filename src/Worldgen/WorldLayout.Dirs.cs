namespace Backrooms.Worldgen;

/// <summary>
/// The one set of direction helpers the layout partials share. A direction is an <see cref="ArchPier"/>
/// (North is -z, East is +x, seen from above), whatever it is used for; keeping the table in one place means
/// a new convention or value cannot make two copies disagree.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The tile one step from (x, z) in a direction.</summary>
    private static (int, int) Step(int x, int z, ArchPier dir) => dir switch
    {
        ArchPier.North => (x, z - 1),
        ArchPier.South => (x, z + 1),
        ArchPier.East => (x + 1, z),
        _ => (x - 1, z),
    };

    /// <summary>A direction as a step (x east, z south).</summary>
    private static (int Dx, int Dz) FacingStep(ArchPier pier) => pier switch
    {
        ArchPier.North => (0, -1),
        ArchPier.South => (0, 1),
        ArchPier.East => (1, 0),
        _ => (-1, 0),
    };

    /// <summary>Turns a direction a quarter clockwise, seen from above.</summary>
    private static ArchPier Turn(ArchPier dir) => dir switch
    {
        ArchPier.North => ArchPier.East,
        ArchPier.East => ArchPier.South,
        ArchPier.South => ArchPier.West,
        _ => ArchPier.North,
    };

    /// <summary>The direction facing the other way.</summary>
    private static ArchPier Opposite(ArchPier dir) => Turn(Turn(dir));
}
