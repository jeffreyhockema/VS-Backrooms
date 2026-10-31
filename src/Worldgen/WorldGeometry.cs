namespace Backrooms.Worldgen;

/// <summary>
/// Vertical placement of the levels: the shared floor (Level 0's) and the levels that lie below it, and the bands of
/// heights they are generated and lit over. Shared by the server-side generator, the client-side map and the offline
/// layout harness (tools/mapgen).
/// </summary>
public readonly struct WorldGeometry
{
    /// <summary>Walkable height between carpet and ceiling (about 3 m, like a commercial drop ceiling).</summary>
    public const int RoomHeight = 3;

    /// <summary>Level 1 is a little taller: four blocks of air under a bare concrete slab.</summary>
    public const int Level1RoomHeight = 4;

    /// <summary>Tallest walkable space of the indoor Levels 0-6 (Level 1, the grand rooms of Levels 3 and 5, the Beverly Room among them).</summary>
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
    public readonly int CapY;
    /// <summary>The highest block of the world.</summary>
    public readonly int TopY;

    /// <summary>
    /// How far below the other levels the Poolrooms' water lies: room for domes fifteen blocks high over it, and for
    /// pits more than twenty deep under it, within the band that is lit.
    /// </summary>
    public const int PoolDrop = 14;

    /// <summary>How deep the Poolrooms' pits go at most, below the water's surface.</summary>
    public const int PoolPitDepth = 22;

    /// <summary>
    /// How far below the other levels Motion's valley floors lie: room for its hills, and for the glass mountain and
    /// the castle on it to rise far above them.
    /// </summary>
    public const int MotionDrop = 30;

    /// <summary>
    /// How far below the other levels the floors of the five kept as 14-18 lie (Level !, Fun, the End, the Hub,
    /// 974): each level's own, changed here and nowhere else. The End's atrium is two storeys.
    /// </summary>
    public const int RunDrop = 0, FunDrop = 0, EndDrop = 6, HubDrop = 28, L974Drop = 0;

    /// <summary>The same for Levels 3999 and 188 (19, 20). Level 3999's atria are 18 high (its plan: 20 down).</summary>
    public const int L3999Drop = 20, L188Drop = 0;

    /// <summary>The same for the experimental Levels 73, the Basement and 52 (21-23).</summary>
    public const int L73Drop = 0, BasementDrop = 0, L52Drop = 0;

    /// <summary>The same for the experimental Levels 31 and 120 (24, 26).</summary>
    public const int L31Drop = 0, L120Drop = 0;

    /// <summary>The same for the experimental Levels 36, 15 and 23 (25, 27, 28).</summary>
    public const int L36Drop = 0, L15Drop = 0, L23Drop = 10; // 23: ten down, so the lid of its forest reaches 48 over the forest floor

    /// <summary>
    /// How far below its own floor the band each of the five is generated and lit over begins (<see cref="ShaftDepth"/> is
    /// the usual). The band is always as tall as the usual one, so a shallower start reaches higher (see
    /// <see cref="BandTopFor"/>); the End's starts 24 down, for its two-storey atrium six below the shared floor.
    /// </summary>
    public const int RunBandDepth = ShaftDepth, FunBandDepth = 12, EndBandDepth = 24, HubBandDepth = 4,
        L974BandDepth = ShaftDepth;

    /// <summary>
    /// The same for Levels 3999 and 188: Level 3999's starts only 4 down, so its band reaches its 18-high atria; Level
    /// 188's 6 down (the hatch's shaft), so its band reaches rel 33, over five storeys and a roof, for the black sky.
    /// </summary>
    public const int L3999BandDepth = 4, L188BandDepth = 6;

    /// <summary>The same for the experimental Levels 73, the Basement and 52 (21-23): the usual band for now.</summary>
    public const int L73BandDepth = 6, BasementBandDepth = 14, L52BandDepth = 3; // 52: open sky; its band reaches rel 36, over eight storeys, a roof and a parapet; (the Basement: 14, band top at rel 25, over the caps of its cracks)

    /// <summary>The same for the experimental Levels 31 and 120 (24, 26): the usual band for now.</summary>
    public const int L31BandDepth = ShaftDepth, L120BandDepth = ShaftDepth;

    /// <summary>
    /// The same for the experimental Levels 36, 15 and 23 (25, 27, 28): the usual band for the two indoor ones; Level 23's
    /// starts 20 below its floor, for its caverns and their lights (the band is lit up to 20 over the forest floor; its
    /// columns are built on up to the top of the world, see WorldGenerator.Band).
    /// </summary>
    public const int L36BandDepth = 14, L15BandDepth = ShaftDepth, L23BandDepth = 20;

    /// <summary>The street level of Level 11.</summary>
    public int CityFloorY => FloorY - CityDrop;

    /// <summary>
    /// The floor of a level: the street for Level 11, the water's surface for the Poolrooms, the valley floor for
    /// Motion, its own drop below the shared floor for each of the five kept as 14-18, and the shared floor for every other.
    /// </summary>
    public int FloorFor(int level) => level switch
    {
        11 => CityFloorY,
        WorldLayout.Poolrooms => FloorY - PoolDrop,
        WorldLayout.Motion => FloorY - MotionDrop,
        WorldLayout.RunLevel => FloorY - RunDrop,
        WorldLayout.FunLevel => FloorY - FunDrop,
        WorldLayout.TheEnd => FloorY - EndDrop,
        WorldLayout.Hub => FloorY - HubDrop,
        WorldLayout.Level974 => FloorY - L974Drop,
        WorldLayout.Level3999 => FloorY - L3999Drop,
        WorldLayout.Level188 => FloorY - L188Drop,
        WorldLayout.Level73 => FloorY - L73Drop,
        WorldLayout.Basement => FloorY - BasementDrop,
        WorldLayout.Level52 => FloorY - L52Drop,
        WorldLayout.Level31 => FloorY - L31Drop,
        WorldLayout.Level120 => FloorY - L120Drop,
        WorldLayout.Level36 => FloorY - L36Drop,
        WorldLayout.Level15 => FloorY - L15Drop,
        WorldLayout.Level23 => FloorY - L23Drop,
        _ => FloorY,
    };

    /// <summary>The band Level 11 is lit in: its subway up to just over the street lamps.</summary>
    public int CityBandBottom => CityFloorY - ShaftDepth;

    /// <summary>
    /// The bottom of the band of heights a level's block light is worked out over (the band is always as tall as the
    /// usual one): the city's subway; the Poolrooms' deepest pits; Motion's castle on its mountain, the only place
    /// there with lamps.
    /// </summary>
    public int BandBottomFor(int level) => level switch
    {
        11 => CityBandBottom,
        WorldLayout.Poolrooms => FloorFor(WorldLayout.Poolrooms) - PoolPitDepth - 2,
        WorldLayout.Motion => FloorFor(WorldLayout.Motion) + 14,
        // The five kept as 14-18: from their own depth below their own floor
        WorldLayout.RunLevel => FloorFor(WorldLayout.RunLevel) - RunBandDepth,
        WorldLayout.FunLevel => FloorFor(WorldLayout.FunLevel) - FunBandDepth,
        WorldLayout.TheEnd => FloorFor(WorldLayout.TheEnd) - EndBandDepth,
        WorldLayout.Hub => FloorFor(WorldLayout.Hub) - HubBandDepth,
        WorldLayout.Level974 => FloorFor(WorldLayout.Level974) - L974BandDepth,
        WorldLayout.Level3999 => FloorFor(WorldLayout.Level3999) - L3999BandDepth,
        WorldLayout.Level188 => FloorFor(WorldLayout.Level188) - L188BandDepth,
        WorldLayout.Level73 => FloorFor(WorldLayout.Level73) - L73BandDepth,
        WorldLayout.Basement => FloorFor(WorldLayout.Basement) - BasementBandDepth,
        WorldLayout.Level52 => FloorFor(WorldLayout.Level52) - L52BandDepth,
        WorldLayout.Level31 => FloorFor(WorldLayout.Level31) - L31BandDepth,
        WorldLayout.Level120 => FloorFor(WorldLayout.Level120) - L120BandDepth,
        WorldLayout.Level36 => FloorFor(WorldLayout.Level36) - L36BandDepth,
        WorldLayout.Level15 => FloorFor(WorldLayout.Level15) - L15BandDepth,
        WorldLayout.Level23 => FloorFor(WorldLayout.Level23) - L23BandDepth,
        _ => BandBottom,
    };

    /// <summary>
    /// The top of the band a level is lit over, as tall as the usual one from <see cref="BandBottomFor"/>. The five kept as
    /// 14-18 are generated up to it and sealed with mantle just above it (the usual <see cref="CapY"/> for a level with
    /// the usual band); it is never above <see cref="TopY"/> - 1.
    /// </summary>
    public int BandTopFor(int level) => System.Math.Min(TopY - 1, BandBottomFor(level) + BandTop - BandBottom);

    /// <summary>Lowest block that can differ from solid concrete (the bottom of the pit shafts).</summary>
    public int BandBottom => FloorY - ShaftDepth;

    /// <summary>Highest block that can differ from solid concrete (just under the mantle cap).</summary>
    public int BandTop => CapY - 1;

    public WorldGeometry(int mapSizeY)
    {
        // Level 0 sits near the top of the world, leaving everything below free for deeper levels later
        FloorY = mapSizeY - 40;
        CeilingY = FloorY + RoomHeight + 1;
        CapY = CeilingY + CrawlspaceHeight + SlabThickness + 1;
        TopY = mapSizeY - 1;
    }

    /// <summary>Whether a height is inside the walkable space of any level.</summary>
    public bool Contains(double y) => y > FloorY && y < FloorY + MaxRoomHeight + 1;
}
