using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Prop = Backrooms.Worldgen.Props;
using Zone = Backrooms.Worldgen.WorldLayout.L14Zone;

namespace Backrooms.Regions;

/// <summary>
/// Level 14, "The Hospital": the rules (docs/design/experimental-levels/14-plan.md; Fandom's Level 14). Every rule watches
/// the players in the level (and, for headless tests, the straw dummies) five times a second; nothing of it is saved.
/// <list type="bullet">
/// <item><b>Contaminated rooms</b> ("filled with toxic, radioactive substances, causing hallucinations, disorientation, fear,
/// and even memory loss"). Stepping in, a line; after <see cref="ContamGraceMs"/> inside, <see cref="ContamDamage"/> every
/// <see cref="ContamEveryMs"/> (poison) with a line now and then, and the room wears at your hold on reality
/// (<see cref="ContamDrain"/> of your stability each time, never below <see cref="ContamStabilityFloor"/>), so the game's
/// own distortion and whispers come on; the client makes the air swim and whisper (AtmosphereSystem.L14.cs). A hazmat suit
/// keeps most of the hurt off and its hood most of the drain (Wear/HazmatSystem.cs).</item>
/// <item><b>Equipment springing to life</b> ("In rare cases, the old, rusty hospital equipment ... may suddenly spring to
/// life ... flying scalpels, stethoscopes, and syringes"). Passing within 2 blocks of an instrument trolley, a crash cart, a
/// monitor, a ventilator or an anaesthesia machine, one time in <see cref="EquipChanceIn"/> it sparks or flings something:
/// sound, sparks or flying steel, 1 to 3 damage, a line; at most once every <see cref="EquipCooldownMs"/> for each player
/// (a few times an hour in the wards).</item>
/// <item><b>Cracked floor</b> ("pay attention to the ground. If there are any signs of instability, the best thing to do
/// would be to run"): stepping onto a cracked tile (the level's own, and the cracks round the floor that gives way), it
/// creaks now and then, with a line at most once a minute.</item>
/// <item><b>Reception rooms</b> ("These compartments may never be entered again once left"). Whoever has left a reception
/// room (stood outside it more than <see cref="LeftReach"/> blocks from its doors) and walks back into it is put back out
/// through the door with a latch and a line. Someone carried in (an arrival, a door from elsewhere) is never stopped:
/// that room is theirs again until they leave it.</item>
/// </list>
/// Test command: <c>/backrooms l14 contam|equipment|crack|reception|state [go|test]</c>.
/// </summary>
public class L14System : ModSystem
{
    private const long TickMs = 200;

    /// <summary>Contaminated rooms: the grace before the first hurt, how often, how much; the stability lost each time and the floor it stops at.</summary>
    public const long ContamGraceMs = 8000, ContamEveryMs = 4000, ContamSickLineMs = 30000, ContamEnterLineMs = 20000;
    public const float ContamDamage = 0.5f;
    public const double ContamDrain = 0.03, ContamStabilityFloor = 0.2;

    /// <summary>Equipment: one pass in this many sets it off; then not again for this long; within this reach (blocks).</summary>
    public const int EquipChanceIn = 30;
    public const long EquipCooldownMs = 6 * 60_000;
    public const double EquipReach = 2.0;

    /// <summary>Cracks: how often the floor may creak under one person, and the line.</summary>
    public const long CreakEveryMs = 3000, CrackLineMs = 60_000;
    public const double CreakChance = 0.55;

    /// <summary>Reception rooms: how far from the doors counts as having left (blocks); how often the line may show.</summary>
    public const double LeftReach = 4.0;
    public const long ShutLineMs = 4000;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private long tick;
    private readonly Random rand = new();

    private sealed class Track
    {
        public bool HasLast;
        public double LastX, LastZ;
        public int TileX = int.MinValue, TileZ = int.MinValue;
        public long ContamSinceMs = -1, ContamNextHitMs, ContamNextSickMs, ContamNextEnterMs, ContamHits;
        public long NextEquipMs;
        public HashSet<long> NearEquip = new();
        public long NextCreakMs, NextCrackLineMs;
        public int Creaks;
        /// <summary>The reception room they are in (its id), the rooms they have left, and where they last stood outside one.</summary>
        public Room Inside;
        public readonly HashSet<long> Left = new();
        public long NextShutMs;
        public int Shut;
    }

    private sealed class Room
    {
        public long Id;
        public readonly List<(int X, int Z, ArchPier Out)> Doors = new();
        public int Tiles;
    }

    private readonly Dictionary<long, Track> tracks = new();
    private readonly Dictionary<long, Room> roomOf = new();

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.3;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            tick = api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] Level 14: {0}", e), (int)TickMs, 1000);
            api.Event.PlayerDisconnect += OnPlayerDisconnect;
        });

        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l14")
                .WithDescription("Level 14 (testing): 'contam' says where you (or from the console the latest straw dummy) stand and the nearest contaminated room ('contam go' puts you in it); 'equipment' sets off the nearest equipment within 6 blocks ('equipment go' takes you beside the nearest); 'crack' finds the nearest cracked floor ('crack go'); 'reception' the nearest reception room ('reception test' walks a straw dummy out of it and back, which must be turned away); 'state' what the rules know of you")
                .WithArgs(api.ChatCommands.Parsers.Word("what"), api.ChatCommands.Parsers.OptionalWord("more"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnCommand)
            .EndSubCommand();
    }

    public override void Dispose()
    {
        if (sapi == null || layout == null) return;
        if (tick != 0) sapi.Event.UnregisterGameTickListener(tick);
        sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
    }

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        if (player.Entity != null) tracks.Remove(player.Entity.EntityId);
    }

    private bool InLevel(double x, double z) => layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(x)), WorldLayout.MacroOf((int)Math.Floor(z))) == WorldLayout.Level14;

    private static string Text(IServerPlayer player, string key, params object[] args) => Say.T(player, "backrooms:" + key, args);

    private static void Tell(Entity who, string code, string key)
    {
        if ((who as EntityPlayer)?.Player is IServerPlayer player) player.SendIngameError("backrooms-l14-" + code, Text(player, key));
    }

    private static long Key(int x, int z) => ((long)x << 32) | (uint)z;

    private static bool Hurts(Entity who) => who is not EntityPlayer p || p.Player?.WorldData.CurrentGameMode == EnumGameMode.Survival;

    // ================= The tick =================

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        var seen = new HashSet<long>();
        foreach (Entity who in Subjects())
        {
            seen.Add(who.EntityId);
            if (!tracks.TryGetValue(who.EntityId, out Track track)) tracks[who.EntityId] = track = new Track();
            double x = who.Pos.X, z = who.Pos.Z;
            if (!InLevel(x, z))
            {
                track.ContamSinceMs = -1;
                track.Inside = null;
                track.NearEquip.Clear();
                track.HasLast = false;
                continue;
            }
            int bx = (int)Math.Floor(x), bz = (int)Math.Floor(z);
            Tile t = layout.TileAt(bx, bz);
            double step = track.HasLast ? Math.Sqrt((x - track.LastX) * (x - track.LastX) + (z - track.LastZ) * (z - track.LastZ)) : double.MaxValue;
            bool carried = step > 4;
            bool newTile = bx != track.TileX || bz != track.TileZ;
            if (!Reception(who, track, t, bx, bz, carried, now))
            {
                Contaminated(who, track, t, now);
                Cracks(who, track, t, newTile, now);
                Equipment(who, track, bx, bz, now);
            }
            track.TileX = (int)Math.Floor(who.Pos.X);
            track.TileZ = (int)Math.Floor(who.Pos.Z);
            track.LastX = who.Pos.X;
            track.LastZ = who.Pos.Z;
            track.HasLast = true;
        }
        if (tracks.Count > seen.Count) foreach (long id in tracks.Keys.Where(id => !seen.Contains(id)).ToList()) tracks.Remove(id);
    }

    /// <summary>The players in the world (playing, alive, not spectating) and, for headless tests, the straw dummies.</summary>
    private IEnumerable<Entity> Subjects()
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
            if (online is IServerPlayer player && player.Entity is { Alive: true } entity && player.ConnectionState == EnumClientState.Playing
                && player.WorldData.CurrentGameMode != EnumGameMode.Spectator) yield return entity;
        foreach (Entity e in Dummies())
            if (e.Alive) yield return e;
    }

    private long dummyScanAt = long.MinValue;
    private Entity[] dummyCache = Array.Empty<Entity>();

    /// <summary>
    /// The console tests' straw dummies. With real players online the scan of every loaded entity runs at most every 5 s
    /// (a dummy put down for a test is found within that); with none, each call looks afresh.
    /// </summary>
    private Entity[] Dummies()
    {
        long now = sapi.World.ElapsedMilliseconds;
        bool anyone = false;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers) { anyone = true; break; }
        if (anyone && now >= dummyScanAt && now - dummyScanAt < 5000) return dummyCache;
        dummyScanAt = now;
        var found = new List<Entity>();
        foreach (Entity e in sapi.World.LoadedEntities.Values)
            if (e.Alive && Senses.IsTestTarget(e)) found.Add(e);
        return dummyCache = found.ToArray();
    }

    // ================= Contaminated rooms =================

    private static bool IsContam(Tile t) => t.Level == WorldLayout.Level14 && t.Kind is TileKind.Floor or TileKind.Doorway
        && WorldLayout.L14IsContam(t) && WorldLayout.L14IsRoom(WorldLayout.L14ZoneOf(t));

    private void Contaminated(Entity who, Track track, Tile t, long now)
    {
        if (!IsContam(t))
        {
            track.ContamSinceMs = -1;
            return;
        }
        if (track.ContamSinceMs < 0)
        {
            track.ContamSinceMs = now;
            track.ContamNextHitMs = now + ContamGraceMs;
            if (now >= track.ContamNextEnterMs)
            {
                track.ContamNextEnterMs = now + ContamEnterLineMs;
                Tell(who, "contam", "l14-contam-enter");
            }
            return;
        }
        if (now < track.ContamNextHitMs) return;
        track.ContamNextHitMs = now + ContamEveryMs;
        track.ContamHits++;
        if (Hurts(who))
        {
            // A hazmat suit keeps most of it off the skin, its hood most of the air out; each wears a little (Wear/HazmatSystem.cs)
            float skin = Backrooms.Wear.HazmatSystem.Through(who, "suit", Backrooms.Wear.HazmatSystem.SuitBlocks);
            float air = Backrooms.Wear.HazmatSystem.Through(who, "hood", Backrooms.Wear.HazmatSystem.HoodBlocks);
            who.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Internal, Type = EnumDamageType.Poison }, ContamDamage * skin);
            // It wears at your hold on reality: the game's distortion and whispers come on as it falls
            double s = Senses.Stability(who);
            if (s > ContamStabilityFloor) who.WatchedAttributes.SetDouble("temporalStability", Math.Max(ContamStabilityFloor, s - ContamDrain * air));
        }
        if (now >= track.ContamNextSickMs)
        {
            track.ContamNextSickMs = now + ContamSickLineMs;
            Tell(who, "contam", "l14-contam-sick");
        }
    }

    // ================= Equipment =================

    /// <summary>What can spring to life: the instrument trolley, a crash cart, a monitor, a ventilator, an anaesthesia machine.</summary>
    private static bool IsEquipment(ushort variant) => variant is Prop.L14Trolley or Prop.RunCrashCart or Prop.L14Monitor or Prop.L14Ventilator or Prop.L14Anaesthesia;

    private void Equipment(Entity who, Track track, int bx, int bz, long now)
    {
        var near = new HashSet<long>();
        (int X, int Z, ushort What)? fresh = null;
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
            {
                int x = bx + dx, z = bz + dz;
                Tile t = layout.TileAt(x, z);
                if (t.Level != WorldLayout.Level14 || t.Kind != TileKind.Floor || !IsEquipment(t.Variant)) continue;
                double ex = x + 0.5 - who.Pos.X, ez = z + 0.5 - who.Pos.Z;
                if (ex * ex + ez * ez > (EquipReach + 0.5) * (EquipReach + 0.5)) continue;
                near.Add(Key(x, z));
                if (!track.NearEquip.Contains(Key(x, z)) && fresh == null) fresh = (x, z, t.Variant);
            }
        track.NearEquip = near;
        if (fresh is not { } f || now < track.NextEquipMs || !Hurts(who) || rand.Next(EquipChanceIn) != 0) return;
        if (SpringToLife(who, f.X, f.Z, f.What)) track.NextEquipMs = now + EquipCooldownMs;
    }

    /// <summary>A piece of equipment at a floor tile comes to life at someone: sparks or flying steel, a hurt, a line. False if it is not there (taken away).</summary>
    private bool SpringToLife(Entity who, int x, int z, ushort what)
    {
        int floor = geometry.FloorFor(WorldLayout.Level14);
        var at = new BlockPos(x, floor + 1, z);
        if (sapi.World.BlockAccessor.GetBlock(at).Id == 0) return false;
        var from = new Vec3d(x + 0.5, floor + 1.8, z + 0.5);
        bool electric = what is Prop.L14Monitor or Prop.L14Ventilator or Prop.L14Anaesthesia;
        int line = what switch
        {
            Prop.L14Monitor => 2,
            Prop.L14Ventilator or Prop.L14Anaesthesia => 4,
            Prop.RunCrashCart => rand.Next(2) == 0 ? 1 : 3,
            _ => new[] { 0, 1, 3 }[rand.Next(3)],
        };
        sapi.World.PlaySoundAt(new AssetLocation(electric ? "backrooms:sounds/ambient/14/spark" : "backrooms:sounds/ambient/14/clatter"), from.X, from.Y, from.Z, null, true, 24, 1f);
        Vec3d eyes = Senses.Eyes(who);
        Vec3d dir = (eyes - from).Normalize();
        if (electric)
        {
            var sparks = new SimpleParticleProperties(18, 28, ColorUtil.ToRgba(255, 255, 220, 120), from.AddCopy(-0.2, -0.2, -0.2), from.AddCopy(0.2, 0.2, 0.2),
                new Vec3f(-3f, 0.5f, -3f), new Vec3f(3f, 4f, 3f), 0.5f, 1f, 0.05f, 0.12f, EnumParticleModel.Cube)
            {
                VertexFlags = 255,
                WithTerrainCollision = true,
                WindAffected = false,
            };
            sapi.World.SpawnParticles(sparks);
        }
        // Flying steel: a few glints from it straight at them
        var steel = new SimpleParticleProperties(3, 6, ColorUtil.ToRgba(255, 200, 205, 210), from.AddCopy(-0.1, -0.1, -0.1), from.AddCopy(0.1, 0.1, 0.1),
            new Vec3f((float)dir.X * 12f, (float)dir.Y * 12f, (float)dir.Z * 12f), new Vec3f((float)dir.X * 16f, (float)dir.Y * 16f + 0.5f, (float)dir.Z * 16f),
            0.35f, 0.2f, 0.12f, 0.2f, EnumParticleModel.Cube)
        {
            VertexFlags = 64,
            WithTerrainCollision = true,
            WindAffected = false,
        };
        sapi.World.SpawnParticles(steel);
        double roll = rand.NextDouble();
        float damage = roll < 0.5 ? 1f : roll < 0.85 ? 2f : 3f;
        EnumDamageType type = electric ? EnumDamageType.Injury : line == 3 ? EnumDamageType.BluntAttack : EnumDamageType.PiercingAttack;
        who.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Block, SourcePos = from, Type = type }, damage);
        Tell(who, "equipment", "l14-equipment-" + line);
        sapi.ModLoader.GetModSystem<MenaceSystem>()?.RaiseNoise(from, MenaceSystem.ImpactLoudness, "l14-equipment", who);
        return true;
    }

    // ================= Cracked floor =================

    private static bool IsCracked(Tile t) => t.Level == WorldLayout.Level14 && t.Kind is TileKind.Floor or TileKind.Doorway
        && (t.Under == Unders.L14Cracks || t.Depth is WorldLayout.L14FCracked or WorldLayout.L14FSagging);

    private void Cracks(Entity who, Track track, Tile t, bool newTile, long now)
    {
        if (!newTile || !IsCracked(t) || now < track.NextCreakMs || rand.NextDouble() >= CreakChance) return;
        track.NextCreakMs = now + CreakEveryMs;
        track.Creaks++;
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/14/creak"), who.Pos.X, who.Pos.Y, who.Pos.Z, null, true, 16, 0.9f);
        if (now < track.NextCrackLineMs) return;
        track.NextCrackLineMs = now + CrackLineMs;
        Tell(who, "crack", "l14-crack-warn");
    }

    // ================= Reception rooms =================

    private static bool IsReceptionTile(Tile t) => t.Level == WorldLayout.Level14 && t.Kind is TileKind.Floor or TileKind.Doorway
        && WorldLayout.L14ZoneOf(t) == Zone.Reception;

    /// <summary>The reception room a block lies in (its floor or its doorways), found once by filling it; null outside one.</summary>
    private Room ReceptionAt(int x, int z)
    {
        if (roomOf.TryGetValue(Key(x, z), out Room known)) return known;
        if (!IsReceptionTile(layout.TileAt(x, z))) return null;
        if (roomOf.Count > 50_000) roomOf.Clear();
        var room = new Room();
        var open = new Queue<(int X, int Z)>();
        var seen = new HashSet<long> { Key(x, z) };
        open.Enqueue((x, z));
        (int X, int Z) least = (x, z);
        while (open.Count > 0 && room.Tiles < 4000)
        {
            var (cx, cz) = open.Dequeue();
            Tile t = layout.TileAt(cx, cz);
            room.Tiles++;
            roomOf[Key(cx, cz)] = room;
            if (cz < least.Z || cz == least.Z && cx < least.X) least = (cx, cz);
            if (t.Kind == TileKind.Doorway) room.Doors.Add((cx, cz, t.Pier));
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = cx + dx, nz = cz + dz;
                if (seen.Add(Key(nx, nz)) && IsReceptionTile(layout.TileAt(nx, nz))) open.Enqueue((nx, nz));
            }
        }
        room.Id = Key(least.X, least.Z);
        return room;
    }

    private static (int Dx, int Dz) Outward(ArchPier side) => side switch
    {
        ArchPier.West => (-1, 0),
        ArchPier.East => (1, 0),
        ArchPier.North => (0, -1),
        _ => (0, 1),
    };

    /// <summary>The reception rooms' one rule. True if it put someone back out (the other rules wait for the next tick).</summary>
    private bool Reception(Entity who, Track track, Tile t, int bx, int bz, bool carried, long now)
    {
        Room room = IsReceptionTile(t) ? ReceptionAt(bx, bz) : null;
        if (room != null)
        {
            if (track.Left.Contains(room.Id))
            {
                // Carried in (an arrival, a way from elsewhere): theirs again. Walked in: turned away.
                if (carried)
                {
                    track.Left.Remove(room.Id);
                    track.Inside = room;
                    return false;
                }
                return PutOut(who, track, room, now);
            }
            track.Inside = room;
            return false;
        }
        if (track.Inside is not { } was) return false;
        // Out of it: far enough from its doors, they have left it
        if (was.Doors.Count == 0) { track.Inside = null; return false; }
        double nearest = was.Doors.Min(d => Math.Sqrt((d.X + 0.5 - who.Pos.X) * (d.X + 0.5 - who.Pos.X) + (d.Z + 0.5 - who.Pos.Z) * (d.Z + 0.5 - who.Pos.Z)));
        if (nearest > LeftReach)
        {
            track.Left.Add(was.Id);
            track.Inside = null;
        }
        return false;
    }

    /// <summary>Back out through the nearest of the room's doors, two blocks beyond it, with the latch and the line.</summary>
    private bool PutOut(Entity who, Track track, Room room, long now)
    {
        if (room.Doors.Count == 0) return false;
        var door = room.Doors.OrderBy(d => (d.X + 0.5 - who.Pos.X) * (d.X + 0.5 - who.Pos.X) + (d.Z + 0.5 - who.Pos.Z) * (d.Z + 0.5 - who.Pos.Z)).First();
        var (ox, oz) = Outward(door.Out);
        double x = door.X + 0.5 + ox * 1.6, z = door.Z + 0.5 + oz * 1.6;
        Tile beyond = layout.TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        if (beyond.Kind != TileKind.Floor || IsReceptionTile(beyond))
        {
            // (Nowhere open there: back where they stood a moment ago)
            if (!track.HasLast) return false;
            x = track.LastX;
            z = track.LastZ;
        }
        who.TeleportToDouble(x, who.Pos.Y, z);
        track.Shut++;
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/14/latch"), door.X + 0.5, who.Pos.Y + 1, door.Z + 0.5, null, true, 16, 0.9f);
        if (now >= track.NextShutMs)
        {
            track.NextShutMs = now + ShutLineMs;
            Tell(who, "reception", "l14-reception-shut");
        }
        track.LastX = x;
        track.LastZ = z;
        return true;
    }

    // ================= Testing =================

    private Entity LatestDummy(Entity near)
    {
        Entity best = null;
        foreach (Entity e in sapi.World.LoadedEntities.Values)
        {
            if (!e.Alive || !Senses.IsTestTarget(e)) continue;
            if (best == null) { best = e; continue; }
            if (near != null ? e.Pos.SquareDistanceTo(near.Pos.XYZ) < best.Pos.SquareDistanceTo(near.Pos.XYZ) : e.EntityId > best.EntityId) best = e;
        }
        return best;
    }

    /// <summary>The nearest tile within a reach (blocks) that passes a test, by rings outward.</summary>
    private (int X, int Z)? Nearest(int x, int z, int reach, System.Func<Tile, int, int, bool> ok)
    {
        for (int r = 0; r <= reach; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    Tile t = layout.TileAt(x + dx, z + dz);
                    if (t.Level == WorldLayout.Level14 && ok(t, x + dx, z + dz)) return (x + dx, z + dz);
                }
        return null;
    }

    private void Put(Entity who, double x, double z) => who.TeleportToDouble(x, geometry.FloorFor(WorldLayout.Level14) + 1, z);

    private string Describe(Tile t) =>
        $"{t.Kind} {WorldLayout.L14ZoneOf(t)}{(WorldLayout.L14IsDark(t) ? " (dark)" : "")}{(WorldLayout.L14IsContam(t) ? " (contaminated)" : "")}, floor {t.Depth}, variant {t.Variant}, under {t.Under}";

    private TextCommandResult OnCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string what = ((string)args[0]).Trim().ToLowerInvariant();
        string more = args.Parsers[1].IsMissing ? "" : ((string)args[1]).Trim().ToLowerInvariant();
        Entity who = args.Caller.Entity ?? LatestDummy(null);
        if (who == null) return TextCommandResult.Error("Needs a player, or a straw dummy put down first (/backrooms dummy place 14)");
        if (!InLevel(who.Pos.X, who.Pos.Z)) return TextCommandResult.Error($"Not in Level 14 ({who.Pos.X:0}, {who.Pos.Z:0})");
        int bx = (int)Math.Floor(who.Pos.X), bz = (int)Math.Floor(who.Pos.Z);
        Tile here = layout.TileAt(bx, bz);
        tracks.TryGetValue(who.EntityId, out Track track);
        string name = who is EntityPlayer p ? p.Player?.PlayerName ?? "player" : $"dummy #{who.EntityId}";
        switch (what)
        {
            case "contam":
            {
                var c = Nearest(bx, bz, 160, (t, _, _) => IsContam(t) && t.Kind == TileKind.Floor && t.Variant == 0);
                string where = c is { } cc ? $"; the nearest contaminated room's floor is at {cc.X}, {cc.Z} ({Math.Sqrt((cc.X - bx) * (cc.X - bx) + (cc.Z - bz) * (cc.Z - bz)):0} blocks)" : "; no contaminated room within 160 blocks";
                if (more == "go" && c is { } go)
                {
                    Put(who, go.X + 0.5, go.Z + 0.5);
                    return TextCommandResult.Success($"{name} put in the contaminated room at {go.X}, {go.Z}");
                }
                double since = track is { ContamSinceMs: >= 0 } ? (sapi.World.ElapsedMilliseconds - track.ContamSinceMs) / 1000.0 : 0;
                return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "{0} at {1}, {2}: {3}; {4}; stability {5:0.00}; in a contaminated room {6:0} s, hurt {7} times{8}",
                    name, bx, bz, Describe(here), IsContam(here) ? "CONTAMINATED" : "clean", Senses.Stability(who), since, track?.ContamHits ?? 0, where));
            }
            case "equipment":
            {
                if (more == "go")
                {
                    var e = Nearest(bx, bz, 96, (t, _, _) => t.Kind == TileKind.Floor && IsEquipment(t.Variant));
                    if (e is not { } eq) return TextCommandResult.Error("No equipment within 96 blocks");
                    var beside = Nearest(eq.X, eq.Z, 2, (t, x, z) => t.Kind == TileKind.Floor && t.Variant == 0 && (x != eq.X || z != eq.Z));
                    if (beside is not { } b) return TextCommandResult.Error($"Equipment at {eq.X}, {eq.Z}, but no open floor beside it");
                    Put(who, b.X + 0.5, b.Z + 0.5);
                    return TextCommandResult.Success($"{name} put beside the {layout.TileAt(eq.X, eq.Z).Variant} at {eq.X}, {eq.Z}");
                }
                var n = Nearest(bx, bz, 6, (t, _, _) => t.Kind == TileKind.Floor && IsEquipment(t.Variant));
                if (n is not { } at) return TextCommandResult.Error("No equipment within 6 blocks ('equipment go' finds some)");
                float before = who.GetBehavior<Vintagestory.GameContent.EntityBehaviorHealth>()?.Health ?? -1;
                if (!SpringToLife(who, at.X, at.Z, layout.TileAt(at.X, at.Z).Variant)) return TextCommandResult.Error($"The equipment at {at.X}, {at.Z} is not there (no block)");
                float after = who.GetBehavior<Vintagestory.GameContent.EntityBehaviorHealth>()?.Health ?? -1;
                return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "The {0} at {1}, {2} sprang to life at {3}: health {4:0.0} -> {5:0.0}",
                    layout.TileAt(at.X, at.Z).Variant, at.X, at.Z, name, before, after));
            }
            case "crack":
            {
                var c = Nearest(bx, bz, 128, (t, _, _) => IsCracked(t));
                if (c is not { } cr) return TextCommandResult.Error("No cracked floor within 128 blocks");
                if (more == "go") { Put(who, cr.X + 0.5, cr.Z + 0.5); return TextCommandResult.Success($"{name} put on the cracked floor at {cr.X}, {cr.Z}"); }
                return TextCommandResult.Success($"The nearest cracked floor: {cr.X}, {cr.Z} ({Describe(layout.TileAt(cr.X, cr.Z))}); {name} has heard it creak {track?.Creaks ?? 0} times");
            }
            case "reception":
            {
                var c = Nearest(bx, bz, 200, (t, _, _) => IsReceptionTile(t) && t.Kind == TileKind.Doorway);
                if (c is not { } rc) return TextCommandResult.Error("No reception room within 200 blocks");
                Room room = ReceptionAt(rc.X, rc.Z);
                string doors = string.Join(", ", room.Doors.Select(d => $"{d.X},{d.Z} {d.Out}"));
                if (more == "test") return ReceptionTest(who, room, name);
                return TextCommandResult.Success($"The nearest reception room #{room.Id:X}: {room.Tiles} tiles, doors {doors}; {name} is {(track?.Inside?.Id == room.Id ? "inside it" : "not inside it")}, has left it: {(track?.Left.Contains(room.Id) == true ? "yes" : "no")}");
            }
            case "state":
            {
                if (track == null) return TextCommandResult.Success($"{name}: nothing yet");
                long now = sapi.World.ElapsedMilliseconds;
                var sb = new StringBuilder();
                sb.Append(CultureInfo.InvariantCulture, $"{name} at {bx}, {bz}: {Describe(here)}; ");
                sb.Append(CultureInfo.InvariantCulture, $"contaminated for {(track.ContamSinceMs >= 0 ? (now - track.ContamSinceMs) / 1000.0 : 0):0} s, hurt {track.ContamHits} times; ");
                sb.Append(CultureInfo.InvariantCulture, $"equipment near {track.NearEquip.Count}, next may spring to life in {Math.Max(0, track.NextEquipMs - now) / 1000} s; ");
                sb.Append(CultureInfo.InvariantCulture, $"creaks {track.Creaks}; reception room {(track.Inside == null ? "none" : track.Inside.Id.ToString("X"))}, left {track.Left.Count}, turned away {track.Shut} times; ");
                sb.Append(CultureInfo.InvariantCulture, $"stability {Senses.Stability(who):0.00}, health {who.GetBehavior<Vintagestory.GameContent.EntityBehaviorHealth>()?.Health ?? -1:0.0}");
                return TextCommandResult.Success(sb.ToString());
            }
        }
        return TextCommandResult.Error("contam [go], equipment [go], crack [go], reception [test] or state");
    }

    /// <summary>
    /// Walks someone (a straw dummy, headless) through the rule: puts them in the room's middle (an arrival), then a block at a
    /// time every quarter second out through a door, down the corridor past <see cref="LeftReach"/>, back, and into the
    /// doorway, where they must be put out. The result goes to the server log.
    /// </summary>
    private TextCommandResult ReceptionTest(Entity who, Room room, string name)
    {
        var door = room.Doors[0];
        var (ox, oz) = Outward(door.Out);
        // Along the corridor outside: whichever way is open for six blocks
        (int Dx, int Dz) along = (0, 0);
        foreach (var (ax, az) in new[] { (oz, ox), (-oz, -ox) })
        {
            bool open = true;
            for (int k = 0; k <= 7 && open; k++)
            {
                Tile t = layout.TileAt(door.X + ox * 2 + ax * k, door.Z + oz * 2 + az * k);
                open = t.Kind is TileKind.Floor or TileKind.Doorway && !IsReceptionTile(t);
            }
            if (open) { along = (ax, az); break; }
        }
        if (along == (0, 0)) return TextCommandResult.Error("No open corridor beside the door to walk along");
        var path = new List<(double X, double Z)>();
        for (int k = 3; k >= 1; k--) path.Add((door.X + 0.5 - ox * k, door.Z + 0.5 - oz * k));   // inside, toward the door
        path.Add((door.X + 0.5, door.Z + 0.5));                                                       // the doorway
        for (int k = 1; k <= 2; k++) path.Add((door.X + 0.5 + ox * k, door.Z + 0.5 + oz * k));       // out
        for (int k = 1; k <= 7; k++) path.Add((door.X + 0.5 + ox * 2 + along.Dx * k, door.Z + 0.5 + oz * 2 + along.Dz * k));
        for (int k = 6; k >= 0; k--) path.Add((door.X + 0.5 + ox * 2 + along.Dx * k, door.Z + 0.5 + oz * 2 + along.Dz * k));
        path.Add((door.X + 0.5 + ox, door.Z + 0.5 + oz));
        path.Add((door.X + 0.5, door.Z + 0.5));                                                       // back into the doorway: turned away
        Put(who, path[0].X, path[0].Z);
        int floor = geometry.FloorFor(WorldLayout.Level14);
        for (int i = 1; i < path.Count; i++)
        {
            var (px, pz) = path[i];
            bool last = i == path.Count - 1;
            sapi.Event.RegisterCallback(_ =>
            {
                if (!who.Alive) return;
                who.TeleportToDouble(px, floor + 1, pz);
                if (!last) return;
                sapi.Event.RegisterCallback(__ =>
                {
                    tracks.TryGetValue(who.EntityId, out Track t);
                    Tile at = layout.TileAt((int)Math.Floor(who.Pos.X), (int)Math.Floor(who.Pos.Z));
                    bool outside = !IsReceptionTile(at);
                    sapi.Logger.Notification("[backrooms] l14 reception test: {0} {1} (at {2:0.0}, {3:0.0}: {4}); turned away {5} times, left {6} rooms",
                        name, outside ? "PASS: put back out" : "FAIL: still in the room", who.Pos.X, who.Pos.Z, Describe(at), t?.Shut ?? 0, t?.Left.Count ?? 0);
                }, 800);
            }, 400 + 300 * i);
        }
        return TextCommandResult.Success($"Walking {name} out of reception room #{room.Id:X} by the door at {door.X}, {door.Z} and back ({path.Count} steps); the result goes to the server log in about {(400 + 300 * path.Count + 800) / 1000} s");
    }
}
