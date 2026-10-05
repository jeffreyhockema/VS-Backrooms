namespace Backrooms.Worldgen;

/// <summary>Vertical placement of Level 0. Shared by the server-side generator and the client-side map.</summary>
public readonly struct WorldGeometry
{
    /// <summary>Walkable height between carpet and ceiling (about 3 m, like a commercial drop ceiling).</summary>
    public const int RoomHeight = 3;

    /// <summary>Level 1 is a little taller: four blocks of air under a bare concrete slab.</summary>
    public const int Level1RoomHeight = 4;

    /// <summary>Tallest walkable space of any level (Level 1, the Beverly Room).</summary>
    public const int MaxRoomHeight = 4;

    /// <summary>Walkable height of each level's ordinary rooms.</summary>
    public static readonly int[] LevelRoomHeights = { RoomHeight, Level1RoomHeight, RoomHeight, RoomHeight, RoomHeight, RoomHeight };

    /// <summary>The dusty void above the Level 0 ceiling tiles.</summary>
    public const int CrawlspaceHeight = 1;

    /// <summary>Depth of the shafts in pit rooms.</summary>
    public const int ShaftDepth = 30;

    private const int SlabThickness = 4;

    /// <summary>
    /// How far below the other levels Level 11's streets lie: the city needs the height for its towers, which rise
    /// almost to the top of the world.
    /// </summary>
    public const int CityDrop = 48;

    public readonly int FloorY;
    /// <summary>Ceiling of Level 0 and Level 2.</summary>
    public readonly int CeilingY;
    public readonly int Level1CeilingY;
    public readonly int CapY;
    /// <summary>The highest block of the world.</summary>
    public readonly int TopY;

    /// <summary>The street level of Level 11.</summary>
    public int CityFloorY => FloorY - CityDrop;

    /// <summary>The floor of a level: the street for Level 11, the shared floor for every other.</summary>
    public int FloorFor(int level) => level == 11 ? CityFloorY : FloorY;

    /// <summary>The band Level 11 is lit in: its subway up to just over the street lamps.</summary>
    public int CityBandBottom => CityFloorY - ShaftDepth;

    /// <summary>Lowest block that can differ from solid concrete (the bottom of the pit shafts).</summary>
    public int BandBottom => FloorY - ShaftDepth;

    /// <summary>Highest block that can differ from solid concrete (just under the mantle cap).</summary>
    public int BandTop => CapY - 1;

    /// <summary>Height at which the map samples whether a column blocks sight (head height).</summary>
    public int EyeY => FloorY + 2;

    public WorldGeometry(int mapSizeY)
    {
        // Level 0 sits near the top of the world, leaving everything below free for deeper levels later
        FloorY = mapSizeY - 40;
        CeilingY = FloorY + RoomHeight + 1;
        Level1CeilingY = FloorY + Level1RoomHeight + 1;
        CapY = CeilingY + CrawlspaceHeight + SlabThickness + 1;
        TopY = mapSizeY - 1;
    }

    /// <summary>Whether a height is inside the walkable space of any level.</summary>
    public bool Contains(double y) => y > FloorY && y < FloorY + MaxRoomHeight + 1;
}
