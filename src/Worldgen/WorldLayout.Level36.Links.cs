using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 36, "Airport"'s links with the rest of the world (docs/design/experimental-levels/LINKS.md, "Level 36"). This file is
/// the level's own.
/// <para><b>In:</b> now and then, in the city (Level 11) and in the Suburbs (Level 9), a door in a plain stretch of outside
/// wall under a backlit sign with an airplane on it (Wikidot: "airplane-symbol signs in Levels 11, 9"): a building's front
/// on a sidewalk, a house's siding over its lawn. Two-way: it opens on the claim hall, beside one of the doors under the same
/// sign in the baggage wall, which is the way back (<see cref="L36Mat.LandDoor"/>, every 128 blocks along the wall; one that
/// nothing has come in by is locked).</para>
/// <para><b>Out:</b> each gate's flight lands in one level of six, always the same for that gate, named on the gate's screen
/// (<see cref="L36FlightTo"/>); a restroom sink, overflowed, with your head under it, to the Poolrooms (src/Regions/L36System.cs
/// and src/Thresholds/ThresholdNetwork.L36.cs). Both one-way.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Layout salts of the links (0x2530-0x253F, in the level's own 0x2500-0x25BF): the entrances in the host levels, the flights' levels.</summary>
    private const ulong SaltL36Entrance = 0x2530, SaltL36FlightTo = 0x2532;

    /// <summary>
    /// The salts of the keys the threshold network finds a gate's landing and a sink's surfacing by (in the level's threshold
    /// range, 0x25C0-0x25FF: ThresholdNetwork.L36.cs uses these, and the showcase works out the same places from them).
    /// </summary>
    public const ulong L36FlightKeySalt = 0x25C2, L36SinkKeySalt = 0x25C3;

    /// <summary>
    /// The share of a host level's cells that hold a door into the airport (the progression rule: rare, a walk of kilometres
    /// between them): in the Suburbs one in three thousand, where nearly every chosen cell has a house wall to take it; in the
    /// city one in fourteen hundred, where only about half do (a street crossing, a run of shop fronts). Either way about one
    /// door to every three or four square kilometres, two kilometres or so apart (36links).
    /// </summary>
    public static double L36EntranceChance(int level) => level == 11 ? 1 / 1400.0 : 1 / 3000.0;

    /// <summary>The levels a gate's flight can land in, as their numbers are shown (Wikidot's "every level is only one flight away", the user's six).</summary>
    public static readonly int[] L36FlightLevels = { 11, 9, 37, 3999, 188, 10 };

    /// <summary>The internal level of a shown number from <see cref="L36FlightLevels"/>.</summary>
    public static int L36LevelOf(int shown) => shown switch { 37 => Poolrooms, 3999 => Level3999, 188 => Level188, _ => shown };

    /// <summary>Which of <see cref="L36FlightLevels"/> a gate's flight lands in, by its jet-bridge door (always the same for that gate).</summary>
    public int L36FlightIndex(int doorX, int doorZ) => (int)(Hashing.Hash(seed, doorX, doorZ, SaltL36FlightTo) % (ulong)L36FlightLevels.Length);

    /// <summary>Where a gate's flight lands, as its number is shown (Gate C32's: 186, which never leaves).</summary>
    public int L36FlightTo(L36Gate gate) => gate.SupportGroup ? 186 : L36FlightLevels[L36FlightIndex(gate.DoorX, gate.DoorZ)];

    /// <summary>The flight screen's board for a gate (<see cref="L36FidsTexts"/>): C32's own, else the one naming its flight's level.</summary>
    private byte L36GateBoard(int doorX, int doorZ, bool c32) => (byte)(c32 ? L36BoardC32 : L36BoardTo + L36FlightIndex(doorX, doorZ));

    // ================= The doors in the host levels =================

    /// <summary>Whether a cell of a host level (9 or 11) is one of the few that hold a door into the airport (cheap: no cell is built).</summary>
    public bool IsL36EntranceCell(int mx, int mz)
    {
        if (!ExpEntrances || IsSpawnMacro(mx, mz)) return false;
        double u = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL36Entrance));
        if (u >= L36EntranceChance(11)) return false;
        int level = LevelAt(mx, mz);
        return (level == 9 || level == 11) && u < L36EntranceChance(level);
    }

    /// <summary>A door into the airport in a host level (Pier the way it faces, out onto the sidewalk or the lawn).</summary>
    public static bool IsL36AirportDoor(Tile t) => t.Under == Unders.L36AirportDoor && t.Kind == TileKind.Wall && t.Level is 9 or 11;

    /// <summary>A door under the airplane sign in the baggage wall (the way back of one in a host level).</summary>
    public static bool IsL36LandDoor(Tile t) => t.Level == Level36 && t.Kind == TileKind.Wall && t.Zone != 0 && (t.Detail & L36MatMask) == L36Mat.LandDoor;

    /// <summary>Somewhere to come in by a door: the claim hall's floor, off the belts.</summary>
    public static bool IsL36LandsideSpot(Tile t) =>
        IsArrivalSpot(t) && t.Zone == (byte)L36Zone.Baggage && (t.Detail & L36MatMask) is not (L36Mat.BeltRun or L36Mat.BeltStill);

    /// <summary>Somewhere a flight to the Poolrooms comes down: a dry tiled floor, never the water.</summary>
    public static bool IsL36DryPoolSpot(Tile t) => IsPoolArrivalSpot(t) && t.Depth == 0;

    /// <summary>
    /// The door into the airport in a cell of Level 11 or 9 (called once per cell from <see cref="MarkExpEntrances"/>): in a
    /// few cells (<see cref="L36EntranceChance"/>), on a plain stretch of outside wall facing open ground, under its sign. Only the
    /// door's own tile changes (its Under), on its own salt, so nothing else in the level moves.
    /// </summary>
    partial void L36Entrances(Builder b, int mx, int mz)
    {
        if (b.Level is not (9 or 11) || b.IsSpawn) return;
        if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL36Entrance)) >= L36EntranceChance(b.Level)) return;
        var found = new List<(int X, int Z)>();
        for (int lz = 2; lz < MacroSize - 2; lz++)
            for (int lx = 2; lx < MacroSize - 2; lx++)
                if (L36DoorFits(b, lx, lz)) found.Add((lx, lz));
        if (found.Count == 0) return;
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltL36Entrance + 1));
        var (x, z) = found[rng.Range(0, found.Count - 1)];
        b.At(x, z).Under = Unders.L36AirportDoor;
    }

    /// <summary>
    /// Whether a wall tile of a host cell can take the door: a plain stretch of a building's front on a sidewalk (the city) or of
    /// a house's siding over open ground (the Suburbs), wall on both sides along it, nothing in it or before it.
    /// </summary>
    private static bool L36DoorFits(Builder b, int lx, int lz)
    {
        Tile w = b.At(lx, lz);
        if (w.Kind != TileKind.Wall || w.Under != 0 || w.Variant != 0) return false;
        bool city = b.Level == 11;
        if (city)
        {
            const byte odd = CityDetail.Corner | CityDetail.Party | CityDetail.Storefront | CityDetail.Column | CityDetail.Open | CityDetail.Setback;
            if (w.Depth < 4 || w.Pipe != 0 || (w.Detail & odd) != 0) return false;
            if ((CityKind)w.Zone is not (CityKind.Office or CityKind.Hotel or CityKind.Apartment or CityKind.Sealed or CityKind.Rowhouse)) return false;
        }
        else if (w.Pattern < WallPattern.SidingWhite || w.Pattern > WallPattern.Brick || w.Stack != 0 || w.Depth != 0) return false;
        var (dx, dz) = FacingStep(w.Pier);
        Tile front = b.At(lx + dx, lz + dz);
        if (front.Kind != TileKind.Floor || front.Variant != 0 || front.Under != 0 || front.Sealed || front.SupplyBox || front.Stair != 0 || front.Depth != 0 || front.Roof != 0)
            return false;
        if (city ? front.Floor is not (FloorKind.Sidewalk or FloorKind.CityPlaza) : (front.Height & StoreyPorch) != 0 || front.Floor is FloorKind.PoolDeep) return false;
        // The wall runs on either side, the same wall facing the same way
        for (int s = -1; s <= 1; s += 2)
        {
            Tile n = b.At(lx + dz * s, lz + dx * s);
            if (n.Kind != TileKind.Wall || n.Pier != w.Pier || n.Under != 0) return false;
            if (city ? n.Depth < 4 || n.Pipe != 0 : n.Pattern != w.Pattern) return false;
        }
        return true;
    }

    /// <summary>
    /// The doors into the airport in Levels 9 and 11 nearest a cell, nearest first, out to <paramref name="rings"/> cells (for
    /// the showcase and the harness): where each is, its host and the way it faces.
    /// </summary>
    public List<(int X, int Z, int Level, ArchPier Facing, int Ring)> L36HostDoorsNear(int cx, int cz, int rings, int want, int level = -1)
    {
        var found = new List<(int X, int Z, int Level, ArchPier Facing, int Ring)>();
        for (int r = 0; r <= rings && found.Count < want; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int mx = cx + dx, mz = cz + dz;
                    if (!IsL36EntranceCell(mx, mz) || level >= 0 && LevelAt(mx, mz) != level) continue;
                    Tile[] tiles = BuildMacro(mx, mz);
                    for (int i = 0; i < tiles.Length; i++)
                        if (IsL36AirportDoor(tiles[i]))
                            found.Add((mx * MacroSize + i % MacroSize, mz * MacroSize + i / MacroSize, tiles[i].Level, tiles[i].Pier, r));
                }
        return found;
    }

    /// <summary>The middle of a host level, to look for its doors from: the city's centre, or the Suburbs straight out from the spawn toward it.</summary>
    public (int Mx, int Mz) L36HostCentre(int level)
    {
        if (level == 11) return (CityCentreX, CityCentreZ);
        double angle = Math.Atan2(CityCentreZ - spawnMacroZ, CityCentreX - spawnMacroX), radius = LevelMidRadius(level, angle);
        return (spawnMacroX + (int)Math.Round(Math.Cos(angle) * radius), spawnMacroZ + (int)Math.Round(Math.Sin(angle) * radius));
    }
}
