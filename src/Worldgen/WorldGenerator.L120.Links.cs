namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of Level 120's ways in and out (WorldLayout.Level120.Links.cs). In Level 4: the door marked SERVER ROOM
/// (<c>l120-door-office-lower/upper</c>: grey steel, the plate at eye height, a cold green light in the gap under it; kind
/// <c>l120-serverroom</c>) in a server room's doorway, the office wall over it as Level 4 draws it; and the M.E.G. placard
/// beside it (<c>l120-megplacard-&lt;side&gt;</c>). In Level 120: the doors back (<c>l120-door-dark-lower/upper</c>: the same
/// steel door, unmarked, a line of office light under it; kind <c>l120-door</c>), the level's own wall above.
/// </summary>
public sealed partial class WorldGenerator
{
    private readonly int[] l120DoorOffice = new int[2], l120DoorDark = new int[2], l120Placard = new int[4];

    /// <summary>The ids of the ways' blocks (from <see cref="InitL120"/>).</summary>
    private void InitL120Links()
    {
        string[] parts = { "lower", "upper" };
        for (int i = 0; i < 2; i++)
        {
            l120DoorOffice[i] = L120Block("l120-door-office-" + parts[i], BlockId("backrooms:officedoor-" + parts[i]));
            l120DoorDark[i] = L120Block("l120-door-dark-" + parts[i], l120DoorOffice[i]);
        }
        for (int f = 0; f < 4; f++) l120Placard[f] = L120Block("l120-megplacard-" + Sides[f]);
    }

    /// <summary>The scaffold's hook (WorldGenerator.ExpLinks.cs): the SERVER ROOM door and its placard in Level 4; -1 elsewhere.</summary>
    partial void L120EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        switch (t.Under)
        {
            case Unders.L120ServerDoor when t.Kind == TileKind.Door && rel is 1 or 2:
                id = l120DoorOffice[rel - 1];
                break;
            case Unders.L120Placard when rel == 1 && t.Kind == TileKind.Floor:
                if (l120Placard[Facing(t.Pier)] != 0) id = l120Placard[Facing(t.Pier)];
                break;
        }
    }

    /// <summary>A door back to the offices in Level 120's wall, <paramref name="rel"/> above the floor: the floor under it, the door, or -1 for the wall.</summary>
    private int L120ExitDoorBlock(in Tile t, int rel) => rel switch
    {
        0 => l120Floor[WorldLayout.L120PanelDirty],
        1 or 2 => l120DoorDark[rel - 1],
        _ => -1,
    };
}
