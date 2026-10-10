using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// The Hub's thresholds (kept as level 17): the ways out of it, and the ways into it from other levels.
/// <list type="bullet">
/// <item>Its carved doors are one-way although you walk through them: canon says the doorway disappears behind you,
/// with the key that opened it (LINKS.md). Level 1's, Level 11's and the one canon gives to Level 178 (here the
/// Snackrooms) open for anyone; the rest only to their level's key, and the pink ribbon door to Level 974 only to
/// someone carrying something cute. The game side of that is <see cref="ThresholdSystem.UseHubDoor"/>.</item>
/// <item>Its plain grey service doors are the way back: whoever comes into the Hub through a door that can be walked back
/// through (Level 1's and Level 2's Hub doors, The End's EXIT doors) arrives beside one, and it leads back.</item>
/// <item>Out in the Far Tunnels: a stretch of wall that isn't there (Level 4, two-way), a rectangular hole in the road
/// (Level 94, one-way), and blind ends where the concrete turns to white tile (Level 37, two-way, paired with Level 37's
/// dry corridors that turn to asphalt).</item>
/// <item>A door that wasn't there, now and then, in any level (<see cref="HubManifest"/>): one-way.</item>
/// </list>
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here.</summary>
    private const ulong SaltHubThreshold = 0x17C0;

    /// <summary>The Hub's grey service doors: the way back for anyone who came in through a two-way door.</summary>
    public static readonly System.Func<Tile, bool> HubServiceDoor = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.HubServiceDoor;

    /// <summary>A carved door in the Hub (any of its three columns).</summary>
    public static readonly System.Func<Tile, bool> HubCarvedDoor = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.HubDoor;

    /// <summary>The doors that weren't there, standing now (put down and taken away by HubSystem), by block position.</summary>
    public static readonly System.Collections.Concurrent.ConcurrentDictionary<(int X, int Z), bool> ManifestDoors = new();

    private static readonly System.Func<Tile, bool> HubTileEnd = t => t.Under == Unders.HubTileEnd;
    private static readonly System.Func<Tile, bool> PoolAsphaltEnd = t => t.Under == Unders.PoolAsphalt;

    private Passage HubWalked(int x, int z, in Tile tile, double rel)
    {
        if (tile.Under is < Unders.HubFirst or > Unders.HubLast) return null;
        int level = tile.Level;
        (int X, int Z) Whole(System.Func<Tile, bool> part) => layout.FeatureOrigin(x, z, t => t.Level == level && part(t));
        switch (tile.Under)
        {
            case Unders.HubFalseWall when level == WorldLayout.Hub && rel > 0.5 && rel < 2.5:
            {
                // Into the wall, which isn't there, and out into the Abandoned Office
                var wall = Whole(t => t.Under == Unders.HubFalseWall);
                Passage office = BothWays(wall, KeyOf(wall, SaltHubThreshold + 1), 4);
                office.Message = "backrooms:hub-falsewall";
                return office;
            }
            case Unders.HubHole when level == WorldLayout.Hub && tile.Kind == TileKind.Pit && rel < -1.5:
            {
                // Down the hole in the road, and out of the sky over the hills of Level 94
                var hole = Whole(t => t.Under == Unders.HubHole);
                Passage fall = OneWay(hole, KeyOf(hole, SaltHubThreshold + 2), WorldLayout.Motion);
                fall.Message = "backrooms:hub-hole";
                return fall;
            }
            case Unders.HubTileEnd when level == WorldLayout.Hub && rel < 2.5:
            {
                // On where the concrete has turned to white tile: the Poolrooms, by a dry corridor that turns to asphalt
                var end = Whole(HubTileEnd);
                Passage pool = BothWays(end, KeyOf(end, SaltHubThreshold + 3), WorldLayout.Poolrooms, PoolAsphaltEnd);
                pool.Find = InPoolAsphaltEnd();
                pool.Message = "backrooms:hub-tileend";
                return pool;
            }
            case Unders.HubTowerVoid when level == WorldLayout.Hub && rel < 27:
            {
                // Over the balcony and into the storm: the Hub casts you out into its tunnels
                var voidOrigin = Whole(t => t.Under == Unders.HubTowerVoid);
                Passage cast = OneWay(voidOrigin, KeyOf(voidOrigin, SaltHubThreshold + 10), WorldLayout.Hub);
                cast.Message = "backrooms:hub-void-fall";
                return cast;
            }
            case Unders.PoolAsphalt when level == WorldLayout.Poolrooms && rel < 2:
            {
                // Where a dry corridor's tile gives way to concrete and asphalt: on into the Hub
                var end = Whole(PoolAsphaltEnd);
                Passage hub = BothWays(end, KeyOf(end, SaltHubThreshold + 4), WorldLayout.Hub, HubTileEnd);
                hub.Find = InHubTileEnd();
                hub.Message = "backrooms:hub-arrive";
                return hub;
            }
        }
        return null;
    }

    private Passage HubUsed(int x, int z, int level, string kind, ref string refusal)
    {
        // A door that wasn't there a moment ago: one way into the Hub
        if (kind == "locked" && ManifestDoors.ContainsKey((x, z))) return HubManifest(x, z);
        switch (kind)
        {
            case "locked" when level == 1 && layout.TileAt(x, z) is { Kind: TileKind.Wall, Variant: Decor.HubEntranceDoor }:
            case "tunneldoor" when level == 2 && layout.TileAt(x, z).Under == Unders.HubEntrance:
            {
                // A door into the Hub: you come out beside one of its grey service doors, which leads back
                Passage hub = BothWays((x, z), KeyOf((x, z), SaltHubThreshold + 5 + (ulong)level), WorldLayout.Hub, HubServiceDoor);
                hub.Message = "backrooms:hub-arrive";
                hub.Sound = level == 2 ? "game:sounds/block/metaldoor" : "game:sounds/block/door";
                return hub;
            }
            case "hubdoor" or "hub-door" or "towerdoor":
                // The carved doors are used through ThresholdSystem.UseHubDoor (they need the player); the Tower is shut
                refusal = "locked";
                return null;
        }
        return null;
    }

    /// <summary>Beside one of the Hub's white-tile ends (the ordinary search can never land there), or anywhere if none is free.</summary>
    private System.Func<ulong, (int X, int Z, double Height)?> InHubTileEnd() => key =>
        layout.HubTileEndArrival(key) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : IntoHub(HubTileEnd)(key);

    /// <summary>On the asphalt of one of Level 37's dry corridor ends, beside the end itself (else anywhere in Level 37).</summary>
    private System.Func<ulong, (int X, int Z, double Height)?> InPoolAsphaltEnd() => key =>
        layout.FindArrival(WorldLayout.Poolrooms, key, PoolAsphaltEnd, spot: WorldLayout.IsPoolAsphaltSpot) is { } a
            ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : In(WorldLayout.Poolrooms, PoolAsphaltEnd)(key);

    /// <summary>Somewhere to arrive in the level for a key (beside a tile matching <paramref name="beside"/>, where one can be found).</summary>
    private System.Func<ulong, (int X, int Z, double Height)?> IntoHub(System.Func<Tile, bool> beside = null) => In(WorldLayout.Hub, beside);

    /// <summary>
    /// A carved door of the Hub's, leading one way to <paramref name="target"/> (a level, or
    /// <see cref="WorldLayout.HubSnackroomsDoor"/>): the same place every time, and no way back.
    /// </summary>
    public Passage HubDoor(int x, int z, int target)
    {
        var door = layout.FeatureOrigin(x, z, t => t.Level == WorldLayout.Hub && HubCarvedDoor(t));
        ulong key = KeyOf(door, SaltHubThreshold + 8);
        var passage = new Passage
        {
            Source = door, Key = key, Message = "backrooms:hub-arrive-oneway", Sound = "backrooms:sounds/effect/hub/doorgrind",
            // (The End's door lets you out beside one of its EXIT doors, as LINKS.md has it)
            // (Level 3999: beside one of its STAFF ONLY doors, ThresholdNetwork.L3999.cs)
            Find = target == WorldLayout.HubSnackroomsDoor ? InSnackrooms() : target == WorldLayout.TheEnd ? EndExitArrival()
                : target == WorldLayout.Level3999 ? L3999StaffDoorArrival() : In(target),
        };
        return passage;
    }

    /// <summary>A door into the Hub that wasn't there a moment ago (placed by HubSystem): one way, anywhere in the Crossroads.</summary>
    public Passage HubManifest(int x, int z)
    {
        Passage passage = OneWay((x, z), KeyOf((x, z), SaltHubThreshold + 9), WorldLayout.Hub);
        passage.Message = "backrooms:hub-arrive-manifest";
        passage.Sound = "backrooms:sounds/effect/hub/doorgrind";
        return passage;
    }
}
