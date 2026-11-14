using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 31, "Roller Rink"'s ways in and out, laid out (docs/design/experimental-levels/LINKS.md, "Level 31"; the thresholds
/// are Thresholds/ThresholdNetwork.L31.cs). This file is the level's own.
/// <list type="bullet">
/// <item><b>In:</b> a wooden door where none should be, in a wall of Level 2's tunnels, Level 3's brick (Wikidot: "the wooden
/// door within the brick walls of a long-forgotten electrical station") or Level 6's dark, with 2000s bubblegum pop playing
/// faintly behind it (Regions.L31System plays it). Rare: about one cell in 1200 of Levels 2 and 3, and half that in Level 6
/// ("even less frequent in Level 6", Fandom), a walk of a kilometre and more between them. Each is drawn on one wall tile
/// with a solid wall behind it and on either side, open floor in front (<see cref="Unders.L31HostDoor"/>, its Pier the way
/// it faces); nothing else in the host moves (its own salts).</item>
/// <item><b>The lobby's wooden door</b> (<see cref="Unders.L31LobbyDoor"/>), in every lobby's back wall: where a wooden door
/// opens, and the way back through it.</item>
/// <item><b>Out: the Revolving Door</b> (Fandom), in the front wall of one lobby in twelve (from layout 16's balance (every world: ExpVersion) one in 48:
/// <see cref="L31RevolvingChance"/>), beside the front doors: to Level 9, 10 or 11, each always the same one
/// (<see cref="L31RevolvingTarget"/>).</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL31HostDoor = 0x2420, SaltL31HostDoorPick = 0x2424, SaltL31RevolvingRoll = 0x2428, SaltL31RevolvingTo = 0x2429;

    /// <summary>The share of the cells of Levels 2 and 3 that hold a wooden door into the rink, and of Level 6's (half as many).</summary>
    public const double L31DoorShare = 1.0 / 1200, L31DoorShareL6 = 1.0 / 2400;

    /// <summary>The share of the lobbies with a revolving door (the pre-releases' rate, before layout 16's balance, which every world now reads: ExpVersion).</summary>
    public const double L31RevolvingShare = 1.0 / 12;

    /// <summary>
    /// The share of the lobbies with a revolving door in this world: from layout 16's balance (every world: ExpVersion) a quarter of it, one lobby in 48
    /// (the progression rule, decision 20: a way from a Level 2 door on to Level 9, 10 or 11 is a shortcut, a quarter as
    /// common; the kept ones are the same doors, the lowest rolls).
    /// </summary>
    public double L31RevolvingChance => ExpVersion >= 16 ? L31RevolvingShare / 4 : L31RevolvingShare;

    /// <summary>Where in a complex's plan the lobby's wooden door is (in its back wall, onto the service corridor), and the
    /// revolving door's three tiles (in its front wall, east of the front doors; the middle one at <see cref="L31RevolvingP"/>).</summary>
    public const int L31LobbyDoorP = 68, L31LobbyDoorQ = 20, L31RevolvingP = 67, L31RevolvingQ = -1;

    /// <summary>A wooden door into the rink in Level 2, 3 or 6.</summary>
    public static bool IsL31HostDoor(Tile t) => t.Under == Unders.L31HostDoor && t.Level is 2 or 3 or 6;

    /// <summary>A lobby's wooden door.</summary>
    public static bool IsL31LobbyDoor(Tile t) => t.Under == Unders.L31LobbyDoor && t.Level == Level31;

    /// <summary>A tile of a revolving door.</summary>
    public static bool IsL31Revolving(Tile t) => t.Under == Unders.L31Revolving && t.Level == Level31;

    /// <summary>Whether a cell of Level 2, 3 or 6 rolls a wooden door (it is laid only where a wall takes one).</summary>
    public bool L31HostDoorCell(int level, int mx, int mz) =>
        level is 2 or 3 or 6 && Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL31HostDoor + (ulong)level)) < (level == 6 ? L31DoorShareL6 : L31DoorShare);

    /// <summary>Where a revolving door leads (by its middle tile, or any): Level 9, 10 or 11, always the same.</summary>
    public int L31RevolvingTarget(int x, int z)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, x, z, SaltL31RevolvingTo));
        return r < 1 / 3.0 ? 9 : r < 2 / 3.0 ? 10 : 11;
    }

    /// <summary>Whether a complex's lobby has a revolving door (<see cref="L31RevolvingChance"/>, and only where the complex is all the level's).</summary>
    public bool L31HasRevolving(int wx, int wz) => L31RevolvingRoll(wx, wz) && L31PlanOf(wx, wz).Kind == L31Kind.Rinks;

    /// <summary>Whether a complex would have a revolving door if it has a lobby (read while its plan is made, so not from the plan).</summary>
    private bool L31RevolvingRoll(int wx, int wz) => Hashing.Unit(Hashing.Hash(seed, wx, wz, SaltL31RevolvingRoll)) < L31RevolvingChance && L31ComplexInside(wx, wz);

    /// <summary>The middle tile of a complex's revolving door, if it has one.</summary>
    public (int X, int Z)? L31RevolvingOf(int wx, int wz) => L31HasRevolving(wx, wz) ? L31PlanOf(wx, wz).World(L31RevolvingP, L31RevolvingQ) : null;

    /// <summary>The nearest revolving door to a place (looking up to <paramref name="rings"/> complexes away), or null.</summary>
    public (int X, int Z)? L31NearestRevolving(int x, int z, int rings = 8)
    {
        int cx = Hashing.FloorDiv(x, L31Period), cz = Hashing.FloorDiv(z, L31Period);
        (int X, int Z)? best = null;
        long bestD = long.MaxValue;
        for (int r = 0; r <= rings; r++)
        {
            // (past the ring a door was found in, a nearer one can still lie one ring further out, in a corner)
            if (best != null && (long)(r - 1) * L31Period * (r - 1) * L31Period > bestD) break;
            for (int wz = cz - r; wz <= cz + r; wz++)
                for (int wx = cx - r; wx <= cx + r; wx++)
                {
                    if (Math.Max(Math.Abs(wx - cx), Math.Abs(wz - cz)) != r || L31RevolvingOf(wx, wz) is not { } d) continue;
                    long dd = (long)(d.X - x) * (d.X - x) + (long)(d.Z - z) * (d.Z - z);
                    if (dd < bestD) { bestD = dd; best = d; }
                }
        }
        return best;
    }

    /// <summary>
    /// A complex's ways out and back (called at the end of its plan): the lobby's wooden door in its back wall, and in some
    /// lobbies (<see cref="L31RevolvingChance"/>) the revolving door in its front wall (the lobby's mural stops above them: WorldGenerator.L31Cladding).
    /// </summary>
    private void L31LayLinks(L31Plan plan)
    {
        if (plan.Kind != L31Kind.Rinks) return;
        ref Tile door = ref plan.At(L31LobbyDoorP, L31LobbyDoorQ);
        if (door.Kind == TileKind.Wall)
        {
            door.Under = Unders.L31LobbyDoor;
            door.Pier = plan.Dir(ArchPier.North);
        }
        if (!L31RevolvingRoll(plan.Wx, plan.Wz)) return;
        for (int k = -1; k <= 1; k++)
        {
            ref Tile t = ref plan.At(L31RevolvingP + k, L31RevolvingQ);
            if (t.Kind != TileKind.Wall) continue;
            t.Under = Unders.L31Revolving;
            t.Stack = (byte)(k + 1);
            t.Pier = plan.Dir(ArchPier.South);
            t.Detail = 0;
        }
    }

    /// <summary>
    /// The nearest wooden door into the rink in a host level (2, 3 or 6) to a cell, looking out ring by ring up to
    /// <paramref name="reach"/> cells: its tile and the way it faces, or null.
    /// </summary>
    public (int X, int Z, ArchPier Facing)? L31NearestHostDoor(int level, int mx0, int mz0, int reach = 1200)
    {
        for (int r = 0; r <= reach; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int mx = mx0 + dx, mz = mz0 + dz;
                    if (!L31HostDoorCell(level, mx, mz) || LevelAt(mx, mz) != level) continue;
                    Tile[] tiles = BuildMacro(mx, mz);
                    for (int i = 0; i < tiles.Length; i++)
                        if (tiles[i].Under == Unders.L31HostDoor) return (mx * MacroSize + i % MacroSize, mz * MacroSize + i / MacroSize, tiles[i].Pier);
                }
        return null;
    }

    // ================= The wooden doors in other levels =================

    /// <summary>
    /// A wooden door into the rink in this cell of Level 2, 3 or 6 (<see cref="L31HostDoorCell"/>), on a wall tile of the
    /// level's own wall with solid wall behind it and on either side and open floor in front, Level 3's red brick if it can
    /// be; never in the spawn cell nor the Snackrooms, never on or before a tile anything else has taken.
    /// </summary>
    partial void L31Entrances(Builder b, int mx, int mz)
    {
        if (!L31HostDoorCell(b.Level, mx, mz) || b.IsSpawn || b.Level == 6 && IsSnackrooms(mx, mz)) return;
        int level = b.Level;
        bool Solid(int x, int z) => b.At(x, z).Kind == TileKind.Wall;
        bool Plain(in Tile t) => t.Kind == TileKind.Wall && !t.Tall && t.Under == 0 && t.Variant == 0 && t.Stack == 0
            && (level != 3 || t.Pattern is WallPattern.RedBrick or WallPattern.Cinder or WallPattern.GlazedTile)
            && (level != 6 || t.Pattern == WallPattern.L6Wall) && (level != 2 || t.Pattern == WallPattern.Tunnel);
        static bool Open(in Tile t) => t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox && !t.Sealed && t.Stair == 0
            && t.Under == 0;
        var brick = new List<(int X, int Z, ArchPier Facing)>();
        var other = new List<(int X, int Z, ArchPier Facing)>();
        foreach (var (dx, dz, facing) in new[] { (1, 0, ArchPier.East), (-1, 0, ArchPier.West), (0, 1, ArchPier.South), (0, -1, ArchPier.North) })
            for (int z = 2; z < MacroSize - 2; z++)
                for (int x = 2; x < MacroSize - 2; x++)
                {
                    Tile w = b.At(x, z);
                    if (!Plain(w) || !Open(b.At(x + dx, z + dz))) continue;
                    // Solid behind, and the wall going on to either side
                    if (!Solid(x - dx, z - dz) || !Solid(x + dz, z + dx) || !Solid(x - dz, z - dx)) continue;
                    (w.Pattern == WallPattern.RedBrick || level != 3 ? brick : other).Add((x, z, facing));
                }
        var from = brick.Count > 0 ? brick : other;
        if (from.Count == 0) return;
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltL31HostDoorPick));
        var (px, pz, pf) = from[rng.Range(0, from.Count - 1)];
        ref Tile door = ref b.At(px, pz);
        door.Under = Unders.L31HostDoor;
        door.Pier = pf;
    }
}
