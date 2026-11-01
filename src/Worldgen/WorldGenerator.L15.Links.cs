using L = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of Level 15's links (laid out in WorldLayout.Level15.Links.cs; the level's own file). In Level 10: the immense
/// white wall, the halls' own wall seen from outside (a steel kick plate at its foot, the graphite band with its pale line,
/// wall lights in every other bay, a cornice light, white panels on up, white steel pilasters every eight blocks and a steel
/// coping at the top of the band), its small reinforced door (<c>l15-walldoor</c>) between lit jambs under a lit lintel, a
/// tread plate before it. In Level 3: a steel door in the wall with cold white light under it (<c>l15-l3door</c>). In Level 15:
/// the hall doors that do not open (<c>l15-sealeddoor</c>), the ESCAPE panel that works (<c>l15-escapelive</c>), the gateway
/// it opens (<c>l15-gatewayshut</c>; L15System swaps in <c>l15-gatewayopen</c>), the pane with a street's light behind it
/// (<c>l15-cityglass</c>), and the office: Level 4's carpet, drywall, ceiling tiles and desks, its concrete stairs going down.
/// </summary>
public sealed partial class WorldGenerator
{
    private readonly int[,] l15WallDoor = new int[2, 4], l15SealedDoor = new int[2, 4], l15L3Door = new int[2, 4];
    private readonly int[] l15GatewayShut = new int[2], l15EscapeLive = new int[4];
    private int l15CityGlass;

    /// <summary>The links' block ids (from <see cref="InitL15"/>).</summary>
    private void InitL15Links()
    {
        for (int f = 0; f < 4; f++)
        {
            for (int p = 0; p < 2; p++)
            {
                string part = p == 0 ? "lower" : "upper";
                l15WallDoor[p, f] = L15Block($"l15-walldoor-{part}-{Sides[f]}", l15Wall[6]);
                l15SealedDoor[p, f] = L15Block($"l15-sealeddoor-{part}-{Sides[f]}", l15WallDoor[p, f]);
                l15L3Door[p, f] = L15Block($"l15-l3door-{part}-{Sides[f]}", l15Wall[3]);
            }
            l15EscapeLive[f] = L15Block($"l15-escapelive-{Sides[f]}", l15Deco[L15DEscape, f]);
        }
        l15GatewayShut[0] = L15Block("l15-gatewayshut-lower", l15Gate);
        l15GatewayShut[1] = L15Block("l15-gatewayshut-upper", l15GatewayShut[0]);
        l15CityGlass = L15Block("l15-cityglass", l15Glass[0]);
    }

    /// <summary>The blocks of Level 15's ways in, in Levels 10 and 3 (-1: the host level's own).</summary>
    partial void L15EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        int f = Facing(t.Pier);
        switch (t.Under)
        {
            case Unders.L15Wall10:
                id = L15Wall10Block(t, gx, gz, rel, door: false);
                break;
            case Unders.L15WallDoor10:
                id = rel is 1 or 2 ? l15WallDoor[rel - 1, f] : rel == 3 ? l15Wall[L15WLintel] : L15Wall10Block(t, gx, gz, rel, door: true);
                break;
            case Unders.L15Apron10:
                if (rel == 0) id = l15Floor[L.L15FloorTrack];
                break;
            case Unders.L15Door3:
                if (rel is 1 or 2) id = l15L3Door[rel - 1, f];
                break;
        }
    }

    /// <summary>
    /// A block of the white wall in the fields (-1 under the ground: the fields' own): the halls' wall, dressed on its face
    /// (<see cref="Tile.Pier"/>) as along a main hall, up to the top of the band, where a steel coping caps it.
    /// </summary>
    private int L15Wall10Block(in Tile t, int gx, int gz, int rel, bool door)
    {
        if (rel < 0) return -1;
        if (rel >= L.L15WallTop) return l15Wall[6];
        if ((t.Detail & L.L15WallPilasterBit) != 0) return l15Wall[rel == 2 ? 7 : 6];
        if ((t.Detail & L.L15WallJambBit) != 0 && rel is >= 1 and <= 3) return l15Wall[L15WJamb];
        int f = Facing(t.Pier);
        int along = t.Pier is ArchPier.North or ArchPier.South ? gx : gz;
        bool bay = Hashing.Mod(along, 8) == 4 && !door;
        switch (rel)
        {
            case 0: return l15Wall[0];
            case 1: return l15Wall[2];
            case 2: return l15Deco[L15DBand, f];
            case 3 when bay: return l15Deco[L15DLampLower, f];
            case 4 when bay:
                bool turn = t.Pier is ArchPier.East or ArchPier.South;
                return l15Deco[Hashing.Mod(along, 16) == (turn ? 4 : 12) ? L15DLampOn : L15DLampUpper, f];
            case L.L15HallHeight: return l15Deco[L15DCornice, f];
        }
        return Hashing.Unit(Hashing.Hash(seed, gx, gz * 16 + rel, 0x2720)) < 0.18 ? l15Wall[1] : l15Wall[0];
    }

    /// <summary>A block of one of the links in Level 15 itself, or -1 for the level's own drawing of the tile.</summary>
    private int L15LinkBlock(in Tile t, int gx, int gz, int rel)
    {
        int f = Facing(t.Pier);
        switch (t.Under)
        {
            case Unders.L15Sealed:
                if (rel is 1 or 2) return l15SealedDoor[rel - 1, f];
                if (rel == 3) return l15Wall[L.L15IsDark(t) ? L15WLintelDead : L15WLintel];
                return -1;
            case Unders.L15Escape:
                return rel == 2 ? l15EscapeLive[f] : -1;
            case Unders.L15Gateway:
                return rel switch
                {
                    0 => l15Floor[L.L15FloorTrack],
                    1 => l15GatewayShut[0],
                    2 or 3 => l15GatewayShut[1],
                    4 => l15Gate,
                    _ => -1,
                };
            case Unders.L15Window:
                return rel is 2 or 3 ? l15CityGlass : -1;
            case Unders.L15Office:
            {
                // Level 4's carpet, its drywall round the stairwell under the floor, its ceiling tiles between the lights, its desks
                int air = t.Height is >= 3 and <= 7 ? t.Height : 4;
                if (rel == 0) return floorIds[(int)FloorKind.OfficeCarpet];
                if (rel < 0) return rel == 1 - L.L15StairSteps ? officeWallBaseId : rel > 1 - L.L15StairSteps ? officeWallId : -1;
                if (rel == 1 && t.Variant == Props.Desk) return deskIds[f];
                if (rel == air + 1 && t.Ceiling == CeilingKind.L15Ceiling) return officeCeilingId;
                return -1;
            }
            case Unders.L15Stairs:
            {
                // Concrete stairs down through the floor (Pier the way they climb), six steps, then the landing; open air over them up
                // to the room's ceiling (Stack is the step here, not a stack of crates)
                int n = t.Stack, room = t.Height is >= 3 and <= 7 ? t.Height : 4;
                if (rel > 0) return rel <= room ? 0 : -1;
                if (n > L.L15StairSteps)
                    return rel == -L.L15StairSteps ? floorIds[(int)FloorKind.OfficeCarpet] : rel < -L.L15StairSteps ? concreteId : 0;
                int tread = 1 - n;
                if (rel < tread) return concreteId;
                return rel == tread ? stairIds[f] : 0;
            }
        }
        return -1;
    }
}
