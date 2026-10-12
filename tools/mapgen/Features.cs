using Backrooms.Worldgen;
static class Features
{
    public static void Run(WorldLayout layout, int m0x, int m0z, int n)
    {
        var found = new Dictionary<string, (int, int)>();
        void Note(string name, int x, int z) { if (!found.ContainsKey(name)) found[name] = (x, z); }
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                var cell = layout.BuildMacro(m0x + mx, m0z + mz);
                for (int i = 0; i < 1024; i++)
                {
                    var t = cell[i]; int x = (m0x + mx) * 32 + i % 32, z = (m0z + mz) * 32 + i / 32;
                    if (i % 32 == 0 || i / 32 == 0) continue;
                    if (t.Level == 1 && t.Kind == TileKind.Doorway && t.Variant == Props.FireDoor && t.Floor == FloorKind.L1Hall) Note("L1 core firedoor", x, z);
                    if (t.Level == 1 && t.Kind == TileKind.Doorway && t.Variant == Props.FireDoor && t.Floor != FloorKind.L1Hall) Note("L1 edge firedoor", x, z);
                    if (t.Level == 1 && t.Kind == TileKind.Wall && t.Variant == Decor.PowerBox) Note("L1 powerbox", x, z);
                    if (t.Level == 1 && t.Overhead == Overheads.ExitSignWE) Note("L1 hanging exit", x, z);
                    if (t.Level == 1 && (t.Variant == Props.Tent || t.Variant == Props.CampTent && t.Stack == 0)) Note("L1 tent", x, z);
                    if (t.Level == 1 && t.Variant == Props.HospitalBed) Note("L1 hospital bed", x, z);
                    if (t.Level == 3 && t.Kind == TileKind.Floor && t.Variant == Props.AngelStatue) Note("L3 statue", x, z);
                    if (t.Level == 3 && t.Kind == TileKind.Floor && t.Variant == Props.Coil) Note("L3 coil", x, z);
                    if (t.Level == 3 && t.Kind == TileKind.Wall && t.Variant >= Decor.RoomSign && t.Variant < Decor.RoomSign + 8) Note("L3 room sign", x, z);
                    if (t.Level == 3 && t.Variant == Props.Conveyor) Note("L3 conveyor", x, z);
                    if (t.Level == 4 && t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator) Note("L4 elevator", x, z);
                    if (t.Level == 4 && t.Kind == TileKind.Wall && t.Variant == Decor.Fountain) Note("L4 fountain", x, z);
                    if (t.Level == 4 && t.Variant == Props.ServerRack) Note("L4 server rack", x, z);
                    if (t.Level == 4 && t.Kind == TileKind.Wall && t.Pattern == WallPattern.OfficeWindow) Note("L4 window", x, z);
                    if (t.Level == 5 && t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator && t.Variant == 0) Note("L5 cage elevator", x, z);
                    if (t.Level == 5 && t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator && t.Variant == 1) Note("L5 modern elevator", x, z);
                    if (t.Level == 5 && t.Variant == Props.ConsoleTable) Note("L5 console table", x, z);
                    if (t.Level == 5 && t.Variant == Props.DiningTable) Note("L5 dining table", x, z);
                    if (t.Level == 5 && t.Variant == Props.MahjongTable) Note("L5 mahjong", x, z);
                    if (t.Level == 5 && t.Variant == Props.FrontDesk) Note("L5 front desk", x, z);
                }
            }
        foreach (var kv in found) Console.WriteLine($"{kv.Key}: {kv.Value.Item1} {kv.Value.Item2}");
    }
}
