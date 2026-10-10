using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// The living detail of Level 8's caves and Level 7's sea, all vanilla blocks. Level 8: speleothems tapering from a
/// thick root to a thin tip, hanging lichen, bracket fungi on the walls, a few rare colonies of glowworms in the
/// biggest chambers, cave-ins of loose boulders and larger crystal clusters deep down. Level 7: waterweed in the
/// shallows, a dead reef among the kelp of the twilight zone, shells on the islands' rims.
/// Every choice is made from a hash of where it is, so it agrees from block to block and from chunk to chunk.
/// </summary>
public sealed partial class WorldGenerator
{
    private const ulong SaltSpeleoDown = 0xC410, SaltSpeleoUp = 0xC411, SaltSpeleoDensity = 0xC412, SaltGlowColony = 0xC413,
        SaltGlowSlot = 0xC414, SaltLichen = 0xC415, SaltFungus = 0xC416, SaltRubble = 0xC417, SaltCrystalKind = 0xC418;
    private const ulong SaltShallows = 0x7C10, SaltReef = 0x7C11, SaltShore = 0x7C12;

    /// <summary>How far up or down a speleothem span is looked for; spans taller than this never need clamping.</summary>
    private const int SpanScan = 16;

    // Level 8
    private static readonly string[] StalagThickness = { "14", "12", "10", "08", "06", "04" };
    private readonly Dictionary<string, int[]> stalagIds = new();
    private readonly Dictionary<string, int> boulderIds = new();
    private readonly int[] glowBaseIds = new int[2], glowShortIds = new int[2], glowSegmentIds = new int[2], glowEndIds = new int[2];
    private readonly int[,] lichenIds = new int[2, 4]; // oldmans, lace; top, segment, bottom, short
    private readonly int[,] fungusIds = new int[3, 4]; // tinderhoof, dryadsaddle, whiteoyster; facing the wall N, E, S, W
    private int[] bigCrystalUpIds = Array.Empty<int>(), bigCrystalDownIds = Array.Empty<int>();

    // Level 7
    private int[] seagrassIds = Array.Empty<int>(), lowWeedIds = Array.Empty<int>(), deadCoralIds = Array.Empty<int>(), shellIds = Array.Empty<int>();
    private int seaweedSectionId, seaweedTopId, shoreBoulderId;

    private void InitCaves()
    {
        foreach (string rock in strata)
        {
            if (stalagIds.ContainsKey(rock)) continue;
            var ids = new int[StalagThickness.Length];
            for (int i = 0; i < ids.Length; i++) ids[i] = OptionalId($"game:stalagsection-{rock}-{StalagThickness[i]}");
            stalagIds[rock] = ids;
            boulderIds[rock] = OptionalId($"game:looseboulders-{rock}-free");
        }
        for (int n = 0; n < 2; n++)
        {
            glowBaseIds[n] = OptionalId($"game:glowworms-base{n + 1}");
            glowShortIds[n] = OptionalId($"game:glowworms-base{n + 1}-short");
            glowSegmentIds[n] = OptionalId($"game:glowworms-segment{n + 1}");
            glowEndIds[n] = OptionalId($"game:glowworms-end{n + 1}");
        }
        string[] lichens = { "oldmans", "lace" }, parts = { "top", "segment", "bottom", "short" };
        for (int l = 0; l < 2; l++)
            for (int p = 0; p < 4; p++)
                lichenIds[l, p] = OptionalId($"game:hanginglichen-{lichens[l]}-{parts[p]}");
        // A bracket fungus's last code part is the side its wall is on
        string[] fungi = { "tinderhoof", "dryadsaddle", "whiteoyster" }, sides = { "north", "east", "south", "west" };
        for (int f = 0; f < 3; f++)
            for (int s = 0; s < 4; s++)
                fungusIds[f, s] = OptionalId($"game:mushroom-{fungi[f]}-normal-{sides[s]}");
        var up = new List<int>();
        var down = new List<int>();
        foreach (string type in new[] { "amethyst", "smokyquartz", "milkyquartz", "rosequartz" })
            foreach (string variant in new[] { "large1", "large2", "cluster1", "cluster2" })
            {
                if (OptionalId($"game:crystal-{type}-{variant}-up") is int u and not 0) up.Add(u);
                if (OptionalId($"game:crystal-{type}-{variant}-down") is int d and not 0) down.Add(d);
            }
        bigCrystalUpIds = up.ToArray();
        bigCrystalDownIds = down.ToArray();

        seagrassIds = Present("game:aquatic-seagrass-green-section", "game:aquatic-seagrass-yellow-section",
            "game:aquatic-seagrass-orange-section", "game:aquatic-seagrass-red-section");
        seaweedSectionId = OptionalId("game:seaweed-section");
        seaweedTopId = OptionalId("game:seaweed-top");
        lowWeedIds = Present("game:aquaticplant-bladderwrack", "game:aquaticplant-irishmoss", "game:aquaticplant-sealace");
        deadCoralIds = Present("game:coral-fan-dead-1", "game:coral-fan-dead-2", "game:coral-fan-dead-3", "game:coral-fan-dead-4",
            "game:coral-shrub-dead-1", "game:coral-shrub-dead-2", "game:coral-shrub-dead-3", "game:coral-brain-dead-1",
            "game:coral-branched-dead-1", "game:coral-shelf-tall-dead-1", "game:coral-shelf-short-dead-1", "game:coral-tube-dead-1",
            "game:coral-sponge-vase-dead-1", "game:coral-sponge-lumpy-dead-2", "game:coral-sponge-smooth-dead-3");
        var shells = new List<string>();
        foreach (string type in new[] { "scallop", "clam", "turritella", "conch", "seastar" })
            foreach (string color in new[] { "plain", "latte", "cinnamon" })
                shells.Add($"game:seashell-{type}-{color}");
        shellIds = Present(shells.ToArray());
        shoreBoulderId = OptionalId("game:looseboulders-basalt-free");
        int missing = (seagrassIds.Length < 4 ? 1 : 0) + (lowWeedIds.Length < 3 ? 1 : 0) + (deadCoralIds.Length < 15 ? 1 : 0) + (bigCrystalUpIds.Length < 16 ? 1 : 0)
            + (glowBaseIds[0] == 0 || glowEndIds[1] == 0 ? 1 : 0) + (lichenIds[1, 3] == 0 ? 1 : 0) + (fungusIds[2, 3] == 0 ? 1 : 0) + (seaweedTopId == 0 ? 1 : 0);
        if (missing > 0) api.Logger.Warning("[backrooms] {0} groups of vanilla cave and sea blocks are missing; Levels 7 and 8 will be barer", missing);
    }

    /// <summary>The ids of those of the codes that exist.</summary>
    private int[] Present(params string[] codes)
    {
        var ids = new List<int>();
        foreach (string code in codes)
            if (OptionalId(code) is int id and not 0) ids.Add(id);
        return ids.ToArray();
    }

    // ---- Level 8 ----

    /// <summary>
    /// What grows in an open cave block of Level 8 off the road: a section of a speleothem, of a glowworm or lichen
    /// strand, a bracket fungus on the wall, a cave-in's boulders. -1 where none of these is.
    /// </summary>
    private int CaveFeature(int gx, int y, int gz, int rel)
    {
        CaveColumn col = caveColumns.Get(gx, gz);
        if (col.Tar) return -1;
        int up = 1;
        while (up <= 4 && col.IsCave(y + up)) up++;
        int down = 1;
        while (down <= 3 && col.IsCave(y - down)) down++;

        if (up <= 4)
        {
            int ceilY = y + up;
            var (kind, len, variant) = Hanging(gx, gz, ceilY, col);
            if (kind != Hang.None && up <= len) return HangingBlock(kind, variant, up - 1, len, StrataName(gx, ceilY, gz));
        }
        if (down <= 3)
        {
            int floorY = y - down;
            int len = Rising(gx, gz, floorY, col);
            if (down <= len) return StalagBlock(StrataName(gx, floorY, gz), down - 1, len);
        }
        if (down == 1)
        {
            // A cave-in: loose boulders where a stretch of the ceiling came down
            if (Noise2(gx / 16.0, gz / 16.0, SaltRubble) > 0.55)
            {
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltRubble + 1 + (ulong)(y & 1023)));
                string rock = StrataName(gx, y - 1, gz);
                if (r < 0.1) return boulderIds.TryGetValue(rock, out int boulder) ? boulder : 0;
                if (r < 0.18) return looseStoneIds.TryGetValue(rock, out int stones) ? stones : 0;
            }
        }
        if (down <= 3) return WallFungus(gx, y, gz, rel);
        return -1;
    }

    private enum Hang : byte { None, Stalactite, Glowworms, Lichen }

    /// <summary>What hangs from the ceiling at <paramref name="ceilY"/> of a column, and how far down it reaches.</summary>
    private (Hang Kind, int Length, int Variant) Hanging(int gx, int gz, int ceilY, CaveColumn col)
    {
        ulong h = Hashing.Hash(seed, gx, gz, SaltSpeleoDown + (ulong)(ceilY & 1023));
        double u = Hashing.Unit(h);
        Hang kind = Hang.None;
        int len = 0, variant = (int)((h >> 40) & 1);
        double density = SpeleoDensity(gx, gz);
        if (u < density)
        {
            kind = Hang.Stalactite;
            len = 2 + (int)((h >> 20) % 3);
        }
        else if (GlowSlot(gx, gz))
        {
            kind = Hang.Glowworms;
            len = 1 + (int)((h >> 20) % 4); // 1: a short base alone; otherwise base, segments and an end
        }
        else if (u < density + 0.025 && Noise2(gx / 18.0, gz / 18.0, SaltLichen) > 0.15)
        {
            kind = Hang.Lichen;
            len = 1 + (int)((h >> 20) % 4);
        }
        if (kind == Hang.None) return (kind, 0, 0);
        int gap = SpanBelow(col, ceilY);
        if (gap < 4) return (Hang.None, 0, 0);
        // Glowworms only in the big chambers
        if (kind == Hang.Glowworms && gap < 9) return (Hang.None, 0, 0);
        // At least three blocks of headroom are always left under whatever hangs here
        return (kind, Math.Min(len, gap - 3), variant);
    }

    /// <summary>How tall a stalagmite rises from the floor at <paramref name="floorY"/> (0: none).</summary>
    private int Rising(int gx, int gz, int floorY, CaveColumn col)
    {
        ulong h = Hashing.Hash(seed, gx, gz, SaltSpeleoUp + (ulong)(floorY & 1023));
        if (Hashing.Unit(h) >= SpeleoDensity(gx, gz) * 0.7) return 0;
        // Not where the pools may flood
        if (col.Pool && floorY + 1 - Geometry.FloorY < -18) return 0;
        int len = 1 + (int)((h >> 20) % 3);
        int ceilY = SpanAbove(col, floorY);
        if (ceilY != int.MaxValue)
        {
            int gap = ceilY - floorY - 1;
            if (gap < 4) return 0;
            var (kind, hang, _) = Hanging(gx, gz, ceilY, col);
            len = Math.Min(len, gap - 3 - (kind == Hang.None ? 0 : hang));
        }
        // Anything too tall to step over stands where there is room to walk round it
        if (len >= 2)
        {
            foreach ((int dx, int dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                if (!caveColumns.Get(gx + dx, gz + dz).IsCave(floorY + 1)) { len = 1; break; }
        }
        return Math.Max(len, 0);
    }

    /// <summary>Speleothems gather in groves: a little denser where a slow noise says so.</summary>
    private double SpeleoDensity(int gx, int gz) => 0.03 + 0.1 * Math.Max(0, Noise2(gx / 11.0, gz / 11.0, SaltSpeleoDensity));

    /// <summary>The open height under a ceiling (a large number if it runs on past <see cref="SpanScan"/>).</summary>
    private static int SpanBelow(CaveColumn col, int ceilY)
    {
        for (int k = 1; k <= SpanScan; k++)
            if (!col.IsCave(ceilY - k)) return k - 1;
        return 99;
    }

    /// <summary>The ceiling over a floor, or int.MaxValue if it lies more than <see cref="SpanScan"/> above.</summary>
    private static int SpanAbove(CaveColumn col, int floorY)
    {
        for (int k = 1; k <= SpanScan; k++)
            if (!col.IsCave(floorY + k)) return floorY + k;
        return int.MaxValue;
    }

    /// <summary>
    /// Glowworm colonies: rare patches, and in one only a strand or so in every 8 by 8 columns, so there are never
    /// more than sixteen strands to a chunk (each block of one is a faint light).
    /// </summary>
    private bool GlowSlot(int gx, int gz)
    {
        if (Noise2(gx / 48.0, gz / 48.0, SaltGlowColony) < 0.5) return false;
        int sx = Hashing.FloorDiv(gx, 8), sz = Hashing.FloorDiv(gz, 8);
        ulong h = Hashing.Hash(seed, sx, sz, SaltGlowSlot);
        if (Hashing.Unit(h) > 0.7) return false;
        return Hashing.Mod(gx, 8) == (int)((h >> 20) % 8) && Hashing.Mod(gz, 8) == (int)((h >> 28) % 8);
    }

    /// <summary>The block <paramref name="k"/> below the ceiling of a hanging feature <paramref name="len"/> long.</summary>
    private int HangingBlock(Hang kind, int variant, int k, int len, string rock)
    {
        switch (kind)
        {
            case Hang.Stalactite:
                return StalagBlock(rock, k, len);
            case Hang.Glowworms:
                if (len == 1) return glowShortIds[variant];
                return k == 0 ? glowBaseIds[variant] : k == len - 1 ? glowEndIds[variant] : glowSegmentIds[variant];
            case Hang.Lichen:
                if (len == 1) return lichenIds[variant, 3];
                return lichenIds[variant, k == 0 ? 0 : k == len - 1 ? 2 : 1];
        }
        return 0;
    }

    /// <summary>
    /// Section <paramref name="k"/> (0 at the root) of a speleothem <paramref name="len"/> long: thick where it grows
    /// from the rock, thinning to a point.
    /// </summary>
    private int StalagBlock(string rock, int k, int len)
    {
        if (!stalagIds.TryGetValue(rock, out int[] ids)) return 0;
        // Root thickness by length (longer ones are thicker), tapering to the thinnest at the tip
        int root = len >= 4 ? 1 : len == 3 ? 2 : len == 2 ? 3 : 4;
        int tip = 5;
        int index = len <= 1 ? root : root + (int)Math.Round((tip - root) * (double)k / (len - 1));
        return ids[Math.Clamp(index, 0, ids.Length - 1)];
    }

    /// <summary>A bracket fungus on the wall beside a cave block near the floor, in the damper stretches.</summary>
    private int WallFungus(int gx, int y, int gz, int rel)
    {
        ulong h = Hashing.Hash(seed, gx, gz, SaltFungus + (ulong)(y & 1023));
        if (Hashing.Unit(h) > 0.05) return -1;
        if (Noise2(gx / 20.0, gz / 20.0, SaltFungus + 1) < 0.2) return -1;
        int start = (int)((h >> 24) & 3);
        for (int i = 0; i < 4; i++)
        {
            int side = (start + i) & 3; // north, east, south, west
            int nx = gx + (side == 1 ? 1 : side == 3 ? -1 : 0), nz = gz + (side == 2 ? 1 : side == 0 ? -1 : 0);
            if (!SolidRock(nx, y, nz, rel)) continue;
            double pick = Hashing.Unit(h << 16);
            int species = pick < 0.6 ? 0 : pick < 0.85 ? 1 : 2;
            return fungusIds[species, side];
        }
        return -1;
    }

    /// <summary>Whether a block of Level 8 is surely rock (not a cave, the road's air, or another level).</summary>
    private bool SolidRock(int gx, int y, int gz, int rel)
    {
        Tile n = TileAt(gx, gz);
        if (n.Level != 8) return false;
        if (n.Tall) return true;
        bool open = !n.IsWallLike || n.Kind == TileKind.Doorway;
        if (open && rel >= 0 && rel <= 4) return rel == 0;
        if (n.Variant is Props.CaveVent or Props.AlmondSeep && rel >= 1 && rel <= 4) return false;
        return !IsCave(gx, y, gz);
    }

    /// <summary>The layout tile at a block (cells are chunks, and recently built ones are cached).</summary>
    private Tile TileAt(int gx, int gz)
    {
        int mx = Hashing.FloorDiv(gx, WorldLayout.MacroSize), mz = Hashing.FloorDiv(gz, WorldLayout.MacroSize);
        return Macro(mx, mz)[WorldLayout.TileIndex(gx - mx * WorldLayout.MacroSize, gz - mz * WorldLayout.MacroSize)];
    }

    /// <summary>A large crystal cluster deep down, on the floor or hanging from the ceiling, by its spot.</summary>
    private int BigCrystal(int gx, int gz, bool up)
    {
        int[] ids = up ? bigCrystalUpIds : bigCrystalDownIds;
        if (ids.Length == 0) return 0;
        // One mineral to a stretch of cave, its forms mixed
        int kind = (int)(Hashing.Hash(seed, Hashing.FloorDiv(gx, 40), Hashing.FloorDiv(gz, 40), SaltCrystalKind) % (ulong)Math.Max(1, ids.Length / 4));
        int form = (int)(Hashing.Hash(seed, gx, gz, SaltCrystalKind + 1) % 4);
        return ids[Math.Min(kind * 4 + form, ids.Length - 1)];
    }

    // ---- Level 7 ----

    /// <summary>
    /// What grows on the seabed in open water at <paramref name="rel"/> (above the bed at <paramref name="bed"/>):
    /// waterweed in the shallows, a dead reef in the twilight zone. -1 where nothing does.
    /// </summary>
    private int SeabedGrowth(in Tile t, int gx, int gz, int rel, int bed)
    {
        if (t.Variant != 0 || t.SupplyBox || t.Under != 0 || t.Floor != FloorKind.Seabed) return -1;
        int depth = t.Depth, k = rel - bed; // 1 on the bottom
        ulong h = Hashing.Hash(seed, gx, gz, SaltShallows);
        if (depth < WorldLayout.TwilightDepth)
        {
            // The shallows: patches of waterweed by the islands and the ledges, and a few out in the open shallows
            // (the daylight zone is otherwise barren)
            bool shore = depth <= 10 && NearShore(gx, gz);
            if (depth > 5 && !shore) return -1;
            double meadow = Noise2(gx / 7.0, gz / 7.0, SaltShallows + 1) + (shore ? 0.3 : -0.15);
            if (meadow < 0.15 || Hashing.Unit(h) > 0.45) return -1;
            double pick = Hashing.Unit(h << 12);
            int room = depth - 2; // the tips stay under the surface
            if (pick < 0.45 && seagrassIds.Length > 0)
            {
                int height = Math.Min(1 + (int)((h >> 40) % 3), room);
                // One colour to a patch, mostly green
                int colour = Noise2(gx / 11.0, gz / 11.0, SaltShallows + 2) > 0.3 ? 1 + (int)((h >> 50) % (ulong)Math.Max(1, seagrassIds.Length - 1)) : 0;
                return k <= height ? seagrassIds[Math.Min(colour, seagrassIds.Length - 1)] : -1;
            }
            if (pick < 0.7 && seaweedSectionId != 0)
            {
                int height = Math.Min(2 + (int)((h >> 40) % 3), room);
                if (height < 2) return k == 1 ? seaweedTopId : -1;
                return k < height ? seaweedSectionId : k == height ? seaweedTopId : -1;
            }
            return k == 1 && lowWeedIds.Length > 0 ? lowWeedIds[(int)((h >> 44) % (ulong)lowWeedIds.Length)] : -1;
        }
        if (depth < WorldLayout.MidnightDepth)
        {
            // The twilight zone: a skeletal reef of dead coral between the kelp, grey and bleached
            if (k != 1 || deadCoralIds.Length == 0) return -1;
            if (Noise2(gx / 13.0, gz / 13.0, SaltReef) < 0.25) return -1;
            ulong r = Hashing.Hash(seed, gx, gz, SaltReef + 1);
            if (Hashing.Unit(r) > 0.14) return -1;
            return deadCoralIds[(int)((r >> 32) % (ulong)deadCoralIds.Length)];
        }
        return -1; // the midnight zone and the abyss stay bare
    }

    /// <summary>Whether a sea block is next to an island or a ledge.</summary>
    private bool NearShore(int gx, int gz)
    {
        foreach ((int dx, int dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2) })
        {
            Tile n = TileAt(gx + dx, gz + dz);
            if (n.Level == 7 && n.Kind == TileKind.Floor) return true;
        }
        return false;
    }

    /// <summary>Shells (and now and then a boulder) along an island's rim, just above the water. -1 where none.</summary>
    private int IslandRim(in Tile t, int gx, int gz)
    {
        if (t.Variant != 0 || t.SupplyBox || t.Stack != 0 || t.Floor != FloorKind.Seabed) return -1;
        ulong h = Hashing.Hash(seed, gx, gz, SaltShore);
        double u = Hashing.Unit(h);
        if (u > 0.1) return -1;
        bool rim = false;
        foreach ((int dx, int dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            if (TileAt(gx + dx, gz + dz) is { Level: 7, Kind: TileKind.Water }) { rim = true; break; }
        if (!rim) return -1;
        if (u < 0.075 && shellIds.Length > 0) return shellIds[(int)((h >> 32) % (ulong)shellIds.Length)];
        return shoreBoulderId;
    }
}
