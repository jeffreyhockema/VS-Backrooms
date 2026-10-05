using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 0, "the Lobby". The interior of each cell is laid out by its zone:
/// <list type="bullet">
/// <item>Lobby, Blackout, Arches: recursive binary splitting into randomly sized rooms (4 to 31 blocks) and
/// narrow hallways, joined by doorless gaps. Every split wall gets at least one gap.</item>
/// <item>OpenOffice: wide open carpet broken up by free-standing partitions that stop abruptly.</item>
/// <item>PillarHall: a lattice of pillars aligned across the whole hall, with some pillars missing.</item>
/// </list>
/// Zones are irregular blobs (a jittered Voronoi diagram over a coarse grid of macro cells). Ceiling lights use
/// a lattice per zone, so their spacing and orientation shift when you cross into another area.
/// </summary>
public sealed partial class WorldLayout
{
    private const int RegionSize = 4;
    private const int MinRoom = 4;

    private const ulong SaltRegionSeed = 0x2E61;
    private const ulong SaltRegionKind = 0x2E62;
    private const ulong SaltManila = 0x3A71;
    private const ulong SaltLight = 0x1167;
    private const ulong SaltPillar = 0x9111;
    private const ulong SaltOutlet = 0x0717;

    // ================= Zones =================

    private enum LightStyle : byte { Grid, Rows }

    private readonly struct Region
    {
        public readonly int X, Z;
        public readonly ZoneKind Zone;
        public readonly LightStyle Lights;
        public readonly int LightSpacing;
        public readonly bool LightRowsAlongX;
        public readonly int LightPhaseX, LightPhaseZ;
        public readonly int PillarSpacing, PillarSize, PillarPhaseX, PillarPhaseZ;
        public readonly bool PlusPillars;
        /// <summary>Most walls in an area share one wallpaper, so trim stays consistent.</summary>
        public readonly WallPattern PrimaryPattern;

        public bool SameAs(Region other) => X == other.X && Z == other.Z;

        public Region(ulong seed, int rx, int rz)
        {
            X = rx;
            Z = rz;
            var rng = new Rng(Hashing.Hash(seed, rx, rz, SaltRegionKind));
            double r = rng.NextDouble();
            Zone = r < 0.55 ? ZoneKind.Lobby
                : r < 0.70 ? ZoneKind.OpenOffice
                : r < 0.82 ? ZoneKind.PillarHall
                : r < 0.92 ? ZoneKind.Arches
                : ZoneKind.Blackout;

            Lights = rng.Chance(0.3) ? LightStyle.Rows : LightStyle.Grid;
            LightSpacing = rng.Chance(0.65) ? 3 : 4;
            LightRowsAlongX = rng.Chance(0.5);
            LightPhaseX = rng.Range(0, 11);
            LightPhaseZ = rng.Range(0, 11);

            PillarSpacing = rng.Range(5, 8);
            PillarSize = rng.Chance(0.35) ? 1 : rng.Chance(0.6) ? 2 : 3;
            PlusPillars = PillarSize == 3 && rng.Chance(0.5);
            PillarPhaseX = rng.Range(0, 15);
            PillarPhaseZ = rng.Range(0, 15);
            PrimaryPattern = rng.Chance(0.8) ? WallPattern.Chevron : WallPattern.Dotted;
        }
    }

    private Region RegionAt(int mx, int mz)
    {
        int rx = Hashing.FloorDiv(mx, RegionSize);
        int rz = Hashing.FloorDiv(mz, RegionSize);
        double best = double.MaxValue;
        int bestX = rx, bestZ = rz;
        for (int dz = -1; dz <= 1; dz++)
        {
            for (int dx = -1; dx <= 1; dx++)
            {
                int cx = rx + dx, cz = rz + dz;
                ulong h = Hashing.Hash(seed, cx, cz, SaltRegionSeed);
                double sx = cx * RegionSize + Hashing.Unit(h) * RegionSize;
                double sz = cz * RegionSize + Hashing.Unit(Hashing.Mix(h)) * RegionSize;
                double d = (mx + 0.5 - sx) * (mx + 0.5 - sx) + (mz + 0.5 - sz) * (mz + 0.5 - sz);
                if (d < best) { best = d; bestX = cx; bestZ = cz; }
            }
        }
        return new Region(seed, bestX, bestZ);
    }

    public ZoneKind ZoneAt(int mx, int mz)
    {
        if (IsSpawnMacro(mx, mz)) return ZoneKind.Lobby;
        return RegionAt(mx, mz).Zone;
    }

    /// <summary>The Manila Room: a very rare, quiet 8x8 room with wooden floors, and a table under a chandelier.</summary>
    public bool IsManilaMacro(int mx, int mz)
    {
        if (Math.Abs(mx - spawnMacroX) < 3 && Math.Abs(mz - spawnMacroZ) < 3) return false;
        if (LevelAt(mx, mz) != 0) return false;
        ZoneKind zone = RegionAt(mx, mz).Zone;
        if (zone != ZoneKind.Lobby && zone != ZoneKind.OpenOffice) return false;
        return Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltManila)) < 0.0015;
    }

    private const ulong SaltRedRoom = 0x3A72;

    /// <summary>
    /// A Red Room: a rare cell of Level 0 papered in red and lit by a few dim red lamps, walled off from the rooms
    /// round it but for one gap in each side. Nothing holds here; whatever was left inside is still there.
    /// </summary>
    public bool IsRedRoom(int mx, int mz)
    {
        if (Math.Abs(mx - spawnMacroX) < 6 && Math.Abs(mz - spawnMacroZ) < 6) return false;
        if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltRedRoom)) >= 0.004) return false;
        return LevelAt(mx, mz) == 0 && RegionAt(mx, mz).Zone == ZoneKind.Lobby && !IsManilaMacro(mx, mz);
    }

    // ================= Edges =================

    /// <summary>An edge between two Level 0 cells: walls with gaps, sometimes fully open.</summary>
    private Edge Level0Edge(ref Rng rng, int mx, int mz, int nx, int nz)
    {
        if (IsRedRoom(mx, mz) || IsRedRoom(nx, nz))
        {
            // Cut off from the rest: one narrow way through each side
            var red = new Edge { Pattern = WallPattern.RedRoom, Base = BaseStyle.Baseboard };
            for (int i = 1; i < MacroSize; i++) red.Tiles[i] = EdgeTile.Wall;
            int gap = rng.Range(4, MacroSize - 6);
            red.Tiles[gap] = red.Tiles[gap + 1] = EdgeTile.Open;
            return red;
        }
        ZoneKind a = ZoneAt(mx, mz), b = ZoneAt(nx, nz);
        bool sameRegion = RegionAt(mx, mz).SameAs(RegionAt(nx, nz));
        WallPattern pattern = a == ZoneKind.Arches || b == ZoneKind.Arches ? WallPattern.Cream : RollPattern(ref rng, RegionAt(mx, mz).PrimaryPattern);
        var edge = new Edge { Pattern = pattern, Base = BaseFor(pattern) };

        static bool IsOpenZone(ZoneKind z) => z is ZoneKind.PillarHall or ZoneKind.OpenOffice;
        if (sameRegion && IsOpenZone(a) && IsOpenZone(b)) return edge;
        // Neighbouring rooms in the same area sometimes merge into one bigger, odd-shaped room
        if (sameRegion && rng.Chance(0.3)) return edge;

        for (int i = 1; i < MacroSize;)
        {
            int len = rng.Range(3, 9);
            bool wall = rng.Chance(0.5);
            for (int k = i; k < Math.Min(MacroSize, i + len); k++) edge.Tiles[k] = wall ? EdgeTile.Wall : EdgeTile.Open;
            i += len;
        }

        // Always leave at least one walkable passage, which keeps the whole level connected
        int width = rng.Range(2, 4);
        int start = rng.Range(2, MacroSize - 1 - width);
        for (int k = start; k < start + width; k++) edge.Tiles[k] = EdgeTile.Open;
        return edge;
    }

    private void BuildLevel0(Builder b, int mx, int mz)
    {
        b.Zone = ZoneAt(mx, mz);
        Region region = RegionAt(mx, mz);
        b.Primary = region.PrimaryPattern;

        if (IsManilaMacro(mx, mz))
        {
            BuildManila(b);
        }
        else
        {
            switch (b.Zone)
            {
                case ZoneKind.OpenOffice: BuildOffice(b); break;
                case ZoneKind.PillarHall: BuildPillars(b, region, mx, mz); break;
                default: Split(b, 1, 1, MacroSize - 1, MacroSize - 1); break;
            }
        }

        if (b.Zone == ZoneKind.Blackout) SoakCarpet(b);
        if (IsRedRoom(mx, mz))
        {
            // Every wall red, the carpet stained dark, no light but the red lamps; and what others left behind
            for (int i = 0; i < b.Tiles.Length; i++)
            {
                ref Tile t = ref b.Tiles[i];
                b.Mood[i] = LightMood.Red;
                if (t.IsWallLike && t.Pattern <= WallPattern.Manila) { t.Pattern = WallPattern.RedRoom; t.Base = BaseStyle.Baseboard; }
                if (t.Kind == TileKind.Pit) t.Kind = TileKind.Floor;
                if (t.Kind == TileKind.Floor) t.Floor = FloorKind.Stained;
            }
            PlaceBoxNearWall(b);
            PlaceBoxNearWall(b);
        }
        PlaceLights(b, region, mx, mz);
        PlaceOutlets(b, mx, mz);
        if (b.IsSpawn) PlaceSpawnBox(b);
        if (TouchesLevel(mx, mz, 1)) WearAway(b, mx, mz);
    }

    /// <summary>
    /// Next to Level 1 the Lobby starts to give way: carpet worn through to concrete and ceiling tiles missing,
    /// so walking out of Level 0 feels gradual.
    /// </summary>
    private void WearAway(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                double patch = Noise((mx * MacroSize + lx) / 5.0, (mz * MacroSize + lz) / 5.0, SaltOutlet + 9);
                if (tile.Kind == TileKind.Floor && patch > 0.15) tile.Floor = FloorKind.Concrete;
                if (!tile.IsWallLike && tile.Ceiling == CeilingKind.Tile && patch > 0.3) tile.Worn = true;
            }
        }
    }

    // ---- Lobby: recursive splitting ----

    /// <summary>Splits the inclusive rectangle into rooms. Walls go on the split lines.</summary>
    private void Split(Builder b, int x0, int z0, int x1, int z1)
    {
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        // Hallways narrower than a room are never cut crosswise
        bool canSplitX = w >= 2 * MinRoom + 1 && h >= MinRoom;
        bool canSplitZ = h >= 2 * MinRoom + 1 && w >= MinRoom;
        if (!canSplitX && !canSplitZ) { Room(b, x0, z0, x1, z1); return; }

        int area = w * h;
        double stopChance = area <= 64 ? 0.8 : area <= 144 ? 0.5 : area <= 300 ? 0.2 : 0;
        if (b.Rng.Chance(stopChance)) { Room(b, x0, z0, x1, z1); return; }

        bool splitX = canSplitX && (!canSplitZ || b.Rng.Chance(w >= h ? 0.8 : 0.2));
        int len = splitX ? w : h;

        int s;
        if (b.Rng.Chance(0.12))
        {
            // A narrow 1-2 block hallway along one side
            int width = b.Rng.Range(1, 2);
            s = b.Rng.Chance(0.5) ? width : len - 1 - width;
        }
        else
        {
            s = b.Rng.Range(MinRoom, len - 1 - MinRoom);
        }

        if (splitX)
        {
            BuildWall(b, x0 + s, z0, alongZ: true, z1 - z0 + 1);
            Split(b, x0, z0, x0 + s - 1, z1);
            Split(b, x0 + s + 1, z0, x1, z1);
        }
        else
        {
            BuildWall(b, x0, z0 + s, alongZ: false, x1 - x0 + 1);
            Split(b, x0, z0, x1, z0 + s - 1);
            Split(b, x0, z0 + s + 1, x1, z1);
        }
    }

    /// <summary>A straight wall of length <paramref name="len"/> starting at (x, z), with at least one gap.</summary>
    private void BuildWall(Builder b, int x, int z, bool alongZ, int len)
    {
        ref Rng rng = ref b.Rng;
        var open = new bool[len];

        int gaps = len < 9 ? 1 : rng.Chance(0.55) ? 1 : 2;
        for (int n = 0; n < gaps; n++)
        {
            int width = Math.Min(len, rng.Range(2, Math.Min(4, len - 1)));
            int start = rng.Range(0, len - width);
            for (int k = start; k < start + width; k++) open[k] = true;
        }

        if (b.Zone == ZoneKind.Arches)
        {
            BuildArchWall(b, x, z, alongZ, open);
            return;
        }

        // Partition walls often just stop short, leaving the end open
        if (len >= 6 && rng.Chance(0.35))
        {
            int cut = rng.Range(2, Math.Min(5, len - 3));
            bool atStart = rng.Chance(0.5);
            for (int k = 0; k < cut; k++) open[atStart ? k : len - 1 - k] = true;
        }

        WallPattern pattern = RollPattern(ref rng, b.Primary);
        BaseStyle baseStyle = BaseFor(pattern);
        for (int k = 0; k < len; k++)
        {
            if (open[k]) continue;
            SetWall(ref b.At(alongZ ? x : x + k, alongZ ? z + k : z), pattern, baseStyle);
        }
    }

    /// <summary>Piers every third block with pairs of arched openings over half-height walls between them.</summary>
    private static void BuildArchWall(Builder b, int x, int z, bool alongZ, bool[] open)
    {
        BaseStyle baseStyle = BaseFor(WallPattern.Cream);
        bool anyDoor = false;
        int len = open.Length;

        for (int pass = 0; pass < 2; pass++)
        {
            for (int k = 0; k < len; k++)
            {
                int phase = k % 3;
                ref Tile tile = ref b.At(alongZ ? x : x + k, alongZ ? z + k : z);
                // A lone opening at the very end would have no pier to rest on
                if (phase == 0 || (phase == 1 && k == len - 1))
                {
                    SetWall(ref tile, WallPattern.Cream, baseStyle);
                    continue;
                }

                // Second pass only runs when the first produced no walkable opening: force the first pair open
                bool door = open[k] || (pass == 1 && k <= 2);
                tile.Kind = door ? TileKind.ArchDoor : TileKind.ArchWindow;
                tile.Pattern = WallPattern.Cream;
                tile.Base = baseStyle;
                bool towardStart = phase == 1;
                tile.Pier = alongZ ? (towardStart ? ArchPier.North : ArchPier.South) : (towardStart ? ArchPier.West : ArchPier.East);
                anyDoor |= door;
            }
            if (anyDoor || len < 3) break;
        }
    }

    private void Room(Builder b, int x0, int z0, int x1, int z1)
    {
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        ref Rng rng = ref b.Rng;

        // Pits are lethal, so they only appear in lit areas where they can be seen
        bool pitsAllowed = !b.IsSpawn && b.Zone == ZoneKind.Lobby;
        if (pitsAllowed && w >= 7 && h >= 7 && rng.Chance(0.015))
        {
            // A grid of 2x2 shafts with thin strips of carpet between them and a walkway around the edge
            for (int z = z0 + 1; z < z1; z++)
            {
                for (int x = x0 + 1; x < x1; x++)
                {
                    if ((x - x0 - 1) % 3 != 2 && (z - z0 - 1) % 3 != 2) b.At(x, z).Kind = TileKind.Pit;
                }
            }
            FillMood(b, x0, z0, x1, z1, LightMood.Half);
            return;
        }

        if (!b.IsSpawn && b.Zone != ZoneKind.Blackout) FillMood(b, x0, z0, x1, z1, RollMood(ref rng));

        if (b.Zone == ZoneKind.Blackout && w >= 3 && h >= 3 && rng.Chance(0.15))
        {
            for (int z = z0; z <= z1; z++)
                for (int x = x0; x <= x1; x++)
                    b.At(x, z).Kind = TileKind.Water;
            return;
        }

        if (!b.IsSpawn && w >= 3 && h >= 3 && rng.Chance(0.07))
        {
            // Wanderers leave their supplies in corners
            int bx = rng.Chance(0.5) ? x0 : x1;
            int bz = rng.Chance(0.5) ? z0 : z1;
            b.At(bx, bz).SupplyBox = true;
        }

        if (rng.Chance(0.3)) Stain(b, rng.Range(x0, x1), rng.Range(z0, z1), rng.Range(1, 3));
    }

    // ---- Open office ----

    private static void BuildOffice(Builder b)
    {
        ref Rng rng = ref b.Rng;
        int partitions = rng.Range(3, 6);
        for (int n = 0; n < partitions; n++)
        {
            WallPattern pattern = RollPattern(ref rng, b.Primary);
            BaseStyle baseStyle = BaseFor(pattern);
            bool alongZ = rng.Chance(0.5);
            int x = rng.Range(2, MacroSize - 3);
            int z = rng.Range(2, MacroSize - 3);
            int len = rng.Range(4, 13);
            int dir = rng.Chance(0.5) ? 1 : -1;
            int endX = x, endZ = z;
            for (int k = 0; k < len; k++)
            {
                int px = alongZ ? x : x + k * dir;
                int pz = alongZ ? z + k * dir : z;
                if (!InInterior(px, pz)) break;
                SetWall(ref b.At(px, pz), pattern, baseStyle);
                endX = px; endZ = pz;
            }

            if (rng.Chance(0.3))
            {
                // L-shaped partition
                int legDir = rng.Chance(0.5) ? 1 : -1;
                int leg = rng.Range(3, 7);
                for (int k = 1; k <= leg; k++)
                {
                    int px = alongZ ? endX + k * legDir : endX;
                    int pz = alongZ ? endZ : endZ + k * legDir;
                    if (!InInterior(px, pz)) break;
                    SetWall(ref b.At(px, pz), pattern, baseStyle);
                }
            }
        }

        if (rng.Chance(0.3))
        {
            int columns = rng.Range(2, 4);
            for (int n = 0; n < columns; n++)
            {
                SetWall(ref b.At(rng.Range(2, MacroSize - 3), rng.Range(2, MacroSize - 3)), b.Primary, BaseFor(b.Primary));
            }
        }

        if (!b.IsSpawn && rng.Chance(0.25)) PlaceBoxNearWall(b);
        if (!b.IsSpawn) MoodPatch(b);
        for (int n = 0; n < 2; n++) Stain(b, rng.Range(1, MacroSize - 1), rng.Range(1, MacroSize - 1), rng.Range(1, 3));
    }

    // ---- Pillar halls ----

    private void BuildPillars(Builder b, Region region, int mx, int mz)
    {
        int spacing = region.PillarSpacing, size = region.PillarSize;
        // Includes the edge lines (lx/lz = 0) where they are open, so the lattice is unbroken across cells
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Floor) continue;

                int gx = mx * MacroSize + lx - region.PillarPhaseX;
                int gz = mz * MacroSize + lz - region.PillarPhaseZ;
                int pillarX = Hashing.FloorDiv(gx, spacing), pillarZ = Hashing.FloorDiv(gz, spacing);
                ulong h = Hashing.Hash(seed, pillarX, pillarZ, SaltPillar);
                double r = Hashing.Unit(h);
                if (r < 0.06) continue; // missing pillar

                // A few pillars stand one block out of line
                int shiftX = r > 0.96 ? 1 : 0;
                int shiftZ = r > 0.93 && r <= 0.96 ? 1 : 0;
                int ix = Hashing.Mod(gx, spacing) - shiftX;
                int iz = Hashing.Mod(gz, spacing) - shiftZ;
                if (ix < 0 || iz < 0 || ix >= size || iz >= size) continue;
                if (region.PlusPillars && ix != 1 && iz != 1) continue;

                SetWall(ref tile, region.PrimaryPattern, BaseFor(region.PrimaryPattern));
            }
        }

        ref Rng rng = ref b.Rng;
        if (!b.IsSpawn && rng.Chance(0.12)) PlaceBoxNearWall(b);
        if (!b.IsSpawn) MoodPatch(b);
        for (int n = 0; n < 3; n++) Stain(b, rng.Range(1, MacroSize - 1), rng.Range(1, MacroSize - 1), rng.Range(1, 3));
    }

    // ---- The Manila Room ----

    private static void BuildManila(Builder b)
    {
        const int outer0 = 11, outer1 = 22; // two-block-thick walls around an 8x8 room (13..20)
        for (int z = outer0; z <= outer1; z++)
        {
            for (int x = outer0; x <= outer1; x++)
            {
                bool wall = x <= outer0 + 1 || x >= outer1 - 1 || z <= outer0 + 1 || z >= outer1 - 1;
                ref Tile tile = ref b.At(x, z);
                if (wall)
                {
                    SetWall(ref tile, WallPattern.Manila, BaseStyle.Baseboard);
                }
                else
                {
                    tile.Floor = FloorKind.Wood;
                }
                b.Mood[TileIndex(x, z)] = LightMood.None;
            }
        }

        // A door in each wall
        const int mid = 16;
        foreach ((int x, int z) in new[] { (outer0, mid), (outer0 + 1, mid), (outer1, mid), (outer1 - 1, mid), (mid, outer0), (mid, outer0 + 1), (mid, outer1), (mid, outer1 - 1) })
        {
            b.At(x, z).Kind = TileKind.Doorway;
        }

        // A table in the middle of the room, under a chandelier
        b.At(mid, mid).Ceiling = CeilingKind.Chandelier;
        b.At(mid, mid).Variant = Props.RoundTable;
        b.At(outer0 + 2, outer0 + 2).SupplyBox = true;
    }

    // ================= Details =================

    private void PlaceLights(Builder b, Region region, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int index = TileIndex(lx, lz);
                ref Tile tile = ref b.Tiles[index];
                LightMood mood = b.Zone == ZoneKind.Blackout ? LightMood.Blackout : b.Mood[index];
                if (tile.IsWallLike || tile.Ceiling != CeilingKind.Tile || mood == LightMood.None) continue;

                int gx = mx * MacroSize + lx - region.LightPhaseX;
                int gz = mz * MacroSize + lz - region.LightPhaseZ;
                bool fixture, emitter;
                if (region.Lights == LightStyle.Grid)
                {
                    int spacing = region.LightSpacing;
                    fixture = Hashing.Mod(gx, spacing) == 0 && Hashing.Mod(gz, spacing) == 0;
                    emitter = Hashing.Mod(Hashing.FloorDiv(gx, spacing), 2) == 0 && Hashing.Mod(Hashing.FloorDiv(gz, spacing), 2) == 0;
                }
                else
                {
                    // Strips of two panels, three blocks apart along the row, rows four blocks apart
                    int along = region.LightRowsAlongX ? gx : gz;
                    int across = region.LightRowsAlongX ? gz : gx;
                    fixture = Hashing.Mod(along, 3) < 2 && Hashing.Mod(across, 4) == 0;
                    emitter = Hashing.Mod(along, 6) == 0 && Hashing.Mod(Hashing.FloorDiv(across, 4), 2) == 0;
                }
                if (!fixture) continue;
                CeilingKind working = emitter ? CeilingKind.LightOn : CeilingKind.LightLit;

                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltLight));
                tile.Ceiling = mood switch
                {
                    // Mostly working, some dead, a few never installed, the odd one failing
                    LightMood.Normal => r < 0.03 ? CeilingKind.Tile : r < 0.09 ? CeilingKind.LightOff : r < 0.11 ? CeilingKind.LightFlicker : working,
                    LightMood.Half => r < 0.5 ? working : CeilingKind.LightOff,
                    LightMood.Dim => r < 0.6 ? CeilingKind.LightOff : r < 0.85 ? CeilingKind.LightFlicker : working,
                    LightMood.Failing => r < 0.25 ? CeilingKind.LightOff : CeilingKind.LightFlicker,
                    LightMood.Dark => CeilingKind.LightOff,
                    LightMood.Red => r < 0.3 ? CeilingKind.LampRed : CeilingKind.Tile,
                    // Blackout zones: dead fixtures, and now and then one that still sputters
                    _ => r < 0.05 ? CeilingKind.LightOff : r < 0.08 ? CeilingKind.LightFlicker : CeilingKind.Tile,
                };
            }
        }
    }

    private void PlaceOutlets(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Wall || tile.Pattern is WallPattern.Cream or WallPattern.Manila) continue;
                if (Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltOutlet)) < 0.04) tile.Outlet = true;
            }
        }
    }

    private static void SoakCarpet(Builder b)
    {
        for (int i = 0; i < b.Tiles.Length; i++)
        {
            if (b.Tiles[i].Floor is FloorKind.Carpet or FloorKind.Stained) b.Tiles[i].Floor = FloorKind.Soaked;
        }
    }

    private static void Stain(Builder b, int cx, int cz, int radius)
    {
        for (int z = cz - radius; z <= cz + radius; z++)
        {
            for (int x = cx - radius; x <= cx + radius; x++)
            {
                if (!InInterior(x, z)) continue;
                int dx = x - cx, dz = z - cz;
                // Ragged edge
                if (dx * dx + dz * dz > radius * radius + b.Rng.Range(-1, 1)) continue;
                ref Tile tile = ref b.At(x, z);
                if (tile.Floor == FloorKind.Carpet) tile.Floor = FloorKind.Stained;
            }
        }
    }

    private static void PlaceBoxNearWall(Builder b)
    {
        for (int attempt = 0; attempt < 40; attempt++)
        {
            int x = b.Rng.Range(1, MacroSize - 2), z = b.Rng.Range(1, MacroSize - 2);
            ref Tile tile = ref b.At(x, z);
            if (tile.Kind != TileKind.Floor) continue;
            if (b.At(x + 1, z).Kind == TileKind.Wall || b.At(x - 1, z).Kind == TileKind.Wall
                || b.At(x, z + 1).Kind == TileKind.Wall || b.At(x, z - 1).Kind == TileKind.Wall)
            {
                tile.SupplyBox = true;
                return;
            }
        }
    }

    private static void FillMood(Builder b, int x0, int z0, int x1, int z1, LightMood mood)
    {
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
                b.Mood[TileIndex(x, z)] = mood;
    }

    /// <summary>Most rooms are evenly lit; some are dim, some have failing lights, a few have gone dark.</summary>
    private static LightMood RollMood(ref Rng rng)
    {
        double r = rng.NextDouble();
        return r < 0.03 ? LightMood.Dark : r < 0.10 ? LightMood.Dim : r < 0.17 ? LightMood.Failing : LightMood.Normal;
    }

    /// <summary>Open areas have no rooms, so moods come in roughly round patches instead.</summary>
    private static void MoodPatch(Builder b)
    {
        LightMood mood = RollMood(ref b.Rng);
        if (mood == LightMood.Normal) return;
        int cx = b.Rng.Range(4, MacroSize - 5), cz = b.Rng.Range(4, MacroSize - 5), radius = b.Rng.Range(5, 10);
        for (int z = 0; z < MacroSize; z++)
            for (int x = 0; x < MacroSize; x++)
                if ((x - cx) * (x - cx) + (z - cz) * (z - cz) <= radius * radius) b.Mood[TileIndex(x, z)] = mood;
    }

}
