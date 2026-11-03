using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// The experimental levels' features (FeatureCatalog's Levels 73 to 47, and their ways in standing in the levels they lead out
/// of). Those levels are regions laid out once round a fixed middle, so the places their showcase tours photograph
/// (<see cref="Showcase"/>, each level's WorldLayout.&lt;Level&gt;.Showcase.cs) are the finder: a feature is a list of spot
/// names from one level's tour, and the nearest of them that stands in the player's level is where it puts you, on the
/// spot's own feet and looking its own way. A level's tour is worked out once and kept.
/// </summary>
public sealed partial class FeatureFinder
{
    /// <summary>Each such feature's code: the level whose showcase tour has its spots, and their names.</summary>
    private static readonly Dictionary<string, (int Tour, string[] Spots)> ShowcaseFeatures = new()
    {
        // ----- Level 73, the Redlands -----
        ["l73run"] = (WorldLayout.Level73, new[] { "the-run" }),
        ["l73path"] = (WorldLayout.Level73, new[] { "path-foot" }),
        ["l73gate"] = (WorldLayout.Level73, new[] { "gatehouse" }),
        ["l73door"] = (WorldLayout.Level73, new[] { "keep-door", "keep-front" }),
        ["l73hall"] = (WorldLayout.Level73, new[] { "main-hall", "stair" }),
        ["l73dining"] = (WorldLayout.Level73, new[] { "dining-hall" }),
        ["l73kitchen"] = (WorldLayout.Level73, new[] { "kitchen", "cellar" }),
        ["l73guest"] = (WorldLayout.Level73, new[] { "guest-room", "guest-fire" }),
        ["l73bath"] = (WorldLayout.Level73, new[] { "bathroom" }),
        ["l73library"] = (WorldLayout.Level73, new[] { "library" }),
        ["l73coranrooms"] = (WorldLayout.Level73, new[] { "solar", "master-bedroom" }),
        ["l73attic"] = (WorldLayout.Level73, new[] { "roof-attic" }),
        ["l73fields"] = (WorldLayout.Level73, new[] { "fields", "track", "dead-tree", "great-hound" }),
        ["l73shore"] = (WorldLayout.Level73, new[] { "shore-moon" }),
        ["l73northdoor"] = (WorldLayout.Level73, new[] { "north-door" }),
        // ----- The Basement -----
        ["bsmcrack"] = (WorldLayout.Basement, new[] { "crack-room" }),
        ["bsmfurnace"] = (WorldLayout.Basement, new[] { "furnace", "fusebox" }),
        ["bsmlaundry"] = (WorldLayout.Basement, new[] { "laundry" }),
        ["bsmworkshop"] = (WorldLayout.Basement, new[] { "workshop" }),
        ["bsmrec"] = (WorldLayout.Basement, new[] { "rec-room" }),
        ["bsmroot"] = (WorldLayout.Basement, new[] { "root-cellar" }),
        ["bsmstore"] = (WorldLayout.Basement, new[] { "store", "store-shelves" }),
        ["bsmfinished"] = (WorldLayout.Basement, new[] { "finished" }),
        ["bsmhall"] = (WorldLayout.Basement, new[] { "hall", "long-view" }),
        ["bsmstair"] = (WorldLayout.Basement, new[] { "stairwell-door" }),
        ["bsmflood"] = (WorldLayout.Basement, new[] { "flood-passage", "flood-stairs" }),
        ["bsmdry"] = (WorldLayout.Basement, new[] { "dry-patch" }),
        ["bsmlift"] = (WorldLayout.Basement, new[] { "lift" }),
        // ----- Level 52, the Greenfield Campus -----
        ["l52quad"] = (WorldLayout.Level52, new[] { "entrance", "approach", "way-back-quad" }),
        ["l52courtyard"] = (WorldLayout.Level52, new[] { "courtyard", "fountain" }),
        ["l52corridor"] = (WorldLayout.Level52, new[] { "corridor", "stair-hall" }),
        ["l52classroom"] = (WorldLayout.Level52, new[] { "classroom" }),
        ["l52lab"] = (WorldLayout.Level52, new[] { "lab" }),
        ["l52library"] = (WorldLayout.Level52, new[] { "library" }),
        ["l52office"] = (WorldLayout.Level52, new[] { "front-office", "staff-room" }),
        ["l52meg"] = (WorldLayout.Level52, new[] { "meg-offices" }),
        ["l52canteen"] = (WorldLayout.Level52, new[] { "canteen" }),
        ["l52gym"] = (WorldLayout.Level52, new[] { "gym" }),
        ["l52lecture"] = (WorldLayout.Level52, new[] { "lecture" }),
        ["l52clock"] = (WorldLayout.Level52, new[] { "clock-tower" }),
        ["l52gap"] = (WorldLayout.Level52, new[] { "gate-boards" }),
        ["l52turner"] = (WorldLayout.Level52, new[] { "turner-court" }),
        ["l52barry"] = (WorldLayout.Level52, new[] { "barry-warehouse", "barry-sign" }),
        ["l52base"] = (WorldLayout.Level52, new[] { "abandoned-base" }),
        // ----- Level 31, the Roller Rink -----
        ["l31rink"] = (WorldLayout.Level31, new[] { "rink", "rink-star" }),
        ["l31dj"] = (WorldLayout.Level31, new[] { "dj" }),
        ["l31lobby"] = (WorldLayout.Level31, new[] { "lobby", "lobby-front" }),
        ["l31foodcourt"] = (WorldLayout.Level31, new[] { "foodcourt", "snackwindow" }),
        ["l31rental"] = (WorldLayout.Level31, new[] { "rental", "coach" }),
        ["l31arcade"] = (WorldLayout.Level31, new[] { "arcade", "prizes" }),
        ["l31cinema"] = (WorldLayout.Level31, new[] { "cinema" }),
        ["l31service"] = (WorldLayout.Level31, new[] { "corridor" }),
        ["l31lounge"] = (WorldLayout.Level31, new[] { "lounge" }),
        ["l31hvac"] = (WorldLayout.Level31, new[] { "hvac" }),
        ["l31bath"] = (WorldLayout.Level31, new[] { "bath", "restroom" }),
        ["l31neon"] = (WorldLayout.Level31, new[] { "hall", "glowroom" }),
        ["l31revolving"] = (WorldLayout.Level31, new[] { "revolving" }),
        ["l31doorback"] = (WorldLayout.Level31, new[] { "lobbydoor" }),
        // ----- Level 36, the Airport -----
        ["l36carousel"] = (WorldLayout.Level36, new[] { "carousel", "claim-hall", "arrivals-board" }),
        ["l36doorback"] = (WorldLayout.Level36, new[] { "land-door" }),
        ["l36lostfound"] = (WorldLayout.Level36, new[] { "lost-and-found" }),
        ["l36checkin"] = (WorldLayout.Level36, new[] { "checkin", "departures-board", "customs" }),
        ["l36agency"] = (WorldLayout.Level36, new[] { "travel-agency" }),
        ["l36security"] = (WorldLayout.Level36, new[] { "security" }),
        ["l36concourse"] = (WorldLayout.Level36, new[] { "concourse", "travelators", "pier", "unit-info" }),
        ["l36gate"] = (WorldLayout.Level36, new[] { "holdroom", "gate-counter", "gate-screen", "gate-sign" }),
        ["l36restroom"] = (WorldLayout.Level36, new[] { "restroom" }),
        ["l36dutyfree"] = (WorldLayout.Level36, new[] { "duty-free", "shop-fashion", "services" }),
        ["l36food"] = (WorldLayout.Level36, new[] { "food-court", "food-stalls" }),
        ["l36lounge"] = (WorldLayout.Level36, new[] { "lounge" }),
        ["l36meeting"] = (WorldLayout.Level36, new[] { "meeting-place", "meeting-kiosk" }),
        ["l36service"] = (WorldLayout.Level36, new[] { "service" }),
        ["l36blackout"] = (WorldLayout.Level36, new[] { "blackout" }),
        ["l36limit"] = (WorldLayout.Level36, new[] { "limit" }),
        // ----- Level 120, Broken Servos -----
        ["l120aisle"] = (WorldLayout.Level120, new[] { "server-aisle", "cold-aisle", "lit-rack", "wrecked-bank", "row-ends" }),
        ["l120terminal"] = (WorldLayout.Level120, new[] { "boot-screen", "terminal-room", "noc-screens" }),
        ["l120ups"] = (WorldLayout.Level120, new[] { "ups-room" }),
        ["l120cooling"] = (WorldLayout.Level120, new[] { "crac" }),
        ["l120storage"] = (WorldLayout.Level120, new[] { "storage" }),
        ["l120racks"] = (WorldLayout.Level120, new[] { "rack-doors", "rack-network", "rack-storage", "hot-aisle", "rack-torn" }),
        ["l120firesup"] = (WorldLayout.Level120, new[] { "fire-suppression" }),
        ["l120tapelib"] = (WorldLayout.Level120, new[] { "tape-library" }),
        ["l120consoles"] = (WorldLayout.Level120, new[] { "noc-consoles" }),
        ["l120cables"] = (WorldLayout.Level120, new[] { "spilled-cables", "floor-hole" }),
        ["l120halldoor"] = (WorldLayout.Level120, new[] { "hall-door" }),
        ["l120exit"] = (WorldLayout.Level120, new[] { "hall-exit" }),
        ["l120passage"] = (WorldLayout.Level120, new[] { "passage-tube", "passage-dark" }),
        ["l120void"] = (WorldLayout.Level120, new[] { "void-doors", "void-odd" }),
        ["l120hallway"] = (WorldLayout.Level120, new[] { "hallway-lane" }),
        ["l120window"] = (WorldLayout.Level120, new[] { "void-window", "hallway-window" }),
        ["l120doorback"] = (WorldLayout.Level120, new[] { "door-back" }),
        ["l120warmdoor"] = (WorldLayout.Level120, new[] { "hallway-door" }),
        // ----- Level 15, the Futuristic Halls -----
        ["l15hall"] = (WorldLayout.Level15, new[] { "hall", "crossing", "hall-sign", "sector-map" }),
        ["l15corridor"] = (WorldLayout.Level15, new[] { "corridor", "service" }),
        ["l15machine"] = (WorldLayout.Level15, new[] { "machine-room", "machine-gate" }),
        ["l15control"] = (WorldLayout.Level15, new[] { "control-room" }),
        ["l15lab"] = (WorldLayout.Level15, new[] { "lab", "lab-glass" }),
        ["l15lecture"] = (WorldLayout.Level15, new[] { "lecture-hall", "lecture-stage" }),
        ["l15dorm"] = (WorldLayout.Level15, new[] { "dorm" }),
        ["l15canteen"] = (WorldLayout.Level15, new[] { "canteen", "serving-line" }),
        ["l15medical"] = (WorldLayout.Level15, new[] { "medical-bay" }),
        ["l15hydro"] = (WorldLayout.Level15, new[] { "hydroponics", "hydro-glass" }),
        ["l15camp"] = (WorldLayout.Level15, new[] { "camp" }),
        ["l15incinerator"] = (WorldLayout.Level15, new[] { "crematorium" }),
        ["l15dock"] = (WorldLayout.Level15, new[] { "dock" }),
        ["l15dark"] = (WorldLayout.Level15, new[] { "dark-hall" }),
        ["l15star"] = (WorldLayout.Level15, new[] { "star-door" }),
        ["l15sealed"] = (WorldLayout.Level15, new[] { "sealed-door" }),
        ["l15escape"] = (WorldLayout.Level15, new[] { "escape-panel", "gateway-shut" }),
        ["l15pane"] = (WorldLayout.Level15, new[] { "street-pane" }),
        ["l15stairs"] = (WorldLayout.Level15, new[] { "office-stairs" }),
        ["l15medcentre"] = (WorldLayout.Level14, new[] { "link-l15-medical" }),
        // ----- Level 23, the Petrified Garden -----
        ["l23forest"] = (WorldLayout.Level23, new[] { "forest-long", "boulder-undergrowth", "fallen-log", "stone-mushrooms" }),
        ["l23glade"] = (WorldLayout.Level23, new[] { "glade", "light-shaft" }),
        ["l23sentry"] = (WorldLayout.Level23, new[] { "sentry" }),
        ["l23heart"] = (WorldLayout.Level23, new[] { "heart-of-water", "heart-warning" }),
        ["l23well"] = (WorldLayout.Level23, new[] { "link-heart-well" }),
        ["l23glow"] = (WorldLayout.Level23, new[] { "glow-teal", "glow-violet", "glow-amber" }),
        ["l23tunnel"] = (WorldLayout.Level23, new[] { "seedling-tunnel", "seedling-waysign" }),
        ["l23seedling"] = (WorldLayout.Level23, new[] { "seedling-camp", "seedling-counter", "seedling-board", "seedling-sign" }),
        ["l23seedtree"] = (WorldLayout.Level23, new[] { "link-seedling-tree" }),
        ["l23trunk"] = (WorldLayout.Level23, new[] { "link-hollow-trunk" }),
        ["l23lighthouse"] = (WorldLayout.Level23, new[] { "ruin-lighthouse" }),
        ["l23sphere"] = (WorldLayout.Level23, new[] { "ruin-sphere" }),
        ["l23colosseum"] = (WorldLayout.Level23, new[] { "ruin-colosseum" }),
        ["l23parthenon"] = (WorldLayout.Level23, new[] { "ruin-parthenon" }),
        ["l23edge"] = (WorldLayout.Level23, new[] { "edge-tangle" }),
        // ----- Level 14, the Hospital -----
        ["l14hall"] = (WorldLayout.Level14, new[] { "hall-lit" }),
        ["l14darkhall"] = (WorldLayout.Level14, new[] { "hall-dark" }),
        ["l14reception"] = (WorldLayout.Level14, new[] { "reception" }),
        ["l14ward"] = (WorldLayout.Level14, new[] { "ward", "icu" }),
        ["l14maternity"] = (WorldLayout.Level14, new[] { "maternity" }),
        ["l14psych"] = (WorldLayout.Level14, new[] { "psych" }),
        ["l14surgery"] = (WorldLayout.Level14, new[] { "surgery" }),
        ["l14storage"] = (WorldLayout.Level14, new[] { "storage" }),
        ["l14office"] = (WorldLayout.Level14, new[] { "office" }),
        ["l14research"] = (WorldLayout.Level14, new[] { "research" }),
        ["l14torture"] = (WorldLayout.Level14, new[] { "torture" }),
        ["l14contam"] = (WorldLayout.Level14, new[] { "contaminated-door" }),
        ["l14futuredoor"] = (WorldLayout.Level14, new[] { "link-future" }),
        ["l14reddoor"] = (WorldLayout.Level14, new[] { "link-red" }),
        ["l14collapse"] = (WorldLayout.Level14, new[] { "link-collapse" }),
        // ----- Level 47, the Adderwood -----
        ["l47forest"] = (WorldLayout.Level47, new[] { "forest-long" }),
        ["l47trail"] = (WorldLayout.Level47, new[] { "trail" }),
        ["l47post"] = (WorldLayout.Level47, new[] { "waystone" }),
        ["l47stream"] = (WorldLayout.Level47, new[] { "stream" }),
        ["l47glade"] = (WorldLayout.Level47, new[] { "glade", "night-glade" }),
        ["l47manor"] = (WorldLayout.Level47, new[] { "great-hall", "entrance-hall", "east-room" }),
        ["l47stones"] = (WorldLayout.Level47, new[] { "stones-through-roof" }),
        ["l47hollow"] = (WorldLayout.Level47, new[] { "dead-hollow" }),
        ["l47giant"] = (WorldLayout.Level47, new[] { "green-giant" }),
        // ----- Their ways in, where they stand in other levels (each tour's links part) -----
        ["l0crack"] = (WorldLayout.Basement, new[] { "link-l0" }),
        ["l0emergency"] = (WorldLayout.Level14, new[] { "link-l0-exit" }),
        ["l1crack"] = (WorldLayout.Basement, new[] { "link-l1" }),
        ["l2crack"] = (WorldLayout.Basement, new[] { "link-l2" }),
        ["l2rinkdoor"] = (WorldLayout.Level31, new[] { "door-l2" }),
        ["l3rinkdoor"] = (WorldLayout.Level31, new[] { "door-l3" }),
        ["l3voltage"] = (WorldLayout.Level15, new[] { "l3-door" }),
        ["l4crack"] = (WorldLayout.Basement, new[] { "link-l4" }),
        ["l4serverroom"] = (WorldLayout.Level120, new[] { "serverroom-door" }),
        ["l5crack"] = (WorldLayout.Basement, new[] { "link-l5" }),
        ["l6rinkdoor"] = (WorldLayout.Level31, new[] { "door-l6" }),
        ["l6deepdark"] = (WorldLayout.Level73, new[] { "deepest-dark" }),
        ["l9gloom"] = (WorldLayout.Level73, new[] { "gloom" }),
        ["l9airport"] = (WorldLayout.Level36, new[] { "door-suburbs" }),
        ["l10whitewall"] = (WorldLayout.Level15, new[] { "wall10" }),
        ["l10deadtree"] = (WorldLayout.Level47, new[] { "way-in-level10" }),
        ["l11school"] = (WorldLayout.Level52, new[] { "way-in-school" }),
        ["l11airport"] = (WorldLayout.Level36, new[] { "door-city" }),
        ["l37greentree"] = (WorldLayout.Level23, new[] { "link-pool-tree", "link-pool-seedling-tree" }),
    };

    /// <summary>Each showcase tour asked for so far, by its level.</summary>
    private readonly Dictionary<int, List<Showcase.Spot>> tours = new();

    /// <summary>Whether a code is one of the showcase features.</summary>
    public static bool IsShowcaseFeature(string code) => ShowcaseFeatures.ContainsKey(code);

    /// <summary>
    /// The nearest spot of a showcase feature that stands in the level, within the radius: put down on its feet, facing as
    /// the tour does, the place reported a few blocks ahead of it. Null if there is none (Error says so for a code that is
    /// not one of these).
    /// </summary>
    private Hit ShowcaseFeature(string code, int gx, int gz, int radius, int level)
    {
        if (!ShowcaseFeatures.TryGetValue(code, out var feature))
        {
            Error = $"No finder for {code}";
            return null;
        }
        if (!tours.TryGetValue(feature.Tour, out List<Showcase.Spot> tour))
            tours[feature.Tour] = tour = Showcase.For(feature.Tour, layout, geometry).ToList();
        Showcase.Spot? best = null;
        long bestSq = (long)radius * radius;
        foreach (Showcase.Spot spot in tour)
        {
            if (Array.IndexOf(feature.Spots, spot.Name) < 0) continue;
            int sx = (int)Math.Floor(spot.X), sz = (int)Math.Floor(spot.Z);
            if (layout.LevelAt(WorldLayout.MacroOf(sx), WorldLayout.MacroOf(sz)) != level) continue;
            long d = Sq(sx - gx, sz - gz);
            if (d > bestSq) continue;
            bestSq = d;
            best = spot;
        }
        if (best is not { } s) return null;
        double h = s.Heading * Math.PI / 180;
        int x = (int)Math.Floor(s.X), z = (int)Math.Floor(s.Z);
        return new Hit
        {
            X = (int)Math.Floor(s.X + Math.Sin(h) * 4), Z = (int)Math.Floor(s.Z - Math.Cos(h) * 4),
            Stand = (x, z), FeetY = s.Y, Detail = $" (heading {(int)Math.Round(s.Heading) % 360} looks at it)",
        };
    }
}
