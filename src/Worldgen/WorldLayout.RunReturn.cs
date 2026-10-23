using System;

namespace Backrooms.Worldgen;

/// <summary>Where an escaped runner comes out: in front of an ordinary door, which becomes Level !'s red one.</summary>
public readonly record struct RunReturnSpot(int StandX, int StandZ, int DoorX, int DoorZ, ArchPier Face, bool ReplacesDoor);

public sealed partial class WorldLayout
{
    private static readonly ArchPier[] ReturnDirs = { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West };

    /// <summary>An ordinary single door of a level, one a person has been through: not an elevator, a fake, or something a feature owns.</summary>
    private static bool IsOrdinaryDoor(in Tile t, int level) =>
        t.Kind == TileKind.Door && t.Level == level && t.Under == 0 && t.Pattern != WallPattern.Elevator
        && (level != TheEnd || (t.Pattern is WallPattern.EndExit or WallPattern.EndStaff && t.Zone < 4));

    private bool IsReturnFront(int x, int z, int level)
    {
        Tile t = TileAt(x, z);
        return t.Level == level && IsArrivalSpot(t);
    }

    /// <summary>
    /// Where to put down someone who has come out of Level !'s true exit, given where the level would have put them
    /// (<paramref name="ax"/>, <paramref name="az"/>): in front of an ordinary single door within <paramref name="reach"/>
    /// tiles, which the red door replaces; failing that, in front of a plain wall (nowhere within 2 tiles of a door or touching a doorway) which the red door is set into. Null if there is neither (the level's own arrival stands).
    /// </summary>
    public RunReturnSpot? FindRunReturn(int level, int ax, int az, int reach = 32)
    {
        for (int r = 0; r <= reach; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int x = ax + dx, z = az + dz;
                    Tile door = TileAt(x, z);
                    if (!IsOrdinaryDoor(door, level)) continue;
                    foreach (ArchPier face in ReturnDirs)
                        if (Fits(x, z, face, level)) return new RunReturnSpot(Step(x, z, face).Item1, Step(x, z, face).Item2, x, z, face, true);
                }
        for (int r = 0; r <= reach; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int x = ax + dx, z = az + dz;
                    Tile wall = TileAt(x, z);
                    if (wall.Kind != TileKind.Wall || wall.Level != level || wall.Under != 0 || NearDoor(x, z)) continue;
                    foreach (ArchPier face in ReturnDirs)
                        if (Fits(x, z, face, level)) return new RunReturnSpot(Step(x, z, face).Item1, Step(x, z, face).Item2, x, z, face, false);
                }
        return null;
    }

    /// <summary>A door or wall tile at (x, z) with open floor in front of it (toward <paramref name="face"/>) and plain wall to either side.</summary>
    private bool Fits(int x, int z, ArchPier face, int level)
    {
        var (fx, fz) = Step(x, z, face);
        if (!IsReturnFront(fx, fz, level)) return false;
        ArchPier side = Turn(face);
        var (lx, lz) = Step(x, z, side);
        var (rx, rz) = Step(x, z, Opposite(side));
        return TileAt(lx, lz).Kind == TileKind.Wall && TileAt(rx, rz).Kind == TileKind.Wall;
    }

    private bool NearDoor(int x, int z)
    {
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
                {
                    TileKind k = TileAt(x + dx, z + dz).Kind;
                    if (k == TileKind.Door || k == TileKind.Doorway && Math.Max(Math.Abs(dx), Math.Abs(dz)) <= 1) return true;
                }
        return false;
    }
}
