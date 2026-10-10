using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 3999, "The Neon Paradise"'s thresholds (kept as level 19): the ways out of it, and the ways into it from other
/// levels (docs/new-levels/3999-plan.md, as the user directed: ordinary thresholds, no ending). Walked through, two-way;
/// fell, dived or taken, one-way. Salts 0x19C0-0x19FF.
///
/// In: the lone arcade's revolving door in Level 10, at the end of a chain of red-lit windmills (two-way, with a lobby's
/// revolving door); a stretch of Level 11's alley wall flickering purple (two-way, a thin spot back); the glowing
/// magenta tiles at the bottom of a deep pool in the far Poolrooms (one-way, up in a natatorium's violet water); a
/// computer in The End that runs TRUEEND.EXE (one-way, <see cref="L3999TrueEnd"/>); the Hub's door marked 3999 (beside a
/// STAFF ONLY door, <see cref="L3999StaffDoorArrival"/>).
///
/// Out: a lobby's revolving door (to the Level 10 arcade); a STAFF ONLY door (one in six opens, onto the Hub beside a
/// service door, two-way; the rest are locked); the mini arcade's elevator (to Level 0, a thin spot back); a themed
/// cabinet played to the end (one-way, to the level on its marquee); a rusted cabinet walked into (one-way, into the
/// nearest block of the Neon Blackout); a natatorium's floor drain (one-way, into Level 37).
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x19C0-0x19FF).</summary>
    private const ulong SaltL3999Threshold = 0x19C0;

    /// <summary>The share of STAFF ONLY doors that open (onto the Hub), and of The End's computers that run TRUEEND.EXE.</summary>
    private const double L3999StaffOpens = 1 / 6.0, L3999TrueEndShare = 0.06;

    /// <summary>A lobby's revolving door, and the Level 10 arcade's.</summary>
    public static readonly Func<Tile, bool> L3999Revolving = WorldLayout.IsL3999Revolving;
    public static readonly Func<Tile, bool> L3999ArcadeDoor = WorldLayout.IsL3999ArcadeDoor;

    /// <summary>A STAFF ONLY door of the level's.</summary>
    public static readonly Func<Tile, bool> L3999StaffDoor = WorldLayout.IsL3999StaffDoor;

    /// <summary>The mini arcade's elevator.</summary>
    private static readonly Func<Tile, bool> L3999Elevator = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.L3999Elevator && t.Level == WorldLayout.Level3999;

    private Passage L3999Walked(int x, int z, in Tile tile, double rel)
    {
        // Cheap first: none of ours here
        bool ours = tile.Under is >= Unders.L3999First and <= Unders.L3999Last || tile.Level == WorldLayout.Level3999 && tile.Variant == Worldgen.Props.L3999Rusted;
        if (!ours) return null;
        int level = tile.Level;
        if (level == 11 && tile.Under == Unders.L3999GlitchWall && rel > 0.5 && rel < 2.5)
        {
            // The wall gives like static, and the city is gone: two-way, a thin spot back
            var wall = layout.FeatureOrigin(x, z, t => t.Level == 11 && t.Under == Unders.L3999GlitchWall);
            Passage passage = BothWays(wall, KeyOf(wall, SaltL3999Threshold + 1), WorldLayout.Level3999);
            passage.Find = IntoL3999();
            passage.Message = "backrooms:l3999-glitchwall";
            passage.Sound = "game:sounds/effect/translocate-breakdimension";
            return passage;
        }
        if (level == WorldLayout.Poolrooms && tile.Under == Unders.L3999MagentaTiles && rel < -tile.Depth + 2)
        {
            // Down to the glowing tiles, and up through warm violet water
            var tiles = layout.FeatureOrigin(x, z, t => t.Level == WorldLayout.Poolrooms && t.Under == Unders.L3999MagentaTiles);
            return new Passage { Source = tiles, Key = KeyOf(tiles, SaltL3999Threshold + 2), Find = IntoL3999Natatorium(), Message = "backrooms:l3999-arrive-natatorium" };
        }
        if (level != WorldLayout.Level3999) return null;
        if (tile.Variant == Worldgen.Props.L3999Rusted && tile.Kind == TileKind.Floor && rel < 2)
        {
            // It looks solid but isn't: through the machine and into the dark
            var from = (x, z);
            return new Passage
            {
                Source = from, Key = KeyOf(from, SaltL3999Threshold + 3), Message = "backrooms:l3999-rusted", Sound = "game:sounds/effect/translocate-breakdimension",
                Find = key => layout.L3999BlackoutArrival(from.x, from.z, key) is { } a ? (a.X, a.Z, StandHeight) : null,
            };
        }
        if (tile.Under == Unders.L3999Drain && rel < -tile.Depth + 1.5)
        {
            // The drain pulls you down, and down, into white tile
            var drain = layout.FeatureOrigin(x, z, t => t.Level == WorldLayout.Level3999 && t.Under == Unders.L3999Drain);
            Passage passage = OneWay(drain, KeyOf(drain, SaltL3999Threshold + 4), WorldLayout.Poolrooms);
            passage.Message = "backrooms:l3999-drain";
            passage.Sound = "game:sounds/environment/largesplash1";
            return passage;
        }
        return null;
    }

    private Passage L3999Used(int x, int z, int level, string kind, ref string refusal)
    {
        switch (kind)
        {
            case "l3999-revolving" when level == 10:
            {
                // The lone arcade's revolving door: into a lobby, out of its revolving door, which is the way back
                var door = layout.FeatureOrigin(x, z, L3999ArcadeDoor);
                Passage passage = BothWays(door, KeyOf(door, SaltL3999Threshold + 5), WorldLayout.Level3999, L3999Revolving);
                passage.Message = "backrooms:l3999-arrive-lobby";
                return WithSound(passage, "backrooms:sounds/effect/3999/revolving");
            }
            case "l3999-revolving":
            {
                if (level != WorldLayout.Level3999) return null;
                // A lobby's revolving door, out into the car park of a lone arcade in the fields of Level 10
                var door = layout.FeatureOrigin(x, z, L3999Revolving);
                return WithSound(new Passage
                {
                    Source = door, Key = KeyOf(door, SaltL3999Threshold + 6), Find = InL10Arcade(), ReturnFeature = L3999ArcadeDoor, TwoWay = true,
                    Message = "backrooms:l3999-revolving-out",
                }, "backrooms:sounds/effect/3999/revolving");
            }
            case "l3999-staff":
            {
                if (level != WorldLayout.Level3999) return null;
                // Most STAFF ONLY doors are locked; one in six opens onto the Hub, beside a service door, and back
                var door = layout.FeatureOrigin(x, z, L3999StaffDoor);
                ulong key = KeyOf(door, SaltL3999Threshold + 7);
                if (!TryGet(door, out _) && Hashing.Unit(key) >= L3999StaffOpens)
                {
                    refusal = "locked";
                    return null;
                }
                Passage passage = BothWays(door, key, WorldLayout.Hub, HubServiceDoor);
                passage.Message = "backrooms:hub-arrive";
                return WithSound(passage, "game:sounds/block/metaldoor");
            }
            case "l3999-elevator":
            {
                if (level != WorldLayout.Level3999) return null;
                // The mini arcade's elevator goes down to the Lobby; a thin spot there leads back
                var car = layout.FeatureOrigin(x, z, L3999Elevator);
                Passage passage = BothWays(car, KeyOf(car, SaltL3999Threshold + 8), 0);
                passage.Message = "backrooms:l3999-elevator-ride";
                return WithSound(passage, "game:sounds/block/metaldoor");
            }
            case "l3999-cabinet":
            {
                if (level != WorldLayout.Level3999) return null;
                // A themed cabinet, played to the end: the screen fills your eyes, and the game lets you into the level it shows
                Tile here = layout.TileAt(x, z);
                if (here.Variant != Worldgen.Props.L3999Themed) { refusal = "nowhere"; return null; }
                int to = WorldLayout.L3999ThemeLevel(here.Stack);
                Func<ulong, (int X, int Z, double Height)?> find = to switch
                {
                    WorldLayout.RunLevel => IntoRun(),
                    WorldLayout.FunLevel => IntoFun(),
                    WorldLayout.Level974 => IntoL974(),
                    _ => In(to),
                };
                return new Passage
                {
                    Source = (x, z), Key = KeyOf((x, z), SaltL3999Threshold + 9 + (ulong)here.Stack), Find = find,
                    Message = "backrooms:l3999-cabinet-taken", Sound = "backrooms:sounds/effect/3999/taken",
                };
            }
        }
        return null;
    }

    /// <summary>Somewhere to arrive in the level for a key: a lobby's floor (beside a tile matching <paramref name="beside"/>, where one can be found).</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL3999(Func<Tile, bool> beside = null) => In(WorldLayout.Level3999, beside);

    /// <summary>Afloat in a Neon Natatorium's violet water (else a lobby).</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL3999Natatorium() => key =>
        layout.L3999NatatoriumArrival(key) is { } a ? (a.X, a.Z, 0.2) : IntoL3999()(key);

    /// <summary>
    /// Arriving in Level 3999 beside one of its STAFF ONLY doors, in a service corridor or the unit behind it, never in the
    /// Blackout (for the Hub's door marked 3999).
    /// </summary>
    internal Func<ulong, (int X, int Z, double Height)?> L3999StaffDoorArrival() => key =>
    {
        static bool Spot(Tile t) =>
            t.Kind == TileKind.Floor && !t.Sealed && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Stair == 0 && t.Under == 0
            && !WorldLayout.L3999IsDark(t) && !WorldLayout.L3999HasSlab(t);
        if (layout.FindArrival(WorldLayout.Level3999, key, L3999StaffDoor, spot: Spot) is { } a) return (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z));
        return IntoL3999()(key);
    };

    /// <summary>
    /// In front of the lone arcade's revolving door, out in the fields of Level 10: the nearest arcade to a place the key
    /// picks just past the Suburbs.
    /// </summary>
    private Func<ulong, (int X, int Z, double Height)?> InL10Arcade() => key =>
    {
        if (layout.L3999ArcadeNear(key) is not { } site) return null;
        int mx = WorldLayout.MacroOf(site.X), mz = WorldLayout.MacroOf(site.Z);
        static bool Lot(Tile t) => t.Kind == TileKind.Floor && !t.Sealed && t.Variant == 0 && t.Stack == 0 && t.Stair == 0 && t.Under is 0 or Unders.L3999Lot;
        bool Near(int cx, int cz) => Math.Abs(cx - mx) <= 2 && Math.Abs(cz - mz) <= 2;
        return layout.FindArrival(10, key, L3999ArcadeDoor, Near, Lot, near: (mx, mz)) is { } a ? (a.X, a.Z, StandHeight) : null;
    };

    /// <summary>
    /// The End's computers: a few (never the central hall's, nor one that says "=)") run TRUEEND.EXE, and whoever turned
    /// one on is taken to Level 3999, one-way. Null for any other.
    /// </summary>
    public Passage L3999TrueEnd(int x, int z, bool central)
    {
        if (central || Hashing.Unit(KeyOf((x, z), SaltL3999Threshold + 30)) >= L3999TrueEndShare) return null;
        return new Passage { Source = (x, z), Key = KeyOf((x, z), SaltL3999Threshold + 31), Find = IntoL3999(), Message = "backrooms:l3999-arrive-lobby" };
    }
}
