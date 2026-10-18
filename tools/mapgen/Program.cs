using Backrooms.Worldgen;
long seed = args.Length > 0 ? long.Parse(args[0]) : 12345;
int n = args.Length > 1 ? int.Parse(args[1]) : 14;
// SPAWN=<cells> sets the spawn macro cell (half the map's size in cells; 16000 is a full-size world)
int smx = int.TryParse(Environment.GetEnvironmentVariable("SPAWN"), out int spawnCells) ? spawnCells : 16000, smz = smx;
// LAYOUT_VERSION=<n> builds the layout of a world made with that layout version (default: the current one)
int layoutVersion = int.TryParse(Environment.GetEnvironmentVariable("LAYOUT_VERSION"), out int lvSet) ? lvSet : WorldLayout.CurrentVersion;
// FOOD_SCALE=<x> lays out a world with that Backrooms scarcity (0.6 Sparse, 0.33 Scarce; default 1, Normal)
double foodScale = double.TryParse(Environment.GetEnvironmentVariable("FOOD_SCALE"), System.Globalization.CultureInfo.InvariantCulture, out double fs) ? fs : 1;
var layout = new WorldLayout(seed, smx, smz, layoutVersion, foodScale);
int m0x = smx - n / 2, m0z = smz - n / 2, size = n * 32;
if (args.Length > 4 && args[2] == "at") { m0x = int.Parse(args[3]) - n / 2; m0z = int.Parse(args[4]) - n / 2; }
// AT=<mx>,<mz> centres any mode's area on that cell (AT=L<level> on that level's first arrival, AT=S on a food court)
if (Environment.GetEnvironmentVariable("AT") is string at && at.Length > 0)
{
  if (at == "S" && layout.FindSnackroomsArrival(99991UL) is { } s0) { m0x = WorldLayout.MacroOf(s0.X) - n / 2; m0z = WorldLayout.MacroOf(s0.Z) - n / 2; }
  else if (at[0] == 'L' && layout.FindArrival(int.Parse(at[1..]), 99991UL) is { } a0) { m0x = WorldLayout.MacroOf(a0.X) - n / 2; m0z = WorldLayout.MacroOf(a0.Z) - n / 2; }
  else if (at.Split(',') is { Length: 2 } xz) { m0x = int.Parse(xz[0]) - n / 2; m0z = int.Parse(xz[1]) - n / 2; }
}
if (args.Length > 3 && args[2] == "region") {
  // Centre the render in the middle of a level, straight out from spawn at a given angle (degrees)
  int want = int.Parse(args[3]); double ang = (args.Length > 4 ? double.Parse(args[4]) : 0) * Math.PI / 180;
  double rIn = -1, rOut = -1;
  for (double r = 1; r < 900; r += 0.5) { int lv = layout.LevelAt(smx + (int)Math.Round(Math.Cos(ang) * r), smz + (int)Math.Round(Math.Sin(ang) * r));
    if (lv == want && rIn < 0) rIn = r; if (lv > want) { rOut = r; break; } }
  double rm = rOut < 0 ? rIn + 20 : (rIn + rOut) / 2;
  int cx = smx + (int)Math.Round(Math.Cos(ang) * rm), cz = smz + (int)Math.Round(Math.Sin(ang) * rm);
  m0x = cx - n / 2; m0z = cz - n / 2;
  Console.WriteLine($"region of level {want}: centre macro {cx},{cz} (blocks {cx*32},{cz*32}), ring {rIn:0}-{rOut:0}");
}

// L0HALL=1: also write hall.bin (Level 0 hallway tiles, one byte per tile) for hallview.py
if (Environment.GetEnvironmentVariable("L0HALL") == "1") { var hb = new byte[size * size]; for (int z = 0; z < size; z++) for (int x = 0; x < size; x++) hb[z * size + x] = layout.LevelAt(WorldLayout.MacroOf(m0x * 32 + x), WorldLayout.MacroOf(m0z * 32 + z)) == 0 ? layout.Level0HallAt(m0x * 32 + x, m0z * 32 + z) : (byte)0; File.WriteAllBytes("hall.bin", hb); }
if (args.Length > 2 && args[2] == "notes") { NotesSim.Run(args, layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "timing") { Timing.Run(layout, m0x, m0z, n); return; }
if (args.Length > 3 && args[2] == "plan") { Debugger.Plan(layout, m0x * 32 + int.Parse(args[3]), m0z * 32 + int.Parse(args[4])); return; }
if (args.Length > 2 && args[2] == "probe") { Probe.Run(layout, m0x, m0z, args); return; }
if (args.Length > 2 && args[2] == "doors") { DoorCheck.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "stats") { Stats.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "edgedoors") { EdgeDoors.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "edgecross") { EdgeCross.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "stats2") { Stats2.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "boxes") { Boxes.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "boiler") { Boiler.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "cubes") { Cubes.Run(layout, m0x, m0z, n); return; }
if (args.Length > 3 && args[2] == "stairs") { StairCheck.RunLevel(layout, int.Parse(args[3]), n, args.Length > 4 ? int.Parse(args[4]) : 4); return; }
if (args.Length > 2 && args[2] == "stairs") { StairCheck.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "posts") { Posts.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "overview") { Overview.Run(layout, smx, smz, int.Parse(args[1]), "overview.bin", args.Length > 3 ? int.Parse(args[3]) : 1); return; }
if (args.Length > 2 && args[2] == "citymap") { CityMap.Run(layout, n, args.Length > 3 ? int.Parse(args[3]) : 0, args.Length > 4 ? int.Parse(args[4]) : 0); return; }
if (args.Length > 2 && args[2] == "noclip") { NoclipFind.Run(layout, smx, smz); return; }
if (args.Length > 2 && args[2] == "links") { Links.Run(layout, seed, smx, smz); return; }
if (args.Length > 3 && args[2] == "validatelevel") { int lv = int.Parse(args[3]); for (ulong k = 1; k <= (args.Length > 4 ? ulong.Parse(args[4]) : 2UL); k++) { var a = layout.FindArrival(lv, k * 99991UL); if (a == null) { Console.WriteLine("no arrival"); continue; }
  int cx = WorldLayout.MacroOf(a.Value.X) - n / 2, cz = WorldLayout.MacroOf(a.Value.Z) - n / 2; Console.WriteLine($"--- level {lv} around {a.Value}"); Validator.Run(layout, cx, cz, n, a.Value.X - cx * 32, a.Value.Z - cz * 32); } return; }
// l3runs: Level 3's wall pipes, cable runs, floor cables, gauges and switchgear as the player sees them; l3dump x z r for render_l3runs.py
if (args.Length > 2 && args[2] == "l3runs") { L3Runs.Run(layout, m0x, m0z, n); return; }
if (args.Length > 4 && args[2] == "l3dump") { L3Runs.Dump(layout, int.Parse(args[3]), int.Parse(args[4]), args.Length > 5 ? int.Parse(args[5]) : 24); return; }
if (args.Length > 2 && args[2] == "conduitmap") { ConduitMap.Run(layout, args.Length > 3 ? int.Parse(args[3]) : 30); return; }
if (args.Length > 4 && args[2] == "peek") { Peek.Run(layout, int.Parse(args[3]), int.Parse(args[4]), args.Length > 5 ? int.Parse(args[5]) : 8); return; }
if (args.Length > 2 && args[2] == "l6density") { Density.Run(layout, smx, smz); return; }
if (args.Length > 6 && args[2] == "path") { PathCheck.Run(layout, n, int.Parse(args[3]), int.Parse(args[4]), int.Parse(args[5]), int.Parse(args[6])); return; }
if (args.Length > 4 && args[2] == "l0") { for (int i = 3; i + 1 < args.Length; i += 2) Console.WriteLine(layout.DescribeLevel0(int.Parse(args[i]), int.Parse(args[i + 1]))); return; }
if (args.Length > 4 && args[2] == "reach") { Reach.Run(layout, smx, smz, n, int.Parse(args[3]), double.Parse(args[4]), args.Length > 5 ? int.Parse(args[5]) : -1); return; }
if (args.Length > 2 && args[2] == "cavetest") { CaveTest.Run(); return; }
if (args.Length > 2 && args[2] == "ore") { CaveTest.OreRun(); return; }
if (args.Length > 2 && args[2] == "wander") { Wander.Run(layout, smx, smz); return; }
if (args.Length > 2 && args[2] == "bands") { Bands.Run(layout, smx, smz, args); return; }
if (args.Length > 2 && args[2] == "loot") { Loot.Run(layout, smx, smz, n, args.Length > 3 ? int.Parse(args[3]) : 3); return; }
if (args.Length > 2 && args[2] == "chalk") { ChalkStats.Run(layout, smx, smz, n); return; }
if (args.Length > 2 && args[2] == "dens") { DenStats.Run(layout, smx, smz, n); return; }
if (args.Length > 2 && args[2] == "parts") { PartsStats.Run(layout, m0x + n / 2, m0z + n / 2, n / 2); return; }
if (args.Length > 2 && args[2] == "gates") { Gates.Run(layout, smx, smz, n); return; }
if (args.Length > 2 && args[2] == "lorespots") { LoreSpots.Run(layout, smx, smz); return; }
if (args.Length > 2 && args[2] == "l9houses") { L9Houses.Run(layout, n); return; }
if (args.Length > 2 && args[2] == "archspots") { ArchSpots.Run(layout, smx, smz, args.Length > 3 ? int.Parse(args[3]) : 30); return; }
if (args.Length > 2 && args[2] == "unreach") { Unreach.Run(layout, n); return; }
if (args.Length > 2 && args[2] == "city") { City.Run(layout, smx, smz, n); return; }
if (args.Length > 4 && args[2] == "hpeek") { HeightPeek.Run(layout, int.Parse(args[3]), int.Parse(args[4]), args.Length > 5 ? int.Parse(args[5]) : 8); return; }
if (args.Length > 2 && args[2] == "findres") { FindReservoir.Run(layout); return; }
if (args.Length > 2 && args[2] == "layouthash") { LayoutHash.Run(args); return; }
// shotgrid and feet: camera planning for the graphics pass's spot lists (ShotGrid.cs)
if (args.Length > 2 && ShotGrid.Run(layout, args)) return;
// Each of the levels kept as 14-20 has its own modes (runstats, funstats, endstats, hubstats, 974stats, 3999stats, 188stats), in its own file
if (args.Length > 2 && LevelModes.Run(layout, args)) return;
if (args.Length > 2 && args[2] == "regions") { Regions.Run(layout, smx, smz); return; }
if (args.Length > 3 && args[2] == "regionmap") { Regions.Map(layout, WorldLayout.FromDisplayName(args[3]), n, args.Length > 4 ? int.Parse(args[4]) : 0, args.Length > 5 ? int.Parse(args[5]) : 0); return; }
if (args.Length > 2 && args[2] == "poolstats") { Regions.PoolStats(layout, args.Length > 3 ? int.Parse(args[3]) : 4); return; }
if (args.Length > 2 && args[2] == "motionstats") { Regions.MotionStats(layout, n); return; }
if (args.Length > 2 && args[2] == "deep") { Deep.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "features") { Features.Run(layout, m0x, m0z, n); return; }
if (args.Length > 2 && args[2] == "validate") { var (vx, vz) = layout.FindSpawn(); Validator.Run(layout, m0x, m0z, n, vx - m0x * 32, vz - m0z * 32); return; }
if (args.Length > 2 && args[2] == "spots") { Spots.Run(layout); return; }
if (args.Length > 2 && args[2] == "probe2") { Probe2.Run(layout, smx, smz); return; }
if (args.Length > 4 && args[2] == "farm") { FindFarm.Run(layout, int.Parse(args[3]), int.Parse(args[4]), 20); return; }
if (args.Length > 2 && args[2] != "region" && args[2] != "at") { Finder.Run(layout); return; }
var sw = System.Diagnostics.Stopwatch.StartNew();
using var w = new BinaryWriter(File.Create("tiles.bin"));
w.Write(size);
for (int mz = 0; mz < n; mz++) for (int mx = 0; mx < n; mx++) {
  var tiles = layout.BuildMacro(m0x + mx, m0z + mz);
  foreach (var t in tiles) { w.Write((byte)t.Kind); w.Write((byte)t.Floor); w.Write((byte)t.Ceiling); w.Write((byte)((t.SupplyBox ? 1 : 0) | (t.Stack > 0 ? 2 : 0) | (t.Pipe > 0 ? 4 : 0) | (t.ExitSign ? 8 : 0) | (t.Worn ? 16 : 0) | (t.Under > 0 ? 32 : 0) | (t.Grand ? 64 : 0))); w.Write(t.Level); w.Write((byte)t.Pattern); w.Write((byte)Math.Min((int)t.Variant, 255)); }
}
var (sx, sz) = layout.FindSpawn();
w.Write(sx - m0x * 32); w.Write(sz - m0z * 32);
Console.WriteLine($"{n*n} macros in {sw.ElapsedMilliseconds} ms");
